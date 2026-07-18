# -*- coding: utf-8 -*-
"""s8b_ratified_freeze の承認束縛 machinery の攻撃 matrix テスト (F6a、RV-core)。

使い捨て tmp git repo に v1→g1 の承認・activation を組み、各攻撃を注入して fail-closed を
確認する。実 repo の output/s8b-freeze/ には一切書かない (発効の禁止)。pytest 専用
(tmp_path fixture 依存、README allowlist 記載)。
"""
from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

_HERE = os.path.dirname(os.path.abspath(__file__))
_ORCH = os.path.dirname(_HERE)
_ROOT = os.path.dirname(_ORCH)
sys.path.insert(0, _ORCH)

from campaign import s8b_ratified_freeze as M  # noqa: E402

_REAL_V1 = Path(_ROOT) / "output" / "s8b-freeze" / "holdout_freeze.json"


# --------------------------------------------------------------------------
# tmp git repo ヘルパ (test_s8b_holdout_freeze.py の _git/_commit_all を踏襲)
# --------------------------------------------------------------------------

def _git(root: Path, *args: str, stdin: bytes | None = None) -> str:
    return subprocess.run(
        ["git", *args], cwd=root, check=True, input=stdin,
        stdout=subprocess.PIPE, stderr=subprocess.PIPE,
    ).stdout.decode("utf-8").strip()


def _init_repo(root: Path) -> None:
    _git(root, "init", "-q")
    _git(root, "config", "user.name", "fixture")
    _git(root, "config", "user.email", "fixture@example.invalid")
    _git(root, "config", "commit.gpgsign", "false")


def _commit(root: Path, subject: str, ai_agent: str) -> str:
    """全 add + 単一 commit。message は subject 段落 + `AI-Agent: <ai_agent>` trailer。"""
    _git(root, "add", "-A")
    message = f"{subject}\n\nAI-Agent: {ai_agent}".encode("utf-8")
    _git(root, "commit", "-q", "-F", "-", stdin=message)
    return _git(root, "rev-parse", "HEAD")


def _commit_raw(root: Path, message: str) -> str:
    """message を逐語で commit する (trailer 併記・大小文字違いの注入用)。"""
    _git(root, "add", "-A")
    _git(root, "commit", "-q", "-F", "-", stdin=message.encode("utf-8"))
    return _git(root, "rev-parse", "HEAD")


def _commit_verbatim(root: Path, message: str) -> str:
    """message を --cleanup=verbatim で commit する (末尾空白等を byte 単位で保存)。

    git の既定 cleanup (strip/whitespace) は各行の末尾空白を落とすため、末尾空白付き
    trailer (`AI-Agent: none `) を注入する R3 攻撃では verbatim が必須。"""
    _git(root, "add", "-A")
    _git(root, "commit", "-q", "--cleanup=verbatim", "-F", "-",
         stdin=message.encode("utf-8"))
    return _git(root, "rev-parse", "HEAD")


def _write(root: Path, rel: str, raw: bytes) -> None:
    path = root / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(raw)


def _sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _gen_raw(number: int, supersedes: str) -> bytes:
    """exact v2 schema を満たす世代 bytes (内容は placeholder、本レーンは内容非検査)。"""
    doc = {key: "x" for key in M.V2_TOP_LEVEL_KEYS}
    doc["schema_version"] = "8b-holdout-freeze/v2"
    doc["generation_number"] = number
    doc["supersedes_sha256"] = supersedes
    doc["measurement_closure"] = []
    return json.dumps(doc, ensure_ascii=False).encode("utf-8")


def _approval_raw(gen_sha: str) -> bytes:
    return M._canonical_bytes({
        "generation_sha256": gen_sha, "approver": "user",
        "approved_at": "2026-07-18T00:00:00Z", "scope": "s8b-holdout",
    })


def _pointer_raw(number: int, path: str, gen_sha: str, parent, approval_sha: str) -> bytes:
    return M._canonical_bytes({
        "generation_number": number, "path": path, "sha256": gen_sha,
        "parent_active_sha256": parent, "approval_sha256": approval_sha,
    })


def _gen_rel(number: int) -> str:
    return f"output/s8b-freeze/holdout_freeze.v2.g{number}.json"


def _base_repo(tmp_path: Path) -> Path:
    """v1 holdout_freeze.json を載せた base commit までを組む。"""
    root = tmp_path / "repo"
    root.mkdir()
    _init_repo(root)
    (root / "README.md").write_text("fixture\n", encoding="utf-8")
    if _REAL_V1.is_file():
        _write(root, M.V1_FREEZE_PATH, _REAL_V1.read_bytes())
    _commit(root, "base", "claude-base")
    return root


def _add_generation(root: Path, number: int, supersedes: str):
    """世代 file を導入 commit G (AI trailer) で載せ、(gen_sha, gen_rel) を返す。"""
    rel = _gen_rel(number)
    raw = _gen_raw(number, supersedes)
    _write(root, rel, raw)
    _commit(root, f"candidate g{number}", "claude-opus")
    return _sha(raw), rel


def _approve_and_point(root: Path, number: int, gen_sha: str, gen_rel: str,
                       parent_ptr_sha, *, ai_agent: str = "none"):
    """approval + active pointer を同一 commit A (none) で載せ、(approval_sha, ptr_sha) を返す。"""
    approval_raw = _approval_raw(gen_sha)
    approval_sha = _sha(approval_raw)
    approval_rel = f"{M.APPROVAL_DIR}/{gen_sha}.json"
    _write(root, approval_rel, approval_raw)

    ptr_raw = _pointer_raw(number, gen_rel, gen_sha, parent_ptr_sha, approval_sha)
    ptr_sha = _sha(ptr_raw)
    ptr_rel = f"{M.ACTIVE_DIR}/{ptr_sha}.json"
    _write(root, ptr_rel, ptr_raw)

    _commit(root, f"approve g{number}", ai_agent)
    return approval_sha, ptr_sha


def _valid_g1(tmp_path: Path):
    """v1→g1 の正常な承認・activation を組み、root と主要 hash を返す (structural placeholder)。

    世代 document は placeholder (内容非検査) なので resolve_active_generation (structural)
    は通るが load_ratified_freeze (semantics 充填済み) は通らない。意味論の happy path は
    build_valid_semantic_g1 を使う。"""
    root = _base_repo(tmp_path)
    gen_sha, gen_rel = _add_generation(root, 1, M.V1_FREEZE_SHA256)
    approval_sha, ptr_sha = _approve_and_point(root, 1, gen_sha, gen_rel, None)
    return root, gen_sha, gen_rel, approval_sha, ptr_sha


# --------------------------------------------------------------------------
# 意味論 (V1〜V3) を満たす valid g1 fixture — RV-verify の happy path 共用。
# --------------------------------------------------------------------------

_RR80_PARAMS = b"ycsb_rr" + b"atio=80 ycsb_zipf_skew=0.9 ycsb_rmw=0\n"
_RR20_PARAMS = b"ycsb_rr" + b"atio=20 ycsb_zipf_skew=0.9 ycsb_rmw=0\n"
_RR50_PARAMS = b"ycsb_rratio=50 ycsb_zipf_skew=0.9 ycsb_rmw=0\n"  # 陽性対照
_FLOOR_PROTOCOL_STUB = b'{"floor_protocol": "stub", "n": 1}\n'    # strict parse 可能・holdout params 無し
_FLOOR_SOURCE_STUB = b"# floor source stub\n"


def _real_bytes(rel: str) -> bytes:
    return (Path(_ROOT) / rel).read_bytes()


def _make_ccbench_submodule(root: Path) -> None:
    """external/ccbench 入れ子 git repo を作る (enumerate_repository_files の submodule 枝用)。"""
    sub = root / "external" / "ccbench"
    sub.mkdir(parents=True)
    _init_repo(sub)
    (sub / "ccbench.txt").write_text("ccbench fixture (no ycsb params)\n", encoding="utf-8")
    _git(sub, "add", "-A")
    _git(sub, "commit", "-q", "-F", "-", stdin=b"ccbench base\n\nAI-Agent: fixture")


def build_valid_semantic_g1(tmp_path: Path, *, mutate_g1=None, extra_closure=None,
                            floor_source_bytes=None):
    """V1 (source blob + G^==frozen_at_head + closure) / V2 (transition) / V3 (層1/層2) を
    すべて満たす v1→g1 を tmp git repo に組む。(root, gen_sha, gen_rel, g1) を返す。

    mutate_g1(g1) が与えられれば直列化前に g1 dict を破壊できる (負例注入用)。
    extra_closure = [(path, bytes), ...] は base コミットに載せた上で measurement_closure に
    正しい sha で追加する (V1d を満たす追加 closure 経由の負例用)。
    floor_source_bytes を与えると floor_source の blob 内容をそれで差し替える (既定は
    ``_FLOOR_SOURCE_STUB``)。oracle W4 が floor_source を「binaries section を持つ floor
    artifact」として消費するため、その正例を組む拡張点。ycsb params を含まない bytes に
    限る (含むと未申告 hit で launch_validate が落ちる)。

    実 v1 freeze bytes を trust root に据え (sha == V1_FREEZE_SHA256)、g1 は v1 doc から
    protected field を継承しつつ allowed field (schema_version/frozen_at_head/design_source.sha256/
    generator.sha256/env_tag/floor_protocol/floor_source/measurement_closure/header) を書く。
    closure 2 本 (rr80/rr20 params) は search で各 holdout に conjunction hit し、closure 導出と
    完全一致する。陽性対照 (rr50) と protocol/source stub も置く。"""
    root = tmp_path / "repo"
    root.mkdir()
    _init_repo(root)

    v1_raw = _REAL_V1.read_bytes()
    v1_doc = json.loads(v1_raw)
    _write(root, M.V1_FREEZE_PATH, v1_raw)

    ka_path = v1_doc["known_axes_freeze"]["path"]      # protected (実 bytes が v1 sha と一致)
    _write(root, ka_path, _real_bytes(ka_path))
    ds_path = v1_doc["design_source"]["path"]
    gen_path = v1_doc["generator"]["path"]
    ds_bytes = b"# design source stub (g1 overrides sha)\n"
    gen_bytes = b"# generator stub (g1 overrides sha)\n"
    _write(root, ds_path, ds_bytes)
    _write(root, gen_path, gen_bytes)

    f80 = "output/env/floor/rr80.json"
    f20 = "output/env/floor/rr20.json"
    fp = "output/env/floor/protocol.json"
    fs = "output/env/floor/source.py"
    fs_bytes = _FLOOR_SOURCE_STUB if floor_source_bytes is None else floor_source_bytes
    _write(root, f80, _RR80_PARAMS)
    _write(root, f20, _RR20_PARAMS)
    _write(root, fp, _FLOOR_PROTOCOL_STUB)
    _write(root, fs, fs_bytes)
    _write(root, "positive_control.txt", _RR50_PARAMS)
    (root / "README.md").write_text("fixture\n", encoding="utf-8")

    for extra_path, extra_bytes in (extra_closure or []):
        _write(root, extra_path, extra_bytes)

    # external/ccbench 入れ子 git repo (search_repository の enumerate 対象。params 無し)。
    _make_ccbench_submodule(root)

    frozen = _commit(root, "base (frozen_at_head)", "claude-base")

    g1 = dict(v1_doc)
    g1["schema_version"] = "8b-holdout-freeze/v2"
    g1["frozen_at_head"] = frozen
    g1["generation_number"] = 1
    g1["supersedes_sha256"] = M.V1_FREEZE_SHA256
    g1["design_source"] = {"path": ds_path, "sha256": _sha(ds_bytes)}
    g1["generator"] = {"path": gen_path, "sha256": _sha(gen_bytes)}
    g1["env_tag"] = "linux-baremetal"
    g1["floor_protocol"] = {"path": fp, "sha256": _sha(_FLOOR_PROTOCOL_STUB)}
    g1["floor_source"] = {"path": fs, "sha256": _sha(fs_bytes)}
    g1["measurement_closure"] = [
        {"canonical_path": f80, "sha256": _sha(_RR80_PARAMS)},
        {"canonical_path": f20, "sha256": _sha(_RR20_PARAMS)},
    ]
    for extra_path, extra_bytes in (extra_closure or []):
        g1["measurement_closure"].append(
            {"canonical_path": extra_path, "sha256": _sha(extra_bytes)}
        )
    if mutate_g1 is not None:
        mutate_g1(g1)
    g1_raw = json.dumps(g1, ensure_ascii=False).encode("utf-8")
    _write(root, _gen_rel(1), g1_raw)
    _commit(root, "candidate g1", "claude-opus")     # G, parent == frozen
    gen_sha = _sha(g1_raw)
    _approve_and_point(root, 1, gen_sha, _gen_rel(1), None)
    return root, gen_sha, _gen_rel(1), g1


# --------------------------------------------------------------------------
# 正常系
# --------------------------------------------------------------------------

def test_happy_path_resolves_and_loads(tmp_path):
    if not _REAL_V1.is_file():
        pytest.fail("実 v1 freeze が無い (trust root 不在 — skip すると攻撃 matrix が緑化する。failures F9 型)")
    root, gen_sha, gen_rel, _g1 = build_valid_semantic_g1(tmp_path)
    res = M.resolve_active_generation(root)
    assert res.generation_number == 1
    assert res.generation_sha256 == gen_sha
    assert res.generation_path == gen_rel
    assert res.activation_head == _git(root, "rev-parse", "HEAD")

    freeze = M.load_ratified_freeze(root)
    assert isinstance(freeze, M.RatifiedFreeze)
    assert freeze.generation_number == 1
    assert freeze.sha256 == gen_sha
    assert freeze.activation_head == res.activation_head
    assert freeze.document["schema_version"] == "8b-holdout-freeze/v2"


def test_legacy_freeze_binds_v1_by_constant(tmp_path):
    if not _REAL_V1.is_file():
        pytest.fail("実 v1 freeze が無い (trust root 不在 — skip すると攻撃 matrix が緑化する。failures F9 型)")
    root = _base_repo(tmp_path)
    legacy = M.load_legacy_freeze(root)
    assert isinstance(legacy, M.LegacyFreeze)
    assert legacy.sha256 == M.V1_FREEZE_SHA256
    # v2 型ではない (candidate/legacy を実走 v2 経路へ流せない型分離)。
    assert not isinstance(legacy, M.RatifiedFreeze)


def test_legacy_freeze_rejects_wrong_bytes(tmp_path):
    root = tmp_path / "r"
    root.mkdir()
    _init_repo(root)
    _write(root, M.V1_FREEZE_PATH, b"{\"tampered\": true}")
    _commit(root, "v1 tamper", "claude")
    with pytest.raises(M.RatifiedFreezeError) as ei:
        M.load_legacy_freeze(root)
    assert ei.value.reason == "legacy-hash"


# --------------------------------------------------------------------------
# approval / pointer / hash の不整合
# --------------------------------------------------------------------------

def test_missing_approval_no_active(tmp_path):
    # candidate 世代のみ (approval/pointer 無し) → active なし (consumer に渡せない型分離)。
    root = _base_repo(tmp_path)
    _add_generation(root, 1, M.V1_FREEZE_SHA256)
    with pytest.raises(M.RatifiedFreezeError) as ei:
        M.resolve_active_generation(root)
    assert ei.value.reason == "no-active"


def test_pointer_references_absent_approval(tmp_path):
    root = _base_repo(tmp_path)
    gen_sha, gen_rel = _add_generation(root, 1, M.V1_FREEZE_SHA256)
    # pointer は存在しない approval_sha を参照 (approval file を載せない)。
    bogus_approval = "a" * 64
    ptr_raw = _pointer_raw(1, gen_rel, gen_sha, None, bogus_approval)
    ptr_sha = _sha(ptr_raw)
    _write(root, f"{M.ACTIVE_DIR}/{ptr_sha}.json", ptr_raw)
    _commit(root, "point only", "none")
    with pytest.raises(M.RatifiedFreezeError) as ei:
        M.resolve_active_generation(root)
    assert ei.value.reason == "pointer-approval"


def test_approval_filename_hash_mismatch(tmp_path):
    root = _base_repo(tmp_path)
    gen_sha, gen_rel = _add_generation(root, 1, M.V1_FREEZE_SHA256)
    approval_raw = _approval_raw(gen_sha)
    # filename を別 hash にする (内容 generation_sha256 と不一致)。
    _write(root, f"{M.APPROVAL_DIR}/{'b' * 64}.json", approval_raw)
    _commit(root, "bad approval name", "none")
    with pytest.raises(M.RatifiedFreezeError) as ei:
        M.resolve_active_generation(root)
    assert ei.value.reason == "approval-filename"


def test_pointer_content_hash_mismatch(tmp_path):
    root = _base_repo(tmp_path)
    gen_sha, gen_rel = _add_generation(root, 1, M.V1_FREEZE_SHA256)
    approval_sha, _ = _approve_and_point(root, 1, gen_sha, gen_rel, None)
    # 別世代 file を足すが pointer.sha256 は g1 のまま → path/sha 突き合わせで検出させる。
    # ここでは pointer.sha256 を壊した第二世代を作らず、pointer が指す sha を改ざん。
    # 直接 pointer の sha256 を別値にした pointer を第二 genesis 代わりに載せると型が変わるため、
    # 単純に「pointer.sha256 が世代 bytes hash と不一致」を作る。
    wrong = "c" * 64
    ptr_raw = _pointer_raw(1, gen_rel, wrong, None, approval_sha)
    ptr_sha = _sha(ptr_raw)
    _write(root, f"{M.ACTIVE_DIR}/{ptr_sha}.json", ptr_raw)
    _commit(root, "wrong sha pointer", "none")
    with pytest.raises(M.RatifiedFreezeError) as ei:
        M.resolve_active_generation(root)
    assert ei.value.reason in ("pointer-generation", "pointer-fork", "genesis-count")


# --------------------------------------------------------------------------
# 導入 commit / trailer / topology (C1-4/C1-6)
# --------------------------------------------------------------------------

def test_non_ancestry_user_commit_rejected(tmp_path):
    root, *_ = _valid_g1(tmp_path)
    head = _git(root, "rev-parse", "HEAD")
    # 別ブランチに未 merge の none commit を作る。
    _git(root, "checkout", "-q", "-b", "sidebranch")
    (root / "side.txt").write_text("s\n", encoding="utf-8")
    side = _commit(root, "side", "none")
    _git(root, "checkout", "-q", head)
    graph = M._commit_graph(head, root)
    with pytest.raises(M.RatifiedFreezeError) as ei:
        M._assert_user_commit(side, graph, root)
    assert ei.value.reason == "user-commit-ancestry"


def test_approval_commit_with_ai_trailer_rejected(tmp_path):
    root = _base_repo(tmp_path)
    gen_sha, gen_rel = _add_generation(root, 1, M.V1_FREEZE_SHA256)
    # approval commit を AI trailer にする (人間 commit でない)。
    with pytest.raises(M.RatifiedFreezeError) as ei:
        _approve_and_point(root, 1, gen_sha, gen_rel, None, ai_agent="claude-opus")
        M.resolve_active_generation(root)
    assert ei.value.reason == "user-commit-trailer"


def test_trailer_both_none_and_structured_rejected(tmp_path):
    root = _base_repo(tmp_path)
    gen_sha, gen_rel = _add_generation(root, 1, M.V1_FREEZE_SHA256)
    approval_raw = _approval_raw(gen_sha)
    approval_sha = _sha(approval_raw)
    _write(root, f"{M.APPROVAL_DIR}/{gen_sha}.json", approval_raw)
    ptr_raw = _pointer_raw(1, gen_rel, gen_sha, None, approval_sha)
    ptr_sha = _sha(ptr_raw)
    _write(root, f"{M.ACTIVE_DIR}/{ptr_sha}.json", ptr_raw)
    _commit_raw(root, "approve\n\nAI-Agent: none\nAI-Agent: claude-opus\n")
    with pytest.raises(M.RatifiedFreezeError) as ei:
        M.resolve_active_generation(root)
    assert ei.value.reason == "user-commit-trailer"


def test_trailer_case_or_space_variant_rejected(tmp_path):
    root = _base_repo(tmp_path)
    gen_sha, gen_rel = _add_generation(root, 1, M.V1_FREEZE_SHA256)
    approval_raw = _approval_raw(gen_sha)
    approval_sha = _sha(approval_raw)
    _write(root, f"{M.APPROVAL_DIR}/{gen_sha}.json", approval_raw)
    ptr_raw = _pointer_raw(1, gen_rel, gen_sha, None, approval_sha)
    ptr_sha = _sha(ptr_raw)
    _write(root, f"{M.ACTIVE_DIR}/{ptr_sha}.json", ptr_raw)
    # 小文字 key は逐語 `AI-Agent: none` でないため拒否。
    _commit_raw(root, "approve\n\nai-agent: none\n")
    with pytest.raises(M.RatifiedFreezeError) as ei:
        M.resolve_active_generation(root)
    assert ei.value.reason == "user-commit-trailer"


def test_trailer_none_trailing_space_rejected(tmp_path):
    # R3: approval commit の trailer 行が `AI-Agent: none ` (末尾空白 1 個)。
    # git interpret-trailers --parse は空白を丸めて "none" を返すため parse 側検査だけでは
    # 素通りする。_is_none_commit の raw 行 byte-for-byte 検査 (== "AI-Agent: none") のみが
    # これを拒否できる。この raw 検査を startswith 化する変異はこのテストで殺せる。
    root = _base_repo(tmp_path)
    gen_sha, gen_rel = _add_generation(root, 1, M.V1_FREEZE_SHA256)
    approval_raw = _approval_raw(gen_sha)
    approval_sha = _sha(approval_raw)
    _write(root, f"{M.APPROVAL_DIR}/{gen_sha}.json", approval_raw)
    ptr_raw = _pointer_raw(1, gen_rel, gen_sha, None, approval_sha)
    ptr_sha = _sha(ptr_raw)
    _write(root, f"{M.ACTIVE_DIR}/{ptr_sha}.json", ptr_raw)
    # 末尾空白付き trailer を verbatim で保存する (既定 cleanup は空白を落とす)。
    commit = _commit_verbatim(root, "approve\n\nAI-Agent: none \n")
    # 前提: raw に末尾空白が保存され、parse 側は "none" に丸める (両立で初めて攻撃が成立)。
    assert M._raw_ai_agent_lines(M._commit_message(commit, root)) == ["AI-Agent: none "]
    assert M._parsed_ai_agent_values(M._commit_message(commit, root), root) == ["none"]
    with pytest.raises(M.RatifiedFreezeError) as ei:
        M.resolve_active_generation(root)
    assert ei.value.reason == "user-commit-trailer"


def test_approval_commit_with_extra_file_rejected(tmp_path):
    root = _base_repo(tmp_path)
    gen_sha, gen_rel = _add_generation(root, 1, M.V1_FREEZE_SHA256)
    approval_raw = _approval_raw(gen_sha)
    approval_sha = _sha(approval_raw)
    _write(root, f"{M.APPROVAL_DIR}/{gen_sha}.json", approval_raw)
    ptr_raw = _pointer_raw(1, gen_rel, gen_sha, None, approval_sha)
    ptr_sha = _sha(ptr_raw)
    _write(root, f"{M.ACTIVE_DIR}/{ptr_sha}.json", ptr_raw)
    (root / "extra.txt").write_text("sneaky\n", encoding="utf-8")  # 余分ファイル
    _commit(root, "approve+extra", "none")
    with pytest.raises(M.RatifiedFreezeError) as ei:
        M.resolve_active_generation(root)
    assert ei.value.reason == "approval-commit-diff"


def test_generation_and_approval_same_commit_rejected(tmp_path):
    # 世代 + approval + pointer を一つの none commit に入れる (C1-4 単一 commit 迂回)。
    # 世代を none commit で導入した時点で provenance 虚偽として拒否される。
    root = _base_repo(tmp_path)
    gen_sha, gen_rel = "", _gen_rel(1)
    gen_raw = _gen_raw(1, M.V1_FREEZE_SHA256)
    gen_sha = _sha(gen_raw)
    _write(root, gen_rel, gen_raw)
    approval_raw = _approval_raw(gen_sha)
    approval_sha = _sha(approval_raw)
    _write(root, f"{M.APPROVAL_DIR}/{gen_sha}.json", approval_raw)
    ptr_raw = _pointer_raw(1, gen_rel, gen_sha, None, approval_sha)
    ptr_sha = _sha(ptr_raw)
    _write(root, f"{M.ACTIVE_DIR}/{ptr_sha}.json", ptr_raw)
    _commit(root, "all-in-one", "none")
    with pytest.raises(M.RatifiedFreezeError) as ei:
        M.resolve_active_generation(root)
    assert ei.value.reason == "generation-commit-none"


def test_generation_introduced_in_none_commit_rejected(tmp_path):
    # 世代を単独 none commit で導入 (AI 生成物を人間 commit に混ぜる)。
    root = _base_repo(tmp_path)
    gen_raw = _gen_raw(1, M.V1_FREEZE_SHA256)
    _write(root, _gen_rel(1), gen_raw)
    _commit(root, "gen in human commit", "none")
    with pytest.raises(M.RatifiedFreezeError) as ei:
        M.resolve_active_generation(root)
    assert ei.value.reason == "generation-commit-none"


# --------------------------------------------------------------------------
# 履歴不変条件 (C1-5) — helper 直叩き + merge 統合
# --------------------------------------------------------------------------

def _blob_oid(root: Path, path: str) -> str:
    return _git(root, "rev-parse", f"HEAD:{path}")


def test_history_allows_delete_then_same_bytes_recreate(tmp_path):
    root = _base_repo(tmp_path)
    rel = f"{M.APPROVAL_DIR}/{'d' * 64}.json"
    raw = _approval_raw("d" * 64)
    _write(root, rel, raw)
    _commit(root, "add", "none")
    (root / rel).unlink()
    _commit(root, "delete", "none")
    _write(root, rel, raw)  # 同一 bytes 再作成
    head = _commit(root, "readd", "none")
    graph = M._commit_graph(head, root)
    oid = _blob_oid(root, rel)
    intro = M._immutable_introductions(graph, rel, oid, root)
    assert len(intro) == 2, "削除→同一 bytes 再作成は不変条件を破らず 2 導入"


def test_history_rejects_delete_then_different_bytes(tmp_path):
    root = _base_repo(tmp_path)
    rel = f"{M.APPROVAL_DIR}/{'e' * 64}.json"
    _write(root, rel, _approval_raw("e" * 64))
    _commit(root, "add", "none")
    _write(root, rel, _approval_raw("f" * 64))  # 別 bytes に改変
    head = _commit(root, "mutate", "none")
    graph = M._commit_graph(head, root)
    oid = _blob_oid(root, rel)
    with pytest.raises(M.RatifiedFreezeError) as ei:
        M._immutable_introductions(graph, rel, oid, root)
    assert ei.value.reason == "history-mutated"


def test_merge_add_add_yields_multiple_introductions(tmp_path):
    # 両親で同一 path/bytes を導入し merge (history simplification 攻撃)。全 DAG 走査で
    # 両導入を検出し、governance record では multiple-introduction で拒否する。
    root = _base_repo(tmp_path)
    base = _git(root, "rev-parse", "HEAD")
    rel = f"{M.APPROVAL_DIR}/{'1' * 64}.json"
    raw = _approval_raw("1" * 64)

    _git(root, "checkout", "-q", "-b", "b1")
    _write(root, rel, raw)
    _commit(root, "add on b1", "none")

    _git(root, "checkout", "-q", base)
    _git(root, "checkout", "-q", "-b", "b2")
    _write(root, rel, raw)
    _commit(root, "add on b2", "none")

    _git(root, "checkout", "-q", "b1")
    _git(root, "merge", "-q", "--no-edit", "b2")  # add/add 同一 bytes → 競合なし
    with pytest.raises(M.RatifiedFreezeError) as ei:
        M.resolve_active_generation(root)
    assert ei.value.reason == "multiple-introduction"


def test_path_later_mutation_rejected(tmp_path):
    root, gen_sha, gen_rel, approval_sha, ptr_sha = _valid_g1(tmp_path)
    # approval を後日別 bytes に改変して再 commit。
    approval_rel = f"{M.APPROVAL_DIR}/{gen_sha}.json"
    _write(root, approval_rel, _approval_raw("9" * 64))
    _commit(root, "mutate approval", "none")
    with pytest.raises(M.RatifiedFreezeError) as ei:
        M.resolve_active_generation(root)
    assert ei.value.reason == "history-mutated"


# --------------------------------------------------------------------------
# revocation / cancellation
# --------------------------------------------------------------------------

def _revocation_raw(gen_sha: str) -> bytes:
    return M._canonical_bytes({
        "generation_sha256": gen_sha, "revoked_by": "user",
        "revoked_at": "2026-07-18T00:00:00Z", "reason": "test",
    })


def _cancel_raw(ptr_sha: str) -> bytes:
    return M._canonical_bytes({
        "pointer_sha256": ptr_sha, "cancelled_by": "user",
        "cancelled_at": "2026-07-18T00:00:00Z", "reason": "test",
    })


def test_valid_revocation_yields_no_active(tmp_path):
    root, gen_sha, *_ = _valid_g1(tmp_path)
    _write(root, f"{M.REVOCATION_DIR}/{gen_sha}.json", _revocation_raw(gen_sha))
    _commit(root, "revoke g1", "none")
    with pytest.raises(M.RatifiedFreezeError) as ei:
        M.resolve_active_generation(root)
    assert ei.value.reason == "tip-revoked"


def test_revocation_with_ai_trailer_is_error_not_ignored(tmp_path):
    root, gen_sha, *_ = _valid_g1(tmp_path)
    _write(root, f"{M.REVOCATION_DIR}/{gen_sha}.json", _revocation_raw(gen_sha))
    _commit(root, "revoke g1 (ai)", "claude-opus")  # 無効 record
    with pytest.raises(M.RatifiedFreezeError) as ei:
        M.resolve_active_generation(root)
    assert ei.value.reason == "user-commit-trailer"


# --------------------------------------------------------------------------
# pointer 連鎖 / fork / genesis / 連番
# --------------------------------------------------------------------------

def test_second_genesis_rejected(tmp_path):
    root, gen_sha, gen_rel, approval_sha, ptr_sha = _valid_g1(tmp_path)
    # 第二の parent-null pointer を足す (同じ g1・approval を指す別 pointer は不可なので、
    # 別世代 g2 を作ってその genesis pointer を載せる)。
    gen2_sha, gen2_rel = _add_generation(root, 2, gen_sha)
    approval2_raw = _approval_raw(gen2_sha)
    approval2_sha = _sha(approval2_raw)
    _write(root, f"{M.APPROVAL_DIR}/{gen2_sha}.json", approval2_raw)
    ptr2_raw = _pointer_raw(2, gen2_rel, gen2_sha, None, approval2_sha)  # parent null = 第二 genesis
    ptr2_sha = _sha(ptr2_raw)
    _write(root, f"{M.ACTIVE_DIR}/{ptr2_sha}.json", ptr2_raw)
    _commit(root, "second genesis", "none")
    with pytest.raises(M.RatifiedFreezeError) as ei:
        M.resolve_active_generation(root)
    # 第二 genesis (pointer.generation_number=2 だが parent=null) → number-gap または genesis-count。
    assert ei.value.reason in ("genesis-count", "pointer-number-gap")


def test_generation_number_jump_g999_rejected(tmp_path):
    root, gen_sha, gen_rel, approval_sha, ptr_sha = _valid_g1(tmp_path)
    # g999 を child pointer で足す (親世代 g998 が無いため連鎖に穴)。
    gen999_sha, gen999_rel = _add_generation(root, 999, gen_sha)
    approval999_raw = _approval_raw(gen999_sha)
    approval999_sha = _sha(approval999_raw)
    _write(root, f"{M.APPROVAL_DIR}/{gen999_sha}.json", approval999_raw)
    ptr999_raw = _pointer_raw(999, gen999_rel, gen999_sha, ptr_sha, approval999_sha)
    ptr999_sha = _sha(ptr999_raw)
    _write(root, f"{M.ACTIVE_DIR}/{ptr999_sha}.json", ptr999_raw)
    _commit(root, "g999", "none")
    with pytest.raises(M.RatifiedFreezeError) as ei:
        M.resolve_active_generation(root)
    assert ei.value.reason == "generation-chain-gap"


def _build_chain_g2(root: Path, g1_sha: str, g1_rel: str, ptr1_sha: str):
    """g1 の上に g2 と child pointer (parent=ptr1) を積む。(g2_sha, g2_rel, ptr2_sha) を返す。"""
    g2_sha, g2_rel = _add_generation(root, 2, g1_sha)
    approval2_sha, ptr2_sha = _approve_and_point(root, 2, g2_sha, g2_rel, ptr1_sha)
    return g2_sha, g2_rel, ptr2_sha


def test_pointer_fork_and_cancellation_recovery(tmp_path):
    root, g1_sha, g1_rel, approval1_sha, ptr1_sha = _valid_g1(tmp_path)
    # g2 (child of ptr1) と g3 (child of ptr1) の 2 本 → fork。
    g2_sha, g2_rel, ptr2_sha = _build_chain_g2(root, g1_sha, g1_rel, ptr1_sha)
    g3_sha, g3_rel = _add_generation(root, 3, g2_sha)
    approval3_raw = _approval_raw(g3_sha)
    approval3_sha = _sha(approval3_raw)
    _write(root, f"{M.APPROVAL_DIR}/{g3_sha}.json", approval3_raw)
    ptr3_raw = _pointer_raw(3, g3_rel, g3_sha, ptr1_sha, approval3_sha)  # 同じ parent=ptr1 → fork
    ptr3_sha = _sha(ptr3_raw)
    _write(root, f"{M.ACTIVE_DIR}/{ptr3_sha}.json", ptr3_raw)
    _commit(root, "fork g3", "none")

    with pytest.raises(M.RatifiedFreezeError) as ei:
        M.resolve_active_generation(root)
    assert ei.value.reason == "pointer-fork"

    # ptr3 を cancellation tombstone で取消 → fork 回復 → active = g2。
    _write(root, f"{M.ACTIVE_CANCEL_DIR}/{ptr3_sha}.json", _cancel_raw(ptr3_sha))
    _commit(root, "cancel ptr3", "none")
    res = M.resolve_active_generation(root)
    assert res.generation_number == 2
    assert res.generation_sha256 == g2_sha


def test_cancellation_with_ai_trailer_is_error(tmp_path):
    root, g1_sha, g1_rel, approval1_sha, ptr1_sha = _valid_g1(tmp_path)
    _write(root, f"{M.ACTIVE_CANCEL_DIR}/{ptr1_sha}.json", _cancel_raw(ptr1_sha))
    _commit(root, "cancel (ai)", "claude-opus")
    with pytest.raises(M.RatifiedFreezeError) as ei:
        M.resolve_active_generation(root)
    assert ei.value.reason == "user-commit-trailer"


# --------------------------------------------------------------------------
# strict parse / schema
# --------------------------------------------------------------------------

def test_generation_with_nan_rejected(tmp_path):
    root = _base_repo(tmp_path)
    raw = b'{"schema_version": "8b-holdout-freeze/v2", "floor": NaN}'
    _write(root, _gen_rel(1), raw)
    _commit(root, "nan gen", "claude-opus")
    with pytest.raises(M.RatifiedFreezeError) as ei:
        M.resolve_active_generation(root)
    assert ei.value.reason == "json-nan"


def test_approval_duplicate_key_rejected(tmp_path):
    root = _base_repo(tmp_path)
    gen_sha, gen_rel = _add_generation(root, 1, M.V1_FREEZE_SHA256)
    dup = b'{"generation_sha256": "%s", "generation_sha256": "%s", "approver": "u", "approved_at": "t", "scope": "s"}' % (
        gen_sha.encode(), gen_sha.encode())
    _write(root, f"{M.APPROVAL_DIR}/{gen_sha}.json", dup)
    _commit(root, "dup approval", "none")
    with pytest.raises(M.RatifiedFreezeError) as ei:
        M.resolve_active_generation(root)
    assert ei.value.reason == "json-duplicate-key"


def test_non_canonical_approval_rejected(tmp_path):
    root = _base_repo(tmp_path)
    gen_sha, gen_rel = _add_generation(root, 1, M.V1_FREEZE_SHA256)
    pretty = json.dumps({
        "generation_sha256": gen_sha, "approver": "u",
        "approved_at": "t", "scope": "s",
    }, indent=2).encode("utf-8")  # canonical でない (空白入り)
    _write(root, f"{M.APPROVAL_DIR}/{gen_sha}.json", pretty)
    _commit(root, "pretty approval", "none")
    with pytest.raises(M.RatifiedFreezeError) as ei:
        M.resolve_active_generation(root)
    assert ei.value.reason == "not-canonical"


def test_generation_with_approval_field_rejected(tmp_path):
    root = _base_repo(tmp_path)
    doc = {key: "x" for key in M.V2_TOP_LEVEL_KEYS}
    doc["schema_version"] = "8b-holdout-freeze/v2"
    doc["generation_number"] = 1
    doc["supersedes_sha256"] = M.V1_FREEZE_SHA256
    doc["approved_by"] = "user"  # 世代に現れてはならない approval 系 field
    raw = json.dumps(doc, ensure_ascii=False).encode("utf-8")
    _write(root, _gen_rel(1), raw)
    _commit(root, "gen with approval field", "claude-opus")
    with pytest.raises(M.RatifiedFreezeError) as ei:
        M.resolve_active_generation(root)
    assert ei.value.reason == "generation-approval-field"


def test_generation_supersedes_mismatch_rejected(tmp_path):
    root = _base_repo(tmp_path)
    _add_generation(root, 1, "0" * 64)  # v1 hash でない supersedes (承認なしでも chain 検査で落ちる)
    with pytest.raises(M.RatifiedFreezeError) as ei:
        M.resolve_active_generation(root)
    assert ei.value.reason == "generation-supersedes"


# --------------------------------------------------------------------------
# 深い不変性 / shallow / dirty / 型分離 / static
# --------------------------------------------------------------------------

def test_ratified_freeze_deep_immutability(tmp_path):
    if not _REAL_V1.is_file():
        pytest.fail("実 v1 freeze が無い (trust root 不在 — skip すると攻撃 matrix が緑化する。failures F9 型)")
    root, *_ = build_valid_semantic_g1(tmp_path)
    freeze = M.load_ratified_freeze(root)
    with pytest.raises((TypeError, AttributeError)):
        freeze.document["schema_version"] = "mutated"       # top-level 再代入不可
    # ネストした list も tuple 化されている。
    assert isinstance(freeze.document["measurement_closure"], tuple)


def test_shallow_repo_rejected(tmp_path):
    root, *_ = _valid_g1(tmp_path)
    head = _git(root, "rev-parse", "HEAD")
    (root / ".git" / "shallow").write_text(head + "\n", encoding="utf-8")
    assert _git(root, "rev-parse", "--is-shallow-repository") == "true"
    with pytest.raises(M.RatifiedFreezeError) as ei:
        M.resolve_active_generation(root)
    assert ei.value.reason == "shallow-repo"


def test_namespace_dirty_rejected(tmp_path):
    root, gen_sha, gen_rel, *_ = _valid_g1(tmp_path)
    # namespace 内の tracked file を worktree で改変 (未 commit)。
    (root / gen_rel).write_bytes((root / gen_rel).read_bytes() + b"\n")
    with pytest.raises(M.RatifiedFreezeError) as ei:
        M.resolve_active_generation(root)
    assert ei.value.reason == "namespace-dirty"


def _has_hardening_pair(cmd) -> bool:
    """argv に `-c core.useReplaceRefs=false` の連続対が含まれるか。"""
    return any(
        cmd[i] == "-c" and cmd[i + 1] == "core.useReplaceRefs=false"
        for i in range(len(cmd) - 1)
    )


def test_git_hardening_reaches_argv(tmp_path, monkeypatch):
    # R7: _GIT_HARDEN の構造 pin + 実効検査。全 git 呼出しが
    # `-c core.useReplaceRefs=false` を前置し、replace refs による object 解決の
    # out-of-band 差替えを封じる。定数を空 tuple 化する変異はこのテストで殺せる。
    root = _base_repo(tmp_path)

    # 構造 pin: 定数そのものが hardening 対を持つ。
    assert M._GIT_HARDEN == ("-c", "core.useReplaceRefs=false")

    # 実効検査: subprocess.run を捕捉し、実 git 呼出しの argv に対が届いているか。
    real_run = M.subprocess.run
    captured: list = []

    def _spy(cmd, *args, **kwargs):
        captured.append(list(cmd))
        return real_run(cmd, *args, **kwargs)

    monkeypatch.setattr(M.subprocess, "run", _spy)
    M._capture_head(root)  # _git 経由で複数の git query を発行する

    git_calls = [cmd for cmd in captured if cmd and cmd[0] == "git"]
    assert git_calls, "git 呼出しが捕捉されていない"
    assert all(_has_hardening_pair(cmd) for cmd in git_calls), (
        "git 呼出しに core.useReplaceRefs=false hardening が欠けている: "
        f"{[cmd for cmd in git_calls if not _has_hardening_pair(cmd)]}"
    )


def test_replace_ref_rejected(tmp_path):
    # refs/replace/* は cat-file/rev-list を out-of-band に書換え履歴検証を無効化し得る。
    # 存在自体を fail-closed 拒否する (shallow と非対称にしない)。
    root, *_ = _valid_g1(tmp_path)
    head = _git(root, "rev-parse", "HEAD")
    _git(root, "replace", "--graft", head)  # refs/replace/<head> を生成
    with pytest.raises(M.RatifiedFreezeError) as ei:
        M.resolve_active_generation(root)
    assert ei.value.reason == "replace-refs"


def test_replace_ref_cannot_forge_history(tmp_path):
    # replace object で過去 commit の governance blob を別 bytes に差し替えても、
    # core.useReplaceRefs=false により object 解決は追従しない (検出が空振りしない)。
    # ここでは capture 段の replace 拒否より前に history 検証が効くことは要求せず、
    # 「replace が存在すれば必ず拒否に倒れる」ことを確認する (無効化されない)。
    root, gen_sha, gen_rel, approval_sha, ptr_sha = _valid_g1(tmp_path)
    # approval commit を別 blob へ replace-graft しても resolve は fail-closed のまま。
    approval_rel = f"{M.APPROVAL_DIR}/{gen_sha}.json"
    approval_commit = _git(root, "log", "-n", "1", "--format=%H", "--", approval_rel)
    _git(root, "replace", "--graft", approval_commit)
    with pytest.raises(M.RatifiedFreezeError) as ei:
        M.resolve_active_generation(root)
    assert ei.value.reason == "replace-refs"


def test_grafts_file_rejected(tmp_path):
    # .git/info/grafts は rev-list の親関係を out-of-band に書換える。存在を fail-closed 拒否。
    root, *_ = _valid_g1(tmp_path)
    head = _git(root, "rev-parse", "HEAD")
    grafts = root / ".git" / "info" / "grafts"
    grafts.parent.mkdir(parents=True, exist_ok=True)
    grafts.write_text(head + "\n", encoding="utf-8")  # HEAD を root 化する graft
    with pytest.raises(M.RatifiedFreezeError) as ei:
        M.resolve_active_generation(root)
    assert ei.value.reason == "grafts"


def test_candidate_generation_not_loadable(tmp_path):
    # 未承認 candidate を load_ratified_freeze から取得できない (型分離)。
    root = _base_repo(tmp_path)
    _add_generation(root, 1, M.V1_FREEZE_SHA256)
    with pytest.raises(M.RatifiedFreezeError) as ei:
        M.load_ratified_freeze(root)
    assert ei.value.reason == "no-active"


def test_no_production_module_constructs_ratified_freeze_directly():
    # RatifiedFreeze( の直接構築は loader 内限定 (公開 API から昇格不能, C1-7)。
    campaign_dir = Path(_ORCH) / "campaign"
    offenders = []
    for path in sorted(campaign_dir.glob("*.py")):
        if path.name == "s8b_ratified_freeze.py":
            continue  # loader 自身は許可
        text = path.read_text(encoding="utf-8")
        if "RatifiedFreeze(" in text:
            offenders.append(path.name)
    assert not offenders, f"loader 外で RatifiedFreeze を直接構築: {offenders}"
