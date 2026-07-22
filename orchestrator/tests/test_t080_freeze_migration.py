# -*- coding: utf-8 -*-
"""T-080 receipt/adapter core の hermetic 回帰。"""
from __future__ import annotations

import contextlib
import copy
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


def _repo_with_schema_valid_receipt(*, extra_path: bool = False, trailer: str = "AI-Agent: none"):
    temp = tempfile.TemporaryDirectory(prefix="izanagi_t080_active_")
    root = Path(temp.name)
    basis = _init_repo(root)
    receipt = _valid_receipt()
    receipt["migration_basis_commit"] = basis
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
        "_verify_ccbench_live", "_verify_closure", "_verify_reconstruction_static",
        "_verify_live_and_static_documents",
    )
    original = {name: getattr(migration, name) for name in names}
    migration._load_artifact = lambda *_args, **_kwargs: (b"{}", {})
    migration._validate_repin_report_git = lambda *_args, **_kwargs: None
    migration._validate_positive_control = lambda *_args, **_kwargs: None
    migration._verify_ccbench_live = lambda *_args, **_kwargs: None
    migration._verify_closure = lambda *_args, **_kwargs: None
    migration._verify_reconstruction_static = lambda *_args, **_kwargs: None
    migration._verify_live_and_static_documents = lambda *_args, **_kwargs: {}
    return original


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
        migration._verify_ccbench_live = lambda *_args, **_kwargs: (_ for _ in ()).throw(
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
        assert len(result.refusals) == 1 and "receipt.history_mutated" in result.refusals[0]
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
