# -*- coding: utf-8 -*-
"""8b oracle schedule/manifest の決定性と改竄拒否を検査する。"""
from __future__ import annotations

import copy
import hashlib
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path
from unittest import mock

import pytest


_HERE = Path(__file__).resolve().parent
_ORCHESTRATOR = _HERE.parent
_ROOT = _ORCHESTRATOR.parent
sys.path.insert(0, str(_ORCHESTRATOR.parent))
sys.path.insert(0, str(_HERE))

from orchestrator.campaign import s8b_oracle_manifest as manifest  # noqa: E402
from orchestrator.campaign import s8b_oracle_artifacts as artifacts  # noqa: E402
from orchestrator.campaign import s8b_oracle_spec as oracle_spec  # noqa: E402
from orchestrator.campaign import s8b_ratified_freeze as ratified_freeze  # noqa: E402
from orchestrator.campaign import s8b_holdout_freeze as holdout_freeze  # noqa: E402
import s8b_v2_freeze_fixture as v2_fixture  # noqa: E402
import s8b_oracle_spec_fixture as spec_fixture  # noqa: E402
import test_s8b_ratified_freeze  # noqa: E402


FREEZE_PATH = _ROOT / "output/s8b-freeze/holdout_freeze.json"
CONFIGURATION_IDS = (
    "p2_2_flag_opt", "backoff_fixed_best", "sort_best",
    "system_gate", "ident_all", "stock_common",
)
ROW_KEYS = {
    "block_id", "replicate_index", "schedule_index",
    "holdout_id", "configuration_id",
}
GENERATOR_SOURCES = {
    "materializer": "orchestrator/campaign/s1_direct_comparison.py",
    "report": "orchestrator/campaign/s8b_oracle_report.py",
    "judge": "orchestrator/campaign/s8b_oracle_judge.py",
    "outcome_stage_contract": (
        "orchestrator/campaign/s8b_outcome_stage_contract.py"
    ),
    "artifacts": "orchestrator/campaign/s8b_oracle_artifacts.py",
}
APPROVED_CONFIGURATION_IDS = (
    "backoff_fixed_best", "ident_all", "p2_2_flag_opt",
    "sort_best", "stock_common", "system_gate",
)
APPROVED_SCHEDULE_SHA256 = (
    "3b10b6b1575d06ac1efc9738d83c6d0179320e4374e9d6da8ec17ed0373f8065"
)
SUBSET_SCHEDULE_SHA256 = (
    "a5c4b580af849b74c232dbc46a86be80be74ab289add057dba1bbd1d3cd9aeda"
)
PIN_GATE_SCHEDULE_SHA256 = (
    "105bf4cb713f309fec174035814b7ab70ac892a70a51d62f028c31f6310c68d2"
)
PIN_GATE_SPEC_SHA256 = (
    "6c7f9365e96168749891bf7f0281285336163eaca751b91bacbc8c00f44acd5f"
)
# production serializer から独立した reviewed-spec golden。UTF-8 非 ASCII、
# sort 済み key 順、compact separator、末尾 LF 無しを raw bytes として固定する。
PIN_GATE_SPEC_RAW = (
    b'{"allowed_excluded_reasons":["machine-failure-\xe6\x97\xa5\xe6\x9c\xac"],'
    b'"binding_identity":['
    b'{"binding_sha256":"33adacfaaaf0299659434759c667f0e30035f47e0e8f66aebb4956ad5b21fd8c",'
    b'"configuration_id":"backoff_fixed_best","entry_sha256":"0000000000000000000000000000000000000000000000000000000000000000",'
    b'"genome_canonical":"g","holdout_id":"rr20","src_token":"s","variant_id":"v"},'
    b'{"binding_sha256":"33adacfaaaf0299659434759c667f0e30035f47e0e8f66aebb4956ad5b21fd8c",'
    b'"configuration_id":"stock_common","entry_sha256":"0000000000000000000000000000000000000000000000000000000000000000",'
    b'"genome_canonical":"g","holdout_id":"rr20","src_token":"s","variant_id":"v"},'
    b'{"binding_sha256":"33adacfaaaf0299659434759c667f0e30035f47e0e8f66aebb4956ad5b21fd8c",'
    b'"configuration_id":"backoff_fixed_best","entry_sha256":"0000000000000000000000000000000000000000000000000000000000000000",'
    b'"genome_canonical":"g","holdout_id":"rr80","src_token":"s","variant_id":"v"},'
    b'{"binding_sha256":"33adacfaaaf0299659434759c667f0e30035f47e0e8f66aebb4956ad5b21fd8c",'
    b'"configuration_id":"stock_common","entry_sha256":"0000000000000000000000000000000000000000000000000000000000000000",'
    b'"genome_canonical":"g","holdout_id":"rr80","src_token":"s","variant_id":"v"}],'
    b'"campaign_ids":{"b0":"campaign-b0"},"generator_versions":{'
    b'"artifacts":{"path":"orchestrator/campaign/s8b_oracle_artifacts.py",'
    b'"sha256":"576ce3cf83f4f3f693d47b6fecd219816f49ed7bfabc665458044e3c5c307c1d"},'
    b'"judge":{"path":"orchestrator/campaign/s8b_oracle_judge.py",'
    b'"sha256":"f3e2fbec0d9dc353dae987aa2f31afeafe178d75e544313fe1af84c06ec1ab3b"},'
    b'"materializer":{"path":"orchestrator/campaign/s1_direct_comparison.py",'
    b'"sha256":"b4b81da6193564ad688b4091efa80294fc4d18e587b2a58bef54320429cf177d"},'
    b'"outcome_stage_contract":{"path":"orchestrator/campaign/s8b_outcome_stage_contract.py",'
    b'"sha256":"f8a0bb2237dcaf3c643a78c04ca6b8cea2a8f83e3d306d85c781716b165c73af"},'
    b'"report":{"path":"orchestrator/campaign/s8b_oracle_report.py",'
    b'"sha256":"30fe2b1bcad143f5a85ca32250744522d6049f4c71e9b853618e3af2dd0091c7"}},'
    b'"run_contract":{"bench_max_rounds":1,"ccbench_pin":"pin","clocks":1800,'
    b'"contract_sha256":"0000000000000000000000000000000000000000000000000000000000000000",'
    b'"env_tag":"test-env","extime":5,"reps":5,"screening":"off","verify":"legacy+s2"},'
    b'"schedule_parameters":{"block_sizes":{"b0":1},'
    b'"configuration_ids":["backoff_fixed_best","stock_common"],'
    b'"holdout_ids":["rr20","rr80"],"master_seed":"pin-gate-seed-v1","n":1},'
    b'"schedule_sha256":"105bf4cb713f309fec174035814b7ab70ac892a70a51d62f028c31f6310c68d2",'
    b'"schema_version":"s8b-oracle-reviewed-spec/v1"}'
)

_APPROVED_BY_MANIFEST_ID = {}


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


def _source(path, *, root=_ROOT):
    source = Path(root) / path
    return {"path": path, "sha256": hashlib.sha256(source.read_bytes()).hexdigest()}


def _generator_versions(*, root=_ROOT):
    return {
        key: _source(path, root=root)
        for key, path in GENERATOR_SOURCES.items()
    }


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


def _build_manifest(freeze_path, *, schedule=None, generator_root=_ROOT):
    schedule = schedule or _schedule()
    bindings = [
        _binding(holdout_id, configuration_id)
        for holdout_id in _holdout_ids()
        for configuration_id in CONFIGURATION_IDS
    ]
    run_contract = {
        "ccbench_pin": "pin", "env_tag": "test-env", "clocks": 1800,
        "reps": 5, "extime": 5, "verify": "legacy+s2",
        "screening": "off", "bench_max_rounds": 1,
        "contract_sha256": "0" * 64,
    }
    campaign_ids = {
        block["block_id"]: f"campaign-{block['block_id']}"
        for block in schedule["blocks"]
    }
    parameters = {
        "n": schedule["n"],
        "master_seed": schedule["master_seed"],
        "block_sizes": {
            block["block_id"]: block["size"] for block in schedule["blocks"]
        },
        "holdout_ids": _holdout_ids(),
        "configuration_ids": CONFIGURATION_IDS,
    }
    approved = spec_fixture.make_reviewed_spec(
        root=generator_root,
        **parameters,
        run_contract=run_contract,
        campaign_ids=campaign_ids,
        binding_identity=bindings,
        allowed_excluded_reasons=["machine-failure"],
        generator_versions=_generator_versions(root=generator_root),
    )
    built = manifest._build_manifest(
        freeze_path=freeze_path,
        spec_sha256=approved.sha256,
        schedule=schedule,
        run_contract=run_contract,
        binding_identity=bindings,
        campaign_ids=campaign_ids,
        allowed_excluded_reasons=["machine-failure"],
        generator_versions=_generator_versions(root=generator_root),
    )
    _APPROVED_BY_MANIFEST_ID[built["manifest_id"]] = approved.reviewed_spec
    return built


def _freeze_copy(tmp_path):
    # strict v2 の per-pair floor + budget を共有 fixture で充填する (C3-4)。
    path = tmp_path / "holdout_freeze.json"
    document = json.loads(FREEZE_PATH.read_text(encoding="utf-8"))
    v2_fixture.fill(document)
    path.write_text(json.dumps(document, ensure_ascii=False), encoding="utf-8")
    return path


def _install_reviewed_spec_sources(root: Path) -> None:
    freeze = json.loads(FREEZE_PATH.read_text(encoding="utf-8"))
    paths = [freeze["known_axes_freeze"]["path"], *GENERATOR_SOURCES.values()]
    spec_fixture.install_reviewed_spec_sources(
        root, source_root=_ROOT, relative_paths=paths,
    )


def _reviewed_spec_document(root: Path, *, configuration_ids=None) -> dict:
    configurations = tuple(configuration_ids or APPROVED_CONFIGURATION_IDS)
    if configurations == APPROVED_CONFIGURATION_IDS:
        schedule_hash = APPROVED_SCHEDULE_SHA256
    elif configurations == ("stock_common",):
        schedule_hash = SUBSET_SCHEDULE_SHA256
    else:  # 独立 literal のない schedule をテスト内で自己再計算しない。
        raise AssertionError(f"unregistered reviewed schedule: {configurations!r}")
    holdout_ids = ("rr20", "rr80")
    fixture = spec_fixture.make_reviewed_spec(
        root=root,
        n=1,
        master_seed="approved-seed-v1",
        block_sizes={"b0": 1},
        holdout_ids=holdout_ids,
        configuration_ids=configurations,
        run_contract={
            "ccbench_pin": "pin", "env_tag": "test-env", "clocks": 1800,
            "reps": 5, "extime": 5, "verify": "legacy+s2",
            "screening": "off", "bench_max_rounds": 1,
            "contract_sha256": "0" * 64,
        },
        campaign_ids={"b0": "campaign-b0"},
        binding_identity=[
            _binding(holdout_id, configuration_id)
            for holdout_id in holdout_ids
            for configuration_id in configurations
        ],
        allowed_excluded_reasons=["machine-failure"],
        generator_versions=_generator_versions(root=root),
    )
    assert fixture.document["schedule_sha256"] == schedule_hash
    return fixture.document


def _install_reviewed_spec(root: Path, document: dict) -> bytes:
    return spec_fixture.install_reviewed_spec_document(root, document)


def _install_pin_gate_spec(root: Path) -> dict:
    document = json.loads(PIN_GATE_SPEC_RAW.decode("utf-8"))
    path = root / oracle_spec.SPEC_REL
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(PIN_GATE_SPEC_RAW)
    return document


def _synthetic_ratified_freeze(
        *, configuration_ids=None) -> ratified_freeze.RatifiedFreeze:
    if configuration_ids is None:
        document = _v2_document()
    else:
        document = json.loads(FREEZE_PATH.read_text(encoding="utf-8"))
        wanted = set(configuration_ids)
        for holdout in document["holdouts"].values():
            entries = holdout["variant_binding"]["entries"]
            holdout["variant_binding"]["entries"] = {
                key: value for key, value in entries.items() if key in wanted
            }
        v2_fixture.fill(document)
    raw = manifest._canonical_bytes(document)
    return ratified_freeze.RatifiedFreeze(
        document=document,
        sha256=hashlib.sha256(raw).hexdigest(),
        generation_number=1,
        activation_head="a" * 40,
        generation_commit="b" * 40,
    )


def _verify(path, freeze_path):
    """verify_manifest の必須 freeze_document/freeze_sha256 を freeze ファイルから
    構成して渡す (C2-7 の明示引数必須化への追随)。freeze ファイルの現在 bytes を
    読むため、freeze を改竄する negative テストではその改竄が sha に反映される。"""
    freeze_bytes = Path(freeze_path).read_bytes()
    freeze_doc = json.loads(freeze_bytes.decode("utf-8"))
    freeze_sha = hashlib.sha256(freeze_bytes).hexdigest()
    document = json.loads(Path(path).read_text(encoding="utf-8"))
    approved = _APPROVED_BY_MANIFEST_ID.get(document.get("manifest_id"))
    if approved is None:
        approved = next(iter(_APPROVED_BY_MANIFEST_ID.values()), object())
    pin = getattr(approved, "sha256", "0" * 64)
    with mock.patch.object(oracle_spec, "APPROVED_SPEC_SHA256", pin):
        return manifest.verify_manifest(
            path,
            root=_ROOT,
            freeze_document=freeze_doc,
            freeze_sha256=freeze_sha,
            approved_spec=approved,
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


def test_build_schedule_uses_replicate_major_cell_ordinals():
    n = 3
    holdout_ids = _holdout_ids()
    configuration_ids = CONFIGURATION_IDS
    schedule = manifest.build_schedule(
        n=n,
        master_seed="schedule-index-seed",
        block_sizes={"b0": n},
        holdout_ids=holdout_ids,
        configuration_ids=configuration_ids,
    )
    cell_count = len(holdout_ids) * len(configuration_ids)
    positions_by_replicate = defaultdict(list)
    for row in schedule["rows"]:
        assert row["schedule_index"] // cell_count == row["replicate_index"]
        positions_by_replicate[row["replicate_index"]].append(
            row["schedule_index"] % cell_count
        )

    expected_positions = set(range(cell_count))
    assert set(positions_by_replicate) == set(range(n))
    for positions in positions_by_replicate.values():
        assert len(positions) == cell_count
        assert len(set(positions)) == cell_count
        assert set(positions) == expected_positions


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
    manifest._write_manifest(path, document)
    verified = _verify(path, freeze_path)
    assert type(document) is artifacts.OfficialManifest
    assert isinstance(verified, manifest.VerifiedManifest)
    assert type(verified.document) is artifacts.OfficialManifest
    assert verified.document == document
    assert verified.sha256 == _canonical_sha256(document)
    with pytest.raises(manifest.ManifestError, match="既に存在"):
        manifest._write_manifest(path, document)


def test_subset_manifest_build_stays_accepted_but_verify_choke_point_rejects(
        tmp_path):
    """MU-1: generic builder は不変、実行 choke point だけが一様 subset を拒否。"""
    freeze_path = _freeze_copy(tmp_path)
    schedule = manifest.build_schedule(
        n=1,
        master_seed="subset-seed",
        block_sizes={"b0": 1},
        holdout_ids=_holdout_ids(),
        configuration_ids=("stock_common",),
    )
    document = manifest._build_manifest(
        freeze_path=freeze_path,
        spec_sha256="a" * 64,
        schedule=schedule,
        run_contract={
            "ccbench_pin": "pin", "env_tag": "test-env", "clocks": 1800,
            "reps": 5, "extime": 5, "verify": "legacy+s2",
            "screening": "off", "bench_max_rounds": 1,
            "contract_sha256": "0" * 64,
        },
        binding_identity=[
            _binding(holdout_id, "stock_common")
            for holdout_id in _holdout_ids()
        ],
        campaign_ids={"b0": "campaign-b0"},
        allowed_excluded_reasons=["machine-failure"],
        generator_versions=_generator_versions(),
    )
    path = tmp_path / "subset-manifest.json"
    manifest._write_manifest(path, document)
    with pytest.raises(
            manifest.ManifestError,
            match="holdout-configuration product と完全一致しない"):
        _verify(path, freeze_path)


def test_missing_holdout_build_stays_accepted_but_verify_rejects(tmp_path):
    """F-1: generic builder は不変、choke point は freeze の全 holdout を要求。"""
    freeze_path = _freeze_copy(tmp_path)
    freeze = json.loads(freeze_path.read_text(encoding="utf-8"))
    retained, dropped = sorted(freeze["holdouts"])
    # generic builder の従来受理集合を保持したまま負例を組めるよう、execution
    # snapshot だけを schedule subset と整合させ、authority の holdouts は全件残す。
    del freeze["floor"]["by_holdout"][dropped]
    del freeze["budget"]["per_holdout_bench_s"][dropped]
    freeze_path.write_text(
        json.dumps(freeze, ensure_ascii=False), encoding="utf-8",
    )
    schedule = manifest.build_schedule(
        n=1,
        master_seed="missing-holdout-seed",
        block_sizes={"b0": 1},
        holdout_ids=(retained,),
        configuration_ids=CONFIGURATION_IDS,
    )
    document = manifest._build_manifest(
        freeze_path=freeze_path,
        spec_sha256="a" * 64,
        schedule=schedule,
        run_contract={
            "ccbench_pin": "pin", "env_tag": "test-env", "clocks": 1800,
            "reps": 5, "extime": 5, "verify": "legacy+s2",
            "screening": "off", "bench_max_rounds": 1,
            "contract_sha256": "0" * 64,
        },
        binding_identity=[
            _binding(retained, configuration_id)
            for configuration_id in CONFIGURATION_IDS
        ],
        campaign_ids={"b0": "campaign-b0"},
        allowed_excluded_reasons=["machine-failure"],
        generator_versions=_generator_versions(),
    )
    assert type(document) is artifacts.OfficialManifest
    path = tmp_path / "missing-holdout-manifest.json"
    manifest._write_manifest(path, document)

    with pytest.raises(
            manifest.ManifestError,
            match=r"schedule holdout 集合が freeze\.holdouts と完全一致しない"):
        _verify(path, freeze_path)


def test_verified_manifest_public_constructor_is_rejected(tmp_path):
    freeze_path = _freeze_copy(tmp_path)
    document = _build_manifest(freeze_path)
    message = (
        "VerifiedManifest は verify_manifest の検証結果からのみ構築できる"
    )

    with pytest.raises(manifest.ManifestError, match=message):
        manifest.VerifiedManifest(
            document=document, sha256=_canonical_sha256(document),
        )

    class VerifiedManifestSubclass(manifest.VerifiedManifest):
        pass

    with pytest.raises(manifest.ManifestError, match=message):
        VerifiedManifestSubclass(
            document=document, sha256=_canonical_sha256(document),
        )
    with pytest.raises(manifest.ManifestError, match=message):
        manifest.VerifiedManifest(
            document=dict(document), sha256=_canonical_sha256(document),
        )
    assert not hasattr(manifest, "_SEAL")


def test_verified_manifest_sealed_constructor_rejects_non_lowercase_hash(
        tmp_path, monkeypatch):
    freeze_path = _freeze_copy(tmp_path)
    document = _build_manifest(freeze_path)
    path = tmp_path / "oracle_manifest.json"
    manifest._write_manifest(path, document)
    original = manifest._canonical_sha256

    def uppercase_final_official_hash(value):
        digest = original(value)
        if type(value) is artifacts.OfficialManifest:
            return digest.upper()
        return digest

    monkeypatch.setattr(
        manifest, "_canonical_sha256", uppercase_final_official_hash,
    )
    with pytest.raises(manifest.ManifestError, match="lowercase 64 hex"):
        _verify(path, freeze_path)


def test_write_manifest_rejects_exploration_and_legacy_artifact_types(tmp_path):
    exploration = artifacts.ExplorationArtifact({
        "schema_version": artifacts.EXPLORATION_ARTIFACT_SCHEMA,
    })
    legacy = artifacts.LegacyManifest({"campaign_ids": {}})
    for document in (exploration, legacy, dict(exploration)):
        with pytest.raises(artifacts.OracleArtifactTypeError, match="OfficialManifest"):
            manifest._write_manifest(tmp_path / "must-not-exist.json", document)
    assert not (tmp_path / "must-not-exist.json").exists()


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
        manifest._build_manifest(
            freeze_path=freeze_path,
            spec_sha256="a" * 64,
            schedule=schedule,
            run_contract={
                "ccbench_pin": "pin", "env_tag": "test-env", "clocks": 1800,
                "reps": 5, "extime": 5, "verify": "legacy+s2",
                "screening": "off", "bench_max_rounds": 1,
                "contract_sha256": "0" * 64,
            },
            binding_identity=bindings,
            campaign_ids={block["block_id"]: f"campaign-{block['block_id']}"
                          for block in schedule["blocks"]},
            allowed_excluded_reasons=["machine-failure"],
            generator_versions=_generator_versions(),
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


def _assert_generator_versions_rejected(
        tmp_path, freeze_path, document, generator_versions, message):
    with pytest.raises(manifest.ManifestError, match=message):
        manifest._build_manifest(
            freeze_path=freeze_path,
            spec_sha256="a" * 64,
            schedule=document["schedule"],
            run_contract=document["run_contract"],
            binding_identity=document["binding_identity"],
            campaign_ids=document["campaign_ids"],
            allowed_excluded_reasons=document["allowed_excluded_reasons"],
            generator_versions=generator_versions,
        )

    tampered = copy.deepcopy(document)
    tampered["generator_versions"] = generator_versions
    path = tmp_path / "generator-tampered.json"
    path.write_text(json.dumps(tampered), encoding="utf-8")
    with pytest.raises(manifest.ManifestError, match=message):
        _verify(path, freeze_path)


def test_generator_versions_exact_five_canonical_paths_and_hashes_verify(tmp_path):
    freeze_path = _freeze_copy(tmp_path)
    document = _build_manifest(freeze_path)
    path = tmp_path / "oracle-manifest-five-generators.json"
    manifest._write_manifest(path, document)
    verified = _verify(path, freeze_path)

    assert set(verified.document["generator_versions"]) == set(GENERATOR_SOURCES)
    for key, canonical_path in GENERATOR_SOURCES.items():
        record = verified.document["generator_versions"][key]
        assert record["path"] == canonical_path
        assert record["sha256"] == hashlib.sha256(
            (_ROOT / canonical_path).read_bytes()
        ).hexdigest()


def test_legacy_three_key_generator_authority_is_rejected_directly_at_build(
        tmp_path):
    freeze_path = _freeze_copy(tmp_path)
    schedule = _schedule(n=1)
    three_key_generators = {
        key: _source(GENERATOR_SOURCES[key])
        for key in ("materializer", "report", "judge")
    }

    with pytest.raises(
            manifest.ManifestError,
            match=(
                r"missing=\['artifacts', 'outcome_stage_contract'\] "
                r"extra=\[\]"
            )):
        manifest._build_manifest(
            freeze_path=freeze_path,
            spec_sha256="a" * 64,
            schedule=schedule,
            run_contract={
                "ccbench_pin": "pin",
                "env_tag": "test-env",
                "clocks": 1800,
                "reps": 5,
                "extime": 5,
                "verify": "legacy+s2",
                "screening": "off",
                "bench_max_rounds": 1,
                "contract_sha256": "0" * 64,
            },
            binding_identity=[
                _binding(holdout_id, configuration_id)
                for holdout_id in _holdout_ids()
                for configuration_id in CONFIGURATION_IDS
            ],
            campaign_ids={"b0": "campaign-b0"},
            allowed_excluded_reasons=["machine-failure"],
            generator_versions=three_key_generators,
        )


@pytest.mark.parametrize("key", tuple(GENERATOR_SOURCES))
def test_generator_hash_must_match_real_root_file_at_build_and_verify(
        tmp_path, key):
    freeze_path = _freeze_copy(tmp_path)
    document = _build_manifest(freeze_path)
    false_generators = copy.deepcopy(document["generator_versions"])
    false_generators[key]["sha256"] = "0" * 64
    _assert_generator_versions_rejected(
        tmp_path, freeze_path, document, false_generators, "実 byte hash",
    )


@pytest.mark.parametrize(
    ("missing_key", "message"),
    [
        (
            "outcome_stage_contract",
            r"missing=\['outcome_stage_contract'\] extra=\[\]",
        ),
        ("artifacts", r"missing=\['artifacts'\] extra=\[\]"),
    ],
)
def test_generator_versions_missing_required_key_is_rejected_at_build_and_verify(
        tmp_path, missing_key, message):
    freeze_path = _freeze_copy(tmp_path)
    document = _build_manifest(freeze_path)
    generator_versions = copy.deepcopy(document["generator_versions"])
    generator_versions.pop(missing_key)
    _assert_generator_versions_rejected(
        tmp_path, freeze_path, document, generator_versions, message,
    )


def test_generator_versions_extra_key_is_rejected_at_build_and_verify(tmp_path):
    freeze_path = _freeze_copy(tmp_path)
    document = _build_manifest(freeze_path)
    generator_versions = copy.deepcopy(document["generator_versions"])
    generator_versions["unexpected"] = _source("orchestrator/campaign/wal.py")
    _assert_generator_versions_rejected(
        tmp_path,
        freeze_path,
        document,
        generator_versions,
        r"missing=\[\] extra=\['unexpected'\]",
    )


@pytest.mark.parametrize(
    "damage",
    ["swapped-paths", "unrelated-artifacts", "absolute-artifacts"],
)
def test_generator_path_must_match_key_canonical_binding_at_build_and_verify(
        tmp_path, damage):
    freeze_path = _freeze_copy(tmp_path)
    document = _build_manifest(freeze_path)
    generator_versions = copy.deepcopy(document["generator_versions"])
    if damage == "swapped-paths":
        generator_versions["materializer"], generator_versions["report"] = (
            generator_versions["report"],
            generator_versions["materializer"],
        )
    elif damage == "unrelated-artifacts":
        generator_versions["artifacts"] = _source(
            "orchestrator/campaign/wal.py"
        )
    else:
        generator_versions["artifacts"]["path"] = str(
            (_ROOT / GENERATOR_SOURCES["artifacts"]).resolve()
        )
    _assert_generator_versions_rejected(
        tmp_path, freeze_path, document, generator_versions, "canonical path",
    )


def test_verify_rehashes_each_canonical_generator_in_supplied_root(
        tmp_path, monkeypatch):
    root_a = tmp_path / "root-a"
    root_b = tmp_path / "root-b"
    known_axes_path = "output/s1-freeze/known_axes_freeze.json"
    for fixture_root in (root_a, root_b):
        for relative_path in (*GENERATOR_SOURCES.values(), known_axes_path):
            target = fixture_root / relative_path
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes((_ROOT / relative_path).read_bytes())

    freeze_document = json.loads(FREEZE_PATH.read_text(encoding="utf-8"))
    v2_fixture.fill(freeze_document)
    freeze_path = root_a / "output/s8b-freeze/holdout_freeze.json"
    freeze_path.parent.mkdir(parents=True)
    freeze_path.write_text(
        json.dumps(freeze_document, ensure_ascii=False), encoding="utf-8",
    )
    monkeypatch.setattr(manifest, "ROOT", root_a)
    document = _build_manifest(
        freeze_path, generator_root=root_a,
    )
    manifest_path = tmp_path / "root-a-manifest.json"
    manifest._write_manifest(manifest_path, document)

    artifacts_path_b = root_b / GENERATOR_SOURCES["artifacts"]
    artifacts_path_b.write_bytes(artifacts_path_b.read_bytes() + b"x")
    freeze_bytes = freeze_path.read_bytes()
    with pytest.raises(
            manifest.ManifestError,
            match=r"generator_versions\.artifacts\.sha256 が実 byte hash と不一致"):
        manifest.verify_manifest(
            manifest_path,
            root=root_b,
            freeze_document=json.loads(freeze_bytes.decode("utf-8")),
            freeze_sha256=hashlib.sha256(freeze_bytes).hexdigest(),
            approved_spec=object(),
        )


def test_verify_manifest_rejects_retired_floor_budget_snapshot_key(tmp_path):
    freeze_path = _freeze_copy(tmp_path)
    document = _build_manifest(freeze_path)
    approved = _APPROVED_BY_MANIFEST_ID[document["manifest_id"]]
    freeze_bytes = freeze_path.read_bytes()
    freeze_document = json.loads(freeze_bytes)
    document["floor_budget_snapshot_sha256"] = _canonical_sha256({
        "floor": freeze_document["floor"],
        "budget": freeze_document["budget"],
    })
    path = tmp_path / "retired-key-manifest.json"
    path.write_text(json.dumps(document), encoding="utf-8")

    with pytest.raises(
            manifest.ManifestError, match="^manifest top-level schema が不一致$"):
        manifest.verify_manifest(
            path,
            root=_ROOT,
            freeze_document=freeze_document,
            freeze_sha256=hashlib.sha256(freeze_bytes).hexdigest(),
            approved_spec=approved,
        )


def test_verify_detects_freeze_byte_tampering(tmp_path):
    freeze_path = _freeze_copy(tmp_path)
    document = _build_manifest(freeze_path)
    path = tmp_path / "oracle_manifest.json"
    manifest._write_manifest(path, document)
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
    bindings = [
        _binding(holdout_id, configuration_id)
        for holdout_id in _holdout_ids()
        for configuration_id in CONFIGURATION_IDS
    ]
    campaign_ids = {
        "early": "campaign-early",
        "late": "campaign-late",
    }
    # build 側: 2 block schedule から manifest を組もうとすると拒否される。
    with pytest.raises(manifest.ManifestError, match="正確に 1 件でない"):
        manifest._build_manifest(
            freeze_path=freeze_path,
            spec_sha256="0" * 64,
            schedule=two_block_schedule,
            run_contract=_run_contract(),
            binding_identity=bindings,
            campaign_ids=campaign_ids,
            allowed_excluded_reasons=["machine-failure"],
            generator_versions=_generator_versions(),
        )

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


def test_reviewed_spec_rejects_two_blocks_before_approval(tmp_path):
    root = tmp_path / "repo"
    root.mkdir()
    _install_reviewed_spec_sources(root)

    holdout_ids = _holdout_ids()
    with pytest.raises(
            oracle_spec.ReviewedSpecError,
            match=r"正確に 1 件でない",
    ) as captured:
        spec_fixture.make_reviewed_spec(
            root=root,
            n=3,
            master_seed="seed-a",
            block_sizes={"early": 1, "late": 2},
            holdout_ids=holdout_ids,
            configuration_ids=CONFIGURATION_IDS,
            run_contract=_run_contract(),
            campaign_ids={
                "early": "campaign-early",
                "late": "campaign-late",
            },
            binding_identity=[
                _binding(holdout_id, configuration_id)
                for holdout_id in holdout_ids
                for configuration_id in CONFIGURATION_IDS
            ],
            allowed_excluded_reasons=["machine-failure"],
            generator_versions=_generator_versions(root=root),
        )

    assert captured.value.reason == "invalid-reviewed-spec"


# ---------------------------------------------------------------------------
# execution snapshot: floor 外形と budget の検査
# ---------------------------------------------------------------------------
def _v2_document():
    document = json.loads(FREEZE_PATH.read_text(encoding="utf-8"))
    v2_fixture.fill(document)
    return document


def _snapshot(document):
    manifest._validate_execution_snapshot(
        document, holdout_ids=tuple(document["holdouts"]),
    )


def test_snapshot_rejects_oracle_shared_false():
    document = copy.deepcopy(_v2_document())
    document["budget"]["oracle_shared"] = False
    with pytest.raises(manifest.ManifestError, match="oracle_shared が true でない"):
        _snapshot(document)


def test_snapshot_rejects_extra_top_level_floor_key():
    # floor は exact {by_holdout}。旧 field 混入を拒否する。
    document = _v2_document()
    document["floor"]["stale"] = 1.0
    with pytest.raises(manifest.ManifestError, match=r"exact \{by_holdout\}"):
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


def test_canonical_bytes_rejects_nan_value():
    # M1: _canonical_bytes は allow_nan=False で NaN 値の canonical 化を拒否する。
    # json.dumps(allow_nan=False) は NaN で ValueError を送出し、_canonical_bytes は
    # それを ManifestError に翻訳する (from exc で __cause__ に元 ValueError を保持)。
    # 変異 = allow_nan=False 除去 → json.dumps が "NaN" を吐いて成功し、このテストが赤になる。
    with pytest.raises(manifest.ManifestError) as ei:
        manifest._canonical_bytes({"x": float("nan")})
    # allow_nan=False が発火した証拠として、翻訳元が ValueError であることを固定する。
    assert isinstance(ei.value.__cause__, ValueError)


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
# reviewed spec approval pin / approved-manifest CLI
# ---------------------------------------------------------------------------
def test_reviewed_spec_exact_schema_and_independent_schedule_hash_literal(
        tmp_path, monkeypatch):
    root = tmp_path / "repo"
    root.mkdir()
    _install_reviewed_spec_sources(root)
    document = _reviewed_spec_document(root)
    raw = _install_reviewed_spec(root, document)
    monkeypatch.setattr(
        oracle_spec, "APPROVED_SPEC_SHA256", hashlib.sha256(raw).hexdigest(),
    )

    approved = oracle_spec.load_approved_spec(root)

    assert json.loads(approved.raw_bytes.decode("utf-8")) == document
    assert approved.raw_bytes == raw
    assert approved.schedule["n"] == 1
    assert manifest.schedule_sha256(
        oracle_spec._mutable_json_tree(approved.schedule)
    ) == APPROVED_SCHEDULE_SHA256


def test_reviewed_spec_document_and_schedule_are_recursive_immutable(
        tmp_path, monkeypatch):
    root = tmp_path / "repo"
    root.mkdir()
    _install_reviewed_spec_sources(root)
    document = _reviewed_spec_document(root)
    raw = _install_reviewed_spec(root, document)
    monkeypatch.setattr(
        oracle_spec, "APPROVED_SPEC_SHA256", hashlib.sha256(raw).hexdigest(),
    )
    approved = oracle_spec.load_approved_spec(root)

    document["campaign_ids"]["b0"] = "changed-after-load"
    with pytest.raises(TypeError):
        approved.document["campaign_ids"]["b0"] = "mutated"
    with pytest.raises(TypeError):
        approved.schedule["rows"][0]["holdout_id"] = "mutated"
    assert approved.document["campaign_ids"]["b0"] == "campaign-b0"
    assert approved.schedule["rows"][0]["holdout_id"] in {"rr20", "rr80"}


def test_approved_snapshot_requires_canonical_reviewed_spec_exact_type(
        tmp_path, monkeypatch):
    root = tmp_path / "repo"
    root.mkdir()
    _install_reviewed_spec_sources(root)
    document = _reviewed_spec_document(root)
    raw = _install_reviewed_spec(root, document)
    sha256 = hashlib.sha256(raw).hexdigest()
    monkeypatch.setattr(oracle_spec, "APPROVED_SPEC_SHA256", sha256)
    canonical = oracle_spec.load_approved_spec(root)

    class ReviewedSpecSubclass(oracle_spec.ReviewedSpec):
        pass

    subclass = ReviewedSpecSubclass(
        document=canonical.document,
        raw_bytes=canonical.raw_bytes,
        sha256=canonical.sha256,
        schedule=canonical.schedule,
    )
    with pytest.raises(
            oracle_spec.ReviewedSpecError, match="ReviewedSpec exact type"):
        oracle_spec.validate_approved_spec_snapshot(subclass, root=root)


def test_reviewed_spec_has_independent_canonical_bytes_and_sha_literal(
        tmp_path, monkeypatch):
    root = tmp_path / "repo"
    root.mkdir()
    _install_reviewed_spec_sources(root)
    document = _install_pin_gate_spec(root)
    monkeypatch.setattr(
        oracle_spec, "APPROVED_SPEC_SHA256", PIN_GATE_SPEC_SHA256,
    )

    approved = oracle_spec.load_approved_spec(root)

    assert json.loads(approved.raw_bytes.decode("utf-8")) == document
    assert approved.raw_bytes == PIN_GATE_SPEC_RAW
    assert approved.sha256 == PIN_GATE_SPEC_SHA256
    assert hashlib.sha256(PIN_GATE_SPEC_RAW).hexdigest() == PIN_GATE_SPEC_SHA256
    assert b"machine-failure-\xe6\x97\xa5\xe6\x9c\xac" in PIN_GATE_SPEC_RAW
    assert PIN_GATE_SPEC_RAW.startswith(b'{"allowed_excluded_reasons":')
    assert not PIN_GATE_SPEC_RAW.endswith(b"\n")
    assert manifest.schedule_sha256(
        oracle_spec._mutable_json_tree(approved.schedule)
    ) == PIN_GATE_SCHEDULE_SHA256


def test_reviewed_spec_none_pin_is_always_no_approved_spec(tmp_path, monkeypatch):
    root = tmp_path / "repo"
    path = root / oracle_spec.SPEC_REL
    path.parent.mkdir(parents=True)
    path.write_bytes(b"not-json")
    monkeypatch.setattr(oracle_spec, "APPROVED_SPEC_SHA256", None)

    with pytest.raises(oracle_spec.ReviewedSpecError) as captured:
        oracle_spec.load_approved_spec(root)

    assert captured.value.reason == "no-approved-spec"


def test_reviewed_spec_pin_mismatch_is_fail_closed(tmp_path, monkeypatch):
    root = tmp_path / "repo"
    root.mkdir()
    _install_reviewed_spec_sources(root)
    document = _reviewed_spec_document(root)
    _install_reviewed_spec(root, document)
    monkeypatch.setattr(oracle_spec, "APPROVED_SPEC_SHA256", "f" * 64)

    with pytest.raises(oracle_spec.ReviewedSpecError) as captured:
        oracle_spec.load_approved_spec(root)

    assert captured.value.reason == "approved-spec-hash-mismatch"


@pytest.mark.parametrize("layer", ["top", "schedule", "run-contract"])
def test_reviewed_spec_key_sets_are_exact(tmp_path, layer):
    root = tmp_path / "repo"
    root.mkdir()
    _install_reviewed_spec_sources(root)
    document = _reviewed_spec_document(root)
    if layer == "top":
        document["unexpected"] = None
    elif layer == "schedule":
        document["schedule_parameters"]["unexpected"] = None
    else:
        document["run_contract"]["unexpected"] = None

    with pytest.raises(oracle_spec.ReviewedSpecError) as captured:
        oracle_spec.validate_reviewed_spec(document, root=root)

    assert captured.value.reason == "invalid-reviewed-spec"


def test_reviewed_spec_requires_canonical_bytes_without_trailing_lf(
        tmp_path, monkeypatch):
    root = tmp_path / "repo"
    root.mkdir()
    _install_reviewed_spec_sources(root)
    raw = PIN_GATE_SPEC_RAW + b"\n"
    path = root / oracle_spec.SPEC_REL
    path.parent.mkdir(parents=True)
    path.write_bytes(raw)
    monkeypatch.setattr(
        oracle_spec, "APPROVED_SPEC_SHA256", hashlib.sha256(raw).hexdigest(),
    )

    with pytest.raises(oracle_spec.ReviewedSpecError) as captured:
        oracle_spec.load_approved_spec(root)

    assert captured.value.reason == "invalid-reviewed-spec"


@pytest.mark.parametrize(
    "public_name",
    ("build_manifest", "build_manifest_from_ratified", "write_manifest"),
)
def test_ungated_manifest_apis_are_not_public(public_name):
    """拒否の含意: 選択 gate のない旧 3 名は属性解決できず、構築・保存へ到達しない。
    受理の含意: public な build_approved_manifest の正例は
    test_build_approved_uses_one_active_snapshot_and_writes_valid_candidate が担う。"""
    with pytest.raises(AttributeError):
        getattr(manifest, public_name)


@pytest.mark.parametrize(
    "option",
    [
        "--schedule", "--schedule-path", "--freeze", "--freeze-path",
        "--campaign-id", "--campaign-ids", "--spec", "--approval",
        "--approver", "--root", "--n", "--master-seed", "--block-sizes",
        "--holdout-id", "--configuration-id",
    ],
)
def test_build_approved_parser_has_output_as_only_value_input(option):
    with pytest.raises(SystemExit) as captured:
        manifest._parser().parse_args([
            "build-approved",
            "--output", f"{manifest.MANIFEST_CANDIDATE_DIR}/manifest.json",
            option, "caller-value",
        ])
    assert captured.value.code == 2


def test_approved_writer_rejects_outside_candidate_root(tmp_path):
    document = artifacts.OfficialManifest({"schema_version": "fixture"})
    with pytest.raises(manifest.ManifestCliError) as captured:
        manifest._write_approved_manifest(
            "outside/manifest.json", document, root=tmp_path,
        )
    assert captured.value.reason == "invalid-output-path"
    assert not (tmp_path / "outside").exists()


def test_approved_writer_rejects_symlink_parent(tmp_path):
    document = artifacts.OfficialManifest({"schema_version": "fixture"})
    output = tmp_path / "output"
    output.mkdir()
    target = tmp_path / "symlink-target"
    target.mkdir()
    (output / "s8b-oracle-manifest-candidates").symlink_to(
        target, target_is_directory=True,
    )
    with pytest.raises(manifest.ManifestCliError) as captured:
        manifest._write_approved_manifest(
            f"{manifest.MANIFEST_CANDIDATE_DIR}/manifest.json",
            document,
            root=tmp_path,
        )
    assert captured.value.reason == "invalid-output-path"
    assert list(target.iterdir()) == []


def test_approved_writer_is_exclusive_create(tmp_path):
    document = artifacts.OfficialManifest({"schema_version": "fixture"})
    path = tmp_path / manifest.MANIFEST_CANDIDATE_DIR / "manifest.json"
    path.parent.mkdir(parents=True)
    path.write_bytes(b"existing")
    with pytest.raises(manifest.ManifestCliError) as captured:
        manifest._write_approved_manifest(
            f"{manifest.MANIFEST_CANDIDATE_DIR}/manifest.json",
            document,
            root=tmp_path,
        )
    assert captured.value.reason == "output-exists"
    assert path.read_bytes() == b"existing"


def test_approved_writer_safely_creates_only_fixed_candidate_root(tmp_path):
    root = tmp_path / "repo"
    root.mkdir()
    document = artifacts.OfficialManifest({"schema_version": "fixture"})
    output = f"{manifest.MANIFEST_CANDIDATE_DIR}/manifest.json"

    manifest._write_approved_manifest(output, document, root=root)

    path = root / output
    assert path.is_file()
    assert json.loads(path.read_text(encoding="utf-8")) == document
    nested_output = f"{manifest.MANIFEST_CANDIDATE_DIR}/caller-dir/other.json"
    with pytest.raises(manifest.ManifestCliError) as captured:
        manifest._write_approved_manifest(nested_output, document, root=root)
    assert captured.value.reason == "invalid-output-path"
    assert not (root / manifest.MANIFEST_CANDIDATE_DIR / "caller-dir").exists()
    assert not (root / "outside").exists()


def test_build_approved_active_without_pin_fails_before_output(
        tmp_path, monkeypatch):
    root = tmp_path / "repo"
    root.mkdir()
    active = _synthetic_ratified_freeze()
    monkeypatch.setattr(
        ratified_freeze, "load_ratified_freeze", lambda candidate: active,
    )
    selection_calls = []
    monkeypatch.setattr(
        ratified_freeze,
        "assert_g1_floor_selection_identity",
        lambda candidate, candidate_root: selection_calls.append(
            (candidate, candidate_root)
        ),
    )
    monkeypatch.setattr(oracle_spec, "APPROVED_SPEC_SHA256", None)
    output = f"{manifest.MANIFEST_CANDIDATE_DIR}/manifest.json"

    with pytest.raises(manifest.ManifestCliError) as captured:
        manifest.build_approved_manifest(output, root=root)

    assert captured.value.reason == "no-approved-spec"
    assert selection_calls == [(active, root)]
    assert not (root / manifest.MANIFEST_CANDIDATE_DIR).exists()


def test_build_approved_valid_fixture_output_depends_only_on_spec_pin(
        tmp_path, monkeypatch):
    """MU-6: valid 入力で pin の一点だけが candidate 出力の有無を変える。"""
    root = tmp_path / "repo"
    root.mkdir()
    _install_reviewed_spec_sources(root)
    _install_pin_gate_spec(root)
    active = _synthetic_ratified_freeze(
        configuration_ids=("backoff_fixed_best", "stock_common"),
    )
    monkeypatch.setattr(
        ratified_freeze, "load_ratified_freeze", lambda candidate: active,
    )
    selection_calls = []
    monkeypatch.setattr(
        ratified_freeze,
        "assert_g1_floor_selection_identity",
        lambda candidate, candidate_root: selection_calls.append(
            (candidate, candidate_root)
        ),
    )
    output = f"{manifest.MANIFEST_CANDIDATE_DIR}/pin-behavior.json"

    monkeypatch.setattr(oracle_spec, "APPROVED_SPEC_SHA256", None)
    with pytest.raises(manifest.ManifestCliError):
        manifest.build_approved_manifest(output, root=root)
    assert not (root / output).exists()

    monkeypatch.setattr(
        oracle_spec, "APPROVED_SPEC_SHA256", PIN_GATE_SPEC_SHA256,
    )
    built = manifest.build_approved_manifest(output, root=root)

    assert type(built) is artifacts.OfficialManifest
    assert selection_calls == [(active, root), (active, root)]
    assert (root / output).is_file()


def test_build_approved_uses_one_active_snapshot_and_writes_valid_candidate(
        tmp_path, monkeypatch):
    root = tmp_path / "repo"
    root.mkdir()
    _install_reviewed_spec_sources(root)
    document = _reviewed_spec_document(root)
    raw = _install_reviewed_spec(root, document)
    monkeypatch.setattr(
        oracle_spec, "APPROVED_SPEC_SHA256", hashlib.sha256(raw).hexdigest(),
    )
    active = _synthetic_ratified_freeze()
    calls = []
    selection_calls = []

    def load_once(candidate):
        calls.append(Path(candidate))
        return active

    monkeypatch.setattr(ratified_freeze, "load_ratified_freeze", load_once)
    monkeypatch.setattr(
        ratified_freeze,
        "assert_g1_floor_selection_identity",
        lambda candidate, candidate_root: selection_calls.append(
            (candidate, candidate_root)
        ),
    )
    output = f"{manifest.MANIFEST_CANDIDATE_DIR}/manifest.json"

    built = manifest.build_approved_manifest(output, root=root)

    assert calls == [root]
    assert selection_calls == [(active, root)]
    output_path = root / output
    assert output_path.is_file()
    verified = manifest.verify_manifest(
        output_path,
        root=root,
        freeze_document=active.document,
        freeze_sha256=active.sha256,
        approved_spec=oracle_spec.load_approved_spec(root),
    )
    assert verified.document == built


def test_build_approved_rejects_uniform_configuration_subset_before_output(
        tmp_path, monkeypatch):
    root = tmp_path / "repo"
    root.mkdir()
    _install_reviewed_spec_sources(root)
    document = _reviewed_spec_document(
        root, configuration_ids=("stock_common",),
    )
    raw = _install_reviewed_spec(root, document)
    monkeypatch.setattr(
        oracle_spec, "APPROVED_SPEC_SHA256", hashlib.sha256(raw).hexdigest(),
    )
    active = _synthetic_ratified_freeze()
    monkeypatch.setattr(
        ratified_freeze, "load_ratified_freeze", lambda candidate: active,
    )
    selection_calls = []
    monkeypatch.setattr(
        ratified_freeze,
        "assert_g1_floor_selection_identity",
        lambda candidate, candidate_root: selection_calls.append(
            (candidate, candidate_root)
        ),
    )
    output = f"{manifest.MANIFEST_CANDIDATE_DIR}/manifest.json"

    with pytest.raises(manifest.ManifestCliError) as captured:
        manifest.build_approved_manifest(output, root=root)

    assert captured.value.reason == "approved-spec-cell-product-mismatch"
    assert selection_calls == [(active, root)]
    assert not (root / manifest.MANIFEST_CANDIDATE_DIR).exists()


def test_build_approved_valid_real_g1_reaches_spec_after_actual_selection_gate(
        tmp_path, monkeypatch):
    from orchestrator.tests.test_s8b_expected_materialization import _run_sealed_case

    case = "_sealed_case_build_approved_valid_real_g1_reaches_spec_after_actual_selection_gate"
    result = _run_sealed_case(
        __name__, case, tmp_path,
    )
    assert result == {"case": case, "completed": True}


def _sealed_case_build_approved_valid_real_g1_reaches_spec_after_actual_selection_gate(tmp_path, monkeypatch):
    root, *_ = test_s8b_ratified_freeze.build_production_emitter_g1(tmp_path)
    monkeypatch.setattr(oracle_spec, "APPROVED_SPEC_SHA256", None)
    output = f"{manifest.MANIFEST_CANDIDATE_DIR}/manifest.json"

    with pytest.raises(manifest.ManifestCliError) as captured:
        manifest.build_approved_manifest(output, root=root)

    assert captured.value.reason == "no-approved-spec"
    assert isinstance(captured.value.__cause__, oracle_spec.ReviewedSpecError)
    assert not (root / output).exists()


def test_build_approved_real_g1_rule_mismatch_preserves_selection_reason(
        tmp_path, monkeypatch):
    from orchestrator.tests.test_s8b_expected_materialization import _run_sealed_case

    case = "_sealed_case_build_approved_real_g1_rule_mismatch_preserves_selection_reason"
    result = _run_sealed_case(
        __name__, case, tmp_path,
    )
    assert result == {"case": case, "completed": True}


def _sealed_case_build_approved_real_g1_rule_mismatch_preserves_selection_reason(tmp_path, monkeypatch):
    root, _sha, _rel, _g1, topology = (
        test_s8b_ratified_freeze.build_production_emitter_g1(tmp_path)
    )
    selected_rel = topology["paths"]["result"]
    earlier_rel = selected_rel.replace(
        "20260718T120000Z", "20260718T115959Z",
    )
    assert earlier_rel != selected_rel
    earlier_path = root / earlier_rel
    earlier_path.parent.mkdir(parents=True, exist_ok=True)
    earlier_path.write_bytes((root / selected_rel).read_bytes())
    test_s8b_ratified_freeze._commit_exact(
        root,
        [earlier_rel],
        subject="earlier official result",
        agent="fixture",
    )
    eligibility_calls = []

    def derive_eligibility(**kwargs):
        eligibility_calls.append(kwargs["result_rel"])
        return kwargs["result_rel"] == earlier_rel

    monkeypatch.setattr(
        holdout_freeze,
        "_derive_floor_selection_eligibility",
        derive_eligibility,
    )
    output = f"{manifest.MANIFEST_CANDIDATE_DIR}/manifest.json"

    with pytest.raises(manifest.ManifestCliError) as captured:
        manifest.build_approved_manifest(output, root=root)

    assert captured.value.reason == "floor-selection-rule-mismatch"
    assert isinstance(
        captured.value.__cause__, ratified_freeze.RatifiedFreezeError,
    )
    assert captured.value.__cause__.reason == "floor-selection-rule-mismatch"
    assert eligibility_calls == [earlier_rel]
    assert not (root / output).exists()


def _install_projection_root(root: Path, *, alter_report=False) -> Path:
    root.mkdir()
    freeze = json.loads(FREEZE_PATH.read_text(encoding="utf-8"))
    configurations = {"backoff_fixed_best", "stock_common"}
    for holdout in freeze["holdouts"].values():
        entries = holdout["variant_binding"]["entries"]
        holdout["variant_binding"]["entries"] = {
            key: value for key, value in entries.items()
            if key in configurations
        }
    v2_fixture.fill(freeze)
    freeze_path = root / "output/s8b-freeze/holdout_freeze.json"
    freeze_path.parent.mkdir(parents=True)
    freeze_path.write_text(json.dumps(freeze, ensure_ascii=False), encoding="utf-8")
    _install_reviewed_spec_sources(root)
    if alter_report:
        report_path = root / GENERATOR_SOURCES["report"]
        report_path.write_bytes(report_path.read_bytes() + b"\n# projection-b\n")
    return freeze_path


def _projection_inputs(root: Path) -> dict:
    holdout_ids = ("rr20", "rr80")
    configuration_ids = ("backoff_fixed_best", "stock_common")
    return {
        "root": root,
        "n": 1,
        "master_seed": "projection-seed-a",
        "block_sizes": {"b0": 1},
        "holdout_ids": holdout_ids,
        "configuration_ids": configuration_ids,
        "run_contract": _run_contract(),
        "campaign_ids": {"b0": "campaign-b0"},
        "binding_identity": [
            _binding(holdout_id, configuration_id)
            for holdout_id in holdout_ids
            for configuration_id in configuration_ids
        ],
        "allowed_excluded_reasons": ["machine-failure"],
        "generator_versions": _generator_versions(root=root),
    }


def _build_projection_manifest(
        *, freeze_path: Path, spec_sha256: str,
        schedule: dict, run_contract: dict, campaign_ids: dict,
        binding_identity: list, allowed_excluded_reasons: list,
        generator_versions: dict):
    return manifest._build_manifest(
        freeze_path=freeze_path,
        spec_sha256=spec_sha256,
        schedule=schedule,
        run_contract=run_contract,
        binding_identity=binding_identity,
        campaign_ids=campaign_ids,
        allowed_excluded_reasons=allowed_excluded_reasons,
        generator_versions=generator_versions,
    )


def _verify_projection_manifest(
        *, root: Path, freeze_path: Path, document,
        approved: oracle_spec.ReviewedSpec, monkeypatch):
    path = root / f"projection-manifest-{document['manifest_id']}.json"
    manifest._write_manifest(path, document)
    raw = freeze_path.read_bytes()
    monkeypatch.setattr(
        oracle_spec, "APPROVED_SPEC_SHA256", approved.sha256,
    )
    return manifest.verify_manifest(
        path,
        root=root,
        freeze_document=json.loads(raw.decode("utf-8")),
        freeze_sha256=hashlib.sha256(raw).hexdigest(),
        approved_spec=approved,
    )


def test_verify_manifest_accepts_exact_approved_spec_projection(
        tmp_path, monkeypatch):
    root = tmp_path / "spec-a-root"
    freeze_path = _install_projection_root(root)
    inputs = _projection_inputs(root)
    approved = spec_fixture.make_reviewed_spec(**inputs)
    schedule = manifest.build_schedule(
        n=1,
        master_seed="projection-seed-a",
        block_sizes={"b0": 1},
        holdout_ids=("rr20", "rr80"),
        configuration_ids=("backoff_fixed_best", "stock_common"),
    )
    monkeypatch.setattr(manifest, "ROOT", root)
    document = _build_projection_manifest(
        freeze_path=freeze_path,
        spec_sha256=approved.sha256,
        schedule=schedule,
        run_contract=_run_contract(),
        campaign_ids={"b0": "campaign-b0"},
        binding_identity=[
            _binding(holdout_id, configuration_id)
            for holdout_id in ("rr20", "rr80")
            for configuration_id in ("backoff_fixed_best", "stock_common")
        ],
        allowed_excluded_reasons=["machine-failure"],
        generator_versions=_generator_versions(root=root),
    )

    verified = _verify_projection_manifest(
        root=root,
        freeze_path=freeze_path,
        document=document,
        approved=approved.reviewed_spec,
        monkeypatch=monkeypatch,
    )

    assert verified.document == document


@pytest.mark.parametrize(
    ("projection", "message"),
    [
        ("schedule", "schedule が approved spec"),
        ("campaign_ids", "campaign_ids が approved spec"),
        ("run_contract", "run_contract が approved spec"),
        ("binding_identity", "binding_identity が approved spec"),
        (
            "allowed_excluded_reasons",
            "allowed_excluded_reasons が approved spec",
        ),
        ("generator_versions", "generator_versions が approved spec"),
        ("spec_sha256", "spec_sha256 が approved spec"),
        ("spec_sha256_format", "spec_sha256 が SHA-256"),
    ],
)
def test_verify_manifest_rejects_one_spec_divergent_projection(
        tmp_path, monkeypatch, projection, message):
    root_a = tmp_path / "spec-a-root"
    root_b = tmp_path / "manifest-b-root"
    freeze_a = _install_projection_root(root_a)
    freeze_b = _install_projection_root(root_b, alter_report=True)
    spec_a_inputs = _projection_inputs(root_a)
    spec_a = spec_fixture.make_reviewed_spec(**spec_a_inputs)

    baseline = _build_projection_manifest(
        freeze_path=freeze_a,
        spec_sha256=spec_a.sha256,
        schedule=copy.deepcopy(spec_a.schedule),
        run_contract=copy.deepcopy(spec_a.document["run_contract"]),
        campaign_ids=copy.deepcopy(spec_a.document["campaign_ids"]),
        binding_identity=copy.deepcopy(spec_a.document["binding_identity"]),
        allowed_excluded_reasons=copy.deepcopy(
            spec_a.document["allowed_excluded_reasons"]
        ),
        generator_versions=copy.deepcopy(
            spec_a.document["generator_versions"]
        ),
    )
    baseline_verified = _verify_projection_manifest(
        root=root_a,
        freeze_path=freeze_a,
        document=baseline,
        approved=spec_a.reviewed_spec,
        monkeypatch=monkeypatch,
    )
    assert baseline_verified.document == baseline

    schedule_b = manifest.build_schedule(
        n=1,
        master_seed="projection-seed-a",
        block_sizes={"b0": 1},
        holdout_ids=("rr20", "rr80"),
        configuration_ids=("backoff_fixed_best", "stock_common"),
    )
    run_contract_b = _run_contract()
    campaign_ids_b = {"b0": "campaign-b0"}
    bindings_b = [
        _binding(holdout_id, configuration_id)
        for holdout_id in ("rr20", "rr80")
        for configuration_id in ("backoff_fixed_best", "stock_common")
    ]
    reasons_b = ["machine-failure"]
    selected_root = root_a
    selected_freeze = freeze_a
    generators_b = _generator_versions(root=root_a)
    recorded_spec_sha = spec_a.sha256

    if projection == "schedule":
        schedule_b = manifest.build_schedule(
            n=2,
            master_seed="projection-seed-b",
            block_sizes={"b0": 2},
            holdout_ids=("rr20", "rr80"),
            configuration_ids=("backoff_fixed_best", "stock_common"),
        )
    elif projection == "campaign_ids":
        campaign_ids_b = {"b0": "campaign-other"}
    elif projection == "run_contract":
        run_contract_b["env_tag"] = "other-env"
    elif projection == "binding_identity":
        bindings_b.reverse()
    elif projection == "allowed_excluded_reasons":
        reasons_b = ["operator-abort"]
    elif projection == "generator_versions":
        selected_root = root_b
        selected_freeze = freeze_b
        generators_b = _generator_versions(root=root_b)
    elif projection == "spec_sha256":
        spec_b_inputs = copy.deepcopy(spec_a_inputs)
        spec_b_inputs["allowed_excluded_reasons"] = ["operator-abort"]
        spec_b = spec_fixture.make_reviewed_spec(**spec_b_inputs)
        recorded_spec_sha = spec_b.sha256

    monkeypatch.setattr(manifest, "ROOT", selected_root)
    manifest_b = _build_projection_manifest(
        freeze_path=selected_freeze,
        spec_sha256=recorded_spec_sha,
        schedule=schedule_b,
        run_contract=run_contract_b,
        campaign_ids=campaign_ids_b,
        binding_identity=bindings_b,
        allowed_excluded_reasons=reasons_b,
        generator_versions=generators_b,
    )
    if projection == "spec_sha256_format":
        manifest_b["spec_sha256"] = "not-a-sha256"
        without_id = dict(manifest_b)
        without_id.pop("manifest_id")
        manifest_b["manifest_id"] = manifest._manifest_id(without_id)

    with pytest.raises(manifest.ManifestError, match=message):
        _verify_projection_manifest(
            root=selected_root,
            freeze_path=selected_freeze,
            document=manifest_b,
            approved=spec_a.reviewed_spec,
            monkeypatch=monkeypatch,
        )


# ---------------------------------------------------------------------------
# M5: bench_max_rounds == 1 完全一致 pin
# ---------------------------------------------------------------------------
def _run_contract(bench_max_rounds=1):
    return {
        "ccbench_pin": "pin", "env_tag": "test-env", "clocks": 1800,
        "reps": 5, "extime": 5, "verify": "legacy+s2",
        "screening": "off", "bench_max_rounds": bench_max_rounds,
        "contract_sha256": "0" * 64,
    }


def test_run_contract_accepts_bench_max_rounds_one():
    source = _run_contract(1)
    validated = manifest._validate_run_contract(source)  # 例外なし
    assert validated["bench_max_rounds"] == 1
    assert validated is not source


def test_generic_builder_still_accepts_run_contract_extra_key(tmp_path):
    """D288: generic builder の部分集合受理と余剰 key 保存を維持する。"""
    freeze_path = _freeze_copy(tmp_path)
    schedule = _schedule(n=1)
    run_contract = _run_contract()
    run_contract["future_extension"] = {"enabled": True}
    document = manifest._build_manifest(
        freeze_path=freeze_path,
        spec_sha256="a" * 64,
        schedule=schedule,
        run_contract=run_contract,
        binding_identity=[
            _binding(holdout_id, configuration_id)
            for holdout_id in _holdout_ids()
            for configuration_id in CONFIGURATION_IDS
        ],
        campaign_ids={"b0": "campaign-b0"},
        allowed_excluded_reasons=["machine-failure"],
        generator_versions=_generator_versions(),
    )

    assert document["run_contract"]["future_extension"] == {"enabled": True}


def test_run_contract_rejects_bench_max_rounds_two():
    with pytest.raises(manifest.ManifestError, match="bench_max_rounds"):
        manifest._validate_run_contract(_run_contract(2))


def test_run_contract_rejects_extime_three():
    source = _run_contract()
    source["extime"] = 3
    with pytest.raises(manifest.ManifestError, match="extime"):
        manifest._validate_run_contract(source)


def test_run_contract_rejects_reps_999():
    source = _run_contract()
    source["reps"] = 999
    with pytest.raises(manifest.ManifestError, match="reps"):
        manifest._validate_run_contract(source)


def test_verify_manifest_requires_freeze_document(tmp_path):
    freeze_path = _freeze_copy(tmp_path)
    document = _build_manifest(freeze_path)
    path = tmp_path / "oracle_manifest.json"
    manifest._write_manifest(path, document)
    with pytest.raises(manifest.ManifestError, match="freeze_document"):
        manifest.verify_manifest(
            path,
            root=_ROOT,
            freeze_document=None,
            freeze_sha256=None,
            approved_spec=object(),
        )
