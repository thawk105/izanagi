from __future__ import annotations

import ast
import json
import os
import re
from pathlib import Path

import pytest

from orchestrator.campaign import ident, site_policy
from orchestrator.campaign import paper_story_a1_paired as paired


REPO_ROOT = Path(__file__).resolve().parents[2]
JOB = REPO_ROOT / "tools/pegasus/paper_story_a1_paired.sh"
REGISTRY = REPO_ROOT / "tools/pegasus/admission_registry.json"


def _gate_args(tmp_path: Path) -> dict:
    repo = tmp_path / "repo"
    repo.mkdir(parents=True)
    return {
        "repo_root": repo,
        "expected_head": "a" * 40,
        "output_root": tmp_path / "output-root",
        "cache_root": tmp_path / "cache-root",
        "result_root": tmp_path / "result-root",
        "pbs_jobid": "12345.nqsv",
        "site": site_policy.PEGASUS_COMPUTE,
        "observed_head": "a" * 40,
        "porcelain": "",
    }


def test_clean_h0_compute_fresh_roots_positive_contract(tmp_path: Path) -> None:
    args = _gate_args(tmp_path)
    roots = paired.validate_measure_environment(**args)
    assert roots == {
        "output_root": os.fspath((tmp_path / "output-root").resolve()),
        "cache_root": os.fspath((tmp_path / "cache-root").resolve()),
        "result_root": os.fspath((tmp_path / "result-root").resolve()),
    }
    assert not any(Path(path).exists() for path in roots.values())


@pytest.mark.parametrize(
    ("field", "value", "message"),
    [
        ("site", site_policy.PEGASUS_LOGIN, "Pegasus compute"),
        ("site", site_policy.PEGASUS_SUSPECT, "Pegasus compute"),
        ("observed_head", "b" * 40, "HEAD differs"),
        ("porcelain", " M tracked.py", "dirty"),
        ("pbs_jobid", "bad job id", "PBS_JOBID"),
    ],
    ids=["M12-login", "M12-suspect", "M12-head-mismatch", "M12-dirty", "bad-pbs"],
)
def test_measure_environment_rejects_site_head_dirty_and_pbs(
    tmp_path: Path, field: str, value: str, message: str
) -> None:
    args = _gate_args(tmp_path)
    args[field] = value
    with pytest.raises(paired.PaperStoryError, match=message):
        paired.validate_measure_environment(**args)


@pytest.mark.parametrize("root_name", ["output_root", "cache_root", "result_root"])
def test_measure_environment_rejects_every_existing_root(
    tmp_path: Path, root_name: str
) -> None:
    args = _gate_args(tmp_path)
    Path(args[root_name]).mkdir()
    with pytest.raises(paired.PaperStoryError, match="must not already exist"):
        paired.validate_measure_environment(**args)


def test_measure_environment_rejects_repo_internal_or_aliased_roots(tmp_path: Path) -> None:
    args = _gate_args(tmp_path)
    args["output_root"] = args["repo_root"] / "raw"
    with pytest.raises(paired.PaperStoryError, match="outside the repository"):
        paired.validate_measure_environment(**args)

    args = _gate_args(tmp_path / "second")
    args["cache_root"] = args["output_root"]
    with pytest.raises(paired.PaperStoryError, match="distinct"):
        paired.validate_measure_environment(**args)


def test_job_body_contains_all_m12_gates_and_no_submitter() -> None:
    source = JOB.read_text(encoding="utf-8")
    required = (
        '[[ -n "${PBS_JOBID:-}" ]]',
        '[[ -n "${PBS_O_WORKDIR:-}" ]]',
        '[[ "$CURRENT_HEAD" == "$IZANAGI_EXPECTED_HEAD" ]]',
        "status --porcelain --untracked-files=all",
        "site_policy.PEGASUS_COMPUTE",
        "if os.path.lexists(root) or os.path.lexists(item):",
        'mkdir -- "$IZANAGI_A1_RAW_ROOT"',
        '--study-id "$EXPECTED_STUDY_ID"',
        '--expected-head "$IZANAGI_EXPECTED_HEAD"',
        '--output-root "$OUTPUT_ROOT"',
        '--cache-root "$IZANAGI_A1_CACHE_ROOT"',
        '--result-root "$RESULT_ROOT"',
        'export IZANAGI_EXPLORATION_OUTPUT_ROOT="$OUTPUT_ROOT"',
        'with open(path, "x", encoding="utf-8")',
    )
    for marker in required:
        assert source.count(marker) == 1, marker
    assert re.search(r"^[ \t]*qsub(?:[ \t]|$)", source, re.MULTILINE) is None
    assert "submit_" not in source


def test_job_body_is_executable_and_registry_is_exact_dispatch_required() -> None:
    assert JOB.stat().st_mode & 0o111
    registry = json.loads(REGISTRY.read_text(encoding="utf-8"))["entries"]
    assert registry["tools/pegasus/paper_story_a1_paired.sh"] == {
        "class": "dispatch-required",
        "reason": "PBS paper-story A-1 paired measurement job body",
        "primary_gate": "PBS allocation and job-body site preflight",
        "evidence": "static job-body classification",
    }


def test_driver_reuses_run_campaign_without_direct_evaluate_call() -> None:
    source = (REPO_ROOT / paired.DRIVER_RELATIVE_PATH).read_text(encoding="utf-8")
    tree = ast.parse(source)
    imported = {
        alias.name
        for node in ast.walk(tree)
        if isinstance(node, ast.ImportFrom)
        for alias in node.names
    }
    called = {
        node.func.id
        for node in ast.walk(tree)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
    }
    assert "run_campaign" in imported
    assert "run_campaign" in called
    assert "evaluate" not in imported
    assert "evaluate" not in called


def test_exact_two_arm_three_workload_campaign_ids_are_distinct_and_bound() -> None:
    policy = paired.load_policy()[0]
    ids = [
        str(ident.campaign_id(paired.campaign_config(policy, workload)))
        for workload in paired.WORKLOAD_ORDER
    ]
    assert len(set(ids)) == 3
    assert len(paired.genomes(policy)) == 2
    for workload in paired.WORKLOAD_ORDER:
        cfg = paired.campaign_config(policy, workload)
        assert cfg.search_config["study_id"] == paired.STUDY_ID
        assert cfg.search_config["arm_order"] == ["adaptive", "static10"]
        assert cfg.search_config["scale"] == {
            "records": 1_000_000,
            "threads": 48,
            "ycsb_zipf_skew": "0.9",
            "ycsb_rmw": "0",
            "ycsb_max_ope": "10",
            "extime_s": 3,
            "reps": 5,
            "expected_verify_configs": ["legacy"],
        }
