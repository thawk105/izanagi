# -*- coding: utf-8 -*-
"""campaign ループ — 同一性確定 → リカバリ → 未評価 genome を評価 (orchestrator-design.md)。

1 campaign = (spec, 探索 config) 固定 (D13)。起動時に:
  1. campaign-id を入力から再計算 (状態を保存せず再現)
  2. campaign.lock を確定 (初回) or 照合 (再開、IdentityMismatch で関所)
  3. WAL をリプレイし terminal (commit/abort) な variant をスキップ (D, A リカバリ)
  4. 残りの genome を評価パイプラインに通す

Phase 1 は探索 = 列挙 (全 genome)。Phase 2 で LLM 誘導の選択/変異が loop の上に乗る。
"""
from __future__ import annotations

import datetime as dt
import hashlib
import json
import os
import secrets
from contextlib import ExitStack, contextmanager
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING, Callable, List, Mapping, Optional, Sequence

from ..calibrator import perf_preflight as _perf_preflight
from ..holdout_observation import HoldoutObservationAdmission
from . import (backoff_hole_grammar, buildcache, campaign_claim,
               env_attestation, execution_guard, ident, reservation,
               source_digest, wal)
from .build_admission import BuildRunContext
from .env_contract import AuthorizedContract, ExecutionEnvironmentContract
from .layout import (campaign_layout, env_scope_dir,
                     campaign_lock_path,
                     exploration_campaign_layout,
                     resolve_campaign_output_root,
                     validate_campaign_id, write_capability_for_directory)
from .lock import HeldCampaignLock, campaign_lock
from .model import (CampaignConfig, Genome, INCOMPLETE_ATTEMPT_RECOVERY_REASON,
                    STAGE_ABORT, STAGE_BUILD_START)
from .pipeline import (AdmissionCapabilityResolver, EvalResult, LEGACY_TAG,
                       PERFORMANCE_TAG, BalancedScheduleConfig, PerfConfig, S2_TAG,
                       SEARCH_CONFIG_VERIFY_KEY,
                       VERIFY_LEGACY_PLUS_PERFORMANCE, VERIFY_LEGACY_PLUS_S2,
                       _PreparedEvaluation, _abort_balanced_workload,
                       _prepare_evaluation, _run_balanced_schedule, evaluate,
                       performance_correctness_workload,
                       s2_correctness_workload, variant_id,
                       _validate_fetchcontent_prebuild_inputs)
from .trigger_gate_binding import (
    SCHEMA_VERSION as TRIGGER_BINDING_SCHEMA,
    SourceBinding,
    TriggerGateBinding,
)

_DEFAULT_CXX = buildcache.DEFAULT_CXX
_compilers_for_current_site = buildcache.compilers_for_current_site

if TYPE_CHECKING:
    from . import reflux_result_evidence


@dataclass
class CampaignSummary:
    campaign_id: str
    layout_root: str
    total: int = 0
    skipped: int = 0           # リカバリでスキップ (既に terminal)
    identity_skipped: int = 0  # identity 確定不能かつ stock id が terminal 済みで今 run 未評価
    # リカバリ skip した variant の確定済み id。skip の id はここが単一の確定点 —
    # 呼び手が revert 後の tree へ source_digest.resolve を再実行すると stock id
    # (別 variant) を引く ([T-157]、D23/D24)。identity_skipped の分は id 未確定なので積まない。
    skipped_variants: List[str] = field(default_factory=list)
    evaluated: int = 0
    committed: int = 0
    aborted: int = 0
    results: List[EvalResult] = field(default_factory=list)
    execution_receipt: Optional[dict] = None
    perf_preflight_receipt: Optional[dict] = None
    balanced_schedule_receipt: Optional[dict] = None


@dataclass(frozen=True)
class _AuthorizationResult:
    authorized_contract: ExecutionEnvironmentContract
    execution_receipt: Optional[dict]
    bound_cfg: CampaignConfig
    campaign_identity: str
    acquired_claim: Optional[campaign_claim.AcquiredClaim] = None
    reservation_binding: Optional[reservation.ReservationBinding] = None


@dataclass(frozen=True)
class _SessionBinding:
    contract_sha256: str
    campaign_identity: str
    protocol_digest: str
    declared_use_class: str
    output_root: Path
    receipt_json: str
    acquired_claim: Optional[campaign_claim.AcquiredClaim]
    reservation_binding: Optional[reservation.ReservationBinding]


class _AuthorizationSession:
    """Opaque handle; authority and immutable bindings live only in the issuer."""

    __slots__ = ()

    def close(self) -> None:
        _AUTHORIZATION_SESSIONS.pop(self, None)

    def __copy__(self):
        raise TypeError("authorization session cannot be copied")

    def __deepcopy__(self, memo):
        raise TypeError("authorization session cannot be copied")

    def __reduce_ex__(self, protocol):
        raise TypeError("authorization session cannot be pickled")


# Strong object keys prove issuance by identity and prevent id reuse while open.
# Closing removes authority permanently; constructing the same type grants none.
_AUTHORIZATION_SESSIONS: dict[
    _AuthorizationSession, tuple[int, Optional[_SessionBinding]]
] = {}


@contextmanager
def authorization_session():
    """Own one process-local authorization lifetime, including exceptional exits."""
    session = _AuthorizationSession()
    _AUTHORIZATION_SESSIONS[session] = (os.getpid(), None)
    try:
        yield session
    finally:
        session.close()


def _authorize_with_session(
        session: _AuthorizationSession, cfg: CampaignConfig,
        authorization_contract: AuthorizedContract, *,
        env_tag: str, clocks_per_us: int,
        numactl: Optional[Sequence[str]],
        env_contract: Optional[ExecutionEnvironmentContract],
        declared_use_class: str,
        output_root: str,
        durable_root_policy,
        pre_write_validator: Optional[Callable[[str], None]],
) -> _AuthorizationResult:
    if type(session) is not _AuthorizationSession:
        raise execution_guard.ExecutionGuardError("authorization session is unissued or closed")
    entry = _AUTHORIZATION_SESSIONS.get(session)
    if entry is None:
        raise execution_guard.ExecutionGuardError("authorization session is unissued or closed")
    issued_pid, saved = entry
    if issued_pid != os.getpid():
        raise execution_guard.ExecutionGuardError("authorization session PID mismatch")
    if saved is None:
        base_root = Path(resolve_campaign_output_root(
            declared_use_class, output_root,
        )).resolve()
        result = _authorize_measurement(
            cfg, authorization_contract,
            env_tag=env_tag, clocks_per_us=clocks_per_us, numactl=numactl,
            env_contract=env_contract, declared_use_class=declared_use_class,
            output_root=output_root, durable_root_policy=durable_root_policy,
            pre_write_validator=pre_write_validator,
        )
        claim = result.acquired_claim
        binding = _SessionBinding(
            contract_sha256=result.authorized_contract.contract_sha256,
            campaign_identity=result.campaign_identity,
            protocol_digest=hashlib.sha256(
                ident.canonical_preimage(result.bound_cfg).encode("utf-8")
            ).hexdigest(),
            declared_use_class=declared_use_class,
            output_root=base_root,
            receipt_json=json.dumps(result.execution_receipt, allow_nan=False),
            acquired_claim=(None if claim is None else campaign_claim.AcquiredClaim(
                path=claim.path.resolve(), record=claim.record,
            )),
            reservation_binding=result.reservation_binding,
        )
        # Bind at the sink, before perf preflight, layout, lock or evaluation.
        if _AUTHORIZATION_SESSIONS.get(session) != (issued_pid, None):
            raise execution_guard.ExecutionGuardError("authorization session closed during authorization")
        _AUTHORIZATION_SESSIONS[session] = (issued_pid, binding)
        return result

    try:
        base_root = Path(resolve_campaign_output_root(
            declared_use_class, output_root,
        )).resolve()
        contract = execution_guard.require_certified_writer_authorization(
            authorization_contract, env_tag=env_tag,
            clocks_per_us=clocks_per_us, numactl=numactl,
            env_contract=env_contract,
        )
        bound_cfg = ident.bind_environment_contract(cfg, contract)
        identity = str(ident.campaign_id(bound_cfg))
        validate_campaign_id(identity)
        digest = hashlib.sha256(
            ident.canonical_preimage(bound_cfg).encode("utf-8")
        ).hexdigest()
        if (contract.contract_sha256 != saved.contract_sha256
                or identity != saved.campaign_identity
                or digest != saved.protocol_digest
                or declared_use_class != saved.declared_use_class
                or base_root != saved.output_root):
            raise execution_guard.ExecutionGuardError("authorization session binding mismatch")
        if pre_write_validator is not None:
            pre_write_validator(identity)
        if reservation.is_reservation_required(contract.isolation_policy):
            binding = reservation.read_binding(os.environ)
            reservation.check_reservation(
                binding, required_s=1, safety_margin_s=0, environ=os.environ,
            )
            if binding != saved.reservation_binding:
                raise execution_guard.ExecutionGuardError("authorization session reservation mismatch")
            claim_root = Path(env_scope_dir(contract.env_tag, base_root)) / "claims"
            if claim_root.is_symlink() or not claim_root.is_dir():
                raise execution_guard.ExecutionGuardError("authorization session claim root invalid")
            write_capability_for_directory(claim_root, policy=durable_root_policy)
            claim = saved.acquired_claim
            if (claim is None
                    or claim.path != campaign_claim._claim_path(claim_root, identity)
                    or claim.record.proc_starttime != campaign_claim.read_proc_starttime()
                    or campaign_claim._read_existing_record(claim.path) != claim.record):
                raise execution_guard.ExecutionGuardError("authorization session claim mismatch")
        receipt = json.loads(saved.receipt_json)
        if contract.attestation_mode == "required":
            verified = env_attestation.load_verified_calibration(contract, _repo_root())
            if not execution_guard.receipt_matches_contract(
                    receipt, env_tag=contract.env_tag,
                    contract_sha256=contract.contract_sha256,
                    attestation_mode=contract.attestation_mode,
                    verified_calibration=verified):
                raise execution_guard.ExecutionGuardError("authorization session receipt mismatch")
        if _AUTHORIZATION_SESSIONS.get(session) != (issued_pid, saved):
            raise execution_guard.ExecutionGuardError("authorization session closed during reuse")
        return _AuthorizationResult(
            contract, receipt, bound_cfg, identity,
            saved.acquired_claim, saved.reservation_binding,
        )
    except (ValueError, TypeError, OSError) as exc:
        raise execution_guard.ExecutionGuardError(
            f"authorization session validation failed: {exc}"
        ) from exc


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _policy_perf_candidates(repo_root: Path) -> tuple[str, ...]:
    """Pegasus policy の既存 perf 候補を evidence 用にだけ読む。"""
    path = Path(repo_root) / "tools/pegasus/policy.json"
    try:
        policy = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise _perf_preflight.PerfPreflightError(
            f"perf candidate policy を読めない: {path}: {exc}"
        ) from exc
    candidates = policy.get("perf_candidates") if isinstance(policy, dict) else None
    if (not isinstance(candidates, list)
            or not all(isinstance(candidate, str) and candidate for candidate in candidates)
            or len(set(candidates)) != len(candidates)):
        raise _perf_preflight.PerfPreflightError(
            "policy.perf_candidates が一意な str list でない"
        )
    return tuple(candidates)


def _perform_perf_preflight(
        producer: Callable[..., object],
        *, receipt_path: str = "",
) -> tuple[dict, bool]:
    """探索 bench の perf 可否を一度だけ確定し、判定不能は上位へ送出する。"""
    receipt = _perf_preflight.validate_perf_preflight_receipt(producer(
        perf_candidates=_policy_perf_candidates(_repo_root()),
    ))
    if receipt_path:
        path = Path(receipt_path)
        if not path.is_absolute() or not path.parent.is_dir() or path.is_symlink():
            raise _perf_preflight.PerfPreflightError(
                "perf preflight receipt path が既存 absolute parent に束縛されていない"
            )
        payload = (
            json.dumps(receipt, sort_keys=True, separators=(",", ":"), allow_nan=False)
            + "\n"
        ).encode("utf-8")
        flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_NOFOLLOW", 0)
        try:
            fd = os.open(path, flags, 0o600)
            try:
                if os.write(fd, payload) != len(payload):
                    raise OSError("short perf preflight receipt write")
                os.fsync(fd)
            finally:
                os.close(fd)
            parent_fd = os.open(
                path.parent, os.O_RDONLY | getattr(os, "O_DIRECTORY", 0),
            )
            try:
                os.fsync(parent_fd)
            finally:
                os.close(parent_fd)
        except OSError as exc:
            raise _perf_preflight.PerfPreflightError(
                f"perf preflight receipt を durable 保存できない: {exc}"
            ) from exc
    return receipt, _perf_preflight.use_perf_from_receipt(receipt)


def _closed_verify_workloads(cfg: CampaignConfig, perf: PerfConfig):
    """Validate verify mode and construct opt-in passes before authorization."""
    mode = cfg.search_config.get(SEARCH_CONFIG_VERIFY_KEY)
    if mode is None or mode == LEGACY_TAG:
        return None
    if mode == VERIFY_LEGACY_PLUS_S2:
        return [(S2_TAG, s2_correctness_workload())]
    if mode == VERIFY_LEGACY_PLUS_PERFORMANCE:
        return [(PERFORMANCE_TAG, performance_correctness_workload(perf))]
    raise ValueError(f"unsupported verify mode: {mode!r}")


def _authorize_measurement(
        cfg: CampaignConfig,
        authorization_contract: AuthorizedContract, *,
        env_tag: str, clocks_per_us: int,
        numactl: Optional[Sequence[str]],
        env_contract: Optional[ExecutionEnvironmentContract] = None,
        declared_use_class: str,
        output_root: str,
        durable_root_policy=None,
        pre_write_validator: Optional[Callable[[str], None]] = None,
        authorization_session: Optional[_AuthorizationSession] = None,
) -> _AuthorizationResult:
    """明示 contract と required attestation を最初の書込みより前に検査する。"""
    if authorization_session is not None:
        return _authorize_with_session(
            authorization_session, cfg, authorization_contract,
            env_tag=env_tag, clocks_per_us=clocks_per_us, numactl=numactl,
            env_contract=env_contract, declared_use_class=declared_use_class,
            output_root=output_root, durable_root_policy=durable_root_policy,
            pre_write_validator=pre_write_validator,
        )
    contract = execution_guard.require_certified_writer_authorization(
        authorization_contract,
        env_tag=env_tag,
        clocks_per_us=clocks_per_us,
        numactl=numactl,
        env_contract=env_contract,
    )
    receipt = None
    if contract.attestation_mode == "required":
        verified = env_attestation.load_verified_calibration(contract, _repo_root())
        receipt = execution_guard.attest_and_build_receipt(contract, verified)
        if not execution_guard.receipt_matches_contract(
            receipt,
            env_tag=contract.env_tag,
            contract_sha256=contract.contract_sha256,
            attestation_mode=contract.attestation_mode,
            verified_calibration=verified,
        ):
            raise execution_guard.ExecutionGuardError(
                "execution receipt の契約再検算に失敗"
            )

    bound_cfg = ident.bind_environment_contract(cfg, contract)
    campaign_identity = str(ident.campaign_id(bound_cfg))
    validate_campaign_id(campaign_identity)
    if pre_write_validator is not None:
        pre_write_validator(campaign_identity)

    acquired_claim = None
    binding = None
    if reservation.is_reservation_required(contract.isolation_policy):
        env = os.environ
        binding = reservation.read_binding(env)
        # presence gate であり、campaign 実行時間の保護を意味しない。
        reservation.check_reservation(
            binding,
            required_s=1,
            safety_margin_s=0,
            environ=env,
        )
        base_root = resolve_campaign_output_root(declared_use_class, output_root)
        claim_root = Path(env_scope_dir(contract.env_tag, base_root)) / "claims"
        if claim_root.is_symlink() or not claim_root.is_dir():
            raise execution_guard.ExecutionGuardError(
                "campaign claim root が durable output root 下に事前 provisioning "
                f"済みでない: {claim_root}"
            )
        write_capability_for_directory(claim_root, policy=durable_root_policy)
        protocol_digest = hashlib.sha256(
            ident.canonical_preimage(bound_cfg).encode("utf-8")
        ).hexdigest()
        record = campaign_claim.ClaimRecord(
            campaign_identity=campaign_identity,
            protocol_digest=protocol_digest,
            job_id=binding.job_id,
            host=binding.host,
            boot_id=binding.boot_id,
            pid=os.getpid(),
            proc_starttime=campaign_claim.read_proc_starttime(),
            created_utc=dt.datetime.now(dt.timezone.utc).isoformat(),
        )
        acquired_claim = campaign_claim.acquire_claim(claim_root, record)

    return _AuthorizationResult(
        authorized_contract=contract,
        execution_receipt=receipt,
        bound_cfg=bound_cfg,
        campaign_identity=campaign_identity,
        acquired_claim=acquired_claim,
        reservation_binding=binding,
    )


def _validate_result_evidence_context(
        context: Optional[
            reflux_result_evidence.ResultEvidenceIssuanceContext
        ], *,
        genomes: Sequence[Genome],
        balanced_schedule: Optional[BalancedScheduleConfig],
) -> None:
    """Reject an ambiguous issuance request before any durable campaign write."""
    if context is None:
        return
    from . import reflux_result_evidence as result_evidence

    if type(context) is not result_evidence.ResultEvidenceIssuanceContext:
        raise TypeError(
            "result_evidence_context must be an exact "
            "ResultEvidenceIssuanceContext"
        )
    if len(genomes) != 1:
        raise result_evidence.ResultEvidenceIssuanceRefused(
            "result evidence issuance refused: campaign issuance requires "
            "exactly one genome"
        )
    if balanced_schedule is not None:
        raise result_evidence.ResultEvidenceIssuanceRefused(
            "result evidence issuance refused: campaign issuance cannot be "
            "combined with a balanced schedule"
        )
    try:
        evidence_root = Path(context.evidence_root).resolve(strict=True)
    except (OSError, TypeError, ValueError) as exc:
        raise result_evidence.ResultEvidenceError(
            "result evidence root must be an existing directory"
        ) from exc
    if not evidence_root.is_dir():
        raise result_evidence.ResultEvidenceError(
            "result evidence root must be an existing directory"
        )


def _validate_result_evidence_layout(
        context: Optional[
            reflux_result_evidence.ResultEvidenceIssuanceContext
        ],
        layout_root: str,
) -> None:
    """Bind the prospective campaign layout beneath the existing evidence root."""
    if context is None:
        return
    from . import reflux_result_evidence as result_evidence

    evidence_root = Path(context.evidence_root).resolve(strict=True)
    try:
        physical_root = Path(layout_root).resolve(strict=False)
    except (OSError, TypeError, ValueError) as exc:
        raise result_evidence.ResultEvidenceError(
            "campaign layout root cannot be resolved"
        ) from exc
    if not physical_root.is_relative_to(evidence_root):
        raise result_evidence.ResultEvidenceError(
            "campaign layout root is outside the result evidence root"
        )


def _issue_campaign_result_evidence(
        *,
        layout: object,
        context: Optional[
            reflux_result_evidence.ResultEvidenceIssuanceContext
        ],
        build_attempt_id: str,
        verify_result: object | None,
        campaign_run_identity: str,
        environment_contract: ExecutionEnvironmentContract,
        execution_receipt: object | None,
) -> None:
    if context is None:
        return
    from . import reflux_result_evidence as result_evidence

    try:
        origin_campaign_id = context.origin_capability.campaign_id
    except AttributeError as exc:
        raise result_evidence.ResultEvidenceError(
            "origin capability campaign id is absent or invalid"
        ) from exc
    if type(origin_campaign_id) is not str or not origin_campaign_id:
        raise result_evidence.ResultEvidenceError(
            "origin capability campaign id is absent or invalid"
        )
    result_evidence.issue_campaign_result_evidence(
        layout=layout,
        context=context,
        build_attempt_id=build_attempt_id,
        verify_result=verify_result,
        campaign_run_identity=campaign_run_identity,
        campaign_id=origin_campaign_id,
        environment_contract=environment_contract,
        execution_receipt=execution_receipt,
    )


def run_campaign(cfg: CampaignConfig, genomes: Sequence[Genome],
                 perf: PerfConfig, env_tag: str, clocks_per_us: int,
                 numactl: Optional[Sequence[str]] = None,
                 do_bench: bool = True, output_root: str = "",
                 log=print, ccbench_dir: str = "", cache_root: str = "",
                 env_contract=None, dependency_prefix: str = "", *,
                 fetchcontent_base_dir: str = "",
                 masstree_source_dir: Optional[object] = None,
                 mimalloc_source_dir: Optional[object] = None,
                 googletest_source_dir: Optional[object] = None,
                 fetchcontent_dependency_receipt: Optional[
                     Mapping[str, object]
                 ] = None,
                 expected_toolchain_manifest=None,
                 authorization_contract: AuthorizedContract,
                 authorization_session: Optional[_AuthorizationSession] = None,
                 build_context: BuildRunContext,
                 capability_resolver: Optional[AdmissionCapabilityResolver] = None,
                 declared_use_class: str,
                 trigger_gate_binding=None,
                 perf_preflight_fn: Optional[Callable[..., object]] = None,
                 perf_preflight_receipt_path: str = "",
                 durable_root_policy=None,
                 correctness=None,
                 record_rep_integer_counters: bool = False,
                 bench_max_rounds: int = 3,
                 balanced_schedule: Optional[BalancedScheduleConfig] = None,
                 a1_source_context=None,
                 backoff_grammar_version: Optional[int] = None,
                 sort_oracle_contract_id: Optional[str] = None,
                 holdout_observation_admission: Optional[
                     HoldoutObservationAdmission
                 ] = None,
                 held_campaign_lock: Optional[HeldCampaignLock] = None,
                 verify_fanout_hosts: tuple[str, ...] = (),
                 result_evidence_context: Optional[
                     reflux_result_evidence.ResultEvidenceIssuanceContext
                 ] = None,
                 ) -> CampaignSummary:
    """`ccbench_dir`/`cache_root` (段5 git worktree 隔離): pipeline.evaluate と同じ実行時
    引数の素通し。`declared_use_class` は official / exploration の閉じた
    path selector で、campaign-id には含めない。
    `env_contract` と `dependency_prefix` は非既定時だけ素通しして既定 caller の
    evaluate 呼出し形を保つ。`expected_toolchain_manifest` は campaign 開始時に観測した
    v2 toolchain を source identity/build へ渡す。`build_context` の安定 policy を campaign
    identity へ束縛し、source ごとの capability resolver は evidence 解決後の pipeline へ渡す。
    `bench_max_rounds` は既定 3 の既存経路では従来の evaluate 呼出し形を維持し、明示的な
    非既定値だけを pipeline へ渡す。`balanced_schedule` は二 arm 専用 opt-in。"""
    if balanced_schedule is not None and record_rep_integer_counters:
        raise ValueError("balanced schedule does not support record_rep_integer_counters")
    if a1_source_context is not None and balanced_schedule is None:
        raise ValueError("A1 source context requires balanced schedule")
    _validate_result_evidence_context(
        result_evidence_context,
        genomes=genomes,
        balanced_schedule=balanced_schedule,
    )
    fetchcontent_prebuild = _validate_fetchcontent_prebuild_inputs(
        env_contract=env_contract,
        fetchcontent_base_dir=fetchcontent_base_dir,
        masstree_source_dir=masstree_source_dir,
        mimalloc_source_dir=mimalloc_source_dir,
        googletest_source_dir=googletest_source_dir,
        fetchcontent_dependency_receipt=fetchcontent_dependency_receipt,
    )
    if (isinstance(bench_max_rounds, bool)
            or not isinstance(bench_max_rounds, int)
            or bench_max_rounds < 1):
        raise ValueError("bench_max_rounds は 1 以上の整数でなければならない")
    if (
        balanced_schedule is not None
        and holdout_observation_admission is not None
    ):
        raise ValueError(
            "balanced_schedule cannot share one holdout observation admission: "
            "two arms require 2 * perf.reps observations but the token allowance "
            "is bound to protocol reps"
        )
    if (
        balanced_schedule is None
        and holdout_observation_admission is not None
        and len(genomes) > 1
    ):
        raise ValueError(
            "one holdout_observation_admission cannot cover multiple genomes: "
            "the attempt-bound token has a finite run_once allowance and reuse "
            "would exhaust it"
        )
    if balanced_schedule is not None:
        if type(balanced_schedule) is not BalancedScheduleConfig:
            raise TypeError("balanced_schedule must be an exact BalancedScheduleConfig")
        search_workload = cfg.search_config.get("workload")
        if (len(genomes) != 2 or do_bench is not True
                or bench_max_rounds != 1
                or cfg.search_config.get("pairing_design")
                != "balanced-a5b5-b5a5-v1"
                or cfg.search_config.get("arm_order")
                != list(balanced_schedule.arm_names)
                or type(search_workload) is not dict
                or search_workload.get("name") != balanced_schedule.workload):
            raise ValueError(
                "balanced schedule requires two arms, bench, max_rounds=1, "
                "the balanced pairing design, its arm order, and its bound workload"
            )
    if declared_use_class == "official":
        layout_constructor = campaign_layout
    elif declared_use_class == "exploration":
        layout_constructor = exploration_campaign_layout
    else:
        raise ValueError(
            f"unsupported declared_use_class: {declared_use_class!r}"
        )
    if declared_use_class == "official" and perf_preflight_fn is not None:
        raise ValueError(
            "official mode への非 default seam 注入を拒否する: "
            "['perf_preflight_fn']"
        )
    if perf_preflight_receipt_path:
        receipt_path = Path(perf_preflight_receipt_path)
        output_path = Path(output_root)
        if (
            not output_root
            or not receipt_path.is_absolute()
            or receipt_path.parent.resolve(strict=False)
               != output_path.resolve(strict=False)
        ):
            raise ValueError(
                "perf preflight receipt は campaign output root 直下に限る"
            )
    if type(build_context) is not BuildRunContext:
        raise TypeError("build_context は build_run_context() 由来の exact value が必要")
    grammar_key = backoff_hole_grammar.BACKOFF_GRAMMAR_VERSION_KEY
    if (grammar_key in cfg.search_config
            or backoff_grammar_version is not None):
        declared_grammar_version = cfg.search_config.get(grammar_key)
        expected_grammar_version = (
            backoff_hole_grammar.BACKOFF_GRAMMAR_VERSION
        )
        if (type(declared_grammar_version) is not int
                or declared_grammar_version != expected_grammar_version
                or type(backoff_grammar_version) is not int
                or backoff_grammar_version != declared_grammar_version):
            raise ValueError(
                "campaign backoff grammar version must exactly match the "
                "running grammar module before authorization or WAL"
            )
    if expected_toolchain_manifest is not None and env_contract is None:
        raise ValueError(
            "expected_toolchain_manifest は env_contract 付き v2 campaign に限る"
        )
    expected_compilers = None
    if expected_toolchain_manifest is not None:
        expected_compilers = buildcache.toolchain_compilers_from_manifest(
            expected_toolchain_manifest,
        )
    marker_present = "trigger_gate_binding_schema" in cfg.search_config
    marker = cfg.search_config.get("trigger_gate_binding_schema")
    if not marker_present:
        if trigger_gate_binding is not None:
            raise TypeError("trigger binding は schema marker 付き campaign 専用")
    elif marker != TRIGGER_BINDING_SCHEMA:
        raise ValueError("trigger binding schema marker が不正")
    elif cfg.search_config.get("axis") != wal.TRIGGER_AXIS:
        raise ValueError("trigger binding schema marker と campaign axis が不一致")
    elif (type(trigger_gate_binding) is not TriggerGateBinding
          or trigger_gate_binding.source is not None):
        raise TypeError("trigger campaign は source-null candidate binding が必要")
    # Verify mode is a closed input.  Resolve it before authorization, claims,
    # perf probes, layout creation, or WAL writes.  Unknown values must never
    # silently fall back to the inherited legacy-only pass.
    extra_correctness = _closed_verify_workloads(cfg, perf)
    cfg = ident.bind_admission_policy(cfg, build_context.policy)
    session_kwargs = (
        {} if authorization_session is None
        else {"authorization_session": authorization_session}
    )
    authorization = _authorize_measurement(
        cfg, authorization_contract, env_tag=env_tag, clocks_per_us=clocks_per_us,
        numactl=numactl, env_contract=env_contract,
        declared_use_class=declared_use_class, output_root=output_root,
        durable_root_policy=durable_root_policy,
        **session_kwargs,
        pre_write_validator=(
            None
            if result_evidence_context is None
            else lambda campaign_identity: _validate_result_evidence_layout(
                result_evidence_context,
                layout_constructor(campaign_identity, output_root).root,
            )
        ),
    )
    authorized_contract = authorization.authorized_contract
    execution_receipt = authorization.execution_receipt
    cfg = authorization.bound_cfg
    cid = authorization.campaign_identity
    perf_preflight_receipt = None
    use_perf = True
    if do_bench:
        perf_preflight_receipt, use_perf = _perform_perf_preflight(
            perf_preflight_fn or _perf_preflight.probe_perf_availability,
            receipt_path=perf_preflight_receipt_path,
        )
    layout = layout_constructor(cid, output_root).ensure()
    a1_non_certifying = ident.is_a1_non_certifying_config(cfg)
    lock_path = campaign_lock_path(
        layout, declared_use_class=declared_use_class, output_root=output_root,
    )
    with ExitStack() as stack:
        if held_campaign_lock is None:
            stack.enter_context(campaign_lock(lock_path))
        else:
            if type(held_campaign_lock) is not HeldCampaignLock:
                raise TypeError("held_campaign_lock must be an exact HeldCampaignLock")
            if (not held_campaign_lock.held
                    or held_campaign_lock.pid != os.getpid()
                    or held_campaign_lock.path != lock_path):
                raise ValueError("held_campaign_lock does not own this campaign path")
        if a1_non_certifying:
            stack.enter_context(wal.a1_non_certifying_io(layout))

        # 同一性を照合した後に限り、replay 前に無終端 tail を物理修復する。
        repair = ident.ensure_resumable_wal(
            cfg, layout, admission_policy=build_context.policy,
            authorization_contract=authorization_contract,
        )
        log(f"[campaign] {cid}  ({layout.root})")
        if repair.status == "repaired":
            log("[campaign] WAL tail repair: " + json.dumps({
                "status": repair.status,
                "original_size": repair.original_size,
                "final_size": repair.final_size,
                "removed_bytes": repair.removed_bytes,
                "removed_sha256": repair.removed_sha256,
                "preview": repair.preview,
                "receipt_path": repair.receipt_path,
            }, ensure_ascii=False, sort_keys=True))
            if balanced_schedule is not None:
                raise ValueError(
                    "balanced schedule refuses re-evaluation after interrupted WAL repair"
                )

        # リカバリ: terminal な variant はスキップ
        replay = (
            wal.replay_a1_non_certifying
            if a1_non_certifying else wal.replay
        )
        states = replay(layout, admission_policy=build_context.policy)
        if balanced_schedule is not None and any(
            state.last_terminal is not None
            and state.last_terminal.payload.get("reason")
            == INCOMPLETE_ATTEMPT_RECOVERY_REASON
            for state in states.values()
        ):
            raise ValueError(
                "balanced schedule refuses recovered incomplete attempts"
            )
        terminal = wal.terminal_variants(states)
        # transient infra 失敗による abort (identity-error = g++/git 一時失敗、*-probe-error =
        # 競合検知 pgrep 一時失敗) は genome-intrinsic な失敗 (verifier-red / build-error /
        # eval-exception) と違い環境修復で解消しうるので permanent skip にせず再評価する
        # (D25/B-3: terminal-abort が transient を誤分類して stock baseline を silently drop /
        # 環境故障を variant 固有欠陥に化けさせる穴を塞ぐ)。永続エラーなら再評価で同じ reason に
        # 倒れ abort 記録するのでクラッシュループにはならない (commit 済みは除外して再評価しない)。
        # 判定基準 (last_terminal) と正本 reason 集合は model.EvalState.retryable_abort を参照。
        retryable = {v for v, st in states.items() if st.retryable_abort}
        terminal = terminal - retryable
        if terminal:
            log(f"[campaign] リカバリ: {len(terminal)} variant は評価済み → スキップ")
        if retryable:
            log(f"[campaign] リカバリ: {len(retryable)} variant は transient abort "
                "(identity/probe-error) → 再評価")

        s = CampaignSummary(
            campaign_id=str(cid), layout_root=layout.root, total=len(genomes),
            execution_receipt=execution_receipt,
            perf_preflight_receipt=perf_preflight_receipt,
        )
        done = set(terminal)        # terminal を seed して 1 run 内の二重評価も防ぐ (U1)
        first_bench = True          # settle は最初の実 bench の前に 1 回だけ (calibrator 契約)
        balanced_prepared: List[_PreparedEvaluation] = []
        balanced_prepare_failed = False
        for g in genomes:
            # identity (D23/D24): skip/abort キーを src_token id に揃える (coder variant の
            # リカバリ冪等性 D・例外 abort の整合 A)。pipeline.evaluate と同じ確定窓口
            # (source_digest.resolve) を使い、確定済み src_token を渡して id 確定点を単一化する。
            # 確定不能は stock id で fails-closed abort (best-effort skip を持ち込まない, 規律2)。
            try:
                if expected_compilers is None:
                    _, resolved_cxx = _compilers_for_current_site()
                else:
                    _, resolved_cxx = expected_compilers
                evidence_cxx = _DEFAULT_CXX if resolved_cxx == _DEFAULT_CXX else resolved_cxx
                source_options = {}
                if backoff_grammar_version is not None:
                    source_options["backoff_grammar_version"] = (
                        backoff_grammar_version
                    )
                if sort_oracle_contract_id is not None:
                    source_options["sort_oracle_contract_id"] = (
                        sort_oracle_contract_id
                    )
                source_evidence = source_digest.resolve_evidence(
                    g, cfg.ccbench_commit, ccbench_dir=ccbench_dir,
                    cxx=evidence_cxx, **source_options,
                )
                src_tok = source_evidence.src_token
            except RuntimeError as e:
                v0 = variant_id(g)              # identity 不明ゆえ canonical のみの stock id
                if v0 in done:
                    # stock id が terminal 済み → この run では評価も abort 記録もできない。
                    # 沈黙させず可視化する (規律3): 永久 drop ではない (次 run で resolve が
                    # 直れば正しい src_token id で評価される) が、summary 上「リカバリ skip」
                    # と区別が付かないと成果物からの欠落が読めない。
                    s.skipped += 1
                    s.identity_skipped += 1
                    log(f"[campaign] {g.canonical()} identity 確定不能かつ stock id は "
                        f"terminal 済み → この run はスキップ (環境修復後の次 run で再評価): {e}")
                    if result_evidence_context is not None:
                        from . import reflux_result_evidence as result_evidence
                        raise result_evidence.ResultEvidenceIssuanceRefused(
                            "result evidence issuance refused: an existing "
                            "terminal attempt cannot be reissued after identity "
                            "resolution failed"
                        )
                    continue
                done.add(v0)
                attempt_id = secrets.token_hex(16)
                start_payload = {
                    "genome": g.canonical(),
                    "build_attempt_id": attempt_id,
                }
                if trigger_gate_binding is not None:
                    start_payload[wal.TRIGGER_BINDING_COMMITMENT_KEY] = \
                        wal.log_trigger_binding(
                            layout, v0, env_tag, attempt_id, trigger_gate_binding,
                        )
                wal.log(layout, v0, STAGE_BUILD_START, env_tag, start_payload)
                wal.log(layout, v0, STAGE_ABORT, env_tag,
                        {"reason": "identity-error", "error": str(e),
                         "build_attempt_id": attempt_id})
                log(f"[campaign] {v0} identity 確定不能 → abort 隔離して継続: {e}")
                r = EvalResult(
                    genome=g, variant=v0, certified=False, aborted=True,
                    notes=[f"source_digest 確定不能 → reject ({e})"],
                    build_attempt_id=attempt_id,
                )
                # A helper-side None check is too late: call arguments are evaluated first.
                if result_evidence_context is not None:
                    _issue_campaign_result_evidence(
                        layout=layout,
                        context=result_evidence_context,
                        build_attempt_id=r.build_attempt_id,
                        verify_result=r.verify_result,
                        campaign_run_identity=cid,
                        environment_contract=authorized_contract,
                        execution_receipt=execution_receipt,
                    )
                s.results.append(r)
                s.evaluated += 1
                s.aborted += 1
                balanced_prepare_failed = balanced_schedule is not None
                continue
            v = variant_id(g, src_tok)
            if v in done:
                if result_evidence_context is not None:
                    from . import reflux_result_evidence as result_evidence
                    raise result_evidence.ResultEvidenceIssuanceRefused(
                        "result evidence issuance refused: an existing terminal "
                        "attempt cannot be reissued"
                    )
                s.skipped += 1
                s.skipped_variants.append(v)
                balanced_prepare_failed = balanced_schedule is not None
                continue
            done.add(v)
            log(f"[campaign] evaluate {g.canonical()}")
            try:
                evaluate_options = {
                    "verify_fanout_hosts": verify_fanout_hosts,
                }
                if cfg.search_config.get("verify_performance_concurrent") is True:
                    evaluate_options["verify_performance_concurrent"] = True
                if env_contract is not None:
                    evaluate_options["env_contract"] = env_contract
                    evaluate_options["declared_use_class"] = declared_use_class
                    if expected_toolchain_manifest is not None:
                        evaluate_options["expected_toolchain_manifest"] = (
                            expected_toolchain_manifest
                        )
                if dependency_prefix:
                    evaluate_options["dependency_prefix"] = dependency_prefix
                if fetchcontent_prebuild:
                    evaluate_options.update({
                        "fetchcontent_base_dir": fetchcontent_base_dir,
                        "masstree_source_dir": masstree_source_dir,
                        "mimalloc_source_dir": mimalloc_source_dir,
                        "googletest_source_dir": googletest_source_dir,
                        "fetchcontent_dependency_receipt": (
                            fetchcontent_dependency_receipt
                        ),
                    })
                if trigger_gate_binding is not None:
                    evaluate_options["trigger_gate_binding"] = TriggerGateBinding(
                        mask=trigger_gate_binding.mask,
                        predicate_sha256=trigger_gate_binding.predicate_sha256,
                        nonce=trigger_gate_binding.nonce,
                        source=SourceBinding(
                            src_token=source_evidence.src_token,
                            source_bytes_sha256=source_evidence.source_bytes_sha256,
                        ),
                    )
                if perf_preflight_receipt is not None:
                    evaluate_options["perf_preflight_receipt"] = perf_preflight_receipt
                if not use_perf:
                    # True は pipeline の legacy default に任せ、利用可能時の呼出し形を維持する。
                    evaluate_options["use_perf"] = False
                if correctness is not None:
                    evaluate_options["correctness"] = correctness
                if record_rep_integer_counters:
                    evaluate_options["record_rep_integer_counters"] = True
                if bench_max_rounds != 3:
                    evaluate_options["bench_max_rounds"] = bench_max_rounds
                if backoff_grammar_version is not None:
                    evaluate_options["backoff_grammar_version"] = (
                        backoff_grammar_version
                    )
                if sort_oracle_contract_id is not None:
                    evaluate_options["sort_oracle_contract_id"] = (
                        sort_oracle_contract_id
                    )
                if holdout_observation_admission is not None:
                    evaluate_options["holdout_observation_admission"] = (
                        holdout_observation_admission
                    )
                if a1_source_context is not None:
                    evaluate_options["a1_source_context"] = a1_source_context
                if balanced_schedule is not None:
                    r = _prepare_evaluation(
                        g, layout, env_tag, cfg.ccbench_commit, perf,
                        clocks_per_us, numactl=numactl, do_bench=do_bench,
                        do_settle=False, src_token=src_tok,
                        extra_correctness=extra_correctness,
                        log=log, ccbench_dir=ccbench_dir, cache_root=cache_root,
                        authorization_contract=authorization_contract,
                        build_context=build_context,
                        capability_resolver=capability_resolver,
                        source_evidence=source_evidence,
                        canonical_build_pin=cfg.ccbench_commit,
                        **evaluate_options,
                    )
                else:
                    r = evaluate(
                        g, layout, env_tag, cfg.ccbench_commit, perf,
                        clocks_per_us, numactl=numactl, do_bench=do_bench,
                        do_settle=(do_bench and first_bench),
                        src_token=src_tok, extra_correctness=extra_correctness,
                        log=log, ccbench_dir=ccbench_dir, cache_root=cache_root,
                        authorization_contract=authorization_contract,
                        build_context=build_context,
                        capability_resolver=capability_resolver,
                        source_evidence=source_evidence,
                        **evaluate_options,
                    )
            except Exception as e:   # noqa: BLE001  この variant 固有の失敗を隔離する
                # 想定外の例外も abort として terminal 化し、再起動で同地点の再クラッシュを
                # 防ぐ (overnight 耐性 / A)。KeyboardInterrupt 等は Exception 外なので通す。
                if isinstance(e, (wal.WalAppendError, wal.WalFramingError)):
                    # WAL I/O が壊れた同じ台帳へ診断を重ねない。元の構造化例外を保つ。
                    raise
                replayed = replay(
                    layout, admission_policy=build_context.policy,
                ).get(v)
                result_attempt_id = ""
                abort_payload = {"reason": f"eval-exception: {type(e).__name__}: {e}"}
                if replayed is not None:
                    active = [
                        attempt for attempt in replayed.attempts.values()
                        if not attempt.committed and not attempt.aborted
                    ]
                    if len(active) == 1:
                        result_attempt_id = active[0].attempt_id
                        abort_payload["build_attempt_id"] = result_attempt_id
                        if active[0].receipt_sha256 is not None:
                            abort_payload["build_admission_receipt_sha256"] = \
                                active[0].receipt_sha256
                wal.log(layout, v, STAGE_ABORT, env_tag, abort_payload)
                log(f"[campaign] {v} 評価中に例外 → abort 隔離して継続: {e}")
                r = EvalResult(genome=g, variant=v, certified=False, aborted=True,
                               notes=[f"評価中の例外 → reject ({e})"],
                               build_attempt_id=result_attempt_id)
            if type(r) is _PreparedEvaluation:
                balanced_prepared.append(r)
                continue
            if balanced_schedule is not None:
                balanced_prepare_failed = True
            # Guard argument evaluation as well as the helper body for originless runs.
            if result_evidence_context is not None:
                _issue_campaign_result_evidence(
                    layout=layout,
                    context=result_evidence_context,
                    build_attempt_id=r.build_attempt_id,
                    verify_result=r.verify_result,
                    campaign_run_identity=cid,
                    environment_contract=authorized_contract,
                    execution_receipt=execution_receipt,
                )
            s.results.append(r)
            s.evaluated += 1
            if r.aborted:
                s.aborted += 1
            elif r.certified:
                s.committed += 1
                if do_bench and r.fitness_tps is not None:
                    first_bench = False     # 実 bench が 1 回成功 → 以降 settle 不要
        if balanced_schedule is not None and balanced_prepared:
            if balanced_prepare_failed or len(balanced_prepared) != 2:
                peer_results = _abort_balanced_workload(
                    balanced_prepared,
                    "balanced-peer-prepare-failed",
                    "both balanced arms were not prepared and verified → reject workload",
                )
                s.results.extend(peer_results)
                s.evaluated += len(peer_results)
                s.aborted += len(peer_results)
            else:
                balanced_results, receipt = _run_balanced_schedule(
                    balanced_prepared, balanced_schedule,
                )
                s.balanced_schedule_receipt = receipt or None
                s.results.extend(balanced_results)
                s.evaluated += len(balanced_results)
                s.aborted += sum(result.aborted for result in balanced_results)
                s.committed += sum(
                    result.certified and not result.aborted
                    for result in balanced_results
                )
        log(f"[campaign] done: {s.committed} committed / {s.aborted} aborted / "
            f"{s.skipped} skipped (of {s.total})")
        return s
