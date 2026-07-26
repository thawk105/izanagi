# -*- coding: utf-8 -*-
"""T-080 receipt/adapter core の hermetic 回帰。"""
from __future__ import annotations

import contextlib
import copy
import ast
import hashlib
import io
import json
import os
import subprocess
import sys
import tempfile
import traceback
import unittest
from pathlib import Path
from typing import Callable


_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(_ROOT))

from orchestrator.campaign import s8b_holdout_freeze as holdout_module
from orchestrator.campaign import t080_freeze_migration as migration


def _run_git(root: Path, *args: str, input_bytes: bytes | None = None) -> bytes:
    completed = subprocess.run(
        ["git", *args], cwd=root, input=input_bytes,
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True,
    )
    return completed.stdout


def _init_repo(root: Path) -> str:
    _run_git(root, "init", "-q")
    _run_git(root, "config", "user.name", "T080 Test")
    _run_git(root, "config", "user.email", "t080@example.invalid")
    (root / "base.txt").write_text("base\n", encoding="utf-8")
    _run_git(root, "add", "base.txt")
    _run_git(root, "commit", "-q", "-m", "base", "-m", "AI-Agent: none")
    return _run_git(root, "rev-parse", "HEAD").decode().strip()


def _commit_all(root: Path, message: str) -> str:
    _run_git(root, "add", "-A")
    _run_git(root, "commit", "-q", "-m", message, "-m", "AI-Agent: none")
    return _run_git(root, "rev-parse", "HEAD").decode().strip()


def _valid_receipt(*, active: bool = True):
    basis = "a" * 40
    repins = [
        {
            "artifact": spec.artifact,
            "json_pointer": spec.json_pointer,
            "path": spec.path,
            "recorded_sha256": spec.recorded_sha256,
            "migration_blob_sha256": "b" * 64,
        }
        for spec in migration.SOURCE_REPIN_SPECS
    ]
    metadata = [
        {
            "artifact": spec.artifact,
            "json_pointer": spec.json_pointer,
            "path": spec.path,
            "recorded_sha256": spec.recorded_sha256,
            "migration_blob_sha256": "c" * 64,
            "disposition": "metadata-only",
        }
        for spec in migration.METADATA_SPECS
    ]
    report = [
        {
            **record,
            "provenance": {
                "status": "provenance_unverified", "commit": None,
                "distance_from_basis": None,
            },
            "diff_summary": {
                "status": "diff_unverified", "path": record["path"],
                "old_line_count": None, "new_line_count": 1,
                "added_lines": None, "deleted_lines": None,
            },
        }
        for record in repins
    ]
    return {
        "schema_version": migration.SCHEMA_VERSION,
        "migration_id": migration.MIGRATION_ID,
        "migration_basis_commit": basis,
        "artifacts": {
            "known_axes": {
                "path": migration.KNOWN_AXES_REL,
                "raw_sha256": migration.KNOWN_AXES_RAW_SHA256,
                "recorded_frozen_at_head": migration.KNOWN_AXES_RECORDED_HEAD,
            },
            "holdout": {
                "path": migration.HOLDOUT_REL,
                "raw_sha256": migration.HOLDOUT_RAW_SHA256,
                "recorded_frozen_at_head": migration.HOLDOUT_RECORDED_HEAD,
            },
        },
        "source_repins": repins,
        "metadata_fields": metadata,
        "reconstruction": {
            "known_axes": {
                "status": "pass", "projected_document_sha256": "d" * 64,
                "rebuilt_document_sha256": "d" * 64,
            },
            "holdout": {
                "status": "pass", "projected_document_sha256": "e" * 64,
                "live_scan_sha256": "f" * 64,
            },
        },
        "repin_report": report,
        "confirmed_by": "human.test" if active else None,
        "confirmed_at": "2026-07-22T12:34:56Z" if active else None,
    }


def _expect_reason(call, reason: str) -> migration.MigrationError:
    try:
        call()
    except migration.MigrationError as exc:
        assert exc.reason == reason, (exc.reason, reason, exc)
        return exc
    raise AssertionError(f"{reason} の拒否が発生しなかった")


def test_schema_accepts_exact_active_and_draft_shapes():
    migration.validate_receipt_schema(_valid_receipt(), confirmation="active")
    migration.validate_receipt_schema(_valid_receipt(active=False), confirmation="draft")


def test_strict_json_rejects_duplicate_nan_bom_non_utf8_and_nonobject():
    cases = (
        b'{"a":1,"a":2}', b'{"a":NaN}', b'{"a":Infinity}',
        b'\xef\xbb\xbf{}', b'\xff', b'[]',
    )
    for raw in cases:
        _expect_reason(lambda raw=raw: migration._strict_load(raw), "receipt.schema_invalid")


def test_canonical_rejects_pretty_trailing_newline_and_accepts_exact_bytes():
    doc = _valid_receipt()
    raw = migration._canonical_bytes(doc)
    assert migration._load_canonical(raw) == doc
    for bad in (json.dumps(doc).encode(), raw + b"\n"):
        _expect_reason(lambda bad=bad: migration._load_canonical(bad), "receipt.canonical_mismatch")


def test_schema_rejects_unknown_key_confirmation_and_count_errors():
    unknown = _valid_receipt()
    unknown["note"] = "free text"
    _expect_reason(lambda: migration.validate_receipt_schema(unknown), "receipt.schema_invalid")

    mixed = _valid_receipt()
    mixed["confirmed_at"] = None
    _expect_reason(lambda: migration.validate_receipt_schema(mixed), "receipt.confirmation_invalid")
    for value in ("a b", "", "x" * 65, "軸"):
        bad = _valid_receipt()
        bad["confirmed_by"] = value
        _expect_reason(lambda bad=bad: migration.validate_receipt_schema(bad), "receipt.confirmation_invalid")
    for value in ("2026-07-22T12:34:56+00:00", "2026-07-22T12:34:56.0Z", "2026-02-30T00:00:00Z"):
        bad = _valid_receipt()
        bad["confirmed_at"] = value
        _expect_reason(lambda bad=bad: migration.validate_receipt_schema(bad), "receipt.confirmation_invalid")

    for field in ("source_repins", "metadata_fields", "repin_report"):
        bad = _valid_receipt()
        bad[field] = bad[field][:-1]
        _expect_reason(lambda bad=bad: migration.validate_receipt_schema(bad), "receipt.schema_invalid")


def test_rfc6901_escape_array_and_canonical_roundtrip():
    value = {"a/b": {"m~n": [{"sha256": "x"}]}}
    pointer = "/a~1b/m~0n/0/sha256"
    assert migration._resolve_pointer(value, pointer) == "x"
    migration._set_pointer(value, pointer, "y")
    assert migration._resolve_pointer(value, pointer) == "y"
    for bad in ("a/b", "/a~2b", "/a~", "/a~01b", "/a~1b/m~0n/00/sha256"):
        _expect_reason(lambda bad=bad: migration._resolve_pointer(value, bad), "receipt.repin_invalid")


def test_repin_duplicate_missing_surplus_and_report_cross_field_are_rejected():
    duplicate = _valid_receipt()
    duplicate["source_repins"][1] = copy.deepcopy(duplicate["source_repins"][0])
    _expect_reason(lambda: migration.validate_receipt_schema(duplicate), "receipt.repin_invalid")

    surplus = _valid_receipt()
    surplus["source_repins"].append(copy.deepcopy(surplus["source_repins"][-1]))
    _expect_reason(lambda: migration.validate_receipt_schema(surplus), "receipt.schema_invalid")

    cross = _valid_receipt()
    cross["repin_report"][0]["migration_blob_sha256"] = "0" * 64
    _expect_reason(lambda: migration.validate_receipt_schema(cross), "receipt.repin_invalid")


def test_structural_schema_then_fixed_closure_and_scan_both_reject_axis_payload():
    doc = _valid_receipt()
    # test source 自身を live scan の holdout conjunction で汚染しないよう token を分割する。
    malicious = (
        "evidence/" + "ycsb_" + "rratio=8" + "0 "
        + "ycsb_" + "zipf_skew=0" + ".9 " + "ycsb_" + "rmw=" + "0"
    )
    doc["source_repins"][0]["path"] = malicious
    doc["repin_report"][0]["path"] = malicious
    doc["repin_report"][0]["diff_summary"]["path"] = malicious
    migration.validate_receipt_structure(doc)
    _expect_reason(lambda: migration.validate_receipt_schema(doc), "receipt.repin_invalid")
    with tempfile.TemporaryDirectory(prefix="izanagi_t080_scan_") as temp:
        root = Path(temp)
        path = root / "receipt.json"
        path.write_bytes(migration._canonical_bytes(doc))
        report = holdout_module.search_repository(root, files=[path])
    assert report["holdouts"]["rr80"]["conjunction_hits"] == ["receipt.json"]
    try:
        holdout_module._assert_search_pass(report)
    except holdout_module.FreezeError as exc:
        assert "rr80: holdout hit 1 件" in str(exc)
    else:
        raise AssertionError("悪性 receipt の live scan が拒否されなかった")


def _synthetic_known_closure():
    doc = {"entries": {}}
    filler_index = 0

    def record(path: str, digest: str):
        return {"path": path, "sha256": digest}

    def ensure(pointer: str, value):
        nonlocal filler_index
        tokens = migration._pointer_tokens(pointer)
        assert tokens[0] == "entries" and tokens[3] == "sources" and tokens[5] == "sha256"
        workload, variant, index = tokens[1], tokens[2], int(tokens[4])
        variant_doc = doc["entries"].setdefault(workload, {}).setdefault(variant, {})
        sources = variant_doc.setdefault("sources", [])
        while len(sources) <= index:
            sources.append(record(f"filler/pre-{filler_index}.txt", "1" * 64))
            filler_index += 1
        sources[index] = value

    changed_paths = set()
    for spec in migration.SOURCE_REPIN_SPECS[:-1]:
        ensure(spec.json_pointer, record(spec.path, spec.recorded_sha256))
        changed_paths.add(spec.path)
    current = sum(1 for _ in migration._iter_known_sources(doc) if "/sources/" in _[0])
    doc["entries"]["filler"] = {
        "extra": {"sources": [
            record(f"filler/extra-{index}.txt", "1" * 64)
            for index in range(63 - current)
        ]}
    }
    return doc, changed_paths


def test_source_closure_exact_12_changed_51_unchanged_and_count_negatives():
    doc, changed_paths = _synthetic_known_closure()
    changed, unchanged = migration._classify_source_closure(
        doc, lambda path: "2" * 64 if path in changed_paths else "1" * 64,
    )
    assert len(changed) == 12 and len(unchanged) == 51

    missing = copy.deepcopy(doc)
    missing["entries"]["filler"]["extra"]["sources"].pop()
    _expect_reason(
        lambda: migration._classify_source_closure(
            missing, lambda path: "2" * 64 if path in changed_paths else "1" * 64,
        ),
        "known_axes.source_closure",
    )
    surplus = copy.deepcopy(doc)
    surplus["entries"]["filler"]["extra"]["sources"].append(
        {"path": "filler/surplus.txt", "sha256": "1" * 64}
    )
    _expect_reason(
        lambda: migration._classify_source_closure(
            surplus, lambda path: "2" * 64 if path in changed_paths else "1" * 64,
        ),
        "known_axes.source_closure",
    )


def test_draft_reconstruction_deep_equality_is_independent_m01_kill():
    legacy = {
        "frozen_at_head": "a" * 40, "ccbench_pin": "b" * 40,
        "python_version": "3.11", "generator": {"path": "g.py", "sha256": "c" * 64},
        "reference_values_note": "legacy",
    }

    def builder(**_kwargs):
        rebuilt = copy.deepcopy(legacy)
        rebuilt["reference_values_note"] = "mutated"
        return rebuilt

    _expect_reason(
        lambda: migration._draft_reconstruct_known_axes(
            legacy, (), builder=builder, pairing=lambda _doc: None,
        ),
        "known_axes.reconstruction_equality",
    )


def _repo_with_receipt() -> tuple[tempfile.TemporaryDirectory, Path, str, bytes]:
    temp = tempfile.TemporaryDirectory(prefix="izanagi_t080_state_")
    root = Path(temp.name)
    _init_repo(root)
    path = root / migration.RECEIPT_REL
    path.parent.mkdir(parents=True)
    raw = b"{}"
    path.write_bytes(raw)
    introduction = _commit_all(root, "introduce receipt")
    return temp, root, introduction, raw


def _repo_with_schema_valid_receipt(
    *, extra_path: bool = False, trailer: str = "AI-Agent: none",
    derivation_ready: bool = False,
    mutate_receipt: Callable[[dict], None] | None = None,
):
    temp = tempfile.TemporaryDirectory(prefix="izanagi_t080_active_")
    root = Path(temp.name)
    basis = _init_repo(root)
    known = holdout = None
    if derivation_ready:
        derivation_paths = {
            *(spec.path for spec in migration.SOURCE_REPIN_SPECS),
            *(spec.path for spec in migration.METADATA_SPECS),
        }
        assert len(derivation_paths) == 6
        basis_paths = {
            migration.KNOWN_AXES_REL,
            migration.HOLDOUT_REL,
            *derivation_paths,
        }
        for rel in sorted(basis_paths):
            target = root / rel
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes((_ROOT / rel).read_bytes())
        known = migration._strict_load(
            (root / migration.KNOWN_AXES_REL).read_bytes(), what="known_axes",
        )
        holdout = migration._strict_load(
            (root / migration.HOLDOUT_REL).read_bytes(), what="holdout",
        )
        _run_git(root, "add", "--", *sorted(basis_paths))
        _run_git(
            root, "update-index", "--add", "--cacheinfo",
            f"160000,{known['ccbench_pin']},{migration.CCBENCH_REL}",
        )
        _run_git(root, "commit", "-q", "-m", "derivation basis", "-m", "AI-Agent: none")
        basis = _run_git(root, "rev-parse", "HEAD").decode().strip()
    receipt = _valid_receipt()
    receipt["migration_basis_commit"] = basis
    if derivation_ready:
        assert known is not None and holdout is not None
        derived = migration._derive_deterministic_fields(receipt, known, holdout, root)
        for field in ("artifacts", "source_repins", "metadata_fields", "repin_report"):
            receipt[field] = copy.deepcopy(derived[field])
        for artifact in ("known_axes", "holdout"):
            receipt["reconstruction"][artifact].update(
                copy.deepcopy(derived["reconstruction"][artifact])
            )
    if mutate_receipt is not None:
        mutate_receipt(receipt)
    path = root / migration.RECEIPT_REL
    path.parent.mkdir(parents=True)
    path.write_bytes(migration._canonical_bytes(receipt))
    _run_git(root, "add", migration.RECEIPT_REL)
    if extra_path:
        (root / "extra.txt").write_text("extra\n", encoding="utf-8")
        _run_git(root, "add", "extra.txt")
    _run_git(root, "commit", "-q", "-m", "introduce receipt", "-m", trailer)
    return temp, root


def _patch_full_gate_to_pass():
    names = (
        "_load_artifact", "_validate_repin_report_git", "_validate_positive_control",
        "_verify_ccbench_current", "_verify_ccbench_basis_from_receipt",
        "_verify_known_closure", "_verify_holdout_closure", "_verify_metadata_closure",
        "_verify_reconstruction_static",
        "_verify_receipt_derivation", "_verify_known_schema", "_verify_known_pairing",
        "_verify_holdout_live_scan",
    )
    original = {name: getattr(migration, name) for name in names}
    migration._load_artifact = lambda *_args, **_kwargs: (b"{}", {})
    migration._validate_repin_report_git = lambda *_args, **_kwargs: None
    migration._validate_positive_control = lambda *_args, **_kwargs: None
    migration._verify_ccbench_current = lambda *_args, **_kwargs: None
    migration._verify_ccbench_basis_from_receipt = lambda *_args, **_kwargs: None
    migration._verify_known_closure = lambda *_args, **_kwargs: None
    migration._verify_holdout_closure = lambda *_args, **_kwargs: None
    migration._verify_metadata_closure = lambda *_args, **_kwargs: None
    migration._verify_reconstruction_static = lambda *_args, **_kwargs: None
    migration._verify_receipt_derivation = lambda *_args, **_kwargs: None
    migration._verify_known_schema = lambda *_args, **_kwargs: None
    migration._verify_known_pairing = lambda *_args, **_kwargs: None
    migration._verify_holdout_live_scan = lambda *_args, **_kwargs: {}
    return original


def test_production_has_no_cross_module_attribute_assignment_f1():
    source = Path(migration.__file__).read_text(encoding="utf-8")
    tree = ast.parse(source)
    forbidden = []
    for node in ast.walk(tree):
        targets = []
        if isinstance(node, (ast.Assign, ast.AnnAssign, ast.AugAssign)):
            targets = node.targets if isinstance(node, ast.Assign) else [node.target]
        for target in targets:
            if isinstance(target, ast.Attribute):
                owner = target.value
                if isinstance(owner, ast.Name) and owner.id.endswith("_module"):
                    forbidden.append((owner.id, target.attr, node.lineno))
    assert forbidden == []
    assert "_verify_live_and_static_documents" not in source


def test_deterministic_fields_and_reconstruction_rerun_reject_mismatch_f2():
    receipt = _valid_receipt()
    expected = {
        field: copy.deepcopy(receipt[field])
        for field in ("artifacts", "source_repins", "metadata_fields", "repin_report")
    }
    expected["reconstruction"] = {
        "known_axes": {
            "projected_document_sha256": "d" * 64,
            "rebuilt_document_sha256": "d" * 64,
        },
        "holdout": {"projected_document_sha256": "e" * 64},
    }
    migration._assert_deterministic_fields(receipt, expected)
    receipt["repin_report"][0]["diff_summary"]["new_line_count"] = 2
    _expect_reason(
        lambda: migration._assert_deterministic_fields(receipt, expected),
        "receipt.derivation_mismatch",
    )

    stored = {
        "source_repins": [], "metadata_fields": [],
        "reconstruction": {
            "known_axes": {"status": "pass", "projected_document_sha256": "1" * 64,
                           "rebuilt_document_sha256": "1" * 64},
            "holdout": {"status": "pass", "projected_document_sha256": "2" * 64,
                        "live_scan_sha256": "3" * 64},
        },
    }
    originals = migration._draft_reconstruct_known_axes, migration._draft_reconstruct_holdout
    rerun_known = copy.deepcopy(stored["reconstruction"]["known_axes"])
    rerun_holdout = copy.deepcopy(stored["reconstruction"]["holdout"])
    try:
        migration._draft_reconstruct_known_axes = lambda *_args, **_kwargs: copy.deepcopy(rerun_known)
        migration._draft_reconstruct_holdout = lambda *_args, **_kwargs: copy.deepcopy(rerun_holdout)
        migration._rerun_draft_reconstruction(stored, {}, {}, Path("."))
        stored["reconstruction"]["holdout"]["live_scan_sha256"] = "4" * 64
        _expect_reason(
            lambda: migration._rerun_draft_reconstruction(stored, {}, {}, Path(".")),
            "receipt.reconstruction_invalid",
        )
    finally:
        migration._draft_reconstruct_known_axes, migration._draft_reconstruct_holdout = originals


def test_public_gate_rejects_tampered_holdout_projected_hash_t091():
    mutation_calls = 0

    def mutate_receipt(receipt: dict) -> None:
        nonlocal mutation_calls
        mutation_calls += 1
        reconstruction = receipt["reconstruction"]["holdout"]
        original = reconstruction["projected_document_sha256"]
        replacement = "1" if original[0] == "0" else "0"
        reconstruction["projected_document_sha256"] = replacement + original[1:]

    temp, root = _repo_with_schema_valid_receipt(
        derivation_ready=True, mutate_receipt=mutate_receipt,
    )
    originals = _patch_full_gate_to_pass()
    try:
        for name in (
            "_load_artifact", "_validate_repin_report_git",
            "_verify_reconstruction_static", "_verify_receipt_derivation",
            "_verify_ccbench_basis_from_receipt", "_verify_known_schema",
            "_verify_known_pairing", "_verify_holdout_closure",
            "_verify_metadata_closure",
        ):
            setattr(migration, name, originals[name])
        # 下の 4 gate は stub のままなので、それらとの gate 間相互作用は未検証である:
        # _verify_known_closure / _validate_positive_control /
        # _verify_ccbench_current / _verify_holdout_live_scan。
        # 以下の ordered 1-tuple は「この 4 gate が pass 固定」の条件下での保証であり、
        # 「全 gate を検証した」ことを意味しない。
        result = migration.verify_receipt(root=root)
        assert mutation_calls == 1
        assert result.refusals == (
            "migration-receipt-verify: [receipt.derivation_mismatch] "
            "reconstruction.holdout.projected_document_sha256 が H_mig 再導出値と不一致",
        )
        assert result.state == "invalid"
        assert result.t080_freeze_migration_observation is None
    finally:
        _restore_functions(originals)
        temp.cleanup()


def test_live_scan_evidence_ignores_only_scope_counters_not_acceptance_f2():
    report = {
        "match_convention": "m", "search": {"file_count": 1},
        "holdouts": {"rr80": {"conjunction_hits": []}},
        "positive_control": {"hit_count": 1},
    }
    scope_only = copy.deepcopy(report)
    scope_only["search"]["file_count"] = 2
    assert migration._live_scan_sha256(report) == migration._live_scan_sha256(scope_only)
    acceptance = copy.deepcopy(report)
    acceptance["holdouts"]["rr80"]["conjunction_hits"] = ["known.txt"]
    assert migration._live_scan_sha256(report) != migration._live_scan_sha256(acceptance)


def test_live_scan_is_bound_to_frozen_expressions_match_convention_and_candidates_g1():
    holdout = json.loads((_ROOT / migration.HOLDOUT_REL).read_text(encoding="utf-8"))
    report = {
        "match_convention": holdout["match_convention"],
        "holdouts": {
            name: {
                "candidate_id": entry["candidate_id"],
                "expressions": copy.deepcopy(entry["unknownness_check"]["expressions"]),
                "conjunction_hits": [],
            }
            for name, entry in holdout["holdouts"].items()
        },
        "positive_control": {"hit_count": 1},
    }
    original = holdout_module.search_repository
    current = copy.deepcopy(report)
    try:
        holdout_module.search_repository = lambda _root: copy.deepcopy(current)
        migration._verify_holdout_live_scan(_ROOT, holdout)
        mutations = (
            lambda value: value.update(match_convention="drifted"),
            lambda value: value["holdouts"].pop("rr20"),
            lambda value: value["holdouts"]["rr80"].update(candidate_id="H2"),
            lambda value: value["holdouts"]["rr80"]["expressions"].update(rratio="drifted"),
        )
        for mutate in mutations:
            current = copy.deepcopy(report)
            mutate(current)
            _expect_reason(
                lambda: migration._verify_holdout_live_scan(_ROOT, holdout),
                "holdout.unknownness_layer2",
            )
    finally:
        holdout_module.search_repository = original


def test_gate_normalizes_unexpected_check_exceptions_and_continues_g5():
    temp, root = _repo_with_schema_valid_receipt()
    originals = _patch_full_gate_to_pass()
    reached = []
    try:
        migration._validate_positive_control = lambda *_args: (_ for _ in ()).throw(OSError("positive"))
        migration._verify_holdout_live_scan = lambda *_args: (_ for _ in ()).throw(
            holdout_module.FreezeError("scan")
        )
        migration._verify_ccbench_current = lambda *_args: (_ for _ in ()).throw(ValueError("ccbench"))
        migration._verify_known_schema = lambda *_args: reached.append("known-schema")
        result = migration.verify_receipt(root=root)
        reasons = {item.split("[", 1)[1].split("]", 1)[0] for item in result.refusals}
        assert reasons == {
            "holdout.positive_control",
            "holdout.unknownness_layer2",
            "known_axes.ccbench_current",
        }
        assert reached == ["known-schema"]
        assert result.state == "invalid"
    finally:
        _restore_functions(originals)
        temp.cleanup()


def _restore_functions(original):
    for name, value in original.items():
        setattr(migration, name, value)


def test_state_never_issued_and_present_invalid():
    with tempfile.TemporaryDirectory(prefix="izanagi_t080_never_") as temp:
        root = Path(temp)
        _init_repo(root)
        assert migration.inspect_receipt_history(root=root).state == "never-issued"
        path = root / migration.RECEIPT_REL
        path.parent.mkdir(parents=True)
        path.write_bytes(b"{}")
        assert migration.inspect_receipt_history(root=root).state == "invalid"


def test_state_clean_introduction_is_invalid_until_full_schema_passes():
    temp, root, _introduction, _raw = _repo_with_receipt()
    try:
        result = migration.inspect_receipt_history(root=root)
        assert result.state == "invalid"
        assert result.refusals[0].startswith("migration-receipt-verify: [receipt.")
    finally:
        temp.cleanup()


def test_state_active_valid_after_schema_topology_and_all_independent_gates():
    temp, root = _repo_with_schema_valid_receipt()
    original = _patch_full_gate_to_pass()
    try:
        result = migration.verify_receipt(root=root)
        assert result.state == "active-valid"
        assert result.refusals == ()
        assert result.t080_freeze_migration_observation is not None
        assert len(result.t080_freeze_migration_observation["items"]) == 17
    finally:
        _restore_functions(original)
        temp.cleanup()


def test_invalid_r_topology_keeps_independent_ccbench_refusal_j4():
    temp, root = _repo_with_schema_valid_receipt(extra_path=True)
    original = _patch_full_gate_to_pass()
    try:
        history = migration.inspect_receipt_history(root=root)
        assert history.state == "invalid" and len(history.refusals) == 1
        assert "receipt.introduction_diff" in history.refusals[0]
        migration._verify_ccbench_current = lambda *_args, **_kwargs: (_ for _ in ()).throw(
            migration.MigrationError("known_axes.ccbench_current", "mismatch")
        )
        result = migration.verify_receipt(root=root)
        assert result.state == "invalid"
        assert any("receipt.introduction_diff" in refusal for refusal in result.refusals)
        assert any("known_axes.ccbench_current" in refusal for refusal in result.refusals)
    finally:
        _restore_functions(original)
        temp.cleanup()


def test_invalid_r_trailer_is_rejected_exactly():
    temp, root = _repo_with_schema_valid_receipt(trailer="AI-Agent: codex")
    try:
        result = migration.inspect_receipt_history(root=root)
        assert result.state == "invalid"
        assert "receipt.user_commit_trailer" in result.refusals[0]
    finally:
        temp.cleanup()


def test_state_post_r_delete_is_issued_but_missing():
    temp, root, _introduction, _raw = _repo_with_receipt()
    try:
        (root / migration.RECEIPT_REL).unlink()
        _commit_all(root, "delete receipt")
        assert migration.inspect_receipt_history(root=root).state == "issued-but-missing"
    finally:
        temp.cleanup()


def test_state_modify_then_revert_is_issued_but_missing():
    temp, root, _introduction, raw = _repo_with_receipt()
    try:
        path = root / migration.RECEIPT_REL
        path.write_bytes(b'{"changed":true}')
        _commit_all(root, "modify receipt")
        path.write_bytes(raw)
        _commit_all(root, "revert receipt bytes")
        result = migration.inspect_receipt_history(root=root)
        assert result.state == "issued-but-missing"
        assert len(result.refusals) == 2
        assert "receipt.history_mutated" in result.refusals[0]
        assert "receipt.schema_invalid" in result.refusals[1]
        assert result.t080_freeze_migration_observation is None
    finally:
        temp.cleanup()


def test_state_delete_then_readd_same_bytes_is_issued_but_missing():
    temp, root, _introduction, raw = _repo_with_receipt()
    try:
        path = root / migration.RECEIPT_REL
        path.unlink()
        _commit_all(root, "delete receipt")
        path.write_bytes(raw)
        _commit_all(root, "readd receipt")
        result = migration.inspect_receipt_history(root=root)
        assert result.state == "issued-but-missing"
        assert "multiple_introduction" in result.refusals[0]
    finally:
        temp.cleanup()


def test_state_same_blob_mode_change_and_diff_tree_merge_edges_are_rejected_f4():
    temp, root, _introduction, _raw = _repo_with_receipt()
    try:
        path = root / migration.RECEIPT_REL
        path.chmod(0o755)
        _commit_all(root, "change receipt mode")
        result = migration.inspect_receipt_history(root=root)
        assert result.state == "issued-but-missing"
        assert any("receipt.history_mutated" in refusal for refusal in result.refusals)
    finally:
        temp.cleanup()

    captured = []
    original = migration._git_text
    try:
        migration._git_text = lambda args, _root: captured.append(tuple(args)) or ""
        assert migration._history_touches_path("a" * 40, migration.RECEIPT_REL, Path(".")) is False
    finally:
        migration._git_text = original
    assert captured and "-m" in captured[0] and "-r" in captured[0]


def test_issued_but_missing_continues_independent_checks_and_observation_is_null_f4():
    temp, root = _repo_with_schema_valid_receipt()
    original = _patch_full_gate_to_pass()
    try:
        (root / migration.RECEIPT_REL).unlink()
        migration._verify_holdout_live_scan = lambda *_args, **_kwargs: (_ for _ in ()).throw(
            migration.MigrationError("holdout.unknownness_layer2", "hit")
        )
        result = migration.verify_receipt(root=root)
        assert result.state == "issued-but-missing"
        assert len(result.refusals) == 2
        assert "receipt.issued_but_missing" in result.refusals[0]
        assert "holdout.unknownness_layer2" in result.refusals[1]
        assert result.t080_freeze_migration_observation is None
        assert result.receipt_raw == migration._canonical_bytes(result.receipt)
    finally:
        _restore_functions(original)
        temp.cleanup()


def test_static_adapter_discards_clean_envelope_when_any_check_refuses_f4():
    known_raw = (migration.ROOT / migration.KNOWN_AXES_REL).read_bytes()
    holdout_raw = (migration.ROOT / migration.HOLDOUT_REL).read_bytes()
    receipt = _valid_receipt()
    resolution = migration.ReceiptResolution(
        "active-valid", (), {"clean": True}, "a" * 40,
        receipt=receipt, receipt_raw=migration._canonical_bytes(receipt),
    )
    original = _patch_full_gate_to_pass()
    try:
        migration._verify_ccbench_current = lambda *_args, **_kwargs: (_ for _ in ()).throw(
            migration.MigrationError("known_axes.ccbench_current", "drift")
        )
        result = migration.static_gate_adapter(
            resolution=resolution, known_raw=known_raw, holdout_raw=holdout_raw,
            root=migration.ROOT,
        )
        assert len(result.refusals) == 1
        assert "known_axes.ccbench_current" in result.refusals[0]
        assert result.t080_freeze_migration_observation is None
    finally:
        _restore_functions(original)


def test_draft_precondition_rejects_head_mismatch_dirty_and_post_r_reissue():
    with tempfile.TemporaryDirectory(prefix="izanagi_t080_draft_basis_") as temp:
        root = Path(temp)
        head = _init_repo(root)
        _expect_reason(
            lambda: migration._capture_draft_basis("f" * 40, root),
            "receipt.basis_invalid",
        )
        (root / "dirty.txt").write_text("dirty\n", encoding="utf-8")
        _expect_reason(
            lambda: migration._capture_draft_basis(head, root),
            "receipt.basis_invalid",
        )

    temp, root, _introduction, _raw = _repo_with_receipt()
    try:
        (root / migration.RECEIPT_REL).unlink()
        head = _commit_all(root, "delete receipt")
        _expect_reason(
            lambda: migration._capture_draft_basis(head, root),
            "receipt.invalid",
        )
    finally:
        temp.cleanup()


def test_draft_precondition_detects_hermetic_submodule_dirty():
    with tempfile.TemporaryDirectory(prefix="izanagi_t080_submodule_source_") as source_temp:
        source = Path(source_temp)
        _init_repo(source)
        with tempfile.TemporaryDirectory(prefix="izanagi_t080_submodule_root_") as root_temp:
            root = Path(root_temp)
            _init_repo(root)
            _run_git(
                root, "-c", "protocol.file.allow=always", "submodule", "add", "-q",
                str(source), migration.CCBENCH_REL,
            )
            head = _commit_all(root, "add submodule")
            (root / migration.CCBENCH_REL / "dirty.txt").write_text("dirty\n", encoding="utf-8")
            _expect_reason(
                lambda: migration._capture_draft_basis(head, root),
                "receipt.basis_invalid",
            )


def test_state_rename_copy_type_change_and_worktree_loss_are_rejected():
    operations = ("rename", "copy", "type", "worktree-missing", "broken-symlink")
    for operation in operations:
        temp, root, _introduction, raw = _repo_with_receipt()
        try:
            path = root / migration.RECEIPT_REL
            if operation == "rename":
                path.rename(path.with_name("renamed.json"))
                _commit_all(root, operation)
            elif operation == "copy":
                (root / "copy.json").write_bytes(raw)
                _commit_all(root, operation)
            elif operation == "type":
                path.unlink()
                path.symlink_to("missing-target")
                _commit_all(root, operation)
            elif operation == "worktree-missing":
                path.unlink()
            else:
                path.unlink()
                path.symlink_to("missing-target")
            assert migration.inspect_receipt_history(root=root).state == "issued-but-missing", operation
        finally:
            temp.cleanup()


def test_hardening_rejects_shallow_replace_graft_and_alternates():
    with tempfile.TemporaryDirectory(prefix="izanagi_t080_source_") as source_temp:
        source = Path(source_temp)
        _init_repo(source)
        (source / "second.txt").write_text("second\n", encoding="utf-8")
        _commit_all(source, "second")
        with tempfile.TemporaryDirectory(prefix="izanagi_t080_shallow_") as clone_parent:
            clone = Path(clone_parent) / "clone"
            subprocess.run(
                ["git", "clone", "-q", "--depth=1", source.as_uri(), str(clone)], check=True,
            )
            _expect_reason(lambda: migration._capture_head(clone), "receipt.git_error")

    factories = ("replace", "graft", "alternate")
    for kind in factories:
        with tempfile.TemporaryDirectory(prefix=f"izanagi_t080_{kind}_") as temp:
            root = Path(temp)
            _init_repo(root)
            (root / "second.txt").write_text("second\n", encoding="utf-8")
            _commit_all(root, "second")
            if kind == "replace":
                _run_git(root, "replace", "HEAD", "HEAD^")
            else:
                git_dir = Path(_run_git(root, "rev-parse", "--git-dir").decode().strip())
                git_dir = git_dir if git_dir.is_absolute() else root / git_dir
                target = git_dir / ("info/grafts" if kind == "graft" else "objects/info/alternates")
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_text("injected\n", encoding="utf-8")
            _expect_reason(lambda root=root: migration._capture_head(root), "receipt.git_error")


def test_git_environment_injection_is_removed():
    with tempfile.TemporaryDirectory(prefix="izanagi_t080_env_") as temp:
        root = Path(temp)
        head = _init_repo(root)
        old = {name: os.environ.get(name) for name in (
            "GIT_DIR", "GIT_WORK_TREE", "GIT_OBJECT_DIRECTORY", "GIT_ALTERNATE_OBJECT_DIRECTORIES",
        )}
        try:
            for name in old:
                os.environ[name] = "/definitely/injected"
            assert migration._capture_head(root) == head
        finally:
            for name, value in old.items():
                if value is None:
                    os.environ.pop(name, None)
                else:
                    os.environ[name] = value


def test_draft_basis_source_bytes_mode_root_and_git_cache_hardening_f3():
    with tempfile.TemporaryDirectory(prefix="izanagi_t080_basis_bytes_") as temp:
        root = Path(temp)
        _init_repo(root)
        source = root / "checker.py"
        source.write_bytes(b"print('basis')\n")
        basis = _commit_all(root, "add checker")
        migration._verify_worktree_basis_files(basis, root, paths=("checker.py",))

        source.write_bytes(b"print('tampered')\n")
        _expect_reason(
            lambda: migration._verify_worktree_basis_files(basis, root, paths=("checker.py",)),
            "receipt.basis_invalid",
        )
        source.write_bytes(b"print('basis')\n")
        source.chmod(0o755)
        _expect_reason(
            lambda: migration._verify_worktree_basis_files(basis, root, paths=("checker.py",)),
            "receipt.basis_invalid",
        )

        child = root / "child"
        child.mkdir()
        _expect_reason(lambda: migration._assert_repository_root(child), "receipt.basis_invalid")

    harden = migration._GIT_HARDEN
    assert "core.fsmonitor=false" in harden
    assert "core.untrackedCache=false" in harden


def test_ccbench_current_and_basis_gitlink_have_independent_reasons_m11_m12():
    with tempfile.TemporaryDirectory(prefix="izanagi_t080_ccbench_source_") as source_temp:
        source = Path(source_temp)
        pin = _init_repo(source)
        with tempfile.TemporaryDirectory(prefix="izanagi_t080_ccbench_root_") as root_temp:
            root = Path(root_temp)
            _init_repo(root)
            _run_git(
                root, "-c", "protocol.file.allow=always", "submodule", "add", "-q",
                str(source), migration.CCBENCH_REL,
            )
            basis = _commit_all(root, "add ccbench")
            migration._verify_ccbench_basis(basis, pin, root)
            _expect_reason(
                lambda: migration._verify_ccbench_basis(basis, "f" * 40, root),
                "known_axes.ccbench_gitlink",
            )

            submodule = root / migration.CCBENCH_REL
            _run_git(submodule, "config", "user.name", "T080 Test")
            _run_git(submodule, "config", "user.email", "t080@example.invalid")
            (submodule / "drift.txt").write_text("drift\n", encoding="utf-8")
            _commit_all(submodule, "drift")
            _expect_reason(
                lambda: migration._verify_ccbench_live(
                    {"migration_basis_commit": basis}, {"ccbench_pin": pin}, root,
                ),
                "known_axes.ccbench_current",
            )


def test_ancestry_missing_nonancestor_ancestor_noncommit_and_git_error():
    with tempfile.TemporaryDirectory(prefix="izanagi_t080_ancestry_") as temp:
        root = Path(temp)
        head = _init_repo(root)
        ancestor = migration._classify_ancestry(head, head, root, artifact="known_axes")
        assert ancestor.status == "ancestor"

        tree = _run_git(root, "rev-parse", "HEAD^{tree}").decode().strip()
        nonancestor_oid = _run_git(
            root, "commit-tree", tree, input_bytes=b"orphan\n\nAI-Agent: none\n",
        ).decode().strip()
        nonancestor = migration._classify_ancestry(nonancestor_oid, head, root, artifact="known_axes")
        assert nonancestor.status == "not-ancestor"

        missing = migration._classify_ancestry("f" * 40, head, root, artifact="known_axes")
        assert missing.status == "missing-commit" and missing.observed is None

        blob = _run_git(root, "hash-object", "-w", "--stdin", input_bytes=b"blob").decode().strip()
        noncommit = migration._classify_ancestry(blob, head, root, artifact="known_axes")
        assert noncommit.status == "object-type-error"
        assert noncommit.refusal_reason == "known_axes.ancestry_object_type"

        git_error = migration._classify_ancestry(head, "e" * 40, root, artifact="known_axes")
        assert git_error.status == "git-error"
        assert git_error.refusal_reason == "known_axes.ancestry_git_error"


def test_repin_report_resolves_nearest_commit_and_numeric_diff_only():
    with tempfile.TemporaryDirectory(prefix="izanagi_t080_report_") as temp:
        root = Path(temp)
        _run_git(root, "init", "-q")
        _run_git(root, "config", "user.name", "T080 Test")
        _run_git(root, "config", "user.email", "t080@example.invalid")
        path = root / "source.py"
        old = b"a\nb\n"
        path.write_bytes(old)
        _commit_all(root, "old")
        path.write_bytes(b"a\nc\nd\n")
        basis = _commit_all(root, "new")
        repin = {
            "artifact": "known_axes", "json_pointer": "/x/sha256", "path": "source.py",
            "recorded_sha256": hashlib.sha256(old).hexdigest(),
            "migration_blob_sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        }
        report = migration._build_repin_report(basis, [repin], root)[0]
        assert report["provenance"]["status"] == "provenance_resolved"
        assert report["provenance"]["distance_from_basis"] == 1
        assert report["diff_summary"] == {
            "status": "diff_resolved", "path": "source.py",
            "old_line_count": 2, "new_line_count": 3,
            "added_lines": 2, "deleted_lines": 1,
        }


def test_artifact_raw_bytes_are_checked_before_semantic_parse_m08():
    with tempfile.TemporaryDirectory(prefix="izanagi_t080_artifact_") as temp:
        root = Path(temp)
        path = root / "artifact.json"
        path.write_bytes(b"{}")
        raw, doc = migration._load_artifact(
            root, "artifact.json",
            "44136fa355b3678a1146ad16f7e8649e94fb4fc21fe77e8310c060f61caaff8a",
            "known_axes.artifact_bytes", "known_axes",
        )
        assert raw == b"{}" and doc == {}
        path.write_bytes(b"{ }")
        _expect_reason(
            lambda: migration._load_artifact(
                root, "artifact.json",
                "44136fa355b3678a1146ad16f7e8649e94fb4fc21fe77e8310c060f61caaff8a",
                "known_axes.artifact_bytes", "known_axes",
            ),
            "known_axes.artifact_bytes",
        )


def test_positive_control_production_literals_are_exact():
    raw = b"ycsb_rratio=50\nycsb_zipf_skew=0.9\nycsb_rmw=0\n"
    assert migration.POSITIVE_CONTROL_PATH == "orchestrator/tests/data/freeze_holdout_positive_control_v1.txt"
    assert migration.POSITIVE_CONTROL_ROOT_KEY == "positive-control/rr50/v1"
    assert hashlib.sha256(raw).hexdigest() == migration.POSITIVE_CONTROL_SHA256


def test_cli_verify_rc_contract_for_refusal_success_and_internal_error():
    with tempfile.TemporaryDirectory(prefix="izanagi_t080_cli_") as temp:
        root = Path(temp)
        _init_repo(root)
        stdout = io.StringIO()
        with contextlib.redirect_stdout(stdout):
            rc = migration.main(["verify", "--path", migration.RECEIPT_REL], root=root)
        assert rc == 2
        assert json.loads(stdout.getvalue())["state"] == "never-issued"

    original = migration.verify_receipt
    try:
        migration.verify_receipt = lambda **_kwargs: migration.ReceiptResolution(
            "active-valid", (), {"ok": True}, "a" * 40,
        )
        stdout = io.StringIO()
        with contextlib.redirect_stdout(stdout):
            assert migration.main(["verify", "--path", migration.RECEIPT_REL]) == 0
        assert json.loads(stdout.getvalue())["state"] == "active-valid"

        migration.verify_receipt = lambda **_kwargs: (_ for _ in ()).throw(RuntimeError("boom"))
        stderr = io.StringIO()
        with contextlib.redirect_stderr(stderr):
            assert migration.main(["verify", "--path", migration.RECEIPT_REL]) == 1
        assert "internal error" in stderr.getvalue()
    finally:
        migration.verify_receipt = original


def test_cli_draft_validate_and_finalize_expected_refusals_return_two():
    with tempfile.TemporaryDirectory(prefix="izanagi_t080_cli_write_") as temp:
        root = Path(temp)
        _init_repo(root)
        commands = (
            ["draft", "--basis", "f" * 40, "--out", migration.DRAFT_REL],
            ["validate-draft", "--path", migration.DRAFT_REL],
            [
                "finalize", "--draft", migration.DRAFT_REL,
                "--confirmed-by", "human", "--confirmed-at", "2026-07-22T00:00:00Z",
                "--out", migration.RECEIPT_REL,
            ],
        )
        for command in commands:
            stdout = io.StringIO()
            with contextlib.redirect_stdout(stdout):
                assert migration.main(command, root=root) == 2
            result = json.loads(stdout.getvalue())
            assert result["state"] == "invalid" and len(result["refusals"]) == 1


def test_history_touches_batch_is_equivalent_to_sequential_any():
    """[T-057] 並行版 `_any_history_touches_path` は逐次 `any(...)` と同値。

    merge・rename・無関係 commit を含む履歴で、全体・部分集合・空集合・単一要素の
    すべてについて逐次版と一致することを固定する。並行化で「触っているのに False」
    (検出力の喪失) や「触っていないのに True」(過剰拒否) になる退行を殺す。
    負例 control として、対象 path を触らない commit だけの部分集合が False になることも要求する。
    """
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp) / "repo"
        root.mkdir()
        _init_repo(root)
        (root / "a.txt").write_text("a1\n", encoding="utf-8")
        c1 = _commit_all(root, "add a")
        (root / "target.txt").write_text("t1\n", encoding="utf-8")
        c2 = _commit_all(root, "add target")
        (root / "a.txt").write_text("a2\n", encoding="utf-8")
        c3 = _commit_all(root, "modify a only")
        _run_git(root, "checkout", "-q", "-b", "side", c1)
        (root / "b.txt").write_text("b1\n", encoding="utf-8")
        c4 = _commit_all(root, "add b on side")
        _run_git(root, "checkout", "-q", "-B", "main", c3)
        _run_git(root, "merge", "-q", "--no-ff", "-m", "merge side", c4)
        c5 = _run_git(root, "rev-parse", "HEAD").decode().strip()
        (root / "target.txt").write_text("t2\n", encoding="utf-8")
        c6 = _commit_all(root, "modify target")
        _run_git(root, "mv", "a.txt", "renamed_a.txt")
        c7 = _commit_all(root, "rename a")

        touching = (c2, c6)
        non_touching = (c1, c3, c4, c5, c7)
        for subset in (
            (),
            (c1,),
            (c2,),
            non_touching,
            touching,
            (c1, c2, c3, c4, c5, c6, c7),
            (c7, c6, c5, c4, c3, c2, c1),
        ):
            expected = any(
                migration._history_touches_path(commit, "target.txt", root)
                for commit in subset
            )
            actual = migration._any_history_touches_path(subset, "target.txt", root)
            assert actual == expected, (subset, actual, expected)
        assert migration._any_history_touches_path(
            non_touching, "target.txt", root) is False
        assert migration._any_history_touches_path(touching, "target.txt", root) is True


def test_cat_blob_memoizes_per_object_without_changing_bytes():
    """[T-057] `_cat_blob` は (root, spec) 単位で memo し、内容を変えない。

    git object は content-addressed なので memo は結果を変えないが、
    「memo が効いていない」(速度退行) と「別 spec の値を返す」(致命的) の両方を殺す。
    """
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp) / "repo"
        root.mkdir()
        _init_repo(root)
        (root / "one.txt").write_text("one\n", encoding="utf-8")
        (root / "two.txt").write_text("two\n", encoding="utf-8")
        _commit_all(root, "add two files")
        oid_one = _run_git(root, "rev-parse", "HEAD:one.txt").decode().strip()
        oid_two = _run_git(root, "rev-parse", "HEAD:two.txt").decode().strip()

        saved_cache = dict(migration._BLOB_CACHE)
        real_git = migration._git
        calls: list[tuple[str, ...]] = []

        def counting(args, git_root, *, stdin=None):
            calls.append(tuple(args))
            return real_git(args, git_root, stdin=stdin)

        migration._BLOB_CACHE.clear()
        migration._git = counting
        try:
            first = migration._cat_blob(oid_one, root)
            second = migration._cat_blob(oid_one, root)
            other = migration._cat_blob(oid_two, root)
        finally:
            migration._git = real_git
            migration._BLOB_CACHE.clear()
            migration._BLOB_CACHE.update(saved_cache)

        assert first == b"one\n" and second == b"one\n", (first, second)
        assert other == b"two\n", other
        blob_calls = [args for args in calls if args[:2] == ("cat-file", "blob")]
        assert len(blob_calls) == 2, blob_calls


def _run():
    fns = [value for name, value in sorted(globals().items())
           if name.startswith("test_") and callable(value)]
    passed = failed = errors = skipped = 0
    for fn in fns:
        try:
            fn()
            passed += 1
        except unittest.SkipTest as exc:
            skipped += 1
            print(f"SKIP {fn.__name__}: {exc}")
        except AssertionError as exc:
            failed += 1
            print(f"FAIL {fn.__name__}: {exc}")
        except Exception:
            errors += 1
            print(f"ERROR {fn.__name__}:")
            traceback.print_exc()
    print(
        f"\n{passed} passed, {skipped} skipped, {failed} failed, "
        f"{errors} errors (of {len(fns)})"
    )
    return 0 if failed == 0 and errors == 0 else 1


if __name__ == "__main__":
    sys.exit(_run())
