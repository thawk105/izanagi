from __future__ import annotations

import argparse
import ast
from dataclasses import replace
import errno
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import time

_MODULE_REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
for _module_path in (
    _MODULE_REPOSITORY_ROOT,
    _MODULE_REPOSITORY_ROOT / "orchestrator/tests",
):
    if str(_module_path) not in sys.path:
        sys.path.insert(0, str(_module_path))

import pytest

from orchestrator.campaign import p3_b4_producer_auth_experiment as E
from orchestrator.campaign import p3_b4_raw_record_producer as production_producer
from p3_b4_rogue_producer_support import (
    install_rogue_planned_attempt,
    produce_rogue_artifacts,
)


REPOSITORY_ROOT = _MODULE_REPOSITORY_ROOT

WAVE_MUTATION_NODES = {
    "W01": "test_w01_fixed_anchor_accepts_regular_and_rejects_rogue",
    "W02": "test_w02_baseline_rejection_is_not_an_incremental_kill",
    "W03": "test_w03_only_the_candidate_guard_can_own_a_kill",
    "W04": "test_w04_main_worktree_status_invariant_detects_change",
    "W05": "test_w05_frozen_predicate_is_digest_equality_only",
    "W06": "test_w06_only_c1_and_r_are_decision_inputs",
    "W07": "test_w07_every_exact_replacement_requires_one_occurrence",
    "W08": "test_w08_preregistration_is_rederived_from_content",
    "W09": "test_w09_pos_1_is_accepted_by_every_candidate",
}


def _observation(
    *,
    guard: E.Candidate | None = None,
    existing: bool = False,
    reason: str | None = None,
) -> E.LayerObservation:
    return E.LayerObservation(
        guard_rejected=guard is not None,
        rejecting_candidate=guard,
        existing_gate_rejected=existing,
        reason=reason,
    )


def _all_expected_results() -> tuple[E.CandidateCaseResult, ...]:
    base_commit = E.resolve_source_head(REPOSITORY_ROOT)
    results = []
    for mutation in E.MUTATIONS:
        for candidate in E.Candidate:
            expected = E.EXPECTED_MATRIX[mutation.mutation_id][candidate]
            baseline = (
                _observation(
                    existing=True,
                    reason="evidence_binding:source_rederivation",
                )
                if expected is E.CaseOutcome.BASELINE_REJECTED
                else _observation()
            )
            if expected is E.CaseOutcome.KILLED:
                prototype = _observation(
                    guard=candidate, reason="producer_auth_mismatch"
                )
            elif expected is E.CaseOutcome.BASELINE_REJECTED:
                prototype = _observation(
                    existing=True,
                    reason="evidence_binding:source_rederivation",
                )
            else:
                prototype = _observation()
            observed = E.classify_case(
                candidate=candidate,
                baseline=baseline,
                prototype=prototype,
            )
            results.append(
                E.CandidateCaseResult(
                    base_commit=base_commit,
                    candidate=candidate,
                    mutation_id=mutation.mutation_id,
                    expected=expected,
                    observed=observed,
                    baseline=baseline,
                    prototype=prototype,
                )
            )
    return tuple(results)


def _all_expected_phase_results() -> tuple[E.CandidatePhaseResult, ...]:
    phases = []
    for result in _all_expected_results():
        for phase, observation in (
            (E.MeasurementPhase.BASELINE, result.baseline),
            (E.MeasurementPhase.PROTOTYPE, result.prototype),
        ):
            phases.append(
                E.CandidatePhaseResult(
                    base_commit=result.base_commit,
                    candidate=result.candidate,
                    mutation_id=result.mutation_id,
                    phase=phase,
                    observation=observation,
                    wall_seconds=1.0,
                )
            )
    return tuple(phases)


def _all_expected_phase_shards() -> list[bytes]:
    results = _all_expected_phase_results()
    return [
        E.canonical_candidate_shard_bytes(
            candidate=candidate,
            phase=phase,
            results=tuple(
                result
                for result in results
                if result.candidate is candidate and result.phase is phase
            ),
            non_regression_passed=(
                True if phase is E.MeasurementPhase.PROTOTYPE else None
            ),
            non_regression_wall_seconds=(
                2.0 if phase is E.MeasurementPhase.PROTOTYPE else None
            ),
        )
        for candidate in E.Candidate
        for phase in E.MeasurementPhase
    ]


def _make_source(*, arm: str, ordinal: int) -> dict[str, object]:
    return {
        "schema_version": "p3-b4-arm-source-artifact/v1",
        "identity": {
            "arm": arm,
            "campaign_id": f"campaign-{ordinal}-{arm}",
            "driver_kind": "base",
            "iteration": ordinal,
            "pair_id": f"pair-{ordinal}",
        },
        "raw": {
            "execution_disposition": "executed",
            "whiteboard_result": "success",
            "terminal_stage": "COMMIT",
            "terminal_reason": None,
            "throughput": 1,
            "treatment_fired": arm == "on",
            "contaminated": False,
            "protocol_ok": True,
        },
        "binding": {},
        "receipt_projection": {},
        "evidence": {},
    }


def _rogue_inputs() -> tuple[bytes, bytes, tuple[bytes, ...]]:
    on = _make_source(arm="on", ordinal=1)
    off = _make_source(arm="off", ordinal=1)
    sources = (
        production_producer._encode_json(on),
        production_producer._encode_json(off),
    )
    attempt = production_producer._encode_json(
        {
            "schema_version": "p3-b4-attempt-result/v1",
            "attempt_id": "attempt-001",
            "block_id": "block-001",
            "assignment_observation": ["on", "off"],
            "arm_sources": [on, off],
        }
    )
    raw = production_producer._encode_json(
        {
            "schema_version": "p3-b4-raw-analysis-records/v1",
            "blocks": [
                {
                    "block_id": "block-001",
                    "reference_tps": 1,
                    "reference_snapshot_hash": "a" * 64,
                    "reference_receipt_hash": "b" * 64,
                    "assignment_observation": ["on", "off"],
                    "arms": [
                        {
                            "arm": "on",
                            "execution_disposition": "executed",
                            "whiteboard_result": "success",
                            "terminal_stage": "COMMIT",
                            "terminal_reason": None,
                            "throughput": 1,
                            "precursor_hash": "c" * 64,
                            "treatment_fired": True,
                            "contaminated": False,
                            "protocol_ok": True,
                            "source_artifact_sha256": hashlib.sha256(
                                sources[0]
                            ).hexdigest(),
                        },
                        {
                            "arm": "off",
                            "execution_disposition": "executed",
                            "whiteboard_result": "success",
                            "terminal_stage": "COMMIT",
                            "terminal_reason": None,
                            "throughput": 1,
                            "precursor_hash": "c" * 64,
                            "treatment_fired": False,
                            "contaminated": False,
                            "protocol_ok": True,
                            "source_artifact_sha256": hashlib.sha256(
                                sources[1]
                            ).hexdigest(),
                        },
                    ],
                }
            ],
        }
    )
    return attempt, raw, sources


def _call_names(function: ast.FunctionDef) -> list[str]:
    names = []
    for node in ast.walk(function):
        if isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name):
                names.append(node.func.id)
            elif isinstance(node.func, ast.Attribute):
                names.append(node.func.attr)
    return names


def _function(source: bytes, name: str) -> ast.FunctionDef:
    tree = ast.parse(source)
    matches = [
        node
        for node in tree.body
        if isinstance(node, ast.FunctionDef) and node.name == name
    ]
    assert len(matches) == 1
    return matches[0]


def _external_scratch_is_writable() -> bool:
    probe = E.SCRATCH_ROOT / f"probe-{os.getpid()}"
    try:
        E.SCRATCH_ROOT.mkdir(parents=True, exist_ok=True)
        probe.mkdir()
        probe.rmdir()
    except OSError as exc:
        if exc.errno in {errno.EROFS, errno.EACCES, errno.EPERM}:
            return False
        raise
    return True


def _scratch_environment(tree: Path) -> dict[str, str]:
    return {
        **os.environ,
        "GIT_OPTIONAL_LOCKS": "0",
        "PYTHONPATH": os.pathsep.join(
            (str(tree), str(tree / "orchestrator/tests"))
        ),
    }


def _subprocess_probe(tree: Path, code: str, *arguments: str) -> str:
    completed = subprocess.run(
        [sys.executable, "-c", code, *arguments],
        cwd=tree,
        env=_scratch_environment(tree),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    if completed.returncode != 0:
        raise AssertionError(
            f"case subprocess rc={completed.returncode}\n"
            f"stdout:\n{completed.stdout}\n"
            f"stderr:\n{completed.stderr}"
        )
    return completed.stdout.strip()


def _prepare_route_state(tree: Path) -> None:
    code = (
        "import json\n"
        "import sys\n"
        "from pathlib import Path\n"
        "import test_p3_b4_raw_record_producer as F\n"
        "evidence=F._build_full_publication_evidence("
        "Path(sys.argv[1]), terminal='commit')\n"
        "admission=evidence.evidence[0].admission\n"
        "value={'publication_root':evidence.publication.publication_root, "
        "'admission_repository':str(admission.repository), "
        "'admission_role_file':str(admission.role_file), "
        "'admission_record_path':str(admission.record_path), "
        "'evidence':[{'on_root':item.on_layout.root, "
        "'off_root':item.off_layout.root, "
        "'on_receipt':str(item.on_receipt), "
        "'off_receipt':str(item.off_receipt), "
        "'iteration':item.iteration} for item in evidence.evidence]}\n"
        "Path(sys.argv[2]).parent.mkdir(parents=True, exist_ok=True)\n"
        "Path(sys.argv[2]).write_text("
        "json.dumps(value,sort_keys=True,separators=(',',':')),encoding='utf-8')\n"
        "print('prepared')\n"
    )
    assert _subprocess_probe(
        tree,
        code,
        str((tree / ".case-artifacts" / "route-evidence").resolve()),
        str((tree / ".case-artifacts" / "route-state.json").resolve()),
    ) == "prepared"


def _route_probe(
    tree: Path,
    candidate: E.Candidate,
    mutation: E.MutationSpec,
) -> E.LayerObservation:
    """Run the real issuer, producer, and material route and preserve rejection."""

    code = (
        "import contextlib\n"
        "import json\n"
        "import sys\n"
        "from pathlib import Path\n"
        "from unittest import mock\n"
        "from orchestrator.campaign import p3_b4_closed_critic as C\n"
        "from orchestrator.campaign import p3_b4_material_report as R\n"
        "from orchestrator.campaign import p3_b4_prerun_issuer as I\n"
        "from orchestrator.campaign import p3_b4_raw_record_producer as P\n"
        "from orchestrator.campaign import p3_b4_producer_auth_experiment as E\n"
        "from orchestrator.campaign.layout import CampaignLayout\n"
        "from p3_b4_rogue_producer_support import "
        "install_rogue_planned_attempt, produce_rogue_artifacts\n"
        "import test_p3_b4_raw_record_producer as F\n"
        "from test_p3_b4_raw_record_producer import "
        "_Evidence, _PublicationEvidence, _SharedAdmission, _assert_write, "
        "_marked_driver_configs, _request\n"
        "production_evaluator=R.evaluate_b4_artifacts\n"
        "def measurement_evaluator(**kwargs):\n"
        " return E.evaluate_with_measurement_floor("
        "evaluator=production_evaluator,evaluator_kwargs=kwargs)\n"
        "def emit(kind, reason=None, candidate=None):\n"
        " print(json.dumps({'kind':kind,'reason':reason,'candidate':candidate},"
        "sort_keys=True,separators=(',',':')))\n"
        " raise SystemExit(0)\n"
        "state_path=Path(sys.argv[1])\n"
        "try:\n"
        " if state_path.exists():\n"
        "  value=json.loads(state_path.read_text(encoding='utf-8'))\n"
        "  admission=_SharedAdmission("
        "repository=Path(value['admission_repository']), "
        "role_file=Path(value['admission_role_file']), "
        "record_path=Path(value['admission_record_path']))\n"
        "  on_cfg,off_cfg=_marked_driver_configs()\n"
        "  items=tuple(_Evidence("
        "admission=admission,on_cfg=on_cfg,off_cfg=off_cfg,"
        "on_layout=CampaignLayout(item['on_root']),"
        "off_layout=CampaignLayout(item['off_root']),"
        "on_receipt=Path(item['on_receipt']),"
        "off_receipt=Path(item['off_receipt']),"
        "iteration=item['iteration']) for item in value['evidence'])\n"
        "  evidence=_PublicationEvidence("
        "publication=I.load_b4_prerun_publication(value['publication_root']),"
        "evidence=items)\n"
        " else:\n"
        "  evidence=F._build_full_publication_evidence("
        "Path(sys.argv[2]), terminal='commit')\n"
        "except I.B4PrerunIssuerError as exc:\n"
        " reason=exc.reason.value\n"
        " emit('guard' if reason=='producer_auth_mismatch' else 'existing',"
        "reason,'issuer' if reason=='producer_auth_mismatch' else None)\n"
        "publication=evidence.publication\n"
        "admission=evidence.evidence[0].admission\n"
        "with contextlib.ExitStack() as stack:\n"
        " stack.enter_context(mock.patch.object(C,'REPOSITORY_ROOT',admission.repository))\n"
        " stack.enter_context(mock.patch.object(C,'ROLE_FILE',admission.role_file))\n"
        " requests=[_request(item,row.attempt_id) for item,row in "
        "zip(evidence.evidence,publication.manifest.rows)]\n"
        " writes=P.publish_b4_attempt_results(publication=publication,requests=requests)\n"
        " for write in writes:\n"
        "  if isinstance(write,P.B4RawRecordRejection):\n"
        "   issue=write.issues[0]\n"
        "   emit('existing',issue.code.value+':'+issue.field)\n"
        "  _assert_write(write)\n"
        " assembly=P.assemble_b4_raw_analysis(publication=publication)\n"
        "if isinstance(assembly,P.B4RawRecordRejection):\n"
        " issue=assembly.issues[0]\n"
        " if issue.code.value=='producer_auth_mismatch':\n"
        "  emit('guard',issue.code.value,'raw_assembly')\n"
        " emit('existing',issue.code.value+':'+issue.field)\n"
        "if not isinstance(assembly,P.B4RawAnalysisAssembly):\n"
        " raise AssertionError('assembly returned an unknown result type')\n"
        "family=sys.argv[3]\n"
        "if family in {'R','D'}:\n"
        " attempt_path=Path(publication.planned_result_artifacts[0].artifact_path)\n"
        " made=produce_rogue_artifacts("
        "judgment=sys.argv[4], attempt_artifact_bytes=attempt_path.read_bytes(), "
        "raw_analysis_bytes=assembly.canonical_bytes, "
        "source_artifact_bytes=assembly.source_artifact_bytes, "
        "output_root=Path(sys.argv[5]), old_bytes=bytes.fromhex(sys.argv[6]), "
        "new_bytes=bytes.fromhex(sys.argv[7]),"
        "rewrite_source_binding=family=='R')\n"
        " if family=='R':\n"
        "  install_rogue_planned_attempt("
        "made,planned_attempt_path=attempt_path)\n"
        "  with mock.patch.object(C,'REPOSITORY_ROOT',admission.repository), "
        "mock.patch.object(C,'ROLE_FILE',admission.role_file):\n"
        "   assembly=P.assemble_b4_raw_analysis(publication=publication)\n"
        "  if isinstance(assembly,P.B4RawRecordRejection):\n"
        "   issue=assembly.issues[0]\n"
        "   if issue.code.value=='producer_auth_mismatch':\n"
        "    emit('guard',issue.code.value,'raw_assembly')\n"
        "   emit('existing',issue.code.value+':'+issue.field)\n"
        "  raise AssertionError('rogue planned attempt artifact was accepted')\n"
        " assembly=P.B4RawAnalysisAssembly("
        "schema_version=assembly.schema_version,canonical_bytes=made.raw_analysis_bytes,"
        "sha256=E.sha256_bytes(made.raw_analysis_bytes),"
        "source_artifact_bytes=assembly.source_artifact_bytes,"
        "planned_attempt_artifact_paths=assembly.planned_attempt_artifact_paths)\n"
        "admission=evidence.evidence[0].admission\n"
        "with mock.patch.object(C, 'REPOSITORY_ROOT', admission.repository), "
        "mock.patch.object(C, 'ROLE_FILE', admission.role_file), "
        "mock.patch.object(R, 'assemble_b4_raw_analysis', return_value=assembly), "
        "mock.patch.object(R, 'evaluate_b4_artifacts', "
        "side_effect=measurement_evaluator):\n"
        " try:\n"
        "  inputs=R._load_and_evaluate(Path(publication.publication_root))\n"
        " except E.ProducerAuthRejection as exc:\n"
        "  emit('guard','producer_auth_mismatch',exc.candidate.value)\n"
        "if isinstance(inputs.assembly,P.B4RawRecordRejection):\n"
        " issue=inputs.assembly.issues[0]\n"
        " emit('existing',issue.code.value+':'+issue.field)\n"
        "if inputs.analysis_result is None:\n"
        " emit('existing','evaluator:result_missing')\n"
        "if inputs.analysis_result.analysis_invalid is not None:\n"
        " reason=E.analysis_invalid_observation_reason("
        "inputs.analysis_result.analysis_invalid.reasons)\n"
        " emit('environment_constant' if "
        "E.is_environment_constant_reason(reason) else 'existing',reason)\n"
        "emit('accepted')\n"
    )
    output = _subprocess_probe(
        tree,
        code,
        str((tree / ".case-artifacts" / "route-state.json").resolve()),
        str((tree / ".case-artifacts" / "route-evidence").resolve()),
        mutation.family,
        mutation.judgment,
        str(
            (
                tree
                / ".case-artifacts"
                / f"rogue-{mutation.mutation_id}"
            ).resolve()
        ),
        mutation.old_bytes.hex(),
        mutation.new_bytes.hex(),
    )
    value = json.loads(output)
    assert set(value) == {"candidate", "kind", "reason"}
    if value["kind"] == "accepted":
        return _observation()
    if value["kind"] == "environment_constant":
        assert type(value["reason"]) is str and value["reason"]
        assert E.is_environment_constant_reason(value["reason"])
        return _observation(reason=value["reason"])
    if value["kind"] == "existing":
        assert type(value["reason"]) is str and value["reason"]
        return _observation(existing=True, reason=value["reason"])
    assert value["kind"] == "guard", value
    rejecting = E.Candidate(value["candidate"])
    assert rejecting is candidate
    return _observation(guard=rejecting, reason=value["reason"])


def _comparison_case_runner(
    tree: Path,
    candidate: E.Candidate,
    mutation: E.MutationSpec,
    prototype_enabled: bool,
) -> E.LayerObservation:
    """Concrete case probe used by the external-scratch comparison test."""

    assert E.measurement_block_count(
        mutation, prototype_enabled=prototype_enabled
    ) == E.REAL_REGIME_BLOCK_COUNT

    if mutation.family == "C1":
        _prepare_route_state(tree)

    if mutation.family in {"C0", "C1"}:
        producer_path = tree / E.PRODUCER_PATH
        producer_path.write_bytes(
            E.apply_exact_once(producer_path.read_bytes(), mutation)
        )
    observation = _route_probe(
        tree,
        candidate,
        mutation,
    )
    if not prototype_enabled:
        assert not observation.guard_rejected
    return observation


def test_expected_matrix_has_twelve_negative_cases_and_pos_1() -> None:
    assert len(E.MUTATIONS) == 13
    assert [item.mutation_id for item in E.MUTATIONS[:-1]] == [
        f"{family}-{judgment}"
        for family in ("C0", "C1", "R", "D")
        for judgment in ("P", "T", "C")
    ]
    assert E.MUTATIONS[-1].mutation_id == "POS-1"
    assert set(E.EXPECTED_MATRIX) == {
        mutation.mutation_id for mutation in E.MUTATIONS
    }
    assert all(
        set(row) == set(E.Candidate)
        for row in E.EXPECTED_MATRIX.values()
    )
    assert all(
        E.EXPECTED_MATRIX[f"R-{judgment}"][candidate]
        is E.CaseOutcome.BASELINE_REJECTED
        for judgment in ("P", "T", "C")
        for candidate in E.Candidate
    )
    assert all(
        E.measurement_block_count(mutation, prototype_enabled=phase) == 201
        for mutation in E.MUTATIONS
        for phase in (False, True)
    )
    assert E.measurement_plan_value() == {
        "comparison_pair_count": 39,
        "phase_count_per_shard": 13,
        "phase_wall_time_field": "results[].wall_seconds",
        "phase_wall_time_unit": "seconds",
        "phases": [phase.value for phase in E.MeasurementPhase],
        "publication_block_count": 201,
        "non_regression_measurements": [
            {
                "candidate": candidate.value,
                "execution_phase": "prototype",
                "node_ids": list(E.non_regression_node_ids(candidate)),
                "producer_node_count": 29,
            }
            for candidate in E.Candidate
        ],
        "required_candidate_phase_shards": [
            {"candidate": candidate.value, "phase": phase.value}
            for candidate in E.Candidate
            for phase in E.MeasurementPhase
        ],
        "shard_unit": "candidate_x_phase",
    }
    assert all(
        E.result_matches_registered_route(result)
        for result in _all_expected_results()
    )


def test_main_worktree_has_no_permanent_prototype_or_pin_change() -> None:
    protected = sorted(
        {
            patch.relative_path
            for patches in E.PROTOTYPE_PATCHES.values()
            for patch in patches
        }
    )
    completed = subprocess.run(
        [
            "git",
            "diff",
            "--exit-code",
            E.resolve_source_head(REPOSITORY_ROOT),
            "--",
            *protected,
        ],
        cwd=REPOSITORY_ROOT,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    assert completed.returncode == 0, completed.stdout.decode("utf-8", "replace")
    assert "observed_producer_sha256" not in (
        REPOSITORY_ROOT / E.PRODUCER_PATH
    ).read_text(encoding="utf-8")


def test_default_scratch_root_is_outside_every_registered_worktree() -> None:
    assert E.SCRATCH_ROOT == Path("/work/1/SFC/tanab/t2103-scratch")
    completed = subprocess.run(
        ["git", "worktree", "list", "--porcelain"],
        cwd=REPOSITORY_ROOT,
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    worktrees = [
        Path(line.removeprefix("worktree ")).resolve()
        for line in completed.stdout.splitlines()
        if line.startswith("worktree ")
    ]
    scratch = E.SCRATCH_ROOT.resolve()
    assert all(
        scratch != worktree
        and worktree not in scratch.parents
        and scratch not in worktree.parents
        for worktree in worktrees
    )


def test_scratch_tree_pins_disk_bytes_and_git_head_to_runtime_head(
    tmp_path: Path,
) -> None:
    resolved = E.resolve_source_head(REPOSITORY_ROOT)
    with E.ScratchTree(
        source_repository=REPOSITORY_ROOT,
        scratch_root=tmp_path / "runtime-head",
    ) as tree:
        head = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=tree,
            check=True,
            stdout=subprocess.PIPE,
            text=True,
        ).stdout.strip()
        blob = subprocess.run(
            ["git", "show", "HEAD:orchestrator/verifier/core.py"],
            cwd=tree,
            check=True,
            stdout=subprocess.PIPE,
        ).stdout
        assert head == resolved
        assert blob == (tree / "orchestrator/verifier/core.py").read_bytes()


@pytest.mark.parametrize("judgment", ["P", "T", "C"])
def test_real_rogue_producer_writes_attempt_raw_and_source_bytes(
    tmp_path: Path,
    judgment: str,
) -> None:
    attempt, raw, sources = _rogue_inputs()
    mutation = E.MUTATION_BY_ID[f"R-{judgment}"]
    produced = produce_rogue_artifacts(
        judgment=judgment,
        attempt_artifact_bytes=attempt,
        raw_analysis_bytes=raw,
        source_artifact_bytes=sources,
        output_root=(tmp_path / judgment).resolve(),
        old_bytes=mutation.old_bytes,
        new_bytes=mutation.new_bytes,
    )

    assert produced.attempt_artifact_path.read_bytes() == produced.attempt_artifact_bytes
    assert produced.raw_analysis_path.read_bytes() == produced.raw_analysis_bytes
    assert tuple(path.read_bytes() for path in produced.source_artifact_paths) == (
        produced.source_artifact_bytes
    )
    assert produced.attempt_artifact_bytes != attempt
    assert produced.raw_analysis_bytes != raw
    assert produced.source_artifact_bytes != sources

    field = {"P": "protocol_ok", "T": "treatment_fired", "C": "contaminated"}[
        judgment
    ]
    expected = {"P": False, "T": False, "C": True}[judgment]
    attempt_value = production_producer._strict_json(
        produced.attempt_artifact_bytes
    )
    assert attempt_value["arm_sources"][0]["raw"][field] is expected
    raw_value = production_producer._strict_json(produced.raw_analysis_bytes)
    assert raw_value["blocks"][0]["arms"][0][field] is expected
    source_value = production_producer._strict_json(
        produced.source_artifact_bytes[0]
    )
    assert source_value["raw"][field] is expected
    assert raw_value["blocks"][0]["arms"][0][
        "source_artifact_sha256"
    ] == hashlib.sha256(produced.source_artifact_bytes[0]).hexdigest()

    d_mutation = E.MUTATION_BY_ID[f"D-{judgment}"]
    post_assembly = produce_rogue_artifacts(
        judgment=judgment,
        attempt_artifact_bytes=attempt,
        raw_analysis_bytes=raw,
        source_artifact_bytes=sources,
        output_root=(tmp_path / f"D-{judgment}").resolve(),
        old_bytes=d_mutation.old_bytes,
        new_bytes=d_mutation.new_bytes,
        rewrite_source_binding=False,
    )
    before_raw = production_producer._strict_json(raw)
    after_raw = production_producer._strict_json(post_assembly.raw_analysis_bytes)
    assert after_raw["blocks"][0]["arms"][0][field] is expected
    assert after_raw["blocks"][0]["arms"][0][
        "source_artifact_sha256"
    ] == before_raw["blocks"][0]["arms"][0]["source_artifact_sha256"]


def test_rogue_producer_is_a_separate_implementation_path() -> None:
    source = (
        REPOSITORY_ROOT / "orchestrator/tests/p3_b4_rogue_producer_support.py"
    ).read_bytes()
    tree = ast.parse(source)
    imported = {
        alias.name
        for node in ast.walk(tree)
        if isinstance(node, (ast.Import, ast.ImportFrom))
        for alias in node.names
    }
    assert not any(
        name.endswith("p3_b4_raw_record_producer") for name in imported
    )
    function = _function(source, "produce_rogue_artifacts")
    calls = _call_names(function)
    assert "_mutated_attempt" in calls
    assert "_mutated_sources" in calls
    assert "_mutated_raw_analysis" in calls
    assert calls.count("_write_exclusive") == 3


def test_each_prototype_patch_anchor_is_unique_and_anchor_is_post_prototype(
    tmp_path: Path,
) -> None:
    assert hashlib.sha256((REPOSITORY_ROOT / E.PRODUCER_PATH).read_bytes()).hexdigest() == (
        E.BASE_PRODUCER_SHA256
    )
    for candidate in E.Candidate:
        with E.ScratchTree(
            source_repository=REPOSITORY_ROOT,
            scratch_root=tmp_path / candidate.name.lower(),
        ) as tree:
            patches = E.PROTOTYPE_PATCHES[candidate]
            E.validate_exact_replacements(tree, patches)
            anchor = E.prepare_candidate_tree(tree, candidate)
            observed = hashlib.sha256(
                (tree / E.PRODUCER_PATH).read_bytes()
            ).hexdigest()
            assert observed == anchor.sha256


def test_prototype_calls_each_guard_once_from_the_fixed_real_callsite(
    tmp_path: Path,
) -> None:
    cases = {
        E.Candidate.ISSUER: (
            "orchestrator/campaign/p3_b4_prerun_issuer.py",
            "issue_b4_prerun_publication",
            "guard_issuer",
        ),
        E.Candidate.RAW_ASSEMBLY: (
            E.PRODUCER_PATH,
            "assemble_b4_raw_analysis",
            "guard_raw_assembly",
        ),
        E.Candidate.FROZEN_CONSUMER: (
            "orchestrator/campaign/p3_b4_material_report.py",
            "_load_and_evaluate",
            "guard_frozen_consumer",
        ),
    }
    for candidate, (relative_path, function_name, guard_name) in cases.items():
        with E.ScratchTree(
            source_repository=REPOSITORY_ROOT,
            scratch_root=tmp_path / candidate.name.lower(),
        ) as tree:
            E.prepare_candidate_tree(tree, candidate)
            function = _function((tree / relative_path).read_bytes(), function_name)
            assert _call_names(function).count(guard_name) == 1


def test_frozen_prototype_uses_material_report_route_and_precedes_evaluator(
    tmp_path: Path,
) -> None:
    with E.ScratchTree(
        source_repository=REPOSITORY_ROOT,
        scratch_root=tmp_path / "frozen",
    ) as tree:
        E.prepare_candidate_tree(tree, E.Candidate.FROZEN_CONSUMER)
        material_source = (
            tree / "orchestrator/campaign/p3_b4_material_report.py"
        ).read_bytes()
        function = _function(material_source, "_load_and_evaluate")
        calls = [
            node
            for node in ast.walk(function)
            if isinstance(node, ast.Call)
            and isinstance(node.func, ast.Name)
            and node.func.id
            in {
                "assemble_b4_raw_analysis",
                "generate_experiment_closure_receipt",
                "guard_frozen_consumer",
                "evaluate_b4_artifacts",
            }
        ]
        line = {node.func.id: node.lineno for node in calls}
        assert line["assemble_b4_raw_analysis"] < line[
            "generate_experiment_closure_receipt"
        ]
        assert line["generate_experiment_closure_receipt"] < line[
            "guard_frozen_consumer"
        ] < line["evaluate_b4_artifacts"]

        analysis_paths = ast.literal_eval(
            next(
                node.value
                for node in ast.parse(
                    (tree / "orchestrator/campaign/p3_b4_analysis_path.py").read_bytes()
                ).body
                if isinstance(node, ast.Assign)
                and any(
                    isinstance(target, ast.Name)
                    and target.id == "_SOURCE_CLOSURE_PATHS"
                    for target in node.targets
                )
            )
        )
        consumer_paths = ast.literal_eval(
            next(
                node.value
                for node in ast.parse(
                    (
                        tree
                        / "orchestrator/campaign/p3_b4_analysis_prereg_consumer.py"
                    ).read_bytes()
                ).body
                if isinstance(node, ast.Assign)
                and any(
                    isinstance(target, ast.Name)
                    and target.id == "_CLOSURE_PATHS"
                    for target in node.targets
                )
            )
        )
        assert analysis_paths == consumer_paths
        assert len(analysis_paths) == 6
        assert analysis_paths[-1] == E.PRODUCER_PATH

        assert b"evaluation_block_count" not in material_source
        helper = _function(
            (tree / E.EXPERIMENT_PATH).read_bytes(),
            "generate_experiment_closure_receipt",
        )
        assert not any(
            isinstance(node, ast.Assign)
            and any(
                isinstance(target, ast.Attribute)
                and target.attr == "EXPECTED_BLOCK_COUNT"
                for target in node.targets
            )
            for node in ast.walk(helper)
        )


def test_measurement_harness_routes_cases_through_real_probe() -> None:
    runner = _function(Path(__file__).read_bytes(), "_comparison_case_runner")
    calls = _call_names(runner)
    assert calls.count("measurement_block_count") == 1
    assert calls.count("_route_probe") == 1
    assert "apply_exact_once" in calls


def test_measurement_supplies_floor_zero_at_the_material_report_evaluator() -> None:
    calls: list[dict[str, object]] = []
    sentinel = object()

    def evaluator(**kwargs: object) -> object:
        calls.append(kwargs)
        return sentinel

    assert E.evaluate_with_measurement_floor(
        evaluator=evaluator,
        evaluator_kwargs={"floor": None, "contract_binding": object()},
    ) is sentinel
    assert len(calls) == 1
    assert calls[0]["floor"] == 0
    assert type(calls[0]["floor"]) is int
    assert E.measurement_evaluator_contract_value() == {
        "floor": 0,
        "floor_domain_error_classification": "ENVIRONMENT_CONSTANT",
        "floor_scope": "experiment_only",
        "production_floor": None,
        "production_floor_availability": "absent",
    }

    route = _function(Path(__file__).read_bytes(), "_route_probe")
    probe_script = next(
        node.value
        for node in ast.walk(route)
        if isinstance(node, ast.Constant)
        and type(node.value) is str
        and "production_evaluator=R.evaluate_b4_artifacts" in node.value
    )
    assert "inputs=R._load_and_evaluate" in probe_script
    assert "side_effect=measurement_evaluator" in probe_script
    assert "E.evaluate_with_measurement_floor" in probe_script


def test_floor_domain_error_is_not_attributed_to_a_candidate() -> None:
    reason = E.analysis_invalid_observation_reason(
        ("floor_domain_error", "block_count_mismatch")
    )
    assert reason == (
        "ENVIRONMENT_CONSTANT:evaluator:analysis_invalid:"
        "reasons=floor_domain_error,block_count_mismatch"
    )
    environment = _observation(reason=reason)
    assert not environment.existing_gate_rejected
    assert not environment.guard_rejected
    for baseline, prototype in (
        (environment, _observation()),
        (_observation(), environment),
    ):
        assert E.classify_case(
            candidate=E.Candidate.ISSUER,
            baseline=baseline,
            prototype=prototype,
        ) is E.CaseOutcome.ENVIRONMENT_CONSTANT

    results = list(_all_expected_results())
    results[0] = replace(
        results[0],
        observed=E.CaseOutcome.ENVIRONMENT_CONSTANT,
        baseline=environment,
    )
    assert not results[0].incremental_kill
    decision = E.decide_candidate(
        results,
        non_regression={candidate: True for candidate in E.Candidate},
    )
    assert not decision.decision_available
    assert "environment_constant_present" in decision.blocking_reasons

    phase_results = [
        result
        for result in _all_expected_phase_results()
        if result.candidate is E.Candidate.ISSUER
        and result.phase is E.MeasurementPhase.BASELINE
    ]
    phase_results[0] = replace(phase_results[0], observation=environment)
    shard = E.canonical_candidate_shard_bytes(
        candidate=E.Candidate.ISSUER,
        phase=E.MeasurementPhase.BASELINE,
        results=phase_results,
        non_regression_passed=None,
        non_regression_wall_seconds=None,
    )
    shard_row = json.loads(shard)["results"][0]
    assert shard_row["classification"] == "ENVIRONMENT_CONSTANT"
    assert shard_row["observation"]["reason"] == reason
    assert not shard_row["observation"]["existing_gate_rejected"]


def test_analysis_invalid_diagnostic_preserves_all_reasons() -> None:
    reason = E.analysis_invalid_observation_reason(
        ("binding_domain_error", "block_count_mismatch")
    )
    assert reason == (
        "evaluator:analysis_invalid:"
        "reasons=binding_domain_error,block_count_mismatch"
    )
    assert not E.is_environment_constant_reason(reason)


def test_report_discloses_measurement_floor_non_guarantee() -> None:
    results = _all_expected_results()
    decision = E.decide_candidate(
        results,
        non_regression={candidate: True for candidate in E.Candidate},
    )
    value = E.comparison_report_value(results=results, decision=decision)
    disclosure = " ".join(value["non_guarantees"])
    for phrase in (
        "measurement supplies floor=0",
        "production route does not currently supply",
        "Production passes floor=None",
        "no authoritative floor artifact has been issued",
        "only when a floor is supplied",
        "not current production behavior",
    ):
        assert phrase in disclosure


def test_c1_preregistration_requires_two_processes() -> None:
    approved = json.loads(
        E.approved_preregistration_path(REPOSITORY_ROOT).read_bytes()
    )
    assert approved["process_model"]["C1"] == (
        "issuance process exits before producer mutation; attempt production "
        "and assembly run in a new process"
    )


def test_comparison_report_is_canonical_and_has_no_volatile_payload() -> None:
    results = _all_expected_results()
    decision = E.decide_candidate(
        results,
        non_regression={candidate: True for candidate in E.Candidate},
    )
    first = E.canonical_report_bytes(results=results, decision=decision)
    second = E.canonical_report_bytes(
        results=tuple(reversed(results)), decision=decision
    )
    assert first == second
    value = json.loads(first)
    assert value["schema_version"] == E.REPORT_SCHEMA_VERSION
    assert value["base_commit"] == E.resolve_source_head(REPOSITORY_ROOT)
    assert len(value["results"]) == 39
    assert value["decision_input_mutation_ids"] == sorted(
        f"{family}-{judgment}"
        for family in ("C1", "R")
        for judgment in ("P", "T", "C")
    )
    encoded = first.decode("utf-8")
    assert {
        item["candidate"]: item["production_file_count"]
        for item in value["change_closures"]
    } == {
        E.Candidate.ISSUER.value: 2,
        E.Candidate.RAW_ASSEMBLY.value: 2,
        E.Candidate.FROZEN_CONSUMER.value: 4,
    }
    assert all(
        "shared runtime experiment module" in item["production_file_count_basis"]
        for item in value["change_closures"]
    )
    non_guarantees = " ".join(value["non_guarantees"])
    for phrase in (
        "other judgment values",
        "arbitrary code mutations",
        "coordinated rewrites",
        "path races",
        "temporary six-member closure with an additional gate",
        "current five-file consumer",
        "production adoption",
    ):
        assert phrase in non_guarantees
    assert str(REPOSITORY_ROOT) not in encoded
    assert "timestamp" not in encoded
    assert "working_tree" not in encoded


def test_wave_mutation_node_mapping_is_complete_and_one_to_one() -> None:
    assert set(WAVE_MUTATION_NODES) == {f"W{index:02d}" for index in range(1, 10)}
    assert len(set(WAVE_MUTATION_NODES.values())) == 9
    assert all(callable(globals().get(node)) for node in WAVE_MUTATION_NODES.values())
    assert {mutant.mutation_id for mutant in E.WAVE_MUTANTS} == {
        f"W{index:02d}" for index in range(1, 9)
    }
    assert all(
        mutant.target_node == WAVE_MUTATION_NODES[mutant.mutation_id]
        for mutant in E.WAVE_MUTANTS
    )
    for mutant in E.WAVE_MUTANTS:
        source = (REPOSITORY_ROOT / mutant.relative_path).read_bytes()
        assert source.count(mutant.old_bytes) == 1
        assert mutant.old_bytes != mutant.new_bytes
        mutated = source.replace(mutant.old_bytes, mutant.new_bytes, 1)
        assert mutated != source
        ast.parse(mutated)


@pytest.mark.parametrize(
    "mutant",
    E.WAVE_MUTANTS,
    ids=lambda item: item.mutation_id.lower(),
)
def test_wave_mutant_kills_exactly_one_registered_node(
    mutant: E.WaveMutant,
    tmp_path: Path,
) -> None:
    """Apply each executable mutant and measure the W01-W08 failing set."""

    with E.ScratchTree(
        source_repository=REPOSITORY_ROOT,
        scratch_root=tmp_path / mutant.mutation_id.lower(),
    ) as tree:
        target = tree / mutant.relative_path
        source = target.read_bytes()
        assert source.count(mutant.old_bytes) == 1
        target.write_bytes(source.replace(mutant.old_bytes, mutant.new_bytes, 1))
        node_ids = [
            "orchestrator/tests/test_p3_b4_producer_auth_experiment.py::"
            + WAVE_MUTATION_NODES[f"W{index:02d}"]
            for index in range(1, 9)
        ]
        completed = subprocess.run(
            [sys.executable, "tools/run_tests.py", *node_ids, "-q", "-rf"],
            cwd=tree,
            env=_scratch_environment(tree),
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
        )
    failed_nodes = set(
        re.findall(
            r"FAILED .*::(test_w[0-9]{2}_[A-Za-z0-9_]+)",
            completed.stdout,
        )
    )
    assert completed.returncode == 1, completed.stdout
    assert failed_nodes == {mutant.target_node}, completed.stdout
    assert "1 failed, 7 passed" in completed.stdout, completed.stdout


def test_w01_fixed_anchor_accepts_regular_and_rejects_rogue(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    repository = tmp_path / "repository"
    producer = repository / E.PRODUCER_PATH
    producer.parent.mkdir(parents=True)
    producer.write_bytes((REPOSITORY_ROOT / E.PRODUCER_PATH).read_bytes())
    monkeypatch.setattr(E, "repository_root_from_module", lambda: repository)
    E.guard_issuer()
    mutation = E.MUTATION_BY_ID["C0-P"]
    producer.write_bytes(E.apply_exact_once(producer.read_bytes(), mutation))
    with pytest.raises(E.ProducerAuthRejection) as caught:
        E.guard_issuer()
    assert caught.value.candidate is E.Candidate.ISSUER


def test_w02_baseline_rejection_is_not_an_incremental_kill() -> None:
    candidate = E.Candidate.RAW_ASSEMBLY
    baseline = _observation(existing=True, reason="source_rederivation")
    prototype = _observation(
        guard=candidate,
        existing=True,
        reason="producer_auth_rejection",
    )
    assert E.classify_case(
        candidate=candidate,
        baseline=baseline,
        prototype=prototype,
    ) is E.CaseOutcome.BASELINE_REJECTED
    report = E.combine_candidate_shards(
        _all_expected_phase_shards(),
        preregistration_data=E.approved_preregistration_path(
            REPOSITORY_ROOT
        ).read_bytes(),
    )
    rows = json.loads(report)["results"]
    r_rows = [row for row in rows if row["mutation_id"].startswith("R-")]
    assert len(r_rows) == 9
    assert all(row["observed"] == "BASELINE_REJECTED" for row in r_rows)
    assert all(not row["incremental_kill"] for row in r_rows)


def test_w03_only_the_candidate_guard_can_own_a_kill() -> None:
    assert E.classify_case(
        candidate=E.Candidate.ISSUER,
        baseline=_observation(),
        prototype=_observation(
            guard=E.Candidate.RAW_ASSEMBLY,
            reason="producer_auth_rejection",
        ),
    ) is E.CaseOutcome.SURVIVED


def test_w04_main_worktree_status_invariant_detects_change(
    tmp_path: Path,
) -> None:
    repository = tmp_path / "repository"
    repository.mkdir()
    subprocess.run(["git", "init", "-q"], cwd=repository, check=True)
    before = E.repository_status_bytes(repository)
    (repository / "unexpected").write_bytes(b"changed")
    with pytest.raises(E.ScratchTreeError, match="status changed"):
        E.assert_repository_unchanged(repository, before)
    harness = _function(
        (REPOSITORY_ROOT / E.EXPERIMENT_PATH).read_bytes(),
        "run_isolated_cases",
    )
    assert "assert_repository_unchanged" in _call_names(harness)


def test_w05_frozen_predicate_is_digest_equality_only() -> None:
    function = _function(
        (REPOSITORY_ROOT / E.EXPERIMENT_PATH).read_bytes(),
        "guard_frozen_consumer",
    )
    comparisons = [node for node in ast.walk(function) if isinstance(node, ast.Compare)]
    assert len(comparisons) == 1
    comparison = comparisons[0]
    assert len(comparison.ops) == 1
    assert isinstance(comparison.ops[0], ast.NotEq)
    assert isinstance(comparison.left, ast.Name)
    assert comparison.left.id == "producer_sha256"
    assert not any(isinstance(node, (ast.In, ast.NotIn)) for node in ast.walk(function))


def test_w06_only_c1_and_r_are_decision_inputs() -> None:
    assert E.DECISION_MUTATION_IDS == frozenset(
        f"{family}-{judgment}"
        for family in ("C1", "R")
        for judgment in ("P", "T", "C")
    )
    assert E.CONTROL_MUTATION_IDS == frozenset(
        {
            "C0-P",
            "C0-T",
            "C0-C",
            "D-P",
            "D-T",
            "D-C",
            "POS-1",
        }
    )
    assert all(
        E.is_decision_input(f"{family}-{judgment}")
        is (family in {"C1", "R"})
        for family in ("C0", "C1", "R", "D")
        for judgment in ("P", "T", "C")
    )
    results = _all_expected_results()
    decision = E.decide_candidate(
        results,
        non_regression={candidate: True for candidate in E.Candidate},
    )
    counts = dict(decision.incremental_kills)
    assert counts == {
        E.Candidate.ISSUER: 0,
        E.Candidate.RAW_ASSEMBLY: 3,
        E.Candidate.FROZEN_CONSUMER: 3,
    }
    assert decision.leaders == (E.Candidate.RAW_ASSEMBLY,)
    assert not decision.complete_candidate_exists


@pytest.mark.parametrize(
    ("variant", "blocking_reason"),
    [
        ("missing", "candidate_mutation_matrix_incomplete"),
        ("duplicate", "duplicate_candidate_mutation_result"),
        ("aborted", "aborted_case_present"),
        ("mismatch", "expected_observed_mismatch"),
    ],
)
def test_decision_is_unavailable_for_incomplete_or_invalid_measurements(
    variant: str,
    blocking_reason: str,
) -> None:
    results = list(_all_expected_results())
    if variant == "missing":
        results.pop()
    elif variant == "duplicate":
        results.append(results[-1])
    elif variant == "aborted":
        results[0] = replace(results[0], observed=E.CaseOutcome.ABORTED)
    else:
        results[0] = replace(results[0], observed=E.CaseOutcome.SURVIVED)
    decision = E.decide_candidate(
        results,
        non_regression={candidate: True for candidate in E.Candidate},
    )
    assert not decision.decision_available
    assert decision.leaders == ()
    assert blocking_reason in decision.blocking_reasons


def test_non_regression_failure_excludes_candidate_from_decision() -> None:
    decision = E.decide_candidate(
        _all_expected_results(),
        non_regression={
            E.Candidate.ISSUER: True,
            E.Candidate.RAW_ASSEMBLY: False,
            E.Candidate.FROZEN_CONSUMER: True,
        },
    )
    assert decision.decision_available
    assert decision.leaders == (E.Candidate.FROZEN_CONSUMER,)
    assert decision.ineligible_candidates == (E.Candidate.RAW_ASSEMBLY,)


def test_w07_every_exact_replacement_requires_one_occurrence() -> None:
    source = (REPOSITORY_ROOT / E.PRODUCER_PATH).read_bytes()
    for mutation in E.MUTATIONS:
        if mutation.family == "POS":
            continue
        assert mutation.old_bytes != mutation.new_bytes
        target = (
            source
            if mutation.family in {"C0", "C1"}
            else E._ARTIFACT_JUDGMENT_OLD
        )
        assert target.count(mutation.old_bytes) == 1
        assert E.apply_exact_once(target, mutation).count(mutation.new_bytes) == 1
    patch = E.ExactPatch(
        E.Candidate.ISSUER,
        "x.py",
        b"anchor",
        b"replacement",
        "test anchor",
        1,
    )
    with pytest.raises(ValueError, match="count is 2"):
        E.apply_exact_once(b"anchor anchor", patch)
    with pytest.raises(ValueError, match="count is 0"):
        E.apply_exact_once(b"absent", patch)


def test_w08_preregistration_is_rederived_from_content(tmp_path: Path) -> None:
    approved = E.approved_preregistration_path(REPOSITORY_ROOT)
    approved_bytes = approved.read_bytes()
    E.assert_preregistration_matches_registry(approved_bytes)
    assert approved_bytes == E.canonical_preregistration_bytes()

    changed = approved_bytes.replace(b'"family":"C1"', b'"family":"C0"', 1)
    with pytest.raises(E.PreregistrationError, match="approved preregistration"):
        E.assert_preregistration_matches_registry(changed)
    changed_matrix = approved_bytes.replace(
        b'"issuer":"SURVIVED"',
        b'"issuer":"KILLED"',
        1,
    )
    with pytest.raises(E.PreregistrationError, match="approved preregistration"):
        E.assert_preregistration_matches_registry(changed_matrix)
    harness = _function(
        (REPOSITORY_ROOT / E.EXPERIMENT_PATH).read_bytes(),
        "run_isolated_cases",
    )
    assert "assert_preregistration_matches_registry" in _call_names(harness)


def test_missing_approved_preregistration_fails_closed(tmp_path: Path) -> None:
    with pytest.raises(
        E.PreregistrationError,
        match="approved preregistration file is unavailable",
    ):
        E.run_isolated_cases(
            source_repository=tmp_path,
            case_runner=lambda *_args: _observation(),
            candidate=E.Candidate.ISSUER,
            phase=E.MeasurementPhase.BASELINE,
            scratch_root=tmp_path / "scratch",
        )


def test_w09_pos_1_is_accepted_by_every_candidate(tmp_path: Path) -> None:
    assert E.EXPECTED_MATRIX["POS-1"] == {
        candidate: E.CaseOutcome.SURVIVED for candidate in E.Candidate
    }
    E.guard_issuer()
    E.guard_frozen_consumer(producer_sha256=E.BASE_PRODUCER_SHA256)
    with E.ScratchTree(
        source_repository=REPOSITORY_ROOT,
        scratch_root=tmp_path / "raw-positive",
    ) as tree:
        E.prepare_candidate_tree(tree, E.Candidate.RAW_ASSEMBLY)
        assert _subprocess_probe(
            tree,
            "from orchestrator.campaign import "
            "p3_b4_producer_auth_experiment as E\n"
            "E.guard_raw_assembly()\n"
            "print('accepted')\n",
        ) == "accepted"
    positive = E.MUTATION_BY_ID["POS-1"]
    assert E.measurement_block_count(
        positive, prototype_enabled=False
    ) == E.REAL_REGIME_BLOCK_COUNT
    assert E.measurement_block_count(
        positive, prototype_enabled=True
    ) == E.REAL_REGIME_BLOCK_COUNT


def test_disposable_tree_mutation_does_not_change_main_worktree(
    tmp_path: Path,
) -> None:
    before = E.repository_status_bytes(REPOSITORY_ROOT)
    scratch_path: Path
    with E.ScratchTree(
        source_repository=REPOSITORY_ROOT,
        scratch_root=tmp_path / "scratch",
    ) as tree:
        scratch_path = tree
        target = tree / E.PRODUCER_PATH
        target.write_bytes(target.read_bytes() + b"\n# disposable mutation\n")
        assert target.read_bytes().endswith(b"# disposable mutation\n")
    assert not scratch_path.exists()
    E.assert_repository_unchanged(REPOSITORY_ROOT, before)


def test_case_failure_records_aborted_and_remaining_cases_continue(
    tmp_path: Path,
) -> None:
    calls: list[tuple[str, E.Candidate, bool]] = []

    def runner(
        _tree: Path,
        candidate: E.Candidate,
        mutation: E.MutationSpec,
        prototype_enabled: bool,
    ) -> E.LayerObservation:
        calls.append((mutation.mutation_id, candidate, prototype_enabled))
        if (
            mutation.mutation_id == "C0-P"
            and candidate is E.Candidate.ISSUER
            and not prototype_enabled
        ):
            raise OSError("volatile absolute path must not enter the report")
        return _observation()

    results = E.run_isolated_cases(
        source_repository=REPOSITORY_ROOT,
        case_runner=runner,
        candidate=E.Candidate.ISSUER,
        phase=E.MeasurementPhase.BASELINE,
        scratch_root=tmp_path / "case-abort",
    )
    assert len(calls) == 13
    assert len(results) == 13
    aborted = [
        result
        for result in results
        if result.observation.reason == "case_aborted:baseline:OSError"
    ]
    assert len(aborted) == 1
    assert "/" not in aborted[0].observation.reason
    assert all(type(result.wall_seconds) is float for result in results)


def _candidate_non_regression(
    candidate: E.Candidate,
    *,
    base_commit: str,
    scratch_root: Path = E.SCRATCH_ROOT,
) -> tuple[bool, str, float]:
    """Return a reportable candidate-specific result for the fixed suites."""

    before = E.repository_status_bytes(REPOSITORY_ROOT)
    outputs: list[str] = []
    started = time.monotonic()
    try:
        with E.ScratchTree(
            source_repository=REPOSITORY_ROOT,
            base_commit=base_commit,
            scratch_root=scratch_root,
        ) as tree:
            E.prepare_candidate_tree(tree, candidate)
            passed = True
            for node_id in E.non_regression_node_ids(candidate):
                completed = subprocess.run(
                    [sys.executable, "tools/run_tests.py", node_id, "-q"],
                    cwd=tree,
                    env=_scratch_environment(tree),
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                )
                outputs.append(completed.stdout)
                if completed.returncode != 0:
                    passed = False
    except Exception as exc:
        return False, f"{type(exc).__name__}", round(
            time.monotonic() - started, 6
        )
    finally:
        E.assert_repository_unchanged(REPOSITORY_ROOT, before)
    return passed, "\n".join(outputs), round(time.monotonic() - started, 6)


def _phase_diagnostic_classification(
    observation: E.LayerObservation,
) -> str:
    if E.is_environment_constant_reason(observation.reason):
        return E.CaseOutcome.ENVIRONMENT_CONSTANT.value
    return "ROUTE_MISMATCH"


def _measure_candidate_phase_shard(
    candidate: E.Candidate,
    phase: E.MeasurementPhase,
    *,
    scratch_root: Path,
) -> tuple[bytes, bool, str]:
    """Run one candidate x phase shard outside pytest collection."""

    results = E.run_isolated_cases(
        source_repository=REPOSITORY_ROOT,
        case_runner=_comparison_case_runner,
        scratch_root=scratch_root,
        candidate=candidate,
        phase=phase,
    )
    assert len(results) == 13
    base_commits = {result.base_commit for result in results}
    assert len(base_commits) == 1
    base_commit = next(iter(base_commits))
    if phase is E.MeasurementPhase.PROTOTYPE:
        passed, output, non_regression_wall_seconds = _candidate_non_regression(
            candidate,
            base_commit=base_commit,
            scratch_root=scratch_root,
        )
    else:
        passed = None
        output = ""
        non_regression_wall_seconds = None
    shard = E.canonical_candidate_shard_bytes(
        candidate=candidate,
        phase=phase,
        results=results,
        non_regression_passed=passed,
        non_regression_wall_seconds=non_regression_wall_seconds,
    )
    route_mismatches = [
        result
        for result in results
        if not E.phase_result_matches_registered_route(result)
    ]
    positive_baseline = next(
        (
            result
            for result in results
            if result.mutation_id == "POS-1"
            and phase is E.MeasurementPhase.BASELINE
        ),
        None,
    )
    positive_baseline_accepted = (
        phase is not E.MeasurementPhase.BASELINE
        or (
            positive_baseline is not None
            and positive_baseline.observation == _observation()
        )
    )
    succeeded = passed is not False and not route_mismatches and (
        positive_baseline_accepted
    )
    diagnostics = []
    if not positive_baseline_accepted:
        if positive_baseline is None:
            diagnostics.append(
                "POS-1 baseline did not reach accepted: "
                f"candidate={candidate.value} reason='observation_missing'"
            )
        else:
            diagnostics.append(
                "POS-1 baseline did not reach accepted: "
                f"candidate={candidate.value} "
                "classification="
                f"{_phase_diagnostic_classification(positive_baseline.observation)} "
                f"reason={positive_baseline.observation.reason!r}"
            )
    diagnostics.extend(
        "phase route mismatch: "
        f"candidate={result.candidate.value} phase={result.phase.value} "
        f"mutation={result.mutation_id} "
        f"classification={_phase_diagnostic_classification(result.observation)} "
        f"reason={result.observation.reason!r}"
        for result in route_mismatches
        if result is not positive_baseline
    )
    if passed is False:
        diagnostics.append("candidate non-regression failed")
        if output:
            diagnostics.append(output)
    return shard, succeeded, "\n".join(diagnostics) + ("\n" if diagnostics else "")


def test_candidate_shards_require_all_39_pairs_before_decision() -> None:
    shards = _all_expected_phase_shards()
    preregistration = E.approved_preregistration_path(REPOSITORY_ROOT).read_bytes()
    with pytest.raises(
        E.ComparisonIntegrityError,
        match="all six candidate phase shards",
    ):
        E.combine_candidate_shards(
            shards[:-1], preregistration_data=preregistration
        )
    report = E.combine_candidate_shards(
        shards, preregistration_data=preregistration
    )
    value = json.loads(report)
    assert len(value["results"]) == 39
    assert value["decision"]["available"]
    assert value["decision"]["leaders"] == [E.Candidate.RAW_ASSEMBLY.value]
    assert not value["decision"]["complete_candidate_exists"]

    for shard in shards:
        shard_value = json.loads(shard)
        assert len(shard_value["results"]) == 13
        assert all(
            type(result["wall_seconds"]) is float
            and result["wall_seconds"] >= 0.0
            for result in shard_value["results"]
        )


def test_pos_1_baseline_must_reach_accepted_before_combination() -> None:
    shards = _all_expected_phase_shards()
    value = json.loads(shards[0])
    positive = next(
        result for result in value["results"] if result["mutation_id"] == "POS-1"
    )
    positive["observation"] = {
        "existing_gate_rejected": True,
        "guard_rejected": False,
        "reason": "evaluator:analysis_invalid",
        "rejecting_candidate": None,
    }
    shards[0] = (
        json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        + "\n"
    ).encode("utf-8")
    with pytest.raises(
        E.ComparisonIntegrityError,
        match=(
            "POS-1 baseline did not reach accepted for issuer: "
            "evaluator:analysis_invalid"
        ),
    ):
        E.combine_candidate_shards(
            shards,
            preregistration_data=E.approved_preregistration_path(
                REPOSITORY_ROOT
            ).read_bytes(),
        )


def test_recorded_comparison_has_39_preregistered_pairs_and_rederived_decision() -> None:
    path = REPOSITORY_ROOT / E.COMPARISON_RELATIVE_PATH
    assert path.is_file(), f"recorded measurement is required: {path}"
    decision = E.assert_recorded_comparison_matches_preregistration(
        path.read_bytes(),
        preregistration_data=E.approved_preregistration_path(
            REPOSITORY_ROOT
        ).read_bytes(),
    )
    assert decision.decision_available
    assert len(decision.incremental_kills) == len(E.Candidate)


def _write_new_artifact(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("xb") as stream:
        stream.write(data)
        stream.flush()
        os.fsync(stream.fileno())


def _measurement_main(arguments: list[str]) -> int:
    parser = argparse.ArgumentParser(
        description="Run and combine sharded T-2103 producer-auth measurements."
    )
    subparsers = parser.add_subparsers(dest="command", required=True)
    measure = subparsers.add_parser("measure-candidate")
    measure.add_argument(
        "--candidate", required=True, choices=[item.value for item in E.Candidate]
    )
    measure.add_argument(
        "--phase",
        required=True,
        choices=[item.value for item in E.MeasurementPhase],
    )
    measure.add_argument("--output", required=True, type=Path)
    measure.add_argument("--scratch-root", type=Path, default=E.SCRATCH_ROOT)
    combine = subparsers.add_parser("combine")
    combine.add_argument("--shard", required=True, action="append", type=Path)
    combine.add_argument("--output", required=True, type=Path)
    parsed = parser.parse_args(arguments)

    if parsed.command == "measure-candidate":
        candidate = E.Candidate(parsed.candidate)
        phase = E.MeasurementPhase(parsed.phase)
        shard, succeeded, diagnostic = _measure_candidate_phase_shard(
            candidate,
            phase,
            scratch_root=parsed.scratch_root,
        )
        _write_new_artifact(parsed.output, shard)
        if not succeeded:
            sys.stderr.write(diagnostic)
            return 1
        return 0

    shard_data = [path.read_bytes() for path in parsed.shard]
    report = E.combine_candidate_shards(
        shard_data,
        preregistration_data=E.approved_preregistration_path(
            REPOSITORY_ROOT
        ).read_bytes(),
    )
    _write_new_artifact(parsed.output, report)
    return 0


if __name__ == "__main__":
    raise SystemExit(_measurement_main(sys.argv[1:]))
