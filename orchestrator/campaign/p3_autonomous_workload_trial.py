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
import copy
import contextlib
import contextvars
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
from types import MappingProxyType
from typing import Any

if __package__ in {None, ""}:  # pragma: no cover - direct CLI execution
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
    __package__ = "orchestrator.campaign"

from . import p3_s4_loop as loop_core
from . import p3_s4_loop_trigger_gating as trigger
from . import reflux_formal_consumer
from . import reflux_origin_binding
from . import reflux_origin_client
from . import reflux_origin_ledger
from . import reflux_origin_topology
from . import s8c_preregistration
from . import trial_registry
from .reflux_source_closure import ValidatedSourceClosure
from .reflux_ir import emit_predicate, parse_wire
from .autonomous_trial_completeness import (
    assert_campaign_layer3_chain,
    assert_autonomous_trial_completeness,
    cell_admission_failure_projection,
    is_positive_cell_admission_decision,
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
    _reject_worktree_container,
    _resolve_exploration_output_root,
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
from .s8c_generation_projection import (
    LEAKPROOF_CONTEXT,
    GatingSpecSnapshot,
    PayloadValidationReceipt,
    apply_critic_feedback,
    snapshot_gating_spec,
    validate_coder_payload,
    validate_planner_payload,
)



# The axis driver imports the campaign namespace directly.  Keep the U1 run
# context and identity types on that same module identity so exact-type seals
# survive package and direct-script entry points alike.
from . import env_contract, ident  # noqa: E402
from .artifact_admission import (  # noqa: E402
    CampaignReadPurpose,
    require_admitted_campaign,
)
from .build_admission import (  # noqa: E402
    BuildAdmissionError,
    BuildRunContext,
    CoderBuildAuthority,
    GeneratorId,
    add_coder_build_authority_argument,  # compatibility export for unit fixtures
    add_registered_coder_build_authority_argument,
    build_run_context,
)


ROOT = Path(__file__).resolve().parents[2]
SCHEMA_VERSION = "p3-autonomous-workload-trial/v3"
REPORT_SCHEMA_VERSION = "p3-autonomous-workload-trial-report/v3"
MAX_GENERATIONS = 10
MAX_APPROVED_GENERATIONS = 2
_INITIAL_ROLE_METRICS = MappingProxyType({
    "throughput_ops_sec": None,
    "abort_rate": None,
    "latency_ns": None,
    "llc_miss_rate": None,
    "ipc": None,
})
DEFAULT_MAX_WALL_S = 3600
PROVIDER_KINDS = frozenset(("fixture", "claude-headless"))
_DRIVE_NOT_PROVIDED: Any = object()
_PREVIEW_NOT_PROVIDED: Any = object()
DRIVER_STOP_REASONS = frozenset((
    "continue",
    "converged",
    "reverse-exhausted",
    "budget-iterations",
    "budget-walltime",
))
GENERATION_DRIVER_WRAPPER = "s8c-generation/v1"
_STANDARD_GENERATION_DRIVER = {
    "wrapper": GENERATION_DRIVER_WRAPPER,
    "delegate": "trigger.drive_iteration",
}
_INJECTED_GENERATION_DRIVER = {
    "wrapper": GENERATION_DRIVER_WRAPPER,
    "delegate": "caller-injected-unsupported",
}
_AUTHORITATIVE_ACCOUNTING = "supervisor-authoritative"
_UNSUPPORTED_ACCOUNTING = "excluded-caller-injected-unsupported"
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

# Producer が journal へ添える自己申告 annotation。artifact acceptance gate ではない。
AUDITOR_DIFF_DECLASSIFICATION_POLICY_ID = (
    "t244-auditor-diff-declassification/v1"
)
AUDITOR_DIFF_DECLASSIFICATION_POLICY = {
    "source_class": "candidate-wire",
    "current_precondition": "raw-ir-equals-effective-ir/v1",
    "sunset_trigger": "reflux-control-separates-raw-and-effective-ir/v1",
    "successor": {
        "working_diff_source": "independent-canonical-emitter-from-raw-ir/v1",
        "allowed_json_pointers": ["/working_diff"],
        "forbidden_json_pointers": ["/diff_digest"],
    },
}
AUDITOR_DIFF_DECLASSIFICATION_POLICY_SHA256 = _sha256(
    _canonical_json_bytes(AUDITOR_DIFF_DECLASSIFICATION_POLICY)
)

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
Null metrics mean not yet observed and must not be invented.
For generation 2 and later, critic_feedback is the complete supervisor-projected
cross-generation diagnostic input; do not infer excluded critic prose.
Return JSON only, with exactly:
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
Every element of violations must be exactly {"type":N}, where N is an integer
auditor gallery code from 1 through 16. Every element of nits must be exactly
{"type":"nit"}. Every element of proposed_tests must be an object
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

_COMMON_PAYLOAD_KEYS = frozenset({
    "schema_version", "pilot_scope", "scientific_claim", "workload",
    "generation", "workload_descriptor", "descriptor_binding",
    "attempt_policy", "stop_policy",
})
ROLE_PAYLOAD_KEY_SPEC = {
    "planner-generation-1": sorted(_COMMON_PAYLOAD_KEYS | {
        "current_perf", "leading_indicators", "whiteboard",
    }),
    "planner-generation-next": sorted(_COMMON_PAYLOAD_KEYS | {
        "current_perf", "leading_indicators", "whiteboard", "critic_feedback",
    }),
    "coder": sorted(_COMMON_PAYLOAD_KEYS | {
        "leakproof_context", "gating_spec", "planner_direction", "baseline",
        "whiteboard",
    }),
    "auditor": sorted(_COMMON_PAYLOAD_KEYS | {
        "working_diff", "diff_digest", "designated_source_context",
        "correctness_digest",
    }),
    "auditor-skip": sorted(_COMMON_PAYLOAD_KEYS | {"pre_audit"}),
    "critic": sorted(_COMMON_PAYLOAD_KEYS | {
        "harness_result", "critic_digest",
    }),
}
ROLE_PAYLOAD_ALLOWLIST_SHA256 = _sha256(
    _canonical_json_bytes(ROLE_PAYLOAD_KEY_SPEC)
)

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


@dataclasses.dataclass(frozen=True, slots=True)
class PreparedCampaignIdentity:
    """Pure producer projection used by both preflight and execution."""

    descriptor: Mapping[str, Any]
    descriptor_record: Mapping[str, Any]
    campaign: CampaignConfig
    campaign_id: str


@dataclasses.dataclass(frozen=True, slots=True)
class OriginBindingRequest:
    """Primary issuer inputs plus the explicitly selected typed ledger client."""

    client: reflux_origin_client.OriginLedgerClient | None
    validated_source_closure: ValidatedSourceClosure
    authority_blob_bytes: bytes
    source_closure_bytes: bytes
    provisioning_receipt: Mapping[str, object]


@dataclasses.dataclass(frozen=True, slots=True)
class OriginProducerInputs:
    """Closed formal-consumer inputs supplied by the logical producer."""

    run_plan: reflux_origin_topology.RecoveryEnvelope
    result_record_bytes: tuple[bytes, ...]
    evidence_root: Path
    verifier_policy_bytes: bytes
    enforcement_arm: str
    generator_closure: Mapping[str, object]
    terminal_operation_id: str


@dataclasses.dataclass(slots=True)
class OriginTrialRuntime:
    """One in-process capability threaded through the bounded trial."""

    capability: reflux_origin_binding.OriginBindingCapability
    client: reflux_origin_client.OriginLedgerClient
    binding_request: OriginBindingRequest
    producer_inputs: OriginProducerInputs
    launch_admission_record_sha256: str
    initial_snapshot: reflux_origin_ledger.OriginSnapshot
    terminal_projection: (
        reflux_formal_consumer.OriginTerminalProjection | None
    ) = None


@dataclasses.dataclass(frozen=True, slots=True)
class OriginPreflightFailure:
    error_type: str
    message: str


@dataclasses.dataclass(frozen=True, slots=True)
class OriginPartialTrialReport:
    report: Mapping[str, Any] | None
    error_type: str | None = None
    message: str | None = None


@dataclasses.dataclass(frozen=True, slots=True)
class OriginCompletedTrialReport:
    report: Mapping[str, Any]


_RUN_SCOPE_SEAL = object()


@dataclasses.dataclass(frozen=True, slots=True)
class _RunScopeBinding:
    admission: trial_registry.TrialLaunchAdmission
    _seal: object = dataclasses.field(repr=False)
    origin_capability: reflux_origin_binding.OriginBindingCapability | None = None


_ACTIVE_TRIAL_BINDING: contextvars.ContextVar[
    _RunScopeBinding | None
] = contextvars.ContextVar("active_trial_binding", default=None)


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
        raise AutonomousTrialError("response object keys 不一致")


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
        # role_query_count means provider.invoke call count.  It is not an
        # estimate of external queries made inside a provider implementation.
        self.role_query_count = 0

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
    contract: env_contract.ExecutionEnvironmentContract,
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
    cfg = ident.bind_admission_policy(cfg, build_context.policy)
    return ident.bind_environment_contract(cfg, contract)


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


def _prepare_campaign_identity(
    *,
    workload: str,
    trial_id: str,
    generations: int,
    site: str,
    contract: env_contract.ExecutionEnvironmentContract,
    build_context: BuildRunContext,
) -> PreparedCampaignIdentity:
    """Derive the existing descriptor/campaign identity without writing artifacts."""
    flags = WORKLOADS[workload]
    descriptor, descriptor_record = _descriptor_for(flags)
    campaign = _campaign_for(
        workload=workload,
        workload_flags=flags,
        descriptor=descriptor,
        descriptor_record=descriptor_record,
        trial_id=trial_id,
        generations=generations,
        contract=contract,
        build_context=build_context,
    )
    campaign = trigger._campaign_cfg_for_site(
        campaign, site, _contract=contract,
    )
    return PreparedCampaignIdentity(
        descriptor=descriptor,
        descriptor_record=descriptor_record,
        campaign=campaign,
        campaign_id=str(ident.campaign_id(campaign)),
    )


def _trial_launch_admission(
    *,
    trial_manifest: Path | None,
    trial_id: str,
    workloads: Sequence[str],
    generations: int,
    allow_unregistered_exploratory: bool,
    effective_preregistration: (
        s8c_preregistration.EffectivePreregistration | None
    ),
) -> trial_registry.TrialLaunchAdmission:
    """Run the artifact-free launcher gate at either public boundary."""
    registry_path = ROOT / trial_registry.DEFAULT_REGISTRY_PATH
    if trial_manifest is None:
        return trial_registry.admit_unregistered_exploratory(
            trial_id=trial_id,
            workloads=workloads,
            allow_unregistered_exploratory=allow_unregistered_exploratory,
            repository_root=ROOT,
            registry_path=registry_path,
        )
    admission = trial_registry.admit_registered_launch(
        effective_preregistration=effective_preregistration,
        manifest_path=Path(trial_manifest),
        trial_id=trial_id,
        workloads=workloads,
        repository_root=ROOT,
        registry_path=registry_path,
    )
    binding = admission.binding
    if binding is None:  # pragma: no cover - sealed registry postcondition
        raise trial_registry.TrialRegistryError(
            "[launch-admission] registered admission has no binding"
        )
    identity_context = build_run_context(
        generator_id=GeneratorId.S8A_TRIGGER_SWEEP,
    )
    site = trigger._current_site()
    contract = trigger._admit_env_contract(site)
    prepared = _prepare_campaign_identity(
        workload=binding.workload,
        trial_id=trial_id,
        generations=generations,
        site=site,
        contract=contract,
        build_context=identity_context,
    )
    trial_registry.assert_campaign_binding(
        binding,
        actual_campaign_id=prepared.campaign_id,
    )
    return admission


def _prepare_origin_trial_runtime(
    *,
    admission: trial_registry.TrialLaunchAdmission,
    request: OriginBindingRequest,
    producer_inputs: OriginProducerInputs,
    trial_id: str,
    selected: list[str],
    generations: int,
    trial_manifest: Path | None,
    effective_preregistration: (
        s8c_preregistration.EffectivePreregistration | None
    ),
    build_context: BuildRunContext,
) -> OriginTrialRuntime:
    """Issue and exercise the fixture capability before lifecycle start."""

    if type(request) is not OriginBindingRequest:
        raise TypeError("origin_binding_request must be an OriginBindingRequest")
    if type(producer_inputs) is not OriginProducerInputs:
        raise TypeError("origin_producer_inputs must be an OriginProducerInputs")
    if request.client is None:
        raise reflux_origin_client.OriginLedgerClientError(
            "origin-bound run requires an explicit typed ledger client"
        )
    if type(request.client) is not reflux_origin_client.OriginLedgerClient:
        raise reflux_origin_client.OriginLedgerClientError(
            "origin-bound run requires the exact typed ledger client"
        )
    if admission.mode != "registered-effective" or admission.binding is None:
        raise reflux_origin_binding.OriginBindingError(
            "[launch-mode] origin request requires registered-effective admission"
        )
    if trial_manifest is None:
        raise reflux_origin_binding.OriginBindingError(
            "[launch-mode] origin request requires a registered manifest"
        )
    if len(selected) != 1:
        raise reflux_origin_binding.OriginBindingError(
            "[trial-workload] origin request requires exactly one workload"
        )
    if type(producer_inputs.run_plan) is not reflux_origin_topology.RecoveryEnvelope:
        raise TypeError("origin producer run_plan must be a RecoveryEnvelope")
    if type(producer_inputs.result_record_bytes) is not tuple or any(
        type(raw) is not bytes for raw in producer_inputs.result_record_bytes
    ):
        raise TypeError("origin result_record_bytes must be a tuple of bytes")
    if type(producer_inputs.verifier_policy_bytes) is not bytes:
        raise TypeError("origin verifier_policy_bytes must be bytes")
    if (
        type(producer_inputs.enforcement_arm) is not str
        or not producer_inputs.enforcement_arm
        or type(producer_inputs.terminal_operation_id) is not str
        or not producer_inputs.terminal_operation_id
    ):
        raise TypeError("origin producer tokens must be non-empty strings")

    launch = reflux_origin_binding.rederive_launch_admission(
        admission,
        effective_preregistration=effective_preregistration,
        manifest_path=Path(trial_manifest),
        trial_id=trial_id,
        workloads=selected,
        allow_unregistered_exploratory=False,
        repository_root=ROOT,
        registry_path=ROOT / trial_registry.DEFAULT_REGISTRY_PATH,
    )
    site = trigger._current_site()
    contract = trigger._admit_env_contract(site)
    prepared_campaign = _prepare_campaign_identity(
        workload=selected[0],
        trial_id=trial_id,
        generations=generations,
        site=site,
        contract=contract,
        build_context=build_context,
    )
    prepared_origin = reflux_origin_binding.prepare_origin_identity(
        authority_blob_bytes=request.authority_blob_bytes,
        source_closure_bytes=request.source_closure_bytes,
        provisioning_receipt=request.provisioning_receipt,
        validated_source_closure=request.validated_source_closure,
    )
    capability = reflux_origin_binding.issue_origin_binding_capability(
        launch_rederivation=launch,
        prepared_campaign=prepared_campaign,
        prepared_origin=prepared_origin,
        validated_source_closure=request.validated_source_closure,
        authority_blob_bytes=request.authority_blob_bytes,
        source_closure_bytes=request.source_closure_bytes,
        provisioning_receipt=request.provisioning_receipt,
        effective_preregistration=effective_preregistration,
        manifest_path=Path(trial_manifest),
        trial_id=trial_id,
        workloads=selected,
        allow_unregistered_exploratory=False,
        repository_root=ROOT,
        registry_path=ROOT / trial_registry.DEFAULT_REGISTRY_PATH,
        trial_workload=selected[0],
        expected_axis_semantics_sha256=prepared_origin.axis_semantics_sha256,
        expected_verifier_policy_sha256=prepared_origin.verifier_policy_sha256,
        expected_environment_contract_sha256=(
            prepared_origin.environment_contract_sha256
        ),
        store_scope=request.client.store_scope,
    )
    client = reflux_origin_client.require_origin_ledger_client(
        capability, request.client
    )
    initial_snapshot = client.read_origin(capability)
    launch_record = trial_registry.launch_admission_record(
        admission, origin_binding=capability
    )
    return OriginTrialRuntime(
        capability=capability,
        client=client,
        binding_request=request,
        producer_inputs=producer_inputs,
        launch_admission_record_sha256=hashlib.sha256(
            _canonical_json_bytes(launch_record)
        ).hexdigest(),
        initial_snapshot=initial_snapshot,
    )


def _launch_admission_record(
    admission: trial_registry.TrialLaunchAdmission,
    origin_capability: reflux_origin_binding.OriginBindingCapability | None,
) -> dict[str, Any]:
    if origin_capability is None:
        return trial_registry.launch_admission_record(admission)
    return trial_registry.launch_admission_record(
        admission, origin_binding=origin_capability
    )


def _complete_origin_runtime(runtime: OriginTrialRuntime) -> None:
    """Evaluate and commit the sole abort-only formal terminal result."""

    if type(runtime) is not OriginTrialRuntime:
        raise TypeError("origin runtime has the wrong exact type")
    capability = reflux_origin_binding.assert_issued_origin_binding_capability(
        runtime.capability
    )
    snapshot = runtime.client.read_origin(capability)
    sealed_batches = runtime.client.read_sealed_batches(capability)
    producer = runtime.producer_inputs
    result = reflux_formal_consumer.evaluate_formal_origin(
        capability=capability,
        source_closure=runtime.binding_request.validated_source_closure,
        run_plan=producer.run_plan,
        authority_blob_bytes=runtime.binding_request.authority_blob_bytes,
        launch_admission_record_sha256=(
            runtime.launch_admission_record_sha256
        ),
        origin_snapshot=snapshot,
        sealed_batches=sealed_batches,
        result_record_bytes=producer.result_record_bytes,
        evidence_root=Path(producer.evidence_root),
        verifier_policy_bytes=producer.verifier_policy_bytes,
        enforcement_arm=producer.enforcement_arm,
        generator_closure=producer.generator_closure,
        operation_id=producer.terminal_operation_id,
    )
    runtime.terminal_projection = result.projection
    runtime.client.commit_formal_result(
        capability,
        operation_id=producer.terminal_operation_id,
        expected_state_commitment=snapshot.state_commitment,
        result=result,
    )


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


def _planner_current_perf_payload(
    frozen_perf: Mapping[str, Any],
    *,
    current_metrics: Mapping[str, Any],
    contention_level: str,
) -> dict[str, Any]:
    """Assembly anchor: production ignores generation-updated metrics."""

    del current_metrics, contention_level
    return dict(frozen_perf)


def _planner_leading_indicators_payload(
    frozen_leading: Mapping[str, Any],
    *,
    current_metrics: Mapping[str, Any],
    contention_level: str,
) -> dict[str, Any]:
    """Assembly anchor: production ignores generation-updated metrics."""

    del current_metrics, contention_level
    return dict(frozen_leading)


def _coder_baseline_payload(
    frozen_perf: Mapping[str, Any],
    *,
    current_metrics: Mapping[str, Any],
    contention_level: str,
) -> dict[str, Any]:
    """Assembly anchor: production ignores generation-updated metrics."""

    del current_metrics, contention_level
    return dict(frozen_perf)


def _generation_driver_identity(
    drive: Callable[..., Mapping[str, Any]],
) -> dict[str, str]:
    return dict(
        _STANDARD_GENERATION_DRIVER
        if drive is trigger.drive_iteration
        else _INJECTED_GENERATION_DRIVER
    )


def _accounting_authority(
    drive: Callable[..., Mapping[str, Any]],
) -> str:
    return (
        _AUTHORITATIVE_ACCOUNTING
        if drive is trigger.drive_iteration
        else _UNSUPPORTED_ACCOUNTING
    )


def _bench_wall_seconds(
    outcome: Mapping[str, Any], *, authoritative: bool,
) -> float:
    """Project current-attempt bench time from pipeline bench_wall_s only."""

    if not authoritative:
        return 0.0
    if outcome.get("outcome") == "duplicate" or outcome.get("ran") is False:
        return 0.0
    if outcome.get("outcome") in {"dry-pass", "rejected", "stopped-before"}:
        return 0.0
    records = outcome.get("records")
    if not isinstance(records, Mapping):
        return 0.0
    candidates: list[float] = []
    for record in records.values():
        if not isinstance(record, Mapping) or "bench_wall_s" not in record:
            continue
        raw = record["bench_wall_s"]
        if isinstance(raw, bool) or not isinstance(raw, (int, float)):
            raise AutonomousTrialError("bench_wall_s は有限非負 number 必須")
        value = float(raw)
        if not math.isfinite(value) or value < 0.0:
            raise AutonomousTrialError("bench_wall_s は有限非負 number 必須")
        candidates.append(value)
    if len(candidates) > 1:
        raise AutonomousTrialError("current attempt の bench_wall_s が一意でない")
    return candidates[0] if candidates else 0.0


def _new_generation_accounting(
    *, workload: str, generation: int, journal: AttemptJournal,
    generation_driver: Mapping[str, str], gating_spec_sha256: str,
    authority: str,
) -> dict[str, Any]:
    return {
        "workload": workload,
        "generation": generation,
        "state": "pending-pre-invoke-failure",
        "role_query_start": journal.role_query_count,
        "auditor_pre_audit_skipped": False,
        "bench_wall_seconds": 0.0,
        "generation_driver": dict(generation_driver),
        "gating_spec_sha256": gating_spec_sha256,
        "accounting_authority": authority,
        "finalized": False,
    }


def _append_generation_accounting(
    accounting: dict[str, Any], *, journal: AttemptJournal,
    generation_record: dict[str, Any] | None,
) -> None:
    if accounting.get("finalized") is not False:
        raise AutonomousTrialError("generation accounting は一度だけ確定可能")
    accounting["finalized"] = True
    bench = accounting["bench_wall_seconds"]
    if generation_record is not None:
        generation_record["bench_wall_seconds"] = bench
        generation_record["generation_driver"] = dict(
            accounting["generation_driver"]
        )
        generation_record["gating_spec_sha256"] = accounting[
            "gating_spec_sha256"
        ]
    journal.append({
        "event": "generation-accounting",
        "workload": accounting["workload"],
        "generation": accounting["generation"],
        "state": accounting["state"],
        "provider_invoke_count": (
            journal.role_query_count - accounting["role_query_start"]
        ),
        "auditor_pre_audit_skipped": accounting[
            "auditor_pre_audit_skipped"
        ],
        "bench_wall_seconds": bench,
        "generation_driver": dict(accounting["generation_driver"]),
        "gating_spec_sha256": accounting["gating_spec_sha256"],
        "accounting_authority": accounting["accounting_authority"],
    })


def _drive_s8c_generation(
    *, drive: Callable[..., Mapping[str, Any]], cfg: CampaignConfig,
    perf: PerfConfig, planner: Any, coder: Any, auditor: AuditorVerdict,
    prior_reverse: bool | None, sub: str, do_build: bool,
    layout: CampaignLayout, cache_root: str, proposal_path: Path,
    resolved_site: str, contract: env_contract.ExecutionEnvironmentContract,
    build_context: BuildRunContext,
) -> tuple[dict[str, Any], dict[str, str]]:
    """Call the selected generation delegate exactly once and bind identity."""

    driver = _generation_driver_identity(drive)
    drive_kwargs: dict[str, Any] = {
        "layout": layout,
        "cache_root": cache_root,
        "proposal_path": str(proposal_path),
        "extra_sources": ({
            "path": "orchestrator/campaign/p3_autonomous_workload_trial.py",
            "role": "T-178 unattended Python supervisor and descriptor projection",
        },),
    }
    if drive is trigger.drive_iteration:
        drive_kwargs.update({
            "_resolved_site": resolved_site,
            "_contract": contract,
        })
    if do_build:
        drive_kwargs["build_context"] = build_context
    outcome = dict(drive(
        cfg,
        perf,
        planner,
        coder,
        auditor,
        prior_reverse,
        sub,
        do_build,
        **drive_kwargs,
    ))
    # Caller-injected delegates predate the explicit digest-production signal.
    # Absence is conservatively projected to false: no digest is consumed, even
    # if a stale same-named file exists.  The standard delegate supplies the
    # exact bool itself.
    outcome.setdefault("critic_digest_generated", False)
    required_harness = {
        "outcome", "variant", "stop_reason", "iteration", "ran",
        "critic_digest_generated",
    }
    missing_harness = sorted(required_harness - set(outcome))
    if missing_harness:
        raise AutonomousTrialError(
            f"harness output に必須 field がない: {missing_harness}"
        )
    if type(outcome["critic_digest_generated"]) is not bool:
        raise AutonomousTrialError(
            "harness output の critic_digest_generated は exact bool 必須"
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
    return outcome, driver


def _jsonable_role_value(role: str, parsed: Any) -> dict[str, Any]:
    if role == "planner":
        return dataclasses.asdict(parsed)
    if role == "coder":
        # The raw response/proposal artifact is the authority for replay.  The
        # journal and report expose only a closed projection: neither the raw
        # wire nor coder-authored free text may cross this disclosure boundary.
        return {
            "axis": parsed.axis,
            "confidence": parsed.confidence,
            "justification_present": bool(parsed.justification.strip()),
        }
    if role == "auditor":
        # Raw auditor strings remain in the non-projected raw response artifact.
        # Trial report / attempt journal receive only this closed code/count view.
        return {
            "verdict": parsed.verdict,
            "diff_digest": parsed.diff_digest,
            "violation_codes": [entry["type"] for entry in parsed.violations],
            "nit_count": len(parsed.nits),
            "proposed_test_count": len(parsed.proposed_tests),
            "uncertainty_present": bool(parsed.uncertainty.strip()),
        }
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
    validation_receipt: PayloadValidationReceipt | None = None,
) -> tuple[Any | None, dict[str, Any]]:
    input_sha256 = _sha256(_canonical_json_bytes(payload))
    if validation_receipt is not None:
        if role not in {"planner", "coder"}:
            raise AutonomousTrialError(
                f"{role} に payload validation receipt を許可しない"
            )
        if type(validation_receipt) is not PayloadValidationReceipt:
            raise AutonomousTrialError(
                f"{role} payload validation receipt の型が不正"
            )
        validation_receipt.assert_bound_to(
            role=role,
            payload=payload,
            payload_allowlist_sha256=ROLE_PAYLOAD_ALLOWLIST_SHA256,
        )
    declassifications: list[dict[str, Any]] = []
    if role == "auditor":
        declassifications.append({
            "policy_id": AUDITOR_DIFF_DECLASSIFICATION_POLICY_ID,
            "policy_sha256": AUDITOR_DIFF_DECLASSIFICATION_POLICY_SHA256,
            "disclosures": [
                {
                    "json_pointer": "/working_diff",
                    "transform": "identity",
                    "value_sha256": _sha256(
                        _canonical_json_bytes(payload["working_diff"])
                    ),
                },
                {
                    "json_pointer": "/diff_digest",
                    "transform": "sha256-hex-of-/working_diff",
                    "value_sha256": _sha256(
                        _canonical_json_bytes(payload["diff_digest"])
                    ),
                },
            ],
        })
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
        "declassifications": declassifications,
        "payload_exact_keys": sorted(payload),
        "payload_allowlist_sha256": ROLE_PAYLOAD_ALLOWLIST_SHA256,
    }
    if validation_receipt is not None:
        base["payload_validation_receipt"] = validation_receipt.as_dict()
    try:
        # This is the single accounting point: every provider.invoke call,
        # including calls that raise or later fail parsing, receives one ordinal.
        journal.role_query_count += 1
        base["role_query_ordinal"] = journal.role_query_count
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
        "declassifications": [],
        "payload_exact_keys": sorted(skip_payload),
        "payload_allowlist_sha256": ROLE_PAYLOAD_ALLOWLIST_SHA256,
        # No provider.invoke call occurred on the pre-audit skip path.
        "role_query_ordinal": None,
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
    _assert_build_transport_admitted_for_site(
        trigger._current_site(),
        do_build,
        transport_admission=transport_admission,
        transport_receipt=transport_receipt,
    )


def _assert_build_transport_admitted_for_site(
    site: str,
    do_build: bool,
    *,
    transport_admission: ClaudeTransportAdmission | None,
    transport_receipt: Mapping[str, Any] | None,
) -> None:
    """解決済み site に対する exact transport admission を検査する。"""
    if not do_build:
        return
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


def _finalize_build_cell_admission(
    cell: Mapping[str, Any],
    *,
    launch_admission: trial_registry.TrialLaunchAdmission,
) -> None:
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


def _finalize_cell_admission(
    cell: dict[str, Any],
    *,
    do_build: bool,
    launch_admission: trial_registry.TrialLaunchAdmission,
    journal: AttemptJournal,
) -> bool:
    """Finalize only the cell admission boundary.

    Only an expected build finalizer failure becomes a diagnostic decision.
    Unexpected exception types still cross this boundary unchanged.
    """
    if do_build:
        try:
            _finalize_build_cell_admission(
                cell, launch_admission=launch_admission,
            )
        except AutonomousTrialError as exc:
            failure_message = str(exc)
            if not failure_message:
                raise AutonomousTrialError(
                    "cell admission failure has an empty diagnostic message"
                ) from exc
            pending_critics = cell.get("_pending_critics", [])
            if type(pending_critics) is not list:
                raise AutonomousTrialError(
                    "pending critic state must be an exact list at admission failure"
                ) from exc
            if "pending_critic_disposition" in cell:
                raise AutonomousTrialError(
                    "pending critic disposition was already recorded"
                ) from exc
            discarded = len(pending_critics)
            for pending in list(pending_critics):
                if type(pending) is not dict:
                    raise AutonomousTrialError(
                        "pending critic entry must be an exact dict"
                    ) from exc
                if pending.get("critic_attempted") is not False:
                    raise AutonomousTrialError(
                        "admission failure cannot discard an attempted critic"
                    ) from exc
                accounting = pending.get("accounting")
                if type(accounting) is not dict:
                    raise AutonomousTrialError(
                        "pending critic accounting state is absent"
                    ) from exc
                generation = pending.get("generation")
                generation_record = next(
                    (
                        record
                        for record in cell.get("generations", [])
                        if isinstance(record, dict)
                        and record.get("generation") == generation
                    ),
                    None,
                )
                # This pending generation has no accounting event yet.  Close
                # its sole event with the already-supported partial state;
                # role-invalid generations have no pending entry and therefore
                # receive no duplicate append here.
                accounting["state"] = "partial-generation"
                _append_generation_accounting(
                    accounting,
                    journal=journal,
                    generation_record=generation_record,
                )
            cell.pop("_pending_critics", None)
            cell["pending_critic_disposition"] = {
                "schema_version": (
                    "p3-autonomous-workload-trial-"
                    "pending-critic-disposition/v1"
                ),
                "action": "discarded",
                "reason": "cell-admission-failure",
                "count": discarded,
            }
            cell["admission_decision"] = {
                "schema_version": (
                    "p3-autonomous-workload-trial-"
                    "cell-admission-failure/v1"
                ),
                "admission_status": "failed",
                "error": {
                    "type": "AutonomousTrialError",
                    "message": failure_message,
                },
            }
            return False
    else:
        cell["admission_decision"] = {"admission_status": "not-applicable"}
    return True


def _run_one_pending_critic(
    cell: dict[str, Any],
    *,
    providers: Mapping[str, Any],
    journal: AttemptJournal,
    run_root: Path,
    transport_receipt: Mapping[str, Any] | None,
    preserve_stop_reason: bool = False,
    require_recomputed_digest: bool = False,
) -> dict[str, Any] | None:
    pending_critics = cell.get("_pending_critics")
    if type(pending_critics) is not list or not pending_critics:
        raise AutonomousTrialError("pending critic が存在しない")
    pending = pending_critics[0]
    if type(pending) is not dict:
        raise AutonomousTrialError("pending critic state は exact dict 必須")
    attempted = pending.get("critic_attempted")
    if type(attempted) is not bool:
        raise AutonomousTrialError("pending critic attempted state は exact bool 必須")
    if attempted:
        raise AutonomousTrialError("pending critic の二重 attempt を拒否")
    # Commit at-most-once state before admission, digest I/O, or provider work.
    pending["critic_attempted"] = True
    generation_record: dict[str, Any] | None = None
    accounting = pending.get("accounting")
    if type(accounting) is not dict:
        raise AutonomousTrialError("pending critic accounting state がない")
    accounting["state"] = "pending-pre-invoke-failure"
    critic: dict[str, Any] | None = None
    try:
        generation = pending["generation"]
        generation_record = next(
            record
            for record in cell["generations"]
            if record["generation"] == generation
        )
        outcome = pending["outcome"]
        current_metrics = pending["metrics"]
        raw_variant = pending["raw_variant"]
        digest_path = Path(cell["campaign_root"]) / trigger.DIGEST_BASENAME
        digest = None
        candidate_label = raw_variant
        digest_generated = pending.get("critic_digest_generated")
        if type(digest_generated) is not bool:
            raise AutonomousTrialError(
                "critic_digest_generated は pending に exact bool で必須"
            )
        if digest_generated:
            if not digest_path.is_file() or digest_path.is_symlink():
                raise AutonomousTrialError(
                    "critic digest generated=true だが通常 file が存在しない"
                )
            critic_view = require_admitted_campaign(
                cell["campaign_root"],
                purpose=CampaignReadPurpose.CERTIFIED_ACCEPTANCE,
            )
            identity_projection = loop_core.make_critic_identity_projection(
                critic_view
            )
            candidate_label = identity_projection.project_variant(raw_variant)
            # _campaign_for fixes this supervisor to the reflux-on trigger cfg.
            # Recreate only that public setting after admission; do not retain
            # the campaign object in the private pending material.
            cfg = trigger.default_cfg(reflux=True)
            digest = loop_core.make_critic_digest(
                critic_view,
                tag=trigger.CRITIC_TAG,
                reflux=(cfg.search_config.get("reflux") == "on"),
                identity_projection=identity_projection,
            )
            if require_recomputed_digest:
                try:
                    persisted_digest = digest_path.read_text(encoding="utf-8")
                except (OSError, UnicodeError) as exc:
                    raise AutonomousTrialError("critic digest を読めない") from exc
                if persisted_digest != digest:
                    raise AutonomousTrialError(
                        "critic digest が admitted campaign の再計算値と一致しない"
                    )
        elif raw_variant:
            # A stale same-named file is intentionally not read on this branch.
            candidate_label = loop_core.UNREGISTERED_CANDIDATE_LABEL
        critic_payload = {
            **pending["common"],
            "harness_result": {
                "outcome": outcome.get("outcome"),
                "candidate_label": candidate_label,
                "verdict": outcome.get("verdict"),
                "metrics": dict(current_metrics),
                "stop_reason": outcome.get("stop_reason"),
            },
            "critic_digest": digest,
        }
        critic, event = _invoke(
            role="critic",
            provider=providers["critic"],
            invocation_id=(
                f"{cell['workload']}.g{generation}.critic"
            ),
            payload=critic_payload,
            raw_root=run_root / "raw",
            journal=journal,
            workload=cell["workload"],
            generation=generation,
            transport_receipt=transport_receipt,
        )
        generation_record["roles"]["critic"] = event
        if critic is None:
            accounting["state"] = "partial-generation"
            if not preserve_stop_reason:
                cell["stop_reason"] = "role-invalid"
        else:
            accounting["state"] = "generation-complete"
        return critic
    finally:
        if pending in pending_critics:
            pending_critics.remove(pending)
        if not pending_critics:
            cell.pop("_pending_critics", None)
        _append_generation_accounting(
            accounting,
            journal=journal,
            generation_record=generation_record,
        )


def _run_pending_critics(
    cell: dict[str, Any],
    *,
    providers: Mapping[str, Any],
    journal: AttemptJournal,
    run_root: Path,
    transport_receipt: Mapping[str, Any] | None,
    preserve_stop_reason: bool = False,
) -> None:
    pending_critics = cell.get("_pending_critics", [])
    while pending_critics:
        critic = _run_one_pending_critic(
            cell,
            providers=providers,
            journal=journal,
            run_root=run_root,
            transport_receipt=transport_receipt,
            preserve_stop_reason=preserve_stop_reason,
        )
        if critic is None:
            break
    if not pending_critics:
        cell.pop("_pending_critics", None)


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
    launch_admission: trial_registry.TrialLaunchAdmission,
    gating_spec_snapshot: GatingSpecSnapshot,
    generation_driver: Mapping[str, str] | None = None,
    accounting_authority: str | None = None,
    effective_preregistration: (
        s8c_preregistration.EffectivePreregistration | None
    ) = None,
    trial_manifest: Path | None = None,
    allow_unregistered_exploratory: bool = True,
    origin_runtime: OriginTrialRuntime | None = None,
) -> dict[str, Any]:
    if type(gating_spec_snapshot) is not GatingSpecSnapshot:
        raise AutonomousTrialError("run 単位 GATING_SPEC snapshot が必要")
    if generation_driver is None:
        generation_driver = _generation_driver_identity(drive)
    if accounting_authority is None:
        accounting_authority = _accounting_authority(drive)
    if origin_runtime is not None and type(origin_runtime) is not OriginTrialRuntime:
        raise TypeError("origin runtime has the wrong exact type")
    origin_capability = (
        None if origin_runtime is None else origin_runtime.capability
    )
    rederivation_arguments = dict(
        effective_preregistration=effective_preregistration,
        manifest_path=trial_manifest,
        trial_id=trial_id,
        workloads=selected,
        allow_unregistered_exploratory=allow_unregistered_exploratory,
        repository_root=ROOT,
        registry_path=ROOT / trial_registry.DEFAULT_REGISTRY_PATH,
    )
    if origin_capability is not None:
        rederivation_arguments["origin_binding"] = origin_capability
    trial_registry.assert_rederived_launch_admission(
        launch_admission, **rederivation_arguments
    )
    active_scope = _ACTIVE_TRIAL_BINDING.get()
    if (
        type(active_scope) is not _RunScopeBinding
        or active_scope._seal is not _RUN_SCOPE_SEAL
        or active_scope.admission is not launch_admission
        or active_scope.origin_capability is not origin_capability
    ):
        raise trial_registry.TrialRegistryError(
            "[run-scope] finish requires the exact sealed run_trial admission"
        )
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
                workload_arguments = dict(
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
                    gating_spec_snapshot=gating_spec_snapshot,
                )
                if origin_runtime is not None:
                    workload_arguments["origin_runtime"] = origin_runtime
                cell = _run_workload(**workload_arguments)
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
                admission_succeeded = _finalize_cell_admission(
                    cell,
                    do_build=do_build,
                    launch_admission=launch_admission,
                    journal=journal,
                )
                if admission_succeeded:
                    try:
                        _run_pending_critics(
                            cell,
                            providers=active_providers,
                            journal=journal,
                            run_root=run_root,
                            transport_receipt=transport_receipt,
                            preserve_stop_reason=True,
                        )
                    except Exception as exc:
                        fatal_error = {
                            "type": type(exc).__name__,
                            "message": _redacted_transport_error(
                                exc, transport_receipt,
                            ),
                        }
                        journal.append(_event_with_transport_receipt(
                            {
                                "event": "supervisor-error",
                                "workload": workload,
                                **fatal_error,
                            },
                            transport_receipt,
                        ))
                        cell["stop_reason"] = "supervisor-error"
                        cell["error"] = dict(fatal_error)
                break
            cells.append(cell)
            admission_succeeded = _finalize_cell_admission(
                cell,
                do_build=do_build,
                launch_admission=launch_admission,
                journal=journal,
            )
            if admission_succeeded:
                try:
                    _run_pending_critics(
                        cell,
                        providers=active_providers,
                        journal=journal,
                        run_root=run_root,
                        transport_receipt=transport_receipt,
                    )
                except Exception as exc:
                    fatal_error = {
                        "type": type(exc).__name__,
                        "message": _redacted_transport_error(
                            exc, transport_receipt,
                        ),
                    }
                    journal.append(_event_with_transport_receipt(
                        {
                            "event": "supervisor-error",
                            "workload": workload,
                            **fatal_error,
                        },
                        transport_receipt,
                    ))
                    cell["stop_reason"] = "supervisor-error"
                    cell["error"] = dict(fatal_error)
                    break
            deferred_wall_generation = cell.pop(
                "_deferred_wall_generation", None
            )
            wall_terminal_emitted = cell.pop(
                "_zero_work_wall_terminal_emitted", False
            )
            if deferred_wall_generation is not None:
                fatal_error = {
                    "type": "SupervisorWallBudget",
                    "message": "wall budget expired before the next workload",
                }
                if not wall_terminal_emitted:
                    journal.append(_event_with_transport_receipt(
                        {
                            "event": "supervisor-wall-budget",
                            "workload": workload,
                            "generation": deferred_wall_generation,
                            "zero_work": True,
                            "role_query_count": 0,
                            "bench_wall_seconds": 0.0,
                        },
                        transport_receipt,
                    ))
                break
            if not admission_succeeded:
                break
    status = (
        "complete"
        if len(cells) == len(selected)
        and fatal_error is None
        and all(
            cell["stop_reason"]
            not in {"role-invalid", "supervisor-error", "supervisor-wall-budget"}
            for cell in cells
        )
        and (
            not do_build
            or all(
                is_positive_cell_admission_decision(
                    cell.get("admission_decision")
                )
                for cell in cells
            )
        )
        else "partial"
    )
    if any("_pending_critics" in cell for cell in cells):
        raise AutonomousTrialError("pending critic remained before report construction")
    if any("admission_decision" not in cell for cell in cells):
        raise AutonomousTrialError(
            "cell admission decision missing before report construction"
        )
    if origin_runtime is not None:
        _complete_origin_runtime(origin_runtime)
    honest_accounting = {
        "role_query_count": journal.role_query_count,
        "bench_wall_seconds": sum(
            generation["bench_wall_seconds"]
            for cell in cells
            for generation in cell.get("generations", [])
        ),
    }
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
        "launch_admission": _launch_admission_record(
            launch_admission, origin_capability
        ),
        "generation_driver": dict(generation_driver),
        "gating_spec_sha256": gating_spec_snapshot.sha256,
        "honest_accounting": honest_accounting,
        "honest_accounting_authority": accounting_authority,
        "cells": cells,
    }
    if fatal_error is not None:
        report["fatal_error"] = fatal_error
    if origin_runtime is not None:
        projection = origin_runtime.terminal_projection
        if projection is None:  # pragma: no cover - formal adapter postcondition
            raise AutonomousTrialError("origin terminal projection is absent")
        report.update(
            reflux_formal_consumer.origin_terminal_projection_record(projection)
        )
    if transport_receipt is not None:
        report["transport_receipt"] = _validate_transport_receipt(
            dict(transport_receipt), expected=transport_receipt
        )
    trial_binding = launch_admission.binding
    if trial_binding is not None:
        report.update({
            "prereg_commit": trial_binding.prereg_commit,
            "measurement_head": trial_binding.measurement_head,
            "manifest_sha256": trial_binding.manifest_sha256,
        })
    run_finish = {
        "event": "run-finish",
        "status": status,
        "report": str(run_root / "report.json"),
        "generation_driver": dict(generation_driver),
        "gating_spec_sha256": gating_spec_snapshot.sha256,
        "honest_accounting": honest_accounting,
        "honest_accounting_authority": accounting_authority,
    }
    admission_failures = cell_admission_failure_projection(cells)
    if admission_failures:
        run_finish["cell_admission_failures"] = admission_failures
    journal.append(_event_with_transport_receipt(
        run_finish,
        transport_receipt,
    ))
    report["attempt_journal_sha256"] = _sha256((run_root / "attempts.jsonl").read_bytes())
    assert_autonomous_trial_completeness(
        report=report,
        attempt_journal=run_root / "attempts.jsonl",
    )
    if do_build and cells:
        campaign_parents = {
            Path(campaign_root).resolve().parent.parent
            for cell in cells
            if isinstance((campaign_root := cell.get("campaign_root")), str)
            and campaign_root
        }
        if len(campaign_parents) > 1:
            raise AutonomousTrialError("build cells do not share one campaign output root")
        assert_campaign_layer3_chain(
            report=report,
            output_root=(
                next(iter(campaign_parents))
                if campaign_parents
                else run_root.resolve().parent
            ),
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
    origin_runtime: OriginTrialRuntime | None = None,
    gating_spec_snapshot: GatingSpecSnapshot,
) -> dict[str, Any]:
    if origin_runtime is not None and type(origin_runtime) is not OriginTrialRuntime:
        raise TypeError("origin runtime has the wrong exact type")
    active_scope = _ACTIVE_TRIAL_BINDING.get()
    if active_scope is None:
        raise trial_registry.TrialRegistryError(
            "[run-scope] workload requires a sealed launch admission from run_trial"
        )
    if (
        type(active_scope) is not _RunScopeBinding
        or active_scope._seal is not _RUN_SCOPE_SEAL
    ):
        raise trial_registry.TrialRegistryError(
            "[run-scope] active workload scope was not issued by run_trial"
        )
    active_admission = active_scope.admission
    trial_registry.assert_issued_trial_launch_admission(active_admission)
    expected_origin_capability = (
        None if origin_runtime is None else origin_runtime.capability
    )
    if active_scope.origin_capability is not expected_origin_capability:
        raise trial_registry.TrialRegistryError(
            "[run-scope] workload origin capability identity changed"
        )
    if (
        active_admission.trial_id != trial_id
        or workload not in active_admission.workloads
    ):
        raise trial_registry.TrialRegistryError(
            "[launch-admission] active admission differs from workload inputs"
        )
    active_binding = active_admission.binding
    if active_binding is not None:
        trial_registry.assert_issued_trial_binding(active_binding)
        if (
            active_binding.trial_id != trial_id
            or active_binding.workload != workload
        ):
            raise trial_registry.TrialRegistryError(
                "[launch-binding] active binding differs from workload inputs"
            )
    _validate_generation_budget(generations)
    if type(gating_spec_snapshot) is not GatingSpecSnapshot:
        raise AutonomousTrialError("run 単位 GATING_SPEC snapshot が必要")
    resolved_site = trigger._current_site()
    _assert_build_transport_admitted_for_site(
        resolved_site,
        do_build,
        transport_admission=transport_admission,
        transport_receipt=transport_receipt,
    )
    contract = trigger._admit_env_contract(resolved_site)
    if type(build_context) is not BuildRunContext:
        raise AutonomousTrialError(
            "workload requires the trial's shared BuildRunContext"
        )
    flags = WORKLOADS[workload]
    prepared = _prepare_campaign_identity(
        workload=workload,
        trial_id=trial_id,
        generations=generations,
        site=resolved_site,
        contract=contract,
        build_context=build_context,
    )
    descriptor = prepared.descriptor
    descriptor_record = prepared.descriptor_record
    cfg = prepared.campaign
    campaign_id = prepared.campaign_id
    if do_build:
        layout = exploration_campaign_layout(campaign_id)
    else:
        layout = CampaignLayout(
            str(run_root / "campaigns" / campaign_id)
        )
    _assert_fresh_campaign_state(layout)
    if origin_runtime is not None:
        reflux_origin_topology.write_recovery_envelope_create_only(
            evidence_root=run_root,
            envelope=origin_runtime.producer_inputs.run_plan,
            relative_path=Path("origin/recovery-envelope.json"),
        )
    result: dict[str, Any] = {
        "workload": workload,
        "workload_flags": dict(flags),
        "descriptor": descriptor,
        "descriptor_binding": descriptor_record,
        "campaign_id": campaign_id,
        "campaign_root": layout.root,
        "generations": [],
        "stop_reason": "fixed-generation-budget",
        "_pending_critics": [],
    }
    if _partial is not None:
        _partial["cell"] = result
    perf = _perf_for(flags)
    prior_reverse: bool | None = None
    critic_feedback: Mapping[str, Any] | None = None
    current_metrics = dict(_INITIAL_ROLE_METRICS)
    # Freeze the role-facing metrics once per workload from the initial state.
    # Later generation outcomes remain critic-only source material.
    frozen_perf, frozen_leading = copy.deepcopy(
        _role_metric_payloads(
            dict(current_metrics),
            contention_level=descriptor["contention"]["label"],
        )
    )
    generation_driver = _generation_driver_identity(drive)
    authority = _accounting_authority(drive)
    active_accounting: dict[str, Any] | None = None
    active_generation_record: dict[str, Any] | None = None
    try:
        for generation in range(1, generations + 1):
            if time.monotonic() - started_monotonic >= max_wall_s:
                result["stop_reason"] = "supervisor-wall-budget"
                if not result["_pending_critics"]:
                    journal.append(_event_with_transport_receipt(
                        {
                            "event": "supervisor-wall-budget",
                            "workload": workload,
                            "generation": generation,
                            "zero_work": True,
                            "role_query_count": 0,
                            "bench_wall_seconds": 0.0,
                        },
                        transport_receipt,
                    ))
                    result["_zero_work_wall_terminal_emitted"] = True
                result["_deferred_wall_generation"] = generation
                break

            if generation >= 2:
                pending = result["_pending_critics"][0]
                source_metrics = dict(pending["metrics"])
                source_generation = pending["generation"]
                critic = _run_one_pending_critic(
                    result,
                    providers=providers,
                    journal=journal,
                    run_root=run_root,
                    transport_receipt=transport_receipt,
                    require_recomputed_digest=True,
                )
                if critic is None:
                    break
                applied = apply_critic_feedback(
                    critic,
                    source_metrics=source_metrics,
                    source_generation=source_generation,
                )
                critic_feedback = applied.planner_projection
                prior_reverse = applied.prior_reverse

            active_accounting = _new_generation_accounting(
                workload=workload,
                generation=generation,
                journal=journal,
                generation_driver=generation_driver,
                gating_spec_sha256=gating_spec_snapshot.sha256,
                authority=authority,
            )
            generation_record: dict[str, Any] = {
                "generation": generation,
                "roles": {},
            }
            active_generation_record = generation_record
            if _partial is not None:
                _partial["generation"] = generation_record
            common = _common_payload(
                workload=workload,
                generation=generation,
                descriptor=descriptor,
                descriptor_record=descriptor_record,
            )
            whiteboard = _whiteboard(layout)
            planner_payload = {
                **common,
                "current_perf": _planner_current_perf_payload(
                    copy.deepcopy(frozen_perf),
                    current_metrics=current_metrics,
                    contention_level=descriptor["contention"]["label"],
                ),
                "leading_indicators": _planner_leading_indicators_payload(
                    copy.deepcopy(frozen_leading),
                    current_metrics=current_metrics,
                    contention_level=descriptor["contention"]["label"],
                ),
                "whiteboard": whiteboard,
            }
            if generation >= 2:
                planner_payload["critic_feedback"] = dict(critic_feedback or {})
            planner_validation_receipt = validate_planner_payload(
                planner_payload,
                expected_workload=workload,
                expected_generation=generation,
                expected_workload_descriptor=descriptor,
                expected_descriptor_binding=descriptor_record,
                expected_whiteboard_origin=_whiteboard(layout),
                expected_current_perf=copy.deepcopy(frozen_perf),
                expected_leading_indicators=copy.deepcopy(frozen_leading),
                expected_critic_feedback=critic_feedback,
                payload_allowlist_sha256=ROLE_PAYLOAD_ALLOWLIST_SHA256,
            )
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
                validation_receipt=planner_validation_receipt,
            )
            active_accounting["state"] = "partial-generation"
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
                "leakproof_context": LEAKPROOF_CONTEXT,
                "gating_spec": gating_spec_snapshot.text,
                # Planner mechanism text is intentionally not forwarded.  Only the
                # abstract control signal crosses the planner-to-coder boundary.
                "planner_direction": {
                    "axis": planner.axis,
                    "direction": planner.direction,
                    "magnitude": planner.magnitude,
                },
                "baseline": _coder_baseline_payload(
                    copy.deepcopy(frozen_perf),
                    current_metrics=current_metrics,
                    contention_level=descriptor["contention"]["label"],
                ),
                "whiteboard": whiteboard,
            }
            coder_validation_receipt = validate_coder_payload(
                coder_payload,
                expected_workload=workload,
                expected_generation=generation,
                expected_workload_descriptor=descriptor,
                expected_descriptor_binding=descriptor_record,
                expected_whiteboard_origin=_whiteboard(layout),
                expected_baseline=copy.deepcopy(frozen_perf),
                gating_spec_snapshot=gating_spec_snapshot,
                payload_allowlist_sha256=ROLE_PAYLOAD_ALLOWLIST_SHA256,
            )
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
                validation_receipt=coder_validation_receipt,
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
                key: value
                for key, value in preview_result.items()
                if key != "working_diff"
            }
            pre_audit_reject = (
                not preview_result["passed"]
                or bool(preview_result["forbidden_identifiers"])
            )
            if pre_audit_reject:
                active_accounting["auditor_pre_audit_skipped"] = True
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

            proposal_path = (
                run_root / "proposals" / f"{workload}.g{generation}.json"
            )
            proposal_value = {
                "planner": dataclasses.asdict(planner),
                "coder": dataclasses.asdict(coder),
                "auditor": dataclasses.asdict(auditor),
                "prior_critic_reverse": prior_reverse,
                "descriptor_sha256": descriptor_record["output_sha256"],
            }
            _write_bytes_bound(
                proposal_path, _canonical_json_bytes(proposal_value)
            )
            outcome, observed_driver = _drive_s8c_generation(
                drive=drive,
                cfg=cfg,
                perf=perf,
                planner=planner,
                coder=coder,
                auditor=auditor,
                prior_reverse=prior_reverse,
                sub=sub,
                do_build=do_build,
                layout=layout,
                cache_root=cache_root,
                proposal_path=proposal_path,
                resolved_site=resolved_site,
                contract=contract,
                build_context=build_context,
            )
            if observed_driver != generation_driver:
                raise AutonomousTrialError("generation driver identity が変化した")
            active_accounting["bench_wall_seconds"] = _bench_wall_seconds(
                outcome,
                authoritative=(authority == _AUTHORITATIVE_ACCOUNTING),
            )
            generation_record["harness"] = outcome
            generation_record["outcome"] = outcome["outcome"]
            current_metrics = _metric_projection(outcome)
            result["generations"].append(generation_record)
            if _partial is not None:
                _partial["generation"] = None
            raw_variant = outcome.get("variant")
            if raw_variant is not None and type(raw_variant) is not str:
                raise TypeError("harness output の variant は str/None が必要")
            result.setdefault("_pending_critics", []).append({
                "generation": generation,
                "common": dict(common),
                "outcome": dict(outcome),
                "metrics": dict(current_metrics),
                "raw_variant": raw_variant,
                "critic_digest_generated": outcome[
                    "critic_digest_generated"
                ],
                "critic_attempted": False,
                "accounting": active_accounting,
            })
            active_accounting = None
            active_generation_record = None
            if outcome.get("stop_reason") != "continue":
                result["stop_reason"] = str(outcome.get("stop_reason"))
                break
    finally:
        if active_accounting is not None:
            _append_generation_accounting(
                active_accounting,
                journal=journal,
                generation_record=active_generation_record,
            )
    return result


def _record_indeterminate_terminal(
    token: trial_registry.TrialLifecycleToken,
    *,
    cause: BaseException,
    origin_terminal_projection: (
        reflux_formal_consumer.OriginTerminalProjection | None
    ) = None,
) -> None:
    """Terminalize a consumed formal trial or expose irrecoverable ledger I/O.

    If the terminal append itself fails, the original start remains consumed
    and rerun stays forbidden.  The raised error names both the original
    failure and the failed terminalization instead of implying recovery.
    """
    try:
        terminal_arguments: dict[str, Any] = {
            "terminal_status": "indeterminate",
        }
        if origin_terminal_projection is not None:
            terminal_arguments["origin_terminal_projection"] = (
                origin_terminal_projection
            )
        trial_registry.record_trial_terminal(token, **terminal_arguments)
    except BaseException as terminal_error:
        raise AutonomousTrialError(
            "formal trial failed after lifecycle start and indeterminate "
            "terminalization also failed; the start remains consumed: "
            f"original={type(cause).__name__}; "
            f"terminal={type(terminal_error).__name__}"
        ) from terminal_error


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
    drive: Callable[..., Mapping[str, Any]] = _DRIVE_NOT_PROVIDED,
    preview: Callable[..., Mapping[str, Any]] = _PREVIEW_NOT_PROVIDED,
    coder_authority: CoderBuildAuthority | None = None,
    trial_manifest: Path | None = None,
    allow_unregistered_exploratory: bool = False,
    effective_preregistration: (
        s8c_preregistration.EffectivePreregistration | None
    ) = None,
    trial_admission: trial_registry.TrialLaunchAdmission | None = None,
    origin_binding_request: OriginBindingRequest | None = None,
    origin_producer_inputs: OriginProducerInputs | None = None,
) -> dict[str, Any]:
    if _TRIAL_ID_RE.fullmatch(trial_id) is None:
        raise AutonomousTrialError(f"trial_id が安全な形式でない: {trial_id!r}")
    if type(provider_kind) is not str:
        raise AutonomousTrialError(
            f"provider kind は plain str 必須: {type(provider_kind).__name__}"
        )
    if provider_kind not in PROVIDER_KINDS:
        raise AutonomousTrialError(f"unknown provider kind: {provider_kind}")
    if provider_kind == "claude-headless" and providers is not None:
        raise AutonomousTrialError(
            "claude-headless provider は caller 注入を許可しない"
        )
    if (
        provider_kind == "claude-headless"
        and (
            drive is not _DRIVE_NOT_PROVIDED
            or preview is not _PREVIEW_NOT_PROVIDED
        )
    ):
        raise AutonomousTrialError(
            "claude-headless drive/preview は caller 注入を許可しない"
        )
    if drive is _DRIVE_NOT_PROVIDED:
        drive = trigger.drive_iteration
    if preview is _PREVIEW_NOT_PROVIDED:
        preview = _preview
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
    if type(allow_unregistered_exploratory) is not bool:
        raise AutonomousTrialError(
            "allow_unregistered_exploratory は bool 必須"
        )
    if (origin_binding_request is None) != (origin_producer_inputs is None):
        raise AutonomousTrialError(
            "origin_binding_request and origin_producer_inputs must be supplied together"
        )
    if (
        origin_binding_request is not None
        and type(origin_binding_request) is not OriginBindingRequest
    ):
        raise TypeError("origin_binding_request must be an OriginBindingRequest")
    if (
        origin_producer_inputs is not None
        and type(origin_producer_inputs) is not OriginProducerInputs
    ):
        raise TypeError("origin_producer_inputs must be an OriginProducerInputs")
    if (
        origin_binding_request is not None
        and origin_binding_request.client is None
    ):
        raise reflux_origin_client.OriginLedgerClientError(
            "origin-bound run requires an explicit typed ledger client"
        )
    selected = list(workloads)
    if trial_admission is None:
        trial_admission = _trial_launch_admission(
            trial_manifest=trial_manifest,
            trial_id=trial_id,
            workloads=selected,
            generations=generations,
            allow_unregistered_exploratory=allow_unregistered_exploratory,
            effective_preregistration=effective_preregistration,
        )
    else:
        trial_registry.assert_issued_trial_launch_admission(trial_admission)
        supplied_binding = trial_admission.binding
        if supplied_binding is not None:
            observed_head = trial_registry.resolve_measurement_commit(ROOT)
            if observed_head != supplied_binding.measurement_head:
                raise trial_registry.TrialRegistryError(
                    "[measurement-head-moved] HEAD changed after CLI preflight"
                )
            if trial_manifest is None:
                raise trial_registry.TrialRegistryError(
                    "[launch-admission] registered admission requires its manifest"
                )
            trial_registry.assert_rederived_launch_binding(
                supplied_binding,
                manifest_path=Path(trial_manifest),
                trial_id=trial_id,
                workloads=selected,
                repository_root=ROOT,
                registry_path=ROOT / trial_registry.DEFAULT_REGISTRY_PATH,
            )
        derived_admission = _trial_launch_admission(
            trial_manifest=trial_manifest,
            trial_id=trial_id,
            workloads=selected,
            generations=generations,
            allow_unregistered_exploratory=allow_unregistered_exploratory,
            effective_preregistration=effective_preregistration,
        )
        if (
            trial_registry.launch_admission_record(trial_admission)
            != trial_registry.launch_admission_record(derived_admission)
        ):
            raise trial_registry.TrialRegistryError(
                "[launch-admission] supplied admission differs from fresh derivation"
            )
    unknown = sorted(set(selected) - set(WORKLOADS))
    if unknown:
        raise AutonomousTrialError(f"unknown workloads: {unknown}")
    # Capture once per run, before any workload or artifact-producing role work.
    gating_spec_snapshot = snapshot_gating_spec(GATING_SPEC)
    generation_driver = _generation_driver_identity(drive)
    accounting_authority = _accounting_authority(drive)
    _assert_build_site_opted_in(
        do_build,
        allow_pegasus_compute_transport=allow_pegasus_compute_transport,
    )
    if do_build and coder_authority is None:
        raise AutonomousTrialError(
            "build trial requires parser-issued --allow-coder-derived-build authority"
        )
    run_root = Path(run_root)
    _reject_worktree_container(run_root)
    if run_root.exists() or run_root.is_symlink():
        raise AutonomousTrialError(
            f"run_root は新規 directory 必須 (resume は MVP 範囲外): {run_root}"
        )
    origin_runtime: OriginTrialRuntime | None = None
    preflight_build_context: BuildRunContext | None = None
    if origin_binding_request is not None:
        preflight_build_context = build_run_context(
            generator_id=GeneratorId.S8A_TRIGGER_SWEEP,
            coder_authority=coder_authority if do_build else None,
        )
        origin_runtime = _prepare_origin_trial_runtime(
            admission=trial_admission,
            request=origin_binding_request,
            producer_inputs=origin_producer_inputs,
            trial_id=trial_id,
            selected=selected,
            generations=generations,
            trial_manifest=trial_manifest,
            effective_preregistration=effective_preregistration,
            build_context=preflight_build_context,
        )
    lifecycle_token: trial_registry.TrialLifecycleToken | None = None
    if trial_admission.mode == "registered-effective":
        lifecycle_arguments = dict(
            admission=trial_admission,
            effective_preregistration=effective_preregistration,
            manifest_path=Path(trial_manifest),
            run_root=run_root,
            repository_root=ROOT,
            registry_path=ROOT / trial_registry.DEFAULT_REGISTRY_PATH,
            lifecycle_path=ROOT / trial_registry.DEFAULT_LIFECYCLE_PATH,
        )
        if origin_runtime is not None:
            lifecycle_arguments["origin_binding"] = origin_runtime.capability
        lifecycle_token = trial_registry.record_trial_start_once(
            **lifecycle_arguments
        )
    try:
        run_root.mkdir(parents=True)
        ensure_exploration_namespace(str(run_root))
        run_children = ["raw", "proposals"]
        if origin_runtime is not None:
            run_children.append("origin")
        for child in run_children:
            (run_root / child).mkdir()
        journal = AttemptJournal(run_root / "attempts.jsonl")
        started = _now_iso()
        started_monotonic = time.monotonic()
        build_context = preflight_build_context or build_run_context(
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
        run_start = {
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
            "launch_admission": _launch_admission_record(
                trial_admission,
                None if origin_runtime is None else origin_runtime.capability,
            ),
            "generation_driver": dict(generation_driver),
            "gating_spec_sha256": gating_spec_snapshot.sha256,
            "honest_accounting_authority": accounting_authority,
        }
        trial_binding = trial_admission.binding
        if trial_binding is not None:
            run_start.update({
                "prereg_commit": trial_binding.prereg_commit,
                "measurement_head": trial_binding.measurement_head,
                "manifest_sha256": trial_binding.manifest_sha256,
            })
        journal.append(run_start)
    except BaseException as exc:
        if lifecycle_token is not None:
            _record_indeterminate_terminal(
                lifecycle_token,
                cause=exc,
                origin_terminal_projection=(
                    None
                    if origin_runtime is None
                    else origin_runtime.terminal_projection
                ),
            )
        raise
    owns_active_providers = providers is None
    active_providers: dict[str, Any] = {}
    lifecycle_terminalized = False
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
        run_scope = _RunScopeBinding(
            trial_admission,
            _RUN_SCOPE_SEAL,
            None if origin_runtime is None else origin_runtime.capability,
        )
        scope_token = _ACTIVE_TRIAL_BINDING.set(run_scope)
        try:
            finish_arguments = dict(
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
                launch_admission=trial_admission,
                gating_spec_snapshot=gating_spec_snapshot,
                generation_driver=generation_driver,
                accounting_authority=accounting_authority,
                effective_preregistration=effective_preregistration,
                trial_manifest=trial_manifest,
                allow_unregistered_exploratory=(
                    allow_unregistered_exploratory
                ),
            )
            if origin_runtime is not None:
                finish_arguments["origin_runtime"] = origin_runtime
            report = _finish_trial(**finish_arguments)
            if lifecycle_token is not None:
                terminal_arguments: dict[str, Any] = {
                    "terminal_status": report["status"],
                }
                if origin_runtime is not None:
                    terminal_arguments["origin_terminal_projection"] = (
                        origin_runtime.terminal_projection
                    )
                trial_registry.record_trial_terminal(
                    lifecycle_token, **terminal_arguments
                )
                lifecycle_terminalized = True
            return report
        finally:
            _ACTIVE_TRIAL_BINDING.reset(scope_token)
    except BaseException as exc:
        if lifecycle_token is not None and not lifecycle_terminalized:
            _record_indeterminate_terminal(
                lifecycle_token,
                cause=exc,
                origin_terminal_projection=(
                    None
                    if origin_runtime is None
                    else origin_runtime.terminal_projection
                ),
            )
        raise
    finally:
        if owns_active_providers:
            _close_owned_providers(active_providers)


def _origin_lifecycle_started(*, trial_id: str, run_root: Path) -> bool:
    lifecycle = ROOT / trial_registry.DEFAULT_LIFECYCLE_PATH
    try:
        rows = [
            json.loads(line)
            for line in lifecycle.read_bytes().splitlines()
            if line
        ]
    except (OSError, ValueError, TypeError):
        return False
    expected_root = os.path.abspath(os.fspath(run_root))
    return any(
        type(row) is dict
        and row.get("event") == "start"
        and row.get("trial_id") == trial_id
        and row.get("run_root") == expected_root
        for row in rows
    )


def run_origin_trial(
    *,
    origin_binding_request: OriginBindingRequest | None = None,
    origin_producer_inputs: OriginProducerInputs | None = None,
    **trial_arguments: Any,
) -> (
    OriginPreflightFailure
    | OriginPartialTrialReport
    | OriginCompletedTrialReport
):
    """Typed public boundary for origin-bound trials; it never raises failures."""

    trial_id = trial_arguments.get("trial_id")
    run_root = trial_arguments.get("run_root")
    if origin_binding_request is None or origin_producer_inputs is None:
        return OriginPreflightFailure(
            "OriginInputPairError",
            "origin_binding_request and origin_producer_inputs are both required",
        )
    try:
        report = run_trial(
            **trial_arguments,
            origin_binding_request=origin_binding_request,
            origin_producer_inputs=origin_producer_inputs,
        )
    except Exception as exc:
        error_type = type(exc).__name__
        message = _redacted_transport_error(exc, None)
        if type(trial_id) is not str or run_root is None or not _origin_lifecycle_started(
            trial_id=trial_id, run_root=Path(run_root)
        ):
            return OriginPreflightFailure(error_type, message)
        report_path = Path(run_root) / "report.json"
        partial_report: Mapping[str, Any] | None = None
        try:
            loaded = json.loads(report_path.read_bytes())
            if type(loaded) is dict:
                partial_report = loaded
        except (OSError, ValueError, TypeError):
            pass
        return OriginPartialTrialReport(partial_report, error_type, message)
    if report.get("status") == "complete":
        return OriginCompletedTrialReport(report)
    fatal = report.get("fatal_error")
    return OriginPartialTrialReport(
        report,
        fatal.get("type") if type(fatal) is dict else None,
        fatal.get("message") if type(fatal) is dict else None,
    )


def _parse_workloads(raw: str) -> list[str]:
    values = [item.strip().lower() for item in raw.split(",") if item.strip()]
    if not values:
        raise argparse.ArgumentTypeError("workloads is empty")
    unknown = sorted(
        set(values) - set(WORKLOADS) - set(trial_registry.HOLDOUT_WORKLOADS)
    )
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
    parser.add_argument("--trial-manifest", type=Path)
    parser.add_argument(
        "--provider", required=True, choices=tuple(sorted(PROVIDER_KINDS))
    )
    parser.add_argument("--workloads", type=_parse_workloads, default=list(WORKLOADS))
    parser.add_argument("--max-generations", type=int, default=1)
    parser.add_argument("--max-wall-seconds", type=int, default=DEFAULT_MAX_WALL_S)
    parser.add_argument("--no-build", action="store_true")
    parser.add_argument(
        "--allow-unregistered-exploratory",
        action="store_true",
        default=False,
    )
    add_registered_coder_build_authority_argument(
        parser,
        coder_entrypoint_site=(
            "orchestrator.campaign.p3_autonomous_workload_trial.main"
        ),
    )
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
    if args.run_root:
        run_root = Path(args.run_root)
    else:
        run_root = (
            Path(_resolve_exploration_output_root(
                legacy_base=str(ROOT / "output"),
            ))
            / "exploration" / "autonomous-trials" / args.trial_id
        )
    fixed_sub = str(Path(args.ccbench_dir).resolve())
    effective_preregistration = None
    if args.trial_manifest is not None:
        manifest = trial_registry.load_trial_manifest(args.trial_manifest)
        effective_preregistration = s8c_preregistration.effective_at(
            ROOT,
            manifest.prereg_commit,
        )
    launch_admission = _trial_launch_admission(
        trial_manifest=args.trial_manifest,
        trial_id=args.trial_id,
        workloads=args.workloads,
        generations=args.max_generations,
        allow_unregistered_exploratory=args.allow_unregistered_exploratory,
        effective_preregistration=effective_preregistration,
    )
    if args.no_build:
        assert_pinned_clean(fixed_sub, trigger.PIN)
        context = contextlib.nullcontext(fixed_sub)
        cache_root = ""
    else:
        from ..calibrator.runner import competing_bench_pids

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
            trial_manifest=args.trial_manifest,
            allow_unregistered_exploratory=(
                args.allow_unregistered_exploratory
            ),
            effective_preregistration=effective_preregistration,
            trial_admission=launch_admission,
        )
    print(json.dumps({
        "status": report["status"],
        "report": str(run_root / "report.json"),
        "cells": len(report["cells"]),
    }, ensure_ascii=False, sort_keys=True))
    return 0 if report["status"] == "complete" else 2


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
