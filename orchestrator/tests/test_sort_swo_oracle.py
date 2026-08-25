# -*- coding: utf-8 -*-
"""Independent sort SWO oracle: matrix laws, real C++ E2E, and constraints."""
from __future__ import annotations

import contextlib
import inspect
import json
from pathlib import Path
import shutil
import subprocess
import sys

import pytest

from orchestrator.campaign import sort_swo_oracle as O
from orchestrator.tests import sort_swo_masstree_fixture as masstree_fixture
from orchestrator.tests import sort_swo_oracle_receipt_memo as oracle_environment_memo


_ROOT = Path(__file__).resolve().parents[2]
_CCBENCH = _ROOT / "external" / "ccbench"


def _get_oracle_environment():
    """Read the controller-prewarmed environment snapshot, fail-closed."""
    return oracle_environment_memo.get_oracle_environment()


_CLEAN_IMPL = (
    "    sort(write_set_.begin(), write_set_.end(),\n"
    "         [](const auto& a, const auto& b) { return a.key_ < b.key_; });"
)
_MULTIPLEXED_NEGATIVE_IMPL = r'''
    sort(write_set_.begin(), write_set_.end(),
         [](const auto& a, const auto& b) {
           if (oracle_test_mode == 1) return &a == &b;
           if (oracle_test_mode == 2) return &a != &b;
           if (oracle_test_mode == 3)
             return ((static_cast<unsigned>(a.storage_) % 3u) + 1u) % 3u
                    == static_cast<unsigned>(b.storage_) % 3u;
           if (oracle_test_mode == 4)
             return static_cast<unsigned>(a.storage_) == 0u
                    && static_cast<unsigned>(b.storage_) == 2u;
           if (oracle_test_mode == 5) {
             if (static_cast<unsigned>(a.storage_) >= 0x80000000u
                 && static_cast<unsigned>(b.storage_) >= 0x80000000u)
               return &a != &b;
             return a.storage_ < b.storage_;
           }
           if (oracle_test_mode == 6) {
             const_cast<WriteElement<Tuple>&>(a).storage_ = static_cast<Storage>(123u);
             return false;
           }
           if (oracle_test_mode == 7) {
             static unsigned calls = 0;
             ++calls;
             return calls > N * N && &a == &b;
           }
           return std::less<Tuple*>{}(a.rcdptr_, b.rcdptr_);
         });
'''


def _materialized(statement: str) -> str:
    return (
        "// EVOLVE-BLOCK-BEGIN silo-writeset-sort\n"
        "#if SORT_VARIANT\n"
        f"{statement}\n"
        "#else\n"
        "sort(write_set_.begin(), write_set_.end());\n"
        "#endif\n"
        "// EVOLVE-BLOCK-END silo-writeset-sort\n"
    )


def _receipt(materialized_hash: str = "1" * 64,
             proposal_hash: str = "2" * 64) -> O.OracleReceipt:
    return O.OracleReceipt(
        contract_id=O.ORACLE_CONTRACT_ID,
        materialized_hole_sha256=materialized_hash,
        proposal_sha256=proposal_hash,
        corpus_id=O.CORPUS_ID,
        corpus_version=O.CORPUS_VERSION,
        compiler_realpath="/fixture/cxx",
        compiler_version="fixture-cxx 1",
        compile_flags_sha256=O.COMPILE_FLAGS_SHA256,
        tu_sha256="3" * 64,
        tu_template_sha256=O.TU_TEMPLATE_SHA256,
        dependency_root_realpath="/fixture/dependency",
        dependency_config_sha256="4" * 64,
    )


_COMPILED_ORACLE_ARTIFACTS = None
_COMPILED_ORACLE_ARTIFACTS_FACTORY = None


def _get_compiled_oracle_artifacts(tmp_path_factory):
    """Exactly two real compiles: one positive TU and one multiplexed negative TU."""
    global _COMPILED_ORACLE_ARTIFACTS, _COMPILED_ORACLE_ARTIFACTS_FACTORY
    if (
        _COMPILED_ORACLE_ARTIFACTS is not None
        and _COMPILED_ORACLE_ARTIFACTS_FACTORY is tmp_path_factory
    ):
        return _COMPILED_ORACLE_ARTIFACTS
    oracle_environment = _get_oracle_environment()
    assert type(oracle_environment) is O.OracleEnvironment, (
        "real oracle E2E requires an injected oracle environment"
    )
    scratch = tmp_path_factory.mktemp("sort-swo-real")
    artifacts = {}
    compile_count = 0
    for name, statement in (
        ("positive", _CLEAN_IMPL),
        ("negative", _MULTIPLEXED_NEGATIVE_IMPL),
    ):
        executable = scratch / name
        finding, unavailable = O._compile(
            O._translation_unit(statement), scratch / f"{name}.cpp", executable,
            compiler=str(oracle_environment.compiler), ccbench_dir=oracle_environment.ccbench_dir,
            masstree_dir=oracle_environment.dependency_root,
        )
        compile_count += 1
        assert unavailable is False
        assert finding is None
        artifacts[name] = executable
    artifacts["compile_count"] = compile_count
    artifacts["environment"] = oracle_environment
    _COMPILED_ORACLE_ARTIFACTS_FACTORY = tmp_path_factory
    _COMPILED_ORACLE_ARTIFACTS = artifacts
    return artifacts


def _copy_masstree_fixture(tmp_path: Path) -> Path:
    destination = tmp_path / "sort-swo-masstree"
    shutil.copytree(masstree_fixture.FIXTURE_ROOT, destination)
    return destination


def _matrix(n: int, true_pairs: set[tuple[int, int]]) -> list[bool]:
    return [(lhs, rhs) in true_pairs for lhs in range(n) for rhs in range(n)]


@pytest.mark.parametrize(
    ("true_pairs", "axiom", "pairs"),
    [
        ({(0, 0)}, O.SwoAxiom.IRREFLEXIVE, ((0, 0),)),
        ({(0, 1), (1, 0)}, O.SwoAxiom.ASYMMETRIC, ((0, 1), (1, 0))),
        ({(0, 1), (1, 2)}, O.SwoAxiom.TRANSITIVE,
         ((0, 1), (1, 2), (0, 2))),
        ({(0, 2)}, O.SwoAxiom.TRANSITIVE_EQUIVALENCE,
         ((0, 1), (1, 2), (0, 2), (2, 0))),
    ],
    ids=["irreflexive", "asymmetric", "transitive", "equivalence-transitive"],
)
def test_matrix_checker_reports_each_axiom_and_exact_indices(true_pairs, axiom, pairs):
    counterexample = O.check_relation_matrix(_matrix(3, true_pairs), 3)
    assert counterexample is not None
    assert counterexample.axiom is axiom
    assert counterexample.input_pairs == pairs


def test_matrix_checker_accepts_strict_weak_order():
    relation = {(lhs, rhs) for lhs in range(4) for rhs in range(4) if lhs < rhs}
    assert O.check_relation_matrix(_matrix(4, relation), 4) is None


def test_cpp_e2e_clean_generic_lambda_positive(tmp_path_factory):
    """P1: the existing const-auto-ref, omitted-return-type fixture passes."""
    compiled_oracle_artifacts = _get_compiled_oracle_artifacts(tmp_path_factory)
    assert O._evaluate_executable(compiled_oracle_artifacts["positive"]) is None


def test_cpp_e2e_stable_cross_allocation_pointer_positive(tmp_path_factory):
    """P2: std::less compares pointers from separate allocations stably and passes."""
    compiled_oracle_artifacts = _get_compiled_oracle_artifacts(tmp_path_factory)
    assert O._evaluate_executable(
        compiled_oracle_artifacts["negative"], test_mode=0,
    ) is None


def test_real_ctor_pointer_topology_and_triplicate_have_expected_matrix_meaning(
        tmp_path_factory):
    compiled_oracle_artifacts = _get_compiled_oracle_artifacts(tmp_path_factory)
    pointer_matrix, pointer_finding = O._run_matrix(
        compiled_oracle_artifacts["negative"], 0, 0, test_mode=0,
    )
    assert pointer_finding is None and pointer_matrix is not None
    # Corpus-0 indices 5 and 6 are distinct allocation slots. std::less must
    # order exactly one direction after the real WriteElement ctor.
    assert O._CORPUS_MANIFEST[0][5][2:] == (2, 0)
    assert O._CORPUS_MANIFEST[0][6][2:] == (2, 1)
    assert bool(pointer_matrix[5 * O._N + 6]) != bool(pointer_matrix[6 * O._N + 5])

    key_matrix, key_finding = O._run_matrix(
        compiled_oracle_artifacts["positive"], 0, 0,
    )
    assert key_finding is None and key_matrix is not None
    assert O._CORPUS_MANIFEST[0][:3] == (
        (0, b"", 1, 0), (0, b"", 1, 0), (0, b"", 1, 0),
    )
    assert all(
        key_matrix[lhs * O._N + rhs] == 0
        for lhs in range(3) for rhs in range(3)
    )


@pytest.mark.parametrize(
    ("mode", "axiom", "pairs"),
    [
        (1, O.SwoAxiom.IRREFLEXIVE, ((0, 0),)),
        (2, O.SwoAxiom.ASYMMETRIC, ((0, 1), (1, 0))),
        (3, O.SwoAxiom.TRANSITIVE, ((0, 3), (3, 4), (0, 4))),
        (4, O.SwoAxiom.TRANSITIVE_EQUIVALENCE,
         ((0, 3), (3, 4), (0, 4), (4, 0))),
    ],
    ids=["irreflexive", "asymmetric", "transitive", "equivalence-transitive"],
)
def test_cpp_e2e_reports_each_axiom_and_exact_indices(
        tmp_path_factory, mode, axiom, pairs):
    compiled_oracle_artifacts = _get_compiled_oracle_artifacts(tmp_path_factory)
    finding = O._evaluate_executable(
        compiled_oracle_artifacts["negative"], test_mode=mode,
    )
    assert finding is not None
    assert finding.kind is O.OracleRejectKind.AXIOM
    assert finding.counterexample is not None
    assert finding.counterexample.axiom is axiom
    assert finding.counterexample.input_pairs == pairs


def test_cpp_e2e_high_storage_only_negative_kills_corpus_narrowing(
        tmp_path_factory):
    compiled_oracle_artifacts = _get_compiled_oracle_artifacts(tmp_path_factory)
    finding = O._evaluate_executable(
        compiled_oracle_artifacts["negative"], test_mode=5,
    )
    assert finding is not None
    assert finding.kind is O.OracleRejectKind.AXIOM
    assert finding.counterexample is not None
    assert finding.counterexample.axiom is O.SwoAxiom.ASYMMETRIC
    assert finding.counterexample.input_pairs == ((6, 7), (7, 6))


def test_cpp_e2e_rejects_corpus_mutation_with_dedicated_reason(
        tmp_path_factory):
    compiled_oracle_artifacts = _get_compiled_oracle_artifacts(tmp_path_factory)
    finding = O._evaluate_executable(
        compiled_oracle_artifacts["negative"], test_mode=6,
    )
    assert finding is not None
    assert finding.kind is O.OracleRejectKind.MUTATION
    assert finding.reason_code == "corpus-mutated-by-comparator"
    assert finding.input_pairs == ((0, 0),)


def test_cpp_e2e_rejects_same_process_call_count_dependence_with_witness(
        tmp_path_factory):
    compiled_oracle_artifacts = _get_compiled_oracle_artifacts(tmp_path_factory)
    finding = O._evaluate_executable(
        compiled_oracle_artifacts["negative"], test_mode=7,
    )
    assert finding is not None
    assert finding.kind is O.OracleRejectKind.NONDETERMINISTIC
    assert finding.reason_code == "relation-varies-within-process"
    assert finding.input_pairs == ((17, 17),)
    assert [item["point"] for item in finding.observations] == [
        "first-pass", "second-pass-after-other-pairs",
    ]


def test_real_compile_budget_is_fixed_positive_and_negative_only(tmp_path_factory):
    compiled_oracle_artifacts = _get_compiled_oracle_artifacts(tmp_path_factory)
    assert compiled_oracle_artifacts["compile_count"] == 2


def test_cpp_e2e_canonical_fixture_trusted_control_compiles_and_runs(
        tmp_path_factory):
    verified = masstree_fixture.verify_sort_swo_masstree_fixture()
    assert type(verified) is masstree_fixture.VerifiedFixture
    assert verified.root == masstree_fixture.FIXTURE_ROOT.resolve()
    assert verified.manifest_sha256 == (
        "8d0151cfaa0b86d1a2753e69f514633ec2fe6ee1077caed819fd3a426b501875"
    )
    assert len(verified.files) == 101
    assert {"AUTHORS", "LICENSE", "PIN", "config.h"} <= {
        path for path, _digest in verified.files
    }
    assert (verified.root / "PIN").read_text(encoding="ascii") == (
        masstree_fixture.PIN + "\n"
    )
    assert not any(
        Path(path).suffix in {".a", ".o"} for path, _digest in verified.files
    )

    compiled_oracle_artifacts = _get_compiled_oracle_artifacts(tmp_path_factory)
    environment = compiled_oracle_artifacts["environment"]
    assert type(environment) is O.OracleEnvironment
    assert environment.dependency_root == masstree_fixture.FIXTURE_ROOT.resolve()
    assert O._evaluate_executable(compiled_oracle_artifacts["positive"]) is None


def test_masstree_manifest_rejects_header_removed_from_manifest(tmp_path):
    fixture = _copy_masstree_fixture(tmp_path)
    manifest = fixture / masstree_fixture.MANIFEST_NAME
    target_suffix = "  btree_leaflink.hh"
    lines = manifest.read_text(encoding="utf-8").splitlines()
    assert sum(line.endswith(target_suffix) for line in lines) == 1
    manifest.write_text(
        "\n".join(line for line in lines if not line.endswith(target_suffix))
        + "\n",
        encoding="utf-8",
    )

    assert masstree_fixture.verify_sort_swo_masstree_fixture(fixture) == (
        masstree_fixture.FixtureVerificationFailure(
            "fixture-file-set-mismatch",
            unregistered_files=("btree_leaflink.hh",),
        )
    )


def test_masstree_manifest_rejects_unregistered_fixture_file(tmp_path):
    fixture = _copy_masstree_fixture(tmp_path)
    (fixture / "unregistered.fixture").write_bytes(b"unregistered\n")

    assert masstree_fixture.verify_sort_swo_masstree_fixture(fixture) == (
        masstree_fixture.FixtureVerificationFailure(
            "fixture-file-set-mismatch",
            unregistered_files=("unregistered.fixture",),
        )
    )


def test_masstree_manifest_rejects_missing_fixture_file(tmp_path):
    fixture = _copy_masstree_fixture(tmp_path)
    (fixture / "btree_leaflink.hh").unlink()

    assert masstree_fixture.verify_sort_swo_masstree_fixture(fixture) == (
        masstree_fixture.FixtureVerificationFailure(
            "fixture-file-set-mismatch",
            missing_files=("btree_leaflink.hh",),
        )
    )


def test_masstree_manifest_rejects_one_byte_change(tmp_path):
    fixture = _copy_masstree_fixture(tmp_path)
    authors = fixture / "AUTHORS"
    changed = bytearray(authors.read_bytes())
    changed[0] ^= 1
    authors.write_bytes(changed)

    assert masstree_fixture.verify_sort_swo_masstree_fixture(fixture) == (
        masstree_fixture.FixtureVerificationFailure(
            "fixture-sha256-mismatch",
            hash_mismatches=(masstree_fixture.FixtureHashMismatch(
                "AUTHORS",
                "a79b96cd3f5e1734cc772598f4005302b296e349ae03d504305dbf9ffe00be9e",
                "bdee444412ea1acce2afbdf1cb221c398fe0a58bd52baa2e564334041ea2e721",
            ),),
        )
    )


def test_masstree_manifest_rejects_symlink_outside_fixture(tmp_path):
    fixture = _copy_masstree_fixture(tmp_path)
    outside = tmp_path / "outside.fixture"
    outside.write_bytes(b"outside\n")
    (fixture / "outside-link").symlink_to(outside)

    assert masstree_fixture.verify_sort_swo_masstree_fixture(fixture) == (
        masstree_fixture.FixtureVerificationFailure(
            "fixture-symlink-present", paths=("outside-link",),
        )
    )


def test_masstree_manifest_rejects_parent_reference(tmp_path):
    fixture = _copy_masstree_fixture(tmp_path)
    manifest = fixture / masstree_fixture.MANIFEST_NAME
    lines = manifest.read_text(encoding="utf-8").splitlines()
    assert lines[1].endswith("  AUTHORS")
    lines[1] = lines[1].replace("  AUTHORS", "  ../outside.fixture")
    manifest.write_text("\n".join(lines) + "\n", encoding="utf-8")

    assert masstree_fixture.verify_sort_swo_masstree_fixture(fixture) == (
        masstree_fixture.FixtureVerificationFailure(
            "fixture-manifest-invalid",
        )
    )


def test_resolver_config_h_missing_is_exact_failure_not_skip(tmp_path):
    fixture = _copy_masstree_fixture(tmp_path)
    (fixture / "config.h").unlink()

    resolution = O.resolve_oracle_environment(
        _CCBENCH,
        compiler=sys.executable,
        dependency_root=fixture,
    )
    assert resolution == O.OracleEnvironmentResolutionFailure(
        "oracle-environment-dependency-unresolved",
        (O.OracleEnvironmentCandidate(
            "argument:compiler", Path(sys.executable), "selected",
        ),),
        (O.OracleEnvironmentCandidate(
            "argument:dependency-root", fixture, "config-h-missing",
        ),),
    )


def test_resolver_dedicated_environment_root_is_selected(monkeypatch, tmp_path):
    dependency = tmp_path / "environment-masstree"
    dependency.mkdir()
    (dependency / "config.h").write_text("#pragma once\n", encoding="utf-8")
    monkeypatch.setenv("IZANAGI_SORT_SWO_MASSTREE_ROOT", str(dependency))

    resolution = O.resolve_oracle_environment(
        tmp_path / "checkout",
        compiler=sys.executable,
    )
    assert resolution == O.OracleEnvironment(
        Path(sys.executable).resolve(),
        (tmp_path / "checkout").resolve(),
        dependency.resolve(),
    )


def test_resolver_without_explicit_root_rejects_ccbench_build_residue(
        monkeypatch, tmp_path):
    ccbench = tmp_path / "checkout"
    residue = ccbench / "build" / "_deps" / "masstree-src"
    residue.mkdir(parents=True)
    (residue / "config.h").write_text("#pragma once\n", encoding="utf-8")
    monkeypatch.delenv("IZANAGI_SORT_SWO_MASSTREE_ROOT", raising=False)

    resolution = O.resolve_oracle_environment(
        ccbench,
        compiler=sys.executable,
    )
    assert resolution == O.OracleEnvironmentResolutionFailure(
        "oracle-environment-dependency-unresolved",
        (O.OracleEnvironmentCandidate(
            "argument:compiler", Path(sys.executable), "selected",
        ),),
        (O.OracleEnvironmentCandidate(
            "environment:IZANAGI_SORT_SWO_MASSTREE_ROOT",
            None,
            "not-configured",
        ),),
    )


def test_resolver_without_explicit_root_rejects_synthetic_ancestor_cache(
        monkeypatch, tmp_path):
    ccbench = tmp_path / "izanagi" / "external" / "ccbench"
    ccbench.mkdir(parents=True)
    synthetic = tmp_path / "izanagi-thirdparty-cache" / "masstree"
    synthetic.mkdir(parents=True)
    (synthetic / "config.h").write_text("#pragma once\n", encoding="utf-8")
    monkeypatch.delenv("IZANAGI_SORT_SWO_MASSTREE_ROOT", raising=False)

    resolution = O.resolve_oracle_environment(
        ccbench,
        compiler=sys.executable,
    )
    assert resolution == O.OracleEnvironmentResolutionFailure(
        "oracle-environment-dependency-unresolved",
        (O.OracleEnvironmentCandidate(
            "argument:compiler", Path(sys.executable), "selected",
        ),),
        (O.OracleEnvironmentCandidate(
            "environment:IZANAGI_SORT_SWO_MASSTREE_ROOT",
            None,
            "not-configured",
        ),),
    )


def test_oracle_environment_memo_explicitly_binds_canonical_fixture(monkeypatch):
    """The sole production resolver call cannot drift back to ambient lookup."""
    calls = []
    sentinel = object()

    def resolve(*args, **kwargs):
        calls.append((args, kwargs))
        return sentinel

    monkeypatch.setattr(oracle_environment_memo, "_PRODUCTION_RESOLVE", resolve)
    assert oracle_environment_memo._resolve_now() is sentinel
    assert calls == [(
        (oracle_environment_memo.CCBENCH,),
        {"dependency_root": oracle_environment_memo.MASSTREE_FIXTURE},
    )]
    assert oracle_environment_memo.MASSTREE_FIXTURE == (
        Path(__file__).resolve().parent / "fixtures" / "sort_swo_masstree"
    )


def test_real_patchharness_checkout_and_resolver_use_explicit_binding(tmp_path):
    """模擬を介さず共有 submodule の実 worktree と実 resolver を結ぶ。"""
    from orchestrator.campaign import patchharness

    compiler = shutil.which("g++")
    assert compiler is not None
    dependency = tmp_path / "masstree"
    dependency.mkdir()
    (dependency / "config.h").write_text("#pragma once\n", encoding="utf-8")
    head = subprocess.run(
        ["git", "-C", str(_CCBENCH), "rev-parse", "--verify", "HEAD"],
        check=True, capture_output=True, text=True,
    ).stdout.strip()

    with patchharness.checkout(head, base_dir=str(_CCBENCH)) as checkout:
        resolution = O.resolve_oracle_environment(
            checkout,
            compiler=compiler,
            dependency_root=dependency,
        )
        assert type(resolution) is O.OracleEnvironment
        assert resolution.ccbench_dir == Path(checkout).resolve()
        assert resolution.ccbench_dir != _CCBENCH.resolve()
        assert resolution.compiler == Path(compiler).resolve()
        assert resolution.dependency_root == dependency.resolve()


def test_materialized_marker_bytes_are_exact_and_proposal_hash_is_distinct(
        monkeypatch):
    oracle_environment = _get_oracle_environment()
    statement = "  " + _CLEAN_IMPL + "\n"
    source = _materialized(statement)
    observed = O.extract_materialized_hole(source, "silo-writeset-sort")
    assert observed == statement + "\n"
    monkeypatch.setattr(O, "_compile", lambda *args, **kwargs: (None, False))
    monkeypatch.setattr(O, "_evaluate_executable", lambda executable: None)
    result = O.check_materialized_sort_swo(
        source,
        marker_id="silo-writeset-sort",
        proposal_source=_CLEAN_IMPL,
        environment=oracle_environment,
    )
    assert result.status is O.OracleStatus.PASS
    assert result.materialized_hole_sha256 == O._sha256(observed)
    assert result.proposal_sha256 == O._sha256(_CLEAN_IMPL)
    assert result.materialized_hole_sha256 != result.proposal_sha256
    assert result.receipt is not None
    assert result.receipt.contract_id == O.ORACLE_CONTRACT_ID
    assert result.receipt.corpus_id == O.CORPUS_ID
    assert result.receipt.compile_flags_sha256 == O.COMPILE_FLAGS_SHA256
    assert result.receipt.tu_template_sha256 == O.TU_TEMPLATE_SHA256
    assert result.receipt.tu_sha256 == O._sha256(O._translation_unit(observed))
    attempt = O.attempt_record(result)
    assert attempt["classification"] == "pass"
    assert attempt["oracle_receipt"] == result.receipt.as_dict()


@pytest.mark.parametrize(
    ("statement", "reason"),
    [
        ("std::sort(write_set_.begin(), write_set_.end());", "qualified-or-non-sort-callee"),
        ("sort(write_set_.begin(), write_set_.end()); other();", "not-a-single-sort-statement"),
    ],
)
def test_structure_rejects_oracle_bypass_and_multiple_statements(statement, reason):
    result = O.check_materialized_sort_swo(
        _materialized(statement), marker_id="silo-writeset-sort",
        proposal_source=statement, environment=None,
    )
    assert result.status is O.OracleStatus.REJECT
    assert result.finding is not None
    assert result.finding.kind is O.OracleRejectKind.STRUCTURE
    assert result.finding.reason_code == reason


def test_unresolved_environment_is_unavailable_not_candidate_reject():
    result = O.check_materialized_sort_swo(
        _materialized(_CLEAN_IMPL), marker_id="silo-writeset-sort",
        proposal_source=_CLEAN_IMPL, environment=None,
    )
    assert result.status is O.OracleStatus.UNAVAILABLE
    assert result.finding is None
    assert result.infrastructure is not None
    assert result.infrastructure.reason_code == O.INFRASTRUCTURE_REASON_CODE


def test_phase_marker_runs_immediately_before_first_oracle_subprocess(
        monkeypatch):
    oracle_environment = _get_oracle_environment()
    assert type(oracle_environment) is O.OracleEnvironment
    order = []

    def compiler_version(_compiler):
        order.append("compiler-subprocess")
        return "fixture-cxx 1"

    monkeypatch.setattr(O, "_compiler_version", compiler_version)
    monkeypatch.setattr(O, "_compile", lambda *args, **kwargs: (None, False))
    monkeypatch.setattr(O, "_evaluate_executable", lambda _executable: None)
    result = O.check_materialized_sort_swo(
        _materialized(_CLEAN_IMPL),
        marker_id="silo-writeset-sort",
        proposal_source=_CLEAN_IMPL,
        environment=oracle_environment,
        phase_marker=lambda: order.append("phase-marker"),
    )
    assert result.status is O.OracleStatus.PASS
    assert order[:2] == ["phase-marker", "compiler-subprocess"]


@pytest.mark.parametrize(
    ("compiler_ok", "dependency_ok", "detail_code", "failed_legs"),
    [
        (
            False,
            True,
            "oracle-environment-compiler-unresolved",
            ("compiler",),
        ),
        (
            True,
            False,
            "oracle-environment-dependency-unresolved",
            ("dependency",),
        ),
        (
            False,
            False,
            "oracle-environment-compiler-and-dependency-unresolved",
            ("compiler", "dependency"),
        ),
    ],
    ids=["compiler", "dependency", "both"],
)
def test_resolver_failure_union_has_three_closed_legs_and_candidate_outcomes(
        tmp_path, compiler_ok, dependency_ok, detail_code, failed_legs):
    compiler = Path(sys.executable) if compiler_ok else tmp_path / "missing-cxx"
    dependency = tmp_path / ("masstree-ok" if dependency_ok else "masstree-missing")
    dependency.mkdir()
    if dependency_ok:
        (dependency / "config.h").write_text("#pragma once\n", encoding="utf-8")

    resolution = O.resolve_oracle_environment(
        tmp_path / "disposable-checkout",
        compiler=compiler,
        dependency_root=dependency,
    )
    assert type(resolution) is O.OracleEnvironmentResolutionFailure
    assert resolution.detail_code == detail_code
    assert resolution.failed_legs == failed_legs
    assert [item.origin for item in resolution.compiler_candidates] == [
        "argument:compiler"
    ]
    assert [item.origin for item in resolution.dependency_candidates] == [
        "argument:dependency-root"
    ]
    assert resolution.compiler_candidates[0].outcome == (
        "selected" if compiler_ok else "missing"
    )
    assert resolution.dependency_candidates[0].outcome == (
        "selected" if dependency_ok else "config-h-missing"
    )


def test_resolution_private_and_durable_projections_do_not_share_full_path(tmp_path):
    missing_dependency = tmp_path / "private-machine-root" / "masstree"
    resolution = O.resolve_oracle_environment(
        tmp_path / "disposable-checkout",
        compiler=sys.executable,
        dependency_root=missing_dependency,
    )
    assert type(resolution) is O.OracleEnvironmentResolutionFailure
    result = O.check_materialized_sort_swo(
        _materialized(_CLEAN_IMPL), marker_id="silo-writeset-sort",
        proposal_source=_CLEAN_IMPL, environment=resolution,
    )
    assert result.status is O.OracleStatus.UNAVAILABLE
    assert result.infrastructure is not None
    assert result.infrastructure.detail_code == resolution.detail_code
    private = O.private_attempt_record(result)
    durable = O.attempt_record(result)
    full_path = str(missing_dependency)
    assert full_path in json.dumps(private, sort_keys=True)
    assert full_path not in json.dumps(durable, sort_keys=True)
    durable_candidate = durable["infrastructure"][
        "environment_resolution"
    ]["dependency_candidates"][0]
    assert set(durable_candidate) == {
        "origin", "outcome", "path_basename", "path_sha256",
    }
    assert durable_candidate["path_basename"] == "masstree"
    assert len(durable_candidate["path_sha256"]) == 64


def test_explicit_compiler_binding_never_falls_back_to_ambient(
        monkeypatch, tmp_path):
    ambient = tmp_path / "ambient-cxx"
    ambient.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
    ambient.chmod(0o755)
    dependency = tmp_path / "masstree"
    dependency.mkdir()
    (dependency / "config.h").write_text("#pragma once\n", encoding="utf-8")
    monkeypatch.setenv("IZANAGI_SORT_SWO_CXX", str(ambient))
    monkeypatch.setenv("CXX", str(ambient))
    monkeypatch.setattr(O.shutil, "which", lambda name: str(ambient))

    resolution = O.resolve_oracle_environment(
        tmp_path / "checkout",
        compiler=tmp_path / "missing-explicit-cxx",
        dependency_root=dependency,
    )
    assert type(resolution) is O.OracleEnvironmentResolutionFailure
    assert resolution.detail_code == "oracle-environment-compiler-unresolved"
    assert [item.origin for item in resolution.compiler_candidates] == [
        "argument:compiler"
    ]
    assert all(item.outcome != "selected" for item in resolution.compiler_candidates)


def test_scratch_failure_is_unavailable_not_candidate_reject(
        monkeypatch):
    oracle_environment = _get_oracle_environment()
    class BrokenScratch:
        def __init__(self, *args, **kwargs):
            raise OSError("scratch unavailable")

    monkeypatch.setattr(O.tempfile, "TemporaryDirectory", BrokenScratch)
    result = O.check_materialized_sort_swo(
        _materialized(_CLEAN_IMPL), marker_id="silo-writeset-sort",
        proposal_source=_CLEAN_IMPL, environment=oracle_environment,
    )
    assert result.status is O.OracleStatus.UNAVAILABLE
    assert result.finding is None


def test_candidate_compile_failure_is_reject_not_unavailable(
        monkeypatch):
    oracle_environment = _get_oracle_environment()
    compile_finding = O.SortSwoFinding(
        O.OracleRejectKind.COMPILE, "candidate-compile-failed",
    )
    compile_calls = []

    def compile_control_then_candidate(*args, **kwargs):
        if args[1].name == "trusted-postflight.cpp":
            return None, False
        compile_calls.append(1)
        if len(compile_calls) == 1:
            return None, False
        return compile_finding, False

    monkeypatch.setattr(O, "_compile", compile_control_then_candidate)
    monkeypatch.setattr(O, "_evaluate_executable", lambda executable: None)
    monkeypatch.setattr(O, "_compiler_version", lambda compiler: "fixture-cxx 1")
    result = O.check_materialized_sort_swo(
        _materialized(_CLEAN_IMPL), marker_id="silo-writeset-sort",
        proposal_source=_CLEAN_IMPL, environment=oracle_environment,
    )
    assert result.status is O.OracleStatus.REJECT
    assert result.finding is compile_finding
    assert len(compile_calls) == 2


def test_candidate_compile_failure_with_failing_postflight_is_unavailable(
        monkeypatch):
    oracle_environment = _get_oracle_environment()
    candidate_finding = O.SortSwoFinding(
        O.OracleRejectKind.COMPILE, "candidate-compile-failed",
    )
    postflight_finding = O.SortSwoFinding(
        O.OracleRejectKind.COMPILE, "candidate-compile-failed",
    )
    results = iter((
        (None, False),
        (candidate_finding, False),
        (postflight_finding, False),
    ))
    monkeypatch.setattr(O, "_compile", lambda *args, **kwargs: next(results))
    monkeypatch.setattr(O, "_evaluate_executable", lambda executable: None)
    monkeypatch.setattr(O, "_compiler_version", lambda compiler: "fixture-cxx 1")

    result = O.check_materialized_sort_swo(
        _materialized(_CLEAN_IMPL), marker_id="silo-writeset-sort",
        proposal_source=_CLEAN_IMPL, environment=oracle_environment,
    )

    assert result.status is O.OracleStatus.UNAVAILABLE
    assert result.finding is None
    assert result.receipt is not None
    assert result.infrastructure is not None
    assert result.infrastructure.phase == "trusted-postflight-compile"
    assert result.infrastructure.detail_code == (
        "trusted-positive-tu-postflight-compile-failed"
    )


def test_postflight_unavailable_retains_candidate_finding(
        monkeypatch):
    oracle_environment = _get_oracle_environment()
    candidate_diagnostic = O.CompilerDiagnostic(
        "candidate source must stay private", 34, 34, "5" * 64, False,
    )
    candidate_finding = O.SortSwoFinding(
        O.OracleRejectKind.COMPILE, "candidate-compile-failed",
        compiler_diagnostic=candidate_diagnostic,
    )
    postflight_finding = O.SortSwoFinding(
        O.OracleRejectKind.COMPILE, "candidate-compile-failed",
    )
    results = iter((
        (None, False),
        (candidate_finding, False),
        (postflight_finding, False),
    ))
    monkeypatch.setattr(O, "_compile", lambda *args, **kwargs: next(results))
    monkeypatch.setattr(O, "_evaluate_executable", lambda executable: None)
    monkeypatch.setattr(O, "_compiler_version", lambda compiler: "fixture-cxx 1")

    result = O.check_materialized_sort_swo(
        _materialized(_CLEAN_IMPL), marker_id="silo-writeset-sort",
        proposal_source=_CLEAN_IMPL, environment=oracle_environment,
    )
    attempt = O.attempt_record(result)

    assert result.receipt is not None
    assert attempt["oracle_receipt"] == result.receipt.as_dict()
    assert attempt["infrastructure"]["dependency_config_sha256"] == (
        result.receipt.dependency_config_sha256
    )
    assert result.candidate_compile_finding is candidate_finding
    assert attempt["candidate_compile_finding"] == {
        "kind": "compile",
        "reason_code": "candidate-compile-failed",
        "corpus_id": O.CORPUS_ID,
        "compiler_diagnostic": candidate_diagnostic.metadata_dict(),
    }
    assert "candidate source must stay private" not in json.dumps(
        attempt, sort_keys=True,
    )


def test_candidate_compile_reject_postflight_control_success_stays_reject(
        monkeypatch):
    oracle_environment = _get_oracle_environment()
    candidate_finding = O.SortSwoFinding(
        O.OracleRejectKind.COMPILE, "candidate-compile-failed",
    )
    calls = []
    candidate_artifacts = []

    def compile_spy(source, source_path, executable, **kwargs):
        calls.append((source, source_path.name, executable.name))
        if len(calls) == 2:
            artifacts = (
                source_path,
                executable,
                source_path.with_suffix(source_path.suffix + ".stderr"),
            )
            for artifact in artifacts:
                artifact.write_bytes(b"candidate-residue")
            candidate_artifacts.extend(artifacts)
            return candidate_finding, False
        if len(calls) == 3:
            assert source_path.parent != candidate_artifacts[0].parent
            assert all(not artifact.exists() for artifact in candidate_artifacts)
        return None, False

    monkeypatch.setattr(O, "_compile", compile_spy)
    monkeypatch.setattr(O, "_evaluate_executable", lambda executable: None)
    monkeypatch.setattr(O, "_compiler_version", lambda compiler: "fixture-cxx 1")

    result = O.check_materialized_sort_swo(
        _materialized(_CLEAN_IMPL), marker_id="silo-writeset-sort",
        proposal_source=_CLEAN_IMPL, environment=oracle_environment,
    )

    assert result.status is O.OracleStatus.REJECT
    assert result.finding is candidate_finding
    digest = O.rejection_digest(
        result, diff_region="fixture diff", marker_id="silo-writeset-sort",
    )
    assert digest["reason"] == "candidate-compile-failed"
    assert digest["oracle_finding"]["reason_code"] == "candidate-compile-failed"
    assert [call[1:] for call in calls] == [
        ("trusted-control.cpp", "trusted-control"),
        ("oracle.cpp", "oracle"),
        ("trusted-postflight.cpp", "trusted-postflight"),
    ]
    assert calls[0][0] == calls[2][0] == O._translation_unit(
        O._TRUSTED_CONTROL_STATEMENT,
    )


def test_candidate_artifact_cleanup_failure_preserves_receipt(
        monkeypatch):
    oracle_environment = _get_oracle_environment()
    candidate_finding = O.SortSwoFinding(
        O.OracleRejectKind.COMPILE, "candidate-compile-failed",
    )
    results = iter((
        (None, False),
        (candidate_finding, False),
        (None, False),
    ))
    compile_calls = 0
    real_unlink = Path.unlink

    def fail_candidate_cleanup(path, *args, **kwargs):
        if path.name == "oracle.cpp":
            raise OSError("candidate cleanup unavailable")
        return real_unlink(path, *args, **kwargs)

    def compile_with_successful_postflight(*args, **kwargs):
        nonlocal compile_calls
        compile_calls += 1
        return next(results)

    monkeypatch.setattr(Path, "unlink", fail_candidate_cleanup)
    monkeypatch.setattr(O, "_compile", compile_with_successful_postflight)
    monkeypatch.setattr(O, "_evaluate_executable", lambda executable: None)
    monkeypatch.setattr(O, "_compiler_version", lambda compiler: "fixture-cxx 1")

    result = O.check_materialized_sort_swo(
        _materialized(_CLEAN_IMPL), marker_id="silo-writeset-sort",
        proposal_source=_CLEAN_IMPL, environment=oracle_environment,
    )

    assert result.status is O.OracleStatus.REJECT
    assert result.receipt is not None
    assert result.finding is candidate_finding
    assert result.infrastructure is None
    assert compile_calls == 3


def test_candidate_artifact_cleanup_and_postflight_failure_preserve_evidence(
        monkeypatch):
    oracle_environment = _get_oracle_environment()
    candidate_finding = O.SortSwoFinding(
        O.OracleRejectKind.COMPILE, "candidate-compile-failed",
    )
    postflight_finding = O.SortSwoFinding(
        O.OracleRejectKind.COMPILE, "candidate-compile-failed",
    )
    results = iter((
        (None, False),
        (candidate_finding, False),
        (postflight_finding, False),
    ))
    real_unlink = Path.unlink

    def fail_candidate_cleanup(path, *args, **kwargs):
        if path.name == "oracle.cpp":
            raise OSError("candidate cleanup unavailable")
        return real_unlink(path, *args, **kwargs)

    monkeypatch.setattr(Path, "unlink", fail_candidate_cleanup)
    monkeypatch.setattr(O, "_compile", lambda *args, **kwargs: next(results))
    monkeypatch.setattr(O, "_evaluate_executable", lambda executable: None)
    monkeypatch.setattr(O, "_compiler_version", lambda compiler: "fixture-cxx 1")

    result = O.check_materialized_sort_swo(
        _materialized(_CLEAN_IMPL), marker_id="silo-writeset-sort",
        proposal_source=_CLEAN_IMPL, environment=oracle_environment,
    )
    attempt = O.attempt_record(result)

    assert result.status is O.OracleStatus.UNAVAILABLE
    assert result.receipt is not None
    assert result.infrastructure is not None
    assert result.infrastructure.phase == "trusted-postflight-compile"
    assert result.infrastructure.detail_code == (
        "trusted-positive-tu-postflight-compile-failed-"
        "after-candidate-cleanup-failed"
    )
    assert result.candidate_compile_finding is candidate_finding
    assert attempt["infrastructure"]["detail_code"] == (
        "trusted-positive-tu-postflight-compile-failed-"
        "after-candidate-cleanup-failed"
    )


def test_candidate_compile_infrastructure_failure_with_successful_postflight_stays_unavailable(
        monkeypatch):
    oracle_environment = _get_oracle_environment()
    candidate_finding = O.SortSwoFinding(
        O.OracleRejectKind.COMPILE, "compiler-launch-unavailable",
    )
    results = iter((
        (None, False),
        (candidate_finding, True),
        (None, False),
    ))
    monkeypatch.setattr(O, "_compile", lambda *args, **kwargs: next(results))
    monkeypatch.setattr(O, "_evaluate_executable", lambda executable: None)
    monkeypatch.setattr(O, "_compiler_version", lambda compiler: "fixture-cxx 1")

    result = O.check_materialized_sort_swo(
        _materialized(_CLEAN_IMPL), marker_id="silo-writeset-sort",
        proposal_source=_CLEAN_IMPL, environment=oracle_environment,
    )

    assert result.status is O.OracleStatus.UNAVAILABLE
    assert result.infrastructure is not None
    assert result.infrastructure.phase == "candidate-compile"
    assert result.infrastructure.detail_code == "compiler-launch-unavailable"
    assert result.candidate_compile_finding is None


def test_candidate_compile_infrastructure_and_postflight_failure_uses_postflight_detail(
        monkeypatch):
    oracle_environment = _get_oracle_environment()
    candidate_finding = O.SortSwoFinding(
        O.OracleRejectKind.COMPILE, "compiler-launch-unavailable",
    )
    postflight_finding = O.SortSwoFinding(
        O.OracleRejectKind.COMPILE, "candidate-compile-failed",
    )
    results = iter((
        (None, False),
        (candidate_finding, True),
        (postflight_finding, False),
    ))
    monkeypatch.setattr(O, "_compile", lambda *args, **kwargs: next(results))
    monkeypatch.setattr(O, "_evaluate_executable", lambda executable: None)
    monkeypatch.setattr(O, "_compiler_version", lambda compiler: "fixture-cxx 1")

    result = O.check_materialized_sort_swo(
        _materialized(_CLEAN_IMPL), marker_id="silo-writeset-sort",
        proposal_source=_CLEAN_IMPL, environment=oracle_environment,
    )

    assert result.status is O.OracleStatus.UNAVAILABLE
    assert result.infrastructure is not None
    assert result.infrastructure.phase == "trusted-postflight-compile"
    assert result.infrastructure.detail_code == (
        "trusted-positive-tu-postflight-compile-failed"
    )
    assert result.candidate_compile_finding is candidate_finding


def test_postflight_source_write_oserror_preserves_receipt(
        monkeypatch):
    oracle_environment = _get_oracle_environment()
    candidate_finding = O.SortSwoFinding(
        O.OracleRejectKind.COMPILE, "candidate-compile-failed",
    )
    compile_calls = 0
    real_write_text = Path.write_text

    def fail_postflight_write(path, *args, **kwargs):
        if path.name == "trusted-postflight.cpp":
            raise OSError("postflight source unavailable")
        return real_write_text(path, *args, **kwargs)

    def compile_with_real_postflight_write(source, source_path, *args, **kwargs):
        nonlocal compile_calls
        compile_calls += 1
        if compile_calls == 2:
            return candidate_finding, False
        if compile_calls == 3:
            source_path.write_text(source, encoding="utf-8")
            raise AssertionError("postflight write unexpectedly succeeded")
        return None, False

    monkeypatch.setattr(Path, "write_text", fail_postflight_write)
    monkeypatch.setattr(O, "_compile", compile_with_real_postflight_write)
    monkeypatch.setattr(O, "_evaluate_executable", lambda executable: None)
    monkeypatch.setattr(O, "_compiler_version", lambda compiler: "fixture-cxx 1")

    result = O.check_materialized_sort_swo(
        _materialized(_CLEAN_IMPL), marker_id="silo-writeset-sort",
        proposal_source=_CLEAN_IMPL, environment=oracle_environment,
    )

    assert result.status is O.OracleStatus.UNAVAILABLE
    assert result.receipt is not None
    assert result.infrastructure is not None
    assert result.infrastructure.phase == "trusted-postflight-compile"
    assert result.candidate_compile_finding is candidate_finding


def test_postflight_cleanup_oserror_preserves_receipt(
        monkeypatch):
    oracle_environment = _get_oracle_environment()
    candidate_finding = O.SortSwoFinding(
        O.OracleRejectKind.COMPILE, "candidate-compile-failed",
    )
    compile_calls = 0
    real_unlink = Path.unlink

    def fail_postflight_cleanup(path, *args, **kwargs):
        if path.name == "trusted-postflight.cpp":
            raise OSError("postflight cleanup unavailable")
        return real_unlink(path, *args, **kwargs)

    def compile_with_successful_postflight(*args, **kwargs):
        nonlocal compile_calls
        compile_calls += 1
        if compile_calls == 2:
            return candidate_finding, False
        return None, False

    monkeypatch.setattr(Path, "unlink", fail_postflight_cleanup)
    monkeypatch.setattr(O, "_compile", compile_with_successful_postflight)
    monkeypatch.setattr(O, "_evaluate_executable", lambda executable: None)
    monkeypatch.setattr(O, "_compiler_version", lambda compiler: "fixture-cxx 1")

    result = O.check_materialized_sort_swo(
        _materialized(_CLEAN_IMPL), marker_id="silo-writeset-sort",
        proposal_source=_CLEAN_IMPL, environment=oracle_environment,
    )

    assert result.status is O.OracleStatus.UNAVAILABLE
    assert result.receipt is not None
    assert result.infrastructure is not None
    assert result.infrastructure.phase == "trusted-postflight-compile"
    assert result.candidate_compile_finding is candidate_finding


def test_postflight_programmer_error_is_not_infrastructure(
        monkeypatch):
    oracle_environment = _get_oracle_environment()
    candidate_finding = O.SortSwoFinding(
        O.OracleRejectKind.COMPILE, "candidate-compile-failed",
    )
    compile_calls = 0

    def compile_with_programmer_error(*args, **kwargs):
        nonlocal compile_calls
        compile_calls += 1
        if compile_calls == 2:
            return candidate_finding, False
        if compile_calls == 3:
            raise AssertionError("programmer error")
        return None, False

    monkeypatch.setattr(O, "_compile", compile_with_programmer_error)
    monkeypatch.setattr(O, "_evaluate_executable", lambda executable: None)
    monkeypatch.setattr(O, "_compiler_version", lambda compiler: "fixture-cxx 1")

    with pytest.raises(AssertionError, match="programmer error"):
        O.check_materialized_sort_swo(
            _materialized(_CLEAN_IMPL), marker_id="silo-writeset-sort",
            proposal_source=_CLEAN_IMPL, environment=oracle_environment,
        )


def test_trusted_positive_preflight_compile_failure_is_unavailable(
        monkeypatch):
    oracle_environment = _get_oracle_environment()
    diagnostic = O.CompilerDiagnostic(
        "trusted diagnostic", 18, 18, O._sha256("trusted diagnostic"), False,
    )
    preflight_finding = O.SortSwoFinding(
        O.OracleRejectKind.COMPILE, "candidate-compile-failed",
        compiler_diagnostic=diagnostic,
    )
    monkeypatch.setattr(
        O, "_compile", lambda *args, **kwargs: (preflight_finding, False),
    )
    monkeypatch.setattr(O, "_compiler_version", lambda compiler: "fixture-cxx 1")
    result = O.check_materialized_sort_swo(
        _materialized(_CLEAN_IMPL), marker_id="silo-writeset-sort",
        proposal_source=_CLEAN_IMPL, environment=oracle_environment,
    )
    assert result.status is O.OracleStatus.UNAVAILABLE
    assert result.finding is None
    assert result.infrastructure is not None
    assert result.infrastructure.phase == "trusted-preflight-compile"
    assert result.infrastructure.detail_code == "trusted-positive-tu-compile-failed"
    assert result.infrastructure.compiler_diagnostic is diagnostic


def test_public_api_propagates_exact_evaluator_axiom_finding(
        monkeypatch):
    oracle_environment = _get_oracle_environment()
    expected = O.SortSwoFinding(
        O.OracleRejectKind.AXIOM,
        "swo-asymmetric",
        O.SwoCounterexample(O.SwoAxiom.ASYMMETRIC, ((3, 4), (4, 3))),
        corpus_id=f"{O.CORPUS_ID}/corpus-1",
        order_id=2,
    )
    evaluations = []
    monkeypatch.setattr(O, "_compile", lambda *args, **kwargs: (None, False))

    def evaluate(executable):
        evaluations.append(executable.name)
        return None if len(evaluations) == 1 else expected

    monkeypatch.setattr(O, "_evaluate_executable", evaluate)
    monkeypatch.setattr(O, "_compiler_version", lambda compiler: "fixture-cxx 1")
    result = O.check_materialized_sort_swo(
        _materialized(_CLEAN_IMPL), marker_id="silo-writeset-sort",
        proposal_source=_CLEAN_IMPL, environment=oracle_environment,
    )
    assert result.status is O.OracleStatus.REJECT
    assert result.finding is expected
    assert result.finding.as_dict() == expected.as_dict()
    assert evaluations == ["trusted-control", "oracle"]


def test_result_contract_rejects_fail_open_combinations():
    with pytest.raises(ValueError):
        O.SortSwoOracleResult(O.OracleStatus.REJECT, "a", "b", None)
    finding = O.SortSwoFinding(O.OracleRejectKind.COMPILE, "candidate-compile-failed")
    with pytest.raises(ValueError):
        O.SortSwoOracleResult(O.OracleStatus.PASS, "a", "b", finding)
    with pytest.raises(ValueError):
        O.SortSwoOracleResult(O.OracleStatus.UNAVAILABLE, "a", "b", finding)


def test_fixed_corpus_contract_has_required_values_topology_and_triplicate():
    storage_values = {item[0] for corpus in O._CORPUS_MANIFEST for item in corpus}
    key_values = {item[1] for corpus in O._CORPUS_MANIFEST for item in corpus}
    assert storage_values == {
        0, 1, 2, 0x7FFFFFFF, 0x80000000, 0xFFFFFFFE, 0xFFFFFFFF,
    }
    assert key_values == {b"", b"a", b"aa", b"b", b"\0", b"a\0", b"\x7f", b"\x80"}
    assert all(corpus[:3] == ((0, b"", 1, 0),) * 3
               for corpus in O._CORPUS_MANIFEST)
    assert all({item[2] for item in corpus} == {0, 1, 2}
               for corpus in O._CORPUS_MANIFEST)
    assert O._N >= 17 and O._CORPORA == (0, 1) and O._ORDERS == (0, 1, 2)


def test_public_oracle_domain_aliases_track_contract_inputs():
    assert (O.N, O.CORPORA, O.ORDERS) == (O._N, O._CORPORA, O._ORDERS)


def test_contract_digest_binds_axiom_checker_source_component():
    assert O._ORACLE_CONTRACT_COMPONENTS_SCHEMA == (
        "sort-swo-contract-components-v1"
    )
    assert O._ORACLE_CONTRACT_COMPONENTS == {
        "axiom_checker_implementation_sha256": (
            O.AXIOM_CHECKER_IMPLEMENTATION_SHA256
        ),
        "compile_flags_sha256": O.COMPILE_FLAGS_SHA256,
        "corpus_sha256": O.CORPUS_SHA256,
        "tu_template_sha256": O.TU_TEMPLATE_SHA256,
    }
    assert O.ORACLE_COMPONENTS_SHA256 == O._contract_components_sha256(
        O._ORACLE_CONTRACT_COMPONENTS,
    )
    changed = dict(O._ORACLE_CONTRACT_COMPONENTS)
    changed["axiom_checker_implementation_sha256"] = "0" * 64
    assert O._contract_components_sha256(changed) != O.ORACLE_COMPONENTS_SHA256
    assert f"-x{O.ORACLE_COMPONENTS_SHA256}-" in O.ORACLE_CONTRACT_ID


def test_contract_digest_binds_corpus_and_order_selection():
    current = O._source_bundle_sha256(
        O._AXIOM_CHECKER_SOURCE_FUNCTIONS,
        n=O._N, orders=O._ORDERS, corpora=O._CORPORA,
    )
    narrowed_corpora = O._source_bundle_sha256(
        O._AXIOM_CHECKER_SOURCE_FUNCTIONS,
        n=O._N, orders=O._ORDERS, corpora=(0,),
    )
    narrowed_orders = O._source_bundle_sha256(
        O._AXIOM_CHECKER_SOURCE_FUNCTIONS,
        n=O._N, orders=(0, 1), corpora=O._CORPORA,
    )
    changed_n = O._source_bundle_sha256(
        O._AXIOM_CHECKER_SOURCE_FUNCTIONS,
        n=O._N - 1, orders=O._ORDERS, corpora=O._CORPORA,
    )
    assert current == O.AXIOM_CHECKER_IMPLEMENTATION_SHA256
    assert len({current, narrowed_corpora, narrowed_orders, changed_n}) == 4


def test_axiom_checker_source_bundle_is_enumerated_and_ordered():
    assert O._AXIOM_CHECKER_SOURCE_FUNCTIONS == (
        O.check_relation_matrix,
        O._evaluate_executable,
        O._run_matrix,
        O._compile_command,
    )


def test_axiom_checker_source_digest_fails_closed_when_source_unavailable(
        monkeypatch):
    monkeypatch.setattr(
        O.inspect, "getsource",
        lambda _function: (_ for _ in ()).throw(OSError("source unavailable")),
    )
    with pytest.raises(OSError, match="source unavailable"):
        O._source_bundle_sha256(
            O._AXIOM_CHECKER_SOURCE_FUNCTIONS,
            n=O._N, orders=O._ORDERS, corpora=O._CORPORA,
        )


def test_axiom_checker_source_digest_changes_with_source_text(monkeypatch):
    target = O.check_relation_matrix
    real_getsource = inspect.getsource

    def digest_with_target_source(source):
        monkeypatch.setattr(
            O.inspect,
            "getsource",
            lambda function: (
                source if function is target else real_getsource(function)
            ),
        )
        return O._source_bundle_sha256(
            O._AXIOM_CHECKER_SOURCE_FUNCTIONS,
            n=O._N, orders=O._ORDERS, corpora=O._CORPORA,
        )

    source_a = "def check_relation_matrix(matrix, n):\n    return None\n"
    source_b = "def check_relation_matrix(matrix, n):\n    return True\n"
    assert len(source_a.encode("utf-8")) == len(source_b.encode("utf-8"))
    assert digest_with_target_source(source_a) != digest_with_target_source(source_b)


def test_contract_manifest_hashes_and_literal_are_exact_snapshot():
    assert O.CORPUS_SHA256 == "436a66d9d5d583e52f5d76c60b4add78c4e252dec471ff8b9620dbf8149bf253"
    assert O.TU_TEMPLATE_SHA256 == "d1a5e422e226240f286f302a4addde79740547682b538d2b46ebfd9dfdd32bca"
    assert O.COMPILE_FLAGS_SHA256 == "7ad0ac2625612307826a109b20f11af4beb8cbf124ad8a2e291f85ec63cbde1e"
    assert O.ORACLE_CONTRACT_ID == (
        "sort-swo-v3-corpus1-protocol2-checker2-grammar1-"
        "x67c3a5d76f3b1604c57d33ab7d0af15f4aaafa896b4810d7c3c95d812d48faa0-"
        "c436a66d9d5d5-tud1a5e422e226-f7ad0ac262561-a215b718a5bfe"
    )
    assert (O.CONTRACT_VERSION, O.CORPUS_VERSION, O.PROTOCOL_VERSION,
            O.AXIOM_CHECKER_VERSION, O.GRAMMAR_VERSION) == (3, 1, 2, 2, 1)


def test_legacy_v2_contract_cannot_construct_current_oracle_result():
    legacy_v2_golden = (
        "sort-swo-v2-corpus1-protocol2-checker2-grammar1-"
        "c436a66d9d5d583e52f5d76c60b4add78c4e252dec471ff8b9620dbf8149bf253-"
        "tud88f98bc19911ae7ddd3049731614c0c661a2fe7c0c36c07aebd74281a07d956-"
        "f7ad0ac2625612307826a109b20f11af4beb8cbf124ad8a2e291f85ec63cbde1e"
    )
    with pytest.raises(ValueError, match="contract_id"):
        O.SortSwoOracleResult(
            O.OracleStatus.UNAVAILABLE,
            "a" * 64,
            "b" * 64,
            contract_id=legacy_v2_golden,
            infrastructure=O.OracleInfrastructureFailure(
                O.INFRASTRUCTURE_REASON_CODE,
                "trusted-preflight-compile",
                "fixture-unavailable",
            ),
        )


def test_translation_unit_uses_real_type_real_ctor_and_candidate_statement_verbatim():
    source = O._translation_unit(_CLEAN_IMPL)
    assert '#include "cc/silo/include/silo_op_element.hh"' in source
    includes = [
        '#include "include/masstree_wrapper.hh"',
        '#include "include/tuple_body.hh"',
        '#include "cc/silo/include/tuple.hh"',
        '#include "cc/silo/include/silo_op_element.hh"',
    ]
    assert [source.index(item) for item in includes] == sorted(
        source.index(item) for item in includes
    )
    assert "std::vector<WriteElement<Tuple>> elements;" in source
    assert "OracleWriteSet write_set_;" in source
    assert "write_set_.emplace_back(static_cast<Storage>(spec.storage)" in source
    assert "pointer, OpType::UPDATE" in source
    assert "struct WriteElement" not in source
    assert "const WriteElement<Tuple>& lhs_element" in source
    assert "snapshot_corpus()" in source
    assert _CLEAN_IMPL in source
    for axiom_name in ("irreflexive", "asymmetric", "transitive-equivalence"):
        assert axiom_name not in source


def test_evaluator_uses_six_separate_process_observations(monkeypatch, tmp_path):
    calls = []

    def stable(_executable, corpus, order, *, test_mode=None):
        calls.append((corpus, order, test_mode))
        return bytes(O._N * O._N), None

    monkeypatch.setattr(O, "_run_matrix", stable)
    assert O._evaluate_executable(tmp_path / "unused") is None
    assert calls == [
        (corpus, order, None) for corpus in O._CORPORA for order in O._ORDERS
    ]


def test_relation_change_across_process_orders_is_nondeterministic(monkeypatch, tmp_path):
    def varying(_executable, corpus, order, *, test_mode=None):
        matrix = bytearray(O._N * O._N)
        if order == 2:
            matrix[1] = 1
        return bytes(matrix), None

    monkeypatch.setattr(O, "_run_matrix", varying)
    finding = O._evaluate_executable(tmp_path / "unused")
    assert finding is not None
    assert finding.kind is O.OracleRejectKind.NONDETERMINISTIC
    assert finding.reason_code == "relation-varies-across-process-order"
    assert finding.input_pairs == ((0, 1),)
    assert finding.corpus_id == f"{O.CORPUS_ID}/corpus-0"
    assert [item["order_id"] for item in finding.observations] == [0, 1, 2]
    assert [item["value"] for item in finding.observations] == [False, False, True]


def test_run_limits_cover_required_resources(monkeypatch):
    calls = []
    monkeypatch.setattr(O.resource, "setrlimit", lambda name, value: calls.append((name, value)))
    O._limit_run()
    assert {name for name, _ in calls} == {
        O.resource.RLIMIT_CPU, O.resource.RLIMIT_AS, O.resource.RLIMIT_FSIZE,
        O.resource.RLIMIT_NPROC, O.resource.RLIMIT_NOFILE, O.resource.RLIMIT_CORE,
    }


def test_hard_timeout_kills_process_group(monkeypatch):
    class TimedOut:
        pid = 316
        returncode = -9
        calls = 0

        def communicate(self, timeout=None):
            self.calls += 1
            if self.calls == 1:
                raise O.subprocess.TimeoutExpired("oracle", timeout)
            return b"", b""

    killed = []
    monkeypatch.setattr(O.os, "killpg", lambda pid, sig: killed.append((pid, sig)))
    timed_out, returncode = O._communicate_hard_timeout(TimedOut(), 0.01)
    assert timed_out is True and returncode == -9
    assert killed == [(316, O.signal.SIGKILL)]


def test_candidate_stdout_stderr_are_discarded_and_matrix_uses_dedicated_fd(monkeypatch, tmp_path):
    captured = {}

    class FailedProcess:
        pid = 317
        returncode = 71

        def communicate(self, timeout=None):
            return b"", b""

    def fake_popen(command, **kwargs):
        captured["command"] = command
        captured["kwargs"] = kwargs
        return FailedProcess()

    monkeypatch.setattr(O.subprocess, "Popen", fake_popen)
    _matrix_value, finding = O._run_matrix(tmp_path / "oracle", 0, 0)
    assert finding is not None and finding.kind is O.OracleRejectKind.EXECUTION
    assert captured["kwargs"]["stdout"] == O.subprocess.DEVNULL
    assert captured["kwargs"]["stderr"] == O.subprocess.DEVNULL
    assert len(captured["kwargs"]["pass_fds"]) == 1
    assert captured["command"][3] == str(captured["kwargs"]["pass_fds"][0])


def test_unattributed_runtime_exit_is_infrastructure_unavailable(monkeypatch, tmp_path):
    class FailedProcess:
        pid = 319
        returncode = 1

        def communicate(self, timeout=None):
            return b"", b""

    monkeypatch.setattr(O.subprocess, "Popen", lambda *args, **kwargs: FailedProcess())
    with pytest.raises(O._EvaluationUnavailable) as caught:
        O._run_matrix(tmp_path / "oracle", 0, 0)
    assert caught.value.phase == "run-exit"
    assert caught.value.detail_code == "unattributed-run-exit-1"


def test_compile_command_reproduces_probe_c2_contract(monkeypatch, tmp_path):
    captured = {}

    class SuccessfulProcess:
        pid = 318
        returncode = 0

        def communicate(self, timeout=None):
            return b"", b""

    def fake_popen(command, **kwargs):
        captured["command"] = command
        Path(command[4]).touch()
        return SuccessfulProcess()

    monkeypatch.setattr(O.subprocess, "Popen", fake_popen)
    executable = tmp_path / "oracle"
    finding, unavailable = O._compile(
        "int main(){}", tmp_path / "oracle.cpp", executable,
        compiler="/usr/bin/g++", ccbench_dir=_CCBENCH,
        masstree_dir=Path("/fixture/masstree"),
    )
    assert finding is None and unavailable is False
    command = captured["command"]
    for flag in (
        "-DGLOBAL=extern", "-DCACHE_LINE_SIZE=64", "-DVAL_SIZE=4", "-DKEY_SIZE=8",
        "-DMASSTREE_USE=0", "-DCLOCKS_PER_US=2100", "-DBACK_OFF=1", "-DWAL=0",
        "-DNO_WAIT_LOCKING_IN_VALIDATION=1", "-DTRACE=0", "-DSORT_VARIANT=0",
        "-DKEY_SORT=0", "-DPARTITION_TABLE=0",
    ):
        assert flag in command
    assert str(_CCBENCH) in command
    assert str(_CCBENCH / "include") in command
    assert "/fixture/masstree" in command


def test_compile_diagnostic_is_bounded_hashed_and_not_serialized_to_critic(
        monkeypatch, tmp_path):
    payload = b"candidate.cpp:1: error: " + b"x" * (O._MAX_DIAGNOSTIC_BYTES + 100)

    class FailedProcess:
        pid = 320
        returncode = 1

        def communicate(self, timeout=None):
            return b"", b""

    def fake_popen(command, **kwargs):
        kwargs["stderr"].write(payload)
        kwargs["stderr"].flush()
        return FailedProcess()

    monkeypatch.setattr(O.subprocess, "Popen", fake_popen)
    finding, unavailable = O._compile(
        "invalid", tmp_path / "candidate.cpp", tmp_path / "candidate",
        compiler="/fixture/cxx", ccbench_dir=Path("/fixture/ccbench"),
        masstree_dir=Path("/fixture/masstree"),
    )
    assert unavailable is False and finding is not None
    diagnostic = finding.compiler_diagnostic
    assert diagnostic is not None
    assert diagnostic.captured_bytes == O._MAX_DIAGNOSTIC_BYTES
    assert diagnostic.total_bytes == len(payload)
    assert diagnostic.truncated is True
    assert diagnostic.sha256 == __import__("hashlib").sha256(payload).hexdigest()
    serialized = finding.as_dict()["compiler_diagnostic"]
    assert "text" not in serialized
    assert "candidate.cpp" not in json.dumps(serialized, sort_keys=True)


def test_no_optional_or_none_pass_api_and_no_unbounded_fixture_enumeration():
    signature = inspect.signature(O.check_materialized_sort_swo)
    assert signature.return_annotation == "SortSwoOracleResult"
    source = inspect.getsource(O._evaluate_executable)
    assert "_CORPORA" in source and "_ORDERS" in source
    assert "glob(" not in source and "rglob(" not in source
    environment_parameter = signature.parameters["environment"]
    assert environment_parameter.default is inspect.Parameter.empty
    resolver_source = inspect.getsource(O.resolve_oracle_environment)
    assert "/work/" not in resolver_source
    assert "IZANAGI_SORT_SWO_CXX" in resolver_source
    assert "IZANAGI_SORT_SWO_MASSTREE_ROOT" in resolver_source
    assert "ccbench-build-dependency" not in resolver_source
    assert "ancestor-cache:" not in resolver_source


def test_s1_sort_best_runs_same_oracle_before_source_materializer(monkeypatch, tmp_path):
    import types
    from orchestrator.campaign import patchharness
    from orchestrator.campaign import p3_s4_loop as loop_axis
    from orchestrator.campaign import s1_direct_comparison as direct

    order = []
    materialized = _materialized(_CLEAN_IMPL)

    @contextlib.contextmanager
    def checkout(*args, **kwargs):
        yield str(tmp_path)

    monkeypatch.setattr(patchharness, "checkout", checkout)
    monkeypatch.setattr(patchharness, "applied", checkout)
    monkeypatch.setattr(
        loop_axis, "quarantine",
        lambda *args, **kwargs: (
            types.SimpleNamespace(passed=True), "base", materialized, "diff",
        ),
    )

    def oracle_check(source, **kwargs):
        kwargs["phase_marker"]()
        order.append("oracle")
        assert source == materialized
        assert kwargs["proposal_source"] == _CLEAN_IMPL
        return O.SortSwoOracleResult(
            O.OracleStatus.PASS, "7" * 64, "8" * 64,
            receipt=_receipt("7" * 64, "8" * 64),
        )

    def resolve(*args, **kwargs):
        order.append("resolve")
        return "fixture-source"

    dependency = tmp_path / "verified-masstree"
    verified_compiler = tmp_path / "verified-cxx"

    def resolve_environment(ccbench, **kwargs):
        order.append("environment")
        assert Path(ccbench) == tmp_path
        assert kwargs == {
            "compiler": verified_compiler,
            "dependency_root": dependency,
        }
        return "fixture-environment"

    monkeypatch.setattr(O, "check_materialized_sort_swo", oracle_check)
    monkeypatch.setattr(O, "resolve_oracle_environment", resolve_environment)
    monkeypatch.setattr(direct.source_digest, "resolve", resolve)
    cell = {
        "configuration": "sort_best",
        "variant": {
            "comparator": _CLEAN_IMPL,
            "flags": {
                "BACK_OFF": 1,
                "NO_WAIT_LOCKING_IN_VALIDATION": 1,
                "NO_WAIT_OF_TICTOC": 0,
                "SORT_VARIANT": 1,
                "WAL": 0,
            },
        },
    }

    with direct.prepare_cell(
            cell,
            "fixture-pin",
            cxx="fixture-cxx",
            oracle_dependency_root=dependency,
            oracle_compiler=verified_compiler,
            oracle_phase_marker=lambda: order.append("marker"),
    ) as prepared:
        assert prepared.src_token == "fixture-source"
        assert prepared.oracle_attempt is not None
        assert prepared.oracle_attempt["classification"] == "pass"
        assert prepared.oracle_attempt["oracle_receipt"]["contract_id"] == O.ORACLE_CONTRACT_ID
    assert order == ["environment", "marker", "oracle", "resolve"]


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-v"]))
