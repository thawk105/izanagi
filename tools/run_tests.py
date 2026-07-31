#!/usr/bin/env python3
"""orchestrator テストの推奨実行ランナー。

Pegasus login では実行形を source snapshot とともに同期 PBS dispatch する。compute
worker は同じ interpreter の pytest/xdist を検査し、pip/network を使わない。その他の
環境では pytest-xdist が無ければ従来どおりユーザーローカルへ導入を試み、失敗時は
直列で回す。並列時の既定 scheduler は ``--dist loadgroup`` で、実 repo / 共有
submodule を使うテストを単一 runner invocation 内で相互排他にする。loadgroup がある
pytest-xdist 2.5 以上でなければ直列へフォールバックする。

**並列度は環境に自動追従する** (毎回の手調整を無くすため、2026-07-19):
`min(使えるコア数, 上限)`。「使えるコア数」は cgroup / CPU affinity を尊重するので、
PBS ジョブ内では割り当て分だけ、素のマシンではコア数どおりになる。上限は実測の
頭打ち (worklog 2026-07-19: 約1946 テストで -n 8/16/32/96 = 18.7/14.6/10.5/13.0s。
32 以降はワーカー起動コストが並列利得を食い、96 は 32 より遅い) と、共有ノードで
全コアを掴まない行儀から OTHER は `_NPROC_CAP`。Pegasus compute は割当 affinity
全数を既定とする。

使い方:
    python3 tools/run_tests.py                 # スイート全体を自動並列度で
    python3 tools/run_tests.py path/to/test_x.py  # 対象を指定 (pytest へそのまま渡す)
    python3 tools/run_tests.py -n 4            # 並列度を明示上書き (最優先)
    IZANAGI_TEST_NPROC=max python3 tools/run_tests.py  # 上限を外し全 affinity コア
    IZANAGI_TEST_NPROC=12 python3 tools/run_tests.py   # 既定を数値で上書き
"""
from __future__ import annotations

import os
import sys

# ``pegasus_policy`` is the single canonical policy module.  Establish its
# import identity before importing the rest of the runner (in particular any
# optional third-party module).
_TOOLS_DIR = os.path.dirname(os.path.abspath(__file__))
if _TOOLS_DIR not in sys.path:
    sys.path.insert(0, _TOOLS_DIR)
import pegasus_policy

import subprocess
import hashlib
import json
import shlex
import shutil
import tempfile
import time
from importlib import metadata
from pathlib import Path
from typing import Optional, Sequence

_REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_DEFAULT_TARGET = os.path.join(_REPO, "orchestrator", "tests")

# 実測の頭打ち + 共有ノードで全コアを掴まない行儀の両方から来る既定上限。
# 環境変数 IZANAGI_TEST_NPROC=max で外せる。
_NPROC_CAP = 32
_MIN_XDIST_VERSION = "2.5"
_RUNNER_VERSION = "2"
_CURRENT_SITE: Optional[pegasus_policy.SiteObservation] = None

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
_GIT_ENV_ALLOWLIST = frozenset({
    "GIT_CONFIG_NOSYSTEM", "GIT_TERMINAL_PROMPT",
})
_WORKER_AUTH_ENV = "IZANAGI_TEST_WORKER_AUTH"
_RUNNER_RESULT_ENV = "IZANAGI_TEST_RUNNER_RESULT"


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
    """Resolve the default through the canonical site policy."""

    observation = _CURRENT_SITE
    if observation is None:
        observation = pegasus_policy.classify_site(
            "runner-local.invalid", None, range(_available_cpus()),
        )
    override = os.environ.get("IZANAGI_TEST_NPROC", "").strip()
    if override:
        if override.lower() in {"max", "all"}:
            requested = len(observation.affinity_cpus)
            return pegasus_policy.resolve_test_workers(requested, observation)
        try:
            value = int(override)
        except ValueError:
            print(f"IZANAGI_TEST_NPROC={override!r} は数値/max ではない — 無視", flush=True)
        else:
            if value > 0:
                return pegasus_policy.resolve_test_workers(value, observation)
            print(f"IZANAGI_TEST_NPROC={override!r} は正でない — 無視", flush=True)
    return max(1, pegasus_policy.resolve_test_workers(None, observation))


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
        # ``packaging`` is deliberately lazy: login dispatch and the wrapper's
        # own exact help/version paths must not import it.
        from packaging.version import InvalidVersion, Version

        return Version(version) >= Version(_MIN_XDIST_VERSION)
    except (ImportError, InvalidVersion):
        return False


def _ensure_xdist() -> bool:
    if _xdist_installed():
        return True
    if (
        _CURRENT_SITE is not None
        and _CURRENT_SITE.site_kind is pegasus_policy.PEGASUS_COMPUTE
    ):
        # Compute jobs are network/install free.  Environment validation in the
        # worker also checks pytest and xdist with this exact interpreter.
        return False
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


def _validate_explicit_nproc(
    args: Sequence[str],
    observation: pegasus_policy.SiteObservation,
) -> Optional[int]:
    """Validate the supported xdist policy spellings before pytest sees them."""

    raw = _explicit_nproc(args)
    if raw is None:
        return None
    if raw.strip().lower() in {"auto", "logical"}:
        resolved = pegasus_policy.resolve_test_workers(
            raw.strip().lower(),
            observation,
        )
        if observation.site_kind is pegasus_policy.OTHER:
            # Preserve pytest-xdist's existing symbolic spellings outside
            # Pegasus.  Compute jobs require an affinity-bounded integer.
            return None
        return resolved
    try:
        value = int(raw, 10)
    except (TypeError, ValueError):
        raise pegasus_policy.SitePolicyError(
            "explicit pytest worker count must be -n0 or a positive integer"
        ) from None
    if value < 0:
        raise pegasus_policy.SitePolicyError(
            "explicit pytest worker count must be -n0 or a positive integer"
        )
    return pegasus_policy.resolve_test_workers(value, observation)


def _resolve_compute_symbolic_nproc(
    args: Sequence[str],
    observation: pegasus_policy.SiteObservation,
) -> list[str]:
    """Replace compute-only symbolic xdist counts with the affinity-bound value."""

    if observation.site_kind is not pegasus_policy.PEGASUS_COMPUTE:
        return list(args)

    def resolve_symbolic(value: str) -> str:
        return str(pegasus_policy.resolve_test_workers(
            value.strip().lower(),
            observation,
        ))

    rewritten: list[str] = []
    i = 0
    while i < len(args):
        token = args[i]
        if token in {"-n", "--numprocesses"} and i + 1 < len(args):
            value = args[i + 1]
            rewritten.extend([
                token,
                (
                    resolve_symbolic(value)
                    if value.strip().lower() in {"auto", "logical"}
                    else value
                ),
            ])
            i += 2
            continue
        if token.startswith("-n") and token != "-n":
            value = token[2:]
            rewritten.append(
                "-n" + (
                    resolve_symbolic(value)
                    if value.strip().lower() in {"auto", "logical"}
                    else value
                )
            )
        elif token.startswith("--numprocesses="):
            value = token.split("=", 1)[1]
            rewritten.append(
                "--numprocesses=" + (
                    resolve_symbolic(value)
                    if value.strip().lower() in {"auto", "logical"}
                    else value
                )
            )
        else:
            rewritten.append(token)
        i += 1
    return rewritten


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
    if (
        use_xdist
        and _CURRENT_SITE is not None
        and _CURRENT_SITE.site_kind is pegasus_policy.PEGASUS_COMPUTE
    ):
        # The job disables entry-point autoload so executable plugin input is
        # closed; load only the same-interpreter xdist distribution verified by
        # the worker.
        cmd += ["-p", "xdist.plugin"]
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
) -> Optional[str]:
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

        event = record_test_run(
            root, task_run_id, suite_id=suite_id, suite_kind=suite_kind,
            duration_s=duration_s, exit_status=exit_status, counts=counts,
            trigger=trigger, collected_node_digest=digest,
        )
    except Exception:
        return None
    event_id = event.get("event_id")
    return event_id if isinstance(event_id, str) else None


def _task_run_event_receipt(
    root: Path,
    task_run_id: str,
    event_id: str,
) -> Optional[dict[str, object]]:
    path = root / task_run_id / "events.jsonl"
    try:
        info = path.lstat()
        if not path.is_file() or path.is_symlink() or info.st_size > 8 * 1024 * 1024:
            return None
        raw = path.read_bytes()
        matches = [
            item for line in raw.splitlines()
            for item in (json.loads(line),)
            if isinstance(item, dict) and item.get("event_id") == event_id
        ]
    except (OSError, json.JSONDecodeError):
        return None
    if len(matches) != 1:
        return None
    return {
        "path": str(path.resolve(strict=True)),
        "size": len(raw),
        "sha256": hashlib.sha256(raw).hexdigest(),
        "event_id": event_id,
    }


def _call_and_record(
    cmd: Sequence[str],
    args: Sequence[str],
    task_run_id: str,
    *,
    receipt: Optional[dict[str, object]] = None,
) -> int:
    if receipt is not None:
        receipt["task_run_attempted"] = True
        receipt["task_run_event_id"] = None
        receipt["task_run_event"] = None
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
                event_id = _record_task_run(
                    task_run_id=task_run_id, root=root, suite_id=suite_id,
                    suite_kind=suite_kind, duration_s=duration_s, exit_status=rc,
                    trigger=trigger, sidecar=sidecar,
                )
                if receipt is not None:
                    receipt["task_run_event_id"] = event_id
                    receipt["task_run_event"] = (
                        _task_run_event_receipt(root, task_run_id, event_id)
                        if event_id is not None else None
                    )
            except Exception:
                if receipt is not None:
                    receipt["task_run_event_id"] = None
                    receipt["task_run_event"] = None
        return rc
    finally:
        if sidecar_dir is not None:
            try:
                shutil.rmtree(sidecar_dir)
            except Exception:
                pass


def _wrapper_local_response(args: Sequence[str]) -> Optional[int]:
    """Handle only exact wrapper-owned, code-free response shapes."""

    if list(args) == ["--help"]:
        print(
            "usage: run_tests.py [pytest arguments]\n"
            "\n"
            "Pegasus login hosts synchronously dispatch executing forms to PBS.\n"
            "Only this exact --help and --version response is handled locally."
        )
        return 0
    if list(args) == ["--version"]:
        print(f"izanagi-run-tests {_RUNNER_VERSION}")
        return 0
    return None


def _write_runner_result(
    path: Path,
    authorization: dict[str, object],
    *,
    runner_exit_status: int,
    pytest_exit_status: Optional[int],
    runner_stage: str,
    task_run: dict[str, object],
) -> None:
    def normalized(status: Optional[int]) -> tuple[Optional[int], Optional[int]]:
        if status is None:
            return None, None
        if type(status) is not int:
            raise ValueError("runner status is not an integer")
        if status < 0:
            process_signal = -status
            if not 1 <= process_signal <= 64:
                raise ValueError("runner signal is outside the supported domain")
            return 128 + process_signal, process_signal
        if status > 255:
            raise ValueError("runner status is outside the supported domain")
        return status, None

    normalized_runner, runner_signal = normalized(runner_exit_status)
    normalized_pytest, pytest_signal = normalized(pytest_exit_status)
    task_run_attempted = task_run.get("task_run_attempted", False)
    if type(task_run_attempted) is not bool:
        raise ValueError("task-run attempted state is not boolean")
    document = {
        "schema": "izanagi-test-runner-result-v2",
        "dispatch_id": authorization["dispatch_id"],
        "snapshot_manifest_sha256": authorization["snapshot_manifest_sha256"],
        "execution_closure_sha256": authorization["execution_closure_sha256"],
        "policy_sha256": authorization["policy_sha256"],
        "authorization_sha256": authorization["authorization_sha256"],
        "qsub_request_sha256": authorization["qsub_request_sha256"],
        "qsub_result_sha256": authorization["qsub_result_sha256"],
        "submit_receipt_sha256": authorization["submit_receipt_sha256"],
        "runner_claim_sha256": authorization["runner_claim_sha256"],
        "worker_environment_sha256": authorization["worker_environment_sha256"],
        "pbs_job_id_raw": authorization["pbs_job_id_raw"],
        "job_id_normalized": authorization["job_id_normalized"],
        "hostname_raw": authorization["hostname_raw"],
        "hostname_canonical": authorization["hostname_canonical"],
        "affinity_cpus": authorization["affinity_cpus"],
        "runner_exit_status": normalized_runner,
        "runner_signal": runner_signal,
        "pytest_exit_status": normalized_pytest,
        "pytest_signal": pytest_signal,
        "runner_stage": runner_stage,
        "task_run_attempted": task_run_attempted,
        "task_run_event_id": task_run.get("task_run_event_id"),
        "task_run_event": task_run.get("task_run_event"),
    }
    raw = (
        json.dumps(document, sort_keys=True, separators=(",", ":")) + "\n"
    ).encode("utf-8")
    path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    try:
        view = memoryview(raw)
        while view:
            written = os.write(fd, view)
            if written <= 0:
                raise OSError("short runner-result write")
            view = view[written:]
        os.fsync(fd)
    finally:
        os.close(fd)


def _finish_compute_runner(
    authorization: Optional[dict[str, object]],
    *,
    runner_exit_status: int,
    pytest_exit_status: Optional[int],
    runner_stage: str,
    task_run: Optional[dict[str, object]] = None,
) -> int:
    if authorization is None:
        return runner_exit_status
    result_path_raw = os.environ.get(_RUNNER_RESULT_ENV)
    if not result_path_raw:
        print("compute runner result path is missing", file=sys.stderr)
        return 125
    try:
        from pegasus.test_dispatch import (
            load_policy,
            snapshot_from_dispatch,
            verify_execution_closure,
            verify_snapshot_tree,
        )

        marker = os.environ.get(_WORKER_AUTH_ENV)
        if not marker:
            raise RuntimeError("compute runner authorization marker is missing")
        snapshot = snapshot_from_dispatch(Path(marker).parent)
        closure_sha = verify_execution_closure(snapshot)
        if closure_sha != authorization["execution_closure_sha256"]:
            raise RuntimeError("compute runner execution closure changed")
        snapshot_policy = load_policy(
            snapshot.snapshot_root
            / "tools"
            / "pegasus"
            / "test_dispatch_policy.json"
        )
        verify_snapshot_tree(snapshot, snapshot_policy)
        _write_runner_result(
            Path(result_path_raw),
            authorization,
            runner_exit_status=runner_exit_status,
            pytest_exit_status=pytest_exit_status,
            runner_stage=runner_stage,
            task_run=task_run or {
                "task_run_attempted": False,
                "task_run_event_id": None,
                "task_run_event": None,
            },
        )
    except Exception as exc:
        print(f"runner result publication failed: {exc}", file=sys.stderr)
        return 125
    if runner_exit_status < 0:
        return 128 + (-runner_exit_status)
    if runner_exit_status > 255:
        return 125
    return runner_exit_status


def _observe_runner_site() -> pegasus_policy.SiteObservation:
    try:
        return pegasus_policy.observe_site()
    except pegasus_policy.SitePolicyError:
        raise
    except Exception as exc:
        raise pegasus_policy.SitePolicyError(
            f"site observation failed: {exc}"
        ) from None


def main(argv: Optional[Sequence[str]] = None) -> int:
    global _CURRENT_SITE

    raw_args = list(sys.argv[1:] if argv is None else argv)
    local_response = _wrapper_local_response(raw_args)
    if local_response is not None:
        return local_response

    try:
        observation = _observe_runner_site()
    except pegasus_policy.SitePolicyError as exc:
        print(f"Pegasus site policy refused execution: {exc}", file=sys.stderr)
        return 125
    _CURRENT_SITE = observation

    if observation.site_kind is pegasus_policy.PEGASUS_LOGIN:
        try:
            from pegasus.submit_tests import dispatch_from_runner

            return dispatch_from_runner(
                raw_args=raw_args,
                source_root=Path(_REPO),
                caller_cwd=Path.cwd(),
            )
        except Exception as exc:
            print(f"Pegasus test dispatch failed: {exc}", file=sys.stderr)
            return 125

    worker_authorization: Optional[dict[str, object]] = None
    if observation.site_kind is pegasus_policy.PEGASUS_COMPUTE:
        marker = os.environ.get(_WORKER_AUTH_ENV)
        if not marker:
            print(
                "Pegasus compute execution requires a dispatch authorization marker.",
                file=sys.stderr,
            )
            return 125
        try:
            from pegasus.test_dispatch import authorize_runner

            worker_authorization = authorize_runner(
                marker_path=Path(marker),
                observation=observation,
                repo_root=Path(_REPO),
            )
        except Exception as exc:
            print(f"Pegasus worker authorization failed: {exc}", file=sys.stderr)
            return 125

    args = _normalize_args(raw_args)
    try:
        _validate_explicit_nproc(args, observation)
        args = _resolve_compute_symbolic_nproc(args, observation)
    except pegasus_policy.SitePolicyError as exc:
        print(f"pytest worker policy refused execution: {exc}", file=sys.stderr)
        return _finish_compute_runner(
            worker_authorization,
            runner_exit_status=2,
            pytest_exit_status=None,
            runner_stage="worker-policy",
        )
    preflight_rc = _preflight_unstaged_deletions(args, Path(_REPO))
    if preflight_rc:
        return _finish_compute_runner(
            worker_authorization,
            runner_exit_status=preflight_rc,
            pytest_exit_status=None,
            runner_stage="deletion-preflight",
        )
    preflight_rc = _preflight_ruleops(args, Path(_REPO))
    if preflight_rc:
        return _finish_compute_runner(
            worker_authorization,
            runner_exit_status=preflight_rc,
            pytest_exit_status=None,
            runner_stage="ruleops-preflight",
        )
    preflight_rc = _preflight_submodule(args, Path(_REPO))
    if preflight_rc:
        return _finish_compute_runner(
            worker_authorization,
            runner_exit_status=preflight_rc,
            pytest_exit_status=None,
            runner_stage="submodule-preflight",
        )

    use_xdist = False
    if _ensure_xdist():
        version = _xdist_version()
        if _xdist_supports_loadgroup(version):
            use_xdist = True
        else:
            if observation.site_kind is pegasus_policy.PEGASUS_COMPUTE:
                print(
                    f"compute job pytest-xdist {version or 'unavailable'} "
                    f"does not satisfy >= {_MIN_XDIST_VERSION}",
                    file=sys.stderr,
                )
                return _finish_compute_runner(
                    worker_authorization,
                    runner_exit_status=125,
                    pytest_exit_status=None,
                    runner_stage="xdist-environment",
                )
            print(
                f"pytest-xdist {version or 'version不明'} は loadgroup 非対応 "
                f"(< {_MIN_XDIST_VERSION}) — 直列で実行します",
                flush=True,
            )
    else:
        if observation.site_kind is pegasus_policy.PEGASUS_COMPUTE:
            print(
                "compute job lacks same-interpreter pytest-xdist; "
                "network installation is forbidden",
                file=sys.stderr,
            )
            return _finish_compute_runner(
                worker_authorization,
                runner_exit_status=125,
                pytest_exit_status=None,
                runner_stage="xdist-environment",
            )
        print("pytest-xdist を導入できない環境 — 直列で実行します", flush=True)

    try:
        default_nproc = (
            _default_nproc()
            if use_xdist and _explicit_nproc(args) is None
            else 1
        )
    except pegasus_policy.SitePolicyError as exc:
        print(f"pytest worker policy refused execution: {exc}", file=sys.stderr)
        return _finish_compute_runner(
            worker_authorization,
            runner_exit_status=2,
            pytest_exit_status=None,
            runner_stage="worker-policy",
        )
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
    if (
        observation.site_kind is pegasus_policy.PEGASUS_COMPUTE
        and worker_authorization is not None
    ):
        marker = Path(os.environ[_WORKER_AUTH_ENV]).resolve(strict=True)
        generated_root = marker.parent / "pytest-generated"
        # Keep legitimate pytest cache/tmp output outside the immutable source
        # execution tree.  Dispatcher input rejects user cache/basetemp
        # overrides, so these controller-owned values remain final.
        cmd += [
            "-o", f"cache_dir={generated_root / 'cache'}",
            "--basetemp", str(generated_root / "tmp"),
        ]
    task_run_id = os.environ.get(_TASK_RUN_ID_ENV)
    task_run_receipt: dict[str, object] = {
        "task_run_attempted": False,
        "task_run_event_id": None,
        "task_run_event": None,
    }
    if not task_run_id:
        rc = subprocess.call(cmd, cwd=_REPO)
    else:
        rc = _call_and_record(
            cmd, args, task_run_id, receipt=task_run_receipt,
        )

    return _finish_compute_runner(
        worker_authorization,
        runner_exit_status=rc,
        pytest_exit_status=rc,
        runner_stage="pytest",
        task_run=task_run_receipt,
    )


if __name__ == "__main__":
    sys.exit(main())
