"""Local read-only dashboard service for Dispatch Engine runs."""

from __future__ import annotations

from datetime import datetime, timezone
from http import HTTPStatus
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
import json
import mimetypes
import os
from pathlib import Path
import shlex
import signal
import socket
from socketserver import TCPServer
import subprocess
import sys
import time
from typing import Any
from urllib.parse import parse_qs, unquote, urlparse

from .agents import list_agents, read_agent
from .events import utc_timestamp
from .runs import resolve_run_dir, runs_dir
from .state import _normalized_workstream_records, run_alerts, run_events, run_status, tail_events

DASHBOARD_SCHEMA_VERSION = 1
DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 0
STARTUP_TIMEOUT_SECONDS = 5.0
STOP_GRACE_SECONDS = 1.0


def launch_dashboard(
    target: Path,
    *,
    run_id: str | None = None,
    host: str = DEFAULT_HOST,
    port: int = DEFAULT_PORT,
    detach: bool = False,
    dashboard_dir: Path | None = None,
) -> dict[str, Any]:
    """Start a dashboard service, or run it in the foreground when detach is false."""

    repo_root = target.resolve()
    selected = resolve_run_dir(repo_root, run_id)
    if selected is None:
        return _run_error("missing_run" if run_id else "no_run", run_id=run_id)

    assets = _resolve_dashboard_dir(dashboard_dir)
    asset_error = _validate_dashboard_assets(assets)
    if asset_error is not None:
        return _dashboard_error(
            "missing_dashboard_assets",
            asset_error,
            run_id=selected.name,
            state_dir=selected,
            dashboard_dir=assets,
        )

    dashboard_state_dir = _dashboard_state_dir(selected)
    metadata_path = _metadata_path(selected)
    dashboard_state_dir.mkdir(parents=True, exist_ok=True)
    if detach:
        existing = _read_metadata(metadata_path)
        if existing and _server_is_alive(existing):
            return _dashboard_payload(
                existing,
                status="reused",
                alive=True,
                state_dir=selected,
                dashboard_dir=assets,
            )
        return _launch_detached_server(
            repo_root,
            selected,
            host=host,
            port=port,
            dashboard_dir=assets,
        )

    return serve_dashboard(
        repo_root,
        run_id=selected.name,
        host=host,
        port=port,
        dashboard_dir=assets,
    )


def serve_dashboard(
    target: Path,
    *,
    run_id: str,
    host: str = DEFAULT_HOST,
    port: int = DEFAULT_PORT,
    dashboard_dir: Path | None = None,
) -> dict[str, Any]:
    """Serve dashboard HTTP requests in the current process."""

    repo_root = target.resolve()
    selected = resolve_run_dir(repo_root, run_id)
    if selected is None:
        return _run_error("missing_run", run_id=run_id)

    assets = _resolve_dashboard_dir(dashboard_dir)
    asset_error = _validate_dashboard_assets(assets)
    if asset_error is not None:
        return _dashboard_error(
            "missing_dashboard_assets",
            asset_error,
            run_id=selected.name,
            state_dir=selected,
            dashboard_dir=assets,
        )

    handler_class = _handler_class(repo_root=repo_root, run_id=selected.name, dashboard_dir=assets)
    server = DashboardHTTPServer((host, port), handler_class)
    actual_host, actual_port = server.server_address[:2]
    url = f"http://{actual_host}:{actual_port}/"
    metadata_path = _metadata_path(selected)
    record = _metadata_record(
        repo_root=repo_root,
        run_state_dir=selected,
        dashboard_dir=assets,
        host=actual_host,
        port=actual_port,
        url=url,
        pid=os.getpid(),
        status="running",
    )
    _write_metadata(metadata_path, record)
    try:
        server.serve_forever()
    finally:
        server.server_close()
        latest = _read_metadata(metadata_path) or record
        if latest.get("pid") == os.getpid() and latest.get("status") == "running":
            latest["status"] = "stopped"
            latest["alive"] = False
            latest["updated_at"] = utc_timestamp()
            latest["stopped_at"] = latest["updated_at"]
            _write_metadata(metadata_path, latest)
    return _dashboard_payload(record, status="running", alive=True, state_dir=selected, dashboard_dir=assets)


class DashboardHTTPServer(ThreadingHTTPServer):
    """HTTP server that avoids reverse-DNS lookup during localhost bind."""

    def server_bind(self) -> None:
        TCPServer.server_bind(self)
        host, port = self.server_address[:2]
        self.server_name = str(host)
        self.server_port = int(port)


def dashboard_status(target: Path, *, run_id: str | None = None) -> dict[str, Any]:
    repo_root = target.resolve()
    selected = resolve_run_dir(repo_root, run_id)
    if selected is None:
        return _run_error("missing_run" if run_id else "no_run", run_id=run_id)

    metadata_path = _metadata_path(selected)
    record = _read_metadata(metadata_path)
    if record is None:
        return {
            "kind": "dashboard_status",
            "status": "not_started",
            "summary": f"No dashboard service metadata found for run {selected.name}.",
            "run_id": selected.name,
            "state_dir": str(selected),
            "metadata_path": str(metadata_path),
            "alive": False,
            "url": None,
            "pid": None,
        }

    alive = _server_is_alive(record)
    status = "running" if alive else str(record.get("status") or "stopped")
    if status == "running" and record.get("status") != "running":
        status = "stale"
    return _dashboard_status_payload(record, status=status, alive=alive, state_dir=selected)


def stop_dashboard(target: Path, *, run_id: str | None = None) -> dict[str, Any]:
    repo_root = target.resolve()
    selected = resolve_run_dir(repo_root, run_id)
    if selected is None:
        return _run_error("missing_run" if run_id else "no_run", run_id=run_id)

    metadata_path = _metadata_path(selected)
    record = _read_metadata(metadata_path)
    if record is None:
        return {
            "kind": "dashboard_stop",
            "status": "not_running",
            "summary": f"No dashboard service metadata found for run {selected.name}.",
            "run_id": selected.name,
            "state_dir": str(selected),
            "metadata_path": str(metadata_path),
            "alive": False,
            "url": None,
            "pid": None,
        }

    pid = _coerce_pid(record.get("pid"))
    alive_before = pid is not None and _pid_is_alive(pid)
    signal_sent = False
    escalated = False
    if alive_before and pid != os.getpid():
        signal_sent = _terminate_pid(pid)
        deadline = time.monotonic() + STOP_GRACE_SECONDS
        while signal_sent and time.monotonic() < deadline and _pid_is_alive(pid):
            time.sleep(0.05)
        if signal_sent and _pid_is_alive(pid):
            escalated = _kill_pid(pid)
            deadline = time.monotonic() + STOP_GRACE_SECONDS
            while escalated and time.monotonic() < deadline and _pid_is_alive(pid):
                time.sleep(0.05)

    alive_after = _server_is_alive(record)
    now = utc_timestamp()
    record["status"] = "stopped" if not alive_after else "stale"
    record["alive"] = alive_after
    record["updated_at"] = now
    record["stopped_at"] = now
    record["stop_signal_sent"] = signal_sent
    record["stop_escalated"] = escalated
    _write_metadata(metadata_path, record)
    return {
        "kind": "dashboard_stop",
        "status": record["status"],
        "summary": f"Dashboard service for run {selected.name} is {record['status']}.",
        "run_id": selected.name,
        "state_dir": str(selected),
        "metadata_path": str(metadata_path),
        "url": record.get("url"),
        "pid": pid,
        "alive": alive_after,
        "signal_sent": signal_sent,
        "escalated": escalated,
    }


def _launch_detached_server(
    repo_root: Path,
    run_state_dir: Path,
    *,
    host: str,
    port: int,
    dashboard_dir: Path,
) -> dict[str, Any]:
    dashboard_state = _dashboard_state_dir(run_state_dir)
    metadata_path = _metadata_path(run_state_dir)
    stdout_path = dashboard_state / "server.stdout.log"
    stderr_path = dashboard_state / "server.stderr.log"
    stdout_path.write_text("", encoding="utf-8")
    stderr_path.write_text("", encoding="utf-8")

    argv = [
        sys.executable,
        str(Path(__file__).resolve().parents[1] / "de.py"),
        "dashboard",
        str(repo_root),
        "--run-id",
        run_state_dir.name,
        "--host",
        host,
        "--port",
        str(port),
        "--serve",
    ]
    env = _detached_env()
    with stdout_path.open("a", encoding="utf-8") as stdout, stderr_path.open("a", encoding="utf-8") as stderr:
        process = subprocess.Popen(
            argv,
            cwd=repo_root,
            env=env,
            stdout=stdout,
            stderr=stderr,
            start_new_session=True,
            close_fds=True,
        )

    deadline = time.monotonic() + STARTUP_TIMEOUT_SECONDS
    last_record: dict[str, Any] | None = None
    while time.monotonic() < deadline:
        if process.poll() is not None:
            break
        last_record = _read_metadata(metadata_path)
        if last_record and _coerce_pid(last_record.get("pid")) == process.pid and _server_is_alive(last_record):
            process._child_created = False  # type: ignore[attr-defined]
            return _dashboard_payload(
                last_record,
                status="running",
                alive=True,
                state_dir=run_state_dir,
                dashboard_dir=dashboard_dir,
            )
        time.sleep(0.05)

    stderr_text = _tail_text(stderr_path)
    start_status = "dashboard_start_timeout" if process.poll() is None else "dashboard_start_failed"
    if process.poll() is None:
        _terminate_pid(process.pid)
        deadline = time.monotonic() + STOP_GRACE_SECONDS
        while time.monotonic() < deadline and _pid_is_alive(process.pid):
            time.sleep(0.05)
        if _pid_is_alive(process.pid):
            _kill_pid(process.pid)
    return _dashboard_error(
        start_status,
        f"Dashboard service did not start for run {run_state_dir.name}."
        + (f" stderr: {stderr_text}" if stderr_text else ""),
        run_id=run_state_dir.name,
        state_dir=run_state_dir,
        dashboard_dir=dashboard_dir,
        extra={
            "pid": process.pid,
            "metadata_path": str(metadata_path),
            "stdout_path": str(stdout_path),
            "stderr_path": str(stderr_path),
        },
    )


def _handler_class(*, repo_root: Path, run_id: str, dashboard_dir: Path) -> type[SimpleHTTPRequestHandler]:
    class DashboardRequestHandler(SimpleHTTPRequestHandler):
        server_version = "DispatchDashboard/1"

        def do_GET(self) -> None:  # noqa: N802 - stdlib handler API
            parsed = urlparse(self.path)
            if parsed.path.startswith("/api/"):
                self._handle_api(parsed.path, parse_qs(parsed.query))
                return
            self._handle_static(parsed.path)

        def do_HEAD(self) -> None:  # noqa: N802 - stdlib handler API
            if self.path == "/" or self.path.startswith("/api/"):
                self.send_response(HTTPStatus.OK)
                self.end_headers()
                return
            self._handle_static(urlparse(self.path).path, include_body=False)

        def log_message(self, format: str, *args: Any) -> None:
            return

        def _handle_api(self, path: str, query: dict[str, list[str]]) -> None:
            if path == "/api/status":
                self._send_state_payload(run_status(repo_root, run_id=run_id))
                return
            if path == "/api/events":
                since = query.get("since", [None])[0]
                self._send_state_payload(run_events(repo_root, run_id=run_id, since=since))
                return
            if path == "/api/alerts":
                self._send_state_payload(run_alerts(repo_root, run_id=run_id))
                return
            if path == "/api/tail":
                self._send_state_payload(tail_events(repo_root, run_id=run_id))
                return
            if path == "/api/plan":
                self._send_state_payload(_plan_payload(repo_root, run_id))
                return
            if path == "/api/host-heartbeat":
                self._send_json(_host_heartbeat(repo_root, run_id), HTTPStatus.OK)
                return
            if path == "/api/logs/coordinator":
                self._send_json(_coordinator_logs(repo_root, run_id), HTTPStatus.OK)
                return
            if path.startswith("/api/logs/agent/"):
                agent_id = unquote(path.removeprefix("/api/logs/agent/"))
                self._send_json(_agent_logs(repo_root, run_id, agent_id), HTTPStatus.OK)
                return
            if path.startswith("/api/report/"):
                agent_id = unquote(path.removeprefix("/api/report/"))
                self._send_state_payload(_agent_report(repo_root, run_id, agent_id))
                return
            if path.startswith("/api/agent/"):
                agent_id = unquote(path.removeprefix("/api/agent/"))
                self._send_state_payload(_agent_detail(repo_root, run_id, agent_id))
                return
            if path == "/api/history":
                self._send_json(_run_history(repo_root), HTTPStatus.OK)
                return
            self._send_json(
                {
                    "kind": "error",
                    "status": "not_found",
                    "summary": f"Unknown dashboard API endpoint: {path}",
                },
                HTTPStatus.NOT_FOUND,
            )

        def _handle_static(self, path: str, include_body: bool = True) -> None:
            asset_path = _static_asset_path(dashboard_dir, path)
            if asset_path is None or not asset_path.is_file():
                self._send_json(
                    {
                        "kind": "error",
                        "status": "missing_dashboard_asset",
                        "summary": f"Dashboard asset not found: {path}",
                    },
                    HTTPStatus.NOT_FOUND,
                )
                return
            content_type = mimetypes.guess_type(str(asset_path))[0] or "application/octet-stream"
            body = asset_path.read_bytes() if include_body else b""
            self.send_response(HTTPStatus.OK)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            if include_body:
                self.wfile.write(body)

        def _send_state_payload(self, payload: dict[str, Any]) -> None:
            self._send_json(payload, _status_code_for_payload(payload))

        def _send_json(self, payload: dict[str, Any], status_code: HTTPStatus) -> None:
            body = json.dumps(payload, indent=2, sort_keys=True).encode("utf-8")
            self.send_response(status_code)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

    return DashboardRequestHandler


def _coordinator_logs(repo_root: Path, run_id: str) -> dict[str, Any]:
    selected = resolve_run_dir(repo_root, run_id)
    if selected is None:
        return _run_error("missing_run", run_id=run_id)
    stdout_path = selected / "logs" / "coordinator-001.stdout.log"
    stderr_path = selected / "logs" / "coordinator-001.stderr.log"
    stdout = _read_text_if_exists(stdout_path)
    stderr = _read_text_if_exists(stderr_path)
    return {
        "kind": "coordinator_logs",
        "status": "ok",
        "run_id": selected.name,
        "state_dir": str(selected),
        "stdout_path": str(stdout_path),
        "stderr_path": str(stderr_path),
        "stdout": stdout,
        "stderr": stderr,
        "stdout_exists": stdout_path.is_file(),
        "stderr_exists": stderr_path.is_file(),
        "stdout_line_count": len(stdout.splitlines()),
        "stderr_line_count": len(stderr.splitlines()),
        "empty_states": {
            "stdout": not stdout,
            "stderr": not stderr,
            "stdout_file": not stdout_path.is_file(),
            "stderr_file": not stderr_path.is_file(),
        },
    }


def _plan_payload(repo_root: Path, run_id: str) -> dict[str, Any]:
    selected = resolve_run_dir(repo_root, run_id)
    if selected is None:
        return _run_error("missing_run", run_id=run_id)
    run = _read_json_object(selected / "run.json")
    if run is None:
        return _dashboard_error(
            "missing_run_file",
            f"Run has no readable run.json: {selected}",
            run_id=selected.name,
            state_dir=selected,
        )

    plan = run.get("plan") if isinstance(run.get("plan"), dict) else {}
    status_payload = run_status(repo_root, run_id=run_id)
    assignments = status_payload.get("workstream_assignments")
    workstreams = _workstream_records(
        _normalized_workstream_records(selected, run),
        assignments if isinstance(assignments, list) else [],
    )
    root_label = str(plan.get("source_path") or plan.get("plan_id") or selected.name)
    root_name = Path(root_label).name if root_label else str(plan.get("plan_id") or selected.name)
    tree = {
        "id": str(plan.get("plan_id") or selected.name),
        "name": root_name,
        "label": root_name,
        "type": "plan",
        "status": _aggregate_status([item.get("status") for item in workstreams]),
        "children": _phase_nodes(workstreams),
    }
    return {
        "kind": "plan",
        "status": "ok",
        "run_id": selected.name,
        "state_dir": str(selected),
        "plan_id": plan.get("plan_id"),
        "source_path": plan.get("source_path"),
        "objective": run.get("objective"),
        "workstream_count": len(workstreams),
        "tree": tree,
        "workstreams": workstreams,
        "empty_states": {
            "plan": not bool(plan),
            "source_path": not bool(plan.get("source_path")),
            "workstreams": not bool(workstreams),
        },
    }


def _workstream_records(
    records: list[dict[str, Any]],
    assignments: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    by_workstream: dict[str, dict[str, Any]] = {}
    for agent in assignments:
        workstream = agent.get("workstream")
        if isinstance(workstream, str) and workstream:
            by_workstream[workstream] = agent

    normalized = []
    for item in records:
        workstream_id = str(item.get("id"))
        agent = by_workstream.get(workstream_id, {})
        depends_on = _string_list_value(item.get("depends_on"))
        files = _string_list_value(item.get("files"))
        validation = _string_list_value(item.get("validation"))
        status = str(agent.get("status") or item.get("status") or "planned")
        normalized.append(
            {
                "id": workstream_id,
                "name": f"{workstream_id} {item.get('title') or ''}".strip(),
                "title": item.get("title") or workstream_id,
                "type": "workstream",
                "status": status,
                "mode": item.get("mode") or "serial",
                "parallel_group": item.get("parallel_group"),
                "scope": item.get("scope"),
                "depends_on": depends_on,
                "dependency_labels": depends_on,
                "files": files,
                "file_count": len(files),
                "validation": validation,
                "validation_count": len(validation),
                "agent_id": agent.get("agent_id") or item.get("assigned_agent"),
                "role": agent.get("role") or item.get("assigned_role"),
                "blocked_reason": item.get("blocked_reason") or item.get("blocker") or item.get("reason"),
                "created_at": item.get("created_at"),
                "updated_at": item.get("updated_at"),
            }
        )
    return sorted(normalized, key=lambda item: item["id"])


def _phase_nodes(workstreams: list[dict[str, Any]]) -> list[dict[str, Any]]:
    groups: dict[str, list[dict[str, Any]]] = {}
    for item in workstreams:
        group = item.get("parallel_group") or item.get("mode") or "serial"
        groups.setdefault(str(group), []).append(item)
    nodes = []
    for group, items in sorted(groups.items()):
        nodes.append(
            {
                "id": f"phase: {group}",
                "name": f"phase: {group}",
                "label": f"phase: {group}",
                "type": "phase",
                "status": _aggregate_status([item.get("status") for item in items]),
                "children": items,
            }
        )
    return nodes


def _aggregate_status(statuses: list[Any]) -> str:
    values = [str(status or "unknown").lower() for status in statuses]
    if not values:
        return "unknown"
    if any(status in {"failed", "error"} for status in values):
        return "failed"
    if any(status in {"blocked", "pending", "warning", "warn"} for status in values):
        return "blocked"
    if any(status in {"running", "assigned", "registered"} for status in values):
        return "running"
    if all(status in {"completed", "completed_with_concerns", "passed", "ok"} for status in values):
        return "completed"
    if any(status in {"planned", "queued", "unknown"} for status in values):
        return "queued"
    return values[0]


def _string_list_value(value: Any) -> list[str]:
    if isinstance(value, list):
        return [str(item) for item in value]
    return []


def _agent_detail(repo_root: Path, run_id: str, agent_id: str) -> dict[str, Any]:
    selected = resolve_run_dir(repo_root, run_id)
    if selected is None:
        return _run_error("missing_run", run_id=run_id)
    agent = read_agent(selected, agent_id)
    if agent is None:
        return _dashboard_error(
            "agent_not_found",
            f"Agent not found for run {selected.name}: {agent_id}",
            run_id=selected.name,
            state_dir=selected,
            extra={"agent_id": agent_id},
        )

    logs = _agent_logs(repo_root, run_id, agent_id)
    report_payload = _agent_report(repo_root, run_id, agent_id)
    report = report_payload.get("report") if report_payload.get("status") == "ok" else None
    changed_files = _changed_files_from_report(report)
    heartbeat_samples = _agent_heartbeat_samples(selected, agent_id)
    validation_evidence = _validation_evidence_detail(
        repo_root,
        run_id,
        selected,
        agent,
        report_path=report_payload.get("report_path"),
        terminal_report_present=report is not None,
    )
    profile = agent.get("capability_profile") if isinstance(agent.get("capability_profile"), dict) else {}
    capabilities = profile.get("capabilities") if isinstance(profile, dict) else {}
    capability_rows = [
        {"capability": key, "mode": value.get("mode")}
        for key, value in sorted(capabilities.items())
        if isinstance(value, dict)
    ]
    return {
        "kind": "agent_detail",
        "status": "ok",
        "run_id": selected.name,
        "state_dir": str(selected),
        "agent_id": agent_id,
        "agent": agent,
        "metadata": _agent_metadata(agent),
        "logs": logs,
        "report": report,
        "report_path": report_payload.get("report_path"),
        "changed_files": changed_files,
        "heartbeat_samples": heartbeat_samples,
        "validation_evidence": validation_evidence,
        "capability_grants": capability_rows,
        "capabilities_exercised": _list_from_report(report, "capabilities_exercised"),
        "capability_escalations": _list_from_report(report, "capability_escalations"),
        "empty_states": {
            "report": report is None,
            "changed_files": not changed_files,
            "heartbeat_samples": not heartbeat_samples,
            "validation_evidence": not validation_evidence.get("applicable"),
            "capability_grants": not capability_rows,
            "capabilities_exercised": not _list_from_report(report, "capabilities_exercised"),
            "capability_escalations": not _list_from_report(report, "capability_escalations"),
        },
    }


def _validation_evidence_detail(
    repo_root: Path,
    run_id: str,
    run_state_dir: Path,
    agent: dict[str, Any],
    *,
    report_path: Any,
    terminal_report_present: bool,
) -> dict[str, Any]:
    role = str(agent.get("role") or "")
    applicable = role in {"reviewer", "validator"}
    diagnostics = []
    if applicable:
        status_payload = run_status(repo_root, run_id=run_id)
        diagnostics = [
            item
            for item in status_payload.get("lifecycle_diagnostics", [])
            if item.get("agent_id") == agent.get("agent_id")
            and item.get("type") in {
                "incomplete_validation_evidence",
                "stale_validation_worker_without_report",
            }
        ]
    expected_report_path = report_path
    if not expected_report_path and applicable:
        directory = {"reviewer": "reviews", "validator": "validation"}[role]
        expected_report_path = str(run_state_dir / directory / f"{agent.get('agent_id')}.json")
    return {
        "applicable": applicable,
        "role": role or None,
        "expected_report_path": expected_report_path,
        "terminal_report_present": terminal_report_present,
        "last_heartbeat_at": agent.get("last_heartbeat_at"),
        "lifecycle_diagnostics": diagnostics,
        "empty_states": {
            "terminal_report": not terminal_report_present,
            "last_heartbeat_at": not bool(agent.get("last_heartbeat_at")),
            "lifecycle_diagnostics": not diagnostics,
        },
    }


def _agent_logs(repo_root: Path, run_id: str, agent_id: str) -> dict[str, Any]:
    selected = resolve_run_dir(repo_root, run_id)
    if selected is None:
        return _run_error("missing_run", run_id=run_id)
    agent = read_agent(selected, agent_id) or {}
    stdout_path = _agent_path_from_record(repo_root, selected, agent, "stdout_path") or selected / "logs" / f"{agent_id}.stdout.log"
    stderr_path = _agent_path_from_record(repo_root, selected, agent, "stderr_path") or selected / "logs" / f"{agent_id}.stderr.log"
    return {
        "kind": "agent_logs",
        "status": "ok",
        "run_id": selected.name,
        "state_dir": str(selected),
        "agent_id": agent_id,
        "stdout_path": str(stdout_path),
        "stderr_path": str(stderr_path),
        "stdout": _read_text_if_exists(stdout_path),
        "stderr": _read_text_if_exists(stderr_path),
    }


def _agent_report(repo_root: Path, run_id: str, agent_id: str) -> dict[str, Any]:
    selected = resolve_run_dir(repo_root, run_id)
    if selected is None:
        return _run_error("missing_run", run_id=run_id)
    agent = read_agent(selected, agent_id) or {}
    report_path = _agent_path_from_record(repo_root, selected, agent, "report_path")
    if report_path is None:
        directory = {"reviewer": "reviews", "validator": "validation"}.get(str(agent.get("role")), "reports")
        report_path = selected / directory / f"{agent_id}.json"
    report = _read_json_object(report_path)
    if report is None:
        return {
            "kind": "agent_report",
            "status": "not_found",
            "summary": f"No report yet for agent {agent_id}.",
            "run_id": selected.name,
            "state_dir": str(selected),
            "agent_id": agent_id,
            "report_path": str(report_path),
            "report": None,
        }
    return {
        "kind": "agent_report",
        "status": "ok",
        "run_id": selected.name,
        "state_dir": str(selected),
        "agent_id": agent_id,
        "report_path": str(report_path),
        "report": report,
    }


def _host_heartbeat(repo_root: Path, run_id: str) -> dict[str, Any]:
    selected = resolve_run_dir(repo_root, run_id)
    if selected is None:
        return _run_error("missing_run", run_id=run_id)

    record_path, record = _read_host_heartbeat_record(repo_root, selected)
    run = _read_json_object(selected / "run.json") or {}
    run_status_value = str(run.get("status") or "unknown").lower()
    terminal = run_status_value in {"completed", "completed_with_concerns", "cancelled", "failed"}
    if record is None:
        effective_status = "stopped" if terminal else "missing"
        source = "derived_terminal" if terminal else "missing"
        return {
            "kind": "host_heartbeat",
            "status": "ok",
            "run_id": selected.name,
            "state_dir": str(selected),
            "source": source,
            "source_path": None,
            "automation_id": None,
            "owner": "interactive-codex",
            "interval_seconds": 900,
            "heartbeat_status": "missing",
            "effective_status": effective_status,
            "active": False,
            "last_wakeup_at": None,
            "next_wakeup_at": None,
            "stopped_at": _first_present(run.get("completed_at"), run.get("cancelled_at"), run.get("failed_at"), run.get("updated_at")) if terminal else None,
            "stop_reason": "terminal run reached" if terminal else None,
            "last_observed_cursor": None,
            "updated_at": None,
            "empty_states": {
                "record": True,
                "last_wakeup_at": True,
                "next_wakeup_at": True,
            },
        }

    heartbeat_status = str(record.get("status") or "unknown").lower()
    effective_status = "stopped" if terminal and heartbeat_status in {"active", "running", "scheduled", "unknown"} else heartbeat_status
    active = effective_status in {"active", "running", "scheduled"} and not terminal
    interval_seconds = _int_or_default(record.get("interval_seconds") or record.get("interval"), 900)
    last_wakeup_at = _first_present(record.get("last_wakeup_at"), record.get("last_wake_at"), record.get("last_checked_at"))
    next_wakeup_at = _first_present(record.get("next_wakeup_at"), record.get("next_wake_at"))
    stopped_at = _first_present(record.get("stopped_at"), run.get("completed_at"), run.get("cancelled_at"), run.get("failed_at")) if not active else record.get("stopped_at")
    return {
        "kind": "host_heartbeat",
        "status": "ok",
        "run_id": selected.name,
        "state_dir": str(selected),
        "source": "record",
        "source_path": str(record_path),
        "automation_id": record.get("automation_id"),
        "owner": record.get("owner") or "interactive-codex",
        "interval_seconds": interval_seconds,
        "heartbeat_status": heartbeat_status,
        "effective_status": effective_status,
        "active": active,
        "last_wakeup_at": last_wakeup_at,
        "next_wakeup_at": next_wakeup_at,
        "stopped_at": stopped_at,
        "stop_reason": record.get("stop_reason") or ("terminal run reached" if terminal else None),
        "last_observed_cursor": record.get("last_observed_cursor"),
        "updated_at": record.get("updated_at"),
        "empty_states": {
            "record": False,
            "last_wakeup_at": not bool(last_wakeup_at),
            "next_wakeup_at": not bool(next_wakeup_at),
        },
    }


def _read_host_heartbeat_record(repo_root: Path, run_state_dir: Path) -> tuple[Path | None, dict[str, Any] | None]:
    candidates = [
        run_state_dir / "host-heartbeat.json",
        run_state_dir / "dashboard" / "host-heartbeat.json",
        repo_root / ".dispatch" / "host-heartbeat.json",
    ]
    for path in candidates:
        record = _read_json_object(path)
        if record is not None:
            return path, record
    return None, None


def _run_history(repo_root: Path) -> dict[str, Any]:
    root = runs_dir(repo_root)
    records = []
    if root.exists():
        for run_path in sorted([path for path in root.iterdir() if path.is_dir()], reverse=True):
            records.append(_history_record(repo_root, run_path))
    return {
        "kind": "history",
        "status": "ok",
        "repo_root": str(repo_root),
        "run_count": len(records),
        "runs": records,
        "empty_states": {
            "runs": not bool(records),
        },
    }


def _history_record(repo_root: Path, run_path: Path) -> dict[str, Any]:
    run = _read_json_object(run_path / "run.json") or {}
    plan = run.get("plan") if isinstance(run.get("plan"), dict) else {}
    agents = list_agents(run_path)
    decisions = _history_decisions(run_path, run)
    reports = _history_reports(run_path)
    validation = _history_validation_counts(reports)
    start = _first_present(run.get("started_at"), run.get("created_at"))
    completed = _first_present(
        run.get("completed_at"),
        run.get("cancelled_at"),
        run.get("failed_at"),
        run.get("ended_at"),
        run.get("updated_at"),
    )
    status = str(run.get("status") or "unknown")
    terminal_reason = _terminal_reason(run, status)
    return {
        "run_id": run.get("run_id") or run_path.name,
        "short_id": run_path.name[:8],
        "repo": str(run.get("repo_root") or repo_root),
        "repo_name": Path(str(run.get("repo_root") or repo_root)).name,
        "state_dir": str(run_path),
        "plan_id": plan.get("plan_id"),
        "objective": run.get("objective"),
        "status": status,
        "created_at": run.get("created_at"),
        "started_at": start,
        "updated_at": run.get("updated_at"),
        "completed_at": completed if status in {"completed", "completed_with_concerns", "failed", "cancelled"} else run.get("completed_at"),
        "duration_ms": _duration_ms(start, completed),
        "worker_count": sum(1 for agent in agents if agent.get("role") == "worker"),
        "agent_count": len(agents),
        "decision_count": len(decisions),
        "pending_decision_count": sum(1 for item in decisions if str(item.get("status") or "pending").lower() == "pending"),
        "files_changed_count": _history_changed_file_count(reports),
        "tests_passed": validation["passed"],
        "tests_total": validation["total"],
        "terminal_reason": terminal_reason,
        "dashboard_command_preview": (
            f"python3 scripts/de.py dashboard {shlex.quote(str(repo_root))} "
            f"--run-id {shlex.quote(run_path.name)} --detach --json"
        ),
        "empty_states": {
            "plan_id": not bool(plan.get("plan_id")),
            "objective": not bool(run.get("objective")),
            "duration": _duration_ms(start, completed) is None,
            "files_changed": _history_changed_file_count(reports) is None,
            "tests": validation["total"] is None,
            "terminal_reason": terminal_reason is None,
        },
    }


def _history_decisions(run_path: Path, run: dict[str, Any]) -> list[dict[str, Any]]:
    decisions = _read_jsonl_objects(run_path / "decisions.jsonl")
    if decisions:
        return decisions
    return [item for item in run.get("decisions", []) if isinstance(item, dict)]


def _history_reports(run_path: Path) -> list[dict[str, Any]]:
    reports: list[dict[str, Any]] = []
    for directory in ("reports", "reviews", "validation"):
        report_dir = run_path / directory
        if not report_dir.is_dir():
            continue
        for path in sorted(report_dir.glob("*.json")):
            report = _read_json_object(path)
            if report is not None:
                reports.append(report)
    return reports


def _history_changed_file_count(reports: list[dict[str, Any]]) -> int | None:
    paths: set[str] = set()
    saw_field = False
    for report in reports:
        changed = _changed_files_from_report(report)
        if changed:
            saw_field = True
        for item in changed:
            if isinstance(item, dict):
                path = item.get("path") or item.get("file")
            else:
                path = item
            if path:
                paths.add(str(path))
    if paths:
        return len(paths)
    return 0 if saw_field else None


def _history_validation_counts(reports: list[dict[str, Any]]) -> dict[str, int | None]:
    total = 0
    passed = 0
    for report in reports:
        validation = report.get("validation")
        if not isinstance(validation, list):
            continue
        for item in validation:
            if not isinstance(item, dict):
                continue
            total += 1
            if str(item.get("status") or "").lower() in {"passed", "ok", "completed"}:
                passed += 1
    return {"passed": passed if total else None, "total": total if total else None}


def _terminal_reason(run: dict[str, Any], status: str) -> str | None:
    if status == "cancelled":
        return run.get("cancellation_reason") or run.get("cancel_reason")
    if status == "failed":
        return run.get("failure_reason") or run.get("error") or run.get("reason")
    if status in {"completed", "completed_with_concerns"}:
        return run.get("completion_summary") or run.get("summary")
    return None


def _first_present(*values: Any) -> Any:
    for value in values:
        if value not in (None, ""):
            return value
    return None


def _duration_ms(start: Any, end: Any) -> int | None:
    start_dt = _parse_timestamp(start)
    end_dt = _parse_timestamp(end)
    if start_dt is None or end_dt is None or end_dt < start_dt:
        return None
    return int((end_dt - start_dt).total_seconds() * 1000)


def _int_or_default(value: Any, default: int) -> int:
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        return default
    return parsed if parsed > 0 else default


def _parse_timestamp(value: Any) -> datetime | None:
    if not isinstance(value, str) or not value:
        return None
    text = value.replace("Z", "+00:00")
    try:
        parsed = datetime.fromisoformat(text)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def _status_code_for_payload(payload: dict[str, Any]) -> HTTPStatus:
    status = payload.get("status")
    if payload.get("kind") == "error":
        if status == "invalid_event_cursor":
            return HTTPStatus.BAD_REQUEST
        if status in {"missing_run", "no_run", "not_found", "agent_not_found"}:
            return HTTPStatus.NOT_FOUND
        return HTTPStatus.INTERNAL_SERVER_ERROR
    if status in {"missing_run", "no_run"}:
        return HTTPStatus.NOT_FOUND
    if status == "invalid_event_cursor":
        return HTTPStatus.BAD_REQUEST
    return HTTPStatus.OK


def _static_asset_path(dashboard_dir: Path, request_path: str) -> Path | None:
    raw = unquote(request_path.split("?", 1)[0])
    if raw in {"", "/"}:
        raw = "/index.html"
    relative = raw.lstrip("/")
    candidate = (dashboard_dir / relative).resolve()
    try:
        candidate.relative_to(dashboard_dir.resolve())
    except ValueError:
        return None
    return candidate


def _resolve_dashboard_dir(dashboard_dir: Path | None) -> Path:
    if dashboard_dir is not None:
        return dashboard_dir.resolve()
    return (Path(__file__).resolve().parents[2] / "dashboard").resolve()


def _validate_dashboard_assets(dashboard_dir: Path) -> str | None:
    index = dashboard_dir / "index.html"
    if not dashboard_dir.is_dir() or not index.is_file():
        return f"Dashboard assets are missing; expected dashboard/index.html at {index}."
    return None


def _metadata_record(
    *,
    repo_root: Path,
    run_state_dir: Path,
    dashboard_dir: Path,
    host: str,
    port: int,
    url: str,
    pid: int,
    status: str,
) -> dict[str, Any]:
    now = utc_timestamp()
    dashboard_state = _dashboard_state_dir(run_state_dir)
    return {
        "schema_version": DASHBOARD_SCHEMA_VERSION,
        "kind": "dashboard_server",
        "status": status,
        "alive": status == "running",
        "run_id": run_state_dir.name,
        "repo_root": str(repo_root),
        "state_dir": str(run_state_dir),
        "dashboard_dir": str(dashboard_dir),
        "host": host,
        "port": port,
        "url": url,
        "pid": pid,
        "created_at": now,
        "updated_at": now,
        "metadata_path": str(_metadata_path(run_state_dir)),
        "stdout_path": str(dashboard_state / "server.stdout.log"),
        "stderr_path": str(dashboard_state / "server.stderr.log"),
    }


def _dashboard_payload(
    record: dict[str, Any],
    *,
    status: str,
    alive: bool,
    state_dir: Path,
    dashboard_dir: Path,
) -> dict[str, Any]:
    return {
        "kind": "dashboard",
        "status": status,
        "summary": f"Dashboard service for run {state_dir.name} is {status}.",
        "run_id": state_dir.name,
        "state_dir": str(state_dir),
        "dashboard_dir": str(dashboard_dir),
        "metadata_path": str(_metadata_path(state_dir)),
        "stdout_path": str(_dashboard_state_dir(state_dir) / "server.stdout.log"),
        "stderr_path": str(_dashboard_state_dir(state_dir) / "server.stderr.log"),
        "url": record.get("url"),
        "pid": _coerce_pid(record.get("pid")),
        "alive": alive,
        "host": record.get("host"),
        "port": record.get("port"),
    }


def _dashboard_status_payload(
    record: dict[str, Any],
    *,
    status: str,
    alive: bool,
    state_dir: Path,
) -> dict[str, Any]:
    return {
        "kind": "dashboard_status",
        "status": status,
        "summary": f"Dashboard service for run {state_dir.name} is {status}.",
        "run_id": state_dir.name,
        "state_dir": str(state_dir),
        "dashboard_dir": record.get("dashboard_dir"),
        "metadata_path": str(_metadata_path(state_dir)),
        "stdout_path": record.get("stdout_path"),
        "stderr_path": record.get("stderr_path"),
        "url": record.get("url"),
        "pid": _coerce_pid(record.get("pid")),
        "alive": alive,
        "host": record.get("host"),
        "port": record.get("port"),
    }


def _dashboard_error(
    status: str,
    summary: str,
    *,
    run_id: str | None,
    state_dir: Path | None = None,
    dashboard_dir: Path | None = None,
    extra: dict[str, Any] | None = None,
) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "kind": "error",
        "status": status,
        "summary": summary,
    }
    if run_id:
        payload["run_id"] = run_id
    if state_dir is not None:
        payload["state_dir"] = str(state_dir)
    if dashboard_dir is not None:
        payload["dashboard_dir"] = str(dashboard_dir)
    if extra:
        payload.update(extra)
    return payload


def _run_error(status: str, *, run_id: str | None = None) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "kind": "error",
        "status": status,
        "summary": f"Run not found: {run_id}" if run_id else "No Dispatch Engine runs found.",
    }
    if run_id:
        payload["run_id"] = run_id
    return payload


def _metadata_path(run_state_dir: Path) -> Path:
    return _dashboard_state_dir(run_state_dir) / "server.json"


def _dashboard_state_dir(run_state_dir: Path) -> Path:
    return run_state_dir / "dashboard"


def _read_metadata(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return None
    return data if isinstance(data, dict) else None


def _write_metadata(path: Path, record: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = path.with_name(f".{path.name}.tmp")
    tmp_path.write_text(json.dumps(record, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    tmp_path.replace(path)


def _server_is_alive(record: dict[str, Any]) -> bool:
    pid = _coerce_pid(record.get("pid"))
    host = record.get("host")
    port = record.get("port")
    if pid is None or not isinstance(host, str) or not isinstance(port, int):
        return False
    return _pid_is_alive(pid) and _tcp_connects(host, port)


def _pid_is_alive(pid: int) -> bool:
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    except OSError:
        return False
    return True


def _coerce_pid(value: Any) -> int | None:
    if isinstance(value, bool) or value is None:
        return None
    try:
        pid = int(value)
    except (TypeError, ValueError):
        return None
    return pid if pid > 0 else None


def _tcp_connects(host: str, port: int) -> bool:
    try:
        with socket.create_connection((host, port), timeout=0.2):
            return True
    except OSError:
        return False


def _terminate_pid(pid: int) -> bool:
    try:
        os.kill(pid, signal.SIGTERM)
    except ProcessLookupError:
        return False
    except OSError:
        return False
    return True


def _kill_pid(pid: int) -> bool:
    try:
        os.kill(pid, signal.SIGKILL)
    except ProcessLookupError:
        return False
    except OSError:
        return False
    return True


def _detached_env() -> dict[str, str]:
    env = dict(os.environ)
    scripts_dir = Path(__file__).resolve().parents[1]
    current = env.get("PYTHONPATH")
    env["PYTHONPATH"] = str(scripts_dir) if not current else f"{scripts_dir}{os.pathsep}{current}"
    return env


def _read_text_if_exists(path: Path) -> str:
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8")


def _read_json_object(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return None
    return data if isinstance(data, dict) else None


def _read_jsonl_objects(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    records = []
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except OSError:
        return []
    for line in lines:
        if not line.strip():
            continue
        try:
            data = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(data, dict):
            records.append(data)
    return records


def _agent_path_from_record(repo_root: Path, run_state_dir: Path, agent: dict[str, Any], field: str) -> Path | None:
    value = agent.get(field)
    if not isinstance(value, str) or not value:
        return None
    raw_path = Path(value)
    if raw_path.is_absolute():
        return raw_path
    if value.startswith(".dispatch/"):
        return repo_root / raw_path
    return run_state_dir / raw_path


def _agent_heartbeat_samples(run_state_dir: Path, agent_id: str) -> list[dict[str, Any]]:
    jsonl_path = run_state_dir / "heartbeats" / f"{agent_id}.jsonl"
    samples = _read_jsonl_objects(jsonl_path)
    json_path = run_state_dir / "heartbeats" / f"{agent_id}.json"
    latest = _read_json_object(json_path)
    if latest is not None:
        samples.append(latest)
    return samples[-40:]


def _agent_metadata(agent: dict[str, Any]) -> dict[str, Any]:
    profile = agent.get("capability_profile") if isinstance(agent.get("capability_profile"), dict) else {}
    scope = profile.get("repo_write_scope") if isinstance(profile, dict) else {}
    return {
        "id": agent.get("agent_id"),
        "role": agent.get("role"),
        "spawned_by": agent.get("spawned_by") or agent.get("parent_agent_id"),
        "spawned_at": agent.get("started_at") or agent.get("created_at"),
        "workstream": agent.get("workstream"),
        "capability_profile": profile.get("profile_id") if isinstance(profile, dict) else agent.get("profile"),
        "permission_scope": scope if isinstance(scope, dict) else None,
        "provider": agent.get("provider"),
        "prompt_path": agent.get("prompt_path"),
        "report_path": agent.get("report_path"),
        "launch_evidence": agent.get("launch_evidence") or agent.get("provider_native_spawn_ref"),
    }


def _changed_files_from_report(report: Any) -> list[Any]:
    if not isinstance(report, dict):
        return []
    for key in ("changed_files", "files_changed"):
        value = report.get(key)
        if isinstance(value, list):
            return value
    return []


def _list_from_report(report: Any, key: str) -> list[Any]:
    if not isinstance(report, dict):
        return []
    value = report.get(key)
    return value if isinstance(value, list) else []


def _tail_text(path: Path, *, max_chars: int = 4000) -> str:
    text = _read_text_if_exists(path)
    if len(text) <= max_chars:
        return text
    return text[-max_chars:]
