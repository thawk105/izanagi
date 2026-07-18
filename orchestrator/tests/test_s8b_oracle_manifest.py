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
sys.path.insert(0, str(_HERE))

from campaign import s8b_oracle_manifest as manifest  # noqa: E402
import s8b_v2_freeze_fixture as v2_fixture  # noqa: E402


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
    # 単一 block 契約 (A3-3): 既定は 1 block に予定全行を含める。
    return manifest.build_schedule(
        n=n,
        master_seed=seed,
        block_sizes=block_sizes or {"b0": n},
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
    # strict v2 の per-pair floor + budget を共有 fixture で充填する (C3-4)。
    path = tmp_path / "holdout_freeze.json"
    document = json.loads(FREEZE_PATH.read_text(encoding="utf-8"))
    v2_fixture.fill(document)
    path.write_text(json.dumps(document, ensure_ascii=False), encoding="utf-8")
    return path


def _verify(path, freeze_path):
    """verify_manifest の必須 freeze_document/freeze_sha256 を freeze ファイルから
    構成して渡す (C2-7 の明示引数必須化への追随)。freeze ファイルの現在 bytes を
    読むため、freeze を改竄する negative テストではその改竄が sha に反映される。"""
    freeze_bytes = Path(freeze_path).read_bytes()
    freeze_doc = json.loads(freeze_bytes.decode("utf-8"))
    freeze_sha = hashlib.sha256(freeze_bytes).hexdigest()
    return manifest.verify_manifest(
        path, root=_ROOT, freeze_document=freeze_doc, freeze_sha256=freeze_sha,
    )


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
    verified = _verify(path, freeze_path)
    assert isinstance(verified, manifest.VerifiedManifest)
    assert verified.document == document
    assert verified.sha256 == _canonical_sha256(document)
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
        _verify(path, freeze_path)


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
        _verify(path, freeze_path)


def test_verify_detects_freeze_byte_tampering(tmp_path):
    freeze_path = _freeze_copy(tmp_path)
    document = _build_manifest(freeze_path)
    path = tmp_path / "oracle_manifest.json"
    manifest.write_manifest(path, document)
    freeze_path.write_bytes(freeze_path.read_bytes() + b"\n")
    with pytest.raises(manifest.ManifestError, match="freeze byte sha256"):
        _verify(path, freeze_path)


@pytest.mark.parametrize(
    ("tamper", "message"),
    [("schedule-hash", "schedule_sha256"),
     ("campaign-empty", "campaign ID"),
     ("binding-schema", "binding_identity entry schema")],
)
def test_verify_detects_manifest_tampering(tmp_path, tamper, message):
    freeze_path = _freeze_copy(tmp_path)
    document = _build_manifest(freeze_path)
    if tamper == "schedule-hash":
        document["schedule_sha256"] = "f" * 64
    elif tamper == "campaign-empty":
        # 単一 block では ID 重複は作れないため、空 ID (fail-closed) を検査する。
        document["campaign_ids"] = {
            block_id: "" for block_id in document["campaign_ids"]
        }
    else:
        document["binding_identity"][0].pop("src_token")
    path = tmp_path / "tampered.json"
    path.write_text(json.dumps(document), encoding="utf-8")
    with pytest.raises(manifest.ManifestError, match=message):
        _verify(path, freeze_path)


def test_n_and_block_size_mismatch_is_rejected():
    with pytest.raises(manifest.ManifestError, match=r"sum\(block_sizes\)"):
        _schedule(n=3, block_sizes={"early": 1, "late": 1})


def test_v1_two_block_manifest_is_rejected_at_build_and_verify(tmp_path):
    """V1: early/late 2 block manifest が build と verify の双方で reject される。

    A3-3 の両破綻経路 (共有台帳での焼失 / block 別 path での総枠 block 数倍 fail-open) を
    単一 block 化で構造的に閉じたことを確認する。
    """
    freeze_path = _freeze_copy(tmp_path)
    two_block_schedule = manifest.build_schedule(
        n=3, master_seed="seed-a", block_sizes={"early": 1, "late": 2},
        holdout_ids=_holdout_ids(), configuration_ids=CONFIGURATION_IDS,
    )
    # build 側: 2 block schedule から manifest を組もうとすると拒否される。
    with pytest.raises(manifest.ManifestError, match="正確に 1 件でない"):
        _build_manifest(freeze_path, schedule=two_block_schedule)

    # verify 側: 正当な単一 block manifest の schedule.blocks を 2 件へ改竄しても拒否される。
    document = _build_manifest(freeze_path)
    document["schedule"]["blocks"] = [
        {"block_id": "early", "size": 1},
        {"block_id": "late", "size": 2},
    ]
    path = tmp_path / "two-block-tampered.json"
    path.write_text(json.dumps(document), encoding="utf-8")
    with pytest.raises(manifest.ManifestError, match="正確に 1 件でない"):
        _verify(path, freeze_path)


# ---------------------------------------------------------------------------
# M1/C3-3: per-pair floor table の exact 検査 (execution snapshot)
# ---------------------------------------------------------------------------
def _v2_document():
    document = json.loads(FREEZE_PATH.read_text(encoding="utf-8"))
    v2_fixture.fill(document)
    return document


def _snapshot(document):
    manifest._validate_execution_snapshot(
        document, holdout_ids=tuple(document["holdouts"]),
    )


def _first_holdout_floor(document):
    holdout_id = next(iter(document["holdouts"]))
    return holdout_id, document["floor"]["by_holdout"][holdout_id]


def test_snapshot_accepts_valid_per_pair_floor():
    _snapshot(_v2_document())  # 正例: 例外なし


def test_snapshot_accepts_explicit_null_pair():
    # 明示 null: pair 1 件を null にし、scalar_alt も null (相関充足)。scale_ref は
    # 非 null (stock 有効) のまま。判定不能 pair を持つ正常 freeze を受理する。
    document = _v2_document()
    _holdout, floor_h = _first_holdout_floor(document)
    a_pair = sorted(floor_h["pairs"])[0]
    floor_h["pairs"][a_pair] = None
    floor_h["scalar_alt"] = None
    _snapshot(document)


def test_snapshot_accepts_all_null_holdout():
    # stock 未確定 holdout: 全 pair null + scalar_alt null + scale_ref null。
    document = _v2_document()
    _holdout, floor_h = _first_holdout_floor(document)
    floor_h["pairs"] = {cfg: None for cfg in floor_h["pairs"]}
    floor_h["scalar_alt"] = None
    floor_h["scale_ref"] = None
    _snapshot(document)


def test_snapshot_rejects_scalar_v1_floor():
    # scalar (v1 数値) 形の holdout 値は Mapping でないため拒否。
    document = _v2_document()
    holdout_id, _floor_h = _first_holdout_floor(document)
    document["floor"]["by_holdout"][holdout_id] = 0.01
    with pytest.raises(manifest.ManifestError, match="pairs, scale_ref, scalar_alt"):
        _snapshot(document)


def test_snapshot_rejects_stock_key_in_pairs():
    document = _v2_document()
    _holdout, floor_h = _first_holdout_floor(document)
    floor_h["pairs"]["stock_common"] = 0.01
    with pytest.raises(manifest.ManifestError, match="pairs の key 集合"):
        _snapshot(document)


def test_snapshot_rejects_missing_pair():
    document = _v2_document()
    _holdout, floor_h = _first_holdout_floor(document)
    dropped = sorted(floor_h["pairs"])[0]
    del floor_h["pairs"][dropped]
    with pytest.raises(manifest.ManifestError, match="pairs の key 集合"):
        _snapshot(document)


def test_snapshot_rejects_extra_pair():
    document = _v2_document()
    _holdout, floor_h = _first_holdout_floor(document)
    floor_h["pairs"]["not-a-configuration"] = 0.02
    with pytest.raises(manifest.ManifestError, match="pairs の key 集合"):
        _snapshot(document)


def test_snapshot_rejects_scale_ref_null_with_finite_pair():
    # 相関違反: scale_ref=null なのに pair/scalar_alt が非 null。
    document = _v2_document()
    _holdout, floor_h = _first_holdout_floor(document)
    floor_h["scale_ref"] = None
    with pytest.raises(manifest.ManifestError, match="scale_ref"):
        _snapshot(document)


def test_snapshot_rejects_scalar_alt_not_max():
    # 全 pair 非 null だが scalar_alt が max(pairs) と不一致。
    document = _v2_document()
    _holdout, floor_h = _first_holdout_floor(document)
    floor_h["scalar_alt"] = floor_h["scalar_alt"] + 1.0
    with pytest.raises(manifest.ManifestError, match="scalar_alt"):
        _snapshot(document)


def test_snapshot_rejects_extra_top_level_floor_key():
    # floor は exact {by_holdout}。旧 field 混入を拒否する。
    document = _v2_document()
    document["floor"]["stale"] = 1.0
    with pytest.raises(manifest.ManifestError, match=r"exact \{by_holdout\}"):
        _snapshot(document)


def test_snapshot_rejects_nonfinite_pair_value():
    # 有限正でない pair (0 以下) を拒否する。
    document = _v2_document()
    _holdout, floor_h = _first_holdout_floor(document)
    a_pair = sorted(floor_h["pairs"])[0]
    floor_h["pairs"][a_pair] = 0.0
    with pytest.raises(manifest.ManifestError, match="有限正 float or null"):
        _snapshot(document)


# ---------------------------------------------------------------------------
# M3: strict JSON load (duplicate key / NaN リテラル拒否)
# ---------------------------------------------------------------------------
def test_load_json_object_rejects_duplicate_top_level_key(tmp_path):
    path = tmp_path / "dup.json"
    path.write_text('{"a": 1, "a": 2}', encoding="utf-8")
    with pytest.raises(manifest.ManifestError, match="重複キー"):
        manifest._load_json_object(path)


def test_load_json_object_rejects_duplicate_nested_key(tmp_path):
    path = tmp_path / "dup-nested.json"
    path.write_text('{"outer": {"b": 1, "b": 2}}', encoding="utf-8")
    with pytest.raises(manifest.ManifestError, match="重複キー"):
        manifest._load_json_object(path)


def test_load_json_object_rejects_nan_literal(tmp_path):
    path = tmp_path / "nan.json"
    path.write_text('{"x": NaN}', encoding="utf-8")
    with pytest.raises(manifest.ManifestError, match="非数値定数"):
        manifest._load_json_object(path)


def test_load_json_object_rejects_infinity_literal(tmp_path):
    path = tmp_path / "inf.json"
    path.write_text('{"x": Infinity}', encoding="utf-8")
    with pytest.raises(manifest.ManifestError, match="非数値定数"):
        manifest._load_json_object(path)


# ---------------------------------------------------------------------------
# M5: bench_max_rounds == 1 完全一致 pin
# ---------------------------------------------------------------------------
def _run_contract(bench_max_rounds=1):
    return {
        "ccbench_pin": "pin", "env_tag": "test-env", "clocks": 1800,
        "reps": 5, "extime": 3, "verify": "legacy+s2",
        "screening": "off", "bench_max_rounds": bench_max_rounds,
    }


def test_run_contract_accepts_bench_max_rounds_one():
    manifest._validate_run_contract(_run_contract(1))  # 例外なし


def test_run_contract_rejects_bench_max_rounds_two():
    with pytest.raises(manifest.ManifestError, match="bench_max_rounds"):
        manifest._validate_run_contract(_run_contract(2))


def test_verify_manifest_requires_freeze_document(tmp_path):
    freeze_path = _freeze_copy(tmp_path)
    document = _build_manifest(freeze_path)
    path = tmp_path / "oracle_manifest.json"
    manifest.write_manifest(path, document)
    with pytest.raises(manifest.ManifestError, match="freeze_document"):
        manifest.verify_manifest(
            path, root=_ROOT, freeze_document=None, freeze_sha256=None,
        )
