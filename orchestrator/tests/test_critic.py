# -*- coding: utf-8 -*-
"""critic digest の単体テスト (machine 非依存・mock WAL)。

pytest でも 素の `python orchestrator/tests/test_critic.py` でも走る。
"""
from __future__ import annotations

import atexit
from array import array
import copy
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from types import MappingProxyType

import pytest


pytestmark = pytest.mark.usefixtures("ratified_enforcement_source")

_HERE = os.path.dirname(os.path.abspath(__file__))
_ORCH = os.path.dirname(_HERE)
sys.path.insert(0, os.path.dirname(_ORCH))

from orchestrator.campaign import (env_contract, ident, pipeline,             # noqa: E402
                                   sort_swo_oracle, wal)
from orchestrator.campaign.artifact_admission import (                    # noqa: E402
    ArtifactAdmissionError, CampaignAdmissionDecision, CampaignNotAdmitted,
    CampaignReadPurpose,
    CampaignVerifierEpoch, HistoricalCampaignView, ImmutableWalRecord,
    require_admitted_campaign,
)
from orchestrator.campaign.auditor_gate import (                              # noqa: E402
    AuditorVerdict,
    apply_mandatory_deny_only_veto,
    compute_diff_digest,
)
from orchestrator.campaign.build_admission import (                            # noqa: E402
    GeneratorId,
    attest_generator_output,
    build_run_context,
    derive_build_admission,
)
from orchestrator.campaign.diff_quarantine import (                            # noqa: E402
    DiffQuarantine,
    DiffQuarantineResult,
    TemplateMarker,
)
from orchestrator.campaign.layout import CampaignLayout                        # noqa: E402
from orchestrator.campaign.model import (STAGE_ABORT, STAGE_BENCH_DONE,        # noqa: E402
                            STAGE_BUILD_DONE, STAGE_BUILD_START,
                            STAGE_COMMIT, STAGE_VERIFY_DONE,
                            CampaignConfig, Genome)
from orchestrator.campaign.pin import CURRENT_PIN                              # noqa: E402
from orchestrator.campaign.sort_swo_oracle import CORPUS_ID                   # noqa: E402
from orchestrator.campaign.source_digest import (                              # noqa: E402
    EMPTY_TRACKED_DIFF_SHA256,
    SourceEvidence,
)
from orchestrator.critic import digest as critic_digest                       # noqa: E402
from orchestrator.critic import online_digest as critic_online_digest         # noqa: E402
from orchestrator.critic.digest import (STOCK_SRC_TOKEN, DiffQuarantineRejection,  # noqa: E402
                           IdentityProjection, LivenessRejection,
                           Rejection, VerifyAbortSignal,
                           _validated_oracle_finding,
                           build_digest, load_diff_rejections,
                           load_legacy_v3_sort_swo_rejections,
                           load_legacy_sort_swo_rejections,
                           load_liveness_rejections, load_rejections,
                           load_screen_rejections, load_verify_abort_signals,
                           load_workload,
                           render_rejections as _render_rejections,
                           render_text)
from campaign_lock_test_support import build_v2_lock              # noqa: E402
from orchestrator.tests import commit_receipt_support as receipt_support  # noqa: E402
from orchestrator.verifier.parse import TxnFramingViolation  # noqa: E402


_ADMISSION_CONTEXT = build_run_context(generator_id=GeneratorId.BACKOFF_SWEEP)
_ENV_CONTRACT = env_contract.GENERATIONS["linux-baremetal"][0].contract


def render_rejections(*args, **kwargs):
    """既存 renderer 期待値は明示 raw 診断として維持する。"""
    kwargs["identity_projection"] = IdentityProjection.RAW
    return _render_rejections(*args, **kwargs)


_INVALID_ORACLE_FINDING = {
    "anomaly_code": "sort-swo-oracle-finding-schema-invalid",
}

# Producer 定数を参照しない独立 golden。current と v3/v2 履歴を固定する。
_CURRENT_ORACLE_CONTRACT_ID_GOLDEN = (
    "sort-swo-v5-corpus2-protocol3-checker4-grammar2-"
    "xcc26c4322fe96e7e9427ace317c5b46f3c3d382b00bdbf937bbab595cbe0c60f-"
    "c7d25fac23469-tu7732f044d8ab-f3caa77f8111f-a091abb17ccad"
)
_LEGACY_ORACLE_CONTRACT_ID_V3_GOLDEN = (
    "sort-swo-v3-corpus1-protocol2-checker2-grammar1-"
    "x67c3a5d76f3b1604c57d33ab7d0af15f4aaafa896b4810d7c3c95d812d48faa0-"
    "c436a66d9d5d5-tud1a5e422e226-f7ad0ac262561-a215b718a5bfe"
)
_LEGACY_ORACLE_CONTRACT_ID_V2_GOLDEN = (
    "sort-swo-v2-corpus1-protocol2-checker2-grammar1-"
    "c436a66d9d5d583e52f5d76c60b4add78c4e252dec471ff8b9620dbf8149bf253-"
    "tud88f98bc19911ae7ddd3049731614c0c661a2fe7c0c36c07aebd74281a07d956-"
    "f7ad0ac2625612307826a109b20f11af4beb8cbf124ad8a2e291f85ec63cbde1e"
)


def _oracle_diagnostic():
    return {
        "captured_bytes": 10,
        "total_bytes": 20,
        "sha256": "d" * 64,
        "truncated": True,
    }


def _valid_oracle_findings():
    corpus = f"{CORPUS_ID}/corpus-0"
    pair = {"lhs_index": 1, "rhs_index": 2}
    return {
        "axiom": {
            "kind": "axiom",
            "reason_code": "swo-asymmetric",
            "corpus_id": corpus,
            "order_id": 0,
            "counterexample": {
                "axiom": "asymmetric",
                "input_pairs": [pair, {"lhs_index": 2, "rhs_index": 1}],
            },
        },
        "compile": {
            "kind": "compile",
            "reason_code": "candidate-compile-failed",
            "corpus_id": CORPUS_ID,
            "compiler_diagnostic": _oracle_diagnostic(),
        },
        "execution": {
            "kind": "execution",
            "reason_code": "candidate-comparator-threw",
            "corpus_id": corpus,
            "order_id": 1,
        },
        "execution-fault": {
            "kind": "execution",
            "reason_code": "candidate-execution-fault",
            "corpus_id": corpus,
            "order_id": 1,
            "observations": [
                {"point": "broker-waitid", "status": 11},
            ],
        },
        "nondeterministic": {
            "kind": "nondeterministic",
            "reason_code": "relation-varies-within-process",
            "corpus_id": corpus,
            "order_id": 1,
            "input_pairs": [pair],
            "observations": [
                {
                    "point": "first-pass",
                    "lhs_index": 1,
                    "rhs_index": 2,
                    "value": True,
                },
                {
                    "point": "second-pass-after-other-pairs",
                    "lhs_index": 1,
                    "rhs_index": 2,
                    "value": False,
                },
            ],
        },
        "structure": {
            "kind": "structure",
            "reason_code": "materialized-marker-invalid",
            "corpus_id": CORPUS_ID,
        },
        "protocol": {
            "kind": "protocol",
            "reason_code": "candidate-observation-value-invalid",
            "corpus_id": corpus,
            "order_id": 1,
        },
        "timeout": {
            "kind": "timeout",
            "reason_code": "candidate-compile-cpu-limit-exceeded",
            "corpus_id": CORPUS_ID,
            "compiler_diagnostic": _oracle_diagnostic(),
        },
    }


def _producer_record(
    *, corpus: int, order: int,
    mutation_pair: tuple[int, int] | None = None,
    repeat_pair: tuple[int, int] | None = None,
    repeat_values: int = 0,
) -> bytes:
    outcome = sort_swo_oracle._BROKER_OUTCOME_OK
    detail = sort_swo_oracle._BROKER_DETAIL_OK
    witness_lhs = witness_rhs = sort_swo_oracle._WITNESS_NONE
    detail_value = 0
    if mutation_pair is not None:
        outcome = sort_swo_oracle._BROKER_OUTCOME_REJECT
        detail = sort_swo_oracle._BROKER_DETAIL_EXECUTION_FAULT
        detail_value = 11
    elif repeat_pair is not None:
        outcome = sort_swo_oracle._BROKER_OUTCOME_REJECT
        detail = sort_swo_oracle._BROKER_DETAIL_REPEAT
        witness_lhs, witness_rhs = repeat_pair
        detail_value = repeat_values
    return sort_swo_oracle._HEADER.pack(
        sort_swo_oracle._MAGIC,
        sort_swo_oracle.PROTOCOL_VERSION,
        corpus,
        order,
        sort_swo_oracle.N,
        outcome,
        detail,
        witness_lhs,
        witness_rhs,
        detail_value,
    ) + bytes(sort_swo_oracle.N * sort_swo_oracle.N)


def _run_matrix_record(monkeypatch, record: bytes, *, corpus: int, order: int):
    class _Authority:
        def __init__(self):
            self._replies = iter((
                b'R:{"fd_identities":[[1,2,49152]],"pid":12345}',
                b"V",
            ))

        def settimeout(self, _timeout):
            pass

        def fileno(self):
            return 43

        def recv(self, _size):
            return next(self._replies)

        def recvmsg(self, _size, _ancillary_size):
            marker_fd = os.open(os.devnull, os.O_RDONLY)
            return (
                next(self._replies),
                [(sort_swo_oracle.socket.SOL_SOCKET,
                  sort_swo_oracle.socket.SCM_RIGHTS,
                  array("i", [marker_fd]).tobytes())],
                0,
                None,
            )

        def sendmsg(self, *_args):
            return 1

        def send(self, payload):
            return len(payload)

        def close(self):
            pass

    class _BrokerAuthority:
        def fileno(self):
            return 42

        def close(self):
            pass

    class _Process:
        pid = 12344

        def communicate(self, *args, **kwargs):
            return b"", b""

    monkeypatch.setattr(
        sort_swo_oracle.socket, "socketpair",
        lambda *args, **kwargs: (_Authority(), _BrokerAuthority()),
    )
    monkeypatch.setattr(
        sort_swo_oracle.subprocess, "Popen", lambda *args, **kwargs: _Process(),
    )
    monkeypatch.setattr(
        sort_swo_oracle, "_communicate_hard_timeout",
        lambda process, timeout: (False, 0),
    )
    monkeypatch.setattr(
        sort_swo_oracle, "_read_all", lambda fd, expected: record,
    )
    return sort_swo_oracle._run_matrix(
        Path("/fixture/oracle"), corpus, order,
    )


def _tmp_layout():
    parent = tempfile.mkdtemp(prefix="izanagi_critic_")
    atexit.register(shutil.rmtree, parent, ignore_errors=True)
    cfg = ident.bind_admission_policy(CampaignConfig(
        spec_slug="critic-fixture",
        search_tag="test",
        spec_content="critic post-policy fixture",
        ccbench_commit=CURRENT_PIN,
        search_config={"records": 1, "threads": 1},
        trial="test",
    ), _ADMISSION_CONTEXT.policy)
    cfg = ident.bind_environment_contract(cfg, _ENV_CONTRACT)
    layout = CampaignLayout(
        root=os.path.join(parent, str(ident.campaign_id(cfg)))
    ).ensure()
    wal.write_lock(layout, build_v2_lock(ident.canonical_preimage(cfg)))
    return layout


def _view(layout):
    return require_admitted_campaign(
        layout, purpose=CampaignReadPurpose.CERTIFIED_ACCEPTANCE,
    )


def _legacy_view(records):
    """Build an E0 historical view from pre-attempt-binding WAL records."""
    return HistoricalCampaignView(
        layout=CampaignLayout(root="critic-legacy-fixture"),
        records=tuple(
            ImmutableWalRecord(
                variant=record.variant,
                stage=record.stage,
                env_tag=record.env_tag,
                ts=record.ts,
                payload=MappingProxyType(dict(record.payload)),
            )
            for record in records
        ),
        decision=CampaignAdmissionDecision(
            classification="historical-pre-admission-schema",
            admission_status="historical-not-reclassified",
            verification_status="not-evaluated-by-overlay",
            campaign_id="critic-legacy-fixture",
            campaign_path="critic-legacy-fixture",
            campaign_lock_sha256="",
            wal_sha256="",
            policy_sha256=None,
            attempt_receipt_sha256s=(),
            overlay_ledger_sha256="",
            overlay_record_key=None,
            validator_sha256="",
        ),
        campaign_verifier_epoch=CampaignVerifierEpoch(
            campaign_verifier_epoch="E0",
            state="E0",
            reason_code="v1-authority-absent",
        ),
    )


_QUARANTINE_HEAD = "\n".join((
    "int outside = 0;",
    "// EVOLVE-BLOCK-BEGIN fixture",
    "#if FIXTURE >= 0",
    "int hole = 0;",
    "#else",
    "int stock = 0;",
    "#endif",
    "// EVOLVE-BLOCK-END fixture",
    "int tail = 0;",
))
_QUARANTINE_MARKER = TemplateMarker(
    marker_id="fixture",
    source_rel="include/backoff.hh",
    begin_line=2,
    if_line=3,
    else_line=5,
    endif_line=7,
    end_line=8,
)


def _producer_quarantine_digest(
    diff_body: str, *, file_rel: str = "include/backoff.hh",
    head_text: str = _QUARANTINE_HEAD,
) -> dict:
    diff_text = "\n".join((
        f"diff --git a/{file_rel} b/{file_rel}",
        f"--- a/{file_rel}",
        f"+++ b/{file_rel}",
        diff_body,
    ))
    result = DiffQuarantine(
        _QUARANTINE_MARKER, diff_text, head_text=head_text,
    ).validate()
    assert not result.passed
    assert result.digest is not None
    return result.digest


def _write_producer_quarantine_rejection(lay: CampaignLayout, digest: dict) -> str:
    attempt = _start_attempt(lay, _G.format(b=1, l=1, t=0, w=0), src_token="diff")
    _attempt_event(lay, attempt, STAGE_ABORT, {
        "reason": "diff-quarantine",
        "diff_quarantine": digest,
    })
    return attempt[0]


def _genome_value(canonical: str) -> Genome:
    protocol, body = canonical.split("|", 1)
    flags = {}
    if body:
        for field in body.split(","):
            name, value = field.split("=", 1)
            flags[name] = int(value)
    genome = Genome(protocol, flags)
    assert genome.canonical() == canonical
    return genome


def _start_attempt(
    lay: CampaignLayout, genome: str, *, src_token: str = STOCK_SRC_TOKEN,
) -> tuple[str, str, str, str]:
    """Write one canonical post-policy BUILD_START and return its binding."""
    genome_value = _genome_value(genome)
    dirty = src_token != STOCK_SRC_TOKEN
    admitted_src_token = (
        hashlib.sha256(f"fixture-src-token:{src_token}".encode("utf-8")).hexdigest()
        if dirty else STOCK_SRC_TOKEN
    )
    evidence = SourceEvidence(
        schema_version="source-evidence/v1",
        source_root=os.path.realpath(lay.root),
        ccbench_commit=CURRENT_PIN,
        genome_sha256=hashlib.sha256(genome.encode("utf-8")).hexdigest(),
        src_token=admitted_src_token,
        source_bytes_sha256=hashlib.sha256(
            f"fixture-source:{genome}:{src_token}".encode("utf-8")
        ).hexdigest(),
        tracked_clean=not dirty,
        tracked_diff_sha256=(
            hashlib.sha256(
                f"fixture-diff:{genome}:{src_token}".encode("utf-8")
            ).hexdigest()
            if dirty else EMPTY_TRACKED_DIFF_SHA256
        ),
        tracked_paths=(("include/fixture.hh",) if dirty else ()),
    )
    capability = None
    if dirty:
        capability = attest_generator_output(
            _ADMISSION_CONTEXT,
            evidence,
            generator_input_sha256=hashlib.sha256(
                f"fixture-input:{genome}:{src_token}".encode("utf-8")
            ).hexdigest(),
        )
    admission = derive_build_admission(
        _ADMISSION_CONTEXT, evidence, generator_receipt=capability,
    )
    receipt = admission.as_wal_receipt()
    variant = pipeline.variant_id(genome_value, admitted_src_token)
    attempt_id = "critic-fixture-attempt-%d" % sum(
        record.stage == STAGE_BUILD_START for record in wal.read_records(lay)
    )
    wal.log(lay, variant, STAGE_BUILD_START, _ENV_CONTRACT.env_tag, {
        "genome": genome,
        "src_token": admitted_src_token,
        "build_attempt_id": attempt_id,
        "build_admission": receipt,
        "build_admission_receipt_sha256": receipt["receipt_sha256"],
    })
    return variant, attempt_id, receipt["receipt_sha256"], admitted_src_token


def _attempt_event(
    lay: CampaignLayout, attempt: tuple[str, str, str, str], stage: str,
    payload: dict,
) -> None:
    variant, attempt_id, receipt_sha, _src_token = attempt
    event_payload = {
        **payload,
        **({"contract_sha256": _ENV_CONTRACT.contract_sha256}
           if stage == STAGE_COMMIT else {}),
        "build_attempt_id": attempt_id,
        "build_admission_receipt_sha256": receipt_sha,
    }
    if stage == STAGE_COMMIT:
        receipt_support.log_receipted_commit(
            lay, variant, _ENV_CONTRACT.env_tag, event_payload,
            operation_identity=attempt_id,
        )
    else:
        wal.log(lay, variant, stage, _ENV_CONTRACT.env_tag, event_payload)


def _oracle_receipt(
    contract_id: str,
    materialized_hash: str,
    proposal_hash: str,
    *,
    corpus_version: int = 1,
) -> dict:
    receipt = {
        "contract_id": contract_id,
        "materialized_hole_sha256": materialized_hash,
        "proposal_sha256": proposal_hash,
        "corpus_id": f"sort-swo-corpus-v{corpus_version}",
        "corpus_version": corpus_version,
        "compiler_realpath": "/usr/bin/c++",
        "compiler_version": "fixture-c++ 1.0",
        "compile_flags_sha256": "c" * 64,
        "tu_sha256": "d" * 64,
        "tu_template_sha256": "e" * 64,
        "dependency_root_realpath": "/fixture/dependency-root",
        "dependency_config_sha256": "f" * 64,
    }
    if corpus_version == 2:
        receipt["dependency_manifest_sha256"] = (
            sort_swo_oracle.DEPENDENCY_MANIFEST_SHA256
        )
        receipt["guarantee_boundary"] = (
            sort_swo_oracle.SORT_SWO_GUARANTEE_BOUNDARY
        )
    return receipt


def _write_oracle_rejection(
    lay: CampaignLayout,
    contract_id: object,
    *,
    reason: object = "swo-asymmetric",
    corpus_version: int = 1,
    oracle_finding: dict | None = None,
) -> None:
    attempt = _start_attempt(lay, _G.format(b=1, l=1, t=0, w=0), src_token="swo")
    materialized_hash = "a" * 64
    proposal_hash = "b" * 64
    receipt = (
        _oracle_receipt(
            contract_id,
            materialized_hash,
            proposal_hash,
            corpus_version=corpus_version,
        )
        if type(contract_id) is str else {}
    )
    _attempt_event(lay, attempt, STAGE_ABORT, {
        "reason": "diff-quarantine",
        "diff_quarantine": {
            "subtype": "sort-swo-oracle",
            "reason": reason,
            "oracle_finding": oracle_finding or {
                **_valid_oracle_findings()["axiom"],
                "corpus_id": f"sort-swo-corpus-v{corpus_version}/corpus-0",
            },
            "materialized_hole_sha256": materialized_hash,
            "proposal_sha256": proposal_hash,
            "oracle_contract_id": contract_id,
            "oracle_receipt": receipt,
        },
    })


@pytest.mark.parametrize("loader", [
    load_workload,
    load_rejections,
    load_liveness_rejections,
    load_screen_rejections,
    load_diff_rejections,
    load_legacy_v3_sort_swo_rejections,
    load_legacy_sort_swo_rejections,
    load_verify_abort_signals,
])
def test_every_raw_loader_requires_validated_view(loader) -> None:
    layout = _tmp_layout()
    with pytest.raises(TypeError, match="require_admitted_campaign"):
        loader(layout)


def test_real_legacy_s4_critic_entry_is_rejected() -> None:
    campaign = (
        Path(__file__).resolve().parents[2]
        / "output/campaigns/p3-s4-loop-s4-autonomous-0b53a387"
    )
    with pytest.raises(CampaignNotAdmitted, match="legacy-unclassified"):
        require_admitted_campaign(
            campaign, purpose=CampaignReadPurpose.CERTIFIED_ACCEPTANCE,
        )


def _write(lay, genome, committed=True, **li):
    attempt = _start_attempt(lay, genome)
    _attempt_event(lay, attempt, STAGE_BUILD_DONE, {})
    if committed:
        _attempt_event(lay, attempt, STAGE_VERIFY_DONE, {
            "verdict": "serializable", "certified": True, "anomalies": 0,
            "commits": 1, "aborts": 0, "workload": {"tag": "legacy"},
        })
    _attempt_event(lay, attempt, STAGE_BENCH_DONE, {"leading_indicators": li})
    if committed:                                  # digest は committed のみ拾う
        _attempt_event(
            lay, attempt, STAGE_COMMIT,
            {"fitness_tps": li.get("throughput_tps")},
        )


def _write_retry_projection_fixture(lay, genome):
    """Write stale signals before a retry whose later attempt is committed."""
    old_attempt = _start_attempt(lay, genome)
    _attempt_event(lay, old_attempt, STAGE_BUILD_DONE, {})
    _attempt_event(lay, old_attempt, STAGE_VERIFY_DONE, {
        "verdict": "serializable", "certified": True, "anomalies": 0,
        "commits": 10, "aborts": 90,
        "workload": {"tag": "legacy"},
    })
    _attempt_event(lay, old_attempt, STAGE_BENCH_DONE, {
        "leading_indicators": {
            "throughput_tps": 1.0, "abort_rate": 0.91,
            "latency_ns": 101.0, "llc_miss_rate": 0.11, "ipc": 0.11,
        },
    })
    _attempt_event(lay, old_attempt, STAGE_ABORT, {"reason": "build-error"})

    new_attempt = _start_attempt(lay, genome)
    _attempt_event(lay, new_attempt, STAGE_BUILD_DONE, {})
    _attempt_event(lay, new_attempt, STAGE_VERIFY_DONE, {
        "verdict": "serializable", "certified": True, "anomalies": 0,
        "commits": 20, "aborts": 80,
        "workload": {"tag": "legacy"},
    })
    _attempt_event(lay, new_attempt, STAGE_BENCH_DONE, {
        "leading_indicators": {
            "throughput_tps": 2.0, "abort_rate": 0.81,
            "latency_ns": 202.0, "llc_miss_rate": 0.22, "ipc": 0.22,
        },
    })
    _attempt_event(lay, new_attempt, STAGE_COMMIT, {"fitness_tps": 2.0})


_G = "silo|BACK_OFF={b},NO_WAIT_LOCKING_IN_VALIDATION={l},NO_WAIT_OF_TICTOC={t},WAL={w}"


def test_load_sorts_by_throughput_and_marginal_back_off():
    lay = _tmp_layout()
    # BACK_OFF 0→1: throughput 半減・abort 不変 (競合低減がなく待ち時間のコスト)
    _write(lay, _G.format(b=0, l=1, t=0, w=0),
           throughput_tps=8_000_000, abort_rate=0.05, latency_ns=1000,
           llc_miss_rate=0.2, ipc=1.5)
    _write(lay, _G.format(b=1, l=1, t=0, w=0),
           throughput_tps=4_000_000, abort_rate=0.05, latency_ns=2000,
           llc_miss_rate=0.2, ipc=1.5)
    d = build_digest("balanced", {"ycsb_rratio": "50"}, _view(lay))
    assert len(d.genomes) == 2
    assert d.fastest.flags["BACK_OFF"] == 0           # throughput 降順
    positional = critic_digest.WorkloadDigest(
        d.tag, d.workload, d.genomes, d.axes,
        d.campaign_verifier_epoch, d.read_purpose, d.fastest,
    )
    assert positional.fastest is d.fastest
    assert positional.verifier_assessment_basis is None
    bo = next(e for e in d.axes if e.axis == "BACK_OFF")
    assert bo.means["throughput_tps"] == {"0": 8_000_000, "1": 4_000_000}
    assert abs(bo.rel_throughput - (-0.5)) < 1e-9     # 0→1 で -50%
    assert bo.means["abort_rate"]["0"] == bo.means["abort_rate"]["1"]  # abort 不変
    assert "latency_ns" not in bo.means


def test_no_wait_axis_is_categorical_LT():
    lay = _tmp_layout()
    _write(lay, _G.format(b=0, l=1, t=0, w=0),         # L = 即abort
           throughput_tps=2_700_000, abort_rate=0.40, latency_ns=500,
           llc_miss_rate=0.3, ipc=1.0)
    _write(lay, _G.format(b=0, l=0, t=1, w=0),         # T = retry
           throughput_tps=1_900_000, abort_rate=0.50, latency_ns=700,
           llc_miss_rate=0.3, ipc=0.9)
    d = build_digest("balanced", {}, _view(lay))
    nw = next(e for e in d.axes if e.axis == "no_wait")
    assert set(nw.levels) == {"L", "T"}                # NWL=1→L / NWT=1→T に畳む
    assert nw.means["throughput_tps"]["L"] == 2_700_000
    assert nw.means["throughput_tps"]["T"] == 1_900_000
    assert "latency_ns" not in nw.means
    assert nw.means["abort_rate"] == {"L": 0.40, "T": 0.50}


def test_marginal_averages_over_other_flags():
    """限界効果は他フラグで周辺化する: WAL=0/1 各 2 genome の平均で軸効果を出す。"""
    lay = _tmp_layout()
    # BACK_OFF=0 を 2 genome (WAL 0/1)、BACK_OFF=1 を 2 genome (WAL 0/1)
    _write(lay, _G.format(b=0, l=1, t=0, w=0), throughput_tps=8_000_000,
           abort_rate=0.05, latency_ns=1000, llc_miss_rate=0.2, ipc=1.5)
    _write(lay, _G.format(b=0, l=1, t=0, w=1), throughput_tps=7_000_000,
           abort_rate=0.05, latency_ns=1100, llc_miss_rate=0.2, ipc=1.4)
    _write(lay, _G.format(b=1, l=1, t=0, w=0), throughput_tps=4_000_000,
           abort_rate=0.05, latency_ns=2000, llc_miss_rate=0.2, ipc=1.0)
    _write(lay, _G.format(b=1, l=1, t=0, w=1), throughput_tps=3_000_000,
           abort_rate=0.05, latency_ns=2100, llc_miss_rate=0.2, ipc=0.9)
    d = build_digest("x", {}, _view(lay))
    bo = next(e for e in d.axes if e.axis == "BACK_OFF")
    assert bo.means["throughput_tps"]["0"] == 7_500_000     # (8M+7M)/2
    assert bo.means["throughput_tps"]["1"] == 3_500_000     # (4M+3M)/2
    wal_eff = next(e for e in d.axes if e.axis == "WAL")
    assert wal_eff.means["throughput_tps"]["0"] == 6_000_000  # (8M+4M)/2
    assert wal_eff.means["throughput_tps"]["1"] == 5_000_000  # (7M+3M)/2


def test_uncommitted_genome_excluded():
    """A (atomicity): bench_done はあるが COMMIT 前にクラッシュした genome は digest から除外。"""
    lay = _tmp_layout()
    _write(lay, _G.format(b=0, l=1, t=0, w=0), throughput_tps=8_000_000,
           abort_rate=0.05, latency_ns=1000, llc_miss_rate=0.2, ipc=1.5)
    _write(lay, _G.format(b=1, l=1, t=0, w=0), committed=False,  # half-evaluated
           throughput_tps=4_000_000, abort_rate=0.05, latency_ns=2000,
           llc_miss_rate=0.2, ipc=1.5)
    d = build_digest("x", {}, _view(lay))
    assert len(d.genomes) == 1                   # 非 committed は不採用
    assert d.genomes[0].flags["BACK_OFF"] == 0


def test_load_workload_uses_committed_retry_attempt_only():
    lay = _tmp_layout()
    genome = _G.format(b=0, l=1, t=0, w=0)
    _write_retry_projection_fixture(lay, genome)

    workload = load_workload(_view(lay))

    assert len(workload) == 1
    assert workload[0].genome == genome
    assert workload[0].li == {
        "throughput_tps": 2.0, "abort_rate": 0.81,
        "llc_miss_rate": 0.22, "ipc": 0.22,
    }


def test_load_verify_abort_signals_uses_committed_retry_attempt_only():
    lay = _tmp_layout()
    genome = _G.format(b=0, l=1, t=0, w=0)
    _write_retry_projection_fixture(lay, genome)

    signals = load_verify_abort_signals(_view(lay))

    assert len(signals) == 1
    assert signals[0].genome == genome
    assert signals[0].commits == 20
    assert signals[0].aborts == 80


def test_admission_rejects_committed_retry_attempt_without_verify():
    """A prior attempt's verify cannot certify a later committed retry."""
    lay = _tmp_layout()
    genome = _G.format(b=0, l=1, t=0, w=0)

    old_attempt = _start_attempt(lay, genome)
    _attempt_event(lay, old_attempt, STAGE_BUILD_DONE, {})
    _attempt_event(lay, old_attempt, STAGE_VERIFY_DONE, {
        "verdict": "serializable", "commits": 10, "aborts": 90,
        "workload": {"tag": "legacy"},
    })
    _attempt_event(lay, old_attempt, STAGE_ABORT, {"reason": "build-error"})

    new_attempt = _start_attempt(lay, genome)
    _attempt_event(lay, new_attempt, STAGE_BUILD_DONE, {})
    _attempt_event(lay, new_attempt, STAGE_COMMIT, {"fitness_tps": 2.0})

    # The old attempt's verify_done is intentionally present, while the
    # committed retry has build_done -> commit and no verify of its own.
    with pytest.raises(ArtifactAdmissionError, match="no preceding verify_done"):
        _view(lay)


def test_load_workload_preserves_legacy_commit_without_build_attempt_id():
    lay = _tmp_layout()
    genome = _G.format(b=0, l=1, t=0, w=0)
    variant = "legacy-critic-variant"
    leading_indicators = {
        "throughput_tps": 123.0,
        "abort_rate": 0.2,
        "latency_ns": 456.0,
        "llc_miss_rate": 0.3,
        "ipc": 1.2,
    }
    wal.log(lay, variant, STAGE_BUILD_START, _ENV_CONTRACT.env_tag, {
        "genome": genome,
    })
    wal.log(lay, variant, STAGE_BUILD_DONE, _ENV_CONTRACT.env_tag)
    wal.log(lay, variant, STAGE_BENCH_DONE, _ENV_CONTRACT.env_tag, {
        "leading_indicators": leading_indicators,
    })
    receipt_support.append_legacy_raw_commit(
        lay, variant, _ENV_CONTRACT.env_tag, {"fitness_tps": 123.0},
    )
    view = _legacy_view(wal.read_records(lay))

    commit = view.records[-1]
    assert "build_attempt_id" not in commit.payload
    state = wal.replay_admitted_records(list(view.records))[variant]
    assert state.committed and state.committed_attempt_id is None

    workload = load_workload(view)

    assert len(workload) == 1
    assert workload[0].genome == genome
    assert workload[0].li == {
        "throughput_tps": 123.0, "abort_rate": 0.2,
        "llc_miss_rate": 0.3, "ipc": 1.2,
    }


def test_digest_omits_latency_from_projection_table_and_axes():
    lay = _tmp_layout()
    _write(lay, _G.format(b=0, l=1, t=0, w=0), throughput_tps=8_000_000,
           abort_rate=0.05, latency_ns=1000, llc_miss_rate=0.2, ipc=1.5)
    d = build_digest("balanced", {}, _view(lay))
    assert len(d.genomes) == 1
    assert d.genomes[0].li == {
        "throughput_tps": 8_000_000, "abort_rate": 0.05,
        "llc_miss_rate": 0.2, "ipc": 1.5,
    }
    assert d.axes
    for axis in d.axes:
        assert set(axis.means) == {
            "throughput_tps", "abort_rate", "llc_miss_rate", "ipc",
        }
    text = render_text([d])
    assert "genome | throughput_tps | abort_rate | llc_miss_rate | ipc" in text
    assert "latency" not in text
    benches = [r for r in wal.read_records(lay) if r.stage == STAGE_BENCH_DONE]
    assert len(benches) == 1
    assert benches[0].payload["leading_indicators"]["latency_ns"] == 1000
    assert critic_digest.HIGHER_IS_BETTER == {
        "throughput_tps": True, "abort_rate": False,
        "llc_miss_rate": False, "ipc": True,
    }


def test_render_text_has_axes_and_indicators():
    lay = _tmp_layout()
    _write(lay, _G.format(b=0, l=1, t=0, w=0), throughput_tps=8_000_000,
           abort_rate=0.05, latency_ns=1000, llc_miss_rate=0.2, ipc=1.5)
    txt = render_text([
        build_digest("read-heavy", {"ycsb_rratio": "95"}, _view(lay))
    ])
    assert "read-heavy" in txt
    assert "BACK_OFF" in txt and "no_wait" in txt and "WAL" in txt
    assert "throughput_tps" in txt and "abort_rate" in txt
    assert "限界効果" in txt
    assert "verifier_assessment_basis" not in txt


def test_historical_p2_digest_keeps_e0_and_names_raw_purpose(monkeypatch):
    campaign = (
        Path(__file__).resolve().parents[2]
        / "output/campaigns/p2-2-silo-read-heavy-enumerate-5ffcabad"
    )
    view = require_admitted_campaign(
        campaign, purpose=CampaignReadPurpose.HISTORICAL_RAW,
    )
    text = render_text([build_digest("read-heavy", {}, view)])
    assert "read_purpose: `HISTORICAL_RAW`" in text
    assert (
        "verifier_assessment_basis: "
        "`recorded-at-original-verifier-epoch`" in text
    )
    assert "campaign_verifier_epoch: `E0` (state=E0)" in text
    assert "certified E0" not in text

    def historical_only(_layout, *, purpose):
        assert purpose is CampaignReadPurpose.HISTORICAL_RAW
        return view

    monkeypatch.setattr(
        critic_online_digest, "require_admitted_campaign", historical_only,
    )
    online_text = critic_online_digest.online_digest_text(
        view.layout, "read-heavy", {}, iterations=999,
    )
    assert (
        "verifier_assessment_basis: "
        "`recorded-at-original-verifier-epoch`" in online_text
    )


def test_phase3_cli_declares_certified_purpose(monkeypatch):
    class PurposeObserved(RuntimeError):
        pass

    def observe(_campaign, *, purpose):
        assert purpose is CampaignReadPurpose.CERTIFIED_ACCEPTANCE
        raise PurposeObserved

    monkeypatch.setattr(critic_digest, "require_admitted_campaign", observe)
    with pytest.raises(PurposeObserved):
        critic_digest.main(["digest", "--campaign-dir", "/unused"])


def test_load_rejections_surfaces_structured_anomaly():
    """S4 (規律3 配線): load_rejections が verify-red の構造化 anomaly を次手入力として拾い、
    verify を持たない abort (build-error 等) は除外する。`load_workload` (緑) と対をなす。"""
    lay = _tmp_layout()
    red = _G.format(b=1, l=1, t=0, w=0)
    builderr = _G.format(b=0, l=1, t=0, w=0)
    # verify-red の variant (pipeline が書く形 = abort payload に verify 構造)
    red_attempt = _start_attempt(lay, red, src_token="codediff1")
    _attempt_event(lay, red_attempt, STAGE_ABORT, {
        "reason": "non-serializable",
        "verify": {"verdict": "non-serializable", "anomaly_count": 1,
                   "anomalies": [{"phenomenon": "G2", "cycle": [1, 2],
                                  "edges": [{"from": 1, "to": 2, "types": ["rw"],
                                             "reasons": [{"type": "rw", "key": "aa"}]}]}],
                   "integrity": {"clean": True}},
    })
    # verify を持たない abort (build-error) は規律3 の次手入力ではない → 除外
    builderr_attempt = _start_attempt(lay, builderr)
    _attempt_event(lay, builderr_attempt, STAGE_ABORT, {"reason": "build-error"})

    rej = load_rejections(_view(lay))
    assert len(rej) == 1                          # build-error は除外
    assert rej[0].genome == red
    assert rej[0].flags["BACK_OFF"] == 1          # genome flags まで復元
    assert rej[0].verdict == "non-serializable"
    assert rej[0].anomalies[0]["phenomenon"] == "G2"
    assert rej[0].anomalies[0]["edges"][0]["reasons"][0]["key"] == "aa"
    assert rej[0].integrity == {"clean": True}
    # コード軸の識別 (D23): 同 canonical 別コードの RED variant が alias しないよう
    # WAL キーと src_token も次手入力に載る
    assert rej[0].variant == red_attempt[0]
    assert rej[0].src_token == red_attempt[3]


def test_load_liveness_rejections_surfaces_reason_and_extra():
    """S4 consumer (規律3): liveness-red (verify 前に死んだ) が構造化されて次手入力に
    届き、infra 系 (build-error/eval-exception 等) は詳細でなく正規化 reason の件数に
    集約される (詳細は返さないが沈黙もさせない)。verify-red は混ざらない。"""
    lay = _tmp_layout()
    to = _G.format(b=1, l=1, t=0, w=0)
    to_attempt = _start_attempt(lay, to, src_token="codediff9")
    _attempt_event(lay, to_attempt, STAGE_ABORT, {
        "reason": "trace-timeout", "timeout_s": 120.0,
    })
    te = _G.format(b=0, l=1, t=0, w=0)
    te_attempt = _start_attempt(lay, te)
    _attempt_event(lay, te_attempt, STAGE_ABORT, {
        "reason": "trace-empty", "commits": 0, "aborts": 4321,
    })
    b1 = _G.format(b=0, l=0, t=1, w=0)
    b1_attempt = _start_attempt(lay, b1)
    _attempt_event(lay, b1_attempt, STAGE_ABORT, {"reason": "build-error"})
    b2 = _G.format(b=1, l=0, t=1, w=0)
    b2_attempt = _start_attempt(lay, b2)
    _attempt_event(lay, b2_attempt, STAGE_ABORT,
                   {"reason": "eval-exception: TypeError: boom"})
    vr = _G.format(b=1, l=1, t=0, w=1)
    vr_attempt = _start_attempt(lay, vr)
    _attempt_event(lay, vr_attempt, STAGE_ABORT, {
        "reason": "non-serializable",
        "verify": {"verdict": "non-serializable"},
    })

    lrs, other = load_liveness_rejections(_view(lay))
    assert {l.reason for l in lrs} == {"trace-timeout", "trace-empty"}
    lto = next(l for l in lrs if l.reason == "trace-timeout")
    assert lto.extra.get("timeout_s") == 120.0
    assert lto.variant == to_attempt[0] and lto.src_token == to_attempt[3]
    assert lto.flags["BACK_OFF"] == 1
    lte = next(l for l in lrs if l.reason == "trace-empty")
    assert lte.extra.get("commits") == 0 and lte.extra.get("aborts") == 4321
    assert other == {"build-error": 1, "eval-exception": 1}


def test_commit_witness_liveness_reasons_preserve_witness_and_workload():
    lay = _tmp_layout()
    reasons = (
        "trace-no-commit-witness",
        "trace-batch-commits-unattributed",
        "trace-witness-unsupported-workload",
    )
    for index, reason in enumerate(reasons):
        genome = _G.format(b=index % 2, l=1, t=0, w=0)
        attempt = _start_attempt(lay, genome, src_token=f"witness-{index}")
        _attempt_event(lay, attempt, STAGE_ABORT, {
            "reason": reason,
            "commit_witness": {
                "commit_counts": 10,
                "batch_commit_counts": index,
            },
            "workload": {"tag": "legacy"},
            "binary_workload": "tpcc_silo.exe" if index == 2 else "ycsb_silo.exe",
        })

    liveness, other = load_liveness_rejections(_view(lay))
    assert other == {}
    assert {item.reason for item in liveness} == set(reasons)
    for item in liveness:
        assert item.extra["commit_witness"]["commit_counts"] == 10
        assert item.extra["workload"] == {"tag": "legacy"}
        assert item.workload == {"tag": "legacy"}
    rendered = render_rejections([], liveness, {}, None)
    for reason in reasons:
        assert f"[liveness:{reason}]" in rendered
        assert "読み方:" in rendered


def test_screen_rejection_loader_is_disjoint_and_render_hides_uncertified_metrics():
    """screen reject は専用 loader だけが拾い、未認証性能値は render へ渡さない。

    否定 assert の恒真化を防ぐため、同じ WAL の payload["screen"] に 12345 が
    実在することを正対照で先に固定する。
    """
    lay = _tmp_layout()
    genome = _G.format(b=1, l=1, t=0, w=0)
    attempt = _start_attempt(lay, genome, src_token="codediff-screen")
    _attempt_event(lay, attempt, STAGE_ABORT, {
        "reason": pipeline.SCREEN_REJECTION_REASON,
        "screen": {
            "median_tps": 12345, "cv": 0.01, "baseline_tps": 20000,
            "baseline_ref": "stock-v1", "floor": 0.10, "k": 1.5,
            "margin": -0.38275,
        },
    })

    records = list(wal.read_records(lay))
    abort = next(r for r in records if r.stage == STAGE_ABORT)
    assert abort.payload["screen"]["median_tps"] == 12345  # 正対照

    assert load_rejections(_view(lay)) == []
    liveness, other = load_liveness_rejections(_view(lay))
    assert liveness == [] and other == {}
    screened = load_screen_rejections(_view(lay))
    assert len(screened) == 1
    assert vars(screened[0]) == {
        "genome": genome,
        "flags": {"BACK_OFF": 1, "NO_WAIT_LOCKING_IN_VALIDATION": 1,
                  "NO_WAIT_OF_TICTOC": 0, "WAL": 0},
        "variant": attempt[0],
        "src_token": attempt[3],
        "reason": pipeline.SCREEN_REJECTION_REASON,
    }

    out = render_rejections([], [], {}, None, screen_rejections=screened)
    assert "screening 正常棄却 (未認証のため性能数値なし)" in out
    assert "件数: 1" in out and f"genome={genome}" in out
    assert "codediff-screen" not in out
    assert pipeline.SCREEN_REJECTION_REASON not in out
    assert "全 variant 緑" not in out
    for hidden in ("12345", "median_tps", "baseline_tps", "cv"):
        assert hidden not in out


def test_rejection_types_keep_forward_workload_tag():
    """D36 決定 4 (段 5 配線予定) への前方寛容: abort payload に workload タグが来たら
    verify-red / liveness-red の両型が生値で保持する (形の確定は D36 実装時)。"""
    lay = _tmp_layout()
    red = _G.format(b=1, l=1, t=0, w=0)
    red_attempt = _start_attempt(lay, red)
    _attempt_event(lay, red_attempt, STAGE_ABORT, {
        "reason": "non-serializable", "workload": {"tag": "s2"},
        "verify": {"verdict": "non-serializable", "anomalies": [],
                   "integrity": {}},
    })
    lv = _G.format(b=0, l=1, t=0, w=0)
    lv_attempt = _start_attempt(lay, lv)
    _attempt_event(lay, lv_attempt, STAGE_ABORT, {
        "reason": "trace-timeout", "workload": {"tag": "s2"},
    })
    rej = load_rejections(_view(lay))
    lrs, _ = load_liveness_rejections(_view(lay))
    assert rej[0].workload == {"tag": "s2"}
    assert lrs[0].workload == {"tag": "s2"}
    assert "workload" not in lrs[0].extra      # 別フィールドに分離 (extra と二重化しない)


def _red_verify_payload(total_cycles=1, txns=100):
    """pipeline が書く形 (result_to_dict) の verify payload (cycle 型)。"""
    return {"verdict": "non-serializable", "anomaly_count": 1,
            "total_cycles": total_cycles,
            "stats": {"txns": txns, "reads": 300, "writes": 100,
                      "keys": 50, "edges": 120},
            "anomalies": [{"phenomenon": "G2", "cycle": [1, 2],
                           "edges": [{"from": 1, "to": 2, "types": ["rw"],
                                      "reasons": [{"type": "rw", "key": "aa",
                                                   "u_ver": [1, 1],
                                                   "v_ver": [1, 2]}]}]}],
            "integrity": {"clean": True, "notes": []}}


def test_render_rejections_cycle_shape_shows_total_cycles():
    """cycle 型 (non-serializable): witness と全数 (total_cycles) を併記し切り詰めを
    明示する — witness 数を全数と誤読させない (S2 で total 4,053 / witness 20 の前例)。"""
    lay = _tmp_layout()
    red = _G.format(b=1, l=1, t=0, w=0)
    attempt = _start_attempt(lay, red, src_token="cd1")
    _attempt_event(lay, attempt, STAGE_ABORT, {
        "reason": "non-serializable",
        "verify": _red_verify_payload(total_cycles=57),
    })
    out = render_rejections(load_rejections(_view(lay)), [], {}, None)
    assert "cycle 全数 57 / witness 1 件" in out
    assert "抜粋" in out                                # 切り詰めの明示
    assert "T1 → T2" in out and "rw key=aa" in out      # どの依存を断つかが読める


def test_render_nonserializable_also_shows_unclean_integrity():
    lay = _tmp_layout()
    red = _G.format(b=1, l=1, t=0, w=0)
    attempt = _start_attempt(lay, red, src_token="cd-unclean")
    payload = _red_verify_payload(total_cycles=1)
    payload["integrity"] = {
        "clean": False,
        "missing_txids": 1,
        "notes": ["cycle と trace 欠落が共存"],
    }
    _attempt_event(lay, attempt, STAGE_ABORT, {
        "reason": "non-serializable",
        "verify": payload,
    })
    out = render_rejections(load_rejections(_view(lay)), [], {}, None)
    assert "integrity.clean=False" in out
    assert "cycle 全数 1" in out


def test_render_rejections_liveness_hints_and_other_counts():
    """liveness 型: reason 別の帰属枠ヒント (枯渇/不全/計器破れ) が付き、infra 系は
    件数 1 行サマリに集約される。"""
    lrs = [
        LivenessRejection(genome=_G.format(b=1, l=1, t=0, w=0),
                          flags={"BACK_OFF": 1}, reason="trace-timeout",
                          extra={"timeout_s": 120.0}, variant="v1"),
        LivenessRejection(genome=_G.format(b=0, l=1, t=0, w=0),
                          flags={"BACK_OFF": 0}, reason="trace-empty",
                          extra={"commits": 0, "aborts": 4321}, variant="v2"),
        LivenessRejection(genome=_G.format(b=0, l=0, t=1, w=0),
                          flags={}, reason="trace-parse-error", variant="v3"),
    ]
    out = render_rejections([], lrs, {"build-error": 2, "eval-exception": 1}, None)
    assert "[liveness:trace-timeout]" in out and "timeout_s=120.0" in out
    assert "commit 枯渇" in out                      # trace-empty の読み方
    assert "計器" in out                             # parse-error = 計器破れ
    assert "build-error×2" in out and "eval-exception×1" in out


def test_render_rejections_carries_no_perf_tokens():
    """規律2: rejection 節に性能語彙 (fitness/throughput/tps/latency) が一切出ない —
    「赤に fitness を付けない」を散文でなく否定 assert で固定。"""
    lay = _tmp_layout()
    red = _G.format(b=1, l=1, t=0, w=0)
    red_attempt = _start_attempt(lay, red, src_token="cd1")
    _attempt_event(lay, red_attempt, STAGE_ABORT, {
        "reason": "non-serializable", "verify": _red_verify_payload(),
    })
    lrs = [LivenessRejection(genome=red, flags={}, reason="trace-timeout",
                             extra={"timeout_s": 120.0}, variant="v1")]
    stock = _G.format(b=0, l=1, t=0, w=0)
    stock_attempt = _start_attempt(lay, stock)
    _attempt_event(lay, stock_attempt, STAGE_BUILD_DONE, {})
    _attempt_event(lay, stock_attempt, STAGE_VERIFY_DONE, {
        "verdict": "serializable", "commits": 900, "aborts": 100,
    })
    out = render_rejections(load_rejections(_view(lay)), lrs, {"build-error": 1},
                            load_verify_abort_signals(_view(lay)))
    low = out.lower()
    for tok in ("fitness", "throughput", "tps", "latency"):
        assert tok not in low, f"rejection 節に性能語彙 {tok} が混入"


def _indeterminate_verify_payload(txns=100, missing=0, notes=None, clean=None):
    """pipeline が書く形の verify payload (integrity 型 = indeterminate)。"""
    if clean is None:
        clean = (missing == 0)
    return {"verdict": "indeterminate", "anomaly_count": 0, "total_cycles": 0,
            "stats": {"txns": txns, "reads": 0, "writes": 0, "keys": 0, "edges": 0},
            "anomalies": [],
            "integrity": {"clean": clean, "orphan_reads": 0, "version_dups": 0,
                          "dup_txids": 0, "genesis_commits": 0,
                          "missing_txids": missing, "write_version_mismatch": 0,
                          "malformed_keys": 0, "notes": notes or []}}


def test_integrity_class_rejection_closes_loop():
    """段 2 の positive control 本丸 (J8-B): integrity-class (indeterminate) の赤が
    WAL → load_rejections → render で **cycle 型と区別して**描画される — clean G2
    (broken-silo) だけで規律3 閉ループを certify しない (phase3.md 残存リスク節)。"""
    lay = _tmp_layout()
    v = _G.format(b=1, l=1, t=0, w=0)
    attempt = _start_attempt(lay, v, src_token="cdI")
    _attempt_event(lay, attempt, STAGE_ABORT, {
        "reason": "indeterminate",
        "verify": _indeterminate_verify_payload(
            txns=97, missing=3,
            notes=["missing txids sample: [7, 8, 9]"],
        ),
    })
    rej = load_rejections(_view(lay))
    assert len(rej) == 1 and rej[0].verdict == "indeterminate"
    assert rej[0].integrity["missing_txids"] == 3
    out = render_rejections(rej, [], {}, None)
    assert "missing_txids" in out                    # どのカウンタが非ゼロか
    assert "missing txids sample" in out             # notes (欠番の見本) が届く
    assert "cycle 全数" not in out                   # cycle 型の描画をしない (区別)


def test_permutation_integrity_render_uses_bounded_closed_counts():
    old_permutation_note = (
        "2 permutation-preservation violation(s) [size-changed×2] — "
        "validationPhase's write_set_ sort dropped or duplicated an element "
        "(non-strict-weak-order comparator UB, not a trace-hook fault)"
    )
    lock_note = (
        "1 lock-coverage violation(s) [missing-lock×1] — writePhase wrote a tuple "
        "without holding its lock (torn-read window; variant broke lock coverage, "
        "not a trace-hook fault): sample"
    )
    unknown_sample = json.dumps('opaque "reason"')
    rejection = Rejection(
        genome=_G.format(b=1, l=1, t=0, w=0),
        flags={},
        verdict="indeterminate",
        stats={"txns": 1},
        integrity={
            "clean": False,
            "permutation_violations": 2,
            "permutation_violation_details": {
                "counts": {
                    "size-changed": 1,
                    "rcdptr-set-changed": 0,
                    "unknown": 1,
                },
                "sample": [{"observation": {"kind": "unknown"}}],
                "unknown_reason_sample": [unknown_sample],
            },
            "notes": [old_permutation_note, lock_note],
        },
    )

    out = render_rejections([rejection], [], {}, None)

    assert "{'counts':" not in out
    assert "permutation_violation_details" not in out
    assert "permutation counts: size-changed=1 rcdptr-set-changed=0 unknown=1" in out
    assert f"permutation unknown samples: {unknown_sample}" in out
    assert old_permutation_note not in out
    assert lock_note in out

    zero_rejection = copy.deepcopy(rejection)
    zero_rejection.integrity["permutation_violations"] = 0
    zero_rejection.integrity["permutation_violation_details"] = {
        "counts": {
            "size-changed": 0,
            "rcdptr-set-changed": 0,
            "unknown": 0,
        },
        "sample": [],
        "unknown_reason_sample": [],
    }
    zero_rejection.integrity["notes"] = [
        "0 permutation-preservation violation(s) [none] — retained note",
        lock_note,
    ]

    zero_out = render_rejections([zero_rejection], [], {}, None)

    assert "permutation counts:" not in zero_out
    assert "permutation unknown samples:" not in zero_out
    assert zero_rejection.integrity["notes"][0] in zero_out
    assert lock_note in zero_out


def test_framing_integrity_render_excludes_structured_details_from_counters():
    framing_detail = TxnFramingViolation(
        kind="count-mismatch",
        txid=7,
        expected_reads=1,
        observed_reads=0,
    )
    rejection = Rejection(
        genome=_G.format(b=1, l=1, t=0, w=0),
        flags={},
        verdict="indeterminate",
        stats={"txns": 1},
        integrity={
            "clean": False,
            "framing_violations": 1,
            "framing_violation_details": [framing_detail],
            "notes": [],
        },
    )

    out = render_rejections([rejection], [], {}, None)

    assert "framing_violations" in out
    assert repr(framing_detail) not in out
    assert "framing_violation_details" not in out


def test_write_intent_rejection_is_mechanism_gap_not_cycle():
    """I 行由来の indeterminate は X と同じ機構欠落型に分類し、次手を write-set
    membership / API 意図の復元へ向ける。cycle witness を捏造しない。"""
    lay = _tmp_layout()
    v = _G.format(b=1, l=0, t=1, w=0)
    payload = _indeterminate_verify_payload(
        txns=1, notes=[
            "1 write-intent coverage violation(s) "
            "[write-set-entry-without-intent×1]"
        ])
    payload["integrity"].update({
        "lock_coverage_violations": 0,
        "permutation_violations": 0,
        "write_intent_violations": 1,
    })
    attempt = _start_attempt(lay, v, src_token="cdWI")
    _attempt_event(lay, attempt, STAGE_ABORT, {
        "reason": "indeterminate", "verify": payload,
    })

    out = render_rejections(load_rejections(_view(lay)), [], {}, None)
    assert "機構欠落型 (write intent coverage)" in out
    assert "write-set membership / API 意図の復元" in out
    assert "cycle 帰属を捏造しない" in out
    assert "write-set-entry-without-intent×1" in out
    assert "cycle 全数" not in out
    assert "lock acquisition / retention" not in out


def test_empty_dsg_rejection_renders_explicitly():
    """J8-B 形状 (ii): integrity 全クリーンでも txns=0 (空 DSG) の indeterminate は
    「trace が空」を明示する — 7 カウンタ全ゼロの空パネルとして沈黙しない
    (実 run では trace-empty が手前で先取るが、verifier 単体経路では到達する形)。"""
    lay = _tmp_layout()
    v = _G.format(b=0, l=1, t=0, w=0)
    attempt = _start_attempt(lay, v, src_token="cdE")
    _attempt_event(lay, attempt, STAGE_ABORT, {
        "reason": "indeterminate",
        "verify": _indeterminate_verify_payload(txns=0, clean=True),
    })
    out = render_rejections(load_rejections(_view(lay)), [], {}, None)
    assert "trace が空 (txns=0)" in out
    assert "緑ではない" in out                       # クリーンでも certify しない旨


def test_verify_abort_signal_stock_contrast():
    """J1 シグナル: verify run の abort 率を stock 対照比つきで表示 (閾値判定なし)。"""
    lay = _tmp_layout()
    stock = _G.format(b=0, l=1, t=0, w=0)
    stock_attempt = _start_attempt(lay, stock)
    _attempt_event(lay, stock_attempt, STAGE_BUILD_DONE, {})
    _attempt_event(lay, stock_attempt, STAGE_VERIFY_DONE, {
        "verdict": "serializable", "commits": 900, "aborts": 100,
    })
    var = _G.format(b=1, l=1, t=0, w=0)
    var_attempt = _start_attempt(lay, var, src_token="cd2")
    _attempt_event(lay, var_attempt, STAGE_BUILD_DONE, {})
    _attempt_event(lay, var_attempt, STAGE_VERIFY_DONE, {
        "verdict": "serializable", "commits": 600, "aborts": 400,
    })
    out = render_rejections([], [], {}, load_verify_abort_signals(_view(lay)))
    assert "rate=10.00%" in out                       # stock 100/1000
    assert "rate=40.00%" in out and "stock 比 4.0×" in out


def test_verify_abort_signal_no_stock_and_legacy_are_explicit():
    """規律3 (沈黙禁止): stock 対照不在・旧形式 WAL (aborts 記録なし)・未発火の
    3 形は明示表示 (欠落を無言で流さない)。"""
    lay = _tmp_layout()
    var = _G.format(b=1, l=1, t=0, w=0)
    attempt = _start_attempt(lay, var, src_token="cd3")
    _attempt_event(lay, attempt, STAGE_BUILD_DONE, {})
    _attempt_event(lay, attempt, STAGE_VERIFY_DONE, {
        "verdict": "serializable", "commits": 500,
    })                                                     # aborts 無し = 旧形式
    out = render_rejections([], [], {}, load_verify_abort_signals(_view(lay)))
    assert "stock 対照なし" in out
    assert "aborts 記録なし (旧形式 WAL)" in out
    out2 = render_rejections([], [], {}, [])
    assert "未発火" in out2


def test_verify_abort_signal_prefers_first_pass_when_s2_writes_second_record():
    """D36 決定4 (S2 有効時): variant ごとに legacy→S2 の順で STAGE_VERIFY_DONE が
    複数回書かれうる (敵対レビュー 2026-07-09 CONFIRMED — 修正前は最後勝ちで legacy の
    commits/aborts が消え、stock 対照とスケールが食い違う比較になっていた)。
    campaign 内の全 genome (stock 含む) は同じ passes 順序で評価されるため、
    legacy パス (常に最初) を先勝ちで採用しスケールを揃える。"""
    lay = _tmp_layout()
    stock = _G.format(b=0, l=1, t=0, w=0)
    attempt = _start_attempt(lay, stock)
    _attempt_event(lay, attempt, STAGE_BUILD_DONE, {})
    _attempt_event(lay, attempt, STAGE_VERIFY_DONE, {
        "verdict": "serializable", "commits": 900, "aborts": 100,
        "workload": {"tag": "legacy"},
    })
    _attempt_event(lay, attempt, STAGE_VERIFY_DONE, {
        "verdict": "serializable", "commits": 1_500_000, "aborts": 500_000,
        "workload": {"tag": "s2"},
    })
    out = load_verify_abort_signals(_view(lay))
    assert len(out) == 1
    assert out[0].commits == 900 and out[0].aborts == 100  # S2 (2 件目) でなく legacy を採用


def test_stock_token_matches_source_digest():
    """STOCK_SRC_TOKEN のローカル定数が source_digest.STOCK から drift しない。"""
    from orchestrator.campaign import source_digest
    assert STOCK_SRC_TOKEN == source_digest.STOCK


class _OneChannelProjection(IdentityProjection):
    """1 test node で 1 identity channel だけを発火させる sentinel。"""

    def __init__(self, channel: str, raw: str, projected: str):
        self.channel = channel
        self.raw = raw
        self.projected = projected

    def _project(self, channel: str, value):
        if value is None or value == "":
            return value
        assert channel == self.channel
        assert value == self.raw
        return self.projected

    def project_variant(self, value):
        return self._project("variant", value)

    def project_src_token(self, variant, value):
        return self._project("src_token", value)

    def project_build_attempt_id(self, variant, value):
        return self._project("build_attempt_id", value)

    def project_build_admission_receipt_sha256(self, variant, value):
        return self._project("build_admission_receipt_sha256", value)


def _assert_one_projection_channel(out: str, raw: str, projected: str) -> None:
    assert projected in out
    assert raw not in out


def test_projection_m2_verify_red_variant_channel():
    raw, projected = "M2-raw-verify-variant", "M2-projected-verify-variant"
    out = _render_rejections(
        [Rejection(genome="g", flags={}, verdict="indeterminate", variant=raw)],
        [], identity_projection=_OneChannelProjection("variant", raw, projected),
    )
    _assert_one_projection_channel(out, raw, projected)


def test_projection_m3_verify_red_src_token_channel():
    raw, projected = "M3-raw-verify-src", "M3-projected-verify-src"
    out = _render_rejections(
        [Rejection(genome="g", flags={}, verdict="indeterminate", src_token=raw)],
        [], identity_projection=_OneChannelProjection("src_token", raw, projected),
    )
    _assert_one_projection_channel(out, raw, projected)


def test_projection_m4_liveness_variant_channel():
    raw, projected = "M4-raw-live-variant", "M4-projected-live-variant"
    out = _render_rejections(
        [], [LivenessRejection(genome="g", flags={}, reason="trace-empty", variant=raw)],
        identity_projection=_OneChannelProjection("variant", raw, projected),
    )
    _assert_one_projection_channel(out, raw, projected)


def test_projection_m5_liveness_src_token_channel():
    raw, projected = "M5-raw-live-src", "M5-projected-live-src"
    out = _render_rejections(
        [], [LivenessRejection(genome="g", flags={}, reason="trace-empty", src_token=raw)],
        identity_projection=_OneChannelProjection("src_token", raw, projected),
    )
    _assert_one_projection_channel(out, raw, projected)


def test_projection_m6_liveness_build_attempt_channel():
    raw, projected = "M6-raw-attempt", "M6-projected-attempt"
    out = _render_rejections(
        [], [LivenessRejection(
            genome="g", flags={}, reason="trace-empty",
            extra={"build_attempt_id": raw},
        )],
        identity_projection=_OneChannelProjection("build_attempt_id", raw, projected),
    )
    _assert_one_projection_channel(out, raw, projected)


def test_projection_m7_liveness_build_admission_channel():
    raw, projected = "M7-raw-admission", "M7-projected-admission"
    out = _render_rejections(
        [], [LivenessRejection(
            genome="g", flags={}, reason="trace-empty",
            extra={"build_admission_receipt_sha256": raw},
        )],
        identity_projection=_OneChannelProjection(
            "build_admission_receipt_sha256", raw, projected,
        ),
    )
    _assert_one_projection_channel(out, raw, projected)


def test_projection_m8_diff_quarantine_variant_channel():
    raw, projected = "M8-raw-diff-variant", "M8-projected-diff-variant"
    out = _render_rejections(
        [], [], diff_rejections=[DiffQuarantineRejection(
            genome="g", flags={}, subtype="fixture", reason="fixture", variant=raw,
        )], identity_projection=_OneChannelProjection("variant", raw, projected),
    )
    _assert_one_projection_channel(out, raw, projected)


def test_projection_m9_diff_quarantine_src_token_channel():
    raw, projected = "M9-raw-diff-src", "M9-projected-diff-src"
    out = _render_rejections(
        [], [], diff_rejections=[DiffQuarantineRejection(
            genome="g", flags={}, subtype="fixture", reason="fixture", src_token=raw,
        )], identity_projection=_OneChannelProjection("src_token", raw, projected),
    )
    _assert_one_projection_channel(out, raw, projected)


def test_projection_m10_verify_abort_variant_channel():
    raw, projected = "M10-raw-abort-variant", "M10-projected-abort-variant"
    out = _render_rejections(
        [], [], abort_signals=[VerifyAbortSignal(
            variant=raw, genome="g", commits=1, aborts=1, is_stock=False,
        )], identity_projection=_OneChannelProjection("variant", raw, projected),
    )
    _assert_one_projection_channel(out, raw, projected)


def test_projected_candidate_label_is_never_rendered_as_variant_field():
    raw = "raw-candidate"
    projected = "candidate-0001"
    projection = _OneChannelProjection("variant", raw, projected)
    out = _render_rejections(
        [Rejection(genome="g", flags={}, verdict="indeterminate", variant=raw)],
        [LivenessRejection(
            genome="g", flags={}, reason="trace-empty", variant=raw,
        )],
        diff_rejections=[DiffQuarantineRejection(
            genome="g", flags={}, subtype="fixture", reason="fixture", variant=raw,
        )],
        abort_signals=[VerifyAbortSignal(
            variant=raw, genome="g", commits=1, aborts=1, is_stock=False,
        )],
        identity_projection=projection,
    )
    assert out.count(f"candidate_label={projected}") == 4
    assert f"variant={projected}" not in out


def test_oracle_finding_accepts_exact_producer_keysets():
    findings = _valid_oracle_findings()
    findings["timeout-run"] = {
        "kind": "timeout",
        "reason_code": "candidate-run-cpu-limit-exceeded",
        "corpus_id": f"{CORPUS_ID}/corpus-1",
        "order_id": 2,
    }
    for finding in findings.values():
        assert _validated_oracle_finding(finding) == finding


def test_oracle_consumer_domain_exactly_tracks_producer():
    assert critic_digest.ORACLE_N == sort_swo_oracle.N
    assert critic_digest.ORACLE_ORDERS == sort_swo_oracle.ORDERS
    assert critic_digest.ORACLE_CORPORA == sort_swo_oracle.CORPORA
    assert critic_digest._ORACLE_CORPUS_IDS == frozenset({
        sort_swo_oracle.CORPUS_ID,
        *(
            f"{sort_swo_oracle.CORPUS_ID}/corpus-{corpus}"
            for corpus in sort_swo_oracle.CORPORA
        ),
    })


def test_oracle_finding_rejects_unknown_key_for_every_kind():
    for finding in _valid_oracle_findings().values():
        finding["unknown_key"] = "must-not-be-projected"
        assert _validated_oracle_finding(finding) == _INVALID_ORACLE_FINDING


def test_oracle_finding_rejects_unknown_reason_code_for_every_kind():
    for finding in _valid_oracle_findings().values():
        finding["reason_code"] = "unknown-reason-code"
        assert _validated_oracle_finding(finding) == _INVALID_ORACLE_FINDING


@pytest.mark.parametrize(
    ("kind", "reason_code"),
    [
        pytest.param("compile", "compiler-launch-unavailable", id="launch"),
        pytest.param("compile", "compiler-signal-unavailable", id="signal"),
        pytest.param("timeout", "compile-wall-timeout", id="wall-timeout"),
    ],
)
def test_oracle_finding_rejects_unavailable_only_reason_codes(
        kind, reason_code):
    finding = copy.deepcopy(_valid_oracle_findings()[kind])
    finding["reason_code"] = reason_code
    assert _validated_oracle_finding(finding) == _INVALID_ORACLE_FINDING


def test_oracle_finding_rejects_non_canonical_corpus_id():
    for corpus_id in (
        "arbitrary-corpus",
        f"{CORPUS_ID}/corpus-2",
        f"{CORPUS_ID}/corpus-0/suffix",
    ):
        finding = _valid_oracle_findings()["structure"]
        finding["corpus_id"] = corpus_id
        assert _validated_oracle_finding(finding) == _INVALID_ORACLE_FINDING


def test_oracle_finding_accepts_all_sort_ir_admission_reasons():
    expected_rule_stages = {
        "sort-ir.input-type.v1": "input-type",
        "sort-ir.raw-size.v1": "raw-size",
        "sort-ir.tokenize-resource.v1": "tokenize-resource",
        "sort-ir.envelope.v1": "envelope",
        "sort-ir.parameter-signature.v1": "parameter-signature",
        "sort-ir.expression-shape.v1": "expression-shape",
        "sort-ir.field-direction.v1": "field-direction",
        "sort-ir.duplicate-field.v1": "duplicate-field",
        "sort-ir.eof.v1": "eof",
    }
    assert critic_digest._SORT_IR_ADMISSION_RULE_STAGES == expected_rule_stages
    assert set(expected_rule_stages) == sort_swo_oracle.SORT_IR_GRAMMAR_RULE_IDS
    for reason in sort_swo_oracle.SORT_IR_GRAMMAR_RULE_IDS:
        finding = {
            "kind": "structure",
            "reason_code": reason,
            "corpus_id": CORPUS_ID,
        }
        assert _validated_oracle_finding(finding) == finding

    for rule_id, admission_stage, expected in (
        (
            "sort-ir.expression-shape.v1",
            "expression-shape",
            ("sort-ir.expression-shape.v1", "expression-shape"),
        ),
        ("sort-ir.expression-shape.v1", "eof", ("", "")),
        ("sort-ir.unknown.v1", "expression-shape", ("", "")),
    ):
        lay = _tmp_layout()
        attempt = _start_attempt(
            lay, _G.format(b=1, l=1, t=0, w=0), src_token="sort-ir",
        )
        finding = {
            "kind": "structure",
            "reason_code": "sort-ir.expression-shape.v1",
            "corpus_id": CORPUS_ID,
        }
        _attempt_event(lay, attempt, STAGE_ABORT, {
            "reason": "diff-quarantine",
            "diff_quarantine": {
                "subtype": "sort-swo-oracle",
                "reason": "sort-ir.expression-shape.v1",
                "rule_id": rule_id,
                "admission_stage": admission_stage,
                "oracle_finding": finding,
                "oracle_contract_id": _CURRENT_ORACLE_CONTRACT_ID_GOLDEN,
            },
        })
        loaded = load_diff_rejections(_view(lay))
        assert (loaded[0].rule_id, loaded[0].admission_stage) == expected
        rendered = render_rejections([], [], diff_rejections=loaded)
        if expected[0]:
            assert f"grammar_rule_id={expected[0]}" in rendered
            assert f"admission_stage={expected[1]}" in rendered
        else:
            assert "grammar_rule_id=" not in rendered
            assert "admission_stage=" not in rendered


def test_oracle_finding_rejects_protocol_kind():
    # Final-frame and broker handshake failures are infrastructure details,
    # not candidate observation findings.
    finding = {
        "kind": "protocol",
        "reason_code": "record-size-mismatch",
        "corpus_id": CORPUS_ID,
    }
    assert _validated_oracle_finding(finding) == _INVALID_ORACLE_FINDING


@pytest.mark.parametrize(
    ("kind", "reason_code", "with_observation"),
    [
        ("execution", "candidate-execution-fault", True),
        ("execution", "candidate-sort-call-contract-violation", False),
        ("execution", "candidate-comparator-threw", True),
        ("execution", "candidate-comparator-call-count-invalid", True),
        ("execution", "candidate-comparator-aborted", False),
        ("execution", "candidate-sandbox-violation", False),
        ("execution", "candidate-process-signalled", True),
        ("execution", "candidate-observation-write-failed", True),
        ("protocol", "candidate-observation-size-invalid", True),
        ("protocol", "candidate-observation-value-invalid", False),
        ("timeout", "candidate-run-wall-timeout", False),
        ("timeout", "candidate-run-cpu-limit-exceeded", False),
    ],
)
def test_oracle_finding_accepts_cs2_producer_reason_codes(
        kind, reason_code, with_observation):
    finding = {
        "kind": kind,
        "reason_code": reason_code,
        "corpus_id": f"{CORPUS_ID}/corpus-0",
        "order_id": 0,
    }
    if with_observation:
        finding["observations"] = [
            {"point": "broker-waitid", "status": 75},
        ]
    assert _validated_oracle_finding(finding) == finding


_PRODUCER_DOMAIN_CASES = [
    pytest.param(corpus, order, id=f"corpus-{corpus}-order-{order}")
    for corpus in sort_swo_oracle.CORPORA
    for order in sort_swo_oracle.ORDERS
]


@pytest.mark.parametrize(("corpus", "order"), _PRODUCER_DOMAIN_CASES)
def test_oracle_finding_accepts_real_producer_mutation_finding(
        monkeypatch, corpus, order):
    pair = (sort_swo_oracle.N - 1, 0)
    record = _producer_record(
        corpus=corpus, order=order, mutation_pair=pair,
    )
    matrix, finding = _run_matrix_record(
        monkeypatch, record, corpus=corpus, order=order,
    )
    assert matrix is None
    assert finding is not None
    assert finding.kind is sort_swo_oracle.OracleRejectKind.EXECUTION
    assert finding.reason_code == "candidate-execution-fault"
    finding_dict = finding.as_dict()
    assert _validated_oracle_finding(finding_dict) == finding_dict


@pytest.mark.parametrize(("corpus", "order"), _PRODUCER_DOMAIN_CASES)
def test_oracle_finding_accepts_real_producer_within_process_finding(
        monkeypatch, corpus, order):
    pair = (sort_swo_oracle.N - 1, 0)
    record = _producer_record(
        corpus=corpus,
        order=order,
        repeat_pair=pair,
        repeat_values=1,
    )
    matrix, finding = _run_matrix_record(
        monkeypatch, record, corpus=corpus, order=order,
    )
    assert matrix is None
    assert finding is not None
    finding_dict = finding.as_dict()
    assert _validated_oracle_finding(finding_dict) == finding_dict


_ACROSS_PROCESS_CASES = [
    pytest.param(corpus, order, id=f"corpus-{corpus}-changed-order-{order}")
    for corpus in sort_swo_oracle.CORPORA
    for order in sort_swo_oracle.ORDERS[1:]
]


@pytest.mark.parametrize(("corpus", "changed_order"), _ACROSS_PROCESS_CASES)
def test_oracle_finding_accepts_real_producer_across_process_finding(
        monkeypatch, corpus, changed_order):
    changed_index = sort_swo_oracle.N * sort_swo_oracle.N - 1
    baseline = bytes(sort_swo_oracle.N * sort_swo_oracle.N)
    changed = bytearray(baseline)
    changed[changed_index] = 1

    def run_matrix(_executable, got_corpus, order, *, test_mode=None):
        assert got_corpus == corpus
        return (bytes(changed) if order == changed_order else baseline), None

    monkeypatch.setattr(sort_swo_oracle, "_CORPORA", (corpus,))
    monkeypatch.setattr(sort_swo_oracle, "_run_matrix", run_matrix)
    finding = sort_swo_oracle._evaluate_executable(Path("/fixture/oracle"))
    assert finding is not None
    finding_dict = finding.as_dict()
    assert _validated_oracle_finding(finding_dict) == finding_dict


def test_oracle_finding_rejects_invalid_observation_schema():
    invalid_observations = (
        [],
        [{"point": "after-call"}] * 9,
        ["after-call"],
        [{}],
        [{"point": "after-call", **{f"key-{index}": index for index in range(8)}}],
        [{"point": "after-call", 1: "non-string-key"}],
        [{"point": "after-call", "": True}],
        [{"point": "after-call", "é" * 33: True}],
        [{"point": "after-call", "value": 1.0}],
        [{"point": "after-call", "value": None}],
        [{"point": "after-call", "value": {"nested": True}}],
        [{"point": "after-call", "value": [True]}],
        [{"point": "after-call", "value": "é" * 81}],
        [{"point": "unknown-producer-point", "value": True}],
        [{"point": ["after-call"], "value": True}],
        [{"point": "after-call", "value": "\ud800"}],
    )
    for observations in invalid_observations:
        finding = copy.deepcopy(_valid_oracle_findings()["execution-fault"])
        finding["observations"] = observations
        assert _validated_oracle_finding(finding) == _INVALID_ORACLE_FINDING


def test_invalid_oracle_finding_renders_only_fixed_anomaly_code():
    lay = _tmp_layout()
    attempt = _start_attempt(lay, _G.format(b=1, l=1, t=0, w=0), src_token="swo")
    _attempt_event(lay, attempt, STAGE_ABORT, {
        "reason": "diff-quarantine",
        "diff_quarantine": {
            "subtype": "sort-swo-oracle",
            "reason": "fixed-outer-reason",
            "oracle_finding": {
                "kind": "UNTRUSTED-KIND",
                "reason_code": "UNTRUSTED-REASON",
                "corpus_id": "UNTRUSTED-CORPUS",
            },
            "oracle_contract_id": _CURRENT_ORACLE_CONTRACT_ID_GOLDEN,
        },
    })

    loaded = load_diff_rejections(_view(lay))
    assert loaded[0].oracle_finding == _INVALID_ORACLE_FINDING
    rendered = render_rejections([], [], diff_rejections=loaded)
    assert "oracle_anomaly=sort-swo-oracle-finding-schema-invalid" in rendered
    assert "UNTRUSTED-KIND" not in rendered
    assert "UNTRUSTED-REASON" not in rendered
    assert "UNTRUSTED-CORPUS" not in rendered


@pytest.mark.parametrize(
    ("kind", "expected", "generation", "contract_id", "corpus_id"),
    [
        pytest.param(
            "structure", "閉じた 79 値 sort IR", "current",
            _CURRENT_ORACLE_CONTRACT_ID_GOLDEN, "sort-swo-corpus-v2/corpus-0",
            id="structure-閉じた 79 値 sort IR",
        ),
        pytest.param(
            "compile", "候補 TU の compile が失敗", "current",
            _CURRENT_ORACLE_CONTRACT_ID_GOLDEN, "sort-swo-corpus-v2/corpus-0",
            id="compile-候補 TU の compile が失敗",
        ),
        pytest.param(
            "timeout", "CPU limit 超過", "current",
            _CURRENT_ORACLE_CONTRACT_ID_GOLDEN, "sort-swo-corpus-v2/corpus-0",
            id="timeout-CPU limit 超過",
        ),
        pytest.param(
            "execution", "一般実行 fault", "current",
            _CURRENT_ORACLE_CONTRACT_ID_GOLDEN, "sort-swo-corpus-v2/corpus-0",
            id="execution-候補 comparator の例外",
        ),
        pytest.param(
            "protocol", "worker observation の長さまたは bool 値が不正", "current",
            _CURRENT_ORACLE_CONTRACT_ID_GOLDEN, "sort-swo-corpus-v2/corpus-0",
            id="protocol-worker observation の長さまたは bool 値が不正",
        ),
        pytest.param(
            "nondeterministic", "fresh process 間で bool が不一致", "current",
            _CURRENT_ORACLE_CONTRACT_ID_GOLDEN, "sort-swo-corpus-v2/corpus-0",
            id="nondeterministic-fresh process 間で bool が不一致",
        ),
        pytest.param(
            "mutation", "comparator 呼出し前後の corpus field snapshot が変化",
            "legacy-v3-read-only", _LEGACY_ORACLE_CONTRACT_ID_V3_GOLDEN,
            "sort-swo-corpus-v1/corpus-0",
            id="mutation-read-only snapshot arena への候補 write を kernel が拒否",
        ),
    ],
)
def test_sort_swo_non_axiom_kinds_have_dedicated_fixed_rendering(
        kind, expected, generation, contract_id, corpus_id):
    finding = {
        "kind": kind,
        "reason_code": f"fixture-{kind}",
        "corpus_id": corpus_id,
        "order_id": 1,
    }
    if kind == "compile":
        finding["compiler_diagnostic"] = {
            "captured_bytes": 10,
            "total_bytes": 20,
            "sha256": "d" * 64,
            "truncated": True,
        }
    if kind == "nondeterministic":
        finding["input_pairs"] = [{"lhs_index": 1, "rhs_index": 2}]
    out = render_rejections(
        [], [], diff_rejections=[DiffQuarantineRejection(
            genome="g", flags={}, subtype="sort-swo-oracle",
            reason=f"fixture-{kind}", oracle_finding=finding,
            materialized_hole_sha256="a" * 64,
            proposal_sha256="b" * 64,
            oracle_contract_id=contract_id,
            oracle_contract_generation=generation,
        )],
    )
    assert f"oracle_kind={kind}" in out
    assert expected in out
    assert "SWO公理=" not in out
    assert "comparator を SWO" not in out
    assert f"oracle_contract_generation={generation}" in out
    assert f"oracle_contract_id={contract_id}" in out
    assert f"materialized_hole_sha256={'a' * 64}" in out


def test_sort_swo_axiom_kind_alone_renders_axiom_and_counterexample():
    out = render_rejections(
        [], [], diff_rejections=[DiffQuarantineRejection(
            genome="g", flags={}, subtype="sort-swo-oracle", reason="swo-asymmetric",
            oracle_finding={
                "kind": "axiom", "reason_code": "swo-asymmetric",
                "corpus_id": "sort-swo-corpus-v2/corpus-1", "order_id": 2,
                "counterexample": {
                    "axiom": "asymmetric",
                    "input_pairs": [
                        {"lhs_index": 3, "rhs_index": 4},
                        {"lhs_index": 4, "rhs_index": 3},
                    ],
                },
            },
            materialized_hole_sha256="a" * 64,
            proposal_sha256="b" * 64,
            oracle_contract_id=_CURRENT_ORACLE_CONTRACT_ID_GOLDEN,
            oracle_contract_generation="current",
        )],
    )
    assert "SWO公理=asymmetric 反例pair=(3,4),(4,3)" in out
    assert "示された pair の comparator 関係を修正する" in out


def test_sort_swo_oracle_contract_and_receipt_roundtrip_through_consumer_limit():
    lay = _tmp_layout()
    attempt = _start_attempt(lay, _G.format(b=1, l=1, t=0, w=0), src_token="swo")
    materialized_hash = "a" * 64
    proposal_hash = "b" * 64
    finding = {
        "kind": "axiom",
        "reason_code": "swo-asymmetric",
        "corpus_id": "sort-swo-corpus-v2/corpus-1",
        "order_id": 2,
        "counterexample": {
            "axiom": "asymmetric",
            "input_pairs": [
                {"lhs_index": 3, "rhs_index": 4},
                {"lhs_index": 4, "rhs_index": 3},
            ],
        },
    }
    receipt = {
        "contract_id": _CURRENT_ORACLE_CONTRACT_ID_GOLDEN,
        "materialized_hole_sha256": materialized_hash,
        "proposal_sha256": proposal_hash,
        "corpus_id": "sort-swo-corpus-v2",
        "corpus_version": 2,
        "compiler_realpath": "/usr/bin/c++",
        "compiler_version": "fixture-c++ 1.0",
        "compile_flags_sha256": "c" * 64,
        "tu_sha256": "d" * 64,
        "tu_template_sha256": "e" * 64,
        "dependency_root_realpath": "/fixture/dependency-root",
        "dependency_config_sha256": "f" * 64,
        "dependency_manifest_sha256": (
            sort_swo_oracle.DEPENDENCY_MANIFEST_SHA256
        ),
        "guarantee_boundary": (
            sort_swo_oracle.SORT_SWO_GUARANTEE_BOUNDARY
        ),
    }
    _attempt_event(lay, attempt, STAGE_ABORT, {
        "reason": "diff-quarantine",
        "diff_quarantine": {
            "subtype": "sort-swo-oracle",
            "reason": "swo-asymmetric",
            "oracle_finding": finding,
            "materialized_hole_sha256": materialized_hash,
            "proposal_sha256": proposal_hash,
            "oracle_contract_id": receipt["contract_id"],
            "oracle_receipt": receipt,
        },
    })

    view = _view(lay)
    projected = next(record for record in view.records if record.stage == STAGE_ABORT)
    projected_finding = projected.payload["diff_quarantine"]["oracle_finding"]
    assert type(projected_finding) is MappingProxyType
    assert type(projected_finding["counterexample"]) is MappingProxyType
    assert type(projected_finding["counterexample"]["input_pairs"]) is tuple
    assert type(projected.payload["diff_quarantine"]["oracle_receipt"]) is MappingProxyType

    loaded = load_diff_rejections(view)
    assert len(loaded) == 1
    assert loaded[0].oracle_contract_id == _CURRENT_ORACLE_CONTRACT_ID_GOLDEN
    assert loaded[0].oracle_contract_generation == "current"
    assert loaded[0].oracle_finding == finding
    assert loaded[0].oracle_receipt == receipt
    assert type(loaded[0].oracle_finding) is dict
    assert type(loaded[0].oracle_finding["counterexample"]) is dict
    assert type(loaded[0].oracle_finding["counterexample"]["input_pairs"]) is list
    assert type(loaded[0].oracle_receipt) is dict

    tampered_receipt = dict(receipt)
    tampered_receipt["guarantee_boundary"] = "guarantees[everything]"
    assert critic_digest._validated_oracle_receipt(
        tampered_receipt,
        contract_id=receipt["contract_id"],
        materialized_hash=materialized_hash,
        proposal_hash=proposal_hash,
    ) == {}


@pytest.mark.parametrize("contract_id", [
    "sort-swo-",
    _CURRENT_ORACLE_CONTRACT_ID_GOLDEN + "-suffix",
    _CURRENT_ORACLE_CONTRACT_ID_GOLDEN.replace("sort-swo-v5", "sort-swo-v4", 1),
    _LEGACY_ORACLE_CONTRACT_ID_V3_GOLDEN,
    _LEGACY_ORACLE_CONTRACT_ID_V2_GOLDEN,
    "",
    None,
])
def test_current_loader_rejects_non_exact_oracle_contract_ids(contract_id):
    lay = _tmp_layout()
    _write_oracle_rejection(lay, contract_id)
    with pytest.raises(critic_digest.OracleContractIdMismatch):
        load_diff_rejections(_view(lay))


def test_oracle_contract_length_boundary_fails_closed_without_empty_fallback():
    lay = _tmp_layout()
    _write_oracle_rejection(lay, "x" * 257)
    with pytest.raises(critic_digest.OracleContractIdTooLong):
        load_diff_rejections(_view(lay))

    lay = _tmp_layout()
    _write_oracle_rejection(lay, "x" * 256)
    with pytest.raises(critic_digest.OracleContractIdMismatch):
        load_diff_rejections(_view(lay))


def test_contract_mismatch_is_raised_before_receipt_validation(monkeypatch):
    lay = _tmp_layout()
    _write_oracle_rejection(lay, "sort-swo-v3-unknown")
    monkeypatch.setattr(
        critic_digest,
        "_validated_oracle_receipt",
        lambda *args, **kwargs: pytest.fail("mismatch 後に receipt を検証してはならない"),
    )
    with pytest.raises(critic_digest.OracleContractIdMismatch):
        load_diff_rejections(_view(lay))


def test_legacy_v2_contract_is_not_accepted_by_current_loader():
    lay = _tmp_layout()
    _write_oracle_rejection(lay, _LEGACY_ORACLE_CONTRACT_ID_V2_GOLDEN)
    with pytest.raises(critic_digest.OracleContractIdMismatch):
        load_diff_rejections(_view(lay))


def test_current_v4_and_legacy_v3_v2_loaders_are_generation_exact():
    fixtures = (
        (
            _CURRENT_ORACLE_CONTRACT_ID_GOLDEN,
            2,
            load_diff_rejections,
            "current",
        ),
        (
            _LEGACY_ORACLE_CONTRACT_ID_V3_GOLDEN,
            1,
            load_legacy_v3_sort_swo_rejections,
            "legacy-v3-read-only",
        ),
        (
            _LEGACY_ORACLE_CONTRACT_ID_V2_GOLDEN,
            1,
            load_legacy_sort_swo_rejections,
            "legacy-v2-read-only",
        ),
    )
    for contract_id, corpus_version, selected_loader, generation in fixtures:
        lay = _tmp_layout()
        _write_oracle_rejection(
            lay, contract_id, corpus_version=corpus_version,
        )
        view = _view(lay)
        loaded = selected_loader(view)
        assert len(loaded) == 1
        assert loaded[0].oracle_contract_id == contract_id
        assert loaded[0].oracle_contract_generation == generation
        assert loaded[0].oracle_receipt["corpus_version"] == corpus_version
        for other_loader in {
            load_diff_rejections,
            load_legacy_v3_sort_swo_rejections,
            load_legacy_sort_swo_rejections,
        } - {selected_loader}:
            with pytest.raises(critic_digest.OracleContractIdMismatch):
                other_loader(view)

    def legacy_mutation(corpus_version):
        return {
            "kind": "mutation",
            "reason_code": "corpus-mutated-by-comparator",
            "corpus_id": f"sort-swo-corpus-v{corpus_version}/corpus-0",
            "order_id": 0,
            "input_pairs": [{"lhs_index": 1, "rhs_index": 2}],
            "observations": [{"point": "after-call", "changed": True}],
        }

    def current_execution_fault(corpus_version):
        return {
            "kind": "execution",
            "reason_code": "candidate-execution-fault",
            "corpus_id": f"sort-swo-corpus-v{corpus_version}/corpus-0",
            "order_id": 0,
            "observations": [{"point": "broker-waitid", "status": 11}],
        }

    vocabulary_fixtures = (
        (
            _CURRENT_ORACLE_CONTRACT_ID_GOLDEN,
            2,
            load_diff_rejections,
            current_execution_fault(2),
            legacy_mutation(2),
        ),
        (
            _LEGACY_ORACLE_CONTRACT_ID_V3_GOLDEN,
            1,
            load_legacy_v3_sort_swo_rejections,
            legacy_mutation(1),
            current_execution_fault(1),
        ),
        (
            _LEGACY_ORACLE_CONTRACT_ID_V2_GOLDEN,
            1,
            load_legacy_sort_swo_rejections,
            legacy_mutation(1),
            current_execution_fault(1),
        ),
    )
    for contract_id, corpus_version, selected_loader, native, transplant in (
            vocabulary_fixtures):
        lay = _tmp_layout()
        _write_oracle_rejection(
            lay,
            contract_id,
            corpus_version=corpus_version,
            oracle_finding=native,
        )
        loaded = selected_loader(_view(lay))
        assert loaded[0].oracle_finding == native
        assert loaded[0].oracle_receipt

        lay = _tmp_layout()
        _write_oracle_rejection(
            lay,
            contract_id,
            corpus_version=corpus_version,
            oracle_finding=transplant,
        )
        loaded = selected_loader(_view(lay))
        assert loaded[0].oracle_finding == _INVALID_ORACLE_FINDING
        assert loaded[0].oracle_receipt


def test_legacy_v2_loader_projects_realistic_record_read_only():
    lay = _tmp_layout()
    _write_oracle_rejection(lay, _LEGACY_ORACLE_CONTRACT_ID_V2_GOLDEN)

    loaded = load_legacy_sort_swo_rejections(_view(lay))

    assert len(loaded) == 1
    assert loaded[0].subtype == "sort-swo-oracle"
    assert loaded[0].oracle_contract_id == _LEGACY_ORACLE_CONTRACT_ID_V2_GOLDEN
    assert loaded[0].oracle_contract_generation == "legacy-v2-read-only"
    assert loaded[0].oracle_receipt["contract_id"] == _LEGACY_ORACLE_CONTRACT_ID_V2_GOLDEN
    assert loaded[0].oracle_finding == {
        **_valid_oracle_findings()["axiom"],
        "corpus_id": "sort-swo-corpus-v1/corpus-0",
    }


def test_non_oracle_diff_rejection_keeps_current_acceptance_without_contract_id():
    lay = _tmp_layout()
    attempt = _start_attempt(lay, _G.format(b=1, l=1, t=0, w=0), src_token="diff")
    _attempt_event(lay, attempt, STAGE_ABORT, {
        "reason": "diff-quarantine",
        "diff_quarantine": {
            "subtype": "frame-altered",
            "reason": "frame-altered",
            "diff_region": "outside-marker",
        },
    })

    loaded = load_diff_rejections(_view(lay))
    assert len(loaded) == 1
    assert loaded[0].subtype == "frame-altered"
    assert loaded[0].oracle_contract_id == ""
    assert loaded[0].oracle_contract_generation == ""


@pytest.mark.parametrize(("diff_body", "expected_reason"), [
    (
        "@@ -2,1 +2,0 @@\n-// EVOLVE-BLOCK-BEGIN fixture",
        "フレーム行 (マーカー/#if/#else/#endif/stock 枝) の削除・改変を検出",
    ),
    (
        "@@ -1,1 +1,0 @@\n-int outside = 0;",
        "EVOLVE-BLOCK 領域外の行の削除・改変を検出",
    ),
    (
        "@@ -4,1 +4,2 @@\n int hole = 0;\n+int bad = 1; // comment",
        "hole 内に禁止コメント delimiter byte を検出 (文字列・raw string 内も保守的に拒否)",
    ),
    (
        "@@ -4,1 +4,2 @@\n int hole = 0;\n+int bad = 1; /* comment */",
        "hole 内に禁止コメント delimiter byte を検出 (文字列・raw string 内も保守的に拒否)",
    ),
])
def test_all_middle_dot_reason_branches_survive_real_producer_path(
        diff_body, expected_reason):
    digest = _producer_quarantine_digest(diff_body)
    assert digest["reason"] == expected_reason
    assert digest["reason"].count("・") == 1

    lay = _tmp_layout()
    _write_producer_quarantine_rejection(lay, digest)

    loaded = load_diff_rejections(_view(lay))
    assert loaded[0].reason == expected_reason
    assert loaded[0].evidence == digest["evidence"]
    rendered = render_rejections([], [], diff_rejections=loaded)
    assert expected_reason in rendered
    assert digest["evidence"] in rendered


@pytest.mark.parametrize(("diff_body", "expected_region", "head_text", "file_rel"), [
    pytest.param("", "template hole src 行 4",
                 _QUARANTINE_HEAD.replace("int hole = 0;", "int hole = /* bad */;"),
                 "include/backoff.hh", id="template-comment"),
    pytest.param("", "template hole src 行 4",
                 _QUARANTINE_HEAD.replace("int hole = 0;", "int hole = 0;\\"),
                 "include/backoff.hh", id="template-splice"),
    pytest.param("@@ -99,1 +99,1 @@\n-old\n+new", "src 行 99 (HEAD 行数 9)",
                 _QUARANTINE_HEAD, "include/backoff.hh", id="head-range"),
    pytest.param("@@ -4,1 +4,1 @@\n-wrong\n+new", "src 行 4",
                 _QUARANTINE_HEAD, "include/backoff.hh", id="head-content"),
    pytest.param("@@ --1,1 +1,1 @@\n-old\n+new", "diff 全体",
                 _QUARANTINE_HEAD, "include/backoff.hh", id="malformed-header"),
    pytest.param("@@ -4,2 +4,2 @@\n-int hole = 0;", "diff 全体",
                 _QUARANTINE_HEAD, "include/backoff.hh", id="malformed-truncated"),
    pytest.param("-bare body", "diff 全体",
                 _QUARANTINE_HEAD, "include/backoff.hh", id="malformed-body"),
    pytest.param("@@ -1,1 +1,0 @@\n-int outside = 0;", "cc/other.cc @@ -1 +1",
                 _QUARANTINE_HEAD, "cc/other.cc", id="outside-file"),
    pytest.param("@@ -1,1 +1,0 @@\n-int outside = 0;", "src 行 1",
                 _QUARANTINE_HEAD, "include/backoff.hh", id="delete-outside"),
    pytest.param("@@ -1,1 +1,2 @@\n+int added = 1;\n int outside = 0;",
                 "anchor src 行 1", _QUARANTINE_HEAD, "include/backoff.hh",
                 id="insert-outside"),
    pytest.param("@@ -4,1 +4,2 @@\n int hole = 0;\n+#include <bad>",
                 "anchor src 行 5", _QUARANTINE_HEAD, "include/backoff.hh",
                 id="content-directive"),
    pytest.param("@@ -4,1 +4,2 @@\n int hole = 0;\n+EVOLVE-BLOCK-BEGIN forged",
                 "anchor src 行 5", _QUARANTINE_HEAD, "include/backoff.hh",
                 id="content-marker"),
    pytest.param("@@ -4,1 +4,2 @@\n int hole = 0;\n+int x; // bad",
                 "anchor src 行 5", _QUARANTINE_HEAD, "include/backoff.hh",
                 id="content-comment-line"),
    pytest.param("@@ -4,1 +4,2 @@\n int hole = 0;\n+int x; /* bad */",
                 "anchor src 行 5", _QUARANTINE_HEAD, "include/backoff.hh",
                 id="content-comment-block"),
    pytest.param("@@ -4,1 +4,2 @@\n int hole = 0;\n+int x;\\",
                 "anchor src 行 5", _QUARANTINE_HEAD, "include/backoff.hh",
                 id="content-line-splice"),
])
def test_diff_region_all_producer_forms_survive_loader_and_renderer(
        diff_body, expected_region, head_text, file_rel):
    digest = _producer_quarantine_digest(
        diff_body, file_rel=file_rel, head_text=head_text,
    )
    assert digest["diff_region"] == expected_region
    lay = _tmp_layout()
    _write_producer_quarantine_rejection(lay, digest)
    loaded = load_diff_rejections(_view(lay))
    assert len(loaded) == 1
    assert loaded[0].diff_region == expected_region
    rendered = render_rejections([], [], diff_rejections=loaded)
    assert f" / region={expected_region}" in rendered


def test_diff_region_path_at_sign_survives_real_producer():
    path = "cc/at@path.cc"
    expected_region = f"{path} @@ -1 +1"
    digest = _producer_quarantine_digest(
        "@@ -1,1 +1,0 @@\n-int outside = 0;", file_rel=path,
    )
    assert digest["diff_region"] == expected_region
    lay = _tmp_layout()
    _write_producer_quarantine_rejection(lay, digest)
    loaded = load_diff_rejections(_view(lay))
    assert len(loaded) == 1
    assert loaded[0].diff_region == expected_region
    assert f" / region={expected_region}" in render_rejections(
        [], [], diff_rejections=loaded,
    )


@pytest.mark.parametrize("region", [
    pytest.param("include/backoff.hh", id="backoff-hh"),
    pytest.param("cc/silo/transaction.cc", id="silo-transaction"),
    pytest.param("cc/mocc/transaction.cc", id="mocc-transaction"),
    pytest.param("mocc-temperature-predicate", id="mocc-marker"),
])
def test_diff_region_stage_four_constants_render_verbatim(region):
    rendered = render_rejections([], [], diff_rejections=[DiffQuarantineRejection(
        genome="g", flags={}, subtype="outside-region", reason="safe-reason",
        diff_region=region,
    )])
    assert f" / region={region}" in rendered


def test_diff_region_forbidden_file_path_and_reason_are_sanitized():
    path = "cc/[outside].cc"
    digest = _producer_quarantine_digest(
        "@@ -1,1 +1,0 @@\n-int outside = 0;", file_rel=path,
    )
    assert "[" in digest["diff_region"]
    assert path in digest["diff_region"]
    digest["reason"] = "unsafe\nreason"
    lay = _tmp_layout()
    variant = _write_producer_quarantine_rejection(lay, digest)
    loaded = load_diff_rejections(_view(lay))
    assert len(loaded) == 1
    assert loaded[0].diff_region == digest["diff_region"]
    assert loaded[0].reason == "diff-quarantine-reason-invalid"
    assert loaded[0].subtype == digest["subtype"] == "outside-region"
    assert loaded[0].variant == variant
    rendered = render_rejections([], [], diff_rejections=loaded)
    assert path not in rendered
    assert "unsafe\nreason" not in rendered
    assert " / region=diff-quarantine-region-invalid" in rendered
    assert "理由: diff-quarantine-reason-invalid" in rendered
    assert rendered.count("[diff-quarantine:outside-region]") == 1


@pytest.mark.parametrize("region", [
    pytest.param("line\nfeed", id="line-feed"),
    pytest.param("tab\there", id="tab"),
    pytest.param("escape\x1bvalue", id="escape"),
    pytest.param("bidi\u202evalue", id="bidi-override"),
    pytest.param("left[bracket", id="left-bracket"),
    pytest.param(123, id="non-string"),
])
def test_diff_region_direct_invalid_values_render_sentinel(region):
    rendered = render_rejections([], [], diff_rejections=[DiffQuarantineRejection(
        genome="g", flags={}, subtype="outside-region", reason="safe-reason",
        diff_region=region,
    )])
    assert " / region=diff-quarantine-region-invalid" in rendered
    if isinstance(region, str):
        assert region not in rendered


@pytest.mark.parametrize("region", [
    pytest.param("", id="empty"),
    pytest.param(None, id="missing-in-wal"),
])
def test_diff_region_empty_or_missing_renders_question_mark(region):
    if region is None:
        digest = _producer_quarantine_digest(
            "@@ -1,1 +1,0 @@\n-int outside = 0;", file_rel="cc/other.cc",
        )
        del digest["diff_region"]
        lay = _tmp_layout()
        _write_producer_quarantine_rejection(lay, digest)
        rejections = load_diff_rejections(_view(lay))
        assert len(rejections) == 1
        assert rejections[0].diff_region == ""
    else:
        rejections = [DiffQuarantineRejection(
            genome="g", flags={}, subtype="outside-region", reason="safe-reason",
            diff_region=region,
        )]
    rendered = render_rejections([], [], diff_rejections=rejections)
    assert " / region=?" in rendered


def test_attacker_controlled_hunk_header_is_nonverbatim_through_real_producer():
    attacker_text = "ATTACK"
    digest = _producer_quarantine_digest(
        "@@ --1,1 +1,1 @@ " + attacker_text + "\u202e",
    )
    assert attacker_text not in digest["evidence"]
    assert digest["evidence"].startswith(
        "branch=malformed-hunk-header diff_line=4 byte_length="
    )
    assert " sha256_12=" in digest["evidence"]

    lay = _tmp_layout()
    _write_producer_quarantine_rejection(lay, digest)

    loaded = load_diff_rejections(_view(lay))
    rendered = render_rejections([], [], diff_rejections=loaded)
    assert loaded[0].evidence == digest["evidence"]
    assert attacker_text not in rendered
    assert digest["evidence"] in rendered


def test_auditor_violation_and_nit_evidence_survives_loader_and_renderer():
    working_diff = "auditor reviewed diff\n"
    auditor = AuditorVerdict(
        verdict="reject",
        diff_digest=compute_diff_digest(working_diff),
        violations=[{"type": 16}, {"type": 1}],
        nits=[{"type": "nit"}],
    )
    result = apply_mandatory_deny_only_veto(
        DiffQuarantineResult(passed=True),
        auditor,
        working_diff,
        diff_region="cc/some/other.cc",
        template_diff_id="some-axis-marker",
    )
    expected_evidence = "violations=type-16,type-1; nits=1"
    assert result.digest["evidence"] == expected_evidence

    lay = _tmp_layout()
    _write_producer_quarantine_rejection(lay, result.digest)

    loaded = load_diff_rejections(_view(lay))
    assert loaded[0].evidence == expected_evidence
    rendered = render_rejections([], [], diff_rejections=loaded)
    assert f"  証拠: {expected_evidence}" in rendered


@pytest.mark.parametrize("unsafe", [
    "line1\nline2",
    "escape\x1bvalue",
    "bidi\u202evalue",
    "\u034f",
    "line\u2028separator",
    "paragraph\u2029separator",
    "left[bracket",
    "right]bracket",
    "at@sign",
    "em\u2014dash",
    "\ud800",
    "",
    123,
])
def test_diff_quarantine_reason_rejects_unsafe_unicode_and_non_strings(unsafe):
    assert (
        critic_digest._validated_diff_quarantine_reason(unsafe)
        == "diff-quarantine-reason-invalid"
    )


@pytest.mark.parametrize("safe", [
    "fixed-outer-reason",
    "正規化済み日本語 123",
    "hole 内に禁止コメント delimiter byte を検出 (文字列・raw string 内も保守的に拒否)",
    "auditor verdict=reject (1 violations)",
])
def test_diff_quarantine_reason_preserves_allowed_normalized_text(safe):
    assert critic_digest._validated_diff_quarantine_reason(safe) == safe


def test_diff_quarantine_evidence_uses_same_unicode_policy():
    safe = "branch=head-anchor-content source_line=1 byte_length=2 sha256_12=abcdef123456"
    assert critic_digest._validated_diff_quarantine_evidence(safe) == safe
    assert (
        critic_digest._validated_diff_quarantine_evidence("unsafe\nraw")
        == "diff-quarantine-evidence-invalid"
    )


def test_renderer_revalidates_reason_evidence_and_contract_generation_pair():
    raw_reason = "unsafe\nrenderer-reason"
    raw_contract = "sort-swo-attacker-contract"
    rendered = render_rejections(
        [], [], diff_rejections=[DiffQuarantineRejection(
            genome="g", flags={}, subtype="sort-swo-oracle",
            reason=raw_reason,
            oracle_finding=_valid_oracle_findings()["axiom"],
            oracle_contract_id=raw_contract,
            oracle_contract_generation="current",
        )],
    )
    assert raw_reason not in rendered
    assert raw_contract not in rendered
    assert "diff-quarantine-reason-invalid" in rendered
    assert "oracle_contract_generation=current" in rendered
    assert "oracle_contract_id=oracle-contract-invalid" in rendered

    raw_evidence = "unsafe\nrenderer-evidence"
    rendered_evidence = render_rejections(
        [], [], diff_rejections=[DiffQuarantineRejection(
            genome="g", flags={}, subtype="frame-altered",
            reason="safe-reason", evidence=raw_evidence,
        )],
    )
    assert raw_evidence not in rendered_evidence
    assert "diff-quarantine-evidence-invalid" in rendered_evidence

    generation_mismatch = render_rejections(
        [], [], diff_rejections=[DiffQuarantineRejection(
            genome="g", flags={}, subtype="sort-swo-oracle",
            reason="safe-reason",
            oracle_finding=_valid_oracle_findings()["axiom"],
            oracle_contract_id=_CURRENT_ORACLE_CONTRACT_ID_GOLDEN,
            oracle_contract_generation="legacy-v2-read-only",
        )],
    )
    assert _CURRENT_ORACLE_CONTRACT_ID_GOLDEN not in generation_mismatch
    assert "oracle_contract_generation=legacy-v2-read-only" in generation_mismatch
    assert "oracle_contract_id=oracle-contract-invalid" in generation_mismatch

    legacy_read_only = render_rejections(
        [], [], diff_rejections=[DiffQuarantineRejection(
            genome="g", flags={}, subtype="sort-swo-oracle",
            reason="safe-reason",
            oracle_finding=_valid_oracle_findings()["axiom"],
            oracle_contract_id=_LEGACY_ORACLE_CONTRACT_ID_V2_GOLDEN,
            oracle_contract_generation="legacy-v2-read-only",
        )],
    )
    assert "oracle_contract_generation=legacy-v2-read-only" in legacy_read_only
    assert f"oracle_contract_id={_LEGACY_ORACLE_CONTRACT_ID_V2_GOLDEN}" in legacy_read_only


def test_invalid_reason_rendering_excludes_volatile_suffix_values():
    rendered = []
    for volatile_suffix in ("working-tree-a", "working-tree-b"):
        out = render_rejections(
            [], [], diff_rejections=[DiffQuarantineRejection(
                genome="g", flags={}, subtype="frame-altered",
                reason=f"unsafe\n{volatile_suffix}",
            )],
        )
        assert volatile_suffix not in out
        rendered.append(out)
    assert rendered[0] == rendered[1]
    assert rendered[0].count("diff-quarantine-reason-invalid") == 1


def test_synthetic_rejection_heading_has_closed_origin_not_workload_provenance():
    out = _render_rejections(
        [Rejection(
            genome="g", flags={}, verdict="indeterminate",
            origin_kind="synthetic-fixture",
        )],
        [],
        identity_projection=IdentityProjection.RAW,
    )
    assert "origin_kind=synthetic-fixture" in out
    assert "workload:" not in out
    with pytest.raises(ValueError, match="origin_kind"):
        _render_rejections(
            [Rejection(
                genome="g", flags={}, verdict="indeterminate",
                origin_kind="unknown",
            )],
            [],
            identity_projection=IdentityProjection.RAW,
        )


def test_critic_digest_direct_cli_uses_canonical_projection_type():
    layout = _tmp_layout()
    attempt = _start_attempt(layout, _G.format(b=1, l=1, t=0, w=0))
    _attempt_event(
        layout, attempt, STAGE_ABORT, {"reason": "direct-cli-fixture"},
    )
    completed = subprocess.run(
        [
            sys.executable,
            str(Path(_ORCH) / "critic" / "digest.py"),
            "--campaign-dir",
            layout.root,
        ],
        check=False,
        capture_output=True,
        text=True,
    )
    assert completed.returncode == 0, completed.stderr
    assert "# rejections" in completed.stdout
    assert "Traceback" not in completed.stderr


def test_render_rejections_requires_identity_projection():
    with pytest.raises(TypeError, match="identity_projection"):
        _render_rejections([], [])
    with pytest.raises(TypeError, match="IdentityProjection"):
        _render_rejections([], [], identity_projection=None)


def _run():
    fns = [v for k, v in sorted(globals().items())
           if k.startswith("test_") and callable(v)]
    passed = failed = 0
    for fn in fns:
        try:
            fn(); print(f"PASS {fn.__name__}"); passed += 1
        except AssertionError as e:
            print(f"FAIL {fn.__name__}: {e}"); failed += 1
        except Exception as e:  # noqa: BLE001
            print(f"ERROR {fn.__name__}: {type(e).__name__}: {e}"); failed += 1
    print(f"\n{passed} passed, {failed} failed")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(_run())
