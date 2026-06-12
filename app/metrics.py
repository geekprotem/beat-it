"""OpenTelemetry metrics setup for heartbeat monitoring."""

from __future__ import annotations

import logging

from opentelemetry.exporter.otlp.proto.http.metric_exporter import OTLPMetricExporter
from opentelemetry.metrics import Observation, set_meter_provider
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import (
    MetricExportResult,
    MetricExporter,
    MetricsData,
    PeriodicExportingMetricReader,
)

from app.config import ServiceConfig
from app.registry import HeartbeatRegistry

logger = logging.getLogger(__name__)


class _LoggingExporterWrapper(MetricExporter):
    """Wraps an exporter to log success/failure after each export."""

    def __init__(self, inner: MetricExporter) -> None:
        self._inner = inner

    def export(self, metrics_data: MetricsData, **kwargs) -> MetricExportResult:
        result = self._inner.export(metrics_data, **kwargs)
        if result == MetricExportResult.SUCCESS:
            logger.info("OTEL metric export succeeded")
        else:
            logger.warning("OTEL metric export failed")
        return result

    def force_flush(self, timeout_millis: float = 10_000) -> bool:
        return self._inner.force_flush(timeout_millis)

    def shutdown(self, timeout_millis: float = 30_000, **kwargs) -> None:
        self._inner.shutdown(timeout_millis, **kwargs)


def setup_metrics(config: ServiceConfig, registry: HeartbeatRegistry) -> None:
    """Configure OTLP exporter, meter, and ObservableGauge per application.

    If config.otel_endpoint is None, this function is a no-op and the service
    operates without metrics.

    Also exports a self-heartbeat gauge that always reports 1 to indicate
    the beat-it service itself is alive.
    """
    if config.otel_endpoint is None:
        return

    try:
        exporter = _LoggingExporterWrapper(
            OTLPMetricExporter(endpoint=config.otel_endpoint)
        )

        reader = PeriodicExportingMetricReader(
            exporter,
            export_interval_millis=config.otel_export_interval * 1000,
        )

        provider = MeterProvider(metric_readers=[reader])
        set_meter_provider(provider)

        meter = provider.get_meter("heartbeat-monitor")

        # Self-heartbeat: always reports 1 to indicate this service is running
        meter.create_observable_gauge(
            name=f"{config.otel_prefix}.beat-it",
            callbacks=[lambda _options: [Observation(1)]],
        )

        for app in config.apps:
            # Capture app name in closure to avoid late-binding issues
            app_name = app.name

            def _make_callback(name: str):
                def callback(_options):
                    return [Observation(registry.get_metric_value(name))]
                return callback

            meter.create_observable_gauge(
                name=f"{config.otel_prefix}.{app_name}",
                callbacks=[_make_callback(app_name)],
            )

        logger.info(
            "OpenTelemetry metrics configured: endpoint=%s, prefix=%s, interval=%ds, apps=%d (+self)",
            config.otel_endpoint,
            config.otel_prefix,
            config.otel_export_interval,
            len(config.apps),
        )
    except Exception:
        logger.exception("Failed to configure OpenTelemetry metrics; continuing without metrics")
