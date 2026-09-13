# -*- coding: utf-8 -*-
"""Unit A tests for declaration-derived S8b materialization snapshots."""
from __future__ import annotations

import contextlib
import hashlib
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
    parent_mode = _mode(root.parent)
    before = E.snapshot_tree_digest(root)

    state = E.make_snapshot_non_writable(root)
    try:
        assert state.tree_digest == before
        assert E.snapshot_tree_digest(root) == before
        for path in (root, root / ".git", root / ".hidden-input",
                     root / "src", root / "src" / "main.cc"):
            assert _mode(path) & 0o222 == 0
        assert _mode(root.parent) & 0o222 == 0
    finally:
        E.restore_snapshot_permissions(state)
    restored = {
        path.relative_to(root).as_posix() if path != root else ".": _mode(path)
        for path in (root, root / ".git", root / ".hidden-input",
                     root / "src", root / "src" / "main.cc")
    }
    assert restored == original
    assert _mode(root.parent) == parent_mode


def test_reference_producer_uses_a_separate_tree_and_replays_declaration(
        tmp_path, monkeypatch):
    monkeypatch.delenv("GIT_NO_REPLACE_OBJECTS", raising=False)
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
        assert os.environ.get("GIT_NO_REPLACE_OBJECTS") == "1"
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
    assert os.environ.get("GIT_NO_REPLACE_OBJECTS") is None
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


def test_build_snapshot_reference_uses_repository_ccbench_authority(
        tmp_path, monkeypatch):
    root = tmp_path / "snapshot"
    _write_tree(root)
    expected = E.snapshot_tree_digest(root)
    captured = {}
    prepared = S.PreparedCell(
        Genome("silo", {"BACK_OFF": 1}),
        _SNAPSHOT_TOKEN, str(root), "/cache",
    )

    def reference(**kwargs):
        captured.update(kwargs)
        return expected

    monkeypatch.setattr(
        E, "produce_expected_materialization_from_declaration", reference,
    )
    monkeypatch.setattr(
        E.source_digest, "resolve_evidence",
        lambda *_args, **_kwargs: _snapshot_evidence(root, _SNAPSHOT_TOKEN),
    )
    declaration = _stock_freeze()["holdouts"]["H1"]["variant_binding"][
        "entries"
    ]["stock_common"]

    with E.admitted_build_snapshot(
            ccbench_commit="abcdef0123456789",
            configuration="stock_common", declaration=declaration,
            snapshot_root=root, genome=prepared.genome,
            prepared_src_token=prepared.src_token, cxx="site-cxx"):
        pass

    assert Path(captured["base_dir"]) == E._repository_ccbench_authority()


def test_build_snapshot_captures_declared_evolve_source_bytes_before_build(
        tmp_path, monkeypatch):
    root = tmp_path / "snapshot"
    _write_tree(root)
    evolve_source = root / "include" / "backoff.hh"
    evolve_source.parent.mkdir()
    evolve_source.write_bytes(b"// admitted predicate bytes\n")
    expected = E.snapshot_tree_digest(root)
    prepared = S.PreparedCell(
        Genome("silo", {"BACK_OFF": 1, "BACKOFF_FIXED": 2}),
        _SNAPSHOT_TOKEN, str(root), "/cache",
    )
    monkeypatch.setattr(
        E, "produce_expected_materialization_from_declaration",
        lambda **_kwargs: expected,
    )
    monkeypatch.setattr(
        E.source_digest, "resolve_evidence",
        lambda *_args, **_kwargs: _snapshot_evidence(root, _SNAPSHOT_TOKEN),
    )

    with E.admitted_build_snapshot(
            ccbench_commit="abcdef0123456789",
            configuration="backoff_fixed_best",
            declaration={
                "backoff_us": 2,
                "flags": {"BACK_OFF": 1, "BACKOFF_FIXED": 2},
                "sources": [],
            },
            snapshot_root=root, genome=prepared.genome,
            prepared_src_token=prepared.src_token,
            cxx="site-cxx",
    ) as admitted:
        assert dict(admitted.evolve_block_sources) == {
            "include/backoff.hh": hashlib.sha256(
                evolve_source.read_bytes()
            ).hexdigest(),
        }


def test_snapshot_root_inode_replacement_is_rejected(tmp_path):
    root = tmp_path / "snapshot"
    root.mkdir()
    identity = E._root_identity(root)
    displaced = tmp_path / "displaced"
    root.rename(displaced)
    root.mkdir()

    with pytest.raises(E.ExpectedMaterializationError, match="root-identity-after-build"):
        E._assert_root_identity(root, identity, stage="after-build")


def test_module_docstring_states_the_exact_proof_boundary():
    doc = inspect.getdoc(E) or ""
    assert "does not prove that the materializer itself is correct" in doc
    assert "same implementation" in doc
    assert "tree after materialization differs" in doc
    assert "does not claim dynamic predicate reachability" in doc
    assert "directory owner can restore" in doc


# Production mechanisms below are exercised without replacing dependencies.
# The low-level session receives a fixed tiny tree's admitted metadata; Git
# replay is covered above, and no real CMake build is needed here.


def _sealed_test_tree(tmp_path):
    ancestor = tmp_path / "view"
    ancestor.mkdir()
    (ancestor / "source-parent").mkdir()
    root = ancestor / "source-parent" / "source"
    _write_tree(root)
    (root / "src" / ".git").write_text("gitdir: /does/not/exist\n")
    (ancestor / "base").mkdir()
    (ancestor / "cache").mkdir()
    return root


def _tiny_session(root):
    digest = E.snapshot_tree_digest(root)
    return E.SealedBuildSession(E.AdmittedBuildSnapshot(
        source_snapshot_sha256=digest, expected_materialization_sha256=digest,
        source_evidence=_snapshot_evidence(root, _SNAPSHOT_TOKEN),
    ))


@contextlib.contextmanager
def _running_tiny_session(root):
    session = _tiny_session(root)
    try:
        session._start(root)
        yield session
    finally:
        session._finish()


def _python_command(code, *args):
    import sys
    return [sys.executable, "-I", "-B", "-c", code, *map(str, args)]


def _run_sealed_case(module, case, tmp_path, **parameters):
    """Exec a fresh interpreter: xdist workers may have multiple OS threads.

    The case retains every assertion and real protection operation. Only its
    completion report crosses processes; capabilities stay with their issuer.
    Five seconds follows the existing tiny-session command/control timeout.
    """
    import json
    import subprocess
    code = """
import contextlib, importlib, inspect, io, json, sys
from pathlib import Path
sys.path.insert(0, sys.argv[1])
module = importlib.import_module(sys.argv[2])
case = getattr(module, sys.argv[3])
parameters = json.loads(sys.argv[5])
parameters['tmp_path'] = Path(sys.argv[4])
# Import pytest without starting pytest.main, plugins, or xdist workers.
import pytest
output = io.StringIO()
try:
    with contextlib.redirect_stdout(output), pytest.MonkeyPatch.context() as patch:
        if 'monkeypatch' in inspect.signature(case).parameters:
            parameters['monkeypatch'] = patch
        case(**parameters)
finally:
    print(output.getvalue(), file=sys.stderr, end='')
print(json.dumps({'case': sys.argv[3], 'completed': True}))
"""
    result = subprocess.run(
        _python_command(code, Path(__file__).resolve().parents[2], module,
                        case, tmp_path, json.dumps(parameters)),
        capture_output=True, text=True, check=True, timeout=5,
    )
    return json.loads(result.stdout)


def _session_python(session, code, *args):
    return session.run(_python_command(code, *args), cwd="/", env=None, timeout_s=5)


def _issue_test_capability(session):
    kind = (E.SealedSnapshotProtectionKind.SEALED_BUILD if session._ran
            else E.SealedSnapshotProtectionKind.SEALED_CACHE_HIT)
    return session.issue(kind, binary_sha256=hashlib.sha256(b"binary").hexdigest(),
                         compiler_input_manifest_sha256=hashlib.sha256(b"manifest").hexdigest())


def _in_real_child(action):
    """Child setup failures fail tests; unavailable namespaces never skip."""
    import json
    reader, writer = os.pipe()
    pid = os.fork()
    if pid == 0:
        os.close(reader)
        try:
            row = {"value": action()}
        except BaseException as exc:
            row = {"error": repr(exc)}
        with os.fdopen(writer, "w") as stream:
            json.dump(row, stream)
        os._exit(0 if "value" in row else 1)
    os.close(writer)
    with os.fdopen(reader) as stream:
        row = json.load(stream)
    status = os.waitpid(pid, 0)[1]
    assert os.waitstatus_to_exitcode(status) == 0, row
    return row["value"]


_SOURCE_ATTACK = """
import json, sys
from pathlib import Path
path = Path(sys.argv[1])
original = path.read_bytes().hex()
results = []
for action in (lambda: path.chmod(0o600), lambda: path.write_bytes(b'changed')):
    try:
        action()
        results.append(0)
    except OSError as exc:
        results.append(exc.errno)
print(json.dumps([results, original, path.read_bytes().hex()]))
"""


def test_sealed_snapshot_owner_chmod_write_erofs_with_writable_control(tmp_path):
    case = "_sealed_snapshot_owner_chmod_write_erofs_with_writable_control_case"
    result = _run_sealed_case(
        "orchestrator.tests.test_s8b_expected_materialization", case, tmp_path,
    )
    assert result == {"case": case, "completed": True}


def _sealed_snapshot_owner_chmod_write_erofs_with_writable_control_case(tmp_path):
    import errno
    import json
    import subprocess
    root = _sealed_test_tree(tmp_path)
    source = root / "src" / "main.cc"
    original = source.read_bytes()
    control = subprocess.run(_python_command(_SOURCE_ATTACK, source),
                             capture_output=True, text=True, check=True, timeout=5)
    assert json.loads(control.stdout) == [[0, 0], original.hex(), b"changed".hex()]
    source.write_bytes(original)
    source.chmod(0o644)
    namespaces = {name: os.readlink("/proc/self/ns/" + name) for name in ("mnt", "user")}
    with _running_tiny_session(root) as session:
        protected = _session_python(session, _SOURCE_ATTACK, source)
        assert protected.returncode == 0, protected.stderr
        assert json.loads(protected.stdout) == [
            [errno.EROFS, errno.EROFS], original.hex(), original.hex(),
        ]
        result = _session_python(session, """
from pathlib import Path
import sys
root = Path(sys.argv[1])
assert not list(root.rglob('.git'))
assert not root.stat().st_mode & 0o222
assert not (root / 'src/main.cc').stat().st_mode & 0o222
""", root)
        assert result.returncode == 0, result.stderr
        with pytest.raises(E.ExpectedMaterializationError, match="not complete"):
            _issue_test_capability(session)
    assert _mode(source) == 0o644
    assert _issue_test_capability(session).kind is E.SealedSnapshotProtectionKind.SEALED_BUILD
    assert namespaces == {name: os.readlink("/proc/self/ns/" + name) for name in namespaces}


@pytest.mark.parametrize("state", ["capabilities", "dropped", "regained", "filtered"])
def test_shared_readonly_file_capability_and_userns_controls(tmp_path, state):
    import errno
    import subprocess
    file = tmp_path / "shared"
    file.write_bytes(b"original")
    file.chmod(0o444)

    def action():
        E._enter_snapshot_namespace()
        mounts = []
        E._mount_snapshot(file, mounts, source=os.fsencode(file), filesystem=None, flags=4096)
        assert _mode(file) == 0o444
        if state != "capabilities":
            E._drop_snapshot_capabilities()
        if state == "filtered":
            E._install_snapshot_seccomp()
        namespace_errno = None
        if state in ("regained", "filtered"):
            try:
                E._enter_snapshot_namespace()
                namespace_errno = 0
            except OSError as exc:
                namespace_errno = exc.errno
        try:
            file.write_bytes(b"changed")
            write_errno = 0
        except OSError as exc:
            write_errno = exc.errno
        result = subprocess.run(_python_command("""
import os
pid = os.fork()
if pid == 0:
    os.execve('/bin/true', ['true'], {})
assert os.waitstatus_to_exitcode(os.waitpid(pid, 0)[1]) == 0
"""), capture_output=True, text=True, timeout=5)
        assert result.returncode == 0, result.stderr
        return [write_errno, namespace_errno]

    result = _in_real_child(action)
    assert result == {
        "capabilities": [0, None], "dropped": [errno.EACCES, None],
        "regained": [0, 0], "filtered": [errno.EACCES, errno.EPERM],
    }[state]
    assert file.read_bytes() == (b"changed" if state in ("capabilities", "regained") else b"original")


def test_sealed_snapshot_shares_late_staging_and_base_inodes(tmp_path):
    case = "_sealed_snapshot_shares_late_staging_and_base_inodes_case"
    result = _run_sealed_case(
        "orchestrator.tests.test_s8b_expected_materialization", case, tmp_path,
    )
    assert result == {"case": case, "completed": True}


def _sealed_snapshot_shares_late_staging_and_base_inodes_case(tmp_path):
    import json
    root = _sealed_test_tree(tmp_path)
    ancestor = root.parent.parent
    with _running_tiny_session(root) as session:
        staging = ancestor / "cache" / "late-staging"
        staging.mkdir()
        (staging / "marker").write_bytes(b"parent")
        result = _session_python(session, """
import json, sys
from pathlib import Path
staging, base = map(Path, sys.argv[1:])
assert (staging / 'marker').read_bytes() == b'parent'
(staging / 'binary').write_bytes(b'child')
(base / 'new-entry').write_bytes(b'child')
p = staging / 'binary'
print(json.dumps([p.stat().st_dev, p.stat().st_ino]))
""", staging, ancestor / "base")
        assert result.returncode == 0, result.stderr
        binary = staging / "binary"
        assert json.loads(result.stdout) == [binary.stat().st_dev, binary.stat().st_ino]
        assert binary.read_bytes() == b"child"
        assert (ancestor / "base" / "new-entry").read_bytes() == b"child"


def test_sealed_session_root_replacement_refuses_issue_and_restores_original(tmp_path):
    case = "_sealed_session_root_replacement_refuses_issue_and_restores_original_case"
    result = _run_sealed_case(
        "orchestrator.tests.test_s8b_expected_materialization", case, tmp_path,
    )
    assert result == {"case": case, "completed": True}


def _sealed_session_root_replacement_refuses_issue_and_restores_original_case(tmp_path):
    root = _sealed_test_tree(tmp_path)
    original = (root / "src/main.cc").read_bytes()
    old_mode = _mode(root)
    displaced = root.with_name("displaced")
    with pytest.raises(E.ExpectedMaterializationError, match="root-identity-after-build"):
        with _running_tiny_session(root) as session:
            root.parent.chmod(0o700)
            root.rename(displaced)
            _write_tree(root)
            (root / "src/main.cc").write_bytes(b"replacement")
            result = _session_python(session,
                "from pathlib import Path; import sys; print(Path(sys.argv[1]).read_bytes().hex())",
                root / "src/main.cc")
            assert result.returncode == 0, result.stderr
            assert result.stdout.strip() == original.hex()
    assert _mode(displaced) == old_mode
    with pytest.raises(E.ExpectedMaterializationError, match="not complete"):
        _issue_test_capability(session)
    with pytest.raises(E.ExpectedMaterializationError, match="cannot run"):
        _session_python(session, "pass")


def test_sealed_session_abnormal_worker_refuses_issue_without_poisoning_parent(tmp_path):
    case = "_sealed_session_abnormal_worker_refuses_issue_without_poisoning_parent_case"
    result = _run_sealed_case(
        "orchestrator.tests.test_s8b_expected_materialization", case, tmp_path,
    )
    assert result == {"case": case, "completed": True}


def _sealed_session_abnormal_worker_refuses_issue_without_poisoning_parent_case(tmp_path):
    root = _sealed_test_tree(tmp_path)
    with pytest.raises(E.ExpectedMaterializationError):
        with _running_tiny_session(root) as session:
            _session_python(session, "import os, signal; os.kill(os.getppid(), signal.SIGKILL)")
    with pytest.raises(E.ExpectedMaterializationError, match="not complete"):
        _issue_test_capability(session)
    with _running_tiny_session(root) as healthy:
        assert _session_python(healthy, "pass").returncode == 0
    _issue_test_capability(healthy)


def test_sealed_session_reaps_detached_descendants_before_issue(tmp_path):
    case = "_sealed_session_reaps_detached_descendants_before_issue_case"
    result = _run_sealed_case(
        "orchestrator.tests.test_s8b_expected_materialization", case, tmp_path,
    )
    assert result == {"case": case, "completed": True}


def _sealed_session_reaps_detached_descendants_before_issue_case(tmp_path):
    root = _sealed_test_tree(tmp_path)
    marker = root.parent.parent / "cache" / "pid"
    with _running_tiny_session(root) as session:
        result = _session_python(session, """
import os, sys, time
pid = os.fork()
if pid == 0:
    os.setsid()
    for fd in (0, 1, 2):
        os.close(fd)
    while True:
        time.sleep(1)
from pathlib import Path
Path(sys.argv[1]).write_text(str(pid))
""", marker)
        assert result.returncode == 0, result.stderr
    pid = int(marker.read_text())
    with pytest.raises(ProcessLookupError):
        os.kill(pid, 0)
    _issue_test_capability(session)


def test_sealed_capability_exact_identity_and_binary_manifest_bindings(tmp_path):
    case = "_sealed_capability_exact_identity_and_binary_manifest_bindings_case"
    result = _run_sealed_case(
        "orchestrator.tests.test_s8b_expected_materialization", case, tmp_path,
    )
    assert result == {"case": case, "completed": True}


def _sealed_capability_exact_identity_and_binary_manifest_bindings_case(tmp_path):
    import dataclasses
    import json
    import pickle
    root = _sealed_test_tree(tmp_path)
    with _running_tiny_session(root) as session:
        pass
    capability = _issue_test_capability(session)
    assert capability.kind is E.SealedSnapshotProtectionKind.SEALED_CACHE_HIT
    bindings = {name: getattr(capability, name) for name in (
        "source_snapshot_sha256", "expected_materialization_sha256",
        "binary_sha256", "compiler_input_manifest_sha256",
    )}
    assert E.validate_sealed_snapshot_capability(capability, **bindings) is capability
    for field in ("binary_sha256", "compiler_input_manifest_sha256"):
        altered = dict(bindings, **{field: hashlib.sha256(b"different").hexdigest()})
        with pytest.raises(E.ExpectedMaterializationError, match=field):
            E.validate_sealed_snapshot_capability(capability, **altered)
    with pytest.raises(E.ExpectedMaterializationError, match="requires issue"):
        E.SealedSnapshotCapability(kind=capability.kind, **bindings)
    reconstructed = json.loads(json.dumps({**bindings, "kind": capability.kind.value}))
    for fake in (SimpleNamespace(**dataclasses.asdict(capability)),
                 pickle.loads(pickle.dumps(capability)), reconstructed):
        with pytest.raises(E.ExpectedMaterializationError, match="not issued"):
            E.validate_sealed_snapshot_capability(fake, **bindings)
    with pytest.raises(E.ExpectedMaterializationError, match="differs from execution"):
        session.issue(E.SealedSnapshotProtectionKind.SEALED_BUILD,
                      binary_sha256=bindings["binary_sha256"],
                      compiler_input_manifest_sha256=bindings["compiler_input_manifest_sha256"])


def test_normal_unmount_busy_control_and_session_issue_rejection(tmp_path):
    """A real busy mount fails; closing the held fd makes unmount succeed.

    The child harness reports that actual failure through the production parent
    finish/issue protocol. No syscall or dependency is replaced.
    """
    import socket
    root = _sealed_test_tree(tmp_path)
    session = _tiny_session(root)
    parent, child = socket.socketpair()
    pid = os.fork()
    if pid == 0:
        parent.close()
        stream = child.makefile("rw")
        mounts = []
        try:
            assert E._read_snapshot_message(stream) == {"finish": True}
            E._enter_snapshot_namespace()
            E._mount_snapshot(root, mounts, data=b"size=1m")
            held = os.open(root, os.O_RDONLY | os.O_DIRECTORY)
            try:
                try:
                    E._unmount_snapshot(mounts)
                except E.ExpectedMaterializationError as exc:
                    import errno
                    assert isinstance(exc.__cause__, OSError)
                    assert exc.__cause__.errno == errno.EBUSY
                else:
                    raise AssertionError("busy unmount did not fail")
            finally:
                os.close(held)
            E._unmount_snapshot(mounts)
            E._send_snapshot_message(stream, {"error": "snapshot normal unmount failed"})
            os._exit(1)
        except BaseException as exc:
            E._send_snapshot_message(stream, {"error": "test setup: " + repr(exc)})
            os._exit(2)
    child.close()
    session._pid = pid
    session._connection = parent
    session._stream = parent.makefile("rw")
    with pytest.raises(E.ExpectedMaterializationError, match="child: snapshot normal unmount failed"):
        session._finish()
    with pytest.raises(E.ExpectedMaterializationError, match="not complete"):
        _issue_test_capability(session)
    with pytest.raises(E.ExpectedMaterializationError, match="cannot run"):
        _session_python(session, "pass")


def test_sealed_session_requires_one_real_os_thread(tmp_path):
    import threading
    root = _sealed_test_tree(tmp_path)
    ready, release = threading.Event(), threading.Event()
    thread = threading.Thread(target=lambda: (ready.set(), release.wait()))
    thread.start()
    ready.wait()
    session = _tiny_session(root)
    try:
        with pytest.raises(E.ExpectedMaterializationError, match="exactly one OS thread"):
            session._start(root)
    finally:
        release.set()
        thread.join()
        with pytest.raises(E.ExpectedMaterializationError):
            session._finish()
    with pytest.raises(E.ExpectedMaterializationError, match="not complete"):
        _issue_test_capability(session)


def test_sealed_session_permission_restore_failure_refuses_issue(tmp_path):
    case = "_sealed_session_permission_restore_failure_refuses_issue_case"
    result = _run_sealed_case(
        "orchestrator.tests.test_s8b_expected_materialization", case, tmp_path,
    )
    assert result == {"case": case, "completed": True}


def _sealed_session_permission_restore_failure_refuses_issue_case(tmp_path):
    root = _sealed_test_tree(tmp_path)
    originals = [(path, _mode(path)) for path in (root.parent, root, *root.rglob("*"))]
    session = _tiny_session(root)
    try:
        session._start(root)
        # A real EBADF from the retained anchor must invalidate completion.
        os.close(session._permission_state.root_fd)
        with pytest.raises(E.ExpectedMaterializationError, match="permission-restore"):
            session._finish()
        with pytest.raises(E.ExpectedMaterializationError, match="not complete"):
            _issue_test_capability(session)
    finally:
        if not session._finished:
            session._finish()
        for path, mode in originals:
            path.chmod(mode)


@pytest.mark.parametrize("matching", [True, False])
def test_private_copy_digest_is_checked_before_seal(tmp_path, matching):
    root = _sealed_test_tree(tmp_path)
    expected = E.snapshot_tree_digest(root)

    def action():
        E._enter_snapshot_namespace()
        mounts = []
        try:
            digest = expected if matching else hashlib.sha256(b"different").hexdigest()
            try:
                E._snapshot_root_view(root, digest, mounts)
            except E.ExpectedMaterializationError as exc:
                assert not matching
                assert "copy digest mismatch" in str(exc)
                return "rejected"
            assert matching
            assert E.snapshot_tree_digest(root) == expected
            return "sealed"
        finally:
            E._unmount_snapshot(mounts)

    assert _in_real_child(action) == ("sealed" if matching else "rejected")


def _run() -> int:
    return pytest.main([__file__, "-q"])


if __name__ == "__main__":
    raise SystemExit(_run())
