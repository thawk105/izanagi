# -*- coding: utf-8 -*-
"""T-080 receipt/adapter core の hermetic 回帰。"""
from __future__ import annotations

import contextlib
import copy
import ast
import collections
import hashlib
import io
import json
import os
import subprocess
import sys
import tempfile
import traceback
import unittest
from unittest import mock
from pathlib import Path
from typing import Callable

import pytest

_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(_ROOT))

from orchestrator.tests.s8b_v2_freeze_fixture import in_sealed_fixture_process
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
        migration._verify_holdout_live_scan = lambda *_args, **_kwargs: (_ for _ in ()).throw(
            holdout_module.FreezeError("scan")
        )
        migration._verify_ccbench_current = lambda *_args: (_ for _ in ()).throw(ValueError("ccbench"))
        migration._verify_known_schema = lambda *_args: reached.append("known-schema")
        result = migration.verify_receipt(root=root)
        reasons = {item.split("[", 1)[1].split("]", 1)[0] for item in result.refusals}
        assert reasons == {
            "holdout.positive_control",
            "holdout.unknownness_layer2",
        }
        assert "t080.live-known-axes-ccbench-current-pin" in {
            marker["check_id"] for marker in result.held_checks
        }
        assert reached == ["known-schema"]
        assert result.state == "invalid"
        reached.clear()
        with mock.patch.object(migration._freeze_hold, "HELD", False):
            released = migration.verify_receipt(root=root)
        released_reasons = {
            item.split("[", 1)[1].split("]", 1)[0]
            for item in released.refusals
        }
        assert released_reasons == {
            "holdout.positive_control",
            "holdout.unknownness_layer2",
            "known_axes.ccbench_current",
        }
        assert reached == ["known-schema"]
        assert released.state == "invalid"
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
        assert not any("known_axes.ccbench_current" in refusal for refusal in result.refusals)
        assert "t080.live-known-axes-ccbench-current-pin" in {
            marker["check_id"] for marker in result.held_checks
        }
        with mock.patch.object(migration._freeze_hold, "HELD", False):
            released = migration.verify_receipt(root=root)
        assert released.state == "invalid"
        assert any(
            "receipt.introduction_diff" in refusal
            for refusal in released.refusals
        )
        assert any(
            "known_axes.ccbench_current" in refusal
            for refusal in released.refusals
        )
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


def test_batched_history_argv_mechanically_excludes_find_copies_harder():
    cheap = (
        "diff-tree", "--stdin", "--root", "--raw", "-m", "-r",
        "--no-renames", "--full-index", "--always", "-z",
    )
    expensive = (
        "diff-tree", "--stdin", "--root", "--raw", "-m", "-r",
        "-M", "-C", "--full-index", "--always", "-z",
    )
    assert migration._BATCH_DIFF_ARGV_CHEAP == cheap
    assert migration._BATCH_DIFF_ARGV_EXPENSIVE == expensive
    assert migration._batched_history_diff_tree_argv(
        detect_renames_and_copies=False,
    ) == cheap
    assert migration._batched_history_diff_tree_argv(
        detect_renames_and_copies=True,
    ) == expensive
    assert "-B" not in cheap and "-B" not in expensive

    forbidden_argvs = (
        expensive + ("--find-copies-harder",),
        expensive + ("-C",),
    )
    for forbidden in forbidden_argvs:
        with mock.patch.object(
            migration, "_batched_history_diff_tree_argv", return_value=forbidden,
        ), mock.patch.object(migration, "_git") as git:
            _expect_reason(
                lambda: migration._run_batched_history_diff_tree(
                    ("a" * 40,),
                    b"target.txt",
                    Path("."),
                    None,
                    detect_renames_and_copies=True,
                ),
                "receipt.git_error",
            )
            git.assert_not_called()


def test_batched_history_runner_rejects_mutated_frozen_argv_before_git():
    mutated = migration._BATCH_DIFF_ARGV_EXPENSIVE + ("-C",)
    with mock.patch.object(
        migration, "_BATCH_DIFF_ARGV_EXPENSIVE", mutated,
    ), mock.patch.object(migration, "_git") as git:
        _expect_reason(
            lambda: migration._run_batched_history_diff_tree(
                ("a" * 40,),
                b"target.txt",
                Path("."),
                None,
                detect_renames_and_copies=True,
            ),
            "receipt.git_error",
        )
        git.assert_not_called()


def test_batched_descendant_mode_change_is_rejected_positive_control():
    """mode/kind/OID batch が same-blob の mode 変化を見落とさない。"""
    temp, root = _repo_with_schema_valid_receipt()
    try:
        path = root / migration.RECEIPT_REL
        path.chmod(0o755)
        _commit_all(root, "change receipt mode after issue")
        result = migration.inspect_receipt_history(root=root)
        assert result.state == "issued-but-missing"
        assert any("receipt.history_mutated" in refusal for refusal in result.refusals)
    finally:
        temp.cleanup()


def test_batched_descendant_exact_copy_is_rejected_positive_control():
    """batch raw diff が receipt blob の別 path exact copy (S3) を見落とさない。"""
    temp, root = _repo_with_schema_valid_receipt()
    try:
        source = root / migration.RECEIPT_REL
        (root / "receipt-copy.json").write_bytes(source.read_bytes())
        _commit_all(root, "copy receipt bytes after issue")
        result = migration.inspect_receipt_history(root=root)
        assert result.state == "issued-but-missing"
        assert any("receipt.history_mutated" in refusal for refusal in result.refusals)
    finally:
        temp.cleanup()


def test_batched_descendant_output_count_mismatch_fails_closed_positive_control():
    """tree または安価側 diff の batch 応答欠落を receipt.git_error に倒す。"""
    for batch_kind in ("tree", "diff"):
        temp, root = _repo_with_schema_valid_receipt()
        original = migration._git
        try:
            (root / "unrelated.txt").write_text("unchanged receipt\n", encoding="utf-8")
            _commit_all(root, "unrelated descendant")

            def truncate_batch(args, repo_root, *, stdin=None):
                out = original(args, repo_root, stdin=stdin)
                if batch_kind == "tree" and list(args) == ["cat-file", "--batch"]:
                    return b""
                if batch_kind == "diff" and list(args[:2]) == ["diff-tree", "--stdin"]:
                    return b""
                return out

            migration._git = truncate_batch
            _expect_reason(
                lambda: migration.inspect_receipt_history(root=root),
                "receipt.git_error",
            )
        finally:
            migration._git = original
            temp.cleanup()


def test_batched_descendant_unchanged_history_is_accepted_positive_control():
    """過剰拒否なら receipt.history_mutated が残るため、正当履歴でその不在を固定する。"""
    temp, root = _repo_with_schema_valid_receipt()
    try:
        (root / "unrelated.txt").write_text("unrelated\n", encoding="utf-8")
        _commit_all(root, "unrelated descendant")
        result = migration.inspect_receipt_history(root=root)
        assert migration._format_refusal(
            migration.RECEIPT_PREFIX, "receipt.history_mutated",
        ) not in result.refusals
    finally:
        temp.cleanup()


def test_batched_descendant_non_utf8_unrelated_path_is_accepted_equivalence_control():
    """raw byte path は decode せず、無関係な履歴として旧 scalar と同じく受理する。"""
    temp, root = _repo_with_schema_valid_receipt()
    try:
        root_raw = os.fsencode(root)
        fd = os.open(
            os.path.join(root_raw, b"unrelated-\xff"),
            os.O_WRONLY | os.O_CREAT | os.O_EXCL,
            0o644,
        )
        os.close(fd)
        _commit_all(root, "unrelated non-UTF-8 path descendant")

        result = migration.inspect_receipt_history(root=root)
        assert result.state == "invalid"
        assert result.refusals == ()
    finally:
        temp.cleanup()


def test_inspect_receipt_history_uses_one_call_per_descendant_batch():
    """全 Git argv と総数が descendant 数に依存せず、scalar 起動へ戻らない。"""
    temp, root = _repo_with_schema_valid_receipt()
    original = migration._git
    try:
        def add_descendants(start, stop):
            for number in range(start, stop):
                (root / f"unrelated-{number}.txt").write_text(
                    f"unrelated {number}\n", encoding="utf-8",
                )
                _commit_all(root, f"unrelated descendant {number}")

        def measure_calls():
            migration._BLOB_CACHE.clear()
            migration._OID_MAP_CACHE.clear()
            receipt_oid = _run_git(
                root, "rev-parse", f"HEAD:{migration.RECEIPT_REL}",
            ).decode("ascii").strip()
            migration._BLOB_CACHE[(str(root), receipt_oid)] = (
                root / migration.RECEIPT_REL
            ).read_bytes()
            calls = []

            def record_git(args, repo_root, *, stdin=None):
                calls.append(tuple(args))
                return original(args, repo_root, stdin=stdin)

            migration._git = record_git
            try:
                result = migration.inspect_receipt_history(root=root)
                assert migration._format_refusal(
                    migration.RECEIPT_PREFIX, "receipt.history_mutated",
                ) not in result.refusals
                return tuple(calls)
            finally:
                migration._git = original

        def normalized_argv(calls):
            return collections.Counter(
                tuple(
                    "<sha1>" if migration._SHA1_RE.fullmatch(arg) else arg
                    for arg in argv
                )
                for argv in calls
            )

        def assert_no_per_commit_calls(calls):
            scalar_raw_diff_tree = tuple(
                argv for argv in calls
                if argv[0] == "diff-tree" and "--raw" in argv and "--stdin" not in argv
            )
            non_batch_cat_file = tuple(
                argv for argv in calls
                if argv[0] == "cat-file"
                and not any(arg.startswith("--batch") for arg in argv[1:])
            )
            assert scalar_raw_diff_tree == ()
            assert non_batch_cat_file == ()

        small_descendants = 3
        large_descendants = 7
        add_descendants(0, small_descendants)
        small_calls = measure_calls()
        add_descendants(small_descendants, large_descendants)
        large_calls = measure_calls()

        assert len(small_calls) == len(large_calls)
        assert normalized_argv(small_calls) == normalized_argv(large_calls)
        assert_no_per_commit_calls(small_calls)
        assert_no_per_commit_calls(large_calls)
    finally:
        migration._git = original
        temp.cleanup()


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
        held = migration.static_gate_adapter(
            resolution=resolution, known_raw=known_raw, holdout_raw=holdout_raw,
            root=migration.ROOT,
        )
        assert held.refusals == ()
        assert held.t080_freeze_migration_observation == {"clean": True}
        assert "t080.static-known-axes-ccbench-current-pin" in {
            marker["check_id"] for marker in held.held_checks
        }
        with mock.patch.object(migration._freeze_hold, "HELD", False):
            result = migration.static_gate_adapter(
                resolution=resolution, known_raw=known_raw,
                holdout_raw=holdout_raw, root=migration.ROOT,
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
        expected = "44136fa355b3678a1146ad16f7e8649e94fb4fc21fe77e8310c060f61caaff8a"
        for what, reason in (
            ("known_axes", "known_axes.artifact_bytes"),
            ("holdout", "holdout.artifact_bytes"),
        ):
            path.write_bytes(b"{}")
            held_checks = []
            raw, doc = migration._load_artifact(
                root, "artifact.json", expected, reason, what,
                held_checks=held_checks,
            )
            assert raw == b"{}" and doc == {}
            assert held_checks[0]["check_id"] == (
                f"t080.live-{what.replace('_', '-')}-artifact-bytes"
            )
            path.write_bytes(b"{ }")
            with mock.patch.object(migration._freeze_hold, "HELD", False):
                _expect_reason(
                    lambda reason=reason, what=what: migration._load_artifact(
                        root, "artifact.json", expected, reason, what,
                    ),
                    reason,
                )


def test_historical_artifact_roots_hold_and_release_positive_control():
    receipt = {"migration_basis_commit": "a" * 40}
    with mock.patch.object(migration, "_basis_blob", return_value=b"{}"), \
            mock.patch.object(migration, "_verify_receipt_derivation"):
        held_checks = migration._verify_historical_receipt_derivation(
            receipt, migration.ROOT,
        )
        assert {marker["check_id"] for marker in held_checks} == {
            "t080.historical-known-axes-artifact-bytes",
            "t080.historical-holdout-artifact-bytes",
        }
        with mock.patch.object(migration._freeze_hold, "HELD", False):
            _expect_reason(
                lambda: migration._verify_historical_receipt_derivation(
                    receipt, migration.ROOT,
                ),
                "receipt.derivation_mismatch",
            )


def test_static_adapter_artifact_roots_hold_and_release_positive_control():
    known_raw = (migration.ROOT / migration.KNOWN_AXES_REL).read_bytes() + b" "
    holdout_raw = (migration.ROOT / migration.HOLDOUT_REL).read_bytes() + b" "
    receipt = copy.deepcopy(_valid_receipt())
    receipt["artifacts"]["holdout"]["raw_sha256"] = hashlib.sha256(
        holdout_raw,
    ).hexdigest()
    resolution = migration.ReceiptResolution(
        "active-valid", (), {"clean": True}, "a" * 40, receipt=receipt,
    )
    original = _patch_full_gate_to_pass()
    try:
        held = migration.static_gate_adapter(
            resolution=resolution, known_raw=known_raw,
            holdout_raw=holdout_raw, root=migration.ROOT,
        )
        assert held.refusals == ()
        assert {
            "t080.static-known-axes-artifact-bytes",
            "t080.static-holdout-artifact-bytes",
        } <= {marker["check_id"] for marker in held.held_checks}
        with mock.patch.object(migration._freeze_hold, "HELD", False):
            released = migration.static_gate_adapter(
                resolution=resolution, known_raw=known_raw,
                holdout_raw=holdout_raw, root=migration.ROOT,
            )
        assert any("known_axes.artifact_bytes" in item for item in released.refusals)
        assert any("holdout.artifact_bytes" in item for item in released.refusals)
    finally:
        _restore_functions(original)


def test_static_adapter_recorded_pin_hold_and_release_positive_control():
    known_raw = (migration.ROOT / migration.KNOWN_AXES_REL).read_bytes()
    holdout = json.loads((migration.ROOT / migration.HOLDOUT_REL).read_bytes())
    holdout["known_axes_freeze"]["sha256"] = "0" * 64
    holdout_raw = migration._canonical_bytes(holdout)
    receipt = copy.deepcopy(_valid_receipt())
    receipt["artifacts"]["holdout"]["raw_sha256"] = hashlib.sha256(
        holdout_raw,
    ).hexdigest()
    resolution = migration.ReceiptResolution(
        "active-valid", (), {"clean": True}, "a" * 40, receipt=receipt,
    )
    original = _patch_full_gate_to_pass()
    reached = []
    try:
        migration._verify_known_schema = lambda *_args: reached.append("schema")
        held = migration.static_gate_adapter(
            resolution=resolution, known_raw=known_raw,
            holdout_raw=holdout_raw, root=migration.ROOT,
        )
        assert "t080.static-known-axes-recorded-pin" in {
            marker["check_id"] for marker in held.held_checks
        }
        assert reached == ["schema"]
        reached.clear()
        with mock.patch.object(migration._freeze_hold, "HELD", False):
            released = migration.static_gate_adapter(
                resolution=resolution, known_raw=known_raw,
                holdout_raw=holdout_raw, root=migration.ROOT,
            )
        assert released.held_checks == ()
        assert reached == []
    finally:
        _restore_functions(original)


def test_ccbench_current_pin_hold_and_release_positive_control():
    known = {"ccbench_pin": "a" * 40}
    check_ids = (
        "t080.draft-known-axes-ccbench-current-pin",
        "t080.live-known-axes-ccbench-current-pin",
        "t080.static-known-axes-ccbench-current-pin",
    )
    with mock.patch.object(
            migration, "_current_ccbench_head", return_value="b" * 40):
        for check_id in check_ids:
            held_checks = []
            migration._verify_ccbench_current_or_hold(
                known, migration.ROOT,
                check_id=check_id, held_checks=held_checks,
            )
            assert [marker["check_id"] for marker in held_checks] == [check_id]
        with mock.patch.object(migration._freeze_hold, "HELD", False):
            for check_id in check_ids:
                _expect_reason(
                    lambda check_id=check_id: migration._verify_ccbench_current_or_hold(
                        known, migration.ROOT,
                        check_id=check_id, held_checks=[],
                    ),
                    "known_axes.ccbench_current",
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


def _build_history_touch_cases(tmp_path: Path):
    target = "target.txt"
    history_cases = []
    observation_cases = []

    def repo_with_files(name: str, files: dict[str, str]) -> tuple[Path, str]:
        root = tmp_path / name
        root.mkdir()
        _init_repo(root)
        for relative, contents in files.items():
            (root / relative).write_text(contents, encoding="utf-8")
        return root, _commit_all(root, f"seed {name}")

    root, _ = repo_with_files("modified", {target: "before\n"})
    (root / target).write_text("after\n", encoding="utf-8")
    modified_commit = _commit_all(root, "modify target")
    modified_root = root
    modified_oid = _run_git(
        root, "rev-parse", f"{modified_commit}:{target}",
    ).decode().strip()
    history_cases.append((1, "modified", modified_commit, root, None, True))
    observation_cases.append(("modified", (modified_commit,), root, b"target.txt"))

    root, _ = repo_with_files("deleted", {target: "before\n"})
    (root / target).unlink()
    deleted_commit = _commit_all(root, "delete target")
    history_cases.append((2, "deleted", deleted_commit, root, None, True))
    observation_cases.append(("deleted", (deleted_commit,), root, b"target.txt"))

    root, _ = repo_with_files("rename-source", {target: "rename me\n"})
    _run_git(root, "mv", target, "renamed.txt")
    rename_source_commit = _commit_all(root, "rename target away")
    history_cases.append((3, "rename source", rename_source_commit, root, None, True))
    observation_cases.append((
        "rename source", (rename_source_commit,), root, b"target.txt",
    ))

    root, _ = repo_with_files("rename-destination", {"source.txt": "rename me\n"})
    _run_git(root, "mv", "source.txt", target)
    rename_destination_commit = _commit_all(root, "rename source to target")
    history_cases.append((
        4, "rename destination", rename_destination_commit, root, None, True,
    ))
    observation_cases.append((
        "rename destination", (rename_destination_commit,), root, b"target.txt",
    ))

    root, _ = repo_with_files("symlink", {target: "regular\n"})
    (root / target).unlink()
    (root / target).symlink_to("symlink-destination")
    symlink_commit = _commit_all(root, "target to symlink")
    history_cases.append((5, "regular to symlink", symlink_commit, root, None, True))
    observation_cases.append((
        "regular to symlink", (symlink_commit,), root, b"target.txt",
    ))

    root, gitlink_target = repo_with_files("gitlink", {target: "regular\n"})
    (root / target).unlink()
    _run_git(
        root, "update-index", "--add", "--cacheinfo",
        f"160000,{gitlink_target},{target}",
    )
    _run_git(root, "commit", "-q", "-m", "target to gitlink", "-m", "AI-Agent: none")
    gitlink_commit = _run_git(root, "rev-parse", "HEAD").decode().strip()
    history_cases.append((6, "regular to gitlink", gitlink_commit, root, None, True))
    observation_cases.append((
        "regular to gitlink", (gitlink_commit,), root, b"target.txt",
    ))

    root = tmp_path / "added"
    root.mkdir()
    _init_repo(root)
    (root / target).write_text("added\n", encoding="utf-8")
    added_commit = _commit_all(root, "add target")
    added_root = root
    added_oid = _run_git(
        root, "rev-parse", f"{added_commit}:{target}",
    ).decode().strip()
    history_cases.append((7, "added", added_commit, root, None, False))
    observation_cases.append(("added", (added_commit,), root, b"target.txt"))

    root, _ = repo_with_files("unrelated", {target: "unchanged\n"})
    (root / "base.txt").write_text("unrelated change\n", encoding="utf-8")
    unrelated_commit = _commit_all(root, "modify unrelated file")
    history_cases.append((8, "unrelated", unrelated_commit, root, None, False))
    observation_cases.append(("unrelated", (unrelated_commit,), root, b"base.txt"))

    root = tmp_path / "root-add"
    root.mkdir()
    _run_git(root, "init", "-q")
    _run_git(root, "config", "user.name", "T080 Test")
    _run_git(root, "config", "user.email", "t080@example.invalid")
    (root / target).write_text("root addition\n", encoding="utf-8")
    root_commit = _commit_all(root, "root adds target")
    history_cases.append((9, "root addition", root_commit, root, None, False))
    observation_cases.append(("root addition", (root_commit,), root, b"target.txt"))

    root, common = repo_with_files("merge-two", {target: "common\n"})
    (root / "first.txt").write_text("first parent\n", encoding="utf-8")
    first_parent = _commit_all(root, "first parent")
    _run_git(root, "checkout", "-q", "-b", "second", common)
    (root / target).write_text("second parent\n", encoding="utf-8")
    second_parent = _commit_all(root, "second parent changes target")
    first_tree = _run_git(root, "rev-parse", f"{first_parent}^{{tree}}").decode().strip()
    merge_two = _run_git(
        root, "commit-tree", first_tree,
        "-p", first_parent, "-p", second_parent,
        input_bytes=b"two-parent merge\n\nAI-Agent: none\n",
    ).decode().strip()
    history_cases.append((10, "second parent differs", merge_two, root, None, True))
    observation_cases.append((
        "second parent differs", (merge_two,), root, b"target.txt",
    ))

    root, common = repo_with_files("merge-three", {target: "common\n"})
    (root / "first.txt").write_text("first parent\n", encoding="utf-8")
    first_parent = _commit_all(root, "first parent")
    _run_git(root, "checkout", "-q", "-b", "second", common)
    (root / "second.txt").write_text("second parent\n", encoding="utf-8")
    second_parent = _commit_all(root, "second parent")
    _run_git(root, "checkout", "-q", "-b", "third", common)
    (root / target).write_text("third parent\n", encoding="utf-8")
    third_parent = _commit_all(root, "third parent changes target")
    first_tree = _run_git(root, "rev-parse", f"{first_parent}^{{tree}}").decode().strip()
    merge_three = _run_git(
        root, "commit-tree", first_tree,
        "-p", first_parent, "-p", second_parent, "-p", third_parent,
        input_bytes=b"three-parent merge\n\nAI-Agent: none\n",
    ).decode().strip()
    history_cases.append((11, "third parent differs", merge_three, root, None, True))
    observation_cases.append((
        "third parent differs", (merge_three,), root, b"target.txt",
    ))

    exact_copy_root, exact_copy_base = repo_with_files(
        "unchanged-copy-source", {target: "same bytes\n"},
    )
    (exact_copy_root / "copy.txt").write_bytes((exact_copy_root / target).read_bytes())
    exact_copy_commit = _commit_all(exact_copy_root, "copy unchanged target")
    exact_copy_oid = _run_git(
        exact_copy_root, "rev-parse", f"{exact_copy_base}:{target}",
    ).decode().strip()
    history_cases.append((
        12, "unchanged exact copy source", exact_copy_commit, exact_copy_root,
        exact_copy_oid, True,
    ))
    observation_cases.append((
        "unchanged exact copy source", (exact_copy_commit,), exact_copy_root, b"copy.txt",
    ))

    near_copy_contents = "".join(
        f"stable line {number:03d}: exact-copy boundary\n" for number in range(100)
    )
    near_copy_root, near_copy_base = repo_with_files(
        "changed-copy-source", {target: near_copy_contents},
    )
    changed_contents = near_copy_contents.replace(
        "stable line 050: exact-copy boundary",
        "changed line 050: exact-copy boundary",
    )
    (near_copy_root / "copy.txt").write_text(changed_contents, encoding="utf-8")
    near_copy_commit = _commit_all(near_copy_root, "copy and change target contents")
    near_copy_oid = _run_git(
        near_copy_root, "rev-parse", f"{near_copy_base}:{target}",
    ).decode().strip()
    observation_cases.append((
        "changed near-copy", (near_copy_commit,), near_copy_root, b"copy.txt",
    ))

    aggregate_root, _ = repo_with_files("aggregate", {target: "before\n"})
    (aggregate_root / "base.txt").write_text("false commit\n", encoding="utf-8")
    false_commit = _commit_all(aggregate_root, "unrelated aggregate commit")
    (aggregate_root / target).write_text("after\n", encoding="utf-8")
    true_commit = _commit_all(aggregate_root, "touching aggregate commit")
    error_commit = "f" * 40
    observation_cases.extend((
        ("aggregate unrelated", (false_commit,), aggregate_root, b"base.txt"),
        ("aggregate touching", (true_commit,), aggregate_root, b"target.txt"),
    ))

    changed_source_root, _ = repo_with_files(
        "modified-copy-source", {target: "source before\n"},
    )
    (changed_source_root / "copy.txt").write_bytes(
        (changed_source_root / target).read_bytes(),
    )
    (changed_source_root / target).write_text("source after\n", encoding="utf-8")
    changed_source_commit = _commit_all(changed_source_root, "copy then modify source")
    observation_cases.append((
        "modified copy source", (changed_source_commit,), changed_source_root, b"target.txt",
    ))

    empty_copy_root, _ = repo_with_files("empty-copy", {target: ""})
    (empty_copy_root / "empty-copy.txt").write_bytes(b"")
    empty_copy_commit = _commit_all(empty_copy_root, "copy empty blob")
    observation_cases.append((
        "empty blob copy", (empty_copy_commit,), empty_copy_root, b"empty-copy.txt",
    ))

    duplicate_dest_root, _ = repo_with_files(
        "duplicate-destinations", {target: "same destination bytes\n"},
    )
    for relative in ("copy-one.txt", "copy-two.txt"):
        (duplicate_dest_root / relative).write_bytes(
            (duplicate_dest_root / target).read_bytes(),
        )
    duplicate_dest_commit = _commit_all(
        duplicate_dest_root, "add identical blob at two destinations",
    )
    observation_cases.append((
        "same oid at two destinations",
        (duplicate_dest_commit,),
        duplicate_dest_root,
        b"copy-one.txt",
    ))

    non_utf8_root, _ = repo_with_files("non-utf8-observation", {target: "unchanged\n"})
    non_utf8_path = b"unrelated-\xff"
    fd = os.open(
        os.path.join(os.fsencode(non_utf8_root), non_utf8_path),
        os.O_WRONLY | os.O_CREAT | os.O_EXCL,
        0o644,
    )
    try:
        os.write(fd, b"non-utf8 path\n")
    finally:
        os.close(fd)
    non_utf8_commit = _commit_all(non_utf8_root, "add non-UTF-8 unrelated path")
    observation_cases.append((
        "non-UTF-8 unrelated path", (non_utf8_commit,), non_utf8_root, non_utf8_path,
    ))

    return {
        "target": target,
        "history_cases": tuple(history_cases),
        "observation_cases": tuple(observation_cases),
        "near_copy": (near_copy_commit, near_copy_root, near_copy_oid),
        "exact_copy": (exact_copy_commit, exact_copy_root),
        "modified": (modified_commit, modified_root, modified_oid),
        "added": (added_commit, added_root, added_oid),
        "aggregate": (aggregate_root, false_commit, true_commit, error_commit),
    }


def test_history_touches_path_positive_control_matrix(tmp_path: Path):
    """[T-057] path 履歴述語の受理集合を synthetic git 履歴で固定する。"""
    cases = _build_history_touch_cases(tmp_path)
    target = cases["target"]
    history_cases = cases["history_cases"]
    assert [number for number, *_rest in history_cases] == list(range(1, 13))
    assert any(expected is True for *_case, expected in history_cases)
    for number, label, commit, root, duplicate_oid, expected in history_cases:
        actual = migration._history_touches_path(
            commit, target, root, duplicate_oid=duplicate_oid,
        )
        batched = migration._batched_history_touches_path(
            (commit,), target, root, duplicate_oid=duplicate_oid,
        )
        assert actual is expected, (number, label, actual, expected)
        assert batched is expected, (number, label, batched, expected)

    near_copy_commit, near_copy_root, near_copy_oid = cases["near_copy"]
    # このケースが True へ戻ったら、それは 2026-08-09 のユーザー裁定
    # 「--find-copies-harder を外し、exact copy だけを OID で検出する」の逆行である。
    # 期待値を変える前に裁定をやり直すこと。
    assert migration._history_touches_path(
        near_copy_commit, target, near_copy_root, duplicate_oid=near_copy_oid,
    ) is False, "case 12b: changed near-copy must not match the target blob OID"
    assert migration._batched_history_touches_path(
        (near_copy_commit,), target, near_copy_root, duplicate_oid=near_copy_oid,
    ) is False, "case 12b batch: changed near-copy must not match the target blob OID"

    exact_copy_commit, exact_copy_root = cases["exact_copy"]
    assert migration._history_touches_path(
        exact_copy_commit, target, exact_copy_root, duplicate_oid=None,
    ) is False, "exact copy must remain undetected when duplicate_oid is omitted"
    assert migration._batched_history_touches_path(
        (exact_copy_commit,), target, exact_copy_root, duplicate_oid=None,
    ) is False, "batch exact copy must remain undetected when duplicate_oid is omitted"

    modified_commit, modified_root, modified_oid = cases["modified"]
    assert migration._history_touches_path(
        modified_commit, target, modified_root, duplicate_oid=modified_oid,
    ) is True
    assert migration._batched_history_touches_path(
        (modified_commit,), target, modified_root, duplicate_oid=modified_oid,
    ) is True
    added_commit, added_root, added_oid = cases["added"]
    assert migration._history_touches_path(
        added_commit, target, added_root, duplicate_oid=added_oid,
    ) is False
    assert migration._batched_history_touches_path(
        (added_commit,), target, added_root, duplicate_oid=added_oid,
    ) is False

    aggregate_root, false_commit, true_commit, error_commit = cases["aggregate"]

    try:
        migration._history_touches_path(error_commit, target, aggregate_root)
    except migration.MigrationError:
        pass
    else:
        raise AssertionError("case 13: nonexistent commit must raise MigrationError")

    assert migration._any_history_touches_path(
        frozenset((error_commit, false_commit, true_commit)), target, aggregate_root,
    ) is True
    _expect_reason(
        lambda: migration._batched_history_touches_path(
            frozenset((error_commit, false_commit, true_commit)), target, aggregate_root,
        ),
        "receipt.git_error",
    )
    _expect_reason(
        lambda: migration._any_history_touches_path(
            frozenset((false_commit, error_commit)), target, aggregate_root,
        ),
        "receipt.git_error",
    )
    assert migration._any_history_touches_path(frozenset(), target, aggregate_root) is False


def test_batched_history_cheap_observation_contains_expensive_observation(tmp_path: Path):
    cases = _build_history_touch_cases(tmp_path)
    for label, commits, root, known_changed_path in cases["observation_cases"]:
        targets = tuple(sorted(commits))
        cheap = migration._run_batched_history_diff_tree(
            targets,
            b"target.txt",
            root,
            None,
            detect_renames_and_copies=False,
        )
        expensive = migration._run_batched_history_diff_tree(
            targets,
            b"target.txt",
            root,
            None,
            detect_renames_and_copies=True,
        )
        assert cheap.paths, label
        assert known_changed_path in cheap.paths, (label, known_changed_path, cheap.paths)
        assert known_changed_path in expensive.paths, (
            label, known_changed_path, expensive.paths,
        )
        assert expensive.paths <= cheap.paths, label
        assert (
            expensive.nonzero_destination_oids
            <= cheap.nonzero_destination_oids
        ), label


def _build_unchanged_target_descendants(tmp_path: Path, name: str):
    root = tmp_path / name
    root.mkdir()
    _init_repo(root)
    (root / "target.txt").write_text("target stays unchanged\n", encoding="utf-8")
    seed = _commit_all(root, "seed target")
    target_oid = _run_git(root, "rev-parse", f"{seed}:target.txt").decode().strip()

    descendants = []
    (root / "unrelated.txt").write_text("added\n", encoding="utf-8")
    descendants.append(_commit_all(root, "add unrelated"))
    (root / "unrelated.txt").write_text("modified\n", encoding="utf-8")
    descendants.append(_commit_all(root, "modify unrelated"))
    (root / "unrelated.txt").unlink()
    descendants.append(_commit_all(root, "delete unrelated"))

    raw_name = b"unrelated-\xff"
    fd = os.open(
        os.path.join(os.fsencode(root), raw_name),
        os.O_WRONLY | os.O_CREAT | os.O_EXCL,
        0o644,
    )
    try:
        os.write(fd, b"raw path\n")
    finally:
        os.close(fd)
    descendants.append(_commit_all(root, "add non-UTF-8 path"))

    merge_base = descendants[-1]
    _run_git(root, "checkout", "-q", "-b", "side", merge_base)
    (root / "side.txt").write_text("side\n", encoding="utf-8")
    side = _commit_all(root, "side unrelated")
    _run_git(root, "checkout", "-q", "-B", "main", merge_base)
    (root / "main.txt").write_text("main\n", encoding="utf-8")
    main = _commit_all(root, "main unrelated")
    _run_git(root, "merge", "-q", "--no-ff", "-m", "merge unrelated", side)
    merge = _run_git(root, "rev-parse", "HEAD").decode().strip()
    descendants.extend((side, main, merge))
    return root, target_oid, tuple(sorted(descendants))


def test_batched_history_cheap_miss_implies_expensive_false_and_skips_expensive(
    tmp_path: Path,
):
    root, target_oid, targets = _build_unchanged_target_descendants(tmp_path, "cheap-miss")
    cheap = migration._run_batched_history_diff_tree(
        targets, b"target.txt", root, target_oid, detect_renames_and_copies=False,
    )
    expensive = migration._run_batched_history_diff_tree(
        targets, b"target.txt", root, target_oid, detect_renames_and_copies=True,
    )
    assert cheap.has_trigger(b"target.txt", target_oid) is False
    assert expensive.touches_path is False

    calls = []
    original = migration._git

    def record_git(args, repo_root, *, stdin=None):
        calls.append((tuple(args), stdin))
        return original(args, repo_root, stdin=stdin)

    with mock.patch.object(migration, "_git", side_effect=record_git):
        assert migration._batched_history_touches_path(
            targets, "target.txt", root, duplicate_oid=target_oid,
        ) is False
    assert len(calls) == 1
    assert calls[0][0] == migration._BATCH_DIFF_ARGV_CHEAP


def _build_multicommit_fallback_targets(tmp_path: Path, name: str):
    root = tmp_path / name
    root.mkdir()
    _init_repo(root)
    (root / "target.txt").write_text("before\n", encoding="utf-8")
    _commit_all(root, "seed target")
    (root / "unrelated.txt").write_text("unrelated\n", encoding="utf-8")
    unrelated = _commit_all(root, "unrelated descendant")
    commit_header = _run_git(root, "cat-file", "commit", unrelated).partition(b"\n\n")[0]
    midpoint_raw = None
    for nonce in range(1024):
        candidate_raw = commit_header + (
            f"\n\nunrelated midpoint {nonce:04d}\n\nAI-Agent: none\n".encode("ascii")
        )
        object_input = (
            f"commit {len(candidate_raw)}\0".encode("ascii") + candidate_raw
        )
        candidate_oid = hashlib.sha1(object_input).hexdigest()
        if 0x70 <= int(candidate_oid[:2], 16) <= 0x8F:
            midpoint_raw = candidate_raw
            break
    assert midpoint_raw is not None
    unrelated = _run_git(
        root, "hash-object", "-t", "commit", "-w", "--stdin",
        input_bytes=midpoint_raw,
    ).decode().strip()
    assert unrelated == candidate_oid

    (root / "target.txt").write_text("after\n", encoding="utf-8")
    _run_git(root, "add", "target.txt")
    tree = _run_git(root, "write-tree").decode().strip()
    touching = None
    # unrelated を SHA 空間中央付近へ置くため期待約 2 回、64 回失敗は 2e-16 未満。
    for attempt in range(64):
        candidate = _run_git(
            root,
            "commit-tree",
            tree,
            "-p",
            unrelated,
            input_bytes=(
                f"touch target {attempt}\n\nAI-Agent: none\n"
            ).encode("ascii"),
        ).decode().strip()
        if unrelated < candidate:
            touching = candidate
            break
    assert touching is not None
    targets = (unrelated, touching)
    assert targets == tuple(sorted(targets))
    return root, targets


def test_batched_history_expensive_fallback_reuses_all_targets_and_stdin(tmp_path: Path):
    root, targets = _build_multicommit_fallback_targets(tmp_path, "fallback")
    calls = []
    original = migration._git

    def record_git(args, repo_root, *, stdin=None):
        calls.append((tuple(args), stdin))
        return original(args, repo_root, stdin=stdin)

    with mock.patch.object(migration, "_git", side_effect=record_git):
        assert migration._batched_history_touches_path(
            targets, "target.txt", root,
        ) is True
    assert len(calls) == 2
    assert calls[0][0] == migration._BATCH_DIFF_ARGV_CHEAP
    assert calls[1][0] == migration._BATCH_DIFF_ARGV_EXPENSIVE
    assert calls[1][1] == calls[0][1]
    assert calls[0][1] == "".join(f"{commit}\n" for commit in targets).encode("ascii")


def test_batched_history_expensive_output_mismatch_fails_closed(tmp_path: Path):
    root, targets = _build_multicommit_fallback_targets(tmp_path, "malformed-expensive")
    original = migration._git
    diff_tree_calls = 0

    def truncate_only_expensive(args, repo_root, *, stdin=None):
        nonlocal diff_tree_calls
        out = original(args, repo_root, stdin=stdin)
        if args and args[0] == "diff-tree":
            diff_tree_calls += 1
            if diff_tree_calls == 2:
                return b""
        return out

    with mock.patch.object(migration, "_git", side_effect=truncate_only_expensive):
        _expect_reason(
            lambda: migration._batched_history_touches_path(
                targets, "target.txt", root,
            ),
            "receipt.git_error",
        )
    assert diff_tree_calls == 2


def test_batched_history_trigger_is_independent_of_worktree_status_commands(tmp_path: Path):
    root, target_oid, targets = _build_unchanged_target_descendants(
        tmp_path, "status-independent",
    )
    calls = []
    original_git = migration._git
    original_git_rc = migration._git_rc

    def record_git(args, repo_root, *, stdin=None):
        calls.append(("_git", tuple(args)))
        return original_git(args, repo_root, stdin=stdin)

    def record_git_rc(args, repo_root):
        calls.append(("_git_rc", tuple(args)))
        return original_git_rc(args, repo_root)

    with mock.patch.object(
        migration, "_git", side_effect=record_git,
    ), mock.patch.object(migration, "_git_rc", side_effect=record_git_rc):
        assert migration._batched_history_touches_path(
            targets, "target.txt", root, duplicate_oid=target_oid,
        ) is False
    forbidden = {
        "status", "diff", "diff-files", "diff-index", "ls-files", "stash",
        "update-index", "read-tree", "write-tree", "add", "restore", "reset",
        "checkout", "switch",
    }
    assert calls
    assert all(argv and argv[0] not in forbidden for _seam, argv in calls)


def test_batched_history_verdict_is_same_for_clean_and_dirty_worktree(tmp_path: Path):
    root = tmp_path / "dirty-status-independent"
    root.mkdir()
    _init_repo(root)
    target = root / "target.txt"
    target.write_text("before\n", encoding="utf-8")
    _commit_all(root, "seed target")
    target.write_text("committed change\n", encoding="utf-8")
    targets = (_commit_all(root, "modify target"),)
    calls = []
    original_git = migration._git
    original_git_rc = migration._git_rc

    def record_git(args, repo_root, *, stdin=None):
        calls.append(("_git", tuple(args)))
        return original_git(args, repo_root, stdin=stdin)

    def record_git_rc(args, repo_root):
        calls.append(("_git_rc", tuple(args)))
        return original_git_rc(args, repo_root)

    with mock.patch.object(
        migration, "_git", side_effect=record_git,
    ), mock.patch.object(migration, "_git_rc", side_effect=record_git_rc):
        clean_verdict = migration._batched_history_touches_path(
            targets, "target.txt", root,
        )
        target.write_text("dirty worktree change\n", encoding="utf-8")
        dirty_verdict = migration._batched_history_touches_path(
            targets, "target.txt", root,
        )
    assert dirty_verdict is clean_verdict is True
    forbidden = {
        "status", "diff", "diff-files", "diff-index", "ls-files", "stash",
        "update-index", "read-tree", "write-tree", "add", "restore", "reset",
        "checkout", "switch",
    }
    assert calls
    assert all(argv and argv[0] not in forbidden for _seam, argv in calls)


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


@contextlib.contextmanager
def _real_layer2_token():
    from orchestrator.tests import test_s8b_ratified_freeze as emitter
    with tempfile.TemporaryDirectory(prefix="t080-layer2-") as directory:
        root, ratified, _topology = emitter.load_emitter_g1(Path(directory))
        token = emitter.M.launch_validate(ratified, root)
        holdout = json.loads((root / migration.HOLDOUT_REL).read_bytes())
        assert migration._verify_holdout_live_scan(
            root, holdout, delegate_to=token, validation_head=token.activation_head,
        ) is token.search_report
        yield root, token, holdout


def _assert_layer2_token_rejected(root, token, holdout):
    assert migration._holdout_layer2_delegation(
        root=root, validation_head=migration._capture_head(root), launch_validated=token,
    ) is None
    _expect_reason(lambda: migration._verify_holdout_live_scan(
        root, holdout, delegate_to=token, validation_head=migration._capture_head(root),
    ), "holdout.unknownness_layer2")


@in_sealed_fixture_process
def test_layer2_delegation_rejects_wrong_activation_head():
    from dataclasses import replace
    with _real_layer2_token() as (root, token, holdout):
        _assert_layer2_token_rejected(root, replace(token, activation_head="0" * 40), holdout)


@in_sealed_fixture_process
def test_layer2_delegation_rejects_foreign_root():
    import shutil
    from orchestrator.campaign import s8b_ratified_freeze as ratified
    with _real_layer2_token() as (root, token, holdout):
        clone = root.parent / "same-head-clone"
        shutil.copytree(root, clone)
        assert migration._capture_head(clone) == token.activation_head
        assert ratified._enumeration_digest(clone) == token.search_digest
        _assert_layer2_token_rejected(clone, token, holdout)
        (clone / "additional-file.txt").write_text("different enumeration\n")
        _assert_layer2_token_rejected(clone, token, holdout)


@in_sealed_fixture_process
def test_layer2_delegation_rejects_enumeration_drift():
    with _real_layer2_token() as (root, token, holdout):
        (root / "additional-file.txt").write_text("outside the freeze namespace\n")
        _assert_layer2_token_rejected(root, token, holdout)


@in_sealed_fixture_process
def test_layer2_delegation_rejects_nonlaunch_type():
    from types import SimpleNamespace
    from orchestrator.campaign import s8b_ratified_freeze as ratified
    class DerivedToken(ratified.LaunchValidatedFreeze):
        pass
    with _real_layer2_token() as (root, token, holdout):
        for cls in (ratified.ReverifiedFreeze, SimpleNamespace, DerivedToken):
            _assert_layer2_token_rejected(root, cls(**vars(token)), holdout)


@in_sealed_fixture_process
def test_layer2_delegation_rejects_stale_generation_token():
    with _real_layer2_token() as (root, token, holdout):
        generation = root / f"output/s8b-freeze/holdout_freeze.v2.g{token.ratified.generation_number}.json"
        generation.write_bytes(generation.read_bytes() + b"\n")
        _assert_layer2_token_rejected(root, token, holdout)


@in_sealed_fixture_process
@pytest.mark.parametrize("field", ["expressions", "match_convention", "candidate_id", "candidate_set"])
def test_delegated_scan_keeps_frozen_document_bindings(field):
    with _real_layer2_token() as (root, token, holdout):
        doc = copy.deepcopy(holdout)
        if field == "expressions":
            doc["holdouts"]["rr80"]["unknownness_check"][field] = {}
        elif field == "match_convention":
            doc[field] = "different convention"
        elif field == "candidate_id":
            doc["holdouts"]["rr80"][field] = "different candidate"
        else:
            del doc["holdouts"]["rr20"]
        _expect_reason(lambda: migration._verify_holdout_live_scan(
            root, doc, delegate_to=token, validation_head=token.activation_head,
        ), "holdout.unknownness_layer2")


def _run():
    fns = [value for name, value in sorted(globals().items())
           if name.startswith("test_") and callable(value)]
    passed = failed = errors = skipped = 0
    for fn in fns:
        try:
            if fn is test_delegated_scan_keeps_frozen_document_bindings:
                for field in ("expressions", "match_convention", "candidate_id", "candidate_set"):
                    fn(field)
            else:
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
