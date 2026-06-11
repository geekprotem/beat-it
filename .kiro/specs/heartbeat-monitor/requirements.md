# Requirements Document

## Introduction

Heartbeat Monitor is a Python API service that provides heartbeat monitoring endpoints. Applications call designated endpoints at regular intervals to indicate they are running. The service tracks whether heartbeats arrive within configured time windows and reports application up/down status via OpenTelemetry gauge metrics.

## Glossary

- **Heartbeat_Service**: The Python API application that receives heartbeat requests and reports status metrics
- **Application_Name**: An identifier for a monitored application, derived from the environment variable suffix (e.g., `APP_NAME_MYAPP` yields application name `MYAPP`)
- **Heartbeat_Interval**: The maximum number of seconds allowed between consecutive heartbeat requests for a given Application_Name before it is considered down
- **OTEL_Exporter**: The component responsible for sending OpenTelemetry gauge metrics to the configured endpoint
- **Metric_Value**: An integer gauge value of `1` (application is up) or `0` (application is down)
- **Configured_Endpoint**: A `/heartbeat/{Application_Name}` route dynamically registered based on environment variables

## Requirements

### Requirement 1: Environment Variable Configuration

**User Story:** As an operator, I want to configure monitored applications via environment variables, so that I can add or remove monitored applications without code changes.

#### Acceptance Criteria

1. WHEN the Heartbeat_Service starts, THE Heartbeat_Service SHALL read all environment variables matching the pattern `APP_NAME_{Application_Name}` and register a Configured_Endpoint for each one
2. WHEN the Heartbeat_Service reads an `APP_NAME_{Application_Name}` variable, THE Heartbeat_Service SHALL parse the variable value as an integer greater than 0 and use it as the Heartbeat_Interval in seconds for that Application_Name
3. IF an `APP_NAME_{Application_Name}` variable has a value that is not a positive integer, THEN THE Heartbeat_Service SHALL log an error indicating the invalid configuration and skip registration of that Application_Name
4. WHEN the `PORT` environment variable is set to a valid port number between 1 and 65535, THE Heartbeat_Service SHALL listen for HTTP traffic on the specified port
5. IF the `PORT` environment variable is not set, THEN THE Heartbeat_Service SHALL listen for HTTP traffic on port 8080
6. WHEN the `OTEL_ENDPOINT` environment variable is set, THE Heartbeat_Service SHALL use the value as the destination for sending metrics
7. IF the `OTEL_ENDPOINT` environment variable is not set, THEN THE Heartbeat_Service SHALL disable metric reporting
8. WHEN the `OTEL_PREFIX` environment variable is set, THE Heartbeat_Service SHALL use the value as a prefix for all metric names

### Requirement 2: Heartbeat Endpoint

**User Story:** As a monitored application, I want to send a GET request to a heartbeat endpoint, so that the monitoring service knows I am running.

#### Acceptance Criteria

1. WHEN a GET request is received at `/heartbeat/{Application_Name}` for a Configured_Endpoint, THE Heartbeat_Service SHALL record the current timestamp as the last heartbeat time for that Application_Name
2. WHEN a GET request is received at `/heartbeat/{Application_Name}` for a Configured_Endpoint, THE Heartbeat_Service SHALL respond with HTTP status 200 within 2 seconds
3. WHEN a GET request is received at `/heartbeat/{name}` where `{name}` does not match any Configured_Endpoint using case-sensitive comparison, THE Heartbeat_Service SHALL respond with HTTP status 400
4. WHEN a GET request is received at `/heartbeat/{name}` where `{name}` does not match any Configured_Endpoint, THE Heartbeat_Service SHALL write a log entry that includes the unrecognized name from the request path
5. IF a non-GET HTTP request is received at `/heartbeat/{Application_Name}`, THEN THE Heartbeat_Service SHALL respond with HTTP status 405

### Requirement 3: Health Check Endpoint

**User Story:** As an operator, I want a health check endpoint, so that I can verify the Heartbeat_Service itself is running.

#### Acceptance Criteria

1. WHEN a GET request is received at `/healthcheck`, THE Heartbeat_Service SHALL respond with HTTP status 200 and a plain text body of `ok`
2. IF a non-GET HTTP request is received at `/healthcheck`, THEN THE Heartbeat_Service SHALL respond with HTTP status 405

### Requirement 4: Status Endpoint

**User Story:** As an operator, I want a status endpoint, so that I can see all configured endpoints and their current heartbeat status at a glance.

#### Acceptance Criteria

1. WHEN a GET request is received at `/status`, THE Heartbeat_Service SHALL respond with HTTP status 200 and a JSON body containing an entry for each Configured_Endpoint
2. WHEN a GET request is received at `/status`, THE Heartbeat_Service SHALL include for each Configured_Endpoint its Application_Name, its current status as "up" if the elapsed time since the last heartbeat is less than or equal to the Heartbeat_Interval or "down" otherwise, and the elapsed time in seconds since the last heartbeat
3. IF no heartbeat has ever been received for a Configured_Endpoint, THEN THE Heartbeat_Service SHALL report that endpoint's status as "down" and represent the elapsed time as null in the status JSON response
4. THE Heartbeat_Service SHALL format the status JSON response with 2-space indentation

### Requirement 5: Metric Reporting

**User Story:** As an operator, I want the service to report application status as OpenTelemetry metrics, so that I can integrate heartbeat status into my observability platform.

#### Acceptance Criteria

1. THE OTEL_Exporter SHALL send a gauge metric for each Configured_Endpoint to the configured OTEL_ENDPOINT at an interval no greater than 60 seconds
2. THE OTEL_Exporter SHALL name each metric using the pattern `{OTEL_PREFIX}.{Application_Name}`
3. WHILE the elapsed time since the last heartbeat for an Application_Name is less than or equal to the Heartbeat_Interval, THE OTEL_Exporter SHALL report a Metric_Value of 1 for that Application_Name
4. WHILE the elapsed time since the last heartbeat for an Application_Name exceeds the Heartbeat_Interval, THE OTEL_Exporter SHALL report a Metric_Value of 0 for that Application_Name
5. IF no heartbeat has ever been received for an Application_Name, THEN THE OTEL_Exporter SHALL report a Metric_Value of 0 for that Application_Name
6. IF the OTEL_ENDPOINT environment variable is not set, THEN THE OTEL_Exporter SHALL disable metric reporting and THE Heartbeat_Service SHALL continue operating without sending metrics
7. IF the OTEL_Exporter fails to send metrics to the OTEL_ENDPOINT, THEN THE OTEL_Exporter SHALL log the failure and retry on the next reporting interval without interrupting Heartbeat_Service operation

### Requirement 6: Container Deployment

**User Story:** As an operator, I want the service to run in a container, so that I can deploy it in containerized environments.

#### Acceptance Criteria

1. THE Heartbeat_Service SHALL provide a Dockerfile that builds a container image without errors
2. THE Heartbeat_Service SHALL expose the configured PORT for incoming HTTP traffic within the container
3. THE Heartbeat_Service SHALL accept all configuration through environment variables passed to the container at runtime
