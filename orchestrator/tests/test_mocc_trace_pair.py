"""Mutation-oriented contract tests for the Mocc TRACE pair gate."""
from __future__ import annotations

import builtins
import copy
import hashlib
import json
from pathlib import Path
from typing import Any

import pytest

from orchestrator.campaign import mocc_trace_pair as pair


OUTER = "e29084e02d626d812281be6f97f45bb2dde3a843"
BASE_OID = "511c9538e4e8efa54b45cda62e72389ed3b706ec"
NEW_OID = "058d0c4e5f237d88ec1c2ebe0739113d82906e47"
JOB_SCRIPT_SHA = "cb9004fa7bc72ba22d73c40e396f3d09bdc156a3ee2ab31b4c274f1322349352"
BINARY_SHA = {
    1: "f4b0ce28bce438d80382af32638c8eb5ddb22ef60291fcc14bf7e2c8051f9366",
    0: "f3dbb186412867e079c921acf63efee0304994867f5ad10042cbfb5c8c6ead35",
}
COMPILER_VERSION = (
    "x86_64-linux-gnu-g++-11 (Ubuntu 11.4.0-1ubuntu1~22.04.3) 11.4.0\n"
    "Copyright (C) 2021 Free Software Foundation, Inc.\n"
    "This is free software; see the source for copying conditions.  There is NO\n"
    "warranty; not even for MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE."
)
GUARANTEE = (
    "選定した macro context における TRACE=0 正規化 preprocess 出力の同一性、"
    "および include 活性の同一性"
)
WORKLOAD_CONFIG = {
    "extime_s": 3,
    "records": 10000,
    "threads": 48,
    "ycsb_max_ope": 10,
    "ycsb_rmw": 0,
    "ycsb_rratio": 50,
    "zipf_skew": 0.9,
}


def _json_bytes(value: object) -> bytes:
    return (
        json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + "\n"
    ).encode("utf-8")


def _sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _write_json(path: Path, value: object) -> bytes:
    raw = _json_bytes(value)
    path.write_bytes(raw)
    return raw


def _job_number(mode: int, ordinal: int) -> int:
    return (949555 if mode == 1 else 949585) + ordinal


def _make_leg(root: Path, mode: int, ordinal: int) -> dict[str, Any]:
    job_number = _job_number(mode, ordinal)
    jobid = f"0:{job_number}.nqsv"
    normalized = f"{job_number}.nqsv"
    leg_dir = root / f"trace{mode}-{ordinal}"
    leg_dir.mkdir(parents=True)
    attempt_dir = (
        "/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-mocc-trace-pair/"
        f"output/env/pegasus/mocc-trace/job-staging/{jobid}"
    )
    run_dir = f"{attempt_dir}/run"
    completed = (778690 + ordinal) if mode == 1 else (1023727 + ordinal)
    elapsed_ns = (3112251374 + ordinal) if mode == 1 else (3091619726 + ordinal)
    elapsed_s = elapsed_ns / 1_000_000_000
    trace_dir = f"{run_dir}/trace"
    if mode == 1:
        evidence = {
            "runs": 1,
            "certified_serializable": 1,
            "non_serializable": 0,
            "indeterminate": 0,
            "results": [
                {
                    "trace_dir": trace_dir,
                    "verdict": "serializable",
                    "certified": True,
                    "serializable": True,
                    "stats": {
                        "txns": completed,
                        "reads": 3767198,
                        "writes": 3826916,
                        "keys": 10000,
                        "edges": 10984663,
                        "abort_reasons": {},
                    },
                    "integrity": {"clean": True},
                    "anomaly_count": 0,
                    "anomalies": [],
                }
            ],
        }
        evidence_path = leg_dir / "verifier.json"
        identity = None
        identity_path = None
    else:
        throughput = completed / elapsed_s
        latency_s = elapsed_s / completed
        evidence = {
            "average_latency_s": latency_s,
            "average_latency_us": latency_s * 1_000_000,
            "completed_txns": completed,
            "elapsed_ns": elapsed_ns,
            "elapsed_s": elapsed_s,
            "measurement_role": "pilot-only; not official calibration",
            "schema_version": "mocc-trace-throughput/v1",
            "throughput_txns_per_s": throughput,
        }
        evidence_path = leg_dir / "throughput.json"
        identity = {
            "schema": "izanagi-trace0-preprocess-identity/v2",
            "guarantee": GUARANTEE,
            "result": "pass",
            "old_oid": BASE_OID,
            "new_oid": NEW_OID,
        }
        identity_path = leg_dir / "trace0-preprocess-identity.json"
    evidence_raw = _write_json(evidence_path, evidence)
    identity_raw = _write_json(identity_path, identity) if identity_path else None

    mocc_trace = {
        "base_oid": BASE_OID,
        "cmake_target": "ycsb_mocc.exe",
        "new_oid": NEW_OID,
        "source_binding": {
            "base_oid": BASE_OID,
            "cmake_target": "ycsb_mocc.exe",
            "new_oid": NEW_OID,
        },
        "trace0_defines": {"CCBENCH_TRACE": "0"},
        "trace1_defines": {"CCBENCH_TRACE": "1"},
        "trace_mode": mode,
        "workload": copy.deepcopy(WORKLOAD_CONFIG),
        "workload_note": (
            "parent-selected pilot workload; not a reproduction of historical "
            "T-816 measurements"
        ),
    }
    report_binding = (
        {
            "guarantee": GUARANTEE,
            "path": "trace0-preprocess-identity.json",
            "schema": "izanagi-trace0-preprocess-identity/v2",
            "sha256": _sha(identity_raw),
        }
        if identity_raw is not None
        else {"guarantee": None, "path": None, "schema": None, "sha256": None}
    )
    artifacts = {
        "attempt_dir": attempt_dir,
        "receipt_sha256_sidecar": "mocc-trace-pilot-receipt.sha256",
        "run_dir": run_dir,
        "submit_receipt": "submit-receipt.json",
        "throughput_json": "throughput.json" if mode == 0 else None,
        "throughput_sha256": _sha(evidence_raw) if mode == 0 else None,
        "trace_dir": trace_dir,
        "verifier_json": "verifier.json" if mode == 1 else None,
        "verifier_sha256": _sha(evidence_raw) if mode == 1 else None,
    }
    receipt = {
        "artifacts": artifacts,
        "build": {
            "binary": (
                f"/scr/0_{normalized}/ccbench-source-build-trace{mode}/"
                "cc/mocc/ycsb_mocc.exe"
            ),
            "binary_sha256": BINARY_SHA[mode],
            "build_dir": f"/scr/0_{normalized}/ccbench-source-build-trace{mode}",
            "cmake_target": "ycsb_mocc.exe",
            "compiler_path": "/usr/bin/x86_64-linux-gnu-g++-11",
            "trace_mode": mode,
        },
        "correctness_tools": {
            "trace0_preprocess_identity_checker": (
                {
                    "path": (
                        "/work/1/SFC/tanab/izanagi/tools/"
                        "check_trace0_preprocess_identity.py"
                    ),
                    "sha256": "b" * 64,
                }
                if mode == 0
                else None
            ),
            "verifier": (
                {
                    "path": "/work/1/SFC/tanab/izanagi/orchestrator/verifier/__main__.py",
                    "sha256": "a" * 64,
                }
                if mode == 1
                else None
            ),
        },
        "created_epoch": 1787727606 + ordinal,
        "eligible_for_refreeze": False,
        "environment": {
            "compiler": {
                "path": "/usr/bin/x86_64-linux-gnu-g++-11",
                "version": COMPILER_VERSION,
            },
            "cpu_model": "Intel(R) Xeon(R) Platinum 8468",
            "environment_tag": "pegasus",
            "expected_cpu_model": "Intel Xeon Platinum 8468",
            "topology": {"cpuset_size": 48, "ht_off": True, "physical_visible": 48},
            "trace0_preprocess_identity_checker_interpreter_path": (
                "/usr/bin/python3.10" if mode == 0 else None
            ),
            "verifier_interpreter_path": "/usr/bin/python3.10" if mode == 1 else None,
        },
        "gates": {
            "trace0_preprocess_identity_rc": "0" if mode == 0 else "not-run",
            "verifier_rc": "not-run" if mode == 0 else "0",
            "workload_rc": "0",
        },
        "mocc_trace": mocc_trace,
        "official_certification": False,
        "pbs": {"jobid": jobid},
        "pilot": True,
        "schema_version": "mocc-trace-pilot-receipt/v3",
        "source": {
            "materialization": "git worktree add --detach in qsub job body",
            "outer_gitlink_advanced": False,
            "outer_repo_commit": OUTER,
            "submodule_base_oid": BASE_OID,
            "submodule_new_oid": NEW_OID,
        },
        "status": "completed",
        "trace0_preprocess_identity_report": report_binding,
        "workload": {
            "argv": ["-ycsb_tuple_num=10000", "-thread_num=48", "-extime=3"],
            "argv_source": "t139_r4_env_probe.py gflags spelling",
            "completed_txns": completed,
            "config": copy.deepcopy(WORKLOAD_CONFIG),
            "elapsed_ns": elapsed_ns,
            "elapsed_s": elapsed_s,
        },
    }
    receipt_path = leg_dir / "mocc-trace-pilot-receipt.json"
    receipt_raw = _write_json(receipt_path, receipt)
    job_result = {
        "binary_sha256": BINARY_SHA[mode],
        "completed_epoch": 1787727606 + ordinal,
        "job_script_sha256": JOB_SCRIPT_SHA,
        "pbs_jobid": jobid,
        "receipt_sha256": _sha(receipt_raw),
        "schema_version": "mocc-trace-pilot-job-result/v2",
        "trace0_preprocess_identity_report": copy.deepcopy(report_binding),
    }
    job_path = leg_dir / "job-result.json"
    _write_json(job_path, job_result)
    parts = [str(receipt_path), str(job_path), str(evidence_path)]
    if identity_path is not None:
        parts.append(str(identity_path))
    return {
        "mode": mode,
        "receipt": receipt,
        "receipt_path": receipt_path,
        "job": job_result,
        "job_path": job_path,
        "evidence": evidence,
        "evidence_path": evidence_path,
        "identity": identity,
        "identity_path": identity_path,
        "parts": parts,
    }


def _make_bundle(tmp_path: Path) -> list[dict[str, Any]]:
    return [
        _make_leg(tmp_path, 1, 0),
        _make_leg(tmp_path, 0, 0),
        _make_leg(tmp_path, 1, 1),
        _make_leg(tmp_path, 0, 1),
    ]


def _rewrite_receipt(leg: dict[str, Any], *, bind_job: bool = True) -> None:
    raw = _write_json(leg["receipt_path"], leg["receipt"])
    if bind_job:
        leg["job"]["receipt_sha256"] = _sha(raw)
        _write_json(leg["job_path"], leg["job"])


def _rewrite_evidence(leg: dict[str, Any], *, bind_receipt: bool = True) -> None:
    raw = _write_json(leg["evidence_path"], leg["evidence"])
    if bind_receipt:
        key = "verifier_sha256" if leg["mode"] == 1 else "throughput_sha256"
        leg["receipt"]["artifacts"][key] = _sha(raw)
        _rewrite_receipt(leg)


def _args(output: Path, bundle: list[dict[str, Any]], *, expected: str | None = OUTER) -> list[str]:
    argv = ["--output", str(output)]
    if expected is not None:
        argv.extend(("--expected-outer-commit", expected))
    for leg in bundle:
        argv.append("--leg")
        argv.extend(leg["parts"])
    return argv


def _assert_rejected(tmp_path: Path, bundle: list[dict[str, Any]], *, expected: str | None = OUTER) -> None:
    output = tmp_path / "pair.json"
    assert pair.main(_args(output, bundle, expected=expected)) == 2
    assert not output.exists()
    assert not (tmp_path / "mocc-trace-pair-receipt.sha256").exists()


def test_pair_accepts_two_per_mode_actual_shape(tmp_path: Path) -> None:
    bundle = _make_bundle(tmp_path)
    output = tmp_path / "pair.json"
    assert pair.main(_args(output, list(reversed(bundle)))) == 0
    receipt = json.loads(output.read_text(encoding="utf-8"))
    assert receipt["schema_version"] == "mocc-trace-pair-receipt/v2"
    assert receipt["n_per_trace_mode"] == 2
    assert receipt["identity"]["outer_repo_commit"] == OUTER
    assert receipt["build_identity"]["job_script_sha256"] == JOB_SCRIPT_SHA
    assert receipt["build_identity"]["compiler_version"] == COMPILER_VERSION
    assert receipt["build_identity"]["binary_sha256_by_trace_mode"] == {
        "trace0": [BINARY_SHA[0], BINARY_SHA[0]],
        "trace1": [BINARY_SHA[1], BINARY_SHA[1]],
    }
    assert receipt["build_identity"]["same_mode_binary_sha256_equal"] is True
    assert [leg["trace_mode"] for leg in receipt["legs"]] == [0, 0, 1, 1]
    assert [leg["build"]["binary_sha256"] for leg in receipt["legs"]] == [
        BINARY_SHA[0],
        BINARY_SHA[0],
        BINARY_SHA[1],
        BINARY_SHA[1],
    ]
    assert all("correctness" not in leg for leg in receipt["legs"][:2])
    assert all("performance" not in leg for leg in receipt["legs"][2:])
    assert receipt["throughput_dispersion_by_trace_mode"]["trace0"][
        "threshold_gate_applied"
    ] is False
    assert receipt["throughput_dispersion_by_trace_mode"]["trace1"] == {
        "min_txns_per_s": None,
        "max_txns_per_s": None,
        "relative_width": None,
        "reason": "correctness-only; TRACE=1 counters are not performance evidence",
        "threshold_gate_applied": False,
    }
    raw = output.read_bytes()
    assert (tmp_path / "mocc-trace-pair-receipt.sha256").read_text(
        encoding="ascii"
    ) == _sha(raw) + "\n"


@pytest.mark.parametrize("missing_mode", (0, 1))
def test_pair_rejects_cardinality_mutation(tmp_path: Path, missing_mode: int) -> None:
    bundle = _make_bundle(tmp_path)
    for index, leg in enumerate(bundle):
        if leg["mode"] == missing_mode:
            del bundle[index]
            break
    _assert_rejected(tmp_path, bundle)


def test_pair_rejects_one_per_mode_cardinality_mutation(tmp_path: Path) -> None:
    bundle = _make_bundle(tmp_path)
    one_per_mode = [
        next(leg for leg in bundle if leg["mode"] == mode) for mode in (0, 1)
    ]
    _assert_rejected(tmp_path, one_per_mode)


def test_pair_n_equals_two_is_positive_control_against_n_three_mutation(
    tmp_path: Path,
) -> None:
    output = tmp_path / "pair.json"
    assert pair.main(_args(output, _make_bundle(tmp_path))) == 0


@pytest.mark.parametrize(
    "mutation",
    (
        "trace1-throughput-reference",
        "trace0-verifier-reference",
        "trace1-mode-evidence-sha",
        "trace0-mode-evidence-sha-m17",
        "policy-projection",
        "official-certification",
        "job-script-sha",
        "compiler-version-m07-prime",
        "identity-report-sha",
        "correctness-tool-path",
        "correctness-tool-sha",
    ),
)
def test_pair_rejects_registered_predicate_mutation(
    tmp_path: Path, mutation: str
) -> None:
    bundle = _make_bundle(tmp_path)
    trace1 = next(leg for leg in bundle if leg["mode"] == 1)
    trace0 = next(leg for leg in bundle if leg["mode"] == 0)
    if mutation == "trace1-throughput-reference":
        trace1["receipt"]["artifacts"]["throughput_json"] = "throughput.json"
        _rewrite_receipt(trace1)
    elif mutation == "trace0-verifier-reference":
        trace0["receipt"]["artifacts"]["verifier_json"] = "verifier.json"
        _rewrite_receipt(trace0)
    elif mutation == "trace1-mode-evidence-sha":
        trace1["receipt"]["artifacts"]["verifier_sha256"] = "0" * 64
        _rewrite_receipt(trace1)
    elif mutation == "trace0-mode-evidence-sha-m17":
        trace0["receipt"]["artifacts"]["throughput_sha256"] = "0" * 64
        _rewrite_receipt(trace0)
    elif mutation == "policy-projection":
        trace0["receipt"]["mocc_trace"]["trace0_defines"]["CCBENCH_TRACE"] = "1"
        _rewrite_receipt(trace0)
    elif mutation == "official-certification":
        trace1["receipt"]["official_certification"] = True
        _rewrite_receipt(trace1)
    elif mutation == "job-script-sha":
        trace1["job"]["job_script_sha256"] = "2" * 64
        _write_json(trace1["job_path"], trace1["job"])
    elif mutation == "compiler-version-m07-prime":
        trace0["receipt"]["environment"]["compiler"]["version"] = "other compiler"
        _rewrite_receipt(trace0)
    elif mutation == "identity-report-sha":
        trace0["receipt"]["trace0_preprocess_identity_report"]["sha256"] = "3" * 64
        trace0["job"]["trace0_preprocess_identity_report"]["sha256"] = "3" * 64
        _rewrite_receipt(trace0)
    elif mutation == "correctness-tool-path":
        trace1["receipt"]["correctness_tools"]["verifier"]["path"] = "relative.py"
        _rewrite_receipt(trace1)
    elif mutation == "correctness-tool-sha":
        trace0["receipt"]["correctness_tools"][
            "trace0_preprocess_identity_checker"
        ]["sha256"] = "not-a-sha"
        _rewrite_receipt(trace0)
    else:
        raise AssertionError(mutation)
    _assert_rejected(tmp_path, bundle)


def test_pair_rejects_wrong_expected_outer_commit(tmp_path: Path) -> None:
    _assert_rejected(tmp_path, _make_bundle(tmp_path), expected="f" * 40)


def test_pair_rejects_missing_expected_outer_commit_m16(tmp_path: Path) -> None:
    _assert_rejected(tmp_path, _make_bundle(tmp_path), expected=None)


def test_pair_accepts_different_binary_sha_within_mode_m15(tmp_path: Path) -> None:
    bundle = _make_bundle(tmp_path)
    trace0 = [leg for leg in bundle if leg["mode"] == 0][1]
    different_sha = "1" * 64
    trace0["receipt"]["build"]["binary_sha256"] = different_sha
    trace0["job"]["binary_sha256"] = different_sha
    _rewrite_receipt(trace0)

    output = tmp_path / "pair.json"
    assert pair.main(_args(output, bundle)) == 0
    receipt = json.loads(output.read_text(encoding="utf-8"))
    assert receipt["build_identity"]["same_mode_binary_sha256_equal"] is False
    assert receipt["build_identity"]["binary_sha256_by_trace_mode"]["trace0"] == [
        BINARY_SHA[0],
        different_sha,
    ]
    assert [
        leg["build"]["binary_sha256"]
        for leg in receipt["legs"]
        if leg["trace_mode"] == 0
    ] == [BINARY_SHA[0], different_sha]


@pytest.mark.parametrize(
    ("mutation", "replacement"),
    (
        ("certified_serializable", 0),
        ("non_serializable", 1),
        ("result_verdict", "non-serializable"),
        ("result_certified", False),
        ("anomaly_count", 1),
        ("anomalies", [{"kind": "fixture"}]),
    ),
)
def test_pair_rejects_each_m09_verifier_predicate_independently(
    tmp_path: Path, mutation: str, replacement: object
) -> None:
    bundle = _make_bundle(tmp_path)
    trace1 = next(leg for leg in bundle if leg["mode"] == 1)
    verifier = trace1["evidence"]
    result = verifier["results"][0]
    if mutation in {"certified_serializable", "non_serializable"}:
        verifier[mutation] = replacement
    elif mutation == "result_verdict":
        result["verdict"] = replacement
    elif mutation == "result_certified":
        result["certified"] = replacement
    elif mutation in {"anomaly_count", "anomalies"}:
        result[mutation] = replacement
    else:
        raise AssertionError(mutation)
    _rewrite_evidence(trace1)
    _assert_rejected(tmp_path, bundle)


def test_pair_rejects_old_v2_pilot_schema_before_field_validation(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    bundle = _make_bundle(tmp_path)
    old = bundle[0]
    old["receipt"]["schema_version"] = "mocc-trace-pilot-receipt/v2"
    del old["receipt"]["correctness_tools"]
    del old["receipt"]["artifacts"]["verifier_sha256"]
    del old["receipt"]["artifacts"]["throughput_sha256"]
    _rewrite_receipt(old)

    _assert_rejected(tmp_path, bundle)
    assert "pilot receipt schema differs" in capsys.readouterr().err


def test_pair_records_wide_throughput_without_threshold_rejection(tmp_path: Path) -> None:
    bundle = _make_bundle(tmp_path)
    trace0 = [leg for leg in bundle if leg["mode"] == 0][1]
    trace0["evidence"]["elapsed_ns"] = 1
    trace0["evidence"]["elapsed_s"] = 1e-9
    completed = trace0["evidence"]["completed_txns"]
    trace0["evidence"]["throughput_txns_per_s"] = completed / 1e-9
    trace0["evidence"]["average_latency_s"] = 1e-9 / completed
    trace0["evidence"]["average_latency_us"] = 1e-3 / completed
    trace0["receipt"]["workload"]["elapsed_ns"] = 1
    trace0["receipt"]["workload"]["elapsed_s"] = 1e-9
    _rewrite_evidence(trace0)
    output = tmp_path / "pair.json"
    assert pair.main(_args(output, bundle)) == 0
    summary = json.loads(output.read_text(encoding="utf-8"))[
        "throughput_dispersion_by_trace_mode"
    ]["trace0"]
    assert summary["max_txns_per_s"] > summary["min_txns_per_s"] * 1000
    assert summary["relative_width"] > 1000
    assert summary["threshold_gate_applied"] is False


@pytest.mark.parametrize(
    ("mutation", "rewrite"),
    (
        ("receipt-sha", False),
        ("jobid", True),
        ("binary-sha", True),
        ("trace0-report-binding", True),
    ),
)
def test_pair_rejects_job_result_mutation(
    tmp_path: Path, mutation: str, rewrite: bool
) -> None:
    bundle = _make_bundle(tmp_path)
    trace0 = next(leg for leg in bundle if leg["mode"] == 0)
    if mutation == "receipt-sha":
        trace0["receipt"]["created_epoch"] += 1
        _rewrite_receipt(trace0, bind_job=False)
    elif mutation == "jobid":
        trace0["job"]["pbs_jobid"] = "0:999999.nqsv"
    elif mutation == "binary-sha":
        trace0["job"]["binary_sha256"] = "4" * 64
    elif mutation == "trace0-report-binding":
        trace0["job"]["trace0_preprocess_identity_report"]["sha256"] = "5" * 64
    else:
        raise AssertionError(mutation)
    if rewrite:
        _write_json(trace0["job_path"], trace0["job"])
    _assert_rejected(tmp_path, bundle)


@pytest.mark.parametrize(
    "mutation",
    (
        "trace1-inline-throughput",
        "trace0-inline-verdict",
        "trace1-verifier-not-run",
        "trace1-integrity",
        "trace1-txns",
        "trace0-checker-not-run",
        "trace0-throughput-role",
        "trace0-throughput-crossbind",
        "trace0-throughput-recompute",
        "eligible-refreeze",
    ),
)
def test_pair_rejects_side_specific_mutation(tmp_path: Path, mutation: str) -> None:
    bundle = _make_bundle(tmp_path)
    trace1 = next(leg for leg in bundle if leg["mode"] == 1)
    trace0 = next(leg for leg in bundle if leg["mode"] == 0)
    if mutation == "trace1-inline-throughput":
        trace1["receipt"]["throughput_txns_per_s"] = 1.0
        _rewrite_receipt(trace1)
    elif mutation == "trace0-inline-verdict":
        trace0["receipt"]["verdict"] = "serializable"
        _rewrite_receipt(trace0)
    elif mutation == "trace1-verifier-not-run":
        trace1["receipt"]["gates"]["verifier_rc"] = "not-run"
        _rewrite_receipt(trace1)
    elif mutation == "trace1-integrity":
        trace1["evidence"]["results"][0]["integrity"]["clean"] = False
        _rewrite_evidence(trace1)
    elif mutation == "trace1-txns":
        trace1["evidence"]["results"][0]["stats"]["txns"] += 1
        _rewrite_evidence(trace1)
    elif mutation == "trace0-checker-not-run":
        trace0["receipt"]["gates"]["trace0_preprocess_identity_rc"] = "not-run"
        _rewrite_receipt(trace0)
    elif mutation == "trace0-throughput-role":
        trace0["evidence"]["measurement_role"] = "official calibration"
        _rewrite_evidence(trace0)
    elif mutation == "trace0-throughput-crossbind":
        trace0["evidence"]["completed_txns"] += 1
        _rewrite_evidence(trace0)
    elif mutation == "trace0-throughput-recompute":
        trace0["evidence"]["throughput_txns_per_s"] *= 1.01
        _rewrite_evidence(trace0)
    elif mutation == "eligible-refreeze":
        trace0["receipt"]["eligible_for_refreeze"] = True
        _rewrite_receipt(trace0)
    else:
        raise AssertionError(mutation)
    _assert_rejected(tmp_path, bundle)


@pytest.mark.parametrize(
    "attribute",
    ("normalized-jobid", "build-dir", "binary-path", "attempt-dir", "run-dir"),
)
def test_pair_rejects_separation_mutation(tmp_path: Path, attribute: str) -> None:
    bundle = _make_bundle(tmp_path)
    first, second = bundle[0], bundle[2]
    if attribute == "normalized-jobid":
        second["receipt"]["pbs"]["jobid"] = first["receipt"]["pbs"]["jobid"][2:]
        second["job"]["pbs_jobid"] = first["receipt"]["pbs"]["jobid"][2:]
    elif attribute == "build-dir":
        second["receipt"]["build"]["build_dir"] = first["receipt"]["build"]["build_dir"]
    elif attribute == "binary-path":
        second["receipt"]["build"]["binary"] = first["receipt"]["build"]["binary"]
    elif attribute == "attempt-dir":
        second["receipt"]["artifacts"]["attempt_dir"] = first["receipt"]["artifacts"]["attempt_dir"]
    elif attribute == "run-dir":
        second["receipt"]["artifacts"]["run_dir"] = first["receipt"]["artifacts"]["run_dir"]
    else:
        raise AssertionError(attribute)
    _rewrite_receipt(second)
    _assert_rejected(tmp_path, bundle)


def test_pair_receipt_is_create_only_and_sha_bound(tmp_path: Path) -> None:
    bundle = _make_bundle(tmp_path)
    output = tmp_path / "pair.json"
    output.write_text("sentinel\n", encoding="utf-8")
    assert pair.main(_args(output, bundle)) == 2
    assert output.read_text(encoding="utf-8") == "sentinel\n"
    output.unlink()
    sidecar = tmp_path / "mocc-trace-pair-receipt.sha256"
    sidecar.write_text("sentinel\n", encoding="ascii")
    assert pair.main(_args(output, bundle)) == 2
    assert not output.exists()
    assert sidecar.read_text(encoding="ascii") == "sentinel\n"


def test_pair_removes_partial_sidecar_after_write_failure(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    bundle = _make_bundle(tmp_path)
    output = tmp_path / "pair.json"
    sidecar = tmp_path / "mocc-trace-pair-receipt.sha256"
    real_open = builtins.open

    class FailingSidecar:
        def __init__(self, handle: Any) -> None:
            self.handle = handle

        def __enter__(self) -> "FailingSidecar":
            self.handle.__enter__()
            return self

        def __exit__(self, *args: object) -> object:
            return self.handle.__exit__(*args)

        def write(self, value: str) -> int:
            del value
            raise OSError("fixture sidecar write failure")

    def failing_open(file: object, mode: str = "r", *args: object, **kwargs: object):
        handle = real_open(file, mode, *args, **kwargs)
        if Path(file) == sidecar and mode == "x":
            return FailingSidecar(handle)
        return handle

    monkeypatch.setattr(pair, "open", failing_open, raising=False)
    assert pair.main(_args(output, bundle)) == 2
    assert not output.exists()
    assert not sidecar.exists()

    monkeypatch.delattr(pair, "open")
    assert pair.main(_args(output, bundle)) == 0


def test_pair_rejects_json_type_confusion(tmp_path: Path) -> None:
    bundle = _make_bundle(tmp_path)
    bundle[0]["receipt"]["pilot"] = 1
    _rewrite_receipt(bundle[0])
    _assert_rejected(tmp_path, bundle)


def test_pair_rejects_symlink_input_and_duplicate_json_key(tmp_path: Path) -> None:
    bundle = _make_bundle(tmp_path)
    target = bundle[0]["receipt_path"]
    link = tmp_path / "receipt-link.json"
    link.symlink_to(target)
    bundle[0]["parts"][0] = str(link)
    _assert_rejected(tmp_path, bundle)

    bundle = _make_bundle(tmp_path / "duplicate")
    receipt_path = bundle[0]["receipt_path"]
    receipt_path.write_text('{"schema_version":"a","schema_version":"b"}\n')
    _assert_rejected(tmp_path / "duplicate", bundle)
