"""tools/mutation_harness.py の fail-closed 契約を一時 git repo で検査する。"""

from __future__ import annotations

import importlib.util
import hashlib
import json
import os
import signal
import subprocess
import sys
import time
from pathlib import Path

import pytest


_REPO = Path(__file__).resolve().parents[2]
_TOOL = _REPO / "tools" / "mutation_harness.py"
_SPEC = importlib.util.spec_from_file_location("mutation_harness_under_test", _TOOL)
assert _SPEC is not None and _SPEC.loader is not None
MH = importlib.util.module_from_spec(_SPEC)
sys.modules[_SPEC.name] = MH
_SPEC.loader.exec_module(MH)


def _git(repo: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", "-C", str(repo), *args],
        check=False,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    assert result.returncode == 0, result.stderr
    return result.stdout


@pytest.fixture
def repo(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    root = tmp_path / "repo"
    root.mkdir()
    _git(root, "init", "-q")
    _git(root, "config", "user.email", "mutation@example.invalid")
    _git(root, "config", "user.name", "Mutation Harness Test")
    (root / "target.py").write_text(
        'VALUE = 0\nTOKEN = "x"\nTOKEN_COPY = "x"\n', encoding="utf-8"
    )
    tests = root / "tests"
    tests.mkdir()
    (tests / "test_gate.py").write_text(
        """\
import os
import signal
import time
from pathlib import Path

import pytest


TARGET = Path(__file__).parents[1] / "target.py"


@pytest.fixture(scope="session", autouse=True)
def record_run():
    value = TARGET.read_text(encoding="utf-8").splitlines()[0].split("=", 1)[1].strip()
    calls = Path(os.environ["IZANAGI_MUTATION_TEST_CALLS"])
    with calls.open("a", encoding="utf-8") as stream:
        stream.write(value + "\\n")
        stream.flush()
        os.fsync(stream.fileno())


@pytest.mark.parametrize("case", ["one", "two", "three"])
def test_gate(case):
    value = TARGET.read_text(encoding="utf-8").splitlines()[0].split("=", 1)[1].strip()
    desired = {"1": "one", "2": "two", "3": "three"}.get(value)
    if case != desired:
        return
    mode = os.environ.get("IZANAGI_MUTATION_TEST_MODE", "normal")
    if mode == "kill-parent-two" and value == "2":
        os.kill(os.getppid(), signal.SIGKILL)
    if mode == "hang-three" and value == "3":
        time.sleep(5)
    assert False, f"mutation value {value} reached {case}"
""",
        encoding="utf-8",
    )
    (tests / "conftest.py").write_text(
        """\
import os
from pathlib import Path


def pytest_sessionfinish(session, exitstatus):
    target = Path(__file__).parents[1] / "target.py"
    value = target.read_text(encoding="utf-8").splitlines()[0].split("=", 1)[1].strip()
    if os.environ.get("IZANAGI_MUTATION_TEST_MODE") == "parse-two" and value == "2":
        session.exitstatus = 3
""",
        encoding="utf-8",
    )
    (root / "tracked.txt").write_text("base\n", encoding="utf-8")
    _git(root, "add", "target.py", "tests/conftest.py", "tests/test_gate.py", "tracked.txt")
    _git(root, "commit", "-qm", "fixture")
    monkeypatch.setenv("IZANAGI_MUTATION_TEST_CALLS", str(root.parent / "calls.txt"))
    monkeypatch.setenv("IZANAGI_MUTATION_TEST_MODE", "normal")
    return root


def _mutation(
    mutation_id: str,
    old: str,
    new: str,
    node: str,
    *,
    replacements: list[dict[str, str]] | None = None,
) -> dict[str, object]:
    return {
        "id": mutation_id,
        "category": "negative",
        "replacements": replacements or [
            {"file": "target.py", "old": old, "new": new}
        ],
        "expected_nodes": [f"tests/test_gate.py::test_gate[{node}]"],
        "expected_status": "KILLED",
        "hang_risk": False,
    }


def _write_spec(path: Path, mutations: list[dict[str, object]]) -> None:
    path.write_text(
        json.dumps(
            {
                "schema": MH.SPEC_SCHEMA,
                "estimated_run_seconds": 0.01,
                "timeout_seconds": 10,
                "hang_timeout_seconds": 1,
                "mutations": mutations,
            },
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )


def _paths(repo: Path) -> tuple[Path, Path, Path, Path]:
    base = repo.parent
    return base / "spec.json", base / "ledger.json", base / "calls.txt", base / "mode.txt"


def _argv(
    repo: Path,
    spec: Path,
    out: Path,
    calls: Path,
    mode: Path,
    *,
    resume: bool = False,
    expected_spec_sha256: str | None = None,
) -> list[str]:
    os.environ["IZANAGI_MUTATION_TEST_CALLS"] = str(calls)
    os.environ["IZANAGI_MUTATION_TEST_MODE"] = (
        mode.read_text(encoding="utf-8").strip() if mode.exists() else "normal"
    )
    args = [
        "--repo",
        str(repo),
        "--spec",
        str(spec),
        "--expected-spec-sha256",
        expected_spec_sha256 or hashlib.sha256(spec.read_bytes()).hexdigest(),
        "--out",
        str(out),
        "--runner-mode",
        "local",
        "--detached",
    ]
    if resume:
        args.append("--resume")
    args.extend(
        [
            "--",
            sys.executable,
            "-m",
            "pytest",
            "tests/test_gate.py",
            "-q",
            "-rf",
        ]
    )
    return args


def _single_spec(path: Path) -> None:
    _write_spec(path, [_mutation("M1", "VALUE = 0", "VALUE = 1", "one")])


def _calls(path: Path) -> list[str]:
    return path.read_text(encoding="utf-8").splitlines() if path.exists() else []


def test_normal_run_uses_cumulative_replacements_and_full_failed_line(repo: Path) -> None:
    spec, out, calls, mode = _paths(repo)
    _write_spec(
        spec,
        [
            _mutation(
                "M1",
                "",
                "",
                "one",
                replacements=[
                    {"file": "target.py", "old": "VALUE = 0", "new": "VALUE = 1"},
                    {"file": "target.py", "old": 'TOKEN = "x"', "new": 'TOKEN = "y"'},
                ],
            )
        ],
    )

    assert MH.main(_argv(repo, spec, out, calls, mode)) == 0

    ledger = json.loads(out.read_text(encoding="utf-8"))
    assert ledger["schema"] == MH.LEDGER_SCHEMA
    assert ledger["mutations"][0]["status"] == "KILLED"
    assert ledger["mutations"][0]["failed_nodes"] == [
        "tests/test_gate.py::test_gate[one]"
    ]
    assert ledger["mutations"][0]["anchor_counts"] == {"0": 1, "1": 1}
    assert _calls(calls) == ["0", "1"]
    assert (repo / "target.py").read_text(encoding="utf-8") == _git(
        repo, "show", "HEAD:target.py"
    )


def test_cumulative_replacement_uses_the_result_of_the_previous_anchor() -> None:
    mutation = MH.Mutation(
        id="CHAIN",
        category="negative",
        replacements=(
            MH.Replacement(file="target.py", old="A = 0", new="A = 1"),
            MH.Replacement(file="target.py", old="A = 1", new="A = 2"),
        ),
        expected_nodes=("tests/test_gate.py::test_gate[one]",),
        expected_status="KILLED",
        hang_risk=False,
    )

    mutated, _diff, counts = MH._mutated_sources(mutation, {"target.py": "A = 0\n"})

    assert mutated == {"target.py": "A = 2\n"}
    assert counts == {"0": 1, "1": 1}


def test_failed_node_parser_keeps_parameter_and_full_node(repo: Path) -> None:
    output = (
        "\x1b[31m | FAILED tests/test_gate.py::test_gate[one]"
        " - AssertionError: mutation reached\x1b[0m\n"
    )

    assert MH._failed_nodes(output, repo) == [
        "tests/test_gate.py::test_gate[one]"
    ]


def test_expected_spec_hash_mismatch_stops_before_runner_and_ledger(repo: Path) -> None:
    spec, out, calls, mode = _paths(repo)
    _single_spec(spec)
    registered = hashlib.sha256(spec.read_bytes()).hexdigest()
    spec.write_text(spec.read_text(encoding="utf-8") + " ", encoding="utf-8")

    with pytest.raises(MH.HarnessError, match="事前登録値と不一致"):
        MH.main(
            _argv(
                repo,
                spec,
                out,
                calls,
                mode,
                expected_spec_sha256=registered,
            )
        )

    assert not calls.exists()
    assert not out.exists()


def test_applied_diff_must_equal_registration_preflight(
    repo: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    spec, out, calls, mode = _paths(repo)
    _single_spec(spec)
    real = MH._mutated_sources
    invocation = 0

    def drifting(*args: object, **kwargs: object) -> tuple[dict[str, str], str, dict[str, int]]:
        nonlocal invocation
        invocation += 1
        mutated, diff, counts = real(*args, **kwargs)
        return mutated, diff + ("# drift\n" if invocation == 2 else ""), counts

    monkeypatch.setattr(MH, "_mutated_sources", drifting)
    with pytest.raises(MH.HarnessError, match="preflight と実適用"):
        MH.main(_argv(repo, spec, out, calls, mode))

    assert _calls(calls) == ["0"]
    assert (repo / "target.py").read_text(encoding="utf-8") == _git(
        repo, "show", "HEAD:target.py"
    )


def test_fake_runner_is_rejected_before_execution(repo: Path) -> None:
    spec, out, calls, mode = _paths(repo)
    _single_spec(spec)
    fake = repo.parent / "fake_runner.py"
    fake.write_text("raise SystemExit(1)\n", encoding="utf-8")
    argv = _argv(repo, spec, out, calls, mode)
    separator = argv.index("--")
    argv[separator + 1 :] = [sys.executable, str(fake), "-rf"]

    with pytest.raises(MH.HarnessError, match="runner entrypoint"):
        MH.main(argv)

    assert not calls.exists()
    assert not out.exists()


def test_expected_node_must_exist_in_pytest_collection(repo: Path) -> None:
    spec, out, calls, mode = _paths(repo)
    _write_spec(spec, [_mutation("M1", "VALUE = 0", "VALUE = 1", "absent")])

    with pytest.raises(MH.HarnessError, match="collection に実在しない"):
        MH.main(_argv(repo, spec, out, calls, mode))

    assert not calls.exists()
    assert not out.exists()


def test_parameter_suffix_is_matched_exactly(repo: Path) -> None:
    spec, out, calls, mode = _paths(repo)
    _write_spec(spec, [_mutation("M1", "VALUE = 0", "VALUE = 2", "one")])

    assert MH.main(_argv(repo, spec, out, calls, mode)) == 1

    record = json.loads(out.read_text(encoding="utf-8"))["mutations"][0]
    assert record["status"] == "MISMATCH"
    assert record["failed_nodes"] == ["tests/test_gate.py::test_gate[two]"]


def test_failed_nodes_strict_superset_never_counts_as_killed(repo: Path) -> None:
    expected = ["tests/test_gate.py::test_gate[one]"]
    failed = [*expected, "tests/test_gate.py::test_gate[two]"]
    status = MH._observed_status(
        result={"timed_out": False, "rc": 1, "artifact_error": None},
        failed=failed,
        expected=expected,
        repo=repo,
    )

    assert status == "MISMATCH"


def test_failed_nodes_strict_subset_never_counts_as_killed(repo: Path) -> None:
    expected = [
        "tests/test_gate.py::test_gate[one]",
        "tests/test_gate.py::test_gate[two]",
    ]
    failed = ["tests/test_gate.py::test_gate[one]"]
    status = MH._observed_status(
        result={"timed_out": False, "rc": 1, "artifact_error": None},
        failed=failed,
        expected=expected,
        repo=repo,
    )

    assert status == "MISMATCH"


def test_same_test_part_from_different_path_never_counts_as_killed(
    repo: Path,
) -> None:
    expected = ["tests/a.py::test_gate[one]"]
    failed = ["tests/b.py::test_gate[one]"]
    status = MH._observed_status(
        result={"timed_out": False, "rc": 1, "artifact_error": None},
        failed=failed,
        expected=expected,
        repo=repo,
    )

    assert status == "MISMATCH"


@pytest.mark.parametrize(
    ("expected_node", "failed_node"),
    [
        pytest.param(
            "tests/x/a.py::test_gate", "tests/y/a.py::test_gate", id="basename"
        ),
        pytest.param(
            "tests/p/x/a.py::test_gate",
            "tests/q/x/a.py::test_gate",
            id="tail2",
        ),
        pytest.param(
            "tests/A.py::test_gate", "tests/a.py::test_gate", id="casefold"
        ),
        pytest.param(
            "tests/a.py::C1::test_gate",
            "tests/a.py::C2::test_gate",
            id="classns",
        ),
    ],
)
def test_match_key_keeps_distinct_pytest_nodes_separate(
    repo: Path, expected_node: str, failed_node: str
) -> None:
    status = MH._observed_status(
        result={"timed_out": False, "rc": 1, "artifact_error": None},
        failed=[failed_node],
        expected=[expected_node],
        repo=repo,
    )

    assert status == "MISMATCH"


@pytest.mark.parametrize("rc", [2, 3, 5])
def test_abnormal_pytest_rc_never_counts_as_killed(repo: Path, rc: int) -> None:
    expected = ["tests/test_gate.py::test_gate[one]"]
    status = MH._observed_status(
        result={"timed_out": False, "rc": rc, "artifact_error": None},
        failed=expected,
        expected=expected,
        repo=repo,
    )

    assert status == "PARSE_ERROR"


@pytest.mark.parametrize("artifact", ["spec", "out", "temp"])
def test_runtime_artifacts_inside_checkout_are_rejected_before_baseline(
    repo: Path, artifact: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    spec, out, calls, mode = _paths(repo)
    _single_spec(spec)
    if artifact == "spec":
        inside = repo / "spec.json"
        inside.write_bytes(spec.read_bytes())
        spec = inside
    elif artifact == "out":
        out = repo / "ledger.json"
    else:
        temp_root = repo / "runtime-tmp"
        temp_root.mkdir()
        monkeypatch.setattr(MH.tempfile, "tempdir", str(temp_root))

    with pytest.raises(MH.HarnessError, match="runtime artifact"):
        MH.main(_argv(repo, spec, out, calls, mode))

    assert not calls.exists()
    assert not out.exists()


@pytest.mark.parametrize("staged", [False, True])
def test_tracked_or_indexed_test_dirt_is_rejected_before_runner(
    repo: Path, staged: bool
) -> None:
    spec, out, calls, mode = _paths(repo)
    _single_spec(spec)
    test_file = repo / "tests" / "test_gate.py"
    test_file.write_text(test_file.read_text(encoding="utf-8") + "# dirt\n", encoding="utf-8")
    if staged:
        _git(repo, "add", "tests/test_gate.py")

    with pytest.raises(MH.HarnessError, match="tracked/index dirt"):
        MH.main(_argv(repo, spec, out, calls, mode))

    assert not calls.exists()
    assert not out.exists()


def test_startup_rejects_one_byte_head_mismatch_before_runner_or_ledger(repo: Path) -> None:
    spec, out, calls, mode = _paths(repo)
    _single_spec(spec)
    target = repo / "target.py"
    target.write_text(target.read_text(encoding="utf-8") + "#", encoding="utf-8")

    with pytest.raises(MH.HarnessError, match="固定 HEAD blob と不一致"):
        MH.main(_argv(repo, spec, out, calls, mode))

    assert not calls.exists()
    assert not out.exists()
    assert target.read_text(encoding="utf-8").endswith("#")


def test_resume_rejects_different_head(repo: Path) -> None:
    spec, out, calls, mode = _paths(repo)
    _single_spec(spec)
    assert MH.main(_argv(repo, spec, out, calls, mode)) == 0
    before = _calls(calls)
    (repo / "tracked.txt").write_text("new head\n", encoding="utf-8")
    _git(repo, "add", "tracked.txt")
    _git(repo, "commit", "-qm", "move head")

    with pytest.raises(MH.HarnessError, match="repo_head"):
        MH.main(_argv(repo, spec, out, calls, mode, resume=True))

    assert _calls(calls) == before


def test_resume_rejects_different_spec_hash(repo: Path) -> None:
    spec, out, calls, mode = _paths(repo)
    _single_spec(spec)
    assert MH.main(_argv(repo, spec, out, calls, mode)) == 0
    document = json.loads(spec.read_text(encoding="utf-8"))
    document["estimated_run_seconds"] = 0.02
    spec.write_text(json.dumps(document) + "\n", encoding="utf-8")
    before = _calls(calls)

    with pytest.raises(MH.HarnessError, match="spec_sha256"):
        MH.main(_argv(repo, spec, out, calls, mode, resume=True))

    assert _calls(calls) == before


def test_resume_reruns_parse_error_and_skips_terminal_record(repo: Path) -> None:
    spec, out, calls, mode = _paths(repo)
    _write_spec(
        spec,
        [
            _mutation("M1", "VALUE = 0", "VALUE = 1", "one"),
            _mutation("M2", "VALUE = 0", "VALUE = 2", "two"),
        ],
    )
    mode.write_text("parse-two\n", encoding="utf-8")
    with pytest.raises(MH.HarnessError, match="failed node"):
        MH.main(_argv(repo, spec, out, calls, mode))
    first = json.loads(out.read_text(encoding="utf-8"))
    assert [record["status"] for record in first["mutations"]] == [
        "KILLED",
        "PARSE_ERROR",
    ]
    assert _calls(calls) == ["0", "1", "2"]

    mode.write_text("normal\n", encoding="utf-8")
    assert MH.main(_argv(repo, spec, out, calls, mode, resume=True)) == 0

    resumed = json.loads(out.read_text(encoding="utf-8"))
    assert [record["id"] for record in resumed["mutations"]] == ["M1", "M2"]
    assert [record["status"] for record in resumed["mutations"]] == [
        "KILLED",
        "KILLED",
    ]
    assert resumed["nonterminal_history"][0]["status"] == "PARSE_ERROR"
    assert _calls(calls) == ["0", "1", "2", "2"]


def test_resume_rejects_incomplete_running_record_before_runner(repo: Path) -> None:
    spec, out, calls, mode = _paths(repo)
    _single_spec(spec)
    assert MH.main(_argv(repo, spec, out, calls, mode)) == 0
    ledger = json.loads(out.read_text(encoding="utf-8"))
    ledger["mutations"][0] = {"id": "M1", "status": "RUNNING"}
    out.write_text(json.dumps(ledger) + "\n", encoding="utf-8")

    before = _calls(calls)
    with pytest.raises(MH.HarnessError, match="field 集合"):
        MH.main(_argv(repo, spec, out, calls, mode, resume=True))

    assert _calls(calls) == before


def test_resume_rejects_corrupt_json(repo: Path) -> None:
    spec, out, calls, mode = _paths(repo)
    _single_spec(spec)
    out.write_text("{broken", encoding="utf-8")

    with pytest.raises(MH.HarnessError, match="resume ledger を読めない"):
        MH.main(_argv(repo, spec, out, calls, mode, resume=True))

    assert not calls.exists()


def test_resume_rejects_duplicate_record_id(repo: Path) -> None:
    spec, out, calls, mode = _paths(repo)
    _single_spec(spec)
    assert MH.main(_argv(repo, spec, out, calls, mode)) == 0
    ledger = json.loads(out.read_text(encoding="utf-8"))
    ledger["mutations"].append(dict(ledger["mutations"][0]))
    out.write_text(json.dumps(ledger) + "\n", encoding="utf-8")

    with pytest.raises(MH.HarnessError, match="ID が重複"):
        MH.main(_argv(repo, spec, out, calls, mode, resume=True))


def test_resume_rejects_every_missing_terminal_and_baseline_field_before_runner(
    repo: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    spec, out, calls, mode = _paths(repo)
    _single_spec(spec)
    assert MH.main(_argv(repo, spec, out, calls, mode)) == 0
    valid = json.loads(out.read_text(encoding="utf-8"))
    before = _calls(calls)

    def runner_forbidden(*args: object, **kwargs: object) -> dict[str, object]:
        raise AssertionError("resume poison must be rejected before runner")

    monkeypatch.setattr(MH, "_run_tests", runner_forbidden)
    for section, fields in (
        ("mutations", MH.MUTATION_RECORD_FIELDS),
        ("baseline", MH.BASELINE_FIELDS),
    ):
        for field in sorted(fields):
            poisoned = json.loads(json.dumps(valid))
            record = poisoned[section][0] if section == "mutations" else poisoned[section]
            del record[field]
            out.write_text(json.dumps(poisoned) + "\n", encoding="utf-8")
            with pytest.raises(MH.HarnessError, match="field 集合"):
                MH.main(_argv(repo, spec, out, calls, mode, resume=True))

    assert _calls(calls) == before


@pytest.mark.parametrize(
    ("field", "value", "message"),
    [
        ("rc", 0, "status が rc/node/artifact evidence と不一致"),
        ("expected_nodes", ["tests/test_gate.py::test_gate[two]"], "現 spec/evidence"),
        ("injection_diff_sha256", "0" * 64, "現 spec/evidence"),
        ("tool_sha256", "0" * 64, "現 spec/evidence"),
    ],
)
def test_resume_rejects_terminal_record_poison(
    repo: Path,
    field: str,
    value: object,
    message: str,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    spec, out, calls, mode = _paths(repo)
    _single_spec(spec)
    assert MH.main(_argv(repo, spec, out, calls, mode)) == 0
    ledger = json.loads(out.read_text(encoding="utf-8"))
    ledger["mutations"][0][field] = value
    out.write_text(json.dumps(ledger) + "\n", encoding="utf-8")
    before = _calls(calls)
    monkeypatch.setattr(
        MH,
        "_run_tests",
        lambda *args, **kwargs: (_ for _ in ()).throw(
            AssertionError("terminal poison reached runner")
        ),
    )

    with pytest.raises(MH.HarnessError, match=message):
        MH.main(_argv(repo, spec, out, calls, mode, resume=True))

    assert _calls(calls) == before


def test_resume_rejects_minimal_forged_terminal_record(repo: Path) -> None:
    spec, out, calls, mode = _paths(repo)
    _single_spec(spec)
    assert MH.main(_argv(repo, spec, out, calls, mode)) == 0
    ledger = json.loads(out.read_text(encoding="utf-8"))
    ledger["mutations"] = [
        {"id": "M1", "status": "KILLED", "matches_expectation": True}
    ]
    out.write_text(json.dumps(ledger) + "\n", encoding="utf-8")
    before = _calls(calls)

    with pytest.raises(MH.HarnessError, match="field 集合"):
        MH.main(_argv(repo, spec, out, calls, mode, resume=True))

    assert _calls(calls) == before


@pytest.mark.parametrize(
    ("old", "message"),
    [("ABSENT", "anchor count=0"), ('"x"', "anchor count=2")],
)
def test_replacement_anchor_must_be_exactly_one(
    repo: Path, old: str, message: str
) -> None:
    spec, out, calls, mode = _paths(repo)
    _write_spec(spec, [_mutation("M1", old, "replacement", "one")])

    with pytest.raises(MH.HarnessError, match=message):
        MH.main(_argv(repo, spec, out, calls, mode))

    assert not calls.exists()
    assert not out.exists()


def test_abnormal_rc_with_expected_failed_node_flushes_parse_error_and_stops(
    repo: Path,
) -> None:
    spec, out, calls, mode = _paths(repo)
    _write_spec(spec, [_mutation("M2", "VALUE = 0", "VALUE = 2", "two")])
    mode.write_text("parse-two\n", encoding="utf-8")

    with pytest.raises(MH.HarnessError, match="failed node"):
        MH.main(_argv(repo, spec, out, calls, mode))

    ledger = json.loads(out.read_text(encoding="utf-8"))
    assert ledger["mutations"][0]["status"] == "PARSE_ERROR"
    assert ledger["mutations"][0]["failed_nodes"] == [
        "tests/test_gate.py::test_gate[two]"
    ]
    assert (repo / "target.py").read_text(encoding="utf-8") == _git(
        repo, "show", "HEAD:target.py"
    )


def test_hang_risk_uses_short_timeout_records_evidence_and_restores(repo: Path) -> None:
    spec, out, calls, mode = _paths(repo)
    mutation = {
        "id": "H1",
        "category": "negative",
        "replacements": [
            {"file": "target.py", "old": "VALUE = 0", "new": "VALUE = 3"}
        ],
        "expected_nodes": [],
        "expected_status": "TIMEOUT",
        "hang_risk": True,
    }
    _write_spec(spec, [mutation])
    document = json.loads(spec.read_text(encoding="utf-8"))
    document["hang_timeout_seconds"] = 0.1
    spec.write_text(json.dumps(document) + "\n", encoding="utf-8")
    mode.write_text("hang-three\n", encoding="utf-8")

    assert MH.main(_argv(repo, spec, out, calls, mode)) == 0

    ledger = json.loads(out.read_text(encoding="utf-8"))
    assert ledger["mutations"][0]["status"] == "TIMEOUT"
    assert ledger["mutations"][0]["timed_out"] is True
    assert (repo / "target.py").read_text(encoding="utf-8") == _git(
        repo, "show", "HEAD:target.py"
    )


def test_restore_verification_rejects_content_different_from_head(repo: Path) -> None:
    spec, _out, _calls_path, _mode = _paths(repo)
    _single_spec(spec)
    parsed, _hash = MH._load_spec(spec)
    head = MH._repo_head(repo)
    originals = MH._read_head_sources(repo, head, parsed)
    (repo / "target.py").write_text("not restored\n", encoding="utf-8")

    with pytest.raises(MH.HarnessError, match="read_text.*固定 HEAD blob と不一致"):
        MH._verify_originals(repo, originals)


def test_apply_mutation_calls_restore_at_the_production_callsite(
    repo: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    spec, out, calls, mode = _paths(repo)
    _single_spec(spec)
    real_restore = MH._restore_targets
    restored: list[tuple[str, ...]] = []

    def recording_restore(root: Path, originals: dict[str, str]) -> None:
        restored.append(tuple(sorted(originals)))
        real_restore(root, originals)

    monkeypatch.setattr(MH, "_restore_targets", recording_restore)
    assert MH.main(_argv(repo, spec, out, calls, mode)) == 0

    assert restored == [("target.py",)]


def test_flock_rejects_a_competing_harness_for_the_same_repo(repo: Path) -> None:
    first = MH._lock_for(repo)
    try:
        with pytest.raises(MH.HarnessError, match="同じ repo で走行中"):
            MH._lock_for(repo)
    finally:
        first.close()


def test_atomic_writer_killed_before_replace_preserves_previous_ledger(
    repo: Path,
) -> None:
    _spec, out, _calls_path, _mode = _paths(repo)
    previous = {"generation": 1, "records": ["complete"]}
    out.write_text(json.dumps(previous) + "\n", encoding="utf-8")
    script = """
import importlib.util
import os
import signal
import sys
from pathlib import Path

tool = Path(sys.argv[1])
out = Path(sys.argv[2])
spec = importlib.util.spec_from_file_location("atomic_writer_under_test", tool)
module = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = module
spec.loader.exec_module(module)

def kill_before_replace(source, destination):
    os.kill(os.getpid(), signal.SIGKILL)

module.os.replace = kill_before_replace
module._write_ledger(out, {"generation": 2, "records": ["replacement"]})
"""
    completed = subprocess.run(
        [sys.executable, "-c", script, str(_TOOL), str(out)],
        check=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        timeout=10,
    )

    assert completed.returncode == -signal.SIGKILL
    assert json.loads(out.read_text(encoding="utf-8")) == previous


def test_signal_arriving_during_restore_is_deferred_until_all_targets_verified(
    repo: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    second = repo / "second.py"
    second.write_text("SECOND = 0\n", encoding="utf-8")
    _git(repo, "add", "second.py")
    _git(repo, "commit", "-qm", "second target")
    originals = {
        "target.py": _git(repo, "show", "HEAD:target.py"),
        "second.py": _git(repo, "show", "HEAD:second.py"),
    }
    (repo / "target.py").write_text("VALUE = 9\n", encoding="utf-8")
    second.write_text("SECOND = 9\n", encoding="utf-8")
    real_write_text = Path.write_text
    sent = False

    def signal_on_first_restore(path: Path, data: str, **kwargs: object) -> int:
        nonlocal sent
        if path.parent == repo and not sent:
            sent = True
            os.kill(os.getpid(), signal.SIGTERM)
        return real_write_text(path, data, **kwargs)

    monkeypatch.setattr(Path, "write_text", signal_on_first_restore)
    old_handlers = MH._install_signal_handlers()
    try:
        with pytest.raises(MH.SignalAbort):
            MH._restore_targets(repo, originals)
    finally:
        MH._restore_signal_handlers(old_handlers)

    assert sent is True
    assert (repo / "target.py").read_text(encoding="utf-8") == originals["target.py"]
    assert second.read_text(encoding="utf-8") == originals["second.py"]


def test_completed_record_is_flushed_before_next_runner_sigkill(repo: Path) -> None:
    spec, out, calls, mode = _paths(repo)
    _write_spec(
        spec,
        [
            _mutation("M1", "VALUE = 0", "VALUE = 1", "one"),
            _mutation("M2", "VALUE = 0", "VALUE = 2", "two"),
        ],
    )
    mode.write_text("kill-parent-two\n", encoding="utf-8")
    command = [sys.executable, str(_TOOL), *_argv(repo, spec, out, calls, mode)]

    try:
        completed = subprocess.run(
            command,
            check=False,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=20,
        )
        assert completed.returncode < 0
        ledger = json.loads(out.read_text(encoding="utf-8"))
        assert [(record["id"], record["status"]) for record in ledger["mutations"]] == [
            ("M1", "KILLED")
        ]
        assert _calls(calls) == ["0", "1", "2"]
        assert "VALUE = 2" in (repo / "target.py").read_text(encoding="utf-8")
    finally:
        original = _git(repo, "show", "HEAD:target.py")
        (repo / "target.py").write_text(original, encoding="utf-8")


def test_sigterm_handler_stops_child_and_restores_active_mutation(repo: Path) -> None:
    spec, out, calls, mode = _paths(repo)
    mutation = {
        "id": "H1",
        "category": "negative",
        "replacements": [
            {"file": "target.py", "old": "VALUE = 0", "new": "VALUE = 3"}
        ],
        "expected_nodes": [],
        "expected_status": "TIMEOUT",
        "hang_risk": True,
    }
    _write_spec(spec, [mutation])
    document = json.loads(spec.read_text(encoding="utf-8"))
    document["hang_timeout_seconds"] = 10
    spec.write_text(json.dumps(document) + "\n", encoding="utf-8")
    mode.write_text("hang-three\n", encoding="utf-8")
    command = [sys.executable, str(_TOOL), *_argv(repo, spec, out, calls, mode)]
    process = subprocess.Popen(
        command,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    try:
        deadline = time.monotonic() + 5
        while _calls(calls) != ["0", "3"] and time.monotonic() < deadline:
            time.sleep(0.02)
        assert _calls(calls) == ["0", "3"]
        process.send_signal(signal.SIGTERM)
        _stdout, stderr = process.communicate(timeout=10)
        assert process.returncode == 128 + signal.SIGTERM
        assert "active mutation restore attempted" in stderr
        assert (repo / "target.py").read_text(encoding="utf-8") == _git(
            repo, "show", "HEAD:target.py"
        )
        ledger = json.loads(out.read_text(encoding="utf-8"))
        assert ledger["mutations"] == []
    finally:
        if process.poll() is None:
            process.kill()
            process.wait(timeout=5)


def test_dispatch_reader_uses_receipt_bound_full_job_stdout(repo: Path) -> None:
    submission = repo / "output" / "pegasus-dispatch" / "request"
    submission.mkdir(parents=True)
    stdout = submission / "izdw-mutation.o123"
    stdout.write_text(
        "FAILED tests/test_gate.py::test_one\n1 failed\n", encoding="utf-8"
    )
    receipt = submission / "receipt.json"
    receipt.write_text(
        json.dumps(
            {
                "submission_dir": str(submission),
                "request_id": "123.server",
                "request": {"job_name": "izdw-mutation"},
                "outcome": {"rc": 1},
                "scheduler_logs": {"stdout": {"path": str(stdout)}},
            }
        ),
        encoding="utf-8",
    )
    console = (
        "truncated relay without summary\n"
        f"[Pegasus dispatch] receipt を {receipt} へ保存しました (child rc=1)\n"
    )

    result = MH._read_dispatch_stdout(console, repo, 1)

    assert result["artifact_error"] is None
    assert result["job_stdout"] == "FAILED tests/test_gate.py::test_one\n1 failed\n"


def test_dispatch_run_calls_receipt_reader_instead_of_using_console_stdout(
    repo: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    observed: list[tuple[str, Path, int]] = []

    def receipt_reader(console: str, root: Path, rc: int) -> dict[str, object]:
        observed.append((console, root, rc))
        return {
            "artifact_error": None,
            "receipt_path": "/bound/receipt.json",
            "job_stdout_path": "/bound/job.stdout",
            "job_stdout": "receipt-bound stdout\n",
        }

    monkeypatch.setattr(MH, "_read_dispatch_stdout", receipt_reader)
    result = MH._run_tests(
        repo,
        [sys.executable, "-c", "print('relay console only')"],
        timeout_s=5,
        runner_mode="dispatch",
    )

    assert observed == [("relay console only\n", repo, 0)]
    assert result["job_stdout"] == "receipt-bound stdout\n"


def test_dispatch_collection_uses_compute_dispatcher_not_login_exempt_runner(
    repo: Path,
) -> None:
    command = [
        sys.executable,
        str(repo / "tools" / "run_tests.py"),
        "tests/test_gate.py",
        "-rf",
    ]

    collection = MH._collection_command(repo, command, "dispatch")

    assert collection[:2] == [
        sys.executable,
        str(repo / "tools" / "pegasus" / "dispatch_compute.py"),
    ]
    assert collection[2:5] == ["--task", "tests", "--"]
    assert collection[-4:] == ["-n", "0", "--collect-only", "-q"]


@pytest.mark.parametrize(
    "verbosity",
    ["-q", "-qq", "--quiet", "-v", "-vv", "--verbose"],
)
@pytest.mark.parametrize("runner_mode", ["local", "dispatch"])
def test_collection_forces_one_quiet_flag_without_dropping_test_selection(
    repo: Path, verbosity: str, runner_mode: str
) -> None:
    if runner_mode == "local":
        command = [
            sys.executable,
            "-m",
            "pytest",
            "tests/test_gate.py",
            "-k",
            "test_gate",
            verbosity,
            "-rf",
        ]
    else:
        command = [
            sys.executable,
            str(repo / "tools" / "run_tests.py"),
            "tests/test_gate.py",
            "-k",
            "test_gate",
            verbosity,
            "-rf",
        ]

    collection = MH._collection_command(repo, command, runner_mode)

    assert collection[-2:] == ["--collect-only", "-q"]
    assert collection.count("-q") == 1
    assert verbosity not in collection[:-2]
    assert "tests/test_gate.py" in collection
    assert collection[collection.index("-k") + 1] == "test_gate"


def test_dispatch_reader_rejects_console_rc_different_from_receipt_line(
    repo: Path,
) -> None:
    console = (
        "[Pegasus dispatch] receipt を /does/not/matter/receipt.json へ保存しました "
        "(child rc=1)\n"
    )

    result = MH._read_dispatch_stdout(console, repo, 3)

    assert "subprocess rc=3" in result["artifact_error"]


def test_unknown_spec_schema_is_rejected(repo: Path) -> None:
    spec, out, calls, mode = _paths(repo)
    _single_spec(spec)
    document = json.loads(spec.read_text(encoding="utf-8"))
    document["schema"] = "izanagi-dev-wave-mutation-spec/v999"
    spec.write_text(json.dumps(document) + "\n", encoding="utf-8")

    with pytest.raises(MH.HarnessError, match="未知の spec schema"):
        MH.main(_argv(repo, spec, out, calls, mode))

    assert not calls.exists()


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__]))
