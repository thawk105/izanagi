from __future__ import annotations

import ast
import errno
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

import pytest

from orchestrator.campaign import p3_b4_producer_auth_experiment as E
from orchestrator.campaign import p3_b4_raw_record_producer as production_producer
from p3_b4_rogue_producer_support import produce_rogue_artifacts


REPOSITORY_ROOT = Path(__file__).resolve().parents[2]

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
    results = []
    for mutation in E.MUTATIONS:
        for candidate in E.Candidate:
            expected = E.EXPECTED_MATRIX[mutation.mutation_id][candidate]
            baseline = (
                _observation(existing=True, reason="source_rederivation")
                if expected is E.CaseOutcome.BASELINE_REJECTED
                else _observation()
            )
            if expected is E.CaseOutcome.KILLED:
                prototype = _observation(
                    guard=candidate, reason="producer_auth_rejection"
                )
            elif expected is E.CaseOutcome.BASELINE_REJECTED:
                prototype = _observation(
                    existing=True, reason="source_rederivation"
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
                    candidate=candidate,
                    mutation_id=mutation.mutation_id,
                    expected=expected,
                    observed=observed,
                    baseline=baseline,
                    prototype=prototype,
                )
            )
    return tuple(results)


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


def _issuer_probe(tree: Path) -> bool:
    code = (
        "import sys\n"
        "from pathlib import Path\n"
        "from orchestrator.campaign import p3_b4_prerun_issuer as I\n"
        "from test_p3_b4_prerun_issuer import _eligible_attempts, _planned\n"
        "attempts=tuple(_eligible_attempts())\n"
        "try:\n"
        " I.issue_b4_prerun_publication(scheduled_inputs=attempts, "
        "planned_result_artifacts=_planned(attempts, Path(sys.argv[2])), "
        "publication_root=sys.argv[1])\n"
        "except Exception as exc:\n"
        " reason=getattr(getattr(exc, 'reason', None), 'value', None)\n"
        " print(reason or type(exc).__name__)\n"
        "else:\n"
        " print('accepted')\n"
    )
    reason = _subprocess_probe(
        tree,
        code,
        str((tree / ".case-artifacts" / "issuer-publication").resolve()),
        str((tree / ".case-artifacts" / "results").resolve()),
    )
    return reason == "producer_auth_mismatch"


def _assembly_probe(tree: Path) -> bool:
    code = (
        "import sys\n"
        "from pathlib import Path\n"
        "from orchestrator.campaign import p3_b4_prerun_issuer as I\n"
        "from orchestrator.campaign import p3_b4_raw_record_producer as P\n"
        "from test_p3_b4_prerun_issuer import _eligible_attempts, _planned\n"
        "publication_root=Path(sys.argv[1])\n"
        "if publication_root.exists():\n"
        " publication=I.load_b4_prerun_publication(str(publication_root))\n"
        "else:\n"
        " attempts=tuple(_eligible_attempts())\n"
        " publication=I.issue_b4_prerun_publication("
        "scheduled_inputs=attempts, planned_result_artifacts=_planned("
        "attempts, Path(sys.argv[2])), publication_root=str(publication_root))\n"
        "result=P.assemble_b4_raw_analysis(publication=publication)\n"
        "print(result.issues[0].code.value)\n"
    )
    return _subprocess_probe(
        tree,
        code,
        str((tree / ".case-artifacts" / "issuer-publication").resolve()),
        str((tree / ".case-artifacts" / "results").resolve()),
    ) == "producer_auth_mismatch"


def _prepare_frozen_publication(tree: Path) -> None:
    code = (
        "import json\n"
        "import sys\n"
        "from pathlib import Path\n"
        "from test_p3_b4_raw_record_producer import "
        "_build_full_publication_evidence\n"
        "evidence=_build_full_publication_evidence("
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
        str((tree / ".case-artifacts" / "frozen-evidence").resolve()),
        str((tree / ".case-artifacts" / "frozen-state.json").resolve()),
    ) == "prepared"


def _frozen_material_probe(tree: Path, mutation: E.MutationSpec) -> bool:
    code = (
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
        "from p3_b4_rogue_producer_support import produce_rogue_artifacts\n"
        "from test_p3_b4_raw_record_producer import "
        "_build_full_publication_evidence, _Evidence, _PublicationEvidence, "
        "_SharedAdmission, _marked_driver_configs, _publish_full_publication\n"
        "state_path=Path(sys.argv[1])\n"
        "if state_path.exists():\n"
        " value=json.loads(state_path.read_text(encoding='utf-8'))\n"
        " admission=_SharedAdmission("
        "repository=Path(value['admission_repository']), "
        "role_file=Path(value['admission_role_file']), "
        "record_path=Path(value['admission_record_path']))\n"
        " on_cfg,off_cfg=_marked_driver_configs()\n"
        " items=tuple(_Evidence("
        "admission=admission,on_cfg=on_cfg,off_cfg=off_cfg,"
        "on_layout=CampaignLayout(item['on_root']),"
        "off_layout=CampaignLayout(item['off_root']),"
        "on_receipt=Path(item['on_receipt']),"
        "off_receipt=Path(item['off_receipt']),"
        "iteration=item['iteration']) for item in value['evidence'])\n"
        " evidence=_PublicationEvidence("
        "publication=I.load_b4_prerun_publication(value['publication_root']),"
        "evidence=items)\n"
        "else:\n"
        " evidence=_build_full_publication_evidence("
        "Path(sys.argv[2]), terminal='commit')\n"
        "publication, first_assembly=_publish_full_publication("
        "publication=evidence.publication, evidence=evidence.evidence)\n"
        "family=sys.argv[3]\n"
        "judgment=sys.argv[4]\n"
        "if family in {'R','D'}:\n"
        " original_assemble=R.assemble_b4_raw_analysis\n"
        " def rogue_assemble(*, publication):\n"
        "  assembly=original_assemble(publication=publication)\n"
        "  if not isinstance(assembly, P.B4RawAnalysisAssembly):\n"
        "   return assembly\n"
        "  attempt_path=Path(publication.planned_result_artifacts[0].artifact_path)\n"
        "  made=produce_rogue_artifacts("
        "judgment=judgment, attempt_artifact_bytes=attempt_path.read_bytes(), "
        "raw_analysis_bytes=assembly.canonical_bytes, "
        "source_artifact_bytes=assembly.source_artifact_bytes, "
        "output_root=Path(sys.argv[5]))\n"
        "  return P.B4RawAnalysisAssembly("
        "schema_version=assembly.schema_version, "
        "canonical_bytes=made.raw_analysis_bytes, "
        "sha256=E.sha256_bytes(made.raw_analysis_bytes), "
        "source_artifact_bytes=made.source_artifact_bytes, "
        "planned_attempt_artifact_paths=assembly.planned_attempt_artifact_paths)\n"
        " R.assemble_b4_raw_analysis=rogue_assemble\n"
        "admission=evidence.evidence[0].admission\n"
        "with mock.patch.object(C, 'REPOSITORY_ROOT', admission.repository), "
        "mock.patch.object(C, 'ROLE_FILE', admission.role_file):\n"
        " try:\n"
        "  inputs=R._load_and_evaluate(Path(publication.publication_root))\n"
        " except E.ProducerAuthRejection:\n"
        "  print('producer_auth_mismatch')\n"
        " else:\n"
        "  if inputs.analysis_result is None:\n"
        "   issue=inputs.assembly.issues[0]\n"
        "   print('route_rejected:'+issue.code.value+':'+issue.field)\n"
        "  else:\n"
        "   print('accepted')\n"
    )
    outcome = _subprocess_probe(
        tree,
        code,
        str((tree / ".case-artifacts" / "frozen-state.json").resolve()),
        str((tree / ".case-artifacts" / "frozen-evidence").resolve()),
        mutation.family,
        mutation.judgment,
        str(
            (
                tree
                / ".case-artifacts"
                / f"material-rogue-{mutation.mutation_id}"
            ).resolve()
        ),
    )
    assert outcome in {"accepted", "producer_auth_mismatch"}, outcome
    return outcome == "producer_auth_mismatch"


def _raw_rogue_rederivation_probe(
    tree: Path,
    mutation: E.MutationSpec,
) -> bool:
    code = (
        "import sys\n"
        "from pathlib import Path\n"
        "from unittest import mock\n"
        "from orchestrator.campaign import p3_b4_closed_critic as C\n"
        "from orchestrator.campaign import p3_b4_raw_record_producer as P\n"
        "from p3_b4_rogue_producer_support import produce_rogue_artifacts\n"
        "from test_p3_b4_raw_record_producer import "
        "_build_full_publication_evidence, _publish_full_publication\n"
        "evidence=_build_full_publication_evidence("
        "Path(sys.argv[1]), terminal='commit')\n"
        "publication, assembly=_publish_full_publication("
        "publication=evidence.publication, evidence=evidence.evidence)\n"
        "attempt_path=Path(publication.planned_result_artifacts[0].artifact_path)\n"
        "made=produce_rogue_artifacts("
        "judgment=sys.argv[2], attempt_artifact_bytes=attempt_path.read_bytes(), "
        "raw_analysis_bytes=assembly.canonical_bytes, "
        "source_artifact_bytes=assembly.source_artifact_bytes, "
        "output_root=Path(sys.argv[3]))\n"
        "attempt_path.write_bytes(made.attempt_artifact_bytes)\n"
        "admission=evidence.evidence[0].admission\n"
        "with mock.patch.object(C, 'REPOSITORY_ROOT', admission.repository), "
        "mock.patch.object(C, 'ROLE_FILE', admission.role_file):\n"
        " result=P.assemble_b4_raw_analysis(publication=publication)\n"
        "assert isinstance(result, P.B4RawRecordRejection)\n"
        "print(result.issues[0].field)\n"
    )
    return _subprocess_probe(
        tree,
        code,
        str((tree / ".case-artifacts" / "raw-rogue-evidence").resolve()),
        mutation.judgment,
        str(
            (
                tree
                / ".case-artifacts"
                / f"raw-rogue-{mutation.mutation_id}"
            ).resolve()
        ),
    ) == "source_rederivation"


def _produce_rogue_case_files(tree: Path, mutation: E.MutationSpec) -> None:
    attempt, raw, sources = _rogue_inputs()
    produced = produce_rogue_artifacts(
        judgment=mutation.judgment,
        attempt_artifact_bytes=attempt,
        raw_analysis_bytes=raw,
        source_artifact_bytes=sources,
        output_root=(tree / ".case-artifacts" / mutation.mutation_id).resolve(),
    )
    assert produced.attempt_artifact_path.is_file()
    assert produced.raw_analysis_path.is_file()
    assert all(path.is_file() for path in produced.source_artifact_paths)


def _comparison_case_runner(
    tree: Path,
    candidate: E.Candidate,
    mutation: E.MutationSpec,
    prototype_enabled: bool,
) -> E.LayerObservation:
    """Concrete case probe used by the external-scratch comparison test."""

    # C1 always performs issuance in a process that exits before mutation and
    # runs the assembly-side probe in a later process.
    c1_issuer_rejected = False
    if mutation.family == "C1":
        if candidate is E.Candidate.FROZEN_CONSUMER:
            _prepare_frozen_publication(tree)
        else:
            c1_issuer_rejected = _issuer_probe(tree)

    if mutation.family in {"C0", "C1"}:
        producer_path = tree / E.PRODUCER_PATH
        producer_path.write_bytes(
            E.apply_exact_once(producer_path.read_bytes(), mutation)
        )
    elif (
        mutation.family in {"R", "D"}
        and candidate is not E.Candidate.FROZEN_CONSUMER
        and not (
            mutation.family == "R"
            and candidate is E.Candidate.RAW_ASSEMBLY
        )
    ):
        _produce_rogue_case_files(tree, mutation)

    guard_rejected = False
    c1_assembly_rejected = False
    if mutation.family == "C1" and not (
        candidate is E.Candidate.FROZEN_CONSUMER
        or (prototype_enabled and candidate is E.Candidate.RAW_ASSEMBLY)
    ):
        c1_assembly_rejected = _assembly_probe(tree)
    if candidate is E.Candidate.FROZEN_CONSUMER:
        frozen_rejected = _frozen_material_probe(tree, mutation)
        guard_rejected = frozen_rejected if prototype_enabled else False
        if not prototype_enabled:
            assert not frozen_rejected
    elif (
        candidate is E.Candidate.RAW_ASSEMBLY
        and mutation.family == "R"
    ):
        raw_rederivation_rejected = _raw_rogue_rederivation_probe(
            tree, mutation
        )
        assert raw_rederivation_rejected
    elif prototype_enabled:
        if candidate is E.Candidate.ISSUER:
            guard_rejected = (
                c1_issuer_rejected
                if mutation.family == "C1"
                else _issuer_probe(tree)
            )
        elif candidate is E.Candidate.RAW_ASSEMBLY:
            guard_rejected = _assembly_probe(tree)
        else:  # pragma: no cover - Candidate is exhaustive above
            raise AssertionError("unexpected candidate")
    if mutation.family == "C1" and candidate is not E.Candidate.RAW_ASSEMBLY:
        assert not c1_assembly_rejected

    existing_gate_rejected = (
        mutation.family == "R" and candidate is E.Candidate.RAW_ASSEMBLY
    )
    return E.LayerObservation(
        guard_rejected=guard_rejected,
        rejecting_candidate=candidate if guard_rejected else None,
        existing_gate_rejected=existing_gate_rejected,
        reason=(
            "producer_auth_rejection"
            if guard_rejected
            else "source_rederivation"
            if existing_gate_rejected
            else None
        ),
    )


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
        E.EXPECTED_MATRIX[f"R-{judgment}"][E.Candidate.RAW_ASSEMBLY]
        is E.CaseOutcome.BASELINE_REJECTED
        for judgment in ("P", "T", "C")
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
        ["git", "diff", "--exit-code", E.BASE_COMMIT, "--", *protected],
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


@pytest.mark.parametrize("judgment", ["P", "T", "C"])
def test_real_rogue_producer_writes_attempt_raw_and_source_bytes(
    tmp_path: Path,
    judgment: str,
) -> None:
    attempt, raw, sources = _rogue_inputs()
    produced = produce_rogue_artifacts(
        judgment=judgment,
        attempt_artifact_bytes=attempt,
        raw_analysis_bytes=raw,
        source_artifact_bytes=sources,
        output_root=(tmp_path / judgment).resolve(),
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
                "generate_verified_analysis_source_closure_receipt",
                "guard_frozen_consumer",
                "evaluate_b4_artifacts",
            }
        ]
        line = {node.func.id: node.lineno for node in calls}
        assert line["assemble_b4_raw_analysis"] < line[
            "generate_verified_analysis_source_closure_receipt"
        ]
        assert line["generate_verified_analysis_source_closure_receipt"] < line[
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


def test_raw_candidate_rejects_through_real_assembly_callsite(
    tmp_path: Path,
) -> None:
    with E.ScratchTree(
        source_repository=REPOSITORY_ROOT,
        scratch_root=tmp_path / "raw-callsite",
    ) as tree:
        E.prepare_candidate_tree(tree, E.Candidate.RAW_ASSEMBLY)
        mutation = E.MUTATION_BY_ID["C0-P"]
        producer_path = tree / E.PRODUCER_PATH
        producer_path.write_bytes(
            E.apply_exact_once(producer_path.read_bytes(), mutation)
        )
        assert _assembly_probe(tree)


def test_c1_preregistration_requires_two_processes() -> None:
    lines = E.canonical_preregistration_bytes().decode("utf-8").splitlines()
    assert lines[1] == "process: C1 issuance and assembly use separate processes"


def test_comparison_report_is_canonical_and_has_no_volatile_payload() -> None:
    results = _all_expected_results()
    decision = E.decide_candidate(results)
    first = E.canonical_report_bytes(results=results, decision=decision)
    second = E.canonical_report_bytes(
        results=tuple(reversed(results)), decision=decision
    )
    assert first == second
    value = json.loads(first)
    assert value["schema_version"] == E.REPORT_SCHEMA_VERSION
    assert len(value["results"]) == 39
    assert value["decision_input_mutation_ids"] == sorted(
        f"{family}-{judgment}"
        for family in ("C1", "R")
        for judgment in ("P", "T", "C")
    )
    encoded = first.decode("utf-8")
    assert str(REPOSITORY_ROOT) not in encoded
    assert "timestamp" not in encoded
    assert "working_tree" not in encoded


def test_wave_mutation_node_mapping_is_complete_and_one_to_one() -> None:
    assert set(WAVE_MUTATION_NODES) == {f"W{index:02d}" for index in range(1, 10)}
    assert len(set(WAVE_MUTATION_NODES.values())) == 9
    assert all(callable(globals().get(node)) for node in WAVE_MUTATION_NODES.values())


def test_w01_fixed_anchor_accepts_regular_and_rejects_rogue() -> None:
    E.guard_issuer()
    E.guard_frozen_consumer(producer_sha256=E.BASE_PRODUCER_SHA256)
    with pytest.raises(E.ProducerAuthRejection) as caught:
        E.guard_frozen_consumer(producer_sha256="0" * 64)
    assert caught.value.candidate is E.Candidate.FROZEN_CONSUMER


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
    harness = _function(
        (REPOSITORY_ROOT / E.EXPERIMENT_PATH).read_bytes(),
        "run_isolated_cases",
    )
    phases = {
        call.args[-1].value
        for call in ast.walk(harness)
        if isinstance(call, ast.Call)
        and isinstance(call.func, ast.Name)
        and call.func.id == "case_runner"
        and call.args
        and isinstance(call.args[-1], ast.Constant)
        and type(call.args[-1].value) is bool
    }
    assert phases == {False, True}


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
    results = _all_expected_results()
    decision = E.decide_candidate(results)
    counts = dict(decision.incremental_kills)
    assert counts == {
        E.Candidate.ISSUER: 0,
        E.Candidate.RAW_ASSEMBLY: 3,
        E.Candidate.FROZEN_CONSUMER: 3,
    }
    assert decision.leaders == (E.Candidate.RAW_ASSEMBLY,)
    assert not decision.complete_candidate_exists


def test_w07_every_exact_replacement_requires_one_occurrence() -> None:
    source = (REPOSITORY_ROOT / E.PRODUCER_PATH).read_bytes()
    for mutation in E.MUTATIONS:
        if mutation.family not in {"C0", "C1"}:
            continue
        assert source.count(mutation.old_bytes) == 1
        assert mutation.old_bytes != mutation.new_bytes
        assert E.apply_exact_once(source, mutation).count(mutation.new_bytes) >= 1
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
    approved = tmp_path / "mutation-prereg.md"
    approved.write_bytes(E.canonical_preregistration_bytes())
    E.assert_preregistration_matches_registry(approved.read_bytes())

    changed = approved.read_bytes().replace(b"C1-P|C1|P", b"C1-P|C0|P", 1)
    with pytest.raises(E.PreregistrationError, match="rederived mutation content"):
        E.assert_preregistration_matches_registry(changed)
    changed_matrix = approved.read_bytes().replace(
        b"C1-P|SURVIVED|KILLED|KILLED",
        b"C1-P|KILLED|KILLED|KILLED",
        1,
    )
    with pytest.raises(E.PreregistrationError, match="expectation matrix"):
        E.assert_preregistration_matches_registry(changed_matrix)
    harness = _function(
        (REPOSITORY_ROOT / E.EXPERIMENT_PATH).read_bytes(),
        "run_isolated_cases",
    )
    assert "assert_preregistration_matches_registry" in _call_names(harness)


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
        assert not _assembly_probe(tree)


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


def test_full_baseline_and_prototype_comparison_in_external_scratch() -> None:
    """Execute all 78 runs only where the ruled external scratch is writable."""

    if not _external_scratch_is_writable():
        pytest.skip(f"required scratch root is not writable: {E.SCRATCH_ROOT}")
    preregistration = E.SCRATCH_ROOT / f"mutation-prereg-{os.getpid()}.md"
    fd = os.open(preregistration, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    try:
        data = E.canonical_preregistration_bytes()
        view = memoryview(data)
        while view:
            written = os.write(fd, view)
            assert written > 0
            view = view[written:]
    finally:
        os.close(fd)
    try:
        results = E.run_isolated_cases(
            source_repository=REPOSITORY_ROOT,
            preregistration_path=preregistration,
            case_runner=_comparison_case_runner,
        )
        assert len(results) == 13 * 3
        assert all(result.expected is result.observed for result in results)
        decision = E.decide_candidate(results)
        assert decision.leaders == (E.Candidate.RAW_ASSEMBLY,)
        assert not decision.complete_candidate_exists
        report = E.canonical_report_bytes(results=results, decision=decision)
        assert len(json.loads(report)["results"]) == 39
    finally:
        preregistration.unlink(missing_ok=True)


@pytest.mark.parametrize("candidate", list(E.Candidate), ids=lambda item: item.name.lower())
def test_candidate_enabled_producer_29_node_non_regression(
    candidate: E.Candidate,
) -> None:
    """Run the unmodified producer suite with each disposable candidate active."""

    if not _external_scratch_is_writable():
        pytest.skip(f"required scratch root is not writable: {E.SCRATCH_ROOT}")
    before = E.repository_status_bytes(REPOSITORY_ROOT)
    try:
        with E.ScratchTree(source_repository=REPOSITORY_ROOT) as tree:
            E.prepare_candidate_tree(tree, candidate)
            completed = subprocess.run(
                [
                    sys.executable,
                    "tools/run_tests.py",
                    "orchestrator/tests/test_p3_b4_raw_record_producer.py",
                    "-q",
                ],
                cwd=tree,
                env=_scratch_environment(tree),
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
            )
            assert completed.returncode == 0, completed.stdout
            if candidate is E.Candidate.ISSUER:
                issuer_loader = subprocess.run(
                    [
                        sys.executable,
                        "tools/run_tests.py",
                        "orchestrator/tests/test_p3_b4_prerun_issuer.py::"
                        "test_issue_publishes_complete_bundle_and_existing_consumers_reverify",
                        "-q",
                    ],
                    cwd=tree,
                    env=_scratch_environment(tree),
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                )
                assert issuer_loader.returncode == 0, issuer_loader.stdout
            if candidate is E.Candidate.FROZEN_CONSUMER:
                frozen_route = subprocess.run(
                    [
                        sys.executable,
                        "tools/run_tests.py",
                        "orchestrator/tests/test_p3_b4_material_report.py::"
                        "test_normal_path_assembles_binds_evaluates_and_builds_document",
                        "-q",
                    ],
                    cwd=tree,
                    env=_scratch_environment(tree),
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                )
                assert frozen_route.returncode == 0, frozen_route.stdout
    finally:
        E.assert_repository_unchanged(REPOSITORY_ROOT, before)
