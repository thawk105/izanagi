"""受入全走の決定的 shard 分割、pytest plugin、併合 gate。

この module は shard 間 manifest や barrier を持たない。各 pytest process が
deselect 前の全 collection から同じ割付けを再導出し、親は事後に report を照合する。
"""
from __future__ import annotations

import hashlib
import json
import math
import multiprocessing
import os
import secrets
import signal
import subprocess
import sys
import time
import xml.etree.ElementTree as ET
from collections import Counter, defaultdict
from dataclasses import dataclass
from multiprocessing.connection import wait as wait_connections
from pathlib import Path
from typing import Any, Callable, Mapping, Optional, Sequence

try:
    import pytest
except ModuleNotFoundError as exc:
    if exc.name != "pytest":
        raise

    def _pytest_hookimpl(
        **_options: Any,
    ) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
        def decorate(function: Callable[..., Any]) -> Callable[..., Any]:
            return function

        return decorate


    class _PytestUsageError(RuntimeError):
        pass
else:
    _pytest_hookimpl = pytest.hookimpl
    _PytestUsageError = pytest.UsageError

from tools import dev_wave_land as _dev_wave_land


INFRA_RC = 16
SCHEMA = "izanagi-acceptance-shard-report/v1"
PLUGIN_SPEC_ENV = "IZANAGI_ACCEPTANCE_SHARD_PLUGIN_V1"
SCHEDULER_PREFIX = "IZANAGI_EFFECTIVE_SCHEDULER_V1 "
ARTIFACT_PREFIX = "IZANAGI_ACCEPTANCE_SHARD_ARTIFACTS_V1 "
_DISPATCH_OUTCOME_PREFIX = b"IZANAGI_DISPATCH_OUTCOME_V1 "
_DISPATCH_MARKER_PAYLOAD_MAX_BYTES = 4096
_DISPATCH_MARKER_LINE_MAX_BYTES = (
    len(_DISPATCH_OUTCOME_PREFIX) + _DISPATCH_MARKER_PAYLOAD_MAX_BYTES + 2
)
_SCHEDULER_ATTR = "_izanagi_effective_scheduler"
_SESSION_PREFIX = ".izanagi-acceptance-shards"
_REPORT_FIELDS = frozenset({
    "schema_version", "shard_count", "shard_index", "pytest_rc",
    "observed_universe", "selected", "finished", "effective_scheduler",
    "terminal_counts", "failures", "group_to_workers", "worker_occupancy",
    "junit_path", "worker_collection_digests", "session_timeline",
})
_TERMINAL_COUNT_KEYS = frozenset({
    "passed", "failed", "error", "skipped", "xfailed", "xpassed",
})
_GIT_ENV_ALLOWLIST = (
    "LANG", "LC_ALL", "LC_CTYPE", "PATH", "SYSTEMROOT", "TMPDIR", "TZ",
)

# Different runtime loadgroups stay separate, but every pair below touches a
# common mutable real-repo resource with at least one writer.  Shard processes
# may run on different hosts, so their local flock files cannot close this edge.
REAL_REPO_GROUP_CONFLICT_EDGES = frozenset({
    ("campaign-repository-scan", "real-repo"),
    ("campaign-repository-scan", "s8c-predicate-snapshot"),
    ("campaign-repository-scan", "s8c-preregistration-candidate"),
    ("real-repo", "s8c-predicate-snapshot"),
    ("real-repo", "s8c-preregistration-candidate"),
    ("s8c-predicate-snapshot", "s8c-preregistration-candidate"),
})
if any(left >= right for left, right in REAL_REPO_GROUP_CONFLICT_EDGES):
    raise RuntimeError("real-repo conflict edges must be canonical distinct pairs")


class ShardError(ValueError):
    """shard の入力または成果物が閉じた契約を満たさない。"""


class CompositeResult(int):
    """既存 dispatcher の int 契約に child-start 証拠を添える。"""

    def __new__(cls, value: int, *, child_started: bool):
        result = int.__new__(cls, value)
        result.child_started = child_started
        return result


@dataclass(frozen=True, order=True)
class ItemRecord:
    nodeid: str
    file: str
    group: Optional[str] = None


@dataclass(frozen=True)
class Assignment:
    selected: tuple[tuple[str, ...], ...]
    loads: tuple[int, ...]
    components: tuple[dict[str, Any], ...]


@dataclass(frozen=True)
class MergeResult:
    rc: int
    reason: str
    scheduler: Optional[str] = None
    universe: tuple[str, ...] = ()
    failures: tuple[str, ...] = ()
    terminal_counts: tuple[tuple[str, int], ...] = ()


@dataclass(frozen=True)
class InternalSpec:
    session_root: Path
    shard_count: int
    shard_index: int

    @property
    def shard_root(self) -> Path:
        return self.session_root / f"shard-{self.shard_index}"

    @property
    def report_path(self) -> Path:
        return self.shard_root / "report.json"

    @property
    def junit_path(self) -> Path:
        return self.shard_root / "junit.xml"


def _canonical_json_bytes(value: Any) -> bytes:
    return (
        json.dumps(
            value, ensure_ascii=True, separators=(",", ":"), sort_keys=True,
        )
        + "\n"
    ).encode("ascii")


def _digest(value: Any) -> str:
    return hashlib.sha256(_canonical_json_bytes(value)).hexdigest()


def _is_within(path: Path, parent: Path) -> bool:
    try:
        path.relative_to(parent)
    except ValueError:
        return False
    return True


def _closed_git_environment() -> dict[str, str]:
    env = {
        key: os.environ[key]
        for key in _GIT_ENV_ALLOWLIST
        if key in os.environ
    }
    env.update({
        "GIT_CONFIG_GLOBAL": os.devnull,
        "GIT_CONFIG_NOSYSTEM": "1",
        "GIT_NO_REPLACE_OBJECTS": "1",
        "GIT_OPTIONAL_LOCKS": "0",
    })
    return env


def _git_common_dir(repo: Path) -> Path:
    try:
        result = subprocess.run(
            [
                "/usr/bin/git", "rev-parse", "--path-format=absolute",
                "--git-common-dir",
            ],
            cwd=repo,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            text=True,
            timeout=10.0,
            check=False,
            env=_closed_git_environment(),
        )
    except (OSError, subprocess.TimeoutExpired):
        raise ShardError("git-common-dir") from None
    lines = result.stdout.splitlines()
    if result.returncode != 0 or len(lines) != 1 or not lines[0]:
        raise ShardError("git-common-dir")
    common_dir = Path(lines[0])
    if not common_dir.is_absolute():
        raise ShardError("git-common-dir-nonabsolute")
    common_dir = common_dir.resolve()
    if common_dir.name != ".git" or not common_dir.is_dir():
        raise ShardError("git-common-dir-shape")
    return common_dir


def _validate_shared_root(repo: Path, main_repo: Path, shared_root: Path) -> None:
    repo = repo.resolve()
    main_repo = main_repo.resolve()
    shared_root = shared_root.resolve()
    for relative_bytes in _dev_wave_land._CONTROL_CONTAINERS:
        if type(relative_bytes) is not bytes or not relative_bytes:
            raise ShardError("control-container-contract")
        relative = Path(os.fsdecode(relative_bytes))
        if relative.is_absolute() or not relative.parts or ".." in relative.parts:
            raise ShardError("control-container-contract")
        control_container = (main_repo / relative).resolve()
        if _is_within(shared_root, control_container):
            raise ShardError("artifact-root-in-control-container")
    if _is_within(shared_root, repo):
        raise ShardError("artifact-root-inside-repo")


def shared_root_for_repo(repo: Path) -> Path:
    repo = repo.resolve()
    main_repo = _git_common_dir(repo).parent
    shared_root = (main_repo.parent / _SESSION_PREFIX).resolve()
    _validate_shared_root(repo, main_repo, shared_root)
    return shared_root


def _write_bytes_create_only(path: Path, payload: bytes) -> None:
    """一時 file から hard-link し、宛先を atomic create-only で確定する。"""

    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.parent / f".{path.name}.{secrets.token_hex(8)}.tmp"
    fd = os.open(temporary, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    try:
        with os.fdopen(fd, "wb", closefd=True) as stream:
            stream.write(payload)
            stream.flush()
            os.fsync(stream.fileno())
        os.link(temporary, path)
        directory_fd = os.open(path.parent, os.O_RDONLY)
        try:
            os.fsync(directory_fd)
        finally:
            os.close(directory_fd)
    finally:
        try:
            temporary.unlink()
        except FileNotFoundError:
            pass


def _record_payload(record: ItemRecord) -> dict[str, Any]:
    return {"file": record.file, "group": record.group, "nodeid": record.nodeid}


def _records_payload(records: Sequence[ItemRecord]) -> list[dict[str, Any]]:
    return [_record_payload(record) for record in records]


def parse_records(value: Any) -> tuple[ItemRecord, ...]:
    if type(value) is not list:
        raise ShardError("observed-universe-shape")
    records: list[ItemRecord] = []
    for entry in value:
        if type(entry) is not dict or set(entry) != {"nodeid", "file", "group"}:
            raise ShardError("observed-item-shape")
        nodeid = entry["nodeid"]
        filename = entry["file"]
        group = entry["group"]
        if (
            type(nodeid) is not str
            or not nodeid
            or type(filename) is not str
            or not filename
            or (group is not None and (type(group) is not str or not group))
        ):
            raise ShardError("observed-item-value")
        path = Path(filename)
        if path.is_absolute() or ".." in path.parts or not filename.endswith(".py"):
            raise ShardError("observed-file-noncanonical")
        if not nodeid.startswith(filename + "::"):
            raise ShardError("observed-nodeid-file-mismatch")
        records.append(ItemRecord(nodeid, filename, group))
    records.sort()
    nodeids = [record.nodeid for record in records]
    if len(nodeids) != len(set(nodeids)):
        raise ShardError("observed-nodeid-duplicate")
    return tuple(records)


class _UnionFind:
    def __init__(self, values: Sequence[str]):
        self.parent = {value: value for value in values}

    def find(self, value: str) -> str:
        parent = self.parent[value]
        while parent != self.parent[parent]:
            parent = self.parent[parent]
        while value != parent:
            next_value = self.parent[value]
            self.parent[value] = parent
            value = next_value
        return parent

    def union(self, left: str, right: str) -> None:
        lroot = self.find(left)
        rroot = self.find(right)
        if lroot == rroot:
            return
        low, high = sorted((lroot, rroot))
        self.parent[high] = low


def _components(records: Sequence[ItemRecord]) -> tuple[dict[str, Any], ...]:
    files = sorted({record.file for record in records})
    groups = sorted({record.group for record in records if record.group is not None})
    vertices = [f"f:{value}" for value in files] + [f"g:{value}" for value in groups]
    union = _UnionFind(vertices)
    for record in records:
        if record.group is not None:
            union.union(f"f:{record.file}", f"g:{record.group}")
    active_groups = set(groups)
    for left, right in sorted(REAL_REPO_GROUP_CONFLICT_EDGES):
        if left in active_groups and right in active_groups:
            union.union(f"g:{left}", f"g:{right}")
    buckets: dict[str, dict[str, set[str]]] = {}
    for record in records:
        root = union.find(f"f:{record.file}")
        bucket = buckets.setdefault(
            root, {"files": set(), "groups": set(), "nodeids": set()},
        )
        bucket["files"].add(record.file)
        if record.group is not None:
            bucket["groups"].add(record.group)
        bucket["nodeids"].add(record.nodeid)
    components = []
    for bucket in buckets.values():
        nodeids = tuple(sorted(bucket["nodeids"]))
        components.append({
            "files": tuple(sorted(bucket["files"])),
            "groups": tuple(sorted(bucket["groups"])),
            "nodeids": nodeids,
            "weight": len(nodeids),
        })
    return tuple(sorted(
        components,
        key=lambda item: (
            -item["weight"], item["files"], item["groups"], item["nodeids"],
        ),
    ))


def _groups_form_declared_conflict_component(groups: Sequence[str]) -> bool:
    pending = set(groups)
    if len(pending) < 2:
        return True
    reached = {min(pending)}
    while True:
        expanded = reached | {
            right if left in reached else left
            for left, right in REAL_REPO_GROUP_CONFLICT_EDGES
            if left in pending and right in pending
            and (left in reached or right in reached)
        }
        if expanded == reached:
            return reached == pending
        reached = expanded


def allocate(records: Sequence[ItemRecord], shard_count: int) -> Assignment:
    """file/group 連結成分を group 優先、残り LPT で決定的に割り付ける。"""

    if shard_count not in {2, 3}:
        raise ShardError("shard-count")
    records = tuple(sorted(records))
    if not records:
        raise ShardError("empty-universe")
    components = _components(records)
    if len(components) < shard_count:
        raise ShardError("empty-shard")
    grouped = [component for component in components if component["groups"]]
    remaining = [component for component in components if not component["groups"]]
    group_names = sorted({group for component in grouped for group in component["groups"]})
    bins: list[list[dict[str, Any]]] = [[] for _ in range(shard_count)]
    loads = [0] * shard_count

    if shard_count >= len(group_names):
        if any(
            not _groups_form_declared_conflict_component(component["groups"])
            for component in grouped
        ):
            raise ShardError("connected-exclusive-groups")
        grouped.sort(key=lambda item: item["groups"])
        for shard_index, component in enumerate(grouped):
            bins[shard_index].append(component)
            loads[shard_index] += component["weight"]
    else:
        grouped.sort(key=lambda item: (
            -item["weight"], item["files"], item["groups"], item["nodeids"],
        ))
        for component in grouped:
            shard_index = min(
                range(shard_count), key=lambda index: (loads[index], index),
            )
            bins[shard_index].append(component)
            loads[shard_index] += component["weight"]

    remaining.sort(key=lambda item: (
        -item["weight"], item["files"], item["groups"], item["nodeids"],
    ))
    for component in remaining:
        shard_index = min(range(shard_count), key=lambda index: (loads[index], index))
        bins[shard_index].append(component)
        loads[shard_index] += component["weight"]

    if any(not components_for_shard for components_for_shard in bins):
        raise ShardError("empty-shard")
    selected = tuple(
        tuple(sorted(
            nodeid
            for component in components_for_shard
            for nodeid in component["nodeids"]
        ))
        for components_for_shard in bins
    )
    component_report = []
    for shard_index, components_for_shard in enumerate(bins):
        for component in components_for_shard:
            component_report.append({
                "files": list(component["files"]),
                "groups": list(component["groups"]),
                "shard": shard_index,
                "weight": component["weight"],
            })
    return Assignment(selected, tuple(loads), tuple(component_report))


def assignment_closure_gate(
    records: Sequence[ItemRecord], selections: Sequence[Sequence[str]],
) -> bool:
    """allocator と独立に file/group の shard 閉包だけを再検査する。"""

    node_to_shard: dict[str, int] = {}
    for shard_index, nodeids in enumerate(selections):
        for nodeid in nodeids:
            if nodeid in node_to_shard:
                return False
            node_to_shard[nodeid] = shard_index
    if set(node_to_shard) != {record.nodeid for record in records}:
        return False
    file_shards: dict[str, set[int]] = defaultdict(set)
    group_shards: dict[str, set[int]] = defaultdict(set)
    for record in records:
        shard = node_to_shard[record.nodeid]
        file_shards[record.file].add(shard)
        if record.group is not None:
            group_shards[record.group].add(shard)
    if not all(len(shards) == 1 for shards in file_shards.values()):
        return False
    if not all(len(shards) == 1 for shards in group_shards.values()):
        return False
    active_groups = set(group_shards)
    return all(
        group_shards[left] == group_shards[right]
        for left, right in REAL_REPO_GROUP_CONFLICT_EDGES
        if left in active_groups and right in active_groups
    )


def _report_index_gate(reports: Sequence[Mapping[str, Any]], expected_k: int) -> bool:
    indexes = [report.get("shard_index") for report in reports]
    return (
        len(reports) == expected_k
        and all(type(index) is int for index in indexes)
        and len(indexes) == len(set(indexes))
        and set(indexes) == set(range(expected_k))
    )


def _observed_universes_gate(
    universes: Sequence[Sequence[ItemRecord]],
) -> bool:
    return bool(universes) and all(
        tuple(universe) == tuple(universes[0]) for universe in universes[1:]
    )


def _login_universe_gate(login: Sequence[str], universe: Sequence[str]) -> bool:
    return Counter(login) == Counter(universe)


def _finished_gate(selected: Sequence[str], finished: Sequence[str]) -> bool:
    return Counter(selected) == Counter(finished)


def _scheduler_gate(schedulers: Sequence[Any]) -> Optional[str]:
    values = set(schedulers)
    if values == {"loadgroup"}:
        return "loadgroup"
    if values == {"serial"}:
        return "serial"
    return None


def _string_list(value: Any, reason: str) -> tuple[str, ...]:
    if type(value) is not list or not all(type(item) is str and item for item in value):
        raise ShardError(reason)
    return tuple(value)


def validate_report_evidence(
    report: Mapping[str, Any],
    records: Sequence[ItemRecord],
    selected: Sequence[str],
    expected_junit_path: Path,
) -> None:
    """診断 payload を producer から独立に再計算して検証する。"""

    if not records or not selected:
        raise ShardError("report-evidence-empty-collection")
    record_by_node = {record.nodeid: record for record in records}
    selected_is_within_universe = all(
        nodeid in record_by_node for nodeid in selected
    )

    expected_digest = _digest(_records_payload(records))
    digests = report["worker_collection_digests"]
    if (
        type(digests) is not list
        or not digests
        or any(type(value) is not str or value != expected_digest for value in digests)
    ):
        raise ShardError("report-evidence-worker-digests")

    occupancy = report["worker_occupancy"]
    if type(occupancy) is not dict or not occupancy:
        raise ShardError("report-evidence-worker-occupancy")
    item_total = 0
    workers: set[str] = set()
    for worker, entry in occupancy.items():
        if type(worker) is not str or not worker or worker in workers:
            raise ShardError("report-evidence-worker-name")
        workers.add(worker)
        if type(entry) is not dict or set(entry) != {"items", "duration_s"}:
            raise ShardError("report-evidence-worker-entry")
        items = entry["items"]
        duration = entry["duration_s"]
        if type(items) is not int or items <= 0:
            raise ShardError("report-evidence-worker-items")
        if (
            type(duration) not in {int, float}
            or not math.isfinite(float(duration))
            or float(duration) < 0
        ):
            raise ShardError("report-evidence-worker-duration")
        item_total += items
    if item_total != len(selected):
        raise ShardError("report-evidence-worker-item-total")

    group_to_workers = report["group_to_workers"]
    if type(group_to_workers) is not dict:
        raise ShardError("report-evidence-group-set")
    if selected_is_within_universe:
        expected_groups = {
            record_by_node[nodeid].group
            for nodeid in selected
            if record_by_node[nodeid].group is not None
        }
        if set(group_to_workers) != expected_groups:
            raise ShardError("report-evidence-group-set")
    for group_workers in group_to_workers.values():
        if (
            type(group_workers) is not list
            or not group_workers
            or any(type(worker) is not str or not worker for worker in group_workers)
            or len(group_workers) != len(set(group_workers))
            or not set(group_workers) <= workers
        ):
            raise ShardError("report-evidence-group-workers")

    if report["junit_path"] != str(expected_junit_path):
        raise ShardError("report-evidence-junit-path")
    terminal_counts = report["terminal_counts"]
    if (
        type(terminal_counts) is not dict
        or set(terminal_counts) != _TERMINAL_COUNT_KEYS
        or any(
            type(value) is not int or value < 0
            for value in terminal_counts.values()
        )
        or sum(terminal_counts.values()) != len(selected)
    ):
        raise ShardError("report-evidence-terminal-counts")


def merge_reports(
    *, expected_k: int, reports: Sequence[Mapping[str, Any]],
    process_results: Mapping[int, int], login_universe: Sequence[str],
    expected_junit_paths: Sequence[Path],
) -> MergeResult:
    """裁定の 6 段 gate を記載順に評価する。"""

    # 診断 evidence は 6 gate より前に producer と独立に検証する。
    try:
        if len(expected_junit_paths) != expected_k:
            raise ShardError("expected-junit-paths")
        parsed: list[tuple[
            Mapping[str, Any], tuple[ItemRecord, ...],
            tuple[str, ...], tuple[str, ...],
        ]] = []
        for report in reports:
            if set(report) != _REPORT_FIELDS or report["schema_version"] != SCHEMA:
                raise ShardError("report-schema")
            index = report["shard_index"]
            if type(index) is not int or index not in range(expected_k):
                raise ShardError("report-shard-index")
            if report["shard_count"] != expected_k:
                raise ShardError("report-shard-count")
            if type(report["pytest_rc"]) is not int:
                raise ShardError("report-rc")
            records = parse_records(report["observed_universe"])
            shard_selected = _string_list(report["selected"], "selected-shape")
            shard_finished = _string_list(report["finished"], "finished-shape")
            validate_report_evidence(
                report, records, shard_selected, expected_junit_paths[index],
            )
            parsed.append((report, records, shard_selected, shard_finished))
    except (KeyError, ShardError, TypeError, ValueError):
        return MergeResult(INFRA_RC, "report-invalid")

    # 1. report index 集合。
    if not _report_index_gate(reports, expected_k):
        return MergeResult(INFRA_RC, "report-index-set")
    if set(process_results) != set(range(expected_k)):
        return MergeResult(INFRA_RC, "process-index-set")
    ordered_parsed = sorted(parsed, key=lambda entry: entry[0]["shard_index"])
    ordered = [entry[0] for entry in ordered_parsed]
    try:
        for report in ordered:
            if process_results[report["shard_index"]] != report["pytest_rc"]:
                raise ShardError("report-process-rc")
    except (KeyError, ShardError):
        return MergeResult(INFRA_RC, "report-invalid")
    universes = [entry[1] for entry in ordered_parsed]
    selected = [entry[2] for entry in ordered_parsed]
    finished = [entry[3] for entry in ordered_parsed]

    # 2. 全 shard が deselect 前に観測した U の一致。
    if not _observed_universes_gate(universes):
        return MergeResult(INFRA_RC, "observed-universe-mismatch")
    records = universes[0]
    universe = tuple(record.nodeid for record in records)

    # 3. login 親の独立 collect-only 集合との一致。
    if not _login_universe_gate(login_universe, universe):
        return MergeResult(INFRA_RC, "login-universe-mismatch")

    # 4. selected の exact partition と file/group 閉包。
    selected_sum = Counter(nodeid for shard in selected for nodeid in shard)
    if selected_sum != Counter(universe) or any(count != 1 for count in selected_sum.values()):
        return MergeResult(INFRA_RC, "selected-partition")
    if not assignment_closure_gate(records, selected):
        return MergeResult(INFRA_RC, "assignment-closure")

    # 5. 各 shard の logfinish 実測と selected の一致。
    if any(
        not _finished_gate(shard_selected, shard_finished)
        for shard_selected, shard_finished in zip(selected, finished)
    ):
        return MergeResult(INFRA_RC, "finished-selected-mismatch")

    # 6. scheduler は既存 land 受理集合の一値で全 shard 一致。
    scheduler = _scheduler_gate([report["effective_scheduler"] for report in ordered])
    if scheduler is None:
        return MergeResult(INFRA_RC, "scheduler")

    rcs = [process_results[index] for index in range(expected_k)]
    if any(type(rc) is not int or rc < 0 or rc >= 2 for rc in rcs):
        return MergeResult(INFRA_RC, "shard-rc")
    rc = 1 if 1 in rcs else 0
    try:
        failures = tuple(sorted({
            failure
            for report in ordered
            for failure in _string_list(report["failures"], "failure-shape")
        }))
    except ShardError:
        return MergeResult(INFRA_RC, "failure-shape")
    counts: Counter[str] = Counter()
    for report in ordered:
        counts.update(report["terminal_counts"])
    return MergeResult(
        rc, "ok", scheduler, universe, failures, tuple(sorted(counts.items())),
    )


def merge_junit(
    paths: Sequence[Path], destination: Path, *, expected_tests: int,
) -> None:
    root = ET.Element("testsuites")
    totals = Counter({"tests": 0, "failures": 0, "errors": 0, "skipped": 0})
    total_time = 0.0
    for path in paths:
        raw = path.read_bytes()
        if b"<!DOCTYPE" in raw.upper() or b"<!ENTITY" in raw.upper():
            raise ShardError("junit-dtd")
        parsed = ET.fromstring(raw)
        suites = [parsed] if parsed.tag == "testsuite" else list(parsed)
        if parsed.tag not in {"testsuite", "testsuites"} or any(
            suite.tag != "testsuite" for suite in suites
        ):
            raise ShardError("junit-root")
        for suite in suites:
            for key in totals:
                value = suite.get(key, "0")
                if not value.isdigit():
                    raise ShardError("junit-count")
                totals[key] += int(value)
            try:
                duration = float(suite.get("time", "0"))
            except ValueError as exc:
                raise ShardError("junit-time") from exc
            if not math.isfinite(duration) or duration < 0:
                raise ShardError("junit-time")
            total_time += duration
            root.append(suite)
    if totals["tests"] != expected_tests:
        raise ShardError("junit-tests")
    for key, value in totals.items():
        root.set(key, str(value))
    root.set("time", f"{total_time:.9f}".rstrip("0").rstrip("."))
    _write_bytes_create_only(destination, ET.tostring(root, encoding="utf-8", xml_declaration=True))


def _canonical_item(item: Any, repo: Path) -> ItemRecord:
    item_path = Path(item.path).resolve()
    if not _is_within(item_path, repo):
        raise ShardError("collected-file-outside-repo")
    relative = item_path.relative_to(repo).as_posix()
    _path, separator, suffix = item.nodeid.partition("::")
    if not separator or not suffix:
        raise ShardError("collected-nodeid")
    marks = list(item.iter_markers(name="xdist_group"))
    if len(marks) > 1:
        raise ShardError("multiple-xdist-group")
    group: Optional[str] = None
    if marks:
        mark = marks[0]
        if (
            len(mark.args) != 1
            or type(mark.args[0]) is not str
            or not mark.args[0]
            or mark.kwargs
        ):
            raise ShardError("xdist-group-shape")
        group = mark.args[0]
    nodeid = f"{relative}::{suffix}"
    if group is not None and nodeid.endswith(f"@{group}"):
        # loadgroup が付けた suffix は、同じ item の実 marker と一致する一段だけを除く。
        nodeid = nodeid[: -(len(group) + 1)]
    return ItemRecord(nodeid, relative, group)


def records_from_items(items: Sequence[Any], repo: Path) -> tuple[ItemRecord, ...]:
    records = tuple(sorted(_canonical_item(item, repo) for item in items))
    if len({record.nodeid for record in records}) != len(records):
        raise ShardError("collected-nodeid-duplicate")
    return records


def _plugin_spec() -> Optional[InternalSpec]:
    raw = os.environ.get(PLUGIN_SPEC_ENV)
    if not raw:
        return None
    try:
        payload = json.loads(raw)
        if type(payload) is not dict or set(payload) != {
            "session_root", "shard_count", "shard_index",
        }:
            raise ShardError("plugin-spec-shape")
        return InternalSpec(
            Path(payload["session_root"]).resolve(),
            payload["shard_count"], payload["shard_index"],
        )
    except (OSError, TypeError, ValueError, json.JSONDecodeError) as exc:
        raise _PytestUsageError(
            f"invalid acceptance shard plugin spec: {exc}"
        ) from exc


_PLUGIN_CONFIG: Any = None
_FINISHED_RAW: list[str] = []
_REPORT_WORKERS: dict[str, str] = {}
_REPORT_DURATIONS: Counter[str] = Counter()
_FAILURES: set[str] = set()
_WORKER_PAYLOADS: dict[str, Mapping[str, Any]] = {}
_WORKER_TEST_BOUNDS: dict[str, dict[str, float]] = {}


def _observed_epoch(value: Any) -> Optional[float]:
    if type(value) not in {int, float}:
        return None
    try:
        observed = float(value)
    except (OverflowError, TypeError, ValueError):
        return None
    if not math.isfinite(observed) or observed <= 0:
        return None
    return observed


def _observed_lock_intervals(value: Any) -> list[dict[str, float]]:
    if type(value) is not list:
        return []
    observed = []
    for interval in value:
        if type(interval) is not dict:
            continue
        acquired = _observed_epoch(interval.get("acquired_epoch_s"))
        released = _observed_epoch(interval.get("released_epoch_s"))
        if acquired is None or released is None:
            continue
        observed.append({
            "acquired_epoch_s": acquired,
            "released_epoch_s": released,
        })
    return observed


def record_real_repo_lock_interval(
    config: Any, acquired: float, released: float,
) -> None:
    if getattr(config, "_izanagi_acceptance_shard_spec", None) is None:
        return
    state = getattr(config, "_izanagi_acceptance_shard_state", None)
    if type(state) is not dict:
        return
    intervals = state.get("real_repo_lock_intervals")
    if type(intervals) is not list:
        return
    intervals.append({
        "acquired_epoch_s": acquired,
        "released_epoch_s": released,
    })


def pytest_configure(config: Any) -> None:
    global _PLUGIN_CONFIG
    global _FINISHED_RAW
    global _REPORT_WORKERS
    global _REPORT_DURATIONS
    global _FAILURES
    global _WORKER_PAYLOADS
    global _WORKER_TEST_BOUNDS
    spec = _plugin_spec()
    if spec is None:
        return
    _PLUGIN_CONFIG = config
    _FINISHED_RAW = []
    _REPORT_WORKERS = {}
    _REPORT_DURATIONS = Counter()
    _FAILURES = set()
    _WORKER_PAYLOADS = {}
    _WORKER_TEST_BOUNDS = {}
    setattr(config, "_izanagi_acceptance_shard_spec", spec)


@_pytest_hookimpl(trylast=True)
def pytest_collection_modifyitems(config: Any, items: list[Any]) -> None:
    spec = getattr(config, "_izanagi_acceptance_shard_spec", None)
    if spec is None:
        return
    # 実 repo は plugin spec に埋め込まず、cwd を唯一の実行 root とする。
    repo = Path.cwd().resolve()
    records = records_from_items(items, repo)
    assignment = allocate(records, spec.shard_count)
    selected = set(assignment.selected[spec.shard_index])
    deselected = []
    retained = []
    by_identity = {id(item): _canonical_item(item, repo).nodeid for item in items}
    for item in items:
        if by_identity[id(item)] in selected:
            retained.append(item)
        else:
            deselected.append(item)
    items[:] = retained
    if deselected:
        config.hook.pytest_deselected(items=deselected)
    setattr(config, "_izanagi_acceptance_shard_state", {
        "records": _records_payload(records),
        "records_digest": _digest(_records_payload(records)),
        "selected": sorted(selected),
        "selected_digest": _digest(sorted(selected)),
        "loads": list(assignment.loads),
    })


@_pytest_hookimpl(trylast=True)
def pytest_collection_finish(session: Any) -> None:
    config = getattr(session, "config", None)
    if getattr(config, "_izanagi_acceptance_shard_spec", None) is None:
        return
    state = getattr(config, "_izanagi_acceptance_shard_state", None)
    if type(state) is not dict:
        return
    if type(state.get("real_repo_lock_intervals")) is not list:
        state["real_repo_lock_intervals"] = []
    try:
        observed = _observed_epoch(time.time())
    except Exception:
        observed = None
    state["collection_finished_epoch_s"] = observed


def pytest_runtest_logfinish(nodeid: str, location: Any) -> None:
    del location
    if _PLUGIN_CONFIG is None or os.environ.get("PYTEST_XDIST_WORKER"):
        return
    _FINISHED_RAW.append(nodeid)


def pytest_runtest_logreport(report: Any) -> None:
    if _PLUGIN_CONFIG is None or os.environ.get("PYTEST_XDIST_WORKER"):
        return
    worker = getattr(report, "worker_id", None)
    if type(worker) is not str or not worker:
        worker = "serial"
    start = _observed_epoch(getattr(report, "start", None))
    stop = _observed_epoch(getattr(report, "stop", None))
    if start is not None or stop is not None:
        bounds = _WORKER_TEST_BOUNDS.setdefault(worker, {})
        if start is not None:
            previous_start = bounds.get("first_test_started_epoch_s")
            bounds["first_test_started_epoch_s"] = (
                start if previous_start is None else min(previous_start, start)
            )
        if stop is not None:
            previous_stop = bounds.get("last_test_finished_epoch_s")
            bounds["last_test_finished_epoch_s"] = (
                stop if previous_stop is None else max(previous_stop, stop)
            )
    nodeid = report.nodeid
    _REPORT_WORKERS.setdefault(nodeid, worker)
    duration = getattr(report, "duration", 0.0)
    if type(duration) in {int, float} and math.isfinite(float(duration)) and duration >= 0:
        _REPORT_DURATIONS[nodeid] += float(duration)
    if getattr(report, "failed", False):
        _FAILURES.add(nodeid)


@_pytest_hookimpl(optionalhook=True)
def pytest_testnodedown(node: Any, error: Any) -> None:
    del error
    if _PLUGIN_CONFIG is None:
        return
    payload = getattr(node, "workeroutput", {}).get("izanagi_acceptance_shard")
    worker_id = getattr(getattr(node, "gateway", None), "id", None)
    if type(worker_id) is str and type(payload) is dict:
        _WORKER_PAYLOADS[worker_id] = payload


def _normalize_runtime_nodeid(nodeid: str, group_by_node: Mapping[str, Optional[str]]) -> str:
    if nodeid in group_by_node:
        return nodeid
    for base, group in group_by_node.items():
        if group is not None and nodeid == f"{base}@{group}":
            return base
    return nodeid


def _scheduler(config: Any) -> str:
    value = getattr(config, _SCHEDULER_ATTR, None)
    if value in {"loadgroup", "serial"}:
        return value
    try:
        dsession = config.pluginmanager.get_plugin("dsession")
        if dsession is None:
            return "serial"
        from xdist.scheduler import LoadGroupScheduling
        if type(dsession.sched) is LoadGroupScheduling:
            return "loadgroup"
    except Exception:
        pass
    return "unknown"


def _worker_payload(config: Any) -> dict[str, Any]:
    state = getattr(config, "_izanagi_acceptance_shard_state", None)
    if type(state) is not dict:
        return {
            "error": "collection-state-missing",
            "collection_finished_epoch_s": None,
            "real_repo_lock_intervals": [],
        }
    worker_id = getattr(config, "workerinput", {}).get("workerid", "")
    payload = {
        "records_digest": state["records_digest"],
        "selected_digest": state["selected_digest"],
        "collection_finished_epoch_s": _observed_epoch(
            state.get("collection_finished_epoch_s")
        ),
        "real_repo_lock_intervals": _observed_lock_intervals(
            state.get("real_repo_lock_intervals")
        ),
    }
    if worker_id == "gw0":
        payload["records"] = state["records"]
        payload["selected"] = state["selected"]
    return payload


def _controller_state(
    config: Any,
) -> tuple[
    list[dict[str, Any]], list[str], list[str], Optional[float],
    dict[str, list[dict[str, float]]],
]:
    state = getattr(config, "_izanagi_acceptance_shard_state", None)
    if type(state) is dict:
        return (
            state["records"], state["selected"], [state["records_digest"]],
            _observed_epoch(state.get("collection_finished_epoch_s")),
            {
                "serial": _observed_lock_intervals(
                    state.get("real_repo_lock_intervals")
                )
            },
        )
    if not _WORKER_PAYLOADS:
        raise ShardError("worker-payloads-missing")
    digests = [
        payload.get("records_digest") for payload in _WORKER_PAYLOADS.values()
    ]
    selected_digests = [
        payload.get("selected_digest") for payload in _WORKER_PAYLOADS.values()
    ]
    if (
        any(type(value) is not str for value in digests + selected_digests)
        or len(set(digests)) != 1
        or len(set(selected_digests)) != 1
    ):
        raise ShardError("worker-collection-mismatch")
    full = [
        payload for payload in _WORKER_PAYLOADS.values()
        if "records" in payload and "selected" in payload
    ]
    if len(full) != 1:
        raise ShardError("worker-authority-count")
    collection_observations = [
        observed
        for payload in _WORKER_PAYLOADS.values()
        if (
            observed := _observed_epoch(
                payload.get("collection_finished_epoch_s")
            )
        ) is not None
    ]
    lock_intervals = {
        worker: _observed_lock_intervals(
            payload.get("real_repo_lock_intervals")
        )
        for worker, payload in _WORKER_PAYLOADS.items()
    }
    return (
        full[0]["records"], full[0]["selected"], sorted(digests),
        max(collection_observations, default=None), lock_intervals,
    )


@_pytest_hookimpl(trylast=True)
def pytest_sessionfinish(session: Any, exitstatus: Any) -> None:
    spec = getattr(session.config, "_izanagi_acceptance_shard_spec", None)
    if spec is None:
        return
    if hasattr(session.config, "workerinput"):
        session.config.workeroutput["izanagi_acceptance_shard"] = _worker_payload(
            session.config
        )
        return
    try:
        (
            raw_records, selected, worker_digests, collection_finished,
            lock_intervals,
        ) = _controller_state(session.config)
        records = parse_records(raw_records)
        group_by_node = {record.nodeid: record.group for record in records}
        finished = sorted(
            _normalize_runtime_nodeid(nodeid, group_by_node)
            for nodeid in _FINISHED_RAW
        )
        normalized_workers: dict[str, str] = {}
        durations: Counter[str] = Counter()
        failures: set[str] = set()
        for raw_nodeid, worker in _REPORT_WORKERS.items():
            nodeid = _normalize_runtime_nodeid(raw_nodeid, group_by_node)
            normalized_workers.setdefault(nodeid, worker)
        for raw_nodeid, duration in _REPORT_DURATIONS.items():
            durations[_normalize_runtime_nodeid(raw_nodeid, group_by_node)] += duration
        for raw_nodeid in _FAILURES:
            failures.add(_normalize_runtime_nodeid(raw_nodeid, group_by_node))
        occupancy: dict[str, dict[str, Any]] = {}
        group_workers: dict[str, set[str]] = defaultdict(set)
        for nodeid in selected:
            worker = normalized_workers.get(nodeid, "unobserved")
            entry = occupancy.setdefault(worker, {"items": 0, "duration_s": 0.0})
            entry["items"] += 1
            entry["duration_s"] += durations[nodeid]
            group = group_by_node.get(nodeid)
            if group is not None:
                group_workers[group].add(worker)
        terminal = session.config.pluginmanager.get_plugin("terminalreporter")
        stats = getattr(terminal, "stats", {}) if terminal is not None else {}
        counts = {
            key: len(stats.get(key, ()))
            for key in ("passed", "failed", "error", "skipped", "xfailed", "xpassed")
        }
        timeline_workers = {}
        lock_observers = {
            worker for worker, intervals in lock_intervals.items() if intervals
        }
        for worker in sorted(set(_WORKER_TEST_BOUNDS) | lock_observers):
            bounds = _WORKER_TEST_BOUNDS.get(worker, {})
            timeline_workers[worker] = {
                "first_test_started_epoch_s": _observed_epoch(
                    bounds.get("first_test_started_epoch_s")
                ),
                "last_test_finished_epoch_s": _observed_epoch(
                    bounds.get("last_test_finished_epoch_s")
                ),
                "real_repo_lock_intervals": _observed_lock_intervals(
                    lock_intervals.get(worker)
                ),
            }
        report = {
            "schema_version": SCHEMA,
            "shard_count": spec.shard_count,
            "shard_index": spec.shard_index,
            "pytest_rc": int(exitstatus),
            "observed_universe": raw_records,
            "selected": selected,
            "finished": finished,
            "effective_scheduler": _scheduler(session.config),
            "terminal_counts": counts,
            "failures": sorted(failures),
            "group_to_workers": {
                group: sorted(workers) for group, workers in sorted(group_workers.items())
            },
            "worker_occupancy": {
                worker: {
                    "items": entry["items"],
                    "duration_s": round(entry["duration_s"], 9),
                }
                for worker, entry in sorted(occupancy.items())
            },
            "junit_path": str(spec.junit_path),
            "worker_collection_digests": worker_digests,
            "session_timeline": {
                "collection_finished_epoch_s": collection_finished,
                "workers": timeline_workers,
            },
        }
        _write_bytes_create_only(spec.report_path, _canonical_json_bytes(report))
    except Exception as exc:
        print(
            f"acceptance shard report finalization failed: {type(exc).__name__}",
            file=sys.stderr,
            flush=True,
        )
        session.exitstatus = INFRA_RC


def create_session(repo: Path, shard_count: int) -> Path:
    if shard_count not in {2, 3}:
        raise ShardError("shard-count")
    repo = repo.resolve()
    main_repo = _git_common_dir(repo).parent
    shared_path = main_repo.parent / _SESSION_PREFIX
    if shared_path.is_symlink():
        raise ShardError("artifact-shared-root-type")
    shared_root = shared_path.resolve()
    _validate_shared_root(repo, main_repo, shared_root)
    shared_path.mkdir(mode=0o700, parents=True, exist_ok=True)
    if shared_path.is_symlink() or not shared_path.is_dir():
        raise ShardError("artifact-shared-root-type")
    shared_root = shared_path.resolve()
    _validate_shared_root(repo, main_repo, shared_root)
    session = shared_root / secrets.token_hex(16)
    session.mkdir(mode=0o700)
    for index in range(shard_count):
        (session / f"shard-{index}").mkdir(mode=0o700)
    return session


def internal_argv(spec: InternalSpec) -> list[str]:
    return [
        f"--izanagi-acceptance-shard-session={spec.session_root}",
        f"--izanagi-acceptance-shard-count={spec.shard_count}",
        f"--izanagi-acceptance-shard-index={spec.shard_index}",
    ]


def _dispatch_worker(
    connection: Any, dispatch_call: Callable[..., Any], spec: InternalSpec,
    artifact_root: Path, control_root: Path, intent_registry_root: Path,
    deadline_at: float,
) -> None:
    log_path = spec.shard_root / "dispatcher.log"
    try:
        fd = os.open(log_path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        os.dup2(fd, 1)
        os.dup2(fd, 2)
        if fd not in {1, 2}:
            os.close(fd)
        result = dispatch_call(
            internal_argv(spec), artifact_root=artifact_root,
            control_root=control_root, nonce=f"shard-{spec.shard_index}",
            intent_registry_root=intent_registry_root,
            intent_group_id=spec.session_root.name,
            intent_shard_index=spec.shard_index,
            deadline_at=deadline_at,
        )
        rc = int(result)
        child_started = getattr(result, "child_started", None) is True
        connection.send({"index": spec.shard_index, "rc": rc, "child_started": child_started})
    except BaseException as exc:
        try:
            connection.send({
                "index": spec.shard_index, "rc": INFRA_RC,
                "child_started": False, "error": type(exc).__name__,
            })
        except BaseException:
            pass
    finally:
        connection.close()


def _terminate(processes: Mapping[int, Any], *, deadline_at: float) -> None:
    for process in processes.values():
        if getattr(process, "pid", None) is not None and process.is_alive():
            process.terminate()
    for process in processes.values():
        if getattr(process, "pid", None) is not None:
            process.join(max(0.0, deadline_at - time.monotonic()))
    for process in processes.values():
        if getattr(process, "pid", None) is not None and process.is_alive():
            process.kill()
            process.join(max(0.0, deadline_at - time.monotonic()))


def _load_reports(session: Path, shard_count: int) -> list[Mapping[str, Any]]:
    reports = []
    for index in range(shard_count):
        path = session / f"shard-{index}" / "report.json"
        try:
            payload = json.loads(path.read_text(encoding="ascii"))
        except (OSError, UnicodeError, json.JSONDecodeError):
            continue
        if type(payload) is dict:
            reports.append(payload)
    return reports


def _emit_merged(result: MergeResult) -> None:
    if result.reason != "ok" or result.scheduler is None:
        print(f"acceptance shard gate failed: {result.reason}", file=sys.stderr, flush=True)
        return
    print(f"collected {len(result.universe)} items", flush=True)
    for nodeid in result.failures:
        print(f"FAILED {nodeid}", flush=True)
    counts = dict(result.terminal_counts)
    summary = ", ".join(
        f"{value} {key}" for key, value in sorted(counts.items()) if value
    ) or "0 tests"
    print(summary, flush=True)
    payload = json.dumps(
        {"effective_scheduler": result.scheduler},
        ensure_ascii=True, separators=(",", ":"), sort_keys=True,
    )
    print(SCHEDULER_PREFIX + payload, flush=True)


def _dispatcher_no_verdict_payload(log_path: Path) -> Optional[Mapping[str, Any]]:
    """dispatcher log 1 本から唯一の未起動 queue-timeout marker を読む。"""

    marker_payload: Optional[bytes] = None
    try:
        with log_path.open("rb") as stream:
            while True:
                line = stream.readline(_DISPATCH_MARKER_LINE_MAX_BYTES + 1)
                if not line:
                    break
                if not line.endswith(b"\n"):
                    if line.startswith(
                        (b"| " + _DISPATCH_OUTCOME_PREFIX, _DISPATCH_OUTCOME_PREFIX)
                    ):
                        return None
                    while True:
                        line = stream.readline(_DISPATCH_MARKER_LINE_MAX_BYTES + 1)
                        if not line:
                            return None
                        if line.endswith(b"\n"):
                            break
                    continue
                raw = line[:-1]
                if raw.endswith(b"\r"):
                    raw = raw[:-1]
                if raw.startswith(b"| " + _DISPATCH_OUTCOME_PREFIX):
                    return None
                if raw.startswith(_DISPATCH_OUTCOME_PREFIX):
                    candidate = raw[len(_DISPATCH_OUTCOME_PREFIX):]
                    if (
                        marker_payload is not None
                        or len(candidate) > _DISPATCH_MARKER_PAYLOAD_MAX_BYTES
                    ):
                        return None
                    marker_payload = candidate
    except OSError:
        return None
    if marker_payload is None:
        return None

    def reject_duplicate_keys(
        pairs: list[tuple[str, object]],
    ) -> dict[str, object]:
        value: dict[str, object] = {}
        for key, item in pairs:
            if key in value:
                raise ValueError("duplicate JSON key")
            value[key] = item
        return value

    try:
        payload = json.loads(
            marker_payload.decode("utf-8"),
            object_pairs_hook=reject_duplicate_keys,
        )
    except (UnicodeError, ValueError, RecursionError):
        return None
    if not (
        type(payload) is dict
        and set(payload) == {"child_rc", "child_started", "kind", "reason"}
        and payload.get("child_rc") is None
        and payload.get("child_started") is False
        and payload.get("kind") == "infra"
        and payload.get("reason") == "queue-wait-timeout"
    ):
        return None
    return payload


def _emit_aggregate_no_verdict_attestation(
    session: Path, shard_count: int, *, child_started_reported: bool,
) -> bool:
    """全 shard 未起動の queue timeout だけを外側へ一行 attest する。"""

    if child_started_reported is True or shard_count not in {2, 3}:
        return False
    for index in range(shard_count):
        if _dispatcher_no_verdict_payload(
            session / f"shard-{index}" / "dispatcher.log"
        ) is None:
            return False
    payload = {
        "child_rc": None,
        "child_started": False,
        "kind": "infra",
        "reason": "queue-wait-timeout",
    }
    print(
        _DISPATCH_OUTCOME_PREFIX.decode("ascii") + json.dumps(
            payload,
            ensure_ascii=True,
            separators=(",", ":"),
            sort_keys=True,
        ),
        file=sys.stderr,
        flush=True,
    )
    return True


def run_parallel(
    *, repo: Path, shard_count: int, dispatch_call: Callable[..., Any],
    collect_login: Callable[[Path, float], tuple[int, Sequence[str]]],
    deadline_at: float,
) -> CompositeResult:
    """K process を全て start 後、login collection と併走させて 6 段 gate する。"""

    if not math.isfinite(deadline_at) or deadline_at <= time.monotonic():
        return CompositeResult(INFRA_RC, child_started=False)
    session = create_session(repo, shard_count)
    print(
        ARTIFACT_PREFIX + json.dumps(
            {"session_root": str(session), "shard_count": shard_count},
            ensure_ascii=True, separators=(",", ":"), sort_keys=True,
        ),
        file=sys.stderr,
        flush=True,
    )
    control_root = repo.resolve() / "output" / "pegasus-dispatch"
    intent_registry_root = session / "dispatch-intents"
    intent_registry_root.mkdir(mode=0o700)
    context = multiprocessing.get_context("fork")
    processes: dict[int, Any] = {}
    receivers: dict[Any, int] = {}
    old_handlers: dict[int, Any] = {}
    finalized = False

    def abort_parent(signum: int, _frame: Any) -> None:
        raise ShardError(f"parent-signal-{signum}")

    for signum in (signal.SIGINT, signal.SIGTERM):
        try:
            old_handlers[signum] = signal.signal(signum, abort_parent)
        except (ValueError, OSError):
            pass

    def finalize_parallel() -> tuple[dict[str, Any], ...]:
        nonlocal finalized
        if finalized:
            return ()
        finalized = True
        for signum, handler in old_handlers.items():
            try:
                signal.signal(signum, handler)
            except (ValueError, OSError):
                pass
        _terminate(processes, deadline_at=deadline_at)
        for connection in receivers:
            try:
                connection.close()
            except OSError:
                pass
        from tools.pegasus import dispatch_compute

        return dispatch_compute.recover_dispatch_intents(
            intent_registry_root,
            control_root,
            deadline_at=deadline_at,
        )

    sender = None
    receiver = None
    try:
        for index in range(shard_count):
            receiver, sender = context.Pipe(duplex=False)
            spec = InternalSpec(session, shard_count, index)
            process = context.Process(
                target=_dispatch_worker,
                args=(
                    sender, dispatch_call, spec, spec.shard_root / "dispatch",
                    control_root, intent_registry_root, deadline_at,
                ),
            )
            processes[index] = process
            receivers[receiver] = index
            process.start()
            sender.close()
            sender = None
            receiver = None
    except BaseException:
        if sender is not None:
            sender.close()
        if receiver is not None:
            receiver.close()
        finalize_parallel()
        result = MergeResult(INFRA_RC, "dispatcher-start")
        _emit_merged(result)
        _emit_aggregate_no_verdict_attestation(
            session, shard_count, child_started_reported=False,
        )
        return CompositeResult(INFRA_RC, child_started=False)
    try:
        login_rc, login_universe = collect_login(session, deadline_at)
    except BaseException:
        finalize_parallel()
        result = MergeResult(INFRA_RC, "login-collection-exception")
        _emit_merged(result)
        _emit_aggregate_no_verdict_attestation(
            session, shard_count, child_started_reported=False,
        )
        return CompositeResult(INFRA_RC, child_started=False)
    if login_rc != 0:
        finalize_parallel()
        result = MergeResult(INFRA_RC, "login-collection")
        _emit_merged(result)
        _emit_aggregate_no_verdict_attestation(
            session, shard_count, child_started_reported=False,
        )
        return CompositeResult(INFRA_RC, child_started=False)

    outcomes: dict[int, dict[str, Any]] = {}
    pending = set(receivers)
    infra = False
    try:
        while pending and not infra:
            timeout = max(0.0, min(1.0, deadline_at - time.monotonic()))
            if timeout == 0:
                infra = True
                break
            ready = wait_connections(pending, timeout=timeout)
            if not ready:
                continue
            for receiver in ready:
                pending.remove(receiver)
                index = receivers[receiver]
                try:
                    payload = receiver.recv()
                except EOFError:
                    payload = {"index": index, "rc": INFRA_RC, "child_started": False}
                finally:
                    receiver.close()
                if type(payload) is not dict or payload.get("index") != index:
                    payload = {"index": index, "rc": INFRA_RC, "child_started": False}
                outcomes[index] = payload
                if type(payload.get("rc")) is not int or payload["rc"] not in {0, 1}:
                    infra = True
                    break
    except BaseException:
        infra = True
    if infra or pending:
        finalize_parallel()
        result = MergeResult(INFRA_RC, "dispatch-infrastructure")
        _emit_merged(result)
        child_started = any(
            payload.get("child_started") is True for payload in outcomes.values()
        )
        _emit_aggregate_no_verdict_attestation(
            session, shard_count, child_started_reported=child_started,
        )
        return CompositeResult(
            INFRA_RC,
            child_started=child_started,
        )
    try:
        for process in processes.values():
            process.join(max(0.0, deadline_at - time.monotonic()))
            if process.is_alive() or process.exitcode != 0:
                infra = True
    except BaseException:
        infra = True
    if infra:
        finalize_parallel()
        result = MergeResult(INFRA_RC, "dispatcher-process")
        _emit_merged(result)
        _emit_aggregate_no_verdict_attestation(
            session,
            shard_count,
            child_started_reported=any(
                payload.get("child_started") is True
                for payload in outcomes.values()
            ),
        )
        return CompositeResult(INFRA_RC, child_started=False)

    recovered = finalize_parallel()
    if recovered:
        result = MergeResult(INFRA_RC, "dispatcher-intent-recovery")
        _emit_merged(result)
        _emit_aggregate_no_verdict_attestation(
            session,
            shard_count,
            child_started_reported=any(
                payload.get("child_started") is True
                for payload in outcomes.values()
            ),
        )
        return CompositeResult(INFRA_RC, child_started=False)

    reports = _load_reports(session, shard_count)
    result = merge_reports(
        expected_k=shard_count,
        reports=reports,
        process_results={index: payload["rc"] for index, payload in outcomes.items()},
        login_universe=login_universe,
        expected_junit_paths=[
            session / f"shard-{index}" / "junit.xml"
            for index in range(shard_count)
        ],
    )
    if result.reason == "ok":
        try:
            merge_junit(
                [session / f"shard-{index}" / "junit.xml" for index in range(shard_count)],
                session / "junit.xml",
                expected_tests=len(result.universe),
            )
        except (OSError, ET.ParseError, ShardError):
            result = MergeResult(INFRA_RC, "junit")
    _emit_merged(result)
    return CompositeResult(
        result.rc,
        child_started=(
            result.rc in {0, 1}
            and any(payload.get("child_started") is True for payload in outcomes.values())
        ),
    )
