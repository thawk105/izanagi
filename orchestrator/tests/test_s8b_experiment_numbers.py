# -*- coding: utf-8 -*-
"""S8b 公式実験数値 leaf の golden・leaf 性・検証器配線を固定する。"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest


ORCHESTRATOR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ORCHESTRATOR.parent))

from orchestrator.campaign import s8b_experiment_numbers  # noqa: E402
from orchestrator.campaign import s8b_floor_contract  # noqa: E402
from orchestrator.campaign import s8b_oracle_manifest  # noqa: E402


_CONTRACT_SHA256 = "a" * 64


def _protocol(*, extime_s: int, reps: int = 5) -> dict:
    return {
        "schema": s8b_floor_contract.PROTOCOL_SCHEMA,
        "formula": s8b_floor_contract.FORMULA_ID,
        "env_tag": "fixture-env",
        "contract_sha256": _CONTRACT_SHA256,
        "ccbench_pin": "0" * 40,
        "freeze": {"path": "output/fixture-freeze.json", "sha256": "b" * 64},
        "stock_configuration": "stock",
        "n_sessions": 8,
        "reps": reps,
        "master_seed": "fixture-seed",
        "schedule_algorithm": s8b_floor_contract.SCHEDULE_ALGORITHM,
        "extime_s": extime_s,
        "wired_min_rel_floor": 0.05,
        "retry_slots_per_cell": 2,
        "session_cv_max": "0.10",
        "cell_cv_max": "0.15",
        "scale_adequacy_rel_tolerance": "0.10",
        "allowed_excluded_reasons": list(s8b_floor_contract._APPROVED_REASONS),
    }


def _run_contract(*, extime: int = 5, reps: int = 5) -> dict:
    return {
        "ccbench_pin": "pin",
        "env_tag": "fixture-env",
        "clocks": 1800,
        "reps": reps,
        "extime": extime,
        "verify": "legacy+s2",
        "screening": "off",
        "bench_max_rounds": 1,
        "contract_sha256": "0" * 64,
    }


def test_approved_numbers_match_independent_golden_literals():
    assert s8b_experiment_numbers.APPROVED_EXTIME_S == 5
    assert s8b_experiment_numbers.APPROVED_REPS == 5


def test_leaf_import_loads_no_other_campaign_module():
    script = f"""
import json
import sys
sys.path.insert(0, {str(ORCHESTRATOR.parent)!r})
import orchestrator.campaign.s8b_experiment_numbers
print(json.dumps(sorted(
    name for name in sys.modules
    if name.startswith('orchestrator.campaign.')
    and name != 'orchestrator.campaign.s8b_experiment_numbers'
)))
"""
    completed = subprocess.run(
        [sys.executable, "-c", script],
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    assert json.loads(completed.stdout) == []


def test_approved_reexports_read_pins_from_leaf_on_import():
    script = f"""
import json
import sys
sys.path.insert(0, {str(ORCHESTRATOR.parent)!r})
from orchestrator.campaign import s8b_experiment_numbers
s8b_experiment_numbers.APPROVED_REPS = 7
s8b_experiment_numbers.APPROVED_EXTIME_S = 7
from orchestrator.campaign import s8b_approved
print(json.dumps({{
    "reps": s8b_approved.APPROVED_REPS,
    "extime_s": s8b_approved.APPROVED_EXTIME_S,
}}))
"""
    completed = subprocess.run(
        [sys.executable, "-c", script],
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    assert json.loads(completed.stdout) == {"reps": 7, "extime_s": 7}


def test_floor_validator_reads_extime_pin_from_leaf(monkeypatch):
    monkeypatch.setattr(s8b_experiment_numbers, "APPROVED_EXTIME_S", 7)
    accepted = s8b_floor_contract.validate_protocol(
        _protocol(extime_s=7), contract_sha256_lookup=lambda _env: _CONTRACT_SHA256,
    )
    assert accepted["extime_s"] == 7
    with pytest.raises(s8b_floor_contract.FloorContractError, match="extime_s"):
        s8b_floor_contract.validate_protocol(
            _protocol(extime_s=5), contract_sha256_lookup=lambda _env: _CONTRACT_SHA256,
        )


def test_floor_validator_reads_reps_pin_from_leaf(monkeypatch):
    monkeypatch.setattr(s8b_experiment_numbers, "APPROVED_REPS", 7)
    accepted = s8b_floor_contract.validate_protocol(
        _protocol(extime_s=5, reps=7),
        contract_sha256_lookup=lambda _env: _CONTRACT_SHA256,
    )
    assert accepted["reps"] == 7
    with pytest.raises(s8b_floor_contract.FloorContractError, match="reps"):
        s8b_floor_contract.validate_protocol(
            _protocol(extime_s=5, reps=5),
            contract_sha256_lookup=lambda _env: _CONTRACT_SHA256,
        )


def test_oracle_validator_reads_extime_pin_from_leaf(monkeypatch):
    monkeypatch.setattr(s8b_experiment_numbers, "APPROVED_EXTIME_S", 7)
    assert s8b_oracle_manifest._validate_run_contract(
        _run_contract(extime=7)
    )["extime"] == 7
    with pytest.raises(s8b_oracle_manifest.ManifestError, match="extime"):
        s8b_oracle_manifest._validate_run_contract(_run_contract(extime=5))


def test_oracle_validator_reads_reps_pin_from_leaf(monkeypatch):
    monkeypatch.setattr(s8b_experiment_numbers, "APPROVED_REPS", 7)
    assert s8b_oracle_manifest._validate_run_contract(
        _run_contract(reps=7)
    )["reps"] == 7
    with pytest.raises(s8b_oracle_manifest.ManifestError, match="reps"):
        s8b_oracle_manifest._validate_run_contract(_run_contract(reps=5))


if __name__ == "__main__":
    sys.exit(pytest.main([__file__]))
