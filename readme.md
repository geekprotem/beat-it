
## Summary
This tool will provide an API with endpoints applications can call to indicate up/down status.

This tool is written in python.

Notice - this tool was built using kiro.

## Running
This application will run in a container.

## Configuration
Configuration is done with environment variables, such as:

### APP_NAME_$APPLICATION_NAME
The value for these envvars will be the number of seconds between expected heartbeats from `$APPLICATION_NAME`.

This will enable a heartbeat endpoint like `/heartbeat/$APPLICATION_NAME` that will expect a `GET` request at least once per defined interval.

### OTEL_ENDPOINT
This is the endpoint to send metrics to.  Each `$APPLICATION_NAME` will send an OTEL gauge metric to the endpoint with a metric named like `$OTEL_PREFIX.$APPLICATION_NAME`.

### OTEL_PREFIX
This is a prefix given to all metric names.

### PORT
The port to listen to for traffic.

## Metric Values

If a heartbeat has been detected for an endpoint within the defined interval for that application, then the metric value to OTEL will be a `1`.  All other cases will be a `0`.

## Endpoints

In addition to the dynamic endpoints setup with environment variables, the following endpoints will also be available:

* /healthcheck - returns a simple `ok` with status `200` when running
* /status - outputs a pretty formatted JSON showing all the endpoints configured and their current status, including how long it has been since the last heartbeat.

If a `/heartbeat` endpoint is called that hasn't been configured in an envvar, a `400` should be returned and an event noting this written to the log.
