# -*- coding: utf-8 -*-
from __future__ import annotations

from concurrent.futures import ProcessPoolExecutor
from contextlib import nullcontext
import hashlib
import inspect
import json
from pathlib import Path
import subprocess
from unittest import mock

import pytest

from orchestrator.campaign import attempt_registry_core
from orchestrator.campaign import s8b_attempt_profile
from orchestrator.campaign import s8b_floor_campaign
from orchestrator.campaign import s8b_floor_contract
from orchestrator.campaign import s8b_floor_stats
from orchestrator.campaign import s8b_holdout_admission as admission
from orchestrator.calibrator import runner as calibrator_runner
from orchestrator.holdout_observation import (
    HoldoutObservationError,
    assert_holdout_observation_admitted,
    assert_issued_holdout_observation,
)
from orchestrator.tests.s8b_floor_evidence_fixture import (
    build_floor_admission_evidence,
    canonical_json_line,
)


_CONFIGURATIONS = (
    "backoff_fixed_best", "ident_all", "p2_2_flag_opt",
    "sort_best", "stock_common", "system_gate",
)
_TEST_RECOVERY_AUTHORITY = ("test-scheduler-authority", "9" * 64)


def _pin_test_recovery_authority(monkeypatch, *extra: tuple[str, str]) -> None:
    monkeypatch.setattr(
        admission, "_FLOOR_RECOVERY_AUTHORITIES",  # noqa: SLF001
        frozenset({_TEST_RECOVERY_AUTHORITY, *extra}),
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
        "reps": 5,
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


def _indexed_protocol_record(
    root: Path, relpath: str = "output/s8b-freeze/floor_protocol.json",
) -> s8b_floor_campaign.IndexedFloorProtocol:
    raw = subprocess.run(
        ["git", "-C", str(root), "show", f"HEAD:{relpath}"], check=True,
        stdout=subprocess.PIPE, stderr=subprocess.PIPE,
    ).stdout
    return s8b_floor_campaign.IndexedFloorProtocol(
        path=relpath,
        document=json.loads(raw),
        raw_bytes=raw,
        sha256=hashlib.sha256(raw).hexdigest(),
        commit_oid=_git(root, "rev-parse", "HEAD"),
    )


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
        resolver_record=None, resolver_side_effect=None,
        use_real_resolver: bool = False, nondefault_seams=None):
    cells, schedule = _cells_and_schedule(protocol, freeze)
    out_root = root / "out"
    run_relpath = (
        f"env/{protocol['env_tag']}/calibration/s8b-floor-pilot/{run_id}"
    )
    run_dir = out_root / run_relpath
    run_dir.mkdir(parents=True, exist_ok=True)
    manifest_path = run_dir / "manifest.json"
    if not manifest_path.exists():
        manifest_path.write_text(json.dumps({
            "schema_version": "s8b-floor-manifest/v3",
            "protocol_sha256": hashlib.sha256(_canonical(protocol)).hexdigest(),
            "freeze_sha256": protocol["freeze"]["sha256"],
            "reps": protocol["reps"],
        }, sort_keys=True) + "\n", encoding="utf-8")
    if journal_exists:
        manifest_sha256 = hashlib.sha256(manifest_path.read_bytes()).hexdigest()
        journal = run_dir / "journal.jsonl"
        if not journal.exists():
            journal.write_text(json.dumps({
                "event": "campaign-start",
                "protocol_sha256": hashlib.sha256(_canonical(protocol)).hexdigest(),
                "freeze_sha256": protocol["freeze"]["sha256"],
                "manifest_sha256": manifest_sha256,
            }, sort_keys=True) + "\n", encoding="utf-8")
    if use_real_resolver:
        resolver_context = nullcontext()
    else:
        if resolver_record is None:
            resolver_record = _indexed_protocol_record(root)
        resolver_context = mock.patch.object(
            s8b_floor_campaign, "resolve_current_floor_protocol",
            return_value=resolver_record, side_effect=resolver_side_effect,
        )
    with resolver_context:
        return admission.reserve_floor_holdout_observations(
            repo_root=root, protocol=protocol,
            verified_freeze_document=freeze,
            freeze_sha256=protocol["freeze"]["sha256"],
            cells=cells, schedule=schedule, campaign_run_id=run_id,
            out_root=out_root, run_dir=run_dir, run_relpath=run_relpath,
            mode="pilot", resume=resume,
            nondefault_seams=(
                [] if nondefault_seams is None else nondefault_seams
            ),
            irreversible_pilot_approved=True,
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
    assert (first / "refreeze-disqualifications").is_dir()
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
    admitted = admission.finalize_floor_holdout_admissions(reservation)

    ledger_path = admission.shared_admission_root(root) / "ledger.jsonl"
    rows = [json.loads(line) for line in ledger_path.read_text().splitlines()]
    assert len(rows) == len(cells) == 12
    assert set(admitted) == {cell["cell_id"] for cell in cells}
    effect_key = {
        "freeze_sha256", "freeze_holdout_key", "configuration_id",
        "ccbench_pin", "env_tag", "observation_role",
    }
    claims = [
        json.loads(path.read_text())
        for path in (admission.shared_admission_root(root) / "claims").iterdir()
    ]
    assert len(claims) == 12
    assert all(set(claim["key"]) == effect_key for claim in claims)
    assert {claim["schema_version"] for claim in claims} == {
        "s8b-holdout-cell-claim/v2"
    }
    assert {claim["entry_kind"] for claim in claims} == {"fresh"}
    assert {tuple(claim["nondefault_seams"]) for claim in claims} == {()}
    for row in rows:
        assert row["attempt_count"] == 10
        assert len(row["attempt_ids"]) == 10
        assert "protocol_sha256" in row
        assert "manifest_sha256" in row
        assert "holdout_id" not in row
        assert effect_key <= row.keys()
        assert row["observation_role"] == (
            admission.OBSERVATION_ROLE_FLOOR_CAMPAIGN
        )
        assert row["irreversible_pilot_approved"] is True
    assert "confirm_user_freeze" not in protocol


def test_observation_role_is_closed_and_separates_two_authorized_producers():
    common = {
        "freeze_sha256": "a" * 64,
        "freeze_holdout_key": "rr80",
        "configuration_id": "stock_common",
        "ccbench_pin": "fixture-pin",
        "env_tag": "fixture-env",
    }
    floor = admission._key_fields(  # noqa: SLF001 - closed-key boundary
        **common,
        observation_role=admission.OBSERVATION_ROLE_FLOOR_CAMPAIGN,
    )
    oracle = admission._key_fields(  # noqa: SLF001 - closed-key boundary
        **common,
        observation_role=admission.OBSERVATION_ROLE_ORACLE_DRIVER,
    )
    n_pilot = admission._key_fields(  # noqa: SLF001 - closed-key boundary
        **common,
        observation_role=admission.OBSERVATION_ROLE_N_PILOT,
    )
    n_pilot_r33 = admission._key_fields(  # noqa: SLF001 - closed-key boundary
        **common,
        observation_role=admission.OBSERVATION_ROLE_N_PILOT_R33,
    )
    assert set(admission._OBSERVATION_ROLES) == {  # noqa: SLF001
        admission.OBSERVATION_ROLE_FLOOR_CAMPAIGN,
        admission.OBSERVATION_ROLE_N_PILOT,
        admission.OBSERVATION_ROLE_ORACLE_DRIVER,
        admission.OBSERVATION_ROLE_N_PILOT_R33,
    }
    assert admission._OBSERVATION_ROLES[  # noqa: SLF001
        admission.OBSERVATION_ROLE_N_PILOT_R33
    ] == {
        "generation_id": "n-pilot-r33",
        "pilot_rounds": 33,
        "allocation_count": 3,
        "cell_count": 12,
        "schedule_row_count": 396,
        "decision_pin": "t1142-n-pilot-r33-admission-authority",
    }
    assert admission._claim_digest(floor) != admission._claim_digest(oracle)  # noqa: SLF001
    assert len({  # noqa: SLF001 - every producer owns a distinct effect key
        admission._claim_digest(floor),
        admission._claim_digest(oracle),
        admission._claim_digest(n_pilot),
        admission._claim_digest(n_pilot_r33),
    }) == 4
    with pytest.raises(admission.HoldoutAdmissionError, match="not recognized"):
        admission._key_fields(  # noqa: SLF001 - unknown role must fail closed
            **common, observation_role="caller_selected_role",
        )


def test_oracle_and_n_pilot_claim_producers_remain_explicitly_v1():
    for producer in (
        admission.reserve_oracle_holdout_observations,
        admission.reserve_n_pilot_holdout_observations,
    ):
        source = inspect.getsource(producer)
        assert '"schema_version": _CLAIM_SCHEMA_V1' in source
        assert '"schema_version": _CLAIM_SCHEMA,' not in source


@pytest.mark.parametrize(
    "seams,match",
    [
        (["not-a-seam"], "unknown names"),
        (["build_fn", "build_fn"], "duplicates"),
        (["probe_fn", "measure_fn"], "canonical order"),
    ],
)
def test_reservation_rejects_invalid_seam_list_before_shared_ledger_write(
    tmp_path, seams, match,
):
    root, protocol, freeze = _init_repo(tmp_path)
    with pytest.raises(admission.HoldoutAdmissionError, match=match):
        _reserve(
            root, protocol, freeze, run_id="invalid-seams",
            nondefault_seams=seams,
        )
    assert not admission.shared_admission_root(root).exists()


def _n_pilot_fixture(protocol: dict, freeze: dict):
    floor_cells, floor_schedule = _cells_and_schedule(protocol, freeze)
    cells = [
        {
            "cell_id": cell["cell_id"],
            "holdout_id": cell["freeze_holdout_key"],
            "configuration_id": cell["configuration_id"],
            "records": cell["records"],
            "threads": cell["threads"],
            "workload": cell["workload"],
        }
        for cell in floor_cells
    ]
    schedule = [
        {
            "seq": row["seq"],
            "pilot_round": row["round"],
            "cell_id": row["cell_id"],
        }
        for row in floor_schedule
    ]
    pilot_protocol = {
        "freeze": {"sha256": protocol["freeze"]["sha256"]},
        "environment": {
            "ccbench_pin": protocol["ccbench_pin"],
            "env_tag": protocol["env_tag"],
        },
        "design": {"reps": protocol["reps"]},
    }
    protocol_sha256 = hashlib.sha256(
        _canonical(pilot_protocol) + b"\n"
    ).hexdigest()
    return pilot_protocol, protocol_sha256, cells, schedule


def _r33_fixture(protocol: dict, freeze: dict):
    floor_cells, _floor_schedule = _cells_and_schedule(protocol, freeze)
    cells = [
        {
            "cell_id": cell["cell_id"],
            "holdout_id": cell["freeze_holdout_key"],
            "configuration_id": cell["configuration_id"],
            "records": cell["records"],
            "threads": cell["threads"],
            "workload": cell["workload"],
        }
        for cell in floor_cells
    ]
    schedule = []
    for pilot_round in range(1, 34):
        for cell in cells:
            schedule.append({
                "seq": len(schedule),
                "pilot_round": pilot_round,
                "cell_id": cell["cell_id"],
            })
    pilot_protocol = {
        "freeze": {
            "path": "output/s8b-freeze/holdout_freeze.json",
            "sha256": protocol["freeze"]["sha256"],
        },
        "environment": {
            "ccbench_pin": protocol["ccbench_pin"],
            "env_tag": protocol["env_tag"],
        },
        "design": {
            "pilot_rounds": 33,
            "allocation_count": 3,
            "allocation_role": "primary-segment",
            "reps": protocol["reps"],
        },
    }
    protocol_sha256 = hashlib.sha256(
        _canonical(pilot_protocol) + b"\n"
    ).hexdigest()
    return pilot_protocol, protocol_sha256, cells, schedule


def _reserve_r33(root: Path, protocol: dict, freeze: dict, *, run_id: str):
    r33_protocol, protocol_sha256, cells, schedule = _r33_fixture(protocol, freeze)
    receipt = admission.reserve_n_pilot_holdout_observations(
        repo_root=root,
        protocol=r33_protocol,
        protocol_sha256=protocol_sha256,
        verified_freeze_document=freeze,
        freeze_sha256=protocol["freeze"]["sha256"],
        cells=cells,
        schedule=schedule,
        campaign_run_id=run_id,
        irreversible_pilot_approved=True,
    )
    return r33_protocol, protocol_sha256, cells, schedule, receipt


def test_n_pilot_requires_exact_irreversible_approval_before_claim(tmp_path):
    root, floor_protocol, freeze = _init_repo(tmp_path)
    protocol, protocol_sha256, cells, schedule = _n_pilot_fixture(
        floor_protocol, freeze,
    )
    with pytest.raises(admission.HoldoutAdmissionError, match="irreversible"):
        admission.reserve_n_pilot_holdout_observations(
            repo_root=root,
            protocol=protocol,
            protocol_sha256=protocol_sha256,
            verified_freeze_document=freeze,
            freeze_sha256=floor_protocol["freeze"]["sha256"],
            cells=cells,
            schedule=schedule,
            campaign_run_id="n-pilot-attempt",
            irreversible_pilot_approved=False,
        )
    assert not admission.shared_admission_root(root).exists()


@pytest.mark.parametrize(
    "approval",
    [1, "true", False, 0, None],
    ids=["truthy-int", "truthy-str", "false", "zero", "none"],
)
def test_n_pilot_rejects_non_true_approval_before_any_admission_write(
    tmp_path, approval,
):
    root, floor_protocol, freeze = _init_repo(tmp_path)
    protocol, protocol_sha256, cells, schedule = _n_pilot_fixture(
        floor_protocol, freeze,
    )

    with pytest.raises(admission.HoldoutAdmissionError, match="irreversible"):
        admission.reserve_n_pilot_holdout_observations(
            repo_root=root,
            protocol=protocol,
            protocol_sha256=protocol_sha256,
            verified_freeze_document=freeze,
            freeze_sha256=floor_protocol["freeze"]["sha256"],
            cells=cells,
            schedule=schedule,
            campaign_run_id="n-pilot-attempt",
            irreversible_pilot_approved=approval,
        )

    shared = admission.shared_admission_root(root)
    assert not (shared / "claims").exists()
    assert not (shared / "ledger.jsonl").exists()
    assert not (shared / "attempt-ledger.jsonl").exists()


def test_n_pilot_ledger_and_attempt_allowance_are_durable_and_protocol_bound(tmp_path):
    root, floor_protocol, freeze = _init_repo(tmp_path)
    protocol, protocol_sha256, cells, schedule = _n_pilot_fixture(
        floor_protocol, freeze,
    )
    admitted = admission.reserve_n_pilot_holdout_observations(
        repo_root=root,
        protocol=protocol,
        protocol_sha256=protocol_sha256,
        verified_freeze_document=freeze,
        freeze_sha256=floor_protocol["freeze"]["sha256"],
        cells=cells,
        schedule=schedule,
        campaign_run_id="n-pilot-attempt",
        irreversible_pilot_approved=True,
    )
    shared = admission.shared_admission_root(root)
    rows = admission._read_ledger(shared / "ledger.jsonl")  # noqa: SLF001
    assert len(rows) == 12
    assert {row["observation_role"] for row in rows} == {
        admission.OBSERVATION_ROLE_N_PILOT,
    }
    assert {row["protocol_sha256"] for row in rows} == {protocol_sha256}
    assert {row["freeze_sha256"] for row in rows} == {
        floor_protocol["freeze"]["sha256"],
    }
    assert len({row["schedule_sha256"] for row in rows}) == 1
    assert {row["campaign_run_id"] for row in rows} == {"n-pilot-attempt"}
    assert {row["irreversible_pilot_approved"] for row in rows} == {True}
    assert {row["reps"] for row in rows} == {floor_protocol["reps"]}

    token = admission.consume_n_pilot_attempt_ticket(
        admitted[0], schedule_index=0,
    )
    assert_issued_holdout_observation(token)
    assert token.permitted_run_once_calls == floor_protocol["reps"]
    ratio = freeze["holdouts"][token.freeze_holdout_key]["ycsb"]["ycsb_rratio"]
    for _ in range(floor_protocol["reps"]):
        assert_holdout_observation_admitted(
            gflags=[f"--ycsb_rratio={ratio}"], admission=token,
        )
    with pytest.raises(HoldoutObservationError, match="exhausted"):
        assert_holdout_observation_admitted(
            gflags=[f"--ycsb_rratio={ratio}"], admission=token,
        )
    with pytest.raises(admission.HoldoutAdmissionError, match="already consumed"):
        admission.consume_n_pilot_attempt_ticket(admitted[0], schedule_index=0)
    attempt_rows = admission._read_ledger(  # noqa: SLF001
        shared / "attempt-ledger.jsonl"
    )
    assert len(attempt_rows) == 1
    assert attempt_rows[0]["observation_role"] == admission.OBSERVATION_ROLE_N_PILOT


def test_r33_reserve_returns_authoritative_receipt_and_opaque_manifest(tmp_path):
    root, protocol, freeze = _init_repo(tmp_path)
    _r33_protocol, _protocol_sha256, _cells, _schedule, receipt = _reserve_r33(
        root, protocol, freeze, run_id="r33-receipt",
    )

    assert isinstance(receipt, admission.NPilotReservationReceipt)
    assert receipt["observation_role"] == admission.OBSERVATION_ROLE_N_PILOT_R33
    assert receipt["pilot_rounds"] == 33
    assert receipt["allocation_count"] == 3
    assert receipt["cell_count"] == 12
    assert receipt["schedule_row_count"] == 396
    assert receipt["attempt_count"] == 396
    assert len({cell["cell_ref"] for cell in receipt["cells"]}) == 12
    assert all(len(cell["global_schedule_indexes"]) == 33 for cell in receipt["cells"])

    shared = admission.shared_admission_root(root)
    assert len(list((shared / "claims").iterdir())) == 12
    rows = admission._read_ledger(shared / "ledger.jsonl")
    assert len(rows) == 12
    assert {row["observation_role"] for row in rows} == {
        admission.OBSERVATION_ROLE_N_PILOT_R33,
    }
    receipt_raw = receipt.receipt_path.read_bytes()
    assert not receipt_raw.endswith(b"\n")
    assert hashlib.sha256(receipt_raw).hexdigest() == receipt.receipt_sha256

    manifest = json.loads(receipt.manifest_path.read_bytes())
    assert receipt.manifest == manifest
    assert set(receipt.manifest) == admission._R33_MANIFEST_KEYS  # noqa: SLF001
    assert manifest["schema_version"] == "s8b-n-pilot-admission-manifest/v1"
    assert manifest["observation_role"] == admission.OBSERVATION_ROLE_N_PILOT_R33
    forbidden = {
        "claim_digest", "claim_file_sha256", "ledger_row_sha256", "claim",
        "ledger_row", "workload", "ycsb", "records", "threads", "run_cmd",
        "binary_path", "absolute_binary_path",
    }
    assert not forbidden.intersection(json.dumps(manifest))
    assert all(set(cell) == {"cell_ref", "global_schedule_indexes"}
               for cell in manifest["cells"])


def test_r33_reserve_separates_raw_freeze_digest_from_canonical_freeze_digest(tmp_path):
    root, protocol, freeze = _init_repo(tmp_path)
    r33_protocol, _protocol_sha256, cells, schedule = _r33_fixture(protocol, freeze)
    raw_freeze = json.dumps(freeze, ensure_ascii=False, indent=2).encode("utf-8") + b"\n"
    raw_freeze_sha256 = hashlib.sha256(raw_freeze).hexdigest()
    r33_protocol = json.loads(json.dumps(r33_protocol))
    r33_protocol["freeze"]["sha256"] = raw_freeze_sha256
    protocol_sha256 = hashlib.sha256(
        _canonical(r33_protocol) + b"\n"
    ).hexdigest()

    receipt = admission.reserve_n_pilot_holdout_observations(
        repo_root=root,
        protocol=r33_protocol,
        protocol_sha256=protocol_sha256,
        verified_freeze_document=freeze,
        freeze_sha256=raw_freeze_sha256,
        cells=cells,
        schedule=schedule,
        campaign_run_id="r33-freeze-raw",
        irreversible_pilot_approved=True,
    )

    canonical_freeze_sha256 = hashlib.sha256(
        _canonical(freeze) + b"\n"
    ).hexdigest()
    assert receipt["freeze_sha256"] == raw_freeze_sha256
    assert receipt["freeze_canonical_sha256"] == canonical_freeze_sha256
    assert canonical_freeze_sha256 != raw_freeze_sha256


def test_r33_consume_reloads_receipt_without_process_local_state(tmp_path, monkeypatch):
    root, protocol, freeze = _init_repo(tmp_path)
    r33_protocol, _protocol_sha256, _cells, _schedule, receipt = _reserve_r33(
        root, protocol, freeze, run_id="r33-consume",
    )
    raw_receipt = json.loads(receipt.receipt_path.read_bytes())
    before = len(admission._n_pilot_cell_states)  # noqa: SLF001
    monkeypatch.setattr(
        admission, "_n_pilot_cell_state",
        lambda _admission: pytest.fail("R33 consume used process-local cell state"),
    )
    first_cell = next(cell for cell in raw_receipt["cells"] if 0 in cell["global_schedule_indexes"])
    first = admission.consume_n_pilot_attempt_ticket(
        raw_receipt,
        repo_root=root,
        protocol=r33_protocol,
        verified_freeze_document=freeze,
        freeze_sha256=protocol["freeze"]["sha256"],
        schedule_sha256=raw_receipt["schedule_sha256"],
        global_schedule_index=0,
        expected_cell_id=first_cell["cell_id"],
    )
    second = next(
        cell for cell in raw_receipt["cells"] if 12 in cell["global_schedule_indexes"]
    )
    second_token = admission.consume_n_pilot_attempt_ticket(
        dict(raw_receipt),
        repo_root=root,
        protocol=r33_protocol,
        verified_freeze_document=freeze,
        freeze_sha256=protocol["freeze"]["sha256"],
        schedule_sha256=raw_receipt["schedule_sha256"],
        global_schedule_index=12,
        expected_cell_id=second["cell_id"],
    )
    assert first.attempt_id != second_token.attempt_id
    assert first.permitted_run_once_calls == second_token.permitted_run_once_calls == 5
    assert len(admission._n_pilot_cell_states) == before  # noqa: SLF001


def test_r33_consume_resolves_public_manifest_to_authoritative_receipt(tmp_path):
    root, protocol, freeze = _init_repo(tmp_path)
    r33_protocol, _protocol_sha256, _cells, _schedule, receipt = _reserve_r33(
        root, protocol, freeze, run_id="r33-public-manifest-consume",
    )
    cell = next(
        item for item in receipt["cells"]
        if 0 in item["global_schedule_indexes"]
    )

    observation = admission.consume_n_pilot_attempt_ticket(
        receipt.manifest,
        repo_root=root,
        protocol=r33_protocol,
        verified_freeze_document=freeze,
        freeze_sha256=protocol["freeze"]["sha256"],
        schedule_sha256=receipt["schedule_sha256"],
        global_schedule_index=0,
        expected_cell_id=cell["cell_id"],
    )

    assert observation.attempt_id


def test_r33_precommit_failure_has_no_visible_claim_and_can_be_aborted(tmp_path, monkeypatch):
    root, protocol, freeze = _init_repo(tmp_path)
    original = admission.write_guarded_create_bytes

    def fail_before_commit(*_args, **_kwargs):
        raise admission.HoldoutAdmissionError("injected receipt staging failure")

    monkeypatch.setattr(admission, "write_guarded_create_bytes", fail_before_commit)
    with pytest.raises(admission.HoldoutAdmissionError, match="staging failure"):
        _reserve_r33(root, protocol, freeze, run_id="r33-precommit")
    monkeypatch.setattr(admission, "write_guarded_create_bytes", original)

    shared = admission.shared_admission_root(root)
    assert not (shared / "ledger.jsonl").exists()
    assert list((shared / "claims").iterdir()) == []
    transaction = next((shared / "transactions").iterdir())
    abort = admission.abort_unpublished_n_pilot_transaction(
        repo_root=root,
        transaction_id=transaction.name,
        approval={"approved_by": "test-operator", "approval_ref": "test-approval"},
    )
    assert abort.is_file()
    assert (shared / "transaction-quarantine" / transaction.name / "staged").is_dir()
    assert json.loads(abort.read_bytes())["visible_publish"] is False


def test_r33_commit_recovery_allows_foreign_append_and_is_idempotent(tmp_path, monkeypatch):
    root, protocol, freeze = _init_repo(tmp_path)
    original = admission._r33_apply_committed_transaction_locked  # noqa: SLF001

    def crash_after_marker(*_args, **_kwargs):
        raise RuntimeError("injected post-marker crash")

    monkeypatch.setattr(
        admission, "_r33_apply_committed_transaction_locked", crash_after_marker,
    )
    with pytest.raises(RuntimeError, match="post-marker"):
        _reserve_r33(root, protocol, freeze, run_id="r33-recovery")
    monkeypatch.setattr(
        admission, "_r33_apply_committed_transaction_locked", original,
    )
    shared = admission.shared_admission_root(root)
    transaction = next((shared / "transactions").iterdir())
    foreign = {
        "schema_version": "s8b-holdout-observation-ledger/v1",
        "event": "admit",
        "freeze_sha256": "a" * 64,
        "freeze_holdout_key": "foreign",
        "configuration_id": "foreign",
        "ccbench_pin": "1" * 40,
        "env_tag": "fixture-env",
        "observation_role": admission.OBSERVATION_ROLE_FLOOR_CAMPAIGN,
    }
    (shared / "ledger.jsonl").write_bytes(admission._canonical_line(foreign))
    with admission._locked(shared):
        admission._recover_n_pilot_transactions_locked(shared)  # noqa: SLF001
    once = (shared / "ledger.jsonl").read_bytes()
    with admission._locked(shared):
        admission._recover_n_pilot_transactions_locked(shared)  # noqa: SLF001
    assert (shared / "ledger.jsonl").read_bytes() == once
    rows = admission._read_ledger(shared / "ledger.jsonl")
    assert len(rows) == 13
    assert len(list((shared / "claims").iterdir())) == 12
    assert len(list((shared / "receipts").iterdir())) == 1
    assert transaction.is_dir()


def test_r33_commit_recovery_rejects_exact_duplicate_ledger_identity(tmp_path):
    root, protocol, freeze = _init_repo(tmp_path)
    _reserve_r33(root, protocol, freeze, run_id="r33-duplicate-ledger")
    shared = admission.shared_admission_root(root)
    ledger_path = shared / "ledger.jsonl"
    rows = admission._read_ledger(ledger_path)  # noqa: SLF001
    ledger_path.write_bytes(ledger_path.read_bytes() + admission._canonical_line(rows[0]))

    with admission._locked(shared):
        with pytest.raises(admission.HoldoutAdmissionError, match="identity is duplicated"):
            admission._recover_n_pilot_transactions_locked(shared)  # noqa: SLF001


def test_r33_consume_marker_recovery_rebuilds_missing_attempt_row(tmp_path, monkeypatch):
    root, protocol, freeze = _init_repo(tmp_path)
    r33_protocol, _protocol_sha256, _cells, _schedule, receipt = _reserve_r33(
        root, protocol, freeze, run_id="r33-marker-recovery",
    )
    original = admission._append_ledger  # noqa: SLF001

    def fail_attempt_append(path, rows):
        if Path(path).name == "attempt-ledger.jsonl":
            raise admission.HoldoutAdmissionError("injected attempt append crash")
        return original(path, rows)

    monkeypatch.setattr(admission, "_append_ledger", fail_attempt_append)
    cell = next(cell for cell in receipt["cells"] if 0 in cell["global_schedule_indexes"])
    with pytest.raises(admission.HoldoutAdmissionError, match="attempt append crash"):
        admission.consume_n_pilot_attempt_ticket(
            receipt,
            repo_root=root,
            protocol=r33_protocol,
            verified_freeze_document=freeze,
            freeze_sha256=protocol["freeze"]["sha256"],
            schedule_sha256=receipt["schedule_sha256"],
            global_schedule_index=0,
            expected_cell_id=cell["cell_id"],
        )
    monkeypatch.setattr(admission, "_append_ledger", original)
    shared = admission.shared_admission_root(root)
    assert len(list((shared / "consumed").iterdir())) == 1
    with admission._locked(shared):
        admission._recover_n_pilot_attempt_ledger_locked(shared)  # noqa: SLF001
        admission._recover_n_pilot_attempt_ledger_locked(shared)  # noqa: SLF001
    assert len(admission._read_ledger(shared / "attempt-ledger.jsonl")) == 1


def test_pilot_claim_requires_irreversible_approval_before_claim(tmp_path):
    root, protocol, freeze = _init_repo(tmp_path)
    cells, schedule = _cells_and_schedule(protocol, freeze)
    out_root = root / "out"
    run_id = "run-a"
    run_relpath = f"env/fixture-env/calibration/s8b-floor-pilot/{run_id}"
    run_dir = out_root / run_relpath
    run_dir.mkdir(parents=True)
    (run_dir / "manifest.json").write_text(json.dumps({
        "protocol_sha256": hashlib.sha256(_canonical(protocol)).hexdigest(),
        "freeze_sha256": protocol["freeze"]["sha256"],
        "reps": protocol["reps"],
    }, sort_keys=True) + "\n", encoding="utf-8")
    with pytest.raises(admission.HoldoutAdmissionError, match="irreversible"):
        admission.reserve_floor_holdout_observations(
            repo_root=root, protocol=protocol,
            verified_freeze_document=freeze,
            freeze_sha256=protocol["freeze"]["sha256"],
            cells=cells, schedule=schedule, campaign_run_id=run_id,
            out_root=out_root, run_dir=run_dir, run_relpath=run_relpath,
            mode="pilot", resume=False, nondefault_seams=[],
            irreversible_pilot_approved=False,
        )
    shared = admission.shared_admission_root(root)
    assert not shared.exists()


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
    admission.finalize_floor_holdout_admissions(first)
    ledger = admission.shared_admission_root(root) / "ledger.jsonl"
    before = ledger.read_bytes()

    with pytest.raises(admission.HoldoutAdmissionError, match="journal is absent"):
        _reserve(root, protocol, freeze, run_id="run-a", resume=True)

    resumed = _reserve(
        root, protocol, freeze, run_id="run-a", resume=True, journal_exists=True,
    )
    admission.finalize_floor_holdout_admissions(resumed)
    assert ledger.read_bytes() == before

    manifest_path = (
        root / "out/env/fixture-env/calibration/s8b-floor-pilot/run-a/manifest.json"
    )
    changed_manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    changed_manifest["evidence_only_change"] = True
    manifest_path.write_text(
        json.dumps(changed_manifest, sort_keys=True) + "\n", encoding="utf-8"
    )
    journal_path = manifest_path.with_name("journal.jsonl")
    journal_row = json.loads(journal_path.read_text(encoding="utf-8"))
    journal_row["manifest_sha256"] = hashlib.sha256(
        manifest_path.read_bytes()
    ).hexdigest()
    journal_path.write_text(
        json.dumps(journal_row, sort_keys=True) + "\n", encoding="utf-8"
    )
    mismatched = _reserve(
        root, protocol, freeze, run_id="run-a", resume=True, journal_exists=True,
    )
    with pytest.raises(admission.HoldoutAdmissionError, match="same run identity"):
        admission.finalize_floor_holdout_admissions(mismatched)


def test_resume_api_has_no_caller_journal_or_manifest_self_report():
    reserve_parameters = inspect.signature(
        admission.reserve_floor_holdout_observations
    ).parameters
    finalize_parameters = inspect.signature(
        admission.finalize_floor_holdout_admissions
    ).parameters
    assert "journal_exists" not in reserve_parameters
    assert "measurement_started" not in reserve_parameters
    assert "manifest_sha256" not in finalize_parameters


@pytest.mark.parametrize(
    "claims_to_keep,expected_entry_kinds",
    [
        (0, {"resume"}),
        (1, {"fresh", "resume"}),
        (12, {"fresh"}),
    ],
    ids=["zero-claims", "one-claim", "all-claims"],
)
def test_resume_claim_transition_table_is_run_wide_and_marker_guarded(
    tmp_path, claims_to_keep, expected_entry_kinds,
):
    root, protocol, freeze = _init_repo(tmp_path)
    _reserve(root, protocol, freeze, run_id="crash-point")
    shared = admission.shared_admission_root(root)
    claim_paths = sorted((shared / "claims").iterdir())
    assert len(claim_paths) == 12
    for path in claim_paths[claims_to_keep:]:
        path.unlink()

    _reserve(
        root, protocol, freeze, run_id="crash-point",
        resume=True, journal_exists=True,
    )

    claims = [json.loads(path.read_bytes()) for path in (shared / "claims").iterdir()]
    assert len(claims) == 12
    assert {claim["entry_kind"] for claim in claims} == expected_entry_kinds
    markers = list((shared / "refreeze-disqualifications").iterdir())
    assert len(markers) == 1
    marker = json.loads(markers[0].read_bytes())
    assert marker["reason"] == "resume"
    assert marker["campaign_run_id"] == "crash-point"


def test_resume_preserves_existing_v1_claims_immutably(tmp_path):
    root, protocol, freeze = _init_repo(tmp_path)
    _reserve(root, protocol, freeze, run_id="legacy-v1")
    shared = admission.shared_admission_root(root)
    before = {}
    for path in (shared / "claims").iterdir():
        claim = json.loads(path.read_bytes())
        claim["schema_version"] = "s8b-holdout-cell-claim/v1"
        claim.pop("entry_kind")
        claim.pop("nondefault_seams")
        path.write_bytes(canonical_json_line(claim))
        before[path.name] = path.read_bytes()

    _reserve(
        root, protocol, freeze, run_id="legacy-v1",
        resume=True, journal_exists=True,
    )

    after = {
        path.name: path.read_bytes() for path in (shared / "claims").iterdir()
    }
    assert after == before
    assert len(list((shared / "refreeze-disqualifications").iterdir())) == 1


def test_resume_backfills_partial_v1_claim_set_without_schema_upgrade(tmp_path):
    root, protocol, freeze = _init_repo(tmp_path)
    _reserve(root, protocol, freeze, run_id="legacy-v1-partial")
    shared = admission.shared_admission_root(root)
    claim_paths = sorted((shared / "claims").iterdir())
    retained_path = claim_paths[0]
    retained = json.loads(retained_path.read_bytes())
    retained["schema_version"] = "s8b-holdout-cell-claim/v1"
    retained.pop("entry_kind")
    retained.pop("nondefault_seams")
    retained_path.write_bytes(canonical_json_line(retained))
    retained_before = retained_path.read_bytes()
    for path in claim_paths[1:]:
        path.unlink()

    _reserve(
        root, protocol, freeze, run_id="legacy-v1-partial",
        resume=True, journal_exists=True,
    )

    claims = [
        json.loads(path.read_bytes()) for path in (shared / "claims").iterdir()
    ]
    assert len(claims) == 12
    assert {claim["schema_version"] for claim in claims} == {
        "s8b-holdout-cell-claim/v1"
    }
    assert retained_path.read_bytes() == retained_before


def test_resume_rejects_actual_terminal_journal(tmp_path):
    root, protocol, freeze = _init_repo(tmp_path)
    first = _reserve(root, protocol, freeze, run_id="run-a")
    admission.finalize_floor_holdout_admissions(first)
    run_dir = root / "out/env/fixture-env/calibration/s8b-floor-pilot/run-a"
    (run_dir / "journal.jsonl").write_text(
        json.dumps({"event": "terminal", "status": "completed"}) + "\n",
        encoding="utf-8",
    )
    with pytest.raises(admission.HoldoutAdmissionError, match="terminal run"):
        _reserve(
            root, protocol, freeze, run_id="run-a",
            resume=True, journal_exists=True,
        )


def test_resolver_record_path_and_bytes_are_the_protocol_authority(tmp_path):
    root, protocol, freeze = _init_repo(tmp_path)
    relpath = "output/s8b-freeze/protocols/selected.json"
    selected = root / relpath
    selected.parent.mkdir(parents=True)
    selected.write_bytes(_canonical(protocol))
    _git(root, "add", relpath)
    _git(root, "-c", "user.name=fixture", "-c", "user.email=f@example.invalid",
         "commit", "-m", "commit selected protocol")
    record = _indexed_protocol_record(root, relpath)

    reservation = _reserve(
        root, protocol, freeze, run_id="run-selected",
        resolver_record=record,
    )

    assert reservation.protocol_sha256 == record.sha256


def test_authority_keeps_resolver_commit_when_head_moves_after_resolution(tmp_path):
    root, protocol, freeze = _init_repo(tmp_path)
    record = _indexed_protocol_record(root)
    fixed_commit = record.commit_oid
    moved = False

    def move_head_after_resolution(*, root):
        nonlocal moved
        assert root == Path(record_root)
        marker = root / "head-moved-after-resolution.txt"
        marker.write_text("new commit\n", encoding="utf-8")
        _git(root, "add", marker.name)
        _git(
            root, "-c", "user.name=fixture", "-c",
            "user.email=f@example.invalid", "commit", "-m", "move HEAD",
        )
        moved = True
        return record

    record_root = root
    original_blob_reader = s8b_floor_campaign._head_blob_100644
    with mock.patch.object(
            s8b_floor_campaign, "_head_blob_100644",
            wraps=original_blob_reader,
    ) as blob_reader:
        reservation = _reserve(
            root, protocol, freeze, run_id="run-fixed-commit",
            resolver_record=record,
            resolver_side_effect=move_head_after_resolution,
        )

    assert moved
    assert _git(root, "rev-parse", "HEAD") != fixed_commit
    assert admission._reservation_state(reservation).measurement_head == fixed_commit
    assert blob_reader.call_args_list == [
        mock.call(root, record.path, fixed_commit),
        mock.call(root, "output/s8b-freeze/holdout_freeze.json", fixed_commit),
    ]


def test_resolved_record_bytes_mismatch_is_rejected_before_any_cell_claim(tmp_path):
    root, protocol, freeze = _init_repo(tmp_path)
    record = _indexed_protocol_record(root)
    mismatched = s8b_floor_campaign.IndexedFloorProtocol(
        path=record.path,
        document=record.document,
        raw_bytes=record.raw_bytes + b" ",
        sha256=record.sha256,
        commit_oid=record.commit_oid,
    )

    with pytest.raises(admission.HoldoutAdmissionError, match="indexed record"):
        _reserve(
            root, protocol, freeze, run_id="run-bytes-mismatch",
            resolver_record=mismatched,
        )

    assert list((admission.shared_admission_root(root) / "claims").iterdir()) == []


def test_resolved_record_sha256_mismatch_is_rejected_before_any_cell_claim(tmp_path):
    root, protocol, freeze = _init_repo(tmp_path)
    record = _indexed_protocol_record(root)
    mismatched = s8b_floor_campaign.IndexedFloorProtocol(
        path=record.path,
        document=record.document,
        raw_bytes=record.raw_bytes,
        sha256="0" * 64,
        commit_oid=record.commit_oid,
    )

    with pytest.raises(admission.HoldoutAdmissionError, match="sha256"):
        _reserve(
            root, protocol, freeze, run_id="run-sha-mismatch",
            resolver_record=mismatched,
        )

    assert list((admission.shared_admission_root(root) / "claims").iterdir()) == []


def test_resolver_exception_is_rejected_before_any_cell_claim(tmp_path):
    root, protocol, freeze = _init_repo(tmp_path)

    with pytest.raises(admission.HoldoutAdmissionError, match="cannot resolve"):
        _reserve(
            root, protocol, freeze, run_id="run-resolver-error",
            resolver_side_effect=s8b_floor_campaign.FloorCampaignError(
                "fixture resolver rejection"
            ),
        )

    assert list((admission.shared_admission_root(root) / "claims").iterdir()) == []


def test_resolver_invalid_record_type_is_rejected_before_any_cell_claim(tmp_path):
    root, protocol, freeze = _init_repo(tmp_path)

    with pytest.raises(admission.HoldoutAdmissionError, match="invalid record type"):
        _reserve(
            root, protocol, freeze, run_id="run-invalid-record",
            resolver_record=object(),
        )

    assert list((admission.shared_admission_root(root) / "claims").iterdir()) == []


def test_resolver_record_without_fixed_commit_is_rejected_before_any_cell_claim(
        tmp_path):
    root, protocol, freeze = _init_repo(tmp_path)
    record = _indexed_protocol_record(root)
    missing_commit = s8b_floor_campaign.IndexedFloorProtocol(
        path=record.path,
        document=record.document,
        raw_bytes=record.raw_bytes,
        sha256=record.sha256,
    )

    with pytest.raises(admission.HoldoutAdmissionError, match="fixed commit OID"):
        _reserve(
            root, protocol, freeze, run_id="run-missing-fixed-commit",
            resolver_record=missing_commit,
        )

    assert list((admission.shared_admission_root(root) / "claims").iterdir()) == []


def test_supplied_protocol_mismatch_remains_rejected_before_any_cell_claim(tmp_path):
    root, protocol, freeze = _init_repo(tmp_path)
    supplied = dict(protocol)
    supplied["master_seed"] = "caller-selected-seed"

    with pytest.raises(admission.HoldoutAdmissionError, match="supplied protocol"):
        _reserve(root, supplied, freeze, run_id="run-supplied-mismatch")

    assert list((admission.shared_admission_root(root) / "claims").iterdir()) == []


def test_committed_versioned_protocol_admits_with_dirty_legacy_worktree(tmp_path):
    source_root = Path(__file__).resolve().parents[2]
    legacy_raw = (
        source_root / "output/s8b-freeze/floor_protocol.json"
    ).read_bytes()
    freeze_raw = (
        source_root / "output/s8b-freeze/holdout_freeze.json"
    ).read_bytes()
    legacy_protocol = json.loads(legacy_raw)
    freeze = json.loads(freeze_raw)
    head_pin = "2" * 40
    versioned_protocol = dict(legacy_protocol)
    versioned_protocol["ccbench_pin"] = head_pin
    versioned_raw = s8b_floor_campaign._canonical_bytes(  # noqa: SLF001
        versioned_protocol
    )
    versioned_relpath = s8b_floor_campaign._derived_reseal_protocol_relpath(  # noqa: SLF001
        versioned_protocol["contract_sha256"], head_pin,
    )

    root = tmp_path / "versioned-repo"
    root.mkdir()
    _git(root, "init")
    fixed = root / "output/s8b-freeze"
    fixed.mkdir(parents=True)
    (fixed / "floor_protocol.json").write_bytes(legacy_raw)
    (fixed / "holdout_freeze.json").write_bytes(freeze_raw)
    versioned_path = root / versioned_relpath
    versioned_path.parent.mkdir(parents=True)
    versioned_path.write_bytes(versioned_raw)
    _git(root, "add", "output/s8b-freeze")
    _git(
        root, "update-index", "--add", "--cacheinfo",
        f"160000,{head_pin},external/ccbench",
    )
    _git(root, "-c", "user.name=fixture", "-c", "user.email=f@example.invalid",
         "commit", "-m", "commit versioned protocol")

    # The resolver must use the committed versioned record, not dirty legacy bytes.
    (fixed / "floor_protocol.json").write_bytes(versioned_raw)
    reservation = _reserve(
        root, versioned_protocol, freeze, run_id="run-versioned",
        use_real_resolver=True,
    )

    assert reservation.protocol_sha256 == hashlib.sha256(versioned_raw).hexdigest()
    assert versioned_path.read_bytes() == versioned_raw


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
    admitted = admission.finalize_floor_holdout_admissions(reservation)
    cell = cells[0]
    seq = next(row["seq"] for row in schedule if row["cell_id"] == cell["cell_id"])
    attempt_id = f"{cell['cell_id']}::seq{seq}"
    run_dir = root / "out/env/fixture-env/calibration/s8b-floor-pilot/run-a"
    (run_dir / "journal.jsonl").write_text(json.dumps({
        "event": "session-start", "seq": seq,
        "round": next(row["round"] for row in schedule if row["seq"] == seq),
        "kind": "planned", "cell_id": cell["cell_id"],
        "attempt_id": attempt_id, "trigger": None,
    }, sort_keys=True) + "\n", encoding="utf-8")
    manifest_sha256 = hashlib.sha256((run_dir / "manifest.json").read_bytes()).hexdigest()
    return (
        root, protocol, cell, admitted[cell["cell_id"]], attempt_id,
        manifest_sha256,
    )


def _floor_expected_marker(admitted, attempt_id: str) -> dict:
    state = admission._cell_state(admitted)  # noqa: SLF001
    return {
        "schema_version": admission._ATTEMPT_SCHEMA,  # noqa: SLF001
        "event": "consume",
        "claim_digest": state.claim_digest,
        "attempt_id": attempt_id,
        "campaign_run_id": state.row["campaign_run_id"],
        "manifest_sha256": state.row["manifest_sha256"],
        "run_relpath": state.row["run_relpath"],
        "cell_id": state.row["cell_id"],
        "freeze_holdout_key": state.row["freeze_holdout_key"],
        "configuration_id": state.row["configuration_id"],
        "observation_role": admission.OBSERVATION_ROLE_FLOOR_CAMPAIGN,
    }


def _issued_inspection_kwargs(
    root: Path, protocol: dict, admitted, manifest_sha256: str,
) -> dict:
    _fixture_protocol, freeze = _fixture_documents()
    cells = s8b_floor_contract.enumerate_cells(
        freeze, stock_configuration=protocol["stock_configuration"],
    )
    state = admission._cell_state(admitted)  # noqa: SLF001
    return {
        "repo_root": root,
        "protocol": protocol,
        "verified_freeze_document": freeze,
        "freeze_sha256": protocol["freeze"]["sha256"],
        "manifest_sha256": manifest_sha256,
        "campaign_run_id": "run-a",
        "run_relpath": "env/fixture-env/calibration/s8b-floor-pilot/run-a",
        "mode": "pilot",
        "cells": cells,
        "schedule": list(state.schedule),
        "sessions": admission._read_run_journal(  # noqa: SLF001
            state.run_dir / "journal.jsonl"
        ),
    }


def _crash_floor_after_marker(monkeypatch, admitted, attempt_id: str) -> None:
    original = admission._append_ledger  # noqa: SLF001

    def crash(path, rows):
        if path.name == "attempt-ledger.jsonl":
            raise RuntimeError("cut-6")
        return original(path, rows)

    monkeypatch.setattr(admission, "_append_ledger", crash)
    with pytest.raises(RuntimeError, match="cut-6"):
        admission.consume_attempt_ticket(admitted, attempt_id=attempt_id)
    monkeypatch.setattr(admission, "_append_ledger", original)


def _append_journal_rows(admitted, *rows: dict) -> None:
    state = admission._cell_state(admitted)  # noqa: SLF001
    with (state.run_dir / "journal.jsonl").open("a", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True) + "\n")


def _write_verified_recovery_registry(
    admitted, *, trigger_start: dict,
) -> Path:
    state = admission._cell_state(admitted)  # noqa: SLF001
    authority_id, authority_policy_sha256 = _TEST_RECOVERY_AUTHORITY
    schedule_sha256 = hashlib.sha256(
        attempt_registry_core.canonical_json_bytes(list(state.schedule))
    ).hexdigest()
    binding = s8b_attempt_profile.S8BAttemptBinding(
        freeze_sha256=state.row["freeze_sha256"],
        protocol_sha256=state.row["protocol_sha256"],
        schedule_sha256=schedule_sha256,
    )
    profile = s8b_attempt_profile.make_s8b_domain_profile(
        max_consumptions_per_budget_key=len(state.attempt_ids),
        recovery_authority_id=authority_id,
        recovery_authority_policy_sha256=authority_policy_sha256,
    )
    target_ordinal = (
        trigger_start["retry_ordinal"]
        if trigger_start.get("kind") == "retry" else 0
    )
    slots = []
    for ordinal in range(target_ordinal + 1):
        slot_identity = {
            "freeze_holdout_key": state.row["freeze_holdout_key"],
            "configuration_id": state.row["configuration_id"],
            "repetition": trigger_start["round"] - 1,
            "attempt_ordinal": ordinal,
        }
        slots.append(s8b_attempt_profile.S8BAttemptSlot(
            **slot_identity,
            schedule_row_sha256=hashlib.sha256(
                attempt_registry_core.canonical_json_bytes(slot_identity)
            ).hexdigest(),
        ))
    rows = attempt_registry_core.create_attempt_registry_genesis(
        profile=profile, slots=slots, binding=binding,
    )
    for ordinal, slot in enumerate(slots):
        slot_id = s8b_attempt_profile.S8B_SLOT_CODEC.slot_id(slot)
        rows = attempt_registry_core.reserve_attempt_slot(
            rows, profile=profile, freeze_id=binding.freeze_sha256,
            slot_id=slot_id, binding=binding,
            run_start_receipt_sha256=hashlib.sha256(
                f"run-start-{ordinal}".encode("utf-8")
            ).hexdigest(),
            process_identity={
                "pid": 101 + ordinal,
                "starttime": f"test-start-{ordinal}",
                "execution_uuid": f"test-start-uuid-{ordinal}",
            },
            started_at=f"2026-08-25T00:00:{ordinal * 3:02d}+00:00",
        )
        start = next(
            row for row in rows
            if row.get("event") == "start"
            and row.get("attempt_ordinal") == ordinal
        )
        receipt = {
            "schema_version": s8b_attempt_profile.S8B_RECOVERY_RECEIPT_SCHEMA_VERSION,
            "event": s8b_attempt_profile.S8B_RECOVERY_RECEIPT_EVENT,
            "source": s8b_attempt_profile.S8B_RECOVERY_RECEIPT_SOURCE,
            "scheduler_request_id": f"test-request-{ordinal}",
            "target_start_event_sha256": start["event_sha256"],
            "raw_scheduler_accounting_record_sha256": hashlib.sha256(
                f"accounting-{ordinal}".encode("utf-8")
            ).hexdigest(),
            "authority_id": authority_id,
            "authority_policy_sha256": authority_policy_sha256,
            "failure_reason": "node_failure",
            "collected_at": f"2026-08-25T00:00:{ordinal * 3 + 1:02d}+00:00",
        }
        rows = attempt_registry_core.record_attempt_recovery(
            rows, profile=profile, freeze_id=binding.freeze_sha256,
            slot_id=slot_id, binding=binding,
            scheduler_accounting_receipt=receipt,
            recoverer_process_identity={
                "pid": 202 + ordinal,
                "starttime": f"test-recover-{ordinal}",
                "execution_uuid": f"test-recover-uuid-{ordinal}",
            },
            recovered_at=f"2026-08-25T00:00:{ordinal * 3 + 2:02d}+00:00",
        )
    relative = s8b_attempt_profile.S8B_REGISTRY_LAYOUT.registry_path.as_posix().format(
        freeze_sha256=binding.freeze_sha256,
    )
    path = state.root.joinpath(*Path(relative).parts)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(b"".join(
        attempt_registry_core.canonical_json_bytes(row) + b"\n" for row in rows
    ))
    return path


def test_attempt_ticket_is_durably_single_use(tmp_path):
    root, protocol, _cell, admitted, attempt_id, _manifest_sha256 = _issued_cell(tmp_path)
    token = admission.consume_attempt_ticket(admitted, attempt_id=attempt_id)
    assert_issued_holdout_observation(token)
    assert token.attempt_id == attempt_id
    assert token.permitted_run_once_calls == protocol["reps"]
    with pytest.raises(admission.HoldoutAdmissionError, match="already consumed"):
        admission.consume_attempt_ticket(admitted, attempt_id=attempt_id)
    shared = admission.shared_admission_root(root)
    consumed = shared / "consumed"
    assert len(list(consumed.iterdir())) == 1
    attempt_rows = admission._read_ledger(shared / "attempt-ledger.jsonl")
    assert attempt_rows[0]["observation_role"] == (
        admission.OBSERVATION_ROLE_FLOOR_CAMPAIGN
    )


def test_cut6_rebuilds_attempt_row_and_reissues_same_attempt_under_lock(
    tmp_path, monkeypatch,
):
    root, protocol, _cell, admitted, attempt_id, _manifest = _issued_cell(tmp_path)
    _crash_floor_after_marker(monkeypatch, admitted, attempt_id)
    shared = admission.shared_admission_root(root)
    assert not (shared / "attempt-ledger.jsonl").exists()
    assert admission.floor_attempt_requires_cut6_replay(
        admitted, attempt_id=attempt_id,
    ) is True

    original_issue = admission._issue_floor_attempt_observation  # noqa: SLF001

    def assert_locked(state, *, attempt_id):
        probe = subprocess.run(
            ["flock", "-n", str(shared / "ledger.lock"), "true"],
            check=False, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        )
        assert probe.returncode == 1
        return original_issue(state, attempt_id=attempt_id)

    monkeypatch.setattr(admission, "_issue_floor_attempt_observation", assert_locked)
    token = admission.consume_attempt_ticket(admitted, attempt_id=attempt_id)

    assert token.attempt_id == attempt_id
    assert token.permitted_run_once_calls == protocol["reps"]
    assert len(list((shared / "consumed").iterdir())) == 1
    rows = admission._read_ledger(shared / "attempt-ledger.jsonl")  # noqa: SLF001
    assert rows == [_floor_expected_marker(admitted, attempt_id)]
    assert all("retry" not in row["attempt_id"] for row in rows)
    assert admission.floor_attempt_requires_cut6_replay(
        admitted, attempt_id=attempt_id,
    ) is False


def test_cut6_replay_query_rejects_start_before_consumed_marker(tmp_path):
    _root, _protocol, _cell, admitted, attempt_id, _manifest = _issued_cell(tmp_path)

    assert admission.floor_attempt_requires_cut6_replay(
        admitted, attempt_id=attempt_id,
    ) is False


def test_floor_recovery_query_signatures_expose_only_admission_verdict_inputs():
    cut6 = inspect.signature(admission.floor_attempt_requires_cut6_replay)
    retry = inspect.signature(admission.floor_retry_trigger_for_round)
    assert tuple(cut6.parameters) == ("admission", "attempt_id")
    assert tuple(retry.parameters) == ("admission", "round_no")
    assert cut6.parameters["attempt_id"].kind is inspect.Parameter.KEYWORD_ONLY
    assert retry.parameters["round_no"].kind is inspect.Parameter.KEYWORD_ONLY


def test_cut6_m_plus_a_plus_rejects_before_any_new_marker_write(
    tmp_path, monkeypatch,
):
    _root, _protocol, _cell, admitted, attempt_id, _manifest = _issued_cell(tmp_path)
    admission.consume_attempt_ticket(admitted, attempt_id=attempt_id)

    def forbidden_write(*_args, **_kwargs):
        pytest.fail("M+A+ reached marker creation")

    monkeypatch.setattr(admission, "_write_exclusive", forbidden_write)
    with pytest.raises(admission.HoldoutAdmissionError, match="already consumed"):
        admission.consume_attempt_ticket(admitted, attempt_id=attempt_id)


def test_cut6_marker_absence_does_not_invent_requested_attempt_row(tmp_path):
    root, _protocol, _cell, admitted, attempt_id, _manifest = _issued_cell(tmp_path)
    shared = admission.shared_admission_root(root)
    expected = _floor_expected_marker(admitted, attempt_id)

    with admission._locked(shared):  # noqa: SLF001
        recovered = admission._recover_floor_attempt_ledger_locked(  # noqa: SLF001
            shared, expected_marker=expected, completed_attempt=False,
        )

    assert recovered is False
    assert not (shared / "attempt-ledger.jsonl").exists()
    assert list((shared / "consumed").iterdir()) == []


def test_cut6_orphan_attempt_row_without_marker_is_rejected(tmp_path):
    root, _protocol, _cell, admitted, attempt_id, _manifest = _issued_cell(tmp_path)
    shared = admission.shared_admission_root(root)
    expected = _floor_expected_marker(admitted, attempt_id)
    with admission._locked(shared):  # noqa: SLF001
        admission._append_ledger(  # noqa: SLF001
            shared / "attempt-ledger.jsonl", [expected],
        )
        with pytest.raises(admission.HoldoutAdmissionError, match="no consume marker"):
            admission._recover_floor_attempt_ledger_locked(  # noqa: SLF001
                shared, expected_marker=expected, completed_attempt=False,
            )


@pytest.mark.parametrize("tamper", ["extra-key", "claim-mismatch"])
def test_cut6_recovery_requires_exact_marker_rederived_from_claim(
    tmp_path, monkeypatch, tamper,
):
    root, _protocol, _cell, admitted, attempt_id, _manifest = _issued_cell(tmp_path)
    _crash_floor_after_marker(monkeypatch, admitted, attempt_id)
    shared = admission.shared_admission_root(root)
    marker_path = next((shared / "consumed").iterdir())
    marker = json.loads(marker_path.read_text(encoding="utf-8"))
    if tamper == "extra-key":
        marker["extra"] = "forbidden"
        match = "exact shape"
    else:
        marker["campaign_run_id"] = "different-run"
        match = "differs from claim and ledger"
    marker_path.write_bytes(_canonical(marker) + b"\n")

    with pytest.raises(admission.HoldoutAdmissionError, match=match):
        admission.consume_attempt_ticket(admitted, attempt_id=attempt_id)
    assert not (shared / "attempt-ledger.jsonl").exists()


def test_cut6_completed_session_forbids_reissue_of_same_attempt(
    tmp_path, monkeypatch,
):
    root, _protocol, cell, admitted, attempt_id, _manifest = _issued_cell(tmp_path)
    _crash_floor_after_marker(monkeypatch, admitted, attempt_id)
    state = admission._cell_state(admitted)  # noqa: SLF001
    start = json.loads((state.run_dir / "journal.jsonl").read_text(encoding="utf-8"))
    _append_journal_rows(admitted, {
        "event": "session", "seq": start["seq"], "round": start["round"],
        "kind": "planned", "cell_id": cell["cell_id"],
        "attempt_id": attempt_id, "valid": True,
    })

    with pytest.raises(admission.HoldoutAdmissionError, match="completed attempt"):
        admission.consume_attempt_ticket(admitted, attempt_id=attempt_id)
    shared = admission.shared_admission_root(root)
    assert not (shared / "attempt-ledger.jsonl").exists()


def test_ticket_consumption_precedes_crashing_measure_callback_m5(tmp_path):
    _root, protocol, cell, admitted, attempt_id, manifest_sha256 = _issued_cell(tmp_path)
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
        manifest_sha256=manifest_sha256,
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


def test_retry_ticket_without_failed_planned_trigger_is_rejected(tmp_path):
    root, protocol, freeze = _init_repo(tmp_path)
    cells, _schedule = _cells_and_schedule(protocol, freeze)
    reservation = _reserve(root, protocol, freeze, run_id="run-a")
    admitted = admission.finalize_floor_holdout_admissions(reservation)
    cell = cells[0]
    retry_id = f"{cell['cell_id']}::retry1"
    run_dir = root / "out/env/fixture-env/calibration/s8b-floor-pilot/run-a"
    (run_dir / "journal.jsonl").write_text(json.dumps({
        "event": "session-start", "seq": 96, "round": 1,
        "kind": "retry", "retry_ordinal": 1,
        "cell_id": cell["cell_id"], "attempt_id": retry_id,
        "trigger": None,
    }, sort_keys=True) + "\n", encoding="utf-8")
    with pytest.raises(admission.HoldoutAdmissionError, match="failed planned trigger"):
        admission.consume_attempt_ticket(
            admitted[cell["cell_id"]], attempt_id=retry_id,
        )
    consumed = admission.shared_admission_root(root) / "consumed"
    assert list(consumed.iterdir()) == []


def test_existing_failed_planned_session_retry_still_passes(tmp_path):
    _root, protocol, cell, admitted, attempt_id, _manifest = _issued_cell(tmp_path)
    state = admission._cell_state(admitted)  # noqa: SLF001
    planned_start = json.loads(
        (state.run_dir / "journal.jsonl").read_text(encoding="utf-8")
    )
    retry_id = f"{cell['cell_id']}::retry1"
    _append_journal_rows(
        admitted,
        {
            "event": "session", "seq": planned_start["seq"],
            "round": planned_start["round"], "kind": "planned",
            "cell_id": cell["cell_id"], "attempt_id": attempt_id,
            "valid": False, "probe_before": {"competing": False},
        },
        {
            "event": "session-start", "seq": len(state.schedule),
            "round": planned_start["round"], "kind": "retry",
            "retry_ordinal": 1, "cell_id": cell["cell_id"],
            "attempt_id": retry_id, "trigger": attempt_id,
        },
    )

    token = admission.consume_attempt_ticket(admitted, attempt_id=retry_id)
    assert token.attempt_id == retry_id
    assert token.permitted_run_once_calls == protocol["reps"]


def test_legacy_retry_rejects_extra_completion_for_same_trigger(tmp_path):
    root, _protocol, cell, admitted, attempt_id, _manifest = _issued_cell(tmp_path)
    state = admission._cell_state(admitted)  # noqa: SLF001
    planned_start = json.loads(
        (state.run_dir / "journal.jsonl").read_text(encoding="utf-8")
    )
    retry_id = f"{cell['cell_id']}::retry1"
    _append_journal_rows(
        admitted,
        {
            "event": "session", "seq": planned_start["seq"],
            "round": planned_start["round"], "kind": "planned",
            "cell_id": cell["cell_id"], "attempt_id": attempt_id,
            "valid": False, "probe_before": {"competing": False},
        },
        {
            "event": "session", "seq": planned_start["seq"],
            "round": planned_start["round"], "kind": "planned",
            "cell_id": cell["cell_id"], "attempt_id": attempt_id,
            "valid": True, "probe_before": {"competing": False},
        },
    )

    with pytest.raises(admission.HoldoutAdmissionError, match="more than one"):
        admission.floor_retry_trigger_for_round(
            admitted, round_no=planned_start["round"],
        )

    _append_journal_rows(admitted, {
        "event": "session-start", "seq": len(state.schedule),
        "round": planned_start["round"], "kind": "retry",
        "retry_ordinal": 1, "cell_id": cell["cell_id"],
        "attempt_id": retry_id, "trigger": attempt_id,
    })
    with pytest.raises(admission.HoldoutAdmissionError, match="exactly one"):
        admission.consume_attempt_ticket(admitted, attempt_id=retry_id)
    consumed = admission.shared_admission_root(root) / "consumed"
    assert list(consumed.iterdir()) == []


def test_malformed_registry_does_not_disable_existing_failed_session_retry(tmp_path):
    root, protocol, cell, admitted, attempt_id, manifest = _issued_cell(tmp_path)
    state = admission._cell_state(admitted)  # noqa: SLF001
    planned_start = json.loads(
        (state.run_dir / "journal.jsonl").read_text(encoding="utf-8")
    )
    registry_path = admission._floor_registry_path(state)  # noqa: SLF001
    registry_path.parent.mkdir(parents=True, exist_ok=True)
    registry_path.write_bytes(b"{malformed-registry}\n")
    retry_id = f"{cell['cell_id']}::retry1"
    _append_journal_rows(admitted, {
        "event": "session", "seq": planned_start["seq"],
        "round": planned_start["round"], "kind": "planned",
        "cell_id": cell["cell_id"], "attempt_id": attempt_id,
        "valid": False, "probe_before": {"competing": True},
    })
    authorization = admission.floor_retry_trigger_for_round(
        admitted, round_no=planned_start["round"],
    )
    assert authorization == admission.FloorRetryAuthorization(
        trigger_attempt_id=attempt_id, source="legacy-failed-session",
    )
    _append_journal_rows(admitted, {
        "event": "session-start", "seq": len(state.schedule),
        "round": planned_start["round"], "kind": "retry",
        "retry_ordinal": 1, "cell_id": cell["cell_id"],
        "attempt_id": retry_id, "trigger": attempt_id,
    })

    token = admission.consume_attempt_ticket(admitted, attempt_id=retry_id)
    assert token.attempt_id == retry_id
    assert token.permitted_run_once_calls == protocol["reps"]
    _append_journal_rows(admitted, {
        "event": "session", "seq": len(state.schedule),
        "round": planned_start["round"], "kind": "retry",
        "retry_ordinal": 1, "cell_id": cell["cell_id"],
        "attempt_id": retry_id, "trigger": attempt_id,
        "valid": True, "probe_before": {"competing": False},
    })
    inspection = admission.inspect_floor_holdout_admission_evidence(
        **_issued_inspection_kwargs(root, protocol, admitted, manifest)
    )
    assert inspection["attempt_row_count"] == 1


def test_verified_registry_recovery_authorizes_exactly_one_retry_ordinal(
    tmp_path, monkeypatch,
):
    _pin_test_recovery_authority(monkeypatch)
    root, protocol, cell, admitted, attempt_id, manifest = _issued_cell(tmp_path)
    admission.consume_attempt_ticket(admitted, attempt_id=attempt_id)
    state = admission._cell_state(admitted)  # noqa: SLF001
    planned_start = json.loads(
        (state.run_dir / "journal.jsonl").read_text(encoding="utf-8")
    )
    _write_verified_recovery_registry(admitted, trigger_start=planned_start)
    authorization = admission.floor_retry_trigger_for_round(
        admitted, round_no=planned_start["round"],
    )
    assert authorization == admission.FloorRetryAuthorization(
        trigger_attempt_id=attempt_id,
        source="verified-registry-recovery",
    )
    retry_id = f"{cell['cell_id']}::retry1"
    _append_journal_rows(admitted, {
        "event": "session-start", "seq": len(state.schedule),
        "round": planned_start["round"], "kind": "retry",
        "retry_ordinal": 1, "cell_id": cell["cell_id"],
        "attempt_id": retry_id, "trigger": attempt_id,
    })

    token = admission.consume_attempt_ticket(admitted, attempt_id=retry_id)
    assert token.attempt_id == retry_id
    assert token.permitted_run_once_calls == protocol["reps"]
    shared = admission.shared_admission_root(root)
    attempts = admission._read_ledger(shared / "attempt-ledger.jsonl")  # noqa: SLF001
    assert [row["attempt_id"] for row in attempts] == [attempt_id, retry_id]
    _append_journal_rows(admitted, {
        "event": "session", "seq": len(state.schedule),
        "round": planned_start["round"], "kind": "retry",
        "retry_ordinal": 1, "cell_id": cell["cell_id"],
        "attempt_id": retry_id, "trigger": attempt_id,
        "valid": True, "probe_before": {"competing": False},
    })
    inspection = admission.inspect_floor_holdout_admission_evidence(
        **_issued_inspection_kwargs(root, protocol, admitted, manifest)
    )
    assert inspection["attempt_row_count"] == 2


def test_registry_recovery_of_retry_attempt_selects_that_attempt_as_trigger(
    tmp_path, monkeypatch,
):
    _pin_test_recovery_authority(monkeypatch)
    root, protocol, cell, admitted, attempt_id, manifest = _issued_cell(tmp_path)
    admission.consume_attempt_ticket(admitted, attempt_id=attempt_id)
    state = admission._cell_state(admitted)  # noqa: SLF001
    planned_start = json.loads(
        (state.run_dir / "journal.jsonl").read_text(encoding="utf-8")
    )
    retry1 = f"{cell['cell_id']}::retry1"
    retry1_start = {
        "event": "session-start", "seq": len(state.schedule),
        "round": planned_start["round"], "kind": "retry",
        "retry_ordinal": 1, "cell_id": cell["cell_id"],
        "attempt_id": retry1, "trigger": attempt_id,
    }
    _append_journal_rows(admitted, retry1_start)
    # The registry contains the prefix recovery for ordinal 0 and the target
    # recovery for ordinal 1.  No valid=False completion is added, so each
    # retry start has exactly one side of the XOR authorization.
    _write_verified_recovery_registry(admitted, trigger_start=retry1_start)
    admission.consume_attempt_ticket(admitted, attempt_id=retry1)

    authorization = admission.floor_retry_trigger_for_round(
        admitted, round_no=planned_start["round"],
    )
    assert authorization == admission.FloorRetryAuthorization(
        trigger_attempt_id=retry1,
        source="verified-registry-recovery",
    )
    retry2 = f"{cell['cell_id']}::retry2"
    _append_journal_rows(admitted, {
        "event": "session-start", "seq": len(state.schedule) + 1,
        "round": planned_start["round"], "kind": "retry",
        "retry_ordinal": 2, "cell_id": cell["cell_id"],
        "attempt_id": retry2, "trigger": retry1,
    })

    token = admission.consume_attempt_ticket(admitted, attempt_id=retry2)
    assert token.attempt_id == retry2
    _append_journal_rows(admitted, {
        "event": "session", "seq": len(state.schedule) + 1,
        "round": planned_start["round"], "kind": "retry",
        "retry_ordinal": 2, "cell_id": cell["cell_id"],
        "attempt_id": retry2, "trigger": retry1,
        "valid": True, "probe_before": {"competing": False},
    })
    inspection = admission.inspect_floor_holdout_admission_evidence(
        **_issued_inspection_kwargs(root, protocol, admitted, manifest)
    )
    assert inspection["attempt_row_count"] == 3


def test_registry_recovery_authority_is_empty_and_fail_closed(tmp_path):
    root, _protocol, cell, admitted, attempt_id, _manifest = _issued_cell(tmp_path)
    assert admission._FLOOR_RECOVERY_AUTHORITIES == frozenset()  # noqa: SLF001
    admission.consume_attempt_ticket(admitted, attempt_id=attempt_id)
    state = admission._cell_state(admitted)  # noqa: SLF001
    planned_start = json.loads(
        (state.run_dir / "journal.jsonl").read_text(encoding="utf-8")
    )
    _write_verified_recovery_registry(admitted, trigger_start=planned_start)
    with pytest.raises(admission.HoldoutAdmissionError, match="authority is not pinned"):
        admission.floor_retry_trigger_for_round(
            admitted, round_no=planned_start["round"],
        )
    assert not any(
        row.get("kind") == "retry"
        for row in admission._read_run_journal(  # noqa: SLF001
            state.run_dir / "journal.jsonl"
        )
    )
    retry_id = f"{cell['cell_id']}::retry1"
    _append_journal_rows(admitted, {
        "event": "session-start", "seq": len(state.schedule),
        "round": planned_start["round"], "kind": "retry",
        "retry_ordinal": 1, "cell_id": cell["cell_id"],
        "attempt_id": retry_id, "trigger": attempt_id,
    })

    with pytest.raises(admission.HoldoutAdmissionError, match="authority is not pinned"):
        admission.consume_attempt_ticket(admitted, attempt_id=retry_id)
    attempts = admission._read_ledger(  # noqa: SLF001
        admission.shared_admission_root(root) / "attempt-ledger.jsonl"
    )
    assert [row["attempt_id"] for row in attempts] == [attempt_id]


@pytest.mark.parametrize("ordinals", [(2,), (1, 2)])
def test_verified_registry_recovery_rejects_non_next_or_multiple_retry_ordinals(
    tmp_path, monkeypatch, ordinals,
):
    _pin_test_recovery_authority(monkeypatch)
    root, _protocol, cell, admitted, attempt_id, _manifest = _issued_cell(tmp_path)
    admission.consume_attempt_ticket(admitted, attempt_id=attempt_id)
    state = admission._cell_state(admitted)  # noqa: SLF001
    planned_start = json.loads(
        (state.run_dir / "journal.jsonl").read_text(encoding="utf-8")
    )
    _write_verified_recovery_registry(admitted, trigger_start=planned_start)
    starts = [
        {
            "event": "session-start", "seq": len(state.schedule) + index,
            "round": planned_start["round"], "kind": "retry",
            "retry_ordinal": ordinal, "cell_id": cell["cell_id"],
            "attempt_id": f"{cell['cell_id']}::retry{ordinal}",
            "trigger": attempt_id,
        }
        for index, ordinal in enumerate(ordinals)
    ]
    _append_journal_rows(admitted, *starts)
    target = f"{cell['cell_id']}::retry{ordinals[-1]}"

    with pytest.raises(admission.HoldoutAdmissionError, match="exactly one next"):
        admission.consume_attempt_ticket(admitted, attempt_id=target)
    attempts = admission._read_ledger(  # noqa: SLF001
        admission.shared_admission_root(root) / "attempt-ledger.jsonl"
    )
    assert [row["attempt_id"] for row in attempts] == [attempt_id]


def test_verified_registry_recovery_rejects_nonlatest_retry_start(
    tmp_path, monkeypatch,
):
    _pin_test_recovery_authority(monkeypatch)
    root, _protocol, cell, admitted, attempt_id, _manifest = _issued_cell(tmp_path)
    admission.consume_attempt_ticket(admitted, attempt_id=attempt_id)
    state = admission._cell_state(admitted)  # noqa: SLF001
    planned_start = json.loads(
        (state.run_dir / "journal.jsonl").read_text(encoding="utf-8")
    )
    _write_verified_recovery_registry(admitted, trigger_start=planned_start)
    retry1 = f"{cell['cell_id']}::retry1"
    retry2 = f"{cell['cell_id']}::retry2"
    _append_journal_rows(
        admitted,
        {
            "event": "session-start", "seq": len(state.schedule),
            "round": planned_start["round"], "kind": "retry",
            "retry_ordinal": 1, "cell_id": cell["cell_id"],
            "attempt_id": retry1, "trigger": attempt_id,
        },
        {
            "event": "session-start", "seq": len(state.schedule) + 1,
            "round": planned_start["round"], "kind": "retry",
            "retry_ordinal": 2, "cell_id": cell["cell_id"],
            "attempt_id": retry2, "trigger": "different-trigger",
        },
    )

    with pytest.raises(admission.HoldoutAdmissionError, match="exactly one next"):
        admission.consume_attempt_ticket(admitted, attempt_id=retry1)
    attempts = admission._read_ledger(  # noqa: SLF001
        admission.shared_admission_root(root) / "attempt-ledger.jsonl"
    )
    assert [row["attempt_id"] for row in attempts] == [attempt_id]


@pytest.mark.parametrize("ordinals", [(2,), (1, 2)])
def test_inspection_rejects_registry_recovery_nonprefix_or_reused_trigger(
    tmp_path, monkeypatch, ordinals,
):
    _pin_test_recovery_authority(monkeypatch)
    root, protocol, cell, admitted, attempt_id, manifest = _issued_cell(tmp_path)
    admission.consume_attempt_ticket(admitted, attempt_id=attempt_id)
    state = admission._cell_state(admitted)  # noqa: SLF001
    planned_start = json.loads(
        (state.run_dir / "journal.jsonl").read_text(encoding="utf-8")
    )
    _write_verified_recovery_registry(admitted, trigger_start=planned_start)
    _append_journal_rows(admitted, *(
        {
            "event": "session-start", "seq": len(state.schedule) + index,
            "round": planned_start["round"], "kind": "retry",
            "retry_ordinal": ordinal, "cell_id": cell["cell_id"],
            "attempt_id": f"{cell['cell_id']}::retry{ordinal}",
            "trigger": attempt_id,
        }
        for index, ordinal in enumerate(ordinals)
    ))

    _assert_evidence_error(
        "mismatch", "session-start-invalid",
        _issued_inspection_kwargs(root, protocol, admitted, manifest),
    )


def test_registry_recovery_without_consumed_trigger_marker_is_rejected(
    tmp_path, monkeypatch,
):
    _pin_test_recovery_authority(monkeypatch)
    root, _protocol, cell, admitted, attempt_id, _manifest = _issued_cell(tmp_path)
    state = admission._cell_state(admitted)  # noqa: SLF001
    planned_start = json.loads(
        (state.run_dir / "journal.jsonl").read_text(encoding="utf-8")
    )
    _write_verified_recovery_registry(admitted, trigger_start=planned_start)
    retry_id = f"{cell['cell_id']}::retry1"
    _append_journal_rows(admitted, {
        "event": "session-start", "seq": len(state.schedule),
        "round": planned_start["round"], "kind": "retry",
        "retry_ordinal": 1, "cell_id": cell["cell_id"],
        "attempt_id": retry_id, "trigger": attempt_id,
    })

    with pytest.raises(admission.HoldoutAdmissionError, match="no consume marker"):
        admission.consume_attempt_ticket(admitted, attempt_id=retry_id)
    assert list((admission.shared_admission_root(root) / "consumed").iterdir()) == []


def test_unverified_registry_recovery_row_is_rejected(tmp_path, monkeypatch):
    _pin_test_recovery_authority(
        monkeypatch, ("tampered", _TEST_RECOVERY_AUTHORITY[1]),
    )
    _root, _protocol, cell, admitted, attempt_id, _manifest = _issued_cell(tmp_path)
    admission.consume_attempt_ticket(admitted, attempt_id=attempt_id)
    state = admission._cell_state(admitted)  # noqa: SLF001
    planned_start = json.loads(
        (state.run_dir / "journal.jsonl").read_text(encoding="utf-8")
    )
    registry_path = _write_verified_recovery_registry(
        admitted, trigger_start=planned_start,
    )
    rows = [json.loads(line) for line in registry_path.read_text().splitlines()]
    recovery = next(row for row in rows if row.get("event") == "recovery")
    recovery["scheduler_accounting_receipt"]["authority_id"] = "tampered"
    registry_path.write_bytes(b"".join(
        attempt_registry_core.canonical_json_bytes(row) + b"\n" for row in rows
    ))
    retry_id = f"{cell['cell_id']}::retry1"
    _append_journal_rows(admitted, {
        "event": "session-start", "seq": len(state.schedule),
        "round": planned_start["round"], "kind": "retry",
        "retry_ordinal": 1, "cell_id": cell["cell_id"],
        "attempt_id": retry_id, "trigger": attempt_id,
    })

    with pytest.raises(admission.HoldoutAdmissionError, match="verification failed"):
        admission.consume_attempt_ticket(admitted, attempt_id=retry_id)


def test_failed_session_and_registry_recovery_evidence_are_mutually_exclusive(tmp_path):
    root, protocol, cell, admitted, attempt_id, manifest = _issued_cell(tmp_path)
    admission.consume_attempt_ticket(admitted, attempt_id=attempt_id)
    state = admission._cell_state(admitted)  # noqa: SLF001
    planned_start = json.loads(
        (state.run_dir / "journal.jsonl").read_text(encoding="utf-8")
    )
    _write_verified_recovery_registry(admitted, trigger_start=planned_start)
    retry_id = f"{cell['cell_id']}::retry1"
    _append_journal_rows(
        admitted,
        {
            "event": "session", "seq": planned_start["seq"],
            "round": planned_start["round"], "kind": "planned",
            "cell_id": cell["cell_id"], "attempt_id": attempt_id,
            "valid": False, "probe_before": {"competing": False},
        },
        {
            "event": "session-start", "seq": len(state.schedule),
            "round": planned_start["round"], "kind": "retry",
            "retry_ordinal": 1, "cell_id": cell["cell_id"],
            "attempt_id": retry_id, "trigger": attempt_id,
        },
    )

    with pytest.raises(admission.HoldoutAdmissionError, match="exactly one"):
        admission.consume_attempt_ticket(admitted, attempt_id=retry_id)
    _assert_evidence_error(
        "mismatch", "session-start-invalid",
        _issued_inspection_kwargs(root, protocol, admitted, manifest),
    )


def test_registry_recovery_from_other_round_cannot_open_retry(
    tmp_path, monkeypatch,
):
    _pin_test_recovery_authority(monkeypatch)
    _root, _protocol, cell, admitted, attempt_id, _manifest = _issued_cell(tmp_path)
    admission.consume_attempt_ticket(admitted, attempt_id=attempt_id)
    state = admission._cell_state(admitted)  # noqa: SLF001
    planned_start = json.loads(
        (state.run_dir / "journal.jsonl").read_text(encoding="utf-8")
    )
    _write_verified_recovery_registry(admitted, trigger_start=planned_start)
    retry_id = f"{cell['cell_id']}::retry1"
    _append_journal_rows(admitted, {
        "event": "session-start", "seq": len(state.schedule),
        "round": planned_start["round"] + 1, "kind": "retry",
        "retry_ordinal": 1, "cell_id": cell["cell_id"],
        "attempt_id": retry_id, "trigger": attempt_id,
    })

    with pytest.raises(admission.HoldoutAdmissionError, match="cell or round"):
        admission.consume_attempt_ticket(admitted, attempt_id=retry_id)


def test_retry_ordinal_above_frozen_attempt_set_is_rejected(tmp_path):
    root, protocol, cell, admitted, attempt_id, _manifest = _issued_cell(tmp_path)
    state = admission._cell_state(admitted)  # noqa: SLF001
    planned_start = json.loads(
        (state.run_dir / "journal.jsonl").read_text(encoding="utf-8")
    )
    ordinal = protocol["retry_slots_per_cell"] + 1
    retry_id = f"{cell['cell_id']}::retry{ordinal}"
    _append_journal_rows(admitted, {
        "event": "session-start", "seq": len(state.schedule),
        "round": planned_start["round"], "kind": "retry",
        "retry_ordinal": ordinal, "cell_id": cell["cell_id"],
        "attempt_id": retry_id, "trigger": attempt_id,
    })

    with pytest.raises(admission.HoldoutAdmissionError, match="frozen ticket set"):
        admission.consume_attempt_ticket(admitted, attempt_id=retry_id)
    assert list((admission.shared_admission_root(root) / "consumed").iterdir()) == []


def test_cell_coordinates_are_evidence_checks_not_extra_key_fields(tmp_path):
    _root, protocol, cell, admitted, _attempt_id, manifest_sha256 = _issued_cell(tmp_path)
    changed = dict(cell)
    changed["records"] += 1
    with pytest.raises(admission.HoldoutAdmissionError, match="records"):
        admission.assert_cell_holdout_admission(
            admitted, cell=changed, protocol=protocol,
            freeze_sha256=protocol["freeze"]["sha256"],
            protocol_sha256=hashlib.sha256(_canonical(protocol)).hexdigest(),
            manifest_sha256=manifest_sha256,
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


def test_canonical_authority_to_run_once_proof_chain_e2e(tmp_path):
    source_root = Path(__file__).resolve().parents[2]
    protocol_raw = (
        source_root / "output/s8b-freeze/floor_protocol.json"
    ).read_bytes()
    freeze_raw = (
        source_root / "output/s8b-freeze/holdout_freeze.json"
    ).read_bytes()
    protocol = json.loads(protocol_raw)
    freeze = json.loads(freeze_raw)

    root = tmp_path / "repo"
    root.mkdir()
    _git(root, "init")
    fixed = root / "output/s8b-freeze"
    fixed.mkdir(parents=True)
    (fixed / "floor_protocol.json").write_bytes(protocol_raw)
    (fixed / "holdout_freeze.json").write_bytes(freeze_raw)
    _git(root, "add", "output/s8b-freeze")
    _git(root, "-c", "user.name=fixture", "-c", "user.email=f@example.invalid",
         "commit", "-m", "real canonical authority")

    cells, schedule = _cells_and_schedule(protocol, freeze)
    out_root = root / "out"
    run_id = "run-e2e"
    run_relpath = f"env/{protocol['env_tag']}/calibration/s8b-floor-pilot/{run_id}"
    run_dir = out_root / run_relpath
    run_dir.mkdir(parents=True)
    protocol_sha256 = hashlib.sha256(protocol_raw).hexdigest()
    manifest_path = run_dir / "manifest.json"
    manifest_path.write_text(json.dumps({
        "protocol_sha256": protocol_sha256,
        "freeze_sha256": protocol["freeze"]["sha256"],
        "reps": protocol["reps"],
    }, sort_keys=True) + "\n", encoding="utf-8")
    manifest_sha256 = hashlib.sha256(manifest_path.read_bytes()).hexdigest()

    with mock.patch.object(
            s8b_floor_campaign, "resolve_current_floor_protocol",
            return_value=_indexed_protocol_record(root),
    ):
        reservation = admission.reserve_floor_holdout_observations(
            repo_root=root, protocol=protocol,
            verified_freeze_document=freeze,
            freeze_sha256=protocol["freeze"]["sha256"],
            cells=cells, schedule=schedule, campaign_run_id=run_id,
            out_root=out_root, run_dir=run_dir, run_relpath=run_relpath,
            mode="pilot", resume=False, nondefault_seams=[],
            irreversible_pilot_approved=True,
        )
    admitted = admission.finalize_floor_holdout_admissions(reservation)
    cell = cells[0]
    scheduled = next(row for row in schedule if row["cell_id"] == cell["cell_id"])
    attempt_id = f"{cell['cell_id']}::seq{scheduled['seq']}"
    (run_dir / "journal.jsonl").write_text(json.dumps({
        "event": "session-start", "seq": scheduled["seq"],
        "round": scheduled["round"], "kind": "planned",
        "cell_id": cell["cell_id"], "attempt_id": attempt_id,
        "trigger": None,
    }, sort_keys=True) + "\n", encoding="utf-8")
    binary = tmp_path / "ccbench-spy"
    binary.write_bytes(b"spy")
    shared = admission.shared_admission_root(root)
    spawns = []

    def subprocess_spy(*_args, **_kwargs):
        assert len(list((shared / "claims").iterdir())) == 12
        assert len(admission._read_ledger(shared / "ledger.jsonl")) == 12
        assert len(list((shared / "consumed").iterdir())) == 1
        assert len(admission._read_ledger(shared / "attempt-ledger.jsonl")) == 1
        spawns.append("run_once")
        return type("Completed", (), {
            "returncode": 0,
            "stdout": "throughput[tps]:\t1000\nmaxrss:\t100 kB\n",
            "stderr": "",
        })()

    def internal_measure(
            measured_binary, _records, _threads, workload, *,
            _holdout_observation_admission):
        return calibrator_runner.run_once(
            measured_binary,
            [f"--ycsb_rratio={workload['ycsb_rratio']}"],
            subprocess_runner=subprocess_spy, use_perf=False,
            holdout_observation_admission=_holdout_observation_admission,
        )

    floor_cell = dict(cell)
    floor_cell["holdout_id"] = floor_cell.pop("freeze_holdout_key")
    wrapped = s8b_floor_campaign._wrap_admission_aware_measure(
        internal_measure,
        admissions={cell["cell_id"]: admitted[cell["cell_id"]]},
        cell_by_id={cell["cell_id"]: floor_cell},
        binaries={cell["cell_id"]: {"binary": str(binary)}},
        protocol=protocol, freeze_sha256=protocol["freeze"]["sha256"],
        protocol_sha256=protocol_sha256, manifest_sha256=manifest_sha256,
        pass_observation_to_internal_measure=True,
    )
    wrapped(
        cell["cell_id"], attempt_id, str(binary), cell["records"],
        cell["threads"], cell["workload"],
    )
    assert spawns == ["run_once"]


def _inspection_case(
    tmp_path: Path, *, competing: bool, session_count: int = 1,
    measurement_head: str = "1" * 40,
    mode: str = "pilot", claim_schema: str = "s8b-holdout-cell-claim/v2",
    entry_kind: str = "fresh", nondefault_seams=(), resume_marker: bool = False,
):
    protocol, freeze = _fixture_documents()
    cells = s8b_floor_contract.enumerate_cells(
        freeze, stock_configuration=protocol["stock_configuration"],
    )
    schedule = s8b_floor_contract.build_schedule(
        cells=cells, master_seed=protocol["master_seed"],
        n_sessions=protocol["n_sessions"],
    )
    cell_by_id = {cell["cell_id"]: cell for cell in cells}
    selected = schedule[:session_count]
    sessions = [{
        "cell_id": row["cell_id"],
        "attempt_id": f"{row['cell_id']}::seq{row['seq']}",
        "probe_before": {"competing": competing},
    } for row in selected if row["cell_id"] in cell_by_id]
    campaign_run_id = "run-inspection"
    run_relpath = f"env/fixture-env/calibration/s8b-floor-{mode}/run-inspection"
    manifest_sha256 = "b" * 64
    root = tmp_path / "admission"
    evidence = build_floor_admission_evidence(
        root, protocol=protocol, freeze=freeze,
        freeze_sha256=protocol["freeze"]["sha256"],
        manifest_sha256=manifest_sha256, campaign_run_id=campaign_run_id,
        run_relpath=run_relpath, mode=mode, cells=cells, schedule=schedule,
        sessions=sessions, measurement_head=measurement_head,
        claim_schema=claim_schema, entry_kind=entry_kind,
        nondefault_seams=nondefault_seams, resume_marker=resume_marker,
    )
    lifecycle = []
    schedule_by_attempt = {
        f"{row['cell_id']}::seq{row['seq']}": row for row in schedule
    }
    for raw_session in sessions:
        scheduled = schedule_by_attempt[raw_session["attempt_id"]]
        lifecycle.append({
            "event": "session-start", "seq": scheduled["seq"],
            "round": scheduled["round"], "kind": "planned",
            "retry_ordinal": None, "cell_id": raw_session["cell_id"],
            "attempt_id": raw_session["attempt_id"], "trigger": None,
        })
        lifecycle.append({
            "event": "session", "kind": "planned", "valid": True,
            **raw_session,
        })
    kwargs = {
        "repo_root": tmp_path,
        "protocol": protocol,
        "verified_freeze_document": freeze,
        "freeze_sha256": protocol["freeze"]["sha256"],
        "manifest_sha256": manifest_sha256,
        "campaign_run_id": campaign_run_id,
        "run_relpath": run_relpath,
        "mode": mode,
        "cells": cells,
        "schedule": schedule,
        "sessions": lifecycle,
    }
    return evidence, kwargs


def _resume_attempt_lifecycle(kwargs: dict) -> list[dict]:
    """Project fixture completions with their prior-run durable authorizations."""

    return [dict(record) for record in kwargs["sessions"]]


def _patch_inspection_root(monkeypatch, root: Path) -> None:
    monkeypatch.setattr(admission, "shared_admission_root", lambda _repo_root: root)
    monkeypatch.setattr(
        admission, "provision_shared_admission_root",
        lambda _repo_root: pytest.fail("read-only inspector must not provision"),
    )


def _assert_evidence_error(category: str, reason: str, kwargs: dict) -> None:
    with pytest.raises(admission.FloorHoldoutEvidenceError) as exc_info:
        admission.inspect_floor_holdout_admission_evidence(**kwargs)
    assert exc_info.value.category == category
    assert exc_info.value.reason == reason


def _rewrite_attempt_evidence(
        evidence, attempt_ids: list[str]) -> None:
    template = dict(evidence.attempt_rows[0])
    consumed_root = evidence.root / "consumed"
    for path in consumed_root.iterdir():
        path.unlink()
    rows = []
    for attempt_id in attempt_ids:
        row = dict(template)
        row["attempt_id"] = attempt_id
        rows.append(row)
        marker_name = hashlib.sha256(attempt_id.encode("utf-8")).hexdigest()
        marker_path = consumed_root / f"{row['claim_digest']}-{marker_name}.json"
        marker_path.write_bytes(canonical_json_line(row))
    (evidence.root / "attempt-ledger.jsonl").write_bytes(
        b"".join(canonical_json_line(row) for row in rows)
    )


def test_inspector_public_contract_and_guarantee_boundary():
    assert "FloorHoldoutEvidenceError" in admission.__all__
    assert "FloorHoldoutEvidenceInspection" in admission.__all__
    assert "inspect_floor_holdout_admission_evidence" in admission.__all__
    parameters = inspect.signature(
        admission.inspect_floor_holdout_admission_evidence
    ).parameters
    assert tuple(parameters) == (
        "repo_root", "protocol", "verified_freeze_document", "freeze_sha256",
        "manifest_sha256", "campaign_run_id", "run_relpath", "mode", "cells",
        "schedule", "sessions",
    )
    doc = inspect.getdoc(admission.inspect_floor_holdout_admission_evidence) or ""
    assert "現在状態だけを見る" in doc
    assert "同一 bytes を再構成する攻撃は検出できない" in doc
    assert "本 wave の保証範囲外" in doc
    assert admission._FLOOR_CLAIM_KEYS_V2 == (  # noqa: SLF001
        admission._FLOOR_CLAIM_KEYS_V1  # noqa: SLF001
        | {"entry_kind", "nondefault_seams"}
    )
    assert "entry_kind" not in admission._FLOOR_CLAIM_KEYS_V1  # noqa: SLF001


def test_inspection_positive_official_fresh_v2_derives_true(tmp_path, monkeypatch):
    evidence, kwargs = _inspection_case(
        tmp_path, competing=True, mode="official",
    )
    _patch_inspection_root(monkeypatch, evidence.root)

    inspection = admission.inspect_floor_holdout_admission_evidence(**kwargs)

    assert inspection == evidence.expected_receipt
    assert inspection.derived_eligible_for_refreeze is True


def test_inspection_positive_legacy_v1_remains_readable_and_conservative(
    tmp_path, monkeypatch,
):
    evidence, kwargs = _inspection_case(
        tmp_path, competing=True, mode="official",
        claim_schema="s8b-holdout-cell-claim/v1",
    )
    _patch_inspection_root(monkeypatch, evidence.root)

    inspection = admission.inspect_floor_holdout_admission_evidence(**kwargs)

    assert inspection == evidence.expected_receipt
    assert inspection.derived_eligible_for_refreeze is False


def test_inspection_positive_legacy_v1_pilot_keeps_receipt_and_is_conservative(
    tmp_path, monkeypatch,
):
    evidence, kwargs = _inspection_case(
        tmp_path, competing=True, mode="pilot",
        claim_schema="s8b-holdout-cell-claim/v1",
    )
    _patch_inspection_root(monkeypatch, evidence.root)

    inspection = admission.inspect_floor_holdout_admission_evidence(**kwargs)

    assert inspection == evidence.expected_receipt
    assert inspection.derived_eligible_for_refreeze is False
    assert all(row["irreversible_pilot_approved"] is True
               for row in evidence.admission_rows)


@pytest.mark.parametrize(
    "seams",
    [
        ["unknown_seam"],
        ["build_fn", "build_fn"],
        ["probe_fn", "measure_fn"],
    ],
    ids=["unknown", "duplicate", "noncanonical-order"],
)
def test_inspection_rejects_noncanonical_or_unknown_v2_seams(
    tmp_path, monkeypatch, seams,
):
    evidence, kwargs = _inspection_case(
        tmp_path, competing=True, mode="official", nondefault_seams=seams,
    )
    _patch_inspection_root(monkeypatch, evidence.root)

    _assert_evidence_error(
        "mismatch", "claim-nondefault-seams-invalid", kwargs,
    )


def test_inspection_v2_nondefault_seam_is_valid_but_disqualifying(
    tmp_path, monkeypatch,
):
    evidence, kwargs = _inspection_case(
        tmp_path, competing=True, mode="official",
        nondefault_seams=["build_fn"],
    )
    _patch_inspection_root(monkeypatch, evidence.root)

    inspection = admission.inspect_floor_holdout_admission_evidence(**kwargs)

    assert inspection == evidence.expected_receipt
    assert inspection.derived_eligible_for_refreeze is False


def test_inspection_resume_marker_is_exact_and_disqualifying(tmp_path, monkeypatch):
    evidence, kwargs = _inspection_case(
        tmp_path, competing=True, mode="official", entry_kind="resume",
        resume_marker=True,
    )
    _patch_inspection_root(monkeypatch, evidence.root)

    inspection = admission.inspect_floor_holdout_admission_evidence(**kwargs)

    assert inspection.derived_eligible_for_refreeze is False


def test_official_fresh_v2_marker_alone_disqualifies_and_live_mismatch_is_exact(
    tmp_path, monkeypatch,
):
    evidence, kwargs = _inspection_case(
        tmp_path, competing=True, mode="official", entry_kind="fresh",
        nondefault_seams=(), resume_marker=True,
    )
    _patch_inspection_root(monkeypatch, evidence.root)

    inspection = admission.inspect_floor_holdout_admission_evidence(**kwargs)

    assert inspection.derived_eligible_for_refreeze is False
    with pytest.raises(admission.FloorHoldoutEvidenceError) as caught:
        s8b_floor_stats.verify_floor_artifact_with_live_admission(
            {"eligible_for_refreeze": True}, {}, expected_binaries=None,
            expected_use_perf=True, **kwargs,
        )
    assert caught.value.category == "mismatch"
    assert caught.value.reason == "refreeze-eligibility-mismatch"


def test_inspection_reports_unknown_schema_only_for_well_formed_claim(
    tmp_path, monkeypatch,
):
    evidence, kwargs = _inspection_case(
        tmp_path, competing=True, mode="official",
    )
    claim_path = next((evidence.root / "claims").iterdir())
    claim = json.loads(claim_path.read_bytes())
    claim["schema_version"] = "s8b-holdout-cell-claim/v999"
    claim_path.write_bytes(canonical_json_line(claim))
    _patch_inspection_root(monkeypatch, evidence.root)

    _assert_evidence_error("mismatch", "claim-schema-unsupported", kwargs)


def test_inspection_maps_malformed_claim_bytes_to_file_mismatch(
    tmp_path, monkeypatch,
):
    evidence, kwargs = _inspection_case(
        tmp_path, competing=True, mode="official",
    )
    claim_path = next((evidence.root / "claims").iterdir())
    claim_path.write_bytes(b"{not-json}\n")
    _patch_inspection_root(monkeypatch, evidence.root)

    _assert_evidence_error("mismatch", "claim-file-mismatch", kwargs)


def test_inspection_rejects_resume_marker_identity_change(tmp_path, monkeypatch):
    evidence, kwargs = _inspection_case(
        tmp_path, competing=True, mode="official", entry_kind="resume",
        resume_marker=True,
    )
    marker_path = next((evidence.root / "refreeze-disqualifications").iterdir())
    marker = json.loads(marker_path.read_bytes())
    marker["run_relpath"] = (
        "env/fixture-env/calibration/s8b-floor-official/other-run"
    )
    marker_path.write_bytes(canonical_json_line(marker))
    _patch_inspection_root(monkeypatch, evidence.root)

    _assert_evidence_error(
        "mismatch", "refreeze-marker-identity-mismatch", kwargs,
    )


def test_inspection_rejects_duplicate_resume_marker(tmp_path, monkeypatch):
    evidence, kwargs = _inspection_case(
        tmp_path, competing=True, mode="official", entry_kind="resume",
        resume_marker=True,
    )
    marker_root = evidence.root / "refreeze-disqualifications"
    marker_path = next(marker_root.iterdir())
    (marker_root / ("f" * 64 + ".json")).write_bytes(marker_path.read_bytes())
    _patch_inspection_root(monkeypatch, evidence.root)

    _assert_evidence_error(
        "mismatch", "refreeze-marker-count-mismatch", kwargs,
    )


def test_inspection_rejects_cell_to_cell_v2_basis_mismatch(tmp_path, monkeypatch):
    evidence, kwargs = _inspection_case(
        tmp_path, competing=True, mode="official",
    )
    claim_path = next((evidence.root / "claims").iterdir())
    claim = json.loads(claim_path.read_bytes())
    claim["nondefault_seams"] = ["build_fn"]
    claim_path.write_bytes(canonical_json_line(claim))
    _patch_inspection_root(monkeypatch, evidence.root)

    _assert_evidence_error("mismatch", "claim-basis-cell-mismatch", kwargs)


def test_inspection_rejects_missing_root(tmp_path, monkeypatch):
    evidence, kwargs = _inspection_case(tmp_path, competing=True)
    missing = tmp_path / "missing-admission"
    _patch_inspection_root(monkeypatch, missing)
    _assert_evidence_error("unverifiable", "root-missing", kwargs)
    assert evidence.root != missing


def test_inspection_rejects_empty_claims_directory(tmp_path, monkeypatch):
    evidence, kwargs = _inspection_case(tmp_path, competing=True)
    for path in (evidence.root / "claims").iterdir():
        path.unlink()
    _patch_inspection_root(monkeypatch, evidence.root)
    _assert_evidence_error("unverifiable", "claims-empty", kwargs)


def test_inspection_rejects_missing_main_ledger(tmp_path, monkeypatch):
    evidence, kwargs = _inspection_case(tmp_path, competing=True)
    (evidence.root / "ledger.jsonl").unlink()
    _patch_inspection_root(monkeypatch, evidence.root)
    _assert_evidence_error("unverifiable", "main-ledger-missing", kwargs)


def test_inspection_rejects_zero_byte_main_ledger(tmp_path, monkeypatch):
    evidence, kwargs = _inspection_case(tmp_path, competing=True)
    (evidence.root / "ledger.jsonl").write_bytes(b"")
    _patch_inspection_root(monkeypatch, evidence.root)
    _assert_evidence_error("mismatch", "main-ledger-empty", kwargs)


def test_inspection_rejects_foreign_campaign_rows_only(tmp_path, monkeypatch):
    evidence, kwargs = _inspection_case(tmp_path, competing=True)
    foreign_rows = []
    for row in evidence.admission_rows:
        foreign = dict(row)
        foreign["campaign_run_id"] = "foreign-campaign"
        foreign_rows.append(foreign)
    (evidence.root / "ledger.jsonl").write_bytes(
        b"".join(canonical_json_line(row) for row in foreign_rows)
    )
    _patch_inspection_root(monkeypatch, evidence.root)
    _assert_evidence_error("mismatch", "main-ledger-campaign-missing", kwargs)


def test_inspection_rejects_empty_cells(tmp_path, monkeypatch):
    evidence, kwargs = _inspection_case(tmp_path, competing=True)
    kwargs["cells"] = []
    _patch_inspection_root(monkeypatch, evidence.root)
    _assert_evidence_error("mismatch", "cells-empty", kwargs)


def test_inspection_rejects_zero_attempt_ledger_when_consumption_expected(
    tmp_path, monkeypatch,
):
    evidence, kwargs = _inspection_case(tmp_path, competing=False)
    (evidence.root / "attempt-ledger.jsonl").write_bytes(b"")
    _patch_inspection_root(monkeypatch, evidence.root)
    _assert_evidence_error("mismatch", "attempt-ledger-empty", kwargs)


def test_inspection_accepts_zero_attempt_rows_only_for_all_preprobe_competing(
    tmp_path, monkeypatch,
):
    evidence, kwargs = _inspection_case(tmp_path, competing=True)
    assert (evidence.root / "attempt-ledger.jsonl").read_bytes() == b""
    _patch_inspection_root(monkeypatch, evidence.root)
    assert admission.inspect_floor_holdout_admission_evidence(
        **kwargs
    ) == evidence.expected_receipt


def test_inspection_resume_accepts_prior_run_crashed_consumption_exact_coverage(
    tmp_path, monkeypatch,
):
    evidence, kwargs = _inspection_case(tmp_path, competing=False)
    # consume 後・session 完了前の crash: durable start/marker/ledger だけが残る。
    kwargs["sessions"] = _resume_attempt_lifecycle(kwargs)[:1]
    _patch_inspection_root(monkeypatch, evidence.root)
    assert admission.inspect_floor_holdout_admission_evidence(
        **kwargs
    ) == evidence.expected_receipt


def test_inspection_resume_rejects_extra_attempt_ledger_row(
    tmp_path, monkeypatch,
):
    evidence, kwargs = _inspection_case(tmp_path, competing=False)
    kwargs["sessions"] = _resume_attempt_lifecycle(kwargs)
    original = evidence.attempt_rows[0]
    extra = dict(original)
    extra["attempt_id"] = next(
        f"{row['cell_id']}::seq{row['seq']}"
        for row in kwargs["schedule"]
        if row["cell_id"] == original["cell_id"]
        and f"{row['cell_id']}::seq{row['seq']}" != original["attempt_id"]
    )
    with (evidence.root / "attempt-ledger.jsonl").open("ab") as stream:
        stream.write(canonical_json_line(extra))
    _patch_inspection_root(monkeypatch, evidence.root)
    _assert_evidence_error(
        "mismatch", "attempt-ledger-coverage-mismatch", kwargs,
    )


def test_inspection_resume_rejects_missing_attempt_ledger_row(
    tmp_path, monkeypatch,
):
    evidence, kwargs = _inspection_case(
        tmp_path, competing=False, session_count=2,
    )
    kwargs["sessions"] = _resume_attempt_lifecycle(kwargs)
    (evidence.root / "attempt-ledger.jsonl").write_bytes(
        canonical_json_line(evidence.attempt_rows[0])
    )
    _patch_inspection_root(monkeypatch, evidence.root)
    _assert_evidence_error(
        "mismatch", "attempt-ledger-coverage-mismatch", kwargs,
    )


def test_inspection_rejects_planned_attempt_id_transplanted_from_another_seq(
        tmp_path, monkeypatch):
    evidence, kwargs = _inspection_case(tmp_path, competing=False)
    start = kwargs["sessions"][0]
    transplanted_schedule = next(
        row for row in kwargs["schedule"]
        if row["cell_id"] == start["cell_id"] and row["seq"] != start["seq"]
    )
    start["seq"] = transplanted_schedule["seq"]
    start["round"] = transplanted_schedule["round"]
    _patch_inspection_root(monkeypatch, evidence.root)

    _assert_evidence_error("mismatch", "session-start-invalid", kwargs)


def test_inspection_rejects_retry_attempt_id_transplanted_from_another_ordinal(
        tmp_path, monkeypatch):
    evidence, kwargs = _inspection_case(tmp_path, competing=False)
    planned_start = kwargs["sessions"][0]
    planned_completion = kwargs["sessions"][1]
    planned_completion["valid"] = False
    planned_completion["probe_before"] = {"competing": True}
    retry_attempt_id = f"{planned_start['cell_id']}::retry1"
    kwargs["sessions"].append({
        "event": "session-start", "seq": len(kwargs["schedule"]),
        "round": planned_start["round"], "kind": "retry",
        "retry_ordinal": 2, "cell_id": planned_start["cell_id"],
        "attempt_id": retry_attempt_id,
        "trigger": planned_start["attempt_id"],
    })
    _rewrite_attempt_evidence(evidence, [retry_attempt_id])
    _patch_inspection_root(monkeypatch, evidence.root)

    _assert_evidence_error("mismatch", "session-start-invalid", kwargs)


def test_inspection_rejects_duplicate_cell_retry_ordinal_with_markers(
        tmp_path, monkeypatch):
    evidence, kwargs = _inspection_case(tmp_path, competing=False)
    planned_start = kwargs["sessions"][0]
    planned_completion = kwargs["sessions"][1]
    planned_completion["valid"] = False
    planned_completion["probe_before"] = {"competing": True}
    retry1 = f"{planned_start['cell_id']}::retry1"
    retry2 = f"{planned_start['cell_id']}::retry2"
    for offset, attempt_id in enumerate((retry1, retry2)):
        kwargs["sessions"].append({
            "event": "session-start", "seq": len(kwargs["schedule"]) + offset,
            "round": planned_start["round"], "kind": "retry",
            "retry_ordinal": 1, "cell_id": planned_start["cell_id"],
            "attempt_id": attempt_id, "trigger": planned_start["attempt_id"],
        })
    _rewrite_attempt_evidence(evidence, [retry1, retry2])
    _patch_inspection_root(monkeypatch, evidence.root)

    _assert_evidence_error("mismatch", "session-start-invalid", kwargs)


def test_inspection_digest_ignores_other_campaign_rows(tmp_path, monkeypatch):
    evidence, kwargs = _inspection_case(tmp_path, competing=False)
    _patch_inspection_root(monkeypatch, evidence.root)
    before = admission.inspect_floor_holdout_admission_evidence(**kwargs)
    foreign_main = dict(evidence.admission_rows[0])
    foreign_main["campaign_run_id"] = "foreign-campaign"
    foreign_attempt = dict(evidence.attempt_rows[0])
    foreign_attempt["campaign_run_id"] = "foreign-campaign"
    with (evidence.root / "ledger.jsonl").open("ab") as stream:
        stream.write(canonical_json_line(foreign_main))
    with (evidence.root / "attempt-ledger.jsonl").open("ab") as stream:
        stream.write(canonical_json_line(foreign_attempt))
    after = admission.inspect_floor_holdout_admission_evidence(**kwargs)
    assert after == before == evidence.expected_receipt


def test_inspection_digest_is_portable_but_measurement_head_stays_exact(
    tmp_path, monkeypatch,
):
    first, first_kwargs = _inspection_case(
        tmp_path / "first", competing=False, measurement_head="1" * 40,
    )
    second, second_kwargs = _inspection_case(
        tmp_path / "second", competing=False, measurement_head="2" * 40,
    )
    _patch_inspection_root(monkeypatch, first.root)
    first_receipt = admission.inspect_floor_holdout_admission_evidence(
        **first_kwargs
    )
    _patch_inspection_root(monkeypatch, second.root)
    second_receipt = admission.inspect_floor_holdout_admission_evidence(
        **second_kwargs
    )
    assert first_receipt == first.expected_receipt
    assert second_receipt == second.expected_receipt
    assert first_receipt == second_receipt

    tampered_rows = [dict(row) for row in first.admission_rows]
    tampered_rows[0]["measurement_head"] = "2" * 40
    (first.root / "ledger.jsonl").write_bytes(
        b"".join(canonical_json_line(row) for row in tampered_rows)
    )
    _patch_inspection_root(monkeypatch, first.root)
    _assert_evidence_error("mismatch", "claim-file-mismatch", first_kwargs)


def test_inspection_accepts_synchronized_non_authoritative_measurement_head_change(
        tmp_path, monkeypatch):
    evidence, kwargs = _inspection_case(
        tmp_path, competing=False, measurement_head="1" * 40,
    )
    changed_head = "2" * 40
    ledger_rows = [dict(row) for row in evidence.admission_rows]
    for row in ledger_rows:
        row["measurement_head"] = changed_head
    (evidence.root / "ledger.jsonl").write_bytes(
        b"".join(canonical_json_line(row) for row in ledger_rows)
    )
    for claim_path in (evidence.root / "claims").iterdir():
        claim = json.loads(claim_path.read_bytes())
        claim["measurement_head"] = changed_head
        claim_path.write_bytes(canonical_json_line(claim))
    _patch_inspection_root(monkeypatch, evidence.root)

    assert admission.inspect_floor_holdout_admission_evidence(
        **kwargs
    ) == evidence.expected_receipt


def test_inspection_rejects_one_sided_measurement_head_change(
        tmp_path, monkeypatch):
    evidence, kwargs = _inspection_case(
        tmp_path, competing=False, measurement_head="1" * 40,
    )
    ledger_rows = [dict(row) for row in evidence.admission_rows]
    ledger_rows[0]["measurement_head"] = "2" * 40
    (evidence.root / "ledger.jsonl").write_bytes(
        b"".join(canonical_json_line(row) for row in ledger_rows)
    )
    _patch_inspection_root(monkeypatch, evidence.root)

    _assert_evidence_error("mismatch", "claim-file-mismatch", kwargs)


def test_inspection_rejects_tampered_claim_file_as_mismatch(tmp_path, monkeypatch):
    evidence, kwargs = _inspection_case(tmp_path, competing=True)
    claim_path = next((evidence.root / "claims").iterdir())
    claim = json.loads(claim_path.read_bytes())
    claim["records"] += 1
    claim_path.write_bytes(canonical_json_line(claim))
    _patch_inspection_root(monkeypatch, evidence.root)
    _assert_evidence_error("mismatch", "claim-file-mismatch", kwargs)


def _run() -> int:
    return pytest.main([__file__, "-q"])


if __name__ == "__main__":
    raise SystemExit(_run())
