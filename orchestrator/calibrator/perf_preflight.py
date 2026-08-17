# -*- coding: utf-8 -*-
"""Floor campaign 用 ``perf stat`` 可用性 preflight。

実測 command は runner と同じ event 列と ``-o`` 形を使う。receipt の一時 path は
artifact を揮発させないよう ``<tmp>/perf.csv`` に正規化して記録する。
"""
from __future__ import annotations

import hashlib
import shlex
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
_OBSERVATION_KEYS = {
    "use_perf", "counter_status", "missing_leading_indicators", "preflight",
}
_CLAIM_SCOPE = {
    "throughput": "eligible",
    "perf_required": "unsupported",
}
_PERF_LEADING_INDICATORS = ("llc_miss_rate", "ipc")
_RAW_PERF_FIELD_NAMES = set(PERF_EVENTS) | {
    "llc_load_misses", "llc_loads", "instructions", "cycles",
}


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


def _missing_leading_indicators(value: object) -> list[str]:
    if not isinstance(value, list):
        raise PerfPreflightError(
            "perf observation.missing_leading_indicators が list でない"
        )
    if (not all(isinstance(name, str) for name in value)
            or any(name not in _PERF_LEADING_INDICATORS for name in value)
            or len(set(value)) != len(value)):
        raise PerfPreflightError(
            "perf observation.missing_leading_indicators が canonical subset でない"
        )
    return list(value)


def _measurement_argv(run_cmd: object) -> list[str]:
    if isinstance(run_cmd, str):
        try:
            argv = shlex.split(run_cmd)
        except ValueError as exc:
            raise PerfPreflightError("measurement run_cmd を argv 化できない") from exc
    elif (isinstance(run_cmd, Sequence)
            and not isinstance(run_cmd, (str, bytes))
            and all(isinstance(token, str) for token in run_cmd)):
        argv = list(run_cmd)
    else:
        raise PerfPreflightError("measurement run_cmd が str または str の argv でない")
    if not argv:
        raise PerfPreflightError("measurement run_cmd が空である")
    return argv


def _has_perf_stat_prefix(argv: Sequence[str]) -> bool:
    return any(
        Path(first).name == "perf" and Path(second).name == "stat"
        for first, second in zip(argv, argv[1:])
    )


def _validate_null_perf_values(value: object, *, path: str) -> None:
    """degraded 成果物内に残った perf raw 値を入れ子も含めて拒否する。"""
    if isinstance(value, Mapping):
        for key, child in value.items():
            child_path = f"{path}.{key}"
            if key == "perf_raw":
                if not isinstance(child, Mapping) or set(child) != set(PERF_EVENTS):
                    raise PerfPreflightError(
                        f"{child_path} の exact event 集合が不一致"
                    )
                if any(raw is not None for raw in child.values()):
                    raise PerfPreflightError(
                        f"{child_path} に non-null perf raw 値がある"
                    )
            elif key in _RAW_PERF_FIELD_NAMES and child is not None:
                raise PerfPreflightError(
                    f"{child_path} に non-null perf raw 値がある"
                )
            _validate_null_perf_values(child, path=child_path)
    elif isinstance(value, Sequence) and not isinstance(value, (str, bytes)):
        for index, child in enumerate(value):
            _validate_null_perf_values(child, path=f"{path}[{index}]")


def build_perf_observation(
        receipt: object | None, *, run_cmd: object,
        leading_indicators: Mapping[str, object]) -> dict | None:
    """receipt と測定値から canonical observation を作る。

    ``None`` receipt は legacy/perf-present の field 不在をそのまま保つ。
    """
    if receipt is None:
        return None
    if not isinstance(leading_indicators, Mapping):
        raise PerfPreflightError("leading_indicators が object でない")
    normalized_receipt = validate_perf_preflight_receipt(receipt)
    use_perf = use_perf_from_receipt(normalized_receipt)
    missing = (
        [
            name for name in _PERF_LEADING_INDICATORS
            if leading_indicators.get(name) is None
        ]
        if use_perf else []
    )
    observation = {
        "use_perf": use_perf,
        "counter_status": (
            "not_required" if not use_perf
            else "complete" if not missing
            else "incomplete"
        ),
        "missing_leading_indicators": missing,
        "preflight": normalized_receipt,
    }
    if not use_perf:
        observation["claim_scope"] = dict(_CLAIM_SCOPE)
    return validate_perf_observation(
        observation, run_cmd=run_cmd, leading_indicators=leading_indicators,
    )


def validate_perf_observation(
        observation: object, *, run_cmd: object,
        leading_indicators: Mapping[str, object]) -> dict:
    """observation と同じ測定成果物の argv/指標を相互検証する。"""
    if not isinstance(observation, Mapping):
        raise PerfPreflightError("perf observation が object でない")
    use_perf = observation.get("use_perf")
    if type(use_perf) is not bool:
        raise PerfPreflightError("perf observation.use_perf が bool でない")
    expected_keys = _OBSERVATION_KEYS | ({"claim_scope"} if not use_perf else set())
    if set(observation) != expected_keys:
        raise PerfPreflightError("perf observation の exact key 集合が不一致")

    normalized_receipt = validate_perf_preflight_receipt(
        observation.get("preflight")
    )
    derived_use_perf = use_perf_from_receipt(normalized_receipt)
    if use_perf is not derived_use_perf:
        raise PerfPreflightError(
            "perf observation.use_perf と preflight receipt が不整合"
        )
    missing = _missing_leading_indicators(
        observation.get("missing_leading_indicators")
    )
    status = observation.get("counter_status")

    if use_perf:
        if status not in {"complete", "incomplete"}:
            raise PerfPreflightError(
                "perf observation.counter_status が perf 有り分岐と不整合"
            )
        expected_status = "complete" if not missing else "incomplete"
        if status != expected_status:
            raise PerfPreflightError(
                "perf observation.counter_status と欠測指標が不整合"
            )
    else:
        if status != "not_required" or missing != []:
            raise PerfPreflightError(
                "degraded perf observation の counter 状態が不整合"
            )
        if observation.get("claim_scope") != _CLAIM_SCOPE:
            raise PerfPreflightError(
                "degraded perf observation.claim_scope が不一致"
            )
        argv = _measurement_argv(run_cmd)
        if _has_perf_stat_prefix(argv):
            raise PerfPreflightError(
                "degraded measurement run_cmd に perf stat prefix がある"
            )
        if not isinstance(leading_indicators, Mapping):
            raise PerfPreflightError("leading_indicators が object でない")
        for name in _PERF_LEADING_INDICATORS:
            if name not in leading_indicators:
                raise PerfPreflightError(
                    f"leading_indicators.{name} が欠落している"
                )
            if leading_indicators[name] is not None:
                raise PerfPreflightError(
                    f"leading_indicators.{name} が non-null である"
                )
        _validate_null_perf_values(
            leading_indicators, path="leading_indicators",
        )
        # 偽 unavailable でも本物の no-perf 走と完全整合しなければ通らず、偽造の利得をゼロにする。

    normalized = {
        "use_perf": use_perf,
        "counter_status": status,
        "missing_leading_indicators": missing,
        "preflight": normalized_receipt,
    }
    if not use_perf:
        normalized["claim_scope"] = dict(_CLAIM_SCOPE)
    return normalized


def _claim_decision(claim_scope: Mapping[str, str], claim: str) -> bool:
    """M4 consumer 検査が判定だけを deny できる seam。"""
    return claim_scope[claim] == "eligible"


def perf_claim_allowed(
        observation: object, claim: str, *, run_cmd: object,
        leading_indicators: Mapping[str, object]) -> bool:
    """canonical degraded observation が claim を支えられるか返す。"""
    normalized = validate_perf_observation(
        observation, run_cmd=run_cmd, leading_indicators=leading_indicators,
    )
    if claim not in _CLAIM_SCOPE:
        raise PerfPreflightError(f"未知の perf claim: {claim!r}")
    if normalized["use_perf"]:
        return True
    claim_scope = normalized.get("claim_scope")
    if not isinstance(claim_scope, Mapping):
        raise PerfPreflightError("perf observation.claim_scope が欠落している")
    return _claim_decision(claim_scope, claim)
