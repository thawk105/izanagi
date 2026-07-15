# -*- coding: utf-8 -*-
"""P3 段 8a D 段: silo-backoff-trigger-gating 軸の機械列挙 sweep (偵察、D46 型)。

abort 要因部分集合 gate の空間を機械列挙で回し、軸の生死 (floor 超地形の有無) を
E 段 (LLM ループ) 実装の固定費を払う前に判定する材料を作る。設計は 3 レンズ敵対
レビュー (2026-07-11、事前登録整合/機構安全/統計) を経る。器は sort 軸偵察
(`s6_sort_sweep.py`、D46) の骨格を踏襲 — 2 軸目の適用 = 器の汎用性の初実証。
軸定数は `axis_trigger_gating` (C 段成果物) から import する (E 段 driver import は
しない — axis-onboarding §1 脚注、sort 軸の歴史的経緯は踏襲しない)。

**位置づけ = 偵察 (preliminary)。事前登録 (phase3-main-experiment.md) が定義する
どの実験構成でもない** (D46 決定 1):
  - 失敗条件 (c) の判定は出さない。「軸の生死」の断定はしない — 出口は記述統計 +
    限定つき観察を insight に凍結し、継続/軸見直しは人間判断。
  - **firewall (D48 必須条件 7): E 段 coder/planner 入力に流してよいのは軸の生死
    二値 (floor 超地形の有無) のみ。** 本 sweep の具体勝ち点・要因部分集合・順位・
    診断数値を leakproof_context / planner direction / whiteboard に入れてはいけない。
    段 6 の正式 grid / (c) 判定も本結果を材料流用せずゼロから再導出する。
  - 8a 由来軸は当面「探索補助」限定で段 6 headline の対象軸にしない (D47 決定 5)。
  - write-heavy / read-heavy の S2 verify は S2_FLAGS 固定 (rr50) のため off-workload 被覆。
  - 本 sweep は fairness 偏向 (D41 型 15) を検出しない。
  - 素の sweep は適応 `Backoff_` との連成地形を測る (gate 単独の帰属は曇る — 偵察の
    目的は帰属でなく生死。設計ドラフト §1(c)、直交性主張は adaptive-off 前提の限定付き)。
  - **cross-run 再測の必須化 (レビュー MS-2/STAT-3):** floor 超候補が出たら、その点 +
    比較基準 ident_all を --remeasure (別 trial = 別セッション) で裏取りしてからでないと
    生死二値を確定しない — 単一 campaign の観測は候補提示のみ。対照の 1 セッション誤差は
    全比較に common-mode で乗るため、reps 増でなく cross-run が正しい打ち手。
  - 全点平坦だった場合の BACKOFF_FIXED 追走 (契機・前提タスクは設計ドラフト裁定 4/7):
    workload は機序ベース事前固定 = read-heavy (純損回避側最良ケース、シート導出)。
    2 パッチ合成の clean 検証が前提 — 発火しない限り実装しない (contingency)。

列挙空間 = 実効要因 (頻度実測 `s8a_trigger_freq.py` が確定した非ゼロ要因) の部分集合
2^N 全点 + 恒等 gate (GATEABLE 5 要因全列挙 = D49 申し送り (a) の stock 対照) + 真 stock
(フラグ 0 = 骨格常駐コスト別掲用)。全候補の述語は「kUnset (fail-safe 契約、coder 契約と
同一) + 部分集合の enum 等値比較の OR 連鎖」の 1 代入文 = enum membership 判定のみで
UB なし・副作用なし・構成的安全。構文契約の禁止トークン
(`axis_trigger_gating.SYNTAX_CONTRACT_FORBIDDEN`) 不使用はテストが機械検査する。
退化点 = 空集合 (実要因全素通し = 真の BACK_OFF=0 相当)。

比較の基準点 = **恒等 gate (ident_all、フラグ 1)** — フラグ 0 stock との比較は骨格常駐
コスト (7 store + 1 分岐) を軸効果に混入させる (D49 申し送り (a))。stock は ident_all との
差 = 骨格コストの別掲にのみ使う。

floor: balanced/write-heavy = 0.030 暫定流用 (D46 と同じ限定 — high-abort 点は判定不能
fails-closed)。read-heavy = 0.030 — wired 規則 = max(0.030, rr95 fresh 実測) で、rr95
fresh 実測 (within 0.19% / between 0.11%、`between_run_noise_t48_skew0p9_rr95_rmw0.json`)
は 0.030 を下回る (D48 前提 (b) の消化)。**限定 (レビュー F3/STAT-2): fresh between は
cold-boot/温度ドリフト未含の下限であり、rr95 の cross-campaign genuine between は未較正。
「0.030 ≥ rr95 genuine-between」は low-abort→low-drift の未検証仮定 — read-heavy の生死
判定はこの残存リスクを負う (将来 rr95 の cross-campaign repro が取れたら max に加える)。**

実行 (計測機で直列、実行前に single-tenant を確認。頻度実測 → 本走の順):
  python3 campaign/s8a_trigger_freq.py                     # 必須前提 (a) — 実効ビット確定
  python3 campaign/s8a_trigger_sweep.py balanced           # 本走 (2^N + 対照 2)
  python3 campaign/s8a_trigger_sweep.py balanced --report  # 集計のみ (計測なし)
  python3 campaign/s8a_trigger_sweep.py balanced --remeasure --names ident_all,g_lc
      # cross-run 裏取り (別 trial に分離)
"""
from __future__ import annotations

import argparse
import contextlib
import itertools
import json
import os
import sys
from typing import Dict, List, Optional, Sequence, Tuple

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from campaign import axis_trigger_gating as T                     # noqa: E402
from campaign import ident, pipeline, source_digest, wal          # noqa: E402
from campaign import p3_s4_loop as L                              # noqa: E402
from campaign.layout import campaign_layout, repo_output_root     # noqa: E402
from campaign.loop import run_campaign                            # noqa: E402
from campaign.model import (STAGE_ABORT, STAGE_BENCH_DONE,        # noqa: E402
                            STAGE_COMMIT, CampaignConfig, Genome)
from campaign.p2_2 import (EXTIME, RECORDS, REPS, THREADS,        # noqa: E402
                           WORKLOADS as P22_WORKLOADS, _assert_single_tenant)
from campaign.pipeline import (SEARCH_CONFIG_VERIFY_KEY,          # noqa: E402
                               VERIFY_LEGACY_PLUS_S2, PerfConfig, variant_id)

PIN = T.PIN
ENV_TAG = "linux-baremetal"
CLK = 1800
NUMA = ["numactl", "--interleave=all"]

SPACE_VERSION = "reason-subset-v1"
TRIAL_MAIN = "p3-s8a-trigger-sweep"

# floor (workload 別)。read-heavy の 0.030 は rr95 実測 (within 0.19%/between 0.11%) で
# 保守性を裏付けた値 (docstring 参照)。high-abort 点には適用しない (D46 踏襲)。
FLOOR_CV = {"balanced": 0.030, "write-heavy": 0.030, "read-heavy": 0.030}
HIGH_ABORT_FACTOR = 2.0   # 基準 (ident_all) 比この倍率超の abort 率は floor 未較正 = 判定不能

# p2_2 と同じ座標系 (skew0.9 固定で rratio を振る)。感度はシート「感度を持つ workload」欄
# の導出により全 3 類型を残す (balanced/write-heavy = 利得側、read-heavy = 純損回避側)。
WORKLOADS = dict(P22_WORKLOADS)

STOCK_NAME = "stock"        # フラグ 0 (骨格が #if で消え preprocess 後に原文一致)
IDENT_NAME = "ident_all"    # フラグ 1 + GATEABLE 5 要因全列挙 = 恒等 gate (比較の基準点)

STOCK_IMPL_NOTE = ("BACKOFF_TRIGGER_GATING=0 — 骨格全体が #if で消え preprocess 後に "
                   "pinned HEAD と原文一致 (src_token=stock)。abort() は要因不問で "
                   "Backoff::backoff() を無条件呼出 (transaction.cc の stock 枝)。"
                   "ident_all との差 = 骨格常駐コスト (7 store + 1 分岐) の別掲用")

# 要因名 → C++ enum 値 / 候補名用短縮 (REASON_NAMES と同語彙、gate 可能 5 種のみ)
_CPP_ENUM = {"lock-conflict": "kLockConflict", "update-absent": "kUpdateAbsent",
             "readvali-tid": "kReadValiTid", "readvali-locked": "kReadValiLocked",
             "node-vali": "kNodeVali"}
_ABBREV = {"lock-conflict": "lc", "update-absent": "ua", "readvali-tid": "rt",
           "readvali-locked": "rl", "node-vali": "nv"}


# ==== 頻度実測 (必須前提 (a)) の消費 ==========================================

def freq_json_path() -> str:
    return os.path.join(repo_output_root(), "env", ENV_TAG, "calibration",
                        f"s8a_trigger_freq_t{THREADS}.json")


def load_effective_reasons() -> List[str]:
    """頻度実測 (s8a_trigger_freq.py、D48 前提 (a)) の実効ビットを読む。

    JSON 不在・部分実行 (effective_reasons 欠落)・保存則破れは fails-closed で停止 —
    不感ビットの根拠なしに列挙空間を決めない。"""
    path = freq_json_path()
    if not os.path.exists(path):
        raise RuntimeError(f"頻度実測が無い: {path} — 先に s8a_trigger_freq.py を回す"
                           " (D48 必須前提 (a): 不感ビット未確定のまま sweep を設計しない)")
    with open(path, encoding="utf-8") as f:
        j = json.load(f)
    if "effective_reasons" not in j:
        raise RuntimeError(f"頻度実測が部分実行 (effective_reasons 欠落): {path} — "
                           "全 workload で回し直すこと (fails-closed)")
    broken = [t for t, w in j.get("workloads", {}).items()
              if not w.get("conservation_ok")]
    if broken:
        raise RuntimeError(f"頻度実測の保存則が破れている workload: {broken} — "
                           "数え漏れのある分布を列挙空間の根拠にしない (fails-closed)")
    eff = list(j["effective_reasons"])
    unknown = [r for r in eff if r not in T.GATEABLE_REASONS]
    if unknown:
        raise RuntimeError(f"effective_reasons に gate 不能な要因: {unknown} "
                           f"(GATEABLE_REASONS={T.GATEABLE_REASONS})")
    return eff


# ==== 述語生成 (構成的安全。ラベルをコメントで付けない — src_token は preprocess 後
#      ハッシュ。述語は必ず 1 行 = hole が単一行のため複数行は検疫で落ちる) =====

def predicate_for(reasons: Sequence[str]) -> str:
    """要因部分集合 → gate 述語の 1 代入文。

    kUnset → true は全候補に固定 (骨格の fail-safe sentinel 契約 = coder 契約と同一。
    偵察空間 = coder 変異空間の一致を保つ、シート/D48)。空集合 = kUnset のみ =
    実要因全素通し (真の BACK_OFF=0 相当の退化点)。"""
    terms = ["izanagi_abort_reason_ == IzanagiAbortReason::kUnset"]
    for r in reasons:
        terms.append(f"izanagi_abort_reason_ == IzanagiAbortReason::{_CPP_ENUM[r]}")
    return "izanagi_gate_pass = " + " || ".join(terms) + ";"


def subset_name(reasons: Sequence[str]) -> str:
    return "g_" + "+".join(_ABBREV[r] for r in reasons) if reasons else "g_none"


def candidates(effective: Sequence[str]) -> List[Tuple[str, str, str]]:
    """(name, category, implementation) の列挙。

    - 実効要因の部分集合 2^N 全点 (D46「代表点手選びは列挙原則の独立性を毀損」の踏襲)。
      空集合 = degenerate (退化点)、それ以外 = subset。
    - ident_all = GATEABLE 5 要因全列挙 (恒等 gate、control-identity)。実効全集合とは
      述語文字列が異なる別 variant — 両者の floor 内一致が不感ビット縮約の健全性検査を
      兼ねる (設計ドラフト §3)。
    順序は GATEABLE_REASONS の定義順を保つ (列挙の決定論)。"""
    eff = [r for r in T.GATEABLE_REASONS if r in effective]   # 定義順に正規化
    out: List[Tuple[str, str, str]] = []
    for k in range(len(eff) + 1):
        for combo in itertools.combinations(eff, k):
            cat = "degenerate" if not combo else "subset"
            out.append((subset_name(combo), cat, predicate_for(combo)))
    out.append((IDENT_NAME, "control-identity",
                predicate_for(list(T.GATEABLE_REASONS))))
    return out


def candidate_names(effective: Sequence[str]) -> List[str]:
    return [STOCK_NAME] + [n for n, _c, _i in candidates(effective)]


# ==== campaign 構成 ===========================================================

def _repo_root() -> str:
    here = os.path.dirname(os.path.abspath(__file__))
    return os.path.dirname(os.path.dirname(here))


def config_for(tag: str, effective: Sequence[str],
               trial: str = TRIAL_MAIN) -> CampaignConfig:
    """workload と実効ビット集合を search_config に焼く — workload 別の identity 分離
    (variant_id クロス汚染の構造的防止、s6_sort_sweep と同型) + 実効ビットが変われば
    別 campaign (列挙空間の異なる sweep を同一 WAL に混ぜない)。"""
    workload = WORKLOADS[tag]
    return CampaignConfig(
        spec_slug=f"p3-s8a-trigger-sweep-{tag}", search_tag="sweep",
        spec_content=(
            "P3 段 8a D 段: silo-backoff-trigger-gating 機械列挙 sweep (偵察、D46 型)。"
            "preliminary = 事前登録外カテゴリ、断定 verdict なし、(c) 判定は出さない。"
            "firewall: E 段へは軸の生死二値のみ (D48 条件 7)・段 6 正式 grid へ材料流用"
            "しない。素の sweep は適応 Backoff_ との連成地形 (直交性主張は adaptive-off "
            f"限定)。空間 = {SPACE_VERSION}: 実効要因 {list(effective)} の部分集合 2^N "
            f"(kUnset→true 固定) + ident_all + stock。workload={tag}。"),
        ccbench_commit=PIN,
        search_config={"scale": "silo", "axis": T.MARKER_ID,
                       "generator": SPACE_VERSION,
                       "space": "reason-subsets(effective)+identall+stock",
                       "effective_reasons": list(effective),
                       "workload": tag, "ycsb": workload,
                       "records": RECORDS, "threads": THREADS,
                       SEARCH_CONFIG_VERIFY_KEY: VERIFY_LEGACY_PLUS_S2},
        trial=trial)


def perf_for(tag: str) -> PerfConfig:
    """p2_2 確定動作点 (D15: t48/1M/extime3/reps5) — diagnostics と同一動作点で地形の
    連続性を保つ (シート「計測動作点」欄)。"""
    return PerfConfig(records=RECORDS, threads=THREADS, workload=WORKLOADS[tag],
                      extime=EXTIME, reps=REPS)


def _genome(gating: int) -> Genome:
    return Genome("silo", {**T._BASE, "BACKOFF_TRIGGER_GATING": gating})


# ==== 駆動 (s6_sort_sweep.run_sweep と同骨格) =================================

def run_sweep(tag: str, names: Optional[List[str]] = None, trial: str = TRIAL_MAIN,
              isolate: bool = True, log=print) -> Dict[str, Dict]:
    """候補ごとに applied(骨格) → quarantine(write) → run_campaign を直列に回す。

    1 候補 = 1 run_campaign 呼び出し (同一 campaign dir に WAL 追記、variant_id は
    src_token で分岐)。中断再開は WAL replay (評価済み variant はスキップ)。失敗は
    variant 単位で隔離され campaign は継続する。
    返り値 = name → {variant_id, category, src_token, outcome}。"""
    from campaign.patchharness import assert_pinned_clean, checkout

    _assert_single_tenant()
    effective = load_effective_reasons()
    root = _repo_root()
    fixed_sub = os.path.join(root, "external", "ccbench")
    assert_pinned_clean(fixed_sub, PIN)

    all_names = candidate_names(effective)
    sel_names = names if names is not None else all_names
    unknown = [n for n in sel_names if n not in all_names]
    if unknown:
        raise ValueError(f"未知の候補名: {unknown} (選択肢: {all_names})")

    cfg = config_for(tag, effective, trial)
    perf = perf_for(tag)
    layout = campaign_layout(str(ident.campaign_id(cfg)))
    layout.ensure()
    patch = os.path.join(root, "patches", T.TEMPLATE_PATCH)

    wt_cm = checkout(PIN, base_dir=fixed_sub) if isolate else \
        contextlib.nullcontext(fixed_sub)
    cache_root = os.path.join(fixed_sub, "build-variants") if isolate else ""

    prov: Dict[str, Dict] = {}
    log(f"\n=== s8a trigger sweep  workload={tag}  trial={trial}  "
        f"{len(sel_names)} 点 (campaign {layout.root}) ===")
    try:
        with wt_cm as sub:
            for name in sel_names:
                try:
                    entry = _eval_one(name, effective, cfg, perf, layout, sub,
                                      patch, cache_root, log=log)
                except Exception as e:
                    # driver 層 (applied/quarantine/resolve) の例外も候補単位で隔離 —
                    # 1 点の transient 失敗で全走を落とし成果ゼロにしない (s6 と同型)。
                    log(f"  ✗ {name}: driver 層エラーで隔離 — {type(e).__name__}: {e}")
                    entry = {"variant_id": None, "category": None, "src_token": None,
                             "outcome": "driver-error", "error": str(e)}
                prov[name] = entry
                _write_provenance(layout, tag, trial, effective, prov)  # 逐次書き
    finally:
        if prov:
            _write_provenance(layout, tag, trial, effective, prov)
    return prov


def _eval_one(name: str, effective: Sequence[str], cfg: CampaignConfig,
              perf: PerfConfig, layout, sub: str, patch: str, cache_root: str,
              log=print) -> Dict:
    from campaign.patchharness import applied
    if name == STOCK_NAME:
        cat, impl = "stock", None
        genome = _genome(0)
    else:
        cat, impl = next((c, i) for n, c, i in candidates(effective) if n == name)
        genome = _genome(1)

    with applied(patch, PIN, sub):
        if impl is not None:
            res, _b, _e, _wd = L.quarantine(sub, impl, marker_id=T.MARKER_ID,
                                            source_rel=T.SOURCE_REL, write=True)
            if not res.passed:
                v = L.record_diff_reject(layout, genome, impl, res, env_tag=ENV_TAG)
                log(f"  ✗ {name}: diff 検疫 reject ({res.digest.get('subtype')}) — "
                    f"機械生成候補が検疫を通らないのは driver のバグ (要修正)")
                return {"variant_id": v, "category": cat, "src_token": None,
                        "outcome": "quarantine-reject"}
        src_tok = source_digest.resolve(genome, cfg.ccbench_commit, sub)
        vid = variant_id(genome, src_tok)
        log(f"  --- {name} ({cat}) variant={vid} src={src_tok[:12]} ---")
        summary = run_campaign(cfg, [genome], perf, ENV_TAG, CLK, numactl=NUMA,
                               log=log, ccbench_dir=sub, cache_root=cache_root)
    r = summary.results[0] if summary.results else None
    if r is not None:
        outcome = "certified" if (r.certified and not r.aborted) else "aborted"
    else:
        outcome = _replay_outcome(layout, vid)   # WAL replay で skip (中断再開時)
    return {"variant_id": vid, "category": cat, "src_token": src_tok,
            "outcome": outcome}


def _replay_outcome(layout, vid: str) -> str:
    recs = wal.records_by_stage(layout, vid)
    if recs.get(STAGE_COMMIT) is not None:
        return "replayed-certified"
    if recs.get(STAGE_ABORT) is not None:
        return "replayed-aborted"
    return "replayed-unknown"


def _write_provenance(layout, tag: str, trial: str, effective: Sequence[str],
                      prov: Dict[str, Dict]) -> str:
    """name → variant_id / implementation 全文の対応を reports/ に凍結する
    (variant_id は src_token 由来で候補名を含まない — この対応が無いと WAL から地形を
    復元できない。proof-chain 成果物には書かない、s6 と同型)。merge 書き。"""
    impls = {n: i for n, _c, i in candidates(effective)}
    impls[STOCK_NAME] = STOCK_IMPL_NOTE
    path = os.path.join(layout.root, "reports", "s8a_trigger_sweep_provenance.json")
    existing: Dict[str, Dict] = {}
    if os.path.exists(path):
        try:
            with open(path, encoding="utf-8") as f:
                existing = json.load(f).get("entries", {})
        except (json.JSONDecodeError, OSError):
            existing = {}
    entries = {**existing,
               **{n: {**e, "implementation": impls.get(n)} for n, e in prov.items()}}
    doc = {"space_version": SPACE_VERSION, "workload": tag, "trial": trial,
           "pin": PIN, "effective_reasons": list(effective),
           "floor_cv": FLOOR_CV.get(tag),
           "freq_source": freq_json_path(),
           "firewall": ("偵察 → E 段は軸の生死二値のみ (D48 条件 7)。"
                        "段 6 正式 grid へ材料流用しない (D46 決定 1)"),
           "entries": entries}
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(doc, f, ensure_ascii=False, indent=2)
    return path


# ==== 集計 (記述統計のみ — 断定 verdict を出さない) ============================

def _load_rows(layout, prov_entries: Dict[str, Dict]) -> List[Dict]:
    rows = []
    for name, e in prov_entries.items():
        vid = e.get("variant_id")
        if not vid:
            continue
        recs = wal.records_by_stage(layout, vid)
        commit = recs.get(STAGE_COMMIT)
        certified = commit is not None
        # BENCH_DONE は screening 経路では uncertified のまま存在し得る。性能値は
        # COMMIT の存在で gate し、探索・正式レポートへ漏らさない。
        bench = (recs.get(STAGE_BENCH_DONE) or {}) if certified else {}
        abort = recs.get(STAGE_ABORT)
        li = bench.get("leading_indicators") or {}
        rows.append({
            "name": name, "category": e.get("category"), "variant_id": vid,
            "certified": certified,
            "aborted": not certified and abort is not None,
            "abort_reason": (abort or {}).get("reason"),
            "median_tps": bench.get("median_tps"), "cv": bench.get("cv"),
            "unstable": bool(bench.get("unstable")),
            "abort_rate": li.get("abort_rate"), "ipc": li.get("ipc"),
            "llc_miss_rate": li.get("llc_miss_rate"),
        })
    return rows


def report(tag: str, trial: str = TRIAL_MAIN, log=print) -> Optional[str]:
    """WAL 直読みの記述統計レポート。比較基準 = ident_all (恒等 gate、D49 申し送り (a))。
    退化点は subset レンジ集計から分離。unstable 点はレンジ集計から除外。"""
    effective = load_effective_reasons()
    cfg = config_for(tag, effective, trial)
    layout = campaign_layout(str(ident.campaign_id(cfg)))
    ppath = os.path.join(layout.root, "reports", "s8a_trigger_sweep_provenance.json")
    if not os.path.exists(ppath):
        log(f"provenance がまだ無い: {ppath} (先に本走を回す)")
        return None
    with open(ppath, encoding="utf-8") as f:
        prov = json.load(f)
    rows = _load_rows(layout, prov["entries"])

    ok = [r for r in rows if r["certified"] and r["median_tps"] is not None]
    ident_row = next((r for r in ok if r["name"] == IDENT_NAME), None)
    stock_row = next((r for r in ok if r["name"] == STOCK_NAME), None)
    stable = [r for r in ok if not r["unstable"]]
    subs = [r for r in stable if r["category"] == "subset"]
    degen = [r for r in stable if r["category"] == "degenerate"]
    screen_rejected = [
        r for r in rows
        if not r["certified"]
        and r["abort_reason"] == pipeline.SCREEN_REJECTION_REASON
    ]
    other_aborted = [
        r for r in rows
        if r["aborted"]
        and r["abort_reason"] != pipeline.SCREEN_REJECTION_REASON
    ]
    floor = FLOOR_CV.get(tag)

    lines: List[str] = []
    w = lines.append
    w(f"# s8a trigger-gating sweep 偵察レポート — workload={tag} trial={trial}")
    w("")
    w("**位置づけ:** 偵察 (preliminary、事前登録外カテゴリ)。断定 verdict なし。")
    w("**限定 (必読):** (1) 失敗条件 (c) の判定は出さない。(2) floor "
      f"{floor:.3f} は参考線 — high-abort 点 (退化点 + abort 率が基準 ident_all 比 "
      f"{HIGH_ABORT_FACTOR} 倍超) は floor 未較正 = 判定不能 (fails-closed)。"
      "read-heavy の floor は rr95 genuine-between 未較正の残存リスクを負う "
      "(fresh 実測は 0.030 内だが下限値 — レビュー F3/STAT-2)。"
      "(3) 本 sweep は fairness 偏向 (D41 型 15) を検出しない。"
      "(4) write-heavy/read-heavy の S2 verify は rr50 固定 (off-workload 被覆)。"
      "(5) 素の sweep は適応 Backoff_ との連成地形 — gate 単独の帰属は曇る "
      "(magnitude 軸との直交性主張は adaptive-off 前提の限定付き)。"
      "(6) firewall: E 段へは軸の生死二値のみ・段 6 正式 grid へ材料流用しない。"
      "本偵察 insight を見て E 段入力を起草する記憶汚染は既知残存リスク — 偵察を見た"
      "事実を E 段 campaign provenance に情報源として記録する (D46 (a) のループ版)。"
      "(7) 本軸は 8a (post-coder) 由来 — 探索補助限定・段 6 headline 非対象 (D47 決定 5)。"
      "(8) 単一 campaign の floor 超は候補提示のみ — 生死二値の確定は cross-run 再測 "
      "(当該点 + ident_all の --remeasure) 後 (レビュー MS-2/STAT-3)。")
    w("**集計母集団:** 数値テーブルとレンジ・min・best は certified 生存点限定。"
      "screening 正常棄却は未認証のため reason だけを別掲し、性能数値を描画しない。")
    if "remeasure" in trial and ident_row is None:
        w("")
        w("**⚠ fails-closed 警告: 本 remeasure campaign に cross-run 基準 ident_all が"
          "無い — common-mode 誤差を抜けないため、この再測では生死を確定できない "
          "(ident_all を含めて回し直すこと。レビュー MS-2/STAT-3)。**")
    w("")
    w("| 点 | 分類 | median tps | CV% | abort率 | unstable | certified | 備考 |")
    w("|---|---|---:|---:|---:|---|---|---|")
    for r in sorted(ok, key=lambda x: -(x["median_tps"] or 0)):
        note = []
        if r["name"] == IDENT_NAME:
            note.append("基準 (恒等 gate、フラグ 1)")
        if r["name"] == STOCK_NAME:
            note.append("stock (フラグ 0) — 骨格コスト別掲用")
        elif _floor_uncalibrated(r, ident_row):
            note.append("high-abort/未較正: floor 判定不能")
        w(f"| {r['name']} | {r['category']} | "
          f"{_fmt(r['median_tps'])} | {_fmt_pct(r['cv'])} | {_fmt_pct(r['abort_rate'])} | "
          f"{'⚠' if r['unstable'] else ''} | {'✓' if r['certified'] else '✗'} | "
          f"{'; '.join(note)} |")
    w("")

    if screen_rejected:
        w("### screening 正常棄却 (未認証のため性能数値なし)")
        w("")
        w("| 点 | 分類 | reason |")
        w("|---|---|---|")
        for r in sorted(screen_rejected, key=lambda x: x["name"]):
            w(f"| {r['name']} | {r['category']} | {r['abort_reason']} |")
        w("")
    if other_aborted:
        w("### その他の非認証 ABORT (性能数値なし)")
        w("")
        w("| 点 | 分類 | reason |")
        w("|---|---|---|")
        for r in sorted(other_aborted, key=lambda x: x["name"]):
            w(f"| {r['name']} | {r['category']} | {r['abort_reason']} |")
        w("")

    # レンジ集計・best-vs-基準は floor 較正済み点 (非 high-abort) に限定する —
    # 強調される best が floor 判定不能点になる誤読を構造的に消す (実装レビュー F2 nit)。
    calib = [r for r in subs if not _floor_uncalibrated(r, ident_row)]
    uncal = [r for r in subs if _floor_uncalibrated(r, ident_row)]
    if calib:
        best, worst = max(calib, key=_tps), min(calib, key=_tps)
        w(f"**subset 点 (certified 生存点限定、stable かつ floor 較正済み, n={len(calib)}"
          f"{f' / 判定不能 {len(uncal)} 点は除外' if uncal else ''}):** "
          f"max={best['name']} {_fmt(_tps(best))} tps / min={worst['name']} "
          f"{_fmt(_tps(worst))} tps / レンジ {_rel(best, worst)} "
          f"(選択バイアス無補正の記述統計 — floor との断定比較は cross-run 再測点のみ)")
        if ident_row:
            w(f"**best vs 基準 (ident_all):** {best['name']} {_rel(best, ident_row)} "
              f"(参考線: floor ±{floor:.1%}。未再測 = 位置関係は暫定)")
    elif subs:
        w(f"**subset 点: 全 {len(subs)} 点が floor 判定不能 (high-abort/材料欠落) — "
          f"レンジ・best は出さない (fails-closed)**")
    if ident_row and stock_row:
        w(f"**骨格常駐コスト (別掲):** ident_all vs stock = {_rel(ident_row, stock_row)} "
          f"(フラグ 1 恒等 gate の 7 store + 1 分岐が乗る側 − 素の stock。軸の固定費)")
    # 不感縮約の backstop: 実効全集合 (subset 側の全ビット点) と ident_all の一致。
    # 不感ビットが真に不発なら両述語は runtime 等価でほぼ構成的に一致する —
    # これは検定ではなく低 power の backstop (一次証拠 = 頻度実測の count=0。
    # レビュー STAT-5 裁定)。
    eff_all = next((r for r in subs
                    if r["name"] == subset_name(list(effective))), None)
    if eff_all and ident_row:
        w(f"**不感縮約の backstop (実効全集合 {eff_all['name']} vs ident_all):** "
          f"{_rel(eff_all, ident_row)} — 一次証拠は頻度実測の count=0 でありこれは"
          f"低 power の backstop。floor 超の不一致を観測したら不感判定の誤りを疑い"
          f"頻度実測へ差し戻す (またはノイズ再測)。floor 内でも同値の証明ではない")
    if degen:
        w(f"**退化点 (別掲、レンジ集計外):** " + ", ".join(
            f"{r['name']} {_fmt(_tps(r))} tps" for r in degen))
    excl = [r for r in ok if r["unstable"]]
    if excl:
        w(f"**unstable 除外点:** " + ", ".join(r["name"] for r in excl))

    text = "\n".join(lines)
    rpath = os.path.join(layout.root, "reports",
                         f"s8a_trigger_sweep_report_{trial}.md")
    os.makedirs(os.path.dirname(rpath), exist_ok=True)
    with open(rpath, "w", encoding="utf-8") as f:
        f.write(text + "\n")
    log(text)
    log(f"\nレポート: {rpath}")
    return rpath


def _tps(r: Dict) -> float:
    return r["median_tps"] or 0.0


def _floor_uncalibrated(r: Dict, ident_row: Optional[Dict]) -> bool:
    """floor を適用してはいけない点か。退化点は無条件 True。非退化点は abort 率が基準
    (ident_all) 比 HIGH_ABORT_FACTOR 倍超で True。比較材料が欠けたら fails-closed で
    True (s6 の should-fix 裁定を踏襲)。"""
    if r["category"] == "degenerate":
        return True
    ab = r.get("abort_rate")
    iab = ident_row.get("abort_rate") if ident_row else None
    if ab is None or iab in (None, 0):
        return True
    return ab > HIGH_ABORT_FACTOR * iab


def _rel(a: Dict, b: Dict) -> str:
    ta, tb = _tps(a), _tps(b)
    return f"{(ta - tb) / tb:+.2%}" if tb else "n/a"


def _fmt(x) -> str:
    return f"{x:,.0f}" if isinstance(x, (int, float)) else "—"


def _fmt_pct(x) -> str:
    return f"{x * 100:.2f}" if isinstance(x, (int, float)) else "—"


# ==== CLI =====================================================================

def main(argv: Optional[List[str]] = None) -> int:
    ap = argparse.ArgumentParser(
        description="P3 段 8a D 段: trigger-gating 機械列挙 sweep (偵察)")
    ap.add_argument("workload", choices=sorted(WORKLOADS.keys()))
    ap.add_argument("--names", help="カンマ区切りの候補名 (省略 = 全点)")
    ap.add_argument("--remeasure", action="store_true",
                    help="cross-run 裏取り (trial を分けた別 campaign)。--names 必須")
    ap.add_argument("--report", action="store_true", help="集計のみ (計測なし)")
    ap.add_argument("--trial", default=None, help="trial 上書き (通常は使わない)")
    ap.add_argument("--no-isolate-worktree", action="store_true",
                    help="worktree 隔離を無効化 (デバッグ用。既定 ON)")
    ap.add_argument("--list", action="store_true", help="候補と implementation を表示")
    a = ap.parse_args(argv if argv is not None else sys.argv[1:])

    if a.list:
        for n, c, i in candidates(load_effective_reasons()):
            print(f"--- {n} ({c}) ---\n{i}")
        return 0

    trial = a.trial or (f"{TRIAL_MAIN}-remeasure1" if a.remeasure else TRIAL_MAIN)
    if a.remeasure and not a.names:
        print("--remeasure には --names (argmax winner,ident_all 等) が必須")
        return 2
    names = [n.strip() for n in a.names.split(",")] if a.names else None
    if a.remeasure and IDENT_NAME not in (names or []):
        # 裁定 MS-2/STAT-3: 対照の 1 セッション誤差は全比較に common-mode で乗る —
        # 基準 ident_all を含まない cross-run 再測は生死確定に使えない (fails-closed。
        # 実装レビュー 2026-07-11 F2)。
        print(f"--remeasure の --names に基準 {IDENT_NAME} が無い — common-mode 誤差を"
              "抜けない再測は生死確定に使えないため拒否 (レビュー MS-2/STAT-3)")
        return 2

    if a.report:
        return 0 if report(a.workload, trial=trial) else 1

    prov = run_sweep(a.workload, names=names, trial=trial,
                     isolate=not a.no_isolate_worktree)
    bad = {n: e for n, e in prov.items()
           if e["outcome"] not in ("certified", "replayed-certified")}
    print(f"\n=== s8a trigger sweep 完了: {len(prov) - len(bad)}/{len(prov)} 点 OK ===")
    if bad:
        for n, e in bad.items():
            print(f"  ✗ {n}: {e['outcome']}")
    report(a.workload, trial=trial)
    return 0 if not bad else 1


if __name__ == "__main__":
    sys.exit(main())
