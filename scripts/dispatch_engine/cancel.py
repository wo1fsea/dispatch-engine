"""Run cancellation control for Dispatch Engine."""

from __future__ import annotations

import errno
import json
import os
import signal
import time
from pathlib import Path
from typing import Any

from .events import run_cancel_completed, run_cancel_requested, run_cancel_signal, utc_timestamp
from .runs import resolve_run_dir

DEFAULT_CANCELLATION_REASON = "User requested cancellation."
CANCEL_ACTOR = "interactive-codex"
TERMINAL_AGENT_STATUSES = frozenset({"completed", "failed", "cancelled"})
DEFAULT_GRACE_SECONDS = 1.0


class DefaultProcessController:
    """Small adapter around OS process signalling for cancel tests."""

    graceful_signal_name = "SIGTERM" if hasattr(signal, "SIGTERM") else "terminate"
    escalation_signal_name = "SIGKILL" if hasattr(signal, "SIGKILL") else "kill"

    def is_alive(self, pid: int) -> bool:
        try:
            os.kill(pid, 0)
        except ProcessLookupError:
            return False
        except SystemError:
            return False
        except OSError as exc:
            if exc.errno == errno.ESRCH:
                return False
            return True
        return True

    def graceful(self, pid: int) -> None:
        os.kill(pid, _signal_value("SIGTERM", "SIGINT"))

    def graceful_group(self, pid: int) -> None:
        if not hasattr(os, "killpg"):
            os.kill(pid, _signal_value("SIGTERM", "SIGINT"))
            return
        try:
            os.killpg(pid, _signal_value("SIGTERM", "SIGINT"))
        except ProcessLookupError:
            os.kill(pid, _signal_value("SIGTERM", "SIGINT"))

    def is_alive_after_grace(self, pid: int, grace_seconds: float) -> bool:
        if grace_seconds > 0:
            time.sleep(grace_seconds)
        return self.is_alive(pid)

    def escalate(self, pid: int) -> None:
        os.kill(pid, _signal_value("SIGKILL", "SIGTERM"))

    def escalate_group(self, pid: int) -> None:
        if not hasattr(os, "killpg"):
            os.kill(pid, _signal_value("SIGKILL", "SIGTERM"))
            return
        try:
            os.killpg(pid, _signal_value("SIGKILL", "SIGTERM"))
        except ProcessLookupError:
            os.kill(pid, _signal_value("SIGKILL", "SIGTERM"))


def cancel_run(
    target: Path,
    *,
    run_id: str | None = None,
    reason: str | None = None,
    process_controller: Any | None = None,
    grace_seconds: float = DEFAULT_GRACE_SECONDS,
) -> dict[str, Any]:
    """Cancel the selected Dispatch Engine run and return a JSON-ready payload."""

    repo_root = target.resolve()
    selected = resolve_run_dir(repo_root, run_id)
    if selected is None:
        return _run_error("missing_run" if run_id else "no_run", run_id=run_id)

    resolved_reason = reason or DEFAULT_CANCELLATION_REASON
    run_file = selected / "run.json"
    try:
        run = _read_json(run_file)
    except (FileNotFoundError, json.JSONDecodeError, OSError) as exc:
        return _state_error(selected, f"Cannot read run state: {exc}")
    if not isinstance(run, dict):
        return _state_error(selected, "Run state must be a JSON object.")

    status = run.get("status")
    event_log = selected / "events.jsonl"
    if status == "cancelled":
        stored_reason = str(run.get("cancellation_reason") or resolved_reason)
        requested_event = run_cancel_requested(
            event_log,
            run_id=selected.name,
            reason=stored_reason,
            selected_by="explicit" if run_id else "latest",
            actor=CANCEL_ACTOR,
        )
        completed_event = run_cancel_completed(
            event_log,
            run_id=selected.name,
            reason=stored_reason,
            updated_agents=[],
            signals=[],
            already_cancelled=True,
            actor=CANCEL_ACTOR,
        )
        return _success_payload(
            selected,
            reason=stored_reason,
            already_terminal=True,
            signals=[],
            updated_agents=[],
            events=[requested_event, completed_event],
        )
    if status in {"completed", "failed"}:
        return {
            "kind": "error",
            "status": "run_already_terminal",
            "summary": f"Run {selected.name} is already terminal: {status}",
            "run_id": selected.name,
            "state_dir": str(selected),
        }

    try:
        supervisors = _read_json_records(selected / "supervisors")
        agents = _read_json_records(selected / "agents")
    except (json.JSONDecodeError, OSError) as exc:
        return _state_error(selected, f"Cannot read run process state: {exc}")
    malformed_record = _malformed_record_reason([*supervisors, *agents])
    if malformed_record is not None:
        return _state_error(selected, malformed_record)

    requested_event = run_cancel_requested(
        event_log,
        run_id=selected.name,
        reason=resolved_reason,
        selected_by="explicit" if run_id else "latest",
        actor=CANCEL_ACTOR,
    )

    controller = process_controller or DefaultProcessController()
    active_supervisors = [_record for _record in supervisors if not _is_terminal(_record)]
    signal_results = [
        _signal_supervisor(record, process_controller=controller, grace_seconds=grace_seconds)
        for record in active_supervisors
    ]
    if not signal_results and not _active_agent_pids(agents):
        signal_results.append(
            {
                "target": "process_state",
                "agent_id": None,
                "pid": None,
                "graceful_signal": getattr(controller, "graceful_signal_name", "terminate"),
                "graceful_sent": False,
                "escalation_signal": None,
                "escalated": False,
                "final_state": "missing_pid",
            }
        )

    for agent in agents:
        if _is_terminal(agent):
            continue
        pid = agent.get("pid")
        if not isinstance(pid, int):
            continue
        signal_results.append(
            _signal_process(
                target=str(agent.get("role") or "agent"),
                agent_id=agent.get("agent_id"),
                pid=pid,
                process_controller=controller,
                grace_seconds=grace_seconds,
            )
        )

    for result in signal_results:
        run_cancel_signal(event_log, signal=result, actor=CANCEL_ACTOR)

    now = utc_timestamp()
    run["status"] = "cancelled"
    run["updated_at"] = now
    run["cancelled_at"] = now
    run["cancelled_by"] = CANCEL_ACTOR
    run["cancellation_reason"] = resolved_reason
    _write_json(run_file, run)

    signal_by_supervisor = {
        str(result.get("agent_id") or ""): result
        for result in signal_results
        if result.get("target") == "supervisor"
    }
    for supervisor in active_supervisors:
        supervisor["status"] = "cancelled"
        supervisor["updated_at"] = now
        supervisor["completed_at"] = now
        supervisor["cancellation_reason"] = resolved_reason
        signal = signal_by_supervisor.get(str(supervisor.get("agent_id") or ""))
        if signal is not None:
            supervisor["cancel_signal"] = _supervisor_signal_record(signal)
        _write_record(selected / "supervisors", supervisor)

    updated_agents = []
    for agent in agents:
        if _is_terminal(agent):
            continue
        agent["status"] = "cancelled"
        agent["updated_at"] = now
        agent["completed_at"] = now
        agent["cancellation_reason"] = resolved_reason
        _write_record(selected / "agents", agent)
        agent_id = agent.get("agent_id")
        if isinstance(agent_id, str) and agent_id:
            updated_agents.append(agent_id)
    updated_agents = sorted(updated_agents)

    completed_event = run_cancel_completed(
        event_log,
        run_id=selected.name,
        reason=resolved_reason,
        updated_agents=updated_agents,
        signals=signal_results,
        already_cancelled=False,
        actor=CANCEL_ACTOR,
    )
    event_names = [requested_event]
    if signal_results:
        event_names.append("run.cancel.signal")
    event_names.append(completed_event)
    return _success_payload(
        selected,
        reason=resolved_reason,
        already_terminal=False,
        signals=signal_results,
        updated_agents=updated_agents,
        events=event_names,
    )


def _signal_supervisor(
    record: dict[str, Any],
    *,
    process_controller: Any,
    grace_seconds: float,
) -> dict[str, Any]:
    pid = record.get("supervisor_pid")
    return _signal_process(
        target="supervisor",
        agent_id=record.get("agent_id"),
        pid=pid if isinstance(pid, int) else None,
        process_controller=process_controller,
        grace_seconds=grace_seconds,
        process_group=True,
    )


def _signal_process(
    *,
    target: str,
    agent_id: Any,
    pid: int | None,
    process_controller: Any,
    grace_seconds: float,
    process_group: bool = False,
) -> dict[str, Any]:
    graceful_signal = getattr(process_controller, "graceful_signal_name", "terminate")
    escalation_signal = getattr(process_controller, "escalation_signal_name", "kill")
    result = {
        "target": target,
        "agent_id": agent_id,
        "pid": pid,
        "graceful_signal": graceful_signal,
        "graceful_sent": False,
        "escalation_signal": None,
        "escalated": False,
        "final_state": "missing_pid",
    }
    if pid is None:
        return result

    try:
        alive = process_controller.is_alive(pid)
    except OSError as exc:
        result["final_state"] = f"signal_error: {exc}"
        return result
    if not alive:
        result["final_state"] = "not_running"
        return result

    try:
        if process_group and hasattr(process_controller, "graceful_group"):
            process_controller.graceful_group(pid)
        else:
            process_controller.graceful(pid)
    except ProcessLookupError:
        result["final_state"] = "not_running"
        return result
    except PermissionError:
        result["final_state"] = "permission_denied"
        return result
    except OSError as exc:
        result["final_state"] = f"signal_error: {exc}"
        return result

    result["graceful_sent"] = True
    try:
        alive_after_grace = process_controller.is_alive_after_grace(pid, grace_seconds)
    except OSError as exc:
        result["final_state"] = f"signal_error: {exc}"
        return result
    if not alive_after_grace:
        result["final_state"] = "terminated"
        return result

    try:
        if process_group and hasattr(process_controller, "escalate_group"):
            process_controller.escalate_group(pid)
        else:
            process_controller.escalate(pid)
    except ProcessLookupError:
        result["final_state"] = "terminated"
        return result
    except PermissionError:
        result["escalation_signal"] = escalation_signal
        result["final_state"] = "permission_denied"
        return result
    except OSError as exc:
        result["escalation_signal"] = escalation_signal
        result["final_state"] = f"signal_error: {exc}"
        return result

    result["escalation_signal"] = escalation_signal
    result["escalated"] = True
    result["final_state"] = "terminated_after_escalation"
    return result


def _read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _read_json_records(directory: Path) -> list[dict[str, Any]]:
    if not directory.exists():
        return []
    records = []
    for path in sorted(directory.glob("*.json")):
        record = _read_json(path)
        if not isinstance(record, dict):
            raise json.JSONDecodeError("record must be a JSON object", path.name, 0)
        records.append(record)
    return records


def _write_record(directory: Path, record: dict[str, Any]) -> None:
    record_id = record.get("agent_id")
    _write_json(directory / f"{record_id}.json", record)


def _write_json(path: Path, record: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = path.with_name(f".{path.name}.tmp")
    tmp_path.write_text(json.dumps(record, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    tmp_path.replace(path)


def _is_terminal(record: dict[str, Any]) -> bool:
    return record.get("status") in TERMINAL_AGENT_STATUSES


def _malformed_record_reason(records: list[dict[str, Any]]) -> str | None:
    for record in records:
        record_id = record.get("agent_id")
        if not isinstance(record_id, str) or not record_id:
            return "Process state record has no agent_id."
    return None


def _active_agent_pids(agents: list[dict[str, Any]]) -> list[int]:
    return [
        agent["pid"]
        for agent in agents
        if not _is_terminal(agent) and isinstance(agent.get("pid"), int)
    ]


def _supervisor_signal_record(signal_result: dict[str, Any]) -> dict[str, Any]:
    return {
        "graceful_signal": signal_result.get("graceful_signal"),
        "graceful_sent": signal_result.get("graceful_sent"),
        "escalation_signal": signal_result.get("escalation_signal"),
        "escalated": signal_result.get("escalated"),
        "final_state": signal_result.get("final_state"),
    }


def _success_payload(
    state_dir: Path,
    *,
    reason: str,
    already_terminal: bool,
    signals: list[dict[str, Any]],
    updated_agents: list[str],
    events: list[str],
) -> dict[str, Any]:
    return {
        "kind": "run_cancel",
        "status": "cancelled",
        "run_id": state_dir.name,
        "state_dir": str(state_dir),
        "reason": reason,
        "already_terminal": already_terminal,
        "signals": signals,
        "updated_agents": updated_agents,
        "events": events,
    }


def _run_error(status: str, *, run_id: str | None) -> dict[str, Any]:
    summary = f"Run not found: {run_id}" if run_id else "No Dispatch Engine runs found."
    result = {"kind": "error", "status": status, "summary": summary}
    if run_id:
        result["run_id"] = run_id
    return result


def _state_error(state_dir: Path, summary: str) -> dict[str, Any]:
    return {
        "kind": "error",
        "status": "cancel_state_error",
        "summary": summary,
        "run_id": state_dir.name,
        "state_dir": str(state_dir),
    }


def _signal_value(name: str, fallback_name: str) -> int:
    signum = getattr(signal, name, None)
    if signum is None:
        signum = getattr(signal, fallback_name)
    return int(signum)
