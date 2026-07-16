# -*- coding: utf-8 -*-
"""8b oracle schedule/manifest の決定性と改竄拒否を検査する。"""
from __future__ import annotations

import copy
import hashlib
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

import pytest


_HERE = Path(__file__).resolve().parent
_ORCHESTRATOR = _HERE.parent
_ROOT = _ORCHESTRATOR.parent
sys.path.insert(0, str(_ORCHESTRATOR))

from campaign import s8b_oracle_manifest as manifest  # noqa: E402


FREEZE_PATH = _ROOT / "output/s8b-freeze/holdout_freeze.json"
CONFIGURATION_IDS = (
    "p2_2_flag_opt", "backoff_fixed_best", "sort_best",
    "system_gate", "ident_all", "stock_common",
)
ROW_KEYS = {
    "block_id", "replicate_index", "schedule_index",
    "holdout_id", "configuration_id",
}


# 注意: holdout の workload 三軸はテストへ静止させない。
# ID だけを freeze から実行時に読み、schedule/manifest に workload 値を複製しない。
def _holdout_ids():
    freeze = json.loads(FREEZE_PATH.read_text(encoding="utf-8"))
    return tuple(freeze["holdouts"])


def _schedule(*, seed="seed-a", n=3, block_sizes=None):
    return manifest.build_schedule(
        n=n,
        master_seed=seed,
        block_sizes=block_sizes or {"early": 1, "late": 2},
        holdout_ids=_holdout_ids(),
        configuration_ids=CONFIGURATION_IDS,
    )


def _canonical_sha256(value) -> str:
    encoded = json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _source(path):
    source = _ROOT / path
    return {"path": path, "sha256": hashlib.sha256(source.read_bytes()).hexdigest()}


def _binding(holdout_id: str, configuration_id: str) -> dict:
    projected = {
        "genome_canonical": f"genome-{configuration_id}",
        "src_token": f"source-{holdout_id}-{configuration_id}",
        "variant_id": f"variant-{configuration_id}",
        "entry_sha256": _canonical_sha256({
            "holdout_id": holdout_id, "configuration_id": configuration_id,
        }),
    }
    return {
        "holdout_id": holdout_id,
        "configuration_id": configuration_id,
        **projected,
        "binding_sha256": _canonical_sha256(projected),
    }


def _build_manifest(freeze_path, *, schedule=None):
    schedule = schedule or _schedule()
    bindings = [
        _binding(holdout_id, configuration_id)
        for holdout_id in _holdout_ids()
        for configuration_id in CONFIGURATION_IDS
    ]
    return manifest.build_manifest(
        freeze_path=freeze_path,
        schedule=schedule,
        run_contract={
            "ccbench_pin": "pin", "env_tag": "test-env", "clocks": 1800,
            "reps": 5, "extime": 3, "verify": "legacy+s2",
            "screening": "off", "bench_max_rounds": 1,
        },
        binding_identity=bindings,
        campaign_ids={block["block_id"]: f"campaign-{block['block_id']}"
                      for block in schedule["blocks"]},
        allowed_excluded_reasons=["machine-failure"],
        generator_versions={
            "materializer": _source("orchestrator/campaign/s1_direct_comparison.py"),
            "report": _source("orchestrator/campaign/s8b_oracle_report.py"),
            "judge": _source("orchestrator/campaign/s8b_oracle_judge.py"),
        },
    )


def _freeze_copy(tmp_path):
    path = tmp_path / "holdout_freeze.json"
    document = json.loads(FREEZE_PATH.read_text(encoding="utf-8"))
    holdout_ids = tuple(document["holdouts"])
    document["floor"] = {
        "by_holdout": {holdout_id: 0.01 for holdout_id in holdout_ids},
    }
    document["budget"] = {
        "total_bench_s": 100.0,
        "per_holdout_bench_s": {
            holdout_id: 50.0 for holdout_id in holdout_ids
        },
        "oracle_shared": True,
    }
    path.write_text(json.dumps(document, ensure_ascii=False), encoding="utf-8")
    return path


def test_current_freeze_is_rejected_as_non_executable_manifest():
    with pytest.raises(manifest.ManifestError, match=r"freeze\.(floor|budget) が null"):
        _build_manifest(FREEZE_PATH)


def test_each_replicate_is_complete_product_and_each_cell_occurs_n_times():
    n = 3
    schedule = _schedule(n=n)
    expected_cells = {
        (holdout_id, configuration_id)
        for holdout_id in _holdout_ids()
        for configuration_id in CONFIGURATION_IDS
    }
    by_replicate = defaultdict(list)
    all_cells = Counter()
    for row in schedule["rows"]:
        assert set(row) == ROW_KEYS
        cell = (row["holdout_id"], row["configuration_id"])
        by_replicate[row["replicate_index"]].append(cell)
        all_cells[cell] += 1

    assert len(expected_cells) == len(_holdout_ids()) * len(CONFIGURATION_IDS)
    assert set(by_replicate) == set(range(n))
    assert all(Counter(cells) == Counter(expected_cells)
               for cells in by_replicate.values())
    assert all_cells == Counter({cell: n for cell in expected_cells})
    assert sum(block["size"] for block in schedule["blocks"]) == n


def test_same_seed_is_byte_identical_and_different_seed_changes_hash():
    first = _schedule(seed="stable")
    second = _schedule(seed="stable")
    different = _schedule(seed="different")
    encode = lambda value: json.dumps(  # noqa: E731
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":"),
    ).encode("utf-8")
    assert encode(first) == encode(second)
    assert manifest.schedule_sha256(first) == manifest.schedule_sha256(second)
    assert manifest.schedule_sha256(first) != manifest.schedule_sha256(different)


def test_schedule_rows_and_manifest_holdout_references_do_not_copy_workload(tmp_path):
    freeze_path = _freeze_copy(tmp_path)
    document = _build_manifest(freeze_path)
    for row in document["schedule"]["rows"]:
        assert set(row) == ROW_KEYS
    assert document["holdout_references"] == [
        {"holdout_id": holdout_id, "freeze_pointer": f"/holdouts/{holdout_id}"}
        for holdout_id in sorted(_holdout_ids())
    ]


def test_write_is_create_only_and_valid_manifest_verifies(tmp_path):
    freeze_path = _freeze_copy(tmp_path)
    document = _build_manifest(freeze_path)
    path = tmp_path / "oracle_manifest.json"
    manifest.write_manifest(path, document)
    assert manifest.verify_manifest(path, root=_ROOT) == document
    with pytest.raises(manifest.ManifestError, match="既に存在"):
        manifest.write_manifest(path, document)


@pytest.mark.parametrize("damage", ["missing-key", "duplicate-cell", "wrong-cell"])
def test_binding_identity_requires_complete_unique_schedule_cell_product(tmp_path, damage):
    freeze_path = _freeze_copy(tmp_path)
    schedule = _schedule()
    bindings = [
        _binding(holdout_id, configuration_id)
        for holdout_id in _holdout_ids()
        for configuration_id in CONFIGURATION_IDS
    ]
    if damage == "missing-key":
        bindings[0].pop("src_token")
    elif damage == "duplicate-cell":
        bindings[0] = copy.deepcopy(bindings[1])
    else:
        bindings[0]["holdout_id"] = "not-in-schedule"
    with pytest.raises(manifest.ManifestError, match="binding_identity|binding identity"):
        manifest.build_manifest(
            freeze_path=freeze_path,
            schedule=schedule,
            run_contract={
                "ccbench_pin": "pin", "env_tag": "test-env", "clocks": 1800,
                "reps": 5, "extime": 3, "verify": "legacy+s2",
                "screening": "off", "bench_max_rounds": 1,
            },
            binding_identity=bindings,
            campaign_ids={block["block_id"]: f"campaign-{block['block_id']}"
                          for block in schedule["blocks"]},
            allowed_excluded_reasons=["machine-failure"],
            generator_versions={
                "materializer": _source(
                    "orchestrator/campaign/s1_direct_comparison.py"),
                "report": _source("orchestrator/campaign/s8b_oracle_report.py"),
                "judge": _source("orchestrator/campaign/s8b_oracle_judge.py"),
            },
        )


def test_campaign_config_preimage_hash_is_bound_and_tampering_is_rejected(tmp_path):
    freeze_path = _freeze_copy(tmp_path)
    document = _build_manifest(freeze_path)
    for record in document["campaign_config_preimages"].values():
        assert hashlib.sha256(record["canonical_json"].encode("utf-8")).hexdigest() == (
            record["sha256"]
        )
    block_id = next(iter(document["campaign_config_preimages"]))
    document["campaign_config_preimages"][block_id]["sha256"] = "f" * 64
    path = tmp_path / "preimage-tampered.json"
    path.write_text(json.dumps(document), encoding="utf-8")
    with pytest.raises(manifest.ManifestError, match="campaign config preimage"):
        manifest.verify_manifest(path, root=_ROOT)


def test_generator_hash_must_match_real_root_file_at_build_and_verify(tmp_path):
    freeze_path = _freeze_copy(tmp_path)
    document = _build_manifest(freeze_path)
    false_generators = copy.deepcopy(document["generator_versions"])
    false_generators["report"]["sha256"] = "0" * 64
    with pytest.raises(manifest.ManifestError, match="実 byte hash"):
        manifest.build_manifest(
            freeze_path=freeze_path,
            schedule=document["schedule"],
            run_contract=document["run_contract"],
            binding_identity=document["binding_identity"],
            campaign_ids=document["campaign_ids"],
            allowed_excluded_reasons=document["allowed_excluded_reasons"],
            generator_versions=false_generators,
        )

    document["generator_versions"] = false_generators
    path = tmp_path / "generator-tampered.json"
    path.write_text(json.dumps(document), encoding="utf-8")
    with pytest.raises(manifest.ManifestError, match="実 byte hash"):
        manifest.verify_manifest(path, root=_ROOT)


def test_verify_detects_freeze_byte_tampering(tmp_path):
    freeze_path = _freeze_copy(tmp_path)
    document = _build_manifest(freeze_path)
    path = tmp_path / "oracle_manifest.json"
    manifest.write_manifest(path, document)
    freeze_path.write_bytes(freeze_path.read_bytes() + b"\n")
    with pytest.raises(manifest.ManifestError, match="freeze byte sha256"):
        manifest.verify_manifest(path, root=_ROOT)


@pytest.mark.parametrize(
    ("tamper", "message"),
    [("schedule-hash", "schedule_sha256"),
     ("campaign-duplicate", "campaign ID"),
     ("binding-schema", "binding_identity entry schema")],
)
def test_verify_detects_manifest_tampering(tmp_path, tamper, message):
    freeze_path = _freeze_copy(tmp_path)
    document = _build_manifest(freeze_path)
    if tamper == "schedule-hash":
        document["schedule_sha256"] = "f" * 64
    elif tamper == "campaign-duplicate":
        campaign_id = next(iter(document["campaign_ids"].values()))
        document["campaign_ids"] = {
            block_id: campaign_id for block_id in document["campaign_ids"]
        }
    else:
        document["binding_identity"][0].pop("src_token")
    path = tmp_path / "tampered.json"
    path.write_text(json.dumps(document), encoding="utf-8")
    with pytest.raises(manifest.ManifestError, match=message):
        manifest.verify_manifest(path, root=_ROOT)


def test_n_and_block_size_mismatch_is_rejected():
    with pytest.raises(manifest.ManifestError, match=r"sum\(block_sizes\)"):
        _schedule(n=3, block_sizes={"early": 1, "late": 1})
