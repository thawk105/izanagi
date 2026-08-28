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
from contextlib import ExitStack
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, List, Optional, Sequence

from ..calibrator import perf_preflight as _perf_preflight
from . import (buildcache, campaign_claim, env_attestation, execution_guard, ident,
               reservation, source_digest, wal)
from .build_admission import BuildRunContext
from .env_contract import AuthorizedContract, ExecutionEnvironmentContract
from .layout import (campaign_layout, env_scope_dir,
                     campaign_lock_path,
                     exploration_campaign_layout,
                     resolve_campaign_output_root,
                     validate_campaign_id, write_capability_for_directory)
from .lock import campaign_lock
from .model import CampaignConfig, Genome, STAGE_ABORT, STAGE_BUILD_START
from .pipeline import (AdmissionCapabilityResolver, EvalResult, LEGACY_TAG,
                       PERFORMANCE_TAG, PerfConfig, S2_TAG,
                       SEARCH_CONFIG_VERIFY_KEY,
                       VERIFY_LEGACY_PLUS_PERFORMANCE, VERIFY_LEGACY_PLUS_S2,
                       evaluate, performance_correctness_workload,
                       s2_correctness_workload, variant_id)
from .trigger_gate_binding import (
    SCHEMA_VERSION as TRIGGER_BINDING_SCHEMA,
    SourceBinding,
    TriggerGateBinding,
)

_DEFAULT_CXX = buildcache.DEFAULT_CXX
_compilers_for_current_site = buildcache.compilers_for_current_site


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


@dataclass(frozen=True)
class _AuthorizationResult:
    authorized_contract: ExecutionEnvironmentContract
    execution_receipt: Optional[dict]
    bound_cfg: CampaignConfig
    campaign_identity: str


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
) -> _AuthorizationResult:
    """明示 contract と required attestation を最初の書込みより前に検査する。"""
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
        campaign_claim.acquire_claim(claim_root, record)

    return _AuthorizationResult(
        authorized_contract=contract,
        execution_receipt=receipt,
        bound_cfg=bound_cfg,
        campaign_identity=campaign_identity,
    )


def run_campaign(cfg: CampaignConfig, genomes: Sequence[Genome],
                 perf: PerfConfig, env_tag: str, clocks_per_us: int,
                 numactl: Optional[Sequence[str]] = None,
                 do_bench: bool = True, output_root: str = "",
                 log=print, ccbench_dir: str = "", cache_root: str = "",
                 env_contract=None, dependency_prefix: str = "", *,
                 expected_toolchain_manifest=None,
                 authorization_contract: AuthorizedContract,
                 build_context: BuildRunContext,
                 capability_resolver: Optional[AdmissionCapabilityResolver] = None,
                 declared_use_class: str,
                 trigger_gate_binding=None,
                 perf_preflight_fn: Optional[Callable[..., object]] = None,
                 perf_preflight_receipt_path: str = "",
                 durable_root_policy=None,
                 ) -> CampaignSummary:
    """`ccbench_dir`/`cache_root` (段5 git worktree 隔離): pipeline.evaluate と同じ実行時
    引数の素通し。`declared_use_class` は official / exploration の閉じた
    path selector で、campaign-id には含めない。
    `env_contract` と `dependency_prefix` は非既定時だけ素通しして既定 caller の
    evaluate 呼出し形を保つ。`expected_toolchain_manifest` は campaign 開始時に観測した
    v2 toolchain を source identity/build へ渡す。`build_context` の安定 policy を campaign
    identity へ束縛し、source ごとの capability resolver は evidence 解決後の pipeline へ渡す。"""
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
    authorization = _authorize_measurement(
        cfg, authorization_contract, env_tag=env_tag, clocks_per_us=clocks_per_us,
        numactl=numactl, env_contract=env_contract,
        declared_use_class=declared_use_class, output_root=output_root,
        durable_root_policy=durable_root_policy,
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
    with ExitStack() as stack:
        stack.enter_context(campaign_lock(campaign_lock_path(
            layout,
            declared_use_class=declared_use_class,
            output_root=output_root,
        )))
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

        # リカバリ: terminal な variant はスキップ
        replay = (
            wal.replay_a1_non_certifying
            if a1_non_certifying else wal.replay
        )
        states = replay(layout, admission_policy=build_context.policy)
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
                source_evidence = source_digest.resolve_evidence(
                    g, cfg.ccbench_commit, ccbench_dir=ccbench_dir, cxx=evidence_cxx,
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
                s.results.append(EvalResult(genome=g, variant=v0, certified=False,
                                            aborted=True,
                                            notes=[f"source_digest 確定不能 → reject ({e})"]))
                s.evaluated += 1
                s.aborted += 1
                continue
            v = variant_id(g, src_tok)
            if v in done:
                s.skipped += 1
                s.skipped_variants.append(v)
                continue
            done.add(v)
            log(f"[campaign] evaluate {g.canonical()}")
            try:
                evaluate_options = {}
                if env_contract is not None:
                    evaluate_options["env_contract"] = env_contract
                    evaluate_options["declared_use_class"] = declared_use_class
                    if expected_toolchain_manifest is not None:
                        evaluate_options["expected_toolchain_manifest"] = (
                            expected_toolchain_manifest
                        )
                if dependency_prefix:
                    evaluate_options["dependency_prefix"] = dependency_prefix
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
                r = evaluate(g, layout, env_tag, cfg.ccbench_commit, perf,
                             clocks_per_us, numactl=numactl, do_bench=do_bench,
                             do_settle=(do_bench and first_bench),
                             src_token=src_tok, extra_correctness=extra_correctness,
                             log=log, ccbench_dir=ccbench_dir, cache_root=cache_root,
                             authorization_contract=authorization_contract,
                             build_context=build_context,
                             capability_resolver=capability_resolver,
                             source_evidence=source_evidence,
                             **evaluate_options)
            except Exception as e:   # noqa: BLE001  この variant 固有の失敗を隔離する
                # 想定外の例外も abort として terminal 化し、再起動で同地点の再クラッシュを
                # 防ぐ (overnight 耐性 / A)。KeyboardInterrupt 等は Exception 外なので通す。
                if isinstance(e, (wal.WalAppendError, wal.WalFramingError)):
                    # WAL I/O が壊れた同じ台帳へ診断を重ねない。元の構造化例外を保つ。
                    raise
                abort_payload = {"reason": f"eval-exception: {type(e).__name__}: {e}"}
                replayed = replay(
                    layout, admission_policy=build_context.policy,
                ).get(v)
                if replayed is not None:
                    active = [
                        attempt for attempt in replayed.attempts.values()
                        if not attempt.committed and not attempt.aborted
                    ]
                    if len(active) == 1:
                        abort_payload["build_attempt_id"] = active[0].attempt_id
                        if active[0].receipt_sha256 is not None:
                            abort_payload["build_admission_receipt_sha256"] = \
                                active[0].receipt_sha256
                wal.log(layout, v, STAGE_ABORT, env_tag, abort_payload)
                log(f"[campaign] {v} 評価中に例外 → abort 隔離して継続: {e}")
                r = EvalResult(genome=g, variant=v, certified=False, aborted=True,
                               notes=[f"評価中の例外 → reject ({e})"])
            s.results.append(r)
            s.evaluated += 1
            if r.aborted:
                s.aborted += 1
            elif r.certified:
                s.committed += 1
                if do_bench and r.fitness_tps is not None:
                    first_bench = False     # 実 bench が 1 回成功 → 以降 settle 不要
        log(f"[campaign] done: {s.committed} committed / {s.aborted} aborted / "
            f"{s.skipped} skipped (of {s.total})")
        return s
