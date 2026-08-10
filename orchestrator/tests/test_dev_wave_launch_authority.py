"""docs 由来 dev-wave launch authority の fail-closed 回帰。"""

from __future__ import annotations

import os
import re
import subprocess
from pathlib import Path

import pytest

from tools.dev_waves.launch_authority import (
    STAGES,
    AuthorityError,
    derive_launch,
    snapshot_authority,
    visible_top_level_lines,
)


_ROOT = Path(__file__).resolve().parents[2]
_OPERATIONS = "docs/dev-wave/operations.md"
_WORKERS = "docs/dev-wave/workers.md"


def _git(root: Path, *args: str) -> str:
    completed = subprocess.run(
        ["git", "-C", os.fspath(root), *args],
        check=True,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    return completed.stdout.strip()


def _authority_line(text: str) -> str:
    matches = [line for line in text.splitlines() if "`<model>`:" in line]
    assert len(matches) == 1
    return matches[0]


def _independent_docs_section(path: Path, section_id: str) -> str:
    text = path.read_text(encoding="utf-8")
    matches = re.findall(
        rf"^## {re.escape(section_id)}(?:[ \t]+—[^\r\n]*)?[ \t]*\r?\n"
        r"(.*?)(?=^## |\Z)",
        text,
        flags=re.MULTILINE | re.DOTALL,
    )
    assert len(matches) == 1
    return matches[0]


def _independent_reasoning(path: Path, section_id: str) -> str:
    section = _independent_docs_section(path, section_id)
    matches = re.findall(r"`reasoning=([A-Za-z0-9_-]+)`", section)
    assert len(matches) == 1
    return matches[0]


def _prepare_repo(tmp_path: Path, *, operations: str | None = None) -> Path:
    root = tmp_path / "repo"
    (root / "docs/dev-wave").mkdir(parents=True)
    (root / _OPERATIONS).write_text(
        operations
        if operations is not None
        else (_ROOT / _OPERATIONS).read_text(encoding="utf-8"),
        encoding="utf-8",
    )
    (root / _WORKERS).write_text(
        (_ROOT / _WORKERS).read_text(encoding="utf-8"), encoding="utf-8"
    )
    _git(root, "init", "-q")
    _git(root, "config", "user.name", "authority-test")
    _git(root, "config", "user.email", "authority-test@example.invalid")
    _git(root, "add", _OPERATIONS, _WORKERS)
    _git(root, "commit", "-qm", "authority fixture")
    return root


def test_snapshot_and_derive_current_authority_positive(tmp_path: Path) -> None:
    root = _prepare_repo(tmp_path)
    snapshot = snapshot_authority(root)
    requirements = {
        (stage, lane): derive_launch(snapshot, stage=stage, lane=lane)
        for stage, lane in (
            ("plan", None),
            ("consult", "sol"),
            ("consult", "luna"),
            ("author", None),
            ("review", None),
            ("fix", None),
            ("focus", None),
        )
    }
    assert tuple(dict.fromkeys(item[0] for item in requirements)) == STAGES
    assert (
        requirements[("consult", "sol")].model
        != requirements[("consult", "luna")].model
    )
    assert (
        requirements[("author", None)].model
        == requirements[("consult", "sol")].model
    )
    assert requirements[("review", None)].effort_authority == "docs"
    assert requirements[("focus", None)].effort_authority == "docs"
    assert requirements[("author", None)].effort is None
    assert requirements[("author", None)].effort_authority == "unbound"
    assert len(snapshot.sections) == 3


def test_review_effort_matches_independent_docs_cross_check() -> None:
    expected = _independent_reasoning(_ROOT / _WORKERS, "DW-S06-A")
    requirement = derive_launch(
        snapshot_authority(_ROOT), stage="review", lane=None
    )
    assert requirement.effort == expected


def test_focus_effort_matches_independent_docs_cross_check() -> None:
    expected = _independent_reasoning(_ROOT / _WORKERS, "DW-S06-C")
    requirement = derive_launch(
        snapshot_authority(_ROOT), stage="focus", lane=None
    )
    assert requirement.effort == expected


def test_all_stage_models_match_independent_docs_cross_check() -> None:
    section = _independent_docs_section(_ROOT / _OPERATIONS, "DW-O01")
    expected_models = re.findall(r"`(gpt-[A-Za-z0-9._-]+)`", section)
    assert len(expected_models) == 3

    snapshot = snapshot_authority(_ROOT)
    for stage in STAGES:
        if stage == "consult":
            for lane, expected in zip(
                ("sol", "luna"), expected_models[:2], strict=True
            ):
                requirement = derive_launch(snapshot, stage=stage, lane=lane)
                assert requirement.model == expected
        else:
            requirement = derive_launch(snapshot, stage=stage, lane=None)
            assert requirement.model == expected_models[2]


def _mutate_normative_line(text: str, case: str) -> str:
    line = _authority_line(text)
    if case == "blockquote":
        replacement = f"> {line}"
    elif case == "list":
        replacement = f"- {line}"
    elif case == "raw_html":
        replacement = f"<div>\n{line}\n</div>\n"
    elif case == "negation":
        replacement = f"この例では次を規範として採用しない: {line}"
    elif case == "link_example":
        replacement = f"[{line}](https://example.invalid/example)"
    elif case == "zero":
        replacement = "model authority は dispatcher 例に置かない。"
    elif case == "duplicate":
        replacement = f"{line}\n{line}"
    elif case == "u2028":
        replacement = line.replace("段 3", "段\u20283", 1)
    elif case == "u2029":
        replacement = line.replace("段 3", "段\u20293", 1)
    else:  # pragma: no cover - registration meta-test が閉じる
        raise AssertionError(case)
    changed = text.replace(line, replacement, 1)
    assert changed != text
    return changed


_NORMATIVE_DECOY_CASES = (
    "blockquote",
    "list",
    "raw_html",
    "negation",
    "link_example",
    "zero",
    "duplicate",
    "u2028",
    "u2029",
)


@pytest.mark.parametrize("case", _NORMATIVE_DECOY_CASES)
def test_model_normative_line_decoys_fail_closed(
    tmp_path: Path, case: str
) -> None:
    original = (_ROOT / _OPERATIONS).read_text(encoding="utf-8")
    root = _prepare_repo(
        tmp_path, operations=_mutate_normative_line(original, case)
    )
    with pytest.raises(AuthorityError):
        snapshot_authority(root)


def test_authority_decoy_case_registration_is_complete() -> None:
    assert set(_NORMATIVE_DECOY_CASES) == {
        "blockquote",
        "list",
        "raw_html",
        "negation",
        "link_example",
        "zero",
        "duplicate",
        "u2028",
        "u2029",
    }


_SEPARATOR_NON_CANDIDATE_CASES = (
    "fence",
    "html_comment",
    "raw_html",
    "visible_prose",
    "non_target_section",
)


def _insert_separator_non_candidate(
    text: str, case: str, separator: str
) -> str:
    line = _authority_line(text)
    decoy = f"補足{separator}説明"
    if case == "fence":
        replacement = f"```text\n{decoy}\n```\n{line}"
    elif case == "html_comment":
        replacement = f"<!-- {decoy} -->\n{line}"
    elif case == "raw_html":
        replacement = f"<div>\n{decoy}\n</div>\n\n{line}"
    elif case == "visible_prose":
        replacement = f"非規範の補足: {decoy}\n{line}"
    elif case == "non_target_section":
        return text + f"\n非対象節の補足: {decoy}\n"
    else:  # pragma: no cover - registration meta-test が閉じる
        raise AssertionError(case)
    changed = text.replace(line, replacement, 1)
    assert changed != text
    return changed


@pytest.mark.parametrize("separator", ("\u2028", "\u2029"))
@pytest.mark.parametrize("case", _SEPARATOR_NON_CANDIDATE_CASES)
def test_unicode_separator_outside_normative_candidate_is_accepted(
    tmp_path: Path, case: str, separator: str
) -> None:
    original = (_ROOT / _OPERATIONS).read_text(encoding="utf-8")
    root = _prepare_repo(
        tmp_path,
        operations=_insert_separator_non_candidate(original, case, separator),
    )
    snapshot_authority(root)


def test_separator_non_candidate_registration_is_complete() -> None:
    assert set(_SEPARATOR_NON_CANDIDATE_CASES) == {
        "fence",
        "html_comment",
        "raw_html",
        "visible_prose",
        "non_target_section",
    }


def test_visible_top_level_lines_keeps_legacy_default_separator_rejection() -> None:
    text = "補足\u2028説明\n"
    with pytest.raises(AuthorityError):
        visible_top_level_lines(text)
    assert visible_top_level_lines(
        text, reject_unicode_separators=False
    )


def test_dirty_working_tree_authority_is_rejected(tmp_path: Path) -> None:
    root = _prepare_repo(tmp_path)
    path = root / _OPERATIONS
    path.write_text(path.read_text(encoding="utf-8") + "\n", encoding="utf-8")
    with pytest.raises(AuthorityError):
        snapshot_authority(root)


def test_historical_commit_is_reconstructed_without_live_head(
    tmp_path: Path,
) -> None:
    root = _prepare_repo(tmp_path)
    historical_commit = _git(root, "rev-parse", "HEAD")
    historical = snapshot_authority(root, commit=historical_commit)
    path = root / _OPERATIONS
    text = path.read_text(encoding="utf-8")
    line = _authority_line(text)
    models = re.findall(r"gpt-[A-Za-z0-9._-]+", line)
    assert len(models) == 3 and models[0] == models[2] and models[0] != models[1]
    swapped = (
        line.replace(models[0], "MODEL-TEMP")
        .replace(models[1], models[0])
        .replace("MODEL-TEMP", models[1])
    )
    path.write_text(text.replace(line, swapped, 1), encoding="utf-8")
    _git(root, "add", _OPERATIONS)
    _git(root, "commit", "-qm", "change authority")
    current = snapshot_authority(root)
    reconstructed = snapshot_authority(root, commit=historical_commit)
    assert reconstructed == historical
    assert reconstructed.digest != current.digest
    assert (
        derive_launch(reconstructed, stage="author", lane=None).model
        != derive_launch(current, stage="author", lane=None).model
    )


def test_lane_validation_is_not_inferred_from_model_value(tmp_path: Path) -> None:
    snapshot = snapshot_authority(_prepare_repo(tmp_path))
    with pytest.raises(AuthorityError):
        derive_launch(snapshot, stage="consult", lane=None)
    with pytest.raises(AuthorityError):
        derive_launch(snapshot, stage="author", lane="sol")


def _run() -> int:
    """新規 test file を repository の plain-runner 契約へ載せる。"""
    return pytest.main([__file__, "-q"])


if __name__ == "__main__":
    raise SystemExit(_run())
