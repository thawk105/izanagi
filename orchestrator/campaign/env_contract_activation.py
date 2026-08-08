# -*- coding: utf-8 -*-
"""Environment-contract activation record の純粋な schema / chain leaf。"""
from __future__ import annotations

import hashlib
import json
import os
import re
import stat
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path


SCHEMA_VERSION = "env-contract-activation/v1"

_RECORD_KEYS = frozenset({
    "schema_version",
    "activation_serial",
    "previous_activation_state_sha256",
    "active_contracts",
    "activation_state_sha256",
})
_ACTIVE_CONTRACT_KEYS = frozenset({
    "env_tag",
    "generation",
    "contract_sha256",
})
_RECORD_NAME_RE = re.compile(r"[0-9]{8}\.json")
_SLUG_RE = re.compile(r"[a-z0-9][a-z0-9._-]*")
_HEX64_RE = re.compile(r"[0-9a-f]{64}")


class ActivationRecordError(ValueError):
    """Activation authority の fail-closed 検証失敗。"""


@dataclass(frozen=True)
class ActiveContract:
    """一つの activation record が指す登録済み契約行。"""

    env_tag: str
    generation: int
    contract_sha256: str

    def __post_init__(self) -> None:
        if type(self.env_tag) is not str or _SLUG_RE.fullmatch(self.env_tag) is None:
            raise ActivationRecordError(f"env_tag が canonical slug でない: {self.env_tag!r}")
        if type(self.generation) is not int or self.generation <= 0:
            raise ActivationRecordError(
                f"generation は正の exact int でなければならない: {self.generation!r}"
            )
        if (type(self.contract_sha256) is not str
                or _HEX64_RE.fullmatch(self.contract_sha256) is None):
            raise ActivationRecordError(
                "contract_sha256 は 64 桁の小文字 hex でなければならない: "
                f"{self.contract_sha256!r}"
            )

    def as_dict(self) -> dict[str, object]:
        return {
            "env_tag": self.env_tag,
            "generation": self.generation,
            "contract_sha256": self.contract_sha256,
        }


@dataclass(frozen=True)
class ActivationState:
    """検証済み chain の terminal state と ever-active 集合。"""

    activation_serial: int
    activation_state_sha256: str
    active_contracts: tuple[ActiveContract, ...]
    ever_active_contract_sha256s: frozenset[str]

    def __post_init__(self) -> None:
        if type(self.activation_serial) is not int or self.activation_serial <= 0:
            raise ActivationRecordError("activation_serial が正の exact int でない")
        if (type(self.activation_state_sha256) is not str
                or _HEX64_RE.fullmatch(self.activation_state_sha256) is None):
            raise ActivationRecordError("activation_state_sha256 が 64 lower-hex でない")
        if type(self.active_contracts) is not tuple or not self.active_contracts:
            raise ActivationRecordError("active_contracts が非空 exact tuple でない")
        if any(type(row) is not ActiveContract for row in self.active_contracts):
            raise ActivationRecordError("active_contracts に exact ActiveContract でない要素がある")
        if type(self.ever_active_contract_sha256s) is not frozenset:
            raise ActivationRecordError("ever_active_contract_sha256s が frozenset でない")
        current_hashes = {row.contract_sha256 for row in self.active_contracts}
        if not current_hashes <= self.ever_active_contract_sha256s:
            raise ActivationRecordError("current contract が ever-active 集合に含まれない")


def _reject_constant(value: str) -> object:
    raise ActivationRecordError(f"JSON の非有限値を受理しない: {value}")


def _object_without_duplicates(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise ActivationRecordError(f"JSON object に重複 key がある: {key!r}")
        result[key] = value
    return result


def canonical_record_bytes(document: Mapping[str, object]) -> bytes:
    """Mapping を activation record と同じ canonical JSON bytes にする (LF は含めない)。"""
    if not isinstance(document, Mapping):
        raise ActivationRecordError("canonical document は Mapping でなければならない")
    try:
        text = json.dumps(
            dict(document),
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=True,
            allow_nan=False,
        )
    except (TypeError, ValueError) as exc:
        raise ActivationRecordError(f"canonical JSON に変換できない: {exc}") from exc
    return text.encode("ascii")


def _state_sha256(document: Mapping[str, object]) -> str:
    body = {key: value for key, value in document.items()
            if key != "activation_state_sha256"}
    return hashlib.sha256(canonical_record_bytes(body)).hexdigest()


def build_activation_record(
    *,
    activation_serial: int,
    previous_activation_state_sha256: str | None,
    active_contracts: Sequence[ActiveContract],
) -> dict[str, object]:
    """型検査済みの canonical activation record object を構築する。"""
    if type(activation_serial) is not int or activation_serial <= 0:
        raise ActivationRecordError("activation_serial は正の exact int でなければならない")
    if activation_serial == 1:
        if previous_activation_state_sha256 is not None:
            raise ActivationRecordError("serial 1 の predecessor は null でなければならない")
    elif (type(previous_activation_state_sha256) is not str
          or _HEX64_RE.fullmatch(previous_activation_state_sha256) is None):
        raise ActivationRecordError("serial 2 以降の predecessor は 64 lower-hex でなければならない")
    rows = tuple(active_contracts)
    if not rows or any(type(row) is not ActiveContract for row in rows):
        raise ActivationRecordError("active_contracts は非空の exact ActiveContract 列でなければならない")
    env_tags = [row.env_tag for row in rows]
    if env_tags != sorted(env_tags) or len(set(env_tags)) != len(env_tags):
        raise ActivationRecordError("active_contracts は env_tag 昇順かつ重複なしでなければならない")
    document: dict[str, object] = {
        "schema_version": SCHEMA_VERSION,
        "activation_serial": activation_serial,
        "previous_activation_state_sha256": previous_activation_state_sha256,
        "active_contracts": [row.as_dict() for row in rows],
    }
    document["activation_state_sha256"] = _state_sha256(document)
    return document


def _decode_record(raw: bytes) -> dict[str, object]:
    if type(raw) is not bytes:
        raise ActivationRecordError("record bytes は exact bytes でなければならない")
    try:
        text = raw.decode("utf-8")
        document = json.loads(
            text,
            object_pairs_hook=_object_without_duplicates,
            parse_constant=_reject_constant,
        )
    except ActivationRecordError:
        raise
    except (UnicodeError, json.JSONDecodeError) as exc:
        raise ActivationRecordError(f"activation record JSON を parse できない: {exc}") from exc
    if type(document) is not dict:
        raise ActivationRecordError("activation record top-level は object でなければならない")
    expected = canonical_record_bytes(document) + b"\n"
    if raw != expected:
        raise ActivationRecordError("activation record bytes が canonical JSON + LF でない")
    return document


def _validate_document(document: dict[str, object]) -> tuple[int, str | None, tuple[ActiveContract, ...], str]:
    if set(document) != _RECORD_KEYS:
        raise ActivationRecordError(
            f"activation record key 集合が exact でない: {sorted(document)}"
        )
    if type(document["schema_version"]) is not str or document["schema_version"] != SCHEMA_VERSION:
        raise ActivationRecordError(f"schema_version が不正: {document['schema_version']!r}")
    serial = document["activation_serial"]
    if type(serial) is not int or serial <= 0:
        raise ActivationRecordError("activation_serial は正の exact int でなければならない")
    predecessor = document["previous_activation_state_sha256"]
    if serial == 1:
        if predecessor is not None:
            raise ActivationRecordError("serial 1 の predecessor は null でなければならない")
    elif type(predecessor) is not str or _HEX64_RE.fullmatch(predecessor) is None:
        raise ActivationRecordError("serial 2 以降の predecessor は 64 lower-hex でなければならない")
    state_hash = document["activation_state_sha256"]
    if type(state_hash) is not str or _HEX64_RE.fullmatch(state_hash) is None:
        raise ActivationRecordError("activation_state_sha256 は 64 lower-hex でなければならない")
    actual_state_hash = _state_sha256(document)
    if state_hash != actual_state_hash:
        raise ActivationRecordError(
            f"activation state hash 不一致: expected={state_hash} observed={actual_state_hash}"
        )
    raw_rows = document["active_contracts"]
    if type(raw_rows) is not list or not raw_rows:
        raise ActivationRecordError("active_contracts は非空 list でなければならない")
    rows: list[ActiveContract] = []
    for index, raw_row in enumerate(raw_rows):
        if type(raw_row) is not dict or set(raw_row) != _ACTIVE_CONTRACT_KEYS:
            keys = sorted(raw_row) if type(raw_row) is dict else type(raw_row).__name__
            raise ActivationRecordError(f"active_contracts[{index}] の key/type が exact でない: {keys}")
        rows.append(ActiveContract(
            env_tag=raw_row["env_tag"],
            generation=raw_row["generation"],
            contract_sha256=raw_row["contract_sha256"],
        ))
    env_tags = [row.env_tag for row in rows]
    if env_tags != sorted(env_tags) or len(set(env_tags)) != len(env_tags):
        raise ActivationRecordError("active_contracts は env_tag 昇順かつ重複なしでなければならない")
    return serial, predecessor, tuple(rows), state_hash


def _registered_index(
    registered_contracts: Mapping[str, tuple[tuple[int, str], ...]],
) -> dict[str, dict[int, str]]:
    if not isinstance(registered_contracts, Mapping) or not registered_contracts:
        raise ActivationRecordError("registered_contracts は非空 Mapping でなければならない")
    result: dict[str, dict[int, str]] = {}
    for env_tag, sequence in registered_contracts.items():
        if type(env_tag) is not str or _SLUG_RE.fullmatch(env_tag) is None:
            raise ActivationRecordError(f"registered env_tag が canonical でない: {env_tag!r}")
        if type(sequence) is not tuple or not sequence:
            raise ActivationRecordError(f"{env_tag!r} の registered sequence が非空 tuple でない")
        rows: dict[int, str] = {}
        for pair in sequence:
            if type(pair) is not tuple or len(pair) != 2:
                raise ActivationRecordError(f"{env_tag!r} の registered row が pair でない")
            generation, contract_sha256 = pair
            if type(generation) is not int or generation <= 0 or generation in rows:
                raise ActivationRecordError(f"{env_tag!r} の registered generation が不正")
            if type(contract_sha256) is not str or _HEX64_RE.fullmatch(contract_sha256) is None:
                raise ActivationRecordError(f"{env_tag!r} の registered hash が不正")
            rows[generation] = contract_sha256
        result[env_tag] = rows
    return result


def validate_activation_records(
    records: Sequence[tuple[str, bytes]],
    *,
    registered_contracts: Mapping[str, tuple[tuple[int, str], ...]],
    expected_head_serial: int,
    expected_head_state_sha256: str,
) -> ActivationState:
    """Record 列を schema、chain、registry、pinned head へ exact 照合する。"""
    if type(expected_head_serial) is not int or expected_head_serial <= 0:
        raise ActivationRecordError("expected head serial が正の exact int でない")
    if (type(expected_head_state_sha256) is not str
            or _HEX64_RE.fullmatch(expected_head_state_sha256) is None):
        raise ActivationRecordError("expected head state hash が 64 lower-hex でない")
    catalog = _registered_index(registered_contracts)
    raw_records = tuple(records)
    if any(type(item) is not tuple or len(item) != 2 for item in raw_records):
        raise ActivationRecordError("records は (filename, bytes) の exact tuple 列でなければならない")
    ordered = sorted(raw_records, key=lambda item: item[0])
    if not ordered:
        raise ActivationRecordError("activation record chain が空")
    names = [item[0] for item in ordered]
    if len(names) != len(set(names)):
        raise ActivationRecordError("activation record filename が重複している")
    previous_hash: str | None = None
    ever_active: set[str] = set()
    terminal_serial = 0
    terminal_hash = ""
    for expected_serial, (name, raw) in enumerate(ordered, start=1):
        if type(name) is not str or _RECORD_NAME_RE.fullmatch(name) is None:
            raise ActivationRecordError(f"activation record filename が不正: {name!r}")
        document = _decode_record(raw)
        serial, predecessor, rows, state_hash = _validate_document(document)
        if serial != expected_serial or name != f"{serial:08d}.json":
            raise ActivationRecordError(
                f"filename / serial / 連番が不一致: name={name!r} serial={serial}"
            )
        if predecessor != previous_hash:
            raise ActivationRecordError(
                f"predecessor hash chain 不一致: serial={serial}"
            )
        row_envs = {row.env_tag for row in rows}
        if row_envs != set(catalog):
            raise ActivationRecordError(
                "active env 集合が登録 env 集合と exact 一致しない: "
                f"active={sorted(row_envs)} registered={sorted(catalog)}"
            )
        for row in rows:
            registered_hash = catalog[row.env_tag].get(row.generation)
            if registered_hash is None:
                raise ActivationRecordError(
                    f"未登録 generation を active にしている: {row.env_tag!r} g{row.generation}"
                )
            if row.contract_sha256 != registered_hash:
                raise ActivationRecordError(
                    f"active contract hash が registry と不一致: {row.env_tag!r} g{row.generation}"
                )
            ever_active.add(row.contract_sha256)
        previous_hash = state_hash
        terminal_serial = serial
        terminal_hash = state_hash
    # serial は state hash の入力にも含まれるため、この比較は独立した
    # trust gate ではなく、誤った head を説明しやすくする冗長な診断である。
    if terminal_serial != expected_head_serial:
        raise ActivationRecordError(
            f"activation head serial 不一致: expected={expected_head_serial} observed={terminal_serial}"
        )
    if terminal_hash != expected_head_state_sha256:
        raise ActivationRecordError(
            "activation head state hash 不一致: "
            f"expected={expected_head_state_sha256} observed={terminal_hash}"
        )
    return ActivationState(
        activation_serial=terminal_serial,
        activation_state_sha256=terminal_hash,
        active_contracts=rows,
        ever_active_contract_sha256s=frozenset(ever_active),
    )


def _read_regular_file_no_follow(path: Path, expected_stat: os.stat_result) -> bytes:
    flags = os.O_RDONLY | getattr(os, "O_CLOEXEC", 0) | os.O_NOFOLLOW
    try:
        descriptor = os.open(path, flags)
    except OSError as exc:
        raise ActivationRecordError(f"activation record を no-follow open できない: {path.name}") from exc
    try:
        observed = os.fstat(descriptor)
        if (not stat.S_ISREG(observed.st_mode)
                or (observed.st_dev, observed.st_ino)
                != (expected_stat.st_dev, expected_stat.st_ino)):
            raise ActivationRecordError(f"activation record の inode/type が open 前後で変化した: {path.name}")
        chunks: list[bytes] = []
        while True:
            chunk = os.read(descriptor, 1024 * 1024)
            if not chunk:
                break
            chunks.append(chunk)
        return b"".join(chunks)
    except OSError as exc:
        raise ActivationRecordError(f"activation record を読めない: {path.name}") from exc
    finally:
        os.close(descriptor)


def read_activation_record_files(directory: Path) -> tuple[tuple[str, bytes], ...]:
    """Directory を symlink 非追随で読み、名前順の regular-file bytes を返す。"""
    if not isinstance(directory, Path):
        raise ActivationRecordError("activation directory は Path でなければならない")
    try:
        directory_stat = os.lstat(directory)
    except OSError as exc:
        raise ActivationRecordError("activation directory を lstat できない") from exc
    if not stat.S_ISDIR(directory_stat.st_mode):
        raise ActivationRecordError("activation directory は symlink でない directory でなければならない")
    records: list[tuple[str, bytes]] = []
    try:
        with os.scandir(directory) as scanner:
            entries = sorted(scanner, key=lambda entry: entry.name)
    except OSError as exc:
        raise ActivationRecordError("activation directory を列挙できない") from exc
    for entry in entries:
        if _RECORD_NAME_RE.fullmatch(entry.name) is None:
            raise ActivationRecordError(f"activation directory に不正な entry がある: {entry.name!r}")
        try:
            entry_stat = entry.stat(follow_symlinks=False)
        except OSError as exc:
            raise ActivationRecordError(f"activation record を lstat できない: {entry.name}") from exc
        if not stat.S_ISREG(entry_stat.st_mode):
            raise ActivationRecordError(f"activation record が symlink または regular file でない: {entry.name}")
        records.append((entry.name, _read_regular_file_no_follow(Path(entry.path), entry_stat)))
    return tuple(records)


def load_activation_state(
    directory: Path,
    *,
    registered_contracts: Mapping[str, tuple[tuple[int, str], ...]],
    expected_head_serial: int,
    expected_head_state_sha256: str,
) -> ActivationState:
    """Filesystem authority を読み、pinned head までの exact chain を返す。"""
    return validate_activation_records(
        read_activation_record_files(directory),
        registered_contracts=registered_contracts,
        expected_head_serial=expected_head_serial,
        expected_head_state_sha256=expected_head_state_sha256,
    )
