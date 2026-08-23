"""受入 shard の activation、割付け、6 段 gate、外形不変の回帰テスト。"""
from __future__ import annotations

import ast
import inspect
import itertools
import sys
import time
import xml.etree.ElementTree as ET
from pathlib import Path

import pytest

from tools import acceptance_shards as SH
from tools import run_tests as RT


_SESSION_ROOT = Path("/acceptance-shard-fixture")


def _records() -> tuple[SH.ItemRecord, ...]:
    return tuple(sorted((
        SH.ItemRecord("orchestrator/tests/test_a.py::test_a1", "orchestrator/tests/test_a.py", "group-a"),
        SH.ItemRecord("orchestrator/tests/test_a.py::test_a2", "orchestrator/tests/test_a.py", "group-a"),
        SH.ItemRecord("orchestrator/tests/test_b.py::test_b", "orchestrator/tests/test_b.py", "group-b"),
        SH.ItemRecord("orchestrator/tests/test_c.py::test_c", "orchestrator/tests/test_c.py", None),
        SH.ItemRecord("orchestrator/tests/test_d.py::test_d", "orchestrator/tests/test_d.py", None),
    )))


def _payload(records):
    return [
        {"file": record.file, "group": record.group, "nodeid": record.nodeid}
        for record in records
    ]


def _reports(records=None, *, k=2, scheduler="loadgroup"):
    records = _records() if records is None else tuple(records)
    assignment = SH.allocate(records, k)
    reports = []
    for index in range(k):
        selected = list(assignment.selected[index])
        selected_records = {
            record.nodeid: record for record in records if record.nodeid in selected
        }
        groups = sorted({
            record.group for record in selected_records.values()
            if record.group is not None
        })
        reports.append({
            "schema_version": SH.SCHEMA,
            "shard_count": k,
            "shard_index": index,
            "pytest_rc": 0,
            "observed_universe": _payload(records),
            "selected": selected,
            "finished": list(selected),
            "effective_scheduler": scheduler,
            "terminal_counts": {
                "passed": len(selected), "failed": 0, "error": 0,
                "skipped": 0, "xfailed": 0, "xpassed": 0,
            },
            "failures": [],
            "group_to_workers": {group: ["gw0"] for group in groups},
            "worker_occupancy": {"gw0": {"items": len(selected), "duration_s": 1.0}},
            "junit_path": str(_SESSION_ROOT / f"shard-{index}" / "junit.xml"),
            "worker_collection_digests": [SH._digest(_payload(records))] * 2,
        })
    return reports


def _merge(reports, *, login=None, process=None):
    if login is None:
        login = [record.nodeid for record in _records()]
    if process is None:
        process = {index: 0 for index in range(len(reports))}
    return SH.merge_reports(
        expected_k=2,
        reports=reports,
        process_results=process,
        login_universe=login,
        expected_junit_paths=[
            _SESSION_ROOT / f"shard-{index}" / "junit.xml"
            for index in range(2)
        ],
    )


def _refresh_selected_evidence(reports):
    by_node = {record.nodeid: record for record in _records()}
    for report in reports:
        selected = report["selected"]
        report["worker_occupancy"] = {
            "gw0": {"items": len(selected), "duration_s": 1.0}
        }
        report["group_to_workers"] = {
            group: ["gw0"]
            for group in sorted({
                by_node[nodeid].group
                for nodeid in selected
                if by_node[nodeid].group is not None
            })
        }
        report["terminal_counts"] = {
            "passed": len(selected), "failed": 0, "error": 0,
            "skipped": 0, "xfailed": 0, "xpassed": 0,
        }
        report["worker_collection_digests"] = [
            SH._digest(report["observed_universe"])
        ] * len(report["worker_collection_digests"])


def test_runner_exclusion_helper_forwards_colliding_keyword_names():
    def target(value, *, exclusions, function):
        return value, exclusions, function

    assert RT._call_with_runner_exclusions(
        (),
        target,
        "payload",
        exclusions="callee-exclusions",
        function="callee-function",
    ) == ("payload", "callee-exclusions", "callee-function")


@pytest.mark.parametrize("value, expected", [(None, 1), ("", 1), ("1", 1), ("2", 2), ("3", 3)])
def test_activation_closed_positive_values(value, expected):
    environ = {} if value is None else {RT._ACCEPTANCE_SHARDS_ENV: value}
    assert RT._acceptance_shard_count(environ) == expected


@pytest.mark.parametrize("value", ["0", "4", " 1", "1 ", "02", "serial"])
def test_activation_invalid_values_are_rc16_inputs(value):
    with pytest.raises(ValueError):
        RT._acceptance_shard_count({RT._ACCEPTANCE_SHARDS_ENV: value})


def test_invalid_activation_returns_rc16_before_execution(monkeypatch):
    monkeypatch.setenv(RT._ACCEPTANCE_SHARDS_ENV, "4")
    monkeypatch.setattr(
        RT,
        "_normalize_args",
        lambda *_args: (_ for _ in ()).throw(AssertionError("must stop before pytest shape")),
    )
    assert RT.main([], site=RT.site_policy.PEGASUS_LOGIN) == 16


def test_internal_spec_is_consumed_without_becoming_pytest_target(tmp_path):
    session = tmp_path / ".izanagi-acceptance-shards" / "nonce"
    argv = [
        f"{RT._INTERNAL_SHARD_SESSION_OPTION}={session}",
        f"{RT._INTERNAL_SHARD_COUNT_OPTION}=3",
        f"{RT._INTERNAL_SHARD_INDEX_OPTION}=1",
    ]
    remaining, spec = RT._consume_internal_shard_spec(argv)
    assert remaining == []
    assert spec == SH.InternalSpec(session.resolve(), 3, 1)


@pytest.mark.parametrize("has_exclusions", [False, True])
def test_internal_shard_command_keeps_default_suite_root(
    monkeypatch, tmp_path, has_exclusions,
):
    repo = tmp_path / "repo"
    default_target = repo / "orchestrator" / "tests"
    default_target.mkdir(parents=True)
    session = tmp_path / ".izanagi-acceptance-shards" / "nonce"
    shard = session / "shard-0"
    shard.mkdir(parents=True)
    captured = {}

    def fake_call(command, **kwargs):
        captured["command"] = list(command)
        captured["kwargs"] = kwargs
        return 0

    monkeypatch.setattr(RT, "_xdist_version", lambda: "3.8.0")
    monkeypatch.setattr(RT, "_xdist_runtime_importable", lambda: True)
    monkeypatch.setattr(RT, "_default_nproc", lambda **_kwargs: 4)
    monkeypatch.setattr(RT.subprocess, "call", fake_call)
    monkeypatch.setattr(RT, "_REPO", str(repo))
    monkeypatch.setattr(RT, "_DEFAULT_TARGET", str(default_target))
    exclusions = ()
    if has_exclusions:
        exclusions = (RT._PermanentExclusion(
            path=default_target / "synthetic_excluded.py",
            reason="synthetic exclusion mechanism test",
            release_condition="synthetic release condition",
            ruling="{{D:synthetic-exclusion}}",
        ),)
    monkeypatch.setattr(RT, "_PERMANENT_FULL_SUITE_EXCLUSIONS", exclusions)
    monkeypatch.setenv(RT._RUNNER_EXCLUSION_ENV, "stale-parent-evidence")
    monkeypatch.setattr(
        SH, "shared_root_for_repo", lambda _repo: session.parent.resolve(),
    )
    rc = RT._run_internal_acceptance_shard(
        SH.InternalSpec(session, 2, 0),
        resolved_site=RT.site_policy.PEGASUS_COMPUTE,
        args=[],
        exclusions=RT._PERMANENT_FULL_SUITE_EXCLUSIONS,
    )
    assert rc == 0
    command = captured["command"]
    assert command.count(RT._DEFAULT_TARGET) == 1
    assert not any(
        token.endswith("test_a.py") or "test_a.py::" in token for token in command
    )
    assert captured["kwargs"]["cwd"] == str(repo)
    child_env = captured["kwargs"]["env"]
    if exclusions:
        assert child_env[RT._RUNNER_EXCLUSION_ENV] == (
            RT._SELECTION_CONTRACT.serialize_payload(exclusions)
        )
    else:
        assert RT._RUNNER_EXCLUSION_ENV not in child_env


def test_explicit_shards_reject_nonlogin_without_fallback(monkeypatch):
    monkeypatch.setenv(RT._ACCEPTANCE_SHARDS_ENV, "2")
    monkeypatch.setenv("PYTEST_ADDOPTS", "")
    monkeypatch.setenv("PYTEST_PLUGINS", "")
    forbidden = lambda *_args, **_kwargs: (_ for _ in ()).throw(
        AssertionError("K=1 execution must not be used")
    )
    monkeypatch.setattr(RT, "_preflight_unstaged_deletions", forbidden)
    assert RT.main([], site=RT.site_policy.OTHER, dispatch_fn=forbidden) == 16


def test_valid_login_activation_enters_composite_with_empty_outer_argv(monkeypatch):
    monkeypatch.setenv(RT._ACCEPTANCE_SHARDS_ENV, "2")
    monkeypatch.setenv("PYTEST_ADDOPTS", "")
    monkeypatch.setenv("PYTEST_PLUGINS", "")
    monkeypatch.setattr(RT, "_bounded_scope_membership", lambda: None)
    monkeypatch.setattr(RT, "_preflight_unstaged_deletions", lambda *_args: 0)
    monkeypatch.setattr(RT, "_preflight_ruleops", lambda *_args: 0)
    monkeypatch.setattr(RT, "_preflight_submodule", lambda *_args: 0)
    observed = {}

    def fake_composite(dispatch_fn, args, **kwargs):
        observed["dispatch_fn"] = dispatch_fn
        observed["args"] = list(args)
        observed["kwargs"] = kwargs
        return 7

    monkeypatch.setattr(RT, "_dispatch_result", fake_composite)
    marker = object()
    assert RT.main(
        [], site=RT.site_policy.PEGASUS_LOGIN, dispatch_fn=marker,
    ) == 7
    assert observed["dispatch_fn"] is marker
    assert observed["args"] == []
    assert observed["kwargs"]["shard_count"] == 2
    assert observed["kwargs"]["exclusions"] == RT._PERMANENT_FULL_SUITE_EXCLUSIONS


@pytest.mark.parametrize(
    "raw_args,force_dispatch,accepted",
    [
        ([], False, True),
        (["--force-dispatch"], True, True),
        (["orchestrator/tests/test_a.py"], False, False),
        (["--force-dispatch", "orchestrator/tests/test_a.py"], True, False),
        (["--force-dispatch", "--force-dispatch"], True, False),
    ],
)
def test_shard_outer_args_accept_only_empty_or_force_dispatch(
    raw_args, force_dispatch, accepted,
):
    assert RT._validate_shard_outer_args(raw_args, force_dispatch) is accepted


def test_force_dispatch_enters_shard_composite_with_empty_internal_argv(
    monkeypatch,
):
    monkeypatch.setenv(RT._ACCEPTANCE_SHARDS_ENV, "2")
    monkeypatch.setenv("PYTEST_ADDOPTS", "")
    monkeypatch.setenv("PYTEST_PLUGINS", "")
    monkeypatch.setattr(RT, "_bounded_scope_membership", lambda: None)
    monkeypatch.setattr(RT, "_preflight_unstaged_deletions", lambda *_args: 0)
    monkeypatch.setattr(RT, "_preflight_ruleops", lambda *_args: 0)
    monkeypatch.setattr(RT, "_preflight_submodule", lambda *_args: 0)
    observed = {}

    def fake_composite(dispatch_fn, args, **kwargs):
        observed["args"] = list(args)
        observed["shard_count"] = kwargs["shard_count"]
        return 0

    monkeypatch.setattr(RT, "_dispatch_result", fake_composite)
    assert RT.main(
        ["--force-dispatch"], site=RT.site_policy.PEGASUS_LOGIN,
    ) == 0
    assert observed == {"args": [], "shard_count": 2}


def test_login_collection_uses_remaining_absolute_deadline(monkeypatch, tmp_path):
    repo = tmp_path / "repo"
    target = repo / "orchestrator" / "tests"
    target.mkdir(parents=True)
    session = tmp_path / "session"
    session.mkdir()
    observed = {}

    def fake_run(command, **kwargs):
        observed["command"] = list(command)
        observed["timeout"] = kwargs["timeout"]
        return RT.subprocess.CompletedProcess(
            command, 0, "orchestrator/tests/test_a.py::test_a\n", "",
        )

    monkeypatch.setattr(RT, "_REPO", str(repo))
    monkeypatch.setattr(RT, "_DEFAULT_TARGET", str(target))
    monkeypatch.setattr(RT.subprocess, "run", fake_run)
    deadline_at = time.monotonic() + 10.0
    rc, universe = RT._collect_login_universe(session, (), deadline_at)
    assert rc == 0
    assert universe == ("orchestrator/tests/test_a.py::test_a",)
    assert 0 < observed["timeout"] <= 10.0
    assert observed["command"].count(str(target)) == 1


def test_parallel_parent_uses_one_absolute_deadline_contract():
    signature = inspect.signature(SH.run_parallel)
    assert "deadline_at" in signature.parameters
    assert "deadline_s" not in signature.parameters
    source = inspect.getsource(SH.run_parallel)
    assert "time.monotonic() +" not in source
    assert "deadline_at=deadline_at" in inspect.getsource(SH._dispatch_worker)
    assert "deadline_at=deadline_at" in source
    assert RT._ACCEPTANCE_SHARD_DEADLINE_S > 900 + 3600 + 300 + 60


def test_allocator_joins_file_group_bipartite_component():
    records = tuple(sorted((
        SH.ItemRecord("a.py::test_1", "a.py", "x"),
        SH.ItemRecord("b.py::test_1", "b.py", "x"),
        SH.ItemRecord("b.py::test_2", "b.py", "y"),
        SH.ItemRecord("c.py::test_1", "c.py", "y"),
        SH.ItemRecord("d.py::test_1", "d.py", None),
    )))
    components = SH._components(records)
    joined = next(component for component in components if "x" in component["groups"])
    assert joined["groups"] == ("x", "y")
    assert joined["files"] == ("a.py", "b.py", "c.py")


def test_allocator_separates_groups_when_k_covers_group_count_and_is_deterministic():
    records = _records()
    baseline = SH.allocate(records, 2)
    assert all(
        SH.allocate(permutation, 2) == baseline
        for permutation in itertools.permutations(records)
    )
    node_to_shard = {
        nodeid: index
        for index, nodeids in enumerate(baseline.selected)
        for nodeid in nodeids
    }
    assert node_to_shard["orchestrator/tests/test_a.py::test_a1"] != node_to_shard[
        "orchestrator/tests/test_b.py::test_b"
    ]
    assert baseline.loads == tuple(
        len(nodeids) for nodeids in baseline.selected
    )


def test_allocator_k3_places_three_exclusive_groups_on_distinct_shards():
    records = _records() + (
        SH.ItemRecord("orchestrator/tests/test_e.py::test_e", "orchestrator/tests/test_e.py", "group-c"),
    )
    assignment = SH.allocate(records, 3)
    node_to_shard = {
        nodeid: index
        for index, nodeids in enumerate(assignment.selected)
        for nodeid in nodeids
    }
    assert len({
        node_to_shard["orchestrator/tests/test_a.py::test_a1"],
        node_to_shard["orchestrator/tests/test_b.py::test_b"],
        node_to_shard["orchestrator/tests/test_e.py::test_e"],
    }) == 3


def test_loadgroup_suffix_is_removed_only_for_matching_observed_group():
    base = "orchestrator/tests/test_a.py::test_a1"
    groups = {base: "group-a"}
    assert SH._normalize_runtime_nodeid(base + "@group-a", groups) == base
    assert SH._normalize_runtime_nodeid(base + "@other", groups) == base + "@other"
    assert SH._normalize_runtime_nodeid(base, groups) == base


def test_m1_observed_universe_gate_has_independent_killer():
    records = _records()
    assert SH._observed_universes_gate((records, records))
    assert not SH._observed_universes_gate((records, records[:-1]))
    reports = _reports()
    reports[1]["observed_universe"] = reports[1]["observed_universe"][:-1]
    reports[1]["worker_collection_digests"] = [
        SH._digest(reports[1]["observed_universe"])
    ] * 2
    assert _merge(reports).reason == "observed-universe-mismatch"


def test_m2_report_index_gate_has_missing_duplicate_and_positive_controls():
    assert SH._report_index_gate(({"shard_index": 0}, {"shard_index": 1}), 2)
    assert not SH._report_index_gate(({"shard_index": 0},), 2)
    assert not SH._report_index_gate(({"shard_index": 0}, {"shard_index": 0}), 2)


def test_m3_group_closure_gate_has_independent_killer_and_positive_control():
    records = _records()
    valid = SH.allocate(records, 2).selected
    assert SH.assignment_closure_gate(records, valid)
    split = [list(valid[0]), list(valid[1])]
    first = "orchestrator/tests/test_a.py::test_a1"
    second = "orchestrator/tests/test_a.py::test_a2"
    for nodeid in (first, second):
        for shard in split:
            if nodeid in shard:
                shard.remove(nodeid)
    split[0].append(first)
    split[1].append(second)
    assert not SH.assignment_closure_gate(records, split)


def test_m4_finished_gate_has_independent_killer():
    assert SH._finished_gate(("a", "b"), ("b", "a"))
    assert not SH._finished_gate(("a", "b"), ("a",))


def test_m5_login_universe_gate_has_independent_killer():
    assert SH._login_universe_gate(("a", "b"), ("b", "a"))
    assert not SH._login_universe_gate(("a",), ("a", "b"))
    reports = _reports()
    wrong_login = [record.nodeid for record in _records()[:-1]]
    assert _merge(reports, login=wrong_login).reason == "login-universe-mismatch"


def test_m1_m5_simultaneous_mutation_has_a_combined_killer():
    reports = _reports()
    reports[1]["observed_universe"] = reports[1]["observed_universe"][:-1]
    reports[1]["worker_collection_digests"] = [
        SH._digest(reports[1]["observed_universe"])
    ] * 2
    wrong_login = [record.nodeid for record in _records()[:-1]]
    result = _merge(reports, login=wrong_login)
    assert result.rc == 16


def test_merge_six_gate_positive_control_and_rc_mapping():
    reports = _reports()
    green = _merge(reports)
    assert green.rc == 0
    assert green.reason == "ok"
    assert green.scheduler == "loadgroup"
    reports[1]["pytest_rc"] = 1
    red = _merge(reports, process={0: 0, 1: 1})
    assert red.rc == 1
    assert red.reason == "ok"


def test_merge_rejects_whole_shard_omission_before_other_gates():
    result = SH.merge_reports(
        expected_k=2,
        reports=_reports()[:1],
        process_results={0: 0},
        login_universe=[record.nodeid for record in _records()],
        expected_junit_paths=[
            _SESSION_ROOT / f"shard-{index}" / "junit.xml"
            for index in range(2)
        ],
    )
    assert (result.rc, result.reason) == (16, "report-index-set")


def test_merge_rejects_selected_partition_substitution():
    reports = _reports()
    reports[0]["selected"][0] = "orchestrator/tests/test_z.py::test_z"
    reports[0]["finished"] = list(reports[0]["selected"])
    assert _merge(reports).reason == "selected-partition"


def test_merge_rejects_group_split_at_gate_four():
    reports = _reports()
    a1 = "orchestrator/tests/test_a.py::test_a1"
    a2 = "orchestrator/tests/test_a.py::test_a2"
    for report in reports:
        report["selected"] = [node for node in report["selected"] if node not in {a1, a2}]
    reports[0]["selected"].append(a1)
    reports[1]["selected"].append(a2)
    for report in reports:
        report["finished"] = list(report["selected"])
    _refresh_selected_evidence(reports)
    assert _merge(reports).reason == "assignment-closure"


def test_merge_rejects_unfinished_selected_node():
    reports = _reports()
    reports[0]["finished"] = reports[0]["finished"][:-1]
    assert _merge(reports).reason == "finished-selected-mismatch"


@pytest.mark.parametrize("schedulers", [("unknown", "unknown"), ("loadgroup", "serial")])
def test_m6_merge_rejects_unknown_and_mixed_scheduler(schedulers):
    reports = _reports()
    reports[0]["effective_scheduler"], reports[1]["effective_scheduler"] = schedulers
    assert _merge(reports).reason == "scheduler"


def test_report_evidence_accepts_consistent_durations_and_rejects_item_mismatch():
    reports = _reports()
    reports[0]["worker_occupancy"] = {
        "gw0": {"items": len(reports[0]["selected"]), "duration_s": 0.000001}
    }
    assert (_merge(reports).rc, _merge(reports).reason) == (0, "ok")
    reports[0]["worker_occupancy"] = {
        "gw0": {"items": 999, "duration_s": 9999.0}
    }
    assert (_merge(reports).rc, _merge(reports).reason) == (16, "report-invalid")


@pytest.mark.parametrize(
    "field,value",
    [
        ("group_to_workers", []),
        ("group_to_workers", {}),
        ("worker_occupancy", {}),
        ("worker_collection_digests", []),
        ("worker_collection_digests", ["wrong-digest"]),
        ("junit_path", ""),
        ("terminal_counts", {}),
    ],
)
def test_report_evidence_rejects_empty_diagnostic_payloads(field, value):
    reports = _reports()
    reports[0][field] = value
    assert (_merge(reports).rc, _merge(reports).reason) == (16, "report-invalid")


def test_report_evidence_rejects_unknown_group_worker_and_nonfinite_duration():
    reports = _reports()
    group = next(iter(reports[0]["group_to_workers"]))
    reports[0]["group_to_workers"][group] = ["ghost-worker"]
    assert _merge(reports).reason == "report-invalid"

    reports = _reports()
    reports[0]["worker_occupancy"]["gw0"]["duration_s"] = float("nan")
    assert _merge(reports).reason == "report-invalid"


def test_report_schema_requires_worker_assignment_diagnostics():
    assert {"group_to_workers", "worker_occupancy"} <= SH._REPORT_FIELDS
    reports = _reports()
    del reports[0]["worker_occupancy"]
    assert _merge(reports).reason == "report-invalid"


def test_merged_output_has_exactly_one_scheduler_marker(capsys):
    SH._emit_merged(_merge(_reports()))
    captured = capsys.readouterr()
    assert captured.err == ""
    assert captured.out.count(SH.SCHEDULER_PREFIX) == 1
    assert "| " + SH.SCHEDULER_PREFIX not in captured.out


def test_infra_gate_emits_no_scheduler_marker(capsys):
    SH._emit_merged(SH.MergeResult(16, "fixture-failure"))
    captured = capsys.readouterr()
    assert SH.SCHEDULER_PREFIX not in captured.out + captured.err


def test_session_artifacts_are_outside_repo(monkeypatch, tmp_path):
    repo = tmp_path / "repo"
    repo.mkdir()
    git_dir = repo / ".git"
    git_dir.mkdir()
    monkeypatch.setattr(SH, "_git_common_dir", lambda _repo: git_dir.resolve())
    session = SH.create_session(repo, 2)
    assert not SH._is_within(session, repo.resolve())
    assert session.parent.name == ".izanagi-acceptance-shards"
    assert (session / "shard-0").is_dir()
    assert (session / "shard-1").is_dir()


@pytest.mark.parametrize(
    "relative",
    [Path(".claude/worktrees"), Path(".codex/worktrees")],
)
def test_shared_root_rejects_land_control_containers(tmp_path, relative):
    main_repo = tmp_path / "repo"
    worktree = main_repo / relative / "wave"
    shared_root = main_repo / relative / SH._SESSION_PREFIX
    with pytest.raises(SH.ShardError, match="artifact-root-in-control-container"):
        SH._validate_shared_root(
            worktree.resolve(), main_repo.resolve(), shared_root.resolve(),
        )


def test_shared_root_guard_tracks_land_control_containers(monkeypatch, tmp_path):
    added = b"future/worktrees"
    monkeypatch.setattr(
        SH._dev_wave_land,
        "_CONTROL_CONTAINERS",
        SH._dev_wave_land._CONTROL_CONTAINERS + (added,),
    )
    main_repo = (tmp_path / "repo").resolve()
    shared_root = (main_repo / "future/worktrees" / SH._SESSION_PREFIX).resolve()
    with pytest.raises(SH.ShardError, match="artifact-root-in-control-container"):
        SH._validate_shared_root(main_repo, main_repo, shared_root)


def test_worktree_shared_root_is_derived_outside_control_container(
    monkeypatch, tmp_path,
):
    main_repo = tmp_path / "repo"
    git_dir = main_repo / ".git"
    worktree = main_repo / ".claude/worktrees/wave"
    git_dir.mkdir(parents=True)
    worktree.mkdir(parents=True)
    monkeypatch.setattr(SH, "_git_common_dir", lambda _repo: git_dir.resolve())
    shared_root = SH.shared_root_for_repo(worktree)
    assert shared_root == (tmp_path / SH._SESSION_PREFIX).resolve()
    assert not SH._is_within(
        shared_root, (main_repo / ".claude/worktrees").resolve(),
    )
    assert not SH._is_within(
        shared_root, (main_repo / ".codex/worktrees").resolve(),
    )


def test_shared_root_inside_repo_guard_remains(tmp_path):
    repo = (tmp_path / "repo").resolve()
    shared_root = repo / "artifacts" / SH._SESSION_PREFIX
    with pytest.raises(SH.ShardError, match="artifact-root-inside-repo"):
        SH._validate_shared_root(repo, repo, shared_root)


def test_parallel_implementation_uses_fork_processes_not_threads():
    tree = ast.parse(Path(SH.__file__).read_text(encoding="utf-8"))
    calls = [node for node in ast.walk(tree) if isinstance(node, ast.Call)]
    contexts = [
        node for node in calls
        if isinstance(node.func, ast.Attribute)
        and node.func.attr == "get_context"
    ]
    assert any(
        len(node.args) == 1
        and isinstance(node.args[0], ast.Constant)
        and node.args[0].value == "fork"
        for node in contexts
    )
    assert not any(
        isinstance(node.func, ast.Attribute) and node.func.attr == "Thread"
        for node in calls
    )


def test_shard_implementation_has_no_manifest_or_barrier_protocol():
    source = Path(SH.__file__).read_text(encoding="utf-8")
    executable = "\n".join(
        line for line in source.splitlines()
        if not line.lstrip().startswith("#")
    )
    assert "multiprocessing.Barrier" not in executable
    assert "manifest.json" not in executable
    assert "collection.json" not in executable


def test_composite_defers_parent_task_record_and_strips_shard_sidecar():
    source = inspect.getsource(RT._dispatch_result)
    assert "shard_environ.pop(_TASK_RUN_SIDECAR_ENV" in source
    assert 'shard_environ[_TASK_RUN_AUTO_RECORD_ENV] = "0"' in source
    assert "acceptance_shards.run_parallel" in source


def test_all_dispatch_workers_start_before_parent_wait_or_collection_result_use():
    source = inspect.getsource(SH.run_parallel)
    tree = ast.parse(source)
    calls = [node for node in ast.walk(tree) if isinstance(node, ast.Call)]
    start_lines = [
        node.lineno for node in calls
        if isinstance(node.func, ast.Attribute) and node.func.attr == "start"
    ]
    blocking_lines = [
        node.lineno for node in calls
        if (
            isinstance(node.func, ast.Attribute) and node.func.attr in {"join", "recv"}
        )
        or (isinstance(node.func, ast.Name) and node.func.id == "wait_connections")
    ]
    collect_line = next(
        node.lineno for node in calls
        if isinstance(node.func, ast.Name) and node.func.id == "collect_login"
    )
    assert len(start_lines) == 1
    assert start_lines[0] < collect_line < min(blocking_lines)


def test_junit_merge_recomputes_counts_and_has_malformed_control(tmp_path):
    paths = []
    for index, attrs in enumerate((
        {"tests": "2", "failures": "0", "errors": "0", "skipped": "1", "time": "1.25"},
        {"tests": "1", "failures": "1", "errors": "0", "skipped": "0", "time": "0.5"},
    )):
        root = ET.Element("testsuite", attrs)
        path = tmp_path / f"{index}.xml"
        path.write_bytes(ET.tostring(root, encoding="utf-8"))
        paths.append(path)
    destination = tmp_path / "merged.xml"
    SH.merge_junit(paths, destination, expected_tests=3)
    merged = ET.parse(destination).getroot()
    assert merged.attrib == {
        "errors": "0", "failures": "1", "skipped": "1", "tests": "3", "time": "1.75",
    }
    with pytest.raises(SH.ShardError, match="junit-tests"):
        SH.merge_junit(paths, tmp_path / "bad.xml", expected_tests=4)


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-q"]))
