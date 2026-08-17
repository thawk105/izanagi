# -*- coding: utf-8 -*-
"""8b oracle official/exploration artifact 境界を検査する。"""
from __future__ import annotations

import ast
import hashlib
import json
import subprocess
import sys
from pathlib import Path

import pytest


ORCH = Path(__file__).resolve().parents[1]
ROOT = ORCH.parent
if str(ORCH.parent) not in sys.path:
    sys.path.insert(0, str(ORCH.parent))

from orchestrator.campaign import s8b_oracle_artifacts as artifacts  # noqa: E402
from orchestrator.campaign import s8b_oracle_exploration as exploration  # noqa: E402
from orchestrator.campaign.layout import (  # noqa: E402
    campaign_layout,
    exploration_campaign_layout,
)


def _degraded_measurement_fixture():
    leading_indicators = {
        "ipc": None,
        "llc_miss_rate": None,
        "perf_raw": {
            "LLC-load-misses": None,
            "LLC-loads": None,
            "instructions": None,
            "cycles": None,
        },
    }
    receipt = {
        "schema": "izanagi-perf-preflight/v1",
        "status": "unavailable",
        "available": False,
        "reason": "perf-not-found",
        "rc": None,
        "parsed_events": [],
        "probe_argv": [
            "perf", "stat", "-x,", "-o", "<tmp>/perf.csv", "-e",
            "LLC-load-misses,LLC-loads,instructions,cycles", "--", "/bin/true",
        ],
        "stderr_sha256": "0" * 64,
        "candidates": [],
    }
    run_cmd = ["./db_bench", "--threads=1"]
    observation = artifacts._perf_preflight.build_perf_observation(
        receipt, run_cmd=run_cmd, leading_indicators=leading_indicators,
    )
    return observation, run_cmd, leading_indicators


def test_exploration_package_uses_disjoint_namespace_schema_and_accepts_three_by_three_hint(
    tmp_path,
):
    layout = exploration_campaign_layout("trial-a", output_root=str(tmp_path))
    document = exploration.package_exploration_artifact(
        layout=layout,
        artifact_role="manifest",
        extime_s=3,
        reps=3,
        payload={"generic": "result"},
    )

    output = tmp_path / "exploration/campaigns/trial-a/reports/manifest.exploration.json"
    assert type(document) is artifacts.ExplorationArtifact
    assert json.loads(output.read_text(encoding="utf-8")) == document
    assert set(document) == artifacts.EXPLORATION_ARTIFACT_KEYS
    assert document["schema_version"] == artifacts.EXPLORATION_ARTIFACT_SCHEMA
    assert document["measurement_hint"] == {"extime_s": 3, "reps": 3}
    assert json.loads((tmp_path / "exploration/namespace.json").read_text()) == {
        "namespace": "exploration",
    }
    assert not (tmp_path / "campaigns").exists()


@pytest.mark.parametrize("campaign_id", ["", ".", "..", ".hidden", "a/b"])
def test_exploration_package_rejects_invalid_slug(campaign_id, tmp_path):
    with pytest.raises(ValueError, match="campaign_id"):
        exploration_campaign_layout(campaign_id, output_root=str(tmp_path))


@pytest.mark.parametrize(
    ("field", "value"),
    [("extime_s", True), ("extime_s", 0), ("reps", False), ("reps", 0)],
)
def test_exploration_package_rejects_invalid_hint(field, value, tmp_path):
    kwargs = {"extime_s": 3, "reps": 3}
    kwargs[field] = value
    with pytest.raises(artifacts.OracleArtifactTypeError, match=field):
        exploration.package_exploration_artifact(
            layout=exploration_campaign_layout("trial-a", output_root=str(tmp_path)),
            artifact_role="manifest",
            payload={"generic": "result"},
            **kwargs,
        )


def test_exploration_package_rejects_unknown_role_and_official_layout(tmp_path):
    layout = exploration_campaign_layout("trial-a", output_root=str(tmp_path))
    with pytest.raises(artifacts.OracleArtifactTypeError, match="artifact_role"):
        exploration.package_exploration_artifact(
            layout=layout, artifact_role="unknown", extime_s=3, reps=3, payload={},
        )
    with pytest.raises(artifacts.OracleArtifactTypeError, match="exact type"):
        exploration.package_exploration_artifact(
            layout=campaign_layout("trial-a", output_root=str(tmp_path)),
            artifact_role="manifest", extime_s=3, reps=3, payload={},
        )


def test_official_loaders_reject_exploration_schema_for_all_roles():
    payload = json.dumps({
        "schema_version": artifacts.EXPLORATION_ARTIFACT_SCHEMA,
        "artifact_role": "manifest",
        "campaign_id": "trial-a",
        "measurement_hint": {"extime_s": 3, "reps": 3},
        "payload": {},
    }).encode()
    for loader in (
        artifacts.load_official_manifest,
        artifacts.load_official_observations,
        artifacts.load_official_verdict,
    ):
        with pytest.raises(artifacts.OracleArtifactTypeError):
            loader(payload)


@pytest.mark.parametrize(
    "loader",
    [
        artifacts.load_official_manifest,
        artifacts.load_official_observations,
        artifacts.load_official_verdict,
    ],
)
def test_role_loaders_reject_duplicate_schema_version(loader):
    payload = b'{"schema_version":"first","schema_version":"second","run_contract":{}}'
    with pytest.raises(artifacts.OracleArtifactTypeError, match="重複キー"):
        loader(payload)


@pytest.mark.parametrize(
    ("loader", "official_schema"),
    [
        (artifacts.load_official_manifest, artifacts.OFFICIAL_MANIFEST_SCHEMA),
        (artifacts.load_official_observations, artifacts.OFFICIAL_OBSERVATIONS_SCHEMA),
        (artifacts.load_official_verdict, artifacts.OFFICIAL_VERDICT_SCHEMA),
    ],
)
@pytest.mark.parametrize(
    "tail",
    [',"value":1e999', ',"nested":{"values":[1e999]}'],
    ids=["top-level", "nested"],
)
def test_role_loaders_reject_exponent_overflow(loader, official_schema, tail):
    run_contract = ',"run_contract":{}' if loader is artifacts.load_official_manifest else ""
    payload = (
        f'{{"schema_version":"{official_schema}"{run_contract}{tail}}}'
    ).encode()

    with pytest.raises(artifacts.OracleArtifactTypeError, match="有限でない"):
        loader(payload)


@pytest.mark.parametrize(
    ("loader", "other_official_schema"),
    [
        (artifacts.load_official_observations, artifacts.OFFICIAL_VERDICT_SCHEMA),
        (artifacts.load_official_verdict, artifacts.OFFICIAL_OBSERVATIONS_SCHEMA),
    ],
)
def test_observations_and_verdict_loaders_reject_unknown_schema(
    loader, other_official_schema,
):
    for rejected in (None, "unknown/v1", other_official_schema):
        with pytest.raises(artifacts.OracleArtifactTypeError, match="schema_version"):
            loader(json.dumps({"schema_version": rejected}).encode())


def test_observations_loader_preserves_t080_sibling_field_exactly():
    sibling = {
        "schema_version": "izanagi-t080-freeze-migration-observation/v1",
        "sentinel": {"nested": [None, "preserved"]},
    }
    document = {
        "schema_version": artifacts.OFFICIAL_OBSERVATIONS_SCHEMA,
        "t080_freeze_migration_observation": sibling,
    }

    loaded = artifacts.load_official_observations(
        json.dumps(document, ensure_ascii=False).encode("utf-8"),
    )

    assert type(loaded) is artifacts.OfficialObservations
    assert loaded == document
    assert loaded["t080_freeze_migration_observation"] == sibling


def test_manifest_loader_separates_official_and_legacy_markers():
    official = artifacts.load_official_manifest(json.dumps({
        "schema_version": artifacts.OFFICIAL_MANIFEST_SCHEMA,
        "run_contract": {},
    }).encode())
    no_schema = artifacts.load_official_manifest(b'{"campaign_ids":{}}')
    no_contract = artifacts.load_official_manifest(json.dumps({
        "schema_version": artifacts.OFFICIAL_MANIFEST_SCHEMA,
    }).encode())

    assert type(official) is artifacts.OfficialManifest
    assert type(no_schema) is artifacts.LegacyManifest
    assert type(no_contract) is artifacts.LegacyManifest
    assert not issubclass(artifacts.LegacyManifest, artifacts.OfficialManifest)
    assert issubclass(artifacts.OracleArtifactTypeError, TypeError)


def test_manifest_loader_rejects_explicit_null_or_unknown_schema():
    for schema in (None, "unknown/v1", artifacts.EXPLORATION_ARTIFACT_SCHEMA):
        with pytest.raises(artifacts.OracleArtifactTypeError, match="schema_version"):
            artifacts.load_official_manifest(json.dumps({
                "schema_version": schema,
                "run_contract": {},
            }).encode())


def test_artifact_contract_import_loads_no_other_campaign_module():
    code = f"""
import sys
sys.path.insert(0, {str(ORCH.parent)!r})
before = set(sys.modules)
import orchestrator.campaign.s8b_oracle_artifacts
loaded = sorted(name for name in set(sys.modules) - before
                if name.startswith('orchestrator.campaign.')
                and name != 'orchestrator.campaign.s8b_oracle_artifacts')
assert loaded == [], loaded
"""
    completed = subprocess.run(
        [sys.executable, "-c", code], cwd=ROOT,
        text=True, capture_output=True, check=False,
    )
    assert completed.returncode == 0, completed.stderr


def test_oracle_schema_aliases_are_sourced_from_artifact_leaf():
    expected = {
        "s8b_oracle_manifest.py": {
            "SCHEMA_VERSION": "OFFICIAL_MANIFEST_SCHEMA",
        },
        "s8b_oracle_report.py": {
            "SCHEMA_VERSION": "OFFICIAL_OBSERVATIONS_SCHEMA",
        },
        "s8b_oracle_judge.py": {
            "INPUT_SCHEMA": "OFFICIAL_OBSERVATIONS_SCHEMA",
            "OUTPUT_SCHEMA": "OFFICIAL_VERDICT_SCHEMA",
        },
        "s8b_verdict.py": {
            "SCHEMA_VERSION": "COMBINED_VERDICT_SCHEMA",
            "ORACLE_SCHEMA": "OFFICIAL_VERDICT_SCHEMA",
        },
    }
    for filename, aliases in expected.items():
        tree = ast.parse((ORCH / "campaign" / filename).read_text(encoding="utf-8"))
        assignments = {
            node.targets[0].id: node.value
            for node in tree.body
            if isinstance(node, ast.Assign)
            and len(node.targets) == 1
            and isinstance(node.targets[0], ast.Name)
        }
        for name, attribute in aliases.items():
            value = assignments[name]
            assert isinstance(value, ast.Attribute)
            assert isinstance(value.value, ast.Name) and value.value.id == "_artifacts"
            assert value.attr == attribute


def test_exploration_cli_packages_three_by_three_without_official_output(tmp_path):
    input_path = tmp_path / "payload.json"
    input_path.write_text('{"generic":"result"}', encoding="utf-8")
    script = ORCH / "campaign/s8b_oracle_exploration.py"
    completed = subprocess.run([
        sys.executable, str(script),
        "--output-root", str(tmp_path),
        "--campaign-id", "cli-trial",
        "--role", "observations",
        "--extime-s", "3",
        "--reps", "3",
        "--input", str(input_path),
    ], cwd=ROOT, text=True, capture_output=True, check=False)

    assert completed.returncode == 0, completed.stderr
    packaged = tmp_path / (
        "exploration/campaigns/cli-trial/reports/observations.exploration.json"
    )
    assert artifacts.load_exploration_artifact(packaged)["measurement_hint"] == {
        "extime_s": 3, "reps": 3,
    }
    assert not (tmp_path / "campaigns").exists()
    assert set(tmp_path.glob("*.json")) == {input_path}


def test_measurement_manifest_write_load_and_hash_are_bound(tmp_path):
    observation, run_cmd, leading_indicators = _degraded_measurement_fixture()
    output = tmp_path / "measurement-manifest.json"

    written = artifacts.write_measurement_manifest(
        output,
        oracle_manifest_sha256="a" * 64,
        campaign_id="oracle-block-1-config-a",
        block_id="block-1",
        perf_observation=observation,
        run_cmd=run_cmd,
        leading_indicators=leading_indicators,
    )

    assert set(written) == artifacts.MEASUREMENT_MANIFEST_KEYS
    assert written["schema_version"] == artifacts.MEASUREMENT_MANIFEST_SCHEMA
    assert artifacts.load_measurement_manifest(
        output, run_cmd=run_cmd, leading_indicators=leading_indicators,
    ) == written
    assert artifacts.measurement_manifest_sha256(output) == hashlib.sha256(
        output.read_bytes()
    ).hexdigest()


def test_measurement_manifest_writer_is_create_only(tmp_path):
    observation, run_cmd, leading_indicators = _degraded_measurement_fixture()
    output = tmp_path / "measurement-manifest.json"
    output.write_bytes(b"existing-sidecar\n")

    with pytest.raises(FileExistsError):
        artifacts.write_measurement_manifest(
            output,
            oracle_manifest_sha256="a" * 64,
            campaign_id="oracle-block-1-config-a",
            block_id="block-1",
            perf_observation=observation,
            run_cmd=run_cmd,
            leading_indicators=leading_indicators,
        )

    assert output.read_bytes() == b"existing-sidecar\n"


def test_measurement_manifest_loader_rejects_extra_top_level_key(tmp_path):
    observation, run_cmd, leading_indicators = _degraded_measurement_fixture()
    document = {
        "schema_version": artifacts.MEASUREMENT_MANIFEST_SCHEMA,
        "oracle_manifest_sha256": "a" * 64,
        "campaign_id": "oracle-block-1-config-a",
        "block_id": "block-1",
        "perf_observation": observation,
        "unexpected": None,
    }

    with pytest.raises(artifacts.OracleArtifactTypeError, match="exact key"):
        artifacts.load_measurement_manifest(
            json.dumps(document).encode(),
            run_cmd=run_cmd,
            leading_indicators=leading_indicators,
        )


def test_measurement_manifest_loader_requires_shared_observation_validator():
    observation, run_cmd, leading_indicators = _degraded_measurement_fixture()
    observation["counter_status"] = "complete"
    document = {
        "schema_version": artifacts.MEASUREMENT_MANIFEST_SCHEMA,
        "oracle_manifest_sha256": "a" * 64,
        "campaign_id": "oracle-block-1-config-a",
        "block_id": "block-1",
        "perf_observation": observation,
    }

    with pytest.raises(artifacts.OracleArtifactTypeError, match="perf_observation"):
        artifacts.load_measurement_manifest(
            json.dumps(document).encode(),
            run_cmd=run_cmd,
            leading_indicators=leading_indicators,
        )


@pytest.mark.parametrize(
    ("field", "value", "message"),
    [
        ("schema_version", "unknown/v1", "schema_version"),
        ("oracle_manifest_sha256", "A" * 64, "lowercase hex"),
        ("campaign_id", "", "campaign_id"),
        ("block_id", None, "block_id"),
    ],
)
def test_measurement_manifest_loader_rejects_noncanonical_identity_fields(
    field, value, message,
):
    observation, run_cmd, leading_indicators = _degraded_measurement_fixture()
    document = {
        "schema_version": artifacts.MEASUREMENT_MANIFEST_SCHEMA,
        "oracle_manifest_sha256": "a" * 64,
        "campaign_id": "oracle-block-1-config-a",
        "block_id": "block-1",
        "perf_observation": observation,
    }
    document[field] = value

    with pytest.raises(artifacts.OracleArtifactTypeError, match=message):
        artifacts.load_measurement_manifest(
            json.dumps(document).encode(),
            run_cmd=run_cmd,
            leading_indicators=leading_indicators,
        )


def test_measurement_manifest_writer_rejects_absent_perf_observation_before_create(
    tmp_path,
):
    output = tmp_path / "measurement-manifest.json"

    with pytest.raises(artifacts.OracleArtifactTypeError, match="perf_observation"):
        artifacts.write_measurement_manifest(
            output,
            oracle_manifest_sha256="a" * 64,
            campaign_id="oracle-block-1-config-a",
            block_id="block-1",
            perf_observation=None,
            run_cmd=["./db_bench"],
            leading_indicators={"ipc": None, "llc_miss_rate": None},
        )

    assert not output.exists()


if __name__ == "__main__":
    sys.exit(pytest.main([__file__]))
