# Implementation Plan

## Overview

Implement the Heartbeat Monitor service — a Python FastAPI application that accepts heartbeat GET requests from monitored applications, tracks their liveness in memory, reports status via OpenTelemetry gauge metrics, and runs in a Docker container. The implementation follows the modular design: config → registry → routes → metrics → entrypoint → container → tests.

## Tasks

- [ ] 1. Project setup and dependencies
  - Create `requirements.txt` with: `fastapi`, `uvicorn[standard]`, `opentelemetry-api`, `opentelemetry-sdk`, `opentelemetry-exporter-otlp-proto-grpc`
  - Create `app/` directory with `__init__.py`
  - Configure Python logging with format `%(asctime)s %(levelname)s %(name)s %(message)s`
  - **Requirements:** 1.1, 1.4, 1.5, 1.6, 1.7, 1.8
  - **Design:** Configuration Module, Application Entrypoint

- [ ] 2. Configuration module (`app/config.py`)
  - Implement `AppConfig` dataclass with `name: str` and `interval_seconds: int`
  - Implement `ServiceConfig` dataclass with `port: int`, `otel_endpoint: str | None`, `otel_prefix: str`, `apps: list[AppConfig]`
  - Implement `load_config()` that reads `os.environ`, filters `APP_NAME_*` keys, strips prefix for app name
  - Parse values as positive integers; log error and skip invalid entries (zero, negative, non-numeric, floats)
  - Read `PORT` (default 8080, validate 1-65535), `OTEL_ENDPOINT` (None if unset), `OTEL_PREFIX` (empty string if unset)
  - **Requirements:** 1.1, 1.2, 1.3, 1.4, 1.5, 1.6, 1.7, 1.8
  - **Design:** Configuration Module, Property 1, Property 2

- [ ] 3. Heartbeat registry (`app/registry.py`)
  - Implement `HeartbeatRegistry.__init__(apps)` initializing `_apps` dict, `_last_seen` dict (all None), `threading.Lock`
  - Implement `record_heartbeat(app_name) -> bool` updating `_last_seen` to `time.time()` under lock; False if not registered
  - Implement `is_registered(app_name) -> bool` for case-sensitive lookup
  - Implement `get_status(app_name) -> tuple[str, float | None]` returning ("up"/"down", elapsed or None)
  - Implement `get_all_statuses() -> list[dict]` returning `{"name", "status", "elapsed_seconds"}` for all apps
  - Implement `get_metric_value(app_name) -> int` returning 1 if up, 0 if down/never seen
  - **Requirements:** 2.1, 4.2, 4.3, 5.3, 5.4, 5.5
  - **Design:** Heartbeat Registry, Property 3, Property 5

- [ ] 4. Route handlers (`app/routes.py`)
  - Implement GET `/healthcheck` returning plain text `ok` with status 200
  - Implement GET `/heartbeat/{name}` that records heartbeat, returns 200 if registered, 400 if not, logs warning for unregistered
  - Implement GET `/status` returning `registry.get_all_statuses()` as JSON with 2-space indent
  - Non-GET methods return 405 via FastAPI method restriction
  - **Requirements:** 2.1, 2.2, 2.3, 2.4, 2.5, 3.1, 3.2, 4.1, 4.2, 4.3, 4.4
  - **Design:** Route Handlers, Property 3, Property 4

- [ ] 5. Metrics module (`app/metrics.py`)
  - Implement `setup_metrics(config, registry)` — no-op if `otel_endpoint` is None
  - Create `OtlpGrpcMetricExporter` pointed at configured endpoint
  - Create `PeriodicExportingMetricReader` with export interval ≤60s
  - Register `ObservableGauge` per app named `{otel_prefix}.{app_name}` with callback reading `registry.get_metric_value()`
  - Wrap export in try/except, log failures without crashing
  - **Requirements:** 5.1, 5.2, 5.3, 5.4, 5.5, 5.6, 5.7
  - **Design:** Metrics Module, Property 6

- [ ] 6. Application entrypoint (`app/main.py`)
  - Call `load_config()`, create `HeartbeatRegistry`, call `setup_metrics()`
  - Create FastAPI app, include route handlers
  - Run uvicorn on configured port
  - Log startup info with configured app count and port
  - **Requirements:** 1.1, 1.4, 1.5
  - **Design:** Application Entrypoint

- [ ] 7. Dockerfile
  - Use Python slim base image
  - Copy and install `requirements.txt`
  - Copy app source code
  - Set CMD to run the application
  - Document default port 8080 with EXPOSE
  - **Requirements:** 6.1, 6.2, 6.3
  - **Design:** Architecture

- [ ] 8. Unit and property-based tests
  - Create `tests/` with `conftest.py` (test fixtures, mock registry, FastAPI TestClient)
  - Create `requirements-dev.txt` with `pytest`, `httpx`, `hypothesis`
  - Unit tests for `load_config()`: valid apps, invalid values, PORT defaults, OTEL settings
  - Unit tests for `HeartbeatRegistry`: record, status computation, metric values
  - Unit tests for routes: healthcheck 200, heartbeat 200/400/405, status JSON format
  - Property-based tests (Hypothesis, min 100 examples) for design Properties 1-6
  - **Requirements:** All
  - **Design:** Testing Strategy, Correctness Properties 1-6

## Task Dependency Graph

```json
{
  "waves": [
    [1],
    [2],
    [3],
    [4],
    [5],
    [6],
    [7],
    [8]
  ]
}
```

Tasks are sequential: each module builds on the previous. Task 8 (tests) depends on all implementation tasks being complete.

## Notes

- All state is in-memory; no database setup required.
- The OTEL exporter is optional — the service works without it when `OTEL_ENDPOINT` is unset.
- FastAPI handles 405 responses automatically when routes specify allowed methods.
- Property-based tests use Hypothesis with `@settings(max_examples=100)`.
