# -*- coding: utf-8 -*-
"""S8b binary admission の root 非依存 durable receipt。

この receipt が保証するのは、発行時に完全検証した admission の、保存から oracle
実走直前までの連続束縛である。gateway が発行したことの証明でも暗号学的保証でもない。
元の ``build-admission/v1`` は絶対 ``source_root`` を含むため、その location だけを
除いた canonical 派生 receipt を保存する。

本モジュールは schema、発行器、exact validator、portable record key の単一正本であり、
floor、freeze、oracle のいずれも import しない。
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Mapping

from .build_admission import (
    ADMISSION_SCHEMA,
    BuildAdmission,
    BuildAdmissionPolicy,
    BuildProvenance,
    ReviewId,
    require_build_admission,
)
from .source_digest import (
    EMPTY_TRACKED_DIFF_SHA256,
    SOURCE_EVIDENCE_SCHEMA,
    SourceEvidence,
)
from .s8b_sort_swo_receipt import (
    SortSwoReceiptError,
    validate_portable_sort_swo_pass_receipt,
)
from .s8b_expected_materialization import (
    ExpectedMaterializationError,
    SealedSnapshotCapability,
    validate_sealed_snapshot_capability,
)
from . import s8b_compiler_input


RECEIPT_SCHEMA = "s8b-binary-admission/v3"

PORTABLE_BUILT_KEYS = frozenset({
    "cell_id", "holdout_id", "configuration_id", "binary", "binary_sha256",
    "bin_hash_short", "binding", "configure_argv", "build_argv", "cached",
    "store_path", "admission_receipt",
})
PORTABLE_SORT_BEST_BUILT_KEYS = PORTABLE_BUILT_KEYS | {"sort_swo_oracle"}

_RECEIPT_KEYS = frozenset({
    "schema", "admission", "subject", "proof", "receipt_sha256",
})
_PROOF_KEYS = frozenset({
    "compiler_input_manifest", "materialization_binding", "source_protection",
})
_SOURCE_PROTECTION_KEYS = frozenset({
    "kind", "source_snapshot_sha256", "expected_materialization_sha256",
    "binary_sha256", "compiler_input_manifest_sha256",
})
_ADMISSION_KEYS = frozenset({
    "schema", "class", "policy_sha256", "review_id", "input_sha256", "source",
})
_SOURCE_KEYS = frozenset({
    "schema", "ccbench_commit", "genome_sha256", "src_token",
    "source_bytes_sha256", "tracked_clean", "tracked_diff_sha256", "tracked_paths",
})
_SUBJECT_KEYS = frozenset({
    "cell_id", "holdout_id", "configuration_id", "entry_sha256",
    "binding_sha256", "binary_sha256", "contract_sha256", "trace",
    "source_snapshot_sha256", "compiler_input_manifest_sha256",
    "expected_materialization_sha256",
})
_BINDING_KEYS = frozenset({
    "genome_canonical", "src_token", "variant_id", "entry_sha256", "binding_sha256",
})


class BinaryAdmissionError(ValueError):
    """S8b binary admission receipt を発行または検証できない。"""


def portable_built_keys_for(configuration_id: object) -> frozenset[str]:
    """configuration ごとの portable binary record exact key 集合を返す。"""

    if configuration_id == "sort_best":
        return PORTABLE_SORT_BEST_BUILT_KEYS
    return PORTABLE_BUILT_KEYS


def _plain_json(value: object) -> object:
    """Read-only Mapping を canonical JSON が扱える組込み値へ射影する。"""
    if isinstance(value, Mapping):
        return {key: _plain_json(child) for key, child in value.items()}
    if isinstance(value, (list, tuple)):
        return [_plain_json(child) for child in value]
    return value


def _canonical_json(value: object) -> str:
    try:
        return json.dumps(
            _plain_json(value), ensure_ascii=True, sort_keys=True, separators=(",", ":"),
            allow_nan=False,
        )
    except (TypeError, ValueError) as exc:
        raise BinaryAdmissionError(f"canonical JSON に変換できない: {exc}") from exc


def _sha256_map(value: Mapping[str, object]) -> str:
    return hashlib.sha256(_canonical_json(value).encode("utf-8")).hexdigest()


def _binding_sha256(value: Mapping[str, object]) -> str:
    rendered = json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")
    return hashlib.sha256(rendered).hexdigest()


def _is_sha256(value: object) -> bool:
    if type(value) is not str or len(value) != 64:
        return False
    try:
        int(value, 16)
    except ValueError:
        return False
    return value == value.lower()


def _exact_mapping(value: object, keys: frozenset[str], label: str) -> Mapping:
    if not isinstance(value, Mapping) or set(value) != set(keys):
        raise BinaryAdmissionError(f"{label} の exact key 集合が不一致")
    return value


def _validate_binding(value: object) -> Mapping:
    binding = _exact_mapping(value, _BINDING_KEYS, "binding")
    for key in ("genome_canonical", "src_token", "variant_id"):
        if type(binding[key]) is not str or not binding[key]:
            raise BinaryAdmissionError(f"binding.{key} が空でない str でない")
    for key in ("entry_sha256", "binding_sha256"):
        if not _is_sha256(binding[key]):
            raise BinaryAdmissionError(f"binding.{key} が SHA-256 でない")
    src_suffix = "" if binding["src_token"] == "stock" else f"|src={binding['src_token']}"
    expected_variant_id = hashlib.sha256(
        f"{binding['genome_canonical']}{src_suffix}".encode("utf-8")
    ).hexdigest()[:12]
    if binding["variant_id"] != expected_variant_id:
        raise BinaryAdmissionError("binding.variant_id が genome/src_token と不一致")
    unsigned = {key: binding[key] for key in sorted(_BINDING_KEYS - {"binding_sha256"})}
    if _binding_sha256(unsigned) != binding["binding_sha256"]:
        raise BinaryAdmissionError("binding.binding_sha256 が canonical body と不一致")
    return binding


def _source_projection(source: SourceEvidence) -> dict[str, object]:
    raw = source.as_receipt()
    return {key: raw[key] for key in sorted(_SOURCE_KEYS)}


def _validate_source(value: object) -> Mapping:
    source = _exact_mapping(value, _SOURCE_KEYS, "receipt admission.source")
    if source["schema"] != SOURCE_EVIDENCE_SCHEMA:
        raise BinaryAdmissionError("receipt source schema が不一致")
    for key in (
        "genome_sha256", "source_bytes_sha256", "tracked_diff_sha256",
    ):
        if not _is_sha256(source[key]):
            raise BinaryAdmissionError(f"receipt source.{key} が SHA-256 でない")
    if type(source["ccbench_commit"]) is not str or not source["ccbench_commit"]:
        raise BinaryAdmissionError("receipt source.ccbench_commit が不正")
    if (source["src_token"] != "stock" and not _is_sha256(source["src_token"])):
        raise BinaryAdmissionError("receipt source.src_token が不正")
    if type(source["tracked_clean"]) is not bool:
        raise BinaryAdmissionError("receipt source.tracked_clean が bool でない")
    paths = source["tracked_paths"]
    if (type(paths) is not list or any(type(path) is not str or not path for path in paths)
            or paths != sorted(set(paths))):
        raise BinaryAdmissionError("receipt source.tracked_paths が sorted unique list[str] でない")
    if source["tracked_clean"] != (not paths):
        raise BinaryAdmissionError("receipt source.tracked_clean と tracked_paths が不整合")
    if source["tracked_clean"] != (
            source["tracked_diff_sha256"] == EMPTY_TRACKED_DIFF_SHA256):
        raise BinaryAdmissionError("receipt source.tracked_clean と tracked diff が不整合")
    return source


def issue_binary_admission_receipt(
    *, admission: BuildAdmission, expected_policy: BuildAdmissionPolicy,
    source: SourceEvidence, cell_id: str, holdout_id: str,
    configuration_id: str, binding: Mapping, binary: Path | str,
    binary_sha256: str, contract_sha256: str, trace: bool,
    source_snapshot_sha256: str, expected_materialization_sha256: str,
    compiler_input_manifest: Mapping,
    compiler_input_manifest_sha256: str,
    source_protection: SealedSnapshotCapability,
    current_compiler_input_masstree_root: Path | str | None = None,
    current_compiler_input_dependency_prefix_roots: object = None,
) -> dict[str, object]:
    """完全検証した admission と発行済み snapshot capability を射影する。

    保護の射程は build 中の source 差し替え (A→B→A) だけであり、汚染 cache
    binary の再利用は閉じない。sealed-cache-hit は過去の保護下 build を証明しない。
    capability は trusted producer 内の実行由来の値であり、kernel attestation や
    電子署名、敵対的 Python / process memory 改変に対する境界ではない。
    """

    try:
        require_build_admission(
            admission, expected_policy=expected_policy, expected_source=source,
        )
    except (TypeError, ValueError, RuntimeError) as exc:
        raise BinaryAdmissionError(f"元 build admission の完全検証に失敗: {exc}") from exc
    admission_body = admission.as_wal_receipt()
    if (admission.provenance is not BuildProvenance.HUMAN_REVIEWED
            or admission_body["class"] != BuildProvenance.HUMAN_REVIEWED.value
            or admission_body["review_id"] != ReviewId.S8B_FLOOR.value):
        raise BinaryAdmissionError("S8b receipt は s8b-floor human-reviewed admission が必要")
    checked_binding = _validate_binding(binding)
    for label, value in (
        ("cell_id", cell_id), ("holdout_id", holdout_id),
        ("configuration_id", configuration_id),
    ):
        if type(value) is not str or not value:
            raise BinaryAdmissionError(f"subject.{label} が空でない str でない")
    if admission_body["input_sha256"] != checked_binding["entry_sha256"]:
        raise BinaryAdmissionError("review input が freeze entry SHA と不一致")
    source_body = _source_projection(source)
    if source_body["genome_sha256"] != hashlib.sha256(
            checked_binding["genome_canonical"].encode("utf-8")).hexdigest():
        raise BinaryAdmissionError("source genome が binding と不一致")
    if source_body["src_token"] != checked_binding["src_token"]:
        raise BinaryAdmissionError("source src_token が binding と不一致")
    if (not _is_sha256(source_snapshot_sha256)
            or not _is_sha256(expected_materialization_sha256)):
        raise BinaryAdmissionError(
            "source snapshot/expected materialization SHA が不正"
        )
    if source_snapshot_sha256 != expected_materialization_sha256:
        raise BinaryAdmissionError(
            "source snapshot SHA が expected materialization と不一致"
        )
    try:
        checked_manifest = s8b_compiler_input.validate_compiler_input_manifest(
            compiler_input_manifest,
            compiler_input_manifest_sha256,
            snapshot_root=source.source_root,
            current_fetchcontent_masstree_root=(
                current_compiler_input_masstree_root
            ),
            current_dependency_prefix_roots=(
                current_compiler_input_dependency_prefix_roots
            ),
        )
    except s8b_compiler_input.CompilerInputError as exc:
        raise BinaryAdmissionError(
            f"compiler input manifest の完全検証に失敗: {exc}"
        ) from exc
    if not _is_sha256(binary_sha256) or not _is_sha256(contract_sha256):
        raise BinaryAdmissionError("binary/contract SHA が不正")
    if type(trace) is not bool or trace is not False:
        raise BinaryAdmissionError("S8b floor binary は trace=False が必要")
    try:
        actual_binary_sha256 = hashlib.sha256(Path(binary).read_bytes()).hexdigest()
    except OSError as exc:
        raise BinaryAdmissionError(f"発行対象 binary bytes を読めない: {exc}") from exc
    if actual_binary_sha256 != binary_sha256:
        raise BinaryAdmissionError("発行対象 binary bytes が build 記録 SHA と不一致")

    try:
        protection = validate_sealed_snapshot_capability(
            source_protection,
            source_snapshot_sha256=source_snapshot_sha256,
            expected_materialization_sha256=expected_materialization_sha256,
            binary_sha256=binary_sha256,
            compiler_input_manifest_sha256=compiler_input_manifest_sha256,
        )
    except ExpectedMaterializationError as exc:
        raise BinaryAdmissionError(f"source protection capability が不正: {exc}") from exc

    body: dict[str, object] = {
        "schema": RECEIPT_SCHEMA,
        "admission": {
            "schema": ADMISSION_SCHEMA,
            "class": admission_body["class"],
            "policy_sha256": admission_body["policy_sha256"],
            "review_id": admission_body["review_id"],
            "input_sha256": admission_body["input_sha256"],
            "source": source_body,
        },
        "subject": {
            "cell_id": cell_id,
            "holdout_id": holdout_id,
            "configuration_id": configuration_id,
            "entry_sha256": checked_binding["entry_sha256"],
            "binding_sha256": checked_binding["binding_sha256"],
            "binary_sha256": binary_sha256,
            "contract_sha256": contract_sha256,
            "trace": trace,
            "source_snapshot_sha256": source_snapshot_sha256,
            "compiler_input_manifest_sha256": compiler_input_manifest_sha256,
            "expected_materialization_sha256": expected_materialization_sha256,
        },
        "proof": {
            "compiler_input_manifest": checked_manifest,
            "materialization_binding": dict(checked_binding),
            "source_protection": {
                "kind": protection.kind.value,
                "source_snapshot_sha256": protection.source_snapshot_sha256,
                "expected_materialization_sha256": protection.expected_materialization_sha256,
                "binary_sha256": protection.binary_sha256,
                "compiler_input_manifest_sha256": protection.compiler_input_manifest_sha256,
            },
        },
    }
    body["receipt_sha256"] = _sha256_map(body)
    return json.loads(_canonical_json(body))


def validate_portable_binary_record(
    record: object, *, expected_policy: BuildAdmissionPolicy | None,
    expected_ccbench_pin: str | None = None,
    expected_contract_sha256: str | None = None,
    expected_cell_id: str | None = None,
    expected_holdout_id: str | None = None,
    expected_configuration_id: str | None = None,
    expected_entry_sha256: str | None = None,
    expected_binding_sha256: str | None = None,
) -> dict[str, object]:
    """Receipt の構造、canonical SHA、record subject、外部 authority を検証する。

    ``expected_policy=None`` は historical reverify 専用で、artifact 内 policy を期待値へ
    流用しない。live consumer は公開 resolver 由来の policy を必ず渡す。
    """

    if not isinstance(record, Mapping):
        raise BinaryAdmissionError("portable binary record が Mapping でない")
    configuration_id = record.get("configuration_id")
    if set(record) != set(portable_built_keys_for(configuration_id)):
        raise BinaryAdmissionError(
            "portable binary record の configuration 条件付き exact key 集合が不一致"
        )
    receipt = record.get("admission_receipt")
    if not isinstance(receipt, Mapping):
        raise BinaryAdmissionError("admission receipt が object でない")
    receipt = _plain_json(receipt)
    receipt = _exact_mapping(receipt, _RECEIPT_KEYS, "admission receipt")
    if receipt["schema"] != RECEIPT_SCHEMA:
        raise BinaryAdmissionError("admission receipt schema が不一致")
    if not _is_sha256(receipt["receipt_sha256"]):
        raise BinaryAdmissionError("admission receipt outer SHA が不正")
    unsigned = dict(receipt)
    outer = unsigned.pop("receipt_sha256")
    if _sha256_map(unsigned) != outer:
        raise BinaryAdmissionError("admission receipt outer SHA が canonical body と不一致")

    admission = _exact_mapping(receipt["admission"], _ADMISSION_KEYS, "receipt admission")
    if (admission["schema"] != ADMISSION_SCHEMA
            or admission["class"] != BuildProvenance.HUMAN_REVIEWED.value
            or admission["review_id"] != ReviewId.S8B_FLOOR.value):
        raise BinaryAdmissionError("receipt admission schema/class/review_id が不一致")
    if not _is_sha256(admission["policy_sha256"]):
        raise BinaryAdmissionError("receipt admission policy SHA が不正")
    if expected_policy is not None:
        if type(expected_policy) is not BuildAdmissionPolicy:
            raise BinaryAdmissionError("expected_policy が公開 resolver 由来の exact policy でない")
        if admission["policy_sha256"] != expected_policy.sha256:
            raise BinaryAdmissionError("receipt admission policy が現行 policy と不一致")
    source = _validate_source(admission["source"])
    subject = _exact_mapping(receipt["subject"], _SUBJECT_KEYS, "receipt subject")
    for key in (
        "entry_sha256", "binding_sha256", "binary_sha256", "contract_sha256",
        "source_snapshot_sha256", "compiler_input_manifest_sha256",
        "expected_materialization_sha256",
    ):
        if not _is_sha256(subject[key]):
            raise BinaryAdmissionError(f"receipt subject.{key} が SHA-256 でない")
    for key in ("cell_id", "holdout_id", "configuration_id"):
        if type(subject[key]) is not str or not subject[key]:
            raise BinaryAdmissionError(f"receipt subject.{key} が空でない str でない")
    if subject["trace"] is not False:
        raise BinaryAdmissionError("receipt subject.trace が false でない")
    if admission["input_sha256"] != subject["entry_sha256"]:
        raise BinaryAdmissionError("receipt review input と subject entry が不一致")

    binding = _validate_binding(record.get("binding"))
    if source["genome_sha256"] != hashlib.sha256(
            binding["genome_canonical"].encode("utf-8")).hexdigest():
        raise BinaryAdmissionError("receipt source genome が record binding と不一致")
    if source["src_token"] != binding["src_token"]:
        raise BinaryAdmissionError("receipt source src_token が record binding と不一致")
    proof = _exact_mapping(receipt["proof"], _PROOF_KEYS, "receipt proof")
    materialization_binding = _validate_binding(
        proof["materialization_binding"]
    )
    if materialization_binding != binding:
        raise BinaryAdmissionError(
            "receipt materialization binding が record binding と不一致"
        )
    try:
        compiler_input_manifest = s8b_compiler_input._normalized_manifest(
            proof["compiler_input_manifest"], target=None,
        )
    except s8b_compiler_input.CompilerInputError as exc:
        raise BinaryAdmissionError(
            f"receipt compiler input manifest が不正: {exc}"
        ) from exc
    recomputed_manifest_sha256 = s8b_compiler_input.manifest_sha256(
        compiler_input_manifest
    )
    if (subject["compiler_input_manifest_sha256"]
            != recomputed_manifest_sha256):
        raise BinaryAdmissionError(
            "receipt subject compiler input manifest SHA が proof 再計算値と不一致"
        )
    if (subject["source_snapshot_sha256"]
            != subject["expected_materialization_sha256"]):
        raise BinaryAdmissionError(
            "receipt subject source snapshot SHA が expected materialization と不一致"
        )
    protection = _exact_mapping(
        proof["source_protection"], _SOURCE_PROTECTION_KEYS,
        "receipt proof.source_protection",
    )
    if protection["kind"] not in ("sealed-build", "sealed-cache-hit"):
        raise BinaryAdmissionError("receipt source_protection.kind が不正")
    for key in sorted(_SOURCE_PROTECTION_KEYS - {"kind"}):
        if protection[key] != subject[key]:
            raise BinaryAdmissionError(f"receipt source_protection.{key} が subject と不一致")
    if expected_ccbench_pin is not None and source["ccbench_commit"] != expected_ccbench_pin:
        raise BinaryAdmissionError("receipt source ccbench pin が外部期待値と不一致")
    if (expected_contract_sha256 is not None
            and subject["contract_sha256"] != expected_contract_sha256):
        raise BinaryAdmissionError("receipt subject contract が外部期待値と不一致")

    record_binary_sha256 = record.get("binary_sha256")
    if subject["binary_sha256"] != record_binary_sha256:
        raise BinaryAdmissionError("receipt subject binary SHA が record と不一致")
    actual_tuple = (
        subject["cell_id"], subject["holdout_id"], subject["configuration_id"],
        subject["entry_sha256"], subject["binding_sha256"],
    )
    record_tuple = (
        record.get("cell_id"), record.get("holdout_id"),
        record.get("configuration_id"), binding["entry_sha256"],
        binding["binding_sha256"],
    )
    expected_tuple = (
        expected_cell_id if expected_cell_id is not None else record.get("cell_id"),
        expected_holdout_id if expected_holdout_id is not None else record.get("holdout_id"),
        expected_configuration_id if expected_configuration_id is not None
        else record.get("configuration_id"),
        expected_entry_sha256 if expected_entry_sha256 is not None
        else binding["entry_sha256"],
        expected_binding_sha256 if expected_binding_sha256 is not None
        else binding["binding_sha256"],
    )
    if actual_tuple != record_tuple or actual_tuple != expected_tuple:
        raise BinaryAdmissionError(
            "receipt subject が record または外部期待の "
            "cell/holdout/configuration/entry/binding と不一致"
        )
    if configuration_id == "sort_best":
        try:
            validate_portable_sort_swo_pass_receipt(
                record["sort_swo_oracle"],
                expected_cell_id=record["cell_id"],
                expected_holdout_id=record["holdout_id"],
                expected_configuration_id=configuration_id,
                expected_entry_sha256=binding["entry_sha256"],
                expected_binary_sha256=record["binary_sha256"],
            )
        except SortSwoReceiptError as exc:
            raise BinaryAdmissionError(f"sort_best SWO receipt が不正: {exc}") from exc
    return json.loads(_canonical_json(receipt))
