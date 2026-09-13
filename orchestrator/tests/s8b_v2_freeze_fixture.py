# -*- coding: utf-8 -*-
"""strict v2 freeze fixture: per-pair floor table + budget 充填形 (C3-4)。

manifest / driver / report の 3 群テストが共有する。実 freeze document の
``holdouts[h].variant_binding.entries`` の key 集合 (= 構成集合) から stock 構成
(``stock_common``) を除いた集合を pair key として per-pair floor を組む。scalar (v1)
形は使わない。verifier 側 (s8b_oracle_manifest._validate_holdout_floor) の per-pair
exact 検査を満たす正例を単一源で生成し、各テストの fixture 分岐を防ぐ。
"""
from __future__ import annotations

import hashlib
import json
import shutil
import subprocess
from pathlib import Path
from typing import Callable, Mapping, Optional, Sequence

from orchestrator.campaign import s8b_floor_contract as _floor_contract
from orchestrator.campaign import s8b_expected_materialization as _snapshot

# Save the real protection functions before floor fixtures install their
# unrelated synthetic declaration-replay seams.
_REAL_ASSERT_MATERIALIZATION = _snapshot.assert_expected_materialization
_REAL_PROTECT_SNAPSHOT = _snapshot.make_snapshot_non_writable
_REAL_RESTORE_SNAPSHOT = _snapshot.restore_snapshot_permissions


# manifest verifier のハードコード stock 名と一致させる (両者とも freeze 記録値に
# stock_common が実在することを別途検査する)。
STOCK_CONFIGURATION = "stock_common"


def holdout_configuration_ids(document, holdout_id) -> set:
    """freeze の当該 holdout の構成集合 (variant_binding.entries の key 集合)。"""
    return set(document["holdouts"][holdout_id]["variant_binding"]["entries"])


def per_pair_floor(document, *, value: float = 0.01,
                   scale_ref: Optional[float] = 100.0) -> dict:
    """全 holdout・全 pair を同一有限正 ``value`` で満たした per-pair floor table。

    各 holdout 値 = exact 3 keys {pairs, scale_ref, scalar_alt}。pairs の key 集合 =
    構成集合 − stock。scalar_alt = max(pairs) (全 pair 非 null のとき)。
    """
    by_holdout = {}
    for holdout_id in document["holdouts"]:
        configs = holdout_configuration_ids(document, holdout_id)
        pairs = {cfg: value for cfg in sorted(configs - {STOCK_CONFIGURATION})}
        scalar_alt = max(pairs.values()) if pairs else None
        by_holdout[holdout_id] = {
            "pairs": pairs,
            "scale_ref": scale_ref,
            "scalar_alt": scalar_alt,
        }
    return {"by_holdout": by_holdout}


def budget(document, *, total_bench_s: float = 100.0,
           per_holdout_bench_s: float = 50.0) -> dict:
    """oracle 共有 budget (per_holdout は全 holdout 一律)。"""
    return {
        "total_bench_s": total_bench_s,
        "per_holdout_bench_s": {
            holdout_id: per_holdout_bench_s for holdout_id in document["holdouts"]
        },
        "oracle_shared": True,
    }


def fill(document, *, total_bench_s: float = 100.0,
         per_holdout_bench_s: float = 50.0, floor_value: float = 0.01,
         scale_ref: Optional[float] = 100.0) -> dict:
    """document に per-pair floor と budget を in-place 充填して返す。"""
    document["floor"] = per_pair_floor(
        document, value=floor_value, scale_ref=scale_ref,
    )
    document["budget"] = budget(
        document, total_bench_s=total_bench_s,
        per_holdout_bench_s=per_holdout_bench_s,
    )
    return document


def canonical_bytes(value) -> bytes:
    return json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")


def in_sealed_fixture_process(test):
    """Keep real seal issuance and all test assertions in one single-thread child.

    Fork the test body, not the capability: issuance records are PID-bound and
    must never be transported back into the xdist worker. Fixture arguments and
    installed monkeypatches are inherited; assertions and spies run in the child.
    Only the failure traceback returns to pytest. No skip/xfail conversion.
    """
    import functools
    import os
    import traceback

    @functools.wraps(test)
    def run(*args, **kwargs):
        read_fd, write_fd = os.pipe()
        try:
            pid = os.fork()
        except BaseException:
            os.close(read_fd)
            os.close(write_fd)
            raise
        if pid == 0:
            os.close(read_fd)
            status = 0
            with os.fdopen(write_fd, "w", encoding="utf-8") as report:
                try:
                    test(*args, **kwargs)
                except BaseException:
                    status = 1
                    report.write(traceback.format_exc())
            os._exit(status)
        os.close(write_fd)
        try:
            with os.fdopen(read_fd, encoding="utf-8") as report:
                failure = report.read()
        finally:
            _, status = os.waitpid(pid, 0)
        assert status == 0, failure or f"sealed fixture child wait status: {status}"
    return run


def run_sealed_fixture_case(module, case, tmp_path, **parameters):
    """Run issuer and assertions in a fresh interpreter, never in an xdist worker."""
    import sys
    code = """
import contextlib, importlib, inspect, io, json, sys
from pathlib import Path
sys.path.insert(0, sys.argv[1])
case = inspect.unwrap(getattr(importlib.import_module(sys.argv[2]), sys.argv[3]))
parameters = json.loads(sys.argv[5])
parameters['tmp_path'] = Path(sys.argv[4])
import pytest
output = io.StringIO()
try:
    with contextlib.redirect_stdout(output), pytest.MonkeyPatch.context() as patch:
        if 'monkeypatch' in inspect.signature(case).parameters:
            parameters['monkeypatch'] = patch
        result = case(**parameters)
finally:
    print(output.getvalue(), file=sys.stderr, end='')
print(json.dumps(result))
"""
    result = subprocess.run(
        [sys.executable, "-I", "-B", "-c", code,
         str(Path(__file__).resolve().parents[2]), module, case,
         str(tmp_path), json.dumps(parameters)],
        capture_output=True, text=True, timeout=5,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    return json.loads(result.stdout)


def in_fresh_sealed_fixture_process(test):
    """Only completion data crosses processes; PID-bound capabilities stay local."""
    import functools
    import inspect

    @functools.wraps(test)
    def run(*args, **kwargs):
        parameters = dict(inspect.signature(test).bind(*args, **kwargs).arguments)
        tmp_path = parameters.pop("tmp_path")
        parameters.pop("monkeypatch", None)
        return run_sealed_fixture_case(
            test.__module__, test.__name__, tmp_path, **parameters,
        )
    return run


def sealed_source_protection_fixture(
        *, source, binary_sha256, compiler_input_manifest_sha256):
    """Issue through a real tiny sealed session; no issuer/registry bypass.

    Only Git replay and evidence derivation use synthetic fixture inputs. Restore
    real snapshot checks locally even when a caller mocks declaration admission.
    These pre-existing fixture bytes use SEALED_CACHE_HIT: no compile is claimed.
    """
    from unittest.mock import patch

    root = Path(source.source_root)
    digest = _snapshot.snapshot_tree_digest(root)
    with patch.object(
            _snapshot, "produce_expected_materialization_from_declaration",
            return_value=digest), patch.object(
            _snapshot.source_digest, "resolve_evidence", return_value=source), patch.object(
            _snapshot, "assert_expected_materialization", _REAL_ASSERT_MATERIALIZATION), patch.object(
            _snapshot, "make_snapshot_non_writable", _REAL_PROTECT_SNAPSHOT), patch.object(
            _snapshot, "restore_snapshot_permissions", _REAL_RESTORE_SNAPSHOT):
        with _snapshot.sealed_build_session(
                ccbench_commit=source.ccbench_commit, configuration="stock_common",
                declaration={}, snapshot_root=root, genome=None,
                prepared_src_token=source.src_token, cxx="c++",
                shared_directories=()) as session:
            pass
    return session.issue(
        _snapshot.SealedSnapshotProtectionKind.SEALED_CACHE_HIT,
        binary_sha256=binary_sha256,
        compiler_input_manifest_sha256=compiler_input_manifest_sha256,
    )


def portable_binary_admission_receipt_fixture(
        *, admission, expected_policy, source, cell_id, holdout_id,
        configuration_id, binding, binary, binary_sha256, contract_sha256,
        trace, source_snapshot_sha256, expected_materialization_sha256,
        compiler_input_manifest, compiler_input_manifest_sha256,
        source_protection=None, current_compiler_input_masstree_root=None,
        current_compiler_input_dependency_prefix_roots=None):
    """Portable reader input only; this dict makes no capability issuance claim.

    Keep issuer tests on the real API. Consumer fixtures need only the durable
    schema, including its internally consistent source protection projection.
    """
    source_body = source.as_receipt()
    source_body.pop("source_root")
    admission_body = admission.as_wal_receipt()
    body = {
        "schema": "s8b-binary-admission/v3",
        "admission": {
            key: admission_body[key] for key in (
                "schema", "class", "policy_sha256", "review_id", "input_sha256",
            )
        },
        "subject": {
            "cell_id": cell_id, "holdout_id": holdout_id,
            "configuration_id": configuration_id,
            "entry_sha256": binding["entry_sha256"],
            "binding_sha256": binding["binding_sha256"],
            "binary_sha256": binary_sha256, "contract_sha256": contract_sha256,
            "trace": trace, "source_snapshot_sha256": source_snapshot_sha256,
            "expected_materialization_sha256": expected_materialization_sha256,
            "compiler_input_manifest_sha256": compiler_input_manifest_sha256,
        },
        "proof": {
            "compiler_input_manifest": compiler_input_manifest,
            "materialization_binding": dict(binding),
            "source_protection": {
                "kind": "sealed-build",
                "source_snapshot_sha256": source_snapshot_sha256,
                "expected_materialization_sha256": expected_materialization_sha256,
                "binary_sha256": binary_sha256,
                "compiler_input_manifest_sha256": compiler_input_manifest_sha256,
            },
        },
    }
    body["admission"]["source"] = source_body
    body["receipt_sha256"] = hashlib.sha256(json.dumps(
        body, ensure_ascii=True, sort_keys=True, separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")).hexdigest()
    return body


def launch_certificate(*, protocol_sha256: str, campaign_run_id: str) -> dict:
    """official path の秒と一致する test-local な実 certificate を組み立てる。"""
    timestamp = campaign_run_id.split("-", 1)[0]
    started_utc = (
        f"{timestamp[0:4]}-{timestamp[4:6]}-{timestamp[6:8]}T"
        f"{timestamp[9:11]}:{timestamp[11:13]}:{timestamp[13:15]}+00:00"
    )
    return {
        "schema": "s8b-floor-launch-certificate/v1",
        "v1_freeze_sha256": (
            "315b1eb83d6fbdc525448c3c96c66ab6013df72487f35d8fa519c27ba34bc688"
        ),
        "clean_scan_digest": "0" * 64,
        "protocol_sha256": protocol_sha256,
        "started_utc": started_utc,
        "campaign_run_id": campaign_run_id,
    }


def _git(root: Path, *args: str) -> str:
    return subprocess.run(
        ["git", *args], cwd=root, check=True, text=True,
        stdout=subprocess.PIPE, stderr=subprocess.PIPE,
    ).stdout.strip()


def _write(root: Path, rel: str, raw: bytes) -> None:
    path = root / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(raw)


def _holdout_hit_text(module, holdout_id: str) -> bytes:
    ycsb = module.HOLDOUTS[holdout_id]["ycsb"]
    values = {
        "rratio": ycsb[module.RRATIO_KEY],
        "skew": ycsb[module.SKEW_KEY],
        "rmw": ycsb[module.RMW_KEY],
    }
    text = "\n".join(
        module.concrete_axis_encodings(axis, value)[0]
        for axis, value in values.items()
    ) + "\n"
    return text.encode("utf-8")


def _synthetic_floor_result(v1: dict, protocol: dict, *, root: Path) -> dict:
    from orchestrator.campaign import s8b_floor_contract as contract
    from orchestrator.campaign import s8b_floor_stats as stats
    from orchestrator.campaign import s8b_binary_admission as binary_admission
    from orchestrator.campaign.build_admission import (
        GeneratorId, ReviewId, build_run_context, derive_build_admission,
    )
    from orchestrator.campaign.s8b_materialization import reviewed_source_capability
    from orchestrator.campaign.source_digest import SOURCE_EVIDENCE_SCHEMA, SourceEvidence
    from orchestrator.tests.s8b_floor_evidence_fixture import (
        expected_portable_sort_swo_pass_receipt,
    )

    cells = contract.enumerate_cells(
        v1, stock_configuration=protocol["stock_configuration"],
    )
    schedule = contract.build_schedule(
        cells=cells, master_seed=protocol["master_seed"],
        n_sessions=protocol["n_sessions"],
    )
    cells_by_id = {cell["cell_id"]: cell for cell in cells}
    sessions = []
    records_by_cell = {cell["cell_id"]: [] for cell in cells}
    for scheduled in schedule:
        cell = cells_by_id[scheduled["cell_id"]]
        seq = scheduled["seq"]
        observations = [
            {
                "rep_index": index, "returncode": 0,
                "execution_failure": False,
                "counter_status": "complete", "missing_perf_events": [],
                "perf_raw": {
                    "LLC-load-misses": 1, "LLC-loads": 2,
                    "instructions": 3, "cycles": 4,
                },
                "throughput": 1000.0,
            }
            for index in range(protocol["reps"])
        ]
        row = {
            "event": "session", "kind": "planned", "round": scheduled["round"],
            "retry_ordinal": None, "trigger": None,
            "cell_id": cell["cell_id"], "holdout_id": cell["holdout_id"],
            "configuration_id": cell["configuration_id"], "seq": seq,
            "throughputs": [1000.0] * protocol["reps"],
            "reps_expected": protocol["reps"], "exec_failures": 0,
            "excluded_reason": None, "retry": False,
            "rep_observations": observations, "rep_integrity_failures": 0,
            "exclusion_class": None,
            "attempt_id": f"{cell['cell_id']}::seq{seq}",
            "probe_before": {"competing": False},
        }
        sessions.append(row)
        records_by_cell[cell["cell_id"]].append(stats.SessionRecord(
            cell_id=row["cell_id"], holdout_id=row["holdout_id"],
            configuration_id=row["configuration_id"], seq=row["seq"],
            throughputs=tuple(row["throughputs"]),
            reps_expected=row["reps_expected"], exec_failures=0,
            excluded_reason=None, retry=False,
            rep_observations=tuple(observations), rep_integrity_failures=0,
        ))
    by_cell = {}
    for cell_id, records in records_by_cell.items():
        by_cell[cell_id] = stats.cell_stats(
            records,
            n_sessions=protocol["n_sessions"],
            reps=protocol["reps"],
            session_cv_max=protocol["session_cv_max"],
        )

    cells_out = {
        cell_id: {
            "holdout_id": value.holdout_id,
            "configuration_id": value.configuration_id,
            "n_valid": value.n_valid,
            "medians": list(value.medians),
            "m": value.m,
            "s": value.s,
            "valid": value.valid,
            "cv": value.cv,
            "notes": list(value.notes),
        }
        for cell_id, value in by_cell.items()
    }
    floors = {}
    for holdout_id in sorted(v1["holdouts"]):
        holdout_cells = {
            cell_id: value for cell_id, value in by_cell.items()
            if value.holdout_id == holdout_id
        }
        value = stats.holdout_floors(
            holdout_cells,
            stock_id=f"{holdout_id}::{protocol['stock_configuration']}",
            wired_min_rel_floor=protocol["wired_min_rel_floor"],
            cell_cv_max=protocol["cell_cv_max"],
        )
        floors[holdout_id] = {
            "pairs": dict(value.pairs),
            "scalar_alt": value.scalar_alt,
            "scale_ref": value.scale_ref,
            "diagnostics": value.diagnostics,
        }
    binaries = {}
    for cell in cells:
        entry = v1["holdouts"][cell["holdout_id"]]["variant_binding"]["entries"][
            cell["configuration_id"]
        ]
        entry_sha256 = hashlib.sha256(canonical_bytes(entry)).hexdigest()
        genome_canonical = json.dumps(
            {"fixture_configuration": cell["configuration_id"]}, ensure_ascii=False,
            sort_keys=True, separators=(",", ":"),
        )
        src_token = hashlib.sha256(
            f"fixture-source:{cell['configuration_id']}".encode("utf-8")
        ).hexdigest()
        binding = {
            "genome_canonical": genome_canonical,
            "src_token": src_token,
            "variant_id": hashlib.sha256(
                f"{genome_canonical}|src={src_token}".encode("utf-8")
            ).hexdigest()[:12],
            "entry_sha256": entry_sha256,
        }
        binding["binding_sha256"] = hashlib.sha256(canonical_bytes(binding)).hexdigest()
        binary_raw = f"honest binary for {cell['configuration_id']}\n".encode("utf-8")
        sha256 = hashlib.sha256(binary_raw).hexdigest()
        binary_rel = f"fixture-binaries/{cell['cell_id'].replace('::', '--')}"
        binary_path = root / binary_rel
        _write(root, binary_rel, binary_raw)
        compiler_input_rel = "fixture.txt"
        compiler_input_raw = (
            root / "external/ccbench" / compiler_input_rel
        ).read_bytes()
        compiler_input_manifest = {
            "schema_version": "s8b-compiler-input/v1",
            "metadata_schema": "cmake-unix-makefiles-cxx-depfile/v1",
            "target": "ycsb_fixture.exe",
            "depfile_count": 1,
            "inputs": [{
                "path": compiler_input_rel,
                "sha256": hashlib.sha256(compiler_input_raw).hexdigest(),
            }],
        }
        compiler_input_manifest_sha256 = hashlib.sha256(
            json.dumps(
                compiler_input_manifest, ensure_ascii=True, sort_keys=True,
                separators=(",", ":"),
            ).encode("utf-8")
        ).hexdigest()
        source = SourceEvidence(
            schema_version=SOURCE_EVIDENCE_SCHEMA,
            source_root=str((root / "external/ccbench").resolve()),
            ccbench_commit=protocol["ccbench_pin"],
            genome_sha256=hashlib.sha256(genome_canonical.encode("utf-8")).hexdigest(),
            src_token=src_token,
            source_bytes_sha256=hashlib.sha256(
                f"source-bytes:{cell['configuration_id']}".encode("utf-8")
            ).hexdigest(),
            tracked_clean=False,
            tracked_diff_sha256=hashlib.sha256(
                f"tracked-diff:{cell['configuration_id']}".encode("utf-8")
            ).hexdigest(),
            tracked_paths=("include/backoff.hh",),
        )
        context = build_run_context(generator_id=GeneratorId.S8A_TRIGGER_SWEEP)
        review = reviewed_source_capability(
            review_id=ReviewId.S8B_FLOOR, source=source,
            input_sha256=entry_sha256,
        )
        admission = derive_build_admission(context, source, review_receipt=review)
        receipt = portable_binary_admission_receipt_fixture(
            admission=admission, expected_policy=context.policy, source=source,
            cell_id=cell["cell_id"], holdout_id=cell["holdout_id"],
            configuration_id=cell["configuration_id"], binding=binding,
            binary=binary_path, binary_sha256=sha256,
            contract_sha256=protocol["contract_sha256"], trace=False,
            source_snapshot_sha256=hashlib.sha256(
                f"expected-materialization:{cell['cell_id']}".encode("utf-8")
            ).hexdigest(),
            expected_materialization_sha256=hashlib.sha256(
                f"expected-materialization:{cell['cell_id']}".encode("utf-8")
            ).hexdigest(),
            compiler_input_manifest=compiler_input_manifest,
            compiler_input_manifest_sha256=compiler_input_manifest_sha256,
        )
        record = {
            "cell_id": cell["cell_id"],
            "holdout_id": cell["holdout_id"],
            "configuration_id": cell["configuration_id"],
            "binary": binary_rel,
            "binary_sha256": sha256,
            "bin_hash_short": sha256[:16],
            "binding": binding,
            "configure_argv": ["cmake", "fixture"],
            "build_argv": ["cmake", "--build", "fixture"],
            "cached": False,
            "store_path": f"fixture-store/{sha256}",
            "admission_receipt": receipt,
        }
        if cell["configuration_id"] == "sort_best":
            record["sort_swo_oracle"] = expected_portable_sort_swo_pass_receipt(
                cell_id=cell["cell_id"], holdout_id=cell["holdout_id"],
                configuration_id=cell["configuration_id"],
                entry_sha256=entry_sha256, binary_sha256=sha256,
            )
        binaries[cell["cell_id"]] = record
    for session in sessions:
        session["binary_sha256_at_measure"] = binaries[
            session["cell_id"]
        ]["binary_sha256"]
    protocol_sha256 = contract.canonical_protocol_sha256(protocol)
    configurations = sorted({cell["configuration_id"] for cell in cells})
    return {
        "schema": contract.LEGACY_RESULT_SCHEMA,
        "formula": protocol["formula"],
        "mode": "official",
        "eligible_for_refreeze": True,
        "env_tag": protocol["env_tag"],
        "ccbench_pin": protocol["ccbench_pin"],
        "protocol_sha256": protocol_sha256,
        "freeze_sha256": protocol["freeze"]["sha256"],
        "manifest_sha256": "0" * 64,
        "stock_configuration": protocol["stock_configuration"],
        "wired_min_rel_floor": protocol["wired_min_rel_floor"],
        "reps": protocol["reps"],
        "n_sessions": protocol["n_sessions"],
        "scale_adequacy_rel_tolerance": protocol["scale_adequacy_rel_tolerance"],
        "holdouts": sorted(v1["holdouts"]),
        "configurations": configurations,
        "binaries": binaries,
        "config": contract.project_protocol_for_floor_artifact(protocol),
        "sessions": sessions,
        "cells": cells_out,
        "floors": floors,
        "wall_ledger": [],
        "excluded": [],
        "attempts": [],
    }


def attach_v5_attempt_registry(
        *, root: Path, freeze: Mapping[str, object],
        protocol: Mapping[str, object], cells: Sequence[Mapping[str, object]],
        schedule: Sequence[Mapping[str, object]], result: dict,
        manifest_raw: bytes, run_dir: str,
        journal_records: Sequence[Mapping[str, object]]) -> dict[str, object]:
    """実 writer と issued marker で v5 の pinned-prefix fixture を作る。"""
    from orchestrator.campaign import s8b_attempt_registry as registry
    from orchestrator.campaign import s8b_floor_attempt_launcher as launcher
    from orchestrator.campaign import s8b_floor_campaign as campaign
    from orchestrator.campaign import s8b_floor_contract as contract
    from orchestrator.campaign import s8b_holdout_admission as admission

    repo_root = Path(root)
    output_root = repo_root / "output"
    relative_run_dir = run_dir.removeprefix("output/")
    absolute_run_dir = output_root / relative_run_dir
    campaign_run_id = absolute_run_dir.name
    manifest_sha256 = hashlib.sha256(manifest_raw).hexdigest()
    admission_root = repo_root / ".git/izanagi/s8b-holdout-admission-v1"
    if admission_root.exists():
        shutil.rmtree(admission_root)

    _write(repo_root, f"{run_dir}/manifest.json", manifest_raw)
    _write(repo_root, f"{run_dir}/journal.jsonl", b"")
    admission_cells = [
        {
            "cell_id": cell["cell_id"],
            "freeze_holdout_key": cell["holdout_id"],
            "configuration_id": cell["configuration_id"],
            "records": cell["records"],
            "threads": cell["threads"],
            "workload": dict(cell["workload"]),
        }
        for cell in cells
    ]
    reservation = admission.reserve_floor_holdout_observations(
        repo_root=repo_root, protocol=protocol,
        verified_freeze_document=freeze,
        freeze_sha256=str(protocol["freeze"]["sha256"]),
        cells=admission_cells, schedule=schedule,
        campaign_run_id=campaign_run_id, out_root=output_root,
        run_dir=absolute_run_dir, run_relpath=relative_run_dir,
        mode="official", resume=False, nondefault_seams=[],
    )
    admissions = admission.finalize_floor_holdout_admissions(reservation)
    starts = [
        dict(record) for record in journal_records
        if record.get("event") == "session-start"
    ]
    _write(repo_root, f"{run_dir}/journal.jsonl", b"".join(
        canonical_bytes(record) + b"\n" for record in starts
    ))

    markers = {}
    for session in result["sessions"]:
        cell_admission = admissions[session["cell_id"]]
        admission.consume_attempt_ticket(
            cell_admission, attempt_id=session["attempt_id"],
        )
        markers[session["attempt_id"]] = (
            admission.validate_floor_attempt_consumption_marker(
                cell_admission, attempt_id=session["attempt_id"],
            )
        )

    protocol_sha256 = contract.canonical_protocol_sha256(protocol)
    plan = campaign._build_floor_attempt_registry_plan(  # noqa: SLF001
        protocol=protocol, cells=cells, schedule=schedule,
        freeze_sha256=str(protocol["freeze"]["sha256"]),
        protocol_sha256=protocol_sha256,
    )
    genesis = launcher.floor_attempt_registry_genesis(plan)
    cells_by_id = {str(cell["cell_id"]): cell for cell in cells}
    schedule_by_seq = {int(row["seq"]): row for row in schedule}
    requests = []
    for index, session in enumerate(result["sessions"][:2]):
        scheduled = schedule_by_seq[int(session["seq"])]
        cell = cells_by_id[str(session["cell_id"])]
        cell_admission = admissions[str(session["cell_id"])]
        requests.append(launcher.floor_attempt_reservation(
            plan,
            slot_key=(str(session["cell_id"]), int(scheduled["round"]), 0),
            repo_root=repo_root, protocol=protocol, mode="official",
            perf_preflight_receipt=result.get("perf_preflight"),
            consumption_marker=markers[session["attempt_id"]],
            run_start_receipt_sha256=launcher.canonical_floor_payload_sha256({
                "fixture": "v5-prefix", "index": index,
            }),
            process_identity={
                "pid": index + 1,
                "starttime": f"fixture-start-{index}",
                "execution_uuid": f"fixture-execution-{index}",
            },
            started_at=f"2026-08-11T00:00:0{index}+00:00",
            admission_claim_digest=str(
                cell_admission.measurement_generation_claim_digest
            ),
            attempt_id=str(session["attempt_id"]),
            campaign_run_id=campaign_run_id,
            manifest_sha256=manifest_sha256,
            run_relpath=relative_run_dir,
            cell_id=str(session["cell_id"]),
            records=int(cell["records"]), threads=int(cell["threads"]),
            workload=dict(cell["workload"]),
        ))
    if len(requests) != 2 or requests[0].slot_id == requests[1].slot_id:
        raise AssertionError("v5 fixture requires two distinct planned slots")

    first = requests[0]
    registry_path = registry.create_attempt_registry(
        repo_root, profile=first.profile, slots=genesis.slots,
        binding=first.binding,
    )

    def reserve(request) -> None:
        registry.reserve_attempt_slot(
            repo_root, profile=request.profile, binding=request.binding,
            slot_id=request.slot_id,
            run_start_receipt_sha256=request.run_start_receipt_sha256,
            process_identity=request.process_identity,
            started_at=request.started_at,
            admission_claim_digest=request.admission_claim_digest,
            attempt_id=request.attempt_id,
            campaign_run_id=request.campaign_run_id,
            manifest_sha256=request.manifest_sha256,
            run_relpath=request.run_relpath, cell_id=request.cell_id,
            deferred_output_reader=lambda: b"fixture-reserved-output",
            launcher_origin_capability=(
                registry._new_launcher_origin_capability()  # noqa: SLF001
            ),
            consumption_marker=request.consumption_marker,
        )

    reserve(first)
    proof = campaign._capture_floor_attempt_registry_prefix(  # noqa: SLF001
        repo_root, plan,
    )
    if int(proof["row_count"]) < 3:
        raise AssertionError("v5 fixture prefix must include a reservation")
    reserve(requests[1])

    _write(repo_root, f"{run_dir}/journal.jsonl", b"".join(
        canonical_bytes(record) + b"\n" for record in journal_records
    ))
    inspection = admission.inspect_floor_holdout_admission_evidence(
        repo_root=repo_root, protocol=protocol,
        verified_freeze_document=freeze,
        freeze_sha256=str(protocol["freeze"]["sha256"]),
        manifest_sha256=manifest_sha256,
        campaign_run_id=campaign_run_id, run_relpath=relative_run_dir,
        mode="official", cells=cells, schedule=schedule,
        sessions=[
            record for record in journal_records
            if record.get("event") in {"session-start", "session"}
        ],
    )
    if inspection.derived_eligible_for_refreeze is not True:
        raise AssertionError("v5 fixture admission must remain refreeze-eligible")
    result["schema"] = contract.RESULT_SCHEMA_V5
    result["holdout_admission"] = dict(inspection)
    result["attempt_registry"] = proof
    live_rows = launcher.read_floor_attempt_registry(repo_root, plan)
    return {
        "proof": proof,
        "registry_path": registry_path,
        "live_row_count": len(live_rows),
    }


def candidate_repository(
        tmp_path: Path, module, *, manifest_kind: str = "v3",
        result_schema: str = _floor_contract.LEGACY_RESULT_SCHEMA,
        mutate_attempt_registry: Optional[Callable[[dict], None]] = None) -> dict:
    """v2 producer 正例用の synthetic-only tmp git repository を作る。"""
    from orchestrator.campaign import env_contract
    from orchestrator.campaign import s8b_floor_contract as contract

    if result_schema not in {
        contract.LEGACY_RESULT_SCHEMA, contract.RESULT_SCHEMA_V5,
    }:
        raise ValueError(f"unknown result_schema: {result_schema}")
    if mutate_attempt_registry is not None and result_schema != contract.RESULT_SCHEMA_V5:
        raise ValueError("attempt registry mutation requires result v5")

    root = tmp_path / "candidate-repo"
    root.mkdir()
    _git(root, "init", "-q")
    _git(root, "config", "user.name", "fixture")
    _git(root, "config", "user.email", "fixture@example.invalid")

    source_root = Path(module.ROOT)
    for rel in (
        module.FREEZE_REL,
        module.DESIGN_REL,
        module.KNOWN_AXES_REL,
        module.SCRIPT_REL,
        module.FLOOR_PROTOCOL_REL,
    ):
        source = source_root / rel
        destination = root / rel
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, destination)

    ccbench = root / "external" / "ccbench"
    ccbench.mkdir(parents=True)
    _git(ccbench, "init", "-q")
    _git(ccbench, "config", "user.name", "fixture")
    _git(ccbench, "config", "user.email", "fixture@example.invalid")
    (ccbench / "fixture.txt").write_text("fixture\n", encoding="utf-8")
    _git(ccbench, "add", "fixture.txt")
    _git(ccbench, "commit", "-qm", "ccbench fixture")

    v1 = json.loads((root / module.FREEZE_REL).read_bytes())
    protocol_raw = (root / module.FLOOR_PROTOCOL_REL).read_bytes()
    protocol_document = json.loads(protocol_raw)
    protocol = contract.validate_protocol(
        protocol_document,
        contract_sha256_lookup=lambda env_tag: env_contract.lookup(
            env_tag,
        ).contract_sha256,
    )
    protocol_sha256 = contract.canonical_protocol_sha256(protocol)
    run_dir = (
        f"output/env/{protocol['env_tag']}/calibration/s8b-floor-official/"
        f"20260811T000000Z-{protocol_sha256[:8]}"
    )
    result_rel = f"{run_dir}/result.json"
    result = _synthetic_floor_result(v1, protocol, root=root)
    cells = contract.enumerate_cells(
        v1, stock_configuration=protocol["stock_configuration"],
    )
    schedule = contract.build_schedule(
        cells=cells, master_seed=protocol["master_seed"],
        n_sessions=protocol["n_sessions"],
    )
    manifest = {
        "schema_version": contract.MANIFEST_SCHEMA,
        "protocol_sha256": protocol_sha256,
        "freeze": dict(protocol["freeze"]),
        "freeze_sha256": protocol["freeze"]["sha256"],
        "env_tag": protocol["env_tag"],
        "ccbench_pin": protocol["ccbench_pin"],
        "stock_configuration": protocol["stock_configuration"],
        "schedule_algorithm": protocol["schedule_algorithm"],
        "master_seed": protocol["master_seed"],
        "n_sessions": protocol["n_sessions"],
        "reps": protocol["reps"],
        "extime_s": protocol["extime_s"],
        "session_cv_max": protocol["session_cv_max"],
        "cell_cv_max": protocol["cell_cv_max"],
        "cells": cells,
        "binaries": result["binaries"],
        "schedule": schedule,
    }
    if manifest_kind == "empty":
        manifest = {}
    elif manifest_kind == "v2":
        manifest["schema_version"] = "s8b-floor-manifest/v2"
    elif manifest_kind != "v3":
        raise ValueError(f"unknown manifest_kind: {manifest_kind}")
    manifest_raw = canonical_bytes(manifest)
    manifest_sha256 = hashlib.sha256(manifest_raw).hexdigest()
    result["manifest_sha256"] = manifest_sha256
    journal_records = []
    schedule_by_seq = {row["seq"]: row for row in schedule}
    for session in result["sessions"]:
        scheduled = schedule_by_seq[session["seq"]]
        journal_records.append({
            "event": "session-start", "seq": session["seq"],
            "kind": "planned", "cell_id": session["cell_id"],
            "round": scheduled["round"], "retry_ordinal": None,
            "attempt_id": session["attempt_id"], "trigger": None,
        })
        journal_records.append(session)
    registry_fixture = None
    if result_schema == contract.LEGACY_RESULT_SCHEMA:
        from orchestrator.tests.s8b_floor_evidence_fixture import (
            build_floor_admission_evidence,
        )
        evidence = build_floor_admission_evidence(
            root / ".git/izanagi/s8b-holdout-admission-v1",
            protocol=protocol, freeze=v1,
            freeze_sha256=protocol["freeze"]["sha256"],
            manifest_sha256=manifest_sha256,
            campaign_run_id=f"20260811T000000Z-{protocol_sha256[:8]}",
            run_relpath=run_dir.removeprefix("output/"), mode="official",
            cells=cells, schedule=schedule, sessions=result["sessions"],
        )
        result["holdout_admission"] = evidence.expected_receipt
    else:
        _git(root, "add", "-A")
        _git(root, "commit", "-qm", "synthetic v5 authority")
        registry_fixture = attach_v5_attempt_registry(
            root=root, freeze=v1, protocol=protocol, cells=cells,
            schedule=schedule, result=result, manifest_raw=manifest_raw,
            run_dir=run_dir, journal_records=journal_records,
        )
        if mutate_attempt_registry is not None:
            mutate_attempt_registry(result["attempt_registry"])
    _write(root, result_rel, canonical_bytes(result))
    _write(root, f"{run_dir}/manifest.json", manifest_raw)
    _write(root, f"{run_dir}/journal.jsonl", b"".join(
        canonical_bytes(record) + b"\n" for record in journal_records
    ))
    campaign_run_id = f"20260811T000000Z-{protocol_sha256[:8]}"
    _write(
        root, f"{run_dir}/launch_certificate.json",
        canonical_bytes(launch_certificate(
            protocol_sha256=protocol_sha256,
            campaign_run_id=campaign_run_id,
        )),
    )

    budget_rel = "output/s8b-freeze-budget-inputs/g1.json"
    budget_document = {
        "total_bench_s": 100,
        "per_holdout_bench_s": {holdout_id: 50 for holdout_id in v1["holdouts"]},
        "oracle_shared": True,
    }
    _write(root, budget_rel, canonical_bytes(budget_document))
    approval = {
        "approved_at": "2026-08-11T00:00:00Z",
        "approver": "fixture-human",
        "budget": budget_document,
        "scope": module.BUDGET_APPROVAL_SCOPE,
    }
    approval_raw = canonical_bytes(approval)
    _write(root, module.BUDGET_APPROVAL_REL, approval_raw)

    closure_paths = []
    for holdout_id in sorted(module.HOLDOUTS):
        rel = f"evidence/{holdout_id}.txt"
        _write(root, rel, _holdout_hit_text(module, holdout_id))
        closure_paths.append(rel)

    _git(root, "add", "-A")
    _git(root, "commit", "-qm", "synthetic v2 candidate inputs")
    fixture = {
        "root": root,
        "head": _git(root, "rev-parse", "HEAD"),
        "result_rel": result_rel,
        "budget_rel": budget_rel,
        "budget": budget_document,
        "approval_sha256": hashlib.sha256(approval_raw).hexdigest(),
        "closure_paths": closure_paths,
    }
    if registry_fixture is not None:
        fixture.update(registry_fixture)
    return fixture
