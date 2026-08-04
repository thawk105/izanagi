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

import json
import secrets
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional, Sequence

from . import (buildcache, env_attestation, env_contract as env_contract_registry,
               execution_guard, ident, site_policy, source_digest, wal)
from .build_admission import BuildRunContext
from .env_contract import ExecutionEnvironmentContract
from .layout import campaign_layout, exploration_campaign_layout
from .model import CampaignConfig, Genome, STAGE_ABORT, STAGE_BUILD_START
from .pipeline import (AdmissionCapabilityResolver, EvalResult, PerfConfig, S2_TAG,
                       SEARCH_CONFIG_VERIFY_KEY,
                       VERIFY_LEGACY_PLUS_S2, evaluate, s2_correctness_workload,
                       variant_id)
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


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _authorize_measurement(
        env_contract: Optional[ExecutionEnvironmentContract], *,
        env_tag: str, clocks_per_us: int,
        numactl: Optional[Sequence[str]],
) -> Optional[dict]:
    """明示 contract と required attestation を最初の書込みより前に検査する。"""
    actual_site = site_policy.current_site()
    if env_contract is None:
        return None
    if (actual_site == site_policy.PEGASUS_COMPUTE
            and env_contract != env_contract_registry.lookup("pegasus")):
        raise execution_guard.ExecutionGuardError(
            "Pegasus compute では登録済み pegasus env_contract だけを受理する"
        )
    if type(env_contract) is not ExecutionEnvironmentContract:
        raise TypeError("env_contract は exact ExecutionEnvironmentContract が必要")
    if (env_tag != env_contract.env_tag
            or clocks_per_us != env_contract.clocks_per_us
            or tuple(numactl or ()) != env_contract.numactl):
        raise execution_guard.ExecutionGuardError(
            "campaign 実行値が env_contract と完全一致しない"
        )
    if env_contract.attestation_mode != "required":
        return None
    verified = env_attestation.load_verified_calibration(env_contract, _repo_root())
    receipt = execution_guard.attest_and_build_receipt(env_contract, verified)
    if not execution_guard.receipt_matches_contract(
        receipt,
        env_tag=env_contract.env_tag,
        contract_sha256=env_contract.contract_sha256,
        attestation_mode=env_contract.attestation_mode,
        verified_calibration=verified,
    ):
        raise execution_guard.ExecutionGuardError(
            "execution receipt の契約再検算に失敗"
        )
    return receipt


def run_campaign(cfg: CampaignConfig, genomes: Sequence[Genome],
                 perf: PerfConfig, env_tag: str, clocks_per_us: int,
                 numactl: Optional[Sequence[str]] = None,
                 do_bench: bool = True, output_root: str = "",
                 log=print, ccbench_dir: str = "", cache_root: str = "",
                 env_contract=None, dependency_prefix: str = "", *,
                 build_context: BuildRunContext,
                 capability_resolver: Optional[AdmissionCapabilityResolver] = None,
                 campaign_namespace: str = "official",
                 trigger_gate_binding=None) -> CampaignSummary:
    """`ccbench_dir`/`cache_root` (段5 git worktree 隔離): pipeline.evaluate と同じ実行時
    引数の素通し。省略時は共有固定パス既定 (既存動作と完全互換)。`campaign_namespace` は
    official / exploration の閉じた path selector。namespace は campaign-id に含めず、
    `env_contract` と `dependency_prefix` は非既定時だけ素通しして既定 caller の
    evaluate 呼出し形を保つ。`build_context` の安定 policy を campaign identity へ束縛し、
    source ごとの capability resolver は evidence 解決後の pipeline へ渡す。"""
    if type(build_context) is not BuildRunContext:
        raise TypeError("build_context は build_run_context() 由来の exact value が必要")
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
    cfg = ident.bind_admission_policy(cfg, build_context.policy)
    if campaign_namespace == "official":
        layout_constructor = campaign_layout
    elif campaign_namespace == "exploration":
        layout_constructor = exploration_campaign_layout
    else:
        raise ValueError(f"未知の campaign namespace: {campaign_namespace!r}")

    execution_receipt = _authorize_measurement(
        env_contract, env_tag=env_tag, clocks_per_us=clocks_per_us,
        numactl=numactl,
    )
    cid = ident.campaign_id(cfg)
    layout = layout_constructor(str(cid), output_root).ensure()

    # D36 決定4-1: search_config[SEARCH_CONFIG_VERIFY_KEY]=="legacy+s2" で S2 構成
    # (t48 フルロード規模、データパス被覆担当) を legacy (検出力担当) に追加する。
    # search_config はここで既に campaign_id のハッシュ対象 (D13) なので、S2 on/off
    # の切り替えは自動的に別 campaign になり WAL terminal skip の汚染を構造的に防ぐ。
    extra_correctness = None
    if cfg.search_config.get(SEARCH_CONFIG_VERIFY_KEY) == VERIFY_LEGACY_PLUS_S2:
        extra_correctness = [(S2_TAG, s2_correctness_workload())]

    # 同一性を照合した後に限り、replay 前に無終端 tail を物理修復する。
    repair = ident.ensure_resumable_wal(
        cfg, layout, admission_policy=build_context.policy,
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
    states = wal.replay(layout, admission_policy=build_context.policy)
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
    )
    done = set(terminal)        # terminal を seed して 1 run 内の二重評価も防ぐ (U1)
    first_bench = True          # settle は最初の実 bench の前に 1 回だけ (calibrator 契約)
    for g in genomes:
        # identity (D23/D24): skip/abort キーを src_token id に揃える (coder variant の
        # リカバリ冪等性 D・例外 abort の整合 A)。pipeline.evaluate と同じ確定窓口
        # (source_digest.resolve) を使い、確定済み src_token を渡して id 確定点を単一化する。
        # 確定不能は stock id で fails-closed abort (best-effort skip を持ち込まない, 規律2)。
        try:
            _, resolved_cxx = _compilers_for_current_site()
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
            r = evaluate(g, layout, env_tag, cfg.ccbench_commit, perf,
                         clocks_per_us, numactl=numactl, do_bench=do_bench,
                         do_settle=(do_bench and first_bench),
                         src_token=src_tok, extra_correctness=extra_correctness,
                         log=log, ccbench_dir=ccbench_dir, cache_root=cache_root,
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
            replayed = wal.replay(layout, admission_policy=build_context.policy).get(v)
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
