from __future__ import annotations

import ast
from contextlib import contextmanager
import importlib.util
import json
import re
import subprocess
import sys
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


SERIAL_TRACE_WITH_ABORT = """\
C 0 0 2 1 1 1
R 0 aa 1 0
W 0 aa U 2 1
E 0
A validation-failure
C 1 0 2 2 1 1
R 1 aa 2 1
W 1 bb U 2 2
E 1
"""


SERIAL_TRACE_WITHOUT_ABORT = SERIAL_TRACE_WITH_ABORT.replace(
    "A validation-failure\n", ""
)


SERIAL_TRACE_WITHOUT_EDGES = """\
C 0 0 2 1 1 1
R 0 aa 1 0
W 0 aa U 2 1
E 0
A validation-failure
C 1 0 2 2 1 1
R 1 bb 1 0
W 1 bb U 2 2
E 1
"""


def _certify_argv(tmp_path: Path, *, workload: str = "balanced", slot: int = 0):
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
    return [
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
        "--group-receipt-out",
        str(tmp_path / "group.json"),
        "--performance-artifact",
        str(performance),
        "--out",
        str(tmp_path / f"certify-{workload}-slot{slot}.json"),
    ]


def _install_certification_runtime(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    *,
    trace_text: str = SERIAL_TRACE_WITH_ABORT,
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
    monkeypatch.setattr(probe, "_ccbench_head", lambda _path: PIN_FULL)
    monkeypatch.setattr(probe, "assert_pinned_clean", lambda *_args: None)

    @contextmanager
    def fake_checkout(_submodule, _pin):
        yield str(tmp_path / "ccbench-source")

    @contextmanager
    def fake_applied(*_args):
        yield

    monkeypatch.setattr(probe, "isolated_checkout", fake_checkout)
    monkeypatch.setattr(probe, "applied", fake_applied)
    monkeypatch.setattr(
        probe.buildcache, "compilers_for_current_site", lambda: ("gcc", "g++")
    )
    monkeypatch.setattr(
        probe.source_digest,
        "resolve_evidence",
        lambda *_args, **_kwargs: SimpleNamespace(genome_sha256="e" * 64),
    )
    monkeypatch.setattr(probe, "build_run_context", lambda **_kwargs: object())
    monkeypatch.setattr(probe, "attest_generator_output", lambda *_args, **_kwargs: object())
    monkeypatch.setattr(probe, "derive_build_admission", lambda *_args, **_kwargs: object())

    def fake_build(*_args, **kwargs):
        events.append("build")
        if kwargs.get("trace") is not True:
            raise RuntimeError("certification build did not request trace=True")
        return SimpleNamespace(binary="ycsb_silo", bin_sha256="a" * 64)

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
            abort_counts=1 if "\nA " in trace_text else 0,
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
    assert document["trace_manifest"]["file_count"] == 1
    assert document["run_phase"]["cpu_over_elapsed"] is not None
    assert document["verify_phase"]["cpu_over_elapsed"] is not None
    assert document["job_phase"]["cpu_over_elapsed"] is not None
    assert "run_phase" in document and "verify_phase" in document
    assert not (tmp_path / "group.json").exists()

    with pytest.raises(FileExistsError, match="refusing to overwrite"):
        probe.main(argv)


@pytest.mark.parametrize(
    ("trace_text", "expected_reason"),
    (
        (SERIAL_TRACE_WITHOUT_ABORT, "target-abort-empty"),
        (SERIAL_TRACE_WITHOUT_EDGES, "target-edges-empty"),
    ),
    ids=("M1-abort-sum", "M2-edges"),
)
def test_public_certification_rejects_nonexercising_target_for_one_reason(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    trace_text: str,
    expected_reason: str,
) -> None:
    _install_certification_runtime(monkeypatch, tmp_path, trace_text=trace_text)
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
        invocation = real_run_verifier(trace_dir, expected_commits, timeout_s)
        if Path(trace_dir).resolve() != probe.POSITIVE_CONTROL_TRACE.resolve():
            invocation["json"]["results"][0]["trace_dir"] = str(
                probe.POSITIVE_CONTROL_TRACE.resolve()
            )
        return invocation

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
    calls = 0

    def drifting_identity():
        nonlocal calls
        calls += 1
        return {"repository_commit": "f" * 40, "module_sha256": {"call": calls}}

    monkeypatch.setattr(probe, "_verifier_identity", drifting_identity)
    argv = _certify_argv(tmp_path)
    assert probe.main(argv) == 1
    document = json.loads(Path(argv[-1]).read_text(encoding="utf-8"))
    assert document["reject_reason"] == "verifier-identity-mismatch"


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


def test_group_receipt_requires_exact_24_terminal_request_set(
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
    result_files = []
    identity = {"repository_commit": "f" * 40, "module_sha256": {"x.py": "a" * 64}}
    for workload in probe.CERT_WORKLOADS:
        for slot in probe.CERT_SLOTS:
            path = tmp_path / f"certify-{workload}-slot{slot}.json"
            path.write_text(
                json.dumps(
                    {
                        "schema_version": probe.CERTIFICATION_SCHEMA_VERSION,
                        "workload": workload,
                        "independent_run_slot": slot,
                        "pbs_jobid": f"{workload}-{slot}",
                        "terminal_status": "certified",
                        "binary_sha256": "b" * 64,
                        "patch_sha256": "c" * 64,
                        "ccbench_commit": PIN_FULL,
                        "verifier_identity": identity,
                    }
                )
                + "\n",
                encoding="utf-8",
            )
            result_files.append(path)

    with pytest.raises(probe.CertificationReject) as caught:
        probe._group_receipt_payload(result_files[:-1], performance)
    assert caught.value.reason == "group-incomplete"

    receipt = probe._group_receipt_payload(result_files, performance)
    assert receipt["complete"] is True
    assert receipt["expected_requests"] == receipt["terminal_requests"] == 24
    assert len(receipt["results"]) == 24
    assert receipt["claim"] == probe.ALLOWED_GROUP_CLAIM


def test_public_certification_creates_group_only_after_all_24_requests(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    _install_certification_runtime(monkeypatch, tmp_path)
    pairs = [
        (workload, slot)
        for workload in probe.CERT_WORKLOADS
        for slot in probe.CERT_SLOTS
    ]
    for index, (workload, slot) in enumerate(pairs):
        private_tmp = tmp_path / f"runtime-{index}"
        private_tmp.mkdir()
        monkeypatch.setenv("TMPDIR", str(private_tmp))
        monkeypatch.setenv("PBS_JOBID", f"{10000 + index}.test")
        argv = _certify_argv(tmp_path, workload=workload, slot=slot)
        assert probe.main(argv) == 0
        if index < 23:
            assert not (tmp_path / "group.json").exists()

    receipt = json.loads((tmp_path / "group.json").read_text(encoding="utf-8"))
    assert receipt["complete"] is True
    assert receipt["terminal_requests"] == 24
    assert {
        (row["workload"], row["independent_run_slot"])
        for row in receipt["results"]
    } == set(pairs)


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
    assert "qsub -l elapstim_req=02:00:00" in text
    assert '--outer-walltime-s "$OUTER_WALLTIME_S"' in text
    assert '--verifier-timeout-s "$VERIFIER_TIMEOUT_S"' in text
    performance_branch = text.split('if [[ "$MODE" == performance ]]; then', 1)[1].split(
        "fi", 1
    )[0]
    assert "--mode" not in performance_branch
    assert "--extime" not in performance_branch


def _run() -> int:
    return pytest.main([__file__, "-q"])


if __name__ == "__main__":
    raise SystemExit(_run())
