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

import contextlib
import importlib.util
import io
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


# operations 由来の条件 dispatch key (O07 削除後 19 件)。契約から導出するが、
# exact な外延は test_operation_contract_pins_exact_section_set が literal で pin する。
_OPERATION_CONDITION_KEYS = sorted(
    key
    for key, pairs in check_docs.CONDITION_DISPATCH_CONTRACT.items()
    if any(path == "docs/dev-wave/operations.md" for path, _ in pairs)
)


_PLACEHOLDER_DEBT_WORKLOG = (
    "  repo scan invariant (F34) は本 docs commit 後に再走 <反映>。"
)
_PLACEHOLDER_DEBT_ARCHIVE_ACCEPTANCE = (
    "- **受入**: <受入全走結果を反映> / check_docs / check_ai_provenance (324) / "
    "repo scan invariant (F34) 緑 <反映>。"
)
_PLACEHOLDER_MENTION_WORKLOG_F36 = (
    "- **F36 新設**: 受入・検査の結果欄の `<反映>` プレースホルダが独立 3 wave + insight 1 本で残存し、"
)
_PLACEHOLDER_MENTION_WORKLOG_T094_A = (
    "- **[T-094]**: 機械検出を**採用**し設計も確定 — 検出は `<反映>` / `<受入結果を反映>` /"
)
_PLACEHOLDER_MENTION_WORKLOG_T094_B = (
    "  `<受入全走結果を反映>` の exact 3 文字列、対象は `docs/worklog.md` と verbatim でない"
)
_PLACEHOLDER_DEBT_INSIGHT = (
    "- 受入全走: <受入結果を反映>。check_docs / check_ai_provenance (324) / "
    "repo scan invariant (F34): <反映>。"
)
_PLACEHOLDER_MENTION_INSIGHT_A = (
    "   4件の `<反映>` は F34 恒久対応の実行証拠にならない。`check_docs` も意味的な反映漏れを検出しないと明記する "
    "(`tools/check_docs.py:7-10`)。独立3 wave は族一般化条件を満たす (`docs/dev-wave/core.md:45-48`) ため、"
    "P8 の「新 gate なので見送る」は根拠不足。  "
)
_PLACEHOLDER_MENTION_INSIGHT_B = (
    "  裁定パッケージでは、候補検出対象を少なくとも `<反映>`、`<受入結果を反映>`、"
    "`<受入全走結果を反映>` の exact literal、対象を `docs/worklog.md`、"
    "`docs/archive/worklog-*.md`、非-verbatim の `output/insights/*.md` とし、既存四件は path だけでなく"
    "「含有行 digest + token count」で固定する案を比較すべきである。単なる `<[^>]*反映[^>]*>` は"
    "日本語メタ変数や欠陥説明の引用を誤検出する。"
)
_PLACEHOLDER_ARCHIVE_NAME = "worklog-phase3-0722-0724.md"

_PLACEHOLDER_WORKLOG_ENTRIES = f"""## 2026-07-25 (1) — [T-067] oracle refusal exact 化残余を消化 (test-only、branch worktree-dev-wave-e2e-real-seal、計測なし)

{_PLACEHOLDER_DEBT_WORKLOG}

### 次の一手

## 2026-07-25 (3) — [T-068][T-077][T-078] を R 発効により確定的に closure (docs-only・コード 0 byte、branch worktree-dev-wave-e2e-real-seal、計測なし)

{_PLACEHOLDER_MENTION_WORKLOG_F36}

### 次の一手

## 2026-07-25 (4) — /rulings: 裁定待ち 5 件をユーザーが推奨どおり一括裁定 — official 解禁を承認 (D86 起票、計測なし)

{_PLACEHOLDER_MENTION_WORKLOG_T094_A}
{_PLACEHOLDER_MENTION_WORKLOG_T094_B}

### 次の一手
"""

_CLEAN_WORKLOG = f"""# synthetic worklog

## ローテーション

## 2026-08-01 (1) — first

### 次の一手
1. [T-001] carry

## 2026-08-02 (2) — second

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


def _write_bytes(root: str, rel: str, content: bytes) -> None:
    path = os.path.join(root, rel)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "wb") as f:
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


def _archive_readme(*names: str) -> str:
    all_names = (_PLACEHOLDER_ARCHIVE_NAME, *names)
    return (
        "# archive\n\n## 現在の収容物\n\n"
        + "".join(f"- `{name}`\n" for name in all_names)
    )


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
                and sections == [
                    f"DW-O{i:02d}"
                    for i in check_docs._OPERATION_NUMBERS
                ]
            ):
                chunks.append(
                    f"`{path}`: `DW-O01`〜`DW-O06`, `DW-O08`〜`DW-O20`"
                )
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

コード・テスト・実行可能資材（以下「実装面」）は軽量版でも
Codex `role=author` が書き、親は実装面を直接編集せず統合する。

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
    codex_skill = """---
name: dev-wave
description: synthetic Codex dev-wave skill
---

# Dev Wave

""" + "\n".join(check_docs.CODEX_DEV_WAVE_SKILL_LITERALS) + "\n"
    _write(root, ".agents/skills/dev-wave/SKILL.md", codex_skill)
    _write(
        root,
        ".agents/skills/dev-wave/agents/openai.yaml",
        check_docs.CODEX_DEV_WAVE_OPENAI_YAML,
    )

    for rel, sections in check_docs.REQUIRED_REFERENCE_SECTIONS.items():
        text = "# synthetic reference\n\n" + "\n\n".join(
            f"## {section} — synthetic\n\nbody"
            for section in sorted(sections)
        ) + "\n"
        literals = check_docs.CODEX_FIRST_REFERENCE_LITERALS.get(rel, ())
        if literals:
            text += "\n" + "\n".join(literals) + "\n"
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
           _archive_readme())
    _write(
        root,
        os.path.join("docs", "archive", _PLACEHOLDER_ARCHIVE_NAME),
        "# synthetic archive\n\n"
        "## 2026-07-24 (4) — 統合 E2E: 実 seal を official floor 経路に通す (D79(7) 部分閉鎖、branch worktree-dev-wave-e2e-real-seal、計測なし)\n\n"
        f"{_PLACEHOLDER_DEBT_ARCHIVE_ACCEPTANCE}\n"
        "\n"
        "## 2026-07-24 (5) — [T-086] PKG-2: FROZEN_MANIFEST exact key-set 暫定 assert (test-only、branch worktree-dev-wave-e2e-real-seal、計測なし)\n\n"
        f"{_PLACEHOLDER_DEBT_WORKLOG}\n\n"
        "### 次の一手\n\n"
        f"{_PLACEHOLDER_WORKLOG_ENTRIES}",
    )
    _write(
        root,
        os.path.join("output", "insights", "2026-07-24_e2e-real-seal.md"),
        f"{_PLACEHOLDER_DEBT_INSIGHT}\n",
    )
    _write(
        root,
        os.path.join(
            "output",
            "insights",
            "2026-07-25_t068-t077-t078-closure-verbatim.md",
        ),
        f"{_PLACEHOLDER_MENTION_INSIGHT_A}\n"
        f"{_PLACEHOLDER_MENTION_INSIGHT_B}\n",
    )
    # backlog guard の必須構造。phase3.md は上の列挙 placeholder を上書きする。
    _write_backlog_docs(root)
    _write_command_guard_docs(root)
    return root


def _run_check(root: str, *, timeout: float | None = None) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, os.path.join(root, "tools", "check_docs.py")],
        capture_output=True, text=True,
        timeout=timeout,
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


def _load_fixture_checker(root: str):
    module_name = f"_check_docs_fixture_{id(root)}"
    path = os.path.join(root, "tools", "check_docs.py")
    spec = importlib.util.spec_from_file_location(module_name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


def _placeholder_findings(root: str) -> list[str]:
    module = _load_fixture_checker(root)
    findings: list[str] = []
    module._check_literal_placeholder_guard(findings)
    return findings


def _assert_placeholder_violation(root: str, *needles: str) -> list[str]:
    findings = _placeholder_findings(root)
    assert findings, "placeholder 違反 fixture が赤にならなかった"
    rendered = "\n".join(findings)
    for needle in needles:
        assert needle in rendered, f"{needle!r} が finding にない:\n{rendered}"
    return findings


def _assert_other_checkers_clean(root: str) -> None:
    module = _load_fixture_checker(root)
    module._check_literal_placeholder_guard = lambda findings: set()
    output = io.StringIO()
    with contextlib.redirect_stdout(output):
        rc = module.main()
    assert rc == 0, output.getvalue()


def test_placeholder_guard_each_literal_independently_fires():
    literals = (
        "<反映>",
        "<受入結果を反映>",
        "<受入全走結果を反映>",
    )
    for literal in literals:
        root = _build_min_repo()
        try:
            _write(
                root,
                "output/insights/independent.md",
                f"independent control: {literal}\n",
            )
            findings = _assert_placeholder_violation(
                root, "未許可のリテラル placeholder", repr(literal)
            )
            assert len(findings) == 1, findings
        finally:
            shutil.rmtree(root, ignore_errors=True)


def test_placeholder_guard_main_propagates_finding_to_rc():
    root = _build_min_repo()
    try:
        rel = "output/insights/2026-07-24_e2e-real-seal.md"
        _write(root, rel, _read(root, rel) + "main wiring control: <反映>\n")
        res = _run_check(root)
        assert res.returncode == 1, res.stdout
        assert "check_docs: 1 件の違反" in res.stdout, res.stdout
        assert "未許可のリテラル placeholder" in res.stdout, res.stdout
    finally:
        shutil.rmtree(root, ignore_errors=True)


def test_placeholder_guard_new_literal_is_violation_in_each_family():
    cases = (
        ("docs/worklog.md", "worklog control: <反映>\n"),
        (
            "docs/archive/worklog-phase3-0722-0724.md",
            "archive control: <受入結果を反映>\n",
        ),
        (
            "output/insights/2026-07-24_e2e-real-seal.md",
            "insight control: <受入全走結果を反映>\n",
        ),
    )
    for rel, addition in cases:
        root = _build_min_repo()
        try:
            _write(root, rel, _read(root, rel) + addition)
            findings = _assert_placeholder_violation(
                root, rel, "未許可のリテラル placeholder"
            )
            assert len(findings) == 1, findings
        finally:
            shutil.rmtree(root, ignore_errors=True)


def test_placeholder_guard_detects_new_family_member():
    cases = (
        (
            "docs/archive/worklog-new.md",
            "# new archive\n\n"
            "## 2025-12-30 (1) — new archive\n\n"
            "new archive member: <反映>\n\n"
            "### 次の一手\n"
            "1. legacy item\n",
        ),
        (
            "output/insights/new-insight.md",
            "new insight member: <反映>\n",
        ),
    )
    for rel, content in cases:
        root = _build_min_repo()
        try:
            _write(root, rel, content)
            if rel.startswith("docs/archive/"):
                readme_rel = "docs/archive/README.md"
                _write(
                    root,
                    readme_rel,
                    _read(root, readme_rel) + "- `worklog-new.md`\n",
                )
            _assert_other_checkers_clean(root)
            findings = _assert_placeholder_violation(
                root, rel, "未許可のリテラル placeholder"
            )
            assert len(findings) == 1, findings
        finally:
            shutil.rmtree(root, ignore_errors=True)


def test_placeholder_guard_registered_line_removal_is_violation():
    root = _build_min_repo()
    try:
        rel = "output/insights/2026-07-24_e2e-real-seal.md"
        _write(root, rel, _read(root, rel).replace(
            _PLACEHOLDER_DEBT_INSIGHT + "\n", "", 1
        ))
        findings = _assert_placeholder_violation(
            root,
            rel,
            "KNOWN_PLACEHOLDER_DEBTS",
            "expected=1, actual=0",
        )
        assert len(findings) == 1, findings
    finally:
        shutil.rmtree(root, ignore_errors=True)


def test_placeholder_guard_registered_line_content_change_is_violation():
    root = _build_min_repo()
    try:
        rel = f"docs/archive/{_PLACEHOLDER_ARCHIVE_NAME}"
        changed = _PLACEHOLDER_DEBT_WORKLOG.replace("repo scan", "Repo scan", 1)
        _write(
            root,
            rel,
            _read(root, rel).replace(_PLACEHOLDER_DEBT_WORKLOG, changed, 1),
        )
        findings = _assert_placeholder_violation(
            root,
            rel,
            "未許可のリテラル placeholder",
            "KNOWN_PLACEHOLDER_DEBTS",
            "expected=1, actual=0",
        )
        assert len(findings) == 2, findings
    finally:
        shutil.rmtree(root, ignore_errors=True)


def test_placeholder_guard_registered_line_duplication_is_violation():
    root = _build_min_repo()
    try:
        rel = f"docs/archive/{_PLACEHOLDER_ARCHIVE_NAME}"
        heading = (
            "## 2026-07-25 (1) — [T-067] oracle refusal exact 化残余を消化 "
            "(test-only、branch worktree-dev-wave-e2e-real-seal、計測なし)"
        )
        original = f"{heading}\n\n{_PLACEHOLDER_DEBT_WORKLOG}\n"
        duplicated = (
            f"{heading}\n\n{_PLACEHOLDER_DEBT_WORKLOG}\n"
            f"{_PLACEHOLDER_DEBT_WORKLOG}\n"
        )
        text = _read(root, rel)
        assert original in text
        _write(root, rel, text.replace(original, duplicated, 1))
        findings = _assert_placeholder_violation(
            root,
            "worklog-entry:4926160d0e41c9e972953e535dcce8cc1744eff78b13277cc91d722dc06129f2",
            "37c4a1747e10844c9c4deb2281e644bd655cc80409b80c09c0a840297d6e8ef0",
            "expected=1, actual=2",
        )
        assert len(findings) == 1, findings
    finally:
        shutil.rmtree(root, ignore_errors=True)


def test_placeholder_guard_same_file_record_replay_is_violation():
    root = _build_min_repo()
    try:
        rel = f"docs/archive/{_PLACEHOLDER_ARCHIVE_NAME}"
        source_heading = (
            "## 2026-07-25 (1) — [T-067] oracle refusal exact 化残余を消化 "
            "(test-only、branch worktree-dev-wave-e2e-real-seal、計測なし)"
        )
        target_heading = (
            "## 2026-07-25 (4) — /rulings: 裁定待ち 5 件をユーザーが推奨どおり"
            "一括裁定 — official 解禁を承認 (D86 起票、計測なし)"
        )
        text = _read(root, rel)
        source = f"{source_heading}\n\n{_PLACEHOLDER_DEBT_WORKLOG}\n"
        target = f"{target_heading}\n\n"
        assert source in text and target in text
        text = text.replace(source, f"{source_heading}\n", 1)
        text = text.replace(
            target,
            f"{target_heading}\n\n{_PLACEHOLDER_DEBT_WORKLOG}\n",
            1,
        )
        _write(root, rel, text)
        findings = _assert_placeholder_violation(
            root,
            rel,
            "未許可のリテラル placeholder",
            "worklog-entry:4926160d0e41c9e972953e535dcce8cc1744eff78b13277cc91d722dc06129f2",
            "expected=1, actual=0",
        )
        assert len(findings) == 2, findings
    finally:
        shutil.rmtree(root, ignore_errors=True)


def test_placeholder_guard_duplicate_worklog_h2_is_violation():
    root = _build_min_repo()
    try:
        rel = f"docs/archive/{_PLACEHOLDER_ARCHIVE_NAME}"
        heading = (
            "## 2026-07-25 (1) — [T-067] oracle refusal exact 化残余を消化 "
            "(test-only、branch worktree-dev-wave-e2e-real-seal、計測なし)"
        )
        text = _read(root, rel)
        assert text.count(heading) == 1
        _write(root, rel, text + f"\n{heading}\n")
        findings = _placeholder_findings(root)
        assert len(findings) == 1, findings
        rendered = findings[0]
        assert "worklog 族の H2 raw bytes が重複" in rendered
        assert heading in rendered
        assert rendered.count(rel) == 2, rendered
    finally:
        shutil.rmtree(root, ignore_errors=True)

    root = _build_min_repo()
    try:
        rel = f"docs/archive/{_PLACEHOLDER_ARCHIVE_NAME}"
        tab_heading = "##\t2026-07-30 (1) — tab-separated duplicate"
        _write(
            root,
            rel,
            _read(root, rel)
            + f"\n{tab_heading}\n\nbody\n\n{tab_heading}\n",
        )
        findings = _placeholder_findings(root)
        assert len(findings) == 1, findings
        rendered = findings[0]
        assert "worklog 族の H2 raw bytes が重複" in rendered
        assert repr(tab_heading) in rendered
        assert rendered.count(rel) == 2, rendered
    finally:
        shutil.rmtree(root, ignore_errors=True)


def test_placeholder_guard_h2_collision_replay_is_violation():
    root = _build_min_repo()
    try:
        source_rel = f"docs/archive/{_PLACEHOLDER_ARCHIVE_NAME}"
        replay_rel = "docs/archive/worklog-h2-collision.md"
        heading = (
            "## 2026-07-25 (1) — [T-067] oracle refusal exact 化残余を消化 "
            "(test-only、branch worktree-dev-wave-e2e-real-seal、計測なし)"
        )
        source = _read(root, source_rel)
        registered = f"{heading}\n\n{_PLACEHOLDER_DEBT_WORKLOG}\n"
        assert registered in source
        _write(
            root,
            source_rel,
            source.replace(
                registered,
                f"{heading}\n",
                1,
            ),
        )
        _write(
            root,
            replay_rel,
            f"# collision replay\n\n{heading}\n\n"
            f"{_PLACEHOLDER_DEBT_WORKLOG}\n\n### 次の一手\n",
        )
        findings = _placeholder_findings(root)
        assert len(findings) == 1, findings
        rendered = findings[0]
        assert "worklog 族の H2 raw bytes が重複" in rendered
        assert source_rel in rendered and replay_rel in rendered
    finally:
        shutil.rmtree(root, ignore_errors=True)

    root = _build_min_repo()
    try:
        source_rel = f"docs/archive/{_PLACEHOLDER_ARCHIVE_NAME}"
        replay_rel = "docs/archive/worklog-tab-scope-replay.md"
        heading = (
            "## 2026-07-25 (1) — [T-067] oracle refusal exact 化残余を消化 "
            "(test-only、branch worktree-dev-wave-e2e-real-seal、計測なし)"
        )
        source = _read(root, source_rel)
        registered = f"{heading}\n\n{_PLACEHOLDER_DEBT_WORKLOG}\n"
        assert registered in source
        _write(
            root,
            source_rel,
            source.replace(registered, f"{heading}\n", 1),
        )
        tab_heading = heading.replace("## ", "##\t", 1)
        _write(
            root,
            replay_rel,
            f"# tab scope replay\n\n{tab_heading}\n\n"
            f"{_PLACEHOLDER_DEBT_WORKLOG}\n\n### 次の一手\n",
        )
        findings = _placeholder_findings(root)
        rendered = "\n".join(findings)
        assert len(findings) == 2, findings
        assert "未許可のリテラル placeholder" in rendered
        assert "expected=1, actual=0" in rendered
        assert "worklog 族の H2 raw bytes が重複" not in rendered
    finally:
        shutil.rmtree(root, ignore_errors=True)


def test_placeholder_guard_entry_rotation_keeps_ledger_green():
    registered_heading = (
        "## 2026-07-25 (4) — /rulings: 裁定待ち 5 件をユーザーが推奨どおり"
        "一括裁定 — official 解禁を承認 (D86 起票、計測なし)"
    )
    first_current_heading = "## 2026-08-01 (1) — first"
    original_first_heading = (
        "## 2026-07-24 (4) — 統合 E2E: 実 seal を official floor 経路に通す "
        "(D79(7) 部分閉鎖、branch worktree-dev-wave-e2e-real-seal、計測なし)"
    )

    def place_registered_entry_in_current(root: str) -> str:
        archive_rel = f"docs/archive/{_PLACEHOLDER_ARCHIVE_NAME}"
        worklog_rel = "docs/worklog.md"
        archive = _read(root, archive_rel)
        start = archive.index(registered_heading)
        entry = archive[start:]
        _write(root, archive_rel, archive[:start])

        assert entry.rstrip().endswith("### 次の一手")
        entry = entry.rstrip() + "\n1. [T-099] rotation handoff\n\n"
        worklog = _read(root, worklog_rel)
        marker = first_current_heading
        assert marker in worklog
        worklog = worklog.replace(
            first_current_heading,
            f"{first_current_heading}\n\n- [T-099] rotation sink",
            1,
        )
        _write(
            root,
            worklog_rel,
            worklog.replace(first_current_heading, entry + first_current_heading, 1),
        )
        baseline = _run_check(root)
        current_res = baseline
        assert current_res.returncode == 0, current_res.stdout
        return entry

    # H2 を現行 worklog に残し、登録行だけを後続 H2 へ移す対は赤。
    root = _build_min_repo()
    try:
        entry = place_registered_entry_in_current(root)
        worklog = _read(root, "docs/worklog.md")
        assert entry in worklog
        worklog = worklog.replace(
            _PLACEHOLDER_MENTION_WORKLOG_T094_A + "\n",
            "",
            1,
        )
        worklog = worklog.replace(
            first_current_heading,
            f"{first_current_heading}\n\n{_PLACEHOLDER_MENTION_WORKLOG_T094_A}",
            1,
        )
        _write(root, "docs/worklog.md", worklog)

        # baseline にない archive member と README 索引を作り、非空遷移も成立させる。
        new_name = "worklog-rotation-prelude.md"
        _write(
            root,
            f"docs/archive/{new_name}",
            "# rotation prelude\n\n"
            "## 2026-07-23 (1) — rotation prelude\n\n"
            "### 次の一手\n"
            "1. [T-098] archive boundary control\n",
        )
        archive_rel = f"docs/archive/{_PLACEHOLDER_ARCHIVE_NAME}"
        archive = _read(root, archive_rel)
        assert original_first_heading in archive
        _write(
            root,
            archive_rel,
            archive.replace(
                original_first_heading,
                f"{original_first_heading}\n\n- [T-098] archive boundary sink",
                1,
            ).replace(
                "## 2026-07-24 (5) — [T-086] PKG-2:",
                "### 次の一手\n\n## 2026-07-24 (5) — [T-086] PKG-2:",
                1,
            ),
        )
        _write(root, "docs/archive/README.md", _archive_readme(new_name))
        _assert_other_checkers_clean(root)
        replay_res = _run_check(root)
        assert replay_res.returncode == 1, replay_res.stdout
        assert "未許可のリテラル placeholder" in replay_res.stdout
        assert "expected=1, actual=0" in replay_res.stdout
    finally:
        shutil.rmtree(root, ignore_errors=True)

    # H2 + 本文の全体を新規 archive member へ移す対は緑。
    root = _build_min_repo()
    try:
        entry = place_registered_entry_in_current(root)
        worklog = _read(root, "docs/worklog.md")
        assert entry in worklog
        _write(root, "docs/worklog.md", worklog.replace(entry, "", 1))
        new_name = "worklog-rotation-new.md"
        _write(root, f"docs/archive/{new_name}", "# rotation\n\n" + entry)
        _write(root, "docs/archive/README.md", _archive_readme(new_name))
        rotated_res = _run_check(root)
        assert rotated_res.returncode == 0, rotated_res.stdout
    finally:
        shutil.rmtree(root, ignore_errors=True)


def test_placeholder_guard_allowlist_is_path_bound():
    root = _build_min_repo()
    try:
        source = "output/insights/2026-07-24_e2e-real-seal.md"
        moved = "output/insights/moved.md"
        _write(root, source, _read(root, source).replace(
            _PLACEHOLDER_DEBT_INSIGHT + "\n", "", 1
        ))
        _write(root, moved, _PLACEHOLDER_DEBT_INSIGHT + "\n")
        findings = _assert_placeholder_violation(
            root,
            source,
            moved,
            "未許可のリテラル placeholder",
            "expected=1, actual=0",
        )
        assert len(findings) == 2, findings
    finally:
        shutil.rmtree(root, ignore_errors=True)


def test_placeholder_guard_backticked_literal_is_still_detected():
    root = _build_min_repo()
    try:
        rel = "output/insights/markdown-context.md"
        _write(
            root,
            rel,
            "inline `<反映>` control\n"
            "```text\n"
            "<受入結果を反映>\n"
            "```\n",
        )
        findings = _assert_placeholder_violation(
            root, rel, "未許可のリテラル placeholder"
        )
        assert len(findings) == 2, findings
    finally:
        shutil.rmtree(root, ignore_errors=True)


def test_placeholder_guard_verbatim_named_file_is_not_exempt():
    root = _build_min_repo()
    try:
        rel = "output/insights/new-verbatim.md"
        _write(root, rel, "verbatim suffix control: <反映>\n")
        findings = _assert_placeholder_violation(
            root, rel, "未許可のリテラル placeholder"
        )
        assert len(findings) == 1, findings
    finally:
        shutil.rmtree(root, ignore_errors=True)


def test_placeholder_guard_ledger_size_is_pinned():
    root = _build_min_repo()
    try:
        module = _load_fixture_checker(root)
        debts = sum(
            count
            for entries in module.KNOWN_PLACEHOLDER_DEBTS.values()
            for count in entries.values()
        )
        mentions = sum(
            count
            for entries in module.KNOWN_PLACEHOLDER_MENTIONS.values()
            for count in entries.values()
        )
        assert debts == 4
        assert mentions == 5
    finally:
        shutil.rmtree(root, ignore_errors=True)


def test_placeholder_guard_ledger_entries_are_pinned_exactly():
    expected = {
        (
            "KNOWN_PLACEHOLDER_DEBTS",
            "worklog-entry:4926160d0e41c9e972953e535dcce8cc1744eff78b13277cc91d722dc06129f2",
            "37c4a1747e10844c9c4deb2281e644bd655cc80409b80c09c0a840297d6e8ef0",
        ): 1,
        (
            "KNOWN_PLACEHOLDER_DEBTS",
            "worklog-entry:0885598e3ddffd2a6a5c0424c3e6a65ba24f67048374cf3eefc064247e746eb7",
            "3beb84d709104086993083d461c6b511b63ffd595f2037c28f5c5ae91e046327",
        ): 1,
        (
            "KNOWN_PLACEHOLDER_DEBTS",
            "worklog-entry:be893df535111cf91c64c141d38afa482dbca6f0a8a829a55b36ac72d8dc79bc",
            "37c4a1747e10844c9c4deb2281e644bd655cc80409b80c09c0a840297d6e8ef0",
        ): 1,
        (
            "KNOWN_PLACEHOLDER_DEBTS",
            "insights-path:output/insights/2026-07-24_e2e-real-seal.md",
            "c022f2e9ee8cfaf2237eafa5c30e0c772a368c953e5ccf03a29233028bbe52fd",
        ): 1,
        (
            "KNOWN_PLACEHOLDER_MENTIONS",
            "worklog-entry:1241aea6de50f3519f1cb497ff8b0fc07d4b4c2b76f35047d091bfb893aa685a",
            "abdbb38938a76268b5cf63c13309339f58f0cc996deaa13db39c3786e2f3b866",
        ): 1,
        (
            "KNOWN_PLACEHOLDER_MENTIONS",
            "worklog-entry:825788c80a8f458dd12f5682450f134950c37fb0ea6ebbdaddfb26d9f9e95511",
            "80101b39632c395324f424bc9929db7a5c5b76c66b21d61e30afd52434f097ce",
        ): 1,
        (
            "KNOWN_PLACEHOLDER_MENTIONS",
            "worklog-entry:825788c80a8f458dd12f5682450f134950c37fb0ea6ebbdaddfb26d9f9e95511",
            "9162d9fc17d08b52b54c4f4b1adb96a3b614ed4d944ac955de27bb0ea5b539e5",
        ): 1,
        (
            "KNOWN_PLACEHOLDER_MENTIONS",
            "insights-path:output/insights/2026-07-25_t068-t077-t078-closure-verbatim.md",
            "90d8e1f6a7f7229085d78f91ddc7bc91155bbe1ec39b44aaae2b2809daaaf5d9",
        ): 1,
        (
            "KNOWN_PLACEHOLDER_MENTIONS",
            "insights-path:output/insights/2026-07-25_t068-t077-t078-closure-verbatim.md",
            "c66c4f6e14de10c369167108971c74fd0d1462b6a4489792efae907c5d02875c",
        ): 1,
    }
    actual = {}
    for ledger_name, ledger in (
        ("KNOWN_PLACEHOLDER_DEBTS", check_docs.KNOWN_PLACEHOLDER_DEBTS),
        ("KNOWN_PLACEHOLDER_MENTIONS", check_docs.KNOWN_PLACEHOLDER_MENTIONS),
    ):
        for scope, entries in ledger.items():
            for digest, count in entries.items():
                actual[(ledger_name, scope, digest)] = count
    assert actual == expected


def test_placeholder_guard_digest_line_boundary_contract():
    root = _build_min_repo()
    try:
        module = _load_fixture_checker(root)
        base = "digest プレースホルダ <反映>".encode("utf-8")
        lf_line = module._placeholder_logical_lines(
            (base + b"\n").decode("utf-8")
        )[0]
        crlf_line = module._placeholder_logical_lines(
            (base + b"\r\n").decode("utf-8")
        )[0]
        variants = (
            base + b" ",
            b"\xef\xbb\xbf" + base,
            "digest プレースホルダ <反映>".encode("utf-8"),
            base + b"\x0b" + "追記".encode("utf-8"),
        )
        baseline_digest = module._placeholder_line_digest(lf_line)
        assert module._placeholder_line_digest(crlf_line) == baseline_digest
        for variant in variants:
            logical = module._placeholder_logical_lines(
                variant.decode("utf-8")
            )
            assert len(logical) == 1
            assert module._placeholder_line_digest(logical[0]) != baseline_digest

        archive_rel = f"docs/archive/{_PLACEHOLDER_ARCHIVE_NAME}"
        archive_bytes = _read(root, archive_rel).encode("utf-8")
        _write_bytes(root, archive_rel, archive_bytes.replace(b"\n", b"\r\n"))
        assert _placeholder_findings(root) == []
    finally:
        shutil.rmtree(root, ignore_errors=True)

    mutations = (
        _PLACEHOLDER_MENTION_WORKLOG_F36 + " ",
        "\ufeff" + _PLACEHOLDER_MENTION_WORKLOG_F36,
        _PLACEHOLDER_MENTION_WORKLOG_F36.replace(
            "プレースホルダ", "プレースホルダ", 1
        ),
        _PLACEHOLDER_MENTION_WORKLOG_F36 + "\v追記",
    )
    for changed in mutations:
        root = _build_min_repo()
        try:
            rel = f"docs/archive/{_PLACEHOLDER_ARCHIVE_NAME}"
            text = _read(root, rel)
            assert _PLACEHOLDER_MENTION_WORKLOG_F36 in text
            _write(
                root,
                rel,
                text.replace(_PLACEHOLDER_MENTION_WORKLOG_F36, changed, 1),
            )
            findings = _assert_placeholder_violation(
                root,
                "未許可のリテラル placeholder",
                "expected=1, actual=0",
            )
            assert len(findings) == 2, findings
        finally:
            shutil.rmtree(root, ignore_errors=True)


def test_placeholder_guard_missing_target_family_is_violation():
    cases = (
        ("output/insights", "output/insights: placeholder 検査の対象 directory が不在"),
        (
            "docs/archive/worklog-phase3-0722-0724.md",
            "docs/archive/worklog-*.md: placeholder 検査の対象族に実体がない",
        ),
    )
    for rel, expected in cases:
        root = _build_min_repo()
        try:
            path = os.path.join(root, rel)
            if os.path.isdir(path):
                shutil.rmtree(path)
            else:
                os.remove(path)
            _assert_placeholder_violation(root, expected)
        finally:
            shutil.rmtree(root, ignore_errors=True)

    root = _build_min_repo()
    try:
        shutil.rmtree(os.path.join(root, "docs", "archive"))
        res = _run_check(root)
        assert res.returncode == 1, res.stdout
        assert (
            "docs/archive: placeholder 検査の対象 directory が不在"
            in res.stdout
        ), res.stdout
        assert "docs/archive/README.md: ファイルが不在" in res.stdout, res.stdout
        assert "Traceback" not in res.stderr, res.stderr
    finally:
        shutil.rmtree(root, ignore_errors=True)


def test_placeholder_guard_read_failures_are_aggregated_without_traceback():
    cases = ("worklog-directory", "archive-invalid-utf8")
    for case in cases:
        root = _build_min_repo()
        try:
            if case == "worklog-directory":
                path = os.path.join(root, "docs", "worklog.md")
                os.remove(path)
                os.mkdir(path)
                expected = (
                    "docs/worklog.md: placeholder 検査の列挙対象が regular file でない"
                )
            else:
                rel = f"docs/archive/{_PLACEHOLDER_ARCHIVE_NAME}"
                _write_bytes(root, rel, b"\xff")
                expected = f"{rel}: placeholder 検査の読取失敗"
            res = _run_check(root)
            assert res.returncode == 1, (case, res.stdout, res.stderr)
            assert re.search(
                r"^check_docs: \d+ 件の違反$", res.stdout, re.MULTILINE
            ), res.stdout
            assert expected in res.stdout, res.stdout
            assert res.stdout.count(expected) == 1, res.stdout
            assert "KNOWN_PLACEHOLDER_DEBTS の登録 digest" not in res.stdout
            assert "KNOWN_PLACEHOLDER_MENTIONS の登録 digest" not in res.stdout
            assert "Traceback" not in res.stdout, res.stdout
            assert "Traceback" not in res.stderr, res.stderr
        finally:
            shutil.rmtree(root, ignore_errors=True)


def test_placeholder_guard_unreadable_insight_does_not_mask_worklog_mismatch():
    root = _build_min_repo()
    try:
        rel = f"docs/archive/{_PLACEHOLDER_ARCHIVE_NAME}"
        archive = _read(root, rel)
        registered = f"{_PLACEHOLDER_DEBT_WORKLOG}\n"
        assert archive.count(registered) == 2
        _write(
            root,
            rel,
            archive.replace(registered, registered * 2, 1),
        )
        _write_bytes(root, "output/insights/unrelated.md", b"\xff")
        res = _run_check(root)
        assert res.returncode == 1, res.stdout
        assert "output/insights/unrelated.md: placeholder 検査の読取失敗" in res.stdout
        assert "insights-path scope の台帳照合を停止" in res.stdout
        assert "KNOWN_PLACEHOLDER_DEBTS の登録 digest" in res.stdout
        assert "expected=1, actual=2" in res.stdout
        assert "Traceback" not in res.stdout + res.stderr
    finally:
        shutil.rmtree(root, ignore_errors=True)


def test_safe_reader_dependency_failures_do_not_emit_derived_findings():
    # decisions.md: 正当な D1 参照を「実在しない D」と派生誤判定しない。
    root = _build_min_repo()
    try:
        _write(root, "README.md", "# living\n\nD1 を参照する。\n")
        _write_bytes(root, "docs/decisions.md", b"\xff")
        res = _run_check(root)
        prefix = "docs/decisions.md: D 見出し検査の読取失敗"
        assert res.returncode == 1, res.stdout
        assert res.stdout.count(prefix) == 1, res.stdout
        assert "実在しない D 参照" not in res.stdout, res.stdout
        assert "検査を停止" in res.stdout, res.stdout
        assert "Traceback" not in res.stdout + res.stderr
    finally:
        shutil.rmtree(root, ignore_errors=True)

    # 通常経路では、実在しない D 参照の本来の finding が発火する。
    root = _build_min_repo()
    try:
        _write(root, "README.md", "# living\n\nD999 を参照する。\n")
        res = _run_check(root)
        assert res.returncode == 1, res.stdout
        assert "実在しない D 参照: 'D999'" in res.stdout, res.stdout
    finally:
        shutil.rmtree(root, ignore_errors=True)

    # phase3.md: ledger だけが sink の T-001 を消失扱いしない。
    root = _build_min_repo()
    try:
        worklog = _read(root, "docs/worklog.md")
        _write(
            root,
            "docs/worklog.md",
            worklog.replace("- [T-001] consumed\n", "", 1),
        )
        _write_bytes(root, "docs/phase3.md", b"\xff")
        res = _run_check(root)
        prefix = "docs/phase3.md: living docs 検査の読取失敗"
        assert res.returncode == 1, res.stdout
        assert res.stdout.count(prefix) == 1, res.stdout
        assert "次の一手 ID [T-001]" not in res.stdout, res.stdout
        assert "検査を停止" in res.stdout, res.stdout
        assert "Traceback" not in res.stdout + res.stderr
    finally:
        shutil.rmtree(root, ignore_errors=True)

    # 通常の見送り台帳構造では、sink にない遷移の本来の finding が発火する。
    root = _build_min_repo()
    try:
        _write(
            root,
            "docs/worklog.md",
            _CLEAN_WORKLOG.replace("[T-001] carry", "[T-777] carry", 1),
        )
        res = _run_check(root)
        assert res.returncode == 1, res.stdout
        assert "次の一手 ID [T-777]" in res.stdout, res.stdout
    finally:
        shutil.rmtree(root, ignore_errors=True)

    # 見送り台帳の構造抽出失敗は空集合でなく未知状態として遷移検査を止める。
    root = _build_min_repo()
    try:
        _write(
            root,
            "docs/worklog.md",
            _CLEAN_WORKLOG.replace("[T-001] carry", "[T-777] carry", 1),
        )
        _write(
            root,
            "docs/phase3.md",
            _CLEAN_PHASE3.replace("## 見送り台帳 (synthetic)", "## broken ledger"),
        )
        res = _run_check(root)
        assert res.returncode == 1, res.stdout
        assert "見送り台帳 sink の構造抽出失敗" in res.stdout, res.stdout
        assert "見送り台帳に依存する worklog 遷移検査を停止" in res.stdout
        assert "次の一手 ID [T-777]" not in res.stdout, res.stdout
    finally:
        shutil.rmtree(root, ignore_errors=True)

    # archive 1 件が不明なら、読めた非隣接 archive 同士を比較しない。
    root = _build_min_repo()
    try:
        archive_rel = f"docs/archive/{_PLACEHOLDER_ARCHIVE_NAME}"
        archive = _read(root, archive_rel)
        assert archive.rstrip().endswith("### 次の一手")
        _write(
            root,
            archive_rel,
            archive.rstrip() + "\n1. [T-777] unreadable middle sink\n",
        )
        unreadable_name = "worklog-archive-unreadable.md"
        later_name = "worklog-archive-later.md"
        _write_bytes(root, f"docs/archive/{unreadable_name}", b"\xff")
        _write(
            root,
            f"docs/archive/{later_name}",
            "# later archive\n\n"
            "## 2026-07-27 (1) — later archive\n\n"
            "### 次の一手\n",
        )
        _write(
            root,
            "docs/archive/README.md",
            _archive_readme(unreadable_name, later_name),
        )
        res = _run_check(root)
        prefix = (
            f"docs/archive/{unreadable_name}: "
            "placeholder 検査の読取失敗"
        )
        assert res.returncode == 1, res.stdout
        assert res.stdout.count(prefix) == 1, res.stdout
        assert "次の一手 ID [T-777]" not in res.stdout, res.stdout
        assert "検査を停止" in res.stdout, res.stdout
        assert "Traceback" not in res.stdout + res.stderr
    finally:
        shutil.rmtree(root, ignore_errors=True)

    # 通常の archive 構造では、archive 境界遷移の本来の finding が発火する。
    root = _build_min_repo()
    try:
        archive_rel = f"docs/archive/{_PLACEHOLDER_ARCHIVE_NAME}"
        later_name = "worklog-archive-structure-later.md"
        _write(
            root,
            archive_rel,
            _read(root, archive_rel).rstrip()
            + "\n1. [T-778] archive positive control\n",
        )
        _write(
            root,
            f"docs/archive/{later_name}",
            "# later archive\n\n"
            "## 2026-07-27 (1) — later archive\n\n"
            "### 次の一手\n",
        )
        _write(root, "docs/archive/README.md", _archive_readme(later_name))
        res = _run_check(root)
        assert res.returncode == 1, res.stdout
        assert "次の一手 ID [T-778]" in res.stdout, res.stdout
    finally:
        shutil.rmtree(root, ignore_errors=True)

    # archive entry の構造抽出失敗時は、読めた非隣接 archive を比較しない。
    root = _build_min_repo()
    try:
        archive_rel = f"docs/archive/{_PLACEHOLDER_ARCHIVE_NAME}"
        malformed_name = "worklog-archive-structure-malformed.md"
        later_name = "worklog-archive-structure-later.md"
        _write(
            root,
            archive_rel,
            _read(root, archive_rel).rstrip()
            + "\n1. [T-778] archive positive control\n",
        )
        _write(
            root,
            f"docs/archive/{malformed_name}",
            "# readable but no worklog H2\n",
        )
        _write(
            root,
            f"docs/archive/{later_name}",
            "# later archive\n\n"
            "## 2026-07-27 (1) — later archive\n\n"
            "### 次の一手\n",
        )
        _write(
            root,
            "docs/archive/README.md",
            _archive_readme(malformed_name, later_name),
        )
        res = _run_check(root)
        assert res.returncode == 1, res.stdout
        assert "archive entry の構造抽出失敗" in res.stdout, res.stdout
        assert "archive 族全体に依存する順序・境界遷移検査を停止" in res.stdout
        assert "次の一手 ID [T-778]" not in res.stdout, res.stdout
    finally:
        shutil.rmtree(root, ignore_errors=True)


def test_safe_reader_rejects_worklog_symlink_and_fifo_without_hang():
    root = _build_min_repo()
    external = tempfile.mkdtemp(prefix="izanagi_checkdocs_external_")
    try:
        worklog = os.path.join(root, "docs", "worklog.md")
        external_rel = "external-worklog.md"
        _write(
            external,
            external_rel,
            "# external\n\n"
            "## EXTERNAL-SENTINEL\n\n"
            "external unauthorized: <受入結果を反映>\n",
        )
        os.remove(worklog)
        os.symlink(os.path.join(external, external_rel), worklog)
        res = _run_check(root, timeout=5)
        assert res.returncode == 1, res.stdout
        assert re.search(r"^check_docs: \d+ 件の違反$", res.stdout, re.MULTILINE)
        assert "docs/worklog.md" in res.stdout
        assert "次の一手の保存則を停止" in res.stdout
        assert "EXTERNAL-SENTINEL" not in res.stdout, res.stdout
        assert "未許可のリテラル placeholder" not in res.stdout, res.stdout
        assert "Traceback" not in res.stdout + res.stderr
    finally:
        shutil.rmtree(root, ignore_errors=True)
        shutil.rmtree(external, ignore_errors=True)

    root = _build_min_repo()
    try:
        worklog = os.path.join(root, "docs", "worklog.md")
        os.remove(worklog)
        os.mkfifo(worklog)
        res = _run_check(root, timeout=5)
        assert res.returncode == 1, res.stdout
        assert re.search(r"^check_docs: \d+ 件の違反$", res.stdout, re.MULTILINE)
        assert "docs/worklog.md" in res.stdout
        assert "regular file" in res.stdout
        assert "次の一手の保存則を停止" in res.stdout
        assert "Traceback" not in res.stdout + res.stderr
    finally:
        shutil.rmtree(root, ignore_errors=True)

    # placeholder 列挙を経由しない decisions.md で safe-reader 単独の拒否を固定する。
    root = _build_min_repo()
    external = tempfile.mkdtemp(prefix="izanagi_checkdocs_external_")
    try:
        decisions = os.path.join(root, "docs", "decisions.md")
        _write(
            external,
            "external-decisions.md",
            "## D4242 EXTERNAL-SAFE-READER-SENTINEL\n"
            "## D4242 EXTERNAL-SAFE-READER-SENTINEL\n",
        )
        os.remove(decisions)
        os.symlink(
            os.path.join(external, "external-decisions.md"),
            decisions,
        )
        res = _run_check(root, timeout=5)
        assert res.returncode == 1, res.stdout
        assert "docs/decisions.md: D 見出し検査の読取失敗" in res.stdout
        assert "symlink を含む path は読まない" in res.stdout
        assert "D4242 の見出しが重複" not in res.stdout, res.stdout
        assert "Traceback" not in res.stdout + res.stderr
    finally:
        shutil.rmtree(root, ignore_errors=True)
        shutil.rmtree(external, ignore_errors=True)

    root = _build_min_repo()
    try:
        decisions = os.path.join(root, "docs", "decisions.md")
        os.remove(decisions)
        os.mkfifo(decisions)
        res = _run_check(root, timeout=5)
        assert res.returncode == 1, res.stdout
        assert "docs/decisions.md: D 見出し検査の読取失敗" in res.stdout
        assert "regular file でないため読まない" in res.stdout
        assert "Traceback" not in res.stdout + res.stderr
    finally:
        shutil.rmtree(root, ignore_errors=True)


def test_placeholder_guard_rejects_symlinked_target_directories():
    cases = (
        (
            "docs/archive",
            _PLACEHOLDER_ARCHIVE_NAME,
            "",
            "docs/archive: placeholder 検査の対象 directory が symlink",
        ),
        (
            "output/insights",
            "2026-07-24_e2e-real-seal.md",
            _PLACEHOLDER_DEBT_INSIGHT + "\n",
            "output/insights: placeholder 検査の対象 directory が symlink",
        ),
    )
    for rel, member, content, expected in cases:
        root = _build_min_repo()
        external = tempfile.mkdtemp(prefix="izanagi_checkdocs_external_")
        try:
            if rel == "docs/archive":
                content = _read(
                    root, f"docs/archive/{_PLACEHOLDER_ARCHIVE_NAME}"
                )
                _write(
                    external,
                    "README.md",
                    "# EXTERNAL-ARCHIVE-README-SENTINEL\n\n"
                    "## 現在の収容物\n",
                )
            _write(external, member, content)
            external_marker = (
                "worklog-external-unapproved.md"
                if rel == "docs/archive"
                else "external-unapproved.md"
            )
            _write(
                external,
                external_marker,
                "# external\n\n## EXTERNAL-DIRECTORY-SENTINEL\n\n"
                "external unauthorized: <受入結果を反映>\n",
            )
            path = os.path.join(root, rel)
            shutil.rmtree(path)
            os.symlink(external, path)
            findings = _assert_placeholder_violation(root, expected)
            assert findings
            res = _run_check(root, timeout=5)
            assert res.returncode == 1, res.stdout
            assert expected in res.stdout, res.stdout
            assert external_marker not in res.stdout, res.stdout
            assert "EXTERNAL-DIRECTORY-SENTINEL" not in res.stdout, res.stdout
            assert "EXTERNAL-ARCHIVE-README-SENTINEL" not in res.stdout, res.stdout
            assert "未許可のリテラル placeholder" not in res.stdout, res.stdout
            assert "Traceback" not in res.stdout + res.stderr
        finally:
            shutil.rmtree(root, ignore_errors=True)
            shutil.rmtree(external, ignore_errors=True)


def test_placeholder_guard_rejects_symlinked_and_non_regular_members():
    cases = (
        (
            f"docs/archive/{_PLACEHOLDER_ARCHIVE_NAME}",
            "archive-symlink",
        ),
        (
            "output/insights/2026-07-24_e2e-real-seal.md",
            "insight-symlink",
        ),
        (
            f"docs/archive/{_PLACEHOLDER_ARCHIVE_NAME}",
            "archive-directory",
        ),
        (
            "output/insights/2026-07-24_e2e-real-seal.md",
            "insight-directory",
        ),
        (
            f"docs/archive/{_PLACEHOLDER_ARCHIVE_NAME}",
            "archive-fifo",
        ),
        (
            "output/insights/2026-07-24_e2e-real-seal.md",
            "insight-fifo",
        ),
    )
    for rel, case in cases:
        root = _build_min_repo()
        external = tempfile.mkdtemp(prefix="izanagi_checkdocs_external_")
        try:
            content = _read(root, rel)
            path = os.path.join(root, rel)
            os.remove(path)
            if case.endswith("symlink"):
                target = os.path.join(external, "registered.md")
                _write(
                    external,
                    "registered.md",
                    content + "\nexternal unauthorized: <受入結果を反映>\n",
                )
                os.symlink(target, path)
            elif case.endswith("fifo"):
                os.mkfifo(path)
            else:
                os.mkdir(path)
            findings = _assert_placeholder_violation(
                root,
                rel,
                "placeholder 検査の対象 member が regular file でない",
            )
            assert findings
            res = _run_check(root, timeout=5)
            assert res.returncode == 1, res.stdout
            assert rel in res.stdout, res.stdout
            assert (
                "placeholder 検査の対象 member が regular file でない"
                in res.stdout
            ), res.stdout
            assert "未許可のリテラル placeholder" not in res.stdout, res.stdout
            assert "Traceback" not in res.stdout + res.stderr
        finally:
            shutil.rmtree(root, ignore_errors=True)
            shutil.rmtree(external, ignore_errors=True)


def test_placeholder_guard_non_exact_literals_are_not_detected():
    """exact 3 文字列は確定裁定であり、意味的に同じ別表記・HTML entity・
    予測値の先書きは本 gate の射程外である (裁定パッケージ [T-100])。
    """

    root = _build_min_repo()
    try:
        _write(
            root,
            "output/insights/non-exact.md",
            "<結果を反映>\n"
            "<反映済み>\n"
            "&lt;反映&gt;\n"
            "受入結果を反映\n"
            "検査は 123 passed と予測する\n",
        )
        assert _placeholder_findings(root) == []
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
            expected=len(_OPERATION_CONDITION_KEYS),
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
    elif case == "codex_command_contract_deleted":
        rel = ".claude/commands/dev-wave.md"
        _write(root, rel, _read(root, rel).replace(
            "Codex `role=author`", "Claude `role=author`", 1,
        ))
    elif case == "codex_core_contract_deleted":
        rel = "docs/dev-wave/core.md"
        _write(root, rel, _read(root, rel).replace(
            "親は直接編集しない", "親も直接編集できる", 1,
        ))
    elif case == "codex_worker_contract_deleted":
        rel = "docs/dev-wave/workers.md"
        _write(root, rel, _read(root, rel).replace(
            "親が直接直さない", "親が直接直す", 1,
        ))
    elif case == "codex_skill_deleted":
        os.remove(os.path.join(
            root, ".agents", "skills", "dev-wave", "SKILL.md"
        ))
    elif case == "codex_skill_extra_file":
        _write(root, ".agents/skills/dev-wave/README.md", "# extra\n")
    elif case == "codex_skill_name_changed":
        rel = ".agents/skills/dev-wave/SKILL.md"
        _write(root, rel, _read(root, rel).replace(
            "name: dev-wave", "name: dev-wave-renamed", 1,
        ))
    elif case == "codex_skill_adapter_deleted":
        rel = ".agents/skills/dev-wave/SKILL.md"
        literal = check_docs.CODEX_DEV_WAVE_SKILL_LITERALS[0]
        _write(root, rel, _read(root, rel).replace(
            literal, "common dispatcher omitted", 1,
        ))
    elif case == "codex_skill_openai_changed":
        rel = ".agents/skills/dev-wave/agents/openai.yaml"
        _write(root, rel, _read(root, rel).replace(
            "display_name: \"Dev Wave\"",
            "display_name: \"Changed\"",
            1,
        ))
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
    "codex_command_contract_deleted",
    "codex_core_contract_deleted",
    "codex_worker_contract_deleted",
    "codex_skill_deleted",
    "codex_skill_extra_file",
    "codex_skill_name_changed",
    "codex_skill_adapter_deleted",
    "codex_skill_openai_changed",
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
    "codex_command_contract_deleted": "Codex-first 実装境界",
    "codex_core_contract_deleted": "Codex-first 実装契約がない",
    "codex_worker_contract_deleted": "Codex-first 実装契約がない",
    "codex_skill_deleted": "Codex dev-wave Skill の必須 file が不在",
    "codex_skill_extra_file": "Codex dev-wave Skill の予算未登録実体",
    "codex_skill_name_changed": "name は 'dev-wave' 必須",
    "codex_skill_adapter_deleted": "Codex adapter 契約がない",
    "codex_skill_openai_changed": "生成済み Skill interface 契約と不一致",
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
_COMMAND_GUARD_EXPECTED_COUNTS["condition_all_operations_deleted"] = len(
    _OPERATION_CONDITION_KEYS
)


def test_operation_contract_pins_exact_section_set():
    """operations 契約の外延と配線を literal で固定する (O07 削除後の 19 節)。

    checker とテスト fixture は同じ `_OPERATION_NUMBERS` から導出される (F9 型の
    自己整合面)。fixture の literal range 表記が単純な縮小・拡大を先に赤くし、
    本 pin は誤配線と外延の完全性を固定する — 二つの独立面の役割分担であり、
    どちらも単独の oracle ではない。
    """
    operations = "docs/dev-wave/operations.md"
    expected = {
        "DW-O01", "DW-O02", "DW-O03", "DW-O04", "DW-O05", "DW-O06",
        "DW-O08", "DW-O09", "DW-O10", "DW-O11", "DW-O12", "DW-O13",
        "DW-O14", "DW-O15", "DW-O16", "DW-O17", "DW-O18", "DW-O19",
        "DW-O20",
    }
    assert check_docs.REQUIRED_REFERENCE_SECTIONS[operations] == expected
    assert check_docs._ALL_OPERATIONS == frozenset(
        (operations, section) for section in expected
    )
    for section in sorted(expected):
        key = section.removeprefix("DW-O")
        operations_pairs = {
            pair
            for pair in check_docs.CONDITION_DISPATCH_CONTRACT[key]
            if pair[0] == operations
        }
        assert operations_pairs == {(operations, section)}, (
            f"条件 {key} の operations 配線が {section} 単独でない"
        )
    assert _OPERATION_CONDITION_KEYS == sorted(
        section.removeprefix("DW-O") for section in expected
    )
    for stage in ("段 5", "段 6"):
        assert check_docs._ALL_OPERATIONS <= (
            check_docs.STAGE_DISPATCH_CONTRACT[stage]
        ), f"{stage} が operations 全節を消費していない"


def test_codex_dev_wave_skill_contract_pins_exact_surface():
    """checker と合成 fixture の同時縮小で adapter 義務が消えないよう外延を固定する。"""

    assert check_docs.CODEX_DEV_WAVE_SKILL_FILES == {
        ".agents/skills/dev-wave/SKILL.md",
        ".agents/skills/dev-wave/agents/openai.yaml",
    }
    assert check_docs.CODEX_DEV_WAVE_SKILL_LITERALS == (
        ".claude/commands/dev-wave.md",
        "docs/skill-self-improvement.md",
        "docs/dev-wave/workers.md",
        "docs/dev-wave/operations.md",
        "manager は実装面を直接編集しない",
        "codex exec",
        "collaboration child",
        ".codex/role-adapters/*.json",
        "hooks/README.md",
        "supervised manifest",
        "段 1〜9",
        "local main",
    )
    assert check_docs.CODEX_DEV_WAVE_OPENAI_YAML == (
        'interface:\n'
        '  display_name: "Dev Wave"\n'
        '  short_description: "Izanagi の開発 wave を共通契約に従って実行"\n'
        '  default_prompt: "Use $dev-wave to run one Izanagi development wave '
        'for the specified task."\n'
    )


def test_command_docs_guard_rejects_symlinked_commands_directory():
    root = _build_min_repo()
    external = tempfile.mkdtemp(prefix="izanagi_checkdocs_external_commands_")
    try:
        command_dir = os.path.join(root, ".claude", "commands")
        shutil.copytree(command_dir, external, dirs_exist_ok=True)
        _write(
            external,
            "EXTERNAL-COMMAND-SENTINEL.md",
            "# EXTERNAL-COMMAND-SENTINEL\n",
        )
        shutil.rmtree(command_dir)
        os.symlink(external, command_dir)
        res = _run_check(root)
        assert res.returncode == 1, res.stdout
        assert re.search(
            r"^check_docs: \d+ 件の違反$", res.stdout, re.MULTILINE
        ), res.stdout
        assert ".claude/commands: command directory が symlink" in res.stdout
        assert "EXTERNAL-COMMAND-SENTINEL" not in res.stdout, res.stdout
        assert "Traceback" not in res.stdout + res.stderr
    finally:
        shutil.rmtree(root, ignore_errors=True)
        shutil.rmtree(external, ignore_errors=True)


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


# ===== T-143: RuleOps living doc の独立 literal pin / 行番号参照 positive control =====

def test_ruleops_doc_is_literal_pinned_as_enumerated_living_doc():
    assert "docs/ruleops.md" in _enumerated_rels()


def test_ruleops_line_reference_is_own_violation():
    root = _build_min_repo()
    try:
        baseline = _run_check(root)
        assert baseline.returncode == 0, baseline.stdout
        _write(
            root,
            os.path.join("docs", "ruleops.md"),
            "# synthetic RuleOps\n\n`ruleops.md:12` を参照する。\n",
        )
        result = _run_check(root)
        assert result.returncode == 1, result.stdout
        assert _violation_count(result) == 1, result.stdout
        assert "docs の行番号参照 (腐敗する)" in result.stdout
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
            "## 2026-08-02 (2) — second", "## 補助見出し (entry ではない)"
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

## 2026-08-01 (1) — first

### 次の一手
1. [T-001] carry

## 2026-08-02 (2) — second

- [T-001] consumed

### 次の一手
1. missing ID

## 2026-08-03 (3) — third

### 次の一手
1. [T-003] latest
"""
        _write_backlog_docs(root, worklog_text=worklog)
        _assert_violation(
            root,
            "エントリ '2026-08-02 (2) — second'",
            "項目先頭に有効な [T-NNN] ID がない",
        )
    finally:
        shutil.rmtree(root, ignore_errors=True)


def test_backlog_guard_id_bearing_middle_entry_rejects_duplicate_ids():
    root = _build_min_repo()
    try:
        worklog = """# worklog

## ローテーション

## 2026-08-01 (1) — first

### 次の一手
1. [T-001] carry

## 2026-08-02 (2) — second

- [T-001] consumed

### 次の一手
1. [T-002] first
2. [T-002] duplicate

## 2026-08-03 (3) — third

- [T-002] consumed

### 次の一手
1. [T-003] latest
"""
        _write_backlog_docs(root, worklog_text=worklog)
        _assert_violation(
            root,
            "エントリ '2026-08-02 (2) — second'",
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

## 2026-08-01 (1) — first

### 次の一手
1. [T-001] carry

## 2026-08-02 (2) — second

- [T-001] consumed

### 次の一手
1. [T-002] carry

## 2026-08-03 (3) — third

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

## 2026-08-01 (1) — first

### 次の一手
1. [T-001] dropped in middle

## 2026-08-02 (2) — second

- [T-900] unrelated

### 次の一手
1. [T-002] carried

## 2026-08-03 (3) — third

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

## 2026-08-02 (2) — current first

### 次の一手
1. [T-002] current
"""
        archive_name = "worklog-synthetic-latest.md"
        archive = """# archive

## 2026-08-01 (1) — archive last

### 次の一手
1. [T-001] lost at rotation
"""
        _write_backlog_docs(root, worklog_text=current)
        _write(root, os.path.join("docs", "archive", archive_name), archive)
        _write(
            root,
            os.path.join("docs", "archive", "README.md"),
            _archive_readme(archive_name),
        )
        _assert_violation(root, archive_name, "次の一手 ID [T-001]", "current first")
    finally:
        shutil.rmtree(root, ignore_errors=True)


def test_backlog_guard_checks_archive_internal_transitions():
    root = _build_min_repo()
    try:
        current = """# current

## ローテーション

## 2026-08-03 (3) — current

- [T-002] consumed

### 次の一手
1. [T-003] current
"""
        archive_name = "worklog-synthetic.md"
        archive = """# archive

## 2026-08-01 (1) — archive first

### 次の一手
1. [T-001] lost inside archive

## 2026-08-02 (2) — archive second

### 次の一手
1. [T-002] carried to current
"""
        _write_backlog_docs(root, worklog_text=current)
        _write(root, os.path.join("docs", "archive", archive_name), archive)
        _write(
            root,
            os.path.join("docs", "archive", "README.md"),
            _archive_readme(archive_name),
        )
        _assert_violation(root, archive_name, "次の一手 ID [T-001]", "archive second")
    finally:
        shutil.rmtree(root, ignore_errors=True)


def test_backlog_guard_id_bearing_archive_entry_requires_ids_on_all_items():
    root = _build_min_repo()
    try:
        current = """# current

## ローテーション

## 2026-08-03 (3) — current

### 次の一手
1. [T-003] current
"""
        archive_name = "worklog-synthetic.md"
        archive = """# archive

## 2026-08-01 (1) — archive first

### 次の一手
1. [T-001] carry

## 2026-08-02 (2) — archive second

- [T-001] consumed

### 次の一手
1. missing ID
"""
        _write_backlog_docs(root, worklog_text=current)
        _write(root, os.path.join("docs", "archive", archive_name), archive)
        _write(
            root,
            os.path.join("docs", "archive", "README.md"),
            _archive_readme(archive_name),
        )
        _assert_violation(
            root,
            archive_name,
            "エントリ '2026-08-02 (2) — archive second'",
            "項目先頭に有効な [T-NNN] ID がない",
        )
    finally:
        shutil.rmtree(root, ignore_errors=True)


def test_backlog_guard_checks_boundaries_between_all_archives():
    root = _build_min_repo()
    try:
        current = """# current

## ローテーション

## 2026-08-03 (3) — current

- [T-002] consumed

### 次の一手
1. [T-003] current
"""
        first_name = "worklog-first.md"
        second_name = "worklog-second.md"
        first = """# first archive

## 2026-08-01 (1) — first archive last

### 次の一手
1. [T-001] lost between archives
"""
        second = """# second archive

## 2026-08-02 (2) — second archive first

### 次の一手
1. [T-002] carried to current
"""
        _write_backlog_docs(root, worklog_text=current)
        _write(root, os.path.join("docs", "archive", first_name), first)
        _write(root, os.path.join("docs", "archive", second_name), second)
        _write(
            root,
            os.path.join("docs", "archive", "README.md"),
            _archive_readme(first_name, second_name),
        )
        _assert_violation(root, first_name, "次の一手 ID [T-001]", "second archive first")
    finally:
        shutil.rmtree(root, ignore_errors=True)


def test_backlog_guard_latest_archive_is_selected_by_entry_date():
    root = _build_min_repo()
    try:
        current = """# current

## ローテーション

## 2026-09-02 (2) — current

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

## 2026-09-01 (1) — newer

### 次の一手
1. [T-001] lost from chronologically latest archive
"""
        _write_backlog_docs(root, worklog_text=current)
        _write(root, os.path.join("docs", "archive", older_name), older)
        _write(root, os.path.join("docs", "archive", newer_name), newer)
        _write(
            root,
            os.path.join("docs", "archive", "README.md"),
            _archive_readme(older_name, newer_name),
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

## 2026-09-02 (3) — current

- [T-002] consumed

### 次の一手
1. [T-003] current
"""
        early_name = "worklog-z-early.md"
        late_name = "worklog-a-late.md"
        early = """# early

## 2026-09-01 (1) — early

### 次の一手
1. [T-001] carry across archive boundary
"""
        late = """# late

## 2026-09-01 (2) — late

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
            _archive_readme(late_name, early_name),
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

## 2026-09-02 (2) — current

- [T-001] consumed

### 次の一手
1. [T-002] current
"""
        first_name = "worklog-a.md"
        second_name = "worklog-z.md"
        archive = """# archive

## 2026-09-01 (1) — same ordinal

### 次の一手
1. [T-001] carry
"""
        _write_backlog_docs(root, worklog_text=current)
        _write(root, os.path.join("docs", "archive", first_name), archive)
        _write(root, os.path.join("docs", "archive", second_name), archive)
        _write(
            root,
            os.path.join("docs", "archive", "README.md"),
            _archive_readme(first_name, second_name),
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
            "# archive\n\n## 2026-08-01 (1) — last\n\n本文。\n",
            "`### 次の一手` が 0 件",
        ),
        "multiple next": (
            "# archive\n\n## 2026-08-01 (1) — last\n\n"
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
                _archive_readme(archive_name),
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
