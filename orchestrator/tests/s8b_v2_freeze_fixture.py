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
from typing import Optional

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

    cells = contract.enumerate_cells(
        v1, stock_configuration=protocol["stock_configuration"],
    )
    sessions = []
    by_cell = {}
    seq = 0
    for cell in cells:
        records = []
        for _round in range(protocol["n_sessions"]):
            observations = [
                {
                    "rep_index": index, "returncode": 0,
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
                "cell_id": cell["cell_id"],
                "holdout_id": cell["holdout_id"],
                "configuration_id": cell["configuration_id"],
                "seq": seq,
                "throughputs": [1000.0] * protocol["reps"],
                "reps_expected": protocol["reps"],
                "exec_failures": 0,
                "excluded_reason": None,
                "retry": False,
                "rep_observations": observations,
                "rep_integrity_failures": 0,
                "exclusion_class": None,
            }
            sessions.append(row)
            records.append(stats.SessionRecord(
                cell_id=row["cell_id"], holdout_id=row["holdout_id"],
                configuration_id=row["configuration_id"], seq=row["seq"],
                throughputs=tuple(row["throughputs"]),
                reps_expected=row["reps_expected"], exec_failures=0,
                excluded_reason=None, retry=False,
                rep_observations=tuple(observations), rep_integrity_failures=0,
            ))
            seq += 1
        by_cell[cell["cell_id"]] = stats.cell_stats(
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
        receipt = binary_admission.issue_binary_admission_receipt(
            admission=admission, expected_policy=context.policy, source=source,
            cell_id=cell["cell_id"], holdout_id=cell["holdout_id"],
            configuration_id=cell["configuration_id"], binding=binding,
            binary=binary_path, binary_sha256=sha256,
            contract_sha256=protocol["contract_sha256"], trace=False,
        )
        binaries[cell["cell_id"]] = {
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
    protocol_sha256 = contract.canonical_protocol_sha256(protocol)
    configurations = sorted({cell["configuration_id"] for cell in cells})
    return {
        "schema": contract.RESULT_SCHEMA,
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


def candidate_repository(tmp_path: Path, module) -> dict:
    """v2 producer 正例用の synthetic-only tmp git repository を作る。"""
    from orchestrator.campaign import env_contract
    from orchestrator.campaign import s8b_floor_contract as contract

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
    _write(root, result_rel, canonical_bytes(
        _synthetic_floor_result(v1, protocol, root=root)
    ))
    _write(root, f"{run_dir}/manifest.json", b"{}")
    _write(root, f"{run_dir}/journal.jsonl", b"{}\n")
    _write(root, f"{run_dir}/launch_certificate.json", b"{}")

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
    return {
        "root": root,
        "head": _git(root, "rev-parse", "HEAD"),
        "result_rel": result_rel,
        "budget_rel": budget_rel,
        "budget": budget_document,
        "approval_sha256": hashlib.sha256(approval_raw).hexdigest(),
        "closure_paths": closure_paths,
    }
