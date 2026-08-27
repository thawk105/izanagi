"""``codex exec --json`` の露出 event stream を fail-closed で検証する。

自然言語の成功自己申告は証拠に数えない。成功には、単一の non-empty thread ID、
正常終了した単一 turn、JSONLへ露出するcommand/file/MCP/web/未知itemの不在、
role/digest echoを含むschema適合agent messageがすべて必要である。

Codex 0.144.2のResponses developer ``additional_tools``や残存builtin（特に
``view_image``）は呼出しがJSONLへ現れないため、このvalidatorはそれらの不使用証明
ではない。raw surfaceはResponses wire attestationで検出し、存在する限りlive roleを
BLOCKEDにする。outer bubblewrapはdefense-in-depthのfilesystem封じ込めである。
"""
from __future__ import annotations

import hashlib
import json
import math
import re
import unicodedata
import uuid
from dataclasses import dataclass
from typing import Any, Iterable, Mapping

try:
    import jsonschema
except ModuleNotFoundError:  # pragma: no cover - runtime では fail-closed にする
    jsonschema = None


MAX_JSONL_BYTES = 8 * 1024 * 1024
MAX_JSONL_LINE_BYTES = 2 * 1024 * 1024
MAX_RESULT_JSON_BYTES = 2 * 1024 * 1024
MAX_JSON_DEPTH = 128

_DIGEST_RE = re.compile(r"^[0-9a-f]{64}$")
_ROLE_RE = re.compile(r"^[a-z0-9][a-z0-9-]{0,63}$")
_ALLOWED_EVENT_TYPES = frozenset({
    "thread.started",
    "turn.started",
    "item.started",
    "item.updated",
    "item.completed",
    "turn.completed",
})
_ALLOWED_ITEM_TYPES = frozenset({"reasoning", "agent_message"})

# Codex CLI stdout のうち worker metering が correctness 証拠として消費する
# event type。stdout 専用 parser と worker consumer は必ずこの同じ集合を参照する。
STDOUT_CONSUMED_EVENT_TYPES = frozenset({"thread.started", "turn.completed"})


class EventValidationError(ValueError):
    """runtime evidence が成功条件を満たさない。"""


@dataclass(frozen=True)
class RunIdentity:
    """launcher が選択した role と、実行に束縛する不変 digest。"""

    role: str
    adapter_digest: str
    instruction_digest: str
    input_digest: str

    def __post_init__(self) -> None:
        if not _ROLE_RE.fullmatch(self.role):
            raise EventValidationError(f"不正な role 名: {self.role!r}")
        for name in ("adapter_digest", "instruction_digest", "input_digest"):
            value = getattr(self, name)
            if not _DIGEST_RE.fullmatch(value):
                raise EventValidationError(f"{name} は lowercase SHA-256 でなければならない")

    def echo(self) -> dict[str, str]:
        return {
            "role": self.role,
            "adapter_digest": self.adapter_digest,
            "instruction_digest": self.instruction_digest,
            "input_digest": self.input_digest,
        }


@dataclass(frozen=True)
class ValidatedEventStream:
    """検証済みの runtime evidence と構造化 role 出力。"""

    thread_id: str
    result: Any
    envelope: Mapping[str, Any]
    events: tuple[Mapping[str, Any], ...]
    event_digest: str


@dataclass(frozen=True)
class ParsedJsonlWithIssues:
    """stdout 専用入口が返す非 issue event と許容済み物理行番号。"""

    events: tuple[Mapping[str, Any], ...]
    duplicate_key_lines: tuple[int, ...]


@dataclass(frozen=True)
class _ObjectPairs:
    """重複と上書き前の値を失わない JSON object の中間表現。"""

    pairs: tuple[tuple[str, Any], ...]


def canonical_json(value: Any) -> str:
    """digest と prompt の双方で使う一意な JSON 表現。"""

    _validate_json_domain(value, label="canonical JSON")
    try:
        return json.dumps(
            value,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        )
    except (TypeError, ValueError, OverflowError, RecursionError) as exc:
        raise EventValidationError(f"canonical JSON serialize失敗: {exc}") from exc


def sha256_json(value: Any) -> str:
    return hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()


def enveloped_output_schema(result_schema: Mapping[str, Any],
                            identity: RunIdentity) -> dict[str, Any]:
    """Responses APIへ渡す固定strict transport schemaを返す。

    role固有schemaはAPI strict subsetより表現力が広い場合があるためwireへ直接
    渡さない。modelはlogical resultを``result_json``へ二重encodeし、trusted側が
    strict parseしてからrole schemaを検証する。
    """

    if not isinstance(result_schema, Mapping):
        raise EventValidationError("role output_schema は JSON object でなければならない")
    schema = {
        "type": "object",
        "additionalProperties": False,
        "required": ["runtime", "result_json"],
        "properties": {
            "runtime": {
                "type": "object",
                "additionalProperties": False,
                "required": list(identity.echo()),
                "properties": {
                    key: {"type": "string", "enum": [value]}
                    for key, value in identity.echo().items()
                },
            },
            "result_json": {"type": "string"},
        },
    }
    _check_schema(schema)
    return schema


def _check_schema(schema: Mapping[str, Any]) -> None:
    if jsonschema is None:
        raise EventValidationError(
            "jsonschema package が無いため output schema を検証できない (fail-closed)"
        )
    try:
        jsonschema.Draft7Validator.check_schema(schema)
    except Exception as exc:  # jsonschema の版により例外型が異なる
        raise EventValidationError(f"不正な output schema: {exc}") from exc


def _validate_schema(value: Any, schema: Mapping[str, Any]) -> None:
    _check_schema(schema)
    try:
        jsonschema.Draft7Validator(schema).validate(value)
    except Exception as exc:
        raise EventValidationError(f"agent output が schema に不適合: {exc}") from exc


def validate_schema_instance(value: Any, schema: Mapping[str, Any], *,
                             label: str = "JSON") -> None:
    """外部入力を同じDraft 7 validatorで検証する公開helper。"""

    try:
        _validate_json_domain(value, label=label)
        _validate_schema(value, schema)
    except EventValidationError as exc:
        raise EventValidationError(f"{label} schema検証失敗: {exc}") from exc


def _decode_jsonl(raw: bytes | str, *, max_bytes: int) -> tuple[str, bytes]:
    if isinstance(raw, str):
        try:
            encoded = raw.encode("utf-8", errors="strict")
        except UnicodeEncodeError as exc:
            raise EventValidationError(f"JSONL がUTF-8へencodeできない: {exc}") from exc
        text = raw
    else:
        encoded = raw
        try:
            text = raw.decode("utf-8", errors="strict")
        except UnicodeDecodeError as exc:
            raise EventValidationError(f"JSONL が UTF-8 でない: {exc}") from exc
    if not encoded:
        raise EventValidationError("JSONL event が空")
    if len(encoded) > max_bytes:
        raise EventValidationError(
            f"JSONL が上限を超過 ({len(encoded)} > {max_bytes} bytes)"
        )
    if encoded.startswith(b"\xef\xbb\xbf") or text.startswith("\ufeff"):
        raise EventValidationError("JSONL の UTF-8 BOM は禁止")
    if "\x00" in text:
        raise EventValidationError("JSONL の NUL byte は禁止")
    if "\r" in text:
        raise EventValidationError("JSONL の改行は LF のみ")
    if unicodedata.normalize("NFC", text) != text:
        raise EventValidationError("JSONL は Unicode NFC でなければならない")
    return text, encoded


def _pairs_without_duplicates(pairs: Iterable[tuple[str, Any]]) -> dict[str, Any]:
    value: dict[str, Any] = {}
    for key, item in pairs:
        if key in value:
            raise EventValidationError(f"JSON key が重複: {key!r}")
        value[key] = item
    return value


def _preserve_object_pairs(pairs: Iterable[tuple[str, Any]]) -> _ObjectPairs:
    return _ObjectPairs(tuple(pairs))


def _reject_constant(value: str) -> None:
    raise EventValidationError(f"JSONの非有限数は禁止: {value}")


def _parse_finite_float(value: str) -> float:
    try:
        parsed = float(value)
    except (ValueError, OverflowError) as exc:
        raise EventValidationError(f"JSON number parse失敗: {value!r}") from exc
    if not math.isfinite(parsed):
        raise EventValidationError(f"JSONの非有限数は禁止: {value}")
    return parsed


def _validate_json_domain(value: Any, *, label: str) -> None:
    """library入力を含むJSON値を有限・有界深さのdomainへ閉じる。"""

    stack: list[tuple[Any, int]] = [(value, 0)]
    while stack:
        item, depth = stack.pop()
        if depth > MAX_JSON_DEPTH:
            raise EventValidationError(
                f"{label} のnestingが上限を超過 (max={MAX_JSON_DEPTH})"
            )
        if item is None or isinstance(item, bool):
            continue
        if isinstance(item, str):
            try:
                item.encode("utf-8", errors="strict")
            except UnicodeEncodeError as exc:
                raise EventValidationError(
                    f"{label} にUTF-8化できない文字列がある"
                ) from exc
            if unicodedata.normalize("NFC", item) != item:
                raise EventValidationError(f"{label} の文字列がUnicode NFCでない")
            continue
        if isinstance(item, int):
            continue
        if isinstance(item, float):
            if not math.isfinite(item):
                raise EventValidationError(f"{label} の非有限数は禁止")
            continue
        if isinstance(item, list):
            stack.extend((child, depth + 1) for child in item)
            continue
        if isinstance(item, dict):
            for key, child in item.items():
                if not isinstance(key, str):
                    raise EventValidationError(f"{label} のobject keyが文字列でない")
                try:
                    key.encode("utf-8", errors="strict")
                except UnicodeEncodeError as exc:
                    raise EventValidationError(
                        f"{label} にUTF-8化できないobject keyがある"
                    ) from exc
                if unicodedata.normalize("NFC", key) != key:
                    raise EventValidationError(f"{label} のobject keyがUnicode NFCでない")
                stack.append((child, depth + 1))
            continue
        raise EventValidationError(
            f"{label} にJSON domain外の型がある: {type(item).__name__}"
        )


def _validate_preserved_json_domain(value: Any, *, label: str) -> None:
    """上書き前の全 object pair を既存 JSON domain と同じ条件で検査する。"""

    stack: list[tuple[Any, int]] = [(value, 0)]
    while stack:
        item, depth = stack.pop()
        if depth > MAX_JSON_DEPTH:
            raise EventValidationError(
                f"{label} のnestingが上限を超過 (max={MAX_JSON_DEPTH})"
            )
        if item is None or isinstance(item, bool):
            continue
        if isinstance(item, str):
            try:
                item.encode("utf-8", errors="strict")
            except UnicodeEncodeError as exc:
                raise EventValidationError(
                    f"{label} にUTF-8化できない文字列がある"
                ) from exc
            if unicodedata.normalize("NFC", item) != item:
                raise EventValidationError(f"{label} の文字列がUnicode NFCでない")
            continue
        if isinstance(item, int):
            continue
        if isinstance(item, float):
            if not math.isfinite(item):
                raise EventValidationError(f"{label} の非有限数は禁止")
            continue
        if isinstance(item, list):
            stack.extend((child, depth + 1) for child in item)
            continue
        if isinstance(item, _ObjectPairs):
            for key, child in item.pairs:
                if not isinstance(key, str):
                    raise EventValidationError(f"{label} のobject keyが文字列でない")
                try:
                    key.encode("utf-8", errors="strict")
                except UnicodeEncodeError as exc:
                    raise EventValidationError(
                        f"{label} にUTF-8化できないobject keyがある"
                    ) from exc
                if unicodedata.normalize("NFC", key) != key:
                    raise EventValidationError(
                        f"{label} のobject keyがUnicode NFCでない"
                    )
                stack.append((child, depth + 1))
            continue
        raise EventValidationError(
            f"{label} にJSON domain外の型がある: {type(item).__name__}"
        )


def _normalize_preserved_json(value: Any) -> Any:
    if isinstance(value, list):
        return [_normalize_preserved_json(item) for item in value]
    if isinstance(value, _ObjectPairs):
        normalized: dict[str, Any] = {}
        for key, item in value.pairs:
            normalized[key] = _normalize_preserved_json(item)
        return normalized
    return value


def _object_has_duplicate_key(value: Any) -> bool:
    stack = [value]
    while stack:
        item = stack.pop()
        if isinstance(item, list):
            stack.extend(item)
        elif isinstance(item, _ObjectPairs):
            keys = [key for key, _child in item.pairs]
            if len(keys) != len(set(keys)):
                return True
            stack.extend(child for _key, child in item.pairs)
    return False


def strict_json_loads(text: str, *, label: str,
                      max_bytes: int = MAX_RESULT_JSON_BYTES) -> Any:
    """duplicate key/BOM/NUL/CR/non-NFC/非有限数を拒否するJSON parser。"""

    if not isinstance(text, str):
        raise EventValidationError(f"{label} は文字列でなければならない")
    try:
        encoded = text.encode("utf-8", errors="strict")
    except UnicodeEncodeError as exc:
        raise EventValidationError(f"{label} がUTF-8へencodeできない: {exc}") from exc
    if not encoded or len(encoded) > max_bytes:
        raise EventValidationError(
            f"{label} のsize不正 ({len(encoded)} bytes, max={max_bytes})"
        )
    if encoded.startswith(b"\xef\xbb\xbf") or text.startswith("\ufeff"):
        raise EventValidationError(f"{label} のBOMは禁止")
    if "\x00" in text:
        raise EventValidationError(f"{label} のNULは禁止")
    if "\r" in text:
        raise EventValidationError(f"{label} のCRは禁止")
    if unicodedata.normalize("NFC", text) != text:
        raise EventValidationError(f"{label} はUnicode NFCでなければならない")
    try:
        value = json.loads(
            text,
            object_pairs_hook=_pairs_without_duplicates,
            parse_constant=_reject_constant,
            parse_float=_parse_finite_float,
        )
    except EventValidationError:
        raise
    except (json.JSONDecodeError, ValueError, OverflowError, RecursionError) as exc:
        raise EventValidationError(f"{label} のJSON parse失敗: {exc}") from exc
    _validate_json_domain(value, label=label)
    return value


def parse_jsonl(raw: bytes | str, *, max_bytes: int = MAX_JSONL_BYTES,
                max_line_bytes: int = MAX_JSONL_LINE_BYTES) -> tuple[Mapping[str, Any], ...]:
    """stdout 全行を JSON object として読み、非JSON混入を拒否する。"""

    text, _ = _decode_jsonl(raw, max_bytes=max_bytes)
    events: list[Mapping[str, Any]] = []
    for lineno, line in enumerate(text.split("\n"), 1):
        if not line.strip():
            continue
        if len(line.encode("utf-8")) > max_line_bytes:
            raise EventValidationError(f"JSONL:{lineno}: 1行の上限を超過")
        try:
            event = strict_json_loads(
                line, label=f"JSONL:{lineno}", max_bytes=max_line_bytes
            )
        except EventValidationError as exc:
            raise EventValidationError(f"JSONL:{lineno}: {exc}") from exc
        if not isinstance(event, dict):
            raise EventValidationError(f"JSONL:{lineno}: event は object でなければならない")
        events.append(event)
    if not events:
        raise EventValidationError("JSONL に event object がない")
    return tuple(events)


def parse_jsonl_allowing_duplicate_keys(
    raw: bytes | str,
    *,
    max_bytes: int = MAX_JSONL_BYTES,
    max_line_bytes: int = MAX_JSONL_LINE_BYTES,
) -> ParsedJsonlWithIssues:
    """Codex CLI stdout の安全な nested duplicate だけを issue として除外する。

    厳格入口は変更せず、この名前を明示した caller だけが opt-in する。重複行は
    correctness 証拠へ一切渡さず、その物理行番号だけを返す。
    """

    text, _ = _decode_jsonl(raw, max_bytes=max_bytes)
    events: list[Mapping[str, Any]] = []
    duplicate_key_lines: list[int] = []
    for lineno, line in enumerate(text.split("\n"), 1):
        if not line.strip():
            continue
        if len(line.encode("utf-8")) > max_line_bytes:
            raise EventValidationError(f"JSONL:{lineno}: 1行の上限を超過")
        label = f"JSONL:{lineno}"
        try:
            preserved = json.loads(
                line,
                object_pairs_hook=_preserve_object_pairs,
                parse_constant=_reject_constant,
                parse_float=_parse_finite_float,
            )
        except EventValidationError:
            raise
        except (
            json.JSONDecodeError,
            ValueError,
            OverflowError,
            RecursionError,
        ) as exc:
            raise EventValidationError(f"{label} のJSON parse失敗: {exc}") from exc

        # T3: last-wins で失われる値を含む元 tree 全体を先に検査する。
        _validate_preserved_json_domain(preserved, label=label)
        if not isinstance(preserved, _ObjectPairs):
            raise EventValidationError(
                f"{label}: event は object でなければならない"
            )
        has_duplicate = _object_has_duplicate_key(preserved)
        if not has_duplicate:
            event = _normalize_preserved_json(preserved)
            if not isinstance(event, dict):  # pragma: no cover - 上の型検査に従う
                raise EventValidationError(
                    f"{label}: event は object でなければならない"
                )
            events.append(event)
            continue

        top_keys = [key for key, _item in preserved.pairs]
        # T1: top-level duplicate は semantic projection を曖昧にするため拒否する。
        if len(top_keys) != len(set(top_keys)):
            raise EventValidationError(f"{label}: top-level JSON key が重複")
        event = _normalize_preserved_json(preserved)
        # T2: worker が読む event は issue-bearing 行から証拠を採らない。
        event_type = event.get("type")
        if (
            isinstance(event_type, str)
            and event_type in STDOUT_CONSUMED_EVENT_TYPES
        ):
            raise EventValidationError(
                f"{label}: 消費対象 event の nested JSON key が重複"
            )
        # T4 は decode、行長、parse、domain、object 検査を全て通過したこの位置で
        # 初めて成立する。許容行は events へ加えず、評価から完全に除外する。
        duplicate_key_lines.append(lineno)
    if not events and not duplicate_key_lines:
        raise EventValidationError("JSONL に event object がない")
    return ParsedJsonlWithIssues(
        events=tuple(events), duplicate_key_lines=tuple(duplicate_key_lines)
    )


def _valid_thread_id(value: Any) -> str:
    if not isinstance(value, str) or not value:
        raise EventValidationError("thread.started に non-empty thread_id がない")
    try:
        parsed = uuid.UUID(value)
    except (ValueError, AttributeError) as exc:
        raise EventValidationError(f"thread_id が UUID でない: {value!r}") from exc
    if str(parsed) != value:
        raise EventValidationError(f"thread_id が canonical UUID でない: {value!r}")
    return value


def _agent_text(item: Mapping[str, Any]) -> str:
    text = item.get("text")
    if not isinstance(text, str) or not text:
        raise EventValidationError("completed agent_message に非空 text がない")
    return text


def validate_event_stream(raw: bytes | str, identity: RunIdentity,
                          result_schema: Mapping[str, Any], *,
                          max_bytes: int = MAX_JSONL_BYTES) -> ValidatedEventStream:
    """Codex JSONLを検査し、唯一の構造化role出力を返す。"""

    events = parse_jsonl(raw, max_bytes=max_bytes)
    thread_ids: list[str] = []
    turn_started = 0
    turn_completed = 0
    completed_seen = False
    agent_messages: list[str] = []

    for index, event in enumerate(events):
        etype = event.get("type")
        if etype not in _ALLOWED_EVENT_TYPES:
            raise EventValidationError(
                f"event[{index}] の type {etype!r} は許可外。error/failed/tool/未知eventは成功にしない"
            )
        if completed_seen:
            raise EventValidationError("turn.completed 後に event が続いている")
        if etype == "thread.started":
            thread_ids.append(_valid_thread_id(event.get("thread_id")))
            if index != 0:
                raise EventValidationError("thread.started は先頭 event でなければならない")
        elif etype == "turn.started":
            if not thread_ids:
                raise EventValidationError("thread.started より前に turn.started がある")
            turn_started += 1
        elif etype in {"item.started", "item.updated", "item.completed"}:
            if turn_started != 1 or turn_completed:
                raise EventValidationError("active turn 外の item event")
            item = event.get("item")
            if not isinstance(item, dict):
                raise EventValidationError(f"event[{index}] に item object がない")
            item_type = item.get("type")
            if item_type not in _ALLOWED_ITEM_TYPES:
                raise EventValidationError(
                    f"item type {item_type!r} は許可外。command/file/MCP/web/plan/未知toolは拒否"
                )
            if etype == "item.completed" and item_type == "agent_message":
                agent_messages.append(_agent_text(item))
        elif etype == "turn.completed":
            turn_completed += 1
            completed_seen = True

    if len(thread_ids) != 1:
        raise EventValidationError(f"thread.started は正確に1件必要 (observed={len(thread_ids)})")
    if turn_started != 1 or turn_completed != 1:
        raise EventValidationError(
            f"turn.started/completed は各1件必要 (started={turn_started}, completed={turn_completed})"
        )
    if len(agent_messages) != 1:
        raise EventValidationError(
            f"completed agent_message は正確に1件必要 (observed={len(agent_messages)})"
        )
    try:
        envelope = strict_json_loads(
            agent_messages[0], label="最終 agent_message", max_bytes=MAX_RESULT_JSON_BYTES
        )
    except EventValidationError as exc:
        raise EventValidationError(
            "最終 agent_message がJSONでない。自然言語の成功自己申告は証拠にしない"
        ) from exc
    schema = enveloped_output_schema(result_schema, identity)
    _validate_schema(envelope, schema)
    result = strict_json_loads(
        envelope["result_json"], label="result_json", max_bytes=MAX_RESULT_JSON_BYTES
    )
    _validate_schema(result, result_schema)

    _, encoded = _decode_jsonl(raw, max_bytes=max_bytes)
    return ValidatedEventStream(
        thread_id=thread_ids[0],
        result=result,
        envelope=envelope,
        events=events,
        event_digest=hashlib.sha256(encoded).hexdigest(),
    )


def encode_jsonl(events: Iterable[Mapping[str, Any]]) -> bytes:
    """テストfixture用のcanonical JSONL encoder。"""

    return ("".join(canonical_json(event) + "\n" for event in events)).encode("utf-8")
