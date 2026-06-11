"""Route handlers for the heartbeat monitor service."""

from __future__ import annotations

import json
import logging

from fastapi import APIRouter
from fastapi.responses import PlainTextResponse, Response

from app.registry import HeartbeatRegistry

logger = logging.getLogger(__name__)

router = APIRouter()

_registry: HeartbeatRegistry | None = None


def set_registry(registry: HeartbeatRegistry) -> None:
    """Set the module-level registry instance during app initialization."""
    global _registry
    _registry = registry


@router.get("/healthcheck")
def healthcheck_handler() -> PlainTextResponse:
    """Return plain text 'ok' for container liveness probes."""
    return PlainTextResponse("ok", status_code=200)


@router.get("/heartbeat/{name}")
def heartbeat_handler(name: str) -> PlainTextResponse:
    """Record a heartbeat for the given application name.

    Returns 200 if registered, 400 if the name is not recognized.
    """
    assert _registry is not None

    if not _registry.record_heartbeat(name):
        logger.warning("Unregistered heartbeat attempt: %s", name)
        return PlainTextResponse(
            f"Unknown application: {name}", status_code=400
        )

    return PlainTextResponse("ok", status_code=200)


@router.get("/status")
def status_handler() -> Response:
    """Return JSON status of all monitored applications with 2-space indentation."""
    assert _registry is not None

    data = {"applications": _registry.get_all_statuses()}
    body = json.dumps(data, indent=2)
    return Response(content=body, media_type="application/json")
