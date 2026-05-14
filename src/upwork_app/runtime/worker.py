"""Long-running Docker collector worker runtime."""

from __future__ import annotations

import signal
import time
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from upwork_app.db.connection import connect_worker
from upwork_app.integrations.upwork.credentials import redact
from upwork_app.repositories import collector_control
from upwork_app.runtime.config import RuntimeSettings, load_runtime_settings
from upwork_app.services.scheduled_collection import collect_scheduled

Sleep = Callable[[float], None]
CollectOnce = Callable[..., Any]


@dataclass(slots=True)
class WorkerRuntime:
    settings: RuntimeSettings
    sleep: Sleep = time.sleep
    collect_once: CollectOnce = collect_scheduled
    stop_requested: bool = False

    def request_stop(self, *_args: object) -> None:
        self.stop_requested = True

    def run(self, *, max_iterations: int | None = None) -> dict[str, Any]:
        iterations = 0
        with connect_worker(self.settings.db_path) as connection:
            collector_control.seed_config(connection, self.settings.persisted_defaults())
            connection.commit()

        while not self.stop_requested:
            self.process_commands()
            config = self.effective_config()
            if not bool(config.get("paused", False)):
                self._run_collection(trigger="worker_interval", config=config)
            iterations += 1
            if max_iterations is not None and iterations >= max_iterations:
                break
            self._sleep_with_command_poll(float(config.get("interval_seconds", 3600)))
        return {"ok": True, "iterations": iterations, "stopped": self.stop_requested}

    def effective_config(self) -> dict[str, Any]:
        with connect_worker(self.settings.db_path) as connection:
            collector_control.seed_config(connection, self.settings.persisted_defaults())
            connection.commit()
            return collector_control.get_config(connection)

    def process_commands(self) -> int:
        processed = 0
        while not self.stop_requested:
            with connect_worker(self.settings.db_path) as connection:
                command = collector_control.next_queued_command(connection)
                if command is None:
                    return processed
                collector_control.mark_running(connection, str(command["command_id"]))
                connection.commit()
            self._apply_command(command)
            processed += 1
        return processed

    def _apply_command(self, command: dict[str, Any]) -> None:
        command_id = str(command["command_id"])
        command_type = str(command["command_type"])
        payload = command["payload"] if isinstance(command["payload"], dict) else {}
        try:
            if command_type == "pause":
                result = self._set_paused(True)
            elif command_type == "resume":
                result = self._set_paused(False)
            elif command_type == "update_config":
                result = self._update_config(payload)
            elif command_type == "run_once":
                result = self._run_collection(
                    trigger="mcp_run_once", config=self.effective_config()
                )
            else:
                raise ValueError(f"unsupported command type: {command_type}")
            with connect_worker(self.settings.db_path) as connection:
                collector_control.mark_applied(connection, command_id, result=result)
                connection.commit()
        except Exception as exc:  # pragma: no cover - exercised via tests with fake failures
            with connect_worker(self.settings.db_path) as connection:
                collector_control.mark_failed(
                    connection,
                    command_id,
                    error_type=type(exc).__name__,
                    redacted_error=redact(exc),
                )
                connection.commit()

    def _set_paused(self, paused: bool) -> dict[str, Any]:
        with connect_worker(self.settings.db_path) as connection:
            config = collector_control.update_config(
                connection, {"paused": paused}, updated_by="worker"
            )
            connection.commit()
            return {"config": config}

    def _update_config(self, payload: dict[str, Any]) -> dict[str, Any]:
        updates = payload.get("updates", payload)
        if not isinstance(updates, dict):
            raise ValueError("update_config payload must be an object")
        with connect_worker(self.settings.db_path) as connection:
            config = collector_control.update_config(connection, updates, updated_by="worker")
            connection.commit()
            return {"config": config}

    def _run_collection(self, *, trigger: str, config: dict[str, Any]) -> dict[str, Any]:
        queries = config.get("queries")
        query_tuple = (
            tuple(str(item) for item in queries) if isinstance(queries, list) and queries else None
        )
        result = self.collect_once(
            db_path=self.settings.db_path,
            queries=query_tuple,
            max_pages=int(config.get("max_pages", self.settings.max_pages)),
            page_size=int(config.get("page_size", self.settings.page_size)),
            trigger=trigger,
            live=self.settings.live,
            fixture=None if self.settings.live else self.settings.fixture_path,
        )
        if hasattr(result, "to_dict"):
            return dict(result.to_dict())
        return {"result": result}

    def _sleep_with_command_poll(self, seconds: float) -> None:
        elapsed = 0.0
        tick = min(5.0, seconds)
        while elapsed < seconds and not self.stop_requested:
            self.sleep(tick)
            elapsed += tick
            self.process_commands()


def run_worker(settings: RuntimeSettings | None = None) -> dict[str, Any]:
    runtime = WorkerRuntime(settings or load_runtime_settings())
    signal.signal(signal.SIGTERM, runtime.request_stop)
    signal.signal(signal.SIGINT, runtime.request_stop)
    return runtime.run()
