# -*- coding: utf-8 -*-
from __future__ import annotations

from concurrent.futures import ProcessPoolExecutor
import hashlib
import json
from pathlib import Path
import subprocess

import pytest

from orchestrator.campaign import s8b_floor_campaign
from orchestrator.campaign import s8b_floor_contract
from orchestrator.campaign import s8b_holdout_admission as admission
from orchestrator.holdout_observation import assert_issued_holdout_observation


_CONFIGURATIONS = (
    "backoff_fixed_best", "ident_all", "p2_2_flag_opt",
    "sort_best", "stock_common", "system_gate",
)


def _canonical(value: object) -> bytes:
    return json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":"),
    ).encode("utf-8")


def _fixture_documents(master_seed: str = "seed-a") -> tuple[dict, dict]:
    holdouts = {}
    for key, candidate, ratio in (("rr80", "H1", "80"), ("rr20", "H2", "20")):
        holdouts[key] = {
            "candidate_id": candidate,
            "records": 1_000_000,
            "threads": 48,
            "ycsb": {
                "ycsb_zipf_skew": "0.9", "ycsb_rratio": ratio,
                "ycsb_rmw": "0",
            },
            "variant_binding": {
                "entries": {
                    configuration: {
                        "holdout_id": key,
                        "flags": {"BACK_OFF": 0},
                        "label": f"fixture-{key}-{configuration}",
                    }
                    for configuration in _CONFIGURATIONS
                },
            },
        }
    freeze = {"schema_version": "holdout-freeze/v1", "holdouts": holdouts}
    freeze_sha256 = hashlib.sha256(_canonical(freeze)).hexdigest()
    protocol = {
        "ccbench_pin": "1" * 40,
        "env_tag": "fixture-env",
        "freeze": {
            "path": "output/s8b-freeze/holdout_freeze.json",
            "sha256": freeze_sha256,
        },
        "master_seed": master_seed,
        "n_sessions": 8,
        "retry_slots_per_cell": 2,
        "stock_configuration": "stock_common",
    }
    return protocol, freeze


def _git(root: Path, *args: str) -> str:
    return subprocess.run(
        ["git", "-C", str(root), *args], check=True,
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
    ).stdout.strip()


def _write_fixed_documents(root: Path, protocol: dict, freeze: dict) -> None:
    fixed = root / "output" / "s8b-freeze"
    fixed.mkdir(parents=True, exist_ok=True)
    (fixed / "floor_protocol.json").write_bytes(_canonical(protocol))
    (fixed / "holdout_freeze.json").write_bytes(_canonical(freeze))


def _init_repo(tmp_path: Path, *, master_seed: str = "seed-a") -> tuple[Path, dict, dict]:
    root = tmp_path / "repo"
    root.mkdir()
    _git(root, "init")
    protocol, freeze = _fixture_documents(master_seed)
    _write_fixed_documents(root, protocol, freeze)
    _git(root, "add", "output/s8b-freeze")
    _git(root, "-c", "user.name=fixture", "-c", "user.email=f@example.invalid",
         "commit", "-m", "fixture authority")
    return root, protocol, freeze


def _cells_and_schedule(protocol: dict, freeze: dict) -> tuple[list[dict], list[dict]]:
    contract_cells = s8b_floor_contract.enumerate_cells(
        freeze, stock_configuration=protocol["stock_configuration"],
    )
    schedule = s8b_floor_contract.build_schedule(
        cells=contract_cells, master_seed=protocol["master_seed"],
        n_sessions=protocol["n_sessions"],
    )
    cells = [
        {
            "cell_id": cell["cell_id"],
            "freeze_holdout_key": cell["holdout_id"],
            "configuration_id": cell["configuration_id"],
            "records": cell["records"],
            "threads": cell["threads"],
            "workload": cell["workload"],
        }
        for cell in contract_cells
    ]
    return cells, schedule


def _reserve(
        root: Path, protocol: dict, freeze: dict, *, run_id: str,
        resume: bool = False, journal_exists: bool = False,
        measurement_started: bool = False):
    cells, schedule = _cells_and_schedule(protocol, freeze)
    return admission.reserve_floor_holdout_observations(
        repo_root=root, protocol=protocol,
        verified_freeze_document=freeze,
        freeze_sha256=protocol["freeze"]["sha256"],
        cells=cells, schedule=schedule, campaign_run_id=run_id,
        run_relpath=f"env/fixture-env/calibration/s8b-floor-pilot/{run_id}",
        mode="pilot", resume=resume, journal_exists=journal_exists,
        measurement_started=measurement_started,
    )


def _parallel_reserve(args: tuple[str, dict, dict, str]) -> str:
    root_text, protocol, freeze, run_id = args
    try:
        _reserve(Path(root_text), protocol, freeze, run_id=run_id)
    except admission.HoldoutAdmissionError:
        return "refused"
    return "admitted"


def test_shared_root_is_identical_across_two_worktrees_and_provisions_parents(tmp_path):
    root, _protocol, _freeze = _init_repo(tmp_path)
    linked = tmp_path / "linked"
    _git(root, "worktree", "add", "--detach", str(linked), "HEAD")

    first = admission.provision_shared_admission_root(root)
    second = admission.provision_shared_admission_root(linked)

    assert first == second
    assert first.is_dir()
    assert (first / "claims").is_dir()
    assert (first / "consumed").is_dir()
    assert (first / "ledger.lock").is_file()


def test_two_worktrees_parallel_fresh_runs_cannot_both_claim_the_same_keys(tmp_path):
    root, protocol, freeze = _init_repo(tmp_path)
    linked = tmp_path / "linked"
    _git(root, "worktree", "add", "--detach", str(linked), "HEAD")
    args = [
        (str(root), protocol, freeze, "run-a"),
        (str(linked), protocol, freeze, "run-b"),
    ]
    with ProcessPoolExecutor(max_workers=2) as executor:
        outcomes = list(executor.map(_parallel_reserve, args))
    assert sorted(outcomes) == ["admitted", "refused"]


def test_admission_rows_use_effect_key_and_issue_frozen_attempt_count(tmp_path):
    root, protocol, freeze = _init_repo(tmp_path)
    cells, _schedule = _cells_and_schedule(protocol, freeze)
    reservation = _reserve(root, protocol, freeze, run_id="run-a")
    admitted = admission.finalize_floor_holdout_admissions(
        reservation, manifest_sha256="a" * 64,
    )

    ledger_path = admission.shared_admission_root(root) / "ledger.jsonl"
    rows = [json.loads(line) for line in ledger_path.read_text().splitlines()]
    assert len(rows) == len(cells) == 12
    assert set(admitted) == {cell["cell_id"] for cell in cells}
    effect_key = {
        "freeze_sha256", "freeze_holdout_key", "configuration_id",
        "ccbench_pin", "env_tag",
    }
    claims = [
        json.loads(path.read_text())
        for path in (admission.shared_admission_root(root) / "claims").iterdir()
    ]
    assert len(claims) == 12
    assert all(set(claim["key"]) == effect_key for claim in claims)
    for row in rows:
        assert row["attempt_count"] == 10
        assert len(row["attempt_ids"]) == 10
        assert "protocol_sha256" in row
        assert "manifest_sha256" in row
        assert "holdout_id" not in row
        assert effect_key <= row.keys()
    assert "confirm_user_freeze" not in protocol


def test_protocol_master_seed_change_does_not_reset_cell_key(tmp_path):
    root, protocol, freeze = _init_repo(tmp_path)
    _reserve(root, protocol, freeze, run_id="run-a")

    changed, same_freeze = _fixture_documents(master_seed="seed-b")
    _write_fixed_documents(root, changed, same_freeze)
    _git(root, "add", "output/s8b-freeze/floor_protocol.json")
    _git(root, "-c", "user.name=fixture", "-c", "user.email=f@example.invalid",
         "commit", "-m", "change schedule seed")

    with pytest.raises(admission.HoldoutAdmissionError, match="already consumed"):
        _reserve(root, changed, same_freeze, run_id="run-b")


def test_resume_requires_same_manifest_and_rejects_issued_ledger_without_journal(tmp_path):
    root, protocol, freeze = _init_repo(tmp_path)
    first = _reserve(root, protocol, freeze, run_id="run-a")
    admission.finalize_floor_holdout_admissions(first, manifest_sha256="a" * 64)
    ledger = admission.shared_admission_root(root) / "ledger.jsonl"
    before = ledger.read_bytes()

    with pytest.raises(admission.HoldoutAdmissionError, match="journal is absent"):
        _reserve(root, protocol, freeze, run_id="run-a", resume=True)

    resumed = _reserve(
        root, protocol, freeze, run_id="run-a", resume=True, journal_exists=True,
    )
    admission.finalize_floor_holdout_admissions(resumed, manifest_sha256="a" * 64)
    assert ledger.read_bytes() == before

    mismatched = _reserve(
        root, protocol, freeze, run_id="run-a", resume=True, journal_exists=True,
    )
    with pytest.raises(admission.HoldoutAdmissionError, match="same run identity"):
        admission.finalize_floor_holdout_admissions(
            mismatched, manifest_sha256="b" * 64,
        )


@pytest.mark.parametrize("filename", ["floor_protocol.json", "holdout_freeze.json"])
def test_worktree_byte_drift_is_rejected_before_any_cell_claim(tmp_path, filename):
    root, protocol, freeze = _init_repo(tmp_path)
    path = root / "output/s8b-freeze" / filename
    path.write_bytes(path.read_bytes() + b"\n")

    with pytest.raises(admission.HoldoutAdmissionError, match="HEAD and working-tree"):
        _reserve(root, protocol, freeze, run_id="run-a")

    claim_root = admission.shared_admission_root(root) / "claims"
    assert list(claim_root.iterdir()) == []


def _issued_cell(tmp_path: Path):
    root, protocol, freeze = _init_repo(tmp_path)
    cells, schedule = _cells_and_schedule(protocol, freeze)
    reservation = _reserve(root, protocol, freeze, run_id="run-a")
    admitted = admission.finalize_floor_holdout_admissions(
        reservation, manifest_sha256="a" * 64,
    )
    cell = cells[0]
    seq = next(row["seq"] for row in schedule if row["cell_id"] == cell["cell_id"])
    return root, protocol, cell, admitted[cell["cell_id"]], f"{cell['cell_id']}::seq{seq}"


def test_attempt_ticket_is_durably_single_use(tmp_path):
    root, _protocol, _cell, admitted, attempt_id = _issued_cell(tmp_path)
    token = admission.consume_attempt_ticket(admitted, attempt_id=attempt_id)
    assert_issued_holdout_observation(token)
    with pytest.raises(admission.HoldoutAdmissionError, match="already consumed"):
        admission.consume_attempt_ticket(admitted, attempt_id=attempt_id)
    consumed = admission.shared_admission_root(root) / "consumed"
    assert len(list(consumed.iterdir())) == 1


def test_ticket_consumption_precedes_crashing_measure_callback_m5(tmp_path):
    _root, protocol, cell, admitted, attempt_id = _issued_cell(tmp_path)
    floor_cell = dict(cell)
    floor_cell["holdout_id"] = floor_cell.pop("freeze_holdout_key")
    binary = tmp_path / "bench"
    binary.write_bytes(b"bench")
    calls = []

    class Crash(BaseException):
        pass

    def crashing_measure(*args):
        calls.append(args)
        raise Crash

    wrapped = s8b_floor_campaign._wrap_admission_aware_measure(
        crashing_measure,
        admissions={cell["cell_id"]: admitted},
        cell_by_id={cell["cell_id"]: floor_cell},
        binaries={cell["cell_id"]: {"binary": str(binary)}},
        protocol=protocol, freeze_sha256=protocol["freeze"]["sha256"],
        protocol_sha256=hashlib.sha256(_canonical(protocol)).hexdigest(),
        manifest_sha256="a" * 64,
    )
    with pytest.raises(Crash):
        wrapped(
            cell["cell_id"], attempt_id, str(binary), floor_cell["records"],
            floor_cell["threads"], floor_cell["workload"],
        )
    with pytest.raises(s8b_floor_campaign.CampaignAbort, match="already consumed"):
        wrapped(
            cell["cell_id"], attempt_id, str(binary), floor_cell["records"],
            floor_cell["threads"], floor_cell["workload"],
        )
    assert len(calls) == 1


def test_cell_coordinates_are_evidence_checks_not_extra_key_fields(tmp_path):
    _root, protocol, cell, admitted, _attempt_id = _issued_cell(tmp_path)
    changed = dict(cell)
    changed["records"] += 1
    with pytest.raises(admission.HoldoutAdmissionError, match="records"):
        admission.assert_cell_holdout_admission(
            admitted, cell=changed, protocol=protocol,
            freeze_sha256=protocol["freeze"]["sha256"],
            protocol_sha256=hashlib.sha256(_canonical(protocol)).hexdigest(),
            manifest_sha256="a" * 64,
        )
    ledger_row = admission._read_ledger(  # noqa: SLF001 - key-shape boundary test
        admission.shared_admission_root(_root) / "ledger.jsonl"
    )[0]
    key_projection = {
        field: ledger_row[field] for field in (
            "freeze_sha256", "freeze_holdout_key", "configuration_id",
            "ccbench_pin", "env_tag",
        )
    }
    assert "records" not in key_projection
    assert "threads" not in key_projection
    assert "workload" not in key_projection
