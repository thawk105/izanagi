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
import textwrap
import time
from pathlib import Path
from types import SimpleNamespace

import pytest


_REPO = Path(__file__).resolve().parents[2]
_TOOL = _REPO / "tools" / "mutation_worktree.py"
_HARNESS = _REPO / "tools" / "mutation_harness.py"
_MARKER = _REPO / "orchestrator" / "campaign" / "mutation_attempt_marker.py"
_SITE_POLICY = _REPO / "orchestrator" / "campaign" / "site_policy.py"
_DISPATCHER = _REPO / "tools" / "pegasus" / "dispatch_compute.py"
_SCHEDULER_NQSV = _REPO / "orchestrator" / "scheduler_nqsv.py"
_SPEC = importlib.util.spec_from_file_location("mutation_worktree_under_test", _TOOL)
assert _SPEC is not None and _SPEC.loader is not None
MW = importlib.util.module_from_spec(_SPEC)
sys.modules[_SPEC.name] = MW
_SPEC.loader.exec_module(MW)
_REAL_CURRENT_SITE = MW.site_policy.current_site

_LIMIT = (
    "共有木の観測点間で git status / git submodule status の stdout bytes が"
    "不変であることだけを主張し、物理永続性は主張しない。"
)


def _limited(function):
    function.__doc__ = _LIMIT
    return function


@pytest.fixture(autouse=True)
def _default_non_pegasus_site(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        MW.site_policy,
        "current_site",
        lambda *, require_evidence=False: MW.site_policy.OTHER,
    )


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
if os.environ.get('IZANAGI_ORPHAN_HOLD') == '1':
    dispatch = repo / 'output' / 'pegasus-dispatch'
    dispatch.mkdir(parents=True, exist_ok=True)
    (dispatch / 'orphan-hold.json').write_text('{}\\n', encoding='utf-8')
if os.environ.get('IZANAGI_ORPHAN_LEDGER') == '1':
    ledger = repo / 'output' / 'pegasus-dispatch' / 'orphan-holds'
    ledger.mkdir(parents=True, exist_ok=True)
    (ledger / '424242.nqsv.json').write_text('{}\\n', encoding='utf-8')
if os.environ.get('IZANAGI_ORPHAN_STOP') == '1':
    Path(str(out) + '.orphan-stop.json').write_text(json.dumps({
        'reason': {
            'code': 'orphan-hold',
            'hold_error': 'injected double hold write failure',
        },
    }), encoding='utf-8')
print('fake-harness-stdout', flush=True)
print('fake-harness-stderr', file=sys.stderr, flush=True)
raise SystemExit(int(os.environ.get('IZANAGI_FAKE_HARNESS_RC', '0')))
"""


def _fake_dispatch_source() -> str:
    # Minimal import protocol from tools/pegasus/dispatch_compute.py. Keep CLI
    # effects guarded: the real harness imports this module to budget dispatch.
    return """#!/usr/bin/env python3
import json
import os
import re
import sys
from pathlib import Path

DEFAULT_WALLTIME = "01:00:00"
DEFAULT_QUEUE_WAIT_TIMEOUT_S = 900.0
DEFAULT_OVERALL_GRACE_S = 300.0
DEFAULT_ACCOUNTING_GRACE_S = 60.0
DEFAULT_CLEANUP_BUDGET_S = 90.0

def _walltime_seconds(value: str) -> int:
    match = re.fullmatch(r"([0-9]+):([0-5][0-9]):([0-5][0-9])", value)
    if match is None:
        raise ValueError("walltime は HH:MM:SS 形式で指定してください")
    hours, minutes, seconds = (int(part) for part in match.groups())
    total = hours * 3600 + minutes * 60 + seconds
    if total <= 0:
        raise ValueError("walltime は 0 より大きくしてください")
    return total

if __name__ == '__main__':
""" + textwrap.indent("""
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
""", "    ")


def _make_repository(
    tmp_path: Path,
    *,
    harness_source: str,
    fake_dispatch: bool = False,
    real_site_policy: bool = False,
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
    campaign = main / "orchestrator" / "campaign"
    campaign.mkdir(parents=True)
    (campaign.parent / "__init__.py").write_text("", encoding="utf-8")
    (campaign / "__init__.py").write_text("", encoding="utf-8")
    site_policy_source = (
        _SITE_POLICY.read_text(encoding="utf-8")
        if real_site_policy
        else (
            "OTHER = 'OTHER'\n"
            "PEGASUS_LOGIN = 'PEGASUS_LOGIN'\n"
            "PEGASUS_COMPUTE = 'PEGASUS_COMPUTE'\n"
            "PEGASUS_SUSPECT = 'PEGASUS_SUSPECT'\n\n"
            "def current_site(*, require_evidence=False):\n"
            "    del require_evidence\n"
            "    return OTHER\n"
        )
    )
    (campaign / "site_policy.py").write_text(site_policy_source, encoding="utf-8")
    (campaign / "mutation_attempt_marker.py").write_text(
        _MARKER.read_text(encoding="utf-8"), encoding="utf-8"
    )
    if real_site_policy:
        (campaign.parent / "scheduler_nqsv.py").write_text(
            _SCHEDULER_NQSV.read_text(encoding="utf-8"), encoding="utf-8"
        )
        pegasus = main / "tools" / "pegasus"
        pegasus.mkdir()
        (pegasus / "dispatch_compute.py").write_text(
            _DISPATCHER.read_text(encoding="utf-8"), encoding="utf-8"
        )
    if fake_dispatch:
        runner = main / "tools" / "run_tests.py"
        runner.write_text(_fake_dispatch_source(), encoding="utf-8")
        runner.chmod(0o755)
        pegasus = main / "tools" / "pegasus"
        pegasus.mkdir(exist_ok=True)
        dispatcher = pegasus / "dispatch_compute.py"
        dispatcher.write_text(_fake_dispatch_source(), encoding="utf-8")
        dispatcher.chmod(0o755)
    _git(
        main,
        "add",
        ".gitignore",
        "orchestrator",
        "tools",
        "target.py",
        "tests/test_gate.py",
    )
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
    attempt_out: Path | None = None,
    wrapper_attempt: int = 1,
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
    if attempt_out is not None:
        args.extend(
            ["--attempt-out", str(attempt_out), "--wrapper-attempt", str(wrapper_attempt)]
        )
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


def _install_local_attempt_marker(
    root: Path,
    monkeypatch: pytest.MonkeyPatch,
    *,
    hostname: str = "bnode114",
) -> dict[str, str]:
    from tools.pegasus import dispatch_compute

    dispatch_root = root / "dispatch-root"
    submission = dispatch_root / "submission"
    submission.mkdir(parents=True)
    request = submission / "request.json"
    request.write_bytes(b'{"task":"mutation"}\n')
    (submission / MW.mutation_attempt_marker.COMPUTE_MARKER_NAME).write_text(
        json.dumps(
            {
                "schema_version": "pegasus-compute-visible/v1",
                "pbs_jobid": "0:424242.nqsv",
                "hostname": hostname,
            }
        )
        + "\n",
        encoding="utf-8",
    )
    binding = MW.mutation_attempt_marker.build_binding(
        dispatch_root=dispatch_root,
        submission_dir=submission,
        pbs_jobid="0:424242.nqsv",
        hostname=hostname,
        request_sha256=hashlib.sha256(request.read_bytes()).hexdigest(),
        is_regular_pbs_jobid=dispatch_compute._is_regular_pbs_jobid,
    )
    monkeypatch.setenv(
        MW.mutation_attempt_marker.MARKER_ENV,
        MW.mutation_attempt_marker.encode_binding(binding),
    )
    monkeypatch.setattr(MW.site_policy, "current_site", _REAL_CURRENT_SITE)
    monkeypatch.setattr(MW.site_policy.socket, "gethostname", lambda: hostname)
    return binding


@_limited
@pytest.mark.parametrize(
    "site", [MW.site_policy.PEGASUS_LOGIN, MW.site_policy.PEGASUS_SUSPECT]
)
def test_local_site_gate_rejects_before_preflight_lock_and_worktree_between_observation_points(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    site: str,
) -> None:
    fixture = _make_repository(tmp_path, harness_source=_fake_harness_source())
    observed: list[bool] = []

    def current_site(*, require_evidence: bool = False) -> str:
        observed.append(require_evidence)
        return site

    def unexpected(*_args: object, **_kwargs: object) -> object:
        raise AssertionError("site gate より後の preflight/lock/worktree へ到達した")

    monkeypatch.setattr(MW.site_policy, "current_site", current_site)
    monkeypatch.setattr(MW, "_preflight", unexpected)
    monkeypatch.setattr(MW, "_out_lock", unexpected)
    monkeypatch.setattr(MW, "_worktree_add", unexpected)

    assert MW.main(_wrapper_argv(fixture)) == 2
    assert observed == [True]
    assert not Path(f"{fixture.out}.lock").exists()
    assert not (fixture.scratch / MW.CONTAINER_NAME).exists()


@_limited
def test_local_site_gate_requires_evidence_for_nqsv_unreadable_login_hostname_between_observation_points(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fixture = _make_repository(tmp_path, harness_source=_fake_harness_source())
    assert (
        MW.site_policy.classify_site("pegasus02", {}, has_nqsv=False)
        == MW.site_policy.OTHER
    )
    monkeypatch.setattr(MW.site_policy, "current_site", _REAL_CURRENT_SITE)
    monkeypatch.setattr(MW.site_policy.socket, "gethostname", lambda: "pegasus02")
    monkeypatch.setattr(MW.site_policy, "_has_nqsv", lambda: False)
    monkeypatch.setattr(
        MW,
        "_preflight",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(
            AssertionError("require_evidence=True なら preflight へ到達しない")
        ),
    )

    assert MW.main(_wrapper_argv(fixture)) == 2
    assert not Path(f"{fixture.out}.lock").exists()
    assert not (fixture.scratch / MW.CONTAINER_NAME).exists()


@_limited
@pytest.mark.parametrize(
    "site", [MW.site_policy.OTHER, MW.site_policy.PEGASUS_COMPUTE]
)
def test_local_site_gate_preserves_other_and_compute_between_observation_points(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    site: str,
) -> None:
    fixture = _make_repository(tmp_path, harness_source=_fake_harness_source())
    observed: list[bool] = []

    def current_site(*, require_evidence: bool = False) -> str:
        observed.append(require_evidence)
        return site

    monkeypatch.setattr(MW.site_policy, "current_site", current_site)

    assert MW.main(_wrapper_argv(fixture, plan_only=True)) == 0
    assert observed == [True]
    assert not (fixture.scratch / MW.CONTAINER_NAME).exists()


@_limited
def test_dispatch_mode_does_not_consult_local_site_gate_between_observation_points(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fixture = _make_repository(tmp_path, harness_source=_fake_harness_source())
    monkeypatch.setattr(
        MW.site_policy,
        "current_site",
        lambda **_kwargs: (_ for _ in ()).throw(
            AssertionError("dispatch mode で local site gate を呼んだ")
        ),
    )

    assert (
        MW.main(
            _wrapper_argv(fixture, runner_mode="dispatch", plan_only=True)
        )
        == 0
    )
    assert not (fixture.scratch / MW.CONTAINER_NAME).exists()


@_limited
def test_i2_dispatch_attempt_does_not_call_marker_validator_between_observation_points(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fixture = _make_repository(tmp_path, harness_source=_fake_harness_source())
    attempts = fixture.artifacts / "attempts.json"
    monkeypatch.setattr(
        MW.mutation_attempt_marker,
        "require_local_attempt_marker",
        lambda: (_ for _ in ()).throw(
            AssertionError("dispatch mode で marker validator を呼んだ")
        ),
    )

    assert MW.main(
        _wrapper_argv(
            fixture,
            runner_mode="dispatch",
            plan_only=True,
            attempt_out=attempts,
        )
    ) == 0


@_limited
def test_i3_local_without_attempt_does_not_call_marker_validator_between_observation_points(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fixture = _make_repository(tmp_path, harness_source=_fake_harness_source())
    monkeypatch.setattr(
        MW.mutation_attempt_marker,
        "require_local_attempt_marker",
        lambda: (_ for _ in ()).throw(
            AssertionError("attempt 無し local で marker validator を呼んだ")
        ),
    )

    assert MW.main(_wrapper_argv(fixture, plan_only=True)) == 0


@_limited
def test_m2_wrapper_local_attempt_without_marker_is_rejected_before_preflight(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capfd: pytest.CaptureFixture[str],
) -> None:
    fixture = _make_repository(tmp_path, harness_source=_fake_harness_source())
    attempts = fixture.artifacts / "attempts.json"
    monkeypatch.setattr(MW.site_policy, "current_site", _REAL_CURRENT_SITE)
    monkeypatch.setattr(MW.site_policy.socket, "gethostname", lambda: "bnode114")
    monkeypatch.delenv(MW.mutation_attempt_marker.MARKER_ENV, raising=False)
    monkeypatch.setattr(
        MW,
        "_preflight",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(
            AssertionError("marker 拒否後の preflight へ到達した")
        ),
    )

    assert MW.main(
        _wrapper_argv(fixture, plan_only=True, attempt_out=attempts)
    ) == MW.WRAPPER_FAILURE_RC
    assert capfd.readouterr().err == (
        "mutation worktree aborted: local attempt authorization が不正です: "
        "mutation local attempt marker がありません\n"
    )


@_limited
def test_wrapper_local_attempt_accepts_real_validator_before_preflight(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fixture = _make_repository(tmp_path, harness_source=_fake_harness_source())
    attempts = fixture.artifacts / "attempts.json"
    binding = _install_local_attempt_marker(tmp_path / "marker", monkeypatch)

    assert MW.main(
        _wrapper_argv(fixture, plan_only=True, attempt_out=attempts)
    ) == 0
    assert json.loads(
        os.environ[MW.mutation_attempt_marker.MARKER_ENV]
    ) == binding


@_limited
def test_m11_m12_wrapper_real_harness_local_attempt_persists_authorization(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fixture = _make_repository(
        tmp_path,
        harness_source=_HARNESS.read_text(encoding="utf-8"),
        real_site_policy=True,
    )
    attempts = fixture.artifacts / "attempts.json"
    observed_hostname = os.uname().nodename
    already_compute = (
        MW.site_policy.classify_site(observed_hostname, {}, False)
        == MW.site_policy.PEGASUS_COMPUTE
    )
    marker_hostname = observed_hostname if already_compute else "bnode114"
    binding = _install_local_attempt_marker(
        tmp_path / "marker", monkeypatch, hostname=marker_hostname
    )
    environment = os.environ.copy()
    wrapper_command = [
        sys.executable,
        str(_TOOL),
        *_wrapper_argv(fixture, attempt_out=attempts),
    ]
    command = (
        wrapper_command
        if already_compute
        else [
            "unshare",
            "-Ur",
            "--uts",
            "sh",
            "-c",
            'hostname bnode114 && exec "$@"',
            "sh",
            *wrapper_command,
        ]
    )

    result = subprocess.run(
        command,
        cwd=_REPO,
        env=environment,
        check=False,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )

    assert result.returncode == 0, result.stderr
    sidecar = json.loads(attempts.read_text(encoding="utf-8"))
    assert sidecar["schema"] == "izanagi-dev-wave-mutation-attempts-local/v1"
    assert sidecar["local_authorization"] == binding
    assert [entry["phase"] for entry in sidecar["attempts"]] == [
        "collection",
        "baseline",
        "mutation",
    ]
    assert all(entry["request"] is None for entry in sidecar["attempts"])


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
    environment["PYTHONDONTWRITEBYTECODE"] = "1"
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
@pytest.mark.parametrize(
    ("plan_only", "child_rc", "terminal"),
    [(True, None, False), (False, 0, True), (False, 1, True)],
)
def test_orphan_hold_always_blocks_should_teardown_between_observation_points(
    plan_only: bool, child_rc: int | None, terminal: bool,
) -> None:
    assert MW._should_teardown(
        plan_only=plan_only,
        child_rc=child_rc,
        terminal=terminal,
        orphan_hold=True,
    ) is False


@_limited
@pytest.mark.parametrize(
    ("plan_only", "child_rc", "terminal"),
    [(True, None, False), (False, 0, True), (False, 1, True)],
)
def test_no_hold_keeps_positive_teardown_paths_between_observation_points(
    plan_only: bool, child_rc: int | None, terminal: bool,
) -> None:
    assert MW._should_teardown(
        plan_only=plan_only,
        child_rc=child_rc,
        terminal=terminal,
        orphan_hold=False,
    ) is True


@_limited
@pytest.mark.parametrize("plan_only", [True, False])
def test_orphan_hold_preserves_container_and_wrapper_receipt_between_observation_points(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capfd: pytest.CaptureFixture[str],
    plan_only: bool,
) -> None:
    fixture = _make_repository(tmp_path, harness_source=_fake_harness_source())
    monkeypatch.setenv("IZANAGI_ORPHAN_HOLD", "1")
    if not plan_only:
        monkeypatch.setenv("IZANAGI_LEDGER_MODE", "terminal")
    rc = MW.main(
        _wrapper_argv(
            fixture,
            runner_mode="dispatch",
            plan_only=plan_only,
        )
    )

    assert rc == MW.WRAPPER_FAILURE_RC
    container = fixture.scratch / MW.CONTAINER_NAME
    assert (container / "repo" / "output" / "pegasus-dispatch" / "orphan-hold.json").is_file()
    receipt = json.loads(
        Path(f"{fixture.out}.wrapper-receipt.json").read_text(encoding="utf-8")
    )
    assert receipt["failure"] == "orphan-hold"
    assert receipt["container_preserved"] is True
    assert receipt["teardown_attempted"] is False
    assert receipt["teardown_completed"] is False
    assert receipt["dispatch_evidence"]["relocated"] is False
    assert receipt["child_rc"] == 0
    assert receipt["terminal_ledger"] is (not plan_only)
    stderr = capfd.readouterr().err
    assert stderr.index("復旧順序:") < stderr.index("resume command:")
    assert "--resume は orphan hold を解除した後にだけ有効" in stderr


@_limited
def test_request_ledger_only_preserves_container_without_teardown(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fixture = _make_repository(tmp_path, harness_source=_fake_harness_source())
    monkeypatch.setenv("IZANAGI_ORPHAN_LEDGER", "1")
    monkeypatch.setenv("IZANAGI_LEDGER_MODE", "terminal")

    rc = MW.main(_wrapper_argv(fixture, runner_mode="dispatch"))

    assert rc == MW.WRAPPER_FAILURE_RC
    container = fixture.scratch / MW.CONTAINER_NAME
    ledger = (
        container
        / "repo"
        / "output"
        / "pegasus-dispatch"
        / "orphan-holds"
        / "424242.nqsv.json"
    )
    assert ledger.is_file()
    receipt = json.loads(
        Path(f"{fixture.out}.wrapper-receipt.json").read_text(encoding="utf-8")
    )
    assert receipt["failure"] == "orphan-hold"
    assert receipt["container_preserved"] is True
    assert receipt["teardown_attempted"] is False


@_limited
def test_request_ledger_scan_error_blocks_teardown(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fixture = _make_repository(tmp_path, harness_source=_fake_harness_source())
    preflight = SimpleNamespace(checkout=fixture.source, out=fixture.out)
    ledger = fixture.source / "output" / "pegasus-dispatch" / "orphan-holds"
    ledger.mkdir(parents=True)
    real_scandir = MW.os.scandir

    def fail_descriptor_scan(path):
        if isinstance(path, int):
            raise PermissionError("injected ledger scan denial")
        return real_scandir(path)

    monkeypatch.setattr(MW.os, "scandir", fail_descriptor_scan)
    blocked = MW._orphan_hold_present(preflight)
    assert blocked is True
    assert MW._should_teardown(
        plan_only=True,
        child_rc=None,
        terminal=False,
        orphan_hold=blocked,
    ) is False


@_limited
def test_orphan_hold_lstat_error_preserves_container_without_teardown(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fixture = _make_repository(tmp_path, harness_source=_fake_harness_source())
    monkeypatch.setenv("IZANAGI_LEDGER_MODE", "terminal")
    target = (
        fixture.scratch
        / MW.CONTAINER_NAME
        / "repo"
        / "output"
        / "pegasus-dispatch"
        / "orphan-hold.json"
    )
    real_lstat = os.lstat

    def indeterminate(path, *args, **kwargs):
        if Path(path) == target:
            raise OSError("injected lstat failure")
        return real_lstat(path, *args, **kwargs)

    monkeypatch.setattr(MW.os, "lstat", indeterminate)

    assert MW.main(_wrapper_argv(fixture, runner_mode="dispatch")) == (
        MW.WRAPPER_FAILURE_RC
    )
    container = fixture.scratch / MW.CONTAINER_NAME
    assert container.is_dir()
    receipt = json.loads(
        Path(f"{fixture.out}.wrapper-receipt.json").read_text(encoding="utf-8")
    )
    assert receipt["failure"] == "orphan-hold"
    assert receipt["container_preserved"] is True
    assert receipt["teardown_attempted"] is False
    assert receipt["teardown_completed"] is False


@_limited
def test_plan_only_exception_fallback_preserves_orphan_hold_container_between_observation_points(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fixture = _make_repository(tmp_path, harness_source=_fake_harness_source())
    teardown_calls = 0

    def fail_after_hold(preflight, *_args, **_kwargs):
        hold = MW._dispatch_root(preflight) / "orphan-hold.json"
        hold.parent.mkdir(parents=True)
        hold.write_text("{}\n", encoding="utf-8")
        raise RuntimeError("injected plan-only failure")

    def forbidden_teardown(*args, **kwargs):
        nonlocal teardown_calls
        teardown_calls += 1
        raise AssertionError("teardown reached despite orphan hold")

    monkeypatch.setattr(MW, "_run_harness", fail_after_hold)
    monkeypatch.setattr(MW, "_teardown", forbidden_teardown)

    assert MW.main(
        _wrapper_argv(fixture, runner_mode="dispatch", plan_only=True)
    ) == MW.WRAPPER_FAILURE_RC
    assert teardown_calls == 0
    assert (fixture.scratch / MW.CONTAINER_NAME).is_dir()
    receipt = json.loads(
        Path(f"{fixture.out}.wrapper-receipt.json").read_text(encoding="utf-8")
    )
    assert receipt["failure"] == "orphan-hold"
    assert receipt["teardown_attempted"] is False
    assert receipt["container_preserved"] is True


@_limited
def test_orphan_stop_sidecar_preserves_container_and_receipt_without_hold(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capfd: pytest.CaptureFixture[str],
) -> None:
    fixture = _make_repository(tmp_path, harness_source=_fake_harness_source())
    monkeypatch.setenv("IZANAGI_LEDGER_MODE", "terminal")
    monkeypatch.setenv("IZANAGI_ORPHAN_STOP", "1")

    assert MW.main(_wrapper_argv(fixture, runner_mode="dispatch")) == (
        MW.WRAPPER_FAILURE_RC
    )

    container = fixture.scratch / MW.CONTAINER_NAME
    assert container.is_dir()
    assert not (
        container / "repo" / "output" / "pegasus-dispatch" / "orphan-hold.json"
    ).exists()
    assert Path(f"{fixture.out}.orphan-stop.json").is_file()
    receipt = json.loads(
        Path(f"{fixture.out}.wrapper-receipt.json").read_text(encoding="utf-8")
    )
    assert receipt["failure"] == "orphan-hold"
    assert receipt["container_preserved"] is True
    assert receipt["teardown_attempted"] is False
    assert receipt["teardown_completed"] is False
    assert receipt["dispatch_evidence"]["relocated"] is False
    stderr = capfd.readouterr().err
    assert stderr.index("復旧順序:") < stderr.index("resume command:")
    assert "orphan hold と orphan-stop sidecar を手動削除" in stderr


@_limited
def test_plan_only_exception_fallback_preserves_sidecar_only_container(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capfd: pytest.CaptureFixture[str],
) -> None:
    fixture = _make_repository(tmp_path, harness_source=_fake_harness_source())
    teardown_calls = 0

    def fail_after_sidecar(preflight, *_args, **_kwargs):
        Path(f"{preflight.out}.orphan-stop.json").write_text(
            '{"reason": {"code": "orphan-hold"}}\n', encoding="utf-8"
        )
        raise RuntimeError("injected plan-only sidecar failure")

    def forbidden_teardown(*args, **kwargs):
        nonlocal teardown_calls
        teardown_calls += 1
        raise AssertionError("teardown reached despite orphan-stop sidecar")

    monkeypatch.setattr(MW, "_run_harness", fail_after_sidecar)
    monkeypatch.setattr(MW, "_teardown", forbidden_teardown)

    assert MW.main(
        _wrapper_argv(fixture, runner_mode="dispatch", plan_only=True)
    ) == MW.WRAPPER_FAILURE_RC
    assert teardown_calls == 0
    container = fixture.scratch / MW.CONTAINER_NAME
    assert container.is_dir()
    assert not (
        container / "repo" / "output" / "pegasus-dispatch" / "orphan-hold.json"
    ).exists()
    receipt = json.loads(
        Path(f"{fixture.out}.wrapper-receipt.json").read_text(encoding="utf-8")
    )
    assert receipt["failure"] == "orphan-hold"
    assert receipt["teardown_attempted"] is False
    assert receipt["teardown_completed"] is False
    assert receipt["container_preserved"] is True
    assert receipt["dispatch_evidence"]["relocated"] is False
    stderr = capfd.readouterr().err
    assert stderr.index("復旧順序:") < stderr.index("resume command:")
    assert "orphan hold と orphan-stop sidecar を手動削除" in stderr


@_limited
def test_dispatch_without_hold_or_sidecar_tears_down_as_before(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    fixture = _make_repository(tmp_path, harness_source=_fake_harness_source())
    monkeypatch.setenv("IZANAGI_LEDGER_MODE", "terminal")
    monkeypatch.setenv("IZANAGI_DISPATCH_EVIDENCE", "1")

    assert MW.main(_wrapper_argv(fixture, runner_mode="dispatch")) == 0
    assert not (fixture.scratch / MW.CONTAINER_NAME).exists()
    assert not Path(f"{fixture.out}.orphan-stop.json").exists()
    receipt = json.loads(
        Path(f"{fixture.out}.wrapper-receipt.json").read_text(encoding="utf-8")
    )
    assert receipt["failure"] is None
    assert receipt["container_preserved"] is False
    assert receipt["teardown_attempted"] is True
    assert receipt["teardown_completed"] is True
    assert receipt["dispatch_evidence"]["relocated"] is True


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
    environment["PYTHONDONTWRITEBYTECODE"] = "1"
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


@_limited
def test_dispatch_attempt_sidecar_records_every_request_between_observation_points(
    tmp_path: Path,
) -> None:
    fixture = _make_repository(
        tmp_path,
        harness_source=_HARNESS.read_text(encoding="utf-8"),
        fake_dispatch=True,
    )
    attempts = fixture.artifacts / "attempts.json"

    assert MW.main(
        _wrapper_argv(
            fixture,
            runner_mode="dispatch",
            attempt_out=attempts,
            wrapper_attempt=1,
        )
    ) == 0

    sidecar = json.loads(attempts.read_text(encoding="utf-8"))
    assert sidecar["schema"] == "izanagi-dev-wave-mutation-attempts/v1"
    assert sidecar["expected_initial_requests"] == 3
    assert [entry["phase"] for entry in sidecar["attempts"]] == [
        "collection",
        "baseline",
        "mutation",
    ]
    assert [entry["state"] for entry in sidecar["attempts"]] == [
        "finished",
        "finished",
        "finished",
    ]
    request_ids = [entry["request"]["request_id"] for entry in sidecar["attempts"]]
    assert len(request_ids) == len(set(request_ids)) == 3
    assert sidecar["attempts"][2]["mutation_id"] == "MW-E2E"
    assert not (fixture.scratch / MW.CONTAINER_NAME).exists()


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__]))
