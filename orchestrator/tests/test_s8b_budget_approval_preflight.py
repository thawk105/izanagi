# -*- coding: utf-8 -*-
"""S8B budget approval preflight の非権威・read-only 契約。"""
from __future__ import annotations

import ast
import copy
import errno
import hashlib
import json
import os
import stat
import subprocess
import sys
from pathlib import Path

import pytest


REPO = Path(__file__).resolve().parents[2]
TOOL_PATH = REPO / "tools/s8b_budget_approval_preflight.py"
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from orchestrator.campaign import s8b_holdout_freeze as FREEZE  # noqa: E402
from tools import s8b_budget_approval_preflight as TOOL  # noqa: E402


_EXPECTED_CLI_OPTIONS = {"-h", "--help", "--out", "--candidate"}
_EXPECTED_SKELETON = (
    b'{"required_fields":["approved_at","approver","budget"],'
    b'"scope":"s8b-holdout-freeze/v2:g1-budget",'
    b'"status":"draft-not-an-approval"}'
)
_EXPECTED_TOOL_IMPORTS = {
    ("import", "argparse"),
    ("import", "datetime"),
    ("import", "hashlib"),
    ("import", "json"),
    ("import", "os"),
    ("import", "stat"),
    ("import", "sys"),
    ("from", "__future__.annotations"),
    ("from", "collections.abc.Mapping"),
    ("from", "collections.abc.Sequence"),
    ("from", "orchestrator.campaign.s8b_holdout_freeze"),
    ("from", "pathlib.Path"),
}


def _active_v1_raw() -> bytes:
    return (REPO / FREEZE.FREEZE_REL).read_bytes()


def _install_active_v1(repo: Path) -> tuple[str, ...]:
    destination = repo / FREEZE.FREEZE_REL
    destination.parent.mkdir(parents=True)
    raw = _active_v1_raw()
    destination.write_bytes(raw)
    document = json.loads(raw)
    return tuple(sorted(document["holdouts"]))


def _approval(holdout_ids: tuple[str, ...]) -> dict:
    per_holdout = {holdout_id: len(holdout_id) for holdout_id in holdout_ids}
    return {
        "approved_at": "2026-01-01T00:00:00Z",
        "approver": "fixture-human",
        "budget": {
            "total_bench_s": sum(per_holdout.values()),
            "per_holdout_bench_s": per_holdout,
            "oracle_shared": True,
        },
        "scope": FREEZE.BUDGET_APPROVAL_SCOPE,
    }


def _write_candidate(path: Path, approval: dict, *, canonical: bool = True) -> bytes:
    path.parent.mkdir(parents=True, exist_ok=True)
    if canonical:
        raw = FREEZE._canonical_bytes(approval)
    else:
        raw = json.dumps(approval, ensure_ascii=False, indent=2).encode("utf-8")
    path.write_bytes(raw)
    return raw


def _all_option_strings(parser) -> set[str]:
    found = set()
    pending = [parser]
    while pending:
        current = pending.pop()
        for action in current._actions:
            found.update(action.option_strings)
            choices = getattr(action, "choices", None)
            if isinstance(choices, dict):
                pending.extend(choices.values())
    return found


def _imported_names(tree: ast.AST) -> set[tuple[str, str]]:
    imported = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported.update(("import", alias.name) for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            prefix = "." * node.level + (node.module or "")
            imported.update(
                ("from", f"{prefix}.{alias.name}") for alias in node.names
            )
        elif (
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Name)
            and node.func.id == "__import__"
        ):
            imported.add(("dynamic", ast.dump(node.args[0]) if node.args else ""))
    return imported


def _tree_snapshot(root: Path) -> dict[str, tuple[str, bytes | str]]:
    snapshot = {}
    for path in sorted(root.rglob("*")):
        relative = path.relative_to(root).as_posix()
        metadata = path.lstat()
        if stat.S_ISREG(metadata.st_mode):
            snapshot[relative] = ("file", path.read_bytes())
        elif stat.S_ISLNK(metadata.st_mode):
            snapshot[relative] = ("symlink", os.readlink(path))
        elif stat.S_ISDIR(metadata.st_mode):
            snapshot[relative] = ("directory", b"")
        else:
            snapshot[relative] = ("other", b"")
    return snapshot


def test_n1_has_no_approver_input_source_and_skeleton_has_no_authority_values(
        tmp_path, capsys):
    options = _all_option_strings(TOOL._parser())
    assert options == _EXPECTED_CLI_OPTIONS

    source = TOOL_PATH.read_text(encoding="utf-8")
    tree = ast.parse(source, filename=str(TOOL_PATH))
    assert _imported_names(tree) == _EXPECTED_TOOL_IMPORTS

    out = tmp_path / "approval-skeleton.json"
    assert TOOL.main(["skeleton", "--out", str(out)]) == 0
    capsys.readouterr()
    assert out.read_bytes() == _EXPECTED_SKELETON


def test_verify_does_not_fill_empty_approver_from_environment(
        tmp_path, monkeypatch, capsys):
    repo = tmp_path / "repo"
    holdout_ids = _install_active_v1(repo)
    monkeypatch.setattr(TOOL, "_REPO_ROOT", repo)
    monkeypatch.setenv("S8B_APPROVAL_USER", "environment-approver")
    monkeypatch.setenv("USER", "environment-user")
    monkeypatch.setenv("LOGNAME", "environment-logname")
    approval = _approval(holdout_ids)
    approval["approver"] = ""
    candidate = tmp_path / "empty-approver.json"
    _write_candidate(candidate, approval)
    before_tmp = _tree_snapshot(tmp_path)

    assert TOOL.main(["verify", "--candidate", str(candidate)]) == 1

    captured = capsys.readouterr()
    assert captured.out == ""
    assert "budget approval.approver" in captured.err
    assert _tree_snapshot(tmp_path) == before_tmp


def test_n2_skeleton_at_contract_path_is_rejected_even_with_matching_pin(
        tmp_path, capsys):
    # Contract test only: this rejection is intentionally overdetermined.  It does
    # not claim that any one missing approval field is the sole gate.
    candidate = tmp_path / FREEZE.BUDGET_APPROVAL_REL
    candidate.parent.mkdir(parents=True)
    assert TOOL.main(["skeleton", "--out", str(candidate)]) == 0
    capsys.readouterr()
    raw = candidate.read_bytes()
    matching_pin = hashlib.sha256(raw).hexdigest()
    holdout_ids = tuple(sorted(json.loads(_active_v1_raw())["holdouts"]))

    with pytest.raises(FREEZE.FreezeError):
        FREEZE._load_budget_approval(
            tmp_path, holdout_ids=holdout_ids, approval_sha256=matching_pin,
        )


def test_skeleton_rejects_repo_existing_leaf_and_symlink_traversal(
        tmp_path, monkeypatch, capsys):
    repo = tmp_path / "repo"
    repo.mkdir()
    monkeypatch.setattr(TOOL, "_REPO_ROOT", repo)

    internal_parent = repo / "drafts"
    internal_parent.mkdir()
    internal = internal_parent / "candidate.json"
    assert TOOL.main(["skeleton", "--out", str(internal)]) == 1
    assert not internal.exists()

    external = tmp_path / "external"
    external.mkdir()
    existing = external / "existing.json"
    existing.write_bytes(b"sentinel")
    assert TOOL.main(["skeleton", "--out", str(existing)]) == 1
    assert existing.read_bytes() == b"sentinel"

    real_parent = external / "real"
    real_parent.mkdir()
    linked_parent = external / "linked"
    linked_parent.symlink_to(real_parent, target_is_directory=True)
    assert TOOL.main(
        ["skeleton", "--out", str(linked_parent / "candidate.json")]
    ) == 1
    assert not (real_parent / "candidate.json").exists()

    target = external / "target.json"
    target.write_bytes(b"target-sentinel")
    linked_leaf = external / "linked-leaf.json"
    linked_leaf.symlink_to(target)
    assert TOOL.main(["skeleton", "--out", str(linked_leaf)]) == 1
    assert target.read_bytes() == b"target-sentinel"
    capsys.readouterr()


def test_skeleton_rejects_dangling_symlink_leaf_via_nofollow_without_excl(
        tmp_path, monkeypatch):
    repo = tmp_path / "repo"
    repo.mkdir()
    monkeypatch.setattr(TOOL, "_REPO_ROOT", repo)

    external = tmp_path / "external"
    external.mkdir()
    missing_target = external / "missing-target.json"
    linked_leaf = external / "dangling-leaf.json"
    linked_leaf.symlink_to(missing_target)

    # A dangling symlink still triggers O_EXCL with EEXIST on Linux.  Disable
    # that independent gate here so this node isolates leaf O_NOFOLLOW.
    monkeypatch.setattr(TOOL.os, "O_EXCL", 0)
    with pytest.raises(OSError) as raised:
        TOOL._write_create_only_outside_repo(
            linked_leaf, TOOL._skeleton_bytes(),
        )

    assert raised.value.errno == errno.ELOOP
    assert linked_leaf.is_symlink()
    assert not missing_target.exists()


def test_relative_skeleton_out_is_argparse_error():
    with pytest.raises(SystemExit) as raised:
        TOOL._parser().parse_args(["skeleton", "--out", "relative.json"])
    assert raised.value.code == 2


def test_verify_success_prints_hash_and_pin_and_changes_no_repo_bytes(
        tmp_path, monkeypatch, capsys):
    repo = tmp_path / "repo"
    holdout_ids = _install_active_v1(repo)
    monkeypatch.setattr(TOOL, "_REPO_ROOT", repo)

    source = repo / FREEZE.SCRIPT_REL
    source.parent.mkdir(parents=True, exist_ok=True)
    source.write_bytes(b"production-source-sentinel")
    canonical = repo / FREEZE.BUDGET_APPROVAL_REL
    canonical.parent.mkdir(parents=True, exist_ok=True)
    canonical.write_bytes(b"canonical-approval-sentinel")
    budget = repo / "output/s8b-freeze-budget-inputs/g1.json"
    budget.parent.mkdir(parents=True, exist_ok=True)
    budget.write_bytes(b"budget-sentinel")
    other = repo / "unrelated.bin"
    other.write_bytes(b"unrelated-sentinel")

    candidate = tmp_path / "human-candidate.json"
    raw = _write_candidate(candidate, _approval(holdout_ids))
    before_tmp = _tree_snapshot(tmp_path)
    before_repo = _tree_snapshot(repo)
    before_candidate = candidate.read_bytes()

    assert TOOL.main(["verify", "--candidate", str(candidate)]) == 0

    captured = capsys.readouterr()
    expected_sha256 = hashlib.sha256(raw).hexdigest()
    assert captured.err == ""
    assert captured.out.splitlines() == [
        f"raw_sha256={expected_sha256}",
        f'BUDGET_APPROVAL_SHA256: Optional[str] = "{expected_sha256}"',
    ]
    assert _tree_snapshot(tmp_path) == before_tmp
    assert _tree_snapshot(repo) == before_repo
    assert candidate.read_bytes() == before_candidate


def test_verify_and_loader_accept_same_canonical_candidate(
        tmp_path, monkeypatch):
    repo = tmp_path / "repo"
    holdout_ids = _install_active_v1(repo)
    monkeypatch.setattr(TOOL, "_REPO_ROOT", repo)
    approval = _approval(holdout_ids)
    candidate = tmp_path / "human-candidate.json"
    raw = _write_candidate(candidate, approval)
    canonical = repo / FREEZE.BUDGET_APPROVAL_REL
    canonical.parent.mkdir(parents=True, exist_ok=True)
    canonical.write_bytes(raw)
    matching_pin = hashlib.sha256(raw).hexdigest()

    assert TOOL._verify_candidate(candidate) == matching_pin
    loaded, actual_sha256 = FREEZE._load_budget_approval(
        repo, holdout_ids=holdout_ids, approval_sha256=matching_pin,
    )
    assert loaded == approval
    assert actual_sha256 == matching_pin


@pytest.mark.parametrize(
    "mutation",
    [
        lambda approval, holdouts: approval.update(extra="unexpected"),
        lambda approval, holdouts: approval.update(scope="wrong-scope"),
        lambda approval, holdouts: approval.update(approver="  "),
        lambda approval, holdouts: approval.update(
            approved_at="2026-01-01T00:00:00+00:00"
        ),
        lambda approval, holdouts: approval["budget"].update(
            extra="unexpected"
        ),
        lambda approval, holdouts: approval["budget"].update(
            oracle_shared=False
        ),
        lambda approval, holdouts: approval["budget"].update(
            total_bench_s=-1
        ),
        lambda approval, holdouts: approval["budget"].update(
            total_bench_s=-0.0
        ),
        lambda approval, holdouts: approval["budget"][
            "per_holdout_bench_s"
        ].pop(holdouts[0]),
    ],
    ids=[
        "approval-extra-key",
        "scope",
        "empty-approver",
        "timestamp",
        "budget-extra-key",
        "oracle-shared",
        "negative",
        "negative-zero",
        "holdout-missing",
    ],
)
def test_verify_and_loader_reject_same_contract_violation(
        tmp_path, monkeypatch, mutation):
    repo = tmp_path / "repo"
    holdout_ids = _install_active_v1(repo)
    monkeypatch.setattr(TOOL, "_REPO_ROOT", repo)
    approval = _approval(holdout_ids)
    mutation(approval, holdout_ids)
    candidate = tmp_path / "invalid-candidate.json"
    raw = _write_candidate(candidate, approval)
    canonical = repo / FREEZE.BUDGET_APPROVAL_REL
    canonical.parent.mkdir(parents=True, exist_ok=True)
    canonical.write_bytes(raw)
    matching_pin = hashlib.sha256(raw).hexdigest()

    with pytest.raises(FREEZE.FreezeError):
        TOOL._verify_candidate(candidate)
    with pytest.raises(FREEZE.FreezeError):
        FREEZE._load_budget_approval(
            repo, holdout_ids=holdout_ids, approval_sha256=matching_pin,
        )


def test_design_asymmetry_verify_does_not_enforce_authority_pin(
        tmp_path, monkeypatch):
    repo = tmp_path / "repo"
    holdout_ids = _install_active_v1(repo)
    monkeypatch.setattr(TOOL, "_REPO_ROOT", repo)
    approval = _approval(holdout_ids)
    candidate = tmp_path / "human-candidate.json"
    raw = _write_candidate(candidate, approval)
    canonical = repo / FREEZE.BUDGET_APPROVAL_REL
    canonical.parent.mkdir(parents=True, exist_ok=True)
    canonical.write_bytes(raw)
    matching_pin = hashlib.sha256(raw).hexdigest()
    mismatched_pin = "0" * 64
    assert mismatched_pin != matching_pin

    assert TOOL._verify_candidate(candidate) == matching_pin
    with pytest.raises(
            FREEZE.FreezeError, match="^budget-approval-sha256-mismatch$"):
        FREEZE._load_budget_approval(
            repo, holdout_ids=holdout_ids, approval_sha256=mismatched_pin,
        )


def test_design_asymmetry_verify_accepts_arbitrary_candidate_path(
        tmp_path, monkeypatch):
    repo = tmp_path / "repo"
    holdout_ids = _install_active_v1(repo)
    monkeypatch.setattr(TOOL, "_REPO_ROOT", repo)
    candidate = tmp_path / "arbitrary-location.json"
    raw = _write_candidate(candidate, _approval(holdout_ids))
    matching_pin = hashlib.sha256(raw).hexdigest()

    assert TOOL._verify_candidate(candidate) == matching_pin
    with pytest.raises(FREEZE.FreezeError, match="nofollow .*読めない"):
        FREEZE._load_budget_approval(
            repo, holdout_ids=holdout_ids, approval_sha256=matching_pin,
        )


def test_design_asymmetry_loader_uses_caller_holdout_ids(
        tmp_path, monkeypatch):
    repo = tmp_path / "repo"
    active_holdout_ids = _install_active_v1(repo)
    monkeypatch.setattr(TOOL, "_REPO_ROOT", repo)
    caller_holdout_ids = active_holdout_ids[1:]
    approval = _approval(caller_holdout_ids)
    candidate = tmp_path / "caller-scoped-candidate.json"
    raw = _write_candidate(candidate, approval)
    canonical = repo / FREEZE.BUDGET_APPROVAL_REL
    canonical.parent.mkdir(parents=True, exist_ok=True)
    canonical.write_bytes(raw)
    matching_pin = hashlib.sha256(raw).hexdigest()

    with pytest.raises(
            FREEZE.FreezeError, match="holdout 集合が不一致"):
        TOOL._verify_candidate(candidate)
    loaded, actual_sha256 = FREEZE._load_budget_approval(
        repo, holdout_ids=caller_holdout_ids, approval_sha256=matching_pin,
    )
    assert loaded == approval
    assert actual_sha256 == matching_pin


@pytest.mark.parametrize(
    "mutation",
    [
        lambda approval, holdouts: approval.update(extra="unexpected"),
        lambda approval, holdouts: approval.update(scope="wrong-scope"),
        lambda approval, holdouts: approval.update(approver="  "),
        lambda approval, holdouts: approval.update(
            approved_at="2026-01-01T00:00:00+00:00"
        ),
        lambda approval, holdouts: approval["budget"].update(
            oracle_shared=False
        ),
        lambda approval, holdouts: approval["budget"].update(
            total_bench_s=-len(holdouts)
        ),
        lambda approval, holdouts: approval["budget"].update(
            extra="unexpected"
        ),
        lambda approval, holdouts: approval["budget"][
            "per_holdout_bench_s"
        ].pop(holdouts[0]),
        lambda approval, holdouts: approval["budget"][
            "per_holdout_bench_s"
        ].update({holdouts[0]: -len(holdouts[0])}),
    ],
    ids=[
        "approval-keys",
        "scope",
        "approver",
        "timestamp",
        "oracle-shared",
        "total-finite-nonnegative",
        "budget-keys",
        "holdout-exact-set",
        "per-holdout-finite-nonnegative",
    ],
)
def test_verify_rejects_each_approval_contract_violation(
        tmp_path, monkeypatch, capsys, mutation):
    repo = tmp_path / "repo"
    holdout_ids = _install_active_v1(repo)
    monkeypatch.setattr(TOOL, "_REPO_ROOT", repo)
    approval = _approval(holdout_ids)
    mutation(approval, holdout_ids)
    candidate = tmp_path / "invalid-candidate.json"
    _write_candidate(candidate, approval)
    before_tmp = _tree_snapshot(tmp_path)

    assert TOOL.main(["verify", "--candidate", str(candidate)]) == 1
    captured = capsys.readouterr()
    assert captured.out == ""
    assert captured.err.startswith("ERROR: ")
    assert _tree_snapshot(tmp_path) == before_tmp


def test_verify_rejects_noncanonical_timestamp_after_parser_accepts(
        tmp_path, monkeypatch, capsys):
    value = "2026-1-01T00:00:00Z"
    parsed = TOOL.dt.datetime.strptime(value, "%Y-%m-%dT%H:%M:%SZ")
    assert parsed.strftime("%Y-%m-%dT%H:%M:%SZ") != value

    repo = tmp_path / "repo"
    holdout_ids = _install_active_v1(repo)
    monkeypatch.setattr(TOOL, "_REPO_ROOT", repo)
    approval = _approval(holdout_ids)
    approval["approved_at"] = value
    candidate = tmp_path / "noncanonical-timestamp.json"
    _write_candidate(candidate, approval)

    assert TOOL.main(["verify", "--candidate", str(candidate)]) == 1
    captured = capsys.readouterr()
    assert captured.out == ""
    assert "canonical UTC timestamp" in captured.err


def test_verify_rejects_noncanonical_bytes(tmp_path, monkeypatch, capsys):
    repo = tmp_path / "repo"
    holdout_ids = _install_active_v1(repo)
    monkeypatch.setattr(TOOL, "_REPO_ROOT", repo)
    candidate = tmp_path / "noncanonical-candidate.json"
    _write_candidate(candidate, _approval(holdout_ids), canonical=False)

    assert TOOL.main(["verify", "--candidate", str(candidate)]) == 1
    captured = capsys.readouterr()
    assert captured.out == ""
    assert "canonical JSON" in captured.err


def test_verify_rejects_symlink_candidate(tmp_path, monkeypatch, capsys):
    repo = tmp_path / "repo"
    holdout_ids = _install_active_v1(repo)
    monkeypatch.setattr(TOOL, "_REPO_ROOT", repo)
    target = tmp_path / "target.json"
    raw = _write_candidate(target, _approval(holdout_ids))
    candidate = tmp_path / "candidate-link.json"
    candidate.symlink_to(target)

    assert TOOL.main(["verify", "--candidate", str(candidate)]) == 1
    captured = capsys.readouterr()
    assert captured.out == ""
    assert captured.err.startswith("ERROR: ")
    assert target.read_bytes() == raw


def test_direct_cli_import_is_cwd_independent(tmp_path):
    holdout_ids = tuple(sorted(json.loads(_active_v1_raw())["holdouts"]))
    candidate = tmp_path / "human-candidate.json"
    raw = _write_candidate(candidate, _approval(holdout_ids))

    completed = subprocess.run(
        [sys.executable, str(TOOL_PATH), "verify", "--candidate", str(candidate)],
        cwd=tmp_path,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )

    expected_sha256 = hashlib.sha256(raw).hexdigest()
    assert completed.returncode == 0, completed.stderr
    assert completed.stderr == ""
    assert completed.stdout.splitlines() == [
        f"raw_sha256={expected_sha256}",
        f'BUDGET_APPROVAL_SHA256: Optional[str] = "{expected_sha256}"',
    ]
