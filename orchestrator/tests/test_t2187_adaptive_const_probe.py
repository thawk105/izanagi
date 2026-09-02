from __future__ import annotations

import ast
import copy
from concurrent.futures import ThreadPoolExecutor
import hashlib
import importlib.util
import json
import re
import shutil
import subprocess
import sys
import threading
import time
from pathlib import Path
from types import SimpleNamespace

import pytest

ROOT = Path(__file__).resolve().parents[2]
DRIVER = ROOT / "tools" / "pegasus" / "probes" / "t2187_adaptive_const_probe.py"
PBS = ROOT / "tools" / "pegasus" / "probes" / "t2187_adaptive_const_probe.pbs"
PATCH = ROOT / "patches" / "cicada-adaptive-params.patch"
CCBENCH = ROOT / "external" / "ccbench"
PIN_FULL = "511c9538e4e8efa54b45cda62e72389ed3b706ec"

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
):
    performance = tmp_path / "performance.json"
    if not performance.exists():
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
        "--cells",
        CERT_CELL,
        "--workloads",
        workload,
        "--threads",
        "48",
        "--rep-index",
        str(slot),
        "--reps-per-job",
        "1",
        "--extime",
        "3",
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

    def observed_verifier(trace_dir, expected_commits, timeout_s):
        events.append(
            "positive-control"
            if Path(trace_dir).resolve() == probe.POSITIVE_CONTROL_TRACE.resolve()
            else "target-verifier"
        )
        return real_run_verifier(trace_dir, expected_commits, timeout_s)

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

    def phase_tagged_verifier(trace_dir, expected_commits, timeout_s):
        invocation = real_run_verifier(trace_dir, expected_commits, timeout_s)
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

    def substitute(trace_dir, expected_commits, timeout_s):
        if Path(trace_dir).resolve() == probe.POSITIVE_CONTROL_TRACE.resolve():
            return real_run_verifier(trace_dir, expected_commits, timeout_s)
        return real_run_verifier(G6_SERIAL_TRACE, 200, timeout_s)

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

    def exit_three(trace_dir, expected_commits, timeout_s):
        invocation = real_run_verifier(trace_dir, expected_commits, timeout_s)
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

    def lenient_argv(trace_dir, expected_commits):
        return [*real_argv(trace_dir, expected_commits), "--lenient"]

    monkeypatch.setattr(probe, "_verifier_argv", lenient_argv)
    argv = _certify_argv(tmp_path)
    assert probe.main(argv) == 1
    document = json.loads(Path(argv[-1]).read_text(encoding="utf-8"))
    assert document["reject_reason"] == "verifier-argv-contract"


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
    invocation = probe._run_verifier(G6_SERIAL_TRACE, 200, 30.0)
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
    )
    assert result["certified"] is True
    assert result["stats"]["abort_reasons"] == {}
    assert document["certified_serializable"] == 1


def test_positive_control_real_fixture_accepts_wr_without_v_ver() -> None:
    invocation = probe._run_verifier(
        probe.POSITIVE_CONTROL_TRACE,
        probe.POSITIVE_CONTROL_EXPECTED_COMMITS,
        probe.POSITIVE_CONTROL_TIMEOUT_S,
    )
    probe._validate_positive_control(invocation)
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
        source_run_patch.setattr(probe, "_try_finalize_group", lambda *_args: False)
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
                "thread_num": str(probe.CERT_THREADS[0]),
                "extime": str(probe.CERT_EXTIME),
            }
            document["independent_run_slot"] = slot
            document["pbs_jobid"] = f"{workload}-{slot}"
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
    assert probe._group_receipt_payload(
        result_files,
        performance,
        performance_sha256,
        attempt_id,
        identity,
        identity_file_sha256,
    ) == receipt

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
    assert '"$CELLS_RAW" != tuned:1:1:1000:2560' in text
    assert '"$THREADS_RAW" != 48' in text
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
    performance_branch = text.split('if [[ "$MODE" == performance ]]; then', 1)[1].split(
        "fi", 1
    )[0]
    assert "--mode" not in performance_branch
    assert "--extime" not in performance_branch


def _run() -> int:
    return pytest.main([__file__, "-q"])


if __name__ == "__main__":
    raise SystemExit(_run())
