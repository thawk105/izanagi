# -*- coding: utf-8 -*-
"""Campaign-loop result-evidence issuance with a real rejected verifier result."""
from __future__ import annotations

import dataclasses
import hashlib
import inspect
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

_HERE = Path(__file__).resolve().parent
_REPO = _HERE.parents[1]
sys.path.insert(0, str(_HERE))
sys.path.insert(0, str(_REPO))

from orchestrator.campaign import env_attestation, env_contract  # noqa: E402
from orchestrator.campaign import execution_guard  # noqa: E402
from orchestrator.campaign import layout as layout_module  # noqa: E402
from orchestrator.campaign import loop  # noqa: E402
from orchestrator.campaign import pipeline  # noqa: E402
from orchestrator.campaign import reflux_origin_binding as origin_binding  # noqa: E402
from orchestrator.campaign import reflux_result_evidence as evidence  # noqa: E402
from orchestrator.campaign import source_digest, trigger_gate_binding, wal  # noqa: E402
from orchestrator.campaign.axis_trigger_gating import (  # noqa: E402
    FROZEN_TEMPLATE_ABORT_HEAD_BYTES,
    FROZEN_TEMPLATE_PROLOGUE_BYTES,
    FROZEN_TEMPLATE_BLOCK_BYTES,
    FROZEN_TEMPLATE_EPILOGUE_BYTES,
)
from orchestrator.campaign.build_admission import (  # noqa: E402
    GeneratorId,
    attest_generator_output,
    build_run_context,
)
from orchestrator.campaign.layout import (  # noqa: E402
    CampaignLayout, ExplorationCampaignLayout, exploration_campaign_layout,
)
from orchestrator.campaign.model import (  # noqa: E402
    CampaignConfig,
    Genome,
    STAGE_ABORT,
    STAGE_BUILD_DONE,
    STAGE_BUILD_START,
)
from orchestrator.campaign.pipeline import (  # noqa: E402
    BalancedScheduleConfig,
    PerfConfig,
)
from orchestrator.campaign.reflux_ir import TriggerGateIR, emit_predicate  # noqa: E402
from orchestrator.tests import test_campaign as campaign_fixtures  # noqa: E402
from orchestrator.tests.reflux_origin_fixture_builder import (  # noqa: E402
    build_launch_admission_inputs,
    build_result_evidence_record,
)
from orchestrator.verifier import result_to_dict  # noqa: E402


_FIXTURE = _HERE / "fixtures" / "r9_dense_cycle4"
_MASK = 7
_ORDERED_VERIFIERS = (pipeline.LEGACY_TAG, pipeline.S2_TAG)


@pytest.fixture(autouse=True)
def _reset_official_output_root_pin():
    layout_module._reset_official_output_root_pin_for_tests()
    yield
    layout_module._reset_official_output_root_pin_for_tests()


def _admit_sandbox_output_root(monkeypatch, root: Path) -> None:
    """Admit one selected tmp root despite the sandbox-owned /tmp/.git marker."""
    selected = root.resolve()
    original = layout_module._has_git_ancestor

    def has_git_ancestor(path, *, label):
        if Path(path).resolve() == selected:
            return False
        return original(path, label=label)

    monkeypatch.setattr(layout_module, "_has_git_ancestor", has_git_ancestor)


def _git(root: Path, *args: str) -> str:
    completed = subprocess.run(
        [
            "git", "-c", "core.hooksPath=", "-c", "core.fsmonitor=",
            "-C", os.fspath(root), *args,
        ],
        check=True,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    return completed.stdout.strip()


def _install_compiler_aliases(tmp_path: Path, monkeypatch) -> None:
    gcc = shutil.which("gcc")
    gxx = shutil.which("g++")
    if gcc is None or gxx is None or shutil.which("cmake") is None:
        pytest.skip("real campaign fixture requires gcc, g++, and cmake")
    aliases = tmp_path / "compiler-bin"
    aliases.mkdir()
    (aliases / "gcc-13").symlink_to(gcc)
    (aliases / "g++-13").symlink_to(gxx)
    monkeypatch.setenv("PATH", os.fspath(aliases) + os.pathsep + os.environ["PATH"])


def _synthetic_silo_checkout(tmp_path: Path) -> tuple[Path, str, str]:
    """Create a buildable Git checkout with the production trigger source shape."""
    root = tmp_path / "ccbench"
    for relative in ("cmake", "include", "cc/silo", "cc/mocc"):
        (root / relative).mkdir(parents=True, exist_ok=True)

    (root / "CMakeLists.txt").write_text(
        "cmake_minimum_required(VERSION 3.16)\n"
        "project(reflux_campaign_fixture LANGUAGES CXX)\n"
        "include(cmake/Options.cmake)\n"
        "function(ccbench_add_protocol protocol)\n"
        "  add_executable(ycsb_${protocol}.exe "
        "${CMAKE_SOURCE_DIR}/cc/${protocol}/transaction.cc)\n"
        "  ccbench_universal_definitions(fixture_definitions)\n"
        "  target_compile_definitions(ycsb_${protocol}.exe PRIVATE "
        "${fixture_definitions})\n"
        "endfunction()\n"
        "add_subdirectory(cc/silo)\n",
        encoding="utf-8",
    )
    (root / "cmake" / "Options.cmake").write_text(
        "set(CCBENCH_BACK_OFF 1 CACHE STRING \"\")\n"
        "set(CCBENCH_ADD_ANALYSIS 0 CACHE STRING \"extra per-tx analysis counters\")\n"
        "set(CCBENCH_NO_WAIT_LOCKING_IN_VALIDATION 1 CACHE STRING \"\")\n"
        "set(CCBENCH_NO_WAIT_OF_TICTOC 0 CACHE STRING \"\")\n"
        "set(CCBENCH_WAL 0 CACHE STRING \"\")\n"
        "set(CCBENCH_BACKOFF_TRIGGER_GATING 0 CACHE STRING \"\")\n"
        "set(CCBENCH_TRACE 0 CACHE STRING \"\")\n"
        "function(ccbench_universal_definitions out_var)\n"
        "  set(${out_var}\n"
        "    ADD_ANALYSIS=${CCBENCH_ADD_ANALYSIS}\n"
        "    BACK_OFF=${CCBENCH_BACK_OFF}\n"
        "    NO_WAIT_LOCKING_IN_VALIDATION="
        "${CCBENCH_NO_WAIT_LOCKING_IN_VALIDATION}\n"
        "    NO_WAIT_OF_TICTOC=${CCBENCH_NO_WAIT_OF_TICTOC}\n"
        "    WAL=${CCBENCH_WAL}\n"
        "    BACKOFF_TRIGGER_GATING=${CCBENCH_BACKOFF_TRIGGER_GATING}\n"
        "    TRACE=${CCBENCH_TRACE}\n"
        "    PARENT_SCOPE)\n"
        "endfunction()\n",
        encoding="utf-8",
    )
    (root / "include" / "backoff.hh").write_text(
        "inline void fixture_backoff_header() {}\n", encoding="utf-8",
    )
    (root / "cc" / "mocc" / "CMakeLists.txt").write_text(
        "ccbench_add_protocol(mocc SOURCES transaction.cc WORKLOADS ycsb)\n",
        encoding="utf-8",
    )
    (root / "cc" / "mocc" / "transaction.cc").write_text(
        "int fixture_mocc_source = 0;\n", encoding="utf-8",
    )
    (root / "cc" / "silo" / "CMakeLists.txt").write_text(
        "ccbench_add_protocol(silo SOURCES transaction.cc WORKLOADS ycsb)\n",
        encoding="utf-8",
    )

    silo_source = (
        "#include <initializer_list>\n"
        "#include <cstdint>\n"
        "#include <vector>\n"
        "namespace izanagi_trace {\n"
        "struct FixtureStream {\n"
        "  template <class T> FixtureStream& operator<<(T) { return *this; }\n"
        "};\n"
        "inline FixtureStream stream(int) { return {}; }\n"
        "template <class A, class B>\n"
        "inline void emit_lock_violation(int, int, A, B) {}\n"
        "}\n"
        "struct Backoff { static void backoff(int) {} };\n"
        "static int FLAGS_clocks_per_us = 1;\n"
        "enum class IzanagiAbortReason {\n"
        "  kUnset, kLockConflict, kUpdateAbsent, kReadValiTid,\n"
        "  kReadValiLocked, kNodeVali, kInsertNode, kScanNode\n"
        "};\n"
        "static thread_local IzanagiAbortReason izanagi_abort_reason_ =\n"
        "    IzanagiAbortReason::kUnset;\n"
        "enum class OpType { INSERT };\n"
        "struct Tuple {};\n"
        "struct WriteEntry { OpType op_; int storage_; int key_; Tuple* rcdptr_; };\n"
        "struct Masstree { void remove_value_if_present(int) {} };\n"
        "static Masstree Masstrees[1];\n"
        "static int get_storage(int) { return 0; }\n"
        "static std::uint64_t rdtscp() { return 0; }\n"
        "struct TxExecutor {\n"
        "  std::vector<WriteEntry> write_set_;\n"
        "  std::vector<int> read_set_;\n"
        "  std::vector<int> node_map_;\n"
        "  void gc_records() {}\n"
        "  void abort();\n"
        "};\n"
        + FROZEN_TEMPLATE_ABORT_HEAD_BYTES.decode("utf-8")
        + FROZEN_TEMPLATE_PROLOGUE_BYTES.decode("utf-8")
        + FROZEN_TEMPLATE_BLOCK_BYTES.decode("utf-8")
        + FROZEN_TEMPLATE_EPILOGUE_BYTES.decode("utf-8")
        + "#endif\n}\n"
        "#if TRACE\n"
        "static void fixture_proof_surfaces() {\n"
        "  izanagi_trace::emit_lock_violation(\n"
        "      0, 0, std::initializer_list<int>{}, std::initializer_list<int>{});\n"
        "  izanagi_trace::stream(0) << \"P \";\n"
        "}\n"
        "#endif\n"
        "int main() { TxExecutor tx; tx.abort(); return 0; }\n"
    )
    transaction = root / "cc" / "silo" / "transaction.cc"
    transaction.write_text(silo_source, encoding="utf-8")

    _git(root, "init", "-q")
    _git(root, "config", "user.name", "Izanagi Fixture")
    _git(root, "config", "user.email", "fixture@example.invalid")
    _git(root, "add", ".")
    _git(root, "commit", "-q", "-m", "synthetic silo baseline")
    commit = _git(root, "rev-parse", "HEAD")

    predicate = emit_predicate(TriggerGateIR(_MASK))
    stock_hole = "  izanagi_gate_pass = true;"
    materialized_hole = "  " + predicate
    current = transaction.read_text(encoding="utf-8")
    assert current.count(stock_hole) == 1
    transaction.write_text(
        current.replace(stock_hole, materialized_hole), encoding="utf-8",
    )
    return root, commit, predicate


def _campaign_config(commit: str, *, suffix: str = "primary") -> CampaignConfig:
    return CampaignConfig(
        spec_slug="fixture-origin-physical",
        search_tag="issuer",
        spec_content=f"run_campaign rejected result evidence fixture: {suffix}",
        ccbench_commit=commit,
        search_config={
            "axis": wal.TRIGGER_AXIS,
            "reflux": "on",
            wal.TRIGGER_BINDING_SCHEMA_MARKER_KEY:
                trigger_gate_binding.SCHEMA_VERSION,
            pipeline.SEARCH_CONFIG_VERIFY_KEY:
                pipeline.VERIFY_LEGACY_PLUS_S2,
        },
        trial="fixture-origin-issuer",
    )


def _issued_origin_capability(
        contract_sha256: str,
) -> origin_binding.OriginBindingCapability:
    raw = build_launch_admission_inputs(
        environment_contract_sha256=contract_sha256,
    )
    seal = object()
    capability = origin_binding.OriginBindingCapability(
        authority_blob_sha256=raw["authority_blob_sha256"],
        source_closure_sha256=raw["source_closure_sha256"],
        origin_id=raw["origin_id"],
        cell_key=raw["cell_key"],
        authority_workload=origin_binding.AuthorityWorkload(
            **raw["authority_workload"]
        ),
        axis_semantics_sha256=raw["axis_semantics_sha256"],
        verifier_policy_sha256=raw["verifier_policy_sha256"],
        environment_contract_sha256=contract_sha256,
        campaign_id=raw["campaign_id"],
        trial_workload=raw["trial_workload"],
        measurement_head=raw["measurement_head"],
        store_scope="fixture",
        enforcement_arm="fixture-enforced",
        arm_binding_digest_sha256="d" * 64,
        _seal=seal,
    )
    origin_binding._ISSUED_CAPABILITY_FIELDS[seal] = (
        origin_binding._capability_fields(capability)
    )
    return origin_binding.assert_issued_origin_binding_capability(capability)


def _issuance_context(
        evidence_root: Path,
        contract: env_contract.ExecutionEnvironmentContract,
        *,
        verified_calibration: object | None = None,
        batch_id: str | None = None,
) -> evidence.ResultEvidenceIssuanceContext:
    capability = _issued_origin_capability(contract.contract_sha256)
    origin_record = {
        "authority_blob_sha256": capability.authority_blob_sha256,
        "source_closure_sha256": capability.source_closure_sha256,
        "origin_id": capability.origin_id,
        "cell_key": capability.cell_key,
        "workload": capability.trial_workload,
        "axis_semantics_sha256": capability.axis_semantics_sha256,
        "verifier_policy_sha256": capability.verifier_policy_sha256,
        "environment_contract_sha256": capability.environment_contract_sha256,
    }
    fixture_record = build_result_evidence_record(
        origin_binding=origin_record,
        trial_binding__campaign_id=capability.campaign_id,
        trial_binding__workload=capability.trial_workload,
        **(
            {}
            if batch_id is None
            else {"ledger_member__batch_id": batch_id}
        ),
    )
    member = fixture_record["ledger_member"]
    return evidence.ResultEvidenceIssuanceContext(
        origin_capability=capability,
        evidence_root=evidence_root,
        batch_id=member["batch_id"],
        query_ordinal=member["query_ordinal"],
        iteration_index=member["iteration_index"],
        replicate_ordinal=member["replicate_ordinal"],
        p6_plan=fixture_record["p6_plan"],
        trial_binding=fixture_record["trial_binding"],
        origin_binding=fixture_record["origin_binding"],
        ordered_verifiers=_ORDERED_VERIFIERS,
        expected_record_path=evidence.result_evidence_relative_path(
            fixture_record
        ).as_posix(),
        env_tag=contract.env_tag,
        attestation_mode=contract.attestation_mode,
        verified_calibration=verified_calibration,
    )


def _install_fixture_attestation_probe(
    monkeypatch,
    verified_calibration,
) -> None:
    """Feed a deterministic observation through the real v2 receipt builder."""
    expected = env_attestation.profile_to_dict(
        verified_calibration.attestation_profile
    )
    clock_samples = expected["effective_clock"]["samples_mhz"]
    median_clock = sorted(clock_samples)[len(clock_samples) // 2]
    expected["effective_clock"]["samples_mhz"] = [
        median_clock for _sample in clock_samples
    ]
    del expected["effective_clock"]["tolerance_pct"]
    observed = env_attestation.normalize_observed_profile(expected)
    original = execution_guard.attest_and_build_receipt

    def attest(contract, verified):
        assert verified == verified_calibration
        return original(
            contract,
            verified,
            probe_fn=lambda: observed,
            now_fn=lambda: "2026-09-09T00:00:00Z",
        )

    monkeypatch.setattr(execution_guard, "attest_and_build_receipt", attest)


def _install_fixture_trace_runner(monkeypatch) -> None:
    """Inject only trace production; the executor's real verifier remains selected."""
    original = pipeline._execute_verification_repetition
    trace_files = tuple(sorted(_FIXTURE.glob("trace_*.log")))
    commits = sum(
        line.startswith(b"C ")
        for path in trace_files
        for line in path.read_bytes().splitlines()
    )

    def execute(*args, **kwargs):
        trace_dir = Path(args[1])

        def trace_runner(*_args, **_kwargs):
            for path in trace_files:
                shutil.copyfile(path, trace_dir / path.name)
            return pipeline._TraceRunResult(
                trace_c_lines=commits,
                returncode=0,
                abort_counts=0,
                commit_count_witness=commits,
                batch_commit_count_witness=0,
            )

        return original(*args, **kwargs, trace_runner=trace_runner)

    monkeypatch.setattr(pipeline, "_execute_verification_repetition", execute)


def _candidate_binding() -> trigger_gate_binding.TriggerGateBinding:
    return trigger_gate_binding.TriggerGateBinding(
        mask=_MASK,
        predicate_sha256=trigger_gate_binding.expected_predicate_sha256(_MASK),
        nonce="7" * 64,
        source=None,
    )


def _drive_campaign(
        *,
        root: Path,
        checkout: Path,
        commit: str,
        build_context,
        predicate: str,
        cache_root: Path,
        context: evidence.ResultEvidenceIssuanceContext | None,
        authorization=None,
        contract=None,
        durable_root_policy=None,
        suffix: str = "primary",
        declared_use_class: str = "official",
):
    root.mkdir(exist_ok=True)

    def capability_resolver(resolved):
        return attest_generator_output(
            build_context,
            resolved,
            generator_input_sha256=hashlib.sha256(
                predicate.encode("utf-8")
            ).hexdigest(),
        )

    contract = contract or campaign_fixtures._AUTH_CONTRACT
    authorization = authorization or campaign_fixtures._AUTHORIZATION
    return loop.run_campaign(
        _campaign_config(commit, suffix=suffix),
        [Genome("silo", {
            "BACK_OFF": 1,
            "NO_WAIT_LOCKING_IN_VALIDATION": 1,
            "NO_WAIT_OF_TICTOC": 0,
            "WAL": 0,
            "BACKOFF_TRIGGER_GATING": 1,
        })],
        PerfConfig(records=1, threads=1),
        contract.env_tag,
        contract.clocks_per_us,
        numactl=list(contract.numactl),
        do_bench=False,
        output_root=os.fspath(root),
        ccbench_dir=os.fspath(checkout),
        cache_root=os.fspath(cache_root),
        authorization_contract=authorization,
        build_context=build_context,
        capability_resolver=capability_resolver,
        declared_use_class=declared_use_class,
        trigger_gate_binding=_candidate_binding(),
        result_evidence_context=context,
        durable_root_policy=durable_root_policy,
        log=lambda *_args: None,
    )


def _campaign_files(summary) -> set[str]:
    root = Path(summary.layout_root)
    return {
        path.relative_to(root).as_posix()
        for path in root.rglob("*")
        if path.is_file()
    }


def _result_evidence_files(root: Path) -> set[str]:
    return {
        path.relative_to(root).as_posix()
        for path in root.rglob("*")
        if path.is_file() and "reflux-result-evidence" in path.as_posix()
    }


def _seed_accepted_terminal(
    layout: CampaignLayout,
    genome: Genome,
    variant: str,
    *,
    attempt_id: str,
) -> None:
    contract = campaign_fixtures._AUTH_CONTRACT
    admission = campaign_fixtures._admission_for(genome, "deadbeef")
    receipt = admission.as_wal_receipt()
    candidate = _candidate_binding()
    binding = trigger_gate_binding.TriggerGateBinding(
        mask=candidate.mask,
        predicate_sha256=candidate.predicate_sha256,
        nonce=candidate.nonce,
        source=trigger_gate_binding.SourceBinding(
            src_token=receipt["source"]["src_token"],
            source_bytes_sha256=receipt["source"]["source_bytes_sha256"],
        ),
    )
    commitment = wal.log_trigger_binding(
        layout, variant, contract.env_tag, attempt_id, binding
    )
    propagated = {
        "build_attempt_id": attempt_id,
        "build_admission_receipt_sha256": receipt["receipt_sha256"],
    }
    wal.log(layout, variant, STAGE_BUILD_START, contract.env_tag, {
        "genome": genome.canonical(),
        "src_token": receipt["source"]["src_token"],
        "build_attempt_id": attempt_id,
        "build_admission": receipt,
        "build_admission_receipt_sha256": receipt["receipt_sha256"],
        wal.TRIGGER_BINDING_COMMITMENT_KEY: commitment,
    })
    wal.log(
        layout,
        variant,
        STAGE_BUILD_DONE,
        contract.env_tag,
        dict(propagated),
    )
    campaign_fixtures.commit_receipts.log_receipted_commit(
        layout,
        variant,
        contract.env_tag,
        {
            **propagated,
            "fitness_tps": 100.0,
            "contract_sha256": contract.contract_sha256,
        },
        operation_identity=attempt_id,
    )


def _wal_shape(summary) -> tuple[set[str], set[str]]:
    records = wal.read_records(CampaignLayout(root=summary.layout_root))
    return (
        {record.stage for record in records},
        {key for record in records for key in record.payload},
    )


def _drive_required_campaign(
    *,
    root: Path,
    authorization,
    contract,
    durable_root_policy,
    **kwargs,
):
    (root / "env" / contract.env_tag / "claims").mkdir(
        parents=True, exist_ok=True
    )
    with campaign_fixtures._campaign_reservation_environment():
        return _drive_campaign(
            root=root,
            authorization=authorization,
            contract=contract,
            durable_root_policy=durable_root_policy,
            **kwargs,
        )


@pytest.mark.usefixtures("ratified_enforcement_source")
def test_real_run_campaign_exploration_issues_rejected_record(
        tmp_path: Path, monkeypatch) -> None:
    """A required contract reaches the real verifier-to-resolver mechanism."""
    campaign_fixtures._refresh_certified_writer_authority()
    _install_compiler_aliases(tmp_path, monkeypatch)
    _install_fixture_trace_runner(monkeypatch)
    authorization = env_contract.authorize("pegasus")
    contract = authorization.contract
    verified = env_attestation.load_verified_calibration(contract, _REPO)
    _install_fixture_attestation_probe(monkeypatch, verified)
    checkout, commit, predicate = _synthetic_silo_checkout(tmp_path)
    build_context = build_run_context(generator_id=GeneratorId.S8A_TRIGGER_SWEEP)
    cache_root = tmp_path / "build-cache"

    issued_root = tmp_path / "output"
    issued_root.mkdir()
    context = _issuance_context(
        issued_root,
        contract,
        verified_calibration=verified,
    )
    durable_root_policy = campaign_fixtures._single_process_test_policy(
        issued_root
    )
    issued = _drive_required_campaign(
        root=issued_root,
        authorization=authorization,
        contract=contract,
        durable_root_policy=durable_root_policy,
        checkout=checkout,
        commit=commit,
        build_context=build_context,
        predicate=predicate,
        cache_root=cache_root,
        context=context,
        declared_use_class="exploration",
    )

    assert issued.aborted == 1 and issued.committed == 0
    assert len(issued.results) == 1
    typed = issued.results[0].verify_result
    assert typed is not None
    assert typed.verdict == "non-serializable"
    assert typed.integrity.clean()
    assert typed.total_cycles == len(typed.anomalies) == 1

    record_path = issued_root / context.expected_record_path
    assert record_path.is_file()
    record = evidence.parse_result_evidence_bytes(record_path.read_bytes())
    assert record["physical_result"]["outcome"] == "rejected"
    snapshot = result_to_dict(typed)
    snapshot.pop("trace_dir", None)
    expected_constraint = evidence.witness_class_sha256(
        snapshot["anomalies"][0]
    )
    assert record["physical_result"]["constraint_sha256"] == expected_constraint

    content_root = (
        Path(issued.layout_root)
        / "reports"
        / "reflux-result-evidence-content"
        / "v1"
    )
    content_files = {
        category: tuple((content_root / category).glob("*"))
        for category in (
            "source-wal", "ordered-wal", "execution-provenance",
        )
    }
    assert all(len(paths) == 1 for paths in content_files.values())

    resolved = evidence.resolve_result_evidence(record, evidence_root=issued_root)
    assert issued.layout_root == exploration_campaign_layout(
        issued.campaign_id, os.fspath(issued_root)
    ).root
    layout = ExplorationCampaignLayout(root=issued.layout_root)
    assert Path(layout.namespace_file).is_file()
    attempt = issued.results[0].build_attempt_id
    frames = wal.ordered_attempt_frames(layout, attempt)
    interval = b"".join(frame.raw_bytes for frame in frames)
    source = resolved.ordered_wal.source_wal_ref.raw_bytes
    assert source[
        resolved.ordered_wal.byte_start:resolved.ordered_wal.byte_end
    ] == interval
    assert resolved.ordered_wal.projection_ref.raw_bytes == (
        content_files["ordered-wal"][0].read_bytes()
    )
    assert resolved.execution_provenance_ref.raw_bytes == (
        content_files["execution-provenance"][0].read_bytes()
    )

    assert resolved.ordered_wal.byte_start == frames[0].byte_start
    assert resolved.ordered_wal.byte_end == frames[-1].byte_end
    assert source == content_files["source-wal"][0].read_bytes()
    for ref, category in (
        (resolved.ordered_wal.source_wal_ref, "source-wal"),
        (resolved.ordered_wal.projection_ref, "ordered-wal"),
        (resolved.execution_provenance_ref, "execution-provenance"),
    ):
        assert ref.normalized_path.parent == content_root / category
        assert ref.normalized_path.is_file()


@pytest.mark.usefixtures("ratified_enforcement_source")
def test_real_run_campaign_issues_rejected_record_and_originless_is_inert(
        tmp_path: Path, monkeypatch) -> None:
    """A required contract reaches the real verifier-to-resolver mechanism."""
    campaign_fixtures._refresh_certified_writer_authority()
    _install_compiler_aliases(tmp_path, monkeypatch)
    _install_fixture_trace_runner(monkeypatch)
    authorization = env_contract.authorize("pegasus")
    contract = authorization.contract
    verified = env_attestation.load_verified_calibration(contract, _REPO)
    _install_fixture_attestation_probe(monkeypatch, verified)
    checkout, commit, predicate = _synthetic_silo_checkout(tmp_path)
    build_context = build_run_context(generator_id=GeneratorId.S8A_TRIGGER_SWEEP)
    cache_root = tmp_path / "build-cache"

    issued_root = tmp_path / "output"
    issued_root.mkdir()
    _admit_sandbox_output_root(monkeypatch, issued_root)
    context = _issuance_context(
        issued_root,
        contract,
        verified_calibration=verified,
    )
    durable_root_policy = campaign_fixtures._single_process_test_policy(
        issued_root
    )
    issued = _drive_required_campaign(
        root=issued_root,
        authorization=authorization,
        contract=contract,
        durable_root_policy=durable_root_policy,
        checkout=checkout,
        commit=commit,
        build_context=build_context,
        predicate=predicate,
        cache_root=cache_root,
        context=context,
    )

    assert issued.aborted == 1 and issued.committed == 0
    assert len(issued.results) == 1
    typed = issued.results[0].verify_result
    assert typed is not None
    assert typed.verdict == "non-serializable"
    assert typed.integrity.clean()
    assert typed.total_cycles == len(typed.anomalies) == 1

    record_path = issued_root / context.expected_record_path
    assert record_path.is_file()
    record = evidence.parse_result_evidence_bytes(record_path.read_bytes())
    assert record["physical_result"]["outcome"] == "rejected"
    snapshot = result_to_dict(typed)
    snapshot.pop("trace_dir", None)
    expected_constraint = evidence.witness_class_sha256(
        snapshot["anomalies"][0]
    )
    assert record["physical_result"]["constraint_sha256"] == expected_constraint

    content_root = (
        Path(issued.layout_root)
        / "reports"
        / "reflux-result-evidence-content"
        / "v1"
    )
    content_files = {
        category: tuple((content_root / category).glob("*"))
        for category in (
            "source-wal", "ordered-wal", "execution-provenance",
        )
    }
    assert all(len(paths) == 1 for paths in content_files.values())

    resolved = evidence.resolve_result_evidence(record, evidence_root=issued_root)
    layout = CampaignLayout(root=issued.layout_root)
    attempt = issued.results[0].build_attempt_id
    frames = wal.ordered_attempt_frames(layout, attempt)
    interval = b"".join(frame.raw_bytes for frame in frames)
    source = resolved.ordered_wal.source_wal_ref.raw_bytes
    assert source[
        resolved.ordered_wal.byte_start:resolved.ordered_wal.byte_end
    ] == interval
    assert resolved.ordered_wal.projection_ref.raw_bytes == (
        content_files["ordered-wal"][0].read_bytes()
    )
    assert resolved.execution_provenance_ref.raw_bytes == (
        content_files["execution-provenance"][0].read_bytes()
    )

    before_reissue = _campaign_files(issued)
    with monkeypatch.context() as reentry:
        reentry.setattr(
            loop.campaign_claim,
            "acquire_claim",
            lambda *_args, **_kwargs: None,
        )
        with pytest.raises(evidence.ResultEvidenceIssuanceRefused):
            _drive_required_campaign(
                root=issued_root,
                authorization=authorization,
                contract=contract,
                durable_root_policy=durable_root_policy,
                checkout=checkout,
                commit=commit,
                build_context=build_context,
                predicate=predicate,
                cache_root=cache_root,
                context=context,
            )
    assert _campaign_files(issued) == before_reissue

    collision_context = _issuance_context(
        issued_root,
        contract,
        verified_calibration=verified,
        batch_id="fixture-collision-batch",
    )
    occupied = issued_root / collision_context.expected_record_path
    occupied.parent.mkdir(parents=True)
    occupied.write_bytes(b"occupied\n")
    with pytest.raises(evidence.ResultEvidenceError):
        _drive_required_campaign(
            root=issued_root,
            authorization=authorization,
            contract=contract,
            durable_root_policy=durable_root_policy,
            checkout=checkout,
            commit=commit,
            build_context=build_context,
            predicate=predicate,
            cache_root=cache_root,
            context=collision_context,
            suffix="collision",
        )
    collision_layouts = tuple(
        path for path in (issued_root / "campaigns").iterdir()
        if path != Path(issued.layout_root)
    )
    assert len(collision_layouts) == 1
    collision_records = wal.read_records(
        CampaignLayout(root=os.fspath(collision_layouts[0]))
    )
    assert [record.payload.get("reason") for record in collision_records
            if record.stage == STAGE_ABORT] == ["non-serializable"]


@pytest.mark.usefixtures("ratified_enforcement_source")
def test_originless_campaign_has_legacy_literal_artifact_and_wal_shape(
        tmp_path: Path, monkeypatch) -> None:
    campaign_fixtures._refresh_certified_writer_authority()
    _install_compiler_aliases(tmp_path, monkeypatch)
    _install_fixture_trace_runner(monkeypatch)
    checkout, commit, predicate = _synthetic_silo_checkout(tmp_path)
    root = tmp_path / "originless-output"
    root.mkdir()
    _admit_sandbox_output_root(monkeypatch, root)
    summary = _drive_campaign(
        root=root,
        checkout=checkout,
        commit=commit,
        build_context=build_run_context(
            generator_id=GeneratorId.S8A_TRIGGER_SWEEP
        ),
        predicate=predicate,
        cache_root=tmp_path / "originless-build-cache",
        context=None,
        suffix="originless-literal-baseline",
    )

    assert _campaign_files(summary) == {"campaign.lock", "runs/wal.jsonl"}
    assert _wal_shape(summary) == (
        {
            "abort",
            "build_done",
            "build_start",
            "trigger_binding",
            "verify_done",
        },
        {
            "aborts",
            "anomalies",
            "build_admission",
            "build_admission_receipt_sha256",
            "build_attempt_id",
            "certified",
            "commit_witness",
            "commits",
            "genome",
            "perf_bin",
            "perf_bin_sha256",
            "perf_build_cmd",
            "perf_cached",
            "perf_configure_cmd",
            "proof_surfaces",
            "reason",
            "src_token",
            "trace_bin",
            "trace_bin_sha256",
            "trace_cached",
            "trigger_gate_binding",
            "trigger_gate_binding_commitment",
            "verdict",
            "verify",
            "workload",
        },
    )
    assert not any(
        "reflux-result-evidence" in path.as_posix()
        for path in root.rglob("*")
    )


@pytest.mark.usefixtures("ratified_enforcement_source")
def test_originless_campaign_does_not_evaluate_issuer_only_attributes(
        tmp_path: Path, monkeypatch) -> None:
    campaign_fixtures._refresh_certified_writer_authority()
    root = tmp_path / "originless-sentinels"
    root.mkdir()
    _admit_sandbox_output_root(monkeypatch, root)
    source = SimpleNamespace(
        src_token="sentinel-source",
        source_bytes_sha256="a" * 64,
    )
    monkeypatch.setattr(
        loop.source_digest,
        "resolve_evidence",
        lambda *_args, **_kwargs: source,
    )

    class GuardedAuthorizedContract:
        @property
        def contract_sha256(self):
            raise AssertionError("originless path evaluated contract_sha256")

    class GuardedEvalResult(pipeline.EvalResult):
        def __getattribute__(self, name):
            if name in {"build_attempt_id", "verify_result"}:
                raise AssertionError(
                    f"originless path evaluated EvalResult.{name}"
                )
            return super().__getattribute__(name)

    guarded_result = GuardedEvalResult(
        genome=Genome("silo", {}),
        variant="sentinel-variant",
        certified=False,
        aborted=True,
    )
    monkeypatch.setattr(
        loop,
        "evaluate",
        lambda *_args, **_kwargs: guarded_result,
    )
    original_authorize = loop._authorize_measurement

    def authorize(*args, **kwargs):
        authorized = original_authorize(*args, **kwargs)
        return dataclasses.replace(
            authorized,
            authorized_contract=GuardedAuthorizedContract(),
        )

    monkeypatch.setattr(loop, "_authorize_measurement", authorize)
    monkeypatch.setattr(
        loop.ident,
        "ensure_resumable_wal",
        lambda *_args, **_kwargs: SimpleNamespace(status="clean"),
    )
    monkeypatch.setattr(
        loop.wal,
        "replay",
        lambda *_args, **_kwargs: {},
    )
    summary = loop.run_campaign(
        _campaign_config("0" * 40),
        [guarded_result.genome],
        PerfConfig(records=1, threads=1),
        campaign_fixtures._AUTH_CONTRACT.env_tag,
        campaign_fixtures._AUTH_CONTRACT.clocks_per_us,
        numactl=list(campaign_fixtures._AUTH_CONTRACT.numactl),
        do_bench=False,
        output_root=os.fspath(root),
        authorization_contract=campaign_fixtures._AUTHORIZATION,
        build_context=campaign_fixtures._BUILD_CONTEXT,
        declared_use_class="official",
        trigger_gate_binding=_candidate_binding(),
        result_evidence_context=None,
        log=lambda *_args: None,
    )
    assert summary.results == [guarded_result]


def test_context_shape_rejects_multiple_genomes_and_balanced_before_writes(
        tmp_path: Path) -> None:
    campaign_fixtures._refresh_certified_writer_authority()
    root = tmp_path / "evidence"
    root.mkdir()
    context = _issuance_context(
        root, campaign_fixtures._AUTH_CONTRACT,
    )
    cfg = _campaign_config("0" * 40)
    genome = Genome("silo", {})
    common = (
        cfg, [genome], PerfConfig(records=1, threads=1),
        campaign_fixtures._AUTH_CONTRACT.env_tag,
        campaign_fixtures._AUTH_CONTRACT.clocks_per_us,
    )
    kwargs = {
        "numactl": list(campaign_fixtures._AUTH_CONTRACT.numactl),
        "authorization_contract": campaign_fixtures._AUTHORIZATION,
        "build_context": campaign_fixtures._BUILD_CONTEXT,
        "declared_use_class": "official",
        "output_root": os.fspath(root),
        "result_evidence_context": context,
    }

    with pytest.raises(evidence.ResultEvidenceIssuanceRefused, match="one genome"):
        loop.run_campaign(common[0], [genome, genome], *common[2:], **kwargs)
    schedule = BalancedScheduleConfig(
        workload="fixture", root_seed="1" * 64, arm_names=("a", "b"),
    )
    with pytest.raises(evidence.ResultEvidenceIssuanceRefused, match="balanced"):
        loop.run_campaign(*common, balanced_schedule=schedule, **kwargs)
    assert list(root.iterdir()) == []


def test_validate_result_evidence_context_rejects_multiple_genomes(
    tmp_path: Path,
) -> None:
    campaign_fixtures._refresh_certified_writer_authority()
    context = _issuance_context(tmp_path, campaign_fixtures._AUTH_CONTRACT)
    genome = Genome("silo", {})

    with pytest.raises(
        evidence.ResultEvidenceIssuanceRefused,
        match="exactly one genome",
    ):
        loop._validate_result_evidence_context(
            context,
            genomes=(genome, genome),
            balanced_schedule=None,
        )


def test_validate_result_evidence_context_rejects_balanced_schedule(
    tmp_path: Path,
) -> None:
    campaign_fixtures._refresh_certified_writer_authority()
    context = _issuance_context(tmp_path, campaign_fixtures._AUTH_CONTRACT)
    schedule = BalancedScheduleConfig(
        workload="fixture", root_seed="1" * 64, arm_names=("a", "b")
    )

    with pytest.raises(
        evidence.ResultEvidenceIssuanceRefused,
        match="balanced schedule",
    ):
        loop._validate_result_evidence_context(
            context,
            genomes=(Genome("silo", {}),),
            balanced_schedule=schedule,
        )


@pytest.mark.usefixtures("ratified_enforcement_source")
def test_context_exact_type_and_root_binding_precede_campaign_writes(
        tmp_path: Path, monkeypatch) -> None:
    campaign_fixtures._refresh_certified_writer_authority()
    evidence_root = tmp_path / "evidence"
    evidence_root.mkdir()
    context = _issuance_context(
        evidence_root, campaign_fixtures._AUTH_CONTRACT,
    )
    common = (
        _campaign_config("0" * 40), [Genome("silo", {})],
        PerfConfig(records=1, threads=1),
        campaign_fixtures._AUTH_CONTRACT.env_tag,
        campaign_fixtures._AUTH_CONTRACT.clocks_per_us,
    )
    kwargs = {
        "numactl": list(campaign_fixtures._AUTH_CONTRACT.numactl),
        "authorization_contract": campaign_fixtures._AUTHORIZATION,
        "build_context": campaign_fixtures._BUILD_CONTEXT,
        "declared_use_class": "official",
        "do_bench": False,
        "trigger_gate_binding": _candidate_binding(),
    }

    class ContextSubclass(evidence.ResultEvidenceIssuanceContext):
        pass

    subclass = ContextSubclass(**{
        field.name: getattr(context, field.name)
        for field in dataclasses.fields(context)
    })
    with pytest.raises(TypeError, match="exact ResultEvidenceIssuanceContext"):
        loop.run_campaign(
            *common,
            output_root=os.fspath(evidence_root),
            result_evidence_context=subclass,
            **kwargs,
        )

    missing_context = dataclasses.replace(
        context, evidence_root=tmp_path / "missing-evidence-root",
    )
    with pytest.raises(evidence.ResultEvidenceError, match="existing directory"):
        loop.run_campaign(
            *common,
            output_root=os.fspath(evidence_root),
            result_evidence_context=missing_context,
            **kwargs,
        )

    outside_root = tmp_path / "outside-output"
    _admit_sandbox_output_root(monkeypatch, outside_root)
    with pytest.raises(evidence.ResultEvidenceError, match="outside"):
        loop.run_campaign(
            *common,
            output_root=os.fspath(outside_root),
            result_evidence_context=context,
            **kwargs,
        )
    assert list(evidence_root.iterdir()) == []
    assert not outside_root.exists()


@pytest.mark.usefixtures("ratified_enforcement_source")
@pytest.mark.parametrize("identity_failure", (False, True))
def test_accepted_terminal_recovery_is_refused_without_new_evidence(
        tmp_path: Path, monkeypatch, identity_failure: bool) -> None:
    campaign_fixtures._refresh_certified_writer_authority()
    root = tmp_path / (
        "accepted-identity-skip" if identity_failure else "accepted-skip"
    )
    root.mkdir()
    _admit_sandbox_output_root(monkeypatch, root)
    cfg = _campaign_config(
        "deadbeef",
        suffix=("identity-skip" if identity_failure else "normal-skip"),
    )
    common_kwargs = {
        "numactl": list(campaign_fixtures._AUTH_CONTRACT.numactl),
        "do_bench": False,
        "output_root": os.fspath(root),
        "authorization_contract": campaign_fixtures._AUTHORIZATION,
        "build_context": campaign_fixtures._BUILD_CONTEXT,
        "declared_use_class": "official",
        "trigger_gate_binding": _candidate_binding(),
        "log": lambda *_args: None,
    }
    empty = loop.run_campaign(
        cfg,
        [],
        PerfConfig(records=1, threads=1),
        campaign_fixtures._AUTH_CONTRACT.env_tag,
        campaign_fixtures._AUTH_CONTRACT.clocks_per_us,
        result_evidence_context=None,
        **common_kwargs,
    )
    genome = Genome("silo", {})
    source = campaign_fixtures._source_evidence(genome, "deadbeef")
    variant = pipeline.variant_id(genome, source.src_token)
    _seed_accepted_terminal(
        CampaignLayout(root=empty.layout_root),
        genome,
        variant,
        attempt_id="accepted-terminal-attempt",
    )
    if identity_failure:
        monkeypatch.setattr(
            loop.source_digest,
            "resolve_evidence",
            lambda *_args, **_kwargs: (_ for _ in ()).throw(
                RuntimeError("fixture identity failure")
            ),
        )
    else:
        monkeypatch.setattr(
            loop.source_digest,
            "resolve_evidence",
            lambda *_args, **_kwargs: source,
        )
    context = _issuance_context(root, campaign_fixtures._AUTH_CONTRACT)
    before = _result_evidence_files(root)

    with pytest.raises(
        evidence.ResultEvidenceIssuanceRefused,
        match="existing terminal attempt cannot be reissued",
    ):
        loop.run_campaign(
            cfg,
            [genome],
            PerfConfig(records=1, threads=1),
            campaign_fixtures._AUTH_CONTRACT.env_tag,
            campaign_fixtures._AUTH_CONTRACT.clocks_per_us,
            result_evidence_context=context,
            **common_kwargs,
        )
    assert _result_evidence_files(root) == before == set()


@pytest.mark.usefixtures("ratified_enforcement_source")
def test_identity_error_terminal_is_explicitly_refused(
        tmp_path: Path, monkeypatch) -> None:
    campaign_fixtures._refresh_certified_writer_authority()
    root = tmp_path / "identity-error"
    root.mkdir()
    _admit_sandbox_output_root(monkeypatch, root)
    context = _issuance_context(
        root, campaign_fixtures._AUTH_CONTRACT,
    )
    monkeypatch.setattr(
        loop.source_digest,
        "resolve_evidence",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(
            RuntimeError("fixture identity failure")
        ),
    )

    evidence_before = _result_evidence_files(root)
    with pytest.raises(evidence.ResultEvidenceIssuanceRefused):
        loop.run_campaign(
            _campaign_config("0" * 40), [Genome("silo", {})],
            PerfConfig(records=1, threads=1),
            campaign_fixtures._AUTH_CONTRACT.env_tag,
            campaign_fixtures._AUTH_CONTRACT.clocks_per_us,
            numactl=list(campaign_fixtures._AUTH_CONTRACT.numactl),
            do_bench=False,
            output_root=os.fspath(root),
            authorization_contract=campaign_fixtures._AUTHORIZATION,
            build_context=campaign_fixtures._BUILD_CONTEXT,
            declared_use_class="official",
            trigger_gate_binding=_candidate_binding(),
            result_evidence_context=context,
            log=lambda *_args: None,
        )
    assert _result_evidence_files(root) == evidence_before
    layouts = tuple((root / "campaigns").iterdir())
    assert len(layouts) == 1
    records = wal.read_records(CampaignLayout(root=os.fspath(layouts[0])))
    assert [record.stage for record in records] == [
        trigger_gate_binding.WAL_RECORD_STAGE,
        STAGE_BUILD_START,
        STAGE_ABORT,
    ]
    assert records[-1].payload["reason"] == "identity-error"


@pytest.mark.usefixtures("ratified_enforcement_source")
def test_originless_eval_exception_after_terminal_preserves_legacy_abort(
        tmp_path: Path, monkeypatch) -> None:
    campaign_fixtures._refresh_certified_writer_authority()
    root = tmp_path / "terminal-then-exception"
    root.mkdir()
    _admit_sandbox_output_root(monkeypatch, root)
    source_sha = "a" * 64
    monkeypatch.setattr(
        loop.source_digest,
        "resolve_evidence",
        lambda *_args, **_kwargs: SimpleNamespace(
            src_token="fixture-source", source_bytes_sha256=source_sha,
        ),
    )

    def terminal_then_raise(genome, layout, env_tag, *_args, **kwargs):
        attempt = "terminal-before-eval-exception"
        variant = pipeline.variant_id(genome, kwargs["src_token"])
        supplied = kwargs["trigger_gate_binding"]
        candidate = trigger_gate_binding.TriggerGateBinding(
            mask=supplied.mask,
            predicate_sha256=supplied.predicate_sha256,
            nonce=supplied.nonce,
            source=None,
        )
        commitment = wal.log_trigger_binding(
            layout, variant, env_tag, attempt, candidate,
        )
        wal.log(layout, variant, STAGE_BUILD_START, env_tag, {
            "genome": genome.canonical(),
            "build_attempt_id": attempt,
            wal.TRIGGER_BINDING_COMMITMENT_KEY: commitment,
        })
        wal.log(layout, variant, STAGE_ABORT, env_tag, {
            "reason": "identity-error",
            "build_attempt_id": attempt,
        })
        raise RuntimeError("after terminal")

    monkeypatch.setattr(loop, "evaluate", terminal_then_raise)
    summary = loop.run_campaign(
        _campaign_config("0" * 40), [Genome("silo", {})],
        PerfConfig(records=1, threads=1),
        campaign_fixtures._AUTH_CONTRACT.env_tag,
        campaign_fixtures._AUTH_CONTRACT.clocks_per_us,
        numactl=list(campaign_fixtures._AUTH_CONTRACT.numactl),
        do_bench=False,
        output_root=os.fspath(root),
        authorization_contract=campaign_fixtures._AUTHORIZATION,
        build_context=campaign_fixtures._BUILD_CONTEXT,
        declared_use_class="official",
        trigger_gate_binding=_candidate_binding(),
        result_evidence_context=None,
        log=lambda *_args: None,
    )
    assert summary.evaluated == summary.aborted == 1
    layouts = tuple((root / "campaigns").iterdir())
    records = wal.read_records(CampaignLayout(root=os.fspath(layouts[0])))
    assert [record.stage for record in records] == [
        trigger_gate_binding.WAL_RECORD_STAGE,
        STAGE_BUILD_START,
        STAGE_ABORT,
        STAGE_ABORT,
    ]
    aborts = [record for record in records if record.stage == STAGE_ABORT]
    assert aborts[0].payload["reason"] == "identity-error"
    assert set(aborts[0].payload) == {"reason", "build_attempt_id"}
    assert aborts[1].payload["reason"].startswith(
        "eval-exception: RuntimeError: after terminal"
    )
    assert set(aborts[1].payload) == {"reason"}


@pytest.mark.usefixtures("ratified_enforcement_source")
@pytest.mark.parametrize("attempt_present", (False, True))
def test_context_eval_exception_is_refused_without_result_evidence(
        tmp_path: Path, monkeypatch, attempt_present: bool) -> None:
    campaign_fixtures._refresh_certified_writer_authority()
    authorization = env_contract.authorize("pegasus")
    contract = authorization.contract
    verified = env_attestation.load_verified_calibration(contract, _REPO)
    _install_fixture_attestation_probe(monkeypatch, verified)
    root = tmp_path / (
        "eval-exception-with-attempt"
        if attempt_present else "eval-exception-without-attempt"
    )
    root.mkdir()
    _admit_sandbox_output_root(monkeypatch, root)
    (root / "env" / contract.env_tag / "claims").mkdir(
        parents=True, exist_ok=True
    )
    context = _issuance_context(
        root,
        contract,
        verified_calibration=verified,
    )
    genome = Genome("silo", {})
    source = campaign_fixtures._source_evidence(genome, "deadbeef")
    monkeypatch.setattr(
        loop.source_digest,
        "resolve_evidence",
        lambda *_args, **_kwargs: source,
    )

    def raise_during_evaluate(genome, layout, env_tag, *_args, **kwargs):
        if attempt_present:
            attempt = "eval-exception-active-attempt"
            variant = pipeline.variant_id(genome, kwargs["src_token"])
            supplied = kwargs["trigger_gate_binding"]
            bound = trigger_gate_binding.TriggerGateBinding(
                mask=supplied.mask,
                predicate_sha256=supplied.predicate_sha256,
                nonce=supplied.nonce,
                source=trigger_gate_binding.SourceBinding(
                    src_token=source.src_token,
                    source_bytes_sha256=source.source_bytes_sha256,
                ),
            )
            commitment = wal.log_trigger_binding(
                layout,
                variant,
                env_tag,
                attempt,
                bound,
            )
            admission = campaign_fixtures._admission_for(genome, "deadbeef")
            receipt = admission.as_wal_receipt()
            wal.log(layout, variant, STAGE_BUILD_START, env_tag, {
                "genome": genome.canonical(),
                "src_token": source.src_token,
                "build_attempt_id": attempt,
                "build_admission": receipt,
                "build_admission_receipt_sha256": receipt["receipt_sha256"],
                wal.TRIGGER_BINDING_COMMITMENT_KEY: commitment,
            })
        raise RuntimeError("fixture eval exception")

    monkeypatch.setattr(loop, "evaluate", raise_during_evaluate)
    before = _result_evidence_files(root)
    with campaign_fixtures._campaign_reservation_environment():
        with pytest.raises(evidence.ResultEvidenceIssuanceRefused):
            loop.run_campaign(
                _campaign_config(
                    "deadbeef",
                    suffix=(
                        "eval-exception-attempt"
                        if attempt_present else "eval-exception-no-attempt"
                    ),
                ),
                [genome],
                PerfConfig(records=1, threads=1),
                contract.env_tag,
                contract.clocks_per_us,
                numactl=list(contract.numactl),
                do_bench=False,
                output_root=os.fspath(root),
                authorization_contract=authorization,
                build_context=campaign_fixtures._BUILD_CONTEXT,
                declared_use_class="official",
                trigger_gate_binding=_candidate_binding(),
                result_evidence_context=context,
                durable_root_policy=campaign_fixtures._single_process_test_policy(
                    root
                ),
                log=lambda *_args: None,
            )
    assert _result_evidence_files(root) == before == set()
    layout = next((root / "campaigns").iterdir())
    records = wal.read_records(CampaignLayout(root=os.fspath(layout)))
    abort = [record for record in records if record.stage == STAGE_ABORT][-1]
    assert ("build_attempt_id" in abort.payload) is attempt_present


def test_issuance_rejects_invalid_origin_capability_campaign_id(
        tmp_path: Path) -> None:
    campaign_fixtures._refresh_certified_writer_authority()
    context = _issuance_context(
        tmp_path, campaign_fixtures._AUTH_CONTRACT,
    )
    invalid_capabilities = (
        object(),
        SimpleNamespace(campaign_id=""),
        SimpleNamespace(campaign_id=7),
    )
    for capability in invalid_capabilities:
        invalid_context = dataclasses.replace(
            context, origin_capability=capability,
        )
        with pytest.raises(
            evidence.ResultEvidenceError,
            match="campaign id is absent or invalid",
        ):
            loop._issue_campaign_result_evidence(
                layout=CampaignLayout(root=os.fspath(tmp_path)),
                context=invalid_context,
                build_attempt_id="fixture-attempt",
                verify_result=None,
                campaign_run_identity="fixture-run",
                environment_contract=campaign_fixtures._AUTH_CONTRACT,
                execution_receipt={},
            )


def test_signature_keeps_context_keyword_only_after_verify_fanout_hosts() -> None:
    parameters = inspect.signature(loop.run_campaign).parameters
    names = tuple(parameters)
    assert names[-2:] == ("verify_fanout_hosts", "result_evidence_context")
    context = parameters["result_evidence_context"]
    assert context.kind is inspect.Parameter.KEYWORD_ONLY
    assert context.default is None


if __name__ == "__main__":  # pragma: no cover - plain-runner false-green guard
    raise SystemExit(pytest.main([__file__, "-q", *sys.argv[1:]]))
