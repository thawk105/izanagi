from __future__ import annotations

import importlib.util
from pathlib import Path
import re
import sys


ROOT = Path(__file__).resolve().parents[2]
LEDGER = ROOT / "docs" / "unreachable-object-ledger.md"
COMMAND = ROOT / ".claude" / "commands" / "cleanup-branches.md"
RESCUE_TOOL = ROOT / "tools" / "check_branch_rescue.py"
FIELD_ROW = re.compile(r"^\| `([^`]+)` \|")


def _load_rescue_tool():
    spec = importlib.util.spec_from_file_location("_branch_rescue_ledger_contract", RESCUE_TOOL)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _visible_markdown_lines(text: str) -> list[str]:
    text = re.sub(r"<!--.*?(?:-->|\Z)", "", text, flags=re.DOTALL)
    lines = text.splitlines()
    if lines and lines[0].strip() == "---":
        try:
            closing = next(
                index for index, line in enumerate(lines[1:], 1)
                if line.strip() == "---"
            )
        except StopIteration:
            return []
        lines = lines[closing + 1:]
    visible: list[str] = []
    in_fence = False
    for line in lines:
        stripped = line.lstrip()
        if stripped.startswith("```"):
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        if line.strip():
            visible.append(line)
    return visible


def _section_bullets(text: str, heading: str) -> list[str]:
    lines = _visible_markdown_lines(text)
    start = next(
        (index for index, line in enumerate(lines) if line.strip() == f"## {heading}"),
        None,
    )
    if start is None:
        return []
    bullets: list[str] = []
    current: list[str] = []
    for line in lines[start + 1:]:
        if line.startswith("## "):
            break
        if line.startswith("- "):
            if current:
                bullets.append(" ".join(part.strip() for part in current))
            current = [line]
        elif current:
            current.append(line)
    if current:
        bullets.append(" ".join(part.strip() for part in current))
    return bullets


def _has_cleanup_execution_edges(text: str) -> bool:
    bullets = _section_bullets(text, "1. 棚卸し (削除の前に全量を見る)")
    denied = ("実行しない", "起動しない", "使わない", "単なる言及")
    rescue = [
        bullet for bullet in bullets
        if "python3 tools/check_branch_rescue.py" in bullet
        and "--ledger-check" in bullet
        and ("全削除・撤去候補" in bullet or "全候補" in bullet)
        and ("1 回" in bullet or "一回" in bullet)
        and not any(word in bullet for word in denied)
    ]
    ledger = [
        bullet for bullet in bullets
        if "python3 tools/audit_dangling_commits.py" in bullet
        and "docs/unreachable-object-ledger.md" in bullet
        and not any(word in bullet for word in denied)
    ]
    return len(rescue) == 1 and len(ledger) == 1


def test_documented_ledger_fields_exactly_match_cli_contract() -> None:
    rescue = _load_rescue_tool()
    text = LEDGER.read_text(encoding="utf-8")
    schema_section = text.split("## 台帳 schema\n", 1)[1].split("\n## ", 1)[0]
    documented = [
        match.group(1)
        for line in schema_section.splitlines()
        if (match := FIELD_ROW.match(line))
    ]
    assert documented == list(rescue.LEDGER_FIELDS)


def test_documented_schema_and_retention_claim_are_fixed() -> None:
    text = LEDGER.read_text(encoding="utf-8")
    assert "`izanagi-unreachable-object-ledger-v1`" in text
    assert "`object_retention_provided: false`" in text
    assert "`object_retention_provided` | boolean。固定値 `false`" in text


def test_documented_coverage_boundary_names_all_three_exclusions() -> None:
    text = LEDGER.read_text(encoding="utf-8")
    assert "手で打つ `git branch -d`" in text
    assert "`DW-O28` の自動撤去 (`tools/dev_wave_cleanup.py`)" in text
    assert "D978 の未施行部分" in text


def test_cleanup_command_visibly_wires_rescue_tool_and_ledger() -> None:
    assert _has_cleanup_execution_edges(COMMAND.read_text(encoding="utf-8"))


def test_m23_frontmatter_only_paths_do_not_count_as_execution_edges() -> None:
    text = """---
description: python3 tools/check_branch_rescue.py --ledger-check docs/unreachable-object-ledger.md
---

## 1. 棚卸し (削除の前に全量を見る)

- 通常の棚卸しだけを行う
"""
    assert _has_cleanup_execution_edges(text) is False


def test_b3_mentions_and_negative_instructions_do_not_count_as_execution_edges() -> None:
    text = """## 1. 棚卸し (削除の前に全量を見る)

- 全候補を一回で `python3 tools/check_branch_rescue.py --ledger-check` に渡すとは書くが実行しない
- `python3 tools/audit_dangling_commits.py` と `docs/unreachable-object-ledger.md` は単なる言及
"""
    assert _has_cleanup_execution_edges(text) is False
