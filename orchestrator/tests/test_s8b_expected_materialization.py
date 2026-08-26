# -*- coding: utf-8 -*-
"""Unit A tests for declaration-derived S8b materialization snapshots."""
from __future__ import annotations

import contextlib
import inspect
import os
import shutil
import stat
from pathlib import Path
from types import SimpleNamespace

import pytest

from orchestrator.campaign import s1_direct_comparison as S
from orchestrator.campaign import s8b_expected_materialization as E
from orchestrator.campaign import s8b_materialization as M
from orchestrator.campaign.model import Genome


def _write_tree(root: Path) -> None:
    root.mkdir()
    (root / "src").mkdir()
    (root / "src" / "main.cc").write_text("int main() { return 0; }\n", encoding="utf-8")
    (root / ".hidden-input").write_text("stable\n", encoding="utf-8")
    (root / ".git").write_text("gitdir: /volatile/checkout/one\n", encoding="utf-8")


def _mode(path: Path) -> int:
    return stat.S_IMODE(path.lstat().st_mode)


def test_tree_digest_exclusion_is_exact_and_volatile_git_payload_is_ignored(tmp_path):
    root = tmp_path / "tree"
    _write_tree(root)

    assert E.TREE_DIGEST_EXCLUSIONS == frozenset({".git"})
    first = E.snapshot_tree_digest(root)
    (root / "src" / ".git").mkdir()
    (root / "src" / ".git" / "config").write_text(
        "worktree = /another/volatile/root\n", encoding="utf-8",
    )
    (root / ".git").write_text(
        "gitdir: /different/absolute/path/with/a/new/working-tree-hash\n",
        encoding="utf-8",
    )
    assert E.snapshot_tree_digest(root) == first

    (root / ".hidden-input").write_text("changed\n", encoding="utf-8")
    assert E.snapshot_tree_digest(root) != first


def test_tree_digest_covers_path_bytes_file_bytes_symlink_and_executable_bit(tmp_path):
    root = tmp_path / "tree"
    _write_tree(root)
    link = root / "source-link"
    link.symlink_to("src/main.cc")
    baseline = E.snapshot_tree_digest(root)

    link.unlink()
    link.symlink_to(".hidden-input")
    assert E.snapshot_tree_digest(root) != baseline
    link.unlink()
    link.symlink_to("src/main.cc")
    assert E.snapshot_tree_digest(root) == baseline

    source = root / "src" / "main.cc"
    os.chmod(source, _mode(source) | 0o111)
    assert E.snapshot_tree_digest(root) != baseline


def test_exact_match_rejects_with_fixed_nonvolatile_reason(tmp_path):
    root = tmp_path / "tree"
    _write_tree(root)
    expected = E.snapshot_tree_digest(root)
    assert E.assert_expected_materialization(root, expected) == expected

    (root / "src" / "main.cc").write_text("int main() { return 1; }\n", encoding="utf-8")
    with pytest.raises(E.ExpectedMaterializationError) as excinfo:
        E.assert_expected_materialization(root, expected)
    assert str(excinfo.value) == (
        "materialized tree differs from declaration "
        "(reason=tree-digest-mismatch count=1)"
    )
    assert str(root) not in str(excinfo.value)
    assert expected not in str(excinfo.value)


def test_non_writable_transition_preserves_digest_and_restores_all_modes(tmp_path):
    root = tmp_path / "tree"
    _write_tree(root)
    original = {
        path.relative_to(root).as_posix() if path != root else ".": _mode(path)
        for path in (root, root / ".git", root / ".hidden-input",
                     root / "src", root / "src" / "main.cc")
    }
    before = E.snapshot_tree_digest(root)

    state = E.make_snapshot_non_writable(root)
    try:
        assert state.tree_digest == before
        assert E.snapshot_tree_digest(root) == before
        for path in (root, root / ".git", root / ".hidden-input",
                     root / "src", root / "src" / "main.cc"):
            assert _mode(path) & 0o222 == 0
    finally:
        E.restore_snapshot_permissions(state)
    restored = {
        path.relative_to(root).as_posix() if path != root else ".": _mode(path)
        for path in (root, root / ".git", root / ".hidden-input",
                     root / "src", root / "src" / "main.cc")
    }
    assert restored == original


def test_reference_producer_uses_a_separate_tree_and_replays_declaration(
        tmp_path, monkeypatch):
    base = tmp_path / "base"
    _write_tree(base)
    actual = tmp_path / "actual"
    shutil.copytree(base, actual, symlinks=True)
    (actual / ".git").write_text("gitdir: /actual/volatile/path\n", encoding="utf-8")
    (actual / "template-applied").write_text("template-v1\n", encoding="utf-8")
    edited = "predicate: canonical-gate\n"
    (actual / "src" / "main.cc").write_text(edited, encoding="utf-8")

    checkout_calls: list[tuple[str, str, Path]] = []

    @contextlib.contextmanager
    def fake_checkout(pin, *, base_dir):
        reference = tmp_path / f"reference-{len(checkout_calls)}"
        shutil.copytree(base_dir, reference, symlinks=True)
        (reference / ".git").write_text(
            f"gitdir: {reference.resolve()}/volatile\n", encoding="utf-8",
        )
        checkout_calls.append((pin, str(base_dir), reference))
        yield str(reference)

    @contextlib.contextmanager
    def fake_applied(patch, pin, *, ccbench_dir):
        assert patch == "template.patch"
        assert pin == "abcdef0123456789"
        (Path(ccbench_dir) / "template-applied").write_text(
            "template-v1\n", encoding="utf-8",
        )
        yield ["template-applied"]

    def fake_quarantine(root, implementation, *, marker_id, source_rel, write):
        assert implementation == "canonical-gate"
        assert marker_id == "gate-marker"
        assert source_rel == "src/main.cc"
        assert write is True
        rendered = f"predicate: {implementation}\n"
        if write:
            (Path(root) / source_rel).write_text(rendered, encoding="utf-8")
        return SimpleNamespace(passed=True), "base", rendered, "diff"

    monkeypatch.setattr(E.patchharness, "checkout", fake_checkout)
    monkeypatch.setattr(E.patchharness, "applied", fake_applied)
    expected = E.produce_expected_materialization_sha256(
        ccbench_commit="abcdef0123456789",
        configuration="system_gate",
        base_dir=base,
        template_patch="template.patch",
        implementation="canonical-gate",
        marker_id="gate-marker",
        source_rel="src/main.cc",
        quarantine_fn=fake_quarantine,
    )

    assert len(checkout_calls) == 1
    assert checkout_calls[0][2] != actual
    assert E.assert_expected_materialization(actual, expected) == expected
    (actual / "src" / "main.cc").write_text("predicate: shadow-gate\n", encoding="utf-8")
    with pytest.raises(E.ExpectedMaterializationError, match="tree-digest-mismatch"):
        E.assert_expected_materialization(actual, expected)


def test_reference_producer_requires_returned_source_to_match_reference_tree(
        tmp_path, monkeypatch):
    base = tmp_path / "base"
    _write_tree(base)

    @contextlib.contextmanager
    def fake_checkout(_pin, *, base_dir):
        reference = tmp_path / "reference"
        shutil.copytree(base_dir, reference)
        yield str(reference)

    @contextlib.contextmanager
    def fake_applied(*_args, **_kwargs):
        yield []

    def fake_quarantine(*_args, **_kwargs):
        return SimpleNamespace(passed=True), "base", "reference-render", "diff"

    monkeypatch.setattr(E.patchharness, "checkout", fake_checkout)
    monkeypatch.setattr(E.patchharness, "applied", fake_applied)
    with pytest.raises(E.ExpectedMaterializationError) as excinfo:
        E.produce_expected_materialization_sha256(
            ccbench_commit="abcdef0123456789",
            configuration="system_gate",
            base_dir=base,
            template_patch="template.patch",
            implementation="canonical-gate",
            marker_id="gate-marker",
            source_rel="src/main.cc",
            quarantine_fn=fake_quarantine,
        )
    assert str(excinfo.value) == (
        "reference source was not materialized exactly "
        "(reason=source-write-mismatch count=1)"
    )


def test_declaration_replay_derives_gate_recipe_without_observed_tree(
        tmp_path, monkeypatch):
    from orchestrator.campaign import trigger_gate_binding

    captured = {}
    monkeypatch.setattr(
        trigger_gate_binding, "is_canonical_predicate", lambda value: value == "raw-gate",
    )
    monkeypatch.setattr(
        trigger_gate_binding, "canonicalize_predicate", lambda _value: "canonical-gate",
    )

    def fake_producer(**kwargs):
        captured.update(kwargs)
        return "a" * 64

    monkeypatch.setattr(E, "produce_expected_materialization_sha256", fake_producer)
    digest = E.produce_expected_materialization_from_declaration(
        ccbench_commit="abcdef0123456789",
        configuration="system_gate",
        declaration={
            "configuration": "system_gate",
            "gate_predicate": "raw-gate",
            "flags": {"BACK_OFF": 1},
        },
        base_dir=tmp_path,
    )

    assert digest == "a" * 64
    assert captured["ccbench_commit"] == "abcdef0123456789"
    assert captured["configuration"] == "system_gate"
    assert captured["base_dir"] == tmp_path
    assert captured["implementation"] == "canonical-gate"
    assert captured["marker_id"]
    assert captured["source_rel"]
    assert callable(captured["quarantine_fn"])


def test_build_descriptor_freezes_entry_and_carries_derived_template_path():
    declaration = {
        "configuration": "backoff_fixed_best",
        "flags": {"BACK_OFF": 1, "BACKOFF_FIXED": 2},
    }
    descriptor = E.expected_materialization_descriptor(
        ccbench_commit="abcdef0123456789",
        configuration="backoff_fixed_best",
        declaration=declaration,
    )
    original = descriptor.declaration
    declaration["flags"]["BACKOFF_FIXED"] = 99

    assert descriptor.ccbench_commit == "abcdef0123456789"
    assert descriptor.configuration == "backoff_fixed_best"
    assert descriptor.declaration == original
    assert descriptor.declaration["flags"]["BACKOFF_FIXED"] == 2
    assert descriptor.template_patch_path == E.template_patch_path_from_declaration(
        configuration="backoff_fixed_best",
        declaration=original,
    )
    assert descriptor.template_patch_path.endswith("patches/silo-backoff-fixed.patch")
    assert len(descriptor.declaration_sha256) == 64


def test_legacy_stock_configuration_is_a_no_patch_materialization():
    declaration = {
        "configuration": "stock",
        "flags": {"BACKOFF_FIXED": 0},
    }
    descriptor = E.expected_materialization_descriptor(
        ccbench_commit="abcdef0123456789",
        configuration="stock",
        declaration=declaration,
    )

    assert descriptor.configuration == "stock"
    assert descriptor.declaration == declaration
    assert descriptor.template_patch_path is None


@pytest.mark.parametrize(("configuration", "declaration", "expected_keys"), [
    (
        "p2_2_flag_opt",
        {
            "flags": {"BACK_OFF": 0},
            "label": "synthetic-flag-opt",
            "sources": [],
            "variant": "synthetic-variant",
        },
        frozenset({"flags", "label", "sources", "variant"}),
    ),
    (
        "backoff_fixed_best",
        {
            "backoff_us": 2,
            "flags": {"BACK_OFF": 1, "BACKOFF_FIXED": 2},
            "sources": [],
        },
        frozenset({"backoff_us", "flags", "sources"}),
    ),
    (
        "sort_best",
        {
            "comparator": "synthetic comparator body",
            "flags": {"SORT_VARIANT": 1},
            "name": "synthetic-sort",
            "note": "synthetic entry with the production freeze shape",
            "sources": [],
        },
        frozenset({"comparator", "flags", "name", "note", "sources"}),
    ),
])
def test_real_freeze_entry_shapes_without_configuration_are_admitted(
        tmp_path, monkeypatch, configuration, declaration, expected_keys):
    captured = {}

    def fake_producer(**kwargs):
        captured.update(kwargs)
        return "a" * 64

    assert frozenset(declaration) == expected_keys
    assert "configuration" not in declaration
    monkeypatch.setattr(E, "produce_expected_materialization_sha256", fake_producer)

    digest = E.produce_expected_materialization_from_declaration(
        ccbench_commit="abcdef0123456789",
        configuration=configuration,
        declaration=declaration,
        base_dir=tmp_path,
    )

    assert digest == "a" * 64
    assert captured["configuration"] == configuration
    assert captured["ccbench_commit"] == "abcdef0123456789"
    assert captured["base_dir"] == tmp_path


def test_redundant_configuration_field_must_still_match_selected_entry_key(
        tmp_path, monkeypatch):
    monkeypatch.setattr(
        E,
        "produce_expected_materialization_sha256",
        lambda **_kwargs: pytest.fail("mismatched redundant field must reject first"),
    )

    with pytest.raises(E.ExpectedMaterializationError, match="configuration-mismatch"):
        E.produce_expected_materialization_from_declaration(
            ccbench_commit="abcdef0123456789",
            configuration="p2_2_flag_opt",
            declaration={
                "configuration": "sort_best",
                "flags": {"BACK_OFF": 0},
                "label": "synthetic-flag-opt",
                "sources": [],
                "variant": "synthetic-variant",
            },
            base_dir=tmp_path,
        )


def test_prepared_cell_binding_identity_remains_exact_five_key():
    genome = Genome("silo", {"BACK_OFF": 1})
    legacy = S.PreparedCell(genome, "stock", "/snapshot", "/cache")
    identity = M.binding_from_prepared(
        {"configuration": "stock"}, legacy,
    )
    assert set(identity) == {
        "genome_canonical", "src_token", "variant_id", "entry_sha256",
        "binding_sha256",
    }
    with pytest.raises(TypeError, match="expected_materialization_sha256"):
        M.binding_from_prepared(
            {"configuration": "stock"}, legacy,
            expected_materialization_sha256="a" * 64,
        )


def test_build_snapshot_gate_orders_reference_exact_readonly_then_evidence():
    shared_source = inspect.getsource(S.prepare_cell)
    assert "s8b_expected_materialization" not in shared_source
    assert "source_digest.resolve" in shared_source

    source = inspect.getsource(E.admitted_build_snapshot)
    reference = source.index("produce_expected_materialization_from_declaration")
    exact = source.index("assert_expected_materialization")
    readonly = source.index("make_snapshot_non_writable")
    evidence = source.index("source_digest.resolve_evidence")
    assert reference < exact < readonly < evidence
    assert "evidence.src_token != prepared_src_token" in source
    assert "Callable" not in str(inspect.signature(E.admitted_build_snapshot))


_SNAPSHOT_TOKEN = "4" * 64
_DIFFERENT_SNAPSHOT_TOKEN = "5" * 64


def _snapshot_evidence(root: Path, token: str) -> M.SourceEvidence:
    return M.SourceEvidence(
        schema_version="source-evidence/v1",
        source_root=str(root),
        ccbench_commit="abcdef0123456789",
        genome_sha256="1" * 64,
        src_token=token,
        source_bytes_sha256="2" * 64,
        tracked_clean=True,
        tracked_diff_sha256=E.source_digest.EMPTY_TRACKED_DIFF_SHA256,
        tracked_paths=(),
    )


def _stock_freeze() -> dict:
    return {"holdouts": {"H1": {"variant_binding": {"entries": {
        "stock_common": {
            "configuration": "stock_common", "flags": {"BACK_OFF": 1},
        },
    }}}}}


def test_build_snapshot_rejects_rederived_token_mismatch_and_restores_snapshot(
        tmp_path, monkeypatch):
    root = tmp_path / "snapshot"
    _write_tree(root)
    expected = E.snapshot_tree_digest(root)
    original_mode = _mode(root / "src" / "main.cc")
    prepared = S.PreparedCell(
        Genome("silo", {"BACK_OFF": 1}),
        _SNAPSHOT_TOKEN, str(root), "/cache",
    )

    monkeypatch.setattr(
        E, "produce_expected_materialization_from_declaration",
        lambda **_kwargs: expected,
    )
    monkeypatch.setattr(
        E.source_digest, "resolve_evidence",
        lambda *_args, **_kwargs: _snapshot_evidence(
            root, _DIFFERENT_SNAPSHOT_TOKEN,
        ),
    )

    declaration = _stock_freeze()["holdouts"]["H1"]["variant_binding"]["entries"][
        "stock_common"
    ]
    with pytest.raises(E.ExpectedMaterializationError, match="src-token-mismatch"):
        with E.admitted_build_snapshot(
                ccbench_commit="abcdef0123456789",
                configuration="stock_common", declaration=declaration,
                snapshot_root=root, genome=prepared.genome,
                prepared_src_token=prepared.src_token, cxx="site-cxx"):
            pytest.fail("token mismatch must reject before consumer body")
    assert _mode(root / "src" / "main.cc") == original_mode


def test_build_snapshot_rejects_change_between_exact_and_readonly(
        tmp_path, monkeypatch):
    root = tmp_path / "snapshot"
    _write_tree(root)
    expected = E.snapshot_tree_digest(root)
    prepared = S.PreparedCell(
        Genome("silo", {"BACK_OFF": 1}), _SNAPSHOT_TOKEN, str(root), "/cache",
    )
    monkeypatch.setattr(
        E, "produce_expected_materialization_from_declaration",
        lambda **_kwargs: expected,
    )
    monkeypatch.setattr(
        E, "make_snapshot_non_writable",
        lambda _root: E.SnapshotPermissionState(
            root=str(root), modes=(), tree_digest="f" * 64,
        ),
    )
    monkeypatch.setattr(E, "restore_snapshot_permissions", lambda _state: None)
    monkeypatch.setattr(
        E.source_digest, "resolve_evidence",
        lambda *_args, **_kwargs: pytest.fail("evidence must follow stable readonly tree"),
    )

    declaration = _stock_freeze()["holdouts"]["H1"]["variant_binding"]["entries"][
        "stock_common"
    ]
    with pytest.raises(
            E.ExpectedMaterializationError,
            match="pre-readonly-digest-mismatch"):
        with E.admitted_build_snapshot(
                ccbench_commit="abcdef0123456789",
                configuration="stock_common", declaration=declaration,
                snapshot_root=root, genome=prepared.genome,
                prepared_src_token=prepared.src_token, cxx="site-cxx"):
            pytest.fail("digest mismatch must reject before consumer body")


def test_build_snapshot_derives_evidence_from_non_writable_snapshot(
        tmp_path, monkeypatch):
    root = tmp_path / "snapshot"
    _write_tree(root)
    expected = E.snapshot_tree_digest(root)
    prepared = S.PreparedCell(
        Genome("silo", {"BACK_OFF": 1}),
        _SNAPSHOT_TOKEN, str(root), "/cache",
    )
    calls = []

    monkeypatch.setattr(
        E, "produce_expected_materialization_from_declaration",
        lambda **_kwargs: calls.append("reference") or expected,
    )
    real_assert = E.assert_expected_materialization
    real_readonly = E.make_snapshot_non_writable

    def exact(*args, **kwargs):
        calls.append("exact")
        return real_assert(*args, **kwargs)

    def readonly(*args, **kwargs):
        calls.append("readonly")
        return real_readonly(*args, **kwargs)

    def evidence(*_args, **_kwargs):
        calls.append("evidence")
        assert _mode(root) & 0o222 == 0
        assert _mode(root / "src" / "main.cc") & 0o222 == 0
        return _snapshot_evidence(root, _SNAPSHOT_TOKEN)

    monkeypatch.setattr(E, "assert_expected_materialization", exact)
    monkeypatch.setattr(E, "make_snapshot_non_writable", readonly)
    monkeypatch.setattr(E.source_digest, "resolve_evidence", evidence)
    declaration = _stock_freeze()["holdouts"]["H1"]["variant_binding"]["entries"][
        "stock_common"
    ]
    with E.admitted_build_snapshot(
            ccbench_commit="abcdef0123456789",
            configuration="stock_common", declaration=declaration,
            snapshot_root=root, genome=prepared.genome,
            prepared_src_token=prepared.src_token,
            cxx="site-cxx",
    ) as admitted:
        calls.append("consumer")
        assert admitted.expected_materialization_sha256 == expected
        assert admitted.source_snapshot_sha256 == expected
        assert admitted.source_evidence.src_token == prepared.src_token
        assert _mode(root / "src" / "main.cc") & 0o222 == 0
    assert calls == ["reference", "exact", "readonly", "evidence", "consumer"]
    assert _mode(root / "src" / "main.cc") & 0o200


def test_module_docstring_states_the_exact_proof_boundary():
    doc = inspect.getdoc(E) or ""
    assert "does not prove that the materializer itself is correct" in doc
    assert "same implementation" in doc
    assert "tree after materialization differs" in doc
    assert "does not claim dynamic predicate reachability" in doc
