# -*- coding: utf-8 -*-
"""tools/check_docs.py の恒真ゲート回帰 (F9) + positive control (machine 非依存)。

pytest でも 素の `python3 orchestrator/tests/test_check_docs.py` でも走る。

背景 (F9): LIVING_DOCS の手書き列挙対象が改名/削除で不在になると、旧実装は
`if not doc.exists(): continue` で黙って skip し、その doc への lint が発火せず
「恒真な保証」に化けていた。本テストは positive control =「列挙対象を 1 個わざと
消すと違反が出る」を、合成した最小 repo に対して固定する (規律3 の positive control)。

戦略: 実 check_docs.py を tmp/tools/ へ複製し REPO を tmp に付け替える。check_docs が
読むファイル群を trivial 内容で合成し、baseline が「違反なし」であることを確認した上で、
列挙対象を 1 個消して「不在 = 違反」に変わることを検査する。列挙名は check_docs 本体の
_ENUMERATED_DOCS から導出するので docs の増減で腐らない。
"""
from __future__ import annotations

import os
import shutil
import subprocess
import sys
import tempfile

_HERE = os.path.dirname(os.path.abspath(__file__))
_ORCH = os.path.dirname(_HERE)
_REPO = os.path.dirname(_ORCH)
sys.path.insert(0, os.path.join(_REPO, "tools"))

import check_docs  # noqa: E402


def _write(root: str, rel: str, content: str) -> None:
    path = os.path.join(root, rel)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)


def _enumerated_rels() -> list[str]:
    """check_docs 本体の _ENUMERATED_DOCS を実 REPO 相対パスへ落とす (増減に追従)。"""
    return sorted(str(p.relative_to(check_docs.REPO)) for p in check_docs._ENUMERATED_DOCS)


def _build_min_repo() -> str:
    """check_docs が『違反なし』を返す最小合成 repo を tmp に作り、root を返す。

    trivial 内容 (行番号参照/現況再掲/pin literal/D 参照/パス参照をどれも含まない) にして、
    唯一発火しうるのが「列挙対象不在」検査になるようにする。
    """
    root = tempfile.mkdtemp(prefix="izanagi_checkdocs_")
    # 実 check_docs.py を複製 — REPO は __file__ 由来なので tmp/tools/ に置くと tmp を指す。
    _dst = os.path.join(root, "tools", "check_docs.py")
    os.makedirs(os.path.dirname(_dst))
    shutil.copy(check_docs.__file__, _dst)

    # 手書き列挙 doc (LIVING_DOCS の glob 前スナップショット) を trivial 内容で用意。
    for rel in _enumerated_rels():
        _write(root, rel, "# placeholder living doc\n")

    # check_docs が main() 内で無条件に read するファイル群。
    _write(root, os.path.join("orchestrator", "campaign", "pin.py"),
           'CURRENT_PIN = "abc1234def5678"\n')
    _write(root, os.path.join("docs", "decisions.md"),
           "## D1 placeholder decision\n\n本文。\n")
    _write(root, os.path.join("docs", "archive", "README.md"),
           "# archive\n\n## 現在の収容物\n\n(なし)\n")
    return root


def _run_check(root: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, os.path.join(root, "tools", "check_docs.py")],
        capture_output=True, text=True,
    )


# ===== baseline: 合成 repo は違反なし (positive control の土台) =====

def test_synthetic_repo_baseline_clean():
    root = _build_min_repo()
    try:
        res = _run_check(root)
        assert res.returncode == 0, f"baseline が違反ありになった:\n{res.stdout}\n{res.stderr}"
        assert "違反なし" in res.stdout, res.stdout
    finally:
        shutil.rmtree(root, ignore_errors=True)


# ===== positive control: 列挙対象を 1 個消すと違反が出る (F9 の核心) =====

def test_missing_enumerated_doc_is_violation():
    root = _build_min_repo()
    try:
        rels = _enumerated_rels()
        assert rels, "列挙対象が空 — _ENUMERATED_DOCS の抽出に失敗している"
        victim = rels[len(rels) // 2]           # 真ん中の 1 個を選ぶ (端の特異性を避ける)
        os.remove(os.path.join(root, victim))
        res = _run_check(root)
        assert res.returncode == 1, f"列挙対象不在なのに fail しなかった:\n{res.stdout}"
        assert "列挙対象が不在" in res.stdout, res.stdout
        assert victim in res.stdout, f"消した {victim} が finding に出ていない:\n{res.stdout}"
    finally:
        shutil.rmtree(root, ignore_errors=True)


def test_missing_enumerated_doc_only_fires_own_finding():
    # 不在検査だけが増える (他の検査を巻き添えにしない) ことを固定 — baseline との差分は 1 件。
    root = _build_min_repo()
    try:
        rels = _enumerated_rels()
        victim = rels[0]
        os.remove(os.path.join(root, victim))
        res = _run_check(root)
        assert res.returncode == 1, res.stdout
        # "check_docs: N 件の違反" の N がちょうど 1 であること。
        header = next((l for l in res.stdout.splitlines() if "件の違反" in l), "")
        assert "1 件の違反" in header, f"不在検査以外も発火している:\n{res.stdout}"
    finally:
        shutil.rmtree(root, ignore_errors=True)


# ===== V19a: output の生きた README を検査網へ固定 =====

def test_output_readmes_are_enumerated_and_valid_fixture_is_clean():
    expected = {"output/README.md", "output/task-runs/README.md"}
    assert expected <= set(_enumerated_rels())
    root = _build_min_repo()
    try:
        res = _run_check(root)
        assert res.returncode == 0, res.stdout
        assert "違反なし" in res.stdout
    finally:
        shutil.rmtree(root, ignore_errors=True)


def test_broken_reference_in_task_runs_readme_is_positive_control():
    """対象を列挙しただけの恒真化を防ぎ、本文 lint が実際に発火することを固定。"""

    root = _build_min_repo()
    try:
        victim = "output/task-runs/README.md"
        _write(root, victim, "# task-runs\n\n壊れた参照: tools/definitely-missing.py\n")
        res = _run_check(root)
        assert res.returncode == 1, f"壊れた参照が赤にならなかった:\n{res.stdout}"
        assert victim in res.stdout, res.stdout
        assert "実在しないパス参照" in res.stdout, res.stdout
        assert "tools/definitely-missing.py" in res.stdout, res.stdout
    finally:
        shutil.rmtree(root, ignore_errors=True)


def test_missing_task_runs_readme_is_violation():
    root = _build_min_repo()
    try:
        victim = "output/task-runs/README.md"
        os.remove(os.path.join(root, victim))
        res = _run_check(root)
        assert res.returncode == 1, res.stdout
        assert victim in res.stdout, res.stdout
        assert "列挙対象が不在" in res.stdout, res.stdout
    finally:
        shutil.rmtree(root, ignore_errors=True)


def test_real_repo_clean():
    res = subprocess.run(
        [sys.executable, os.path.join(_REPO, "tools", "check_docs.py")],
        capture_output=True,
        text=True,
    )
    assert res.returncode == 0, f"実 repo で違反が出た:\n{res.stdout}\n{res.stderr}"
    assert "違反なし" in res.stdout, res.stdout


def _run():
    fns = [v for k, v in sorted(globals().items())
           if k.startswith("test_") and callable(v)]
    passed = failed = 0
    for fn in fns:
        try:
            fn()
            print(f"PASS {fn.__name__}")
            passed += 1
        except AssertionError as e:
            print(f"FAIL {fn.__name__}: {e}")
            failed += 1
        except Exception as e:  # noqa: BLE001
            print(f"ERROR {fn.__name__}: {type(e).__name__}: {e}")
            failed += 1
    print(f"\n{passed} passed, {failed} failed")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(_run())
