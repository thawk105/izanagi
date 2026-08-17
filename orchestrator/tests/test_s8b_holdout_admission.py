# -*- coding: utf-8 -*-
from __future__ import annotations

from concurrent.futures import ProcessPoolExecutor
import hashlib
import inspect
import json
from pathlib import Path
import subprocess

import pytest

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
        nondefault_seams=None):
    cells, schedule = _cells_and_schedule(protocol, freeze)
    out_root = root / "out"
    run_relpath = f"env/fixture-env/calibration/s8b-floor-pilot/{run_id}"
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
    return admission.reserve_floor_holdout_observations(
        repo_root=root, protocol=protocol,
        verified_freeze_document=freeze,
        freeze_sha256=protocol["freeze"]["sha256"],
        cells=cells, schedule=schedule, campaign_run_id=run_id,
        out_root=out_root, run_dir=run_dir, run_relpath=run_relpath,
        mode="pilot", resume=resume,
        nondefault_seams=[] if nondefault_seams is None else nondefault_seams,
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
    assert admission._OBSERVATION_ROLES == frozenset({  # noqa: SLF001
        admission.OBSERVATION_ROLE_FLOOR_CAMPAIGN,
        admission.OBSERVATION_ROLE_N_PILOT,
        admission.OBSERVATION_ROLE_ORACLE_DRIVER,
    })
    assert admission._claim_digest(floor) != admission._claim_digest(oracle)  # noqa: SLF001
    assert len({  # noqa: SLF001 - every producer owns a distinct effect key
        admission._claim_digest(floor),
        admission._claim_digest(oracle),
        admission._claim_digest(n_pilot),
    }) == 3
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
