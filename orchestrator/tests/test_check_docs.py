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


_CLEAN_WORKLOG = """# synthetic worklog

## ローテーション

## 2026-01-01 (1) — first

### 次の一手
1. [T-001] carry

## 2026-01-02 (2) — second

- [T-001] consumed

### 次の一手
1. [T-002] continue
"""

_CLEAN_PHASE3 = """# synthetic phase

## 見送り台帳 (synthetic)

- [T-900] deferred item

### 裁定・完了記録

- completed item

## 残存リスク

- risk
"""


def _write(root: str, rel: str, content: str) -> None:
    path = os.path.join(root, rel)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)


def _enumerated_rels() -> list[str]:
    """check_docs 本体の _ENUMERATED_DOCS を実 REPO 相対パスへ落とす (増減に追従)。"""
    return sorted(str(p.relative_to(check_docs.REPO)) for p in check_docs._ENUMERATED_DOCS)


def _write_backlog_docs(
    root: str,
    worklog_text: str = _CLEAN_WORKLOG,
    phase3_text: str = _CLEAN_PHASE3,
) -> None:
    _write(root, os.path.join("docs", "worklog.md"), worklog_text)
    _write(root, os.path.join("docs", "phase3.md"), phase3_text)


def _assert_violation(root: str, *needles: str) -> subprocess.CompletedProcess:
    res = _run_check(root)
    assert res.returncode == 1, f"違反 fixture が赤にならなかった:\n{res.stdout}\n{res.stderr}"
    for needle in needles:
        assert needle in res.stdout, f"{needle!r} が finding にない:\n{res.stdout}"
    return res


def _build_min_repo() -> str:
    """check_docs が『違反なし』を返す最小合成 repo を tmp に作り、root を返す。

    trivial 内容 (行番号参照/現況再掲/pin literal/D 参照/パス参照をどれも含まない) と、
    保存則を満たす最小 worklog / 見送り台帳を用意し、baseline を違反なしにする。
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
    # backlog guard の必須構造。phase3.md は上の列挙 placeholder を上書きする。
    _write_backlog_docs(root)
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


# ===== backlog guard: fail-closed の全構造分岐 =====

def test_backlog_guard_missing_worklog_is_violation():
    root = _build_min_repo()
    try:
        os.remove(os.path.join(root, "docs", "worklog.md"))
        _assert_violation(root, "docs/worklog.md: ファイルが不在")
    finally:
        shutil.rmtree(root, ignore_errors=True)


def test_backlog_guard_missing_phase3_is_violation():
    root = _build_min_repo()
    try:
        os.remove(os.path.join(root, "docs", "phase3.md"))
        _assert_violation(root, "docs/phase3.md: ファイルが不在")
    finally:
        shutil.rmtree(root, ignore_errors=True)


def test_backlog_guard_rotation_heading_must_be_unique():
    fixtures = {
        "zero": _CLEAN_WORKLOG.replace("## ローテーション\n", ""),
        "multiple": _CLEAN_WORKLOG.replace(
            "## ローテーション\n", "## ローテーション\n\n## ローテーション (duplicate)\n", 1
        ),
    }
    for name, worklog in fixtures.items():
        root = _build_min_repo()
        try:
            _write_backlog_docs(root, worklog_text=worklog)
            expected = "`## ローテーション` が 0 件" if name == "zero" else "`## ローテーション` が 2 件"
            _assert_violation(root, expected)
        finally:
            shutil.rmtree(root, ignore_errors=True)


def test_backlog_guard_entry_title_must_fullmatch():
    root = _build_min_repo()
    try:
        worklog = _CLEAN_WORKLOG.replace(
            "## 2026-01-02 (2) — second", "## 補助見出し (entry ではない)"
        )
        _write_backlog_docs(root, worklog_text=worklog)
        _assert_violation(root, "worklog entry title に full-match しない")
    finally:
        shutil.rmtree(root, ignore_errors=True)


def test_backlog_guard_zero_entries_is_violation():
    root = _build_min_repo()
    try:
        _write_backlog_docs(root, worklog_text="# worklog\n\n## ローテーション\n")
        _assert_violation(root, "worklog エントリが 0 件")
    finally:
        shutil.rmtree(root, ignore_errors=True)


def test_backlog_guard_next_action_section_must_be_unique():
    fixtures = {
        "zero": _CLEAN_WORKLOG.replace("### 次の一手\n1. [T-001] carry\n", "本文だけ。\n", 1),
        "multiple": _CLEAN_WORKLOG.replace(
            "### 次の一手\n1. [T-001] carry\n",
            "### 次の一手\n1. [T-001] carry\n\n### 次の一手 (duplicate)\n1. [T-003] duplicate\n",
            1,
        ),
    }
    for name, worklog in fixtures.items():
        root = _build_min_repo()
        try:
            _write_backlog_docs(root, worklog_text=worklog)
            count = "0 件" if name == "zero" else "2 件"
            _assert_violation(root, "`### 次の一手`", count, "source を一意に抽出できない")
        finally:
            shutil.rmtree(root, ignore_errors=True)


def test_backlog_guard_deferred_ledger_section_must_be_unique():
    fixtures = {
        "zero": _CLEAN_PHASE3.replace("## 見送り台帳 (synthetic)", "## 別の台帳"),
        "multiple": _CLEAN_PHASE3.replace(
            "### 裁定・完了記録",
            "## 見送り台帳 (duplicate)\n\n- duplicate\n\n### 裁定・完了記録",
        ),
    }
    for name, phase3 in fixtures.items():
        root = _build_min_repo()
        try:
            _write_backlog_docs(root, phase3_text=phase3)
            count = "0 件" if name == "zero" else "2 件"
            _assert_violation(root, "`## 見送り台帳`", count, "sink を一意に抽出できない")
        finally:
            shutil.rmtree(root, ignore_errors=True)


def test_backlog_guard_completion_record_section_must_be_unique():
    fixtures = {
        "zero": _CLEAN_PHASE3.replace("### 裁定・完了記録", "### 別の記録"),
        "multiple": _CLEAN_PHASE3.replace(
            "## 残存リスク",
            "### 裁定・完了記録 (duplicate)\n\n- duplicate\n\n## 残存リスク",
        ),
    }
    for name, phase3 in fixtures.items():
        root = _build_min_repo()
        try:
            _write_backlog_docs(root, phase3_text=phase3)
            count = "0 件" if name == "zero" else "2 件"
            _assert_violation(root, "`### 裁定・完了記録`", count, "終端を一意に抽出できない")
        finally:
            shutil.rmtree(root, ignore_errors=True)


def test_backlog_guard_completion_record_must_follow_ledger():
    root = _build_min_repo()
    try:
        phase3 = """# phase

### 裁定・完了記録

- completed

## 見送り台帳

- [T-900] deferred
"""
        _write_backlog_docs(root, phase3_text=phase3)
        _assert_violation(root, "`### 裁定・完了記録` が `## 見送り台帳` より後にない")
    finally:
        shutil.rmtree(root, ignore_errors=True)


def test_backlog_guard_zero_entries_with_valid_ids_is_violation():
    root = _build_min_repo()
    try:
        worklog = _CLEAN_WORKLOG.replace("[T-001]", "legacy", 2).replace("[T-002]", "legacy")
        _write_backlog_docs(root, worklog_text=worklog)
        _assert_violation(root, "有効 ID を持つエントリが 1 件もない")
    finally:
        shutil.rmtree(root, ignore_errors=True)


def test_backlog_guard_latest_item_requires_id():
    root = _build_min_repo()
    try:
        worklog = _CLEAN_WORKLOG.replace("1. [T-002] continue", "1. missing ID")
        _write_backlog_docs(root, worklog_text=worklog)
        _assert_violation(root, "末尾エントリ", "項目先頭に有効な [T-NNN] ID がない")
    finally:
        shutil.rmtree(root, ignore_errors=True)


def test_backlog_guard_latest_next_action_rejects_duplicate_ids():
    root = _build_min_repo()
    try:
        worklog = _CLEAN_WORKLOG.replace(
            "1. [T-002] continue", "1. [T-002] first\n2. [T-002] duplicate"
        )
        _write_backlog_docs(root, worklog_text=worklog)
        _assert_violation(root, "`### 次の一手` 内で ID [T-002] が重複")
    finally:
        shutil.rmtree(root, ignore_errors=True)


def test_backlog_guard_id_bearing_middle_entry_requires_ids_on_all_items():
    root = _build_min_repo()
    try:
        worklog = """# worklog

## ローテーション

## 2026-01-01 (1) — first

### 次の一手
1. [T-001] carry

## 2026-01-02 (2) — second

- [T-001] consumed

### 次の一手
1. missing ID

## 2026-01-03 (3) — third

### 次の一手
1. [T-003] latest
"""
        _write_backlog_docs(root, worklog_text=worklog)
        _assert_violation(
            root,
            "エントリ '2026-01-02 (2) — second'",
            "項目先頭に有効な [T-NNN] ID がない",
        )
    finally:
        shutil.rmtree(root, ignore_errors=True)


def test_backlog_guard_id_bearing_middle_entry_rejects_duplicate_ids():
    root = _build_min_repo()
    try:
        worklog = """# worklog

## ローテーション

## 2026-01-01 (1) — first

### 次の一手
1. [T-001] carry

## 2026-01-02 (2) — second

- [T-001] consumed

### 次の一手
1. [T-002] first
2. [T-002] duplicate

## 2026-01-03 (3) — third

- [T-002] consumed

### 次の一手
1. [T-003] latest
"""
        _write_backlog_docs(root, worklog_text=worklog)
        _assert_violation(
            root,
            "エントリ '2026-01-02 (2) — second'",
            "`### 次の一手` 内で ID [T-002] が重複",
        )
    finally:
        shutil.rmtree(root, ignore_errors=True)


def test_backlog_guard_ledger_rejects_invalid_id_format():
    root = _build_min_repo()
    try:
        phase3 = _CLEAN_PHASE3.replace("[T-900]", "[T-01]")
        _write_backlog_docs(root, phase3_text=phase3)
        _assert_violation(root, "見送り台帳の項目先頭 ID '[T-01]' が不正形式")
    finally:
        shutil.rmtree(root, ignore_errors=True)


def test_backlog_guard_ledger_rejects_duplicate_ids():
    root = _build_min_repo()
    try:
        phase3 = _CLEAN_PHASE3.replace(
            "- [T-900] deferred item", "- [T-900] first\n- [T-900] duplicate"
        )
        _write_backlog_docs(root, phase3_text=phase3)
        _assert_violation(root, "見送り台帳の ID [T-900] が重複")
    finally:
        shutil.rmtree(root, ignore_errors=True)


def test_backlog_guard_ledger_live_item_requires_id():
    root = _build_min_repo()
    try:
        phase3 = _CLEAN_PHASE3.replace("- [T-900] deferred item", "- deferred item")
        _write_backlog_docs(root, phase3_text=phase3)
        _assert_violation(root, "見送り台帳の生存項目先頭に有効な [T-NNN] ID がない")
    finally:
        shutil.rmtree(root, ignore_errors=True)


def test_backlog_guard_ledger_struck_item_rejects_id():
    root = _build_min_repo()
    try:
        phase3 = _CLEAN_PHASE3.replace(
            "### 裁定・完了記録",
            "- ~~[T-901] retired item~~\n\n### 裁定・完了記録",
        )
        _write_backlog_docs(root, phase3_text=phase3)
        _assert_violation(root, "見送り台帳の取り消し線項目に ID '[T-901]' がある")
    finally:
        shutil.rmtree(root, ignore_errors=True)


# ===== backlog guard: 保存則の正例 =====

def test_backlog_guard_carried_id_in_next_action_is_clean():
    root = _build_min_repo()
    try:
        worklog = _CLEAN_WORKLOG.replace(
            "- [T-001] consumed\n\n### 次の一手\n1. [T-002] continue",
            "本文。\n\n### 次の一手\n1. [T-001] continue",
        )
        _write_backlog_docs(root, worklog_text=worklog)
        res = _run_check(root)
        assert res.returncode == 0, res.stdout
    finally:
        shutil.rmtree(root, ignore_errors=True)


def test_backlog_guard_consumed_id_in_body_is_clean():
    root = _build_min_repo()
    try:
        res = _run_check(root)
        assert res.returncode == 0, res.stdout
    finally:
        shutil.rmtree(root, ignore_errors=True)


def test_backlog_guard_deferred_id_in_ledger_is_clean():
    root = _build_min_repo()
    try:
        worklog = _CLEAN_WORKLOG.replace("- [T-001] consumed\n\n", "本文。\n\n")
        phase3 = _CLEAN_PHASE3.replace("[T-900]", "[T-001]")
        _write_backlog_docs(root, worklog_text=worklog, phase3_text=phase3)
        res = _run_check(root)
        assert res.returncode == 0, res.stdout
    finally:
        shutil.rmtree(root, ignore_errors=True)


def test_backlog_guard_pre_id_transition_is_not_applicable():
    root = _build_min_repo()
    try:
        worklog = _CLEAN_WORKLOG.replace("1. [T-001] carry", "1. legacy item").replace(
            "- [T-001] consumed\n\n", "本文。\n\n"
        )
        _write_backlog_docs(root, worklog_text=worklog)
        res = _run_check(root)
        assert res.returncode == 0, res.stdout
    finally:
        shutil.rmtree(root, ignore_errors=True)


def test_backlog_guard_source_is_only_next_action_in_three_entry_chain():
    root = _build_min_repo()
    try:
        worklog = """# worklog

## ローテーション

## 2026-01-01 (1) — first

### 次の一手
1. [T-001] carry

## 2026-01-02 (2) — second

- [T-001] consumed

### 次の一手
1. [T-002] carry

## 2026-01-03 (3) — third

- [T-002] consumed

### 次の一手
1. [T-003] latest
"""
        _write_backlog_docs(root, worklog_text=worklog)
        res = _run_check(root)
        assert res.returncode == 0, res.stdout
    finally:
        shutil.rmtree(root, ignore_errors=True)


def test_backlog_guard_four_digit_id_is_clean():
    root = _build_min_repo()
    try:
        worklog = _CLEAN_WORKLOG.replace("[T-002]", "[T-1000]")
        _write_backlog_docs(root, worklog_text=worklog)
        res = _run_check(root)
        assert res.returncode == 0, res.stdout
    finally:
        shutil.rmtree(root, ignore_errors=True)


# ===== backlog guard: 保存則の負例 =====

def test_backlog_guard_dropped_id_is_violation():
    root = _build_min_repo()
    try:
        worklog = _CLEAN_WORKLOG.replace("- [T-001] consumed\n\n", "本文。\n\n")
        _write_backlog_docs(root, worklog_text=worklog)
        _assert_violation(root, "次の一手 ID [T-001]", "後続エントリ")
    finally:
        shutil.rmtree(root, ignore_errors=True)


def test_backlog_guard_prose_and_html_comment_do_not_satisfy_sink():
    root = _build_min_repo()
    try:
        worklog = _CLEAN_WORKLOG.replace(
            "- [T-001] consumed",
            "本文で [T-001] に言及する。\n\n<!-- [T-001] はここにあるだけ -->",
        )
        _write_backlog_docs(root, worklog_text=worklog)
        _assert_violation(root, "次の一手 ID [T-001]", "後続エントリ")
    finally:
        shutil.rmtree(root, ignore_errors=True)


def test_backlog_guard_fences_and_multiline_comment_do_not_satisfy_sink():
    hidden_sinks = {
        "backtick fence": "```text\n- [T-001] dummy\n```",
        "tilde fence": "~~~text\n- [T-001] dummy\n~~~",
        "HTML comment": "<!--\n- [T-001] dummy\n-->",
    }
    for name, hidden_sink in hidden_sinks.items():
        root = _build_min_repo()
        try:
            worklog = _CLEAN_WORKLOG.replace("- [T-001] consumed", hidden_sink)
            _write_backlog_docs(root, worklog_text=worklog)
            _assert_violation(root, "次の一手 ID [T-001]", "後続エントリ")
        finally:
            shutil.rmtree(root, ignore_errors=True)


def test_backlog_guard_hidden_ledger_items_do_not_satisfy_sink():
    hidden_sinks = {
        "backtick fence": "```text\n- [T-001] dummy\n```",
        "tilde fence": "~~~text\n- [T-001] dummy\n~~~",
        "HTML comment": "<!--\n- [T-001] dummy\n-->",
    }
    for name, hidden_sink in hidden_sinks.items():
        root = _build_min_repo()
        try:
            worklog = _CLEAN_WORKLOG.replace("- [T-001] consumed\n\n", "本文。\n\n")
            phase3 = _CLEAN_PHASE3.replace(
                "- [T-900] deferred item",
                f"- [T-900] deferred item\n\n{hidden_sink}",
            )
            _write_backlog_docs(root, worklog_text=worklog, phase3_text=phase3)
            _assert_violation(root, "次の一手 ID [T-001]", "見送り台帳にもない")
        finally:
            shutil.rmtree(root, ignore_errors=True)


def test_backlog_guard_hidden_ledger_items_are_not_live_items():
    hidden_items = {
        "backtick fence": "```text\n- missing ID\n```",
        "tilde fence": "~~~text\n- missing ID\n~~~",
        "HTML comment": "<!--\n- missing ID\n-->",
    }
    for name, hidden_item in hidden_items.items():
        root = _build_min_repo()
        try:
            phase3 = _CLEAN_PHASE3.replace(
                "- [T-900] deferred item",
                f"- [T-900] deferred item\n\n{hidden_item}",
            )
            _write_backlog_docs(root, phase3_text=phase3)
            res = _run_check(root)
            assert res.returncode == 0, f"{name}:\n{res.stdout}"
        finally:
            shutil.rmtree(root, ignore_errors=True)


def test_backlog_guard_rejects_redundant_zero_padding():
    root = _build_min_repo()
    try:
        worklog = _CLEAN_WORKLOG.replace("[T-002]", "[T-0001]")
        _write_backlog_docs(root, worklog_text=worklog)
        _assert_violation(root, "項目先頭 ID '[T-0001]' が不正形式")
    finally:
        shutil.rmtree(root, ignore_errors=True)


def test_backlog_guard_completion_record_does_not_satisfy_sink():
    root = _build_min_repo()
    try:
        worklog = _CLEAN_WORKLOG.replace("- [T-001] consumed\n\n", "本文。\n\n")
        phase3 = _CLEAN_PHASE3.replace("- completed item", "- [T-001] completed item")
        _write_backlog_docs(root, worklog_text=worklog, phase3_text=phase3)
        _assert_violation(root, "次の一手 ID [T-001]", "見送り台帳にもない")
    finally:
        shutil.rmtree(root, ignore_errors=True)


def test_backlog_guard_checks_all_adjacent_transitions():
    root = _build_min_repo()
    try:
        worklog = """# worklog

## ローテーション

## 2026-01-01 (1) — first

### 次の一手
1. [T-001] dropped in middle

## 2026-01-02 (2) — second

- [T-900] unrelated

### 次の一手
1. [T-002] carried

## 2026-01-03 (3) — third

- [T-002] consumed

### 次の一手
1. [T-003] latest
"""
        _write_backlog_docs(root, worklog_text=worklog)
        res = _assert_violation(root, "次の一手 ID [T-001]")
        assert "次の一手 ID [T-002]" not in res.stdout, res.stdout
    finally:
        shutil.rmtree(root, ignore_errors=True)


def test_backlog_guard_checks_latest_archive_rotation_boundary():
    root = _build_min_repo()
    try:
        current = """# current

## ローテーション

## 2026-01-02 (2) — current first

### 次の一手
1. [T-002] current
"""
        archive_name = "worklog-synthetic-latest.md"
        archive = """# archive

## 2026-01-01 (1) — archive last

### 次の一手
1. [T-001] lost at rotation
"""
        _write_backlog_docs(root, worklog_text=current)
        _write(root, os.path.join("docs", "archive", archive_name), archive)
        _write(
            root,
            os.path.join("docs", "archive", "README.md"),
            f"# archive\n\n## 現在の収容物\n\n- `{archive_name}`\n",
        )
        _assert_violation(root, archive_name, "次の一手 ID [T-001]", "current first")
    finally:
        shutil.rmtree(root, ignore_errors=True)


def test_backlog_guard_checks_archive_internal_transitions():
    root = _build_min_repo()
    try:
        current = """# current

## ローテーション

## 2026-01-03 (3) — current

- [T-002] consumed

### 次の一手
1. [T-003] current
"""
        archive_name = "worklog-synthetic.md"
        archive = """# archive

## 2026-01-01 (1) — archive first

### 次の一手
1. [T-001] lost inside archive

## 2026-01-02 (2) — archive second

### 次の一手
1. [T-002] carried to current
"""
        _write_backlog_docs(root, worklog_text=current)
        _write(root, os.path.join("docs", "archive", archive_name), archive)
        _write(
            root,
            os.path.join("docs", "archive", "README.md"),
            f"# archive\n\n## 現在の収容物\n\n- `{archive_name}`\n",
        )
        _assert_violation(root, archive_name, "次の一手 ID [T-001]", "archive second")
    finally:
        shutil.rmtree(root, ignore_errors=True)


def test_backlog_guard_id_bearing_archive_entry_requires_ids_on_all_items():
    root = _build_min_repo()
    try:
        current = """# current

## ローテーション

## 2026-01-03 (3) — current

### 次の一手
1. [T-003] current
"""
        archive_name = "worklog-synthetic.md"
        archive = """# archive

## 2026-01-01 (1) — archive first

### 次の一手
1. [T-001] carry

## 2026-01-02 (2) — archive second

- [T-001] consumed

### 次の一手
1. missing ID
"""
        _write_backlog_docs(root, worklog_text=current)
        _write(root, os.path.join("docs", "archive", archive_name), archive)
        _write(
            root,
            os.path.join("docs", "archive", "README.md"),
            f"# archive\n\n## 現在の収容物\n\n- `{archive_name}`\n",
        )
        _assert_violation(
            root,
            archive_name,
            "エントリ '2026-01-02 (2) — archive second'",
            "項目先頭に有効な [T-NNN] ID がない",
        )
    finally:
        shutil.rmtree(root, ignore_errors=True)


def test_backlog_guard_checks_boundaries_between_all_archives():
    root = _build_min_repo()
    try:
        current = """# current

## ローテーション

## 2026-01-03 (3) — current

- [T-002] consumed

### 次の一手
1. [T-003] current
"""
        first_name = "worklog-first.md"
        second_name = "worklog-second.md"
        first = """# first archive

## 2026-01-01 (1) — first archive last

### 次の一手
1. [T-001] lost between archives
"""
        second = """# second archive

## 2026-01-02 (2) — second archive first

### 次の一手
1. [T-002] carried to current
"""
        _write_backlog_docs(root, worklog_text=current)
        _write(root, os.path.join("docs", "archive", first_name), first)
        _write(root, os.path.join("docs", "archive", second_name), second)
        _write(
            root,
            os.path.join("docs", "archive", "README.md"),
            "# archive\n\n## 現在の収容物\n\n"
            f"- `{first_name}`\n- `{second_name}`\n",
        )
        _assert_violation(root, first_name, "次の一手 ID [T-001]", "second archive first")
    finally:
        shutil.rmtree(root, ignore_errors=True)


def test_backlog_guard_latest_archive_is_selected_by_entry_date():
    root = _build_min_repo()
    try:
        current = """# current

## ローテーション

## 2026-02-02 (2) — current

### 次の一手
1. [T-002] current
"""
        older_name = "worklog-zz-older.md"
        newer_name = "worklog-aa-newer.md"
        older = """# older

## 2025-12-31 (1) — older

### 次の一手
1. legacy item
"""
        newer = """# newer

## 2026-02-01 (1) — newer

### 次の一手
1. [T-001] lost from chronologically latest archive
"""
        _write_backlog_docs(root, worklog_text=current)
        _write(root, os.path.join("docs", "archive", older_name), older)
        _write(root, os.path.join("docs", "archive", newer_name), newer)
        _write(
            root,
            os.path.join("docs", "archive", "README.md"),
            "# archive\n\n## 現在の収容物\n\n"
            f"- `{older_name}`\n- `{newer_name}`\n",
        )
        res = _assert_violation(root, newer_name, "次の一手 ID [T-001]")
        assert older_name not in res.stdout, res.stdout
    finally:
        shutil.rmtree(root, ignore_errors=True)


def test_backlog_guard_same_day_archives_use_entry_ordinal_not_filename():
    root = _build_min_repo()
    try:
        current = """# current

## ローテーション

## 2026-02-02 (3) — current

- [T-002] consumed

### 次の一手
1. [T-003] current
"""
        early_name = "worklog-z-early.md"
        late_name = "worklog-a-late.md"
        early = """# early

## 2026-02-01 (1) — early

### 次の一手
1. [T-001] carry across archive boundary
"""
        late = """# late

## 2026-02-01 (2) — late

- [T-001] consumed

### 次の一手
1. [T-002] carry to current
"""
        _write_backlog_docs(root, worklog_text=current)
        _write(root, os.path.join("docs", "archive", early_name), early)
        _write(root, os.path.join("docs", "archive", late_name), late)
        _write(
            root,
            os.path.join("docs", "archive", "README.md"),
            "# archive\n\n## 現在の収容物\n\n"
            f"- `{late_name}`\n- `{early_name}`\n",
        )
        res = _run_check(root)
        assert res.returncode == 0, res.stdout
    finally:
        shutil.rmtree(root, ignore_errors=True)


def test_backlog_guard_ambiguous_same_day_archive_order_is_violation():
    root = _build_min_repo()
    try:
        current = """# current

## ローテーション

## 2026-02-02 (2) — current

- [T-001] consumed

### 次の一手
1. [T-002] current
"""
        first_name = "worklog-a.md"
        second_name = "worklog-z.md"
        archive = """# archive

## 2026-02-01 (1) — same ordinal

### 次の一手
1. [T-001] carry
"""
        _write_backlog_docs(root, worklog_text=current)
        _write(root, os.path.join("docs", "archive", first_name), archive)
        _write(root, os.path.join("docs", "archive", second_name), archive)
        _write(
            root,
            os.path.join("docs", "archive", "README.md"),
            "# archive\n\n## 現在の収容物\n\n"
            f"- `{first_name}`\n- `{second_name}`\n",
        )
        _assert_violation(
            root,
            "archive worklog の順序を一意に決定できない",
            first_name,
            second_name,
        )
    finally:
        shutil.rmtree(root, ignore_errors=True)


def test_backlog_guard_latest_archive_structure_is_fail_closed():
    fixtures = {
        "zero entries": ("# archive\n", "日付付き worklog entry が 0 件"),
        "invalid H2": (
            "# archive\n\n## 9999-12-31 malformed entry\n",
            "entry title に full-match しない",
        ),
        "zero next": (
            "# archive\n\n## 2026-01-01 (1) — last\n\n本文。\n",
            "`### 次の一手` が 0 件",
        ),
        "multiple next": (
            "# archive\n\n## 2026-01-01 (1) — last\n\n"
            "### 次の一手\n1. [T-001] first\n\n"
            "### 次の一手 (duplicate)\n1. [T-002] second\n",
            "`### 次の一手` が 2 件",
        ),
    }
    for name, (archive, expected) in fixtures.items():
        root = _build_min_repo()
        try:
            archive_name = "worklog-synthetic-latest.md"
            _write(root, os.path.join("docs", "archive", archive_name), archive)
            _write(
                root,
                os.path.join("docs", "archive", "README.md"),
                f"# archive\n\n## 現在の収容物\n\n- `{archive_name}`\n",
            )
            _assert_violation(root, archive_name, expected)
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
