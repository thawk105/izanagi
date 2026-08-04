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
    from orchestrator.campaign.reflux_ir import emit_predicate, parse_wire
    from orchestrator.campaign.autonomous_trial_completeness import (
        assert_campaign_layer3_chain,
        assert_autonomous_trial_completeness,
    )
    from orchestrator.campaign.auditor_gate import AuditorVerdict, parse_auditor_dict
    from orchestrator.campaign.claude_projected_provider import ClaudeProjectedRoleProvider
    from orchestrator.campaign.claude_transport import (
        ClaudeTransportAdmission,
        admit_claude_transport,
        is_valid_pbs_jobid,
    )
    from orchestrator.campaign.role_session_isolation import CrossRoleSessionTracker
    from orchestrator.campaign.layout import (
        CampaignLayout,
        ensure_exploration_namespace,
        exploration_campaign_layout,
    )
    from orchestrator.campaign import layer3_report
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
    from .reflux_ir import emit_predicate, parse_wire
    from .autonomous_trial_completeness import (
        assert_campaign_layer3_chain,
        assert_autonomous_trial_completeness,
    )
    from .auditor_gate import AuditorVerdict, parse_auditor_dict
    from .claude_projected_provider import ClaudeProjectedRoleProvider
    from .claude_transport import (
        ClaudeTransportAdmission,
        admit_claude_transport,
        is_valid_pbs_jobid,
    )
    from .role_session_isolation import CrossRoleSessionTracker
    from .layout import (
        CampaignLayout,
        ensure_exploration_namespace,
        exploration_campaign_layout,
    )
    from . import layer3_report
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

# The axis driver imports the campaign namespace directly.  Keep the U1 run
# context and identity types on that same module identity so exact-type seals
# survive package and direct-script entry points alike.
from campaign import ident  # noqa: E402
from campaign.build_admission import (  # noqa: E402
    BuildAdmissionError,
    BuildRunContext,
    CoderBuildAuthority,
    GeneratorId,
    add_coder_build_authority_argument,
    build_run_context,
)


ROOT = Path(__file__).resolve().parents[2]
SCHEMA_VERSION = "p3-autonomous-workload-trial/v2"
REPORT_SCHEMA_VERSION = "p3-autonomous-workload-trial-report/v2"
MAX_GENERATIONS = 10
MAX_APPROVED_GENERATIONS = 1
DEFAULT_MAX_WALL_S = 3600
PROVIDER_KINDS = frozenset(("fixture", "claude-headless"))
DRIVER_STOP_REASONS = frozenset((
    "continue",
    "converged",
    "reverse-exhausted",
    "budget-iterations",
    "budget-walltime",
))
_TRIAL_ID_RE = re.compile(r"[a-z0-9][a-z0-9._-]{0,63}")
_LOWER_HEX_RE = re.compile(r"[0-9a-f]{64}")
_TRANSPORT_RECEIPT_KEYS = {
    "schema_version",
    "mode",
    "site",
    "admitted_env_keys",
    "endpoint_values",
    "endpoint_values_sha256",
    "policy_path",
    "policy_sha256",
    "source_tls_trust_override_keys",
    "forwarded_tls_trust_override_keys",
    "pbs_jobid",
}

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
the coder must independently infer the wire from only the abstract
direction and magnitude.
Do not emit Markdown or any additional key.
""",
    "coder": """
You are called by a bounded unattended Python supervisor with projection-only
input. The workload_descriptor is causal input to synthesis. Null baseline
metrics mean not yet observed and must not be invented. Follow the source
role's exact five-bit wire contract. Return JSON only, exactly:
{"proposal":{"axis":"silo-backoff-trigger-gating","wire":"10100","justification":"string","confidence":"high|medium|low"}}
wire is exactly five 0/1 characters in LSB-first order: lock-conflict,
update-absent, readvali-tid, readvali-locked, node-vali. 1 means back off.
The frozen emitter alone adds the kUnset fail-safe. Do not emit Markdown or extra keys.
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

GATING_SPEC = """Return exactly one five-character wire. It is LSB-first in
this order: lock-conflict, update-absent, readvali-tid, readvali-locked,
node-vali. 1 means back off for that reason and 0 means skip backoff. The
frozen emitter exclusively adds the kUnset fail-safe and materializes the
single assignment line. No source code or additional field is accepted."""

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
        {"axis", "wire", "justification", "confidence"},
        path="$.proposal",
    )
    if proposal["axis"] != trigger.MARKER_ID:
        raise AutonomousTrialError("coder axis が trigger-gating でない")
    parse_wire(proposal["wire"])
    if proposal["confidence"] not in {"high", "medium", "low"}:
        raise AutonomousTrialError("coder confidence が未知")
    return trigger.CoderProposalTriggerGating(
        axis=proposal["axis"],
        wire=proposal["wire"],
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
            wire = "11111" if generation == 1 else "10000"
            value = {
                "proposal": {
                    "axis": trigger.MARKER_ID,
                    "wire": wire,
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
        self.failed = False

    def append(self, event: Mapping[str, Any]) -> dict[str, Any]:
        if self.failed:
            raise AutonomousTrialError(
                "attempt journal の過去の append 失敗後は追記・report 公開を継続できない"
            )
        stored = dict(event)
        self.seq += 1
        stored["seq"] = self.seq
        stored["ts"] = _now_iso()
        payload = _canonical_json_bytes(stored) + b"\n"
        flags = os.O_WRONLY | os.O_CREAT | os.O_APPEND
        if hasattr(os, "O_NOFOLLOW"):
            flags |= os.O_NOFOLLOW
        try:
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
        except BaseException:
            # A failed append can leave a missing or partial event on disk.  Never
            # append a terminal event after that failure and thereby publish a
            # smaller attempt universe as a valid partial report.
            self.failed = True
            raise
        return stored


def _campaign_for(
    *, workload: str, workload_flags: Mapping[str, str], descriptor: Mapping[str, Any],
    descriptor_record: Mapping[str, Any], trial_id: str, generations: int,
    build_context: BuildRunContext | None = None,
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
    cfg = CampaignConfig(
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
    if type(build_context) is not BuildRunContext:
        raise AutonomousTrialError(
            "autonomous campaign identity requires one shared BuildRunContext"
        )
    return ident.bind_admission_policy(cfg, build_context.policy)


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
    predicate = emit_predicate(parse_wire(coder.wire))
    if trigger.check_syntax_contract(predicate):
        raise RuntimeError("canonical trigger predicate violates syntax contract")
    with applied(patch, trigger.PIN, sub):
        result, _base, _edited, working_diff = loop_core.quarantine(
            sub,
            predicate,
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
        "forbidden_identifiers": [],
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


def _validate_transport_receipt(
    receipt: object, *, expected: Mapping[str, Any] | None = None
) -> dict[str, Any]:
    """Fail closed on the exact run-level transport receipt schema."""
    if type(receipt) is not dict or set(receipt) != _TRANSPORT_RECEIPT_KEYS:
        raise AutonomousTrialError("transport receipt top-level schema が exact でない")
    if any(
        type(receipt[key]) is not str
        for key in ("schema_version", "mode", "site", "policy_path")
    ) or any(
        type(receipt[key]) is not list
        for key in (
            "admitted_env_keys",
            "source_tls_trust_override_keys",
            "forwarded_tls_trust_override_keys",
        )
    ):
        raise AutonomousTrialError("transport receipt field type が exact でない")
    if (
        receipt["schema_version"] != "claude-transport-receipt/v1"
        or receipt["mode"] != "explicit-http-proxy-env"
        or receipt["site"] != "PEGASUS_COMPUTE"
        or receipt["admitted_env_keys"] != ["http_proxy", "https_proxy"]
        or receipt["policy_path"]
        != "tools/pegasus/policies/transport_v1.json"
        or receipt["source_tls_trust_override_keys"] != []
        or receipt["forwarded_tls_trust_override_keys"] != []
    ):
        raise AutonomousTrialError("transport receipt contract が一致しない")
    endpoint_values = receipt["endpoint_values"]
    if (
        type(endpoint_values) is not dict
        or set(endpoint_values) != {"http_proxy", "https_proxy"}
        or any(type(endpoint_values[key]) is not str for key in endpoint_values)
    ):
        raise AutonomousTrialError("transport receipt endpoint schema が exact でない")
    if not is_valid_pbs_jobid(receipt["pbs_jobid"]):
        raise AutonomousTrialError("transport receipt PBS_JOBID が不正")
    for key in ("endpoint_values_sha256", "policy_sha256"):
        value = receipt[key]
        if type(value) is not str or _LOWER_HEX_RE.fullmatch(value) is None:
            raise AutonomousTrialError("transport receipt hash schema が不正")
    endpoint_bytes = json.dumps(
        endpoint_values,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")
    if hashlib.sha256(endpoint_bytes).hexdigest() != receipt["endpoint_values_sha256"]:
        raise AutonomousTrialError("transport receipt endpoint hash が一致しない")
    if expected is not None and receipt != expected:
        raise AutonomousTrialError("transport receipt が run-level snapshot と一致しない")
    return {
        "schema_version": receipt["schema_version"],
        "mode": receipt["mode"],
        "site": receipt["site"],
        "admitted_env_keys": list(receipt["admitted_env_keys"]),
        "endpoint_values": dict(endpoint_values),
        "endpoint_values_sha256": receipt["endpoint_values_sha256"],
        "policy_path": receipt["policy_path"],
        "policy_sha256": receipt["policy_sha256"],
        "source_tls_trust_override_keys": list(
            receipt["source_tls_trust_override_keys"]
        ),
        "forwarded_tls_trust_override_keys": list(
            receipt["forwarded_tls_trust_override_keys"]
        ),
        "pbs_jobid": receipt["pbs_jobid"],
    }


def _redacted_transport_error(
    exc: BaseException, transport_receipt: Mapping[str, Any] | None
) -> str:
    message = str(exc)
    if transport_receipt is None:
        return message
    endpoint_values = transport_receipt.get("endpoint_values")
    secrets: list[str] = []
    if isinstance(endpoint_values, Mapping):
        secrets.extend(
            value for value in endpoint_values.values()
            if isinstance(value, str) and value
        )
    pbs_jobid = transport_receipt.get("pbs_jobid")
    if isinstance(pbs_jobid, str) and pbs_jobid:
        secrets.append(pbs_jobid)
    for secret in sorted(set(secrets), key=len, reverse=True):
        message = message.replace(secret, "<redacted>")
    return message


def _event_with_transport_receipt(
    event: Mapping[str, Any], transport_receipt: Mapping[str, Any] | None
) -> dict[str, Any]:
    stored = dict(event)
    if transport_receipt is not None:
        stored["transport_receipt"] = _validate_transport_receipt(
            dict(transport_receipt), expected=transport_receipt
        )
    return stored


def _append_provider_init_error(
    *,
    journal: AttemptJournal,
    fatal_error: Mapping[str, str],
    transport_receipt: Mapping[str, Any] | None,
) -> dict[str, Any]:
    safe_error = dict(fatal_error)
    message = safe_error.get("message")
    if isinstance(message, str):
        safe_error["message"] = _redacted_transport_error(
            RuntimeError(message), transport_receipt
        )
    event: dict[str, Any] = {"event": "provider-init-error", **safe_error}
    if transport_receipt is not None:
        event["transport_receipt"] = _validate_transport_receipt(
            dict(transport_receipt), expected=transport_receipt
        )
    return journal.append(event)


def _invoke(
    *, role: str, provider: Any, invocation_id: str, payload: Mapping[str, Any],
    raw_root: Path, journal: AttemptJournal, workload: str, generation: int,
    transport_receipt: Mapping[str, Any] | None = None,
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
        provenance = dict(response.provenance)
        if transport_receipt is None:
            if "transport_receipt" in provenance:
                raise AutonomousTrialError(
                    "transport opt-out provenance に receipt を許可しない"
                )
        else:
            provenance["transport_receipt"] = _validate_transport_receipt(
                provenance.get("transport_receipt"), expected=transport_receipt
            )
        raw_bytes = response.raw_response.encode("utf-8")
        raw_path = raw_root / f"raw_{invocation_id}.txt"
        raw_sha256 = _write_bytes_bound(raw_path, raw_bytes)
        parsed = PARSERS[role](response.raw_response)
    except Exception as exc:
        error_artifacts: dict[str, str] = {}
        invalid = {
            **base,
            "status": "invalid",
            "error_type": type(exc).__name__,
            "error": _redacted_transport_error(exc, transport_receipt),
            "error_artifacts": error_artifacts,
        }
        if transport_receipt is not None:
            invalid["transport_receipt"] = _validate_transport_receipt(
                dict(transport_receipt), expected=transport_receipt
            )
        artifact_root = getattr(provider, "artifact_root", None)
        if isinstance(artifact_root, Path):
            for kind in ("payload", "envelope"):
                candidate = artifact_root / f"{kind}_{invocation_id}.json"
                try:
                    if candidate.is_file() and not candidate.is_symlink():
                        artifact_bytes = candidate.read_bytes()
                        error_artifacts[f"{kind}_path"] = str(candidate)
                        error_artifacts[f"{kind}_sha256"] = _sha256(artifact_bytes)
                except OSError:
                    continue
        event = journal.append(invalid)
        return None, event
    event = journal.append({
        **base,
        "status": "valid",
        "raw_response_path": str(raw_path),
        "raw_response_sha256": raw_sha256,
        "parsed": _jsonable_role_value(role, parsed),
        "provenance": provenance,
    })
    return parsed, event


def _journal_auditor_skip(
    *, invocation_id: str, common: Mapping[str, Any],
    preview_result: Mapping[str, Any], journal: AttemptJournal,
    workload: str, generation: int,
) -> dict[str, Any]:
    evidence = {
        key: value for key, value in preview_result.items()
        if key != "working_diff"
    }
    skip_payload = {**common, "pre_audit": evidence}
    return journal.append({
        "event": "role-attempt",
        "workload": workload,
        "generation": generation,
        "role": "auditor",
        "invocation_id": invocation_id,
        "input_payload_sha256": _sha256(_canonical_json_bytes(skip_payload)),
        "descriptor_sha256": common["descriptor_binding"]["output_sha256"],
        "attempt": 1,
        "retry": False,
        "status": "skipped",
        "skip_reason": "machine-pre-audit-rejection",
        "pre_audit": evidence,
    })


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


def _provider_set(
    *,
    kind: str,
    run_root: Path,
    executable: str,
    allow_pegasus_compute_transport: bool = False,
    transport_admission: ClaudeTransportAdmission | None = None,
    source_env: Mapping[str, str] | None = None,
    projected_provider_factory: Callable[..., Any] | None = None,
) -> dict[str, Any]:
    if type(allow_pegasus_compute_transport) is not bool:
        raise AutonomousTrialError(
            "allow_pegasus_compute_transport は bool 必須"
        )
    if allow_pegasus_compute_transport:
        if kind != "claude-headless":
            raise AutonomousTrialError(
                "Pegasus compute transport は claude-headless provider 専用"
            )
        if not isinstance(transport_admission, ClaudeTransportAdmission):
            raise AutonomousTrialError("transport opt-in に run-level admission が必要")
        if not isinstance(source_env, Mapping):
            raise AutonomousTrialError("transport opt-in に source env snapshot が必要")
    elif transport_admission is not None or source_env is not None:
        raise AutonomousTrialError("transport opt-out に admission/env を渡してはならない")
    provider_factory = (
        ClaudeProjectedRoleProvider
        if projected_provider_factory is None
        else projected_provider_factory
    )
    cross_role_session_tracker = (
        CrossRoleSessionTracker() if kind == "claude-headless" else None
    )
    result: dict[str, Any] = {}
    try:
        for role, (role_file, role_name) in ROLE_FILES.items():
            if kind == "fixture":
                result[role] = FixtureRoleProvider(role)
            elif kind == "claude-headless":
                result[role] = provider_factory(
                    artifact_root=run_root / "provider" / role,
                    role_file=role_file,
                    role_name=role_name,
                    mediated_contract=ROLE_CONTRACTS[role],
                    repository_root=ROOT,
                    executable=executable,
                    environ=source_env,
                    allow_pegasus_compute_transport=allow_pegasus_compute_transport,
                    transport_admission=transport_admission,
                    **(
                        {"cross_role_session_tracker": cross_role_session_tracker}
                        if cross_role_session_tracker is not None
                        else {}
                    ),
                )
            else:  # pragma: no cover - argparse closes this
                raise AutonomousTrialError(f"unknown provider kind: {kind}")
    except BaseException:
        _close_owned_providers(result)
        raise
    return result


def _assert_build_site_opted_in(
    do_build: bool, *, allow_pegasus_compute_transport: bool
) -> None:
    """成果物作成前に build site と transport の明示 opt-in を閉じる。"""
    if not do_build:
        return
    site = trigger._current_site()
    if site == trigger.site_policy.OTHER:
        return
    if site == trigger.site_policy.PEGASUS_COMPUTE:
        if allow_pegasus_compute_transport:
            return
        raise AutonomousTrialError(
            "8c の Pegasus compute build は T-276 の明示 transport opt-in が必要"
        )
    raise AutonomousTrialError(f"8c の build は未受理 site={site!r} では実行できない")


def _assert_build_transport_admitted(
    do_build: bool,
    *,
    transport_admission: ClaudeTransportAdmission | None,
    transport_receipt: Mapping[str, Any] | None,
) -> None:
    """計測到達前に exact admission と run-level receipt の一致を要求する。"""
    if not do_build:
        return
    site = trigger._current_site()
    if site == trigger.site_policy.OTHER:
        return
    if site != trigger.site_policy.PEGASUS_COMPUTE:
        raise AutonomousTrialError(
            f"8c の build は未受理 site={site!r} では実行できない"
        )
    if (
        not isinstance(transport_admission, ClaudeTransportAdmission)
        or transport_receipt is None
    ):
        raise AutonomousTrialError(
            "8c の Pegasus compute build は T-276 transport admission 成功が必要"
        )
    admitted_receipt = _validate_transport_receipt(
        transport_admission.receipt.as_dict()
    )
    _validate_transport_receipt(
        dict(transport_receipt), expected=admitted_receipt
    )


def _finalize_build_cell_admission(cell: Mapping[str, Any]) -> None:
    """Render and validate the Layer-3/admission chain before report publish."""
    campaign_root_value = cell.get("campaign_root")
    if not isinstance(campaign_root_value, str) or not campaign_root_value:
        raise AutonomousTrialError("build cell has no campaign_root for admission validation")
    campaign_root = Path(campaign_root_value).resolve()
    reports = campaign_root / "reports"
    if not reports.is_dir():
        raise AutonomousTrialError("build cell campaign has no reports directory")
    persisted = reports / "layer3_report.json"
    if persisted.exists() or persisted.is_symlink():
        raise AutonomousTrialError("fresh build cell already has a Layer-3 report")
    try:
        layer3 = layer3_report.render(
            campaign_root,
            persisted,
            output_root=campaign_root.parent.parent,
        )
    except layer3_report.Layer3ReportError as exc:
        raise AutonomousTrialError(
            f"build cell campaign admission/Layer-3 validation failed: {exc}"
        ) from exc
    if not isinstance(cell, dict):
        raise AutonomousTrialError("build cell must be mutable before report finalization")
    cell["admission_decision"] = layer3["admission_decision"]


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
    transport_receipt: Mapping[str, Any] | None,
    transport_admission: ClaudeTransportAdmission | None = None,
    build_context: BuildRunContext | None = None,
) -> dict[str, Any]:
    if fatal_error is None:
        _assert_build_transport_admitted(
            do_build,
            transport_admission=transport_admission,
            transport_receipt=transport_receipt,
        )
    cells: list[dict[str, Any]] = []
    if fatal_error is None:
        for workload in selected:
            if time.monotonic() - started_monotonic >= max_wall_s:
                fatal_error = {
                    "type": "SupervisorWallBudget",
                    "message": "wall budget expired before the next workload",
                }
                journal.append(_event_with_transport_receipt(
                    {"event": "supervisor-wall-budget", "workload": workload},
                    transport_receipt,
                ))
                break
            partial: dict[str, Any] = {}
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
                    _partial=partial,
                    transport_receipt=transport_receipt,
                    transport_admission=transport_admission,
                    build_context=build_context,
                )
            except Exception as exc:
                fatal_error = {
                    "type": type(exc).__name__,
                    "message": _redacted_transport_error(exc, transport_receipt),
                }
                journal.append(_event_with_transport_receipt(
                    {
                        "event": "supervisor-error",
                        "workload": workload,
                        **fatal_error,
                    },
                    transport_receipt,
                ))
                partial_cell = partial.get("cell")
                if isinstance(partial_cell, dict):
                    current_generation = partial.get("generation")
                    cell_generations = partial_cell.get("generations")
                    if (
                        isinstance(current_generation, dict)
                        and isinstance(cell_generations, list)
                        and not any(item is current_generation for item in cell_generations)
                    ):
                        cell_generations.append(current_generation)
                    cell = partial_cell
                    cell["stop_reason"] = "supervisor-error"
                    cell["error"] = dict(fatal_error)
                else:
                    cell = {
                        "workload": workload,
                        "generations": [],
                        "stop_reason": "supervisor-error",
                        "error": dict(fatal_error),
                    }
                cells.append(cell)
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
    for cell in cells:
        if do_build:
            _finalize_build_cell_admission(cell)
        else:
            cell["admission_decision"] = {"admission_status": "not-applicable"}
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
    if transport_receipt is not None:
        report["transport_receipt"] = _validate_transport_receipt(
            dict(transport_receipt), expected=transport_receipt
        )
    journal.append(_event_with_transport_receipt(
        {
            "event": "run-finish",
            "status": status,
            "report": str(run_root / "report.json"),
        },
        transport_receipt,
    ))
    report["attempt_journal_sha256"] = _sha256((run_root / "attempts.jsonl").read_bytes())
    assert_autonomous_trial_completeness(
        report=report,
        attempt_journal=run_root / "attempts.jsonl",
    )
    if do_build and cells:
        campaign_parents = {
            Path(cell["campaign_root"]).resolve().parent.parent for cell in cells
        }
        if len(campaign_parents) != 1:
            raise AutonomousTrialError("build cells do not share one campaign output root")
        assert_campaign_layer3_chain(
            report=report,
            output_root=next(iter(campaign_parents)),
        )
    if _sha256((run_root / "attempts.jsonl").read_bytes()) != report[
        "attempt_journal_sha256"
    ]:
        raise AutonomousTrialError(
            "completeness 検査後に attempt journal bytes が変化した"
        )
    _write_json_atomic(run_root / "report.json", report)
    return report


def _run_workload(
    *, workload: str, generations: int, providers: Mapping[str, Any],
    journal: AttemptJournal, run_root: Path, sub: str, do_build: bool,
    cache_root: str, trial_id: str, started_monotonic: float, max_wall_s: int,
    drive: Callable[..., Mapping[str, Any]] = trigger.drive_iteration,
    preview: Callable[..., Mapping[str, Any]] = _preview,
    _partial: dict[str, Any] | None = None,
    transport_receipt: Mapping[str, Any] | None = None,
    transport_admission: ClaudeTransportAdmission | None = None,
    build_context: BuildRunContext | None = None,
) -> dict[str, Any]:
    _validate_generation_budget(generations)
    _assert_build_transport_admitted(
        do_build,
        transport_admission=transport_admission,
        transport_receipt=transport_receipt,
    )
    if type(build_context) is not BuildRunContext:
        raise AutonomousTrialError(
            "workload requires the trial's shared BuildRunContext"
        )
    flags = WORKLOADS[workload]
    descriptor, descriptor_record = _descriptor_for(flags)
    cfg = _campaign_for(
        workload=workload,
        workload_flags=flags,
        descriptor=descriptor,
        descriptor_record=descriptor_record,
        trial_id=trial_id,
        generations=generations,
        build_context=build_context,
    )
    campaign_id = str(ident.campaign_id(cfg))
    if do_build:
        layout = exploration_campaign_layout(campaign_id)
    else:
        layout = CampaignLayout(
            str(run_root / "campaigns" / campaign_id)
        )
    _assert_fresh_campaign_state(layout)
    result: dict[str, Any] = {
        "workload": workload,
        "workload_flags": dict(flags),
        "descriptor": descriptor,
        "descriptor_binding": descriptor_record,
        "campaign_id": campaign_id,
        "campaign_root": layout.root,
        "generations": [],
        "stop_reason": "fixed-generation-budget",
    }
    if _partial is not None:
        _partial["cell"] = result
    perf = _perf_for(flags)
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
            if transport_receipt is not None:
                journal.append(_event_with_transport_receipt(
                    {
                        "event": "supervisor-wall-budget",
                        "workload": workload,
                        "generation": generation,
                    },
                    transport_receipt,
                ))
            break
        generation_record: dict[str, Any] = {"generation": generation, "roles": {}}
        if _partial is not None:
            _partial["generation"] = generation_record
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
            transport_receipt=transport_receipt,
        )
        generation_record["roles"]["planner"] = event
        if planner is None:
            generation_record["outcome"] = "planner-invalid"
            result["generations"].append(generation_record)
            if _partial is not None:
                _partial["generation"] = None
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
            transport_receipt=transport_receipt,
        )
        generation_record["roles"]["coder"] = event
        if coder is None:
            generation_record["outcome"] = "coder-invalid"
            result["generations"].append(generation_record)
            if _partial is not None:
                _partial["generation"] = None
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
            event = _journal_auditor_skip(
                invocation_id=f"{workload}.g{generation}.auditor",
                common=common,
                preview_result=preview_result,
                journal=journal,
                workload=workload,
                generation=generation,
            )
            generation_record["roles"]["auditor"] = event
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
                transport_receipt=transport_receipt,
            )
            generation_record["roles"]["auditor"] = event
            if auditor is None:
                generation_record["outcome"] = "auditor-invalid"
                result["generations"].append(generation_record)
                if _partial is not None:
                    _partial["generation"] = None
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
        drive_kwargs = {
            "layout": layout,
            "cache_root": cache_root,
            "proposal_path": str(proposal_path),
            "extra_sources": ({
                "path": "orchestrator/campaign/p3_autonomous_workload_trial.py",
                "role": "T-178 unattended Python supervisor and descriptor projection",
            },),
        }
        if do_build:
            drive_kwargs["build_context"] = build_context
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
                **drive_kwargs,
            )
        )
        required_harness = {
            "outcome", "variant", "stop_reason", "iteration", "ran",
        }
        missing_harness = sorted(required_harness - set(outcome))
        if missing_harness:
            raise AutonomousTrialError(
                f"harness output に必須 field がない: {missing_harness}"
            )
        if (
            not isinstance(outcome["stop_reason"], str)
            or outcome["stop_reason"] not in DRIVER_STOP_REASONS
        ):
            raise AutonomousTrialError(
                f"harness output の stop_reason が未知: {outcome['stop_reason']!r}"
            )
        if outcome["ran"] or "trigger_gate_binding_commitment" in outcome:
            binding_commitment = outcome.get("trigger_gate_binding_commitment")
            if (
                type(binding_commitment) is not str
                or len(binding_commitment) != 64
                or any(character not in "0123456789abcdef"
                       for character in binding_commitment)
            ):
                raise AutonomousTrialError("harness binding commitment が不正")
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
            transport_receipt=transport_receipt,
        )
        generation_record["roles"]["critic"] = event
        result["generations"].append(generation_record)
        if _partial is not None:
            _partial["generation"] = None
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
    allow_pegasus_compute_transport: bool = False,
    providers: Mapping[str, Any] | None = None,
    drive: Callable[..., Mapping[str, Any]] = trigger.drive_iteration,
    preview: Callable[..., Mapping[str, Any]] = _preview,
    coder_authority: CoderBuildAuthority | None = None,
) -> dict[str, Any]:
    if _TRIAL_ID_RE.fullmatch(trial_id) is None:
        raise AutonomousTrialError(f"trial_id が安全な形式でない: {trial_id!r}")
    if not isinstance(provider_kind, str) or provider_kind not in PROVIDER_KINDS:
        raise AutonomousTrialError(f"unknown provider kind: {provider_kind}")
    if provider_kind == "claude-headless" and providers is not None:
        raise AutonomousTrialError(
            "claude-headless provider は caller 注入を許可しない"
        )
    _validate_generation_budget(generations)
    if isinstance(max_wall_s, bool) or not isinstance(max_wall_s, int) or max_wall_s < 1:
        raise AutonomousTrialError("max_wall_s は正の int 必須")
    if type(allow_pegasus_compute_transport) is not bool:
        raise AutonomousTrialError(
            "allow_pegasus_compute_transport は bool 必須"
        )
    if allow_pegasus_compute_transport and provider_kind != "claude-headless":
        raise AutonomousTrialError(
            "Pegasus compute transport は claude-headless provider 専用"
        )
    if allow_pegasus_compute_transport and providers is not None:
        raise AutonomousTrialError(
            "Pegasus compute transport は owned projected providers 専用"
        )
    selected = list(workloads)
    if not selected or len(selected) != len(set(selected)):
        raise AutonomousTrialError("workloads は重複なしの非空列必須")
    unknown = sorted(set(selected) - set(WORKLOADS))
    if unknown:
        raise AutonomousTrialError(f"unknown workloads: {unknown}")
    _assert_build_site_opted_in(
        do_build,
        allow_pegasus_compute_transport=allow_pegasus_compute_transport,
    )
    if do_build and coder_authority is None:
        raise AutonomousTrialError(
            "build trial requires parser-issued --allow-coder-derived-build authority"
        )
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
    build_context = build_run_context(
        generator_id=GeneratorId.S8A_TRIGGER_SWEEP,
        coder_authority=coder_authority if do_build else None,
    )
    transport_admission: ClaudeTransportAdmission | None = None
    transport_receipt: dict[str, Any] | None = None
    source_env_snapshot: dict[str, str] | None = None
    admission_error: BaseException | None = None
    if allow_pegasus_compute_transport:
        source_env_snapshot = dict(os.environ)
        try:
            transport_admission = admit_claude_transport(
                source_env=source_env_snapshot,
                repository_root=ROOT,
            )
            transport_receipt = _validate_transport_receipt(
                transport_admission.receipt.as_dict()
            )
            journal.append({
                "event": "transport-admission",
                "transport_receipt": transport_receipt,
            })
        except Exception as exc:
            admission_error = exc
            journal.append({
                "event": "transport-admission-error",
                "type": type(exc).__name__,
                "message": _redacted_transport_error(exc, None),
            })
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
    fatal_error: dict[str, str] | None = (
        {
            "type": type(admission_error).__name__,
            "message": _redacted_transport_error(admission_error, None),
        }
        if admission_error is not None
        else None
    )
    try:
        try:
            if fatal_error is not None:
                raise AutonomousTrialError("transport admission failed")
            active_providers = (
                dict(providers)
                if providers is not None
                else _provider_set(
                    kind=provider_kind,
                    run_root=run_root,
                    executable=claude_executable,
                    allow_pegasus_compute_transport=allow_pegasus_compute_transport,
                    transport_admission=transport_admission,
                    source_env=source_env_snapshot,
                )
            )
        except Exception as exc:
            if fatal_error is None:
                fatal_error = {
                    "type": type(exc).__name__,
                    "message": _redacted_transport_error(exc, transport_receipt),
                }
                _append_provider_init_error(
                    journal=journal,
                    fatal_error=fatal_error,
                    transport_receipt=transport_receipt,
                )
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
            transport_receipt=transport_receipt,
            transport_admission=transport_admission,
            build_context=build_context,
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
        "--provider", required=True, choices=tuple(sorted(PROVIDER_KINDS))
    )
    parser.add_argument("--workloads", type=_parse_workloads, default=list(WORKLOADS))
    parser.add_argument("--max-generations", type=int, default=1)
    parser.add_argument("--max-wall-seconds", type=int, default=DEFAULT_MAX_WALL_S)
    parser.add_argument("--no-build", action="store_true")
    add_coder_build_authority_argument(parser)
    parser.add_argument("--claude-executable", default="claude")
    parser.add_argument(
        "--allow-pegasus-compute-transport",
        action="store_true",
        default=False,
    )
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
    _assert_build_site_opted_in(
        not args.no_build,
        allow_pegasus_compute_transport=args.allow_pegasus_compute_transport,
    )
    if not args.no_build and args.coder_build_authority is None:
        raise BuildAdmissionError(
            "--allow-coder-derived-build の明示 opt-in が必要"
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
            allow_pegasus_compute_transport=args.allow_pegasus_compute_transport,
            coder_authority=(
                None if args.no_build else args.coder_build_authority
            ),
        )
    print(json.dumps({
        "status": report["status"],
        "report": str(run_root / "report.json"),
        "cells": len(report["cells"]),
    }, ensure_ascii=False, sort_keys=True))
    return 0 if report["status"] == "complete" else 2


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
