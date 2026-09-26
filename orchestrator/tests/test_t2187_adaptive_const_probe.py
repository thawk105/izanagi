from __future__ import annotations

import argparse
import ast
import copy
from concurrent.futures import ThreadPoolExecutor
from contextlib import contextmanager
import hashlib
import importlib.util
import json
import os
import re
import shutil
import subprocess
import sys
import threading
import time
from pathlib import Path
from types import SimpleNamespace

import pytest

from orchestrator.campaign import backoff_policy_performance_analysis as policy_analysis
from orchestrator.campaign.backoff_counterfactual_cohort2_analysis import (
    PREREGISTERED_SEEDS,
)

ROOT = Path(__file__).resolve().parents[2]
DRIVER = ROOT / "tools" / "pegasus" / "probes" / "t2187_adaptive_const_probe.py"
PBS = ROOT / "tools" / "pegasus" / "probes" / "t2187_adaptive_const_probe.pbs"
SUBMIT_T2417 = (
    ROOT
    / "tools"
    / "pegasus"
    / "submit_t2417_backoff_policy_performance.sh"
)
POLICY_PERFORMANCE_PREREGISTRATION = (
    ROOT / "docs" / "backoff-policy-performance-preregistration.md"
)
POLICY_PERFORMANCE_PREREGISTRATION_ERRATUM_1 = (
    ROOT / "docs" / "backoff-policy-performance-preregistration-erratum-1.md"
)
PATCH = ROOT / "patches" / "cicada-adaptive-params.patch"
PATCH_B = ROOT / "patches" / "cicada-adaptive-dynamic.patch"
PATCH_C = ROOT / "patches" / "cicada-adaptive-counterfactual.patch"
CCBENCH = ROOT / "external" / "ccbench"
PIN_FULL = "68106660686232781bca3be792a750d3e19d7a8a"
# The preregistered t2417 producer runs from its historical series checkout.
T2417_SERIES_PIN_FULL = "511c9538e4e8efa54b45cda62e72389ed3b706ec"
T2417_SERIES_PIN = "511c953"

SPEC = importlib.util.spec_from_file_location(
    "t2187_adaptive_const_probe_under_test", DRIVER
)
assert SPEC is not None and SPEC.loader is not None
probe = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = probe
SPEC.loader.exec_module(probe)

VALID_CELLS = (
    "none:0:100:1000:10,"
    "step0.5-upd10:1:0.5:1000:10,"
    "stock:1:100:1000:10"
)
CERT_CELL = "tuned:1:1:1000:2560"
DYNAMIC_CERT_CELL = (
    "cw-as-dyn:1:1:1000:2560:10000:10240:1:1:4:1"
)
COHORT2_POLICY1_CERT_CELL = (
    "cw-as-dyn-c2-p1:1:1:1000:2560:10000:9223372036854775807:1:1:4:1:1"
)
COHORT2_POLICY2_CERT_CELL = (
    "cw-as-dyn-c2-p2:1:1:1000:2560:10000:9223372036854775807:1:1:4:1:2"
)
TRACE_CELLS = (
    "cw:1:1:1000:2560:10000:10240:0:100:100:0,"
    "cw-as:1:1:1000:2560:10000:10240:1:1:4:0,"
    "cw-as-dyn:1:1:1000:2560:10000:10240:1:1:4:1"
)
COUNTERFACTUAL_TRACE_CELLS = (
    "cw-as-dyn-p0:1:1:1000:2560:10000:10240:1:1:4:1:0,"
    "cw-as-dyn-p1:1:1:1000:2560:10000:10240:1:1:4:1:1,"
    "cw-as-dyn-p2:1:1:1000:2560:10000:10240:1:1:4:1:2"
)
EXPECTED_PERMUTATIONS = (
    "cw-as-dyn-p0:1:1:1000:2560:10000:10240:1:1:4:1:0,"
    "cw-as-dyn-p1:1:1:1000:2560:10000:10240:1:1:4:1:1,"
    "cw-as-dyn-p2:1:1:1000:2560:10000:10240:1:1:4:1:2",
    "cw-as-dyn-p0:1:1:1000:2560:10000:10240:1:1:4:1:0,"
    "cw-as-dyn-p2:1:1:1000:2560:10000:10240:1:1:4:1:2,"
    "cw-as-dyn-p1:1:1:1000:2560:10000:10240:1:1:4:1:1",
    "cw-as-dyn-p1:1:1:1000:2560:10000:10240:1:1:4:1:1,"
    "cw-as-dyn-p0:1:1:1000:2560:10000:10240:1:1:4:1:0,"
    "cw-as-dyn-p2:1:1:1000:2560:10000:10240:1:1:4:1:2",
    "cw-as-dyn-p1:1:1:1000:2560:10000:10240:1:1:4:1:1,"
    "cw-as-dyn-p2:1:1:1000:2560:10000:10240:1:1:4:1:2,"
    "cw-as-dyn-p0:1:1:1000:2560:10000:10240:1:1:4:1:0",
    "cw-as-dyn-p2:1:1:1000:2560:10000:10240:1:1:4:1:2,"
    "cw-as-dyn-p0:1:1:1000:2560:10000:10240:1:1:4:1:0,"
    "cw-as-dyn-p1:1:1:1000:2560:10000:10240:1:1:4:1:1",
    "cw-as-dyn-p2:1:1:1000:2560:10000:10240:1:1:4:1:2,"
    "cw-as-dyn-p1:1:1:1000:2560:10000:10240:1:1:4:1:1,"
    "cw-as-dyn-p0:1:1:1000:2560:10000:10240:1:1:4:1:0",
)
EXPECTED_SEEDS_BY_SLOT = {
    0: 7170359757993337886,
    1: 17989269546948137795,
    2: 3716960512023197351,
    3: 2309627334396074330,
    4: 17927187949116432153,
    5: 3065832495472073934,
    6: 4312234405970990967,
    7: 427285116805996036,
    8: 3640648522570663905,
    9: 6418011988295890983,
    10: 8628608498907907249,
    11: 3020250207517407008,
    12: 2373385927424670485,
    13: 12508141252750115867,
    14: 5818589253263944573,
    15: 13760661656174455019,
    16: 16587099826641119208,
    17: 13478069633953621058,
}
EXPECTED_POLICY_WORKLOADS = "write-heavy,balanced,read-heavy"
EXPECTED_POLICY_THREADS = "6,12,18,24,30,36,42,48"
EXPECTED_POLICY_PREREG_SHA256 = (
    "2f5170c99dda9dd70647a611bff798b6e54c5e29b60e872cd755e5b8515cc25c"
)
COUNTERFACTUAL_COHORT2_TRACE_CELLS = (
    "cw-as-dyn-c2-p0:1:1:1000:2560:10000:9223372036854775807:1:1:4:1:0,"
    "cw-as-dyn-c2-p1:1:1:1000:2560:10000:9223372036854775807:1:1:4:1:1,"
    "cw-as-dyn-c2-p2:1:1:1000:2560:10000:9223372036854775807:1:1:4:1:2"
)
NONMONOTONIC_TRACE_CELLS = (
    "nm-step0.5:1:0.5:1000:10:0:0:0:100:100:0,"
    "nm-step1:1:1:1000:10:0:0:0:100:100:0,"
    "nm-step1-u2560:1:1:1000:2560:0:0:0:100:100:0,"
    "nm-step2:1:2:1000:10:0:0:0:100:100:0,"
    "nm-step25:1:25:1000:10:0:0:0:100:100:0,"
    "nm-step100:1:100:1000:10:0:0:0:100:100:0"
)


SERIAL_TRACE = """\
C 0 0 2 1 1 1
R 0 aa 1 0
W 0 aa U 2 1
E 0
C 1 0 2 2 1 1
R 1 aa 2 1
W 1 bb U 2 2
E 1
"""

SERIAL_TRACE_WITHOUT_EDGES = """\
C 0 0 2 1 1 1
R 0 aa 1 0
W 0 aa U 2 1
E 0
C 1 0 2 2 1 1
R 1 bb 1 0
W 1 bb U 2 2
E 1
"""

G6_SERIAL_TRACE = ROOT / "orchestrator" / "tests" / "fixtures" / "g6_silo_serial_1thread"


def _certify_argv(
    tmp_path: Path,
    *,
    workload: str = "balanced",
    slot: int = 0,
    attempt_id: str = "attempt-test",
    cells: str = CERT_CELL,
    threads: int = 48,
    step_policy_seed: int | None = None,
):
    performance = tmp_path / "performance.json"
    if not performance.exists():
        # The A+B patch/source identity fields make old v1 fixtures ambiguous;
        # this current-code fixture intentionally follows the current schema.
        performance.write_text(
            json.dumps(
                {
                    "schema_version": probe.SCHEMA_VERSION,
                    "kind": "performance-only-probe",
                    "not_certified": probe.NOT_CERTIFIED,
                }
            )
            + "\n",
            encoding="utf-8",
        )
    expected_identity = tmp_path / "expected-verifier-identity.json"
    if not expected_identity.exists():
        expected_identity.write_text(
            json.dumps(probe._verifier_identity(), sort_keys=True) + "\n",
            encoding="utf-8",
        )
    result_paths = [
        tmp_path / f"certify-{item_workload}-slot{item_slot}-{attempt_id}.json"
        for item_workload in probe.CERT_WORKLOADS
        for item_slot in probe.CERT_SLOTS
    ]
    argv = [
        "--mode",
        "certify",
        "--repo-head",
        subprocess.run(
            ["git", "-C", str(ROOT), "rev-parse", "HEAD"],
            check=True,
            capture_output=True,
            text=True,
        ).stdout.strip(),
        "--repo-clean",
        "1",
        "--cells",
        cells,
        "--workloads",
        workload,
        "--threads",
        str(threads),
        "--rep-index",
        str(slot),
        "--reps-per-job",
        "1",
        "--extime",
        (
            "6"
            if cells in {COHORT2_POLICY1_CERT_CELL, COHORT2_POLICY2_CERT_CELL}
            else "3"
        ),
        "--prologue-elapsed-s",
        "2.5",
        "--prologue-cpu-s",
        "1.25",
        "--group-receipt-out",
        str(tmp_path / "group.json"),
        "--attempt-id",
        attempt_id,
        "--performance-artifact",
        str(performance),
        "--performance-artifact-sha256",
        hashlib.sha256(performance.read_bytes()).hexdigest(),
        "--expected-verifier-identity",
        str(expected_identity),
        "--expected-verifier-identity-sha256",
        hashlib.sha256(expected_identity.read_bytes()).hexdigest(),
    ]
    if step_policy_seed is not None:
        argv.extend(("--step-policy-seed", str(step_policy_seed)))
    for path in result_paths:
        argv.extend(("--group-result-path", str(path)))
    argv.extend(
        (
            "--out",
            str(tmp_path / f"certify-{workload}-slot{slot}-{attempt_id}.json"),
        )
    )
    return argv


def _install_certification_runtime(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    *,
    trace_text: str = SERIAL_TRACE,
    abort_count_stdout: object = 1,
    events: list[str] | None = None,
) -> None:
    """Replace only compute-heavy build/run seams; verifier CLIs remain real."""
    from orchestrator.campaign import pipeline

    events = events if events is not None else []
    monkeypatch.setenv("TMPDIR", str(tmp_path))
    monkeypatch.setenv("PBS_JOBID", "12345.test")
    monkeypatch.setattr(probe.site_policy, "current_site", lambda: "PEGASUS_COMPUTE")
    monkeypatch.setattr(probe.site_policy, "refuses_heavy_work", lambda _site: False)
    monkeypatch.setattr(probe, "_assert_single_tenant", lambda: None)
    monkeypatch.setattr(probe, "_validated_repo_clean", lambda value: value == "1")
    monkeypatch.setattr(
        probe.buildcache, "compilers_for_current_site", lambda: ("gcc", "g++")
    )
    real_build_deadline = probe._run_build_with_deadline

    def observed_build_deadline(builder, timeout_s):
        events.append("build")
        return real_build_deadline(builder, timeout_s)

    monkeypatch.setattr(probe, "_run_build_with_deadline", observed_build_deadline)

    def fake_build(*_args, **kwargs):
        from orchestrator.campaign.build_admission import BuildAdmission

        if kwargs.get("trace") is not True:
            raise RuntimeError("certification build did not request trace=True")
        assert type(kwargs["admission"]) is BuildAdmission
        assert kwargs["source_evidence"].ccbench_commit == probe.CURRENT_PIN
        checkout = Path(kwargs["ccbench_dir"])
        assert checkout.is_dir()
        applied_diff = subprocess.run(
            ["git", "-C", str(checkout), "diff", "--"],
            check=True,
            capture_output=True,
            text=True,
        ).stdout
        assert all(
            macro in applied_diff
            for macro in (
                "BACKOFF_INCR_MILLI",
                "BACKOFF_MAX_US",
                "BACKOFF_UPDATE_US",
            )
        )
        return SimpleNamespace(
            binary="ycsb_silo", bin_sha256="a" * 64, trace=True
        )

    monkeypatch.setattr(probe.buildcache, "build", fake_build)
    monkeypatch.setattr(probe, "_trace_binary_counts", lambda _binary: (0, 0))

    def fake_run(_binary, trace_dir, flags, *_args, **kwargs):
        events.append("run")
        assert flags["ycsb_zipf_skew"] == "0.9"
        assert flags["ycsb_rratio"] in {"5", "50", "95"}
        assert flags["ycsb_rmw"] == "0"
        assert flags["ycsb_max_ope"] == "10"
        assert flags["ycsb_tuple_num"] == "1000000"
        assert flags["thread_num"] == "48"
        assert flags["extime"] == "3"
        assert kwargs["timeout_s"] == probe.RUN_TIMEOUT_S
        path = Path(trace_dir)
        (path / "log").mkdir()
        (path / "trace_0.log").write_text(trace_text, encoding="ascii")
        return SimpleNamespace(
            trace_c_lines=2,
            returncode=0,
            abort_counts=abort_count_stdout,
            commit_count_witness=2,
            batch_commit_count_witness=0,
        )

    monkeypatch.setattr(pipeline, "_run_trace", fake_run)


def test_cells_parser_accepts_three_cells_and_normalizes_milliunits() -> None:
    assert probe.parse_cells(VALID_CELLS) == (
        probe.Cell("none", 0, 100.0, 1000, 10),
        probe.Cell("step0.5-upd10", 1, 0.5, 1000, 10),
        probe.Cell("stock", 1, 100.0, 1000, 10),
    )
    assert [cell.incr_milli for cell in probe.parse_cells(VALID_CELLS)] == [
        100_000,
        500,
        100_000,
    ]


@pytest.mark.parametrize(
    "cells",
    (
        "bad:1:0:1000:10",
        "bad:1:-0.5:1000:10",
        "bad:1:1:0:10",
        "bad:1:1:-1:10",
        "bad:1:1:1000:0",
        "bad:1:1:1000:-1",
    ),
    ids=(
        "zero-step",
        "negative-step",
        "zero-ceiling",
        "negative-ceiling",
        "zero-update",
        "negative-update",
    ),
)
def test_cells_parser_rejects_nonpositive_constants(cells: str) -> None:
    with pytest.raises(ValueError):
        probe.parse_cells(cells)


@pytest.mark.parametrize(
    "cells",
    (
        "dup:1:1:1000:10,dup:1:2:1000:10",
        "short:1:1:1000",
        "",
        "submilli:1:0.0001:1000:10",
    ),
    ids=("duplicate-label", "missing-field", "empty", "rounding-loss"),
)
def test_cells_parser_rejects_malformed_or_lossy_grids(cells: str) -> None:
    with pytest.raises(ValueError):
        probe.parse_cells(cells)


def test_is_stock_control_requires_exact_three_constants_and_backoff() -> None:
    stock = probe.Cell("stock", 1, 100.0, 1000, 10)
    assert probe.is_stock_control(stock)
    assert stock.is_stock_control

    assert not probe.is_stock_control(probe.Cell("step-drift", 1, 99.999, 1000, 10))
    assert not probe.is_stock_control(probe.Cell("ceiling-drift", 1, 100.0, 999, 10))
    assert not probe.is_stock_control(probe.Cell("update-drift", 1, 100.0, 1000, 11))
    assert not probe.is_stock_control(probe.Cell("disabled", 0, 100.0, 1000, 10))
    assert not probe.is_stock_control(
        probe.Cell(
            "inverted",
            1,
            100.0,
            1000,
            10,
            step_policy=1,
            has_step_policy=True,
        )
    )


def test_existing_out_is_rejected_before_site_or_measurement(tmp_path: Path) -> None:
    out = tmp_path / "already-there.json"
    out.write_text("do not overwrite\n", encoding="utf-8")

    with pytest.raises(FileExistsError, match="refusing to overwrite"):
        probe.main(["--cells", VALID_CELLS, "--out", str(out)])

    assert out.read_text(encoding="utf-8") == "do not overwrite\n"


def test_patch_applies_to_exact_pin_and_has_three_fail_closed_macros() -> None:
    assert PATCH.is_file()
    patch = PATCH.read_text(encoding="utf-8")
    assert re.search(r"\bIZANAGI_[A-Z0-9_]+\b", patch) is None

    head = subprocess.run(
        ["git", "-C", str(CCBENCH), "rev-parse", "HEAD"],
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    assert head == PIN_FULL
    subprocess.run(
        ["git", "-C", str(CCBENCH), "apply", "--check", str(PATCH)],
        check=True,
        capture_output=True,
        text=True,
    )

    for macro in (
        "BACKOFF_INCR_MILLI",
        "BACKOFF_MAX_US",
        "BACKOFF_UPDATE_US",
    ):
        assert re.search(
            rf"^\+#ifndef {macro}\n\+#error ", patch, flags=re.MULTILINE
        )
        assert f"CCBENCH_{macro}" in patch
    assert patch.count("static_assert(") == 3


def test_pbs_restores_plus_lists_and_is_compute_only() -> None:
    subprocess.run(
        ["bash", "-n", str(PBS)],
        check=True,
        capture_output=True,
        text=True,
    )
    text = PBS.read_text(encoding="utf-8")
    assert "#PBS -l elapstim_req=00:40:00" in text
    assert (
        "# qsub -v 'IZANAGI_T2187_CELLS="
        "none:0:100:1000:10+stock:1:100:1000:10"
    ) in text
    assert "${CELLS_RAW//+/,}" in text
    assert "${WORKLOADS_RAW//+/,}" in text
    assert "${THREADS_RAW//+/,}" in text
    assert "write-heavy+balanced+read-heavy" in text
    assert "^bnode[0-9]+" in text
    assert "--cells \"$CELLS\"" in text
    assert "--workloads \"$WORKLOADS\"" in text
    assert "--threads \"$THREADS\"" in text


def test_pbs_rejects_legacy_semicolon_list_delimiter() -> None:
    text = PBS.read_text(encoding="utf-8")
    assert '"$CELLS_RAW" == *";"*' in text
    assert '"$WORKLOADS_RAW" == *";"*' in text
    assert r'^[0-9]+(\+[0-9]+)*$' in text
    assert "${CELLS_RAW//;/,}" not in text
    assert "${WORKLOADS_RAW//;/,}" not in text
    assert "${THREADS_RAW//;/,}" not in text


def test_public_certification_contract_runs_full_real_verifier_path_and_saves_create_only(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    events: list[str] = []
    _install_certification_runtime(monkeypatch, tmp_path, events=events)
    real_run_verifier = probe._run_verifier

    def observed_verifier(
        trace_dir, expected_commits, timeout_s, protocol, ccbench_root
    ):
        events.append(
            "positive-control"
            if Path(trace_dir).resolve() == probe.POSITIVE_CONTROL_TRACE.resolve()
            else "target-verifier"
        )
        return real_run_verifier(
            trace_dir, expected_commits, timeout_s, protocol, ccbench_root
        )

    monkeypatch.setattr(probe, "_run_verifier", observed_verifier)
    argv = _certify_argv(tmp_path)
    assert probe.main(argv) == 0
    assert events == ["build", "run", "positive-control", "target-verifier"]

    out = Path(argv[-1])
    document = json.loads(out.read_text(encoding="utf-8"))
    assert document["terminal_status"] == "certified"
    assert document["build_trace_enabled"] is True
    assert document["run"] == {
        "exit_code": 0,
        "trace_c_lines": 2,
        "commit_count": 2,
        "batch_commit_count": 0,
        "abort_count_stdout": 1,
    }
    assert document["positive_control"]["exit_code"] == 1
    assert document["target_verifier"]["exit_code"] == 0
    assert document["target_verifier"]["argv"][:3] == [
        sys.executable,
        "-B",
        "orchestrator/verify.py",
    ]
    assert "--lenient" not in document["target_verifier"]["argv"]
    assert document["proof_surface"]["protocol"] == probe.CERT_PROTOCOL
    assert document["proof_surface"]["source_snapshot_identity"] == document[
        "source_evidence"
    ]
    proof_root = document["proof_surface"]["ccbench_root"]
    for invocation in (
        document["positive_control"],
        document["target_verifier"],
    ):
        invocation_argv = invocation["argv"]
        assert invocation_argv[invocation_argv.index("--protocol") + 1] == "silo"
        assert invocation_argv[invocation_argv.index("--ccbench-root") + 1] == proof_root
    assert document["target_verifier"]["environment"] == {
        "PYTHONDONTWRITEBYTECODE": "1"
    }
    assert document["verifier_json"] == document["target_verifier"]["json"]
    assert document["abort_count"] == 1
    assert document["abort_reasons"] == {}
    assert document["build_cache_key"].endswith("_t1")
    assert re.fullmatch(r"[0-9a-f]{64}", document["build_admission_receipt_sha256"])
    assert document["source_evidence"]["ccbench_commit"] == probe.CURRENT_PIN
    assert re.fullmatch(
        r"[0-9a-f]{64}", document["source_evidence"]["source_bytes_sha256"]
    )
    assert document["verifier_identity"] == document["expected_verifier_identity"]
    assert document["trace_manifest"]["file_count"] == 1
    assert document["run_phase"]["cpu_over_elapsed"] is not None
    assert document["verify_phase"]["cpu_over_elapsed"] is not None
    assert document["job_phase"]["cpu_over_elapsed"] is not None
    assert document["prologue_phase"] == {
        "elapsed_seconds": 2.5,
        "cpu_seconds": 1.25,
        "cpu_over_elapsed": 0.5,
    }
    assert document["job_phase"]["elapsed_seconds"] >= 2.5
    assert document["job_phase"]["cpu_seconds"] >= 1.25
    assert "run_phase" in document and "verify_phase" in document
    assert Path(document["trace_directory"]).is_dir()
    assert not (tmp_path / "group.json").exists()

    with pytest.raises(FileExistsError, match="refusing to overwrite"):
        probe.main(argv)


def test_trace_build_budget_is_a_hard_deadline() -> None:
    with pytest.raises(probe.CertificationReject) as caught:
        probe._run_build_with_deadline(lambda: time.sleep(5.0), 0.05)
    assert caught.value.reason == "trace-build-budget-exceeded"


def test_run_and_verify_phase_measurements_keep_distinct_meanings(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    _install_certification_runtime(monkeypatch, tmp_path)
    measurements = iter(
        (
            {"elapsed_seconds": 11.0, "cpu_seconds": 22.0, "cpu_over_elapsed": 2.0},
            {"elapsed_seconds": 3.0, "cpu_seconds": 12.0, "cpu_over_elapsed": 4.0},
        )
    )
    monkeypatch.setattr(probe, "_phase_measurement", lambda *_args: next(measurements))
    real_run_verifier = probe._run_verifier

    def phase_tagged_verifier(
        trace_dir, expected_commits, timeout_s, protocol, ccbench_root
    ):
        invocation = real_run_verifier(
            trace_dir, expected_commits, timeout_s, protocol, ccbench_root
        )
        if Path(trace_dir).resolve() != probe.POSITIVE_CONTROL_TRACE.resolve():
            invocation.update(
                elapsed_seconds=5.0,
                cpu_seconds=4.0,
                cpu_over_elapsed=0.8,
                max_rss_kib=123,
            )
        return invocation

    monkeypatch.setattr(probe, "_run_verifier", phase_tagged_verifier)
    argv = _certify_argv(tmp_path)
    assert probe.main(argv) == 0
    document = json.loads(Path(argv[-1]).read_text(encoding="utf-8"))
    assert document["run_phase"] == {
        "elapsed_seconds": 3.0,
        "cpu_seconds": 12.0,
        "cpu_over_elapsed": 4.0,
    }
    assert document["verify_phase"] == {
        "elapsed_seconds": 5.0,
        "cpu_seconds": 4.0,
        "cpu_over_elapsed": 0.8,
        "max_rss_kib": 123,
    }


@pytest.mark.parametrize(
    ("trace_text", "abort_count_stdout", "expected_reason"),
    (
        (SERIAL_TRACE, None, "target-abort-empty"),
        (SERIAL_TRACE, 0, "target-abort-empty"),
        (SERIAL_TRACE, -1, "target-abort-empty"),
        (SERIAL_TRACE, "1", "target-abort-empty"),
        (SERIAL_TRACE_WITHOUT_EDGES, 1, "target-edges-empty"),
    ),
    ids=("M17-none", "M17-zero", "M17-negative", "M17-non-int", "M2-edges"),
)
def test_public_certification_rejects_nonexercising_target_for_one_reason(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    trace_text: str,
    abort_count_stdout: object,
    expected_reason: str,
) -> None:
    _install_certification_runtime(
        monkeypatch,
        tmp_path,
        trace_text=trace_text,
        abort_count_stdout=abort_count_stdout,
    )
    argv = _certify_argv(tmp_path)
    assert probe.main(argv) == 1
    document = json.loads(Path(argv[-1]).read_text(encoding="utf-8"))
    assert document["terminal_status"] == "rejected"
    assert document["reject_reason"] == expected_reason


def test_public_certification_rejects_substituted_target_trace_only(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    _install_certification_runtime(monkeypatch, tmp_path)
    real_run_verifier = probe._run_verifier

    def substitute(trace_dir, expected_commits, timeout_s, protocol, ccbench_root):
        if Path(trace_dir).resolve() == probe.POSITIVE_CONTROL_TRACE.resolve():
            return real_run_verifier(
                trace_dir, expected_commits, timeout_s, protocol, ccbench_root
            )
        return real_run_verifier(
            G6_SERIAL_TRACE, 200, timeout_s, protocol, ccbench_root
        )

    monkeypatch.setattr(probe, "_run_verifier", substitute)
    argv = _certify_argv(tmp_path)
    assert probe.main(argv) == 1
    document = json.loads(Path(argv[-1]).read_text(encoding="utf-8"))
    assert document["reject_reason"] == "target-trace-dir-mismatch"


def test_public_certification_rejects_target_exit_three_only(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    _install_certification_runtime(monkeypatch, tmp_path)
    real_run_verifier = probe._run_verifier

    def exit_three(trace_dir, expected_commits, timeout_s, protocol, ccbench_root):
        invocation = real_run_verifier(
            trace_dir, expected_commits, timeout_s, protocol, ccbench_root
        )
        if Path(trace_dir).resolve() != probe.POSITIVE_CONTROL_TRACE.resolve():
            invocation["exit_code"] = 3
        return invocation

    monkeypatch.setattr(probe, "_run_verifier", exit_three)
    argv = _certify_argv(tmp_path)
    assert probe.main(argv) == 1
    document = json.loads(Path(argv[-1]).read_text(encoding="utf-8"))
    assert document["reject_reason"] == "target-verifier-exit"


def test_public_certification_rejects_lenient_argv_only(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    _install_certification_runtime(monkeypatch, tmp_path)
    real_argv = probe._verifier_argv

    def lenient_argv(trace_dir, expected_commits, protocol, ccbench_root):
        return [
            *real_argv(trace_dir, expected_commits, protocol, ccbench_root),
            "--lenient",
        ]

    monkeypatch.setattr(probe, "_verifier_argv", lenient_argv)
    argv = _certify_argv(tmp_path)
    assert probe.main(argv) == 1
    document = json.loads(Path(argv[-1]).read_text(encoding="utf-8"))
    assert document["reject_reason"] == "verifier-argv-contract"


@pytest.mark.parametrize("surface", ("positive", "target"))
@pytest.mark.parametrize("option", ("--protocol", "--ccbench-root"))
@pytest.mark.parametrize("mutation", ("missing", "mismatch"))
def test_public_certification_rejects_unbound_proof_surface_argv_for_one_reason(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    surface: str,
    option: str,
    mutation: str,
) -> None:
    _install_certification_runtime(monkeypatch, tmp_path)
    real_argv = probe._verifier_argv

    def mutate_surface(trace_dir, expected_commits, protocol, ccbench_root):
        invocation_argv = real_argv(
            trace_dir, expected_commits, protocol, ccbench_root
        )
        is_positive = Path(trace_dir).resolve() == probe.POSITIVE_CONTROL_TRACE.resolve()
        if (surface == "positive") == is_positive:
            index = invocation_argv.index(option)
            if mutation == "missing":
                del invocation_argv[index : index + 2]
            else:
                invocation_argv[index + 1] = "not-the-bound-value"
        return invocation_argv

    monkeypatch.setattr(probe, "_verifier_argv", mutate_surface)
    argv = _certify_argv(tmp_path)
    assert probe.main(argv) == 1
    document = json.loads(Path(argv[-1]).read_text(encoding="utf-8"))
    assert document["reject_reason"] == "verifier-argv-contract"


def test_public_certification_rejects_non_silo_genome_before_verification(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    _install_certification_runtime(monkeypatch, tmp_path)
    monkeypatch.setattr(
        probe,
        "genome_for",
        lambda _cell, **_kwargs: probe.Genome("si", {}),
    )
    argv = _certify_argv(tmp_path)
    assert probe.main(argv) == 1
    document = json.loads(Path(argv[-1]).read_text(encoding="utf-8"))
    assert document["reject_reason"] == "certification-protocol-mismatch"


def test_public_certification_rejects_verifier_identity_drift_only(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    _install_certification_runtime(monkeypatch, tmp_path)
    argv = _certify_argv(tmp_path)
    calls = 0

    def drifting_identity():
        nonlocal calls
        calls += 1
        return {
            "repository_commit": "f" * 40,
            "module_sha256": {"x.py": f"{calls:064x}"},
        }

    monkeypatch.setattr(probe, "_verifier_identity", drifting_identity)
    assert probe.main(argv) == 1
    document = json.loads(Path(argv[-1]).read_text(encoding="utf-8"))
    assert document["reject_reason"] == "verifier-identity-mismatch"


def test_public_certification_rejects_post_verifier_identity_drift_only(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    _install_certification_runtime(monkeypatch, tmp_path)
    argv = _certify_argv(tmp_path)
    expected = json.loads(
        Path(argv[argv.index("--expected-verifier-identity") + 1]).read_text(
            encoding="utf-8"
        )
    )
    calls = 0

    def after_drift_identity():
        nonlocal calls
        calls += 1
        if calls == 1:
            return expected
        return {
            "repository_commit": "f" * 40,
            "module_sha256": {"x.py": "a" * 64},
        }

    monkeypatch.setattr(probe, "_verifier_identity", after_drift_identity)
    assert probe.main(argv) == 1
    document = json.loads(Path(argv[-1]).read_text(encoding="utf-8"))
    assert document["reject_reason"] == "verifier-identity-mismatch"


def test_real_serial_fixture_with_positive_stdout_abort_satisfies_abort_gate() -> None:
    invocation = probe._run_verifier(
        G6_SERIAL_TRACE, 200, 30.0, probe.CERT_PROTOCOL, CCBENCH
    )
    identity = probe._verifier_identity()
    trace_result = SimpleNamespace(
        returncode=0,
        trace_c_lines=200,
        commit_count_witness=200,
        batch_commit_count_witness=0,
        abort_counts=7,
    )
    document, result = probe._validate_target(
        invocation,
        G6_SERIAL_TRACE,
        trace_result,
        identity,
        identity,
        probe.CERT_PROTOCOL,
        CCBENCH,
    )
    assert result["certified"] is True
    assert result["stats"]["abort_reasons"] == {}
    assert document["certified_serializable"] == 1


def test_target_validation_rejects_nonempty_anomalies_from_real_serial_fixture(
) -> None:
    invocation = probe._run_verifier(
        G6_SERIAL_TRACE, 200, 30.0, probe.CERT_PROTOCOL, CCBENCH
    )
    identity = probe._verifier_identity()
    invocation["json"]["results"][0]["anomalies"] = [
        {"phenomenon": "G2", "edges": []}
    ]
    trace_result = SimpleNamespace(
        returncode=0,
        trace_c_lines=200,
        commit_count_witness=200,
        batch_commit_count_witness=0,
        abort_counts=7,
    )
    with pytest.raises(probe.CertificationReject) as caught:
        probe._validate_target(
            invocation,
            G6_SERIAL_TRACE,
            trace_result,
            identity,
            identity,
            probe.CERT_PROTOCOL,
            CCBENCH,
        )
    assert caught.value.reason == "target-verdict"


def test_positive_control_real_fixture_accepts_wr_without_v_ver() -> None:
    invocation = probe._run_verifier(
        probe.POSITIVE_CONTROL_TRACE,
        probe.POSITIVE_CONTROL_EXPECTED_COMMITS,
        probe.POSITIVE_CONTROL_TIMEOUT_S,
        probe.CERT_PROTOCOL,
        CCBENCH,
    )
    probe._validate_positive_control(invocation, probe.CERT_PROTOCOL, CCBENCH)
    wr_reasons = [
        reason
        for anomaly in invocation["json"]["results"][0]["anomalies"]
        for edge in anomaly["edges"]
        for reason in edge["reasons"]
        if reason["type"] == "wr"
    ]
    assert wr_reasons
    assert all("u_ver" in reason and "v_ver" not in reason for reason in wr_reasons)


def test_default_mode_and_lazy_import_surface_remain_performance() -> None:
    parser = probe._argument_parser()
    args = parser.parse_args(["--cells", VALID_CELLS, "--out", "unused.json"])
    assert args.mode == "performance"

    tree = ast.parse(DRIVER.read_text(encoding="utf-8"), filename=str(DRIVER))
    top_imports = [
        node
        for node in tree.body
        if isinstance(node, (ast.Import, ast.ImportFrom))
    ]
    assert all(
        not (
            isinstance(node, ast.ImportFrom)
            and (
                node.module == "orchestrator.campaign.pipeline"
                or (
                    node.module == "orchestrator.campaign"
                    and any(alias.name == "pipeline" for alias in node.names)
                )
            )
        )
        and not (
            isinstance(node, ast.Import)
            and any(
                alias.name == "orchestrator.campaign.pipeline"
                for alias in node.names
            )
        )
        for node in top_imports
    )


def test_public_default_path_never_dispatches_to_certify(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    out = tmp_path / "existing.json"
    out.write_text("existing\n", encoding="utf-8")
    monkeypatch.setattr(
        probe,
        "_certify_main",
        lambda _args: (_ for _ in ()).throw(AssertionError("certify dispatched")),
    )
    with pytest.raises(FileExistsError, match="refusing to overwrite"):
        probe.main(["--cells", VALID_CELLS, "--out", str(out)])


def test_public_performance_rejection_path_loads_without_pipeline(
    tmp_path: Path,
) -> None:
    out = tmp_path / "existing.json"
    out.write_text("existing\n", encoding="utf-8")
    program = f"""
import importlib.abc
import importlib.util
import pathlib
import sys

class BlockPipeline(importlib.abc.MetaPathFinder):
    def find_spec(self, fullname, path=None, target=None):
        if fullname == "orchestrator.campaign.pipeline":
            raise ImportError("pipeline intentionally unavailable")
        return None

sys.meta_path.insert(0, BlockPipeline())
driver = pathlib.Path({str(DRIVER)!r})
spec = importlib.util.spec_from_file_location("t2187_lazy_import_probe", driver)
module = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = module
spec.loader.exec_module(module)
try:
    module.main(["--cells", {VALID_CELLS!r}, "--out", {str(out)!r}])
except FileExistsError:
    raise SystemExit(0)
raise SystemExit(9)
"""
    completed = subprocess.run(
        [sys.executable, "-B", "-c", program],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    assert completed.returncode == 0, completed.stderr


@pytest.mark.parametrize(
    ("old", "new", "reason"),
    (
        (CERT_CELL, "stock:1:100:1000:10", "certification-cell-mismatch"),
        ("balanced", "write-heavy,balanced", "certification-workload-mismatch"),
        ("48", "24", "certification-workload-shape-mismatch"),
        ("3", "1", "certification-workload-shape-mismatch"),
        ("0", "8", "certification-slot-mismatch"),
    ),
    ids=("cell", "workload-set", "threads", "extime", "slot"),
)
def test_public_certification_exact_axes_reject_widening(
    tmp_path: Path, old: str, new: str, reason: str
) -> None:
    argv = _certify_argv(tmp_path)
    index = argv.index(old)
    argv[index] = new
    with pytest.raises(probe.CertificationReject) as caught:
        probe.main(argv)
    assert caught.value.reason == reason


def test_certification_budget_includes_pbs_prologue(tmp_path: Path) -> None:
    parser = probe._argument_parser()
    argv = _certify_argv(tmp_path)
    argv.extend(("--outer-walltime-s", "7200"))
    args = parser.parse_args(argv)
    with pytest.raises(probe.CertificationReject) as caught:
        probe._certification_contract(args)
    assert caught.value.reason == "certification-time-budget-invalid"


def test_public_certification_rejects_trace_disabled_cache_identity(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    _install_certification_runtime(monkeypatch, tmp_path)
    monkeypatch.setattr(probe.buildcache, "cache_key", lambda *_args, **_kwargs: "silo_x_t0")
    argv = _certify_argv(tmp_path)
    assert probe.main(argv) == 1
    document = json.loads(Path(argv[-1]).read_text(encoding="utf-8"))
    assert document["reject_reason"] == "trace-build-identity"


def test_performance_artifact_requires_preregistered_sha(tmp_path: Path) -> None:
    performance = tmp_path / "performance.json"
    performance.write_text(
        json.dumps(
            {
                "schema_version": probe.SCHEMA_VERSION,
                "kind": "performance-only-probe",
                "not_certified": probe.NOT_CERTIFIED,
            }
        )
        + "\n",
        encoding="utf-8",
    )
    with pytest.raises(probe.CertificationReject) as caught:
        probe._performance_artifact_identity(performance, "0" * 64)
    assert caught.value.reason == "performance-artifact-identity-mismatch"


def test_verifier_identity_manifest_requires_preregistered_sha(tmp_path: Path) -> None:
    manifest = tmp_path / "verifier-identity.json"
    manifest.write_text(
        json.dumps(
            {
                "repository_commit": "f" * 40,
                "module_sha256": {"x.py": "a" * 64},
            }
        ),
        encoding="utf-8",
    )
    with pytest.raises(probe.CertificationReject) as caught:
        probe._load_expected_verifier_identity(manifest, "0" * 64)
    assert caught.value.reason == "verifier-identity-mismatch"


def test_group_receipt_requires_exact_24_terminal_request_set(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    _install_certification_runtime(monkeypatch, tmp_path)
    with monkeypatch.context() as source_run_patch:
        source_run_patch.setattr(
            probe, "_try_finalize_group", lambda *_args, **_kwargs: False
        )
        source_argv = _certify_argv(tmp_path)
        assert probe.main(source_argv) == 0
    source_document = json.loads(Path(source_argv[-1]).read_text(encoding="utf-8"))
    source_trace = Path(source_document["trace_directory"])
    performance = Path(source_argv[source_argv.index("--performance-artifact") + 1])
    performance_sha256 = hashlib.sha256(performance.read_bytes()).hexdigest()
    attempt_id = source_document["attempt_id"]
    identity = source_document["verifier_identity"]
    identity_file_sha256 = source_document[
        "expected_verifier_identity_file_sha256"
    ]
    real_genome_for = probe.genome_for

    def synthetic_group_genome(
        cell, *, backoff_trace=False, step_policy_seed=None
    ):
        if cell == probe.CERT_TUNED_CELL and backoff_trace is False:
            return SimpleNamespace(canonical=lambda: "synthetic-canonical-genome")
        return real_genome_for(
            cell,
            backoff_trace=backoff_trace,
            step_policy_seed=step_policy_seed,
        )

    monkeypatch.setattr(probe, "genome_for", synthetic_group_genome)
    result_files = []
    valid_documents = []
    for workload in probe.CERT_WORKLOADS:
        for slot in probe.CERT_SLOTS:
            trace_dir = tmp_path / f"group-trace-{workload}-{slot}"
            shutil.copytree(source_trace, trace_dir)
            document = copy.deepcopy(source_document)
            document["workload"] = workload
            document["workload_flags"] = {
                **probe.WORKLOADS[workload],
                "ycsb_tuple_num": str(probe.CERT_RECORDS),
                "thread_num": str(document["threads"]),
                "extime": str(probe.CERT_EXTIME),
            }
            document["independent_run_slot"] = slot
            document["pbs_jobid"] = f"{workload}-{slot}"
            document["source_evidence"]["source_bytes_sha256"] = hashlib.sha256(
                b"synthetic-shared-source-bytes"
            ).hexdigest()
            document["source_evidence"]["genome_sha256"] = hashlib.sha256(
                b"synthetic-canonical-genome"
            ).hexdigest()
            document["proof_surface"]["source_snapshot_identity"] = copy.deepcopy(
                document["source_evidence"]
            )
            document["genome"] = "synthetic-canonical-genome"
            document["binary_sha256"] = hashlib.sha256(
                b"synthetic-shared-binary"
            ).hexdigest()
            document["trace_directory"] = str(trace_dir.resolve())
            document["target_verifier"]["argv"][3] = str(trace_dir.resolve())
            document["target_verifier"]["json"]["results"][0]["trace_dir"] = str(
                trace_dir.resolve()
            )
            document["target_verifier"]["stdout"] = json.dumps(
                document["target_verifier"]["json"]
            )
            document["verifier_json"] = document["target_verifier"]["json"]
            document["trace_manifest"] = probe._trace_manifest(trace_dir)
            path = tmp_path / f"group-result-{workload}-slot{slot}.json"
            path.write_text(
                json.dumps(document) + "\n",
                encoding="utf-8",
            )
            result_files.append(path)
            valid_documents.append(copy.deepcopy(document))

    with pytest.raises(probe.CertificationReject) as caught:
        probe._group_receipt_payload(
            result_files[:-1],
            performance,
            performance_sha256,
            attempt_id,
            identity,
            identity_file_sha256,
        )
    assert caught.value.reason == "group-incomplete"

    receipt = probe._group_receipt_payload(
        result_files,
        performance,
        performance_sha256,
        attempt_id,
        identity,
        identity_file_sha256,
    )
    assert receipt["complete"] is True
    assert receipt["expected_requests"] == receipt["terminal_requests"] == 24
    assert len(receipt["results"]) == 24
    assert receipt["claim"] == probe.ALLOWED_GROUP_CLAIM
    assert len(
        {
            row["source_evidence"]["source_bytes_sha256"]
            for row in receipt["results"]
        }
    ) == 1
    assert len(
        {
            row["source_evidence"]["genome_sha256"]
            for row in receipt["results"]
        }
    ) == 1
    assert {row["genome"] for row in receipt["results"]} == {
        "synthetic-canonical-genome"
    }
    assert receipt["proof_surface"]["protocol"] == probe.CERT_PROTOCOL
    assert receipt["proof_surface"]["source_snapshot_identity"] == valid_documents[
        0
    ]["source_evidence"]
    assert receipt["source_evidence"] == valid_documents[0]["source_evidence"]
    assert receipt["genome"] == "synthetic-canonical-genome"
    assert {
        row["proof_surface"]["protocol"] for row in receipt["results"]
    } == {probe.CERT_PROTOCOL}
    assert all(row["build_trace_enabled"] is True for row in receipt["results"])
    assert len({row["patch_sha256"] for row in receipt["results"]}) == 1
    assert len(
        {row["counterfactual_patch_sha256"] for row in receipt["results"]}
    ) == 1
    assert len({row["ccbench_commit"] for row in receipt["results"]}) == 1
    assert len({row["trace_dir"] for row in receipt["results"]}) == 24
    assert all(row["build_cache_key"].endswith("_t1") for row in receipt["results"])
    assert probe._group_receipt_payload(
        result_files,
        performance,
        performance_sha256,
        attempt_id,
        identity,
        identity_file_sha256,
    ) == receipt

    def write_documents(documents: list[dict]) -> None:
        for path, document in zip(result_files, documents):
            path.write_text(json.dumps(document) + "\n", encoding="utf-8")

    for mutation in (
        "source-bytes-sha256",
        "genome-sha256",
        "genome",
        "patch-sha256",
        "dynamic-patch-sha256",
        "counterfactual-patch-sha256",
        "patch-stack-order",
        "ccbench-commit",
        "repo-head",
        "cell-field",
        "claim",
        "trace-dir-duplicate",
        "trace-disabled",
        "source-src-token",
        "proof-snapshot-detached",
        "proof-protocol",
    ):
        candidates = copy.deepcopy(valid_documents)
        if mutation == "source-bytes-sha256":
            candidates[0]["source_evidence"]["source_bytes_sha256"] = "3" * 64
            candidates[0]["proof_surface"]["source_snapshot_identity"] = copy.deepcopy(
                candidates[0]["source_evidence"]
            )
        elif mutation == "genome-sha256":
            candidates[0]["source_evidence"]["genome_sha256"] = "4" * 64
            candidates[0]["proof_surface"]["source_snapshot_identity"] = copy.deepcopy(
                candidates[0]["source_evidence"]
            )
        elif mutation == "genome":
            candidates[0]["genome"] = "synthetic-other-genome"
        elif mutation == "patch-sha256":
            candidates[0]["patch_sha256"] = "0" * 64
        elif mutation == "dynamic-patch-sha256":
            candidates[0]["dynamic_patch_sha256"] = "0" * 64
        elif mutation == "counterfactual-patch-sha256":
            candidates[0]["counterfactual_patch_sha256"] = "0" * 64
        elif mutation == "patch-stack-order":
            candidates[0]["patch_stack"] = list(
                reversed(candidates[0]["patch_stack"])
            )
        elif mutation == "ccbench-commit":
            candidates[0]["ccbench_commit"] = "f" * 40
        elif mutation == "repo-head":
            candidates[0]["repo_head"] = "f" * 40
        elif mutation == "cell-field":
            candidates[0]["count_window"] = 1
        elif mutation == "claim":
            candidates[0]["allowed_group_claim"] += " drift"
        elif mutation == "trace-dir-duplicate":
            donor = candidates[0]
            candidate = candidates[1]
            candidate["trace_directory"] = donor["trace_directory"]
            candidate["target_verifier"]["argv"][3] = donor["trace_directory"]
            candidate["target_verifier"]["json"]["results"][0]["trace_dir"] = (
                donor["trace_directory"]
            )
            candidate["target_verifier"]["stdout"] = json.dumps(
                candidate["target_verifier"]["json"]
            )
            candidate["verifier_json"] = candidate["target_verifier"]["json"]
            candidate["trace_manifest"] = donor["trace_manifest"]
        elif mutation == "trace-disabled":
            candidates[0]["build_trace_enabled"] = False
        elif mutation == "source-src-token":
            candidates[0]["source_evidence"]["src_token"] = "different-snapshot"
            candidates[0]["proof_surface"]["source_snapshot_identity"] = copy.deepcopy(
                candidates[0]["source_evidence"]
            )
        elif mutation == "proof-snapshot-detached":
            candidates[0]["proof_surface"]["source_snapshot_identity"] = {
                **candidates[0]["source_evidence"],
                "source_bytes_sha256": "5" * 64,
            }
        elif mutation == "proof-protocol":
            candidates[0]["proof_surface"]["protocol"] = "si"
        write_documents(candidates)
        with pytest.raises(probe.CertificationReject) as caught:
            probe._group_receipt_payload(
                result_files,
                performance,
                performance_sha256,
                attempt_id,
                identity,
                identity_file_sha256,
            )
        if mutation in {"proof-snapshot-detached", "proof-protocol"}:
            expected_reason = "group-proof-surface-mismatch"
        elif mutation in {"cell-field", "claim"}:
            expected_reason = "group-workload-contract-mismatch"
        else:
            expected_reason = "group-build-identity-mismatch"
        assert caught.value.reason == expected_reason, mutation

    write_documents(valid_documents)

    failed_group = tmp_path / "failed-group.json"
    candidates = copy.deepcopy(valid_documents)
    candidates[0]["allowed_group_claim"] += " drift"
    write_documents(candidates)
    assert probe._try_finalize_group(
        result_files,
        failed_group,
        performance,
        performance_sha256,
        attempt_id,
        identity,
        identity_file_sha256,
    ) is False
    failure_path = tmp_path / f"group-failure-{attempt_id}.json"
    failure = json.loads(failure_path.read_text(encoding="utf-8"))
    assert set(failure) == {"reason", "detail", "attempt_id", "failed_utc"}
    assert failure["reason"] == "group-workload-contract-mismatch"
    assert failure["attempt_id"] == attempt_id
    assert isinstance(failure["detail"], str) and failure["detail"]
    assert isinstance(failure["failed_utc"], str) and failure["failed_utc"]
    original_failure = failure_path.read_bytes()
    assert probe._try_finalize_group(
        result_files,
        failed_group,
        performance,
        performance_sha256,
        attempt_id,
        identity,
        identity_file_sha256,
    ) is False
    assert failure_path.read_bytes() == original_failure

    write_documents(valid_documents)

    concurrent_group = tmp_path / "group-concurrent.json"
    finalize_barrier = threading.Barrier(2)

    def finalize_concurrently():
        finalize_barrier.wait()
        return probe._try_finalize_group(
            result_files,
            concurrent_group,
            performance,
            performance_sha256,
            attempt_id,
            identity,
            identity_file_sha256,
        )

    with ThreadPoolExecutor(max_workers=2) as executor:
        outcomes = list(executor.map(lambda _index: finalize_concurrently(), range(2)))
    assert outcomes == [True, True]
    assert json.loads(concurrent_group.read_text(encoding="utf-8"))["complete"] is True

    for certified_count in (0, 23):
        for index, (path, document) in enumerate(zip(result_files, valid_documents)):
            candidate = copy.deepcopy(document)
            if index >= certified_count:
                candidate["terminal_status"] = "rejected"
                candidate["certified"] = False
                candidate.pop("certification_gate", None)
                candidate["reject_reason"] = "synthetic-reject"
            path.write_text(json.dumps(candidate) + "\n", encoding="utf-8")
        group_out = tmp_path / f"group-{certified_count}.json"
        assert probe._try_finalize_group(
            result_files,
            group_out,
            performance,
            performance_sha256,
            attempt_id,
            identity,
            identity_file_sha256,
        ) is False
        assert not group_out.exists()


def test_group_receipt_rejects_status_only_certification_json(
    tmp_path: Path,
) -> None:
    performance = tmp_path / "performance.json"
    performance.write_text(
        json.dumps(
            {
                "schema_version": probe.SCHEMA_VERSION,
                "kind": "performance-only-probe",
                "not_certified": probe.NOT_CERTIFIED,
            }
        )
        + "\n",
        encoding="utf-8",
    )
    identity = {
        "repository_commit": "f" * 40,
        "module_sha256": {"x.py": "a" * 64},
    }
    result_files = []
    for workload in probe.CERT_WORKLOADS:
        for slot in probe.CERT_SLOTS:
            path = tmp_path / f"status-only-{workload}-{slot}.json"
            path.write_text(
                json.dumps(
                    {
                        "schema_version": probe.CERTIFICATION_SCHEMA_VERSION,
                        "workload": workload,
                        "independent_run_slot": slot,
                        "terminal_status": "certified",
                    }
                ),
                encoding="utf-8",
            )
            result_files.append(path)
    with pytest.raises(probe.CertificationReject) as caught:
        probe._group_receipt_payload(
            result_files,
            performance,
            hashlib.sha256(performance.read_bytes()).hexdigest(),
            "attempt-test",
            identity,
            "b" * 64,
        )
    assert caught.value.reason == "group-result-not-certified"


def test_public_certification_creates_group_only_after_all_24_requests(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    _install_certification_runtime(monkeypatch, tmp_path)
    pairs = [
        (workload, slot)
        for workload in probe.CERT_WORKLOADS
        for slot in probe.CERT_SLOTS
    ]
    (tmp_path / "stale-duplicate.json").write_text(
        json.dumps(
            {
                "schema_version": probe.CERTIFICATION_SCHEMA_VERSION,
                "workload": "balanced",
                "independent_run_slot": 0,
                "terminal_status": "certified",
            }
        ),
        encoding="utf-8",
    )
    for index, (workload, slot) in enumerate(pairs):
        private_tmp = tmp_path / f"runtime-{index}"
        private_tmp.mkdir()
        monkeypatch.setenv("TMPDIR", str(private_tmp))
        monkeypatch.setenv("PBS_JOBID", f"{10000 + index}.test")
        argv = _certify_argv(tmp_path, workload=workload, slot=slot)
        assert probe.main(argv) == 0
        document = json.loads(Path(argv[-1]).read_text(encoding="utf-8"))
        if index < 23:
            assert not (tmp_path / "group.json").exists()
            assert Path(document["trace_directory"]).is_dir()

    receipt = json.loads((tmp_path / "group.json").read_text(encoding="utf-8"))
    assert receipt["complete"] is True
    assert receipt["terminal_requests"] == 24
    assert {
        (row["workload"], row["independent_run_slot"])
        for row in receipt["results"]
    } == set(pairs)
    assert all(not Path(row["trace_dir"]).exists() for row in receipt["results"])


def test_pbs_certify_mode_preserves_literal_performance_exec_and_exact_axes() -> None:
    text = PBS.read_text(encoding="utf-8")
    assert text.splitlines()[:6] == [
        "#!/bin/bash",
        "#PBS -A SFC",
        "#PBS -q gen_S",
        "#PBS -b 1",
        "#PBS -l elapstim_req=00:40:00",
        "#PBS -N izanagi-t2187",
    ]
    assert "MODE=${IZANAGI_T2187_MODE:-performance}" in text
    assert '"$CERT_TUNED_CELL"|"$CERT_DYNAMIC_CELL")' in text
    assert '"$CERT_COHORT2_POLICY1_CELL")' in text
    assert '"$CERT_COHORT2_POLICY2_CELL")' in text
    assert '[[ "$THREADS_RAW" == 24 || "$THREADS_RAW" == 48 ]]' in text
    assert "--mode certify" in text
    assert "qsub -l elapstim_req=02:15:00" in text
    assert "IZANAGI_T2187_OUTER_WALLTIME_S=8100" in text
    assert '--outer-walltime-s "$OUTER_WALLTIME_S"' in text
    assert '--verifier-timeout-s "$VERIFIER_TIMEOUT_S"' in text
    assert '--prologue-budget-s "$PROLOGUE_BUDGET_S"' in text
    assert '--performance-artifact-sha256 "$PERFORMANCE_ARTIFACT_SHA256"' in text
    assert '--expected-verifier-identity "$EXPECTED_VERIFIER_IDENTITY"' in text
    assert (
        '--expected-verifier-identity-sha256 '
        '"$EXPECTED_VERIFIER_IDENTITY_SHA256"'
    ) in text
    assert '"${GROUP_RESULT_ARGS[@]}"' in text
    performance_branch = text.split(
        'if [[ "$MODE" == performance ]]; then', 1
    )[1].split('OUT="$OUT_DIR/certify-', 1)[0]
    assert "--mode" not in performance_branch
    assert '--extime "$EXTIME"' in performance_branch
    assert (
        '--backoff-trace-terminal-us "$CCBENCH_BACKOFF_TRACE_TERMINAL_US"'
        in performance_branch
    )


def test_five_field_cells_preserve_legacy_cell_and_genome_bytes() -> None:
    cell = probe.parse_cells(CERT_CELL)[0]
    assert cell == probe.Cell("tuned", 1, 1.0, 1000, 2560)
    assert cell.extended is False
    genome = probe.genome_for(cell)
    assert genome.canonical() == (
        "silo|BACKOFF_INCR_MILLI=1000,BACKOFF_MAX_US=1000,"
        "BACKOFF_UPDATE_US=2560,BACK_OFF=1,"
        "NO_WAIT_LOCKING_IN_VALIDATION=1,NO_WAIT_OF_TICTOC=0,WAL=0"
    )
    assert genome.cmake_defines() == [
        "-DCCBENCH_BACKOFF_INCR_MILLI=1000",
        "-DCCBENCH_BACKOFF_MAX_US=1000",
        "-DCCBENCH_BACKOFF_UPDATE_US=2560",
        "-DCCBENCH_BACK_OFF=1",
        "-DCCBENCH_NO_WAIT_LOCKING_IN_VALIDATION=1",
        "-DCCBENCH_NO_WAIT_OF_TICTOC=0",
        "-DCCBENCH_WAL=0",
    ]


def test_parse_cells_accepts_legacy_dynamic_and_policy_forms() -> None:
    legacy, dynamic, policy = probe.parse_cells(
        "legacy:1:1:1000:2560,"
        "dynamic:1:1:1000:2560:10000:10240:1:1:4:1,"
        "policy:1:1:1000:2560:10000:10240:1:1:4:1:2"
    )
    assert legacy.label == "legacy"
    assert legacy.extended is False
    assert legacy.has_step_policy is False
    assert probe._cell_identity(legacy)["cell_format_fields"] == 5
    assert dynamic.label == "dynamic"
    assert dynamic.extended is True
    assert dynamic.has_step_policy is False
    assert probe._cell_identity(dynamic)["cell_format_fields"] == 11
    assert policy.label == "policy"
    assert policy.extended is True
    assert policy.has_step_policy is True
    assert policy.step_policy == 2
    assert probe._cell_identity(policy)["cell_format_fields"] == 12


@pytest.mark.parametrize(
    "suffix",
    ("-1", "3", "", "2:extra"),
    ids=("negative", "too-large", "empty", "thirteen-fields"),
)
def test_parse_cells_rejects_invalid_step_policy(suffix: str) -> None:
    with pytest.raises(ValueError):
        probe.parse_cells(
            "policy:1:1:1000:2560:10000:10240:1:1:4:1:" + suffix
        )


def test_eleven_and_explicit_policy_zero_have_distinct_identity() -> None:
    eleven, explicit_zero = probe.parse_cells(
        "eleven:1:1:1000:2560:10000:10240:1:1:4:1,"
        "explicit-zero:1:1:1000:2560:10000:10240:1:1:4:1:0"
    )
    eleven_identity = probe._cell_identity(eleven)
    zero_identity = probe._cell_identity(explicit_zero)
    assert eleven.has_step_policy is False
    assert eleven_identity["cell_format_fields"] == 11
    assert "step_policy" not in eleven_identity
    assert explicit_zero.has_step_policy is True
    assert explicit_zero.step_policy == 0
    assert zero_identity["cell_format_fields"] == 12
    assert zero_identity["step_policy"] == 0
    assert eleven_identity != zero_identity


def test_grid_distinguishes_policy_builds() -> None:
    grid = probe.parse_cells(
        "none:0:100:1000:10,stock:1:100:1000:10,"
        "forward:1:1:1000:2560:10000:10240:1:1:4:1:0,"
        "invert:1:1:1000:2560:10000:10240:1:1:4:1:1,"
        "randomized:1:1:1000:2560:10000:10240:1:1:4:1:2"
    )
    probe._validate_grid_contract(grid)
    duplicate_policy = probe.parse_cells(
        "forward-again:1:1:1000:2560:10000:10240:1:1:4:1:0"
    )[0]
    with pytest.raises(ValueError, match="duplicate build configurations"):
        probe._validate_grid_contract((*grid, duplicate_policy))


def test_cell_document_round_trip_requires_policy_key_presence_to_match_format() -> None:
    five, eleven, twelve = probe.parse_cells(
        "five:1:1:1000:2560,"
        "eleven:1:1:1000:2560:10000:10240:1:1:4:1,"
        "twelve:1:1:1000:2560:10000:10240:1:1:4:1:0"
    )
    assert probe._cell_from_document(probe._cell_identity(twelve)) == twelve

    twelve_without_key = probe._cell_identity(twelve)
    del twelve_without_key["step_policy"]
    eleven_with_key = {**probe._cell_identity(eleven), "step_policy": 0}
    five_with_key = {**probe._cell_identity(five), "step_policy": 0}
    twelve_with_bool = {**probe._cell_identity(twelve), "step_policy": False}
    for document in (
        twelve_without_key,
        eleven_with_key,
        five_with_key,
        twelve_with_bool,
    ):
        with pytest.raises(
            probe.CertificationReject,
            match="group-workload-contract-mismatch",
        ):
            probe._cell_from_document(document)


def test_genome_for_policy_cell_supplies_real_build_define() -> None:
    legacy, dynamic, policy_zero, policy = probe.parse_cells(
        "legacy:1:1:1000:2560,"
        "dynamic:1:1:1000:2560:10000:10240:1:1:4:1,"
        "policy-zero:1:1:1000:2560:10000:10240:1:1:4:1:0,"
        "policy:1:1:1000:2560:10000:10240:1:1:4:1:2"
    )
    legacy_flags = probe.genome_for(legacy).flags
    dynamic_flags = probe.genome_for(dynamic).flags
    policy_genome = probe.genome_for(policy)
    assert "BACKOFF_STEP_POLICY" not in legacy_flags
    assert "BACKOFF_STEP_POLICY_SEED" not in legacy_flags
    assert "BACKOFF_STEP_POLICY" not in dynamic_flags
    assert "BACKOFF_STEP_POLICY_SEED" not in dynamic_flags
    assert {
        key: probe.genome_for(policy_zero).flags[key]
        for key in ("BACKOFF_STEP_POLICY", "BACKOFF_STEP_POLICY_SEED")
    } == {
        "BACKOFF_STEP_POLICY": 0,
        "BACKOFF_STEP_POLICY_SEED": 11_400_714_819_323_198_485,
    }
    assert policy_genome.flags["BACKOFF_STEP_POLICY"] == 2
    assert policy_genome.flags["BACKOFF_STEP_POLICY_SEED"] == (
        11_400_714_819_323_198_485
    )
    assert "BACKOFF_STEP_POLICY=2" in policy_genome.canonical()
    assert (
        "BACKOFF_STEP_POLICY_SEED=11400714819323198485"
        in policy_genome.canonical()
    )
    custom_seed = 18_446_744_073_709_551_615
    assert probe.genome_for(
        policy, step_policy_seed=custom_seed
    ).flags["BACKOFF_STEP_POLICY_SEED"] == custom_seed
    policy_one = probe.parse_cells(
        "policy-one:1:1:1000:2560:10000:10240:1:1:4:1:1"
    )[0]
    for inert_cell in (policy_zero, policy_one):
        assert probe.genome_for(
            inert_cell, step_policy_seed=custom_seed
        ).flags["BACKOFF_STEP_POLICY_SEED"] == probe.STOCK_STEP_POLICY_SEED


def test_terminal_define_is_present_only_for_cohort2_trace_builds() -> None:
    cohort1 = probe.COUNTERFACTUAL_TRACE_CELLS[0]
    cohort2 = probe.COUNTERFACTUAL_COHORT2_TRACE_CELLS[0]
    cohort1_genome = probe.genome_for(cohort1, backoff_trace=True)
    cohort2_genome = probe.genome_for(
        cohort2,
        backoff_trace=True,
        backoff_trace_terminal_us=5_000_000,
    )
    assert "BACKOFF_TRACE_TERMINAL_US" not in cohort1_genome.flags
    assert cohort2_genome.flags["BACKOFF_TRACE_TERMINAL_US"] == 5_000_000
    with pytest.raises(ValueError, match="requires backoff trace mode"):
        probe.genome_for(cohort2, backoff_trace_terminal_us=5_000_000)


@pytest.mark.parametrize(
    "text",
    (
        "-1",
        "0x1",
        "+1",
        "1_0",
        "00",
        "014481721328008317845",
        "18446744073709551616",
        "１２",
    ),
    ids=(
        "negative",
        "hex",
        "plus",
        "underscore",
        "leading-zero",
        "allowed-leading-zero",
        "overflow",
        "non-ascii",
    ),
)
def test_step_policy_seed_rejects_non_decimal_or_out_of_uint64(text: str) -> None:
    parser = probe._argument_parser()
    with pytest.raises(SystemExit):
        parser.parse_args(
            [
                "--cells",
                COUNTERFACTUAL_TRACE_CELLS,
                "--step-policy-seed",
                text,
                "--out",
                "unused.json",
            ]
        )
    with pytest.raises(argparse.ArgumentTypeError):
        probe._uint64_decimal(False)


def test_policy_two_requires_seed_before_build_dispatch(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="step-policy-seed is required"):
        probe.main(
            [
                "--cells",
                COUNTERFACTUAL_TRACE_CELLS,
                "--out",
                str(tmp_path / "must-not-build.json"),
            ]
        )


def test_extended_cells_parse_all_dynamic_fields() -> None:
    cells = probe.parse_cells(TRACE_CELLS)
    assert cells == probe.TRACE_CELLS
    assert all(cell.extended for cell in cells)
    assert cells[1].step_min_milli == 1000
    assert cells[1].step_max_milli == 4000
    flags = probe.genome_for(cells[2]).flags
    assert {
        macro: flags[macro]
        for macro in (
            "BACKOFF_COUNT_WINDOW",
            "BACKOFF_COUNT_CAP_US",
            "BACKOFF_STEP_ADAPT",
            "BACKOFF_STEP_MIN_MILLI",
            "BACKOFF_STEP_MAX_MILLI",
            "BACKOFF_DYN_CEILING",
            "BACKOFF_TRACE",
        )
    } == {
        "BACKOFF_COUNT_WINDOW": 10000,
        "BACKOFF_COUNT_CAP_US": 10240,
        "BACKOFF_STEP_ADAPT": 1,
        "BACKOFF_STEP_MIN_MILLI": 1000,
        "BACKOFF_STEP_MAX_MILLI": 4000,
        "BACKOFF_DYN_CEILING": 1,
        "BACKOFF_TRACE": 0,
    }


@pytest.mark.parametrize(
    "cell",
    (
        "bad:1:1:1000:2560:0",
        "bad:1:1:1000:2560:0:10240:0:100:100:0",
        "bad:1:1:1000:2560:-1:0:0:100:100:0",
        "bad:1:1:1000:2560:1:10240:2:1:4:0",
        "bad:1:1:1000:2560:1:10240:1:0.0001:4:0",
        "bad:1:1:1000:2560:1:10240:1:4:1:0",
        "bad:1:5:1000:2560:1:10240:1:1:4:0",
        "bad:1:1:1000:2560:1:10240:1:1:13:1",
        "bad:1:1:1000:2560:1:10240:1:1:4:2",
    ),
    ids=(
        "six-fields",
        "M7-k-zero-cap-nonzero",
        "negative-window",
        "step-toggle",
        "lossy-step-bound",
        "reversed-bounds",
        "initial-step-outside-bounds",
        "dynamic-floor-impossible",
        "dynamic-toggle",
    ),
)
def test_extended_cells_reject_invalid_shape_and_inert_or_impossible_combinations(
    cell: str,
) -> None:
    with pytest.raises(ValueError):
        probe.parse_cells(cell)


def test_grid_contract_uses_all_dynamic_configuration_fields() -> None:
    grid = probe.parse_cells(
        "none:0:100:1000:10,"
        "stock:1:100:1000:10,"
        "tuned:1:1:1000:2560,"
        "tuned-u10240:1:1:1000:10240,"
        + TRACE_CELLS
    )
    probe._validate_grid_contract(grid)
    duplicate = (*grid, probe.Cell("same-build", 1, 1.0, 1000, 2560))
    with pytest.raises(ValueError, match="duplicate build configurations"):
        probe._validate_grid_contract(duplicate)


def test_expected_patch_a_sha256_is_checked_before_patch_b(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    changed_a = tmp_path / "changed-a.patch"
    changed_a.write_bytes(PATCH.read_bytes() + b"\n")
    monkeypatch.setattr(probe, "PATCH_A", changed_a)
    with pytest.raises(RuntimeError, match="immutable patch A SHA-256 mismatch"):
        probe._patch_stack_identity()
    assert probe.EXPECTED_PATCH_A_SHA256 == hashlib.sha256(PATCH.read_bytes()).hexdigest()


def test_patch_stack_identity_is_exact_ordered_a_b_c(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    assert PATCH_B.is_file()
    assert PATCH_C.is_file()
    identity = probe._patch_stack_identity()
    assert [entry["path"] for entry in identity["patch_stack"]] == [
        "patches/cicada-adaptive-params.patch",
        "patches/cicada-adaptive-dynamic.patch",
        "patches/cicada-adaptive-counterfactual.patch",
    ]
    stack_bytes = "izanagi-patch-stack/v1\n" + "".join(
        f"{entry['path']} {entry['sha256']}\n"
        for entry in identity["patch_stack"]
    )
    assert identity["patch_sha256"] == probe.EXPECTED_PATCH_A_SHA256
    assert identity["dynamic_patch_sha256"] == hashlib.sha256(
        PATCH_B.read_bytes()
    ).hexdigest()
    assert identity["counterfactual_patch_sha256"] == hashlib.sha256(
        PATCH_C.read_bytes()
    ).hexdigest()
    assert [entry["sha256"] for entry in identity["patch_stack"]] == [
        hashlib.sha256(PATCH.read_bytes()).hexdigest(),
        hashlib.sha256(PATCH_B.read_bytes()).hexdigest(),
        hashlib.sha256(PATCH_C.read_bytes()).hexdigest(),
    ]
    assert identity["patch_stack_sha256"] == hashlib.sha256(
        stack_bytes.encode("utf-8")
    ).hexdigest()
    pure_pin = subprocess.run(
        ["git", "-C", str(CCBENCH), "apply", "--check", str(PATCH_B)],
        capture_output=True,
        text=True,
    )
    assert pure_pin.returncode != 0
    pure_pin_c = subprocess.run(
        ["git", "-C", str(CCBENCH), "apply", "--check", str(PATCH_C)],
        capture_output=True,
        text=True,
    )
    assert pure_pin_c.returncode != 0
    monkeypatch.setenv("TMPDIR", str(tmp_path))
    with probe.isolated_checkout(CCBENCH, probe.CURRENT_PIN) as work_root:
        with probe._applied_patch_stack(work_root) as c_files:
            assert set(c_files) == {"cmake/Options.cmake", "include/backoff.hh"}
            diff = subprocess.run(
                ["git", "-C", work_root, "diff", "--"],
                check=True,
                capture_output=True,
                text=True,
            ).stdout
            assert "BACKOFF_STEP_POLICY" in diff
            assert "both_actions_feasible" in diff
        probe.assert_pinned_clean(work_root, probe.CURRENT_PIN)


def test_patch_b_defaults_are_stock_equivalent_and_trace_uses_numeric_if() -> None:
    assert PATCH_B.is_file()
    patch = PATCH_B.read_text(encoding="utf-8")
    for name, value in {
        "COUNT_WINDOW": 0,
        "COUNT_CAP_US": 0,
        "STEP_ADAPT": 0,
        "STEP_MIN_MILLI": 100000,
        "STEP_MAX_MILLI": 100000,
        "DYN_CEILING": 0,
        "TRACE": 0,
    }.items():
        assert re.search(
            rf"^\+set\(CCBENCH_BACKOFF_{name}[ ]+{value}\b",
            patch,
            flags=re.MULTILINE,
        )
    assert re.search(r"^\+#if BACKOFF_TRACE$", patch, flags=re.MULTILINE)
    assert re.search(r"^\+#ifdef BACKOFF_TRACE$", patch, flags=re.MULTILINE) is None


def test_trace_binary_counts_match_small_fixture_binaries_and_fail_closed(
    tmp_path: Path,
) -> None:
    trace_source = tmp_path / "trace.cc"
    trace_binary = tmp_path / "trace.exe"
    trace_source.write_text(
        'extern "C" const char* izanagi_backoff_trace_probe() {\n'
        '  return "IZANAGI_BACKOFF_TRACE v=1";\n'
        '}\n'
        'int main() { return izanagi_backoff_trace_probe()[0] == \'\\0\'; }\n',
        encoding="utf-8",
    )
    perf_source = tmp_path / "perf.cc"
    perf_binary = tmp_path / "perf.exe"
    perf_source.write_text("int main() { return 0; }\n", encoding="utf-8")
    for source, binary in (
        (trace_source, trace_binary),
        (perf_source, perf_binary),
    ):
        subprocess.run(
            ["g++", "-O0", str(source), "-o", str(binary)],
            check=True,
            capture_output=True,
            text=True,
        )

    trace_counts = probe._trace_binary_counts(str(trace_binary))
    perf_counts = probe._trace_binary_counts(str(perf_binary))
    assert trace_counts[0] >= 1 and trace_counts[1] >= 1
    assert perf_counts == (0, 0)

    probe._validate_trace_binary_counts(*trace_counts, backoff_trace=True)
    probe._validate_trace_binary_counts(*perf_counts, backoff_trace=False)
    with pytest.raises(RuntimeError):
        probe._validate_trace_binary_counts(*trace_counts, backoff_trace=False)
    with pytest.raises(RuntimeError):
        probe._validate_trace_binary_counts(*perf_counts, backoff_trace=True)


def test_public_certification_accepts_each_exact_cell_and_rejects_widening(
    tmp_path: Path,
) -> None:
    parser = probe._argument_parser()
    for exact, threads, seed in (
        (CERT_CELL, 48, None),
        (DYNAMIC_CERT_CELL, 48, None),
        (COHORT2_POLICY1_CERT_CELL, 24, None),
        (
            COHORT2_POLICY2_CERT_CELL,
            24,
            probe.CERT_PREREGISTERED_STEP_POLICY_SEEDS[0],
        ),
    ):
        argv = _certify_argv(
            tmp_path,
            cells=exact,
            threads=threads,
            step_policy_seed=seed,
        )
        axes, workload = probe._certification_contract(
            parser.parse_args(argv)
        )
        assert axes.cell in probe.CERT_CELLS
        assert workload == "balanced"
        assert axes.threads == threads

    for invalid in (
        f"{CERT_CELL},{DYNAMIC_CERT_CELL}",
        "cw:1:1:1000:2560:10000:10240:0:100:100:0",
        "cw-as-dyn:1:1:1000:2560:10001:10240:1:1:4:1",
        (
            "cw-as-dyn-c2-p1:1:1:1000:2560:10000:"
            "9223372036854775806:1:1:4:1:1"
        ),
    ):
        argv = _certify_argv(tmp_path)
        argv[argv.index(CERT_CELL)] = invalid
        with pytest.raises(probe.CertificationReject) as caught:
            probe._certification_contract(parser.parse_args(argv))
        assert caught.value.reason == "certification-cell-mismatch"


def test_probe_seed_table_matches_cohort2_preregistered_seeds() -> None:
    assert len(probe.CERT_PREREGISTERED_STEP_POLICY_SEEDS) == 12
    assert set(probe.CERT_PREREGISTERED_STEP_POLICY_SEEDS) == PREREGISTERED_SEEDS
    assert probe.STOCK_STEP_POLICY_SEED not in PREREGISTERED_SEEDS
    assert probe.CERT_POLICY2_STEP_POLICY_SEEDS == (
        PREREGISTERED_SEEDS | {probe.STOCK_STEP_POLICY_SEED}
    )


def test_certification_contract_accepts_only_cell_closed_thread_seed_axes(
    tmp_path: Path,
) -> None:
    parser = probe._argument_parser()
    for seed in probe.CERT_POLICY2_STEP_POLICY_SEEDS:
        for threads in (24, 48):
            axes, workload = probe._certification_contract(
                parser.parse_args(
                    _certify_argv(
                        tmp_path,
                        cells=COHORT2_POLICY2_CERT_CELL,
                        threads=threads,
                        step_policy_seed=seed,
                    )
                )
            )
            assert axes == probe.CertificationAxes(
                probe.CERT_COHORT2_POLICY2_CELL, threads, seed
            )
            assert workload == "balanced"

    for threads in (24, 48):
        axes, _workload = probe._certification_contract(
            parser.parse_args(
                _certify_argv(
                    tmp_path,
                    cells=COHORT2_POLICY1_CERT_CELL,
                    threads=threads,
                )
            )
        )
        assert axes == probe.CertificationAxes(
            probe.CERT_COHORT2_POLICY1_CELL,
            threads,
            probe.STOCK_STEP_POLICY_SEED,
        )

    for cells in (CERT_CELL, DYNAMIC_CERT_CELL):
        args = parser.parse_args(
            _certify_argv(tmp_path, cells=cells, threads=24)
        )
        with pytest.raises(probe.CertificationReject) as caught:
            probe._certification_contract(args)
        assert caught.value.reason == "certification-workload-shape-mismatch"


def test_certification_contract_rejects_seed_and_thread_near_misses(
    tmp_path: Path,
) -> None:
    parser = probe._argument_parser()
    invalid_seed = next(
        seed
        for seed in range(2**64)
        if seed not in probe.CERT_POLICY2_STEP_POLICY_SEEDS
    )
    cases = (
        (
            _certify_argv(
                tmp_path,
                cells=COHORT2_POLICY2_CERT_CELL,
                step_policy_seed=invalid_seed,
            ),
            "certification-step-policy-seed-mismatch",
        ),
        (
            _certify_argv(tmp_path, cells=COHORT2_POLICY2_CERT_CELL),
            "certification-step-policy-seed-missing",
        ),
        (
            _certify_argv(tmp_path, cells=CERT_CELL, threads=24),
            "certification-workload-shape-mismatch",
        ),
    )
    for argv, reason in cases:
        with pytest.raises(probe.CertificationReject) as caught:
            probe._certification_contract(parser.parse_args(argv))
        assert caught.value.reason == reason

    seed = probe.CERT_PREREGISTERED_STEP_POLICY_SEEDS[0]
    for raw_threads in ("23", "25", "47", "24,48", "024", "24 "):
        argv = _certify_argv(
            tmp_path,
            cells=COHORT2_POLICY2_CERT_CELL,
            step_policy_seed=seed,
        )
        argv[argv.index("--threads") + 1] = raw_threads
        with pytest.raises(probe.CertificationReject) as caught:
            probe._certification_contract(parser.parse_args(argv))
        assert caught.value.reason == "certification-workload-shape-mismatch"
    argv = _certify_argv(
        tmp_path,
        cells=COHORT2_POLICY2_CERT_CELL,
        step_policy_seed=seed,
    )
    argv[argv.index("--threads") + 1] = "49"
    with pytest.raises(ValueError, match="outside 1..48"):
        probe._certification_contract(parser.parse_args(argv))

    p0 = (
        "cw-as-dyn-c2-p0:1:1:1000:2560:10000:"
        "9223372036854775807:1:1:4:1:0"
    )
    for cells in (CERT_CELL, DYNAMIC_CERT_CELL, COHORT2_POLICY1_CERT_CELL, p0):
        argv = _certify_argv(tmp_path, cells=cells, step_policy_seed=seed)
        with pytest.raises(probe.CertificationReject) as caught:
            probe._certification_contract(parser.parse_args(argv))
        assert caught.value.reason == "step-policy-seed-certification-conflict"


@pytest.mark.parametrize(
    ("option", "value"),
    (
        ("--threads", "48"),
        (
            "--step-policy-seed",
            str(probe.CERT_PREREGISTERED_STEP_POLICY_SEEDS[0]),
        ),
    ),
    ids=("threads", "step-policy-seed"),
)
def test_certification_axis_options_reject_duplicates(
    tmp_path: Path, option: str, value: str
) -> None:
    argv = _certify_argv(
        tmp_path,
        cells=COHORT2_POLICY2_CERT_CELL,
        step_policy_seed=probe.CERT_PREREGISTERED_STEP_POLICY_SEEDS[0],
    )
    argv.extend((option, value))
    with pytest.raises(SystemExit) as caught:
        probe._argument_parser().parse_args(argv)
    assert caught.value.code == 2


def test_certification_raw_thread_literal_rejects_before_thread_parser(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    args = probe._argument_parser().parse_args(
        _certify_argv(
            tmp_path,
            cells=COHORT2_POLICY2_CERT_CELL,
            step_policy_seed=probe.CERT_PREREGISTERED_STEP_POLICY_SEEDS[0],
        )
    )
    args.threads = "24,48"

    def unexpected_parse(_text: str) -> tuple[int, ...]:
        raise AssertionError("raw thread rejection must precede parsing")

    monkeypatch.setattr(probe, "_parse_threads", unexpected_parse)
    with pytest.raises(probe.CertificationReject) as caught:
        probe._certification_contract(args)
    assert caught.value.reason == "certification-workload-shape-mismatch"


def test_policy2_certification_missing_seed_rejects_before_build(
    tmp_path: Path,
) -> None:
    with pytest.raises(probe.CertificationReject) as caught:
        probe.main(
            _certify_argv(tmp_path, cells=COHORT2_POLICY2_CERT_CELL)
        )
    assert caught.value.reason == "certification-step-policy-seed-missing"


def test_certification_claim_requires_validated_axes_and_binds_actual_identity() -> None:
    seed = probe.CERT_PREREGISTERED_STEP_POLICY_SEEDS[0]
    axes24 = probe.CertificationAxes(
        probe.CERT_COHORT2_POLICY2_CELL, 24, seed
    )
    axes48 = probe.CertificationAxes(
        probe.CERT_COHORT2_POLICY2_CELL, 48, seed
    )
    claim24 = probe._certification_claim(axes24)
    claim48 = probe._certification_claim(axes48)
    assert claim24 != claim48
    assert "threads=24" in claim24 and f"compile seed {seed}" in claim24
    assert "BACKOFF_TRACE=0" in claim24
    assert "BACKOFF_TRACE_TERMINAL_US の terminal define なし" in claim24
    with pytest.raises(TypeError, match="CertificationAxes"):
        probe._certification_claim(  # type: ignore[arg-type]
            {"cell": probe.CERT_COHORT2_POLICY2_CELL, "threads": 24}
        )
    with pytest.raises(ValueError, match="cell closed table"):
        probe.CertificationAxes(probe.CERT_TUNED_CELL, 24, None)


def test_published_claim_compatibility_is_exact_for_the_four_old_literals() -> None:
    published_axes = (
        probe.CertificationAxes(probe.CERT_TUNED_CELL, 48, None),
        probe.CertificationAxes(probe.CERT_DYNAMIC_CELL, 48, None),
        probe.CertificationAxes(
            probe.CERT_COHORT2_POLICY1_CELL,
            48,
            probe.STOCK_STEP_POLICY_SEED,
        ),
        probe.CertificationAxes(
            probe.CERT_COHORT2_POLICY2_CELL,
            48,
            probe.STOCK_STEP_POLICY_SEED,
        ),
    )
    for axes in published_axes:
        assert probe._certification_claim(axes) == probe.CERT_CLAIMS[axes.cell]
    generated_axes = (
        probe.CertificationAxes(
            probe.CERT_COHORT2_POLICY1_CELL,
            24,
            probe.STOCK_STEP_POLICY_SEED,
        ),
        probe.CertificationAxes(
            probe.CERT_COHORT2_POLICY2_CELL,
            24,
            probe.STOCK_STEP_POLICY_SEED,
        ),
        *(
            probe.CertificationAxes(
                probe.CERT_COHORT2_POLICY2_CELL, threads, seed
            )
            for seed in probe.CERT_PREREGISTERED_STEP_POLICY_SEEDS
            for threads in (24, 48)
        ),
    )
    for axes in generated_axes:
        claim = probe._certification_claim(axes)
        assert claim not in probe.CERT_CLAIMS.values()
        assert f"threads={axes.threads}" in claim
        assert "BACKOFF_TRACE=0" in claim
        assert "BACKOFF_TRACE_TERMINAL_US の terminal define なし" in claim


def test_published_cohort2_receipts_reaccept_exact_old_claim_identities(
    tmp_path: Path,
) -> None:
    performance = tmp_path / "performance.json"
    performance.write_text(
        json.dumps(
            {
                "schema_version": probe.SCHEMA_VERSION,
                "kind": "performance-only-probe",
                "not_certified": probe.NOT_CERTIFIED,
            }
        )
        + "\n",
        encoding="utf-8",
    )
    performance_sha256 = hashlib.sha256(performance.read_bytes()).hexdigest()
    performance_identity = {
        "path": str(performance.resolve(strict=True)),
        "sha256": performance_sha256,
    }
    verifier_identity = {
        "repository_commit": "a" * 40,
        "module_sha256": {"orchestrator/verify.py": "b" * 64},
    }
    verifier_file_sha256 = "c" * 64
    patch_identity = probe._patch_stack_identity()
    execution_identity = {
        "driver_sha256": "d" * 64,
        "pbs_sha256": "e" * 64,
        "driver_argv": ["t2187_adaptive_const_probe.py", "--mode", "certify"],
        "repo_status_clean": True,
    }
    source_evidence = {
        "ccbench_commit": probe.CURRENT_PIN,
        "genome_sha256": "f" * 64,
        "src_token": "published-source",
        "source_bytes_sha256": "1" * 64,
    }

    for attempt_id, cell in (
        ("c2-p1-a1", probe.CERT_COHORT2_POLICY1_CELL),
        ("c2-p2-a1", probe.CERT_COHORT2_POLICY2_CELL),
    ):
        axes = probe.CertificationAxes(
            cell, 48, probe.STOCK_STEP_POLICY_SEED
        )
        genome = probe.genome_for(
            cell, step_policy_seed=axes.step_policy_seed
        ).canonical()
        prereg_sha256 = probe._certification_prereg_sha256(cell)
        results = []
        result_files = []
        for workload in probe.CERT_WORKLOADS:
            for slot in probe.CERT_SLOTS:
                path = tmp_path / f"{attempt_id}-{workload}-{slot}.json"
                path.write_text("{}\n", encoding="utf-8")
                result_files.append(path)
                results.append(
                    {
                        "path": str(path.resolve(strict=True)),
                        "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
                        **probe._cell_identity(cell),
                        "cell_order": [cell.label],
                        "claim": probe._certification_claim(axes),
                        "backoff_trace": False,
                        "records": probe.CERT_RECORDS,
                        "threads": 48,
                        "extime_s": 6,
                        "workload": workload,
                        "workload_flags": {
                            **probe.WORKLOADS[workload],
                            "ycsb_tuple_num": str(probe.CERT_RECORDS),
                            "thread_num": "48",
                            "extime": "6",
                        },
                        "step_policy_seed": probe.STOCK_STEP_POLICY_SEED,
                        "repo_head": "2" * 40,
                        "prereg_sha256": prereg_sha256,
                        "ccbench_commit": probe.PIN_FULL,
                        "ccbench_head": probe.PIN_FULL,
                        **execution_identity,
                        "genome": genome,
                        "source_evidence": source_evidence,
                        "proof_surface": {
                            "protocol": probe.CERT_PROTOCOL,
                            "source_snapshot_identity": source_evidence,
                        },
                        **patch_identity,
                        "binary_sha256": "3" * 64,
                        "build_cache_key": "published-build_t1",
                    }
                )
        receipt = {
            "schema_version": probe.GROUP_RECEIPT_SCHEMA_VERSION,
            "complete": True,
            "certified_requests": 24,
            "attempt_id": attempt_id,
            "verifier_identity": verifier_identity,
            "expected_verifier_identity_file_sha256": verifier_file_sha256,
            "performance_artifact": performance_identity,
            **probe._cell_identity(cell),
            "cell_order": [cell.label],
            "claim": probe._certification_claim(axes),
            "backoff_trace": False,
            "records": probe.CERT_RECORDS,
            "threads": 48,
            "extime_s": 6,
            "step_policy_seed": probe.STOCK_STEP_POLICY_SEED,
            "hostname": "published-host",
            "prereg_sha256": prereg_sha256,
            "repo_head": "2" * 40,
            **patch_identity,
            "ccbench_commit": probe.PIN_FULL,
            "ccbench_head": probe.PIN_FULL,
            "genome": genome,
            "source_evidence": source_evidence,
            "proof_surface": {
                "protocol": probe.CERT_PROTOCOL,
                "source_snapshot_identity": source_evidence,
            },
            **execution_identity,
            "results": results,
        }
        group_out = tmp_path / f"{attempt_id}-group.json"
        group_out.write_text(json.dumps(receipt) + "\n", encoding="utf-8")
        probe._validate_published_group(
            group_out,
            result_files,
            performance,
            performance_sha256,
            attempt_id,
            verifier_identity,
            verifier_file_sha256,
        )
        wrong_claim_receipt = copy.deepcopy(receipt)
        wrong_claim_receipt["claim"] += " drift"
        for row in wrong_claim_receipt["results"]:
            row["claim"] = wrong_claim_receipt["claim"]
        group_out.write_text(
            json.dumps(wrong_claim_receipt) + "\n", encoding="utf-8"
        )
        with pytest.raises(probe.CertificationReject) as caught:
            probe._validate_published_group(
                group_out,
                result_files,
                performance,
                performance_sha256,
                attempt_id,
                verifier_identity,
                verifier_file_sha256,
            )
        assert caught.value.reason == "group-receipt-collision"

        mixed_receipt = copy.deepcopy(receipt)
        if cell == probe.CERT_COHORT2_POLICY1_CELL:
            mixed_receipt["results"][0]["threads"] = 24
            mixed_receipt["results"][0]["workload_flags"]["thread_num"] = "24"
        else:
            mixed_receipt["results"][0]["step_policy_seed"] = (
                probe.CERT_PREREGISTERED_STEP_POLICY_SEEDS[0]
            )
        group_out.write_text(
            json.dumps(mixed_receipt) + "\n", encoding="utf-8"
        )
        with pytest.raises(probe.CertificationReject) as caught:
            probe._validate_published_group(
                group_out,
                result_files,
                performance,
                performance_sha256,
                attempt_id,
                verifier_identity,
                verifier_file_sha256,
            )
        assert caught.value.reason == "group-receipt-collision"
        if cell == probe.CERT_COHORT2_POLICY2_CELL:
            invalid_seed = next(
                value
                for value in range(2**64)
                if value not in probe.CERT_POLICY2_STEP_POLICY_SEEDS
            )
            receipt["step_policy_seed"] = invalid_seed
            for row in receipt["results"]:
                row["step_policy_seed"] = invalid_seed
            group_out.write_text(
                json.dumps(receipt) + "\n", encoding="utf-8"
            )
            with pytest.raises(probe.CertificationReject) as caught:
                probe._validate_published_group(
                    group_out,
                    result_files,
                    performance,
                    performance_sha256,
                    attempt_id,
                    verifier_identity,
                    verifier_file_sha256,
                )
            assert caught.value.reason == "group-receipt-collision"


def test_group_axes_reject_mixed_policy2_seed_or_thread() -> None:
    seed_a, seed_b = probe.CERT_PREREGISTERED_STEP_POLICY_SEEDS[:2]

    def row(threads: int, seed: int) -> dict:
        return {
            **probe._cell_identity(probe.CERT_COHORT2_POLICY2_CELL),
            "threads": threads,
            "step_policy_seed": seed,
        }

    for rows in (
        [row(48, seed_a), row(48, seed_b)],
        [row(24, seed_a), row(48, seed_a)],
    ):
        with pytest.raises(probe.CertificationReject) as caught:
            probe._group_certification_axes(rows)
        assert caught.value.reason == "group-cell-identity-mismatch"


def test_cohort2_certification_is_exact_and_policy2_uses_default_seed(
    tmp_path: Path,
) -> None:
    parser = probe._argument_parser()
    for exact, expected_cell, request_seed in (
        (
            COHORT2_POLICY1_CERT_CELL,
            probe.CERT_COHORT2_POLICY1_CELL,
            None,
        ),
        (
            COHORT2_POLICY2_CERT_CELL,
            probe.CERT_COHORT2_POLICY2_CELL,
            probe.CERT_PREREGISTERED_STEP_POLICY_SEEDS[0],
        ),
    ):
        argv = _certify_argv(
            tmp_path,
            cells=exact,
            step_policy_seed=request_seed,
        )
        axes, workload = probe._certification_contract(
            parser.parse_args(argv)
        )
        assert (axes.cell, workload, axes.threads) == (
            expected_cell,
            "balanced",
            48,
        )
        assert axes.step_policy_seed == (
            request_seed
            if request_seed is not None
            else probe.STOCK_STEP_POLICY_SEED
        )
        assert probe.CERT_EXTIME_BY_CELL[axes.cell] == 6
        assert probe._certification_prereg_sha256(axes.cell) == (
            "8b4127f4be895da0d25da88b0837f679ecf06d43ab656b16d2944146b9f7a9e9"
        )

    policy2_genome = probe.genome_for(probe.CERT_COHORT2_POLICY2_CELL)
    assert policy2_genome.flags["BACKOFF_STEP_POLICY"] == 2
    assert policy2_genome.flags["BACKOFF_STEP_POLICY_SEED"] == (
        probe.STOCK_STEP_POLICY_SEED
    )

    wrong_extime = _certify_argv(tmp_path)
    wrong_extime[wrong_extime.index(CERT_CELL)] = COHORT2_POLICY1_CERT_CELL
    with pytest.raises(probe.CertificationReject) as caught:
        probe._certification_contract(parser.parse_args(wrong_extime))
    assert caught.value.reason == "certification-workload-shape-mismatch"

    near_miss = _certify_argv(tmp_path)
    near_miss[near_miss.index(CERT_CELL)] = (
        "cw-as-dyn-c2-p1:1:1:1000:2560:10000:"
        "9223372036854775806:1:1:4:1:1"
    )
    near_miss[near_miss.index("3")] = "6"
    with pytest.raises(probe.CertificationReject) as caught:
        probe._certification_contract(parser.parse_args(near_miss))
    assert caught.value.reason == "certification-cell-mismatch"


def test_trace_parser_requires_exact_sequence_summary_and_computes_direction() -> None:
    stdout = """\
unrelated benchmark output
IZANAGI_BACKOFF_TRACE v=1 seq=0 tsc=100 window_us=10 window_commits=100 trigger=1 backoff_before=1 backoff_after=2 gradient_sign=1 step_us=1 ceiling_us=1000 ceiling_changed=0 parity_branch=-1
IZANAGI_BACKOFF_TRACE v=1 seq=1 tsc=120 window_us=10 window_commits=120 trigger=2 backoff_before=2 backoff_after=2 gradient_sign=0 step_us=1 ceiling_us=500 ceiling_changed=1 parity_branch=0
IZANAGI_BACKOFF_TRACE v=1 seq=2 tsc=140 window_us=10 window_commits=110 trigger=0 backoff_before=2 backoff_after=1 gradient_sign=0 step_us=1 ceiling_us=500 ceiling_changed=0 parity_branch=1
IZANAGI_BACKOFF_TRACE_SUMMARY v=1 updates=3 retained=3 dropped=0
"""
    events, summary, directional = probe._parse_backoff_trace(stdout)
    assert [event["seq"] for event in events] == [0, 1, 2]
    assert [event["window_us"] for event in events] == [10, 10, 10]
    assert [event["trigger"] for event in events] == ["count", "cap", "time"]
    assert [event["parity_branch"] for event in events] == [
        "none",
        "decrement",
        "increment",
    ]
    assert summary == {"updates": 3, "retained": 3, "dropped": 0}
    assert directional == {"scored": 1, "successes": 1, "rate": 1.0}

    for mutated in (
        stdout.replace("seq=1", "seq=2"),
        stdout.replace("tsc=120", "tsc=99"),
        stdout.replace("dropped=0", "dropped=1"),
        stdout.replace("updates=3", "updates=4"),
        stdout.replace("trigger=0", "trigger=3"),
        stdout.replace("parity_branch=1", "parity_branch=2"),
    ):
        with pytest.raises(ValueError):
            probe._parse_backoff_trace(mutated)

    def overflow_record(seq: int) -> str:
        return (
            f"IZANAGI_BACKOFF_TRACE v=1 seq={seq} tsc={seq} window_us=1 "
            "window_commits=1 trigger=0 backoff_before=1 backoff_after=1 "
            "gradient_sign=0 step_us=1 ceiling_us=1000 ceiling_changed=0 "
            "parity_branch=0"
        )

    overflow_stdout = "\n".join(
        overflow_record(seq) for seq in range(1, 65_537)
    )
    overflow_stdout += (
        "\nIZANAGI_BACKOFF_TRACE_SUMMARY v=1 updates=65537 "
        "retained=65536 dropped=1\n"
    )
    overflow_events, overflow_summary, overflow_directional = (
        probe._parse_backoff_trace(overflow_stdout, allow_overflow=True)
    )
    assert len(overflow_events) == 65_536
    assert (overflow_events[0]["seq"], overflow_events[-1]["seq"]) == (1, 65_536)
    assert overflow_summary == {"updates": 65_537, "retained": 65_536, "dropped": 1}
    assert overflow_directional == {"scored": 0, "successes": 0, "rate": None}
    del overflow_events

    with pytest.raises(ValueError, match="contiguous from zero"):
        probe._parse_backoff_trace(overflow_stdout)
    with pytest.raises(ValueError, match="contiguous from zero"):
        probe._parse_backoff_trace(overflow_stdout, allow_overflow=False)

    count_drift_stdout = "\n".join(
        overflow_record(seq) for seq in range(2, 65_537)
    )
    count_drift_stdout += (
        "\nIZANAGI_BACKOFF_TRACE_SUMMARY v=1 updates=65537 "
        "retained=65535 dropped=2\n"
    )
    with pytest.raises(ValueError, match="overflow contract failed"):
        probe._parse_backoff_trace(count_drift_stdout, allow_overflow=True)

    sequence_drift_stdout = overflow_stdout.replace(
        "seq=32768 tsc=32768 ", "seq=32769 tsc=32768 ", 1
    )
    with pytest.raises(ValueError, match="overflow contract failed"):
        probe._parse_backoff_trace(sequence_drift_stdout, allow_overflow=True)


def test_parse_backoff_trace_accepts_v1_and_exact_v2() -> None:
    v1_record = (
        "IZANAGI_BACKOFF_TRACE v=1 seq=0 tsc=100 window_us=10 "
        "window_commits=100 trigger=1 backoff_before=100 backoff_after=101 "
        "gradient_sign=1 step_us=1 ceiling_us=1000 ceiling_changed=0 "
        "parity_branch=-1"
    )
    v1_stdout = (
        v1_record
        + "\nIZANAGI_BACKOFF_TRACE_SUMMARY v=1 updates=1 retained=1 dropped=0\n"
    )
    v2_record = (
        "IZANAGI_BACKOFF_TRACE v=2 seq=0 tsc=100 window_us=10 "
        "window_commits=100 trigger=1 backoff_before=100 backoff_after=99 "
        "gradient_sign=1 step_us=1 ceiling_us=1000 ceiling_changed=0 "
        "parity_branch=-1 recommended_delta_sign=1 assigned_invert=1 "
        "inversion_realized=1 both_actions_feasible=1"
    )
    v2_stdout = (
        v2_record
        + "\nIZANAGI_BACKOFF_TRACE_SUMMARY v=2 updates=1 retained=1 dropped=0\n"
    )

    v1_events, v1_summary, v1_directional = probe._parse_backoff_trace(v1_stdout)
    v2_events, v2_summary, v2_directional = probe._parse_backoff_trace(v2_stdout)
    assert set(v1_events[0]) == {
        "seq",
        "tsc",
        "window_us",
        "window_commits",
        "trigger",
        "backoff_before",
        "backoff_after",
        "gradient_sign",
        "step_us",
        "ceiling_us",
        "ceiling_changed",
        "parity_branch",
    }
    assert v1_summary == {"updates": 1, "retained": 1, "dropped": 0}
    assert v1_directional == {"scored": 0, "successes": 0, "rate": None}
    assert {
        key: v2_events[0][key]
        for key in (
            "recommended_delta_sign",
            "assigned_invert",
            "inversion_realized",
            "both_actions_feasible",
        )
    } == {
        "recommended_delta_sign": 1,
        "assigned_invert": 1,
        "inversion_realized": 1,
        "both_actions_feasible": 1,
    }
    assert v2_summary == {"updates": 1, "retained": 1, "dropped": 0}
    assert set(v2_directional) == {
        "scored",
        "successes",
        "rate",
        "assigned_forward",
        "assigned_invert",
        "realized_invert",
    }

    mixed_records = (
        v1_record
        + "\n"
        + v2_record.replace("seq=0", "seq=1")
        + "\nIZANAGI_BACKOFF_TRACE_SUMMARY v=2 updates=2 retained=2 dropped=0\n"
    )
    malformed = (
        v2_record.rsplit(" both_actions_feasible=1", 1)[0]
        + "\nIZANAGI_BACKOFF_TRACE_SUMMARY v=2 updates=1 retained=1 dropped=0\n",
        v1_stdout.replace("v=1", "v=2"),
        v2_stdout.replace("v=2", "v=1"),
        mixed_records,
        v2_stdout.replace("TRACE_SUMMARY v=2", "TRACE_SUMMARY v=1"),
        v2_stdout.replace("assigned_invert=1", "assigned_invert=0"),
        v2_stdout.replace("recommended_delta_sign=1", "recommended_delta_sign=0"),
        v2_stdout.replace("backoff_after=99", "backoff_after=98"),
    )
    for candidate in malformed:
        with pytest.raises(ValueError):
            probe._parse_backoff_trace(candidate)


def test_parse_backoff_trace_accepts_exact_v3_terminal_contract_only() -> None:
    normal = (
        "IZANAGI_BACKOFF_TRACE v=3 seq=0 tsc=100 window_us=10 "
        "window_commits=10000 trigger=1 backoff_before=100 backoff_after=101 "
        "gradient_sign=1 step_us=1 ceiling_us=1000 ceiling_changed=0 "
        "parity_branch=-1 recommended_delta_sign=1 assigned_invert=0 "
        "inversion_realized=0 both_actions_feasible=1 terminal_flush=0"
    )
    terminal = (
        "IZANAGI_BACKOFF_TRACE v=3 seq=1 tsc=200 window_us=11 "
        "window_commits=10000 trigger=3 backoff_before=101 backoff_after=101 "
        "gradient_sign=0 step_us=1 ceiling_us=1000 ceiling_changed=0 "
        "parity_branch=-1 recommended_delta_sign=0 assigned_invert=-1 "
        "inversion_realized=0 both_actions_feasible=0 terminal_flush=1"
    )
    summary = (
        "IZANAGI_BACKOFF_TRACE_SUMMARY v=3 updates=1 retained=1 "
        "dropped=0 flushes=1"
    )
    stdout = "\n".join((normal, terminal, summary)) + "\n"

    events, parsed_summary, directional = probe._parse_backoff_trace(stdout)
    assert [event["terminal_flush"] for event in events] == [0, 1]
    assert events[-1]["trigger"] == "terminal"
    assert events[-1]["assigned_invert"] == -1
    assert parsed_summary == {
        "updates": 1,
        "retained": 1,
        "dropped": 0,
        "flushes": 1,
    }
    assert directional["scored"] == 1

    malformed = (
        # v2 and earlier cannot carry the terminal field.
        stdout.replace("v=3", "v=2"),
        # v3 records and summaries require their new fields.
        stdout.replace(" terminal_flush=0", "", 1),
        stdout.replace(" flushes=1", ""),
        stdout.replace("assigned_invert=-1", "assigned_invert=0"),
        stdout.replace("recommended_delta_sign=0", "recommended_delta_sign=1"),
        stdout.replace("updates=1", "updates=2"),
        stdout.replace("retained=1", "retained=2"),
        stdout.replace("flushes=1", "flushes=2"),
    )
    for candidate in malformed:
        with pytest.raises(ValueError):
            probe._parse_backoff_trace(candidate)


def test_parse_backoff_trace_accepts_v3_without_terminal_and_pins_summary() -> None:
    normal = (
        "IZANAGI_BACKOFF_TRACE v=3 seq=0 tsc=100 window_us=10 "
        "window_commits=10000 trigger=1 backoff_before=100 backoff_after=101 "
        "gradient_sign=1 step_us=1 ceiling_us=1000 ceiling_changed=0 "
        "parity_branch=-1 recommended_delta_sign=1 assigned_invert=0 "
        "inversion_realized=0 both_actions_feasible=1 terminal_flush=0"
    )
    summary = (
        "IZANAGI_BACKOFF_TRACE_SUMMARY v=3 updates=1 retained=1 "
        "dropped=0 flushes=0"
    )
    stdout = f"{normal}\n{summary}\n"

    events, parsed_summary, directional = probe._parse_backoff_trace(stdout)
    assert len(events) == 1
    assert events[0]["terminal_flush"] == 0
    assert events[0]["trigger"] == "count"
    assert parsed_summary == {
        "updates": 1,
        "retained": 1,
        "dropped": 0,
        "flushes": 0,
    }
    assert directional["scored"] == 0

    for _field, old, new in (
        ("updates", "updates=1", "updates=2"),
        ("retained", "retained=1", "retained=0"),
        ("dropped", "dropped=0", "dropped=1"),
        ("flushes", "flushes=0", "flushes=1"),
    ):
        with pytest.raises(
            ValueError,
            match="summary/count or dropped contract failed",
        ):
            probe._parse_backoff_trace(stdout.replace(old, new))


def test_parse_backoff_trace_rejects_two_or_nonfinal_v3_terminals_at_position_gate(
) -> None:
    terminal_0 = (
        "IZANAGI_BACKOFF_TRACE v=3 seq=0 tsc=100 window_us=11 "
        "window_commits=10000 trigger=3 backoff_before=101 backoff_after=101 "
        "gradient_sign=0 step_us=1 ceiling_us=1000 ceiling_changed=0 "
        "parity_branch=-1 recommended_delta_sign=0 assigned_invert=-1 "
        "inversion_realized=0 both_actions_feasible=0 terminal_flush=1"
    )
    terminal_1 = terminal_0.replace("seq=0", "seq=1").replace(
        "tsc=100", "tsc=200"
    )
    normal_1 = (
        "IZANAGI_BACKOFF_TRACE v=3 seq=1 tsc=200 window_us=10 "
        "window_commits=10000 trigger=1 backoff_before=100 backoff_after=101 "
        "gradient_sign=1 step_us=1 ceiling_us=1000 ceiling_changed=0 "
        "parity_branch=-1 recommended_delta_sign=1 assigned_invert=0 "
        "inversion_realized=0 both_actions_feasible=1 terminal_flush=0"
    )
    two_terminals = "\n".join(
        (
            terminal_0,
            terminal_1,
            "IZANAGI_BACKOFF_TRACE_SUMMARY v=3 updates=0 retained=0 "
            "dropped=0 flushes=2",
        )
    )
    nonfinal_terminal = "\n".join(
        (
            terminal_0,
            normal_1,
            "IZANAGI_BACKOFF_TRACE_SUMMARY v=3 updates=1 retained=1 "
            "dropped=0 flushes=1",
        )
    )

    for candidate in (two_terminals, nonfinal_terminal):
        with pytest.raises(
            ValueError,
            match="permits zero terminals or one final terminal",
        ):
            probe._parse_backoff_trace(candidate)


def test_directional_success_v2_is_stratified_by_current_assignment() -> None:
    events = [
        {
            "backoff_before": 100.0,
            "backoff_after": 101.0,
            "window_commits": 100,
            "window_us": 10,
            "assigned_invert": 0,
            "inversion_realized": 0,
        },
        {
            "backoff_before": 100.0,
            "backoff_after": 99.0,
            "window_commits": 90,
            "window_us": 10,
            "assigned_invert": 1,
            "inversion_realized": 1,
        },
        {
            "backoff_before": 100.0,
            "backoff_after": 101.0,
            "window_commits": 80,
            "window_us": 10,
            "assigned_invert": 1,
            "inversion_realized": 0,
        },
        {
            "backoff_before": 100.0,
            "backoff_after": 99.0,
            "window_commits": 90,
            "window_us": 10,
            "assigned_invert": 1,
            "inversion_realized": 0,
        },
    ]
    assert probe._directional_success(events) == {
        "scored": 3,
        "successes": 2,
        "rate": 2 / 3,
        "assigned_forward": {"scored": 1, "successes": 0, "rate": 0.0},
        "assigned_invert": {"scored": 2, "successes": 2, "rate": 1.0},
        "realized_invert": {"scored": 1, "successes": 1, "rate": 1.0},
    }


def test_trace_parser_rejects_summary_without_any_event() -> None:
    with pytest.raises(ValueError, match="at least one event"):
        probe._parse_backoff_trace(
            "IZANAGI_BACKOFF_TRACE_SUMMARY v=1 updates=0 retained=0 dropped=0\n"
        )


def test_directional_success_does_not_score_zero_action() -> None:
    events = [
        {
            "backoff_before": 1.0,
            "backoff_after": 1.0,
            "window_commits": 100,
            "window_us": 10.0,
        },
        {
            "backoff_before": 1.0,
            "backoff_after": 2.0,
            "window_commits": 120,
            "window_us": 10.0,
        },
    ]
    assert probe._directional_success(events) == {
        "scored": 0,
        "successes": 0,
        "rate": None,
    }


def test_counterfactual_stack_artifacts_use_schema_v3() -> None:
    assert probe.LEGACY_SCHEMA_VERSION == (
        "izanagi-cicada-adaptive-3const-probe/v2"
    )
    assert probe.LEGACY_TRACE_SCHEMA_VERSION == (
        "izanagi-dynamic-backoff-trace/v2"
    )
    assert probe.UNSUPPORTED_V2_CERTIFICATION_SCHEMA_VERSION == (
        "izanagi-cicada-adaptive-3const-certification/v2"
    )
    assert probe.UNSUPPORTED_V2_GROUP_RECEIPT_SCHEMA_VERSION == (
        "izanagi-cicada-adaptive-3const-certification-group/v2"
    )
    assert probe.SCHEMA_VERSION == "izanagi-cicada-adaptive-3const-probe/v3"
    assert probe.TRACE_SCHEMA_VERSION == "izanagi-dynamic-backoff-trace/v3"
    assert probe.COHORT2_TRACE_SCHEMA_VERSION == (
        "izanagi-dynamic-backoff-trace/v4"
    )
    assert probe.CERTIFICATION_SCHEMA_VERSION == (
        "izanagi-cicada-adaptive-3const-certification/v3"
    )
    assert probe.GROUP_RECEIPT_SCHEMA_VERSION == (
        "izanagi-cicada-adaptive-3const-certification-group/v3"
    )
    assert probe._artifact_contract_metadata(
        backoff_trace=False,
        cells_text=TRACE_CELLS,
        workloads_text="write-heavy,balanced,read-heavy",
        threads_text="24,48",
        rep_index=0,
        reps_per_job=1,
        extime=3,
    ) == {
        "schema_version": probe.SCHEMA_VERSION,
        "not_certified": (
            "trace-disabled performance runs only; no serializability check was run"
        ),
    }
    assert probe._artifact_contract_metadata(
        backoff_trace=True,
        cells_text=TRACE_CELLS,
        workloads_text="write-heavy,balanced,read-heavy",
        threads_text="24,48",
        rep_index=0,
        reps_per_job=1,
        extime=3,
    ) == {
        "schema_version": probe.TRACE_SCHEMA_VERSION,
        "not_certified": (
            "trace-enabled diagnostic runs only; no serializability check was run"
        ),
    }
    assert set(probe.CERT_CLAIMS) == set(probe.CERT_CELLS)
    assert probe.CERT_CELLS == (
        probe.CERT_TUNED_CELL,
        probe.CERT_DYNAMIC_CELL,
        probe.CERT_COHORT2_POLICY1_CELL,
        probe.CERT_COHORT2_POLICY2_CELL,
    )
    assert probe.CERT_EXTIME_BY_CELL == {
        probe.CERT_TUNED_CELL: 3,
        probe.CERT_DYNAMIC_CELL: 3,
        probe.CERT_COHORT2_POLICY1_CELL: 6,
        probe.CERT_COHORT2_POLICY2_CELL: 6,
    }
    assert probe.CERT_CLAIMS[probe.CERT_TUNED_CELL] == probe.ALLOWED_GROUP_CLAIM
    assert "cw-as-dyn" in probe.CERT_CLAIMS[probe.CERT_DYNAMIC_CELL]
    assert "機構の各枝の被覆は認証しない" in probe.CERT_CLAIMS[
        probe.CERT_DYNAMIC_CELL
    ]
    assert "step policy 1" in probe.CERT_CLAIMS[
        probe.CERT_COHORT2_POLICY1_CELL
    ]
    assert "default compile seed 11400714819323198485" in probe.CERT_CLAIMS[
        probe.CERT_COHORT2_POLICY2_CELL
    ]
    assert probe._cell_identity(probe.CERT_DYNAMIC_CELL) == {
        "cell": "cw-as-dyn",
        "back_off": 1,
        "step_us": 1.0,
        "ceiling_us": 1000,
        "update_us": 2560,
        "count_window": 10000,
        "count_cap_us": 10240,
        "step_adapt": 1,
        "step_min_us": 1.0,
        "step_max_us": 4.0,
        "dyn_ceiling": 1,
        "cell_format_fields": 11,
    }


def test_legacy_v2_performance_artifact_remains_readable(tmp_path: Path) -> None:
    artifact = tmp_path / "legacy-v2.json"
    artifact.write_text(
        json.dumps(
            {
                "schema_version": probe.LEGACY_SCHEMA_VERSION,
                "kind": "performance-only-probe",
                "not_certified": (
                    "trace-disabled performance runs only; "
                    "no serializability check was run"
                ),
            }
        )
        + "\n",
        encoding="utf-8",
    )
    assert probe._performance_artifact_identity(
        artifact, hashlib.sha256(artifact.read_bytes()).hexdigest()
    ) == {
        "path": str(artifact.resolve(strict=True)),
        "sha256": hashlib.sha256(artifact.read_bytes()).hexdigest(),
    }


def test_not_certified_text_is_mode_specific_without_changing_performance_identity(
    tmp_path: Path,
) -> None:
    common = {
        "cells_text": TRACE_CELLS,
        "workloads_text": "write-heavy,balanced,read-heavy",
        "threads_text": "24,48",
        "rep_index": 0,
        "reps_per_job": 1,
        "extime": 3,
    }
    performance = probe._artifact_contract_metadata(
        backoff_trace=False, **common
    )
    diagnostic = probe._artifact_contract_metadata(
        backoff_trace=True, **common
    )
    assert performance["not_certified"] == (
        "trace-disabled performance runs only; no serializability check was run"
    )
    assert diagnostic["not_certified"] == (
        "trace-enabled diagnostic runs only; no serializability check was run"
    )

    artifact = tmp_path / "performance.json"
    artifact.write_text(
        json.dumps(
            {
                "schema_version": probe.SCHEMA_VERSION,
                "kind": "performance-only-probe",
                "not_certified": (
                    "trace-disabled performance runs only; "
                    "no serializability check was run"
                ),
            }
        )
        + "\n",
        encoding="utf-8",
    )
    assert probe._performance_artifact_identity(
        artifact, hashlib.sha256(artifact.read_bytes()).hexdigest()
    ) == {
        "path": str(artifact.resolve(strict=True)),
        "sha256": hashlib.sha256(artifact.read_bytes()).hexdigest(),
    }


def test_v2_certification_and_group_artifacts_are_explicitly_unsupported(
    tmp_path: Path,
) -> None:
    certification = tmp_path / "certification-v2.json"
    certification.write_text(
        json.dumps(
            {"schema_version": probe.UNSUPPORTED_V2_CERTIFICATION_SCHEMA_VERSION}
        )
        + "\n",
        encoding="utf-8",
    )
    with pytest.raises(probe.CertificationReject) as caught:
        probe._validated_certification_row(
            certification,
            attempt_id="attempt-test",
            expected_verifier_identity={},
            expected_verifier_identity_file_sha256="a" * 64,
            performance_identity={},
        )
    assert caught.value.reason == "legacy-certification-schema-unsupported"
    assert caught.value.detail == (
        "v2 certification artifacts are unsupported; group aggregation accepts "
        "v3 certification artifacts only"
    )

    group = tmp_path / "group-v2.json"
    group.write_text(
        json.dumps(
            {"schema_version": probe.UNSUPPORTED_V2_GROUP_RECEIPT_SCHEMA_VERSION}
        )
        + "\n",
        encoding="utf-8",
    )
    with pytest.raises(probe.CertificationReject) as caught:
        probe._validate_published_group(
            group,
            [],
            tmp_path / "unused-performance.json",
            "b" * 64,
            "attempt-test",
            {},
            "c" * 64,
        )
    assert caught.value.reason == "legacy-group-receipt-schema-unsupported"
    assert caught.value.detail == (
        "v2 group receipt artifacts are unsupported; published receipt validation "
        "accepts v3 group receipt artifacts only"
    )


def test_counterfactual_artifacts_record_exact_preregistration_sha_only_on_exact_axes(
    tmp_path: Path,
) -> None:
    expected = hashlib.sha256(
        probe.COUNTERFACTUAL_PREREGISTRATION.read_bytes()
    ).hexdigest()
    exact = {
        "backoff_trace": True,
        "cells_text": probe.COUNTERFACTUAL_TRACE_CELLS_TEXT,
        "step_policy_seed": 5744733223455690259,
        "workloads_text": "write-heavy,balanced,read-heavy",
        "threads_text": "24,48",
        "rep_index": 0,
        "reps_per_job": 1,
        "extime": 3,
        "backoff_trace_terminal_us": 0,
    }
    assert probe._artifact_contract_metadata(**exact) == {
        "schema_version": probe.TRACE_SCHEMA_VERSION,
        "not_certified": (
            "trace-enabled diagnostic runs only; no serializability check was run"
        ),
        "counterfactual_preregistration": expected,
    }
    assert re.fullmatch(r"[0-9a-f]{64}", expected)
    assert "counterfactual_preregistration" not in probe._artifact_contract_metadata(
        backoff_trace=True,
        cells_text=probe.TRACE_CELLS_TEXT,
        workloads_text=exact["workloads_text"],
        threads_text=exact["threads_text"],
        rep_index=0,
        reps_per_job=1,
        extime=3,
    )
    nonmonotonic = probe._artifact_contract_metadata(
        backoff_trace=True,
        cells_text=probe.NONMONOTONIC_TRACE_CELLS_TEXT,
        workloads_text="write-heavy",
        threads_text="48",
        rep_index=0,
        reps_per_job=1,
        extime=3,
        backoff_trace_terminal_us=0,
    )
    assert nonmonotonic == {
        "schema_version": probe.TRACE_SCHEMA_VERSION,
        "not_certified": probe.DIAGNOSTIC_NOT_CERTIFIED,
    }
    assert "counterfactual_preregistration" not in nonmonotonic
    for field, drift in (
        ("backoff_trace", False),
        ("cells_text", probe.COUNTERFACTUAL_TRACE_CELLS_TEXT[:-1] + "1"),
        ("workloads_text", "write-heavy"),
        ("threads_text", "48"),
        ("rep_index", 1),
        ("reps_per_job", 2),
        ("extime", 4),
        ("backoff_trace_terminal_us", 1),
    ):
        changed = {**exact, field: drift}
        assert "counterfactual_preregistration" not in (
            probe._artifact_contract_metadata(**changed)
        )

    rows = [
        {
            **probe._cell_identity(cell),
            **probe._counterfactual_row_metadata(
                preregistration_sha256=expected,
                cell=cell,
                step_policy_seed=7,
            ),
        }
        for cell in probe.COUNTERFACTUAL_TRACE_CELLS
    ]
    assert all(row["counterfactual_preregistration"] == expected for row in rows)
    assert "step_policy_seed" not in rows[0]
    assert "step_policy_seed" not in rows[1]
    assert rows[2]["step_policy_seed"] == 7
    out = tmp_path / "counterfactual.json"
    probe._append_journal(out, rows[2])
    journal_row = json.loads(
        Path(str(out) + ".journal.jsonl").read_text(encoding="utf-8")
    )
    assert journal_row["counterfactual_preregistration"] == expected
    assert journal_row["step_policy_seed"] == 7


def test_cohort2_trace_metadata_uses_independent_exact_v4_predicate() -> None:
    cohort1 = probe._artifact_contract_metadata(
        step_policy_seed=5744733223455690259,
        backoff_trace=True,
        cells_text=probe.COUNTERFACTUAL_TRACE_CELLS_TEXT,
        workloads_text="write-heavy,balanced,read-heavy",
        threads_text="24,48",
        rep_index=0,
        reps_per_job=1,
        extime=3,
    )
    cohort1_expected = hashlib.sha256(
        probe.COUNTERFACTUAL_PREREGISTRATION.read_bytes()
    ).hexdigest()
    assert cohort1 == {
        "schema_version": probe.TRACE_SCHEMA_VERSION,
        "not_certified": probe.DIAGNOSTIC_NOT_CERTIFIED,
        "counterfactual_preregistration": cohort1_expected,
    }

    exact = {
        "backoff_trace": True,
        "cells_text": probe.COUNTERFACTUAL_COHORT2_TRACE_CELLS_TEXT,
        "step_policy_seed": 14481721328008317845,
        "workloads_text": "write-heavy,balanced,read-heavy",
        "threads_text": "24,48",
        "rep_index": 0,
        "reps_per_job": 1,
        "extime": 6,
        "backoff_trace_terminal_us": 5_000_000,
    }
    cohort2_expected = hashlib.sha256(
        probe.COUNTERFACTUAL_COHORT2_PREREGISTRATION.read_bytes()
    ).hexdigest()
    assert probe._artifact_contract_metadata(**exact) == {
        "schema_version": probe.COHORT2_TRACE_SCHEMA_VERSION,
        "not_certified": probe.DIAGNOSTIC_NOT_CERTIFIED,
        "counterfactual_preregistration": cohort2_expected,
    }
    assert cohort2_expected == (
        "8b4127f4be895da0d25da88b0837f679ecf06d43ab656b16d2944146b9f7a9e9"
    )
    for field, drift in (
        ("backoff_trace", False),
        ("cells_text", probe.COUNTERFACTUAL_COHORT2_TRACE_CELLS_TEXT[:-1] + "1"),
        ("workloads_text", "balanced"),
        ("threads_text", "48"),
        ("rep_index", 1),
        ("reps_per_job", 2),
        ("extime", 5),
        ("backoff_trace_terminal_us", 0),
    ):
        changed = {**exact, field: drift}
        metadata = probe._artifact_contract_metadata(**changed)
        assert "counterfactual_preregistration" not in metadata
        assert metadata["schema_version"] != probe.COHORT2_TRACE_SCHEMA_VERSION


def test_step_policy_seed_accepts_uint64_endpoints_and_default_calls() -> None:
    parser = probe._argument_parser()
    for text, expected in (("0", 0), ("18446744073709551615", 2**64 - 1)):
        args = parser.parse_args(
            [
                "--cells",
                COUNTERFACTUAL_TRACE_CELLS,
                "--step-policy-seed",
                text,
                "--out",
                "unused.json",
            ]
        )
        assert args.step_policy_seed == expected
    args = parser.parse_args(["--cells", VALID_CELLS, "--out", "unused.json"])
    assert args.step_policy_seed is None


def test_public_certification_rejects_step_policy_seed_before_dispatch(
    tmp_path: Path,
) -> None:
    argv = _certify_argv(tmp_path)
    argv.extend(("--step-policy-seed", "7"))
    with pytest.raises(probe.CertificationReject) as caught:
        probe.main(argv)
    assert caught.value.reason == "step-policy-seed-certification-conflict"


def test_perf_and_diagnostic_binary_trace_counts_fail_closed() -> None:
    probe._validate_trace_binary_counts(0, 0, backoff_trace=False)
    probe._validate_trace_binary_counts(1, 2, backoff_trace=True)
    for counts, enabled in (((1, 0), False), ((0, 1), False), ((0, 1), True), ((1, 0), True)):
        with pytest.raises(RuntimeError):
            probe._validate_trace_binary_counts(
                counts[0], counts[1], backoff_trace=enabled
            )


def test_pbs_dynamic_output_and_plus_transport_are_fail_closed() -> None:
    text = PBS.read_text(encoding="utf-8")
    assert "IZANAGI_T2187_BACKOFF_TRACE must be 0 or 1" in text
    assert "IZANAGI_T2187_OUT_DIR is required for dynamic-backoff output" in text
    assert (
        "DYNAMIC_OUT_PREFIX=/work/1/SFC/tanab/izanagi-job-evidence/"
        "dynamic-backoff/"
    ) in text
    assert 'CELLS=${CELLS_RAW//+/,}' in text
    assert '"$CERT_TUNED_CELL"|"$CERT_DYNAMIC_CELL")' in text
    assert '"$CERT_COHORT2_POLICY1_CELL")' in text
    assert '"$CERT_COHORT2_POLICY2_CELL")' in text
    assert '"${BACKOFF_TRACE_ARGS[@]}"' in text
    assert 'export IZANAGI_T2187_REPO_HEAD="$REPO_HEAD"' in text
    assert '--repo-head "$REPO_HEAD"' in text
    assert "STEP_POLICY_SEED=${IZANAGI_T2187_STEP_POLICY_SEED:-}" in text
    assert "EXTIME=${IZANAGI_T2187_EXTIME:-3}" in text
    assert "IZANAGI_T2187_EXTIME must be an ASCII positive integer" in text
    assert '! "$STEP_POLICY_SEED" =~ ^[0-9]+$' in text
    assert "IZANAGI_T2187_STEP_POLICY_SEED is required for policy 2" in text
    assert text.count("--step-policy-seed") == 1
    performance_branch = text.split(
        'if [[ "$MODE" == performance ]]; then', 1
    )[1].split('OUT="$OUT_DIR/certify-', 1)[0]
    certification_branch = text.split(
        'OUT="$OUT_DIR/certify-', 1
    )[1]
    assert '"${STEP_POLICY_SEED_ARGS[@]}"' in performance_branch
    assert '"${STEP_POLICY_SEED_ARGS[@]}"' in certification_branch
    assert '--extime "$EXTIME"' in performance_branch
    assert (
        '--backoff-trace-terminal-us "$CCBENCH_BACKOFF_TRACE_TERMINAL_US"'
        in performance_branch
    )
    assert '--extime "$EXTIME"' in certification_branch


def test_pbs_certification_seed_and_thread_closed_tables_are_exact() -> None:
    text = PBS.read_text(encoding="utf-8")
    seed_block = text.split("cert_policy2_seed_allowed() {", 1)[1].split(
        "}\n", 1
    )[0]
    assert {int(value) for value in re.findall(r"\b[0-9]{15,20}\b", seed_block)} == (
        set(probe.CERT_POLICY2_STEP_POLICY_SEEDS)
    )
    assert "certify policy 2 requires an explicit step policy seed" in text
    assert "certify policy 2 seed is outside the exact closed table" in text
    assert (
        '[[ "$THREADS_RAW" == 24 || "$THREADS_RAW" == 48 ]] && '
        "CERT_THREAD_OK=1"
    ) in text
    assert '[[ "$THREADS_RAW" == 48 ]] && CERT_THREAD_OK=1' in text
    seed_args_position = text.index("STEP_POLICY_SEED_ARGS=()")
    performance_branch_position = text.index(
        'if [[ "$MODE" == performance ]]; then'
    )
    assert seed_args_position < performance_branch_position
    certification_exec = text.split('OUT="$OUT_DIR/certify-', 1)[1]
    assert '"${STEP_POLICY_SEED_ARGS[@]}"' in certification_exec


def test_execution_identity_fields_have_exact_types_and_file_hashes(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(probe, "_validated_repo_clean", lambda value: value == "1")
    monkeypatch.setattr(sys, "argv", [str(DRIVER), "--repo-clean", "1"])
    identity = probe._execution_identity("1")
    assert identity == {
        "driver_sha256": hashlib.sha256(DRIVER.read_bytes()).hexdigest(),
        "pbs_sha256": hashlib.sha256(PBS.read_bytes()).hexdigest(),
        "driver_argv": [str(DRIVER), "--repo-clean", "1"],
        "repo_status_clean": True,
    }


def test_driver_repo_clean_attestation_is_rechecked(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        probe.subprocess,
        "run",
        lambda *_args, **_kwargs: SimpleNamespace(stdout=" M tracked.py\n"),
    )
    with pytest.raises(RuntimeError, match="not tracked-clean"):
        probe._validated_repo_clean("1")


def test_pbs_rechecks_repo_clean_and_passes_identity_and_prologue_args() -> None:
    text = PBS.read_text(encoding="utf-8")
    assert 'git -C "$REPO_ROOT" status --porcelain --untracked-files=no' in text
    assert 'export IZANAGI_T2187_REPO_CLEAN=1' in text
    assert text.count("--repo-clean 1") == 2
    assert text.count('--prologue-elapsed-s "$PROLOGUE_ELAPSED_S"') == 2
    assert text.count('--prologue-cpu-s "$PROLOGUE_CPU_S"') == 2


def test_driver_rejects_dynamic_output_outside_dedicated_namespace(
    tmp_path: Path,
) -> None:
    with pytest.raises(ValueError, match="dynamic output must be below"):
        probe._validate_dynamic_output_path(tmp_path / "result.json")
    probe._validate_dynamic_output_path(
        probe.DYNAMIC_OUT_PREFIX / "trace" / "result.json"
    )


@pytest.mark.parametrize(
    "binding",
    ("receipt", "result-path", "performance-artifact"),
)
def test_dynamic_certification_rejects_each_foreign_namespace(
    tmp_path: Path, binding: str
) -> None:
    certify_root = tmp_path / "certify"
    performance_root = tmp_path / "perf"
    result_paths = [certify_root / f"result-{index}.json" for index in range(24)]
    args = SimpleNamespace(
        group_receipt_out=certify_root / "group.json",
        group_result_path=result_paths,
        performance_artifact=performance_root / "performance.json",
        out=str(result_paths[0]),
    )
    if binding == "receipt":
        args.group_receipt_out = tmp_path / "foreign" / "group.json"
    elif binding == "result-path":
        args.group_result_path[0] = tmp_path / "foreign" / "result.json"
    else:
        args.performance_artifact = tmp_path / "foreign" / "performance.json"
    old_certify = probe.DYNAMIC_CERTIFY_PREFIX
    old_performance = probe.DYNAMIC_PERFORMANCE_PREFIX
    try:
        probe.DYNAMIC_CERTIFY_PREFIX = certify_root
        probe.DYNAMIC_PERFORMANCE_PREFIX = performance_root
        for cell in probe.DYNAMIC_CERT_CELLS:
            with pytest.raises(probe.CertificationReject) as caught:
                probe._validate_dynamic_certification_namespaces(args, cell)
            assert caught.value.reason == "dynamic-certification-namespace-invalid"
    finally:
        probe.DYNAMIC_CERTIFY_PREFIX = old_certify
        probe.DYNAMIC_PERFORMANCE_PREFIX = old_performance


def test_dynamic_performance_artifact_rejects_certify_identity_drift(
    tmp_path: Path,
) -> None:
    patch_identity = probe._patch_stack_identity()
    repo_head = "a" * 40
    prereg_sha256 = "b" * 64
    execution_identity = {
        "driver_sha256": hashlib.sha256(DRIVER.read_bytes()).hexdigest(),
        "pbs_sha256": hashlib.sha256(PBS.read_bytes()).hexdigest(),
        "driver_argv": [str(DRIVER), "--mode", "performance"],
        "repo_status_clean": True,
    }
    document = {
        "schema_version": probe.SCHEMA_VERSION,
        "kind": "performance-only-probe",
        "not_certified": probe.NOT_CERTIFIED,
        "repo_head": repo_head,
        "prereg_sha256": prereg_sha256,
        "extime_s": 3,
        "patch_stack_sha256": patch_identity["patch_stack_sha256"],
        "ccbench_head": probe.PIN_FULL,
        **execution_identity,
        "cells": [
            {**probe._cell_identity(probe.CERT_DYNAMIC_CELL), "threads": 48}
        ],
    }
    performance = tmp_path / "performance.json"

    def write_and_digest() -> str:
        performance.write_text(json.dumps(document) + "\n", encoding="utf-8")
        return hashlib.sha256(performance.read_bytes()).hexdigest()

    expected = {
        "expected_repo_head": repo_head,
        "expected_prereg_sha256": prereg_sha256,
        "expected_patch_stack_sha256": patch_identity["patch_stack_sha256"],
        "required_cell": probe.CERT_DYNAMIC_CELL,
        "expected_extime": 3,
        "expected_axes": probe.CertificationAxes(
            probe.CERT_DYNAMIC_CELL, 48, None
        ),
    }
    probe._performance_artifact_identity(
        performance, write_and_digest(), **expected
    )
    document["repo_head"] = "c" * 40
    with pytest.raises(probe.CertificationReject) as caught:
        probe._performance_artifact_identity(
            performance, write_and_digest(), **expected
        )
    assert caught.value.reason == "performance-artifact-identity-mismatch"
    document["repo_head"] = repo_head
    document["extime_s"] = 4
    with pytest.raises(probe.CertificationReject) as caught:
        probe._performance_artifact_identity(
            performance, write_and_digest(), **expected
        )
    assert caught.value.reason == "performance-artifact-identity-mismatch"


def test_cohort2_performance_binding_requires_extime_and_default_seed(
    tmp_path: Path,
) -> None:
    patch_identity = probe._patch_stack_identity()
    repo_head = "a" * 40
    prereg_sha256 = probe._prereg_sha256()
    cell = probe.CERT_COHORT2_POLICY2_CELL
    actual_seed = probe.CERT_PREREGISTERED_STEP_POLICY_SEEDS[0]
    row = {
        **probe._cell_identity(cell),
        "genome": probe.genome_for(
            cell, step_policy_seed=actual_seed
        ).canonical(),
        "step_policy_seed": actual_seed,
        "threads": 48,
    }
    document = {
        "schema_version": probe.SCHEMA_VERSION,
        "kind": "performance-only-probe",
        "not_certified": probe.NOT_CERTIFIED,
        "repo_head": repo_head,
        "prereg_sha256": prereg_sha256,
        "extime_s": 6,
        "patch_stack_sha256": patch_identity["patch_stack_sha256"],
        "ccbench_head": probe.PIN_FULL,
        "driver_sha256": hashlib.sha256(DRIVER.read_bytes()).hexdigest(),
        "pbs_sha256": hashlib.sha256(PBS.read_bytes()).hexdigest(),
        "driver_argv": [str(DRIVER), "--mode", "performance"],
        "repo_status_clean": True,
        "cells": [row],
    }
    performance = tmp_path / "cohort2-performance.json"

    def write_and_digest() -> str:
        performance.write_text(json.dumps(document) + "\n", encoding="utf-8")
        return hashlib.sha256(performance.read_bytes()).hexdigest()

    expected = {
        "expected_repo_head": repo_head,
        "expected_prereg_sha256": prereg_sha256,
        "expected_patch_stack_sha256": patch_identity["patch_stack_sha256"],
        "required_cell": cell,
        "expected_extime": 6,
        "expected_axes": probe.CertificationAxes(cell, 48, actual_seed),
    }
    probe._performance_artifact_identity(
        performance, write_and_digest(), **expected
    )
    row["step_policy_seed"] = probe.STOCK_STEP_POLICY_SEED
    with pytest.raises(probe.CertificationReject) as caught:
        probe._performance_artifact_identity(
            performance, write_and_digest(), **expected
        )
    assert caught.value.reason == "performance-artifact-identity-mismatch"
    row["step_policy_seed"] = actual_seed
    row["threads"] = 24
    with pytest.raises(probe.CertificationReject) as caught:
        probe._performance_artifact_identity(
            performance, write_and_digest(), **expected
        )
    assert caught.value.reason == "performance-artifact-identity-mismatch"


def test_point_journal_is_append_only_jsonl(tmp_path: Path) -> None:
    out = tmp_path / "result.json"
    probe._append_journal(out, {"point": 1})
    probe._append_journal(out, {"point": 2})
    journal = Path(str(out) + ".journal.jsonl")
    assert [json.loads(line) for line in journal.read_text().splitlines()] == [
        {"point": 1},
        {"point": 2},
    ]
    assert not out.exists()


def test_backoff_trace_and_certification_modes_are_disjoint(tmp_path: Path) -> None:
    argv = _certify_argv(tmp_path)
    argv.insert(0, "--backoff-trace")
    with pytest.raises(probe.CertificationReject) as caught:
        probe.main(argv)
    assert caught.value.reason == "backoff-trace-certification-conflict"


def test_backoff_trace_mode_requires_exact_diagnostic_axes(tmp_path: Path) -> None:
    parser = probe._argument_parser()
    argv = [
        "--backoff-trace",
        "--cells",
        TRACE_CELLS,
        "--workloads",
        "write-heavy,balanced,read-heavy",
        "--threads",
        "24,48",
        "--reps-per-job",
        "1",
        "--extime",
        "3",
        "--out",
        str(probe.DYNAMIC_OUT_PREFIX / "trace" / "test.json"),
    ]
    args = parser.parse_args(argv)
    cells = probe.parse_cells(args.cells)
    workloads = probe._parse_workloads(args.workloads)
    threads = probe._parse_threads(args.threads)
    probe._validate_backoff_trace_contract(args, cells, workloads, threads)
    for option, drift in (
        ("--cells", DYNAMIC_CERT_CELL),
        ("--workloads", "balanced"),
        ("--threads", "48"),
        ("--extime", "4"),
    ):
        changed = list(argv)
        changed[changed.index(option) + 1] = drift
        args = parser.parse_args(changed)
        cells = probe.parse_cells(args.cells)
        workloads = probe._parse_workloads(args.workloads)
        threads = probe._parse_threads(args.threads)
        with pytest.raises(ValueError, match="requires exact"):
            probe._validate_backoff_trace_contract(
                args, cells, workloads, threads
            )

    nonmonotonic_argv = list(argv)
    for option, exact in (
        ("--cells", NONMONOTONIC_TRACE_CELLS),
        ("--workloads", "write-heavy"),
        ("--threads", "48"),
    ):
        nonmonotonic_argv[nonmonotonic_argv.index(option) + 1] = exact
    args = parser.parse_args(nonmonotonic_argv)
    probe._validate_backoff_trace_contract(
        args,
        probe.parse_cells(args.cells),
        probe._parse_workloads(args.workloads),
        probe._parse_threads(args.threads),
    )
    for option, drift in (
        ("--workloads", "balanced"),
        ("--threads", "24"),
        ("--extime", "4"),
    ):
        changed = list(nonmonotonic_argv)
        changed[changed.index(option) + 1] = drift
        args = parser.parse_args(changed)
        with pytest.raises(ValueError, match="requires exact"):
            probe._validate_backoff_trace_contract(
                args,
                probe.parse_cells(args.cells),
                probe._parse_workloads(args.workloads),
                probe._parse_threads(args.threads),
            )


def test_backoff_trace_contract_accepts_only_four_exact_cell_literals(
    tmp_path: Path,
) -> None:
    parser = probe._argument_parser()

    def inputs(
        cells_text: str,
        workloads_text: str = "write-heavy,balanced,read-heavy",
        threads_text: str = "24,48",
        *,
        extime: int = 3,
        terminal_us: int = 0,
        seed: int | None = None,
    ):
        args = parser.parse_args(
            [
                "--backoff-trace",
                "--cells",
                cells_text,
                "--workloads",
                workloads_text,
                "--threads",
                threads_text,
                "--reps-per-job",
                "1",
                "--extime",
                str(extime),
                "--backoff-trace-terminal-us",
                str(terminal_us),
                "--out",
                str(tmp_path / "unused.json"),
            ]
        )
        if seed is not None:
            args.step_policy_seed = seed
        return (
            args,
            probe.parse_cells(args.cells),
            probe._parse_workloads(args.workloads),
            probe._parse_threads(args.threads),
        )

    assert tuple(probe.BACKOFF_TRACE_CONTRACTS) == (
        probe.TRACE_CELLS_TEXT,
        probe.COUNTERFACTUAL_TRACE_CELLS_TEXT,
        probe.COUNTERFACTUAL_COHORT2_TRACE_CELLS_TEXT,
        probe.NONMONOTONIC_TRACE_CELLS_TEXT,
    )
    for exact, workloads, threads, extime, terminal_us in (
        (TRACE_CELLS, "write-heavy,balanced,read-heavy", "24,48", 3, 0),
        (
            COUNTERFACTUAL_TRACE_CELLS,
            "write-heavy,balanced,read-heavy",
            "24,48",
            3,
            0,
        ),
        (
            COUNTERFACTUAL_COHORT2_TRACE_CELLS,
            "write-heavy,balanced,read-heavy",
            "24,48",
            6,
            5_000_000,
        ),
        (NONMONOTONIC_TRACE_CELLS, "write-heavy", "48", 3, 0),
    ):
        probe._validate_backoff_trace_contract(
            *inputs(
                exact,
                workloads,
                threads,
                extime=extime,
                terminal_us=terminal_us,
                seed={
                    COUNTERFACTUAL_TRACE_CELLS: 5744733223455690259,
                    COUNTERFACTUAL_COHORT2_TRACE_CELLS: 14481721328008317845,
                }.get(exact),
            )
        )

    counterfactual_items = COUNTERFACTUAL_TRACE_CELLS.split(",")
    negative_inputs = (
        inputs(COUNTERFACTUAL_TRACE_CELLS[:-1] + "1"),
        inputs(",".join((counterfactual_items[0], counterfactual_items[2]))),
        inputs(TRACE_CELLS + "," + COUNTERFACTUAL_TRACE_CELLS),
        inputs(COUNTERFACTUAL_TRACE_CELLS, threads_text="24"),
        inputs(COUNTERFACTUAL_COHORT2_TRACE_CELLS, extime=3),
        inputs(
            COUNTERFACTUAL_COHORT2_TRACE_CELLS,
            extime=6,
            terminal_us=4_999_999,
        ),
        inputs(NONMONOTONIC_TRACE_CELLS),
        inputs(NONMONOTONIC_TRACE_CELLS, "write-heavy", "24"),
        inputs(NONMONOTONIC_TRACE_CELLS, "write-heavy", "48", extime=4),
        inputs(
            NONMONOTONIC_TRACE_CELLS,
            "write-heavy",
            "48",
            terminal_us=1,
        ),
        (
            inputs(TRACE_CELLS)[0],
            probe.COUNTERFACTUAL_TRACE_CELLS,
            probe.TRACE_WORKLOADS,
            probe.TRACE_THREADS,
        ),
    )
    for values in negative_inputs:
        with pytest.raises(ValueError, match="one exact diagnostic cell set"):
            probe._validate_backoff_trace_contract(*values)

    pbs_text = PBS.read_text(encoding="utf-8")
    case_start = pbs_text.index('case "$CELLS_RAW" in')
    case_block = pbs_text[case_start:pbs_text.index("  esac", case_start)]
    pbs_contracts = {}
    branches = re.finditer(
        r'^    (?P<patterns>(?:"\$[A-Z0-9_]+"\|?)+)\)\n'
        r"(?P<body>.*?)(?=^      ;;$)",
        case_block,
        re.MULTILINE | re.DOTALL,
    )
    for branch in branches:
        names = re.findall(r'"\$([A-Z0-9_]+)"', branch.group("patterns"))
        assignments = dict(
            re.findall(
                r"^      (TRACE_(?:WORKLOADS_RAW|THREADS_RAW|EXTIME))=(\S+)$",
                branch.group("body"),
                re.MULTILINE,
            )
        )
        assert set(assignments) == {
            "TRACE_WORKLOADS_RAW",
            "TRACE_THREADS_RAW",
            "TRACE_EXTIME",
        }
        axes = (
            tuple(assignments["TRACE_WORKLOADS_RAW"].split("+")),
            tuple(
                int(value)
                for value in assignments["TRACE_THREADS_RAW"].split("+")
            ),
            int(assignments["TRACE_EXTIME"]),
        )
        for name in names:
            pbs_contracts[name] = axes

    python_contract_by_raw = {
        "TRACE_CELLS_RAW": probe.TRACE_CELLS_TEXT,
        "COUNTERFACTUAL_TRACE_CELLS_RAW": probe.COUNTERFACTUAL_TRACE_CELLS_TEXT,
        "COUNTERFACTUAL_COHORT2_TRACE_CELLS_RAW": (
            probe.COUNTERFACTUAL_COHORT2_TRACE_CELLS_TEXT
        ),
        "NONMONOTONIC_TRACE_CELLS_RAW": probe.NONMONOTONIC_TRACE_CELLS_TEXT,
    }
    assert set(pbs_contracts) == set(python_contract_by_raw)
    for raw_name, cells_text in python_contract_by_raw.items():
        _cells, workloads, threads, extime, _terminal_us = (
            probe.BACKOFF_TRACE_CONTRACTS[cells_text]
        )
        assert pbs_contracts[raw_name] == (workloads, threads, extime)
    assert "CCBENCH_BACKOFF_TRACE_TERMINAL_US=5000000" in pbs_text


def test_two_layer_trace_literals_are_byte_identical() -> None:
    pbs_text = PBS.read_text(encoding="utf-8")

    def raw(name: str) -> str:
        match = re.search(rf"^{name}='([^']*)'$", pbs_text, re.MULTILINE)
        assert match is not None
        return match.group(1)

    assert probe.TRACE_CELLS_TEXT.replace(",", "+") == raw(
        "TRACE_CELLS_RAW"
    )
    assert probe.COUNTERFACTUAL_TRACE_CELLS_TEXT.replace(",", "+") == raw(
        "COUNTERFACTUAL_TRACE_CELLS_RAW"
    )
    assert probe.COUNTERFACTUAL_COHORT2_TRACE_CELLS_TEXT.replace(",", "+") == raw(
        "COUNTERFACTUAL_COHORT2_TRACE_CELLS_RAW"
    )
    assert probe.NONMONOTONIC_TRACE_CELLS_TEXT.replace(",", "+") == raw(
        "NONMONOTONIC_TRACE_CELLS_RAW"
    )
    assert re.findall(
        r"^([A-Z0-9_]*TRACE_CELLS_RAW)=", pbs_text, re.MULTILINE
    ) == [
        "TRACE_CELLS_RAW",
        "COUNTERFACTUAL_TRACE_CELLS_RAW",
        "COUNTERFACTUAL_COHORT2_TRACE_CELLS_RAW",
        "NONMONOTONIC_TRACE_CELLS_RAW",
    ]


def test_pbs_marks_eleven_and_twelve_fields_extended(tmp_path: Path) -> None:
    pbs_text = PBS.read_text(encoding="utf-8")
    start = pbs_text.index("HAS_EXTENDED_CELL=0\n")
    end = pbs_text.index("OUT_DIR=${OUT_DIR_RAW:-$DEFAULT_OUT_DIR}\n", start)
    classification_block = pbs_text[start:end]
    classification_script = tmp_path / "classify-pbs-cells.sh"
    classification_script.write_text(classification_block, encoding="utf-8")
    assert classification_script.read_text(encoding="utf-8") in pbs_text

    def classify(cell: str, out_dir: str = "") -> subprocess.CompletedProcess[str]:
        command = ["/bin/bash", "-x", str(classification_script)]
        assert str(PBS) not in command
        return subprocess.run(
            command,
            check=False,
            capture_output=True,
            text=True,
            env={
                "CELLS_RAW": cell,
                "MODE": "performance",
                "BACKOFF_TRACE": "0",
                "WORKLOADS_RAW": "balanced",
                "THREADS_RAW": "48",
                "OUT_DIR_RAW": out_dir,
                "STEP_POLICY_SEED": "7",
            },
        )

    def assignments(
        completed: subprocess.CompletedProcess[str], name: str
    ) -> list[str]:
        return re.findall(rf"^\+ {name}=([01])$", completed.stderr, re.MULTILINE)

    eleven_fields = "extended-11:1:1:1000:2560:10000:10240:1:1:4:1"
    twelve_fields = "extended-12:1:1:1000:2560:10000:10240:1:1:4:1:2"
    four_colons = "five-fields:1:1:1000:2560"
    for cell in (eleven_fields, twelve_fields):
        completed = classify(cell, "/dynamic-output")
        assert completed.returncode == 0, completed.stderr
        assert assignments(completed, "HAS_EXTENDED_CELL") == ["0", "1"]
        assert assignments(completed, "NEEDS_DYNAMIC_OUT") == ["0", "1"]
    completed = classify(four_colons)
    assert completed.returncode == 0, completed.stderr
    assert assignments(completed, "HAS_EXTENDED_CELL") == ["0"]
    assert assignments(completed, "NEEDS_DYNAMIC_OUT") == ["0"]

    completed = classify(eleven_fields)
    assert completed.returncode == 2
    assert completed.stdout == ""
    assert assignments(completed, "HAS_EXTENDED_CELL") == ["0", "1"]
    assert assignments(completed, "NEEDS_DYNAMIC_OUT") == ["0", "1"]
    assert (
        "IZANAGI_T2187_OUT_DIR is required for dynamic-backoff output\n"
        in completed.stderr
    )


def _policy_contract_values(rep_index: int, **changes):
    seed = EXPECTED_SEEDS_BY_SLOT.get(rep_index, EXPECTED_SEEDS_BY_SLOT[0])
    values = {
        "mode": "performance",
        "backoff_trace": False,
        "cells": EXPECTED_PERMUTATIONS[rep_index % 6],
        "workloads": EXPECTED_POLICY_WORKLOADS,
        "threads": EXPECTED_POLICY_THREADS,
        "rep_index": rep_index,
        "reps_per_job": 1,
        "extime": 3,
        "stage": 1,
        "step_policy_seed": seed,
    }
    values.update(changes)
    args = SimpleNamespace(**values)
    return (
        args,
        probe.parse_cells(args.cells),
        probe._parse_workloads(args.workloads),
        probe._parse_threads(args.threads),
    )


def _policy_metadata_values(rep_index: int, **changes) -> dict:
    args, cells, workloads, threads = _policy_contract_values(rep_index, **changes)
    return {
        "mode": args.mode,
        "backoff_trace": args.backoff_trace,
        "cells_text": args.cells,
        "cells": cells,
        "workloads_text": args.workloads,
        "workloads": workloads,
        "threads_text": args.threads,
        "threads": threads,
        "rep_index": args.rep_index,
        "reps_per_job": args.reps_per_job,
        "extime": args.extime,
        "stage": args.stage,
        "step_policy_seed": args.step_policy_seed,
    }


def _install_policy_performance_runtime(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    *,
    missing_coordinate: tuple[int, int, str, int] | None = None,
) -> tuple[Path, dict[str, int]]:
    monkeypatch.setattr(probe, "PIN_FULL", T2417_SERIES_PIN_FULL)
    monkeypatch.setattr(probe, "CURRENT_PIN", T2417_SERIES_PIN)
    dynamic_root = tmp_path / "dynamic"
    policy_root = dynamic_root / "perf" / "t2417-policy"
    checkout = tmp_path / "checkout"
    checkout.mkdir()
    state = {"rep_index": 0}

    monkeypatch.setattr(probe, "DYNAMIC_OUT_PREFIX", dynamic_root)
    monkeypatch.setattr(probe, "DYNAMIC_PERFORMANCE_PREFIX", dynamic_root / "perf")
    monkeypatch.setattr(probe, "DYNAMIC_POLICY_PERFORMANCE_PREFIX", policy_root)
    monkeypatch.setattr(probe.site_policy, "current_site", lambda: "PEGASUS_COMPUTE")
    monkeypatch.setattr(probe.site_policy, "refuses_heavy_work", lambda _site: False)
    monkeypatch.setattr(probe, "_assert_single_tenant", lambda: None)
    monkeypatch.setattr(probe, "_ccbench_head", lambda _submodule: T2417_SERIES_PIN_FULL)
    monkeypatch.setattr(probe, "assert_pinned_clean", lambda *_args: None)
    monkeypatch.setattr(probe, "_validated_repo_head", lambda _value: "a" * 40)
    monkeypatch.setattr(
        probe,
        "_execution_identity",
        lambda _value: {
            "driver_sha256": hashlib.sha256(b"producer-driver").hexdigest(),
            "pbs_sha256": hashlib.sha256(b"producer-pbs").hexdigest(),
            "driver_argv": ["probe.py", "--mode", "performance"],
            "repo_status_clean": True,
        },
    )
    monkeypatch.setattr(
        probe.buildcache, "compilers_for_current_site", lambda: ("gcc", "g++")
    )
    monkeypatch.setattr(probe, "build_run_context", lambda **_kwargs: object())
    monkeypatch.setattr(probe, "attest_generator_output", lambda *_args, **_kwargs: object())

    @contextmanager
    def fake_checkout(*_args, **_kwargs):
        yield str(checkout)

    @contextmanager
    def fake_patch_stack(*_args, **_kwargs):
        yield ()

    monkeypatch.setattr(probe, "isolated_checkout", fake_checkout)
    monkeypatch.setattr(probe, "_applied_patch_stack", fake_patch_stack)

    def fake_evidence(genome, ccbench_commit, **_kwargs):
        canonical = genome.canonical()
        return SimpleNamespace(
            ccbench_commit=ccbench_commit,
            genome_sha256=hashlib.sha256(canonical.encode()).hexdigest(),
            src_token=hashlib.sha256(("src:" + canonical).encode()).hexdigest(),
            source_bytes_sha256=hashlib.sha256(
                ("producer-source:" + canonical).encode()
            ).hexdigest(),
        )

    monkeypatch.setattr(probe.source_digest, "resolve_evidence", fake_evidence)
    monkeypatch.setattr(
        probe,
        "derive_build_admission",
        lambda _context, evidence, **_kwargs: SimpleNamespace(
            receipt_sha256=hashlib.sha256(
                ("admission:" + evidence.genome_sha256).encode()
            ).hexdigest()
        ),
    )
    monkeypatch.setattr(
        probe.buildcache,
        "cache_key",
        lambda genome, *_args, **_kwargs: (
            hashlib.sha256(
                f"{state['rep_index']}:{genome.canonical()}".encode()
            ).hexdigest()
            + "_t0"
        ),
    )

    def fake_build(genome, *_args, **_kwargs):
        canonical = genome.canonical()
        return SimpleNamespace(
            binary=canonical,
            bin_sha256=hashlib.sha256(
                f"binary:{state['rep_index']}:{canonical}".encode()
            ).hexdigest(),
            cached=False,
            trace=False,
        )

    monkeypatch.setattr(probe.buildcache, "build", fake_build)
    monkeypatch.setattr(probe, "_trace_binary_counts", lambda _binary: (0, 0))
    monkeypatch.setattr(probe, "_append_journal", lambda *_args, **_kwargs: None)

    workload_by_ratio = {"5": "write-heavy", "50": "balanced", "95": "read-heavy"}

    def fake_measure(binary, *, threads, workload, **_kwargs):
        match = re.search(r"(?:^|,)BACKOFF_STEP_POLICY=([0-2])(?:,|$)", binary)
        policy = int(match.group(1)) if match is not None else -1
        coordinate = (
            state["rep_index"],
            policy,
            workload_by_ratio[workload["ycsb_rratio"]],
            threads,
        )
        throughputs = () if coordinate == missing_coordinate else (1_000_000.0,)
        return SimpleNamespace(
            throughputs=throughputs,
            abort_rate=0.0,
            latency_ns=None,
            run_cmd=[binary],
        )

    monkeypatch.setattr(probe, "measure_point", fake_measure)
    return policy_root, state


def _produce_policy_performance_artifacts(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    *,
    missing_coordinate: tuple[int, int, str, int] | None = None,
) -> list[Path]:
    policy_root, state = _install_policy_performance_runtime(
        monkeypatch,
        tmp_path,
        missing_coordinate=missing_coordinate,
    )
    paths = []
    for rep_index in range(18):
        state["rep_index"] = rep_index
        runtime = tmp_path / f"runtime-{rep_index}"
        runtime.mkdir()
        monkeypatch.setenv("TMPDIR", str(runtime))
        out = policy_root / f"rep-{rep_index}.json"
        assert probe.main(
            [
                "--repo-head",
                "a" * 40,
                "--repo-clean",
                "1",
                "--cells",
                EXPECTED_PERMUTATIONS[rep_index % 6],
                "--workloads",
                EXPECTED_POLICY_WORKLOADS,
                "--threads",
                EXPECTED_POLICY_THREADS,
                "--rep-index",
                str(rep_index),
                "--step-policy-seed",
                str(EXPECTED_SEEDS_BY_SLOT[rep_index]),
                "--out",
                str(out),
            ]
        ) == 0
        paths.append(out)
    return paths


def _pbs_policy_constants() -> tuple[tuple[str, ...], tuple[int, ...]]:
    pbs_text = PBS.read_text(encoding="utf-8")
    definitions = pbs_text.split('if [[ -z "${PBS_JOBID:-}"', 1)[0]
    program = definitions + """
printf '%s\\n' "${POLICY_PERFORMANCE_PERMUTATIONS_RAW[@]}"
printf '%s\\n' --seeds--
printf '%s\\n' "${POLICY_PERFORMANCE_SEEDS[@]}"
"""
    completed = subprocess.run(
        ["/bin/bash", "-c", program],
        check=True,
        capture_output=True,
        text=True,
    )
    permutations_text, seeds_text = completed.stdout.split("--seeds--\n", 1)
    return (
        tuple(line.replace("+", ",") for line in permutations_text.splitlines()),
        tuple(int(line) for line in seeds_text.splitlines()),
    )


def test_policy_performance_driver_literals_match_independent_contract_literals() -> None:
    assert probe.POLICY_PERFORMANCE_PERMUTATIONS_TEXT == EXPECTED_PERMUTATIONS
    assert probe.POLICY_PERFORMANCE_SEEDS == tuple(EXPECTED_SEEDS_BY_SLOT.values())


def test_policy_performance_pbs_literals_match_independent_contract_literals() -> None:
    pbs_permutations, pbs_seeds = _pbs_policy_constants()
    assert pbs_permutations == EXPECTED_PERMUTATIONS
    assert pbs_seeds == tuple(EXPECTED_SEEDS_BY_SLOT.values())
    pbs_text = PBS.read_text(encoding="utf-8")
    assert "EXTIME=${IZANAGI_T2187_EXTIME:-3}" in pbs_text
    assert "IZANAGI_T2187_REPS_PER_JOB" not in pbs_text
    performance_branch = pbs_text.split(
        'if [[ "$MODE" == performance ]]; then', 1
    )[1].split('OUT="$OUT_DIR/certify-', 1)[0]
    assert '--extime "$EXTIME"' in performance_branch
    assert "--reps-per-job" not in performance_branch
    policy_gate = pbs_text.split(
        "# T2417_POLICY_PERFORMANCE_GATE_BEGIN\n", 1
    )[1].split("# T2417_POLICY_PERFORMANCE_GATE_END", 1)[0]
    assert '"$EXTIME" != 3' in policy_gate
    assert (
        "POLICY_PERFORMANCE_OUT_PREFIX=/work/1/SFC/tanab/"
        "izanagi-job-evidence/dynamic-backoff/perf/t2417-policy/"
    ) in pbs_text
    assert (
        'OUT="$OUT_DIR/policy-perf-rep${REP_INDEX}-${PBS_JOBID//:/_}.json"'
        in pbs_text
    )


def test_policy_performance_driver_and_pbs_literals_are_byte_identical() -> None:
    pbs_permutations, pbs_seeds = _pbs_policy_constants()
    assert probe.POLICY_PERFORMANCE_PERMUTATIONS_TEXT == pbs_permutations
    assert probe.POLICY_PERFORMANCE_SEEDS == pbs_seeds


def test_policy_performance_preregistration_path_bytes_and_reader_are_independent() -> None:
    assert probe.BACKOFF_POLICY_PERFORMANCE_PREREGISTRATION == (
        ROOT / "docs" / "backoff-policy-performance-preregistration.md"
    )
    assert hashlib.sha256(POLICY_PERFORMANCE_PREREGISTRATION.read_bytes()).hexdigest() == (
        EXPECTED_POLICY_PREREG_SHA256
    )
    assert probe._backoff_policy_performance_prereg_sha256() == (
        EXPECTED_POLICY_PREREG_SHA256
    )


def test_policy_performance_contract_accepts_all_18_blocks_and_rep_modulo_six() -> None:
    for rep_index in range(18):
        values = _policy_contract_values(rep_index)
        probe._validate_backoff_policy_performance_contract(*values)
        assert values[0].cells == EXPECTED_PERMUTATIONS[rep_index % 6]


def test_policy_performance_selector_uses_parsed_exact_three_cell_set() -> None:
    for cells_text in EXPECTED_PERMUTATIONS:
        assert probe._is_backoff_policy_performance_cell_set(
            probe.parse_cells(cells_text)
        )
    raw_drift = EXPECTED_PERMUTATIONS[0].replace(",", ", ", 1)
    parsed_drift = probe.parse_cells(raw_drift)
    assert probe._is_backoff_policy_performance_cell_set(parsed_drift)
    with pytest.raises(ValueError, match="policy-performance-contract-violation"):
        probe._validate_backoff_policy_performance_contract(
            *_policy_contract_values(0, cells=raw_drift)
        )


@pytest.mark.parametrize(
    ("rep_index", "changes"),
    (
        (0, {"cells": EXPECTED_PERMUTATIONS[1]}),
        (1, {"cells": EXPECTED_PERMUTATIONS[0]}),
        (18, {"cells": EXPECTED_PERMUTATIONS[0]}),
        (0, {"workloads": "balanced,write-heavy,read-heavy"}),
        (0, {"threads": "6,12,18,24,30,36,42"}),
        (0, {"extime": 4}),
        (0, {"reps_per_job": 2}),
        (0, {"stage": 2}),
        (0, {"step_policy_seed": None}),
        (0, {"step_policy_seed": EXPECTED_SEEDS_BY_SLOT[0] + 1}),
        (0, {"mode": "certify"}),
        (0, {"backoff_trace": True}),
    ),
    ids=(
        "nonassigned-permutation",
        "order-rep-mismatch",
        "rep-18",
        "workloads-axis",
        "threads-axis",
        "extime",
        "reps-per-job",
        "stage",
        "seed-missing",
        "seed-mismatch",
        "mode",
        "trace-enabled-helper",
    ),
)
def test_policy_performance_contract_rejects_each_exact_condition_for_stable_reason(
    rep_index: int, changes: dict
) -> None:
    with pytest.raises(ValueError, match="policy-performance-contract-violation"):
        probe._validate_backoff_policy_performance_contract(
            *_policy_contract_values(rep_index, **changes)
        )


def test_policy_performance_exact_three_cells_still_fail_legacy_grid_contract() -> None:
    with pytest.raises(ValueError, match="exactly none:0:100:1000:10"):
        probe._validate_grid_contract(probe.parse_cells(EXPECTED_PERMUTATIONS[0]))


def test_public_dispatch_keeps_policy_grid_and_trace_validators_disjoint(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    class DispatchObserved(Exception):
        pass

    cases = (
        (
            "policy",
            "_validate_backoff_policy_performance_contract",
            [
                "--cells",
                EXPECTED_PERMUTATIONS[4],
                "--workloads",
                EXPECTED_POLICY_WORKLOADS,
                "--threads",
                EXPECTED_POLICY_THREADS,
                "--rep-index",
                "4",
                "--step-policy-seed",
                str(EXPECTED_SEEDS_BY_SLOT[4]),
                "--out",
                str(probe.DYNAMIC_POLICY_PERFORMANCE_PREFIX / "dispatch.json"),
            ],
        ),
        (
            "grid",
            "_validate_grid_contract",
            ["--cells", VALID_CELLS, "--out", str(tmp_path / "grid.json")],
        ),
        (
            "trace",
            "_validate_backoff_trace_contract",
            [
                "--backoff-trace",
                "--cells",
                COUNTERFACTUAL_TRACE_CELLS,
                "--workloads",
                EXPECTED_POLICY_WORKLOADS,
                "--threads",
                "24,48",
                "--step-policy-seed",
                "5744733223455690259",
                "--out",
                str(probe.DYNAMIC_OUT_PREFIX / "trace" / "dispatch.json"),
            ],
        ),
    )
    observed = []
    for expected, validator_name, argv in cases:
        with monkeypatch.context() as scoped:
            real_validator = getattr(probe, validator_name)

            def observe(*args, _name=expected, _real=real_validator):
                _real(*args)
                observed.append(_name)
                raise DispatchObserved

            scoped.setattr(probe, validator_name, observe)
            with pytest.raises(DispatchObserved):
                probe.main(argv)
    assert observed == ["policy", "grid", "trace"]


def test_policy_performance_output_requires_resolved_true_child() -> None:
    prefix = probe.DYNAMIC_POLICY_PERFORMANCE_PREFIX
    probe._validate_backoff_policy_performance_output_path(
        prefix / "attempt" / ".." / "other" / "result.json"
    )
    for rejected in (prefix, prefix.parent / "other" / "result.json"):
        with pytest.raises(
            ValueError, match="policy-performance-output-prefix-violation"
        ):
            probe._validate_backoff_policy_performance_output_path(rejected)


def test_public_policy_performance_rejects_output_outside_dedicated_prefix(
    tmp_path: Path,
) -> None:
    args, _cells, _workloads, _threads = _policy_contract_values(0)
    argv = [
        "--cells",
        args.cells,
        "--workloads",
        args.workloads,
        "--threads",
        args.threads,
        "--rep-index",
        str(args.rep_index),
        "--step-policy-seed",
        str(args.step_policy_seed),
        "--out",
        str(tmp_path / "outside.json"),
    ]
    with pytest.raises(
        ValueError, match="policy-performance-output-prefix-violation"
    ):
        probe.main(argv)


def test_public_policy_performance_missing_seed_uses_contract_reason() -> None:
    args, _cells, _workloads, _threads = _policy_contract_values(0)
    argv = [
        "--cells",
        args.cells,
        "--workloads",
        args.workloads,
        "--threads",
        args.threads,
        "--rep-index",
        "0",
        "--out",
        str(probe.DYNAMIC_POLICY_PERFORMANCE_PREFIX / "missing-seed.json"),
    ]
    with pytest.raises(ValueError, match="step-policy-seed is required"):
        probe.main(argv)


def test_public_policy_performance_wrong_seed_uses_contract_reason() -> None:
    args, _cells, _workloads, _threads = _policy_contract_values(0)
    argv = [
        "--cells",
        args.cells,
        "--workloads",
        args.workloads,
        "--threads",
        args.threads,
        "--rep-index",
        "0",
        "--step-policy-seed",
        str(EXPECTED_SEEDS_BY_SLOT[0] + 1),
        "--out",
        str(probe.DYNAMIC_POLICY_PERFORMANCE_PREFIX / "wrong-seed.json"),
    ]
    with pytest.raises(ValueError, match="policy-performance-contract-violation"):
        probe.main(argv)


def test_public_policy_producer_output_is_final_and_analysis_compatible(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    paths = _produce_policy_performance_artifacts(monkeypatch, tmp_path)
    document = json.loads(paths[0].read_text(encoding="utf-8"))
    assert document["backoff_policy_performance_prereg_sha256"] == (
        EXPECTED_POLICY_PREREG_SHA256
    )
    assert document["performance_contract"] == "backoff-policy-arm-perf/v1"
    assert document["headline_eligible"] is False
    assert document["correctness_status"] == "uncertified"
    protected = {
        "backoff_policy_performance_prereg_sha256",
        "performance_contract",
        "headline_eligible",
        "correctness_status",
    }
    for row in document["cells"]:
        assert row["build_trace_enabled"] is False
        assert row["build_cache_key"].endswith("_t0")
        assert re.fullmatch(
            r"[0-9a-f]{64}", row["build_admission_receipt_sha256"]
        )
        assert protected.isdisjoint(row)
    documents = [json.loads(path.read_text(encoding="utf-8")) for path in paths]
    for current in documents:
        assert len(
            {
                next(
                    row
                    for row in current["cells"]
                    if row["step_policy"] == policy
                )["source_evidence"]["source_bytes_sha256"]
                for policy in range(3)
            }
        ) == 3
    for policy in (0, 1):
        assert len(
            {
                next(
                    row
                    for row in current["cells"]
                    if row["step_policy"] == policy
                )["source_evidence"]["source_bytes_sha256"]
                for current in documents
            }
        ) == 1
        assert len(
            {
                next(
                    row
                    for row in current["cells"]
                    if row["step_policy"] == policy
                )["genome"]
                for current in documents
            }
        ) == 1
    for field in ("binary_sha256", "build_cache_key"):
        for policy in range(3):
            assert len(
                {
                    next(
                        row
                        for row in current["cells"]
                        if row["step_policy"] == policy
                    )[field]
                    for current in documents
                }
            ) == 18
    for field in ("source_bytes_sha256", "genome"):
        assert len(
            {
                (
                    next(
                        row
                        for row in current["cells"]
                        if row["step_policy"] == 2
                    )["source_evidence"][field]
                    if field == "source_bytes_sha256"
                    else next(
                        row
                        for row in current["cells"]
                        if row["step_policy"] == 2
                    )[field]
                )
                for current in documents
            }
        ) == 18
    result = policy_analysis.analyze_policy_performance(
        paths,
        POLICY_PERFORMANCE_PREREGISTRATION,
        POLICY_PERFORMANCE_PREREGISTRATION_ERRATUM_1,
    )
    assert result["analysis_status"] == "complete"
    assert result["blocks"]["present_rep_indices"] == list(range(18))


def test_public_policy_producer_reasoned_missing_is_local_in_analysis(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    missing = (4, 0, "balanced", 12)
    paths = _produce_policy_performance_artifacts(
        monkeypatch,
        tmp_path,
        missing_coordinate=missing,
    )
    missing_rows = []
    for path in paths:
        document = json.loads(path.read_text(encoding="utf-8"))
        missing_rows.extend(
            row for row in document["cells"] if "missing_reason" in row
        )
    assert len(missing_rows) == 1
    assert missing_rows[0]["median_tps"] is None
    assert missing_rows[0]["throughputs"] == []
    assert missing_rows[0]["missing_reason"] == "no-throughput-samples"
    assert probe._performance_measurement_summary([0.0])[2] == (
        "nonpositive-throughput"
    )
    assert probe._performance_measurement_summary([float("nan")]) == (
        [],
        None,
        "nonfinite-throughput",
    )

    result = policy_analysis.analyze_policy_performance(
        paths,
        POLICY_PERFORMANCE_PREREGISTRATION,
        POLICY_PERFORMANCE_PREREGISTRATION_ERRATUM_1,
    )

    def point(contrast: str, workload: str, threads: int) -> dict:
        return next(
            item
            for item in result["contrasts"][contrast]["points"]
            if item["workload"] == workload and item["threads"] == threads
        )

    for contrast in ("p0/p1", "p0/p2"):
        affected = point(contrast, "balanced", 12)
        assert affected["reason"] == "n-insufficient"
        assert affected["missing_rep_indices"] == [4]
    assert point("p2/p1", "balanced", 12)["decision"] == "equivalent"
    assert all(
        item["reason"] is None
        for contrast in result["contrasts"].values()
        for item in contrast["points"]
        if not (
            contrast["left"] == "p0"
            and item["workload"] == "balanced"
            and item["threads"] == 12
        )
    )


def test_public_policy_producer_shared_source_across_arms_is_artifact_invalid(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    paths = _produce_policy_performance_artifacts(monkeypatch, tmp_path)
    document = json.loads(paths[0].read_text(encoding="utf-8"))
    shared_source = hashlib.sha256(b"inert-policy-source").hexdigest()
    for row in document["cells"]:
        row["source_evidence"]["source_bytes_sha256"] = shared_source
    paths[0].write_text(json.dumps(document) + "\n", encoding="utf-8")

    with pytest.raises(ValueError, match="artifact-invalid"):
        policy_analysis.analyze_policy_performance(
            paths,
            POLICY_PERFORMANCE_PREREGISTRATION,
            POLICY_PERFORMANCE_PREREGISTRATION_ERRATUM_1,
        )


def test_public_policy_producer_p0_source_drift_between_blocks_is_artifact_invalid(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    paths = _produce_policy_performance_artifacts(monkeypatch, tmp_path)
    document = json.loads(paths[1].read_text(encoding="utf-8"))
    changed_source = hashlib.sha256(b"drifted-p0-source").hexdigest()
    for row in document["cells"]:
        if row["step_policy"] == 0:
            row["source_evidence"]["source_bytes_sha256"] = changed_source
    paths[1].write_text(json.dumps(document) + "\n", encoding="utf-8")

    with pytest.raises(ValueError, match="artifact-invalid"):
        policy_analysis.analyze_policy_performance(
            paths,
            POLICY_PERFORMANCE_PREREGISTRATION,
            POLICY_PERFORMANCE_PREREGISTRATION_ERRATUM_1,
        )


def test_public_policy_producer_p0_binary_drift_between_blocks_is_accepted(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    paths = _produce_policy_performance_artifacts(monkeypatch, tmp_path)
    p0_binaries = {
        next(
            row
            for row in json.loads(path.read_text(encoding="utf-8"))["cells"]
            if row["step_policy"] == 0
        )["binary_sha256"]
        for path in paths
    }
    assert len(p0_binaries) == 18

    result = policy_analysis.analyze_policy_performance(
        paths,
        POLICY_PERFORMANCE_PREREGISTRATION,
        POLICY_PERFORMANCE_PREREGISTRATION_ERRATUM_1,
    )
    assert result["analysis_status"] == "complete"


def test_public_generic_policy_grid_is_accepted_but_uncertified(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    _policy_root, state = _install_policy_performance_runtime(monkeypatch, tmp_path)
    state["rep_index"] = 0
    runtime = tmp_path / "generic-runtime"
    runtime.mkdir()
    monkeypatch.setenv("TMPDIR", str(runtime))
    cells = (
        "none:0:100:1000:10,"
        "stock:1:100:1000:10,"
        "cw-as-dyn-p0:1:1:1000:2560:10000:10240:1:1:4:1:0"
    )
    out = probe.DYNAMIC_PERFORMANCE_PREFIX / "generic-policy.json"
    assert probe.main(
        [
            "--repo-head",
            "a" * 40,
            "--repo-clean",
            "1",
            "--cells",
            cells,
            "--workloads",
            "balanced",
            "--threads",
            "48",
            "--out",
            str(out),
        ]
    ) == 0
    document = json.loads(out.read_text(encoding="utf-8"))
    assert document["headline_eligible"] is False
    assert document["correctness_status"] == "uncertified"
    assert "performance_contract" not in document
    assert "backoff_policy_performance_prereg_sha256" not in document


def test_policy_performance_fields_are_top_level_only_and_require_every_condition(
    tmp_path: Path,
) -> None:
    exact = probe._artifact_contract_metadata(**_policy_metadata_values(7))
    assert exact == {
        "schema_version": probe.SCHEMA_VERSION,
        "not_certified": (
            "trace-disabled performance runs only; no serializability check was run"
        ),
        "backoff_policy_performance_prereg_sha256": EXPECTED_POLICY_PREREG_SHA256,
        "performance_contract": "backoff-policy-arm-perf/v1",
        "headline_eligible": False,
        "correctness_status": "uncertified",
    }
    assert "counterfactual_preregistration" not in exact
    protected = {
        "backoff_policy_performance_prereg_sha256",
        "performance_contract",
        "headline_eligible",
        "correctness_status",
    }
    drifts = (
        {"cells": EXPECTED_PERMUTATIONS[0]},
        {"workloads": "write-heavy,balanced"},
        {"threads": "6,12,18,24,30,36,42"},
        {"extime": 4},
        {"reps_per_job": 2},
        {"stage": 2},
        {"step_policy_seed": EXPECTED_SEEDS_BY_SLOT[7] + 1},
    )
    for drift in drifts:
        metadata = probe._artifact_contract_metadata(
            **_policy_metadata_values(7, **drift)
        )
        assert protected.isdisjoint(metadata)

    row = probe._counterfactual_row_metadata(
        preregistration_sha256=None,
        cell=probe.parse_cells(EXPECTED_PERMUTATIONS[0])[2],
        step_policy_seed=EXPECTED_SEEDS_BY_SLOT[0],
    )
    assert protected.isdisjoint(row)
    journal_target = tmp_path / "policy.json"
    probe._append_journal(journal_target, row)
    journal_row = json.loads(
        Path(str(journal_target) + ".journal.jsonl").read_text(encoding="utf-8")
    )
    assert protected.isdisjoint(journal_row)
    driver_text = DRIVER.read_text(encoding="utf-8")
    row_and_journal_block = driver_text.split("                        row = {", 1)[
        1
    ].split("                        shown = (", 1)[0]
    assert all(field not in row_and_journal_block for field in protected)


def test_policy_performance_artifact_is_rejected_by_existing_certification_identity(
    tmp_path: Path,
) -> None:
    regular = tmp_path / "regular.json"
    regular.write_text(
        json.dumps(
            {
                "schema_version": probe.SCHEMA_VERSION,
                "kind": "performance-only-probe",
                "not_certified": probe.NOT_CERTIFIED,
            }
        )
        + "\n",
        encoding="utf-8",
    )
    assert probe._performance_artifact_identity(
        regular, hashlib.sha256(regular.read_bytes()).hexdigest()
    )["path"] == str(regular.resolve(strict=True))

    policy = tmp_path / "policy.json"
    policy.write_text(
        json.dumps(
            {
                "schema_version": probe.SCHEMA_VERSION,
                "kind": "performance-only-probe",
                "not_certified": probe.NOT_CERTIFIED,
                "performance_contract": "backoff-policy-arm-perf/v1",
            }
        )
        + "\n",
        encoding="utf-8",
    )
    with pytest.raises(probe.CertificationReject) as caught:
        probe._performance_artifact_identity(
            policy, hashlib.sha256(policy.read_bytes()).hexdigest()
        )
    assert caught.value.reason == "performance-artifact-contract-rejected"

    markerless_policy = tmp_path / "markerless-policy.json"
    markerless_policy.write_text(
        json.dumps(
            {
                "schema_version": probe.SCHEMA_VERSION,
                "kind": "performance-only-probe",
                "not_certified": probe.NOT_CERTIFIED,
                "cells": [
                    probe._cell_identity(
                        probe.parse_cells(EXPECTED_PERMUTATIONS[0])[0]
                    )
                ],
            }
        )
        + "\n",
        encoding="utf-8",
    )
    with pytest.raises(probe.CertificationReject) as caught:
        probe._performance_artifact_identity(
            markerless_policy,
            hashlib.sha256(markerless_policy.read_bytes()).hexdigest(),
        )
    assert caught.value.reason == "performance-artifact-contract-rejected"


def test_policy_performance_artifact_is_rejected_by_both_group_public_paths(
    tmp_path: Path,
) -> None:
    policy = tmp_path / "policy.json"
    policy.write_text(
        json.dumps(
            {
                "schema_version": probe.SCHEMA_VERSION,
                "kind": "performance-only-probe",
                "not_certified": probe.NOT_CERTIFIED,
                "performance_contract": "backoff-policy-arm-perf/v1",
            }
        )
        + "\n",
        encoding="utf-8",
    )
    policy_sha256 = hashlib.sha256(policy.read_bytes()).hexdigest()
    identity = {
        "repository_commit": "a" * 40,
        "module_sha256": {"verifier.py": "b" * 64},
    }
    identity_file_sha256 = "c" * 64
    pairs = [
        (workload, slot)
        for workload in probe.CERT_WORKLOADS
        for slot in probe.CERT_SLOTS
    ]
    result_files = [tmp_path / f"result-{index}.json" for index in range(24)]
    with pytest.raises(probe.CertificationReject) as caught:
        probe._group_receipt_payload(
            result_files,
            policy,
            policy_sha256,
            "attempt-test",
            identity,
            identity_file_sha256,
        )
    assert caught.value.reason == "performance-artifact-contract-rejected"

    cell = probe.CERT_TUNED_CELL
    axes = probe.CertificationAxes(cell, 48, None)
    patch_identity = probe._patch_stack_identity()
    execution_identity = {
        "driver_sha256": "d" * 64,
        "pbs_sha256": "e" * 64,
        "driver_argv": ["t2187_adaptive_const_probe.py", "--mode", "certify"],
        "repo_status_clean": True,
    }
    source_evidence = {
        "ccbench_commit": probe.CURRENT_PIN,
        "genome_sha256": "f" * 64,
        "src_token": "published-source",
        "source_bytes_sha256": "1" * 64,
    }
    genome = probe.genome_for(cell).canonical()
    prereg_sha256 = probe._certification_prereg_sha256(cell)
    results = []
    for path, (workload, slot) in zip(result_files, pairs):
        path.write_text("{}\n", encoding="utf-8")
        results.append(
            {
                "path": str(path.resolve(strict=True)),
                "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
                **probe._cell_identity(cell),
                "cell_order": [cell.label],
                "claim": probe._certification_claim(axes),
                "backoff_trace": False,
                "records": probe.CERT_RECORDS,
                "threads": 48,
                "extime_s": probe.CERT_EXTIME,
                "workload": workload,
                "workload_flags": {
                    **probe.WORKLOADS[workload],
                    "ycsb_tuple_num": str(probe.CERT_RECORDS),
                    "thread_num": "48",
                    "extime": str(probe.CERT_EXTIME),
                },
                "independent_run_slot": slot,
                "repo_head": "2" * 40,
                "prereg_sha256": prereg_sha256,
                "ccbench_commit": probe.PIN_FULL,
                "ccbench_head": probe.PIN_FULL,
                **execution_identity,
                "genome": genome,
                "source_evidence": source_evidence,
                "proof_surface": {
                    "protocol": probe.CERT_PROTOCOL,
                    "source_snapshot_identity": source_evidence,
                },
                **patch_identity,
            }
        )
    group = tmp_path / "group.json"
    group.write_text(
        json.dumps(
            {
                "schema_version": probe.GROUP_RECEIPT_SCHEMA_VERSION,
                "complete": True,
                "certified_requests": 24,
                "attempt_id": "attempt-test",
                "verifier_identity": identity,
                "expected_verifier_identity_file_sha256": identity_file_sha256,
                "performance_artifact": {
                    "path": str(policy.resolve(strict=True)),
                    "sha256": policy_sha256,
                },
                **probe._cell_identity(cell),
                "cell_order": [cell.label],
                "claim": probe._certification_claim(axes),
                "backoff_trace": False,
                "records": probe.CERT_RECORDS,
                "threads": 48,
                "extime_s": probe.CERT_EXTIME,
                "hostname": "published-host",
                "prereg_sha256": prereg_sha256,
                "repo_head": "2" * 40,
                **patch_identity,
                "ccbench_commit": probe.PIN_FULL,
                "ccbench_head": probe.PIN_FULL,
                "genome": genome,
                "source_evidence": source_evidence,
                "proof_surface": {
                    "protocol": probe.CERT_PROTOCOL,
                    "source_snapshot_identity": source_evidence,
                },
                **execution_identity,
                "results": results,
            }
        )
        + "\n",
        encoding="utf-8",
    )
    with pytest.raises(probe.CertificationReject) as caught:
        probe._validate_published_group(
            group,
            result_files,
            policy,
            policy_sha256,
            "attempt-test",
            identity,
            identity_file_sha256,
        )
    assert caught.value.reason == "performance-artifact-contract-rejected"


def _run_extracted_pbs_policy_gate(
    tmp_path: Path, **changes: str
) -> subprocess.CompletedProcess[str]:
    pbs_text = PBS.read_text(encoding="utf-8")
    definitions = pbs_text.split('if [[ -z "${PBS_JOBID:-}"', 1)[0]
    gate = pbs_text.split("# T2417_POLICY_PERFORMANCE_GATE_BEGIN\n", 1)[1].split(
        "# T2417_POLICY_PERFORMANCE_GATE_END", 1
    )[0]
    gate_script = tmp_path / "t2417-policy-gate.sh"
    gate_script.write_text(definitions + gate, encoding="utf-8")
    environment = {
        **os.environ,
        "MODE": "performance",
        "BACKOFF_TRACE": "0",
        "CELLS_RAW": EXPECTED_PERMUTATIONS[0].replace(",", "+"),
        "WORKLOADS_RAW": EXPECTED_POLICY_WORKLOADS.replace(",", "+"),
        "THREADS_RAW": EXPECTED_POLICY_THREADS.replace(",", "+"),
        "EXTIME": "3",
        "REP_INDEX": "0",
        "STAGE": "1",
        "STEP_POLICY_SEED": str(EXPECTED_SEEDS_BY_SLOT[0]),
        "OUT_DIR_RAW": (
            "/work/1/SFC/tanab/izanagi-job-evidence/dynamic-backoff/"
            "perf/t2417-policy/test-attempt"
        ),
    }
    environment.update(changes)
    return subprocess.run(
        ["/bin/bash", str(gate_script)],
        check=False,
        capture_output=True,
        text=True,
        env=environment,
    )


def test_extracted_pbs_policy_gate_accepts_all_18_blocks(tmp_path: Path) -> None:
    for rep_index in range(18):
        completed = _run_extracted_pbs_policy_gate(
            tmp_path,
            CELLS_RAW=EXPECTED_PERMUTATIONS[rep_index % 6].replace(",", "+"),
            REP_INDEX=str(rep_index),
            STEP_POLICY_SEED=str(EXPECTED_SEEDS_BY_SLOT[rep_index]),
        )
        assert completed.returncode == 0, (rep_index, completed.stderr)


@pytest.mark.parametrize(
    "changes",
    (
        {"CELLS_RAW": EXPECTED_PERMUTATIONS[1].replace(",", "+")},
        {"REP_INDEX": "18"},
        {"WORKLOADS_RAW": "balanced+write-heavy+read-heavy"},
        {"THREADS_RAW": "6+12+18+24+30+36+42"},
        {"EXTIME": "4"},
        {"STAGE": "2"},
        {"STEP_POLICY_SEED": ""},
        {"STEP_POLICY_SEED": str(EXPECTED_SEEDS_BY_SLOT[0] + 1)},
        {"OUT_DIR_RAW": "/work/1/SFC/tanab/izanagi-job-evidence/dynamic-backoff/trace"},
    ),
    ids=(
        "nonassigned-permutation",
        "rep-18",
        "workloads-axis",
        "threads-axis",
        "extime",
        "stage",
        "seed-missing",
        "seed-mismatch",
        "output-prefix",
    ),
)
def test_extracted_pbs_policy_gate_rejects_each_drift_before_build(
    tmp_path: Path, changes: dict[str, str]
) -> None:
    completed = _run_extracted_pbs_policy_gate(tmp_path, **changes)
    assert completed.returncode == 2
    assert "policy-performance-" in completed.stderr
    pbs_text = PBS.read_text(encoding="utf-8")
    assert pbs_text.index("# T2417_POLICY_PERFORMANCE_GATE_END") < pbs_text.index(
        'verify_pinned_clean "$GFLAGS_SOURCE_PATH"'
    )


def test_pbs_rejects_submission_head_drift_before_dependency_build(
    tmp_path: Path,
) -> None:
    pbs_text = PBS.read_text(encoding="utf-8")
    gate = pbs_text.split("# T2417_EXPECTED_REPO_HEAD_GATE_BEGIN\n", 1)[1].split(
        "# T2417_EXPECTED_REPO_HEAD_GATE_END", 1
    )[0]
    gate_script = tmp_path / "expected-head-gate.sh"
    gate_script.write_text(gate, encoding="utf-8")
    common = {
        **os.environ,
        "IS_POLICY_PERFORMANCE": "1",
        "REPO_HEAD": "a" * 40,
    }
    accepted = subprocess.run(
        ["/bin/bash", str(gate_script)],
        check=False,
        capture_output=True,
        text=True,
        env={**common, "EXPECTED_REPO_HEAD": "a" * 40},
    )
    assert accepted.returncode == 0, accepted.stderr
    rejected = subprocess.run(
        ["/bin/bash", str(gate_script)],
        check=False,
        capture_output=True,
        text=True,
        env={**common, "EXPECTED_REPO_HEAD": "b" * 40},
    )
    assert rejected.returncode == 2
    assert rejected.stdout == ""
    assert "policy-performance-repo-head-mismatch" in rejected.stderr
    assert pbs_text.index("# T2417_EXPECTED_REPO_HEAD_GATE_END") < pbs_text.index(
        'verify_pinned_clean "$GFLAGS_SOURCE_PATH"'
    )


def test_submit_t2417_uses_one_checkout_and_exact_18_block_ledger(
    tmp_path: Path,
) -> None:
    subprocess.run(
        ["/bin/bash", "-n", str(SUBMIT_T2417)],
        check=True,
        capture_output=True,
        text=True,
    )
    assert SUBMIT_T2417.stat().st_mode & 0o111
    submit_text = SUBMIT_T2417.read_text(encoding="utf-8")
    assert 'git -C "$REPO_ROOT" symbolic-ref -q HEAD' in submit_text
    assert 'git -C "$REPO_ROOT" status --porcelain --untracked-files=all' in (
        submit_text
    )
    assert "qstat" not in submit_text
    assert "sleep" not in submit_text
    fake_bin = tmp_path / "bin"
    fake_bin.mkdir()
    qsub_log = tmp_path / "qsub.log"
    ledger_root = tmp_path / "ledgers"
    fake_git = fake_bin / "git"
    fake_git.write_text(
        "#!/bin/bash\n"
        "case \"$*\" in\n"
        "  *'rev-parse --show-toplevel'*) printf '%s\\n' \"$FAKE_REPO_ROOT\" ;;\n"
        "  *'rev-parse HEAD'*) printf '%040d\\n' 0 ;;\n"
        "  *'symbolic-ref -q HEAD'*) exit 1 ;;\n"
        "  *'status --porcelain --untracked-files=all'*) exit 0 ;;\n"
        "  *) exit 9 ;;\n"
        "esac\n",
        encoding="utf-8",
    )
    fake_qsub = fake_bin / "qsub"
    fake_qsub.write_text(
        "#!/bin/bash\n"
        "printf '%s\\n' \"$*\" >> \"$QSUB_LOG\"\n"
        "printf '%s\\n' 'Request 982971.nqsv submitted to queue: gen_S.'\n",
        encoding="utf-8",
    )
    fake_git.chmod(0o755)
    fake_qsub.chmod(0o755)
    completed = subprocess.run(
        ["/bin/bash", str(SUBMIT_T2417), "test-attempt"],
        check=False,
        capture_output=True,
        text=True,
        env={
            **os.environ,
            "PATH": f"{fake_bin}:{os.environ['PATH']}",
            "FAKE_REPO_ROOT": str(ROOT.resolve()),
            "QSUB_LOG": str(qsub_log),
            "IZANAGI_T2417_LEDGER_ROOT": str(ledger_root),
        },
    )
    assert completed.returncode == 0, completed.stderr
    ledger = [json.loads(line) for line in completed.stdout.splitlines()]
    assert len(ledger) == 18
    assert [entry["job_id"] for entry in ledger] == ["982971.nqsv"] * 18
    assert [entry["rep_index"] for entry in ledger] == list(range(18))
    assert [entry["order_index"] for entry in ledger] == [
        rep_index % 6 for rep_index in range(18)
    ]
    assert [entry["order"].replace("+", ",") for entry in ledger] == [
        EXPECTED_PERMUTATIONS[rep_index % 6] for rep_index in range(18)
    ]
    assert [int(entry["seed"]) for entry in ledger] == list(
        EXPECTED_SEEDS_BY_SLOT.values()
    )
    persisted = [
        json.loads(line)
        for line in (ledger_root / "test-attempt.submission-ledger.jsonl")
        .read_text(encoding="utf-8")
        .splitlines()
    ]
    assert persisted[0]["event"] == "submission-started"
    assert persisted[0]["attempt_id"] == "test-attempt"
    assert persisted[0]["expected_repo_head"] == "0" * 40
    assert persisted[0]["pbs_sha256"] == hashlib.sha256(PBS.read_bytes()).hexdigest()
    assert re.fullmatch(
        r"[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}Z",
        persisted[0]["submitted_utc"],
    )
    assert persisted[1:19] == ledger
    assert persisted[-1]["event"] == "submission-complete"
    assert persisted[-1]["submitted"] == 18

    qsub_lines = qsub_log.read_text(encoding="utf-8").splitlines()
    assert len(qsub_lines) == 18
    environments = []
    scheduler_dir = (ledger_root / "test-attempt" / "scheduler").resolve()
    for rep_index, line in enumerate(qsub_lines):
        arguments = line.split(" ")
        assert len(arguments) == 7
        stdout_option, stdout_text, stderr_option, stderr_text = arguments[:4]
        option, environment_text, pbs_body = arguments[4:]
        assert stdout_option == "-o"
        assert stderr_option == "-e"
        scheduler_stdout = Path(stdout_text)
        scheduler_stderr = Path(stderr_text)
        assert scheduler_stdout == scheduler_dir / f"rep{rep_index}.stdout"
        assert scheduler_stderr == scheduler_dir / f"rep{rep_index}.stderr"
        assert scheduler_stdout.is_absolute()
        assert scheduler_stderr.is_absolute()
        assert not scheduler_stdout.resolve().is_relative_to(ROOT.resolve())
        assert not scheduler_stderr.resolve().is_relative_to(ROOT.resolve())
        assert option == "-v"
        assert Path(pbs_body) == PBS
        environments.append(
            dict(item.split("=", 1) for item in environment_text.split(","))
        )
    assert set(environments[0]) == {
        "IZANAGI_T2187_MODE",
        "IZANAGI_T2187_BACKOFF_TRACE",
        "IZANAGI_T2187_EXPECTED_REPO_HEAD",
        "IZANAGI_T2187_OUT_DIR",
        "IZANAGI_T2187_CELLS",
        "IZANAGI_T2187_WORKLOADS",
        "IZANAGI_T2187_THREADS",
        "IZANAGI_T2187_REP_INDEX",
        "IZANAGI_T2187_STEP_POLICY_SEED",
        "IZANAGI_T2187_STAGE",
    }
    changing = {
        key
        for key in environments[0]
        if len({environment[key] for environment in environments}) > 1
    }
    assert changing == {
        "IZANAGI_T2187_CELLS",
        "IZANAGI_T2187_REP_INDEX",
        "IZANAGI_T2187_STEP_POLICY_SEED",
    }
    assert {
        environment["IZANAGI_T2187_EXPECTED_REPO_HEAD"]
        for environment in environments
    } == {"0" * 40}
    assert [
        int(environment["IZANAGI_T2187_REP_INDEX"])
        for environment in environments
    ] == list(range(18))
    assert [
        environment["IZANAGI_T2187_CELLS"].replace("+", ",")
        for environment in environments
    ] == [EXPECTED_PERMUTATIONS[rep_index % 6] for rep_index in range(18)]
    assert [
        int(environment["IZANAGI_T2187_STEP_POLICY_SEED"])
        for environment in environments
    ] == list(EXPECTED_SEEDS_BY_SLOT.values())
    assert 'if [[ "$submitted" -ne 18 ]]' in submit_text

    repo_internal = subprocess.run(
        ["/bin/bash", str(SUBMIT_T2417), "repo-internal-scheduler"],
        check=False,
        capture_output=True,
        text=True,
        env={
            **os.environ,
            "PATH": f"{fake_bin}:{os.environ['PATH']}",
            "FAKE_REPO_ROOT": str(ROOT.resolve()),
            "QSUB_LOG": str(qsub_log),
            "IZANAGI_T2417_LEDGER_ROOT": str(ROOT / "scheduler-must-not-land-here"),
        },
    )
    assert repo_internal.returncode == 2
    assert repo_internal.stdout == ""
    assert "scheduler output directory must be outside" in repo_internal.stderr
    assert len(qsub_log.read_text(encoding="utf-8").splitlines()) == 18


def test_submit_t2417_records_partial_jobs_prints_qdel_and_rejects_attempt_reuse(
    tmp_path: Path,
) -> None:
    fake_bin = tmp_path / "bin"
    fake_bin.mkdir()
    qsub_log = tmp_path / "qsub.log"
    ledger_root = tmp_path / "ledgers"
    fake_git = fake_bin / "git"
    fake_git.write_text(
        "#!/bin/bash\n"
        "case \"$*\" in\n"
        "  *'rev-parse --show-toplevel'*) printf '%s\\n' \"$FAKE_REPO_ROOT\" ;;\n"
        "  *'rev-parse HEAD'*) printf '%040d\\n' 0 ;;\n"
        "  *'symbolic-ref -q HEAD'*) exit 1 ;;\n"
        "  *'status --porcelain --untracked-files=all'*) exit 0 ;;\n"
        "  *) exit 9 ;;\n"
        "esac\n",
        encoding="utf-8",
    )
    fake_qsub = fake_bin / "qsub"
    fake_qsub.write_text(
        "#!/bin/bash\n"
        "count=0\n"
        "if [[ -f \"$QSUB_LOG\" ]]; then count=$(wc -l < \"$QSUB_LOG\"); fi\n"
        "printf '%s\\n' \"$*\" >> \"$QSUB_LOG\"\n"
        "if [[ $count -ge 3 ]]; then exit 1; fi\n"
        "printf '%d.test\\n' \"$((100 + count))\"\n",
        encoding="utf-8",
    )
    fake_git.chmod(0o755)
    fake_qsub.chmod(0o755)
    environment = {
        **os.environ,
        "PATH": f"{fake_bin}:{os.environ['PATH']}",
        "FAKE_REPO_ROOT": str(ROOT.resolve()),
        "QSUB_LOG": str(qsub_log),
        "IZANAGI_T2417_LEDGER_ROOT": str(ledger_root),
    }
    completed = subprocess.run(
        ["/bin/bash", str(SUBMIT_T2417), "partial-attempt"],
        check=False,
        capture_output=True,
        text=True,
        env=environment,
    )
    assert completed.returncode == 1
    assert "submitted job IDs: 100.test 101.test 102.test\n" in completed.stdout
    assert "qdel -- 100.test 101.test 102.test\n" in completed.stdout
    persisted = [
        json.loads(line)
        for line in (ledger_root / "partial-attempt.submission-ledger.jsonl")
        .read_text(encoding="utf-8")
        .splitlines()
    ]
    assert [entry["job_id"] for entry in persisted if "job_id" in entry] == [
        "100.test",
        "101.test",
        "102.test",
    ]
    assert persisted[-1]["event"] == "submission-failed"
    assert persisted[-1]["rep_index"] == 3
    assert persisted[-1]["reason"] == "qsub-failed"
    assert len(qsub_log.read_text(encoding="utf-8").splitlines()) == 4

    reused = subprocess.run(
        ["/bin/bash", str(SUBMIT_T2417), "partial-attempt"],
        check=False,
        capture_output=True,
        text=True,
        env=environment,
    )
    assert reused.returncode == 2
    assert reused.stdout == ""
    assert "attempt id already has a submission ledger" in reused.stderr
    assert len(qsub_log.read_text(encoding="utf-8").splitlines()) == 4

    fake_qsub.write_text(
        "#!/bin/bash\n"
        "printf '%s\\n' \"$*\" >> \"$QSUB_LOG\"\n"
        "printf '%s\\n' garbage\n",
        encoding="utf-8",
    )
    invalid = subprocess.run(
        ["/bin/bash", str(SUBMIT_T2417), "invalid-qsub-output"],
        check=False,
        capture_output=True,
        text=True,
        env=environment,
    )
    assert invalid.returncode == 1
    assert "qsub raw output for rep 0:\ngarbage\n" in invalid.stderr
    invalid_persisted = [
        json.loads(line)
        for line in (ledger_root / "invalid-qsub-output.submission-ledger.jsonl")
        .read_text(encoding="utf-8")
        .splitlines()
    ]
    assert invalid_persisted[1] == {
        "event": "qsub-output-unparsed",
        "raw_output": "garbage",
        "rep_index": 0,
    }
    assert invalid_persisted[-1]["event"] == "submission-failed"
    assert invalid_persisted[-1]["reason"] == "invalid-job-id"
    assert all(entry["event"] != "job-submitted" for entry in invalid_persisted)


def test_backoff_trace_mode_rejects_nonzero_rep_index_only(tmp_path: Path) -> None:
    parser = probe._argument_parser()
    args = parser.parse_args(
        [
            "--backoff-trace",
            "--cells",
            TRACE_CELLS,
            "--workloads",
            "write-heavy,balanced,read-heavy",
            "--threads",
            "24,48",
            "--rep-index",
            "1",
            "--reps-per-job",
            "1",
            "--extime",
            "3",
            "--out",
            str(probe.DYNAMIC_OUT_PREFIX / "trace" / "test.json"),
        ]
    )
    with pytest.raises(ValueError, match="rep index 0"):
        probe._validate_backoff_trace_contract(
            args,
            probe.parse_cells(args.cells),
            probe._parse_workloads(args.workloads),
            probe._parse_threads(args.threads),
        )


# Independent expectations, transcribed from the frozen cohort seed tables.
EXPECTED_COUNTERFACTUAL_SEEDS = (
    5744733223455690259, 781552995023334429, 1606918558588661,
    16736322205931003081, 1227967287010452276, 2171878327641984105,
    2057459156086657874, 11135758292722279839, 13576760736062537317,
    5470969369189575692, 2410271300384854639, 13467815584134101060,
)
EXPECTED_COUNTERFACTUAL_COHORT2_SEEDS = (
    14481721328008317845, 7453732891837486670, 766609016836229506,
    14479507243158715447, 3736279228254271919, 6574519577559702715,
    15525319108568766040, 13039315294558381935, 16889140200793892447,
    15536816158447092057, 13171317188614694465, 3421410286381859835,
)
COUNTERFACTUAL_REGISTERED_CASES = [
    pytest.param(cohort, seed, id=f"cohort{cohort}-slot{slot:02d}")
    for cohort, seeds in (
        (1, EXPECTED_COUNTERFACTUAL_SEEDS),
        (2, EXPECTED_COUNTERFACTUAL_COHORT2_SEEDS),
    )
    for slot, seed in enumerate(seeds)
]


def _counterfactual_exact_inputs(cohort: int) -> dict:
    return {
        "backoff_trace": True,
        "cells_text": (
            COUNTERFACTUAL_TRACE_CELLS if cohort == 1
            else COUNTERFACTUAL_COHORT2_TRACE_CELLS
        ),
        "workloads_text": "write-heavy,balanced,read-heavy",
        "threads_text": "24,48",
        "rep_index": 0,
        "reps_per_job": 1,
        "extime": 3 if cohort == 1 else 6,
        "backoff_trace_terminal_us": 0 if cohort == 1 else 5_000_000,
    }


def _counterfactual_validator_inputs(exact: dict) -> tuple:
    args = probe._argument_parser().parse_args(
        ["--cells", exact["cells_text"], "--out", "unused.json"]
    )
    for key, value in exact.items():
        setattr(args, {"cells_text": "cells", "workloads_text": "workloads",
                      "threads_text": "threads"}.get(key, key), value)
    return (args, probe.parse_cells(args.cells),
            probe._parse_workloads(args.workloads), probe._parse_threads(args.threads))


def test_counterfactual_seed_table_matches_frozen_section_8_1() -> None:
    section = probe.COUNTERFACTUAL_PREREGISTRATION.read_text().split(
        "### 8.1 seed の逐語一覧", 1
    )[1].split("## 9.", 1)[0]
    original = tuple(int(seed) for seed in re.findall(
        r"^\| \d{2} \| (\d+) \|", section, re.MULTILINE
    ))
    assert original == EXPECTED_COUNTERFACTUAL_SEEDS
    assert probe.COUNTERFACTUAL_PREREGISTERED_STEP_POLICY_SEEDS == original
    assert len(original) == len(set(original)) == 12
    assert probe.CERT_PREREGISTERED_STEP_POLICY_SEEDS == EXPECTED_COUNTERFACTUAL_COHORT2_SEEDS


@pytest.mark.parametrize("cohort,seed", COUNTERFACTUAL_REGISTERED_CASES)
def test_counterfactual_validator_accepts_every_registered_seed(cohort, seed) -> None:
    exact = {**_counterfactual_exact_inputs(cohort), "step_policy_seed": seed}
    probe._validate_backoff_trace_contract(*_counterfactual_validator_inputs(exact))


@pytest.mark.parametrize("cohort,seed", COUNTERFACTUAL_REGISTERED_CASES)
def test_counterfactual_metadata_accepts_every_registered_seed(cohort, seed) -> None:
    document = (probe.COUNTERFACTUAL_PREREGISTRATION if cohort == 1
                else probe.COUNTERFACTUAL_COHORT2_PREREGISTRATION)
    assert probe._artifact_contract_metadata(
        **_counterfactual_exact_inputs(cohort), step_policy_seed=seed
    ) == {
        "schema_version": (probe.TRACE_SCHEMA_VERSION if cohort == 1
                           else probe.COHORT2_TRACE_SCHEMA_VERSION),
        "not_certified": probe.DIAGNOSTIC_NOT_CERTIFIED,
        "counterfactual_preregistration": hashlib.sha256(document.read_bytes()).hexdigest(),
    }


class _Seed(int):
    pass


COUNTERFACTUAL_INVALID_CASES = [
    pytest.param(cohort, seed, id=f"cohort{cohort}-{label}")
    for cohort in (1, 2)
    for label, seed in (
        ("none", None), ("seven", 7), ("zero", 0), ("uint64-max", 2**64 - 1),
        ("compile-default", 11400714819323198485),
        ("other-cohort", 14481721328008317845 if cohort == 1 else 5744733223455690259),
        ("string", "5744733223455690259" if cohort == 1 else "14481721328008317845"),
        ("bool", True),
        ("type-alias", float(1606918558588661) if cohort == 1 else _Seed(766609016836229506)),
    )
] + [
    pytest.param(1, _Seed(1606918558588661), id="cohort1-int-subclass"),
]


@pytest.mark.parametrize("cohort,seed", COUNTERFACTUAL_INVALID_CASES)
def test_counterfactual_validator_rejects_invalid_seed(cohort, seed) -> None:
    exact = {**_counterfactual_exact_inputs(cohort), "step_policy_seed": seed}
    with pytest.raises(ValueError, match=f"step-policy-seed.*cohort{cohort}"):
        probe._validate_backoff_trace_contract(*_counterfactual_validator_inputs(exact))


@pytest.mark.parametrize("cohort,seed", COUNTERFACTUAL_INVALID_CASES)
def test_counterfactual_metadata_omits_binding_for_invalid_seed(cohort, seed, monkeypatch) -> None:
    def unexpected_hash():
        pytest.fail("invalid seed reached preregistration hash")

    monkeypatch.setattr(probe, "_counterfactual_prereg_sha256", unexpected_hash)
    monkeypatch.setattr(probe, "_counterfactual_cohort2_prereg_sha256", unexpected_hash)
    metadata = probe._artifact_contract_metadata(
        **_counterfactual_exact_inputs(cohort), step_policy_seed=seed
    )
    assert "counterfactual_preregistration" not in metadata
    assert metadata["schema_version"] == probe.TRACE_SCHEMA_VERSION


@pytest.mark.parametrize("cohort", (1, 2), ids=("cohort1", "cohort2"))
def test_counterfactual_validator_rejects_omitted_seed(cohort) -> None:
    with pytest.raises(ValueError, match=f"step-policy-seed.*cohort{cohort}"):
        probe._validate_backoff_trace_contract(
            *_counterfactual_validator_inputs(_counterfactual_exact_inputs(cohort))
        )


@pytest.mark.parametrize("cohort", (1, 2), ids=("cohort1", "cohort2"))
def test_counterfactual_metadata_omits_binding_for_omitted_seed(cohort) -> None:
    metadata = probe._artifact_contract_metadata(**_counterfactual_exact_inputs(cohort))
    assert "counterfactual_preregistration" not in metadata
    assert metadata["schema_version"] == probe.TRACE_SCHEMA_VERSION


def _counterfactual_serialized_outputs(cohort, seed, tmp_path):
    exact = _counterfactual_exact_inputs(cohort)
    metadata = probe._artifact_contract_metadata(**exact, step_policy_seed=seed)
    rows = [
        {**probe._cell_identity(cell), **probe._counterfactual_row_metadata(
            preregistration_sha256=metadata.get("counterfactual_preregistration"),
            cell=cell, step_policy_seed=seed,
        )}
        for cell in probe.parse_cells(exact["cells_text"])
    ]
    out = tmp_path / "counterfactual.json"
    out.write_text(json.dumps({**metadata, "runs": rows}))
    for row in rows:
        probe._append_journal(out, row)
    return (json.loads(out.read_text()), [json.loads(line) for line in
            Path(str(out) + ".journal.jsonl").read_text().splitlines()])


@pytest.mark.parametrize("cohort", (1, 2), ids=("cohort1", "cohort2"))
def test_counterfactual_registered_seed_binding_reaches_json_and_journal(cohort, tmp_path) -> None:
    seed = 5744733223455690259 if cohort == 1 else 14481721328008317845
    payload, journal = _counterfactual_serialized_outputs(cohort, seed, tmp_path)
    document = (probe.COUNTERFACTUAL_PREREGISTRATION if cohort == 1
                else probe.COUNTERFACTUAL_COHORT2_PREREGISTRATION)
    expected = hashlib.sha256(document.read_bytes()).hexdigest()
    assert payload["counterfactual_preregistration"] == expected
    assert journal == payload["runs"]
    for rows in (payload["runs"], journal):
        assert len(rows) == 3
        assert all(row["counterfactual_preregistration"] == expected for row in rows)
        assert "step_policy_seed" not in rows[0]
        assert "step_policy_seed" not in rows[1]
        assert rows[2]["step_policy_seed"] == seed


@pytest.mark.parametrize("cohort", (1, 2), ids=("cohort1", "cohort2"))
def test_counterfactual_unregistered_seed_omits_binding_from_json_and_journal(cohort, tmp_path) -> None:
    payload, journal = _counterfactual_serialized_outputs(cohort, 7, tmp_path)
    assert "counterfactual_preregistration" not in payload
    assert journal == payload["runs"]
    assert len(journal) == 3
    for row in payload["runs"] + journal:
        assert "counterfactual_preregistration" not in row


@pytest.mark.parametrize("cohort", (1, 2), ids=("cohort1", "cohort2"))
@pytest.mark.parametrize("field,drift", (
    ("cells_text", COUNTERFACTUAL_TRACE_CELLS[:-1] + "1"),
    ("workloads_text", "write-heavy"),
    ("threads_text", "48"), ("rep_index", 1), ("reps_per_job", 2),
    ("extime", 4), ("backoff_trace_terminal_us", 1),
))
def test_counterfactual_registered_seed_does_not_bypass_exact_axes(cohort, field, drift) -> None:
    exact = {**_counterfactual_exact_inputs(cohort), field: drift,
             "step_policy_seed": 5744733223455690259 if cohort == 1 else 14481721328008317845}
    with pytest.raises(ValueError, match="one exact diagnostic cell set"):
        probe._validate_backoff_trace_contract(*_counterfactual_validator_inputs(exact))
    assert "counterfactual_preregistration" not in probe._artifact_contract_metadata(**exact)


def _run() -> int:
    return pytest.main([__file__, "-q"])


if __name__ == "__main__":
    raise SystemExit(_run())
