"""rr80/rr20 calibration selection is bound, finite, and shell-valid."""

from __future__ import annotations

import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SUBMIT = ROOT / "tools/pegasus/submit_certify.sh"
JOB = ROOT / "tools/pegasus/certify_calibration.sh"
COST_PROBE = ROOT / "tools/pegasus/probes/t1683_rr5_cost_probe.py"
README = ROOT / "tools/pegasus/README.md"


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


def test_runbook_shows_ai_driven_h1_h2_submission_path() -> None:
    source = README.read_text(encoding="utf-8")

    assert "submit_certify.sh --rratio 80" in source
    assert "submit_certify.sh --rratio 20" in source
    assert "人間が JSON を編集・登録する必要はなく" in source
