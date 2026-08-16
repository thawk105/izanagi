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
from orchestrator.campaign import s8b_holdout_admission as admission
from orchestrator.calibrator import runner as calibrator_runner
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
        resume: bool = False, journal_exists: bool = False):
    cells, schedule = _cells_and_schedule(protocol, freeze)
    out_root = root / "out"
    run_relpath = f"env/fixture-env/calibration/s8b-floor-pilot/{run_id}"
    run_dir = out_root / run_relpath
    run_dir.mkdir(parents=True, exist_ok=True)
    manifest_path = run_dir / "manifest.json"
    if not manifest_path.exists():
        manifest_path.write_text(json.dumps({
            "schema_version": "s8b-floor-manifest/v2",
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
        mode="pilot", resume=resume, irreversible_pilot_approved=True,
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
    assert admission._claim_digest(floor) != admission._claim_digest(oracle)  # noqa: SLF001
    with pytest.raises(admission.HoldoutAdmissionError, match="not recognized"):
        admission._key_fields(  # noqa: SLF001 - unknown role must fail closed
            **common, observation_role="caller_selected_role",
        )


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
            mode="pilot", resume=False, irreversible_pilot_approved=False,
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
        mode="pilot", resume=False, irreversible_pilot_approved=True,
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


def _run() -> int:
    return pytest.main([__file__, "-q"])


if __name__ == "__main__":
    raise SystemExit(_run())
