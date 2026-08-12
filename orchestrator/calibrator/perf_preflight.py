# -*- coding: utf-8 -*-
"""Floor campaign 用 ``perf stat`` 可用性 preflight。

実測 command は runner と同じ event 列と ``-o`` 形を使う。receipt の一時 path は
artifact を揮発させないよう ``<tmp>/perf.csv`` に正規化して記録する。
"""
from __future__ import annotations

import hashlib
import subprocess
import tempfile
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Callable

from .runner import PERF_EVENTS


SCHEMA = "izanagi-perf-preflight/v1"
PROBE_TIMEOUT_S = 10.0
_OUTPUT_TOKEN = "<tmp>/perf.csv"
_BASE_PROBE_ARGV = (
    "perf", "stat", "-x,", "-o", _OUTPUT_TOKEN,
    "-e", ",".join(PERF_EVENTS), "--", "/bin/true",
)
_RECEIPT_KEYS = {
    "schema", "status", "available", "probe_argv", "rc",
    "parsed_events", "reason", "stderr_sha256", "candidates",
}
_CANDIDATE_KEYS = {"path", "rc", "executable"}
_ERROR_REASONS = {"probe-timeout", "probe-os-error", "probe-signal"}


class PerfPreflightError(ValueError):
    """receipt または probe 契約が不正、または判定不能。"""


def _sha256_text(value: object) -> str:
    text = value if isinstance(value, str) else ""
    return hashlib.sha256(text.encode("utf-8", errors="replace")).hexdigest()


def _runtime_argv(executable: str, output_path: Path) -> list[str]:
    return [
        executable, "stat", "-x,", "-o", str(output_path),
        "-e", ",".join(PERF_EVENTS), "--", "/bin/true",
    ]


def _event_name(raw: str) -> str | None:
    event = raw.strip().strip('"').split(":", 1)[0]
    for requested in PERF_EVENTS:
        if event.lower() == requested.lower():
            return requested
    return None


def _present_events(text: str) -> list[str]:
    present: set[str] = set()
    for line in text.splitlines():
        fields = line.split(",")
        if len(fields) >= 3:
            event = _event_name(fields[2])
            if event is not None:
                present.add(event)
    return [event for event in PERF_EVENTS if event in present]


def _candidate_evidence(
        path: str, *, subprocess_runner: Callable[..., object], timeout_s: float,
        directory: Path) -> dict:
    output_path = directory / f"candidate-{hashlib.sha256(path.encode()).hexdigest()}.csv"
    try:
        proc = subprocess_runner(
            _runtime_argv(path, output_path), capture_output=True, text=True,
            timeout=timeout_s,
        )
    except (FileNotFoundError, PermissionError):
        return {"path": path, "rc": None, "executable": False}
    except (subprocess.TimeoutExpired, OSError, UnicodeError):
        return {"path": path, "rc": None, "executable": False}
    rc = getattr(proc, "returncode", None)
    if type(rc) is not int:
        return {"path": path, "rc": None, "executable": False}
    return {"path": path, "rc": rc, "executable": True}


def probe_perf_availability(
        *, perf_candidates: Sequence[str] = (),
        subprocess_runner: Callable[..., object] = subprocess.run,
        timeout_s: float = PROBE_TIMEOUT_S) -> dict:
    """literal ``perf`` を probe し、policy 候補は evidence としてだけ実行する。"""
    if (isinstance(perf_candidates, (str, bytes))
            or not isinstance(perf_candidates, Sequence)
            or not all(isinstance(path, str) and path for path in perf_candidates)):
        raise PerfPreflightError("perf_candidates が空でない str の sequence でない")
    if not isinstance(timeout_s, (int, float)) or isinstance(timeout_s, bool) or timeout_s <= 0:
        raise PerfPreflightError("timeout_s が正数でない")

    with tempfile.TemporaryDirectory(prefix="izanagi_perf_preflight_") as tmp:
        directory = Path(tmp)
        output_path = directory / "perf.csv"
        rc = None
        stderr = ""
        parsed_events: list[str] = []
        status = "probe_error"
        available = False
        reason = "probe-os-error"
        try:
            proc = subprocess_runner(
                _runtime_argv("perf", output_path), capture_output=True, text=True,
                timeout=timeout_s,
            )
            rc = getattr(proc, "returncode", None)
            stderr = getattr(proc, "stderr", "") or ""
            if type(rc) is not int:
                reason = "probe-os-error"
            elif rc < 0:
                reason = "probe-signal"
            elif rc != 0:
                status = "unavailable"
                reason = "nonzero-rc"
            else:
                try:
                    output = output_path.read_text(encoding="utf-8")
                except (OSError, UnicodeError) as exc:
                    stderr = f"{stderr}\n{exc}"
                    reason = "probe-os-error"
                else:
                    parsed_events = _present_events(output)
                    status = "available" if parsed_events == PERF_EVENTS else "unavailable"
                    available = status == "available"
                    reason = "available" if available else "requested-events-missing"
        except FileNotFoundError as exc:
            status = "unavailable"
            reason = "perf-not-found"
            stderr = str(exc)
        except subprocess.TimeoutExpired as exc:
            reason = "probe-timeout"
            stderr = str(exc)
        except (OSError, UnicodeError) as exc:
            reason = "probe-os-error"
            stderr = str(exc)

        candidates = [
            _candidate_evidence(
                path, subprocess_runner=subprocess_runner, timeout_s=timeout_s,
                directory=directory,
            )
            for path in perf_candidates
        ]

    receipt = {
        "schema": SCHEMA,
        "status": status,
        "available": available,
        "probe_argv": list(_BASE_PROBE_ARGV),
        "rc": rc,
        "parsed_events": parsed_events,
        "reason": reason,
        "stderr_sha256": _sha256_text(stderr),
        "candidates": candidates,
    }
    return validate_perf_preflight_receipt(receipt)


def validate_perf_preflight_receipt(receipt: object) -> dict:
    """closed schema と判定表から receipt の相互整合を再導出する。"""
    if not isinstance(receipt, Mapping) or set(receipt) != _RECEIPT_KEYS:
        raise PerfPreflightError("perf preflight receipt の exact key 集合が不一致")
    if receipt.get("schema") != SCHEMA:
        raise PerfPreflightError("perf preflight receipt.schema が不一致")
    if receipt.get("probe_argv") != list(_BASE_PROBE_ARGV):
        raise PerfPreflightError("perf preflight receipt.probe_argv が不一致")
    if type(receipt.get("available")) is not bool:
        raise PerfPreflightError("perf preflight receipt.available が bool でない")
    if type(receipt.get("rc")) is not int and receipt.get("rc") is not None:
        raise PerfPreflightError("perf preflight receipt.rc が int/null でない")
    parsed = receipt.get("parsed_events")
    if (not isinstance(parsed, list)
            or not all(isinstance(event, str) for event in parsed)
            or len(set(parsed)) != len(parsed)
            or parsed != [event for event in PERF_EVENTS if event in parsed]):
        raise PerfPreflightError("perf preflight receipt.parsed_events が canonical subset でない")
    digest = receipt.get("stderr_sha256")
    if (not isinstance(digest, str) or len(digest) != 64
            or any(ch not in "0123456789abcdef" for ch in digest)):
        raise PerfPreflightError("perf preflight receipt.stderr_sha256 が sha256 でない")

    status = receipt.get("status")
    reason = receipt.get("reason")
    rc = receipt.get("rc")
    available = receipt.get("available")
    if status == "available":
        consistent = available is True and rc == 0 and reason == "available" and parsed == PERF_EVENTS
    elif status == "unavailable":
        consistent = available is False and (
            (reason == "nonzero-rc" and type(rc) is int and rc > 0 and parsed == [])
            or (reason == "perf-not-found" and rc is None and parsed == [])
            or (reason == "requested-events-missing" and rc == 0 and parsed != PERF_EVENTS)
        )
    elif status == "probe_error":
        consistent = available is False and reason in _ERROR_REASONS and (
            (reason == "probe-signal" and type(rc) is int and rc < 0)
            or (reason == "probe-timeout" and rc is None)
            or (reason == "probe-os-error"
                and (rc is None or (type(rc) is int and rc >= 0)))
        )
    else:
        consistent = False
    if not consistent:
        raise PerfPreflightError("perf preflight receipt の status/判定内容が不整合")

    candidates = receipt.get("candidates")
    if not isinstance(candidates, list):
        raise PerfPreflightError("perf preflight receipt.candidates が list でない")
    normalized_candidates = []
    seen_paths: set[str] = set()
    for candidate in candidates:
        if not isinstance(candidate, Mapping) or set(candidate) != _CANDIDATE_KEYS:
            raise PerfPreflightError("perf preflight candidate の exact key 集合が不一致")
        path = candidate.get("path")
        candidate_rc = candidate.get("rc")
        executable = candidate.get("executable")
        if (not isinstance(path, str) or not path or path in seen_paths
                or type(executable) is not bool
                or (type(candidate_rc) is not int and candidate_rc is not None)
                or (executable and type(candidate_rc) is not int)
                or (not executable and candidate_rc is not None)):
            raise PerfPreflightError("perf preflight candidate が不整合")
        seen_paths.add(path)
        normalized_candidates.append({
            "path": path, "rc": candidate_rc, "executable": executable,
        })

    return {
        "schema": SCHEMA,
        "status": status,
        "available": available,
        "probe_argv": list(_BASE_PROBE_ARGV),
        "rc": rc,
        "parsed_events": list(parsed),
        "reason": reason,
        "stderr_sha256": digest,
        "candidates": normalized_candidates,
    }


def use_perf_from_receipt(receipt: object | None) -> bool:
    """legacy field 不在だけを perf ありと解釈する唯一の入口。"""
    if receipt is None:
        return True
    normalized = validate_perf_preflight_receipt(receipt)
    if normalized["status"] == "probe_error":
        raise PerfPreflightError(
            f"perf preflight が判定不能: {normalized['reason']}"
        )
    return normalized["available"]
