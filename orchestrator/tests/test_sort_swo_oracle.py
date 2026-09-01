# -*- coding: utf-8 -*-
"""Independent sort SWO oracle: matrix laws, real C++ E2E, and constraints."""
from __future__ import annotations

import contextlib
import hashlib
import inspect
import json
from pathlib import Path
import shutil
import stat
import subprocess
import sys

import pytest

from orchestrator.campaign import evolve_block as EB
from orchestrator.campaign import sort_swo_oracle as O
from orchestrator.tests import sort_swo_masstree_fixture as masstree_fixture
from orchestrator.tests import sort_swo_oracle_receipt_memo as oracle_environment_memo
from orchestrator.tests.condition_gate_test_support import (
    SORT_VARIANT_SOURCE,
    condition_gate_compilers,
    install_condition_gate_build_fixture,
)


_ROOT = Path(__file__).resolve().parents[2]
_CCBENCH = _ROOT / "external" / "ccbench"


def _get_oracle_environment():
    """Read the controller-prewarmed environment snapshot, fail-closed."""
    return oracle_environment_memo.get_oracle_environment()


_CLEAN_IMPL = (
    "    sort(write_set_.begin(), write_set_.end(),\n"
    "         [](const auto& a, const auto& b) { return a.key_ < b.key_; });"
)
_BODY_IMPL = (
    "    sort(write_set_.begin(), write_set_.end(),\n"
    "         [](const auto& a, const auto& b) {\n"
    "           return a.body_.get_val() < b.body_.get_val();\n"
    "         });"
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
           if (oracle_test_mode == 8) {
             observation_count = 0;
             return a.key_ < b.key_;
           }
           return std::less<Tuple*>{}(a.rcdptr_, b.rcdptr_);
         });
'''

_SNAPSHOT_NEGATIVE_IMPL = r'''
    sort(write_set_.begin(), write_set_.end(),
         [](const auto& a, const auto& b) {
           const int mode = oracle_test_mode % 100;
           if (mode == 20) {
             volatile Storage* target =
                 &const_cast<WriteElement<Tuple>&>(a).storage_;
             const Storage saved = *target;
             *target = static_cast<Storage>(7u); *target = saved;
           } else if (mode == 21 && !a.key_.empty()) {
             volatile char* target = const_cast<volatile char*>(a.key_.data());
             const char saved = *target;
             *target = static_cast<char>(saved ^ 1); *target = saved;
           } else if (mode == 22) {
             auto key = a.body_.get_key();
             volatile char* target = const_cast<volatile char*>(key.data());
             const char saved = *target;
             *target = static_cast<char>(saved ^ 1); *target = saved;
           } else if (mode == 23) {
             volatile char* target = static_cast<volatile char*>(
                 const_cast<TupleBody&>(a.body_).get_val_ptr());
             const char saved = *target;
             *target = static_cast<char>(saved ^ 1); *target = saved;
           } else if (mode == 24) {
             volatile char* target =
                 const_cast<WriteElement<Tuple>&>(a).get_val_ptr();
             const char saved = *target;
             *target = static_cast<char>(saved ^ 1); *target = saved;
           } else if (mode == 25 && a.rcdptr_ != nullptr) {
             volatile std::uint64_t* target = &a.rcdptr_->tidword_.obj_;
             const std::uint64_t saved = *target;
             *target = saved ^ 1u; *target = saved;
           } else if (mode == 26 && a.rcdptr_ != nullptr) {
             auto key = a.rcdptr_->body_.get_key();
             volatile char* target = const_cast<volatile char*>(key.data());
             const char saved = *target;
             *target = static_cast<char>(saved ^ 1); *target = saved;
           } else if (mode == 27 && a.rcdptr_ != nullptr) {
             volatile char* target = static_cast<volatile char*>(
                 a.rcdptr_->body_.get_val_ptr());
             const char saved = *target;
             *target = static_cast<char>(saved ^ 1); *target = saved;
           }
           return a.key_ < b.key_;
         });
'''

_SANDBOX_NEGATIVE_IMPL = r'''
    sort(write_set_.begin(), write_set_.end(),
         [](const auto& a, const auto& b) {
           const int mode = oracle_test_mode % 1000;
           if (mode == 300) {
             const int fd = static_cast<int>(::syscall(
                 SYS_openat, AT_FDCWD, "/proc/self/fd",
                 O_RDONLY | O_DIRECTORY | O_CLOEXEC, 0));
             char entries[4096];
             const long count = fd < 0 ? -1 : ::syscall(
                 SYS_getdents64, fd, entries, sizeof(entries));
             if (fd >= 0) ::syscall(SYS_close, fd);
             if (fd < 0 || count <= 0) return true;
           } else if (mode == 301) {
             const unsigned char byte = 0;
             ::write(198, &byte, 1);
           } else if (mode == 302) {
             const long page_size = 4096;
             void* page = reinterpret_cast<void*>(
                 reinterpret_cast<std::uintptr_t>(&a) & ~(page_size - 1));
             if (::mprotect(page, page_size, PROT_READ | PROT_WRITE) != 0) return true;
             auto& target = const_cast<WriteElement<Tuple>&>(a).storage_;
             const auto saved = target; target = static_cast<Storage>(9u); target = saved;
             if (::mprotect(page, page_size, PROT_READ) != 0) return true;
           } else if (mode == 303) {
             void* page = oracle_arena_begin + ORACLE_ARENA_SIZE - 4096;
             if (::munmap(page, 4096) != 0) return true;
             void* shadow = ::mmap(page, 4096, PROT_READ | PROT_WRITE,
                 MAP_PRIVATE | MAP_ANONYMOUS | MAP_FIXED, -1, 0);
             if (shadow != page) return true;
             static_cast<unsigned char*>(shadow)[0] = 0x5a;
           } else if (mode == 304) {
             struct sigaction action{};
             action.sa_handler = +[](int) {};
             if (::sigaction(SIGSEGV, &action, nullptr) != 0) return true;
           }
           return a.key_ < b.key_;
         });
'''

_ABORT_IMPL = r'''
    sort(write_set_.begin(), write_set_.end(),
         [](const auto&, const auto&) {
           HeapObject empty;
           return empty.view().size() != 0;
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
    """Compile the bounded worker set once for all real boundary checks."""
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
    verified_dependency = O._prepare_verified_dependency(
        oracle_environment.dependency_root,
        scratch / "verified-masstree",
    )
    artifacts = {}
    compile_count = 0
    for name, statement in (
        ("positive", _CLEAN_IMPL),
        ("body", _BODY_IMPL),
        ("negative", _MULTIPLEXED_NEGATIVE_IMPL),
        ("snapshot", _SNAPSHOT_NEGATIVE_IMPL),
        ("sandbox", _SANDBOX_NEGATIVE_IMPL),
        ("abort", _ABORT_IMPL),
    ):
        executable = scratch / name
        finding, unavailable = O._compile_verified(
            O._translation_unit(statement), scratch / f"{name}.cpp", executable,
            compiler=str(oracle_environment.compiler), ccbench_dir=oracle_environment.ccbench_dir,
            dependency=verified_dependency,
            fault_injection=name in {"snapshot", "sandbox"},
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
    """POS-1/POS-2: clean key and real-body comparators are exact PASS."""
    compiled_oracle_artifacts = _get_compiled_oracle_artifacts(tmp_path_factory)
    assert O._evaluate_executable(compiled_oracle_artifacts["positive"]) is None
    assert O._evaluate_executable(compiled_oracle_artifacts["body"]) is None
    environment = compiled_oracle_artifacts["environment"]
    for statement in (_CLEAN_IMPL, _BODY_IMPL):
        result = O.check_materialized_sort_swo(
            _materialized(statement), marker_id="silo-writeset-sort",
            proposal_source=statement, environment=environment,
        )
        assert result.status is O.OracleStatus.PASS
        assert result.finding is None


def test_cpp_e2e_stable_cross_allocation_pointer_positive(tmp_path_factory):
    """P2: std::less compares pointers from separate allocations stably and passes."""
    compiled_oracle_artifacts = _get_compiled_oracle_artifacts(tmp_path_factory)
    assert O._evaluate_executable(
        compiled_oracle_artifacts["negative"], test_mode=0,
    ) is None
    result = O.check_materialized_sort_swo(
        _materialized(_MULTIPLEXED_NEGATIVE_IMPL),
        marker_id="silo-writeset-sort",
        proposal_source=_MULTIPLEXED_NEGATIVE_IMPL,
        environment=compiled_oracle_artifacts["environment"],
    )
    assert result.status is O.OracleStatus.PASS
    assert result.finding is None


def test_real_ctor_pointer_topology_and_triplicate_have_expected_matrix_meaning(
        tmp_path_factory):
    compiled_oracle_artifacts = _get_compiled_oracle_artifacts(tmp_path_factory)
    pointer_matrix, pointer_finding = O._run_matrix(
        compiled_oracle_artifacts["negative"], 0, 0, test_mode=0,
    )
    assert pointer_finding is None and pointer_matrix is not None
    # Corpus-0 indices 5 and 6 are distinct allocation slots. std::less must
    # order exactly one direction after the real WriteElement ctor.
    assert O._CORPUS_MANIFEST[0][5][2:4] == (2, 0)
    assert O._CORPUS_MANIFEST[0][6][2:4] == (2, 1)
    assert bool(pointer_matrix[5 * O._N + 6]) != bool(pointer_matrix[6 * O._N + 5])

    key_matrix, key_finding = O._run_matrix(
        compiled_oracle_artifacts["positive"], 0, 0,
    )
    assert key_finding is None and key_matrix is not None
    assert tuple(item[:4] for item in O._CORPUS_MANIFEST[0][:3]) == (
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
    assert finding.kind is O.OracleRejectKind.EXECUTION
    assert finding.reason_code == "candidate-execution-fault"

    clean_matrix, clean_finding = O._run_matrix(
        compiled_oracle_artifacts["positive"], 0, 0,
    )
    assert clean_finding is None and clean_matrix is not None
    allocation_classes = {
        20: "element",
        21: "element-key-pointee",
        22: "element-body-key",
        23: "element-body-value",
        24: "write-value-buffer",
        25: "tuple-object",
        26: "tuple-body-key",
        27: "tuple-body-value",
    }
    for mode, allocation_class in allocation_classes.items():
        _matrix_value, denied = O._run_matrix(
            compiled_oracle_artifacts["snapshot"], 0, 0,
            test_mode=2000 + mode,
        )
        assert denied is not None, allocation_class
        assert denied.kind is O.OracleRejectKind.EXECUTION, allocation_class
        assert denied.reason_code == "candidate-execution-fault", allocation_class
        assert all(
            observation.get("write_denied") is not True
            for observation in denied.observations
        ), allocation_class

        control_matrix, control_finding = O._run_matrix(
            compiled_oracle_artifacts["snapshot"], 0, 0,
            test_mode=1000 + mode,
        )
        assert control_finding is None, allocation_class
        assert control_matrix == clean_matrix, allocation_class

    sandbox_surfaces = {
        300: "openat-plus-getdents64",
        301: "write-non-observation-fd",
        302: "mprotect",
        303: "arena-shadow-mmap-plus-munmap",
        304: "rt-sigaction",
    }
    for mode, surface in sandbox_surfaces.items():
        _matrix_value, denied = O._run_matrix(
            compiled_oracle_artifacts["sandbox"], 0, 0, test_mode=mode,
        )
        assert denied is not None, surface
        assert denied.kind is O.OracleRejectKind.EXECUTION, surface
        assert denied.reason_code == "candidate-sandbox-violation", surface

        control_matrix, control_finding = O._run_matrix(
            compiled_oracle_artifacts["sandbox"], 0, 0,
            test_mode=1000 + mode,
        )
        assert control_finding is None, surface
        assert control_matrix == clean_matrix, surface

    _matrix_value, aborted = O._run_matrix(
        compiled_oracle_artifacts["abort"], 0, 0,
    )
    assert aborted is not None
    assert aborted.kind is O.OracleRejectKind.EXECUTION
    assert aborted.reason_code == "candidate-comparator-aborted"

    fd_timeline = []
    matrix, timeline_finding = O._run_matrix(
        compiled_oracle_artifacts["positive"], 0, 0,
        fd_observer=lambda *event: fd_timeline.append(event),
    )
    assert timeline_finding is None and matrix == clean_matrix
    assert [event[0] for event in fd_timeline] == [
        "stopped", "authority-sent",
    ]
    before, authority_event = fd_timeline
    assert before[1] == authority_event[1]
    assert before[2] == authority_event[2]
    assert before[3] is None
    assert authority_event[3] not in before[2]
    assert O._worker_fd_boundary_is_safe(
        before[2], authority_event[2], authority_event[3],
        final_created_after_stop=True,
    )
    assert not O._worker_fd_boundary_is_safe(
        before[2], authority_event[2] + (authority_event[3],),
        authority_event[3],
        final_created_after_stop=True,
    )
    assert not O._worker_fd_boundary_is_safe(
        before[2], authority_event[2], authority_event[3],
        final_created_after_stop=False,
    )

    for mode, mutation in ((1404, "fork-inherit-close"), (1405, "dup-number")):
        injected_timeline = []
        expected_phase, expected_detail = (
            ("protocol-authority", "worker-fd-boundary-verification-failed")
            if mode == 1404
            else ("worker-hardening", "worker-hardening-preflight-failed")
        )
        with pytest.raises(
            O._EvaluationUnavailable,
            match=expected_detail,
        ) as failure:
            O._run_matrix(
                compiled_oracle_artifacts["sandbox"], 0, 0,
                test_mode=mode,
                fd_observer=lambda *event: injected_timeline.append(event),
            )
        assert failure.value.phase == expected_phase, mutation
        if mode == 1404:
            assert [event[0] for event in injected_timeline] == [
                "stopped", "authority-sent",
            ], mutation
            injected_before, injected_authority = injected_timeline
            assert injected_before[2] == injected_authority[2], mutation
            assert not O._worker_fd_boundary_is_safe(
                injected_before[2], injected_authority[2],
                injected_authority[3], final_created_after_stop=False,
            ), mutation
            assert injected_authority[3] not in injected_before[2]
        else:
            assert injected_timeline == []


def test_broker_rejects_final_pipe_identity_held_at_different_worker_fd(
        tmp_path):
    """Removing the parent reservation or child dup2 makes the fd inequality guard fail."""
    worker_path = tmp_path / "fd-identity-worker"
    worker_path.write_text(
        f"""#!{sys.executable}
import os
import signal
import stat
import sys

observation_fd = int(sys.argv[3])
expected_identity = tuple(int(value) for value in sys.argv[4:7])
metadata = os.fstat(observation_fd)
actual_identity = (
    metadata.st_dev, metadata.st_ino, stat.S_IFMT(metadata.st_mode),
)
if actual_identity != expected_identity:
    os._exit(76)
os.closerange(0, observation_fd)
os.closerange(observation_fd + 1, 65536)
os.kill(os.getpid(), signal.SIGSTOP)
os.kill(os.getpid(), signal.SIGSTOP)
os.write(observation_fd, bytes({2 * O._N * O._N}))
os._exit(0)
""",
        encoding="utf-8",
    )
    worker_path.chmod(0o700)

    authority, broker_authority = O.socket.socketpair(
        O.socket.AF_UNIX, O.socket.SOCK_SEQPACKET,
    )
    worker_fd_number = O.os.open(O.os.devnull, O.os.O_RDONLY)
    reserved_identity = O._broker_fd_identity(worker_fd_number)
    assert broker_authority.fileno() != worker_fd_number
    broker_pid = O.os.fork()
    if broker_pid == 0:
        authority.close()
        O.os.setsid()
        real_pipe = O.os.pipe
        real_read = O.os.read
        real_send_control = O._broker_send_control
        transferred_pipe_fds = []

        def pipe_with_controller_transfer():
            observation_read, observation_write = real_pipe()
            O.os.set_blocking(observation_read, False)
            O.os.dup2(observation_write, worker_fd_number)
            O.os.close(observation_write)
            transferred_pipe_fds.extend((
                O.os.dup(observation_read), O.os.dup(worker_fd_number),
            ))
            return observation_read, worker_fd_number

        def send_control_with_pipe(authority_socket, payload):
            if not payload.startswith(b"R:"):
                real_send_control(authority_socket, payload)
                return
            authority_socket.sendmsg(
                [payload],
                [(O.socket.SOL_SOCKET, O.socket.SCM_RIGHTS,
                  O.array("i", transferred_pipe_fds))],
            )
            for fd in transferred_pipe_fds:
                O.os.close(fd)
            transferred_pipe_fds.clear()

        def nonblocking_observation_read(fd, size):
            try:
                return real_read(fd, size)
            except BlockingIOError:
                return b""

        O.os.pipe = pipe_with_controller_transfer
        O.os.read = nonblocking_observation_read
        O._broker_send_control = send_control_with_pipe
        status = O._broker_main([
            str(worker_path), "0", "0", str(broker_authority.fileno()),
        ])
        O.os._exit(status)

    broker_authority.close()
    final_read_fd = None
    final_write_fd = None
    worker_pid = None
    broker_reaped = False
    received_fds = []
    try:
        authority.settimeout(O._RUN_TIMEOUT_S)
        item_size = O.array("i").itemsize
        ready, ancillary, flags, _address = authority.recvmsg(
            4096, O.socket.CMSG_SPACE(2 * item_size),
        )
        assert ready.startswith(b"R:")
        assert not flags & (O.socket.MSG_CTRUNC | O.socket.MSG_TRUNC)
        for level, kind, data in ancillary:
            if level == O.socket.SOL_SOCKET and kind == O.socket.SCM_RIGHTS:
                values = O.array("i")
                values.frombytes(data[:len(data) - len(data) % item_size])
                received_fds.extend(values)
        assert len(received_fds) == 2
        final_read_fd, final_write_fd = received_fds
        received_fds.clear()

        ready_payload = O.json.loads(ready[2:].decode("ascii"))
        assert set(ready_payload) == {"fd_identities", "pid"}
        worker_pid = int(ready_payload["pid"])
        before = tuple(
            tuple(int(field) for field in identity)
            for identity in ready_payload["fd_identities"]
        )
        final_identity = O._broker_fd_identity(final_write_fd)
        assert before == (final_identity,)
        worker_metadata = O.os.stat(f"/proc/{worker_pid}/fd/{worker_fd_number}")
        assert (
            worker_metadata.st_dev,
            worker_metadata.st_ino,
            stat.S_IFMT(worker_metadata.st_mode),
        ) == final_identity
        assert O._broker_fd_identity(worker_fd_number) == reserved_identity
        assert final_write_fd != worker_fd_number

        authority.sendmsg(
            [b"F"],
            [(O.socket.SOL_SOCKET, O.socket.SCM_RIGHTS,
              O.array("i", [final_write_fd]))],
        )
        O.os.close(final_write_fd)
        final_write_fd = None
        O._broker_send_control(authority, b"A")
        waited_pid, broker_status = O.os.waitpid(broker_pid, 0)
        broker_reaped = True
        assert waited_pid == broker_pid
        assert O.os.WIFEXITED(broker_status)
        assert O.os.WEXITSTATUS(broker_status) == 0

        record = O._read_all(final_read_fd, O._RECORD_SIZE)
        assert len(record) == O._RECORD_SIZE
        unpacked = O._HEADER.unpack(record[:O._HEADER.size])
        assert unpacked[5:7] == (
            O._BROKER_OUTCOME_INFRASTRUCTURE,
            O._BROKER_DETAIL_FD_BOUNDARY,
        ), unpacked[5:7]
    finally:
        authority.close()
        O.os.close(worker_fd_number)
        for fd in (*received_fds, final_read_fd, final_write_fd):
            if fd is not None:
                O.os.close(fd)
        if not broker_reaped:
            if worker_pid is not None:
                try:
                    O.os.kill(worker_pid, O.signal.SIGKILL)
                except ProcessLookupError:
                    pass
            try:
                O.os.killpg(broker_pid, O.signal.SIGKILL)
            except ProcessLookupError:
                pass
            try:
                O.os.kill(broker_pid, O.signal.SIGKILL)
            except ProcessLookupError:
                pass
            try:
                O.os.waitpid(broker_pid, 0)
            except ChildProcessError:
                pass


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
    count_finding = O._evaluate_executable(
        compiled_oracle_artifacts["negative"], test_mode=8,
    )
    assert count_finding is not None
    assert count_finding.kind is O.OracleRejectKind.EXECUTION
    assert count_finding.reason_code == "candidate-comparator-call-count-invalid"


def test_real_compile_budget_is_fixed_positive_and_negative_only(tmp_path_factory):
    compiled_oracle_artifacts = _get_compiled_oracle_artifacts(tmp_path_factory)
    assert compiled_oracle_artifacts["compile_count"] == 6


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
    fixture_relative = masstree_fixture.FIXTURE_ROOT.relative_to(_ROOT)
    required_tracked = {
        (fixture_relative / relative).as_posix()
        for relative, _digest in verified.files
    }
    completed = subprocess.run(
        ["git", "ls-files", "--", fixture_relative.as_posix()],
        cwd=_ROOT, check=True, capture_output=True, text=True,
    )
    tracked = set(completed.stdout.splitlines())
    assert required_tracked <= tracked
    ignored_required = (fixture_relative / "config.h").as_posix()
    assert ignored_required in required_tracked
    assert required_tracked - (tracked - {ignored_required}) == {
        ignored_required
    }

    compiled_oracle_artifacts = _get_compiled_oracle_artifacts(tmp_path_factory)
    environment = compiled_oracle_artifacts["environment"]
    assert type(environment) is O.OracleEnvironment
    assert environment.dependency_root == masstree_fixture.FIXTURE_ROOT.resolve()
    assert O._evaluate_executable(compiled_oracle_artifacts["positive"]) is None


def test_production_dependency_verifier_copies_canonical_bytes_privately(tmp_path):
    private_root = tmp_path / "private-masstree"
    verified = O._prepare_verified_dependency(
        masstree_fixture.FIXTURE_ROOT, private_root,
    )
    assert type(verified) is O._VerifiedDependencyRoot
    assert verified.root == private_root.resolve()
    assert verified.root != masstree_fixture.FIXTURE_ROOT.resolve()
    assert verified.manifest_sha256 == O.DEPENDENCY_MANIFEST_SHA256
    assert verified.config_sha256 == dict(verified.files)["config.h"]
    assert len(verified.files) == 101
    assert stat.S_IMODE(private_root.stat().st_mode) & 0o077 == 0
    O._assert_verified_dependency_unchanged(verified)


@pytest.mark.parametrize(
    "mutation",
    ["unregistered-file", "symlink", "changed-byte", "missing-file"],
)
def test_production_dependency_verifier_rejects_manifest_boundary_mutations(
        tmp_path, mutation):
    fixture = _copy_masstree_fixture(tmp_path)
    if mutation == "unregistered-file":
        (fixture / "unregistered.hh").write_text("// extra\n", encoding="utf-8")
    elif mutation == "symlink":
        (fixture / "escape.hh").symlink_to(tmp_path / "outside.hh")
    elif mutation == "changed-byte":
        with (fixture / "config.h").open("ab") as stream:
            stream.write(b"\n")
    else:
        (fixture / "config.h").unlink()
    with pytest.raises(O._DependencyVerificationError):
        O._prepare_verified_dependency(fixture, tmp_path / "private")


def test_compile_verified_fails_closed_before_compiler_on_private_copy_change(
        monkeypatch, tmp_path):
    verified = O._prepare_verified_dependency(
        masstree_fixture.FIXTURE_ROOT, tmp_path / "private",
    )
    (verified.root / "config.h").write_bytes(b"changed")
    compiler_called = False

    def compiler(*args, **kwargs):
        nonlocal compiler_called
        compiler_called = True
        return None, False

    monkeypatch.setattr(O, "_compile", compiler)
    finding, unavailable = O._compile_verified(
        "int main() {}", tmp_path / "candidate.cpp", tmp_path / "candidate",
        compiler="/usr/bin/c++", ccbench_dir=_CCBENCH,
        dependency=verified,
    )
    assert unavailable is True
    assert finding is not None
    assert finding.reason_code == "dependency-sha256-mismatch"
    assert compiler_called is False


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
    assert result.receipt.tu_sha256 == O._translation_unit_bundle_sha256(
        O._translation_unit(observed)
    )
    attempt = O.attempt_record(result)
    assert attempt["classification"] == "pass"
    assert attempt["oracle_receipt"] == result.receipt.as_dict()


def test_shared_evolve_block_parser_preserves_public_wrapper_bytes():
    statement = "  " + _CLEAN_IMPL + "\n"
    source = _materialized(statement)
    shared = EB.extract_materialized_evolve_block(source, "silo-writeset-sort")
    assert shared.hole == statement + "\n"
    assert O.extract_materialized_hole(source, "silo-writeset-sort") == shared.hole
    assert shared.conditional.startswith("#if ")
    assert shared.conditional.endswith("#endif\n")


@pytest.mark.parametrize(
    ("source", "message"),
    [
        ("", "materialized marker boundary is not unique"),
        (
            _materialized(_CLEAN_IMPL) + _materialized(_CLEAN_IMPL),
            "materialized marker boundary is not unique",
        ),
        (
            _materialized(_CLEAN_IMPL).replace("#else", "#elif 1"),
            "materialized marker does not contain one #if/#else/#endif",
        ),
    ],
)
def test_shared_evolve_block_parser_preserves_public_wrapper_rejections(source, message):
    with pytest.raises(ValueError, match=message):
        EB.extract_materialized_evolve_block(source, "silo-writeset-sort")
    with pytest.raises(ValueError, match=message):
        O.extract_materialized_hole(source, "silo-writeset-sort")


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
    assert all(tuple(item[:4] for item in corpus[:3]) == ((0, b"", 1, 0),) * 3
               for corpus in O._CORPUS_MANIFEST)
    assert all({item[2] for item in corpus} == {0, 1, 2}
               for corpus in O._CORPUS_MANIFEST)
    assert all(
        len(item[4]) > 20 and item[5] and item[6]
        for corpus in O._CORPUS_MANIFEST for item in corpus
    )
    assert all(
        len(key) > 20 and value
        for corpus in O._TUPLE_BODY_MANIFEST for key, value in corpus
    )
    assert O._N >= 17 and O._CORPORA == (0, 1) and O._ORDERS == (0, 1, 2)


def test_public_oracle_domain_aliases_track_contract_inputs():
    assert (O.N, O.CORPORA, O.ORDERS) == (O._N, O._CORPORA, O._ORDERS)


def test_contract_digest_binds_axiom_checker_source_component():
    assert O._ORACLE_CONTRACT_COMPONENTS_SCHEMA == (
        "sort-swo-contract-components-v2"
    )
    assert O._ORACLE_CONTRACT_COMPONENTS == {
        "axiom_checker_implementation_sha256": (
            O.AXIOM_CHECKER_IMPLEMENTATION_SHA256
        ),
        "compile_flags_sha256": O.COMPILE_FLAGS_SHA256,
        "corpus_sha256": O.CORPUS_SHA256,
        "dependency_manifest_sha256": O.DEPENDENCY_MANIFEST_SHA256,
        "guarantee_boundary_sha256": hashlib.sha256(
            O.SORT_SWO_GUARANTEE_BOUNDARY.encode("ascii")
        ).hexdigest(),
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
        O._parse_dependency_manifest,
        O._dependency_file_inventory,
        O._verify_dependency_root,
        O._read_verified_dependency_file,
        O._prepare_verified_dependency,
        O._assert_verified_dependency_unchanged,
        O._dependency_command,
        O._dependency_manifest_closure,
        O._compile_verified,
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

    worker = O._translation_unit(O._STATEMENT_PLACEHOLDER)
    current_tu_bundle = O._translation_unit_bundle_sha256(worker)
    broker_target = O._broker_main
    broker_source = real_getsource(broker_target)
    monkeypatch.setattr(
        O.inspect,
        "getsource",
        lambda function: (
            broker_source + "\n# broker-source-mutation\n"
            if function is broker_target else real_getsource(function)
        ),
    )
    assert O._translation_unit_bundle_sha256(worker) != current_tu_bundle


def _independent_tu_template_sha256() -> str:
    """Rebuild the canonical worker/broker bundle without producer helpers."""
    members = [
        ("worker", O._TU_PREFIX + O._STATEMENT_PLACEHOLDER + O._TU_SUFFIX),
    ]
    for function in (
        O._broker_fd_identity,
        O._broker_worker_fd_numbers,
        O._broker_worker_fd_identities_from_snapshot,
        O._worker_fd_boundary_is_safe,
        O._broker_send_control,
        O._broker_receive_control,
        O._broker_receive_fd,
        O._broker_write_all,
        O._broker_order,
        O._broker_frame,
        O._broker_main,
    ):
        members.append((
            f"broker:{function.__module__}.{function.__qualname__}",
            inspect.getsource(function),
        ))
    members.append((
        "broker-semantics",
        json.dumps(
            {
                "broker_details": {
                    "aborted": O._BROKER_DETAIL_ABORTED,
                    "call_count": O._BROKER_DETAIL_CALL_COUNT,
                    "comparator_threw": O._BROKER_DETAIL_COMPARATOR_THREW,
                    "cpu": O._BROKER_DETAIL_CPU,
                    "execution_fault": O._BROKER_DETAIL_EXECUTION_FAULT,
                    "fd_boundary": O._BROKER_DETAIL_FD_BOUNDARY,
                    "observation_size": O._BROKER_DETAIL_OBSERVATION_SIZE,
                    "observation_value": O._BROKER_DETAIL_OBSERVATION_VALUE,
                    "observation_write": O._BROKER_DETAIL_OBSERVATION_WRITE,
                    "ok": O._BROKER_DETAIL_OK,
                    "repeat": O._BROKER_DETAIL_REPEAT,
                    "sandbox": O._BROKER_DETAIL_SANDBOX,
                    "signal": O._BROKER_DETAIL_SIGNAL,
                    "sort_contract": O._BROKER_DETAIL_SORT_CONTRACT,
                },
                "broker_outcomes": {
                    "infrastructure": O._BROKER_OUTCOME_INFRASTRUCTURE,
                    "ok": O._BROKER_OUTCOME_OK,
                    "reject": O._BROKER_OUTCOME_REJECT,
                },
                "header": O._HEADER.format,
                "magic_hex": O._MAGIC.hex(),
                "n": O._N,
                "protocol_version": O.PROTOCOL_VERSION,
            },
            sort_keys=True, separators=(",", ":"), ensure_ascii=True,
        ),
    ))
    digest = hashlib.sha256()
    for label, source in members:
        for value in (label.encode("utf-8"), source.encode("utf-8")):
            digest.update(len(value).to_bytes(8, "big"))
            digest.update(value)
    return digest.hexdigest()


def _independent_axiom_checker_sha256() -> str:
    digest = hashlib.sha256()
    for function in (
        O.check_relation_matrix,
        O._evaluate_executable,
        O._run_matrix,
        O._compile_command,
        O._parse_dependency_manifest,
        O._dependency_file_inventory,
        O._verify_dependency_root,
        O._read_verified_dependency_file,
        O._prepare_verified_dependency,
        O._assert_verified_dependency_unchanged,
        O._dependency_command,
        O._dependency_manifest_closure,
        O._compile_verified,
    ):
        for value in (
            f"{function.__module__}.{function.__qualname__}".encode("utf-8"),
            inspect.getsource(function).encode("utf-8"),
        ):
            digest.update(len(value).to_bytes(8, "big"))
            digest.update(value)
    semantics = json.dumps(
        {
            "_CORPORA": (0, 1),
            "_DEPENDENCY_MANIFEST_NAME": "SHA256SUMS",
            "_MIN_DEPENDENCY_MANIFEST_CLOSURE": 31,
            "_N": 18,
            "_ORDERS": (0, 1, 2),
        },
        sort_keys=True, separators=(",", ":"), ensure_ascii=True,
    ).encode("utf-8")
    digest.update(len(semantics).to_bytes(8, "big"))
    digest.update(semantics)
    return digest.hexdigest()


def _independent_contract_id(
    tu_template_sha256: str,
    dependency_manifest_sha256: str,
    axiom_checker_sha256: str,
) -> tuple[str, str]:
    components = {
        "axiom_checker_implementation_sha256": axiom_checker_sha256,
        "compile_flags_sha256": O.COMPILE_FLAGS_SHA256,
        "corpus_sha256": O.CORPUS_SHA256,
        "dependency_manifest_sha256": dependency_manifest_sha256,
        "guarantee_boundary_sha256": hashlib.sha256(
            O.SORT_SWO_GUARANTEE_BOUNDARY.encode("ascii")
        ).hexdigest(),
        "tu_template_sha256": tu_template_sha256,
    }
    canonical = json.dumps(
        {
            "components": components,
            "schema": "sort-swo-contract-components-v2",
        },
        sort_keys=True, separators=(",", ":"), ensure_ascii=True,
    ).encode("utf-8")
    components_sha256 = hashlib.sha256(canonical).hexdigest()
    contract_id = (
        f"sort-swo-v{O.CONTRACT_VERSION}-corpus{O.CORPUS_VERSION}-"
        f"protocol{O.PROTOCOL_VERSION}-checker{O.AXIOM_CHECKER_VERSION}-"
        f"grammar{O.GRAMMAR_VERSION}-x{components_sha256}-"
        f"c{O.CORPUS_SHA256[:12]}-tu{tu_template_sha256[:12]}-"
        f"f{O.COMPILE_FLAGS_SHA256[:12]}-"
        f"a{axiom_checker_sha256[:12]}"
    )
    return components_sha256, contract_id


def test_contract_manifest_hashes_and_literal_are_exact_snapshot():
    independent_tu_sha256 = _independent_tu_template_sha256()
    independent_axiom_checker_sha256 = _independent_axiom_checker_sha256()
    independent_dependency_manifest_sha256 = hashlib.sha256(
        (masstree_fixture.FIXTURE_ROOT / masstree_fixture.MANIFEST_NAME).read_bytes()
    ).hexdigest()
    independent_components_sha256, independent_contract_id = (
        _independent_contract_id(
            independent_tu_sha256,
            independent_dependency_manifest_sha256,
            independent_axiom_checker_sha256,
        )
    )
    assert independent_tu_sha256 == O.TU_TEMPLATE_SHA256
    assert independent_axiom_checker_sha256 == O.AXIOM_CHECKER_IMPLEMENTATION_SHA256
    assert independent_dependency_manifest_sha256 == O.DEPENDENCY_MANIFEST_SHA256
    assert independent_components_sha256 == O.ORACLE_COMPONENTS_SHA256
    assert independent_contract_id == O.ORACLE_CONTRACT_ID
    assert O.CORPUS_SHA256 == "7d25fac23469f4bb807bccd4fb97dc7a6fbcf34dd5de602ba08bcf7bb70df5eb"
    assert O.TU_TEMPLATE_SHA256 == "7732f044d8ab2b657231cfeb132f59a981b761b9ac62a8d61e6b5338140083e4"
    assert O.COMPILE_FLAGS_SHA256 == "3caa77f8111ff611183eaec0acfdff11eb75d74c81a3bfec66262674921c3b25"
    assert O.ORACLE_CONTRACT_ID == (
        "sort-swo-v4-corpus2-protocol3-checker3-grammar1-"
        "x5474fdb4483a32d73d82b29908152e7f004bb2c921963d3aa5a3d5654a0c012a-"
        "c7d25fac23469-tu7732f044d8ab-f3caa77f8111f-a0af8a35f3f9a"
    )
    assert (O.CONTRACT_VERSION, O.CORPUS_VERSION, O.PROTOCOL_VERSION,
            O.AXIOM_CHECKER_VERSION, O.GRAMMAR_VERSION) == (4, 2, 3, 3, 1)


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
    assert "OracleWriteSet* write_set_storage = nullptr;" in source
    assert "OracleWriteSet& write_set_ = *write_set_storage;" in source
    assert "write_set_storage->emplace_back(" in source
    assert "active_write_set = write_set_storage;" in source
    assert "first != active_write_set->begin()" in source
    assert "spec.write_value" in source
    assert "write_set_storage->elements.back().body_ = TupleBody(" in source
    assert "struct WriteElement" not in source
    assert "const WriteElement<Tuple>& lhs_element" in source
    assert "inventory_corpus(&write_set_, aliases, separate, corpus_id)" in source
    assert "mprotect(oracle_arena_begin" in source
    assert "SECCOMP_RET_KILL_PROCESS" in source
    assert source.index("offsetof(struct seccomp_data, arch)") < source.index(
        "offsetof(struct seccomp_data, nr)"
    )
    for forbidden_allow in (
        "SYS_rt_sigprocmask", "SYS_sigaltstack", "SYS_mremap",
        "SYS_madvise", "SYS_shmat", "SYS_shmdt", "SYS_remap_file_pages",
        "SYS_process_madvise", "SYS_userfaultfd", "SYS_pidfd_open",
        "SYS_pidfd_getfd", "SYS_io_uring_setup", "SYS_io_uring_enter",
        "SYS_io_uring_register", "SYS_dup", "SYS_dup2", "SYS_dup3",
        "SYS_fcntl", "SYS_recvmsg", "SYS_ptrace", "SYS_process_vm_writev",
    ):
        assert f"allow_syscall(*filter, {forbidden_allow})" not in source
    assert "mode == 1300" in source and "allow_syscall(*filter, SYS_openat)" in source
    assert "mode == 1301" in source and "allow_any_write" in source
    assert "mode == 1302" in source and "allow_syscall(*filter, SYS_mprotect)" in source
    assert "mode == 1303" in source and "allow_syscall(*filter, SYS_mmap)" in source
    assert "mode == 1304" in source and "allow_syscall(*filter, SYS_rt_sigaction)" in source
    assert "PR_SET_NO_NEW_PRIVS" in source
    assert "PR_SET_DUMPABLE" in source
    assert "::fstat(observation_fd, &observation_stat)" in source
    assert "expected_observation_dev" in source
    assert "expected_observation_ino" in source
    assert "expected_observation_type" in source
    assert "#ifdef NDEBUG" in source
    assert "IZSWO3" not in source
    assert "_BROKER_OUTCOME" not in source
    assert "trusted_snapshot" not in source
    assert "Known residual" in source
    assert O._COMPILE_FLAGS[-1] == "-DFORCE_ENABLE_ASSERTIONS=1"
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
        O.resource.RLIMIT_NOFILE, O.resource.RLIMIT_CORE,
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


def test_candidate_stdout_stderr_are_discarded_and_matrix_uses_dedicated_fd():
    runner = inspect.getsource(O._run_matrix)
    broker = inspect.getsource(O._broker_main)
    assert "stdout=subprocess.DEVNULL" in runner
    assert "stderr=subprocess.DEVNULL" in runner
    assert "pass_fds=tuple(inherited_fds)" in runner
    assert runner.index("_broker_receive_control(authority)") < runner.index(
        "if final_created_after_stop:"
    )
    assert "SCM_RIGHTS" in runner
    assert "after = before" not in runner
    assert "after = before" not in broker
    assert "_broker_worker_fd_identities_from_snapshot(" in broker
    assert broker.index("acknowledged = _broker_receive_control(authority)") < broker.index(
        "observed_numbers = _broker_worker_fd_numbers(worker_fd_directory)"
    )
    assert broker.index("worker_pid = os.fork()") < broker.index(
        "final_fd = _broker_receive_fd(authority)"
    )
    assert 'test_mode == "1405"' in broker
    assert "os.dup2(injected_final_fd, observation_write)" in broker
    assert "final_created_after_stop=injected_final_fd is None" in broker
    assert broker.index("reaped = os.waitid") < broker.index(
        "_broker_write_all(final_fd, frame)"
    )
    assert "_broker_write_all" not in O._translation_unit(_CLEAN_IMPL)


def test_unattributed_runtime_exit_is_infrastructure_unavailable():
    import types

    wait_result = types.SimpleNamespace(
        si_code=O.os.CLD_EXITED, si_status=1,
    )
    frame = O._broker_frame(
        wait_result, b"", 0, 0, fd_boundary_safe=True,
    )
    unpacked = O._HEADER.unpack(frame[:O._HEADER.size])
    assert unpacked[5:10] == (
        O._BROKER_OUTCOME_REJECT,
        O._BROKER_DETAIL_SIGNAL,
        O._WITNESS_NONE,
        O._WITNESS_NONE,
        1,
    )


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
        "-DKEY_SORT=0", "-DPARTITION_TABLE=0", "-DFORCE_ENABLE_ASSERTIONS=1",
    ):
        assert flag in command
    assert str(_CCBENCH) in command
    assert str(_CCBENCH / "include") in command
    assert "/fixture/masstree" in command
    assert command[-1] == "-DFORCE_ENABLE_ASSERTIONS=1"
    assert "-DIZANAGI_ORACLE_FAULT_INJECTION=1" not in command
    fault_command = O._compile_command(
        tmp_path / "fault.cpp", tmp_path / "fault",
        compiler="/usr/bin/g++", ccbench_dir=_CCBENCH,
        masstree_dir=Path("/fixture/masstree"), fault_injection=True,
    )
    assert fault_command[-2:] == [
        "-DIZANAGI_ORACLE_FAULT_INJECTION=1",
        "-DFORCE_ENABLE_ASSERTIONS=1",
    ]


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
    compilers = condition_gate_compilers()
    if compilers is None:
        pytest.skip("condition gate fixture requires real compilers and CMake")
    install_condition_gate_build_fixture(tmp_path)
    (tmp_path / "cc" / "silo" / "transaction.cc").write_text(
        SORT_VARIANT_SOURCE, encoding="utf-8",
    )

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
            cxx=compilers[1],
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
