"""OpenTelemetry metrics setup for heartbeat monitoring."""

from __future__ import annotations

import logging

from opentelemetry.exporter.otlp.proto.grpc.metric_exporter import OTLPMetricExporter
from opentelemetry.metrics import Observation, set_meter_provider
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader

from app.config import ServiceConfig
from app.registry import HeartbeatRegistry

logger = logging.getLogger(__name__)


def setup_metrics(config: ServiceConfig, registry: HeartbeatRegistry) -> None:
    """Configure OTLP exporter, meter, and ObservableGauge per application.

    If config.otel_endpoint is None, this function is a no-op and the service
    operates without metrics.
    """
    if config.otel_endpoint is None:
        return

    try:
        exporter = OTLPMetricExporter(endpoint=config.otel_endpoint)

        reader = PeriodicExportingMetricReader(
            exporter,
            export_interval_millis=60000,
        )

        provider = MeterProvider(metric_readers=[reader])
        set_meter_provider(provider)

        meter = provider.get_meter("heartbeat-monitor")

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
            "OpenTelemetry metrics configured: endpoint=%s, prefix=%s, apps=%d",
            config.otel_endpoint,
            config.otel_prefix,
            len(config.apps),
        )
    except Exception:
        logger.exception("Failed to configure OpenTelemetry metrics; continuing without metrics")
