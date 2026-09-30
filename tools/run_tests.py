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
    python3 tools/run_tests.py --force-dispatch  # LOGIN から必ず計算ノードへ
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
import math
import re
import secrets
import shlex
import shutil
import tempfile
import threading
import time
from contextlib import contextmanager
from contextvars import ContextVar
from enum import Enum
from importlib import metadata
from pathlib import Path
from typing import Any, Mapping, NamedTuple, Optional, Sequence

from packaging.version import InvalidVersion, Version

_REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_DEFAULT_TARGET = os.path.join(_REPO, "orchestrator", "tests")
if _REPO not in sys.path:
    sys.path.insert(0, _REPO)

from orchestrator.campaign import site_policy  # noqa: E402
from orchestrator import test_selection_contract as _SELECTION_CONTRACT  # noqa: E402

# 実測の頭打ち + 共有ノードで全コアを掴まない行儀の両方から来る既定上限。
# 環境変数 IZANAGI_TEST_NPROC=max で外せる。
_NPROC_CAP = 32
_MIN_XDIST_VERSION = Version("2.5")

_TASK_RUN_ID_ENV = "IZANAGI_TASK_RUN_ID"
_TASK_RUNS_ROOT_ENV = "IZANAGI_TASK_RUNS_ROOT"
_TASK_RUN_SIDECAR_ENV = "IZANAGI_TASK_RUN_SIDECAR"
_TASK_RUN_AUTO_RECORD_ENV = "IZANAGI_TASK_RUN_AUTO_RECORD"
_RUNNER_EXCLUSION_ENV = _SELECTION_CONTRACT.RUNNER_EXCLUSION_ENV
_TEST_TRIGGER_ENV = "IZANAGI_TEST_TRIGGER"
_RUN_GROWTH_HELD_TESTS_ENV = "IZANAGI_RUN_GROWTH_HELD_TESTS"
_DISPATCH_WALLTIME_OVERRIDE_ENV = "IZANAGI_DISPATCH_WALLTIME_OVERRIDE"
_DISPATCH_QUEUE_WAIT_TIMEOUT_OVERRIDE_ENV = "IZANAGI_DISPATCH_QUEUE_WAIT_TIMEOUT_OVERRIDE"
_DISPATCH_OVERALL_GRACE_OVERRIDE_ENV = "IZANAGI_DISPATCH_OVERALL_GRACE_OVERRIDE"
_ACCEPTANCE_SHARDS_ENV = "IZANAGI_ACCEPTANCE_SHARDS"
_ACCEPTANCE_SHARD_DEADLINE_S = 5100.0
_RUN_GROWTH_HELD_TESTS_TOKEN = "explicit-user-command"
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
    "--junitxml", "--junit-prefix", "--rootdir",
    "--basetemp", "--durations", "--durations-min", "--verbosity",
    "--show-capture", "--import-mode", "--log-level", "--log-format",
    "--log-date-format", "--log-cli-level", "--log-cli-format",
    "--log-cli-date-format", "--log-file", "--log-file-mode",
    "--log-file-level", "--log-file-format", "--log-file-date-format",
})
_FULL_SUITE_DISQUALIFY_VALUE_OPTIONS = frozenset({
    "--override-ini", "-o", "-p", "--confcutdir",
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
_VALUE_OPTIONS = (
    _NONSELECT_VALUE_OPTIONS
    | _FULL_SUITE_DISQUALIFY_VALUE_OPTIONS
    | _SELECT_VALUE_OPTIONS
)
_SUBMODULE_MARKER = Path("external") / "ccbench" / "CMakeLists.txt"
_SUBMODULE_GIT_MARKER = Path("external") / "ccbench" / ".git"
_DELETION_GATE_RC = 13
_SUBMODULE_GATE_RC = 14
_RULEOPS_GATE_RC = 15
_PEGASUS_DISPATCH_RC = 16
_ACCEPTANCE_DIST_OVERRIDE_RC = 17
_PERMANENT_EXCLUSION_GATE_RC = 18
_FORCE_DISPATCH_OPTION = "--force-dispatch"
_INTERNAL_SHARD_SESSION_OPTION = "--izanagi-acceptance-shard-session"
_INTERNAL_SHARD_COUNT_OPTION = "--izanagi-acceptance-shard-count"
_INTERNAL_SHARD_INDEX_OPTION = "--izanagi-acceptance-shard-index"
_PEGASUS_DISPATCH_EXEMPT_FLAGS = frozenset({
    "--collect-only", "--co", "--help", "--version", "--markers", "--fixtures",
    "--fixtures-per-test", "--trace-config", "--setup-plan",
})
_PEGASUS_BOUNDED_SCOPE_EXEMPT_FLAGS = frozenset({"--help", "--version"})
_BOUNDED_SCOPE_UNIT_ENV = "IZANAGI_RUN_TESTS_SCOPE_UNIT"
_BOUNDED_SCOPE_CAP_ENV = "IZANAGI_RUN_TESTS_SCOPE_CAP"
_BOUNDED_SCOPE_UNIT_PREFIX = "izanagi-run-tests-"
_BOUNDED_SCOPE_TOKEN_BYTES = 8
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


class _DispatchCallResult(NamedTuple):
    """親が dispatch の child 起動証拠を失わずに受け取る結果。"""

    rc: int
    child_started: bool


_PermanentExclusion = _SELECTION_CONTRACT.Exclusion
_PERMANENT_EXCLUSION_SET_VERSION = _SELECTION_CONTRACT.EXCLUSION_SET_VERSION
_SANCTIONED_CLEANUP_TEST_PATH = _SELECTION_CONTRACT.SANCTIONED_CLEANUP_TEST_PATH

# ここが runtime の active table。現在は共有契約の cleanup entry を参照する。
# sanctioned な上限と payload の定義は引き続き共有契約 module にだけ存在する。
_PERMANENT_FULL_SUITE_EXCLUSIONS = _SELECTION_CONTRACT.SANCTIONED_EXCLUSIONS


def _permanent_exclusions_are_sanctioned(
    exclusions: tuple[_PermanentExclusion, ...],
) -> tuple[_PermanentExclusion, ...] | None:
    """runner の恒久除外表を private canonical tuple へ写す。"""

    return _SELECTION_CONTRACT.canonicalize_sanctioned_exclusion_set(exclusions)


def _runner_exclusion_payload(
    exclusions: Sequence[_PermanentExclusion],
) -> list[dict[str, str]]:
    return _SELECTION_CONTRACT.payload_entries(exclusions)


@contextmanager
def _runner_exclusion_environment(
    exclusions: Sequence[_PermanentExclusion],
):
    """実 pytest child に runner 所有の除外証跡だけを一時的に渡す。"""

    previous = os.environ.get(_RUNNER_EXCLUSION_ENV)
    if exclusions:
        os.environ[_RUNNER_EXCLUSION_ENV] = _SELECTION_CONTRACT.serialize_payload(
            exclusions
        )
    else:
        os.environ.pop(_RUNNER_EXCLUSION_ENV, None)
    try:
        yield
    finally:
        if previous is None:
            os.environ.pop(_RUNNER_EXCLUSION_ENV, None)
        else:
            os.environ[_RUNNER_EXCLUSION_ENV] = previous


def _call_with_runner_exclusions(
    exclusions: Sequence[_PermanentExclusion], function, /, *args, **kwargs,
):
    with _runner_exclusion_environment(exclusions):
        return function(*args, **kwargs)


def _consume_runner_options(args: Sequence[str]) -> tuple[list[str], bool]:
    """runner 専用 option を pytest / dispatch child の argv から除く。"""

    force_dispatch = _FORCE_DISPATCH_OPTION in args
    return (
        [value for value in args if value != _FORCE_DISPATCH_OPTION],
        force_dispatch,
    )


def _validate_shard_outer_args(
    raw_args: Sequence[str], force_dispatch: bool,
) -> bool:
    """shard 親は空 argv または単独の force-dispatch だけを受理する。"""

    values = list(raw_args)
    return (
        (not values and force_dispatch is False)
        or (values == [_FORCE_DISPATCH_OPTION] and force_dispatch is True)
    )


def _acceptance_shard_request(
    environ: Optional[Mapping[str, str]] = None,
) -> Optional[int]:
    """shard 要求の env 字句だけを閉集合として解釈する。"""

    source = os.environ if environ is None else environ
    value = source.get(_ACCEPTANCE_SHARDS_ENV)
    if value is None or value == "":
        return None
    if value in {"1", "2", "3"}:
        return int(value, 10)
    raise ValueError(f"{_ACCEPTANCE_SHARDS_ENV}={value!r} is not accepted")


def _resolve_acceptance_shard_count(
    request: Optional[int],
    *,
    is_acceptance: bool,
    resolved_site: str,
    raw_args: Sequence[str],
    force_dispatch: bool,
    internal_shard_spec: Optional[object],
    positional: Sequence[str],
    bounded_membership: Optional[bool],
) -> int:
    """確定済み入力だけから effective K を解決する。"""

    if request is not None and type(request) is not int:
        raise ValueError("acceptance shard request must be an integer")
    eligible = (
        is_acceptance
        and site_policy.is_pegasus_login(resolved_site)
        and _validate_shard_outer_args(raw_args, force_dispatch)
        and not positional
        and internal_shard_spec is None
        and bounded_membership is not True
    )
    if request is None:
        return 2 if eligible else 1
    if request == 1:
        return 1
    if request in {2, 3}:
        if not eligible:
            raise ValueError("explicit acceptance shard request is ineligible")
        return request
    raise ValueError("invalid acceptance shard request")


def _consume_internal_shard_spec(
    args: Sequence[str],
) -> tuple[list[str], Optional[object]]:
    """dispatch child 専用 spec を pytest argv より前で exact に消費する。"""

    values: dict[str, str] = {}
    remaining: list[str] = []
    options = {
        _INTERNAL_SHARD_SESSION_OPTION,
        _INTERNAL_SHARD_COUNT_OPTION,
        _INTERNAL_SHARD_INDEX_OPTION,
    }
    for token in args:
        option, separator, value = token.partition("=")
        if option not in options:
            remaining.append(token)
            continue
        if not separator or not value or option in values:
            raise ValueError("invalid or duplicate internal acceptance shard option")
        values[option] = value
    if not values:
        return remaining, None
    if set(values) != options:
        raise ValueError("incomplete internal acceptance shard spec")
    from tools.acceptance_shards import InternalSpec

    try:
        count = int(values[_INTERNAL_SHARD_COUNT_OPTION], 10)
        index = int(values[_INTERNAL_SHARD_INDEX_OPTION], 10)
    except ValueError as exc:
        raise ValueError("non-integer internal acceptance shard spec") from exc
    spec = InternalSpec(
        Path(values[_INTERNAL_SHARD_SESSION_OPTION]).resolve(), count, index,
    )
    return remaining, spec


def _print_runner_help(args: Sequence[str]) -> None:
    """pytest の help を保ったまま runner 専用 option も公開する。"""

    if "--help" in args:
        print(
            "Izanagi runner option:\n"
            "  --force-dispatch  Pegasus LOGIN で headroom/queue 判定を"
            "行わず必ず計算ノードへ dispatch する\n",
            flush=True,
        )


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


class _TreeFingerprint(NamedTuple):
    digest: str
    summary: tuple[int, ...]


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


def _has_non_loadgroup_user_dist(args: Sequence[str]) -> bool:
    return any(value != "loadgroup" for value in _user_dist_values(args))


def _build_pytest_command(
        args: Sequence[str], *, use_xdist: bool, default_nproc: int,
        has_target: bool, python_executable: str = sys.executable,
        default_target: str = _DEFAULT_TARGET,
        exclusions: Sequence[_PermanentExclusion] = ()) -> list[str]:
    """外部状態を読まず pytest argv を組み立てる純関数。

    runner の既定値を先に置き、ユーザー引数は必ず末尾へ保つ。したがって明示
    ``-n`` / ``--dist`` は pytest の後勝ち規則により最優先になる。
    受入形の非 ``loadgroup`` な ``--dist`` は ``main()`` が構築前に拒否する。
    ``exclusions`` は ``main()`` が恒久除外表を適用する走行で渡す。
    """
    user_args = list(args)
    cmd = [python_executable, "-m", "pytest"]
    cmd.extend(_SELECTION_CONTRACT.exclusion_tokens(exclusions))
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
    """Return the peak-ledger key for this target set.

    Full-suite runs retain the single ``tests-full`` key.  Partial runs use
    ``tests-partial-<12 hex>`` where the digest is SHA-256 over the sorted,
    duplicate-free, repo-relative positional target strings.  Consequently
    target order does not change the key, while a different target set does.
    """

    if _is_full_suite(args):
        return "tests-full"
    targets = sorted(set(_normalized_fingerprint_args(_positional_tokens(args))))
    payload = json.dumps(targets, ensure_ascii=False, separators=(",", ":"))
    digest = hashlib.sha256(payload.encode("utf-8")).hexdigest()[:12]
    return f"tests-partial-{digest}"


def _is_acceptance_run(args: Sequence[str]) -> bool:
    """Recognize the closed acceptance shape independently of full-suite IDs."""

    # V14: removing strip must make the whitespace-only deletion-gate control red.
    if os.environ.get("PYTEST_ADDOPTS", "").strip():
        return False
    if os.environ.get("PYTEST_PLUGINS", "").strip():
        return False
    default_target = Path(_DEFAULT_TARGET).resolve()
    positional_count = 0
    i = 0
    while i < len(args):
        token = args[i]
        option, separator, value = token.partition("=")
        if token == "--" or option in _NO_EXECUTION_FLAGS or option in _SELECT_FLAGS:
            return False
        if option in _FULL_SUITE_DISQUALIFY_VALUE_OPTIONS:
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
            positional_count += 1
            if positional_count > 1:
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


def _is_scoped_acceptance_run(args: Sequence[str]) -> bool:
    """Recognize only the launcher-bound positional scoped target list."""
    marker = os.environ.get("IZANAGI_SCOPED_ACCEPTANCE_TARGETS_SHA256")
    if not marker or re.fullmatch(r"[0-9a-f]{64}", marker) is None:
        return False
    if os.environ.get("PYTEST_ADDOPTS", "").strip() or os.environ.get("PYTEST_PLUGINS", "").strip():
        return False
    targets = []
    for token in args:
        if token.startswith("-"):
            return False
        path, separator, node = token.partition("::")
        try:
            relative = Path(path).resolve().relative_to(Path(_REPO).resolve()).as_posix()
        except (OSError, ValueError):
            return False
        if (not Path(relative).name.startswith("test_")
                or not relative.endswith(".py") or separator and not node):
            return False
        targets.append(relative + (separator + node if separator else ""))
    if not targets or targets != sorted(set(targets)):
        return False
    payload = json.dumps(targets, ensure_ascii=False, separators=(",", ":"))
    return hashlib.sha256(payload.encode()).hexdigest() == marker


def _is_receipted_acceptance_run(args: Sequence[str]) -> bool:
    return _is_acceptance_run(args) or _is_scoped_acceptance_run(args)


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
    if not _is_receipted_acceptance_run(args):
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

    if not _is_receipted_acceptance_run(args):
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
    if not _is_receipted_acceptance_run(args):
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
    *, run_growth_held_tests: bool = False,
) -> tuple[str, str]:
    """Derive a privacy-safe suite kind/ID from wrapper inputs only."""

    addopts = os.environ.get("PYTEST_ADDOPTS") if pytest_addopts is None else pytest_addopts
    suffix = "-growth-held-opt-in" if run_growth_held_tests else ""
    if _is_full_suite(args, addopts):
        return "full", f"pytest-orchestrator-full{suffix}"
    projection = {
        "args": _normalized_fingerprint_args(args),
        # Selection text is reduced to a digest before entering the projection.
        "addopts_digest": (
            hashlib.sha256(addopts.encode("utf-8")).hexdigest()[:12]
            if addopts and addopts.strip() else None
        ),
    }
    raw = json.dumps(projection, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return "targeted", f"pytest-targeted-{hashlib.sha256(raw).hexdigest()[:12]}{suffix}"


def _growth_held_tests_opted_in(environ: Mapping[str, str]) -> bool:
    return environ.get(_RUN_GROWTH_HELD_TESTS_ENV) == _RUN_GROWTH_HELD_TESTS_TOKEN


def _emit_recording_diagnostic(diagnostic: Optional[str]) -> None:
    """Emit one fixed task-run diagnostic without exposing exception details."""

    if (
        not isinstance(diagnostic, str)
        or (
            not diagnostic.startswith("recording-unavailable:")
            and not diagnostic.startswith("pilot-closed:")
        )
    ):
        return
    try:
        print(
            f"IZANAGI_TASK_RUN_DIAGNOSTIC_V1 {diagnostic}",
            file=sys.stderr,
            flush=True,
        )
    except Exception:
        # Diagnostics are fail-open too; never replace the child result.
        pass


class _RecordingSession:
    """Lazy owner for one manual or automatic wrapper observation."""

    def __init__(
        self,
        repo_root: Path = Path(_REPO),
        task_run_id: Optional[str] = None,
    ) -> None:
        self.repo_root = Path(repo_root)
        self.task_run_id = (
            os.environ.get(_TASK_RUN_ID_ENV)
            if task_run_id is None else task_run_id
        )
        self._start_attempted = False
        self._automatic_run: Any = None
        self._finish_attempted = False
        self._manual_sidecar_path: Optional[Path] = None
        self._manual_sidecar_required = False
        self._diagnostics_emitted: set[str] = set()

    @property
    def is_manual(self) -> bool:
        return bool(self.task_run_id)

    @property
    def recording_enabled(self) -> bool:
        return self.is_manual or os.environ.get(_TASK_RUN_AUTO_RECORD_ENV) != "0"

    @property
    def sidecar_path(self) -> Optional[Path]:
        if self._automatic_run is None:
            return self._manual_sidecar_path
        value = getattr(self._automatic_run, "sidecar_path", None)
        return None if value is None else Path(value)

    @property
    def automatic_run(self) -> Any:
        return self._automatic_run

    @property
    def root(self) -> Path:
        if self._automatic_run is not None:
            return Path(self._automatic_run.generation_root)
        return Path(os.environ.get(
            _TASK_RUNS_ROOT_ENV, os.path.join(_REPO, "output", "task-runs"),
        ))

    @property
    def effective_task_run_id(self) -> Optional[str]:
        if self._automatic_run is not None:
            return str(self._automatic_run.task_run_id)
        return self.task_run_id

    @property
    def trigger(self) -> str:
        # An automatic observation deliberately never inherits the manual
        # trigger classification from its parent environment.
        if not self.is_manual:
            return "unspecified"
        trigger = os.environ.get(_TEST_TRIGGER_ENV, "unspecified")
        return trigger if trigger in _TRIGGERS else "unspecified"

    def ensure_started(self) -> None:
        """Resolve automatic recording exactly once, immediately before a child."""

        if self._start_attempted:
            return
        self._start_attempted = True
        if self.is_manual or os.environ.get(_TASK_RUN_AUTO_RECORD_ENV) == "0":
            return
        try:
            from tools.task_runs import start_automatic_test_run

            run, diagnostic = start_automatic_test_run(self.repo_root)
        except Exception:
            run, diagnostic = None, "recording-unavailable:filesystem"
        if diagnostic is None and run is None:
            diagnostic = "recording-unavailable:filesystem"
        if diagnostic is not None:
            self._emit(diagnostic)
        self._automatic_run = run

    def _emit(self, diagnostic: Optional[str]) -> None:
        if not isinstance(diagnostic, str) or diagnostic in self._diagnostics_emitted:
            return
        self._diagnostics_emitted.add(diagnostic)
        _emit_recording_diagnostic(diagnostic)

    def child_environment(
        self, base: Optional[Mapping[str, str]] = None,
    ) -> dict[str, str]:
        """Return a child environment with nested automatic recording disabled."""

        child_env = dict(os.environ if base is None else base)
        child_env[_TASK_RUN_AUTO_RECORD_ENV] = "0"
        child_env.pop(_TASK_RUN_SIDECAR_ENV, None)
        if self._automatic_run is not None:
            child_env.pop(_TASK_RUN_ID_ENV, None)
            child_env.pop(_TASK_RUNS_ROOT_ENV, None)
            sidecar = self.sidecar_path
            if sidecar is not None:
                child_env[_TASK_RUN_SIDECAR_ENV] = str(sidecar)
        elif self._manual_sidecar_path is not None:
            child_env[_TASK_RUN_SIDECAR_ENV] = str(self._manual_sidecar_path)
        return child_env

    def set_manual_sidecar(self, path: Optional[Path]) -> None:
        self._manual_sidecar_path = path
        self._manual_sidecar_required = True

    def record(
        self, *, suite_id: str, suite_kind: str, duration_s: float,
        exit_status: int,
    ) -> tuple[bool, Optional[str]]:
        task_run_id = self.effective_task_run_id
        if task_run_id is None:
            return False, None
        sidecar = self.sidecar_path
        try:
            result = _record_task_run(
                task_run_id=task_run_id,
                root=self.root,
                suite_id=suite_id,
                suite_kind=suite_kind,
                duration_s=duration_s,
                exit_status=exit_status,
                trigger=self.trigger,
                sidecar=sidecar,
                sidecar_required=(
                    self._automatic_run is not None
                    or self._manual_sidecar_required
                ),
            )
        except Exception:
            result = (False, "recording-unavailable:filesystem")
        if not isinstance(result, tuple) or len(result) != 2:
            result = (True, None)
        self._emit(result[1])
        return result

    def finish(self, outcome: str) -> None:
        if self._automatic_run is None or self._finish_attempted:
            return
        self._finish_attempted = True
        try:
            from tools.task_runs import finish_automatic_test_run

            diagnostic = finish_automatic_test_run(self._automatic_run, outcome)
        except Exception:
            diagnostic = "recording-unavailable:finish"
        self._emit(diagnostic)


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
    sidecar_required: bool = False,
) -> tuple[bool, Optional[str]]:
    """Best-effort single E1 call, returning only fixed diagnostics."""

    counts = None
    digest = None
    sidecar_diagnostic: Optional[str] = None
    if _REPO not in sys.path:
        sys.path.insert(0, _REPO)
    if sidecar is not None or sidecar_required:
        try:
            from tools.task_runs.pytest_stats import read_sidecar

            stats = None if sidecar is None else read_sidecar(sidecar)
            if stats is not None:
                counts, digest = stats
            else:
                sidecar_diagnostic = "recording-unavailable:sidecar"
        except Exception:
            sidecar_diagnostic = "recording-unavailable:sidecar"
    try:
        from tools.task_runs import record_test_run

        record_test_run(
            root, task_run_id, suite_id=suite_id, suite_kind=suite_kind,
            duration_s=duration_s, exit_status=exit_status, counts=counts,
            trigger=trigger, collected_node_digest=digest,
        )
    except Exception:
        return False, "recording-unavailable:filesystem"
    return True, sidecar_diagnostic


def _call_and_record(
    cmd: Sequence[str], args: Sequence[str], task_run_id: Optional[str] = None,
    *, recording_session: Optional[_RecordingSession] = None,
) -> int:
    session = recording_session or _RecordingSession(task_run_id=task_run_id)
    recording_ready = True
    try:
        suite_kind, suite_id = _suite_identity(
            args,
            run_growth_held_tests=_growth_held_tests_opted_in(os.environ),
        )
    except Exception:
        recording_ready = False
        suite_kind, suite_id = "targeted", "pytest-targeted-unavailable"
    sidecar_dir: Optional[Path] = None
    sidecar: Optional[Path] = None
    try:
        if session.is_manual:
            sidecar_dir, sidecar = _private_sidecar()
    except Exception:
        sidecar_dir = None
        sidecar = None
    if session.is_manual:
        session.set_manual_sidecar(sidecar)

    try:
        try:
            started = time.monotonic()
        except Exception:
            started = None
            recording_ready = False
        # This is the direct-route child boundary: lazy automatic bootstrap is
        # deliberately the last recording operation before the child process
        # is started.  Environment construction is part of the call argument
        # evaluation, so the automatic task-run cannot precede it.
        session.ensure_started()
        rc = subprocess.call(
            list(cmd), env=session.child_environment(), cwd=_REPO,
        )
        if started is not None:
            try:
                duration_s = time.monotonic() - started
            except Exception:
                recording_ready = False
                duration_s = 0.0
        else:
            duration_s = 0.0
        if recording_ready:
            session.record(
                suite_id=suite_id,
                suite_kind=suite_kind,
                duration_s=duration_s,
                exit_status=rc,
            )
        elif session.recording_enabled:
            session._emit("recording-unavailable:filesystem")
        session.finish("completed")
        return rc
    finally:
        if sidecar_dir is not None:
            try:
                shutil.rmtree(sidecar_dir)
            except Exception:
                pass


def _dispatch_environment(
    recording_session: Optional[_RecordingSession] = None,
) -> dict[str, str]:
    """計算ノード子へ渡す環境から親だけが所有する台帳状態を除く。"""

    child_env = os.environ.copy()
    child_env.pop(_TASK_RUN_ID_ENV, None)
    child_env.pop(_TASK_RUN_SIDECAR_ENV, None)
    child_env.pop(_TASK_RUNS_ROOT_ENV, None)
    child_env[_TASK_RUN_AUTO_RECORD_ENV] = "0"
    if recording_session is not None:
        sidecar = recording_session.sidecar_path
        if sidecar is not None:
            child_env[_TASK_RUN_SIDECAR_ENV] = str(sidecar)
    return child_env


def _default_dispatch(
    args: Sequence[str], *, environ: dict[str, str],
    artifact_root: Optional[Path] = None,
    control_root: Optional[Path] = None,
    nonce: Optional[str] = None,
    intent_registry_root: Optional[Path] = None,
    intent_group_id: Optional[str] = None,
    intent_shard_index: Optional[int] = None,
    deadline_at: Optional[float] = None,
) -> int:
    """テスト用に dispatch の walltime を環境変数で短縮できる。"""
    from tools.pegasus import dispatch_compute

    dispatch_kwargs = {
        "task": "tests",
        "repo_root": Path(_REPO),
        "environ": environ,
    }
    if artifact_root is not None or control_root is not None:
        if artifact_root is None or control_root is None:
            raise ValueError("artifact_root / control_root must be specified together")
        dispatch_kwargs["artifact_root"] = artifact_root
        dispatch_kwargs["control_root"] = control_root
    if nonce is not None:
        dispatch_kwargs["nonce"] = nonce
    intent_values = (
        intent_registry_root, intent_group_id, intent_shard_index,
    )
    if any(value is not None for value in intent_values):
        if not all(value is not None for value in intent_values):
            raise ValueError("intent registry arguments must be specified together")
        dispatch_kwargs["intent_registry_root"] = intent_registry_root
        dispatch_kwargs["intent_group_id"] = intent_group_id
        dispatch_kwargs["intent_shard_index"] = intent_shard_index
    if deadline_at is not None:
        dispatch_kwargs["deadline_at"] = deadline_at
    walltime = environ.get(_DISPATCH_WALLTIME_OVERRIDE_ENV)
    if walltime:
        dispatch_kwargs["walltime"] = walltime
    queue_wait_timeout = environ.get(_DISPATCH_QUEUE_WAIT_TIMEOUT_OVERRIDE_ENV)
    if queue_wait_timeout:
        queue_wait_timeout_s = float(queue_wait_timeout)
        if (
            not math.isfinite(queue_wait_timeout_s)
            or queue_wait_timeout_s < 0
            or math.copysign(1.0, queue_wait_timeout_s) < 0
        ):
            raise ValueError(
                f"{_DISPATCH_QUEUE_WAIT_TIMEOUT_OVERRIDE_ENV} は"
                "有限な非負数でなければなりません"
            )
        dispatch_kwargs["queue_wait_timeout_s"] = queue_wait_timeout_s
    overall_grace = environ.get(_DISPATCH_OVERALL_GRACE_OVERRIDE_ENV)
    if overall_grace:
        overall_grace_s = float(overall_grace)
        if (
            not math.isfinite(overall_grace_s)
            or overall_grace_s < 0
            or math.copysign(1.0, overall_grace_s) < 0
        ):
            raise ValueError(
                f"{_DISPATCH_OVERALL_GRACE_OVERRIDE_ENV} は"
                "有限な非負数でなければなりません"
            )
        dispatch_kwargs["overall_grace_s"] = overall_grace_s
    result = dispatch_compute.dispatch(args, **dispatch_kwargs)
    return result


def _parse_collect_only_nodeids(stdout: str) -> tuple[str, ...]:
    """pytest ``--collect-only -q`` の nodeid 行だけを repo-relative にする。"""

    repo = Path(_REPO).resolve()
    default_target = Path(_DEFAULT_TARGET).resolve()
    nodeids: list[str] = []
    for raw_line in stdout.splitlines():
        line = raw_line.strip()
        path_text, separator, suffix = line.partition("::")
        if not separator or not suffix or not path_text.endswith(".py"):
            continue
        path = Path(path_text)
        if not path.is_absolute():
            path = repo / path
        try:
            resolved = path.resolve(strict=False)
            resolved.relative_to(default_target)
            relative = resolved.relative_to(repo).as_posix()
        except (OSError, ValueError):
            continue
        nodeids.append(f"{relative}::{suffix}")
    if not nodeids or len(nodeids) != len(set(nodeids)):
        raise ValueError("collect-only output did not contain a unique non-empty universe")
    return tuple(sorted(nodeids))


def _collect_login_universe(
    session_root: Path,
    exclusions: Sequence[_PermanentExclusion],
    deadline_at: float,
) -> tuple[int, tuple[str, ...]]:
    """compute shard と並行に login 親で独立の U を観測する。"""

    from tools import acceptance_shards

    command = [
        sys.executable,
        "-m",
        "pytest",
        *_SELECTION_CONTRACT.exclusion_tokens(exclusions),
        _DEFAULT_TARGET,
        "--collect-only",
        "-q",
        "-p",
        "no:cacheprovider",
    ]
    child_env = _dispatch_environment()
    child_env.pop(_ACCEPTANCE_SHARDS_ENV, None)
    child_env.pop(acceptance_shards.PLUGIN_SPEC_ENV, None)
    if exclusions:
        child_env[_RUNNER_EXCLUSION_ENV] = _SELECTION_CONTRACT.serialize_payload(
            exclusions
        )
    else:
        child_env.pop(_RUNNER_EXCLUSION_ENV, None)
    try:
        timeout = deadline_at - time.monotonic()
        if not math.isfinite(timeout) or timeout <= 0:
            return _PEGASUS_DISPATCH_RC, ()
        result = _call_with_runner_exclusions(
            exclusions,
            subprocess.run,
            command,
            cwd=_REPO,
            capture_output=True,
            text=True,
            check=False,
            env=child_env,
            timeout=timeout,
        )
        log = (
            "command=" + json.dumps(command, ensure_ascii=True) + "\n"
            + "stdout:\n" + result.stdout + "\nstderr:\n" + result.stderr
        ).encode("utf-8", errors="replace")
        acceptance_shards._write_bytes_create_only(
            session_root / "login-collection.log", log,
        )
        if result.returncode != 0:
            return _PEGASUS_DISPATCH_RC, ()
        return 0, _parse_collect_only_nodeids(result.stdout)
    except (OSError, subprocess.TimeoutExpired, TypeError, ValueError):
        return _PEGASUS_DISPATCH_RC, ()


def _run_internal_acceptance_shard(
    spec: object,
    *,
    resolved_site: str,
    args: Sequence[str],
    exclusions: Sequence[_PermanentExclusion],
) -> int:
    """計算ノードで既定 suite root を全 collection して担当外を deselect する。"""

    from tools import acceptance_shards

    if not isinstance(spec, acceptance_shards.InternalSpec):
        return _PEGASUS_DISPATCH_RC
    repo = Path(_REPO).resolve()
    session = spec.session_root.resolve()
    try:
        expected_shared_root = acceptance_shards.shared_root_for_repo(repo)
    except acceptance_shards.ShardError:
        return _PEGASUS_DISPATCH_RC
    if (
        resolved_site != site_policy.PEGASUS_COMPUTE
        or list(args)
        or spec.shard_count not in {2, 3}
        or spec.shard_index not in range(spec.shard_count)
        or acceptance_shards._is_within(session, repo)
        or session.parent != expected_shared_root
        or not spec.shard_root.is_dir()
    ):
        return _PEGASUS_DISPATCH_RC
    version = _xdist_version()
    if not (
        _xdist_supports_loadgroup(version)
        and _xdist_runtime_importable()
    ):
        return _PEGASUS_DISPATCH_RC
    command = _build_pytest_command(
        [
            f"--junitxml={spec.junit_path}",
            "-p",
            "tools.acceptance_shards",
            "-p",
            "no:cacheprovider",
        ],
        use_xdist=True,
        default_nproc=_default_nproc(site=resolved_site),
        has_target=False,
        default_target=_DEFAULT_TARGET,
        exclusions=exclusions,
    )
    child_env = os.environ.copy()
    child_env.pop(_ACCEPTANCE_SHARDS_ENV, None)
    if exclusions:
        child_env[_RUNNER_EXCLUSION_ENV] = _SELECTION_CONTRACT.serialize_payload(
            exclusions
        )
    else:
        child_env.pop(_RUNNER_EXCLUSION_ENV, None)
    child_env[acceptance_shards.PLUGIN_SPEC_ENV] = json.dumps(
        {
            "session_root": str(session),
            "shard_count": spec.shard_count,
            "shard_index": spec.shard_index,
        },
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    )
    return _call_with_runner_exclusions(
        exclusions,
        subprocess.call,
        command,
        cwd=_REPO,
        env=child_env,
    )


def _invoke_dispatch(
    dispatch_fn,
    args: Sequence[str],
    *,
    environ: dict[str, str],
) -> _DispatchCallResult:
    """dispatcher の想定外例外も top-level infra rc へ一義化する。"""

    try:
        result = dispatch_fn(args, environ=environ)
    except Exception:
        _emit_recording_diagnostic("recording-unavailable:dispatch")
        return _DispatchCallResult(_PEGASUS_DISPATCH_RC, False)
    try:
        rc = int(result)
    except (TypeError, ValueError):
        _emit_recording_diagnostic("recording-unavailable:dispatch")
        return _DispatchCallResult(_PEGASUS_DISPATCH_RC, False)
    # Receipt evidence is deliberately fail-closed: absent, non-bool, or
    # false is never promoted to "child started".  An infra rc is also not a
    # pytest-child observation, even if an older dispatcher labelled it true
    # after qsub accepted the job.
    try:
        marker = getattr(result, "child_started", None)
    except Exception:
        marker = None
    child_started = (
        type(marker) is bool
        and marker is True
        and rc != _PEGASUS_DISPATCH_RC
    )
    return _DispatchCallResult(rc, child_started)


def _dispatch_and_record(
    dispatch_fn,
    args: Sequence[str],
    task_run_id: Optional[str] = None,
    *,
    environ: dict[str, str],
    recording_session: Optional[_RecordingSession] = None,
) -> int:
    """親の wall time と最終 rc を task_run へ一度だけ記録する。"""

    session = recording_session or _RecordingSession(task_run_id=task_run_id)
    recording_ready = True
    try:
        suite_kind, suite_id = _suite_identity(
            args,
            run_growth_held_tests=_growth_held_tests_opted_in(environ),
        )
    except Exception:
        recording_ready = False
        suite_kind, suite_id = "targeted", "pytest-targeted-unavailable"
    try:
        started = time.monotonic()
    except Exception:
        started = None
        recording_ready = False
    # This is the dispatch-route receipt boundary.  Automatic bootstrap is
    # intentionally deferred until the dispatcher has returned a strict
    # positive child-start receipt.
    environ = dict(environ)
    environ[_TASK_RUN_AUTO_RECORD_ENV] = "0"
    environ.pop(_TASK_RUN_ID_ENV, None)
    environ.pop(_TASK_RUNS_ROOT_ENV, None)
    if session.sidecar_path is not None:
        environ[_TASK_RUN_SIDECAR_ENV] = str(session.sidecar_path)
    else:
        environ.pop(_TASK_RUN_SIDECAR_ENV, None)
    dispatch_result = _invoke_dispatch(dispatch_fn, args, environ=environ)
    rc = dispatch_result.rc
    if started is not None:
        try:
            duration_s = time.monotonic() - started
        except Exception:
            duration_s = 0.0
            recording_ready = False
    else:
        duration_s = 0.0
    if not dispatch_result.child_started and not session.is_manual:
        session._emit("recording-unavailable:dispatch-no-child")
    elif recording_ready:
        session.ensure_started()
        session.record(
            suite_id=suite_id,
            suite_kind=suite_kind,
            duration_s=duration_s,
            exit_status=rc,
        )
    elif session.recording_enabled:
        session._emit("recording-unavailable:filesystem")
    session.finish("completed")
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
    except Exception as exc:
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
    except Exception:
        pass


def _safe_release_grant(grant) -> None:
    if grant is None:
        return
    try:
        release = getattr(grant, "release", None)
        if callable(release):
            release()
    except Exception:
        pass


def _safe_remember_peak(module, operation: Optional[str], peak: Optional[int]) -> None:
    if module is None or operation is None or peak is None:
        return
    try:
        module.remember_peak(operation, peak)
    except Exception:
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
    except Exception:
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
    accepted_memory_max = {str(cap)}
    if cap > 0:
        try:
            page_size = os.sysconf("SC_PAGE_SIZE")
        except (OSError, ValueError):
            pass
        else:
            if type(page_size) is int and page_size > 0:
                accepted_memory_max.add(str(cap - cap % page_size))
    return memory_max in accepted_memory_max and oom_group == "1"


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


def _has_valid_bounded_scope_marker() -> bool:
    """実 bounded 親の形式に一致する marker pair だけを警告抑止に使う。"""

    unit = os.environ.get(_BOUNDED_SCOPE_UNIT_ENV)
    raw_cap = os.environ.get(_BOUNDED_SCOPE_CAP_ENV)
    if unit is None or raw_cap is None:
        return False
    token_length = _BOUNDED_SCOPE_TOKEN_BYTES * 2
    if re.fullmatch(
        rf"{re.escape(_BOUNDED_SCOPE_UNIT_PREFIX)}[1-9][0-9]*-"
        rf"[0-9a-f]{{{token_length}}}\.scope",
        unit,
    ) is None:
        return False
    if not raw_cap.isascii() or not raw_cap.isdecimal():
        return False
    cap = int(raw_cap, 10)
    return cap > 0 and raw_cap == str(cap)


def _new_scope_unit() -> str:
    token = secrets.token_hex(_BOUNDED_SCOPE_TOKEN_BYTES)
    return f"{_BOUNDED_SCOPE_UNIT_PREFIX}{os.getpid()}-{token}.scope"


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


def _run_bounded_scope(
    args: Sequence[str], cap: int,
    *, recording_session: Optional[_RecordingSession] = None,
) -> _ScopeResult:
    unit = _new_scope_unit()
    # task_run は scope 親が結果確定後に所有する。子へ渡すと CAP_OOM 後の
    # compute fallback と二重記録になり得る。
    session = recording_session or _RecordingSession()
    # Popen と scope attestation が成功するまでは task-run を作らない。
    # 失敗時は scope diagnostic だけを返し、cap を消費する空の task を残さない。
    child_env = _dispatch_environment(session)
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

    session.ensure_started()
    # Keep the injected mapping coherent for tests and callers that inspect the
    # launch environment after a successful Popen.  A real Popen has already
    # copied its environment; missing late transport is fail-open and is
    # reported by the normal sidecar diagnostic path.
    child_env.clear()
    child_env.update(_dispatch_environment(session))
    child_env[_BOUNDED_SCOPE_UNIT_ENV] = unit
    child_env[_BOUNDED_SCOPE_CAP_ENV] = str(cap)

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


def _scope_recording_diagnostic(result: _ScopeResult) -> str:
    code = {
        _ScopeOutcome.CAP_OOM: "cap-oom",
        _ScopeOutcome.HEADROOM_SHORT: "headroom-short",
        _ScopeOutcome.DISPATCH_INFRA: "dispatch-infra",
    }.get(result.outcome, result.outcome.value.replace("_", "-"))
    return f"recording-unavailable:scope-outcome-{code}"


def _run_bounded_scope_and_record(
    args: Sequence[str], cap: int,
    *, recording_session: Optional[_RecordingSession] = None,
) -> _ScopeResult:
    session = recording_session or _RecordingSession()
    if not session.is_manual and not session.recording_enabled:
        # Explicit opt-out retains the pre-existing plain scope route.
        return _run_bounded_scope(args, cap, recording_session=session)
    recording_ready = True
    try:
        suite_kind, suite_id = _suite_identity(
            args,
            run_growth_held_tests=_growth_held_tests_opted_in(os.environ),
        )
    except Exception:
        recording_ready = False
        suite_kind, suite_id = "targeted", "pytest-targeted-unavailable"
    try:
        started = time.monotonic()
    except Exception:
        started = None
        recording_ready = False
    result = _run_bounded_scope(args, cap, recording_session=session)
    if result.outcome is not _ScopeOutcome.CHILD_RC:
        # R-B4SCOPE: a scope outcome without CHILD_RC is not a pytest
        # observation.  Keep only the fixed diagnostic; main() decides later
        # whether a CAP_OOM fallback dispatch will reuse this session.
        if session.recording_enabled:
            _emit_recording_diagnostic(_scope_recording_diagnostic(result))
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
        assert result.child_rc is not None
        session.record(
            suite_id=suite_id,
            suite_kind=suite_kind,
            duration_s=duration_s,
            exit_status=result.child_rc,
        )
    elif session.recording_enabled:
        _emit_recording_diagnostic("recording-unavailable:filesystem")
    return result


def _tree_and_submodules_fingerprint(
    repo: Path | str,
) -> Optional[_TreeFingerprint]:
    """Hash worktree/index and recursive submodule state; fail closed.

    Status output captures untracked-path membership, while binary diffs also
    distinguish edits to paths that were already dirty before the local run.
    Recursive submodule HEAD/status/diff output is part of the same digest.
    """

    repo_path = Path(repo).resolve()
    commands = (
        (
            "status",
            [
                "git", "-C", str(repo_path), "status", "--porcelain=v1", "-z",
                "--untracked-files=all", "--ignore-submodules=none",
            ],
        ),
        (
            "diff",
            [
                "git", "-C", str(repo_path), "diff", "--binary",
                "--no-ext-diff", "HEAD", "--",
            ],
        ),
        (
            "submodule-heads",
            [
                "git", "-C", str(repo_path), "submodule", "status",
                "--recursive",
            ],
        ),
        (
            "submodule-status",
            [
                "git", "-C", str(repo_path), "submodule", "foreach",
                "--recursive", "--quiet",
                "git status --porcelain=v1 -z --untracked-files=all",
            ],
        ),
        (
            "submodule-diff",
            [
                "git", "-C", str(repo_path), "submodule", "foreach",
                "--recursive", "--quiet",
                "git diff --binary --no-ext-diff HEAD --",
            ],
        ),
    )
    fingerprint = hashlib.sha256()
    summary: list[int] = []
    for label, command in commands:
        try:
            env = _git_env()
            env["GIT_OPTIONAL_LOCKS"] = "0"
            result = subprocess.run(
                command,
                capture_output=True,
                env=env,
                timeout=120,
            )
        except (OSError, subprocess.TimeoutExpired):
            return None
        if result.returncode != 0 or not isinstance(result.stdout, bytes):
            return None
        label_bytes = label.encode("ascii")
        fingerprint.update(len(label_bytes).to_bytes(2, "big"))
        fingerprint.update(label_bytes)
        fingerprint.update(len(result.stdout).to_bytes(8, "big"))
        fingerprint.update(result.stdout)
        summary.append(len(result.stdout))
    return _TreeFingerprint(fingerprint.hexdigest(), tuple(summary))


def _cap_oom_fingerprint_refusal(
    before: Optional[_TreeFingerprint],
    after: Optional[_TreeFingerprint],
) -> int:
    if before is None or after is None:
        detail = (
            "local 試行前後の tree / submodule 指紋を安全に取得できませんでした"
            f"（before={'ok' if before is not None else 'failed'}、"
            f"after={'ok' if after is not None else 'failed'}）"
        )
    else:
        detail = (
            "local 試行の前後で tree / submodule 状態が変化しました"
            f"（digest {before.digest[:12]} -> {after.digest[:12]}、"
            f"各状態出力 bytes {before.summary} -> {after.summary}）"
        )
    print(
        "bounded scope が MemoryMax に達しましたが、"
        f"{detail}。自動 fallback せず停止します。git status と "
        "git submodule status --recursive で差分を確認してください。",
        file=sys.stderr,
        flush=True,
    )
    return _PEGASUS_DISPATCH_RC


def _dispatch_result(
    dispatch_fn,
    args: Sequence[str],
    *, recording_session: Optional[_RecordingSession] = None,
    shard_count: int = 1,
    exclusions: Sequence[_PermanentExclusion] = (),
) -> int:
    selected_dispatch = _default_dispatch if dispatch_fn is None else dispatch_fn
    if shard_count > 1:
        from tools import acceptance_shards

        underlying = selected_dispatch

        def selected_dispatch(
            original_args: Sequence[str], *, environ: dict[str, str],
        ) -> int:
            if list(original_args):
                return acceptance_shards.CompositeResult(
                    _PEGASUS_DISPATCH_RC, child_started=False,
                )

            def dispatch_call(
                internal_args: Sequence[str], *, artifact_root: Path,
                control_root: Path, nonce: str, intent_registry_root: Path,
                intent_group_id: str, intent_shard_index: int,
                deadline_at: float,
            ):
                shard_environ = dict(environ)
                shard_environ.pop(_TASK_RUN_SIDECAR_ENV, None)
                shard_environ[_TASK_RUN_AUTO_RECORD_ENV] = "0"
                return underlying(
                    internal_args,
                    environ=shard_environ,
                    artifact_root=artifact_root,
                    control_root=control_root,
                    nonce=nonce,
                    intent_registry_root=intent_registry_root,
                    intent_group_id=intent_group_id,
                    intent_shard_index=intent_shard_index,
                    deadline_at=deadline_at,
                )

            return acceptance_shards.run_parallel(
                repo=Path(_REPO),
                shard_count=shard_count,
                dispatch_call=dispatch_call,
                collect_login=lambda session, deadline_at: _collect_login_universe(
                    session, exclusions, deadline_at,
                ),
                deadline_at=time.monotonic() + _ACCEPTANCE_SHARD_DEADLINE_S,
            )

    session = recording_session or _RecordingSession()
    if not session.is_manual and not session.recording_enabled:
        # Explicit opt-out retains the pre-existing plain dispatch route while
        # _dispatch_environment still installs the nested-run marker.
        return _invoke_dispatch(
            selected_dispatch, args, environ=_dispatch_environment(session),
        ).rc
    child_env = _dispatch_environment(session)
    return _dispatch_and_record(
        selected_dispatch,
        args,
        session.task_run_id,
        environ=child_env,
        recording_session=session,
    )


def _launch_local_scope(
    args: Sequence[str], cap: int, *, module=None, operation=None, grant=None,
    recording_session: Optional[_RecordingSession] = None,
):
    accounting = (
        _ScopeAccounting(module, operation, grant)
        if module is not None and operation is not None
        else None
    )
    token = _scope_accounting.set(accounting)
    try:
        return _run_bounded_scope_and_record(
            args, cap, recording_session=recording_session,
        )
    finally:
        _scope_accounting.reset(token)


def main(
    argv: Optional[Sequence[str]] = None,
    *,
    site: Optional[str] = None,
    dispatch_fn=None,
    admit_fn=None,
) -> int:
    raw_args = list(sys.argv[1:] if argv is None else argv)
    pytest_args, force_dispatch = _consume_runner_options(raw_args)
    try:
        pytest_args, internal_shard_spec = _consume_internal_shard_spec(pytest_args)
        shard_request = _acceptance_shard_request()
    except (OSError, TypeError, ValueError) as exc:
        print(
            f"acceptance shard 指定を受理できません: {exc}",
            file=sys.stderr,
            flush=True,
        )
        return _PEGASUS_DISPATCH_RC
    args = _normalize_args(pytest_args)
    is_acceptance = _is_receipted_acceptance_run(args)
    positional = _positional_tokens(args)
    try:
        configured_exclusions = tuple(_PERMANENT_FULL_SUITE_EXCLUSIONS)
    except TypeError:
        print(
            "恒久除外表が裁定済み literal path と一致しないため、"
            "テスト command を作らず停止します。",
            file=sys.stderr,
            flush=True,
        )
        return _PERMANENT_EXCLUSION_GATE_RC
    canonical_exclusions = _permanent_exclusions_are_sanctioned(
        configured_exclusions
    )
    if canonical_exclusions is None:
        print(
            "恒久除外表が裁定済み literal path と一致しないため、"
            "テスト command を作らず停止します。",
            file=sys.stderr,
            flush=True,
        )
        return _PERMANENT_EXCLUSION_GATE_RC
    exclusions = canonical_exclusions if is_acceptance else ()
    if is_acceptance and _has_non_loadgroup_user_dist(args):
        print(
            "受入形では --dist loadgroup 以外の --dist 上書きを拒否します。",
            file=sys.stderr,
            flush=True,
        )
        return _ACCEPTANCE_DIST_OVERRIDE_RC
    if not is_acceptance and not _has_valid_bounded_scope_marker():
        print(
            "警告: 受入形でない走行です。この結果を受入全走として扱わないでください。",
            file=sys.stderr,
            flush=True,
        )
    _print_runner_help(args)
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

    try:
        shard_count = _resolve_acceptance_shard_count(
            shard_request,
            is_acceptance=is_acceptance,
            resolved_site=resolved_site,
            raw_args=raw_args,
            force_dispatch=force_dispatch,
            internal_shard_spec=internal_shard_spec,
            positional=positional,
            bounded_membership=bounded_membership,
        )
    except ValueError:
        print(
            "明示 shard mode は空 argv の受入形かつ Pegasus LOGIN でのみ受理します。",
            file=sys.stderr,
            flush=True,
        )
        return _PEGASUS_DISPATCH_RC
    shard_mode = shard_count > 1
    explicit_shard_mode = shard_request in {2, 3} and shard_mode

    dispatch_exempt = _has_dispatch_exempt_flag(args)
    bounded_scope_exempt = _has_bounded_scope_exempt_flag(args)
    login_admission_dispatch = False
    if (
        bounded_membership is None
        and not bounded_scope_exempt
        and not force_dispatch
        and not explicit_shard_mode
        and internal_shard_spec is None
        and site_policy.is_pegasus_login(resolved_site)
    ):
        module, cap, admission_outcome, headroom_reason, grant = (
            _evaluate_login_admission(admit_fn, operation=operation)
        )
        queue_unavailable = False
        queue_reason = ""
        if admission_outcome is _ScopeOutcome.HEADROOM_SHORT:
            if admit_fn is None:
                queue_possible, queue_reason = _queue_dispatch_possible()
            else:
                # 裁定済みの test seam は admission 全体を決定的に注入する。
                queue_possible, queue_reason = True, "injected dispatch admission"
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
                login_admission_dispatch = True

        if admission_outcome is None:
            if cap is None:
                _safe_release_grant(grant)
                return _PEGASUS_DISPATCH_RC
            _print_granted_budget(cap, headroom_reason)
            tree_before = _tree_and_submodules_fingerprint(Path(_REPO))
            recording_session = _RecordingSession()
            try:
                scope_result = _call_with_runner_exclusions(
                    exclusions,
                    _launch_local_scope,
                    args,
                    cap,
                    module=module,
                    operation=operation,
                    grant=grant,
                    recording_session=recording_session,
                )
            finally:
                _safe_release_grant(grant)
            if scope_result.outcome is _ScopeOutcome.CHILD_RC:
                if scope_result.child_rc is None:
                    recording_session.finish("blocked")
                    return _PEGASUS_DISPATCH_RC
                recording_session.finish("completed")
                return scope_result.child_rc
            if scope_result.outcome is _ScopeOutcome.DISPATCH_INFRA:
                recording_session.finish("blocked")
                return _PEGASUS_DISPATCH_RC
            if scope_result.outcome is not _ScopeOutcome.CAP_OOM:
                recording_session.finish("blocked")
                return _PEGASUS_DISPATCH_RC
            tree_after = _tree_and_submodules_fingerprint(Path(_REPO))
            if (
                tree_before is None
                or tree_after is None
                or tree_before != tree_after
            ):
                recording_session.finish("blocked")
                return _cap_oom_fingerprint_refusal(tree_before, tree_after)
            if queue_unavailable:
                recording_session.finish("blocked")
                return _no_execution_capacity(headroom_reason, queue_reason)
            return _call_with_runner_exclusions(
                exclusions,
                _dispatch_result,
                dispatch_fn,
                args,
                recording_session=recording_session,
                shard_count=shard_count,
                exclusions=exclusions,
            )

    preflight_rc = _preflight_unstaged_deletions(args, Path(_REPO))
    if preflight_rc:
        return preflight_rc
    preflight_rc = _preflight_ruleops(args, Path(_REPO))
    if preflight_rc:
        return preflight_rc
    preflight_rc = _preflight_submodule(args, Path(_REPO))
    if preflight_rc:
        return preflight_rc

    if internal_shard_spec is not None:
        return _run_internal_acceptance_shard(
            internal_shard_spec,
            resolved_site=resolved_site,
            args=args,
            exclusions=exclusions,
        )

    if (
        (force_dispatch or not dispatch_exempt)
        and resolved_site == site_policy.PEGASUS_SUSPECT
    ):
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
    if site_policy.is_pegasus_login(resolved_site):
        if force_dispatch or shard_mode:
            return _call_with_runner_exclusions(
                exclusions,
                _dispatch_result,
                dispatch_fn,
                args,
                shard_count=shard_count,
                exclusions=exclusions,
            )
        if bounded_membership is True:
            pass
        elif login_admission_dispatch or not dispatch_exempt:
            return _call_with_runner_exclusions(
                exclusions, _dispatch_result, dispatch_fn, args,
                shard_count=shard_count,
                exclusions=exclusions,
            )

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
            and _has_non_loadgroup_user_dist(args)):
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
        exclusions=exclusions,
    )
    task_run_id = os.environ.get(_TASK_RUN_ID_ENV)
    if not task_run_id:
        if os.environ.get(_TASK_RUN_AUTO_RECORD_ENV) == "0":
            return _call_with_runner_exclusions(
                exclusions, subprocess.call, cmd, cwd=_REPO,
            )
        return _call_with_runner_exclusions(
            exclusions,
            _call_and_record,
            cmd,
            args,
            recording_session=_RecordingSession(),
        )
    return _call_with_runner_exclusions(
        exclusions,
        _call_and_record,
        cmd,
        args,
        task_run_id,
        recording_session=_RecordingSession(task_run_id=task_run_id),
    )


if __name__ == "__main__":
    sys.exit(main())
