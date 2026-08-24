#!/usr/bin/env python3
"""Event-driven driver for the unmodified xdist LoadGroupScheduling class."""
from __future__ import annotations

import argparse
import hashlib
import heapq
import importlib.machinery
import json
import math
import os
import statistics
import sys
import zipfile
from collections import Counter, OrderedDict, deque
from dataclasses import dataclass
from pathlib import Path
from types import SimpleNamespace
from typing import Any, Mapping, Sequence

import xdist as _xdist_module
import xdist.dsession as _xdist_dsession_module
import xdist.scheduler.loadgroup as _xdist_loadgroup_module
import xdist.scheduler.loadscope as _xdist_loadscope_module
from xdist.scheduler.loadgroup import LoadGroupScheduling
from xdist.scheduler.loadscope import LoadScopeScheduling


MANIFEST_SCHEMA = "t1618-input-manifest/v2"
CALLERS = (
    "_reschedule.initial",
    "_reschedule.protocol_complete",
    "tests_finished",
    "has_pending",
    "remove_node",
)


class ReplayError(RuntimeError):
    """The replay diverged from an asserted scheduler invariant."""


def _canonical_json_bytes(value: Any) -> bytes:
    return (
        json.dumps(value, ensure_ascii=True, separators=(",", ":"), sort_keys=True)
        + "\n"
    ).encode("ascii")


def _json_digest(value: Any) -> str:
    return hashlib.sha256(_canonical_json_bytes(value)).hexdigest()


def _sha256_path(path: Path) -> str:
    digest = hashlib.sha256()
    try:
        with path.open("rb") as stream:
            while chunk := stream.read(1024 * 1024):
                digest.update(chunk)
    except OSError as exc:
        raise ReplayError(f"cannot hash live xdist source {path}: {exc}") from exc
    return digest.hexdigest()


def _xdist_provider_in_sys_path_entry(entry: Path) -> str | None:
    """Return the provider that could shadow xdist from one sys.path entry."""
    try:
        if entry.is_dir():
            package = entry / "xdist"
            if package.is_dir():
                return str(package.resolve())
            for suffix in importlib.machinery.all_suffixes():
                module = entry / f"xdist{suffix}"
                if module.is_file():
                    return str(module.resolve())
            return None
        if not entry.is_file() or not zipfile.is_zipfile(entry):
            return None
        with zipfile.ZipFile(entry) as archive:
            names = archive.namelist()
        module_names = {
            f"xdist{suffix}" for suffix in importlib.machinery.all_suffixes()
        }
        if any(name.startswith("xdist/") or name in module_names for name in names):
            return f"{entry}!/xdist"
        return None
    except (OSError, zipfile.BadZipFile) as exc:
        raise ReplayError(f"cannot inspect sys.path entry for xdist shadowing: {entry}: {exc}") from exc


def _verify_no_xdist_shadow(pinned_package: Path) -> dict[str, Any]:
    entries: list[tuple[int, str | None, Path | None]] = []
    anchor_index: int | None = None
    for index, raw_entry in enumerate(sys.path):
        if type(raw_entry) is not str:
            entries.append((index, None, None))
            continue
        entry = (Path.cwd() if raw_entry == "" else Path(raw_entry)).resolve()
        entries.append((index, raw_entry, entry))
        if (entry / "xdist").resolve() == pinned_package and anchor_index is None:
            anchor_index = index
    if anchor_index is None:
        raise ReplayError("pinned xdist package has no matching sys.path entry")
    for index, raw_entry, entry in entries[:anchor_index]:
        if raw_entry is None or entry is None:
            raise ReplayError(f"non-string sys.path entry precedes pinned xdist at index {index}")
        provider = _xdist_provider_in_sys_path_entry(entry)
        if provider is not None:
            raise ReplayError(
                f"xdist shadow provider precedes pinned package at sys.path[{index}]: {provider}"
            )
    anchor_entry = entries[anchor_index][2]
    if anchor_entry is None:
        raise ReplayError("pinned xdist sys.path anchor is not a filesystem path")
    return {
        "status": "passed",
        "pinned_package_path": str(pinned_package),
        "pinned_sys_path_entry": str(anchor_entry),
        "pinned_sys_path_index": anchor_index,
        "preceding_entries_checked": anchor_index,
    }


def verify_xdist_sources(manifest: Mapping[str, Any]) -> dict[str, Any]:
    expected = manifest.get("xdist")
    if (
        type(expected) is not dict
        or set(expected) != {"version", "source_root", "sources"}
        or expected.get("version") != "3.8.0"
    ):
        raise ReplayError("manifest xdist contract is missing or has the wrong version")
    modules = {
        "xdist": _xdist_module,
        "loadscope": _xdist_loadscope_module,
        "loadgroup": _xdist_loadgroup_module,
        "dsession": _xdist_dsession_module,
    }
    resolved: dict[str, Any] = {}
    sources = expected.get("sources")
    if type(sources) is not dict or set(sources) != set(modules):
        raise ReplayError("manifest xdist source set differs from the imported source set")
    for name, module in modules.items():
        raw_path = getattr(module, "__file__", None)
        if type(raw_path) is not str:
            raise ReplayError(f"imported xdist module has no file: {name}")
        path = Path(raw_path).resolve()
        expected_entry = sources[name]
        if (
            type(expected_entry) is not dict
            or set(expected_entry) != {"path", "sha256"}
            or type(expected_entry.get("path")) is not str
            or type(expected_entry.get("sha256")) is not str
        ):
            raise ReplayError(f"manifest xdist source entry is invalid: {name}")
        digest = _sha256_path(path)
        if path != Path(expected_entry["path"]).resolve():
            raise ReplayError(f"imported xdist path differs from manifest for {name}: {path}")
        if digest != expected_entry.get("sha256"):
            raise ReplayError(f"imported xdist SHA-256 differs from manifest for {name}")
        resolved[name] = {"path": str(path), "sha256": digest}
    pinned_package = Path(resolved["xdist"]["path"]).parent
    source_root = expected.get("source_root")
    if type(source_root) is not str or Path(source_root).resolve() != pinned_package:
        raise ReplayError("manifest xdist source root differs from the imported package")
    shadow_check = _verify_no_xdist_shadow(pinned_package)
    return {
        "status": "passed",
        "version": "3.8.0",
        "sources": resolved,
        "shadow_check": shadow_check,
    }


def _clone_strings(values: Sequence[str]) -> list[str]:
    clone = json.loads(json.dumps(list(values), ensure_ascii=False))
    if clone != list(values) or any(left is right for left, right in zip(values, clone)):
        raise ReplayError("worker collection decode did not create independent string objects")
    return clone


def _split_scope(nodeid: str) -> str:
    return nodeid.split("@")[-1] if nodeid.rfind("@") > nodeid.rfind("]") else nodeid


class IndexMapList(list[str]):
    """Value-equivalent collection whose index surface is an O(1) control."""

    def __init__(self, values: Sequence[str]) -> None:
        super().__init__(values)
        self._index_by_value = {value: index for index, value in enumerate(self)}
        if len(self._index_by_value) != len(self):
            raise ReplayError("O(1) index control requires a unique collection")

    def index(self, value: str, start: int = 0, stop: int | None = None) -> int:
        if start != 0 or stop is not None:
            return super().index(value, start, len(self) if stop is None else stop)
        try:
            return self._index_by_value[value]
        except KeyError as exc:
            raise ValueError(f"{value!r} is not in list") from exc


@dataclass(frozen=True)
class ReplayInput:
    population_id: str
    controller_id: str
    collection: tuple[str, ...]
    duration_by_nodeid: Mapping[str, float]
    group_by_nodeid: Mapping[str, str | None]
    worker_count: int
    expected_worker_occupancy: Mapping[str, Mapping[str, Any]] | None = None
    expected_group_to_workers: Mapping[str, Sequence[str]] | None = None


def load_replay_input(manifest_path: Path, controller_id: str) -> ReplayInput:
    try:
        manifest = json.loads(manifest_path.read_text(encoding="ascii"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise ReplayError(f"cannot read input manifest: {exc}") from exc
    if type(manifest) is not dict or manifest.get("schema_version") != MANIFEST_SCHEMA:
        raise ReplayError("unknown input manifest schema")
    matches = []
    for population in manifest.get("populations", []):
        for controller in population.get("controllers", []):
            if controller.get("id") == controller_id:
                matches.append((population, controller))
    if len(matches) != 1:
        raise ReplayError(f"controller id is not unique in manifest: {controller_id!r}")
    population, controller = matches[0]
    records = population.get("items")
    item_fields = population.get("item_fields")
    order_indices = controller.get("order_indices")
    if type(records) is not list or item_fields != [
        "scheduler_nodeid", "duration_s", "group", "outcome", "ledger_duration_s"
    ]:
        raise ReplayError("compact population item table has unknown shape")
    if order_indices is None:
        collection = [record[0] for record in records]
    elif type(order_indices) is list and all(type(index) is int for index in order_indices):
        try:
            collection = [records[index][0] for index in order_indices]
        except (IndexError, TypeError) as exc:
            raise ReplayError("controller compact order index is out of range") from exc
    else:
        raise ReplayError("controller compact order has unknown shape")
    if _json_digest(collection) != controller.get("ordered_collection_sha256"):
        raise ReplayError("ordered collection digest mismatch")
    duration_by_nodeid: dict[str, float] = {}
    group_by_nodeid: dict[str, str | None] = {}
    for record in records:
        if type(record) is not list or len(record) != 5:
            raise ReplayError("compact item record is not a five-field array")
        nodeid, duration, group, outcome, ledger_duration = record
        if (
            type(nodeid) is not str
            or type(duration) not in {int, float}
            or not math.isfinite(float(duration))
            or float(duration) < 0
            or (group is not None and type(group) is not str)
            or outcome not in {"passed", "skipped", "failure", "error"}
            or (
                ledger_duration is not None
                and (
                    type(ledger_duration) not in {int, float}
                    or not math.isfinite(float(ledger_duration))
                    or float(ledger_duration) < 0
                )
            )
        ):
            raise ReplayError("item record has invalid fields")
        if nodeid in duration_by_nodeid:
            raise ReplayError("item records contain duplicate scheduler nodeids")
        duration_by_nodeid[nodeid] = float(duration)
        group_by_nodeid[nodeid] = group
    if (
        len(collection) != controller.get("selected_n")
        or len(collection) != len(set(collection))
        or not set(collection) <= set(duration_by_nodeid)
    ):
        raise ReplayError("controller collection does not join item records")
    return ReplayInput(
        population_id=population["id"],
        controller_id=controller_id,
        collection=tuple(collection),
        duration_by_nodeid=duration_by_nodeid,
        group_by_nodeid=group_by_nodeid,
        worker_count=int(population["worker_count_per_controller"]),
        expected_worker_occupancy=controller.get("expected_worker_occupancy"),
        expected_group_to_workers=controller.get("expected_group_to_workers"),
    )


class _NoopLog:
    def __call__(self, *_args: Any, **_kwargs: Any) -> None:
        return None


class ReplayWorker:
    def __init__(
        self, worker_id: int, shutdown_sink: list[dict[str, Any]], diagnostics: bool
    ) -> None:
        self.worker_id = worker_id
        self.gateway = SimpleNamespace(id=f"gw{worker_id}")
        self.shutting_down = False
        self.queue: deque[int] = deque()
        self.sent_batches: list[tuple[int, ...]] = []
        self.shutdown_calls = 0
        self._shutdown_sink = shutdown_sink
        self._diagnostics = diagnostics
        self._event_seq = 0

    def set_event_seq(self, value: int) -> None:
        self._event_seq = value

    def send_runtest_some(self, indices: Sequence[int]) -> None:
        batch = tuple(indices)
        if not batch:
            raise ReplayError("scheduler sent an empty batch")
        self.sent_batches.append(batch)
        self.queue.extend(batch)

    def shutdown(self) -> None:
        self.shutdown_calls += 1
        self.shutting_down = True
        if self._diagnostics:
            self._shutdown_sink.append({
                "event_seq": self._event_seq,
                "worker": self.gateway.id,
                "call": self.shutdown_calls,
            })

    def __repr__(self) -> str:
        return f"ReplayWorker({self.gateway.id})"


class PendingProbe:
    def __init__(
        self,
        scheduler: LoadGroupScheduling,
        pending_by_workload: dict[int, int],
        policy: str,
        real_callers: frozenset[str],
        amplification_k: int,
        diagnostics: bool,
    ) -> None:
        self.scheduler = scheduler
        self.pending_by_workload = pending_by_workload
        self.policy = policy
        self.real_callers = real_callers
        self.amplification_k = amplification_k
        self.diagnostics = diagnostics
        self.context = "unclassified"
        self.event_seq = 0
        self.call_total = 0
        self.calls_by_caller: Counter[str] = Counter()
        self.scope_visits_by_caller: Counter[str] = Counter()
        self.item_visits_by_caller: Counter[str] = Counter()
        self.records: list[dict[str, Any]] = []

    def _real(self, workload: dict[str, dict[str, bool]]) -> int:
        value = 0
        for _ in range(self.amplification_k):
            value = LoadScopeScheduling._pending_of(self.scheduler, workload)
        return value

    def _oracle(self, workload: dict[str, dict[str, bool]]) -> int:
        key = id(workload)
        if key not in self.pending_by_workload:
            raise ReplayError("pending oracle saw an unknown workload")
        value = 0
        for _ in range(self.amplification_k):
            value = self.pending_by_workload[key]
        return value

    def __call__(self, workload: dict[str, dict[str, bool]]) -> int:
        caller = self.context
        if caller not in CALLERS:
            raise ReplayError(f"unclassified _pending_of caller: {caller!r}")
        self.call_total += 1
        if self.diagnostics:
            self.calls_by_caller[caller] += 1
        certify = self.policy in {"certify-real", "certify-oracle"}
        use_real = (
            self.policy in {"all-real", "certify-real"}
            or (self.policy == "mixed" and caller in self.real_callers)
        )
        if certify:
            real = self._real(workload)
            oracle = self._oracle(workload)
            if real != oracle:
                raise ReplayError(
                    f"pending oracle mismatch at event {self.event_seq}: real={real} oracle={oracle}"
                )
            value = real if self.policy == "certify-real" else oracle
        else:
            value = self._real(workload) if use_real else self._oracle(workload)
            real = value if use_real else None
            oracle = value if not use_real else None
        if self.diagnostics:
            scopes = len(workload)
            items = sum(len(unit) for unit in workload.values())
            self.scope_visits_by_caller[caller] += scopes
            self.item_visits_by_caller[caller] += items
            self.records.append({
                "type": "pending_of",
                "population_id": self.scheduler._t1618_population_id,
                "event_seq": self.event_seq,
                "caller": caller,
                "workload_scopes": scopes,
                "workload_items": items,
                "pending": value,
                "real": real,
                "oracle": oracle,
            })
        return value


class ReplayEngine:
    def __init__(
        self,
        replay_input: ReplayInput,
        *,
        scenario: str,
        index_mode: str,
        pending_policy: str,
        real_callers: Sequence[str] = (),
        identity_mode: str = "first-worker-alias",
        amplification_k: int = 1,
        diagnostics: bool = True,
    ) -> None:
        if scenario not in {"protocol-only", "pass-event"}:
            raise ReplayError(f"unknown event scenario: {scenario!r}")
        if index_mode not in {"real", "o1"}:
            raise ReplayError(f"unknown index mode: {index_mode!r}")
        if pending_policy not in {"all-real", "all-oracle", "certify-real", "certify-oracle", "mixed"}:
            raise ReplayError(f"unknown pending policy: {pending_policy!r}")
        if identity_mode not in {"first-worker-alias", "all-worker-clone"}:
            raise ReplayError(f"unknown identity mode: {identity_mode!r}")
        if amplification_k not in {1, 2, 4, 8}:
            raise ReplayError("amplification K must be one of 1, 2, 4, 8")
        unknown_callers = set(real_callers) - set(CALLERS)
        if unknown_callers:
            raise ReplayError(f"unknown real caller categories: {sorted(unknown_callers)!r}")
        self.input = replay_input
        self.scenario = scenario
        self.index_mode = index_mode
        self.pending_policy = pending_policy
        self.real_callers = frozenset(real_callers)
        self.identity_mode = identity_mode
        self.amplification_k = amplification_k
        self.diagnostics = diagnostics
        self.event_seq = 0
        self.virtual_time = 0.0
        self.heap_seq = 0
        self.events: list[dict[str, Any]] = []
        self.workqueue_transitions: list[dict[str, Any]] = []
        self.shutdown_calls: list[dict[str, Any]] = []
        self.assigned_scopes: dict[str, list[str]] = {}
        self.group_workers: dict[str, set[str]] = {}
        self.shutdown_triggered = False
        self.prepared = False
        self.timed_completed = False
        self.tests_finished_stats = {
            "property_evaluations": 0,
            "collection_early_returns": 0,
            "workqueue_early_returns": 0,
            "workers_scanned_by_event": [],
            "pending_short_circuits": 0,
            "full_worker_scans": 0,
        }
        self.pending_by_workload: dict[int, int] = {}
        self.scheduler = self._make_scheduler()
        self.scheduler._t1618_population_id = replay_input.population_id
        self.workers = [
            ReplayWorker(index, self.shutdown_calls, diagnostics)
            for index in range(replay_input.worker_count)
        ]
        base_collection = list(replay_input.collection)
        if identity_mode == "first-worker-alias":
            self.prepared_collections = [base_collection] + [
                _clone_strings(base_collection) for _ in self.workers[1:]
            ]
        else:
            self.prepared_collections = [
                _clone_strings(base_collection) for _ in self.workers
            ]
        self.probe = PendingProbe(
            self.scheduler,
            self.pending_by_workload,
            pending_policy,
            self.real_callers,
            amplification_k,
            diagnostics,
        )
        self.scheduler._pending_of = self.probe
        self._wrap_assign_work_unit()

    def _make_scheduler(self) -> LoadGroupScheduling:
        scheduler = LoadGroupScheduling.__new__(LoadGroupScheduling)
        scheduler.numnodes = self.input.worker_count
        scheduler.collection = None
        scheduler.workqueue = OrderedDict()
        scheduler.assigned_work = {}
        scheduler.registered_collections = {}
        scheduler.log = _NoopLog()
        scheduler.config = SimpleNamespace(option=SimpleNamespace(loadscopereorder=True))
        return scheduler

    def _set_worker_event_seq(self) -> None:
        for worker in self.workers:
            worker.set_event_seq(self.event_seq)

    def _wrap_assign_work_unit(self) -> None:
        original = LoadScopeScheduling._assign_work_unit
        cloned = False

        def assign(node: ReplayWorker) -> None:
            nonlocal cloned
            if not self.scheduler.workqueue:
                raise ReplayError("assignment wrapper entered with an empty workqueue")
            before = len(self.scheduler.workqueue)
            scope, unit = next(iter(self.scheduler.workqueue.items()))
            pending_added = len(unit)
            if self.identity_mode == "all-worker-clone" and not cloned:
                if self.scheduler.collection is None:
                    raise ReplayError("official collection is unavailable at first assignment")
                for worker in self.workers:
                    values = _clone_strings(self.scheduler.registered_collections[worker])
                    self.scheduler.registered_collections[worker] = (
                        IndexMapList(values) if self.index_mode == "o1" else values
                    )
                cloned = True
            original(self.scheduler, node)
            workload = self.scheduler.assigned_work[node]
            self.pending_by_workload[id(workload)] += pending_added
            if self.diagnostics:
                self.assigned_scopes[node.gateway.id].append(scope)
                groups = {
                    self.input.group_by_nodeid[nodeid]
                    for nodeid in unit
                    if self.input.group_by_nodeid[nodeid] is not None
                }
                if len(groups) > 1:
                    raise ReplayError("one loadgroup work unit contains multiple groups")
                for group in groups:
                    if group is None:
                        raise ReplayError("loadgroup diagnostic retained a null group")
                    self.group_workers.setdefault(group, set()).add(node.gateway.id)
                self.workqueue_transitions.append({
                    "event_seq": self.event_seq,
                    "worker": node.gateway.id,
                    "scope": scope,
                    "before_units": before,
                    "after_units": len(self.scheduler.workqueue),
                    "item_count": pending_added,
                })

        self.scheduler._assign_work_unit = assign

    def _begin_event(self, kind: str, worker: ReplayWorker | None) -> None:
        self.event_seq += 1
        self.probe.event_seq = self.event_seq
        self._set_worker_event_seq()
        self._current_event_kind = kind
        self._current_worker = None if worker is None else worker.gateway.id

    def _evaluate_tests_finished(self) -> bool:
        before_calls = self.probe.call_total
        self.probe.context = "tests_finished"
        collection_completed = self.scheduler.collection_is_completed if self.diagnostics else False
        had_workqueue = bool(self.scheduler.workqueue) if self.diagnostics else False
        result = self.scheduler.tests_finished
        scanned = self.probe.call_total - before_calls
        if self.diagnostics:
            stats = self.tests_finished_stats
            stats["property_evaluations"] += 1
            if not collection_completed:
                stats["collection_early_returns"] += 1
            elif had_workqueue:
                stats["workqueue_early_returns"] += 1
            else:
                stats["workers_scanned_by_event"].append(scanned)
                active = len(self.scheduler.assigned_work)
                if not result and scanned < active:
                    stats["pending_short_circuits"] += 1
                if scanned == active:
                    stats["full_worker_scans"] += 1
        if result and not self.shutdown_triggered:
            self.shutdown_triggered = True
            for worker in list(self.scheduler.nodes):
                worker.shutdown()
        if self.diagnostics:
            self.events.append({
                "type": "event",
                "population_id": self.input.population_id,
                "event_seq": self.event_seq,
                "event": self._current_event_kind,
                "worker": self._current_worker,
                "virtual_time_s": self.virtual_time,
                "tests_finished": result,
                "tests_finished_workers_scanned": scanned,
                "workqueue_units": len(self.scheduler.workqueue),
                "active_workers": len(self.scheduler.assigned_work),
            })
        return result

    def prepare(self) -> None:
        if self.prepared:
            raise ReplayError("replay preparation was requested twice")
        for worker in self.workers:
            self._begin_event("workerready", worker)
            self.scheduler.add_node(worker)
            self.pending_by_workload[id(self.scheduler.assigned_work[worker])] = 0
            self.assigned_scopes[worker.gateway.id] = []
            self._evaluate_tests_finished()
        for index, worker in enumerate(self.workers):
            self._begin_event("collectionfinish", worker)
            self.scheduler.add_node_collection(worker, self.prepared_collections[index])
            if index + 1 < len(self.workers):
                self._evaluate_tests_finished()
        if not self.scheduler.collection_is_completed:
            raise ReplayError("worker collection preparation did not complete")
        if self.index_mode == "o1":
            for worker in self.workers:
                self.scheduler.registered_collections[worker] = IndexMapList(
                    self.scheduler.registered_collections[worker]
                )
        self.prepared = True

    def _identity_matrix(self) -> dict[str, Any]:
        official = self.scheduler.collection
        if official is None:
            raise ReplayError("identity matrix requested before schedule")
        rows = []
        matrix_digest = hashlib.sha256()
        for worker in self.workers:
            worker_collection = self.scheduler.registered_collections[worker]
            bits = bytes(
                1 if official[index] is worker_collection[index] else 0
                for index in range(len(official))
            )
            matrix_digest.update(bits)
            rows.append({
                "worker": worker.gateway.id,
                "true_count": bits.count(1),
                "false_count": bits.count(0),
                "row_sha256": hashlib.sha256(bits).hexdigest(),
            })
        if self.identity_mode == "first-worker-alias":
            if rows[0]["true_count"] != len(official) or any(row["true_count"] for row in rows[1:]):
                raise ReplayError("first-worker identity alias matrix is not the real xdist shape")
        elif any(row["true_count"] for row in rows):
            raise ReplayError("all-worker-clone control retained an identity alias")
        return {
            "mode": self.identity_mode,
            "rows": rows,
            "matrix_sha256": matrix_digest.hexdigest(),
        }

    def _push_next(self, worker: ReplayWorker, heap: list[tuple[Any, ...]]) -> None:
        if not worker.queue:
            return
        index = worker.queue[0]
        nodeid = self.scheduler.registered_collections[worker][index]
        self.heap_seq += 1
        finish = self.virtual_time + self.input.duration_by_nodeid[nodeid]
        heapq.heappush(
            heap, (finish, 1, worker.worker_id, self.heap_seq, "protocol", worker, index)
        )

    def _push_workerfinished(self, worker: ReplayWorker, heap: list[tuple[Any, ...]]) -> None:
        self.heap_seq += 1
        tie_priority = 0 if self.scenario == "protocol-only" else 2
        heapq.heappush(
            heap,
            (
                self.virtual_time,
                tie_priority,
                worker.worker_id,
                self.heap_seq,
                "workerfinished",
                worker,
                None,
            ),
        )

    def _protocol_events(self) -> None:
        heap: list[tuple[Any, ...]] = []
        for worker in self.workers:
            self._push_next(worker, heap)
        completed: list[str] = []
        nonprotocol = (
            ("logstart", "testreport.setup", "testreport.call", "testreport.teardown", "logfinish")
            if self.scenario == "pass-event" else ()
        )
        while heap:
            (
                finish, _priority, _worker_id, _heap_seq, kind, worker, expected_index
            ) = heapq.heappop(heap)
            self.virtual_time = finish
            if kind == "workerfinished":
                if worker.queue:
                    raise ReplayError("workerfinished interleaved before the worker queue drained")
                self._begin_event("workerfinished", worker)
                self.probe.context = "remove_node"
                crashitem = self.scheduler.remove_node(worker)
                if crashitem is not None:
                    raise ReplayError(
                        f"normal worker finish produced a crash item: {crashitem!r}"
                    )
                self._evaluate_tests_finished()
                continue
            if kind != "protocol" or expected_index is None:
                raise ReplayError(f"unknown virtual event kind: {kind!r}")
            if not worker.queue or worker.queue[0] != expected_index:
                raise ReplayError("worker FIFO diverged from the virtual event heap")
            for kind in nonprotocol:
                self._begin_event(kind, worker)
                self._evaluate_tests_finished()
            self._begin_event("runtest_protocol_complete", worker)
            item_index = worker.queue.popleft()
            nodeid = self.scheduler.registered_collections[worker][item_index]
            workload = self.scheduler.assigned_work[worker]
            key = id(workload)
            self.pending_by_workload[key] -= 1
            if self.pending_by_workload[key] < 0:
                raise ReplayError("pending oracle became negative")
            self.probe.context = "_reschedule.protocol_complete"
            self.scheduler.mark_test_complete(worker, item_index, self.input.duration_by_nodeid[nodeid])
            completed.append(nodeid)
            self._evaluate_tests_finished()
            if worker.queue:
                self._push_next(worker, heap)
            elif worker.shutting_down:
                self._push_workerfinished(worker, heap)
            else:
                raise ReplayError("drained worker was neither rescheduled nor shutting down")
        if len(completed) != len(self.input.collection) or Counter(completed) != Counter(self.input.collection):
            raise ReplayError("protocol replay did not complete the exact collection")

        if self.scheduler.nodes:
            raise ReplayError("workers remain after the interleaved workerfinished sequence")

    def _finish_summary(self) -> tuple[dict[str, dict[str, Any]], dict[str, list[str]], dict[str, Any]]:
        occupancy = {
            worker.gateway.id: {
                "items": sum(len(batch) for batch in worker.sent_batches),
                "duration_s": round(sum(
                    self.input.duration_by_nodeid[self.scheduler.registered_collections[worker][index]]
                    for batch in worker.sent_batches for index in batch
                ), 9),
            }
            for worker in self.workers
        }
        group_to_workers = {
            group: sorted(workers) for group, workers in sorted(self.group_workers.items())
        }
        scope_counts = [len(self.assigned_scopes[worker.gateway.id]) for worker in self.workers]
        item_counts = [sum(len(batch) for batch in worker.sent_batches) for worker in self.workers]
        distribution = {
            "scopes": _distribution(scope_counts),
            "items": _distribution(item_counts),
        }
        return occupancy, group_to_workers, distribution

    def run_timed(self) -> None:
        if not self.prepared or self.timed_completed:
            raise ReplayError("timed replay requires exactly one completed preparation")
        before = self.probe.call_total
        self.probe.context = "has_pending"
        if self.scheduler.has_pending:
            raise ReplayError("has_pending was true before initial schedule")
        if self.probe.call_total - before != self.input.worker_count:
            raise ReplayError("terminal-present has_pending did not scan every empty workload")
        self.probe.context = "_reschedule.initial"
        self.scheduler.schedule()
        self._evaluate_tests_finished()
        if self.scheduler.collection is None:
            raise ReplayError("scheduler did not establish an official collection")
        self._protocol_events()
        self.timed_completed = True

    def finalize(self) -> dict[str, Any]:
        if not self.timed_completed:
            raise ReplayError("replay finalization requested before timed replay")
        identity = self._identity_matrix() if self.diagnostics else None
        if self.diagnostics:
            occupancy, group_to_workers, distribution = self._finish_summary()
        else:
            occupancy, group_to_workers, distribution = {}, {}, {
                "scopes": _distribution([]), "items": _distribution([])
            }
        sent = [
            {"worker": worker.gateway.id, "batch": list(batch)}
            for worker in self.workers for batch in worker.sent_batches
        ]
        sent_items = sum(len(entry["batch"]) for entry in sent)
        returned_indices = [index for entry in sent for index in entry["batch"]]
        expected_indices = list(range(len(self.input.collection)))
        if Counter(returned_indices) != Counter(expected_indices):
            raise ReplayError("sent indices do not cover the exact collection")
        slot_probes = sum(index + 1 for index in returned_indices)
        expected_slot_probes = len(expected_indices) * (len(expected_indices) + 1) // 2
        if slot_probes != expected_slot_probes:
            raise ReplayError("list index slot probe gate failed")
        result = {
            "population": {"id": self.input.population_id},
            "controller_id": self.input.controller_id,
            "scenario": self.scenario,
            "index_mode": self.index_mode,
            "pending_policy": self.pending_policy,
            "real_callers": sorted(self.real_callers),
            "identity_mode": self.identity_mode,
            "amplification_k": self.amplification_k,
            "event_count": self.event_seq,
            "virtual_makespan_s": self.virtual_time,
            "sent_item_count": sent_items,
            "retry_count": 0,
            "list_index_slot_probes": slot_probes,
            "expected_list_index_slot_probes": expected_slot_probes,
            "pending_calls": dict(sorted(self.probe.calls_by_caller.items())),
            "pending_scope_visits": dict(sorted(self.probe.scope_visits_by_caller.items())),
            "pending_item_visits": dict(sorted(self.probe.item_visits_by_caller.items())),
            "tests_finished": self.tests_finished_stats,
            "worker_occupancy": occupancy,
            "group_to_workers": group_to_workers,
            "worker_workload_distribution": distribution,
            "identity_matrix": identity,
            "shutdown_calls": self.shutdown_calls,
            "events": self.events,
            "pending_trace": self.probe.records,
            "workqueue_transitions": self.workqueue_transitions,
            "behavior_signature": {
                "sent_batches": sent,
                "workqueue_transitions": self.workqueue_transitions,
                "shutdown_calls": self.shutdown_calls,
                "event_sequence": [
                    (event["event_seq"], event["event"], event["worker"], event["tests_finished"])
                    for event in self.events
                ],
            },
        }
        return result

    def run(self) -> dict[str, Any]:
        self.prepare()
        self.run_timed()
        return self.finalize()


def _distribution(values: Sequence[int]) -> dict[str, float | int]:
    if not values:
        return {"min": 0, "median": 0.0, "max": 0}
    return {"min": min(values), "median": statistics.median(values), "max": max(values)}


def occupancy_gate(replay_input: ReplayInput, result: Mapping[str, Any]) -> dict[str, Any]:
    expected = replay_input.expected_worker_occupancy
    expected_groups = replay_input.expected_group_to_workers
    if expected is None and expected_groups is None:
        return {"status": "not-applicable", "adopt_path_b": True}
    if type(expected) is not dict or type(expected_groups) is not dict:
        raise ReplayError("only one K=2 observation oracle was present")
    observed = result["worker_occupancy"]
    expected_items = sorted(entry["items"] for entry in expected.values())
    observed_items = sorted(entry["items"] for entry in observed.values())
    expected_distribution = _distribution(expected_items)
    observed_distribution = _distribution(observed_items)
    vector_match = expected_items == observed_items
    expected_counter = Counter(expected_items)
    observed_counter = Counter(observed_items)
    missing = sorted((expected_counter - observed_counter).elements())
    unexpected = sorted((observed_counter - expected_counter).elements())
    group_match = result["group_to_workers"] == expected_groups
    return {
        "status": "passed" if vector_match and group_match else "failed",
        "adopt_path_b": vector_match and group_match,
        "sorted_item_count_vector_match": vector_match,
        "expected_sorted_item_count_vector": expected_items,
        "observed_sorted_item_count_vector": observed_items,
        "missing_item_counts": missing,
        "unexpected_item_counts": unexpected,
        "expected_item_distribution": expected_distribution,
        "observed_item_distribution": observed_distribution,
        "group_to_workers_match": group_match,
        "expected_group_to_workers": expected_groups,
        "observed_group_to_workers": result["group_to_workers"],
    }


def certify(replay_input: ReplayInput, scenario: str) -> dict[str, Any]:
    real = ReplayEngine(
        replay_input, scenario=scenario, index_mode="real",
        pending_policy="certify-real", diagnostics=True,
    ).run()
    oracle = ReplayEngine(
        replay_input, scenario=scenario, index_mode="real",
        pending_policy="certify-oracle", diagnostics=True,
    ).run()
    if real["behavior_signature"] != oracle["behavior_signature"]:
        raise ReplayError("real-only and oracle-only behavior transcripts differ")
    occupancy = occupancy_gate(replay_input, real)
    clone = ReplayEngine(
        replay_input, scenario=scenario, index_mode="o1",
        pending_policy="certify-oracle", identity_mode="all-worker-clone",
        diagnostics=True,
    ).run()
    if clone["behavior_signature"]["event_sequence"] != real["behavior_signature"]["event_sequence"]:
        raise ReplayError("all-worker clone control changed the event sequence")
    return {
        "status": "correctness-passed",
        "scenario": scenario,
        "all_pending_values_equal": True,
        "behavior_transcript_equal": True,
        "pending_call_count": sum(real["pending_calls"].values()),
        "occupancy_gate": occupancy,
        "all_worker_clone_control": "passed",
        "real": real,
    }


def _synthetic_input() -> ReplayInput:
    collection = []
    groups: dict[str, str | None] = {}
    durations: dict[str, float] = {}
    for index in range(200):
        base = f"orchestrator/tests/test_synthetic_{index // 20:02d}.py::test_{index:03d}"
        group = "synthetic-a" if index < 5 else "synthetic-b" if 5 <= index < 12 else None
        nodeid = f"{base}@{group}" if group is not None else base
        collection.append(nodeid)
        groups[nodeid] = group
        durations[nodeid] = 0.001 + ((index * 17) % 31) / 10000.0
    return ReplayInput(
        population_id="synthetic-worker4-item200",
        controller_id="synthetic-controller",
        collection=tuple(collection),
        duration_by_nodeid=durations,
        group_by_nodeid=groups,
        worker_count=4,
    )


def self_test() -> dict[str, Any]:
    replay_input = _synthetic_input()
    protocol = certify(replay_input, "protocol-only")
    pass_event = certify(replay_input, "pass-event")
    primary = protocol["real"]
    alias_rows = primary["identity_matrix"]["rows"]
    if alias_rows[0]["true_count"] != 200 or any(row["true_count"] for row in alias_rows[1:]):
        raise ReplayError("synthetic first-worker alias gate failed")
    workerfinished = [
        event["tests_finished_workers_scanned"]
        for event in primary["events"] if event["event"] == "workerfinished"
    ]
    if workerfinished != [1, 1, 1, 0]:
        raise ReplayError(f"synthetic workerfinished scan sequence differs: {workerfinished!r}")
    for worker_index in range(4):
        worker = f"gw{worker_index}"
        protocol_sequences = [
            event["event_seq"]
            for event in primary["events"]
            if event["worker"] == worker and event["event"] == "runtest_protocol_complete"
        ]
        finish_sequences = [
            event["event_seq"]
            for event in primary["events"]
            if event["worker"] == worker and event["event"] == "workerfinished"
        ]
        if len(finish_sequences) != 1 or not protocol_sequences or finish_sequences[0] <= max(protocol_sequences):
            raise ReplayError(f"workerfinished did not follow the final protocol event for {worker}")
    if primary["pending_calls"].get("remove_node") != 4:
        raise ReplayError("synthetic remove_node did not call _pending_of four times")
    clone = ReplayEngine(
        replay_input, scenario="protocol-only", index_mode="o1",
        pending_policy="all-oracle", identity_mode="all-worker-clone", diagnostics=True,
    ).run()
    if any(row["true_count"] for row in clone["identity_matrix"]["rows"]):
        raise ReplayError("synthetic clone identity control failed")
    if clone["behavior_signature"]["event_sequence"] != primary["behavior_signature"]["event_sequence"]:
        raise ReplayError("O(1) index control changed the synthetic event sequence")
    return {
        "schema_version": "t1618-replay-self-test/v1",
        "status": "passed",
        "worker_count": 4,
        "item_count": 200,
        "protocol_event_count": primary["event_count"],
        "pass_event_count": pass_event["real"]["event_count"],
        "workerfinished_tests_finished_scans": workerfinished,
        "list_index_slot_probes": primary["list_index_slot_probes"],
        "oracle_certification": "passed",
        "first_worker_identity_alias": "passed",
        "all_worker_clone_control": "passed",
    }


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--manifest", type=Path)
    parser.add_argument("--controller")
    parser.add_argument("--scenario", choices=("protocol-only", "pass-event"), default="protocol-only")
    args = parser.parse_args(argv)
    try:
        if args.self_test:
            value = self_test()
        else:
            if args.manifest is None or args.controller is None:
                parser.error("--manifest and --controller are required outside --self-test")
            value = certify(load_replay_input(args.manifest, args.controller), args.scenario)
        print(json.dumps(value, ensure_ascii=True, sort_keys=True))
    except ReplayError as exc:
        print(f"replay failed: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
