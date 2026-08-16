# -*- coding: utf-8 -*-
"""s8b_floor_contract の leaf 性・共有 API・fail-closed 契約。"""
from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from copy import deepcopy
from pathlib import Path

import pytest


ORCHESTRATOR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ORCHESTRATOR.parent))

from orchestrator.campaign import s8b_floor_campaign  # noqa: E402
from orchestrator.campaign import s8b_floor_contract  # noqa: E402


_CONTRACT_SHA256 = "a" * 64
_STOCK = "stock"


def _protocol() -> dict:
    return {
        "schema": s8b_floor_contract.PROTOCOL_SCHEMA,
        "formula": s8b_floor_contract.FORMULA_ID,
        "env_tag": "fixture-env",
        "contract_sha256": _CONTRACT_SHA256,
        "ccbench_pin": "0" * 40,
        "freeze": {"path": "output/fixture-freeze.json", "sha256": "b" * 64},
        "stock_configuration": _STOCK,
        "n_sessions": 8,
        "reps": 5,
        "master_seed": "fixture-seed",
        "schedule_algorithm": s8b_floor_contract.SCHEDULE_ALGORITHM,
        "extime_s": 5,
        "wired_min_rel_floor": 0.05,
        "retry_slots_per_cell": 2,
        "session_cv_max": "0.10",
        "cell_cv_max": "0.15",
        "scale_adequacy_rel_tolerance": "0.10",
        "allowed_excluded_reasons": list(s8b_floor_contract._APPROVED_REASONS),
    }


def _lookup_contract_sha256(env_tag: str) -> str:
    if env_tag != "fixture-env":
        raise s8b_floor_contract.FloorContractError(
            f"protocol.env_tag が env 契約に未登録: {env_tag!r}"
        )
    return _CONTRACT_SHA256


def _freeze() -> dict:
    entries = {
        _STOCK: {"binding": "s"},
        "sort_best": {"binding": "sort"},
        "variant": {"binding": "v"},
    }
    return {
        "holdouts": {
            "holdout-a": {
                "records": 100,
                "threads": 2,
                "ycsb": {"field-a": "value-a"},
                "variant_binding": {"entries": deepcopy(entries)},
            },
            "holdout-b": {
                "records": 200,
                "threads": 4,
                "ycsb": {"field-b": "value-b"},
                "variant_binding": {"entries": deepcopy(entries)},
            },
        },
    }


def test_leaf_import_loads_no_other_campaign_module():
    script = f"""
import json
import sys
sys.path.insert(0, {str(ORCHESTRATOR.parent)!r})
import orchestrator.campaign.s8b_floor_contract
print(json.dumps(sorted(
    name for name in sys.modules
    if name.startswith('orchestrator.campaign.')
    and name != 'orchestrator.campaign.s8b_floor_contract'
)))
"""
    completed = subprocess.run(
        [sys.executable, "-c", script],
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    assert json.loads(completed.stdout) == [
        "orchestrator.campaign.s8b_experiment_numbers"
    ]


def test_floor_campaign_directly_reexports_shared_leaf_objects():
    for name in (
        "PROTOCOL_SCHEMA",
        "FREEZE_SCHEMA",
        "SCHEDULE_ALGORITHM",
        "RESULT_SCHEMA",
        "MANIFEST_SCHEMA",
        "JOURNAL_SCHEMA",
        "canonical_protocol_sha256",
        "project_protocol_for_floor_artifact",
        "build_portable_run_cmd",
        "derive_expected_cells",
        "_round_seed",
    ):
        assert getattr(s8b_floor_campaign, name) is getattr(s8b_floor_contract, name)

    assert s8b_floor_contract.RESULT_SCHEMA == "s8b-floor-result/v4"
    assert s8b_floor_contract.MANIFEST_SCHEMA == "s8b-floor-manifest/v3"
    assert s8b_floor_contract.FLOOR_HOLDOUT_ADMISSION_SCHEMA == (
        "s8b-floor-holdout-admission-receipt/v1"
    )


def test_leaf_full_validator_normalizes_18_keys_and_projects_exact_7_scalars():
    normalized = s8b_floor_contract.validate_protocol(
        _protocol(), contract_sha256_lookup=_lookup_contract_sha256,
    )
    assert len(normalized) == 18
    assert normalized["wired_min_rel_floor"] == 0.05

    projection = s8b_floor_contract.project_protocol_for_floor_artifact(normalized)
    assert tuple(projection) == s8b_floor_contract._FLOOR_ARTIFACT_PROTOCOL_KEYS
    assert set(projection) == {
        "formula",
        "n_sessions",
        "reps",
        "stock_configuration",
        "wired_min_rel_floor",
        "session_cv_max",
        "cell_cv_max",
    }
    reference = json.dumps(
        normalized, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False,
    ).encode("utf-8")
    assert s8b_floor_contract.canonical_protocol_sha256(normalized) == hashlib.sha256(
        reference
    ).hexdigest()


def test_leaf_full_validator_rejects_contract_hash_mismatch():
    protocol = _protocol()
    protocol["contract_sha256"] = "c" * 64
    with pytest.raises(s8b_floor_contract.FloorContractError, match="contract_sha256"):
        s8b_floor_contract.validate_protocol(
            protocol, contract_sha256_lookup=_lookup_contract_sha256,
        )


def test_leaf_full_validator_rejects_nonapproved_extime():
    protocol = _protocol()
    protocol["extime_s"] = 3
    with pytest.raises(s8b_floor_contract.FloorContractError, match="extime_s"):
        s8b_floor_contract.validate_protocol(
            protocol, contract_sha256_lookup=_lookup_contract_sha256,
        )

    protocol = _protocol()
    protocol["extime_s"] = 7
    with pytest.raises(s8b_floor_contract.FloorContractError, match="extime_s"):
        s8b_floor_contract.validate_protocol(
            protocol, contract_sha256_lookup=_lookup_contract_sha256,
        )


def test_floor_campaign_translates_floor_contract_error():
    cells = [{"cell_id": "duplicate"}, {"cell_id": "duplicate"}]
    with pytest.raises(s8b_floor_campaign.FloorCampaignError) as exc_info:
        s8b_floor_campaign.build_schedule(
            cells=cells, master_seed="seed", n_sessions=1,
        )
    assert isinstance(exc_info.value.__cause__, s8b_floor_contract.FloorContractError)

    with pytest.raises(s8b_floor_campaign.FloorCampaignError) as protocol_exc:
        s8b_floor_campaign.validate_protocol(_protocol())
    assert isinstance(protocol_exc.value.__cause__, s8b_floor_contract.FloorContractError)


def test_expected_cells_are_derived_from_ratified_freeze_binding():
    expected = s8b_floor_contract.derive_expected_cells(
        _freeze(), stock_configuration=_STOCK,
    )
    assert expected == {
        "holdout-a": ["sort_best", "stock", "variant"],
        "holdout-b": ["sort_best", "stock", "variant"],
    }


def _admission_receipt() -> dict:
    return {
        "schema": s8b_floor_contract.FLOOR_HOLDOUT_ADMISSION_SCHEMA,
        "campaign_run_id": "run-a",
        "run_relpath": "env/fixture/calibration/s8b-floor-pilot/run-a",
        "mode": "pilot",
        "protocol_sha256": "1" * 64,
        "freeze_sha256": "2" * 64,
        "manifest_sha256": "3" * 64,
        "claim_identities": {"holdout-a::sort_best": "4" * 64},
        "admission_row_count": 1,
        "attempt_row_count": 0,
        "ledger_projection_sha256": "5" * 64,
    }


def test_holdout_admission_receipt_validator_accepts_only_exact_shape():
    value = _admission_receipt()
    assert s8b_floor_contract.validate_floor_holdout_admission_receipt(value) == value
    for mutation in ("missing", "extra"):
        changed = deepcopy(value)
        if mutation == "missing":
            changed.pop("mode")
        else:
            changed["unexpected"] = True
        with pytest.raises(s8b_floor_contract.FloorContractError, match="exact key"):
            s8b_floor_contract.validate_floor_holdout_admission_receipt(changed)


@pytest.mark.parametrize(
    "run_relpath",
    ["/absolute/run", ".", "a/./b", "a/../b", "a\\b", "a//b", "a/"],
)
def test_holdout_admission_receipt_rejects_noncanonical_run_relpath(run_relpath):
    value = _admission_receipt()
    value["run_relpath"] = run_relpath
    with pytest.raises(s8b_floor_contract.FloorContractError, match="canonical POSIX"):
        s8b_floor_contract.validate_floor_holdout_admission_receipt(value)


def test_holdout_admission_receipt_binds_claim_count():
    value = _admission_receipt()
    value["admission_row_count"] = 0
    with pytest.raises(s8b_floor_contract.FloorContractError, match="件数"):
        s8b_floor_contract.validate_floor_holdout_admission_receipt(value)


def _authorization_schedule() -> list[dict]:
    return [
        {"seq": 0, "round": 1, "cell_id": "cell"},
        {"seq": 1, "round": 1, "cell_id": "cell"},
    ]


def test_canonical_authorization_rejects_attempt_id_transplanted_from_other_seq():
    start = {
        "event": "session-start", "kind": "planned", "seq": 1, "round": 1,
        "cell_id": "cell", "retry_ordinal": None,
        "attempt_id": "cell::seq0", "trigger": None,
    }
    with pytest.raises(s8b_floor_contract.FloorContractError, match="planned"):
        s8b_floor_contract.validate_session_start_authorizations(
            [start], schedule=_authorization_schedule(), retry_slots_per_cell=2,
        )


def test_canonical_authorization_rejects_attempt_id_transplanted_from_retry_ordinal():
    start = {
        "event": "session-start", "kind": "retry", "seq": 2, "round": 1,
        "cell_id": "cell", "retry_ordinal": 2,
        "attempt_id": "cell::retry1", "trigger": "cell::seq0",
    }
    with pytest.raises(s8b_floor_contract.FloorContractError, match="retry"):
        s8b_floor_contract.validate_session_start_authorizations(
            [start], schedule=_authorization_schedule(), retry_slots_per_cell=2,
        )


def test_canonical_authorization_rejects_duplicate_cell_retry_ordinal():
    starts = [
        {
            "event": "session-start", "kind": "retry", "seq": 2 + index,
            "round": 1, "cell_id": "cell", "retry_ordinal": 1,
            "attempt_id": attempt_id, "trigger": "cell::seq0",
        }
        for index, attempt_id in enumerate(("cell::retry1", "cell::retry2"))
    ]
    with pytest.raises(s8b_floor_contract.FloorContractError, match="retry"):
        s8b_floor_contract.validate_session_start_authorizations(
            starts, schedule=_authorization_schedule(), retry_slots_per_cell=2,
        )


def test_result_v4_key_contract_is_mode_conditional_and_exact():
    official = s8b_floor_contract.result_keys_for_mode("official")
    pilot = s8b_floor_contract.result_keys_for_mode("pilot")
    assert pilot == official | {"perf_preflight"}
    assert "unexpected" not in official


def test_enumerate_cells_rejects_freeze_without_sort_best():
    freeze = _freeze()
    for holdout in freeze["holdouts"].values():
        holdout["variant_binding"]["entries"].pop("sort_best")
    with pytest.raises(s8b_floor_contract.FloorContractError, match="sort_best"):
        s8b_floor_contract.enumerate_cells(freeze, stock_configuration=_STOCK)


def test_portable_run_cmd_has_canonical_workload_order_and_exact_prefix():
    workload = {"field-z": "value-z", "field-a": "value-a"}
    argv = s8b_floor_contract.build_portable_run_cmd(
        binary="output/store/hash/bench", workload=workload,
        records=100, threads=2, extime_s=3, clocks_per_us=1800,
        numactl=("numactl", "--interleave=all"),
    )
    reversed_argv = s8b_floor_contract.build_portable_run_cmd(
        binary="output/store/hash/bench",
        workload=dict(reversed(list(workload.items()))),
        records=100, threads=2, extime_s=3, clocks_per_us=1800,
        numactl=("numactl", "--interleave=all"),
    )
    assert argv == reversed_argv
    assert argv[:9] == (
        "numactl", "--interleave=all", "perf", "stat", "-e",
        "LLC-load-misses,LLC-loads,instructions,cycles", "--",
        "output/store/hash/bench", "-thread_num=2",
    )
    assert argv[-2:] == ("-field-a=value-a", "-field-z=value-z")


def test_portable_run_cmd_without_perf_has_one_exact_direct_shape():
    argv = s8b_floor_contract.build_portable_run_cmd(
        binary="output/store/hash/bench", workload={"field-z": "value-z"},
        records=100, threads=2, extime_s=3, clocks_per_us=1800,
        numactl=("numactl", "--interleave=all"), use_perf=False,
    )
    assert argv == (
        "numactl", "--interleave=all", "output/store/hash/bench",
        "-thread_num=2", "-ycsb_tuple_num=100", "-extime=3",
        "-clocks_per_us=1800", "-field-z=value-z",
    )


@pytest.mark.parametrize("value", [0, 1, None, "false"])
def test_portable_run_cmd_rejects_non_bool_use_perf(value):
    with pytest.raises(s8b_floor_contract.FloorContractError, match="use_perf"):
        s8b_floor_contract.build_portable_run_cmd(
            binary="output/store/hash/bench", workload={"field": "value"},
            records=1, threads=1, extime_s=1, clocks_per_us=1,
            numactl=(), use_perf=value,
        )


@pytest.mark.parametrize("binary", ["/runtime/bench", "output/../bench", "output\\bench"])
def test_portable_run_cmd_rejects_nonportable_binary(binary):
    with pytest.raises(s8b_floor_contract.FloorContractError, match="portable"):
        s8b_floor_contract.build_portable_run_cmd(
            binary=binary, workload={"field": "value"}, records=1, threads=1,
            extime_s=1, clocks_per_us=1, numactl=(),
        )


@pytest.mark.parametrize("mutation", ["missing-stock", "configuration-drift"])
def test_expected_cells_reject_invalid_ratified_freeze_binding(mutation):
    freeze = _freeze()
    entries = freeze["holdouts"]["holdout-b"]["variant_binding"]["entries"]
    if mutation == "missing-stock":
        del entries[_STOCK]
    else:
        entries["unexpected-variant"] = entries.pop("variant")

    with pytest.raises(s8b_floor_contract.FloorContractError):
        s8b_floor_contract.derive_expected_cells(
            freeze, stock_configuration=_STOCK,
        )


if __name__ == "__main__":
    sys.exit(pytest.main([__file__]))
