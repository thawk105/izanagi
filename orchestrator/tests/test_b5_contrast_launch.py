import json
from dataclasses import replace
from pathlib import Path
import subprocess
import sys
from types import SimpleNamespace, ModuleType

import pytest

from tools.pegasus import b5_contrast_launch as launch


def _git(path, *args, input=None):
    return subprocess.run(["git", "-C", str(path), *args], input=input,
                          capture_output=True, text=True, check=True).stdout.strip()


def _fixed_repo(path):
    path.mkdir(parents=True)
    _git(path, "init", "-q")
    # A deterministic tracked file and HEAD without staging/committing the worktree.
    _git(path, "fast-import", "--quiet", input=(
        "blob\nmark :1\ndata 8\nfixture\n\n"
        "commit refs/heads/master\n"
        "author Test <test@example.invalid> 1000000000 +0000\n"
        "committer Test <test@example.invalid> 1000000000 +0000\n"
        "data 7\nfixture\nM 100644 :1 tracked.txt\n\ndone\n"))
    _git(path, "symbolic-ref", "HEAD", "refs/heads/master")
    _git(path, "read-tree", "HEAD")
    (path / "tracked.txt").write_text("fixture\n")
    return _git(path, "rev-parse", "HEAD")


@pytest.fixture
def submit_tree(tmp_path, monkeypatch):
    repo = tmp_path / "submit-tree"
    head = _fixed_repo(repo)
    ccbench = repo / "external/ccbench"
    pin = _fixed_repo(ccbench)
    module = repo / "orchestrator/campaign/p3_s4_loop.py"
    module.parent.mkdir(parents=True)
    module.write_text(f'PIN = "{pin}"\n')
    return repo, head, ccbench


def test_validate_submit_tree_accepts_fixed_clean_heads(submit_tree):
    repo, head, _ = submit_tree
    tree = launch.validate_submit_tree(repo, head)
    assert tree.repo == repo
    assert tree.expected_head == head
    assert tree.common_repo == repo
    (repo / "untracked.txt").write_text("untracked is permitted")
    assert launch.validate_submit_tree(repo, head) == tree


@pytest.mark.parametrize("head", ["1" * 40, "abcd", "A" * 40, ""])
def test_validate_submit_tree_rejects_head(submit_tree, head):
    repo, _, _ = submit_tree
    with pytest.raises(ValueError, match="HEAD"):
        launch.validate_submit_tree(repo, head)


@pytest.mark.parametrize("which", ["superproject", "ccbench"])
def test_validate_submit_tree_rejects_tracked_dirty(submit_tree, which):
    repo, head, ccbench = submit_tree
    ((repo if which == "superproject" else ccbench) / "tracked.txt").write_text("dirty\n")
    with pytest.raises(ValueError, match="not clean"):
        launch.validate_submit_tree(repo, head)


def test_validate_submit_tree_rejects_ccbench_pin(submit_tree, monkeypatch):
    repo, head, _ = submit_tree
    (repo / "orchestrator/campaign/p3_s4_loop.py").write_text(
        'PIN = "' + "f" * 40 + '"\n')
    with pytest.raises(ValueError, match="pin mismatch"):
        launch.validate_submit_tree(repo, head)


@pytest.mark.parametrize("container", [".claude", ".codex"])
def test_validate_submit_tree_rejects_ai_worktree(tmp_path, container):
    repo = tmp_path / container / "worktrees/submit"
    repo.mkdir(parents=True)
    with pytest.raises(ValueError, match="AI worktree"):
        launch.validate_submit_tree(repo, "a" * 40)


def test_validate_submit_tree_rejects_symlink(submit_tree, tmp_path):
    repo, head, _ = submit_tree
    alias = tmp_path / "alias"
    alias.symlink_to(repo, target_is_directory=True)
    with pytest.raises(ValueError, match="symlink"):
        launch.validate_submit_tree(alias, head)


def _pilot(tmp_path):
    thirdparty = tmp_path / "thirdparty"
    thirdparty.mkdir(exist_ok=True)
    tree = launch.SubmitTree(tmp_path / "submit-tree", "a" * 40,
                             tmp_path / "main-repo", thirdparty)
    jobs = launch.pilot_jobs("write-heavy", tmp_path / "ledgers", tmp_path / "evidence",
                             launch.K2(tmp_path / "knowledge.json",
                                       "known_result_conditioned_derivative", "false"))
    return tree, jobs


def _expected_environment(tmp_path, arm):
    name = "block-stock" if arm == "stock" else arm
    env = {
        "IZANAGI_S4_REPO_ROOT": str(tmp_path / "submit-tree"),
        "IZANAGI_S4_EXPECTED_HEAD": "a" * 40,
        "IZANAGI_S4_EVIDENCE_ROOT": str(tmp_path / "evidence" / name),
        "IZANAGI_S4_THIRDPARTY_SOURCE_ROOT": str(tmp_path / "thirdparty"),
        "IZANAGI_S4_B5_MODE": "block-stock" if arm == "stock" else "series",
        "IZANAGI_S4_B5_ARM": arm,
        "IZANAGI_S4_B5_WORKLOAD": "write-heavy",
        "IZANAGI_S4_B5_SERIES": "1",
        "IZANAGI_S4_B5_BLOCK": "1",
        "IZANAGI_S4_B5_LEDGER_ROOT": str(tmp_path / "ledgers" / name),
    }
    if arm == "llm":
        env.update({
            "IZANAGI_S4_KNOWLEDGE_MANIFEST": str(tmp_path / "knowledge.json"),
            "IZANAGI_S4_CODER_ROLE": "coder-v4-autonomous-k2",
            "IZANAGI_S4_KNOWLEDGE_CLASSIFICATION": "known_result_conditioned_derivative",
            "IZANAGI_S4_KNOWLEDGE_DE_NOVO_CLAIM": "false",
        })
    return env


def test_four_qsub_argv_and_explicit_environment_are_exact(tmp_path):
    tree, jobs = _pilot(tmp_path)
    assert [job.arm for job in jobs] == ["random", "sweep-matched", "llm", "stock"]
    for job, arm in zip(jobs, ["random", "sweep-matched", "llm", "stock"]):
        env = _expected_environment(tmp_path, arm)
        assert launch.build_job_environment(job, tree) == env
        evidence = env["IZANAGI_S4_EVIDENCE_ROOT"]
        expected = ["qsub", "-v", ",".join(f"{k}={v}" for k, v in env.items()),
                    "-l", "elapstim_req=03:00:00" if arm == "stock" else "elapstim_req=08:00:00",
                    "-o", evidence + "/job.stdout", "-e", evidence + "/job.stderr",
                    "tools/pegasus/p3_s4_loop_pegasus.sh"]
        assert launch.qsub_argv(job, tree) == expected


def test_pilot_cap_is_literal_60_and_four_jobs_53_sessions(tmp_path):
    _, jobs = _pilot(tmp_path)
    assert launch.PILOT_LOGICAL_SESSION_CAP == 60
    assert len(jobs) == 4
    assert launch.validate_pilot_cap(jobs) == 3 * (1 + 10 + 5) + 5 == 53
    with pytest.raises(ValueError, match="four"):
        launch.validate_pilot_cap(jobs + (jobs[0],))


@pytest.mark.parametrize("mutation", ["cap61", "five-jobs"])
def test_m18_mutants_fail_independent_pilot_cap_test(tmp_path, monkeypatch, mutation):
    source = Path(launch.__file__).read_text()
    if mutation == "cap61":
        source = source.replace('JOB_BODY = ', 'PILOT_LOGICAL_SESSION_CAP = 61\nJOB_BODY = ', 1)
        source = source.replace('!= (10, 5, 5, 60)', '!= (10, 5, 5, 61)', 1)
    else:
        source = source.replace('    return jobs\n', '    return jobs + (jobs[0],)\n', 1)
    module = ModuleType("tools.pegasus._b5_mutant")
    module.__package__ = "tools.pegasus"
    module.__file__ = launch.__file__
    monkeypatch.setitem(sys.modules, module.__name__, module)
    exec(compile(source, module.__file__, "exec"), module.__dict__)
    monkeypatch.setitem(globals(), "launch", module)
    with pytest.raises(AssertionError):
        test_pilot_cap_is_literal_60_and_four_jobs_53_sessions(tmp_path)


@pytest.mark.parametrize("name,value", [("B_EVALUATIONS", 11), ("N_EVAL", 6),
                                      ("BLOCK_STOCK_SESSIONS", 6),
                                      ("PILOT_LOGICAL_SESSION_CAP", 61)])
def test_changed_budget_cannot_construct_pilot(tmp_path, monkeypatch, name, value):
    monkeypatch.setattr(launch, name, value)
    with pytest.raises(ValueError, match="budgets changed"):
        _pilot(tmp_path)


@pytest.mark.parametrize("field,value", [("workload", "balanced"), ("series", 2),
                                       ("block", 2), ("mode", "block-stock")])
def test_pilot_coordinates_cannot_expand(tmp_path, field, value):
    tree, jobs = _pilot(tmp_path)
    with pytest.raises(ValueError, match="pilot requires"):
        launch.qsub_argv(replace(jobs[0], **{field: value}), tree)


@pytest.mark.parametrize("value", ["has space", "has,comma", "has\ttab", "has\nnewline"])
def test_qsub_rejects_ambiguous_path_values(tmp_path, value):
    tree, jobs = _pilot(tmp_path)
    with pytest.raises(ValueError, match="qsub -v"):
        launch.qsub_argv(replace(jobs[0], ledger_root=tmp_path / value), tree)


@pytest.mark.parametrize("root", ["submit-tree", "main-repo"])
@pytest.mark.parametrize("field", ["ledger_root", "evidence_root"])
def test_output_paths_must_be_outside_both_repositories(tmp_path, root, field):
    tree, jobs = _pilot(tmp_path)
    with pytest.raises(ValueError, match="inside a repository"):
        launch.qsub_argv(replace(jobs[0], **{field: tmp_path / root / "output"}), tree)


def test_dry_run_prints_final_argv_without_runner_or_mkdir(tmp_path, monkeypatch, capsys):
    tree, jobs = _pilot(tmp_path)
    def forbidden(*args, **kwargs):
        pytest.fail("dry-run invoked subprocess or mkdir")
    monkeypatch.setattr(launch.subprocess, "run", forbidden)
    monkeypatch.setattr(Path, "mkdir", forbidden)
    assert launch.launch(jobs, tree, submit=False, runner=forbidden) == 0
    records = [json.loads(line) for line in capsys.readouterr().out.splitlines()]
    assert len(records) == 4
    for record, job in zip(records, jobs):
        assert record["environment"] == _expected_environment(tmp_path, job.arm)
        assert record["argv"] == launch.qsub_argv(job, tree)
    assert not (tmp_path / "evidence").exists()
    assert not (tmp_path / "ledgers").exists()


@pytest.mark.parametrize("rc", [0, 9])
def test_submit_only_mkdir_then_argv_runner(tmp_path, rc):
    tree, jobs = _pilot(tmp_path)
    calls = []
    def runner(argv, *, cwd):
        evidence = Path(argv[argv.index("-o") + 1]).parent
        assert evidence.is_dir() and list(evidence.iterdir()) == []
        assert evidence.stat().st_mode & 0o777 == 0o700
        assert cwd == tree.repo
        calls.append(argv)
        return SimpleNamespace(returncode=rc)
    assert launch.launch(jobs, tree, submit=True, runner=runner) == rc
    assert calls == [launch.qsub_argv(j, tree) for j in (jobs if rc == 0 else jobs[:1])]
    assert not (tmp_path / "ledgers").exists()


def test_preexisting_attempt_rejected_before_any_submission(tmp_path):
    tree, jobs = _pilot(tmp_path)
    jobs[-1].evidence_root.mkdir(parents=True)
    with pytest.raises(ValueError, match="not fresh"):
        launch.launch(jobs, tree, submit=True, runner=lambda *a, **k: pytest.fail("qsub"))
    assert not jobs[0].evidence_root.exists()


def test_main_dry_run_validates_tree_and_prints_four_jobs(tmp_path, monkeypatch, capsys):
    tree, _ = _pilot(tmp_path)
    checked = []
    def validate(repo, head):
        checked.append((repo, head))
        return tree
    monkeypatch.setattr(launch, "validate_submit_tree", validate)
    monkeypatch.setattr(launch.subprocess, "run", lambda *a, **k: pytest.fail("qsub"))
    assert launch.main([
        "--repo-root", str(tree.repo), "--expected-head", tree.expected_head,
        "--thirdparty-source-root", str(tree.thirdparty_source_root),
        "--ledger-root", str(tmp_path / "ledgers"),
        "--evidence-root", str(tmp_path / "evidence"),
        "--knowledge-manifest", str(tmp_path / "knowledge.json"),
        "--knowledge-classification", "known_result_conditioned_derivative",
        "--knowledge-de-novo-claim", "false", "--dry-run",
    ]) == 0
    assert checked == [(tree.repo, tree.expected_head)]
    assert len(capsys.readouterr().out.splitlines()) == 4
    assert not (tmp_path / "evidence").exists()



def test_target_checkout_pin_m28(submit_tree, monkeypatch):
    repo, head, _ = submit_tree
    target = repo / "orchestrator/campaign/p3_s4_loop.py"
    target_pin = target.read_text().split('"')[1]
    monkeypatch.setattr(launch.p3_s4_loop, "PIN", "e" * 40)
    assert launch.validate_submit_tree(repo, head).repo == repo
    monkeypatch.setattr(launch.p3_s4_loop, "PIN", target_pin)
    target.write_text('PIN = "' + "f" * 40 + '"\n')
    with pytest.raises(ValueError, match="pin mismatch"):
        launch.validate_submit_tree(repo, head)

def test_target_pin_mutant_m28(submit_tree, monkeypatch):
    repo, head, _ = submit_tree
    target = repo / "orchestrator/campaign/p3_s4_loop.py"
    monkeypatch.setattr(launch.p3_s4_loop, "PIN", target.read_text().split('"')[1])
    source = Path(launch.__file__).read_text()
    assert source.count('!= pins[0]:') == 1
    mutant = ModuleType("tools.pegasus._b5_pin_mutant")
    mutant.__package__, mutant.__file__ = "tools.pegasus", launch.__file__
    monkeypatch.setitem(sys.modules, mutant.__name__, mutant)
    exec(compile(source.replace('!= pins[0]:', '!= p3_s4_loop.PIN:'), launch.__file__, "exec"), mutant.__dict__)
    monkeypatch.setitem(globals(), "launch", mutant)
    with pytest.raises(pytest.fail.Exception):
        test_validate_submit_tree_rejects_ccbench_pin(submit_tree, monkeypatch)


def _run() -> int:
    """Keep this test file covered by the repository plain-runner contract."""
    return pytest.main([__file__, "-q"])


if __name__ == "__main__":
    raise SystemExit(_run())
