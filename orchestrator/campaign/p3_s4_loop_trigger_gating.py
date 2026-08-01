# -*- coding: utf-8 -*-
"""P3 段 8a E 段 driver — silo-backoff-trigger-gating 軸の coder 自律ループ機械部分。

`p3_s4_loop_sort.py` (D43) を型とする兄弟 driver (コード片軸 2 軸目)。設計は 3 レンズ
敵対レビュー (リーク制御/fails-closed/regression、2026-07-12) の裁定反映済み — 裁定の
正本は D51 + insight `output/insights/2026-07-12_s8a-stage-e-design-review.md`。

sort 版との構造差 (新テンプレの形):
  - **軸定数は全て `campaign.axis_trigger_gating` から import する** (自前定義しない)。
    軸定数ブロックが C 段成果物として先に在り、D 偵察器 (`s8a_trigger_sweep.py`) と
    本 driver の両方がそこから import する — sort 軸の歴史的経緯 (偵察器が E 段 driver を
    import) の逆転が完成する (D48 必須条件 5、axis-onboarding §1 脚注)。
  - auditor 機械 gate の軸非依存部品は `campaign.auditor_gate` を使う (共有昇格)。
  - hole は骨格の述語代入 1 行 (`izanagi_gate_pass = <述語>;`、D49 決定 2)。coder 出力は
    `CoderProposalTriggerGating` (value なし — コード片軸)。
  - **構文契約の禁止識別子 grep** (`SYNTAX_CONTRACT_FORBIDDEN`) を pre-build 検査に追加。
    執行の役割分担 (レビュー FC-8 裁定): リスト上の識別子は本 grep が機械執行する
    hard gate (fails-closed、subtype="syntax-contract")。auditor 目視はその超集合
    (リストに載らない意味的違反 — 恒真述語・fairness 誘導等) を執行し、**grep 緑は
    auditor 目視義務を免除しない** (runbook §2)。grep は識別子境界 (\\b 前置) 付き
    部分一致 — コメント内等の過検出は安全側 (reject) として許容する。
  - **provenance 情報源記録の受け皿** (D46 (a) のループ版、07-11 監査 L4-1 の宿主確定):
    `<campaign root>/reports/p3_s8a_trigger_loop_provenance.json`。詳細は
    `_write_provenance_header` / `_append_provenance_entry` の docstring。記録は
    `drive_iteration` (= `--run-iteration` の実経路) が自動で行い CLI で省略できない —
    「宣言止まり」(謳うだけで発火しない義務) にしない。fixture main 直呼び経路
    (機械 E2E) は偵察 insight 非依拠の配線確認であり provenance 対象外 (レビュー FC-7
    裁定。F 段の実 LLM 駆動は必ず `--run-iteration` → `drive_iteration` を通る)。

偵察 firewall (D48 条件 7): 本 driver・coder 定義・runbook が E 段入力
(leakproof_context / planner direction / whiteboard) に流してよい偵察由来情報は軸の
生死二値 (`LIVENESS_BINARY`) のみ。偵察の具体勝ち点・要因部分集合・順位・シートの診断
数値は流さない (正本 = `axis_trigger_gating` docstring)。

planner-v4 は無改変で再利用 (`L.PlannerProposal`)。direction/magnitude は抽象シグナル
のまま (機序含みの解釈をメインセッションが注入しない、D43)。PIN は sort driver と同一
(d706650) だが backoff driver (028f34d literal) と異なるため worktree 隔離は既定 ON を
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

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from campaign import env_contract, execution_guard, ident, site_policy, wal  # noqa: E402
from campaign import p3_s4_loop as L                              # noqa: E402
from campaign.auditor_gate import (AuditorGateFailure,            # noqa: E402
                                   AuditorVerdict, assert_digest_matches,
                                   auditor_reject_result, parse_auditor_dict,
                                   compute_diff_digest)
from campaign.axis_trigger_gating import (_BASE, MARKER_ID, PIN,  # noqa: E402
                                          SOURCE_REL, SYNTAX_CONTRACT_FORBIDDEN,
                                          TEMPLATE_PATCH)
from campaign.diff_quarantine import DiffQuarantineResult          # noqa: E402
from campaign.layout import (CampaignLayout,                       # noqa: E402
                             exploration_campaign_layout)
from campaign.loop import run_campaign                             # noqa: E402
from campaign.model import CampaignConfig, Genome                  # noqa: E402
from campaign.pipeline import SEARCH_CONFIG_VERIFY_KEY             # noqa: E402
from campaign.pipeline import VERIFY_LEGACY_PLUS_S2                # noqa: E402
from campaign.projection_guard import (                            # noqa: E402
    assert_closed_proposal_schema,
    assert_no_ability_probe_material,
)
from critic.digest import DIFF_QUARANTINE_REASON                   # noqa: E402

# ---- campaign 定数 (軸定数は axis_trigger_gating が正本 — ここは環境・計測の定数のみ) ----
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


# ==== 提案の型 (LLM 出力) =======================================================

@dataclass
class CoderProposalTriggerGating:
    """coder-v4-autonomous-trigger-gating の出力 (gate 述語の代入式 1 行。value
    フィールドは無い — コード片軸、D48/D49)。`strategy_summary` 相当の一言要約も
    持たせない (具体戦略の例示リーク、D43 の反省を継承)。"""
    axis: str
    implementation: str               # hole (述語代入 1 行) を置換する文字列
    justification: str = ""
    confidence: str = "medium"


# ==== 構文契約の禁止識別子 grep (D48 決定 2 の機械執行部分) ======================

_FORBIDDEN_RE = re.compile("|".join(r"\b" + re.escape(t)
                                    for t in SYNTAX_CONTRACT_FORBIDDEN))


def check_syntax_contract(implementation: str) -> List[str]:
    """implementation 中の禁止識別子 (SYNTAX_CONTRACT_FORBIDDEN) を列挙する。

    空リスト = 違反なし。マッチは識別子境界 (\\b) 前置の部分一致 — コメント内や
    合成語 (write_set_foo) への過検出は安全側 (reject 方向) として許容する
    (レビュー FC-N1 裁定)。"""
    return sorted({m.group(0) for m in _FORBIDDEN_RE.finditer(implementation)})


def _syntax_contract_reject_result(matched: Sequence[str]) -> DiffQuarantineResult:
    """禁止識別子 reject を diff-quarantine 経路に相乗りさせる合成結果。

    evidence にはマッチした識別子名**のみ**を載せ、coder の gate 式本文は載せない —
    reject は render_rejections 経由で critic に還流するため、式本文 (coder の要因
    部分集合の推測) を運ばない (リークレンズ nit 裁定)。"""
    reason = (f"構文契約違反: 禁止識別子 {', '.join(matched)} を参照 — 述語が読めるのは"
              f"要因 enum とコンパイル時定数のみ (D48 決定 2)")
    return DiffQuarantineResult(
        passed=False, reason=reason,
        digest={"rejection_type": DIFF_QUARANTINE_REASON, "subtype": "syntax-contract",
                "reason": reason, "diff_region": SOURCE_REL, "template_diff_id": MARKER_ID,
                "evidence": f"forbidden={list(matched)}"})


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


# ==== diff 検疫 + 構文契約 grep + auditor gate ==================================

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


def _campaign_cfg_for_site(cfg: CampaignConfig, site: str) -> CampaignConfig:
    """Pegasus contract だけ campaign identity を別 namespace に分ける。"""
    if site != site_policy.PEGASUS_COMPUTE:
        return cfg
    return replace(
        cfg,
        search_config={**cfg.search_config, _CAMPAIGN_ENV_KEY: _SITE_ENV_TAGS[site]},
    )


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
                                 implementation: str,
                                 res: DiffQuarantineResult,
                                 contract: env_contract.ExecutionEnvironmentContract) -> str:
    return L.record_diff_reject(
        layout, genome, implementation, res, env_tag=contract.env_tag
    )


def _quarantine_and_audit(sub: str, coder: CoderProposalTriggerGating,
                          auditor: AuditorVerdict, genome: Genome,
                          layout: CampaignLayout, state: L.LoopState,
                          planner: L.PlannerProposal, write: bool,
                          contract: env_contract.ExecutionEnvironmentContract,
                          log=print) -> Optional[Dict]:
    """hole 挿入 → diff 検疫 → 構文契約 grep → auditor gate (digest 照合 + verdict)。
    reject dict を返すか (build へ進まない)、None (通過)。

    **前提: 呼び出し元が既に `applied(TEMPLATE_PATCH)` 下にある。**"""
    res, _base, _edited, working_diff = L.quarantine(
        sub, coder.implementation, marker_id=MARKER_ID, source_rel=SOURCE_REL, write=write)
    if not res.passed:
        v = _record_diff_reject_admitted(
            layout, genome, coder.implementation, res, contract,
        )
        L.project_whiteboard(state, planner, "rejected")
        log(f"  diff 検疫 reject: {res.subtype} — {res.reason}")
        return {"outcome": "rejected", "variant": v, "digest": res.digest}

    matched = check_syntax_contract(coder.implementation)
    if matched:
        sres = _syntax_contract_reject_result(matched)
        v = _record_diff_reject_admitted(
            layout, genome, coder.implementation, sres, contract,
        )
        L.project_whiteboard(state, planner, "rejected")
        log(f"  構文契約 reject: 禁止識別子 {matched}")
        return {"outcome": "rejected", "variant": v, "digest": sres.digest}

    assert_digest_matches(auditor, working_diff)   # 不一致 → AuditorGateFailure (共有照合コア)

    if auditor.verdict != "pass":
        subtype = "auditor-uncertain" if auditor.verdict == "uncertain" else "auditor-violation"
        ares = auditor_reject_result(subtype, auditor,
                                     diff_region=SOURCE_REL, template_diff_id=MARKER_ID)
        v = _record_diff_reject_admitted(
            layout, genome, coder.implementation, ares, contract,
        )
        L.project_whiteboard(state, planner, "rejected")
        log(f"  auditor gate reject (verdict={auditor.verdict}): "
            f"{len(auditor.violations)} violations")
        return {"outcome": "rejected", "variant": v, "digest": ares.digest}

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
    return CampaignConfig(
        spec_slug="p3-s8a-trigger-loop", search_tag="s8a-trigger-autonomous",
        spec_content=("P3 段 8a E 段: silo-backoff-trigger-gating (abort 要因別 backoff "
                      "gate 述語) coder 自律ループ。planner が方向 (値なし) を提案し "
                      "coder が勝ち筋を見ずに gate 述語 (代入式 1 行) を合成、diff 検疫 + "
                      "構文契約 grep + auditor 機械 gate を通した hole 変異のみ "
                      "build/verify(legacy+S2)/bench に進む。E 段へ流す偵察由来情報は"
                      "軸の生死二値のみ (D48 条件 7)"),
        ccbench_commit=PIN,
        search_config={"scale": "silo", "axis": MARKER_ID,
                       "reflux": "on" if reflux else "off",
                       "records": 100_000, "threads": 4,
                       SEARCH_CONFIG_VERIFY_KEY: VERIFY_LEGACY_PLUS_S2},
        trial="p3-s8a-trigger-loop")


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


def _run_one_iteration_resolved(
        campaign_cfg: CampaignConfig, perf,
        planner: L.PlannerProposal, coder: CoderProposalTriggerGating,
        auditor: AuditorVerdict, state: L.LoopState, sub: str, do_build: bool,
        layout: CampaignLayout, contract: env_contract.ExecutionEnvironmentContract,
        resolved_site: str, log=print, cache_root: str = "",
        dependency_prefix: str = "",
) -> Dict:
    """実 site/contract/layout を公開 API で一度だけ解決した後の内部実装。"""
    from campaign.patchharness import applied
    genome = Genome("silo", dict(_BASE))
    layout.ensure()
    ident.ensure_campaign_identity(campaign_cfg, layout)

    with applied(_template_patch_path(_repo_root()), PIN, sub):
        gate = _quarantine_and_audit(
            sub, coder, auditor, genome, layout, state, planner,
            write=do_build, contract=contract, log=log,
        )
        if gate is not None:
            return _with_campaign_location(gate, campaign_cfg, layout)
        if not do_build:
            return _with_campaign_location(
                {"outcome": "dry-pass", "variant": None}, campaign_cfg, layout,
            )
        campaign_options = {}
        if resolved_site == site_policy.PEGASUS_COMPUTE:
            campaign_options["env_contract"] = contract
            if dependency_prefix:
                campaign_options["dependency_prefix"] = dependency_prefix
        summary = run_campaign(
            campaign_cfg, [genome], perf, contract.env_tag, contract.clocks_per_us,
            numactl=list(contract.numactl), log=log, ccbench_dir=sub,
            cache_root=cache_root, campaign_namespace="exploration",
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
        return _with_campaign_location(
            _resolve_duplicate(layout, planner, state, summary, log=log),
            campaign_cfg, layout,
        )
    recs = wal.records_by_stage(layout, v) if v else {}
    r = summary.results[0] if summary.results else None
    if r and r.certified and not r.aborted:
        L.project_whiteboard(state, planner, "success", delta_pct=None)
        return _with_campaign_location({
            "outcome": "certified", "variant": v, "fitness_tps": r.fitness_tps,
            "verdict": r.verdict, "records": recs,
        }, campaign_cfg, layout)
    L.project_whiteboard(state, planner, "fail")
    return _with_campaign_location({
        "outcome": "aborted", "variant": v,
        "verdict": (r.verdict if r else ""), "records": recs,
    }, campaign_cfg, layout)


def run_one_iteration(cfg: CampaignConfig, perf, planner: L.PlannerProposal,
                      coder: CoderProposalTriggerGating, auditor: AuditorVerdict,
                      state: L.LoopState, sub: str, do_build: bool,
                      layout: Optional[CampaignLayout] = None, log=print,
                      cache_root: str = "", *,
                      dependency_prefix: str = "") -> Dict:
    """1 iteration の機械部分 (sort 版と同型の構造。genome は _BASE をそのまま焼く —
    FLAG=1 は軸定数モジュールの _BASE に含まれる)。

    provenance は書かない (機械部)。実 LLM 駆動の funnel は `drive_iteration` で、
    そちらが記録義務を担う (fixture main 直呼びは配線確認専用 = 偵察 insight 非依拠、
    レビュー FC-7 裁定)。"""
    resolved_site = _current_site()
    contract = _admit_env_contract(resolved_site)
    campaign_cfg = _campaign_cfg_for_site(cfg, resolved_site)
    if layout is None:
        layout = exploration_campaign_layout(str(ident.campaign_id(campaign_cfg)))
    elif do_build and layout.root != exploration_campaign_layout(
            str(ident.campaign_id(campaign_cfg))).root:
        raise ValueError(f"build 経路の layout 注入は cfg 由来と一致必須 (WAL 分裂防止): "
                         f"{layout.root} != cfg 由来")
    _assert_resume_allowed(contract, layout)
    return _run_one_iteration_resolved(
        campaign_cfg, perf, planner, coder, auditor, state, sub, do_build,
        layout, contract, resolved_site, log=log, cache_root=cache_root,
        dependency_prefix=dependency_prefix,
    )


# ==== 駆動口 (実 planner/coder/auditor proposal を受けて 1 iteration を継続) ======

def load_proposal_file(path: str) -> Tuple[L.PlannerProposal, CoderProposalTriggerGating,
                                           AuditorVerdict, Optional[bool]]:
    """メインセッションが spawn した planner/coder/auditor の構造化出力を JSON から読む。

    schema は sort 版と同型 (coder に value フィールドが無い点も同じ)::

        {"planner": {axis, direction, magnitude, justification?, uncertainty?},
         "coder":   {axis, implementation, justification?, confidence?},
         "auditor": {verdict, diff_digest, violations?, nits?, proposed_tests?, uncertainty?},
         "prior_critic_reverse": true|false|null}

    トップレベルキーは `d[...]` で読む (欠落 = KeyError で fails-closed)。"""
    with open(path, encoding="utf-8") as f:
        d = json.load(f)
    assert_closed_proposal_schema(
        d, require_auditor=True, require_coder_value=False,
    )
    p, c, a = d["planner"], d["coder"], d["auditor"]
    planner = L.PlannerProposal(
        axis=p["axis"], direction=p["direction"], magnitude=p["magnitude"],
        justification=p.get("justification", ""), uncertainty=p.get("uncertainty", ""))
    coder = CoderProposalTriggerGating(
        axis=c["axis"], implementation=c["implementation"],
        justification=c.get("justification", ""), confidence=c.get("confidence", "medium"))
    auditor = parse_auditor_dict(a)   # verdict 未知・digest 空/非文字列 → AuditorGateFailure
    prior = d.get("prior_critic_reverse")
    if prior is not None and not isinstance(prior, bool):
        raise ValueError(f"prior_critic_reverse は null か bool のみ (got {type(prior).__name__}: "
                         f"{prior!r}) — 非 bool は停止フィードバックを fail-open させる (規律2)")
    assert_no_ability_probe_material(d)
    return planner, coder, auditor, prior


def drive_iteration(cfg: CampaignConfig, perf, planner: L.PlannerProposal,
                    coder: CoderProposalTriggerGating, auditor: AuditorVerdict,
                    prior_critic_reverse: Optional[bool], sub: str, do_build: bool,
                    layout: Optional[CampaignLayout] = None, log=print,
                    cache_root: str = "", proposal_path: str = "",
                    extra_sources: Sequence[Dict[str, str]] = (), *,
                    dependency_prefix: str = "") -> Dict:
    """段 8a trigger-gating の 1 iteration をメインセッション駆動で回す (sort 版と
    同型の骨格 + provenance 配線)。

    provenance の書き込み順序 (レビュー FC-1 裁定):
      1. ヘッダ = 本関数入口 (build 前)。情報源の静的欠落は 1 度のビルドも走らせず停止
      2. entry = run_one_iteration の後・`save_loop_state` の**前**。entry が書けない
         iteration は checkpoint が前進しない → 再開時に WAL replay (重複解決) 経由で
         同 iteration が再記録される (duplicate 経路も entry を書く)
    """
    resolved_site = _current_site()
    contract = _admit_env_contract(resolved_site)
    campaign_cfg = _campaign_cfg_for_site(cfg, resolved_site)
    if layout is None:
        layout = exploration_campaign_layout(str(ident.campaign_id(campaign_cfg)))
    _assert_resume_allowed(contract, layout)
    layout.ensure()
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
    )
    _append_provenance_entry(layout, state.iteration, {
        "proposal_path": proposal_path,
        "auditor_diff_digest": auditor.diff_digest,
        "variant": out.get("variant"),
        "outcome": out["outcome"],
    })
    L.save_loop_state(layout, state)

    digest_txt = L.make_critic_digest(
        layout, tag=CRITIC_TAG, reflux=(cfg.search_config.get("reflux") == "on"))
    with open(os.path.join(layout.root, DIGEST_BASENAME), "w", encoding="utf-8") as f:
        f.write(digest_txt)

    post = L.check_stop(state)
    out.update({"stop_reason": post.reason, "iteration": state.iteration, "ran": True})
    return out


# ==== CLI =======================================================================

def _preview_diff(implementation_path: str, sub: str, root: str) -> Dict:
    """auditor へ渡す実 diff を得る (メインセッションが auditor spawn 前に呼ぶ。
    sort 版と同型)。"""
    from campaign.patchharness import applied, assert_pinned_clean
    with open(implementation_path, encoding="utf-8") as f:
        implementation = f.read()
    assert_pinned_clean(sub, PIN)
    with applied(_template_patch_path(root), PIN, sub):
        res, _base, _edited, working_diff = L.quarantine(
            sub, implementation, marker_id=MARKER_ID, source_rel=SOURCE_REL, write=False)
    return {"passed": res.passed, "working_diff": working_diff,
           "diff_digest": compute_diff_digest(working_diff),
           "subtype": (res.subtype.value if res.subtype else None), "reason": res.reason}


def main(argv: Optional[List[str]] = None) -> int:
    """fixture proposal で 1 iteration の機械 E2E を実走する (配線実証)。

    実 LLM (planner-v4/coder-v4-autonomous-trigger-gating/auditor/critic) はメイン
    セッションが spawn する (F 段、別セッション)。fixture 経路は恒等 gate (stock 相当、
    偵察 insight 非依拠) での配線確認であり provenance 記録の対象外 — 実 LLM 駆動は
    必ず `--run-iteration` → `drive_iteration` を通り、そこで記録義務が自動で果たされる
    (レビュー FC-7 裁定)。"""
    ap = argparse.ArgumentParser(
        description="P3 段 8a trigger-gating coder 自律ループ (機械 E2E)")
    ap.add_argument("--no-build", action="store_true",
                    help="build/verify/bench を省き挿入→検疫→構文契約→auditor gate の配線のみ確認")
    ap.add_argument("--reflux", choices=["on", "off"], default="on",
                    help="critic 還流 on/off (LLM ablation の対照アーム)")
    ap.add_argument("--run-iteration", metavar="PROPOSAL.json",
                    help="実 planner/coder/auditor proposal (JSON) を受けて checkpoint 継続で "
                         "1 iteration を回す (メインセッションが毎 iteration これを呼ぶ)")
    ap.add_argument("--preview-diff", metavar="IMPLEMENTATION.txt",
                    help="auditor spawn 前の配線: implementation テキストを読み working_diff + "
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

    if a.preview_diff:
        out = _preview_diff(a.preview_diff, fixed_sub, root)
        print(json.dumps(out, ensure_ascii=False, indent=2))
        return 0 if out["passed"] else 1

    from campaign import patchharness
    from campaign.p2_2 import _assert_single_tenant
    if not a.no_build:
        _assert_single_tenant()
    patchharness.assert_pinned_clean(fixed_sub, PIN)

    cfg = default_cfg(reflux=(a.reflux == "on"))
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
                                  extra_sources=extra_sources)
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

    # fixture proposal (機械 E2E 用。恒等 gate = stock 相当、D 偵察の ident_all と同じ
    # 「常に backoff する」述語 — SYNTAX_CONTRACT_FORBIDDEN 非参照は自明)。
    state = L.LoopState(start_ts=time.monotonic())
    state.iteration = 1
    planner = L.PlannerProposal(axis=MARKER_ID, direction="explore_both", magnitude="small",
                                justification="fixture (機械 E2E 用)")
    fixture_impl = "  izanagi_gate_pass = true;"
    coder = CoderProposalTriggerGating(axis=MARKER_ID, implementation=fixture_impl,
                                       justification="fixture", confidence="low")

    print(f"=== 段8a trigger-gating loop 1 iteration (機械 E2E, reflux={a.reflux}, "
          f"build={not a.no_build}, isolate_worktree={isolate}) ===")
    with wt_cm as sub:
        from campaign.patchharness import applied
        with applied(_template_patch_path(root), PIN, sub):
            res, _b, _e, working_diff = L.quarantine(
                sub, fixture_impl, marker_id=MARKER_ID, source_rel=SOURCE_REL, write=False)
        auditor = AuditorVerdict(verdict="pass", diff_digest=compute_diff_digest(working_diff),
                                 uncertainty="fixture (機械 E2E 用、実 auditor 未使用)")
        out = run_one_iteration(cfg, perf, planner, coder, auditor, state, sub,
                                do_build=not a.no_build, cache_root=cache_root)
    print(f"  outcome={out['outcome']} variant={out.get('variant')}")

    expected_layout = exploration_campaign_layout(out["campaign_id"])
    layout = CampaignLayout(out["layout_root"])
    if layout.root != expected_layout.root:
        raise ValueError("返却された campaign_id と exploration layout_root が一致しない")
    digest_txt = L.make_critic_digest(layout, tag=CRITIC_TAG, reflux=(a.reflux == "on"))
    out_path = os.path.join(layout.root, DIGEST_BASENAME)
    layout.ensure()
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(digest_txt)

    stop = L.check_stop(state)
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
