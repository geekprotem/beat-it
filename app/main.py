"""Application entrypoint for the heartbeat monitor service."""

from __future__ import annotations

import logging

import uvicorn
from fastapi import FastAPI

from app.config import load_config
from app.metrics import setup_metrics
from app.registry import HeartbeatRegistry
from app.routes import router, set_registry

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

config = load_config()
registry = HeartbeatRegistry(config.apps)
setup_metrics(config, registry)

app = FastAPI()
set_registry(registry)
app.include_router(router)

logger.info(
    "Starting heartbeat monitor: %d application(s) configured, port %d",
    len(config.apps),
    config.port,
)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=config.port)
