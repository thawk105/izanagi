from __future__ import annotations

import importlib.util
from pathlib import Path
import re
import sys

import pytest


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


def _ledger_entry(status: str = "pending") -> dict[str, object]:
    resolved = status != "pending"
    return {
        "schema": "izanagi-unreachable-object-ledger-v1",
        "entry_id": "e-1",
        "recorded_at": "2030-01-01T00:00:00Z",
        "source_refs": ["refs/heads/topic"],
        "source_tips": {"refs/heads/topic": "a" * 40},
        "assessment_report_sha256": "b" * 64,
        "object_oid": "a" * 40,
        "object_type": "commit",
        "assessment_schema": "izanagi-branch-landed-v1",
        "assessment_verdict": "not-landed",
        "assessment_reason": "fixture",
        "storage_kind": "loose",
        "object_mtime": "2030-01-01T00:00:00Z",
        "loss_possible_not_before": "2030-02-01T00:00:00Z",
        "lower_bound_basis": "loose-object-mtime-plus-prune-expire",
        "gc_auto_threshold": 6700,
        "gc_auto_sample_fanout": "17",
        "gc_auto_sample_count": 12,
        "gc_auto_sample_threshold": 27,
        "gc_auto_heuristic_version": "git-2.34.1-fanout-17-sample",
        "loose_count_at_loss": 12,
        "status": status,
        "resolved_at": "2030-01-10T00:00:00Z" if resolved else None,
        "rescue_ref": "refs/heads/rescue/e-1" if status == "rescued" else None,
        "resolution_note": f"resolved as {status}" if resolved else None,
        "object_retention_provided": False,
    }


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
    fence: tuple[str, int] | None = None
    for line in lines:
        marker = re.match(r"^[ ]{0,3}(`{3,}|~{3,})", line)
        if fence is None and marker is not None:
            token = marker.group(1)
            fence = (token[0], len(token))
            continue
        if fence is not None:
            closing = re.fullmatch(r"[ ]{0,3}([`~]+)[ \t]*", line)
            if (closing is not None and closing.group(1)[0] == fence[0]
                    and len(closing.group(1)) >= fence[1]):
                fence = None
            continue
        if line.strip():
            visible.append(line)
    return visible


def _visible_section_lines(text: str, heading: str) -> list[str]:
    lines = _visible_markdown_lines(text)
    start = next(
        (index for index, line in enumerate(lines) if line.strip() == f"## {heading}"),
        None,
    )
    if start is None:
        return []
    section: list[str] = []
    for line in lines[start + 1:]:
        if line.startswith("## "):
            break
        section.append(line)
    return section


def _documents_resolution_field_contract(text: str) -> bool:
    prose = " ".join(_visible_section_lines(text, "追記と状態遷移"))
    required = (
        r"`pending` は 3 解決 field をすべて null とする",
        r"`rescued` は full refname の `rescue_ref`、\s*`resolved_at`、"
        r"\s*非空の `resolution_note` を必須とする",
        r"それ以外の解決 status は `resolved_at` と\s*"
        r"非空の `resolution_note` を必須とし、\s*`rescue_ref` は null とする",
    )
    return all(re.search(pattern, prose) is not None for pattern in required)


def _documents_stale_resolution_contract(text: str) -> bool:
    prose = " ".join(_visible_section_lines(text, "rescue gate の運用契約"))
    notified = re.search(
        r"`rescued`、`reachable-again`、`object-missing` の\s*"
        r"entry が dangling audit で再報告された場合も "
        r"stale resolution として通知する",
        prose,
    )
    accepted_loss_excluded = re.search(
        r"`accepted-loss` は再報告だけで stale としない",
        prose,
    )
    return notified is not None and accepted_loss_excluded is not None


def _documents_rc3_stale_resolution_notification(text: str) -> bool:
    return any(
        re.fullmatch(
            r"\|\s*`3`\s*\|.*stale resolution の通知あり.*\|",
            line,
        )
        for line in _visible_section_lines(text, "rescue gate の運用契約")
    )


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


def test_documented_resolution_and_stale_notification_contracts_are_visible() -> None:
    text = LEDGER.read_text(encoding="utf-8")

    assert _documents_resolution_field_contract(text)
    assert _documents_stale_resolution_contract(text)
    assert _documents_rc3_stale_resolution_notification(text)


@pytest.mark.parametrize(
    ("opening", "closing"),
    [
        ("<!--", "-->"),
        ("```text", "```"),
        ("~~~text", "~~~"),
    ],
)
def test_hidden_ledger_contract_prose_does_not_satisfy_consumer(
    opening: str, closing: str,
) -> None:
    resolution_contract = "\n".join(
        (
            "`pending` は 3 解決 field をすべて null とする。",
            "`rescued` は full refname の `rescue_ref`、`resolved_at`、"
            "非空の `resolution_note` を必須とする。",
            "それ以外の解決 status は `resolved_at` と非空の "
            "`resolution_note` を必須とし、`rescue_ref` は null とする。",
        )
    )
    stale_contract = "\n".join(
        (
            "`rescued`、`reachable-again`、`object-missing` の entry が "
            "dangling audit で再報告された場合も stale resolution として通知する。",
            "`accepted-loss` は再報告だけで stale としない。",
            "| `3` | 可視化は完全だが、stale resolution の通知あり |",
        )
    )
    text = f"""## 追記と状態遷移

{opening}
{resolution_contract}
{closing}

## rescue gate の運用契約

{opening}
{stale_contract}
{closing}
"""

    assert _documents_resolution_field_contract(text) is False
    assert _documents_stale_resolution_contract(text) is False
    assert _documents_rc3_stale_resolution_notification(text) is False


@pytest.mark.parametrize(
    "status",
    ["pending", "rescued", "accepted-loss", "reachable-again", "object-missing"],
)
def test_ledger_status_accepts_only_its_coherent_resolution_shape(status: str) -> None:
    rescue = _load_rescue_tool()

    assert rescue._validate_ledger_entry(_ledger_entry(status)) == (True, "ok")


def test_pending_ledger_entry_requires_all_resolution_fields_to_be_null() -> None:
    rescue = _load_rescue_tool()
    mutations = {
        "resolved_at": "2030-01-10T00:00:00Z",
        "rescue_ref": "refs/heads/rescue/e-1",
        "resolution_note": "premature resolution",
    }

    for field, value in mutations.items():
        entry = _ledger_entry()
        entry[field] = value
        assert rescue._validate_ledger_entry(entry) == (
            False,
            "ledger-entry-resolution-fields-invalid",
        )


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("resolved_at", None),
        ("rescue_ref", None),
        ("rescue_ref", "heads/rescue/e-1"),
        ("rescue_ref", "refs/heads/rescue bad"),
        ("resolution_note", None),
        ("resolution_note", "   "),
    ],
)
def test_rescued_ledger_entry_requires_timestamp_full_ref_and_note(
    field: str, value: object,
) -> None:
    rescue = _load_rescue_tool()
    entry = _ledger_entry("rescued")
    entry[field] = value

    assert rescue._validate_ledger_entry(entry) == (
        False,
        "ledger-entry-resolution-fields-invalid",
    )


@pytest.mark.parametrize(
    "status",
    ["accepted-loss", "reachable-again", "object-missing"],
)
@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("resolved_at", None),
        ("rescue_ref", "refs/heads/rescue/e-1"),
        ("resolution_note", None),
        ("resolution_note", ""),
    ],
)
def test_non_rescue_resolutions_require_timestamp_note_and_null_rescue_ref(
    status: str, field: str, value: object,
) -> None:
    rescue = _load_rescue_tool()
    entry = _ledger_entry(status)
    entry[field] = value

    assert rescue._validate_ledger_entry(entry) == (
        False,
        "ledger-entry-resolution-fields-invalid",
    )


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


def test_b3_tilde_fence_bullets_do_not_count_as_execution_edges() -> None:
    text = """## 1. 棚卸し (削除の前に全量を見る)

~~~text
- 全削除・撤去候補を 1 回で `python3 tools/check_branch_rescue.py --ledger-check` に渡して実行する
- `python3 tools/audit_dangling_commits.py` を実行し `docs/unreachable-object-ledger.md` と照合する
~~~
"""
    assert _has_cleanup_execution_edges(text) is False
