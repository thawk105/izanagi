"""T-2851 runner contract tests; binary and node execution are fixture-only."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
import hashlib
import json
from pathlib import Path
import subprocess
import sys

import pytest

from orchestrator.campaign import t2851_transfer_runner as runner
from orchestrator.verifier.core import verify_trace_dir


def _record():
    refs = {a: {"R0": "R0", "R1": "R1", "R2": "R2"}
            for a in ("wh-base", "bal-base", "rh-base")}
    binaries = {k: {"perf_path": "/unused/" + k, "perf_sha256": "0" * 64,
                    "trace_path": "/unused/" + k, "trace_sha256": "0" * 64}
                for k in ("R0", "R1", "R2", "K")}
    return dict(workload="ycsb", selection_rule="frozen", binaries=binaries,
                references={"silo": refs},
                search_groups=[dict(task="t", method="m", learning_cells=["wh-base"],
                                    independent_searches=["1"], reachability=False)],
                series=[dict(task="t", method="m", independent_search="1",
                             protocol="silo", anchor="wh-base", selected_identity="K")])


def _freeze():
    return runner.freeze_candidates(_record())


def test_cells_and_known_separate():
    y = runner.cells("ycsb")
    assert len(y) == 26 and sum(c.held_out for c in y) == 23
    assert len(runner.cells("tpcc", "s1")) == 12
    assert len(runner.cells("tpcc", "s2")) == 12
    assert runner.known_separate("silo", "bal-rmw1")
    assert not runner.known_separate("mocc", "bal-rmw1")
    assert not runner.known_separate("silo", "wh-rmw1")
    assert next(c for c in y if c.name == "wh-rr25").flags["ycsb_rratio"] == "25"
    assert next(c for c in runner.cells("tpcc", "s2") if c.name == "s2-L-scan10").flags["tpcc_perc_delivery"] == "10"


def test_order_hand_calculated_and_prefix():
    names = ["c", "a", "b"]
    ordered = sorted(names)
    key = "t2851-order-v1|1|silo|wh-base|1"
    for i in (2, 1):
        j = int.from_bytes(hashlib.sha256(f"{key}|{i}".encode()).digest(), "big") % (i + 1)
        ordered[i], ordered[j] = ordered[j], ordered[i]
    actual = runner.order_identities(names, workload="ycsb", stage=None,
                                     cohort=1, protocol="silo", cell="wh-base", block=1)
    assert actual == tuple(ordered)
    assert any(actual != runner.order_identities(names, workload="ycsb", stage=None,
               cohort=1, protocol="silo", cell="wh-base", block=b) for b in range(2, 33))
    assert runner.order_identities(names, workload="tpcc", stage="s1", cohort=1,
                                   protocol="silo", cell="wh-base", block=1) != actual


def test_freeze_m_and_same_identity():
    frozen = _freeze()
    assert frozen["m_by_family"] == {"ycsb": 18}  # wh: 9 cells, 2 strong refs
    assert len(frozen["jobs"]) == 2 * 26
    assert frozen["sha256"] == runner._sha({k: frozen[k] for k in
        ("workload", "stage", "series", "search_groups", "selection_rule", "references", "binaries")})
    changed = _record()
    changed["series"][0]["selected_identity"] = "R1"
    same = runner.freeze_candidates(changed)
    assert any(x["same_identity"] for x in same["comparisons"])
    assert same["m_by_family"]["ycsb"] == 9
    assert all(x["family"] == "descriptive" for x in frozen["comparisons"]
               if x["reference"] == "R0")


@pytest.mark.parametrize("change", ["missing", "duplicate", "exclusive", "unknown", "learning", "reference"])
def test_freeze_rejects_invalid(change):
    rec = _record()
    if change == "missing":
        rec["series"] = []
    elif change == "duplicate":
        rec["series"].append(dict(rec["series"][0]))
    elif change == "exclusive":
        rec["series"][0]["selection_failure"] = "failed"
    elif change == "unknown":
        rec["series"][0]["selected_identity"] = "absent"
    elif change == "learning":
        rec["search_groups"][0]["learning_cells"] = ["wh-rr25"]
    else:
        rec["references"]["silo"]["wh-base"]["R1"] = "absent"
    with pytest.raises(ValueError):
        runner.freeze_candidates(rec)


def test_activation_rejects_before_measurement(monkeypatch):
    frozen = _freeze()
    spec = dict(freeze=frozen, cohort=1, protocol="silo", cell="wh-rr25")
    def forbidden(*a, **kw):
        raise AssertionError("measurement reached")
    monkeypatch.setattr(runner.calibrator, "run_once", forbidden)
    with pytest.raises(ValueError, match="activation"):
        runner.run_job(spec)
    with pytest.raises(ValueError, match="activation"):
        runner.verify_candidate(dict(spec, identity="K"))
    activation = {"decision_id": "D", "freeze_sha256": frozen["sha256"]}
    assert runner.activation_allowed(runner._find_cell(frozen, "wh-rr25"), frozen, activation)
    assert not runner.activation_allowed(runner._find_cell(frozen, "wh-rr25"), frozen,
                                         activation | {"freeze_sha256": "wrong"})
    assert runner.activation_allowed(runner._find_cell(frozen, "wh-base"), frozen, None)
    tpcc = {"sha256": "h"}
    cell = runner._find_cell({"workload": "tpcc", "stage": "s1"}, "s1-H-wh04")
    assert not runner.activation_allowed(cell, tpcc, {"decision_id": "D", "freeze_sha256": "h"})
    assert runner.activation_allowed(cell, tpcc, {"decision_id": "D", "freeze_sha256": "h",
                                                 "stage": "s1", "certification_path": "path"})


def test_cohort_two_boundary_and_rejections():
    t = datetime(2026, 1, 1, tzinfo=timezone.utc)
    args = dict(cohort1_last_end_utc=t.isoformat(), prior_hostname="A", current_hostname="A")
    for count in (0, 1):
        gate = runner.cohort2_admission(**args, same_host_rejections=count,
                                        cohort2_first_start_utc=(t + timedelta(hours=24)).isoformat())
        assert gate["next_action"] == "resubmit-same-host" and not gate["measure"]
    third = runner.cohort2_admission(**args, same_host_rejections=2,
                                     cohort2_first_start_utc=(t + timedelta(hours=24)).isoformat())
    assert third["measure"] and not third["separate_allocation"]
    early = runner.cohort2_admission(**(args | {"current_hostname": "B"}), same_host_rejections=0,
                                     cohort2_first_start_utc=(t + timedelta(hours=24, seconds=-1)).isoformat())
    assert early["next_action"] == "wait-24h" and not early["measure"]
    ontime = runner.cohort2_admission(**(args | {"current_hostname": "B"}), same_host_rejections=0,
                                      cohort2_first_start_utc=(t + timedelta(hours=24)).isoformat())
    assert ontime["measure"] and ontime["separate_allocation"]


def test_isolation_retry_once(monkeypatch):
    frozen = _freeze()
    monkeypatch.setattr(runner, "_probe", lambda *a, **kw: False)
    spec = dict(freeze=frozen, cohort=1, protocol="silo", cell="wh-base")
    first = runner.run_job(spec)
    assert first["next_action"] == "resubmit-isolation" and first["completed_blocks"] == 0
    second = runner.run_job(spec | {"attempt_history": [first]})
    assert second["next_action"] == "retry-exhausted"
    with pytest.raises(ValueError, match="retry limit"):
        runner.run_job(spec | {"attempt_history": [first, second]})


def test_verification_mapping():
    base = dict(completed=True, serializable=True, anomalies=0,
                witness_ok=True, certified=True)
    assert runner.verification_status(**base) == "certified"
    for change in (dict(completed=False), dict(witness_ok=False),
                   dict(certified=False), dict(serializable=None)):
        assert runner.verification_status(**(base | change)) == "未確定"
    assert runner.verification_status(**(base | {"anomalies": 1})) == "失格"
    assert runner.verification_status(**(base | {"serializable": False})) == "失格"


def test_verification_mapping_with_real_verifier_fixtures():
    fixtures = Path(__file__).parent / "fixtures"
    red = verify_trace_dir(str(fixtures / "r1_write_skew"), max_report=0)
    assert runner.verification_status(completed=True, serializable=red.serializable,
           anomalies=max(len(red.anomalies), red.total_cycles), witness_ok=True,
           certified=red.certified) == "失格"
    green_graph = verify_trace_dir(str(fixtures / "g1_serial"))
    assert green_graph.serializable and not green_graph.certified
    assert runner.verification_status(completed=True, serializable=green_graph.serializable,
           anomalies=max(len(green_graph.anomalies), green_graph.total_cycles),
           witness_ok=True, certified=green_graph.certified) == "未確定"


def test_tpcc_parser_from_result_cc_shape():
    stdout = "  Transaction type: Payment\n    commits: 8\n    aborts: 2\n  Transaction type: NewOrder\n    commits: 7\n    aborts: 0\n"
    assert runner.parse_tpcc_counts(stdout) == {"Payment": {"commits": 8, "aborts": 2},
                                                "NewOrder": {"commits": 7, "aborts": 0}}
    assert runner.parse_tpcc_counts(stdout.replace("    aborts: 2\n", "")) is None
    assert runner.parse_tpcc_counts(stdout + "  Transaction type: Payment\n") is None


def test_run_job_anchor_uses_real_run_once_with_subprocess_seam(tmp_path, monkeypatch):
    binary = tmp_path / "binary"
    binary.write_bytes(b"fake")
    digest = hashlib.sha256(binary.read_bytes()).hexdigest()
    frozen = _freeze()
    for pair in frozen["binaries"].values():
        pair.update(perf_path=str(binary), perf_sha256=digest)
    calls = []
    def subprocess_runner(cmd, **kwargs):
        calls.append(cmd)
        return subprocess.CompletedProcess(cmd, 0, stdout="throughput[tps]:\t100\n", stderr="")
    monkeypatch.setattr(runner, "_probe", lambda *a, **kw: True)
    result = runner.run_job(dict(freeze=frozen, cohort=1, protocol="silo", cell="wh-base"),
                            subprocess_runner=subprocess_runner)
    assert result["completed_blocks"] == 32
    assert len(calls) == 1 + 32 * 4
    assert all("perf" not in str(cmd[0]) for cmd in calls)
    assert result["blocks"][0]["runs"]["K"]["tps"] == 100


def test_verify_tpcc_anchor_is_indeterminate():
    frozen = {"workload": "tpcc", "stage": "s1", "sha256": "h",
              "jobs": [{"cohort": 1, "protocol": "silo", "cell": "s1-H-base",
                        "R0": "R0", "identities": ["R0", "K"]}]}
    result = runner.verify_candidate(dict(freeze=frozen, protocol="silo",
                                          cell="s1-H-base", identity="K"))
    assert result["status"] == "未確定" and result["reason"] == "認定経路なし"
    repeated = runner.verify_candidate(dict(freeze=frozen, protocol="silo",
        cell="s1-H-base", identity="K", attempt_history=[result]))
    assert repeated["reason"] == "reverification-not-admitted"
    exhausted = runner.verify_candidate(dict(freeze=frozen, protocol="silo",
        cell="s1-H-base", identity="K", attempt_history=[result, repeated]))
    assert exhausted["reason"] == "reverification-limit"


def test_freeze_cli_create_only(tmp_path):
    source, target = tmp_path / "input.json", tmp_path / "freeze.json"
    source.write_text(json.dumps(_record()))
    assert runner.main(["freeze", str(source), str(target)]) == 0
    assert json.loads(target.read_text())["sha256"] == _freeze()["sha256"]
    with pytest.raises(SystemExit) as exc:
        runner.main(["freeze", str(source), str(target)])
    assert exc.value.code != 0


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-q"]))
