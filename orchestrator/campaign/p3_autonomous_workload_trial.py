# -*- coding: utf-8 -*-
"""T-178 bounded unattended workload-conditioned CC synthesis pilot.

This is intentionally a narrow supervisor over the already accepted
``silo-backoff-trigger-gating`` axis.  It does not claim to be a generic
evolution daemon.  A run performs a fixed number of generations for selected
YCSB A/B/C cells, invokes fresh projected planner/coder/auditor/critic roles,
delegates every mutation/evaluation to the existing fail-closed harness, and
writes an exhaustive attempt journal plus a terminal report.

YCSB A/B/C are an exploratory wiring pilot only.  A formal descriptor claim
still requires the frozen H1/H2 on/off/swapped protocol from
``docs/phase3-8b-descriptor-design.md``.
"""
from __future__ import annotations

import argparse
import contextlib
import dataclasses
import datetime as dt
import hashlib
import json
import math
import os
import re
import sys
import time
from collections.abc import Callable, Mapping, Sequence
from pathlib import Path
from typing import Any

_ORCHESTRATOR_FOR_IMPORT = Path(__file__).resolve().parents[1]
if str(_ORCHESTRATOR_FOR_IMPORT) not in sys.path:
    sys.path.insert(0, str(_ORCHESTRATOR_FOR_IMPORT))

if __package__ in {None, ""}:  # pragma: no cover - direct CLI execution
    _ROOT_FOR_IMPORT = Path(__file__).resolve().parents[2]
    if str(_ROOT_FOR_IMPORT) not in sys.path:
        sys.path.insert(0, str(_ROOT_FOR_IMPORT))
    from orchestrator.campaign import p3_s4_loop as loop_core
    from orchestrator.campaign import p3_s4_loop_trigger_gating as trigger
    from orchestrator.campaign.auditor_gate import AuditorVerdict, parse_auditor_dict
    from orchestrator.campaign.claude_projected_provider import ClaudeProjectedRoleProvider
    from orchestrator.campaign.layout import (
        CampaignLayout,
        ensure_exploration_namespace,
        exploration_campaign_layout,
    )
    from orchestrator.campaign.model import CampaignConfig
    from orchestrator.campaign.patchharness import applied, assert_pinned_clean, checkout
    from orchestrator.campaign.pipeline import PerfConfig
    from orchestrator.campaign.s8b_descriptor import (
        project_from_search_config,
        projection_record,
        validate_descriptor,
    )
    from orchestrator.campaign.s8b_prediction_runner import (
        PredictionRunnerError,
        ProviderResponse,
        _canonical_json_bytes,
        _now_iso,
        _parse_json_object,
        _sha256,
        _write_bytes_bound,
    )
else:
    from . import p3_s4_loop as loop_core
    from . import p3_s4_loop_trigger_gating as trigger
    from .auditor_gate import AuditorVerdict, parse_auditor_dict
    from .claude_projected_provider import ClaudeProjectedRoleProvider
    from .layout import (
        CampaignLayout,
        ensure_exploration_namespace,
        exploration_campaign_layout,
    )
    from .model import CampaignConfig
    from .patchharness import applied, assert_pinned_clean, checkout
    from .pipeline import PerfConfig
    from .s8b_descriptor import (
        project_from_search_config,
        projection_record,
        validate_descriptor,
    )
    from .s8b_prediction_runner import (
        PredictionRunnerError,
        ProviderResponse,
        _canonical_json_bytes,
        _now_iso,
        _parse_json_object,
        _sha256,
        _write_bytes_bound,
    )


ROOT = Path(__file__).resolve().parents[2]
SCHEMA_VERSION = "p3-autonomous-workload-trial/v2"
REPORT_SCHEMA_VERSION = "p3-autonomous-workload-trial-report/v1"
MAX_GENERATIONS = 10
MAX_APPROVED_GENERATIONS = 1
DEFAULT_MAX_WALL_S = 3600
_TRIAL_ID_RE = re.compile(r"[a-z0-9][a-z0-9._-]{0,63}")

WORKLOADS: dict[str, dict[str, str]] = {
    "ycsb-a": {"ycsb_zipf_skew": "0.9", "ycsb_rratio": "50", "ycsb_rmw": "0"},
    "ycsb-b": {"ycsb_zipf_skew": "0.9", "ycsb_rratio": "95", "ycsb_rmw": "0"},
    "ycsb-c": {"ycsb_zipf_skew": "0.9", "ycsb_rratio": "100", "ycsb_rmw": "0"},
}

ROLE_FILES = {
    "planner": (ROOT / ".claude/agents/planner-v4.md", "planner-v4"),
    "coder": (
        ROOT / ".claude/agents/coder-v4-autonomous-trigger-gating.md",
        "coder-v4-autonomous-trigger-gating",
    ),
    "auditor": (ROOT / ".claude/agents/auditor.md", "auditor"),
    "critic": (ROOT / ".claude/agents/critic.md", "critic"),
}

ROLE_CONTRACTS = {
    "planner": """
You are called by a bounded unattended Python supervisor. All usable evidence is
in the single JSON object on stdin; do not request tools, files, clarification,
or another turn. The workload_descriptor is causal input to this proposal.
Null metrics mean not yet observed and must not be invented. Return JSON only,
with exactly:
{"proposal":{"axis":"silo-backoff-trigger-gating","direction":"increase|decrease|explore_both","magnitude":"small|medium|large","justification":"string","uncertainty":"string"}}
Keep justification brief and limited to named input fields and observation
availability. Do not name abort reasons, predicates, or a concrete gate design;
the coder must independently infer implementation from only the abstract
direction and magnitude.
Do not emit Markdown or any additional key.
""",
    "coder": """
You are called by a bounded unattended Python supervisor with projection-only
input. The workload_descriptor is causal input to synthesis. Null baseline
metrics mean not yet observed and must not be invented. Follow the source
role's closed-region and forbidden-identifier rules. Return JSON only, exactly:
{"proposal":{"axis":"silo-backoff-trigger-gating","implementation":"izanagi_gate_pass = <side-effect-free predicate>;","justification":"string","confidence":"high|medium|low"}}
The implementation must be one physical line. Do not emit Markdown or extra keys.
""",
    "auditor": """
Runtime capabilities are intentionally lowered to tools=[]: every byte you may
inspect is projected into stdin. Do not request or infer filesystem data. Review
only working_diff, designated_source_context, and correctness_digest. The
workload descriptor is context, never a reason to relax correctness. Echo the
provided diff_digest exactly. Return JSON only, exactly:
{"verdict":"pass|reject|uncertain","diff_digest":"string","violations":[],"nits":[],"proposed_tests":[],"uncertainty":"string"}
Every element of violations must be an object with string fields type, location,
correctness_impact, and verifier_blind_spot. Every element of nits must be an
object {"finding":"string"}. Every element of proposed_tests must be an object
with string fields mutation, expected_gate, and machine_judgment. Empty arrays
are valid; strings directly inside any of these arrays are invalid.
For pass, violations must be empty. For reject, violations must be non-empty.
For uncertain, violations must be empty and uncertainty non-empty. No extra keys.
""",
    "critic": """
Runtime capabilities are intentionally lowered to tools=[]: use only the
projected digest and result on stdin. Never weaken correctness. Missing metrics
must remain uncertainty. Return JSON only, exactly:
{"attribution":"string","recommend":"string","avoid":"string","uncertainty":"string","reverse_recommended":false}
reverse_recommended must be a JSON boolean and means the next planner should
reverse its abstract direction. Do not emit Markdown or extra keys.
""",
}

GATING_SPEC = """The only writable hole is one assignment line:
izanagi_gate_pass = <predicate>;
Allowed reads: izanagi_abort_reason_, IzanagiAbortReason enum members, literals.
kUnset must always evaluate true. Forbidden identifiers: thid_, result_,
read_set_, write_set_, node_map_. No comments, preprocessor directives,
definitions, loops, side effects, or line continuation."""

DESIGNATED_SOURCE_CONTEXT = """Axis: silo-backoff-trigger-gating.
The template frame, abort-reason stores, sentinel reset, markers, #if/#else,
stock branch, gate declaration, and Backoff::backoff call are immutable.
Only the EVOLVE-BLOCK assignment hole may differ. Machine quarantine checks the
region, and a separate syntax gate rejects thid_, result_, read_set_, write_set_,
and node_map_. Auditor review remains required for semantic violations.
The immutable enum is:
IzanagiAbortReason::{kUnset,kLockConflict,kUpdateAbsent,kReadValiTid,
kReadValiLocked,kNodeVali,kInsertNode,kScanNode}.
The immutable consumer calls Backoff::backoff when izanagi_gate_pass is true and
skips that delay when false. The immutable begin path resets the reason to
kUnset. The submitted working_diff is relative to the template-applied baseline,
so a one-line hole-only hunk is the complete coder edit under review."""


class AutonomousTrialError(RuntimeError):
    """Bounded supervisor contract violation."""


def _validate_generation_budget(generations: int) -> None:
    if type(generations) is not int:
        raise AutonomousTrialError(f"generations は 1..{MAX_GENERATIONS} 必須")
    if not 1 <= generations <= MAX_GENERATIONS:
        raise AutonomousTrialError(f"generations は 1..{MAX_GENERATIONS} 必須")
    if generations > MAX_APPROVED_GENERATIONS:
        raise AutonomousTrialError(
            "generations は D106 残余 1 の裁定まで承認済み上限 "
            f"{MAX_APPROVED_GENERATIONS} 以下必須"
        )


def _assert_fresh_campaign_state(layout: CampaignLayout) -> None:
    try:
        state = loop_core.load_loop_state(layout)
    except (OSError, ValueError, KeyError, OverflowError) as exc:
        raise AutonomousTrialError(
            "campaign checkpoint の読取・decode・schema 検査に失敗"
        ) from exc
    if state is not None:
        raise AutonomousTrialError(
            "既存 campaign state は D106 残余 1 の裁定まで再利用不可"
        )


def _strict_keys(value: Mapping[str, Any], expected: set[str], *, path: str) -> None:
    actual = set(value)
    if actual != expected:
        raise AutonomousTrialError(
            f"{path} keys 不一致: missing={sorted(expected - actual)} "
            f"unknown={sorted(actual - expected)}"
        )


def _string(value: Any, *, path: str, allow_empty: bool = False) -> str:
    if not isinstance(value, str) or (not allow_empty and not value.strip()):
        raise AutonomousTrialError(f"{path} は{'空でもよい ' if allow_empty else '空でない '}str 必須")
    return value


def _parse_raw_object(raw: str, *, role: str) -> dict[str, Any]:
    if not isinstance(raw, str):
        raise AutonomousTrialError(f"{role} raw response は str 必須")
    try:
        return _parse_json_object(raw.encode("utf-8"), source=f"{role} response")
    except PredictionRunnerError as exc:
        raise AutonomousTrialError(str(exc)) from exc


def parse_planner(raw: str) -> loop_core.PlannerProposal:
    value = _parse_raw_object(raw, role="planner")
    _strict_keys(value, {"proposal"}, path="$")
    proposal = value["proposal"]
    if not isinstance(proposal, Mapping):
        raise AutonomousTrialError("$.proposal は object 必須")
    _strict_keys(
        proposal,
        {"axis", "direction", "magnitude", "justification", "uncertainty"},
        path="$.proposal",
    )
    if proposal["axis"] != trigger.MARKER_ID:
        raise AutonomousTrialError("planner axis が trigger-gating でない")
    if proposal["direction"] not in {"increase", "decrease", "explore_both"}:
        raise AutonomousTrialError("planner direction が未知")
    if proposal["magnitude"] not in {"small", "medium", "large"}:
        raise AutonomousTrialError("planner magnitude が未知")
    return loop_core.PlannerProposal(
        axis=proposal["axis"],
        direction=proposal["direction"],
        magnitude=proposal["magnitude"],
        justification=_string(proposal["justification"], path="$.proposal.justification"),
        uncertainty=_string(
            proposal["uncertainty"], path="$.proposal.uncertainty", allow_empty=True
        ),
    )


def parse_coder(raw: str) -> trigger.CoderProposalTriggerGating:
    value = _parse_raw_object(raw, role="coder")
    _strict_keys(value, {"proposal"}, path="$")
    proposal = value["proposal"]
    if not isinstance(proposal, Mapping):
        raise AutonomousTrialError("$.proposal は object 必須")
    _strict_keys(
        proposal,
        {"axis", "implementation", "justification", "confidence"},
        path="$.proposal",
    )
    if proposal["axis"] != trigger.MARKER_ID:
        raise AutonomousTrialError("coder axis が trigger-gating でない")
    implementation = _string(proposal["implementation"], path="$.proposal.implementation")
    if "\n" in implementation or "\r" in implementation:
        raise AutonomousTrialError("coder implementation は物理 1 行必須")
    if proposal["confidence"] not in {"high", "medium", "low"}:
        raise AutonomousTrialError("coder confidence が未知")
    return trigger.CoderProposalTriggerGating(
        axis=proposal["axis"],
        implementation=implementation,
        justification=_string(proposal["justification"], path="$.proposal.justification"),
        confidence=proposal["confidence"],
    )


def parse_auditor(raw: str) -> AuditorVerdict:
    value = _parse_raw_object(raw, role="auditor")
    _strict_keys(
        value,
        {"verdict", "diff_digest", "violations", "nits", "proposed_tests", "uncertainty"},
        path="$",
    )
    try:
        return parse_auditor_dict(dict(value))
    except (KeyError, ValueError) as exc:
        raise AutonomousTrialError(str(exc)) from exc


def parse_critic(raw: str) -> dict[str, Any]:
    value = _parse_raw_object(raw, role="critic")
    _strict_keys(
        value,
        {"attribution", "recommend", "avoid", "uncertainty", "reverse_recommended"},
        path="$",
    )
    for key in ("attribution", "recommend", "avoid"):
        _string(value[key], path=f"$.{key}")
    _string(value["uncertainty"], path="$.uncertainty", allow_empty=True)
    if not isinstance(value["reverse_recommended"], bool):
        raise AutonomousTrialError("$.reverse_recommended は bool 必須")
    return dict(value)


PARSERS: dict[str, Callable[[str], Any]] = {
    "planner": parse_planner,
    "coder": parse_coder,
    "auditor": parse_auditor,
    "critic": parse_critic,
}


class FixtureRoleProvider:
    """Deterministic provider for no-build wiring and regression tests."""

    provider_kind = "fixture"

    def __init__(self, role: str) -> None:
        self.role = role
        self.role_file_sha256 = _sha256(ROLE_FILES[role][0].read_bytes())
        self.effective_prompt_sha256 = _sha256(ROLE_CONTRACTS[role].encode("utf-8"))

    def invoke(self, *, invocation_id: str, payload: Mapping[str, Any]) -> ProviderResponse:
        if self.role == "planner":
            value = {
                "proposal": {
                    "axis": trigger.MARKER_ID,
                    "direction": "explore_both",
                    "magnitude": "small",
                    "justification": "fixture: descriptor-conditioned wiring proposal",
                    "uncertainty": "fixture output; no scientific inference",
                }
            }
        elif self.role == "coder":
            generation = payload.get("generation")
            implementation = (
                "izanagi_gate_pass = true;"
                if generation == 1
                else "izanagi_gate_pass = izanagi_abort_reason_ == "
                "IzanagiAbortReason::kUnset || izanagi_abort_reason_ == "
                "IzanagiAbortReason::kLockConflict;"
            )
            value = {
                "proposal": {
                    "axis": trigger.MARKER_ID,
                    "implementation": implementation,
                    "justification": "fixture: deterministic closed-region candidate",
                    "confidence": "low",
                }
            }
        elif self.role == "auditor":
            value = {
                "verdict": "pass",
                "diff_digest": payload["diff_digest"],
                "violations": [],
                "nits": [],
                "proposed_tests": [],
                "uncertainty": "fixture audit only",
            }
        elif self.role == "critic":
            value = {
                "attribution": "fixture has no measured indicators",
                "recommend": "continue the fixed generation schedule",
                "avoid": "do not infer performance from dry-run output",
                "uncertainty": "all performance metrics are absent",
                "reverse_recommended": False,
            }
        else:  # pragma: no cover - construction is closed over ROLE_FILES
            raise AutonomousTrialError(f"unknown fixture role: {self.role}")
        return ProviderResponse(
            raw_response=_canonical_json_bytes(value).decode("utf-8"),
            provenance={
                "child_id": f"fixture-{invocation_id}",
                "role_name": self.role,
                "role_file_sha256": self.role_file_sha256,
                "effective_prompt_sha256": self.effective_prompt_sha256,
                "model": "fixture",
                "fresh_context": True,
                "declared_tools": [],
                "observed_tool_events": [],
                "payload_sha256": _sha256(_canonical_json_bytes(payload)),
            },
        )


class AttemptJournal:
    """Append-only, fsynced supervisor event journal."""

    def __init__(self, path: Path) -> None:
        self.path = Path(path)
        self.seq = 0

    def append(self, event: Mapping[str, Any]) -> dict[str, Any]:
        stored = dict(event)
        self.seq += 1
        stored["seq"] = self.seq
        stored["ts"] = _now_iso()
        payload = _canonical_json_bytes(stored) + b"\n"
        flags = os.O_WRONLY | os.O_CREAT | os.O_APPEND
        if hasattr(os, "O_NOFOLLOW"):
            flags |= os.O_NOFOLLOW
        fd = os.open(self.path, flags, 0o600)
        try:
            view = memoryview(payload)
            while view:
                written = os.write(fd, view)
                if written <= 0:
                    raise OSError("journal write did not advance")
                view = view[written:]
            os.fsync(fd)
        finally:
            os.close(fd)
        return stored


def _campaign_for(
    *, workload: str, workload_flags: Mapping[str, str], descriptor: Mapping[str, Any],
    descriptor_record: Mapping[str, Any], trial_id: str, generations: int,
) -> CampaignConfig:
    base = trigger.default_cfg(reflux=True)
    search_config = dict(base.search_config)
    search_config.update({
        "workload": workload,
        "ycsb": dict(workload_flags),
        "records": 100_000,
        "threads": 4,
        "descriptor_schema": descriptor["schema_version"],
        "descriptor_sha256": descriptor_record["output_sha256"],
        "generation_budget": generations,
        "stop_policy": "fixed-generations-no-performance-early-stop",
        "pilot_scope": "exploratory-ycsb-abc",
    })
    return CampaignConfig(
        spec_slug=f"p3-t178-{workload}",
        search_tag="workload-conditioned-autonomous",
        spec_content=(
            "T-178 exploratory YCSB A/B/C workload-conditioned unattended synthesis. "
            "Python invokes fresh projected planner/coder/auditor/critic roles; existing "
            "trigger-gating quarantine/correctness/performance harness remains authoritative. "
            "Fixed generations, no performance-target early stop, no formal descriptor claim."
        ),
        ccbench_commit=base.ccbench_commit,
        search_config=search_config,
        trial=f"{trial_id}-{workload}",
    )


def _perf_for(workload_flags: Mapping[str, str]) -> PerfConfig:
    return PerfConfig(
        records=100_000,
        threads=4,
        workload=dict(workload_flags),
        extime=1,
        reps=2,
    )


def _descriptor_for(workload_flags: Mapping[str, str]) -> tuple[dict, dict]:
    projected_input = {
        "records": 100_000,
        "threads": 4,
        "ycsb": dict(workload_flags),
    }
    descriptor = project_from_search_config(projected_input)
    validate_descriptor(descriptor)
    return descriptor, projection_record(projected_input, descriptor)


def _preview(coder: trigger.CoderProposalTriggerGating, *, sub: str) -> dict[str, Any]:
    assert_pinned_clean(sub, trigger.PIN)
    patch = trigger._template_patch_path(str(ROOT))
    with applied(patch, trigger.PIN, sub):
        result, _base, _edited, working_diff = loop_core.quarantine(
            sub,
            coder.implementation,
            marker_id=trigger.MARKER_ID,
            source_rel=trigger.SOURCE_REL,
            write=False,
        )
    return {
        "passed": result.passed,
        "working_diff": working_diff,
        "diff_digest": hashlib.sha256(working_diff.encode("utf-8")).hexdigest(),
        "subtype": result.subtype.value if result.subtype else None,
        "reason": result.reason,
        "forbidden_identifiers": trigger.check_syntax_contract(coder.implementation),
    }


def _whiteboard(layout: CampaignLayout) -> list[dict[str, Any]]:
    state = loop_core.load_loop_state(layout)
    return [] if state is None else loop_core.whiteboard_for_planner(state)


def _finite_metric_or_none(value: Any) -> float | None:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    try:
        metric = float(value)
    except OverflowError:
        return None
    return metric if math.isfinite(metric) else None


def _metric_projection(outcome: Mapping[str, Any]) -> dict[str, Any]:
    records = outcome.get("records")
    bench_done = records.get("bench_done") if isinstance(records, Mapping) else None
    leading = (
        bench_done.get("leading_indicators")
        if isinstance(bench_done, Mapping)
        and isinstance(bench_done.get("leading_indicators"), Mapping)
        else {}
    )
    fitness = outcome.get("fitness_tps")
    return {
        "throughput_ops_sec": _finite_metric_or_none(fitness),
        "abort_rate": _finite_metric_or_none(leading.get("abort_rate")),
        "latency_ns": _finite_metric_or_none(leading.get("latency_ns")),
        "llc_miss_rate": _finite_metric_or_none(leading.get("llc_miss_rate")),
        "ipc": _finite_metric_or_none(leading.get("ipc")),
    }


def _role_metric_payloads(
    current_metrics: Mapping[str, Any],
    *,
    contention_level: str,
) -> tuple[dict[str, Any], dict[str, Any]]:
    abort_rate = current_metrics["abort_rate"]
    llc_miss_rate = current_metrics["llc_miss_rate"]
    perf_payload = {
        "throughput_ops_sec": current_metrics["throughput_ops_sec"],
        "abort_rate_pct": (
            None
            if abort_rate is None
            else _finite_metric_or_none(abort_rate * 100.0)
        ),
        "latency_ns": current_metrics["latency_ns"],
        "llc_miss_rate": llc_miss_rate,
        "ipc": current_metrics["ipc"],
    }
    leading_payload = {
        "contention_level": contention_level,
        "cache_miss_rate_pct": (
            None
            if llc_miss_rate is None
            else _finite_metric_or_none(llc_miss_rate * 100.0)
        ),
        "IPC_overall": current_metrics["ipc"],
    }
    return perf_payload, leading_payload


def _jsonable_role_value(role: str, parsed: Any) -> dict[str, Any]:
    if role in {"planner", "coder", "auditor"}:
        return dataclasses.asdict(parsed)
    return dict(parsed)


def _write_json_atomic(path: Path, value: Mapping[str, Any]) -> None:
    data = json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2, allow_nan=False)
    tmp = path.with_name(path.name + f".{os.getpid()}.tmp")
    if tmp.exists() or tmp.is_symlink():
        raise AutonomousTrialError(f"report tmp が既に存在: {tmp}")
    with tmp.open("x", encoding="utf-8") as stream:
        stream.write(data)
        stream.write("\n")
        stream.flush()
        os.fsync(stream.fileno())
    os.replace(tmp, path)


def _invoke(
    *, role: str, provider: Any, invocation_id: str, payload: Mapping[str, Any],
    raw_root: Path, journal: AttemptJournal, workload: str, generation: int,
) -> tuple[Any | None, dict[str, Any]]:
    input_sha256 = _sha256(_canonical_json_bytes(payload))
    base = {
        "event": "role-attempt",
        "workload": workload,
        "generation": generation,
        "role": role,
        "invocation_id": invocation_id,
        "input_payload_sha256": input_sha256,
        "descriptor_sha256": payload["descriptor_binding"]["output_sha256"],
        "attempt": 1,
        "retry": False,
    }
    try:
        response = provider.invoke(invocation_id=invocation_id, payload=payload)
        if not isinstance(response, ProviderResponse):
            raise AutonomousTrialError("provider は ProviderResponse を返す必要がある")
        raw_bytes = response.raw_response.encode("utf-8")
        raw_path = raw_root / f"raw_{invocation_id}.txt"
        raw_sha256 = _write_bytes_bound(raw_path, raw_bytes)
        parsed = PARSERS[role](response.raw_response)
    except Exception as exc:
        error_artifacts: dict[str, str] = {}
        artifact_root = getattr(provider, "artifact_root", None)
        if isinstance(artifact_root, Path):
            for kind in ("payload", "envelope"):
                candidate = artifact_root / f"{kind}_{invocation_id}.json"
                if candidate.is_file() and not candidate.is_symlink():
                    error_artifacts[f"{kind}_path"] = str(candidate)
                    error_artifacts[f"{kind}_sha256"] = _sha256(candidate.read_bytes())
        event = journal.append({
            **base,
            "status": "invalid",
            "error_type": type(exc).__name__,
            "error": str(exc),
            "error_artifacts": error_artifacts,
        })
        return None, event
    event = journal.append({
        **base,
        "status": "valid",
        "raw_response_path": str(raw_path),
        "raw_response_sha256": raw_sha256,
        "parsed": _jsonable_role_value(role, parsed),
        "provenance": dict(response.provenance),
    })
    return parsed, event


def _common_payload(
    *, workload: str, generation: int, descriptor: Mapping[str, Any],
    descriptor_record: Mapping[str, Any],
) -> dict[str, Any]:
    return {
        "schema_version": SCHEMA_VERSION,
        "pilot_scope": "exploratory-ycsb-abc",
        "scientific_claim": False,
        "workload": workload,
        "generation": generation,
        "workload_descriptor": dict(descriptor),
        "descriptor_binding": dict(descriptor_record),
        "attempt_policy": {"attempts_per_role_generation": 1, "retry": False},
        "stop_policy": {
            "performance_early_stop": False,
            "generation_budget_is_fixed": True,
        },
    }


def _close_owned_providers(providers: Mapping[str, Any]) -> None:
    for provider in reversed(tuple(providers.values())):
        close = getattr(provider, "close", None)
        if callable(close):
            close()


def _provider_set(*, kind: str, run_root: Path, executable: str) -> dict[str, Any]:
    result: dict[str, Any] = {}
    try:
        for role, (role_file, role_name) in ROLE_FILES.items():
            if kind == "fixture":
                result[role] = FixtureRoleProvider(role)
            elif kind == "claude-headless":
                result[role] = ClaudeProjectedRoleProvider(
                    artifact_root=run_root / "provider" / role,
                    role_file=role_file,
                    role_name=role_name,
                    mediated_contract=ROLE_CONTRACTS[role],
                    repository_root=ROOT,
                    executable=executable,
                )
            else:  # pragma: no cover - argparse closes this
                raise AutonomousTrialError(f"unknown provider kind: {kind}")
    except BaseException:
        _close_owned_providers(result)
        raise
    return result


def _finish_trial(
    *,
    trial_id: str,
    selected: list[str],
    generations: int,
    provider_kind: str,
    run_root: Path,
    sub: str,
    do_build: bool,
    cache_root: str,
    max_wall_s: int,
    drive: Callable[..., Mapping[str, Any]],
    preview: Callable[..., Mapping[str, Any]],
    journal: AttemptJournal,
    started: str,
    started_monotonic: float,
    active_providers: Mapping[str, Any],
    fatal_error: dict[str, str] | None,
) -> dict[str, Any]:
    cells: list[dict[str, Any]] = []
    if fatal_error is None:
        for workload in selected:
            if time.monotonic() - started_monotonic >= max_wall_s:
                fatal_error = {
                    "type": "SupervisorWallBudget",
                    "message": "wall budget expired before the next workload",
                }
                journal.append({"event": "supervisor-wall-budget", "workload": workload})
                break
            try:
                cell = _run_workload(
                    workload=workload,
                    generations=generations,
                    providers=active_providers,
                    journal=journal,
                    run_root=run_root,
                    sub=sub,
                    do_build=do_build,
                    cache_root=cache_root,
                    trial_id=trial_id,
                    started_monotonic=started_monotonic,
                    max_wall_s=max_wall_s,
                    drive=drive,
                    preview=preview,
                )
            except Exception as exc:
                fatal_error = {"type": type(exc).__name__, "message": str(exc)}
                journal.append({
                    "event": "supervisor-error",
                    "workload": workload,
                    **fatal_error,
                })
                cells.append({
                    "workload": workload,
                    "generations": [],
                    "stop_reason": "supervisor-error",
                    "error": dict(fatal_error),
                })
                break
            cells.append(cell)
    status = (
        "complete"
        if len(cells) == len(selected)
        and fatal_error is None
        and all(
            cell["stop_reason"]
            not in {"role-invalid", "supervisor-error", "supervisor-wall-budget"}
            for cell in cells
        )
        else "partial"
    )
    report = {
        "schema_version": REPORT_SCHEMA_VERSION,
        "trial_id": trial_id,
        "status": status,
        "started_at": started,
        "finished_at": _now_iso(),
        "provider": provider_kind,
        "do_build": do_build,
        "workloads_requested": selected,
        "generation_budget_per_workload": generations,
        "stop_policy": {
            "fixed_generations": True,
            "performance_early_stop": False,
            "max_wall_s": max_wall_s,
        },
        "claim_scope": {
            "scientific_claim": False,
            "label": "exploratory wiring pilot",
            "formal_followup": "H1 rr80 / H2 rr20 x on/off/swapped",
            "known_workload_warning": (
                "YCSB A/B are known rr50/rr95 points; YCSB C is an exploratory "
                "read-only negative-control candidate."
            ),
        },
        "attempt_journal": str(run_root / "attempts.jsonl"),
        "cells": cells,
    }
    if fatal_error is not None:
        report["fatal_error"] = fatal_error
    journal.append({
        "event": "run-finish",
        "status": status,
        "report": str(run_root / "report.json"),
    })
    report["attempt_journal_sha256"] = _sha256((run_root / "attempts.jsonl").read_bytes())
    _write_json_atomic(run_root / "report.json", report)
    return report


def _run_workload(
    *, workload: str, generations: int, providers: Mapping[str, Any],
    journal: AttemptJournal, run_root: Path, sub: str, do_build: bool,
    cache_root: str, trial_id: str, started_monotonic: float, max_wall_s: int,
    drive: Callable[..., Mapping[str, Any]] = trigger.drive_iteration,
    preview: Callable[..., Mapping[str, Any]] = _preview,
) -> dict[str, Any]:
    _validate_generation_budget(generations)
    flags = WORKLOADS[workload]
    descriptor, descriptor_record = _descriptor_for(flags)
    cfg = _campaign_for(
        workload=workload,
        workload_flags=flags,
        descriptor=descriptor,
        descriptor_record=descriptor_record,
        trial_id=trial_id,
        generations=generations,
    )
    if do_build:
        layout = exploration_campaign_layout(str(trigger.ident.campaign_id(cfg)))
    else:
        layout = CampaignLayout(str(run_root / "campaigns" / str(trigger.ident.campaign_id(cfg))))
    _assert_fresh_campaign_state(layout)
    perf = _perf_for(flags)
    result: dict[str, Any] = {
        "workload": workload,
        "workload_flags": dict(flags),
        "descriptor": descriptor,
        "descriptor_binding": descriptor_record,
        "campaign_id": str(trigger.ident.campaign_id(cfg)),
        "campaign_root": layout.root,
        "generations": [],
        "stop_reason": "fixed-generation-budget",
    }
    prior_reverse: bool | None = None
    current_metrics = {
        "throughput_ops_sec": None,
        "abort_rate": None,
        "latency_ns": None,
        "llc_miss_rate": None,
        "ipc": None,
    }

    for generation in range(1, generations + 1):
        if time.monotonic() - started_monotonic >= max_wall_s:
            result["stop_reason"] = "supervisor-wall-budget"
            break
        generation_record: dict[str, Any] = {"generation": generation, "roles": {}}
        common = _common_payload(
            workload=workload,
            generation=generation,
            descriptor=descriptor,
            descriptor_record=descriptor_record,
        )
        whiteboard = _whiteboard(layout)
        perf_payload, leading_payload = _role_metric_payloads(
            current_metrics,
            contention_level=descriptor["contention"]["label"],
        )
        planner_payload = {
            **common,
            "current_perf": dict(perf_payload),
            "leading_indicators": dict(leading_payload),
            "whiteboard": whiteboard,
        }
        planner, event = _invoke(
            role="planner",
            provider=providers["planner"],
            invocation_id=f"{workload}.g{generation}.planner",
            payload=planner_payload,
            raw_root=run_root / "raw",
            journal=journal,
            workload=workload,
            generation=generation,
        )
        generation_record["roles"]["planner"] = event
        if planner is None:
            generation_record["outcome"] = "planner-invalid"
            result["generations"].append(generation_record)
            result["stop_reason"] = "role-invalid"
            break

        coder_payload = {
            **common,
            "leakproof_context": (
                "Use only this campaign's projected descriptor, metrics, planner direction, "
                "and abstract whiteboard. No prior sweep winner, candidate ranking, or "
                "unmeasured performance is available."
            ),
            "gating_spec": GATING_SPEC,
            # Planner mechanism text is intentionally not forwarded.  Only the
            # abstract control signal crosses the planner→coder boundary.
            "planner_direction": {
                "axis": planner.axis,
                "direction": planner.direction,
                "magnitude": planner.magnitude,
            },
            "baseline": dict(perf_payload),
            "whiteboard": whiteboard,
        }
        coder, event = _invoke(
            role="coder",
            provider=providers["coder"],
            invocation_id=f"{workload}.g{generation}.coder",
            payload=coder_payload,
            raw_root=run_root / "raw",
            journal=journal,
            workload=workload,
            generation=generation,
        )
        generation_record["roles"]["coder"] = event
        if coder is None:
            generation_record["outcome"] = "coder-invalid"
            result["generations"].append(generation_record)
            result["stop_reason"] = "role-invalid"
            break

        preview_result = dict(preview(coder, sub=sub))
        generation_record["preview"] = {
            key: value for key, value in preview_result.items() if key != "working_diff"
        }
        pre_audit_reject = (
            not preview_result["passed"]
            or bool(preview_result["forbidden_identifiers"])
        )
        if pre_audit_reject:
            auditor = AuditorVerdict(
                verdict="uncertain",
                diff_digest=preview_result["diff_digest"],
                uncertainty="not invoked: machine pre-audit rejection",
            )
            generation_record["roles"]["auditor"] = {
                "status": "skipped",
                "reason": "machine-pre-audit-rejection",
            }
        else:
            auditor_payload = {
                **common,
                "working_diff": preview_result["working_diff"],
                "diff_digest": preview_result["diff_digest"],
                "designated_source_context": DESIGNATED_SOURCE_CONTEXT,
                "correctness_digest": (
                    "pre-build audit: no performance or post-run correctness result exists yet"
                ),
            }
            auditor, event = _invoke(
                role="auditor",
                provider=providers["auditor"],
                invocation_id=f"{workload}.g{generation}.auditor",
                payload=auditor_payload,
                raw_root=run_root / "raw",
                journal=journal,
                workload=workload,
                generation=generation,
            )
            generation_record["roles"]["auditor"] = event
            if auditor is None:
                generation_record["outcome"] = "auditor-invalid"
                result["generations"].append(generation_record)
                result["stop_reason"] = "role-invalid"
                break

        proposal_path = run_root / "proposals" / f"{workload}.g{generation}.json"
        proposal_value = {
            "planner": dataclasses.asdict(planner),
            "coder": dataclasses.asdict(coder),
            "auditor": dataclasses.asdict(auditor),
            "prior_critic_reverse": prior_reverse,
            "descriptor_sha256": descriptor_record["output_sha256"],
        }
        _write_bytes_bound(proposal_path, _canonical_json_bytes(proposal_value))
        outcome = dict(
            drive(
                cfg,
                perf,
                planner,
                coder,
                auditor,
                prior_reverse,
                sub,
                do_build,
                layout=layout,
                cache_root=cache_root,
                proposal_path=str(proposal_path),
                extra_sources=({
                    "path": "orchestrator/campaign/p3_autonomous_workload_trial.py",
                    "role": "T-178 unattended Python supervisor and descriptor projection",
                },),
            )
        )
        generation_record["harness"] = outcome
        generation_record["outcome"] = outcome["outcome"]
        current_metrics = _metric_projection(outcome)

        digest_path = Path(layout.root) / trigger.DIGEST_BASENAME
        digest = digest_path.read_text(encoding="utf-8") if digest_path.exists() else ""
        critic_payload = {
            **common,
            "harness_result": {
                "outcome": outcome.get("outcome"),
                "variant": outcome.get("variant"),
                "verdict": outcome.get("verdict"),
                "metrics": dict(current_metrics),
                "stop_reason": outcome.get("stop_reason"),
            },
            "critic_digest": digest,
        }
        critic, event = _invoke(
            role="critic",
            provider=providers["critic"],
            invocation_id=f"{workload}.g{generation}.critic",
            payload=critic_payload,
            raw_root=run_root / "raw",
            journal=journal,
            workload=workload,
            generation=generation,
        )
        generation_record["roles"]["critic"] = event
        result["generations"].append(generation_record)
        if critic is None:
            result["stop_reason"] = "role-invalid"
            break
        prior_reverse = critic["reverse_recommended"]
        if outcome.get("stop_reason") != "continue":
            result["stop_reason"] = str(outcome.get("stop_reason"))
            break
    return result


def run_trial(
    *,
    trial_id: str,
    workloads: Sequence[str],
    generations: int,
    provider_kind: str,
    run_root: Path,
    sub: str,
    do_build: bool,
    cache_root: str = "",
    max_wall_s: int = DEFAULT_MAX_WALL_S,
    claude_executable: str = "claude",
    providers: Mapping[str, Any] | None = None,
    drive: Callable[..., Mapping[str, Any]] = trigger.drive_iteration,
    preview: Callable[..., Mapping[str, Any]] = _preview,
) -> dict[str, Any]:
    if _TRIAL_ID_RE.fullmatch(trial_id) is None:
        raise AutonomousTrialError(f"trial_id が安全な形式でない: {trial_id!r}")
    _validate_generation_budget(generations)
    if isinstance(max_wall_s, bool) or not isinstance(max_wall_s, int) or max_wall_s < 1:
        raise AutonomousTrialError("max_wall_s は正の int 必須")
    selected = list(workloads)
    if not selected or len(selected) != len(set(selected)):
        raise AutonomousTrialError("workloads は重複なしの非空列必須")
    unknown = sorted(set(selected) - set(WORKLOADS))
    if unknown:
        raise AutonomousTrialError(f"unknown workloads: {unknown}")
    run_root = Path(run_root)
    if run_root.exists() or run_root.is_symlink():
        raise AutonomousTrialError(
            f"run_root は新規 directory 必須 (resume は MVP 範囲外): {run_root}"
        )
    run_root.mkdir(parents=True)
    ensure_exploration_namespace(str(run_root))
    for child in ("raw", "proposals"):
        (run_root / child).mkdir()
    journal = AttemptJournal(run_root / "attempts.jsonl")
    started = _now_iso()
    started_monotonic = time.monotonic()
    journal.append({
        "event": "run-start",
        "schema_version": SCHEMA_VERSION,
        "trial_id": trial_id,
        "provider": provider_kind,
        "workloads": selected,
        "generation_budget_per_workload": generations,
        "max_wall_s": max_wall_s,
        "do_build": do_build,
        "performance_early_stop": False,
        "scientific_claim": False,
    })
    owns_active_providers = providers is None
    active_providers: dict[str, Any] = {}
    fatal_error: dict[str, str] | None = None
    try:
        try:
            active_providers = (
                dict(providers)
                if providers is not None
                else _provider_set(
                    kind=provider_kind, run_root=run_root, executable=claude_executable
                )
            )
        except Exception as exc:
            fatal_error = {"type": type(exc).__name__, "message": str(exc)}
            journal.append({"event": "provider-init-error", **fatal_error})
        return _finish_trial(
            trial_id=trial_id,
            selected=selected,
            generations=generations,
            provider_kind=provider_kind,
            run_root=run_root,
            sub=sub,
            do_build=do_build,
            cache_root=cache_root,
            max_wall_s=max_wall_s,
            drive=drive,
            preview=preview,
            journal=journal,
            started=started,
            started_monotonic=started_monotonic,
            active_providers=active_providers,
            fatal_error=fatal_error,
        )
    finally:
        if owns_active_providers:
            _close_owned_providers(active_providers)


def _parse_workloads(raw: str) -> list[str]:
    values = [item.strip().lower() for item in raw.split(",") if item.strip()]
    if not values:
        raise argparse.ArgumentTypeError("workloads is empty")
    unknown = sorted(set(values) - set(WORKLOADS))
    if unknown:
        raise argparse.ArgumentTypeError(f"unknown workloads: {unknown}")
    if len(values) != len(set(values)):
        raise argparse.ArgumentTypeError("workloads contains duplicates")
    return values


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="T-178 bounded unattended workload-conditioned CC synthesis pilot"
    )
    parser.add_argument("--trial-id", required=True)
    parser.add_argument(
        "--provider", required=True, choices=("fixture", "claude-headless")
    )
    parser.add_argument("--workloads", type=_parse_workloads, default=list(WORKLOADS))
    parser.add_argument("--max-generations", type=int, default=1)
    parser.add_argument("--max-wall-seconds", type=int, default=DEFAULT_MAX_WALL_S)
    parser.add_argument("--no-build", action="store_true")
    parser.add_argument("--claude-executable", default="claude")
    parser.add_argument("--ccbench-dir", default=str(ROOT / "external/ccbench"))
    parser.add_argument(
        "--run-root",
        default="",
        help=(
            "fresh artifact directory "
            "(default: output/exploration/autonomous-trials/<trial-id>)"
        ),
    )
    args = parser.parse_args(argv)
    _validate_generation_budget(args.max_generations)
    if args.provider == "fixture" and not args.no_build:
        raise AutonomousTrialError(
            "fixture provider cannot be used with a real build"
        )
    run_root = (
        Path(args.run_root)
        if args.run_root
        else ROOT / "output" / "exploration" / "autonomous-trials" / args.trial_id
    )
    fixed_sub = str(Path(args.ccbench_dir).resolve())
    if args.no_build:
        assert_pinned_clean(fixed_sub, trigger.PIN)
        context = contextlib.nullcontext(fixed_sub)
        cache_root = ""
    else:
        from calibrator.runner import competing_bench_pids

        competitors = competing_bench_pids()
        if competitors:
            raise AutonomousTrialError(
                "competing benchmark detected; refusing measurement: " + " | ".join(competitors)
            )
        context = checkout(trigger.PIN, base_dir=fixed_sub)
        cache_root = str(Path(fixed_sub) / "build-variants")
    with context as sub:
        report = run_trial(
            trial_id=args.trial_id,
            workloads=args.workloads,
            generations=args.max_generations,
            provider_kind=args.provider,
            run_root=run_root,
            sub=sub,
            do_build=not args.no_build,
            cache_root=cache_root,
            max_wall_s=args.max_wall_seconds,
            claude_executable=args.claude_executable,
        )
    print(json.dumps({
        "status": report["status"],
        "report": str(run_root / "report.json"),
        "cells": len(report["cells"]),
    }, ensure_ascii=False, sort_keys=True))
    return 0 if report["status"] == "complete" else 2


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
