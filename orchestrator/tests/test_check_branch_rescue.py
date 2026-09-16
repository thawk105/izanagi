from __future__ import annotations

import datetime as dt
import importlib.util
import json
import os
from pathlib import Path
import shlex
import subprocess
import sys
from typing import Any
from unittest import mock

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


def _make_fake_landed(
    path: Path,
    verdict: Any = "landed",
    *,
    mutate: bool = False,
    target_binding: str = "matching",
    conclusive: bool | None = None,
    checker_rc: int | None = None,
) -> Path:
    if checker_rc is None:
        rc = (
            {"landed": 0, "not-landed": 1, "indeterminate": 2}.get(verdict, 0)
            if isinstance(verdict, str)
            else 0
        )
    else:
        rc = checker_rc
    decision_conclusive = verdict != "indeterminate" if conclusive is None else conclusive
    reason = f"fake-{verdict}"
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
    "decision": {{"verdict": {verdict!r}, "reason": {reason!r},
                   "conclusive": {decision_conclusive!r}}},
    "observations": {{"ledger_corpus": {{"bytes_read": 0}}}},
}}
oid = sys.argv[-1]
other_oid = ("0" if oid[0] != "0" else "1") * len(oid)
target_binding = {target_binding!r}
if target_binding == "matching":
    payload["branch"] = {{"input": oid, "tip": oid}}
elif target_binding == "missing-input":
    payload["branch"] = {{"tip": oid}}
elif target_binding == "missing-tip":
    payload["branch"] = {{"input": oid}}
elif target_binding == "different-input":
    payload["branch"] = {{"input": other_oid, "tip": oid}}
elif target_binding == "different-tip":
    payload["branch"] = {{"input": oid, "tip": other_oid}}
elif target_binding != "missing-branch":
    raise AssertionError("unknown target binding fixture")
print(json.dumps(payload, sort_keys=True))
raise SystemExit({rc})
"""
    path.write_text(body, encoding="utf-8")
    return path


def _make_fake_audit(path: Path, commits: list[str]) -> Path:
    rows = "".join(f"  commit {oid} (fixture)\n" for oid in commits)
    body = f"""#!/usr/bin/env python3
print("audit_dangling_commits: 要確認の到達不能変更 {len(commits)} commit")
print({rows!r}, end="")
print("audit_dangling_commits: elapsed_seconds=0.001")
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
    del timeout
    cli: list[str] = ["--repo", str(repo)]
    now: dt.datetime | None = None
    landed_checker = TOOL.LANDED_CHECKER_PATH
    audit_tool = TOOL.AUDIT_TOOL_PATH
    index = 0
    while index < len(extra):
        if extra[index] == "--now":
            now = TOOL._parse_now(extra[index + 1])
            index += 2
        elif extra[index] == "--landed-checker":
            landed_checker = Path(extra[index + 1])
            index += 2
        elif extra[index] == "--audit-tool":
            audit_tool = Path(extra[index + 1])
            index += 2
        else:
            cli.append(extra[index])
            index += 1
    parser = TOOL._parser()
    args = parser.parse_args(cli)
    with mock.patch.dict(os.environ, env or {}, clear=False):
        TOOL._validate_cli(parser, args)
        rc, payload = TOOL.assess(
            args, assessment_time=now,
            landed_checker=landed_checker, audit_tool=audit_tool,
        )
    stdout = json.dumps(payload, ensure_ascii=True, sort_keys=True, separators=(",", ":")) + "\n"
    result = subprocess.CompletedProcess(
        [sys.executable, str(TOOL_PATH), *cli], rc, stdout=stdout, stderr="",
    )
    assert payload["schema"] == "izanagi-branch-rescue-v1"
    return rc, payload, result


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


def _repository_control_bytes(repo: Path) -> dict[str, bytes]:
    git_dir = repo / ".git"
    return {
        str(path.relative_to(repo)): path.read_bytes()
        for path in git_dir.rglob("*") if path.is_file()
    }


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
        "gc_auto_threshold": 6700,
        "gc_auto_sample_fanout": "17",
        "gc_auto_sample_count": 12,
        "gc_auto_sample_threshold": 27,
        "gc_auto_heuristic_version": "git-2.34.1-fanout-17-sample",
        "loose_count_at_loss": 12,
        "status": "pending",
        "resolved_at": None,
        "rescue_ref": None,
        "resolution_note": None,
        "object_retention_provided": retained,
    }


def _resolved_ledger_entry(oid: str, status: str, entry_id: str) -> dict[str, Any]:
    entry = _ledger_entry(oid)
    entry.update({
        "entry_id": entry_id,
        "status": status,
        "resolved_at": "2030-01-10T00:00:00Z",
        "rescue_ref": f"refs/heads/rescue/{entry_id}" if status == "rescued" else None,
        "resolution_note": f"resolved as {status}",
    })
    return entry


def _reflog_config(ordinary: str, unreachable: str) -> dict[str, dict[str, Any]]:
    return {
        "gc_reflog_expire": {
            "effective": ordinary,
            "source": "global-ordinary",
        },
        "gc_reflog_expire_unreachable": {
            "effective": unreachable,
            "source": "global-unreachable",
        },
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


def test_m03_m18_p06_candidate_reflog_only_commit_is_a_positive_root(tmp_path: Path):
    repo = _init_repo(tmp_path)
    topic = _empty_child(repo)
    _git(repo, "branch", "topic", topic)
    _git(repo, "branch", "-f", "topic", "main")
    checker = _make_fake_landed(tmp_path / "landed.py")

    rc, payload, process = _run_tool(
        repo, "--branch", "topic", "--landed-checker", str(checker),
    )
    assert rc == 0, process.stdout + process.stderr
    assert topic in _closure_oids(payload)
    excluded = [item for item in payload["root_snapshot"]["excluded"]
                if item["kind"] == "candidate-reflog"]
    assert excluded and excluded[0]["name"] == "refs/heads/topic"
    assert topic in payload["deletion_loss_closure"]["stdin_positive_oids"]
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
    ])
    TOOL._validate_cli(parser, args)
    original = TOOL.Git.run
    closure_stdin: list[str] = []

    def recording(git: Any, command: Any, **kwargs: Any):
        if command[0] == "rev-list" and "--stdin" in command and "--parents" in command:
            closure_stdin.extend(kwargs["input_data"].decode("ascii").splitlines())
        return original(git, command, **kwargs)

    monkeypatch.setattr(TOOL.Git, "run", recording)
    rc, payload = TOOL.assess(args, landed_checker=checker)
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


@pytest.mark.parametrize(
    "target_binding",
    [
        "missing-branch",
        "missing-input",
        "missing-tip",
        "different-input",
        "different-tip",
    ],
)
def test_landed_checker_report_is_bound_to_requested_full_oid(
    tmp_path: Path, target_binding: str,
):
    repo = _init_repo(tmp_path)
    oid = _git(repo, "rev-parse", "main").stdout.strip()
    checker = _make_fake_landed(
        tmp_path / "landed.py", target_binding=target_binding,
    )

    assessment = TOOL._landed_assessment(repo, checker, oid, 5.0, 5.0)

    assert assessment["verdict"] == "indeterminate"
    assert assessment["reason"] == "checker-target-contract-invalid"
    assert assessment["conclusive"] is False
    assert assessment["complete"] is False


@pytest.mark.parametrize(
    ("verdict", "conclusive"),
    [
        ("landed", False),
        ("not-landed", False),
        ("indeterminate", True),
    ],
)
def test_landed_checker_report_rejects_conclusive_mismatch(
    tmp_path: Path, verdict: str, conclusive: bool,
):
    repo = _init_repo(tmp_path)
    oid = _git(repo, "rev-parse", "main").stdout.strip()
    checker = _make_fake_landed(
        tmp_path / "landed.py", verdict, conclusive=conclusive,
    )

    assessment = TOOL._landed_assessment(repo, checker, oid, 5.0, 5.0)

    assert assessment["verdict"] == "indeterminate"
    assert assessment["reason"] == "checker-conclusive-contract-invalid"
    assert assessment["conclusive"] is False
    assert assessment["complete"] is False


@pytest.mark.parametrize(
    "verdict",
    [
        pytest.param(["landed"], id="array"),
        pytest.param({"verdict": "landed"}, id="object"),
        pytest.param(True, id="bool"),
        pytest.param(None, id="null"),
        pytest.param(0, id="number"),
    ],
)
def test_landed_checker_report_rejects_non_string_verdict(
    tmp_path: Path, verdict: Any,
):
    repo = _init_repo(tmp_path)
    oid = _git(repo, "rev-parse", "main").stdout.strip()
    checker = _make_fake_landed(
        tmp_path / "landed.py", verdict, checker_rc=0,
    )

    assessment = TOOL._landed_assessment(repo, checker, oid, 5.0, 5.0)

    assert assessment["verdict"] == "indeterminate"
    assert assessment["reason"] == "checker-rc-verdict-mismatch"
    assert assessment["conclusive"] is False
    assert assessment["complete"] is False


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


@pytest.mark.parametrize(
    ("ordinary", "unreachable", "expected_deadline", "expected_setting"),
    [
        ("5.days.ago", "30.days.ago", "2030-01-06T00:00:00Z", "gc.reflogExpire"),
        (
            "90.days.ago",
            "4.days.ago",
            "2030-01-05T00:00:00Z",
            "gc.reflogExpireUnreachable",
        ),
        ("never", "6.days.ago", "2030-01-07T00:00:00Z", "gc.reflogExpireUnreachable"),
        ("6.days.ago", "never", "2030-01-07T00:00:00Z", "gc.reflogExpire"),
        ("never", "never", "9999-12-31T23:59:59Z", "gc.reflogExpire=never"),
    ],
)
def test_reflog_expiry_uses_both_global_candidates_and_never(
    ordinary: str,
    unreachable: str,
    expected_deadline: str,
    expected_setting: str,
):
    timestamp = dt.datetime(2030, 1, 1, tzinfo=dt.timezone.utc)
    deadline, setting, _source, status = TOOL._reflog_expiry(
        "refs/heads/topic",
        timestamp,
        timestamp,
        _reflog_config(ordinary, unreachable),
        [],
    )

    assert deadline == expected_deadline
    assert setting == expected_setting
    assert status == "determinate"


@pytest.mark.parametrize(
    ("refname", "scoped_ordinary", "scoped_unreachable", "expected_deadline", "expected_setting"),
    [
        (
            "refs/heads/topic",
            "3.days.ago",
            "8.days.ago",
            "2030-01-04T00:00:00Z",
            "gc.refs/heads/*.reflogExpire",
        ),
        (
            "refs/heads/topic",
            "never",
            "8.days.ago",
            "2030-01-09T00:00:00Z",
            "gc.refs/heads/*.reflogExpireUnreachable",
        ),
        (
            "refs/heads/topic",
            "3.days.ago",
            "never",
            "2030-01-04T00:00:00Z",
            "gc.refs/heads/*.reflogExpire",
        ),
        (
            "refs/heads/topic",
            "never",
            "never",
            "9999-12-31T23:59:59Z",
            "gc.reflogExpire=never",
        ),
        (
            "refs/tags/topic",
            "1.days.ago",
            "2.days.ago",
            "2030-01-31T00:00:00Z",
            "gc.reflogExpireUnreachable",
        ),
    ],
)
def test_reflog_expiry_applies_scoped_candidates_only_to_matching_refs(
    refname: str,
    scoped_ordinary: str,
    scoped_unreachable: str,
    expected_deadline: str,
    expected_setting: str,
):
    timestamp = dt.datetime(2030, 1, 1, tzinfo=dt.timezone.utc)
    scoped = [
        {
            "source": "scoped-ordinary",
            "pattern": "refs/heads/*",
            "setting": "ordinary",
            "effective": scoped_ordinary,
        },
        {
            "source": "scoped-unreachable",
            "pattern": "refs/heads/*",
            "setting": "unreachable",
            "effective": scoped_unreachable,
        },
    ]
    deadline, setting, _source, status = TOOL._reflog_expiry(
        refname,
        timestamp,
        timestamp,
        _reflog_config("90.days.ago", "30.days.ago"),
        scoped,
    )

    assert deadline == expected_deadline
    assert setting == expected_setting
    assert status == "determinate"


def test_scoped_reflog_config_reads_ordinary_and_unreachable(tmp_path: Path):
    repo = _init_repo(tmp_path)
    _git(repo, "config", "gc.refs/heads/*.reflogExpire", "2.days.ago")
    _git(repo, "config", "gc.refs/heads/*.reflogExpireUnreachable", "7.days.ago")
    git = TOOL.Git(repo, TOOL.time.monotonic() + 10.0)

    with mock.patch.dict(os.environ, {
        "GIT_CONFIG_GLOBAL": os.devnull,
        "GIT_CONFIG_NOSYSTEM": "1",
    }, clear=False):
        config, scoped = TOOL._config_snapshot(git)
    observed = {
        (item["pattern"], item["setting"], item["effective"])
        for item in scoped
    }
    deadline, setting, _source, status = TOOL._reflog_expiry(
        "refs/heads/topic",
        dt.datetime(2030, 1, 1, tzinfo=dt.timezone.utc),
        dt.datetime(2030, 1, 1, tzinfo=dt.timezone.utc),
        config,
        scoped,
    )

    assert observed == {
        ("refs/heads/*", "ordinary", "2.days.ago"),
        ("refs/heads/*", "unreachable", "7.days.ago"),
    }
    assert deadline == "2030-01-03T00:00:00Z"
    assert setting == "gc.refs/heads/*.reflogExpire"
    assert status == "determinate"


def test_m10_m26_packed_mtime_never_becomes_determinate_deadline(tmp_path: Path):
    repo = _init_repo(tmp_path)
    topic = _empty_child(repo)
    _git(repo, "branch", "topic", topic)
    _git(repo, "repack", "-a", "-d")
    loose = repo / ".git" / "objects" / topic[:2] / topic[2:]
    assert not loose.exists()
    for pack in (repo / ".git" / "objects" / "pack").glob("*.pack"):
        future = dt.datetime(2040, 1, 1, tzinfo=dt.timezone.utc).timestamp()
        os.utime(pack, (future, future))
    checker = _make_fake_landed(tmp_path / "landed.py")

    rc, payload, _ = _run_tool(
        repo, "--branch", "topic", "--landed-checker", str(checker),
        "--now", "2030-01-15T00:00:00Z",
    )
    assert rc == 0
    retention = _commit_row(payload, topic)["retention"]
    assert retention["storage_kind"] == "packed"
    assert retention["pack_mtime_observed"] > payload["generated_at"]
    assert retention["loss_possible_not_before"] == "2030-01-15T00:00:00Z"
    assert retention["lower_bound_basis"] == "assessment-time-conservative-floor"
    assert retention["deadline_status"] == "conservative-floor"


def test_m11_m28_p07_packed_conservative_floor_is_complete_rc0(tmp_path: Path):
    repo = _init_repo(tmp_path)
    topic = _empty_child(repo)
    _git(repo, "branch", "topic", topic)
    _git(repo, "repack", "-a", "-d")
    checker = _make_fake_landed(tmp_path / "landed.py")

    rc, payload, process = _run_tool(
        repo, "--branch", "topic", "--landed-checker", str(checker),
        "--now", "2030-01-15T00:00:00Z",
    )
    assert rc == 0, process.stdout + process.stderr
    retention = _commit_row(payload, topic)["retention"]
    assert retention["deadline_status"] == "conservative-floor"
    assert retention["loss_possible_not_before"] == payload["generated_at"]
    assert payload["decision_inputs"]["visualization_complete"] is True


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


def test_audit_re_report_notifies_stale_resolutions_except_accepted_loss(
    tmp_path: Path,
):
    repo = _init_repo(tmp_path)
    rows = [
        _resolved_ledger_entry("1" * 40, "rescued", "e-rescued"),
        _resolved_ledger_entry("2" * 40, "reachable-again", "e-reachable"),
        _resolved_ledger_entry("3" * 40, "object-missing", "e-missing"),
        _resolved_ledger_entry("4" * 40, "accepted-loss", "e-accepted"),
    ]
    ledger = repo / "docs" / "unreachable-object-ledger.md"
    ledger.parent.mkdir()
    ledger.write_text(
        "# Ledger\n\n" + "".join(f"- {json.dumps(row)}\n" for row in rows),
        encoding="utf-8",
    )
    audit = _make_fake_audit(
        tmp_path / "audit.py", [row["object_oid"] for row in rows],
    )

    rc, payload, process = _run_tool(
        repo,
        "--ledger-check",
        "--audit-tool",
        str(audit),
        "--now",
        "2030-01-15T00:00:00Z",
    )

    assert rc == 3, process.stdout + process.stderr
    assert payload["decision_inputs"]["visualization_complete"] is True
    assert payload["ledger"]["unledgered_commits"] == []
    assert payload["ledger"]["notifications"] == [
        {
            "kind": "stale-ledger-resolution",
            "object_oid": "1" * 40,
            "entry_id": "e-rescued",
            "urgency": "due",
            "status": "rescued",
            "message": (
                "audit re-reported an unreachable commit with a stale ledger resolution"
            ),
        },
        {
            "kind": "stale-ledger-resolution",
            "object_oid": "2" * 40,
            "entry_id": "e-reachable",
            "urgency": "due",
            "status": "reachable-again",
            "message": (
                "audit re-reported an unreachable commit with a stale ledger resolution"
            ),
        },
        {
            "kind": "stale-ledger-resolution",
            "object_oid": "3" * 40,
            "entry_id": "e-missing",
            "urgency": "due",
            "status": "object-missing",
            "message": (
                "audit re-reported an unreachable commit with a stale ledger resolution"
            ),
        },
    ]


def test_m15_m24_retention_and_authorization_claims_are_absent_or_fixed(tmp_path: Path):
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
    assert not _all_key_values(payload, "branch_delete_authorized")

    nonempty_tip = _empty_child(repo)
    _git(repo, "branch", "nonempty-topic", nonempty_tip)
    checker = _make_fake_landed(tmp_path / "landed.py")
    nonempty_rc, nonempty_payload, nonempty_process = _run_tool(
        repo, "--branch", "nonempty-topic", "--landed-checker", str(checker),
    )
    assert nonempty_rc == 0, nonempty_process.stdout + nonempty_process.stderr
    assert nonempty_payload["deletion_loss_closure"]["commit_count"] > 0
    nonempty_branch_claims = _all_key_values(
        nonempty_payload, "branch_delete_authorized",
    )
    nonempty_deletion_claims = _all_key_values(
        nonempty_payload, "deletion_authorized",
    )
    assert not nonempty_branch_claims, (
        "non-empty closure contains branch_delete_authorized values: "
        f"{nonempty_branch_claims!r}"
    )
    assert not nonempty_deletion_claims, (
        "non-empty closure contains deletion_authorized values: "
        f"{nonempty_deletion_claims!r}"
    )

    empty_rc, empty_payload, empty_process = _run_tool(
        repo, "--branch", "missing-topic", "--landed-checker", str(checker),
    )
    assert empty_rc == 2, empty_process.stdout + empty_process.stderr
    assert empty_payload["deletion_loss_closure"]["commit_count"] == 0
    assert any(issue["code"] == "candidate-ref-missing"
               for issue in empty_payload["issues"])
    empty_branch_claims = _all_key_values(
        empty_payload, "branch_delete_authorized",
    )
    empty_deletion_claims = _all_key_values(
        empty_payload, "deletion_authorized",
    )
    assert not empty_branch_claims, (
        "empty closure contains branch_delete_authorized values: "
        f"{empty_branch_claims!r}"
    )
    assert not empty_deletion_claims, (
        "empty closure contains deletion_authorized values: "
        f"{empty_deletion_claims!r}"
    )

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
    _topic_with_file(repo)
    checker = _make_fake_landed(tmp_path / "landed.py")
    audit = _make_fake_audit(tmp_path / "audit.py", [])
    parser = TOOL._parser()
    args = parser.parse_args([
        "--repo", str(repo), "--branch", "topic", "--ledger-check",
    ])
    real_spawn = TOOL.subprocess.run
    spawned: list[list[str]] = []
    child_envs: list[dict[str, str]] = []

    def recording_spawn(argv: Any, *positional: Any, **kwargs: Any):
        spawned.append(list(argv))
        child_envs.append(dict(kwargs["env"]))
        return real_spawn(argv, *positional, **kwargs)

    before = _repository_control_bytes(repo)
    monkeypatch.setattr(TOOL.subprocess, "run", recording_spawn)
    TOOL._validate_cli(parser, args)
    rc, payload = TOOL.assess(
        args, landed_checker=checker, audit_tool=audit,
    )
    after = _repository_control_bytes(repo)
    assert rc == 0, payload["issues"]
    assert spawned
    assert after == before
    assert any(argv[:2] == [sys.executable, str(checker)] for argv in spawned)
    assert any(argv[:2] == [sys.executable, str(audit)] for argv in spawned)
    assert all(env["GIT_NO_LAZY_FETCH"] == "1" for env in child_envs)
    python_child_envs = [
        env for argv, env in zip(spawned, child_envs)
        if argv[0] == sys.executable
    ]
    assert len(python_child_envs) == 2
    assert all(env["PYTHONDONTWRITEBYTECODE"] == "1" for env in python_child_envs)
    git_argv = [argv for argv in spawned if argv[0] == "git"]
    observed_commands = {
        next(token for token in argv[1:] if token in TOOL.GIT_COMMAND_ALLOWLIST)
        for argv in git_argv
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


def test_m21_p08_prunable_worktree_roots_use_conservative_floor(tmp_path: Path):
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
    assert {root["deadline_status"] for root in roots} == {"conservative-floor"}
    assert {root["loss_possible_not_before"] for root in roots} == {
        "2030-01-15T00:00:00Z"
    }
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


def test_m29_p09_alternate_only_commit_has_conservative_external_retention(tmp_path: Path):
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
    assert rc == 0
    retention = _commit_row(payload, external)["retention"]
    assert retention["storage_kind"] == "alternate"
    assert retention["deadline_status"] == "conservative-floor"
    assert retention["loss_possible_not_before"] == "2030-01-15T00:00:00Z"
    assert retention["lower_bound_basis"].startswith("alternate-object-database-")
    assert payload["root_snapshot"]["alternates"]["alternate_refs_used_as_roots"] is False


def test_normal_preview_preserves_repository_control_bytes(tmp_path: Path):
    repo = _init_repo(tmp_path)
    _topic_with_file(repo)
    checker = _make_fake_landed(tmp_path / "landed.py")
    audit = _make_fake_audit(tmp_path / "audit.py", [])

    before = _repository_control_bytes(repo)
    rc, payload, process = _run_tool(
        repo, "--branch", "topic", "--ledger-check",
        "--landed-checker", str(checker), "--audit-tool", str(audit),
    )
    after = _repository_control_bytes(repo)
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


def test_a1_retired_worktree_reflog_only_commit_is_a_positive_root(tmp_path: Path):
    repo = _init_repo(tmp_path)
    topic = _empty_child(repo)
    retired = tmp_path / "retired"
    _git(repo, "worktree", "add", "--detach", str(retired), topic)
    _git(retired, "switch", "--detach", "main")
    checker = _make_fake_landed(tmp_path / "landed.py")

    rc, payload, process = _run_tool(
        repo, "--retire-worktree", str(retired),
        "--landed-checker", str(checker),
    )
    assert rc == 0, process.stdout + process.stderr
    assert topic in _closure_oids(payload)
    assert topic in payload["deletion_loss_closure"]["stdin_positive_oids"]
    assert any(
        item["kind"] == "retired-worktree-reflog" and item["oid"] == topic
        for item in payload["root_snapshot"]["excluded"]
    )


def test_a1_candidate_reflog_parse_failure_is_rc2(tmp_path: Path):
    repo = _init_repo(tmp_path)
    _git(repo, "branch", "topic", "main")
    log = repo / ".git" / "logs" / "refs" / "heads" / "topic"
    log.write_bytes(b"malformed reflog\n")

    rc, payload, _ = _run_tool(repo, "--branch", "topic")
    assert rc == 2
    assert any(issue["code"] == "reflog-parse-error" for issue in payload["issues"])


def test_a1_candidate_reflog_missing_object_is_defined_rc2(tmp_path: Path):
    repo = _init_repo(tmp_path)
    missing_oid = _empty_child(repo)
    _git(repo, "branch", "topic", missing_oid)
    _git(repo, "branch", "-f", "topic", "main")
    object_path = repo / ".git" / "objects" / missing_oid[:2] / missing_oid[2:]
    object_path.unlink()

    rc, payload, _ = _run_tool(repo, "--branch", "topic")
    assert rc == 2
    assert payload["root_snapshot"]["complete"] is False
    assert missing_oid not in payload["deletion_loss_closure"]["stdin_positive_oids"]
    assert any(
        issue["code"] == "removed-reflog-object-missing"
        and missing_oid in str(issue["subject"])
        for issue in payload["issues"]
    )


def test_a2_a6_production_cli_rejects_child_path_and_time_injection(tmp_path: Path):
    repo = _init_repo(tmp_path)
    _git(repo, "branch", "topic", "main")
    for option, value in (
        ("--now", "2099-01-01T00:00:00Z"),
        ("--landed-checker", str(tmp_path / "landed.py")),
        ("--audit-tool", str(tmp_path / "audit.py")),
    ):
        result = subprocess.run(
            [sys.executable, str(TOOL_PATH), "--repo", str(repo),
             "--branch", "topic", option, value],
            cwd=ROOT, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            check=False,
        )
        assert result.returncode == 64
        assert result.stdout == ""


def test_m20_a4_effective_global_prune_config_is_observed(tmp_path: Path):
    repo = _init_repo(tmp_path)
    topic = _empty_child(repo)
    _git(repo, "branch", "topic", topic)
    _git(repo, "config", "--unset", "gc.pruneExpire")
    object_path = repo / ".git" / "objects" / topic[:2] / topic[2:]
    mtime = dt.datetime(2030, 1, 14, tzinfo=dt.timezone.utc).timestamp()
    os.utime(object_path, (mtime, mtime))
    home = tmp_path / "home"
    home.mkdir()
    (home / ".gitconfig").write_text("[gc]\n\tpruneExpire = now\n", encoding="utf-8")
    checker = _make_fake_landed(tmp_path / "landed.py")

    rc, payload, process = _run_tool(
        repo, "--branch", "topic", "--landed-checker", str(checker),
        "--now", "2030-01-15T00:00:00Z", env={"HOME": str(home)},
    )
    assert rc == 0, process.stdout + process.stderr
    retention = _commit_row(payload, topic)["retention"]
    assert retention["loss_possible_not_before"] == "2030-01-15T00:00:00Z"
    assert payload["gc"]["config"]["gc_prune_expire"]["source"].startswith("file:")


def test_a4_absolute_prune_expiry_is_determinate(tmp_path: Path):
    repo = _init_repo(tmp_path)
    topic = _empty_child(repo)
    _git(repo, "branch", "topic", topic)
    _git(repo, "config", "gc.pruneExpire", "2030-02-01")
    object_path = repo / ".git" / "objects" / topic[:2] / topic[2:]
    mtime = dt.datetime(2030, 1, 20, tzinfo=dt.timezone.utc).timestamp()
    os.utime(object_path, (mtime, mtime))
    checker = _make_fake_landed(tmp_path / "landed.py")

    rc, payload, process = _run_tool(
        repo, "--branch", "topic", "--landed-checker", str(checker),
        "--now", "2030-01-15T00:00:00Z",
    )
    assert rc == 0, process.stdout + process.stderr
    retention = _commit_row(payload, topic)["retention"]
    assert retention["deadline_status"] == "determinate"
    assert retention["lower_bound_basis"] == "loose-object-mtime-vs-absolute-prune-expire"
    assert retention["loss_possible_not_before"] == "2030-01-15T00:00:00Z"


def test_p05_porcelain_accepts_locked_detached_bare_and_c_quoted_path(tmp_path: Path):
    oid = "a" * 40
    plain = tmp_path / "plain"
    reason = tmp_path / "reason"
    quoted = str(tmp_path / "quoted\npath").replace("\n", "\\012")
    bare = tmp_path / "bare.git"
    porcelain = (
        f"worktree {plain}\nHEAD {oid}\ndetached\nlocked\n\n"
        f"worktree {reason}\nHEAD {oid}\nbranch refs/heads/topic\nlocked maintenance\n\n"
        f"worktree \"{quoted}\"\nHEAD {oid}\ndetached\nprunable\n\n"
        f"worktree {bare}\nbare\n\n"
    ).encode("ascii")

    class FakeGit:
        def run(self, _args: Any):
            return subprocess.CompletedProcess([], 0, stdout=porcelain, stderr=b"")

    rows = TOOL._parse_worktrees(FakeGit(), tmp_path / "common", plain)
    assert len(rows) == 4
    assert next(row for row in rows if row.path == plain).locked_reason == ""
    assert next(row for row in rows if row.path == reason).locked_reason == "maintenance"
    assert next(row for row in rows if "\n" in str(row.path)).prunable_reason == ""
    bare_row = next(row for row in rows if row.path == bare)
    assert bare_row.bare is True and bare_row.head is None

    repo = _init_repo(tmp_path / "live")
    _git(repo, "branch", "topic", "main")
    standalone = tmp_path / "locked-standalone"
    with_reason = tmp_path / "locked-reason"
    _git(repo, "worktree", "add", "--detach", str(standalone), "main")
    _git(repo, "worktree", "add", "--detach", str(with_reason), "main")
    _git(repo, "worktree", "lock", str(standalone))
    _git(repo, "worktree", "lock", "--reason", "maintenance", str(with_reason))
    rc, payload, process = _run_tool(repo, "--branch", "topic")
    assert rc == 0, process.stdout + process.stderr
    live_rows = {row["path"]: row for row in payload["root_snapshot"]["worktrees"]}
    assert live_rows[str(standalone)]["locked"] is True
    assert live_rows[str(with_reason)]["locked_reason"] == "maintenance"


def test_m19_unknown_worktree_field_keeps_record_as_permanent_root(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
):
    repo = _init_repo(tmp_path)
    _git(repo, "branch", "topic", "main")
    original = TOOL.Git.run

    def inject_unknown(git: Any, args: Any, **kwargs: Any):
        result = original(git, args, **kwargs)
        if args == ["worktree", "list", "--porcelain"]:
            result = subprocess.CompletedProcess(
                result.args, result.returncode,
                stdout=result.stdout.replace(b"\n\n", b"\nfuture-field fixture\n\n", 1),
                stderr=result.stderr,
            )
        return result

    monkeypatch.setattr(TOOL.Git, "run", inject_unknown)
    rc, payload, process = _run_tool(repo, "--branch", "topic")
    assert rc == 0, process.stdout + process.stderr
    row = next(item for item in payload["root_snapshot"]["worktrees"]
               if item["path"] == str(repo))
    assert row["inspection_complete"] is False
    assert row["root_classification"] == "permanent"
    issue = next(item for item in payload["issues"]
                 if item["code"] == "worktree-record-unknown-field")
    assert issue["affects_completeness"] is False


def test_a8_git_ref_rules_and_non_utf8_ref_are_reversible(tmp_path: Path):
    repo = _init_repo(tmp_path)
    _git(repo, "branch", "topic+rescue", "main")
    raw_name = b"refs/tags/nonutf8-\xff"

    class FakeGit:
        def run(self, _args: Any):
            row = raw_name + b"\0" + b"a" * 40 + b"\0commit\0\0\n"
            return subprocess.CompletedProcess([], 0, stdout=row, stderr=b"")

    refs = TOOL._parse_refs(FakeGit())
    assert os.fsencode(refs[0]["name"]) == raw_name
    assert json.loads(json.dumps(refs, ensure_ascii=True))[0]["name"] == refs[0]["name"]

    rc, payload, process = _run_tool(repo, "--branch", "topic+rescue")
    assert rc == 0, process.stdout + process.stderr
    assert payload["candidates"][0]["input"] == "topic+rescue"


def test_a8_non_utf8_ref_is_stable_in_snapshot_digest(tmp_path: Path):
    repo = _init_repo(tmp_path)
    oid = _git(repo, "rev-parse", "main").stdout.strip()
    _git(repo, "branch", "topic", "main")
    raw_ref = os.fsencode(repo / ".git" / "refs" / "tags") + b"/nonutf8-\xff"
    with open(raw_ref, "wb") as stream:
        stream.write(oid.encode("ascii") + b"\n")

    rc, payload, process = _run_tool(repo, "--branch", "topic")
    assert rc == 0, process.stdout + process.stderr
    assert payload["root_snapshot"]["stable"] is True
    names = [root["name"] for root in payload["root_snapshot"]["roots"]]
    assert b"refs/tags/nonutf8-\xff" in [os.fsencode(name) for name in names]


def test_a9_out_of_range_reflog_timestamp_is_defined_rc2(tmp_path: Path):
    repo = _init_repo(tmp_path)
    oid = _git(repo, "rev-parse", "main").stdout.strip()
    _git(repo, "branch", "topic", "main")
    log = repo / ".git" / "logs" / "refs" / "heads" / "topic"
    log.write_text(
        f"{oid} {oid} Test <test@example.invalid> 253402300800 +0000\tfixture\n",
        encoding="ascii",
    )

    rc, payload, _ = _run_tool(repo, "--branch", "topic")
    assert rc == 2
    assert any(issue["code"] == "reflog-parse-error" for issue in payload["issues"])


def test_a9_reflog_expiry_addition_overflow_is_defined_rc2(tmp_path: Path):
    repo = _init_repo(tmp_path)
    oid = _git(repo, "rev-parse", "main").stdout.strip()
    _git(repo, "branch", "topic", "main")
    log = repo / ".git" / "logs" / "refs" / "heads" / "topic"
    log.write_text(
        f"{oid} {oid} Test <test@example.invalid> 253402214400 +0000\tfixture\n",
        encoding="ascii",
    )

    rc, payload, _ = _run_tool(repo, "--branch", "topic")
    assert rc == 2
    assert any(
        issue["code"] == "reflog-parse-error"
        and "expiry" in issue["message"]
        for issue in payload["issues"]
    )


def test_a10_ledger_rejects_sample_threshold_not_derived_from_gc_auto() -> None:
    entry = _ledger_entry("a" * 40)
    entry["gc_auto_sample_threshold"] = 26
    valid, reason = TOOL._validate_ledger_entry(entry)
    assert valid is False
    assert reason == "ledger-entry-gc-sample-threshold-invalid"


def test_m22_audit_requires_one_final_elapsed_seconds_line(tmp_path: Path):
    repo = _init_repo(tmp_path)
    audit = tmp_path / "audit.py"
    audit.write_text(
        "print('audit_dangling_commits: 要確認 0 件')\n",
        encoding="utf-8",
    )

    rc, payload, _ = _run_tool(
        repo, "--ledger-check", "--audit-tool", str(audit),
    )
    assert rc == 2
    assert payload["ledger"]["audit"]["complete"] is False
    assert any(issue["code"] == "audit-contract-invalid" for issue in payload["issues"])


def test_m25_promisor_fixture_forces_no_lazy_fetch_for_every_child(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
):
    repo = _init_repo(tmp_path)
    main = _git(repo, "rev-parse", "main").stdout.strip()
    missing_oid = _empty_child(repo, main)
    tree = _git(repo, "rev-parse", f"{main}^{{tree}}").stdout.strip()
    live_oid = _git(repo, "commit-tree", tree, "-p", main, "-m", "live").stdout.strip()
    assert live_oid != missing_oid
    _git(repo, "branch", "topic", missing_oid)
    remote = tmp_path / "remote.git"
    _git(tmp_path, "clone", "--bare", str(repo), str(remote))
    _git(repo, "branch", "-f", "topic", live_oid)
    _git(repo, "remote", "add", "origin", str(remote))
    _git(repo, "config", "remote.origin.promisor", "true")
    _git(repo, "config", "extensions.partialClone", "origin")
    object_path = repo / ".git" / "objects" / missing_oid[:2] / missing_oid[2:]
    object_path.unlink()

    trap_dir = tmp_path / "trap-bin"
    trap_dir.mkdir()
    trap_marker = tmp_path / "untrusted-python-ran"
    trap_python = trap_dir / "python3"
    trap_python.write_text(
        "#!/bin/sh\n"
        f"printf hit > {shlex.quote(str(trap_marker))}\n"
        f"exec {shlex.quote(str(Path(sys.executable).resolve()))} \"$@\"\n",
        encoding="utf-8",
    )
    trap_python.chmod(0o700)
    checker = tmp_path / "landed.py"
    checker.write_text(
        "import json\n"
        "import os\n"
        "import subprocess\n"
        "import sys\n"
        f"missing_oid = {missing_oid!r}\n"
        "probe_env = dict(os.environ)\n"
        "probe_env.pop('GIT_NO_LAZY_FETCH', None)\n"
        "probe = subprocess.run(['git', 'cat-file', '-t', missing_oid], env=probe_env,\n"
        "                       stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)\n"
        "if probe.returncode == 0:\n"
        "    raise SystemExit(17)\n"
        "payload = {\n"
        "    'schema': 'izanagi-branch-landed-v1',\n"
        "    'branch_delete_authorized': False,\n"
        "    'manual_review_required': True,\n"
        "    'decision': {'verdict': 'landed', 'reason': 'wrapper-probed', 'conclusive': True},\n"
        "    'branch': {'input': sys.argv[-1], 'tip': sys.argv[-1]},\n"
        "    'observations': {'ledger_corpus': {'bytes_read': 0}},\n"
        "}\n"
        "print(json.dumps(payload, sort_keys=True))\n",
        encoding="utf-8",
    )
    real_spawn = TOOL.subprocess.run
    observed_envs: list[dict[str, str]] = []

    def recording_spawn(argv: Any, *positional: Any, **kwargs: Any):
        observed_envs.append(dict(kwargs["env"]))
        return real_spawn(argv, *positional, **kwargs)

    before = _repository_control_bytes(repo)
    monkeypatch.setattr(TOOL.subprocess, "run", recording_spawn)
    rc, payload, _ = _run_tool(
        repo, "--branch", "topic", "--landed-checker", str(checker),
        env={"PATH": str(trap_dir) + os.pathsep + os.environ["PATH"]},
    )
    after = _repository_control_bytes(repo)
    issue_codes = [issue["code"] for issue in payload["issues"]]
    assert rc == 2, issue_codes
    assert "removed-reflog-object-missing" in issue_codes, (issue_codes, payload["issues"])
    assert _commit_row(payload, live_oid)["landed_assessment"]["complete"] is True
    assert observed_envs
    assert all(env.get("GIT_NO_LAZY_FETCH") == "1" for env in observed_envs)
    assert trap_marker.exists() is False
    assert after == before


def test_m27_unclassified_storage_has_null_indeterminate_floor(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
):
    oid = "a" * 40
    objects = tmp_path / "objects"
    objects.mkdir()
    monkeypatch.setattr(TOOL, "_cat_types", lambda _git, _oids: {oid: None})
    retention, complete = TOOL._retention(
        None, oid, dt.datetime(2030, 1, 15, tzinfo=dt.timezone.utc),
        objects, [], {}, {"effective": "14.days.ago"}, [],
    )
    assert complete is False
    assert retention["deadline_status"] == "indeterminate"
    assert retention["loss_possible_not_before"] is None


def test_deadline_contract_assessment_time_failure_is_defined_rc2(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
):
    repo = _init_repo(tmp_path)
    parser = TOOL._parser()
    args = parser.parse_args(["--repo", str(repo), "--ledger-check"])

    def unavailable_clock() -> dt.datetime:
        raise RuntimeError("clock unavailable")

    monkeypatch.setattr(TOOL, "_current_assessment_time", unavailable_clock)
    rc, payload = TOOL.assess(args)
    assert rc == 2
    assert payload["generated_at"] == "1970-01-01T00:00:00Z"
    assert payload["issues"][0]["code"] == "assessment-time-indeterminate"


def test_m30_gc_prune_expire_never_is_determinate(tmp_path: Path):
    repo = _init_repo(tmp_path)
    topic = _empty_child(repo)
    _git(repo, "branch", "topic", topic)
    _git(repo, "config", "gc.pruneExpire", "never")
    checker = _make_fake_landed(tmp_path / "landed.py")

    rc, payload, process = _run_tool(
        repo, "--branch", "topic", "--landed-checker", str(checker),
        "--now", "2030-01-15T00:00:00Z",
    )
    assert rc == 0, process.stdout + process.stderr
    retention = _commit_row(payload, topic)["retention"]
    assert retention["deadline_status"] == "determinate"
    assert retention["lower_bound_basis"] == "gc-prune-expire-never"
    assert retention["loss_possible_not_before"] == "9999-12-31T23:59:59Z"


if __name__ == "__main__":
    raise SystemExit(pytest.main(["-q", __file__]))


@pytest.mark.parametrize("candidate_count", [0, 2])
def test_real_checker_unlanded_spool_details(tmp_path, candidate_count):
    repo = _init_repo(tmp_path)
    _git(repo, "switch", "-c", "topic")
    path = "docs/spool/worklog/2026-08-25-topic-1.md"
    _write(repo, path, "---\nschema: izanagi-spool-v1\nledger: worklog\nauthored: 2026-08-25\n"
           "wave: topic\nseq: 1\ntitle: Topic\n---\nBody.\n")
    topic = _commit(repo, "fragment")
    oid = _git(repo, "rev-parse", f"{topic}:{path}").stdout.strip()
    _git(repo, "switch", "main")
    if candidate_count:
        _write(repo, path, "Different main content.\n")
        _commit(repo, "main mismatch")
        (repo / path).unlink()
        _commit(repo, "remove mismatch")
    assessment = TOOL._landed_assessment(repo, LANDED_PATH, topic, 30, 30)
    assert {k: assessment[k] for k in ("verdict", "conclusive", "checker_rc", "complete")} == {
        "verdict": "indeterminate", "conclusive": False, "checker_rc": 2, "complete": False,
    }
    details = assessment["unproven_unit_details"]
    assert details == {
        "units": [{
            "commit": topic, "path": path, "change": "A",
            "required_state": {"path": path, "mode": "100644", "object_type": "blob", "oid": oid},
            "decision": {"reason": "folded-receipt-absent"},
            "evidence": [{"layer": "exact-tree-state", "decisive": False,
                          "outcome": "not-matched", "reason": "exact-state-absent-from-main-history",
                          "candidate_count": candidate_count, "candidate_limit": 1024,
                          "matched_commit": None},
                         {"layer": "folded-receipt", "decisive": True, "outcome": "not-matched",
                          "reason": "folded-receipt-absent", "candidate_count": None,
                          "candidate_limit": None, "matched_commit": None}],
        }],
        "reason_counts": {"folded-receipt-absent": 1}, "unit_limit": 100,
        "unproven_count": 1, "truncated": False, "complete": True, "missing_reason": None,
    }
    rc, payload, process = _run_tool(repo, "--branch", "topic", "--assessment-timeout-seconds", "30")
    assert rc == 2
    assert _commit_row(json.loads(process.stdout), topic)["landed_assessment"]["unproven_unit_details"] == details
    assert payload["decision_inputs"]["indeterminate"] == 1
    # The same fragment's exact historical state is sufficient even without a receipt.
    content = _git(repo, "show", f"{topic}:{path}").stdout
    _write(repo, path, content)
    _commit(repo, "main witness")
    (repo / path).unlink()
    _commit(repo, "remove witness")
    positive = TOOL._landed_assessment(repo, LANDED_PATH, topic, 30, 30)
    assert {k: positive[k] for k in ("verdict", "conclusive", "checker_rc", "complete")} == {
        "verdict": "landed", "conclusive": True, "checker_rc": 0, "complete": True,
    }
    assert positive["unproven_unit_details"]["units"] == []
    assert positive["unproven_unit_details"]["complete"] is True


def test_unproven_details_are_bounded_and_count_all_reasons():
    unit = {
        "commit": "a" * 40, "path": "f", "change": "M",
        "required_state": {"path": "f", "mode": "100644", "object_type": "blob", "oid": "b" * 40},
        "decision": {"verdict": "indeterminate", "reason": "exact-state-not-proven"},
        "evidence": [{"layer": "exact-tree-state", "decisive": True, "outcome": "not-matched",
                      "reason": "exact-state-absent-from-main-history", "candidate_count": 5,
                      "candidate_limit": 1024, "matched_commit": None}],
    }
    payload = {"proof_units": [unit] * 101, "summary": {"proof_units": 101, "files_enumerated": True}}
    result = TOOL._unproven_unit_details(payload)
    assert len(result["units"]) == 100
    assert result["unproven_count"] == 101
    assert result["reason_counts"] == {"exact-state-not-proven": 101}
    assert result["truncated"] is True
    assert result["complete"] is False
    assert result["missing_reason"] == "unit-output-limit"
    assert result["units"][0] == {
        "commit": "a" * 40, "path": "f", "change": "M", "required_state": unit["required_state"],
        "decision": {"reason": "exact-state-not-proven"},
        "evidence": [{"layer": "exact-tree-state", "decisive": True, "outcome": "not-matched",
                      "reason": "exact-state-absent-from-main-history", "candidate_count": 5,
                      "candidate_limit": 1024, "matched_commit": None}],
    }


@pytest.mark.parametrize("failure", ["timeout", "no-units", "partial-units"])
def test_missing_child_unit_details_never_claim_complete(tmp_path, monkeypatch, failure):
    if failure == "timeout":
        def timeout(*args, **kwargs):
            raise subprocess.TimeoutExpired(args[0], 1)
        monkeypatch.setattr(TOOL.subprocess, "run", timeout)
        assessment = TOOL._landed_assessment(tmp_path, LANDED_PATH, "a" * 40, 1, 1)
        assert assessment["reason"] == "checker-timeout"
        assert assessment["complete"] is False
        assert assessment["checker_rc"] is None
        result = assessment["unproven_unit_details"]
        assert result["missing_reason"] == "child-report-unavailable"
    else:
        payload = {} if failure == "no-units" else {
            "proof_units": [], "summary": {"proof_units": 3, "files_enumerated": True},
        }
        result = TOOL._unproven_unit_details(payload)
        assert result["missing_reason"] == ("proof-units-unavailable" if failure == "no-units"
                                             else "proof-unit-details-incomplete")
    assert result["complete"] is False
    assert result["units"] == []


def test_unit_details_do_not_change_assessment_decisions(tmp_path, monkeypatch):
    repo = _init_repo(tmp_path)
    oid = _empty_child(repo)
    checker = _make_fake_landed(tmp_path / "checker.py", "indeterminate")
    monkeypatch.setattr(TOOL.time, "monotonic", lambda: 1.0)
    before = TOOL._landed_assessment(repo, checker, oid, 30, 30)
    calls = []
    def injected_details(payload):
        calls.append(payload)
        return {"complete": True, "units": ["different"]}
    monkeypatch.setattr(TOOL, "_unproven_unit_details", injected_details)
    after = TOOL._landed_assessment(repo, checker, oid, 30, 30)
    assert len(calls) == 1
    assert calls[0] == {
        "schema": "izanagi-branch-landed-v1",
        "branch_delete_authorized": False,
        "manual_review_required": True,
        "decision": {
            "verdict": "indeterminate", "reason": "fake-indeterminate", "conclusive": False,
        },
        "observations": {"ledger_corpus": {"bytes_read": 0}},
        "branch": {"input": oid, "tip": oid},
    }
    assert after["unproven_unit_details"] == {"complete": True, "units": ["different"]}
    assert before["unproven_unit_details"] != after["unproven_unit_details"]
    assert {k: v for k, v in after.items() if k != "unproven_unit_details"} == {
        k: v for k, v in before.items() if k != "unproven_unit_details"
    }
    assert (after["verdict"], after["conclusive"], after["checker_rc"], after["complete"]) == (
        "indeterminate", False, 2, False,
    )


def test_unit_details_do_not_change_rescue_rc_or_decision_inputs(tmp_path, monkeypatch):
    repo = _init_repo(tmp_path)
    topic = _topic_with_file(repo)
    checker = _make_fake_landed(tmp_path / "checker.py", "indeterminate")
    args = ("--branch", "topic", "--landed-checker", str(checker))
    before_rc, before, _ = _run_tool(repo, *args)
    calls = []
    def injected_details(payload):
        calls.append(payload)
        return {"complete": True, "units": ["rescue-injected"]}
    monkeypatch.setattr(TOOL, "_unproven_unit_details", injected_details)
    after_rc, after, process = _run_tool(repo, *args)
    assert len(calls) == 1
    assert calls[0] == {
        "schema": "izanagi-branch-landed-v1",
        "branch_delete_authorized": False,
        "manual_review_required": True,
        "decision": {
            "verdict": "indeterminate", "reason": "fake-indeterminate", "conclusive": False,
        },
        "observations": {"ledger_corpus": {"bytes_read": 0}},
        "branch": {"input": topic, "tip": topic},
    }
    after_details = _commit_row(after, topic)["landed_assessment"]["unproven_unit_details"]
    assert after_details == {"complete": True, "units": ["rescue-injected"]}
    assert _commit_row(json.loads(process.stdout), topic)["landed_assessment"]["unproven_unit_details"] == after_details
    assert _commit_row(before, topic)["landed_assessment"]["unproven_unit_details"] != after_details
    assert before_rc == after_rc == 2
    assert before["decision_inputs"] == after["decision_inputs"]
    assert after["decision_inputs"]["indeterminate"] == 1
    assert after["decision_inputs"]["visualization_complete"] is False
    for payload in (before, after):
        assessment = _commit_row(payload, topic)["landed_assessment"]
        assert (assessment["complete"], assessment["conclusive"], assessment["verdict"], assessment["checker_rc"]) == (
            False, False, "indeterminate", 2,
        )
