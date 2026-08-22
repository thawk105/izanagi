"""docs 由来 dev-wave launch authority の fail-closed 回帰。"""

from __future__ import annotations

import hashlib
import json
import os
import re
import subprocess
from dataclasses import replace
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
_V1_MODEL_LINE = (
    "`<model>`: 段 3 のみ 2 本で `gpt-5.6-sol`→`gpt-5.6-luna`、"
    "他段 `gpt-5.6-sol`。"
)
_V2_MODEL_LINE = "`<model>`: 全段 `gpt-5.6-sol` (段 3 の 2 本も同じ)。"
_STAGE_LANES = (
    ("plan", None),
    ("consult", "sol"),
    ("consult", "luna"),
    ("author", None),
    ("review", None),
    ("fix", None),
    ("focus", None),
)


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


def _operations_with_authority_line(line: str) -> str:
    text = (_ROOT / _OPERATIONS).read_text(encoding="utf-8")
    return text.replace(_authority_line(text), line, 1)


def _workers_with_stage_reasoning() -> str:
    text = (_ROOT / _WORKERS).read_text(encoding="utf-8")
    replacements = (
        (
            "codex は `reasoning=xhigh`、`sandbox=workspace-write` とする。",
            "codex は `reasoning=medium`、`sandbox=workspace-write` とする。",
        ),
        (
            "実装 wave は異なるレンズの敵対レビューを `reasoning=xhigh` で必ず 2 本並列で行う。",
            "実装 wave は異なるレンズの敵対レビューを `reasoning=high` で必ず 2 本並列で行う。",
        ),
        (
            "並列 fix の統合後、焦点再レビューは全体へ `reasoning=xhigh` で 1 本でよい。",
            "並列 fix の統合後、焦点再レビューは全体へ `reasoning=low` で 1 本でよい。",
        ),
    )
    for old, new in replacements:
        assert text.count(old) == 1
        text = text.replace(old, new, 1)
    return text


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


def _prepare_repo(
    tmp_path: Path,
    *,
    operations: str | None = None,
    workers: str | None = None,
) -> Path:
    root = tmp_path / "repo"
    (root / "docs/dev-wave").mkdir(parents=True)
    (root / _OPERATIONS).write_text(
        operations
        if operations is not None
        else (_ROOT / _OPERATIONS).read_text(encoding="utf-8"),
        encoding="utf-8",
    )
    (root / _WORKERS).write_text(
        workers
        if workers is not None
        else (_ROOT / _WORKERS).read_text(encoding="utf-8"),
        encoding="utf-8",
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
        for stage, lane in _STAGE_LANES
    }
    assert tuple(dict.fromkeys(item[0] for item in requirements)) == STAGES
    assert snapshot.model_authority_version == "v2"
    assert {requirement.model for requirement in requirements.values()} == {
        "gpt-5.6-sol"
    }
    assert requirements[("review", None)].effort_authority == "docs"
    assert requirements[("focus", None)].effort_authority == "docs"
    assert requirements[("author", None)].effort == "xhigh"
    assert requirements[("author", None)].effort_authority == "docs"
    assert requirements[("fix", None)].effort == "xhigh"
    assert requirements[("fix", None)].effort_authority == "docs"
    assert len(snapshot.sections) == 4


def test_v2_all_stage_and_lane_models_resolve_to_single_model(
    tmp_path: Path,
) -> None:
    root = _prepare_repo(
        tmp_path, operations=_operations_with_authority_line(_V2_MODEL_LINE)
    )
    snapshot = snapshot_authority(root)
    requirements = [
        derive_launch(snapshot, stage=stage, lane=lane)
        for stage, lane in _STAGE_LANES
    ]
    assert snapshot.model_authority_version == "v2"
    assert snapshot.consult_models == ("gpt-5.6-sol", "gpt-5.6-sol")
    assert snapshot.other_model == "gpt-5.6-sol"
    assert [requirement.model for requirement in requirements] == [
        "gpt-5.6-sol"
    ] * 7


def test_authority_snapshot_serialized_contract_and_digest_are_unchanged(
    tmp_path: Path,
) -> None:
    root = _prepare_repo(
        tmp_path, operations=_operations_with_authority_line(_V2_MODEL_LINE)
    )
    snapshot = snapshot_authority(root)
    payload = {
        "authority_commit": snapshot.authority_commit,
        "sections": [section.as_dict() for section in snapshot.sections],
    }
    canonical = json.dumps(
        payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")
    expected_digest = hashlib.sha256(canonical).hexdigest()
    assert snapshot.digest == expected_digest
    assert snapshot.as_dict() == {**payload, "digest": expected_digest}


def test_v2_snapshot_mapping_inconsistency_fails_closed(tmp_path: Path) -> None:
    root = _prepare_repo(
        tmp_path, operations=_operations_with_authority_line(_V2_MODEL_LINE)
    )
    snapshot = snapshot_authority(root)
    inconsistent_model = f"{snapshot.consult_models[0]}-inconsistent-fixture"
    inconsistent = replace(
        snapshot,
        consult_models=(inconsistent_model, snapshot.consult_models[1]),
    )
    with pytest.raises(AuthorityError, match="v2 の全段 model が一致しない"):
        derive_launch(inconsistent, stage="consult", lane="sol")


def test_review_effort_matches_independent_docs_cross_check() -> None:
    expected = _independent_reasoning(_ROOT / _WORKERS, "DW-S06-A")
    requirement = derive_launch(
        snapshot_authority(_ROOT), stage="review", lane=None
    )
    assert requirement.effort == expected


def test_author_effort_matches_independent_docs_cross_check() -> None:
    expected = _independent_reasoning(_ROOT / _WORKERS, "DW-S05-A")
    requirement = derive_launch(
        snapshot_authority(_ROOT), stage="author", lane=None
    )
    assert requirement.effort == expected


def test_fix_effort_matches_author_derivation() -> None:
    snapshot = snapshot_authority(_ROOT)
    author = derive_launch(snapshot, stage="author", lane=None)
    fix = derive_launch(snapshot, stage="fix", lane=None)
    assert fix.effort == author.effort
    assert fix.effort_authority == author.effort_authority


def test_fix_effort_matches_author_docs_cross_check() -> None:
    expected = _independent_reasoning(_ROOT / _WORKERS, "DW-S05-A")
    requirement = derive_launch(
        snapshot_authority(_ROOT), stage="fix", lane=None
    )
    assert requirement.effort == expected


def test_focus_effort_matches_independent_docs_cross_check() -> None:
    expected = _independent_reasoning(_ROOT / _WORKERS, "DW-S06-C")
    requirement = derive_launch(
        snapshot_authority(_ROOT), stage="focus", lane=None
    )
    assert requirement.effort == expected


def test_derive_launch_uses_stage_specific_effort_sections(tmp_path: Path) -> None:
    root = _prepare_repo(tmp_path, workers=_workers_with_stage_reasoning())
    snapshot = snapshot_authority(root)

    assert derive_launch(snapshot, stage="author", lane=None).effort == "medium"
    assert derive_launch(snapshot, stage="fix", lane=None).effort == "medium"
    assert derive_launch(snapshot, stage="review", lane=None).effort == "high"
    assert derive_launch(snapshot, stage="focus", lane=None).effort == "low"


def test_all_stage_models_match_independent_docs_cross_check() -> None:
    section = _independent_docs_section(_ROOT / _OPERATIONS, "DW-O01")
    expected_models = re.findall(r"`(gpt-[A-Za-z0-9._-]+)`", section)
    assert expected_models == ["gpt-5.6-sol"]

    snapshot = snapshot_authority(_ROOT)
    for stage, lane in _STAGE_LANES:
        requirement = derive_launch(snapshot, stage=stage, lane=lane)
        assert requirement.model == expected_models[0]


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


def test_live_v1_is_rejected_but_historical_v1_is_reconstructed(
    tmp_path: Path,
) -> None:
    root = _prepare_repo(
        tmp_path, operations=_operations_with_authority_line(_V1_MODEL_LINE)
    )
    historical_commit = _git(root, "rev-parse", "HEAD")
    with pytest.raises(AuthorityError, match="live authority は v2"):
        snapshot_authority(root)
    historical = snapshot_authority(root, commit=historical_commit)
    assert historical.model_authority_version == "v1"
    assert historical.consult_models == ("gpt-5.6-sol", "gpt-5.6-luna")
    assert historical.other_model == "gpt-5.6-sol"
    assert (
        derive_launch(historical, stage="consult", lane="sol").model
        != derive_launch(historical, stage="consult", lane="luna").model
    )
    for stage in ("plan", "author", "review", "fix", "focus"):
        assert derive_launch(historical, stage=stage, lane=None).model == (
            "gpt-5.6-sol"
        )

    path = root / _OPERATIONS
    text = path.read_text(encoding="utf-8")
    path.write_text(
        text.replace(_V1_MODEL_LINE, _V2_MODEL_LINE, 1), encoding="utf-8"
    )
    _git(root, "add", _OPERATIONS)
    _git(root, "commit", "-qm", "adopt v2 authority")
    current = snapshot_authority(root)
    reconstructed = snapshot_authority(root, commit=historical_commit)
    assert reconstructed == historical
    assert reconstructed.digest != current.digest
    assert current.model_authority_version == "v2"
    assert (
        derive_launch(current, stage="author", lane=None).model
        == "gpt-5.6-sol"
    )


def test_historical_v1_rejects_same_lens_model_and_reconstructs_valid_v1(
    tmp_path: Path,
) -> None:
    malformed_root = _prepare_repo(
        tmp_path / "malformed",
        operations=_operations_with_authority_line(
            _V1_MODEL_LINE.replace("gpt-5.6-luna", "gpt-5.6-sol")
        ),
    )
    malformed_commit = _git(malformed_root, "rev-parse", "HEAD")
    with pytest.raises(AuthorityError, match="v1 の consult 2 レンズ model が同一"):
        snapshot_authority(malformed_root, commit=malformed_commit)

    valid_root = _prepare_repo(
        tmp_path / "valid", operations=_operations_with_authority_line(_V1_MODEL_LINE)
    )
    valid_commit = _git(valid_root, "rev-parse", "HEAD")
    historical = snapshot_authority(valid_root, commit=valid_commit)
    assert historical.model_authority_version == "v1"
    assert historical.consult_models == ("gpt-5.6-sol", "gpt-5.6-luna")
    assert (
        derive_launch(historical, stage="consult", lane="sol").model
        != derive_launch(historical, stage="consult", lane="luna").model
    )


@pytest.mark.parametrize("invalid_model", ("gpt-", "gpt-5.6/luna", "luna"))
def test_v2_model_slug_drift_fails_closed(
    tmp_path: Path, invalid_model: str
) -> None:
    invalid_line = _V2_MODEL_LINE.replace("gpt-5.6-sol", invalid_model, 1)
    root = _prepare_repo(
        tmp_path, operations=_operations_with_authority_line(invalid_line)
    )
    with pytest.raises(AuthorityError):
        snapshot_authority(root)


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
