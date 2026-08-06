#!/usr/bin/env python3
"""orchestrator テストの推奨実行ランナー。

pytest-xdist が無ければユーザーローカル (`pip install --user`) へ自動導入してから
並列実行する。導入に失敗した環境 (オフライン等) では直列で回す — テスト自体は
xdist に依存しない。並列時の既定 scheduler は ``--dist loadgroup`` で、実 repo / 共有
submodule を使うテストを単一 runner invocation 内で相互排他にする。loadgroup がある
pytest-xdist 2.5 以上でなければ直列へフォールバックする。

Pegasus では例外を設ける。ログインノード上の実行形は gen_S へ同期 dispatch し、
計算ノードでは affinity 全数を既定にする。計算ノードは外部 network 不可のため
pytest-xdist が import 不能または 2.5 未満なら pip / 直列 fallback をせず rc=16 で停止する。

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
import signal
import subprocess
import sys
import hashlib
import importlib
import json
import re
import secrets
import shlex
import shutil
import tempfile
import threading
import time
from contextvars import ContextVar
from enum import Enum
from importlib import metadata
from pathlib import Path
from typing import NamedTuple, Optional, Sequence

from packaging.version import InvalidVersion, Version

_REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_DEFAULT_TARGET = os.path.join(_REPO, "orchestrator", "tests")
if _REPO not in sys.path:
    sys.path.insert(0, _REPO)

from orchestrator.campaign import site_policy  # noqa: E402

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

# Only this closed table is known not to narrow test selection.  Any positional
# argument, selector, malformed option, or unknown option is conservatively
# targeted.
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
_PATH_VALUE_OPTIONS = frozenset({
    "--rootdir", "--confcutdir", "--basetemp", "--junitxml", "--log-file",
})
_SELECT_VALUE_OPTIONS = frozenset({
    "-k", "-m", "--deselect", "--ignore", "--ignore-glob", "--maxfail",
    "--stepwise-skip",
})
_VALUE_OPTIONS = _NONSELECT_VALUE_OPTIONS | _SELECT_VALUE_OPTIONS
_SUBMODULE_MARKER = Path("external") / "ccbench" / "CMakeLists.txt"
_SUBMODULE_GIT_MARKER = Path("external") / "ccbench" / ".git"
_DELETION_GATE_RC = 13
_SUBMODULE_GATE_RC = 14
_RULEOPS_GATE_RC = 15
_PEGASUS_DISPATCH_RC = 16
_PEGASUS_DISPATCH_EXEMPT_FLAGS = frozenset({
    "--collect-only", "--co", "--help", "--version", "--markers", "--fixtures",
    "--fixtures-per-test", "--trace-config", "--setup-plan",
})
_PEGASUS_BOUNDED_SCOPE_EXEMPT_FLAGS = frozenset({"--help", "--version"})
_BOUNDED_SCOPE_UNIT_ENV = "IZANAGI_RUN_TESTS_SCOPE_UNIT"
_BOUNDED_SCOPE_CAP_ENV = "IZANAGI_RUN_TESTS_SCOPE_CAP"
_BOUNDED_SCOPE_UNIT_PREFIX = "izanagi-run-tests-"
_CGROUP_ROOT = Path("/sys/fs/cgroup")
_PROC_SELF_CGROUP = Path("/proc/self/cgroup")
_SCOPE_POLL_SECONDS = 0.005
_SCOPE_ATTEST_SECONDS = 1.0
_SCOPE_DRAIN_SECONDS = 0.1
_GIT_ENV_ALLOWLIST = frozenset({
    "GIT_CONFIG_NOSYSTEM", "GIT_TERMINAL_PROMPT",
})


class _ScopeOutcome(Enum):
    CHILD_RC = "child_rc"
    CAP_OOM = "cap_oom"
    HEADROOM_SHORT = "headroom_short"
    DISPATCH_INFRA = "dispatch_infra"


class _ScopeResult(NamedTuple):
    outcome: _ScopeOutcome
    child_rc: Optional[int] = None


class _ScopeSamples:
    def __init__(self) -> None:
        self.ready = threading.Event()
        self.stop = threading.Event()
        self.attested = False
        self.cgroup: Optional[Path] = None
        self.last_events: Optional[tuple[int, int]] = None
        self.peak_current: Optional[int] = None


class _ScopeAccounting(NamedTuple):
    module: object
    operation: str
    grant: object


_scope_accounting: ContextVar[Optional[_ScopeAccounting]] = ContextVar(
    "run_tests_scope_accounting", default=None,
)


def _available_cpus() -> int:
    """割り当て (cgroup / CPU affinity) を尊重した「このプロセスが使えるコア数」。

    PBS ジョブ内では割り当て分、素の login node では全コアを返す。os.cpu_count()
    (物理総数) と違い、割り当てを超えて掴まない。
    """
    return site_policy.available_cpus()


def _default_nproc(*, site: str = site_policy.OTHER) -> int:
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
    return max(1, site_policy.default_test_jobs(site, cap=_NPROC_CAP))


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


def _xdist_runtime_importable() -> bool:
    try:
        importlib.import_module("xdist")
    except Exception:
        return False
    return True


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


def _absolute_path(value: str, caller_cwd: Path) -> str:
    path = Path(value)
    if not path.is_absolute():
        path = caller_cwd / path
    try:
        return str(path.resolve(strict=False))
    except OSError:
        return os.path.abspath(os.fspath(path))


def _normalize_args(
    args: Sequence[str], caller_cwd: Optional[Path] = None,
) -> list[str]:
    """Normalize pytest path inputs once, relative to the caller's cwd."""

    base = Path.cwd() if caller_cwd is None else Path(caller_cwd)
    normalized: list[str] = []
    i = 0
    while i < len(args):
        token = args[i]
        option, separator, value = token.partition("=")
        if option in _PATH_VALUE_OPTIONS and separator:
            normalized_value = _absolute_path(value, base) if value else value
            normalized.append(f"{option}={normalized_value}")
            i += 1
            continue
        if token in _VALUE_OPTIONS:
            normalized.append(token)
            if i + 1 < len(args):
                option_value = args[i + 1]
                if token in _PATH_VALUE_OPTIONS and option_value:
                    option_value = _absolute_path(option_value, base)
                normalized.append(option_value)
                i += 2
                continue
            i += 1
            continue
        if token.startswith("-"):
            normalized.append(token)
            i += 1
            continue

        path_part, node_separator, node_part = token.partition("::")
        candidate = Path(path_part)
        if not candidate.is_absolute():
            candidate = base / candidate
        try:
            exists = candidate.exists()
        except OSError:
            exists = False
        if exists:
            path_part = _absolute_path(path_part, base)
        normalized.append(
            path_part + (node_separator + node_part if node_separator else "")
        )
        i += 1
    return normalized


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


def _positional_tokens(args: Sequence[str]) -> tuple[str, ...]:
    positional: list[str] = []
    i = 0
    while i < len(args):
        token = args[i]
        if token == "--":
            positional.extend(args[i + 1:])
            break
        if token in _VALUE_OPTIONS:
            i += 2
            continue
        if token.startswith("-"):
            i += 1
            continue
        positional.append(token)
        i += 1
    return tuple(positional)


def _has_no_execution_flag(args: Sequence[str]) -> bool:
    if any(token.split("=", 1)[0] in _NO_EXECUTION_FLAGS for token in args):
        return True
    try:
        addopts = shlex.split(os.environ.get("PYTEST_ADDOPTS", ""))
    except ValueError:
        return False
    return any(token.split("=", 1)[0] in _NO_EXECUTION_FLAGS for token in addopts)


def _has_dispatch_exempt_flag(args: Sequence[str]) -> bool:
    """Pegasus dispatch を免除する、裁定済みの閉集合だけを認識する。"""

    if any(
        token.split("=", 1)[0] in _PEGASUS_DISPATCH_EXEMPT_FLAGS
        for token in args
    ):
        return True
    try:
        addopts = shlex.split(os.environ.get("PYTEST_ADDOPTS", ""))
    except ValueError:
        return False
    return any(
        token.split("=", 1)[0] in _PEGASUS_DISPATCH_EXEMPT_FLAGS
        for token in addopts
    )


def _has_bounded_scope_exempt_flag(args: Sequence[str]) -> bool:
    """即終了する pytest 形だけを bounded scope から免除する。"""

    if any(token in _PEGASUS_BOUNDED_SCOPE_EXEMPT_FLAGS for token in args):
        return True
    try:
        addopts = shlex.split(os.environ.get("PYTEST_ADDOPTS", ""))
    except ValueError:
        return False
    return any(token in _PEGASUS_BOUNDED_SCOPE_EXEMPT_FLAGS for token in addopts)


def _test_operation(args: Sequence[str]) -> str:
    return "tests-full" if _is_full_suite(args) else "tests-partial"


def _is_acceptance_run(args: Sequence[str]) -> bool:
    """Recognize the closed acceptance shape independently of full-suite IDs."""

    # V14: removing strip must make the whitespace-only deletion-gate control red.
    if os.environ.get("PYTEST_ADDOPTS", "").strip():
        return False
    default_target = Path(_DEFAULT_TARGET).resolve()
    i = 0
    while i < len(args):
        token = args[i]
        option, separator, value = token.partition("=")
        if token == "--" or option in _NO_EXECUTION_FLAGS or option in _SELECT_FLAGS:
            return False
        if option in {"-o", "-p", "--override-ini"}:
            return False
        if token.startswith("-k") or token.startswith("-m"):
            return False
        if (
            token.startswith("-o") and not token.startswith("--")
        ) or (
            token.startswith("-p") and not token.startswith("--")
        ):
            return False

        if not token.startswith("-"):
            if "::" in token:
                return False
            try:
                if Path(token).resolve(strict=False) != default_target:
                    return False
            except OSError:
                return False
            i += 1
            continue
        if token in _NONSELECT_FLAGS:
            i += 1
            continue
        if len(token) >= 2 and not token.startswith("--") and (
            set(token[1:]) <= {"q", "v"}
        ):
            i += 1
            continue
        if token in _VALUE_OPTIONS:
            if i + 1 >= len(args) or not args[i + 1]:
                return False
            i += 2
            continue
        if separator and option in _VALUE_OPTIONS:
            if not value:
                return False
            i += 1
            continue
        if token.startswith("-n") and token != "-n" and len(token) > 2:
            i += 1
            continue
        # Default-deny every option not consumed by the closed spellings above.
        return False

    return True


def _git_env() -> dict[str, str]:
    env = {
        key: value for key, value in os.environ.items()
        if not key.startswith("GIT_") or key in _GIT_ENV_ALLOWLIST
    }
    env["GIT_TERMINAL_PROMPT"] = "0"
    return env


def _deletion_git_failure(message: str) -> int:
    print(
        f"未 stage 削除の git 検査が成立しません ({message})。"
        "受入形は未検査のため停止します。",
        file=sys.stderr,
        flush=True,
    )
    print(
        "git の実行環境を直し、意図した削除は git add -A で stage し、"
        "意図しない削除はファイルを復元してから再実行してください。",
        file=sys.stderr,
        flush=True,
    )
    return _DELETION_GATE_RC


def _preflight_unstaged_deletions(
    args: Sequence[str], repo: Path | str,
) -> int:
    if not _is_acceptance_run(args):
        return 0
    repo_path = Path(repo).resolve()
    try:
        result = subprocess.run(
            ["git", "-C", str(repo_path), "ls-files", "--deleted"],
            capture_output=True,
            text=True,
            env=_git_env(),
        )
    except (OSError, UnicodeDecodeError) as exc:
        return _deletion_git_failure(f"実行不能: {exc}")
    if result.returncode != 0:
        return _deletion_git_failure(f"git rc={result.returncode}")

    deleted = tuple(line for line in result.stdout.splitlines() if line)
    if not deleted:
        return 0

    print(
        f"未 stage 削除を {len(deleted)} 件検出しました:",
        file=sys.stderr,
        flush=True,
    )
    for path in deleted:
        print(f"  {path}", file=sys.stderr, flush=True)
    print(
        "意図した削除は git add -A で stage し、意図しない削除は"
        "ファイルを復元してから再実行してください。",
        file=sys.stderr,
        flush=True,
    )
    return _DELETION_GATE_RC


def _preflight_ruleops(args: Sequence[str], repo: Path | str) -> int:
    """Validate the production RuleOps ledger on acceptance-shaped runs only."""

    if not _is_acceptance_run(args):
        return 0
    repo_path = Path(repo).resolve()
    command = [
        sys.executable,
        str(repo_path / "tools" / "ruleops.py"),
        "check",
        "--repo",
        str(repo_path),
    ]
    try:
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            timeout=60,
        )
    except subprocess.TimeoutExpired:
        detail = "timeout"
        child_rc = "timeout"
    except (OSError, UnicodeDecodeError) as exc:
        detail = f"実行不能: {exc}"
        child_rc = "unavailable"
    else:
        if result.returncode == 0:
            return 0
        child_rc = str(result.returncode)
        detail = (result.stderr or result.stdout).strip() or "reason 出力なし"
    print(
        f"RuleOps production ledger preflight が失敗しました "
        f"(child rc={child_rc}: {detail})。",
        file=sys.stderr,
        flush=True,
    )
    return _RULEOPS_GATE_RC


def _submodule_is_initialized(repo: Path) -> bool:
    marker = repo / _SUBMODULE_MARKER
    git_marker = repo / _SUBMODULE_GIT_MARKER
    try:
        return (
            marker.is_file()
            and not marker.is_symlink()
            and git_marker.exists()
            and not git_marker.is_symlink()
        )
    except OSError:
        return False


def _submodule_failure(marker: Path, detail: str) -> int:
    print(
        f"submodule marker {marker} を初期化できませんでした ({detail})。",
        file=sys.stderr,
        flush=True,
    )
    print(
        "local modules cache を確認し、"
        "git submodule update --init -- external/ccbench を手動実行してください。",
        file=sys.stderr,
        flush=True,
    )
    return _SUBMODULE_GATE_RC


def _preflight_submodule(args: Sequence[str], repo: Path | str) -> int:
    if _has_no_execution_flag(args):
        return 0
    repo_path = Path(repo).resolve()
    marker = repo_path / _SUBMODULE_MARKER
    if _submodule_is_initialized(repo_path):
        return 0
    if not _is_acceptance_run(args):
        print(
            f"警告: submodule marker {marker} がありません。"
            "targeted run のため初期化せず続行します。",
            file=sys.stderr,
            flush=True,
        )
        return 0

    try:
        common_result = subprocess.run(
            ["git", "-C", str(repo_path), "rev-parse", "--git-common-dir"],
            capture_output=True,
            text=True,
            env=_git_env(),
            timeout=120,
        )
    except subprocess.TimeoutExpired:
        return _submodule_failure(marker, "git common-dir 検査が timeout")
    except (OSError, UnicodeDecodeError) as exc:
        return _submodule_failure(marker, f"git common-dir 検査不能: {exc}")
    if common_result.returncode != 0:
        return _submodule_failure(
            marker, f"git common-dir 検査 rc={common_result.returncode}",
        )
    common_text = common_result.stdout.strip()
    if not common_text:
        return _submodule_failure(marker, "git common-dir が空")
    common_dir = Path(common_text)
    if not common_dir.is_absolute():
        common_dir = repo_path / common_dir
    modules_cache = common_dir / "modules" / "external" / "ccbench"
    try:
        cache_exists = modules_cache.is_dir()
    except OSError:
        cache_exists = False
    if not cache_exists:
        return _submodule_failure(marker, f"local modules cache {modules_cache} がない")

    try:
        result = subprocess.run(
            [
                "git", "-C", str(repo_path), "submodule", "update", "--init",
                # V15: cache-only auto-init must never fetch the pinned commit.
                "--no-fetch", "--", "external/ccbench",
            ],
            capture_output=True,
            text=True,
            env=_git_env(),
            timeout=120,
        )
    except subprocess.TimeoutExpired:
        return _submodule_failure(marker, "git submodule update が timeout")
    except (OSError, UnicodeDecodeError) as exc:
        return _submodule_failure(marker, f"git submodule update 実行不能: {exc}")
    if _submodule_is_initialized(repo_path):
        return 0

    return _submodule_failure(marker, f"git submodule update rc={result.returncode}")


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
            rc = subprocess.call(list(cmd), cwd=_REPO)
        else:
            rc = subprocess.call(list(cmd), env=child_env, cwd=_REPO)
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


def _dispatch_environment() -> dict[str, str]:
    """計算ノード子へ渡す環境から親だけが所有する台帳状態を除く。"""

    child_env = os.environ.copy()
    child_env.pop(_TASK_RUN_ID_ENV, None)
    child_env.pop(_TASK_RUN_SIDECAR_ENV, None)
    child_env.pop(_TASK_RUNS_ROOT_ENV, None)
    return child_env


def _default_dispatch(
    args: Sequence[str], *, environ: dict[str, str],
) -> int:
    from tools.pegasus import dispatch_compute

    return dispatch_compute.dispatch(
        args,
        task="tests",
        repo_root=Path(_REPO),
        environ=environ,
    )


def _invoke_dispatch(
    dispatch_fn,
    args: Sequence[str],
    *,
    environ: dict[str, str],
) -> int:
    """dispatcher の想定外例外も top-level infra rc へ一義化する。"""

    try:
        return int(dispatch_fn(args, environ=environ))
    except (Exception, KeyboardInterrupt) as exc:
        print(
            f"Pegasus dispatcher を完了できませんでした: "
            f"{type(exc).__name__}: {exc}",
            file=sys.stderr,
            flush=True,
        )
        return _PEGASUS_DISPATCH_RC


def _dispatch_and_record(
    dispatch_fn,
    args: Sequence[str],
    task_run_id: str,
    *,
    environ: dict[str, str],
) -> int:
    """親の wall time と最終 rc を task_run へ一度だけ記録する。"""

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
    try:
        started = time.monotonic()
    except Exception:
        started = None
        recording_ready = False
    rc = _invoke_dispatch(dispatch_fn, args, environ=environ)
    if started is not None:
        try:
            duration_s = time.monotonic() - started
        except Exception:
            duration_s = 0.0
            recording_ready = False
    else:
        duration_s = 0.0
    if recording_ready:
        try:
            _record_task_run(
                task_run_id=task_run_id,
                root=root,
                suite_id=suite_id,
                suite_kind=suite_kind,
                duration_s=duration_s,
                exit_status=rc,
                trigger=trigger,
                sidecar=None,
            )
        except Exception:
            pass
    return rc


def _load_login_headroom():
    """予算 leaf を遅延 import する。"""

    try:
        module = importlib.import_module("orchestrator.campaign.login_headroom")
    except Exception as exc:
        print(
            "login headroom admission を読み込めないため、"
            f"計算ノードへ dispatch します: {type(exc).__name__}: {exc}",
            file=sys.stderr,
            flush=True,
        )
        return None
    return module


def _evaluate_login_admission(admit_fn, *, min_bytes=None, operation=None):
    loaded = _load_login_headroom()
    if loaded is None:
        return (
            None,
            None,
            _ScopeOutcome.HEADROOM_SHORT,
            "ログインノードの観測余裕=不明 bytes です。",
            None,
        )
    module = loaded
    try:
        if admit_fn is None:
            kwargs = {} if min_bytes is None else {"min_bytes": min_bytes}
            if operation is not None:
                kwargs["operation"] = operation
            decision = module.grant_budget(**kwargs)
        else:
            # 未 land テスト用の旧 admission seam。実運用は grant_budget だけを通る。
            decision = admit_fn(module.MAX_LOCAL_BUDGET_BYTES)
    except (Exception, KeyboardInterrupt) as exc:
        print(
            "login headroom admission を完了できないため、"
            f"計算ノードへ dispatch します: {type(exc).__name__}: {exc}",
            file=sys.stderr,
            flush=True,
        )
        return (
            module,
            None,
            _ScopeOutcome.HEADROOM_SHORT,
            "ログインノードの観測余裕=不明 bytes です。",
            None,
        )

    if admit_fn is not None and isinstance(decision, tuple) and len(decision) == 2:
        admission, reason = decision
        budget = module.MAX_LOCAL_BUDGET_BYTES if admission is module.Admission.LOCAL else None
    elif isinstance(decision, tuple) and len(decision) == 3:
        admission, budget, reason = decision
    else:
        admission, budget, reason = None, None, "予算 API が不正な結果を返しました。"
    is_local = admission is module.Admission.LOCAL
    if is_local and (type(budget) is not int or budget <= 0):
        is_local = False
        budget = None
    return (
        module,
        budget,
        None if is_local else _ScopeOutcome.HEADROOM_SHORT,
        reason if isinstance(reason, str) else "予算の理由を取得できませんでした。",
        decision,
    )


def _safe_bind_scope(grant, cgroup: Optional[Path]) -> None:
    if grant is None or cgroup is None:
        return
    try:
        bind_scope = getattr(grant, "bind_scope", None)
        if callable(bind_scope):
            bind_scope(cgroup)
    except (Exception, KeyboardInterrupt):
        pass


def _safe_release_grant(grant) -> None:
    if grant is None:
        return
    try:
        release = getattr(grant, "release", None)
        if callable(release):
            release()
    except (Exception, KeyboardInterrupt):
        pass


def _safe_remember_peak(module, operation: Optional[str], peak: Optional[int]) -> None:
    if module is None or operation is None or peak is None:
        return
    try:
        module.remember_peak(operation, peak)
    except (Exception, KeyboardInterrupt):
        pass


def _queue_dispatch_possible() -> tuple[bool, str]:
    """キュー観測不能は現行どおり dispatch 可へ倒す。"""

    try:
        module = importlib.import_module("orchestrator.campaign.queue_state")
        possible, reason = module.dispatch_possible()
        if type(possible) is not bool or not isinstance(reason, str):
            raise ValueError("invalid queue availability result")
        if not possible and ("ENA=" not in reason or "STS=" not in reason):
            raise ValueError("queue refusal lacks ENA/STS diagnostics")
        return possible, reason
    except (Exception, KeyboardInterrupt):
        return (
            True,
            "キューは ENA=不明、STS=不明です（観測不能のため可用扱い）。",
        )


def _print_granted_budget(cap: int, reason: str) -> None:
    print(
        f"bounded local に与えた予算: {cap} bytes。{reason}",
        file=sys.stderr,
        flush=True,
    )


def _no_execution_capacity(headroom_reason: str, queue_reason: str) -> int:
    print(
        "ログインの余裕もキューも無いため、いまは実行できません。"
        f"観測した余裕: {headroom_reason} {queue_reason}",
        file=sys.stderr,
        flush=True,
    )
    return _PEGASUS_DISPATCH_RC


def _parse_unified_cgroup(text: str) -> str:
    matches = []
    for line in text.splitlines():
        parts = line.split(":", 2)
        if len(parts) == 3 and parts[:2] == ["0", ""]:
            matches.append(parts[2])
    if len(matches) != 1:
        raise ValueError("unified cgroup entry is not unique")
    path = matches[0]
    components = path.removeprefix("/").split("/")
    if not path.startswith("/") or any(
        component in {"", ".", ".."} for component in components
    ):
        raise ValueError("unified cgroup path is not normalized")
    return path


def _scope_cgroup_path(proc_cgroup: Path, unit: str) -> Optional[Path]:
    try:
        path = _parse_unified_cgroup(proc_cgroup.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, ValueError):
        return None
    if Path(path).name != unit:
        return None
    return _CGROUP_ROOT / path.removeprefix("/")


def _read_scope_events(cgroup: Path) -> tuple[int, int]:
    parsed = {}
    for line in (cgroup / "memory.events").read_text(encoding="utf-8").splitlines():
        fields = line.split()
        if len(fields) != 2 or not fields[1].isascii() or not fields[1].isdecimal():
            raise ValueError("malformed memory.events")
        if fields[0] in parsed:
            raise ValueError("duplicate memory.events field")
        parsed[fields[0]] = int(fields[1], 10)
    return parsed["max"], parsed["oom"]


def _read_scope_current(cgroup: Path) -> int:
    raw = (cgroup / "memory.current").read_text(encoding="utf-8").strip()
    if not raw.isascii() or not raw.isdecimal():
        raise ValueError("malformed memory.current")
    return int(raw, 10)


def _scope_properties_are_enforced(cgroup: Path, cap: int) -> bool:
    try:
        memory_max = (cgroup / "memory.max").read_text(encoding="utf-8").strip()
        oom_group = (cgroup / "memory.oom.group").read_text(
            encoding="utf-8",
        ).strip()
    except (OSError, UnicodeError):
        return False
    return memory_max == str(cap) and oom_group == "1"


def _attest_scope_oom_group(cgroup: Path) -> bool:
    oom_group = cgroup / "memory.oom.group"
    try:
        oom_group.write_text("1\n", encoding="utf-8")
        attested = oom_group.read_text(encoding="utf-8").strip()
    except (OSError, UnicodeError):
        return False
    return attested == "1"


def _bounded_scope_membership() -> Optional[bool]:
    """None は marker 無し、bool は marker に対する kernel 側の検証結果。"""

    unit = os.environ.get(_BOUNDED_SCOPE_UNIT_ENV)
    raw_cap = os.environ.get(_BOUNDED_SCOPE_CAP_ENV)
    if unit is None and raw_cap is None:
        return None
    if unit is None or raw_cap is None:
        return False
    if re.fullmatch(rf"{re.escape(_BOUNDED_SCOPE_UNIT_PREFIX)}[0-9]+-[0-9a-f]+\.scope", unit) is None:
        return False
    if not raw_cap.isascii() or not raw_cap.isdecimal():
        return False
    cap = int(raw_cap, 10)
    if cap <= 0:
        return False
    cgroup = _scope_cgroup_path(_PROC_SELF_CGROUP, unit)
    return (
        cgroup is not None
        and _attest_scope_oom_group(cgroup)
        and _scope_properties_are_enforced(cgroup, cap)
    )


def _new_scope_unit() -> str:
    return f"{_BOUNDED_SCOPE_UNIT_PREFIX}{os.getpid()}-{secrets.token_hex(8)}.scope"


def _scope_command(
    args: Sequence[str], cap: int, unit: str,
    *, script_path: Optional[Path] = None,
) -> list[str]:
    script = Path(__file__).resolve() if script_path is None else script_path.resolve()
    return [
        "systemd-run", "--user", "--scope", "-q", f"--unit={unit}",
        "-p", "MemoryAccounting=yes",
        "-p", f"MemoryMax={cap}",
        "-p", "MemorySwapMax=0",
        "--", sys.executable, str(script), *args,
    ]


def _sample_scope(process, unit: str, cap: int, samples: _ScopeSamples) -> None:
    """走行中だけ cgroup を読み、消滅前の最後の観測を保持する。"""

    deadline = time.monotonic() + _SCOPE_ATTEST_SECONDS
    cgroup = None
    try:
        while not samples.stop.is_set():
            cgroup = _scope_cgroup_path(
                Path("/proc") / str(process.pid) / "cgroup",
                unit,
            )
            if cgroup is not None:
                break
            if process.poll() is not None or time.monotonic() >= deadline:
                return
            time.sleep(_SCOPE_POLL_SECONDS)

        if cgroup is None or not _attest_scope_oom_group(cgroup):
            return
        if not _scope_properties_are_enforced(cgroup, cap):
            return
        samples.cgroup = cgroup
        samples.attested = True

        first_sample = True
        while not samples.stop.is_set():
            current = None
            events = None
            try:
                current = _read_scope_current(cgroup)
            except (OSError, UnicodeError, ValueError):
                pass
            try:
                events = _read_scope_events(cgroup)
            except (OSError, UnicodeError, ValueError, KeyError):
                pass

            if current is not None:
                samples.peak_current = max(
                    current,
                    samples.peak_current if samples.peak_current is not None else 0,
                )
            if events is not None:
                samples.last_events = events
            if first_sample:
                samples.ready.set()
                first_sample = False
            if current is None or events is None:
                return
            time.sleep(_SCOPE_POLL_SECONDS)
    finally:
        samples.ready.set()


def _start_scope_sampler(process, unit: str, cap: int):
    samples = _ScopeSamples()
    thread = threading.Thread(
        target=_sample_scope,
        args=(process, unit, cap, samples),
        name=f"{unit}-sampler",
        daemon=True,
    )
    thread.start()
    return samples, thread


def _stop_bounded_scope(process, unit: str) -> None:
    """attestation 失敗時に scope 全体の停止を試み、runner も回収する。"""

    try:
        subprocess.run(
            ["systemctl", "--user", "stop", unit],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            timeout=5,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired):
        pass
    try:
        if process.poll() is None:
            process.terminate()
        process.wait(timeout=5)
    except (OSError, subprocess.TimeoutExpired):
        try:
            process.kill()
            process.wait(timeout=5)
        except (OSError, subprocess.TimeoutExpired):
            pass


def _run_bounded_scope(args: Sequence[str], cap: int) -> _ScopeResult:
    unit = _new_scope_unit()
    # task_run は scope 親が結果確定後に所有する。子へ渡すと CAP_OOM 後の
    # compute fallback と二重記録になり得る。
    child_env = _dispatch_environment()
    child_env[_BOUNDED_SCOPE_UNIT_ENV] = unit
    child_env[_BOUNDED_SCOPE_CAP_ENV] = str(cap)
    try:
        process = subprocess.Popen(
            _scope_command(args, cap, unit),
            cwd=_REPO,
            env=child_env,
        )
    except (OSError, ValueError) as exc:
        print(
            f"bounded scope を起動できませんでした: {type(exc).__name__}: {exc}",
            file=sys.stderr,
            flush=True,
        )
        return _ScopeResult(_ScopeOutcome.DISPATCH_INFRA)

    samples, sampler = _start_scope_sampler(process, unit, cap)
    samples.ready.wait(_SCOPE_ATTEST_SECONDS + _SCOPE_POLL_SECONDS)
    if not samples.attested:
        samples.stop.set()
        _stop_bounded_scope(process, unit)
        sampler.join(_SCOPE_DRAIN_SECONDS)
        print(
            "bounded scope の memory.max / memory.oom.group を走行中に"
            "attest できないため、scope を停止して dispatcher infrastructure "
            "failure とします。",
            file=sys.stderr,
            flush=True,
        )
        return _ScopeResult(_ScopeOutcome.DISPATCH_INFRA)

    accounting = _scope_accounting.get()
    if accounting is not None:
        _safe_bind_scope(accounting.grant, samples.cgroup)

    try:
        rc = process.wait()
    except (OSError, ValueError) as exc:
        samples.stop.set()
        _stop_bounded_scope(process, unit)
        sampler.join(_SCOPE_DRAIN_SECONDS)
        print(
            f"bounded scope の終了を確認できませんでした: {type(exc).__name__}: {exc}",
            file=sys.stderr,
            flush=True,
        )
        return _ScopeResult(_ScopeOutcome.DISPATCH_INFRA)

    final_events = None
    if _termination_signal(rc) is not None and samples.cgroup is not None:
        try:
            final_events = _read_scope_events(samples.cgroup)
        except (OSError, UnicodeError, ValueError, KeyError):
            pass

    # 正常終了では sampler 自身が cgroup の消滅を観測するまで待つ。ここで stop を
    # 立てると、最後の memory.events を読む直前に観測を打ち切り得る。
    sampler.join()
    if samples.peak_current is not None:
        print(
            f"bounded scope の観測ピーク: {samples.peak_current} bytes",
            file=sys.stderr,
            flush=True,
        )
    if samples.last_events is None:
        print(
            "bounded scope の memory.events を走行中に一度も読めないため、"
            "dispatcher infrastructure failure として停止します。",
            file=sys.stderr,
            flush=True,
        )
        return _ScopeResult(_ScopeOutcome.DISPATCH_INFRA)
    if _termination_signal(rc) is not None:
        # signal 終了は、終了後に読めたこの scope 自身の最終 counter だけを
        # cap 到達の証明に使う。古い走行中 sample へは倒さない。
        if final_events is None:
            print(
                "bounded scope は signal で終了しましたが、終了後の "
                "memory.events で cap 到達を証明できないため dispatcher "
                "infrastructure failure とします。",
                file=sys.stderr,
                flush=True,
            )
            return _ScopeResult(_ScopeOutcome.DISPATCH_INFRA)
        max_delta, oom_delta = final_events
        if max_delta > 0 and oom_delta > 0:
            if accounting is not None:
                _safe_remember_peak(
                    accounting.module,
                    accounting.operation,
                    max(cap, samples.peak_current or 0),
                )
            return _ScopeResult(_ScopeOutcome.CAP_OOM)
        print(
            "bounded scope は signal で終了しましたが、終了後の "
            "memory.events は cap 到達を示さないため dispatcher "
            "infrastructure failure とします。",
            file=sys.stderr,
            flush=True,
        )
        return _ScopeResult(_ScopeOutcome.DISPATCH_INFRA)
    if accounting is not None:
        _safe_remember_peak(
            accounting.module,
            accounting.operation,
            samples.peak_current,
        )
    return _ScopeResult(_ScopeOutcome.CHILD_RC, int(rc))


def _termination_signal(returncode: int) -> Optional[int]:
    signum = -returncode if returncode < 0 else returncode - 128
    if signum <= 0:
        return None
    try:
        return signum if signum in signal.valid_signals() else None
    except (AttributeError, OSError, ValueError):
        return signum if signum == signal.SIGKILL else None


def _run_bounded_scope_and_record(
    args: Sequence[str], cap: int,
) -> _ScopeResult:
    task_run_id = os.environ.get(_TASK_RUN_ID_ENV)
    if not task_run_id:
        return _run_bounded_scope(args, cap)

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
    try:
        started = time.monotonic()
    except Exception:
        started = None
        recording_ready = False
    result = _run_bounded_scope(args, cap)
    if result.outcome is not _ScopeOutcome.CHILD_RC:
        return result
    if started is not None:
        try:
            duration_s = time.monotonic() - started
        except Exception:
            duration_s = 0.0
            recording_ready = False
    else:
        duration_s = 0.0
    if recording_ready:
        try:
            assert result.child_rc is not None
            _record_task_run(
                task_run_id=task_run_id,
                root=root,
                suite_id=suite_id,
                suite_kind=suite_kind,
                duration_s=duration_s,
                exit_status=result.child_rc,
                trigger=trigger,
                sidecar=None,
            )
        except Exception:
            pass
    return result


def _tree_and_submodules_clean(repo: Path | str) -> bool:
    repo_path = Path(repo).resolve()
    commands = (
        [
            "git", "-C", str(repo_path), "status", "--porcelain=v1",
            "--untracked-files=all", "--ignore-submodules=none",
        ],
        [
            "git", "-C", str(repo_path), "submodule", "foreach", "--recursive",
            "--quiet", "git status --porcelain=v1 --untracked-files=all",
        ],
    )
    for command in commands:
        try:
            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                env=_git_env(),
                timeout=120,
            )
        except (OSError, UnicodeError, subprocess.TimeoutExpired):
            return False
        if result.returncode != 0 or result.stdout.strip():
            return False
    return True


def _cap_oom_dirty_refusal() -> int:
    print(
        "bounded scope が MemoryMax に達しましたが、working tree または submodule が"
        " clean ではないため自動 fallback しません。git status と git submodule status "
        "--recursive を確認し、変更を復旧または退避してから再実行してください。",
        file=sys.stderr,
        flush=True,
    )
    return _PEGASUS_DISPATCH_RC


def _dispatch_result(dispatch_fn, args: Sequence[str]) -> int:
    selected_dispatch = _default_dispatch if dispatch_fn is None else dispatch_fn
    child_env = _dispatch_environment()
    task_run_id = os.environ.get(_TASK_RUN_ID_ENV)
    if task_run_id:
        return _dispatch_and_record(
            selected_dispatch,
            args,
            task_run_id,
            environ=child_env,
        )
    return _invoke_dispatch(selected_dispatch, args, environ=child_env)


def _launch_local_scope(
    args: Sequence[str], cap: int, *, module=None, operation=None, grant=None,
):
    accounting = (
        _ScopeAccounting(module, operation, grant)
        if module is not None and operation is not None
        else None
    )
    token = _scope_accounting.set(accounting)
    try:
        return _run_bounded_scope_and_record(args, cap)
    finally:
        _scope_accounting.reset(token)


def main(
    argv: Optional[Sequence[str]] = None,
    *,
    site: Optional[str] = None,
    dispatch_fn=None,
    admit_fn=None,
) -> int:
    args = _normalize_args(sys.argv[1:] if argv is None else argv)
    operation = _test_operation(args)
    resolved_site = site_policy.current_site() if site is None else site
    if resolved_site not in {
        site_policy.OTHER,
        site_policy.PEGASUS_LOGIN,
        site_policy.PEGASUS_COMPUTE,
        site_policy.PEGASUS_SUSPECT,
    }:
        print(
            "実行 site を安全に分類できないため、テスト実行を拒否します。",
            file=sys.stderr,
            flush=True,
        )
        return _PEGASUS_DISPATCH_RC

    bounded_membership = _bounded_scope_membership()
    if bounded_membership is False:
        print(
            "bounded scope marker と cgroup の memory.max / memory.oom.group が"
            "一致しないため、テスト実行を拒否します。",
            file=sys.stderr,
            flush=True,
        )
        return _PEGASUS_DISPATCH_RC

    dispatch_exempt = _has_dispatch_exempt_flag(args)
    bounded_scope_exempt = _has_bounded_scope_exempt_flag(args)
    if (
        bounded_membership is None
        and not bounded_scope_exempt
        and site_policy.is_pegasus_login(resolved_site)
    ):
        module, cap, admission_outcome, headroom_reason, grant = (
            _evaluate_login_admission(admit_fn, operation=operation)
        )
        queue_unavailable = False
        queue_reason = ""
        if admission_outcome is _ScopeOutcome.HEADROOM_SHORT:
            queue_possible, queue_reason = _queue_dispatch_possible()
            if not queue_possible:
                queue_unavailable = True
                if module is None:
                    return _no_execution_capacity(headroom_reason, queue_reason)
                _safe_release_grant(grant)
                module, cap, admission_outcome, headroom_reason, grant = (
                    _evaluate_login_admission(
                        admit_fn, min_bytes=0, operation=operation,
                    )
                )
                if (
                    admission_outcome is _ScopeOutcome.HEADROOM_SHORT
                    or cap is None
                ):
                    _safe_release_grant(grant)
                    return _no_execution_capacity(headroom_reason, queue_reason)
            else:
                _safe_release_grant(grant)
                return _dispatch_result(dispatch_fn, args)

        if admission_outcome is None:
            if cap is None:
                _safe_release_grant(grant)
                return _PEGASUS_DISPATCH_RC
            _print_granted_budget(cap, headroom_reason)
            try:
                scope_result = _launch_local_scope(
                    args,
                    cap,
                    module=module,
                    operation=operation,
                    grant=grant,
                )
            finally:
                _safe_release_grant(grant)
            if scope_result.outcome is _ScopeOutcome.CHILD_RC:
                if scope_result.child_rc is None:
                    return _PEGASUS_DISPATCH_RC
                return scope_result.child_rc
            if scope_result.outcome is _ScopeOutcome.DISPATCH_INFRA:
                return _PEGASUS_DISPATCH_RC
            if scope_result.outcome is not _ScopeOutcome.CAP_OOM:
                return _PEGASUS_DISPATCH_RC
            if queue_unavailable:
                return _no_execution_capacity(headroom_reason, queue_reason)
            if not _tree_and_submodules_clean(Path(_REPO)):
                return _cap_oom_dirty_refusal()
            return _dispatch_result(dispatch_fn, args)

    preflight_rc = _preflight_unstaged_deletions(args, Path(_REPO))
    if preflight_rc:
        return preflight_rc
    preflight_rc = _preflight_ruleops(args, Path(_REPO))
    if preflight_rc:
        return preflight_rc
    preflight_rc = _preflight_submodule(args, Path(_REPO))
    if preflight_rc:
        return preflight_rc

    if not dispatch_exempt and resolved_site == site_policy.PEGASUS_SUSPECT:
        queue_hint = _queue_dispatch_possible()
        print(
            site_policy.heavy_work_refusal(
                resolved_site, "pytest テスト実行",
                queue_hint=queue_hint,
            ),
            file=sys.stderr,
            flush=True,
        )
        return _PEGASUS_DISPATCH_RC
    if not dispatch_exempt and site_policy.is_pegasus_login(resolved_site):
        if bounded_membership is True:
            pass
        else:
            return _dispatch_result(dispatch_fn, args)

    use_xdist = False
    if site_policy.is_pegasus_compute(resolved_site):
        version = _xdist_version()
        if (
            _xdist_supports_loadgroup(version)
            and _xdist_runtime_importable()
        ):
            use_xdist = True
        else:
            print(
                f"Pegasus 計算ノードの pytest-xdist "
                f"{version or '未導入'} は import / loadgroup 要件 "
                f"(>= {_MIN_XDIST_VERSION}) を満たしません。"
                "計算ノードは外部 network 不可のため pip を呼ばず停止します。",
                file=sys.stderr,
                flush=True,
            )
            return _PEGASUS_DISPATCH_RC
    else:
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

    default_nproc = _default_nproc(site=resolved_site) if use_xdist else 1
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
        has_target=bool(_positional_tokens(args)),
    )
    task_run_id = os.environ.get(_TASK_RUN_ID_ENV)
    if not task_run_id:
        return subprocess.call(cmd, cwd=_REPO)
    return _call_and_record(cmd, args, task_run_id)


if __name__ == "__main__":
    sys.exit(main())
