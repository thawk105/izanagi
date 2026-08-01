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
import subprocess
import sys
import hashlib
import importlib
import json
import shlex
import shutil
import tempfile
import time
from importlib import metadata
from pathlib import Path
from typing import Optional, Sequence

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
_ALLOW_UNSTAGED_DELETIONS_ENV = "IZANAGI_TEST_ALLOW_UNSTAGED_DELETIONS"
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
_GIT_ENV_ALLOWLIST = frozenset({
    "GIT_CONFIG_NOSYSTEM", "GIT_TERMINAL_PROMPT",
})


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
    if os.environ.get(_TEST_TRIGGER_ENV) == "final":
        print(
            f"未 stage 削除の git 検査が成立しません ({message})。"
            f"{_TEST_TRIGGER_ENV}=final は未検査のため停止します。",
            file=sys.stderr,
            flush=True,
        )
        return _DELETION_GATE_RC
    print(
        f"警告: 未 stage 削除の git 検査が成立しません ({message}) — 続行します。",
        file=sys.stderr,
        flush=True,
    )
    return 0


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
    bypass = os.environ.get(_ALLOW_UNSTAGED_DELETIONS_ENV) == "1"
    final_run = os.environ.get(_TEST_TRIGGER_ENV) == "final"
    if bypass and not final_run:
        print(
            f"警告: 未 stage 削除 {len(deleted)} 件を "
            f"{_ALLOW_UNSTAGED_DELETIONS_ENV}=1 により許可して続行します。",
            file=sys.stderr,
            flush=True,
        )
        return 0

    print(
        f"未 stage 削除を {len(deleted)} 件検出しました:",
        file=sys.stderr,
        flush=True,
    )
    for path in deleted:
        print(f"  {path}", file=sys.stderr, flush=True)
    if bypass and final_run:
        print(
            f"{_TEST_TRIGGER_ENV}=final では "
            f"{_ALLOW_UNSTAGED_DELETIONS_ENV}=1 を使用できません。",
            file=sys.stderr,
            flush=True,
        )
    print(
        "git add -A で削除を stage してから再実行してください。",
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


def main(
    argv: Optional[Sequence[str]] = None,
    *,
    site: Optional[str] = None,
    dispatch_fn=None,
) -> int:
    args = _normalize_args(sys.argv[1:] if argv is None else argv)
    preflight_rc = _preflight_unstaged_deletions(args, Path(_REPO))
    if preflight_rc:
        return preflight_rc
    preflight_rc = _preflight_ruleops(args, Path(_REPO))
    if preflight_rc:
        return preflight_rc
    preflight_rc = _preflight_submodule(args, Path(_REPO))
    if preflight_rc:
        return preflight_rc

    resolved_site = site_policy.current_site() if site is None else site
    dispatch_exempt = _has_dispatch_exempt_flag(args)
    if not dispatch_exempt and resolved_site == site_policy.PEGASUS_SUSPECT:
        print(
            site_policy.heavy_work_refusal(
                resolved_site, "pytest テスト実行",
            ),
            file=sys.stderr,
            flush=True,
        )
        return _PEGASUS_DISPATCH_RC
    if not dispatch_exempt and site_policy.is_pegasus_login(resolved_site):
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
