"""rr80/rr20 calibration selection is bound, finite, and shell-valid."""

from __future__ import annotations

import importlib.util
import re
import shlex
import shutil
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SUBMIT = ROOT / "tools/pegasus/submit_certify.sh"
JOB = ROOT / "tools/pegasus/certify_calibration.sh"
COST_PROBE = ROOT / "tools/pegasus/probes/t1683_rr5_cost_probe.py"
README = ROOT / "tools/pegasus/README.md"


def _load_cost_probe():
    spec = importlib.util.spec_from_file_location(
        "t1683_rr5_cost_probe_test", COST_PROBE,
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_submitter_exposes_only_the_calibration_whitelist() -> None:
    source = SUBMIT.read_text(encoding="utf-8")

    assert "[--job-script PATH] [--rratio 20|50|80]" in source
    assert 'RRATIO=50' in source
    assert 'RRATIO" != "20"' in source
    assert 'RRATIO" != "50"' in source
    assert 'RRATIO" != "80"' in source
    assert "IZANAGI_CALIBRATION_RRATIO=$RRATIO" in source
    assert '"calibration_rratio": int(rratio)' in source
    assert '"ycsb_rratio": str(request["calibration_rratio"])' in source
    assert "':(exclude)output'" in source


def test_job_rechecks_the_submission_workload_and_records_it() -> None:
    source = JOB.read_text(encoding="utf-8")

    assert 'CALIBRATION_RRATIO="$IZANAGI_CALIBRATION_RRATIO"' in source
    assert '"calibration_rratio": (' in source
    assert 'ycsb_rratio=$CALIBRATION_RRATIO' in source
    assert '"calibration": {"workload": {"ycsb_rratio": rratio}}' in source
    assert "ycsb_rratio=50" not in source
    assert source.index("condition_gate_argv=") < source.index("build_argv=")
    assert "--macro BACKOFF_FIXED" in source
    assert "--stock-comparison" in source
    assert "--meaning-case=-1:branch:stock-adaptive-backoff" in source
    assert "--use-class certified-selection" in source
    assert "-DCCBENCH_BACKOFF_FIXED=-1" in source
    assert '"-DCMAKE_CXX_FLAGS=-DBACKOFF_FIXED=-1"' not in source


def test_calibration_shell_scripts_parse() -> None:
    for script in (SUBMIT, JOB):
        completed = subprocess.run(
            ["bash", "-n", str(script)],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        assert completed.returncode == 0, completed.stderr


def test_cost_probe_condition_gate_dominates_first_buildcache_call() -> None:
    source = COST_PROBE.read_text(encoding="utf-8")
    main = source[source.index("def main()") :]
    assert main.index("_require_condition_gates") < main.index("buildcache.build(")
    assert 'int(adopted["BACKOFF_NOINLINE"])' in source


def test_cost_probe_requests_every_genome_value_and_inert_witness() -> None:
    probe = _load_cost_probe()
    for workload_id in ("rr5", "rr50"):
        workload = probe._load_workload(workload_id)
        cells = probe._condition_requests_by_genome(workload)
        assert [name for name, _defines, _requests in cells] == [
            name for name, _defines in workload["genomes"]
        ]
        assert {
            (name, request.macro, request.requested_value)
            for name, _defines, requests in cells
            for request, _declaration in requests
        } == {
            (name, macro, int(defines[macro]))
            for name, defines in workload["genomes"]
            for macro in ("BACKOFF_FIXED", "BACKOFF_NOINLINE")
        }
        stock_requests = {
            request.macro: (request, declaration)
            for name, _defines, requests in cells if name.endswith("-stock")
            for request, declaration in requests
        }
        assert stock_requests["BACKOFF_FIXED"][0].stock_comparison is True
        assert stock_requests["BACKOFF_FIXED"][1] is not None
        assert stock_requests["BACKOFF_NOINLINE"][0].stock_comparison is True


def test_cost_probe_uses_factory_noinline_and_legacy_backoff_declarations() -> None:
    probe = _load_cost_probe()
    workload = {
        "genomes": [(
            "synthetic-stock",
            {"BACKOFF_FIXED": -1, "BACKOFF_NOINLINE": 0},
        )],
    }

    cells = probe._condition_requests_by_genome(workload)
    requests = {
        request.macro: (request, declaration)
        for _name, _defines, rows in cells
        for request, declaration in rows
    }
    noinline_request, noinline_declaration = requests["BACKOFF_NOINLINE"]
    fixed_request, fixed_declaration = requests["BACKOFF_FIXED"]

    assert type(noinline_declaration) is (
        probe.condition_meaning_gate.ConditionalBranchMeaningDeclaration
    )
    assert noinline_declaration == (
        probe.condition_meaning_gate.declare_define_runtime_meaning(
            noinline_request,
        )
    )
    assert fixed_request.requested_value == -1
    assert type(fixed_declaration) is (
        probe.condition_meaning_gate.MeaningWitnessDeclaration
    )
    assert fixed_declaration.cases[0].expected_selected_branch == (
        probe.condition_meaning_gate.STOCK_ADAPTIVE_BRANCH
    )


def test_submitter_rejects_an_unregistered_ratio_before_side_effects(tmp_path: Path) -> None:
    completed = subprocess.run(
        [
            str(SUBMIT),
            "--rratio",
            "95",
            "--attempts-root",
            str(tmp_path / "attempts"),
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )

    assert completed.returncode == 2
    assert "--rratio must be exactly 20, 50, or 80" in completed.stderr
    assert not (tmp_path / "attempts").exists()


def _run_submit_dry_run_in_clean_fixture(
    tmp_path: Path,
) -> tuple[Path, Path, Path, list[str]]:
    fixture_repo = tmp_path / "repo"
    fixture_tools = fixture_repo / "tools" / "pegasus"
    fixture_tools.parent.mkdir(parents=True)
    shutil.copytree(
        ROOT / "tools" / "pegasus",
        fixture_tools,
        ignore=shutil.ignore_patterns("__pycache__"),
    )
    subprocess.run(["git", "init", "-q", str(fixture_repo)], check=True)
    subprocess.run(
        ["git", "-C", str(fixture_repo), "config", "user.email", "fixture@example.invalid"],
        check=True,
    )
    subprocess.run(
        ["git", "-C", str(fixture_repo), "config", "user.name", "Fixture"],
        check=True,
    )
    subprocess.run(["git", "-C", str(fixture_repo), "add", "."], check=True)
    subprocess.run(
        ["git", "-C", str(fixture_repo), "commit", "-qm", "fixture"],
        check=True,
    )

    completed = subprocess.run(
        [
            "bash",
            str(fixture_tools / "submit_certify.sh"),
            "--repo-root",
            str(fixture_repo),
            "--attempts-root",
            str(tmp_path / "attempts"),
            "--dry-run",
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    assert completed.returncode == 0, completed.stderr
    command_lines = [
        line for line in completed.stdout.splitlines()
        if line.startswith("qsub command:")
    ]
    assert len(command_lines) == 1
    qsub_argv = shlex.split(command_lines[0].removeprefix("qsub command:"))

    git_common_dir = Path(subprocess.run(
        [
            "git",
            "-C",
            str(fixture_repo),
            "rev-parse",
            "--path-format=absolute",
            "--git-common-dir",
        ],
        capture_output=True,
        text=True,
        check=True,
    ).stdout.strip())
    expected_root = (
        git_common_dir.parent.parent
        / "izanagi-job-evidence"
        / "calibration-certify"
    )
    return fixture_repo, git_common_dir.parent, expected_root, qsub_argv


def test_submit_dry_run_passes_scheduler_file_paths_to_qsub(tmp_path: Path) -> None:
    _fixture_repo, _git_common_repo, expected_root, qsub_argv = (
        _run_submit_dry_run_in_clean_fixture(tmp_path)
    )

    assert qsub_argv[0] == "qsub"
    assert "-o" in qsub_argv
    assert "-e" in qsub_argv
    stdout_path = Path(qsub_argv[qsub_argv.index("-o") + 1])
    stderr_path = Path(qsub_argv[qsub_argv.index("-e") + 1])
    assert stdout_path.is_absolute()
    assert stderr_path.is_absolute()

    stdout_name = re.fullmatch(r"([0-9a-f]{32})\.scheduler\.stdout", stdout_path.name)
    stderr_name = re.fullmatch(r"([0-9a-f]{32})\.scheduler\.stderr", stderr_path.name)
    assert stdout_name is not None
    assert stderr_name is not None
    assert stdout_name.group(1) == stderr_name.group(1)
    assert stdout_path != expected_root
    assert stderr_path != expected_root
    assert stdout_path.parent == expected_root
    assert stderr_path.parent == expected_root
    assert expected_root.is_dir()


def test_submit_dry_run_keeps_scheduler_output_outside_the_repository(tmp_path: Path) -> None:
    """受理: 返り先が repo の外なら検査は通り、qsub argv はそのまま構築される。

    拒否: 返り先が repo root 自身またはその配下へ動いた瞬間、この検査は赤になる。
    """
    fixture_repo, git_common_repo, _expected_root, qsub_argv = (
        _run_submit_dry_run_in_clean_fixture(tmp_path)
    )

    assert "-o" in qsub_argv
    assert "-e" in qsub_argv
    stdout_path = Path(qsub_argv[qsub_argv.index("-o") + 1])
    stderr_path = Path(qsub_argv[qsub_argv.index("-e") + 1])
    for output_path in (stdout_path, stderr_path):
        assert output_path != fixture_repo
        assert fixture_repo not in output_path.parents
        assert output_path != git_common_repo
        assert git_common_repo not in output_path.parents


def test_runbook_shows_ai_driven_h1_h2_submission_path() -> None:
    source = README.read_text(encoding="utf-8")

    assert "submit_certify.sh --rratio 80" in source
    assert "submit_certify.sh --rratio 20" in source
    assert "人間が JSON を編集・登録する必要はなく" in source
