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
from collections.abc import Callable
from pathlib import Path

import pytest


_REPO = Path(__file__).resolve().parents[2]
_TOOL = _REPO / "tools" / "mutation_harness.py"
_SPEC = importlib.util.spec_from_file_location("mutation_harness_under_test", _TOOL)
assert _SPEC is not None and _SPEC.loader is not None
MH = importlib.util.module_from_spec(_SPEC)
sys.modules[_SPEC.name] = MH
_SPEC.loader.exec_module(MH)
_REAL_CURRENT_SITE = MH.site_policy.current_site


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
import json
import os
import signal
import subprocess
import sys
import time
from pathlib import Path

import pytest


TARGET = Path(__file__).parents[1] / "target.py"


def _publish_sigterm_record(path, payload):
    temporary = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    try:
        with temporary.open("x", encoding="utf-8") as stream:
            json.dump(payload, stream, sort_keys=True)
            stream.write("\\n")
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
        directory_fd = os.open(path.parent, os.O_RDONLY)
        try:
            os.fsync(directory_fd)
        finally:
            os.close(directory_fd)
    finally:
        if temporary.exists():
            temporary.unlink()


def _publish_sigterm_discovery(calls, value, written_monotonic_ns):
    discovery = calls.with_name("sigterm-discovery-v1.json")
    _publish_sigterm_record(
        discovery,
        {
            "schema": "izanagi-mutation-sigterm-discovery/v1",
            "value": value,
            "pid": os.getpid(),
            "pgid": os.getpgid(0),
            "written_monotonic_ns": written_monotonic_ns,
        },
    )


def _publish_sigterm_ready(calls, child_pid):
    marker = calls.with_name("sigterm-ready-v1.json")
    _publish_sigterm_record(marker, {
        "schema": "izanagi-mutation-sigterm-ready/v1",
        "pid": os.getpid(),
        "child_pid": child_pid,
        "pgid": os.getpgid(0),
        "ready_monotonic_ns": time.monotonic_ns(),
    })


def _append_sigterm_stage_event(calls, event, value):
    trace = calls.with_name("sigterm-stage-trace-v1.jsonl")
    with trace.open("a", encoding="utf-8") as stream:
        json.dump(
            {
                "schema": "izanagi-mutation-sigterm-stage/v1",
                "event": event,
                "value": value,
            },
            stream,
            sort_keys=True,
        )
        stream.write("\\n")
        stream.flush()
        os.fsync(stream.fileno())


@pytest.fixture(scope="session", autouse=True)
def record_run(request):
    value = TARGET.read_text(encoding="utf-8").splitlines()[0].split("=", 1)[1].strip()
    calls = Path(os.environ["IZANAGI_MUTATION_TEST_CALLS"])
    mode = os.environ.get("IZANAGI_MUTATION_TEST_MODE")
    discovery_written_ns = None
    with calls.open("a", encoding="utf-8") as stream:
        if mode == "hang-three-sigterm-ready" and value == "3":
            discovery_written_ns = time.monotonic_ns()
        stream.write(value + "\\n")
        stream.flush()
        os.fsync(stream.fileno())
    if discovery_written_ns is not None:
        _publish_sigterm_discovery(calls, value, discovery_written_ns)
    if mode == "hang-three-sigterm-ready" and value == "0":
        request.addfinalizer(
            lambda: _append_sigterm_stage_event(calls, "stage-0-complete", value)
        )
    elif mode == "hang-three-sigterm-ready" and value == "3":
        _append_sigterm_stage_event(calls, "stage-3-entered", value)
    dispatch_modes = {
        "hang-three-dispatched",
        "hang-three-dispatched-missing-request",
        "hang-three-dispatched-malformed-request",
        "hang-three-unrelated",
    }
    if mode in dispatch_modes and value == "3":
        submission = TARGET.parent / "output" / "pegasus-dispatch" / "queued-request"
        submission.mkdir(parents=True)
        if mode == "hang-three-dispatched-missing-request":
            return
        if mode == "hang-three-dispatched-malformed-request":
            (submission / "request.json").write_text("{\\n", encoding="utf-8")
            return
        environment = {}
        if mode == "hang-three-dispatched":
            environment["PYTHONDONTWRITEBYTECODE"] = os.environ[
                "PYTHONDONTWRITEBYTECODE"
            ]
        (submission / "request.json").write_text(
            json.dumps(
                {
                    "schema_version": "pegasus-dispatch-request/v2",
                    "repo_root": str(TARGET.parent),
                    "task": "tests",
                    "args": (
                        ["tests/test_gate.py", "-q", "-rf"]
                        if mode == "hang-three-dispatched"
                        else ["unrelated/test.py", "-q", "-rf"]
                    ),
                    "environment": environment,
                }
            )
            + "\\n",
            encoding="utf-8",
        )


@pytest.mark.xdist_group("mutation-group")
@pytest.mark.parametrize("case", ["one", "two", "three"])
def test_gate(case):
    value = TARGET.read_text(encoding="utf-8").splitlines()[0].split("=", 1)[1].strip()
    desired = {"1": "one", "2": "two", "3": "three"}.get(value)
    if case != desired:
        return
    mode = os.environ.get("IZANAGI_MUTATION_TEST_MODE", "normal")
    if mode == "kill-parent-two" and value == "2":
        os.kill(os.getppid(), signal.SIGKILL)
    if mode == "hang-three-sigterm-ready" and value == "3":
        child = subprocess.Popen(
            [
                sys.executable,
                "-c",
                (
                    "import sys, time; time.sleep(120); "
                    "print('sigterm descendant 120-second absolute cap reached', "
                    "file=sys.stderr, flush=True)"
                ),
            ],
            start_new_session=False,
        )
        try:
            _publish_sigterm_ready(
                Path(os.environ["IZANAGI_MUTATION_TEST_CALLS"]), child.pid
            )
        except BaseException as exc:
            time.sleep(120)
            pytest.fail(
                "sigterm descendant 120-second absolute cap reached after "
                f"readiness publication failure: {type(exc).__name__}: {exc}"
            )
        time.sleep(120)
        pytest.fail(
            "sigterm descendant 120-second absolute cap reached before SIGTERM cleanup"
        )
    if mode in {
        "hang-three",
        "hang-three-dispatched",
        "hang-three-dispatched-missing-request",
        "hang-three-dispatched-malformed-request",
        "hang-three-unrelated",
    } and value == "3":
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
    monkeypatch.setattr(
        MH.site_policy,
        "current_site",
        lambda *, require_evidence=False: MH.site_policy.OTHER,
    )
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
    runner_mode: str = "local",
    attempt_out: Path | None = None,
    wrapper_attempt: int = 1,
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
        runner_mode,
        "--detached",
    ]
    if attempt_out is not None:
        args.extend(
            [
                "--attempt-out",
                str(attempt_out),
                "--wrapper-attempt",
                str(wrapper_attempt),
            ]
        )
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


def _group_argv(
    repo: Path,
    spec: Path,
    out: Path,
    calls: Path,
    mode: Path,
    *,
    resume: bool = False,
) -> list[str]:
    return [
        *_argv(repo, spec, out, calls, mode, resume=resume),
        "-n",
        "2",
        "--dist",
        "loadgroup",
    ]


def _single_spec(path: Path) -> None:
    _write_spec(path, [_mutation("M1", "VALUE = 0", "VALUE = 1", "one")])


def _calls(path: Path) -> list[str]:
    return path.read_text(encoding="utf-8").splitlines() if path.exists() else []


def _install_local_attempt_marker(
    root: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> dict[str, str]:
    from tools.pegasus import dispatch_compute

    dispatch_root = root / "dispatch-root"
    submission = dispatch_root / "submission"
    submission.mkdir(parents=True)
    request = submission / "request.json"
    request.write_bytes(b'{"task":"mutation"}\n')
    (submission / MH.mutation_attempt_marker.COMPUTE_MARKER_NAME).write_text(
        json.dumps(
            {
                "schema_version": "pegasus-compute-visible/v1",
                "pbs_jobid": "0:424242.nqsv",
                "hostname": "bnode114.example",
            }
        )
        + "\n",
        encoding="utf-8",
    )
    binding = MH.mutation_attempt_marker.build_binding(
        dispatch_root=dispatch_root,
        submission_dir=submission,
        pbs_jobid="0:424242.nqsv",
        hostname="bnode114.example",
        request_sha256=hashlib.sha256(request.read_bytes()).hexdigest(),
        is_regular_pbs_jobid=dispatch_compute._is_regular_pbs_jobid,
    )
    monkeypatch.setenv(
        MH.mutation_attempt_marker.MARKER_ENV,
        MH.mutation_attempt_marker.encode_binding(binding),
    )
    monkeypatch.setattr(MH.site_policy, "current_site", _REAL_CURRENT_SITE)
    monkeypatch.setattr(MH.site_policy.socket, "gethostname", lambda: "bnode114")
    return binding


@pytest.mark.parametrize(
    "site", [MH.site_policy.PEGASUS_LOGIN, MH.site_policy.PEGASUS_SUSPECT]
)
def test_local_site_gate_rejects_before_lock_and_collection(
    repo: Path,
    monkeypatch: pytest.MonkeyPatch,
    site: str,
) -> None:
    spec, out, calls, mode = _paths(repo)
    _single_spec(spec)
    observed: list[bool] = []

    def current_site(*, require_evidence: bool = False) -> str:
        observed.append(require_evidence)
        return site

    def unexpected(*_args: object, **_kwargs: object) -> object:
        raise AssertionError("site gate より後の lock/collection へ到達した")

    monkeypatch.setattr(MH.site_policy, "current_site", current_site)
    monkeypatch.setattr(MH, "_lock_for", unexpected)
    monkeypatch.setattr(MH, "_collect_expected_nodes", unexpected)

    assert MH.main(_argv(repo, spec, out, calls, mode)) == 2
    assert observed == [True]
    assert not MH._lock_path_for(repo.resolve()).exists()
    assert not calls.exists()


def test_local_site_gate_requires_evidence_for_nqsv_unreadable_login_hostname(
    repo: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    spec, out, calls, mode = _paths(repo)
    _single_spec(spec)
    assert (
        MH.site_policy.classify_site("pegasus02", {}, has_nqsv=False)
        == MH.site_policy.OTHER
    )
    monkeypatch.setattr(MH.site_policy, "current_site", _REAL_CURRENT_SITE)
    monkeypatch.setattr(MH.site_policy.socket, "gethostname", lambda: "pegasus02")
    monkeypatch.setattr(MH.site_policy, "_has_nqsv", lambda: False)
    monkeypatch.setattr(
        MH,
        "_lock_for",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(
            AssertionError("require_evidence=True なら lock へ到達しない")
        ),
    )

    assert MH.main(_argv(repo, spec, out, calls, mode)) == 2
    assert not calls.exists()


@pytest.mark.parametrize(
    "site", [MH.site_policy.OTHER, MH.site_policy.PEGASUS_COMPUTE]
)
def test_local_site_gate_preserves_other_and_compute(
    repo: Path,
    monkeypatch: pytest.MonkeyPatch,
    site: str,
) -> None:
    spec, out, calls, mode = _paths(repo)
    _single_spec(spec)
    observed: list[bool] = []

    def current_site(*, require_evidence: bool = False) -> str:
        observed.append(require_evidence)
        return site

    monkeypatch.setattr(MH.site_policy, "current_site", current_site)
    argv = _argv(repo, spec, out, calls, mode)
    argv.insert(argv.index("--"), "--plan-only")

    assert MH.main(argv) == 0
    assert observed == [True]
    assert not calls.exists()


def test_dispatch_mode_does_not_consult_local_site_gate(
    repo: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    spec, out, calls, mode = _paths(repo)
    _single_spec(spec)
    document = json.loads(spec.read_text(encoding="utf-8"))
    document["schema"] = "izanagi-dev-wave-mutation-spec/v999"
    spec.write_text(json.dumps(document) + "\n", encoding="utf-8")
    monkeypatch.setattr(
        MH.site_policy,
        "current_site",
        lambda **_kwargs: (_ for _ in ()).throw(
            AssertionError("dispatch mode で local site gate を呼んだ")
        ),
    )
    argv = _argv(repo, spec, out, calls, mode)
    argv[argv.index("--runner-mode") + 1] = "dispatch"

    with pytest.raises(MH.HarnessError, match="未知の spec schema"):
        MH.main(argv)
    assert not calls.exists()


def test_i2_dispatch_attempt_does_not_call_local_marker_validator(
    repo: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    spec, out, calls, mode = _paths(repo)
    _single_spec(spec)
    attempts = repo.parent / "dispatch-attempts.json"
    document = json.loads(spec.read_text(encoding="utf-8"))
    document["schema"] = "izanagi-dev-wave-mutation-spec/v999"
    spec.write_text(json.dumps(document) + "\n", encoding="utf-8")
    monkeypatch.setattr(
        MH.mutation_attempt_marker,
        "require_local_attempt_marker",
        lambda: (_ for _ in ()).throw(
            AssertionError("dispatch mode で marker validator を呼んだ")
        ),
    )

    with pytest.raises(MH.HarnessError, match="未知の spec schema"):
        MH.main(
            _argv(
                repo,
                spec,
                out,
                calls,
                mode,
                runner_mode="dispatch",
                attempt_out=attempts,
            )
        )
    assert not attempts.exists()


def test_i3_local_without_attempt_does_not_call_marker_validator(
    repo: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    spec, out, calls, mode = _paths(repo)
    _single_spec(spec)
    monkeypatch.setattr(
        MH.mutation_attempt_marker,
        "require_local_attempt_marker",
        lambda: (_ for _ in ()).throw(
            AssertionError("attempt 無し local で marker validator を呼んだ")
        ),
    )
    argv = _argv(repo, spec, out, calls, mode)
    argv.insert(argv.index("--"), "--plan-only")

    assert MH.main(argv) == 0
    assert not calls.exists()


def test_m2_direct_harness_local_attempt_without_marker_is_rejected(
    repo: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    spec, out, calls, mode = _paths(repo)
    _single_spec(spec)
    attempts = repo.parent / "attempts.json"
    monkeypatch.setattr(MH.site_policy, "current_site", _REAL_CURRENT_SITE)
    monkeypatch.setattr(MH.site_policy.socket, "gethostname", lambda: "bnode114")
    monkeypatch.delenv(MH.mutation_attempt_marker.MARKER_ENV, raising=False)
    monkeypatch.setattr(
        MH,
        "_lock_for",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(
            AssertionError("marker 拒否後の lock へ到達した")
        ),
    )

    with pytest.raises(MH.HarnessError, match="marker がありません"):
        MH.main(_argv(repo, spec, out, calls, mode, attempt_out=attempts))
    assert not attempts.exists()


def test_direct_harness_forged_marker_is_rejected_before_lock(
    repo: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    spec, out, calls, mode = _paths(repo)
    _single_spec(spec)
    attempts = repo.parent / "attempts.json"
    binding = _install_local_attempt_marker(repo.parent / "marker", monkeypatch)
    forged = {**binding, "request_sha256": "0" * 64}
    monkeypatch.setenv(
        MH.mutation_attempt_marker.MARKER_ENV,
        MH.mutation_attempt_marker.encode_binding(forged),
    )
    monkeypatch.setattr(
        MH,
        "_lock_for",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(
            AssertionError("偽造 marker 拒否後の lock へ到達した")
        ),
    )

    with pytest.raises(MH.HarnessError, match="SHA-256.*不一致"):
        MH.main(_argv(repo, spec, out, calls, mode, attempt_out=attempts))
    assert not attempts.exists()


def test_m11_m12_direct_harness_local_attempt_persists_authorization_and_schema(
    repo: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    spec, out, calls, mode = _paths(repo)
    _single_spec(spec)
    attempts = repo.parent / "attempts.json"
    binding = _install_local_attempt_marker(repo.parent / "marker", monkeypatch)

    assert MH.main(_argv(repo, spec, out, calls, mode, attempt_out=attempts)) == 0

    sidecar = json.loads(attempts.read_text(encoding="utf-8"))
    assert sidecar["schema"] == MH.LOCAL_ATTEMPT_SCHEMA
    assert sidecar["local_authorization"] == binding
    assert [entry["phase"] for entry in sidecar["attempts"]] == [
        "collection",
        "baseline",
        "mutation",
    ]
    assert all(entry["state"] == "finished" for entry in sidecar["attempts"])
    assert all(entry["request"] is None for entry in sidecar["attempts"])

    loaded_spec, loaded_sha256 = MH._load_spec(spec)
    resumed = MH._new_attempt_recorder(
        attempts,
        resume=True,
        wrapper_attempt_ordinal=2,
        head=sidecar["repo_head"],
        spec=loaded_spec,
        spec_sha256=loaded_sha256,
        runner_sha256=sidecar["runner_sha256"],
        tool_sha256=sidecar["tool_sha256"],
        local_authorization=binding,
    )
    assert resumed.document["local_authorization"] == binding
    forged = {**binding, "pbs_jobid": "0:777777.nqsv"}
    with pytest.raises(MH.HarnessError, match="local_authorization.*不一致"):
        MH._new_attempt_recorder(
            attempts,
            resume=True,
            wrapper_attempt_ordinal=2,
            head=sidecar["repo_head"],
            spec=loaded_spec,
            spec_sha256=loaded_sha256,
            runner_sha256=sidecar["runner_sha256"],
            tool_sha256=sidecar["tool_sha256"],
            local_authorization=forged,
        )


def _pid_is_alive(pid: int) -> bool:
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    try:
        stat = Path(f"/proc/{pid}/stat").read_text(encoding="ascii")
    except FileNotFoundError:
        return False
    except OSError:
        return True
    fields = stat.rsplit(") ", 1)
    return len(fields) != 2 or not fields[1].startswith("Z ")


def _sigterm_marker_content(marker: Path) -> str:
    try:
        return marker.read_text(encoding="utf-8")
    except FileNotFoundError:
        return "<not created>"
    except OSError as exc:
        return f"<unreadable: {type(exc).__name__}: {exc}>"


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


def test_missing_rf_is_rejected_before_runner_or_ledger(
    repo: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    spec, out, calls, mode = _paths(repo)
    _single_spec(spec)
    argv = _argv(repo, spec, out, calls, mode)
    argv.remove("-rf")
    runner_starts = 0

    def runner_forbidden(*args: object, **kwargs: object) -> dict[str, object]:
        nonlocal runner_starts
        runner_starts += 1
        raise AssertionError("missing -rf reached the runner")

    monkeypatch.setattr(MH, "_run_tests", runner_forbidden)

    with pytest.raises(MH.HarnessError, match=r"DW-M08.*-rf"):
        MH.main(argv)

    assert runner_starts == 0
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


def test_group_suffixed_expected_node_is_collected_and_killed(repo: Path) -> None:
    spec, out, calls, mode = _paths(repo)
    mutation = _mutation("M1", "VALUE = 0", "VALUE = 1", "one")
    mutation["expected_nodes"] = [
        "tests/test_gate.py::test_gate[one]@mutation-group"
    ]
    _write_spec(spec, [mutation])

    assert MH.main(_group_argv(repo, spec, out, calls, mode)) == 0

    ledger = json.loads(out.read_text(encoding="utf-8"))
    record = ledger["mutations"][0]
    assert record["status"] == "KILLED"
    assert record["failed_nodes"] == [
        "tests/test_gate.py::test_gate[one]@mutation-group"
    ]
    assert ledger["procedure"]["collection"]["collected_nodes"] == [
        "tests/test_gate.py::test_gate[one]",
        "tests/test_gate.py::test_gate[two]",
        "tests/test_gate.py::test_gate[three]",
    ]
    assert ledger["procedure"]["registration_preflight"]["M1"][
        "expected_nodes"
    ] == ["tests/test_gate.py::test_gate[one]@mutation-group"]


def test_group_unsuffixed_expected_node_matches_suffixed_failure(repo: Path) -> None:
    spec, out, calls, mode = _paths(repo)
    _write_spec(spec, [_mutation("M1", "VALUE = 0", "VALUE = 1", "one")])

    assert MH.main(_group_argv(repo, spec, out, calls, mode)) == 0

    record = json.loads(out.read_text(encoding="utf-8"))["mutations"][0]
    assert record["status"] == "KILLED"
    assert record["failed_nodes"] == [
        "tests/test_gate.py::test_gate[one]@mutation-group"
    ]
    assert record["expected_nodes"] == ["tests/test_gate.py::test_gate[one]"]


def test_group_suffixed_expected_node_resume_reuses_valid_ledger(repo: Path) -> None:
    spec, out, calls, mode = _paths(repo)
    mutation = _mutation("M1", "VALUE = 0", "VALUE = 1", "one")
    mutation["expected_nodes"] = [
        "tests/test_gate.py::test_gate[one]@mutation-group"
    ]
    _write_spec(spec, [mutation])
    assert MH.main(_group_argv(repo, spec, out, calls, mode)) == 0
    calls_before_resume = _calls(calls)

    assert MH.main(
        _group_argv(repo, spec, out, calls, mode, resume=True)
    ) == 0

    assert _calls(calls) == calls_before_resume
    record = json.loads(out.read_text(encoding="utf-8"))["mutations"][0]
    assert record["status"] == "KILLED"
    assert record["expected_nodes"] == [
        "tests/test_gate.py::test_gate[one]@mutation-group"
    ]


def test_registration_rejects_group_suffix_alias_as_duplicate(repo: Path) -> None:
    spec, out, calls, mode = _paths(repo)
    mutation = _mutation("M1", "VALUE = 0", "VALUE = 1", "one")
    mutation["expected_nodes"] = [
        "tests/test_gate.py::test_gate[one]",
        "tests/test_gate.py::test_gate[one]@mutation-group",
    ]
    _write_spec(spec, [mutation])

    with pytest.raises(MH.HarnessError, match="expected_nodes .*正規化後に重複"):
        MH.main(_group_argv(repo, spec, out, calls, mode))

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


def test_group_suffix_normalization_keeps_strict_superset_as_mismatch(
    repo: Path,
) -> None:
    status = MH._observed_status(
        result={"timed_out": False, "rc": 1, "artifact_error": None},
        failed=[
            "tests/test_gate.py::test_gate[one]@mutation-group",
            "tests/test_gate.py::test_gate[two]@mutation-group",
        ],
        expected=["tests/test_gate.py::test_gate[one]"],
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


@pytest.mark.parametrize(
    "node",
    [
        (
            "orchestrator/tests/test_axis1_search_runner.py::"
            "test_real_catalog_leaf_resolves_every_runner_field"
            "[arxiv-AX1-20260902-E1-Q1@arxiv]"
        ),
        (
            "orchestrator/tests/test_acceptance_schedule_order.py::"
            "test_g3_splitter_exactly_matches_loadgroup_scheduler[@]"
        ),
        (
            "orchestrator/tests/test_acceptance_schedule_order.py::"
            "test_g3_splitter_exactly_matches_loadgroup_scheduler[試験::場合@直列]"
        ),
        (
            "orchestrator/tests/test_acceptance_schedule_order.py::"
            "test_g3_splitter_exactly_matches_loadgroup_scheduler[試験::場合[値@例]]"
        ),
    ],
)
def test_match_key_preserves_real_parametrize_ids_containing_at(
    repo: Path, node: str
) -> None:
    assert MH._match_key(node, repo) == node


def test_match_key_removes_only_group_after_nested_real_parametrize_id(
    repo: Path,
) -> None:
    suffixed = (
        "orchestrator/tests/test_acceptance_schedule_order.py::"
        "test_g3_splitter_exactly_matches_loadgroup_scheduler"
        "[試験::場合[値@例]]@mutation-group"
    )

    assert MH._match_key(suffixed, repo) == (
        "orchestrator/tests/test_acceptance_schedule_order.py::"
        "test_g3_splitter_exactly_matches_loadgroup_scheduler"
        "[試験::場合[値@例]]"
    )


def test_match_key_does_not_collapse_at_in_realistic_paths(repo: Path) -> None:
    left = "tests@left/x.py::test_case"
    right = "tests@right/x.py::test_case"

    assert MH._match_key(left, repo) == "tests@left/x.py::test_case"
    assert MH._match_key(right, repo) == "tests@right/x.py::test_case"
    assert MH._match_key(left, repo) != MH._match_key(right, repo)
    assert MH._observed_status(
        result={"timed_out": False, "rc": 1, "artifact_error": None},
        failed=[right],
        expected=[left],
        repo=repo,
    ) == "MISMATCH"


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


def test_mutation_nonzero_normal_rc_without_failed_nodes_is_parse_error(
    repo: Path,
) -> None:
    status = MH._observed_status(
        result={"timed_out": False, "rc": 1, "artifact_error": None},
        failed=[],
        expected=["tests/test_gate.py::test_gate[one]"],
        repo=repo,
    )

    assert status == "PARSE_ERROR"


def test_group_suffixed_expected_with_nonzero_rc_and_no_failures_is_parse_error(
    repo: Path,
) -> None:
    status = MH._observed_status(
        result={"timed_out": False, "rc": 1, "artifact_error": None},
        failed=[],
        expected=["tests/test_gate.py::test_gate[one]@mutation-group"],
        repo=repo,
    )

    assert status == "PARSE_ERROR"


def test_baseline_nonzero_normal_rc_without_failed_nodes_is_parse_error(
    repo: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    spec_path, _out, _calls_path, _mode = _paths(repo)
    _single_spec(spec_path)
    spec, _spec_sha256 = MH._load_spec(spec_path)

    monkeypatch.setattr(
        MH,
        "_run_tests",
        lambda *args, **kwargs: {
            "rc": 1,
            "timed_out": False,
            "job_stdout": "1 failed in 0.01s\n",
            "duration_s": 0.01,
            "artifact_error": None,
        },
    )

    baseline = MH._baseline(
        repo,
        spec,
        [sys.executable, "-m", "pytest"],
        "local",
        head=MH._repo_head(repo),
        spec_sha256="spec",
        registration_sha256="registration",
        runner_sha256="runner",
        tool_sha256="tool",
        collection_sha256="collection",
    )

    assert baseline["status"] == "PARSE_ERROR"
    assert baseline["rc"] == 1
    assert baseline["failed_nodes"] == []


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


def test_resume_rejects_orphan_stop_sidecar_before_runner_without_hold(
    repo: Path,
) -> None:
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
    before = _calls(calls)
    sidecar = Path(f"{out.resolve()}.orphan-stop.json")
    sidecar_payload = {
        "reason": {
            "code": "orphan-hold",
            "hold_error": "injected double hold write failure",
        }
    }
    sidecar.write_text(json.dumps(sidecar_payload) + "\n", encoding="utf-8")
    original_sidecar = sidecar.read_bytes()
    mode.write_text("normal\n", encoding="utf-8")

    with pytest.raises(MH.HarnessError) as caught:
        MH.main(_argv(repo, spec, out, calls, mode, resume=True))

    message = str(caught.value)
    assert str(sidecar) in message
    assert "reason.hold_error=injected double hold write failure" in message
    assert message.index("対象の不在または終端") < message.index("dirty path の復元")
    assert message.index("dirty path の復元") < message.index("clean/HEAD 確認")
    assert message.index("clean/HEAD 確認") < message.index("hold と sidecar の手動削除")
    assert _calls(calls) == before
    assert sidecar.read_bytes() == original_sidecar
    assert not (repo / "output" / "pegasus-dispatch" / MH.ORPHAN_HOLD_NAME).exists()


def test_fresh_rejects_orphan_stop_sidecar_before_runner_without_hold(
    repo: Path,
) -> None:
    spec, out, calls, mode = _paths(repo)
    _single_spec(spec)
    sidecar = Path(f"{out.resolve()}.orphan-stop.json")
    sidecar.write_text('{"reason": {"code": "orphan-hold"}}\n', encoding="utf-8")

    with pytest.raises(MH.HarnessError) as caught:
        MH.main(_argv(repo, spec, out, calls, mode))

    assert str(sidecar) in str(caught.value)
    assert not calls.exists()
    assert not out.exists()
    assert not (repo / "output" / "pegasus-dispatch" / MH.ORPHAN_HOLD_NAME).exists()


def test_orphan_stop_sidecar_lstat_error_rejects_before_runner(
    repo: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    spec, out, calls, mode = _paths(repo)
    _single_spec(spec)
    sidecar = Path(f"{out.resolve()}.orphan-stop.json")
    real_lstat = os.lstat

    def indeterminate(path, *args, **kwargs):
        if Path(path) == sidecar:
            raise OSError("injected sidecar lstat failure")
        return real_lstat(path, *args, **kwargs)

    monkeypatch.setattr(MH.os, "lstat", indeterminate)

    with pytest.raises(MH.HarnessError) as caught:
        MH.main(_argv(repo, spec, out, calls, mode))

    assert str(sidecar) in str(caught.value)
    assert not calls.exists()
    assert not out.exists()


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
    assert not MH._orphan_stop_path(out).exists()
    assert (repo / "target.py").read_text(encoding="utf-8") == _git(
        repo, "show", "HEAD:target.py"
    )


def test_local_timeout_after_dispatch_submission_stops_without_terminal_record(
    repo: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
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
    document["hang_timeout_seconds"] = 1
    spec.write_text(json.dumps(document) + "\n", encoding="utf-8")
    mode.write_text("hang-three-dispatched\n", encoding="utf-8")
    (repo / ".git" / "info" / "exclude").write_text(
        "/output/\n", encoding="utf-8"
    )

    def receipt_recovery_forbidden(*args: object, **kwargs: object) -> None:
        raise AssertionError("local timeout must not interpret a dispatch receipt")

    monkeypatch.setattr(MH, "_recover_dispatch_request", receipt_recovery_forbidden)

    assert MH.main(_argv(repo, spec, out, calls, mode)) == 2

    ledger = json.loads(out.read_text(encoding="utf-8"))
    assert ledger["mutations"] == []
    sidecar = json.loads(
        MH._orphan_stop_path(out).read_text(encoding="utf-8")
    )
    assert sidecar["reason"]["code"] == "runner-mode-violation"
    assert sidecar["reason"]["phase"] == "mutation"
    assert sidecar["reason"]["mutation_id"] == "H1"
    assert sidecar["reason"]["hold_latched"] is False
    assert sidecar["reason"]["job_may_have_been_submitted"] is True
    assert sidecar["reason"]["verification_required"] is True
    assert sidecar["reason"]["dispatch_submission_state"] == "matched"
    assert sidecar["active_record"]["new_dispatch_submission"] is True
    assert sidecar["active_record"]["dispatch_submission"]["state"] == "matched"
    submission = repo / "output" / "pegasus-dispatch" / "queued-request"
    assert sidecar["active_record"]["dispatch_submission"]["corroboration"] == [
        {
            "submission_dir": str(submission),
            "nonce_matches": True,
            "repo_matches": True,
            "task_matches": True,
            "args_match": False,
        }
    ]
    assert not (
        repo / "output" / "pegasus-dispatch" / MH.ORPHAN_HOLD_NAME
    ).exists()
    assert (repo / "target.py").read_text(encoding="utf-8").startswith("VALUE = 3\n")


def test_local_timeout_ignores_conclusively_unrelated_submission(
    repo: Path,
) -> None:
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
    document["hang_timeout_seconds"] = 1
    spec.write_text(json.dumps(document) + "\n", encoding="utf-8")
    mode.write_text("hang-three-unrelated\n", encoding="utf-8")
    (repo / ".git" / "info" / "exclude").write_text(
        "/output/\n", encoding="utf-8"
    )

    assert MH.main(_argv(repo, spec, out, calls, mode)) == 0

    ledger = json.loads(out.read_text(encoding="utf-8"))
    assert ledger["mutations"][0]["status"] == "TIMEOUT"
    assert not MH._orphan_stop_path(out).exists()
    assert not (
        repo / "output" / "pegasus-dispatch" / MH.ORPHAN_HOLD_NAME
    ).exists()
    assert (repo / "target.py").read_text(encoding="utf-8") == _git(
        repo, "show", "HEAD:target.py"
    )


def test_local_timeout_inventory_failure_stops_without_terminal_record(
    repo: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
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
    document["hang_timeout_seconds"] = 1
    spec.write_text(json.dumps(document) + "\n", encoding="utf-8")
    mode.write_text("hang-three\n", encoding="utf-8")
    (repo / ".git" / "info" / "exclude").write_text(
        "/output/\n", encoding="utf-8"
    )
    real_inventory = MH._dispatch_submission_inventory
    mutation_inventory_calls = 0

    def inventory(root: Path) -> set[Path]:
        nonlocal mutation_inventory_calls
        if (root / "target.py").read_text(encoding="utf-8").startswith("VALUE = 3\n"):
            mutation_inventory_calls += 1
            if mutation_inventory_calls == 2:
                raise MH.HarnessError("injected inventory failure")
        return real_inventory(root)

    monkeypatch.setattr(MH, "_dispatch_submission_inventory", inventory)

    assert MH.main(_argv(repo, spec, out, calls, mode)) == 2

    ledger = json.loads(out.read_text(encoding="utf-8"))
    assert ledger["mutations"] == []
    sidecar = json.loads(MH._orphan_stop_path(out).read_text(encoding="utf-8"))
    assert sidecar["reason"]["code"] == "runner-mode-evidence-unavailable"
    assert sidecar["reason"]["dispatch_submission_state"] == "indeterminate"
    assert sidecar["active_record"]["new_dispatch_submission"] is None
    assert sidecar["active_record"]["dispatch_submission"]["errors"] == [
        {"code": "after-inventory-failed", "error_type": "HarnessError"}
    ]
    assert not (
        repo / "output" / "pegasus-dispatch" / MH.ORPHAN_HOLD_NAME
    ).exists()
    assert (repo / "target.py").read_text(encoding="utf-8").startswith("VALUE = 3\n")


@pytest.mark.parametrize(
    ("mode_value", "request_error_type"),
    [
        pytest.param(
            "hang-three-dispatched-missing-request",
            "HarnessError",
            id="missing",
        ),
        pytest.param(
            "hang-three-dispatched-malformed-request",
            "JSONDecodeError",
            id="malformed",
        ),
    ],
)
def test_local_timeout_with_unreadable_dispatch_request_stops_as_evidence_unavailable(
    repo: Path,
    mode_value: str,
    request_error_type: str,
) -> None:
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
    document["hang_timeout_seconds"] = 1
    spec.write_text(json.dumps(document) + "\n", encoding="utf-8")
    mode.write_text(mode_value + "\n", encoding="utf-8")
    (repo / ".git" / "info" / "exclude").write_text(
        "/output/\n", encoding="utf-8"
    )

    assert MH.main(_argv(repo, spec, out, calls, mode)) == 2

    ledger = json.loads(out.read_text(encoding="utf-8"))
    assert ledger["mutations"] == []
    sidecar = json.loads(MH._orphan_stop_path(out).read_text(encoding="utf-8"))
    assert sidecar["reason"]["code"] == "runner-mode-evidence-unavailable"
    assert sidecar["reason"]["dispatch_submission_state"] == "indeterminate"
    assert sidecar["active_record"]["new_dispatch_submission"] is None
    submission = repo / "output" / "pegasus-dispatch" / "queued-request"
    assert sidecar["active_record"]["dispatch_submission"]["errors"] == [
        {
            "submission_dir": str(submission),
            "code": "request-unreadable",
            "error_type": request_error_type,
        }
    ]
    assert not (
        repo / "output" / "pegasus-dispatch" / MH.ORPHAN_HOLD_NAME
    ).exists()
    assert (repo / "target.py").read_text(encoding="utf-8").startswith("VALUE = 3\n")


def test_preexisting_dispatch_hold_blocks_local_runner_start(repo: Path) -> None:
    spec, out, calls, mode = _paths(repo)
    _single_spec(spec)
    (repo / ".git" / "info" / "exclude").write_text(
        "/output/\n", encoding="utf-8"
    )
    hold = repo / "output" / "pegasus-dispatch" / MH.ORPHAN_HOLD_NAME
    hold.parent.mkdir(parents=True)
    hold.write_text("{}\n", encoding="utf-8")

    assert MH.main(_argv(repo, spec, out, calls, mode)) == 2

    assert not calls.exists()
    assert hold.is_file()
    stop = json.loads(MH._orphan_stop_path(out).read_text(encoding="utf-8"))
    assert stop["reason"]["code"] == "orphan-hold"
    assert stop["reason"]["phase"] == "collection"


def test_preexisting_dispatch_request_ledger_blocks_local_runner_start(
    repo: Path,
) -> None:
    spec, out, calls, mode = _paths(repo)
    _single_spec(spec)
    (repo / ".git" / "info" / "exclude").write_text(
        "/output/\n", encoding="utf-8"
    )
    ledger = (
        repo
        / "output"
        / "pegasus-dispatch"
        / MH.ORPHAN_HOLD_DIR_NAME
        / "424242.nqsv.json"
    )
    ledger.parent.mkdir(parents=True)
    ledger.write_text("{}\n", encoding="utf-8")

    assert MH.main(_argv(repo, spec, out, calls, mode)) == 2

    assert not calls.exists()
    assert ledger.is_file()
    stop = json.loads(MH._orphan_stop_path(out).read_text(encoding="utf-8"))
    assert stop["reason"]["code"] == "orphan-hold"
    assert stop["reason"]["phase"] == "collection"


def test_dispatch_request_ledger_scan_error_is_fail_closed(
    repo: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    ledger = repo / "output" / "pegasus-dispatch" / MH.ORPHAN_HOLD_DIR_NAME
    ledger.mkdir(parents=True)
    real_scandir = MH.os.scandir

    def fail_descriptor_scan(path):
        if isinstance(path, int):
            raise PermissionError("injected ledger scan denial")
        return real_scandir(path)

    monkeypatch.setattr(MH.os, "scandir", fail_descriptor_scan)
    assert MH._dispatch_orphan_hold_present(repo) is True


def test_dispatch_timeout_latches_hold_preserves_bytes_stops_next_and_writes_stop(
    repo: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    spec, out, calls, mode = _paths(repo)
    _write_spec(
        spec,
        [
            _mutation("M1", "VALUE = 0", "VALUE = 1", "one"),
            _mutation("M2", "VALUE = 0", "VALUE = 2", "two"),
        ],
    )
    (repo / ".git" / "info" / "exclude").write_text(
        "/output/\n", encoding="utf-8"
    )
    argv = _argv(repo, spec, out, calls, mode)
    argv[argv.index("--runner-mode") + 1] = "dispatch"
    run_count = 0

    monkeypatch.setattr(MH, "_runner_identity", lambda *args, **kwargs: {"runner": "fixture"})
    monkeypatch.setattr(MH, "_tool_identity", lambda *args, **kwargs: {"tool": "fixture"})
    monkeypatch.setattr(
        MH,
        "_collect_expected_nodes",
        lambda *args, **kwargs: {"status": "fixture-collection"},
    )
    monkeypatch.setattr(MH, "_validate_collection_record", lambda *args, **kwargs: None)
    monkeypatch.setattr(
        MH,
        "_baseline",
        lambda *args, **kwargs: {
            "status": "PASSED",
            "rc": 0,
            "failed_nodes": [],
        },
    )
    monkeypatch.setattr(MH, "_validate_baseline_record", lambda *args, **kwargs: None)

    def timed_out(*args: object, **kwargs: object) -> dict[str, object]:
        nonlocal run_count
        run_count += 1
        return {
            "rc": None,
            "timed_out": True,
            "output": "dispatcher timed out",
            "job_stdout": "dispatcher timed out",
            "duration_s": 1.0,
            "artifact_error": None,
            "request": None,
        }

    monkeypatch.setattr(MH, "_run_tests", timed_out)

    assert MH.main(argv) == 2

    assert run_count == 1
    assert (repo / "target.py").read_text(encoding="utf-8").startswith("VALUE = 1\n")
    hold = repo / "output" / "pegasus-dispatch" / MH.ORPHAN_HOLD_NAME
    assert hold.is_file()
    ledger_path = out
    ledger = json.loads(ledger_path.read_text(encoding="utf-8"))
    assert ledger["schema"] == MH.LEDGER_SCHEMA
    assert ledger["mutations"] == []
    out = MH._orphan_stop_path(ledger_path)
    stop = json.loads(out.read_text(encoding="utf-8"))
    assert stop["schema"] == MH.ORPHAN_STOP_SCHEMA
    assert stop["reason"]["code"] == "orphan-hold"
    assert stop["reason"]["phase"] == "mutation"
    assert stop["reason"]["mutation_id"] == "M1"
    assert stop["reason"]["source_state"] == "mutation-left-in-place"
    assert stop["reason"]["dirty_paths"] == ["target.py"]
    assert stop["ledger_path"] == str(ledger_path)
    assert "partial_ledger" not in stop


def test_dispatch_hold_write_failure_stops_harness_without_restore_or_next_runner(
    repo: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    spec, out, calls, mode = _paths(repo)
    _write_spec(
        spec,
        [
            _mutation("M1", "VALUE = 0", "VALUE = 1", "one"),
            _mutation("M2", "VALUE = 0", "VALUE = 2", "two"),
        ],
    )
    (repo / ".git" / "info" / "exclude").write_text(
        "/output/\n", encoding="utf-8"
    )
    runner = repo.parent / "dispatch_hold_failure.py"
    runner_calls = repo.parent / "dispatch-runner-calls.txt"
    runner.write_text(
        """\
import os
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, os.environ["IZANAGI_SOURCE_ROOT"])
from tools.pegasus import dispatch_compute as DC


class Clock:
    def __init__(self):
        self.now = 0.0

    def __call__(self):
        return self.now

    def sleep(self, seconds):
        self.now += seconds


class Scheduler:
    def __call__(self, command, **kwargs):
        values = list(command)
        if values == ["qstat", "-Q"]:
            return subprocess.CompletedProcess(values, 0, "gen_S enabled\\n", "")
        if values[0] == "qsub":
            return subprocess.CompletedProcess(
                values, 0, "Request 123.server submitted to queue: gen_S.\\n", ""
            )
        if values[:2] == ["qstat", "-f"]:
            return subprocess.CompletedProcess(
                values, 0, "Request ID = 123.server\\nRequest State = HLD\\n", ""
            )
        if values[0] == "qdel":
            return subprocess.CompletedProcess(values, 153, "", "not deleted")
        raise AssertionError(values)


calls = Path(os.environ["IZANAGI_DISPATCH_RUNNER_CALLS"])
with calls.open("a", encoding="utf-8") as stream:
    stream.write("run\\n")
    stream.flush()
    os.fsync(stream.fileno())

real_write = DC._write_json_atomic_replace


def fail_hold(path, payload, **kwargs):
    if (
        Path(path).name == DC._ORPHAN_HOLD_NAME
        and not kwargs.get("create_only", False)
    ):
        raise OSError("injected dispatcher hold write failure")
    return real_write(path, payload, **kwargs)


DC._write_json_atomic_replace = fail_hold
clock = Clock()
raise SystemExit(
    DC.dispatch(
        [],
        repo_root=Path.cwd(),
        output_root=Path.cwd() / "output" / "pegasus-dispatch",
        run_command=Scheduler(),
        clock=clock,
        sleep=clock.sleep,
        queue_wait_timeout_s=0,
        accounting_grace_s=0,
        poll_interval_s=1,
        immediate_qstat_attempts=1,
        cleanup_budget_s=1,
        nonce="hold-write-failure",
    )
)
""",
        encoding="utf-8",
    )
    monkeypatch.setenv("IZANAGI_SOURCE_ROOT", str(_REPO))
    monkeypatch.setenv("IZANAGI_DISPATCH_RUNNER_CALLS", str(runner_calls))
    argv = _argv(repo, spec, out, calls, mode)
    argv[argv.index("--runner-mode") + 1] = "dispatch"
    separator = argv.index("--")
    argv[separator + 1 :] = [sys.executable, str(runner), "-rf"]
    monkeypatch.setattr(MH, "_runner_identity", lambda *args, **kwargs: {"runner": "fixture"})
    monkeypatch.setattr(MH, "_tool_identity", lambda *args, **kwargs: {"tool": "fixture"})
    monkeypatch.setattr(
        MH,
        "_collect_expected_nodes",
        lambda *args, **kwargs: {"status": "fixture-collection"},
    )
    monkeypatch.setattr(MH, "_validate_collection_record", lambda *args, **kwargs: None)
    monkeypatch.setattr(
        MH,
        "_baseline",
        lambda *args, **kwargs: {"status": "PASSED", "rc": 0, "failed_nodes": []},
    )
    monkeypatch.setattr(MH, "_validate_baseline_record", lambda *args, **kwargs: None)

    assert MH.main(argv) == 2

    assert runner_calls.read_text(encoding="utf-8").splitlines() == ["run"]
    assert (repo / "target.py").read_text(encoding="utf-8").startswith("VALUE = 1\n")
    hold = repo / "output" / "pegasus-dispatch" / MH.ORPHAN_HOLD_NAME
    assert hold.is_file()
    ledger = json.loads(out.read_text(encoding="utf-8"))
    assert ledger["schema"] == MH.LEDGER_SCHEMA
    assert ledger["mutations"] == []
    stop_path = MH._orphan_stop_path(out)
    assert stop_path.is_file()
    stop = json.loads(stop_path.read_text(encoding="utf-8"))
    assert stop["reason"]["code"] == "orphan-hold"
    assert stop["reason"]["mutation_id"] == "M1"
    assert stop["ledger_path"] == str(out)


def test_dispatch_non_timeout_parse_error_is_not_an_orphan_condition(
    repo: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    spec_path, _out, _calls_path, _mode = _paths(repo)
    _single_spec(spec_path)
    spec, spec_sha256 = MH._load_spec(spec_path)
    head = MH._repo_head(repo)
    originals = MH._read_head_sources(repo, head, spec)
    registration = MH._validate_registrations(repo, spec, originals)
    monkeypatch.setattr(
        MH,
        "_run_tests",
        lambda *args, **kwargs: {
            "rc": 3,
            "timed_out": False,
            "output": "parse failure",
            "job_stdout": "parse failure",
            "duration_s": 0.1,
            "artifact_error": None,
        },
    )

    record = MH._apply_mutation(
        repo,
        head,
        originals,
        spec.mutations[0],
        spec,
        [sys.executable, "ignored", "-rf"],
        "dispatch",
        registration["M1"],
        spec_sha256=spec_sha256,
        runner_sha256="runner",
        tool_sha256="tool",
        collection_sha256="collection",
    )

    assert record["status"] == "PARSE_ERROR"
    assert not (repo / "output" / "pegasus-dispatch" / MH.ORPHAN_HOLD_NAME).exists()
    assert (repo / "target.py").read_text(encoding="utf-8") == originals["target.py"]


def test_orphan_stop_records_origin_and_verification_errors_without_restoring(
    repo: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    spec, out, calls, mode = _paths(repo)
    _single_spec(spec)
    (repo / ".git" / "info" / "exclude").write_text(
        "/output/\n", encoding="utf-8"
    )
    argv = _argv(repo, spec, out, calls, mode)
    argv[argv.index("--runner-mode") + 1] = "dispatch"
    monkeypatch.setattr(MH, "_runner_identity", lambda *args, **kwargs: {"runner": "fixture"})
    monkeypatch.setattr(MH, "_tool_identity", lambda *args, **kwargs: {"tool": "fixture"})
    monkeypatch.setattr(
        MH,
        "_collect_expected_nodes",
        lambda *args, **kwargs: {"status": "fixture-collection"},
    )
    monkeypatch.setattr(MH, "_validate_collection_record", lambda *args, **kwargs: None)
    monkeypatch.setattr(
        MH,
        "_baseline",
        lambda *args, **kwargs: {"status": "PASSED", "rc": 0, "failed_nodes": []},
    )
    monkeypatch.setattr(MH, "_validate_baseline_record", lambda *args, **kwargs: None)

    def runner_failure(*args: object, **kwargs: object) -> dict[str, object]:
        hold = repo / "output" / "pegasus-dispatch" / MH.ORPHAN_HOLD_NAME
        hold.parent.mkdir(parents=True)
        hold.write_text("{}\n", encoding="utf-8")
        raise RuntimeError("injected runner failure")

    real_assert_dirt = MH._assert_only_expected_dirt
    dirt_checks = 0

    def verification_failure(*args: object, **kwargs: object) -> None:
        nonlocal dirt_checks
        dirt_checks += 1
        if dirt_checks == 2:
            raise MH.HarnessError("injected preservation verification failure")
        real_assert_dirt(*args, **kwargs)

    monkeypatch.setattr(MH, "_run_tests", runner_failure)
    monkeypatch.setattr(MH, "_assert_only_expected_dirt", verification_failure)

    assert MH.main(argv) == 2

    assert (repo / "target.py").read_text(encoding="utf-8").startswith("VALUE = 1\n")
    stop = json.loads(MH._orphan_stop_path(out).read_text(encoding="utf-8"))
    reason = stop["reason"]
    assert reason["origin_error_type"] == "RuntimeError"
    assert reason["origin_error_message"] == "injected runner failure"
    assert reason["verification_error_type"] == "HarnessError"
    assert reason["verification_error_message"] == (
        "injected preservation verification failure"
    )


def test_signal_unwind_with_hold_marks_restore_skipped_and_preserves_mutation(
    repo: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    spec_path, _out, _calls_path, _mode = _paths(repo)
    _single_spec(spec_path)
    spec, spec_sha256 = MH._load_spec(spec_path)
    head = MH._repo_head(repo)
    originals = MH._read_head_sources(repo, head, spec)
    registration = MH._validate_registrations(repo, spec, originals)
    (repo / ".git" / "info" / "exclude").write_text(
        "/output/\n", encoding="utf-8"
    )

    def interrupted(*args: object, **kwargs: object) -> dict[str, object]:
        hold = repo / "output" / "pegasus-dispatch" / MH.ORPHAN_HOLD_NAME
        hold.parent.mkdir(parents=True)
        hold.write_text("{}\n", encoding="utf-8")
        raise MH.SignalAbort(signal.SIGTERM)

    monkeypatch.setattr(MH, "_run_tests", interrupted)

    with pytest.raises(MH.SignalAbort) as raised:
        MH._apply_mutation(
            repo,
            head,
            originals,
            spec.mutations[0],
            spec,
            [sys.executable, "ignored", "-rf"],
            "dispatch",
            registration["M1"],
            spec_sha256=spec_sha256,
            runner_sha256="runner",
            tool_sha256="tool",
            collection_sha256="collection",
        )

    assert raised.value.orphan_stop is not None
    assert raised.value.orphan_stop.source_state == "mutation-left-in-place"
    assert (repo / "target.py").read_text(encoding="utf-8").startswith("VALUE = 1\n")


@pytest.mark.parametrize("phase", ["collection", "baseline"])
def test_preexisting_hold_blocks_collection_and_baseline_runner_start(
    repo: Path,
    monkeypatch: pytest.MonkeyPatch,
    phase: str,
) -> None:
    spec_path, _out, _calls_path, _mode = _paths(repo)
    _single_spec(spec_path)
    spec, spec_sha256 = MH._load_spec(spec_path)
    head = MH._repo_head(repo)
    (repo / ".git" / "info" / "exclude").write_text(
        "/output/\n", encoding="utf-8"
    )
    hold = repo / "output" / "pegasus-dispatch" / MH.ORPHAN_HOLD_NAME
    hold.parent.mkdir(parents=True)
    hold.write_text("{}\n", encoding="utf-8")
    starts = 0

    def forbidden(*args: object, **kwargs: object) -> dict[str, object]:
        nonlocal starts
        starts += 1
        raise AssertionError("runner started despite orphan hold")

    monkeypatch.setattr(MH, "_run_tests", forbidden)
    with pytest.raises(MH.OrphanHoldStop):
        if phase == "collection":
            MH._collect_expected_nodes(
                repo,
                spec,
                [sys.executable, "ignored", "-rf"],
                "dispatch",
                head=head,
                spec_sha256=spec_sha256,
                runner_sha256="runner",
                tool_sha256="tool",
            )
        else:
            MH._baseline(
                repo,
                spec,
                [sys.executable, "ignored", "-rf"],
                "dispatch",
                head=head,
                spec_sha256=spec_sha256,
                registration_sha256="registration",
                runner_sha256="runner",
                tool_sha256="tool",
                collection_sha256="collection",
            )
    assert starts == 0


def test_harness_lstat_error_blocks_before_mutation_runner(
    repo: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    spec_path, _out, _calls_path, _mode = _paths(repo)
    _single_spec(spec_path)
    spec, spec_sha256 = MH._load_spec(spec_path)
    head = MH._repo_head(repo)
    originals = MH._read_head_sources(repo, head, spec)
    registration = MH._validate_registrations(repo, spec, originals)
    hold = repo / "output" / "pegasus-dispatch" / MH.ORPHAN_HOLD_NAME
    real_lstat = os.lstat
    starts = 0

    def indeterminate(path, *args, **kwargs):
        if Path(path) == hold:
            raise OSError("injected lstat failure")
        return real_lstat(path, *args, **kwargs)

    def forbidden(*args: object, **kwargs: object) -> dict[str, object]:
        nonlocal starts
        starts += 1
        raise AssertionError("runner started after indeterminate hold check")

    monkeypatch.setattr(MH.os, "lstat", indeterminate)
    monkeypatch.setattr(MH, "_run_tests", forbidden)

    with pytest.raises(MH.OrphanHoldStop):
        MH._apply_mutation(
            repo,
            head,
            originals,
            spec.mutations[0],
            spec,
            [sys.executable, "ignored", "-rf"],
            "dispatch",
            registration["M1"],
            spec_sha256=spec_sha256,
            runner_sha256="runner",
            tool_sha256="tool",
            collection_sha256="collection",
        )
    assert starts == 0
    assert (repo / "target.py").read_text(encoding="utf-8") == originals["target.py"]


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


def test_sigterm_handler_stops_child_and_restores_active_mutation(
    repo: Path, record_property: Callable[[str, object], None]
) -> None:
    """Returning to elapsed-time stage inference fails the exact pre/post-signal event trace."""
    spec, out, calls, mode = _paths(repo)
    discovery = calls.with_name("sigterm-discovery-v1.json").resolve()
    marker = calls.with_name("sigterm-ready-v1.json").resolve()
    stage_trace = calls.with_name("sigterm-stage-trace-v1.jsonl").resolve()
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
    document["hang_timeout_seconds"] = 60
    spec.write_text(json.dumps(document) + "\n", encoding="utf-8")
    mode.write_text("hang-three-sigterm-ready\n", encoding="utf-8")
    command = [sys.executable, str(_TOOL), *_argv(repo, spec, out, calls, mode)]
    process = subprocess.Popen(
        command,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    spawned_monotonic_ns = time.monotonic_ns()
    discovery_payload: dict[str, object] | None = None
    marker_payload: dict[str, object] | None = None
    cleanup_deadline: float | None = None

    def cleanup_warning(message: str) -> None:
        print(f"WARNING: {message}", file=sys.stderr, flush=True)

    def read_wait_record(path: Path, label: str) -> dict[str, object] | None:
        try:
            content = path.read_text(encoding="utf-8")
        except FileNotFoundError:
            return None
        except OSError as exc:
            pytest.fail(
                f"{label} unreadable: path={str(path)!r}; "
                f"error={type(exc).__name__}: {exc}"
            )
        try:
            candidate = json.loads(content)
        except json.JSONDecodeError as exc:
            pytest.fail(
                f"{label} is corrupt JSON: path={str(path)!r}; "
                f"content={content!r}; error={exc}"
            )
        if not isinstance(candidate, dict):
            pytest.fail(
                f"{label} is corrupt: JSON root is not an object: "
                f"path={str(path)!r}; content={content!r}"
            )
        return candidate

    def positive_record_int(
        payload: dict[str, object], field: str, label: str
    ) -> int:
        value = payload.get(field)
        if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
            pytest.fail(
                f"{label} is corrupt: {field} must be a positive int; "
                f"value={value!r}"
            )
        return value

    def read_stage_trace() -> list[dict[str, str]]:
        try:
            lines = stage_trace.read_text(encoding="utf-8").splitlines()
        except OSError as exc:
            pytest.fail(
                "sigterm causal stage trace is unavailable: "
                f"path={stage_trace}; error={type(exc).__name__}: {exc}"
            )
        try:
            records = [json.loads(line) for line in lines]
        except json.JSONDecodeError as exc:
            pytest.fail(
                "sigterm causal stage trace is corrupt: "
                f"path={stage_trace}; error={exc}"
            )
        return records

    def communicate_or_fail(label: str) -> tuple[str, str]:
        try:
            stdout, stderr = process.communicate(timeout=20)
        except subprocess.TimeoutExpired as exc:
            pytest.fail(
                f"{label} communicate 20-second timeout exceeded: "
                f"partial_stdout={exc.output!r}; partial_stderr={exc.stderr!r}; "
                f"calls={_calls(calls)!r}; "
                f"discovery_content={_sigterm_marker_content(discovery)!r}; "
                f"marker_content={_sigterm_marker_content(marker)!r}"
            )
        return stdout, stderr

    def fail_early_exit(rc: int) -> None:
        _stdout, stderr = communicate_or_fail("harness early-exit diagnostic")
        pytest.fail(
            "harness exited before sigterm readiness: "
            f"rc={rc}; stderr={stderr!r}; calls={_calls(calls)!r}; "
            f"discovery_path={str(discovery)!r}; "
            f"discovery_content={_sigterm_marker_content(discovery)!r}; "
            f"marker_path={str(marker)!r}; "
            f"marker_content={_sigterm_marker_content(marker)!r}"
        )

    try:
        deadline = time.monotonic() + 30
        while True:
            rc = process.poll()
            if rc is not None:
                fail_early_exit(rc)

            if discovery_payload is None:
                discovery_payload = read_wait_record(
                    discovery, "sigterm discovery record"
                )
            if marker_payload is None:
                marker_payload = read_wait_record(
                    marker, "sigterm readiness marker"
                )
            if marker_payload is not None and discovery_payload is None:
                pytest.fail(
                    "sigterm readiness marker appeared before the required discovery "
                    f"record: discovery_path={str(discovery)!r}; "
                    f"marker_content={_sigterm_marker_content(marker)!r}"
                )
            if marker_payload is not None and discovery_payload is not None:
                break

            if time.monotonic() >= deadline:
                rc = process.poll()
                if rc is not None:
                    fail_early_exit(rc)
                process.kill()
                _stdout, stderr = communicate_or_fail(
                    "readiness-deadline cleanup"
                )
                pytest.fail(
                    "sigterm readiness 30-second deadline exceeded: "
                    f"rc={process.returncode}; stderr={stderr!r}; "
                    f"calls={_calls(calls)!r}; "
                    f"discovery_path={str(discovery)!r}; "
                    f"discovery_content={_sigterm_marker_content(discovery)!r}; "
                    f"marker_path={str(marker)!r}; "
                    f"marker_content={_sigterm_marker_content(marker)!r}"
                )
            time.sleep(0.02)

        discovery_required = {
            "schema",
            "value",
            "pid",
            "pgid",
            "written_monotonic_ns",
        }
        discovery_missing = discovery_required - set(discovery_payload)
        if discovery_missing:
            pytest.fail(
                "sigterm discovery record is corrupt: "
                f"missing_fields={sorted(discovery_missing)!r}; "
                f"payload={discovery_payload!r}"
            )
        if (
            discovery_payload.get("schema")
            != "izanagi-mutation-sigterm-discovery/v1"
            or discovery_payload.get("value") != "3"
        ):
            pytest.fail(
                "sigterm discovery record is corrupt: schema/value mismatch; "
                f"payload={discovery_payload!r}"
            )
        discovery_pid = positive_record_int(
            discovery_payload, "pid", "sigterm discovery record"
        )
        discovery_pgid = positive_record_int(
            discovery_payload, "pgid", "sigterm discovery record"
        )
        written_monotonic_ns = positive_record_int(
            discovery_payload,
            "written_monotonic_ns",
            "sigterm discovery record",
        )

        marker_fields = {
            "schema",
            "pid",
            "child_pid",
            "pgid",
            "ready_monotonic_ns",
        }
        if set(marker_payload) != marker_fields:
            pytest.fail(
                "sigterm readiness marker is corrupt: field set mismatch; "
                f"expected={sorted(marker_fields)!r}; "
                f"actual={sorted(marker_payload)!r}"
            )
        if marker_payload.get("schema") != "izanagi-mutation-sigterm-ready/v1":
            pytest.fail(
                "sigterm readiness marker is corrupt: schema mismatch; "
                f"payload={marker_payload!r}"
            )
        marker_pid = positive_record_int(
            marker_payload, "pid", "sigterm readiness marker"
        )
        child_pid = positive_record_int(
            marker_payload, "child_pid", "sigterm readiness marker"
        )
        pgid = positive_record_int(
            marker_payload, "pgid", "sigterm readiness marker"
        )
        ready_monotonic_ns = positive_record_int(
            marker_payload,
            "ready_monotonic_ns",
            "sigterm readiness marker",
        )
        if discovery_pid != marker_pid or discovery_pgid != pgid:
            pytest.fail(
                "sigterm discovery/readiness process identity mismatch: "
                f"discovery_pid={discovery_pid}, marker_pid={marker_pid}, "
                f"discovery_pgid={discovery_pgid}, marker_pgid={pgid}"
            )
        if written_monotonic_ns > ready_monotonic_ns:
            pytest.fail(
                "sigterm monotonic timestamps are corrupt: discovery write follows "
                f"readiness; written={written_monotonic_ns}, ready={ready_monotonic_ns}"
            )
        assert marker_pid != child_pid
        assert pgid != os.getpgrp()
        try:
            marker_actual_pgid = os.getpgid(marker_pid)
        except ProcessLookupError as exc:
            pytest.fail(
                "sigterm runner PID vanished before group validation; "
                "harness の 60 秒 hang timeout が先に発火した可能性: "
                f"marker_pid={marker_pid}, recorded_pgid={pgid}, "
                f"harness_rc={process.poll()}; error={exc}"
            )
        except OSError as exc:
            pytest.fail(
                "sigterm runner process-group validation failed: "
                f"marker_pid={marker_pid}, recorded_pgid={pgid}; "
                f"error={type(exc).__name__}: {exc}"
            )
        try:
            child_actual_pgid = os.getpgid(child_pid)
        except ProcessLookupError as exc:
            pytest.fail(
                "sigterm descendant PID vanished before group validation; "
                "the descendant 120-second absolute cap may have fired: "
                f"child_pid={child_pid}, recorded_pgid={pgid}; error={exc}"
            )
        except OSError as exc:
            pytest.fail(
                "sigterm descendant process-group validation failed: "
                f"child_pid={child_pid}, recorded_pgid={pgid}; "
                f"error={type(exc).__name__}: {exc}"
            )
        assert marker_actual_pgid == pgid
        assert child_actual_pgid == pgid
        stage_trace_before_signal = read_stage_trace()
        assert stage_trace_before_signal == [
            {
                "schema": "izanagi-mutation-sigterm-stage/v1",
                "event": "stage-0-complete",
                "value": "0",
            },
            {
                "schema": "izanagi-mutation-sigterm-stage/v1",
                "event": "stage-3-entered",
                "value": "3",
            },
        ]

        rc = process.poll()
        if rc is not None:
            fail_early_exit(rc)
        sigterm_sent_ns = time.monotonic_ns()
        process.send_signal(signal.SIGTERM)
        record_property(
            "readiness_to_sigterm_s",
            (sigterm_sent_ns - ready_monotonic_ns) / 1_000_000_000,
        )
        record_property(
            "calls3_to_sigterm_s",
            (sigterm_sent_ns - written_monotonic_ns) / 1_000_000_000,
        )
        record_property(
            "spawn_to_readiness_s",
            (ready_monotonic_ns - spawned_monotonic_ns) / 1_000_000_000,
        )
        _stdout, stderr = communicate_or_fail("post-SIGTERM")
        assert process.returncode == 128 + signal.SIGTERM
        assert "active mutation restore attempted" in stderr
        assert (repo / "target.py").read_text(encoding="utf-8") == _git(
            repo, "show", "HEAD:target.py"
        )
        ledger = json.loads(out.read_text(encoding="utf-8"))
        assert ledger["mutations"] == []
        assert read_stage_trace() == stage_trace_before_signal
        assert _calls(calls) == ["0", "3"]

        cleanup_deadline = time.monotonic() + 10
        while _pid_is_alive(child_pid) and time.monotonic() < cleanup_deadline:
            time.sleep(0.02)
        if _pid_is_alive(child_pid):
            pytest.fail(
                "post-SIGTERM descendant cleanup 10-second deadline exceeded: "
                f"child_pid={child_pid}, pgid={pgid}"
            )
    finally:
        if cleanup_deadline is None:
            cleanup_deadline = time.monotonic() + 10
        if process.poll() is None:
            process.kill()
            try:
                process.wait(timeout=max(0.0, cleanup_deadline - time.monotonic()))
            except subprocess.TimeoutExpired:
                cleanup_warning(
                    "sigterm finally cleanup 10-second deadline exceeded while "
                    f"waiting for harness pid={process.pid}"
                )

        def reread_cleanup_record(
            path: Path, label: str
        ) -> dict[str, object] | None:
            try:
                content = path.read_text(encoding="utf-8")
            except FileNotFoundError:
                cleanup_warning(
                    f"sigterm cleanup {label} was not available: path={path}"
                )
                return None
            except OSError as exc:
                cleanup_warning(
                    f"sigterm cleanup {label} reread failed: path={path}; "
                    f"error={type(exc).__name__}: {exc}"
                )
                return None
            try:
                candidate = json.loads(content)
            except json.JSONDecodeError as exc:
                cleanup_warning(
                    f"sigterm cleanup {label} reread found corrupt JSON: "
                    f"path={path}; error={exc}"
                )
                return None
            if not isinstance(candidate, dict):
                cleanup_warning(
                    f"sigterm cleanup {label} reread found non-object JSON: path={path}"
                )
                return None
            return candidate

        discovery_reread = reread_cleanup_record(discovery, "discovery record")
        marker_reread = reread_cleanup_record(marker, "readiness marker")
        cleanup_records = (
            ("cached discovery record", discovery_payload, False),
            ("reread discovery record", discovery_reread, False),
            ("cached readiness marker", marker_payload, True),
            ("reread readiness marker", marker_reread, True),
        )
        cleanup_groups: dict[int, dict[int, set[str]]] = {}
        for label, payload, has_child in cleanup_records:
            if payload is None:
                continue
            candidate_pgid = payload.get("pgid")
            if (
                isinstance(candidate_pgid, bool)
                or not isinstance(candidate_pgid, int)
                or candidate_pgid <= 0
                or candidate_pgid == os.getpgrp()
            ):
                cleanup_warning(
                    f"sigterm cleanup ignored invalid pgid from {label}: "
                    f"pgid={candidate_pgid!r}"
                )
                continue
            members = cleanup_groups.setdefault(candidate_pgid, {})
            for field in (("pid", "runner"), ("child_pid", "descendant")):
                if field[0] == "child_pid" and not has_child:
                    continue
                candidate_pid = payload.get(field[0])
                if (
                    isinstance(candidate_pid, int)
                    and not isinstance(candidate_pid, bool)
                    and candidate_pid > 0
                ):
                    members.setdefault(candidate_pid, set()).add(
                        f"{label} {field[1]}"
                    )
                elif candidate_pid is not None:
                    cleanup_warning(
                        f"sigterm cleanup ignored invalid {field[0]} from {label}: "
                        f"pid={candidate_pid!r}"
                    )

        def confirmed_group_member(
            candidate_pgid: int,
            members: dict[int, set[str]],
            signal_name: str,
        ) -> int | None:
            observed_alive = False
            for candidate_pid, sources in sorted(members.items()):
                if not _pid_is_alive(candidate_pid):
                    continue
                observed_alive = True
                try:
                    actual_pgid = os.getpgid(candidate_pid)
                except ProcessLookupError:
                    cleanup_warning(
                        "sigterm cleanup ownership recheck lost a recorded PID; "
                        f"killpg({signal_name}) not authorized by pid={candidate_pid}, "
                        f"recorded_pgid={candidate_pgid}, sources={sorted(sources)!r}"
                    )
                    continue
                except OSError as exc:
                    cleanup_warning(
                        "sigterm cleanup ownership recheck failed; "
                        f"killpg({signal_name}) not authorized by pid={candidate_pid}, "
                        f"recorded_pgid={candidate_pgid}, sources={sorted(sources)!r}; "
                        f"error={type(exc).__name__}: {exc}"
                    )
                    continue
                if actual_pgid != candidate_pgid:
                    cleanup_warning(
                        "sigterm cleanup ownership mismatch; "
                        f"killpg({signal_name}) skipped for pid={candidate_pid}, "
                        f"recorded_pgid={candidate_pgid}, actual_pgid={actual_pgid}, "
                        f"sources={sorted(sources)!r}"
                    )
                    continue
                return candidate_pid
            if observed_alive:
                cleanup_warning(
                    "sigterm cleanup could not confirm any recorded PID in its "
                    f"recorded pgid={candidate_pgid}; killpg({signal_name}) skipped"
                )
            return None

        for cleanup_pgid, cleanup_members in sorted(cleanup_groups.items()):
            if not any(_pid_is_alive(pid) for pid in cleanup_members):
                continue
            member_pid = confirmed_group_member(
                cleanup_pgid, cleanup_members, "SIGTERM"
            )
            if member_pid is None:
                continue
            try:
                os.killpg(cleanup_pgid, signal.SIGTERM)
            except OSError as exc:
                cleanup_warning(
                    "sigterm cleanup killpg(SIGTERM) failed after ownership "
                    f"confirmation: pgid={cleanup_pgid}, member_pid={member_pid}; "
                    f"error={type(exc).__name__}: {exc}"
                )
            while (
                any(_pid_is_alive(pid) for pid in cleanup_members)
                and time.monotonic() < cleanup_deadline
            ):
                time.sleep(0.02)
            if not any(_pid_is_alive(pid) for pid in cleanup_members):
                continue
            cleanup_warning(
                "sigterm finally cleanup 10-second deadline exceeded for "
                f"pgid={cleanup_pgid}; escalating to SIGKILL"
            )
            member_pid = confirmed_group_member(
                cleanup_pgid, cleanup_members, "SIGKILL"
            )
            if member_pid is None:
                continue
            try:
                os.killpg(cleanup_pgid, signal.SIGKILL)
            except OSError as exc:
                cleanup_warning(
                    "sigterm cleanup killpg(SIGKILL) failed after ownership "
                    f"confirmation: pgid={cleanup_pgid}, member_pid={member_pid}; "
                    f"error={type(exc).__name__}: {exc}"
                )


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


def test_attempt_sidecar_is_started_before_popen_and_finished_after_failure(
    repo: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    attempt_path = tmp_path / "attempts.json"
    recorder = MH.AttemptRecorder(
        path=attempt_path,
        wrapper_attempt_ordinal=7,
        document={
            "schema": MH.ATTEMPT_SCHEMA,
            "repo_head": "a" * 40,
            "spec_sha256": "b" * 64,
            "runner_sha256": "c" * 64,
            "tool_sha256": "d" * 64,
            "expected_initial_requests": 3,
            "attempts": [],
        },
    )
    observed_state: list[str] = []

    def failing_popen(*args: object, **kwargs: object) -> None:
        sidecar = json.loads(attempt_path.read_text(encoding="utf-8"))
        observed_state.append(sidecar["attempts"][0]["state"])
        raise OSError("fixture popen failure")

    monkeypatch.setattr(MH.subprocess, "Popen", failing_popen)

    result = MH._run_tests(
        repo,
        [sys.executable, "-c", "pass"],
        timeout_s=1,
        runner_mode="dispatch",
        attempt_recorder=recorder,
        attempt_phase="mutation",
        mutation_id="M1",
    )

    assert observed_state == ["started"]
    assert result["rc"] is None
    sidecar = json.loads(attempt_path.read_text(encoding="utf-8"))
    assert sidecar["attempts"][0]["state"] == "finished"
    assert sidecar["attempts"][0]["wrapper_attempt_ordinal"] == 7
    assert sidecar["attempts"][0]["request"] is None


@pytest.mark.parametrize("runner_mode", ["local", "dispatch"])
@pytest.mark.parametrize("with_attempt_recorder", [False, True])
def test_dispatch_inventory_snapshot_precedes_runner_in_every_mode(
    repo: Path,
    monkeypatch: pytest.MonkeyPatch,
    runner_mode: str,
    with_attempt_recorder: bool,
) -> None:
    events: list[str] = []

    def inventory(root: Path) -> set[Path]:
        assert root == repo
        events.append("inventory")
        return set()

    def failing_popen(*args: object, **kwargs: object) -> None:
        events.append("popen")
        raise OSError("fixture popen failure")

    recorder = None
    if with_attempt_recorder:
        recorder = MH.AttemptRecorder(
            path=repo.parent / f"attempts-{runner_mode}.json",
            wrapper_attempt_ordinal=1,
            document={
                "schema": MH.ATTEMPT_SCHEMA,
                "repo_head": "a" * 40,
                "spec_sha256": "b" * 64,
                "runner_sha256": "c" * 64,
                "tool_sha256": "d" * 64,
                "expected_initial_requests": 1,
                "attempts": [],
            },
        )
    monkeypatch.setattr(MH, "_dispatch_submission_inventory", inventory)
    monkeypatch.setattr(MH.subprocess, "Popen", failing_popen)

    result = MH._run_tests(
        repo,
        [sys.executable, "-c", "pass"],
        timeout_s=1,
        runner_mode=runner_mode,
        attempt_recorder=recorder,
        attempt_phase="baseline" if recorder is not None else None,
    )

    assert result["rc"] is None
    assert events == ["inventory", "popen"]


def test_timeout_request_recovery_uses_partial_receipt_as_correspondence_source(
    repo: Path,
) -> None:
    before = MH._dispatch_submission_inventory(repo)
    submission = repo / "output" / "pegasus-dispatch" / "timeout-request"
    submission.mkdir(parents=True)
    receipt = submission / "receipt.json"
    receipt.write_text(
        json.dumps(
            {
                "submission_dir": str(submission),
                "request_id": "987.server",
                "request": {"job_name": "izdw-timeout"},
            }
        ),
        encoding="utf-8",
    )

    request = MH._recover_dispatch_request(repo, before)

    assert request == {
        "request_id": "987.server",
        "submission_dir": str(submission),
        "receipt_path": str(receipt),
        "job_stdout_path": None,
        "outcome_rc": None,
    }


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


@pytest.fixture
def timeout_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    for name in (
        MH._DISPATCH_QUEUE_WAIT_TIMEOUT_OVERRIDE_ENV,
        MH._DISPATCH_OVERALL_GRACE_OVERRIDE_ENV,
        "IZANAGI_DISPATCH_WALLTIME_OVERRIDE",
    ):
        monkeypatch.delenv(name, raising=False)


@pytest.mark.parametrize(
    "timeout,overrides,collection,expected",
    [
        (1, {}, False, 5130),
        (10000, {}, False, 10000),
        (1, {"QUEUE_WAIT_TIMEOUT": "3600", "OVERALL_GRACE": "600"}, False, 8130),
        (1, {"QUEUE_WAIT_TIMEOUT": "0"}, False, 4230),
        (1, {"OVERALL_GRACE": "0"}, False, 4830),
        (1, {"QUEUE_WAIT_TIMEOUT": "0", "OVERALL_GRACE": "0"}, False, 3930),
        (1, {"WALLTIME": "02:00:00"}, False, 8730),
        (1, {"WALLTIME": "00:02:00"}, False, 1650),
        (1, {"WALLTIME": "00:02:00"}, True, 5130),
        (1, {"WALLTIME": "02:00:00"}, True, 5130),
        (1, {"WALLTIME": "invalid"}, False, 5130),
        (1, {"WALLTIME": "00:00:00"}, False, 5130),
        (1, {"QUEUE_WAIT_TIMEOUT": "invalid"}, False, 5130),
    ],
)
def test_t2484_timeout_budget_arithmetic(
    timeout_environment, monkeypatch, timeout, overrides, collection, expected,
) -> None:
    for name, value in overrides.items():
        monkeypatch.setenv(f"IZANAGI_DISPATCH_{name}_OVERRIDE", value)
    spec = MH.MutationSpec((), 1, timeout, 0.25)
    assert MH._effective_timeout(spec, "dispatch", collection=collection) == expected


def test_t2484_timeout_diagnostic_is_nonrejecting(
    timeout_environment, capsys,
) -> None:
    spec = MH.MutationSpec((), 1, 1, 0.25)
    assert MH._effective_timeout(spec, "dispatch", hang_risk=True) == 5130
    diagnostic = capsys.readouterr().err
    for text in ("spec=1", "P=180", "Q=900", "W=3600", "G=300", "A=60", "C=90",
                 "effective=5130", "厳密上限ではない", "内側 walltime"):
        assert text in diagnostic


@pytest.mark.parametrize(
    "phase,mode,hang,timeout,overrides,expected",
    [
        ("collection", "dispatch", False, 1, {}, 5130),
        ("baseline", "dispatch", False, 1, {}, 5130),
        ("mutation", "dispatch", False, 1, {}, 5130),
        ("mutation", "dispatch", True, 1, {}, 5130),
        ("collection", "dispatch", False, 10000, {}, 10000),
        ("baseline", "dispatch", False, 10000, {}, 10000),
        ("mutation", "dispatch", True, 10000, {}, 10000),
        ("collection", "dispatch", False, 1, {"WALLTIME": "00:02:00"}, 5130),
        ("baseline", "dispatch", False, 1, {"WALLTIME": "02:00:00"}, 8730),
        ("mutation", "dispatch", True, 1, {"WALLTIME": "02:00:00"}, 8730),
        ("collection", "dispatch", False, 2399,
         {"QUEUE_WAIT_TIMEOUT": "1800", "OVERALL_GRACE": "600"}, None),
        ("collection", "dispatch", False, 2400,
         {"QUEUE_WAIT_TIMEOUT": "1800", "OVERALL_GRACE": "600"}, 6330),
        ("collection", "local", False, 10, {"WALLTIME": "invalid"}, 10),
        ("baseline", "local", False, 10, {"QUEUE_WAIT_TIMEOUT": "invalid"}, 10),
        ("mutation", "local", False, 10, {}, 10),
        ("mutation", "local", True, 10, {"QUEUE_WAIT_TIMEOUT": "invalid"}, 1),
        ("baseline", "dispatch", False, 1, {"WALLTIME": "invalid"}, 5130),
    ],
)
def test_t2484_callers_reach_communicate_with_effective_timeout(
    repo, timeout_environment, monkeypatch, phase, mode, hang, timeout, overrides, expected,
) -> None:
    # Only the final process sink is replaced. Real git, guards, injection,
    # collection gate, timeout helper and _run_tests all remain in the path.
    for name, value in overrides.items():
        monkeypatch.setenv(f"IZANAGI_DISPATCH_{name}_OVERRIDE", value)
    spec_path, _, _, _ = _paths(repo)
    _single_spec(spec_path)
    loaded, spec_sha = MH._load_spec(spec_path)
    mutation = MH.dataclasses.replace(loaded.mutations[0], hang_risk=hang)
    spec = MH.dataclasses.replace(loaded, mutations=(mutation,), timeout_seconds=timeout)
    head = MH._repo_head(repo)
    originals = MH._read_head_sources(repo, head, spec)
    registration = MH._validate_registrations(repo, spec, originals)
    seen = []
    commands = []

    class SinkReached(Exception):
        pass

    class ProcessSink:
        def communicate(self, *, timeout):
            seen.append(timeout)
            raise SinkReached

        def poll(self):
            return 0

    real_popen = MH.subprocess.Popen

    def observe_popen(command, *args, **kwargs):
        if "--timeout-sink" in command:
            commands.append(command)
            return ProcessSink()
        return real_popen(command, *args, **kwargs)

    monkeypatch.setattr(MH.subprocess, "Popen", observe_popen)
    command = [sys.executable, str(repo / "tools/run_tests.py"), "--timeout-sink", "-rf"]
    common = dict(spec_sha256=spec_sha, runner_sha256="runner", tool_sha256="tool")
    with pytest.raises(SinkReached if expected is not None else MH.HarnessError) as caught:
        if phase == "collection":
            MH._collect_expected_nodes(repo, spec, command, mode, head=head, **common)
        elif phase == "baseline":
            MH._baseline(repo, spec, command, mode, head=head,
                         registration_sha256="registration", collection_sha256="collection",
                         **common)
        else:
            MH._apply_mutation(repo, head, originals, mutation, spec, command, mode,
                               registration[mutation.id], collection_sha256="collection",
                               **common)
    assert seen == ([] if expected is None else [expected])
    if expected is None:
        assert "外側 timeout" in str(caught.value)
        assert commands == []
    elif phase == "collection" and mode == "dispatch":
        assert commands[0][1] == str(repo / "tools/pegasus/dispatch_compute.py")
        assert "--walltime" not in commands[0]
    assert (repo / "target.py").read_text(encoding="utf-8") == originals["target.py"]


@pytest.mark.parametrize("job_may_remain", [False, True])
def test_t2484_inband_rc16_preserves_receipt_hold_contract(repo, job_may_remain) -> None:
    result = {"rc": 16, "timed_out": False, "job_may_remain": job_may_remain}
    stop = MH._dispatch_orphan_stop(
        repo, runner_mode="dispatch", phase="mutation", mutation_id="M1",
        source_state="mutation-left-in-place", dirty_paths=("target.py",), result=result,
    )
    hold = MH._dispatch_orphan_hold_path(repo)
    if job_may_remain:
        assert isinstance(stop, MH.OrphanHoldStop)
        assert json.loads(hold.read_text())["reason"] == "dispatch-receipt-job-may-remain"
    else:
        assert stop is None
        assert not hold.exists()


def _commit_case(repo: Path) -> tuple[str, dict[str, str], MH.MutationSpec, MH.Mutation, dict[str, object]]:
    _git(repo, "checkout", "--detach", "-q")
    spec_path, _, _, _ = _paths(repo)
    _single_spec(spec_path)
    spec, _ = MH._load_spec(spec_path)
    head = MH._repo_head(repo)
    originals = MH._read_head_sources(repo, head, spec)
    mutation = spec.mutations[0]
    registration = MH._validate_registrations(repo, spec, originals)[mutation.id]
    return head, originals, spec, mutation, registration


def _apply_case(
    repo: Path, case: tuple, *, inject: str = "commit", runner_mode: str = "local"
) -> dict[str, object]:
    head, originals, spec, mutation, registration = case
    return MH._apply_mutation(
        repo, head, originals, mutation, spec,
        [sys.executable, "-m", "pytest", "tests/test_gate.py", "-rf"],
        runner_mode, registration, spec_sha256="spec", runner_sha256="runner",
        tool_sha256="tool", collection_sha256="collection", inject=inject,
    )


def _fake_result(*, rc: int = 0, output: str = "", timed_out: bool = False) -> dict[str, object]:
    return {
        "rc": rc, "timed_out": timed_out, "job_stdout": output,
        "duration_s": 0.01, "artifact_error": None,
    }


def _assert_restored_commit(repo: Path, head: str, originals: dict[str, str]) -> None:
    assert MH._repo_head(repo) == head
    assert subprocess.run(
        ["git", "-C", str(repo), "symbolic-ref", "-q", "HEAD"],
        capture_output=True,
    ).returncode == 1
    assert (repo / "target.py").read_bytes() == _git(repo, "show", f"{head}:target.py").encode()
    assert (repo / "target.py").read_text(encoding="utf-8") == originals["target.py"]
    MH._assert_clean_tracked(repo)


def test_commit_injection_exposes_head_blob_and_value_layer(
    repo: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    case = _commit_case(repo)
    head, originals, *_ = case
    equivalent = MH.dataclasses.replace(
        case[3],
        replacements=(MH.Replacement("target.py", 'TOKEN = "x"', 'TOKEN = "x"  # equivalent'),),
    )
    equivalent_spec = MH.dataclasses.replace(case[2], mutations=(equivalent,))
    equivalent_registration = MH._validate_registrations(repo, equivalent_spec, originals)[equivalent.id]
    equivalent_case = (head, originals, equivalent_spec, equivalent, equivalent_registration)
    seen: list[str] = []

    def runner(root: Path, *_args: object, **_kwargs: object) -> dict[str, object]:
        head_blob = _git(root, "show", "HEAD:target.py").encode()
        disk = (root / "target.py").read_bytes()
        value = disk.splitlines()[0]
        seen.append(value.decode())
        if disk != head_blob:
            return _fake_result(rc=1, output="FAILED tests/test_gate.py::test_gate[one]\n")
        if value == b"VALUE = 1":
            return _fake_result(rc=1, output="FAILED tests/test_gate.py::test_gate[one]\n")
        return _fake_result()

    monkeypatch.setattr(MH, "_run_tests", runner)
    assert _apply_case(repo, equivalent_case, inject="file-swap")["status"] == "KILLED"
    assert _apply_case(repo, equivalent_case)["status"] == "SURVIVED"
    assert _apply_case(repo, case)["status"] == "KILLED"
    assert seen == ["VALUE = 0", "VALUE = 0", "VALUE = 1"]
    _assert_restored_commit(repo, head, originals)


@pytest.mark.parametrize("plan_only", [True, False])
def test_commit_attached_head_rejected_before_runner(
    repo: Path, monkeypatch: pytest.MonkeyPatch, plan_only: bool,
) -> None:
    spec, out, calls, mode = _paths(repo)
    _single_spec(spec)
    branch = _git(repo, "symbolic-ref", "HEAD").strip()
    before = _git(repo, "rev-parse", branch).strip()
    monkeypatch.setattr(MH, "_run_tests", lambda *_a, **_k: pytest.fail("runner reached"))
    argv = _argv(repo, spec, out, calls, mode)
    argv[argv.index("--"):argv.index("--")] = ["--inject", "commit"] + (["--plan-only"] if plan_only else [])
    with pytest.raises(MH.HarnessError, match="detached HEAD"):
        MH.main(argv)
    assert _git(repo, "rev-parse", branch).strip() == before


@pytest.mark.parametrize("defect", ["extra-path", "wrong-parent", "wrong-blob"])
def test_commit_post_commit_boundary_rejects_single_defect(
    repo: Path, monkeypatch: pytest.MonkeyPatch, defect: str,
) -> None:
    case = _commit_case(repo)
    head, originals, *_ = case
    real_commit = MH._commit_mutation

    def broken_commit(root: Path, mutation_id: str, touched: tuple[str, ...]) -> None:
        if defect == "extra-path":
            (root / "tracked.txt").write_text("extra\n", encoding="utf-8")
            _git(
                root, "-c", "user.name=izanagi-mutation-harness",
                "-c", f"user.email={MH.HARNESS_EMAIL}",
                "-c", "commit.gpgsign=false", "commit", "--quiet", "--only",
                "-m", "extra path", "--", *touched, "tracked.txt",
            )
        elif defect == "wrong-parent":
            _git(root, "commit", "--quiet", "--allow-empty", "-m", "intermediate")
            real_commit(root, mutation_id, touched)
        else:
            (root / touched[0]).write_text("VALUE = 8\nTOKEN = \"x\"\nTOKEN_COPY = \"x\"\n", encoding="utf-8")
            real_commit(root, mutation_id, touched)

    monkeypatch.setattr(MH, "_commit_mutation", broken_commit)
    monkeypatch.setattr(MH, "_run_tests", lambda *_a, **_k: pytest.fail("runner reached"))
    expected = {
        "extra-path": "changed paths", "wrong-parent": "親", "wrong-blob": "注入 bytes",
    }[defect]
    with pytest.raises(MH.HarnessError) as caught:
        _apply_case(repo, case)
    assert expected in str(caught.value) or expected in str(caught.value.__context__)
    if defect == "wrong-blob":
        _assert_restored_commit(repo, head, originals)


@pytest.mark.parametrize("outcome", ["normal", "nonzero", "timeout"])
def test_commit_restores_after_runner_outcomes(
    repo: Path, monkeypatch: pytest.MonkeyPatch, outcome: str,
) -> None:
    case = _commit_case(repo)
    head, originals, *_ = case
    branch = _git(repo, "for-each-ref", "--format=%(refname):%(objectname)", "refs/heads").strip()
    result = {
        "normal": _fake_result(),
        "nonzero": _fake_result(rc=1, output="FAILED tests/test_gate.py::test_gate[one]\n"),
        "timeout": _fake_result(rc=None, timed_out=True),
    }[outcome]
    monkeypatch.setattr(MH, "_run_tests", lambda *_a, **_k: result)
    assert _apply_case(repo, case)["status"] == {
        "normal": "SURVIVED", "nonzero": "KILLED", "timeout": "TIMEOUT",
    }[outcome]
    _assert_restored_commit(repo, head, originals)
    assert _git(repo, "for-each-ref", "--format=%(refname):%(objectname)", "refs/heads").strip() == branch


def test_commit_restore_refuses_attached_head_without_moving_branch(
    repo: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    case = _commit_case(repo)
    branch = _git(repo, "for-each-ref", "--format=%(refname)", "refs/heads").strip()
    branch_head = _git(repo, "rev-parse", branch).strip()

    def attach(root: Path, *_a: object, **_k: object) -> dict[str, object]:
        _git(root, "symbolic-ref", "HEAD", branch)
        return _fake_result()

    monkeypatch.setattr(MH, "_run_tests", attach)
    with pytest.raises(MH.HarnessError, match="detached HEAD"):
        _apply_case(repo, case)
    assert _git(repo, "rev-parse", branch).strip() == branch_head


def test_commit_signal_during_runner_restores(
    repo: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    case = _commit_case(repo)
    head, originals, *_ = case

    def interrupted(*_a: object, **_k: object) -> dict[str, object]:
        os.kill(os.getpid(), signal.SIGTERM)
        pytest.fail("signal handler did not abort")

    monkeypatch.setattr(MH, "_run_tests", interrupted)
    handlers = MH._install_signal_handlers()
    try:
        with pytest.raises(MH.SignalAbort):
            _apply_case(repo, case)
    finally:
        MH._restore_signal_handlers(handlers)
    _assert_restored_commit(repo, head, originals)


def _inject_argv(args: list[str], inject: str, *, plan_only: bool = False) -> list[str]:
    result = list(args)
    result[result.index("--"):result.index("--")] = ["--inject", inject] + (
        ["--plan-only"] if plan_only else []
    )
    return result


def test_commit_orphan_hold_preserves_m_then_manual_resume(
    repo: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    _git(repo, "checkout", "--detach", "-q")
    spec, out, calls, mode = _paths(repo)
    _single_spec(spec)
    (repo / ".git" / "info" / "exclude").write_text("/output/\n", encoding="utf-8")
    head = MH._repo_head(repo)
    branch_before = _git(repo, "for-each-ref", "--format=%(refname):%(objectname)", "refs/heads")
    real_run = MH._run_tests
    observed_m: list[str] = []

    def hold_runner(root: Path, command: list[str], **kwargs: object) -> dict[str, object]:
        if (root / "target.py").read_text(encoding="utf-8").startswith("VALUE = 1\n"):
            mutation_head = MH._repo_head(root)
            observed_m.append(mutation_head)
            assert (root / "target.py").read_bytes() == _git(root, "show", "HEAD:target.py").encode()
            hold, error = MH._latch_dispatch_orphan_hold(
                root, phase="mutation", mutation_id="M1", result={},
                reason="fixture-orphan", source_state=MH.COMMIT_SOURCE_STATE,
            )
            assert error is None and hold.exists()
            return _fake_result()
        return real_run(root, command, **kwargs)

    monkeypatch.setattr(MH, "_run_tests", hold_runner)
    argv = _inject_argv(_argv(repo, spec, out, calls, mode), "commit")
    assert MH.main(argv) == 2
    assert len(observed_m) == 1
    assert MH._repo_head(repo) == observed_m[0]
    MH._assert_clean_tracked(repo)
    assert _git(repo, "for-each-ref", "--format=%(refname):%(objectname)", "refs/heads") == branch_before
    sidecar = MH._orphan_stop_path(out)
    reason = json.loads(sidecar.read_text(encoding="utf-8"))["reason"]
    assert reason["source_state"] == MH.COMMIT_SOURCE_STATE
    assert "git reset --soft H" in reason["recovery"]
    for resume in (False, True):
        blocked = _inject_argv(_argv(repo, spec, out, calls, mode, resume=resume), "commit")
        with pytest.raises(MH.HarnessError):
            MH.main(blocked)
    _git(repo, "reset", "--soft", head)
    _git(repo, "restore", f"--source={head}", "--staged", "--worktree", "--", "target.py")
    _assert_restored_commit(repo, head, {"target.py": _git(repo, "show", f"{head}:target.py")})
    MH._dispatch_orphan_hold_path(repo).unlink()
    sidecar.unlink()
    monkeypatch.setattr(MH, "_run_tests", real_run)
    assert MH.main(_inject_argv(_argv(repo, spec, out, calls, mode, resume=True), "commit")) == 0
    _assert_restored_commit(repo, head, {"target.py": _git(repo, "show", f"{head}:target.py")})


@pytest.mark.parametrize("first,second", [("file-swap", "commit"), ("commit", "file-swap")])
def test_resume_rejects_injection_policy_mismatch(
    repo: Path, first: str, second: str,
) -> None:
    _git(repo, "checkout", "--detach", "-q")
    spec, out, calls, mode = _paths(repo)
    _single_spec(spec)
    assert MH.main(_inject_argv(_argv(repo, spec, out, calls, mode), first)) == 0
    assert json.loads(out.read_text(encoding="utf-8"))["schema"] == MH.LEDGER_SCHEMA
    before = _calls(calls)
    with pytest.raises(MH.HarnessError, match="source_policy"):
        MH.main(_inject_argv(_argv(repo, spec, out, calls, mode, resume=True), second))
    assert _calls(calls) == before


@pytest.mark.parametrize("inject", ["file-swap", "commit"])
@pytest.mark.parametrize("resume", [False, True])
@pytest.mark.parametrize("plan_only", [False, True])
def test_residual_harness_commit_rejected_before_runner(
    repo: Path, monkeypatch: pytest.MonkeyPatch, inject: str, resume: bool,
    plan_only: bool,
) -> None:
    _git(repo, "checkout", "--detach", "-q")
    spec, out, calls, mode = _paths(repo)
    _single_spec(spec)
    _git(
        repo, "-c", "user.name=izanagi-mutation-harness",
        "-c", f"user.email={MH.HARNESS_EMAIL}",
        "-c", "commit.gpgsign=false", "commit", "--quiet", "--allow-empty", "-m", "residual",
    )
    monkeypatch.setattr(MH, "_run_tests", lambda *_a, **_k: pytest.fail("runner reached"))
    with pytest.raises(MH.HarnessError, match="残留 commit"):
        MH.main(_inject_argv(_argv(repo, spec, out, calls, mode, resume=resume), inject, plan_only=plan_only))
    assert not calls.exists()
