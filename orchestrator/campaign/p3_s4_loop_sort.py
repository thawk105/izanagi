# -*- coding: utf-8 -*-
"""P3 後続段 5 driver — sort-strategy 変異軸の coder 自律ループ機械部分 (D41/D42/D43)。

`p3_s4_loop.py` (backoff 軸) の**兄弟 driver**。D42 決定6の方針通り、既存モジュールの
定数パラメータ化でなく新規モジュールとして新設した — sort 戦略は backoff (スカラー値の
変異) と異なり write_set_ 施錠順序 comparator という**コード片**の変異であり、genome
構築 (`BACKOFF_FIXED` 前提) と attribution 整合チェック (`_NOW_BACKOFF_RE` = backoff
固有の変数名/数値リテラル前提) が転用不可なため。共有できる汎用ヘルパ (`quarantine`/
`record_diff_reject`/`make_critic_digest`/`check_stop`/`LoopState` 永続化等) は
`orchestrator.campaign.p3_s4_loop` を `L` としてそのまま import し再利用する (`L.` 接頭辞 = backoff
driver と共有しているコードの目印)。

sort 戦略固有の設計 (敵対レビュー 2026-07-10、3レンズで確定):
  - `CoderProposalSort` に `value` フィールドは無い (数値でなくコード片の変異)。
    `strategy_summary` のような一言要約フィールドも持たない — 具体戦略名の例示は
    D39 決定7 (coder に勝ち筋の機序を見せない) を出力スキーマの例示という経路で
    直撃するリークだったため、`justification` のみに絞った (backoff 版と同型)。
  - `assert_value_literal_consistent` 相当の数値整合チェックは適用不可。代わりに auditor を
    **mandatory deny-only veto; affirmative security credit なし**の pre-build gate にする。
    `diff_digest` は attribution/provenance 専用であり、審査した working_diff の sha256 と、
    `--run-iteration` 実行時に
    `quarantine()` が実際に生成する working_diff の digest を突合し、不一致なら
    `AuditorGateFailure` で即座に停止する (backoff の `AttributionMismatch` と同型の
    「宣言でなく機械照合」)。auditor の reject/uncertain は
    diff-quarantine reject と同じ WAL 経路 (`record_diff_reject`) に相乗りさせ、
    既存の consumer (`load_diff_rejections`/`render_rejections`) をそのまま使う
    (auditor.md 型5 「consumer 取り残し」を自ら再演しない)。
  - PIN = `pin.CURRENT_PIN` (511c953、permutation 保存 assert 込み) — `p3_s4_loop.py`
    自身は歴史的 driver として `PIN="028f34d"` を literal 保持したまま変更しない
    (`pin.py` の裁定)。PIN が異なるため共有 tree での `assert_pinned_clean` 衝突を
    避けるべく、`--isolate-worktree` 相当を**既定 ON** にする (`--no-isolate-worktree`
    で opt-out。backoff driver の既定 OFF とは非対称、敵対レビュー 2026-07-10)。
  - `default_cfg()` で S2 verify (`legacy+s2`) を配線する。D41 がsort-strategy 採用の
    根拠にした「S2 (zipf skew0.9) が hot key 競合を実際に踏む」という前提を、この
    driver 自身でも効かせないと D41 の条件付き採用の土台が崩れる (敵対レビュー
    2026-07-10 で必須修正と判定)。

planner-v4 は無改変で再利用する (`L.PlannerProposal` そのまま)。direction/magnitude の
意味論は「コード変更の大小・探索方向」という抽象シグナルのままに留め、"乖離度"
"再順序化" 等の機序を示唆する解釈をメインセッション側にも注入しない (敵対レビュー
2026-07-10: 具体的な解釈注入は fairness reward hack を誘発しうる方向のヒントになり
D39 決定7 に触れる)。coder は新設の `coder-v4-autonomous-sort` (fresh subagent、
tools=[]) を使う。実 LLM (planner-v4/coder-v4-autonomous-sort/auditor/critic) は
メインセッションが spawn する — 本モジュールは LLM を spawn しない (Model Y 設計、
`p3_s4_loop.py` と同じ)。運用手順は `docs/phase3-s5-sort-runbook.md`。

型14 (非 SWO comparator) は、実 ``WriteElement<Tuple>`` と版固定 corpus を使う独立
oracle で build 前に反例探索する。有限 corpus 上で SWO 公理の反例を探す gate であり、任意
C++ の全入力に対する SWO の証明ではない。対象は coder 自律ループが合成する comparator
であり、s6 sweep の列挙候補 (SWO-by-construction) は対象外。fairness (型15) の機械観測点は
依然として未実装。
"""
from __future__ import annotations

import argparse
import contextlib
import json
import os
import sys
import time
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple
from pathlib import Path

if __package__ in {None, ""}:  # pragma: no cover - direct CLI execution
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
    __package__ = "orchestrator.campaign"

from . import buildcache, condition_meaning_gate, env_contract, ident, pin, wal  # noqa: E402
from . import p3_s4_loop as L                              # noqa: E402
from .p3_b4_protocol import (  # noqa: E402
    B4_PROTOCOL_KEY,
    B4_PROTOCOL_VALUE,
    driver_kind_from_identity as b4_driver_kind_from_identity,
)
from .artifact_admission import (                         # noqa: E402
    CampaignReadPurpose,
    require_admitted_campaign,
)
from .build_admission import (BuildAdmissionError, BuildRunContext, GeneratorId,  # noqa: E402
                                      add_registered_coder_build_authority_argument,
                                      build_run_context)
from .auditor_gate import (AuditorGateFailure,            # noqa: E402
                                   AuditorVerdict,
                                   apply_mandatory_deny_only_veto,
                                   auditor_reject_result, compute_diff_digest,
                                   parse_auditor_dict)
from .diff_quarantine import DiffQuarantineResult          # noqa: E402
from .layout import (CampaignLayout,                       # noqa: E402
                             exploration_campaign_layout)
from .loop import run_campaign                             # noqa: E402
from .model import CampaignConfig, Genome                  # noqa: E402
from .pipeline import SEARCH_CONFIG_VERIFY_KEY             # noqa: E402
from .pipeline import VERIFY_LEGACY_PLUS_S2                # noqa: E402
from .projection_guard import (                            # noqa: E402
    assert_closed_proposal_schema,
    assert_no_ability_probe_material,
)
from ..critic.digest import DIFF_QUARANTINE_REASON                   # noqa: E402
from ..critic.digest import load_diff_rejections                     # noqa: E402


# ---- campaign 定数 (s5_permutation_coverage.py 様式。実走前に pin/env を確認する) ----
PIN = pin.CURRENT_PIN                 # 511c953 (izanagi-trace, permutation 保存 assert 込み)
DECLARED_USE_CLASS = "exploration"
ENV_TAG = "linux-baremetal"
CLK = 1800
NUMA = ["numactl", "--interleave=all"]

MARKER_ID = "silo-writeset-sort"
SOURCE_REL = "cc/silo/transaction.cc"           # EVOLVE_BLOCK_SOURCES の一員 (D38 で拡張済み)
TEMPLATE_PATCH = "patches/silo-sort-variant.patch"  # 骨格 (hole) を敷く不変フレーム

# BACK_OFF を明示 (Options.cmake の CACHE 既定に暗黙依存しない、敵対レビュー 2026-07-10)。
_BASE = {"BACK_OFF": 1, "NO_WAIT_LOCKING_IN_VALIDATION": 1,
         "NO_WAIT_OF_TICTOC": 0, "WAL": 0}


def _require_condition_gate(source_root: str, genome: Genome) -> dict:
    value = genome.flags["SORT_VARIANT"]
    _cc, cxx = buildcache.compilers_for_current_site()
    captured = condition_meaning_gate.capture_define_inputs(source_root)
    request = condition_meaning_gate.make_define_request(
        driver_id="orchestrator.campaign.p3_s4_loop_sort",
        macro="SORT_VARIANT", requested_value=value, default_value=0,
    )
    supply = condition_meaning_gate.evaluate_define_supply_effectuation(
        captured, request=request, cxx=cxx, cmake="cmake",
    )
    meaning = condition_meaning_gate.evaluate_define_runtime_meaning(
        captured, request=request, declaration=None, cxx=cxx,
    )
    admission = condition_meaning_gate.require_condition_gate_family(
        [supply], [meaning], use_class="certified-selection",
    )
    if not admission.admitted:
        raise RuntimeError(
            "condition gate rejected P3 sort loop: "
            f"supply={supply.reason_code} meaning={meaning.reason_code}"
        )
    return {
        "supply_record": json.loads(supply.canonical_json()),
        "meaning_record": json.loads(meaning.canonical_json()),
        "admission": json.loads(admission.canonical_json()),
    }

# 停止条件 (収束/逆方向枯渇/予算) は `L.check_stop` に完全委譲 — backoff driver と同じ
# 規約 (`L.MAX_ITER`/`L.MAX_WALLTIME_S`、design v1 §4、D39 で凍結) をそのまま使う。


# ==== 提案・状態の型 (LLM 出力と harness 状態) =================================

@dataclass
class CoderProposalSort:
    """coder-v4-autonomous-sort の出力 (comparator コード片。value フィールドは無い —
    軸がコード片の変異のため数値概念が構造的に存在しない、D42 条件6)。`strategy_summary`
    のような一言要約フィールドも持たせない (敵対レビュー 2026-07-10: 具体戦略の例示が
    D39 決定7 のリーク制御を出力スキーマ経由で直撃した反省)。"""
    axis: str
    implementation: str               # EVOLVE-BLOCK hole 全体 (sort(...) 文一式) を置換する文字列
    justification: str = ""
    confidence: str = "medium"


# AuditorVerdict / AuditorGateFailure / compute_diff_digest / _AUDITOR_VERDICTS は
# `orchestrator.campaign.auditor_gate` へ共有昇格した (段 8a E 段レビュー 2026-07-12 — コード片軸
# 2 軸目)。本モジュールの公開名 (S.AuditorVerdict 等) は import で同一オブジェクトの
# まま維持 (既存テスト・runbook 無改変)。


# ==== diff 検疫 + auditor gate (hole 挿入は L.quarantine に委譲) ================

def _auditor_reject_result(subtype: str, auditor: AuditorVerdict) -> DiffQuarantineResult:
    """auditor gate reject の合成結果 (軸定数を束ねた薄い wrapper — 本体は
    `auditor_gate.auditor_reject_result` へ共有昇格、旧署名は後方互換で維持)。"""
    return auditor_reject_result(subtype, auditor,
                                 diff_region=SOURCE_REL, template_diff_id=MARKER_ID)


def _quarantine_and_audit(sub: str, coder: CoderProposalSort, auditor: AuditorVerdict,
                          genome: Genome, layout: CampaignLayout, state: L.LoopState,
                          planner: L.PlannerProposal, write: bool,
                          log=print) -> Optional[Dict]:
    """hole 挿入 → diff 検疫 → mandatory deny-only veto; affirmative security credit なし。

    ``diff_digest`` は attribution/provenance 専用。呼び出し元が return すべき reject dict を
    返すか (reject/gate不通過)、None (通過、呼び出し元は build へ進めるか dry-pass を返す)。

    **前提: 呼び出し元が既に `applied(TEMPLATE_PATCH)` 下にある。**"""
    res, _base, _edited, working_diff = L.quarantine(
        sub, coder.implementation, marker_id=MARKER_ID, source_rel=SOURCE_REL, write=write)
    combined = apply_mandatory_deny_only_veto(
        res,
        auditor,
        working_diff,
        diff_region=SOURCE_REL,
        template_diff_id=MARKER_ID,
    )
    oracle_rejected = False
    if combined.passed:
        # Import block is owned by a concurrent wave.  Keep the oracle dependency
        # local to the gate path and bind it to trusted post-materialization bytes.
        from .diff_quarantine import DiffRejectSubtype
        from .sort_swo_oracle import (
            ORACLE_CONTRACT_ID,
            OracleStatus,
            SortSwoOracleResult,
            SortSwoOracleUnavailable,
            attempt_record,
            check_materialized_sort_swo,
            rejection_digest,
            resolve_oracle_environment,
        )
        oracle_environment = resolve_oracle_environment(sub)
        oracle = check_materialized_sort_swo(
            _edited,
            marker_id=MARKER_ID,
            proposal_source=coder.implementation,
            environment=oracle_environment,
        )
        if type(oracle) is not SortSwoOracleResult or type(oracle.status) is not OracleStatus:
            raise TypeError("sort SWO oracle returned a non-contract result")
        if oracle.contract_id != ORACLE_CONTRACT_ID:
            raise TypeError("sort SWO oracle contract_id mismatch")
        if oracle.status is OracleStatus.UNAVAILABLE:
            if write:
                from .model import STAGE_S1_SESSION
                payload = attempt_record(oracle)
                payload["genome"] = genome.canonical()
                wal.log(
                    layout, L.diffq_variant_id(genome, coder.implementation),
                    STAGE_S1_SESSION, ENV_TAG, payload,
                )
            raise SortSwoOracleUnavailable(oracle)
        if oracle.status is OracleStatus.REJECT:
            assert oracle.finding is not None
            digest = rejection_digest(
                oracle, diff_region=SOURCE_REL, marker_id=MARKER_ID,
            )
            combined = DiffQuarantineResult(
                passed=False,
                subtype=DiffRejectSubtype.SORT_SWO_ORACLE,
                reason=oracle.finding.reason_code,
                digest=digest,
                violations=[digest],
            )
            oracle_rejected = True
        elif oracle.status is OracleStatus.PASS:
            if write:
                from .model import STAGE_S1_SESSION
                payload = attempt_record(oracle)
                payload["genome"] = genome.canonical()
                wal.log(
                    layout, L.diffq_variant_id(genome, coder.implementation),
                    STAGE_S1_SESSION, ENV_TAG, payload,
                )
        else:
            raise TypeError("sort SWO oracle returned an unknown status")
    if not combined.passed:
        v = L.record_diff_reject(
            layout, genome, coder.implementation, combined, env_tag=ENV_TAG,
        )
        L.project_whiteboard(state, planner, "rejected")
        if oracle_rejected:
            log(f"  sort SWO oracle reject: {combined.reason}")
        elif combined is res:
            log(f"  diff 検疫 reject: {combined.subtype} — {combined.reason}")
        else:
            log(f"  auditor gate reject (verdict={auditor.verdict}): "
                f"{len(auditor.violations)} violations")
        return {"outcome": "rejected", "variant": v, "digest": combined.digest}

    return None


# ==== campaign 設定 (S2 verify 配線込み、敵対レビュー 2026-07-10 必須修正) ========

def _repo_root() -> str:
    here = os.path.dirname(os.path.abspath(__file__))
    return os.path.dirname(os.path.dirname(here))


def default_cfg(
    reflux: bool = True,
    *,
    b4_reflux_ablation: bool = False,
    _b4_launch_context=None,
) -> CampaignConfig:
    """段 5 sort-strategy 自律ループの campaign 設定。

    `search_config[SEARCH_CONFIG_VERIFY_KEY] = VERIFY_LEGACY_PLUS_S2` で S2 (t48
    フルロード規模、zipf skew0.9 の hot key 競合) を legacy に追加する — D41 が
    sort-strategy 採用の根拠にした「S2 が実際に hot key 競合を踏む」という前提を
    この driver 自身で満たさないと D41 の条件付き採用の土台が崩れる (敵対レビュー
    2026-07-10 で必須修正と判定)。"""
    from .sort_swo_oracle import ORACLE_CONTRACT_ID

    search_config = {
        "scale": "silo", "axis": MARKER_ID,
        "reflux": "on" if reflux else "off",
        "records": 100_000, "threads": 4,
        "sort_swo_oracle": ORACLE_CONTRACT_ID,
        SEARCH_CONFIG_VERIFY_KEY: VERIFY_LEGACY_PLUS_S2,
    }
    if b4_reflux_ablation:
        from .p3_b4_launcher import require_b4_any_context
        require_b4_any_context(
            _b4_launch_context,
            expected_driver_kind="sort",
            boundary="sort marker creation",
        )
        search_config[B4_PROTOCOL_KEY] = B4_PROTOCOL_VALUE
    cfg = CampaignConfig(
        spec_slug="p3-s5-sort-loop", search_tag="s5-sort-autonomous",
        spec_content=("P3 後続段 5: sort-strategy (write_set 施錠順序 comparator) coder "
                      "自律ループ。planner が方向 (値なし) を提案し coder が勝ち筋を見ずに "
                      "comparator コードを合成、diff 検疫 (4a 型) + auditor 機械 gate + "
                      "独立 SWO oracle を通した hole 変異のみ build/verify(legacy+S2)/bench に "
                      "進む。critic 帰属を次 iteration に還流 (LLM ablation の on アーム)"),
        ccbench_commit=PIN,
        search_config=search_config,
        trial="p3-s5-sort-loop")
    context = build_run_context(generator_id=GeneratorId.BACKOFF_SWEEP)
    cfg = ident.bind_admission_policy(cfg, context.policy)
    return ident.bind_environment_contract(cfg, env_contract.lookup(ENV_TAG))


default_perf = L.default_perf   # 軸非依存 (kickoff 規模、有意性を主張しない配線規模)


# ==== 1 iteration の機械 E2E ==================================================

# 重複提案の解決は backoff 版と単一実装 ([T-157])。旧 sort 版は revert 後の tree へ
# `source_digest.resolve(..., sub)` を再実行しており、正しい tree でも patch revert 後
# ゆえ stock id (別 variant) を引いていた。id は run_campaign が applied(...) 内で確定
# した summary.skipped_variants だけを使う (id 確定点の単一化、D23/D24)。
_resolve_duplicate = L._resolve_duplicate


def run_one_iteration(cfg: CampaignConfig, perf, planner: L.PlannerProposal,
                      coder: CoderProposalSort, auditor: AuditorVerdict,
                      state: L.LoopState, sub: str, do_build: bool,
                      layout: Optional[CampaignLayout] = None, log=print,
                      cache_root: str = "",
                      build_context: Optional[BuildRunContext] = None,
                      _b4_launch_context=None) -> Dict:
    """1 iteration の機械部分を回す (backoff 版 `run_one_iteration` と同型の構造)。

    genome は `SORT_VARIANT=1` を焼く (`BACKOFF_FIXED` 相当なし)。auditor gate は
    dry/実 build いずれの経路でも通す (`_quarantine_and_audit` に factoring — backoff 版は
    dry/build で quarantine 呼び出しを重複させていたが、本 driver は auditor gate が
    増えた分ここで共通化した)。"""
    if cfg.search_config.get(B4_PROTOCOL_KEY) == B4_PROTOCOL_VALUE:
        from .p3_b4_launcher import require_b4_production_context
        require_b4_production_context(
            _b4_launch_context,
            expected_driver_kind=b4_driver_kind_from_identity(
                search_tag=cfg.search_tag,
                trial=cfg.trial,
                axis=cfg.search_config.get("axis"),
            ),
            expected_campaign_id=str(ident.campaign_id(cfg)),
            expected_arm=cfg.search_config.get("reflux"),
            boundary="sort run_one_iteration",
        )
    from .patchharness import applied
    if build_context is None and not do_build:
        build_context = build_run_context(generator_id=GeneratorId.BACKOFF_SWEEP)
    if type(build_context) is not BuildRunContext:
        raise TypeError("build_context は build_run_context() 由来の exact value が必要")
    cfg = ident.bind_admission_policy(cfg, build_context.policy)
    cfg = ident.bind_environment_contract(cfg, env_contract.lookup(ENV_TAG))
    genome = Genome("silo", {**_BASE, "SORT_VARIANT": 1})
    if layout is None:
        layout = exploration_campaign_layout(str(ident.campaign_id(cfg)))
    elif do_build and layout.root != exploration_campaign_layout(
            str(ident.campaign_id(cfg))).root:
        raise ValueError(f"build 経路の layout 注入は cfg 由来と一致必須 (WAL 分裂防止): "
                         f"{layout.root} != cfg 由来")
    layout.ensure()
    # auditor/diff reject も初回 WAL write になりうるため recovery seam を先行する。
    ident.ensure_resumable_attempts(
        cfg, layout, admission_policy=build_context.policy,
    )

    with applied(os.path.join(_repo_root(), TEMPLATE_PATCH), PIN, sub):
        gate = _quarantine_and_audit(sub, coder, auditor, genome, layout, state, planner,
                                     write=do_build, log=log)
        if gate is not None:
            return gate
        if not do_build:
            return {"outcome": "dry-pass", "variant": None}
        condition_gate = _require_condition_gate(sub, genome)
        summary = run_campaign(cfg, [genome], perf, ENV_TAG, CLK, numactl=NUMA, log=log,
                              ccbench_dir=sub, cache_root=cache_root,
                              authorization_contract=env_contract.authorize(ENV_TAG),
                              build_context=build_context,
                              declared_use_class=DECLARED_USE_CLASS)
    v = next((r.variant for r in summary.results), None)
    if v is None and summary.skipped > 0:
        duplicate = _resolve_duplicate(layout, planner, state, summary, log=log)
        duplicate["condition_gate"] = condition_gate
        return duplicate
    recs = wal.records_by_stage(layout, v) if v else {}
    r = summary.results[0] if summary.results else None
    if r and r.certified and not r.aborted:
        L.project_whiteboard(state, planner, "success", delta_pct=None)
        return {"outcome": "certified", "variant": v, "fitness_tps": r.fitness_tps,
                "verdict": r.verdict, "records": recs,
                "condition_gate": condition_gate}
    L.project_whiteboard(state, planner, "fail")
    return {"outcome": "aborted", "variant": v,
            "verdict": (r.verdict if r else ""), "records": recs,
            "condition_gate": condition_gate}


# ==== 段 5 駆動口 (実 planner/coder/auditor proposal を受けて 1 iteration を継続) ===

def load_proposal_file(
    path: str,
    *,
    b4_reflux_ablation: bool = False,
    b4_closed_critic_receipt_sha256: str | None = None,
) -> Tuple[L.PlannerProposal, CoderProposalSort,
           AuditorVerdict, Optional[bool]]:
    """メインセッションが spawn した planner/coder/auditor の構造化出力を JSON から読む。

    schema::

        {"planner": {axis, direction, magnitude, justification?, uncertainty?},
         "coder":   {axis, implementation, justification?, confidence?},
         "auditor": {verdict, diff_digest, violations?, nits?, proposed_tests?, uncertainty?},
         "prior_critic_reverse": true|false|null}

    `planner`/`coder`/`auditor` トップレベルキーは `d[...]` で読む (`.get` に頼らない —
    欠落は `KeyError` で fails-closed に落ちる、敵対レビュー 2026-07-10)。"""
    with open(path, encoding="utf-8") as f:
        d = json.load(f)
    schema_document = d
    if b4_reflux_ablation:
        if "prior_critic_reverse" in d:
            raise L.B4ProtocolError(
                "B-4 proposal must not self-report prior_critic_reverse"
            )
        has_receipt_binding = L.B4_PROPOSAL_RECEIPT_SHA256_KEY in d
        if b4_closed_critic_receipt_sha256 is None:
            if has_receipt_binding:
                raise L.B4ProtocolError(
                    "B-4 bootstrap proposal must not claim a critic receipt"
                )
        else:
            claimed = d.get(L.B4_PROPOSAL_RECEIPT_SHA256_KEY)
            if (
                type(claimed) is not str
                or claimed != b4_closed_critic_receipt_sha256
            ):
                raise L.B4ProtocolError(
                    "B-4 proposal receipt hash differs from terminal receipt bytes"
                )
        schema_document = dict(d)
        schema_document.pop(L.B4_PROPOSAL_RECEIPT_SHA256_KEY, None)
    elif b4_closed_critic_receipt_sha256 is not None:
        raise L.B4ProtocolError("proposal receipt binding requires B-4 mode")
    assert_closed_proposal_schema(
        schema_document, require_auditor=True, require_coder_value=False,
    )
    p, c, a = d["planner"], d["coder"], d["auditor"]
    planner = L.PlannerProposal(
        axis=p["axis"], direction=p["direction"], magnitude=p["magnitude"],
        justification=p.get("justification", ""), uncertainty=p.get("uncertainty", ""))
    coder = CoderProposalSort(
        axis=c["axis"], implementation=c["implementation"],
        justification=c.get("justification", ""), confidence=c.get("confidence", "medium"))
    auditor = parse_auditor_dict(a)   # verdict 未知・digest 空/非文字列 → AuditorGateFailure
    prior = None if b4_reflux_ablation else d.get("prior_critic_reverse")
    if prior is not None and not isinstance(prior, bool):
        raise ValueError(f"prior_critic_reverse は null か bool のみ (got {type(prior).__name__}: "
                         f"{prior!r}) — 非 bool は停止フィードバックを fail-open させる (規律2)")
    assert_no_ability_probe_material(d)
    return planner, coder, auditor, prior


def drive_iteration(cfg: CampaignConfig, perf, planner: L.PlannerProposal,
                    coder: CoderProposalSort, auditor: AuditorVerdict,
                    prior_critic_reverse: Optional[bool], sub: str, do_build: bool,
                    layout: Optional[CampaignLayout] = None, log=print,
                    cache_root: str = "",
                    build_context: Optional[BuildRunContext] = None,
                    b4_closed_critic_receipt: str | os.PathLike[str] | None = None,
                    b4_proposal_receipt_sha256: str | None = None,
                    _b4_launch_context=None) -> Dict:
    """段 5 sort-strategy の 1 iteration をメインセッション駆動で回す (backoff 版
    `drive_iteration` と同型: checkpoint 復元 → critic feedback 畳込み → 入口
    check_stop → iteration++ → run_one_iteration → checkpoint 保存 → digest 書き出し →
    末尾 check_stop)。checkpoint/whiteboard/停止判定は `L.` 側の汎用実装をそのまま使う
    (backoff 軸と同じ LoopState 型・同じ収束/予算/逆方向枯渇の規約)。"""
    if build_context is None and not do_build:
        build_context = build_run_context(generator_id=GeneratorId.BACKOFF_SWEEP)
    if type(build_context) is not BuildRunContext:
        raise TypeError("build_context は build_run_context() 由来の exact value が必要")
    cfg = ident.bind_admission_policy(cfg, build_context.policy)
    cfg = ident.bind_environment_contract(cfg, env_contract.lookup(ENV_TAG))
    if layout is None:
        layout = exploration_campaign_layout(str(ident.campaign_id(cfg)))
    b4_mode = L.b4_reflux_ablation_mode(cfg)
    if b4_mode:
        from .p3_b4_launcher import require_b4_production_context
        require_b4_production_context(
            _b4_launch_context,
            expected_driver_kind=b4_driver_kind_from_identity(
                search_tag=cfg.search_tag,
                trial=cfg.trial,
                axis=cfg.search_config.get("axis"),
            ),
            expected_campaign_id=str(ident.campaign_id(cfg)),
            expected_arm=cfg.search_config.get("reflux"),
            boundary="sort drive_iteration",
        )
        state = L.load_loop_state(layout)
        if state is None:
            state = L.LoopState(start_wall=time.time())
        L.require_b4_bootstrap_history_empty(layout, state)
        authorization = L.require_b4_iteration_authorization(
            cfg,
            layout,
            state,
            do_build=do_build,
            terminal_receipt_path=b4_closed_critic_receipt,
        )
        assert authorization is not None
        if prior_critic_reverse is not None:
            raise L.B4ProtocolError(
                "B-4 driver rejects self-reported prior_critic_reverse"
            )
        if authorization.terminal_receipt_sha256 != b4_proposal_receipt_sha256:
            raise L.B4ProtocolError(
                "B-4 proposal is not bound to the verified terminal receipt"
            )
        if authorization.receipt is not None:
            prior_critic_reverse = (
                authorization.receipt.decision_reverse_recommended
            )
        L.consume_b4_iteration_authorization(authorization)
    else:
        if (
            b4_closed_critic_receipt is not None
            or b4_proposal_receipt_sha256 is not None
        ):
            raise L.B4ProtocolError(
                "B-4 receipt inputs require the exact protocol marker"
            )
        state = None
    layout.ensure()
    ident.ensure_resumable_attempts(
        cfg, layout, admission_policy=build_context.policy,
    )
    if state is None:
        state = L.load_loop_state(layout)
        if state is None:
            state = L.LoopState(start_wall=time.time())
    L._fold_critic_reverse(state, prior_critic_reverse)

    pre = L.check_stop(state)
    if pre.stop:
        L.save_loop_state(layout, state)
        log(f"  入口停止 (iteration 消費せず): {pre.reason}")
        return {"outcome": "stopped-before", "variant": None,
                "stop_reason": pre.reason, "iteration": state.iteration, "ran": False}

    state.iteration += 1
    iteration_kwargs = {}
    if b4_mode:
        iteration_kwargs["_b4_launch_context"] = _b4_launch_context
    out = run_one_iteration(cfg, perf, planner, coder, auditor, state, sub,
                            do_build=do_build, layout=layout, log=log,
                            cache_root=cache_root, build_context=build_context,
                            **iteration_kwargs)
    L.save_loop_state(layout, state)

    critic_view = require_admitted_campaign(
        layout.root,
        purpose=CampaignReadPurpose.CERTIFIED_ACCEPTANCE,
    )
    digest_txt = L.make_critic_digest(
        critic_view,
        tag="p3-s5-sort",
        reflux=(cfg.search_config.get("reflux") == "on"),
        identity_projection=L.make_critic_identity_projection(critic_view),
    )
    with open(os.path.join(layout.root, "s5_sort_loop_digest.txt"), "w", encoding="utf-8") as f:
        f.write(digest_txt)

    post = L.check_stop(state)
    out.update({"stop_reason": post.reason, "iteration": state.iteration, "ran": True})
    return out


# ==== CLI =======================================================================

def _preview_diff(implementation_path: str, sub: str, root: str) -> Dict:
    """auditor へ渡す実 diff を得る (メインセッションが auditor spawn 前に呼ぶ)。

    implementation テキストファイルを読み、テンプレ骨格下で `quarantine(write=False)` を
    実走し working_diff + diff_digest を返す。auditor の入力構築 (diff 本文) と、
    proposal JSON の `auditor.diff_digest` (機械照合対象) の両方をこの一手で揃える。"""
    from .patchharness import applied, assert_pinned_clean
    with open(implementation_path, encoding="utf-8") as f:
        implementation = f.read()
    assert_pinned_clean(sub, PIN)
    with applied(os.path.join(root, TEMPLATE_PATCH), PIN, sub):
        res, _base, _edited, working_diff = L.quarantine(
            sub, implementation, marker_id=MARKER_ID, source_rel=SOURCE_REL, write=False)
    return {"passed": res.passed, "working_diff": working_diff,
           "diff_digest": compute_diff_digest(working_diff),
           "subtype": (res.subtype.value if res.subtype else None), "reason": res.reason}


def main(
    argv: Optional[List[str]] = None,
    *,
    _b4_launch_context=None,
) -> int:
    """fixture proposal で 1 iteration の機械 E2E を実走する (配線実証)。

    実 LLM (planner-v4/coder-v4-autonomous-sort/auditor/critic) はメインセッションが
    spawn する。本 main は harness の機械経路 (挿入→検疫→auditor gate→評価→WAL→digest→
    whiteboard→停止判定) が通ることを、人間が与えた fixture comparator (stock 相当の
    2 段比較、SWO 充足が自明) で確認する口。"""
    ap = argparse.ArgumentParser(description="P3 後続段 5 sort-strategy coder 自律ループ (機械 E2E)")
    ap.add_argument("--no-build", action="store_true",
                    help="build/verify/bench を省き挿入→検疫→auditor gate の配線のみ確認")
    add_registered_coder_build_authority_argument(
        ap,
        coder_entrypoint_site="orchestrator.campaign.p3_s4_loop_sort.main",
    )
    ap.add_argument("--reflux", choices=["on", "off"], default="on",
                    help="critic 還流 on/off (LLM ablation の対照アーム)")
    ap.add_argument("--b4-reflux-ablation", action="store_true",
                    help="exact B-4 protocol marker を campaign identity に焼く")
    ap.add_argument("--b4-closed-critic-receipt", type=Path, metavar="PATH",
                    help="B-4 continuation の certified terminal receipt")
    ap.add_argument("--run-iteration", metavar="PROPOSAL.json",
                    help="段5 駆動: 実 planner/coder/auditor proposal (JSON) を受けて "
                         "checkpoint 継続で 1 iteration を回す (メインセッションが毎 iteration これを呼ぶ)")
    ap.add_argument("--preview-diff", metavar="IMPLEMENTATION.txt",
                    help="auditor spawn 前の配線: implementation テキストを読み working_diff + "
                         "diff_digest を JSON で標準出力へ (build/single-tenant 不要)")
    ap.add_argument("--no-isolate-worktree", action="store_true",
                    help="段5 sort driver は git worktree 隔離が既定 ON (PIN が backoff driver "
                         "と異なるため共有 tree 衝突を避ける)。このフラグで無効化 (デバッグ用)")
    a = ap.parse_args(argv if argv is not None else sys.argv[1:])

    if a.b4_closed_critic_receipt is not None and not a.run_iteration:
        raise L.B4ProtocolError(
            "--b4-closed-critic-receipt requires --run-iteration"
        )
    if a.b4_closed_critic_receipt is not None and not a.b4_reflux_ablation:
        raise L.B4ProtocolError(
            "--b4-closed-critic-receipt requires --b4-reflux-ablation"
        )
    if a.b4_reflux_ablation and a.no_build:
        raise L.B4ProtocolError("B-4 protocol forbids --no-build")
    if a.b4_reflux_ablation and not a.run_iteration:
        raise L.B4ProtocolError(
            "B-4 protocol forbids the fixture run_one_iteration route"
        )

    root = _repo_root()
    fixed_sub = os.path.join(root, "external", "ccbench")

    if a.preview_diff:
        out = _preview_diff(a.preview_diff, fixed_sub, root)
        print(json.dumps(out, ensure_ascii=False, indent=2))
        return 0 if out["passed"] else 1

    if not a.no_build and a.coder_build_authority is None:
        raise BuildAdmissionError("--allow-coder-derived-build の明示 opt-in が必要")

    build_context = build_run_context(
        generator_id=GeneratorId.BACKOFF_SWEEP,
        coder_authority=None if a.no_build else a.coder_build_authority,
    )

    from . import patchharness
    from .p2_2 import _assert_single_tenant
    if not a.no_build:
        _assert_single_tenant()
    patchharness.assert_pinned_clean(fixed_sub, PIN)

    cfg = default_cfg(
        reflux=(a.reflux == "on"),
        b4_reflux_ablation=a.b4_reflux_ablation,
        _b4_launch_context=(
            _b4_launch_context if a.b4_reflux_ablation else None
        ),
    )
    cfg = ident.bind_admission_policy(cfg, build_context.policy)
    cfg = ident.bind_environment_contract(cfg, env_contract.lookup(ENV_TAG))
    perf = default_perf()

    isolate = not a.no_isolate_worktree
    if isolate:
        wt_cm = patchharness.checkout(PIN, base_dir=fixed_sub)
        cache_root = os.path.join(fixed_sub, "build-variants")
    else:
        wt_cm = contextlib.nullcontext(fixed_sub)
        cache_root = ""

    if a.run_iteration:
        proposal_receipt_sha256 = None
        if (
            a.b4_reflux_ablation
            and a.b4_closed_critic_receipt is not None
        ):
            proposal_receipt_sha256 = L.b4_terminal_receipt_sha256(
                a.b4_closed_critic_receipt
            )
        planner, coder, auditor, prior_rev = load_proposal_file(
            a.run_iteration,
            b4_reflux_ablation=a.b4_reflux_ablation,
            b4_closed_critic_receipt_sha256=proposal_receipt_sha256,
        )
        print(f"=== 段5 sort-strategy iteration (proposal={a.run_iteration}, "
              f"reflux={a.reflux}, build={not a.no_build}, prior_critic_reverse={prior_rev}, "
              f"isolate_worktree={isolate}) ===")
        with wt_cm as sub:
            out = drive_iteration(cfg, perf, planner, coder, auditor, prior_rev, sub,
                                  do_build=not a.no_build, cache_root=cache_root,
                                  build_context=build_context,
                                  b4_closed_critic_receipt=(
                                      a.b4_closed_critic_receipt
                                  ),
                                  b4_proposal_receipt_sha256=(
                                      proposal_receipt_sha256
                                  ),
                                  _b4_launch_context=_b4_launch_context)
        layout = exploration_campaign_layout(str(ident.campaign_id(cfg)))
        print(f"  ran={out['ran']} outcome={out['outcome']} "
              f"variant={out.get('variant')} iteration={out['iteration']}")
        print(f"  停止判定: {out['stop_reason']}")
        print(f"  checkpoint: {L.loop_state_path(layout)}")
        print(f"  digest: {os.path.join(layout.root, 's5_sort_loop_digest.txt')}")
        ok = (out["stop_reason"] in ("continue", "converged", "reverse-exhausted",
                                     "budget-iterations", "budget-walltime")
              and os.path.exists(L.loop_state_path(layout)))
        return 0 if ok else 1

    # fixture proposal (機械 E2E 用。stock 相当の 2 段比較 = SWO 充足が自明)。
    state = L.LoopState(start_ts=time.monotonic())
    state.iteration = 1
    planner = L.PlannerProposal(axis=MARKER_ID, direction="explore_both", magnitude="small",
                                justification="fixture (機械 E2E 用)")
    fixture_impl = (
        "  sort(write_set_.begin(), write_set_.end(),\n"
        "       [](const WriteElement<Tuple>& a, const WriteElement<Tuple>& b) -> bool {\n"
        "         return a.storage_ != b.storage_ ? a.storage_ < b.storage_\n"
        "                                         : a.key_ < b.key_;\n"
        "       });")
    coder = CoderProposalSort(axis=MARKER_ID, implementation=fixture_impl,
                              justification="fixture", confidence="low")

    print(f"=== 段5 sort-strategy loop 1 iteration (機械 E2E, reflux={a.reflux}, "
          f"build={not a.no_build}, isolate_worktree={isolate}) ===")
    with wt_cm as sub:
        from .patchharness import applied
        with applied(os.path.join(root, TEMPLATE_PATCH), PIN, sub):
            res, _b, _e, working_diff = L.quarantine(
                sub, fixture_impl, marker_id=MARKER_ID, source_rel=SOURCE_REL, write=False)
        auditor = AuditorVerdict(verdict="pass", diff_digest=compute_diff_digest(working_diff),
                                 uncertainty="fixture (機械 E2E 用、実 auditor 未使用)")
        out = run_one_iteration(cfg, perf, planner, coder, auditor, state, sub,
                                do_build=not a.no_build, cache_root=cache_root,
                                build_context=build_context)
    print(f"  outcome={out['outcome']} variant={out.get('variant')}")

    layout = exploration_campaign_layout(str(ident.campaign_id(cfg)))
    critic_view = require_admitted_campaign(
        layout.root,
        purpose=CampaignReadPurpose.CERTIFIED_ACCEPTANCE,
    )
    digest_txt = L.make_critic_digest(
        critic_view,
        tag="p3-s5-sort",
        reflux=(a.reflux == "on"),
        identity_projection=L.make_critic_identity_projection(critic_view),
    )
    out_path = os.path.join(layout.root, "s5_sort_loop_digest.txt")
    layout.ensure()
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(digest_txt)

    stop = L.check_stop(state)
    dqs = load_diff_rejections(critic_view)
    n_wal = len(list(wal.read_records(layout)))
    checks = {
        f"iteration(={state.iteration}) が WAL レコード数(={n_wal})と独立 (WAL 由来でない)":
            state.iteration == 1 and n_wal != state.iteration,
        "critic digest 書き出し": os.path.exists(out_path),
        "停止判定が機械的に返る": stop.reason in (
            "continue", "converged", "reverse-exhausted",
            "budget-iterations", "budget-walltime"),
    }
    if out["outcome"] != "dry-pass":
        checks["whiteboard に 1 行射影 (機序なし)"] = len(state.whiteboard) == 1
        checks["whiteboard entry が方向/結果のみ (機序フィールド無し)"] = (
            len(state.whiteboard) == 1
            and set(vars(state.whiteboard[0])) == {
                "iteration", "direction", "magnitude", "result", "delta_pct"})
    if out["outcome"] == "rejected":
        checks["reject が WAL に焼かれ load_diff_rejections が復元"] = (
            any(d.variant == out["variant"] and d.subtype for d in dqs))
        checks["reject が whiteboard で result=rejected"] = (
            state.whiteboard[0].result == "rejected")
    elif out["outcome"] == "certified":
        checks["certified で fitness_tps あり"] = out.get("fitness_tps") is not None
        checks["certified で whiteboard result=success"] = (
            state.whiteboard[0].result == "success")

    print("\n=== 判定 (WAL/状態 機械確認) ===")
    ok = all(checks.values())
    for name, passed in checks.items():
        print(f"  [{'PASS' if passed else 'FAIL'}] {name}")
    print(f"\ncampaign dir: {layout.root}")
    print(f"停止判定: stop={stop.stop} reason={stop.reason}")
    print(f"\n段5 sort-strategy loop 1 iteration 判定: {'PASS' if ok else 'FAIL'}")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
