from __future__ import annotations

import asyncio
import concurrent.futures
import copy
from dataclasses import replace
import json
import multiprocessing
import multiprocessing.context
import os
from pathlib import Path
import pty
import re
import subprocess
import sys

import pytest

from tools.pegasus import run_acceptance_nproc_study as study


_HEAD = "1" * 40
_SHIRAKAMI_HEAD = "2" * 40
_GOOGLETEST_HEAD = "3" * 40
_SUBMODULE_ROWS = (
    (_HEAD, "external/ccbench", None, "external/ccbench"),
    (
        _SHIRAKAMI_HEAD,
        "external/ccbench/third_party/shirakami",
        "external/ccbench",
        "third_party/shirakami",
    ),
    (
        _GOOGLETEST_HEAD,
        "external/ccbench/third_party/shirakami/third_party/googletest",
        "external/ccbench/third_party/shirakami",
        "third_party/googletest",
    ),
)
_SUBMODULE_STATUS = "".join(
    f" {head} {path}\n" for head, path, _parent, _relative in _SUBMODULE_ROWS
)
_GITLINK = f"160000 commit {_HEAD}\texternal/ccbench"
_JUNIT = b"""<?xml version="1.0" encoding="utf-8"?>
<testsuite tests="2" failures="0" errors="0" skipped="0">
  <testcase classname="suite.test_fast" name="test_a" time="0.5" />
  <testcase classname="suite.test_repo" name="test_b@real_repo" time="0.25" />
</testsuite>
"""
_JUNIT_REVERSED = b"""<?xml version="1.0" encoding="utf-8"?>
<testsuite tests="2" failures="0" errors="0" skipped="0">
  <testcase classname="suite.test_repo" name="test_b@real_repo" time="0.25" />
  <testcase classname="suite.test_fast" name="test_a" time="0.5" />
</testsuite>
"""
_JUNIT_ONE_TEST = b"""<?xml version="1.0" encoding="utf-8"?>
<testsuite tests="1" failures="0" errors="0" skipped="0">
  <testcase classname="suite.test_fast" name="test_a" time="0.5" />
</testsuite>
"""
_JUNIT_SKIPPED = b"""<?xml version="1.0" encoding="utf-8"?>
<testsuite tests="2" failures="0" errors="0" skipped="1">
  <testcase classname="suite.test_fast" name="test_a" time="0.5"><skipped /></testcase>
  <testcase classname="suite.test_repo" name="test_b@real_repo" time="0.25" />
</testsuite>
"""
_PATH_BASE_START = "# BEGIN acceptance nproc ambient PATH construction"
_PATH_BASE_END = "# END acceptance nproc ambient PATH construction"
_PATH_SHIM_START = "# BEGIN acceptance nproc Python shim PATH prefix"
_PATH_SHIM_END = "# END acceptance nproc Python shim PATH prefix"
_FALLBACK_PATH_CONSTRUCTION = """PATH="/usr/bin:/bin"
  for candidate in /opt/nec/nqsv/bin /system/tool/bin; do
    [[ -d "$candidate" ]] || continue
    PATH="${PATH}:$candidate"
  done"""
_RESET_PATH_MUTATION = """export PATH="/usr/bin:/bin"
for candidate in /opt/nec/nqsv/bin /system/tool/bin; do
  [[ -d "$candidate" ]] || continue
  PATH="${PATH}:$candidate"
done
export PATH"""


def _acceptance_shell_text() -> str:
    repo = Path(__file__).resolve().parents[2]
    return (repo / "tools/pegasus/acceptance_nproc_study.sh").read_text(
        encoding="utf-8"
    )


def _marked_shell_block(text: str, start_marker: str, end_marker: str) -> str:
    assert text.count(start_marker) == 1
    assert text.count(end_marker) == 1
    start = text.index(start_marker) + len(start_marker)
    end = text.index(end_marker, start)
    return text[start:end].strip()


def _evaluated_study_path(
    text: str, ambient_elements: tuple[str, ...],
) -> tuple[str, ...]:
    assert ambient_elements
    assert all(ambient_elements)
    base_block = _marked_shell_block(text, _PATH_BASE_START, _PATH_BASE_END)
    shim_block = _marked_shell_block(text, _PATH_SHIM_START, _PATH_SHIM_END)
    synthetic_tmp = "/synthetic/acceptance-nproc-study"
    script = "\n".join((
        "set -eu",
        base_block,
        f"TMPDIR={synthetic_tmp}",
        shim_block,
        'printf "%s" "$PATH"',
    ))
    completed = subprocess.run(
        ["/bin/bash", "-c", script],
        check=True,
        capture_output=True,
        env={"PATH": os.pathsep.join(ambient_elements)},
        text=True,
    )
    assert completed.stderr == ""
    return tuple(completed.stdout.split(os.pathsep))


def _assert_exact_study_path_contract(text: str) -> None:
    ambient_elements = (
        "/synthetic/ambient-alpha",
        "/synthetic/ambient-beta",
        "/synthetic/ambient-gamma",
    )
    assert ambient_elements
    observed = _evaluated_study_path(text, ambient_elements)
    expected = (
        "/synthetic/acceptance-nproc-study/python-shim",
        *ambient_elements,
    )
    assert observed == expected, (
        f"observed PATH elements {observed!r} differ from exact {expected!r}"
    )
    assert observed[0] == expected[0]
    assert observed[1:] == ambient_elements


def test_acceptance_path_prefixes_shim_and_preserves_exact_ambient_order() -> None:
    shell_text = _acceptance_shell_text()
    base_block = _marked_shell_block(
        shell_text, _PATH_BASE_START, _PATH_BASE_END
    )
    assert _FALLBACK_PATH_CONSTRUCTION in base_block
    pinned_shims = """ln -s "$PY" "$TMPDIR/python-shim/python3"
ln -s "$PY" "$TMPDIR/python-shim/python3.10"""
    assert pinned_shims in shell_text
    assert shell_text.index(pinned_shims) < shell_text.index(_PATH_SHIM_START)
    _assert_exact_study_path_contract(shell_text)


def test_acceptance_path_contract_rejects_reset_mutation() -> None:
    shell_text = _acceptance_shell_text()
    base_block = _marked_shell_block(
        shell_text, _PATH_BASE_START, _PATH_BASE_END
    )
    assert "AMBIENT_PATH=${PATH:-}" in base_block
    assert shell_text.count(base_block) == 1
    reset_mutation = shell_text.replace(base_block, _RESET_PATH_MUTATION, 1)
    assert reset_mutation != shell_text
    with pytest.raises(AssertionError, match="observed PATH elements"):
        _assert_exact_study_path_contract(reset_mutation)


@pytest.fixture(autouse=True)
def _fixed_python_user_base(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("PYTHONUSERBASE", str(tmp_path / "python-user-base"))
    cache_root = tmp_path / "thirdparty-cache"
    cache_root.mkdir()
    monkeypatch.setenv(study.THIRDPARTY_CACHE_ENV, str(cache_root))


def _cleanup(*, residual: list[int] | None = None) -> dict[str, object]:
    return {
        "kill_sent": False,
        "reaped": not residual,
        "residual_pids": [] if residual is None else residual,
        "term_sent": False,
    }


def _isolation(host: str) -> dict[str, object]:
    return {
        "disturbance_candidates": [],
        "disturbance_rule": study.DISTURBANCE_RULE,
        "disturbed": False,
        "host_end": host,
        "host_match": True,
        "host_start": host,
        "interval_s": 1.0,
        "max_gap_s": 1.0,
        "processes": [],
        "read_errors": [],
        "sample_count": 2,
        "valid": True,
    }


class FakeExecutor:
    def __init__(
        self, root: Path, host: str, *, dirty_after_measurement: bool = False,
        junit_by_nproc: dict[str, bytes] | None = None,
        honor_submodule_init: bool = True,
        imports_available: bool = True,
        write_junit: bool = True,
        measurement_returncode: int = 0,
        honor_absorbgitdirs: bool = True,
        missing_absorbed_gitdir: str | None = None,
        clone_gitmodules_mode: int | None = None,
    ):
        self.root = root
        self.host = host
        self.dirty_after_measurement = dirty_after_measurement
        self.junit_by_nproc = {} if junit_by_nproc is None else dict(junit_by_nproc)
        self.honor_submodule_init = honor_submodule_init
        self.imports_available = imports_available
        self.write_junit = write_junit
        self.measurement_returncode = measurement_returncode
        self.honor_absorbgitdirs = honor_absorbgitdirs
        self.missing_absorbed_gitdir = missing_absorbed_gitdir
        self.clone_gitmodules_mode = clone_gitmodules_mode
        self.measurement_seen = False
        self.requests: list[study.ExecRequest] = []
        self.clone_root: Path | None = None
        self.materialized_order: list[str] = []
        self.registered: set[str] = set()
        self.registered_order: list[str] = []
        self.pre_init_statuses: list[str] = []
        self.configured_urls: dict[str, str] = {}
        self.absorbed_gitdirs: dict[str, Path] = {}
        self.absorbed_order: list[str] = []

    def _clone_relative(self, repo: Path) -> str:
        assert self.clone_root is not None
        relative = repo.relative_to(self.clone_root)
        return "" if relative == Path(".") else relative.as_posix()

    def _direct_submodule(self, owner: Path) -> tuple[str, str]:
        owner_path = self._clone_relative(owner)
        matches = [
            (path, relative)
            for _head, path, parent, relative in _SUBMODULE_ROWS
            if (parent or "") == owner_path
        ]
        assert len(matches) == 1
        return matches[0]

    def _scratch_submodule_status(self) -> str:
        rows: list[str] = []
        for head, path, parent, _relative in _SUBMODULE_ROWS:
            if parent is not None and parent not in self.registered:
                continue
            prefix = " " if path in self.registered else "-"
            rows.append(f"{prefix}{head} {path}\n")
        return "".join(rows)

    def _head_for_repo(self, repo: Path) -> str:
        roots = (self.root / "repo", self.clone_root)
        for root in roots:
            if root is None:
                continue
            try:
                relative = repo.relative_to(root).as_posix()
            except ValueError:
                continue
            for head, path, _parent, _direct in _SUBMODULE_ROWS:
                if relative == path:
                    return head
        return _HEAD

    def __call__(self, request: study.ExecRequest) -> study.ExecResult:
        self.requests.append(request)
        stdout = b""
        stderr = b""
        returncode = 0
        if request.purpose.startswith("qstat:"):
            stdout = (
                "(Per-Req) Elapse Time Limit = Max: 14400S\n"
                "Remaining Elapse = 14399S\n"
                f"Execution Host = {self.host}/0\n"
            ).encode()
        elif request.purpose == "clone-superproject":
            destination = Path(request.argv[-1])
            self.clone_root = destination
            (destination / "tools/pegasus").mkdir(parents=True)
            (destination / ".git").mkdir()
            canonical_gitmodules = self.root / "repo/.gitmodules"
            clone_gitmodules = destination / ".gitmodules"
            clone_gitmodules.write_bytes(canonical_gitmodules.read_bytes())
            clone_gitmodules.chmod(
                canonical_gitmodules.stat().st_mode & 0o777
                if self.clone_gitmodules_mode is None
                else self.clone_gitmodules_mode
            )
        elif request.purpose.startswith("materialize-submodule:"):
            destination = Path(request.argv[-1])
            destination.mkdir(parents=True, exist_ok=True)
            (destination / ".git").mkdir()
            self.materialized_order.append(request.purpose.split(":", 1)[1])
        elif request.purpose == "validate-measurement-imports":
            if not self.imports_available:
                returncode = 86
                stderr = b"fake pytest/xdist import failure"
        elif request.purpose == "create-acceptance-shard-session":
            session = self.root / "sessions" / f"session-{len(self.requests):04d}"
            for index in range(2):
                (session / f"shard-{index}").mkdir(parents=True)
            stdout = f"{session}\n".encode()
        elif request.purpose.startswith("measurement:"):
            assert request.tmp_capacity is not None
            tmp_tree = Path(request.env["TMPDIR"])
            assert tmp_tree.is_dir()
            start_free = study._sample_tmp_free_bytes(request.tmp_capacity.path)
            start_sample = {
                "free_bytes": start_free,
                "monotonic_s": 0.0,
                "read_errors": [],
            }
            preflight = study.summarize_tmp_capacity_samples(
                [start_sample], spec=request.tmp_capacity,
            )
            if preflight["passed"] is True:
                self.measurement_seen = True
                (tmp_tree / "fake-pytest-temp").write_bytes(
                    b"measured temporary data"
                )
            end_free = study._sample_tmp_free_bytes(request.tmp_capacity.path)
            tmp_capacity = study.summarize_tmp_capacity_samples(
                [
                    start_sample,
                    {
                        "free_bytes": end_free,
                        "monotonic_s": 1.0,
                        "read_errors": [],
                    },
                ],
                spec=request.tmp_capacity,
            )
            session_token = next(
                token for token in request.argv
                if token.startswith("--izanagi-acceptance-shard-session=")
            )
            shard_token = next(
                token for token in request.argv
                if token.startswith("--izanagi-acceptance-shard-index=")
            )
            session = Path(session_token.split("=", 1)[1])
            shard = int(shard_token.split("=", 1)[1])
            junit = self.junit_by_nproc.get(request.env["IZANAGI_TEST_NPROC"], _JUNIT)
            if self.write_junit and tmp_capacity["passed"] is True:
                (session / f"shard-{shard}" / "junit.xml").write_bytes(junit)
            return study.ExecResult(
                returncode=self.measurement_returncode,
                stdout=b"measurement stdout",
                stderr=b"",
                duration_s=1.0 + shard / 10,
                timed_out=False,
                stdout_sha256=study._sha256(b"measurement stdout"),
                stderr_sha256=study._sha256(b""),
                isolation=_isolation(self.host),
                process_cleanup=_cleanup(),
                tmp_capacity=tmp_capacity,
            )
        elif len(request.argv) >= 4 and request.argv[0:2] == ("git", "-C"):
            repo = Path(request.argv[2])
            args = request.argv[3:]
            if args == ("rev-parse", "HEAD"):
                stdout = f"{self._head_for_repo(repo)}\n".encode()
            elif args == ("submodule", "status", "--recursive"):
                if repo == self.root / "repo":
                    stdout = _SUBMODULE_STATUS.encode()
                else:
                    assert repo == self.clone_root
                    stdout = self._scratch_submodule_status().encode()
            elif args == ("ls-tree", "HEAD", "external/ccbench"):
                stdout = f"{_GITLINK}\n".encode()
            elif args == (
                "config", "-z", "-f", ".gitmodules", "--get-regexp",
                r"^submodule\..*\.path$",
            ):
                _path, relative = self._direct_submodule(repo)
                stdout = f"submodule.{relative}.path\n{relative}\0".encode()
            elif len(args) == 4 and args[:3] == ("submodule", "init", "--"):
                path, relative = self._direct_submodule(repo)
                assert args[3] == relative
                before = self._scratch_submodule_status()
                self.pre_init_statuses.append(before)
                if self.honor_submodule_init:
                    visible = {
                        row[42:]
                        for row in before.splitlines()
                    }
                    if path not in visible:
                        returncode = 1
                        stderr = b"nested submodule is not visible before parent registration"
                    else:
                        self.registered.add(path)
                        self.registered_order.append(path)
            elif (
                len(args) == 5
                and args[:3] == ("config", "--local", "--replace-all")
            ):
                path, relative = self._direct_submodule(repo)
                assert args[3] == f"submodule.{relative}.url"
                self.configured_urls[path] = args[4]
            elif (
                len(args) == 4
                and args[:3] == ("config", "--local", "--get-all")
            ):
                path, relative = self._direct_submodule(repo)
                assert args[3] == f"submodule.{relative}.url"
                stdout = f"{self.configured_urls[path]}\n".encode()
            elif (
                len(args) == 4
                and args[:3] == ("submodule", "absorbgitdirs", "--")
            ):
                path, relative = self._direct_submodule(repo)
                assert args[3] == relative
                self.absorbed_order.append(path)
                if self.honor_absorbgitdirs:
                    owner_path = self._clone_relative(repo)
                    owner_gitdir = (
                        self.clone_root / ".git"
                        if not owner_path
                        else self.absorbed_gitdirs[owner_path]
                    )
                    target = owner_gitdir / "modules" / relative
                    marker = repo / relative / ".git"
                    marker.rmdir()
                    if path != self.missing_absorbed_gitdir:
                        target.mkdir(parents=True)
                    marker.write_text(
                        f"gitdir: {os.path.relpath(target, marker.parent)}\n",
                        encoding="utf-8",
                    )
                    self.absorbed_gitdirs[path] = target
            elif args and args[0] == "status":
                if (
                    self.dirty_after_measurement
                    and self.measurement_seen
                    and "after:status" in request.purpose
                ):
                    stdout = b" M orchestrator/tests/example.py\n"
            elif args and args[0] == "diff":
                stdout = b""
        return study.ExecResult(
            returncode=returncode,
            stdout=stdout,
            stderr=stderr,
            duration_s=0.001,
            timed_out=False,
            stdout_sha256=study._sha256(stdout),
            stderr_sha256=study._sha256(stderr),
            isolation=_isolation(self.host),
            process_cleanup=_cleanup(),
        )


def _config(tmp_path: Path) -> study.StudyConfig:
    repo = tmp_path / "repo"
    scratch = tmp_path / "scratch"
    output_root = tmp_path / "receipts"
    (repo / "external/ccbench").mkdir(parents=True)
    (repo / ".gitmodules").write_text(
        "[submodule \"external/ccbench\"]\n", encoding="utf-8"
    )
    (repo / ".gitmodules").chmod(0o644)
    scratch.mkdir()
    output_root.mkdir()
    return study.StudyConfig(
        repo_root=repo,
        output=output_root / "receipt.json",
        scratch_root=scratch,
        mode="smoke",
        seed="unit-seed",
        requested_elapstim_s=14400,
        setup_cap_s=900,
        arm_timeout_s={
            arm: study.SMOKE_ARM_LIVENESS_CAP_S for arm in study.ARMS
        },
        finalize_reserve_s=300,
        margin_s=60,
    )


def _failed_schema_fixture(tmp_path: Path) -> dict[str, object]:
    config = _config(tmp_path)
    receipt = study._new_receipt(
        config, study.build_schedule("smoke", "unit-seed"), planned_total_s=3000
    )
    receipt["status"] = "failed"
    receipt["failure"] = {"message": "fixture", "stage": "unit", "type": "ContractError"}
    receipt["completed_epoch_s"] = 1
    return receipt


def _manifest_runs(
    schedule: tuple[study.ScheduleBlock, ...],
) -> list[dict[str, object]]:
    runs: list[dict[str, object]] = []
    for expected in study._expected_run_manifest(schedule):
        runs.append({
            **expected,
            "session_root": (
                f"/sessions/block-{expected['global_block_index']}"
                f"-arm-{expected['arm']}"
            ),
        })
    return runs


def _poison_process_creation(monkeypatch: pytest.MonkeyPatch) -> None:
    def poison(*_args: object, **_kwargs: object) -> object:
        raise AssertionError("real process creation escaped the injected fake executor")

    for name in (
        "Popen", "run", "call", "check_call", "check_output", "getoutput", "getstatusoutput",
    ):
        monkeypatch.setattr(subprocess, name, poison)
    for name in (
        "system", "popen", "spawnl", "spawnle", "spawnlp", "spawnlpe", "spawnv",
        "spawnve", "spawnvp", "spawnvpe", "posix_spawn", "posix_spawnp", "fork", "forkpty",
        "execl", "execle", "execlp", "execlpe", "execv", "execve", "execvp", "execvpe",
    ):
        if hasattr(os, name):
            monkeypatch.setattr(os, name, poison)
    monkeypatch.setattr(multiprocessing, "Process", poison)
    context_types = {
        value
        for value in vars(multiprocessing.context).values()
        if (
            isinstance(value, type)
            and issubclass(value, multiprocessing.context.BaseContext)
            and "Process" in vars(value)
        )
    }
    for context_type in context_types:
        monkeypatch.setattr(context_type, "Process", poison)
    monkeypatch.setattr(concurrent.futures, "ProcessPoolExecutor", poison)
    monkeypatch.setattr(pty, "fork", poison)
    monkeypatch.setattr(asyncio, "create_subprocess_exec", poison)
    monkeypatch.setattr(asyncio, "create_subprocess_shell", poison)


def test_process_creation_tripwire_fires_on_every_multiprocessing_context(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _poison_process_creation(monkeypatch)
    process_factories = [
        multiprocessing.Process,
        multiprocessing.context._default_context.Process,
        *(
            multiprocessing.get_context(method).Process
            for method in multiprocessing.get_all_start_methods()
        ),
    ]
    for process_factory in process_factories:
        with pytest.raises(
            AssertionError,
            match="real process creation escaped the injected fake executor",
        ):
            process_factory()


def test_full_schedule_uses_each_permutation_once_and_excludes_warmup() -> None:
    schedule = study.build_schedule("full", "seed-a")
    assert len(schedule) == 7
    assert schedule[0].phase == "warmup"
    assert schedule[0].analysis_block_index is None
    measured = [block for block in schedule if block.phase == "measurement"]
    assert len(measured) == 6
    assert len({block.arm_order for block in measured}) == 6
    assert {arm for block in measured for arm in block.arm_order} == {16, 32, 48}
    assert study.build_schedule("full", "seed-a") == schedule
    assert study._rank("seed-a", "measurement-0", (16, 32, 48)) != study._rank(
        "seed-b", "measurement-0", (16, 32, 48)
    )


def test_validate_full_schedule_rejects_missing_or_duplicate_permutations() -> None:
    valid = study.build_schedule("full", "seed-a")
    study.validate_schedule(valid, mode="full")

    only_five_measured = list(valid)
    only_five_measured[-1] = replace(only_five_measured[-1], phase="warmup")
    with pytest.raises(study.ContractError) as missing_exc:
        study.validate_schedule(only_five_measured, mode="full")
    assert str(missing_exc.value) == (
        "full measurement schedule must use all six permutations once"
    )

    duplicate_permutation = list(valid)
    duplicate_permutation[-1] = replace(
        duplicate_permutation[-1], arm_order=duplicate_permutation[-2].arm_order
    )
    with pytest.raises(study.ContractError) as duplicate_exc:
        study.validate_schedule(duplicate_permutation, mode="full")
    assert str(duplicate_exc.value) == (
        "full measurement schedule must use all six permutations once"
    )


def test_smoke_has_one_measured_block_and_no_warmup() -> None:
    schedule = study.build_schedule("smoke", "seed-a")
    assert len(schedule) == 1
    assert schedule[0].phase == "measurement"
    assert schedule[0].analysis_block_index == 0


def test_run_manifest_rejects_warmup_measurement_swap_with_same_analysis_count() -> None:
    schedule = study.build_schedule("full", "seed-a")
    runs = _manifest_runs(schedule)
    study.validate_run_manifest(runs, schedule)
    for run in runs[:6]:
        run["analysis_block_index"] = 0
        run["analysis_included"] = True
    for run in runs[6:12]:
        run["analysis_block_index"] = None
        run["analysis_included"] = False
    assert sum(run["analysis_included"] is True for run in runs) == 36
    with pytest.raises(study.ContractError, match="run manifest differs from schedule"):
        study.validate_run_manifest(runs, schedule)


def test_run_manifest_rejects_fixed_arm_order_behind_balanced_schedule() -> None:
    schedule = study.build_schedule("full", "seed-a")
    block = next(
        block for block in schedule
        if block.phase == "measurement" and block.arm_order != study.ARMS
    )
    runs = _manifest_runs(schedule)
    start = block.global_block_index * len(study.ARMS) * study.SHARD_COUNT
    for order_index, arm in enumerate(study.ARMS):
        for shard_index in range(study.SHARD_COUNT):
            run = runs[start + order_index * study.SHARD_COUNT + shard_index]
            run["arm"] = arm
            run["session_root"] = f"/sessions/fixed-arm-{arm}"
    with pytest.raises(study.ContractError, match="field arm"):
        study.validate_run_manifest(runs, schedule)


def test_run_manifest_rejects_cross_block_shard_label_and_split_session() -> None:
    schedule = study.build_schedule("full", "seed-a")
    cross_block = _manifest_runs(schedule)
    cross_block[1]["global_block_index"] = 1
    with pytest.raises(study.ContractError, match="field global_block_index"):
        study.validate_run_manifest(cross_block, schedule)

    split_session = _manifest_runs(schedule)
    split_session[1]["session_root"] = "/sessions/different-arm-pair"
    with pytest.raises(study.ContractError, match="different session_root"):
        study.validate_run_manifest(split_session, schedule)


def test_budget_strictly_rejects_equality() -> None:
    with pytest.raises(study.ContractError, match="strictly"):
        study.validate_budget(
            setup_cap_s=1,
            block_count=1,
            arm_timeout_s={16: 1, 32: 1, 48: 1},
            finalize_reserve_s=1,
            requested_elapstim_s=5,
        )
    assert study.validate_budget(
        setup_cap_s=1,
        block_count=1,
        arm_timeout_s={16: 1, 32: 1, 48: 1},
        finalize_reserve_s=1,
        requested_elapstim_s=6,
    ) == 5


def test_remaining_budget_strictly_rejects_equality() -> None:
    with pytest.raises(study.ContractError, match="strictly"):
        study.validate_remaining_budget(
            remaining_s=10, remaining_arm_timeout_s=5,
            finalize_reserve_s=3, margin_s=2,
        )


def test_arm_timeout_preserves_every_postrun_fingerprint_window() -> None:
    assert study.allocate_shard_timeout(arm_remaining_s=600.0, remaining_shards=2) == 270.0
    assert study.allocate_shard_timeout(
        arm_remaining_s=600.0,
        remaining_shards=2,
        observed_cleanup_reserve_s=5.0,
    ) == 265.0
    with pytest.raises(study.ContractError, match="postrun fingerprint"):
        study.allocate_shard_timeout(arm_remaining_s=60.0, remaining_shards=2)


def test_timeout_basis_rejects_small_smoke_cap_and_full_without_calibration(
    tmp_path: Path,
) -> None:
    smoke = _config(tmp_path)
    with pytest.raises(study.ContractError, match="fixed per-arm liveness cap"):
        study.validate_timeout_calibration(
            replace(smoke, arm_timeout_s={16: 600, 32: 600, 48: 600})
        )
    with pytest.raises(study.ContractError, match="complete smoke calibration receipt"):
        study.validate_timeout_calibration(replace(smoke, mode="full"))


def test_junit_diagnostics_record_serial_work_and_real_repo_chain() -> None:
    result = study.analyze_junit(_JUNIT)
    assert result["test_count"] == 2
    assert result["serial_work_sum_s"] == pytest.approx(0.75)
    assert result["real_repo_exclusive_chain_s"] == pytest.approx(0.25)
    assert result["real_repo_test_count"] == 1


def test_junit_identity_set_digest_is_order_independent() -> None:
    original = study.analyze_junit(_JUNIT)
    reversed_order = study.analyze_junit(_JUNIT_REVERSED)
    assert original["nodeids_sha256"] != reversed_order["nodeids_sha256"]
    assert (
        original["testcase_identity_set_sha256"]
        == reversed_order["testcase_identity_set_sha256"]
    )


def test_junit_identity_sets_require_every_shard_index() -> None:
    digest = study._sha256(b"fixed-testcase-identity-set")
    skipped_digest = study._sha256(b"fixed-skipped-testcase-identity-set")
    valid = [
        {
            "shard_index": shard_index,
            "junit": {
                "skipped_testcase_identity_set_sha256": skipped_digest,
                "testcase_identity_set_sha256": digest,
            },
        }
        for shard_index in range(study.SHARD_COUNT)
    ]
    study.validate_junit_identity_sets(valid)

    with pytest.raises(study.ContractError) as exc_info:
        study.validate_junit_identity_sets(valid[:1])
    assert str(exc_info.value) == (
        "JUnit testcase identity sets do not cover every shard"
    )


def test_continuous_isolation_detects_middle_only_same_uid_consumer() -> None:
    identity = (9001, 321)
    process = {"command": "compiler", "pgroup": 700, "ticks": 8, "uid": 1001}
    samples = [
        {"hostname": "bnode001", "monotonic_s": 0.0, "processes": {}, "read_errors": []},
        {"hostname": "bnode001", "monotonic_s": 1.0,
         "processes": {identity: process}, "read_errors": []},
        {"hostname": "bnode001", "monotonic_s": 2.0, "processes": {}, "read_errors": []},
    ]
    result = study.summarize_isolation_samples(
        samples, own_uid=1001, exempt_pgroups={100, 200}, expected_host="bnode001"
    )
    assert result["valid"] is True
    assert result["disturbed"] is True
    assert result["disturbance_candidates"][0]["uid_relation"] == "same"
    assert result["disturbance_candidates"][0]["created"] is True
    assert result["disturbance_candidates"][0]["disappeared"] is True


def test_continuous_isolation_does_not_reject_other_uid_system_activity() -> None:
    identity = (91, 654)
    system_process = {
        "command": "pbs-monitor", "pgroup": 700, "ticks": 20, "uid": 0,
    }
    samples = [
        {
            "hostname": "bnode001", "monotonic_s": 0.0,
            "processes": {identity: {**system_process, "ticks": 2}}, "read_errors": [],
        },
        {
            "hostname": "bnode001", "monotonic_s": 1.0,
            "processes": {identity: system_process}, "read_errors": [],
        },
    ]
    result = study.summarize_isolation_samples(
        samples, own_uid=42, exempt_pgroups=set(), expected_host="bnode001"
    )
    assert result["valid"] is True
    assert result["disturbed"] is False
    assert result["disturbance_candidates"] == []
    assert result["processes"][0]["uid"] == 0


def test_sampler_gap_or_read_failure_is_invalid() -> None:
    samples = [
        {"hostname": "bnode001", "monotonic_s": 0.0, "processes": {}, "read_errors": []},
        {"hostname": "bnode001", "monotonic_s": 2.0, "processes": {},
         "read_errors": ["77:PermissionError"]},
    ]
    result = study.summarize_isolation_samples(
        samples, own_uid=42, exempt_pgroups=set(), expected_host="bnode001"
    )
    assert result["valid"] is False


def test_proc_snapshot_records_ppid_cwd_and_exe_for_the_reader_itself() -> None:
    snapshot = study._read_proc_snapshot()
    own_rows = [
        row for (pid, _starttime), row in snapshot["processes"].items()
        if pid == os.getpid()
    ]
    assert own_rows
    assert len(own_rows) == 1
    row = own_rows[0]
    assert row["ppid"] == os.getppid()
    assert row["cwd"] == str(Path.cwd())
    assert isinstance(row["exe"], str)
    assert Path(row["exe"]).is_absolute()


def _owned_workload_shape_samples() -> tuple[list[dict[str, object]], tuple[Path, Path]]:
    scratch_root = Path("/scr/unit-acceptance-job")
    tmp_root = Path("/tmp/izn-unit000000/run-000")
    root_identity = (5000, 11)
    root_process = {
        "command": f"python3.10 {scratch_root}/tools/run_tests.py",
        "cwd": str(scratch_root),
        "exe": "/usr/bin/python3.10",
        "pgroup": 100,
        "ppid": 1,
        "ticks": 10,
        "uid": 1001,
    }
    workload: dict[tuple[int, int], dict[str, object]] = {}

    for offset in range(29):
        workload[(6000 + offset, 100 + offset)] = {
            "command": f"python3.10 -m pytest {scratch_root}/tests/test_gate_{offset}.py",
            "cwd": str(scratch_root),
            "exe": "/usr/bin/python3.10",
            "pgroup": 700 + offset,
            "ppid": root_identity[0],
            "ticks": 3,
            "uid": 1001,
        }
    for offset in range(22):
        workload[(6100 + offset, 200 + offset)] = {
            "command": f"cc1plus {scratch_root}/oracle/source_{offset}.cpp",
            "cwd": None,
            "exe": "/usr/libexec/gcc/cc1plus",
            "pgroup": 800 + offset,
            "ppid": root_identity[0],
            "ticks": 3,
            "uid": 1001,
        }
    for offset in range(11):
        workload[(6200 + offset, 300 + offset)] = {
            "command": f"git pack-objects {scratch_root}/.git/objects/pack/unit-{offset}",
            "cwd": str(scratch_root / ".git"),
            "exe": "/usr/bin/git",
            "pgroup": 900 + offset,
            "ppid": 1,
            "ticks": 3,
            "uid": 1001,
        }
    for offset in range(7):
        workload[(6300 + offset, 400 + offset)] = {
            "command": f"python3.10 -m pytest -n 2 {tmp_root}/nested-{offset}",
            "cwd": str(tmp_root),
            "exe": "/usr/bin/python3.10",
            "pgroup": 1000 + offset,
            "ppid": root_identity[0],
            "ticks": 3,
            "uid": 1001,
        }
    short_identity = (6999, 999)
    workload[short_identity] = {
        "command": "",
        "cwd": None,
        "exe": None,
        "pgroup": 1099,
        "ppid": root_identity[0],
        "ticks": 4,
        "uid": 1001,
    }
    assert len(workload) == 70

    middle = {root_identity: {**root_process, "ticks": 20}, **workload}
    final = {
        root_identity: {**root_process, "ticks": 30},
        **{
            identity: {**row, "ticks": 7}
            for identity, row in workload.items()
            if identity != short_identity
        },
    }
    samples: list[dict[str, object]] = [
        {
            "hostname": "bnode001", "monotonic_s": 0.0,
            "processes": {root_identity: root_process}, "read_errors": [],
        },
        {
            "hostname": "bnode001", "monotonic_s": 1.0,
            "processes": middle, "read_errors": [],
        },
        {
            "hostname": "bnode001", "monotonic_s": 2.0,
            "processes": final, "read_errors": [],
        },
    ]
    return samples, (scratch_root, tmp_root)


def test_m13_observed_shape_has_70_nonexempt_owned_processes() -> None:
    samples, job_roots = _owned_workload_shape_samples()
    result = study.summarize_isolation_samples(
        samples,
        own_uid=1001,
        exempt_pgroups={100},
        expected_host="bnode001",
        job_roots=job_roots,
    )
    workload_rows = [row for row in result["processes"] if row["exempt"] is False]
    assert workload_rows
    assert len(workload_rows) == 70
    assert all(row["owned"] is True for row in workload_rows)
    assert result["disturbance_candidates"] == []
    assert result["disturbance_rule"] == (
        "unowned uid>=1000 process CPU delta >=2 ticks; ownership is the union "
        "of exempt pgroup, sticky (pid,starttime), owned-parent closure, resolved "
        "job-root cwd/exe, and job-root command prefix"
    )
    assert {
        reason for row in result["processes"] for reason in row["ownership_reasons"]
    } == {
        "1:pgroup",
        "2:sticky-identity",
        "3:owned-parent",
        "4:job-root-cwd-or-exe",
        "5:job-root-command",
    }


def test_m14_owned_parent_is_the_only_gate_for_unreadable_short_process() -> None:
    samples, job_roots = _owned_workload_shape_samples()
    result = study.summarize_isolation_samples(
        samples,
        own_uid=1001,
        exempt_pgroups={100},
        expected_host="bnode001",
        job_roots=job_roots,
    )
    workload_rows = [row for row in result["processes"] if row["exempt"] is False]
    short_row = next(row for row in workload_rows if row["command"] == "")
    other_rows = [row for row in workload_rows if row["command"] != ""]
    assert other_rows
    assert all(row["owned"] is True for row in other_rows)
    assert short_row["created"] is True
    assert short_row["disappeared"] is True
    assert short_row["owned"] is True
    assert short_row["ownership_reasons"] == ["3:owned-parent"]


def test_m15_job_paths_are_the_only_gate_for_daemonized_git_processes() -> None:
    samples, job_roots = _owned_workload_shape_samples()
    result = study.summarize_isolation_samples(
        samples,
        own_uid=1001,
        exempt_pgroups={100},
        expected_host="bnode001",
        job_roots=job_roots,
    )
    workload_rows = [row for row in result["processes"] if row["exempt"] is False]
    daemon_rows = [row for row in workload_rows if row["command"].startswith("git ")]
    other_rows = [row for row in workload_rows if not row["command"].startswith("git ")]
    assert daemon_rows
    assert other_rows
    assert all(row["owned"] is True for row in other_rows)
    assert all(
        row["ownership_reasons"]
        == ["2:sticky-identity", "4:job-root-cwd-or-exe", "5:job-root-command"]
        for row in daemon_rows
    )


def _foreign_and_same_uid_disturbance_result() -> dict[str, object]:
    scratch_root = Path("/scr/unit-acceptance-job")
    identities = {
        "owned": (7000, 1),
        "system": (7001, 2),
        "foreign": (7002, 3),
        "same": (7003, 4),
    }
    rows = {
        identities["owned"]: {
            "command": "driver", "cwd": str(scratch_root), "exe": None,
            "pgroup": 100, "ppid": 1, "ticks": 2, "uid": 1001,
        },
        identities["system"]: {
            "command": "daemon", "cwd": "/", "exe": "/usr/bin/daemon",
            "pgroup": 200, "ppid": 1, "ticks": 2, "uid": 0,
        },
        identities["foreign"]: {
            "command": "foreign", "cwd": "/work/foreign", "exe": "/usr/bin/python",
            "pgroup": 201, "ppid": 1, "ticks": 2, "uid": 1002,
        },
        identities["same"]: {
            "command": "ambient", "cwd": "/work/ambient", "exe": "/usr/bin/python",
            "pgroup": 202, "ppid": 1, "ticks": 2, "uid": 1001,
        },
    }
    samples = [
        {
            "hostname": "bnode001", "monotonic_s": 0.0,
            "processes": rows, "read_errors": [],
        },
        {
            "hostname": "bnode001", "monotonic_s": 1.0,
            "processes": {
                identity: {**row, "ticks": 8} for identity, row in rows.items()
            },
            "read_errors": [],
        },
    ]
    return study.summarize_isolation_samples(
        samples,
        own_uid=1001,
        exempt_pgroups={100},
        expected_host="bnode001",
        job_roots=(scratch_root,),
    )


def test_m16_foreign_uid_disturbance_keeps_owned_and_system_positives() -> None:
    result = _foreign_and_same_uid_disturbance_result()
    candidates = {
        row["pid"]: row["uid_relation"] for row in result["disturbance_candidates"]
    }
    assert candidates == {7002: "other", 7003: "same"}
    accepted = {
        row["pid"]: row for row in result["processes"]
        if row["pid"] in {7000, 7001}
    }
    assert accepted
    assert accepted[7000]["owned"] is True
    assert accepted[7001]["uid"] == 0


def test_m17_infinite_cpu_threshold_would_lose_both_fixed_negatives() -> None:
    result = _foreign_and_same_uid_disturbance_result()
    candidates = [
        (row["pid"], row["cpu_ticks_delta"])
        for row in result["disturbance_candidates"]
    ]
    assert candidates
    assert candidates == [(7002, 6), (7003, 6)]
    accepted_pids = {
        row["pid"] for row in result["processes"] if row["pid"] in {7000, 7001}
    }
    assert accepted_pids == {7000, 7001}


def test_internal_shard_argv_rejects_any_extra_n_option(tmp_path: Path) -> None:
    clone = tmp_path / "clone"
    session = tmp_path / "session"
    argv = [
        "python3.10", str(clone / "tools/run_tests.py"),
        f"--izanagi-acceptance-shard-session={session}",
        "--izanagi-acceptance-shard-count=2",
        "--izanagi-acceptance-shard-index=0",
        "-n", "32",
    ]
    with pytest.raises(study.ContractError, match="pinned empty-argv"):
        study.validate_measurement_argv(
            argv, clone=clone, session=session, shard_index=0,
            python_command="python3.10",
        )


def test_run_environment_requires_driver_pythonuserbase(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    config = _config(tmp_path)
    monkeypatch.delenv("PYTHONUSERBASE")
    with pytest.raises(
        study.ContractError,
        match="driver PYTHONUSERBASE must be a nonempty absolute path",
    ):
        study._run_environment(
            config, global_run_index=0, arm=16,
            root=config.scratch_root / "run-environments",
        )


def test_run_environment_exact_task_projection_and_only_tmp_uses_short_root(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    config = _config(tmp_path)
    base = {
        "IZANAGI_TASK_RUN_ID": "base-id",
        "IZANAGI_TASK_RUNS_ROOT": "/base/root",
        "IZANAGI_TASK_RUN_SIDECAR": "/base/sidecar",
        "IZANAGI_TASK_RUN_AUTO_RECORD": "1",
        "BASE_ONLY_SENTINEL": "keep",
    }
    task_run_keys = {
        "IZANAGI_TASK_RUN_ID",
        "IZANAGI_TASK_RUNS_ROOT",
        "IZANAGI_TASK_RUN_SIDECAR",
        "IZANAGI_TASK_RUN_AUTO_RECORD",
    }
    assert task_run_keys <= set(base)
    assert base["BASE_ONLY_SENTINEL"] == "keep"
    monkeypatch.setenv("AMBIENT_ONLY_SENTINEL", "reject")
    assert os.environ["AMBIENT_ONLY_SENTINEL"] == "reject"
    monkeypatch.setattr(study, "_base_env", lambda: dict(base))

    env = study._run_environment(
        config, global_run_index=7, arm=32,
        root=config.scratch_root / "run-environments",
    )
    try:
        projection_keys = (
            "AMBIENT_ONLY_SENTINEL",
            "BASE_ONLY_SENTINEL",
            "IZANAGI_TASK_RUN_AUTO_RECORD",
            "IZANAGI_TASK_RUN_ID",
            "IZANAGI_TASK_RUNS_ROOT",
            "IZANAGI_TASK_RUN_SIDECAR",
        )
        assert {key: env.get(key) for key in projection_keys} == {
            "AMBIENT_ONLY_SENTINEL": None,
            "BASE_ONLY_SENTINEL": "keep",
            "IZANAGI_TASK_RUN_AUTO_RECORD": "0",
            "IZANAGI_TASK_RUN_ID": None,
            "IZANAGI_TASK_RUNS_ROOT": None,
            "IZANAGI_TASK_RUN_SIDECAR": None,
        }
        tmp_tree = Path(env["TMPDIR"])
        assert tmp_tree.name == "run-007"
        assert tmp_tree.parent.parent == Path("/tmp")
        assert re.fullmatch(r"izn-[0-9a-f]{12}", tmp_tree.parent.name)
        for key in (
            "HOME", "XDG_CACHE_HOME", "XDG_CONFIG_HOME", "XDG_DATA_HOME",
            "XDG_STATE_HOME",
        ):
            assert Path(env[key]).is_relative_to(config.scratch_root)
    finally:
        study._remove_tmp_tree(
            Path(env["TMPDIR"]), global_run_index=7, purpose="measurement"
        )


def test_mh5_driver_calls_production_task_run_helper_once(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    config = _config(tmp_path)
    base = {
        "BASE_ONLY_SENTINEL": "keep",
        "IZANAGI_TASK_RUN_ID": "remove",
    }
    calls: list[object] = []

    def helper_spy(supplied: object) -> dict[str, str]:
        calls.append(supplied)
        assert supplied == base
        return {
            "BASE_ONLY_SENTINEL": "keep",
            "IZANAGI_TASK_RUN_AUTO_RECORD": "0",
        }

    monkeypatch.setattr(study, "_base_env", lambda: dict(base))
    monkeypatch.setattr(
        study.production_runner, "task_run_child_environment", helper_spy
    )
    env = study._run_environment(
        config, global_run_index=8, arm=48,
        root=config.scratch_root / "run-environments",
    )
    try:
        assert calls == [base]
        assert env["BASE_ONLY_SENTINEL"] == "keep"
        assert env["IZANAGI_TASK_RUN_AUTO_RECORD"] == "0"
    finally:
        study._remove_tmp_tree(
            Path(env["TMPDIR"]), global_run_index=8, purpose="measurement"
        )


def test_run_environments_isolate_home_and_keep_one_pythonuserbase(
    tmp_path: Path,
) -> None:
    config = _config(tmp_path)
    root = config.scratch_root / "run-environments"
    first = study._run_environment(
        config, global_run_index=0, arm=16, root=root
    )
    second = study._run_environment(
        config, global_run_index=1, arm=48, root=root
    )
    try:
        assert first["HOME"] != second["HOME"]
        assert first["TMPDIR"] != second["TMPDIR"]
        assert first["PYTHONUSERBASE"] == second["PYTHONUSERBASE"]
        assert first["PYTHONUSERBASE"] == os.environ["PYTHONUSERBASE"]
        assert first[study.THIRDPARTY_CACHE_ENV] == os.environ[study.THIRDPARTY_CACHE_ENV]
        assert second[study.THIRDPARTY_CACHE_ENV] == os.environ[study.THIRDPARTY_CACHE_ENV]
    finally:
        study._remove_tmp_tree(
            Path(first["TMPDIR"]), global_run_index=0, purpose="measurement"
        )
        study._remove_tmp_tree(
            Path(second["TMPDIR"]), global_run_index=1, purpose="measurement"
        )


def test_m6_prepare_tmp_tree_has_one_exact_root_gate(tmp_path: Path) -> None:
    config = _config(tmp_path)
    path = study._prepare_tmp_tree(config, global_run_index=9)
    assert path.parent.parent == Path("/tmp")
    study._remove_tmp_tree(path, global_run_index=9, purpose="measurement")


def test_m7_remove_tmp_tree_postcondition_is_the_single_noop_gate(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    positive = tmp_path / "positive"
    positive.mkdir()
    (positive / "payload").write_bytes(b"positive")
    positive_evidence = study._remove_tmp_tree(
        positive, global_run_index=0, purpose="measurement"
    )
    assert positive_evidence["removed"] is True
    assert not positive.exists()

    negative = tmp_path / "negative"
    negative.mkdir()
    (negative / "payload").write_bytes(b"negative")
    monkeypatch.setattr(study.shutil, "rmtree", lambda _path: None)
    with pytest.raises(study.ContractError, match="still exists after cleanup"):
        study._remove_tmp_tree(
            negative, global_run_index=1, purpose="measurement"
        )


def test_process_cleanup_rejects_residual_group_member() -> None:
    with pytest.raises(study.ContractError, match="fully reaped"):
        study.validate_process_cleanup(_cleanup(residual=[1234]))


def test_analysis_rejects_warmup_leaking_into_smoke_estimand() -> None:
    runs = []
    for phase, included in (("measurement", True), ("warmup", False)):
        for arm in (16, 32, 48):
            for shard in (0, 1):
                runs.append({
                    "analysis_block_index": 0,
                    "analysis_included": included,
                    "arm": arm,
                    "junit": {
                        "real_repo_exclusive_chain_s": 0.2,
                        "serial_work_sum_s": 1.0,
                    },
                    "phase": phase,
                    "shard_index": shard,
                    "wall_s": 2.0,
                })
    outcomes, contrasts = study._derive_analysis(runs, mode="smoke")
    assert len(outcomes) == 3
    assert len(contrasts) == 2
    for run in runs:
        run["analysis_included"] = True
    with pytest.raises(study.ContractError, match="measured run count"):
        study._derive_analysis(runs, mode="smoke")


def test_receipt_schema_rejects_missing_excluded_estimand_and_unknown_field(
    tmp_path: Path,
) -> None:
    receipt = _failed_schema_fixture(tmp_path)
    study.validate_receipt(receipt, expected_mode="smoke", require_complete=False)
    missing = copy.deepcopy(receipt)
    missing.pop("excluded_estimands")
    with pytest.raises(study.ContractError, match="closed map"):
        study.validate_receipt(missing, expected_mode="smoke", require_complete=False)
    unknown = copy.deepcopy(receipt)
    unknown["unexpected"] = True
    with pytest.raises(study.ContractError, match="unknown"):
        study.validate_receipt(unknown, expected_mode="smoke", require_complete=False)


def test_receipt_schema_rejects_changed_excluded_estimand_value(
    tmp_path: Path,
) -> None:
    valid = _failed_schema_fixture(tmp_path)
    study.validate_receipt(valid, expected_mode="smoke", require_complete=False)

    changed = copy.deepcopy(valid)
    changed["excluded_estimands"][0]["statement_ja"] = "別の除外項"
    with pytest.raises(study.ContractError) as exc_info:
        study.validate_receipt(changed, expected_mode="smoke", require_complete=False)
    assert str(exc_info.value) == (
        "receipt excluded_estimands differs from the fixed exclusion"
    )


def test_receipt_pins_three_known_nonequivalences_and_estimand_scope(
    tmp_path: Path,
) -> None:
    """M12-C uses the builder literal; M12-V uses each changed-field rejection."""
    valid = _failed_schema_fixture(tmp_path)
    expected_nonequivalences = [
        {
            "id": "home-xdg-cold-isolated",
            "statement": (
                "HOME and XDG roots are cold-isolated per run; production uses "
                "real HOME and ambient XDG"
            ),
        },
        {
            "id": "clone-on-scratch-filesystem",
            "statement": (
                "the study clone is on /scr; production reads the canonical "
                "repository on /work"
            ),
        },
        {
            "id": "serial-shards-on-one-node",
            "statement": (
                "shards run serially as 0 then 1 on one node without "
                "counterbalancing; production submits parallel PBS jobs"
            ),
        },
    ]
    assert valid["design"]["known_nonequivalences"] == expected_nonequivalences
    assert valid["design"]["internal_comparison_scope"] == (
        "The known nonequivalences do not invalidate the within-study paired "
        "comparison that changes only worker count."
    )
    assert valid["design"]["absolute_wall_extrapolation"] == (
        "The study does not justify extrapolation to production absolute wall time."
    )
    study.validate_receipt(valid, expected_mode="smoke", require_complete=False)

    for removed_index in range(3):
        changed = copy.deepcopy(valid)
        changed["design"]["known_nonequivalences"].pop(removed_index)
        with pytest.raises(
            study.ContractError,
            match="known nonequivalences differ from the fixed design",
        ):
            study.validate_receipt(
                changed, expected_mode="smoke", require_complete=False
            )

    for field in ("internal_comparison_scope", "absolute_wall_extrapolation"):
        changed = copy.deepcopy(valid)
        changed["design"][field] = "changed scope"
        with pytest.raises(study.ContractError, match="estimand scope"):
            study.validate_receipt(
                changed, expected_mode="smoke", require_complete=False
            )

    changed_arm_scope = copy.deepcopy(valid)
    changed_arm_scope["design"]["arm_timeout_scope"] = "excludes cleanup"
    with pytest.raises(study.ContractError, match="arm timeout scope"):
        study.validate_receipt(
            changed_arm_scope, expected_mode="smoke", require_complete=False
        )

    changed_capacity_rule = copy.deepcopy(valid)
    changed_capacity_rule["cleanup"]["tmp_capacity_rule"] = "changed rule"
    with pytest.raises(study.ContractError, match="TMP capacity rule"):
        study.validate_receipt(
            changed_capacity_rule, expected_mode="smoke", require_complete=False
        )

    changed_peak_rule = copy.deepcopy(valid)
    changed_peak_rule["cleanup"]["tmp_peak_capacity_rule"] = "changed peak rule"
    with pytest.raises(study.ContractError, match="TMP peak capacity rule"):
        study.validate_receipt(
            changed_peak_rule, expected_mode="smoke", require_complete=False
        )


def test_v2_receipt_rejects_v1_schema_identifier(tmp_path: Path) -> None:
    valid = _failed_schema_fixture(tmp_path)
    assert valid["schema_version"] == "izanagi-acceptance-nproc-study/v2"
    changed = copy.deepcopy(valid)
    changed["schema_version"] = "izanagi-acceptance-nproc-study/v1"
    with pytest.raises(study.ContractError, match="schema or mode mismatch"):
        study.validate_receipt(changed, expected_mode="smoke", require_complete=False)


def test_job_failure_schema_is_closed() -> None:
    receipt = {
        "message": "failed",
        "mode": "smoke",
        "pbs_jobid": "0:1.nqsv",
        "recorded_epoch_s": 1,
        "returncode": 2,
        "schema_version": study.JOB_FAILURE_SCHEMA_VERSION,
        "stage": "bootstrap",
    }
    study.validate_job_failure_receipt(receipt)
    receipt["unknown"] = True
    with pytest.raises(study.ContractError, match="unknown"):
        study.validate_job_failure_receipt(receipt)


def test_fake_executor_is_the_only_process_surface_and_smoke_receipt_is_complete(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    _poison_process_creation(monkeypatch)
    monkeypatch.setattr(study, "_tmp_free_bytes", lambda _path: 1 << 50)
    config = _config(tmp_path)
    host = "bnode999"
    monkeypatch.setattr(study.socket, "gethostname", lambda: host)
    nodefile = tmp_path / "pbs-nodefile"
    nodefile.write_text(host + "\n", encoding="utf-8")
    monkeypatch.setenv("PBS_JOBID", "0:123.nqsv")
    monkeypatch.setenv("PBS_NODEFILE", str(nodefile))
    executor = FakeExecutor(tmp_path, host)
    rc, receipt = study.run_study(config, executor)
    assert rc == 0
    assert receipt["status"] == "complete"
    assert len(receipt["runs"]) == 6
    assert all(run["analysis_included"] for run in receipt["runs"])
    assert receipt["design"]["primary_contrast"] == {"arm": 32, "reference_arm": 48}
    assert {row["priority"] for row in receipt["contrasts"]} == {"primary", "secondary"}
    expected_submodule_order = [path for _head, path, _parent, _relative in _SUBMODULE_ROWS]
    assert executor.materialized_order == expected_submodule_order
    assert executor.registered_order == expected_submodule_order
    assert executor.absorbed_order == expected_submodule_order
    assert executor.pre_init_statuses == [
        f"-{_HEAD} external/ccbench\n",
        (
            f" {_HEAD} external/ccbench\n"
            f"-{_SHIRAKAMI_HEAD} external/ccbench/third_party/shirakami\n"
        ),
        (
            f" {_HEAD} external/ccbench\n"
            f" {_SHIRAKAMI_HEAD} external/ccbench/third_party/shirakami\n"
            f"-{_GOOGLETEST_HEAD} "
            "external/ccbench/third_party/shirakami/third_party/googletest\n"
        ),
    ]
    assert executor.configured_urls == {
        path: str(config.repo_root / path) for path in expected_submodule_order
    }
    assert executor.clone_root is not None
    assert executor.absorbed_gitdirs["external/ccbench"] == (
        executor.clone_root / ".git/modules/external/ccbench"
    )
    for path in expected_submodule_order:
        marker = executor.clone_root / path / ".git"
        assert marker.is_file()
        assert not marker.is_symlink()
        assert executor.absorbed_gitdirs[path].is_dir()
    assert (
        (executor.clone_root / ".gitmodules").stat().st_mode
        == (config.repo_root / ".gitmodules").stat().st_mode
    )
    purposes = [request.purpose for request in executor.requests]
    for index, path in enumerate(expected_submodule_order):
        assert purposes.index(f"materialize-submodule:{path}") < purposes.index(
            f"register-submodule:{path}"
        ) < purposes.index(f"override-submodule-url:{path}") < purposes.index(
            f"absorb-submodule-gitdir:{path}"
        )
        if index + 1 < len(expected_submodule_order):
            assert purposes.index(f"absorb-submodule-gitdir:{path}") < purposes.index(
                f"materialize-submodule:{expected_submodule_order[index + 1]}"
            )
    measurement_requests = [
        request for request in executor.requests if request.purpose.startswith("measurement:")
    ]
    assert len(measurement_requests) == 6
    import_request = next(
        request for request in executor.requests
        if request.purpose == "validate-measurement-imports"
    )
    assert import_request.argv == ("python3.10", "-c", "import pytest, xdist")
    assert purposes.index("validate-measurement-imports") < purposes.index("measurement:0")
    assert import_request.env["PYTHONUSERBASE"] == os.environ["PYTHONUSERBASE"]
    assert import_request.env[study.THIRDPARTY_CACHE_ENV] == os.environ[
        study.THIRDPARTY_CACHE_ENV
    ]
    assert not Path(import_request.env["TMPDIR"]).exists()
    assert len({request.env["HOME"] for request in measurement_requests}) == 6
    assert {
        request.env["PYTHONUSERBASE"] for request in measurement_requests
    } == {os.environ["PYTHONUSERBASE"]}
    for request in measurement_requests:
        assert "-n" not in request.argv
        assert request.isolation_job_roots == (
            config.scratch_root.resolve(),
            Path(request.env["TMPDIR"]).parent,
        )
        assert request.env["IZANAGI_TEST_NPROC"] in {"16", "32", "48"}
        assert request.env[study.THIRDPARTY_CACHE_ENV] == os.environ[
            study.THIRDPARTY_CACHE_ENV
        ]
        assert request.env["HOME"].startswith(str(config.scratch_root))
        assert Path(request.env["TMPDIR"]).parent.parent == Path("/tmp")
        assert not Path(request.env["TMPDIR"]).exists()
        assert {
            key: request.env.get(key)
            for key in (
                "IZANAGI_TASK_RUN_AUTO_RECORD",
                "IZANAGI_TASK_RUN_ID",
                "IZANAGI_TASK_RUNS_ROOT",
                "IZANAGI_TASK_RUN_SIDECAR",
            )
        } == {
            "IZANAGI_TASK_RUN_AUTO_RECORD": "0",
            "IZANAGI_TASK_RUN_ID": None,
            "IZANAGI_TASK_RUNS_ROOT": None,
            "IZANAGI_TASK_RUN_SIDECAR": None,
        }
        assert not any(key.startswith(("CCACHE_", "SCCACHE_")) for key in request.env)
    cleanups = receipt["cleanup"]["tmp_tree_cleanups"]
    assert [row["global_run_index"] for row in cleanups] == [-1, 0, 1, 2, 3, 4, 5]
    assert [row["purpose"] for row in cleanups] == [
        "setup-import-probe", "measurement", "measurement", "measurement",
        "measurement", "measurement", "measurement",
    ]
    assert all(row["removed"] is True for row in cleanups)
    assert all(row["usage_bytes_before_cleanup"] > 0 for row in cleanups)
    capacity_checks = receipt["cleanup"]["tmp_capacity_checks"]
    assert receipt["cleanup"]["tmp_capacity_rule"] == (
        "observed maximum times observed max/min safety factor plus observed "
        "mean reserve"
    )
    assert [row["global_run_index"] for row in capacity_checks] == [1, 2, 3, 4, 5]
    assert all(row["passed"] is True for row in capacity_checks)
    peak_observations = receipt["cleanup"]["tmp_peak_capacity_observations"]
    assert peak_observations
    assert [row["global_run_index"] for row in peak_observations] == [0, 1, 2, 3, 4, 5]
    assert all(row["sample_count"] == 2 for row in peak_observations)
    assert all(row["passed"] is True for row in peak_observations)
    assert all(run["cleanup_wall_s"] >= 0 for run in receipt["runs"])
    assert all(
        run["budget_wall_s"] == run["wall_s"] + run["cleanup_wall_s"]
        for run in receipt["runs"]
    )
    study.validate_receipt(receipt, expected_mode="smoke", require_complete=True)
    for run in receipt["runs"]:
        shard_stage = (
            f"block-{run['global_block_index']}-arm-{run['arm']}"
            f"-shard-{run['shard_index']}"
        )
        assert purposes.index(f"qstat:{shard_stage}") < purposes.index(
            f"run-{run['global_run_index']}-before:head"
        )

    missing_shard_gate = copy.deepcopy(receipt)
    missing_shard_gate["budget"]["budget_checks"] = [
        check for check in missing_shard_gate["budget"]["budget_checks"]
        if check["stage"] != "block-0-arm-16-shard-0"
    ]
    with pytest.raises(study.ContractError, match="stage-start remaining-walltime"):
        study.validate_receipt(
            missing_shard_gate, expected_mode="smoke", require_complete=True
        )

    different_set = copy.deepcopy(receipt)
    different_set["runs"][2]["junit"]["testcase_identity_set_sha256"] = study._sha256(
        b"different-testcase-set"
    )
    with pytest.raises(study.ContractError, match="JUnit testcase identity set differs"):
        study.validate_receipt(
            different_set, expected_mode="smoke", require_complete=True
        )

    wrong_manifest = copy.deepcopy(receipt)
    wrong_manifest["runs"][0]["order_index"] = 2
    with pytest.raises(study.ContractError, match="run manifest differs from schedule"):
        study.validate_receipt(
            wrong_manifest, expected_mode="smoke", require_complete=True
        )

    split_session = copy.deepcopy(receipt)
    split_root = str(config.scratch_root / "different-session")
    split_session["runs"][1]["session_root"] = split_root
    split_session["runs"][1]["argv"][2] = (
        f"--izanagi-acceptance-shard-session={split_root}"
    )
    with pytest.raises(study.ContractError, match="different session_root"):
        study.validate_receipt(
            split_session, expected_mode="smoke", require_complete=True
        )

    inconsistent_capacity = copy.deepcopy(receipt)
    inconsistent_capacity["cleanup"]["tmp_capacity_checks"][0]["passed"] = False
    with pytest.raises(study.ContractError, match="TMP capacity observation"):
        study.validate_receipt(
            inconsistent_capacity, expected_mode="smoke", require_complete=True
        )

    failed_capacity = copy.deepcopy(receipt)
    failed_capacity_row = failed_capacity["cleanup"]["tmp_capacity_checks"][0]
    failed_capacity_row["free_bytes"] = 0
    failed_capacity_row["passed"] = False
    with pytest.raises(study.ContractError, match="failed TMP capacity observation"):
        study.validate_receipt(
            failed_capacity, expected_mode="smoke", require_complete=True
        )


def test_tmp_capacity_gate_rejects_before_next_run_and_keeps_first_cleanup(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    _poison_process_creation(monkeypatch)
    config = _config(tmp_path)
    host = "bnode999"
    monkeypatch.setattr(study.socket, "gethostname", lambda: host)
    nodefile = tmp_path / "pbs-nodefile"
    nodefile.write_text(host + "\n", encoding="utf-8")
    monkeypatch.setenv("PBS_JOBID", "0:123.nqsv")
    monkeypatch.setenv("PBS_NODEFILE", str(nodefile))
    monkeypatch.setattr(study, "_tmp_free_bytes", lambda _path: 0)
    executor = FakeExecutor(tmp_path, host)

    rc, receipt = study.run_study(config, executor)

    assert rc == 1
    assert receipt["status"] == "failed"
    assert receipt["failure"]["type"] == "ContractError"
    assert receipt["failure"]["message"].startswith(
        "insufficient /tmp capacity for the next run: free=0 required="
    )
    measurements = [
        request for request in executor.requests
        if request.purpose.startswith("measurement:")
    ]
    assert len(measurements) == 1
    assert not Path(measurements[0].env["TMPDIR"]).exists()
    measured_usage = receipt["cleanup"]["tmp_tree_cleanups"][1][
        "usage_bytes_before_cleanup"
    ]
    assert receipt["cleanup"]["tmp_tree_cleanups"] == [
        {
            "global_run_index": -1,
            "purpose": "setup-import-probe",
            "removed": True,
            "usage_bytes_before_cleanup": receipt["cleanup"]["tmp_tree_cleanups"][0][
                "usage_bytes_before_cleanup"
            ],
        },
        {
            "global_run_index": 0,
            "purpose": "measurement",
            "removed": True,
            "usage_bytes_before_cleanup": measured_usage,
        },
    ]
    assert receipt["cleanup"]["tmp_capacity_checks"] == [
        {
            "free_bytes": 0,
            "global_run_index": 1,
            "observed_max_bytes": measured_usage,
            "observed_mean_reserve_bytes": measured_usage,
            "observed_min_bytes": measured_usage,
            "observed_run_count": 1,
            "passed": False,
            "required_bytes": measured_usage + measured_usage,
            "safety_factor_denominator_bytes": measured_usage,
            "safety_factor_numerator_bytes": measured_usage,
            "scaled_observed_max_bytes": measured_usage,
        }
    ]


def test_c1_first_run_capacity_learns_peak_and_keeps_passing_positive() -> None:
    spec = study.TmpCapacitySpec(
        path=Path("/tmp/unit-capacity"),
        global_run_index=0,
        prior_observed_max_consumption_bytes=0,
        receipt_reserve_bytes=100,
    )
    positive_samples = [
        {"free_bytes": 1000, "monotonic_s": 0.0, "read_errors": []},
        {"free_bytes": 600, "monotonic_s": 1.0, "read_errors": []},
    ]
    negative_samples = [
        {"free_bytes": 1000, "monotonic_s": 0.0, "read_errors": []},
        {"free_bytes": 400, "monotonic_s": 1.0, "read_errors": []},
    ]
    assert positive_samples
    positive = study.summarize_tmp_capacity_samples(positive_samples, spec=spec)
    negative = study.summarize_tmp_capacity_samples(negative_samples, spec=spec)
    assert {
        key: positive[key]
        for key in (
            "free_bytes", "minimum_free_bytes", "observed_consumption_bytes",
            "passed", "receipt_reserve_bytes", "required_bytes", "sample_count",
            "start_free_bytes",
        )
    } == {
        "free_bytes": 600,
        "minimum_free_bytes": 600,
        "observed_consumption_bytes": 400,
        "passed": True,
        "receipt_reserve_bytes": 100,
        "required_bytes": 400,
        "sample_count": 2,
        "start_free_bytes": 1000,
    }
    assert {
        key: negative[key]
        for key in (
            "free_bytes", "minimum_free_bytes", "observed_consumption_bytes",
            "passed", "receipt_reserve_bytes", "required_bytes", "sample_count",
            "start_free_bytes",
        )
    } == {
        "free_bytes": 400,
        "minimum_free_bytes": 400,
        "observed_consumption_bytes": 600,
        "passed": False,
        "receipt_reserve_bytes": 100,
        "required_bytes": 600,
        "sample_count": 2,
        "start_free_bytes": 1000,
    }


def test_c1_first_measurement_rejects_its_own_live_capacity_drop(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    _poison_process_creation(monkeypatch)
    config = _config(tmp_path)
    host = "bnode991"
    monkeypatch.setattr(study.socket, "gethostname", lambda: host)
    nodefile = tmp_path / "pbs-nodefile"
    nodefile.write_text(host + "\n", encoding="utf-8")
    monkeypatch.setenv("PBS_JOBID", "0:134.nqsv")
    monkeypatch.setenv("PBS_NODEFILE", str(nodefile))
    free_samples = iter((1 << 20, 1))
    monkeypatch.setattr(
        study, "_sample_tmp_free_bytes", lambda _path: next(free_samples)
    )
    executor = FakeExecutor(tmp_path, host)

    rc, receipt = study.run_study(config, executor)

    assert rc == 1
    assert executor.measurement_seen is True
    assert receipt["runs"] == []
    assert receipt["cleanup"]["tmp_capacity_checks"] == []
    observations = receipt["cleanup"]["tmp_peak_capacity_observations"]
    assert observations
    assert len(observations) == 1
    observation = observations[0]
    assert observation["global_run_index"] == 0
    assert observation["minimum_free_bytes"] == 1
    assert observation["passed"] is False
    assert observation["passed"] == (
        observation["free_bytes"] >= observation["required_bytes"]
    )
    assert receipt["failure"]["message"].startswith(
        "insufficient /tmp capacity during run: free=1 required="
    )
    assert study._receipt_reserve_bytes(receipt) == len(
        study._receipt_json_bytes(receipt)
    )


def test_setup_import_probe_failure_stops_before_measurement(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    _poison_process_creation(monkeypatch)
    config = _config(tmp_path)
    host = "bnode996"
    monkeypatch.setattr(study.socket, "gethostname", lambda: host)
    nodefile = tmp_path / "pbs-nodefile"
    nodefile.write_text(host + "\n", encoding="utf-8")
    monkeypatch.setenv("PBS_JOBID", "0:129.nqsv")
    monkeypatch.setenv("PBS_NODEFILE", str(nodefile))
    executor = FakeExecutor(tmp_path, host, imports_available=False)

    rc, receipt = study.run_study(config, executor)

    assert rc == 1
    assert receipt["failure"]["stage"] == "setup-import-check"
    assert receipt["failure"]["type"] == "ContractError"
    assert "cannot import pytest and xdist" in receipt["failure"]["message"]
    assert "rc=86" in receipt["failure"]["message"]
    assert "fake pytest/xdist import failure" in receipt["failure"]["message"]
    assert executor.measurement_seen is False


def test_setup_import_probe_success_reaches_measurement(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    _poison_process_creation(monkeypatch)
    config = _config(tmp_path)
    host = "bnode995"
    monkeypatch.setattr(study.socket, "gethostname", lambda: host)
    nodefile = tmp_path / "pbs-nodefile"
    nodefile.write_text(host + "\n", encoding="utf-8")
    monkeypatch.setenv("PBS_JOBID", "0:130.nqsv")
    monkeypatch.setenv("PBS_NODEFILE", str(nodefile))
    executor = FakeExecutor(tmp_path, host, imports_available=True)

    rc, receipt = study.run_study(config, executor)

    assert rc == 0
    assert receipt["status"] == "complete"
    assert executor.measurement_seen is True


def test_missing_junit_diagnostic_includes_child_returncode(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    _poison_process_creation(monkeypatch)
    config = _config(tmp_path)
    host = "bnode994"
    monkeypatch.setattr(study.socket, "gethostname", lambda: host)
    nodefile = tmp_path / "pbs-nodefile"
    nodefile.write_text(host + "\n", encoding="utf-8")
    monkeypatch.setenv("PBS_JOBID", "0:131.nqsv")
    monkeypatch.setenv("PBS_NODEFILE", str(nodefile))
    executor = FakeExecutor(
        tmp_path, host, write_junit=False, measurement_returncode=86,
    )

    rc, receipt = study.run_study(config, executor)

    assert rc == 1
    assert receipt["failure"]["type"] == "ContractError"
    assert receipt["failure"]["stage"].endswith("shard-0")
    assert receipt["failure"]["message"].endswith("child_returncode=86")


def test_materialize_without_registration_stops_setup_with_contract_error(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    _poison_process_creation(monkeypatch)
    config = _config(tmp_path)
    host = "bnode997"
    monkeypatch.setattr(study.socket, "gethostname", lambda: host)
    nodefile = tmp_path / "pbs-nodefile"
    nodefile.write_text(host + "\n", encoding="utf-8")
    monkeypatch.setenv("PBS_JOBID", "0:128.nqsv")
    monkeypatch.setenv("PBS_NODEFILE", str(nodefile))
    executor = FakeExecutor(tmp_path, host, honor_submodule_init=False)

    rc, receipt = study.run_study(config, executor)

    assert rc == 1
    assert receipt["status"] == "failed"
    assert receipt["failure"] == {
        "message": "all recursive submodules must be initialized at their gitlinks",
        "stage": "setup",
        "type": "ContractError",
    }
    assert executor.materialized_order == [
        path for _head, path, _parent, _relative in _SUBMODULE_ROWS
    ]
    assert executor.registered_order == []
    assert executor.measurement_seen is False


@pytest.mark.parametrize(
    ("executor_options", "message"),
    (
        (
            {"honor_absorbgitdirs": False},
            "initialized submodule git marker is not a non-symlink regular file",
        ),
        (
            {"missing_absorbed_gitdir": _SUBMODULE_ROWS[-1][1]},
            "absorbed submodule gitdir",
        ),
        (
            {"clone_gitmodules_mode": 0o600},
            "st_mode mismatch .gitmodules: 0o100600 != 0o100644",
        ),
    ),
)
def test_setup_equivalence_gate_rejects_topology_or_mode_before_measurement(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    executor_options: dict[str, object],
    message: str,
) -> None:
    _poison_process_creation(monkeypatch)
    config = _config(tmp_path)
    host = "bnode993"
    monkeypatch.setattr(study.socket, "gethostname", lambda: host)
    nodefile = tmp_path / "pbs-nodefile"
    nodefile.write_text(host + "\n", encoding="utf-8")
    monkeypatch.setenv("PBS_JOBID", "0:132.nqsv")
    monkeypatch.setenv("PBS_NODEFILE", str(nodefile))
    executor = FakeExecutor(tmp_path, host, **executor_options)

    rc, receipt = study.run_study(config, executor)

    assert rc == 1
    assert receipt["failure"]["stage"] == "setup-equivalence-gate"
    assert receipt["failure"]["type"] == "ContractError"
    assert message in receipt["failure"]["message"]
    assert executor.measurement_seen is False


def test_setup_equivalence_gate_requires_existing_thirdparty_cache(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    _poison_process_creation(monkeypatch)
    config = _config(tmp_path)
    host = "bnode992"
    monkeypatch.setattr(study.socket, "gethostname", lambda: host)
    nodefile = tmp_path / "pbs-nodefile"
    nodefile.write_text(host + "\n", encoding="utf-8")
    monkeypatch.setenv("PBS_JOBID", "0:133.nqsv")
    monkeypatch.setenv("PBS_NODEFILE", str(nodefile))
    monkeypatch.setenv(
        study.THIRDPARTY_CACHE_ENV, str(tmp_path / "missing-thirdparty-cache")
    )
    executor = FakeExecutor(tmp_path, host)

    rc, receipt = study.run_study(config, executor)

    assert rc == 1
    assert receipt["failure"]["stage"] == "setup-equivalence-gate"
    assert receipt["failure"]["type"] == "ContractError"
    assert "does not identify an existing directory" in receipt["failure"]["message"]
    assert executor.measurement_seen is False


def test_thirdparty_cache_environment_is_required(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv(study.THIRDPARTY_CACHE_ENV)
    with pytest.raises(study.ContractError, match="is required"):
        study._thirdparty_cache_root()


def test_full_timeout_is_hash_bound_to_complete_smoke_and_fixed_derivation(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    _poison_process_creation(monkeypatch)
    host = "bnode998"
    monkeypatch.setattr(study.socket, "gethostname", lambda: host)

    smoke_root = tmp_path / "smoke"
    smoke_config = _config(smoke_root)
    smoke_nodefile = smoke_config.scratch_root / "pbs-nodefile"
    smoke_nodefile.write_text(host + "\n", encoding="utf-8")
    monkeypatch.setenv("PBS_JOBID", "0:126.nqsv")
    monkeypatch.setenv("PBS_NODEFILE", str(smoke_nodefile))
    smoke_rc, smoke_receipt = study.run_study(
        smoke_config, FakeExecutor(smoke_root, host)
    )
    assert smoke_rc == 0
    raw_smoke = (
        json.dumps(smoke_receipt, ensure_ascii=True, sort_keys=True) + "\n"
    ).encode()
    smoke_path = tmp_path / "successful-smoke.json"
    smoke_path.write_bytes(raw_smoke)

    derived, calibration = study._read_smoke_calibration(smoke_path)
    assert derived == {16: 93, 32: 93, 48: 93}
    assert calibration["smoke_receipt_sha256"] == study._sha256(raw_smoke)
    assert calibration["derivation_rule"] == study.FULL_TIMEOUT_RULE

    failed_smoke = copy.deepcopy(smoke_receipt)
    failed_smoke["status"] = "failed"
    failed_smoke["failure"] = {
        "message": "forced failure", "stage": "unit", "type": "ContractError",
    }
    failed_path = tmp_path / "failed-smoke.json"
    failed_path.write_text(json.dumps(failed_smoke), encoding="utf-8")
    with pytest.raises(study.ContractError, match="completed receipt was required"):
        study._read_smoke_calibration(failed_path)

    full_root = tmp_path / "full"
    full_base = _config(full_root)
    full_config = replace(
        full_base, mode="full", arm_timeout_s=derived,
        calibration_receipt=smoke_path,
    )
    full_nodefile = full_config.scratch_root / "pbs-nodefile"
    full_nodefile.write_text(host + "\n", encoding="utf-8")
    monkeypatch.setenv("PBS_JOBID", "0:127.nqsv")
    monkeypatch.setenv("PBS_NODEFILE", str(full_nodefile))
    full_rc, full_receipt = study.run_study(
        full_config, FakeExecutor(full_root, host)
    )
    assert full_rc == 0
    assert full_receipt["budget"]["timeout_calibration"] == calibration
    study.validate_receipt(full_receipt, expected_mode="full", require_complete=True)

    missing_hash = copy.deepcopy(full_receipt)
    missing_hash["budget"]["timeout_calibration"]["smoke_receipt_sha256"] = ""
    with pytest.raises(study.ContractError, match="calibration provenance"):
        study.validate_receipt(missing_hash, expected_mode="full", require_complete=True)

    changed_rule = copy.deepcopy(full_receipt)
    changed_rule["budget"]["timeout_calibration"]["derivation_rule"] = "ad hoc"
    with pytest.raises(study.ContractError, match="calibration provenance"):
        study.validate_receipt(changed_rule, expected_mode="full", require_complete=True)


def test_postrun_dirt_overrides_a_green_child(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    _poison_process_creation(monkeypatch)
    config = _config(tmp_path)
    host = "bnode999"
    monkeypatch.setattr(study.socket, "gethostname", lambda: host)
    nodefile = tmp_path / "pbs-nodefile"
    nodefile.write_text(host + "\n", encoding="utf-8")
    monkeypatch.setenv("PBS_JOBID", "0:124.nqsv")
    monkeypatch.setenv("PBS_NODEFILE", str(nodefile))
    executor = FakeExecutor(tmp_path, host, dirty_after_measurement=True)
    rc, receipt = study.run_study(config, executor)
    assert rc == 1
    assert receipt["status"] == "failed"
    assert receipt["failure"]["type"] == "PostrunDirt"
    assert receipt["failure"]["stage"].endswith("shard-0")


def test_arm_specific_deselection_prevents_complete_receipt(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    _poison_process_creation(monkeypatch)
    config = _config(tmp_path)
    host = "bnode999"
    monkeypatch.setattr(study.socket, "gethostname", lambda: host)
    nodefile = tmp_path / "pbs-nodefile"
    nodefile.write_text(host + "\n", encoding="utf-8")
    monkeypatch.setenv("PBS_JOBID", "0:125.nqsv")
    monkeypatch.setenv("PBS_NODEFILE", str(nodefile))
    executor = FakeExecutor(tmp_path, host, junit_by_nproc={"32": _JUNIT_ONE_TEST})
    rc, receipt = study.run_study(config, executor)
    assert rc == 1
    assert receipt["status"] == "failed"
    assert receipt["invariant_checks"]["junit_identity_sets_match_by_shard"] is False
    assert receipt["failure"]["type"] == "ContractError"
    assert "JUnit testcase identity set differs" in receipt["failure"]["message"]


def test_arm_specific_skip_identity_prevents_complete_receipt(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    _poison_process_creation(monkeypatch)
    config = _config(tmp_path)
    host = "bnode990"
    monkeypatch.setattr(study.socket, "gethostname", lambda: host)
    nodefile = tmp_path / "pbs-nodefile"
    nodefile.write_text(host + "\n", encoding="utf-8")
    monkeypatch.setenv("PBS_JOBID", "0:135.nqsv")
    monkeypatch.setenv("PBS_NODEFILE", str(nodefile))
    executor = FakeExecutor(tmp_path, host, junit_by_nproc={"32": _JUNIT_SKIPPED})

    rc, receipt = study.run_study(config, executor)

    assert rc == 1
    assert receipt["status"] == "failed"
    assert receipt["invariant_checks"]["junit_identity_sets_match_by_shard"] is False
    assert receipt["failure"]["type"] == "ContractError"
    assert "JUnit skipped testcase identity set differs" in receipt["failure"]["message"]


def test_static_contract_has_signal_traps_exact_registry_and_no_red_checker() -> None:
    repo = Path(__file__).resolve().parents[2]
    shell_text = (repo / "tools/pegasus/acceptance_nproc_study.sh").read_text(encoding="utf-8")
    driver_text = (repo / "tools/pegasus/run_acceptance_nproc_study.py").read_text(encoding="utf-8")
    assert "#PBS -b 1" in shell_text
    assert "#PBS -v IZANAGI_PEGASUS_THIRDPARTY_CACHE" in shell_text
    assert "umask 077" in shell_text
    assert "umask=0o022" in driver_text
    assert "THIRDPARTY_CACHE_ENV" in driver_text
    for signal_name in ("ERR", "TERM", "HUP", "INT", "EXIT"):
        assert f" {signal_name}" in shell_text or f"{signal_name} " in shell_text
    for recovery_contract in (
        "ACTIVE_CHILD_PID=$!",
        "ACTIVE_CHILD_PGID=$ACTIVE_CHILD_PID",
        'kill -TERM -- "-$ACTIVE_CHILD_PGID"',
        'kill -KILL -- "-$ACTIVE_CHILD_PGID"',
        'wait "$ACTIVE_CHILD_PID"',
        'kill -0 -- "-$ACTIVE_CHILD_PGID"',
        "recover_active_child",
    ):
        assert recovery_contract in shell_text
    driver_recovery = int(
        re.search(r"^DRIVER_MAX_RECOVERY_S=([0-9]+)$", shell_text, re.MULTILINE).group(1)
    )
    outer_kill_after = int(
        re.search(r"^OUTER_KILL_AFTER_S=([0-9]+)$", shell_text, re.MULTILINE).group(1)
    )
    shell_smoke_cap = int(
        re.search(r"^SMOKE_ARM_LIVENESS_CAP_S=([0-9]+)$", shell_text, re.MULTILINE).group(1)
    )
    assert driver_recovery > (
        study.PER_SHARD_POSTRUN_RESERVE_S + study.FAILURE_FINALIZE_CAP_S + 15
    )
    assert outer_kill_after > driver_recovery
    assert shell_smoke_cap == study.SMOKE_ARM_LIVENESS_CAP_S
    assert 'timeout --signal=TERM --kill-after="$kill_after_s"' in shell_text
    assert "os.path.realpath(sys.executable)" in shell_text
    assert '[[ "$resolved_python" == /* && -x "$resolved_python" ]]' in shell_text
    assert 'PY=$resolved_python' in shell_text
    assert '[[ -n "$PYTHONUSERBASE" && "$PYTHONUSERBASE" == /* ]]' in shell_text
    assert "site.getuserbase()" in shell_text
    assert shell_text.index("site.getuserbase()") < shell_text.index(
        'export HOME="$TMPDIR/job-home"'
    )
    assert "IZANAGI_ACCEPTANCE_NPROC_SMOKE_RECEIPT" in shell_text
    assert "manual arm timeout overrides are forbidden" in shell_text
    assert "postrun_deadline = time.monotonic()" in driver_text
    assert "deadline = time.monotonic() + timeout_s" in driver_text
    assert "min(float(FAILURE_FINALIZE_CAP_S)" in driver_text
    forbidden = "tools/" + "check_acceptance_reds.py"
    assert forbidden not in shell_text
    assert forbidden not in driver_text
    registry = json.loads(
        (repo / "tools/pegasus/admission_registry.json").read_text(encoding="utf-8")
    )["entries"]
    expected = {
        "tools/pegasus/acceptance_nproc_study.sh",
        "tools/pegasus/run_acceptance_nproc_study.py",
    }
    assert expected <= set(registry)
    assert all(registry[path]["class"] == "dispatch-required" for path in expected)


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__]))
