# -*- coding: utf-8 -*-
"""s6_sort_sweep (段6前提タスク (i): sort comparator 機械列挙 sweep) の単体テスト。

build/verify/bench を伴わない機械部分のみ:
  1. **SWO 有限モデル総当たり** — 列挙候補の C++ 比較式を Python モデルへ機械導出し、
     有限空間で SWO 4 公理 (非反射・非対称・推移・同値の推移) を全対検査する。
     「全点 SWO-by-construction」の宣言 (設計 §5 backstop 4) をここで機械化する —
     転写ミス由来の非 SWO (D42: write_set_>=16 でハング) を実走前に落とす。
  2. category (full-order / degenerate) の意味論検査 — 実 workload 制約
     (単一 storage・key 一意・rcdptr 一意) 下で tie の有無と一致するか。
  3. 検疫通過 — 全候補が diff 検疫 (フレーム不可触・hole 封じ込め) を write=False で通る。
  4. identity — workload/trial が campaign_id に焼かれ分離される (機構レンズ should-fix)。
  5. nosort の無名引数形 (-Werror=unused-parameter 対策、機構レンズ must-fix) と
     コメント不在 (src_token は preprocess 後ハッシュでコメントが消える罠)。
"""
from __future__ import annotations

import itertools
import os
import re
import sys
import tempfile

_HERE = os.path.dirname(os.path.abspath(__file__))
_ORCH = os.path.dirname(_HERE)
sys.path.insert(0, _ORCH)

from campaign import ident                                        # noqa: E402
from campaign import p3_s4_loop as L                              # noqa: E402
from campaign import s6_sort_sweep as W                           # noqa: E402
from campaign.pipeline import SEARCH_CONFIG_VERIFY_KEY             # noqa: E402
from campaign.pipeline import VERIFY_LEGACY_PLUS_S2                # noqa: E402

# ==== C++ 比較式 → Python モデルの機械導出 ====================================
# 生成器 (_one/_two/_mk) が出す式形のみ受理する。受理できない式は即 fail
# (パーサが緩いと検査対象がすり替わる — fails-closed)。

_MEMBER_IDX = {"storage_": 0, "key_": 1, "rcdptr_": 2}


def _parse_cmp(expr: str):
    m = re.fullmatch(r"([ab])\.(storage_|key_|rcdptr_) < ([ab])\.(storage_|key_|rcdptr_)",
                     expr.strip())
    assert m, f"想定外の比較式: {expr!r}"
    assert m.group(2) == m.group(4), f"別メンバ間比較は列挙空間にない: {expr!r}"
    idx = _MEMBER_IDX[m.group(2)]
    pair = (m.group(1), m.group(3))
    if pair == ("a", "b"):
        return lambda a, b: a[idx] < b[idx]
    if pair == ("b", "a"):
        return lambda a, b: b[idx] < a[idx]
    raise AssertionError(f"a/b の組が不正: {expr!r}")


def model_from_impl(impl: str):
    """implementation 文字列から比較関数 (a,b)->bool を導出する。a/b は (S,K,P) タプル。"""
    body = " ".join(impl.split())
    m = re.search(r"return (.+?);", body)
    assert m, f"return 文が見つからない: {impl!r}"
    expr = m.group(1).strip()
    if expr == "false":
        return lambda a, b: False
    tern = re.fullmatch(r"a\.storage_ != b\.storage_ \? (.+?) : (.+)", expr)
    if tern:
        f1, f2 = _parse_cmp(tern.group(1)), _parse_cmp(tern.group(2))
        return lambda a, b: f1(a, b) if a[0] != b[0] else f2(a, b)
    return _parse_cmp(expr)


# 有限モデル空間: S∈{0,1}, K∈{"a","b"}, P∈{1,2,3} の全 12 要素 (重複 (S,K,P) なし —
# 実データでも rcdptr は一意)。SWO 公理は全対 (12^2, 推移は 12^3) を総当たり。
_SPACE = [(s, k, p) for s in (0, 1) for k in ("a", "b") for p in (1, 2, 3)]


def _assert_swo(f, name: str):
    for x in _SPACE:
        assert not f(x, x), f"{name}: 非反射性違反 comp(x,x)=true at {x}"
    for x, y in itertools.product(_SPACE, repeat=2):
        if f(x, y):
            assert not f(y, x), f"{name}: 非対称性違反 at {x},{y}"
    for x, y, z in itertools.product(_SPACE, repeat=3):
        if f(x, y) and f(y, z):
            assert f(x, z), f"{name}: 推移性違反 at {x},{y},{z}"

    def equiv(x, y):
        return not f(x, y) and not f(y, x)
    for x, y, z in itertools.product(_SPACE, repeat=3):
        if equiv(x, y) and equiv(y, z):
            assert equiv(x, z), f"{name}: 同値の推移性違反 at {x},{y},{z}"


def test_all_candidates_are_swo():
    for name, _cat, impl in W.CANDIDATES:
        _assert_swo(model_from_impl(impl), name)


def test_sk_aa_matches_python_tuple_order():
    """sk_aa (coder iter1 同値点 = stock 順序) は (S,K) タプル辞書式と完全一致する
    (導出パーサ自体のクロスチェック)。"""
    f = model_from_impl(next(i for n, _c, i in W.CANDIDATES if n == "sk_aa"))
    for x, y in itertools.product(_SPACE, repeat=2):
        assert f(x, y) == ((x[0], x[1]) < (y[0], y[1]))


# ==== category の意味論 (実 workload 制約下の tie 有無) ========================
# 実 workload 制約: 単一 storage (YCSB)・key 一意・rcdptr 一意。K↔P の対応は
# 単調とは限らない (アドレス順 ≠ キー順) ので P はシャッフルして置く。

_WORKLOAD_SPACE = [(0, "a", 2), (0, "b", 3), (0, "c", 1)]


def test_category_semantics_under_workload_constraints():
    for name, cat, impl in W.CANDIDATES:
        f = model_from_impl(impl)
        has_tie = any(not f(x, y) and not f(y, x)
                      for x, y in itertools.combinations(_WORKLOAD_SPACE, 2))
        if cat == "full-order":
            assert not has_tie, f"{name}: full-order なのに tie が残る"
        else:
            assert has_tie, f"{name}: degenerate なのに tie が無い"


# ==== 列挙の構造 ==============================================================

def test_candidate_names_unique_and_counts():
    names = [n for n, _c, _i in W.CANDIDATES]
    assert len(names) == len(set(names)) == 15
    assert len([n for n, c, _i in W.CANDIDATES if c == "degenerate"]) == 3
    assert W.STOCK_NAME not in names
    assert W.CODER_EQUIV in names
    assert W.candidate_names()[0] == W.STOCK_NAME
    assert len(W.candidate_names()) == 16


def test_nosort_uses_anonymous_params():
    """nosort は引数名を持たない (-Werror=unused-parameter でビルド不能になるため。
    機構レンズ must-fix、GCC13 実測)。"""
    impl = next(i for n, _c, i in W.CANDIDATES if n == "nosort")
    assert "return false;" in impl
    assert re.search(r"WriteElement<Tuple>&\s*[ab]\b", impl) is None, \
        "nosort に引数名が付いている (未使用引数警告でビルドが落ちる)"


def test_no_comments_in_implementations():
    """src_token は preprocess 後ハッシュ (コメント除去) — コメントだけ違う 2 候補は
    同一 variant に潰れて WAL replay で誤 skip される (機構レンズ nit)。"""
    for name, _cat, impl in W.CANDIDATES:
        assert "//" not in impl and "/*" not in impl, f"{name}: コメントを含む"


def test_implementations_reference_only_allowed_members():
    """closed-region 契約: 参照可能メンバは storage_/key_/rcdptr_ のみ (a./b. 経由)。"""
    for name, _cat, impl in W.CANDIDATES:
        for m in re.finditer(r"\b([ab])\.(\w+)", impl):
            assert m.group(2) in _MEMBER_IDX, f"{name}: 契約外メンバ {m.group(0)}"


# ==== 検疫通過 (fixture 骨格、write=False) =====================================

_TEMPLATE = """#pragma once
#include "storage.hh"

class TxExecutor {
 public:
  bool validationPhase() {
#ifndef SORT_VARIANT
#error "SORT_VARIANT must be defined"
#endif
    // EVOLVE-BLOCK-BEGIN silo-writeset-sort
    // izanagi Phase 3 (D41/phase3.md): coder の編集面はこの #if 枝のみ。
#if SORT_VARIANT
    sort(write_set_.begin(), write_set_.end());
#else
    sort(write_set_.begin(), write_set_.end());
#endif
    // EVOLVE-BLOCK-END silo-writeset-sort
    return true;
  }
};
"""


def _mk_template_dir() -> str:
    d = tempfile.mkdtemp(prefix="izanagi_s6sweep_")
    full = os.path.join(d, W.S.SOURCE_REL)
    os.makedirs(os.path.dirname(full), exist_ok=True)
    with open(full, "w", encoding="utf-8") as f:
        f.write(_TEMPLATE)
    return d


def test_all_candidates_pass_quarantine():
    d = _mk_template_dir()
    for name, _cat, impl in W.CANDIDATES:
        res, _b, _e, _wd = L.quarantine(d, impl, marker_id=W.S.MARKER_ID,
                                        source_rel=W.S.SOURCE_REL, write=False)
        assert res.passed, f"{name}: 機械生成候補が検疫 reject — {res.reason}"


# ==== campaign identity =======================================================

def test_workload_and_trial_baked_into_identity():
    """balanced / write-heavy / remeasure が別 campaign_id に解決される (identity の
    ハッシュ分離。spec_slug ラベルだけに依存しない — 機構レンズ should-fix)。"""
    ca = ident.campaign_id(W.config_for("balanced"))
    cb = ident.campaign_id(W.config_for("write-heavy"))
    cr = ident.campaign_id(W.config_for("balanced", trial=f"{W.TRIAL_MAIN}-remeasure1"))
    assert len({str(ca), str(cb), str(cr)}) == 3


def test_config_wires_s2_verify_and_space_provenance():
    cfg = W.config_for("balanced")
    assert cfg.search_config[SEARCH_CONFIG_VERIFY_KEY] == VERIFY_LEGACY_PLUS_S2
    assert cfg.search_config["generator"] == W.SPACE_VERSION
    assert cfg.search_config["ycsb"] == W.WORKLOADS["balanced"]
    assert cfg.ccbench_commit == W.PIN


def test_perf_is_p2_2_operating_point():
    """計測規模は p2_2 確定動作点 (配線規模 t4/100k ではない — 読解 2026-07-10 の
    決定的事実: 配線規模では contention が弱く施錠順序の影響が観測できない)。"""
    p = W.perf_for("balanced")
    assert (p.records, p.threads, p.extime, p.reps) == (1_000_000, 48, 3, 5)


def test_genome_flags():
    assert W._genome(0).flags["SORT_VARIANT"] == 0
    assert W._genome(1).flags["SORT_VARIANT"] == 1
    assert W._genome(1).flags["BACK_OFF"] == 1


# ==== 実装後レビューの是正 (2026-07-10) =======================================

def _tmp_layout():
    from campaign.layout import CampaignLayout
    return CampaignLayout(root=tempfile.mkdtemp(prefix="izanagi_s6sweep_lay_")).ensure()


def test_replay_outcome_distinguishes_commit_and_abort():
    """WAL replay skip 時、前 run の commit/abort を区別する (一律 'replayed' だと abort 点
    が完了サマリ/exit code から消える — 実装後レビュー should-fix)。"""
    from campaign import wal as _wal
    lay = _tmp_layout()
    _wal.log(lay, "v-commit", W.STAGE_COMMIT, W.ENV_TAG, {"fitness_tps": 1.0})
    _wal.log(lay, "v-abort", W.STAGE_ABORT, W.ENV_TAG, {"reason": "verify-red"})
    assert W._replay_outcome(lay, "v-commit") == "replayed-certified"
    assert W._replay_outcome(lay, "v-abort") == "replayed-aborted"
    assert W._replay_outcome(lay, "v-none") == "replayed-unknown"


def test_provenance_merges_existing_entries():
    """部分 --names 実行が既存の name→variant_id 対応を truncate しない (merge)。"""
    lay = _tmp_layout()
    W._write_provenance(lay, "balanced", W.TRIAL_MAIN,
                        {"k_asc": {"variant_id": "v1", "category": "full-order",
                                   "src_token": "s1", "outcome": "certified"}})
    W._write_provenance(lay, "balanced", W.TRIAL_MAIN,
                        {"stock": {"variant_id": "v0", "category": "stock",
                                   "src_token": "stock", "outcome": "certified"}})
    import json as _json
    with open(os.path.join(lay.root, "reports", "s6_sort_sweep_provenance.json"),
              encoding="utf-8") as f:
        doc = _json.load(f)
    assert set(doc["entries"]) == {"k_asc", "stock"}
    assert doc["entries"]["k_asc"]["variant_id"] == "v1"
    # stock の実効 comparator が自蔵される (PIN+patch を辿らなくても監査できる)
    assert "operator<" in doc["entries"]["stock"]["implementation"]


def test_floor_uncalibrated_fails_closed():
    """退化点は stock 非依存で無条件 True。比較材料欠損も True (fails-closed)。"""
    degen = {"category": "degenerate", "abort_rate": 0.01}
    ok = {"category": "full-order", "abort_rate": 0.10}
    calm = {"category": "full-order", "abort_rate": 0.05}
    stock = {"category": "stock", "abort_rate": 0.04}
    assert W._floor_uncalibrated(degen, None)          # stock 欠落でも退化点は True
    assert W._floor_uncalibrated(degen, stock)
    assert W._floor_uncalibrated(ok, stock)            # 0.10 > 2.0 * 0.04
    assert not W._floor_uncalibrated(calm, stock)      # 0.05 <= 0.08
    assert W._floor_uncalibrated(ok, None)             # stock 欠落 → fails-closed
    assert W._floor_uncalibrated({"category": "full-order", "abort_rate": None}, stock)
