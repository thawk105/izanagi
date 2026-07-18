# -*- coding: utf-8 -*-
"""F7 検証意味論 (V1 source blob / V2 transition / V3 二層未知性) + launch_validate の攻撃 matrix。

RV-verify レーン。tmp git repo に意味論的に valid な v1→g1 を組み (build_valid_semantic_g1)、
各意味論を 1 つずつ破って fail-closed を確認する。実 repo の output/s8b-freeze/ には書かない。
pytest 専用 (tmp_path fixture 依存、README allowlist 記載)。
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

import pytest

_HERE = os.path.dirname(os.path.abspath(__file__))
_ORCH = os.path.dirname(_HERE)
_ROOT = os.path.dirname(_ORCH)
sys.path.insert(0, _ORCH)
sys.path.insert(0, _HERE)

from campaign import s8b_ratified_freeze as M  # noqa: E402
from campaign import s8b_holdout_freeze as HF  # noqa: E402
import test_s8b_ratified_freeze as B  # noqa: E402  (fixture 共用)

_REAL_V1 = Path(_ROOT) / "output" / "s8b-freeze" / "holdout_freeze.json"


def _need_v1():
    # trust root 不在で skip すると本ファイルの攻撃 matrix が丸ごと緑扱いになる (failures F9 型、
    # codex 相談 2026-07-18 C-10)。実 v1 freeze は repo 同梱の恒久 artifact なので不在 = fail。
    if not _REAL_V1.is_file():
        pytest.fail(f"実 v1 freeze が無い (trust root 不在): {_REAL_V1}")


# --------------------------------------------------------------------------
# 正常系
# --------------------------------------------------------------------------

def test_semantic_happy_path_loads_and_launch_validates(tmp_path):
    _need_v1()
    root, gen_sha, gen_rel, _g1 = B.build_valid_semantic_g1(tmp_path)
    freeze = M.load_ratified_freeze(root)
    assert freeze.generation_number == 1
    lv = M.launch_validate(freeze, root)
    assert isinstance(lv, M.LaunchValidatedFreeze)
    assert lv.activation_head == freeze.activation_head
    assert lv.ratified is freeze


# --------------------------------------------------------------------------
# V1 — source blob + G^==frozen_at_head + closure
# --------------------------------------------------------------------------

def test_source_blob_mismatch_rejected(tmp_path):
    _need_v1()
    def mut(g1):
        g1["generator"] = {"path": g1["generator"]["path"], "sha256": "a" * 64}
    root, *_ = B.build_valid_semantic_g1(tmp_path, mutate_g1=mut)
    with pytest.raises(M.RatifiedFreezeError) as ei:
        M.load_ratified_freeze(root)
    assert ei.value.reason == "source-blob-mismatch"


def test_design_source_worktree_drift_still_loads(tmp_path):
    _need_v1()
    # V5 (陽性テスト): design_source が指す docs 系 file の worktree copy を未 commit で
    # 改変しても load_ratified_freeze は成功する。V1b は frozen_at_head の **blob bytes** を
    # 照合するため worktree drift に非依存 (D5' の意図)。design_source は closure でも
    # floor_protocol/floor_source でも namespace (output/s8b-freeze/) でもないため、dirty
    # 拒否 (closure-dirty / namespace-dirty) の経路には触れない。
    #
    # 変異 = V1b の blob 読みを worktree 読み化 → 改変後 bytes が記録 sha と食い違い
    # source-blob-mismatch で落ち、この陽性テストが赤になる。
    root, _gen_sha, _gen_rel, g1 = B.build_valid_semantic_g1(tmp_path)
    ds_path = g1["design_source"]["path"]         # docs 系 file (closure/namespace 外)
    assert not ds_path.startswith(M.FREEZE_DIR)    # namespace-dirty 経路に触れないことの前提
    target = root / ds_path
    assert target.is_file()
    # worktree copy に未 commit の drift を注入 (blob は不変のまま)。
    target.write_bytes(target.read_bytes() + b"\n# uncommitted worktree drift\n")

    freeze = M.load_ratified_freeze(root)          # blob 照合なので成功するのが正
    assert isinstance(freeze, M.RatifiedFreeze)
    assert freeze.generation_number == 1


def test_frozen_at_head_not_generation_parent_rejected(tmp_path):
    _need_v1()
    def mut(g1):
        g1["frozen_at_head"] = "0" * 40  # 形式は妥当だが G^ でない
    root, *_ = B.build_valid_semantic_g1(tmp_path, mutate_g1=mut)
    with pytest.raises(M.RatifiedFreezeError) as ei:
        M.load_ratified_freeze(root)
    assert ei.value.reason == "frozen-at-head-mismatch"


def test_generation_commit_merge_rejected(tmp_path):
    _need_v1()
    # 世代 file を merge commit で導入する (両親に g1 は不在)。structural 層の
    # _assert_candidate_commit が merge を拒否する (generation-commit-merge)。
    root = _build_merge_introduced_g1(tmp_path)
    with pytest.raises(M.RatifiedFreezeError) as ei:
        M.resolve_active_generation(root)
    assert ei.value.reason == "generation-commit-merge"


def test_closure_entry_absent_from_generation_tree_rejected(tmp_path):
    _need_v1()
    def mut(g1):
        g1["measurement_closure"].append(
            {"canonical_path": "output/env/floor/missing.json", "sha256": "b" * 64}
        )
    root, *_ = B.build_valid_semantic_g1(tmp_path, mutate_g1=mut)
    with pytest.raises(M.RatifiedFreezeError) as ei:
        M.load_ratified_freeze(root)
    assert ei.value.reason == "closure-not-in-generation"


def test_closure_bytes_sha_mismatch_rejected(tmp_path):
    _need_v1()
    def mut(g1):
        g1["measurement_closure"][0]["sha256"] = "c" * 64  # bytes は改竄せず記録 sha を偽る
    root, *_ = B.build_valid_semantic_g1(tmp_path, mutate_g1=mut)
    with pytest.raises(M.RatifiedFreezeError) as ei:
        M.load_ratified_freeze(root)
    assert ei.value.reason == "closure-sha-mismatch"


def test_env_tag_unknown_rejected(tmp_path):
    _need_v1()
    def mut(g1):
        g1["env_tag"] = "mars-rover-unregistered"
    root, *_ = B.build_valid_semantic_g1(tmp_path, mutate_g1=mut)
    with pytest.raises(M.RatifiedFreezeError) as ei:
        M.load_ratified_freeze(root)
    assert ei.value.reason == "env-tag-unknown"


# --------------------------------------------------------------------------
# V2 — transition table (F5 JSON Pointer 完全列挙)
# --------------------------------------------------------------------------

@pytest.mark.parametrize("mut", [
    lambda g1: g1.__setitem__("what", "tampered what"),           # protected top-level
    lambda g1: g1.__setitem__("confirmed_by", "attacker"),        # protected
    lambda g1: g1.__setitem__("match_convention", "loosened"),    # protected
    lambda g1: g1.__setitem__("scope_note", "tampered scope"),    # protected
    lambda g1: g1["derangement"].__setitem__("rr80", "rr80"),     # protected nested
])
def test_transition_out_of_enumeration_diff_rejected(tmp_path, mut):
    _need_v1()
    root, *_ = B.build_valid_semantic_g1(tmp_path, mutate_g1=mut)
    with pytest.raises(M.RatifiedFreezeError) as ei:
        M.load_ratified_freeze(root)
    assert ei.value.reason == "transition-violation"


def test_transition_gn_to_gn1_env_tag_change_rejected_unit():
    # gN→gN+1 の transition table は env_tag を allowed に含めない (環境が変わる = 別実験)。
    # 登録済み代替 env_tag が 1 つしか無く V1c が先に発火するため、transition table を直接駆動する。
    prev = {"env_tag": "linux-baremetal", "floor": None}
    nxt = {"env_tag": "linux-baremetal-2", "floor": None}
    with pytest.raises(M.RatifiedFreezeError) as ei:
        M._assert_transition(prev, nxt, M._TRANSITION_GN_TO_GN1, label="g1→g2")
    assert ei.value.reason == "transition-violation"


def test_transition_gn_to_gn1_allows_floor_change_unit():
    # 逆に floor/floor_protocol/measurement_closure/header は gN→gN+1 で変わってよい (正常系)。
    prev = {"env_tag": "linux-baremetal", "floor": None, "generation_number": 1}
    nxt = {"env_tag": "linux-baremetal", "floor": {"rr80": 1.0}, "generation_number": 2}
    M._assert_transition(prev, nxt, M._TRANSITION_GN_TO_GN1, label="g1→g2")  # 例外なし


@pytest.mark.parametrize("field", ["holdouts", "derangement"])
def test_transition_gn_to_gn1_forbids_measurement_field_rewrite_unit(field):
    # V4: gN→gN+1 で /holdouts・/derangement (workload identity) を書き換える世代対は拒否する。
    # 両者は _TRANSITION_GN_TO_GN1 の列挙外 (protected) — 列挙外 pointer の変化は
    # transition-violation。header (generation_number) だけが allowed で変わる。
    # `field="holdouts"` は「_TRANSITION_GN_TO_GN1 に /holdouts を追加する」変異を殺す
    # (allowed に入ると /holdouts の書換えが素通りし、この case が赤になる)。
    prev = {
        "generation_number": 1,
        "holdouts": {"rr80": {"records": 1000000}},
        "derangement": {"rr80": "rr20"},
    }
    nxt = {
        "generation_number": 2,  # allowed (header) — 変わってよい
        "holdouts": {"rr80": {"records": 1000000}},
        "derangement": {"rr80": "rr20"},
    }
    # 対象 field の nested leaf を 1 つ書き換える (列挙外の diff)。
    if field == "holdouts":
        nxt["holdouts"] = {"rr80": {"records": 2000000}}
    else:
        nxt["derangement"] = {"rr80": "rr50"}
    with pytest.raises(M.RatifiedFreezeError) as ei:
        M._assert_transition(prev, nxt, M._TRANSITION_GN_TO_GN1, label="g1→g2")
    assert ei.value.reason == "transition-violation"


def test_chain_g2_env_tag_unchanged_loads(tmp_path):
    _need_v1()
    # env_tag を保てば g2 は正常 load される (gN→gN+1 allowed の正常系)。
    root, g1_sha, g1_rel, g1 = B.build_valid_semantic_g1(tmp_path)
    _build_g2(root, g1, g1_sha, mutate_g2=None)
    freeze = M.load_ratified_freeze(root)
    assert freeze.generation_number == 2


# --------------------------------------------------------------------------
# V3 — 二層未知性 + closure (launch_validate)
# --------------------------------------------------------------------------

def test_layer1_snapshot_tamper_rejected_unit():
    # holdouts は transition で protected のため、層1 単体を直接駆動して改竄検出を確認する。
    doc = json.loads(_REAL_V1.read_bytes()) if _REAL_V1.is_file() else None
    if doc is None:
        pytest.fail("実 v1 freeze が無い (trust root 不在 — skip すると攻撃 matrix が緑化する。failures F9 型)")
    name = next(iter(HF.HOLDOUTS))
    doc["holdouts"][name]["unknownness_check"]["zero_hit_output_sha256"] = "e" * 64
    with pytest.raises(M.RatifiedFreezeError) as ei:
        M._verify_snapshot_layer1(doc)
    assert ei.value.reason == "layer1-snapshot-mismatch"


def test_undeclared_hit_outside_closure_rejected(tmp_path):
    _need_v1()
    root, *_ = B.build_valid_semantic_g1(tmp_path)
    freeze = M.load_ratified_freeze(root)
    # closure 外の untracked ファイルに rr80 params を仕込む → 現 search に未申告 hit が出る。
    (root / "sneaky_measurement.txt").write_bytes(B._RR80_PARAMS)
    with pytest.raises(M.RatifiedFreezeError) as ei:
        M.launch_validate(freeze, root)
    assert ei.value.reason == "closure-hit-mismatch"


def test_declared_closure_hit_absent_from_search_rejected(tmp_path):
    _need_v1()
    # closure に「search 対象外 (output/s8b-freeze/ 配下) だが rr80 params を持つ」artifact を
    # 追加宣言する (V1d は満たす。base コミット済み・sha 一致)。期待 hit に出るが search は
    # output/s8b-freeze/ を除外するため現 hit に現れない → closure-hit-mismatch。
    excluded_path = "output/s8b-freeze/hidden_measure.json"
    root, *_ = B.build_valid_semantic_g1(
        tmp_path, extra_closure=[(excluded_path, B._RR80_PARAMS)]
    )
    freeze = M.load_ratified_freeze(root)
    with pytest.raises(M.RatifiedFreezeError) as ei:
        M.launch_validate(freeze, root)
    assert ei.value.reason == "closure-hit-mismatch"


def test_per_holdout_no_crosstalk(tmp_path):
    _need_v1()
    # V1: per-holdout の hit 集合比較が「どの holdout が不一致か」を正しく帰属することを固定する。
    #
    # closure bytes pin + dirty 拒否の下では、全 holdout を束ねた union 比較と per-holdout
    # 比較は「拒否するか否か」では等価 (未申告 hit が 1 つでもあれば両者とも closure-hit-mismatch)。
    # 差が出るのは例外に載る**帰属情報**だけ: per-holdout は不一致 holdout 名 (rr80) を前置し、
    # union は名前を持たない。よってこのテストは reason ではなく帰属 (holdout 名) を検査する。
    #
    # 未申告 hit ファイルは holdout 名を含まない名前 (extra_conflict.txt) にする。これで
    # "rr80" が例外 message に現れる唯一の経路が per-holdout 帰属 (f"{name}: ...") に限定され、
    # ファイル名の偶然一致で素通りしない。per-holdout→union 化の変異は、帰属が消えて
    # "rr80" が message から失われるためこのテストで殺せる (下記 assert が赤になる)。
    root, *_ = B.build_valid_semantic_g1(tmp_path)
    freeze = M.load_ratified_freeze(root)
    # closure は f80/f20 両方宣言済み。rr80 params を持つ untracked hit を rr80 名を含まない
    # ファイル名で追加し、rr80 の hit 集合だけを未申告で不一致にする (rr20 は一致のまま)。
    (root / "extra_conflict.txt").write_bytes(B._RR80_PARAMS)
    with pytest.raises(M.RatifiedFreezeError) as ei:
        M.launch_validate(freeze, root)
    message = str(ei.value)
    assert ei.value.reason == "closure-hit-mismatch"
    # 帰属検査: 不一致は rr80 の hit 集合。ファイル名 (extra_conflict.txt) も未申告 hit の
    # path も "rr80" を含まないため、message 中の "rr80" は per-holdout 帰属からしか来ない。
    assert "rr80" in message, message
    # 未申告ファイルが帰属に載る (per-holdout 検査が現/期待の差を取れている)。
    assert "extra_conflict.txt" in message, message


def test_enumeration_digest_shift_rejected(tmp_path, monkeypatch):
    _need_v1()
    root, *_ = B.build_valid_semantic_g1(tmp_path)
    freeze = M.load_ratified_freeze(root)
    real_search = HF.search_repository

    def racing_search(r=root, files=None):
        # search 実行中に untracked ファイルを増やし、列挙前後 digest を食い違わせる。
        (Path(r) / "added_mid_scan.txt").write_text("x\n", encoding="utf-8")
        return real_search(r, files)

    monkeypatch.setattr(M._hf, "search_repository", racing_search)
    with pytest.raises(M.RatifiedFreezeError) as ei:
        M.launch_validate(freeze, root)
    assert ei.value.reason == "enumeration-shifted"


def test_positive_control_not_hit_rejected(tmp_path):
    _need_v1()
    # 陽性対照 (rr50) file の内容を無害化する (rr50 params を含まない bytes に差し替える)。
    # search は worktree を直読みするため、この改変だけで陽性対照が 0 hit になる。
    root, *_ = B.build_valid_semantic_g1(tmp_path)
    freeze = M.load_ratified_freeze(root)
    (root / "positive_control.txt").write_bytes(b"neutralized, no ycsb params here\n")
    with pytest.raises(M.RatifiedFreezeError) as ei:
        M.launch_validate(freeze, root)
    assert ei.value.reason == "search-not-operational"


def test_activation_head_moved_rejected(tmp_path):
    _need_v1()
    root, *_ = B.build_valid_semantic_g1(tmp_path)
    freeze = M.load_ratified_freeze(root)
    # load 後に HEAD を進める (無害な commit)。launch 直前の H 一致再確認で拒否。
    (root / "later.txt").write_text("later\n", encoding="utf-8")
    B._commit(root, "later commit", "claude")
    with pytest.raises(M.RatifiedFreezeError) as ei:
        M.launch_validate(freeze, root)
    assert ei.value.reason == "activation-head-moved"


# --------------------------------------------------------------------------
# g2 / 追加 closure 用の repo ビルダ
# --------------------------------------------------------------------------

def _build_g2(root: Path, g1: dict, g1_sha: str, *, mutate_g2):
    """有効 g1 repo の上に g2 (+ approval/pointer) を積む。frozen_at_head=G2^、closure は g1 と同じ。"""
    frozen = B._git(root, "rev-parse", "HEAD")  # G2 の親 = 現 HEAD (approval commit A1)
    g2 = dict(g1)
    g2["generation_number"] = 2
    g2["supersedes_sha256"] = g1_sha
    g2["frozen_at_head"] = frozen
    # closure/floor_protocol/floor_source は g1 と同一 (既に G tree/worktree に実在)。
    if mutate_g2 is not None:
        mutate_g2(g2)
    g2_raw = json.dumps(g2, ensure_ascii=False).encode("utf-8")
    B._write(root, B._gen_rel(2), g2_raw)
    B._commit(root, "candidate g2", "claude-opus")  # G2
    g2_sha = B._sha(g2_raw)
    B._approve_and_point(root, 2, g2_sha, B._gen_rel(2), _pointer_sha_of_g1(root))
    return g2_sha


def _pointer_sha_of_g1(root: Path) -> str:
    """g1 の active pointer sha (parent chain 用) を H tree から復元する。"""
    out = B._git(root, "ls-tree", "-r", "--name-only", "HEAD", "--", M.ACTIVE_DIR)
    ptrs = [line for line in out.splitlines() if line.endswith(".json")]
    assert len(ptrs) == 1, ptrs
    return Path(ptrs[0]).stem


def _build_merge_introduced_g1(tmp_path: Path) -> Path:
    """g1 世代 file を merge commit で導入する repo を組む (両親に g1 不在)。

    structural 層 (_assert_candidate_commit) が merge の世代導入を拒否することの確認用。
    build_valid_semantic_g1 の base までを組んだ後、側枝を切り、merge commit で g1 を追加する。"""
    root, _gen_sha, _gen_rel, g1 = B.build_valid_semantic_g1(tmp_path)
    # 既存 g1 (非 merge 導入) を取り除いた歴史を新規に組み直すのは重いので、別 repo を base から
    # 作り直す: build_valid_semantic_g1 は approval まで済ませているため、ここでは g1 の
    # merge 導入を別途検証する専用 repo を最小構成で組む。
    root2 = tmp_path / "merge_repo"
    root2.mkdir()
    B._init_repo(root2)
    if B._REAL_V1.is_file():
        B._write(root2, M.V1_FREEZE_PATH, B._REAL_V1.read_bytes())
    (root2 / "README.md").write_text("m\n", encoding="utf-8")
    base = B._commit(root2, "base", "claude-base")
    B._git(root2, "checkout", "-q", "-b", "b1")
    (root2 / "a.txt").write_text("a\n", encoding="utf-8")
    B._commit(root2, "b1", "claude")
    B._git(root2, "checkout", "-q", base)
    B._git(root2, "checkout", "-q", "-b", "b2")
    (root2 / "b.txt").write_text("b\n", encoding="utf-8")
    B._commit(root2, "b2", "claude")
    B._git(root2, "checkout", "-q", "b1")
    B._git(root2, "merge", "-q", "--no-commit", "--no-ff", "b2")
    # merge commit の中で g1 を追加する (両親に g1 不在 → 導入 commit = merge)。
    g1_raw = json.dumps(g1, ensure_ascii=False).encode("utf-8")
    B._write(root2, B._gen_rel(1), g1_raw)
    B._commit(root2, "merge introduces g1", "claude-opus")
    g1_sha = B._sha(g1_raw)
    B._approve_and_point(root2, 1, g1_sha, B._gen_rel(1), None)
    return root2
