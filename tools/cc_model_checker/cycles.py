"""Dependency cycles over a validated committed history."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Literal, Mapping

INITIAL_WRITER = "initial"


class ModelInputError(ValueError):
    """Malformed committed-history input, distinct from a model violation."""


@dataclass(frozen=True)
class CommittedVersion:
    id: str
    key: str
    writer: str


@dataclass(frozen=True)
class Read:
    key: str
    version_id: str


@dataclass(frozen=True)
class DependencyEdge:
    source: str
    target: str
    kind: Literal["ww", "wr", "rw"]
    key: str
    from_version: str
    to_version: str


@dataclass(frozen=True)
class Cycle:
    txns: tuple[str, ...]
    edges: tuple[DependencyEdge, ...]


def find_cycle(
    committed_txn_ids: frozenset[str],
    versions_by_key: Mapping[str, tuple[CommittedVersion, ...]],
    read_log_by_txn: Mapping[str, tuple[Read, ...]],
) -> Cycle | None:
    """Find the first DFS cycle. Each version tuple is in logical version order.

    Initial versions occupy the prefix of each tuple; adapters, including a
    timestamped adapter, must establish this order before calling.
    """
    committed = frozenset(committed_txn_ids)
    if INITIAL_WRITER in committed:
        raise ModelInputError("reserved initial writer is a transaction")
    by_id: dict[str, CommittedVersion] = {}
    positions: dict[str, tuple[tuple[CommittedVersion, ...], int]] = {}
    for key, versions in versions_by_key.items():
        seen_written = False
        for index, version in enumerate(versions):
            if version.id in by_id:
                raise ModelInputError(f"duplicate version ID: {version.id}")
            if version.key != key:
                raise ModelInputError(f"version key mismatch: {version.id}")
            if version.writer not in committed and version.writer != INITIAL_WRITER:
                raise ModelInputError(f"unknown writer: {version.writer}")
            if version.writer == INITIAL_WRITER and seen_written:
                raise ModelInputError("initial versions must precede written versions")
            if version.writer != INITIAL_WRITER:
                seen_written = True
            by_id[version.id] = version
            positions[version.id] = (versions, index)
    for reader, reads in read_log_by_txn.items():
        if reader not in committed:
            raise ModelInputError(f"unknown reader: {reader}")
        for read in reads:
            version = by_id.get(read.version_id)
            if version is None:
                raise ModelInputError(f"missing read version: {read.version_id}")
            if version.key != read.key:
                raise ModelInputError(f"read key mismatch: {read.version_id}")
    edges: dict[str, list[DependencyEdge]] = {txn: [] for txn in committed}

    def add(source: str, target: str, kind: Literal["ww", "wr", "rw"],
            key: str, earlier: str, later: str) -> None:
        if source != target and source in committed and target in committed:
            edges[source].append(DependencyEdge(source, target, kind, key, earlier, later))

    for key, versions in versions_by_key.items():
        for earlier, later in zip(versions, versions[1:]):
            add(earlier.writer, later.writer, "ww", key, earlier.id, later.id)
    for reader in sorted(read_log_by_txn):
        for read in read_log_by_txn[reader]:
            version = by_id[read.version_id]
            if version.writer == reader:
                continue
            add(version.writer, reader, "wr", read.key, version.id, version.id)
            versions, index = positions[version.id]
            for later in versions[index + 1:]:
                add(reader, later.writer, "rw", read.key, version.id, later.id)

    explored: set[str] = set()

    def visit(node: str, path: tuple[str, ...], path_edges: tuple[DependencyEdge, ...]) -> Cycle | None:
        for edge in edges[node]:
            if edge.target in path:
                offset = path.index(edge.target)
                return Cycle(path[offset:], path_edges[offset:] + (edge,))
            if edge.target not in explored:
                found = visit(edge.target, path + (edge.target,), path_edges + (edge,))
                if found is not None:
                    return found
        explored.add(node)
        return None

    for txn in sorted(committed):
        if txn not in explored:
            found = visit(txn, (txn,), ())
            if found is not None:
                return found
    return None
