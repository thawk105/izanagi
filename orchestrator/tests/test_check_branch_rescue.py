from __future__ import annotations

import datetime as dt
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
from typing import Any

import pytest


ROOT = Path(__file__).resolve().parents[2]
TOOL_PATH = ROOT / "tools" / "check_branch_rescue.py"
LANDED_PATH = ROOT / "tools" / "check_branch_landed.py"
AUDIT_PATH = ROOT / "tools" / "audit_dangling_commits.py"
SPEC = importlib.util.spec_from_file_location("check_branch_rescue", TOOL_PATH)
assert SPEC is not None and SPEC.loader is not None
TOOL = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = TOOL
SPEC.loader.exec_module(TOOL)


def _git(repo: Path, *args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(
        ["git", *args], cwd=repo, text=True,
        stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        env={
            **os.environ,
            "GIT_CONFIG_NOSYSTEM": "1",
            "GIT_TERMINAL_PROMPT": "0",
            "LC_ALL": "C",
        },
        check=False,
    )
    if check and result.returncode:
        raise AssertionError(
            f"git {' '.join(args)} failed ({result.returncode})\n"
            f"{result.stdout}\n{result.stderr}"
        )
    return result


def _write(repo: Path, relative: str, content: str | bytes) -> Path:
    path = repo / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    if isinstance(content, bytes):
        path.write_bytes(content)
    else:
        path.write_text(content, encoding="utf-8")
    return path


def _commit(repo: Path, message: str) -> str:
    _git(repo, "add", "-A")
    _git(repo, "commit", "-m", message)
    return _git(repo, "rev-parse", "HEAD").stdout.strip()


def _init_repo(tmp_path: Path) -> Path:
    repo = tmp_path / "repo"
    repo.mkdir(parents=True)
    _git(repo, "init", "-b", "main")
    _git(repo, "config", "user.name", "test")
    _git(repo, "config", "user.email", "test@example.invalid")
    _git(repo, "config", "commit.gpgsign", "false")
    _git(repo, "config", "tag.gpgsign", "false")
    _git(repo, "config", "core.hooksPath", "/dev/null")
    _git(repo, "config", "core.logAllRefUpdates", "true")
    _git(repo, "config", "gc.auto", "6700")
    _git(repo, "config", "gc.pruneExpire", "14.days.ago")
    _git(repo, "config", "gc.reflogExpire", "90.days.ago")
    _git(repo, "config", "gc.reflogExpireUnreachable", "30.days.ago")
    _write(repo, "base.txt", "base\n")
    _commit(repo, "base")
    return repo


def _empty_child(repo: Path, parent: str | None = None) -> str:
    parent = parent or _git(repo, "rev-parse", "main").stdout.strip()
    tree = _git(repo, "rev-parse", f"{parent}^{{tree}}").stdout.strip()
    return _git(repo, "commit-tree", tree, "-p", parent).stdout.strip()


def _make_fake_landed(path: Path, verdict: str = "landed", *, mutate: bool = False) -> Path:
    rc = {"landed": 0, "not-landed": 1, "indeterminate": 2}[verdict]
    body = f"""#!/usr/bin/env python3
import json
import subprocess
import sys
if {mutate!r}:
    subprocess.run(["git", "commit", "--allow-empty", "-m", "snapshot mutation"], check=True,
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
payload = {{
    "schema": "izanagi-branch-landed-v1",
    "branch_delete_authorized": False,
    "manual_review_required": True,
    "decision": {{"verdict": {verdict!r}, "reason": "fake-{verdict}",
                   "conclusive": {verdict != 'indeterminate'!r}}},
    "observations": {{"ledger_corpus": {{"bytes_read": 0}}}},
}}
print(json.dumps(payload, sort_keys=True))
raise SystemExit({rc})
"""
    path.write_text(body, encoding="utf-8")
    return path


def _make_fake_audit(path: Path, commits: list[str]) -> Path:
    rows = "".join(f"  commit {oid} (fixture)\\n" for oid in commits)
    body = f"""#!/usr/bin/env python3
print("audit_dangling_commits: 要確認の到達不能変更 {len(commits)} commit")
print({rows!r}, end="")
raise SystemExit({1 if commits else 0})
"""
    path.write_text(body, encoding="utf-8")
    return path


def _run_tool(
    repo: Path,
    *extra: str,
    timeout: float = 60,
    env: dict[str, str] | None = None,
) -> tuple[int, dict[str, Any], subprocess.CompletedProcess[str]]:
    result = subprocess.run(
        [sys.executable, str(TOOL_PATH), "--repo", str(repo), *extra],
        cwd=ROOT, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        env={**os.environ, **(env or {})}, timeout=timeout, check=False,
    )
    assert result.stdout.count("\n") == 1, result.stdout + result.stderr
    payload = json.loads(result.stdout)
    assert payload["schema"] == "izanagi-branch-rescue-v1"
    return result.returncode, payload, result


def _topic_with_file(repo: Path, name: str = "topic", content: str = "topic\n") -> str:
    _git(repo, "switch", "-c", name)
    _write(repo, f"{name}.txt", content)
    oid = _commit(repo, name)
    _git(repo, "switch", "main")
    return oid


def _closure_oids(payload: dict[str, Any]) -> list[str]:
    return [item["oid"] for item in payload["deletion_loss_closure"]["commits"]]


def _commit_row(payload: dict[str, Any], oid: str) -> dict[str, Any]:
    rows = [item for item in payload["deletion_loss_closure"]["commits"] if item["oid"] == oid]
    assert len(rows) == 1, payload["deletion_loss_closure"]
    return rows[0]


def _all_key_values(value: Any, key: str) -> list[Any]:
    result: list[Any] = []
    if isinstance(value, dict):
        for child_key, child in value.items():
            if child_key == key:
                result.append(child)
            result.extend(_all_key_values(child, key))
    elif isinstance(value, list):
        for child in value:
            result.extend(_all_key_values(child, key))
    return result


def _ledger_entry(oid: str, *, retained: bool = False) -> dict[str, Any]:
    return {
        "schema": "izanagi-unreachable-object-ledger-v1",
        "entry_id": "e-1",
        "recorded_at": "2030-01-01T00:00:00Z",
        "source_refs": ["refs/heads/topic"],
        "source_tips": {"refs/heads/topic": oid},
        "assessment_report_sha256": "a" * 64,
        "object_oid": oid,
        "object_type": "commit",
        "assessment_schema": "izanagi-branch-landed-v1",
        "assessment_verdict": "not-landed",
        "assessment_reason": "fixture",
        "storage_kind": "loose",
        "object_mtime": "2030-01-01T00:00:00Z",
        "loss_possible_not_before": "2030-02-01T00:00:00Z",
        "lower_bound_basis": "loose-object-mtime-plus-prune-expire",
        "gc_auto_threshold": 27,
        "loose_count_at_loss": 12,
        "gc_headroom_at_loss": 15,
        "status": "pending",
        "resolved_at": None,
        "rescue_ref": None,
        "resolution_note": None,
        "object_retention_provided": retained,
    }


def test_p01_empty_closure_is_complete_rc0(tmp_path: Path):
    repo = _init_repo(tmp_path)
    _git(repo, "branch", "topic", "main")
    rc, payload, process = _run_tool(repo, "--branch", "topic")
    assert rc == 0, process.stdout + process.stderr
    assert payload["root_snapshot"]["stable"] is True
    assert payload["deletion_loss_closure"]["complete"] is True
    assert payload["deletion_loss_closure"]["commit_count"] == 0
    assert payload["decision_inputs"]["visualization_complete"] is True


def test_p02_real_checker_landed_and_loose_deadline_is_rc0(tmp_path: Path):
    repo = _init_repo(tmp_path)
    topic = _topic_with_file(repo, content="same state\n")
    _write(repo, "topic.txt", "same state\n")
    _commit(repo, "same state on main")
    object_path = repo / ".git" / "objects" / topic[:2] / topic[2:]
    mtime = dt.datetime(2030, 1, 14, tzinfo=dt.timezone.utc).timestamp()
    os.utime(object_path, (mtime, mtime))

    rc, payload, process = _run_tool(
        repo, "--branch", "topic", "--now", "2030-01-15T00:00:00Z",
    )
    assert rc == 0, process.stdout + process.stderr
    row = _commit_row(payload, topic)
    assert row["landed_assessment"]["verdict"] == "landed"
    assert row["landed_assessment"]["complete"] is True
    assert row["retention"]["storage_kind"] == "loose"
    assert row["retention"]["deadline_status"] == "determinate"
    assert row["retention"]["loss_possible_not_before"] > payload["generated_at"]
    assert str(LANDED_PATH) not in process.stderr


def test_p03_real_checker_not_landed_is_still_rc0(tmp_path: Path):
    repo = _init_repo(tmp_path)
    topic = _topic_with_file(repo, content="unique state\n")
    rc, payload, process = _run_tool(repo, "--branch", "topic")
    assert rc == 0, process.stdout + process.stderr
    row = _commit_row(payload, topic)
    assert row["landed_assessment"]["verdict"] == "not-landed"
    assert payload["decision_inputs"]["not_landed"] == 1
    assert payload["decision_inputs"]["visualization_complete"] is True


def test_p04_missing_ledger_and_real_audit_zero_is_rc0(tmp_path: Path):
    repo = _init_repo(tmp_path)
    outside = tmp_path / "offrepo"
    outside.mkdir()
    rc, payload, process = _run_tool(
        repo, "--ledger-check",
        env={"IZANAGI_DEV_WAVE_JOBS_DIR": str(outside)},
    )
    assert rc == 0, process.stdout + process.stderr
    assert payload["ledger"]["file_present"] is False
    assert payload["ledger"]["entry_count"] == 0
    assert payload["ledger"]["audit"]["reported_commit_count"] == 0
    assert payload["ledger"]["unledgered_commits"] == []


def test_m01_surviving_reflog_is_time_limited_not_negative_root(tmp_path: Path):
    repo = _init_repo(tmp_path)
    main = _git(repo, "rev-parse", "main").stdout.strip()
    topic = _empty_child(repo, main)
    _git(repo, "branch", "topic", topic)
    _git(repo, "branch", "keeper", topic)
    _git(repo, "branch", "-f", "keeper", main)
    checker = _make_fake_landed(tmp_path / "landed.py")

    rc, payload, process = _run_tool(
        repo, "--branch", "topic", "--landed-checker", str(checker),
        "--now", "2030-01-15T00:00:00Z",
    )
    assert rc == 0, process.stdout + process.stderr
    assert topic in _closure_oids(payload)
    temporary = [
        root for root in payload["root_snapshot"]["roots"]
        if root["classification"] == "time-limited" and root["oid"] == topic
    ]
    assert temporary
    assert topic not in payload["deletion_loss_closure"]["stdin_negative_oids"]
    assert _commit_row(payload, topic)["retention"]["additional_sources"]


def test_m02_nonretired_detached_worktree_head_is_permanent_root(tmp_path: Path):
    repo = _init_repo(tmp_path)
    topic = _topic_with_file(repo)
    detached = tmp_path / "detached"
    _git(repo, "worktree", "add", "--detach", str(detached), topic)

    rc, payload, process = _run_tool(repo, "--branch", "topic")
    assert rc == 0, process.stdout + process.stderr
    assert payload["deletion_loss_closure"]["commit_count"] == 0
    roots = [
        root for root in payload["root_snapshot"]["roots"]
        if root["kind"] == "worktree-head" and root["worktree"] == str(detached)
    ]
    assert roots == [{
        "kind": "worktree-head", "name": str(detached), "oid": topic,
        "worktree": str(detached), "reflog_timestamp": None,
        "classification": "permanent", "loss_possible_not_before": None,
        "expiry_setting": None, "expiry_source": None,
        "deadline_status": "not-applicable",
    }]


def test_m03_candidate_reflog_is_not_a_post_cleanup_root(tmp_path: Path):
    repo = _init_repo(tmp_path)
    topic = _empty_child(repo)
    _git(repo, "branch", "topic", topic)
    checker = _make_fake_landed(tmp_path / "landed.py")

    rc, payload, process = _run_tool(
        repo, "--branch", "topic", "--landed-checker", str(checker),
    )
    assert rc == 0, process.stdout + process.stderr
    assert topic in _closure_oids(payload)
    excluded = [item for item in payload["root_snapshot"]["excluded"]
                if item["kind"] == "candidate-reflog"]
    assert excluded and excluded[0]["name"] == "refs/heads/topic"
    assert topic not in payload["deletion_loss_closure"]["stdin_negative_oids"]


def test_m04_remote_ref_is_in_full_refs_namespace_root_set(tmp_path: Path):
    repo = _init_repo(tmp_path)
    topic = _topic_with_file(repo)
    _git(repo, "remote", "add", "origin", ".")
    _git(repo, "fetch", "origin", "refs/heads/topic:refs/remotes/origin/keep")

    rc, payload, process = _run_tool(repo, "--branch", "topic")
    assert rc == 0, process.stdout + process.stderr
    assert payload["deletion_loss_closure"]["commit_count"] == 0
    assert any(root["kind"] == "ref" and root["name"] == "refs/remotes/origin/keep"
               and root["oid"] == topic for root in payload["root_snapshot"]["roots"])


def test_m05_all_candidates_are_subtracted_in_one_closure(tmp_path: Path):
    repo = _init_repo(tmp_path)
    shared = _empty_child(repo)
    _git(repo, "branch", "topic-a", shared)
    _git(repo, "branch", "topic-b", shared)
    checker = _make_fake_landed(tmp_path / "landed.py")

    one_a = _run_tool(repo, "--branch", "topic-a", "--landed-checker", str(checker))[1]
    one_b = _run_tool(repo, "--branch", "topic-b", "--landed-checker", str(checker))[1]
    rc, combined, process = _run_tool(
        repo, "--branch", "topic-a", "--branch", "topic-b",
        "--landed-checker", str(checker),
    )
    assert one_a["deletion_loss_closure"]["commit_count"] == 0
    assert one_b["deletion_loss_closure"]["commit_count"] == 0
    assert rc == 0, process.stdout + process.stderr
    assert combined["deletion_loss_closure"]["commit_count"] == 1
    assert _closure_oids(combined) == [shared]
    assert combined["deletion_loss_closure"]["stdin_positive_oids"] == [shared]


def test_m06_rev_list_stdin_uses_caret_oids_and_never_not_line(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
):
    repo = _init_repo(tmp_path)
    topic = _empty_child(repo)
    _git(repo, "branch", "topic", topic)
    checker = _make_fake_landed(tmp_path / "landed.py")
    parser = TOOL._parser()
    args = parser.parse_args([
        "--repo", str(repo), "--branch", "topic",
        "--landed-checker", str(checker),
    ])
    TOOL._validate_cli(parser, args)
    original = TOOL.Git.run
    closure_stdin: list[str] = []

    def recording(git: Any, command: Any, **kwargs: Any):
        if command[0] == "rev-list" and "--stdin" in command and "--parents" in command:
            closure_stdin.extend(kwargs["input_data"].decode("ascii").splitlines())
        return original(git, command, **kwargs)

    monkeypatch.setattr(TOOL.Git, "run", recording)
    rc, payload = TOOL.assess(args)
    assert rc == 0, payload["issues"]
    assert topic in closure_stdin
    assert any(line.startswith("^") for line in closure_stdin)
    assert "--not" not in closure_stdin


def test_m07_indeterminate_assessment_forces_rc2(tmp_path: Path):
    repo = _init_repo(tmp_path)
    _topic_with_file(repo)
    checker = _make_fake_landed(tmp_path / "indeterminate.py", "indeterminate")
    rc, payload, _ = _run_tool(
        repo, "--branch", "topic", "--landed-checker", str(checker),
    )
    assert rc == 2
    assert payload["decision_inputs"]["indeterminate"] == 1
    assert payload["decision_inputs"]["visualization_complete"] is False


def test_m08_not_landed_is_content_not_technical_failure(tmp_path: Path):
    repo = _init_repo(tmp_path)
    _topic_with_file(repo)
    checker = _make_fake_landed(tmp_path / "not-landed.py", "not-landed")
    rc, payload, process = _run_tool(
        repo, "--branch", "topic", "--landed-checker", str(checker),
    )
    assert rc == 0, process.stdout + process.stderr
    assert payload["decision_inputs"]["not_landed"] == 1
    assert payload["decision_inputs"]["visualization_complete"] is True


def test_m09_loose_deadline_uses_object_mtime_not_now(tmp_path: Path):
    repo = _init_repo(tmp_path)
    topic = _empty_child(repo)
    _git(repo, "branch", "topic", topic)
    object_path = repo / ".git" / "objects" / topic[:2] / topic[2:]
    mtime = dt.datetime(2030, 1, 14, tzinfo=dt.timezone.utc).timestamp()
    os.utime(object_path, (mtime, mtime))
    checker = _make_fake_landed(tmp_path / "landed.py")

    rc, payload, process = _run_tool(
        repo, "--branch", "topic", "--landed-checker", str(checker),
        "--now", "2030-01-15T00:00:00Z",
    )
    assert rc == 0, process.stdout + process.stderr
    retention = _commit_row(payload, topic)["retention"]
    assert retention["loose_mtime"] == "2030-01-14T00:00:00Z"
    assert retention["loss_possible_not_before"] == "2030-01-28T00:00:00Z"
    assert retention["loss_possible_not_before"] != "2030-01-29T00:00:00Z"


def test_m10_m11_packed_mtime_never_becomes_determinate_deadline(tmp_path: Path):
    repo = _init_repo(tmp_path)
    topic = _empty_child(repo)
    _git(repo, "branch", "topic", topic)
    _git(repo, "repack", "-a", "-d")
    loose = repo / ".git" / "objects" / topic[:2] / topic[2:]
    assert not loose.exists()
    for pack in (repo / ".git" / "objects" / "pack").glob("*.pack"):
        os.utime(pack, (946684800, 946684800))
    checker = _make_fake_landed(tmp_path / "landed.py")

    rc, payload, _ = _run_tool(
        repo, "--branch", "topic", "--landed-checker", str(checker),
        "--now", "2030-01-15T00:00:00Z",
    )
    assert rc == 2
    retention = _commit_row(payload, topic)["retention"]
    assert retention["storage_kind"] == "packed"
    assert retention["pack_mtime_observed"] == "2000-01-01T00:00:00Z"
    assert retention["loss_possible_not_before"] == "2030-01-15T00:00:00Z"
    assert retention["lower_bound_basis"] == "assessment-time-conservative-floor"
    assert retention["deadline_status"] == "indeterminate"


def test_m12_gc_auto_uses_fanout_sample_not_total_count(tmp_path: Path):
    repo = _init_repo(tmp_path)
    _git(repo, "branch", "topic", "main")
    sample = repo / ".git" / "objects" / "17"
    sample.mkdir(exist_ok=True)
    for index in range(27):
        (sample / f"{index:038x}").write_bytes(b"fixture")

    rc, payload, process = _run_tool(repo, "--branch", "topic")
    assert rc == 0, process.stdout + process.stderr
    auto = payload["gc"]["auto_trigger"]
    assert auto["version_matches"] is True
    assert auto["sample_entry_count"] >= 27
    assert auto["threshold"] == 27
    assert auto["total_loose_count_observation"] < 6700
    assert auto["proximity"] == "at-or-above"
    assert auto["next_eligible_git_command_may_trigger"] is True


def test_m13_closure_limit_keeps_the_over_limit_observation(tmp_path: Path):
    repo = _init_repo(tmp_path)
    _git(repo, "switch", "-c", "topic")
    _write(repo, "one", "1\n")
    first = _commit(repo, "one")
    _write(repo, "two", "2\n")
    second = _commit(repo, "two")
    _git(repo, "switch", "main")
    checker = _make_fake_landed(tmp_path / "landed.py")

    rc, payload, _ = _run_tool(
        repo, "--branch", "topic", "--max-deletion-loss-commits", "1",
        "--landed-checker", str(checker),
    )
    assert rc == 2
    closure = payload["deletion_loss_closure"]
    assert closure["complete"] is False
    assert closure["commit_count"] is None
    assert closure["observed_commit_count"] == 2
    assert _closure_oids(payload) == [first, second]
    assert all("landed_assessment" in item and "retention" in item
               for item in closure["commits"])


def test_m14_unledgered_audit_finding_returns_rc3(tmp_path: Path):
    repo = _init_repo(tmp_path)
    oid = _git(repo, "rev-parse", "main").stdout.strip()
    audit = _make_fake_audit(tmp_path / "audit.py", [oid])

    rc, payload, process = _run_tool(
        repo, "--ledger-check", "--audit-tool", str(audit),
        "--now", "2030-01-15T00:00:00Z",
    )
    assert rc == 3, process.stdout + process.stderr
    assert payload["ledger"]["unledgered_commits"] == [oid]
    assert payload["ledger"]["notifications"] == [{
        "kind": "unledgered-audit-finding", "object_oid": oid,
        "entry_id": None, "urgency": "due",
        "message": "audit reported an unreachable commit with no ledger entry",
    }]


def test_m15_retention_claim_is_fixed_false_and_true_entry_is_rejected(tmp_path: Path):
    repo = _init_repo(tmp_path)
    oid = _git(repo, "rev-parse", "main").stdout.strip()
    audit = _make_fake_audit(tmp_path / "audit.py", [])
    ledger = repo / "docs" / "unreachable-object-ledger.md"
    ledger.parent.mkdir()
    ledger.write_text("# Ledger\n\n- " + json.dumps(_ledger_entry(oid)) + "\n", encoding="utf-8")

    rc, payload, process = _run_tool(
        repo, "--ledger-check", "--audit-tool", str(audit),
        "--now", "2030-01-15T00:00:00Z",
    )
    assert rc == 0, process.stdout + process.stderr
    assert _all_key_values(payload, "object_retention_provided")
    assert set(_all_key_values(payload, "object_retention_provided")) == {False}
    assert not _all_key_values(payload, "deletion_authorized")

    ledger.write_text("# Ledger\n\n- " + json.dumps(_ledger_entry(oid, retained=True)) + "\n",
                      encoding="utf-8")
    invalid_rc, invalid, _ = _run_tool(
        repo, "--ledger-check", "--audit-tool", str(audit),
        "--now", "2030-01-15T00:00:00Z",
    )
    assert invalid_rc == 2
    assert any(issue["code"] == "ledger-entry-retention-claim-invalid"
               for issue in invalid["issues"])


def test_m16_git_allowlist_rejects_forbidden_command_before_spawn(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
):
    repo = _init_repo(tmp_path)
    _git(repo, "branch", "topic", "main")
    parser = TOOL._parser()
    args = parser.parse_args(["--repo", str(repo), "--branch", "topic"])
    TOOL._validate_cli(parser, args)
    real_spawn = TOOL.subprocess.run
    spawned: list[list[str]] = []

    def recording_spawn(argv: Any, *positional: Any, **kwargs: Any):
        spawned.append(list(argv))
        return real_spawn(argv, *positional, **kwargs)

    monkeypatch.setattr(TOOL.subprocess, "run", recording_spawn)
    rc, payload = TOOL.assess(args)
    assert rc == 0, payload["issues"]
    assert spawned
    assert all(argv[0] == "git" for argv in spawned)
    observed_commands = {
        next(token for token in argv[1:] if token in TOOL.GIT_COMMAND_ALLOWLIST)
        for argv in spawned
    }
    assert observed_commands <= TOOL.GIT_COMMAND_ALLOWLIST
    assert not {"gc", "prune", "update-ref", "checkout", "reset"} & observed_commands

    runner = TOOL.Git(repo, __import__("time").monotonic() + 10)
    called = False

    def forbidden_spawn(*_args: Any, **_kwargs: Any):
        nonlocal called
        called = True
        raise AssertionError("subprocess must not be reached")

    monkeypatch.setattr(TOOL.subprocess, "run", forbidden_spawn)
    with pytest.raises(TOOL.RescueError, match="not allowed"):
        runner.run(["gc"])
    assert called is False
    assert "gc" not in TOOL.GIT_COMMAND_ALLOWLIST


def test_m17_root_digest_movement_forces_rc2(tmp_path: Path):
    repo = _init_repo(tmp_path)
    _topic_with_file(repo)
    checker = _make_fake_landed(tmp_path / "moving.py", mutate=True)

    rc, payload, _ = _run_tool(
        repo, "--branch", "topic", "--landed-checker", str(checker),
    )
    assert rc == 2
    snapshot = payload["root_snapshot"]
    assert snapshot["start_digest"] != snapshot["end_digest"]
    assert snapshot["stable"] is False
    assert any(issue["code"] == "root-snapshot-moved" for issue in payload["issues"])


def test_retiring_one_of_two_same_detached_heads_keeps_the_other_root(tmp_path: Path):
    repo = _init_repo(tmp_path)
    topic = _topic_with_file(repo)
    one = tmp_path / "one"
    two = tmp_path / "two"
    _git(repo, "worktree", "add", "--detach", str(one), topic)
    _git(repo, "worktree", "add", "--detach", str(two), topic)

    rc, payload, process = _run_tool(
        repo, "--branch", "topic", "--retire-worktree", str(one),
    )
    assert rc == 0, process.stdout + process.stderr
    assert payload["deletion_loss_closure"]["commit_count"] == 0
    assert topic in payload["deletion_loss_closure"]["stdin_negative_oids"]
    rows = {row["path"]: row for row in payload["root_snapshot"]["worktrees"]}
    assert rows[str(one)]["retired"] is True
    assert rows[str(two)]["retired"] is False


def test_surviving_index_commit_is_root_but_blob_is_not_commit_root(tmp_path: Path):
    repo = _init_repo(tmp_path)
    topic = _empty_child(repo)
    _git(repo, "branch", "topic", topic)
    _git(repo, "update-index", "--add", "--cacheinfo", "160000", topic, "gitlink")

    rc, payload, process = _run_tool(repo, "--branch", "topic")
    assert rc == 0, process.stdout + process.stderr
    assert payload["deletion_loss_closure"]["commit_count"] == 0
    indexes = payload["root_snapshot"]["indexes"]
    assert indexes["object_count"] >= 2
    assert indexes["commit_root_count"] == 1
    roots = [root for root in payload["root_snapshot"]["roots"]
             if root["kind"] == "index-commit"]
    assert [root["oid"] for root in roots] == [topic]
    assert topic in payload["deletion_loss_closure"]["stdin_negative_oids"]


def test_prunable_worktree_roots_are_time_limited_not_negative(tmp_path: Path):
    repo = _init_repo(tmp_path)
    topic = _topic_with_file(repo)
    original = tmp_path / "prunable"
    moved = tmp_path / "moved-aside"
    _git(repo, "worktree", "add", "--detach", str(original), topic)
    original.rename(moved)
    assert "prunable" in _git(repo, "worktree", "list", "--porcelain").stdout
    checker = _make_fake_landed(tmp_path / "landed.py")

    rc, payload, process = _run_tool(
        repo, "--branch", "topic", "--landed-checker", str(checker),
        "--now", "2030-01-15T00:00:00Z",
    )
    assert rc == 0, process.stdout + process.stderr
    assert topic in _closure_oids(payload)
    roots = [root for root in payload["root_snapshot"]["roots"]
             if root["worktree"] == str(original) and root["oid"] == topic]
    assert roots
    assert {root["classification"] for root in roots} == {"time-limited"}
    assert all(root["expiry_setting"] == "gc.worktreePruneExpire" for root in roots)
    assert topic not in payload["deletion_loss_closure"]["stdin_negative_oids"]


def test_private_ref_presence_is_reported_and_never_used_as_negative_root(tmp_path: Path):
    repo = _init_repo(tmp_path)
    _git(repo, "branch", "topic", "main")
    main = _git(repo, "rev-parse", "main").stdout.strip()
    private = repo / ".git" / "refs" / "worktree" / "fixture"
    private.parent.mkdir(parents=True)
    private.write_text(main + "\n", encoding="ascii")

    rc, payload, _ = _run_tool(repo, "--branch", "topic")
    assert rc == 2
    assert any(issue["code"] == "private-ref-present" for issue in payload["issues"])
    assert not any(root["name"] == "refs/worktree/fixture"
                   for root in payload["root_snapshot"]["roots"])


def test_alternate_only_commit_has_indeterminate_external_retention(tmp_path: Path):
    source = _init_repo(tmp_path / "source")
    external = _topic_with_file(source, "external", "external\n")
    repo = _init_repo(tmp_path / "target")
    alternates = repo / ".git" / "objects" / "info" / "alternates"
    alternates.parent.mkdir(parents=True, exist_ok=True)
    alternates.write_text(str(source / ".git" / "objects") + "\n", encoding="utf-8")
    _git(repo, "branch", "topic", external)
    checker = _make_fake_landed(tmp_path / "landed.py")

    rc, payload, _ = _run_tool(
        repo, "--branch", "topic", "--landed-checker", str(checker),
        "--now", "2030-01-15T00:00:00Z",
    )
    assert rc == 2
    retention = _commit_row(payload, external)["retention"]
    assert retention["storage_kind"] == "alternate"
    assert retention["deadline_status"] == "indeterminate"
    assert retention["loss_possible_not_before"] == "2030-01-15T00:00:00Z"
    assert payload["root_snapshot"]["alternates"]["alternate_refs_used_as_roots"] is False


def test_normal_preview_preserves_repository_control_bytes(tmp_path: Path):
    repo = _init_repo(tmp_path)
    _git(repo, "branch", "topic", "main")

    def control_bytes() -> dict[str, bytes]:
        paths = [repo / ".git" / "index"]
        for relative in ("refs", "logs", "objects"):
            root = repo / ".git" / relative
            paths.extend(path for path in root.rglob("*") if path.is_file())
        return {str(path.relative_to(repo)): path.read_bytes() for path in paths}

    before = control_bytes()
    rc, payload, process = _run_tool(repo, "--branch", "topic")
    after = control_bytes()
    assert rc == 0, process.stdout + process.stderr
    assert after == before
    assert payload["root_snapshot"]["stable"] is True


def test_assessment_limit_marks_every_unrun_commit(tmp_path: Path):
    repo = _init_repo(tmp_path)
    _git(repo, "switch", "-c", "topic")
    for index in range(3):
        _write(repo, f"f{index}", f"{index}\n")
        _commit(repo, f"commit {index}")
    _git(repo, "switch", "main")
    checker = _make_fake_landed(tmp_path / "landed.py")

    rc, payload, _ = _run_tool(
        repo, "--branch", "topic", "--max-assessments", "1",
        "--landed-checker", str(checker),
    )
    assert rc == 2
    commits = payload["deletion_loss_closure"]["commits"]
    assert len(commits) == 3
    assert commits[0]["landed_assessment"]["complete"] is True
    assert [item["landed_assessment"]["reason"] for item in commits[1:]] == [
        "assessment-limit-exceeded", "assessment-limit-exceeded",
    ]


def test_usage_rc64_and_fixed_coverage_boundary(tmp_path: Path):
    repo = _init_repo(tmp_path)
    missing = subprocess.run(
        [sys.executable, str(TOOL_PATH), "--repo", str(repo)], cwd=ROOT,
        text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False,
    )
    assert missing.returncode == 64
    assert missing.stdout == ""
    relative = subprocess.run(
        [sys.executable, str(TOOL_PATH), "--repo", str(repo),
         "--retire-worktree", "relative"], cwd=ROOT,
        text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False,
    )
    assert relative.returncode == 64
    assert relative.stdout == ""

    _git(repo, "branch", "topic", "main")
    rc, payload, _ = _run_tool(repo, "--branch", "topic")
    assert rc == 0
    assert payload["coverage_boundary"]["does_not_cover"] == [
        "manual git branch -d",
        "DW-O28 automatic retirement",
        "D978 unenacted deletion paths",
    ]
    assert not _all_key_values(payload, "deletion_authorized")


if __name__ == "__main__":
    raise SystemExit(pytest.main(["-q", __file__]))
