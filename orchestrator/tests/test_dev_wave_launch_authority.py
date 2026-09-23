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
    _MERGE_HEAD_MAX_BYTES,
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
            "codex は `reasoning=medium`、`sandbox=workspace-write` とする。",
            "codex は `reasoning=medium`、`sandbox=workspace-write` とする。",
        ),
        (
            "実装 wave は異なるレンズの敵対レビューを `reasoning=medium` で必ず 2 本並列で行う。",
            "実装 wave は異なるレンズの敵対レビューを `reasoning=high` で必ず 2 本並列で行う。",
        ),
        (
            "並列 fix の統合後、焦点再レビューは全体へ `reasoning=medium` で 1 本でよい。",
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


def _git_dir(root: Path) -> Path:
    git_dir = Path(_git(root, "rev-parse", "--absolute-git-dir"))
    assert git_dir.is_absolute()
    return git_dir


def _replace_model(text: str, model: str) -> str:
    changed = text.replace(
        _authority_line(text),
        f"`<model>`: 全段 `{model}` (段 3 の 2 本も同じ)。",
        1,
    )
    assert changed != text
    return changed


def _replace_author_effort(text: str, effort: str) -> str:
    changed, count = re.subn(
        r"codex は `reasoning=[A-Za-z0-9_-]+`、"
        r"`sandbox=workspace-write` とする。",
        f"codex は `reasoning={effort}`、"
        "`sandbox=workspace-write` とする。",
        text,
        count=1,
    )
    assert count == 1
    return changed


def _replace_worker_efforts(
    text: str, *, author: str, review: str, focus: str
) -> str:
    changed = _replace_author_effort(text, author)
    replacements = (
        (
            r"実装 wave は異なるレンズの敵対レビューを "
            r"`reasoning=[A-Za-z0-9_-]+` で必ず 2 本並列で行う。",
            "実装 wave は異なるレンズの敵対レビューを "
            f"`reasoning={review}` で必ず 2 本並列で行う。",
        ),
        (
            r"並列 fix の統合後、焦点再レビューは全体へ "
            r"`reasoning=[A-Za-z0-9_-]+` で 1 本でよい。",
            "並列 fix の統合後、焦点再レビューは全体へ "
            f"`reasoning={focus}` で 1 本でよい。",
        ),
    )
    for pattern, replacement in replacements:
        changed, count = re.subn(pattern, replacement, changed, count=1)
        assert count == 1
    return changed


def _commit_authority_files(root: Path, message: str) -> str:
    _git(root, "add", _OPERATIONS, _WORKERS)
    _git(root, "commit", "-qm", message)
    return _git(root, "rev-parse", "HEAD")


def _merge_no_commit(root: Path, branch: str, *, expected_rc: int) -> None:
    completed = subprocess.run(
        [
            "git",
            "-C",
            os.fspath(root),
            "merge",
            "--no-commit",
            "--no-ff",
            branch,
        ],
        check=False,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    assert completed.returncode == expected_rc, completed.stderr


def _prepare_mid_merge_repo(
    tmp_path: Path, *, conflicted: bool
) -> tuple[Path, str, str]:
    root = _prepare_repo(tmp_path)
    branch = _git(root, "branch", "--show-current")
    base_operations = (root / _OPERATIONS).read_text(encoding="utf-8")
    base_workers = (root / _WORKERS).read_text(encoding="utf-8")

    _git(root, "checkout", "-qb", "incoming")
    if conflicted:
        (root / _OPERATIONS).write_text(
            _replace_model(base_operations, "gpt-5.6-terra"),
            encoding="utf-8",
        )
    else:
        (root / _OPERATIONS).write_text(
            base_operations + "\nincoming authority note\n", encoding="utf-8"
        )
    incoming = _commit_authority_files(root, "incoming authority")

    _git(root, "checkout", "-q", branch)
    if conflicted:
        (root / _OPERATIONS).write_text(
            _replace_model(base_operations, "gpt-5.6-luna"),
            encoding="utf-8",
        )
    else:
        (root / _WORKERS).write_text(
            base_workers + "\nwave authority note\n", encoding="utf-8"
        )
    head = _commit_authority_files(root, "wave authority")
    _merge_no_commit(root, "incoming", expected_rc=1 if conflicted else 0)
    assert (_git_dir(root) / "MERGE_HEAD").read_text(
        encoding="ascii"
    ).splitlines() == [incoming]
    return root, head, incoming


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
        "gpt-6-sol"
    }
    assert requirements[("review", None)].effort_authority == "docs"
    assert requirements[("focus", None)].effort_authority == "docs"
    assert requirements[("author", None)].effort == "medium"
    assert requirements[("author", None)].effort_authority == "docs"
    assert requirements[("fix", None)].effort == "medium"
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
    assert expected_models == ["gpt-6-sol"]

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
    with pytest.raises(
        AuthorityError,
        match=rf"{re.escape(_OPERATIONS)}: working tree が authority commit と異なる",
    ):
        snapshot_authority(root)


def test_mid_merge_conflicted_authority_author_is_accepted(
    tmp_path: Path,
) -> None:
    root, head, _incoming = _prepare_mid_merge_repo(
        tmp_path, conflicted=True
    )
    assert _git(root, "ls-files", "-u")

    accepted = snapshot_authority(root, allow_mid_merge=True)

    assert accepted == snapshot_authority(root, commit=head)
    assert accepted.authority_commit == head
    assert accepted.other_model == "gpt-5.6-luna"


def test_mid_merge_clean_auto_merged_authority_author_is_accepted(
    tmp_path: Path,
) -> None:
    root, head, _incoming = _prepare_mid_merge_repo(
        tmp_path, conflicted=False
    )
    assert not _git(root, "ls-files", "-u")
    assert (root / _OPERATIONS).read_bytes() != bytes(
        subprocess.run(
            ["git", "-C", os.fspath(root), "show", f"{head}:{_OPERATIONS}"],
            check=True,
            stdout=subprocess.PIPE,
        ).stdout
    )

    accepted = snapshot_authority(root, allow_mid_merge=True)

    assert accepted == snapshot_authority(root, commit=head)
    assert accepted.authority_commit == head


def test_mid_merge_accepts_when_operations_matches_and_workers_is_deleted(
    tmp_path: Path,
) -> None:
    root, head, _incoming = _prepare_mid_merge_repo(
        tmp_path, conflicted=False
    )
    committed_operations = subprocess.run(
        ["git", "-C", os.fspath(root), "show", f"{head}:{_OPERATIONS}"],
        check=True,
        stdout=subprocess.PIPE,
    ).stdout
    (root / _OPERATIONS).write_bytes(committed_operations)
    (root / _WORKERS).unlink()

    accepted = snapshot_authority(root, allow_mid_merge=True)

    assert accepted == snapshot_authority(root, commit=head)


def test_mid_merge_accepts_when_workers_matches_and_operations_is_deleted(
    tmp_path: Path,
) -> None:
    root, head, _incoming = _prepare_mid_merge_repo(
        tmp_path, conflicted=False
    )
    committed_workers = subprocess.run(
        ["git", "-C", os.fspath(root), "show", f"{head}:{_WORKERS}"],
        check=True,
        stdout=subprocess.PIPE,
    ).stdout
    (root / _WORKERS).write_bytes(committed_workers)
    (root / _OPERATIONS).unlink()

    accepted = snapshot_authority(root, allow_mid_merge=True)

    assert accepted == snapshot_authority(root, commit=head)


def test_non_author_stage_in_mid_merge_is_rejected(tmp_path: Path) -> None:
    root, _head, _incoming = _prepare_mid_merge_repo(
        tmp_path, conflicted=False
    )

    with pytest.raises(
        AuthorityError,
        match=rf"{re.escape(_OPERATIONS)}: working tree が authority commit と異なる",
    ):
        snapshot_authority(root, allow_mid_merge=False)


def test_same_named_merge_head_branch_is_not_merge_state(
    tmp_path: Path,
) -> None:
    root = _prepare_repo(tmp_path)
    head = _git(root, "rev-parse", "HEAD")
    _git(root, "branch", "MERGE_HEAD", head)
    assert _git(root, "rev-parse", "--verify", "MERGE_HEAD") == head
    assert not (_git_dir(root) / "MERGE_HEAD").exists()
    path = root / _OPERATIONS
    path.write_text(path.read_text(encoding="utf-8") + "\n", encoding="utf-8")

    with pytest.raises(
        AuthorityError,
        match="working tree が authority commit と異なる",
    ):
        snapshot_authority(root, allow_mid_merge=True)


def test_octopus_merge_head_is_rejected(tmp_path: Path) -> None:
    root = _prepare_repo(tmp_path)
    first = _git(root, "rev-parse", "HEAD")
    _git(root, "commit", "--allow-empty", "-qm", "second commit")
    second = _git(root, "rev-parse", "HEAD")
    assert first != second
    (_git_dir(root) / "MERGE_HEAD").write_text(
        f"{first}\n{second}\n", encoding="ascii"
    )
    path = root / _OPERATIONS
    path.write_text(path.read_text(encoding="utf-8") + "\n", encoding="utf-8")

    with pytest.raises(AuthorityError, match="一意な commit OID 1 行"):
        snapshot_authority(root, allow_mid_merge=True)


def test_merge_head_symlink_is_rejected(tmp_path: Path) -> None:
    root = _prepare_repo(tmp_path)
    git_dir = _git_dir(root)
    target = git_dir / "merge-head-target"
    target.write_text(_git(root, "rev-parse", "HEAD") + "\n", encoding="ascii")
    os.symlink(target.name, git_dir / "MERGE_HEAD")
    path = root / _OPERATIONS
    path.write_text(path.read_text(encoding="utf-8") + "\n", encoding="utf-8")

    with pytest.raises(AuthorityError, match="regular file"):
        snapshot_authority(root, allow_mid_merge=True)


def test_merge_head_fifo_is_rejected(tmp_path: Path) -> None:
    root = _prepare_repo(tmp_path)
    os.mkfifo(_git_dir(root) / "MERGE_HEAD")
    path = root / _OPERATIONS
    path.write_text(path.read_text(encoding="utf-8") + "\n", encoding="utf-8")

    with pytest.raises(AuthorityError, match="regular file"):
        snapshot_authority(root, allow_mid_merge=True)


def test_merge_head_directory_is_rejected(tmp_path: Path) -> None:
    root = _prepare_repo(tmp_path)
    (_git_dir(root) / "MERGE_HEAD").mkdir()
    path = root / _OPERATIONS
    path.write_text(path.read_text(encoding="utf-8") + "\n", encoding="utf-8")

    with pytest.raises(AuthorityError, match="regular file"):
        snapshot_authority(root, allow_mid_merge=True)


def test_merge_head_over_size_limit_is_rejected(tmp_path: Path) -> None:
    root = _prepare_repo(tmp_path)
    (_git_dir(root) / "MERGE_HEAD").write_bytes(
        b"f" * (_MERGE_HEAD_MAX_BYTES + 1)
    )
    path = root / _OPERATIONS
    path.write_text(path.read_text(encoding="utf-8") + "\n", encoding="utf-8")

    with pytest.raises(AuthorityError, match="サイズ上限"):
        snapshot_authority(root, allow_mid_merge=True)


_MALFORMED_MERGE_HEAD_CASES = (
    "valid_then_invalid",
    "empty",
    "non_hex",
    "missing_object",
    "non_commit_object",
    "leading_whitespace",
)


@pytest.mark.parametrize("case", _MALFORMED_MERGE_HEAD_CASES)
def test_malformed_merge_head_is_rejected(
    tmp_path: Path, case: str
) -> None:
    root = _prepare_repo(tmp_path)
    head = _git(root, "rev-parse", "HEAD")
    if case == "valid_then_invalid":
        raw = f"{head}\nnot-an-oid\n"
    elif case == "empty":
        raw = ""
    elif case == "non_hex":
        raw = "z" * 40 + "\n"
    elif case == "missing_object":
        raw = "f" * 40 + "\n"
        missing = subprocess.run(
            ["git", "-C", os.fspath(root), "cat-file", "-e", "f" * 40],
            check=False,
        )
        assert missing.returncode != 0
    elif case == "non_commit_object":
        raw = _git(root, "rev-parse", "HEAD^{tree}") + "\n"
    elif case == "leading_whitespace":
        raw = f" {head}\n"
    else:  # pragma: no cover - registration meta-test が閉じる
        raise AssertionError(case)
    (_git_dir(root) / "MERGE_HEAD").write_text(raw, encoding="ascii")
    path = root / _OPERATIONS
    path.write_text(path.read_text(encoding="utf-8") + "\n", encoding="utf-8")

    expected_message = "commit object" if case == "non_commit_object" else None
    with pytest.raises(AuthorityError, match=expected_message):
        snapshot_authority(root, allow_mid_merge=True)


def test_allow_mid_merge_is_ignored_for_historical_snapshot(
    tmp_path: Path,
) -> None:
    root = _prepare_repo(tmp_path)
    head = _git(root, "rev-parse", "HEAD")
    (_git_dir(root) / "MERGE_HEAD").write_text("not-an-oid\n", encoding="ascii")
    (root / _OPERATIONS).unlink()

    assert snapshot_authority(
        root, commit=head, allow_mid_merge=True
    ) == snapshot_authority(root, commit=head)


def test_malformed_merge_head_case_registration_is_complete() -> None:
    assert set(_MALFORMED_MERGE_HEAD_CASES) == {
        "valid_then_invalid",
        "empty",
        "non_hex",
        "missing_object",
        "non_commit_object",
        "leading_whitespace",
    }


def test_merge_head_without_trailing_newline_is_accepted(
    tmp_path: Path,
) -> None:
    root = _prepare_repo(tmp_path)
    head = _git(root, "rev-parse", "HEAD")
    (_git_dir(root) / "MERGE_HEAD").write_bytes(head.encode("ascii"))
    path = root / _OPERATIONS
    path.write_text(path.read_text(encoding="utf-8") + "\n", encoding="utf-8")

    assert snapshot_authority(
        root, allow_mid_merge=True
    ) == snapshot_authority(root, commit=head)


def test_merge_head_with_crlf_terminator_is_accepted(tmp_path: Path) -> None:
    root = _prepare_repo(tmp_path)
    head = _git(root, "rev-parse", "HEAD")
    (_git_dir(root) / "MERGE_HEAD").write_bytes(
        head.encode("ascii") + b"\r\n"
    )
    path = root / _OPERATIONS
    path.write_text(path.read_text(encoding="utf-8") + "\n", encoding="utf-8")

    assert snapshot_authority(
        root, allow_mid_merge=True
    ) == snapshot_authority(root, commit=head)


def test_merge_head_replacement_object_does_not_change_type_check(
    tmp_path: Path,
) -> None:
    root = _prepare_repo(tmp_path)
    head = _git(root, "rev-parse", "HEAD")
    blob = subprocess.run(
        ["git", "-C", os.fspath(root), "hash-object", "-w", "--stdin"],
        check=True,
        input=b"replacement-source\n",
        stdout=subprocess.PIPE,
    ).stdout.decode("ascii").strip()
    _git(root, "update-ref", f"refs/replace/{blob}", head)
    assert _git(root, "cat-file", "-t", blob) == "commit"
    assert _git(root, "--no-replace-objects", "cat-file", "-t", blob) == "blob"
    (_git_dir(root) / "MERGE_HEAD").write_text(blob + "\n", encoding="ascii")
    path = root / _OPERATIONS
    path.write_text(path.read_text(encoding="utf-8") + "\n", encoding="utf-8")

    with pytest.raises(AuthorityError, match="commit object"):
        snapshot_authority(root, allow_mid_merge=True)


def test_merge_detection_is_worktree_local(tmp_path: Path) -> None:
    root = _prepare_repo(tmp_path / "main")
    branch = _git(root, "branch", "--show-current")
    base_operations = (root / _OPERATIONS).read_text(encoding="utf-8")
    base_workers = (root / _WORKERS).read_text(encoding="utf-8")
    _git(root, "checkout", "-qb", "incoming")
    (root / _OPERATIONS).write_text(
        base_operations + "\nincoming linked-worktree note\n", encoding="utf-8"
    )
    _commit_authority_files(root, "incoming linked-worktree authority")
    _git(root, "checkout", "-q", branch)
    (root / _WORKERS).write_text(
        base_workers + "\nwave linked-worktree note\n", encoding="utf-8"
    )
    head = _commit_authority_files(root, "wave linked-worktree authority")
    sibling = tmp_path / "sibling"
    _git(root, "worktree", "add", "--detach", "-q", os.fspath(sibling), head)
    try:
        sibling_operations = (sibling / _OPERATIONS).read_bytes()
        (sibling / _OPERATIONS).write_bytes(sibling_operations + b"\n")
        with pytest.raises(AuthorityError, match="working tree"):
            snapshot_authority(sibling, allow_mid_merge=True)
        (sibling / _OPERATIONS).write_bytes(sibling_operations)

        _merge_no_commit(sibling, "incoming", expected_rc=0)
        sibling_git_dir = _git_dir(sibling)
        root_git_dir = _git_dir(root)
        assert sibling_git_dir != root_git_dir
        assert (sibling_git_dir / "MERGE_HEAD").is_file()
        assert not (root_git_dir / "MERGE_HEAD").exists()
        assert snapshot_authority(
            sibling, allow_mid_merge=True
        ) == snapshot_authority(sibling, commit=head)

        root_operations = (root / _OPERATIONS).read_bytes()
        (root / _OPERATIONS).write_bytes(root_operations + b"\n")
        with pytest.raises(AuthorityError, match="working tree"):
            snapshot_authority(root, allow_mid_merge=True)
        (root / _OPERATIONS).write_bytes(root_operations)

        _git(sibling, "merge", "--abort")
        assert not (sibling_git_dir / "MERGE_HEAD").exists()
        (sibling / _OPERATIONS).write_bytes(sibling_operations + b"\n")
        with pytest.raises(AuthorityError, match="working tree"):
            snapshot_authority(sibling, allow_mid_merge=True)
    finally:
        _git(root, "worktree", "remove", "--force", os.fspath(sibling))


def test_mid_merge_binding_target_is_head(tmp_path: Path) -> None:
    root = _prepare_repo(tmp_path / "merge")
    branch = _git(root, "branch", "--show-current")
    base_operations = (root / _OPERATIONS).read_text(encoding="utf-8")
    base_workers = (root / _WORKERS).read_text(encoding="utf-8")
    incoming_operations = _replace_model(base_operations, "gpt-5.6-terra")
    incoming_workers = _replace_worker_efforts(
        base_workers, author="high", review="medium", focus="low"
    )
    head_operations = _replace_model(base_operations, "gpt-5.6-luna")
    head_workers = _replace_worker_efforts(
        base_workers, author="medium", review="low", focus="high"
    )
    working_operations = _replace_model(base_operations, "gpt-5.6-working")
    working_workers = _replace_worker_efforts(
        base_workers, author="low", review="high", focus="medium"
    )

    _git(root, "checkout", "-qb", "incoming")
    (root / _OPERATIONS).write_text(incoming_operations, encoding="utf-8")
    (root / _WORKERS).write_text(incoming_workers, encoding="utf-8")
    incoming = _commit_authority_files(root, "incoming distinct authority")
    _git(root, "checkout", "-q", branch)
    (root / _OPERATIONS).write_text(head_operations, encoding="utf-8")
    (root / _WORKERS).write_text(head_workers, encoding="utf-8")
    head = _commit_authority_files(root, "head distinct authority")
    _merge_no_commit(root, "incoming", expected_rc=1)
    assert _git(root, "ls-files", "-u")
    (root / _OPERATIONS).write_text(working_operations, encoding="utf-8")
    (root / _WORKERS).write_text(working_workers, encoding="utf-8")

    working_root = _prepare_repo(
        tmp_path / "working-valid",
        operations=working_operations,
        workers=working_workers,
    )
    head_snapshot = snapshot_authority(root, commit=head)
    incoming_snapshot = snapshot_authority(root, commit=incoming)
    working_snapshot = snapshot_authority(working_root)
    assert len(
        {
            head_snapshot.other_model,
            incoming_snapshot.other_model,
            working_snapshot.other_model,
        }
    ) == 3
    snapshots = (head_snapshot, incoming_snapshot, working_snapshot)
    for effort_field in (
        "author_effort",
        "review_effort",
        "focus_effort",
    ):
        assert len(
            {getattr(snapshot, effort_field) for snapshot in snapshots}
        ) == 3
    section_hashes = tuple(
        {section.section: section.sha256 for section in snapshot.sections}
        for snapshot in snapshots
    )
    for section_id in ("DW-O01", "DW-S06-A", "DW-S06-C", "DW-S05-A"):
        assert len(
            {by_section[section_id] for by_section in section_hashes}
        ) == 3

    accepted = snapshot_authority(root, allow_mid_merge=True)

    assert accepted == head_snapshot
    assert accepted.authority_commit == head


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
