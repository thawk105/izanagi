"""使い捨て mutation worktree の fail-closed 契約を real Git fixture で検査する。

全テストが主張するのは共有木の観測点間で git status / git submodule status の
stdout bytes が不変であることだけであり、物理ノード死・client eviction 後を含む
物理永続性は主張しない。
"""

from __future__ import annotations

import hashlib
import importlib.util
import json
import os
import shlex
import shutil
import signal
import subprocess
import sys
import time
from pathlib import Path
from types import SimpleNamespace

import pytest


_REPO = Path(__file__).resolve().parents[2]
_TOOL = _REPO / "tools" / "mutation_worktree.py"
_HARNESS = _REPO / "tools" / "mutation_harness.py"
_SPEC = importlib.util.spec_from_file_location("mutation_worktree_under_test", _TOOL)
assert _SPEC is not None and _SPEC.loader is not None
MW = importlib.util.module_from_spec(_SPEC)
sys.modules[_SPEC.name] = MW
_SPEC.loader.exec_module(MW)

_LIMIT = (
    "共有木の観測点間で git status / git submodule status の stdout bytes が"
    "不変であることだけを主張し、物理永続性は主張しない。"
)


def _limited(function):
    function.__doc__ = _LIMIT
    return function


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


def _configure(repo: Path) -> None:
    _git(repo, "config", "user.email", "mutation-worktree@example.invalid")
    _git(repo, "config", "user.name", "Mutation Worktree Test")


def _plain_repo(path: Path) -> Path:
    path.mkdir()
    _git(path, "init", "-q")
    _configure(path)
    (path / "tracked.txt").write_text("base\n", encoding="utf-8")
    _git(path, "add", "tracked.txt")
    _git(path, "commit", "-qm", "fixture")
    return path


def _fake_harness_source() -> str:
    return """#!/usr/bin/env python3
import hashlib
import json
import os
import signal
import subprocess
import sys
import time
from pathlib import Path

args = sys.argv[1:]
out = Path(args[args.index('--out') + 1])
repo = Path(args[args.index('--repo') + 1])
spec = Path(args[args.index('--spec') + 1])
if os.environ.get('IZANAGI_CAPTURE') == '1':
    capture = Path(str(out) + '.capture.json')
    capture.write_text(json.dumps({
        'argv': args,
        'cwd': os.getcwd(),
        'env': dict(os.environ),
    }, sort_keys=True), encoding='utf-8')
signal_record = os.environ.get('IZANAGI_SIGNAL_RECORD')
if signal_record:
    def stop(signum, _frame):
        Path(signal_record).write_text(str(signum), encoding='utf-8')
        raise SystemExit(128 + signum)
    signal.signal(signal.SIGINT, stop)
    signal.signal(signal.SIGTERM, stop)
ready = os.environ.get('IZANAGI_READY')
if ready:
    Path(ready).write_text('ready', encoding='utf-8')
    release = Path(os.environ['IZANAGI_RELEASE'])
    while not release.exists():
        time.sleep(0.02)
for raw_path in os.environ.get('IZANAGI_DRIFT_PATHS', '').split(os.pathsep):
    if raw_path:
        Path(raw_path).write_text('drifted\\n', encoding='utf-8')
mode = os.environ.get('IZANAGI_LEDGER_MODE')
if mode:
    spec_document = json.loads(spec.read_text(encoding='utf-8'))
    ids = [mutation['id'] for mutation in spec_document['mutations']]
    records = []
    if mode in {'terminal', 'boolean-recorded'}:
        records = [
            {'id': mutation_id, 'status': 'KILLED', 'matches_expectation': True}
            for mutation_id in ids
        ]
    count = len(ids)
    recorded = len(records)
    summary = {
        'registered': count,
        'recorded': recorded,
        'completed': recorded,
        'matching': recorded,
        'KILLED': recorded,
        'SURVIVED': 0,
        'MISMATCH': 0,
        'TIMEOUT': 0,
        'PARSE_ERROR': 0,
    }
    if mode == 'boolean-recorded':
        summary['recorded'] = True
    out.write_text(json.dumps({
        'schema': 'izanagi-dev-wave-mutation/v4',
        'repo_head': subprocess.run(
            ['git', '-C', str(repo), 'rev-parse', 'HEAD'], check=True,
            text=True, stdout=subprocess.PIPE,
        ).stdout.strip(),
        'spec_sha256': hashlib.sha256(spec.read_bytes()).hexdigest(),
        'baseline': {'status': 'PASSED', 'rc': 0, 'failed_nodes': []},
        'summary': summary,
        'mutations': records,
    }), encoding='utf-8')
if os.environ.get('IZANAGI_DISPATCH_EVIDENCE') == '1':
    dispatch = repo / 'output' / 'pegasus-dispatch'
    dispatch.mkdir(parents=True, exist_ok=False)
    (dispatch / 'receipt.json').write_text('evidence', encoding='utf-8')
print('fake-harness-stdout', flush=True)
print('fake-harness-stderr', file=sys.stderr, flush=True)
raise SystemExit(int(os.environ.get('IZANAGI_FAKE_HARNESS_RC', '0')))
"""


def _fake_dispatch_source() -> str:
    return """#!/usr/bin/env python3
import json
import os
import sys
from pathlib import Path

script = Path(__file__).resolve()
repo = next(parent for parent in script.parents if (parent / 'target.py').is_file())
dispatch = repo / 'output' / 'pegasus-dispatch'
request_number = str(os.getpid())
submission = dispatch / ('submission-' + request_number)
submission.mkdir(parents=True, exist_ok=False)
job_name = 'izdw-fake'
if '--collect-only' in sys.argv:
    output = 'tests/test_gate.py::test_gate\\n'
    rc = 0
elif 'FLAG = True' in (repo / 'target.py').read_text(encoding='utf-8'):
    output = 'FAILED tests/test_gate.py::test_gate - AssertionError: mutation\\n1 failed\\n'
    rc = 1
else:
    output = '1 passed\\n'
    rc = 0
stdout = submission / (job_name + '.o' + request_number)
stdout.write_text(output, encoding='utf-8')
receipt = submission / 'receipt.json'
receipt.write_text(json.dumps({
    'submission_dir': str(submission),
    'outcome': {'rc': rc},
    'request': {'job_name': job_name},
    'request_id': request_number + '.local',
    'scheduler_logs': {'stdout': {'path': str(stdout)}},
}), encoding='utf-8')
print('[Pegasus dispatch] receipt を ' + str(receipt) + ' へ保存しました (child rc=' + str(rc) + ')')
raise SystemExit(rc)
"""


def _make_repository(
    tmp_path: Path, *, harness_source: str, fake_dispatch: bool = False
) -> SimpleNamespace:
    submodule = tmp_path / "ccbench-origin"
    submodule.mkdir()
    _git(submodule, "init", "-q")
    _configure(submodule)
    (submodule / "CMakeLists.txt").write_text("cmake_minimum_required(VERSION 3.10)\n")
    _git(submodule, "add", "CMakeLists.txt")
    _git(submodule, "commit", "-qm", "ccbench")

    main = tmp_path / "main"
    main.mkdir()
    _git(main, "init", "-q")
    _configure(main)
    (main / "tools").mkdir()
    harness = main / "tools" / "mutation_harness.py"
    harness.write_text(harness_source, encoding="utf-8")
    harness.chmod(0o755)
    (main / "target.py").write_text("FLAG = False\n", encoding="utf-8")
    tests = main / "tests"
    tests.mkdir()
    (tests / "test_gate.py").write_text(
        "from pathlib import Path\n\n"
        "def test_gate():\n"
        "    target = Path(__file__).parents[1] / 'target.py'\n"
        "    assert 'FLAG = True' not in target.read_text(encoding='utf-8')\n",
        encoding="utf-8",
    )
    (main / ".gitignore").write_text("output/\n", encoding="utf-8")
    if fake_dispatch:
        runner = main / "tools" / "run_tests.py"
        runner.write_text(_fake_dispatch_source(), encoding="utf-8")
        runner.chmod(0o755)
        pegasus = main / "tools" / "pegasus"
        pegasus.mkdir()
        dispatcher = pegasus / "dispatch_compute.py"
        dispatcher.write_text(_fake_dispatch_source(), encoding="utf-8")
        dispatcher.chmod(0o755)
    _git(main, "add", ".gitignore", "tools", "target.py", "tests/test_gate.py")
    _git(
        main,
        "-c",
        "protocol.file.allow=always",
        "submodule",
        "add",
        "-q",
        str(submodule),
        "external/ccbench",
    )
    _git(main, "commit", "-qm", "fixture")

    source = tmp_path / "source"
    _git(main, "worktree", "add", "-q", "--detach", str(source), "HEAD")
    scratch = tmp_path / "scratch"
    scratch.mkdir()
    artifacts = tmp_path / "artifacts"
    artifacts.mkdir()
    spec = artifacts / "spec.json"
    _write_spec(spec)
    return SimpleNamespace(
        main=main,
        source=source,
        scratch=scratch,
        artifacts=artifacts,
        spec=spec,
        out=artifacts / "ledger.json",
        commit=_git(source, "rev-parse", "HEAD").strip(),
    )


def _write_spec(path: Path) -> None:
    path.write_text(
        json.dumps(
            {
                "schema": "izanagi-dev-wave-mutation-spec/v1",
                "estimated_run_seconds": 0.01,
                "timeout_seconds": 20,
                "hang_timeout_seconds": 2,
                "mutations": [
                    {
                        "id": "MW-E2E",
                        "category": "negative",
                        "replacements": [
                            {"file": "target.py", "old": "FLAG = False", "new": "FLAG = True"}
                        ],
                        "expected_nodes": ["tests/test_gate.py::test_gate"],
                        "expected_status": "KILLED",
                        "hang_risk": False,
                    }
                ],
            },
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )


def _wrapper_argv(
    fixture: SimpleNamespace,
    *,
    runner_mode: str = "local",
    plan_only: bool = False,
    resume: bool = False,
    out: Path | None = None,
) -> list[str]:
    args = [
        "--source-repo",
        str(fixture.source),
        "--scratch-root",
        str(fixture.scratch),
        "--spec",
        str(fixture.spec),
        "--expected-spec-sha256",
        hashlib.sha256(fixture.spec.read_bytes()).hexdigest(),
        "--out",
        str(fixture.out if out is None else out),
        "--runner-mode",
        runner_mode,
    ]
    if resume:
        args.append("--resume")
    if plan_only:
        args.append("--plan-only")
    else:
        args.append("--detached")
    runner = (
        [sys.executable, "tools/run_tests.py", "tests/test_gate.py", "-rf"]
        if runner_mode == "dispatch"
        else [sys.executable, "-m", "pytest", "tests/test_gate.py", "-q", "-rf"]
    )
    return [*args, "--", *runner]


def _fake_preflight(tmp_path: Path) -> tuple[SimpleNamespace, MW.AdminBinding, Path]:
    common = tmp_path / "common"
    worktrees = common / "worktrees"
    own = worktrees / "own"
    foreign = worktrees / "foreign"
    own.mkdir(parents=True)
    foreign.mkdir()
    (foreign / "sentinel").write_text("foreign\n", encoding="utf-8")
    container = tmp_path / "container"
    checkout = container / "repo"
    checkout.mkdir(parents=True)
    dotgit = checkout / ".git"
    dotgit.write_text("gitdir: fixture\n", encoding="utf-8")
    backpointer = os.fsencode(dotgit) + b"\n"
    (own / "gitdir").write_bytes(backpointer)
    preflight = SimpleNamespace(
        container=container,
        checkout=checkout,
        evidence=tmp_path / "ledger.json.dispatch-evidence",
    )
    binding = MW.AdminBinding(common, own, dotgit, backpointer)
    return preflight, binding, foreign


@_limited
def test_source_must_be_the_exact_worktree_root_between_observation_points(
    tmp_path: Path,
) -> None:
    repo = _plain_repo(tmp_path / "repo")
    nested = repo / "nested"
    nested.mkdir()
    with pytest.raises(MW.MutationWorktreeError, match="root そのもの"):
        MW._resolve_source_and_commit(nested, None)


@_limited
def test_scratch_inside_any_registered_worktree_is_rejected_between_observation_points(
    tmp_path: Path,
) -> None:
    repo = _plain_repo(tmp_path / "repo")
    scratch = repo / "scratch"
    scratch.mkdir()
    with pytest.raises(MW.MutationWorktreeError, match="registered worktree の外"):
        MW._validate_scratch(scratch, (repo.resolve(),))


@_limited
def test_scratch_symlink_is_rejected_between_observation_points(tmp_path: Path) -> None:
    target = tmp_path / "target"
    target.mkdir()
    link = tmp_path / "scratch"
    link.symlink_to(target, target_is_directory=True)
    with pytest.raises(MW.MutationWorktreeError, match="symlink"):
        MW._validate_scratch(link, ())


@_limited
def test_existing_container_is_preserved_and_never_claimed_between_observation_points(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    fixture = _make_repository(tmp_path, harness_source=_fake_harness_source())
    container = fixture.scratch / MW.CONTAINER_NAME
    container.mkdir()
    sentinel = container / "sentinel"
    sentinel.write_text("owned elsewhere\n", encoding="utf-8")
    monkeypatch.setenv("IZANAGI_FAKE_HARNESS_RC", "0")
    assert MW.main(_wrapper_argv(fixture, plan_only=True)) == 125
    assert sentinel.read_text(encoding="utf-8") == "owned elsewhere\n"


@_limited
def test_same_out_from_different_scratch_is_rejected_between_observation_points(
    tmp_path: Path,
) -> None:
    fixture = _make_repository(tmp_path, harness_source=_fake_harness_source())
    scratch_b = tmp_path / "scratch-b"
    scratch_b.mkdir()
    second_fixture = SimpleNamespace(**vars(fixture))
    second_fixture.scratch = scratch_b
    ready = tmp_path / "first-ready"
    release = tmp_path / "first-release"
    environment = os.environ.copy()
    environment.update(
        {
            "IZANAGI_READY": str(ready),
            "IZANAGI_RELEASE": str(release),
            "IZANAGI_FAKE_HARNESS_RC": "0",
        }
    )
    first = subprocess.Popen(
        [sys.executable, str(_TOOL), *_wrapper_argv(fixture, plan_only=True)],
        env=environment,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    try:
        deadline = time.monotonic() + 10
        while not ready.exists() and time.monotonic() < deadline:
            time.sleep(0.02)
        assert ready.is_file()
        second = subprocess.run(
            [
                sys.executable,
                str(_TOOL),
                *_wrapper_argv(second_fixture, plan_only=True),
            ],
            check=False,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=10,
        )
        assert second.returncode == 125
        assert not (scratch_b / MW.CONTAINER_NAME).exists()
    finally:
        release.write_text("release\n", encoding="utf-8")
        stdout, stderr = first.communicate(timeout=10)
        assert first.returncode == 0, (stdout, stderr)


@_limited
def test_post_provision_rejects_head_mismatch_between_observation_points(
    tmp_path: Path,
) -> None:
    fixture = _make_repository(tmp_path, harness_source=_fake_harness_source())
    preflight = SimpleNamespace(checkout=fixture.main, commit="0" * 40)
    with pytest.raises(MW.MutationWorktreeError):
        MW._verify_provisioned(preflight)


@_limited
def test_teardown_removes_only_own_admin_dir_between_observation_points(
    tmp_path: Path,
) -> None:
    preflight, binding, foreign = _fake_preflight(tmp_path)
    assert MW._teardown(
        preflight, binding, runner_mode="local", evidence_required=False
    ) is False
    assert not preflight.container.exists()
    assert not binding.admin_dir.exists()
    assert (foreign / "sentinel").read_text(encoding="utf-8") == "foreign\n"


@_limited
def test_dispatch_evidence_is_relocated_before_delete_between_observation_points(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    preflight, binding, _foreign = _fake_preflight(tmp_path)
    dispatch = preflight.checkout / "output" / "pegasus-dispatch"
    dispatch.mkdir(parents=True)
    (dispatch / "receipt.json").write_text("evidence\n", encoding="utf-8")
    real_rmtree = shutil.rmtree
    observed: list[Path] = []

    def checking_rmtree(path: Path) -> None:
        observed.append(Path(path))
        if Path(path) == preflight.container:
            assert preflight.evidence.is_dir()
            assert not dispatch.exists()
        real_rmtree(path)

    monkeypatch.setattr(MW.shutil, "rmtree", checking_rmtree)
    assert MW._teardown(
        preflight, binding, runner_mode="dispatch", evidence_required=True
    ) is True
    assert observed == [preflight.container, binding.admin_dir]
    assert (preflight.evidence / "receipt.json").read_text(encoding="utf-8") == "evidence\n"


@_limited
def test_incomplete_run_keeps_container_for_resume_between_observation_points(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capfd: pytest.CaptureFixture[str],
) -> None:
    fixture = _make_repository(tmp_path, harness_source=_fake_harness_source())
    monkeypatch.setenv("IZANAGI_LEDGER_MODE", "partial")
    monkeypatch.setenv("IZANAGI_FAKE_HARNESS_RC", "0")
    assert MW.main(_wrapper_argv(fixture)) == 125
    assert (fixture.scratch / MW.CONTAINER_NAME).is_dir()
    receipt = json.loads(
        Path(f"{fixture.out}.wrapper-receipt.json").read_text(encoding="utf-8")
    )
    assert receipt["terminal_ledger"] is False
    assert receipt["container_preserved"] is True
    preserved_streams = capfd.readouterr()
    assert str(_TOOL) in preserved_streams.err
    assert "--resume" in preserved_streams.err
    assert str(fixture.scratch / MW.CONTAINER_NAME / "repo" / "tools") not in (
        preserved_streams.err.split("resume command:", 1)[-1]
    )

    monkeypatch.setenv("IZANAGI_LEDGER_MODE", "terminal")
    assert MW.main(_wrapper_argv(fixture, resume=True)) == 0
    assert not (fixture.scratch / MW.CONTAINER_NAME).exists()
    resumed_receipt = json.loads(
        Path(f"{fixture.out}.wrapper-receipt.json").read_text(encoding="utf-8")
    )
    assert resumed_receipt["terminal_ledger"] is True
    assert resumed_receipt["teardown_completed"] is True


@_limited
def test_child_return_code_is_propagated_between_observation_points() -> None:
    assert MW._select_return_code(child_rc=37, signum=None, wrapper_failed=False) == 37


@_limited
def test_teardown_failure_overrides_child_rc_between_observation_points(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    fixture = _make_repository(tmp_path, harness_source=_fake_harness_source())
    monkeypatch.setenv("IZANAGI_LEDGER_MODE", "terminal")
    monkeypatch.setenv("IZANAGI_DISPATCH_EVIDENCE", "1")

    real_rmtree = shutil.rmtree

    def failing_rmtree(path: Path) -> None:
        if Path(path) == fixture.scratch / MW.CONTAINER_NAME:
            raise OSError("injected teardown failure")
        real_rmtree(path)

    monkeypatch.setattr(MW.shutil, "rmtree", failing_rmtree)
    assert MW.main(_wrapper_argv(fixture, runner_mode="dispatch")) == 125
    receipt = json.loads(
        Path(f"{fixture.out}.wrapper-receipt.json").read_text(encoding="utf-8")
    )
    assert receipt["child_rc"] == 0
    assert receipt["dispatch_evidence"]["relocated"] is True
    assert receipt["teardown_completed"] is False


@_limited
@pytest.mark.parametrize("signum", [signal.SIGINT, signal.SIGTERM])
def test_sigint_and_sigterm_are_forwarded_between_observation_points(
    tmp_path: Path, signum: int
) -> None:
    fixture = _make_repository(tmp_path, harness_source=_fake_harness_source())
    ready = tmp_path / "child-ready"
    release = tmp_path / "never-release"
    signal_record = tmp_path / "child-signal"
    environment = os.environ.copy()
    environment.update(
        {
            "IZANAGI_READY": str(ready),
            "IZANAGI_RELEASE": str(release),
            "IZANAGI_SIGNAL_RECORD": str(signal_record),
        }
    )
    process = subprocess.Popen(
        [sys.executable, str(_TOOL), *_wrapper_argv(fixture, plan_only=True)],
        env=environment,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    try:
        deadline = time.monotonic() + 10
        while not ready.exists() and time.monotonic() < deadline:
            time.sleep(0.02)
        assert ready.is_file()
        process.send_signal(signum)
        stdout, stderr = process.communicate(timeout=15)
        assert process.returncode == 128 + signum, (stdout, stderr)
        assert signal_record.read_text(encoding="utf-8") == str(int(signum))
        assert (fixture.scratch / MW.CONTAINER_NAME).is_dir()
    finally:
        if process.poll() is None:
            process.kill()
            process.wait(timeout=5)


@_limited
def test_spec_and_out_inside_registered_worktree_are_rejected_between_observation_points(
    tmp_path: Path,
) -> None:
    repo = _plain_repo(tmp_path / "repo")
    inside_spec = repo / "spec.json"
    inside_spec.write_text("{}\n", encoding="utf-8")
    outside_spec = tmp_path / "outside.json"
    outside_spec.write_text("{}\n", encoding="utf-8")
    container = tmp_path / "generated"
    with pytest.raises(MW.MutationWorktreeError, match="--spec"):
        MW._validate_artifact_locations(
            spec_arg=inside_spec,
            out_arg=tmp_path / "outside-ledger.json",
            registered=(repo.resolve(),),
            container=container,
        )
    with pytest.raises(MW.MutationWorktreeError, match="--out"):
        MW._validate_artifact_locations(
            spec_arg=outside_spec,
            out_arg=repo / "ledger.json",
            registered=(repo.resolve(),),
            container=container,
        )
    with pytest.raises(MW.MutationWorktreeError, match="generated worktree"):
        MW._validate_artifact_locations(
            spec_arg=outside_spec,
            out_arg=container / "ledger.json",
            registered=(repo.resolve(),),
            container=container,
        )
    for suffix in (".wrapper-receipt.json", ".dispatch-evidence", ".lock"):
        out = tmp_path / f"collision-{suffix.removeprefix('.')}"
        derived_spec = Path(f"{out}{suffix}")
        derived_spec.write_text("{}\n", encoding="utf-8")
        with pytest.raises(MW.MutationWorktreeError, match="派生 artifact"):
            MW._validate_artifact_locations(
                spec_arg=derived_spec,
                out_arg=out,
                registered=(repo.resolve(),),
                container=container,
            )


@_limited
def test_terminal_ledger_rejects_boolean_counts_between_observation_points(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    fixture = _make_repository(tmp_path, harness_source=_fake_harness_source())
    monkeypatch.setenv("IZANAGI_LEDGER_MODE", "boolean-recorded")
    assert MW.main(_wrapper_argv(fixture)) == 125
    assert (fixture.scratch / MW.CONTAINER_NAME).is_dir()
    receipt = json.loads(
        Path(f"{fixture.out}.wrapper-receipt.json").read_text(encoding="utf-8")
    )
    assert receipt["terminal_ledger"] is False


@_limited
def test_checkout_git_calls_disable_hooks_between_observation_points(
    tmp_path: Path,
) -> None:
    fixture = _make_repository(tmp_path, harness_source=_fake_harness_source())
    hook_record = tmp_path / "post-checkout-ran"
    hook = fixture.main / ".git" / "hooks" / "post-checkout"
    hook.write_text(
        "#!/bin/sh\n" f"touch {shlex.quote(str(hook_record))}\n",
        encoding="utf-8",
    )
    hook.chmod(0o755)
    assert MW.main(_wrapper_argv(fixture, plan_only=True)) == 0
    assert not hook_record.exists()


@_limited
def test_shared_tree_drift_fails_closed_between_observation_points(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    fixture = _make_repository(tmp_path, harness_source=_fake_harness_source())
    source_sentinel = fixture.source / "target.py"
    main_sentinel = fixture.main / "target.py"
    source_before = source_sentinel.read_bytes()
    main_before = main_sentinel.read_bytes()
    monkeypatch.setenv(
        "IZANAGI_DRIFT_PATHS",
        os.pathsep.join((str(source_sentinel), str(main_sentinel))),
    )
    try:
        assert MW.main(_wrapper_argv(fixture, plan_only=True)) == 125
        assert source_sentinel.read_bytes() != source_before
        assert main_sentinel.read_bytes() != main_before
        receipt = json.loads(
            Path(f"{fixture.out}.wrapper-receipt.json").read_text(encoding="utf-8")
        )
        assert receipt["shared_snapshot_matches"] is False
    finally:
        source_sentinel.write_bytes(source_before)
        main_sentinel.write_bytes(main_before)


@_limited
def test_fake_harness_wrapper_is_exactly_transparent_between_observation_points(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capfd: pytest.CaptureFixture[str],
) -> None:
    fixture = _make_repository(tmp_path, harness_source=_fake_harness_source())
    monkeypatch.setenv("IZANAGI_CAPTURE", "1")
    monkeypatch.setenv("IZANAGI_FAKE_HARNESS_RC", "17")
    monkeypatch.setenv("GIT_DIR", "/poison/git-dir")
    monkeypatch.setenv("GIT_WORK_TREE", "/poison/work-tree")
    monkeypatch.setenv("GIT_INDEX_FILE", "/poison/index")
    monkeypatch.setenv("GIT_CONFIG_NOSYSTEM", "1")
    argv = _wrapper_argv(fixture, plan_only=True)

    assert MW.main(argv) == 17
    wrapper_streams = capfd.readouterr()
    capture_path = Path(str(fixture.out) + ".capture.json")
    wrapper_capture = json.loads(capture_path.read_text(encoding="utf-8"))
    checkout = fixture.scratch / MW.CONTAINER_NAME / MW.CHECKOUT_NAME
    assert not (fixture.scratch / MW.CONTAINER_NAME).exists()

    direct_script = checkout / "tools" / "mutation_harness.py"
    direct_script.parent.mkdir(parents=True)
    direct_script.write_text(_fake_harness_source(), encoding="utf-8")
    direct_environment = {
        key: value
        for key, value in os.environ.items()
        if not key.startswith("GIT_")
        or key in {"GIT_CONFIG_NOSYSTEM", "GIT_TERMINAL_PROMPT"}
    }
    direct_environment["GIT_TERMINAL_PROMPT"] = "0"
    direct_environment["PYTHONDONTWRITEBYTECODE"] = "1"
    direct = subprocess.run(
        [sys.executable, str(direct_script), *wrapper_capture["argv"]],
        cwd=fixture.scratch / MW.CONTAINER_NAME,
        env=direct_environment,
        check=False,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    direct_capture = json.loads(capture_path.read_text(encoding="utf-8"))
    assert direct.returncode == 17
    assert wrapper_capture == direct_capture
    assert wrapper_streams.out == direct.stdout
    assert wrapper_streams.err == direct.stderr
    receipt = json.loads(
        Path(f"{fixture.out}.wrapper-receipt.json").read_text(encoding="utf-8")
    )
    assert receipt["child_rc"] == 17
    assert receipt["resolved_commit"] == fixture.commit
    assert receipt["lock_path"] == f"{fixture.out}.lock"
    assert receipt["shared_snapshot_matches"] is True


@_limited
def test_real_harness_local_e2e_uses_disposable_tree_between_observation_points(
    tmp_path: Path,
) -> None:
    fixture = _make_repository(tmp_path, harness_source=_HARNESS.read_text(encoding="utf-8"))
    source_before = (fixture.source / "target.py").read_bytes()
    main_before = (fixture.main / "target.py").read_bytes()

    assert MW.main(_wrapper_argv(fixture)) == 0

    ledger = json.loads(fixture.out.read_text(encoding="utf-8"))
    assert ledger["summary"]["matching"] == 1
    assert ledger["mutations"][0]["status"] == "KILLED"
    assert ledger["mutations"][0]["failed_nodes"] == ["tests/test_gate.py::test_gate"]
    assert (fixture.source / "target.py").read_bytes() == source_before
    assert (fixture.main / "target.py").read_bytes() == main_before
    assert not (fixture.scratch / MW.CONTAINER_NAME).exists()


@_limited
def test_relocated_evidence_is_revalidated_by_resume_plan_only_between_observation_points(
    tmp_path: Path,
) -> None:
    fixture = _make_repository(
        tmp_path,
        harness_source=_HARNESS.read_text(encoding="utf-8"),
        fake_dispatch=True,
    )
    evidence = Path(f"{fixture.out}.dispatch-evidence")

    assert MW.main(_wrapper_argv(fixture, runner_mode="dispatch")) == 0
    assert evidence.is_dir()
    assert not (fixture.scratch / MW.CONTAINER_NAME).exists()

    assert MW.main(
        _wrapper_argv(
            fixture,
            runner_mode="dispatch",
            resume=True,
            plan_only=True,
        )
    ) == 0
    assert evidence.is_dir()
    assert not (fixture.scratch / MW.CONTAINER_NAME).exists()
    receipt = json.loads(
        Path(f"{fixture.out}.wrapper-receipt.json").read_text(encoding="utf-8")
    )
    assert receipt["dispatch_evidence"]["rehydrated"] is True
    assert receipt["dispatch_evidence"]["relocated"] is True
    assert receipt["shared_snapshot_matches"] is True


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__]))
