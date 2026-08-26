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
    visible: list[str] = []
    in_fence = False
    in_comment = False
    for line in text.splitlines():
        stripped = line.lstrip()
        if stripped.startswith("```"):
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        if "<!--" in line:
            in_comment = True
            line = line.split("<!--", 1)[0]
        if not in_comment and line.strip():
            visible.append(line)
        if "-->" in stripped:
            in_comment = False
    return visible


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
    lines = _visible_markdown_lines(COMMAND.read_text(encoding="utf-8"))
    assert any("tools/check_branch_rescue.py" in line for line in lines)
    assert any("docs/unreachable-object-ledger.md" in line for line in lines)
