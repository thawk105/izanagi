"""Execute job shell wiring without PBS, builds, or measurements."""
from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess
import sys

import pytest

ROOT = Path(__file__).resolve().parents[2]
JOB = ROOT / "tools/pegasus/b10_backoff_grid.sh"
# Preregistration §8.2 fixes these independently of the shell under test.
FORMAL = "t2500-tail-formal"
STEM = "t2500-backoff-static-tail-formal"
LEGACY = ("extended", "t2266-tail", "t2418-explore")


def _source():
    return JOB.read_text(encoding="utf-8")


def _sweep(source):
    start = source.index('if [[ "$B10_RUN_KIND" == "t2266-tail" ]]; then')
    end = source.index("\nCURRENT_STAGE=ccbench_worktree_cleanup", start)
    return source[start:end]


def _finalizer(source):
    # Keep argv, heredoc header, body, and terminator contiguous.
    start = source.index('timeout "$FINALIZE_CAP_S" "$PY" -I -B -')
    end = source.index("\nPY\n", start) + len("\nPY\n")
    return source[start:end]


def _environment(tmp_path, kind):
    repo = tmp_path / "repo"
    repo.mkdir()
    (repo / ".git").mkdir()
    explore = tmp_path / "explore"
    explore.mkdir()
    nodefile = tmp_path / "nodes"
    nodefile.write_text("bnode001\n")
    return {
        **os.environ, "PY": sys.executable, "REPO_ROOT": str(repo),
        "PBS_O_WORKDIR": str(repo), "PBS_JOBID": "fixture-job",
        "PBS_NODEFILE": str(nodefile), "B10_RUN_KIND": kind,
        "WORKLOAD": "balanced", "OUTPUT_ROOT": str(tmp_path / "output"),
        "B10_OUTPUT_ROOT": str(tmp_path / "output"),
        "B10_BUILD_CACHE_ROOT": "/scr/fixture-job-b10-backoff-grid-balanced/build-cache",
        "CCBENCH_WORKTREE": str(tmp_path / "detached"),
        "B10_PREREGISTRATION_COMMIT": "a" * 40,
        "B10_EXPLORE_CAMPAIGN": str(explore),
        "SWEEP_CAP_S": "11700", "AA_CAP_S": "3900", "REPORT_CAP_S": "300",
        "FINALIZE_CAP_S": "300", "FREEZE_AFTER": "fixture-freeze",
        "CALLS": str(tmp_path / "calls.jsonl"), "TRACE": str(tmp_path / "trace"),
        "DRIVER_RC": "0", "CURRENT_STAGE": "fixture",
    }


# Only external boundaries are replaced; validation and finalizer Python run.
STUBS = r'''
set -Eeuo pipefail
fail() { echo "$2" >&2; exit "$1"; }
hostname() { echo bnode001; }
mkdir() {
  # Observe scratch creation in DEBUG trace without writing under /scr.
  if [[ "${@: -1}" != /scr/* ]]; then command mkdir "$@"; fi
}
timeout() {
  if [[ "$5" == "-" ]]; then
    shift
    "$@"
    return
  fi
  "$PY" -I -B -c 'import json,sys; open(sys.argv[1], "a").write(json.dumps(sys.argv[2:])+"\n")' \
    "$CALLS" "$CURRENT_STAGE" "$@"
  return "$DRIVER_RC"
}
'''


def _run(snippet, env):
    return subprocess.run(
        ["bash", "-c", STUBS + "\n" + snippet], env=env,
        capture_output=True, text=True, check=False,
    )


def _calls(env):
    path = Path(env["CALLS"])
    return [json.loads(row) for row in path.read_text().splitlines()] if path.exists() else []


def _expected(env, kind):
    prefix = [env["PY"], "-I", "-B"]
    module = env["REPO_ROOT"] + "/orchestrator/campaign/"
    workload = ["balanced", "--output-root", env["OUTPUT_ROOT"]]
    build = ["--cache-root", env["B10_BUILD_CACHE_ROOT"],
             "--ccbench-dir", env["CCBENCH_WORKTREE"]]
    if kind == FORMAL:
        return [["t2500_tail_formal_sweep", "11700", *prefix,
                 module + "b10_backoff_static_tail_formal.py",
                 "--preregistration-commit", env["B10_PREREGISTRATION_COMMIT"],
                 "run", "balanced", "--explore-campaign", env["B10_EXPLORE_CAMPAIGN"],
                 "--output-root", env["OUTPUT_ROOT"], *build]]
    stage = {"extended": "extended_sweep", "t2266-tail": "t2266_tail_sweep",
             "t2418-explore": "t2418_explore_sweep"}[kind]
    calls = [[stage, "11700", *prefix, module + "backoff_extended_sweep.py",
              *workload, *build]]
    if kind != "extended":
        calls[0] += ["--run-kind", kind]
    else:
        calls += [
            ["add_analysis", "3900", *prefix, module + "backoff_overthrottle.py",
             *workload, *build],
            ["report", "300", *prefix, module + "backoff_extended_sweep_report.py",
             *workload, "--defer-plot"],
        ]
    return calls


@pytest.mark.parametrize("kind", LEGACY)
def test_job_legacy_commands_unchanged(tmp_path, kind):
    env = _environment(tmp_path, kind)
    result = _run(_sweep(_source()), env)
    assert result.returncode == 0, result.stderr
    assert _calls(env) == _expected(env, kind)


def test_job_formal_command_uses_run_cli(tmp_path):
    env = _environment(tmp_path, FORMAL)
    result = _run(_sweep(_source()), env)
    assert result.returncode == 0, result.stderr
    assert _calls(env) == _expected(env, FORMAL)


def _entry_through_sweep(source):
    case_start = source.index('case "$B10_RUN_KIND" in')
    case_end = source.index("\nesac", case_start) + len("\nesac")
    start = source.index('REPO_ROOT=$(cd "$PBS_O_WORKDIR" && pwd -P)')
    end = source.index("\nCURRENT_STAGE=allocation_reservation", start)
    return "\n".join((
        source[case_start:case_end],
        r'''trap 'printf "%s\n" "$BASH_COMMAND" >>"$TRACE"' DEBUG''',
        source[start:end], _sweep(source),
    ))


@pytest.mark.parametrize("bad", [
    "valid", "missing-commit", "short-commit", "upper-commit", "branch",
    "missing-explore", "relative", "absent", "file", "symlink",
    "repo", "repo-child", "repo-parent", "other-repo", "parent-symlink",
])
def test_job_formal_inputs_checked_before_work(tmp_path, bad):
    env = _environment(tmp_path, FORMAL)
    repo = Path(env["REPO_ROOT"])
    explore = Path(env["B10_EXPLORE_CAMPAIGN"])
    if bad == "missing-commit":
        del env["B10_PREREGISTRATION_COMMIT"]
    elif bad in ("short-commit", "upper-commit", "branch"):
        env["B10_PREREGISTRATION_COMMIT"] = {
            "short-commit": "a" * 39, "upper-commit": "A" * 40, "branch": "HEAD",
        }[bad]
    elif bad == "missing-explore":
        del env["B10_EXPLORE_CAMPAIGN"]
    elif bad == "relative":
        env["B10_EXPLORE_CAMPAIGN"] = "relative"
    elif bad == "absent":
        explore.rmdir()
    elif bad == "file":
        explore.rmdir()
        explore.write_text("not a directory")
    elif bad == "symlink":
        explore.rmdir()
        explore.symlink_to(tmp_path, target_is_directory=True)
    elif bad in ("repo", "repo-child", "repo-parent"):
        child = repo / "child"
        child.mkdir()
        env["B10_EXPLORE_CAMPAIGN"] = str({
            "repo": repo, "repo-child": child, "repo-parent": repo.parent,
        }[bad])
    elif bad == "other-repo":
        (explore / ".git").mkdir()
    elif bad == "parent-symlink":
        (repo / "child").mkdir()
        alias = tmp_path / "alias"
        alias.symlink_to(repo, target_is_directory=True)
        env["B10_EXPLORE_CAMPAIGN"] = str(alias / "child")
    result = _run(_entry_through_sweep(_source()), env)
    trace = Path(env["TRACE"]).read_text().splitlines()
    mkdir_calls = [i for i, line in enumerate(trace) if line.startswith("mkdir ")]
    if bad == "valid":
        assert result.returncode == 0, result.stderr
        assert _calls(env) == _expected(env, FORMAL)
        # Validation and scratch/output creation are observed in this execution.
        commit_check = next(i for i, line in enumerate(trace)
                            if line.startswith("[[") and "B10_PREREGISTRATION_COMMIT" in line)
        path_check = next(i for i, line in enumerate(trace)
                          if line.startswith('"$PY"') and '"$B10_EXPLORE_CAMPAIGN"' in line)
        assert commit_check < min(mkdir_calls)
        assert path_check < min(mkdir_calls)
        assert Path(env["OUTPUT_ROOT"]).is_dir()
    else:
        assert result.returncode == 2, result.stderr
        assert not mkdir_calls
        assert not Path(env["OUTPUT_ROOT"]).exists()
        assert not _calls(env)


@pytest.mark.parametrize("kind", LEGACY)
@pytest.mark.parametrize("inputs", ["missing", "invalid"])
def test_job_legacy_ignores_formal_environment(tmp_path, kind, inputs):
    env = _environment(tmp_path, kind)
    for key in ("B10_PREREGISTRATION_COMMIT", "B10_EXPLORE_CAMPAIGN"):
        if inputs == "missing":
            del env[key]
        else:
            env[key] = "invalid"
    result = _run(_entry_through_sweep(_source()), env)
    assert result.returncode == 0, result.stderr
    assert _calls(env) == _expected(env, kind)


def test_job_unknown_kind_rejected(tmp_path):
    env = _environment(tmp_path, "unknown")
    result = _run(_entry_through_sweep(_source()), env)
    assert result.returncode == 2
    assert not Path(env["OUTPUT_ROOT"]).exists()
    assert not _calls(env)


def _campaign(env, variants, receipt_names, campaign_count=1):
    base = Path(env["OUTPUT_ROOT"])
    (base / "campaigns").mkdir(parents=True)
    for index in range(campaign_count):
        campaign = base / "campaigns" / f"fixture-{index}"
        (campaign / "runs").mkdir(parents=True)
        (campaign / "reports").mkdir()
        rows = [{"stage": "commit", "variant": variant} for variant in variants]
        rows += [{"stage": "prepare", "variant": "uncommitted"}]
        (campaign / "runs/wal.jsonl").write_text(
            "\n".join(json.dumps(row) for row in rows) + "\n")
        for name in receipt_names:
            # Shell checks existence only; semantics belong to the driver.
            (campaign / "reports" / name).write_text("execution fixture\n")
    return base / "campaigns/fixture-0"


@pytest.mark.parametrize("case", [
    "valid", "duplicate-valid", "seven", "nine", "duplicate-padding", "null",
    "missing", "wrong-stem", "root", "campaign-root", "symlink", "directory",
    "zero-campaigns", "two-campaigns",
])
def test_job_formal_requires_eight_commits_and_execution_artifact(tmp_path, case):
    env = _environment(tmp_path, FORMAL)
    variants = list(range(8))
    if case == "seven":
        variants = list(range(7))
    elif case == "nine":
        variants = list(range(9))
    elif case == "duplicate-padding":
        variants = list(range(7)) + [0]
    elif case == "duplicate-valid":
        variants += [0, 1]
    elif case == "null":
        variants[-1] = None
    name = STEM + "-execution.json"
    count = {"zero-campaigns": 0, "two-campaigns": 2}.get(case, 1)
    campaign = _campaign(env, variants, [name], count)
    receipt = campaign / "reports" / name
    if case == "missing":
        receipt.unlink()
    elif case in ("wrong-stem", "root", "campaign-root"):
        target = {
            "wrong-stem": campaign / "reports/t2266-backoff-static-tail-balanced.json",
            "root": Path(env["OUTPUT_ROOT"]) / name,
            "campaign-root": campaign / name,
        }[case]
        receipt.rename(target)
    elif case == "symlink":
        target = tmp_path / "receipt"
        receipt.rename(target)
        receipt.symlink_to(target)
    elif case == "directory":
        receipt.unlink()
        receipt.mkdir()
    result = _run(_finalizer(_source()), env)
    success = case in ("valid", "duplicate-valid")
    assert (result.returncode == 0) == success, result.stderr
    completion = Path(env["OUTPUT_ROOT"]) / "completion.json"
    assert completion.exists() == success
    if success:
        document = json.loads(completion.read_text())
        assert document["run_kind"] == FORMAL
        assert document["status"] == "complete"
        # No collective .dat/.json/-complete.json has been materialized.
        for suffix in (".dat", ".json", "-complete.json"):
            assert not list(Path(env["OUTPUT_ROOT"]).rglob(STEM + suffix))


@pytest.mark.parametrize("kind,count,stem", [
    ("t2266-tail", 8, "t2266-backoff-static-tail-balanced"),
    ("t2418-explore", 5, "t2418-backoff-static-explore-balanced"),
])
@pytest.mark.parametrize("case", [
    "valid", "duplicate-valid", "too-few", "too-many", "null", "duplicate-padding",
    "missing-dat", "missing-json", "wrong-stem", "root", "symlink-dat", "symlink-json",
])
def test_job_legacy_finalizer_contract_unchanged(tmp_path, kind, count, stem, case):
    env = _environment(tmp_path, kind)
    variants = list(range(count))
    if case == "too-few":
        variants.pop()
    elif case == "too-many":
        variants.append(count)
    elif case == "null":
        variants[-1] = None
    elif case == "duplicate-padding":
        variants[-1] = 0
    elif case == "duplicate-valid":
        variants += [0]
    campaign = _campaign(env, variants, [stem + ".dat", stem + ".json"])
    for suffix in (".dat", ".json"):
        receipt = campaign / "reports" / (stem + suffix)
        if case == "missing-" + suffix[1:]:
            receipt.unlink()
        elif case == "symlink-" + suffix[1:]:
            target = tmp_path / ("target" + suffix)
            receipt.rename(target)
            receipt.symlink_to(target)
        elif case == "wrong-stem":
            receipt.rename(campaign / "reports" / ("wrong" + suffix))
        elif case == "root":
            receipt.rename(Path(env["OUTPUT_ROOT"]) / (stem + suffix))
    result = _run(_finalizer(_source()), env)
    success = case in ("valid", "duplicate-valid")
    assert (result.returncode == 0) == success, result.stderr
    assert (Path(env["OUTPUT_ROOT"]) / "completion.json").exists() == success


def test_job_extended_finalizer_does_not_require_tail_artifacts(tmp_path):
    env = _environment(tmp_path, "extended")
    (Path(env["OUTPUT_ROOT"]) / "campaigns/only-campaign").mkdir(parents=True)
    result = _run(_finalizer(_source()), env)
    assert result.returncode == 0, result.stderr
    assert (Path(env["OUTPUT_ROOT"]) / "completion.json").is_file()


@pytest.mark.parametrize("rc", [0, 1, 23, 124],
                         ids=["success", "internal-deadline", "driver-error", "timeout"])
def test_job_failed_sweep_cannot_reach_finalizer(tmp_path, rc):
    env = _environment(tmp_path, FORMAL)
    _campaign(env, range(8), [STEM + "-execution.json"])
    env["DRIVER_RC"] = str(rc)
    source = _source()
    # Contiguous source connects sweep failure to finalization. Only external
    # cleanup/freeze dependencies are supplied by this small harness.
    start = source.index('if [[ "$B10_RUN_KIND" == "t2266-tail" ]]; then')
    snippet = '''
remove_ccbench_worktree() { :; }
freeze_digest() { echo fixture-freeze; }
EXPECTED_FREEZE_TREES_SHA256=fixture-freeze
''' + source[start:]
    result = _run(snippet, env)
    assert result.returncode == rc, result.stderr
    assert _calls(env) == _expected(env, FORMAL)
    assert (Path(env["OUTPUT_ROOT"]) / "completion.json").exists() == (rc == 0)


if __name__ == "__main__":
    sys.exit(pytest.main([__file__, "-q"]))
