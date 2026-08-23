"""T-338 unit 5 writer and executable conformance-vector boundary.

Coverage table: ``relabel`` 39 (unit-3 semantic fixture/predicate surface),
``new`` 6 (authority/publish and create-only destination), and
``architecture`` 1 (``kind="api"``: caller cannot choose a relative path).
The 44 rejection vectors cover §6.1--§6.10 and §7.1(1)--(20); semantic and
publish positives remain separate.
"""

from __future__ import annotations

import ast
from collections import Counter
from dataclasses import replace
import errno
import hashlib
import importlib
import inspect
import json
import os
from pathlib import Path
from types import SimpleNamespace

import pytest

from orchestrator.submission_gate import _git
from orchestrator.submission_gate import _manifest
from orchestrator.submission_gate import _semantic_validator as semantic
from orchestrator.submission_gate import _writer as writer
from orchestrator.submission_gate._receipt_io import (
    ReceiptParseError,
    parse_receipt_bytes,
)
from orchestrator.submission_gate._receipt_schema import ReceiptSchema
from orchestrator.submission_gate._safe_io import SafeIOError
from orchestrator.preregistration import approval_payload as approval
from orchestrator.preregistration.blobref import BlobRef, read_pinned_blob


_ROOT = Path(__file__).resolve().parents[2]
_CONFORMANCE = _ROOT / "orchestrator" / "tests" / "fixtures" / "t338_submission_gate" / "conformance"
_UNIT3 = importlib.import_module("orchestrator.tests.test_t338_submission_gate_unit3")
_PATH = importlib.import_module("orchestrator.tests.test_t139_submission_path")
_UNIT3_ONLY = "対応なし・unit5独自"
_V1_INDEX_REF = BlobRef(
    "orchestrator/tests/fixtures/t338_submission_gate/conformance/index-v1.json",
    "383bd3f272bac02fcf5b865a69d8652d9668b6d1",
    "c66953bef617ff34e51ed988cf063c8e86e2a42e4132cdbab7f02732f2dc0643",
)
_SEMANTIC_REASON_CODES = frozenset(
    {
        "a03",
        "a07",
        "allocation",
        "argv",
        "authority",
        "binary",
        "cardinality",
        "compile",
        "correctness",
        "intent",
        "phase",
        "planned_actual",
        "pointer",
        "preregistration",
        "reason",
        "reference",
        "reject_only",
        "run_log",
        "schedule",
        "schema",
        "schema_pin",
        "semantic",
        "shape",
        "source",
        "study",
        "wait",
    }
)


def _index() -> dict[str, object]:
    return json.loads((_CONFORMANCE / "index-v2.json").read_text(encoding="utf-8"))


def _vector_entries() -> list[dict[str, object]]:
    return _index()["vectors"]  # type: ignore[return-value]


def _entry(vector_id: str) -> dict[str, object]:
    return next(item for item in _vector_entries() if item["id"] == vector_id)


def _vector(item: dict[str, object]) -> dict[str, object]:
    path = _CONFORMANCE / str(item["path"])
    return json.loads(path.read_text(encoding="utf-8"))


def _resolve_recipe_value(value: object, fixture: object) -> object:
    """Resolve only fixture-local values; vector files remain JSON data."""

    if isinstance(value, dict):
        if set(value) == {"fixture_pointer"}:
            path = str(value["fixture_pointer"])
            root = fixture.root  # type: ignore[attr-defined]
            data = (root / path).read_bytes()
            return _UNIT3._file_record(root, path, data)
        if set(value) == {"fixture_failure_evidence"}:
            path = str(value["fixture_failure_evidence"])
            root = fixture.root  # type: ignore[attr-defined]
            data = (root / path).read_bytes()
            return {"kind": "scheduler", "pointer": _UNIT3._file_record(root, path, data)}
        return {key: _resolve_recipe_value(child, fixture) for key, child in value.items()}
    if isinstance(value, list):
        return [_resolve_recipe_value(child, fixture) for child in value]
    return value


def _set_path(value: object, path: list[object], replacement: object) -> None:
    if not path:
        raise AssertionError("mutation path must not be empty")
    current = value
    for component in path[:-1]:
        current = current[component]  # type: ignore[index]
    current[path[-1]] = replacement  # type: ignore[index]


def _update_file_records(value: object, relative_path: str, data: bytes) -> None:
    if isinstance(value, dict):
        if (
            value.get("path") == relative_path
            and "size" in value
            and "sha256" in value
        ):
            value["size"] = len(data)
            value["sha256"] = hashlib.sha256(data).hexdigest()
        for child in value.values():
            _update_file_records(child, relative_path, data)
    elif isinstance(value, list):
        for child in value:
            _update_file_records(child, relative_path, data)


def _replace_file(fixture: object, value: dict[str, object], mutation: dict[str, object]) -> None:
    relative_path = str(mutation["path"])
    target = fixture.root / relative_path  # type: ignore[attr-defined]
    raw = target.read_bytes()
    old = str(mutation["old"]).encode("utf-8")
    new = str(mutation["new"]).encode("utf-8")
    if raw.count(old) != 1:
        raise AssertionError(f"vector replacement is not unique in {relative_path}")
    updated = raw.replace(old, new, 1)
    target.write_bytes(updated)
    _update_file_records(value, relative_path, updated)


def _apply_mutation(fixture: object, value: dict[str, object], mutation: object) -> None:
    if mutation is None:
        return
    recipe = mutation  # type: ignore[assignment]
    if not isinstance(recipe, dict):
        raise AssertionError("vector mutation must be an object or null")
    operation = recipe.get("op")
    if operation == "none":
        return
    if operation == "forged_binding":
        assert recipe["record"] == "fixture.record"
        assert recipe["prereg_commit"] == "fixture.binding.prereg_commit"
        return
    if operation == "schema_pin":
        schema_sha256 = recipe["sha256"]
        assert isinstance(schema_sha256, str) and len(schema_sha256) == 64
        return
    if operation == "scenario":
        assert isinstance(recipe["name"], str)
        return
    if operation == "set":
        _set_path(
            value,
            recipe["path"],  # type: ignore[arg-type]
            _resolve_recipe_value(recipe["value"], fixture),
        )
        return
    if operation == "set_many":
        for change in recipe["changes"]:  # type: ignore[union-attr]
            _set_path(
                value,
                change["path"],
                _resolve_recipe_value(change["value"], fixture),
            )
        return
    if operation == "pop":
        container = value
        path = recipe["path"]  # type: ignore[assignment]
        for component in path:
            container = container[component]  # type: ignore[index]
        del container[int(recipe["index"])]  # type: ignore[index]
        return
    if operation == "reverse":
        container = value
        for component in recipe["path"]:  # type: ignore[union-attr]
            container = container[component]  # type: ignore[index]
        container.reverse()  # type: ignore[union-attr]
        return
    if operation == "replace_file":
        _replace_file(fixture, value, recipe)
        return
    if operation == "sequence":
        for child in recipe["operations"]:  # type: ignore[union-attr]
            _apply_mutation(fixture, value, child)
        return
    raise AssertionError(f"unknown conformance mutation operation: {operation!r}")


def _duplicate_verification_pair_payload() -> dict[str, object]:
    pairs = [(arm, workload) for arm in semantic._ARMS for workload in semantic._WORKLOADS]
    evidence = [
        {"arm": arm, "workload": workload, "run_scope": {"allocation_id": "alloc-verification"}}
        for arm, workload in pairs
    ]
    liveness = [
        {
            "allocation_id": "alloc-verification",
            "probe": "liveness_run",
            "arm_or_null": arm,
            "workload_or_null": workload,
        }
        for arm, workload in pairs
    ]
    evidence[-1]["arm"] = evidence[0]["arm"]
    evidence[-1]["workload"] = evidence[0]["workload"]
    liveness[-1]["arm_or_null"] = liveness[0]["arm_or_null"]
    liveness[-1]["workload_or_null"] = liveness[0]["workload_or_null"]
    return {
        "planned_execution": {"consumed_cluster_slots": [1]},
        "attempts": [
            {
                "attempt_id": "attempt-verification",
                "cluster_slot_or_null": None,
                "reason_code": "completed",
                "allocation_id": "alloc-verification",
                "performance_started_marker": None,
                "failure_evidence": None,
            }
        ],
        "actual_runs": [],
        "correctness_evidence": evidence,
        "liveness": liveness,
    }


def _assert_semantic_vector(
    fixture: object,
    value: dict[str, object],
    schema: ReceiptSchema,
    item: dict[str, object],
    vector: dict[str, object],
) -> None:
    entrypoint = vector["entrypoint"]
    _apply_mutation(fixture, value, vector.get("mutation"))
    if entrypoint == "receipt":
        document = _UNIT3._receipt_document(value)
        if item["kind"] == "positive":
            semantic._validate_receipt_semantics(
                fixture.root,  # type: ignore[attr-defined]
                document,
                schema=schema,
                binding=fixture.binding,  # type: ignore[attr-defined]
            )
            return
        with pytest.raises(semantic.SemanticValidationError) as caught:
            semantic._validate_receipt_semantics(
                fixture.root,  # type: ignore[attr-defined]
                document,
                schema=schema,
                binding=fixture.binding,  # type: ignore[attr-defined]
            )
        assert caught.value.reason_code == item["expected_reason"]
        return
    if entrypoint == "preregistration":
        recipe = vector["mutation"]
        assert recipe["op"] == "forged_binding"
        forged = SimpleNamespace(
            record=fixture.record,  # type: ignore[attr-defined]
            prereg_commit=fixture.binding.prereg_commit,  # type: ignore[attr-defined]
        )
        with pytest.raises(semantic.SemanticValidationError) as caught:
            semantic._parse_preregistration_8key(
                value["preregistration"], binding=forged
            )
        assert caught.value.reason_code == item["expected_reason"]
        return
    if entrypoint == "create_only_references":
        with pytest.raises(semantic.SemanticValidationError) as caught:
            semantic._validate_create_only_references(fixture.root, value)  # type: ignore[attr-defined]
        assert caught.value.reason_code == item["expected_reason"]
        return
    if entrypoint == "reason_branches":
        recipe = vector["mutation"]
        assert recipe == {"op": "scenario", "name": "duplicate_verification_pair"}
        payload = _duplicate_verification_pair_payload()
        with pytest.raises(semantic.SemanticValidationError) as caught:
            semantic._validate_reason_branches(payload, {}, anomaly=False)
        assert caught.value.reason_code == item["expected_reason"]
        return
    if entrypoint == "schema_pin":
        recipe = vector["mutation"]
        assert recipe["op"] == "schema_pin"
        bad_sha256 = recipe["sha256"]
        bad_ref = replace(schema.ref, sha256=bad_sha256)
        bad_schema = ReceiptSchema(ref=bad_ref, sha256=bad_sha256, document=schema.document)
        document = _UNIT3._receipt_document(value)
        with pytest.raises(semantic.SemanticValidationError) as caught:
            semantic._validate_receipt_semantics(
                fixture.root,  # type: ignore[attr-defined]
                document,
                schema=bad_schema,
                binding=fixture.binding,  # type: ignore[attr-defined]
            )
        assert caught.value.reason_code == item["expected_reason"]
        return
    raise AssertionError(f"unknown semantic vector entrypoint: {entrypoint!r}")


def test_conformance_index_has_complete_scoped_coverage() -> None:
    entries = _vector_entries()
    assert len(entries) == 46
    assert sum(item["kind"] in {"negative", "api"} for item in entries) == 44
    assert sum(item["kind"] == "positive" for item in entries) == 2
    assert Counter(item["classification"] for item in entries) == Counter(
        {"relabel": 39, "new": 6, "architecture": 1}
    )
    covered = {cover for item in entries for cover in item["covers"]}
    assert {f"6.{number}" for number in range(1, 11)} <= covered
    assert {f"7.1({number})" for number in range(1, 21)} <= covered
    assert {"semantic_positive", "writer_authority", "writer_api"} <= covered

    for item in entries:
        path = _CONFORMANCE / str(item["path"])
        assert path.is_file()
        assert hashlib.sha256(path.read_bytes()).hexdigest() == item["sha256"]
        vector = json.loads(path.read_text(encoding="utf-8"))
        for key in ("id", "kind", "classification", "covers", "unit3_reference", "entrypoint"):
            assert vector[key] == item[key]
        reference = item["unit3_reference"]
        if reference != _UNIT3_ONLY:
            function = getattr(_UNIT3, reference, None)
            assert inspect.isfunction(function), reference


def test_v1_projection_is_independently_pinned_and_v2_appends_four() -> None:
    historical = read_pinned_blob(_ROOT, _V1_INDEX_REF)
    assert hashlib.sha256(historical).hexdigest() == _V1_INDEX_REF.sha256
    assert (_CONFORMANCE / "index-v1.json").read_bytes() == historical
    old_entries = json.loads(historical)["vectors"]
    assert len(old_entries) == 42
    assert _vector_entries()[:42] == old_entries
    assert [item["id"] for item in _vector_entries()[42:]] == [
        "writer_publish_sealed_authority",
        "manifest_index_ref_mismatch",
        "payload_index_ref_mismatch",
        "historical_index_blob_replaced",
    ]


def test_writer_api_has_no_caller_selected_destination() -> None:
    parameters = inspect.signature(writer._publish_receipt).parameters
    assert set(parameters) == {"repository_root", "raw_bytes", "binding"}
    assert all(parameter.kind is inspect.Parameter.KEYWORD_ONLY for parameter in parameters.values())
    assert "relative_path" not in parameters


def test_semantic_positive_reuses_unit3_full_fixture(tmp_path: Path) -> None:
    fixture = _UNIT3._make_git_fixture(tmp_path)
    value, schema = _UNIT3._full_receipt(fixture)
    semantic._validate_receipt_semantics(
        fixture.root,
        _UNIT3._receipt_document(value),
        schema=schema,
        binding=fixture.binding,
    )
    assert _entry("semantic_positive")["expected_reason"] is None


def test_publish_rejected_missing_authority_after_semantic_gate(tmp_path: Path) -> None:
    fixture = _UNIT3._make_git_fixture(tmp_path)
    value, _ = _UNIT3._full_receipt(fixture)
    document = _UNIT3._receipt_document(value)
    destination_parent = fixture.root / "output" / "receipts" / "t139"
    destination_parent.mkdir(parents=True)

    with pytest.raises(writer.VectorAuthorityUnavailableError) as caught:
        writer._publish_receipt(
            repository_root=fixture.root,
            raw_bytes=document.raw_bytes,
            binding=fixture.binding,
        )

    assert caught.value.reason_code == "vector_authority_unavailable"
    assert not any(destination_parent.iterdir())


def test_publish_rejects_stale_binding_before_schema_load(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    fixture = _UNIT3._make_git_fixture(tmp_path)
    value, _ = _UNIT3._full_receipt(fixture)
    document = _UNIT3._receipt_document(value)
    stale_binding = _UNIT3._binding._PreregBinding._issue(
        record=fixture.record,
        approved_manifest=fixture.binding.approved_manifest,
        repository_root=fixture.root,
        measurement_head=fixture.effective_commit,
        prereg_commit=fixture.root_commit,
        prereg_content_commit=fixture.content_commit,
        prereg_effective_commit=fixture.effective_commit,
        root_identity=(fixture.root.stat().st_dev, fixture.root.stat().st_ino),
        token=_UNIT3._binding._CAPABILITY_TOKEN,
    )
    schema_loads = 0
    original_load_schema = writer._load_schema_from_ref

    def record_schema_load(*args: object, **kwargs: object) -> object:
        nonlocal schema_loads
        schema_loads += 1
        return original_load_schema(*args, **kwargs)

    monkeypatch.setattr(writer, "_load_schema_from_ref", record_schema_load)

    with pytest.raises(_git.GitSupportError):
        writer._publish_receipt(
            repository_root=fixture.root,
            raw_bytes=document.raw_bytes,
            binding=stale_binding,
        )

    assert schema_loads == 0


def test_destination_is_derived_from_shape_checked_receipt() -> None:
    raw = b'{"study_id":"abc-1","series_id":"' + b"a" * 64 + b'","study_stage":"main_run"}'
    document = writer.parse_receipt_bytes(raw)
    assert writer._destination(document) == (
        "output/receipts/t139/abc-1--"
        + "a" * 64
        + "--main_run.json"
    )


def test_parse_and_type_checks_precede_binding_use(tmp_path: Path) -> None:
    with pytest.raises(TypeError):
        writer._publish_receipt(
            repository_root=tmp_path,
            raw_bytes=bytearray(b"{}"),
            binding=object(),
        )
    with pytest.raises(ReceiptParseError):
        writer._publish_receipt(
            repository_root=tmp_path,
            raw_bytes=b'{"x":1,"x":2}',
            binding=object(),
        )


def test_vector_guard_is_structurally_fail_closed() -> None:
    fixture = SimpleNamespace(approved_manifest=object())
    with pytest.raises(_manifest.VectorAuthorityMismatchError):
        writer._assert_vector_authority(binding=fixture)  # type: ignore[arg-type]


def test_vector_guard_rejects_legacy_d282_authority(tmp_path: Path) -> None:
    fixture = _UNIT3._make_git_fixture(tmp_path)
    with pytest.raises(writer.VectorAuthorityUnavailableError) as caught:
        writer._assert_vector_authority(binding=fixture.binding)
    assert caught.value.reason_code == "vector_authority_unavailable"


def test_receipt_publish_call_sites_are_path_aware_and_allow_event_sink() -> None:
    allowed_writer = Path("orchestrator/submission_gate/_writer.py")
    allowed_receipt_io = Path("orchestrator/submission_gate/_receipt_io.py")
    allowed_event_sink = Path("orchestrator/submission_gate/_attempt_authority.py")
    for source_path in _ROOT.rglob("*.py"):
        relative = source_path.relative_to(_ROOT)
        if relative.parts[:2] == ("orchestrator", "tests"):
            continue
        source = source_path.read_text(encoding="utf-8")
        tree = ast.parse(source, filename=str(relative))
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            function = node.func
            name = function.id if isinstance(function, ast.Name) else (
                function.attr if isinstance(function, ast.Attribute) else None
            )
            if name == "create_receipt_bytes":
                assert relative == allowed_writer
            elif name == "create_only_relative_bytes":
                if relative == allowed_receipt_io:
                    continue
                assert relative == allowed_event_sink
                assert 799 <= node.lineno <= 806
                assert len(node.args) >= 2 and isinstance(node.args[1], ast.JoinedStr)
                assert "authority.event_directory" in ast.get_source_segment(source, node)


def test_conformance_reasons_remain_explicit() -> None:
    for item in _vector_entries():
        vector = _vector(item)
        entrypoint = vector["entrypoint"]
        if entrypoint in {"receipt", "preregistration", "create_only_references", "reason_branches", "schema_pin"}:
            if item["kind"] == "positive":
                assert item["expected_reason"] is None
                continue
            assert item["expected_reason"] in _SEMANTIC_REASON_CODES
        elif entrypoint == "writer_authority":
            assert item["expected_reason"] is None
            if item["kind"] == "positive":
                assert vector["expected"] == "writer_create_only_publishes_raw_input_bytes"
            elif item["id"] == "publish_rejected_missing_authority":
                assert item["expected_exception"] == "VectorAuthorityUnavailableError"
                assert item["expected_code"] == "vector_authority_unavailable"
            else:
                assert item["expected_exception"] == "VectorAuthorityMismatchError"
                assert item["expected_code"] in {
                    "manifest_index_ref_mismatch",
                    "payload_index_ref_mismatch",
                    "vector_index_blob_digest_mismatch",
                }
        elif entrypoint == "parse":
            assert item["expected_reason"] is None
            assert item["expected_exception"] == "ReceiptParseError"
        elif entrypoint == "safe_io":
            assert item["expected_reason"] is None
            assert item["expected_exception"] == "SafeIOError"
            assert item["expected_errno"] == "EEXIST"
        elif entrypoint == "api":
            assert item["expected_reason"] is None
            assert item["expected_api"] == "no_caller_selected_destination"
        else:
            raise AssertionError(f"unclassified vector entrypoint: {entrypoint!r}")


@pytest.mark.parametrize(
    "item",
    _vector_entries(),
    ids=lambda item: str(item["id"]),
)
def test_conformance_vector_is_executed(
    item: dict[str, object], tmp_path: Path
) -> None:
    vector = _vector(item)
    assert vector["id"] == item["id"]
    entrypoint = vector["entrypoint"]

    if entrypoint == "api":
        parameters = inspect.signature(writer._publish_receipt).parameters
        assert vector["expected_api"] == "no_caller_selected_destination"
        assert set(parameters) == {"repository_root", "raw_bytes", "binding"}
        assert "relative_path" not in parameters
        return

    if entrypoint == "parse":
        with pytest.raises(ReceiptParseError) as caught:
            parse_receipt_bytes(str(vector["raw_payload"]).encode("utf-8"))
        assert vector["expected_exception"] == "ReceiptParseError"
        assert "duplicate JSON object key" in str(caught.value)
        return

    if entrypoint == "writer_authority":
        if item["id"] == "publish_rejected_missing_authority":
            fixture = _UNIT3._make_git_fixture(tmp_path)
            value, _ = _UNIT3._full_receipt(fixture)
            document = _UNIT3._receipt_document(value)
            destination_parent = fixture.root / "output" / "receipts" / "t139"
            destination_parent.mkdir(parents=True)
            with pytest.raises(writer.VectorAuthorityUnavailableError) as caught:
                writer._publish_receipt(
                    repository_root=fixture.root,
                    raw_bytes=document.raw_bytes,
                    binding=fixture.binding,
                )
            assert vector["expected_code"] == caught.value.reason_code
            assert not any(destination_parent.iterdir())
            return
        if item["id"] == "writer_publish_sealed_authority":
            fixture = _PATH._authority_fixture(tmp_path)
            value, _ = _UNIT3._full_receipt(fixture)
            document = _UNIT3._receipt_document(value)
            destination = fixture.root / writer._destination(document)
            destination.parent.mkdir(parents=True)
            writer._publish_receipt(
                repository_root=fixture.root,
                raw_bytes=document.raw_bytes,
                binding=fixture.binding,
            )
            assert destination.read_bytes() == document.raw_bytes
            with pytest.raises(SafeIOError) as caught:
                writer._publish_receipt(
                    repository_root=fixture.root,
                    raw_bytes=document.raw_bytes,
                    binding=fixture.binding,
                )
            assert caught.value.errno == errno.EEXIST
            assert destination.read_bytes() == document.raw_bytes
            return
        root = _PATH._clone_repository(tmp_path)
        manifest_ref = approval.T139_APPROVAL_MANIFEST_REF
        projection_ref = approval.T139_VECTOR_APPROVAL_REF
        if item["id"] == "manifest_index_ref_mismatch":
            manifest_ref = _PATH._mutated_ref(
                root,
                manifest_ref,
                ("namespaces", "conformance_vectors", "namespace_projection", "sha256"),
                "f" * 64,
            )
        elif item["id"] == "payload_index_ref_mismatch":
            projection_ref = _PATH._mutated_ref(
                root,
                projection_ref,
                ("conformance_vector_index", "approval", "sha256"),
                "f" * 64,
            )
        elif item["id"] == "historical_index_blob_replaced":
            approved = _manifest._load_approved_manifest(root)
            original = read_pinned_blob(root, approved.vector_index)
            (root / approved.vector_index.path).write_bytes(original + b"\n")
            commit = _UNIT3._commit(root, "replace historical index", approved.vector_index.path)
            (root / approved.vector_index.path).write_bytes(original)
            bad_ref = BlobRef(approved.vector_index.path, commit, approved.vector_index.sha256)
            with pytest.raises(_manifest.VectorAuthorityMismatchError) as caught:
                _manifest._require_vector_index(os.fspath(root), bad_ref, bad_ref)
            assert vector["expected_code"] == caught.value.reason_code
            assert not (root / "output" / "receipts" / "t139").exists()
            return
        else:
            raise AssertionError(item["id"])
        with pytest.raises(_manifest.VectorAuthorityMismatchError) as caught:
            _manifest._load_approved_manifest_from_refs(
                os.fspath(root), manifest_ref=manifest_ref, projection_ref=projection_ref
            )
        assert vector["expected_code"] == caught.value.reason_code
        assert not (root / "output" / "receipts" / "t139").exists()
        return

    if entrypoint == "safe_io":
        fixture = _PATH._authority_fixture(tmp_path)
        value, _ = _UNIT3._full_receipt(fixture)
        document = _UNIT3._receipt_document(value)
        destination = fixture.root / writer._destination(document)
        destination.parent.mkdir(parents=True)
        destination.write_bytes(b"existing receipt\n")
        with pytest.raises(SafeIOError) as caught:
            writer._publish_receipt(
                repository_root=fixture.root,
                raw_bytes=document.raw_bytes,
                binding=fixture.binding,
            )
        assert vector["expected_exception"] == "SafeIOError"
        assert caught.value.errno == errno.EEXIST
        assert destination.read_bytes() == b"existing receipt\n"
        return

    fixture = _UNIT3._make_git_fixture(tmp_path)
    value, schema = _UNIT3._full_receipt(fixture)
    _assert_semantic_vector(fixture, value, schema, item, vector)


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-q"]))
