"""Independent rogue producer used by the B-4 auth comparison.

The functions here are intentionally outside the production producer module.
They parse real attempt, raw-analysis, and arm-source bytes, change one named
judgment, rebuild the raw/source digest binding, and publish concrete files.
They are not mocks and do not replace either the issuer or evaluator.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
import hashlib
import json
import os
from pathlib import Path
from typing import Any, Mapping, NoReturn, Sequence


@dataclass(frozen=True, slots=True)
class RogueProducerArtifacts:
    judgment: str
    target_arm: str
    attempt_artifact_path: Path
    attempt_artifact_bytes: bytes
    raw_analysis_path: Path
    raw_analysis_bytes: bytes
    source_artifact_paths: tuple[Path, ...]
    source_artifact_bytes: tuple[bytes, ...]


_JUDGMENTS: Mapping[str, tuple[str, bool, bool]] = {
    "P": ("protocol_ok", True, False),
    "T": ("treatment_fired", True, False),
    "C": ("contaminated", False, True),
}


def _reject_constant(token: str) -> NoReturn:
    raise ValueError(f"non-standard JSON constant: {token}")


def _pairs(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    value: dict[str, Any] = {}
    for key, item in pairs:
        if key in value:
            raise ValueError(f"duplicate JSON key: {key}")
        value[key] = item
    return value


def _strict_json(data: bytes) -> Any:
    try:
        return json.loads(
            data.decode("utf-8"),
            object_pairs_hook=_pairs,
            parse_float=Decimal,
            parse_constant=_reject_constant,
        )
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValueError("rogue input is not strict UTF-8 JSON") from exc


def _canonical_json_bytes(value: object) -> bytes:
    def encode(item: object) -> str:
        if item is None:
            return "null"
        if type(item) is bool:
            return "true" if item else "false"
        if type(item) is int:
            return str(item)
        if isinstance(item, Decimal):
            if not item.is_finite():
                raise ValueError("non-finite decimal is not JSON")
            return str(item)
        if type(item) is str:
            return json.dumps(item, ensure_ascii=False)
        if isinstance(item, (list, tuple)):
            return "[" + ",".join(encode(child) for child in item) + "]"
        if isinstance(item, dict):
            if any(type(key) is not str for key in item):
                raise ValueError("JSON object key is not an exact string")
            return "{" + ",".join(
                json.dumps(key, ensure_ascii=False) + ":" + encode(item[key])
                for key in sorted(item)
            ) + "}"
        raise ValueError(f"unsupported JSON type: {type(item).__name__}")

    return encode(value).encode("utf-8")


def _on_arm_source(value: object, *, container: str) -> dict[str, Any]:
    if type(value) is not dict:
        raise ValueError(f"{container} is not an object")
    sources = value.get("arm_sources")
    if type(sources) is not list:
        raise ValueError(f"{container} arm_sources is not a list")
    matching = [
        source
        for source in sources
        if type(source) is dict
        and type(source.get("identity")) is dict
        and source["identity"].get("arm") == "on"
    ]
    if len(matching) != 1:
        raise ValueError(f"{container} does not have exactly one on-arm source")
    return matching[0]


def _change_raw_judgment(
    raw: object,
    *,
    judgment: str,
    container: str,
    old_bytes: bytes,
    new_bytes: bytes,
) -> None:
    if judgment not in _JUDGMENTS:
        raise ValueError("judgment must be one of P, T, or C")
    if type(raw) is not dict:
        raise ValueError(f"{container} raw judgment is not an object")
    field, old_value, new_value = _JUDGMENTS[judgment]
    projection = {
        name: raw.get(name)
        for name in ("contaminated", "protocol_ok", "treatment_fired")
    }
    projection_bytes = _canonical_json_bytes(projection)
    if projection_bytes.count(old_bytes) != 1 or old_bytes == new_bytes:
        raise ValueError(
            f"{container} preregistered old bytes do not occur exactly once"
        )
    changed_bytes = projection_bytes.replace(old_bytes, new_bytes, 1)
    changed = _strict_json(changed_bytes)
    if (
        type(changed) is not dict
        or set(changed) != set(projection)
        or raw.get(field) is not old_value
        or changed.get(field) is not new_value
        or any(
            changed[name] is not projection[name]
            for name in projection
            if name != field
        )
    ):
        raise ValueError(f"{container} exact replacement changed the wrong field")
    raw.update(changed)


def _mutated_attempt(
    data: bytes,
    judgment: str,
    old_bytes: bytes,
    new_bytes: bytes,
) -> bytes:
    value = _strict_json(data)
    source = _on_arm_source(value, container="attempt artifact")
    _change_raw_judgment(
        source.get("raw"),
        judgment=judgment,
        container="attempt artifact on arm",
        old_bytes=old_bytes,
        new_bytes=new_bytes,
    )
    return _canonical_json_bytes(value)


def _mutated_sources(
    source_artifact_bytes: Sequence[bytes],
    judgment: str,
    old_bytes: bytes,
    new_bytes: bytes,
) -> tuple[tuple[bytes, ...], int]:
    decoded = [_strict_json(data) for data in source_artifact_bytes]
    matching = [
        index
        for index, source in enumerate(decoded)
        if type(source) is dict
        and type(source.get("identity")) is dict
        and source["identity"].get("arm") == "on"
    ]
    if not matching:
        raise ValueError("source artifacts contain no on arm")
    index = matching[0]
    source = decoded[index]
    _change_raw_judgment(
        source.get("raw"),
        judgment=judgment,
        container="source artifact on arm",
        old_bytes=old_bytes,
        new_bytes=new_bytes,
    )
    encoded = tuple(_canonical_json_bytes(item) for item in decoded)
    return encoded, index


def _mutated_raw_analysis(
    data: bytes,
    *,
    judgment: str,
    source_index: int,
    source_bytes: bytes,
    old_bytes: bytes,
    new_bytes: bytes,
    rewrite_source_binding: bool,
) -> bytes:
    value = _strict_json(data)
    if type(value) is not dict or type(value.get("blocks")) is not list:
        raise ValueError("raw analysis blocks are absent")
    blocks = value["blocks"]
    if not blocks or type(blocks[0]) is not dict:
        raise ValueError("raw analysis has no first block")
    arms = blocks[0].get("arms")
    if type(arms) is not list:
        raise ValueError("raw analysis first block arms are absent")
    matching = [
        arm for arm in arms if type(arm) is dict and arm.get("arm") == "on"
    ]
    if len(matching) != 1:
        raise ValueError("raw analysis first block has no unique on arm")
    raw_arm = matching[0]
    _change_raw_judgment(
        raw_arm,
        judgment=judgment,
        container="raw analysis first on arm",
        old_bytes=old_bytes,
        new_bytes=new_bytes,
    )
    if source_index != 0:
        raise ValueError(
            "first on-arm raw record is not aligned with source artifact index 0"
        )
    if rewrite_source_binding:
        raw_arm["source_artifact_sha256"] = hashlib.sha256(source_bytes).hexdigest()
    return _canonical_json_bytes(value)


def _write_exclusive(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    try:
        view = memoryview(data)
        while view:
            written = os.write(fd, view)
            if written <= 0:
                raise OSError("short write")
            view = view[written:]
        os.fsync(fd)
    finally:
        os.close(fd)


def install_rogue_planned_attempt(
    artifacts: RogueProducerArtifacts,
    *,
    planned_attempt_path: Path,
) -> None:
    """Have this separate producer replace the real planned attempt artifact."""

    if not isinstance(planned_attempt_path, Path) or not planned_attempt_path.is_absolute():
        raise ValueError("planned_attempt_path must be an absolute Path")
    if not planned_attempt_path.is_file() or planned_attempt_path.is_symlink():
        raise ValueError("planned attempt target must be an existing regular file")
    planned_attempt_path.write_bytes(artifacts.attempt_artifact_bytes)
    if planned_attempt_path.read_bytes() != artifacts.attempt_artifact_bytes:
        raise OSError("rogue planned attempt write did not remain visible")


def produce_rogue_artifacts(
    *,
    judgment: str,
    attempt_artifact_bytes: bytes,
    raw_analysis_bytes: bytes,
    source_artifact_bytes: Sequence[bytes],
    output_root: Path,
    old_bytes: bytes,
    new_bytes: bytes,
    rewrite_source_binding: bool = True,
) -> RogueProducerArtifacts:
    """Publish concrete P, T, or C rogue outputs from this separate module."""

    if not isinstance(output_root, Path) or not output_root.is_absolute():
        raise ValueError("output_root must be an absolute Path")
    mutated_attempt = _mutated_attempt(
        attempt_artifact_bytes, judgment, old_bytes, new_bytes
    )
    mutated_sources, source_index = _mutated_sources(
        source_artifact_bytes, judgment, old_bytes, new_bytes
    )
    mutated_raw = _mutated_raw_analysis(
        raw_analysis_bytes,
        judgment=judgment,
        source_index=source_index,
        source_bytes=mutated_sources[source_index],
        old_bytes=old_bytes,
        new_bytes=new_bytes,
        rewrite_source_binding=rewrite_source_binding,
    )

    attempt_path = output_root / f"rogue-attempt-{judgment}.json"
    raw_path = output_root / f"rogue-raw-analysis-{judgment}.json"
    source_paths = tuple(
        output_root / "sources" / f"source-{index:03d}.json"
        for index in range(len(mutated_sources))
    )
    _write_exclusive(attempt_path, mutated_attempt)
    _write_exclusive(raw_path, mutated_raw)
    for path, data in zip(source_paths, mutated_sources):
        _write_exclusive(path, data)

    return RogueProducerArtifacts(
        judgment=judgment,
        target_arm="on",
        attempt_artifact_path=attempt_path,
        attempt_artifact_bytes=mutated_attempt,
        raw_analysis_path=raw_path,
        raw_analysis_bytes=mutated_raw,
        source_artifact_paths=source_paths,
        source_artifact_bytes=mutated_sources,
    )


__all__ = [
    "RogueProducerArtifacts",
    "install_rogue_planned_attempt",
    "produce_rogue_artifacts",
]
