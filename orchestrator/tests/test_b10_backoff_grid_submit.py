"""Exercise the real submission shell with scheduler commands confined to stubs."""
import hashlib
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import re
import shlex
import subprocess
import sys
from types import SimpleNamespace

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from orchestrator.campaign import b10_backoff_static_tail_formal as formal


REPO = Path(__file__).resolve().parents[2]
SUBMIT = REPO / "tools/pegasus/submit_b10_backoff_grid.sh"
JOB = REPO / "tools/pegasus/b10_backoff_grid.sh"
# Preregistration section 8.2, independent of the shell under test.
FORMAL = "t2500-tail-formal"
COMMIT = "0123456789abcdef" * 2 + "01234567"
WORKLOADS = ["write-heavy", "balanced", "read-heavy"]


@pytest.fixture
def submission(tmp_path):
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    output = tmp_path / "output"
    output.mkdir()
    explore = tmp_path / "explore"
    explore.mkdir()
    calls = tmp_path / "calls.jsonl"
    stub = "#!" + sys.executable + "\n" + '''import hashlib, json, os, pathlib, sys
name = pathlib.Path(sys.argv[0]).name
with open(os.environ["SUBMIT_TEST_CALLS"], "a") as stream:
    stream.write(json.dumps([name, *sys.argv[1:]]) + "\\n")
if name == "qstat":
    print("gen_S ENA ACT")
elif name == "pegasusinfo":
    print("test scheduler")
elif name == "qsub":
    rows = pathlib.Path(os.environ["SUBMIT_TEST_CALLS"]).read_text().splitlines()
    count = sum(json.loads(row)[0] == "qsub" for row in rows)
    print(f"{100 + count}.test")
elif name == "sha256sum":
    path = pathlib.Path(sys.argv[-1])
    print(hashlib.sha256(path.read_bytes()).hexdigest() + "  " + str(path))
else:
    assert name == "check_quota"
'''
    for name in ("qsub", "qstat", "pegasusinfo", "check_quota", "sha256sum"):
        path = bin_dir / name
        path.write_text(stub)
        path.chmod(0o700)
    env = {**os.environ, "PATH": str(bin_dir) + os.pathsep + os.environ["PATH"],
           "SUBMIT_TEST_CALLS": str(calls), "PYTHON": sys.executable}

    def run(args, *, include_output=True):
        argv = ["bash", str(SUBMIT)]
        if include_output:
            argv += ["--output-parent", str(output)]
        started = datetime.now(timezone.utc).replace(microsecond=0)
        result = subprocess.run(argv + args, cwd=REPO, env=env,
                                capture_output=True, text=True, timeout=30)
        finished = datetime.now(timezone.utc).replace(microsecond=0)
        result.utc_window = (started, finished)
        return result

    return SimpleNamespace(run=run, output=output, explore=explore, calls=calls,
                           tmp=tmp_path)


def _calls(submission):
    if not submission.calls.exists():
        return []
    return [json.loads(line) for line in submission.calls.read_text().splitlines()]


def _rejected(submission, args):
    result = submission.run(args)
    assert result.returncode == 2, (result.stdout, result.stderr)
    assert _calls(submission) == []  # Includes queue, quota, info, hash, and qsub.
    assert list(submission.output.iterdir()) == []


def _assert_submission(submission, result, kind, *, explore=None):
    assert result.returncode == 0, (result.stdout, result.stderr)
    calls = _calls(submission)
    assert calls[:4] == [["check_quota"], ["qstat", "-Q"], ["pegasusinfo"],
                         ["sha256sum", "--", str(JOB)]]
    qsubs = calls[4:]
    assert len(qsubs) == 3
    receipts = list(submission.output.glob("*.submit.jsonl"))
    assert len(receipts) == 1
    events = [json.loads(line) for line in receipts[0].read_text().splitlines()]
    assert len(events) == 4
    manifest = events[0]
    group = manifest["group_id"]
    assert re.fullmatch(r"b10-backoff-grid-\d{8}T\d{6}Z-[1-9]\d*", group)
    timestamp = datetime.strptime(group.rsplit("-", 2)[1], "%Y%m%dT%H%M%SZ").replace(
        tzinfo=timezone.utc)
    assert result.utc_window[0] <= timestamp <= result.utc_window[1]
    assert receipts[0].name == group + ".submit.jsonl"
    nonce = manifest["submission_nonce"]
    assert re.fullmatch(r"[0-9a-f]{32}", nonce)
    digest = hashlib.sha256(JOB.read_bytes()).hexdigest()
    schema = "b10-backoff-grid-submit-event/v1"
    assert manifest == {
        "schema_version": schema, "event": "manifest", "run_kind": kind,
        "group_id": group, "submission_nonce": nonce,
        "job_script_sha256": digest, "workloads": WORKLOADS,
    }
    for index, workload in enumerate(WORKLOADS):
        base = str(submission.output / (group + "-" + workload))
        values = [f"B10_WORKLOAD={workload}", f"B10_OUTPUT_ROOT={base}",
                  f"B10_SUBMISSION_NONCE={nonce}", f"JOB_SCRIPT_SHA256={digest}"]
        if kind != "extended":
            values += [f"B10_RUN_KIND={kind}"]
        if kind == FORMAL:
            values += [f"B10_PREREGISTRATION_COMMIT={COMMIT}",
                       f"B10_EXPLORE_CAMPAIGN={explore}"]
        assert qsubs[index] == ["qsub", "-v", ",".join(values),
                                "-o", base + ".stdout", "-e", base + ".stderr", str(JOB)]
        assert events[index + 1] == {
            "schema_version": schema, "event": "submitted", "run_kind": kind,
            "workload": workload, "job_id": f"{101 + index}.test",
            "output_root": base, "stdout": base + ".stdout", "stderr": base + ".stderr",
        }
    assert result.stdout.splitlines() == ["101.test", "102.test", "103.test"]


def test_submit_shell_syntax_and_preregistered_literal():
    subprocess.run(["bash", "-n", str(SUBMIT)], check=True)
    text = (REPO / "docs/b10-backoff-static-tail-preregistration.md").read_text()
    section = text.split("### 8.2 ", 1)[1].split("## 9.", 1)[0]
    assert "`run_kind` は `t2500-tail-formal`" in section
    assert "`t2500-backoff-static-tail-formal`" in section


@pytest.mark.parametrize("kind", [None, "extended", "t2266-tail", "t2418-explore"])
def test_submit_legacy_qsub_argv_and_receipt_unchanged(submission, kind):
    args = [] if kind is None else ["--run-kind", kind]
    _assert_submission(submission, submission.run(args), kind or "extended")


def test_submit_formal_forwards_both_inputs_to_three_jobs(submission):
    # A noncanonical spelling must propagate the resolved value.
    explore = str(submission.explore) + "/../explore"
    result = submission.run(["--run-kind", FORMAL, "--preregistration-commit", COMMIT,
                             "--explore-campaign", explore])
    _assert_submission(submission, result, FORMAL, explore=str(submission.explore.resolve()))


@pytest.mark.parametrize("kind", [None, "extended", "t2266-tail", "t2418-explore", FORMAL])
def test_submit_repeated_arguments_produce_distinct_group_ids(submission, kind):
    args = [] if kind is None else ["--run-kind", kind]
    if kind == FORMAL:
        args += ["--preregistration-commit", COMMIT,
                 "--explore-campaign", str(submission.explore)]
    groups = []
    for index in range(2):
        output = submission.tmp / f"repeat-{index}"
        output.mkdir()
        result = submission.run(["--output-parent", str(output), *args], include_output=False)
        assert result.returncode == 0, (result.stdout, result.stderr)
        receipts = list(output.glob("*.submit.jsonl"))
        assert len(receipts) == 1
        groups.append(json.loads(receipts[0].read_text().splitlines()[0])["group_id"])
    assert groups[0] != groups[1]


@pytest.mark.parametrize("commit", ["", "a" * 39, "a" * 41, "A" * 40,
                                     "abcdef0", "main", "HEAD", "a b", "a,b", "a=b", "a\nb"])
def test_submit_rejects_invalid_formal_commit(submission, commit):
    _rejected(submission, ["--run-kind", FORMAL, "--preregistration-commit", commit,
                           "--explore-campaign", str(submission.explore)])


@pytest.mark.parametrize("missing", ["commit", "explore", "both"])
def test_submit_requires_both_formal_inputs(submission, missing):
    args = ["--run-kind", FORMAL]
    if missing == "explore":
        args += ["--preregistration-commit", COMMIT]
    if missing == "commit":
        args += ["--explore-campaign", str(submission.explore)]
    _rejected(submission, args)


@pytest.mark.parametrize("case", ["empty", "relative", "missing", "file", "symlink",
                                   "repo", "repo-child", "repo-ancestor", "git-ancestor",
                                   "git-self", "space", "comma", "equals", "newline",
                                   "resolved-space", "resolved-comma", "resolved-equals",
                                   "resolved-newline"])
def test_submit_rejects_invalid_formal_explore_before_side_effects(submission, case):
    path = submission.explore
    if case == "empty":
        value = ""
    elif case == "relative":
        value = "docs"
    elif case == "missing":
        value = str(submission.tmp / "missing")
    elif case == "file":
        path = submission.tmp / "file"
        path.write_text("not a directory")
        value = str(path)
    elif case == "symlink":
        path = submission.tmp / "link"
        path.symlink_to(submission.explore, target_is_directory=True)
        value = str(path)
    elif case.startswith("repo"):
        value = str({"repo": REPO, "repo-child": REPO / "docs",
                     "repo-ancestor": REPO.parent}[case])
    elif case.startswith("git"):
        (path / ".git").write_text("gitdir: /unneeded")
        if case == "git-ancestor":
            path = path / "child"
            path.mkdir()
        value = str(path)
    else:
        character = {"space": " ", "comma": ",", "equals": "=", "newline": "\n"}[
            case.removeprefix("resolved-")]
        unsafe = submission.tmp / ("unsafe" + character + "name")
        unsafe.mkdir()
        if case.startswith("resolved-"):
            (unsafe / "child").mkdir()
            link = submission.tmp / "safe-link"
            link.symlink_to(unsafe, target_is_directory=True)
            path = link / "child"  # Leaf is real; only its ancestor is a symlink.
        else:
            path = unsafe
        value = str(path)
    _rejected(submission, ["--run-kind", FORMAL, "--preregistration-commit", COMMIT,
                           "--explore-campaign", value])


@pytest.mark.parametrize("kind", ["extended", "t2266-tail", "t2418-explore"])
@pytest.mark.parametrize("flags", ["commit", "explore", "both", "empty-commit", "empty-explore", "empty-both"])
def test_submit_legacy_rejects_formal_flags(submission, kind, flags):
    args = ["--run-kind", kind]
    if "commit" in flags or "both" in flags:
        args += ["--preregistration-commit", "" if flags.startswith("empty") else COMMIT]
    if "explore" in flags or "both" in flags:
        args += ["--explore-campaign", "" if flags.startswith("empty") else str(submission.explore)]
    _rejected(submission, args)


def test_submit_unknown_kind_still_rejected(submission):
    _rejected(submission, ["--run-kind", "unknown"])


@pytest.mark.parametrize("position,expected_rc", [
    (0, 0),  # Help is the first option.
    (1, 2),  # run-kind consumes help; the original kind is an unknown option.
    (2, 0),  # Help follows the complete run-kind option.
    (3, 2),  # commit consumes help; the empty original value is an unknown option.
    (4, 0),  # The recognized commit option lets the loop reach help.
    (5, 2),  # explore consumes help; /missing is an unknown option.
    (6, 0),  # New explore flag recognition intentionally makes help reachable (old rc=2).
    (7, 2),  # output-parent consumes help; /missing is an unknown option.
    (8, 0),  # Help is reached before --unknown.
    (9, 2),  # --unknown rejects before help can be reached.
])
@pytest.mark.parametrize("kind", ["extended", FORMAL, "unknown"])
def test_submit_help_at_every_argument_position(submission, position, expected_rc, kind):
    args = ["--run-kind", kind, "--preregistration-commit", "",
            "--explore-campaign", "/missing", "--output-parent", "/missing", "--unknown"]
    args.insert(position, "--help")
    result = submission.run(args, include_output=False)
    assert result.returncode == expected_rc, result.stderr
    assert "usage:" in result.stderr
    assert FORMAL in result.stderr
    assert "--preregistration-commit" in result.stderr
    assert "--explore-campaign" in result.stderr
    assert _calls(submission) == []
    assert list(submission.output.iterdir()) == []


def test_submit_help_after_new_explore_flag_intentionally_returns_zero(submission):
    result = submission.run(["--run-kind", "extended", "--explore-campaign", "/x", "--help"],
                            include_output=False)
    assert result.returncode == 0, result.stderr  # Recognizing the new flag changes old rc=2.
    assert "usage:" in result.stderr
    assert _calls(submission) == []
    assert list(submission.output.iterdir()) == []


@pytest.mark.parametrize("alias", [False, True], ids=["direct", "alias-dot"])
def test_submit_rejects_trailing_newline_explore_before_side_effects(submission, alias):
    unsafe = submission.tmp / "explore\n"
    unsafe.mkdir()  # submission.explore is the different directory reached if LF is lost.
    value = str(unsafe)
    if alias:
        link = submission.tmp / "safe-alias"
        link.symlink_to(unsafe, target_is_directory=True)
        value = str(link) + "/."  # Pass the lexical and leaf-symlink checks.
    _rejected(submission, ["--run-kind", FORMAL, "--preregistration-commit", COMMIT,
                           "--explore-campaign", value])


def _documented_argv(section, replacements):
    text = (REPO / "docs/b10-backoff-static-tail-submission.md").read_text()
    body = text.split(f"## {section}. ", 1)[1].split("\n## ", 1)[0]
    block = re.search(r"```\n(.*?)\n```", body, re.S).group(1)
    for placeholder, value in replacements.items():
        assert placeholder in block
        block = block.replace(placeholder, shlex.quote(value))
    assert "<" not in block
    lines = block.replace("\\\n", "").splitlines()
    return [shlex.split(line) for line in lines if line.strip()]


def test_documented_submission_argv_reaches_three_jobs(submission):
    commands = _documented_argv(2, {
        "<repo root>": str(REPO), "<40 桁の commit hash>": COMMIT,
        "<探索走の campaign directory の絶対 path>": str(submission.explore),
        "<repo 外の絶対 path>": str(submission.output),
    })
    assert commands[0] == ["cd", str(REPO)]
    assert len(commands) == 2
    assert commands[1][0] == str(SUBMIT.relative_to(REPO))
    result = submission.run(commands[1][1:], include_output=False)
    _assert_submission(submission, result, FORMAL, explore=str(submission.explore))


@pytest.mark.parametrize("verdict,expected_rc", [("valid", 0), ("invalid", 1)])
def test_documented_cohort_entry_reaches_report_cli(monkeypatch, verdict, expected_rc):
    campaigns = ["/outside/write", "/outside/balanced", "/outside/read"]
    commands = _documented_argv(4, {
        "<投入時と同じ commit hash>": COMMIT,
        "<write-heavy の campaign>": campaigns[0], "<balanced の campaign>": campaigns[1],
        "<read-heavy の campaign>": campaigns[2],
        "<投入時と同じ探索走の campaign>": "/outside/explore",
        "<集団報告の出力先 directory>": "/outside/report",
    })
    assert len(commands) == 1
    command = commands[0]
    assert command[:4] == ["python3.10", "-I", "-B",
                           "orchestrator/campaign/b10_backoff_static_tail_formal.py"]
    argv = command[4:]
    seen = []
    binding = SimpleNamespace(spec={"test": "binding"})

    def load(repo, commit):
        seen.append(("binding", repo, commit))
        return binding

    def explore(path):
        seen.append(("explore", path))
        return "test-mode"

    def campaign(spec, actual_binding, path, *, correctness_mode):
        assert spec is binding.spec and actual_binding is binding
        seen.append(("campaign", path, correctness_mode))
        return {"path": path}

    def report(spec, loaded, output):
        assert spec is binding.spec
        seen.append(("report", loaded, output))
        return {"verdict": verdict}

    monkeypatch.setattr(formal, "load_preregistration", load)
    monkeypatch.setattr(formal, "load_explore_correctness_mode", explore)
    monkeypatch.setattr(formal, "load_formal_campaign_for_report", campaign)
    monkeypatch.setattr(formal, "materialize_report", report)
    assert formal.main(argv) == expected_rc
    assert seen == [("binding", str(REPO), COMMIT), ("explore", "/outside/explore"),
                    *(("campaign", path, "test-mode") for path in campaigns),
                    ("report", [{"path": path} for path in campaigns], "/outside/report")]
    for count in (2, 4):
        bad = list(argv)
        start = bad.index("report") + 1
        bad[start:start + 3] = campaigns[:count] if count == 2 else campaigns + ["/outside/fourth"]
        seen.clear()
        with pytest.raises(SystemExit) as error:
            formal.main(bad)
        assert error.value.code == 2
        assert seen == []


def _run():
    return pytest.main([__file__, "-q"])


if __name__ == "__main__":
    sys.exit(_run())
