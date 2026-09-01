# probe 逐語 (repo へ commit していない使い捨ての計測 probe)

本 wave の計測に使った probe の全文である。実装面であるため Codex `role=author` が書き、
親は実行だけを行った。repo 外 (`dev-wave-jobs/.../probe-runtime/`) に置いたまま commit していない。

```text
#!/usr/bin/env python3
"""T-2097 residual probe, arm runner, and artifact aggregation CLI."""

from __future__ import annotations

import argparse
import hashlib
import inspect
import json
import math
import os
import re
import socket
import statistics
import subprocess
import sys
import time
import xml.etree.ElementTree as ET
from collections import defaultdict
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

import pytest


SCHEMA = "izanagi-t2097-residual-summary/v1"
PROCESS_SCHEMA = "izanagi-t2097-residual-process/v1"
OUTER_SCHEMA = "izanagi-t2097-residual-outer/v1"
ARCHIVE_SCHEMA = "izanagi-t2097-residual-archive/v1"
CALIBRATION_KIND = "instrumented zero-selected calibration"
PLUGIN_ENV = "PYTEST_PLUGINS"
INJECTION_BACKUP_ENV = "IZANAGI_T2097_INJECTION_ENV_BACKUP"
CONTROLLER_IMPORT_MARKER = ".controller-import-owner"
MODE_ENV = "IZANAGI_T2097_MODE"
TIMING_ENV = "IZANAGI_T2097_TIMING"
OUTPUT_ENV = "IZANAGI_T2097_OUTPUT"
GROWTH_ENV = "IZANAGI_RUN_GROWTH_HELD_TESTS"
GROWTH_TOKEN = "explicit-user-command"
SHARD_SPEC_ENV = "IZANAGI_ACCEPTANCE_SHARD_PLUGIN_V1"
WALL_RE = re.compile(r"\bin ([0-9]+(?:[.][0-9]+)?)s\b")
WORKER_RE = re.compile(r"^gw[0-9]+$")
MAX_CLOCK_DRIFT_NS = 5_000_000
EXPECTED_AFFINITY = 48
EXPECTED_WORKERS = 48
EXPECTED_GROUP_KEYS = {
    1: frozenset({"dev-waves-runtime"}),
    2: frozenset({"p3-b4-material-report"}),
}
ARCHIVE_SESSION_PREFIXES = (
    "7ac4faab", "349543d5", "6f39928e", "690c10ec", "4524841d",
    "b6b39445", "bd617d36", "92a64a50", "68f13f48", "63bcb314",
    "ab716aea", "3125bcc7", "8410a1ac", "dd911f21",
)
ARM_SPECS = (
    ("R2-A1", 2, "none", "real"),
    ("R2-B1", 2, "timing", "real"),
    ("R1-B1", 1, "timing", "real"),
    ("R1-A1", 1, "none", "real"),
    ("R1-A2", 1, "none", "real"),
    ("R1-B2", 1, "timing", "real"),
    ("R2-B2", 2, "timing", "real"),
    ("R2-A2", 2, "none", "real"),
    ("Z-S1", 2, "selector", "zero"),
    ("Z-B1", 2, "timing", "zero"),
)
ARM_BY_NAME = {entry[0]: entry for entry in ARM_SPECS}
SAFE_TAG_RE = re.compile(r"^[A-Za-z0-9._-]+$")


def _now() -> dict[str, int]:
    return {"epoch_ns": time.time_ns(), "perf_ns": time.perf_counter_ns()}


def _environment_state() -> dict[str, dict[str, Any]]:
    result: dict[str, dict[str, Any]] = {}
    for name in ("PYTHONPATH", PLUGIN_ENV):
        present = name in os.environ
        result[name] = {
            "set": present,
            "value_sha256": (
                hashlib.sha256(os.environ[name].encode()).hexdigest()
                if present else "absent"
            ),
        }
    return result


def _restore_injected_environment(trigger: str) -> dict[str, Any]:
    backup_raw = os.environ.pop(INJECTION_BACKUP_ENV, None)
    backup: Any = None
    backup_error: str | None = None
    if backup_raw is None:
        backup_error = "backup-environment-missing"
    else:
        try:
            backup = json.loads(backup_raw)
        except (json.JSONDecodeError, TypeError) as exc:
            backup_error = f"backup-environment-invalid:{type(exc).__name__}"
    if not isinstance(backup, dict):
        backup = {}
    for name in ("PYTHONPATH", PLUGIN_ENV):
        saved = backup.get(name)
        if not isinstance(saved, dict) or not isinstance(saved.get("set"), bool):
            os.environ.pop(name, None)
            if backup_error is None:
                backup_error = f"backup-entry-invalid:{name}"
            continue
        if saved["set"]:
            value = saved.get("value")
            if isinstance(value, str):
                os.environ[name] = value
            else:
                os.environ.pop(name, None)
                if backup_error is None:
                    backup_error = f"backup-value-invalid:{name}"
        else:
            os.environ.pop(name, None)
    restored = _environment_state()
    production_mismatch = any(value["set"] for value in restored.values())
    return {
        "name": "injection_environment_restored",
        **_now(),
        "trigger": trigger,
        "restored_environment": restored,
        "production_environment_expected": {
            "PYTHONPATH": "unset", PLUGIN_ENV: "unset",
        },
        "backup_error": backup_error,
        "env_restore_failed": production_mismatch or backup_error is not None,
    }


def _classify_import_process() -> dict[str, Any]:
    if os.environ.get("PYTEST_XDIST_WORKER"):
        return {
            "name": "probe_import_process_classified",
            **_now(),
            "import_process_role": "worker",
            "classification_method": "xdist-worker-environment",
            "classification_error": None,
        }
    marker = Path(os.environ[OUTPUT_ENV]).resolve() / CONTROLLER_IMPORT_MARKER
    try:
        marker.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
        fd = os.open(marker, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    except FileExistsError:
        return {
            "name": "probe_import_process_classified",
            **_now(),
            "import_process_role": "worker",
            "classification_method": "controller-import-marker-exists",
            "classification_error": None,
        }
    except OSError as exc:
        return {
            "name": "probe_import_process_classified",
            **_now(),
            "import_process_role": "controller",
            "classification_method": "marker-error-fallback",
            "classification_error": f"{type(exc).__name__}:{exc}",
        }
    marker_error = None
    try:
        payload = f"pid={os.getpid()}\n".encode("ascii")
        if os.write(fd, payload) != len(payload):
            raise OSError("controller-import-marker-write-incomplete")
        os.fsync(fd)
    except OSError as exc:
        marker_error = f"{type(exc).__name__}:{exc}"
    finally:
        os.close(fd)
    return {
        "name": "probe_import_process_classified",
        **_now(),
        "import_process_role": "controller",
        "classification_method": "controller-import-marker-created",
        "classification_error": marker_error,
    }


def _canonical_bytes(value: Any) -> bytes:
    return (
        json.dumps(value, ensure_ascii=True, separators=(",", ":"), sort_keys=True)
        + "\n"
    ).encode("ascii")


def _digest(value: Any) -> str:
    return hashlib.sha256(_canonical_bytes(value)).hexdigest()


def _read_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as stream:
        return json.load(stream)


def _atomic_json(path: Path, value: Any, *, replace: bool = True) -> None:
    path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    temporary = path.parent / f".{path.name}.{os.getpid()}.{time.time_ns()}.tmp"
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
    fd = os.open(temporary, flags, 0o600)
    try:
        with os.fdopen(fd, "wb") as stream:
            stream.write(_canonical_bytes(value))
            stream.flush()
            os.fsync(stream.fileno())
        if replace:
            os.replace(temporary, path)
        else:
            os.link(temporary, path)
            temporary.unlink()
    finally:
        try:
            temporary.unlink()
        except FileNotFoundError:
            pass


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _git_head(repo: Path) -> str:
    result = subprocess.run(
        ["/usr/bin/git", "rev-parse", "HEAD"], cwd=repo,
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
        check=False, timeout=15,
    )
    lines = result.stdout.splitlines()
    if result.returncode != 0 or len(lines) != 1 or not re.fullmatch(
        r"[0-9a-f]{40}", lines[0]
    ):
        raise RuntimeError("tested-tip-unavailable")
    return lines[0]


def _openssl_version() -> dict[str, Any]:
    command = ["openssl", "version"]
    try:
        result = subprocess.run(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=False,
            timeout=15,
        )
    except OSError as exc:
        return {
            "command": command,
            "returncode": None,
            "stdout": "",
            "stderr": "",
            "execution_error": f"{type(exc).__name__}:{exc}",
        }
    return {
        "command": command,
        "returncode": int(result.returncode),
        "stdout": result.stdout.rstrip("\n"),
        "stderr": result.stderr.rstrip("\n"),
    }


def _role(config: Any | None = None) -> str:
    if config is not None:
        worker = getattr(config, "workerinput", {}).get("workerid")
        if isinstance(worker, str) and worker:
            return worker
    worker = os.environ.get("PYTEST_XDIST_WORKER")
    return worker if worker else "controller"


_ACTIVE = os.environ.get(MODE_ENV) in {"real", "zero"} and bool(
    os.environ.get(OUTPUT_ENV)
)
_MODE = os.environ.get(MODE_ENV, "inactive")
_TIMING = os.environ.get(TIMING_ENV) == "1"
_IMPORT_CLASSIFICATION = _classify_import_process() if _ACTIVE else None
_IMPORT_ENV_RESTORE = (
    _restore_injected_environment("worker-module-import")
    if (
        _ACTIVE
        and _IMPORT_CLASSIFICATION is not None
        and _IMPORT_CLASSIFICATION["import_process_role"] == "worker"
    ) else None
)
_STATE: dict[str, Any] = {
    "import_clock": _now(),
    "events": [
        value for value in (_IMPORT_CLASSIFICATION, _IMPORT_ENV_RESTORE)
        if value is not None
    ],
    "clock_samples": [],
    "reports": [],
    "protocols": [],
    "makereports": [],
    "serializations": [],
    "hook_orders": {},
    "hook_order_errors": [],
    "flushes": {},
    "controller_report_event_count": 0,
    "ready_worker_ids": set(),
    "import_process_classification": _IMPORT_CLASSIFICATION,
    "environment_restore": (
        _IMPORT_ENV_RESTORE if _IMPORT_ENV_RESTORE is not None else {
            "status": "pending-all-workers-ready",
            "restored_environment": _environment_state(),
            "production_environment_expected": {
                "PYTHONPATH": "unset", PLUGIN_ENV: "unset",
            },
            "env_restore_failed": True,
        }
    ),
}


def _event(name: str, **fields: Any) -> dict[str, Any]:
    value = {"name": name, **_now(), **fields}
    _STATE["events"].append(value)
    return value


def _clock_sample(name: str) -> None:
    _STATE["clock_samples"].append({"name": name, **_now()})


def _source_path(function: Any) -> str:
    try:
        source = inspect.getsourcefile(function) or inspect.getfile(function)
    except (OSError, TypeError):
        return "unavailable"
    try:
        return str(Path(source).resolve())
    except OSError:
        return str(source)


def _hook_descriptor(impl: Any) -> dict[str, Any]:
    function = impl.function
    return {
        "plugin_name": str(impl.plugin_name),
        "module": str(getattr(function, "__module__", "")),
        "qualname": str(getattr(function, "__qualname__", "")),
        "source": _source_path(function),
        "tryfirst": bool(impl.tryfirst),
        "trylast": bool(impl.trylast),
        "wrapper": bool(impl.wrapper),
        "hookwrapper": bool(impl.hookwrapper),
    }


def _hook_order(config: Any, hook_name: str) -> dict[str, Any]:
    hook = getattr(config.pluginmanager.hook, hook_name)
    stored = list(hook.get_hookimpls())
    enter = [_hook_descriptor(impl) for impl in reversed(stored)]
    exits = [
        _hook_descriptor(impl)
        for impl in stored
        if impl.wrapper or impl.hookwrapper
    ]
    return {"enter_or_call": enter, "wrapper_exit": exits}


def _is_our(descriptor: Mapping[str, Any], qualname: str) -> bool:
    return (
        descriptor.get("module") == __name__
        and str(descriptor.get("qualname", "")).endswith(qualname)
    )


def _validate_hook_orders(config: Any) -> None:
    names = ["pytest_collection_modifyitems"]
    if _TIMING:
        names.extend((
            "pytest_runtest_protocol", "pytest_sessionfinish",
            "pytest_terminal_summary", "pytest_unconfigure",
        ))
    orders = {name: _hook_order(config, name) for name in names}
    _STATE["hook_orders"] = orders
    errors: list[str] = []

    collection = orders["pytest_collection_modifyitems"]
    flat = collection["enter_or_call"]
    acceptance = [
        item for item in flat
        if item["module"] == "tools.acceptance_shards"
        and item["qualname"].endswith("pytest_collection_modifyitems")
    ]
    selector = [item for item in flat if _is_our(item, "_SelectorPlugin.pytest_collection_modifyitems")]
    if len(acceptance) != 1 or acceptance[0]["wrapper"] or not acceptance[0]["trylast"]:
        errors.append("production-collection-hook-shape")
    if len(selector) != 1 or not selector[0]["wrapper"] or not selector[0]["trylast"]:
        errors.append("selector-hook-shape")
    exit_order = collection["wrapper_exit"]
    if not exit_order or not _is_our(
        exit_order[0], "_SelectorPlugin.pytest_collection_modifyitems"
    ):
        errors.append("selector-not-first-post-yield")

    if _TIMING:
        for hook_name, qualname in (
            ("pytest_runtest_protocol", "_TimingPlugin.pytest_runtest_protocol"),
            ("pytest_sessionfinish", "_TimingPlugin.pytest_sessionfinish"),
            ("pytest_terminal_summary", "_TimingPlugin.pytest_terminal_summary"),
            ("pytest_unconfigure", "_TimingPlugin.pytest_unconfigure"),
        ):
            order = orders[hook_name]
            if not order["enter_or_call"] or not _is_our(
                order["enter_or_call"][0], qualname
            ):
                errors.append(f"{hook_name}-probe-not-outermost-enter")
            if not order["wrapper_exit"] or not _is_our(
                order["wrapper_exit"][-1], qualname
            ):
                errors.append(f"{hook_name}-probe-not-outermost-exit")
        protocol = orders["pytest_runtest_protocol"]["enter_or_call"]
        conftest = [
            item for item in protocol
            if item["source"].endswith("/orchestrator/tests/conftest.py")
            and item["qualname"].endswith("pytest_runtest_protocol")
        ]
        if len(conftest) != 1 or not conftest[0]["wrapper"] or not conftest[0]["tryfirst"]:
            errors.append("production-protocol-hook-shape")

    _STATE["hook_order_errors"] = errors
    if errors:
        raise pytest.UsageError("T-2097 hook order mismatch: " + ",".join(errors))


class _SelectorPlugin:
    @pytest.hookimpl(wrapper=True, trylast=True)
    def pytest_collection_modifyitems(self, config: Any, items: list[Any]):
        _event("collection_modifyitems_selector_enter", item_count=len(items))
        result = yield
        state = getattr(config, "_izanagi_acceptance_shard_state", None)
        if not isinstance(state, dict):
            raise pytest.UsageError("T-2097 production shard state missing")
        required = {"records", "records_digest", "selected", "selected_digest", "loads"}
        if not required.issubset(state):
            raise pytest.UsageError("T-2097 production shard state incomplete")
        _STATE["collection"] = {
            "observed_count": len(state["records"]),
            "observed_digest": state["records_digest"],
            "selected_count": len(state["selected"]),
            "selected_digest": state["selected_digest"],
            "post_production_item_count": len(items),
        }
        if _MODE == "zero":
            items[:] = []
        _event(
            "collection_modifyitems_selector_exit",
            item_count=len(items),
            production_state_observed=True,
        )
        return result

    @pytest.hookimpl(optionalhook=True)
    def pytest_testnodeready(self, node: Any) -> None:
        worker_id = str(getattr(node.gateway, "id", ""))
        _event("testnodeready", worker_id=worker_id)
        if _role() != "controller" or not WORKER_RE.fullmatch(worker_id):
            return
        ready_worker_ids = _STATE["ready_worker_ids"]
        ready_worker_ids.add(worker_id)
        if (
            len(ready_worker_ids) == EXPECTED_WORKERS
            and _STATE["environment_restore"].get("status")
            == "pending-all-workers-ready"
        ):
            restored = _restore_injected_environment("all-workers-ready")
            _STATE["environment_restore"] = restored
            _STATE["events"].append(restored)


class _TimingPlugin:
    @pytest.hookimpl(wrapper=True, tryfirst=True)
    def pytest_sessionstart(self, session: Any):
        _event("sessionstart_enter")
        result = yield
        terminal = session.config.pluginmanager.get_plugin("terminalreporter")
        instant = getattr(terminal, "_session_start", None)
        if _role(session.config) == "controller":
            if instant is None or not all(hasattr(instant, name) for name in ("time", "perf_count")):
                raise pytest.UsageError("T-2097 terminal session start unavailable")
            _STATE["terminal_session_start"] = {
                "epoch_ns": round(float(instant.time) * 1_000_000_000),
                "perf_ns": round(float(instant.perf_count) * 1_000_000_000),
            }
        _clock_sample("sessionstart_exit")
        _event("sessionstart_exit")
        return result

    @pytest.hookimpl(optionalhook=True)
    def pytest_xdist_setupnodes(self, config: Any, specs: Sequence[Any]) -> None:
        del config
        _event("xdist_setupnodes", worker_count=len(specs))

    @pytest.hookimpl(optionalhook=True)
    def pytest_xdist_newgateway(self, gateway: Any) -> None:
        _event("xdist_newgateway", worker_id=str(getattr(gateway, "id", "")))

    @pytest.hookimpl(optionalhook=True)
    def pytest_configure_node(self, node: Any) -> None:
        _event("configure_node", worker_id=str(getattr(node.gateway, "id", "")))

    @pytest.hookimpl(wrapper=True, tryfirst=True)
    def pytest_collection(self, session: Any):
        del session
        begin = _event("collection_enter")
        result = yield
        _event("collection_exit", begin_perf_ns=begin["perf_ns"])
        return result

    @pytest.hookimpl(trylast=True)
    def pytest_collection_finish(self, session: Any) -> None:
        _event("collection_finish", item_count=len(session.items))

    @pytest.hookimpl(optionalhook=True)
    def pytest_xdist_node_collection_finished(self, node: Any, ids: Sequence[str]) -> None:
        _event(
            "node_collection_finished_received",
            worker_id=str(getattr(node.gateway, "id", "")),
            item_count=len(ids),
            ids_digest=_digest(list(ids)),
        )

    @pytest.hookimpl(wrapper=True, tryfirst=True)
    def pytest_runtestloop(self, session: Any):
        del session
        begin = _event("runtestloop_enter")
        result = yield
        _event("runtestloop_exit", begin_perf_ns=begin["perf_ns"])
        return result

    @pytest.hookimpl(wrapper=True, tryfirst=True)
    def pytest_runtest_protocol(self, item: Any, nextitem: Any):
        del nextitem
        begin = time.perf_counter_ns()
        nodeid = str(item.nodeid)
        result = yield
        end = time.perf_counter_ns()
        _STATE["protocols"].append({
            "nodeid": nodeid, "begin_perf_ns": begin, "end_perf_ns": end,
        })
        return result

    @pytest.hookimpl(wrapper=True, tryfirst=True)
    def pytest_runtest_makereport(self, item: Any, call: Any):
        begin = time.perf_counter_ns()
        result = yield
        end = time.perf_counter_ns()
        _STATE["makereports"].append({
            "nodeid": str(item.nodeid), "when": str(call.when),
            "begin_perf_ns": begin, "end_perf_ns": end,
        })
        return result

    @pytest.hookimpl(wrapper=True, tryfirst=True)
    def pytest_runtest_logreport(self, report: Any):
        begin = time.perf_counter_ns()
        result = yield
        end = time.perf_counter_ns()
        if _STATE.get("role") == "controller":
            _STATE["controller_report_event_count"] += 1
            return result
        _STATE["reports"].append({
            "nodeid": str(report.nodeid),
            "when": str(getattr(report, "when", "")),
            "start_epoch_ns": round(float(report.start) * 1_000_000_000),
            "stop_epoch_ns": round(float(report.stop) * 1_000_000_000),
            "duration_ns": round(float(report.duration) * 1_000_000_000),
            "hook_begin_perf_ns": begin,
            "hook_end_perf_ns": end,
            "report_worker_id": str(getattr(report, "worker_id", "")),
        })
        return result

    @pytest.hookimpl(wrapper=True, tryfirst=True, optionalhook=True)
    def pytest_report_to_serializable(self, config: Any, report: Any):
        del config
        begin = time.perf_counter_ns()
        result = yield
        end = time.perf_counter_ns()
        _STATE["serializations"].append({
            "nodeid": str(getattr(report, "nodeid", "")),
            "when": str(getattr(report, "when", "")),
            "begin_perf_ns": begin,
            "end_perf_ns": end,
        })
        return result

    @pytest.hookimpl(optionalhook=True)
    def pytest_testnodedown(self, node: Any, error: Any) -> None:
        _event(
            "workerfinished_received",
            worker_id=str(getattr(node.gateway, "id", "")),
            error_type=(type(error).__name__ if error is not None else "none"),
        )

    @pytest.hookimpl(wrapper=True, tryfirst=True)
    def pytest_terminal_summary(self, terminalreporter: Any, exitstatus: Any, config: Any):
        del terminalreporter, exitstatus, config
        _event("terminal_summary_enter")
        result = yield
        _event("terminal_summary_exit")
        return result

    @pytest.hookimpl(wrapper=True, tryfirst=True)
    def pytest_sessionfinish(self, session: Any, exitstatus: Any):
        _event("sessionfinish_enter", exitstatus=int(exitstatus))
        result = yield
        _clock_sample("sessionfinish_exit")
        _event("sessionfinish_exit", exitstatus=int(session.exitstatus))
        _flush_process(session.config, "sessionfinish")
        return result

    @pytest.hookimpl(wrapper=True, tryfirst=True)
    def pytest_unconfigure(self, config: Any):
        _event("unconfigure_enter")
        result = yield
        _clock_sample("unconfigure_exit")
        _event("unconfigure_exit")
        _flush_process(config, "unconfigure")
        return result


class _SelectorOnlyFlushPlugin:
    @pytest.hookimpl(wrapper=True, tryfirst=True)
    def pytest_sessionfinish(self, session: Any, exitstatus: Any):
        _event("sessionfinish_enter", exitstatus=int(exitstatus))
        result = yield
        _clock_sample("sessionfinish_exit")
        _event("sessionfinish_exit", exitstatus=int(session.exitstatus))
        _flush_process(session.config, "sessionfinish")
        return result

    @pytest.hookimpl(wrapper=True, tryfirst=True)
    def pytest_unconfigure(self, config: Any):
        _event("unconfigure_enter")
        result = yield
        _clock_sample("unconfigure_exit")
        _event("unconfigure_exit")
        _flush_process(config, "unconfigure")
        return result


@pytest.hookimpl(wrapper=True, tryfirst=True)
def pytest_load_initial_conftests(early_config: Any, parser: Any, args: Sequence[str]):
    del early_config, parser, args
    if not _ACTIVE:
        yield
        return
    _event("load_initial_conftests_enter")
    result = yield
    _event("load_initial_conftests_exit")
    return result


def pytest_configure(config: Any) -> None:
    if not _ACTIVE:
        return
    role = _role(config)
    if (
        role != "controller"
        and _STATE["environment_restore"].get("status")
        == "pending-all-workers-ready"
    ):
        restored = _restore_injected_environment("worker-pytest-configure")
        _STATE["environment_restore"] = restored
        _STATE["events"].append(restored)
    _STATE["role"] = role
    _STATE["hostname"] = socket.gethostname()
    _STATE["pid"] = os.getpid()
    _STATE["mode"] = _MODE
    _STATE["timing"] = _TIMING
    _clock_sample("configure")
    _event(
        "configure", role=role, pytest_version=pytest.__version__,
        xdist_version=_distribution_version("pytest-xdist"),
    )
    selector = _SelectorPlugin()
    config.pluginmanager.register(selector, "t2097-selector")
    if _TIMING:
        timing = _TimingPlugin()
        config.pluginmanager.register(timing, "t2097-timing")
    else:
        flush = _SelectorOnlyFlushPlugin()
        config.pluginmanager.register(flush, "t2097-selector-flush")
    _validate_hook_orders(config)


def _distribution_version(name: str) -> str:
    try:
        from importlib import metadata
        return metadata.version(name)
    except Exception:
        return "unavailable"


def _process_payload(config: Any, kind: str) -> dict[str, Any]:
    cut = _STATE.get("flush_cut") if kind == "unconfigure" else None
    event_start = int(cut["events"]) if isinstance(cut, dict) else 0
    clock_start = int(cut["clock_samples"]) if isinstance(cut, dict) else 0
    compact_delta = isinstance(cut, dict)
    return {
        "schema_version": PROCESS_SCHEMA,
        "snapshot_kind": kind,
        "role": _role(config),
        "pid": os.getpid(),
        "hostname": socket.gethostname(),
        "mode": _MODE,
        "timing": _TIMING,
        "python": sys.version,
        "import_clock": _STATE["import_clock"],
        "delta_from_sessionfinish": compact_delta,
        "clock_samples": _STATE["clock_samples"][clock_start:],
        "events": _STATE["events"][event_start:],
        "reports": [] if compact_delta else _STATE["reports"],
        "protocols": [] if compact_delta else _STATE["protocols"],
        "makereports": [] if compact_delta else _STATE["makereports"],
        "serializations": [] if compact_delta else _STATE["serializations"],
        "hook_orders": {} if compact_delta else _STATE["hook_orders"],
        "hook_order_errors": [] if compact_delta else _STATE["hook_order_errors"],
        "collection": {} if compact_delta else _STATE.get("collection", {}),
        "terminal_session_start": (
            {} if compact_delta else _STATE.get("terminal_session_start", {})
        ),
        "controller_report_event_count": _STATE["controller_report_event_count"],
        "import_process_classification": _STATE["import_process_classification"],
        "environment_restore": dict(_STATE["environment_restore"]),
        "env_restore_failed": bool(
            _STATE["environment_restore"].get("env_restore_failed", True)
        ),
        "earlier_flushes": dict(_STATE["flushes"]),
        "write_measurement": {
            "scope": "create-write-flush-fsync",
            "primary_duration_ns": "00000000000000000000",
        },
    }


def _flush_process(config: Any, kind: str) -> None:
    output = Path(os.environ[OUTPUT_ENV]).resolve()
    output.mkdir(mode=0o700, parents=True, exist_ok=True)
    role = _role(config)
    path = output / f"{role}.{kind}.json"
    payload = _process_payload(config, kind)
    raw = _canonical_bytes(payload)
    marker = b'"primary_duration_ns":"00000000000000000000"'
    position = raw.find(marker)
    if position < 0:
        raise pytest.UsageError("T-2097 write duration marker missing")
    digits_at = position + len(b'"primary_duration_ns":"')
    begin = time.perf_counter_ns()
    fd = os.open(path, os.O_RDWR | os.O_CREAT | os.O_EXCL, 0o600)
    try:
        view = memoryview(raw)
        written = 0
        while written < len(view):
            written += os.write(fd, view[written:])
        os.fsync(fd)
        duration = time.perf_counter_ns() - begin
        digits = f"{duration:020d}".encode("ascii")
        if len(digits) != 20:
            raise pytest.UsageError("T-2097 write duration overflow")
        os.lseek(fd, digits_at, os.SEEK_SET)
        if os.write(fd, digits) != len(digits):
            raise pytest.UsageError("T-2097 write duration patch incomplete")
        os.fsync(fd)
    finally:
        os.close(fd)
    _STATE["flushes"][kind] = duration
    if kind == "sessionfinish":
        _STATE["flush_cut"] = {
            "events": len(_STATE["events"]),
            "clock_samples": len(_STATE["clock_samples"]),
        }


def _cache_state(repo: Path) -> dict[str, Any]:
    pyc_count = 0
    rewrite_count = 0
    for path in repo.rglob("*.pyc"):
        if ".git" in path.parts:
            continue
        pyc_count += 1
        if "-pytest-" in path.name:
            rewrite_count += 1
    tmp_raw = os.environ.get("TMPDIR")
    tmp_effective = Path(tmp_raw if tmp_raw else "/tmp").resolve()
    return {
        "worktree_pyc_count": pyc_count,
        "pytest_rewrite_pyc_count": rewrite_count,
        "tmpdir_environment_set": tmp_raw is not None,
        "tmpdir_effective": str(tmp_effective),
        "tmpdir_filesystem": _mount_for_path(tmp_effective),
        "python_dont_write_bytecode_environment_set": (
            "PYTHONDONTWRITEBYTECODE" in os.environ
        ),
        "python_dont_write_bytecode_environment_value_sha256": (
            hashlib.sha256(os.environ["PYTHONDONTWRITEBYTECODE"].encode()).hexdigest()
            if "PYTHONDONTWRITEBYTECODE" in os.environ else "absent"
        ),
    }


def _mount_for_path(path: Path) -> dict[str, str]:
    best: tuple[int, dict[str, str]] | None = None
    try:
        lines = Path("/proc/self/mountinfo").read_text(encoding="utf-8").splitlines()
    except OSError as exc:
        return {"status": f"unavailable:{type(exc).__name__}"}
    for line in lines:
        left, separator, right = line.partition(" - ")
        if not separator:
            continue
        fields = left.split()
        tail = right.split()
        if len(fields) < 5 or len(tail) < 2:
            continue
        mountpoint = Path(fields[4].replace("\\040", " "))
        try:
            path.relative_to(mountpoint)
        except ValueError:
            continue
        record = {"mountpoint": str(mountpoint), "fstype": tail[0], "source": tail[1]}
        candidate = (len(mountpoint.parts), record)
        if best is None or candidate[0] > best[0]:
            best = candidate
    return best[1] if best is not None else {"status": "unavailable:no-mount"}


def _proc_stat(pid: int) -> dict[str, Any] | None:
    try:
        raw = Path(f"/proc/{pid}/stat").read_text(encoding="ascii")
        close = raw.rfind(")")
        if close < 0:
            return None
        comm = raw[raw.find("(") + 1:close]
        fields = raw[close + 2:].split()
        if len(fields) < 20:
            return None
        return {
            "pid": pid,
            "comm": comm,
            "uid": os.stat(f"/proc/{pid}").st_uid,
            "ppid": int(fields[1]),
            "utime": int(fields[11]),
            "stime": int(fields[12]),
            "starttime": int(fields[19]),
        }
    except (OSError, ValueError):
        return None


def _all_processes() -> tuple[dict[int, dict[str, Any]], int]:
    values: dict[int, dict[str, Any]] = {}
    errors = 0
    try:
        entries = list(Path("/proc").iterdir())
    except OSError:
        return values, 1
    for entry in entries:
        if not entry.name.isdigit():
            continue
        value = _proc_stat(int(entry.name))
        if value is None:
            if entry.exists():
                errors += 1
        else:
            values[value["pid"]] = value
    return values, errors


def _descendants(processes: Mapping[int, Mapping[str, Any]], root_pid: int) -> set[int]:
    children: dict[int, list[int]] = defaultdict(list)
    for pid, value in processes.items():
        children[int(value["ppid"])].append(pid)
    reached = {root_pid}
    pending = [root_pid]
    while pending:
        parent = pending.pop()
        for child in children.get(parent, ()):
            if child not in reached:
                reached.add(child)
                pending.append(child)
    return reached


def _node_cpu() -> dict[str, int]:
    try:
        line = Path("/proc/stat").read_text(encoding="ascii").splitlines()[0]
        fields = line.split()
        if not fields or fields[0] != "cpu":
            raise ValueError
        names = ("user", "nice", "system", "idle", "iowait", "irq", "softirq", "steal")
        values = [int(value) for value in fields[1:1 + len(names)]]
        return dict(zip(names, values))
    except (OSError, ValueError, IndexError):
        return {}


def _load_sample() -> dict[str, Any]:
    try:
        fields = Path("/proc/loadavg").read_text(encoding="ascii").split()
        return {
            "load_1": float(fields[0]), "load_5": float(fields[1]),
            "load_15": float(fields[2]), "runnable_total": fields[3],
        }
    except (OSError, ValueError, IndexError):
        return {"status": "unavailable"}


def _process_job_ids(
    processes: Mapping[int, Mapping[str, Any]], descendants: set[int],
    kernel_processes: set[int],
) -> tuple[list[dict[str, Any]], int, list[str]]:
    jobs: dict[str, set[int]] = defaultdict(set)
    unreadable = 0
    unreadable_comms: set[str] = set()
    for pid, process in processes.items():
        if pid in descendants or pid in kernel_processes:
            continue
        try:
            raw = Path(f"/proc/{pid}/environ").read_bytes()
        except (OSError, PermissionError):
            if Path(f"/proc/{pid}").exists():
                unreadable += 1
                unreadable_comms.add(str(process["comm"]))
            continue
        for entry in raw.split(b"\0"):
            if entry.startswith(b"PBS_JOBID="):
                job = entry.partition(b"=")[2].decode("ascii", errors="replace")
                if job:
                    jobs[job].add(pid)
    return [
        {
            "pbs_jobid": job,
            "process_count": len(pids),
            "representative_comms": sorted({
                str(processes[pid]["comm"]) for pid in pids
            })[:20],
        }
        for job, pids in sorted(jobs.items())
    ], unreadable, sorted(unreadable_comms)[:20]


def _kernel_processes(
    processes: Mapping[int, Mapping[str, Any]],
) -> tuple[set[int], int, list[str]]:
    kernel: set[int] = set()
    for pid, process in processes.items():
        if process.get("comm") == "kthreadd":
            kernel.update(_descendants(processes, pid))
    cmdline_read_errors = 0
    unreadable_comms: set[str] = set()
    for pid, process in processes.items():
        if pid in kernel:
            continue
        try:
            cmdline = Path(f"/proc/{pid}/cmdline").read_bytes()
        except (OSError, PermissionError):
            if Path(f"/proc/{pid}").exists():
                cmdline_read_errors += 1
                unreadable_comms.add(str(process["comm"]))
            continue
        if not cmdline:
            kernel.add(pid)
    return kernel, cmdline_read_errors, sorted(unreadable_comms)[:20]


class _NodeMonitor:
    def __init__(self, root_pid: int):
        self.root_pid = root_pid
        self.samples: list[dict[str, Any]] = []
        self.previous: dict[tuple[int, int], tuple[int, bool, dict[str, Any]]] = {}
        self.foreign_cpu: dict[tuple[int, int], dict[str, Any]] = {}
        self.sample_gaps_ns: list[int] = []

    def sample(self, label: str) -> None:
        clock = _now()
        processes, read_errors = _all_processes()
        descendants = _descendants(processes, self.root_pid)
        descendants.update(_descendants(processes, os.getpid()))
        kernel_processes, cmdline_errors, cmdline_error_comms = _kernel_processes(
            processes
        )
        jobs, env_unreadable, env_unreadable_comms = _process_job_ids(
            processes, descendants, kernel_processes
        )
        current: dict[tuple[int, int], tuple[int, bool, dict[str, Any]]] = {}
        for pid, value in processes.items():
            key = (pid, int(value["starttime"]))
            ticks = int(value["utime"]) + int(value["stime"])
            is_descendant = pid in descendants
            current[key] = (ticks, is_descendant, value)
            previous = self.previous.get(key)
            if previous is None or is_descendant or previous[1]:
                continue
            delta = max(0, ticks - previous[0])
            if delta:
                record = self.foreign_cpu.setdefault(key, {
                    "pid": pid, "starttime_ticks": key[1],
                    "uid": int(value["uid"]),
                    "comm": str(value["comm"]),
                    "process_classification": (
                        "kernel-thread" if pid in kernel_processes else "userspace"
                    ),
                    "cpu_delta_ticks": 0,
                })
                record["cpu_delta_ticks"] += delta
        if self.samples:
            self.sample_gaps_ns.append(clock["perf_ns"] - self.samples[-1]["perf_ns"])
        own_job = os.environ.get("PBS_JOBID", "")
        foreign_jobs = [entry for entry in jobs if entry["pbs_jobid"] != own_job]
        self.samples.append({
            "label": label,
            **clock,
            "node_cpu_ticks": _node_cpu(),
            "load": _load_sample(),
            "process_count": len(processes),
            "descendant_process_count": len(descendants),
            "kernel_process_count": len(kernel_processes),
            "process_stat_read_errors": read_errors,
            "process_cmdline_read_errors": cmdline_errors,
            "process_cmdline_unreadable_representative_comms": cmdline_error_comms,
            "foreign_pbs_jobs": foreign_jobs,
            "foreign_process_environ_unreadable": env_unreadable,
            "foreign_process_environ_unreadable_representative_comms": (
                env_unreadable_comms
            ),
        })
        self.previous = current

    def finish(self) -> dict[str, Any]:
        ticks_per_second = int(os.sysconf("SC_CLK_TCK"))
        foreign = sorted(
            self.foreign_cpu.values(),
            key=lambda item: (-item["cpu_delta_ticks"], item["pid"]),
        )
        foreign_significant = [
            item for item in foreign
            if item["cpu_delta_ticks"] >= ticks_per_second
        ]
        kernel_significant = [
            item for item in foreign_significant
            if item.get("process_classification") == "kernel-thread"
        ]
        userspace_significant = [
            item for item in foreign_significant
            if item.get("process_classification") == "userspace"
        ]
        foreign_jobs = sorted({
            entry["pbs_jobid"]
            for sample in self.samples
            for entry in sample["foreign_pbs_jobs"]
        })
        visibility_gap = any(
            sample["process_stat_read_errors"] > 0
            or sample["process_cmdline_read_errors"] > 0
            or sample["foreign_process_environ_unreadable"] > 0
            for sample in self.samples
        )
        monitor_gap = bool(self.sample_gaps_ns) and max(self.sample_gaps_ns) > 3_000_000_000
        visibility_comms = sorted({
            comm
            for sample in self.samples
            for field in (
                "process_cmdline_unreadable_representative_comms",
                "foreign_process_environ_unreadable_representative_comms",
            )
            for comm in sample[field]
        })[:20]
        reasons = {
            "competing_jobs": {
                "present": bool(foreign_jobs or userspace_significant),
                "foreign_pbs_job_count": len(foreign_jobs),
                "significant_userspace_process_count": len(userspace_significant),
                "representative_comms": sorted({
                    str(item["comm"]) for item in userspace_significant
                } | {
                    str(comm)
                    for sample in self.samples
                    for job in sample["foreign_pbs_jobs"]
                    for comm in job.get("representative_comms", [])
                })[:20],
            },
            "kernel_thread_activity": {
                "present": bool(kernel_significant),
                "significant_process_count": len(kernel_significant),
                "representative_comms": sorted({
                    str(item["comm"]) for item in kernel_significant
                })[:20],
            },
            "process_visibility_gaps": {
                "present": visibility_gap or monitor_gap,
                "process_stat_read_error_observations": sum(
                    int(sample["process_stat_read_errors"]) for sample in self.samples
                ),
                "process_cmdline_read_error_observations": sum(
                    int(sample["process_cmdline_read_errors"]) for sample in self.samples
                ),
                "foreign_environ_read_error_observations": sum(
                    int(sample["foreign_process_environ_unreadable"])
                    for sample in self.samples
                ),
                "monitor_sample_gap_over_three_seconds": monitor_gap,
                "representative_comms": visibility_comms,
            },
        }
        return {
            "sample_interval_target_s": 1.0,
            "clock_ticks_per_second": ticks_per_second,
            "samples": self.samples,
            "foreign_process_cpu_increments": foreign,
            "foreign_process_cpu_significant": foreign_significant,
            "foreign_userspace_cpu_significant": userspace_significant,
            "kernel_thread_cpu_significant": kernel_significant,
            "foreign_pbs_job_ids": foreign_jobs,
            "maximum_sample_gap_ns": max(self.sample_gaps_ns, default=0),
            "disturbance_reasons": reasons,
            "disturbed": any(reason["present"] for reason in reasons.values()),
        }


def _runner_command(python: Path, repo: Path, session: Path, shard: int) -> list[str]:
    return [
        str(python), str(repo / "tools" / "run_tests.py"),
        f"--izanagi-acceptance-shard-session={session}",
        "--izanagi-acceptance-shard-count=3",
        f"--izanagi-acceptance-shard-index={shard}",
    ]


def _expected_group_gate(report: Mapping[str, Any], shard: int) -> dict[str, Any]:
    actual = report.get("group_to_workers")
    expected = EXPECTED_GROUP_KEYS.get(shard)
    valid_shape = isinstance(actual, dict) and all(
        isinstance(group, str)
        and isinstance(workers, list)
        and len(workers) == 1
        and isinstance(workers[0], str)
        and WORKER_RE.fullmatch(workers[0])
        for group, workers in (actual.items() if isinstance(actual, dict) else ())
    )
    actual_keys = frozenset(actual) if isinstance(actual, dict) else frozenset()
    passed = expected is not None and valid_shape and actual_keys == expected
    return {
        "passed": passed,
        "expected_group_keys": sorted(expected if expected is not None else ()),
        "actual_group_keys": sorted(actual_keys),
        "one_worker_per_group": valid_shape,
    }


def _local_report_checks(report: Mapping[str, Any], shard: int, kind: str) -> dict[str, Any]:
    selected = report.get("selected")
    finished = report.get("finished")
    occupancy = report.get("worker_occupancy")
    checks: dict[str, Any] = {
        "shard_count_is_three": report.get("shard_count") == 3,
        "shard_index_matches": report.get("shard_index") == shard,
        "group_to_workers_expected": _expected_group_gate(report, shard),
    }
    if kind == "real":
        checks["finished_equals_selected"] = (
            isinstance(selected, list) and isinstance(finished, list)
            and finished == selected
        )
        checks["worker_count_is_48"] = (
            isinstance(occupancy, dict)
            and set(occupancy) != {"unobserved"}
            and len(occupancy) == EXPECTED_WORKERS
            and all(WORKER_RE.fullmatch(str(worker)) for worker in occupancy)
        )
    else:
        checks["calibration_finished_is_empty"] = finished == []
        checks["calibration_selected_is_nonempty"] = isinstance(selected, list) and bool(selected)
    return checks


def _checks_pass(checks: Mapping[str, Any]) -> bool:
    for value in checks.values():
        if isinstance(value, bool) and not value:
            return False
        if isinstance(value, dict) and value.get("passed") is False:
            return False
    return True


def command_run_arm(args: argparse.Namespace) -> int:
    root = args.root.resolve()
    repo = args.repo.resolve()
    python = args.python.resolve()
    if not args.probe_source.is_absolute() or not args.pbs_source.is_absolute():
        raise RuntimeError("probe-source-not-absolute")
    source = args.probe_source.resolve()
    pbs = args.pbs_source.resolve()
    if not SAFE_TAG_RE.fullmatch(args.job_tag):
        raise RuntimeError("unsafe-job-tag")
    if args.arm not in ARM_BY_NAME:
        raise RuntimeError("unknown-arm")
    _, expected_shard, expected_probe, kind = ARM_BY_NAME[args.arm]
    if args.shard != expected_shard or args.probe != expected_probe:
        raise RuntimeError("arm-contract-mismatch")
    if root != root.resolve() or repo != repo.resolve() or not root.is_dir():
        raise RuntimeError("root-contract")
    if (
        not source.is_file()
        or not pbs.is_file()
        or source.name != "_t2097_residual_probe.py"
        or pbs.name != "_t2097_residual_probe.pbs"
        or source.parent != pbs.parent
        or source.parent == repo
        or repo in source.parents
        or repo in pbs.parents
    ):
        raise RuntimeError("external-probe-source-contract")
    session = root / f"{args.job_tag}-{args.arm}"
    if session.exists() or session.is_symlink():
        raise RuntimeError("arm-session-already-exists")
    shard_root = session / f"shard-{args.shard}"
    shard_root.mkdir(mode=0o700, parents=True)
    output = shard_root / "probe"
    if kind == "zero":
        _atomic_json(
            session / "instrumented-zero-selected-calibration.json",
            {
                "schema_version": "izanagi-t2097-calibration-marker/v1",
                "classification": CALIBRATION_KIND,
                "arm": args.arm,
            },
            replace=False,
        )
    affinity = sorted(os.sched_getaffinity(0))
    pre_clock = _now()
    cache_before = _cache_state(repo)
    tested_tip_before = _git_head(repo)
    manifest = {
        "arm": args.arm,
        "kind": kind,
        "probe": args.probe,
        "shard_index": args.shard,
        "shard_count": 3,
        "hostname": socket.gethostname(),
        "openssl_version": _openssl_version(),
        "pbs_jobid": os.environ.get("PBS_JOBID", "unavailable"),
        "affinity_cpus": affinity,
        "tested_tip": tested_tip_before,
        "probe_sha256": _sha256_file(source),
        "pbs_sha256": _sha256_file(pbs),
        "growth_hold": {
            "environment_name": GROWTH_ENV,
            "effective_opt_in": os.environ.get(GROWTH_ENV) == GROWTH_TOKEN,
        },
        "arm_driver_start": pre_clock,
        "cache_before": cache_before,
    }
    _atomic_json(session / "arm-manifest.json", manifest, replace=False)
    if len(affinity) != EXPECTED_AFFINITY:
        outer = {
            "schema_version": OUTER_SCHEMA,
            **manifest,
            "runner_started": False,
            "stop_conditions": {"affinity_is_48": False},
        }
        _atomic_json(shard_root / "outer.json", outer, replace=False)
        return 4

    command = _runner_command(python, repo, session, args.shard)
    environment = os.environ.copy()
    for name in (
        "PYTHONHOME", "PYTHONSTARTUP", "PYTHONPATH", "PYTEST_ADDOPTS", PLUGIN_ENV,
        "IZANAGI_ACCEPTANCE_SHARDS",
    ):
        environment.pop(name, None)
    environment["IZANAGI_TEST_NPROC"] = "48"
    environment["IZANAGI_TASK_RUN_AUTO_RECORD"] = "0"
    if args.probe == "none":
        for name in (
            PLUGIN_ENV, INJECTION_BACKUP_ENV, MODE_ENV, TIMING_ENV, OUTPUT_ENV,
        ):
            environment.pop(name, None)
    else:
        environment[INJECTION_BACKUP_ENV] = json.dumps({
            name: {
                "set": name in environment,
                "value": environment.get(name),
            }
            for name in ("PYTHONPATH", PLUGIN_ENV)
        }, ensure_ascii=True, separators=(",", ":"), sort_keys=True)
        environment["PYTHONPATH"] = str(source.parent)
        environment[PLUGIN_ENV] = "_t2097_residual_probe"
        environment[MODE_ENV] = kind
        environment[TIMING_ENV] = "1" if args.probe == "timing" else "0"
        environment[OUTPUT_ENV] = str(output)

    stdout_path = shard_root / "pytest.stdout"
    stderr_path = shard_root / "pytest.stderr"
    with stdout_path.open("xb") as stdout, stderr_path.open("xb") as stderr:
        runner_start = _now()
        process = subprocess.Popen(
            command, cwd=repo, env=environment, stdout=stdout, stderr=stderr,
            start_new_session=True,
        )
        monitor = _NodeMonitor(process.pid)
        monitor.sample("arm-start")
        while process.poll() is None:
            time.sleep(1.0)
            monitor.sample("running")
        monitor.sample("arm-end")
        returncode = int(process.returncode)
    post_clock = _now()
    cache_after = _cache_state(repo)
    tested_tip_after = _git_head(repo)
    expected_rc = 5 if kind == "zero" else None
    stop_conditions: dict[str, Any] = {
        "affinity_is_48": True,
        "tested_tip_unchanged": tested_tip_after == tested_tip_before,
        "outer_clock_offset_drift_within_5ms": abs(
            (post_clock["epoch_ns"] - post_clock["perf_ns"])
            - (runner_start["epoch_ns"] - runner_start["perf_ns"])
        ) <= MAX_CLOCK_DRIFT_NS,
    }
    if kind == "zero":
        stop_conditions["runner_returncode_expected"] = returncode == expected_rc
    report_path = shard_root / "report.json"
    if report_path.is_file():
        report = _read_json(report_path)
        stop_conditions.update(_local_report_checks(report, args.shard, kind))
    else:
        stop_conditions["report_present"] = False
    monitor_result = monitor.finish()
    outer = {
        "schema_version": OUTER_SCHEMA,
        **manifest,
        "runner_started": True,
        "runner_command": command,
        "runner_returncode": returncode,
        "expected_returncode": expected_rc,
        "runner_start": runner_start,
        "runner_end": post_clock,
        "outer_wall_ns": post_clock["perf_ns"] - runner_start["perf_ns"],
        "outer_clock_offset_drift_ns": abs(
            (post_clock["epoch_ns"] - post_clock["perf_ns"])
            - (runner_start["epoch_ns"] - runner_start["perf_ns"])
        ),
        "tested_tip_after": tested_tip_after,
        "cache_after": cache_after,
        "isolation": monitor_result,
        "disturbed": monitor_result["disturbed"],
        "stop_conditions": stop_conditions,
    }
    _atomic_json(shard_root / "outer.json", outer, replace=False)
    return 0 if _checks_pass(stop_conditions) else 4


def _find_wall(path: Path) -> tuple[float, str]:
    candidates: list[Path] = []
    direct = path / "pytest.stdout"
    if direct.is_file():
        candidates.append(direct)
    candidates.extend(sorted(path.glob("dispatch/*/*.o*")))
    matches: list[tuple[float, Path]] = []
    for candidate in candidates:
        try:
            text = candidate.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        values = WALL_RE.findall(text)
        if values:
            matches.append((float(values[-1]), candidate))
    if len(matches) != 1:
        raise RuntimeError(f"pytest-wall-count:{path}:{len(matches)}")
    return matches[0][0], str(matches[0][1])


def _universe_digest(report: Mapping[str, Any]) -> str:
    records = report.get("observed_universe")
    if not isinstance(records, list):
        raise RuntimeError("observed-universe-shape")
    return _digest(records)


def _max_occupancy(report: Mapping[str, Any]) -> tuple[str, float]:
    occupancy = report.get("worker_occupancy")
    if not isinstance(occupancy, dict) or not occupancy:
        raise RuntimeError("worker-occupancy-shape")
    values: list[tuple[str, float]] = []
    for worker, entry in occupancy.items():
        if not isinstance(entry, dict):
            raise RuntimeError("worker-occupancy-entry")
        duration = entry.get("duration_s")
        if not isinstance(duration, (int, float)) or not math.isfinite(float(duration)):
            raise RuntimeError("worker-occupancy-duration")
        values.append((str(worker), float(duration)))
    return max(values, key=lambda item: (item[1], item[0]))


def _read_process_snapshots(
    probe_root: Path,
) -> tuple[dict[str, Mapping[str, Any]], list[dict[str, Any]]]:
    snapshots: dict[str, Mapping[str, Any]] = {}
    issues: list[dict[str, Any]] = []
    paired_unconfigure_paths: set[Path] = set()
    for sessionfinish_path in sorted(probe_root.glob("*.sessionfinish.json")):
        filename_role = sessionfinish_path.name.removesuffix(".sessionfinish.json")
        try:
            base = _read_json(sessionfinish_path)
        except Exception as exc:
            issues.append({
                "role": filename_role,
                "reason": "sessionfinish-unreadable",
                "path": str(sessionfinish_path),
                "error": f"{type(exc).__name__}:{exc}",
            })
            continue
        role = base.get("role")
        if (
            base.get("schema_version") != PROCESS_SCHEMA
            or not isinstance(role, str)
            or role != filename_role
            or role in snapshots
        ):
            issues.append({
                "role": filename_role,
                "reason": "sessionfinish-contract",
                "path": str(sessionfinish_path),
            })
            continue
        merged = dict(base)
        merged["snapshot_pair_state"] = "sessionfinish-only"
        unconfigure_path = probe_root / f"{role}.unconfigure.json"
        if not unconfigure_path.is_file():
            issues.append({
                "role": role,
                "reason": "unconfigure-snapshot-missing",
                "path": str(unconfigure_path),
            })
            snapshots[role] = merged
            continue
        paired_unconfigure_paths.add(unconfigure_path)
        try:
            delta = _read_json(unconfigure_path)
        except Exception as exc:
            issues.append({
                "role": role,
                "reason": "unconfigure-unreadable",
                "path": str(unconfigure_path),
                "error": f"{type(exc).__name__}:{exc}",
            })
            snapshots[role] = merged
            continue
        if (
            delta.get("schema_version") != PROCESS_SCHEMA
            or delta.get("role") != role
            or delta.get("snapshot_kind") != "unconfigure"
            or delta.get("delta_from_sessionfinish") is not True
        ):
            issues.append({
                "role": role,
                "reason": "invalid-unconfigure-snapshot-pair",
                "path": str(unconfigure_path),
                "observed": {
                    "schema_version": delta.get("schema_version"),
                    "role": delta.get("role"),
                    "snapshot_kind": delta.get("snapshot_kind"),
                    "delta_from_sessionfinish": delta.get(
                        "delta_from_sessionfinish"
                    ),
                },
            })
            snapshots[role] = merged
            continue
        merged["snapshot_kind"] = "unconfigure"
        merged["snapshot_pair_state"] = "complete"
        merged["events"] = list(base.get("events", [])) + list(delta.get("events", []))
        merged["clock_samples"] = list(base.get("clock_samples", [])) + list(
            delta.get("clock_samples", [])
        )
        merged["earlier_flushes"] = delta.get("earlier_flushes", {})
        merged["write_measurement"] = delta.get("write_measurement", {})
        merged["environment_restore"] = delta.get(
            "environment_restore", base.get("environment_restore", {})
        )
        merged["controller_report_event_count"] = delta.get(
            "controller_report_event_count", base.get("controller_report_event_count", 0)
        )
        snapshots[role] = merged
    for path in sorted(probe_root.glob("*.unconfigure.json")):
        if path not in paired_unconfigure_paths:
            issues.append({
                "role": path.name.removesuffix(".unconfigure.json"),
                "reason": "orphan-unconfigure-snapshot",
                "path": str(path),
            })
    return snapshots, issues


def _process_write_measurements(
    snapshots: Mapping[str, Mapping[str, Any]],
) -> dict[str, dict[str, int]]:
    result: dict[str, dict[str, int]] = {}
    for role, snapshot in snapshots.items():
        kind = snapshot.get("snapshot_kind")
        if kind not in {"sessionfinish", "unconfigure"}:
            raise RuntimeError(f"probe-write-snapshot-kind:{role}")
        measurement = snapshot.get("write_measurement")
        if not isinstance(measurement, Mapping):
            raise RuntimeError(f"probe-write-measurement:{role}")
        primary = measurement.get("primary_duration_ns")
        if not isinstance(primary, (str, int)):
            raise RuntimeError(f"probe-write-duration:{role}")
        values = {f"{kind}_primary": int(primary)}
        values.update({
            f"{name}_primary": int(duration)
            for name, duration in snapshot.get("earlier_flushes", {}).items()
        })
        result[role] = values
    return result


def _environment_restore_summary(
    snapshots: Mapping[str, Mapping[str, Any]],
) -> dict[str, Any]:
    processes: dict[str, Any] = {}
    failed_roles: list[str] = []
    for role, snapshot in sorted(snapshots.items()):
        restore = snapshot.get("environment_restore")
        if not isinstance(restore, Mapping):
            process = {"status": "not-recorded", "env_restore_failed": True}
        else:
            process = dict(restore)
        if process.get("env_restore_failed") is not False:
            failed_roles.append(role)
        processes[role] = process
    return {
        "env_restore_failed": bool(failed_roles),
        "failed_process_count": len(failed_roles),
        "failed_process_roles": failed_roles,
        "processes": processes,
    }


def _event_values(snapshot: Mapping[str, Any], name: str) -> list[Mapping[str, Any]]:
    events = snapshot.get("events", [])
    return [event for event in events if isinstance(event, dict) and event.get("name") == name]


def _clock_offsets(snapshot: Mapping[str, Any]) -> tuple[int, int, list[int]]:
    samples: list[Mapping[str, Any]] = []
    imported = snapshot.get("import_clock")
    if isinstance(imported, dict):
        samples.append(imported)
    samples.extend(
        item for item in snapshot.get("clock_samples", []) if isinstance(item, dict)
    )
    offsets = [
        int(item["epoch_ns"]) - int(item["perf_ns"])
        for item in samples
        if isinstance(item.get("epoch_ns"), int) and isinstance(item.get("perf_ns"), int)
    ]
    if len(offsets) < 2:
        raise RuntimeError("clock-samples-insufficient")
    offset = round(statistics.median(offsets))
    drift = max(offsets) - min(offsets)
    return offset, drift, offsets


def _merge_intervals(intervals: Iterable[tuple[int, int]]) -> list[tuple[int, int]]:
    ordered = sorted((int(start), int(stop)) for start, stop in intervals if stop >= start)
    merged: list[tuple[int, int]] = []
    for start, stop in ordered:
        if not merged or start > merged[-1][1]:
            merged.append((start, stop))
        else:
            merged[-1] = (merged[-1][0], max(merged[-1][1], stop))
    return merged


def _interval_length(intervals: Iterable[tuple[int, int]]) -> int:
    return sum(stop - start for start, stop in _merge_intervals(intervals))


def _intersect_length(
    left: Iterable[tuple[int, int]], right: Iterable[tuple[int, int]],
) -> int:
    a = _merge_intervals(left)
    b = _merge_intervals(right)
    i = j = total = 0
    while i < len(a) and j < len(b):
        start = max(a[i][0], b[j][0])
        stop = min(a[i][1], b[j][1])
        if stop > start:
            total += stop - start
        if a[i][1] <= b[j][1]:
            i += 1
        else:
            j += 1
    return total


def _derive_timing(
    report: Mapping[str, Any], snapshots: Mapping[str, Mapping[str, Any]],
    wall_s: float, outer: Mapping[str, Any] | None,
) -> dict[str, Any]:
    controller = snapshots.get("controller")
    workers = {role: value for role, value in snapshots.items() if WORKER_RE.fullmatch(role)}
    if controller is None or len(workers) != EXPECTED_WORKERS:
        raise RuntimeError("probe-process-cardinality")
    terminal_start = controller.get("terminal_session_start")
    if not isinstance(terminal_start, dict) or not isinstance(terminal_start.get("perf_ns"), int):
        raise RuntimeError("terminal-session-start")
    session_start = int(terminal_start["perf_ns"])
    wall_ns = round(wall_s * 1_000_000_000)
    terminal_point = session_start + wall_ns

    offsets: dict[str, int] = {}
    clock_drift: dict[str, int] = {}
    clock_offset_samples: dict[str, list[int]] = {}
    for role, snapshot in snapshots.items():
        offset, drift, samples = _clock_offsets(snapshot)
        offsets[role] = offset
        clock_drift[role] = drift
        clock_offset_samples[role] = samples

    report_intervals: dict[str, list[tuple[int, int]]] = defaultdict(list)
    probe_duration_ns: dict[str, int] = defaultdict(int)
    report_event_count = 0
    phase_counts: dict[str, int] = defaultdict(int)
    for role, snapshot in workers.items():
        offset = offsets[role]
        for event in snapshot.get("reports", []):
            if not isinstance(event, dict):
                continue
            start = int(event["start_epoch_ns"]) - offset
            stop = int(event["stop_epoch_ns"]) - offset
            duration = int(event["duration_ns"])
            if stop < start or duration < 0:
                raise RuntimeError("report-clock-order")
            report_intervals[role].append((start, stop))
            probe_duration_ns[role] += duration
            report_event_count += 1
            phase_counts[str(event.get("when", ""))] += 1

    w_star, r_s = _max_occupancy(report)
    if w_star not in report_intervals:
        raise RuntimeError("w-star-worker-snapshot-missing")
    w_intervals = _merge_intervals(report_intervals[w_star])
    all_intervals = _merge_intervals(
        interval for values in report_intervals.values() for interval in values
    )
    if not w_intervals or not all_intervals:
        raise RuntimeError("report-intervals-empty")
    first_w = w_intervals[0][0]
    last_w = w_intervals[-1][1]
    last_all = all_intervals[-1][1]
    r_ns = round(r_s * 1_000_000_000)
    parts_ns = {
        "A": first_w - session_start,
        "B": (last_w - first_w) - r_ns,
        "D": last_all - last_w,
        "C": terminal_point - last_all,
    }
    residual_ns = wall_ns - r_ns
    algebraic_error_ns = residual_ns - sum(parts_ns.values())

    union_clipped = [
        (max(start, session_start), min(stop, terminal_point))
        for start, stop in all_intervals
        if stop > session_start and start < terminal_point
    ]
    union_ns = _interval_length(union_clipped)
    complement_ns = wall_ns - union_ns

    protocols = [
        (int(value["begin_perf_ns"]), int(value["end_perf_ns"]))
        for value in workers[w_star].get("protocols", [])
        if isinstance(value, dict)
    ]
    window = [(first_w, last_w)]
    report_in_window = [
        (max(start, first_w), min(stop, last_w))
        for start, stop in w_intervals if stop > first_w and start < last_w
    ]
    protocol_nonreport_ns = min(
        max(parts_ns["B"], 0),
        max(
            0,
            _intersect_length(protocols, window)
            - _intersect_length(protocols, report_in_window),
        ),
    )
    b_children = {
        "within_probe_protocol_nonreport_s": protocol_nonreport_ns / 1e9,
        "unclassified_outer_protocol_s": (parts_ns["B"] - protocol_nonreport_ns) / 1e9,
    }
    workerfinished = _event_values(controller, "workerfinished_received")
    workerfinished_times = [int(value["perf_ns"]) for value in workerfinished]
    c_children: dict[str, float] = {}
    if workerfinished_times:
        final_received = max(workerfinished_times)
        if last_all <= final_received <= terminal_point:
            c_children = {
                "last_report_to_workerfinished_received_s": (final_received - last_all) / 1e9,
                "workerfinished_received_to_terminal_point_s": (
                    terminal_point - final_received
                ) / 1e9,
            }
        else:
            c_children = {"unclassified_terminal_interval_s": parts_ns["C"] / 1e9}

    terminal_lower_events = _event_values(controller, "terminal_summary_exit")
    terminal_upper_events = _event_values(controller, "sessionfinish_exit")
    if len(terminal_lower_events) != 1 or len(terminal_upper_events) != 1:
        raise RuntimeError("terminal-bound-events")
    terminal_lower = int(terminal_lower_events[0]["perf_ns"])
    terminal_upper = int(terminal_upper_events[0]["perf_ns"])
    outside_wall_s = None
    runner_to_session_s = None
    if isinstance(outer, dict):
        outside = outer.get("outer_wall_ns")
        runner = outer.get("runner_start")
        if isinstance(outside, int):
            outside_wall_s = outside / 1e9
        if isinstance(runner, dict) and isinstance(runner.get("perf_ns"), int):
            runner_to_session_s = (session_start - int(runner["perf_ns"])) / 1e9

    occupancy = report["worker_occupancy"]
    occupancy_comparison = {
        role: {
            "probe_report_duration_s": probe_duration_ns[role] / 1e9,
            "production_report_duration_s": float(occupancy[role]["duration_s"]),
            "absolute_difference_s": abs(
                probe_duration_ns[role] / 1e9 - float(occupancy[role]["duration_s"])
            ),
        }
        for role in sorted(workers)
        if role in occupancy
    }
    protocol_count = sum(len(value.get("protocols", [])) for value in workers.values())
    controller_report_event_count = int(controller.get("controller_report_event_count", 0))
    max_occupancy_difference = max(
        (value["absolute_difference_s"] for value in occupancy_comparison.values()),
        default=math.inf,
    )
    phases_valid = set(phase_counts).issubset({"setup", "call", "teardown"})
    independent_checks = {
        "outer_wall_bounds_pytest_wall": (
            outside_wall_s is not None and outside_wall_s + 0.001 >= wall_s
        ),
        "terminal_point_within_hook_bounds_allowing_stdout_rounding": (
            terminal_lower - 6_000_000 <= terminal_point <= terminal_upper + 6_000_000
        ),
        "report_event_count_at_least_finished": report_event_count >= len(report.get("finished", [])),
        "controller_and_worker_report_event_counts_match": (
            controller_report_event_count == report_event_count
        ),
        "report_phases_closed": phases_valid,
        "worker_mapping_matches": set(workers) == set(occupancy),
        "protocol_count_matches_finished": protocol_count == len(report.get("finished", [])),
        "protocol_spans_cover_worker_reports": all(
            protocols_for_worker
            and min(begin for begin, _ in protocols_for_worker) <= min(
                begin for begin, _ in report_intervals[role]
            )
            and max(end for _, end in protocols_for_worker) >= max(
                end for _, end in report_intervals[role]
            )
            for role, snapshot in workers.items()
            for protocols_for_worker in [[
                (int(value["begin_perf_ns"]), int(value["end_perf_ns"]))
                for value in snapshot.get("protocols", []) if isinstance(value, dict)
            ]]
        ),
        "probe_durations_match_production_report": max_occupancy_difference <= 0.010,
        "wall_exposure_intervals_nonnegative": all(value >= 0 for value in parts_ns.values()),
        "report_union_is_within_wall": 0 <= union_ns <= wall_ns,
    }
    hook_errors = {
        role: value.get("hook_order_errors", [])
        for role, value in snapshots.items()
        if value.get("hook_order_errors")
    }
    stop_checks = {
        "clock_offset_drift_within_5ms": max(clock_drift.values()) <= MAX_CLOCK_DRIFT_NS,
        "hook_execution_order_expected": not hook_errors,
    }
    non_additive = {
        "clock_offset_drift_ns_by_process": clock_drift,
        "clock_offset_samples_ns_by_process": clock_offset_samples,
        "protocol_span_s_by_worker": {
            role: (
                (max(int(value["end_perf_ns"]) for value in snapshot.get("protocols", []))
                 - min(int(value["begin_perf_ns"]) for value in snapshot.get("protocols", []))) / 1e9
                if snapshot.get("protocols") else 0.0
            )
            for role, snapshot in workers.items()
        },
        "makereport_service_sum_s": sum(
            int(value["end_perf_ns"]) - int(value["begin_perf_ns"])
            for snapshot in workers.values()
            for value in snapshot.get("makereports", [])
        ) / 1e9,
        "serialization_service_sum_s": sum(
            int(value["end_perf_ns"]) - int(value["begin_perf_ns"])
            for snapshot in workers.values()
            for value in snapshot.get("serializations", [])
        ) / 1e9,
        "controller_workerfinished_received_count": len(workerfinished_times),
        "process_write_measurements_ns": _process_write_measurements(snapshots),
        "production_probe_duration_comparison": occupancy_comparison,
        "hook_order_errors": hook_errors,
    }
    session_external: dict[str, float] = {}
    if outside_wall_s is not None:
        session_external["runner_outer_wall_s"] = outside_wall_s
    if runner_to_session_s is not None:
        session_external["runner_start_to_pytest_session_s"] = runner_to_session_s
    return {
        "wall_s": wall_s,
        "R_w_star_s": r_s,
        "w_star": w_star,
        "residual_s": residual_ns / 1e9,
        "wall_exposure_intervals_s": {
            name: value / 1e9 for name, value in parts_ns.items()
        },
        "B_additive_children_s": b_children,
        "C_additive_children_s": c_children,
        "all_worker_report_union_s": union_ns / 1e9,
        "no_worker_reporting_complement_s": complement_ns / 1e9,
        "algebraic_identity": {
            "expression": "A+B+D+C == wall-R_w_star",
            "error_ns": algebraic_error_ns,
            "classification": "algebraic identity, not validation",
        },
        "terminal_bounds_s_from_session_start": {
            "lower": (terminal_lower - session_start) / 1e9,
            "upper": (terminal_upper - session_start) / 1e9,
            "pytest_stdout_wall": wall_s,
        },
        "independent_checks": independent_checks,
        "timing_stop_conditions": stop_checks,
        "non_additive_diagnostics": non_additive,
        "outside_residual_table": session_external,
        "report_event_count": report_event_count,
        "controller_report_event_count": controller_report_event_count,
        "report_phase_counts": dict(sorted(phase_counts.items())),
        "protocol_event_count": protocol_count,
    }


def _d1299(
    report: Mapping[str, Any], outer: Mapping[str, Any] | None,
) -> dict[str, Any]:
    worker_digests = report.get("worker_collection_digests", [])
    unique_digests = sorted(set(worker_digests)) if isinstance(worker_digests, list) else []
    result: dict[str, Any] = {
        "K": int(report["shard_count"]),
        "worker_count": len(report.get("worker_occupancy", {})),
        "collection_digest": _universe_digest(report),
        "worker_collection_digests": unique_digests,
    }
    if isinstance(outer, dict):
        if isinstance(outer.get("tested_tip"), str):
            result["tested_tip"] = outer["tested_tip"]
        growth = outer.get("growth_hold")
        if isinstance(growth, dict) and isinstance(growth.get("effective_opt_in"), bool):
            result["growth_hold_effective_opt_in"] = growth["effective_opt_in"]
    else:
        request_paths = []
        junit = report.get("junit_path")
        if isinstance(junit, str):
            shard_root = Path(junit).parent
            request_paths = sorted(shard_root.glob("dispatch/*/request.json"))
        if len(request_paths) == 1:
            request = _read_json(request_paths[0])
            tested = request.get("runner_binding", {}).get("tested_main")
            if isinstance(tested, str):
                result["tested_tip"] = tested
            environment = request.get("environment", {})
            if isinstance(environment, dict):
                result["growth_hold_effective_opt_in"] = (
                    environment.get(GROWTH_ENV) == GROWTH_TOKEN
                )
    return result


def _calibration_timing(
    snapshots: Mapping[str, Mapping[str, Any]], wall_s: float,
    outer: Mapping[str, Any] | None,
) -> dict[str, Any]:
    controller = snapshots.get("controller")
    workers = {role: value for role, value in snapshots.items() if WORKER_RE.fullmatch(role)}
    if controller is None or len(workers) != EXPECTED_WORKERS:
        raise RuntimeError("calibration-process-cardinality")
    drifts: dict[str, int] = {}
    for role, snapshot in snapshots.items():
        _, drift, _ = _clock_offsets(snapshot)
        drifts[role] = drift
    ready = _event_values(controller, "testnodeready")
    collections = _event_values(controller, "node_collection_finished_received")
    start = controller.get("terminal_session_start", {}).get("perf_ns")
    result: dict[str, Any] = {
        "classification": CALIBRATION_KIND,
        "wall_s": wall_s,
        "worker_process_count": len(workers),
        "worker_ready_event_count": len(ready),
        "worker_collection_event_count": len(collections),
        "clock_offset_drift_ns_by_process": drifts,
        "timing_stop_conditions": {
            "clock_offset_drift_within_5ms": max(drifts.values()) <= MAX_CLOCK_DRIFT_NS,
            "hook_execution_order_expected": all(
                not snapshot.get("hook_order_errors") for snapshot in snapshots.values()
            ),
            "worker_ready_event_count_is_48": len(ready) == EXPECTED_WORKERS,
            "worker_collection_event_count_is_48": len(collections) == EXPECTED_WORKERS,
        },
        "non_additive_diagnostics": {
            "process_write_measurements_ns": _process_write_measurements(snapshots),
        },
    }
    if isinstance(start, int) and ready and collections:
        final_ready = max(int(value["perf_ns"]) for value in ready)
        final_collection = max(int(value["perf_ns"]) for value in collections)
        result["milestones_s_from_pytest_session"] = {
            "all_workers_ready": (final_ready - start) / 1e9,
            "all_collections_received": (final_collection - start) / 1e9,
        }
    if isinstance(outer, dict) and isinstance(outer.get("runner_start"), dict):
        runner = outer["runner_start"].get("perf_ns")
        if isinstance(start, int) and isinstance(runner, int):
            result["outside_residual_table"] = {
                "runner_start_to_pytest_session_s": (start - runner) / 1e9,
            }
    return result


def _recorded_arm_fields(
    report: Mapping[str, Any] | None,
    outer: Mapping[str, Any] | None,
) -> dict[str, Any]:
    red_nodeids: list[str] | None = None
    terminal_counts: dict[str, int] | None = None
    rc: int | None = None
    if isinstance(report, Mapping):
        failures = report.get("failures")
        counts = report.get("terminal_counts")
        pytest_rc = report.get("pytest_rc")
        if isinstance(failures, list) and all(
            isinstance(nodeid, str) for nodeid in failures
        ):
            red_nodeids = list(failures)
        if isinstance(counts, dict) and all(
            isinstance(name, str)
            and isinstance(count, int)
            and not isinstance(count, bool)
            and count >= 0
            for name, count in counts.items()
        ):
            terminal_counts = dict(counts)
        if isinstance(pytest_rc, int) and not isinstance(pytest_rc, bool):
            rc = pytest_rc
    hostname: str | None = None
    openssl_version: Mapping[str, Any] | None = None
    if isinstance(outer, Mapping):
        outer_rc = outer.get("runner_returncode")
        if isinstance(outer_rc, int) and not isinstance(outer_rc, bool):
            rc = outer_rc
        raw_hostname = outer.get("hostname")
        if isinstance(raw_hostname, str):
            hostname = raw_hostname
        raw_openssl = outer.get("openssl_version")
        if isinstance(raw_openssl, Mapping):
            openssl_version = dict(raw_openssl)
    return {
        "rc": rc,
        "red_nodeids": red_nodeids,
        "terminal_counts": terminal_counts,
        "environment": {
            "hostname": hostname,
            "openssl_version": openssl_version,
        },
    }


def _summarize_arm(session: Path, spec: tuple[str, int, str, str]) -> dict[str, Any]:
    arm, shard, probe, kind = spec
    shard_root = session / f"shard-{shard}"
    report_path = shard_root / "report.json"
    if not report_path.is_file():
        result: dict[str, Any] = {
            "arm": arm, "shard_index": shard, "probe": probe, "kind": kind,
            "artifact_state": "stopped-before-report",
        }
        outer_path = shard_root / "outer.json"
        outer = None
        if outer_path.is_file():
            outer = _read_json(outer_path)
            result["stop_conditions"] = outer.get("stop_conditions", {})
            if isinstance(outer.get("disturbed"), bool):
                result["disturbed"] = outer["disturbed"]
            if isinstance(outer.get("isolation"), dict):
                result["isolation"] = outer["isolation"]
        result.update(_recorded_arm_fields(None, outer))
        return result
    report = _read_json(report_path)
    wall_s, wall_source = _find_wall(shard_root)
    worker, maximum = _max_occupancy(report)
    outer_path = shard_root / "outer.json"
    outer = _read_json(outer_path) if outer_path.is_file() else None
    result = {
        "arm": arm,
        "shard_index": shard,
        "probe": probe,
        "kind": kind,
        "artifact_state": "report-present",
        "wall_s": wall_s,
        "wall_source": wall_source,
        "R_w_star_s": maximum,
        "w_star": worker,
        "residual_s": wall_s - maximum,
        "selected_count": len(report.get("selected", [])),
        "finished_count": len(report.get("finished", [])),
        "observed_universe": {
            "count": len(report.get("observed_universe", [])),
            "digest": _universe_digest(report),
        },
        "D1299": _d1299(report, outer),
        "stop_conditions": _local_report_checks(report, shard, kind),
        **_recorded_arm_fields(report, outer),
    }
    if isinstance(outer, dict):
        result["cache"] = {
            "before": outer.get("cache_before", {}),
            "after": outer.get("cache_after", {}),
        }
        result["isolation"] = outer.get("isolation", {})
        result["disturbed"] = bool(outer.get("disturbed", False))
        result["stop_conditions"].update(outer.get("stop_conditions", {}))
    if probe != "none":
        snapshots, snapshot_issues = _read_process_snapshots(shard_root / "probe")
        result["probe_snapshot_issues"] = snapshot_issues
        result["probe_snapshot_pair_complete"] = not snapshot_issues
        result["injection_environment_restore"] = _environment_restore_summary(
            snapshots
        )
        result["D1299"]["worker_count"] = sum(
            1 for role in snapshots if WORKER_RE.fullmatch(role)
        )
        result["hook_execution_order"] = {
            role: {
                "registered_call_order": snapshot.get("hook_orders", {}),
                "observed_probe_marker_sequence": [
                    event.get("name")
                    for event in snapshot.get("events", [])
                    if isinstance(event, dict) and isinstance(event.get("name"), str)
                ],
            }
            for role, snapshot in snapshots.items()
        }
        if kind == "real" and probe == "timing":
            timing = _derive_timing(report, snapshots, wall_s, outer)
            for key, value in timing.items():
                if key in {"wall_s", "R_w_star_s", "w_star", "residual_s"}:
                    continue
                result[key] = value
            result["stop_conditions"].update(timing["timing_stop_conditions"])
        elif kind == "zero" and probe == "timing":
            timing = _calibration_timing(snapshots, wall_s, outer)
            result["calibration_timing"] = timing
            result["stop_conditions"].update(timing["timing_stop_conditions"])
        else:
            result["calibration"] = {"classification": CALIBRATION_KIND}
            result["stop_conditions"]["hook_execution_order_expected"] = all(
                not snapshot.get("hook_order_errors") for snapshot in snapshots.values()
            )
            selector_drifts = {
                role: _clock_offsets(snapshot)[1]
                for role, snapshot in snapshots.items()
            }
            result["calibration"]["clock_offset_drift_ns_by_process"] = selector_drifts
            result["stop_conditions"]["clock_offset_drift_within_5ms"] = (
                max(selector_drifts.values()) <= MAX_CLOCK_DRIFT_NS
            )
    return result


def _summarize_arm_error(
    session: Path, spec: tuple[str, int, str, str], exc: Exception,
) -> dict[str, Any]:
    arm, shard, probe, kind = spec
    shard_root = session / f"shard-{shard}"
    result: dict[str, Any] = {
        "arm": arm,
        "shard_index": shard,
        "probe": probe,
        "kind": kind,
        "artifact_state": "aggregation-stopped",
        "aggregation_error": f"{type(exc).__name__}:{exc}",
    }
    outer_path = shard_root / "outer.json"
    outer = None
    if outer_path.is_file():
        try:
            candidate = _read_json(outer_path)
            if not isinstance(candidate, dict):
                raise RuntimeError("outer-json-shape")
            outer = candidate
            result["stop_conditions"] = outer.get("stop_conditions", {})
            result["disturbed"] = bool(outer.get("disturbed", False))
            if isinstance(outer.get("isolation"), dict):
                result["isolation"] = outer["isolation"]
            result["cache"] = {
                "before": outer.get("cache_before", {}),
                "after": outer.get("cache_after", {}),
            }
        except Exception as outer_exc:
            result["outer_artifact_error"] = (
                f"{type(outer_exc).__name__}:{outer_exc}"
            )
    report_path = shard_root / "report.json"
    report = None
    if report_path.is_file():
        try:
            report = _read_json(report_path)
            wall_s, wall_source = _find_wall(shard_root)
            worker, maximum = _max_occupancy(report)
            result.update({
                "wall_s": wall_s,
                "wall_source": wall_source,
                "R_w_star_s": maximum,
                "w_star": worker,
                "residual_s": wall_s - maximum,
                "observed_universe": {
                    "count": len(report.get("observed_universe", [])),
                    "digest": _universe_digest(report),
                },
            })
        except Exception as partial_exc:
            result["raw_report_error"] = f"{type(partial_exc).__name__}:{partial_exc}"
    result.update(_recorded_arm_fields(report, outer))
    return result


def _contrast(arms: Mapping[str, Mapping[str, Any]]) -> dict[str, Any]:
    pairs = (
        ("R2-B1", "R2-A1"), ("R2-B2", "R2-A2"),
        ("R1-B1", "R1-A1"), ("R1-B2", "R1-A2"),
        ("Z-B1", "Z-S1"),
    )
    rows = []
    for instrumented, control in pairs:
        left = arms.get(instrumented)
        right = arms.get(control)
        if not isinstance(left, dict) or not isinstance(right, dict):
            continue
        values = {}
        for field in ("wall_s", "R_w_star_s", "residual_s"):
            if isinstance(left.get(field), (int, float)) and isinstance(
                right.get(field), (int, float)
            ):
                values[field] = {
                    "instrumented": float(left[field]),
                    "control": float(right[field]),
                    "difference": float(left[field]) - float(right[field]),
                }
        rows.append({
            "instrumented_arm": instrumented,
            "control_arm": control,
            "raw_values_and_difference": values,
        })
    outcome_rows = []
    for instrumented, control in pairs[:-1]:
        left = arms.get(instrumented)
        right = arms.get(control)
        row: dict[str, Any] = {
            "instrumented_arm": instrumented,
            "control_arm": control,
        }
        left_red = left.get("red_nodeids") if isinstance(left, Mapping) else None
        right_red = right.get("red_nodeids") if isinstance(right, Mapping) else None
        if (
            isinstance(left_red, list)
            and all(isinstance(nodeid, str) for nodeid in left_red)
            and isinstance(right_red, list)
            and all(isinstance(nodeid, str) for nodeid in right_red)
        ):
            instrumented_red = set(left_red)
            control_red = set(right_red)
            row.update({
                "comparison_available": True,
                "probe_changes_outcomes": instrumented_red != control_red,
                "instrumented_red_count": len(instrumented_red),
                "control_red_count": len(control_red),
                "added_red_nodeids": sorted(instrumented_red - control_red),
                "removed_red_nodeids": sorted(control_red - instrumented_red),
            })
        else:
            row.update({
                "comparison_available": False,
                "unavailable_reason": "red-nodeid-set-unavailable",
            })
        outcome_rows.append(row)
    return {
        "paired_raw_differences": rows,
        "red_nodeid_outcome_comparisons": outcome_rows,
    }


def _cross_universe(arms: Mapping[str, Mapping[str, Any]]) -> dict[str, Any]:
    by_shard: dict[int, set[tuple[int, str]]] = defaultdict(set)
    for value in arms.values():
        observed = value.get("observed_universe")
        shard = value.get("shard_index")
        if isinstance(shard, int) and isinstance(observed, dict):
            count = observed.get("count")
            digest = observed.get("digest")
            if isinstance(count, int) and isinstance(digest, str):
                by_shard[shard].add((count, digest))
    stable_within = all(len(values) <= 1 for values in by_shard.values())
    comparable = 1 in by_shard and 2 in by_shard and len(by_shard[1]) == len(by_shard[2]) == 1
    match = comparable and by_shard[1] == by_shard[2]
    return {
        "stable_within_each_shard": stable_within,
        "shard_1_and_2_observed": comparable,
        "shard_1_equals_shard_2": match,
        "observations_by_shard": {
            str(shard): [
                {"count": count, "digest": digest}
                for count, digest in sorted(values)
            ]
            for shard, values in sorted(by_shard.items())
        },
    }


def command_summarize(args: argparse.Namespace) -> int:
    root = args.root.resolve()
    if not SAFE_TAG_RE.fullmatch(args.job_tag):
        raise RuntimeError("unsafe-job-tag")
    arms: dict[str, Mapping[str, Any]] = {}
    missing: list[str] = []
    for spec in ARM_SPECS:
        arm = spec[0]
        session = root / f"{args.job_tag}-{arm}"
        if not session.is_dir():
            missing.append(arm)
            continue
        try:
            arms[arm] = _summarize_arm(session, spec)
        except Exception as exc:
            arms[arm] = _summarize_arm_error(session, spec, exc)
    cross = _cross_universe(arms)
    for arm in arms.values():
        if "stop_conditions" in arm and cross["shard_1_and_2_observed"]:
            arm["stop_conditions"]["shard_1_and_2_universe_equal"] = cross[
                "shard_1_equals_shard_2"
            ]
    summary = {
        "schema_version": SCHEMA,
        "job_tag": args.job_tag,
        "scope": "one PBS job, one hostname, this checkout only",
        "arm_order": [entry[0] for entry in ARM_SPECS],
        "arms": arms,
        "missing_arms": missing,
        "cross_arm_stop_conditions": {
            "observed_universe": cross,
        },
        "probe_presence_controls": _contrast(arms),
    }
    _atomic_json(args.out.resolve(), summary)
    print(json.dumps({
        "schema_version": SCHEMA,
        "arm_count": len(arms),
        "missing_arm_count": len(missing),
        "out": str(args.out.resolve()),
    }, sort_keys=True))
    return 0


def command_check_progress(args: argparse.Namespace) -> int:
    root = args.root.resolve()
    if not SAFE_TAG_RE.fullmatch(args.job_tag):
        raise RuntimeError("unsafe-job-tag")
    arms: dict[str, Mapping[str, Any]] = {}
    failures: list[str] = []
    aggregation_errors: list[dict[str, str]] = []
    for spec in ARM_SPECS:
        session = root / f"{args.job_tag}-{spec[0]}"
        if not session.is_dir():
            continue
        try:
            value = _summarize_arm(session, spec)
            arms[spec[0]] = value
            if not _checks_pass(value.get("stop_conditions", {})):
                failures.append(f"{spec[0]}:local-stop-condition")
        except Exception as exc:
            value = _summarize_arm_error(session, spec, exc)
            arms[spec[0]] = value
            aggregation_errors.append({
                "arm": spec[0],
                "error": f"{type(exc).__name__}:{exc}",
            })
            if not _checks_pass(value.get("stop_conditions", {})):
                failures.append(f"{spec[0]}:local-stop-condition")
    cross = _cross_universe(arms)
    if cross["shard_1_and_2_observed"] and not cross["shard_1_equals_shard_2"]:
        failures.append("shard-1-shard-2-universe-mismatch")
    value = {
        "schema_version": "izanagi-t2097-progress/v1",
        "job_tag": args.job_tag,
        "completed_arms": list(arms),
        "failures": failures,
        "aggregation_errors": aggregation_errors,
        "cross_universe": cross,
    }
    _atomic_json(root / f"{args.job_tag}-progress.json", value)
    return 4 if failures else 0


def _junit_longest(path: Path) -> float:
    root = ET.parse(path).getroot()
    longest = 0.0
    for testcase in root.iter("testcase"):
        raw = testcase.attrib.get("time")
        if raw is None:
            continue
        value = float(raw)
        if not math.isfinite(value) or value < 0:
            raise RuntimeError("junit-duration-shape")
        longest = max(longest, value)
    if longest <= 0:
        raise RuntimeError("junit-longest-unavailable")
    return longest


def _archive_session(root: Path, prefix: str) -> Path:
    matches = sorted(
        path for path in root.glob(prefix + "*")
        if path.is_dir() and re.fullmatch(r"[0-9a-f]{32}", path.name)
    )
    if len(matches) != 1:
        raise RuntimeError(f"archive-session-prefix:{prefix}:{len(matches)}")
    return matches[0]


def _archive_request(shard_root: Path) -> Mapping[str, Any]:
    paths = sorted(shard_root.glob("dispatch/*/request.json"))
    if len(paths) != 1:
        raise RuntimeError("archive-request-count")
    value = _read_json(paths[0])
    if not isinstance(value, dict):
        raise RuntimeError("archive-request-shape")
    return value


def command_recompute_archive(args: argparse.Namespace) -> int:
    root = args.root.resolve()
    sessions = []
    row_count = 0
    for prefix in ARCHIVE_SESSION_PREFIXES:
        session = _archive_session(root, prefix)
        rows = []
        tips: set[str] = set()
        for shard in range(3):
            shard_root = session / f"shard-{shard}"
            report = _read_json(shard_root / "report.json")
            wall_s, wall_source = _find_wall(shard_root)
            worker, actual_max_s = _max_occupancy(report)
            occupancy = report["worker_occupancy"]
            total_report_s = sum(
                float(entry["duration_s"]) for entry in occupancy.values()
            )
            worker_count = len(occupancy)
            if worker_count != EXPECTED_WORKERS:
                raise RuntimeError("archive-worker-count")
            longest_s = _junit_longest(shard_root / "junit.xml")
            lower_bound_worker_s = max(longest_s, total_report_s / worker_count)
            request = _archive_request(shard_root)
            tested_tip = request.get("runner_binding", {}).get("tested_main")
            if not isinstance(tested_tip, str):
                raise RuntimeError("archive-tested-tip")
            tips.add(tested_tip)
            rows.append({
                "shard_index": shard,
                "wall_s": wall_s,
                "wall_source": wall_source,
                "actual_max_worker": worker,
                "actual_max_worker_report_duration_s": actual_max_s,
                "residual_s": wall_s - actual_max_s,
                "lower_bound_inputs": {
                    "longest_single_s": longest_s,
                    "longest_single_source": "junit.xml testcase time (millisecond-rounded)",
                    "total_report_duration_s": total_report_s,
                    "total_report_duration_source": "report.json worker_occupancy sum",
                    "worker_count": worker_count,
                },
                "lower_bound_worker_s": lower_bound_worker_s,
                "lower_bound_residual_s": wall_s - lower_bound_worker_s,
                "collection_digest": _universe_digest(report),
                "tested_tip": tested_tip,
            })
            row_count += 1
        if len(tips) != 1:
            raise RuntimeError("archive-tested-tip-mismatch")
        sessions.append({
            "session": session.name,
            "tested_tip": next(iter(tips)),
            "shards": rows,
        })
    value = {
        "schema_version": ARCHIVE_SCHEMA,
        "archive_session_count": len(sessions),
        "row_count": row_count,
        "actual_residual_source_contract": (
            "pytest wall from each shard PBS stdout minus the unrounded measured maximum "
            "from report.json worker_occupancy"
        ),
        "sessions": sessions,
    }
    _atomic_json(args.out.resolve(), value)
    print(json.dumps({
        "schema_version": ARCHIVE_SCHEMA,
        "archive_session_count": len(sessions),
        "row_count": row_count,
        "out": str(args.out.resolve()),
    }, sort_keys=True))
    return 0


def _ancestor_pids(pid: int) -> set[int]:
    result = {pid}
    current = pid
    while current > 1:
        value = _proc_stat(current)
        if value is None:
            break
        parent = int(value["ppid"])
        if parent <= 0 or parent in result:
            break
        result.add(parent)
        current = parent
    return result


def command_preflight_consumers(args: argparse.Namespace) -> int:
    root = args.root.resolve()
    root_bytes = os.fsencode(str(root))
    exempt = _ancestor_pids(os.getpid())
    consumers: list[dict[str, Any]] = []
    scanned = 0
    visibility_errors = 0
    processes, stat_errors = _all_processes()
    visibility_errors += stat_errors
    for pid, process in sorted(processes.items()):
        if pid in exempt:
            continue
        scanned += 1
        evidence: list[str] = []
        try:
            cmdline = Path(f"/proc/{pid}/cmdline").read_bytes()
            if root_bytes in cmdline:
                evidence.append("cmdline")
        except OSError:
            visibility_errors += 1
        try:
            fds = list(Path(f"/proc/{pid}/fd").iterdir())
        except OSError:
            visibility_errors += 1
            fds = []
        for fd in fds:
            try:
                target = os.readlink(fd)
            except OSError:
                continue
            try:
                target_path = Path(target).resolve(strict=False)
                target_path.relative_to(root)
            except (OSError, ValueError):
                continue
            evidence.append("open-fd-under-shared-root")
            break
        if evidence:
            consumers.append({
                "pid": pid,
                "starttime_ticks": process["starttime"],
                "comm": process["comm"],
                "evidence": sorted(set(evidence)),
            })
    value = {
        "schema_version": "izanagi-t2097-consumer-preflight/v1",
        "shared_root": str(root),
        "sample": _now(),
        "scanned_non_ancestor_process_count": scanned,
        "process_visibility_errors": visibility_errors,
        "consumer_count": len(consumers),
        "consumers": consumers,
        "passed": not consumers,
    }
    _atomic_json(args.out.resolve(), value)
    print(json.dumps({
        "consumer_count": len(consumers),
        "process_visibility_errors": visibility_errors,
        "passed": value["passed"],
        "out": str(args.out.resolve()),
    }, sort_keys=True))
    return 0 if value["passed"] else 4


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    summarize = subparsers.add_parser("summarize")
    summarize.add_argument("--root", type=Path, required=True)
    summarize.add_argument("--job-tag", required=True)
    summarize.add_argument("--out", type=Path, required=True)
    summarize.set_defaults(function=command_summarize)

    archive = subparsers.add_parser("recompute-archive")
    archive.add_argument("--root", type=Path, required=True)
    archive.add_argument("--out", type=Path, required=True)
    archive.set_defaults(function=command_recompute_archive)

    run_arm = subparsers.add_parser("run-arm")
    run_arm.add_argument("--root", type=Path, required=True)
    run_arm.add_argument("--job-tag", required=True)
    run_arm.add_argument("--arm", required=True)
    run_arm.add_argument("--shard", type=int, choices=(1, 2), required=True)
    run_arm.add_argument("--probe", choices=("none", "selector", "timing"), required=True)
    run_arm.add_argument("--repo", type=Path, required=True)
    run_arm.add_argument("--python", type=Path, required=True)
    run_arm.add_argument("--probe-source", type=Path, required=True)
    run_arm.add_argument("--pbs-source", type=Path, required=True)
    run_arm.set_defaults(function=command_run_arm)

    progress = subparsers.add_parser("check-progress")
    progress.add_argument("--root", type=Path, required=True)
    progress.add_argument("--job-tag", required=True)
    progress.set_defaults(function=command_check_progress)

    consumers = subparsers.add_parser("preflight-consumers")
    consumers.add_argument("--root", type=Path, required=True)
    consumers.add_argument("--out", type=Path, required=True)
    consumers.set_defaults(function=command_preflight_consumers)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    return int(args.function(args))


if __name__ == "__main__":
    raise SystemExit(main())
```
