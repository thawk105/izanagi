from __future__ import annotations

import contextlib
import types
from pathlib import Path

import pytest

from orchestrator.campaign import condition_meaning_gate as gate
from tools.pegasus.probes import t2228_driver_gate_liveness_probe as probe


DRIVER_ID = "orchestrator/campaign/backoff_repro.py"


def _issue_production_family(source: Path, *, driver_id: str) -> object:
    source.mkdir()
    request = gate.make_define_request(
        driver_id=driver_id,
        macro="BACKOFF_FIXED",
        requested_value=-1,
        default_value=None,
        stock_comparison=True,
    )
    captured = gate.capture_define_inputs(source)
    supply = gate.evaluate_define_supply_effectuation(
        captured,
        request=request,
        cxx="unused-cxx",
        cmake="unused-cmake",
    )
    meaning = gate.evaluate_define_runtime_meaning(
        captured,
        request=request,
        declaration=None,
        cxx="unused-cxx",
    )
    return gate.require_condition_gate_family(
        [supply], [meaning], use_class="raw-measurement",
    )


def _production_observation(
    source: Path, *, driver_id: str = DRIVER_ID,
) -> probe._GateObservation:
    value, observed, completed, exception = probe._measure_call(
        gate,
        driver_id=driver_id,
        call=lambda: _issue_production_family(source, driver_id=driver_id),
    )
    assert completed is True
    assert exception is None
    assert value is observed.admissions[0]
    assert len(observed.requests) == 1
    assert len(observed.supply_records) == 1
    assert len(observed.meaning_records) == 1
    assert len(observed.admissions) == 1
    return observed


def test_m1_exception_before_records_keeps_initial_result_false() -> None:
    def fail_before_gate() -> None:
        raise RuntimeError("pre-gate failure")

    result = probe._base_result("repro")
    _value, observed, completed, exception = probe._measure_call(
        gate,
        driver_id=DRIVER_ID,
        call=fail_before_gate,
    )
    if completed and probe._gate_success(gate, observed):
        result["ok"] = True
    result["exception"] = exception
    probe._finish_result(result)

    assert completed is False
    assert observed == probe._GateObservation()
    assert result["ok"] is False
    assert result["rc"] == 1


def test_m2_production_integrity_rejects_tampered_issued_record(
    tmp_path: Path,
) -> None:
    observed = _production_observation(tmp_path / "family")
    admission = probe._validated_family_admission(
        gate,
        observed.supply_records,
        observed.meaning_records,
        observed.admissions,
    )
    assert admission is observed.admissions[0]

    supply = observed.supply_records[0]
    object.__setattr__(supply, "record_digest", "0" * 64)

    assert probe._validated_family_admission(
        gate,
        observed.supply_records,
        observed.meaning_records,
        observed.admissions,
    ) is None


def test_m3_production_admission_is_bound_to_exact_record_ids(
    tmp_path: Path,
) -> None:
    observed = _production_observation(tmp_path / "family-a")
    unrelated = _production_observation(
        tmp_path / "family-b",
        driver_id="orchestrator/campaign/other-driver.py",
    )
    assert observed.admissions[0].admitted is False
    assert probe._gate_success(gate, observed) is False

    assert probe._validated_family_admission(
        gate,
        observed.supply_records,
        observed.meaning_records,
        unrelated.admissions,
    ) is None


def test_m4_runtime_error_without_attribute_keeps_reason_code_null() -> None:
    error = RuntimeError("configure-timeout: text is not a reason attribute")

    document = probe._exception_document(error)

    assert document["type"] == "RuntimeError"
    assert document["message"] == str(error)
    assert document["reason_code"] is None
    assert document["cause"] is None
    assert document["context"] is None


@pytest.mark.parametrize(
    "stop",
    [KeyboardInterrupt(), SystemExit(9)],
    ids=["keyboard-interrupt", "system-exit"],
)
def test_measure_call_propagates_process_control_exceptions(
    stop: BaseException,
) -> None:
    def interrupt() -> None:
        raise stop

    with pytest.raises(type(stop)):
        probe._measure_call(gate, driver_id=DRIVER_ID, call=interrupt)


def test_network_observation_propagates_process_control_exception(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def interrupt(*_args: object, **_kwargs: object) -> object:
        raise KeyboardInterrupt

    monkeypatch.setattr(probe.socket, "getaddrinfo", interrupt)
    with pytest.raises(KeyboardInterrupt):
        probe._network_observation()


def test_current_pin_control_requires_production_assert_pinned_clean_origin() -> None:
    def assert_pinned_clean() -> None:
        raise RuntimeError("controlled pin mismatch")

    _value, observed, completed, exception = probe._measure_call(
        gate, driver_id=DRIVER_ID, call=assert_pinned_clean,
    )
    assert exception is not None
    assert any(
        row["function"] == "assert_pinned_clean"
        for row in exception["traceback"]
    )
    production_exception = {
        **exception,
        "traceback": [{
            "module": "orchestrator.campaign.patchharness",
            "function": "assert_pinned_clean",
        }],
    }
    assert probe._current_pin_control_success(
        observed,
        completed=completed,
        exception=production_exception,
        current_head="a" * 40,
        required_head="b" * 40,
    ) is True
    assert probe._current_pin_control_success(
        observed,
        completed=completed,
        exception=production_exception,
        current_head="a" * 40,
        required_head="a" * 40,
    ) is False


def test_m5_run_sweep_rejects_aborted_summary_with_observed_production_records(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    summary = types.SimpleNamespace(
        campaign_id="campaign", committed=2, aborted=0, evaluated=2, skipped=0,
    )
    issue_count = 0

    def run_workload(
        workload_name: str,
        workload: dict,
        *,
        screening_enabled: bool,
        screening_fixed_us: int,
    ) -> object:
        nonlocal issue_count
        assert workload_name == "write-heavy"
        assert workload == {"fixture": "production-issued"}
        assert screening_enabled is True
        assert screening_fixed_us == 2
        issue_count += 1
        _issue_production_family(
            tmp_path / f"family-{issue_count}",
            driver_id=probe.EXPECTED_DRIVER_IDS["sweep"],
        )
        return summary

    bundle = types.SimpleNamespace(
        gate=gate,
        buildcache=types.SimpleNamespace(
            _ccbench_dir=lambda: str(tmp_path),
        ),
        sweep=types.SimpleNamespace(
            WORKLOADS=(("write-heavy", {"fixture": "production-issued"}),),
            run_workload=run_workload,
        ),
    )
    monkeypatch.setattr(
        probe,
        "_driver_metadata",
        lambda _bundle, *, common, output_root: ({}, "unused-cxx"),
    )
    monkeypatch.setattr(
        probe, "_ccbench_head_and_clean", lambda _root, _expected: "f" * 40,
    )

    def accept_production_records(
        gate_module: types.ModuleType,
        observed: probe._GateObservation,
    ) -> bool:
        return probe._validated_family_admission(
            gate_module,
            observed.supply_records,
            observed.meaning_records,
            observed.admissions,
        ) is observed.admissions[0]

    monkeypatch.setattr(probe, "_gate_success", accept_production_records)

    green = probe._run_sweep(bundle, common={}, output_root=tmp_path / "green")
    assert green["ok"] is True
    assert green["rc"] == 0

    summary.aborted = 1
    aborted = probe._run_sweep(bundle, common={}, output_root=tmp_path / "aborted")
    assert aborted["ok"] is False
    assert aborted["rc"] == 1
    assert aborted["summary"]["aborted"] == 1


def test_m6_atomic_writer_refuses_existing_evidence(tmp_path: Path) -> None:
    destination = tmp_path / "repro.json"
    destination.write_text("existing\n", encoding="utf-8")

    with pytest.raises(FileExistsError):
        probe._write_atomic_create_only(destination, {"ok": True})

    assert destination.read_text(encoding="utf-8") == "existing\n"
    assert list(tmp_path.iterdir()) == [destination]


def _stub_main_execution(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    calls: list[str],
) -> list[str]:
    roots = [tmp_path / name for name in ("s1", "repro", "sweep")]
    for root in roots:
        root.mkdir()
    evidence = tmp_path / "evidence"
    scratch = tmp_path / "scratch"
    evidence.mkdir()
    scratch.mkdir()

    monkeypatch.setattr(
        probe, "_validate_repo_root", lambda root, _expected: root,
    )
    monkeypatch.setattr(
        probe,
        "_canonical_external_directory",
        lambda value, **_kwargs: value,
    )
    monkeypatch.setattr(probe, "_network_observation", lambda: {})
    monkeypatch.setattr(probe, "_scratch_capacity", lambda _path: {})
    monkeypatch.setattr(probe, "_load_production", lambda root: object())
    monkeypatch.setattr(
        probe,
        "_driver_execution_context",
        lambda _bundle, _output_root: contextlib.nullcontext(),
    )

    def runner(driver: str):
        def run(
            _bundle: object,
            *,
            common: dict,
            output_root: Path,
        ) -> dict:
            calls.append(driver)
            result = probe._base_result(driver)
            result["metadata"] = {
                "run_binding": common["run_binding"],
                "output_root": str(output_root),
            }
            result["ok"] = True
            return probe._finish_result(result)

        return run

    monkeypatch.setattr(probe, "_run_s1", runner("s1"))
    monkeypatch.setattr(probe, "_run_repro", runner("repro"))
    monkeypatch.setattr(probe, "_run_sweep", runner("sweep"))
    return [
        "--s1-repo", str(roots[0]),
        "--repro-repo", str(roots[1]),
        "--sweep-repo", str(roots[2]),
        "--expected-repo-head", "a" * 40,
        "--evidence-dir", str(evidence),
        "--scratch-output-root", str(scratch),
        "--pbs-job-id", "1234.pegasus",
    ]


def test_all_driver_payloads_share_one_process_run_binding(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[str] = []
    argv = _stub_main_execution(tmp_path, monkeypatch, calls)
    published: list[dict] = []
    monkeypatch.setattr(
        probe,
        "_write_atomic_create_only",
        lambda _path, payload: published.append(dict(payload)),
    )

    assert probe.main(argv) == 0
    assert calls == list(probe.DRIVER_ORDER)
    assert len(published) == 3
    bindings = [payload["run_binding"] for payload in published]
    assert bindings[0] == bindings[1] == bindings[2]
    assert bindings[0]["pbs_job_id"] == "1234.pegasus"
    assert all(
        payload["metadata"]["run_binding"] == bindings[0]
        for payload in published
    )


def test_publish_failure_stops_before_next_driver(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[str] = []
    argv = _stub_main_execution(tmp_path, monkeypatch, calls)

    def fail_publish(_path: Path, _payload: dict) -> None:
        raise FileExistsError("existing evidence")

    monkeypatch.setattr(probe, "_write_atomic_create_only", fail_publish)

    assert probe.main(argv) == 4
    assert calls == ["s1"]


def test_pbs_closes_git_environment_and_rejects_repo_local_logs() -> None:
    pbs = Path(probe.__file__).with_suffix(".pbs").read_text(encoding="utf-8")
    first_git = pbs.index('REPO_HEAD=$(git')
    pre_git = pbs[:first_git]
    for variable in (
        "GIT_DIR",
        "GIT_WORK_TREE",
        "GIT_INDEX_FILE",
        "GIT_COMMON_DIR",
        "GIT_OBJECT_DIRECTORY",
        "GIT_ALTERNATE_OBJECT_DIRECTORIES",
        "GIT_CEILING_DIRECTORIES",
    ):
        assert variable in pre_git
    assert pbs.index("validate_external_pbs_log 1 stdout") < first_git
    assert pbs.index("validate_external_pbs_log 2 stderr") < first_git
    assert '"/proc/$$/fd/$descriptor"' in pbs
    assert '"$REPO_ROOT"|"$REPO_ROOT/"*' in pbs
    assert '--pbs-job-id "$PBS_JOBID"' in pbs


def _synthetic_freeze_with_one_inert_cell() -> dict:
    cell_ids = [f"cell-{index:02d}" for index in range(18)]
    cells = {}
    for index, cell_id in enumerate(cell_ids):
        cells[cell_id] = {
            "workload": "write-heavy",
            "configuration": "stock_common",
            "variant": {
                "flags": (
                    {"BACKOFF_FIXED": -1}
                    if index == 0
                    else {"WAL": 0}
                ),
            },
        }
    lap = list(cell_ids)
    return {
        "cells": cells,
        "schedule": {
            "floor": [lap],
            "test_block_1": [lap],
            "test_block_2": [lap],
        },
    }


def test_m7_reachability_counts_inert_request_from_freeze_data() -> None:
    reachability = probe._enumerate_s1_reachability(
        _synthetic_freeze_with_one_inert_cell(),
        __import__(
            "orchestrator.campaign.s1_direct_comparison",
            fromlist=["schedule_for_role"],
        ),
        gate,
    )

    assert reachability["cell_count"] == 18
    assert reachability["inert_request_count"] == 1
    assert probe._s1_reachability_success(reachability) is True


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__]))
