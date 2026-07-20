#!/usr/bin/env python3
"""orchestrator テストの推奨実行ランナー。

pytest-xdist が無ければユーザーローカル (`pip install --user`) へ自動導入してから
並列実行する。導入に失敗した環境 (オフライン等) では直列で回す — テスト自体は
xdist に依存しない。並列時の既定 scheduler は ``--dist loadgroup`` で、実 repo / 共有
submodule を使うテストを単一 runner invocation 内で相互排他にする。loadgroup がある
pytest-xdist 2.5 以上でなければ直列へフォールバックする。

**並列度は環境に自動追従する** (毎回の手調整を無くすため、2026-07-19):
`min(使えるコア数, 上限)`。「使えるコア数」は cgroup / CPU affinity を尊重するので、
PBS ジョブ内では割り当て分だけ、素のマシンではコア数どおりになる。上限は実測の
頭打ち (worklog 2026-07-19: 約1946 テストで -n 8/16/32/96 = 18.7/14.6/10.5/13.0s。
32 以降はワーカー起動コストが並列利得を食い、96 は 32 より遅い) と、共有ノードで
全コアを掴まない行儀 (orchestrator/tests/README.md) の両方から `_NPROC_CAP`。

使い方:
    python3 tools/run_tests.py                 # スイート全体を自動並列度で
    python3 tools/run_tests.py path/to/test_x.py  # 対象を指定 (pytest へそのまま渡す)
    python3 tools/run_tests.py -n 4            # 並列度を明示上書き (最優先)
    IZANAGI_TEST_NPROC=max python3 tools/run_tests.py  # 上限を外し全 affinity コア
    IZANAGI_TEST_NPROC=12 python3 tools/run_tests.py   # 既定を数値で上書き
"""
from __future__ import annotations

import os
import subprocess
import sys
import hashlib
import json
import shutil
import tempfile
import time
from importlib import metadata
from pathlib import Path
from typing import Optional, Sequence

from packaging.version import InvalidVersion, Version

_REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_DEFAULT_TARGET = os.path.join(_REPO, "orchestrator", "tests")

# 実測の頭打ち + 共有ノードで全コアを掴まない行儀の両方から来る既定上限。
# 環境変数 IZANAGI_TEST_NPROC=max で外せる。
_NPROC_CAP = 32
_MIN_XDIST_VERSION = Version("2.5")

_TASK_RUN_ID_ENV = "IZANAGI_TASK_RUN_ID"
_TASK_RUNS_ROOT_ENV = "IZANAGI_TASK_RUNS_ROOT"
_TASK_RUN_SIDECAR_ENV = "IZANAGI_TASK_RUN_SIDECAR"
_TEST_TRIGGER_ENV = "IZANAGI_TEST_TRIGGER"
_TRIGGERS = frozenset({
    "baseline", "after-change", "after-failure", "final", "review-fix",
    "unspecified",
})

# V14: only this closed table is known not to narrow test selection.  Any
# positional argument, selector, malformed option, or unknown option is
# conservatively targeted.
_NONSELECT_FLAGS = frozenset({
    "-s", "--disable-warnings", "--strict-config", "--strict-markers",
    "--continue-on-collection-errors", "--keep-duplicates", "--no-header",
    "--no-summary", "--full-trace", "--setup-only", "--setup-show",
    "--setup-plan", "--trace-config", "--version", "--help",
})
_NONSELECT_VALUE_OPTIONS = frozenset({
    "-n", "--numprocesses", "--dist", "--color", "--tb", "--capture",
    "--junitxml", "--junit-prefix", "--rootdir", "--confcutdir",
    "--basetemp", "--durations", "--durations-min", "--verbosity",
    "--show-capture", "--import-mode", "--log-level", "--log-format",
    "--log-date-format", "--log-cli-level", "--log-cli-format",
    "--log-cli-date-format", "--log-file", "--log-file-mode",
    "--log-file-level", "--log-file-format", "--log-file-date-format",
    "--override-ini", "-o", "-p",
})
_SELECT_FLAGS = frozenset({
    "-k", "-m", "--lf", "--last-failed", "--ff", "--failed-first",
    "--deselect", "--ignore", "--ignore-glob", "-x", "--exitfirst",
    "--maxfail", "--stepwise", "--sw", "--stepwise-skip", "--new-first",
    "--nf", "--collect-only", "--co", "--pyargs",
})
_NO_EXECUTION_FLAGS = frozenset({
    "--help", "--version", "--setup-only", "--setup-plan", "--collect-only",
    "--co", "--fixtures", "--fixtures-per-test", "--markers", "--trace-config",
})


def _available_cpus() -> int:
    """割り当て (cgroup / CPU affinity) を尊重した「このプロセスが使えるコア数」。

    PBS ジョブ内では割り当て分、素の login node では全コアを返す。os.cpu_count()
    (物理総数) と違い、割り当てを超えて掴まない。
    """
    process_cpu_count = getattr(os, "process_cpu_count", None)  # py3.13+, affinity 尊重
    if process_cpu_count is not None:
        n = process_cpu_count()
        if n:
            return n
    try:
        return len(os.sched_getaffinity(0))  # Linux
    except AttributeError:  # 非 Linux
        return os.cpu_count() or 1


def _default_nproc() -> int:
    """既定の並列度 = min(使えるコア数, 上限)。IZANAGI_TEST_NPROC で上書き可。"""
    override = os.environ.get("IZANAGI_TEST_NPROC", "").strip()
    if override:
        if override.lower() in {"max", "all"}:
            return max(1, _available_cpus())
        try:
            value = int(override)
        except ValueError:
            print(f"IZANAGI_TEST_NPROC={override!r} は数値/max ではない — 無視", flush=True)
        else:
            if value > 0:
                return value
            print(f"IZANAGI_TEST_NPROC={override!r} は正でない — 無視", flush=True)
    return max(1, min(_available_cpus(), _NPROC_CAP))


def _xdist_version() -> Optional[str]:
    # find_spec("xdist") はアンインストール残骸 (空 dir = namespace package) に騙される。
    # pytest の plugin 発見と同じ実体 = dist メタデータ (entry points) の有無で判定する
    try:
        return metadata.distribution("pytest-xdist").version
    except metadata.PackageNotFoundError:
        return None


def _xdist_installed() -> bool:
    return _xdist_version() is not None


def _xdist_supports_loadgroup(version: Optional[str]) -> bool:
    if version is None:
        return False
    try:
        return Version(version) >= _MIN_XDIST_VERSION
    except InvalidVersion:
        return False


def _ensure_xdist() -> bool:
    if _xdist_installed():
        return True
    print("pytest-xdist 未導入 — pip install --user で自動導入します", flush=True)
    try:
        r = subprocess.run(
            [sys.executable, "-m", "pip", "install", "--user", "--quiet", "pytest-xdist"],
            timeout=120,
        )
    except (subprocess.TimeoutExpired, OSError):
        return False
    return r.returncode == 0 and _xdist_installed()


def _is_target(token: str) -> bool:
    # オプションの値 (例: -n の「4」) を対象指定と誤認して既定ターゲットを外すと、
    # pytest が repo 全体を無指定収集してしまう。実在パスか test id だけを対象と数える
    return "::" in token or os.path.exists(token)


def _explicit_nproc(args: Sequence[str]) -> Optional[str]:
    """pytest-xdist の nproc 上書きを全 supported spelling から取り出す。"""
    value: Optional[str] = None
    i = 0
    while i < len(args):
        token = args[i]
        if token in {"-n", "--numprocesses"}:
            if i + 1 < len(args):
                value = args[i + 1]
                i += 2
                continue
        elif token.startswith("-n") and token != "-n":
            value = token[2:]
        elif token.startswith("--numprocesses="):
            value = token.split("=", 1)[1]
        i += 1
    return value


def _xdist_requested(args: Sequence[str], default_nproc: int) -> bool:
    explicit = _explicit_nproc(args)
    if explicit is None:
        return default_nproc != 0
    return explicit.strip() != "0"


def _user_dist_values(args: Sequence[str]) -> tuple[str, ...]:
    values: list[str] = []
    i = 0
    while i < len(args):
        token = args[i]
        if token == "--dist" and i + 1 < len(args):
            values.append(args[i + 1])
            i += 2
            continue
        if token.startswith("--dist="):
            values.append(token.split("=", 1)[1])
        i += 1
    return tuple(values)


def _build_pytest_command(
        args: Sequence[str], *, use_xdist: bool, default_nproc: int,
        has_target: bool, python_executable: str = sys.executable,
        default_target: str = _DEFAULT_TARGET) -> list[str]:
    """外部状態を読まず pytest argv を組み立てる純関数。

    runner の既定値を先に置き、ユーザー引数は必ず末尾へ保つ。したがって pytest の
    後勝ち規則により明示 ``-n`` / ``--dist`` が従来どおり最優先になる。
    """
    user_args = list(args)
    cmd = [python_executable, "-m", "pytest"]
    if not has_target:
        cmd.append(default_target)
    if use_xdist:
        if _explicit_nproc(user_args) is None:
            cmd += ["-n", str(default_nproc)]
        if _xdist_requested(user_args, default_nproc):
            cmd += ["--dist", "loadgroup"]
    return cmd + user_args


def _is_full_suite(args: Sequence[str], pytest_addopts: Optional[str] = None) -> bool:
    """Return true only for the closed, conservative V14 full-suite shape."""

    addopts = os.environ.get("PYTEST_ADDOPTS") if pytest_addopts is None else pytest_addopts
    if addopts is not None and addopts.strip():
        return False
    i = 0
    while i < len(args):
        token = args[i]
        if token == "--":
            return False
        option = token.split("=", 1)[0]
        if option in _NO_EXECUTION_FLAGS:
            return False
        if option in _SELECT_FLAGS or token.startswith("-k") or token.startswith("-m"):
            return False
        if token in _NONSELECT_FLAGS or (
            len(token) >= 2 and token[0] == "-" and set(token[1:]) <= {"q", "v"}
        ):
            i += 1
            continue
        if option in _NONSELECT_VALUE_OPTIONS:
            if "=" in token:
                if not token.split("=", 1)[1]:
                    return False
                i += 1
                continue
            if option == "-n" and token != "-n":
                # Handled below by the compact -nVALUE spelling.
                return False
            if i + 1 >= len(args):
                return False
            i += 2
            continue
        if token.startswith("-n") and token != "-n" and len(token) > 2:
            i += 1
            continue
        return False
    return True


def _normalized_fingerprint_args(args: Sequence[str]) -> list[str]:
    """Normalize repo-local path spelling before hashing; never persist argv."""

    repo = Path(_REPO).resolve()
    normalized: list[str] = []
    for token in args:
        path_part, separator, node_part = token.partition("::")
        try:
            candidate = Path(path_part)
            if candidate.is_absolute():
                path_part = candidate.resolve(strict=False).relative_to(repo).as_posix()
        except (OSError, ValueError):
            pass
        normalized.append(path_part + (separator + node_part if separator else ""))
    return normalized


def _suite_identity(
    args: Sequence[str], pytest_addopts: Optional[str] = None,
) -> tuple[str, str]:
    """Derive a privacy-safe suite kind/ID from wrapper inputs only."""

    addopts = os.environ.get("PYTEST_ADDOPTS") if pytest_addopts is None else pytest_addopts
    if _is_full_suite(args, addopts):
        return "full", "pytest-orchestrator-full"
    projection = {
        "args": _normalized_fingerprint_args(args),
        # Selection text is reduced to a digest before entering the projection.
        "addopts_digest": (
            hashlib.sha256(addopts.encode("utf-8")).hexdigest()[:12]
            if addopts and addopts.strip() else None
        ),
    }
    raw = json.dumps(projection, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return "targeted", f"pytest-targeted-{hashlib.sha256(raw).hexdigest()[:12]}"


def _private_sidecar() -> tuple[Path, Path]:
    """Create a repo-external 0700 directory; the hook creates the file."""

    directory = Path(tempfile.mkdtemp(prefix="izanagi-task-run-", dir="/tmp")).resolve()
    os.chmod(directory, 0o700)
    repo = Path(_REPO).resolve()
    if directory == repo or repo in directory.parents:
        raise OSError("sidecar directory unexpectedly resides in repository")
    return directory, directory / "pytest-stats.json"


def _record_task_run(
    *, task_run_id: str, root: Path, suite_id: str, suite_kind: str,
    duration_s: float, exit_status: int, trigger: str, sidecar: Optional[Path],
) -> None:
    """Best-effort single E1 call; never emit output or catch interrupts."""

    counts = None
    digest = None
    if _REPO not in sys.path:
        sys.path.insert(0, _REPO)
    if sidecar is not None:
        try:
            from tools.task_runs.pytest_stats import read_sidecar

            stats = read_sidecar(sidecar)
            if stats is not None:
                counts, digest = stats
        except Exception:
            pass
    try:
        from tools.task_runs import record_test_run

        record_test_run(
            root, task_run_id, suite_id=suite_id, suite_kind=suite_kind,
            duration_s=duration_s, exit_status=exit_status, counts=counts,
            trigger=trigger, collected_node_digest=digest,
        )
    except Exception:
        pass


def _call_and_record(cmd: Sequence[str], args: Sequence[str], task_run_id: str) -> int:
    recording_ready = True
    try:
        suite_kind, suite_id = _suite_identity(args)
    except Exception:
        recording_ready = False
        suite_kind, suite_id = "targeted", "pytest-targeted-unavailable"
    trigger = os.environ.get(_TEST_TRIGGER_ENV, "unspecified")
    if trigger not in _TRIGGERS:
        trigger = "unspecified"
    root = Path(os.environ.get(
        _TASK_RUNS_ROOT_ENV, os.path.join(_REPO, "output", "task-runs"),
    ))
    sidecar_dir: Optional[Path] = None
    sidecar: Optional[Path] = None
    child_env = None
    try:
        sidecar_dir, sidecar = _private_sidecar()
        child_env = os.environ.copy()
        child_env[_TASK_RUN_SIDECAR_ENV] = str(sidecar)
    except Exception:
        sidecar_dir = None
        sidecar = None

    try:
        try:
            started = time.monotonic()
        except Exception:
            started = None
            recording_ready = False
        if child_env is None:
            rc = subprocess.call(list(cmd))
        else:
            rc = subprocess.call(list(cmd), env=child_env)
        if started is not None:
            try:
                duration_s = time.monotonic() - started
            except Exception:
                recording_ready = False
                duration_s = 0.0
        else:
            duration_s = 0.0
        if recording_ready:
            try:
                _record_task_run(
                    task_run_id=task_run_id, root=root, suite_id=suite_id,
                    suite_kind=suite_kind, duration_s=duration_s, exit_status=rc,
                    trigger=trigger, sidecar=sidecar,
                )
            except Exception:
                pass
        return rc
    finally:
        if sidecar_dir is not None:
            try:
                shutil.rmtree(sidecar_dir)
            except Exception:
                pass


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    use_xdist = False
    if _ensure_xdist():
        version = _xdist_version()
        if _xdist_supports_loadgroup(version):
            use_xdist = True
        else:
            print(
                f"pytest-xdist {version or 'version不明'} は loadgroup 非対応 "
                f"(< {_MIN_XDIST_VERSION}) — 直列で実行します",
                flush=True,
            )
    else:
        print("pytest-xdist を導入できない環境 — 直列で実行します", flush=True)

    default_nproc = _default_nproc() if use_xdist else 1
    if (use_xdist and _xdist_requested(args, default_nproc)
            and any(value != "loadgroup" for value in _user_dist_values(args))):
        print(
            "警告: ユーザー指定の --dist が既定の --dist loadgroup より後に渡されます。"
            "後勝ちの scheduler では real-repo group の単一 runner invocation 内排他が"
            "無効になります。",
            file=sys.stderr,
            flush=True,
        )

    cmd = _build_pytest_command(
        args,
        use_xdist=use_xdist,
        default_nproc=default_nproc,
        has_target=any(_is_target(arg) for arg in args),
    )
    task_run_id = os.environ.get(_TASK_RUN_ID_ENV)
    if not task_run_id:
        return subprocess.call(cmd)
    return _call_and_record(cmd, args, task_run_id)


if __name__ == "__main__":
    sys.exit(main())
