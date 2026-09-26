import json
from collections import Counter
from dataclasses import replace
from pathlib import Path
import subprocess
import sys
from types import SimpleNamespace, ModuleType

import pytest

from tools.pegasus import b5_contrast_launch as launch
from orchestrator.campaign import b5_generator_contrast as core


def _git(path, *args, input=None):
    return subprocess.run(["git", "-C", str(path), *args], input=input,
                          capture_output=True, text=True, check=True).stdout.strip()


def test_v2_schedule_pairs_and_six_orders_twice():
    schedule = launch.registered_v2_schedule()
    assert schedule["cohort"] == core.COHORT_REGISTERED_V2
    assert len(schedule["orders"]) == 24
    for workload in ("write-heavy", "balanced"):
        orders = [row["order"] for row in schedule["orders"] if row["workload"] == workload]
        assert sorted({order: orders.count(order) for order in orders}.values()) == [2] * 6
    assert all(row["workload"] in ("write-heavy", "balanced") for row in schedule["jobs"])


@pytest.mark.parametrize("reply,expected", [("outage", "outage"), ("success", "ready")])
def test_v2_login_429_does_not_count_a_and_empty_output_does(tmp_path, reply, expected):
    ledger = core.SeriesLedger.create(tmp_path / "ledger", {"cohort": core.COHORT_REGISTERED_V2,
                          "arm": "llm", "workload": "write-heavy", "series": 1, "block": 1})
    ledger.append("series-start", a=0, b=0)
    ledger.append("stock-start", a=0, b=0, outcome="certified", quality="normal",
                  fitness_tps=100., bench_payload={"leading_indicators": {"abort_rate": 0.1}},
                  campaign_root="/tmp/stock")
    job = launch.RegisteredJob("job", 1, "series-step", "llm", "write-heavy", 1, 1,
                               ledger.root, tmp_path / "evidence")
    class FakeParent:
        def __init__(self, *_args): pass
        def tick(self, _item, a, _request, handshake):
            if reply == "outage":
                (handshake / f"outage-{a}.json").write_text('{"api_error_status":429}')
            return reply
    driver = launch.V2Launcher((job,), {"job": launch.SubmitTree(tmp_path, "0" * 40, tmp_path)},
                               parent_config={"series": [{"job_id": "job", "workload": "write-heavy",
                                                          "series": 1, "block": 1,
                                                          "ledger_root": str(ledger.root)}]},
                               state_root=tmp_path / "state", max_active_series=1,
                               parent_factory=FakeParent)
    assert driver._drive_parent(job, ledger, 1, first=False) == expected
    opportunities = [e for e in ledger.events if e["kind"] == "proposal-opportunity"]
    rejected = [e for e in ledger.events if e["kind"] == "proposal-rejected"]
    assert len(opportunities) == len(rejected) == (0 if reply == "outage" else 1)
    if rejected:
        assert rejected[0]["provenance"]["reason"] == "empty-output"


@pytest.mark.parametrize("source,first", [("round", False), ("critic", False),
                                          ("round", True)])
def test_v2_model_mismatch_ends_without_consuming_a(tmp_path, source, first):
    ledger = core.SeriesLedger.create(tmp_path / "ledger", {"cohort": core.COHORT_REGISTERED_V2,
                          "arm": "llm", "workload": "write-heavy", "series": 1, "block": 1})
    ledger.append("series-start", a=0, b=0)
    ledger.append("stock-start", a=0, b=0, outcome="certified", quality="normal",
                  fitness_tps=100., bench_payload={"leading_indicators": {"abort_rate": 0.1}},
                  campaign_root="/tmp/stock")
    if source == "critic":
        ledger.append("proposal-opportunity", a=1, b=0)
        ledger.append("evaluation-result", a=1, b=1, outcome="certified", quality="normal",
                      fitness_tps=100., bench_payload={"leading_indicators": {"abort_rate": 0.1}},
                      campaign_root="/tmp/evaluation", whiteboard_entry={
                          "iteration": 1, "direction": "up", "magnitude": "small",
                          "result": "certified", "delta_pct": None})
    a = 2 if source == "critic" else 1
    prior_a = sum(e["kind"] == "proposal-opportunity" for e in ledger.events)
    materials = tmp_path / "materials"
    job = launch.RegisteredJob("job", 1, "series-step", "llm", "write-heavy", 1, 1,
                               ledger.root, tmp_path / "evidence")

    class MismatchedParent:
        def __init__(self, *_args): pass
        def tick(self, _item, requested_a, request, _handshake):
            k = core._read_json(request)["next_evaluation"] - 1
            directory = materials / (f"critic-{k}" if source == "critic"
                                     else f"round-{requested_a}")
            directory.mkdir(parents=True)
            (directory / "model-mismatch.md").write_text("unexpected model\n")
            return "success"

    driver = launch.V2Launcher((job,), {"job": launch.SubmitTree(tmp_path, "0" * 40, tmp_path)},
                               parent_config={"series": [{"job_id": "job", "workload": "write-heavy",
                                                          "series": 1, "block": 1,
                                                          "ledger_root": str(ledger.root),
                                                          "materials_root": str(materials)}]},
                               state_root=tmp_path / "state", max_active_series=1,
                               parent_factory=MismatchedParent)
    assert driver._drive_parent(job, ledger, a, first=first) == "done"
    assert sum(e["kind"] == "proposal-opportunity" for e in ledger.events) == prior_a
    assert not [e for e in ledger.events if e["kind"] == "proposal-rejected"]
    if first:
        assert core._read_json(ledger.root / "handshake" / f"stop-{a}.json") == {
            "reason": "unclassified-missing"}
    else:
        assert ledger.events[-1]["kind"] == "series-end"
        assert ledger.events[-1]["reason"] == "unclassified-missing"


def test_v2_three_parent_outages_leave_a_b_and_missing_unchanged(tmp_path):
    ledger = core.SeriesLedger.create(tmp_path / "ledger", {"cohort": core.COHORT_REGISTERED_V2,
                          "arm": "llm", "workload": "write-heavy", "series": 1, "block": 1})
    ledger.append("series-start", a=0, b=0)
    ledger.append("stock-start", a=0, b=0, outcome="certified", quality="normal",
                  fitness_tps=100., bench_payload={"leading_indicators": {"abort_rate": 0.1}},
                  campaign_root="/tmp/stock")
    job = launch.RegisteredJob("job", 1, "series-step", "llm", "write-heavy", 1, 1,
                               ledger.root, tmp_path / "evidence")
    class ParentWithOutages:
        calls = 0
        def __init__(self, *_args): pass
        def tick(self, _item, _a, _request, _handshake):
            self.calls += 1
            return "outage" if self.calls <= 3 else "success"
    driver = launch.V2Launcher((job,), {"job": launch.SubmitTree(tmp_path, "0" * 40, tmp_path)},
                               parent_config={"series": [{"job_id": "job", "workload": "write-heavy",
                                                          "series": 1, "block": 1,
                                                          "ledger_root": str(ledger.root)}]},
                               state_root=tmp_path / "state", max_active_series=1,
                               parent_factory=ParentWithOutages)
    for _ in range(3):
        assert driver._drive_parent(job, ledger, 1, first=False) == "outage"
        assert not [e for e in ledger.events if e["kind"] in
                    {"proposal-opportunity", "evaluation-result", "series-end"}]
    assert driver._drive_parent(job, ledger, 1, first=False) == "ready"
    assert [e["a"] for e in ledger.events if e["kind"] == "proposal-opportunity"] == [1]
    assert not [e for e in ledger.events if e["kind"] in {"evaluation-result", "series-end"}]


def test_v2_three_429s_restart_stock_then_accept_same_a_and_evaluate(tmp_path, monkeypatch):
    from concurrent.futures import ThreadPoolExecutor
    import time
    from orchestrator.tests.test_b5_generator_contrast import FakeRunner, ROOT
    from tools.pegasus.b5_llm_parent import Parent, FORBIDDEN

    for key in FORBIDDEN:
        monkeypatch.delenv(key, raising=False)
    monkeypatch.setattr(core, "LLM_POLL_S", 0.001)
    real_time = time.time

    def exercise(label, outages):
        root = tmp_path / label
        root.mkdir()
        stock = launch.RegisteredJob("stock", 0, "block-stock", "stock", "write-heavy", 1, 1,
                                     root / "stock", root / "stock-evidence")
        stock_ledger = core.SeriesLedger.create(stock.ledger_root, {"cohort": core.COHORT_REGISTERED_V2})
        stock_ledger.append("series-end", reason="b-complete")
        job = launch.RegisteredJob("llm", 1, "series-step", "llm", "write-heavy", 1, 1,
                                   root / "ledger", root / "evidence",
                                   launch.K2(root / "manifest", "de_novo", "true"))
        for name, content in (("header", "request {a} {request_path}\n"),
                              ("resume", "request {a} {request_path}\n"),
                              ("template", "# template\n## 2. fixed\ntext\n")):
            (root / name).write_text(content)
        config = {"effect_checkout": str(ROOT), "settings": "settings.json", "model": "fixture",
                  "header": str(root / "header"), "resume": str(root / "resume"),
                  "template": str(root / "template"), "manifest": str(root / "manifest"),
                  "series": [{"job_id": "llm", "workload": "write-heavy", "series": 1,
                              "block": 1, "ledger_root": str(job.ledger_root),
                              "materials_root": str(root), "session_id": "fixed-session"}]}
        runner = FakeRunner()
        launches = []
        clock = [real_time()]
        monkeypatch.setattr(launch.time, "time", lambda: clock[0])

        class Child:
            pid = 12345
            def __init__(self, publish=None): self.publish = publish
            def poll(self):
                if self.publish:
                    self.publish()
                    self.publish = None
                return 0

        def spawn(argv, **kwargs):
            index = len(launches)
            launches.append(argv)
            publish = None
            if index < outages:
                answer = {"is_error": True, "api_error_status": 429}
            else:
                request = Path(kwargs["stdin"].read().decode().splitlines()[0].split()[-1])
                expected = json.loads(request.read_text())
                handshake = request.parent
                inputs = {"planner_input": {"whiteboard": [], "current_perf": expected["current_perf"]},
                          "coder_input": {"whiteboard": [], "baseline": expected["baseline"]}}
                proposal = {"planner": {"axis": core.loop_driver.MARKER_ID,
                                        "direction": "decrease", "magnitude": "small"},
                            "coder": {"proposal": {"axis": core.loop_driver.MARKER_ID, "value": 20,
                                                   "implementation": "double now_backoff = 20;",
                                                   "justification": "fixture", "confidence": "low"},
                                      "knowledge_use": [], "classification": "de_novo",
                                      "data_boundary_report": {"instruction_like_content_detected": False,
                                                               "details": "fixture"}},
                            "prior_critic_reverse": True}
                def publish():
                    (handshake / "inputs-1.json").write_text(json.dumps(inputs))
                    (handshake / "proposal-1.json").write_text(json.dumps(proposal))
                answer = {"is_error": False}
            kwargs["stdout"].write(json.dumps(answer).encode())
            return Child(publish)

        def parent_factory(parent_config, state_dir):
            return Parent(parent_config, state_dir, spawn=spawn, alive=lambda _pid: False,
                          now=lambda: clock[0])

        with ThreadPoolExecutor(max_workers=1) as pool:
            futures = []
            def submit(argv, **_kwargs):
                evidence = Path(argv[argv.index("-o") + 1]).parent
                env = dict(part.split("=", 1) for part in argv[argv.index("-v") + 1].split(","))
                def compute():
                    try:
                        core.run_series_step("llm", "write-heavy", 1, 1,
                            step=env["IZANAGI_S4_B5_STEP"], ledger_root=job.ledger_root,
                            prebuild_receipt=root / "receipt", repo_root=ROOT,
                            k2=core.K2Args(root / "manifest"), runner=runner)
                        rc = 0
                    except Exception:
                        rc = 1
                        raise
                    finally:
                        (evidence / "compute-result.json").write_text(json.dumps({"driver_rc": rc}))
                futures.append(pool.submit(compute))
                return subprocess.CompletedProcess(argv, 0, "123.server\n", "")

            thirdparty = root / "thirdparty"
            thirdparty.mkdir()
            driver = launch.V2Launcher((stock, job), {"stock": launch.SubmitTree(ROOT, "0" * 40, ROOT, thirdparty),
                                                   "llm": launch.SubmitTree(ROOT, "0" * 40, ROOT, thirdparty)},
                parent_config=config, state_root=root / "state", max_active_series=1,
                submitter=submit, parent_factory=parent_factory)
            for _ in range(5000):
                status = driver.tick()
                clock[0] += 901 if status.get("llm") == "outage" else 0.01
                if (job.ledger_root / "header.json").exists():
                    events = core.SeriesLedger(job.ledger_root).events
                    if any(e["kind"] == "evaluation-result" for e in events):
                        break
                time.sleep(0.001)
            else:
                handshake = job.ledger_root / "handshake"
                handshake.mkdir(exist_ok=True)
                (handshake / "outage-1.json").write_text('{"api_error_status":429}')
                pytest.fail("first evaluation did not finish")
            for future in futures:
                future.result()
        ledger = core.SeriesLedger(job.ledger_root)
        assert ledger.header["purpose"] == "registered"
        assert ledger.header["cohort"] == core.COHORT_REGISTERED_V2
        assert ledger.header["prereg_version"] == core.PREREG_VERSION_V2
        parent_state = root / "state/parents/llm"
        state = json.loads((parent_state / "state.json").read_text())
        attempts = {a: sum(path.is_dir() for path in parent_state.glob(f"a-{a}-attempt-*"))
                    for a in (1, 2)}
        return ledger, runner, launches, attempts, state

    baseline, baseline_runner, baseline_launches, baseline_attempts, baseline_state = exercise("baseline", 0)
    resumed, resumed_runner, resumed_launches, resumed_attempts, resumed_state = exercise("resumed", 3)
    count = lambda ledger, kind: sum(e["kind"] == kind for e in ledger.events)
    assert [count(resumed, kind) for kind in ("proposal-opportunity", "evaluation-result",
                                              "series-end")] == [1, 1, 0]
    assert [count(resumed, kind) for kind in ("proposal-opportunity", "evaluation-result",
                                              "series-end")] == [
        count(baseline, kind) for kind in ("proposal-opportunity", "evaluation-result", "series-end")]
    assert count(resumed, "stock-start") == 4 and count(baseline, "stock-start") == 1
    assert len({e["campaign_root"] for e in resumed.events if e["kind"] == "stock-start"}) == 4
    assert [call["kind"] for call in resumed_runner.calls] == ["stock-start"] * 4 + ["search"]
    assert len(resumed_launches) == len(baseline_launches) + 3
    assert baseline_attempts == {1: 1, 2: 1}
    assert resumed_attempts == {1: 4, 2: 1}
    assert "--session-id" in baseline_launches[0] and "--resume" in baseline_launches[1]
    assert resumed_state["failures"] == baseline_state["failures"] == 0
    assert resumed_state["success_a"] == baseline_state["success_a"] == 1
    assert [e["quality"] for e in resumed.events if e["kind"] == "evaluation-result"] == ["normal"]
    assert all("--resume" in argv for argv in resumed_launches[1:])
    assert [e["a"] for e in resumed.events if e["kind"] == "proposal-opportunity"] == [1]


def test_v2_qsub_no_answer_stays_fail_closed_on_restart(tmp_path):
    repo = tmp_path / "repo"
    repo.mkdir()
    thirdparty = tmp_path / "thirdparty"
    thirdparty.mkdir()
    job = launch.RegisteredJob("stock", 0, "block-stock", "stock", "write-heavy", 1, 1,
                               tmp_path / "ledger", tmp_path / "evidence")
    tree = launch.SubmitTree(repo, "0" * 40, repo, thirdparty)
    calls = []
    def submit(argv, **_kwargs):
        calls.append(argv)
        return subprocess.CompletedProcess(argv, 0, "", "")
    driver = launch.V2Launcher((job,), {"stock": tree}, parent_config={"series": []},
                               state_root=tmp_path / "state", max_active_series=1,
                               submitter=submit)
    with pytest.raises(RuntimeError, match="did not answer"):
        driver._submit(job)
    with pytest.raises(RuntimeError, match="unanswered qsub"):
        driver._submit(job)
    assert len(calls) == 1


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
    trees_by_arm = {
        arm: launch.SubmitTree(tmp_path / f"submit-tree-{arm}", "a" * 40,
                               tmp_path / "main-repo", thirdparty)
        for arm in launch.PILOT_ARMS
    }
    jobs = launch.pilot_jobs("write-heavy", tmp_path / "ledgers", tmp_path / "evidence",
                             launch.K2(tmp_path / "knowledge.json",
                                       "known_result_conditioned_derivative", "false"))
    return trees_by_arm, jobs


def _expected_environment(tmp_path, arm):
    name = "block-stock" if arm == "stock" else arm
    env = {
        "IZANAGI_S4_REPO_ROOT": str(tmp_path / f"submit-tree-{arm}"),
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
    trees_by_arm, jobs = _pilot(tmp_path)
    assert [job.arm for job in jobs] == ["random", "sweep-matched", "llm", "stock"]
    for job, arm in zip(jobs, ["random", "sweep-matched", "llm", "stock"]):
        env = _expected_environment(tmp_path, arm)
        assert launch.build_job_environment(job, trees_by_arm[job.arm]) == env
        evidence = env["IZANAGI_S4_EVIDENCE_ROOT"]
        expected = ["qsub", "-v", ",".join(f"{k}={v}" for k, v in env.items()),
                    "-l", "elapstim_req=03:00:00" if arm == "stock" else "elapstim_req=08:00:00",
                    "-o", evidence + "/job.stdout", "-e", evidence + "/job.stderr",
                    "tools/pegasus/p3_s4_loop_pegasus.sh"]
        assert launch.qsub_argv(job, trees_by_arm[job.arm]) == expected


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
    trees_by_arm, jobs = _pilot(tmp_path)
    with pytest.raises(ValueError, match="pilot requires"):
        launch.qsub_argv(replace(jobs[0], **{field: value}), trees_by_arm[jobs[0].arm])


@pytest.mark.parametrize("value", ["has space", "has,comma", "has\ttab", "has\nnewline"])
def test_qsub_rejects_ambiguous_path_values(tmp_path, value):
    trees_by_arm, jobs = _pilot(tmp_path)
    with pytest.raises(ValueError, match="qsub -v"):
        launch.qsub_argv(replace(jobs[0], ledger_root=tmp_path / value), trees_by_arm[jobs[0].arm])


@pytest.mark.parametrize("root", ["submit-tree-random", "main-repo"])
@pytest.mark.parametrize("field", ["ledger_root", "evidence_root"])
def test_output_paths_must_be_outside_both_repositories(tmp_path, root, field):
    trees_by_arm, jobs = _pilot(tmp_path)
    with pytest.raises(ValueError, match="inside a repository"):
        launch.qsub_argv(replace(jobs[0], **{field: tmp_path / root / "output"}), trees_by_arm[jobs[0].arm])


def test_dry_run_prints_final_argv_without_runner_or_mkdir(tmp_path, monkeypatch, capsys):
    trees_by_arm, jobs = _pilot(tmp_path)
    def forbidden(*args, **kwargs):
        pytest.fail("dry-run invoked subprocess or mkdir")
    monkeypatch.setattr(launch.subprocess, "run", forbidden)
    monkeypatch.setattr(Path, "mkdir", forbidden)
    assert launch.launch(jobs, trees_by_arm, submit=False, runner=forbidden) == 0
    records = [json.loads(line) for line in capsys.readouterr().out.splitlines()]
    assert len(records) == 4
    for record, job in zip(records, jobs):
        assert record["environment"] == _expected_environment(tmp_path, job.arm)
        assert record["argv"] == launch.qsub_argv(job, trees_by_arm[job.arm])
    assert not (tmp_path / "evidence").exists()
    assert not (tmp_path / "ledgers").exists()


@pytest.mark.parametrize("rc", [0, 9])
def test_submit_only_mkdir_then_argv_runner(tmp_path, rc):
    trees_by_arm, jobs = _pilot(tmp_path)
    calls = []
    def runner(argv, *, cwd):
        evidence = Path(argv[argv.index("-o") + 1]).parent
        assert evidence.is_dir() and list(evidence.iterdir()) == []
        assert evidence.stat().st_mode & 0o777 == 0o700
        env = dict(value.split("=", 1) for value in argv[argv.index("-v") + 1].split(","))
        assert env["IZANAGI_S4_REPO_ROOT"] == str(cwd)
        calls.append((argv, cwd))
        return SimpleNamespace(returncode=rc)
    assert launch.launch(jobs, trees_by_arm, submit=True, runner=runner) == rc
    assert calls == [(launch.qsub_argv(j, trees_by_arm[j.arm]), trees_by_arm[j.arm].repo)
                     for j in (jobs if rc == 0 else jobs[:1])]
    assert not (tmp_path / "ledgers").exists()


def test_preexisting_attempt_rejected_before_any_submission(tmp_path):
    trees_by_arm, jobs = _pilot(tmp_path)
    jobs[-1].evidence_root.mkdir(parents=True)
    with pytest.raises(ValueError, match="not fresh"):
        launch.launch(jobs, trees_by_arm, submit=True, runner=lambda *a, **k: pytest.fail("qsub"))
    assert not jobs[0].evidence_root.exists()


def test_main_dry_run_validates_tree_and_prints_four_jobs(tmp_path, monkeypatch, capsys):
    trees_by_arm, jobs = _pilot(tmp_path)
    expected_head = "a" * 40
    checked = []
    def validate(repo, head):
        checked.append((repo, head))
        return next(replace(tree, thirdparty_source_root=None)
                    for tree in trees_by_arm.values() if tree.repo == repo)
    monkeypatch.setattr(launch, "validate_submit_tree", validate)
    monkeypatch.setattr(launch.subprocess, "run", lambda *a, **k: pytest.fail("qsub"))
    assert launch.main([
        *[value for arm in launch.PILOT_ARMS
          for value in (f"--repo-root-{arm}", str(trees_by_arm[arm].repo))],
        "--expected-head", expected_head,
        "--thirdparty-source-root", str(tmp_path / "thirdparty"),
        "--ledger-root", str(tmp_path / "ledgers"),
        "--evidence-root", str(tmp_path / "evidence"),
        "--knowledge-manifest", str(tmp_path / "knowledge.json"),
        "--knowledge-classification", "known_result_conditioned_derivative",
        "--knowledge-de-novo-claim", "false", "--dry-run",
    ]) == 0
    assert checked == [(trees_by_arm[arm].repo, expected_head) for arm in launch.PILOT_ARMS]
    records = [json.loads(line) for line in capsys.readouterr().out.splitlines()]
    assert len(records) == 4
    for record, job in zip(records, jobs):
        assert record["arm"] == job.arm
        assert record["environment"] == _expected_environment(tmp_path, job.arm)
        assert record["argv"] == launch.qsub_argv(job, trees_by_arm[job.arm])
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


def test_registered_schedule_coordinates():
    schedule = launch.registered_schedule()
    assert schedule == launch.registered_schedule()
    assert schedule["cohort"] == "b5-registered-v1"
    assert len(schedule["orders"]) == 36
    expected_blocks = {1: 1, 2: 1, 3: 1, 4: 1, 5: 2, 6: 2,
                       7: 2, 8: 2, 9: 3, 10: 3, 11: 3, 12: 3}
    for workload in ("write-heavy", "balanced", "read-heavy"):
        rows = [r for r in schedule["orders"] if r["workload"] == workload]
        assert {r["series"]: r["block"] for r in rows} == expected_blocks
    # A literal anchor distinguishes D-2's ascending X/Y placement.
    assert [r["order"] for r in schedule["orders"][:4]] == ["LSR", "RLS", "RSL", "SLR"]
    letters = {"llm": "L", "random": "R", "sweep-matched": "S"}
    for row in schedule["orders"]:
        jobs = sorted((j for j in schedule["jobs"] if j["mode"] == "series"
                       and (j["workload"], j["series"]) == (row["workload"], row["series"])),
                      key=lambda j: j["stage"])
        assert [j["stage"] for j in jobs] == [1, 2, 3]
        assert [j["block"] for j in jobs] == [row["block"]] * 3
        assert "".join(letters[j["arm"]] for j in jobs) == row["order"]


def test_registered_schedule_llm_four_per_stage():
    schedule = launch.registered_schedule()
    assert Counter((j["block"], j["stage"]) for j in schedule["jobs"] if j["arm"] == "llm") == {
        (b, s): 4 for b in (1, 2, 3) for s in (1, 2, 3)}


def test_registered_schedule_six_orders_twice():
    schedule = launch.registered_schedule()
    expected = Counter({order: 2 for order in ("LRS", "SRL", "LSR", "RSL", "RLS", "SLR")})
    for workload in ("write-heavy", "balanced", "read-heavy"):
        rows = [r for r in schedule["orders"] if r["workload"] == workload]
        assert Counter(r["order"] for r in rows) == expected
        for block in (1, 2, 3):
            orders = [r["order"] for r in rows if r["block"] == block]
            assert len(orders) == 4
            for baseline in "RS":
                assert Counter(o.index("L") < o.index(baseline) for o in orders) == {True: 2, False: 2}


def test_registered_stage_job_counts():
    jobs = launch.registered_schedule()["jobs"]
    assert len(jobs) == len({j["job_id"] for j in jobs}) == 117
    assert Counter(j["mode"] for j in jobs) == {"series": 108, "block-stock": 9}
    assert Counter((j["block"], j["stage"]) for j in jobs) == {
        (b, s): count for b in (1, 2, 3) for s, count in ((1, 12), (2, 15), (3, 12))}
    stocks = [j for j in jobs if j["arm"] == "stock"]
    assert Counter((j["workload"], j["block"]) for j in stocks) == {
        (w, b): 1 for w in ("write-heavy", "balanced", "read-heavy") for b in (1, 2, 3)}
    assert all(j["series"] == j["block"] and j["stage"] == 2 for j in stocks)


def test_registered_walltime_decimal_boundaries():
    for factor, series, stock in (
        ("2.5", (53148, "14:45:48"), (13618, "03:46:58")),
        ("3", (63777, "17:42:57"), (16341, "04:32:21")),
        ("4.06", (86312, "23:58:32"), (22115, "06:08:35")),
        ("0.000001", (1, "00:00:01"), (1, "00:00:01")),
        ("1.0000000000000000000000000000001", (21260, "05:54:20"), (5448, "01:30:48")),
    ):
        assert launch.registered_walltimes(factor) == {
            "series": dict(zip(("seconds", "walltime"), series)),
            "block-stock": dict(zip(("seconds", "walltime"), stock))}
    for invalid in ("0", "-1", "4.06000000000000000001", "NaN", "sNaN", "Infinity", "-Infinity", "bad"):
        with pytest.raises(ValueError, match="walltime factor"):
            launch.registered_walltimes(invalid)


@pytest.fixture
def registered_stage(tmp_path, submit_tree):
    # Real independent Git checkouts, including CCBench and target PIN. No
    # validate_submit_tree stub: both positive and negative admissions run it.
    import shutil
    repo, head, _ = submit_tree
    k2 = launch.K2(tmp_path / "knowledge.json", "known_result_conditioned_derivative", "false")
    jobs = launch.registered_jobs(2, 2, tmp_path / "ledgers", tmp_path / "evidence", k2)
    mapping = {}
    for job in jobs:
        target = tmp_path / job.job_id
        shutil.copytree(repo, target)
        mapping[job.job_id] = str(target)
    thirdparty = tmp_path / "thirdparty"
    thirdparty.mkdir()
    options = dict(expected_head=head, thirdparty_source_root=thirdparty, walltime_factor="2.5")
    return jobs, mapping, options


def test_registered_job_specific_submit_trees(registered_stage, capsys):
    jobs, mapping, options = registered_stage
    assert launch.launch_registered(jobs, mapping, submit=False, **options) == 0
    records = [json.loads(line) for line in capsys.readouterr().out.splitlines()]
    assert len(records) == 15
    assert {r["job_id"]: r["cwd"] for r in records} == mapping
    assert len({r["environment"]["IZANAGI_S4_REPO_ROOT"] for r in records}) == 15
    for row, job in zip(records, jobs):
        expected_id = (f"b2-{job.workload}-stock" if job.arm == "stock" else
                       f"b2-{job.workload}-r{job.series:02d}-{job.arm}")
        assert row["job_id"] == expected_id
        assert row["cwd"] == mapping[expected_id]
    duplicate = {**mapping, jobs[-1].job_id: mapping[jobs[0].job_id]}
    with pytest.raises(ValueError, match="distinct"):
        launch.launch_registered(jobs, duplicate, submit=False, **options)


def test_registered_environment_exact(registered_stage, tmp_path, capsys):
    jobs, mapping, options = registered_stage
    assert launch.launch_registered(jobs, mapping, submit=False, **options) == 0
    rows = [json.loads(line) for line in capsys.readouterr().out.splitlines()]
    for row, job in zip(rows, jobs):
        suffix = Path("b5-registered-v1/block-2") / job.workload
        suffix /= "block-stock" if job.arm == "stock" else f"r{job.series:02d}/{job.arm}"
        evidence = tmp_path / "evidence" / suffix
        env = {
            "IZANAGI_S4_REPO_ROOT": mapping[job.job_id],
            "IZANAGI_S4_EXPECTED_HEAD": options["expected_head"],
            "IZANAGI_S4_EVIDENCE_ROOT": str(evidence),
            "IZANAGI_S4_THIRDPARTY_SOURCE_ROOT": str(tmp_path / "thirdparty"),
            "IZANAGI_S4_B5_MODE": "block-stock" if job.arm == "stock" else "series",
            "IZANAGI_S4_B5_ARM": job.arm,
            "IZANAGI_S4_B5_WORKLOAD": job.workload,
            "IZANAGI_S4_B5_SERIES": str(job.series),
            "IZANAGI_S4_B5_BLOCK": "2",
            "IZANAGI_S4_B5_LEDGER_ROOT": str(tmp_path / "ledgers" / suffix),
            "IZANAGI_S4_B5_PURPOSE": "registered",
        }
        if job.arm == "llm":
            env.update({"IZANAGI_S4_KNOWLEDGE_MANIFEST": str(tmp_path / "knowledge.json"),
                        "IZANAGI_S4_CODER_ROLE": "coder-v4-autonomous-k2",
                        "IZANAGI_S4_KNOWLEDGE_CLASSIFICATION": "known_result_conditioned_derivative",
                        "IZANAGI_S4_KNOWLEDGE_DE_NOVO_CLAIM": "false"})
        assert row["environment"] == env
        assert row["argv"] == ["qsub", "-v", ",".join(f"{k}={v}" for k, v in env.items()),
                               "-l", "elapstim_req=" + ("03:46:58" if job.arm == "stock" else "14:45:48"),
                               "-o", str(evidence / "job.stdout"), "-e", str(evidence / "job.stderr"),
                               "tools/pegasus/p3_s4_loop_pegasus.sh"]


def test_registered_dry_run_has_no_side_effects(registered_stage, tmp_path, monkeypatch, capsys):
    jobs, mapping, options = registered_stage
    before = sorted(str(p.relative_to(tmp_path)) for p in tmp_path.rglob("*"))
    def forbidden(*args, **kwargs):
        pytest.fail("registered dry-run attempted mkdir or qsub")
    monkeypatch.setattr(Path, "mkdir", forbidden)
    assert launch.launch_registered(jobs, mapping, submit=False, runner=forbidden, **options) == 0
    assert len(capsys.readouterr().out.splitlines()) == 15
    assert sorted(str(p.relative_to(tmp_path)) for p in tmp_path.rglob("*")) == before


@pytest.mark.parametrize("failure", ["head", "dirty", "pin", "fresh", "overlap", "other-tree", "missing-map"])
def test_registered_checks_all_jobs_before_submission(registered_stage, failure):
    jobs, mapping, options = registered_stage
    last_repo = Path(mapping[jobs[-1].job_id])
    if failure == "head":
        options["expected_head"] = "e" * 40
    elif failure == "dirty":
        (last_repo / "tracked.txt").write_text("dirty")
    elif failure == "pin":
        (last_repo / "orchestrator/campaign/p3_s4_loop.py").write_text('PIN = "' + 'e' * 40 + '"\n')
    elif failure == "fresh":
        jobs[-1].ledger_root.mkdir(parents=True)
    elif failure == "overlap":
        jobs = jobs[:-1] + (replace(jobs[-1], ledger_root=jobs[0].evidence_root / "child"),)
    elif failure == "other-tree":
        jobs = (replace(jobs[0], ledger_root=last_repo / "output"),) + jobs[1:]
    else:
        del mapping[jobs[-1].job_id]
    def forbidden(*args, **kwargs):
        pytest.fail("qsub before all admissions")
    with pytest.raises(ValueError):
        launch.launch_registered(jobs, mapping, submit=True, runner=forbidden, **options)
    assert not jobs[0].evidence_root.exists()


@pytest.mark.parametrize("fail_at", [None, 2])
def test_registered_submit_stops_at_first_failure(registered_stage, fail_at):
    jobs, mapping, options = registered_stage
    calls = []
    def runner(argv, *, cwd):
        evidence = Path(argv[argv.index("-o") + 1]).parent
        assert evidence.is_dir() and list(evidence.iterdir()) == []
        assert evidence.stat().st_mode & 0o777 == 0o700
        calls.append(str(cwd))
        return SimpleNamespace(returncode=9 if len(calls) == fail_at else 0)
    assert launch.launch_registered(jobs, mapping, submit=True, runner=runner, **options) == (9 if fail_at else 0)
    assert calls == [mapping[j.job_id] for j in (jobs[:fail_at] if fail_at else jobs)]
    assert all(not j.ledger_root.exists() for j in jobs)
    if fail_at:
        assert all(not j.evidence_root.exists() for j in jobs[fail_at:])


def test_registered_cli_schedule_and_dry_run(registered_stage, tmp_path, capsys):
    jobs, mapping, options = registered_stage
    assert launch.main(["registered-schedule"]) == 0
    assert json.loads(capsys.readouterr().out) == launch.registered_schedule()
    path = tmp_path / "trees.json"
    path.write_text(json.dumps(mapping))
    assert launch.main(["registered", "--block", "2", "--stage", "2", "--walltime-factor", "2.5",
                        "--submit-trees", str(path), "--expected-head", options["expected_head"],
                        "--ledger-root", str(tmp_path / "ledgers"), "--evidence-root", str(tmp_path / "evidence"),
                        "--thirdparty-source-root", str(options["thirdparty_source_root"]),
                        "--knowledge-manifest", str(tmp_path / "knowledge.json"),
                        "--knowledge-classification", "known_result_conditioned_derivative",
                        "--knowledge-de-novo-claim", "false", "--dry-run"]) == 0
    assert {r["job_id"] for r in map(json.loads, capsys.readouterr().out.splitlines())} == set(mapping)
    assert all(not j.evidence_root.exists() for j in jobs)


def _run() -> int:
    """Keep this test file covered by the repository plain-runner contract."""
    return pytest.main([__file__, "-q"])


if __name__ == "__main__":
    raise SystemExit(_run())
