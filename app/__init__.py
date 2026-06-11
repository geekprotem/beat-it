"""Heartbeat Monitor - A lightweight service for tracking application liveness."""

import logging

logging.basicConfig(
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
    level=logging.INFO,
)
