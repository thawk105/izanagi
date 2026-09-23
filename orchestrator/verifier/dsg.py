# -*- coding: utf-8 -*-
"""Direct Serialization Graph (Adya) の構築と cycle 検出。

理論 (roadmap §3.1 Tier1):
  committed trx を節点、共有オブジェクトへの競合アクセスを辺とする有向グラフ。
  辺は全て「a が直列順序で b より前」を意味する (a -> b):
    ww : a が版 V を書き、b が同キーの次版を書いた             (write-depends)
    wr : a が版 V を書き、b がその V を読んだ                   (read-depends)
    rw : a が版 V を読み、b が同キーで V の **直後版** を書いた (anti-dependency)
  **DSG が非巡回 ⇔ serializable。** cycle が 1 本でもあれば non-serializable。
  - G0  : ww だけで閉じた cycle
  - G1c : wr/ww から成り rw を含まない cycle (wr を 1 本以上含む)
  - G2  : rw (anti-dependency) を 1 本以上含む cycle  ← SI が許し serializable が
          許さない現象 (write-skew)。「G2 まで見る」= rw を含む cycle を捕まえる。

版順序: 同一キー上では版ID (epoch,tid) が全順序を成し producer を一意に決める
(ww 競合で tid が単調増加。trace-hook で版重複 0 を実測)。rw の「直後版」は
この全順序上の immediate successor 一つだけを使う (それ以降は ww で推移的に届く)。
"""
from __future__ import annotations

import os
from array import array
from bisect import bisect_left, bisect_right
from collections import Counter, defaultdict, deque
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Dict, List, Optional, Sequence, Set, Tuple

from .model import (ObjectIdentity, object_identity, object_label,
                    TxnV3, EdgeReasonV3, AnomalyV3)
from .model import (GENESIS, RW, WR, WW, Anomaly, CycleEdge, EdgeReason,
                    ExistenceViolation, Integrity, Txn, Version)
from .parse import _token_at, _object_at, _CompactTrace, _kill_pool_workers, _txn_from_columns


# Bias the unsigned 64-bit version into signed array("q") without wrapping.
# This preserves tuple order over the entire pair of unsigned 32-bit fields.
_VERSION_BIAS = 1 << 63
_VERSION_LIMIT = 1 << 32


def _packed_version(epoch: int, tid: int) -> int:
    return ((epoch << 32) | tid) - _VERSION_BIAS


def _unpacked_version(value: int) -> Version:
    value += _VERSION_BIAS
    return value >> 32, value & (_VERSION_LIMIT - 1)


def _packed_read_position(values: array, epoch: int, tid: int,
                          lo: int, hi: int) -> tuple[int, int]:
    """Exact writer index (-1 if absent) and strict tuple-order successor.

    Out-of-range tids must not carry into the epoch: all versions of the
    same epoch precede a too-large tid and follow a negative tid.
    """
    if 0 <= epoch < _VERSION_LIMIT and 0 <= tid < _VERSION_LIMIT:
        value = _packed_version(epoch, tid)
        index = bisect_left(values, value, lo, hi)
        writer = index if index < hi and values[index] == value else -1
        return writer, bisect_right(values, value, lo, hi)
    if epoch < 0:
        return -1, lo
    if epoch >= _VERSION_LIMIT:
        return -1, hi
    boundary = ((epoch + (tid >= _VERSION_LIMIT)) << 32) - _VERSION_BIAS
    return -1, bisect_left(values, boundary, lo, hi)


class _PackedVersions(Mapping):
    """Compatibility view; edge workers only use the array attributes.

    Only writer keys have ids. The small per-file tuple selects array headers,
    like trace.files selects columns; no per-write Python objects are retained.
    """

    def __init__(self, key_ids, token_to_key, key_offsets,
                 versions_flat, producers_flat):
        self.key_ids = key_ids
        self.token_to_key = token_to_key
        self.key_offsets = key_offsets
        self.versions_flat = versions_flat
        self.producers_flat = producers_flat

    def __len__(self):
        return len(self.key_offsets) - 1

    def __iter__(self):
        return iter(self.key_ids)

    def __getitem__(self, key):
        key_id = self.key_ids[key]
        return [_unpacked_version(self.versions_flat[index])
                for index in range(self.key_offsets[key_id],
                                   self.key_offsets[key_id + 1])]


class _PackedProducer(Mapping):
    def __init__(self, versions):
        self.packed = versions

    def __len__(self):
        return len(self.packed.versions_flat)

    def __iter__(self):
        for key in self.packed:
            for version in self.packed[key]:
                yield key, version

    def __getitem__(self, key_version):
        key, (epoch, tid) = key_version
        packed = self.packed
        key_id = packed.key_ids[key]
        index, _ = _packed_read_position(
            packed.versions_flat, epoch, tid,
            packed.key_offsets[key_id], packed.key_offsets[key_id + 1])
        if index < 0:
            raise KeyError(key_version)
        return packed.producers_flat[index]


@dataclass(frozen=True)
class _EdgeTask:
    task_index: int
    kind: str
    start: int
    end: int


@dataclass(frozen=True)
class _EdgeCandidateColumns:
    task_index: int
    worker_pid: int
    run_src: array
    run_offsets: array
    run_dst: array
    orphan_reads: int


@dataclass(frozen=True)
class _EdgeWorkerState:
    """One verification's immutable edge input, isolated per child process."""

    trace: _CompactTrace
    producer: Mapping[Tuple[str, Version], int]
    versions: Mapping[str, List[Version]]
    keys: tuple[str, ...]


# Set only by a pool initializer inside each child process.  The parent never
# writes worker input to module globals, so concurrent verifier calls cannot
# replace one another's fork snapshot.  Sequential fallback passes its state
# explicitly and does not consult this slot.
_EDGE_WORKER_STATE: Optional[_EdgeWorkerState] = None
_LAST_DSG_WORKER_PIDS: frozenset[int] = frozenset()


def _weighted_ranges(weights: Sequence[int], parts: int) -> List[tuple[int, int]]:
    """Split contiguous rows near equal cumulative weight without splitting rows."""
    count = len(weights)
    if count == 0:
        return []
    parts = max(1, min(parts, count))
    prefix = [0]
    for weight in weights:
        prefix.append(prefix[-1] + weight)
    if prefix[-1] == 0:
        return [
            (count * part // parts, count * (part + 1) // parts)
            for part in range(parts)
        ]
    boundaries = [0]
    for part in range(1, parts):
        target = prefix[-1] * part / parts
        boundary = bisect_left(prefix, target, lo=boundaries[-1] + 1)
        maximum = count - (parts - part)
        boundaries.append(min(max(boundary, boundaries[-1] + 1), maximum))
    boundaries.append(count)
    return list(zip(boundaries, boundaries[1:]))


def _initialize_edge_worker(state: _EdgeWorkerState) -> None:
    global _EDGE_WORKER_STATE
    _EDGE_WORKER_STATE = state


def _ordered_complete_edge_outcomes(
        received: Sequence[_EdgeCandidateColumns], task_count: int,
) -> Optional[List[_EdgeCandidateColumns]]:
    """Return every task exactly once in logical task order, or no evidence."""
    indices = [outcome.task_index for outcome in received]
    if (len(indices) != task_count
            or sorted(indices) != list(range(task_count))):
        return None
    return sorted(received, key=lambda outcome: outcome.task_index)


def _edge_candidates_for_task(
        task: _EdgeTask, state: Optional[_EdgeWorkerState] = None,
) -> _EdgeCandidateColumns:
    worker_state = state if state is not None else _EDGE_WORKER_STATE
    if worker_state is None:
        raise RuntimeError("compact edge worker state is not initialized")
    trace = worker_state.trace
    producer = worker_state.producer
    versions = worker_state.versions
    destinations_by_source: Dict[int, array] = {}
    orphan_reads = 0

    def add(src: int, dst: int) -> None:
        if src != dst:
            destinations = destinations_by_source.get(src)
            if destinations is None:
                destinations = array("q")
                destinations_by_source[src] = destinations
            destinations.append(dst)

    if isinstance(versions, _PackedVersions):
        values = versions.versions_flat
        writers = versions.producers_flat
        offsets = versions.key_offsets
        if task.kind == "read":
            for rank in range(task.start, task.end):
                path_index = trace.winner_path_index[rank]
                columns = trace.files[path_index]
                token_to_key = versions.token_to_key[path_index]
                row = trace.winner_row[rank]
                txid = trace.winner_txid[rank]
                for read_index in range(columns.txn_read_offsets[row],
                                        columns.txn_read_offsets[row + 1]):
                    key_id = token_to_key[columns.read_key_id[read_index]]
                    epoch = columns.read_ver_epoch[read_index]
                    tid = columns.read_ver_tid[read_index]
                    lo = offsets[key_id] if key_id >= 0 else 0
                    hi = offsets[key_id + 1] if key_id >= 0 else 0
                    writer, successor = _packed_read_position(
                        values, epoch, tid, lo, hi)
                    if writer >= 0:
                        add(writers[writer], txid)
                    elif epoch != 1 or tid != 0:
                        orphan_reads += 1
                    if successor < hi:
                        add(txid, writers[successor])
        elif task.kind == "ww":
            for key_id in range(task.start, task.end):
                for index in range(offsets[key_id], offsets[key_id + 1] - 1):
                    add(writers[index], writers[index + 1])
        else:
            raise RuntimeError(f"unknown compact edge task: {task.kind}")
    elif task.kind == "read":
        for rank in range(task.start, task.end):
            columns = trace.files[trace.winner_path_index[rank]]
            row = trace.winner_row[rank]
            txid = trace.winner_txid[rank]
            read_start = columns.txn_read_offsets[row]
            read_end = columns.txn_read_offsets[row + 1]
            for read_index in range(read_start, read_end):
                key = _object_at(columns, columns.read_key_id[read_index])
                version = (
                    columns.read_ver_epoch[read_index],
                    columns.read_ver_tid[read_index],
                )
                writer = producer.get((key, version))
                if writer is not None:
                    add(writer, txid)
                elif version != GENESIS:
                    orphan_reads += 1
                key_versions = versions.get(key)
                if key_versions:
                    successor = bisect_right(key_versions, version)
                    if successor < len(key_versions):
                        writer = producer.get((key, key_versions[successor]))
                        if writer is not None:
                            add(txid, writer)
    elif task.kind == "ww":
        for key_index in range(task.start, task.end):
            key = worker_state.keys[key_index]
            key_versions = versions[key]
            for version_index in range(len(key_versions) - 1):
                first = producer.get((key, key_versions[version_index]))
                second = producer.get((key, key_versions[version_index + 1]))
                if first is not None and second is not None:
                    add(first, second)
    else:
        raise RuntimeError(f"unknown compact edge task: {task.kind}")

    run_src = array("q")
    run_offsets = array("q", [0])
    run_dst = array("q")
    for source, destinations in destinations_by_source.items():
        run_src.append(source)
        run_dst.extend(destinations)
        run_offsets.append(len(run_dst))
    return _EdgeCandidateColumns(
        task_index=task.task_index,
        worker_pid=os.getpid(),
        run_src=run_src,
        run_offsets=run_offsets,
        run_dst=run_dst,
        orphan_reads=orphan_reads,
    )


def _edge_worker(task: _EdgeTask) -> _EdgeCandidateColumns:
    return _edge_candidates_for_task(task)


def _edge_reason(etype, key, u_ver, v_ver):
    if isinstance(key, tuple):
        return EdgeReasonV3(etype, key[1], u_ver, v_ver, table=key[0])
    return EdgeReason(etype, key, u_ver, v_ver)


class DSG:
    """trace から構築した依存グラフ。辺の type/witness は軽量化のため**保持せず**、
    cycle witness を見つけた後にその数本だけ再構成する (数百万辺の type を全保持
    するとメモリを食うため)。"""

    def __init__(self, txns: List[Txn]):
        self._compact: Optional[_CompactTrace] = None
        self.txns = txns
        self.by_id: Dict[int, Txn] = {t.txid: t for t in txns}
        # (key, version) -> 産んだ trx の txid
        self.producer: Dict[Tuple[ObjectIdentity, Version], int] = {}
        # key -> その上の版の昇順リスト (real のみ。genesis は含めない)
        self.versions: Dict[ObjectIdentity, List[Version]] = {}
        # 軽量隣接 (type を捨てた純粋な有向グラフ)。SCC 検出にこれだけ使う
        self.adj: Dict[int, Set[int]] = defaultdict(set)
        self.integrity = Integrity()
        self._build()
        if txns and isinstance(txns[0], TxnV3):
            self._check_existence()

    @classmethod
    def from_compact(cls, trace: _CompactTrace) -> "DSG":
        """Build from parse columns without materializing parent-side Txn objects."""
        graph = cls.__new__(cls)
        graph._compact = trace
        graph.txns = []
        graph.by_id = {}
        graph.producer = {}
        graph.versions = {}
        graph.adj = {}
        graph.integrity = Integrity()
        graph._build_compact()
        if any(c.schema == 3 for c in trace.files):
            graph._check_existence()
        return graph

    def _existence_rows(self, writes):
        """Yield winner rows as (txid, object, version, op), without Txn copies."""
        if self._compact is None:
            for txn in self.txns:
                for item in (txn.writes if writes else txn.reads):
                    yield (txn.txid, object_identity(item),
                           txn.commit if writes else item.ver,
                           item.op if writes else None)
            return
        trace = self._compact
        for rank, txid in enumerate(trace.winner_txid):
            columns = trace.files[trace.winner_path_index[rank]]
            row = trace.winner_row[rank]
            offsets = columns.txn_write_offsets if writes else columns.txn_read_offsets
            for index in range(offsets[row], offsets[row + 1]):
                token = (columns.write_key_id if writes else columns.read_key_id)[index]
                version = ((columns.txn_commit_epoch[row], columns.txn_commit_tid[row])
                           if writes else
                           (columns.read_ver_epoch[index], columns.read_ver_tid[index]))
                op = _token_at(columns, columns.write_op_id[index]) if writes else None
                yield txid, _object_at(columns, token), version, op

    def _check_existence(self):
        """Apply the stage-1 v3 contract after edge building, once in the parent.

        First-write I implies unborn genesis; this is not an independent check
        of the initial load set. Ambiguous objects have no derived diagnostics.
        """
        ig = self.integrity
        ig.existence_violation_details = details = []
        if ig.version_dups or ig.genesis_commits:
            return
        histories = defaultdict(dict)
        for txid, obj, version, op in self._existence_rows(True):
            owner, ops = histories[obj].setdefault(version, (txid, set()))
            ops.add(op)
        unborn, ambiguous = set(), set()

        def add(txid, obj, version, kind, ops=()):
            details.append(ExistenceViolation(txid, obj[0], obj[1], version, kind, ops))

        for obj, history in histories.items():
            for version, (txid, ops) in history.items():
                if len(ops) > 1:
                    add(txid, obj, version, "ambiguous-write-version", tuple(sorted(ops)))
                    ambiguous.add(obj)
            if obj in ambiguous:
                continue
            versions = sorted(history)
            live = history[versions[0]][1] != {"I"}
            if not live:
                unborn.add(obj)
            for version in versions:
                txid, ops = history[version]
                op = next(iter(ops))
                kind = None
                if op == "I" and live:
                    kind = "insert-on-live"
                elif op == "U" and not live:
                    kind = "update-on-absent"
                elif op == "D" and not live:
                    kind = "delete-on-absent"
                if kind:
                    add(txid, obj, version, kind, (op,))
                live = op != "D"
        for txid, obj, version, _ in self._existence_rows(False):
            if obj in ambiguous:
                continue
            if version == GENESIS:
                if obj in unborn:
                    add(txid, obj, version, "read-unborn-genesis")
            elif histories.get(obj, {}).get(version, (None, set()))[1] == {"D"}:
                add(txid, obj, version, "read-deleted-version")
        details.sort(key=lambda v: (v.txid, v.table, v.key, v.version, v.kind))
        ig.existence_violations = len(details)
        if details:
            counts = Counter(v.kind for v in details)
            kinds = ", ".join(f"{kind}×{counts[kind]}" for kind in sorted(counts))
            sample = "; ".join(
                f"txn{v.txid} table={v.table} key={v.key} ver={v.version} kind={v.kind}"
                for v in details[:5])
            ig.notes.append(f"{len(details)} v3 existence violation(s) [{kinds}]: {sample}")

    # ---- 構築 ----

    def _build(self) -> None:
        per_key: Dict[ObjectIdentity, List[Version]] = defaultdict(list)
        for t in self.txns:
            # commit が genesis 番兵 (1,0) 以下の trx は非物理 (Silo の epoch/tid は 1 始まり)。
            # ちょうど (1,0) は「genesis 読み」と区別できず wr 辺が落ち、(1,0) 未満 (epoch=0 等)
            # は genesis 読みの直後版判定 (bisect) の並びを狂わせるため、どちらも integrity 違反
            # として弾く (= verdict は indeterminate になる)。FIX2 と対で安全側に倒す。
            if t.commit <= GENESIS:
                self.integrity.genesis_commits += 1
                self.integrity.notes.append(
                    f"txid {t.txid} commits at or below genesis sentinel (1,0): "
                    f"{t.commit} (non-physical)")
            for w in t.writes:
                kv = (object_identity(w), t.commit)
                if kv in self.producer and self.producer[kv] != t.txid:
                    self.integrity.version_dups += 1
                    self.integrity.notes.append(
                        f"version dup: {object_label(object_identity(w))} ver={t.commit} "
                        f"by txid {self.producer[kv]} and {t.txid}")
                else:
                    self.producer[kv] = t.txid
                per_key[object_identity(w)].append(t.commit)
        for k, vs in per_key.items():
            self.versions[k] = sorted(set(vs))

        self._add_read_edges()
        self._add_ww_edges()

    def _build_compact(self) -> None:
        trace = self._compact
        if trace is None:
            raise RuntimeError("compact DSG requested without compact trace")
        # Decide before recording integrity or allocating the packed index.
        for rank in range(len(trace.winner_txid)):
            columns = trace.files[trace.winner_path_index[rank]]
            row = trace.winner_row[rank]
            if columns.txn_write_offsets[row] != columns.txn_write_offsets[row + 1]:
                if not (0 <= columns.txn_commit_epoch[row] < _VERSION_LIMIT
                        and 0 <= columns.txn_commit_tid[row] < _VERSION_LIMIT):
                    self._build_compact_tuple()
                    return
        self._build_compact_packed(trace)
        self._build_compact_edges(trace.worker_count)

    def _build_compact_packed(self, trace: _CompactTrace) -> None:
        # Count/scatter into flat columns. Temporary Python sorting objects are
        # bounded by the hottest key, not the complete write population.
        key_ids: Dict[ObjectIdentity, int] = {}
        token_to_key = tuple(array("i", [-1]) * (len(c.token_offsets) - 1)
                             for c in trace.files)
        counts = array("Q")
        for rank in range(len(trace.winner_txid)):
            path = trace.winner_path_index[rank]
            columns = trace.files[path]
            row = trace.winner_row[rank]
            local_ids = token_to_key[path]
            for index in range(columns.txn_write_offsets[row],
                               columns.txn_write_offsets[row + 1]):
                token = columns.write_key_id[index]
                key_id = local_ids[token]
                if key_id < 0:
                    key = _object_at(columns, token)
                    key_id = key_ids.get(key, -1)
                    if key_id < 0:
                        key_id = len(key_ids)
                        key_ids[key] = key_id
                        counts.append(0)
                    local_ids[token] = key_id
                counts[key_id] += 1
        # Resolve read-only occurrences of writer keys without scanning reads.
        for path, columns in enumerate(trace.files):
            local_ids = token_to_key[path]
            for token in range(len(local_ids)):
                if columns.schema == 3 and columns.token_table[token] < 0:
                    continue
                if local_ids[token] < 0:
                    key = _object_at(columns, token)
                    local_ids[token] = key_ids.get(key, -1)
        offsets = array("Q", [0])
        for count in counts:
            offsets.append(offsets[-1] + count)
        cursor = offsets[:-1]
        values = array("q", [0]) * offsets[-1]
        writers = array("q", [0]) * offsets[-1]
        for rank, txid in enumerate(trace.winner_txid):
            path = trace.winner_path_index[rank]
            columns = trace.files[path]
            row = trace.winner_row[rank]
            value = _packed_version(columns.txn_commit_epoch[row],
                                    columns.txn_commit_tid[row])
            for index in range(columns.txn_write_offsets[row],
                               columns.txn_write_offsets[row + 1]):
                key_id = token_to_key[path][columns.write_key_id[index]]
                slot = cursor[key_id]
                values[slot] = value
                writers[slot] = txid
                cursor[key_id] += 1
        del counts, cursor
        # Stable sort retains occurrence order for equal versions. Compact in
        # place, so a second all-write payload is not live at the fork boundary.
        unique_offsets = array("Q", [0])
        end = 0
        for key_id in range(len(key_ids)):
            order = sorted(range(offsets[key_id], offsets[key_id + 1]),
                           key=values.__getitem__)
            rows = [(values[index], writers[index]) for index in order]
            previous = None
            for value, writer in rows:
                if value != previous:
                    values[end] = value
                    writers[end] = writer
                    end += 1
                    previous = value
            unique_offsets.append(end)
            del order, rows
        del values[end:], writers[end:]
        packed = _PackedVersions(key_ids, token_to_key, unique_offsets,
                                 values, writers)
        self.versions = packed
        self.producer = _PackedProducer(packed)
        # Replay diagnostic events in original rank/write order, including
        # write-free genesis commits. The first producer is already known.
        for rank, txid in enumerate(trace.winner_txid):
            path = trace.winner_path_index[rank]
            columns = trace.files[path]
            row = trace.winner_row[rank]
            commit = (columns.txn_commit_epoch[row], columns.txn_commit_tid[row])
            if commit <= GENESIS:
                self.integrity.genesis_commits += 1
                self.integrity.notes.append(
                    f"txid {txid} commits at or below genesis sentinel (1,0): "
                    f"{commit} (non-physical)")
            value = _packed_version(*commit)
            for index in range(columns.txn_write_offsets[row],
                               columns.txn_write_offsets[row + 1]):
                token = columns.write_key_id[index]
                key_id = token_to_key[path][token]
                slot = bisect_left(values, value, unique_offsets[key_id],
                                   unique_offsets[key_id + 1])
                first = writers[slot]
                if first != txid:
                    key = _object_at(columns, token)
                    self.integrity.version_dups += 1
                    self.integrity.notes.append(
                        f"version dup: {object_label(key)} ver={commit} "
                        f"by txid {first} and {txid}")

    def _build_compact_tuple(self) -> None:
        trace = self._compact
        if trace is None:
            raise RuntimeError("compact DSG requested without compact trace")
        per_key: Dict[ObjectIdentity, List[Version]] = {}
        for rank, txid in enumerate(trace.winner_txid):
            columns = trace.files[trace.winner_path_index[rank]]
            row = trace.winner_row[rank]
            commit = (
                columns.txn_commit_epoch[row], columns.txn_commit_tid[row],
            )
            if commit <= GENESIS:
                self.integrity.genesis_commits += 1
                self.integrity.notes.append(
                    f"txid {txid} commits at or below genesis sentinel (1,0): "
                    f"{commit} (non-physical)")
            write_start = columns.txn_write_offsets[row]
            write_end = columns.txn_write_offsets[row + 1]
            for write_index in range(write_start, write_end):
                token_id = columns.write_key_id[write_index]
                key = _object_at(columns, token_id)
                key_version = (key, commit)
                if (key_version in self.producer
                        and self.producer[key_version] != txid):
                    self.integrity.version_dups += 1
                    self.integrity.notes.append(
                        f"version dup: {object_label(key)} ver={commit} "
                        f"by txid {self.producer[key_version]} and {txid}")
                else:
                    self.producer[key_version] = txid
                per_key.setdefault(key, []).append(commit)
        for key, key_versions in per_key.items():
            self.versions[key] = sorted(set(key_versions))
        self._build_compact_edges(trace.worker_count)

    def _build_compact_edges(self, worker_count: int) -> None:
        global _LAST_DSG_WORKER_PIDS

        trace = self._compact
        if trace is None:
            raise RuntimeError("compact edge build requested without compact trace")
        read_weights: List[int] = []
        for rank in range(len(trace.winner_txid)):
            columns = trace.files[trace.winner_path_index[rank]]
            row = trace.winner_row[rank]
            count = columns.txn_read_offsets[row + 1] - columns.txn_read_offsets[row]
            read_weights.append(count)
        keys = tuple(self.versions)
        if isinstance(self.versions, _PackedVersions):
            offsets = self.versions.key_offsets
            ww_weights = [max(0, offsets[i + 1] - offsets[i] - 1)
                          for i in range(len(keys))]
        else:
            ww_weights = [max(0, len(self.versions[key]) - 1) for key in keys]

        tasks: List[_EdgeTask] = []
        parallelism = max(1, min(worker_count, len(trace.winner_txid) or 1))
        for start, end in _weighted_ranges(read_weights, parallelism):
            tasks.append(_EdgeTask(len(tasks), "read", start, end))
        for start, end in _weighted_ranges(ww_weights, min(worker_count, len(keys) or 1)):
            tasks.append(_EdgeTask(len(tasks), "ww", start, end))

        state = _EdgeWorkerState(
            trace=trace,
            producer=self.producer,
            versions=self.versions,
            keys=keys,
        )
        outcomes: Optional[List[_EdgeCandidateColumns]] = None
        received: List[_EdgeCandidateColumns] = []
        executor = None
        futures = []
        future = None
        if worker_count > 1 and len(tasks) > 1:
            try:
                import multiprocessing
                from concurrent.futures import ProcessPoolExecutor, as_completed

                context = multiprocessing.get_context("fork")
                executor = ProcessPoolExecutor(
                    max_workers=worker_count,
                    mp_context=context,
                    initializer=_initialize_edge_worker,
                    initargs=(state,),
                )
                failed = True
                try:
                    futures = [executor.submit(_edge_worker, task) for task in tasks]
                    failed = False
                    for future in as_completed(futures):
                        try:
                            received.append(future.result())
                        except Exception:
                            failed = True
                            break
                    if failed:
                        for future in futures:
                            future.cancel()
                except BaseException:
                    failed = True
                    raise
                finally:
                    if failed:
                        _kill_pool_workers(executor)
                    executor.shutdown(wait=True, cancel_futures=True)
                if not failed:
                    outcomes = _ordered_complete_edge_outcomes(
                        received, len(tasks))
            except (
                    ImportError, OSError, BlockingIOError, RuntimeError,
                    ValueError, AssertionError,
            ):
                outcomes = None
        if outcomes is None:
            received.clear()
            futures.clear()
            future = executor = None
            outcomes = _ordered_complete_edge_outcomes(
                [_edge_candidates_for_task(task, state) for task in tasks],
                len(tasks),
            )
            if outcomes is None:
                raise AssertionError("parent edge recomputation was incomplete")

        _LAST_DSG_WORKER_PIDS = frozenset(
            outcome.worker_pid for outcome in outcomes
        )
        self.integrity.orphan_reads += sum(
            outcome.orphan_reads for outcome in outcomes)

        # Task order is the legacy _add call order: txid/read row, wr then rw,
        # followed by first-seen key order for ww.  Replay into real sets before
        # freezing their runtime iteration order for Tarjan/BFS.
        adjacency: Dict[int, Set[int]] = defaultdict(set)
        for outcome in outcomes:
            for run_index, source in enumerate(outcome.run_src):
                start = outcome.run_offsets[run_index]
                end = outcome.run_offsets[run_index + 1]
                # Keep the operand on array slice's generic iterable path.
                # Passing a set/dict or pre-resizing the set can change set
                # iteration order and therefore change the selected witness.
                adjacency[source].update(outcome.run_dst[start:end])
        self.adj = {
            source: tuple(destinations)
            for source, destinations in adjacency.items()
        }

    def _add(self, u: int, v: int) -> None:
        if u != v:                       # 自己ループ (RMW で自分が直後版を書く等) は辺にしない
            self.adj[u].add(v)

    def _add_read_edges(self) -> None:
        prod = self.producer
        for t in self.txns:
            tid = t.txid
            for r in t.reads:
                k, rv = object_identity(r), r.ver
                # wr: 読んだ版そのものを書いた producer -> 読み手。
                # **genesis 判定は「値が (1,0) か」でなく「producer が居るか」で行う** (FIX2)。
                # genesis (1,0) は誰も書かないので producer 不在 → wr 辺なし。逆に万一 (1,0) を
                # 書いた trx が居れば producer が居るので wr 辺を張る (落とさない)。非 genesis
                # なのに producer 不在 = orphan (abort 版の dirty read 等) として integrity に記録。
                p = prod.get((k, rv))
                if p is not None:
                    if p != tid:
                        self._add(p, tid)
                elif rv != GENESIS:
                    self.integrity.orphan_reads += 1
                # rw (anti-dependency): 読んだ版の直後版を書いた trx へ 読み手 -> 上書き手
                vs = self.versions.get(k)
                if vs:
                    idx = bisect_right(vs, rv)
                    if idx < len(vs):
                        w_tx = prod.get((k, vs[idx]))
                        if w_tx is not None and w_tx != tid:
                            self._add(tid, w_tx)

    def _add_ww_edges(self) -> None:
        prod = self.producer
        for k, vs in self.versions.items():
            for i in range(len(vs) - 1):
                a = prod.get((k, vs[i]))
                b = prod.get((k, vs[i + 1]))
                if a is not None and b is not None:
                    self._add(a, b)

    @property
    def n_edges(self) -> int:
        return sum(len(s) for s in self.adj.values())

    # ---- cycle 検出 (Tarjan SCC, iterative) ----

    def _sccs(self) -> List[List[int]]:
        """非自明な (size>1) SCC のみ返す。自己ループは辺にしていないので
        singleton SCC は cycle ではない。"""
        index: Dict[int, int] = {}
        low: Dict[int, int] = {}
        on_stack: Dict[int, bool] = {}
        stack: List[int] = []
        counter = 0
        out: List[List[int]] = []

        for root in list(self.adj.keys()):
            if root in index:
                continue
            work: List[Tuple[int, "object"]] = [(root, iter(self.adj.get(root, ())))]
            index[root] = low[root] = counter
            counter += 1
            stack.append(root)
            on_stack[root] = True
            while work:
                node, it = work[-1]
                advanced = False
                for w in it:
                    if w not in index:
                        index[w] = low[w] = counter
                        counter += 1
                        stack.append(w)
                        on_stack[w] = True
                        work.append((w, iter(self.adj.get(w, ()))))
                        advanced = True
                        break
                    elif on_stack.get(w):
                        if index[w] < low[node]:
                            low[node] = index[w]
                if advanced:
                    continue
                if low[node] == index[node]:
                    comp: List[int] = []
                    while True:
                        x = stack.pop()
                        on_stack[x] = False
                        comp.append(x)
                        if x == node:
                            break
                    if len(comp) > 1:
                        out.append(comp)
                work.pop()
                if work:
                    parent = work[-1][0]
                    if low[node] < low[parent]:
                        low[parent] = low[node]
        return out

    def _shortest_cycle(self, scc: Set[int]) -> List[int]:
        """SCC 内の (ある節点 s を通る) 最短 cycle を BFS で取り、節点列で返す。
        非自明 SCC では必ず存在する。返りは [s, ..., u] (閉じる辺 u->s は含めず)。"""
        s = min(scc)
        parent: Dict[int, Optional[int]] = {s: None}
        q = deque([s])
        while q:
            u = q.popleft()
            for v in self.adj.get(u, ()):
                if v not in scc:
                    continue
                if v == s:
                    path = [u]
                    x = u
                    while parent[x] is not None:
                        x = parent[x]  # type: ignore[assignment]
                        path.append(x)
                    path.reverse()
                    return path
                if v not in parent:
                    parent[v] = u
                    q.append(v)
        return [s]  # 到達不能 — 理論上起きない

    # ---- witness 辺の再構成 (type と key/版を取り戻す) ----

    def _txn_for_id(self, txid: int) -> Txn:
        if self._compact is None:
            return self.by_id[txid]
        rank = bisect_left(self._compact.winner_txid, txid)
        if (rank >= len(self._compact.winner_txid)
                or self._compact.winner_txid[rank] != txid):
            raise KeyError(txid)
        columns = self._compact.files[self._compact.winner_path_index[rank]]
        return _txn_from_columns(columns, self._compact.winner_row[rank])

    def _reasons(self, u: int, v: int) -> List[EdgeReason]:
        ut, vt = self._txn_for_id(u), self._txn_for_id(v)
        reasons: List[EdgeReason] = []
        u_writes = {object_identity(w): ut.commit for w in ut.writes}
        v_writes = {object_identity(w): vt.commit for w in vt.writes}

        # ww: u の版の直後版を v が書いた
        for k in sorted(u_writes.keys() & v_writes.keys()):
            vs = self.versions.get(k)
            if not vs:
                continue
            iu = bisect_left(vs, u_writes[k])
            if iu < len(vs) and vs[iu] == u_writes[k] and iu + 1 < len(vs) \
                    and vs[iu + 1] == v_writes[k]:
                reasons.append(_edge_reason(WW, k, u_writes[k], v_writes[k]))

        # wr: u が書いた版そのものを v が読んだ
        for r in vt.reads:
            k = object_identity(r)
            if k in u_writes and r.ver == u_writes[k]:
                reasons.append(_edge_reason(WR, k, u_writes[k], None))

        # rw: u が読んだ版の直後版を v が書いた
        for r in ut.reads:
            k = object_identity(r)
            vs = self.versions.get(k)
            if not vs or k not in v_writes:
                continue
            idx = bisect_right(vs, r.ver)
            if idx < len(vs) and vs[idx] == v_writes[k]:
                reasons.append(_edge_reason(RW, k, r.ver, v_writes[k]))
        return reasons

    @staticmethod
    def _classify(edges: List[CycleEdge]) -> str:
        """cycle を G0/G1c/G2 に分類する。

        **realizable な (物理的に起こりうる) trace では戻り値は常に G2。** 証明:
        大域順序を commit (epoch,tid) の辞書式順とすると、ww は版順=commit 順なので
        前向き (a.commit<b.commit)、wr も b が a の commit 済み版を読むので前向き。
        commit 順を**減少**させられるのは rw だけ。cycle は始点に戻る以上、減少辺を
        最低1本含む → 必ず rw を含む → G2。よって G0 (ww のみ)/G1c (wr のみ) は
        realizable trace では出ない。G0/G1c 枝は **非 realizable な手製/破損 trace**
        (例: 複数 trx が版スタンプを共有) でのみ到達するが、verdict は cycle の有無
        (= total==0) だけで決まり分類に依存しないので無害。詳細は
        tests/fixtures/README.md と output/insights/。
        """
        all_types = {t for e in edges for t in e.types}
        if RW in all_types:
            return "G2"
        if WR in all_types:
            return "G1c"
        return "G0"

    def anomalies(self, max_report: Optional[int] = None) -> Tuple[List[Anomaly], int]:
        """検出した anomaly のリストと、全 cycle (SCC) 数を返す。
        max_report で報告本数を絞る (全数は第2返り値)。"""
        sccs = self._sccs()
        total = len(sccs)
        # 大きい順より「小さく読みやすい witness」を優先したいので size 昇順
        sccs.sort(key=len)
        out: List[Anomaly] = []
        for comp in sccs:
            if max_report is not None and len(out) >= max_report:
                break
            scc_set = set(comp)
            nodes = self._shortest_cycle(scc_set)
            edges: List[CycleEdge] = []
            ring = list(zip(nodes, nodes[1:] + nodes[:1]))
            for a, b in ring:
                reasons = self._reasons(a, b)
                if not reasons:
                    self.integrity.notes.append(
                        f"witness edge {a}->{b} had no reconstructable reason")
                edges.append(CycleEdge(src=a, dst=b, reasons=reasons))
            extra = {}
            if isinstance(self._txn_for_id(nodes[0]), TxnV3):
                extra["cycle_tx_types"] = tuple(self._txn_for_id(n).tx_type for n in nodes)
            out.append((AnomalyV3 if extra else Anomaly)(
                cycle=nodes, phenomenon=self._classify(edges), edges=edges, **extra))
        return out, total
