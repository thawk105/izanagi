# -*- coding: utf-8 -*-
"""Phase 3 段 8c 事前登録の実 repository invariant。"""
from __future__ import annotations

import argparse
import ast
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest


HERE = Path(__file__).resolve().parent
ORCHESTRATOR = HERE.parent
ROOT = ORCHESTRATOR.parent
TOOLS = ROOT / "tools"
sys.path.insert(0, str(ORCHESTRATOR.parent))
sys.path.insert(0, str(TOOLS))

import check_docs  # noqa: E402
from orchestrator.campaign import s8b_holdout_freeze  # noqa: E402
from orchestrator.campaign import s8c_preregistration as prereg  # noqa: E402


PREREG_DOC = ROOT / prereg.SOURCE_PATH
GIT_TIMEOUT_SECONDS = 180
CANDIDATE_XDIST_GROUP = pytest.mark.xdist_group("s8c-preregistration-candidate")
WAVE_REQUIRED_PATHS = frozenset(
    {
        prereg.SOURCE_PATH,
        prereg.EVIDENCE_CONTRACT_PATH,
        prereg.EVALUATOR_MODULE_PATH,
        prereg.CORE_MODULE_PATH,
        prereg.PROJECTION_MODULE_PATH,
        "orchestrator/tests/test_s8c_preregistration_core.py",
        "orchestrator/tests/test_s8c_preregistration_invariant.py",
        "orchestrator/tests/test_s8c_preregistration_predicates.py",
        "orchestrator/campaign/s8c_schedule.py",
        "orchestrator/tests/test_s8c_schedule.py",
    }
)
MACHINE_CONTRACT_FUNCTION_CHECKS = frozenset(
    {
        ("C01", "orchestrator/campaign/p3_autonomous_workload_trial.py", "_campaign_for"),
        ("C01", "orchestrator/campaign/p3_autonomous_workload_trial.py", "_descriptor_for"),
        ("C01", "orchestrator/campaign/p3_autonomous_workload_trial.py", "_perf_for"),
        ("C01", "orchestrator/campaign/p3_autonomous_workload_trial.py", "_run_workload"),
        ("C01", "orchestrator/campaign/p3_autonomous_workload_trial.py", "main"),
        ("C01", "orchestrator/campaign/p3_autonomous_workload_trial.py", "run_trial"),
        ("C01", "orchestrator/campaign/s8b_ratified_freeze.py", "load_ratified_freeze"),
        ("C02", "orchestrator/campaign/p3_autonomous_workload_trial.py", "_invocation_namespace"),
        ("C02", "orchestrator/campaign/trial_registry.py", "assert_issued_trial_arm_execution"),
        ("C02", "orchestrator/campaign/trial_registry.py", "assert_issued_trial_binding"),
        ("C02", "orchestrator/campaign/trial_registry.py", "assert_issued_resolved_arm_input"),
        ("C02", "orchestrator/campaign/trial_registry.py", "assert_rederived_trial_arm_execution"),
        ("C02", "orchestrator/campaign/trial_registry.py", "assert_trial_registry_acceptance"),
        ("C02", "orchestrator/campaign/trial_registry.py", "bind_trial_arm"),
        ("C02", "orchestrator/campaign/trial_registry.py", "resolve_arm_input"),
        ("C02", "orchestrator/campaign/trial_registry.py", "_expected_registered_arm_execution_record"),
        ("C02", "orchestrator/campaign/trial_registry.py", "validate_execution_input_descriptor"),
        ("C02", "orchestrator/campaign/trial_registry.py", "assert_execution_digest_chain"),
        ("C02", "orchestrator/campaign/p3_autonomous_workload_trial.py", "_invocation_id"),
        ("C02", "orchestrator/campaign/p3_autonomous_workload_trial.py", "_run_workload"),
        ("C02", "orchestrator/campaign/p3_autonomous_workload_trial.py", "proposal_path"),
        ("C02", "orchestrator/campaign/p3_autonomous_workload_trial.py", "run_trial"),
        ("C04", "orchestrator/campaign/p3_autonomous_workload_trial.py", "main"),
        (
            "C04",
            "orchestrator/campaign/p3_autonomous_workload_trial.py",
            "mark_experiment_indeterminate",
        ),
        ("C04", "orchestrator/campaign/p3_autonomous_workload_trial.py", "run_trial"),
        ("C04", "orchestrator/campaign/trial_registry.py", "forbid_trial_restart"),
        ("C04", "orchestrator/campaign/trial_registry.py", "reject_started_trial"),
        ("C05", "orchestrator/campaign/s8c_schedule.py", "consume_schedule"),
        ("C05", "orchestrator/campaign/s8c_schedule.py", "verify_schedule"),
        ("C07", "orchestrator/campaign/s8c_result_judge.py", "verify_floor_bytes"),
        ("C07", "orchestrator/campaign/s8c_result_judge.py", "judge"),
        ("C07", "orchestrator/campaign/s8c_result_judge.py", "publish_result_table"),
        ("C07", "orchestrator/campaign/s8b_ratified_freeze.py", "load_ratified_freeze"),
        ("C09", "orchestrator/campaign/p3_autonomous_workload_trial.py", "assert_campaign_layer3_chain"),
        ("C09", "orchestrator/campaign/p3_autonomous_workload_trial.py", "main"),
        ("C09", "orchestrator/campaign/trial_registry.py", "assert_trial_registry_acceptance"),
        ("C09", "orchestrator/campaign/p3_autonomous_workload_trial.py", "run_trial"),
        ("C09", "orchestrator/campaign/trial_registry.py", "assert_campaign_layer3_chain"),
        ("C10", "orchestrator/campaign/trial_registry.py", "assert_trial_registry_acceptance"),
        ("C10", "orchestrator/campaign/autonomous_trial_completeness.py", "verify_s8c_cross_binding"),
        ("C10", "orchestrator/campaign/trial_registry.py", "verify_s8c_cross_binding"),
        ("C11", "orchestrator/campaign/p3_autonomous_workload_trial.py", "_run_workload"),
        ("C11", "orchestrator/campaign/p3_autonomous_workload_trial.py", "apply_critic_feedback"),
        ("C11", "orchestrator/campaign/p3_autonomous_workload_trial.py", "main"),
        ("C11", "orchestrator/campaign/p3_autonomous_workload_trial.py", "run_trial"),
        ("C11", "orchestrator/campaign/s8c_generation_projection.py", "_validate_critic_projection"),
        ("C11", "orchestrator/campaign/s8c_generation_projection.py", "apply_critic_feedback"),
        ("C11", "orchestrator/campaign/s8c_generation_projection.py", "validate_planner_payload"),
        ("C12", "orchestrator/campaign/env_contract.py", "lookup"),
        ("C12", "orchestrator/campaign/execution_guard.py", "attest_and_build_receipt"),
        ("C12", "orchestrator/campaign/p3_autonomous_workload_trial.py", "main"),
        ("C12", "orchestrator/campaign/p3_autonomous_workload_trial.py", "run_trial"),
    }
)
MACHINE_CONTRACT_FUNCTION_EXCLUSIONS = frozenset(
    {
        ("C01", "orchestrator/campaign/s8b_ratified_freeze.py", "_run_workload", "different-module-token"),
        ("C01", "orchestrator/campaign/s8b_ratified_freeze.py", "run_trial", "different-module-token"),
        ("C02", "orchestrator/campaign/p3_autonomous_workload_trial.py", "invocation namespace", "non-identifier-token"),
        ("C02", "orchestrator/campaign/p3_autonomous_workload_trial.py", "provider invocation_id", "non-identifier-token"),
        ("C04", "orchestrator/campaign/p3_autonomous_workload_trial.py", "crash handler", "non-identifier-token"),
        ("C04", "orchestrator/campaign/trial_registry.py", "run_trial crash handler", "non-identifier-token"),
        ("C04", "orchestrator/campaign/trial_registry.py", "run_trial preflight", "non-identifier-token"),
        ("C05", "orchestrator/campaign/s8c_schedule.py", "run_trial", "different-module-token"),
        ("C05", "output/s8c-preregistration/schedule.v1.json", "launch next cell", "non-identifier-token"),
        ("C05", "output/s8c-preregistration/schedule.v1.json", "load_schedule", "different-module-token"),
        ("C05", "output/s8c-preregistration/schedule.v1.json", "run_trial", "different-module-token"),
        ("C07", "orchestrator/campaign/s8b_ratified_freeze.py", "verify_floor_bytes", "different-module-token"),
        ("C09", "orchestrator/campaign/p3_autonomous_workload_trial.py", "report publish", "non-identifier-token"),
        ("C09", "orchestrator/campaign/trial_registry.py", "registry append", "non-identifier-token"),
        ("C10", "orchestrator/campaign/autonomous_trial_completeness.py", "assert_trial_registry_acceptance", "different-module-token"),
        ("C10", "orchestrator/campaign/autonomous_trial_completeness.py", "authoritative bytes reread", "non-identifier-token"),
        ("C10", "orchestrator/campaign/trial_registry.py", "registry append", "non-identifier-token"),
        ("C11", "orchestrator/campaign/p3_autonomous_workload_trial.py", "next generation", "non-identifier-token"),
        ("C11", "orchestrator/campaign/s8c_generation_projection.py", "AppliedCriticFeedback.planner_projection", "non-identifier-token"),
        ("C12", "orchestrator/campaign/env_contract.py", "attestation consumer", "non-identifier-token"),
        ("C12", "orchestrator/campaign/env_contract.py", "run_trial", "different-module-token"),
        ("C12", "orchestrator/campaign/execution_guard.py", "campaign launch", "non-identifier-token"),
        ("C12", "orchestrator/campaign/execution_guard.py", "run_trial", "different-module-token"),
        ("C12", "orchestrator/campaign/p3_autonomous_workload_trial.py", "campaign launch", "non-identifier-token"),
        ("C12", "orchestrator/campaign/p3_autonomous_workload_trial.py", "env_contract.lookup", "non-identifier-token"),
        ("C12", "orchestrator/campaign/p3_autonomous_workload_trial.py", "execution_guard.attest_and_build_receipt", "non-identifier-token"),
        ("C12", "orchestrator/campaign/p3_autonomous_workload_trial.py", "reservation.check_reservation", "non-identifier-token"),
        ("C12", "orchestrator/campaign/p3_autonomous_workload_trial.py", "reservation.read_binding", "non-identifier-token"),
        ("C12", "orchestrator/campaign/reservation.py", "campaign launch", "non-identifier-token"),
        ("C12", "orchestrator/campaign/reservation.py", "reservation.check_reservation", "non-identifier-token"),
        ("C12", "orchestrator/campaign/reservation.py", "reservation.read_binding", "non-identifier-token"),
        ("C12", "orchestrator/campaign/reservation.py", "run_trial", "different-module-token"),
    }
)
_DECLARED_UNIMPLEMENTED_CONTRACT_FUNCTIONS = frozenset(
    (condition, path, name)
    for condition, path, name, reason in MACHINE_CONTRACT_FUNCTION_EXCLUSIONS
    if reason == "declared-unimplemented-token"
)


def _git_text(
    *args: str,
    root: Path = ROOT,
    env: dict[str, str] | None = None,
    input_text: str | None = None,
) -> str:
    command = ["git", *args]
    try:
        result = subprocess.run(
            command,
            cwd=root,
            check=True,
            text=True,
            env=env,
            input=input_text,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=GIT_TIMEOUT_SECONDS,
        )
    except subprocess.TimeoutExpired:
        pytest.fail(
            f"git command timed out after {GIT_TIMEOUT_SECONDS}s: {command!r}",
            pytrace=False,
        )
    except subprocess.CalledProcessError as exc:
        pytest.fail(
            f"git command failed with exit code {exc.returncode}: {command!r}\n"
            f"stderr: {exc.stderr}",
            pytrace=False,
        )
    return result.stdout.strip()


def _candidate_commit(tmp_path: Path, *, root: Path = ROOT) -> str:
    """実 index を変えず、HEAD + index/worktree の候補 commit を合成する。"""
    index = tmp_path / "candidate.index"
    env = os.environ.copy()
    env.update(
        {
            "GIT_INDEX_FILE": str(index),
            "GIT_AUTHOR_NAME": "s8c invariant fixture",
            "GIT_AUTHOR_EMAIL": "s8c-invariant@example.invalid",
            "GIT_COMMITTER_NAME": "s8c invariant fixture",
            "GIT_COMMITTER_EMAIL": "s8c-invariant@example.invalid",
        }
    )
    _git_text("read-tree", "HEAD", root=root, env=env)
    _git_text("add", "-A", "--", root=root, env=env)
    tree = _git_text("write-tree", root=root, env=env)
    return _git_text(
        "commit-tree",
        tree,
        "-p",
        "HEAD",
        root=root,
        env=env,
        input_text="s8c invariant candidate\n",
    )


def _commit_paths(commit: str, *, root: Path = ROOT) -> set[str]:
    return set(
        _git_text("ls-tree", "-r", "--name-only", commit, root=root).splitlines()
    )


def _wave_paths(paths: set[str]) -> set[str]:
    return {
        path
        for path in paths
        if path in WAVE_REQUIRED_PATHS
        or path.startswith(f"{prereg.FREEZE_DIR}/")
    }


def _machine_contract_function_findings(
    value: dict[str, object],
) -> tuple[
    frozenset[tuple[str, str, str]],
    frozenset[tuple[str, str, str, str]],
    frozenset[tuple[str, str, str]],
]:
    checked: set[tuple[str, str, str]] = set()
    excluded: set[tuple[str, str, str, str]] = set()
    missing: set[tuple[str, str, str]] = set()
    function_names_by_path: dict[str, frozenset[str]] = {}
    symbol_names_by_path: dict[str, frozenset[str]] = {}

    def parse_module(path: str) -> None:
        if path not in symbol_names_by_path:
            if not path.endswith(".py"):
                function_names_by_path[path] = frozenset()
                symbol_names_by_path[path] = frozenset()
                return
            tree = ast.parse((ROOT / path).read_bytes(), filename=path)
            function_names_by_path[path] = frozenset(
                node.name
                for node in tree.body
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
            )
            symbols = set(function_names_by_path[path])
            for node in ast.walk(tree):
                if isinstance(node, ast.Name):
                    symbols.add(node.id)
                elif isinstance(node, ast.Attribute):
                    symbols.add(node.attr)
                elif isinstance(node, (ast.Import, ast.ImportFrom)):
                    symbols.update(
                        alias.asname or alias.name.rsplit(".", 1)[-1]
                        for alias in node.names
                    )
            symbol_names_by_path[path] = frozenset(symbols)

    def classify(
        identifier: str,
        path: str,
        name: str,
        *,
        entrypoint: bool = False,
    ) -> None:
        key = (identifier, path, name)
        parse_module(path)
        if entrypoint:
            if name in function_names_by_path[path]:
                checked.add(key)
            else:
                missing.add(key)
            return
        if not name.isidentifier():
            excluded.add((*key, "non-identifier-token"))
        elif key in _DECLARED_UNIMPLEMENTED_CONTRACT_FUNCTIONS:
            excluded.add((*key, "declared-unimplemented-token"))
        elif name in symbol_names_by_path[path]:
            checked.add(key)
        elif any(
            name in symbols
            for other_path, symbols in symbol_names_by_path.items()
            if other_path != path
        ):
            excluded.add((*key, "different-module-token"))
        else:
            missing.add(key)

    conditions = value["conditions"]
    assert isinstance(conditions, list)
    module_paths: set[str] = set()
    for row in conditions:
        assert isinstance(row, dict)
        if row["machine_checkable"] is not True:
            continue
        consumer = row["consumer_requirement"]
        assert isinstance(consumer, dict)
        consumer_path = consumer["path"]
        assert isinstance(consumer_path, str)
        module_paths.add(consumer_path)
        required_evidence = row["required_evidence"]
        assert isinstance(required_evidence, list)
        for evidence in required_evidence:
            assert isinstance(evidence, dict)
            path = evidence["path"]
            assert isinstance(path, str)
            module_paths.add(path)
    for path in module_paths:
        parse_module(path)

    for row in conditions:
        assert isinstance(row, dict)
        if row["machine_checkable"] is not True:
            continue
        identifier = f"C{row['condition_number']:02d}"
        consumer = row["consumer_requirement"]
        assert isinstance(consumer, dict)
        consumer_path = consumer["path"]
        assert isinstance(consumer_path, str)
        for name in consumer["entrypoints"]:
            assert isinstance(name, str)
            classify(identifier, consumer_path, name, entrypoint=True)
        required_evidence = row["required_evidence"]
        assert isinstance(required_evidence, list)
        for evidence in required_evidence:
            assert isinstance(evidence, dict)
            path = evidence["path"]
            assert isinstance(path, str)
            for chain in evidence["reachable_from"]:
                assert isinstance(chain, str)
                tokens = chain.split(" -> ")
                assert tokens and all(tokens)
                for token in tokens:
                    classify(identifier, path, token)

    return frozenset(checked), frozenset(excluded), frozenset(missing)


def _assert_machine_contract_function_pins(
    value: dict[str, object],
    *,
    excluded_pin: frozenset[tuple[str, str, str, str]],
) -> None:
    checked, excluded, missing = _machine_contract_function_findings(value)
    assert checked == MACHINE_CONTRACT_FUNCTION_CHECKS
    assert excluded == excluded_pin
    assert missing == frozenset()


@pytest.fixture(scope="session")
def repository_candidate_commit(tmp_path_factory: pytest.TempPathFactory) -> str:
    """実 repository の候補 commit を session 内で一度だけ合成する。"""
    return _candidate_commit(tmp_path_factory.mktemp("s8c-candidate"))


@CANDIDATE_XDIST_GROUP
def test_candidate_freeze_matches_contract_and_generation_chain(
    repository_candidate_commit: str,
) -> None:
    """g1 発行前は意図的に赤。未 commit 差分を含む同じ履歴性質を検査する。"""

    candidate = repository_candidate_commit
    validation = prereg.validate_condition_freeze_at(ROOT, candidate)
    head_paths = _commit_paths(candidate)
    legacy_prefix = "output/s8c-preregistration/condition-freeze.v1.g"
    assert not any(path.startswith(legacy_prefix) for path in head_paths)
    generation_numbers = sorted(
        int(match.group(1))
        for path in head_paths
        if (match := prereg._GENERATION_RE.fullmatch(path)) is not None
    )
    assert generation_numbers == list(range(1, validation.generation_number + 1))
    assert validation.generation_number == generation_numbers[-1]

    latest_raw = prereg.read_blob_at(
        ROOT,
        validation.commit,
        prereg.generation_path(validation.generation_number),
    )
    assert latest_raw is not None
    latest = json.loads(latest_raw)
    assert latest["protected_sha256"] == validation.protected_sha256
    assert latest["section5_field_names_sha256"] == validation.contract.section5_field_names_sha256
    assert latest["section6_conditions_sha256"] == validation.contract.section6_conditions_sha256
    assert latest["normative_body_sha256"] == validation.contract.normative_body_sha256
    evidence_raw = prereg.read_blob_at(
        ROOT, validation.commit, prereg.EVIDENCE_CONTRACT_PATH
    )
    assert evidence_raw is not None
    assert latest["evidence_contract_sha256"] == prereg.evidence_contract_sha256(evidence_raw)
    if validation.generation_number == 1:
        assert latest["supersedes_sha256"] is None


@CANDIDATE_XDIST_GROUP
def test_candidate_freeze_batch_is_bounded_by_frozen_touch_points(
    repository_candidate_commit: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    calls: list[tuple[int, int]] = []
    original = prereg._batch_oids

    def counted_batch_oids(repo_root, commits, paths):
        calls.append((len(commits), len(paths)))
        return original(repo_root, commits, paths)

    monkeypatch.setattr(prereg, "_batch_oids", counted_batch_oids)
    prereg.validate_condition_freeze_at(ROOT, repository_candidate_commit)
    main_calls = [call for call in calls if call[1] > 1]
    assert len(main_calls) == 1
    commit_count, path_count = main_calls[0]
    assert commit_count * path_count < prereg.MAX_BATCH_REQUESTS
    assert commit_count < prereg.MAX_COMMITS


@CANDIDATE_XDIST_GROUP
def test_repository_tip_binds_current_decider_version_without_activation(
    repository_candidate_commit: str,
) -> None:
    candidate = repository_candidate_commit
    report = prereg.activation_report_at(ROOT, candidate)
    assert report.commit == candidate
    assert report.condition_freeze_valid is True
    assert report.freeze_reason_code == "valid"
    assert report.freeze_generation is not None

    tip_raw = prereg.read_blob_at(
        ROOT,
        report.commit,
        prereg.generation_path(report.freeze_generation),
    )
    assert tip_raw is not None
    tip = json.loads(tip_raw)
    record = prereg._load_freeze_record(
        tip_raw,
        expected_generation=report.freeze_generation,
    )

    assert tip["schema_version"] == prereg.SCHEMA_VERSION
    assert tip["decider_version"] == prereg.DECIDER_VERSION
    assert record.schema_version == prereg.SCHEMA_VERSION
    assert record.decider_version == prereg.DECIDER_VERSION
    assert report.decider_version == prereg.DECIDER_VERSION
    assert report.decider_version_matches is True
    assert report.decider_version_reason_code == "decider-version-match"
    assert report.effective is False


def test_machine_contract_function_names_exist_and_checked_set_is_exact() -> None:
    value = json.loads((ROOT / prereg.EVIDENCE_CONTRACT_PATH).read_bytes())
    _assert_machine_contract_function_pins(
        value,
        excluded_pin=MACHINE_CONTRACT_FUNCTION_EXCLUSIONS,
    )


def test_machine_contract_exclusion_pin_cannot_be_omitted() -> None:
    value = json.loads((ROOT / prereg.EVIDENCE_CONTRACT_PATH).read_bytes())
    with pytest.raises(AssertionError):
        _assert_machine_contract_function_pins(
            value,
            excluded_pin=frozenset(),
        )


def test_machine_contract_rejects_prewave_accept_trial_name() -> None:
    value = json.loads((ROOT / prereg.EVIDENCE_CONTRACT_PATH).read_bytes())
    c09 = value["conditions"][8]
    serialized = json.dumps(c09, ensure_ascii=False)
    assert serialized.count("assert_trial_registry_acceptance") == 4
    value["conditions"][8] = json.loads(
        serialized.replace("assert_trial_registry_acceptance", "accept_trial")
    )

    checked, excluded, missing = _machine_contract_function_findings(value)
    old = (
        "C09",
        "orchestrator/campaign/trial_registry.py",
        "assert_trial_registry_acceptance",
    )
    prewave = (
        "C09",
        "orchestrator/campaign/trial_registry.py",
        "accept_trial",
    )
    assert checked == MACHINE_CONTRACT_FUNCTION_CHECKS - {old}
    assert excluded == MACHINE_CONTRACT_FUNCTION_EXCLUSIONS
    assert missing == frozenset({prewave})


def test_generation_4_changes_revision_procedure_without_changing_condition_contract(
) -> None:
    generation_3_raw = (ROOT / prereg.generation_path(3)).read_bytes()
    generation_4_raw = (ROOT / prereg.generation_path(4)).read_bytes()
    generation_3 = prereg._load_freeze_record(
        generation_3_raw,
        expected_generation=3,
    )
    generation_4 = prereg._load_freeze_record(
        generation_4_raw,
        expected_generation=4,
    )

    assert (
        generation_4.section5_field_names_sha256
        == generation_3.section5_field_names_sha256
    )
    assert (
        generation_4.section6_conditions_sha256
        == generation_3.section6_conditions_sha256
    )
    assert len(generation_3.section6_condition_hashes) == 12
    assert len(generation_4.section6_condition_hashes) == 12
    assert (
        generation_4.section6_condition_hashes
        == generation_3.section6_condition_hashes
    )
    assert (
        generation_4.evidence_contract_sha256
        == generation_3.evidence_contract_sha256
    )

    assert (
        generation_4.normative_body_sha256
        != generation_3.normative_body_sha256
    )
    assert generation_4.protected_sha256 != generation_3.protected_sha256
    assert generation_4.supersedes_sha256 == generation_3.raw_sha256
    assert generation_4.ruling_reference == "D458"
    assert generation_4.schema_version == "s8c-prereg-condition-freeze/v2"
    assert generation_4.decider_version == "s8c-decider/v1"


@pytest.mark.parametrize("generation", (1, 2, 3))
def test_repository_legacy_v1_generations_remain_readable(generation: int) -> None:
    raw = (ROOT / prereg.generation_path(generation)).read_bytes()
    record = prereg._load_freeze_record(raw, expected_generation=generation)
    assert record.schema_version == prereg.LEGACY_SCHEMA_VERSION
    assert record.decider_version is None


def test_candidate_commit_observes_uncommitted_worktree_delta(tmp_path: Path) -> None:
    """HEAD 不適合・未 commit candidate 適合を作り、HEAD への退行を赤にする。"""

    root = tmp_path / "candidate-repo"
    root.mkdir()
    _git_text("init", "-q", "-b", "main", root=root)
    _git_text("config", "user.name", "fixture", root=root)
    _git_text("config", "user.email", "fixture@example.invalid", root=root)
    source = root / prereg.SOURCE_PATH
    source.parent.mkdir(parents=True)
    source.write_bytes(b"# incomplete HEAD fixture\n")
    _git_text("add", "-A", root=root)
    _git_text("commit", "-q", "-m", "invalid HEAD", root=root)
    head = _git_text("rev-parse", "HEAD", root=root)

    source.write_bytes(PREREG_DOC.read_bytes())
    candidate = _candidate_commit(tmp_path, root=root)

    assert candidate != head
    with pytest.raises(prereg.PreregistrationError) as invalid_head:
        prereg.parse_preregistration_at(root, head)
    assert invalid_head.value.reason == "section-missing"
    candidate_contract = prereg.parse_preregistration_at(root, candidate)
    worktree_contract = prereg.parse_preregistration_markdown(source.read_bytes())
    assert candidate_contract.normative_body_sha256 == worktree_contract.normative_body_sha256


@CANDIDATE_XDIST_GROUP
def test_candidate_is_not_effective_and_has_zero_satisfied_predicates(
    repository_candidate_commit: str,
) -> None:
    candidate = repository_candidate_commit
    report = prereg.activation_report_at(ROOT, candidate)
    assert report.commit == candidate
    assert report.effective is False
    assert len(report.predicates) == len(prereg.PREDICATE_IDS) == 12
    assert tuple(result.id for result in report.predicates) == prereg.PREDICATE_IDS
    assert sum(
        result.status is prereg.PredicateStatus.SATISFIED
        for result in report.predicates
    ) == 0


@CANDIDATE_XDIST_GROUP
def test_wave_files_do_not_contaminate_production_holdout_scan(
    repository_candidate_commit: str,
) -> None:
    candidate = repository_candidate_commit
    head_paths = _commit_paths(candidate)
    assert WAVE_REQUIRED_PATHS <= head_paths
    wave_paths = _wave_paths(head_paths)
    assert any(path.startswith(f"{prereg.FREEZE_DIR}/") for path in wave_paths)

    enumerated = set(s8b_holdout_freeze.enumerate_repository_files(ROOT))
    assert wave_paths <= enumerated
    wave_texts = {
        path: (ROOT / path).read_text(encoding="utf-8")
        for path in sorted(wave_paths)
    }
    hits = s8b_holdout_freeze.holdout_conjunction_hits(wave_texts)
    assert set(hits) == set(s8b_holdout_freeze.HOLDOUTS)
    assert all(paths == [] for paths in hits.values())

    report = s8b_holdout_freeze.search_repository(ROOT, files=sorted(enumerated))
    s8b_holdout_freeze._assert_search_pass(report)
    assert report["positive_control"]["hit_count"] > 0


def test_s8c_namespace_is_not_excluded_from_holdout_scan() -> None:
    sentinel = f"{prereg.FREEZE_DIR}/sentinel.json"
    assert all(
        not sentinel.startswith(prefix)
        for prefix in s8b_holdout_freeze.EXCLUDED_PATHS
    )


def test_actual_cli_has_no_approval_or_activation_commands() -> None:
    parser = prereg._build_parser()
    subparsers = next(
        action
        for action in parser._actions
        if isinstance(action, argparse._SubParsersAction)
    )
    commands = set(subparsers.choices)
    assert commands == {"check", "prepare-revision"}
    assert commands.isdisjoint({"approve", "activate", "revoke"})


def test_s8c_preregistration_is_an_enumerated_living_doc() -> None:
    assert check_docs.REPO == ROOT
    assert PREREG_DOC in check_docs.LIVING_DOCS
    assert PREREG_DOC in check_docs._ENUMERATED_DOCS


def test_living_doc_section5_value_violations_are_empty() -> None:
    contract = prereg.parse_preregistration_worktree(ROOT)
    assert contract.section5_value_violations == ()
    target = next(
        item
        for item in contract.section5_findings
        if item.name == prereg.SECTION5_ITERATION_CONTRAST_FIELD
    )
    assert target.status is prereg.FieldStatus.UNFILLED


def test_living_doc_section5_value_validator_positive_control() -> None:
    source = PREREG_DOC.read_bytes()
    field = prereg.SECTION5_ITERATION_CONTRAST_FIELD.encode("utf-8")
    old_cell = b"|" + field + "|未記入|".encode("utf-8")
    mutated_value = (
        b'{"H1":{"delta_min":1,"direction":"on-minus-off","n":1,'
        b'"sd_max":0,"unit":"ops_per_second"},'
        b'"H2":{"delta_min":1,"direction":"on-minus-off","n":2,'
        b'"sd_max":0,"unit":"ops_per_second"}}'
    )
    new_cell = b"|" + field + b"|`" + mutated_value + b"`|"
    assert source.count(old_cell) == 1
    mutated = source.replace(old_cell, new_cell)
    assert mutated != source

    contract = prereg.parse_preregistration_markdown(mutated)
    target = next(
        item
        for item in contract.section5_findings
        if item.name == prereg.SECTION5_ITERATION_CONTRAST_FIELD
    )
    assert target.status is prereg.FieldStatus.FILLED
    assert contract.section5_value_violations == (
        prereg.Section5ValueViolation(
            prereg.SECTION5_ITERATION_CONTRAST_FIELD,
            "H1.n",
            "n-range",
        ),
    )


def test_section5_validator_keys_exist_in_living_doc_field_names() -> None:
    contract = prereg.parse_preregistration_worktree(ROOT)
    validator_keys = set(prereg._SECTION5_VALUE_VALIDATORS)
    assert validator_keys == {prereg.SECTION5_ITERATION_CONTRAST_FIELD}
    assert validator_keys <= set(contract.section5_field_names)


def test_s8c_living_doc_reference_negative_controls(monkeypatch, capsys) -> None:
    """8c 文書の不在 path と腐敗行番号を本番 main 経路で赤にする。"""

    original_safe_read = check_docs._safe_read_text
    injected = False
    missing = "docs/definitely-missing-s8c-negative-control.md"
    stale_line = "phase3-8c-preregistration.md:1"

    def dirty_safe_read(path, *args, **kwargs):
        nonlocal injected
        text = original_safe_read(path, *args, **kwargs)
        if path == PREREG_DOC and text is not None:
            injected = True
            return text + f"\nnegative path: {missing}\nnegative line: {stale_line}\n"
        return text

    monkeypatch.setattr(check_docs, "_safe_read_text", dirty_safe_read)
    returncode = check_docs.main()
    output = capsys.readouterr().out
    assert injected, "8c 文書が LIVING_DOCS の本番読取経路を通っていない"
    assert returncode == 1
    assert f"実在しないパス参照: {missing!r}" in output
    assert f"docs の行番号参照 (腐敗する): {stale_line!r}" in output
