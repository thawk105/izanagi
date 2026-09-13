# -*- coding: utf-8 -*-
"""F7 検証意味論 (V1 source blob / V2 transition / V3 二層未知性) + launch_validate の攻撃 matrix。

RV-verify レーン。tmp git repo に意味論的に valid な v1→g1 を組み (build_valid_semantic_g1)、
各意味論を 1 つずつ破って fail-closed を確認する。実 repo の output/s8b-freeze/ には書かない。
pytest 専用 (tmp_path fixture 依存、README allowlist 記載)。
"""
from __future__ import annotations

from orchestrator.tests.s8b_v2_freeze_fixture import in_sealed_fixture_process

import copy
import json
import dataclasses
import hashlib
import os
import shlex
import subprocess
import sys
from pathlib import Path
from unittest import mock

import pytest

_HERE = os.path.dirname(os.path.abspath(__file__))
_ORCH = os.path.dirname(_HERE)
_ROOT = os.path.dirname(_ORCH)
sys.path.insert(0, os.path.dirname(_ORCH))
sys.path.insert(0, _HERE)

from orchestrator.tests.s8b_v2_freeze_fixture import portable_binary_admission_receipt_fixture

from orchestrator.campaign import s8b_ratified_freeze as M  # noqa: E402
from orchestrator.campaign import s8b_holdout_freeze as HF  # noqa: E402
from orchestrator.campaign import env_contract as EC  # noqa: E402
from orchestrator.campaign import s8b_floor_contract as FC  # noqa: E402
from orchestrator.campaign import s8b_floor_stats as FS  # noqa: E402
from orchestrator.campaign import s8b_binary_admission as BA  # noqa: E402
from orchestrator.campaign import s8b_selector_freeze as SF  # noqa: E402
from orchestrator.campaign.build_admission import (  # noqa: E402
    GeneratorId, ReviewId, build_run_context, derive_build_admission,
    resolve_current_build_admission_policy,
)
from orchestrator.campaign.s8b_materialization import reviewed_source_capability  # noqa: E402
from orchestrator.campaign.source_digest import SOURCE_EVIDENCE_SCHEMA, SourceEvidence  # noqa: E402
from s8b_floor_evidence_fixture import (  # noqa: E402
    build_floor_admission_evidence,
    expected_portable_sort_swo_pass_receipt,
)
import test_s8b_ratified_freeze as B  # noqa: E402  (fixture 共用)

_REAL_V1 = Path(_ROOT) / "output" / "s8b-freeze" / "holdout_freeze.json"


def _need_v1():
    # trust root 不在で skip すると本ファイルの攻撃 matrix が丸ごと緑扱いになる (failures F9 型、
    # codex 相談 2026-07-18 C-10)。実 v1 freeze は repo 同梱の恒久 artifact なので不在 = fail。
    if not _REAL_V1.is_file():
        pytest.fail(f"実 v1 freeze が無い (trust root 不在): {_REAL_V1}")


_NEGATIVE_REGISTRY = {
    "source": {
        "baseline_validator": "load_ratified_freeze(emitter baseline)",
        "mutation_stage": "generation document before G",
        "repaired_deps": (), "invoke_layer": "load_ratified_freeze",
        "reason": "source-blob-mismatch", "cause": None,
    },
    "frozen": {
        "baseline_validator": "load_ratified_freeze(emitter baseline)",
        "mutation_stage": "generation document before G",
        "repaired_deps": (), "invoke_layer": "load_ratified_freeze",
        "reason": "frozen-at-head-mismatch", "cause": None,
    },
    "closure-missing": {
        "baseline_validator": "load_ratified_freeze(emitter baseline)",
        "mutation_stage": "generation document before G",
        "repaired_deps": (), "invoke_layer": "load_ratified_freeze",
        "reason": "closure-not-in-generation", "cause": None,
    },
    "closure-sha": {
        "baseline_validator": "load_ratified_freeze(emitter baseline)",
        "mutation_stage": "generation document before G",
        "repaired_deps": (), "invoke_layer": "load_ratified_freeze",
        "reason": "closure-sha-mismatch", "cause": None,
    },
    "env": {
        "baseline_validator": "load_ratified_freeze(emitter baseline)",
        "mutation_stage": "generation document before G",
        "repaired_deps": (), "invoke_layer": "load_ratified_freeze",
        "reason": "env-tag-unknown", "cause": None,
    },
    "transition": {
        "baseline_validator": "load_ratified_freeze(emitter baseline)",
        "mutation_stage": "generation document before G",
        "repaired_deps": (), "invoke_layer": "load_ratified_freeze",
        "reason": "transition-violation", "cause": None,
    },
    "scan-undeclared": {
        "baseline_validator": "launch_validate(emitter baseline)",
        "mutation_stage": "worktree after X",
        "repaired_deps": (), "invoke_layer": "launch_validate",
        "reason": "closure-hit-mismatch", "cause": None,
    },
    "scan-missing": {
        "baseline_validator": "launch_validate(emitter baseline)",
        "mutation_stage": "search report projection after real search",
        "repaired_deps": ("real search report",), "invoke_layer": "launch_validate",
        "reason": "closure-hit-mismatch", "cause": None,
    },
    "scan-per-holdout": {
        "baseline_validator": "launch_validate(emitter baseline)",
        "mutation_stage": "worktree after X",
        "repaired_deps": (), "invoke_layer": "launch_validate",
        "reason": "closure-hit-mismatch", "cause": None,
    },
    "scan-enumeration": {
        "baseline_validator": "launch_validate(emitter baseline)",
        "mutation_stage": "search enumeration race",
        "repaired_deps": (), "invoke_layer": "launch_validate",
        "reason": "enumeration-shifted", "cause": None,
    },
    "scan-positive": {
        "baseline_validator": "launch_validate(emitter baseline)",
        "mutation_stage": "positive-control worktree bytes after X",
        "repaired_deps": (), "invoke_layer": "launch_validate",
        "reason": "search-not-operational", "cause": None,
    },
    "selector-undeclared-hit": {
        "baseline_validator": "launch_validate(emitter selector evidence)",
        "mutation_stage": "selector evidence initial base commit",
        "repaired_deps": (), "invoke_layer": "launch_validate",
        "reason": "closure-hit-mismatch", "cause": None,
    },
    "selector-payload-hit": {
        "baseline_validator": "launch_validate(production-shaped selector evidence)",
        "mutation_stage": "selector payload initial base commit",
        "repaired_deps": (), "invoke_layer": "launch_validate",
        "reason": "closure-hit-mismatch", "cause": None,
    },
    "closure-namespace": {
        "baseline_validator": "load_ratified_freeze(emitter artifacts)",
        "mutation_stage": "G measurement_closure namespace path",
        "repaired_deps": ("closure sha", "G blob"), "invoke_layer": "launch_validate",
        "reason": "closure-role-conflict", "cause": None,
    },
    "generation-scope": {
        "baseline_validator": "load_ratified_freeze(otherwise-valid emitter g2)",
        "mutation_stage": "new C2 + new run artifacts + G2 + A2",
        "repaired_deps": ("all g2 artifact hashes", "approval pointer chain"),
        "invoke_layer": "launch_validate",
        "reason": "certificate-generation-scope", "cause": None,
    },
    "coherent-journal-result": {
        "baseline_validator": "launch_validate(emitter baseline)",
        "mutation_stage": "result document before G",
        "repaired_deps": ("generation.floor_source.sha256", "G result blob"),
        "invoke_layer": "launch_validate",
        "reason": "binding-chain-mismatch", "cause": "result-sessions",
    },
    "valid-run-cmd-required": {
        "baseline_validator": "launch_validate(emitter baseline)",
        "mutation_stage": "journal and result documents before G",
        "repaired_deps": ("generation.floor_source.sha256", "G result blob"),
        "invoke_layer": "launch_validate",
        "reason": "journal-state-invalid", "cause": "run-cmd-required",
    },
    "binaries-cell-set": {
        "baseline_validator": "launch_validate(emitter baseline)",
        "mutation_stage": "manifest and result binaries before G",
        "repaired_deps": ("manifest/result binaries mirror", "manifest hash chain"),
        "invoke_layer": "launch_validate",
        "reason": "manifest-invalid", "cause": "binaries-cell-set",
    },
    "binary-cell-binding": {
        "baseline_validator": "launch_validate(emitter baseline)",
        "mutation_stage": "manifest and result binaries before G",
        "repaired_deps": ("manifest/result binaries mirror", "manifest hash chain"),
        "invoke_layer": "launch_validate",
        "reason": "manifest-invalid", "cause": "binary-cell-binding",
    },
    "binary-hash": {
        "baseline_validator": "launch_validate(emitter baseline)",
        "mutation_stage": "manifest, result, and session receipts before G",
        "repaired_deps": (
            "manifest/result binaries mirror", "journal/result binary receipts",
            "manifest hash chain",
        ),
        "invoke_layer": "launch_validate",
        "reason": "manifest-invalid", "cause": "binary-hash",
    },
    "binding-sha": {
        "baseline_validator": "launch_validate(emitter baseline)",
        "mutation_stage": "manifest and result binary bindings before G",
        "repaired_deps": ("manifest/result binaries mirror", "manifest hash chain"),
        "invoke_layer": "launch_validate",
        "reason": "manifest-invalid", "cause": "binding-sha",
    },
}


def _assert_registered_refusal(case_id: str, invoke) -> M.RatifiedFreezeError:
    case = _NEGATIVE_REGISTRY[case_id]
    assert set(case) == {
        "baseline_validator", "mutation_stage", "repaired_deps", "invoke_layer",
        "reason", "cause",
    }
    with pytest.raises(M.RatifiedFreezeError) as caught:
        invoke()
    assert caught.value.reason == case["reason"]
    assert caught.value.cause == case["cause"]
    return caught.value


def _assert_emitter_baseline(tmp_path: Path) -> None:
    root, freeze, _topology = B.load_emitter_g1(tmp_path)
    assert isinstance(M.launch_validate(freeze, root), M.LaunchValidatedFreeze)


# --------------------------------------------------------------------------
# launch_validate 専用の production-shape 局所 stub (issuer helper 非依存)
# --------------------------------------------------------------------------

def _lgit(root: Path, *args: str, stdin: bytes | None = None) -> str:
    return subprocess.run(
        ["git", *args], cwd=root, check=True, input=stdin,
        stdout=subprocess.PIPE, stderr=subprocess.PIPE,
    ).stdout.decode("utf-8").strip()


def _lcommit(root: Path, subject: str, agent: str) -> str:
    _lgit(root, "add", "-A")
    _lgit(
        root, "commit", "-q", "-F", "-",
        stdin=f"{subject}\n\nAI-Agent: {agent}".encode("utf-8"),
    )
    return _lgit(root, "rev-parse", "HEAD")


def _lwrite(root: Path, rel: str, raw: bytes) -> None:
    path = root / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(raw)


def _lraw(document) -> bytes:
    return (json.dumps(document, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode()


def _ljline(document) -> bytes:
    return (json.dumps(
        document, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False,
    ) + "\n").encode()


def _lsha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _make_local_ccbench(root: Path) -> None:
    sub = root / "external" / "ccbench"
    sub.mkdir(parents=True)
    _lgit(sub, "init", "-q")
    _lgit(sub, "config", "user.name", "fixture")
    _lgit(sub, "config", "user.email", "fixture@example.invalid")
    (sub / "fixture.txt").write_text("scan fixture\n", encoding="utf-8")
    _lcommit(sub, "ccbench base", "fixture")


def _binding(cell: dict, freeze: dict) -> dict:
    entry = freeze["holdouts"][cell["holdout_id"]]["variant_binding"]["entries"][
        cell["configuration_id"]]
    preimage = {
        "entry_sha256": _lsha(M._canonical_bytes(entry)),
        "genome_canonical": f"fixture|{cell['configuration_id']}",
        "src_token": _lsha(("fixture-src:" + cell["cell_id"]).encode()),
        "variant_id": _lsha(
            f"fixture|{cell['configuration_id']}|src="
            f"{_lsha(('fixture-src:' + cell['cell_id']).encode())}".encode()
        )[:12],
    }
    return {**preimage, "binding_sha256": _lsha(M._canonical_bytes(preimage))}


def _portable_binaries(
        cells: list[dict], freeze: dict, protocol: dict, root: Path) -> dict:
    out = {}
    for cell in cells:
        cell_id = cell["cell_id"]
        binary_raw = ("binary:" + cell_id).encode()
        binary_sha = _lsha(binary_raw)
        binary_rel = f"output/fixture-bin/{binary_sha}/bench"
        _lwrite(root, binary_rel, binary_raw)
        binding = _binding(cell, freeze)
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
                "sha256": _lsha(compiler_input_raw),
            }],
        }
        compiler_input_manifest_sha256 = _lsha(
            json.dumps(
                compiler_input_manifest, ensure_ascii=True, sort_keys=True,
                separators=(",", ":"),
            ).encode()
        )
        source = SourceEvidence(
            schema_version=SOURCE_EVIDENCE_SCHEMA,
            source_root=str((root / "external/ccbench").resolve()),
            ccbench_commit=protocol["ccbench_pin"],
            genome_sha256=_lsha(binding["genome_canonical"].encode()),
            src_token=binding["src_token"],
            source_bytes_sha256=_lsha(("source:" + cell_id).encode()),
            tracked_clean=False,
            tracked_diff_sha256=_lsha(("diff:" + cell_id).encode()),
            tracked_paths=("include/backoff.hh",),
        )
        context = build_run_context(generator_id=GeneratorId.S8A_TRIGGER_SWEEP)
        review = reviewed_source_capability(
            review_id=ReviewId.S8B_FLOOR, source=source,
            input_sha256=binding["entry_sha256"],
        )
        admission = derive_build_admission(context, source, review_receipt=review)
        receipt = portable_binary_admission_receipt_fixture(
            admission=admission, expected_policy=context.policy, source=source,
            cell_id=cell_id, holdout_id=cell["holdout_id"],
            configuration_id=cell["configuration_id"], binding=binding,
            binary=root / binary_rel, binary_sha256=binary_sha,
            contract_sha256=protocol["contract_sha256"], trace=False,
            source_snapshot_sha256=_lsha(
                ("expected-materialization:" + cell_id).encode()
            ),
            expected_materialization_sha256=_lsha(
                ("expected-materialization:" + cell_id).encode()
            ),
            compiler_input_manifest=compiler_input_manifest,
            compiler_input_manifest_sha256=compiler_input_manifest_sha256,
        )
        record = {
            "cell_id": cell_id,
            "holdout_id": cell["holdout_id"],
            "configuration_id": cell["configuration_id"],
            "binary": binary_rel,
            "binary_sha256": binary_sha,
            "bin_hash_short": binary_sha[:16],
            "binding": binding,
            "configure_argv": ["cmake", "${CCBENCH_ROOT}"],
            "build_argv": ["cmake", "--build", "${OUT_ROOT}"],
            "cached": False,
            "store_path": f"output/fixture-store/{binary_sha}",
            "admission_receipt": receipt,
        }
        if cell["configuration_id"] == "sort_best":
            record["sort_swo_oracle"] = expected_portable_sort_swo_pass_receipt(
                cell_id=cell_id, holdout_id=cell["holdout_id"],
                configuration_id=cell["configuration_id"],
                entry_sha256=binding["entry_sha256"], binary_sha256=binary_sha,
            )
        out[cell_id] = record
    return out


def _session_rows(
        cells: list[dict], schedule: list[dict], binaries: dict,
        protocol: dict) -> list[dict]:
    by_id = {cell["cell_id"]: cell for cell in cells}
    contract = EC.lookup(protocol["env_tag"])
    rows = []
    for row in schedule:
        cell = by_id[row["cell_id"]]
        seq = row["seq"]
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
            for index in range(5)
        ]
        rows.append({
            "event": "session", "kind": "planned", "seq": seq, "round": row["round"],
            "retry_ordinal": None, "attempt_id": f"{cell['cell_id']}::seq{seq}", "trigger": None,
            "cell_id": cell["cell_id"], "holdout_id": cell["holdout_id"],
            "configuration_id": cell["configuration_id"], "records": cell["records"],
            "threads": cell["threads"], "workload": dict(cell["workload"]),
            "throughputs": [1000.0] * 5, "reps_expected": 5, "exec_failures": 0,
            "excluded_reason": None, "retry": False, "session_median": 1000.0,
            "rep_observations": observations, "rep_integrity_failures": 0,
            "exclusion_class": None, "valid": True, "session_cv": 0.0,
            "duration_s": 1.0,
            "run_cmd": shlex.join(FC.build_portable_run_cmd(
                binary=binaries[cell["cell_id"]]["binary"], workload=cell["workload"],
                records=cell["records"], threads=cell["threads"],
                extime_s=protocol["extime_s"], clocks_per_us=contract.clocks_per_us,
                numactl=contract.numactl,
            )),
            "notes": [],
            "probe_before": {"rc": 1, "stdout": "", "stderr": "", "competing": False},
            "probe_after": {"rc": 1, "stdout": "", "stderr": "", "competing": False},
            "binary_sha256_at_measure": binaries[cell["cell_id"]]["binary_sha256"],
        })
    return rows


def _result_document(protocol: dict, cells: list[dict], binaries: dict,
                     sessions: list[dict], manifest_sha: str, wall_ledger: list[dict]) -> dict:
    by_cell = {cell["cell_id"]: [] for cell in cells}
    for row in sessions:
        by_cell[row["cell_id"]].append(FS.SessionRecord(
            cell_id=row["cell_id"], holdout_id=row["holdout_id"],
            configuration_id=row["configuration_id"], seq=row["seq"],
            throughputs=tuple(row["throughputs"]), reps_expected=row["reps_expected"],
            exec_failures=row["exec_failures"], excluded_reason=row["excluded_reason"],
            retry=row["retry"], rep_observations=tuple(row["rep_observations"]),
            rep_integrity_failures=row["rep_integrity_failures"],
        ))
    computed = {}
    cells_out = {}
    for cell in cells:
        stats = FS.cell_stats(
            by_cell[cell["cell_id"]], n_sessions=protocol["n_sessions"],
            reps=protocol["reps"], session_cv_max=protocol["session_cv_max"],
        )
        computed[cell["cell_id"]] = stats
        cells_out[cell["cell_id"]] = {
            "holdout_id": stats.holdout_id, "configuration_id": stats.configuration_id,
            "n_valid": stats.n_valid, "medians": list(stats.medians), "m": stats.m,
            "s": stats.s, "valid": stats.valid, "cv": stats.cv, "notes": list(stats.notes),
        }
    floors = {}
    for holdout in sorted({cell["holdout_id"] for cell in cells}):
        holdout_cells = {cid: value for cid, value in computed.items()
                         if value.holdout_id == holdout}
        floor = FS.holdout_floors(
            holdout_cells, stock_id=f"{holdout}::{protocol['stock_configuration']}",
            wired_min_rel_floor=protocol["wired_min_rel_floor"],
            cell_cv_max=protocol["cell_cv_max"],
        )
        floors[holdout] = {
            "pairs": dict(floor.pairs), "scalar_alt": floor.scalar_alt,
            "scale_ref": floor.scale_ref, "diagnostics": floor.diagnostics,
        }
    attempts = [{
        "seq": r["seq"], "cell_id": r["cell_id"], "kind": r["kind"], "round": r["round"],
        "retry_ordinal": r["retry_ordinal"], "valid": r["valid"],
        "excluded_reason": r["excluded_reason"], "session_cv": r["session_cv"],
        "exclusion_class": r["exclusion_class"],
        "rep_integrity_failures": r["rep_integrity_failures"],
        "session_median": r["session_median"], "duration_s": r["duration_s"],
    } for r in sessions]
    return {
        "schema": FC.RESULT_SCHEMA, "formula": protocol["formula"], "mode": "official",
        "eligible_for_refreeze": True, "env_tag": protocol["env_tag"],
        "ccbench_pin": protocol["ccbench_pin"],
        "protocol_sha256": FC.canonical_protocol_sha256(protocol),
        "freeze_sha256": M.V1_FREEZE_SHA256, "manifest_sha256": manifest_sha,
        "stock_configuration": protocol["stock_configuration"],
        "wired_min_rel_floor": protocol["wired_min_rel_floor"], "reps": protocol["reps"],
        "n_sessions": protocol["n_sessions"],
        "scale_adequacy_rel_tolerance": protocol["scale_adequacy_rel_tolerance"],
        "holdouts": sorted({c["holdout_id"] for c in cells}),
        "configurations": sorted({c["configuration_id"] for c in cells}),
        "binaries": binaries,
        "config": FC.project_protocol_for_floor_artifact(protocol),
        "sessions": json.loads(json.dumps(sessions)), "cells": cells_out, "floors": floors,
        "wall_ledger": wall_ledger, "excluded": [], "attempts": attempts,
    }


def _build_independent_launch_repo(tmp_path: Path, *, mutate=None, cert_mutate=None,
                                   cert_at_generation=False, executable_role=None):
    """C(cert only)→G(run artifacts+closure+generation)→A(approval)→X(pointer)→H。"""
    root = tmp_path / "launch-repo"
    root.mkdir()
    _lgit(root, "init", "-q")
    _lgit(root, "config", "user.name", "fixture")
    _lgit(root, "config", "user.email", "fixture@example.invalid")
    _make_local_ccbench(root)
    freeze = json.loads(_REAL_V1.read_bytes())
    _lwrite(root, M.V1_FREEZE_PATH, _REAL_V1.read_bytes())
    calibration_path = EC.lookup("linux-baremetal").calibration_ref.path
    _lwrite(root, calibration_path, (Path(_ROOT) / calibration_path).read_bytes())
    _lwrite(root, "positive_control.txt", B._RR50_PARAMS)
    (root / "README.md").write_text("launch fixture\n", encoding="utf-8")
    base_commit = _lcommit(root, "base", "fixture")

    contract = EC.lookup("linux-baremetal")
    protocol = {
        "schema": FC.PROTOCOL_SCHEMA, "formula": FC.FORMULA_ID,
        "env_tag": contract.env_tag, "ccbench_pin": "fixture-pin",
        "freeze": {"path": M.V1_FREEZE_PATH, "sha256": M.V1_FREEZE_SHA256},
        "stock_configuration": "stock_common", "n_sessions": 8, "reps": 5,
        "master_seed": "fixture-seed", "schedule_algorithm": FC.SCHEDULE_ALGORITHM,
        "extime_s": 5, "wired_min_rel_floor": 0.9, "retry_slots_per_cell": 2,
        "session_cv_max": "0.10", "cell_cv_max": "0.15",
        "scale_adequacy_rel_tolerance": "0.10",
        "allowed_excluded_reasons": list(FC._APPROVED_REASONS),
        "contract_sha256": contract.contract_sha256,
    }
    protocol = FC.validate_protocol(
        protocol, contract_sha256_lookup=lambda _env: contract.contract_sha256,
    )
    protocol_sha = FC.canonical_protocol_sha256(protocol)
    run_id = f"20260718T120000Z-{protocol_sha[:8]}"
    run_dir = f"output/env/{contract.env_tag}/calibration/s8b-floor-official/{run_id}"
    paths = {
        "protocol": f"{run_dir}/protocol.json", "cert": f"{run_dir}/launch_certificate.json",
        "journal": f"{run_dir}/journal.jsonl", "manifest": f"{run_dir}/manifest.json",
        "result": f"{run_dir}/result.json", "closure80": f"{run_dir}/closure80.txt",
        "closure20": f"{run_dir}/closure20.txt",
    }
    cert = {
        "schema": "s8b-floor-launch-certificate/v1",
        "v1_freeze_sha256": M.V1_FREEZE_SHA256,
        "clean_scan_digest": "0" * 64, "protocol_sha256": protocol_sha,
        "started_utc": "2026-07-18T12:00:00+00:00", "campaign_run_id": run_id,
    }
    if cert_mutate is not None:
        cert_mutate(cert)
    cert_raw = _lraw(cert)
    if cert_at_generation:
        c_commit = base_commit
    else:
        _lwrite(root, paths["cert"], cert_raw)
        c_commit = _lcommit(root, "launch certificate", "fixture")

    cells = FC.enumerate_cells(freeze, stock_configuration=protocol["stock_configuration"])
    schedule = FC.build_schedule(
        cells=cells, master_seed=protocol["master_seed"], n_sessions=protocol["n_sessions"],
    )
    binaries = _portable_binaries(cells, freeze, protocol, root)
    manifest = {
        "schema_version": FC.MANIFEST_SCHEMA, "protocol_sha256": protocol_sha,
        "freeze": dict(protocol["freeze"]), "freeze_sha256": M.V1_FREEZE_SHA256,
        "env_tag": protocol["env_tag"], "ccbench_pin": protocol["ccbench_pin"],
        "stock_configuration": protocol["stock_configuration"],
        "schedule_algorithm": protocol["schedule_algorithm"], "master_seed": protocol["master_seed"],
        "n_sessions": protocol["n_sessions"], "reps": protocol["reps"],
        "extime_s": protocol["extime_s"], "session_cv_max": protocol["session_cv_max"],
        "cell_cv_max": protocol["cell_cv_max"], "cells": cells,
        "binaries": binaries, "schedule": schedule,
    }
    manifest_raw = _lraw(manifest)
    cert_sha = _lsha(cert_raw)
    manifest_sha = _lsha(manifest_raw)
    campaign_start = {
        "event": "campaign-start", "schema": FC.JOURNAL_SCHEMA,
        "protocol_sha256": protocol_sha, "freeze_sha256": M.V1_FREEZE_SHA256,
        "manifest_sha256": manifest_sha, "launch_certificate_sha256": cert_sha,
        "hostname": "fixture-host", "boot_id": "fixture-boot", "job_id": None,
        "cpuset": "/", "utc": cert["started_utc"], "pid": 1, "starttime": 1,
        "execution_uuid": "0" * 32,
        "execution_receipt": {
            "schema": "s8b-execution-receipt/v1", "env_tag": protocol["env_tag"],
            "contract_sha256": protocol["contract_sha256"],
            "attestation": {"hostname": "fixture-host", "boot_id": "fixture-boot",
                            "cpuset": "/", "captured_utc": cert["started_utc"]},
        },
    }
    sessions = _session_rows(cells, schedule, binaries, protocol)
    journal = [{"event": "launch-start", "schema": FC.JOURNAL_SCHEMA,
                "launch_certificate_sha256": cert_sha, "utc": cert["started_utc"]},
               campaign_start]
    for round_no in range(1, protocol["n_sessions"] + 1):
        rs = {"event": "round-start", "round": round_no, "utc": cert["started_utc"]}
        journal.append(rs)
        for row in [s for s in sessions if s["round"] == round_no]:
            journal.append({
                "event": "session-start", "seq": row["seq"], "kind": row["kind"],
                "cell_id": row["cell_id"], "round": row["round"],
                "retry_ordinal": row["retry_ordinal"], "attempt_id": row["attempt_id"],
                "trigger": row["trigger"], "started_iso": cert["started_utc"],
            })
            journal.append(row)
        journal.append({"event": "round-complete", "round": round_no,
                        "utc": cert["started_utc"]})
    journal.append({"event": "terminal", "status": "completed"})
    wall_ledger = [r for r in journal if r["event"] in
                   {"campaign-start", "round-start", "round-complete"}]
    result = _result_document(protocol, cells, binaries, sessions, manifest_sha, wall_ledger)

    state = {"protocol": protocol, "cert": cert, "manifest": manifest,
             "journal": journal, "result": result, "paths": paths}
    if mutate is not None:
        mutate(state)
        protocol, cert, manifest, journal, result = (
            state["protocol"], state["cert"], state["manifest"], state["journal"], state["result"])
        if state.get("repair_manifest"):
            repaired_manifest_sha = _lsha(_lraw(manifest))
            campaign = next(r for r in journal if r["event"] == "campaign-start")
            campaign["manifest_sha256"] = repaired_manifest_sha
            result["manifest_sha256"] = repaired_manifest_sha
            wall_campaign = next(r for r in result["wall_ledger"]
                                 if r["event"] == "campaign-start")
            wall_campaign["manifest_sha256"] = repaired_manifest_sha
    protocol_record_raw = _lraw(protocol)
    protocol_raw = protocol_record_raw + state.get("post_hash_protocol_suffix", b"")
    cert_raw = _lraw(cert)
    manifest_raw = _lraw(manifest)
    journal_raw = b"".join(_ljline(record) for record in journal)
    admission = build_floor_admission_evidence(
        root / ".git/izanagi/s8b-holdout-admission-v1",
        protocol=protocol, freeze=freeze, freeze_sha256=M.V1_FREEZE_SHA256,
        manifest_sha256=_lsha(manifest_raw), campaign_run_id=run_id,
        run_relpath=run_dir.removeprefix("output/"), mode="official",
        cells=cells, schedule=schedule, sessions=sessions,
    )
    result["holdout_admission"] = admission.expected_receipt
    result_raw = _lraw(result)
    result_record_sha = _lsha(result_raw)
    post_hash_suffix = state.get("post_hash_result_suffix", b"")
    if post_hash_suffix:
        assert isinstance(post_hash_suffix, bytes)
        result_raw += post_hash_suffix
    if cert_at_generation:
        _lwrite(root, paths["cert"], cert_raw)
    # 通常 mutation は C bytes を変えない。cert_mutate は C の構築前にだけ適用する。
    assert (root / paths["cert"]).read_bytes() == cert_raw
    _lwrite(root, paths["protocol"], protocol_raw)
    _lwrite(root, paths["manifest"], manifest_raw)
    _lwrite(root, paths["journal"], journal_raw)
    _lwrite(root, paths["result"], result_raw)
    closure80_record_raw = B._RR80_PARAMS
    closure80_raw = closure80_record_raw + state.get("post_hash_closure80_suffix", b"")
    _lwrite(root, paths["closure80"], closure80_raw)
    _lwrite(root, paths["closure20"], B._RR20_PARAMS)
    if executable_role is not None:
        executable_path = root / paths[executable_role]
        executable_path.chmod(executable_path.stat().st_mode | 0o111)
    gen_doc = dict(freeze)
    gen_doc.update({
        "schema_version": "8b-holdout-freeze/v2", "generation_number": 1,
        "supersedes_sha256": M.V1_FREEZE_SHA256, "env_tag": protocol["env_tag"],
        "floor_protocol": {"path": paths["protocol"], "sha256": _lsha(protocol_record_raw)},
        "floor_source": {"path": paths["result"], "sha256": result_record_sha},
        "floor": B._independent_floor_projection(result),
        "measurement_closure": [
            {"canonical_path": paths["closure80"], "sha256": _lsha(closure80_record_raw)},
            {"canonical_path": paths["closure20"], "sha256": _lsha(B._RR20_PARAMS)},
        ],
    })
    gen_raw = _lraw(gen_doc)
    gen_path = M._gen_path(1)
    _lwrite(root, gen_path, gen_raw)
    g_commit = _lcommit(root, "generation artifacts", "fixture")
    gen_sha = _lsha(gen_raw)
    approval_raw = M._canonical_bytes({
        "generation_sha256": gen_sha, "approver": "user",
        "approved_at": "2026-07-18T12:01:00Z", "scope": "s8b-holdout",
    })
    approval_sha = _lsha(approval_raw)
    _lwrite(root, f"{M.APPROVAL_DIR}/{gen_sha}.json", approval_raw)
    a_commit = _lcommit(root, "approve generation", "none")
    pointer_raw = M._canonical_bytes({
        "generation_number": 1, "path": gen_path, "sha256": gen_sha,
        "parent_active_sha256": None, "approval_sha256": approval_sha,
    })
    pointer_sha = _lsha(pointer_raw)
    _lwrite(root, f"{M.ACTIVE_DIR}/{pointer_sha}.json", pointer_raw)
    x_commit = _lcommit(root, "activate generation", "none")
    (root / "validation-head.txt").write_text("H differs from A\n", encoding="utf-8")
    h_commit = _lcommit(root, "validation head", "fixture")
    ratified = M.RatifiedFreeze(
        document=M._deep_freeze(gen_doc), sha256=gen_sha, generation_number=1,
        activation_head=h_commit, generation_commit=g_commit,
    )
    return root, ratified, {
        **state, "C": c_commit, "G": g_commit, "A": a_commit,
        "X": x_commit, "H": h_commit,
    }


def _build_launch_repo(tmp_path: Path, *, mutate=None, cert_mutate=None,
                       cert_at_generation=False, executable_role=None,
                       selector_valid_cell=False, selector_extra_files=(),
                       selector_payload_hit=False):
    """決定的観測下の production-emitter bytes を G/A/X に載せた launch fixture。"""
    def combined(state):
        if cert_mutate is not None:
            cert_mutate(state["cert"])
        if mutate is not None:
            mutate(state)

    root, gen_sha, _gen_path, g1, topology = B.build_production_emitter_g1(
        tmp_path, mutate=combined if (mutate is not None or cert_mutate is not None) else None,
        cert_at_generation=cert_at_generation, executable_role=executable_role,
        selector_valid_cell=selector_valid_cell,
        selector_extra_files=selector_extra_files,
        selector_payload_hit=selector_payload_hit,
    )
    ratified = M.RatifiedFreeze(
        document=M._deep_freeze(g1), sha256=gen_sha, generation_number=1,
        activation_head=topology["X"], generation_commit=topology["G"],
    )
    return root, ratified, topology


def _mutate_portable_binary_island(state: dict, case_id: str) -> None:
    """manifest/result の mirror を保ったまま portable binary 束縛だけを壊す。"""
    manifest_binaries = state["manifest"]["binaries"]
    result_binaries = state["result"]["binaries"]
    assert manifest_binaries == result_binaries
    cell_id = sorted(manifest_binaries)[0]

    if case_id == "binaries-cell-set":
        manifest_binaries.pop(cell_id)
        result_binaries.pop(cell_id)
    elif case_id == "binary-cell-binding":
        foreign_cell_id = f"{cell_id}-foreign"
        manifest_binaries[cell_id]["cell_id"] = foreign_cell_id
        result_binaries[cell_id]["cell_id"] = foreign_cell_id
    elif case_id == "binary-hash":
        bad_sha = "not-a-sha256"
        for binaries in (manifest_binaries, result_binaries):
            binaries[cell_id]["binary_sha256"] = bad_sha
            binaries[cell_id]["bin_hash_short"] = bad_sha[:16]
        for record in state["journal"]:
            if record.get("event") == "session" and record["cell_id"] == cell_id:
                record["binary_sha256_at_measure"] = bad_sha
        for record in state["result"]["sessions"]:
            if record["cell_id"] == cell_id:
                record["binary_sha256_at_measure"] = bad_sha
    elif case_id == "binding-sha":
        bad_sha = "0" * 64
        assert manifest_binaries[cell_id]["binding"]["binding_sha256"] != bad_sha
        manifest_binaries[cell_id]["binding"]["binding_sha256"] = bad_sha
        result_binaries[cell_id]["binding"]["binding_sha256"] = bad_sha
    else:  # pragma: no cover - parametrization is the closed world
        raise AssertionError(case_id)

    assert manifest_binaries == result_binaries
    state["repair_manifest"] = True


@in_sealed_fixture_process
def test_historical_reverify_rejects_cross_cell_policy_mixture(tmp_path):
    """historical は current policy 非依存だが、記録 policy の cell 間混在は拒否する。"""
    def mutate(state):
        manifest_binaries = state["manifest"]["binaries"]
        result_binaries = state["result"]["binaries"]
        cell_id = sorted(manifest_binaries)[0]
        receipt = copy.deepcopy(manifest_binaries[cell_id]["admission_receipt"])
        replacement = "f" * 64
        if receipt["admission"]["policy_sha256"] == replacement:
            replacement = "e" * 64
        receipt["admission"]["policy_sha256"] = replacement
        unsigned = dict(receipt)
        unsigned.pop("receipt_sha256")
        receipt["receipt_sha256"] = BA._sha256_map(unsigned)
        manifest_binaries[cell_id]["admission_receipt"] = receipt
        result_binaries[cell_id]["admission_receipt"] = copy.deepcopy(receipt)
        state["repair_manifest"] = True

    _need_v1()
    root, freeze, _topology = _build_launch_repo(tmp_path, mutate=mutate)
    with pytest.raises(M.RatifiedFreezeError) as excinfo:
        M.reverify_published_freeze(freeze, root)
    assert excinfo.value.reason == "manifest-invalid"
    assert excinfo.value.cause == "binary-admission-policy-mixed"


def _edge_node_fixture(edge_to_cut=None) -> dict[str, str]:
    nodes = {node for edge in M.EQUALITY_CHAIN_ADJACENCY for node in edge}
    adjacency = {node: set() for node in nodes}
    for edge in M.EQUALITY_CHAIN_ADJACENCY:
        if edge == edge_to_cut:
            continue
        left, right = edge
        adjacency[left].add(right)
        adjacency[right].add(left)
    values = {}
    component = 0
    for node in sorted(nodes):
        if node in values:
            continue
        component += 1
        stack = [node]
        while stack:
            current = stack.pop()
            if current in values:
                continue
            values[current] = f"component-{component}"
            stack.extend(adjacency[current])
    return values


@pytest.mark.parametrize("edge", M.EQUALITY_CHAIN_ADJACENCY,
                         ids=lambda edge: f"{edge[0]}--{edge[1]}")
def test_equality_chain_each_edge_raw_tamper_rejected(edge):
    """各辺の片側 field だけを壊す raw tamper が必ず発火する。"""
    nodes = _edge_node_fixture()
    nodes[edge[1]] = "raw-tamper"
    with pytest.raises(M.RatifiedFreezeError) as ei:
        M._assert_equality_adjacency(nodes)
    assert ei.value.reason == "binding-chain-mismatch"


@pytest.mark.parametrize("edge", M.EQUALITY_CHAIN_ADJACENCY,
                         ids=lambda edge: f"{edge[0]}--{edge[1]}")
def test_equality_chain_each_edge_coherent_island_rejected(edge):
    """対象辺以外の関連値を全再束縛した coherent island でも独立 anchor 辺が発火する。"""
    nodes = _edge_node_fixture(edge)
    with pytest.raises(M.RatifiedFreezeError) as ei:
        M._assert_equality_adjacency(nodes)
    assert ei.value.reason == "binding-chain-mismatch"
    assert ei.value.cause == f"equality-edge:{edge[0]}->{edge[1]}"


# --------------------------------------------------------------------------
# 正常系
# --------------------------------------------------------------------------

@in_sealed_fixture_process
def test_semantic_happy_path_loads_and_launch_validates(tmp_path):
    _need_v1()
    root, freeze, topology = _build_launch_repo(tmp_path)
    assert topology["C"] != topology["G"] != topology["A"] != topology["X"]
    assert topology["H"] == topology["X"]
    assert _lgit(root, "merge-base", "--is-ancestor", topology["C"], topology["G"]) == ""
    loaded = M.load_ratified_freeze(root)
    assert loaded.sha256 == freeze.sha256
    lv = M.launch_validate(freeze, root)
    assert isinstance(lv, M.LaunchValidatedFreeze)
    assert lv.activation_head == freeze.activation_head
    assert lv.ratified is freeze
    assert isinstance(lv.floor_artifact, M.VerifiedFloorArtifact)
    assert lv.floor_artifact.path.endswith("/result.json")
    assert lv.floor_artifact.sha256 == _lsha(lv.floor_artifact.raw_bytes)
    assert set(lv.binaries_by_cell) == set(topology["manifest"]["binaries"])


def _with_earlier_floor_result_at_head(
        root: Path, freeze: M.RatifiedFreeze) -> tuple[M.RatifiedFreeze, str]:
    selected_rel = freeze.document["floor_source"]["path"]
    selected_run_id = selected_rel.rsplit("/", 2)[-2]
    proto8 = selected_run_id.rsplit("-", 1)[1]
    earlier_rel = selected_rel.replace(
        selected_run_id, f"20260718T115959Z-{proto8}",
    )
    B._write(root, earlier_rel, b"{}")
    activation_head = B._fixed_commit_all(
        root, "earlier official result", "fixture",
    )
    return M.RatifiedFreeze(
        document=freeze.document, sha256=freeze.sha256,
        generation_number=freeze.generation_number,
        activation_head=activation_head,
        generation_commit=freeze.generation_commit,
    ), earlier_rel


def _install_real_earlier_official_run(
        root: Path, topology: dict, *, resume: bool) -> tuple[str, bool]:
    """実 admission を追記し、scan-neutral な earlier official run を設置する。"""
    from orchestrator.campaign import s8b_holdout_admission as admission

    selected_rel = topology["paths"]["result"]
    selected_run_id = selected_rel.rsplit("/", 2)[-2]
    proto8 = selected_run_id.rsplit("-", 1)[1]
    earlier_run_id = f"20260718T115959Z-{proto8}"
    assert earlier_run_id < selected_run_id
    namespace_rel = selected_rel.rsplit("/", 2)[0]
    run_dir_rel = f"{namespace_rel}/{earlier_run_id}"
    earlier_rel = f"{run_dir_rel}/result.json"
    run_dir = root / run_dir_rel
    assert not run_dir.exists()

    selected_run_dir = root / selected_rel.rsplit("/", 1)[0]
    selected_before = {
        path.name: path.read_bytes()
        for path in selected_run_dir.iterdir() if path.is_file()
    }
    admission_root = root / ".git/izanagi/s8b-holdout-admission-v1"
    admission_before = {
        path.relative_to(admission_root).as_posix(): path.read_bytes()
        for path in admission_root.rglob("*") if path.is_file()
    }

    protocol = copy.deepcopy(topology["protocol"])
    v1 = json.loads((root / protocol["freeze"]["path"]).read_bytes())
    cells = FC.enumerate_cells(
        v1, stock_configuration=protocol["stock_configuration"],
    )
    admission_cells = [
        {
            "cell_id": cell["cell_id"],
            "freeze_holdout_key": cell["holdout_id"],
            "configuration_id": cell["configuration_id"],
            "records": cell["records"],
            "threads": cell["threads"],
            "workload": cell["workload"],
        }
        for cell in cells
    ]
    schedule = FC.build_schedule(
        cells=cells, master_seed=protocol["master_seed"],
        n_sessions=protocol["n_sessions"],
    )
    schedule_by_seq = {row["seq"]: row for row in schedule}

    run_dir.mkdir(parents=True)
    manifest_raw = B._json_bytes_with_escaped_strings(topology["manifest"])
    manifest_sha256 = hashlib.sha256(manifest_raw).hexdigest()
    (run_dir / "manifest.json").write_bytes(manifest_raw)
    journal_path = run_dir / "journal.jsonl"
    journal_path.write_bytes(b"")
    run_relpath = run_dir_rel.removeprefix("output/")
    reservation = admission.reserve_floor_holdout_observations(
        repo_root=root, protocol=protocol, verified_freeze_document=v1,
        freeze_sha256=protocol["freeze"]["sha256"],
        cells=admission_cells, schedule=schedule,
        campaign_run_id=earlier_run_id, out_root=root / "output",
        run_dir=run_dir, run_relpath=run_relpath, mode="official",
        resume=resume, nondefault_seams=[],
    )
    admitted = admission.finalize_floor_holdout_admissions(reservation)

    journal_records = []
    for session in topology["result"]["sessions"]:
        scheduled = schedule_by_seq[session["seq"]]
        start = {
            "event": "session-start", "seq": session["seq"],
            "kind": "planned", "cell_id": session["cell_id"],
            "round": scheduled["round"], "retry_ordinal": None,
            "attempt_id": session["attempt_id"], "trigger": None,
        }
        journal_records.append(start)
        journal_path.write_bytes(B._jsonl_bytes(journal_records))
        competing = session["probe_before"]["competing"]
        if competing is False:
            admission.consume_attempt_ticket(
                admitted[session["cell_id"]],
                attempt_id=session["attempt_id"],
            )
        journal_records.append({
            "event": "session", "cell_id": session["cell_id"],
            "attempt_id": session["attempt_id"],
            "probe_before": {"competing": competing},
        })
        journal_path.write_bytes(B._jsonl_bytes(journal_records))

    inspection = admission.inspect_floor_holdout_admission_evidence(
        repo_root=root, protocol=protocol, verified_freeze_document=v1,
        freeze_sha256=protocol["freeze"]["sha256"],
        manifest_sha256=manifest_sha256, campaign_run_id=earlier_run_id,
        run_relpath=run_relpath, mode="official", cells=cells,
        schedule=schedule, sessions=journal_records,
    )
    claim_entry_kinds = {
        json.loads(
            (admission_root / "measurement-generation-claims"
             / f"{claim_digest}.claim").read_bytes()
        )["entry_kind"]
        for claim_digest in inspection["claim_identities"].values()
    }
    assert claim_entry_kinds == ({"resume"} if resume else {"fresh"})
    marker_name = hashlib.sha256(earlier_run_id.encode("utf-8")).hexdigest()
    marker_path = (
        admission_root / "refreeze-disqualifications" / f"{marker_name}.json"
    )
    assert marker_path.is_file() is resume
    result = copy.deepcopy(topology["result"])
    result["eligible_for_refreeze"] = inspection.derived_eligible_for_refreeze
    result["manifest_sha256"] = manifest_sha256
    result["holdout_admission"] = dict(inspection)
    for row in result["wall_ledger"]:
        if row.get("event") == "campaign-start":
            row["manifest_sha256"] = manifest_sha256
    (run_dir / "result.json").write_bytes(
        B._json_bytes_with_escaped_strings(result)
    )
    assert not (run_dir / "launch_certificate.json").exists()

    selected_after = {
        path.name: path.read_bytes()
        for path in selected_run_dir.iterdir() if path.is_file()
    }
    assert selected_after == selected_before
    for relative, before in admission_before.items():
        after = (admission_root / relative).read_bytes()
        if relative in {"ledger.jsonl", "attempt-ledger.jsonl"}:
            assert after.startswith(before)
        else:
            assert after == before

    B._fixed_commit_all(root, "earlier official result", "fixture")
    return earlier_rel, inspection.derived_eligible_for_refreeze


@in_sealed_fixture_process
def test_launch_validate_rejects_floor_selection_rule_mismatch(
        tmp_path, monkeypatch):
    root, freeze, _topology = _build_launch_repo(tmp_path)
    freeze, earlier_rel = _with_earlier_floor_result_at_head(root, freeze)
    calls = []

    def derived_eligible(**kwargs):
        calls.append(kwargs["result_rel"])
        return True

    monkeypatch.setattr(HF, "_derive_floor_selection_eligibility", derived_eligible)
    with pytest.raises(M.RatifiedFreezeError) as caught:
        M.launch_validate(freeze, root)
    assert caught.value.reason == "floor-selection-rule-mismatch"
    assert caught.value.cause == "earliest-eligible-official-run-id/v1"
    assert calls == [earlier_rel]


@in_sealed_fixture_process
def test_g1_selection_helper_rejects_rule_mismatch(tmp_path, monkeypatch):
    root, freeze, _topology = _build_launch_repo(tmp_path)
    freeze, earlier_rel = _with_earlier_floor_result_at_head(root, freeze)
    calls = []

    def derived_eligible(**kwargs):
        calls.append(kwargs["result_rel"])
        return True

    monkeypatch.setattr(HF, "_derive_floor_selection_eligibility", derived_eligible)
    with pytest.raises(M.RatifiedFreezeError) as caught:
        M.assert_g1_floor_selection_identity(freeze, root)
    assert caught.value.reason == "floor-selection-rule-mismatch"
    assert caught.value.cause == "earliest-eligible-official-run-id/v1"
    assert calls == [earlier_rel]


@in_sealed_fixture_process
def test_launch_validate_rejects_genuine_eligible_earlier_official_run(
        tmp_path):
    root, _freeze, topology = _build_launch_repo(tmp_path)
    _earlier_rel, derived = _install_real_earlier_official_run(
        root, topology, resume=False,
    )
    assert derived is True
    loaded = M.load_ratified_freeze(root)

    with pytest.raises(M.RatifiedFreezeError) as caught:
        M.launch_validate(loaded, root)
    assert caught.value.reason == "floor-selection-rule-mismatch"
    assert caught.value.cause == "earliest-eligible-official-run-id/v1"


@in_sealed_fixture_process
def test_launch_validate_accepts_genuine_ineligible_earlier_resume(
        tmp_path):
    root, _freeze, topology = _build_launch_repo(tmp_path)
    _earlier_rel, derived = _install_real_earlier_official_run(
        root, topology, resume=True,
    )
    assert derived is False
    loaded = M.load_ratified_freeze(root)

    validated = M.launch_validate(loaded, root)
    assert type(validated) is M.LaunchValidatedFreeze
    assert validated.ratified is loaded


@in_sealed_fixture_process
def test_g1_selection_helper_rejects_genuine_eligible_earlier_official_run(
        tmp_path):
    root, _freeze, topology = _build_launch_repo(tmp_path)
    _earlier_rel, derived = _install_real_earlier_official_run(
        root, topology, resume=False,
    )
    assert derived is True
    loaded = M.load_ratified_freeze(root)

    with pytest.raises(M.RatifiedFreezeError) as caught:
        M.assert_g1_floor_selection_identity(loaded, root)
    assert caught.value.reason == "floor-selection-rule-mismatch"
    assert caught.value.cause == "earliest-eligible-official-run-id/v1"


@in_sealed_fixture_process
def test_g1_selection_helper_accepts_genuine_ineligible_earlier_resume(
        tmp_path):
    root, _freeze, topology = _build_launch_repo(tmp_path)
    _earlier_rel, derived = _install_real_earlier_official_run(
        root, topology, resume=True,
    )
    assert derived is False
    loaded = M.load_ratified_freeze(root)

    assert M.assert_g1_floor_selection_identity(loaded, root) is None


@in_sealed_fixture_process
def test_g1_selection_helper_rejects_foreign_env_namespace(
        tmp_path, monkeypatch):
    original_paths = {}

    def move_selected_result_to_foreign_env(state):
        selected_rel = state["paths"]["result"]
        foreign_rel = selected_rel.replace(
            "/linux-baremetal/", "/foreign-env/", 1,
        )
        assert foreign_rel != selected_rel
        state["paths"]["result"] = foreign_rel
        original_paths["selected"] = selected_rel
        original_paths["foreign"] = foreign_rel

    root, _freeze, _topology = _build_launch_repo(
        tmp_path, mutate=move_selected_result_to_foreign_env,
    )
    loaded = M.load_ratified_freeze(root)
    selected_rel = original_paths["selected"]
    selected_run_id = selected_rel.rsplit("/", 2)[-2]
    proto8 = selected_run_id.rsplit("-", 1)[1]
    earlier_rel = selected_rel.replace(
        selected_run_id, f"20260718T115959Z-{proto8}",
    )
    B._write(root, earlier_rel, b"{}")
    B._fixed_commit_all(root, "earlier true-namespace result", "fixture")
    calls = []

    def derived_eligible(**kwargs):
        calls.append(kwargs["result_rel"])
        return True

    monkeypatch.setattr(HF, "_derive_floor_selection_eligibility", derived_eligible)
    with pytest.raises(M.RatifiedFreezeError) as caught:
        M.assert_g1_floor_selection_identity(loaded, root)
    assert caught.value.reason == "floor-selection-unverifiable"
    assert caught.value.cause == "selection-env-chain"
    assert loaded.document["env_tag"] == "linux-baremetal"
    assert loaded.document["floor_source"]["path"] == original_paths["foreign"]
    assert earlier_rel < selected_rel
    assert calls == []


@in_sealed_fixture_process
def test_g1_selection_helper_rejects_protocol_hash_prefix_mismatch(tmp_path):
    def move_selected_result_to_wrong_proto8(state):
        selected_rel = state["paths"]["result"]
        run_id = selected_rel.rsplit("/", 2)[-2]
        timestamp, proto8 = run_id.rsplit("-", 1)
        wrong_proto8 = "0" * 8 if proto8 != "0" * 8 else "f" * 8
        state["paths"]["result"] = selected_rel.replace(
            run_id, f"{timestamp}-{wrong_proto8}",
        )

    root, _freeze, _topology = _build_launch_repo(
        tmp_path, mutate=move_selected_result_to_wrong_proto8,
    )
    loaded = M.load_ratified_freeze(root)
    with pytest.raises(M.RatifiedFreezeError) as caught:
        M.assert_g1_floor_selection_identity(loaded, root)
    assert caught.value.reason == "floor-selection-unverifiable"
    assert caught.value.cause == "selection-path-proto8"


@in_sealed_fixture_process
def test_g1_selection_helper_accepts_valid_selection(tmp_path):
    root, freeze, _topology = _build_launch_repo(tmp_path)
    assert M.assert_g1_floor_selection_identity(freeze, root) is None


@in_sealed_fixture_process
def test_launch_validate_preserves_floor_selection_path_failure_reason(
        tmp_path, monkeypatch):
    root, freeze, _topology = _build_launch_repo(tmp_path)

    def path_failure(**_kwargs):
        raise HF.FreezeError(
            "floor selection namespace non-symlink directory chain を開けない"
        )

    monkeypatch.setattr(HF, "_assert_floor_selection_identity", path_failure)
    with pytest.raises(M.RatifiedFreezeError) as caught:
        M.launch_validate(freeze, root)
    assert caught.value.reason == "floor-selection-unverifiable"
    assert caught.value.cause == (
        "floor selection namespace non-symlink directory chain を開けない"
    )


@in_sealed_fixture_process
def test_historical_reverify_does_not_apply_current_floor_selection(
        tmp_path):
    root, freeze, _topology = _build_launch_repo(tmp_path)
    freeze, _earlier_rel = _with_earlier_floor_result_at_head(root, freeze)
    reverified = M.reverify_published_freeze(freeze, root)
    assert type(reverified) is M.ReverifiedFreeze


def test_reverify_rejects_unreachable_admission_root(tmp_path):
    root, freeze, _ = _build_independent_launch_repo(tmp_path)
    admission_root = root / ".git/izanagi/s8b-holdout-admission-v1"
    admission_root.rename(admission_root.with_name("admission-unavailable"))
    with pytest.raises(M.RatifiedFreezeError) as caught:
        M.launch_validate(freeze, root)
    assert caught.value.reason == "floor-admission-unverifiable"
    assert caught.value.cause == "root-missing"


def test_reverify_rejects_admission_claim_content_mismatch(tmp_path):
    root, freeze, _ = _build_independent_launch_repo(tmp_path)
    claims = sorted(
        (root / ".git/izanagi/s8b-holdout-admission-v1/claims").glob("*.claim")
    )
    assert claims
    claims[0].write_bytes(b"{}\n")
    with pytest.raises(M.RatifiedFreezeError) as caught:
        M.launch_validate(freeze, root)
    assert caught.value.reason == "floor-admission-mismatch"
    assert caught.value.cause == "claim-file-mismatch"


def test_reverify_rejects_reported_true_when_live_basis_is_disqualified(tmp_path):
    root, freeze, _ = _build_independent_launch_repo(tmp_path)
    claims = sorted(
        (root / ".git/izanagi/s8b-holdout-admission-v1/claims").glob("*.claim")
    )
    assert claims
    for path in claims:
        claim = json.loads(path.read_bytes())
        claim["nondefault_seams"] = ["build_fn"]
        path.write_bytes(M._canonical_bytes(claim) + b"\n")

    with pytest.raises(M.RatifiedFreezeError) as caught:
        M.launch_validate(freeze, root)
    assert caught.value.reason == "floor-admission-mismatch"
    assert caught.value.cause == "refreeze-eligibility-mismatch"


@in_sealed_fixture_process
def test_public_reverify_accepts_recorded_g1_under_g2_current_while_live_refuses(
        tmp_path):
    """read-only public 入口だけが記録 g1 を解決し、live admission は current g2 に留まる。"""
    _need_v1()
    root, freeze, topology = _build_launch_repo(tmp_path)
    g1 = EC.lookup(topology["protocol"]["env_tag"])
    g2 = dataclasses.replace(
        g1,
        calibration_ref=EC.CalibrationRef(
            path=g1.calibration_ref.path + ".successor",
            sha256="f" * 64,
        ),
    )
    assert EC.is_valid_successor(g1, g2)
    candidate = {
        g1.env_tag: (
            EC.GenerationEntry(generation=1, contract=g1),
            EC.GenerationEntry(generation=2, contract=g2),
        ),
    }
    assert EC._validate_generations_without_bootstrap_fuse(candidate) is None
    assert EC.validate_generations(candidate) is None
    assert EC.lookup(g1.env_tag) is g1
    historical = mock.Mock(wraps=EC.resolve_by_contract_sha256)
    journal_spy = mock.Mock(wraps=M._validate_journal)
    result_spy = mock.Mock(wraps=M._validate_result)
    run_cmd_spy = mock.Mock(wraps=M._run_cmd_matches_portable_session)
    occurrence_spy = mock.Mock(wraps=M._validate_axis_occurrences)

    with mock.patch.object(M._env_contract, "lookup", return_value=g2), \
            mock.patch.object(
                M._env_contract, "resolve_by_contract_sha256", historical,
            ), mock.patch.object(M, "_validate_journal", journal_spy), \
            mock.patch.object(M, "_validate_result", result_spy), \
            mock.patch.object(M, "_run_cmd_matches_portable_session", run_cmd_spy), \
            mock.patch.object(M, "_validate_axis_occurrences", occurrence_spy):
        reverified = M.reverify_published_freeze(freeze, root)
        with pytest.raises(M.RatifiedFreezeError) as excinfo:
            M.launch_validate(freeze, root)

    assert type(reverified) is M.ReverifiedFreeze
    assert not isinstance(reverified, M.LaunchValidatedFreeze)
    assert historical.call_count == 1
    assert historical.call_args.args == (g1.contract_sha256,)
    assert historical.call_args.kwargs == {"expected_env_tag": g1.env_tag}
    assert journal_spy.call_args.kwargs["contract"] is g1
    assert result_spy.call_args.kwargs["contract"] is g1
    assert occurrence_spy.call_args.kwargs["contract"] is g1
    assert run_cmd_spy.call_count > 0
    assert all(call.kwargs["contract"] is g1 for call in run_cmd_spy.call_args_list)
    assert excinfo.value.reason == "floor-artifact-invalid"
    assert excinfo.value.cause == "protocol-invalid"


@pytest.mark.parametrize(
    "case_id",
    ["malformed", "unknown", "ambiguous", "cross-env", "dishonest-resolver"],
)
@in_sealed_fixture_process
def test_public_reverify_resolver_refusals_do_not_fallback_to_current(
        tmp_path, case_id):
    """public read-only 入口は resolver 拒否・不正返却を current lookup で救済しない。

    ambiguous / dishonest は patch-only の構造防御であり production artifact から
    到達しない。
    """
    _need_v1()
    root, freeze, topology = _build_launch_repo(tmp_path)
    g1 = EC.lookup(topology["protocol"]["env_tag"])
    foreign = EC.GenerationEntry(generation=1, contract=EC.lookup("pegasus"))

    def resolve(recorded, *, expected_env_tag=None):
        assert recorded == g1.contract_sha256
        if case_id == "cross-env" and expected_env_tag is None:
            return EC.GenerationEntry(generation=1, contract=g1)
        if case_id == "dishonest-resolver":
            return foreign
        messages = {
            "malformed": "contract_sha256 は 64 桁の小文字 hex でない",
            "unknown": "未知の contract_sha256",
            "ambiguous": "contract_sha256 を一意に解決できない",
            "cross-env": "expected_env_tag と一致しない",
        }
        raise EC.EnvContractError(messages[case_id])

    resolver = mock.Mock(side_effect=resolve)
    current_fallback = mock.Mock(
        side_effect=AssertionError("read-only 再検証が current lookup へ fallback した"),
    )
    with mock.patch.object(M._env_contract, "lookup", current_fallback), \
            mock.patch.object(
                M._env_contract, "resolve_by_contract_sha256", resolver,
            ):
        with pytest.raises(M.RatifiedFreezeError) as excinfo:
            M.reverify_published_freeze(freeze, root)

    assert excinfo.value.reason == "floor-artifact-invalid"
    assert excinfo.value.cause == "protocol-invalid"
    assert resolver.call_count == 1
    assert resolver.call_args.kwargs == {"expected_env_tag": g1.env_tag}
    current_fallback.assert_not_called()


@in_sealed_fixture_process
def test_public_reverify_rejects_dishonest_same_env_wrong_hash_resolver(tmp_path):
    """same-env/wrong-hash 返却は patch-only の構造防御であり、
    production artifact から到達しない。"""
    _need_v1()
    root, freeze, topology = _build_launch_repo(tmp_path)
    g1 = EC.lookup(topology["protocol"]["env_tag"])
    wrong = dataclasses.replace(
        g1,
        calibration_ref=EC.CalibrationRef(
            path=g1.calibration_ref.path + ".dishonest",
            sha256="e" * 64,
        ),
    )
    assert wrong.env_tag == g1.env_tag
    assert wrong.contract_sha256 != g1.contract_sha256
    resolver = mock.Mock(
        return_value=EC.GenerationEntry(generation=2, contract=wrong),
    )
    current_fallback = mock.Mock(
        side_effect=AssertionError("dishonest resolver 拒否後に current へ fallback した"),
    )

    with mock.patch.object(M._env_contract, "lookup", current_fallback), \
            mock.patch.object(
                M._env_contract, "resolve_by_contract_sha256", resolver,
            ):
        with pytest.raises(M.RatifiedFreezeError) as excinfo:
            M.reverify_published_freeze(freeze, root)

    assert excinfo.value.reason == "floor-artifact-invalid"
    assert excinfo.value.cause == "protocol-invalid"
    assert resolver.call_count == 1
    assert resolver.call_args.args == (g1.contract_sha256,)
    assert resolver.call_args.kwargs == {"expected_env_tag": g1.env_tag}
    current_fallback.assert_not_called()


@pytest.mark.parametrize(
    "case_id",
    ["missing-calibration", "calibration-hash-mismatch"],
)
@in_sealed_fixture_process
def test_public_reverify_calibration_refusals_do_not_fallback_to_current(
        tmp_path, case_id):
    """解決世代の calibration が読めなければ public read-only 入口全体を拒否する。"""
    _need_v1()
    root, freeze, topology = _build_launch_repo(tmp_path)
    g1 = EC.lookup(topology["protocol"]["env_tag"])
    resolver = mock.Mock(wraps=EC.resolve_by_contract_sha256)
    current_fallback = mock.Mock(
        side_effect=AssertionError("calibration 拒否後に current lookup へ fallback した"),
    )
    calibration_path = root / g1.calibration_ref.path
    if case_id == "missing-calibration":
        calibration_path.unlink()
        expected_detail = "存在しない"
    else:
        calibration_path.write_bytes(b"tampered historical calibration\n")
        expected_detail = "calibration sha256 不一致"

    with mock.patch.object(M._env_contract, "lookup", current_fallback), \
            mock.patch.object(
                M._env_contract, "resolve_by_contract_sha256", resolver,
            ):
        with pytest.raises(M.RatifiedFreezeError) as excinfo:
            M.reverify_published_freeze(freeze, root)

    assert excinfo.value.reason == "journal-state-invalid"
    assert excinfo.value.cause == "receipt-contract"
    assert expected_detail in str(excinfo.value)
    assert resolver.call_count == 1
    current_fallback.assert_not_called()


# --------------------------------------------------------------------------
# V1 — source blob + G^==frozen_at_head + closure
# --------------------------------------------------------------------------

@in_sealed_fixture_process
def test_source_blob_mismatch_rejected(tmp_path):
    _need_v1()
    _assert_emitter_baseline(tmp_path / "baseline")
    def mut(g1):
        g1["generator"] = {"path": g1["generator"]["path"], "sha256": "a" * 64}
    root, *_ = B.build_production_emitter_g1(tmp_path / "mutation", mutate_g1=mut)
    _assert_registered_refusal("source", lambda: M.load_ratified_freeze(root))


@in_sealed_fixture_process
def test_design_source_worktree_drift_still_loads(tmp_path):
    _need_v1()
    # V5 (陽性テスト): design_source が指す docs 系 file の worktree copy を未 commit で
    # 改変しても load_ratified_freeze は成功する。V1b は frozen_at_head の **blob bytes** を
    # 照合するため worktree drift に非依存 (D5' の意図)。design_source は closure でも
    # floor_protocol/floor_source でも namespace (output/s8b-freeze/) でもないため、dirty
    # 拒否 (closure-dirty / namespace-dirty) の経路には触れない。
    #
    # 変異 = V1b の blob 読みを worktree 読み化 → 改変後 bytes が記録 sha と食い違い
    # source-blob-mismatch で落ち、この陽性テストが赤になる。
    root, _gen_sha, _gen_rel, g1, _topology = B.build_production_emitter_g1(tmp_path)
    ds_path = g1["design_source"]["path"]         # docs 系 file (closure/namespace 外)
    assert not ds_path.startswith(M.FREEZE_DIR)    # namespace-dirty 経路に触れないことの前提
    target = root / ds_path
    assert target.is_file()
    # worktree copy に未 commit の drift を注入 (blob は不変のまま)。
    target.write_bytes(target.read_bytes() + b"\n# uncommitted worktree drift\n")

    freeze = M.load_ratified_freeze(root)          # blob 照合なので成功するのが正
    assert isinstance(freeze, M.RatifiedFreeze)
    assert freeze.generation_number == 1


@in_sealed_fixture_process
def test_frozen_at_head_not_generation_parent_rejected(tmp_path):
    _need_v1()
    _assert_emitter_baseline(tmp_path / "baseline")
    def mut(g1):
        g1["frozen_at_head"] = "0" * 40  # 形式は妥当だが G^ でない
    root, *_ = B.build_production_emitter_g1(tmp_path / "mutation", mutate_g1=mut)
    _assert_registered_refusal("frozen", lambda: M.load_ratified_freeze(root))


def test_generation_commit_merge_rejected(tmp_path):
    _need_v1()
    # 世代 file を merge commit で導入する (両親に g1 は不在)。structural 層の
    # _assert_candidate_commit が merge を拒否する (generation-commit-merge)。
    root = _build_merge_introduced_g1(tmp_path)
    with pytest.raises(M.RatifiedFreezeError) as ei:
        M.resolve_active_generation(root)
    assert ei.value.reason == "generation-commit-merge"


@in_sealed_fixture_process
def test_closure_entry_absent_from_generation_tree_rejected(tmp_path):
    _need_v1()
    _assert_emitter_baseline(tmp_path / "baseline")
    def mut(g1):
        g1["measurement_closure"].append(
            {"canonical_path": "output/env/floor/missing.json", "sha256": "b" * 64}
        )
    root, *_ = B.build_production_emitter_g1(tmp_path / "mutation", mutate_g1=mut)
    _assert_registered_refusal("closure-missing", lambda: M.load_ratified_freeze(root))


@in_sealed_fixture_process
def test_closure_bytes_sha_mismatch_rejected(tmp_path):
    _need_v1()
    _assert_emitter_baseline(tmp_path / "baseline")
    def mut(g1):
        g1["measurement_closure"][0]["sha256"] = "c" * 64  # bytes は改竄せず記録 sha を偽る
    root, *_ = B.build_production_emitter_g1(tmp_path / "mutation", mutate_g1=mut)
    _assert_registered_refusal("closure-sha", lambda: M.load_ratified_freeze(root))


@in_sealed_fixture_process
def test_env_tag_unknown_rejected(tmp_path):
    _need_v1()
    _assert_emitter_baseline(tmp_path / "baseline")
    def mut(g1):
        g1["env_tag"] = "mars-rover-unregistered"
    root, *_ = B.build_production_emitter_g1(tmp_path / "mutation", mutate_g1=mut)
    _assert_registered_refusal("env", lambda: M.load_ratified_freeze(root))


# --------------------------------------------------------------------------
# V2 — transition table (F5 JSON Pointer 完全列挙)
# --------------------------------------------------------------------------

@pytest.mark.parametrize("mut", [
    lambda g1: g1.__setitem__("what", "tampered what"),           # protected top-level
    lambda g1: g1.__setitem__("confirmed_by", "attacker"),        # protected
    lambda g1: g1.__setitem__("match_convention", "loosened"),    # protected
    lambda g1: g1.__setitem__("scope_note", "tampered scope"),    # protected
    lambda g1: g1["derangement"].__setitem__("rr80", "rr80"),     # protected nested
])
@in_sealed_fixture_process
def test_transition_out_of_enumeration_diff_rejected(tmp_path, mut):
    _need_v1()
    _assert_emitter_baseline(tmp_path / "baseline")
    root, *_ = B.build_production_emitter_g1(
        tmp_path / "mutation", mutate_g1=mut)
    _assert_registered_refusal("transition", lambda: M.load_ratified_freeze(root))


def test_transition_gn_to_gn1_env_tag_change_rejected_unit():
    # gN→gN+1 の transition table は env_tag を allowed に含めない (環境が変わる = 別実験)。
    # 登録済み代替 env_tag が 1 つしか無く V1c が先に発火するため、transition table を直接駆動する。
    prev = {"env_tag": "linux-baremetal", "floor": None}
    nxt = {"env_tag": "linux-baremetal-2", "floor": None}
    with pytest.raises(M.RatifiedFreezeError) as ei:
        M._assert_transition(prev, nxt, M._TRANSITION_GN_TO_GN1, label="g1→g2")
    assert ei.value.reason == "transition-violation"


def test_transition_gn_to_gn1_allows_floor_change_unit():
    # 逆に floor/floor_protocol/measurement_closure/header は gN→gN+1 で変わってよい (正常系)。
    # 裁定根拠: docs/phase3-8b-descriptor-design.md:381 の F5。
    assert {
        "/floor", "/floor_protocol", "/floor_source", "/measurement_closure",
        "/generation_number",
    } <= M._TRANSITION_GN_TO_GN1
    assert "/env_tag" not in M._TRANSITION_GN_TO_GN1
    prev = {"env_tag": "linux-baremetal", "floor": None, "generation_number": 1}
    nxt = {"env_tag": "linux-baremetal", "floor": {"rr80": 1.0}, "generation_number": 2}
    M._assert_transition(prev, nxt, M._TRANSITION_GN_TO_GN1, label="g1→g2")  # 例外なし


@pytest.mark.parametrize("field", ["holdouts", "derangement"])
def test_transition_gn_to_gn1_forbids_measurement_field_rewrite_unit(field):
    # V4: gN→gN+1 で /holdouts・/derangement (workload identity) を書き換える世代対は拒否する。
    # 両者は _TRANSITION_GN_TO_GN1 の列挙外 (protected) — 列挙外 pointer の変化は
    # transition-violation。header (generation_number) だけが allowed で変わる。
    # `field="holdouts"` は「_TRANSITION_GN_TO_GN1 に /holdouts を追加する」変異を殺す
    # (allowed に入ると /holdouts の書換えが素通りし、この case が赤になる)。
    prev = {
        "generation_number": 1,
        "holdouts": {"rr80": {"records": 1000000}},
        "derangement": {"rr80": "rr20"},
    }
    nxt = {
        "generation_number": 2,  # allowed (header) — 変わってよい
        "holdouts": {"rr80": {"records": 1000000}},
        "derangement": {"rr80": "rr20"},
    }
    # 対象 field の nested leaf を 1 つ書き換える (列挙外の diff)。
    if field == "holdouts":
        nxt["holdouts"] = {"rr80": {"records": 2000000}}
    else:
        nxt["derangement"] = {"rr80": "rr50"}
    with pytest.raises(M.RatifiedFreezeError) as ei:
        M._assert_transition(prev, nxt, M._TRANSITION_GN_TO_GN1, label="g1→g2")
    assert ei.value.reason == "transition-violation"


@in_sealed_fixture_process
def test_chain_g2_env_tag_unchanged_loads(tmp_path):
    _need_v1()
    # env_tag を保ち、新 C2 と新 run artifacts を持つ g2 は静的 load までは正常。
    root, g1_sha, _g1_rel, g1, topology = B.build_production_emitter_g1(tmp_path)
    freeze, g2_topology = B.append_production_emitter_g2(
        root, g1, g1_sha, topology)
    assert freeze.generation_number == 2
    assert g2_topology["C2"] != g2_topology["G2"] != g2_topology["A2"] != g2_topology["X2"]


# --------------------------------------------------------------------------
# V3 — 二層未知性 + closure (launch_validate)
# --------------------------------------------------------------------------

def test_layer1_snapshot_tamper_rejected_unit():
    # holdouts は transition で protected のため、層1 単体を直接駆動して改竄検出を確認する。
    doc = json.loads(_REAL_V1.read_bytes()) if _REAL_V1.is_file() else None
    if doc is None:
        pytest.fail("実 v1 freeze が無い (trust root 不在 — skip すると攻撃 matrix が緑化する。failures F9 型)")
    name = next(iter(HF.HOLDOUTS))
    doc["holdouts"][name]["unknownness_check"]["zero_hit_output_sha256"] = "e" * 64
    with pytest.raises(M.RatifiedFreezeError) as ei:
        M._verify_snapshot_layer1(doc)
    assert ei.value.reason == "layer1-snapshot-mismatch"


@in_sealed_fixture_process
def test_undeclared_hit_outside_closure_rejected(tmp_path):
    _need_v1()
    root, freeze, _ = _build_launch_repo(tmp_path)
    assert isinstance(M.launch_validate(freeze, root), M.LaunchValidatedFreeze)
    # closure 外の untracked ファイルに rr80 params を仕込む → 現 search に未申告 hit が出る。
    (root / "sneaky_measurement.txt").write_bytes(B._RR80_PARAMS)
    _assert_registered_refusal("scan-undeclared", lambda: M.launch_validate(freeze, root))


@in_sealed_fixture_process
def test_declared_closure_hit_absent_from_search_rejected(tmp_path, monkeypatch):
    _need_v1()
    # 正しい G bytes から導出した declared closure path を scan report だけから 1 件落とす。
    # expected/current の missing 側比較が実際に発火することを、issuer helper 非依存で固定する。
    root, freeze, topology = _build_launch_repo(tmp_path)
    hidden = topology["paths"]["closure80"]
    real_search = HF.search_repository
    assert isinstance(M.launch_validate(freeze, root), M.LaunchValidatedFreeze)

    def missing_declared(r=root, files=None, exempt_exact=None):
        report = real_search(r, files=files, exempt_exact=exempt_exact)
        report["holdouts"]["rr80"]["conjunction_hits"].remove(hidden)
        return report

    monkeypatch.setattr(M._hf, "search_repository", missing_declared)
    _assert_registered_refusal("scan-missing", lambda: M.launch_validate(freeze, root))


@in_sealed_fixture_process
def test_extra_closure_in_freeze_namespace_rejected_without_broad_closed_world(tmp_path):
    _need_v1()
    root, _gen_sha, _gen_rel, _g1, _topology = B.build_production_emitter_g1(
        tmp_path,
        extra_closure=[("output/s8b-freeze/hidden_measure.json", B._RR80_PARAMS)],
    )
    freeze = M.load_ratified_freeze(root)
    _assert_registered_refusal(
        "closure-namespace", lambda: M.launch_validate(freeze, root))


@in_sealed_fixture_process
def test_per_holdout_no_crosstalk(tmp_path):
    _need_v1()
    # V1: per-holdout の hit 集合比較が「どの holdout が不一致か」を正しく帰属することを固定する。
    #
    # closure bytes pin + dirty 拒否の下では、全 holdout を束ねた union 比較と per-holdout
    # 比較は「拒否するか否か」では等価 (未申告 hit が 1 つでもあれば両者とも closure-hit-mismatch)。
    # 差が出るのは例外に載る**帰属情報**だけ: per-holdout は不一致 holdout 名 (rr80) を前置し、
    # union は名前を持たない。よってこのテストは reason ではなく帰属 (holdout 名) を検査する。
    #
    # 未申告 hit ファイルは holdout 名を含まない名前 (extra_conflict.txt) にする。これで
    # "rr80" が例外 message に現れる唯一の経路が per-holdout 帰属 (f"{name}: ...") に限定され、
    # ファイル名の偶然一致で素通りしない。per-holdout→union 化の変異は、帰属が消えて
    # "rr80" が message から失われるためこのテストで殺せる (下記 assert が赤になる)。
    root, freeze, _ = _build_launch_repo(tmp_path)
    assert isinstance(M.launch_validate(freeze, root), M.LaunchValidatedFreeze)
    # closure は f80/f20 両方宣言済み。rr80 params を持つ untracked hit を rr80 名を含まない
    # ファイル名で追加し、rr80 の hit 集合だけを未申告で不一致にする (rr20 は一致のまま)。
    (root / "extra_conflict.txt").write_bytes(B._RR80_PARAMS)
    error = _assert_registered_refusal(
        "scan-per-holdout", lambda: M.launch_validate(freeze, root))
    message = str(error)
    # 帰属検査: 不一致は rr80 の hit 集合。ファイル名 (extra_conflict.txt) も未申告 hit の
    # path も "rr80" を含まないため、message 中の "rr80" は per-holdout 帰属からしか来ない。
    assert "rr80" in message, message
    # 未申告ファイルが帰属に載る (per-holdout 検査が現/期待の差を取れている)。
    assert "extra_conflict.txt" in message, message


@in_sealed_fixture_process
def test_enumeration_digest_shift_rejected(tmp_path, monkeypatch):
    _need_v1()
    root, freeze, _ = _build_launch_repo(tmp_path)
    real_search = HF.search_repository
    assert isinstance(M.launch_validate(freeze, root), M.LaunchValidatedFreeze)

    def racing_search(r=root, files=None, exempt_exact=None):
        # search 実行中に untracked ファイルを増やし、列挙前後 digest を食い違わせる。
        (Path(r) / "added_mid_scan.txt").write_text("x\n", encoding="utf-8")
        return real_search(r, files=files, exempt_exact=exempt_exact)

    monkeypatch.setattr(M._hf, "search_repository", racing_search)
    _assert_registered_refusal("scan-enumeration", lambda: M.launch_validate(freeze, root))


@in_sealed_fixture_process
def test_positive_control_not_hit_rejected(tmp_path):
    _need_v1()
    # 陽性対照 (rr50) file の内容を無害化する (rr50 params を含まない bytes に差し替える)。
    # search は worktree を直読みするため、この改変だけで陽性対照が 0 hit になる。
    root, freeze, _ = _build_launch_repo(tmp_path)
    assert isinstance(M.launch_validate(freeze, root), M.LaunchValidatedFreeze)
    contract = EC.lookup("linux-baremetal")
    verified_calibration = M._env_attestation.load_verified_calibration(contract, root)
    (root / "positive_control.txt").write_bytes(b"neutralized, no ycsb params here\n")
    # calibration v1 自体にも rr50 workload が記録されるため、search positive control
    # の独立 fixture ではその検索 hit だけを中立化する。consumer admission は改変前に
    # 実 bytes から得た verified 値を固定し、このテストの攻撃面を scan に限定する。
    (root / contract.calibration_ref.path).write_bytes(b"neutralized calibration scan input\n")
    with mock.patch.object(M._env_attestation, "load_verified_calibration",
                           return_value=verified_calibration):
        _assert_registered_refusal("scan-positive", lambda: M.launch_validate(freeze, root))


@in_sealed_fixture_process
def test_activation_head_moved_rejected(tmp_path):
    _need_v1()
    root, freeze, _ = _build_launch_repo(tmp_path)
    # load 後に HEAD を進める (無害な commit)。launch 直前の H 一致再確認で拒否。
    (root / "later.txt").write_text("later\n", encoding="utf-8")
    _lcommit(root, "later commit", "fixture")
    with pytest.raises(M.RatifiedFreezeError) as ei:
        M.launch_validate(freeze, root)
    assert ei.value.reason == "activation-head-moved"


@in_sealed_fixture_process
def test_generation_two_rejected_before_artifact_io(tmp_path, monkeypatch):
    _need_v1()
    root, g1_sha, _g1_rel, g1, topology = B.build_production_emitter_g1(
        tmp_path, generation_strings_escaped=True)
    g2, _g2_topology = B.append_production_emitter_g2(root, g1, g1_sha, topology)
    # 静的層の成功を先に固定し、実在する全 g2 artifact より generation scope が先行する。
    loaded = M.load_ratified_freeze(root)
    assert loaded.sha256 == g2.sha256 and loaded.generation_number == 2
    _assert_registered_refusal("generation-scope", lambda: M.launch_validate(g2, root))

    # 同じ g2 fixture の scope 値だけを一貫して 1 に射影すると full validate が通る。
    # これにより generation-scope 以外の gate がすべて green なことを pin する。
    forced = M.RatifiedFreeze(
        document=g2.document, sha256=g2.sha256, generation_number=1,
        activation_head=g2.activation_head, generation_commit=g2.generation_commit,
    )
    real_resolve = M.resolve_active_generation

    def resolve_with_forced_scope(candidate_root):
        resolution = real_resolve(candidate_root)
        return M.ActiveResolution(
            activation_head=resolution.activation_head,
            generation_number=1,
            generation_path=resolution.generation_path,
            generation_bytes=resolution.generation_bytes,
            generation_sha256=resolution.generation_sha256,
            generation_commit=resolution.generation_commit,
            approval_sha256=resolution.approval_sha256,
            approval_document=resolution.approval_document,
            pointer_sha256=resolution.pointer_sha256,
            pointer_document=resolution.pointer_document,
        )

    monkeypatch.setattr(M, "resolve_active_generation", resolve_with_forced_scope)
    assert isinstance(M.launch_validate(forced, root), M.LaunchValidatedFreeze)


@in_sealed_fixture_process
def test_g1_only_selection_helper_is_noop_for_g2(tmp_path, monkeypatch):
    _need_v1()
    root, g1_sha, _g1_rel, g1, topology = B.build_production_emitter_g1(
        tmp_path,
    )
    emitted_g2, _g2_topology = B.append_production_emitter_g2(
        root, g1, g1_sha, topology,
    )
    loaded_g2 = M.load_ratified_freeze(root)
    assert type(loaded_g2) is M.RatifiedFreeze
    assert loaded_g2.generation_number == 2
    assert loaded_g2.sha256 == emitted_g2.sha256

    def reject_any_source_inspection(*_args, **_kwargs):
        raise AssertionError("g2 selection helper inspected a source record")

    monkeypatch.setattr(M, "_source_record_path_sha", reject_any_source_inspection)
    assert M.assert_g1_floor_selection_identity(loaded_g2, root) is None


@in_sealed_fixture_process
def test_g1_only_selection_helper_skips_earlier_eligible_run_for_g2(
        tmp_path, monkeypatch):
    _need_v1()
    root, g1_sha, _g1_rel, g1, topology = B.build_production_emitter_g1(
        tmp_path,
    )
    B.append_production_emitter_g2(root, g1, g1_sha, topology)
    loaded_g2 = M.load_ratified_freeze(root)
    loaded_g2, earlier_rel = _with_earlier_floor_result_at_head(root, loaded_g2)
    calls = []

    def derived_eligible(**kwargs):
        calls.append(kwargs["result_rel"])
        return True

    monkeypatch.setattr(HF, "_derive_floor_selection_eligibility", derived_eligible)
    assert M.assert_g1_floor_selection_identity(loaded_g2, root) is None
    assert calls == []

    forced_g1 = M.RatifiedFreeze(
        document=loaded_g2.document, sha256=loaded_g2.sha256,
        generation_number=1, activation_head=loaded_g2.activation_head,
        generation_commit=loaded_g2.generation_commit,
    )
    with pytest.raises(M.RatifiedFreezeError) as caught:
        M.assert_g1_floor_selection_identity(forced_g1, root)
    assert caught.value.reason == "floor-selection-rule-mismatch"
    assert caught.value.cause == "earliest-eligible-official-run-id/v1"
    assert calls == [earlier_rel]


@in_sealed_fixture_process
def test_manifest_cells_independent_derivation_rejects_ghost_cell(tmp_path):
    _need_v1()
    def mutate(state):
        ghost = dict(state["manifest"]["cells"][0])
        ghost["cell_id"] = "ghost::cell"
        state["manifest"]["cells"].append(ghost)
        state["repair_manifest"] = True
    root, freeze, _ = _build_launch_repo(tmp_path, mutate=mutate)
    with pytest.raises(M.RatifiedFreezeError) as ei:
        M.launch_validate(freeze, root)
    assert ei.value.reason == "manifest-invalid"
    assert ei.value.cause == "cells-derivation"


@in_sealed_fixture_process
def test_manifest_schedule_independent_derivation_rejected(tmp_path):
    _need_v1()
    def mutate(state):
        state["manifest"]["schedule"][0], state["manifest"]["schedule"][1] = (
            state["manifest"]["schedule"][1], state["manifest"]["schedule"][0])
        state["repair_manifest"] = True
    root, freeze, _ = _build_launch_repo(tmp_path, mutate=mutate)
    with pytest.raises(M.RatifiedFreezeError) as ei:
        M.launch_validate(freeze, root)
    assert ei.value.reason == "manifest-invalid"
    assert ei.value.cause == "schedule-derivation"


@in_sealed_fixture_process
def test_session_start_schedule_bijection_rejected(tmp_path):
    _need_v1()
    def mutate(state):
        first = next(r for r in state["journal"] if r["event"] == "session-start")
        first["cell_id"] = "ghost::cell"
    root, freeze, _ = _build_launch_repo(tmp_path, mutate=mutate)
    with pytest.raises(M.RatifiedFreezeError) as ei:
        M.launch_validate(freeze, root)
    assert ei.value.reason == "journal-state-invalid"
    assert ei.value.cause == "planned-schedule"


@in_sealed_fixture_process
def test_retry_authorization_outside_frozen_budget_rejected(tmp_path):
    _need_v1()
    def mutate(state):
        first = next(r for r in state["journal"] if r["event"] == "session-start")
        first["kind"] = "retry"
        first["retry_ordinal"] = 3
        first["trigger"] = "missing-planned-attempt"
        first["attempt_id"] = f"{first['cell_id']}::retry3"
    root, freeze, _ = _build_launch_repo(tmp_path, mutate=mutate)
    with pytest.raises(M.RatifiedFreezeError) as ei:
        M.launch_validate(freeze, root)
    assert ei.value.reason == "journal-state-invalid"
    assert ei.value.cause == "retry-authorization"


@in_sealed_fixture_process
def test_round_start_complete_state_machine_rejects_duplicate(tmp_path):
    _need_v1()
    def mutate(state):
        terminal = state["journal"].pop()
        state["journal"].append({
            "event": "round-complete", "round": 1, "utc": "2026-07-18T12:00:00+00:00",
        })
        state["journal"].append(terminal)
    root, freeze, _ = _build_launch_repo(tmp_path, mutate=mutate)
    with pytest.raises(M.RatifiedFreezeError) as ei:
        M.launch_validate(freeze, root)
    assert ei.value.reason == "journal-state-invalid"
    assert ei.value.cause == "round-state"


@pytest.mark.parametrize("terminal_mutation", [
    lambda journal: journal.insert(-1, {"event": "terminal", "status": "aborted", "reason": "x"}),
    lambda journal: journal.append({"event": "round-complete", "round": 8,
                                    "utc": "2026-07-18T12:00:00+00:00"}),
    lambda journal: journal[-1].__setitem__("status", "aborted"),
])
@in_sealed_fixture_process
def test_terminal_unique_final_completed_required(tmp_path, terminal_mutation):
    _need_v1()
    def mutate(state):
        terminal_mutation(state["journal"])
        if state["journal"][-1].get("event") == "terminal" \
                and state["journal"][-1].get("status") == "aborted":
            state["journal"][-1]["reason"] = "x"
    root, freeze, _ = _build_launch_repo(tmp_path, mutate=mutate)
    with pytest.raises(M.RatifiedFreezeError) as ei:
        M.launch_validate(freeze, root)
    assert ei.value.reason == "journal-state-invalid"


@in_sealed_fixture_process
def test_result_unknown_key_strict_schema_rejected(tmp_path):
    _need_v1()
    def mutate(state):
        state["result"]["unknown_free_text"] = "x"
    root, freeze, _ = _build_launch_repo(tmp_path, mutate=mutate)
    with pytest.raises(M.RatifiedFreezeError) as ei:
        M.launch_validate(freeze, root)
    assert ei.value.reason == "floor-artifact-invalid"
    assert ei.value.cause == "schema-keys"


@in_sealed_fixture_process
def test_eligible_requires_bool_true_not_integer_one(tmp_path):
    _need_v1()
    def mutate(state):
        state["result"]["eligible_for_refreeze"] = 1
    root, freeze, _ = _build_launch_repo(tmp_path, mutate=mutate)
    with pytest.raises(M.RatifiedFreezeError) as ei:
        M.launch_validate(freeze, root)
    assert ei.value.reason == "binding-chain-mismatch"
    assert ei.value.cause == "eligible-flag"


@in_sealed_fixture_process
def test_verified_floor_artifact_and_binary_index_are_deep_frozen(tmp_path):
    _need_v1()
    root, freeze, topology = _build_launch_repo(tmp_path)
    validated = M.launch_validate(freeze, root)
    first_cell = next(iter(topology["result"]["cells"]))
    topology["result"]["cells"][first_cell]["valid"] = False
    assert validated.floor_artifact.document["cells"][first_cell]["valid"] is True
    with pytest.raises(TypeError):
        validated.floor_artifact.document["cells"][first_cell]["valid"] = False
    with pytest.raises(TypeError):
        validated.binaries_by_cell[first_cell]["cached"] = True


@pytest.mark.parametrize(
    "case_id",
    ["binaries-cell-set", "binary-cell-binding", "binary-hash", "binding-sha"],
)
@in_sealed_fixture_process
def test_portable_binary_coherent_island_rejected_by_exact_cause(tmp_path, case_id):
    _need_v1()
    _assert_emitter_baseline(tmp_path / "baseline")
    root, freeze, _ = _build_launch_repo(
        tmp_path / "mutation",
        mutate=lambda state: _mutate_portable_binary_island(state, case_id),
    )
    _assert_registered_refusal(case_id, lambda: M.launch_validate(freeze, root))


@in_sealed_fixture_process
def test_production_shape_run_cmd_calls_exact_portable_matcher(tmp_path):
    _need_v1()
    root, freeze, topology = _build_launch_repo(tmp_path)
    session = next(r for r in topology["journal"] if r["event"] == "session")
    assert session["run_cmd"] is not None
    assert M._run_cmd_matches_portable_session(
        session, protocol=topology["protocol"], binaries=topology["manifest"]["binaries"],
        contract=EC.lookup(topology["protocol"]["env_tag"]),
    )
    assert M.launch_validate(freeze, root).floor_artifact.document["sessions"][0]["run_cmd"]


@in_sealed_fixture_process
def test_run_cmd_projection_uses_passed_contract_as_structural_pin(tmp_path):
    """これは構造 pin であって受理正例ではない。正当な successor では
    clocks_per_us / numactl は世代間で同値になるため、この unit でしか検出できない。"""
    _need_v1()
    _root, _freeze, topology = _build_launch_repo(tmp_path)
    session = dict(next(r for r in topology["journal"] if r["event"] == "session"))
    base = EC.lookup(topology["protocol"]["env_tag"])
    sentinel = dataclasses.replace(base, clocks_per_us=base.clocks_per_us + 1)
    binary = topology["manifest"]["binaries"][session["cell_id"]]["binary"]
    session["run_cmd"] = shlex.join(FC.build_portable_run_cmd(
        binary=binary, workload=session["workload"], records=session["records"],
        threads=session["threads"], extime_s=topology["protocol"]["extime_s"],
        clocks_per_us=sentinel.clocks_per_us, numactl=sentinel.numactl,
    ))

    assert M._run_cmd_matches_portable_session(
        session, protocol=topology["protocol"],
        binaries=topology["manifest"]["binaries"], contract=sentinel,
    )
    assert not M._run_cmd_matches_portable_session(
        session, protocol=topology["protocol"],
        binaries=topology["manifest"]["binaries"], contract=base,
    )


def _mutate_run_cmd(state, mutation: str, *, result_only: bool = False) -> None:
    journal_session = next(r for r in state["journal"] if r["event"] == "session")
    result_session = next(
        r for r in state["result"]["sessions"] if r["seq"] == journal_session["seq"])
    argv = shlex.split(journal_session["run_cmd"])
    if mutation == "prefix":
        argv[:0] = ["env", "INJECTED=1"]
    elif mutation == "binary":
        argv[argv.index("--") + 1] = "output/foreign-store/bench"
    elif mutation == "flag-order":
        workload_count = len(journal_session["workload"])
        assert workload_count >= 2
        argv[-workload_count], argv[-workload_count + 1] = (
            argv[-workload_count + 1], argv[-workload_count])
    elif mutation == "other-holdout-axis":
        other = next(
            r for r in state["journal"]
            if r.get("event") == "session"
            and r["holdout_id"] != journal_session["holdout_id"])
        changed = False
        for key in sorted(journal_session["workload"]):
            if journal_session["workload"][key] != other["workload"][key]:
                old = f"-{key}={journal_session['workload'][key]}"
                argv[argv.index(old)] = f"-{key}={other['workload'][key]}"
                changed = True
                break
        assert changed
    else:  # pragma: no cover - test helper closed world
        raise AssertionError(mutation)
    mutated = shlex.join(argv)
    result_session["run_cmd"] = mutated
    if not result_only:
        journal_session["run_cmd"] = mutated


@pytest.mark.parametrize(
    "mutation", ["prefix", "binary", "flag-order", "other-holdout-axis"],
)
@in_sealed_fixture_process
def test_run_cmd_projection_tamper_rejected_end_to_end(tmp_path, mutation):
    _need_v1()
    root, freeze, _ = _build_launch_repo(
        tmp_path, mutate=lambda state: _mutate_run_cmd(state, mutation))
    with pytest.raises(M.RatifiedFreezeError) as ei:
        M.launch_validate(freeze, root)
    assert ei.value.reason == "journal-state-invalid"
    assert ei.value.cause == "run-cmd-projection"


@in_sealed_fixture_process
def test_result_run_cmd_projection_is_independently_rejected(tmp_path):
    _need_v1()
    root, freeze, _ = _build_launch_repo(
        tmp_path, mutate=lambda state: _mutate_run_cmd(
            state, "prefix", result_only=True))
    with pytest.raises(M.RatifiedFreezeError) as ei:
        M.launch_validate(freeze, root)
    assert ei.value.reason == "floor-artifact-invalid"
    assert ei.value.cause == "run-cmd-projection"


@in_sealed_fixture_process
def test_valid_session_requires_run_cmd_even_when_journal_and_result_agree(tmp_path):
    _need_v1()
    _assert_emitter_baseline(tmp_path / "baseline")

    def mutate(state):
        journal_session = next(r for r in state["journal"] if r["event"] == "session")
        result_session = next(
            r for r in state["result"]["sessions"] if r["seq"] == journal_session["seq"])
        assert journal_session["valid"] is True and result_session["valid"] is True
        journal_session["run_cmd"] = None
        result_session["run_cmd"] = None

    root, freeze, _ = _build_launch_repo(tmp_path / "mutation", mutate=mutate)
    _assert_registered_refusal(
        "valid-run-cmd-required", lambda: M.launch_validate(freeze, root))


def test_run_id_timestamp_to_certificate_time_wiring_rejects_coherent_island(tmp_path):
    """cert と journal の時刻島を一緒にずらしても official path anchor が拒否する。"""
    _need_v1()
    shifted = "2026-07-18T12:00:01+00:00"
    root, freeze, _ = _build_independent_launch_repo(
        tmp_path, cert_mutate=lambda cert: cert.__setitem__("started_utc", shifted))
    with pytest.raises(M.RatifiedFreezeError) as ei:
        M.launch_validate(freeze, root)
    assert ei.value.reason == "binding-chain-mismatch"
    assert ei.value.cause == "certificate-invalid"


def test_certificate_to_launch_start_time_wiring_rejects_single_field(tmp_path):
    _need_v1()
    def mutate(state):
        state["journal"][0]["utc"] = "2026-07-18T12:00:01+00:00"
    root, freeze, _ = _build_independent_launch_repo(tmp_path, mutate=mutate)
    with pytest.raises(M.RatifiedFreezeError) as ei:
        M.launch_validate(freeze, root)
    assert ei.value.cause == "equality-edge:cert.started_utc->journal.launch-start.utc"


@in_sealed_fixture_process
def test_result_raw_sha_to_floor_source_wiring_rejects_semantic_island(tmp_path):
    """同じ parsed result を保つ trailing whitespace tamper でも raw hash anchor が拒否する。"""
    _need_v1()
    def mutate(state):
        state["post_hash_result_suffix"] = b" "
    root, freeze, _ = _build_launch_repo(tmp_path, mutate=mutate)
    with pytest.raises(M.RatifiedFreezeError) as ei:
        M.launch_validate(freeze, root)
    assert ei.value.reason == "floor-artifact-invalid"
    assert ei.value.cause == "result-record-sha"


def test_protocol_raw_sha_to_generation_record_wiring_rejects_semantic_island(tmp_path):
    """generation record を正規 bytes hash に保っても捕捉 raw bytes の差を拒否する。"""
    _need_v1()
    root, freeze, _ = _build_independent_launch_repo(
        tmp_path, mutate=lambda state: state.__setitem__("post_hash_protocol_suffix", b" "))
    with pytest.raises(M.RatifiedFreezeError) as ei:
        M.launch_validate(freeze, root)
    assert ei.value.reason == "floor-artifact-invalid"
    assert ei.value.cause == "protocol-record-sha"


def test_closure_raw_sha_to_generation_record_wiring_rejects_semantic_island(tmp_path):
    """generation record を元 closure hash に保っても捕捉 raw bytes の差を拒否する。"""
    _need_v1()
    root, freeze, _ = _build_independent_launch_repo(
        tmp_path, mutate=lambda state: state.__setitem__("post_hash_closure80_suffix", b"\n"))
    with pytest.raises(M.RatifiedFreezeError) as ei:
        M.launch_validate(freeze, root)
    assert ei.value.reason == "floor-artifact-invalid"
    assert ei.value.cause == "closure-record-sha"


@in_sealed_fixture_process
def test_journal_result_equality_rejects_rehashed_coherent_island(tmp_path):
    """result と generation SHA を再計算しても、独立 journal anchor が差分を拒否する。"""
    _need_v1()
    def mutate(state):
        state["result"]["sessions"][0]["notes"] = ["coherent-island"]
    root, freeze, _ = _build_launch_repo(tmp_path, mutate=mutate)
    _assert_registered_refusal(
        "coherent-journal-result", lambda: M.launch_validate(freeze, root))


def _first_axis_tokens() -> list[str]:
    # 3 軸値は既存 redaction 済み fixture bytes からのみ導出する。リテラルを再掲しない。
    return B._RR80_PARAMS.decode("utf-8").strip().split()


def _rehash_selector_prediction(document: dict) -> None:
    body = {key: value for key, value in document.items() if key != "body_sha256"}
    raw = json.dumps(
        body, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False,
    ).encode("utf-8")
    document["body_sha256"] = hashlib.sha256(raw).hexdigest()


@in_sealed_fixture_process
def test_selector_exact_exemption_accepts_declared_three_axis_evidence(tmp_path):
    _need_v1()
    root, freeze, topology = _build_launch_repo(
        tmp_path, selector_valid_cell=True,
    )
    raw_path = "output/s8b-freeze/selector-runs/raw_rr20_on.txt"
    envelope_path = "output/s8b-freeze/selector-runs/envelope_rr20_on.json"
    payload_path = "output/s8b-freeze/selector-runs/payload_rr20_on.json"
    hits = HF.holdout_conjunction_hits({
        raw_path: (root / raw_path).read_text(encoding="utf-8"),
        envelope_path: (root / envelope_path).read_text(encoding="utf-8"),
    })
    assert raw_path in hits["rr80"]
    assert envelope_path in hits["rr80"]

    exempt = M._selector_evidence_exempt_exact(head=topology["X"], root=root)
    assert raw_path in exempt
    assert envelope_path in exempt
    assert payload_path not in exempt
    assert isinstance(M.launch_validate(freeze, root), M.LaunchValidatedFreeze)


@in_sealed_fixture_process
def test_selector_parser_classification_boundary_at_ratified_launch(
        tmp_path, monkeypatch):
    _need_v1()
    prediction_rel = "output/s8b-freeze/selector_predictions.json"
    journal_rel = "output/s8b-freeze/selector-runs/journal.jsonl"
    raw_rel = "output/s8b-freeze/selector-runs/raw_rr20_on.txt"
    envelope_rel = "output/s8b-freeze/selector-runs/envelope_rr20_on.json"
    boundary_paths = [prediction_rel, journal_rel, raw_rel, envelope_rel]
    boundary = {}
    install_prediction = B._install_emitter_selector_prediction

    def install_parser_boundary(root, **kwargs):
        install_prediction(root, **kwargs)
        prediction_path = root / prediction_rel
        document = json.loads(prediction_path.read_bytes())
        row = next(
            row for row in document["rows"]
            if row["raw_response_path"] == raw_rel
        )
        rejected_rationale = f"{row['rationale']} <反映>"
        rejected_raw = json.dumps({
            "schema_version": "8b-selector-output/v1",
            "choice_id": row["choice_id"],
            "rationale": rejected_rationale,
        }, ensure_ascii=False, separators=(",", ":"))
        raw_sha256 = hashlib.sha256(rejected_raw.encode("utf-8")).hexdigest()
        (root / raw_rel).write_bytes(rejected_raw.encode("utf-8"))
        row["rationale"] = rejected_rationale
        row["raw_sha256"] = raw_sha256

        records = [
            json.loads(line)
            for line in (root / journal_rel).read_text(
                encoding="utf-8",
            ).splitlines()
        ]
        invocation = next(record for record in records if (
            record["record_type"] == "invocation"
            and record["target_holdout"] == row["target_holdout"]
            and record["arm"] == row["arm"]
        ))
        invocation["rationale"] = rejected_rationale
        invocation["raw_sha256"] = raw_sha256

        envelope = json.loads((root / envelope_rel).read_bytes())
        envelope["result"] = rejected_raw
        envelope_raw = B._json_bytes(envelope)
        (root / envelope_rel).write_bytes(envelope_raw)
        envelope_record = next(record for record in records if (
            record["record_type"] == "envelope"
            and record["target_holdout"] == row["target_holdout"]
            and record["arm"] == row["arm"]
        ))
        envelope_record["envelope_sha256"] = hashlib.sha256(
            envelope_raw
        ).hexdigest()

        _rehash_selector_prediction(document)
        prediction_path.write_bytes(B._json_bytes(document))
        (root / journal_rel).write_bytes(B._jsonl_bytes(records))
        boundary["raw"] = rejected_raw
        boundary["commit"] = B._commit_exact(
            root,
            boundary_paths,
            subject="parser classification boundary",
            agent="fixture",
        )

    monkeypatch.setattr(
        B, "_install_emitter_selector_prediction", install_parser_boundary,
    )

    def ratified_only_preflight(repo_root, **_kwargs):
        paths = set(B.FLOOR._PREFLIGHT_FIXED_FILES)
        paths.update(
            path.relative_to(repo_root).as_posix()
            for path in (repo_root / B.FLOOR._SELECTOR_RUNS_REL).iterdir()
            if path.is_file() and not path.is_symlink()
        )
        return {
            rel: hashlib.sha256((repo_root / rel).read_bytes()).hexdigest()
            for rel in paths
        }

    run_campaign_core = B.FLOOR._run_campaign_core

    def build_without_floor_selector_verify(*args, **kwargs):
        kwargs["_floor_preflight_fn"] = ratified_only_preflight
        return run_campaign_core(*args, **kwargs)

    monkeypatch.setattr(
        B.FLOOR, "_run_campaign_core", build_without_floor_selector_verify,
    )
    root, _freeze, topology = _build_launch_repo(
        tmp_path, selector_valid_cell=True,
    )
    document = json.loads((root / prediction_rel).read_bytes())
    with pytest.raises(SF.SelectorOutputError) as parser_error:
        SF.parse_selector_output(boundary["raw"])
    assert parser_error.value.code == "rationale_placeholder"
    committed_paths = tuple(filter(None, B._fixed_git(
        root,
        "diff-tree", "--no-commit-id", "--no-renames", "--name-only", "-r",
        boundary["commit"],
    ).splitlines()))
    assert committed_paths == tuple(sorted(boundary_paths))

    ratified = M.load_ratified_freeze(root)
    assert ratified.activation_head == topology["X"]
    # check=True の無例外完了をもって boundary commit が A の祖先であることを検査する。
    B._fixed_git(
        root, "merge-base", "--is-ancestor", boundary["commit"],
        ratified.activation_head,
    )
    assert isinstance(
        M.launch_validate(ratified, root),
        M.LaunchValidatedFreeze,
    )

    with pytest.raises(SF.SelectorFreezeError) as verification_error:
        SF.verify_prediction_freeze(
            document,
            freeze=json.loads(
                (root / document["sources"]["holdout_freeze"]["path"]).read_bytes()
            ),
            root=root,
        )
    assert str(verification_error.value).count(
        "invalid:rationale_placeholder"
    ) == 1

    wrong_code_document = json.loads(B._json_bytes(document))
    wrong_code_row = next(
        row for row in wrong_code_document["rows"]
        if row["raw_response_path"] == raw_rel
    )
    wrong_code_row.update({
        "status": "invalid",
        "choice_id": None,
        "binding_key": None,
        "binding_entry_sha256": None,
        "rationale": None,
        "parser_error_code": "invalid_json",
    })
    selector_freeze = json.loads(
        (root / wrong_code_document["sources"]["holdout_freeze"]["path"]).read_bytes()
    )
    wrong_code_document["swapped_follow_expectations"] = (
        SF._derive_swapped_expectations(
            selector_freeze, wrong_code_document["rows"],
        )
    )
    _rehash_selector_prediction(wrong_code_document)
    with pytest.raises(SF.SelectorFreezeError) as wrong_code_error:
        SF.verify_prediction_freeze(
            wrong_code_document, freeze=selector_freeze, root=root,
        )
    assert str(wrong_code_error.value).count(
        "invalid:rationale_placeholder"
    ) == 1
    assert str(wrong_code_error.value).count(
        "parser_error_code='invalid_json'"
    ) == 1

    honest_document = json.loads(B._json_bytes(document))
    honest_row = next(
        row for row in honest_document["rows"]
        if row["raw_response_path"] == raw_rel
    )
    honest_row.update({
        "status": "invalid",
        "choice_id": None,
        "binding_key": None,
        "binding_entry_sha256": None,
        "rationale": None,
        "parser_error_code": "rationale_placeholder",
    })
    honest_document["swapped_follow_expectations"] = SF._derive_swapped_expectations(
        selector_freeze, honest_document["rows"],
    )
    _rehash_selector_prediction(honest_document)
    assert SF.verify_prediction_freeze(
        honest_document, freeze=selector_freeze, root=root,
    ) is None

    # X 後の selector evidence 書換えは、意味検証より先に H-pure 履歴検査が拒否する。
    (root / raw_rel).write_bytes((boundary["raw"] + " ").encode("utf-8"))
    post_a_commit = B._commit_exact(
        root,
        [raw_rel],
        subject="mutate selector evidence after approval",
        agent="fixture",
    )
    assert B._fixed_git(root, "rev-parse", f"{post_a_commit}^") == topology["X"]
    with pytest.raises(M.RatifiedFreezeError) as post_a_error:
        M.load_ratified_freeze(root)
    assert post_a_error.value.reason == "history-mutated"


def test_selector_exact_exemption_absent_prediction_is_noop(tmp_path):
    root = tmp_path / "no-selector"
    root.mkdir()
    subprocess.run(["git", "init", "-q"], cwd=root, check=True)
    subprocess.run(
        ["git", "-c", "user.name=fixture", "-c", "user.email=fixture@example.invalid",
         "-c", "commit.gpgsign=false", "commit", "--allow-empty", "-q", "-m", "empty"],
        cwd=root, check=True,
    )
    head = subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=root, check=True, text=True,
        stdout=subprocess.PIPE,
    ).stdout.strip()
    assert M._selector_evidence_exempt_exact(head=head, root=root) == {}


@in_sealed_fixture_process
def test_selector_exact_exemption_rejects_undeclared_selector_run_hit(tmp_path):
    _need_v1()
    orphan = "output/s8b-freeze/selector-runs/envelope_orphan.json"
    root, freeze, _ = _build_launch_repo(
        tmp_path, selector_extra_files=[(orphan, B._RR80_PARAMS)],
    )
    exempt = M._selector_evidence_exempt_exact(head=freeze.activation_head, root=root)
    assert orphan not in exempt
    _assert_registered_refusal(
        "selector-undeclared-hit", lambda: M.launch_validate(freeze, root),
    )


@in_sealed_fixture_process
def test_selector_payload_is_not_exempt_and_conjunction_is_scanned(tmp_path):
    _need_v1()
    payload = "output/s8b-freeze/selector-runs/payload_rr20_on.json"
    root, freeze, _ = _build_launch_repo(
        tmp_path, selector_valid_cell=True, selector_payload_hit=True,
    )
    exempt = M._selector_evidence_exempt_exact(head=freeze.activation_head, root=root)
    assert payload not in exempt
    _assert_registered_refusal(
        "selector-payload-hit", lambda: M.launch_validate(freeze, root),
    )


@in_sealed_fixture_process
def test_selector_exact_exemption_rejects_declared_sha_mismatch(tmp_path):
    _need_v1()
    root, _freeze, topology = _build_launch_repo(tmp_path, selector_valid_cell=True)
    journal_path = root / "output/s8b-freeze/selector-runs/journal.jsonl"
    records = [json.loads(line) for line in journal_path.read_text().splitlines()]
    envelope = next(record for record in records if record["record_type"] == "envelope")
    envelope["envelope_sha256"] = "0" * 64
    journal_path.write_bytes(B._jsonl_bytes(records))
    head = B._fixed_commit_all(root, "bad envelope declaration", "fixture")
    with pytest.raises(M.RatifiedFreezeError) as caught:
        M._selector_evidence_exempt_exact(head=head, root=root)
    assert caught.value.reason == "scan-exemption-invalid"
    assert caught.value.cause == "selector-evidence-hash"


@in_sealed_fixture_process
def test_selector_exact_exemption_rejects_coherent_wrong_raw_sha(tmp_path):
    _need_v1()
    root, _freeze, _topology = _build_launch_repo(tmp_path, selector_valid_cell=True)
    predictions = root / "output/s8b-freeze/selector_predictions.json"
    document = json.loads(predictions.read_bytes())
    row = next(row for row in document["rows"] if row["arm"] != "off")
    row["raw_sha256"] = "0" * 64
    _rehash_selector_prediction(document)
    predictions.write_bytes(B._json_bytes(document))
    journal_path = root / "output/s8b-freeze/selector-runs/journal.jsonl"
    records = [json.loads(line) for line in journal_path.read_text().splitlines()]
    invocation = next(record for record in records if (
        record["record_type"] == "invocation"
        and record["target_holdout"] == row["target_holdout"]
        and record["arm"] == row["arm"]
    ))
    invocation["raw_sha256"] = row["raw_sha256"]
    journal_path.write_bytes(B._jsonl_bytes(records))
    head = B._fixed_commit_all(root, "coherent wrong raw sha", "fixture")
    with pytest.raises(M.RatifiedFreezeError) as caught:
        M._selector_evidence_exempt_exact(head=head, root=root)
    assert caught.value.reason == "scan-exemption-invalid"
    assert caught.value.cause == "selector-evidence-hash"


@in_sealed_fixture_process
def test_selector_exact_exemption_rejects_prediction_source_blob_hash_mismatch(
        tmp_path):
    _need_v1()
    root, _freeze, _topology = _build_launch_repo(tmp_path, selector_valid_cell=True)
    predictions = root / "output/s8b-freeze/selector_predictions.json"
    document = json.loads(predictions.read_bytes())
    document["sources"]["builder"]["sha256"] = "0" * 64
    _rehash_selector_prediction(document)
    predictions.write_bytes(B._json_bytes(document))
    head = B._fixed_commit_all(root, "bad selector source hash", "fixture")
    with pytest.raises(M.RatifiedFreezeError) as caught:
        M._selector_evidence_exempt_exact(head=head, root=root)
    assert caught.value.reason == "scan-exemption-invalid"
    assert caught.value.cause == "selector-evidence-hash"


@in_sealed_fixture_process
def test_selector_exact_exemption_rejects_self_declared_wrong_protocol_sha(tmp_path):
    _need_v1()
    root, _freeze, _topology = _build_launch_repo(tmp_path, selector_valid_cell=True)
    journal_path = root / "output/s8b-freeze/selector-runs/journal.jsonl"
    records = [json.loads(line) for line in journal_path.read_text().splitlines()]
    records[0]["protocol_sha256"] = "0" * 64
    journal_path.write_bytes(B._jsonl_bytes(records))
    head = B._fixed_commit_all(root, "self declared wrong protocol", "fixture")
    with pytest.raises(M.RatifiedFreezeError) as caught:
        M._selector_evidence_exempt_exact(head=head, root=root)
    assert caught.value.reason == "scan-exemption-invalid"
    assert caught.value.cause == "selector-declaration-invalid"


@in_sealed_fixture_process
def test_selector_launch_rejects_wrong_journal_schema_value(tmp_path):
    """M11: key 集合と他の束縛が正しい journal でも schema 値 drift は拒否する。"""
    _need_v1()
    root, _freeze, _topology = _build_launch_repo(
        tmp_path, selector_valid_cell=True,
    )
    journal_path = root / "output/s8b-freeze/selector-runs/journal.jsonl"
    records = [json.loads(line) for line in journal_path.read_text().splitlines()]
    records[0]["schema"] = "8b-prediction-journal/future"
    journal_path.write_bytes(B._jsonl_bytes(records))
    head = B._fixed_commit_all(root, "wrong selector journal schema", "fixture")

    with pytest.raises(M.RatifiedFreezeError) as caught:
        M._selector_evidence_exempt_exact(head=head, root=root)
    assert caught.value.reason == "scan-exemption-invalid"
    assert caught.value.cause == "selector-declaration-invalid"


@pytest.mark.parametrize(
    ("record_type", "field", "replacement"),
    [
        ("claim", "decision_method", "future-agent-method"),
        ("static_terminal", "decision_method", "future-static-method"),
        ("static_terminal", "choice_id", "future-static-choice"),
    ],
    ids=("claim-decision-method", "static-decision-method", "static-choice-id"),
)
@in_sealed_fixture_process
def test_selector_launch_rejects_journal_row_decision_drift(
        tmp_path, record_type, field, replacement):
    """M12: 非空で shape-valid な journal 値も封印 prediction row と違えば拒否する。"""
    _need_v1()
    root, _freeze, _topology = _build_launch_repo(
        tmp_path, selector_valid_cell=True,
    )
    journal_path = root / "output/s8b-freeze/selector-runs/journal.jsonl"
    records = [json.loads(line) for line in journal_path.read_text().splitlines()]
    record = next(row for row in records if row["record_type"] == record_type)
    record[field] = replacement
    journal_path.write_bytes(B._jsonl_bytes(records))
    head = B._fixed_commit_all(root, "selector journal row drift", "fixture")

    with pytest.raises(M.RatifiedFreezeError) as caught:
        M._selector_evidence_exempt_exact(head=head, root=root)
    assert caught.value.reason == "scan-exemption-invalid"
    assert caught.value.cause == "selector-declaration-invalid"


@in_sealed_fixture_process
def test_selector_launch_projection_ignores_current_choice_semantics(
        tmp_path, monkeypatch):
    _need_v1()
    root, freeze, _topology = _build_launch_repo(tmp_path, selector_valid_cell=True)
    baseline = M._selector_evidence_exempt_exact(
        head=freeze.activation_head, root=root,
    )
    monkeypatch.setattr(SF, "CHOICE_TO_BINDING", {"future": "future-binding"})
    monkeypatch.setattr(SF, "STATIC_DEFAULT_CHOICE_ID", "future-default")
    monkeypatch.setattr(
        SF, "selector_basis_sha256",
        lambda _freeze: (_ for _ in ()).throw(AssertionError("launch must not rederive basis")),
    )
    monkeypatch.setattr(
        SF, "_derive_swapped_expectations",
        lambda *_args: (_ for _ in ()).throw(AssertionError("launch must not rederive swap")),
    )
    assert M._selector_evidence_exempt_exact(
        head=freeze.activation_head, root=root,
    ) == baseline


@in_sealed_fixture_process
def test_selector_exact_exemption_rejects_nonancestor_pre_oracle_head(tmp_path):
    _need_v1()
    root, _freeze, _topology = _build_launch_repo(tmp_path, selector_valid_cell=True)
    predictions = root / "output/s8b-freeze/selector_predictions.json"
    document = json.loads(predictions.read_bytes())
    source_tree = B._git(
        root, "rev-parse", f"{document['pre_oracle_head']}^{{tree}}",
    )
    unrelated = B._git(root, "commit-tree", source_tree, stdin=b"unrelated\n")
    document["pre_oracle_head"] = unrelated
    _rehash_selector_prediction(document)
    predictions.write_bytes(B._json_bytes(document))
    journal_path = root / "output/s8b-freeze/selector-runs/journal.jsonl"
    records = [json.loads(line) for line in journal_path.read_text().splitlines()]
    records[0]["pre_oracle_head"] = unrelated
    journal_path.write_bytes(B._jsonl_bytes(records))
    head = B._fixed_commit_all(root, "non ancestor prediction", "fixture")
    with pytest.raises(M.RatifiedFreezeError) as caught:
        M._selector_evidence_exempt_exact(head=head, root=root)
    assert caught.value.reason == "scan-exemption-invalid"
    assert caught.value.cause == "selector-declaration-invalid"


@in_sealed_fixture_process
def test_selector_exact_exemption_rejects_journal_rows_mismatch(tmp_path):
    _need_v1()
    root, _freeze, _topology = _build_launch_repo(tmp_path, selector_valid_cell=True)
    journal_path = root / "output/s8b-freeze/selector-runs/journal.jsonl"
    records = [json.loads(line) for line in journal_path.read_text().splitlines()]
    invocation = next(record for record in records if record["record_type"] == "invocation")
    invocation["rationale"] = "journal-only mismatch"
    journal_path.write_bytes(B._jsonl_bytes(records))
    head = B._fixed_commit_all(root, "journal row mismatch", "fixture")
    with pytest.raises(M.RatifiedFreezeError) as caught:
        M._selector_evidence_exempt_exact(head=head, root=root)
    assert caught.value.reason == "scan-exemption-invalid"
    assert caught.value.cause == "selector-declaration-invalid"


@in_sealed_fixture_process
def test_selector_exact_exemption_rejects_duplicate_key_document(tmp_path):
    _need_v1()
    root, _freeze, _topology = _build_launch_repo(tmp_path, selector_valid_cell=True)
    predictions = root / "output/s8b-freeze/selector_predictions.json"
    raw = predictions.read_text(encoding="utf-8")
    predictions.write_text(raw.replace(
        '"schema_version":',
        '"schema_version":"duplicate","schema_version":',
        1,
    ), encoding="utf-8")
    head = B._fixed_commit_all(root, "duplicate prediction key", "fixture")
    with pytest.raises(M.RatifiedFreezeError) as caught:
        M._selector_evidence_exempt_exact(head=head, root=root)
    assert caught.value.reason == "scan-exemption-invalid"
    assert caught.value.cause == "selector-declaration-invalid"


@in_sealed_fixture_process
def test_selector_exact_exemption_rejects_h_worktree_bytes_mismatch(tmp_path):
    _need_v1()
    root, freeze, _topology = _build_launch_repo(tmp_path, selector_valid_cell=True)
    raw_path = root / "output/s8b-freeze/selector-runs/raw_rr20_on.txt"
    raw_path.write_bytes(raw_path.read_bytes() + b"\nworktree drift\n")
    with pytest.raises(M.RatifiedFreezeError) as caught:
        M._selector_evidence_exempt_exact(head=freeze.activation_head, root=root)
    assert caught.value.reason == "scan-exemption-invalid"
    assert caught.value.cause == "selector-evidence-bytes"


@in_sealed_fixture_process
def test_selector_exact_exemption_rejects_worktree_symlink(tmp_path):
    _need_v1()
    root, freeze, _topology = _build_launch_repo(tmp_path, selector_valid_cell=True)
    raw_path = root / "output/s8b-freeze/selector-runs/raw_rr20_on.txt"
    raw_path.unlink()
    raw_path.symlink_to(root / "README.md")
    with pytest.raises(M.RatifiedFreezeError) as caught:
        M._selector_evidence_exempt_exact(head=freeze.activation_head, root=root)
    assert caught.value.reason == "scan-exemption-invalid"
    assert caught.value.cause == "selector-evidence-bytes"


@in_sealed_fixture_process
def test_selector_exact_exemption_rejects_executable_h_mode(tmp_path):
    _need_v1()
    root, _freeze, _topology = _build_launch_repo(tmp_path, selector_valid_cell=True)
    raw_path = root / "output/s8b-freeze/selector-runs/raw_rr20_on.txt"
    raw_path.chmod(0o755)
    head = B._fixed_commit_all(root, "executable selector raw", "fixture")
    with pytest.raises(M.RatifiedFreezeError) as caught:
        M._selector_evidence_exempt_exact(head=head, root=root)
    assert caught.value.reason == "scan-exemption-invalid"
    assert caught.value.cause == "selector-evidence-mode"


@in_sealed_fixture_process
def test_single_axis_occurrence_in_free_field_rejected(tmp_path):
    _need_v1()
    token = _first_axis_tokens()[0]
    def mutate(state):
        journal_session = next(r for r in state["journal"] if r["event"] == "session")
        result_session = next(r for r in state["result"]["sessions"]
                              if r["seq"] == journal_session["seq"])
        journal_session["notes"] = [token]
        result_session["notes"] = [token]
    root, freeze, _ = _build_launch_repo(tmp_path, mutate=mutate)
    with pytest.raises(M.RatifiedFreezeError) as ei:
        M.launch_validate(freeze, root)
    assert ei.value.reason == "floor-artifact-invalid"
    assert ei.value.cause == "axis-occurrence"


@in_sealed_fixture_process
def test_three_axes_distributed_across_free_fields_rejected(tmp_path):
    _need_v1()
    tokens = _first_axis_tokens()
    assert len(tokens) == 3
    def mutate(state):
        journal_session = next(r for r in state["journal"] if r["event"] == "session")
        result_session = next(r for r in state["result"]["sessions"]
                              if r["seq"] == journal_session["seq"])
        journal_session["notes"] = [tokens[0]]
        journal_session["probe_before"]["stdout"] = tokens[1]
        journal_session["probe_after"]["stderr"] = tokens[2]
        result_session.update(json.loads(json.dumps(journal_session)))
    root, freeze, _ = _build_launch_repo(tmp_path, mutate=mutate)
    with pytest.raises(M.RatifiedFreezeError) as ei:
        M.launch_validate(freeze, root)
    assert ei.value.reason == "floor-artifact-invalid"
    assert ei.value.cause == "axis-occurrence"


@in_sealed_fixture_process
def test_untracked_symlink_fails_closed_before_scan(tmp_path):
    _need_v1()
    root, freeze, _ = _build_launch_repo(tmp_path)
    (root / "untracked-link").symlink_to(root / "README.md")
    with pytest.raises(M.RatifiedFreezeError) as ei:
        M.launch_validate(freeze, root)
    assert ei.value.reason == "scan-exemption-invalid"
    assert ei.value.cause == "untracked-symlink"


@pytest.mark.parametrize("bad_path", [
    "output//x", "output/./x", "output/../x", "output\\x", "output/x\x00y",
])
def test_closure_path_raw_posix_grammar_rejected_unit(bad_path):
    doc = {
        "floor_protocol": {"path": "output/protocol.json", "sha256": "0" * 64},
        "floor_source": {"path": "output/result.json", "sha256": "1" * 64},
        "measurement_closure": [{"canonical_path": bad_path, "sha256": "2" * 64}],
    }
    with pytest.raises(M.RatifiedFreezeError) as ei:
        M._closure_entries(doc)
    assert ei.value.reason == "closure-path"


@pytest.mark.parametrize("raw", [b"text\x00hidden", b"\xff\xfe"])
def test_closure_is_utf8_without_nul(raw):
    with pytest.raises(M.RatifiedFreezeError) as ei:
        M._closure_text(raw)
    assert ei.value.reason == "closure-nontext"


def test_raw_scanner_and_occurrence_validator_equivalent_for_encodings():
    workload = dict(HF.HOLDOUTS["rr80"]["ycsb"])
    structured_path = "output/fixture/manifest.json"
    closure_path = "output/fixture/declared.txt"
    structured = {"cells": [{"workload": workload}]}
    hits = M._validate_axis_occurrences(
        artifacts=[
            (structured_path, structured, _ljline(structured)),
            (closure_path, None, B._RR80_PARAMS),
        ],
        protocol={"env_tag": "linux-baremetal"},
        binaries={},
        contract=EC.lookup("linux-baremetal"),
        closure_paths=frozenset({closure_path}),
    )
    raw_hits = HF.holdout_conjunction_hits({
        structured_path: _ljline(structured).decode(),
        closure_path: B._RR80_PARAMS.decode(),
    })
    assert hits == raw_hits
    assert structured_path in hits["rr80"]
    assert closure_path in hits["rr80"]


def test_axis_scanner_allows_only_enumerated_sort_receipt_leaf():
    token = _first_axis_tokens()[0]
    path = "output/fixture/result.json"
    record = {
        "binaries": {
            "rr80::sort_best": {
                "sort_swo_oracle": {"corpus_version": token},
            },
        },
    }
    M._validate_axis_occurrences(
        artifacts=[(path, record, _ljline(record))],
        protocol={"env_tag": "linux-baremetal"}, binaries={},
        contract=EC.lookup("linux-baremetal"),
    )


def test_axis_scanner_does_not_allow_sort_receipt_subtree():
    token = _first_axis_tokens()[0]
    path = "output/fixture/result.json"
    record = {
        "binaries": {
            "rr80::sort_best": {
                "sort_swo_oracle": {"free_text": token},
            },
        },
    }
    with pytest.raises(M.RatifiedFreezeError) as caught:
        M._validate_axis_occurrences(
            artifacts=[(path, record, _ljline(record))],
            protocol={"env_tag": "linux-baremetal"}, binaries={},
            contract=EC.lookup("linux-baremetal"),
        )
    assert caught.value.cause == "axis-occurrence"


@in_sealed_fixture_process
def test_closure_role_collision_with_result_rejected(tmp_path):
    _need_v1()
    root, freeze, topology = _build_launch_repo(tmp_path)
    doc = M._plain_json(freeze.document)
    doc["measurement_closure"][0] = {
        "canonical_path": topology["paths"]["result"],
        "sha256": freeze.document["floor_source"]["sha256"],
    }
    collided = M.RatifiedFreeze(
        document=M._deep_freeze(doc), sha256=freeze.sha256,
        generation_number=1, activation_head=freeze.activation_head,
        generation_commit=freeze.generation_commit,
    )
    with pytest.raises(M.RatifiedFreezeError) as ei:
        M.launch_validate(collided, root)
    assert ei.value.reason == "closure-role-conflict"


def test_cert_raw_hit_checked_before_cert_schema(tmp_path):
    _need_v1()
    def cert_mutate(cert):
        cert["schema"] = B._RR80_PARAMS.decode("utf-8")
    root, freeze, _ = _build_independent_launch_repo(
        tmp_path, cert_mutate=cert_mutate)
    with pytest.raises(M.RatifiedFreezeError) as ei:
        M.launch_validate(freeze, root)
    assert ei.value.reason == "floor-artifact-invalid"
    assert ei.value.cause == "certificate-holdout-hit"


def test_certificate_same_commit_as_generation_rejected(tmp_path):
    _need_v1()
    root, freeze, _ = _build_independent_launch_repo(
        tmp_path, cert_at_generation=True)
    with pytest.raises(M.RatifiedFreezeError) as ei:
        M.launch_validate(freeze, root)
    assert ei.value.reason == "binding-chain-mismatch"
    assert ei.value.cause == "cert-lineage"


@in_sealed_fixture_process
def test_floor_source_introduction_must_be_exact_generation_commit(tmp_path):
    _need_v1()
    root, freeze, topology = _build_launch_repo(tmp_path)
    wrong_g = M.RatifiedFreeze(
        document=freeze.document, sha256=freeze.sha256, generation_number=1,
        activation_head=freeze.activation_head, generation_commit=topology["A"],
    )
    with pytest.raises(M.RatifiedFreezeError) as ei:
        M.launch_validate(wrong_g, root)
    assert ei.value.reason == "binding-chain-mismatch"
    assert ei.value.cause == "generation-introduction"


@in_sealed_fixture_process
def test_validation_head_artifact_change_rejected_even_if_worktree_matches_h(tmp_path):
    _need_v1()
    root, freeze, topology = _build_launch_repo(tmp_path)
    journal_path = root / topology["paths"]["journal"]
    journal_path.write_bytes(journal_path.read_bytes() + b"\n")
    new_h = _lcommit(root, "tamper journal at H", "fixture")
    moved = M.RatifiedFreeze(
        document=freeze.document, sha256=freeze.sha256, generation_number=1,
        activation_head=new_h, generation_commit=freeze.generation_commit,
    )
    with pytest.raises(M.RatifiedFreezeError) as ei:
        M.launch_validate(moved, root)
    assert ei.value.reason == "floor-artifact-invalid"
    assert ei.value.cause == "g-h-worktree-mismatch"


@in_sealed_fixture_process
def test_worktree_executable_mode_drift_rejected(tmp_path):
    _need_v1()
    root, freeze, topology = _build_launch_repo(tmp_path)
    result_path = root / topology["paths"]["result"]
    result_path.chmod(result_path.stat().st_mode | 0o111)
    with pytest.raises(M.RatifiedFreezeError) as ei:
        M.launch_validate(freeze, root)
    assert ei.value.reason == "floor-artifact-invalid"
    assert ei.value.cause == "g-h-worktree-mismatch"


@in_sealed_fixture_process
def test_manifest_mode_100755_accepted_when_g_h_worktree_match(tmp_path):
    _need_v1()
    root, freeze, topology = _build_launch_repo(tmp_path, executable_role="manifest")
    validated = M.launch_validate(freeze, root)
    assert isinstance(validated, M.LaunchValidatedFreeze)
    assert topology["mode_map"][topology["paths"]["manifest"]] == "100755"
    assert validated.ratified is freeze


@in_sealed_fixture_process
def test_worktree_parent_symlink_rejected_component_walk(tmp_path):
    _need_v1()
    root, freeze, topology = _build_launch_repo(tmp_path)
    run_dir = (root / topology["paths"]["result"]).parent
    external = tmp_path / "external-run-dir"
    run_dir.rename(external)
    run_dir.symlink_to(external, target_is_directory=True)
    with pytest.raises(M.RatifiedFreezeError) as ei:
        M.launch_validate(freeze, root)
    assert ei.value.reason == "floor-artifact-invalid"
    assert ei.value.cause == "worktree-symlink"


@in_sealed_fixture_process
def test_namespace_exemption_requires_exact_h_worktree_bytes(tmp_path):
    _need_v1()
    root, freeze, _ = _build_launch_repo(tmp_path)
    approval = next((root / M.APPROVAL_DIR).glob("*.json"))
    approval.write_bytes(approval.read_bytes() + b"\n")
    with pytest.raises(M.RatifiedFreezeError) as ei:
        M.launch_validate(freeze, root)
    assert ei.value.reason == "scan-exemption-invalid"
    assert ei.value.cause == "namespace-dirty"


@pytest.mark.parametrize("raw", [
    b'{"event":"terminal","event":"terminal","status":"completed"}\n',
    b'{"event":"terminal","status":NaN}\n',
    b'{"event":"terminal","status":"completed"}',
    b'\n',
])
def test_strict_jsonl_rejects_duplicate_nan_truncated_and_blank(raw):
    with pytest.raises(M.RatifiedFreezeError):
        M._strict_jsonl(raw)


@in_sealed_fixture_process
def test_binary_receipt_is_derived_from_journal_not_result(tmp_path):
    _need_v1()
    def mutate(state):
        session = next(r for r in state["journal"] if r["event"] == "session")
        session["binary_sha256_at_measure"] = "f" * 64
        result_session = next(r for r in state["result"]["sessions"] if r["seq"] == session["seq"])
        result_session["binary_sha256_at_measure"] = "f" * 64
    root, freeze, _ = _build_launch_repo(tmp_path, mutate=mutate)
    with pytest.raises(M.RatifiedFreezeError) as ei:
        M.launch_validate(freeze, root)
    assert ei.value.reason == "binding-chain-mismatch"
    assert ei.value.cause == "binary-receipt"


@in_sealed_fixture_process
def test_result_excluded_projection_rederived_from_journal(tmp_path):
    _need_v1()
    def mutate(state):
        state["result"]["excluded"].append({
            "seq": 0, "cell_id": state["result"]["sessions"][0]["cell_id"],
            "kind": "planned", "retry": False, "round": 1,
            "excluded_reason": "performance_anomaly", "session_cv": 1.0,
            "exclusion_class": "performance_anomaly",
            "rep_integrity_failures": 0,
        })
    root, freeze, _ = _build_launch_repo(tmp_path, mutate=mutate)
    with pytest.raises(M.RatifiedFreezeError) as ei:
        M.launch_validate(freeze, root)
    assert ei.value.reason == "binding-chain-mismatch"
    assert ei.value.cause == "result-excluded"


@in_sealed_fixture_process
def test_ratified_journal_required_consumer_passes_contract_mode_and_verified(tmp_path):
    """required receipt dispatch は validate_receipt_v2 単独でなく契約再検算 API を通る。"""
    _need_v1()
    root, ratified, topology = _build_launch_repo(tmp_path)
    paths = topology["paths"]
    protocol = json.loads((root / paths["protocol"]).read_bytes())
    manifest_raw = (root / paths["manifest"]).read_bytes()
    manifest = json.loads(manifest_raw)
    cert_raw = (root / paths["cert"]).read_bytes()
    records = M._strict_jsonl((root / paths["journal"]).read_bytes())
    protocol_sha = FC.canonical_protocol_sha256(protocol)
    cells, schedule, binaries = M._validate_manifest(
        manifest, protocol=protocol, protocol_sha256=protocol_sha, ratified=ratified,
        expected_policy=resolve_current_build_admission_policy(),
    )
    base = EC.lookup(protocol["env_tag"])
    required = dataclasses.replace(
        base, attestation_mode="required",
        isolation_policy=EC.IsolationPolicy(single_process=True, allow_resume=False),
    )
    verified = object()
    receipt_spy = mock.Mock(return_value=False)

    with mock.patch.object(M._env_attestation, "load_verified_calibration",
                              return_value=verified), \
            mock.patch.object(M._execution_guard, "receipt_matches_contract", receipt_spy):
        with pytest.raises(M.RatifiedFreezeError) as excinfo:
            M._validate_journal(
                records, protocol=protocol, schedule=schedule, cells=cells,
                binaries=binaries, cert_sha256=hashlib.sha256(cert_raw).hexdigest(),
                manifest_sha256=hashlib.sha256(manifest_raw).hexdigest(), root=root,
                contract=required,
            )

    assert excinfo.value.cause == "receipt-contract"
    assert receipt_spy.call_args.kwargs["attestation_mode"] == "required"
    assert receipt_spy.call_args.kwargs["verified_calibration"] is verified


def _build_merge_introduced_g1(tmp_path: Path) -> Path:
    """g1 世代 file を merge commit で導入する repo を組む (両親に g1 不在)。

    structural 層 (_assert_candidate_commit) が merge の世代導入を拒否することの確認用。
    build_valid_semantic_g1 の base までを組んだ後、側枝を切り、merge commit で g1 を追加する。"""
    root, _gen_sha, _gen_rel, g1 = B.build_valid_semantic_g1(tmp_path)
    # 既存 g1 (非 merge 導入) を取り除いた歴史を新規に組み直すのは重いので、別 repo を base から
    # 作り直す: build_valid_semantic_g1 は approval まで済ませているため、ここでは g1 の
    # merge 導入を別途検証する専用 repo を最小構成で組む。
    root2 = tmp_path / "merge_repo"
    root2.mkdir()
    B._init_repo(root2)
    if B._REAL_V1.is_file():
        B._write(root2, M.V1_FREEZE_PATH, B._REAL_V1.read_bytes())
    (root2 / "README.md").write_text("m\n", encoding="utf-8")
    base = B._commit(root2, "base", "claude-base")
    B._git(root2, "checkout", "-q", "-b", "b1")
    (root2 / "a.txt").write_text("a\n", encoding="utf-8")
    B._commit(root2, "b1", "claude")
    B._git(root2, "checkout", "-q", base)
    B._git(root2, "checkout", "-q", "-b", "b2")
    (root2 / "b.txt").write_text("b\n", encoding="utf-8")
    B._commit(root2, "b2", "claude")
    B._git(root2, "checkout", "-q", "b1")
    B._git(root2, "merge", "-q", "--no-commit", "--no-ff", "b2")
    # merge commit の中で g1 を追加する (両親に g1 不在 → 導入 commit = merge)。
    g1_raw = json.dumps(g1, ensure_ascii=False).encode("utf-8")
    B._write(root2, B._gen_rel(1), g1_raw)
    B._commit(root2, "merge introduces g1", "claude-opus")
    g1_sha = B._sha(g1_raw)
    B._approve_and_point(root2, 1, g1_sha, B._gen_rel(1), None)
    return root2
