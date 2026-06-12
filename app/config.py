"""Configuration module for parsing environment variables at startup."""

from __future__ import annotations

import logging
import os
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)

APP_NAME_PREFIX = "APP_NAME_"


@dataclass
class AppConfig:
    """Configuration for a single monitored application."""

    name: str  # Application_Name (from env var suffix)
    interval_seconds: int  # Heartbeat_Interval (env var value)


@dataclass
class ServiceConfig:
    """Top-level service configuration."""

    port: int  # PORT or default 8080
    otel_endpoint: str | None  # OTEL_ENDPOINT or None
    otel_prefix: str  # OTEL_PREFIX or default ""
    otel_export_interval: int  # OTEL_EXPORT_INTERVAL (seconds) or default 60
    apps: list[AppConfig] = field(default_factory=list)  # Parsed APP_NAME_* entries


def _parse_port(raw: str | None) -> int:
    """Parse PORT env var, returning default 8080 if invalid or unset."""
    if raw is None:
        return 8080
    try:
        port = int(raw)
    except ValueError:
        logger.warning("PORT value %r is not a valid integer, using default 8080", raw)
        return 8080
    if port < 1 or port > 65535:
        logger.warning("PORT value %d is out of range 1-65535, using default 8080", port)
        return 8080
    return port


def _parse_interval(name: str, raw: str) -> int | None:
    """Parse an APP_NAME_* value as a positive integer.

    Returns the integer on success, or None if the value is invalid.
    """
    # Reject float strings (e.g. "3.5") — int() would reject them anyway,
    # but we want a clear error message.
    if "." in raw:
        logger.error(
            "Invalid config for %s%s: value %r is not a positive integer",
            APP_NAME_PREFIX,
            name,
            raw,
        )
        return None

    try:
        value = int(raw)
    except ValueError:
        logger.error(
            "Invalid config for %s%s: value %r is not a positive integer",
            APP_NAME_PREFIX,
            name,
            raw,
        )
        return None

    if value <= 0:
        logger.error(
            "Invalid config for %s%s: value %d is not a positive integer",
            APP_NAME_PREFIX,
            name,
            value,
        )
        return None

    return value


def _parse_otel_export_interval(raw: str | None) -> int:
    """Parse OTEL_EXPORT_INTERVAL env var as seconds, defaulting to 60."""
    if raw is None:
        return 60
    try:
        value = int(raw)
    except ValueError:
        logger.warning(
            "OTEL_EXPORT_INTERVAL value %r is not a valid integer, using default 60",
            raw,
        )
        return 60
    if value <= 0:
        logger.warning(
            "OTEL_EXPORT_INTERVAL value %d must be positive, using default 60",
            value,
        )
        return 60
    return value


def load_config() -> ServiceConfig:
    """Read os.environ, filter APP_NAME_* keys, parse values, return config."""
    port = _parse_port(os.environ.get("PORT"))
    otel_endpoint = os.environ.get("OTEL_ENDPOINT") or None
    otel_prefix = os.environ.get("OTEL_PREFIX", "")
    otel_export_interval = _parse_otel_export_interval(
        os.environ.get("OTEL_EXPORT_INTERVAL")
    )

    apps: list[AppConfig] = []
    for key, value in os.environ.items():
        if not key.startswith(APP_NAME_PREFIX):
            continue
        app_name = key[len(APP_NAME_PREFIX):]
        if not app_name:
            continue
        interval = _parse_interval(app_name, value)
        if interval is not None:
            apps.append(AppConfig(name=app_name, interval_seconds=interval))

    return ServiceConfig(
        port=port,
        otel_endpoint=otel_endpoint,
        otel_prefix=otel_prefix,
        otel_export_interval=otel_export_interval,
        apps=apps,
    )
