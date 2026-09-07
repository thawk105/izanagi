# -*- coding: utf-8 -*-
"""T-1998 fixed balanced stock-inline consumer tests."""
from __future__ import annotations

import hashlib
import json
import shlex
import sys
from dataclasses import dataclass, replace
from pathlib import Path

import pytest

_HERE = Path(__file__).resolve().parent
_REPO_ROOT = _HERE.parents[1]
sys.path.insert(0, str(_REPO_ROOT))

from orchestrator.campaign import (  # noqa: E402
    campaign_lock,
    env_contract,
    pipeline,
    t1998_stock_inline_pair as T,
    wal,
)
from orchestrator.campaign.build_admission import (  # noqa: E402
    GeneratorId,
    attest_generator_output,
    build_run_context,
    derive_build_admission,
)
from orchestrator.campaign.layout import CampaignLayout  # noqa: E402
from orchestrator.campaign.model import (  # noqa: E402
    COMMIT_CONTRACT_SHA256_KEY,
    Genome,
    STAGE_BENCH_DONE,
    STAGE_BUILD_DONE,
    STAGE_BUILD_START,
    STAGE_VERIFY_DONE,
)
from orchestrator.campaign.source_digest import (  # noqa: E402
    EMPTY_TRACKED_DIFF_SHA256,
    SOURCE_EVIDENCE_SCHEMA,
    SourceEvidence,
)
from orchestrator.tests import commit_receipt_support as receipt_support  # noqa: E402
from orchestrator.tests.campaign_lock_test_support import (  # noqa: E402
    build_v2_campaign_lock,
)


_SHORT_GITLINK = "511c953"
_FULL_GITLINK = _SHORT_GITLINK + "1" * 33
_SCRIPT_SHA = "9" * 64
_BASELINE_SOURCE_SHA = "1" * 64
_TARGET_SOURCE_SHA = "2" * 64
_TOOLCHAIN_SHA = "3" * 64
_PERF_SHA_BASE = "4" * 64
_PERF_SHA_TARGET = "5" * 64
_FLAGS = (
    {
        "NO_WAIT_LOCKING_IN_VALIDATION": 1,
        "NO_WAIT_OF_TICTOC": 0,
        "WAL": 0,
        "BACK_OFF": 0,
        "BACKOFF_FIXED": -1,
    },
    {
        "NO_WAIT_LOCKING_IN_VALIDATION": 1,
        "NO_WAIT_OF_TICTOC": 0,
        "WAL": 0,
        "BACK_OFF": 1,
        "BACKOFF_FIXED": -1,
    },
    *(
        {
            "NO_WAIT_LOCKING_IN_VALIDATION": 1,
            "NO_WAIT_OF_TICTOC": 0,
            "WAL": 0,
            "BACK_OFF": 1,
            "BACKOFF_FIXED": fixed,
        }
        for fixed in (2, 5, 10, 25, 50, 100)
    ),
)
_TOOLCHAIN = {
    "cc": {"realpath": "/usr/bin/cc", "version": "fixture-cc"},
    "cmake": {"realpath": "/usr/bin/cmake", "version": "fixture-cmake"},
    "cxx": {"realpath": "/usr/bin/c++", "version": "fixture-cxx"},
}


@dataclass(frozen=True)
class _Fixture:
    root: Path
    preregistered: T.T1998PreregisteredIdentity
    campaign: Path


def _canonical_json(value: object) -> str:
    return json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=True,
        allow_nan=False,
    )


def _campaign_id(lock_text: str) -> str:
    decoded = campaign_lock.decode_campaign_lock(lock_text)
    digest = hashlib.sha256(decoded.identity_preimage.encode("utf-8")).hexdigest()[:8]
    return f"backoff-sweep-{decoded.identity['search_tag']}-{digest}"


def _source_sha(canonical: str, ordinal: int) -> str:
    if canonical == T.BASELINE_CANONICAL_GENOME:
        return _BASELINE_SOURCE_SHA
    if canonical == T.TARGET_CANONICAL_GENOME:
        return _TARGET_SOURCE_SHA
    return f"{ordinal + 10:064x}"


def _write_producer(
    tmp_path: Path,
    *,
    short_gitlink: str = _SHORT_GITLINK,
    full_gitlink: str = _FULL_GITLINK,
    diagnostic_arm: str | None = None,
    diagnostic_genome_arm: str | None = None,
    trace_enabled_arm: str | None = None,
    unstable_arm: str | None = None,
    off_pair_diagnostic_ordinal: int | None = None,
    target_toolchain_sha: str = _TOOLCHAIN_SHA,
    off_grid_high: bool = False,
) -> _Fixture:
    root = tmp_path / "producer"
    campaigns = root / "campaigns"
    campaigns.mkdir(parents=True)
    context = build_run_context(generator_id=GeneratorId.BACKOFF_SWEEP)
    authorization = env_contract.authorize("linux-baremetal")
    lock_identity = {
        "ccbench_commit": short_gitlink,
        "search_config": {
            "records": 1_000_000,
            "threads": 48,
            "workload": "balanced",
            "build_admission": dict(context.policy.as_preimage()),
        },
        "search_tag": "silo-balanced-sweep",
        "spec_content": "T-1998 fixture",
        "trial": "unit",
    }
    lock_text = build_v2_campaign_lock(
        _canonical_json(lock_identity), authorization=authorization,
    )
    decoded = campaign_lock.decode_campaign_lock(lock_text)
    assert decoded.authority is not None
    campaign_id = _campaign_id(lock_text)
    campaign = campaigns / campaign_id
    layout = CampaignLayout(str(campaign)).ensure()
    Path(layout.lock_file).write_text(lock_text, encoding="utf-8")

    selected: dict[str, dict[str, object]] = {}
    for ordinal, flags in enumerate(_FLAGS):
        arm = (
            "baseline" if flags["BACK_OFF"] == 0
            else "target" if flags["BACKOFF_FIXED"] == 5
            else None
        )
        genome_flags = dict(flags)
        if (
            (arm is not None and arm == diagnostic_genome_arm)
            or ordinal == off_pair_diagnostic_ordinal
        ):
            genome_flags["BACKOFF_NOINLINE"] = 1
        genome = Genome("silo", genome_flags)
        canonical = genome.canonical()
        src_token = "stock" if ordinal == 0 else f"{ordinal:064x}"
        source_sha = _source_sha(canonical, ordinal)
        source = SourceEvidence(
            schema_version=SOURCE_EVIDENCE_SCHEMA,
            source_root=str(tmp_path.resolve()),
            ccbench_commit=short_gitlink,
            genome_sha256=hashlib.sha256(canonical.encode("utf-8")).hexdigest(),
            src_token=src_token,
            source_bytes_sha256=source_sha,
            tracked_clean=True,
            tracked_diff_sha256=EMPTY_TRACKED_DIFF_SHA256,
            tracked_paths=(),
        )
        generator_receipt = attest_generator_output(
            context,
            source,
            generator_input_sha256=hashlib.sha256(
                f"T-1998 fixture {ordinal}".encode("ascii")
            ).hexdigest(),
        )
        admission = derive_build_admission(
            context, source, generator_receipt=generator_receipt,
        )
        admission_receipt = admission.as_wal_receipt()
        variant = pipeline.variant_id(genome, src_token)
        attempt = f"attempt-{ordinal}"
        median = (
            100.0 if arm == "baseline"
            else 120.0 if arm == "target"
            else 999.0 if off_grid_high and flags["BACKOFF_FIXED"] == 2
            else 80.0 + ordinal
        )
        samples = [median - 2, median - 1, median, median + 1, median + 2]
        unstable = arm is not None and arm == unstable_arm
        build_dir = f"/fixture/build/{variant}/perf"
        configure = [
            "/usr/bin/cmake", "-S", "/fixture/ccbench", "-B", build_dir,
            *(f"-DCCBENCH_{key}={flags[key]}" for key in sorted(flags)),
            f"-DCCBENCH_TRACE={1 if arm is not None and arm == trace_enabled_arm else 0}",
        ]
        if (
            (arm is not None and arm == diagnostic_arm)
            or ordinal == off_pair_diagnostic_ordinal
        ):
            configure.append("-DCCBENCH_BACKOFF_NOINLINE=1")
        perf_sha = _PERF_SHA_BASE if arm == "baseline" else (
            _PERF_SHA_TARGET if arm == "target" else f"{ordinal + 30:064x}"
        )
        toolchain_sha = target_toolchain_sha if arm == "target" else _TOOLCHAIN_SHA
        terminal_common = {
            "build_attempt_id": attempt,
            "build_admission_receipt_sha256": admission_receipt["receipt_sha256"],
        }
        wal.log(layout, variant, STAGE_BUILD_START, authorization.contract.env_tag, {
            **terminal_common,
            "genome": canonical,
            "src_token": src_token,
            "build_admission": admission_receipt,
        }, ts=float(ordinal * 10 + 1))
        wal.log(layout, variant, STAGE_BUILD_DONE, authorization.contract.env_tag, {
            **terminal_common,
            "trace_bin_sha256": f"{ordinal + 50:064x}",
            "perf_bin_sha256": perf_sha,
            "perf_configure_cmd": shlex.join(configure),
            "toolchain": _TOOLCHAIN,
            "toolchain_record_sha256": toolchain_sha,
        }, ts=float(ordinal * 10 + 2))
        wal.log(layout, variant, STAGE_VERIFY_DONE, authorization.contract.env_tag, {
            "build_attempt_id": attempt,
            "verdict": "serializable",
            "certified": True,
            "anomalies": 0,
            "workload": {"tag": "balanced"},
        }, ts=float(ordinal * 10 + 3))
        wal.log(layout, variant, STAGE_BENCH_DONE, authorization.contract.env_tag, {
            "build_attempt_id": attempt,
            "tps": samples,
            "median_tps": median,
            "cv": 0.01,
            "unstable": unstable,
            "run_cmd": shlex.join([
                "numactl", "--interleave=all",
                f"{build_dir}/cc/silo/ycsb_silo.exe",
                "-thread_num=48", "-ycsb_rratio=50",
            ]),
        }, ts=float(ordinal * 10 + 4))
        commit_payload = {
            **terminal_common,
            "fitness_tps": median,
            "cv": 0.01,
            "unstable": unstable,
            "verify_configs": ["balanced"],
            COMMIT_CONTRACT_SHA256_KEY:
                decoded.authority.environment_contract_sha256,
        }
        receipt_support.log_receipted_commit(
            layout, variant, authorization.contract.env_tag, commit_payload,
            operation_identity=attempt, tags=("balanced",),
            ts=float(ordinal * 10 + 5),
        )
        if arm is not None:
            selected[arm] = {"samples": samples, "median": median}

    lock_sha = hashlib.sha256(Path(layout.lock_file).read_bytes()).hexdigest()
    wal_sha = hashlib.sha256(Path(layout.wal_file).read_bytes()).hexdigest()
    ratio = selected["target"]["median"] / selected["baseline"]["median"]
    result = {
        "schema_version": "a5-second-boot-result/v1",
        "status": "complete",
        "workload": "balanced",
        "target_fixed_us": 5,
        "no_backoff_median_tps": selected["baseline"]["median"],
        "target_median_tps": selected["target"]["median"],
        "no_backoff_tps": selected["baseline"]["samples"],
        "target_tps": selected["target"]["samples"],
        "ratio": ratio,
        "improvement_percent": (ratio - 1.0) * 100.0,
        "campaign_id": campaign_id,
        "wal_sha256": wal_sha,
        "lock_sha256": lock_sha,
        "pbs_jobid": "fixture.1",
        "hostname": "fixture-node",
        "fqdn": "fixture-node.example.invalid",
        "boot_id": "fixture-boot",
        "boot_epoch": 1,
        "repository_commit": decoded.authority.contract_loader_commit,
        "ccbench_commit": full_gitlink,
        "toolchain": _TOOLCHAIN,
        "perf_preflight": {"fixture": True},
        "perf_counter_statuses": ["available"],
    }
    (root / "result.json").write_text(
        _canonical_json(result) + "\n", encoding="utf-8",
    )
    reservation = {
        "schema_version": "a5-second-boot-reservation/v1",
        "binding": {
            "script_sha256": _SCRIPT_SHA,
            "job_id": "fixture.1",
            "nonce": "a" * 32,
        },
        "node_boot_evidence": {
            "hostname": "fixture-node",
            "fqdn": "fixture-node.example.invalid",
            "boot_id": "fixture-boot",
            "boot_epoch": 1,
            "pbs_jobid": "fixture.1",
        },
        "source_binding": {
            "repository_commit": decoded.authority.contract_loader_commit,
            "ccbench_gitlink_commit": full_gitlink,
        },
    }
    (root / "reservation.json").write_text(
        _canonical_json(reservation) + "\n", encoding="utf-8",
    )
    preregistered = T.T1998PreregisteredIdentity(
        common=T.T1998CommonPreregisteredIdentity(
            repository_commit=decoded.authority.contract_loader_commit,
            ccbench_gitlink_commit=full_gitlink,
            environment_contract_sha256=
                decoded.authority.environment_contract_sha256,
            launcher_script_sha256=_SCRIPT_SHA,
        ),
        baseline=T.T1998ArmPreregisteredIdentity(
            canonical_genome=T.BASELINE_CANONICAL_GENOME,
            source_bytes_sha256=_BASELINE_SOURCE_SHA,
        ),
        target=T.T1998ArmPreregisteredIdentity(
            canonical_genome=T.TARGET_CANONICAL_GENOME,
            source_bytes_sha256=_TARGET_SOURCE_SHA,
        ),
    )
    return _Fixture(root=root, preregistered=preregistered, campaign=campaign)


def _consume(fixture: _Fixture) -> T.T1998StockInlineDecision:
    return T.consume_balanced_stock_inline_pair(
        fixture.root, preregistered=fixture.preregistered,
    )


def _read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, value: object) -> None:
    path.write_text(_canonical_json(value) + "\n", encoding="utf-8")


def _refresh_result_wal_sha(fixture: _Fixture) -> None:
    result_path = fixture.root / "result.json"
    result = _read_json(result_path)
    result["wal_sha256"] = hashlib.sha256(
        (fixture.campaign / "runs/wal.jsonl").read_bytes()
    ).hexdigest()
    _write_json(result_path, result)


def test_real_admission_and_receipts_accept_only_the_fixed_pair(tmp_path: Path) -> None:
    fixture = _write_producer(tmp_path, off_grid_high=True)
    decision = _consume(fixture)

    assert decision.status == "accepted"
    assert decision.ratio == 1.2
    assert decision.baseline.median_tps == 100.0
    assert decision.target.median_tps == 120.0
    assert decision.baseline.commit_receipt_id
    assert decision.target.commit_receipt_id
    assert decision.identity.abbreviated_gitlink_is_full_identity is False
    assert decision.identity.submitter_identity_recoverable is False
    assert decision.identity.explicit_diagnostic_marker_check_is_sufficient is False


def test_baseline_and_target_source_identities_may_normally_differ(tmp_path: Path) -> None:
    fixture = _write_producer(tmp_path)
    assert fixture.preregistered.baseline.source_bytes_sha256 != (
        fixture.preregistered.target.source_bytes_sha256
    )
    assert _consume(fixture).status == "accepted"


def test_preregistered_source_digest_drift_is_rejected(tmp_path: Path) -> None:
    """The T-1998 source-identity gate alone rejects this target preregistration."""
    fixture = _write_producer(tmp_path)
    changed = replace(
        fixture.preregistered,
        target=replace(
            fixture.preregistered.target,
            source_bytes_sha256="f" * 64,
        ),
    )

    with pytest.raises(T.T1998PairRejected) as excinfo:
        T.consume_balanced_stock_inline_pair(fixture.root, preregistered=changed)
    assert excinfo.value.as_dict() == {
        "code": "source-identity-unbound",
        "field": "wal.build_start.build_admission.source.source_bytes_sha256",
        "expected": "f" * 64,
        "actual": _TARGET_SOURCE_SHA,
        "arm": "target",
    }


def test_sibling_failure_receipt_is_rejected(tmp_path: Path) -> None:
    """The T-1998 sibling-receipt gate alone rejects this producer root."""
    fixture = _write_producer(tmp_path)
    Path(str(fixture.root) + ".failure.json").write_text("{}\n", encoding="utf-8")

    with pytest.raises(T.T1998PairRejected) as excinfo:
        _consume(fixture)
    assert excinfo.value.code == "producer-failure-receipt"
    assert excinfo.value.arm == "baseline"


def test_short_gitlink_must_prefix_the_full_preregistration(tmp_path: Path) -> None:
    """The T-1998 abbreviated-gitlink gate alone rejects this coherent campaign."""
    fixture = _write_producer(
        tmp_path, short_gitlink="deadbee", full_gitlink=_FULL_GITLINK,
    )

    with pytest.raises(T.T1998PairRejected) as excinfo:
        _consume(fixture)
    assert excinfo.value.code == "gitlink-identity-mismatch"
    assert excinfo.value.field == "campaign.lock.ccbench_commit"


def test_launcher_script_digest_is_bound_to_preregistration(tmp_path: Path) -> None:
    """The T-1998 job-body digest gate alone rejects this changed expectation."""
    fixture = _write_producer(tmp_path)
    changed = replace(
        fixture.preregistered,
        common=replace(
            fixture.preregistered.common, launcher_script_sha256="e" * 64,
        ),
    )

    with pytest.raises(T.T1998PairRejected) as excinfo:
        T.consume_balanced_stock_inline_pair(fixture.root, preregistered=changed)
    assert excinfo.value.code == "launcher-script-identity-mismatch"
    assert excinfo.value.field == "reservation.binding.script_sha256"


@pytest.mark.parametrize("location", ["configure", "genome"])
def test_explicit_noinline_one_is_diagnostic_build(
    tmp_path: Path, location: str,
) -> None:
    """The T-1998 diagnostic marker gate alone rejects this one producer signal."""
    fixture = _write_producer(
        tmp_path,
        diagnostic_arm="target" if location == "configure" else None,
        diagnostic_genome_arm="target" if location == "genome" else None,
    )

    with pytest.raises(T.T1998PairRejected) as excinfo:
        _consume(fixture)
    assert excinfo.value.code == "diagnostic-build"
    assert excinfo.value.arm == "target"


def test_off_pair_diagnostic_build_does_not_taint_fixed_pair(tmp_path: Path) -> None:
    fixture = _write_producer(tmp_path, off_pair_diagnostic_ordinal=1)

    assert _consume(fixture).status == "accepted"


def test_trace_enabled_configure_is_not_performance_evidence(tmp_path: Path) -> None:
    """The T-1998 trace-disabled build gate alone rejects this configure record."""
    fixture = _write_producer(tmp_path, trace_enabled_arm="target")

    with pytest.raises(T.T1998PairRejected) as excinfo:
        _consume(fixture)
    assert excinfo.value.code == "performance-build-not-trace-disabled"
    assert excinfo.value.arm == "target"


@pytest.mark.parametrize("unstable_arm", ["baseline", "target"])
def test_unstable_arm_is_inconclusive(
    tmp_path: Path, unstable_arm: str,
) -> None:
    """The T-1998 stability layer alone makes a coherent unstable arm inconclusive."""
    fixture = _write_producer(tmp_path, unstable_arm=unstable_arm)
    decision = _consume(fixture)

    assert decision.status == "inconclusive"
    assert decision.reason == "unstable-arm"
    assert decision.ratio is None
    assert decision.improvement_percent is None


def test_toolchain_record_digest_drift_is_rejected(tmp_path: Path) -> None:
    """The T-1998 toolchain identity layer alone rejects the target digest drift."""
    fixture = _write_producer(tmp_path, target_toolchain_sha="d" * 64)

    with pytest.raises(T.T1998PairRejected) as excinfo:
        _consume(fixture)
    assert excinfo.value.code == "toolchain-identity-mismatch"
    assert excinfo.value.arm == "target"


def test_result_projection_drift_is_rejected(tmp_path: Path) -> None:
    """The T-1998 pair-value projection layer alone rejects this result field."""
    fixture = _write_producer(tmp_path)
    result_path = fixture.root / "result.json"
    result = _read_json(result_path)
    result["target_median_tps"] = 121.0
    _write_json(result_path, result)

    with pytest.raises(T.T1998PairRejected) as excinfo:
        _consume(fixture)
    assert excinfo.value.code == "pair-value-mismatch"
    assert excinfo.value.field == "result.target_median_tps"
    assert excinfo.value.arm == "target"


def test_invalid_persisted_receipt_is_rejected_by_real_admission(tmp_path: Path) -> None:
    """The real certified admission layer alone rejects this receipt mutation."""
    fixture = _write_producer(tmp_path)
    wal_path = fixture.campaign / "runs/wal.jsonl"
    records = [json.loads(line) for line in wal_path.read_text().splitlines()]
    commit = next(record for record in records if record["stage"] == "commit")
    commit["payload"]["commit_verification_receipt"]["receipt_id"] = "mutated"
    wal_path.write_text(
        "".join(_canonical_json(record) + "\n" for record in records),
        encoding="utf-8",
    )
    _refresh_result_wal_sha(fixture)

    with pytest.raises(T.T1998PairRejected) as excinfo:
        _consume(fixture)
    assert excinfo.value.code == "producer-rejected-variant"
    assert excinfo.value.field == "certified_campaign_admission"
    assert "ArtifactAdmissionError" in str(excinfo.value.actual)


def test_consumer_does_not_call_secondary_replay_admission() -> None:
    source = (_REPO_ROOT / "orchestrator/campaign/t1998_stock_inline_pair.py").read_text(
        encoding="utf-8",
    )
    assert "admit_replay_evidence" not in source
    assert "from .backoff_sweep" not in source
    assert "import backoff_sweep" not in source
    assert "argmax" not in source


def _run() -> int:
    return int(pytest.main(["-q", str(Path(__file__).resolve())]))


if __name__ == "__main__":
    raise SystemExit(_run())
