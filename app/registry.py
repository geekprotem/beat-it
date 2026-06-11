"""Thread-safe in-memory store for heartbeat state."""

from __future__ import annotations

import threading
import time

from app.config import AppConfig


class HeartbeatRegistry:
    """Tracks heartbeat timestamps and computes liveness status for monitored apps."""

    def __init__(self, apps: list[AppConfig]) -> None:
        self._apps: dict[str, AppConfig] = {app.name: app for app in apps}
        self._last_seen: dict[str, float | None] = {app.name: None for app in apps}
        self._lock = threading.Lock()

    def record_heartbeat(self, app_name: str) -> bool:
        """Record current timestamp for app_name.

        Returns True if the app is registered, False otherwise.
        """
        with self._lock:
            if app_name not in self._apps:
                return False
            self._last_seen[app_name] = time.time()
            return True

    def is_registered(self, app_name: str) -> bool:
        """Check if an app_name is a configured endpoint (case-sensitive)."""
        return app_name in self._apps

    def get_status(self, app_name: str) -> tuple[str, float | None]:
        """Return (status, elapsed_seconds) for a given app.

        Status is "up" if last_seen is not None and elapsed <= interval_seconds,
        otherwise "down". Elapsed is None if never seen.
        """
        with self._lock:
            last_seen = self._last_seen.get(app_name)

        if last_seen is None:
            return ("down", None)

        elapsed = time.time() - last_seen
        interval = self._apps[app_name].interval_seconds

        if elapsed <= interval:
            return ("up", elapsed)
        return ("down", elapsed)

    def get_all_statuses(self) -> list[dict]:
        """Return a list of status dicts for all configured apps.

        Each dict has keys: "name", "status", "elapsed_seconds".
        """
        statuses = []
        for app_name in self._apps:
            status, elapsed = self.get_status(app_name)
            statuses.append({
                "name": app_name,
                "status": status,
                "elapsed_seconds": elapsed,
            })
        return statuses

    def get_metric_value(self, app_name: str) -> int:
        """Return 1 if the app is up, 0 if down or never seen."""
        status, _ = self.get_status(app_name)
        return 1 if status == "up" else 0
