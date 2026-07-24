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
import re
import shutil
import subprocess
import sys
import tempfile

import pytest

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


def _write_command_guard_docs(root: str) -> None:
    def refs(pairs: set[tuple[str, str]] | frozenset[tuple[str, str]]) -> str:
        grouped: dict[str, list[str]] = {}
        for path, section in sorted(pairs):
            grouped.setdefault(path, []).append(section)
        chunks = []
        for path, sections in grouped.items():
            if path == "docs/skill-self-improvement.md":
                chunks.append(f"`{path}` の全節")
            elif (
                path == "docs/dev-wave/operations.md"
                and sections == [f"DW-O{i:02d}" for i in range(1, 21)]
            ):
                chunks.append(f"`{path}`: `DW-O01`〜`DW-O20`")
            else:
                ids = ", ".join(f"`{section}`" for section in sections)
                chunks.append(f"`{path}`: {ids}")
        return "; ".join(chunks)

    stage_rows = []
    for key, pairs in check_docs.STAGE_DISPATCH_CONTRACT.items():
        display_key = (
            f"{key} preflight" if key in {"段 2", "段 3", "段 8"} else key
        )
        grouped: dict[str, set[tuple[str, str]]] = {}
        for path, section in pairs:
            grouped.setdefault(path, set()).add((path, section))
        for path, path_pairs in sorted(grouped.items()):
            if key == "段 6" and path == "docs/dev-wave/workers.md":
                s05 = {
                    pair for pair in path_pairs
                    if pair[1].startswith("DW-S05-")
                }
                s06 = path_pairs - s05
                stage_rows.append(f"| {display_key} | {refs(s05)} |")
                stage_rows.append(f"| {display_key} | {refs(s06)} |")
            else:
                stage_rows.append(f"| {display_key} | {refs(path_pairs)} |")
    condition_rows = "\n".join(
        f"| {key} | synthetic | {refs(pairs)} |"
        for key, pairs in check_docs.CONDITION_DISPATCH_CONTRACT.items()
    )
    dev_wave = f"""---
description: synthetic dev-wave
argument-hint: [synthetic]
disable-model-invocation: true
---

$ARGUMENTS

条件には最遅読了段がある。`DW-O08`、`DW-O09`、`DW-O10` は段 1 brief 前、
`DW-O13` は段 2 プラン前が期限である。期限後に成立したら成果物を invalidate し、
前者は段 1 brief、後者は段 2 から再実行する。巻き戻し後は段・条件を再評価し、
旧成果物を流用してはならない。

## 段 dispatch

| 段 | 参照 |
|---|---|
{chr(10).join(stage_rows)}

段 6 で fix を codex へ再投する子は、`DW-S05-A`、`DW-S05-B`、`DW-S05-C` を
全文継承する。段 6 時点で成立している全条件の `DW-Oxx` も fix 操作の直前に読む。

## 条件 dispatch

| # | 条件 | 参照 |
|---|---|---|
{condition_rows}
"""
    cleanup = """---
description: synthetic cleanup
argument-hint: [synthetic]
---

$ARGUMENTS
docs/skill-self-improvement.md
"""
    rulings = """---
description: synthetic rulings
argument-hint: [synthetic]
---

$ARGUMENTS
docs/skill-self-improvement.md
"""
    _write(root, ".claude/commands/dev-wave.md", dev_wave)
    _write(root, ".claude/commands/cleanup-branches.md", cleanup)
    _write(root, ".claude/commands/rulings.md", rulings)

    for rel, sections in check_docs.REQUIRED_REFERENCE_SECTIONS.items():
        text = "# synthetic reference\n\n" + "\n\n".join(
            f"## {section} — synthetic\n\nbody"
            for section in sorted(sections)
        ) + "\n"
        _write(root, rel, text)

    self_doc = """# synthetic self

## 発火 gate

body

## routing

body

## command 入口の編集条件

body

## command 別の終端

### dev-wave

body

### cleanup-branches

body

### rulings

body

## 検査と commit 境界

body
"""
    _write(root, "docs/skill-self-improvement.md", self_doc)


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
    _write_command_guard_docs(root)
    return root


def _run_check(root: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, os.path.join(root, "tools", "check_docs.py")],
        capture_output=True, text=True,
    )


def _violation_count(res: subprocess.CompletedProcess) -> int:
    match = re.search(r"^check_docs: (\d+) 件の違反$", res.stdout, re.MULTILINE)
    assert match is not None, f"違反件数 header を解析できない:\n{res.stdout}"
    return int(match.group(1))


# ===== baseline: 合成 repo は違反なし (positive control の土台) =====

def test_synthetic_repo_baseline_clean():
    root = _build_min_repo()
    try:
        res = _run_check(root)
        assert res.returncode == 0, f"baseline が違反ありになった:\n{res.stdout}\n{res.stderr}"
        assert "違反なし" in res.stdout, res.stdout
    finally:
        shutil.rmtree(root, ignore_errors=True)


def _read(root: str, rel: str) -> str:
    with open(os.path.join(root, rel), encoding="utf-8") as f:
        return f.read()


def _pad_to_bytes(root: str, rel: str, target: int) -> None:
    text = _read(root, rel)
    current = len(text.encode("utf-8"))
    assert current <= target
    _write(root, rel, text + ("\n" * (target - current)))


def _rewrite_matching_lines(
    root: str,
    rel: str,
    predicate,
    rewrite,
    expected: int = 1,
) -> None:
    lines = _read(root, rel).splitlines(keepends=True)
    matched = sum(1 for line in lines if predicate(line))
    assert matched == expected, (rel, matched, expected)
    _write(
        root,
        rel,
        "".join(
            rewrite(line) if predicate(line) else line
            for line in lines
        ),
    )


def _mutate_command_guard(root: str, case: str) -> None:
    if case == "command_byte_over":
        _pad_to_bytes(
            root,
            ".claude/commands/cleanup-branches.md",
            check_docs.COMMAND_LIMITS[
                ".claude/commands/cleanup-branches.md"
            ].max_bytes + 1,
        )
    elif case == "reference_byte_over":
        _pad_to_bytes(
            root,
            "docs/dev-wave/mutation.md",
            check_docs.REFERENCE_LIMITS[
                "docs/dev-wave/mutation.md"
            ].max_bytes + 1,
        )
    elif case == "self_byte_over":
        _pad_to_bytes(
            root,
            "docs/skill-self-improvement.md",
            check_docs.SELF_LIMITS[
                "docs/skill-self-improvement.md"
            ].max_bytes + 1,
        )
    elif case == "long_line":
        rel = ".claude/commands/cleanup-branches.md"
        _write(root, rel, _read(root, rel) + ("x" * 111) + "\n")
    elif case == "unregistered_command":
        _write(root, ".claude/commands/extra.md", "# extra\n")
    elif case == "registered_command_deleted":
        os.remove(os.path.join(root, ".claude/commands/cleanup-branches.md"))
    elif case == "arguments_missing":
        rel = ".claude/commands/cleanup-branches.md"
        _write(root, rel, _read(root, rel).replace("$ARGUMENTS", "arguments"))
    elif case == "frontmatter_key_changed":
        rel = ".claude/commands/cleanup-branches.md"
        _write(root, rel, _read(root, rel).replace(
            "argument-hint:", "argument-hint-renamed:", 1
        ))
    elif case == "frontmatter_duplicate":
        rel = ".claude/commands/cleanup-branches.md"
        _write(root, rel, _read(root, rel).replace(
            "description: synthetic cleanup",
            "description: synthetic cleanup\ndescription: duplicate",
            1,
        ))
    elif case == "frontmatter_malformed":
        rel = ".claude/commands/cleanup-branches.md"
        _write(root, rel, _read(root, rel).replace("---", "not-frontmatter", 1))
    elif case == "disable_value_changed":
        rel = ".claude/commands/dev-wave.md"
        _write(root, rel, _read(root, rel).replace(
            "disable-model-invocation: true",
            "disable-model-invocation: false",
            1,
        ))
    elif case == "reference_section_deleted":
        rel = "docs/dev-wave/mutation.md"
        _write(root, rel, _read(root, rel).replace(
            "## DW-M05 — synthetic", "### removed DW-M05", 1
        ))
    elif case == "reference_section_duplicated":
        rel = "docs/dev-wave/mutation.md"
        _write(root, rel, _read(root, rel) + "\n## DW-M05 — duplicate\n")
    elif case == "stage2_operations_deleted":
        _rewrite_matching_lines(
            root,
            ".claude/commands/dev-wave.md",
            lambda line: line.startswith("| 段 2 preflight |")
            and "`docs/dev-wave/operations.md`" in line,
            lambda line: "",
        )
    elif case == "stage3_o13_deleted":
        _rewrite_matching_lines(
            root,
            ".claude/commands/dev-wave.md",
            lambda line: line.startswith("| 段 3 preflight |")
            and "`docs/dev-wave/operations.md`" in line,
            lambda line: line.replace(", `DW-O13`", ""),
        )
    elif case == "stage6_s05_inheritance_deleted":
        _rewrite_matching_lines(
            root,
            ".claude/commands/dev-wave.md",
            lambda line: line.startswith("| 段 6 |")
            and "`DW-S05-A`" in line,
            lambda line: "",
        )
    elif case == "stage6_all_operations_deleted":
        _rewrite_matching_lines(
            root,
            ".claude/commands/dev-wave.md",
            lambda line: line.startswith("| 段 6 |")
            and "`docs/dev-wave/operations.md`" in line,
            lambda line: "",
        )
    elif case == "stage8_operations_deleted":
        _rewrite_matching_lines(
            root,
            ".claude/commands/dev-wave.md",
            lambda line: line.startswith("| 段 8 preflight |")
            and "`docs/dev-wave/operations.md`" in line,
            lambda line: "",
        )
    elif case == "stage8_self_deleted":
        _rewrite_matching_lines(
            root,
            ".claude/commands/dev-wave.md",
            lambda line: line.startswith("| 段 8 preflight |")
            and "`docs/skill-self-improvement.md`" in line,
            lambda line: "",
        )
    elif case == "condition_o13_deleted":
        _rewrite_matching_lines(
            root,
            ".claude/commands/dev-wave.md",
            lambda line: line.startswith("| 13 |"),
            lambda line: "",
        )
    elif case == "condition_all_operations_deleted":
        _rewrite_matching_lines(
            root,
            ".claude/commands/dev-wave.md",
            lambda line: re.match(r"^\| (?:0[1-9]|1[0-9]|20) \|", line)
            is not None,
            lambda line: "",
            expected=20,
        )
    elif case == "condition_supervisor_deleted":
        _rewrite_matching_lines(
            root,
            ".claude/commands/dev-wave.md",
            lambda line: line.startswith("| 22 |"),
            lambda line: "",
        )
    elif case == "self_heading_deleted":
        rel = "docs/skill-self-improvement.md"
        _write(root, rel, _read(root, rel).replace(
            "## routing\n", "", 1
        ))
    elif case == "self_h3_deleted":
        rel = "docs/skill-self-improvement.md"
        _write(root, rel, _read(root, rel).replace(
            "### cleanup-branches\n", "", 1
        ))
    elif case == "self_long_line":
        rel = "docs/skill-self-improvement.md"
        _write(root, rel, _read(root, rel) + ("x" * 101) + "\n")
    elif case == "self_reference_deleted":
        rel = ".claude/commands/cleanup-branches.md"
        _write(root, rel, _read(root, rel).replace(
            "docs/skill-self-improvement.md", "self contract omitted", 1
        ))
    elif case == "reference_orphan_h2":
        rel = "docs/dev-wave/operations.md"
        _write(root, rel, _read(root, rel) + "\n## DW-X99 — orphan\n\nbody\n")
    elif case == "dispatch_heading_duplicated":
        rel = ".claude/commands/dev-wave.md"
        _write(root, rel, _read(root, rel) + "\n## 段 dispatch\n\n")
    elif case == "dispatch_heading_missing":
        rel = ".claude/commands/dev-wave.md"
        _write(root, rel, _read(root, rel).replace(
            "## 条件 dispatch", "## 条件 dispatch omitted", 1
        ))
    elif case == "d2_rollback_body_deleted":
        rel = ".claude/commands/dev-wave.md"
        text = _read(root, rel)
        changed = re.sub(
            r"条件には最遅読了段がある。.*?旧成果物を流用してはならない。\n\n",
            "",
            text,
            count=1,
            flags=re.DOTALL,
        )
        assert changed != text
        _write(root, rel, changed)
    elif case == "d4_inheritance_body_deleted":
        rel = ".claude/commands/dev-wave.md"
        text = _read(root, rel)
        changed = re.sub(
            r"段 6 で fix を codex へ再投する子は、.*?"
            r"fix 操作の直前に読む。\n\n",
            "",
            text,
            count=1,
            flags=re.DOTALL,
        )
        assert changed != text
        _write(root, rel, changed)
    elif case == "fifth_reference":
        _write(root, "docs/dev-wave/extra.md", "# extra\n")
    elif case == "nested_reference":
        _write(root, "docs/dev-wave/appendix/extra.md", "# extra\n")
    elif case == "non_md_reference":
        _write(root, "docs/dev-wave/extra.txt", "extra\n")
    elif case == "aggregate_over":
        for rel, limit in check_docs.REFERENCE_LIMITS.items():
            _pad_to_bytes(root, rel, limit.max_bytes - 1)
    elif case == "invalid_utf8":
        path = os.path.join(root, "docs/dev-wave/core.md")
        with open(path, "wb") as f:
            f.write(b"\xff")
    elif case == "symlink":
        path = os.path.join(root, "docs/dev-wave/core.md")
        os.remove(path)
        os.symlink("workers.md", path)
    elif case == "non_regular":
        path = os.path.join(root, "docs/dev-wave/mutation.md")
        os.remove(path)
        os.mkfifo(path)
    elif case == "registered_reference_deleted":
        os.remove(os.path.join(root, "docs/dev-wave/operations.md"))
    elif case == "dispatch_allowlist":
        _rewrite_matching_lines(
            root,
            ".claude/commands/dev-wave.md",
            lambda line: line.startswith("| wave 開始 |"),
            lambda line: line.removesuffix(" |\n")
            + "; `docs/failures.md` |\n",
        )
    else:
        raise AssertionError(f"unknown case: {case}")


_COMMAND_GUARD_CASES = [
    "command_byte_over",
    "reference_byte_over",
    "self_byte_over",
    "long_line",
    "unregistered_command",
    "registered_command_deleted",
    "arguments_missing",
    "frontmatter_key_changed",
    "frontmatter_duplicate",
    "frontmatter_malformed",
    "disable_value_changed",
    "reference_section_deleted",
    "reference_section_duplicated",
    "stage2_operations_deleted",
    "stage3_o13_deleted",
    "stage6_s05_inheritance_deleted",
    "stage6_all_operations_deleted",
    "stage8_operations_deleted",
    "stage8_self_deleted",
    "condition_o13_deleted",
    "condition_all_operations_deleted",
    "condition_supervisor_deleted",
    "self_heading_deleted",
    "self_h3_deleted",
    "self_long_line",
    "self_reference_deleted",
    "reference_orphan_h2",
    "dispatch_heading_duplicated",
    "dispatch_heading_missing",
    "d2_rollback_body_deleted",
    "d4_inheritance_body_deleted",
    "fifth_reference",
    "nested_reference",
    "non_md_reference",
    "aggregate_over",
    "invalid_utf8",
    "symlink",
    "non_regular",
    "registered_reference_deleted",
    "dispatch_allowlist",
]

_COMMAND_GUARD_NEEDLES = {
    "command_byte_over": "bytes > 予算",
    "reference_byte_over": "bytes > 予算",
    "self_byte_over": "bytes > 予算",
    "long_line": "最長行予算",
    "unregistered_command": "command byte予算が未登録",
    "registered_command_deleted": "予算登録済み command が不在",
    "arguments_missing": "$ARGUMENTS が 0 件",
    "frontmatter_key_changed": "frontmatter key 集合が契約と不一致",
    "frontmatter_duplicate": "frontmatter key 重複",
    "frontmatter_malformed": "frontmatter を一意に解析できない",
    "disable_value_changed": "disable-model-invocation は 'true' 必須",
    "reference_section_deleted": "H2 見出し DW-M05 が 0 件",
    "reference_section_duplicated": "H2 見出し DW-M05 が 2 件",
    "stage2_operations_deleted": "段 dispatch '段 2' が契約と不一致",
    "stage3_o13_deleted": "段 dispatch '段 3' が契約と不一致",
    "stage6_s05_inheritance_deleted": "段 dispatch '段 6' が契約と不一致",
    "stage6_all_operations_deleted": "段 dispatch '段 6' が契約と不一致",
    "stage8_operations_deleted": "段 dispatch '段 8' が契約と不一致",
    "stage8_self_deleted": "段 dispatch '段 8' が契約と不一致",
    "condition_o13_deleted": "条件 dispatch '13' が契約と不一致",
    "condition_all_operations_deleted": "条件 dispatch '01' が契約と不一致",
    "condition_supervisor_deleted": "条件 dispatch '22' が契約と不一致",
    "self_heading_deleted": "H2 見出し 'routing' が 0 件",
    "self_h3_deleted": "H3 見出し 'cleanup-branches' が 0 件",
    "self_long_line": "最長行予算",
    "self_reference_deleted": "docs/skill-self-improvement.md への到達性がない",
    "reference_orphan_h2": "dispatch 契約にない孤児 H2",
    "dispatch_heading_duplicated": "段/条件 dispatch 表を一意に抽出できない",
    "dispatch_heading_missing": "段/条件 dispatch 表を一意に抽出できない",
    "d2_rollback_body_deleted": "D2 巻き戻し構造",
    "d4_inheritance_body_deleted": "D4 fix 子の段5全文継承",
    "fifth_reference": "docs/dev-wave/** の予算未登録実体",
    "nested_reference": "docs/dev-wave/** の予算未登録実体",
    "non_md_reference": "docs/dev-wave/** の予算未登録実体",
    "aggregate_over": "hard ceiling",
    "invalid_utf8": "invalid UTF-8",
    "symlink": "symlink または regular file 以外",
    "non_regular": "symlink または regular file 以外",
    "registered_reference_deleted": "登録済み dev-wave reference が不在",
    "dispatch_allowlist": "規範 dispatch の参照先が allowlist 外",
}
_COMMAND_GUARD_EXPECTED_COUNTS = {
    case: 1 for case in _COMMAND_GUARD_CASES
}
_COMMAND_GUARD_EXPECTED_COUNTS["condition_all_operations_deleted"] = 20


@pytest.mark.parametrize("case", _COMMAND_GUARD_CASES)
def test_command_docs_guard_positive_controls(case):
    """各 finding 分岐は baseline からケース別の期待件数だけ増える。"""

    root = _build_min_repo()
    try:
        baseline = _run_check(root)
        assert baseline.returncode == 0, baseline.stdout
        _mutate_command_guard(root, case)
        res = _run_check(root)
        assert res.returncode == 1, (
            f"{case}: positive control が赤にならなかった:\n{res.stdout}\n{res.stderr}"
        )
        assert _violation_count(res) == _COMMAND_GUARD_EXPECTED_COUNTS[case], (
            f"{case}: baseline との差分件数が期待値と違う:\n{res.stdout}"
        )
        assert _COMMAND_GUARD_NEEDLES[case] in res.stdout, (
            f"{case}: 対応する finding 分岐が発火していない:\n{res.stdout}"
        )
    finally:
        shutil.rmtree(root, ignore_errors=True)


# ===== positive control: 列挙対象を 1 個消すと違反が出る (F9 の核心) =====

def test_missing_enumerated_doc_is_violation():
    root = _build_min_repo()
    try:
        rels = _enumerated_rels()
        assert rels, "列挙対象が空 — _ENUMERATED_DOCS の抽出に失敗している"
        governed = {
            *check_docs.REFERENCE_LIMITS,
            *check_docs.SELF_LIMITS,
        }
        candidates = [rel for rel in rels if rel not in governed]
        assert candidates, "command guard 外の LIVING_DOCS 対象がない"
        victim = candidates[len(candidates) // 2]
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
        assert _violation_count(res) == 1, (
            f"不在検査以外も発火している:\n{res.stdout}"
        )
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
        calls = (
            [(case, (case,)) for case in _COMMAND_GUARD_CASES]
            if fn is test_command_docs_guard_positive_controls
            else [(fn.__name__, ())]
        )
        for label, args in calls:
            display = (
                f"{fn.__name__}[{label}]"
                if args else fn.__name__
            )
            try:
                fn(*args)
                print(f"PASS {display}")
                passed += 1
            except AssertionError as e:
                print(f"FAIL {display}: {e}")
                failed += 1
            except Exception as e:  # noqa: BLE001
                print(f"ERROR {display}: {type(e).__name__}: {e}")
                failed += 1
    print(f"\n{passed} passed, {failed} failed")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(_run())
