# -*- coding: utf-8 -*-
"""Independent sort SWO oracle: matrix laws, real C++ E2E, and constraints."""
from __future__ import annotations

import contextlib
import inspect
import json
from pathlib import Path

import pytest

from orchestrator.campaign import sort_swo_oracle as O


_ROOT = Path(__file__).resolve().parents[2]
_CCBENCH = _ROOT / "external" / "ccbench"
_ENVIRONMENT = O.resolve_oracle_environment(_CCBENCH)
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


@pytest.fixture(scope="module")
def compiled_oracle_artifacts(tmp_path_factory):
    """Exactly two real compiles: one positive TU and one multiplexed negative TU."""
    assert _ENVIRONMENT is not None, "real oracle E2E requires an injected oracle environment"
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
            compiler=str(_ENVIRONMENT.compiler), ccbench_dir=_ENVIRONMENT.ccbench_dir,
            masstree_dir=_ENVIRONMENT.dependency_root,
        )
        compile_count += 1
        assert unavailable is False
        assert finding is None
        artifacts[name] = executable
    artifacts["compile_count"] = compile_count
    return artifacts


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


def test_cpp_e2e_clean_generic_lambda_positive(compiled_oracle_artifacts):
    """P1: the existing const-auto-ref, omitted-return-type fixture passes."""
    assert O._evaluate_executable(compiled_oracle_artifacts["positive"]) is None


def test_cpp_e2e_stable_cross_allocation_pointer_positive(compiled_oracle_artifacts):
    """P2: std::less compares pointers from separate allocations stably and passes."""
    assert O._evaluate_executable(
        compiled_oracle_artifacts["negative"], test_mode=0,
    ) is None


def test_real_ctor_pointer_topology_and_triplicate_have_expected_matrix_meaning(
        compiled_oracle_artifacts):
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
        compiled_oracle_artifacts, mode, axiom, pairs):
    finding = O._evaluate_executable(
        compiled_oracle_artifacts["negative"], test_mode=mode,
    )
    assert finding is not None
    assert finding.kind is O.OracleRejectKind.AXIOM
    assert finding.counterexample is not None
    assert finding.counterexample.axiom is axiom
    assert finding.counterexample.input_pairs == pairs


def test_cpp_e2e_high_storage_only_negative_kills_corpus_narrowing(
        compiled_oracle_artifacts):
    finding = O._evaluate_executable(
        compiled_oracle_artifacts["negative"], test_mode=5,
    )
    assert finding is not None
    assert finding.kind is O.OracleRejectKind.AXIOM
    assert finding.counterexample is not None
    assert finding.counterexample.axiom is O.SwoAxiom.ASYMMETRIC
    assert finding.counterexample.input_pairs == ((6, 7), (7, 6))


def test_cpp_e2e_rejects_corpus_mutation_with_dedicated_reason(
        compiled_oracle_artifacts):
    finding = O._evaluate_executable(
        compiled_oracle_artifacts["negative"], test_mode=6,
    )
    assert finding is not None
    assert finding.kind is O.OracleRejectKind.MUTATION
    assert finding.reason_code == "corpus-mutated-by-comparator"
    assert finding.input_pairs == ((0, 0),)


def test_cpp_e2e_rejects_same_process_call_count_dependence_with_witness(
        compiled_oracle_artifacts):
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


def test_real_compile_budget_is_fixed_positive_and_negative_only(compiled_oracle_artifacts):
    assert compiled_oracle_artifacts["compile_count"] == 2


def test_materialized_marker_bytes_are_exact_and_proposal_hash_is_distinct(monkeypatch):
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
        environment=_ENVIRONMENT,
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


def test_scratch_failure_is_unavailable_not_candidate_reject(monkeypatch):
    class BrokenScratch:
        def __init__(self, *args, **kwargs):
            raise OSError("scratch unavailable")

    monkeypatch.setattr(O.tempfile, "TemporaryDirectory", BrokenScratch)
    result = O.check_materialized_sort_swo(
        _materialized(_CLEAN_IMPL), marker_id="silo-writeset-sort",
        proposal_source=_CLEAN_IMPL, environment=_ENVIRONMENT,
    )
    assert result.status is O.OracleStatus.UNAVAILABLE
    assert result.finding is None


def test_candidate_compile_failure_is_reject_not_unavailable(monkeypatch):
    compile_finding = O.SortSwoFinding(
        O.OracleRejectKind.COMPILE, "candidate-compile-failed",
    )
    compile_calls = []

    def compile_control_then_candidate(*args, **kwargs):
        compile_calls.append(1)
        return ((None, False) if len(compile_calls) == 1
                else (compile_finding, False))

    monkeypatch.setattr(O, "_compile", compile_control_then_candidate)
    monkeypatch.setattr(O, "_evaluate_executable", lambda executable: None)
    monkeypatch.setattr(O, "_compiler_version", lambda compiler: "fixture-cxx 1")
    result = O.check_materialized_sort_swo(
        _materialized(_CLEAN_IMPL), marker_id="silo-writeset-sort",
        proposal_source=_CLEAN_IMPL, environment=_ENVIRONMENT,
    )
    assert result.status is O.OracleStatus.REJECT
    assert result.finding is compile_finding
    assert len(compile_calls) == 2


def test_trusted_positive_preflight_compile_failure_is_unavailable(monkeypatch):
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
        proposal_source=_CLEAN_IMPL, environment=_ENVIRONMENT,
    )
    assert result.status is O.OracleStatus.UNAVAILABLE
    assert result.finding is None
    assert result.infrastructure is not None
    assert result.infrastructure.phase == "trusted-preflight-compile"
    assert result.infrastructure.detail_code == "trusted-positive-tu-compile-failed"
    assert result.infrastructure.compiler_diagnostic is diagnostic


def test_public_api_propagates_exact_evaluator_axiom_finding(monkeypatch):
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
        proposal_source=_CLEAN_IMPL, environment=_ENVIRONMENT,
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


def test_contract_manifest_hashes_and_literal_are_exact_snapshot():
    assert O.CORPUS_SHA256 == "436a66d9d5d583e52f5d76c60b4add78c4e252dec471ff8b9620dbf8149bf253"
    assert O.TU_TEMPLATE_SHA256 == "d88f98bc19911ae7ddd3049731614c0c661a2fe7c0c36c07aebd74281a07d956"
    assert O.COMPILE_FLAGS_SHA256 == "7ad0ac2625612307826a109b20f11af4beb8cbf124ad8a2e291f85ec63cbde1e"
    assert O.ORACLE_CONTRACT_ID == (
        "sort-swo-v2-corpus1-protocol2-checker2-grammar1-"
        "c436a66d9d5d583e52f5d76c60b4add78c4e252dec471ff8b9620dbf8149bf253-"
        "tud88f98bc19911ae7ddd3049731614c0c661a2fe7c0c36c07aebd74281a07d956-"
        "f7ad0ac2625612307826a109b20f11af4beb8cbf124ad8a2e291f85ec63cbde1e"
    )
    assert (O.CONTRACT_VERSION, O.CORPUS_VERSION, O.PROTOCOL_VERSION,
            O.AXIOM_CHECKER_VERSION, O.GRAMMAR_VERSION) == (2, 1, 2, 2, 1)


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

    monkeypatch.setattr(O, "check_materialized_sort_swo", oracle_check)
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

    with direct.prepare_cell(cell, "fixture-pin", cxx="fixture-cxx") as prepared:
        assert prepared.src_token == "fixture-source"
        assert prepared.oracle_attempt is not None
        assert prepared.oracle_attempt["classification"] == "pass"
        assert prepared.oracle_attempt["oracle_receipt"]["contract_id"] == O.ORACLE_CONTRACT_ID
    assert order == ["oracle", "resolve"]


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-v"]))
