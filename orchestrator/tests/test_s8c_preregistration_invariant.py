# -*- coding: utf-8 -*-
"""Phase 3 段 8c 事前登録の実 repository invariant。"""
from __future__ import annotations

import argparse
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
    }
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
