import ast
import json
import re
import shlex
import sys
from pathlib import Path


REPO = Path(__file__).resolve().parents[2]
JOB = REPO / "tools/pegasus/a5_second_boot_backoff_sweep.sh"
SUBMITTER = REPO / "tools/pegasus/submit_a5_second_boot_backoff_sweep.sh"
REGISTRY = REPO / "tools/pegasus/admission_registry.json"
EXPECTED_WORKLOADS = ("write-heavy", "balanced")


def _shell_array(source: str, name: str) -> tuple[str, ...]:
    assignment_pattern = re.compile(
        rf"(?m)^[ \t]*(?:(?:declare|readonly|typeset)"
        rf"(?:[ \t]+-[A-Za-z]+)*[ \t]+)?{re.escape(name)}"
        rf"(?:\[[^\]\n]*\])?[ \t]*\+?="
    )
    assignments = list(assignment_pattern.finditer(source))
    if len(assignments) != 1:
        raise AssertionError(
            f"expected exactly one assignment or append for {name}, "
            f"found {len(assignments)}"
        )
    array_pattern = re.compile(
        rf"(?ms)^[ \t]*{re.escape(name)}[ \t]*=[ \t]*"
        rf"\((?P<body>.*?)\)[ \t]*(?:\#.*)?$"
    )
    arrays = list(array_pattern.finditer(source))
    if len(arrays) != 1 or arrays[0].start() != assignments[0].start():
        raise AssertionError(f"missing unique literal shell array: {name}")
    return tuple(shlex.split(arrays[0].group("body"), comments=True, posix=True))


def _shell_case_patterns(source: str) -> tuple[str, ...]:
    lexer = shlex.shlex(source, posix=True, punctuation_chars="|")
    lexer.whitespace_split = True
    tokens = list(lexer)
    if not tokens or tokens[0] == "|" or tokens[-1] == "|":
        raise AssertionError(f"invalid shell case pattern list: {source!r}")
    if any(token != "|" for token in tokens[1::2]):
        raise AssertionError(f"invalid shell case alternation: {source!r}")
    return tuple(tokens[::2])


def _job_workload_case(source: str) -> tuple[str, ...]:
    match = re.search(
        r'case "\$WORKLOAD" in\n(?P<body>.*?)\n(?:\s*)esac',
        source,
        flags=re.DOTALL,
    )
    if match is None:
        raise AssertionError("missing literal WORKLOAD case gate")
    accepted = []
    for clause in match.group("body").split(";;"):
        candidate = clause.strip()
        if not candidate:
            continue
        pattern_source, separator, _commands = candidate.partition(")")
        if not separator:
            raise AssertionError(f"unterminated WORKLOAD case clause: {candidate!r}")
        patterns = _shell_case_patterns(pattern_source.strip())
        if patterns == ("*",):
            continue
        accepted.extend(patterns)
    return tuple(accepted)


def _finalizer_tree(source: str) -> ast.Module:
    blocks = re.findall(r"<<'PY'\n(?P<body>.*?)\nPY(?:\n|$)", source, re.DOTALL)
    matches = [block for block in blocks if "BASELINE_FLAGS" in block]
    if len(matches) != 1:
        raise AssertionError(f"expected one Python finalizer, found {len(matches)}")
    return ast.parse(matches[0])


def _target_writes_name(target: ast.AST, name: str) -> bool:
    if isinstance(target, ast.Name):
        return target.id == name
    if isinstance(target, (ast.Attribute, ast.Subscript, ast.Starred)):
        return _target_writes_name(target.value, name)
    if isinstance(target, (ast.List, ast.Tuple)):
        return any(_target_writes_name(item, name) for item in target.elts)
    return False


def _mutation_sites(tree: ast.AST, name: str) -> list[ast.AST]:
    sites = []
    mutating_methods = {
        "__delitem__", "__setitem__", "add", "append", "clear", "discard",
        "difference_update", "extend", "insert", "intersection_update", "pop",
        "popitem", "remove", "reverse", "setdefault", "sort",
        "symmetric_difference_update", "update",
    }
    for node in ast.walk(tree):
        targets: list[ast.AST] = []
        if isinstance(node, ast.Assign):
            targets = node.targets
        elif isinstance(node, (ast.AnnAssign, ast.AugAssign, ast.NamedExpr)):
            targets = [node.target]
        elif isinstance(node, ast.Delete):
            targets = node.targets
        if any(_target_writes_name(target, name) for target in targets):
            sites.append(node)
        if (isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
                and node.func.attr in mutating_methods
                and _target_writes_name(node.func.value, name)):
            sites.append(node)
    return sites


def _single_assignment(tree: ast.AST, name: str) -> ast.Assign:
    sites = _mutation_sites(tree, name)
    if len(sites) != 1:
        raise AssertionError(
            f"expected exactly one assignment or mutation for {name}, found {len(sites)}"
        )
    assignment = sites[0]
    if (not isinstance(assignment, ast.Assign) or len(assignment.targets) != 1
            or not isinstance(assignment.targets[0], ast.Name)
            or assignment.targets[0].id != name):
        raise AssertionError(f"{name} must have one direct assignment")
    return assignment


def _assert_assignment_expression(tree: ast.AST, name: str, expression: str) -> ast.Assign:
    assignment = _single_assignment(tree, name)
    expected = ast.parse(expression, mode="eval").body
    assert ast.dump(assignment.value, include_attributes=False) == ast.dump(
        expected, include_attributes=False
    )
    return assignment


def _if_with_system_exit(tree: ast.AST, message: str) -> ast.If:
    matches = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.If):
            continue
        for statement in node.body:
            if (isinstance(statement, ast.Raise)
                    and isinstance(statement.exc, ast.Call)
                    and isinstance(statement.exc.func, ast.Name)
                    and statement.exc.func.id == "SystemExit"
                    and len(statement.exc.args) == 1
                    and isinstance(statement.exc.args[0], ast.Constant)
                    and statement.exc.args[0].value == message):
                matches.append(node)
    if len(matches) != 1:
        raise AssertionError(
            f"expected one active completeness check for {message!r}, found {len(matches)}"
        )
    return matches[0]


def _integer_assignment(source: str, name: str) -> int:
    match = re.search(rf"(?m)^{re.escape(name)}=([0-9]+)$", source)
    if match is None:
        raise AssertionError(f"missing integer shell assignment: {name}")
    return int(match.group(1))


def _pbs_walltime_seconds(source: str) -> int:
    match = re.search(
        r"(?m)^#PBS -l elapstim_req=([0-9]{2}):([0-9]{2}):([0-9]{2})$",
        source,
    )
    if match is None:
        raise AssertionError("missing canonical PBS elapstim_req")
    hours, minutes, seconds = map(int, match.groups())
    return hours * 3600 + minutes * 60 + seconds


def _assert_submitter_workloads(source: str) -> None:
    workloads = _shell_array(source, "WORKLOADS")
    assert len(workloads) == len(EXPECTED_WORKLOADS)
    assert set(workloads) == set(EXPECTED_WORKLOADS)


def _assert_job_workloads(source: str) -> None:
    workloads = _job_workload_case(source)
    assert len(workloads) == len(EXPECTED_WORKLOADS)
    assert set(workloads) == set(EXPECTED_WORKLOADS)


def _assert_no_backoff_denominator(source: str) -> None:
    tree = _finalizer_tree(source)
    flags_assignment = _single_assignment(tree, "BASELINE_FLAGS")
    assert ast.literal_eval(flags_assignment.value) == {
        "BACK_OFF": 0, "BACKOFF_FIXED": -1,
    }
    baseline_assignment = _assert_assignment_expression(
        tree, "baseline", "selected_by_flags(BASELINE_FLAGS)"
    )
    assert flags_assignment.lineno < baseline_assignment.lineno
    assert (
        'target = selected_by_flags({"BACK_OFF": 1, "BACKOFF_FIXED": target_fixed_us})'
        in source
    )


def _assert_complete_committed_sweep(source: str) -> None:
    tree = _finalizer_tree(source)
    genome_count = _single_assignment(tree, "EXPECTED_GENOME_COUNT")
    assert ast.literal_eval(genome_count.value) == 8
    tps_count = _single_assignment(tree, "EXPECTED_TPS_COUNT")
    assert ast.literal_eval(tps_count.value) == 5
    _assert_assignment_expression(
        tree, "states", "wal.replay(layout, admission_policy=policy)"
    )
    _assert_assignment_expression(tree, "records", "wal.read_records(layout)")
    _assert_assignment_expression(
        tree,
        "expected_genomes",
        "{genome.canonical() for genome in expected_genome_objects}",
    )
    _assert_assignment_expression(
        tree,
        "abort_count",
        'sum(record.stage == "abort" for record in records)',
    )
    completeness = _if_with_system_exit(
        tree, "A-5 requires exactly eight committed genomes and zero abort records"
    )
    expected_condition = ast.parse(
        "len(states) != EXPECTED_GENOME_COUNT "
        "or abort_count != 0 "
        "or any(not state.committed or state.aborted for state in states.values())",
        mode="eval",
    ).body
    assert ast.dump(completeness.test, include_attributes=False) == ast.dump(
        expected_condition, include_attributes=False
    )
    _assert_assignment_expression(tree, "committed_genomes", "set(committed)")
    canonical_check = _if_with_system_exit(
        tree, "all eight canonical genomes must commit"
    )
    expected_canonical_check = ast.parse(
        "committed_genomes != expected_genomes", mode="eval"
    ).body
    assert ast.dump(canonical_check.test, include_attributes=False) == ast.dump(
        expected_canonical_check, include_attributes=False
    )


def _assert_walltime_budget(source: str) -> None:
    assert "#PBS -A SFC" in source
    assert "#PBS -q gen_S" in source
    assert "#PBS -b 1" in source
    walltime = _pbs_walltime_seconds(source)
    cap_names = (
        "QSTAT_CAP_S",
        "WORKTREE_SETUP_CAP_S",
        "DEPENDENCY_BUILD_CAP_S",
        "SWEEP_CAP_S",
        "WORKTREE_CLEANUP_CAP_S",
        "FINALIZE_CAP_S",
    )
    caps = {name: _integer_assignment(source, name) for name in cap_names}
    margin = _integer_assignment(source, "FINAL_MARGIN_S")
    assert caps["SWEEP_CAP_S"] == 5400
    assert sum(caps.values()) + margin < walltime
    assert _integer_assignment(source, "EXPECTED_WALLTIME_S") == walltime
    assert (
        '[[ $((INNER_CAP_TOTAL_S + FINAL_MARGIN_S)) -lt "$EXPECTED_WALLTIME_S" ]]'
        in source
    )


def _assert_execution_shape(job: str, submitter: str) -> None:
    normalized_job = re.sub(r"\\\n\s*", " ", job)
    normalized_submitter = re.sub(r"\\\n\s*", " ", submitter)
    normalized_job = re.sub(r"[ \t]+", " ", normalized_job)
    normalized_submitter = re.sub(r"[ \t]+", " ", normalized_submitter)
    driver = (
        'timeout "$SWEEP_CAP_S" "$PY" -I -B '
        '"$JOB_REPO/orchestrator/campaign/backoff_sweep.py" "$WORKLOAD"'
    )
    assert normalized_job.count(driver) == 1
    assert "read-heavy" not in job
    assert "read-heavy" not in submitter
    assert "--screening" not in job
    assert "--screening-fixed-us" not in job
    assert "--confirm-each-candidate" not in job
    assert "IZANAGI_PEGASUS_THIRDPARTY_CACHE" not in job
    assert 'export http_proxy="$BUILD_NETWORK_PROXY_URL"' in job
    assert 'export https_proxy="$BUILD_NETWORK_PROXY_URL"' in job
    assert 'JOB_REPO="$TMPDIR/job-repo"' in job
    assert 'JOB_CCBENCH="$JOB_REPO/external/ccbench"' in job
    assert 'mkdir -m 0700 "$OUTPUT_ROOT/env/pegasus" "$OUTPUT_ROOT/env/pegasus/claims"' in job
    assert 'destination = base / "result.json"' in job
    assert 'fd = os.open(temporary, flags, 0o600)' in job
    assert 'os.link(temporary, destination, follow_symlinks=False)' in job
    assert 'git -C "$CCBENCH_BASE" worktree prune --expire now' in normalized_job
    assert "printf '%s\\nprune_rc=%s\\n'" in job
    assert 'A5_EXPECTED_HEAD=$EXPECTED_HEAD' in submitter
    assert '-o "$stdout" -e "$stderr" "$JOB_SCRIPT"' in normalized_submitter
    assert normalized_submitter.index('cd -- "$REPO_ROOT"') < normalized_submitter.index(
        "job_id=$(qsub"
    )
    for fragment in (
        '"hostname": hostname',
        '"fqdn": fqdn',
        '"boot_id": boot_id',
        '"boot_epoch": int(boot_epoch)',
        '"pbs_jobid": pbs_jobid',
        '"repository_commit": repository_commit',
        '"ccbench_commit": ccbench_commit',
        '"toolchain": toolchains[0]',
        '"perf_preflight": preflights[0]',
        '"wal_sha256": hashlib.sha256(wal_after).hexdigest()',
        '"lock_sha256": hashlib.sha256(lock_after).hexdigest()',
        'improvement_percent = (target["median"] / baseline["median"] - 1) * 100',
    ):
        assert fragment in job


def _assert_current_pair_contract() -> None:
    job = JOB.read_text(encoding="utf-8")
    submitter = SUBMITTER.read_text(encoding="utf-8")
    _assert_submitter_workloads(submitter)
    _assert_job_workloads(job)
    _assert_no_backoff_denominator(job)
    _assert_complete_committed_sweep(job)
    _assert_walltime_budget(job)
    _assert_execution_shape(job, submitter)


def test_submitter_workload_set_is_exactly_the_two_adopted_values():
    _assert_submitter_workloads(SUBMITTER.read_text(encoding="utf-8"))


def test_job_body_accepts_exactly_the_two_adopted_workloads():
    _assert_job_workloads(JOB.read_text(encoding="utf-8"))


def test_finalizer_denominator_is_exactly_no_backoff():
    _assert_no_backoff_denominator(JOB.read_text(encoding="utf-8"))


def test_finalizer_requires_all_eight_commits_and_zero_aborts():
    _assert_complete_committed_sweep(JOB.read_text(encoding="utf-8"))


def test_inner_caps_and_final_margin_fit_strictly_inside_pbs_walltime():
    _assert_walltime_budget(JOB.read_text(encoding="utf-8"))


def test_job_body_is_registered_only_as_dispatch_required():
    registry = json.loads(REGISTRY.read_text(encoding="utf-8"))["entries"]
    assert registry["tools/pegasus/a5_second_boot_backoff_sweep.sh"] == {
        "class": "dispatch-required",
        "reason": "PBS A-5 second-boot backoff sweep measurement job body",
        "primary_gate": "PBS allocation and job-body site preflight",
        "evidence": "static job-body classification",
    }
    assert registry["tools/pegasus/submit_a5_second_boot_backoff_sweep.sh"] == {
        "class": "local-ok",
        "reason": "login-side PBS A-5 two-workload fan-out submitter",
        "primary_gate": (
            "qsub submission; compute work stays in independent job bodies"
        ),
        "evidence": "static login-side submitter classification",
    }


def test_current_scripts_are_a_positive_example_of_the_complete_contract():
    _assert_current_pair_contract()


def _run() -> int:
    tests = [
        value for name, value in sorted(globals().items())
        if name.startswith("test_") and callable(value)
    ]
    passed = failed = 0
    for test in tests:
        try:
            test()
            print(f"PASS {test.__name__}")
            passed += 1
        except Exception as exc:  # noqa: BLE001
            print(f"FAIL {test.__name__}: {type(exc).__name__}: {exc}")
            failed += 1
    print(f"\n{passed} passed, {failed} failed")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(_run())
