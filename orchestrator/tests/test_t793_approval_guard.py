"""T-793 unresolved approval marker gate と fold 全経路の回帰。"""

from __future__ import annotations

import dataclasses
import hashlib
import json
import logging
from pathlib import Path
import sys

import pytest

from orchestrator.publication import approval_guard
from orchestrator.tests import test_spool_fold as spool_test


ROOT = Path(__file__).resolve().parents[2]
spool_fold = spool_test.spool_fold

_MARKER_CASES = (
    ("fold-commit", b"__UNRESOLVED_APPROVAL_FOLD_COMMIT__"),
    ("generic", b"__UNRESOLVED__"),
)


def _approval_fragment(repo: Path, blob: bytes) -> Path:
    approved = repo / "approved.md"
    approved.write_bytes(blob)
    spool_test._commit(repo, "approved blob")
    commit = spool_test._run_git(repo, "rev-parse", "HEAD")
    sha256 = hashlib.sha256(blob).hexdigest()
    body = (
        "## {{D:approval}}. approval\n\n"
        "approved_blobs:\n"
        "  publication_core\n"
        "    path   = approved.md\n"
        f"    commit = {commit}\n"
        f"    sha256 = {sha256}\n"
    )
    return spool_test._fragment(repo, "decisions", body)


def _unresolved_approval_fragment(repo: Path) -> Path:
    body = (
        "## {{D:approval}}. approval\n\n"
        "approved_blobs:\n"
        "  publication_core\n"
        "    path   = missing.md\n"
        f"    commit = {'0' * 40}\n"
        f"    sha256 = {hashlib.sha256(b'').hexdigest()}\n"
    )
    return spool_test._fragment(repo, "decisions", body)


def _plan_with_marker_only_in_after_bytes(repo: Path, marker: bytes):
    fragment = _approval_fragment(repo, b"stable payload\n")
    marker_path = repo / "marker-only-after.md"
    marker_blob = b"payload " + marker + b"\n"
    marker_path.write_bytes(marker_blob)
    spool_test._commit(repo, "marker blob outside fragment")
    marker_commit = spool_test._run_git(repo, "rev-parse", "HEAD")
    marker_sha256 = hashlib.sha256(marker_blob).hexdigest()
    plan = spool_fold.plan_fold(repo, fold_date="2026-08-11")
    decision_target = next(
        target for target in plan.targets if target.path == "docs/decisions.md"
    )
    injected = (
        "\n## D999. injected approval (2026-08-11)\n\n"
        "approved_blobs:\n"
        "  publication_core\n"
        "    path   = marker-only-after.md\n"
        f"    commit = {marker_commit}\n"
        f"    sha256 = {marker_sha256}\n"
    ).encode("utf-8")
    after_bytes = decision_target.after_bytes + injected
    altered_target = dataclasses.replace(
        decision_target,
        after_bytes=after_bytes,
        after_sha256=hashlib.sha256(after_bytes).hexdigest(),
    )
    altered_targets = tuple(
        altered_target if target.path == "docs/decisions.md" else target
        for target in plan.targets
    )
    transaction_id = spool_fold._plan_transaction_id(
        plan.fold_date,
        plan.origin,
        plan.input_closure_sha256,
        plan.fragments,
        plan.gc_paths,
        plan.projected_worklog_bytes,
        plan.rotation_path,
        altered_targets,
    )
    assert marker_path.name.encode("utf-8") not in fragment.read_bytes()
    return dataclasses.replace(
        plan,
        transaction_id=transaction_id,
        targets=altered_targets,
    )


def test_p2_draft_markers_outside_approved_blobs_do_not_stop_fold() -> None:
    draft = ROOT / "output/insights/2026-08-11_t139-pubcore-stage2/addendum-p-draft.md"
    draft_bytes = draft.read_bytes()
    assert any(
        marker in draft_bytes for marker in approval_guard.UNRESOLVED_APPROVAL_MARKERS
    )
    assert approval_guard.require_resolved_approval_markers(ROOT, (draft_bytes,)) is None


def test_non_marker_draft_words_in_pinned_blob_are_accepted(
    tmp_path: Path,
) -> None:
    repo = spool_test._repo(tmp_path)
    fragment = _approval_fragment(repo, "未確定 未凍結 draft\n".encode("utf-8"))
    assert approval_guard.require_resolved_approval_markers(
        repo, (fragment.read_bytes(),)
    ) is None


def test_well_formed_unresolvable_pin_is_diagnostic_but_accepted(
    tmp_path: Path,
    caplog: pytest.LogCaptureFixture,
) -> None:
    repo = spool_test._repo(tmp_path)
    _unresolved_approval_fragment(repo)

    with caplog.at_level(logging.WARNING, logger=approval_guard.__name__):
        assert spool_fold.validate_spool_tree(repo) == []
        assert spool_fold.plan_fold(repo, fold_date="2026-08-11").status == "planned"

    diagnostics = [
        record.getMessage()
        for record in caplog.records
        if record.name == approval_guard.__name__
    ]
    assert diagnostics
    assert all(
        f"[{approval_guard.UNRESOLVED_APPROVED_BLOB_REF_DIAGNOSTIC_CODE}]"
        in message
        for message in diagnostics
    )


def test_duplicate_field_in_approved_blob_role_is_rejected_with_dedicated_code(
    tmp_path: Path,
) -> None:
    repo = spool_test._repo(tmp_path)
    fragment = _approval_fragment(repo, b"stable payload\n")
    raw = fragment.read_bytes()
    stable_sha256 = hashlib.sha256(b"stable payload\n").hexdigest()
    sha_line = (
        f"    sha256 = {stable_sha256}\n"
    ).encode("ascii")
    assert raw.count(sha_line) == 1
    fragment.write_bytes(raw.replace(sha_line, sha_line + sha_line, 1))

    issues = spool_fold.validate_spool_tree(repo)
    assert [issue.code for issue in issues] == ["malformed-approved-blob-ref"]
    with pytest.raises(
        approval_guard.MalformedApprovedBlobRefError,
        match="field 'sha256' が重複",
    ):
        approval_guard.require_resolved_approval_markers(
            repo, (fragment.read_bytes(),)
        )


def test_incomplete_approved_blob_role_is_rejected_with_dedicated_code(
    tmp_path: Path,
) -> None:
    repo = spool_test._repo(tmp_path)
    fragment = _unresolved_approval_fragment(repo)
    raw = fragment.read_bytes()
    raw = raw.replace(b"    sha256 = ", b"    omitted = ", 1)
    fragment.write_bytes(raw)

    issues = spool_fold.validate_spool_tree(repo)
    assert [issue.code for issue in issues] == ["malformed-approved-blob-ref"]


@pytest.mark.parametrize(
    ("case", "marker"),
    _MARKER_CASES,
    ids=("fold-commit", "generic"),
)
def test_exact_marker_in_pinned_blob_is_rejected_by_discover(
    tmp_path: Path,
    case: str,
    marker: bytes,
) -> None:
    assert case in {"fold-commit", "generic"}
    repo = spool_test._repo(tmp_path)
    _approval_fragment(repo, b"payload " + marker + b"\n")
    issues = spool_fold.validate_spool_tree(repo)
    assert [issue.code for issue in issues] == ["unresolved-approval-marker"]
    with pytest.raises(spool_fold.SpoolValidationError):
        spool_fold.plan_fold(repo, fold_date="2026-08-11")


def test_spool_guard_resolves_from_source_root_without_repo_on_sys_path(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    repo = spool_test._repo(tmp_path)
    _approval_fragment(repo, b"payload __UNRESOLVED__\n")
    root = ROOT.resolve()
    root_free_path = [
        entry
        for entry in sys.path
        if Path(entry or ".").resolve() != root
    ]
    monkeypatch.setattr(sys, "path", root_free_path)
    for module_name in (
        "orchestrator.publication.approval_guard",
        "orchestrator.preregistration.blobref",
        "orchestrator.publication",
        "orchestrator.preregistration",
        "orchestrator",
    ):
        monkeypatch.delitem(sys.modules, module_name, raising=False)

    issues = spool_fold.validate_spool_tree(repo)

    assert [issue.code for issue in issues] == ["unresolved-approval-marker"]
    assert sys.path == root_free_path


def test_exact_marker_is_rejected_when_plan_is_passed_directly_to_apply_fold(
    tmp_path: Path,
) -> None:
    repo = spool_test._repo(tmp_path)
    plan = _plan_with_marker_only_in_after_bytes(
        repo, b"__UNRESOLVED_APPROVAL_FOLD_COMMIT__"
    )
    decisions_before = (repo / "docs/decisions.md").read_bytes()

    with pytest.raises(spool_fold.TransactionError, match="未確定 marker"):
        spool_fold.apply_fold(repo, plan)

    assert (repo / "docs/decisions.md").read_bytes() == decisions_before
    assert not spool_fold._state_path(repo).exists()


def test_exact_marker_is_rejected_by_main_resume_path(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    repo = spool_test._repo(tmp_path)
    plan = _plan_with_marker_only_in_after_bytes(repo, b"__UNRESOLVED__")
    state_path = spool_fold._state_path(repo)
    state = (
        json.dumps(
            spool_fold._plan_state(plan),
            ensure_ascii=False,
            separators=(",", ":"),
            sort_keys=True,
        ).encode("utf-8")
        + b"\n"
    )
    spool_fold._atomic_write(state_path, state)
    decisions_before = (repo / "docs/decisions.md").read_bytes()
    original_file = spool_fold.__file__
    spool_fold.__file__ = str(repo / "tools/spool_fold.py")
    try:
        returncode = spool_fold.main([])
    finally:
        spool_fold.__file__ = original_file

    captured = capsys.readouterr()
    assert returncode == 2
    assert "未確定 marker" in captured.err
    assert (repo / "docs/decisions.md").read_bytes() == decisions_before
    assert state_path.exists()


def test_discover_plan_path_checks_the_rendered_decisions_after_bytes(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    repo = spool_test._repo(tmp_path)
    _approval_fragment(repo, b"stable payload\n")
    calls: list[tuple[bytes, ...]] = []
    original = approval_guard.require_resolved_approval_markers

    def recording_guard(repository_root: Path, decision_payloads) -> None:
        payloads = tuple(decision_payloads)
        calls.append(payloads)
        original(repository_root, payloads)

    monkeypatch.setattr(
        approval_guard,
        "require_resolved_approval_markers",
        recording_guard,
    )
    plan = spool_fold.plan_fold(repo, fold_date="2026-08-11")
    after_bytes = next(
        target.after_bytes
        for target in plan.targets
        if target.path == "docs/decisions.md"
    )
    assert any(after_bytes in payloads for payloads in calls)


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-q"]))
