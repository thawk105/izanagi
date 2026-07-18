# -*- coding: utf-8 -*-
"""8b oracle report の manifest 限定・物理 trial 区間復元を検査する。"""
from __future__ import annotations

import copy
import hashlib
import json
import shutil
import sys
from pathlib import Path

import pytest

ORCH = Path(__file__).resolve().parents[1]
ROOT = ORCH.parent
sys.path.insert(0, str(ORCH))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import s8b_v2_freeze_fixture as v2_fixture  # noqa: E402
from campaign import (  # noqa: E402
    execution_guard,
    s8b_oracle_judge as judge,
    s8b_oracle_manifest as oracle_manifest,
    s8b_oracle_report as report,
    wal,
)
from campaign.layout import campaign_layout  # noqa: E402


# 注意: holdout の三軸 conjunction はテストへ静止させない。
# holdout ID と全 cell は freeze から実行時に組み立てる。
REAL_FREEZE = ROOT / "output/s8b-freeze/holdout_freeze.json"
CONFIGURATIONS = (
    "p2_2_flag_opt", "backoff_fixed_best", "sort_best",
    "system_gate", "ident_all", "stock_common",
)
SESSION = report.SESSION_STAGE
GENOME = "Silo|BACK_OFF=1"
SRC_TOKEN = "source-digest"
VARIANT = "same-variant"


def _canonical_sha256(value) -> str:
    encoded = json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _source(path: str) -> dict:
    source = ROOT / path
    return {"path": path, "sha256": hashlib.sha256(source.read_bytes()).hexdigest()}


def _freeze(tmp_path: Path) -> tuple[Path, tuple[str, ...]]:
    document = json.loads(REAL_FREEZE.read_text(encoding="utf-8"))
    holdout_ids = tuple(document["holdouts"])
    # strict v2: per-pair floor + budget を共有 fixture で充填する (C3-4)。
    v2_fixture.fill(document)
    path = tmp_path / "holdout-freeze-fixture.json"
    path.write_text(json.dumps(document, ensure_ascii=False), encoding="utf-8")
    return path, holdout_ids


def _binding(holdout_id: str, configuration_id: str) -> dict:
    projected = {
        "genome_canonical": GENOME,
        "src_token": SRC_TOKEN,
        "variant_id": VARIANT,
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


def _manifest(tmp_path: Path, *, campaign_id: str = "oracle-b0", n: int = 1) -> dict:
    freeze_path, holdout_ids = _freeze(tmp_path)
    schedule = oracle_manifest.build_schedule(
        n=n, master_seed="report-fixture", block_sizes={"b0": n},
        holdout_ids=holdout_ids, configuration_ids=CONFIGURATIONS,
    )
    return oracle_manifest.build_manifest(
        freeze_path=freeze_path,
        schedule=schedule,
        run_contract={
            "ccbench_pin": "pin", "env_tag": "fixture-env", "clocks": 1800,
            "reps": 2, "extime": 1, "verify": "legacy+s2",
            "screening": "off", "bench_max_rounds": 1,
            "contract_sha256": "0" * 64,
        },
        binding_identity=[
            _binding(holdout_id, configuration_id)
            for holdout_id in holdout_ids
            for configuration_id in CONFIGURATIONS
        ],
        campaign_ids={"b0": campaign_id},
        allowed_excluded_reasons=["machine-fault"],
        generator_versions={
            "materializer": _source("orchestrator/campaign/s1_direct_comparison.py"),
            "report": _source("orchestrator/campaign/s8b_oracle_report.py"),
            "judge": _source("orchestrator/campaign/s8b_oracle_judge.py"),
        },
    )


def _session(layout, event: str, payload: dict) -> None:
    wal.log(layout, "oracle-session", SESSION, "fixture-env", {"event": event, **payload})


def _campaign_start(layout, manifest: dict, campaign_id: str = "oracle-b0",
                    *, receipt: dict | None = None) -> None:
    payload = {
        "manifest_sha256": oracle_manifest.manifest_sha256(manifest),
        "block_id": "b0",
        "campaign_id": campaign_id,
        # C3-10: manifest run_contract の env_tag/contract_sha256 と一致する execution
        # receipt を既定で載せる (report が受理する形)。負例は receipt=<改竄> で注入。
        "execution_receipt": receipt if receipt is not None else {
            "schema": execution_guard.RECEIPT_SCHEMA,
            "env_tag": "fixture-env",
            "contract_sha256": "0" * 64,
            "attestation": {
                "hostname": "fixture-host", "boot_id": None,
                "cpuset": None, "captured_utc": "2026-07-18T00:00:00+00:00",
            },
        },
    }
    _session(layout, "campaign-start", payload)


def _verify(layout, variant: str, tag: str, certified: bool) -> None:
    wal.log(layout, variant, "verify_done", "fixture-env", {
        "verdict": "serializable" if certified else "cycle",
        "certified": certified,
        "workload": {"tag": tag},
    })


def _trial(layout, item: dict, outcome: str, *, variant: str = VARIANT,
           attempt: int = 1, tps: tuple[float, ...] = (10.0, 12.0),
           screen_marker: bool = False,
           excluded_reason: str | None = None) -> None:
    identity = {
        "schedule_index": item["schedule_index"],
        "holdout_id": item["holdout_id"],
        "configuration_id": item["configuration_id"],
        "attempt": attempt,
    }
    _session(layout, "trial-start", identity)
    wal.log(layout, variant, "build_start", "fixture-env", {
        "genome": GENOME, "src_token": SRC_TOKEN,
    })
    if outcome == "build-failed":
        wal.log(layout, variant, "abort", "fixture-env", {"reason": "build-error"})
    else:
        wal.log(layout, variant, "build_done", "fixture-env", {
            "trace_bin": "trace", "perf_bin": "perf",
        })
        if outcome == "binary-mismatch":
            # C3-5: build_done 後・verify/bench 起動前の TOCTOU abort。
            wal.log(layout, variant, "abort", "fixture-env", {
                "reason": "bench-binary-mismatch",
            })
        elif outcome == "legacy-red":
            _verify(layout, variant, "legacy", False)
            wal.log(layout, variant, "abort", "fixture-env", {
                "reason": "cycle", "workload": {"tag": "legacy"},
            })
        else:
            _verify(layout, variant, "legacy", True)
            if outcome in {"timeout", "verify-inconclusive"}:
                wal.log(layout, variant, "abort", "fixture-env", {
                    "reason": ("trace-timeout" if outcome == "timeout" else "trace-empty"),
                    "workload": {"tag": "s2"},
                })
            elif outcome == "s2-red":
                _verify(layout, variant, "s2", False)
                wal.log(layout, variant, "abort", "fixture-env", {
                    "reason": "cycle", "workload": {"tag": "s2"},
                })
            else:
                _verify(layout, variant, "s2", True)
                if outcome == "bench-failed":
                    wal.log(layout, variant, "abort", "fixture-env", {
                        "reason": "bench-no-throughput",
                    })
                else:
                    payload = {"tps": list(tps), "median_tps": sum(tps) / len(tps)}
                    if screen_marker:
                        payload["screening"] = True
                    wal.log(layout, variant, "bench_done", "fixture-env", payload)
                    wal.log(layout, variant, "commit", "fixture-env", {
                        "fitness_tps": sum(tps) / len(tps),
                        "verify_configs": ["legacy", "s2"],
                    })
    declared = {
        "legacy-red": "correctness-red",
        "s2-red": "correctness-red",
    }.get(outcome, outcome)
    _session(layout, "trial-result", {
        **identity,
        "outcome": declared,
        "excluded_reason": excluded_reason,
        "screen_outcome": "not_enabled",
    })


def _layout(tmp_path: Path, manifest: dict, campaign_id: str = "oracle-b0"):
    layout = campaign_layout(campaign_id, output_root=str(tmp_path)).ensure()
    _campaign_start(layout, manifest, campaign_id)
    return layout


def test_success_uses_real_manifest_and_binds_physical_trial_intervals(tmp_path):
    manifest = _manifest(tmp_path, n=2)
    schedule = manifest["schedule"]["rows"]
    layout = _layout(tmp_path, manifest)
    _trial(layout, schedule[0], "committed", tps=(10.0, 12.0))
    _trial(layout, schedule[1], "committed", tps=(20.0, 24.0))

    observations = report.build_observations(manifest=manifest, output_root=tmp_path)

    assert observations["schema_version"] == report.SCHEMA_VERSION
    assert [row["status"] for row in observations["rows"][:2]] == ["completed", "completed"]
    assert [row["bench_values"] for row in observations["rows"][:2]] == [
        [10.0, 12.0], [20.0, 24.0],
    ]
    assert all(row["binding_ok"] for row in observations["rows"][:2])
    assert len(observations["expected_cells"]) == len(schedule)


@pytest.mark.parametrize(
    ("case", "expected_outcome", "legacy", "s2"),
    [
        ("build-failed", "build-failed", "missing", "missing"),
        ("legacy-red", "correctness-red", "red", "missing"),
        ("s2-red", "correctness-red", "pass", "red"),
        ("timeout", "timeout", "pass", "missing"),
        ("verify-inconclusive", "verify-inconclusive", "pass", "missing"),
        ("bench-failed", "bench-failed", "pass", "pass"),
        ("binary-mismatch", "binary-mismatch", "missing", "missing"),
    ],
)
def test_failure_outcomes_remain_as_completed_observation_rows(
        tmp_path, case, expected_outcome, legacy, s2):
    manifest = _manifest(tmp_path)
    item = manifest["schedule"]["rows"][0]
    layout = _layout(tmp_path, manifest)
    _trial(layout, item, case)

    row = report.build_observations(manifest=manifest, output_root=tmp_path)["rows"][0]

    assert row["status"] == "completed"
    assert row["outcome"] == expected_outcome
    assert row["legacy_verify"] == legacy
    assert row["s2_verify"] == s2


def test_verify_inconclusive_wal_stays_observable_and_judges_indeterminate(tmp_path):
    manifest = _manifest(tmp_path)
    schedule = manifest["schedule"]["rows"]
    inconclusive_item = schedule[0]
    layout = _layout(tmp_path, manifest)
    for item in schedule:
        _trial(
            layout, item,
            "verify-inconclusive" if item is inconclusive_item else "committed",
        )

    observations = report.build_observations(manifest=manifest, output_root=tmp_path)
    row = observations["rows"][0]
    verdict = judge.judge_oracle(observations)

    assert row["status"] == "completed"
    assert row["outcome"] == "verify-inconclusive"
    assert row["legacy_verify"] == "pass"
    assert row["s2_verify"] == "missing"
    assert verdict["status"] == "indeterminate"
    cell = verdict["holdouts"][row["holdout_id"]]["configurations"][
        row["configuration_id"]
    ]
    assert cell["status"] == "unknown"


def test_binary_mismatch_wal_stays_observable_and_judges_indeterminate(tmp_path):
    """C3-5: binary-mismatch trial が report で observable outcome になり、judge の
    eligibility へ unknown 伝播する (cell=unknown / overall=indeterminate)。"""
    manifest = _manifest(tmp_path)
    schedule = manifest["schedule"]["rows"]
    mismatch_item = schedule[0]
    layout = _layout(tmp_path, manifest)
    for item in schedule:
        _trial(
            layout, item,
            "binary-mismatch" if item is mismatch_item else "committed",
        )

    observations = report.build_observations(manifest=manifest, output_root=tmp_path)
    row = observations["rows"][0]
    verdict = judge.judge_oracle(observations)

    assert row["status"] == "completed"
    assert row["outcome"] == "binary-mismatch"
    assert row["legacy_verify"] == "missing" and row["s2_verify"] == "missing"
    assert verdict["status"] == "indeterminate"
    cell = verdict["holdouts"][row["holdout_id"]]["configurations"][
        row["configuration_id"]
    ]
    assert cell["status"] == "unknown"


def test_receipt_mismatch_is_protocol_violation(tmp_path):
    """manifest run_contract (v2) が宣言する env_tag/contract_sha256 と campaign-start の
    execution_receipt が食い違えば全行 protocol_violation (report が receipt を照合する)。"""
    manifest = _manifest(tmp_path)
    schedule = manifest["schedule"]["rows"]
    layout = campaign_layout("oracle-b0", output_root=str(tmp_path)).ensure()
    # contract_sha256 が manifest と不一致な receipt を載せる。
    _campaign_start(layout, manifest, "oracle-b0", receipt={
        "schema": execution_guard.RECEIPT_SCHEMA,
        "env_tag": "fixture-env",
        "contract_sha256": "1" * 64,
        "attestation": {
            "hostname": "h", "boot_id": None, "cpuset": None,
            "captured_utc": "2026-07-18T00:00:00+00:00",
        },
    })
    for item in schedule:
        _trial(layout, item, "committed")

    observations = report.build_observations(manifest=manifest, output_root=tmp_path)
    assert all(row["status"] == "protocol_violation" for row in observations["rows"])
    assert any("execution_receipt" in (row.get("reason") or "")
               for row in observations["rows"])


@pytest.mark.parametrize("damage", ["missing", "partial"])
def test_missing_or_partial_expected_binding_is_protocol_violation(tmp_path, damage):
    manifest = _manifest(tmp_path)
    item = manifest["schedule"]["rows"][0]
    if damage == "missing":
        manifest["binding_identity"] = [
            entry for entry in manifest["binding_identity"]
            if (entry["holdout_id"], entry["configuration_id"])
            != (item["holdout_id"], item["configuration_id"])
        ]
    else:
        entry = next(entry for entry in manifest["binding_identity"]
                     if entry["holdout_id"] == item["holdout_id"]
                     and entry["configuration_id"] == item["configuration_id"])
        entry.pop("src_token")
    layout = _layout(tmp_path, manifest)
    _trial(layout, item, "committed")

    row = report.build_observations(manifest=manifest, output_root=tmp_path)["rows"][0]

    assert row["binding_ok"] is False
    assert row["status"] == "protocol_violation"
    assert "binding" in row["reason"]


def test_definitive_red_survives_later_committed_retry(tmp_path):
    manifest = _manifest(tmp_path)
    item = manifest["schedule"]["rows"][0]
    layout = _layout(tmp_path, manifest)
    _trial(layout, item, "legacy-red", attempt=1)
    _session(layout, "retry", {
        "schedule_index": item["schedule_index"], "attempt": 2,
        "reason": "transient retry",
    })
    _trial(layout, item, "committed", attempt=2, tps=(1000.0, 1002.0))

    row = report.build_observations(manifest=manifest, output_root=tmp_path)["rows"][0]

    assert row["status"] == "completed"
    assert row["outcome"] == "correctness-red"
    assert row["legacy_verify"] == "red"
    assert [attempt["outcome"] for attempt in row["attempt_verify_outcomes"]] == [
        "correctness-red", "committed",
    ]


@pytest.mark.parametrize("phantom_outcome", ["legacy-red", "committed"])
def test_trial_window_with_phantom_schedule_index_is_protocol_violation(
        tmp_path, phantom_outcome):
    manifest = _manifest(tmp_path)
    schedule = manifest["schedule"]["rows"]
    layout = _layout(tmp_path, manifest)
    phantom = dict(schedule[0], schedule_index=len(schedule) + 100)
    _trial(layout, phantom, phantom_outcome)
    for item in schedule:
        _trial(layout, item, "committed")

    observations = report.build_observations(manifest=manifest, output_root=tmp_path)

    assert all(row["status"] == "protocol_violation"
               for row in observations["rows"])
    assert "schedule 外" in observations["rows"][0]["reason"]
    assert judge.judge_oracle(observations)["status"] == "indeterminate"


def test_allowed_excluded_reason_row_stays_reported_and_judges_unknown(tmp_path):
    manifest = _manifest(tmp_path)
    schedule = manifest["schedule"]["rows"]
    excluded_item = schedule[0]
    layout = _layout(tmp_path, manifest)
    for item in schedule:
        if item is excluded_item:
            _trial(layout, item, "timeout", excluded_reason="machine-fault")
        else:
            _trial(layout, item, "committed")

    observations = report.build_observations(manifest=manifest, output_root=tmp_path)
    row = observations["rows"][0]
    verdict = judge.judge_oracle(observations)

    assert row["status"] == "completed"
    assert row["outcome"] == "timeout"
    assert row["excluded_reason"] == "machine-fault"
    assert verdict["status"] == "indeterminate"
    cell = verdict["holdouts"][row["holdout_id"]]["configurations"][
        row["configuration_id"]
    ]
    assert cell["status"] == "unknown"
    assert any(reason["code"] == "excluded" for reason in cell["reasons"])


def test_excluded_reason_outside_allowed_list_is_protocol_violation(tmp_path):
    manifest = _manifest(tmp_path)
    item = manifest["schedule"]["rows"][0]
    layout = _layout(tmp_path, manifest)
    _trial(layout, item, "timeout", excluded_reason="power-outage")

    row = report.build_observations(manifest=manifest, output_root=tmp_path)["rows"][0]

    assert row["status"] == "protocol_violation"
    assert "許可一覧外" in row["reason"]


def test_correctness_red_with_excluded_reason_is_protocol_violation(tmp_path):
    manifest = _manifest(tmp_path)
    item = manifest["schedule"]["rows"][0]
    layout = _layout(tmp_path, manifest)
    _trial(layout, item, "legacy-red", excluded_reason="machine-fault")

    row = report.build_observations(manifest=manifest, output_root=tmp_path)["rows"][0]

    assert row["status"] == "protocol_violation"
    assert "correctness-red に excluded_reason" in row["reason"]


def test_manifest_hash_is_recomputed_independently_after_tampering(tmp_path):
    manifest = _manifest(tmp_path)
    item = manifest["schedule"]["rows"][0]
    layout = _layout(tmp_path, manifest)
    _trial(layout, item, "committed")
    tampered = copy.deepcopy(manifest)
    tampered["allowed_excluded_reasons"].append("tampered")
    tampered["manifest_sha256"] = oracle_manifest.manifest_sha256(manifest)

    row = report.build_observations(manifest=tampered, output_root=tmp_path)["rows"][0]

    assert row["status"] == "protocol_violation"
    assert "manifest_sha256" in row["reason"]


def test_expected_cells_keep_deleted_holdout_indeterminate(tmp_path):
    manifest = _manifest(tmp_path)
    layout = _layout(tmp_path, manifest)
    for item in manifest["schedule"]["rows"]:
        _trial(layout, item, "committed")
    observations = report.build_observations(manifest=manifest, output_root=tmp_path)
    assert judge.judge_oracle(observations)["status"] == "determinate"
    holdouts = {entry["holdout_id"] for entry in observations["expected_cells"]}
    removed = next(iter(holdouts))
    observations["rows"] = [
        row for row in observations["rows"] if row["holdout_id"] != removed
    ]

    assert removed in {entry["holdout_id"] for entry in observations["expected_cells"]}
    assert judge.judge_oracle(observations)["status"] == "indeterminate"


def test_schedule_row_without_trial_start_is_not_started_with_reason(tmp_path):
    manifest = _manifest(tmp_path)
    item = manifest["schedule"]["rows"][0]
    layout = _layout(tmp_path, manifest)
    _session(layout, "budget-refused", {
        "schedule_index": item["schedule_index"], "reason": "budget exhausted",
    })

    row = report.build_observations(manifest=manifest, output_root=tmp_path)["rows"][0]

    assert row["status"] == "not-started"
    assert row["outcome"] is None
    assert "budget-refused" in row["reason"]


def test_screen_marker_is_protocol_violation(tmp_path):
    manifest = _manifest(tmp_path)
    item = manifest["schedule"]["rows"][0]
    layout = _layout(tmp_path, manifest)
    _trial(layout, item, "committed", screen_marker=True)

    row = report.build_observations(manifest=manifest, output_root=tmp_path)["rows"][0]

    assert row["status"] == "protocol_violation"
    assert "screen marker" in row["reason"]


def test_only_manifest_campaign_is_read_and_missing_owned_campaign_is_reported(tmp_path):
    manifest = _manifest(tmp_path)
    item = manifest["schedule"]["rows"][0]
    owned = _layout(tmp_path, manifest)
    _trial(owned, item, "committed", tps=(7.0, 9.0))
    external = _layout(tmp_path, manifest, "outside-manifest")
    _trial(external, item, "committed", tps=(9000.0, 9002.0))
    rows = report.build_observations(manifest=manifest, output_root=tmp_path)["rows"]
    assert rows[0]["bench_values"] == [7.0, 9.0]

    shutil.rmtree(Path(owned.root))
    missing = report.build_observations(manifest=manifest, output_root=tmp_path)["rows"][0]
    assert missing["status"] == "missing-campaign"
    assert missing["reason"]
