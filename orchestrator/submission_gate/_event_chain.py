"""最小の連番 hash-chain primitive と単位間 handoff 契約。

この module は attempt の series FSM、retry 制限、qualification lineage、親系列 ID、
anomaly 判定を実装しない。単位3 semantic validator は ``ChainEvent`` から
event index・previous hash・event hash・payload の構造的整合性だけを期待してよく、
親系列 ID の意味論や retry 判定をこの型から導出してはならない。単位5 writer は
``append_event`` が作った canonical bytes を create-only sink へ渡す境界だけを期待してよく、
sink の永続性・認可・tamper-evidence・attempt authority は別途検査する。
将来の単位4がこの primitive と durable sink を組み合わせて authority を構築する。
"""

from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
import hashlib
import json
import re
from types import MappingProxyType
from typing import Any, Final


_HASH_RE: Final = re.compile(r"[0-9a-f]{64}\Z")
_ZERO_HASH: Final = "0" * 64
_EVENT_KEYS: Final = frozenset(
    {"event_index", "previous_event_sha256", "event_type", "payload", "event_sha256"}
)


class EventChainError(ValueError):
    """hash-chain event の構造・連番・前イベント参照が不正である。"""


@dataclass(frozen=True, slots=True)
class ChainEvent:
    """hash 鎖の構造的整合性だけを表す replay 結果。意味論は保持しない。"""

    event_index: int
    previous_event_sha256: str
    event_type: str
    payload: Mapping[str, Any]
    event_sha256: str


def _canonical_json_bytes(value: object) -> bytes:
    try:
        return json.dumps(
            value,
            sort_keys=True,
            ensure_ascii=True,
            separators=(",", ":"),
            allow_nan=False,
        ).encode("utf-8")
    except (TypeError, ValueError, UnicodeError, RecursionError) as exc:
        raise EventChainError("event payload は canonical JSON にできない") from exc


def _hash_value(value: object) -> str:
    return hashlib.sha256(_canonical_json_bytes(value)).hexdigest()


def hash_event(envelope: Mapping[str, Any]) -> str:
    """event hash を envelope の ``event_sha256`` 以外の全 field から計算する。"""

    if not isinstance(envelope, Mapping):
        raise EventChainError("event envelope は Mapping でなければならない")
    unsigned = dict(envelope)
    unsigned.pop("event_sha256", None)
    return _hash_value(unsigned)


def _require_hash(value: object, label: str) -> str:
    if type(value) is not str or _HASH_RE.fullmatch(value) is None:
        raise EventChainError(f"{label} は 64 桁 lowercase hex でなければならない")
    return value


def _parse_event(value: object, expected_index: int, previous: str) -> ChainEvent:
    if not isinstance(value, Mapping) or set(value) != _EVENT_KEYS:
        raise EventChainError(f"event {expected_index} の key 集合が不正である")
    event = dict(value)
    if type(event["event_index"]) is not int or event["event_index"] != expected_index:
        raise EventChainError(f"event {expected_index} の index が欠番または重複している")
    previous_hash = _require_hash(event["previous_event_sha256"], "previous_event_sha256")
    if previous_hash != previous:
        raise EventChainError(f"event {expected_index} の previous hash が不一致である")
    event_type = event["event_type"]
    if type(event_type) is not str or not event_type or "\n" in event_type or "\x00" in event_type:
        raise EventChainError(f"event {expected_index} の event_type が不正である")
    payload = event["payload"]
    if type(payload) is not dict:
        raise EventChainError(f"event {expected_index} の payload が object でない")
    event_hash = _require_hash(event["event_sha256"], "event_sha256")
    actual_hash = hash_event(event)
    if event_hash != actual_hash:
        raise EventChainError(f"event {expected_index} の hash が不一致である")
    return ChainEvent(
        event_index=expected_index,
        previous_event_sha256=previous_hash,
        event_type=event_type,
        payload=MappingProxyType(dict(payload)),
        event_sha256=event_hash,
    )


def replay_event_chain(
    events: Sequence[Mapping[str, Any]],
) -> tuple[ChainEvent, ...]:
    """連番、previous hash、event hash を全量 replay して返す。"""

    if isinstance(events, (str, bytes, bytearray)) or not isinstance(events, Sequence):
        raise EventChainError("events は sequence でなければならない")
    previous = _ZERO_HASH
    seen: set[str] = set()
    replayed: list[ChainEvent] = []
    for index, value in enumerate(events):
        event = _parse_event(value, index, previous)
        if event.event_sha256 in seen:
            raise EventChainError("duplicate event hash がある")
        seen.add(event.event_sha256)
        replayed.append(event)
        previous = event.event_sha256
    return tuple(replayed)


def append_event(
    events: Sequence[Mapping[str, Any]],
    *,
    event_type: str,
    payload: Mapping[str, Any],
    create_only: Callable[[str, bytes], None],
) -> Mapping[str, Any]:
    """次の event を検証し、create-only sink へ渡して返す。

    ``create_only`` callable の永続性・tamper-evidence 保証は呼び手 (将来の単位4)
    の責務であり、本 primitive 自体は保証しない。
    """

    prior = replay_event_chain(events)
    if type(event_type) is not str or not event_type or "\n" in event_type or "\x00" in event_type:
        raise EventChainError("event_type が不正である")
    if not isinstance(payload, Mapping):
        raise EventChainError("payload は Mapping でなければならない")
    if not callable(create_only):
        raise EventChainError("create_only は callable でなければならない")
    event: dict[str, Any] = {
        "event_index": len(prior),
        "previous_event_sha256": prior[-1].event_sha256 if prior else _ZERO_HASH,
        "event_type": event_type,
        "payload": dict(payload),
    }
    event["event_sha256"] = hash_event(event)
    replay_event_chain([*events, event])
    encoded = _canonical_json_bytes(event) + b"\n"
    create_only(f"{len(prior):04d}.json", encoded)
    return event
