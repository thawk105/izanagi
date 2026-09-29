"""Closed counterexample shape. Validation proves shape, not counterexample truth."""
from __future__ import annotations

import json
import re
from dataclasses import asdict, dataclass, fields
from typing import Literal

SCHEMA = "cc-model-counterexample/1"
_ID = re.compile(r"[A-Za-z0-9_.:-]{1,64}\Z")
_DIGEST = re.compile(r"sha256:[0-9a-fA-F]{64}\Z")


@dataclass(frozen=True)
class CounterexampleStep:
    number: int
    thread: str
    name: str
    key: str | None
    version_id: str | None
    observed_value: None | bool | int | str


@dataclass(frozen=True)
class CycleEdge:
    source: str
    target: str
    kind: Literal["ww", "wr", "rw"]
    key: str
    from_version: str
    to_version: str


@dataclass(frozen=True)
class Counterexample:
    schema: str
    specification_digest: str
    scenario_id: str
    judgment_id: str
    steps: tuple[CounterexampleStep, ...]
    cycle_txns: tuple[str, ...] | None
    cycle_edges: tuple[CycleEdge, ...] | None
    rule_ids: tuple[str, ...]


def _mapping(value: object, cls: type, where: str) -> dict:
    if type(value) is not dict:
        raise ValueError(f"{where} must be an object")
    expected = {field.name for field in fields(cls)}
    if set(value) != expected:
        raise ValueError(f"{where} fields differ: {sorted(set(value) ^ expected)}")
    return value


def _id(value: object, where: str) -> str:
    if type(value) is not str or _ID.fullmatch(value) is None:
        raise ValueError(f"{where} must be an atomic ID")
    return value


def _optional_id(value: object, where: str) -> str | None:
    return None if value is None else _id(value, where)


def _sequence(value: object, where: str) -> list | tuple:
    if type(value) not in (list, tuple):
        raise ValueError(f"{where} must be an array")
    return value


def _observed(value: object) -> None | bool | int | str:
    if value is None or type(value) is bool:
        return value
    if type(value) is int and abs(value) <= 2**63:
        return value
    if type(value) is str and (_ID.fullmatch(value) or _DIGEST.fullmatch(value)):
        return value
    raise ValueError("observed_value must be a bounded atomic value")


def validate_counterexample(value: object) -> Counterexample:
    """Validate a closed record; this does not establish historical truth."""
    if type(value) is Counterexample:
        value = asdict(value)
    data = _mapping(value, Counterexample, "counterexample")
    if data["schema"] != SCHEMA or type(data["schema"]) is not str:
        raise ValueError("unsupported schema")
    digest = data["specification_digest"]
    if type(digest) is not str or _DIGEST.fullmatch(digest) is None:
        raise ValueError("invalid specification digest")
    scenario_id = _id(data["scenario_id"], "scenario_id")
    judgment_id = _id(data["judgment_id"], "judgment_id")
    steps = []
    for number, item in enumerate(_sequence(data["steps"], "steps"), 1):
        item = _mapping(item, CounterexampleStep, "step")
        if type(item["number"]) is not int or item["number"] != number:
            raise ValueError("step numbers must start at 1 and be consecutive")
        steps.append(CounterexampleStep(number, _id(item["thread"], "thread"),
                                        _id(item["name"], "name"),
                                        _optional_id(item["key"], "key"),
                                        _optional_id(item["version_id"], "version_id"),
                                        _observed(item["observed_value"])))
    if not steps:
        raise ValueError("steps must be nonempty")
    raw_txns, raw_edges = data["cycle_txns"], data["cycle_edges"]
    txns = None if raw_txns is None else tuple(_id(x, "cycle txn") for x in _sequence(raw_txns, "cycle_txns"))
    edges = None
    if raw_edges is not None:
        edge_list = []
        for raw in _sequence(raw_edges, "cycle_edges"):
            raw = _mapping(raw, CycleEdge, "cycle edge")
            kind = raw["kind"]
            if type(kind) is not str or kind not in ("ww", "wr", "rw"):
                raise ValueError("invalid cycle edge kind")
            edge_list.append(CycleEdge(_id(raw["source"], "source"),
                                       _id(raw["target"], "target"), kind,
                                       _id(raw["key"], "key"),
                                       _id(raw["from_version"], "from_version"),
                                       _id(raw["to_version"], "to_version")))
        edges = tuple(edge_list)
    if judgment_id == "J1":
        if txns is None or edges is None or len(txns) < 2 or len(txns) != len(edges):
            raise ValueError("J1 requires a nonempty closed cycle")
        if len(set(txns)) != len(txns):
            raise ValueError("cycle transactions must be unique")
        for index, edge in enumerate(edges):
            if edge.source != txns[index] or edge.target != txns[(index + 1) % len(txns)]:
                raise ValueError("cycle edges do not connect in order")
    elif txns is not None or edges is not None:
        raise ValueError("non-J1 judgment cannot contain a cycle")
    rule_ids = tuple(_id(x, "rule_id") for x in _sequence(data["rule_ids"], "rule_ids"))
    if len(rule_ids) != len(set(rule_ids)):
        raise ValueError("duplicate rule IDs")
    return Counterexample(SCHEMA, digest, scenario_id, judgment_id,
                          tuple(steps), txns, edges, rule_ids)


def to_json_bytes(value: Counterexample) -> bytes:
    checked = validate_counterexample(value)
    return json.dumps(asdict(checked), sort_keys=True, allow_nan=False,
                      ensure_ascii=True, separators=(",", ":")).encode("ascii")


def from_json_bytes(value: bytes) -> Counterexample:
    if type(value) is not bytes:
        raise ValueError("JSON input must be bytes")

    def unique_pairs(pairs: list[tuple[str, object]]) -> dict:
        result = {}
        for key, item in pairs:
            if key in result:
                raise ValueError(f"duplicate JSON key: {key}")
            result[key] = item
        return result

    def reject_constant(value: str) -> None:
        raise ValueError(f"invalid JSON constant: {value}")

    try:
        parsed = json.loads(value.decode("utf-8"), object_pairs_hook=unique_pairs,
                            parse_constant=reject_constant)
    except (UnicodeError, json.JSONDecodeError) as exc:
        raise ValueError("invalid JSON bytes") from exc
    return validate_counterexample(parsed)
