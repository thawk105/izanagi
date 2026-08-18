# -*- coding: utf-8 -*-
"""P3 段 8a E 段 driver — silo-backoff-trigger-gating 軸の coder 自律ループ機械部分。

`p3_s4_loop_sort.py` (D43) を型とする兄弟 driver。設計は 3 レンズ
敵対レビュー (リーク制御/fails-closed/regression、2026-07-12) の裁定反映済み — 裁定の
正本は D51 + insight `output/insights/2026-07-12_s8a-stage-e-design-review.md`。

sort 版との構造差 (新テンプレの形):
  - **軸定数は全て `orchestrator.campaign.axis_trigger_gating` から import する** (自前定義しない)。
    軸定数ブロックが C 段成果物として先に在り、D 偵察器 (`s8a_trigger_sweep.py`) と
    本 driver の両方がそこから import する — sort 軸の歴史的経緯 (偵察器が E 段 driver を
    import) の逆転が完成する (D48 必須条件 5、axis-onboarding §1 脚注)。
  - auditor 機械 gate は **mandatory deny-only veto; affirmative security credit なし**。
    `diff_digest` は attribution/provenance 専用で、軸非依存部品は
    `orchestrator.campaign.auditor_gate` を使う (共有昇格)。
  - hole は骨格の述語代入 1 行 (`izanagi_gate_pass = <述語>;`、D49 決定 2)。coder 出力は
    `CoderProposalTriggerGating` の固定 5-bit wire (value なし)。
  - 構文契約 grep は受理 gate ではなく、凍結 emitter 出力の内部 drift assertion。
    coder 由来 C++ は materialize 経路へ存在せず、auditor は正準述語の diff だけを見る。
  - **provenance 情報源記録の受け皿** (D46 (a) のループ版、07-11 監査 L4-1 の宿主確定):
    `<campaign root>/reports/p3_s8a_trigger_loop_provenance.json`。詳細は
    `_write_provenance_header` / `_append_provenance_entry` の docstring。記録は
    `drive_iteration` (= `--run-iteration` と fixture main の共通経路) が自動で行い CLI で
    省略できない — 「宣言止まり」(謳うだけで発火しない義務) にしない。no-build の
    dry-pass は provenance/checkpoint までの配線確認とし、admitted campaign を要求する
    critic digest は生成しない。

偵察 firewall (D48 条件 7): 本 driver・coder 定義・runbook が E 段入力
(leakproof_context / planner direction / whiteboard) に流してよい偵察由来情報は軸の
生死二値 (`LIVENESS_BINARY`) のみ。偵察の具体勝ち点・要因部分集合・順位・シートの診断
数値は流さない (正本 = `axis_trigger_gating` docstring)。

planner-v4 は無改変で再利用 (`L.PlannerProposal`)。direction/magnitude は抽象シグナル
のまま (機序含みの解釈をメインセッションが注入しない、D43)。PIN は sort driver と同一
(511c953) だが backoff driver (028f34d literal) と異なるため worktree 隔離は既定 ON を
踏襲。運用手順は `docs/phase3-s8a-trigger-runbook.md`。
"""
from __future__ import annotations

import argparse
import contextlib
import json
import os
import re
import sys
import time
from dataclasses import dataclass, replace
from typing import Dict, List, Optional, Sequence, Tuple
from pathlib import Path

if __package__ in {None, ""}:  # pragma: no cover - direct CLI execution
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
    __package__ = "orchestrator.campaign"

from . import env_contract, execution_guard, ident, site_policy, wal  # noqa: E402
from . import p3_s4_loop as L                              # noqa: E402
from .build_admission import (BuildAdmissionError, BuildRunContext, GeneratorId,  # noqa: E402
                                      add_registered_coder_build_authority_argument,
                                      build_run_context)
from .auditor_gate import (AuditorGateFailure,            # noqa: E402
                                   AuditorVerdict,
                                   apply_mandatory_deny_only_veto,
                                   parse_auditor_dict, compute_diff_digest)
from .axis_trigger_gating import (_BASE, MARKER_ID, PIN,  # noqa: E402
                                          SOURCE_REL, SYNTAX_CONTRACT_FORBIDDEN,
                                          TEMPLATE_PATCH)
from .diff_quarantine import DiffQuarantineResult          # noqa: E402
from .layout import (CampaignLayout,                       # noqa: E402
                             exploration_campaign_layout)
from .loop import run_campaign                             # noqa: E402
from .model import (CampaignConfig, Genome, STAGE_ABORT,  # noqa: E402
                    STAGE_BUILD_START)
from .pipeline import SEARCH_CONFIG_VERIFY_KEY             # noqa: E402
from .pipeline import VERIFY_LEGACY_PLUS_S2                # noqa: E402
from .projection_guard import (                            # noqa: E402
    CODER_CONTRACT_TRIGGER_WIRE,
    assert_closed_proposal_schema,
    assert_no_ability_probe_material,
)
from . import reflux_ir as _reflux_ir                       # noqa: E402
from .reflux_ir import (TriggerGateIR, emit_predicate,     # noqa: E402
                                parse_wire)
from .trigger_gate_binding import (                        # noqa: E402
    SCHEMA_VERSION as TRIGGER_GATE_BINDING_SCHEMA,
    WAL_RECORD_STAGE as TRIGGER_GATE_BINDING_WAL_STAGE,
    TriggerGateBinding,
    commitment,
    expected_predicate_sha256,
    new_nonce,
)


# ---- campaign 定数 (軸定数は axis_trigger_gating が正本 — ここは環境・計測の定数のみ) ----
DECLARED_USE_CLASS = "exploration"
ENV_TAG = "linux-baremetal"
_SITE_ENV_TAGS = {
    site_policy.OTHER: ENV_TAG,
    site_policy.PEGASUS_COMPUTE: "pegasus",
}
_CAMPAIGN_ENV_KEY = "measurement_env"

_current_site = site_policy.current_site
_lookup = env_contract.lookup

DIGEST_BASENAME = "s8a_trigger_loop_digest.txt"
CRITIC_TAG = "p3-s8a-trigger"

# E 段入力 (coder/planner) に渡しうる偵察由来情報の全量 (D48 条件 7 / D50 決定 1)。
# 生死の根拠数値・workload 別の勝ち gate はここに書かない (リークレンズ N2 裁定 —
# 監査向けの詳述は provenance の gate_record 側に分離)。
LIVENESS_BINARY = "alive"
_PLANNER_DIRECTIONS = frozenset({"increase", "decrease", "explore_both"})
_PLANNER_MAGNITUDES = frozenset({"small", "medium", "large"})


# ==== 提案の型 (LLM 出力) =======================================================

@dataclass(frozen=True)
class CoderProposalTriggerGating:
    """coder-v4-autonomous-trigger-gating の固定 5-bit wire 出力。value
    フィールドは無い。`strategy_summary` 相当の一言要約も
    持たせない (具体戦略の例示リーク、D43 の反省を継承)。"""
    axis: str
    wire: str
    justification: str = ""
    confidence: str = "medium"

    def __post_init__(self) -> None:
        parse_wire(self.wire)
        if self.axis != MARKER_ID:
            raise ValueError("coder axis が trigger-gating でない")


def _assert_trigger_proposal_contract(
    planner: L.PlannerProposal, coder: CoderProposalTriggerGating,
) -> None:
    """Recheck trigger proposal attribution at loader and final sink."""
    if (
        type(coder) is not CoderProposalTriggerGating
        or not all(hasattr(planner, field) for field in (
            "axis", "direction", "magnitude",
        ))
        or type(planner.axis) is not str
        or type(coder.axis) is not str
        or planner.axis != coder.axis
        or planner.axis != MARKER_ID
    ):
        raise ValueError("planner/coder axis が trigger-gating と一致しない")
    if (
        type(planner.direction) is not str
        or planner.direction not in _PLANNER_DIRECTIONS
    ):
        raise ValueError("planner direction が閉じた enum にない")
    if (
        type(planner.magnitude) is not str
        or planner.magnitude not in _PLANNER_MAGNITUDES
    ):
        raise ValueError("planner magnitude が閉じた enum にない")


# ==== trusted emitter の内部 drift assertion ===================================

_FORBIDDEN_RE = re.compile("|".join(r"\b" + re.escape(t)
                                    for t in SYNTAX_CONTRACT_FORBIDDEN))


def check_syntax_contract(predicate: str) -> List[str]:
    """trusted emitter 出力の内部 drift を検査する。

    候補の受理 gate ではない。発火時は caller 入力を含めない固定文言で停止する。"""
    return sorted({m.group(0) for m in _FORBIDDEN_RE.finditer(predicate)})


# ==== provenance 情報源記録 (D46 (a) のループ版、07-11 監査 L4-1 の宿主) ==========

# E 段の入力・資材 (本 driver・coder 定義・runbook・whiteboard 種) を起草した実装
# セッション (2026-07-12) が読んだ情報源。firewall は「文書を経路として流さない」ことを
# 保証するが起草者の記憶は防げない — 見た事実を封じるのではなく記録して事後監査可能に
# する (D46 残存リスク (a) と同じ扱い)。不読も明示する (監査時に「見ていない」を主張
# するため)。F 段セッションが新たに文書を読んだら --extra-source で追記する義務 (runbook)。
INFORMATION_SOURCES: Tuple[Dict[str, str], ...] = (
    {"path": "docs/decisions.md#D48/D49/D50",
     "role": "読了 — 軸定義・機構実装・偵察の決定要旨。D50 決定/実測節は floor 超 best の"
             "workload 別数値を含む (起草者は見た)"},
    {"path": "docs/worklog.md 2026-07-11 (5)(6) / 2026-07-12 (1)",
     "role": "読了 — 直近状態と E 段 gate の判断待ち"},
    {"path": "docs/phase3.md 8a 項 / docs/axis-onboarding.md",
     "role": "読了 — 段の完了状況とオンボーディング手順 (§3-E が本実装の規定)"},
    {"path": "orchestrator/campaign/axis_trigger_gating.py",
     "role": "読了 — 軸定数・firewall 文言の正本"},
    {"path": "patches/silo-backoff-trigger-gating-variant.patch",
     "role": "読了 — 骨格と hole (述語代入 1 行) の現物"},
    {"path": "p3_s4_loop(_sort).py / test_p3_s4_loop_sort.py / "
             "phase3-s5-sort-runbook.md / coder-v4-autonomous-sort.md",
     "role": "読了 — sort 軸 E 段資材 (写経元の型)"},
    {"path": "output/insights/2026-07-11_s8a-trigger-gating-recon.md",
     "role": "不読 — 偵察 insight 本文 (勝ち点の詳細・裁定台帳) は E 段起草で開いて"
             "いない (D50 の凍結要旨のみ経由)"},
    {"path": "output/insights/2026-07-10_s8a-stage-b-sheet-backoff-trigger-gating.md",
     "role": "不読 — 軸定義シート本文は E 段起草で開いていない (D48 の裁定要旨のみ経由)"},
)

# E 段 gate 通過の根拠 (レビュー FC-5 裁定 — gate 判断こそ監査可能に記録する。規律 6:
# 外部入力の解釈を構造化して残す)。
GATE_RECORD: Dict[str, str] = {
    "basis": "D50 決定 1 — floor 超地形が 3 workload で cross-run 再現 (軸は生の強い候補)",
    "approval": "ユーザー指示 2026-07-12「izanagiの仕事を進めてください」を worklog "
                "2026-07-11 (5) 人間判断待ち (1) (E 段 gate) への承認と解釈して着手",
    "firewall_scope": "E 段 coder/planner 入力へ流すのは軸の生死二値 (alive) のみ "
                      "(D48 条件 7)",
}

PROVENANCE_BASENAME = "p3_s8a_trigger_loop_provenance.json"

# 偵察の診断値キー — E 段 provenance には決して書かない (リークレンズ SF1 裁定。手本の
# 偵察器 _write_provenance はこれらを持つが、あちらは偵察自身の記録であり E 段は違う)。
_PROVENANCE_FORBIDDEN_KEYS = frozenset({"effective_reasons", "floor_cv", "freq_source"})


def _provenance_path(layout: CampaignLayout) -> str:
    # reports/ は proof-chain 保護対象外 (guard_write が守るのは runs/・campaign.lock・
    # build-variants のみ) — 偵察器 provenance と同じ側チャネル置き場。
    return os.path.join(layout.root, "reports", PROVENANCE_BASENAME)


def _load_provenance(layout: CampaignLayout) -> Dict:
    """既存 provenance を読む。未知キーは保存 (前方互換)。JSON decode 不能は破損
    ファイルを `.corrupt.<unix秒>` へ退避した上で例外停止 — 手本 (偵察器) の
    「existing={} で silent 継続」は記録義務の黙殺なので継がない (レビュー FC-3 と
    regression SF4 の折衷裁定: 退避で復旧材料は保全しつつ、義務の fail-open はしない)。"""
    path = _provenance_path(layout)
    if not os.path.exists(path):
        return {}
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        quarantined = f"{path}.corrupt.{int(time.time())}"
        os.replace(path, quarantined)
        raise RuntimeError(
            f"provenance が JSON として読めない (破損): {path} — {e}。破損ファイルは "
            f"{quarantined} へ退避した。記録義務を黙って放棄しない (fails-closed) — "
            f"内容を確認し、復旧または削除してから再実行すること") from e


def _write_provenance(layout: CampaignLayout, prov: Dict) -> None:
    """atomic 書き込み (PID 付き tmp → os.replace、`save_loop_state` と同じ様式)。
    手本の偵察器は非 atomic 直書きだが、ここは中断で truncated JSON を残すと以後の
    全 iteration が破損停止するため atomic に強化する (レビュー FC-2 裁定)。"""
    bad = _PROVENANCE_FORBIDDEN_KEYS & set(prov)
    if bad:
        raise ValueError(f"E 段 provenance に偵察診断キー {sorted(bad)} は書けない "
                         f"(D48 条件 7 — 偵察 firewall。レビュー SF1 裁定)")
    path = _provenance_path(layout)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    tmp = f"{path}.{os.getpid()}.tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(prov, f, ensure_ascii=False, indent=1)
    os.replace(tmp, path)


def parse_extra_source(spec: str) -> Dict[str, str]:
    """--extra-source PATH:ROLE のパース。最初のコロンのみで分割 (ROLE 内コロン許容)。
    PATH/ROLE いずれか空は ValueError — 指定したのに記録されない silent drop は
    記録義務の穴になる (fails-closed、レビュー FC-6 裁定)。"""
    path, sep, role = spec.partition(":")
    if not sep or not path.strip() or not role.strip():
        raise ValueError(f"--extra-source は PATH:ROLE 形式 (どちらも非空) — got {spec!r}")
    return {"path": path.strip(), "role": role.strip()}


def _write_provenance_header(layout: CampaignLayout,
                             extra_sources: Sequence[Dict[str, str]] = ()) -> None:
    """run レベルの provenance ヘッダを焼く (drive_iteration 入口 = build 前。静的な
    記録欠落を 1 度のビルドも走らせず検出する、レビュー FC-1(a)/regression SF1 裁定)。

    ヘッダは毎回現在の定数で上書き merge (定数改訂の追随)、既存 entries は保持。
    information_sources は path キーの後勝ち union (既存 → 定数 → 今回の extra) —
    上書き置換だと過去 iteration の --extra-source 追記分が次の焼き直しで消える
    (07-12 (5) real 裁定。回避策「毎回再指定」を不要にする恒久修正)。"""
    if not INFORMATION_SOURCES:
        raise ValueError("INFORMATION_SOURCES が空 — E 段 provenance の情報源記録義務 "
                         "(D46 (a) ループ版) を満たせないため起動しない (fails-closed)")
    prov = _load_provenance(layout)
    merged: Dict[str, Dict[str, str]] = {}
    for src in (list(prov.get("information_sources", []))
                + list(INFORMATION_SOURCES) + list(extra_sources)):
        merged[src["path"]] = src
    prov.update({
        "axis": MARKER_ID,
        "pin": PIN,
        "axis_constants_module": "campaign.axis_trigger_gating",
        "information_sources": list(merged.values()),
        "liveness_binary": LIVENESS_BINARY,
        "gate_record": dict(GATE_RECORD),
        "firewall": ("E 段 coder/planner 入力へ流してよい偵察由来情報は軸の生死二値のみ。"
                     "偵察の具体勝ち点・要因部分集合・順位・シート診断数値は流さない "
                     "(D48 条件 7、正本 = axis_trigger_gating docstring)"),
    })
    prov.setdefault("entries", {})
    _write_provenance(layout, prov)


def _append_provenance_entry(layout: CampaignLayout, iteration: int,
                             entry: Dict) -> None:
    """iteration ごとの entry を merge 追記する (WAL の variant_id と proposal の出所を
    繋ぐ側チャネル — 偵察器 provenance の entries と同じ意図)。同 iteration キーは
    上書き = 再実行で冪等 (regression SF2 裁定)。呼び出しは `save_loop_state` より前 —
    provenance が書けない iteration は checkpoint を前進させず、再開時に WAL replay
    (重複解決) 経由で同 iteration が再記録される (レビュー FC-1(b)(c) 裁定)。"""
    prov = _load_provenance(layout)
    entries = prov.setdefault("entries", {})
    merged = dict(entries.get(str(iteration), {}))
    merged.update(entry)
    entries[str(iteration)] = merged
    _write_provenance(layout, prov)


# ==== wire materialize + diff 検疫 + auditor gate ==============================

def _site_admits_measurement(site: str) -> bool:
    """計測を許す既知 site の exact set。未知値は fail-closed。"""
    return site in {site_policy.OTHER, site_policy.PEGASUS_COMPUTE}


def _admit_env_contract(site: str) -> env_contract.ExecutionEnvironmentContract:
    """解決済み site を admission 後に閉じた対応から契約へ写像する。"""
    if not _site_admits_measurement(site):
        raise execution_guard.ExecutionGuardError(
            f"計測用 env bytes は site={site!r} では生成できない"
        )
    return _lookup(_SITE_ENV_TAGS[site])


def _campaign_cfg_for_site(
        cfg: CampaignConfig, site: str, *,
        _contract: Optional[env_contract.ExecutionEnvironmentContract] = None,
) -> CampaignConfig:
    """Resolved site contract を identity に束縛し、Pegasus marker も分離する。"""
    contract = _contract if _contract is not None else _admit_env_contract(site)
    if site == site_policy.PEGASUS_COMPUTE:
        cfg = replace(
            cfg,
            search_config={
                **cfg.search_config,
                _CAMPAIGN_ENV_KEY: _SITE_ENV_TAGS[site],
            },
        )
    return ident.bind_environment_contract(cfg, contract)


def _assert_resume_allowed(
    contract: env_contract.ExecutionEnvironmentContract,
    layout: CampaignLayout,
) -> None:
    if contract.isolation_policy.allow_resume:
        return
    existing = [
        path for path in (
            layout.lock_file, L.loop_state_path(layout), layout.wal_file,
            _provenance_path(layout),
        )
        if os.path.lexists(path)
    ]
    if existing:
        raise execution_guard.ExecutionGuardError(
            f"env {contract.env_tag} は allow_resume=False: 既存 campaign artifact を拒否: "
            + ", ".join(existing)
        )


def _receipt_provenance(
    *, site: str, contract: env_contract.ExecutionEnvironmentContract,
    receipt: Dict,
) -> Dict:
    encoded = json.dumps(
        receipt, sort_keys=True, separators=(",", ":"), ensure_ascii=False,
    ).encode("utf-8")
    import hashlib
    return {
        "site": site,
        "contract_sha256": contract.contract_sha256,
        "execution_receipt_sha256": hashlib.sha256(encoded).hexdigest(),
        "execution_receipt": receipt,
    }


def _record_diff_reject_admitted(layout: CampaignLayout, genome: Genome,
                                 predicate: str,
                                 res: DiffQuarantineResult,
                                 contract: env_contract.ExecutionEnvironmentContract,
                                 binding: TriggerGateBinding) -> str:
    return L.record_diff_reject(
        layout, genome, predicate, res, env_tag=contract.env_tag,
        trigger_gate_binding=binding,
    )


def _quarantine_and_audit(sub: str, coder: CoderProposalTriggerGating,
                          auditor: AuditorVerdict, genome: Genome,
                          layout: CampaignLayout, state: L.LoopState,
                          planner: L.PlannerProposal, write: bool,
                          contract: env_contract.ExecutionEnvironmentContract,
                          binding: TriggerGateBinding,
                          log=print) -> Optional[Dict]:
    """wire 正準化 → diff 検疫 → mandatory deny-only veto; affirmative security credit なし。

    ``diff_digest`` は attribution/provenance 専用。
    reject dict を返すか (build へ進まない)、None (通過)。

    **前提: 呼び出し元が既に `applied(TEMPLATE_PATCH)` 下にある。**"""
    ir = parse_wire(coder.wire)
    predicate = emit_predicate(ir)
    if check_syntax_contract(predicate):
        raise RuntimeError("canonical trigger predicate violates syntax contract")
    expected_predicate = _reflux_ir.emit_predicate(
        TriggerGateIR(binding.mask)
    )
    if predicate.strip() != expected_predicate.strip():
        raise RuntimeError("trigger predicate と binding が不一致")
    res, _base, _edited, working_diff = L.quarantine(
        sub, predicate, marker_id=MARKER_ID, source_rel=SOURCE_REL, write=write)
    combined = apply_mandatory_deny_only_veto(
        res,
        auditor,
        working_diff,
        diff_region=SOURCE_REL,
        template_diff_id=MARKER_ID,
    )
    if not combined.passed:
        v = _record_diff_reject_admitted(
            layout, genome, predicate, combined, contract, binding,
        )
        L.project_whiteboard(state, planner, "rejected")
        if combined is res:
            log(f"  diff 検疫 reject: {combined.subtype} — {combined.reason}")
        else:
            log(f"  auditor gate reject (verdict={auditor.verdict}): "
                f"{len(auditor.violations)} violations")
        return {
            "outcome": "rejected", "variant": v, "digest": combined.digest,
            "trigger_gate_binding_commitment": commitment(binding),
        }

    return None


# ==== campaign 設定 =============================================================

def _repo_root() -> str:
    here = os.path.dirname(os.path.abspath(__file__))
    return os.path.dirname(os.path.dirname(here))


def _template_patch_path(root: str) -> str:
    # axis_trigger_gating.TEMPLATE_PATCH は basename (patches/ を含まない)
    return os.path.join(root, "patches", TEMPLATE_PATCH)


def default_cfg(reflux: bool = True) -> CampaignConfig:
    """段 8a trigger-gating 自律ループの campaign 設定。

    spec_slug/search_tag/trial は本軸固有 (sort からの流用禁止 — campaign 出力の軸別
    分離、regression SF3 裁定)。verify は legacy+S2 (D43 必須修正の型を踏襲 — S2 の
    hot key 競合が abort 要因を実際に踏む構成でないと gate 述語の評価土台が崩れる)。"""
    cfg = CampaignConfig(
        spec_slug="p3-s8a-trigger-loop", search_tag="s8a-trigger-autonomous",
        spec_content=("P3 段 8a E 段: silo-backoff-trigger-gating (abort 要因別 backoff "
                      "gate) coder 自律ループ。planner が方向 (値なし) を提案し "
                      "coder が勝ち筋を見ずに固定 5-bit wire を返し、凍結 emitter の "
                      "正準述語だけを diff 検疫 + auditor 機械 gate に通して "
                      "build/verify(legacy+S2)/bench に進む。E 段へ流す偵察由来情報は"
                      "軸の生死二値のみ (D48 条件 7)"),
        ccbench_commit=PIN,
        search_config={"scale": "silo", "axis": MARKER_ID,
                       "reflux": "on" if reflux else "off",
                       "trigger_gate_binding_schema": TRIGGER_GATE_BINDING_SCHEMA,
                       "records": 100_000, "threads": 4,
                       SEARCH_CONFIG_VERIFY_KEY: VERIFY_LEGACY_PLUS_S2},
        trial="p3-s8a-trigger-loop")
    context = build_run_context(generator_id=GeneratorId.S8A_TRIGGER_SWEEP)
    return ident.bind_admission_policy(cfg, context.policy)


default_perf = L.default_perf   # 軸非依存 (配線規模、有意性を主張しない)


# ==== 1 iteration の機械 E2E ====================================================

# 重複提案の解決は backoff 版と単一実装 ([T-157]、経緯は p3_s4_loop_sort と同じ)。
_resolve_duplicate = L._resolve_duplicate


def _with_campaign_location(
        outcome: Dict, campaign_cfg: CampaignConfig,
        layout: CampaignLayout,
) -> Dict:
    outcome.update({
        "campaign_id": str(ident.campaign_id(campaign_cfg)),
        "layout_root": layout.root,
    })
    return outcome


def _assert_layout_matches_campaign(
        campaign_cfg: CampaignConfig, layout: CampaignLayout, *,
        require_authoritative_root: bool,
) -> None:
    campaign_id = str(ident.campaign_id(campaign_cfg))
    expected = exploration_campaign_layout(campaign_id).root
    matches = (
        layout.root == expected
        if require_authoritative_root
        else (
            os.path.basename(os.path.normpath(layout.root)) == campaign_id
            or layout.root == expected
        )
    )
    if not matches:
        raise ValueError(
            "layout 注入は最終 campaign-id 由来と一致必須 (WAL 分裂防止): "
            f"{layout.root} != {expected}"
        )


class WalBuildStartEvidenceMissingError(RuntimeError):
    """A WAL attempt lacks build-start evidence needed by the binding gate."""

    def __init__(self, *, variant: object, records: Dict[str, Dict],
                 failure_reason: str) -> None:
        self.variant = variant
        self.available_stages = tuple(sorted(records))
        self.stages = self.available_stages
        self.failure_reason = failure_reason
        self.abort_record_present = STAGE_ABORT in records
        abort_record = records.get(STAGE_ABORT)
        self.abort_details = {
            field: abort_record[field]
            for field in ("reason", "error", "build_attempt_id")
            if isinstance(abort_record, dict) and field in abort_record
        }
        self.abort_reason = self.abort_details.get("reason")
        self.abort_error = self.abort_details.get("error")
        self.abort_build_attempt_id = self.abort_details.get("build_attempt_id")
        abort_summary = "abort レコードなし"
        if self.abort_record_present:
            fields = ", ".join(
                f"{field}={value}"
                for field, value in self.abort_details.items()
            )
            abort_summary = f"abort={{ {fields} }}"
        super().__init__(
            "WAL build_start evidence missing: "
            f"failure_reason={failure_reason!r}, variant={variant!r}, "
            f"stages={list(self.available_stages)!r}, {abort_summary}"
        )


def _wal_binding_commitment(records: Dict[str, Dict], *, variant: object) -> str:
    """Return the commitment already validated against the raw WAL binding."""
    if STAGE_BUILD_START not in records:
        raise WalBuildStartEvidenceMissingError(
            variant=variant, records=records,
            failure_reason="build_start_missing",
        )
    start = records[STAGE_BUILD_START]
    if wal.TRIGGER_BINDING_COMMITMENT_KEY not in start:
        raise WalBuildStartEvidenceMissingError(
            variant=variant, records=records,
            failure_reason="binding_commitment_missing",
        )
    return start[wal.TRIGGER_BINDING_COMMITMENT_KEY]


def _wal_attempt_provenance(layout: CampaignLayout, variant: object) -> Dict:
    """Copy one provenance attempt identity from its authoritative WAL start."""
    if variant is None:
        return {"variant": None}
    if type(variant) is not str:
        raise RuntimeError("provenance variant が文字列でない")
    start = wal.records_by_stage(layout, variant).get(STAGE_BUILD_START)
    if type(start) is not dict:
        raise RuntimeError("provenance variant に対応する WAL build_start がない")
    attempt_id = start.get("build_attempt_id")
    binding_commitment = start.get(wal.TRIGGER_BINDING_COMMITMENT_KEY)
    if type(attempt_id) is not str or type(binding_commitment) is not str:
        raise RuntimeError("provenance 用 WAL build_start attempt が不正")
    return {
        "variant": variant,
        "build_attempt_id": attempt_id,
        wal.TRIGGER_BINDING_COMMITMENT_KEY: binding_commitment,
    }


def _run_one_iteration_resolved(
        campaign_cfg: CampaignConfig, perf,
        planner: L.PlannerProposal, coder: CoderProposalTriggerGating,
        auditor: AuditorVerdict, state: L.LoopState, sub: str, do_build: bool,
        layout: CampaignLayout, contract: env_contract.ExecutionEnvironmentContract,
        resolved_site: str, log=print, cache_root: str = "",
        dependency_prefix: str = "",
        build_context: Optional[BuildRunContext] = None,
) -> Dict:
    """実 site/contract/layout を公開 API で一度だけ解決した後の内部実装。"""
    from .patchharness import applied
    _assert_trigger_proposal_contract(planner, coder)
    if type(build_context) is not BuildRunContext:
        raise TypeError("build_context は build_run_context() 由来の exact value が必要")
    genome = Genome("silo", dict(_BASE))
    ir = parse_wire(coder.wire)
    binding = TriggerGateBinding(
        ir.mask,
        expected_predicate_sha256(ir.mask),
        new_nonce(),
        source=None,
    )
    layout.ensure()
    ident.ensure_resumable_attempts(
        campaign_cfg, layout, admission_policy=build_context.policy,
    )

    with applied(_template_patch_path(_repo_root()), PIN, sub):
        gate = _quarantine_and_audit(
            sub, coder, auditor, genome, layout, state, planner,
            write=do_build, contract=contract, binding=binding, log=log,
        )
        if gate is not None:
            return _with_campaign_location(gate, campaign_cfg, layout)
        if not do_build:
            return _with_campaign_location(
                {
                    "outcome": "dry-pass", "variant": None,
                    "trigger_gate_binding_commitment": commitment(binding),
                }, campaign_cfg, layout,
            )
        campaign_options = {}
        if resolved_site == site_policy.PEGASUS_COMPUTE:
            campaign_options["env_contract"] = contract
            if dependency_prefix:
                campaign_options["dependency_prefix"] = dependency_prefix
        summary = run_campaign(
            campaign_cfg, [genome], perf, contract.env_tag, contract.clocks_per_us,
            numactl=list(contract.numactl), log=log, ccbench_dir=sub,
            cache_root=cache_root,
            authorization_contract=env_contract.authorize(contract.env_tag),
            build_context=build_context,
            declared_use_class=DECLARED_USE_CLASS,
            trigger_gate_binding=binding,
            **campaign_options,
        )
    execution_receipt = getattr(summary, "execution_receipt", None)
    if execution_receipt is not None:
        _append_provenance_entry(
            layout, state.iteration,
            _receipt_provenance(
                site=resolved_site, contract=contract,
                receipt=execution_receipt,
            ),
        )
    v = next((r.variant for r in summary.results), None)
    if v is None and summary.skipped > 0:
        duplicate = _resolve_duplicate(layout, planner, state, summary, log=log)
        duplicate.get("records", {}).pop(TRIGGER_GATE_BINDING_WAL_STAGE, None)
        duplicate["trigger_gate_binding_commitment"] = _wal_binding_commitment(
            duplicate["records"], variant=duplicate["variant"],
        )
        return _with_campaign_location(duplicate, campaign_cfg, layout)
    recs = wal.records_by_stage(layout, v) if v else {}
    recs.pop(TRIGGER_GATE_BINDING_WAL_STAGE, None)
    binding_commitment = (
        _wal_binding_commitment(recs, variant=v)
        if v is not None else commitment(binding)
    )
    r = summary.results[0] if summary.results else None
    if r and r.certified and not r.aborted:
        L.project_whiteboard(state, planner, "success", delta_pct=None)
        return _with_campaign_location({
            "outcome": "certified", "variant": v, "fitness_tps": r.fitness_tps,
            "verdict": r.verdict, "records": recs,
            "trigger_gate_binding_commitment": binding_commitment,
        }, campaign_cfg, layout)
    L.project_whiteboard(state, planner, "fail")
    return _with_campaign_location({
        "outcome": "aborted", "variant": v,
        "verdict": (r.verdict if r else ""), "records": recs,
        "trigger_gate_binding_commitment": binding_commitment,
    }, campaign_cfg, layout)


def run_one_iteration(cfg: CampaignConfig, perf, planner: L.PlannerProposal,
                      coder: CoderProposalTriggerGating, auditor: AuditorVerdict,
                      state: L.LoopState, sub: str, do_build: bool,
                      layout: Optional[CampaignLayout] = None, log=print,
                      cache_root: str = "", *,
                      dependency_prefix: str = "",
                      build_context: Optional[BuildRunContext] = None) -> Dict:
    """1 iteration の機械部分 (sort 版と同型の構造。genome は _BASE をそのまま焼く —
    FLAG=1 は軸定数モジュールの _BASE に含まれる)。

    provenance は書かない (機械部)。実 LLM 駆動と fixture main の funnel は
    `drive_iteration` で、そちらが記録義務を担う。"""
    _assert_trigger_proposal_contract(planner, coder)
    resolved_site = _current_site()
    contract = _admit_env_contract(resolved_site)
    campaign_cfg = _campaign_cfg_for_site(
        cfg, resolved_site, _contract=contract,
    )
    if build_context is None and not do_build:
        build_context = build_run_context(generator_id=GeneratorId.S8A_TRIGGER_SWEEP)
    if type(build_context) is not BuildRunContext:
        raise TypeError("build_context は build_run_context() 由来の exact value が必要")
    campaign_cfg = ident.bind_admission_policy(campaign_cfg, build_context.policy)
    if layout is None:
        layout = exploration_campaign_layout(str(ident.campaign_id(campaign_cfg)))
    else:
        _assert_layout_matches_campaign(
            campaign_cfg, layout, require_authoritative_root=do_build,
        )
    _assert_resume_allowed(contract, layout)
    return _run_one_iteration_resolved(
        campaign_cfg, perf, planner, coder, auditor, state, sub, do_build,
        layout, contract, resolved_site, log=log, cache_root=cache_root,
        dependency_prefix=dependency_prefix,
        build_context=build_context,
    )


# ==== 駆動口 (実 planner/coder/auditor proposal を受けて 1 iteration を継続) ======

def load_proposal_file(path: str) -> Tuple[L.PlannerProposal, CoderProposalTriggerGating,
                                           AuditorVerdict, Optional[bool]]:
    """メインセッションが spawn した planner/coder/auditor の構造化出力を JSON から読む。

    schema は sort 版と同型 (coder に value フィールドが無い点も同じ)::

        {"planner": {axis, direction, magnitude, justification?, uncertainty?},
         "coder":   {axis, wire, justification?, confidence?},
         "auditor": {verdict, diff_digest, violations?, nits?, proposed_tests?, uncertainty?},
         "prior_critic_reverse": true|false|null}

    トップレベルキーは `d[...]` で読む (欠落 = KeyError で fails-closed)。"""
    with open(path, encoding="utf-8") as f:
        d = json.load(f)
    assert_closed_proposal_schema(
        d, require_auditor=True, require_coder_value=False,
        coder_contract=CODER_CONTRACT_TRIGGER_WIRE,
    )
    p, c, a = d["planner"], d["coder"], d["auditor"]
    planner = L.PlannerProposal(
        axis=p["axis"], direction=p["direction"], magnitude=p["magnitude"],
        justification=p.get("justification", ""), uncertainty=p.get("uncertainty", ""))
    coder = CoderProposalTriggerGating(
        axis=c["axis"], wire=c["wire"],
        justification=c.get("justification", ""), confidence=c.get("confidence", "medium"))
    auditor = parse_auditor_dict(a)   # verdict 未知・digest 空/非文字列 → AuditorGateFailure
    prior = d.get("prior_critic_reverse")
    if prior is not None and not isinstance(prior, bool):
        raise ValueError(f"prior_critic_reverse は null か bool のみ (got {type(prior).__name__}: "
                         f"{prior!r}) — 非 bool は停止フィードバックを fail-open させる (規律2)")
    assert_no_ability_probe_material(d)
    _assert_trigger_proposal_contract(planner, coder)
    return planner, coder, auditor, prior


def drive_iteration(cfg: CampaignConfig, perf, planner: L.PlannerProposal,
                    coder: CoderProposalTriggerGating, auditor: AuditorVerdict,
                    prior_critic_reverse: Optional[bool], sub: str, do_build: bool,
                    layout: Optional[CampaignLayout] = None, log=print,
                    cache_root: str = "", proposal_path: str = "",
                    extra_sources: Sequence[Dict[str, str]] = (), *,
                    dependency_prefix: str = "",
                    build_context: Optional[BuildRunContext] = None,
                    _resolved_site: Optional[str] = None,
                    _contract: Optional[
                        env_contract.ExecutionEnvironmentContract
                    ] = None) -> Dict:
    """段 8a trigger-gating の 1 iteration をメインセッション駆動で回す (sort 版と
    同型の骨格 + provenance 配線)。

    provenance の書き込み順序 (レビュー FC-1 裁定):
      1. ヘッダ = 本関数入口 (build 前)。情報源の静的欠落は 1 度のビルドも走らせず停止
      2. entry = run_one_iteration の後・`save_loop_state` の**前**。entry が書けない
         iteration は checkpoint が前進しない → 再開時に WAL replay (重複解決) 経由で
         同 iteration が再記録される (duplicate 経路も entry を書く)
    """
    _assert_trigger_proposal_contract(planner, coder)
    if _resolved_site is None and _contract is None:
        resolved_site = _current_site()
        contract = _admit_env_contract(resolved_site)
    elif _resolved_site is None or _contract is None:
        raise TypeError("resolved site と contract は同時に渡す必要がある")
    else:
        resolved_site = _resolved_site
        contract = _contract
        if not _site_admits_measurement(resolved_site):
            raise execution_guard.ExecutionGuardError(
                f"計測用 env bytes は site={resolved_site!r} では生成できない"
            )
        if contract.env_tag != _SITE_ENV_TAGS[resolved_site]:
            raise execution_guard.ExecutionGuardError(
                "解決済み site と environment contract の env_tag が一致しない"
            )
    campaign_cfg = _campaign_cfg_for_site(
        cfg, resolved_site, _contract=contract,
    )
    if build_context is None and not do_build:
        build_context = build_run_context(generator_id=GeneratorId.S8A_TRIGGER_SWEEP)
    if type(build_context) is not BuildRunContext:
        raise TypeError("build_context は build_run_context() 由来の exact value が必要")
    campaign_cfg = ident.bind_admission_policy(campaign_cfg, build_context.policy)
    if layout is None:
        layout = exploration_campaign_layout(str(ident.campaign_id(campaign_cfg)))
    else:
        _assert_layout_matches_campaign(
            campaign_cfg, layout, require_authoritative_root=do_build,
        )
    _assert_resume_allowed(contract, layout)
    layout.ensure()
    ident.ensure_resumable_attempts(
        campaign_cfg, layout, admission_policy=build_context.policy,
    )
    _write_provenance_header(layout, extra_sources=extra_sources)
    state = L.load_loop_state(layout)
    if state is None:
        state = L.LoopState(start_wall=time.time())
    L._fold_critic_reverse(state, prior_critic_reverse)

    pre = L.check_stop(state)
    if pre.stop:
        L.save_loop_state(layout, state)
        log(f"  入口停止 (iteration 消費せず): {pre.reason}")
        return _with_campaign_location({
            "outcome": "stopped-before", "variant": None,
            "stop_reason": pre.reason, "iteration": state.iteration, "ran": False,
        }, campaign_cfg, layout)

    state.iteration += 1
    out = _run_one_iteration_resolved(
        campaign_cfg, perf, planner, coder, auditor, state, sub, do_build,
        layout, contract, resolved_site, log=log, cache_root=cache_root,
        dependency_prefix=dependency_prefix,
        build_context=build_context,
    )
    provenance_entry = {
        "proposal_path": proposal_path,
        "auditor_diff_digest": auditor.diff_digest,
        "outcome": out["outcome"],
        "trigger_gate_binding_commitment": out.get(
            "trigger_gate_binding_commitment"
        ),
    }
    provenance_entry.update(_wal_attempt_provenance(layout, out.get("variant")))
    _append_provenance_entry(layout, state.iteration, provenance_entry)
    L.save_loop_state(layout, state)

    if do_build and out["outcome"] != "dry-pass":
        critic_view = L.require_admitted_campaign(
            layout.root,
            purpose=L.CampaignReadPurpose.CERTIFIED_ACCEPTANCE,
        )
        digest_txt = L.make_critic_digest(
            critic_view,
            tag=CRITIC_TAG,
            reflux=(cfg.search_config.get("reflux") == "on"),
            identity_projection=L.make_critic_identity_projection(critic_view),
        )
        with open(os.path.join(layout.root, DIGEST_BASENAME), "w", encoding="utf-8") as f:
            f.write(digest_txt)
        out["critic_digest_generated"] = True
    else:
        # No-build is a wiring preview even when a machine/auditor gate rejects
        # the candidate.  Keep its WAL/provenance, but do not invoke an
        # admitted-campaign consumer.
        out["critic_digest_generated"] = False

    post = L.check_stop(state)
    out.update({"stop_reason": post.reason, "iteration": state.iteration, "ran": True})
    return out


# ==== CLI =======================================================================

def _preview_wire(wire: str, sub: str, root: str) -> Dict:
    """auditor へ渡す実 diff を得る (メインセッションが auditor spawn 前に呼ぶ。
    sort 版と同型)。"""
    from .patchharness import applied, assert_pinned_clean
    predicate = emit_predicate(parse_wire(wire))
    assert_pinned_clean(sub, PIN)
    with applied(_template_patch_path(root), PIN, sub):
        res, _base, _edited, working_diff = L.quarantine(
            sub, predicate, marker_id=MARKER_ID, source_rel=SOURCE_REL, write=False)
    return {"passed": res.passed, "working_diff": working_diff,
           "diff_digest": compute_diff_digest(working_diff),
           "subtype": (res.subtype.value if res.subtype else None), "reason": res.reason}


def main(argv: Optional[List[str]] = None) -> int:
    """fixture proposal で 1 iteration の機械 E2E を実走する (配線実証)。

    実 LLM (planner-v4/coder-v4-autonomous-trigger-gating/auditor/critic) はメイン
    セッションが spawn する (F 段、別セッション)。fixture 経路も `drive_iteration` の
    provenance funnel を通る。`--no-build` の dry-pass は配線確認だけを返し、admission
    必須の critic digest は生成しない。"""
    ap = argparse.ArgumentParser(
        description="P3 段 8a trigger-gating coder 自律ループ (機械 E2E)")
    ap.add_argument("--no-build", action="store_true",
                    help="build/verify/bench を省き wire→正準述語→検疫→auditor gate の配線のみ確認")
    add_registered_coder_build_authority_argument(
        ap,
        coder_entrypoint_site=(
            "orchestrator.campaign.p3_s4_loop_trigger_gating.main"
        ),
    )
    ap.add_argument("--reflux", choices=["on", "off"], default="on",
                    help="critic 還流 on/off (LLM ablation の対照アーム)")
    ap.add_argument("--run-iteration", metavar="PROPOSAL.json",
                    help="実 planner/coder/auditor proposal (JSON) を受けて checkpoint 継続で "
                         "1 iteration を回す (メインセッションが毎 iteration これを呼ぶ)")
    ap.add_argument("--preview-wire", metavar="WIRE",
                    help="auditor spawn 前の配線: 5-bit wire から working_diff + "
                         "diff_digest を JSON で標準出力へ (build/single-tenant 不要)")
    ap.add_argument("--extra-source", action="append", default=[], metavar="PATH:ROLE",
                    help="provenance の information_sources へ追記する動的情報源 (F 段"
                         "セッションが新たに読んだ文書。PATH:ROLE 形式、複数回指定可。"
                         "malformed は起動拒否)")
    ap.add_argument("--no-isolate-worktree", action="store_true",
                    help="worktree 隔離 (既定 ON — PIN が backoff driver と異なるため共有 tree "
                         "衝突を避ける) を無効化 (デバッグ用)")
    a = ap.parse_args(argv if argv is not None else sys.argv[1:])

    extra_sources = [parse_extra_source(s) for s in a.extra_source]

    root = _repo_root()
    fixed_sub = os.path.join(root, "external", "ccbench")

    if a.preview_wire:
        out = _preview_wire(a.preview_wire, fixed_sub, root)
        print(json.dumps(out, ensure_ascii=False, indent=2))
        return 0 if out["passed"] else 1

    if not a.no_build and a.coder_build_authority is None:
        raise BuildAdmissionError("--allow-coder-derived-build の明示 opt-in が必要")

    build_context = build_run_context(
        generator_id=GeneratorId.S8A_TRIGGER_SWEEP,
        coder_authority=None if a.no_build else a.coder_build_authority,
    )

    from . import patchharness
    from .p2_2 import _assert_single_tenant
    if not a.no_build:
        _assert_single_tenant()
    patchharness.assert_pinned_clean(fixed_sub, PIN)

    cfg = default_cfg(reflux=(a.reflux == "on"))
    cfg = ident.bind_admission_policy(cfg, build_context.policy)
    perf = default_perf()

    isolate = not a.no_isolate_worktree
    if isolate:
        wt_cm = patchharness.checkout(PIN, base_dir=fixed_sub)
        cache_root = os.path.join(fixed_sub, "build-variants")
    else:
        wt_cm = contextlib.nullcontext(fixed_sub)
        cache_root = ""

    if a.run_iteration:
        planner, coder, auditor, prior_rev = load_proposal_file(a.run_iteration)
        print(f"=== 段8a trigger-gating iteration (proposal={a.run_iteration}, "
              f"reflux={a.reflux}, build={not a.no_build}, prior_critic_reverse={prior_rev}, "
              f"isolate_worktree={isolate}) ===")
        with wt_cm as sub:
            out = drive_iteration(cfg, perf, planner, coder, auditor, prior_rev, sub,
                                  do_build=not a.no_build, cache_root=cache_root,
                                  proposal_path=os.path.abspath(a.run_iteration),
                                  extra_sources=extra_sources,
                                  build_context=build_context)
        expected_layout = exploration_campaign_layout(out["campaign_id"])
        layout = CampaignLayout(out["layout_root"])
        if layout.root != expected_layout.root:
            raise ValueError("返却された campaign_id と exploration layout_root が一致しない")
        print(f"  ran={out['ran']} outcome={out['outcome']} "
              f"variant={out.get('variant')} iteration={out['iteration']}")
        print(f"  停止判定: {out['stop_reason']}")
        print(f"  checkpoint: {L.loop_state_path(layout)}")
        print(f"  digest: {os.path.join(layout.root, DIGEST_BASENAME)}")
        print(f"  provenance: {_provenance_path(layout)}")
        ok = (out["stop_reason"] in ("continue", "converged", "reverse-exhausted",
                                     "budget-iterations", "budget-walltime")
              and os.path.exists(L.loop_state_path(layout))
              and os.path.exists(_provenance_path(layout)))
        return 0 if ok else 1

    # fixture proposal: 11111 は ident_all であり真の stock ではない。
    planner = L.PlannerProposal(axis=MARKER_ID, direction="explore_both", magnitude="small",
                                justification="fixture (機械 E2E 用)")
    fixture_wire = "11111"
    coder = CoderProposalTriggerGating(axis=MARKER_ID, wire=fixture_wire,
                                       justification="fixture", confidence="low")

    print(f"=== 段8a trigger-gating loop 1 iteration (機械 E2E, reflux={a.reflux}, "
          f"build={not a.no_build}, isolate_worktree={isolate}) ===")
    with wt_cm as sub:
        from .patchharness import applied
        with applied(_template_patch_path(root), PIN, sub):
            fixture_predicate = emit_predicate(parse_wire(fixture_wire))
            res, _b, _e, working_diff = L.quarantine(
                sub, fixture_predicate, marker_id=MARKER_ID,
                source_rel=SOURCE_REL, write=False)
        auditor = AuditorVerdict(verdict="pass", diff_digest=compute_diff_digest(working_diff),
                                 uncertainty="fixture (機械 E2E 用、実 auditor 未使用)")
        out = drive_iteration(
            cfg, perf, planner, coder, auditor, None, sub,
            do_build=not a.no_build, cache_root=cache_root,
            proposal_path="fixture-main", build_context=build_context,
        )
    print(f"  outcome={out['outcome']} variant={out.get('variant')}")

    expected_layout = exploration_campaign_layout(out["campaign_id"])
    layout = CampaignLayout(out["layout_root"])
    if layout.root != expected_layout.root:
        raise ValueError("返却された campaign_id と exploration layout_root が一致しない")
    out_path = os.path.join(layout.root, DIGEST_BASENAME)
    state = L.load_loop_state(layout)
    if state is None:
        raise RuntimeError("fixture provenance funnel が checkpoint を生成しなかった")
    stop = L.check_stop(state)
    n_wal = len(list(wal.read_records(layout)))
    checks = {
        f"iteration(={state.iteration}) が WAL レコード数(={n_wal})と独立 (WAL 由来でない)":
            state.iteration == 1 and n_wal != state.iteration,
        "provenance funnel を通過": os.path.exists(_provenance_path(layout)),
        "停止判定が機械的に返る": stop.reason in (
            "continue", "converged", "reverse-exhausted",
            "budget-iterations", "budget-walltime"),
    }
    if out["outcome"] == "dry-pass":
        checks["dry-pass は critic digest を生成しない"] = not os.path.exists(out_path)
    else:
        checks["admitted outcome は critic digest を生成"] = os.path.exists(out_path)
    if out["outcome"] != "dry-pass":
        checks["whiteboard に 1 行射影 (機序なし)"] = len(state.whiteboard) == 1
        checks["whiteboard entry が方向/結果のみ (機序フィールド無し)"] = (
            len(state.whiteboard) == 1
            and set(vars(state.whiteboard[0])) == {
                "iteration", "direction", "magnitude", "result", "delta_pct"})
    if out["outcome"] == "certified":
        checks["certified で fitness_tps あり"] = out.get("fitness_tps") is not None

    print("\n=== 判定 (WAL/状態 機械確認) ===")
    ok = all(checks.values())
    for name, passed in checks.items():
        print(f"  [{'PASS' if passed else 'FAIL'}] {name}")
    print(f"\ncampaign dir: {layout.root}")
    print(f"停止判定: stop={stop.stop} reason={stop.reason}")
    print(f"\n段8a trigger-gating loop 1 iteration 判定: {'PASS' if ok else 'FAIL'}")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
