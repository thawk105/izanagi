# -*- coding: utf-8 -*-
"""Issue and resolve the authoritative P3 B-4 floor artifact.

The issuer accepts one pinned producer schema, rederives every recorded gain
and upper with the producer's binary64 operation order, and preserves the
accepted ``candidate_floor`` exactly as a :class:`fractions.Fraction`.

It does not infer a missing identity component, adopt a floor on the caller's
behalf, edit the preregistration, or prove that the measurement design was
frozen before its results were observed.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import re
import stat
import sys
import tempfile
from dataclasses import dataclass
from fractions import Fraction
from pathlib import Path
from typing import Final, Sequence

if __package__ in {None, ""}:  # pragma: no cover - direct CLI execution
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
    __package__ = "orchestrator.campaign"

from . import floor_pair_driver
from .genome import protocol_from_floor_genome


B4_FLOOR_ARTIFACT_SCHEMA_VERSION: Final[str] = (
    "p3-b4-authoritative-floor/v1"
)
B4_FLOOR_AGGREGATE_ARTIFACT_SCHEMA_VERSION: Final[str] = (
    "p3-b4-authoritative-floor/v2"
)
AGGREGATE_MAXIMUM_ID: Final[str] = "exact-fraction-max/v1"
AGGREGATE_NON_GUARANTEES: Final[tuple[str, ...]] = (
    "期待 spec 列が結果を見る前に選ばれたこと、§5 の対象集合との意味的一致、"
    "1 campaign・1 セルあたり n = 62 と 24 時間以上の分離は機械検査しない。",
    "loader の期待 spec 列は成果物内の記録であり、期待列と source を共に変更して"
    "外側 pin も再計算した場合の採用責任は §5 pin の確認者に残る。",
    "平坦な非保証一覧は各入力の原文の転記である。spec と summary の再読込は"
    "raw window の測定内容や選択時系列を証明しない。",
)
ACCEPTED_FLOOR_PAIR_SUMMARY_SCHEMA_VERSION: Final[str] = (
    "floor-pair-summary/v3"
)
FLOOR_PAIR_SUMMARY_FORMAT: Final[str] = "floor-pair-summary-json/v1"
GENERATOR_IDENTITY: Final[str] = (
    "orchestrator/campaign/p3_b4_floor_artifact_issuer.py"
)

BINARY64_INTERMEDIATE_ROUNDING_LIMITATION: Final[str] = (
    "binary64 の中間丸めにより、記録された float D が同じ入力の exact D より小さいことがある。"
)
FREEZE_TIMING_NOT_PROVEN: Final[str] = (
    "凍結が測定の結果を見る前に行われたことを証明しない。"
)
SOURCE_SUMMARY_REFERENCES_NOT_VERIFIED: Final[str] = (
    "source summary の参照先を実在照合していない"
)
NON_GUARANTEES: Final[tuple[str, ...]] = (
    BINARY64_INTERMEDIATE_ROUNDING_LIMITATION,
    FREEZE_TIMING_NOT_PROVEN,
    SOURCE_SUMMARY_REFERENCES_NOT_VERIFIED,
)

PREREGISTRATION_FLOOR_LABEL: Final[str] = (
    "floor (対象動作点で再実測した between-run floor) の artifact パスと hash"
)
PREREGISTRATION_ABSENT_SENTINEL: Final[str] = "未記入"

_HEX40_RE = re.compile(r"[0-9a-f]{40}")
_HEX64_RE = re.compile(r"[0-9a-f]{64}")
_ID_RE = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]{0,127}")
_FLOOR_PIN_RE = re.compile(
    r"artifact_path=(?P<path>[^;]+); sha256=(?P<sha256>[0-9a-f]{64})"
)
_SUMMARY_TOP_KEYS = {
    "schema",
    "format",
    "spec_relpath",
    "spec_sha256",
    "loaded_head",
    "plan_sha256",
    "generated_at",
    "status",
    "upper",
    "candidate_floor",
    "statistics",
    "window_artifacts",
    "campaigns",
    "dropped_sample_count",
    "dropped_record_count",
    "dropped",
    "derivation",
    "proof_limitations",
}


class B4FloorArtifactError(ValueError):
    """A floor input, artifact, binding, or preregistration pin is invalid."""

    def __init__(self, code: str, detail: str):
        super().__init__(f"{code}: {detail}")
        self.code = code
        self.detail = detail


class B4FloorIdentityError(B4FloorArtifactError):
    """The summary-bound spec cannot supply the complete five-part identity."""

    def __init__(self, missing_elements: Sequence[str], detail: str):
        missing = tuple(sorted(set(missing_elements)))
        super().__init__("identity_missing", f"{', '.join(missing)}: {detail}")
        self.missing_elements = missing


@dataclass(frozen=True)
class B4FloorArtifactIdentity:
    """The five filename identity components derived without caller input."""

    env_tag: str
    protocol: str
    threads: int
    workload_identifier: str
    campaign_identifier: str


@dataclass(frozen=True)
class B4ValidatedFloorPairSummary:
    """A self-consistent summary plus its summary-bound identity derivation."""

    summary_path: str
    summary_sha256: str
    candidate_floor: float
    floor_exact: Fraction
    source_float_hex: str
    spec_relpath: str
    spec_sha256: str
    loaded_head: str
    plan_sha256: str
    campaign_ids: tuple[str, ...]
    workload_values: tuple[tuple[tuple[str, str], ...], ...]
    proof_limitations: tuple[str, ...]
    identity: B4FloorArtifactIdentity | None
    missing_identity_elements: tuple[str, ...]


@dataclass(frozen=True)
class B4AuthoritativeFloor:
    """An immutable authoritative floor returned by the artifact loader."""

    floor: Fraction
    artifact_path: str
    artifact_sha256: str
    schema_version: str
    generator_identity: str
    source_float_hex: str
    source_summary_path: str
    source_summary_sha256: str
    identity: B4FloorArtifactIdentity
    non_guarantees: tuple[str, ...]


@dataclass(frozen=True)
class B4AuthoritativeFloorWrite:
    """The repository-relative create-only output and its content digest."""

    artifact_path: str
    artifact_sha256: str


def _fail(code: str, detail: str) -> None:
    raise B4FloorArtifactError(code, detail)


def _canonical_json_bytes(value: object) -> bytes:
    try:
        return (
            json.dumps(
                value,
                sort_keys=True,
                separators=(",", ":"),
                ensure_ascii=False,
                allow_nan=False,
            )
            + "\n"
        ).encode("utf-8")
    except (TypeError, ValueError) as exc:
        raise B4FloorArtifactError(
            "canonical_json_error", f"canonical JSON に変換できない: {exc}"
        ) from exc


def _load_json_bytes(
    raw: bytes,
    *,
    label: str,
    require_canonical: bool,
) -> object:
    def reject_duplicate(pairs: list[tuple[str, object]]) -> dict[str, object]:
        result: dict[str, object] = {}
        for key, value in pairs:
            if key in result:
                _fail("json_duplicate_key", f"{label}: duplicate key {key!r}")
            result[key] = value
        return result

    def reject_constant(token: str) -> None:
        _fail("json_nonfinite", f"{label}: non-finite constant {token}")

    try:
        value = json.loads(
            raw,
            object_pairs_hook=reject_duplicate,
            parse_constant=reject_constant,
        )
    except B4FloorArtifactError:
        raise
    except (json.JSONDecodeError, UnicodeError) as exc:
        raise B4FloorArtifactError(
            "json_parse_error", f"{label}: JSON を parse できない: {exc}"
        ) from exc
    _reject_nonfinite(value, label=label)
    if require_canonical and _canonical_json_bytes(value) != raw:
        _fail("json_noncanonical", f"{label}: canonical JSON bytes でない")
    return value


def _reject_nonfinite(value: object, *, label: str) -> None:
    if type(value) is float and not math.isfinite(value):
        _fail("json_nonfinite", f"{label}: non-finite float がある")
    if type(value) is list:
        for child in value:
            _reject_nonfinite(child, label=label)
    elif type(value) is dict:
        for child in value.values():
            _reject_nonfinite(child, label=label)


def _exact_object(
    value: object,
    expected: set[str],
    *,
    label: str,
) -> dict[str, object]:
    if type(value) is not dict:
        _fail("schema_error", f"{label} は exact object でなければならない")
    actual = set(value)
    if actual != expected:
        _fail(
            "schema_error",
            f"{label} key 不一致: missing={sorted(expected - actual)}, "
            f"unknown={sorted(actual - expected)}",
        )
    return value


def _exact_list(value: object, *, label: str, allow_empty: bool) -> list[object]:
    if type(value) is not list:
        _fail("schema_error", f"{label} は exact array でなければならない")
    if not allow_empty and not value:
        _fail("schema_error", f"{label} は空であってはならない")
    return value


def _text(value: object, *, label: str, allow_empty: bool = False) -> str:
    if type(value) is not str or (not allow_empty and value == ""):
        _fail("schema_error", f"{label} は exact string でなければならない")
    return value


def _identifier(value: object, *, label: str) -> str:
    text = _text(value, label=label)
    if _ID_RE.fullmatch(text) is None:
        _fail("schema_error", f"{label} は canonical ID でなければならない")
    return text


def _sha256(value: object, *, label: str) -> str:
    text = _text(value, label=label)
    if _HEX64_RE.fullmatch(text) is None:
        _fail("schema_error", f"{label} は 64 桁 lowercase SHA-256 でない")
    return text


def _nonnegative_int(value: object, *, label: str) -> int:
    if type(value) is not int or value < 0:
        _fail("schema_error", f"{label} は exact non-negative int でない")
    return value


def _positive_int(value: object, *, label: str) -> int:
    result = _nonnegative_int(value, label=label)
    if result == 0:
        _fail("schema_error", f"{label} は positive でなければならない")
    return result


def _float(
    value: object,
    *,
    label: str,
    nonnegative: bool = False,
    reject_negative_zero: bool = False,
) -> float:
    if type(value) is not float or not math.isfinite(value):
        _fail("schema_error", f"{label} は exact finite float でなければならない")
    if nonnegative and value < 0.0:
        _fail("schema_error", f"{label} は non-negative でなければならない")
    if (
        reject_negative_zero
        and value == 0.0
        and math.copysign(1.0, value) < 0
    ):
        _fail("schema_error", f"{label} は negative zero であってはならない")
    return value


def _same_float(left: float, right: float) -> bool:
    return left == right and math.copysign(1.0, left) == math.copysign(1.0, right)


def _relative_path(value: object, *, label: str) -> str:
    text = _text(value, label=label)
    path = Path(text)
    if path.is_absolute() or text != path.as_posix():
        _fail("path_error", f"{label} は canonical repository-relative path でない")
    if not path.parts or any(part in {"", ".", ".."} for part in path.parts):
        _fail("path_error", f"{label} は dot/parent component を含められない")
    return text


def _repo_root(repo_root: Path) -> Path:
    if not isinstance(repo_root, Path):
        _fail("path_error", "repo_root は Path でなければならない")
    try:
        root = repo_root.resolve(strict=True)
    except OSError as exc:
        raise B4FloorArtifactError(
            "path_error", f"repo_root を解決できない: {exc}"
        ) from exc
    if not root.is_dir():
        _fail("path_error", "repo_root は directory でなければならない")
    return root


def _argument_relpath(root: Path, path: Path, *, label: str) -> str:
    if not isinstance(path, Path):
        _fail("path_error", f"{label} は Path でなければならない")
    lexical = path if path.is_absolute() else root / path
    try:
        relative = lexical.relative_to(root)
    except ValueError as exc:
        raise B4FloorArtifactError(
            "path_error", f"{label} が repo_root 外にある"
        ) from exc
    return _relative_path(relative.as_posix(), label=label)


def _assert_no_symlink(root: Path, relpath: str, *, label: str) -> Path:
    target = root / relpath
    cursor = root
    for part in Path(relpath).parts:
        cursor = cursor / part
        try:
            mode = cursor.lstat().st_mode
        except OSError as exc:
            raise B4FloorArtifactError(
                "path_error", f"{label} が存在しない: {cursor}: {exc}"
            ) from exc
        if stat.S_ISLNK(mode):
            _fail("path_error", f"{label} に symlink component がある: {cursor}")
    return target


def _read_regular(root: Path, relpath: str, *, label: str) -> bytes:
    target = _assert_no_symlink(root, relpath, label=label)
    try:
        mode = target.lstat().st_mode
    except OSError as exc:
        raise B4FloorArtifactError(
            "path_error", f"{label} を lstat できない: {exc}"
        ) from exc
    if not stat.S_ISREG(mode):
        _fail("path_error", f"{label} は regular file でなければならない")
    try:
        return target.read_bytes()
    except OSError as exc:
        raise B4FloorArtifactError(
            "path_error", f"{label} を読めない: {exc}"
        ) from exc


def _validate_window_artifacts(value: object) -> None:
    rows = _exact_list(value, label="summary.window_artifacts", allow_empty=False)
    for index, item in enumerate(rows):
        label = f"summary.window_artifacts[{index}]"
        row = _exact_object(
            item,
            {"window_id", "campaign_id", "artifact_relpath", "artifact_sha256"},
            label=label,
        )
        _identifier(row["window_id"], label=f"{label}.window_id")
        _identifier(row["campaign_id"], label=f"{label}.campaign_id")
        _relative_path(row["artifact_relpath"], label=f"{label}.artifact_relpath")
        _sha256(row["artifact_sha256"], label=f"{label}.artifact_sha256")


def _fraction_wire(value: object, *, label: str) -> Fraction:
    obj = _exact_object(value, {"numerator", "denominator"}, label=label)
    numerator = _nonnegative_int(obj["numerator"], label=f"{label}.numerator")
    denominator = _positive_int(obj["denominator"], label=f"{label}.denominator")
    return Fraction(numerator, denominator)


def _validate_campaigns(value: object) -> tuple[str, ...]:
    rows = _exact_list(value, label="summary.campaigns", allow_empty=False)
    campaign_ids: list[str] = []
    for index, item in enumerate(rows):
        label = f"summary.campaigns[{index}]"
        row = _exact_object(
            item,
            {
                "window_id",
                "campaign_id",
                "planned_sample_count",
                "dropped_sample_count",
                "dropped_fraction",
                "threshold",
                "admissible",
                "strata",
            },
            label=label,
        )
        _identifier(row["window_id"], label=f"{label}.window_id")
        campaign_ids.append(
            _identifier(row["campaign_id"], label=f"{label}.campaign_id")
        )
        _positive_int(
            row["planned_sample_count"], label=f"{label}.planned_sample_count"
        )
        _nonnegative_int(
            row["dropped_sample_count"], label=f"{label}.dropped_sample_count"
        )
        _fraction_wire(row["dropped_fraction"], label=f"{label}.dropped_fraction")
        _text(row["threshold"], label=f"{label}.threshold")
        if type(row["admissible"]) is not bool:
            _fail("schema_error", f"{label}.admissible は exact bool でない")
        strata = _exact_list(row["strata"], label=f"{label}.strata", allow_empty=False)
        for stratum_index, stratum_value in enumerate(strata):
            stratum_label = f"{label}.strata[{stratum_index}]"
            stratum = _exact_object(
                stratum_value,
                {
                    "window_id",
                    "pair_id",
                    "planned_sample_count",
                    "dropped_sample_count",
                    "retained_sample_count",
                },
                label=stratum_label,
            )
            _identifier(stratum["window_id"], label=f"{stratum_label}.window_id")
            _identifier(stratum["pair_id"], label=f"{stratum_label}.pair_id")
            for field in (
                "planned_sample_count",
                "dropped_sample_count",
                "retained_sample_count",
            ):
                _nonnegative_int(stratum[field], label=f"{stratum_label}.{field}")
    if len(campaign_ids) != len(set(campaign_ids)):
        _fail("schema_error", "summary.campaigns campaign_id が重複している")
    return tuple(campaign_ids)


def _validate_dropped(value: object) -> None:
    rows = _exact_list(value, label="summary.dropped", allow_empty=True)
    fields = {
        "window_id",
        "pair_id",
        "sample_index",
        "side_id",
        "status",
        "error",
        "dropped_by_session_id",
    }
    for index, item in enumerate(rows):
        label = f"summary.dropped[{index}]"
        row = _exact_object(item, fields, label=label)
        _identifier(row["window_id"], label=f"{label}.window_id")
        _identifier(row["pair_id"], label=f"{label}.pair_id")
        _nonnegative_int(row["sample_index"], label=f"{label}.sample_index")
        _identifier(row["side_id"], label=f"{label}.side_id")
        _identifier(row["status"], label=f"{label}.status")
        for field in ("error", "dropped_by_session_id"):
            if row[field] is not None:
                _text(row[field], label=f"{label}.{field}")


def _rederive_summary(value: object) -> float:
    derivations = _exact_list(value, label="summary.derivation", allow_empty=False)
    if len(derivations) != 1:
        _fail("self_inconsistency", "summary.derivation は exact 1 item でない")
    derivation = _exact_object(
        derivations[0], {"samples", "strata"}, label="summary.derivation[0]"
    )
    samples = _exact_list(
        derivation["samples"], label="summary.derivation[0].samples", allow_empty=False
    )
    values_by_stratum: dict[tuple[str, str], list[float]] = {}
    seen_samples: set[tuple[str, str, int]] = set()
    for index, item in enumerate(samples):
        label = f"summary.derivation[0].samples[{index}]"
        sample = _exact_object(
            item,
            {
                "window_id",
                "pair_id",
                "sample_index",
                "session_medians",
                "gain_1",
                "gain_2",
                "difference",
            },
            label=label,
        )
        window_id = _identifier(sample["window_id"], label=f"{label}.window_id")
        pair_id = _identifier(sample["pair_id"], label=f"{label}.pair_id")
        sample_index = _nonnegative_int(
            sample["sample_index"], label=f"{label}.sample_index"
        )
        sample_key = (window_id, pair_id, sample_index)
        if sample_key in seen_samples:
            _fail("self_inconsistency", f"duplicate derived sample: {sample_key}")
        seen_samples.add(sample_key)
        medians = _exact_object(
            sample["session_medians"],
            {"candidate_1", "candidate_2"},
            label=f"{label}.session_medians",
        )
        side_1 = _exact_object(
            medians["candidate_1"],
            {"candidate", "reference"},
            label=f"{label}.session_medians.candidate_1",
        )
        side_2 = _exact_object(
            medians["candidate_2"],
            {"candidate", "reference"},
            label=f"{label}.session_medians.candidate_2",
        )
        candidate_1 = _float(
            side_1["candidate"],
            label=f"{label}.session_medians.candidate_1.candidate",
            nonnegative=True,
        )
        candidate_2 = _float(
            side_2["candidate"],
            label=f"{label}.session_medians.candidate_2.candidate",
            nonnegative=True,
        )
        reference_1 = _float(
            side_1["reference"],
            label=f"{label}.session_medians.candidate_1.reference",
            nonnegative=True,
        )
        reference_2 = _float(
            side_2["reference"],
            label=f"{label}.session_medians.candidate_2.reference",
            nonnegative=True,
        )
        if reference_1 <= 0.0:
            _fail(
                "schema_error",
                f"{label}.session_medians.candidate_1.reference は positive でない",
            )
        if reference_2 <= 0.0:
            _fail(
                "schema_error",
                f"{label}.session_medians.candidate_2.reference は positive でない",
            )

        # Keep this operation order identical to floor_pair_driver.compute_gain_difference.
        gain_1 = candidate_1 / reference_1 - 1.0
        gain_2 = candidate_2 / reference_2 - 1.0
        difference = abs(gain_1 - gain_2)
        if not all(math.isfinite(item) for item in (gain_1, gain_2, difference)):
            _fail("self_inconsistency", f"{label} の再導出値が finite でない")
        recorded_gain_1 = _float(
            sample["gain_1"],
            label=f"{label}.gain_1",
            reject_negative_zero=True,
        )
        recorded_gain_2 = _float(
            sample["gain_2"],
            label=f"{label}.gain_2",
            reject_negative_zero=True,
        )
        recorded_difference = _float(
            sample["difference"],
            label=f"{label}.difference",
            nonnegative=True,
            reject_negative_zero=True,
        )
        if not _same_float(recorded_gain_1, gain_1):
            _fail("self_inconsistency", f"{label}.gain_1 が再導出値と不一致")
        if not _same_float(recorded_gain_2, gain_2):
            _fail("self_inconsistency", f"{label}.gain_2 が再導出値と不一致")
        if not _same_float(recorded_difference, difference):
            _fail("self_inconsistency", f"{label}.difference が再導出値と不一致")
        values_by_stratum.setdefault((window_id, pair_id), []).append(difference)

    strata = _exact_list(
        derivation["strata"], label="summary.derivation[0].strata", allow_empty=False
    )
    seen_strata: set[tuple[str, str]] = set()
    stratum_uppers: list[float] = []
    for index, item in enumerate(strata):
        label = f"summary.derivation[0].strata[{index}]"
        stratum = _exact_object(
            item,
            {"window_id", "pair_id", "values", "upper_function", "upper"},
            label=label,
        )
        key = (
            _identifier(stratum["window_id"], label=f"{label}.window_id"),
            _identifier(stratum["pair_id"], label=f"{label}.pair_id"),
        )
        if key in seen_strata:
            _fail("self_inconsistency", f"duplicate derived stratum: {key}")
        seen_strata.add(key)
        recorded_values_raw = _exact_list(
            stratum["values"], label=f"{label}.values", allow_empty=False
        )
        recorded_values = [
            _float(
                value,
                label=f"{label}.values[{value_index}]",
                nonnegative=True,
                reject_negative_zero=True,
            )
            for value_index, value in enumerate(recorded_values_raw)
        ]
        rederived_values = values_by_stratum.get(key)
        if (
            rederived_values is None
            or len(recorded_values) != len(rederived_values)
            or any(
                not _same_float(recorded, rederived)
                for recorded, rederived in zip(recorded_values, rederived_values)
            )
        ):
            _fail("self_inconsistency", f"{label}.values が sample 再導出値と不一致")
        if stratum["upper_function"] != "sample_max/v1":
            _fail("schema_error", f"{label}.upper_function が未対応")
        recorded_upper = _float(
            stratum["upper"],
            label=f"{label}.upper",
            nonnegative=True,
            reject_negative_zero=True,
        )
        rederived_upper = max(recorded_values)
        if not _same_float(recorded_upper, rederived_upper):
            _fail("self_inconsistency", f"{label}.upper が層内 max と不一致")
        stratum_uppers.append(rederived_upper)
    if seen_strata != set(values_by_stratum):
        _fail("self_inconsistency", "sample strata と recorded strata が exact 一致しない")
    return max(stratum_uppers)


def _validate_summary_document(
    value: object,
) -> tuple[dict[str, object], float, tuple[str, ...], tuple[str, ...]]:
    summary = _exact_object(value, _SUMMARY_TOP_KEYS, label="floor-pair summary")
    if summary["schema"] != ACCEPTED_FLOOR_PAIR_SUMMARY_SCHEMA_VERSION:
        _fail(
            "summary_schema_error",
            "summary.schema は pinned "
            f"{ACCEPTED_FLOOR_PAIR_SUMMARY_SCHEMA_VERSION!r} でなければならない",
        )
    if summary["format"] != FLOOR_PAIR_SUMMARY_FORMAT:
        _fail("summary_schema_error", "summary.format が未対応")
    if summary["status"] != "generated":
        _fail("summary_status_error", "summary.status は 'generated' でなければならない")
    _relative_path(summary["spec_relpath"], label="summary.spec_relpath")
    _sha256(summary["spec_sha256"], label="summary.spec_sha256")
    loaded_head = _text(summary["loaded_head"], label="summary.loaded_head")
    if _HEX40_RE.fullmatch(loaded_head) is None:
        _fail("schema_error", "summary.loaded_head は 40 桁 lowercase hex でない")
    _sha256(summary["plan_sha256"], label="summary.plan_sha256")
    _text(summary["generated_at"], label="summary.generated_at")
    _validate_window_artifacts(summary["window_artifacts"])
    campaign_ids = _validate_campaigns(summary["campaigns"])
    _nonnegative_int(
        summary["dropped_sample_count"], label="summary.dropped_sample_count"
    )
    _nonnegative_int(
        summary["dropped_record_count"], label="summary.dropped_record_count"
    )
    _validate_dropped(summary["dropped"])
    proof = _exact_object(
        summary["proof_limitations"], {"section", "items"}, label="summary.proof_limitations"
    )
    _text(proof["section"], label="summary.proof_limitations.section")
    proof_items = tuple(
        _text(item, label=f"summary.proof_limitations.items[{index}]")
        for index, item in enumerate(
            _exact_list(
                proof["items"],
                label="summary.proof_limitations.items",
                allow_empty=True,
            )
        )
    )

    # type(...) is float is deliberate: bool compares equal to 0.0 in Python.
    upper = _float(
        summary["upper"],
        label="summary.upper",
        nonnegative=True,
        reject_negative_zero=True,
    )
    candidate_floor = _float(
        summary["candidate_floor"],
        label="summary.candidate_floor",
        nonnegative=True,
        reject_negative_zero=True,
    )
    rederived_upper = _rederive_summary(summary["derivation"])
    if not _same_float(upper, rederived_upper):
        _fail("self_inconsistency", "summary.upper が層間 max の再導出値と不一致")
    if not _same_float(candidate_floor, upper):
        _fail("self_inconsistency", "summary.candidate_floor が summary.upper と不一致")
    return summary, candidate_floor, campaign_ids, proof_items


def _aggregate_identifier(prefix: str, value: object) -> str:
    digest = hashlib.sha256(_canonical_json_bytes(value)).hexdigest()[:20]
    return f"{prefix}-{digest}"


def _derive_identity(
    root: Path,
    spec: floor_pair_driver.FloorPairSpec,
    campaign_ids: tuple[str, ...],
) -> tuple[
    B4FloorArtifactIdentity | None,
    tuple[str, ...],
    tuple[tuple[tuple[str, str], ...], ...],
]:
    """Derive identity after producer validation has fixed its other parts.

    ``floor_pair_driver.py:759-776, 1136-1147`` guarantees nonempty cells with
    calibration-consistent threads/workloads.  The issuer summary validator at
    ``p3_b4_floor_artifact_issuer.py:411-433`` guarantees nonempty campaigns.
    Only receipt-derived protocol can therefore remain missing here.
    Protocol is the protocol part of each accepted build receipt's canonical
    genome; this does not recheck the protocol in the CCBench source.
    """
    missing: list[str] = []
    env_tag = spec.environment.env_tag

    threads_values = {cell.perf_config.threads for cell in spec.cells}
    workloads = {cell.perf_config.workload for cell in spec.cells}

    protocols: set[str] = set()
    protocol_failed = False
    for artifact in spec.artifacts:
        reference = artifact.build_receipt
        try:
            receipt_path = reference.path
            receipt_sha = reference.sha256
            raw = _read_regular(root, receipt_path, label=f"build receipt {receipt_path}")
            if hashlib.sha256(raw).hexdigest() != receipt_sha:
                protocol_failed = True
                continue
            record = _load_json_bytes(
                raw, label=f"build receipt {receipt_path}", require_canonical=False
            )
            if type(record) is not dict or "binding" not in record:
                protocol_failed = True
                continue
            binding = record["binding"]
            if type(binding) is not dict or "genome_canonical" not in binding:
                protocol_failed = True
                continue
            protocol = protocol_from_floor_genome(binding["genome_canonical"])
            protocols.add(
                _identifier(
                    protocol,
                    label=(
                        f"build receipt {receipt_path}.binding.genome_canonical"
                    ),
                )
            )
        except (ValueError, B4FloorArtifactError):
            protocol_failed = True
    if protocol_failed or len(protocols) != 1:
        missing.append("protocol")

    missing_tuple = tuple(sorted(set(missing)))
    workload_values = tuple(sorted(workloads))
    if missing_tuple:
        return None, missing_tuple, workload_values
    workload_wire = [dict(items) for items in workload_values]
    workload_identifier = _aggregate_identifier("set", workload_wire)
    campaign_identifier = (
        campaign_ids[0]
        if len(campaign_ids) == 1
        else _aggregate_identifier("set", list(campaign_ids))
    )
    identity = B4FloorArtifactIdentity(
        env_tag=env_tag,
        protocol=next(iter(protocols)),
        threads=next(iter(threads_values)),
        workload_identifier=workload_identifier,
        campaign_identifier=campaign_identifier,
    )
    return identity, (), workload_values


def _exact_floor(candidate_floor: float) -> Fraction:
    if type(candidate_floor) is not float or not math.isfinite(candidate_floor):
        _fail("floor_domain_error", "candidate_floor は exact finite float でない")
    if candidate_floor == 0.0 and math.copysign(1.0, candidate_floor) < 0:
        _fail("floor_domain_error", "candidate_floor は negative zero であってはならない")
    floor_exact = Fraction(*candidate_floor.as_integer_ratio())
    if not (Fraction(0, 1) <= floor_exact < Fraction(1, 1)):
        _fail("floor_domain_error", "candidate_floor は exact 0 <= floor < 1 でない")
    return floor_exact


def load_floor_pair_summary(
    *,
    repo_root: Path,
    summary_path: Path,
) -> B4ValidatedFloorPairSummary:
    """Load a v3 summary, rederive its float values, and derive its identity.

    Protocol comes from each accepted build receipt's binding genome.  A
    non-canonical or mixed receipt protocol is returned as a missing identity
    component without erasing producer acceptance of the summary itself;
    artifact issuance remains fail-closed on that missing component.
    """

    root = _repo_root(repo_root)
    summary_relpath = _argument_relpath(root, summary_path, label="summary_path")
    raw = _read_regular(root, summary_relpath, label="floor-pair summary")
    value = _load_json_bytes(raw, label="floor-pair summary", require_canonical=True)
    summary, candidate_floor, campaign_ids, proof_limitations = (
        _validate_summary_document(value)
    )
    spec_relpath = _relative_path(summary["spec_relpath"], label="summary.spec_relpath")
    spec_raw = _read_regular(root, spec_relpath, label="summary-bound spec")
    spec_sha256 = _sha256(summary["spec_sha256"], label="summary.spec_sha256")
    observed_spec_sha256 = hashlib.sha256(spec_raw).hexdigest()
    if observed_spec_sha256 != spec_sha256:
        _fail(
            "spec_hash_mismatch",
            f"expected={spec_sha256}, observed={observed_spec_sha256}",
        )
    try:
        spec = floor_pair_driver.load_frozen_spec(
            Path(spec_relpath),
            spec_sha256,
            repo_root=root,
        )
    except (
        floor_pair_driver.FloorPairSpecError,
        floor_pair_driver.FloorPairBindingError,
    ) as exc:
        raise B4FloorArtifactError(
            "spec_rejected_by_producer",
            f"summary-bound spec を floor_pair_driver.load_frozen_spec が拒否: {exc}",
        ) from exc
    identity, missing, workloads = _derive_identity(root, spec, campaign_ids)
    floor_exact = _exact_floor(candidate_floor)
    return B4ValidatedFloorPairSummary(
        summary_path=summary_relpath,
        summary_sha256=hashlib.sha256(raw).hexdigest(),
        candidate_floor=candidate_floor,
        floor_exact=floor_exact,
        source_float_hex=candidate_floor.hex(),
        spec_relpath=spec_relpath,
        spec_sha256=spec_sha256,
        loaded_head=_text(summary["loaded_head"], label="summary.loaded_head"),
        plan_sha256=_sha256(summary["plan_sha256"], label="summary.plan_sha256"),
        campaign_ids=campaign_ids,
        workload_values=workloads,
        proof_limitations=proof_limitations,
        identity=identity,
        missing_identity_elements=missing,
    )


def _identity_value(identity: B4FloorArtifactIdentity) -> dict[str, object]:
    return {
        "env_tag": identity.env_tag,
        "protocol": identity.protocol,
        "threads": identity.threads,
        "workload_identifier": identity.workload_identifier,
        "campaign_identifier": identity.campaign_identifier,
    }


def _authority_value(summary: B4ValidatedFloorPairSummary) -> dict[str, object]:
    if summary.identity is None or summary.missing_identity_elements:
        raise B4FloorIdentityError(
            summary.missing_identity_elements,
            "summary-bound spec/receipt から全 identity 要素を導出できない",
        )
    return {
        "schema": B4_FLOOR_ARTIFACT_SCHEMA_VERSION,
        "generator_identity": GENERATOR_IDENTITY,
        "floor_exact": [summary.floor_exact.numerator, summary.floor_exact.denominator],
        "source_float_hex": summary.source_float_hex,
        "artifact_identity": _identity_value(summary.identity),
        "identity_derivation": {
            "workloads": [dict(items) for items in summary.workload_values],
            "campaign_ids": list(summary.campaign_ids),
        },
        "source_summary": {
            "artifact_path": summary.summary_path,
            "artifact_sha256": summary.summary_sha256,
            "schema": ACCEPTED_FLOOR_PAIR_SUMMARY_SCHEMA_VERSION,
            "status": "generated",
            "spec_relpath": summary.spec_relpath,
            "spec_sha256": summary.spec_sha256,
            "loaded_head": summary.loaded_head,
            "plan_sha256": summary.plan_sha256,
        },
        "non_guarantees": [*NON_GUARANTEES, *summary.proof_limitations],
    }


def _artifact_filename(identity: B4FloorArtifactIdentity) -> str:
    return (
        f"b4-floor__env-{identity.env_tag}"
        f"__protocol-{identity.protocol}"
        f"__threads-{identity.threads}"
        f"__workload-{identity.workload_identifier}"
        f"__campaign-{identity.campaign_identifier}.json"
    )


def _publish_create_only(path: Path, raw: bytes) -> None:
    parent = path.parent
    try:
        parent_mode = parent.lstat().st_mode
    except OSError as exc:
        raise B4FloorArtifactError(
            "publish_error", f"artifact parent を lstat できない: {exc}"
        ) from exc
    if not stat.S_ISDIR(parent_mode) or stat.S_ISLNK(parent_mode):
        _fail("publish_error", "artifact parent は non-symlink directory でない")
    descriptor: int | None = None
    temporary_name: str | None = None
    try:
        descriptor, temporary_name = tempfile.mkstemp(
            prefix=".b4-floor-stage-", dir=parent
        )
        os.fchmod(descriptor, 0o600)
        offset = 0
        while offset < len(raw):
            written = os.write(descriptor, raw[offset:])
            if written <= 0:
                _fail("publish_error", "artifact staging write が進行しない")
            offset += written
        os.fsync(descriptor)
        os.close(descriptor)
        descriptor = None
        try:
            os.link(temporary_name, path, follow_symlinks=False)
        except FileExistsError as exc:
            raise B4FloorArtifactError(
                "artifact_exists", f"create-only target が既に存在する: {path.name}"
            ) from exc
        directory_descriptor = os.open(parent, os.O_RDONLY | os.O_DIRECTORY)
        try:
            os.fsync(directory_descriptor)
        finally:
            os.close(directory_descriptor)
    except B4FloorArtifactError:
        raise
    except OSError as exc:
        raise B4FloorArtifactError(
            "publish_error", f"create-only publish に失敗: {exc}"
        ) from exc
    finally:
        if descriptor is not None:
            os.close(descriptor)
        if temporary_name is not None:
            try:
                os.unlink(temporary_name)
            except FileNotFoundError:
                pass


def issue_authoritative_floor(
    *,
    repo_root: Path,
    summary_path: Path,
) -> B4AuthoritativeFloorWrite:
    """Validate one summary and create its deterministic authority JSON once."""

    root = _repo_root(repo_root)
    summary = load_floor_pair_summary(repo_root=root, summary_path=summary_path)
    value = _authority_value(summary)
    filename = _artifact_filename(summary.identity)
    artifact_relpath = (Path(summary.summary_path).parent / filename).as_posix()
    _relative_path(artifact_relpath, label="authority artifact path")
    parent_relpath = Path(artifact_relpath).parent.as_posix()
    if parent_relpath != ".":
        _assert_no_symlink(root, parent_relpath, label="authority artifact parent")
    raw = _canonical_json_bytes(value)
    _publish_create_only(root / artifact_relpath, raw)
    return B4AuthoritativeFloorWrite(
        artifact_path=artifact_relpath,
        artifact_sha256=hashlib.sha256(raw).hexdigest(),
    )



def _load_expected_specs(
    root: Path, expected_specs: Sequence[tuple[str, str]],
) -> dict[tuple[str, str], floor_pair_driver.FloorPairSpec]:
    if not isinstance(expected_specs, Sequence) or isinstance(expected_specs, (str, bytes)):
        _fail("aggregate_expected_specs_error", "expected_specs must be a nonempty sequence")
    if not expected_specs:
        _fail("aggregate_expected_specs_error", "expected_specs must not be empty")
    pins: list[tuple[str, str]] = []
    for item in expected_specs:
        if type(item) not in (tuple, list) or len(item) != 2:
            _fail("aggregate_expected_specs_error", "expected spec must be a path/hash pair")
        pins.append((
            _relative_path(item[0], label="expected spec path"),
            _sha256(item[1], label="expected spec sha256"),
        ))
    if len({path for path, _ in pins}) != len(pins):
        _fail("aggregate_expected_specs_error", "duplicate expected spec path")
    result = {}
    for path, digest in sorted(pins):
        raw = _read_regular(root, path, label="expected spec")
        if hashlib.sha256(raw).hexdigest() != digest:
            _fail("spec_hash_mismatch", f"expected spec: {path}")
        try:
            spec = floor_pair_driver.load_frozen_spec(Path(path), digest, repo_root=root)
        except (floor_pair_driver.FloorPairSpecError,
                floor_pair_driver.FloorPairBindingError) as exc:
            raise B4FloorArtifactError("spec_rejected_by_producer", str(exc)) from exc
        if len(spec.windows) != 2:
            _fail("aggregate_window_count_error", f"{path}: exactly two windows required")
        result[(path, digest)] = spec
    return result


def _validate_aggregate_summary_coverage(
    spec: floor_pair_driver.FloorPairSpec,
    summary: B4ValidatedFloorPairSummary,
    document: dict[str, object],
) -> None:
    """Compare spec expectations with summary observations, in separate units."""
    if summary.summary_path != spec.outputs.summary_relpath:
        _fail("aggregate_summary_path_error", "summary path differs from spec output")
    windows = {w.window_id: w for w in spec.windows}
    artifacts = document["window_artifacts"]
    observed = [(r["window_id"], r["campaign_id"], r["artifact_relpath"]) for r in artifacts]
    expected = {(w.window_id, w.campaign_id, w.artifact_relpath) for w in spec.windows}
    if len(observed) != len(expected) or set(observed) != expected:
        _fail("aggregate_window_binding_error", "window artifact closure differs from spec")
    campaigns = document["campaigns"]
    observed_campaigns = [(r["window_id"], r["campaign_id"]) for r in campaigns]
    if (len(observed_campaigns) != len(windows)
            or set(observed_campaigns) != {(w.window_id, w.campaign_id) for w in spec.windows}):
        _fail("aggregate_campaign_binding_error", "campaign closure differs from spec")
    derivation = document["derivation"][0]
    closed = set(spec.statistics.closed_strata)
    strata = [(r["window_id"], r["pair_id"]) for r in derivation["strata"]]
    if len(strata) != len(closed) or set(strata) != closed:
        _fail("aggregate_strata_error", "derived strata differ from spec closed_strata")
    pairs = {p.pair_id: p for p in spec.pairs}
    cells = {c.cell_id for c in spec.cells}
    for window in spec.windows:
        observed_cells = {pairs[pair].cell_id for wid, pair in strata if wid == window.window_id}
        if observed_cells != cells:
            _fail("aggregate_cell_coverage_error", f"{window.window_id}: cells not covered")
    planned = {
        (w.window_id, pair, index)
        for w in spec.windows for pair in w.pair_ids for index in range(w.sample_count)
    }
    retained = {(r["window_id"], r["pair_id"], r["sample_index"])
                for r in derivation["samples"]}
    # dropped contains record rows; two sides can refer to the same sample.
    dropped = {(r["window_id"], r["pair_id"], r["sample_index"])
               for r in document["dropped"]}
    if retained & dropped or retained | dropped != planned:
        _fail("aggregate_sample_partition_error", "retained/dropped must partition planned samples")
    if (document["dropped_sample_count"] != len(dropped)
            or document["dropped_record_count"] != len(document["dropped"])):
        _fail("aggregate_sample_count_error", "summary sample/record counts differ")
    for campaign in campaigns:
        wid = campaign["window_id"]
        window = windows[wid]
        projection = {key for key in closed if key[0] == wid}
        rows = campaign["strata"]
        keys = [(r["window_id"], r["pair_id"]) for r in rows]
        if len(keys) != len(projection) or set(keys) != projection:
            _fail("aggregate_strata_error", f"{wid}: campaign strata differ from window projection")
        planned_count = window.sample_count * len(window.pair_ids)
        dropped_count = sum(key[0] == wid for key in dropped)
        if (campaign["planned_sample_count"] != planned_count
                or campaign["dropped_sample_count"] != dropped_count):
            _fail("aggregate_sample_count_error", f"{wid}: campaign counts differ")
        for row in rows:
            key = (wid, row["pair_id"])
            drop_count = sum(item[:2] == key for item in dropped)
            retain_count = sum(item[:2] == key for item in retained)
            if (row["planned_sample_count"] != window.sample_count
                    or row["dropped_sample_count"] != drop_count
                    or row["retained_sample_count"] != retain_count):
                _fail("aggregate_sample_count_error", f"{key}: stratum counts differ")
        if (_fraction_wire(campaign["dropped_fraction"], label="campaign.dropped_fraction")
                != Fraction(dropped_count, planned_count)
                or campaign["threshold"] != "1/20"
                or campaign["admissible"] is not True
                or dropped_count * 20 > planned_count):
            _fail("aggregate_drop_policy_error", f"{wid}: campaign drop policy differs")
    expected_statistics = {
        "reference_measurements_per_pair_sample": spec.statistics.reference_measurements_per_pair_sample,
        "difference_formula": spec.statistics.difference_formula,
    }
    if _canonical_json_bytes(document["statistics"]) != _canonical_json_bytes(expected_statistics):
        _fail("aggregate_statistics_error", "summary statistics differ from spec")


def _aggregate_authority_value(
    root: Path, summary_paths: Sequence[Path], expected_specs: Sequence[tuple[str, str]],
) -> dict[str, object]:
    specs = _load_expected_specs(root, expected_specs)
    if not isinstance(summary_paths, Sequence) or isinstance(summary_paths, (str, bytes)) or not summary_paths:
        _fail("aggregate_summary_set_error", "summary_paths must be a nonempty sequence")
    paths = [_argument_relpath(root, p, label="aggregate summary") for p in summary_paths]
    if len(set(paths)) != len(paths):
        _fail("aggregate_summary_set_error", "duplicate summary path")
    sources = []
    seen_specs: set[tuple[str, str]] = set()
    for path in paths:
        summary = load_floor_pair_summary(repo_root=root, summary_path=Path(path))
        pin = (summary.spec_relpath, summary.spec_sha256)
        if pin not in specs or pin in seen_specs:
            _fail("aggregate_spec_closure_error", "unexpected or duplicate summary-bound spec")
        seen_specs.add(pin)
        raw = _read_regular(root, path, label="aggregate summary")
        if hashlib.sha256(raw).hexdigest() != summary.summary_sha256:
            _fail("aggregate_source_hash_error", "summary changed during validation")
        document = _load_json_bytes(raw, label="aggregate summary", require_canonical=True)
        _validate_aggregate_summary_coverage(specs[pin], summary, document)
        single = _authority_value(summary)
        sources.append((summary, document, single))
    if seen_specs != set(specs):
        _fail("aggregate_spec_closure_error", "expected spec has no summary")
    return _compose_aggregate_authority(sources, tuple(specs))


def _compose_aggregate_authority(
    sources: Sequence[tuple[B4ValidatedFloorPairSummary, dict[str, object], dict[str, object]]],
    expected_specs: Sequence[tuple[str, str]],
) -> dict[str, object]:
    sources = sorted(sources, key=lambda item: (
        item[0].spec_relpath, item[0].spec_sha256,
        item[0].summary_path, item[0].summary_sha256,
    ))
    identities = {(s.identity.env_tag, s.identity.protocol, s.identity.threads) for s, _, _ in sources}
    if len(identities) != 1:
        _fail("aggregate_identity_error", "env_tag/protocol/threads must agree across inputs")
    env, protocol, threads = next(iter(identities))
    workloads = sorted(
        {items for s, _, _ in sources for items in s.workload_values},
        key=lambda items: _canonical_json_bytes(dict(items)),
    )
    workload_wire = [dict(items) for items in workloads]
    campaigns = sorted({cid for s, _, _ in sources for cid in s.campaign_ids})
    identity = B4FloorArtifactIdentity(
        env, protocol, threads, _aggregate_identifier("set", workload_wire),
        campaigns[0] if len(campaigns) == 1 else _aggregate_identifier("set", campaigns),
    )
    # Fraction comparison preserves the accepted binary64 values exactly.
    maximum = max(s.floor_exact for s, _, _ in sources)
    representative = next(single for s, _, single in sources if s.floor_exact == maximum)
    return {
        **representative,
        "schema": B4_FLOOR_AGGREGATE_ARTIFACT_SCHEMA_VERSION,
        "artifact_identity": _identity_value(identity),
        "identity_derivation": {"workloads": workload_wire, "campaign_ids": campaigns},
        "non_guarantees": [
            *NON_GUARANTEES,
            *(item for s, _, _ in sources for item in s.proof_limitations),
            *AGGREGATE_NON_GUARANTEES,
        ],
        "aggregation": {
            "operation": AGGREGATE_MAXIMUM_ID,
            "expected_specs": [[path, digest] for path, digest in sorted(expected_specs)],
            "sources": [{
                **single["source_summary"],
                "floor_exact": single["floor_exact"],
                "source_float_hex": s.source_float_hex,
                "identity_derivation": single["identity_derivation"],
                "proof_limitations": document["proof_limitations"],
            } for s, document, single in sources],
        },
    }


def _aggregate_artifact_filename(identity: B4FloorArtifactIdentity) -> str:
    return _artifact_filename(identity).replace("b4-floor__", "b4-floor-aggregate__", 1)


def issue_aggregate_authoritative_floor(
    *, repo_root: Path, summary_paths: Sequence[Path],
    expected_specs: Sequence[tuple[str, str]], output_dir: Path,
) -> B4AuthoritativeFloorWrite:
    """Issue one maximum for an explicitly supplied spec closure, create-only.

    Neither the timing nor the preregistration suitability of the supplied
    expectation is proved. Every source remains necessary to load v2.
    """
    root = _repo_root(repo_root)
    if not isinstance(output_dir, Path):
        _fail("path_error", "output_dir must be Path")
    if output_dir == root or output_dir == Path("."):
        parent = root
    else:
        relpath = _argument_relpath(root, output_dir, label="aggregate output directory")
        parent = _assert_no_symlink(root, relpath, label="aggregate output directory")
    if not parent.is_dir():
        _fail("path_error", "aggregate output directory must be an existing directory")
    value = _aggregate_authority_value(root, summary_paths, expected_specs)
    filename = _aggregate_artifact_filename(_parse_identity(value["artifact_identity"]))
    path = parent / filename
    raw = _canonical_json_bytes(value)
    _publish_create_only(path, raw)
    return B4AuthoritativeFloorWrite(path.relative_to(root).as_posix(), hashlib.sha256(raw).hexdigest())


def _load_aggregate_authority(
    root: Path, relpath: str, digest: str, value: dict[str, object],
) -> B4AuthoritativeFloor:
    aggregation = _exact_object(
        value.get("aggregation"), {"operation", "expected_specs", "sources"},
        label="authority.aggregation",
    )
    sources = _exact_list(aggregation["sources"], label="aggregation.sources", allow_empty=False)
    paths = []
    for source in sources:
        if type(source) is not dict:
            _fail("schema_error", "aggregation source must be object")
        path = _relative_path(source.get("artifact_path"), label="aggregation source path")
        expected = _sha256(source.get("artifact_sha256"), label="aggregation source sha256")
        raw = _read_regular(root, path, label="aggregation source")
        if hashlib.sha256(raw).hexdigest() != expected:
            _fail("aggregate_source_hash_error", f"source hash differs: {path}")
        paths.append(Path(path))
    reconstructed = _aggregate_authority_value(root, paths, aggregation["expected_specs"])
    if _canonical_json_bytes(value) != _canonical_json_bytes(reconstructed):
        _fail("aggregate_reconstruction_error", "authority differs from full source reconstruction")
    source = reconstructed["source_summary"]
    return B4AuthoritativeFloor(
        floor=Fraction(*reconstructed["floor_exact"]), artifact_path=relpath,
        artifact_sha256=digest, schema_version=B4_FLOOR_AGGREGATE_ARTIFACT_SCHEMA_VERSION,
        generator_identity=GENERATOR_IDENTITY, source_float_hex=reconstructed["source_float_hex"],
        source_summary_path=source["artifact_path"], source_summary_sha256=source["artifact_sha256"],
        identity=_parse_identity(reconstructed["artifact_identity"]),
        non_guarantees=tuple(reconstructed["non_guarantees"]),
    )


def _parse_identity(value: object) -> B4FloorArtifactIdentity:
    identity = _exact_object(
        value,
        {"env_tag", "protocol", "threads", "workload_identifier", "campaign_identifier"},
        label="authority.artifact_identity",
    )
    return B4FloorArtifactIdentity(
        env_tag=_identifier(identity["env_tag"], label="authority.artifact_identity.env_tag"),
        protocol=_identifier(identity["protocol"], label="authority.artifact_identity.protocol"),
        threads=_positive_int(identity["threads"], label="authority.artifact_identity.threads"),
        workload_identifier=_identifier(
            identity["workload_identifier"],
            label="authority.artifact_identity.workload_identifier",
        ),
        campaign_identifier=_identifier(
            identity["campaign_identifier"],
            label="authority.artifact_identity.campaign_identifier",
        ),
    )


def load_authoritative_floor(
    *,
    repo_root: Path,
    artifact_path: str,
    expected_sha256: str,
) -> B4AuthoritativeFloor:
    """Load one canonical authority artifact bound to its required digest."""

    root = _repo_root(repo_root)
    relpath = _relative_path(artifact_path, label="artifact_path")
    raw = _read_regular(root, relpath, label="authority artifact")
    observed_sha256 = hashlib.sha256(raw).hexdigest()
    expected = _sha256(expected_sha256, label="expected_sha256")
    if observed_sha256 != expected:
        _fail(
            "artifact_hash_mismatch",
            f"expected={expected}, observed={observed_sha256}",
        )
    value = _load_json_bytes(raw, label="authority artifact", require_canonical=True)
    if type(value) is dict and value.get("schema") == B4_FLOOR_AGGREGATE_ARTIFACT_SCHEMA_VERSION:
        return _load_aggregate_authority(root, relpath, observed_sha256, value)
    authority = _exact_object(
        value,
        {
            "schema",
            "generator_identity",
            "floor_exact",
            "source_float_hex",
            "artifact_identity",
            "identity_derivation",
            "source_summary",
            "non_guarantees",
        },
        label="authority",
    )
    if authority["schema"] != B4_FLOOR_ARTIFACT_SCHEMA_VERSION:
        _fail("artifact_schema_error", "authority.schema が pinned version と不一致")
    if authority["generator_identity"] != GENERATOR_IDENTITY:
        _fail("artifact_schema_error", "authority.generator_identity が不一致")
    ratio = _exact_list(authority["floor_exact"], label="authority.floor_exact", allow_empty=False)
    if len(ratio) != 2 or type(ratio[0]) is not int or type(ratio[1]) is not int:
        _fail("artifact_schema_error", "authority.floor_exact は exact [int, int] でない")
    if ratio[1] <= 0:
        _fail("artifact_schema_error", "authority.floor_exact denominator は positive でない")
    floor = Fraction(ratio[0], ratio[1])
    if [floor.numerator, floor.denominator] != ratio:
        _fail("artifact_schema_error", "authority.floor_exact は既約 canonical ratio でない")
    if not (Fraction(0, 1) <= floor < Fraction(1, 1)):
        _fail("floor_domain_error", "authority.floor_exact が 0 <= floor < 1 でない")
    source_float_hex = _text(
        authority["source_float_hex"], label="authority.source_float_hex"
    )
    try:
        source_float = float.fromhex(source_float_hex)
    except ValueError as exc:
        raise B4FloorArtifactError(
            "artifact_schema_error", "authority.source_float_hex が binary64 hex でない"
        ) from exc
    if not math.isfinite(source_float) or source_float.hex() != source_float_hex:
        _fail("artifact_schema_error", "authority.source_float_hex が canonical finite hex でない")
    if Fraction(*source_float.as_integer_ratio()) != floor:
        _fail("artifact_schema_error", "source_float_hex と floor_exact が exact 一致しない")
    identity = _parse_identity(authority["artifact_identity"])
    derivation = _exact_object(
        authority["identity_derivation"],
        {"workloads", "campaign_ids"},
        label="authority.identity_derivation",
    )
    workload_rows = _exact_list(
        derivation["workloads"],
        label="authority.identity_derivation.workloads",
        allow_empty=False,
    )
    workload_values: list[dict[str, str]] = []
    for index, workload_value in enumerate(workload_rows):
        label = f"authority.identity_derivation.workloads[{index}]"
        if (
            type(workload_value) is not dict
            or not workload_value
            or any(
                type(key) is not str or type(item) is not str
                for key, item in workload_value.items()
            )
        ):
            _fail("artifact_schema_error", f"{label} は nonempty dict[str, str] でない")
        workload_values.append(dict(workload_value))
    if workload_values != sorted(workload_values, key=_canonical_json_bytes):
        _fail("artifact_schema_error", "identity workloads は canonical sort 順でない")
    if len({_canonical_json_bytes(item) for item in workload_values}) != len(workload_values):
        _fail("artifact_schema_error", "identity workloads に重複がある")
    if identity.workload_identifier != _aggregate_identifier("set", workload_values):
        _fail("artifact_identity_error", "workload_identifier が derivation と不一致")
    campaigns = _exact_list(
        derivation["campaign_ids"],
        label="authority.identity_derivation.campaign_ids",
        allow_empty=False,
    )
    for index, campaign in enumerate(campaigns):
        _identifier(campaign, label=f"authority.identity_derivation.campaign_ids[{index}]")
    if len(campaigns) != len(set(campaigns)):
        _fail("artifact_schema_error", "identity campaign_ids に重複がある")
    expected_campaign_identifier = (
        campaigns[0]
        if len(campaigns) == 1
        else _aggregate_identifier("set", campaigns)
    )
    if identity.campaign_identifier != expected_campaign_identifier:
        _fail("artifact_identity_error", "campaign_identifier が derivation と不一致")
    source = _exact_object(
        authority["source_summary"],
        {
            "artifact_path",
            "artifact_sha256",
            "schema",
            "status",
            "spec_relpath",
            "spec_sha256",
            "loaded_head",
            "plan_sha256",
        },
        label="authority.source_summary",
    )
    source_path = _relative_path(
        source["artifact_path"], label="authority.source_summary.artifact_path"
    )
    source_sha = _sha256(
        source["artifact_sha256"], label="authority.source_summary.artifact_sha256"
    )
    if source["schema"] != ACCEPTED_FLOOR_PAIR_SUMMARY_SCHEMA_VERSION:
        _fail("artifact_schema_error", "authority source summary schema が pin と不一致")
    if source["status"] != "generated":
        _fail("artifact_schema_error", "authority source summary status が generated でない")
    _relative_path(source["spec_relpath"], label="authority.source_summary.spec_relpath")
    _sha256(source["spec_sha256"], label="authority.source_summary.spec_sha256")
    loaded_head = _text(source["loaded_head"], label="authority.source_summary.loaded_head")
    if _HEX40_RE.fullmatch(loaded_head) is None:
        _fail("artifact_schema_error", "authority source loaded_head が不正")
    _sha256(source["plan_sha256"], label="authority.source_summary.plan_sha256")
    non_guarantees = tuple(
        _text(item, label=f"authority.non_guarantees[{index}]")
        for index, item in enumerate(
            _exact_list(
                authority["non_guarantees"], label="authority.non_guarantees", allow_empty=False
            )
        )
    )
    if non_guarantees[: len(NON_GUARANTEES)] != NON_GUARANTEES:
        _fail(
            "artifact_schema_error",
            "authority.non_guarantees の issuer 固定 prefix が exact contract と不一致",
        )
    return B4AuthoritativeFloor(
        floor=floor,
        artifact_path=relpath,
        artifact_sha256=observed_sha256,
        schema_version=B4_FLOOR_ARTIFACT_SCHEMA_VERSION,
        generator_identity=GENERATOR_IDENTITY,
        source_float_hex=source_float_hex,
        source_summary_path=source_path,
        source_summary_sha256=source_sha,
        identity=identity,
        non_guarantees=non_guarantees,
    )


def _floor_cell(document: str) -> str:
    prefix = f"|{PREREGISTRATION_FLOOR_LABEL}|"
    matches = [line for line in document.splitlines() if line.startswith(prefix)]
    if len(matches) != 1:
        _fail(
            "preregistration_floor_row_error",
            f"§5 floor row は exact 1 件でなければならない: observed={len(matches)}",
        )
    line = matches[0]
    if not line.endswith("|"):
        _fail("preregistration_floor_row_error", "§5 floor row の終端が不正")
    return line[len(prefix) : -1]


def resolve_preregistered_authoritative_floor(
    *,
    repo_root: Path,
    preregistration_path: Path,
) -> B4AuthoritativeFloor | None:
    """Resolve the exact §5 floor pin; only the verbatim sentinel means absent."""

    root = _repo_root(repo_root)
    prereg_relpath = _argument_relpath(
        root, preregistration_path, label="preregistration_path"
    )
    raw = _read_regular(root, prereg_relpath, label="preregistration")
    try:
        document = raw.decode("utf-8")
    except UnicodeError as exc:
        raise B4FloorArtifactError(
            "preregistration_encoding_error", "preregistration は UTF-8 でない"
        ) from exc
    cell = _floor_cell(document)
    if cell == PREREGISTRATION_ABSENT_SENTINEL:
        return None
    match = _FLOOR_PIN_RE.fullmatch(cell)
    if match is None:
        _fail(
            "preregistration_floor_grammar_error",
            "floor cell は 'artifact_path=<repo relative>; sha256=<lowercase hex64>' でない",
        )
    artifact_path = _relative_path(match.group("path"), label="floor artifact_path")
    expected_sha256 = match.group("sha256")
    return load_authoritative_floor(
        repo_root=root,
        artifact_path=artifact_path,
        expected_sha256=expected_sha256,
    )


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", required=True, type=Path)
    modes = parser.add_mutually_exclusive_group(required=True)
    modes.add_argument("--summary", type=Path)
    modes.add_argument("--aggregate-summary", action="append", type=Path)
    parser.add_argument("--expected-spec", action="append", nargs=2, metavar=("PATH", "SHA256"))
    parser.add_argument("--aggregate-output-dir", type=Path)
    args = parser.parse_args(argv)
    if args.summary is not None:
        if args.expected_spec is not None or args.aggregate_output_dir is not None:
            parser.error("aggregate-only arguments cannot accompany --summary")
    elif args.expected_spec is None or args.aggregate_output_dir is None:
        parser.error("aggregate mode requires --expected-spec and --aggregate-output-dir")
    try:
        if args.summary is not None:
            result = issue_authoritative_floor(
                repo_root=args.repo_root,
                summary_path=args.summary,
            )
        else:
            result = issue_aggregate_authoritative_floor(
                repo_root=args.repo_root, summary_paths=args.aggregate_summary,
                expected_specs=args.expected_spec, output_dir=args.aggregate_output_dir,
            )
    except B4FloorIdentityError as exc:
        error = {
            "error": exc.code,
            "missing_identity_elements": list(exc.missing_elements),
        }
        sys.stderr.buffer.write(_canonical_json_bytes(error))
        return 2
    except B4FloorArtifactError as exc:
        sys.stderr.buffer.write(
            _canonical_json_bytes({"error": exc.code, "detail": exc.detail})
        )
        return 2
    sys.stdout.buffer.write(
        _canonical_json_bytes(
            {
                "artifact_path": result.artifact_path,
                "artifact_sha256": result.artifact_sha256,
            }
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
