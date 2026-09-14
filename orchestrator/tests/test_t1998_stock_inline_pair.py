# -*- coding: utf-8 -*-
"""T-1998 fixed balanced stock-inline consumer tests."""
from __future__ import annotations

import hashlib
import json
import shlex
import subprocess
import sys
from dataclasses import dataclass, replace
from functools import lru_cache
from pathlib import Path

import pytest

_HERE = Path(__file__).resolve().parent
_REPO_ROOT = _HERE.parents[1]
sys.path.insert(0, str(_REPO_ROOT))

from orchestrator.campaign import (  # noqa: E402
    campaign_lock,
    contract_loader_binding,
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
_FULL_GITLINK = "511c9538e4e8efa54b45cda62e72389ed3b706ec"
_SCRIPT_SHA = "dff913cb1044858b56f25721f2d0aac6539bbcf2a7ddb63b9e6b4bbcac7aecd8"
_BASELINE_SOURCE_SHA = (
    "2d691b45afd02a7979b1872eeb0a5c5c58223550892331b31641599aa239a2c6"
)
_TARGET_SOURCE_SHA = (
    "678b7203aa1f9fdca4c35f9b3219d0b9662b60b22331484027adfc6c34580b12"
)
_REPOSITORY_COMMIT = subprocess.run(
    ["git", "-C", str(_REPO_ROOT), "rev-parse", "HEAD"],
    check=True,
    capture_output=True,
    text=True,
).stdout.strip()
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
    role: {
        "requested": requested,
        "realpath": f"/usr/bin/{requested}",
        "version_first_line": f"fixture-{role}",
    }
    for role, requested in (("cc", "cc"), ("cmake", "cmake"), ("cxx", "c++"))
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


_TOOLCHAIN_SHA = hashlib.sha256(
    _canonical_json({
        role: {**entry, "version": f"{entry['version_first_line']}\nFull version details"}
        for role, entry in _TOOLCHAIN.items()
    }).encode("utf-8")
).hexdigest()


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


def _git_bytes(*args: str, repo_root: Path = _REPO_ROOT) -> bytes:
    return subprocess.run(
        ["git", "-C", str(repo_root), *args],
        check=True,
        capture_output=True,
    ).stdout


@lru_cache(maxsize=None)
def _contract_loader_binding(
    repository_commit: str,
    repo_root: Path = _REPO_ROOT,
) -> contract_loader_binding.ContractLoaderBinding:
    blob_sha256s = {
        relative: hashlib.sha256(
            _git_bytes(
                "show",
                f"{repository_commit}:{relative}",
                repo_root=repo_root,
            )
        ).hexdigest()
        for relative in contract_loader_binding.CONTRACT_LOADER_RELATIVE_PATHS
    }
    return contract_loader_binding.ContractLoaderBinding(
        contract_loader_commit=repository_commit,
        contract_loader_blob_sha256s=blob_sha256s,
    )


def _write_producer(
    tmp_path: Path,
    *,
    env_tag: str = "pegasus",
    short_gitlink: str = _SHORT_GITLINK,
    full_gitlink: str = _FULL_GITLINK,
    diagnostic_arm: str | None = None,
    typed_diagnostic_arm: str | None = None,
    diagnostic_genome_arm: str | None = None,
    diagnostic_genome_value: int = 1,
    trace_enabled_arm: str | None = None,
    typed_trace_arm: str | None = None,
    unstable_arm: str | None = None,
    off_pair_diagnostic_ordinal: int | None = None,
    target_toolchain_sha: str = _TOOLCHAIN_SHA,
    off_grid_high: bool = False,
    omit_perf_build_arm: str | None = None,
    mismatched_perf_build_arm: str | None = None,
    decoy_bench_executable: str | None = None,
    verify_env_mismatch_arm: str | None = None,
    orphan_record: str | None = None,
    repository_commit: str = _REPOSITORY_COMMIT,
    repository_root: Path = _REPO_ROOT,
) -> _Fixture:
    root = tmp_path / "producer"
    campaigns = root / "campaigns"
    campaigns.mkdir(parents=True)
    context = build_run_context(generator_id=GeneratorId.BACKOFF_SWEEP)
    authorization = env_contract.authorize(env_tag)
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
        _canonical_json(lock_identity),
        authorization=authorization,
        binding=_contract_loader_binding(repository_commit, repository_root),
    )
    decoded = campaign_lock.decode_campaign_lock(lock_text)
    assert decoded.authority is not None
    assert decoded.authority.contract_loader_commit == repository_commit
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
            genome_flags["BACKOFF_NOINLINE"] = diagnostic_genome_value
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
        ]
        trace_value = 1 if arm is not None and arm == trace_enabled_arm else 0
        trace_type = ":BOOL" if arm is not None and arm == typed_trace_arm else ""
        configure.append(f"-DCCBENCH_TRACE{trace_type}={trace_value}")
        if (
            (arm is not None and arm == diagnostic_arm)
            or ordinal == off_pair_diagnostic_ordinal
        ):
            configure.append("-DCCBENCH_BACKOFF_NOINLINE=1")
        if arm is not None and arm == typed_diagnostic_arm:
            configure.append("-DCCBENCH_BACKOFF_NOINLINE:STRING=1")
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
        build_done_payload = {
            **terminal_common,
            "trace_bin_sha256": f"{ordinal + 50:064x}",
            "perf_bin_sha256": perf_sha,
            "perf_configure_cmd": shlex.join(configure),
            "toolchain": _TOOLCHAIN,
            "toolchain_record_sha256": toolchain_sha,
        }
        if ordinal == 1 and orphan_record == "build-anomaly":
            build_done_payload["anomalies"] = 1
        if arm != omit_perf_build_arm:
            built_dir = (
                f"{build_dir}-mismatch"
                if arm is not None and arm == mismatched_perf_build_arm
                else build_dir
            )
            build_done_payload["perf_build_cmd"] = shlex.join([
                "/usr/bin/cmake", "--build", built_dir,
            ])
        wal.log(
            layout, variant, STAGE_BUILD_DONE, authorization.contract.env_tag,
            build_done_payload, ts=float(ordinal * 10 + 2),
        )
        verify_env_tag = (
            "fixture-mismatched-env"
            if arm is not None and arm == verify_env_mismatch_arm
            else authorization.contract.env_tag
        )
        wal.log(layout, variant, STAGE_VERIFY_DONE, verify_env_tag, {
            "build_attempt_id": attempt,
            "verdict": "serializable",
            "certified": True,
            "anomalies": 0,
            "workload": {"tag": "balanced"},
        }, ts=float(ordinal * 10 + 3))
        if ordinal == 1 and orphan_record in {
            "verify-anomaly", "verify-nonserializable", "verify-clean",
        }:
            wal.log(layout, variant, STAGE_VERIFY_DONE, authorization.contract.env_tag, {
                "verdict": (
                    "not-serializable"
                    if orphan_record == "verify-nonserializable"
                    else "serializable"
                ),
                "certified": True,
                "anomalies": 1 if orphan_record == "verify-anomaly" else 0,
                "workload": {"tag": "balanced"},
            }, ts=float(ordinal * 10 + 3.5))
        run_cmd = [
            *authorization.contract.numactl,
            f"{build_dir}/cc/silo/ycsb_silo.exe",
            "-thread_num=48", "-ycsb_rratio=50",
        ]
        if arm == "target" and decoy_bench_executable is not None:
            run_cmd = [decoy_bench_executable, f"{build_dir}/cc/silo/ycsb_silo.exe"]
        wal.log(layout, variant, STAGE_BENCH_DONE, authorization.contract.env_tag, {
            "build_attempt_id": attempt,
            "tps": samples,
            "median_tps": median,
            "cv": 0.01,
            "unstable": unstable,
            "run_cmd": shlex.join(run_cmd),
        }, ts=float(ordinal * 10 + 4))
        if ordinal == 1 and orphan_record == "bench":
            wal.log(layout, variant, STAGE_BENCH_DONE, authorization.contract.env_tag, {
                "tps": samples,
                "median_tps": median,
                "cv": 0.01,
                "unstable": False,
                "run_cmd": shlex.join(run_cmd),
            }, ts=float(ordinal * 10 + 4.5))
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


def _temporary_preregistration_repo(
    tmp_path: Path,
    *,
    committed_drift: bool = False,
    committed_missing: bool = False,
    worktree_drift: bool = False,
) -> tuple[Path, str]:
    repo = tmp_path / "prereg-repo"
    document = repo / T.T1998_PREREGISTRATION_PATH
    subprocess.run(["git", "init", str(repo)], check=True, capture_output=True)
    canonical_document = (
        _REPO_ROOT / T.T1998_PREREGISTRATION_PATH
    ).read_bytes()
    drifted_document = canonical_document + b"\n"
    document.parent.mkdir(parents=True)
    if not committed_missing:
        document.write_bytes(
            drifted_document if committed_drift else canonical_document
        )
    for relative in contract_loader_binding.CONTRACT_LOADER_RELATIVE_PATHS:
        destination = repo / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes((_REPO_ROOT / relative).read_bytes())
    subprocess.run(
        [
            "git", "-C", str(repo), "add", "--",
            *([] if committed_missing else [T.T1998_PREREGISTRATION_PATH]),
            *contract_loader_binding.CONTRACT_LOADER_RELATIVE_PATHS,
        ],
        check=True,
        capture_output=True,
    )
    subprocess.run(
        [
            "git", "-C", str(repo),
            "-c", "user.name=T-1998 fixture",
            "-c", "user.email=t1998@example.invalid",
            "commit", "-m", "fixture preregistration",
        ],
        check=True,
        capture_output=True,
    )
    commit = subprocess.run(
        ["git", "-C", str(repo), "rev-parse", "HEAD"],
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    document.write_bytes(
        drifted_document if worktree_drift else canonical_document
    )
    return repo, commit


def _preregistration_repo_with_blob_drift(tmp_path: Path) -> tuple[Path, str]:
    return _temporary_preregistration_repo(tmp_path, committed_drift=True)


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


def test_bench_execution_target_requires_exact_nonempty_prefix() -> None:
    prefix = ("numactl", "--interleave=all")
    executable = "/build/cc/silo/ycsb_silo.exe"

    assert T._bench_execution_target([*prefix, executable, "--help"], prefix) == executable
    assert T._bench_execution_target(
        ["numactl", "--interleave=0", executable], prefix,
    ) is None
    assert T._bench_execution_target([executable, "--help"], prefix) is None


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


def test_baseline_source_digest_drift_is_rejected(tmp_path: Path) -> None:
    """The baseline source-identity comparison alone owns this rejection."""
    fixture = _write_producer(tmp_path)
    changed = replace(
        fixture.preregistered,
        baseline=replace(
            fixture.preregistered.baseline,
            source_bytes_sha256="f" * 64,
        ),
    )

    with pytest.raises(T.T1998PairRejected) as excinfo:
        T.consume_balanced_stock_inline_pair(fixture.root, preregistered=changed)
    assert excinfo.value.as_dict() == {
        "code": "source-identity-unbound",
        "field": "wal.build_start.build_admission.source.source_bytes_sha256",
        "expected": "f" * 64,
        "actual": _BASELINE_SOURCE_SHA,
        "arm": "baseline",
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


def test_old_job_body_digest_is_rejected_from_reservation(tmp_path: Path) -> None:
    """The artifact-side launcher binding alone rejects the historical digest."""
    fixture = _write_producer(tmp_path)
    reservation_path = fixture.root / "reservation.json"
    reservation = _read_json(reservation_path)
    old_digest = "0ef4d41ee1ddf8ecd7a86a32a3b9dbaf128279125ef4820c54421973ee281d84"
    reservation["binding"]["script_sha256"] = old_digest
    _write_json(reservation_path, reservation)

    with pytest.raises(T.T1998PairRejected) as excinfo:
        _consume(fixture)
    assert excinfo.value.as_dict() == {
        "code": "launcher-script-identity-mismatch",
        "field": "reservation.binding.script_sha256",
        "expected": _SCRIPT_SHA,
        "actual": old_digest,
        "arm": "baseline",
    }


def test_document_identity_mismatch_is_rejected_after_artifact_checks(
    tmp_path: Path,
) -> None:
    """The document-identity gate alone rejects a coherent alternate gitlink."""
    alternate_short = "deadbee"
    alternate_full = alternate_short + "1" * 33
    fixture = _write_producer(
        tmp_path,
        short_gitlink=alternate_short,
        full_gitlink=alternate_full,
    )

    with pytest.raises(T.T1998PairRejected) as excinfo:
        _consume(fixture)
    assert excinfo.value.as_dict() == {
        "code": "preregistration-identity-mismatch",
        "field": "preregistered.common.ccbench_gitlink_commit",
        "expected": _FULL_GITLINK,
        "actual": alternate_full,
        "arm": "unknown",
    }


def test_current_preregistration_sha_mismatch_is_rejected(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The current-document SHA gate alone rejects worktree byte drift."""
    repo, repository_commit = _temporary_preregistration_repo(
        tmp_path,
        worktree_drift=True,
    )
    monkeypatch.setattr(contract_loader_binding, "_REPO_ROOT", repo)
    fixture = _write_producer(
        tmp_path,
        repository_commit=repository_commit,
        repository_root=repo,
    )

    with pytest.raises(T.T1998PairRejected) as excinfo:
        T.consume_balanced_stock_inline_pair(
            fixture.root,
            preregistered=fixture.preregistered,
            repo_root=repo,
        )
    assert excinfo.value.as_dict() == {
        "code": "current-preregistration-sha-mismatch",
        "field": "preregistration.current.sha256",
        "expected": T.CURRENT_PREREGISTRATION_SHA256,
        "actual": hashlib.sha256(
            (repo / T.T1998_PREREGISTRATION_PATH).read_bytes()
        ).hexdigest(),
        "arm": "unknown",
    }


def test_measurement_preregistration_sha_mismatch_is_rejected(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The measurement SHA gate alone rejects a present, changed blob."""
    repo, repository_commit = _temporary_preregistration_repo(
        tmp_path,
        committed_drift=True,
    )
    monkeypatch.setattr(contract_loader_binding, "_REPO_ROOT", repo)
    fixture = _write_producer(
        tmp_path,
        repository_commit=repository_commit,
        repository_root=repo,
    )

    with pytest.raises(T.T1998PairRejected) as excinfo:
        T.consume_balanced_stock_inline_pair(
            fixture.root,
            preregistered=fixture.preregistered,
            repo_root=repo,
        )
    assert excinfo.value.as_dict() == {
        "code": "measurement-preregistration-sha-mismatch",
        "field": "preregistration.measurement.sha256",
        "expected": T.MEASUREMENT_TIME_PREREGISTRATION_SHA256,
        "actual": hashlib.sha256(
            _git_bytes(
                "show",
                f"{repository_commit}:{T.T1998_PREREGISTRATION_PATH}",
                repo_root=repo,
            )
        ).hexdigest(),
        "arm": "unknown",
    }


def test_measurement_commit_without_preregistration_blob_is_rejected(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The measurement-time document pin alone rejects a missing commit blob."""
    repo, repository_commit = _temporary_preregistration_repo(
        tmp_path,
        committed_missing=True,
    )
    monkeypatch.setattr(contract_loader_binding, "_REPO_ROOT", repo)
    fixture = _write_producer(
        tmp_path,
        repository_commit=repository_commit,
        repository_root=repo,
    )

    with pytest.raises(T.T1998PairRejected) as excinfo:
        T.consume_balanced_stock_inline_pair(
            fixture.root,
            preregistered=fixture.preregistered,
            repo_root=repo,
        )
    assert excinfo.value.code == "measurement-preregistration-sha-mismatch"
    assert excinfo.value.field == "preregistration.measurement.sha256"
    assert excinfo.value.arm == "unknown"


def test_parse_preregistration_rejects_duplicate_key() -> None:
    """The strict parser alone rejects a duplicate machine-spec key."""
    raw = (_REPO_ROOT / T.T1998_PREREGISTRATION_PATH).read_bytes()
    matching_lines = [
        line for line in raw.splitlines(keepends=True)
        if b'"ccbench_gitlink_commit"' in line
    ]
    assert len(matching_lines) == 1
    key_line = matching_lines[0]

    with pytest.raises(ValueError, match="duplicate JSON key"):
        T._parse_preregistration(raw.replace(key_line, key_line * 2, 1))


def test_load_preregistration_rejects_worktree_blob_mismatch(
    tmp_path: Path,
) -> None:
    """The loader's byte equality gate alone rejects this real Git repository."""
    repo, prereg_commit = _preregistration_repo_with_blob_drift(tmp_path)

    with pytest.raises(
        ValueError,
        match="working preregistration bytes differ from commit blob",
    ):
        T.load_preregistration(repo, prereg_commit)


def test_load_preregistration_returns_document_identity_from_real_head() -> None:
    identity = T.load_preregistration(_REPO_ROOT, _REPOSITORY_COMMIT)

    assert identity == T.T1998PreregisteredIdentity(
        common=T.T1998CommonPreregisteredIdentity(
            repository_commit=_REPOSITORY_COMMIT,
            ccbench_gitlink_commit=_FULL_GITLINK,
            environment_contract_sha256=(
                "e576e9cd1369bba3ae8faca084d1b7256bf919a7dd2e5d6facb093cd9e242c01"
            ),
            launcher_script_sha256=_SCRIPT_SHA,
        ),
        baseline=T.T1998ArmPreregisteredIdentity(
            canonical_genome=(
                "silo|BACKOFF_FIXED=-1,BACK_OFF=0,"
                "NO_WAIT_LOCKING_IN_VALIDATION=1,NO_WAIT_OF_TICTOC=0,WAL=0"
            ),
            source_bytes_sha256=_BASELINE_SOURCE_SHA,
        ),
        target=T.T1998ArmPreregisteredIdentity(
            canonical_genome=(
                "silo|BACKOFF_FIXED=5,BACK_OFF=1,"
                "NO_WAIT_LOCKING_IN_VALIDATION=1,NO_WAIT_OF_TICTOC=0,WAL=0"
            ),
            source_bytes_sha256=_TARGET_SOURCE_SHA,
        ),
    )


@pytest.mark.parametrize("location", ["configure", "typed-configure", "genome"])
def test_explicit_noinline_one_is_diagnostic_build(
    tmp_path: Path, location: str,
) -> None:
    """The T-1998 diagnostic marker gate alone rejects this one producer signal."""
    fixture = _write_producer(
        tmp_path,
        diagnostic_arm="target" if location == "configure" else None,
        typed_diagnostic_arm="target" if location == "typed-configure" else None,
        diagnostic_genome_arm="target" if location == "genome" else None,
    )

    with pytest.raises(T.T1998PairRejected) as excinfo:
        _consume(fixture)
    assert excinfo.value.code == "diagnostic-build"
    assert excinfo.value.arm == "target"


def test_off_pair_diagnostic_build_is_rejected(tmp_path: Path) -> None:
    """The all-genome producer-shape layer alone rejects this off-pair key."""
    fixture = _write_producer(tmp_path, off_pair_diagnostic_ordinal=1)

    with pytest.raises(T.T1998PairRejected) as excinfo:
        _consume(fixture)
    assert excinfo.value.code == "diagnostic-build"
    assert excinfo.value.field == "wal.build_start.genome.BACKOFF_NOINLINE"
    assert excinfo.value.arm == "unknown"


def test_off_pair_diagnostic_key_value_is_not_interpreted(tmp_path: Path) -> None:
    """The all-genome producer-shape layer alone rejects a zero-valued key."""
    fixture = _write_producer(
        tmp_path, off_pair_diagnostic_ordinal=1, diagnostic_genome_value=0,
    )

    with pytest.raises(T.T1998PairRejected) as excinfo:
        _consume(fixture)
    assert excinfo.value.code == "diagnostic-build"
    assert excinfo.value.arm == "unknown"


def test_trace_enabled_configure_is_not_performance_evidence(tmp_path: Path) -> None:
    """The T-1998 trace-disabled build gate alone rejects this configure record."""
    fixture = _write_producer(tmp_path, trace_enabled_arm="target")

    with pytest.raises(T.T1998PairRejected) as excinfo:
        _consume(fixture)
    assert excinfo.value.code == "performance-build-not-trace-disabled"
    assert excinfo.value.arm == "target"


def test_typed_trace_disabled_define_is_normalized(tmp_path: Path) -> None:
    fixture = _write_producer(tmp_path, typed_trace_arm="target")

    assert _consume(fixture).status == "accepted"


@pytest.mark.parametrize("decoy", ["/bin/true", "/bin/echo"])
def test_decoy_bench_binary_token_is_rejected(tmp_path: Path, decoy: str) -> None:
    """The executable-position layer alone rejects the review's decoy command."""
    fixture = _write_producer(tmp_path, decoy_bench_executable=decoy)

    with pytest.raises(T.T1998PairRejected) as excinfo:
        _consume(fixture)
    assert excinfo.value.code == "performance-build-not-trace-disabled"
    assert excinfo.value.field == "wal.bench_done.run_cmd.executable"
    assert excinfo.value.arm == "target"


def test_missing_perf_build_command_is_rejected(tmp_path: Path) -> None:
    """The performance-build receipt layer alone rejects a missing build command."""
    fixture = _write_producer(tmp_path, omit_perf_build_arm="target")

    with pytest.raises(T.T1998PairRejected) as excinfo:
        _consume(fixture)
    assert excinfo.value.code == "performance-build-not-trace-disabled"
    assert excinfo.value.field == "wal.build_done.perf_build_cmd.--build"
    assert excinfo.value.arm == "target"


def test_perf_build_directory_must_match_configure(tmp_path: Path) -> None:
    """The configure/build directory layer alone rejects this directory drift."""
    fixture = _write_producer(tmp_path, mismatched_perf_build_arm="target")

    with pytest.raises(T.T1998PairRejected) as excinfo:
        _consume(fixture)
    assert excinfo.value.code == "performance-build-not-trace-disabled"
    assert excinfo.value.field == "wal.build_done.perf_build_cmd.--build"
    assert excinfo.value.arm == "target"


def test_verify_environment_tag_drift_is_rejected(tmp_path: Path) -> None:
    """The fixed-arm environment layer alone rejects verify_done env-tag drift."""
    fixture = _write_producer(tmp_path, verify_env_mismatch_arm="target")

    with pytest.raises(T.T1998PairRejected) as excinfo:
        _consume(fixture)
    assert excinfo.value.code == "environment-identity-mismatch"
    assert excinfo.value.field == "wal.env_tag"
    assert excinfo.value.arm == "target"


@pytest.mark.parametrize(
    ("orphan_record", "field"),
    [
        ("verify-anomaly", "wal.verify_done.anomalies"),
        ("verify-nonserializable", "wal.verify_done.verdict"),
        ("verify-clean", "wal.verify_done.build_attempt_id"),
        ("bench", "wal.bench_done.build_attempt_id"),
        ("build-anomaly", "wal.build_done.anomalies"),
    ],
)
def test_all_verify_and_bench_records_are_fail_closed(
    tmp_path: Path, orphan_record: str, field: str,
) -> None:
    """The all-record discipline-2 layer alone rejects this orphan signal."""
    fixture = _write_producer(tmp_path, orphan_record=orphan_record)

    with pytest.raises(T.T1998PairRejected) as excinfo:
        _consume(fixture)
    assert excinfo.value.code == "producer-rejected-variant"
    assert excinfo.value.field == field
    assert excinfo.value.arm == "unknown"


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
    """The real admission layer alone rejects this target receipt mutation."""
    fixture = _write_producer(tmp_path)
    wal_path = fixture.campaign / "runs/wal.jsonl"
    records = [json.loads(line) for line in wal_path.read_text().splitlines()]
    commit = next(
        record for record in records
        if record["stage"] == "commit"
        and record["payload"]["fitness_tps"] == 120.0
    )
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
    assert excinfo.value.arm == "unknown"
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
