#!/usr/bin/env python3
"""Measure condition-meaning-gate liveness for the three T-2228 drivers.

The probe deliberately imports production code from a separate node-local
clone for each driver.  Gate calls are observed through return events; no
production callable or root binding is replaced.
"""
from __future__ import annotations

import argparse
import contextlib
import dataclasses
import hashlib
import importlib
import json
import os
import shutil
import socket
import subprocess
import sys
import tempfile
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from types import ModuleType
from typing import Any, Callable, Mapping, Sequence


SCHEMA_VERSION = "izanagi-t2228-driver-gate-liveness/v1"
DRIVER_ORDER = ("s1", "repro", "sweep")
RESULT_NAMES = {
    "s1": "s1.json",
    "repro": "repro.json",
    "sweep": "sweep.json",
}
EXPECTED_DRIVER_IDS = {
    "s1": "orchestrator.campaign.s1_direct_comparison.prepare_cell",
    "repro": "orchestrator/campaign/backoff_repro.py",
    "sweep": "orchestrator/campaign/backoff_sweep.py",
}
PRODUCTION_RELATIVE_PATHS = (
    "orchestrator/campaign/backoff_sweep.py",
    "orchestrator/campaign/backoff_repro.py",
    "orchestrator/campaign/s1_direct_comparison.py",
    "orchestrator/campaign/condition_meaning_gate.py",
)
CURRENT_CCBENCH_PIN = "511c953"
REPRO_CCBENCH_PIN = "dff0f1e"
NETWORK_TARGET = ("github.com", 443)


@dataclass(frozen=True)
class _Production:
    root: Path
    sweep: ModuleType
    repro: ModuleType
    s1: ModuleType
    gate: ModuleType
    buildcache: ModuleType
    layout: ModuleType


@dataclass
class _GateObservation:
    requests: list[object] = field(default_factory=list)
    supply_records: list[object] = field(default_factory=list)
    meaning_records: list[object] = field(default_factory=list)
    admissions: list[object] = field(default_factory=list)


def _json_safe(value: object) -> Any:
    if dataclasses.is_dataclass(value):
        return {
            item.name: _json_safe(getattr(value, item.name))
            for item in dataclasses.fields(value)
            if item.metadata.get("canonical", True)
        }
    if isinstance(value, Mapping):
        return {
            str(key): _json_safe(item)
            for key, item in sorted(value.items(), key=lambda row: str(row[0]))
        }
    if isinstance(value, (tuple, list)):
        return [_json_safe(item) for item in value]
    if isinstance(value, (set, frozenset)):
        return sorted(_json_safe(item) for item in value)
    if isinstance(value, Path):
        return os.fspath(value)
    if value is None or type(value) in {bool, int, float, str}:
        return value
    as_dict = getattr(value, "as_dict", None)
    if callable(as_dict):
        return _json_safe(as_dict())
    raise TypeError(f"value is not JSON serializable: {type(value).__name__}")


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        while True:
            chunk = stream.read(1024 * 1024)
            if not chunk:
                break
            digest.update(chunk)
    return digest.hexdigest()


def _write_atomic_create_only(path: Path, payload: Mapping[str, Any]) -> None:
    """Durably stage JSON, then publish it atomically without replacement."""
    if not path.is_absolute():
        raise ValueError("evidence path must be absolute")
    if not path.parent.is_dir():
        raise FileNotFoundError(f"evidence directory does not exist: {path.parent}")
    encoded = (
        json.dumps(
            payload,
            ensure_ascii=False,
            sort_keys=True,
            indent=2,
            allow_nan=False,
        )
        + "\n"
    ).encode("utf-8")
    descriptor, temporary_name = tempfile.mkstemp(
        prefix=f".{path.name}.", suffix=".tmp", dir=path.parent,
    )
    temporary = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(encoded)
            stream.flush()
            os.fsync(stream.fileno())
        os.link(temporary, path)
        directory_fd = os.open(
            path.parent, os.O_RDONLY | getattr(os, "O_DIRECTORY", 0),
        )
        try:
            os.fsync(directory_fd)
        finally:
            os.close(directory_fd)
    finally:
        try:
            temporary.unlink()
        except FileNotFoundError:
            pass


def _run_git(root: Path, *args: str) -> str:
    completed = subprocess.run(
        ["git", "-C", os.fspath(root), *args],
        check=True,
        capture_output=True,
        text=True,
        timeout=60.0,
    )
    return completed.stdout.strip()


def _validate_repo_root(root: Path, expected_head: str) -> Path:
    if not root.is_absolute():
        raise ValueError(f"driver repository must be absolute: {root}")
    canonical = root.resolve(strict=True)
    if canonical != root or not canonical.is_dir():
        raise ValueError(f"driver repository must be a canonical directory: {root}")
    head = _run_git(canonical, "rev-parse", "HEAD")
    if head != expected_head:
        raise RuntimeError(
            f"driver repository HEAD mismatch: expected={expected_head} actual={head}"
        )
    status = _run_git(canonical, "status", "--porcelain", "--untracked-files=no")
    if status:
        raise RuntimeError(f"driver repository is not tracked-clean: {canonical}")
    alternates = canonical / ".git" / "objects" / "info" / "alternates"
    if alternates.exists():
        raise RuntimeError(f"driver repository uses object alternates: {canonical}")
    return canonical


def _purge_orchestrator_modules() -> None:
    for name in tuple(sys.modules):
        if name == "orchestrator" or name.startswith("orchestrator."):
            del sys.modules[name]


def _load_production(root: Path) -> _Production:
    """Import one complete production module family from exactly one clone."""
    _purge_orchestrator_modules()
    importlib.invalidate_caches()
    sys.path.insert(0, os.fspath(root))
    try:
        gate = importlib.import_module(
            "orchestrator.campaign.condition_meaning_gate"
        )
        sweep = importlib.import_module("orchestrator.campaign.backoff_sweep")
        repro = importlib.import_module("orchestrator.campaign.backoff_repro")
        s1 = importlib.import_module(
            "orchestrator.campaign.s1_direct_comparison"
        )
        buildcache = importlib.import_module("orchestrator.campaign.buildcache")
        layout = importlib.import_module("orchestrator.campaign.layout")
    finally:
        del sys.path[0]
    modules = {
        "orchestrator/campaign/backoff_sweep.py": sweep,
        "orchestrator/campaign/backoff_repro.py": repro,
        "orchestrator/campaign/s1_direct_comparison.py": s1,
        "orchestrator/campaign/condition_meaning_gate.py": gate,
    }
    for relative, module in modules.items():
        imported = Path(module.__file__).resolve(strict=True)
        expected = (root / relative).resolve(strict=True)
        if imported != expected:
            raise RuntimeError(
                f"production import escaped driver clone: {relative}: {imported}"
            )
    return _Production(root, sweep, repro, s1, gate, buildcache, layout)


class _GateObserver:
    """Retain exact production return objects without wrapping callables."""

    def __init__(
        self,
        gate: ModuleType,
        *,
        driver_id: str,
        stop_after_admission: bool,
    ) -> None:
        self.gate = gate
        self.driver_id = driver_id
        self.stop_after_admission = stop_after_admission
        self.observed = _GateObservation()
        self._previous: object = None
        self._active = False
        self._targets = {
            gate.make_define_request.__code__: (
                "request", gate.DefineRequest,
            ),
            gate.evaluate_define_supply_effectuation.__code__: (
                "supply", gate.ConditionArmRecord,
            ),
            gate.evaluate_define_runtime_meaning.__code__: (
                "meaning", gate.ConditionArmRecord,
            ),
            gate.require_condition_gate_family.__code__: (
                "admission", gate.ConditionFamilyAdmission,
            ),
        }

    def _stop(self) -> None:
        if self._active:
            sys.setprofile(self._previous)
            self._active = False

    def _profile(self, frame: object, event: str, value: object) -> None:
        if event != "return":
            return
        target = self._targets.get(frame.f_code)
        if target is None:
            return
        kind, expected_type = target
        if type(value) is expected_type:
            if kind == "request" and value.driver_id == self.driver_id:
                self.observed.requests.append(value)
            elif kind == "supply" and value.driver_id == self.driver_id:
                self.observed.supply_records.append(value)
            elif kind == "meaning" and value.driver_id == self.driver_id:
                self.observed.meaning_records.append(value)
            elif kind == "admission":
                self.observed.admissions.append(value)
        if kind == "admission" and self.stop_after_admission:
            self._stop()

    def __enter__(self) -> "_GateObserver":
        if self._active:
            raise RuntimeError("gate observer cannot be entered twice")
        self._previous = sys.getprofile()
        sys.setprofile(self._profile)
        self._active = True
        return self

    def __exit__(self, exc_type: object, exc: object, tb: object) -> None:
        self._stop()


def _exception_document(exc: BaseException) -> dict[str, Any]:
    seen: set[int] = set()

    def visit(current: BaseException | None) -> dict[str, Any] | None:
        if current is None:
            return None
        if id(current) in seen:
            return {
                "type": type(current).__name__,
                "module": type(current).__module__,
                "message": str(current),
                "reason_code": getattr(current, "reason_code", None),
                "cycle": True,
            }
        seen.add(id(current))
        traceback_rows = []
        traceback = current.__traceback__
        while traceback is not None:
            frame = traceback.tb_frame
            traceback_rows.append({
                "module": frame.f_globals.get("__name__"),
                "function": frame.f_code.co_name,
                "filename": Path(frame.f_code.co_filename).name,
                "line": traceback.tb_lineno,
            })
            traceback = traceback.tb_next
        return {
            "type": type(current).__name__,
            "module": type(current).__module__,
            "message": str(current),
            "reason_code": getattr(current, "reason_code", None),
            "traceback": traceback_rows,
            "suppress_context": bool(current.__suppress_context__),
            "cause": visit(current.__cause__),
            "context": visit(current.__context__),
        }

    document = visit(exc)
    assert document is not None
    return document


def _request_digest(gate: ModuleType, request: object) -> str:
    _spec, _requested, _default, companions = gate._validate_define_request(
        request
    )
    return gate._request_digest(request, companions)


def _observation_document(
    gate: ModuleType, observed: _GateObservation,
) -> dict[str, Any]:
    requests = []
    for request in observed.requests:
        requests.append({
            "driver_id": request.driver_id,
            "macro": request.macro,
            "route": request.route,
            "requested_value": request.requested_value,
            "default_value": request.default_value,
            "owner_tu": request.owner_tu,
            "target": request.target,
            "companion_defines": _json_safe(request.companion_defines),
            "stock_comparison": request.stock_comparison,
            "request_digest": _request_digest(gate, request),
        })

    def record_document(record: object) -> dict[str, Any]:
        canonical = record.canonical_json()
        return {
            "macro": record.macro,
            "arm": record.arm,
            "terminal_status": record.terminal_status,
            "reason_code": record.reason_code,
            "request_digest": record.request_digest,
            "record_id": record.record_id,
            "canonical_json": canonical,
            "document": json.loads(canonical),
        }

    admissions = []
    for admission in observed.admissions:
        canonical = admission.canonical_json()
        admissions.append({
            "admission_id": admission.admission_id,
            "admitted": admission.admitted,
            "record_ids": list(admission.record_ids),
            "unestablished_meaning_macros": (
                None
                if admission.unestablished_meaning_macros is None
                else list(admission.unestablished_meaning_macros)
            ),
            "canonical_json": canonical,
            "document": json.loads(canonical),
        })
    return {
        "requests": requests,
        "supply_records": [
            record_document(record) for record in observed.supply_records
        ],
        "meaning_records": [
            record_document(record) for record in observed.meaning_records
        ],
        "admissions": admissions,
    }


def _gate_success(gate: ModuleType, observed: _GateObservation) -> bool:
    inert = [
        request
        for request in observed.requests
        if type(request) is gate.DefineRequest
        and request.macro == "BACKOFF_FIXED"
        and request.requested_value == -1
        and request.stock_comparison is True
    ]
    if len(inert) != 1:
        return False
    digest = _request_digest(gate, inert[0])
    supply = [
        record
        for record in observed.supply_records
        if type(record) is gate.ConditionArmRecord
        and record.request_digest == digest
    ]
    meaning = [
        record
        for record in observed.meaning_records
        if type(record) is gate.ConditionArmRecord
        and record.request_digest == digest
    ]
    if len(supply) != 1 or len(meaning) != 1:
        return False
    if not all(
        type(record) is gate.ConditionArmRecord
        and record.driver_id == inert[0].driver_id
        and record.macro == inert[0].macro
        and record.request_digest == digest
        and record.terminal_status == "green"
        for record in (*supply, *meaning)
    ):
        return False
    admission = _validated_family_admission(
        gate,
        observed.supply_records,
        observed.meaning_records,
        observed.admissions,
    )
    return admission is not None and admission.admitted is True


def _validated_family_admission(
    gate: ModuleType,
    supply_records: Sequence[object],
    meaning_records: Sequence[object],
    admissions: Sequence[object],
) -> object | None:
    """Revalidate records and admission with the production family gate."""
    if len(admissions) != 1 \
            or type(admissions[0]) is not gate.ConditionFamilyAdmission:
        return None
    admission = admissions[0]
    try:
        expected = gate.require_condition_gate_family(
            list(supply_records),
            list(meaning_records),
            use_class=admission.use_class,
        )
    except Exception:
        return None
    return admission if admission == expected else None


def _s1_cell_success(
    gate: ModuleType,
    observed: _GateObservation,
    *,
    expects_backoff_record: bool,
) -> bool:
    records = [*observed.supply_records, *observed.meaning_records]
    if not expects_backoff_record:
        return (
            not observed.requests
            and not records
            and not observed.admissions
        )
    if len(observed.requests) != 1 or len(records) != 2 \
            or len(observed.admissions) != 1:
        return False
    request = observed.requests[0]
    if type(request) is not gate.DefineRequest \
            or request.macro != "BACKOFF_FIXED" \
            or request.requested_value != 10 \
            or len(observed.supply_records) != 1 \
            or len(observed.meaning_records) != 1:
        return False
    digest = _request_digest(gate, request)
    supply = observed.supply_records[0]
    meaning = observed.meaning_records[0]
    expected_shapes = (
        (supply, "supply-effectuation"),
        (meaning, "runtime-meaning"),
    )
    if not all(
        type(record) is gate.ConditionArmRecord
        and record.arm == arm
        and record.terminal_status == "green"
        and record.driver_id == request.driver_id
        and record.macro == request.macro
        and record.request_digest == digest
        for record, arm in expected_shapes
    ):
        return False
    admission = _validated_family_admission(
        gate,
        observed.supply_records,
        observed.meaning_records,
        observed.admissions,
    )
    return admission is not None and admission.admitted is True


def _summary_document(summary: object) -> dict[str, Any]:
    return {
        field_name: getattr(summary, field_name)
        for field_name in (
            "campaign_id", "committed", "aborted", "evaluated", "skipped",
        )
    }


def _sweep_accepts(
    gate: ModuleType,
    observed: _GateObservation,
    summary: object,
) -> bool:
    committed = getattr(summary, "committed", None)
    aborted = getattr(summary, "aborted", None)
    return (
        _gate_success(gate, observed)
        and type(committed) is int
        and committed == 2
        and type(aborted) is int
        and aborted == 0
    )


def _measure_call(
    gate: ModuleType,
    *,
    driver_id: str,
    call: Callable[[], object],
    stop_after_admission: bool = True,
) -> tuple[object | None, _GateObservation, bool, dict[str, Any] | None]:
    observer = _GateObserver(
        gate,
        driver_id=driver_id,
        stop_after_admission=stop_after_admission,
    )
    value: object | None = None
    completed = False
    exception = None
    try:
        with observer:
            value = call()
        completed = True
    except Exception as exc:
        exception = _exception_document(exc)
    return value, observer.observed, completed, exception


def _network_observation() -> dict[str, Any]:
    host, port = NETWORK_TARGET
    document: dict[str, Any] = {
        "host": host,
        "port": port,
        "reachable": False,
    }
    connection: socket.socket | None = None
    try:
        infos = socket.getaddrinfo(host, port, type=socket.SOCK_STREAM)
        if not infos:
            raise OSError("getaddrinfo returned no addresses")
        family, socktype, protocol, _canonical, address = infos[0]
        document["first_resolved_address"] = str(address[0])
        connection = socket.socket(family, socktype, protocol)
        connection.settimeout(3.0)
        connection.connect(address)
        document["reachable"] = True
        document["exception"] = None
    except Exception as exc:
        document["exception"] = _exception_document(exc)
    finally:
        if connection is not None:
            connection.close()
    return document


def _scratch_capacity(path: Path) -> dict[str, int]:
    usage = shutil.disk_usage(path)
    stats = os.statvfs(path)
    return {
        "total_bytes": usage.total,
        "used_bytes": usage.used,
        "free_bytes": usage.free,
        "free_inodes": stats.f_favail,
    }


def _cmake_identity() -> dict[str, Any]:
    document: dict[str, Any] = {}
    try:
        candidate = shutil.which("cmake")
        if candidate is None:
            raise FileNotFoundError("cmake is unavailable")
        path = Path(candidate).resolve(strict=True)
        completed = subprocess.run(
            [os.fspath(path), "--version"],
            check=False,
            capture_output=True,
            text=True,
            timeout=10.0,
        )
        document.update({
            "path": os.fspath(path),
            "sha256": _sha256_file(path),
            "returncode": completed.returncode,
            "stdout_first_line": (
                completed.stdout.splitlines()[0]
                if completed.stdout.splitlines() else ""
            ),
            "stderr": completed.stderr,
            "exception": None,
        })
    except Exception as exc:
        document["exception"] = _exception_document(exc)
    return document


def _production_hashes(bundle: _Production) -> dict[str, Any]:
    return {
        relative: {
            "path": os.fspath((bundle.root / relative).resolve(strict=True)),
            "sha256": _sha256_file((bundle.root / relative).resolve(strict=True)),
        }
        for relative in PRODUCTION_RELATIVE_PATHS
    }


def _compiler_metadata(bundle: _Production) -> tuple[dict[str, Any], str]:
    cc, cxx = bundle.buildcache.compilers_for_current_site()
    document: dict[str, Any] = {"cc": cc, "cxx": cxx}
    try:
        manifest = bundle.buildcache.observed_toolchain_manifest(cc, cxx)
        document["observed_toolchain_manifest"] = _json_safe(manifest)
        document["manifest_exception"] = None
    except Exception as exc:
        document["observed_toolchain_manifest"] = None
        document["manifest_exception"] = _exception_document(exc)
    return document, cxx


def _driver_metadata(
    bundle: _Production,
    *,
    common: Mapping[str, Any],
    output_root: Path,
) -> tuple[dict[str, Any], str]:
    compiler, cxx = _compiler_metadata(bundle)
    return ({
        **common,
        "driver_repo_root": os.fspath(bundle.root),
        "runtime_output_root": os.fspath(output_root),
        "compiler": compiler,
        "cmake": _cmake_identity(),
        "production_file_sha256": _production_hashes(bundle),
    }, cxx)


def _base_result(driver: str) -> dict[str, Any]:
    return {
        "schema_version": SCHEMA_VERSION,
        "driver": driver,
        "ok": False,
        "rc": 1,
        "exception": None,
    }


def _finish_result(result: dict[str, Any]) -> dict[str, Any]:
    result["rc"] = 0 if result["ok"] is True else 1
    return result


def _enumerate_s1_reachability(
    document: Mapping[str, Any],
    s1: ModuleType,
    gate: ModuleType,
) -> dict[str, Any]:
    roles: dict[str, Any] = {}
    for role in ("develop", "floor", "block1", "block2"):
        schedule = s1.schedule_for_role(document, role)
        roles[role] = {
            "schedule_length": len(schedule),
            "schedule": [
                {
                    "schedule_index": item.schedule_index,
                    "lap": item.lap,
                    "freeze_cell_id": item.freeze_cell_id,
                    "cell_id": item.cell_id,
                }
                for item in schedule
            ],
        }
    cells = document.get("cells")
    if not isinstance(cells, Mapping):
        raise TypeError("freeze cells must be a mapping")
    rows = []
    inert_request_count = 0
    for freeze_cell_id in sorted(cells):
        cell = cells[freeze_cell_id]
        if not isinstance(cell, Mapping):
            raise TypeError(f"freeze cell is not a mapping: {freeze_cell_id}")
        variant = cell.get("variant")
        flags = variant.get("flags") if isinstance(variant, Mapping) else None
        if not isinstance(flags, Mapping):
            raise TypeError(f"freeze cell flags are invalid: {freeze_cell_id}")
        condition_rows = []
        for macro in sorted(set(flags) & set(gate.DEFINE_SPECS)):
            if macro not in s1._CONDITION_DEFAULTS:
                raise RuntimeError(f"s1 condition default is missing: {macro}")
            value = flags[macro]
            default = s1._CONDITION_DEFAULTS[macro]
            if type(value) is int:
                requested_text = str(value)
            elif type(value) is str and value \
                    and not any(character.isspace() for character in value):
                requested_text = value
            else:
                raise TypeError(f"condition value is not an exact scalar: {macro}")
            default_text = str(default)
            inert = gate._is_inert_value(
                gate.DEFINE_SPECS[macro],
                requested=requested_text,
                default=default_text,
            )
            inert_request_count += int(inert)
            condition_rows.append({
                "macro": macro,
                "value": value,
                "default_value": default,
                "inert": inert,
            })
        rows.append({
            "freeze_cell_id": freeze_cell_id,
            "configuration": cell.get("configuration"),
            "workload": cell.get("workload"),
            "condition_macros": condition_rows,
        })
    return {
        "roles": roles,
        "cell_count": len(rows),
        "cells": rows,
        "inert_request_count": inert_request_count,
    }


def _s1_reachability_success(document: Mapping[str, Any]) -> bool:
    roles = document.get("roles")
    return (
        document.get("cell_count") == 18
        and type(document.get("inert_request_count")) is int
        and isinstance(roles, Mapping)
        and set(roles) == {"develop", "floor", "block1", "block2"}
        and all(isinstance(row, Mapping) for row in roles.values())
        and all(
            type(row.get("schedule_length")) is int
            and row["schedule_length"] >= 18
            for row in roles.values()
        )
    )


def _select_s1_cell(
    document: Mapping[str, Any], *, workload: str, configuration: str,
) -> tuple[str, Mapping[str, Any]]:
    cells = document.get("cells")
    if not isinstance(cells, Mapping):
        raise TypeError("freeze cells must be a mapping")
    matches = [
        (freeze_id, cell)
        for freeze_id, cell in cells.items()
        if isinstance(cell, Mapping)
        and cell.get("workload") == workload
        and cell.get("configuration") == configuration
    ]
    if len(matches) != 1:
        raise RuntimeError(
            f"freeze cell is not unique: {workload}:{configuration}: {len(matches)}"
        )
    return matches[0]


def _run_s1(
    bundle: _Production,
    *,
    common: Mapping[str, Any],
    output_root: Path,
) -> dict[str, Any]:
    result = _base_result("s1")
    try:
        metadata, cxx = _driver_metadata(
            bundle, common=common, output_root=output_root,
        )
        result["metadata"] = metadata
        document = bundle.s1.load_verified_freeze()
        reachability = _enumerate_s1_reachability(
            document, bundle.s1, bundle.gate,
        )
        result["reachability"] = reachability
        pin = document.get("ccbench_pin")
        if type(pin) is not str or not pin:
            raise RuntimeError("freeze ccbench_pin is unavailable")
        result["freeze_pin"] = pin
        cell_results: dict[str, Any] = {}
        specifications = (
            ("backoff_fixed_best", True),
            ("p2_2_flag_opt", False),
        )
        for configuration, expects_backoff in specifications:
            freeze_id, cell = _select_s1_cell(
                document,
                workload="write-heavy",
                configuration=configuration,
            )

            def prepare() -> None:
                with bundle.s1.prepare_cell(
                    cell,
                    pin,
                    cxx=cxx,
                    condition_use_class="certified-selection",
                ):
                    pass

            _value, observed, completed, exception = _measure_call(
                bundle.gate,
                driver_id=EXPECTED_DRIVER_IDS["s1"],
                call=prepare,
            )
            cell_results[configuration] = {
                "freeze_cell_id": freeze_id,
                "workload": cell.get("workload"),
                "configuration": cell.get("configuration"),
                "flags": _json_safe(cell.get("variant", {}).get("flags", {})),
                "completed": completed,
                "exception": exception,
                "observation": _observation_document(bundle.gate, observed),
                "meets_expected_gate_shape": (
                    completed
                    and _s1_cell_success(
                        bundle.gate,
                        observed,
                        expects_backoff_record=expects_backoff,
                    )
                ),
            }
        result["cells"] = cell_results
        if (
            _s1_reachability_success(reachability)
            and cell_results["backoff_fixed_best"]["meets_expected_gate_shape"]
            is True
            and cell_results["p2_2_flag_opt"]["meets_expected_gate_shape"]
            is True
        ):
            result["ok"] = True
    except Exception as exc:
        result["exception"] = _exception_document(exc)
    return _finish_result(result)


def _ccbench_head_and_clean(root: Path, expected: str) -> str:
    full = _run_git(root, "rev-parse", f"{expected}^{{commit}}")
    _run_git(root, "checkout", "--detach", full)
    actual = _run_git(root, "rev-parse", "HEAD")
    status = _run_git(root, "status", "--porcelain", "--untracked-files=all")
    if actual != full or status:
        raise RuntimeError(
            f"ccbench checkout is not pinned-clean: expected={full} status={status!r}"
        )
    return full


def _current_pin_control_success(
    observed: _GateObservation,
    *,
    completed: bool,
    exception: Mapping[str, Any] | None,
    current_head: str,
    required_head: str,
) -> bool:
    if completed or current_head == required_head or exception is None:
        return False
    if observed != _GateObservation():
        return False
    traceback_rows = exception.get("traceback")
    return (
        isinstance(traceback_rows, list)
        and any(
            isinstance(row, Mapping)
            and row.get("module") == "orchestrator.campaign.patchharness"
            and row.get("function") == "assert_pinned_clean"
            for row in traceback_rows
        )
    )


def _run_repro(
    bundle: _Production,
    *,
    common: Mapping[str, Any],
    output_root: Path,
) -> dict[str, Any]:
    result = _base_result("repro")
    try:
        metadata, cxx = _driver_metadata(
            bundle, common=common, output_root=output_root,
        )
        result["metadata"] = metadata
        ccbench = Path(bundle.buildcache._ccbench_dir()).resolve(strict=True)
        points = bundle.repro._genomes_reversed(10)
        current_full = _ccbench_head_and_clean(ccbench, CURRENT_CCBENCH_PIN)
        required_full = _run_git(
            ccbench, "rev-parse", f"{REPRO_CCBENCH_PIN}^{{commit}}",
        )

        def current_pin_call() -> None:
            with bundle.repro._conditioned_backoff_patch(points, cxx=cxx):
                pass

        _value, current_observed, current_completed, current_exception = \
            _measure_call(
                bundle.gate,
                driver_id=EXPECTED_DRIVER_IDS["repro"],
                call=current_pin_call,
            )
        current_control_ok = _current_pin_control_success(
            current_observed,
            completed=current_completed,
            exception=current_exception,
            current_head=current_full,
            required_head=required_full,
        )
        result["current_pin_pre_gate_control"] = {
            "ccbench_head": current_full,
            "required_ccbench_head": required_full,
            "completed": current_completed,
            "exception": current_exception,
            "observation": _observation_document(bundle.gate, current_observed),
            "failed_before_gate": current_control_ok,
            "pin_mismatch_before_gate": current_control_ok,
            "used_for_ok": True,
        }

        historical_full = _ccbench_head_and_clean(ccbench, REPRO_CCBENCH_PIN)

        def historical_call() -> None:
            with bundle.repro._conditioned_backoff_patch(points, cxx=cxx):
                pass

        _value, observed, completed, exception = _measure_call(
            bundle.gate,
            driver_id=EXPECTED_DRIVER_IDS["repro"],
            call=historical_call,
        )
        result["historical_pin_run"] = {
            "ccbench_head": historical_full,
            "completed": completed,
            "exception": exception,
            "observation": _observation_document(bundle.gate, observed),
        }
        final_head = _run_git(ccbench, "rev-parse", "HEAD")
        final_status = _run_git(
            ccbench, "status", "--porcelain", "--untracked-files=all",
        )
        result["historical_pin_run"]["final_ccbench_head"] = final_head
        result["historical_pin_run"]["final_ccbench_status"] = final_status
        if (
            completed
            and exception is None
            and current_control_ok
            and final_head == historical_full
            and not final_status
            and _gate_success(bundle.gate, observed)
        ):
            result["ok"] = True
    except Exception as exc:
        result["exception"] = _exception_document(exc)
    return _finish_result(result)


def _run_sweep(
    bundle: _Production,
    *,
    common: Mapping[str, Any],
    output_root: Path,
) -> dict[str, Any]:
    result = _base_result("sweep")
    try:
        metadata, _cxx = _driver_metadata(
            bundle, common=common, output_root=output_root,
        )
        result["metadata"] = metadata
        ccbench = Path(bundle.buildcache._ccbench_dir()).resolve(strict=True)
        result["ccbench_head"] = _ccbench_head_and_clean(
            ccbench, CURRENT_CCBENCH_PIN,
        )
        workload = dict(bundle.sweep.WORKLOADS[0][1])

        def run_workload() -> object:
            return bundle.sweep.run_workload(
                "write-heavy",
                workload,
                screening_enabled=True,
                screening_fixed_us=2,
            )

        summary, observed, completed, exception = _measure_call(
            bundle.gate,
            driver_id=EXPECTED_DRIVER_IDS["sweep"],
            call=run_workload,
            # The observer removes itself on the family-admission return, before
            # the screening campaign starts.
            stop_after_admission=True,
        )
        result["completed"] = completed
        result["exception"] = exception
        result["workload"] = workload
        result["observation"] = _observation_document(bundle.gate, observed)
        result["summary"] = (
            _summary_document(summary) if completed else None
        )
        if (
            completed
            and exception is None
            and _sweep_accepts(bundle.gate, observed, summary)
        ):
            result["ok"] = True
    except Exception as exc:
        result["exception"] = _exception_document(exc)
    return _finish_result(result)


@contextlib.contextmanager
def _driver_execution_context(
    bundle: _Production, output_root: Path,
):
    output_root.mkdir(mode=0o700)
    variable = bundle.layout._OFFICIAL_OUTPUT_ROOT_ENV
    previous = os.environ.get(variable)
    prior_cwd = Path.cwd()
    os.environ[variable] = os.fspath(output_root)
    os.chdir(bundle.root)
    try:
        yield
    finally:
        os.chdir(prior_cwd)
        if previous is None:
            os.environ.pop(variable, None)
        else:
            os.environ[variable] = previous


def _canonical_external_directory(
    value: Path,
    *,
    repo_roots: Sequence[Path],
    label: str,
) -> Path:
    if not value.is_absolute():
        raise ValueError(f"{label} must be absolute")
    canonical = value.resolve(strict=True)
    if canonical != value or not canonical.is_dir():
        raise ValueError(f"{label} must be an existing canonical directory")
    for root in repo_roots:
        try:
            canonical.relative_to(root)
        except ValueError:
            continue
        raise ValueError(f"{label} must be outside every driver repository")
    return canonical


def _argument_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--s1-repo", required=True, type=Path)
    parser.add_argument("--repro-repo", required=True, type=Path)
    parser.add_argument("--sweep-repo", required=True, type=Path)
    parser.add_argument("--expected-repo-head", required=True)
    parser.add_argument("--evidence-dir", required=True, type=Path)
    parser.add_argument("--scratch-output-root", required=True, type=Path)
    parser.add_argument("--pbs-job-id", required=True)
    return parser


def _make_run_binding(pbs_job_id: str) -> dict[str, Any]:
    if type(pbs_job_id) is not str or not pbs_job_id:
        raise ValueError("--pbs-job-id must be a non-empty string")
    return {
        "run_id": uuid.uuid4().hex,
        "pbs_job_id": pbs_job_id,
        "process_id": os.getpid(),
    }


def main(argv: Sequence[str] | None = None) -> int:
    args = _argument_parser().parse_args(argv)
    if not isinstance(args.expected_repo_head, str) \
            or len(args.expected_repo_head) != 40 \
            or any(character not in "0123456789abcdef"
                   for character in args.expected_repo_head):
        raise ValueError("--expected-repo-head must be a full lowercase commit")
    raw_roots = {
        "s1": args.s1_repo,
        "repro": args.repro_repo,
        "sweep": args.sweep_repo,
    }
    roots = {
        driver: _validate_repo_root(root, args.expected_repo_head)
        for driver, root in raw_roots.items()
    }
    if len(set(roots.values())) != 3:
        raise ValueError("each driver requires a distinct repository clone")
    evidence_dir = _canonical_external_directory(
        args.evidence_dir,
        repo_roots=tuple(roots.values()),
        label="evidence directory",
    )
    scratch_output_root = _canonical_external_directory(
        args.scratch_output_root,
        repo_roots=tuple(roots.values()),
        label="scratch output root",
    )
    run_binding = _make_run_binding(args.pbs_job_id)
    common = {
        "hostname": socket.gethostname(),
        "network_observation": _network_observation(),
        "scratch_capacity_at_start": _scratch_capacity(scratch_output_root),
        "expected_repo_head": args.expected_repo_head,
        "run_binding": run_binding,
    }
    runners = {
        "s1": _run_s1,
        "repro": _run_repro,
        "sweep": _run_sweep,
    }
    completed_drivers: list[str] = []
    overall_rc = 0
    for driver in DRIVER_ORDER:
        result = _base_result(driver)
        try:
            bundle = _load_production(roots[driver])
            output_root = scratch_output_root / driver
            with _driver_execution_context(bundle, output_root):
                result = runners[driver](
                    bundle, common=common, output_root=output_root,
                )
        except Exception as exc:
            result["exception"] = _exception_document(exc)
            result = _finish_result(result)
        completed_drivers.append(driver)
        result["planned_driver_order"] = list(DRIVER_ORDER)
        result["drivers_completed_before_publish"] = list(completed_drivers)
        result["run_binding"] = run_binding
        destination = evidence_dir / RESULT_NAMES[driver]
        try:
            _write_atomic_create_only(destination, result)
        except Exception as exc:
            print(
                json.dumps({
                    "driver": driver,
                    "published": False,
                    "path": os.fspath(destination),
                    "run_binding": run_binding,
                    "exception": _exception_document(exc),
                }, ensure_ascii=False, sort_keys=True),
                flush=True,
            )
            return 4
        else:
            print(
                json.dumps({
                    "driver": driver,
                    "ok": result["ok"],
                    "rc": result["rc"],
                    "published": True,
                    "path": os.fspath(destination),
                    "run_binding": run_binding,
                }, ensure_ascii=False, sort_keys=True),
                flush=True,
            )
        if result["ok"] is not True and overall_rc == 0:
            overall_rc = 1
    return overall_rc


if __name__ == "__main__":
    raise SystemExit(main())
