# -*- coding: utf-8 -*-
"""orchestrator (campaign engine) STAGE1 の単体テスト (machine 非依存)。

pytest でも 素の `python orchestrator/tests/test_campaign.py` でも走る。
WAL/lock のテストは TMPDIR 配下に一時 campaign を作る (conftest.py は TMPDIR を
設定しないので、明示されていなければ環境既定の /tmp)。
"""
from __future__ import annotations

import atexit
import argparse
import ast
import collections
import contextlib
import datetime as dt
import enum
import errno
import fcntl
import hashlib
import importlib
import inspect
import io
import json
import os
import re
import shutil
import statistics
import subprocess
import sys
import tempfile
import threading
import time
import tokenize
import types
from pathlib import Path
from unittest import mock as unittest_mock

try:
    import pytest
except ModuleNotFoundError as exc:
    if exc.name != "pytest":
        raise
    pytest = None

_HERE = os.path.dirname(os.path.abspath(__file__))
_ORCH = os.path.dirname(_HERE)
_REPOSITORY = os.path.dirname(_ORCH)
sys.path.insert(0, _REPOSITORY)

from orchestrator import holdout_observation                                  # noqa: E402
from orchestrator.campaign import (buildcache, campaign_lock, genome, ident, pin, pipeline,  # noqa: E402
                      s8b_ratified_freeze, site_policy, source_digest,
                      trigger_gate_binding, wal)
from orchestrator.calibrator import perf_preflight as perf_preflight_module   # noqa: E402
from orchestrator.campaign import env_contract as ec                          # noqa: E402
from orchestrator.campaign.build_admission import (  # noqa: E402
    BuildAdmission,
    BuildAdmissionError,
    GeneratorId,
    add_coder_build_authority_argument,
    build_run_context,
    derive_build_admission,
)
from orchestrator.campaign import layout as layout_module                    # noqa: E402
from orchestrator.campaign.layout import (CampaignLayout,                     # noqa: E402
                             ExplorationCampaignLayout,
                             campaign_lock_dir, campaign_lock_path,
                             campaign_layout, ensure_exploration_namespace,
                             exploration_campaign_layout)
from orchestrator.campaign.lock import (                                       # noqa: E402
    BenchBusy,
    CampaignBusy,
    bench_lock,
    campaign_lock as campaign_flock,
)
from orchestrator.campaign.model import (CampaignConfig, Genome,              # noqa: E402
                            COMMIT_CONTRACT_SHA256_KEY,
                            STAGE_BENCH_DONE, STAGE_BUILD_DONE, STAGE_BUILD_START,
                            STAGE_COMMIT, STAGE_ABORT, STAGE_VERIFY_DONE,
                            STAGE_S1_SESSION, STAGE_S8B_ORACLE_SESSION,
                            STAGES, WAL_STAGES, WalRecord)
from orchestrator.campaign.pipeline import (EvalResult, PerfConfig,           # noqa: E402
                               ScreeningConfig)
from orchestrator.campaign.reflux_ir import TriggerGateIR, emit_predicate     # noqa: E402
from orchestrator.campaign.source_digest import SourceEvidence                # noqa: E402
from skiputil import Skip, skip, skip_conditional_unrun          # noqa: E402
from orchestrator.verifier.model import (Anomaly, CycleEdge, EdgeReason,       # noqa: E402
                            Integrity, ProofSurfaceAssessment, RW, VerifyResult)
from certified_writer_fixtures import (                          # noqa: E402
    build_admission_fixture,
    build_source_drift_fixture,
)
from campaign_lock_test_support import build_v2_lock              # noqa: E402
import commit_receipt_support as commit_receipts                  # noqa: E402

_AUTHORITY_PARSER = argparse.ArgumentParser(add_help=False)
add_coder_build_authority_argument(_AUTHORITY_PARSER)
_BUILD_CONTEXT = build_run_context(
    generator_id=GeneratorId.BACKOFF_SWEEP,
    coder_authority=_AUTHORITY_PARSER.parse_args(
        ["--allow-coder-derived-build"]
    ).coder_build_authority,
)
# T-530 golden は ambient active head から導かない。reviewed registry の
# linux-baremetal generation 1 を明示し、この module の standard campaign fixture
# 1 系統だけを同じ contract fingerprint へ束縛する。
_T530_CONTRACT = ec.GENERATIONS["linux-baremetal"][0].contract
_T530_CONTRACT_SHA256 = (
    "1b2ee85346a4c867754bda497b23d649e66027011167cfb0f9c7f9a1a5fa1dc7"
)
assert _T530_CONTRACT.contract_sha256 == _T530_CONTRACT_SHA256


def _refresh_certified_writer_authority():
    global _AUTHORIZATION, _AUTH_CONTRACT
    authorization = ec.authorize("linux-baremetal")
    _AUTHORIZATION = authorization
    _AUTH_CONTRACT = authorization.contract


if pytest is not None:
    @pytest.fixture(autouse=True)
    def _certified_writer_authority():
        _refresh_certified_writer_authority()


@contextlib.contextmanager
def _assert_raises_contains(expected_type, expected_text):
    try:
        yield
    except expected_type as exc:
        assert expected_text in str(exc), str(exc)
    else:
        raise AssertionError(f"{expected_type.__name__} が送出されなかった")


def _source_evidence(
        genome_value: Genome, commit: str, *, src_token: str = "stock",
        source_root: str = "/tmp/izanagi-test-ccbench",
) -> SourceEvidence:
    dirty = src_token != "stock"
    return SourceEvidence(
        schema_version="source-evidence/v1",
        source_root=os.path.realpath(os.path.abspath(source_root)),
        ccbench_commit=commit,
        genome_sha256=hashlib.sha256(
            genome_value.canonical().encode("utf-8")
        ).hexdigest(),
        src_token=src_token,
        source_bytes_sha256=(src_token if dirty else hashlib.sha256(b"stock").hexdigest()),
        tracked_clean=not dirty,
        tracked_diff_sha256=("4" * 64 if dirty else hashlib.sha256(b"").hexdigest()),
        tracked_paths=(("include/backoff.hh",) if dirty else ()),
    )


def _install_complete_silo_proof_source(source_root: str) -> None:
    """Add the compiled Silo X/P fixture without replacing existing source."""
    protocol_root = Path(source_root) / "cc/silo"
    protocol_root.mkdir(parents=True, exist_ok=True)
    (protocol_root / "CMakeLists.txt").write_text(
        "ccbench_add_protocol(silo SOURCES transaction.cc WORKLOADS ycsb)\n",
        encoding="utf-8",
    )
    transaction = protocol_root / "transaction.cc"
    with transaction.open("a", encoding="utf-8") as stream:
        stream.write(
            "\n#if TRACE\n"
            "izanagi_trace::emit_lock_violation(0, 0, {}, {});\n"
            "izanagi_trace::stream(0) << \"P \";\n"
            "#endif\n"
        )


def _admission_for(
        genome_value: Genome, commit: str, *, src_token: str = "stock",
        source_root: str = "/tmp/izanagi-test-ccbench",
) -> BuildAdmission:
    evidence = _source_evidence(
        genome_value, commit, src_token=src_token, source_root=source_root,
    )
    return derive_build_admission(_BUILD_CONTEXT, evidence)


def _write_receiptful_attempt(
        layout: CampaignLayout, genome_value: Genome, variant: str, *,
        attempt_id: str, terminal: str, reason: str | None = None,
        contract: ec.ExecutionEnvironmentContract = _T530_CONTRACT,
) -> None:
    """Seed one canonical post-policy attempt without bypassing topology checks."""
    admission = _admission_for(genome_value, "deadbeef")
    receipt = admission.as_wal_receipt()
    propagated = {
        "build_attempt_id": attempt_id,
        "build_admission_receipt_sha256": receipt["receipt_sha256"],
    }
    wal.log(layout, variant, STAGE_BUILD_START, contract.env_tag, {
        "genome": genome_value.canonical(),
        "src_token": receipt["source"]["src_token"],
        "build_attempt_id": attempt_id,
        "build_admission": receipt,
        "build_admission_receipt_sha256": receipt["receipt_sha256"],
    })
    if terminal == STAGE_COMMIT:
        wal.log(layout, variant, STAGE_BUILD_DONE, contract.env_tag,
                dict(propagated))
        commit_receipts.log_receipted_commit(
            layout, variant, contract.env_tag, {
            **propagated, "fitness_tps": 100.0,
            "contract_sha256": contract.contract_sha256,
            }, operation_identity=attempt_id,
        )
    elif terminal == STAGE_ABORT:
        wal.log(layout, variant, STAGE_ABORT, contract.env_tag, {
            **propagated, "reason": reason or "fixture-abort",
        })
    else:  # pragma: no cover - helper calls are closed in this module
        raise AssertionError(f"unsupported fixture terminal: {terminal}")


def _write_prebuild_abort(
        layout: CampaignLayout, genome_value: Genome, variant: str, *,
        attempt_id: str, reason: str,
) -> None:
    wal.log(layout, variant, STAGE_BUILD_START, "test-env", {
        "genome": genome_value.canonical(),
        "build_attempt_id": attempt_id,
    })
    wal.log(layout, variant, STAGE_ABORT, "test-env", {
        "reason": reason,
        "build_attempt_id": attempt_id,
    })


# ===== genome 列挙 =====

def test_silo_space_size_and_constraint():
    gs = genome.space_for("silo")
    assert gs.raw_size() == 16              # 2^4
    genomes = gs.enumerate()
    assert len(genomes) == 8                # no-wait XOR: 両 1 (冗長) と 両 0 (livelock) を計 8 除外
    # no-wait はちょうど一方が 1 (両 1 も両 0 も 1 個も無い)
    for g in genomes:
        assert (g.flags["NO_WAIT_LOCKING_IN_VALIDATION"]
                != g.flags["NO_WAIT_OF_TICTOC"])


def test_mocc_space_has_eight_operable_ycsb_boolean_genomes():
    gs = genome.space_for("mocc")
    assert gs.raw_size() == 8
    assert set(gs.axes) == {"BACK_OFF", "TEMPERATURE_RESET_OPT", "KEY_SORT"}
    enumerated = gs.enumerate()
    assert len(enumerated) == 8
    assert len({item.canonical() for item in enumerated}) == 8
    assert all(item.protocol == "mocc" for item in enumerated)


def test_mocc_space_excludes_fixed_and_measurement_axes_and_names_ycsb_scope():
    gs = genome.space_for("mocc")
    assert not ({
        "RWLOCK", "INSERT_READ_DELAY_MS", "INSERT_BATCH_DELAY_MS", "TRACE",
    } & set(gs.axes))
    assert "RWLOCK" in gs.notes and "bare define" in gs.notes
    assert "INSERT_*_DELAY_MS" in gs.notes and "計測撹乱ノブ" in gs.notes
    assert "YCSB workload" in gs.notes and "include/ycsb.hh" in gs.notes


def test_tictoc_and_cicada_are_registered():
    assert genome.space_for("tictoc") is genome.TICTOC_SPACE
    assert genome.space_for("cicada") is genome.CICADA_SPACE


def test_tictoc_space_has_twenty_four_operable_ycsb_boolean_genomes():
    gs = genome.space_for("tictoc")
    assert gs.raw_size() == 32
    assert set(gs.axes) == {
        "BACK_OFF",
        "NO_WAIT_LOCKING_IN_VALIDATION",
        "NO_WAIT_OF_TICTOC",
        "PREEMPTIVE_ABORTS",
        "TIMESTAMP_HISTORY",
    }
    assert all(values == [0, 1] for values in gs.axes.values())
    enumerated = gs.enumerate()
    assert len(enumerated) == 24
    assert len({item.canonical() for item in enumerated}) == 24
    assert all(item.protocol == "tictoc" for item in enumerated)


def test_tictoc_space_excludes_redundant_double_no_wait_but_keeps_wait_pair():
    enumerated = genome.space_for("tictoc").enumerate()
    pairs = {
        (
            item.flags["NO_WAIT_LOCKING_IN_VALIDATION"],
            item.flags["NO_WAIT_OF_TICTOC"],
        )
        for item in enumerated
    }
    assert pairs == {(0, 0), (0, 1), (1, 0)}


def test_tictoc_space_excludes_dead_and_measurement_axes_and_names_ycsb_scope():
    """notes の語句だけを検査し、C++ 側の事実そのものは検証しない。"""
    gs = genome.space_for("tictoc")
    assert not {"PARTITION_TABLE", "SLEEP_READ_PHASE", "TRACE"} & set(gs.axes)
    assert "PARTITION_TABLE" in gs.notes and "死にフラグ" in gs.notes
    assert "workload source" in gs.notes and "共通 header" in gs.notes
    assert "SLEEP_READ_PHASE" in gs.notes and "計測撹乱ノブ" in gs.notes
    assert "(1,1)" in gs.notes and "(1,0)" in gs.notes and "冗長" in gs.notes
    assert "silo" in gs.notes and "XOR" in gs.notes and "transaction.cc:626" in gs.notes
    assert "競合下の完走性・公平性・starvation" in gs.notes and "未実測" in gs.notes
    assert "24" in gs.notes and "YCSB workload" in gs.notes
    assert "静的導出" in gs.notes and "実測ではない" in gs.notes
    assert "bare define" in gs.notes and "導出不能として残す候補もない" in gs.notes
    assert "CLI から個別指定" in gs.notes and "全組合せが異なる挙動" in gs.notes


def test_cicada_space_has_twenty_four_operable_ycsb_boolean_genomes():
    gs = genome.space_for("cicada")
    assert gs.raw_size() == 32
    assert set(gs.axes) == {
        "BACK_OFF",
        "INLINE_VERSION_OPT",
        "INLINE_VERSION_PROMOTION",
        "REUSE_VERSION",
        "WRITE_LATEST_ONLY",
    }
    assert all(values == [0, 1] for values in gs.axes.values())
    enumerated = gs.enumerate()
    assert len(enumerated) == 24
    assert len({item.canonical() for item in enumerated}) == 24
    assert all(item.protocol == "cicada" for item in enumerated)


def test_cicada_space_requires_inline_opt_for_promotion():
    enumerated = genome.space_for("cicada").enumerate()
    pairs = {
        (
            item.flags["INLINE_VERSION_OPT"],
            item.flags["INLINE_VERSION_PROMOTION"],
        )
        for item in enumerated
    }
    assert pairs == {(0, 0), (1, 0), (1, 1)}


def test_cicada_space_excludes_semantic_dead_and_measurement_axes_and_names_ycsb_scope():
    """notes の語句だけを検査し、C++ 側の事実そのものは検証しない。"""
    gs = genome.space_for("cicada")
    assert not {
        "SINGLE_EXEC",
        "PARTITION_TABLE",
        "WORKER1_INSERT_DELAY_RPHASE",
        "INSERT_READ_DELAY_MS",
        "INSERT_BATCH_DELAY_MS",
        "TRACE",
    } & set(gs.axes)
    assert "SINGLE_EXEC" in gs.notes and "多版から単版" in gs.notes
    assert "測るものそのもの" in gs.notes and "fresh configure" in gs.notes
    assert "PARTITION_TABLE" in gs.notes and "print 専用" in gs.notes
    assert "README の説明と現行コードが食い違う" in gs.notes
    assert "WORKER1_INSERT_DELAY_RPHASE" in gs.notes
    assert "INSERT_READ_DELAY_MS" in gs.notes and "INSERT_BATCH_DELAY_MS" in gs.notes
    assert "計測撹乱ノブ" in gs.notes
    assert "WRITE_LATEST_ONLY" in gs.notes and "読み側の可視性が不変" in gs.notes
    assert "余分に abort" in gs.notes
    assert "(OPT,PROMOTION)=(0,1)" in gs.notes and "(0,0)" in gs.notes
    assert "CC / data path の挙動が同一" in gs.notes and "起動時の option 表示だけは異なる" in gs.notes
    assert "24" in gs.notes and "YCSB workload" in gs.notes
    assert "静的導出" in gs.notes and "実測ではない" in gs.notes
    assert "bare define" in gs.notes and "導出不能として残す候補もない" in gs.notes
    assert "CLI から個別指定" in gs.notes and "全組合せが異なる挙動" in gs.notes


def test_buildcache_detects_trace_symbol_leak():
    """規律1: nm 出力に izanagi_trace があれば perf build への漏れと判定 (継続執行)。"""
    clean = "0000 T main\n0000 t _ZN4silo6commitEv\n0000 T makeDB\n"
    leaked = clean + "0000 t _ZN12izanagi_trace4emitE...\n"
    assert not buildcache._has_trace_symbols(clean)
    assert buildcache._has_trace_symbols(leaked)


@contextlib.contextmanager
def _tmp_dir(tmp_path):
    """pytest では tmp_path fixture、素の runner (tmp_path=None) では tempfile ベースの
    一時 dir を pathlib.Path で供給する。二重 runner 契約 (README) をどちらの経路でも満たす。"""
    if tmp_path is not None:
        yield tmp_path
        return
    import pathlib
    d = tempfile.mkdtemp(prefix="izanagi_tc_")
    try:
        yield pathlib.Path(d)
    finally:
        shutil.rmtree(d, ignore_errors=True)


def test_buildcache_clears_stale_build_dir(tmp_path=None):
    """kill 残骸 (CMakeCache あり・binary 無し) は configure 前に破棄される。

    残骸 CMakeCache の一時 worktree パス焼き付きが以後の configure を永続的に即死させた
    2026-07-11 s8a stock build-error の回帰固定。"""
    with _tmp_dir(tmp_path) as tmp:
        bdir = tmp / "silo_deadbeef00_t0"
        bdir.mkdir()
        (bdir / "CMakeCache.txt").write_text("CMAKE_HOME_DIRECTORY:INTERNAL=/tmp/gone_wt/wt\n")
        binary = str(bdir / "cc" / "silo" / "ycsb_silo.exe")
        buildcache._clear_stale_build_dir(str(bdir), binary)
        assert not bdir.exists()                 # 中途 dir は破棄される


def test_buildcache_stale_clear_spares_complete_and_absent(tmp_path=None):
    """binary が完成している dir は破棄しない (正当な成果物)。bdir 不在は no-op。"""
    with _tmp_dir(tmp_path) as tmp:
        bdir = tmp / "silo_cafebabe00_t1"
        binpath = bdir / "cc" / "silo" / "ycsb_silo.exe"
        binpath.parent.mkdir(parents=True)
        binpath.write_bytes(b"\x7fELF")
        buildcache._clear_stale_build_dir(str(bdir), str(binpath))
        assert binpath.exists()                  # 完成品は温存
        absent = tmp / "no_such_dir"
        buildcache._clear_stale_build_dir(str(absent), str(absent / "x.exe"))  # 例外なく no-op


def test_genome_canonical_deterministic():
    g1 = Genome("silo", {"WAL": 0, "BACK_OFF": 1})
    g2 = Genome("silo", {"BACK_OFF": 1, "WAL": 0})    # 順序違い
    assert g1.canonical() == g2.canonical()           # flag 名順で正準化
    assert g1.canonical() == "silo|BACK_OFF=1,WAL=0"
    assert g1.cmake_defines() == ["-DCCBENCH_BACK_OFF=1", "-DCCBENCH_WAL=0"]


def test_enumerate_deterministic_order():
    a = [g.canonical() for g in genome.space_for("silo").enumerate()]
    b = [g.canonical() for g in genome.space_for("silo").enumerate()]
    assert a == b                                     # 決定論的順序


# ===== campaign 同一性 (D13) =====

def _cfg(**kw):
    base = dict(spec_slug="readheavy-locont", search_tag="fullsearch",
                spec_content="rratio=95,skew=0.9", ccbench_commit="977e194",
                search_config={"tier": "0-1", "scale": "silo"})
    base.update(kw)
    return _bound(CampaignConfig(**base))


def _bound(cfg: CampaignConfig) -> CampaignConfig:
    cfg = ident.bind_admission_policy(cfg, _BUILD_CONTEXT.policy)
    return ident.bind_environment_contract(cfg, _T530_CONTRACT)


_PRE_T343_REPRESENTATIVE_CAMPAIGN_ID = "readheavy-locont-fullsearch-45ca7ab9"
_T343_REPRESENTATIVE_CAMPAIGN_ID = "readheavy-locont-fullsearch-4347a1fd"
_T816_REPRESENTATIVE_CAMPAIGN_ID = "readheavy-locont-fullsearch-27d737fd"
_T530_REPRESENTATIVE_CAMPAIGN_ID = "readheavy-locont-fullsearch-cbddc476"
_PRE_T343_BACKOFF_CAMPAIGN_IDS = frozenset({
    "backoff-sweep-silo-write-heavy-sweep-4891e99f",
    "backoff-sweep-silo-balanced-sweep-3d39fe94",
    "backoff-sweep-silo-read-heavy-sweep-9d37b4cf",
})
_T343_BACKOFF_CAMPAIGN_IDS = frozenset({
    "backoff-sweep-silo-write-heavy-sweep-c7e53c07",
    "backoff-sweep-silo-balanced-sweep-09c1364f",
    "backoff-sweep-silo-read-heavy-sweep-adad17bc",
})
_T816_POLICY_KICKOFF_BACKOFF_CAMPAIGN_IDS = frozenset({
    "backoff-sweep-silo-write-heavy-sweep-4fdedcc4",
    "backoff-sweep-silo-balanced-sweep-920bb445",
    "backoff-sweep-silo-read-heavy-sweep-ac548305",
})
_T816_BACKOFF_CAMPAIGN_IDS = frozenset({
    "backoff-sweep-silo-write-heavy-sweep-172b45ad",
    "backoff-sweep-silo-balanced-sweep-2899b6a7",
    "backoff-sweep-silo-read-heavy-sweep-57160b6c",
})
_T530_BACKOFF_CAMPAIGN_IDS = frozenset({
    "backoff-sweep-silo-write-heavy-sweep-d0589634",
    "backoff-sweep-silo-balanced-sweep-255794e7",
    "backoff-sweep-silo-read-heavy-sweep-38d2a05a",
})
_PRE_T343_S6_CAMPAIGN_IDS = frozenset({
    "p3-s6-sort-sweep-balanced-sweep-dd25aa8c",
    "p3-s6-sort-sweep-write-heavy-sweep-0484feef",
})
_T343_S6_CAMPAIGN_IDS = frozenset({
    "p3-s6-sort-sweep-balanced-sweep-c5a978ca",
    "p3-s6-sort-sweep-write-heavy-sweep-dde984c3",
})
_T816_S6_CAMPAIGN_IDS = frozenset({
    "p3-s6-sort-sweep-balanced-sweep-36c93671",
    "p3-s6-sort-sweep-write-heavy-sweep-e6174b76",
})
_T530_S6_CAMPAIGN_IDS = frozenset({
    "p3-s6-sort-sweep-balanced-sweep-cc0921a0",
    "p3-s6-sort-sweep-write-heavy-sweep-209414f0",
})


def _certified_lock_text(cfg: CampaignConfig) -> str:
    return build_v2_lock(ident.canonical_preimage(cfg))


def _write_certified_lock(layout: CampaignLayout, cfg: CampaignConfig) -> None:
    wal.write_lock(layout, _certified_lock_text(cfg))


def _campaign_id_from_historical_preimage(spec_slug, search_tag, preimage):
    rendered = json.dumps(
        preimage, sort_keys=True, separators=(",", ":"), ensure_ascii=False,
    )
    digest = hashlib.sha256(rendered.encode("utf-8")).hexdigest()[:8]
    return f"{spec_slug}-{search_tag}-{digest}"


def test_campaign_id_deterministic():
    assert str(ident.campaign_id(_cfg())) == str(ident.campaign_id(_cfg()))


def test_campaign_id_binds_admission_policy():
    historical = _campaign_id_from_historical_preimage(
        "readheavy-locont", "fullsearch", {
            "spec_content": "rratio=95,skew=0.9",
            "ccbench_commit": "977e194",
            "search_tag": "fullsearch",
            "search_config": {"tier": "0-1", "scale": "silo"},
            "trial": None,
        },
    )
    current = str(ident.campaign_id(_cfg()))
    assert historical == _PRE_T343_REPRESENTATIVE_CAMPAIGN_ID
    assert current == _T816_REPRESENTATIVE_CAMPAIGN_ID
    assert current not in {
        historical,
        _T343_REPRESENTATIVE_CAMPAIGN_ID,
        _T530_REPRESENTATIVE_CAMPAIGN_ID,
    }


def test_environment_contract_binding_is_runtime_carrier_only():
    raw = CampaignConfig(
        spec_slug="contract", search_tag="identity",
        spec_content="explicit reviewed contract fixture", ccbench_commit="deadbeef",
        search_config={"axis": "fixture"},
    )
    admission_bound = ident.bind_admission_policy(raw, _BUILD_CONTEXT.policy)
    bound = ident.bind_environment_contract(admission_bound, _T530_CONTRACT)
    assert bound.search_config == admission_bound.search_config
    assert bound.bound_environment_contract is _T530_CONTRACT
    assert set(json.loads(ident.canonical_preimage(bound))) == {
        "spec_content", "ccbench_commit", "search_tag", "search_config", "trial",
    }
    for forbidden in (
            "env_tag", "generation", "issued_pid", "activation_serial",
            "created_at", "receipt"):
        assert forbidden not in bound.search_config
    assert ident.canonical_preimage(bound) == \
        ident.canonical_preimage(admission_bound)


def test_bind_environment_contract_rejects_legacy_identity_hash():
    foreign = ec.GENERATIONS["pegasus"][0].contract.contract_sha256
    for conflicting in (None, foreign, _T530_CONTRACT_SHA256.upper()):
        cfg = CampaignConfig(
            spec_slug="contract", search_tag="conflict",
            spec_content="conflicting prebind", ccbench_commit="deadbeef",
            search_config={"environment_contract_sha256": conflicting},
        )
        before = dict(cfg.search_config)
        try:
            ident.bind_environment_contract(cfg, _T530_CONTRACT)
            assert False, "異なる事前束縛値を上書きせず拒否すべき"
        except ValueError as exc:
            assert (
                "search_config.environment_contract_sha256 は旧 identity field"
                in str(exc)
            )
        assert cfg.search_config == before


def test_campaign_lock_identity_excludes_contract_authority():
    stored = json.loads(ident.canonical_preimage(_cfg()))
    assert set(stored) == {
        "spec_content", "ccbench_commit", "search_tag", "search_config", "trial",
    }
    assert "environment_contract_sha256" not in stored["search_config"]
    decoded = campaign_lock.decode_campaign_lock(_certified_lock_text(_cfg()))
    assert decoded.identity == stored
    assert decoded.authority.environment_contract_sha256 == _T530_CONTRACT_SHA256


def test_different_runtime_contracts_keep_same_campaign_id():
    admission_bound = ident.bind_admission_policy(CampaignConfig(
        spec_slug="contract", search_tag="identity",
        spec_content="runtime authority is outside identity",
        ccbench_commit="deadbeef", search_config={"axis": "fixture"},
    ), _BUILD_CONTEXT.policy)
    linux = ident.bind_environment_contract(admission_bound, _T530_CONTRACT)
    pegasus = ident.bind_environment_contract(
        admission_bound, ec.GENERATIONS["pegasus"][0].contract,
    )
    assert linux.search_config == pegasus.search_config
    assert linux.bound_environment_contract is not pegasus.bound_environment_contract
    assert ident.campaign_id(linux) == ident.campaign_id(pegasus)


def test_run_campaign_binds_guard_contract_before_campaign_id():
    from orchestrator.campaign import loop as L

    cfg = CampaignConfig(
        spec_slug="contract", search_tag="order",
        spec_content="authorization before identity", ccbench_commit="deadbeef",
    )
    captured = []
    sentinel = RuntimeError("campaign-id-spy-stop")
    saved = L.ident.campaign_id

    def campaign_id_spy(received):
        captured.append(received)
        raise sentinel

    L.ident.campaign_id = campaign_id_spy
    caught = None
    try:
        try:
            L.run_campaign(
                cfg, [], PerfConfig(records=1, threads=1),
                _AUTH_CONTRACT.env_tag, _AUTH_CONTRACT.clocks_per_us,
                numactl=list(_AUTH_CONTRACT.numactl),
                authorization_contract=_AUTHORIZATION,
                build_context=_BUILD_CONTEXT, declared_use_class="official",
                log=lambda _message: None,
            )
        except RuntimeError as exc:
            caught = exc
    finally:
        L.ident.campaign_id = saved
    assert caught is sentinel and len(captured) == 1
    assert "environment_contract_sha256" not in captured[0].search_config
    assert captured[0].bound_environment_contract is _AUTH_CONTRACT


def test_campaign_id_content_sensitive():
    # spec の中身を変えると hash が変わる (名前据え置きでも別 campaign, honest-by-construction)
    h0 = ident.campaign_id(_cfg()).cfg_hash8
    h1 = ident.campaign_id(_cfg(spec_content="rratio=50,skew=0.9")).cfg_hash8
    assert h0 != h1


def test_campaign_id_slug_not_in_hash():
    # slug は人間ラベル → 変えても hash 不変 (内容が同一性源)
    h0 = ident.campaign_id(_cfg()).cfg_hash8
    h1 = ident.campaign_id(_cfg(spec_slug="別名")).cfg_hash8
    assert h0 == h1


def test_campaign_id_trial_and_searchtag_change_hash():
    h0 = ident.campaign_id(_cfg()).cfg_hash8
    assert ident.campaign_id(_cfg(trial="2")).cfg_hash8 != h0          # 意図的再実行
    assert ident.campaign_id(_cfg(search_tag="llmguided")).cfg_hash8 != h0  # ablation 軸


def test_campaign_id_search_config_order_invariant():
    # search_config のキー順は同一性に影響しない (正準化)
    a = ident.campaign_id(_cfg(search_config={"tier": "0-1", "scale": "silo"}))
    b = ident.campaign_id(_cfg(search_config={"scale": "silo", "tier": "0-1"}))
    assert a.cfg_hash8 == b.cfg_hash8


def test_campaign_id_verify_config_changes_hash():
    """D36 決定4-1: search_config['verify'] (S2 on/off) は campaign_id ハッシュに
    含まれる (search_config は既に汎用ハッシュ対象、D13) — S2 の ablation は別
    campaign になり WAL terminal skip の汚染 (S2 素通り certified の恒久化) を
    構造的に防ぐ。"""
    h0 = ident.campaign_id(_cfg(search_config={"tier": "0-1", "scale": "silo"})).cfg_hash8
    h1 = ident.campaign_id(_cfg(search_config={
        "tier": "0-1", "scale": "silo",
        pipeline.SEARCH_CONFIG_VERIFY_KEY: pipeline.VERIFY_LEGACY_PLUS_S2})).cfg_hash8
    assert h0 != h1


def _screening(**kw):
    base = dict(baseline_tps=10000.0, baseline_ref="stock-v1",
                baseline_measured_at=time.time(), floor=0.10, k=1.5,
                baseline_abort_rate=0.03, high_abort_factor=2.0)
    base.update(kw)
    return ScreeningConfig(**base)


def test_screening_config_is_frozen_and_requires_baseline_abort_rate():
    assert ScreeningConfig.__dataclass_params__.frozen is True
    try:
        ScreeningConfig(baseline_tps=1.0, baseline_ref="v", baseline_measured_at=1.0,
                        floor=0.1)
        assert False, "baseline_abort_rate must be required"
    except TypeError:
        pass
    sc = _screening()
    try:
        sc.floor = 0.2
        assert False, "frozen dataclass must reject mutation"
    except (AttributeError, TypeError):
        pass


def test_screening_config_rejects_invalid_statistical_policy():
    invalid = [
        ("k", 1.499999),
        ("baseline_tps", 0.0),
        ("baseline_tps", -1.0),
        ("floor", 0.0),
        ("floor", 1.0),
        ("baseline_abort_rate", -0.000001),
        ("high_abort_factor", 0.999999),
        ("reanchor_threshold_s", 0.0),
        ("reanchor_threshold_s", -1.0),
    ]
    for field_name, value in invalid:
        try:
            _screening(**{field_name: value})
            assert False, f"{field_name}={value!r} must fail closed"
        except ValueError as exc:
            assert field_name in str(exc)


def test_screening_search_config_omits_none_and_binds_current_admission_policy():
    base = {"tier": "0-1", "scale": "silo"}
    search = {**base, **ident.screening_search_config(None)}
    assert search == base and "screening" not in search
    cfg = _cfg(search_config=search)
    assert str(ident.campaign_id(_bound(cfg))) == _T816_REPRESENTATIVE_CAMPAIGN_ID
    assert str(ident.campaign_id(_bound(cfg))) not in {
        _PRE_T343_REPRESENTATIVE_CAMPAIGN_ID,
        _T343_REPRESENTATIVE_CAMPAIGN_ID,
        _T530_REPRESENTATIVE_CAMPAIGN_ID,
    }


def test_screening_search_config_hashes_policy_not_reanchored_measurements():
    sc = _screening()
    entry = ident.screening_search_config(sc)
    assert entry == {"screening": {
        "baseline_ref": "stock-v1", "floor": "0.1", "k": "1.5",
        "high_abort_factor": "2.0"}}
    h0 = ident.campaign_id(_cfg(search_config=entry)).cfg_hash8
    reanchored = _screening(baseline_tps=12345.0, baseline_measured_at=2000.0,
                            baseline_abort_rate=0.04)
    assert ident.campaign_id(_cfg(
        search_config=ident.screening_search_config(reanchored))).cfg_hash8 == h0
    for changed in (_screening(floor=0.11), _screening(k=1.6)):
        assert ident.campaign_id(_cfg(
            search_config=ident.screening_search_config(changed))).cfg_hash8 != h0


def test_screening_float_identity_does_not_collapse_distinct_values():
    for field_name, left, right in (
            ("floor", 0.03000001, 0.03000002),
            ("k", 1.5000001, 1.5000002)):
        a = _screening(**{field_name: left})
        b = _screening(**{field_name: right})
        a_entry = ident.screening_search_config(a)
        b_entry = ident.screening_search_config(b)
        assert a_entry != b_entry
        assert ident.campaign_id(_cfg(search_config=a_entry)).cfg_hash8 != \
            ident.campaign_id(_cfg(search_config=b_entry)).cfg_hash8


def test_screening_none_keeps_representative_legacy_campaign_ids_unchanged():
    """pre-T343/T530 の歴史値を残し、authority-free current ID を固定する。"""
    import dataclasses

    from orchestrator.campaign.backoff_sweep import WORKLOADS as BACKOFF_WORKLOADS
    from orchestrator.campaign.backoff_sweep import config_for as backoff_config
    from orchestrator.campaign.s6_sort_sweep import config_for as s6_config

    workloads = {
        "write-heavy": {"ycsb_zipf_skew": "0.9", "ycsb_rratio": "5", "ycsb_rmw": "0"},
        "balanced": {"ycsb_zipf_skew": "0.9", "ycsb_rratio": "50", "ycsb_rmw": "0"},
        "read-heavy": {"ycsb_zipf_skew": "0.9", "ycsb_rratio": "95", "ycsb_rmw": "0"},
    }
    historical_backoff = {
        _campaign_id_from_historical_preimage(
            f"backoff-sweep-silo-{tag}", "sweep", {
                "spec_content": (
                    f"P2 case study: silo static-backoff sweep — workload={tag}"
                ),
                "ccbench_commit": "dff0f1e",
                "search_tag": "sweep",
                "search_config": {
                    "scale": "silo-backoff", "base": "L-W0",
                    "sweep_us": [2, 5, 10, 25, 50, 100],
                    "workload": tag, "records": 1_000_000, "threads": 48,
                    "ycsb": workload,
                },
                "trial": "p2-backoff",
            },
        )
        for tag, workload in workloads.items()
    }
    assert historical_backoff == _PRE_T343_BACKOFF_CAMPAIGN_IDS

    saved_lookup = ec.lookup
    ec.lookup = lambda _env_tag: _T530_CONTRACT
    try:
        current_policy_kickoff_backoff_cfgs = [
            _bound(dataclasses.replace(
                backoff_config(tag, workload), ccbench_commit="dff0f1e",
            ))
            for tag, workload in BACKOFF_WORKLOADS
        ]
        current_backoff_cfgs = [
            _bound(backoff_config(tag, workload))
            for tag, workload in BACKOFF_WORKLOADS
        ]
        s6_cfgs = [
            _bound(s6_config(tag)) for tag in ("balanced", "write-heavy")
        ]
    finally:
        ec.lookup = saved_lookup
    current_policy_kickoff_backoff = {
        str(ident.campaign_id(cfg))
        for cfg in current_policy_kickoff_backoff_cfgs
    }
    assert (
        current_policy_kickoff_backoff
        == _T816_POLICY_KICKOFF_BACKOFF_CAMPAIGN_IDS
    )
    assert current_policy_kickoff_backoff.isdisjoint(
        _T343_BACKOFF_CAMPAIGN_IDS | _T530_BACKOFF_CAMPAIGN_IDS
    )
    current_backoff = {
        str(ident.campaign_id(cfg)) for cfg in current_backoff_cfgs
    }
    assert current_backoff == _T816_BACKOFF_CAMPAIGN_IDS
    assert current_backoff.isdisjoint(
        _T343_BACKOFF_CAMPAIGN_IDS | _T530_BACKOFF_CAMPAIGN_IDS
    )

    historical_s6 = set()
    for tag in ("balanced", "write-heavy"):
        historical_s6.add(_campaign_id_from_historical_preimage(
            f"p3-s6-sort-sweep-{tag}", "sweep", {
                "spec_content": (
                    "P3 段6前提 (i): sort comparator 空間の機械列挙 sweep (偵察、D44)。"
                    "preliminary = 事前登録外カテゴリ、断定 verdict なし、(c) 判定は出さない。"
                    "空間 = mech-enum-v1: keys{storage_,key_,rcdptr_} x dir{asc,desc} x "
                    "lexicographic-prefix + nosort、全点 SWO-by-construction。"
                    f"workload={tag}。"
                ),
                "ccbench_commit": "d706650",
                "search_tag": "sweep",
                "search_config": {
                    "scale": "silo", "axis": "silo-writeset-sort",
                    "generator": "mech-enum-v1",
                    "space": "keys{S,K,P}xdir{a,d}xprefix+nosort",
                    "workload": tag, "ycsb": workloads[tag],
                    "records": 1_000_000, "threads": 48,
                    "verify": "legacy+s2",
                },
                "trial": "p3-s6-sort-sweep",
            },
        ))
    assert historical_s6 == _PRE_T343_S6_CAMPAIGN_IDS
    # T-816 pin 前進後の current は歴史的 T343/T530 集合と分離する。
    assert {str(ident.campaign_id(cfg)) for cfg in s6_cfgs} == \
        _T816_S6_CAMPAIGN_IDS
    assert {str(ident.campaign_id(cfg)) for cfg in s6_cfgs}.isdisjoint(
        _T343_S6_CAMPAIGN_IDS | _T530_S6_CAMPAIGN_IDS
    )


def test_identity_mismatch_guard():
    cfg = _cfg()
    stored = _certified_lock_text(_bound(cfg))
    ident.verify_against_lock(
        cfg, stored, admission_policy=_BUILD_CONTEXT.policy,
    )
    try:
        ident.verify_against_lock(
            _cfg(spec_content="x"), stored,
            admission_policy=_BUILD_CONTEXT.policy,
        )
        assert False, "should raise IdentityMismatch"
    except ident.IdentityMismatch:
        pass


def test_campaign_lock_requires_exact_admission_policy():
    cfg = _cfg()
    stored = json.loads(ident.canonical_preimage(_bound(cfg)))
    stored["search_config"].pop(ident.ADMISSION_POLICY_SEARCH_KEY)
    forged = build_v2_lock(json.dumps(
        stored, sort_keys=True, separators=(",", ":"),
    ))
    try:
        ident.verify_against_lock(
            cfg, forged, admission_policy=_BUILD_CONTEXT.policy,
        )
        assert False, "admission policy 欠落 lock を拒否すべき"
    except ident.IdentityMismatch as exc:
        assert "admission policy" in str(exc)


@pytest.mark.usefixtures("ratified_enforcement_source")
def test_ensure_campaign_identity_uses_atomic_lock_and_loser_only_verifies():
    cfg = _cfg()
    lay = _layout()
    saved_write_lock = wal.write_lock

    def forbidden_write_lock(*_args, **_kwargs):
        raise AssertionError("非原子 write_lock を呼んではならない")

    wal.write_lock = forbidden_write_lock
    try:
        assert ident.ensure_campaign_identity(
            cfg, lay, admission_policy=_BUILD_CONTEXT.policy,
        ) is True
        assert wal.read_lock(lay) == _certified_lock_text(_bound(cfg))
        assert ident.ensure_campaign_identity(
            cfg, lay, admission_policy=_BUILD_CONTEXT.policy,
        ) is False
    finally:
        wal.write_lock = saved_write_lock


# lock 作成時の active-H 要求は撤回された。真正性検証は admission 側の
# ident.verify_recorded_activation_tuple と、そのテストが担う。


def test_ensure_campaign_identity_propagates_wal_lstat_eio_before_lock():
    cfg = _cfg()
    lay = _layout()
    saved_lstat = wal.os.lstat

    def fail_target(path):
        if os.fspath(path) == os.fspath(lay.wal_file):
            raise OSError(errno.EIO, "injected WAL lstat EIO")
        return saved_lstat(path)

    wal.os.lstat = fail_target
    caught = None
    try:
        try:
            ident.ensure_campaign_identity(
                cfg, lay, admission_policy=_BUILD_CONTEXT.policy,
            )
        except OSError as exc:
            caught = exc
    finally:
        wal.os.lstat = saved_lstat
    assert caught is not None and caught.errno == errno.EIO
    assert not os.path.exists(lay.lock_file)


def test_ensure_campaign_identity_rejects_symlink_and_nonregular_wal_before_lock():
    cfg = _cfg()

    symlinked = _layout(); symlinked.ensure()
    target = os.path.join(symlinked.root, "target")
    with open(target, "wb") as stream:
        stream.write(b"target-bytes")
    os.symlink(target, symlinked.wal_file)
    try:
        ident.ensure_campaign_identity(
            cfg, symlinked, admission_policy=_BUILD_CONTEXT.policy,
        )
        assert False, "symlink WAL を lock 作成前に拒否すべき"
    except OSError as exc:
        assert exc.errno == errno.EINVAL
    assert open(target, "rb").read() == b"target-bytes"
    assert not os.path.exists(symlinked.lock_file)

    nonregular = _layout(); nonregular.ensure()
    os.mkdir(nonregular.wal_file)
    try:
        ident.ensure_campaign_identity(
            cfg, nonregular, admission_policy=_BUILD_CONTEXT.policy,
        )
        assert False, "非 regular WAL を lock 作成前に拒否すべき"
    except OSError as exc:
        assert exc.errno == errno.EINVAL
    assert not os.path.exists(nonregular.lock_file)


def test_ensure_campaign_identity_fstat_rejects_lstat_open_race_to_nonregular():
    cfg = _cfg()
    lay = _layout(); lay.ensure()
    regular = os.path.join(lay.root, "regular-stat-source")
    with open(regular, "wb") as stream:
        stream.write(b"regular")
    os.mkdir(lay.wal_file)
    regular_info = os.lstat(regular)
    real_lstat = wal.os.lstat

    def stale_regular_lstat(path):
        if os.fspath(path) == os.fspath(lay.wal_file):
            return regular_info
        return real_lstat(path)

    wal.os.lstat = stale_regular_lstat
    try:
        try:
            ident.ensure_campaign_identity(
                cfg, lay, admission_policy=_BUILD_CONTEXT.policy,
            )
            assert False, "lstat 後に非 regular へ替わった WAL を fstat で拒否すべき"
        except OSError as exc:
            assert exc.errno == errno.EINVAL
    finally:
        wal.os.lstat = real_lstat
    assert not os.path.exists(lay.lock_file)


def test_ensure_resumable_wal_rejects_missing_lock_with_bytes_unchanged():
    cfg = _cfg()
    lay = _layout(); lay.ensure()
    with open(lay.wal_file, "wb") as stream:
        stream.write(b'{"unowned":true}')
    before = open(lay.wal_file, "rb").read()
    try:
        ident.ensure_resumable_wal(
            cfg, lay, admission_policy=_BUILD_CONTEXT.policy,
        )
        assert False, "lock の無い既存 WAL bytes を拒否すべき"
    except ident.IdentityMismatch as exc:
        assert exc.reason == "missing-lock-with-wal-bytes"
    assert open(lay.wal_file, "rb").read() == before
    assert not os.path.exists(lay.lock_file)
    assert not [name for name in os.listdir(lay.runs_dir)
                if name.startswith("wal-tail-repair-")]


def test_ensure_resumable_wal_lock_mismatch_does_not_repair_bytes():
    stored_cfg = _cfg(spec_content="stored")
    requested_cfg = _cfg(spec_content="requested")
    lay = _layout(); lay.ensure()
    _write_certified_lock(lay, _bound(stored_cfg))
    wal.log(lay, "v", STAGE_BUILD_START, "test")
    with open(lay.wal_file, "ab") as stream:
        stream.write(b"torn-tail")
    before = open(lay.wal_file, "rb").read()
    try:
        ident.ensure_resumable_wal(
            requested_cfg, lay, admission_policy=_BUILD_CONTEXT.policy,
        )
        assert False, "lock mismatch を拒否すべき"
    except ident.IdentityMismatch as exc:
        assert exc.reason == "lock-mismatch"
    assert open(lay.wal_file, "rb").read() == before
    assert not [name for name in os.listdir(lay.runs_dir)
                if name.startswith("wal-tail-repair-")]


# ===== WAL / recovery / atomicity (D, A) =====

def _tmpdir(prefix: str) -> str:
    """テスト用一時 dir。プロセス終了時に後始末する (TMPDIR 配下に leak させない)。"""
    d = tempfile.mkdtemp(prefix=prefix)
    atexit.register(shutil.rmtree, d, ignore_errors=True)
    return d


def _layout():
    return CampaignLayout(root=_tmpdir("izanagi_camp_"))


def test_wal_append_replay():
    lay = _layout(); lay.ensure()
    wal.write_lock(lay, ident.canonical_preimage(_cfg()))
    attempt_id = "wal-append-replay-attempt"
    receipt, receipt_sha = _wal_admission_receipt("v1")
    propagated = {
        "build_attempt_id": attempt_id,
        "build_admission_receipt_sha256": receipt_sha,
    }
    _attempt_start(lay, "v1", attempt_id, receipt, receipt_sha)
    _attempt_stage(
        lay, "v1", STAGE_BUILD_DONE, attempt_id, receipt_sha,
        bin_hash="abc",
    )
    wal.log(lay, "v1", STAGE_VERIFY_DONE, "linux-baremetal", {
        "verdict": "serializable", **propagated,
    })
    _attempt_stage(
        lay, "v1", STAGE_COMMIT, attempt_id, receipt_sha, tps=900000,
    )
    states = wal.replay(lay)
    assert states["v1"].committed
    assert "v1" in wal.terminal_variants(states)
    assert states["v1"].env_tag == "linux-baremetal"


def _wal_admission_receipt(variant_seed: str = "v"):
    genome_value = Genome("silo", {"BACK_OFF": len(variant_seed)})
    admission = _admission_for(genome_value, "deadbeef")
    return admission.as_wal_receipt(), admission.receipt_sha256


def _attempt_start(lay, variant, attempt_id, receipt, receipt_sha):
    wal.log(lay, variant, STAGE_BUILD_START, _T530_CONTRACT.env_tag, {
        "build_attempt_id": attempt_id,
        "build_admission": receipt,
        "build_admission_receipt_sha256": receipt_sha,
    })


def _attempt_stage(lay, variant, stage, attempt_id, receipt_sha, **extra):
    payload = {
        "build_attempt_id": attempt_id,
        "build_admission_receipt_sha256": receipt_sha,
        **extra,
    }
    if stage == STAGE_COMMIT:
        payload["contract_sha256"] = _T530_CONTRACT_SHA256
    if stage == STAGE_COMMIT:
        commit_receipts.log_receipted_commit(
            lay, variant, _T530_CONTRACT.env_tag, payload,
            operation_identity=attempt_id,
        )
    else:
        wal.log(lay, variant, stage, _T530_CONTRACT.env_tag, payload)


def _contract_binding_lock(contract_sha256=_T530_CONTRACT_SHA256):
    lock = json.loads(_certified_lock_text(_cfg()))
    lock["authority"]["environment_contract_sha256"] = contract_sha256
    return lock


def _contract_commit(payload, *, env_tag=None):
    return WalRecord(
        variant="contract-v", stage=STAGE_COMMIT,
        env_tag=env_tag or _T530_CONTRACT.env_tag, ts=1.0,
        payload=payload,
    )


def test_commit_contract_validator_rejects_missing_field_without_defaulting():
    class Payload(dict):
        def __contains__(self, key):
            if key == COMMIT_CONTRACT_SHA256_KEY:
                return True
            return super().__contains__(key)

        def get(self, key, *default):
            if key == COMMIT_CONTRACT_SHA256_KEY:
                return default[0] if default else None
            return super().get(key, *default)

    try:
        wal.validate_commit_contract_bindings(
            [_contract_commit(Payload())],
            campaign_lock=_contract_binding_lock(),
        )
        assert False, "missing contract field を expected 値で補ってはならない"
    except wal.AttemptTopologyError as exc:
        assert "exact lowercase" in str(exc)


def test_commit_contract_requirement_is_derived_from_lock_not_record_presence():
    class Payload(dict):
        def __contains__(self, key):
            if key == COMMIT_CONTRACT_SHA256_KEY:
                return False
            return super().__contains__(key)

        def get(self, key, *default):
            if key == COMMIT_CONTRACT_SHA256_KEY:
                return None
            return super().get(key, *default)

    try:
        wal.validate_commit_contract_bindings(
            [_contract_commit(Payload())],
            campaign_lock=_contract_binding_lock(),
        )
        assert False, "record 欠落から unbound lane を推論してはならない"
    except wal.AttemptTopologyError as exc:
        assert "exact lowercase" in str(exc)


def test_commit_contract_validator_rejects_format_and_hash_mismatch():
    invalid_values = (
        None,
        1,
        _T530_CONTRACT_SHA256.upper(),
        "g" * 64,
        "0" * 63,
    )
    for actual in invalid_values:
        try:
            wal.validate_commit_contract_bindings(
                [_contract_commit({COMMIT_CONTRACT_SHA256_KEY: actual})],
                campaign_lock=_contract_binding_lock(),
            )
            assert False, f"invalid contract_sha256 {actual!r} を拒否すべき"
        except wal.AttemptTopologyError:
            pass
    foreign = ec.GENERATIONS["pegasus"][0].contract.contract_sha256
    try:
        wal.validate_commit_contract_bindings(
            [_contract_commit({COMMIT_CONTRACT_SHA256_KEY: foreign})],
            campaign_lock=_contract_binding_lock(),
        )
        assert False, "lock と異なる valid SHA-256 を拒否すべき"
    except wal.AttemptTopologyError as exc:
        assert "campaign.lock と不一致" in str(exc)


def test_commit_contract_validator_rejects_unknown_ever_active_hash():
    unknown = "0" * 64
    try:
        wal.validate_commit_contract_bindings(
            [_contract_commit({COMMIT_CONTRACT_SHA256_KEY: unknown})],
            campaign_lock=_contract_binding_lock(unknown),
        )
        assert False, "self-consistent でも未知の H を拒否すべき"
    except wal.AttemptTopologyError as exc:
        assert "ever-active" in str(exc)


def test_commit_contract_validator_rejects_contract_env_tag_mismatch():
    try:
        wal.validate_commit_contract_bindings(
            [_contract_commit(
                {COMMIT_CONTRACT_SHA256_KEY: _T530_CONTRACT_SHA256},
                env_tag="pegasus",
            )],
            campaign_lock=_contract_binding_lock(),
        )
        assert False, "contract と COMMIT env_tag の不一致を拒否すべき"
    except wal.AttemptTopologyError as exc:
        assert "env_tag" in str(exc)


def test_commit_contract_projection_ignores_inner_identity_contract_spoof():
    decoded = campaign_lock.decode_campaign_lock(_certified_lock_text(_cfg()))
    identity = dict(decoded.identity)
    identity["search_config"] = {
        **identity["search_config"],
        "environment_contract_sha256": (
            ec.GENERATIONS["pegasus"][0].contract.contract_sha256
        ),
    }
    inner_spoofed = campaign_lock.encode_campaign_lock_v2(
        campaign_lock.canonical_json(identity), decoded.authority,
    )
    wal.validate_commit_contract_bindings(
        [_contract_commit({COMMIT_CONTRACT_SHA256_KEY: _T530_CONTRACT_SHA256})],
        campaign_lock=json.loads(inner_spoofed),
    )


def test_commit_contract_projection_rejects_outer_authority_change():
    foreign = ec.GENERATIONS["pegasus"][0].contract.contract_sha256
    try:
        wal.validate_commit_contract_bindings(
            [_contract_commit({COMMIT_CONTRACT_SHA256_KEY: _T530_CONTRACT_SHA256})],
            campaign_lock=_contract_binding_lock(foreign),
        )
        assert False, "outer authority と COMMIT の不一致を拒否すべき"
    except wal.AttemptTopologyError as exc:
        assert "campaign.lock と不一致" in str(exc)


def test_commit_contract_rejection_precedes_tail_repair_mutation():
    lay = CampaignLayout(root=_tmpdir("t530_contract_tail_order_")).ensure()
    wal.write_lock(lay, campaign_lock.canonical_json(_contract_binding_lock()))
    commit_receipts.log_receipted_commit(
        lay, "contract-v", _T530_CONTRACT.env_tag,
        {COMMIT_CONTRACT_SHA256_KEY: "0" * 64},
    )
    with open(lay.wal_file, "ab") as stream:
        stream.write(b'{"torn":')
    before = open(lay.wal_file, "rb").read()
    files_before = set(os.listdir(lay.runs_dir))
    try:
        wal.repair_truncated_tail(lay)
        assert False, "binding rejection must precede repair writes"
    except wal.AttemptTopologyError:
        pass
    assert open(lay.wal_file, "rb").read() == before
    assert set(os.listdir(lay.runs_dir)) == files_before


def test_contract_rejection_precedes_recovery_abort_and_repair_receipt():
    cfg = _cfg(spec_content="contract rejection precedes every WAL mutation")
    lay = CampaignLayout(root=_tmpdir("t530_contract_recovery_order_")).ensure()
    _write_certified_lock(lay, cfg)
    committed_receipt, committed_sha = _wal_admission_receipt("mismatched")
    _attempt_start(
        lay, "mismatched-v", "mismatched-attempt",
        committed_receipt, committed_sha,
    )
    _attempt_stage(
        lay, "mismatched-v", STAGE_BUILD_DONE,
        "mismatched-attempt", committed_sha,
    )
    commit_receipts.log_receipted_commit(
        lay, "mismatched-v", _T530_CONTRACT.env_tag, {
            "build_attempt_id": "mismatched-attempt",
            "build_admission_receipt_sha256": committed_sha,
            COMMIT_CONTRACT_SHA256_KEY: "0" * 64,
        }, operation_identity="mismatched-attempt",
    )
    receipt, receipt_sha = _wal_admission_receipt("active")
    _attempt_start(lay, "active-v", "active-attempt", receipt, receipt_sha)

    before_recovery = open(lay.wal_file, "rb").read()
    try:
        wal.recover_interrupted_attempts(
            lay, admission_policy=_BUILD_CONTEXT.policy,
        )
        assert False, "contract rejection must precede recovery ABORT"
    except wal.InterruptedAttemptRecoveryError as exc:
        assert exc.condition == "existing-contract-binding-violation"
    assert open(lay.wal_file, "rb").read() == before_recovery
    assert not any(
        record.stage == STAGE_ABORT for record in wal.read_records(lay)
    )

    with open(lay.wal_file, "ab") as stream:
        stream.write(b'{"torn":')
    before_repair = open(lay.wal_file, "rb").read()
    files_before = set(os.listdir(lay.runs_dir))
    try:
        wal.repair_truncated_tail(lay)
        assert False, "contract rejection must precede tail repair receipt"
    except wal.AttemptTopologyError:
        pass
    assert open(lay.wal_file, "rb").read() == before_repair
    assert set(os.listdir(lay.runs_dir)) == files_before


def test_unbound_legacy_and_guided_campaigns_remain_readable():
    legacy = CampaignLayout(root=_tmpdir("t530_legacy_unbound_")).ensure()
    wal.write_lock(legacy, json.dumps({
        "spec_content": "legacy", "ccbench_commit": "old",
        "search_tag": "legacy", "search_config": {}, "trial": None,
    }, sort_keys=True, separators=(",", ":")))
    commit_receipts.append_legacy_raw_commit(
        legacy, "legacy-v", "historical-env", {"fitness_tps": 1.0},
    )
    assert wal.replay(legacy)["legacy-v"].committed

    from orchestrator.campaign import guided, replay

    trial = "fixture"
    meta = {
        "tag": "balanced", "workload": {"ycsb_rratio": "50"},
        "seed": "7", "trial": trial,
    }
    guided_layout = CampaignLayout(
        root=_tmpdir("t530_guided_unbound_")
    ).ensure()
    guided_cfg = guided._trial_config(meta, trial)
    wal.write_lock(guided_layout, ident.canonical_preimage(guided_cfg))
    canonical = genome.space_for("silo").enumerate()[0].canonical()
    guided._log_eval(guided_layout, replay.GenomeResult(
        genome=canonical, flags=replay.parse_flags(canonical),
        fitness_tps=2.0, tps=[2.0], leading_indicators={}, certified=True,
        verification_evidence=commit_receipts.replay_evidence(
            source_variant=canonical,
            source_payload={"fitness_tps": 2.0},
        ),
    ))
    with open(guided_layout.wal_file, "ab") as stream:
        stream.write(b'{"torn":')
    repair = ident.ensure_resumable_wal(
        guided_cfg, guided_layout,
        admission_policy=guided._NO_BUILD_POLICY,
        require_environment_contract=False,
    )
    records, truncated = wal.read_records_checked(guided_layout)
    assert repair.status == "repaired" and truncated is False
    assert records[-1].variant == canonical and records[-1].stage == STAGE_COMMIT


def test_certified_lane_rejects_historical_v1_lock_as_read_only():
    cfg = _cfg(spec_content="historical v1 certified resume")
    historical_v1_lock = ident.canonical_preimage(cfg)
    try:
        ident.verify_against_lock(
            cfg, historical_v1_lock, admission_policy=_BUILD_CONTEXT.policy,
        )
        assert False, "certified lane で historical v1 lock を拒否すべき"
    except ident.IdentityMismatch as exc:
        assert exc.reason == "legacy-lock-read-only"


def _admission_aware_layout(prefix: str):
    lay = CampaignLayout(root=_tmpdir(prefix)).ensure()
    _write_certified_lock(lay, _cfg(spec_content=prefix))
    return lay


def _trigger_admission_layout(prefix: str):
    lay = CampaignLayout(root=_tmpdir(prefix)).ensure()
    search = {
        "tier": "0-1", "scale": "silo",
        "axis": wal.TRIGGER_AXIS, "reflux": "on",
        wal.TRIGGER_BINDING_SCHEMA_MARKER_KEY: trigger_gate_binding.SCHEMA_VERSION,
    }
    _write_certified_lock(lay, _cfg(search_config=search))
    return lay


def _trigger_receipt_and_binding(mask: int = 5):
    receipt, receipt_sha = _wal_admission_receipt("trigger")
    source = receipt["source"]
    binding = trigger_gate_binding.TriggerGateBinding(
        mask=mask,
        predicate_sha256=trigger_gate_binding.expected_predicate_sha256(mask),
        nonce=(f"{mask:x}" * 64)[:64],
        source=trigger_gate_binding.SourceBinding(
            src_token=source["src_token"],
            source_bytes_sha256=source["source_bytes_sha256"],
        ),
    )
    return receipt, receipt_sha, binding


def _write_trigger_attempt(
        lay, *, raw=None, commitment=None, binding_first=True,
        duplicate_binding=False, receipt_bearing=True, abort_extra=None,
        abort_reason="fixture-abort",
):
    attempt_id = "trigger-attempt"
    receipt, receipt_sha, binding = _trigger_receipt_and_binding()
    if not receipt_bearing:
        binding = trigger_gate_binding.TriggerGateBinding(
            mask=binding.mask,
            predicate_sha256=binding.predicate_sha256,
            nonce=binding.nonce,
            source=None,
        )
    raw_payload = {
        "build_attempt_id": attempt_id,
        wal.TRIGGER_BINDING_PAYLOAD_KEY: (
            trigger_gate_binding.to_record(binding) if raw is None else raw
        ),
    }
    start_payload = {
        "build_attempt_id": attempt_id,
        wal.TRIGGER_BINDING_COMMITMENT_KEY: (
            trigger_gate_binding.commitment(binding)
            if commitment is None else commitment
        ),
    }
    abort_payload = {"build_attempt_id": attempt_id, "reason": abort_reason}
    if receipt_bearing:
        start_payload.update({
            "src_token": receipt["source"]["src_token"],
            "build_admission": receipt,
            "build_admission_receipt_sha256": receipt_sha,
        })
        abort_payload["build_admission_receipt_sha256"] = receipt_sha
    abort_payload.update(abort_extra or {})

    def write_binding():
        wal.log(
            lay, "trigger-v", trigger_gate_binding.WAL_RECORD_STAGE, "test-env",
            raw_payload,
        )

    if binding_first:
        write_binding()
    wal.log(lay, "trigger-v", STAGE_BUILD_START, "test-env", start_payload)
    if not binding_first:
        write_binding()
    if duplicate_binding:
        write_binding()
    wal.log(lay, "trigger-v", STAGE_ABORT, "test-env", abort_payload)
    return binding


def _assert_trigger_replay_rejected(lay, expected: str):
    try:
        wal.replay(lay, admission_policy=_BUILD_CONTEXT.policy)
        assert False, "invalid trigger binding campaign を拒否すべき"
    except wal.AttemptTopologyError as exc:
        assert expected in str(exc)


def test_attempt_topology_rejects_cross_attempt_splice():
    lay = _admission_aware_layout("attempt_splice_")
    receipt_a, sha_a = _wal_admission_receipt("a")
    receipt_b, sha_b = _wal_admission_receipt("bb")
    _attempt_start(lay, "v", "attempt-a", receipt_a, sha_a)
    _attempt_start(lay, "v", "attempt-b", receipt_b, sha_b)
    _attempt_stage(lay, "v", STAGE_BUILD_DONE, "attempt-a", sha_a)
    _attempt_stage(lay, "v", STAGE_COMMIT, "attempt-a", sha_a)
    try:
        wal.replay(lay, admission_policy=_BUILD_CONTEXT.policy)
        assert False, "cross-attempt splice を拒否すべき"
    except wal.AttemptTopologyError as exc:
        assert "未終端 attempt" in str(exc)


def test_attempt_topology_accepts_abort_then_retry():
    lay = _admission_aware_layout("attempt_retry_")
    receipt_a, sha_a = _wal_admission_receipt("a")
    receipt_b, sha_b = _wal_admission_receipt("bb")
    _attempt_start(lay, "v", "attempt-a", receipt_a, sha_a)
    _attempt_stage(
        lay, "v", STAGE_ABORT, "attempt-a", sha_a, reason="build-error",
    )
    _attempt_start(lay, "v", "attempt-b", receipt_b, sha_b)
    _attempt_stage(lay, "v", STAGE_BUILD_DONE, "attempt-b", sha_b)
    _attempt_stage(lay, "v", STAGE_COMMIT, "attempt-b", sha_b)
    state = wal.replay(lay, admission_policy=_BUILD_CONTEXT.policy)["v"]
    assert state.committed
    assert state.attempts["attempt-a"].aborted
    assert state.attempts["attempt-b"].committed


def test_attempt_topology_rejects_delayed_verify_signal_after_retry():
    lay = _admission_aware_layout("attempt_delayed_verify_signal_")
    receipt_a, sha_a = _wal_admission_receipt("a")
    receipt_b, sha_b = _wal_admission_receipt("bb")
    _attempt_start(lay, "v", "attempt-a", receipt_a, sha_a)
    _attempt_stage(lay, "v", STAGE_BUILD_DONE, "attempt-a", sha_a)
    _attempt_stage(lay, "v", STAGE_ABORT, "attempt-a", sha_a, reason="build-error")
    _attempt_start(lay, "v", "attempt-b", receipt_b, sha_b)
    _attempt_stage(lay, "v", STAGE_BUILD_DONE, "attempt-b", sha_b)
    _attempt_stage(lay, "v", STAGE_COMMIT, "attempt-b", sha_b)

    # The old attempt's correctness signal arrives after the retry committed.
    _attempt_stage(
        lay, "v", STAGE_VERIFY_DONE, "attempt-a", sha_a,
        verdict="serializable", certified=True, workload={"tag": "legacy"},
    )
    with pytest.raises(wal.AttemptTopologyError, match="active attempt"):
        wal.replay(lay, admission_policy=_BUILD_CONTEXT.policy)


def test_attempt_topology_rejects_delayed_bench_signal_after_retry():
    lay = _admission_aware_layout("attempt_delayed_bench_signal_")
    receipt_a, sha_a = _wal_admission_receipt("a")
    receipt_b, sha_b = _wal_admission_receipt("bb")
    _attempt_start(lay, "v", "attempt-a", receipt_a, sha_a)
    _attempt_stage(lay, "v", STAGE_BUILD_DONE, "attempt-a", sha_a)
    _attempt_stage(lay, "v", STAGE_ABORT, "attempt-a", sha_a, reason="build-error")
    _attempt_start(lay, "v", "attempt-b", receipt_b, sha_b)
    _attempt_stage(lay, "v", STAGE_BUILD_DONE, "attempt-b", sha_b)
    _attempt_stage(lay, "v", STAGE_COMMIT, "attempt-b", sha_b)

    # Keep this fixture bench-only so the bench topology branch is exercised.
    _attempt_stage(
        lay, "v", STAGE_BENCH_DONE, "attempt-a", sha_a,
        median_tps=1.0, cv=0.1, tps=[1.0],
    )
    with pytest.raises(wal.AttemptTopologyError, match="active attempt"):
        wal.replay(lay, admission_policy=_BUILD_CONTEXT.policy)


def test_attempt_topology_rejects_verify_before_build_done():
    """M-B: verify_done は同一 active attempt の build_done 後に限る。"""
    lay = _admission_aware_layout("attempt_verify_before_build_done_")
    receipt, receipt_sha = _wal_admission_receipt("a")
    attempt_id = "attempt-a"
    _attempt_start(lay, "v", attempt_id, receipt, receipt_sha)
    _attempt_stage(
        lay, "v", STAGE_VERIFY_DONE, attempt_id, receipt_sha,
        verdict="serializable", certified=True, workload={"tag": "legacy"},
    )

    with pytest.raises(
            wal.AttemptTopologyError,
            match="build_done より前の attempt に属する",
    ):
        wal.replay(lay, admission_policy=_BUILD_CONTEXT.policy)


def test_attempt_topology_rejects_duplicate_bench_within_attempt():
    """M-C: 同一 active attempt の bench_done は一度だけ受理する。"""
    lay = _admission_aware_layout("attempt_duplicate_bench_")
    receipt, receipt_sha = _wal_admission_receipt("a")
    attempt_id = "attempt-a"
    _attempt_start(lay, "v", attempt_id, receipt, receipt_sha)
    _attempt_stage(lay, "v", STAGE_BUILD_DONE, attempt_id, receipt_sha)
    for median_tps in (1.0, 2.0):
        _attempt_stage(
            lay, "v", STAGE_BENCH_DONE, attempt_id, receipt_sha,
            median_tps=median_tps, cv=0.1, tps=[median_tps],
        )

    with pytest.raises(
            wal.AttemptTopologyError,
            match="bench_done: 同一 attempt で重複",
    ):
        wal.replay(lay, admission_policy=_BUILD_CONTEXT.policy)


def test_attempt_topology_rejects_receipt_sha_reuse_on_active_signal():
    for signal_stage in (STAGE_VERIFY_DONE, STAGE_BENCH_DONE):
        lay = _admission_aware_layout(
            f"attempt_receipt_reuse_signal_{signal_stage}_"
        )
        receipt_a, sha_a = _wal_admission_receipt("a")
        receipt_b, sha_b = _wal_admission_receipt("bb")
        assert sha_a != sha_b
        _attempt_start(lay, "v", "attempt-a", receipt_a, sha_a)
        _attempt_stage(lay, "v", STAGE_BUILD_DONE, "attempt-a", sha_a)
        _attempt_stage(lay, "v", STAGE_ABORT, "attempt-a", sha_a, reason="build-error")
        _attempt_start(lay, "v", "attempt-b", receipt_b, sha_b)
        _attempt_stage(lay, "v", STAGE_BUILD_DONE, "attempt-b", sha_b)

        # The attempt ID is current; only the receipt SHA is stale.
        payload = {
            "build_attempt_id": "attempt-b",
            "build_admission_receipt_sha256": sha_a,
        }
        if signal_stage == STAGE_VERIFY_DONE:
            payload.update({
                "verdict": "serializable", "certified": True,
                "workload": {"tag": "legacy"},
            })
        else:
            payload.update({"median_tps": 1.0, "cv": 0.1, "tps": [1.0]})
        wal.log(lay, "v", signal_stage, _T530_CONTRACT.env_tag, payload)

        with pytest.raises(wal.AttemptTopologyError, match="receipt SHA"):
            wal.replay(lay, admission_policy=_BUILD_CONTEXT.policy)


def test_attempt_topology_rejects_delayed_signal_from_finished_same_variant_attempt():
    """これは終了済み attempt の遅延 signal の実証であり、真の並行 peer の実証ではない。"""
    lay = _admission_aware_layout("attempt_finished_peer_signal_")
    receipt_a, sha_a = _wal_admission_receipt("a")
    receipt_b, sha_b = _wal_admission_receipt("bb")
    _attempt_start(lay, "v", "attempt-a", receipt_a, sha_a)
    _attempt_stage(lay, "v", STAGE_BUILD_DONE, "attempt-a", sha_a)
    _attempt_stage(lay, "v", STAGE_ABORT, "attempt-a", sha_a, reason="build-error")
    _attempt_start(lay, "v", "attempt-b", receipt_b, sha_b)
    _attempt_stage(lay, "v", STAGE_BUILD_DONE, "attempt-b", sha_b)

    _attempt_stage(
        lay, "v", STAGE_VERIFY_DONE, "attempt-a", sha_a,
        verdict="serializable", certified=True, workload={"tag": "legacy"},
    )
    _attempt_stage(
        lay, "v", STAGE_BENCH_DONE, "attempt-a", sha_a,
        median_tps=1.0, cv=0.1, tps=[1.0],
    )
    with pytest.raises(wal.AttemptTopologyError, match="active attempt"):
        wal.replay(lay, admission_policy=_BUILD_CONTEXT.policy)


def test_attempt_topology_accepts_pipeline_signal_shape_without_receipt_sha():
    lay = _admission_aware_layout("attempt_pipeline_signal_shape_")
    receipt, receipt_sha = _wal_admission_receipt("a")
    attempt_id = "attempt-pipeline-shape"
    _attempt_start(lay, "v", attempt_id, receipt, receipt_sha)
    _attempt_stage(lay, "v", STAGE_BUILD_DONE, attempt_id, receipt_sha)

    # These are the production verify/bench key shapes: attempt-bound, with
    # no build_admission_receipt_sha256 on either signal.
    wal.log(lay, "v", STAGE_VERIFY_DONE, _T530_CONTRACT.env_tag, {
        "build_attempt_id": attempt_id,
        "verdict": "serializable", "certified": True,
        "commits": 1, "aborts": 0,
        "commit_witness": {"commit_counts": 1, "batch_commit_counts": 0},
        "anomalies": 0, "workload": {"tag": "legacy"},
    })
    wal.log(lay, "v", STAGE_BENCH_DONE, _T530_CONTRACT.env_tag, {
        "build_attempt_id": attempt_id,
        "median_tps": 100.0, "cv": 0.1, "bench_wall_s": 0.1,
        "high_variance": False, "unstable": False, "rounds": 1,
        "cv_history": [0.1], "tps": [100.0], "settled": True,
        "leading_indicators": {}, "rep_notes": [], "run_cmd": ["fake"],
    })

    state = wal.replay(lay, admission_policy=_BUILD_CONTEXT.policy)["v"]
    assert state.attempts[attempt_id].stages_seen == [
        STAGE_BUILD_START, STAGE_BUILD_DONE,
        STAGE_VERIFY_DONE, STAGE_BENCH_DONE,
    ]


def test_replay_committed_projection_excludes_prior_aborted_attempt_signals():
    lay = _admission_aware_layout("attempt_committed_projection_retry_")
    receipt_a, sha_a = _wal_admission_receipt("a")
    receipt_b, sha_b = _wal_admission_receipt("bb")
    _attempt_start(lay, "v", "attempt-a", receipt_a, sha_a)
    _attempt_stage(lay, "v", STAGE_BUILD_DONE, "attempt-a", sha_a)
    _attempt_stage(
        lay, "v", STAGE_VERIFY_DONE, "attempt-a", sha_a,
        verdict="serializable", certified=True, workload={"tag": "legacy"},
    )
    _attempt_stage(
        lay, "v", STAGE_BENCH_DONE, "attempt-a", sha_a,
        median_tps=1.0, cv=0.1, tps=[1.0],
    )
    _attempt_stage(lay, "v", STAGE_ABORT, "attempt-a", sha_a, reason="build-error")

    _attempt_start(lay, "v", "attempt-b", receipt_b, sha_b)
    _attempt_stage(lay, "v", STAGE_BUILD_DONE, "attempt-b", sha_b)
    _attempt_stage(
        lay, "v", STAGE_VERIFY_DONE, "attempt-b", sha_b,
        verdict="serializable", certified=True, workload={"tag": "legacy"},
    )
    _attempt_stage(
        lay, "v", STAGE_BENCH_DONE, "attempt-b", sha_b,
        median_tps=2.0, cv=0.1, tps=[2.0],
    )
    _attempt_stage(lay, "v", STAGE_COMMIT, "attempt-b", sha_b)

    state = wal.replay(lay, admission_policy=_BUILD_CONTEXT.policy)["v"]
    assert state.committed_attempt_id == "attempt-b"
    assert state.committed_build_start is not None
    assert state.committed_build_start.payload["build_attempt_id"] == "attempt-b"
    assert [
        record.payload["build_attempt_id"]
        for record in state.committed_verify
    ] == ["attempt-b"]
    assert state.committed_bench is not None
    assert state.committed_bench.payload["build_attempt_id"] == "attempt-b"
    assert all(
        record.payload["build_attempt_id"] != "attempt-a"
        for record in state.committed_verify
    )
    assert state.committed_bench.payload["median_tps"] == 2.0


def _active_receiptful_attempt(lay, variant: str, attempt_id: str):
    receipt, receipt_sha = _wal_admission_receipt(attempt_id)
    _attempt_start(lay, variant, attempt_id, receipt, receipt_sha)
    return receipt, receipt_sha


def test_resumable_wal_rejects_truncated_tail_with_active_attempt_before_repair():
    for case in ("lf-missing-verify", "signal-then-torn"):
        cfg = _cfg(spec_content=f"truncated-active-{case}")
        lay = CampaignLayout(root=_tmpdir(f"recovery_tail_{case}_")).ensure()
        _write_certified_lock(lay, cfg)
        _receipt, receipt_sha = _active_receiptful_attempt(
            lay, "tail-v", f"attempt-{case}",
        )
        _attempt_stage(
            lay, "tail-v", STAGE_BUILD_DONE, f"attempt-{case}", receipt_sha,
        )
        signal = WalRecord(
            variant="tail-v", stage=STAGE_VERIFY_DONE, env_tag="test-env",
            ts=3.0, payload={"verdict": "red", "certified": False},
        )
        if case == "lf-missing-verify":
            with open(lay.wal_file, "ab") as stream:
                stream.write(wal._record_to_line(signal).encode("utf-8"))
        else:
            wal.append(lay, signal)
            with open(lay.wal_file, "ab") as stream:
                stream.write(b'{"torn":')
        before = open(lay.wal_file, "rb").read()
        runs_before = set(os.listdir(lay.runs_dir))

        try:
            ident.ensure_resumable_wal(
                cfg, lay, admission_policy=_BUILD_CONTEXT.policy,
            )
            assert False, "active attempt と truncated tail の併存を拒否すべき"
        except wal.InterruptedAttemptRecoveryError as exc:
            assert exc.condition == "truncated-tail-with-active-attempt"
            assert exc.variant == "tail-v"
        assert open(lay.wal_file, "rb").read() == before
        assert set(os.listdir(lay.runs_dir)) == runs_before


def _assert_recovery_blocked(lay, condition: str):
    before = open(lay.wal_file, "rb").read()
    try:
        wal.recover_interrupted_attempts(
            lay, admission_policy=_BUILD_CONTEXT.policy,
        )
        assert False, f"{condition} recovery を fail-closed に拒否すべき"
    except wal.InterruptedAttemptRecoveryError as exc:
        assert exc.condition == condition
        assert exc.variant and exc.attempt_id and exc.attempt_ids
    assert open(lay.wal_file, "rb").read() == before


def test_recovery_payload_receipt_matrix_is_exact_and_retryable():
    lay = _admission_aware_layout("recovery_payload_matrix_")
    wal.log(lay, "receiptless-v", STAGE_BUILD_START, "old-env", {
        "build_attempt_id": "receiptless-attempt",
    })
    _receipt, receipt_sha = _active_receiptful_attempt(
        lay, "receiptful-v", "receiptful-attempt",
    )
    prefix = open(lay.wal_file, "rb").read()

    recovered = wal.recover_interrupted_attempts(
        lay, admission_policy=_BUILD_CONTEXT.policy,
    )
    assert len(recovered) == 2
    by_variant = {record.variant: record for record in recovered}
    assert by_variant["receiptless-v"].payload == {
        "reason": "recovery-abort-incomplete-attempt",
        "build_attempt_id": "receiptless-attempt",
    }
    assert by_variant["receiptful-v"].payload == {
        "reason": "recovery-abort-incomplete-attempt",
        "build_attempt_id": "receiptful-attempt",
        "build_admission_receipt_sha256": receipt_sha,
    }
    assert by_variant["receiptless-v"].env_tag == "old-env"
    assert open(lay.wal_file, "rb").read().startswith(prefix)
    states = wal.replay(lay, admission_policy=_BUILD_CONTEXT.policy)
    assert states["receiptless-v"].retryable_abort
    assert states["receiptful-v"].retryable_abort


def test_recovery_fail_closed_after_verify_or_bench_signal():
    for signal in (STAGE_VERIFY_DONE, STAGE_BENCH_DONE):
        lay = _admission_aware_layout(f"recovery_signal_{signal}_")
        _active_receiptful_attempt(lay, "signal-v", f"attempt-{signal}")
        wal.log(lay, "signal-v", signal, "test-env", {"signal": True})
        _assert_recovery_blocked(lay, "signal-after-start")


def test_recovery_fail_closed_after_build_done_but_accepts_start_only():
    blocked = _admission_aware_layout("recovery_build_done_")
    _receipt, receipt_sha = _active_receiptful_attempt(
        blocked, "built-v", "built-attempt",
    )
    _attempt_stage(
        blocked, "built-v", STAGE_BUILD_DONE, "built-attempt", receipt_sha,
    )
    _assert_recovery_blocked(blocked, "attempt-record-after-start")

    accepted = _admission_aware_layout("recovery_start_only_")
    _active_receiptful_attempt(accepted, "building-v", "building-attempt")
    recovered = wal.recover_interrupted_attempts(
        accepted, admission_policy=_BUILD_CONTEXT.policy,
    )
    assert len(recovered) == 1
    assert recovered[0].payload["build_attempt_id"] == "building-attempt"


def test_recovery_api_requires_matching_post_policy_lock_without_mutating_wal():
    missing = CampaignLayout(root=_tmpdir("recovery_missing_lock_")).ensure()
    wal.log(missing, "missing-lock-v", STAGE_BUILD_START, "test-env", {
        "build_attempt_id": "missing-lock-attempt",
    })
    _assert_recovery_blocked(missing, "admission-policy-lock-mismatch")

    legacy = CampaignLayout(root=_tmpdir("recovery_legacy_lock_")).ensure()
    wal.write_lock(legacy, json.dumps({
        "spec_content": "legacy", "ccbench_commit": "deadbeef",
        "search_tag": "legacy", "search_config": {}, "trial": "legacy",
    }, sort_keys=True, separators=(",", ":")))
    wal.log(legacy, "legacy-lock-v", STAGE_BUILD_START, "test-env", {
        "build_attempt_id": "legacy-lock-attempt",
    })
    _assert_recovery_blocked(legacy, "admission-policy-lock-mismatch")


def test_recovery_fail_closed_for_trigger_lock_or_attempt_commitment():
    machine_search = {
        "tier": "0-1", "scale": "silo", "axis": wal.TRIGGER_AXIS,
        "generator": "reason-subset-v1",
        "space": "reason-subsets(effective)+identall+stock",
    }
    machine = CampaignLayout(root=_tmpdir("recovery_trigger_machine_")).ensure()
    _write_certified_lock(machine, _cfg(search_config=machine_search))
    _active_receiptful_attempt(machine, "machine-v", "machine-attempt")
    _assert_recovery_blocked(machine, "trigger-campaign")

    proposal = _trigger_admission_layout("recovery_trigger_commitment_")
    receipt, receipt_sha, binding = _trigger_receipt_and_binding()
    attempt_id = "proposal-attempt"
    commitment = wal.log_trigger_binding(
        proposal, "proposal-v", "test-env", attempt_id, binding,
    )
    wal.log(proposal, "proposal-v", STAGE_BUILD_START, "test-env", {
        "build_attempt_id": attempt_id,
        "src_token": receipt["source"]["src_token"],
        "build_admission": receipt,
        "build_admission_receipt_sha256": receipt_sha,
        wal.TRIGGER_BINDING_COMMITMENT_KEY: commitment,
    })
    _assert_recovery_blocked(proposal, "trigger-campaign")


def test_recovery_exhaustion_is_byte_stable():
    lay = _admission_aware_layout("recovery_exhausted_")
    for index in range(wal.INCOMPLETE_ATTEMPT_RECOVERY_LIMIT):
        attempt_id = f"recovered-{index}"
        _receipt, receipt_sha = _active_receiptful_attempt(
            lay, "exhausted-v", attempt_id,
        )
        _attempt_stage(
            lay, "exhausted-v", STAGE_ABORT, attempt_id, receipt_sha,
            reason="recovery-abort-incomplete-attempt",
        )
    _active_receiptful_attempt(lay, "exhausted-v", "active-after-limit")
    _assert_recovery_blocked(lay, "recovery-exhausted")


def test_recovery_invalid_topology_and_multiple_active_are_byte_stable():
    invalid = _admission_aware_layout("recovery_invalid_topology_")
    _receipt, receipt_sha = _active_receiptful_attempt(
        invalid, "invalid-history-v", "invalid-history-attempt",
    )
    _attempt_stage(
        invalid, "invalid-history-v", STAGE_BUILD_DONE,
        "invalid-history-attempt",
        "f" * 64,
    )
    assert receipt_sha != "f" * 64
    _attempt_stage(
        invalid, "invalid-history-v", STAGE_ABORT,
        "invalid-history-attempt", receipt_sha, reason="build-error",
    )
    _active_receiptful_attempt(
        invalid, "recoverable-v", "recoverable-attempt",
    )
    _assert_recovery_blocked(invalid, "existing-topology-violation")

    multiple = _admission_aware_layout("recovery_multiple_active_")
    _active_receiptful_attempt(multiple, "multiple-v", "attempt-a")
    _active_receiptful_attempt(multiple, "multiple-v", "attempt-b")
    _assert_recovery_blocked(multiple, "multiple-active-attempts")


def test_recovery_schema_detection_noops_only_without_attempt_keys():
    lay = _admission_aware_layout("recovery_schema_noop_")
    wal.log(lay, "guided-v", STAGE_BUILD_START, "test-env", {
        "fixture": "no attempt-schema key",
    })
    before = open(lay.wal_file, "rb").read()
    assert wal.recover_interrupted_attempts(
        lay, admission_policy=_BUILD_CONTEXT.policy,
    ) == []
    assert open(lay.wal_file, "rb").read() == before

    marker_on_non_start = _admission_aware_layout(
        "recovery_schema_non_start_marker_"
    )
    wal.log(marker_on_non_start, "marked-v", STAGE_BUILD_DONE, "test-env", {
        "build_attempt_id": "orphan-build-done",
        "build_admission_receipt_sha256": "a" * 64,
    })
    _assert_recovery_blocked(
        marker_on_non_start, "existing-topology-violation",
    )


def test_concurrent_recovery_appends_one_terminal_abort():
    lay = _admission_aware_layout("recovery_concurrent_")
    _active_receiptful_attempt(lay, "concurrent-v", "concurrent-attempt")
    barrier = threading.Barrier(3)
    results = []
    failures = []

    def recover():
        barrier.wait()
        try:
            results.append(wal.recover_interrupted_attempts(
                lay, admission_policy=_BUILD_CONTEXT.policy,
            ))
        except BaseException as exc:  # test worker must surface every failure
            failures.append(exc)

    workers = [threading.Thread(target=recover) for _ in range(2)]
    for worker in workers:
        worker.start()
    barrier.wait()
    for worker in workers:
        worker.join()
    assert failures == []
    assert sorted(len(result) for result in results) == [0, 1]
    recovery_aborts = [
        record for record in wal.read_records(lay)
        if record.stage == STAGE_ABORT
        and record.payload.get("reason")
        == "recovery-abort-incomplete-attempt"
    ]
    assert len(recovery_aborts) == 1


def test_recovery_waits_for_external_exclusive_wal_lock():
    lay = _admission_aware_layout("recovery_external_lock_")
    _active_receiptful_attempt(lay, "locked-v", "locked-attempt")
    holder_fd = os.open(lay.wal_file, os.O_RDWR | os.O_CLOEXEC)
    fcntl.flock(holder_fd, fcntl.LOCK_EX)
    started = threading.Event()
    finished = threading.Event()
    results = []
    failures = []

    def recover():
        started.set()
        try:
            results.append(wal.recover_interrupted_attempts(
                lay, admission_policy=_BUILD_CONTEXT.policy,
            ))
        except BaseException as exc:
            failures.append(exc)
        finally:
            finished.set()

    worker = threading.Thread(target=recover)
    worker.start()
    try:
        assert started.wait(1.0), "recovery worker が開始しなかった"
        assert not finished.wait(1.0), "外部 LOCK_EX 保持中に recovery が進んだ"
    finally:
        fcntl.flock(holder_fd, fcntl.LOCK_UN)
        os.close(holder_fd)
    worker.join(2.0)
    assert not worker.is_alive()
    assert failures == []
    assert len(results) == 1 and len(results[0]) == 1


def test_trigger_binding_canonical_fixture_replays_and_records_by_stage_validates():
    lay = _trigger_admission_layout("trigger_binding_positive_")
    binding = _write_trigger_attempt(lay)
    state = wal.replay(lay, admission_policy=_BUILD_CONTEXT.policy)["trigger-v"]
    assert state.aborted and state.attempts["trigger-attempt"].aborted
    by_stage = wal.records_by_stage(lay, "trigger-v")
    assert by_stage[STAGE_BUILD_START][wal.TRIGGER_BINDING_COMMITMENT_KEY] == \
        trigger_gate_binding.commitment(binding)
    assert trigger_gate_binding.WAL_RECORD_STAGE not in by_stage


def test_trigger_binding_replay_rejects_missing_binding_and_records_bypass():
    lay = _trigger_admission_layout("trigger_binding_missing_")
    receipt, receipt_sha, binding = _trigger_receipt_and_binding()
    wal.log(lay, "trigger-v", STAGE_BUILD_START, "test-env", {
        "build_attempt_id": "trigger-attempt",
        "src_token": receipt["source"]["src_token"],
        "build_admission": receipt,
        "build_admission_receipt_sha256": receipt_sha,
        wal.TRIGGER_BINDING_COMMITMENT_KEY: trigger_gate_binding.commitment(binding),
    })
    wal.log(lay, "trigger-v", STAGE_ABORT, "test-env", {
        "build_attempt_id": "trigger-attempt",
        "build_admission_receipt_sha256": receipt_sha,
        "reason": "fixture-abort",
    })
    _assert_trigger_replay_rejected(lay, "一対一")
    try:
        wal.records_by_stage(lay, "trigger-v")
        assert False, "records_by_stage が binding 検証を迂回した"
    except wal.AttemptTopologyError as exc:
        assert "一対一" in str(exc)


def test_trigger_binding_replay_rejects_mask_or_predicate_sha_single_tamper():
    for field in ("mask", "predicate_sha256"):
        lay = _trigger_admission_layout(f"trigger_binding_{field}_")
        _receipt, _sha, binding = _trigger_receipt_and_binding()
        raw = trigger_gate_binding.to_record(binding)
        raw[field] = (binding.mask + 1) % 32 if field == "mask" else "f" * 64
        _write_trigger_attempt(lay, raw=raw)
        _assert_trigger_replay_rejected(lay, "record が不正")


def test_trigger_binding_replay_rejects_source_and_commitment_mismatch():
    source_lay = _trigger_admission_layout("trigger_binding_source_mismatch_")
    _receipt, _sha, binding = _trigger_receipt_and_binding()
    raw = trigger_gate_binding.to_record(binding)
    raw["source"]["source_bytes_sha256"] = "e" * 64
    tampered_binding = trigger_gate_binding.validate_record(raw, require_source=True)
    _write_trigger_attempt(
        source_lay, raw=raw,
        commitment=trigger_gate_binding.commitment(tampered_binding),
    )
    _assert_trigger_replay_rejected(source_lay, "source が receipt/WAL と不一致")

    commitment_lay = _trigger_admission_layout("trigger_binding_commitment_mismatch_")
    _write_trigger_attempt(commitment_lay, commitment="0" * 64)
    _assert_trigger_replay_rejected(commitment_lay, "commitment")


def test_trigger_binding_replay_rejects_duplicate_and_late_record():
    duplicate = _trigger_admission_layout("trigger_binding_duplicate_")
    _write_trigger_attempt(duplicate, duplicate_binding=True)
    _assert_trigger_replay_rejected(duplicate, "重複")

    late = _trigger_admission_layout("trigger_binding_late_")
    _write_trigger_attempt(late, binding_first=False)
    _assert_trigger_replay_rejected(late, "順序")


def test_trigger_binding_replay_rejects_interposed_record():
    lay = _trigger_admission_layout("trigger_binding_interposed_")
    receipt, receipt_sha, binding = _trigger_receipt_and_binding()
    attempt_id = "interposed-attempt"
    raw = WalRecord(
        variant="trigger-v", stage=trigger_gate_binding.WAL_RECORD_STAGE,
        env_tag="test-env", ts=1.0,
        payload={
            "build_attempt_id": attempt_id,
            wal.TRIGGER_BINDING_PAYLOAD_KEY:
                trigger_gate_binding.to_record(binding),
        },
    )
    interposed = WalRecord(
        variant="other-v", stage=STAGE_S1_SESSION, env_tag="test-env",
        ts=2.0, payload={},
    )
    start = WalRecord(
        variant="trigger-v", stage=STAGE_BUILD_START, env_tag="test-env",
        ts=3.0,
        payload={
            "build_attempt_id": attempt_id,
            "src_token": receipt["source"]["src_token"],
            "build_admission": receipt,
            "build_admission_receipt_sha256": receipt_sha,
            wal.TRIGGER_BINDING_COMMITMENT_KEY:
                trigger_gate_binding.commitment(binding),
        },
    )
    try:
        wal.validate_trigger_bindings(
            [raw, interposed, start],
            campaign_lock=json.loads(wal.read_lock(lay)),
        )
        assert False, "binding と build_start の interposition を拒否すべき"
    except wal.AttemptTopologyError as exc:
        assert "順序" in str(exc)


def test_trigger_binding_fsync_before_start_recovers_to_abort_tombstone():
    lay = _trigger_admission_layout("trigger_binding_orphan_recovery_")
    _receipt, _receipt_sha, binding = _trigger_receipt_and_binding(mask=6)
    raw = WalRecord(
        variant="trigger-v", stage=trigger_gate_binding.WAL_RECORD_STAGE,
        env_tag="test-env", ts=1.0,
        payload={
            "build_attempt_id": "orphan-attempt",
            wal.TRIGGER_BINDING_PAYLOAD_KEY:
                trigger_gate_binding.to_record(binding),
        },
    )
    lock = json.loads(wal.read_lock(lay))
    assert wal.validate_trigger_bindings([raw], campaign_lock=lock) == {}
    try:
        wal.validate_trigger_bindings(
            [raw, WalRecord(
                variant="other-v", stage=STAGE_S1_SESSION,
                env_tag="test-env", ts=2.0, payload={},
            )],
            campaign_lock=lock,
        )
        assert False, "末尾以外の orphan binding を拒否すべき"
    except wal.AttemptTopologyError as exc:
        assert "一対一" in str(exc)

    wal.append(lay, raw)
    states = wal.replay(lay, admission_policy=_BUILD_CONTEXT.policy)
    recovered = wal.read_records(lay)
    assert [record.stage for record in recovered] == [
        trigger_gate_binding.WAL_RECORD_STAGE, STAGE_ABORT,
    ]
    assert recovered[-1].payload == {
        "build_attempt_id": "orphan-attempt",
        "reason": "recovery-abort-trigger-binding-orphan",
    }
    assert states["trigger-v"].resumable
    wal.replay(lay, admission_policy=_BUILD_CONTEXT.policy)
    assert len(wal.read_records(lay)) == 2

    _write_trigger_attempt(lay)
    retried = wal.replay(lay, admission_policy=_BUILD_CONTEXT.policy)["trigger-v"]
    assert retried.aborted
    assert retried.attempts["trigger-attempt"].aborted


def test_trigger_binding_receiptless_attempt_rejects_verify_payload():
    positive = _trigger_admission_layout("trigger_binding_source_null_positive_")
    _write_trigger_attempt(
        positive, receipt_bearing=False, abort_reason="identity-error",
    )
    assert wal.replay(
        positive, admission_policy=_BUILD_CONTEXT.policy,
    )["trigger-v"].aborted

    lay = _trigger_admission_layout("trigger_binding_source_null_verify_")
    _write_trigger_attempt(
        lay, receipt_bearing=False, abort_extra={"verify": {"certified": False}},
    )
    _assert_trigger_replay_rejected(lay, "verify payload")

    stage_lay = _trigger_admission_layout("trigger_binding_source_null_stage_")
    _receipt, _sha, source_binding = _trigger_receipt_and_binding()
    candidate = trigger_gate_binding.TriggerGateBinding(
        mask=source_binding.mask,
        predicate_sha256=source_binding.predicate_sha256,
        nonce=source_binding.nonce,
        source=None,
    )
    wal.log_trigger_binding(
        stage_lay, "trigger-v", "test-env", "trigger-attempt", candidate,
    )
    wal.log(stage_lay, "trigger-v", STAGE_BUILD_START, "test-env", {
        "build_attempt_id": "trigger-attempt",
        wal.TRIGGER_BINDING_COMMITMENT_KEY: trigger_gate_binding.commitment(candidate),
    })
    wal.log(stage_lay, "trigger-v", STAGE_VERIFY_DONE, "test-env", {
        "certified": False,
    })
    wal.log(stage_lay, "trigger-v", STAGE_ABORT, "test-env", {
        "build_attempt_id": "trigger-attempt", "reason": "fixture-abort",
    })
    _assert_trigger_replay_rejected(stage_lay, "build/verify/bench/commit")


def test_attempt_topology_rejects_duplicate_start():
    lay = _admission_aware_layout("attempt_duplicate_")
    receipt, receipt_sha = _wal_admission_receipt()
    _attempt_start(lay, "v", "attempt-a", receipt, receipt_sha)
    _attempt_start(lay, "v", "attempt-a", receipt, receipt_sha)
    try:
        wal.replay(lay, admission_policy=_BUILD_CONTEXT.policy)
        assert False, "duplicate START を拒否すべき"
    except wal.AttemptTopologyError as exc:
        assert "duplicate attempt id" in str(exc)


def test_attempt_topology_rejects_receipt_sha_reuse_from_other_attempt():
    lay = _admission_aware_layout("attempt_receipt_reuse_")
    receipt_a, sha_a = _wal_admission_receipt("a")
    receipt_b, sha_b = _wal_admission_receipt("bb")
    _attempt_start(lay, "v", "attempt-a", receipt_a, sha_a)
    _attempt_stage(lay, "v", STAGE_ABORT, "attempt-a", sha_a, reason="build-error")
    _attempt_start(lay, "v", "attempt-b", receipt_b, sha_b)
    _attempt_stage(lay, "v", STAGE_BUILD_DONE, "attempt-b", sha_a)
    try:
        wal.replay(lay, admission_policy=_BUILD_CONTEXT.policy)
        assert False, "別 attempt receipt SHA 流用を拒否すべき"
    except wal.AttemptTopologyError as exc:
        assert "receipt SHA" in str(exc)


def test_resume_rejects_committed_attempt_without_receipt():
    lay = _admission_aware_layout("attempt_receiptless_commit_")
    wal.log(lay, "v", STAGE_BUILD_START, _T530_CONTRACT.env_tag, {
        "build_attempt_id": "attempt-a",
    })
    wal.log(lay, "v", STAGE_BUILD_DONE, _T530_CONTRACT.env_tag, {
        "build_attempt_id": "attempt-a",
        "build_admission_receipt_sha256": "1" * 64,
    })
    commit_receipts.append_legacy_raw_commit(
        lay, "v", _T530_CONTRACT.env_tag, {
        "build_attempt_id": "attempt-a",
        "build_admission_receipt_sha256": "1" * 64,
        COMMIT_CONTRACT_SHA256_KEY: _T530_CONTRACT_SHA256,
        },
    )
    try:
        wal.replay(lay, admission_policy=_BUILD_CONTEXT.policy)
        assert False, "receiptless committed attempt を拒否すべき"
    except wal.AttemptTopologyError as exc:
        assert "receiptless pre-build attempt" in str(exc)


def test_wal_atomicity_uncommitted_is_resumable():
    lay = _layout(); lay.ensure()
    # build まで進んで crash (commit 無し) = half-evaluated
    wal.log(lay, "v2", STAGE_BUILD_START, "linux-baremetal")
    wal.log(lay, "v2", STAGE_BUILD_DONE, "linux-baremetal", {"bin_hash": "x"})
    states = wal.replay(lay)
    assert not states["v2"].committed
    assert "v2" in wal.resumable_variants(states)        # 破棄して再評価
    assert "v2" not in wal.terminal_variants(states)


def test_wal_abort_is_terminal_not_adopted():
    lay = _layout(); lay.ensure()
    wal.log(lay, "v3", STAGE_BUILD_DONE, "linux-baremetal")
    wal.log(lay, "v3", STAGE_ABORT, "linux-baremetal", {"reason": "non-serializable"})
    states = wal.replay(lay)
    assert states["v3"].aborted and not states["v3"].committed
    assert "v3" in wal.terminal_variants(states)          # 再評価しない
    assert "v3" not in wal.resumable_variants(states)


def test_wal_tolerates_truncated_last_line():
    lay = _layout(); lay.ensure()
    commit_receipts.append_legacy_raw_commit(
        lay, "v4", "linux-baremetal", {},
    )
    # 追記中クラッシュを模す: 壊れた半端な JSON を末尾に足す
    with open(lay.wal_file, "a", encoding="utf-8") as f:
        f.write('{"variant":"v5","stage":"build_st')     # 切れた行
    records, truncated_tail = wal.read_records_checked(lay)
    assert [record.variant for record in records] == ["v4"]
    assert truncated_tail is True
    states = wal.replay(lay)                              # 例外を投げず
    assert states["v4"].committed
    assert "v5" not in states                             # 壊れた行は捨てる


def test_wal_complete_invalid_final_line_is_not_treated_as_crash_prefix():
    lay = _layout(); lay.ensure()
    commit_receipts.append_legacy_raw_commit(
        lay, "v4", "linux-baremetal", {},
    )
    with open(lay.wal_file, "ab") as f:
        # JSON として完全だが payload が無い raw record。最終行でも黙殺しない。
        f.write(b'{"variant":"v5","stage":"build_start",'
                b'"env_tag":"linux-baremetal","ts":1}\n')
    # C02 は受理集合を変えないため kill 集計には含めず、例外階層の防壁 pin とする。
    assert not issubclass(wal.WalLineError, (KeyError, json.JSONDecodeError))
    try:
        wal.read_records(lay)
        assert False, "構文的に完全な契約違反を最終行でも拒否すべき"
    except wal.WalLineError as exc:
        assert "keys must be exactly" in str(exc)


def test_wal_parse_line_rejects_nested_duplicate_and_unknown_top_level_key():
    nested_duplicate = (
        '{"variant":"v","stage":"commit","env_tag":"e","ts":1,'
        '"payload":{"metrics":{"tps":1,"tps":2}}}'
    )
    try:
        wal.parse_line(nested_duplicate)
        assert False, "nested duplicate key を拒否すべき"
    except wal.WalDuplicateKeyError as exc:
        assert "tps" in str(exc)

    unknown = (
        '{"variant":"v","stage":"commit","env_tag":"e","ts":1,'
        '"payload":{},"unknown":true}'
    )
    try:
        wal.parse_line(unknown)
        assert False, "未知 top-level key を拒否すべき"
    except wal.WalLineError as exc:
        assert "unknown" in str(exc)


def test_wal_parse_line_rejects_invalid_basic_types_and_nonfinite_ts():
    bad_fragments = [
        '"variant":1,"stage":"commit","env_tag":"e","ts":1,"payload":{}',
        '"variant":"v","stage":1,"env_tag":"e","ts":1,"payload":{}',
        '"variant":"v","stage":"commit","env_tag":1,"ts":1,"payload":{}',
        '"variant":"v","stage":"commit","env_tag":"e","ts":true,"payload":{}',
        '"variant":"v","stage":"commit","env_tag":"e","ts":NaN,"payload":{}',
    ]
    for bad_fragment in bad_fragments:
        try:
            wal.parse_line("{" + bad_fragment + "}")
            assert False, "基本型または有限性の違反を拒否すべき: " + bad_fragment
        except wal.WalLineError:
            pass


def test_wal_parse_line_requires_object_payload_and_checks_nested_duplicates_first():
    try:
        wal.parse_line(
            '{"variant":"v","stage":"commit","env_tag":"e","ts":1,'
            '"payload":["not-a-mapping"]}')
        assert False, "非 object payload を拒否すべき"
    except wal.WalLineError as exc:
        assert "payload must be a JSON object" in str(exc)

    try:
        wal.parse_line('{"variant":"v","stage":"commit","env_tag":"e","ts":1,'
                       '"payload":[{"tps":1,"tps":2}]}')
        assert False, "list payload の中の duplicate key も拒否すべき"
    except wal.WalDuplicateKeyError:
        pass


def test_wal_log_rejects_falsy_nonobject_payload_but_none_means_empty_object():
    rejected = _layout()
    try:
        wal.log(rejected, "v", STAGE_BUILD_DONE, "test", payload=[])
        assert False, "falsy list を empty object に正規化してはならない"
    except wal.WalPayloadTypeError as exc:
        assert exc.path == "payload"
    assert not os.path.exists(rejected.runs_dir)

    accepted = _layout()
    record = wal.log(accepted, "v", STAGE_BUILD_DONE, "test", payload=None)
    assert record.payload == {}
    assert wal.read_records(accepted)[0].payload == {}


def test_wal_blank_line_is_rejected_but_collected_reader_keeps_valid_records():
    lay = _layout(); lay.ensure()
    commit_receipts.append_legacy_raw_commit(lay, "before", "test", {})
    commit_receipts.append_legacy_raw_commit(lay, "after", "test", {})
    with open(lay.wal_file, encoding="utf-8") as stream:
        lines = stream.readlines()
    with open(lay.wal_file, "w", encoding="utf-8") as stream:
        stream.writelines([lines[0], "\n", lines[1]])

    try:
        wal.read_records_checked(lay)
        assert False, "正常 record 間の空行を拒否すべき"
    except wal.WalLineError as exc:
        assert "must not be empty" in str(exc)

    records, line_issues, truncated_tail = wal.read_records_collected(lay)
    assert [record.variant for record in records] == ["before", "after"]
    assert line_issues == [(2, "WalLineError: WAL line must not be empty")]
    assert truncated_tail is False


def test_wal_writer_rejects_nonstring_json_key_before_writing():
    lay = _layout()
    try:
        wal.log(lay, "v", STAGE_COMMIT, "test", {1: "int-key"})
        assert False, "non-string key を serialize 前に拒否すべき"
    except wal.WalPayloadTypeError as exc:
        assert exc.path == "payload[<key>]"
    assert not os.path.exists(lay.wal_file)
    assert not os.path.exists(lay.runs_dir)


def _raw_wal_record(variant="raw", stage=STAGE_COMMIT, payload=None) -> bytes:
    return json.dumps({
        "variant": variant,
        "stage": stage,
        "env_tag": "test",
        "ts": 1,
        "payload": {} if payload is None else payload,
    }, ensure_ascii=False, separators=(",", ":")).encode("utf-8")


def test_wal_unterminated_complete_json_is_always_truncated_tail():
    lay = _layout(); lay.ensure()
    with open(lay.wal_file, "wb") as stream:
        stream.write(_raw_wal_record())
    checked, truncated = wal.read_records_checked(lay)
    collected, issues, collected_truncated = wal.read_records_collected(lay)
    assert checked == [] and truncated is True
    assert collected == [] and issues == [] and collected_truncated is True
    try:
        list(wal.iter_lines(lay.wal_file))
        assert False, "strict adapter は無終端 tail を拒否すべき"
    except wal.WalFramingError:
        pass


def test_wal_multibyte_partial_tail_is_not_decoded():
    lay = _layout(); lay.ensure()
    commit_receipts.append_legacy_raw_commit(lay, "before", "test", {})
    with open(lay.wal_file, "ab") as stream:
        stream.write(b'{"variant":"broken","payload":"\xe3\x81')
    checked, truncated = wal.read_records_checked(lay)
    collected, issues, collected_truncated = wal.read_records_collected(lay)
    assert [record.variant for record in checked] == ["before"]
    assert truncated is True
    assert [record.variant for record in collected] == ["before"]
    assert issues == [] and collected_truncated is True


def test_wal_terminated_invalid_utf8_is_line_issue_not_tail():
    lay = _layout(); lay.ensure()
    with open(lay.wal_file, "wb") as stream:
        stream.write(b"\xff\n")
    try:
        wal.read_records_checked(lay)
        assert False, "newline 終端済み UTF-8 違反は伝播すべき"
    except UnicodeDecodeError:
        pass
    records, issues, truncated = wal.read_records_collected(lay)
    assert records == [] and truncated is False and len(issues) == 1
    assert issues[0][0] == 1
    assert issues[0][1].startswith("UnicodeDecodeError: ")


def test_wal_terminated_invalid_json_is_line_issue_not_tail():
    lay = _layout(); lay.ensure()
    with open(lay.wal_file, "wb") as stream:
        stream.write(b'{"variant":}\n')
    try:
        wal.read_records_checked(lay)
        assert False, "newline 終端済み JSON 違反は伝播すべき"
    except json.JSONDecodeError:
        pass
    records, issues, truncated = wal.read_records_collected(lay)
    assert records == [] and truncated is False and len(issues) == 1
    assert issues[0][0] == 1
    assert issues[0][1].startswith("JSONDecodeError: ")


def test_wal_append_rejects_every_unterminated_tail_without_changing_bytes():
    tails = (
        b'{"variant":"fragment"',
        _raw_wal_record(variant="complete"),
        b'{"variant":"multibyte-\xe3\x81',
    )
    for tail in tails:
        lay = _layout(); lay.ensure()
        wal.log(lay, "before", STAGE_BUILD_DONE, "test")
        with open(lay.wal_file, "ab") as stream:
            stream.write(tail)
        before = open(lay.wal_file, "rb").read()
        try:
            wal.log(lay, "after", STAGE_BUILD_DONE, "test")
            assert False, "unframed tail への append を拒否すべき"
        except wal.WalAppendError as exc:
            assert exc.phase == "tail-gate"
            assert exc.wal_path == lay.wal_file
            assert exc.written_bytes == 0 < exc.total_bytes
            assert isinstance(exc.cause, wal.WalFramingError)
        assert open(lay.wal_file, "rb").read() == before


def test_wal_repair_tail_then_append_restores_independent_frames():
    lay = _layout(); lay.ensure()
    wal.log(lay, "before", STAGE_BUILD_DONE, "test")
    framed = open(lay.wal_file, "rb").read()
    tail = b'{"variant":"torn"'
    with open(lay.wal_file, "ab") as stream:
        stream.write(tail)
    result = wal.repair_truncated_tail(lay)
    assert result.status == "repaired"
    assert result.original_size == len(framed) + len(tail)
    assert result.final_size == len(framed)
    assert result.removed_bytes == len(tail)
    assert result.removed_sha256 == hashlib.sha256(tail).hexdigest()
    assert len(result.preview.encode("utf-8")) <= 256
    assert result.receipt_path and os.path.isfile(result.receipt_path)
    wal.log(lay, "after", STAGE_BUILD_DONE, "test")
    records, truncated = wal.read_records_checked(lay)
    assert [record.variant for record in records] == ["before", "after"]
    assert truncated is False


def test_wal_repair_without_any_newline_truncates_to_zero():
    lay = _layout(); lay.ensure()
    tail = _raw_wal_record()
    with open(lay.wal_file, "wb") as stream:
        stream.write(tail)
    result = wal.repair_truncated_tail(lay)
    assert result.status == "repaired"
    assert result.original_size == len(tail) and result.final_size == 0
    assert result.removed_bytes == len(tail)
    assert open(lay.wal_file, "rb").read() == b""


def test_wal_repair_missing_empty_and_framed_are_noops():
    missing = _layout()
    result = wal.repair_truncated_tail(missing)
    assert result == wal.WalTailRepairResult(
        "missing", 0, 0, 0, None, "", None)
    assert not os.path.exists(missing.runs_dir)

    empty = _layout(); empty.ensure()
    open(empty.wal_file, "wb").close()
    result = wal.repair_truncated_tail(empty)
    assert result == wal.WalTailRepairResult(
        "noop", 0, 0, 0, None, "", None)

    framed = _layout(); framed.ensure()
    wal.log(framed, "v", STAGE_BUILD_DONE, "test")
    size = os.path.getsize(framed.wal_file)
    result = wal.repair_truncated_tail(framed)
    assert result == wal.WalTailRepairResult(
        "noop", size, size, 0, None, "", None)


def test_wal_repair_receipt_is_durable_and_complete_before_truncate():
    lay = _layout(); lay.ensure()
    wal.log(lay, "before", STAGE_BUILD_DONE, "test")
    final_size = os.path.getsize(lay.wal_file)
    removed = b"torn-tail\x00\xff"
    with open(lay.wal_file, "ab") as stream:
        stream.write(removed)

    real_ftruncate = wal.os.ftruncate
    real_fsync = wal.os.fsync
    observed = {"receipt_before_truncate": False,
                "receipt_fsync_before_truncate": False,
                "wal_fsync_after": False}
    wal_fd = {"value": None}

    def checked_ftruncate(fd, size):
        receipts = [name for name in os.listdir(lay.runs_dir)
                    if name.startswith("wal-tail-repair-")]
        assert len(receipts) == 1
        with open(os.path.join(lay.runs_dir, receipts[0]), encoding="utf-8") as stream:
            receipt = json.load(stream)
        assert receipt["cut_offset"] == final_size
        assert receipt["removed_bytes"] == len(removed)
        assert receipt["removed_sha256"] == hashlib.sha256(removed).hexdigest()
        assert observed["receipt_fsync_before_truncate"]
        observed["receipt_before_truncate"] = True
        wal_fd["value"] = fd
        return real_ftruncate(fd, size)

    def tracked_fsync(fd):
        try:
            fd_path = os.readlink("/proc/self/fd/%d" % fd)
        except OSError:
            fd_path = ""
        if (not observed["receipt_before_truncate"]
                and os.path.basename(fd_path).startswith("wal-tail-repair-")):
            observed["receipt_fsync_before_truncate"] = True
        if wal_fd["value"] == fd:
            observed["wal_fsync_after"] = True
        return real_fsync(fd)

    wal.os.ftruncate = checked_ftruncate
    wal.os.fsync = tracked_fsync
    try:
        result = wal.repair_truncated_tail(lay)
    finally:
        wal.os.ftruncate = real_ftruncate
        wal.os.fsync = real_fsync
    assert result.status == "repaired"
    assert observed == {"receipt_before_truncate": True,
                        "receipt_fsync_before_truncate": True,
                        "wal_fsync_after": True}


def test_wal_append_completes_short_writes_and_rejects_zero_progress():
    lay = _layout()
    real_write = wal.os.write

    def short_write(fd, data):
        return real_write(fd, data[:7])

    wal.os.write = short_write
    try:
        wal.log(lay, "short", STAGE_BUILD_DONE, "test", {"text": "あ"})
    finally:
        wal.os.write = real_write
    records, truncated = wal.read_records_checked(lay)
    assert [record.variant for record in records] == ["short"]
    assert truncated is False
    assert open(lay.wal_file, "rb").read().count(b"\n") == 1

    zero = _layout()
    wal.os.write = lambda _fd, _data: 0
    try:
        try:
            wal.log(zero, "zero", STAGE_BUILD_DONE, "test")
            assert False, "zero-progress write を成功扱いしてはならない"
        except wal.WalAppendError as exc:
            assert exc.phase == "write"
            assert exc.written_bytes == 0 < exc.total_bytes
            assert isinstance(exc.cause, OSError)
    finally:
        wal.os.write = real_write
    assert open(zero.wal_file, "rb").read() == b""


def test_wal_append_fsyncs_directory_under_flock_on_every_append():
    lay = _layout()
    real_flock = wal.fcntl.flock
    real_fsync = wal.os.fsync
    real_close = wal.os.close
    locked = set()
    dir_fsyncs = []

    def tracked_flock(fd, operation):
        result = real_flock(fd, operation)
        if operation & fcntl.LOCK_EX:
            locked.add(fd)
        return result

    def tracked_fsync(fd):
        try:
            path = os.readlink("/proc/self/fd/%d" % fd)
        except OSError:
            path = ""
        if path == lay.runs_dir:
            wal_fds = [held for held in locked
                       if os.path.exists("/proc/self/fd/%d" % held)
                       and os.readlink("/proc/self/fd/%d" % held) == lay.wal_file]
            assert wal_fds, "runs dir fsync 時に WAL flock が解放済み"
            dir_fsyncs.append(fd)
        return real_fsync(fd)

    def tracked_close(fd):
        try:
            return real_close(fd)
        finally:
            locked.discard(fd)

    wal.fcntl.flock = tracked_flock
    wal.os.fsync = tracked_fsync
    wal.os.close = tracked_close
    try:
        wal.log(lay, "first", STAGE_BUILD_DONE, "test")
        wal.log(lay, "second", STAGE_BUILD_DONE, "test")
    finally:
        wal.fcntl.flock = real_flock
        wal.os.fsync = real_fsync
        wal.os.close = real_close
    assert len(dir_fsyncs) == 2


def test_wal_append_maps_wal_close_failure_to_structured_error():
    lay = _layout()
    real_close = wal.os.close
    injected = {"done": False}

    def fail_after_wal_close(fd):
        try:
            path = os.readlink("/proc/self/fd/%d" % fd)
        except OSError:
            path = ""
        result = real_close(fd)
        if path == lay.wal_file and not injected["done"]:
            injected["done"] = True
            raise OSError(errno.EIO, "injected WAL close EIO")
        return result

    wal.os.close = fail_after_wal_close
    caught = None
    try:
        try:
            wal.log(lay, "close-failure", STAGE_BUILD_DONE, "test")
        except wal.WalAppendError as exc:
            caught = exc
    finally:
        wal.os.close = real_close
    assert caught is not None
    assert caught.phase == "close"
    assert caught.written_bytes == caught.total_bytes
    assert isinstance(caught.cause, OSError) and caught.cause.errno == errno.EIO
    assert [record.variant for record in wal.read_records(lay)] == ["close-failure"]


def test_wal_repair_hashes_large_removed_tail_incrementally():
    lay = _layout(); lay.ensure()
    wal.log(lay, "before", STAGE_BUILD_DONE, "test")
    tail = b"streamed-tail-without-newline-" * 6000
    with open(lay.wal_file, "ab") as stream:
        stream.write(tail)

    real_sha256 = wal.hashlib.sha256
    constructor_sizes = []
    update_sizes = []

    class TrackingDigest:
        def __init__(self, initial=b""):
            constructor_sizes.append(len(initial))
            self._inner = real_sha256()
            if initial:
                self.update(initial)

        def update(self, chunk):
            update_sizes.append(len(chunk))
            self._inner.update(chunk)

        def hexdigest(self):
            return self._inner.hexdigest()

    wal.hashlib.sha256 = TrackingDigest
    try:
        result = wal.repair_truncated_tail(lay)
    finally:
        wal.hashlib.sha256 = real_sha256
    assert result.status == "repaired"
    assert result.removed_bytes == len(tail)
    assert result.removed_sha256 == real_sha256(tail).hexdigest()
    assert result.preview == tail[:128].hex()
    assert constructor_sizes == [0]
    assert len(update_sizes) >= 3 and max(update_sizes) <= 65536
    assert sum(update_sizes) == len(tail)


def test_wal_reader_stage_contract_is_exact_and_unknown_stage_fails_closed():
    assert STAGES == (
        STAGE_BUILD_START, STAGE_BUILD_DONE, STAGE_VERIFY_DONE,
        STAGE_BENCH_DONE, STAGE_COMMIT, STAGE_ABORT,
    )
    assert WAL_STAGES == STAGES + (
        STAGE_S1_SESSION, STAGE_S8B_ORACLE_SESSION,
    )
    assert len(WAL_STAGES) == 8 and len(set(WAL_STAGES)) == 8
    raw = _raw_wal_record(stage="sess1on-typo").decode("utf-8")
    try:
        wal.parse_line(raw)
        assert False, "unknown stage を reader が拒否すべき"
    except wal.WalLineError as exc:
        assert "unknown WAL stage" in str(exc)


def test_wal_writer_stage_contract_is_exact_and_unknown_stage_fails_closed():
    lay = _layout()
    try:
        wal.log(lay, "v", "sess1on-typo", "test")
        assert False, "unknown stage を writer が拒否すべき"
    except wal.WalLineError as exc:
        assert "unknown WAL stage" in str(exc)
    assert not os.path.exists(lay.runs_dir)

    for bad_record in (
            wal.WalRecord(1, STAGE_COMMIT, "test", 1, {}),
            wal.WalRecord("v", STAGE_COMMIT, "test", float("nan"), {})):
        lay = _layout()
        try:
            wal.append(lay, bad_record)
            assert False, "basic record 違反を open 前に拒否すべき"
        except wal.WalLineError:
            pass
        assert not os.path.exists(lay.runs_dir)


def test_wal_payload_deep_type_rejections_happen_before_open():
    cycle = []
    cycle.append(cycle)
    invalid = (
        ({"outer": {1: "bad"}}, "payload[\"outer\"][<key>]"),
        ({"outer": (1, 2)}, "payload[\"outer\"]"),
        ({"outer": {1, 2}}, "payload[\"outer\"]"),
        ({"outer": b"bytes"}, "payload[\"outer\"]"),
        ({"outer": cycle}, "payload[\"outer\"][0]"),
        ({"outer": float("nan")}, "payload[\"outer\"]"),
        ({"outer": float("inf")}, "payload[\"outer\"]"),
        ({"outer": "\ud800"}, "payload[\"outer\"]"),
    )
    for payload, expected_path in invalid:
        lay = _layout()
        try:
            wal.log(lay, "v", STAGE_BUILD_DONE, "test", payload)
            assert False, "invalid payload を拒否すべき: %r" % (payload,)
        except wal.WalPayloadTypeError as exc:
            assert exc.path == expected_path
        assert not os.path.exists(lay.runs_dir)


def test_wal_payload_accepts_ordered_dict_native_tree_and_shared_dag():
    shared = [1, {"finite": 1.25, "ok": True, "none": None}]
    payload = collections.OrderedDict((
        ("left", shared),
        ("right", shared),
        ("text", "日本語"),
    ))
    lay = _layout()
    wal.log(lay, "v", STAGE_BUILD_DONE, "test", payload)
    record = wal.read_records(lay)[0]
    assert record.payload == {
        "left": shared, "right": shared, "text": "日本語",
    }


def test_wal_reader_rejects_raw_nonfinite_payload_constants_and_overflow():
    for token in ("NaN", "Infinity", "-Infinity"):
        raw = (_raw_wal_record().decode("utf-8")
               .replace('"payload":{}', '"payload":{"bad":%s}' % token))
        try:
            wal.parse_line(raw)
            assert False, "raw non-finite constant を拒否すべき"
        except wal.WalPayloadTypeError as exc:
            assert exc.path is None
            assert token in str(exc)
    overflow = (_raw_wal_record().decode("utf-8")
                .replace('"payload":{}', '"payload":{"bad":1e999}'))
    try:
        wal.parse_line(overflow)
        assert False, "JSON overflow 由来の inf を拒否すべき"
    except wal.WalPayloadTypeError as exc:
        assert exc.path == 'payload["bad"]'


def test_wal_exception_hierarchy_and_append_attributes_are_separate():
    assert issubclass(wal.WalFramingError, wal.WalLineError)
    assert issubclass(wal.WalPayloadTypeError, wal.WalLineError)
    for error_type in (wal.WalLineError, wal.WalFramingError,
                       wal.WalPayloadTypeError, wal.WalAppendError):
        assert not issubclass(error_type, (json.JSONDecodeError, KeyError))
    assert not issubclass(wal.WalAppendError, wal.WalLineError)


def test_wal_append_and_repair_wait_for_exclusive_flock():
    append_layout = _layout(); append_layout.ensure()
    wal.log(append_layout, "before", STAGE_BUILD_DONE, "test")
    held = os.open(append_layout.wal_file, os.O_RDWR)
    fcntl.flock(held, fcntl.LOCK_EX)
    append_started = threading.Event()
    append_done = threading.Event()
    append_errors = []

    def append_worker():
        append_started.set()
        try:
            wal.log(append_layout, "after", STAGE_BUILD_DONE, "test")
        except BaseException as exc:  # noqa: BLE001 - worker 診断を親で検査
            append_errors.append(exc)
        finally:
            append_done.set()

    thread = threading.Thread(target=append_worker)
    thread.start()
    assert append_started.wait(1.0)
    assert not append_done.wait(0.05)
    fcntl.flock(held, fcntl.LOCK_UN)
    os.close(held)
    thread.join(2.0)
    assert append_done.is_set() and append_errors == []
    assert [r.variant for r in wal.read_records(append_layout)] == ["before", "after"]

    repair_layout = _layout(); repair_layout.ensure()
    wal.log(repair_layout, "before", STAGE_BUILD_DONE, "test")
    with open(repair_layout.wal_file, "ab") as stream:
        stream.write(b"tail")
    held = os.open(repair_layout.wal_file, os.O_RDWR)
    fcntl.flock(held, fcntl.LOCK_EX)
    repair_started = threading.Event()
    repair_done = threading.Event()
    repair_results = []

    def repair_worker():
        repair_started.set()
        try:
            repair_results.append(wal.repair_truncated_tail(repair_layout))
        finally:
            repair_done.set()

    thread = threading.Thread(target=repair_worker)
    thread.start()
    assert repair_started.wait(1.0)
    assert not repair_done.wait(0.05)
    fcntl.flock(held, fcntl.LOCK_UN)
    os.close(held)
    thread.join(2.0)
    assert repair_done.is_set()
    assert len(repair_results) == 1 and repair_results[0].status == "repaired"


def test_wal_records_by_stage_last_wins_per_stage():
    """D36 決定4-2: p3_kickoff/p3_s4_red/p3_s4_loop の重複 _records_of() を統合した
    共通ヘルパ。stage ごとに最後の payload が残る (宣言でなく WAL レコードで判定)。"""
    lay = _layout(); lay.ensure()
    wal.log(lay, "v1", STAGE_BUILD_START, "linux-baremetal", {"genome": "g"})
    commit_receipts.append_legacy_raw_commit(
        lay, "v1", "linux-baremetal", {"fitness_tps": 1}, ts=1.0,
    )
    commit_receipts.append_legacy_raw_commit(
        lay, "v1", "linux-baremetal", {"fitness_tps": 2}, ts=2.0,
    )  # 歴史 WAL の最後勝ち projection
    wal.log(lay, "v2", STAGE_BUILD_START, "linux-baremetal", {"genome": "other"})
    recs = wal.records_by_stage(lay, "v1")
    assert recs[STAGE_BUILD_START]["genome"] == "g"
    assert recs[STAGE_COMMIT]["fitness_tps"] == 2
    assert "v2" not in recs                              # 他 variant は混ざらない


def test_lock_preimage_roundtrip_and_immutable():
    lay = _layout(); lay.ensure()
    pre = "preimage-A"
    wal.write_lock(lay, pre)
    assert wal.read_lock(lay) == pre
    wal.write_lock(lay, "preimage-B")                    # 既存があれば上書きしない
    assert wal.read_lock(lay) == pre


# ===== bench 排他ロック (I) =====

def test_bench_lock_exclusive():
    fd_path = os.path.join(_tmpdir("izanagi_lock_"), "bench.lock")
    with bench_lock(fd_path, blocking=True):
        # 保持中に非ブロッキング取得 → BenchBusy
        try:
            with bench_lock(fd_path, blocking=False):
                assert False, "should be busy"
        except BenchBusy:
            pass
    # 解放後は取れる
    with bench_lock(fd_path, blocking=False):
        pass


_CAMPAIGN_LOCK_HOLDER = r'''
import sys
import time
from pathlib import Path
from orchestrator.campaign.lock import campaign_lock

lock_path, ready_path, release_path = sys.argv[1:4]
with campaign_lock(lock_path):
    Path(ready_path).touch()
    while not Path(release_path).exists():
        time.sleep(0.01)
'''


def _start_campaign_lock_holder(
        lock_path: str, ready_path: Path, release_path: Path,
) -> subprocess.Popen:
    env = dict(os.environ)
    env["PYTHONPATH"] = str(_REPOSITORY)
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    return subprocess.Popen(
        [sys.executable, "-c", _CAMPAIGN_LOCK_HOLDER,
         lock_path, str(ready_path), str(release_path)],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        env=env,
    )


def _wait_for_campaign_lock_holder(child: subprocess.Popen, ready_path: Path) -> None:
    deadline = time.monotonic() + 10.0
    while not ready_path.exists():
        returncode = child.poll()
        if returncode is not None:
            stdout, stderr = child.communicate()
            raise AssertionError(
                "campaign lock holder が ready 前に終了した: "
                f"returncode={returncode}, stdout={stdout!r}, stderr={stderr!r}"
            )
        if time.monotonic() >= deadline:
            raise AssertionError("campaign lock holder の ready 待ちが timeout した")
        time.sleep(0.01)


def _finish_campaign_lock_holder(
        child: subprocess.Popen, release_path: Path,
) -> None:
    release_path.touch()
    try:
        stdout, stderr = child.communicate(timeout=10)
    except subprocess.TimeoutExpired as exc:
        child.kill()
        child.communicate(timeout=10)
        raise AssertionError("campaign lock holder が release 後も終了しない") from exc
    assert child.returncode == 0, (
        f"campaign lock holder failed: returncode={child.returncode}, "
        f"stdout={stdout!r}, stderr={stderr!r}"
    )


def test_campaign_lock_reentry_rejected_in_same_process():
    layout = _layout().ensure()
    output_root = _tmpdir("izanagi_campaign_lock_reentry_output_")
    lock_path = campaign_lock_path(
        layout, declared_use_class="official", output_root=output_root,
    )
    with campaign_flock(lock_path):
        try:
            with campaign_flock(lock_path, blocking=False):
                raise AssertionError("同一 process の campaign lock 再入を拒否すべき")
        except CampaignBusy:
            pass


def test_campaign_lock_same_campaign_rejects_competing_process():
    layout = _layout().ensure()
    output_root = _tmpdir("izanagi_campaign_lock_competing_output_")
    lock_path = campaign_lock_path(
        layout, declared_use_class="official", output_root=output_root,
    )
    control_root = Path(_tmpdir("izanagi_campaign_lock_process_"))
    ready_path = control_root / "ready"
    release_path = control_root / "release"
    child = _start_campaign_lock_holder(lock_path, ready_path, release_path)
    try:
        _wait_for_campaign_lock_holder(child, ready_path)
        try:
            with campaign_flock(lock_path, blocking=False):
                raise AssertionError("競合 process が保持中の campaign lock を取得すべきでない")
        except CampaignBusy:
            pass
    finally:
        _finish_campaign_lock_holder(child, release_path)


def test_campaign_lock_different_campaigns_can_run_in_parallel():
    layouts = [_layout().ensure(), _layout().ensure()]
    output_root = _tmpdir("izanagi_campaign_lock_parallel_output_")
    lock_paths = [
        campaign_lock_path(
            layout, declared_use_class="official", output_root=output_root,
        )
        for layout in layouts
    ]
    control_root = Path(_tmpdir("izanagi_campaign_lock_parallel_"))
    controls = [
        (control_root / f"ready-{index}", control_root / f"release-{index}")
        for index in range(len(lock_paths))
    ]
    children = [
        _start_campaign_lock_holder(lock_path, ready_path, release_path)
        for lock_path, (ready_path, release_path) in zip(lock_paths, controls)
    ]
    try:
        for child, (ready_path, _release_path) in zip(children, controls):
            _wait_for_campaign_lock_holder(child, ready_path)
        assert all(child.poll() is None for child in children)
    finally:
        for _ready_path, release_path in controls:
            release_path.touch()
        for child, (_ready_path, release_path) in zip(children, controls):
            _finish_campaign_lock_holder(child, release_path)


def test_campaign_lock_released_can_be_reacquired():
    layout = _layout().ensure()
    output_root = _tmpdir("izanagi_campaign_lock_reacquire_output_")
    lock_path = campaign_lock_path(
        layout, declared_use_class="official", output_root=output_root,
    )
    with campaign_flock(lock_path):
        pass
    with campaign_flock(lock_path, blocking=False):
        pass


def test_campaign_lock_path_is_outside_campaign_root():
    layout = _layout()
    output_root = _tmpdir("izanagi_campaign_lock_outside_output_")
    lock_path = Path(
        campaign_lock_path(
            layout, declared_use_class="official", output_root=output_root,
        )
    ).resolve()
    campaign_root = Path(layout.root).resolve()
    assert not lock_path.is_relative_to(campaign_root)


def test_campaign_lock_path_normalizes_symlink_realpath():
    real_root = _tmpdir("izanagi_campaign_lock_real_")
    link_parent = _tmpdir("izanagi_campaign_lock_link_")
    link_root = os.path.join(link_parent, "campaign")
    os.symlink(real_root, link_root)

    real_layout = CampaignLayout(root=real_root)
    symlink_layout = CampaignLayout(root=link_root)
    output_root = _tmpdir("izanagi_campaign_lock_symlink_output_")
    assert campaign_lock_path(
        real_layout, declared_use_class="official", output_root=output_root,
    ) == campaign_lock_path(
        symlink_layout, declared_use_class="official", output_root=output_root,
    )


def test_campaign_lock_helpers_use_explicit_output_root_for_each_use_class():
    output_root = Path(_tmpdir("izanagi_campaign_lock_explicit_root_"))
    layout = CampaignLayout(root=str(output_root / "campaigns" / "campaign"))
    expected_lock_dir = output_root / "campaign-locks"

    for declared_use_class in ("official", "exploration"):
        lock_dir = Path(campaign_lock_dir(
            declared_use_class, str(output_root),
        ))
        lock_path = Path(campaign_lock_path(
            layout, declared_use_class, str(output_root),
        ))
        assert lock_dir == expected_lock_dir
        assert lock_path.parent == expected_lock_dir


def test_campaign_lock_path_hash_key_is_twenty_hex_chars():
    output_root = _tmpdir("izanagi_campaign_lock_hash_output_")
    lock_name = os.path.basename(
        campaign_lock_path(
            _layout(), declared_use_class="official", output_root=output_root,
        )
    )
    assert lock_name.endswith(".flock")
    key = lock_name[:-len(".flock")]
    assert re.fullmatch(r"^[0-9a-f]{20}$", key)


# ===== STAGE2: ビルドキャッシュキー (規律1: trace/perf 別ビルド) =====

def test_cache_key_separates_trace_genome_and_commit():
    g1 = Genome("silo", {"BACK_OFF": 1})
    g2 = Genome("silo", {"BACK_OFF": 0})
    admission_1 = _admission_for(g1, "abc123")
    admission_2 = _admission_for(g2, "abc123")
    kt = buildcache.cache_key(g1, "abc123", trace=True, admission=admission_1)
    kp = buildcache.cache_key(g1, "abc123", trace=False, admission=admission_1)
    assert kt.endswith("_t1") and kp.endswith("_t0")    # trace 有無で別ビルド (規律1)
    assert kt != kp
    assert kt.startswith("silo_")
    assert kt != buildcache.cache_key(
        g2, "abc123", trace=True, admission=admission_2,
    )
    assert kt != buildcache.cache_key(
        g1, "xyz999", trace=True, admission=_admission_for(g1, "xyz999"),
    )


def test_cache_key_separates_compiler_request_name():
    genome_value = Genome("silo", {"BACK_OFF": 1})
    commit = "abc123"
    src_token = "1" * 64
    admission = _admission_for(
        genome_value, commit, src_token=src_token,
    )
    common = {
        "trace": False,
        "src_token": src_token,
        "admission": admission,
    }

    assert buildcache.cache_key(
        genome_value, commit, cxx="g++-12", **common,
    ) != buildcache.cache_key(
        genome_value, commit, cxx="g++-13", **common,
    )


def test_cache_key_default_toolchain_change_does_not_alias_historical_key(monkeypatch):
    # module global の差し替え + cc/cxx 明示は key 計算上の実編集と等価。
    # 定義時既定を含む実編集での再現は T-785 の repo 外 probe が担う。
    genome_value = Genome("silo", {"BACK_OFF": 1})
    commit = "abc123"
    src_token = "1" * 64
    common = {
        "trace": False,
        "src_token": src_token,
        "admission": _admission_for(genome_value, commit, src_token=src_token),
    }
    historical_key = buildcache.cache_key(genome_value, commit, **common)
    changed_keys = []
    for cc, cxx in (("gcc-12", "g++-12"), ("gcc", "g++")):
        monkeypatch.setattr(buildcache, "DEFAULT_CC", cc)
        monkeypatch.setattr(buildcache, "DEFAULT_CXX", cxx)
        changed_key = buildcache.cache_key(
            genome_value, commit, cc=cc, cxx=cxx, **common,
        )
        assert changed_key != historical_key
        changed_keys.append(changed_key)
        assert buildcache.cache_key(
            genome_value, commit, cc="gcc-13", cxx="g++-13", **common,
        ) == historical_key
    assert changed_keys[0] != changed_keys[1]


# ===== STAGE2: variant_id (WAL キー) =====

def test_variant_id_deterministic_and_sensitive():
    a = pipeline.variant_id(Genome("silo", {"BACK_OFF": 1, "WAL": 0}))
    a2 = pipeline.variant_id(Genome("silo", {"WAL": 0, "BACK_OFF": 1}))  # 順不同
    b = pipeline.variant_id(Genome("silo", {"BACK_OFF": 0, "WAL": 0}))
    assert a == a2 and len(a) == 12      # canonical なので flag 記述順に非依存
    assert a != b                        # flag 値が違えば別 id


def test_trigger_binding_does_not_enter_variant_id_preimage():
    parameters = inspect.signature(pipeline.variant_id).parameters
    assert tuple(parameters) == ("genome", "src_token")
    genome_value = Genome("silo", {"BACK_OFF": 1, "WAL": 0})
    source_token = "c" * 64
    expected = pipeline.variant_id(genome_value, source_token)
    for mask in range(32):
        binding = trigger_gate_binding.TriggerGateBinding(
            mask=mask,
            predicate_sha256=trigger_gate_binding.expected_predicate_sha256(mask),
            nonce=(f"{mask:02x}" * 32),
            source=None,
        )
        assert trigger_gate_binding.commitment(binding)
        assert pipeline.variant_id(genome_value, source_token) == expected


def test_trigger_fixture_has_32_unique_predicates_source_bytes_and_variant_ids():
    genome_value = Genome("silo", {"BACK_OFF": 1, "WAL": 0})
    predicates = [emit_predicate(TriggerGateIR(mask)) for mask in range(32)]
    materialized = [
        ("fixture-prefix\n" + predicate + "\nfixture-suffix\n").encode("ascii")
        for predicate in predicates
    ]
    source_tokens = [hashlib.sha256(body).hexdigest() for body in materialized]
    variants = [pipeline.variant_id(genome_value, token) for token in source_tokens]
    assert len(set(predicates)) == len(set(materialized)) == len(set(variants)) == 32


@pytest.mark.usefixtures("ratified_enforcement_source")
def test_trigger_campaign_epoch_never_writes_pre_t428_paths():
    from orchestrator.campaign import loop as campaign_loop
    from orchestrator.campaign import p3_s4_loop_trigger_gating as trigger_driver

    # 4f0d020 default_cfg の marker 前 other/compute config を ident.campaign_id で再計算。
    old_ids = {
        "p3-s8a-trigger-loop-s8a-trigger-autonomous-0e79a5f1",
        "p3-s8a-trigger-loop-s8a-trigger-autonomous-63bc09ae",
    }
    context = build_run_context(generator_id=GeneratorId.S8A_TRIGGER_SWEEP)
    cfg = trigger_driver.default_cfg()
    current_id = str(ident.campaign_id(
        ident.bind_environment_contract(cfg, _AUTH_CONTRACT)
    ))
    assert cfg.search_config[wal.TRIGGER_BINDING_SCHEMA_MARKER_KEY] == \
        trigger_gate_binding.SCHEMA_VERSION
    assert current_id not in old_ids
    candidate = trigger_gate_binding.TriggerGateBinding(
        mask=20,
        predicate_sha256=trigger_gate_binding.expected_predicate_sha256(20),
        nonce="2" * 64,
        source=None,
    )
    output_root = _tmpdir("izanagi_trigger_epoch_")
    summary = campaign_loop.run_campaign(
        cfg, [], PerfConfig(records=1000, threads=2),
        _AUTH_CONTRACT.env_tag, _AUTH_CONTRACT.clocks_per_us,
        numactl=list(_AUTH_CONTRACT.numactl),
        authorization_contract=_AUTHORIZATION,
        do_bench=False, output_root=output_root, log=lambda *_args: None,
        build_context=context, declared_use_class="exploration",
        trigger_gate_binding=candidate,
    )
    assert summary.campaign_id == current_id
    assert os.path.exists(summary.layout_root)
    for old_id in old_ids:
        assert not os.path.lexists(
            exploration_campaign_layout(old_id, output_root).root
        )


# ===== STAGE2: 評価パイプライン (build→verify→[bench]→commit) =====
#
# 実ビルド/実機なしでパイプラインの制御フローと **規律2 の自動執行** を回帰テスト化する。
# pipeline モジュールの外部依存 (buildcache/verify/bench) をダミーに差し替え、
# verifier の verdict だけを操作して abort/commit の分岐を検査する。

def _tmp_layout():
    root = _tmpdir("izanagi_pipe_")
    return CampaignLayout(root=os.path.join(root, "campaigns", "test")).ensure()


def _uncreated_authorization_layout():
    root = _tmpdir("izanagi_authorization_")
    return CampaignLayout(root=os.path.join(root, "campaign")), root


def _assert_authorization_rejects_without_writes(
        authorization_contract, *, env_tag, clocks_per_us, numactl,
        env_contract=None, expected_type=Exception):
    lay, root = _uncreated_authorization_layout()
    try:
        pipeline.evaluate(
            Genome("silo", {"BACK_OFF": 1}), lay, env_tag, "deadbeef",
            PerfConfig(records=1000, threads=2), clocks_per_us,
            numactl=numactl, env_contract=env_contract,
            authorization_contract=authorization_contract,
            build_context=_BUILD_CONTEXT, log=lambda *_args: None,
        )
        assert False, "authorization input must be rejected"
    except expected_type:
        pass
    assert os.listdir(root) == []


def test_m1_pipeline_requires_authorization_before_any_sink_write():
    lay, root = _uncreated_authorization_layout()
    try:
        pipeline.evaluate(
            Genome("silo", {"BACK_OFF": 1}), lay,
            _AUTH_CONTRACT.env_tag, "deadbeef", PerfConfig(records=1000, threads=2),
            _AUTH_CONTRACT.clocks_per_us, numactl=list(_AUTH_CONTRACT.numactl),
            build_context=_BUILD_CONTEXT,
        )
        assert False, "authorization_contract must be a required keyword-only argument"
    except TypeError as exc:
        assert "authorization_contract" in str(exc)
    assert os.listdir(root) == []
    _assert_authorization_rejects_without_writes(
        None,
        env_tag=_AUTH_CONTRACT.env_tag,
        clocks_per_us=_AUTH_CONTRACT.clocks_per_us,
        numactl=list(_AUTH_CONTRACT.numactl),
        expected_type=TypeError,
    )

    class ContractSubclass(ec.ExecutionEnvironmentContract):
        pass

    subclass = ContractSubclass(
        env_tag=_AUTH_CONTRACT.env_tag,
        clocks_per_us=_AUTH_CONTRACT.clocks_per_us,
        numactl=_AUTH_CONTRACT.numactl,
        attestation_mode=_AUTH_CONTRACT.attestation_mode,
        isolation_policy=_AUTH_CONTRACT.isolation_policy,
        calibration_ref=_AUTH_CONTRACT.calibration_ref,
    )
    _assert_authorization_rejects_without_writes(
        subclass,
        env_tag=subclass.env_tag,
        clocks_per_us=subclass.clocks_per_us,
        numactl=list(subclass.numactl),
        expected_type=TypeError,
    )


def test_m0_activation_receipt_refusal_precedes_any_sink_write():
    import dataclasses

    guard = pipeline.execution_guard
    forged = dataclasses.replace(
        _AUTHORIZATION, activation_state_sha256="0" * 64,
    )
    _assert_authorization_rejects_without_writes(
        forged,
        env_tag=_AUTH_CONTRACT.env_tag,
        clocks_per_us=_AUTH_CONTRACT.clocks_per_us,
        numactl=list(_AUTH_CONTRACT.numactl),
        expected_type=guard.CertifiedWriterAuthorizationError,
    )


def test_activation_receipt_check_precedes_registry_runtime_site_and_selector_checks():
    import dataclasses

    guard = pipeline.execution_guard
    forged_receipt = dataclasses.replace(
        _AUTHORIZATION, activation_state_sha256="0" * 64,
    )
    assert forged_receipt.process_seal is guard._env_contract._AUTHORIZATION_PROCESS_SEAL
    mismatched_selector = ec.lookup("pegasus")

    cases = (
        (
            "registry",
            lambda: unittest_mock.patch.object(
                guard._env_contract, "GENERATIONS", {},
            ),
            {},
            "未登録 generation",
        ),
        (
            "runtime",
            contextlib.nullcontext,
            {"clocks_per_us": _AUTH_CONTRACT.clocks_per_us + 1},
            "campaign execution values",
        ),
        (
            "site",
            lambda: unittest_mock.patch.object(
                guard._site_policy, "current_site",
                lambda: guard._site_policy.PEGASUS_COMPUTE,
            ),
            {},
            "Pegasus compute",
        ),
        (
            "selector",
            contextlib.nullcontext,
            {"env_contract": mismatched_selector},
            "build selector",
        ),
    )
    base = {
        "env_tag": _AUTH_CONTRACT.env_tag,
        "clocks_per_us": _AUTH_CONTRACT.clocks_per_us,
        "numactl": list(_AUTH_CONTRACT.numactl),
        "env_contract": None,
    }
    for _name, arm_later_check, overrides, later_match in cases:
        with arm_later_check():
            call = {**base, **overrides}
            with _assert_raises_contains(
                guard.CertifiedWriterAuthorizationError,
                later_match,
            ):
                guard.require_certified_writer_authorization(
                    _AUTHORIZATION, **call,
                )

            with unittest_mock.patch.dict(
                    guard._env_contract._AUTHORIZED_CONTRACTS,
                    {_AUTH_CONTRACT.env_tag: forged_receipt},
            ):
                with _assert_raises_contains(
                    guard.CertifiedWriterAuthorizationError,
                    "authorization receipt の serial/state hash",
                ):
                    guard.require_certified_writer_authorization(
                        forged_receipt,
                        **call,
                    )


def test_m2_pipeline_rejects_forged_contract_even_when_runtime_matches_it():
    import dataclasses

    forged = dataclasses.replace(
        _AUTH_CONTRACT,
        isolation_policy=dataclasses.replace(
            _AUTH_CONTRACT.isolation_policy,
            single_process=not _AUTH_CONTRACT.isolation_policy.single_process,
        ),
    )
    _assert_authorization_rejects_without_writes(
        dataclasses.replace(_AUTHORIZATION, contract=forged),
        env_tag=forged.env_tag,
        clocks_per_us=forged.clocks_per_us,
        numactl=list(forged.numactl),
        expected_type=pipeline.execution_guard.ExecutionGuardError,
    )


def test_runtime_authorization_rejects_equality_spoof_and_float_clock():
    class EqualitySpoof:
        def __eq__(self, _other):
            return True

        def __ne__(self, _other):
            return False

        def __str__(self):
            return "forged-runtime-value"

    _assert_authorization_rejects_without_writes(
        _AUTHORIZATION,
        env_tag=EqualitySpoof(),
        clocks_per_us=_AUTH_CONTRACT.clocks_per_us,
        numactl=list(_AUTH_CONTRACT.numactl),
        expected_type=TypeError,
    )
    _assert_authorization_rejects_without_writes(
        _AUTHORIZATION,
        env_tag=_AUTH_CONTRACT.env_tag,
        clocks_per_us=1800.0,
        numactl=list(_AUTH_CONTRACT.numactl),
        expected_type=TypeError,
    )


def test_m3_pipeline_rejects_authorization_selector_mismatch():
    _assert_authorization_rejects_without_writes(
        _AUTHORIZATION,
        env_tag=_AUTH_CONTRACT.env_tag,
        clocks_per_us=_AUTH_CONTRACT.clocks_per_us,
        numactl=list(_AUTH_CONTRACT.numactl),
        env_contract=ec.lookup("pegasus"),
        expected_type=pipeline.execution_guard.ExecutionGuardError,
    )


def test_build_selector_rejects_custom_equality_subclass():
    class SelectorSubclass(ec.ExecutionEnvironmentContract):
        def __eq__(self, _other):
            return True

        def __ne__(self, _other):
            return False

    selector = SelectorSubclass(
        env_tag="forged-selector",
        clocks_per_us=_AUTH_CONTRACT.clocks_per_us,
        numactl=_AUTH_CONTRACT.numactl,
        attestation_mode=_AUTH_CONTRACT.attestation_mode,
        isolation_policy=_AUTH_CONTRACT.isolation_policy,
        calibration_ref=_AUTH_CONTRACT.calibration_ref,
    )
    _assert_authorization_rejects_without_writes(
        _AUTHORIZATION,
        env_tag=_AUTH_CONTRACT.env_tag,
        clocks_per_us=_AUTH_CONTRACT.clocks_per_us,
        numactl=list(_AUTH_CONTRACT.numactl),
        env_contract=selector,
        expected_type=TypeError,
    )


def test_m4_pipeline_rejects_unresolved_none_numactl_for_pegasus():
    pegasus_authorization = ec.authorize("pegasus")
    pegasus = pegasus_authorization.contract
    _assert_authorization_rejects_without_writes(
        pegasus_authorization,
        env_tag=pegasus.env_tag,
        clocks_per_us=pegasus.clocks_per_us,
        numactl=None,
        expected_type=pipeline.execution_guard.ExecutionGuardError,
    )


def test_m5_pipeline_compute_rejects_registered_linux_contract():
    saved = pipeline.execution_guard._site_policy.current_site
    pipeline.execution_guard._site_policy.current_site = (
        lambda: site_policy.PEGASUS_COMPUTE
    )
    try:
        _assert_authorization_rejects_without_writes(
            _AUTHORIZATION,
            env_tag=_AUTH_CONTRACT.env_tag,
            clocks_per_us=_AUTH_CONTRACT.clocks_per_us,
            numactl=list(_AUTH_CONTRACT.numactl),
            expected_type=pipeline.execution_guard.ExecutionGuardError,
        )
    finally:
        pipeline.execution_guard._site_policy.current_site = saved


def test_p1_pipeline_accepts_registered_contract_without_enabling_v2_build():
    lay = _tmp_layout()
    with _mock_pipeline(certified=True) as calls:
        result = pipeline.evaluate(
            Genome("silo", {"BACK_OFF": 1}), lay,
            _AUTH_CONTRACT.env_tag, "deadbeef", PerfConfig(records=1000, threads=2),
            _AUTH_CONTRACT.clocks_per_us,
            numactl=list(_AUTH_CONTRACT.numactl),
            authorization_contract=_AUTHORIZATION,
            do_bench=False, build_context=_BUILD_CONTEXT,
            log=lambda *_args: None,
        )
    assert result.certified and not result.aborted
    assert calls.builds == [("legacy", True, None), ("legacy", False, None)]


@pytest.mark.usefixtures("ratified_enforcement_source")
def test_p1_run_campaign_accepts_registered_contract():
    from orchestrator.campaign import loop as campaign_loop

    out_root = _tmpdir("izanagi_authorization_run_")
    cfg = CampaignConfig(
        spec_slug="authorization-positive",
        search_tag="registered-contract",
        spec_content="registered authorization positive control",
        ccbench_commit="deadbeef",
    )
    summary = campaign_loop.run_campaign(
        cfg, [], PerfConfig(records=1, threads=1),
        _AUTH_CONTRACT.env_tag, _AUTH_CONTRACT.clocks_per_us,
        numactl=list(_AUTH_CONTRACT.numactl), do_bench=False,
        output_root=out_root,
        authorization_contract=_AUTHORIZATION,
        build_context=_BUILD_CONTEXT, declared_use_class="official",
        log=lambda *_args: None,
    )
    assert summary.total == 0 and summary.results == []
    expected = campaign_layout(str(ident.campaign_id(_bound(cfg))), out_root)
    assert summary.layout_root == expected.root
    assert os.path.isdir(expected.root)


_CERTIFIED_WRITER_TARGETS = frozenset({
    "campaign.loop.run_campaign",
    "campaign.pipeline.evaluate",
})
_CERTIFIED_WRITER_OTHER = "<other>"
_CERTIFIED_WRITER_MODULE = "module:"
_CERTIFIED_WRITER_SYMBOL = "symbol:"
_CERTIFIED_WRITER_UNKNOWN = "unknown:"
_CERTIFIED_WRITER_OUT_OF_SCOPE = "out-of-scope:"
_CERTIFIED_WRITER_BUILTIN_GETATTR = "builtin:getattr"
_CERTIFIED_WRITER_PROVEN_LOCAL_GETATTR = "local:getattr-noncanonical-result"


class _CertifiedWriterOutOfScopeReason(enum.Enum):
    LEXICAL_LOCAL_SHADOW = "lexical-local-shadow"
    DEFINITE_NONCANONICAL_REBIND = "definite-noncanonical-rebind"
    PROVEN_NONCANONICAL_GETATTR_RESULT = "proven-noncanonical-getattr-result"


_CERTIFIED_WRITER_SAFE_OUT_OF_SCOPE_REASONS = frozenset({
    _CertifiedWriterOutOfScopeReason.LEXICAL_LOCAL_SHADOW,
    _CertifiedWriterOutOfScopeReason.DEFINITE_NONCANONICAL_REBIND,
    _CertifiedWriterOutOfScopeReason.PROVEN_NONCANONICAL_GETATTR_RESULT,
})


def _certified_writer_normalize_module(name):
    if name == "orchestrator.campaign":
        return "campaign"
    if name.startswith("orchestrator.campaign."):
        return name[len("orchestrator."):]
    return name


class _CertifiedWriterLocalBindings(ast.NodeVisitor):
    """Collect one lexical scope's bindings without entering nested scopes."""

    def __init__(self):
        self.names = set()
        self.global_names = set()
        self.nonlocal_names = set()

    def visit_Name(self, node):
        if isinstance(node.ctx, ast.Store):
            self.names.add(node.id)

    def visit_FunctionDef(self, node):
        self.names.add(node.name)

    visit_AsyncFunctionDef = visit_FunctionDef

    def visit_ClassDef(self, node):
        self.names.add(node.name)

    def visit_Lambda(self, node):
        return None

    def visit_ListComp(self, node):
        # Comprehension iteration variables stay in the implicit scope, but a
        # walrus target is local to the containing scope.  Walk only evaluated
        # expressions so NamedExpr Store nodes are predeclared outside.
        for generator in node.generators:
            self.visit(generator.iter)
            for condition in generator.ifs:
                self.visit(condition)
        self.visit(node.elt)

    visit_SetComp = visit_ListComp
    visit_GeneratorExp = visit_ListComp

    def visit_DictComp(self, node):
        for generator in node.generators:
            self.visit(generator.iter)
            for condition in generator.ifs:
                self.visit(condition)
        self.visit(node.key)
        self.visit(node.value)

    def visit_Import(self, node):
        for alias in node.names:
            self.names.add(alias.asname or alias.name.split(".", 1)[0])

    def visit_ImportFrom(self, node):
        for alias in node.names:
            if alias.name != "*":
                self.names.add(alias.asname or alias.name)

    def visit_Global(self, node):
        self.global_names.update(node.names)

    def visit_Nonlocal(self, node):
        self.nonlocal_names.update(node.names)

    def visit_ExceptHandler(self, node):
        if node.name:
            self.names.add(node.name)
        self.generic_visit(node)


class _CertifiedWriterResolver(ast.NodeVisitor):
    """Resolve certified-writer calls by import provenance and lexical scope."""

    def __init__(self, rel_path, module_name):
        self.rel_path = rel_path
        self.module_name = _certified_writer_normalize_module(module_name)
        self.scopes = [{}]
        self.scope_kinds = ["module"]
        self.scope_globals = [set()]
        self.scope_nonlocals = [set()]
        self.resolved = []
        self.unresolved = []
        self.out_of_scope = []
        self._unresolved_keys = set()
        self._out_of_scope_keys = set()

    @staticmethod
    def _module_value(name):
        return _CERTIFIED_WRITER_MODULE + _certified_writer_normalize_module(name)

    @staticmethod
    def _symbol_value(name):
        return _CERTIFIED_WRITER_SYMBOL + _certified_writer_normalize_module(name)

    @staticmethod
    def _unknown_value(target):
        return _CERTIFIED_WRITER_UNKNOWN + target

    @staticmethod
    def _out_of_scope_value(target, reason):
        assert isinstance(reason, _CertifiedWriterOutOfScopeReason)
        return f"{_CERTIFIED_WRITER_OUT_OF_SCOPE}{reason.value}:{target}"

    @staticmethod
    def _targets(values):
        return {value for value in values if value in _CERTIFIED_WRITER_TARGETS}

    @staticmethod
    def _unknown_targets(values):
        return {
            value[len(_CERTIFIED_WRITER_UNKNOWN):]
            for value in values
            if value.startswith(_CERTIFIED_WRITER_UNKNOWN)
        }

    @staticmethod
    def _out_of_scope_entries(values):
        entries = set()
        for value in values:
            if not value.startswith(_CERTIFIED_WRITER_OUT_OF_SCOPE):
                continue
            payload = value[len(_CERTIFIED_WRITER_OUT_OF_SCOPE):]
            reason_value, target = payload.split(":", 1)
            entries.add((target, _CertifiedWriterOutOfScopeReason(reason_value)))
        return entries

    @classmethod
    def _out_of_scope_targets(cls, values):
        return {target for target, _reason in cls._out_of_scope_entries(values)}

    @staticmethod
    def _spelled_targets(name):
        return {
            target for target in _CERTIFIED_WRITER_TARGETS
            if target.rsplit(".", 1)[1] == name
        }

    def _lookup(self, name):
        skip_class_scopes = self.scope_kinds[-1] in {
            "function", "lambda", "comprehension",
        }
        for scope, kind in zip(reversed(self.scopes),
                               reversed(self.scope_kinds)):
            if skip_class_scopes and kind == "class":
                continue
            if name in scope:
                return scope[name]
        if name == "getattr":
            return frozenset({_CERTIFIED_WRITER_BUILTIN_GETATTR})
        return frozenset({_CERTIFIED_WRITER_OTHER})

    def _bind(self, name, values):
        self.scopes[-1][name] = frozenset(values)

    def _bind_at(self, scope_index, name, values):
        self.scopes[scope_index][name] = frozenset(values)

    def _binding_scope_index(self):
        for index in range(len(self.scope_kinds) - 1, -1, -1):
            if self.scope_kinds[index] != "comprehension":
                return index
        return 0

    def _assignment_scope(self, name, scope_index=None):
        index = len(self.scopes) - 1 if scope_index is None else scope_index
        if name in self.scope_globals[index]:
            return 0, True
        if name in self.scope_nonlocals[index]:
            for outer in range(index - 1, 0, -1):
                if self.scope_kinds[outer] in {"function", "lambda"}:
                    return outer, True
            return 0, True
        return index, False

    def _candidate_targets(self, values):
        return (
            self._targets(values)
            | self._unknown_targets(values)
            | self._out_of_scope_targets(values)
        )

    def _replacement_values(self, name, values, *, scope_index=None,
                            uncertain=False):
        """Keep canonical provenance when a binding ceases to be canonical."""
        index = len(self.scopes) - 1 if scope_index is None else scope_index
        old_values = self.scopes[index].get(
            name, frozenset({_CERTIFIED_WRITER_OTHER}),
        )
        old_targets = self._candidate_targets(old_values)
        new_targets = self._candidate_targets(values)
        if new_targets:
            return frozenset(values)
        candidates = old_targets | self._spelled_targets(name)
        if not candidates:
            return frozenset(values)
        if uncertain or self.scope_kinds[index] == "class":
            return frozenset(self._unknown_value(target) for target in candidates)
        return frozenset(
            self._out_of_scope_value(
                target,
                _CertifiedWriterOutOfScopeReason.DEFINITE_NONCANONICAL_REBIND,
            )
            for target in candidates
        )

    def _local_other_values(self, name):
        targets = self._spelled_targets(name)
        return frozenset(
            self._out_of_scope_value(
                target,
                _CertifiedWriterOutOfScopeReason.LEXICAL_LOCAL_SHADOW,
            )
            for target in targets
        ) if targets else frozenset({_CERTIFIED_WRITER_OTHER})

    def _snapshot_scopes(self):
        return [dict(scope) for scope in self.scopes]

    def _restore_scopes(self, snapshot):
        self.scopes = [dict(scope) for scope in snapshot]

    def _merge_path_scopes(self, paths):
        merged = []
        for scope_index in range(len(self.scopes)):
            names = set().union(*(path[scope_index] for path in paths))
            scope = {}
            for name in names:
                values_by_path = [
                    path[scope_index].get(
                        name, frozenset({_CERTIFIED_WRITER_OTHER}),
                    )
                    for path in paths
                ]
                if all(values == values_by_path[0]
                       for values in values_by_path[1:]):
                    scope[name] = values_by_path[0]
                    continue
                targets = set().union(
                    *(self._candidate_targets(values)
                      for values in values_by_path)
                )
                scope[name] = frozenset(
                    self._unknown_value(target) for target in targets
                ) if targets else frozenset({_CERTIFIED_WRITER_OTHER})
            merged.append(scope)
        self.scopes = merged

    def _relative_import_base(self, module, level):
        if not level:
            return _certified_writer_normalize_module(module or "")
        module_parts = self.module_name.split(".")
        package = (
            module_parts
            if Path(self.rel_path).name == "__init__.py"
            else module_parts[:-1]
        )
        keep = len(package) - (level - 1)
        base = package[:max(keep, 0)]
        if module:
            base.extend(module.split("."))
        return _certified_writer_normalize_module(".".join(base))

    def _imported_value(self, full_name):
        normalized = _certified_writer_normalize_module(full_name)
        if normalized == "builtins.getattr":
            return frozenset({_CERTIFIED_WRITER_BUILTIN_GETATTR})
        if normalized in _CERTIFIED_WRITER_TARGETS:
            return frozenset({normalized})
        if normalized in {"campaign", "campaign.loop", "campaign.pipeline"}:
            return frozenset({self._module_value(normalized)})
        return frozenset({self._symbol_value(normalized)})

    def _attribute_values(self, base_values, attr):
        values = set()
        for value in base_values:
            if value.startswith(_CERTIFIED_WRITER_MODULE):
                module = value[len(_CERTIFIED_WRITER_MODULE):]
                full_name = _certified_writer_normalize_module(f"{module}.{attr}")
                if full_name == "builtins.getattr":
                    values.add(_CERTIFIED_WRITER_BUILTIN_GETATTR)
                elif full_name in _CERTIFIED_WRITER_TARGETS:
                    values.add(full_name)
                else:
                    values.add(self._module_value(full_name))
            elif value.startswith(_CERTIFIED_WRITER_UNKNOWN):
                values.add(value)
            elif value.startswith(_CERTIFIED_WRITER_OUT_OF_SCOPE):
                values.add(value)
            else:
                values.add(_CERTIFIED_WRITER_OTHER)
        return frozenset(values or {_CERTIFIED_WRITER_OTHER})

    def _expr_values(self, node):
        if isinstance(node, ast.Name):
            return self._lookup(node.id)
        if isinstance(node, ast.Attribute):
            return self._attribute_values(self._expr_values(node.value), node.attr)
        if isinstance(node, (ast.BoolOp, ast.IfExp)):
            children = node.values if isinstance(node, ast.BoolOp) else (node.body, node.orelse)
            values = set()
            for child in children:
                values.update(self._expr_values(child))
            return frozenset(values or {_CERTIFIED_WRITER_OTHER})
        if isinstance(node, ast.NamedExpr):
            return self._named_expr_values(node)
        if isinstance(node, ast.Lambda):
            return frozenset({_CERTIFIED_WRITER_OTHER})
        if isinstance(node, ast.Call):
            targets = self._dynamic_call_targets(node)
            if targets:
                return frozenset(self._unknown_value(target) for target in targets)
        if isinstance(node, ast.Subscript):
            targets = self._canonical_provenance_targets(node)
            if targets:
                return frozenset(self._unknown_value(target) for target in targets)
        return frozenset({_CERTIFIED_WRITER_OTHER})

    def _dynamic_call_targets(self, node):
        if not isinstance(node, ast.Call):
            return set()
        func_values = self._expr_values(node.func)
        if (_CERTIFIED_WRITER_BUILTIN_GETATTR in func_values
                and len(node.args) >= 2):
            base_values = self._expr_values(node.args[0])
            if (isinstance(node.args[1], ast.Constant)
                    and isinstance(node.args[1].value, str)):
                values = self._attribute_values(
                    base_values, node.args[1].value,
                )
                return self._targets(values) | self._unknown_targets(values)

            # The attribute name is runtime data.  If its base can be a
            # canonical module, conservatively retain every target exported by
            # that module as UNRESOLVED instead of silently dropping the call.
            targets = set()
            for value in base_values:
                if not value.startswith(_CERTIFIED_WRITER_MODULE):
                    continue
                module = value[len(_CERTIFIED_WRITER_MODULE):]
                targets.update(
                    target for target in _CERTIFIED_WRITER_TARGETS
                    if target.rsplit(".", 1)[0] == module
                )
            return targets
        partial_values = {
            self._module_value("functools.partial"),
            self._symbol_value("functools.partial"),
        }
        if func_values & partial_values:
            targets = set()
            for arg in node.args:
                values = self._expr_values(arg)
                targets.update(self._targets(values))
                targets.update(self._unknown_targets(values))
            return targets
        return set()

    def _shadowed_getattr_targets(self, node):
        if not isinstance(node, ast.Call) or len(node.args) < 2:
            return set()
        func_values = self._expr_values(node.func)
        if _CERTIFIED_WRITER_BUILTIN_GETATTR in func_values:
            return set()
        if _CERTIFIED_WRITER_PROVEN_LOCAL_GETATTR not in func_values:
            return set()
        is_getattr_spelling = (
            isinstance(node.func, ast.Name) and node.func.id == "getattr"
        ) or (
            isinstance(node.func, ast.Attribute)
            and node.func.attr == "getattr"
        )
        if not is_getattr_spelling:
            return set()
        if not (isinstance(node.args[1], ast.Constant)
                and isinstance(node.args[1].value, str)):
            return set()
        values = self._attribute_values(
            self._expr_values(node.args[0]), node.args[1].value,
        )
        return self._targets(values) | self._unknown_targets(values)

    def _unmodelled_shadowed_getattr_targets(self, node):
        if not isinstance(node, ast.Call) or len(node.args) < 2:
            return set()
        func_values = self._expr_values(node.func)
        if func_values & {
                _CERTIFIED_WRITER_BUILTIN_GETATTR,
                _CERTIFIED_WRITER_PROVEN_LOCAL_GETATTR,
        }:
            return set()
        is_getattr_spelling = (
            isinstance(node.func, ast.Name) and node.func.id == "getattr"
        ) or (
            isinstance(node.func, ast.Attribute)
            and node.func.attr == "getattr"
        )
        if not is_getattr_spelling:
            return set()
        values = self._expr_values(node.args[0])
        targets = set()
        for value in values:
            if not value.startswith(_CERTIFIED_WRITER_MODULE):
                continue
            module = value[len(_CERTIFIED_WRITER_MODULE):]
            targets.update(
                target for target in _CERTIFIED_WRITER_TARGETS
                if target.rsplit(".", 1)[0] == module
            )
        return targets

    def _targets_in_expr(self, node):
        targets = set()
        for child in ast.walk(node):
            if isinstance(child, (ast.Name, ast.Attribute)):
                values = self._expr_values(child)
                targets.update(self._targets(values))
                targets.update(self._unknown_targets(values))
            elif isinstance(child, ast.Call):
                targets.update(self._dynamic_call_targets(child))
                targets.update(
                    self._unmodelled_shadowed_getattr_targets(child)
                )
        return targets

    def _canonical_provenance_targets(self, node):
        """Return targets exposed to an unsupported callable-producing form."""
        targets = set()
        for child in ast.walk(node):
            if not isinstance(child, (ast.Name, ast.Attribute)):
                continue
            values = self._expr_values(child)
            targets.update(self._targets(values))
            targets.update(self._unknown_targets(values))
            for value in values:
                if not value.startswith(_CERTIFIED_WRITER_MODULE):
                    continue
                module = value[len(_CERTIFIED_WRITER_MODULE):]
                targets.update(
                    target for target in _CERTIFIED_WRITER_TARGETS
                    if target.rsplit(".", 1)[0] == module
                )
        return targets

    def _out_of_scope_entries_in_expr(self, node):
        entries = set()
        for child in ast.walk(node):
            if isinstance(child, (ast.Name, ast.Attribute)):
                entries.update(
                    self._out_of_scope_entries(self._expr_values(child))
                )
            elif isinstance(child, ast.Call):
                entries.update(
                    (target,
                     _CertifiedWriterOutOfScopeReason.PROVEN_NONCANONICAL_GETATTR_RESULT)
                    for target in self._shadowed_getattr_targets(child)
                )
        return entries

    @staticmethod
    def _traceable_alias_expr(node):
        if isinstance(node, (ast.Name, ast.Attribute, ast.Constant)):
            return True
        if isinstance(node, ast.BoolOp):
            return all(_CertifiedWriterResolver._traceable_alias_expr(value)
                       for value in node.values)
        if isinstance(node, ast.IfExp):
            return (
                _CertifiedWriterResolver._traceable_alias_expr(node.body)
                and _CertifiedWriterResolver._traceable_alias_expr(node.orelse)
            )
        return False

    @staticmethod
    def _assignment_names(node):
        if isinstance(node, ast.Name):
            return {node.id}
        if isinstance(node, (ast.Tuple, ast.List)):
            names = set()
            for element in node.elts:
                names.update(_CertifiedWriterResolver._assignment_names(element))
            return names
        if isinstance(node, ast.Starred):
            return _CertifiedWriterResolver._assignment_names(node.value)
        return set()

    def _bind_assignment_target(self, node, values, *, scope_index=None,
                                uncertain=False):
        names = self._assignment_names(node)
        if isinstance(node, ast.Name):
            index, indirect = self._assignment_scope(node.id, scope_index)
            if indirect:
                candidates = (
                    self._candidate_targets(values)
                    | self._candidate_targets(
                        self.scopes[index].get(
                            node.id, frozenset({_CERTIFIED_WRITER_OTHER}),
                        )
                    )
                    | self._spelled_targets(node.id)
                )
                values = (
                    {self._unknown_value(target) for target in candidates}
                    or {_CERTIFIED_WRITER_OTHER}
                )
                uncertain = True
            replacement = self._replacement_values(
                node.id, values, scope_index=index, uncertain=uncertain,
            )
            self._bind_at(index, node.id, replacement)
        else:
            for name in names:
                index, indirect = self._assignment_scope(name, scope_index)
                replacement = self._replacement_values(
                    name, {_CERTIFIED_WRITER_OTHER}, scope_index=index,
                    uncertain=uncertain or indirect,
                )
                self._bind_at(index, name, replacement)

    def _record(self, collection, node, target, display=None, reason=None):
        display = display or ast.unparse(node)
        if collection is self.out_of_scope:
            assert isinstance(reason, _CertifiedWriterOutOfScopeReason)
        record = (
            self.rel_path,
            getattr(node, "lineno", 0),
            getattr(node, "col_offset", 0) + 1,
            display,
            target,
            node if isinstance(node, ast.Call) else None,
            reason,
        )
        if collection is self.unresolved:
            key = record[:5]
            if key in self._unresolved_keys:
                return
            self._unresolved_keys.add(key)
        elif collection is self.out_of_scope:
            key = record[:5] + (reason,)
            if key in self._out_of_scope_keys:
                return
            self._out_of_scope_keys.add(key)
        collection.append(record)

    def _record_unresolved(self, node, targets, display=None):
        for target in sorted(targets):
            self._record(self.unresolved, node, target, display=display)

    def _record_out_of_scope(self, node, entries, display=None):
        for target, reason in sorted(entries, key=lambda entry: (
                entry[0], entry[1].value)):
            self._record(
                self.out_of_scope, node, target, display=display,
                reason=reason,
            )

    def _scope_declarations(self, body):
        collector = _CertifiedWriterLocalBindings()
        for statement in body:
            collector.visit(statement)
        local_names = collector.names - collector.global_names - collector.nonlocal_names
        scope = {name: self._local_other_values(name) for name in local_names}
        return scope, collector.global_names, collector.nonlocal_names

    def _argument_defaults(self, arguments):
        positional = list(arguments.posonlyargs) + list(arguments.args)
        default_values = {}
        for argument, default in zip(positional[-len(arguments.defaults):],
                                     arguments.defaults):
            default_values[argument.arg] = self._expr_values(default)
            if not self._traceable_alias_expr(default):
                self.visit(default)
        for argument, default in zip(arguments.kwonlyargs,
                                     arguments.kw_defaults):
            if default is None:
                continue
            default_values[argument.arg] = self._expr_values(default)
            if not self._traceable_alias_expr(default):
                self.visit(default)
        return positional, default_values

    def _visit_argument_annotations(self, arguments):
        annotated = (
            list(arguments.posonlyargs) + list(arguments.args)
            + list(arguments.kwonlyargs)
        )
        if arguments.vararg:
            annotated.append(arguments.vararg)
        if arguments.kwarg:
            annotated.append(arguments.kwarg)
        for argument in annotated:
            if argument.annotation is not None:
                self.visit(argument.annotation)

    def _bind_definition_name(self, name, values=None):
        values = self._replacement_values(
            name, values or {_CERTIFIED_WRITER_OTHER},
        )
        self._bind(name, values)

    @staticmethod
    def _proven_noncanonical_getattr_definition(node):
        return (
            node.name == "getattr"
            and not node.decorator_list
            and len(node.body) == 1
            and isinstance(node.body[0], ast.Return)
            and isinstance(node.body[0].value, ast.Lambda)
        )

    def visit_Import(self, node):
        for alias in node.names:
            if alias.asname:
                self._bind(alias.asname, {self._module_value(alias.name)})
            else:
                root = alias.name.split(".", 1)[0]
                self._bind(root, {self._module_value(root)})

    def visit_ImportFrom(self, node):
        base = self._relative_import_base(node.module, node.level)
        for alias in node.names:
            if alias.name == "*":
                targets = {
                    target for target in _CERTIFIED_WRITER_TARGETS
                    if target.rsplit(".", 1)[0] == base
                }
                self._record_unresolved(node, targets)
                continue
            full_name = f"{base}.{alias.name}" if base else alias.name
            self._bind(alias.asname or alias.name, self._imported_value(full_name))

    def visit_FunctionDef(self, node):
        # Python evaluates decorators, defaults, and annotations in the outer
        # scope before installing the newly defined name.
        for decorator in node.decorator_list:
            self.visit(decorator)
        positional, default_values = self._argument_defaults(node.args)
        self._visit_argument_annotations(node.args)
        if node.returns is not None:
            self.visit(node.returns)
        for type_parameter in getattr(node, "type_params", ()):  # Python 3.12+
            self.visit(type_parameter)
        definition_values = (
            {_CERTIFIED_WRITER_PROVEN_LOCAL_GETATTR}
            if self._proven_noncanonical_getattr_definition(node)
            else None
        )
        self._bind_definition_name(node.name, definition_values)

        scope, global_names, nonlocal_names = self._scope_declarations(node.body)
        arguments = positional + list(node.args.kwonlyargs)
        if node.args.vararg:
            arguments.append(node.args.vararg)
        if node.args.kwarg:
            arguments.append(node.args.kwarg)
        for argument in arguments:
            scope[argument.arg] = default_values.get(
                argument.arg, self._local_other_values(argument.arg),
            )
        self.scopes.append(scope)
        self.scope_kinds.append("function")
        self.scope_globals.append(global_names)
        self.scope_nonlocals.append(nonlocal_names)
        for statement in node.body:
            self.visit(statement)
        self.scope_nonlocals.pop()
        self.scope_globals.pop()
        self.scope_kinds.pop()
        self.scopes.pop()

    visit_AsyncFunctionDef = visit_FunctionDef

    def visit_ClassDef(self, node):
        for expression in [*node.decorator_list, *node.bases, *node.keywords]:
            self.visit(expression)
        for type_parameter in getattr(node, "type_params", ()):  # Python 3.12+
            self.visit(type_parameter)
        self._bind_definition_name(node.name)
        _scope, global_names, nonlocal_names = self._scope_declarations(node.body)
        ambiguous_scope = {}
        for name in _scope:
            candidates = self._candidate_targets(self._lookup(name))
            candidates.update(self._spelled_targets(name))
            if candidates:
                ambiguous_scope[name] = frozenset(
                    self._unknown_value(target) for target in candidates
                )
        self.scopes.append(ambiguous_scope)
        self.scope_kinds.append("class")
        self.scope_globals.append(global_names)
        self.scope_nonlocals.append(nonlocal_names)
        for statement in node.body:
            self.visit(statement)
        self.scope_nonlocals.pop()
        self.scope_globals.pop()
        self.scope_kinds.pop()
        self.scopes.pop()

    def visit_Lambda(self, node):
        positional, default_values = self._argument_defaults(node.args)
        self._visit_argument_annotations(node.args)
        scope = {}
        arguments = (
            positional + list(node.args.kwonlyargs)
        )
        if node.args.vararg:
            arguments.append(node.args.vararg)
        if node.args.kwarg:
            arguments.append(node.args.kwarg)
        for argument in arguments:
            scope[argument.arg] = default_values.get(
                argument.arg, self._local_other_values(argument.arg),
            )
        self.scopes.append(scope)
        self.scope_kinds.append("lambda")
        self.scope_globals.append(set())
        self.scope_nonlocals.append(set())
        self.visit(node.body)
        self.scope_nonlocals.pop()
        self.scope_globals.pop()
        self.scope_kinds.pop()
        self.scopes.pop()

    def visit_Assign(self, node):
        if isinstance(node.value, ast.Lambda):
            self.visit(node.value)
            for target in node.targets:
                self._bind_assignment_target(
                    target, {_CERTIFIED_WRITER_OTHER},
                )
            return
        if isinstance(node.value, ast.Subscript):
            values = self._expr_values(node.value)
            unknown = self._unknown_targets(values)
            if unknown:
                self._record_unresolved(node.value, unknown)
                for target in node.targets:
                    self._bind_assignment_target(
                        target, values, uncertain=True,
                    )
                return
        if self._traceable_alias_expr(node.value):
            values = self._expr_values(node.value)
            unknown = self._unknown_targets(values)
            if unknown:
                self._record_unresolved(node.value, unknown)
            canonical = self._targets(values)
            if canonical and not all(isinstance(target, ast.Name)
                                     for target in node.targets):
                # Storing a certified callable behind an attribute/subscript
                # leaves a callable container that direct-call provenance can
                # no longer close.
                self._record_unresolved(node.value, canonical)
                for target in node.targets:
                    self._bind_assignment_target(
                        target, {_CERTIFIED_WRITER_OTHER},
                    )
                return
            for target in node.targets:
                self._bind_assignment_target(target, values)
            return

        overwritten = set()
        for target in node.targets:
            for name in self._assignment_names(target):
                values = self._lookup(name)
                overwritten.update(self._targets(values))
                overwritten.update(self._unknown_targets(values))
        if overwritten:
            self._record_unresolved(node.value, overwritten)
        self.visit(node.value)
        replacement = (
            {self._unknown_value(target) for target in overwritten}
            or {_CERTIFIED_WRITER_OTHER}
        )
        for target in node.targets:
            self._bind_assignment_target(
                target, replacement, uncertain=True,
            )

    def visit_AnnAssign(self, node):
        # Value-less annotations still evaluate their annotation expression in
        # module/class scopes.  Visiting everywhere is the conservative choice
        # when postponed-annotation details are not modelled.
        self.visit(node.annotation)
        if node.value is None:
            # A value-less annotation does not execute a store and therefore
            # must not erase an existing runtime binding.
            return
        proxy = ast.Assign(targets=[node.target], value=node.value)
        ast.copy_location(proxy, node)
        self.visit_Assign(proxy)

    def _named_expr_values(self, node):
        # Walrus targets are Store nodes.  Evaluate the value first, then bind
        # the target in the containing (non-comprehension) scope; never treat
        # the Store-side Name as a callable reference.
        scope_index = self._binding_scope_index()
        if isinstance(node.value, ast.Lambda):
            self.visit(node.value)
            values = frozenset({_CERTIFIED_WRITER_OTHER})
            uncertain = False
        else:
            values = self._expr_values(node.value)
            uncertain = False
            if not self._traceable_alias_expr(node.value):
                overwritten = set()
                for name in self._assignment_names(node.target):
                    old_values = self.scopes[scope_index].get(
                        name, frozenset({_CERTIFIED_WRITER_OTHER}),
                    )
                    overwritten.update(self._targets(old_values))
                    overwritten.update(self._unknown_targets(old_values))
                self._record_unresolved(node.value, overwritten)
                self.visit(node.value)
                values = frozenset(
                    {self._unknown_value(target) for target in overwritten}
                    or {_CERTIFIED_WRITER_OTHER}
                )
                uncertain = True
        self._bind_assignment_target(
            node.target, values, scope_index=scope_index,
            uncertain=uncertain,
        )
        return values

    def visit_NamedExpr(self, node):
        self._named_expr_values(node)

    def visit_AugAssign(self, node):
        targets = set()
        for name in self._assignment_names(node.target):
            values = self._lookup(name)
            targets.update(self._targets(values))
            targets.update(self._unknown_targets(values))
        self._record_unresolved(node, targets)
        self.visit(node.value)
        self._bind_assignment_target(
            node.target,
            {self._unknown_value(target) for target in targets}
            or {_CERTIFIED_WRITER_OTHER},
        )

    def visit_For(self, node):
        self.visit(node.iter)
        before = self._snapshot_scopes()
        definitely_nonempty = (
            isinstance(node.iter, (ast.Tuple, ast.List))
            and bool(node.iter.elts)
            and not any(isinstance(element, ast.Starred)
                        for element in node.iter.elts)
        )
        if definitely_nonempty:
            # A literal tuple/list runs in order, so the post-loop target is
            # the final element rather than an arbitrary union of iterations.
            assigned_values = self._expr_values(node.iter.elts[-1])
            uncertain = False
        else:
            assigned_values = {_CERTIFIED_WRITER_OTHER}
            uncertain = True

        self._bind_assignment_target(
            node.target, assigned_values, uncertain=uncertain,
        )
        for statement in node.body:
            self.visit(statement)
        iterated = self._snapshot_scopes()

        # Only a statically non-empty literal sequence proves that the old
        # target binding cannot survive.  Every other loop keeps both paths;
        # disagreement involving canonical provenance becomes UNRESOLVED.
        if definitely_nonempty:
            self._restore_scopes(iterated)
        else:
            self._restore_scopes(before)
            self._merge_path_scopes([before, iterated])
        loop_exit = self._snapshot_scopes()
        for statement in node.orelse:
            self.visit(statement)
        else_exit = self._snapshot_scopes()
        if node.orelse and any(
                isinstance(child, ast.Break)
                for statement in node.body for child in ast.walk(statement)):
            self._restore_scopes(loop_exit)
            self._merge_path_scopes([loop_exit, else_exit])

    visit_AsyncFor = visit_For

    def visit_While(self, node):
        self.visit(node.test)
        before = self._snapshot_scopes()
        for statement in node.body:
            self.visit(statement)
        iterated = self._snapshot_scopes()
        self._restore_scopes(before)
        self._merge_path_scopes([before, iterated])
        loop_exit = self._snapshot_scopes()
        for statement in node.orelse:
            self.visit(statement)
        else_exit = self._snapshot_scopes()
        if node.orelse and any(
                isinstance(child, ast.Break)
                for statement in node.body for child in ast.walk(statement)):
            self._restore_scopes(loop_exit)
            self._merge_path_scopes([loop_exit, else_exit])

    def visit_If(self, node):
        self.visit(node.test)
        before = self._snapshot_scopes()
        for statement in node.body:
            self.visit(statement)
        body_path = self._snapshot_scopes()
        self._restore_scopes(before)
        for statement in node.orelse:
            self.visit(statement)
        else_path = self._snapshot_scopes()
        self._restore_scopes(before)
        self._merge_path_scopes([body_path, else_path])

    def visit_Try(self, node):
        before = self._snapshot_scopes()
        for statement in [*node.body, *node.orelse]:
            self.visit(statement)
        paths = [self._snapshot_scopes()]
        for handler in node.handlers:
            self._restore_scopes(before)
            if handler.type is not None:
                self.visit(handler.type)
            if handler.name:
                self._bind(
                    handler.name, {_CERTIFIED_WRITER_OTHER},
                )
            for statement in handler.body:
                self.visit(statement)
            paths.append(self._snapshot_scopes())
        self._restore_scopes(before)
        self._merge_path_scopes(paths)
        for statement in node.finalbody:
            self.visit(statement)

    visit_TryStar = visit_Try

    def visit_Match(self, node):
        self.visit(node.subject)
        before = self._snapshot_scopes()
        paths = [before]
        for case in node.cases:
            self._restore_scopes(before)
            if case.guard is not None:
                self.visit(case.guard)
            for statement in case.body:
                self.visit(statement)
            paths.append(self._snapshot_scopes())
        self._restore_scopes(before)
        self._merge_path_scopes(paths)

    def visit_With(self, node):
        for item in node.items:
            self.visit(item.context_expr)
            if item.optional_vars:
                self._bind_assignment_target(
                    item.optional_vars, {_CERTIFIED_WRITER_OTHER},
                )
        for statement in node.body:
            self.visit(statement)

    visit_AsyncWith = visit_With

    def _mark_deferred_namedexprs_unresolved(self, expressions):
        for expression in expressions:
            for child in ast.walk(expression):
                if not isinstance(child, ast.NamedExpr):
                    continue
                scope_index = self._binding_scope_index()
                candidates = self._candidate_targets(
                    self._expr_values(child.value)
                )
                for name in self._assignment_names(child.target):
                    candidates.update(self._candidate_targets(
                        self.scopes[scope_index].get(
                            name, frozenset({_CERTIFIED_WRITER_OTHER}),
                        )
                    ))
                    candidates.update(self._spelled_targets(name))
                if not candidates:
                    continue
                self._record_unresolved(child, candidates)
                self._bind_assignment_target(
                    child.target,
                    {self._unknown_value(target) for target in candidates},
                    scope_index=scope_index, uncertain=True,
                )

    def _visit_comprehension(self, node, result_expressions, *, deferred=False):
        first, *rest = node.generators
        self.visit(first.iter)
        scope = {
            name: frozenset({_CERTIFIED_WRITER_OTHER})
            for name in self._assignment_names(first.target)
        }
        self.scopes.append(scope)
        self.scope_kinds.append("comprehension")
        self.scope_globals.append(set())
        self.scope_nonlocals.append(set())
        self._bind_assignment_target(first.target, {_CERTIFIED_WRITER_OTHER})
        definitely_empty = (
            isinstance(first.iter, (ast.Tuple, ast.List))
            and not first.iter.elts
        )
        if deferred or definitely_empty:
            uncertain_expressions = list(result_expressions)
            uncertain_expressions.extend(first.ifs)
            for generator in rest:
                uncertain_expressions.append(generator.iter)
                uncertain_expressions.extend(generator.ifs)
            self._mark_deferred_namedexprs_unresolved(uncertain_expressions)
            self.scope_nonlocals.pop()
            self.scope_globals.pop()
            self.scope_kinds.pop()
            self.scopes.pop()
            return
        for condition in first.ifs:
            self.visit(condition)
        for generator in rest:
            self.visit(generator.iter)
            self._bind_assignment_target(
                generator.target, {_CERTIFIED_WRITER_OTHER},
            )
            for condition in generator.ifs:
                self.visit(condition)
        for expression in result_expressions:
            self.visit(expression)
        self.scope_nonlocals.pop()
        self.scope_globals.pop()
        self.scope_kinds.pop()
        self.scopes.pop()

    def visit_ListComp(self, node):
        self._visit_comprehension(node, [node.elt])

    visit_SetComp = visit_ListComp

    def visit_GeneratorExp(self, node):
        self._visit_comprehension(node, [node.elt], deferred=True)

    def visit_DictComp(self, node):
        self._visit_comprehension(node, [node.key, node.value])

    def visit_Call(self, node):
        dynamic_targets = self._dynamic_call_targets(node.func)
        if dynamic_targets:
            self._record_unresolved(node.func, dynamic_targets)
        else:
            values = self._expr_values(node.func)
            targets = self._targets(values)
            unknown_targets = self._unknown_targets(values)
            out_of_scope_entries = self._out_of_scope_entries(values)
            if unknown_targets:
                self._record_unresolved(node.func, unknown_targets)
            elif targets:
                for target in sorted(targets):
                    self._record(
                        self.resolved, node, target,
                        display=ast.unparse(node.func),
                    )
            elif out_of_scope_entries:
                self._record_out_of_scope(node.func, out_of_scope_entries)
            else:
                nested_targets = self._targets_in_expr(node.func)
                if nested_targets:
                    self._record_unresolved(node.func, nested_targets)
                else:
                    nested_out_of_scope = self._out_of_scope_entries_in_expr(
                        node.func,
                    )
                    if nested_out_of_scope:
                        self._record_out_of_scope(
                            node.func, nested_out_of_scope,
                        )

        if self._dynamic_call_targets(node):
            self._record_unresolved(node.func, self._dynamic_call_targets(node))
        for argument in node.args:
            self.visit(argument)
        for keyword in node.keywords:
            self.visit(keyword.value)

    def visit_Name(self, node):
        if not isinstance(node.ctx, ast.Load):
            return
        values = self._expr_values(node)
        targets = self._targets(values) | self._unknown_targets(values)
        self._record_unresolved(node, targets)
        self._record_out_of_scope(
            node, self._out_of_scope_entries(values),
        )

    def visit_Attribute(self, node):
        values = self._expr_values(node)
        targets = self._targets(values) | self._unknown_targets(values)
        if targets:
            self._record_unresolved(node, targets)
        elif self._out_of_scope_entries(values):
            self._record_out_of_scope(
                node, self._out_of_scope_entries(values),
            )
        else:
            self.visit(node.value)


def _certified_writer_module_name(rel_path):
    parts = list(Path(rel_path).with_suffix("").parts)
    if parts and parts[-1] == "__init__":
        parts.pop()
    return _certified_writer_normalize_module(".".join(parts))


def _certified_writer_resolve_source(source, rel_path, module_name=None):
    tree = ast.parse(source, filename=rel_path)
    resolver = _CertifiedWriterResolver(
        rel_path,
        module_name or _certified_writer_module_name(rel_path),
    )
    resolver.visit(tree)
    return resolver.resolved, resolver.unresolved, resolver.out_of_scope


def _certified_writer_diagnostic(record):
    rel_path, lineno, col, unparsed_func, target, _call = record[:6]
    return f"{rel_path}:{lineno}:{col} {unparsed_func} -> {target}"


def _certified_writer_resolve_path(path, rel_path):
    try:
        with tokenize.open(path) as source_file:
            source = source_file.read()
    except (OSError, SyntaxError, UnicodeError) as exc:
        return [], [], [], {
            "path": rel_path,
            "phase": "decode",
            "error": type(exc).__name__,
            "message": str(exc),
        }
    try:
        resolved, unresolved, out_of_scope = _certified_writer_resolve_source(
            source, rel_path,
        )
    except SyntaxError as exc:
        return [], [], [], {
            "path": rel_path,
            "phase": "parse",
            "error": type(exc).__name__,
            "line": exc.lineno,
            "column": exc.offset,
            "message": exc.msg,
        }
    return resolved, unresolved, out_of_scope, None


def test_certified_writer_authorization_caller_inventory_is_closed():
    """Close repo source outside tests, VCS/worktrees, generated, and vendored trees."""
    from orchestrator.campaign import loop as campaign_loop

    for callable_obj in (campaign_loop.run_campaign, pipeline.evaluate):
        parameter = inspect.signature(callable_obj).parameters["authorization_contract"]
        assert parameter.kind is inspect.Parameter.KEYWORD_ONLY
        assert parameter.default is inspect.Parameter.empty

    fixture_cases = [
        (
            "direct-name.py",
            "from campaign.loop import run_campaign\n"
            "run_campaign(authorization_contract=object())\n",
            "fixture.direct_name",
            collections.Counter({"campaign.loop.run_campaign": 1}),
            collections.Counter(),
        ),
        (
            "module-alias.py",
            "import campaign.loop as L\n"
            "L.run_campaign(authorization_contract=object())\n",
            "fixture.module_alias",
            collections.Counter({"campaign.loop.run_campaign": 1}),
            collections.Counter(),
        ),
        (
            "from-alias.py",
            "from campaign.pipeline import evaluate as ev\n"
            "ev(authorization_contract=object())\n",
            "fixture.from_alias",
            collections.Counter({"campaign.pipeline.evaluate": 1}),
            collections.Counter(),
        ),
        (
            "relative.py",
            "from .pipeline import evaluate\n"
            "evaluate(authorization_contract=object())\n",
            "campaign.relative_fixture",
            collections.Counter({"campaign.pipeline.evaluate": 1}),
            collections.Counter(),
        ),
        (
            "fully-qualified.py",
            "import campaign.loop\n"
            "campaign.loop.run_campaign(authorization_contract=object())\n",
            "fixture.fully_qualified",
            collections.Counter({"campaign.loop.run_campaign": 1}),
            collections.Counter(),
        ),
        (
            "default-binding.py",
            "from campaign import pipeline\n"
            "def drive(evaluate_fn=pipeline.evaluate):\n"
            "    evaluate_fn(authorization_contract=object())\n",
            "fixture.default_binding",
            collections.Counter({"campaign.pipeline.evaluate": 1}),
            collections.Counter(),
        ),
        (
            "fallback-binding.py",
            "from campaign import pipeline\n"
            "def drive(evaluate_fn=None):\n"
            "    evaluate_fn = evaluate_fn or pipeline.evaluate\n"
            "    evaluate_fn(authorization_contract=object())\n",
            "fixture.fallback_binding",
            collections.Counter({"campaign.pipeline.evaluate": 1}),
            collections.Counter(),
        ),
        (
            "shadow.py",
            "from campaign.loop import run_campaign as certified\n"
            "def argument_shadow(run_campaign):\n"
            "    run_campaign()\n"
            "def assignment_shadow():\n"
            "    run_campaign = lambda: None\n"
            "    run_campaign()\n"
            "def definition_shadow():\n"
            "    def run_campaign():\n"
            "        return None\n"
            "    run_campaign()\n"
            "certified(authorization_contract=object())\n",
            "fixture.shadow",
            collections.Counter({"campaign.loop.run_campaign": 1}),
            collections.Counter({"campaign.loop.run_campaign": 3}),
        ),
    ]
    assert len(fixture_cases) == 8
    assert {case[0] for case in fixture_cases} == {
        "direct-name.py",
        "module-alias.py",
        "from-alias.py",
        "relative.py",
        "fully-qualified.py",
        "default-binding.py",
        "fallback-binding.py",
        "shadow.py",
    }
    for rel_path, source, module_name, expected, expected_out_of_scope in fixture_cases:
        resolved, unresolved, out_of_scope = _certified_writer_resolve_source(
            source, rel_path, module_name,
        )
        expected_count = sum(expected.values())
        assert expected_count > 0
        assert len(resolved) == expected_count, rel_path
        assert collections.Counter(record[4] for record in resolved) == expected
        assert not unresolved, rel_path
        assert len(out_of_scope) == sum(expected_out_of_scope.values()), rel_path
        assert collections.Counter(
            record[4] for record in out_of_scope
        ) == expected_out_of_scope
        assert all(
            any(keyword.arg == "authorization_contract"
                for keyword in record[5].keywords)
            for record in resolved
        ), rel_path

    unresolved_fixtures = [
        (
            "getattr.py",
            "import campaign.loop as L\n"
            "getattr(L, 'run_campaign')()\n",
            "campaign.loop.run_campaign",
        ),
        (
            "getattr-nonliteral.py",
            "import campaign.loop as L\n"
            "name = 'run_campaign'\n"
            "getattr(L, name)()\n",
            "campaign.loop.run_campaign",
        ),
        (
            "getattr-assignment-alias.py",
            "import campaign.loop as L\n"
            "g = getattr\n"
            "g(L, 'run_campaign')()\n",
            "campaign.loop.run_campaign",
        ),
        (
            "builtins-getattr.py",
            "import builtins\n"
            "import campaign.loop as L\n"
            "builtins.getattr(L, 'run_campaign')()\n",
            "campaign.loop.run_campaign",
        ),
        (
            "builtins-module-alias.py",
            "import builtins as b\n"
            "from campaign import pipeline\n"
            "b.getattr(pipeline, 'evaluate')()\n",
            "campaign.pipeline.evaluate",
        ),
        (
            "builtins-getattr-import-alias.py",
            "from builtins import getattr as g\n"
            "from campaign import pipeline\n"
            "g(pipeline, 'evaluate')()\n",
            "campaign.pipeline.evaluate",
        ),
        (
            "partial.py",
            "from functools import partial\n"
            "from campaign.loop import run_campaign\n"
            "partial(run_campaign)()\n",
            "campaign.loop.run_campaign",
        ),
        (
            "container.py",
            "from campaign.pipeline import evaluate\n"
            "[evaluate][0]()\n",
            "campaign.pipeline.evaluate",
        ),
    ]
    assert len(unresolved_fixtures) == 8
    assert {case[0] for case in unresolved_fixtures} == {
        "getattr.py",
        "getattr-nonliteral.py",
        "getattr-assignment-alias.py",
        "builtins-getattr.py",
        "builtins-module-alias.py",
        "builtins-getattr-import-alias.py",
        "partial.py",
        "container.py",
    }
    for rel_path, source, expected_target in unresolved_fixtures:
        resolved, unresolved, out_of_scope = _certified_writer_resolve_source(
            source, rel_path, "fixture.unresolved",
        )
        assert len(unresolved) == 1, rel_path
        assert unresolved[0][4] == expected_target
        assert not resolved, rel_path
        assert not out_of_scope, rel_path

    regression_fixtures = [
        (
            "loop-target-merge.py",
            "from campaign.loop import run_campaign as writer\n"
            "for writer in ():\n"
            "    pass\n"
            "writer()\n",
            collections.Counter(),
            collections.Counter({"campaign.loop.run_campaign": 1}),
            collections.Counter(),
        ),
        (
            "valueless-annassign.py",
            "from campaign.loop import run_campaign as writer\n"
            "writer: object\n"
            "writer(authorization_contract=object())\n",
            collections.Counter({"campaign.loop.run_campaign": 1}),
            collections.Counter(),
            collections.Counter(),
        ),
        (
            "lambda-default.py",
            "from campaign import pipeline\n"
            "drive = lambda evaluate_fn=pipeline.evaluate: "
            "evaluate_fn(authorization_contract=object())\n",
            collections.Counter({"campaign.pipeline.evaluate": 1}),
            collections.Counter(),
            collections.Counter(),
        ),
        (
            "class-method-free-name.py",
            "from campaign.loop import run_campaign\n"
            "class Driver:\n"
            "    run_campaign = lambda: None\n"
            "    def drive(self):\n"
            "        run_campaign(authorization_contract=object())\n",
            collections.Counter({"campaign.loop.run_campaign": 1}),
            collections.Counter(),
            collections.Counter(),
        ),
        (
            "walrus-shadow.py",
            "from campaign.loop import run_campaign\n"
            "(run_campaign := lambda: None)\n"
            "run_campaign()\n",
            collections.Counter(),
            collections.Counter(),
            collections.Counter({"campaign.loop.run_campaign": 1}),
        ),
        (
            "shadowed-getattr.py",
            "import campaign.loop as L\n"
            "def getattr(_obj, _name):\n"
            "    return lambda: None\n"
            "getattr(L, 'run_campaign')()\n",
            collections.Counter(),
            collections.Counter(),
            collections.Counter({"campaign.loop.run_campaign": 1}),
        ),
        (
            "class-annassign-call.py",
            "from campaign.loop import run_campaign\n"
            "def build():\n"
            "    class Driver:\n"
            "        marker: run_campaign()\n",
            collections.Counter({"campaign.loop.run_campaign": 1}),
            collections.Counter(),
            collections.Counter(),
        ),
        (
            "empty-loop-body-rebind.py",
            "from campaign.loop import run_campaign as writer\n"
            "def local_fn():\n"
            "    return None\n"
            "for _ in ():\n"
            "    writer = local_fn\n"
            "writer()\n",
            collections.Counter(),
            collections.Counter({"campaign.loop.run_campaign": 1}),
            collections.Counter(),
        ),
        (
            "branch-body-rebind.py",
            "from campaign.loop import run_campaign as writer\n"
            "def local_fn():\n"
            "    return None\n"
            "if condition:\n"
            "    writer = local_fn\n"
            "writer()\n",
            collections.Counter(),
            collections.Counter({"campaign.loop.run_campaign": 1}),
            collections.Counter(),
        ),
        (
            "definite-loop-target.py",
            "from campaign.loop import run_campaign as writer\n"
            "for writer in (lambda: None,):\n"
            "    pass\n"
            "writer()\n",
            collections.Counter(),
            collections.Counter(),
            collections.Counter({"campaign.loop.run_campaign": 1}),
        ),
        (
            "function-default-before-name.py",
            "from campaign.loop import run_campaign\n"
            "def run_campaign(x=run_campaign()):\n"
            "    return x\n",
            collections.Counter({"campaign.loop.run_campaign": 1}),
            collections.Counter(),
            collections.Counter(),
        ),
        (
            "comprehension-walrus-canonical.py",
            "from campaign.loop import run_campaign\n"
            "[(writer := run_campaign) for _ in (0,)]\n"
            "writer()\n",
            collections.Counter({"campaign.loop.run_campaign": 1}),
            collections.Counter(),
            collections.Counter(),
        ),
        (
            "comprehension-walrus-shadow.py",
            "from campaign.loop import run_campaign\n"
            "[(run_campaign := lambda: None) for _ in (0,)]\n"
            "run_campaign()\n",
            collections.Counter(),
            collections.Counter(),
            collections.Counter({"campaign.loop.run_campaign": 1}),
        ),
    ]
    assert len(regression_fixtures) == 13
    assert {case[0] for case in regression_fixtures} == {
        "loop-target-merge.py",
        "valueless-annassign.py",
        "lambda-default.py",
        "class-method-free-name.py",
        "walrus-shadow.py",
        "shadowed-getattr.py",
        "class-annassign-call.py",
        "empty-loop-body-rebind.py",
        "branch-body-rebind.py",
        "definite-loop-target.py",
        "function-default-before-name.py",
        "comprehension-walrus-canonical.py",
        "comprehension-walrus-shadow.py",
    }
    for (rel_path, source, expected_resolved, expected_unresolved,
         expected_out_of_scope) in regression_fixtures:
        resolved, unresolved, out_of_scope = _certified_writer_resolve_source(
            source, rel_path, "fixture.regression",
        )
        assert len(resolved) == sum(expected_resolved.values()), rel_path
        assert collections.Counter(record[4] for record in resolved) == expected_resolved
        assert len(unresolved) == sum(expected_unresolved.values()), rel_path
        assert collections.Counter(record[4] for record in unresolved) == expected_unresolved
        assert len(out_of_scope) == sum(expected_out_of_scope.values()), rel_path
        assert collections.Counter(
            record[4] for record in out_of_scope
        ) == expected_out_of_scope

    out_of_scope_reason_fixtures = [
        (
            "lexical-local-shadow-reason.py",
            "def drive(run_campaign):\n"
            "    run_campaign()\n",
            _CertifiedWriterOutOfScopeReason.LEXICAL_LOCAL_SHADOW,
        ),
        (
            "definite-rebind-reason.py",
            "from campaign.loop import run_campaign\n"
            "run_campaign = lambda: None\n"
            "run_campaign()\n",
            _CertifiedWriterOutOfScopeReason.DEFINITE_NONCANONICAL_REBIND,
        ),
        (
            "shadowed-getattr-reason.py",
            "import campaign.loop as L\n"
            "def getattr(_obj, _name):\n"
            "    return lambda: None\n"
            "getattr(L, 'run_campaign')()\n",
            _CertifiedWriterOutOfScopeReason.PROVEN_NONCANONICAL_GETATTR_RESULT,
        ),
    ]
    assert len(out_of_scope_reason_fixtures) == 3
    for rel_path, source, expected_reason in out_of_scope_reason_fixtures:
        resolved, unresolved, out_of_scope = _certified_writer_resolve_source(
            source, rel_path, "fixture.out_of_scope_reason",
        )
        assert not resolved, rel_path
        assert not unresolved, rel_path
        assert len(out_of_scope) == 1, rel_path
        assert out_of_scope[0][4] == "campaign.loop.run_campaign", rel_path
        assert out_of_scope[0][6] is expected_reason, rel_path

    final_fix_fixtures = [
        (
            "break-loop-else.py",
            "from campaign.loop import run_campaign as writer\n"
            "for _ in (0,):\n"
            "    break\n"
            "else:\n"
            "    writer = None\n"
            "writer()\n",
            collections.Counter({"campaign.loop.run_campaign": 1}),
        ),
        (
            "empty-comprehension-walrus.py",
            "from campaign.loop import run_campaign\n"
            "[(run_campaign := lambda: None) for _ in ()]\n"
            "run_campaign()\n",
            collections.Counter({"campaign.loop.run_campaign": 2}),
        ),
        (
            "global-canonical-binding.py",
            "from campaign.loop import run_campaign\n"
            "writer = lambda: None\n"
            "def bind():\n"
            "    global writer\n"
            "    writer = run_campaign\n"
            "bind()\n"
            "writer()\n",
            collections.Counter({"campaign.loop.run_campaign": 1}),
        ),
        (
            "nonlocal-canonical-binding.py",
            "from campaign.loop import run_campaign\n"
            "def outer():\n"
            "    writer = lambda: None\n"
            "    def bind():\n"
            "        nonlocal writer\n"
            "        writer = run_campaign\n"
            "    bind()\n"
            "    writer()\n",
            collections.Counter({"campaign.loop.run_campaign": 1}),
        ),
        (
            "class-sequential-binding.py",
            "from campaign.loop import run_campaign\n"
            "class Driver:\n"
            "    run_campaign()\n"
            "    run_campaign = lambda: None\n",
            collections.Counter({"campaign.loop.run_campaign": 1}),
        ),
        (
            "vars-dynamic-extraction.py",
            "import campaign.loop as L\n"
            "writer = vars(L)['run_campaign']\n"
            "writer()\n",
            collections.Counter({"campaign.loop.run_campaign": 2}),
        ),
    ]
    assert len(final_fix_fixtures) == 6
    for rel_path, source, expected_unresolved in final_fix_fixtures:
        resolved, unresolved, out_of_scope = _certified_writer_resolve_source(
            source, rel_path, "fixture.final_fix",
        )
        assert not resolved, rel_path
        assert len(unresolved) == sum(expected_unresolved.values()), rel_path
        assert collections.Counter(
            record[4] for record in unresolved
        ) == expected_unresolved
        assert not out_of_scope, rel_path

    with tempfile.TemporaryDirectory(prefix="certified-writer-source-") as tmpdir:
        encoded_path = Path(tmpdir) / "pep263.py"
        encoded_path.write_bytes(
            b"# coding: latin-1\n"
            b"from campaign.loop import run_campaign\n"
            b"label = 'caf\xe9'\n"
            b"run_campaign(authorization_contract=object())\n"
        )
        resolved, unresolved, out_of_scope, source_error = _certified_writer_resolve_path(
            encoded_path, "pep263.py",
        )
        assert len(resolved) == 1
        assert resolved[0][4] == "campaign.loop.run_campaign"
        assert not unresolved
        assert not out_of_scope
        assert source_error is None

        malformed_path = Path(tmpdir) / "malformed.py"
        malformed_path.write_text("def broken(:\n", encoding="utf-8")
        resolved, unresolved, out_of_scope, source_error = _certified_writer_resolve_path(
            malformed_path, "malformed.py",
        )
        assert not resolved and not unresolved and not out_of_scope
        assert source_error is not None
        assert source_error["path"] == "malformed.py"
        assert source_error["phase"] == "parse"
        assert source_error["error"] == "SyntaxError"
        assert isinstance(source_error["line"], int)
        assert isinstance(source_error["column"], int)

    repo_root = Path(_ORCH).parent
    source_paths = []
    candidates = []
    # Prune transient workspace roots before descent; os.walk skips each
    # directory whose scandir raises OSError (including concurrent removal).
    for directory, dirnames, filenames in os.walk(repo_root):
        if Path(directory) == repo_root:
            dirnames[:] = [name for name in dirnames if not name.startswith(".")]
        for filename in filenames:
            if not filename.endswith(".py"):
                continue
            path = Path(directory) / filename
            try:
                path.stat()
            except OSError:
                continue
            candidates.append(path)
    for path in sorted(candidates):
        rel_path = path.relative_to(repo_root)
        parts = rel_path.parts
        # Tests contain authority-omission negative controls and same-name mocks.
        if parts[:2] == ("orchestrator", "tests"):
            continue
        # .git is version-control metadata, not repository-owned source.
        if ".git" in parts:
            continue
        # .claude contains nested worktrees whose callers belong to other trees.
        if ".claude" in parts:
            continue
        # .codex contains nested worktrees whose callers belong to other trees.
        if ".codex" in parts:
            continue
        # external is vendored/submodule code outside this repository's authority.
        if parts and parts[0] == "external":
            continue
        # __pycache__ is generated interpreter cache content.
        if "__pycache__" in parts:
            continue
        # output is generated campaign/dispatch output, not an import source root.
        if parts and parts[0] == "output":
            continue
        # Virtual environments and build trees are generated dependency/artifact roots.
        if parts and parts[0] in {".venv", "venv", "build"}:
            continue
        source_paths.append(path)
    assert source_paths, "repo-wide certified-writer scan found no Python files"

    resolved_calls = []
    unresolved_calls = []
    out_of_scope_calls = []
    source_errors = []
    for path in source_paths:
        rel_path = path.relative_to(repo_root).as_posix()
        resolved, unresolved, out_of_scope, source_error = _certified_writer_resolve_path(
            path, rel_path,
        )
        if source_error is not None:
            source_errors.append(source_error)
            continue
        resolved_calls.extend(resolved)
        unresolved_calls.extend(unresolved)
        out_of_scope_calls.extend(out_of_scope)

    assert not source_errors, (
        "certified-writer source scan failures:\n"
        + json.dumps(source_errors, ensure_ascii=False, sort_keys=True, indent=2)
    )

    assert all(
        isinstance(record[6], _CertifiedWriterOutOfScopeReason)
        for record in out_of_scope_calls
    ), "OUT_OF_SCOPE certified-writer record missing a closed reason"
    observed_out_of_scope_reasons = {
        record[6] for record in out_of_scope_calls
    }
    unsafe_out_of_scope_reasons = (
        observed_out_of_scope_reasons
        - _CERTIFIED_WRITER_SAFE_OUT_OF_SCOPE_REASONS
    )
    assert not unsafe_out_of_scope_reasons, (
        "unsafe OUT_OF_SCOPE certified-writer reasons: "
        + ", ".join(sorted(reason.value
                           for reason in unsafe_out_of_scope_reasons))
    )

    expected_inventory = collections.Counter({
        ("orchestrator/campaign/b10_backoff_static_tail_formal.py", "campaign.loop.run_campaign"): 1,
        ("orchestrator/campaign/b10_backoff_shape_sweep.py", "campaign.loop.run_campaign"): 1,
        ("orchestrator/campaign/backoff_extended_sweep.py", "campaign.loop.run_campaign"): 1,
        ("orchestrator/campaign/backoff_repro.py", "campaign.loop.run_campaign"): 1,
        ("orchestrator/campaign/backoff_sweep.py", "campaign.loop.run_campaign"): 1,
        ("orchestrator/campaign/demo.py", "campaign.loop.run_campaign"): 2,
        ("orchestrator/campaign/p2_2.py", "campaign.loop.run_campaign"): 1,
        ("orchestrator/campaign/p3_kickoff.py", "campaign.loop.run_campaign"): 2,
        ("orchestrator/campaign/p3_s4_loop.py", "campaign.loop.run_campaign"): 1,
        ("orchestrator/campaign/p3_s4_loop_sort.py", "campaign.loop.run_campaign"): 1,
        ("orchestrator/campaign/p3_s4_loop_trigger_gating.py", "campaign.loop.run_campaign"): 1,
        ("orchestrator/campaign/p3_s4_red.py", "campaign.loop.run_campaign"): 2,
        ("orchestrator/campaign/paper_story_a1_paired.py", "campaign.loop.run_campaign"): 2,
        ("orchestrator/campaign/paper_story_a2_certification.py", "campaign.loop.run_campaign"): 1,
        ("orchestrator/campaign/s6_sort_sweep.py", "campaign.loop.run_campaign"): 1,
        ("orchestrator/campaign/s8a_trigger_sweep.py", "campaign.loop.run_campaign"): 1,
        ("orchestrator/campaign/sanity_silo.py", "campaign.loop.run_campaign"): 1,
        ("orchestrator/campaign/loop.py", "campaign.pipeline.evaluate"): 1,
        ("orchestrator/campaign/screening_driver.py", "campaign.pipeline.evaluate"): 1,
        ("orchestrator/campaign/s1_direct_comparison.py", "campaign.pipeline.evaluate"): 1,
        ("orchestrator/campaign/s8b_oracle_driver.py", "campaign.pipeline.evaluate"): 1,
        ("orchestrator/qualification/t126_driver.py", "campaign.pipeline.evaluate"): 1,
    })
    assert sum(count for (path, target), count in expected_inventory.items()
               if target == "campaign.loop.run_campaign") == 21
    assert sum(count for (path, target), count in expected_inventory.items()
               if target == "campaign.pipeline.evaluate") == 5

    unresolved_diagnostics = "\n".join(
        _certified_writer_diagnostic(record)
        for record in sorted(unresolved_calls, key=lambda record: record[:5])
    )
    # Ordered contract: UNRESOLVED, missing authority, then inventory drift.
    assert not unresolved_calls, (
        "UNRESOLVED certified-writer references:\n" + unresolved_diagnostics
    )

    missing_authorization = [
        record for record in resolved_calls
        if not any(keyword.arg == "authorization_contract"
                   for keyword in record[5].keywords)
    ]
    missing_diagnostics = "\n".join(
        _certified_writer_diagnostic(record)
        for record in sorted(missing_authorization, key=lambda record: record[:5])
    )
    assert not missing_authorization, (
        "authorization_contract missing:\n" + missing_diagnostics
    )

    actual_inventory = collections.Counter(
        (record[0], record[4]) for record in resolved_calls
    )
    new_callers = actual_inventory - expected_inventory
    stale_inventory = expected_inventory - actual_inventory

    def inventory_diagnostics(difference, *, expected_first):
        lines = []
        for (rel_path, target), count in sorted(difference.items()):
            actual_count = actual_inventory[(rel_path, target)]
            expected_count = expected_inventory[(rel_path, target)]
            records = [
                record for record in resolved_calls
                if (record[0], record[4]) == (rel_path, target)
            ]
            callsites = ", ".join(
                _certified_writer_diagnostic(record) for record in records
            )
            prefix = "stale fixed inventory" if expected_first else "new/unregistered caller"
            lines.append(
                f"{prefix}: {rel_path} target={target} "
                f"expected={expected_count} actual={actual_count} delta={count} "
                f"callsites=[{callsites}]"
            )
        return "\n".join(lines)

    inventory_message = "\n".join(filter(None, [
        inventory_diagnostics(new_callers, expected_first=False),
        inventory_diagnostics(stale_inventory, expected_first=True),
    ]))
    assert not new_callers and not stale_inventory, inventory_message

    # Legacy raw-AST guards remain intact so every formerly rejected input is
    # still rejected even when semantic provenance classifies a same-name call
    # as unrelated.
    campaign_dir = Path(_ORCH) / "campaign"
    expected_run_calls = {
        "b10_backoff_static_tail_formal.py": 1,
        "backoff_extended_sweep.py": 1,
        "backoff_repro.py": 1, "backoff_sweep.py": 1, "demo.py": 2,
        "p2_2.py": 1, "p3_kickoff.py": 2, "p3_s4_loop.py": 1,
        "p3_s4_loop_sort.py": 1, "p3_s4_loop_trigger_gating.py": 1,
        "p3_s4_red.py": 2, "s6_sort_sweep.py": 1,
        "s8a_trigger_sweep.py": 1, "sanity_silo.py": 1,
    }
    for name, expected_count in expected_run_calls.items():
        tree = ast.parse((campaign_dir / name).read_text(encoding="utf-8"))
        calls = [
            node for node in ast.walk(tree)
            if isinstance(node, ast.Call)
            and isinstance(node.func, ast.Name)
            and node.func.id == "run_campaign"
        ]
        assert len(calls) == expected_count, name
        assert all(
            any(keyword.arg == "authorization_contract"
                for keyword in call.keywords)
            for call in calls
        ), name
        assert all(
            any(keyword.arg == "declared_use_class"
                for keyword in call.keywords)
            for call in calls
        ), name
    assert sum(expected_run_calls.values()) == 17

    direct_sinks = {
        "loop.py": ("evaluate",),
        "screening_driver.py": ("evaluate",),
        "s1_direct_comparison.py": ("evaluate_fn",),
        "s8b_oracle_driver.py": ("evaluate_fn",),
    }
    for name, callable_names in direct_sinks.items():
        tree = ast.parse((campaign_dir / name).read_text(encoding="utf-8"))
        calls = [
            node for node in ast.walk(tree)
            if isinstance(node, ast.Call)
            and isinstance(node.func, ast.Name)
            and node.func.id in callable_names
        ]
        assert calls, name
        assert any(
            any(keyword.arg == "authorization_contract"
                for keyword in call.keywords)
            for call in calls
        ), name
    qualification_tree = ast.parse(
        (Path(_ORCH) / "qualification/t126_driver.py").read_text(encoding="utf-8")
    )
    t126_calls = [
        node for node in ast.walk(qualification_tree)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and node.func.attr == "evaluate"
    ]
    assert len(t126_calls) == 1
    assert any(
        keyword.arg == "authorization_contract"
        for keyword in t126_calls[0].keywords
    )


def test_certified_writer_preflight_stdin_cli_rejects_with_json_only():
    helper = Path(_ORCH) / "campaign/certified_writer_preflight.py"
    scratch = Path(_tmpdir("izanagi_preflight_cli_"))
    receipt = scratch / "receipt.json"
    receipt.write_bytes(b"{}\n")
    before = {path.relative_to(scratch): path.read_bytes()
              for path in scratch.rglob("*") if path.is_file()}
    completed = subprocess.run(
        [sys.executable, "-I", "-B", "-", "floor", "--repo-root",
         str(Path(_ORCH).parent), "--receipt", str(receipt)],
        input=helper.read_text(encoding="utf-8"), text=True,
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False,
    )
    after = {path.relative_to(scratch): path.read_bytes()
             for path in scratch.rglob("*") if path.is_file()}
    assert completed.returncode == 3
    assert completed.stdout == ""
    assert completed.stderr.count("\n") == 1
    diagnostic = json.loads(completed.stderr)
    assert set(diagnostic) == {"gate", "reason"}
    assert diagnostic["gate"] == "admission"
    assert type(diagnostic["reason"]) is str and diagnostic["reason"]
    assert after == before


def test_certified_writer_preflight_cli_input_error_is_exit_four():
    helper = Path(_ORCH) / "campaign/certified_writer_preflight.py"
    completed = subprocess.run(
        [sys.executable, "-I", "-B", "-", "floor"],
        input=helper.read_text(encoding="utf-8"), text=True,
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False,
    )
    assert completed.returncode == 4 and completed.stdout == ""
    lines = completed.stderr.splitlines()
    assert len(lines) == 1
    assert set(json.loads(lines[0])) == {"gate", "reason"}


def test_certified_writer_preflight_cli_acceptance_is_silent_and_read_only():
    from orchestrator.campaign import certified_writer_admission as admission
    from orchestrator.campaign import certified_writer_preflight as helper

    scratch = Path(_tmpdir("izanagi_preflight_accept_"))
    repo = scratch / "repo"
    repo.mkdir()
    subprocess.run(
        ["git", "-c", "core.hooksPath=", "init", "-q", str(repo)],
        check=True,
    )
    (repo / "fixture.txt").write_text("fixture\n", encoding="utf-8")
    subprocess.run(
        ["git", "-c", "core.hooksPath=", "-C", str(repo),
         "-c", "user.email=fixture@example.invalid",
         "-c", "user.name=Fixture", "add", "."],
        check=True,
    )
    subprocess.run(
        ["git", "-c", "core.hooksPath=", "-C", str(repo),
         "-c", "user.email=fixture@example.invalid",
         "-c", "user.name=Fixture", "commit", "-qm", "fixture"],
        check=True,
    )
    source_commit = subprocess.check_output(
        ["git", "-C", str(repo), "rev-parse", "HEAD"], text=True,
    ).strip()
    receipt = scratch / "receipt.json"
    receipt.write_text(
        json.dumps({"source_commit": source_commit}) + "\n", encoding="utf-8"
    )
    before = receipt.read_bytes()
    stdout, stderr = io.StringIO(), io.StringIO()
    with unittest_mock.patch.object(admission, "admit") as admit, \
            contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
        rc = helper.main([
            "floor", "--repo-root", str(repo),
            "--receipt", str(receipt),
        ])
    assert rc == 0 and stdout.getvalue() == "" and stderr.getvalue() == ""
    assert receipt.read_bytes() == before
    admit.assert_called_once()


def test_p2_actual_floor_and_t126_admission_accept_valid_evidence(tmp_path=None):
    from orchestrator.campaign import certified_writer_admission as admission
    from orchestrator.campaign import certified_writer_preflight as helper

    root = Path(tmp_path) if tmp_path is not None else Path(
        _tmpdir("izanagi_actual_admission_")
    )
    fixture = build_admission_fixture(root)
    assert fixture.shared_floor_walltime_s != fixture.t126_walltime_s

    saved_site = admission.site_policy.current_site
    saved_calibration = admission.env_attestation.load_verified_calibration
    admission.site_policy.current_site = lambda: site_policy.PEGASUS_COMPUTE
    admission.env_attestation.load_verified_calibration = lambda *_args: object()
    try:
        for mode in ("floor", "t126"):
            receipt = fixture.receipts[mode]
            before = receipt.read_bytes()
            admission.admit(
                mode,
                repo_root=fixture.repo_root,
                receipt_path=receipt,
                environ=fixture.environments[mode],
            )
            stdout, stderr = io.StringIO(), io.StringIO()
            with unittest_mock.patch.dict(
                    os.environ, fixture.environments[mode], clear=False), \
                    contextlib.redirect_stdout(stdout), \
                    contextlib.redirect_stderr(stderr):
                rc = helper.main([
                    mode, "--repo-root", str(fixture.repo_root),
                    "--receipt", str(receipt),
                ])
            assert rc == 0 and stdout.getvalue() == "" and stderr.getvalue() == ""
            assert receipt.read_bytes() == before
    finally:
        admission.site_policy.current_site = saved_site
        admission.env_attestation.load_verified_calibration = saved_calibration


def test_floor_admission_uses_authority_resolver_not_legacy_literal(tmp_path=None):
    from orchestrator.campaign import certified_writer_admission as admission
    from orchestrator.campaign import s8b_floor_campaign as floor_campaign

    root = Path(tmp_path) if tmp_path is not None else Path(
        _tmpdir("izanagi_floor_resolver_admission_")
    )
    fixture = build_admission_fixture(root)
    legacy = fixture.repo_root / floor_campaign._FLOOR_PROTOCOL_REL
    protocol_bytes = legacy.read_bytes()
    selected_rel = "output/authority-selected/floor_protocol.json"
    selected = fixture.repo_root / selected_rel
    selected.parent.mkdir(parents=True)
    selected.write_bytes(protocol_bytes)
    record = floor_campaign.IndexedFloorProtocol(
        path=selected_rel,
        document=floor_campaign._strict_parse_protocol_bytes(
            protocol_bytes, source=selected_rel,
        ),
        raw_bytes=protocol_bytes,
        sha256=hashlib.sha256(protocol_bytes).hexdigest(),
    )
    legacy.write_bytes(b"legacy literal must not be read\n")

    with unittest_mock.patch.object(
            admission.s8b_floor_campaign, "resolve_current_floor_protocol",
            return_value=record,
    ) as resolver, unittest_mock.patch.object(
            admission.site_policy, "current_site",
            return_value=site_policy.PEGASUS_COMPUTE,
    ), unittest_mock.patch.object(
            admission.env_attestation, "load_verified_calibration",
            return_value=object(),
    ):
        admission.admit(
            "floor",
            repo_root=fixture.repo_root,
            receipt_path=fixture.receipts["floor"],
            environ=fixture.environments["floor"],
        )
    resolver.assert_called_once_with(root=fixture.repo_root)


def test_floor_admission_rejects_disk_bytes_different_from_index_record(tmp_path=None):
    from orchestrator.campaign import certified_writer_admission as admission
    from orchestrator.campaign import s8b_floor_campaign as floor_campaign

    root = Path(tmp_path) if tmp_path is not None else Path(
        _tmpdir("izanagi_floor_index_bytes_mismatch_")
    )
    fixture = build_admission_fixture(root)
    original_resolver = floor_campaign.resolve_current_floor_protocol

    def resolve_then_replace(*, root):
        record = original_resolver(root=root)
        (root / record.path).write_bytes(record.raw_bytes + b"\n")
        return record

    with unittest_mock.patch.object(
            admission.s8b_floor_campaign, "resolve_current_floor_protocol",
            side_effect=resolve_then_replace,
    ), unittest_mock.patch.object(
            admission.site_policy, "current_site",
            return_value=site_policy.PEGASUS_COMPUTE,
    ), unittest_mock.patch.object(
            admission.env_attestation, "load_verified_calibration",
            return_value=object(),
    ):
        try:
            admission.admit(
                "floor",
                repo_root=fixture.repo_root,
                receipt_path=fixture.receipts["floor"],
                environ=fixture.environments["floor"],
            )
        except admission.AdmissionRejected as exc:
            assert str(exc) == "floor protocol bytes differ from indexed authority"
        else:
            raise AssertionError("indexed SHA と異なる disk bytes を受理した")


def test_certified_writer_environment_accepts_recorded_pegasus_identity():
    from orchestrator.campaign import certified_writer_admission as admission

    # job-staging/0:867876.nqsv/reservation.json の identity を literal 固定する。
    environ = {
        "IZANAGI_SUBMISSION_NONCE": "751223708553eba8b7c942d845fbb266",
        "PBS_JOBID": "0:867876.nqsv",
    }
    assert admission._required_environment(environ) == (
        "751223708553eba8b7c942d845fbb266",
        "0:867876.nqsv",
    )


def test_m8_preflight_rejects_fail_open_domain_module_drift(tmp_path=None):
    root = Path(tmp_path) if tmp_path is not None else Path(
        _tmpdir("izanagi_source_drift_")
    )
    repo, receipt, helper_source = build_source_drift_fixture(root)
    completed = subprocess.run(
        [sys.executable, "-I", "-B", "-", "floor", "--repo-root",
         str(repo), "--receipt", str(receipt)],
        input=helper_source, text=True,
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False,
    )
    assert completed.returncode == 3
    assert completed.stdout == ""
    assert completed.stderr.count("\n") == 1
    diagnostic = json.loads(completed.stderr)
    assert diagnostic["gate"] == "admission"
    assert (
        "imported module differs from source commit: "
        "orchestrator/campaign/certified_writer_admission.py"
        in diagnostic["reason"]
    )


def _green_vr():
    """実 VerifyResult (緑): certified=True になる最小の health。"""
    return VerifyResult(trace_dir="/tmp/ev", serializable=True, anomalies=[],
                        integrity=Integrity(proof_surfaces=ProofSurfaceAssessment(
                            protocol="silo",
                            lock_coverage="evidence-present",
                            permutation="evidence-present",
                            write_intent="evidence-absent",
                        )), n_txns=100, n_reads=300,
                        n_writes=100, n_keys=50, n_edges=120)


def _red_vr():
    """実 VerifyResult (赤): rw を含む 2-cycle (G2) anomaly を持つ non-serializable。"""
    edges = [CycleEdge(src=1, dst=2,
                       reasons=[EdgeReason(etype=RW, key="aa", u_ver=(1, 1), v_ver=(1, 2))]),
             CycleEdge(src=2, dst=1,
                       reasons=[EdgeReason(etype=RW, key="bb", u_ver=(1, 1), v_ver=(1, 2))])]
    a = Anomaly(cycle=[1, 2], phenomenon="G2", edges=edges)
    return VerifyResult(trace_dir="/tmp/ev", serializable=False, anomalies=[a],
                        integrity=Integrity(proof_surfaces=ProofSurfaceAssessment(
                            protocol="silo",
                            lock_coverage="evidence-present",
                            permutation="evidence-present",
                            write_intent="evidence-absent",
                        )), n_txns=2, n_reads=2,
                        n_writes=2, n_keys=2, n_edges=2)


_MATCH_TRACE_WITNESS = object()


@contextlib.contextmanager
def _mock_pipeline(certified=True, median=12345.0, cv=0.01, rc=0, ncommit=100,
                   aborts=7, abort_rate=0.03, build_raises=False,
                   high_variance=False, unstable=False, competing=None,
                   trace_timeout=False, probe_raises=None,
                   bench_rounds=None, round_binding="unique",
                   trace_content=None, site_compilers=None, source_raises=False,
                   build_cached=False,
                   commit_witness=_MATCH_TRACE_WITNESS, batch_witness=0,
                   unsupported_workload=False, preexisting_trace=False,
                   unavailable_trace_dir=False,
                   measurement_site=site_policy.PEGASUS_COMPUTE):
    """pipeline の外部依存をダミー化。trace の rc/commit 数・bench の throughput・
    build 失敗を引数で操作し、evaluate の分岐 (特に規律2 の abort) を検査する。
    yield する list = measure_point (実 bench) が呼ばれた回数の証跡。
    `probe_raises` に例外を渡すと competing_bench_pids がそれを送出する (probe 故障注入)。"""
    class CallEvidence(list):
        def __init__(self):
            super().__init__()
            self.trace = []
            self.events = []
            self.builds = []
            self.cache_hits = []
            self.build_roots = []
            self.build_options = []
            self.source_resolve_calls = []
            self.measure_kwargs = []
            self.lock_enters = 0
            self.competition_probes = 0
            self.verify_witnesses = []

    class ScriptedPoint:
        """ScalePoint 同様、値等価だが identity は別にできる round fixture。"""
        def __init__(self, round_median, reps=2, use_perf=True):
            self.throughputs = ([] if round_median is None else
                                [round_median] * reps)
            self.run_cmd = "<run>"
            self._median = round_median
            self._use_perf = use_perf

        def leading_indicators(self):
            return {"throughput_tps": self._median,
                    "abort_rate": abort_rate, "latency_ns": 1000.0,
                    "llc_miss_rate": 0.2 if self._use_perf else None,
                    "ipc": 1.5 if self._use_perf else None}

        def __eq__(self, other):
            return (isinstance(other, ScriptedPoint)
                    and self.throughputs == other.throughputs
                    and self.run_cmd == other.run_cmd)

    bench_calls = CallEvidence()
    real_verify_trace_dir_with_capability = (
        pipeline.verify_trace_dir_with_capability
    )
    round_specs = list(bench_rounds or [{
        "median": median, "cv": cv, "rep_returncodes": [0, 0, 0, 0, 0],
    }])
    shared_point = {"value": None}
    saved = {}

    def patch(name, val):
        saved[name] = getattr(pipeline, name)
        setattr(pipeline, name, val)

    @contextlib.contextmanager
    def fake_lock(*a, **k):
        bench_calls.lock_enters += 1
        yield

    def fake_measure(*a, **k):
        index = len(bench_calls)
        spec = round_specs[index]
        bench_calls.append(1)                            # 実 bench が走った証跡
        bench_calls.events.append("bench")
        bench_calls.measure_kwargs.append(dict(k))
        if "rep_returncodes" in k:
            k["rep_returncodes"].extend(spec["rep_returncodes"])
        point = ScriptedPoint(
            spec["median"], reps=k.get("reps", 2),
            use_perf=k.get("use_perf", True),
        )
        if round_binding == "duplicate":
            if shared_point["value"] is None:
                shared_point["value"] = point
            return shared_point["value"]
        return point

    def fake_build(genome, commit, trace, src_token=None, ccbench_dir="", cache_root="",
                   *, admission, build_context, source_evidence):
        assert build_context is _BUILD_CONTEXT
        assert admission.as_wal_receipt()["source"] == source_evidence.as_receipt()
        bench_calls.builds.append(("legacy", trace, None))
        bench_calls.cache_hits.append(build_cached)
        if build_raises:
            raise RuntimeError("build boom")
        bin_sha256 = ("da" if trace else "db") * 32  # 64 hex (WAL 新キー用)
        return types.SimpleNamespace(bin_hash=bin_sha256[:16], bin_sha256=bin_sha256,
                                     binary="/nonexistent/ycsb.exe", cached=build_cached,
                                     configure_cmd="<cfg>", build_cmd="<build>")

    def fake_build_v2(genome, *, admission, build_context, source_evidence,
                      contract, ccbench_commit, trace, src_token,
                      cc, cxx, cache_root, ccbench_dir="", timeout_s=None,
                      dependency_prefix="", expected_toolchain_manifest=None,
                      declared_use_class=None):
        assert build_context is _BUILD_CONTEXT
        assert admission.as_wal_receipt()["source"] == source_evidence.as_receipt()
        bench_calls.builds.append(("v2", trace, contract.contract_sha256))
        bench_calls.cache_hits.append(build_cached)
        bench_calls.build_roots.append(ccbench_dir)
        bench_calls.build_options.append({
            "cc": cc, "cxx": cxx, "dependency_prefix": dependency_prefix,
        })
        if build_raises:
            raise RuntimeError("build boom")
        bin_sha256 = ("da" if trace else "db") * 32
        toolchain = {
            "cc": {"requested": cc, "realpath": f"/fixture/{cc}",
                   "version_first_line": "cc fixture"},
            "cxx": {"requested": cxx, "realpath": f"/fixture/{cxx}",
                    "version_first_line": "cxx fixture"},
            "cmake": {"requested": "cmake", "realpath": "/fixture/cmake",
                      "version_first_line": "cmake fixture"},
        }
        manifest_sha256 = None
        if expected_toolchain_manifest is not None:
            manifest_sha256 = hashlib.sha256(
                json.dumps(
                    expected_toolchain_manifest, sort_keys=True,
                    separators=(",", ":"),
                ).encode("utf-8")
            ).hexdigest()
        return types.SimpleNamespace(
            bin_hash=bin_sha256[:16], bin_sha256=bin_sha256,
            binary="/nonexistent/ycsb.exe", cached=build_cached,
            configure_cmd="<cfg-v2>", build_cmd="<build-v2>",
            contract_sha256=contract.contract_sha256,
            toolchain=toolchain,
            toolchain_manifest_sha256=manifest_sha256,
        )

    patch("buildcache", types.SimpleNamespace(
        build=fake_build, build_v2=fake_build_v2,
        is_full_sha256=buildcache.is_full_sha256,
        _ccbench_dir=buildcache._ccbench_dir,
        DEFAULT_CC=buildcache.DEFAULT_CC, DEFAULT_CXX=buildcache.DEFAULT_CXX,
        toolchain_compilers_from_manifest=buildcache.toolchain_compilers_from_manifest,
        compilers_for_current_site=lambda: (
            site_compilers
            or (buildcache.DEFAULT_CC, buildcache.DEFAULT_CXX)
        )))
    patch(
        "_compilers_for_current_site",
        lambda: site_compilers or (buildcache.DEFAULT_CC, buildcache.DEFAULT_CXX),
    )
    patch("_resolve_site", lambda _site=None: measurement_site)
    # source_digest は identity 核 (実 git/g++ 依存)。pipeline の段階遷移テストでは
    # mock し stock 固定 (source_digest 自体は専用テストで実機検証する)。
    def fake_source_resolve(genome_value, commit, *, ccbench_dir="", cxx="g++-13"):
        bench_calls.source_resolve_calls.append((
            (genome_value, commit, ccbench_dir, cxx), {},
        ))
        if source_raises:
            raise RuntimeError("source evidence unavailable")
        return _source_evidence(
            genome_value,
            commit,
            source_root=ccbench_dir or str(commit_receipts.proof_source_root()),
        )

    patch("source_digest", types.SimpleNamespace(
        STOCK="stock",
        assert_worktree_within_allowlist=lambda *a, **k: None,
        resolve_evidence=fake_source_resolve))
    if trace_timeout:
        def _raise_timeout(*a, **k):
            bench_calls.trace.append(1)
            raise subprocess.TimeoutExpired(cmd="trace",
                                            timeout=pipeline.TRACE_TIMEOUT_S)
        patch("_run_trace", _raise_timeout)
    else:
        def fake_trace(_binary, trace_dir, *_args, **_kwargs):
            bench_calls.trace.append(1)
            bench_calls.events.append("verify")
            if unsupported_workload:
                raise pipeline._TraceWitnessUnsupportedWorkload(
                    "/fixture/tpcc_silo.exe"
                )
            if preexisting_trace:
                raise pipeline._TraceDirNotEmpty(["trace_0.log"])
            if unavailable_trace_dir:
                raise pipeline._TraceDirUnavailable(
                    "/fixture/missing-traces", "missing"
                )
            if trace_content is not None:
                with open(os.path.join(trace_dir, "trace_0.log"),
                          "w", encoding="ascii") as stream:
                    stream.write(trace_content)
            witness = (
                ncommit if commit_witness is _MATCH_TRACE_WITNESS
                else commit_witness
            )
            return pipeline._TraceRunResult(
                trace_c_lines=ncommit,
                returncode=rc,
                abort_counts=aborts,
                commit_count_witness=witness,
                batch_commit_count_witness=batch_witness,
            )
        patch("_run_trace", fake_trace)
    # 実 VerifyResult を返す (result_to_dict が S4 で abort payload を作るので duck-type 不可)。
    if trace_content is None:
        def fake_verify(tdir, *, expected_commits=None, **receipt_binding):
            bench_calls.verify_witnesses.append(expected_commits)
            fixture = "g1_serial" if certified else "r1_write_skew"
            result, capability = real_verify_trace_dir_with_capability(
                os.path.join(_HERE, "fixtures", fixture),
                **receipt_binding,
            )
            # The pre-receipt pipeline fixture intentionally exposes txn 1→2
            # and keys aa/bb in its structured red payload.  A red capability
            # is never eligible for receipt issuance, so preserve that exact
            # diagnostic while still returning a verifier-issued opaque value.
            if not certified:
                result = _red_vr()
            return result, capability
        patch("verify_trace_dir_with_capability", fake_verify)
    else:
        def wrapped_real_verify(
                tdir, *, expected_commits=None, **receipt_binding,
        ):
            bench_calls.verify_witnesses.append(expected_commits)
            return real_verify_trace_dir_with_capability(
                tdir, expected_commits=expected_commits,
                **receipt_binding,
            )
        patch("verify_trace_dir_with_capability", wrapped_real_verify)
    def fake_remeasure(measure_fn, settle_fn=None, **k):
        # scripted round を全て通し、実装と同じく CV が厳密に低い最初の点を採る。
        points = [measure_fn() for _ in round_specs]
        best_index = 0
        for index in range(1, len(round_specs)):
            new_cv = round_specs[index]["cv"]
            best_cv = round_specs[best_index]["cv"]
            if new_cv is not None and (best_cv is None or new_cv < best_cv):
                best_index = index
        selected = round_specs[best_index]
        pt = points[best_index]
        if round_binding == "unmatched":
            pt = ScriptedPoint(selected["median"])
        nf = types.SimpleNamespace(
            median=(selected["median"] if pt.throughputs else None),
            cv=selected["cv"],
            high_variance=high_variance)
        return types.SimpleNamespace(point=pt, nf=nf, rounds=len(points),
                                     stable=not unstable, unstable=unstable,
                                     cv_history=[spec["cv"] for spec in round_specs])

    patch("bench_lock", fake_lock)
    patch("settle", lambda *a, **k: {"settled": True})

    def fake_competing():
        bench_calls.competition_probes += 1
        if probe_raises is not None:
            raise probe_raises
        return list(competing or [])
    patch("competing_bench_pids", fake_competing)  # 既定: 単一テナント
    patch("measure_point", fake_measure)
    patch("remeasure_until_stable", fake_remeasure)
    try:
        yield bench_calls
    finally:
        for k, v in saved.items():
            setattr(pipeline, k, v)


def _eval(lay, do_bench=True, screening=None, expected_perf_sha256=None,
          record_rep_returncodes=False, protocol="silo", **mock_kw):
    """1 genome を mock 下で評価し (EvalResult, bench 呼び出し回数 list) を返す。"""
    if wal.read_lock(lay) is None:
        cfg = _cfg()
        if screening is not None:
            cfg = _cfg(search_config={
                **cfg.search_config,
                **ident.screening_search_config(screening),
            })
        _write_certified_lock(lay, _bound(cfg))
    with _mock_pipeline(**mock_kw) as calls:
        r = pipeline.evaluate(
            Genome(protocol, {"BACK_OFF": 1}), lay, _AUTH_CONTRACT.env_tag, "deadbeef",
            PerfConfig(records=1000, threads=2), clocks_per_us=1800,
            numactl=_AUTH_CONTRACT.numactl,
            do_bench=do_bench, screening=screening,
            expected_perf_sha256=expected_perf_sha256,
            record_rep_returncodes=record_rep_returncodes,
            authorization_contract=_AUTHORIZATION,
            log=lambda *a: None, build_context=_BUILD_CONTEXT)
    return r, calls


def test_pipeline_no_bench_wal_commit_binds_authorized_contract():
    lay = _tmp_layout()
    result, _calls = _eval(lay, do_bench=False)
    records = wal.read_records(lay)
    commits = [record for record in records if record.stage == STAGE_COMMIT]
    assert result.certified and len(commits) == 1
    assert commits[0].payload[COMMIT_CONTRACT_SHA256_KEY] == \
        _AUTH_CONTRACT.contract_sha256
    assert all(
        COMMIT_CONTRACT_SHA256_KEY not in record.payload
        for record in records if record.stage != STAGE_COMMIT
    )


def test_pipeline_bench_wal_commit_binds_authorized_contract():
    lay = _tmp_layout()
    result, _calls = _eval(lay, do_bench=True)
    records = wal.read_records(lay)
    commits = [record for record in records if record.stage == STAGE_COMMIT]
    assert result.certified and len(commits) == 1
    assert commits[0].payload[COMMIT_CONTRACT_SHA256_KEY] == \
        _AUTH_CONTRACT.contract_sha256
    assert all(
        COMMIT_CONTRACT_SHA256_KEY not in record.payload
        for record in records if record.stage != STAGE_COMMIT
    )


# ===== T-316: build provenance admission ======================================

def test_build_admission_coder_default_rejects_before_pipeline_build_spy():
    lay = _tmp_layout()
    with _mock_pipeline(certified=True) as calls:
        try:
            pipeline.evaluate(
                Genome("silo", {"BACK_OFF": 1}), lay, _AUTH_CONTRACT.env_tag, "deadbeef",
                PerfConfig(records=1000, threads=2), clocks_per_us=1800,
                numactl=_AUTH_CONTRACT.numactl,
                authorization_contract=_AUTHORIZATION,
                do_bench=False, build_context=object(),
                log=lambda *_args: None,
            )
            assert False, "forged build context を拒否すべき"
        except TypeError as exc:
            assert "build_context" in str(exc)
    assert calls.builds == [], "opt-in 無し CODER_DERIVED が build spy に到達した"


def test_m3_evaluate_admission_is_a_required_keyword_only_parameter():
    """Current API requires the run context, not a caller-declared admission."""
    parameters = inspect.signature(pipeline.evaluate).parameters
    assert "admission" not in parameters
    parameter = parameters["build_context"]
    assert parameter.kind is inspect.Parameter.KEYWORD_ONLY
    assert parameter.default is inspect.Parameter.empty


def test_build_admission_explicit_coder_opt_in_reaches_build_and_records_receipt():
    lay = _tmp_layout()
    with _mock_pipeline(certified=True) as calls:
        result = pipeline.evaluate(
            Genome("silo", {"BACK_OFF": 1}), lay, _AUTH_CONTRACT.env_tag, "deadbeef",
            PerfConfig(records=1000, threads=2), clocks_per_us=1800,
            numactl=_AUTH_CONTRACT.numactl,
            authorization_contract=_AUTHORIZATION,
            do_bench=False, build_context=_BUILD_CONTEXT, log=lambda *_args: None,
        )
    assert result.certified and len(calls.builds) == 2
    start = next(r for r in wal.read_records(lay) if r.stage == STAGE_BUILD_START)
    receipt = start.payload["build_admission"]
    assert receipt["class"] == "coder-authored"
    assert receipt["authority_kind"] == "cli-opt-in"
    assert start.payload["build_admission_receipt_sha256"] == receipt["receipt_sha256"]
    for record in wal.read_records(lay):
        if record.stage in {STAGE_BUILD_DONE, STAGE_COMMIT}:
            assert record.payload["build_attempt_id"] == start.payload["build_attempt_id"]
            assert record.payload["build_admission_receipt_sha256"] == receipt["receipt_sha256"]


def _write_materialized_trigger_source(
        source_path: str,
        predicate: str,
        *,
        hole_line: str | None = None,
        line_ending: bytes = b"\n",
) -> str:
    from orchestrator.campaign import axis_trigger_gating, p3_s4_loop
    from orchestrator.campaign.diff_quarantine import parse_template_file

    base_text = (
        axis_trigger_gating.FROZEN_TEMPLATE_BLOCK_BYTES
        + axis_trigger_gating.FROZEN_TEMPLATE_EPILOGUE_BYTES
    ).decode("utf-8")
    with open(source_path, "w", encoding="utf-8") as stream:
        stream.write(base_text)

    marker = parse_template_file(source_path, axis_trigger_gating.MARKER_ID)
    assert marker is not None
    materialized = p3_s4_loop.render_hole(base_text, marker, predicate)
    lines = materialized.split("\n")
    if hole_line is not None:
        lines[marker.hole_first - 1] = hole_line
    with open(source_path, "wb") as stream:
        stream.write(line_ending.join(line.encode("utf-8") for line in lines))
    return lines[marker.hole_first - 1]


def _assert_materialized_trigger_predicate_rejected(
        source_root: str, mask: int = 20,
) -> None:
    binding = trigger_gate_binding.TriggerGateBinding(
        mask=mask,
        predicate_sha256=trigger_gate_binding.expected_predicate_sha256(mask),
        nonce="f" * 64,
        source=None,
    )
    evidence = _source_evidence(
        Genome("silo", {"BACK_OFF": 1}), "deadbeef", source_root=source_root,
    )
    with _assert_raises_contains(
            BuildAdmissionError,
            "trigger binding predicate が materialized source と不一致",
    ):
        pipeline._require_materialized_trigger_predicate(evidence, binding)


def test_trigger_predicate_hole_indent_matches_template_patch_bytes():
    from orchestrator.campaign import axis_trigger_gating

    patch_path = Path(_REPOSITORY) / "patches" / axis_trigger_gating.TEMPLATE_PATCH
    patch_lines = patch_path.read_bytes().splitlines()
    begin = (
        b"+  // EVOLVE-BLOCK-BEGIN "
        + axis_trigger_gating.MARKER_ID.encode("utf-8")
    )
    end = (
        b"+  // EVOLVE-BLOCK-END "
        + axis_trigger_gating.MARKER_ID.encode("utf-8")
    )
    begin_indices = [index for index, line in enumerate(patch_lines) if line == begin]
    end_indices = [index for index, line in enumerate(patch_lines) if line == end]
    assert len(begin_indices) == 1
    assert len(end_indices) == 1
    begin_index, end_index = begin_indices[0], end_indices[0]
    assert begin_index < end_index

    block = patch_lines[begin_index + 1:end_index]
    if_indices = [
        index for index, line in enumerate(block)
        if line == b"+#if BACKOFF_TRIGGER_GATING"
    ]
    else_indices = [
        index for index, line in enumerate(block) if line == b"+#else"
    ]
    assert len(if_indices) == 1
    assert len(else_indices) == 1
    if_index, else_index = if_indices[0], else_indices[0]
    assert if_index < else_index
    expected_hole = (
        b"+"
        + axis_trigger_gating.PREDICATE_HOLE_INDENT.encode("utf-8")
        + b"izanagi_gate_pass = true;"
    )
    assert block[if_index + 1:else_index] == [expected_hole]


def test_trigger_binding_rejects_materialized_predicate_with_outer_spaces():
    from orchestrator.campaign import axis_trigger_gating

    source_root = _tmpdir("izanagi_trigger_outer_spaces_")
    source_path = os.path.join(source_root, axis_trigger_gating.SOURCE_REL)
    os.makedirs(os.path.dirname(source_path), exist_ok=True)
    predicate = emit_predicate(TriggerGateIR(20))
    _write_materialized_trigger_source(
        source_path, predicate, hole_line="  " + predicate + "  ",
    )
    _assert_materialized_trigger_predicate_rejected(source_root)


def test_trigger_binding_rejects_materialized_predicate_with_leading_tab():
    from orchestrator.campaign import axis_trigger_gating

    source_root = _tmpdir("izanagi_trigger_leading_tab_")
    source_path = os.path.join(source_root, axis_trigger_gating.SOURCE_REL)
    os.makedirs(os.path.dirname(source_path), exist_ok=True)
    predicate = emit_predicate(TriggerGateIR(20))
    _write_materialized_trigger_source(
        source_path, predicate, hole_line="\t" + predicate,
    )
    _assert_materialized_trigger_predicate_rejected(source_root)


def test_trigger_binding_rejects_materialized_predicate_with_leading_vertical_tab():
    from orchestrator.campaign import axis_trigger_gating

    source_root = _tmpdir("izanagi_trigger_leading_vertical_tab_")
    source_path = os.path.join(source_root, axis_trigger_gating.SOURCE_REL)
    os.makedirs(os.path.dirname(source_path), exist_ok=True)
    predicate = emit_predicate(TriggerGateIR(20))
    _write_materialized_trigger_source(
        source_path, predicate, hole_line="\v" + predicate,
    )
    _assert_materialized_trigger_predicate_rejected(source_root)


def test_trigger_binding_rejects_materialized_predicate_with_leading_form_feed():
    from orchestrator.campaign import axis_trigger_gating

    source_root = _tmpdir("izanagi_trigger_leading_form_feed_")
    source_path = os.path.join(source_root, axis_trigger_gating.SOURCE_REL)
    os.makedirs(os.path.dirname(source_path), exist_ok=True)
    predicate = emit_predicate(TriggerGateIR(20))
    _write_materialized_trigger_source(
        source_path, predicate, hole_line="\f" + predicate,
    )
    _assert_materialized_trigger_predicate_rejected(source_root)


def test_trigger_binding_rejects_materialized_predicate_with_leading_non_breaking_space():
    from orchestrator.campaign import axis_trigger_gating

    source_root = _tmpdir("izanagi_trigger_leading_non_breaking_space_")
    source_path = os.path.join(source_root, axis_trigger_gating.SOURCE_REL)
    os.makedirs(os.path.dirname(source_path), exist_ok=True)
    predicate = emit_predicate(TriggerGateIR(20))
    _write_materialized_trigger_source(
        source_path, predicate, hole_line="\u00a0" + predicate,
    )
    _assert_materialized_trigger_predicate_rejected(source_root)


def test_trigger_binding_rejects_materialized_predicate_with_leading_ideographic_space():
    from orchestrator.campaign import axis_trigger_gating

    source_root = _tmpdir("izanagi_trigger_leading_ideographic_space_")
    source_path = os.path.join(source_root, axis_trigger_gating.SOURCE_REL)
    os.makedirs(os.path.dirname(source_path), exist_ok=True)
    predicate = emit_predicate(TriggerGateIR(20))
    _write_materialized_trigger_source(
        source_path, predicate, hole_line="\u3000" + predicate,
    )
    _assert_materialized_trigger_predicate_rejected(source_root)


def test_trigger_binding_rejects_materialized_predicate_with_trailing_space():
    from orchestrator.campaign import axis_trigger_gating

    source_root = _tmpdir("izanagi_trigger_trailing_space_")
    source_path = os.path.join(source_root, axis_trigger_gating.SOURCE_REL)
    os.makedirs(os.path.dirname(source_path), exist_ok=True)
    predicate = emit_predicate(TriggerGateIR(20))
    _write_materialized_trigger_source(
        source_path, predicate, hole_line=predicate + " ",
    )
    _assert_materialized_trigger_predicate_rejected(source_root)


def test_trigger_binding_rejects_materialized_predicate_with_four_space_indent():
    from orchestrator.campaign import axis_trigger_gating

    source_root = _tmpdir("izanagi_trigger_four_spaces_")
    source_path = os.path.join(source_root, axis_trigger_gating.SOURCE_REL)
    os.makedirs(os.path.dirname(source_path), exist_ok=True)
    predicate = emit_predicate(TriggerGateIR(20))
    _write_materialized_trigger_source(
        source_path, predicate, hole_line="    " + predicate,
    )
    _assert_materialized_trigger_predicate_rejected(source_root)


def test_trigger_binding_rejects_materialized_predicate_with_crlf_line_ending():
    from orchestrator.campaign import axis_trigger_gating

    source_root = _tmpdir("izanagi_trigger_crlf_")
    source_path = os.path.join(source_root, axis_trigger_gating.SOURCE_REL)
    os.makedirs(os.path.dirname(source_path), exist_ok=True)
    predicate = emit_predicate(TriggerGateIR(20))
    _write_materialized_trigger_source(
        source_path, predicate, line_ending=b"\r\n",
    )
    _assert_materialized_trigger_predicate_rejected(source_root)


def test_trigger_binding_rejects_materialized_predicate_with_cr_only_line_ending():
    from orchestrator.campaign import axis_trigger_gating

    source_root = _tmpdir("izanagi_trigger_cr_only_")
    source_path = os.path.join(source_root, axis_trigger_gating.SOURCE_REL)
    os.makedirs(os.path.dirname(source_path), exist_ok=True)
    predicate = emit_predicate(TriggerGateIR(20))
    _write_materialized_trigger_source(
        source_path, predicate, line_ending=b"\r",
    )
    _assert_materialized_trigger_predicate_rejected(source_root)


def test_trigger_build_start_binding_uses_same_source_evidence_as_both_cache_builds():
    lay = _tmp_layout()
    from orchestrator.campaign import axis_trigger_gating

    source_root = _tmpdir("izanagi_trigger_materialized_")
    source_path = os.path.join(source_root, axis_trigger_gating.SOURCE_REL)
    os.makedirs(os.path.dirname(source_path), exist_ok=True)
    predicate = emit_predicate(TriggerGateIR(20))
    hole_line = _write_materialized_trigger_source(source_path, predicate)
    _install_complete_silo_proof_source(source_root)
    assert hole_line == "  " + predicate
    candidate = trigger_gate_binding.TriggerGateBinding(
        mask=20,
        predicate_sha256=trigger_gate_binding.expected_predicate_sha256(20),
        nonce="d" * 64,
        source=None,
    )
    with _mock_pipeline(certified=True) as calls:
        result = pipeline.evaluate(
            Genome("silo", {"BACK_OFF": 1}), lay, _AUTH_CONTRACT.env_tag, "deadbeef",
            PerfConfig(records=1000, threads=2), clocks_per_us=1800,
            numactl=_AUTH_CONTRACT.numactl,
            authorization_contract=_AUTHORIZATION,
            do_bench=False, build_context=_BUILD_CONTEXT,
            trigger_gate_binding=candidate, ccbench_dir=source_root,
            log=lambda *_args: None,
        )
    assert result.certified and calls.builds == [
        ("legacy", True, None), ("legacy", False, None),
    ]
    records = wal.read_records(lay)
    raw = next(record for record in records
               if record.stage == trigger_gate_binding.WAL_RECORD_STAGE)
    start = next(record for record in records if record.stage == STAGE_BUILD_START)
    binding = trigger_gate_binding.validate_record(
        raw.payload[wal.TRIGGER_BINDING_PAYLOAD_KEY], require_source=True,
    )
    receipt_source = start.payload["build_admission"]["source"]
    assert binding.source == trigger_gate_binding.SourceBinding(
        src_token=start.payload["src_token"],
        source_bytes_sha256=receipt_source["source_bytes_sha256"],
    )
    assert binding.source.src_token == receipt_source["src_token"]
    assert start.payload[wal.TRIGGER_BINDING_COMMITMENT_KEY] == \
        trigger_gate_binding.commitment(binding)
    assert "mask" not in start.payload


def test_trigger_binding_rejects_crossed_materialized_predicate_and_mask():
    lay = _tmp_layout()
    from orchestrator.campaign import axis_trigger_gating

    source_root = _tmpdir("izanagi_trigger_cross_binding_")
    source_path = os.path.join(source_root, axis_trigger_gating.SOURCE_REL)
    os.makedirs(os.path.dirname(source_path), exist_ok=True)
    predicate_a = emit_predicate(TriggerGateIR(20))
    hole_line = _write_materialized_trigger_source(source_path, predicate_a)
    assert hole_line == "  " + predicate_a
    binding_b = trigger_gate_binding.TriggerGateBinding(
        mask=21,
        predicate_sha256=trigger_gate_binding.expected_predicate_sha256(21),
        nonce="e" * 64,
        source=None,
    )
    with _mock_pipeline(certified=True) as calls:
        result = pipeline.evaluate(
            Genome("silo", {"BACK_OFF": 1}), lay, _AUTH_CONTRACT.env_tag, "deadbeef",
            PerfConfig(records=1000, threads=2), clocks_per_us=1800,
            numactl=_AUTH_CONTRACT.numactl,
            authorization_contract=_AUTHORIZATION,
            do_bench=False, build_context=_BUILD_CONTEXT,
            trigger_gate_binding=binding_b, ccbench_dir=source_root,
            log=lambda *_args: None,
        )
    assert result.aborted and calls.builds == []
    records = wal.read_records(lay)
    assert [record.stage for record in records] == [
        trigger_gate_binding.WAL_RECORD_STAGE, STAGE_BUILD_START, STAGE_ABORT,
    ]
    assert records[-1].payload["reason"] == "admission-error"
    assert records[-1].payload["error"] == (
        "BuildAdmissionError: "
        "trigger binding predicate が materialized source と不一致"
    )
    assert all("mask" not in record.payload for record in records[1:])


def test_trigger_prebuild_abort_records_source_null_binding_before_start():
    lay = _tmp_layout()
    candidate = trigger_gate_binding.TriggerGateBinding(
        mask=3,
        predicate_sha256=trigger_gate_binding.expected_predicate_sha256(3),
        nonce="3" * 64,
        source=None,
    )
    with _mock_pipeline(source_raises=True) as calls:
        result = pipeline.evaluate(
            Genome("silo", {"BACK_OFF": 1}), lay, _AUTH_CONTRACT.env_tag, "deadbeef",
            PerfConfig(records=1000, threads=2), clocks_per_us=1800,
            numactl=_AUTH_CONTRACT.numactl,
            authorization_contract=_AUTHORIZATION,
            do_bench=False, build_context=_BUILD_CONTEXT,
            trigger_gate_binding=candidate, log=lambda *_args: None,
        )
    assert result.aborted and calls.builds == []
    records = wal.read_records(lay)
    assert [record.stage for record in records] == [
        trigger_gate_binding.WAL_RECORD_STAGE, STAGE_BUILD_START, STAGE_ABORT,
    ]
    raw, start, _abort = records
    restored = trigger_gate_binding.validate_record(
        raw.payload[wal.TRIGGER_BINDING_PAYLOAD_KEY], require_source=False,
    )
    assert restored.source is None
    assert start.payload[wal.TRIGGER_BINDING_COMMITMENT_KEY] == \
        trigger_gate_binding.commitment(restored)


def test_build_admission_stock_positive_reaches_build_without_coder_opt_in():
    lay = _tmp_layout()
    with _mock_pipeline(certified=True) as calls:
        result = pipeline.evaluate(
            Genome("silo", {"BACK_OFF": 1}), lay, _AUTH_CONTRACT.env_tag, pin.CURRENT_PIN,
            PerfConfig(records=1000, threads=2), clocks_per_us=1800,
            numactl=_AUTH_CONTRACT.numactl,
            authorization_contract=_AUTHORIZATION,
            do_bench=False, build_context=_BUILD_CONTEXT, log=lambda *_args: None,
        )
    assert result.certified and len(calls.builds) == 2
    start = next(r for r in wal.read_records(lay) if r.stage == STAGE_BUILD_START)
    assert start.payload["build_admission"]["class"] == "stock-baseline"


def test_build_admission_is_immutable_and_rejects_nonexact_values():
    admission = _admission_for(Genome("silo", {}), "deadbeef")
    caught = None
    try:
        admission._body_json = "{}"
    except (AttributeError, TypeError) as exc:
        caught = exc
    assert caught is not None
    try:
        BuildAdmission(admission.provenance, {})
        assert False, "public constructor を受理してはならない"
    except BuildAdmissionError:
        pass


def test_build_admission_loop_and_screening_revalidate_before_build_entry_spy():
    from orchestrator.campaign import loop as L
    from orchestrator.campaign import screening_driver as SD

    bad = object()
    cfg = CampaignConfig(
        spec_slug="t316-admission", search_tag="test", spec_content="fixture",
        ccbench_commit="deadbeef",
    )
    genome = Genome("silo", {"BACK_OFF": 1})
    build_entries = []
    saved_eval, saved_sd = L.evaluate, L.source_digest
    L.evaluate = lambda *args, **kwargs: build_entries.append("loop")
    L.source_digest = _sd_mock("stock")
    loop_error = None
    try:
        try:
            L.run_campaign(
                cfg, [genome], PerfConfig(records=1, threads=1), "test", 1800,
                authorization_contract=_AUTHORIZATION,
                do_bench=False, output_root=_tmpdir("t316_loop_"),
                build_context=bad, declared_use_class="official",
                log=lambda *_args: None,
            )
        except TypeError as exc:
            loop_error = exc
    finally:
        L.evaluate, L.source_digest = saved_eval, saved_sd

    bound_cfg = _bound(cfg)
    layout = campaign_layout(str(ident.campaign_id(bound_cfg)), _tmpdir("t316_screen_"))
    saved_screen_eval = SD.evaluate
    SD.evaluate = lambda *args, **kwargs: build_entries.append("screening")
    screening_error = None
    try:
        try:
            SD.evaluate_candidate(
                cfg, layout, genome, PerfConfig(records=1, threads=1),
                _AUTH_CONTRACT.env_tag, _AUTH_CONTRACT.clocks_per_us,
                numactl=_AUTH_CONTRACT.numactl,
                authorization_contract=_AUTHORIZATION,
                build_context=bad, screening=None, src_token="stock",
                log=lambda *_args: None,
            )
        except TypeError as exc:
            screening_error = exc
    finally:
        SD.evaluate = saved_screen_eval
    assert build_entries == [], "loop/screening が build entry spy に到達した"
    assert loop_error is not None and screening_error is not None


def test_build_admission_noncoder_opt_in_is_rejected_independently():
    """Sealed BuildAdmission cannot be directly constructed for any class."""
    admission = _admission_for(Genome("silo", {}), "deadbeef")
    try:
        BuildAdmission(admission.provenance, admission.as_wal_receipt())
        assert False, "direct constructor must remain sealed"
    except BuildAdmissionError:
        pass


def test_build_admission_preview_never_reaches_build_entry_with_or_without_opt_in():
    from orchestrator.campaign import p3_s4_loop_sort as sort_preview
    from orchestrator.campaign import p3_s4_loop_trigger_gating as trigger_preview

    previews = []
    build_entries = []
    preview_cases = (
        (sort_preview, "_preview_diff", "--preview-diff", "fixture.txt"),
        (trigger_preview, "_preview_wire", "--preview-wire", "11111"),
    )
    for module, preview_name, preview_option, preview_value in preview_cases:
        saved_preview, saved_run = getattr(module, preview_name), module.run_campaign
        setattr(module, preview_name, lambda *_args, **_kwargs: previews.append(module) or {
            "passed": True,
        })
        module.run_campaign = lambda *_args, **_kwargs: build_entries.append(module)
        try:
            assert module.main([preview_option, preview_value]) == 0
            assert module.main([
                preview_option, preview_value, "--allow-coder-derived-build",
            ]) == 0
        finally:
            setattr(module, preview_name, saved_preview)
            module.run_campaign = saved_run
    assert len(previews) == 4
    assert build_entries == [], "preview が run_campaign build spy に到達した"


def test_pipeline_green_commits_with_fitness():
    lay = _tmp_layout()
    r, calls = _eval(lay, certified=True)
    assert r.certified and not r.aborted
    assert r.fitness_tps == 12345.0 and len(calls) == 1
    st = wal.replay(lay)[r.variant]
    assert st.committed and not st.aborted
    assert STAGE_COMMIT in st.stages_seen
    commit = [rec for rec in wal.read_records(lay) if rec.stage == STAGE_COMMIT][-1]
    assert "screened" not in commit.payload


def test_pipeline_env_contract_opt_in_uses_v2_for_trace_and_perf_only():
    lay = _tmp_layout()
    contract = ec.lookup("linux-baremetal")
    with _mock_pipeline(certified=True) as calls:
        result = pipeline.evaluate(
            Genome("silo", {"BACK_OFF": 1}), lay, contract.env_tag, "deadbeef",
            PerfConfig(records=1000, threads=2), clocks_per_us=1800,
            numactl=contract.numactl, authorization_contract=ec.authorize(contract.env_tag),
            do_bench=False, env_contract=contract, log=lambda *a: None,
        build_context=_BUILD_CONTEXT,
        )
    assert result.certified and not result.aborted
    assert calls.builds == [
        ("v2", True, contract.contract_sha256),
        ("v2", False, contract.contract_sha256),
    ]
    assert calls.build_options == [{
        "cc": buildcache.DEFAULT_CC,
        "cxx": buildcache.DEFAULT_CXX,
        "dependency_prefix": "",
    }] * 2


def test_m12_pipeline_compute_uses_gxx_for_source_digest_and_v2_builds():
    lay = _tmp_layout()
    contract = ec.lookup("pegasus")
    prefix = "/scr/job/gflags;/scr/job/glog"
    with _mock_pipeline(certified=True, site_compilers=("gcc", "g++")) as calls:
        result = pipeline.evaluate(
            Genome("silo", {"BACK_OFF": 1}), lay, "pegasus", "deadbeef",
            PerfConfig(records=1000, threads=2), clocks_per_us=2100,
            authorization_contract=ec.authorize(contract.env_tag), numactl=contract.numactl,
            do_bench=False, env_contract=contract, dependency_prefix=prefix,
            log=lambda *a: None, build_context=_BUILD_CONTEXT,
        )
    assert result.certified and not result.aborted
    assert calls.source_resolve_calls == [(
        (Genome("silo", {"BACK_OFF": 1}), "deadbeef", "", "g++"), {},
    )]
    assert calls.build_options == [{
        "cc": "gcc", "cxx": "g++", "dependency_prefix": prefix,
    }] * 2
    assert "site" not in inspect.signature(pipeline.evaluate).parameters


def test_pipeline_v2_passes_nondefault_prepared_ccbench_tree_to_both_builds(
        tmp_path,
):
    lay = _tmp_layout()
    contract = ec.lookup("linux-baremetal")
    prepared_tree = str(tmp_path / "prepared-cell-tree")
    _install_complete_silo_proof_source(prepared_tree)
    with _mock_pipeline(certified=True) as calls:
        result = pipeline.evaluate(
            Genome("silo", {"BACK_OFF": 1}), lay, contract.env_tag, "deadbeef",
            PerfConfig(records=1000, threads=2), clocks_per_us=1800,
            numactl=contract.numactl, authorization_contract=ec.authorize(contract.env_tag),
            do_bench=False, env_contract=contract, ccbench_dir=prepared_tree,
            log=lambda *a: None,
        build_context=_BUILD_CONTEXT,
        )
    assert result.certified and not result.aborted
    assert calls.build_roots == [prepared_tree, prepared_tree]


def test_pipeline_records_leading_indicators_in_wal():
    """P2-3: bench_done に leading indicators (abort率/latency/cache/IPC) が残る (§3.5)。"""
    lay = _tmp_layout()
    r, _ = _eval(lay, certified=True)
    bench = [rec for rec in wal.read_records(lay)
             if rec.stage == STAGE_BENCH_DONE]
    assert len(bench) == 1
    li = bench[0].payload.get("leading_indicators")
    assert li is not None
    assert set(li) == {"throughput_tps", "abort_rate", "latency_ns",
                       "llc_miss_rate", "ipc"}
    assert li["abort_rate"] == 0.03 and li["ipc"] == 1.5
    assert "screening" not in bench[0].payload
    assert "rep_returncodes" not in bench[0].payload
    assert isinstance(bench[0].payload.get("bench_wall_s"), float)
    assert bench[0].payload["bench_wall_s"] >= 0.0


def test_pipeline_receipt_none_omits_perf_observation_from_bench_payload():
    """P1: receipt 不在の official/legacy WAL shape は従来どおり不変。"""
    lay = _tmp_layout()
    result, _ = _eval(lay, certified=True)

    assert result.certified and not result.aborted
    bench = next(
        record for record in wal.read_records(lay)
        if record.stage == STAGE_BENCH_DONE
    )
    assert "perf_observation" not in bench.payload


def test_pipeline_records_returncodes_from_best_middle_round():
    """M-P2: 最終でなく、CV 最良の中間 round に属する rc だけを記録する。"""
    lay = _tmp_layout()
    rounds = [
        {"median": 100.0, "cv": 0.09, "rep_returncodes": [0, 0, 0, 0, 0]},
        {"median": 200.0, "cv": 0.06, "rep_returncodes": [0, 0, 4, 0, 0]},
        {"median": 300.0, "cv": 0.07, "rep_returncodes": [0, 0, 0, 0, 0]},
    ]

    result, _ = _eval(
        lay, certified=True, record_rep_returncodes=True,
        bench_rounds=rounds, unstable=True,
    )

    assert result.certified and not result.aborted
    bench = next(rec for rec in wal.read_records(lay)
                 if rec.stage == STAGE_BENCH_DONE)
    assert bench.payload["median_tps"] == 200.0
    assert bench.payload["rep_returncodes"] == [0, 0, 4, 0, 0]


def test_pipeline_cv_tie_keeps_first_round_returncodes_by_identity():
    """M-P3: CV 同値では dataclass 等値でなく、先に採用した点の identity へ結ぶ。"""
    lay = _tmp_layout()
    rounds = [
        {"median": 100.0, "cv": 0.06, "rep_returncodes": [0, 1, 0, 0, 0]},
        {"median": 100.0, "cv": 0.06, "rep_returncodes": [0, 0, 0, 0, 0]},
    ]

    result, _ = _eval(
        lay, certified=True, record_rep_returncodes=True,
        bench_rounds=rounds, unstable=True,
    )

    assert result.certified and not result.aborted
    bench = next(rec for rec in wal.read_records(lay)
                 if rec.stage == STAGE_BENCH_DONE)
    assert bench.payload["rep_returncodes"] == [0, 1, 0, 0, 0]


def _assert_returncode_round_binding_rejected(round_binding, expected_matches):
    lay = _tmp_layout()
    rounds = [
        {"median": 100.0, "cv": 0.08, "rep_returncodes": [0, 0, 0, 0, 0]},
        {"median": 100.0, "cv": 0.07, "rep_returncodes": [0, 0, 0, 0, 0]},
    ]

    result, _ = _eval(
        lay, certified=True, record_rep_returncodes=True,
        bench_rounds=rounds, unstable=True, round_binding=round_binding,
    )

    assert result.aborted
    records = wal.read_records(lay)
    assert not any(rec.stage == STAGE_BENCH_DONE for rec in records)
    assert not any(rec.stage == STAGE_COMMIT for rec in records)
    abort = [rec for rec in records if rec.stage == STAGE_ABORT][-1]
    assert abort.payload["reason"] == "bench-returncodes-round-unbound"
    assert abort.payload["matching_rounds"] == expected_matches


def test_pipeline_unmatched_returncode_round_aborts_before_bench_done():
    """M-P4: 採用点への identity 対応が 0 件なら WAL 性能値を書かない。"""
    _assert_returncode_round_binding_rejected("unmatched", 0)


def test_pipeline_duplicate_returncode_round_aborts_before_bench_done():
    """M-P4: 採用点への identity 対応が複数なら WAL 性能値を書かない。"""
    _assert_returncode_round_binding_rejected("duplicate", 2)


# _mock_pipeline の fake_build が返す full sha256 (trace=False=perf 側)。
_MOCK_PERF_SHA = "db" * 32
_MOCK_TRACE_SHA = "da" * 32


def test_pipeline_build_done_carries_full_and_prefix_bin_keys():
    """L1/A-8 結線: build_done payload に 4 キー (trace_bin/perf_bin=16 字 legacy-display、
    trace_bin_sha256/perf_bin_sha256=exact 64 lowercase hex) が揃い、旧 16 字キーが新 64 字
    キーの接頭辞であること。新キーの欠落 (結線消失) をこのテストが殺す。"""
    lay = _tmp_layout()
    r, _ = _eval(lay, certified=True)
    done = [rec for rec in wal.read_records(lay) if rec.stage == STAGE_BUILD_DONE]
    assert len(done) == 1
    p = done[0].payload
    for k in ("trace_bin", "perf_bin", "trace_bin_sha256", "perf_bin_sha256"):
        assert k in p, f"build_done に {k} が無い"
    assert p["trace_bin_sha256"] == _MOCK_TRACE_SHA
    assert p["perf_bin_sha256"] == _MOCK_PERF_SHA
    assert len(p["trace_bin_sha256"]) == 64 and len(p["perf_bin_sha256"]) == 64
    # 16 字系列は 64 字系列の exact 接頭辞 (sha256-prefix-16 契約)。
    assert p["trace_bin"] == p["trace_bin_sha256"][:16]
    assert p["perf_bin"] == p["perf_bin_sha256"][:16]


def test_pipeline_v2_build_done_records_bound_toolchain_once_for_trace_and_perf():
    expected = {
        role: {
            "requested": f"test-{role}",
            "realpath": f"/fixture/test-{role}",
            "version_first_line": f"{role} version A",
            "version": f"{role} version A",
        }
        for role in ("cc", "cxx", "cmake")
    }
    lay = _tmp_layout()
    with _mock_pipeline(site_compilers=("test-cc", "test-cxx")):
        result = pipeline.evaluate(
            Genome("silo", {"BACK_OFF": 1}), lay,
            _AUTH_CONTRACT.env_tag, "deadbeef",
            PerfConfig(records=1000, threads=2), clocks_per_us=1800,
            numactl=_AUTH_CONTRACT.numactl,
            authorization_contract=_AUTHORIZATION,
            build_context=_BUILD_CONTEXT, do_bench=False,
            env_contract=_AUTH_CONTRACT,
            expected_toolchain_manifest=expected,
            declared_use_class="official", log=lambda *_args: None,
        )
    assert result.certified and not result.aborted
    done = [rec for rec in wal.read_records(lay) if rec.stage == STAGE_BUILD_DONE]
    assert len(done) == 1
    payload = done[0].payload
    assert payload["toolchain"]["cc"] == {
        "requested": "test-cc", "realpath": "/fixture/test-cc",
        "version_first_line": "cc fixture",
    }
    assert payload["toolchain"]["cxx"] == {
        "requested": "test-cxx", "realpath": "/fixture/test-cxx",
        "version_first_line": "cxx fixture",
    }
    assert payload["toolchain_record_sha256"] == hashlib.sha256(
        json.dumps(expected, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()
    assert "toolchain_manifest_sha256" not in payload


def test_pipeline_v2_toolchain_mismatch_aborts_before_build_done():
    expected = {
        role: {
            "requested": f"test-{role}",
            "realpath": f"/fixture/test-{role}",
            "version_first_line": f"{role} version A",
            "version": f"{role} version A",
        }
        for role in ("cc", "cxx", "cmake")
    }
    lay = _tmp_layout()
    with _mock_pipeline(site_compilers=("test-cc", "test-cxx")):
        real_build_v2 = pipeline.buildcache.build_v2

        def mismatching_build_v2(genome, *, trace, **kwargs):
            result = real_build_v2(genome, trace=trace, **kwargs)
            if trace:
                result.toolchain = dict(result.toolchain)
                result.toolchain["cxx"] = dict(result.toolchain["cxx"])
                result.toolchain["cxx"]["realpath"] = "/fixture/other-cxx"
            return result

        pipeline.buildcache.build_v2 = mismatching_build_v2
        result = pipeline.evaluate(
            Genome("silo", {"BACK_OFF": 1}), lay,
            _AUTH_CONTRACT.env_tag, "deadbeef",
            PerfConfig(records=1000, threads=2), clocks_per_us=1800,
            numactl=_AUTH_CONTRACT.numactl,
            authorization_contract=_AUTHORIZATION,
            build_context=_BUILD_CONTEXT, do_bench=False,
            env_contract=_AUTH_CONTRACT,
            expected_toolchain_manifest=expected,
            declared_use_class="official", log=lambda *_args: None,
        )
    assert result.aborted and not result.certified
    records = wal.read_records(lay)
    assert not any(rec.stage == STAGE_BUILD_DONE for rec in records)
    abort = [rec for rec in records if rec.stage == STAGE_ABORT]
    assert len(abort) == 1
    assert abort[0].payload["error"] == "trace/perf toolchain binding mismatch"


def test_pipeline_perf_sha_gate_mismatch_aborts_before_trace_and_bench():
    """A-1 positive control: expected_perf_sha256 が perf バイナリと不一致なら、trace/bench を
    一度も起動せず bench-binary-mismatch で abort。payload に expected/actual/path が載る。"""
    lay = _tmp_layout()
    r, calls = _eval(lay, certified=True, expected_perf_sha256=_MOCK_TRACE_SHA)  # perf!=trace
    assert r.aborted and not r.certified
    assert len(calls) == 0 and len(calls.trace) == 0     # trace も bench も走らない
    aborts = [rec for rec in wal.read_records(lay) if rec.stage == STAGE_ABORT]
    assert len(aborts) == 1
    p = aborts[0].payload
    assert p["reason"] == "bench-binary-mismatch"
    assert p["expected"] == _MOCK_TRACE_SHA
    assert p["actual"] == _MOCK_PERF_SHA                  # 実測 (perf) が載る
    assert "path" in p
    assert STAGE_VERIFY_DONE not in {rec.stage for rec in wal.read_records(lay)}


def test_pipeline_perf_sha_gate_match_continues_normally():
    """A-1: expected_perf_sha256 が perf バイナリと一致すれば従来どおり続行 (certified)。"""
    lay = _tmp_layout()
    r, calls = _eval(lay, certified=True, expected_perf_sha256=_MOCK_PERF_SHA)
    assert r.certified and not r.aborted
    assert len(calls) == 1                                # 通常どおり bench が走る


def test_pipeline_perf_sha_gate_rejects_malformed_expected():
    """A-6/A-1: expected が exact 64 lowercase hex でない (16 桁等) 場合も受理せず、trace/bench
    を起動せず bench-binary-mismatch で abort (prefix 照合しない, fail-closed)。"""
    lay = _tmp_layout()
    r, calls = _eval(lay, certified=True,
                     expected_perf_sha256=_MOCK_PERF_SHA[:16])  # 16 桁 (perf の正 prefix)
    assert r.aborted and not r.certified
    assert len(calls) == 0 and len(calls.trace) == 0
    aborts = [rec for rec in wal.read_records(lay) if rec.stage == STAGE_ABORT]
    assert aborts[0].payload["reason"] == "bench-binary-mismatch"
    # 形不正でも actual (build 済み bin_sha256) は記録される。expected は形不正の 16 桁のまま。
    assert aborts[0].payload["expected"] == _MOCK_PERF_SHA[:16]
    assert aborts[0].payload["actual"] == _MOCK_PERF_SHA


def test_pipeline_no_gate_by_default_is_unchanged():
    """デフォルト (expected_perf_sha256=None) では gate 不発 = 従来と完全同一挙動。"""
    lay = _tmp_layout()
    r, calls = _eval(lay, certified=True)
    assert r.certified and len(calls) == 1
    done = [rec for rec in wal.read_records(lay) if rec.stage == STAGE_BUILD_DONE]
    assert done and "bench-binary-mismatch" not in {
        rec.payload.get("reason") for rec in wal.read_records(lay)}


def _assert_legacy_cache_hit_site_refusal(site):
    """legacy build 2 本が cache hit した後でも producer 前で拒否する。"""
    lay = _tmp_layout()
    subprocess_calls = []

    def forbidden_subprocess(*args, **kwargs):
        subprocess_calls.append((args, kwargs))
        raise AssertionError("拒否理由の生成で subprocess を起動してはならない")

    with _mock_pipeline(
            certified=True, build_cached=True, measurement_site=site) as calls:
        with unittest_mock.patch.object(
                pipeline.subprocess, "run", forbidden_subprocess):
            try:
                pipeline.evaluate(
                    Genome("silo", {"BACK_OFF": 1}), lay,
                    _AUTH_CONTRACT.env_tag, "deadbeef",
                    PerfConfig(records=1000, threads=2), clocks_per_us=1800,
                    numactl=_AUTH_CONTRACT.numactl,
                    authorization_contract=_AUTHORIZATION,
                    log=lambda *a: None, build_context=_BUILD_CONTEXT,
                )
            except buildcache.BuildError as exc:
                assert "計算ノード" in str(exc)
            else:
                raise AssertionError(f"{site} の cache hit 後に producer が拒否されなかった")

    assert calls.builds == [("legacy", True, None), ("legacy", False, None)]
    assert calls.cache_hits == [True, True]
    assert calls.trace == [] and len(calls) == 0
    assert subprocess_calls == []
    records = list(wal.read_records(lay))
    build_done = [record for record in records if record.stage == STAGE_BUILD_DONE]
    assert len(build_done) == 1
    assert build_done[0].payload["trace_cached"] is True
    assert build_done[0].payload["perf_cached"] is True
    assert STAGE_VERIFY_DONE not in {record.stage for record in records}
    assert STAGE_BENCH_DONE not in {record.stage for record in records}
    assert STAGE_COMMIT not in {record.stage for record in records}


def test_m18_legacy_cache_hit_login_refuses_measurement_and_commit():
    """禁止署名: LOGIN では legacy cache hit 後も producer/COMMIT を通さない。"""
    _assert_legacy_cache_hit_site_refusal(site_policy.PEGASUS_LOGIN)


def test_m18_legacy_cache_hit_suspect_refuses_measurement_and_commit():
    """禁止署名: SUSPECT も LOGIN と同じく fail-closed に拒否する。"""
    _assert_legacy_cache_hit_site_refusal(site_policy.PEGASUS_SUSPECT)


def test_m18_legacy_cache_hit_compute_measures_and_commits():
    """正例: COMPUTE の legacy cache hit は従来どおり verify/bench/COMMIT する。"""
    lay = _tmp_layout()
    result, calls = _eval(
        lay, certified=True, build_cached=True,
        measurement_site=site_policy.PEGASUS_COMPUTE,
    )
    assert result.certified and not result.aborted
    assert result.fitness_tps == 12345.0
    assert calls.cache_hits == [True, True]
    assert len(calls.trace) == 1 and len(calls) == 1
    commits = [record for record in wal.read_records(lay)
               if record.stage == STAGE_COMMIT]
    assert len(commits) == 1
    assert commits[0].payload["fitness_tps"] == 12345.0


def test_m18_legacy_cache_hit_other_remains_accepted():
    """受理集合を LOGIN/SUSPECT 以外へ狭めず、OTHER の従来挙動を保つ。"""
    lay = _tmp_layout()
    result, calls = _eval(
        lay, certified=True, build_cached=True,
        measurement_site=site_policy.OTHER,
    )
    assert result.certified and result.fitness_tps == 12345.0
    assert calls.cache_hits == [True, True]
    assert len(calls.trace) == 1 and len(calls) == 1
    assert any(record.stage == STAGE_COMMIT for record in wal.read_records(lay))


def test_m18_trace_producer_refuses_before_subprocess():
    """_run_trace 自身の gate を削る変異を subprocess spy で kill する。"""
    trace_root = _tmpdir("izanagi_login_trace_producer_")
    calls = []

    def forbidden_subprocess(*args, **kwargs):
        calls.append((args, kwargs))
        raise AssertionError("LOGIN で trace subprocess を起動してはならない")

    saved_resolve = pipeline._resolve_site
    try:
        pipeline._resolve_site = lambda _site=None: site_policy.PEGASUS_LOGIN
        with unittest_mock.patch.object(
                pipeline.subprocess, "run", forbidden_subprocess):
            try:
                pipeline._run_trace(
                    "/not/executed/ycsb.exe", trace_root, {}, clocks_per_us=1800,
                )
            except buildcache.BuildError:
                pass
            else:
                raise AssertionError("LOGIN の trace producer が拒否されなかった")
    finally:
        pipeline._resolve_site = saved_resolve
    assert calls == []
    assert not os.path.exists(os.path.join(trace_root, "log"))


def test_m18_throughput_producer_refuses_before_measure_point():
    """_run_bench 自身の gate を削る変異を measure_point spy で kill する。"""
    lay = _tmp_layout()
    calls = []
    saved_resolve = pipeline._resolve_site
    saved_measure = pipeline.measure_point
    try:
        pipeline._resolve_site = lambda _site=None: site_policy.PEGASUS_SUSPECT
        pipeline.measure_point = lambda *args, **kwargs: calls.append((args, kwargs))
        try:
            pipeline._run_bench(
                "/not/executed/ycsb.exe",
                PerfConfig(records=1000, threads=2),
                1800, None, False, lay, "variant", "test-env",
                lambda *args, **kwargs: None,
                build_attempt_id="test-attempt",
            )
        except buildcache.BuildError:
            pass
        else:
            raise AssertionError("SUSPECT の throughput producer が拒否されなかった")
    finally:
        pipeline._resolve_site = saved_resolve
        pipeline.measure_point = saved_measure
    assert calls == []


def test_m18_commit_rechecks_site_immediately_before_write():
    """計測後に site が拒否側なら fitness_tps を COMMIT しない。"""
    lay = _tmp_layout()
    sites = iter((
        site_policy.PEGASUS_COMPUTE,  # cache hit 後 producer 前
        site_policy.PEGASUS_COMPUTE,  # _run_bench 入口
        site_policy.PEGASUS_LOGIN,    # COMMIT 直前
    ))
    with _mock_pipeline(certified=True, build_cached=True) as calls:
        pipeline._resolve_site = lambda _site=None: next(sites)
        try:
            pipeline.evaluate(
                Genome("silo", {"BACK_OFF": 1}), lay,
                _AUTH_CONTRACT.env_tag, "deadbeef",
                PerfConfig(records=1000, threads=2), clocks_per_us=1800,
                numactl=_AUTH_CONTRACT.numactl,
                authorization_contract=_AUTHORIZATION,
                log=lambda *a: None, build_context=_BUILD_CONTEXT,
            )
        except buildcache.BuildError:
            pass
        else:
            raise AssertionError("LOGIN で COMMIT が拒否されなかった")
    assert len(calls.trace) == 1 and len(calls) == 1
    assert not any(record.stage == STAGE_COMMIT for record in wal.read_records(lay))


def test_m18_no_bench_commit_rechecks_site_immediately_before_write():
    """fitness 無しの配線用 COMMIT も拒否 site では書かない。"""
    lay = _tmp_layout()
    sites = iter((
        site_policy.PEGASUS_COMPUTE,  # cache hit 後 producer 前
        site_policy.PEGASUS_SUSPECT,  # no-bench COMMIT 直前
    ))
    with _mock_pipeline(certified=True, build_cached=True) as calls:
        pipeline._resolve_site = lambda _site=None: next(sites)
        try:
            pipeline.evaluate(
                Genome("silo", {"BACK_OFF": 1}), lay,
                _AUTH_CONTRACT.env_tag, "deadbeef",
                PerfConfig(records=1000, threads=2), clocks_per_us=1800,
                numactl=_AUTH_CONTRACT.numactl,
                authorization_contract=_AUTHORIZATION,
                do_bench=False, log=lambda *a: None,
                build_context=_BUILD_CONTEXT,
            )
        except buildcache.BuildError:
            pass
        else:
            raise AssertionError("SUSPECT で no-bench COMMIT が拒否されなかった")
    assert len(calls.trace) == 1 and len(calls) == 0
    assert not any(record.stage == STAGE_COMMIT for record in wal.read_records(lay))


def test_pipeline_red_aborts_without_fitness_or_bench():
    """規律2: verifier が non-certified なら abort。fitness を付けず、bench も走らせない。"""
    lay = _tmp_layout()
    r, calls = _eval(lay, certified=False)
    assert r.aborted and not r.certified
    assert r.fitness_tps is None
    assert len(calls) == 0                       # 壊れた variant に計測資源を使わない
    st = wal.replay(lay)[r.variant]
    assert st.aborted and not st.committed       # commit レコードが無い (採用されない)
    assert STAGE_ABORT in st.stages_seen
    assert STAGE_COMMIT not in st.stages_seen


def test_pipeline_write_intent_violation_aborts_without_commit():
    """I 行入り trace は実 parser/verifier を通って correctness gate で reject される。
    cycle ではないため serializable=True のまま indeterminate、fitness/COMMIT は無し。"""
    trace_content = (
        "C 0 0 5 10 0 1\n"
        "W 0 aa U 5 10\n"
        "I 0 aa write-set-entry-without-intent\n"
        "E 0\n"
    )
    i_rows = [line for line in trace_content.splitlines() if line.startswith("I ")]
    assert i_rows == ["I 0 aa write-set-entry-without-intent"]  # DW-M03: 単一理由

    lay = _tmp_layout()
    r, calls = _eval(lay, trace_content=trace_content, ncommit=1)

    assert r.aborted and not r.certified
    assert r.verdict == "indeterminate"
    assert r.fitness_tps is None
    assert len(calls) == 0
    records = wal.read_records(lay)
    assert STAGE_COMMIT not in {record.stage for record in records}
    verify_done = [record for record in records
                   if record.stage == STAGE_VERIFY_DONE]
    assert len(verify_done) == 1
    assert verify_done[0].payload["verdict"] == "indeterminate"
    assert verify_done[0].payload["certified"] is False
    abort = [record for record in records if record.stage == STAGE_ABORT]
    assert len(abort) == 1 and abort[0].payload["reason"] == "indeterminate"
    verify = abort[0].payload["verify"]
    assert verify["integrity"]["write_intent_violations"] == 1
    assert verify["total_cycles"] == 0
    assert verify["serializable"] is True
    assert verify["certified"] is False


def test_pipeline_red_abort_carries_structured_anomaly():
    """S4 (規律3 配線): verify-red の abort payload に構造化 anomaly (cycle/edge/EdgeReason) が
    載り件数に潰れない。Phase 3 の RED variant で次手生成が『なぜ壊れたか』を読める前提。"""
    lay = _tmp_layout()
    r, _ = _eval(lay, certified=False)
    aborts = [rec for rec in wal.read_records(lay) if rec.stage == STAGE_ABORT]
    assert len(aborts) == 1
    verify = aborts[0].payload.get("verify")
    assert verify is not None, "abort payload に verify 構造が無い (件数に潰れている = S4 未配線)"
    assert verify["verdict"] == "non-serializable"
    assert verify["anomaly_count"] == 1
    a = verify["anomalies"][0]
    assert a["phenomenon"] == "G2" and a["cycle"] == [1, 2]
    edge = a["edges"][0]                          # どの依存で cycle ができたかまで残る
    assert edge["from"] == 1 and edge["to"] == 2 and "rw" in edge["types"]
    assert edge["reasons"][0]["key"] == "aa"
    assert "trace_dir" not in verify              # 使い捨て tmpdir は載せない


def test_parse_abort_counts_matches_ccbench_stdout():
    """abort_counts_ 集計のパース: 実 stdout 形式 (タブ区切り) を読み、
    batch_abort_counts_ を誤マッチせず、行が無ければ None (呼び手が fails-closed)。"""
    stdout = ("success_forwarding_:\t0\n"
              "abort_counts_:\t3742\n"
              "batch_abort_counts_:\t99\n"
              "commit_counts_:\t81234\n")
    assert pipeline._parse_abort_counts(stdout) == 3742
    assert pipeline._parse_abort_counts("batch_abort_counts_:\t99\n") is None
    assert pipeline._parse_abort_counts("") is None
    assert pipeline._parse_abort_counts("abort_counts_:\t0\n") == 0


def test_pipeline_verify_payload_records_aborts():
    """phase3.md blocking: STAGE_VERIFY_DONE payload に verify run の abort 数が載る。
    完了条件 2『abort > 0 = 合成枝 (abort-path) が verify 中に実行された証拠』を WAL で
    機械確認する前提配線 (旧配線は abort 数をどこにも記録せず確認自体が実行不能だった)。"""
    lay = _tmp_layout()
    r, _ = _eval(lay, certified=True, aborts=42)
    recs = [rec for rec in wal.read_records(lay) if rec.stage == STAGE_VERIFY_DONE]
    assert len(recs) == 1
    assert recs[0].payload.get("aborts") == 42
    assert recs[0].payload.get("commits") == 100


def test_pipeline_missing_abort_counts_rejects():
    """abort_counts_ が stdout から読めない run は certified にしない (fails-closed)。
    空振り認証 (abort≈0 で合成枝が未実行のまま緑) の検査可能性を落としたまま
    緑を出さない (規律3: 計器の故障を沈黙させない)。"""
    lay = _tmp_layout()
    r, calls = _eval(lay, certified=True, aborts=None)
    assert r.aborted and not r.certified and len(calls) == 0
    st = wal.replay(lay)[r.variant]
    assert st.aborted and not st.committed
    assert STAGE_VERIFY_DONE not in st.stages_seen        # verify 前に reject
    assert st.last_terminal.payload.get("reason") == "trace-no-abort-counts"


def test_pipeline_missing_commit_witness_rejects_with_structured_wal():
    lay = _tmp_layout()
    r, calls = _eval(lay, do_bench=False, commit_witness=None)
    assert r.aborted and not r.certified and calls.verify_witnesses == []
    payload = wal.replay(lay)[r.variant].last_terminal.payload
    assert payload["reason"] == "trace-no-commit-witness"
    assert payload["commit_witness"] == {
        "commit_counts": None,
        "batch_commit_counts": 0,
    }
    assert payload["workload"] == {"tag": "legacy"}
    assert STAGE_VERIFY_DONE not in wal.replay(lay)[r.variant].stages_seen


def test_pipeline_missing_batch_commit_witness_rejects():
    lay = _tmp_layout()
    r, calls = _eval(lay, do_bench=False, batch_witness=None)
    assert r.aborted and calls.verify_witnesses == []
    payload = wal.replay(lay)[r.variant].last_terminal.payload
    assert payload["reason"] == "trace-no-commit-witness"
    assert payload["commit_witness"] == {
        "commit_counts": 100,
        "batch_commit_counts": None,
    }


def test_pipeline_nonzero_batch_commits_rejects_with_structured_wal():
    lay = _tmp_layout()
    r, calls = _eval(lay, do_bench=False, batch_witness=1)
    assert r.aborted and not r.certified and calls.verify_witnesses == []
    payload = wal.replay(lay)[r.variant].last_terminal.payload
    assert payload["reason"] == "trace-batch-commits-unattributed"
    assert payload["commit_witness"] == {
        "commit_counts": 100,
        "batch_commit_counts": 1,
    }
    assert payload["workload"] == {"tag": "legacy"}


def test_pipeline_unsupported_workload_rejects_with_structured_wal():
    lay = _tmp_layout()
    r, calls = _eval(lay, do_bench=False, unsupported_workload=True)
    assert r.aborted and not r.certified and calls.verify_witnesses == []
    payload = wal.replay(lay)[r.variant].last_terminal.payload
    assert payload["reason"] == "trace-witness-unsupported-workload"
    assert payload["commit_witness"] == {
        "commit_counts": None,
        "batch_commit_counts": None,
    }
    assert payload["binary_workload"] == "tpcc_silo.exe"
    assert payload["workload"] == {"tag": "legacy"}


def test_pipeline_unavailable_trace_dir_rejects_with_structured_wal():
    lay = _tmp_layout()
    r, calls = _eval(lay, do_bench=False, unavailable_trace_dir=True)
    assert r.aborted and not r.certified and calls.verify_witnesses == []
    payload = wal.replay(lay)[r.variant].last_terminal.payload
    assert payload["reason"] == "trace-no-commit-witness"
    assert payload["commit_witness"] == {
        "commit_counts": None,
        "batch_commit_counts": None,
    }
    assert payload["trace_dir"] == "/fixture/missing-traces"
    assert payload["trace_dir_error"] == "missing"
    assert payload["workload"] == {"tag": "legacy"}


def test_pipeline_preexisting_trace_rejects_with_structured_wal():
    lay = _tmp_layout()
    r, calls = _eval(lay, do_bench=False, preexisting_trace=True)
    assert r.aborted and not r.certified and calls.verify_witnesses == []
    payload = wal.replay(lay)[r.variant].last_terminal.payload
    assert payload["reason"] == "trace-no-commit-witness"
    assert payload["commit_witness"] == {
        "commit_counts": None,
        "batch_commit_counts": None,
    }
    assert payload["preexisting_trace_files"] == ["trace_0.log"]
    assert payload["workload"] == {"tag": "legacy"}


def test_pipeline_tail_loss_witness_reaches_verifier():
    lay = _tmp_layout()
    trace = "C 0 0 1 1 0 1\nW 0 aa U 1 1\n"
    r, calls = _eval(
        lay, do_bench=False, trace_content=trace,
        ncommit=1, commit_witness=2,
    )
    assert r.aborted and not r.certified
    assert calls.verify_witnesses == [2]
    payload = wal.replay(lay)[r.variant].last_terminal.payload
    assert payload["reason"] == "indeterminate"
    expected_note = "commit witness mismatch: expected=2 observed=1 delta=-1"
    framing_note = (
        "1 txn framing violation(s) [missing-end×1] — declared R/W counts or "
        "mandatory E boundary is broken (trace may omit dependency edges): "
        "txn0 missing-end reads=0/0 writes=1/1"
    )
    assert payload["verify"]["integrity"]["notes"] == [
        expected_note,
        framing_note,
    ]
    assert payload["verify"]["integrity"]["clean"] is False
    assert payload["verify"]["certified"] is False
    verify_records = [
        record for record in wal.read_records(lay)
        if record.stage == STAGE_VERIFY_DONE
    ]
    assert len(verify_records) == 1
    assert verify_records[0].payload["commit_witness"] == {
        "commit_counts": 2,
        "batch_commit_counts": 0,
    }
    assert STAGE_COMMIT not in wal.replay(lay)[r.variant].stages_seen


def test_pipeline_matching_commit_witness_commits_and_records_verify_payload():
    lay = _tmp_layout()
    r, calls = _eval(lay, do_bench=False)
    assert r.certified and not r.aborted
    assert calls.verify_witnesses == [100]
    records = list(wal.read_records(lay))
    verify = [record for record in records if record.stage == STAGE_VERIFY_DONE]
    assert len(verify) == 1
    assert verify[0].payload["commit_witness"] == {
        "commit_counts": 100,
        "batch_commit_counts": 0,
    }
    assert verify[0].payload["proof_surfaces"] == {
        "protocol": "silo",
        "X": "evidence-present",
        "P": "evidence-present",
        "I": "evidence-absent",
    }
    assert any(record.stage == STAGE_COMMIT for record in records)


def test_pipeline_records_mocc_missing_proof_surfaces_and_does_not_commit():
    """同じ実 verifier 入力を mocc source assessment で fail-closed にする。"""
    lay = _tmp_layout()
    result, calls = _eval(lay, do_bench=False, protocol="mocc")
    assert calls.verify_witnesses == [100]
    assert result.aborted and not result.certified
    assert result.verdict == "indeterminate"
    records = list(wal.read_records(lay))
    verify = [record for record in records if record.stage == STAGE_VERIFY_DONE]
    assert len(verify) == 1
    assert verify[0].payload["proof_surfaces"] == {
        "protocol": "mocc",
        "X": "evidence-absent",
        "P": "evidence-absent",
        "I": "evidence-absent",
    }
    assert STAGE_COMMIT not in {record.stage for record in records}


def test_run_trace_parses_abort_from_stdout():
    """回帰 (結線検査): 実 _run_trace が ccbench stdout を _parse_abort_counts に通して
    型付き結果の属性で返す。_parse_abort_counts 単体と pipeline 層 (_run_trace ごとモック) の
    テストだけでは、この結線を消しても (旧配線 = stdout を捨てる) 全緑のまま
    (2026-07-03 敵対検証 medium: テスト正直さ)。"""
    sdir = _tmpdir("izanagi_runtrace_bin_")
    fake = os.path.join(sdir, "ycsb_fake_ccbench.sh")
    with open(fake, "w", encoding="utf-8") as f:
        f.write("#!/bin/sh\nprintf 'abort_counts_:\\t42\\n'\n")
    os.chmod(fake, 0o755)
    result = pipeline._run_trace(
        fake, _tmpdir("izanagi_runtrace_t1_"), {"w": "1"}, 1800,
    )
    assert (result.trace_c_lines, result.returncode, result.abort_counts) == (0, 0, 42)
    fake2 = os.path.join(sdir, "ycsb_fake_noabort.sh")
    with open(fake2, "w", encoding="utf-8") as f:
        f.write("#!/bin/sh\nprintf 'commit_counts_:\\t9\\n'\n")
    os.chmod(fake2, 0o755)
    result2 = pipeline._run_trace(
        fake2, _tmpdir("izanagi_runtrace_t2_"), {}, 1800,
    )
    assert result2.abort_counts is None      # 集計行なし → None (呼び手が fails-closed)


def test_run_trace_parses_commit_witness_from_stdout():
    """回帰 (結線検査): 実 _run_trace が ccbench stdout を _parse_abort_counts に通して
    型付き結果の属性で返し、commit/batch witness も同じ stdout から束ねる。
    _parse_abort_counts 単体と pipeline 層 (_run_trace ごとモック) の
    テストだけでは、この結線を消しても (旧配線 = stdout を捨てる) 全緑のまま
    (2026-07-03 敵対検証 medium: テスト正直さ)。"""
    sdir = _tmpdir("izanagi_runtrace_bin_")
    fake = os.path.join(sdir, "ycsb_fake_ccbench.sh")
    with open(fake, "w", encoding="utf-8") as f:
        f.write(
            "#!/bin/sh\nprintf 'abort_counts_:\\t42\\n"
            "commit_counts_:\\t9\\nbatch_commit_counts_:\\t0\\n'\n"
        )
    os.chmod(fake, 0o755)
    result = pipeline._run_trace(
        fake, _tmpdir("izanagi_runtrace_t1_"), {"w": "1"}, 1800,
    )
    assert result.trace_c_lines == 0
    assert result.returncode == 0
    assert result.abort_counts == 42
    assert result.commit_count_witness == 9
    assert result.batch_commit_count_witness == 0
    fake2 = os.path.join(sdir, "ycsb_fake_noabort.sh")
    with open(fake2, "w", encoding="utf-8") as f:
        f.write(
            "#!/bin/sh\nprintf 'commit_counts_:\\t9\\n"
            "batch_commit_counts_:\\t0\\n'\n"
        )
    os.chmod(fake2, 0o755)
    result2 = pipeline._run_trace(
        fake2, _tmpdir("izanagi_runtrace_t2_"), {}, 1800,
    )
    assert result2.abort_counts is None       # 集計行なし → None (呼び手が fails-closed)


def test_run_trace_prepends_exact_nonempty_numactl_to_subprocess_argv():
    """実 _run_trace が登録 prefix を subprocess argv 先頭へ落とさず渡す。"""
    trace_dir = _tmpdir("izanagi_runtrace_numactl_")
    binary = "/not/executed/ycsb_silo.exe"
    prefix = ("numactl", "--interleave=all")
    calls = []

    def subprocess_spy(argv, **kwargs):
        calls.append((argv, kwargs))
        return types.SimpleNamespace(
            returncode=0,
            stdout=("abort_counts_: 0\ncommit_counts_: 0\n"
                    "batch_commit_counts_: 0\n"),
        )

    with unittest_mock.patch.object(pipeline.subprocess, "run", subprocess_spy):
        pipeline._run_trace(
            binary, trace_dir, {"thread_num": "48"}, 1800,
            numactl=prefix,
        )

    assert len(calls) == 1
    argv = calls[0][0]
    assert argv[:len(prefix)] == list(prefix)
    assert argv[len(prefix)] == binary


def test_commit_witness_parser_rejects_duplicate_stdout():
    assert pipeline._parse_commit_witness(
        "commit_counts_: 1\ncommit_counts_: 1\nbatch_commit_counts_: 0\n"
    ) == (None, 0)


def test_commit_witness_parser_rejects_missing_stdout():
    assert pipeline._parse_commit_witness("batch_commit_counts_: 0\n") == (None, 0)


def test_commit_witness_parser_rejects_negative_stdout():
    assert pipeline._parse_commit_witness(
        "commit_counts_: -1\nbatch_commit_counts_: 0\n"
    ) == (None, 0)


def test_commit_witness_parser_rejects_noninteger_stdout():
    assert pipeline._parse_commit_witness(
        "commit_counts_: nope\nbatch_commit_counts_: 0\n"
    ) == (None, 0)


def test_run_trace_rejects_non_ycsb_binary_before_subprocess():
    tdir = _tmpdir("izanagi_runtrace_tpcc_")
    try:
        pipeline._run_trace("/not/executed/tpcc_silo.exe", tdir, {}, 1800)
        assert False, "YCSB allowlist 外を拒否すべき"
    except pipeline._TraceWitnessUnsupportedWorkload as exc:
        assert exc.workload == "tpcc_silo.exe"
    assert not os.path.exists(os.path.join(tdir, "log"))


def test_run_trace_rejects_preexisting_trace_files_before_subprocess():
    tdir = _tmpdir("izanagi_runtrace_stale_")
    with open(os.path.join(tdir, "trace_0.log"), "w", encoding="ascii") as stream:
        stream.write("C 0 0 1 1 0 0\nE 0\n")
    calls = []

    def subprocess_spy(*args, **kwargs):
        calls.append((args, kwargs))
        return types.SimpleNamespace(
            returncode=0,
            stdout=("abort_counts_: 0\ncommit_counts_: 1\n"
                    "batch_commit_counts_: 0\n"),
        )

    caught = None
    with unittest_mock.patch.object(
            pipeline.subprocess, "run", subprocess_spy):
        try:
            pipeline._run_trace(
                "/not/executed/ycsb_silo.exe", tdir, {}, 1800
            )
        except pipeline._TraceDirNotEmpty as exc:
            caught = exc
    assert caught is not None, "残骸 trace を拒否すべき"
    assert caught.paths == ("trace_0.log",)
    assert calls == []
    assert not os.path.exists(os.path.join(tdir, "log"))


def test_run_trace_rejects_missing_trace_dir_before_subprocess():
    root = _tmpdir("izanagi_runtrace_missing_root_")
    missing = os.path.join(root, "missing")
    calls = []
    with unittest_mock.patch.object(
            pipeline.subprocess, "run", lambda *a, **k: calls.append((a, k))):
        try:
            pipeline._run_trace("/not/executed/ycsb_silo.exe", missing, {}, 1800)
            assert False, "不在 trace_dir を拒否すべき"
        except pipeline._TraceDirUnavailable as exc:
            assert exc.path == missing
            assert exc.reason == "missing"
    assert calls == []


def test_run_trace_rejects_nondirectory_trace_dir_before_subprocess():
    root = _tmpdir("izanagi_runtrace_file_root_")
    not_directory = os.path.join(root, "trace-file")
    with open(not_directory, "w", encoding="ascii") as stream:
        stream.write("not a directory\n")
    calls = []
    with unittest_mock.patch.object(
            pipeline.subprocess, "run", lambda *a, **k: calls.append((a, k))):
        try:
            pipeline._run_trace(
                "/not/executed/ycsb_silo.exe", not_directory, {}, 1800
            )
            assert False, "directory でない trace_dir を拒否すべき"
        except pipeline._TraceDirUnavailable as exc:
            assert exc.path == not_directory
            assert exc.reason == "not-directory"
    assert calls == []


def test_pipeline_no_bench_commits_without_fitness():
    """配線モード (do_bench=False): certified なら bench せず commit (fitness None)。"""
    lay = _tmp_layout()
    r, calls = _eval(lay, certified=True, do_bench=False)
    assert r.certified and r.fitness_tps is None
    assert len(calls) == 0
    assert wal.replay(lay)[r.variant].committed


def test_pipeline_trace_nonzero_exit_aborts():
    """規律2: trace バイナリが異常終了したら certified にせず abort (部分トレース防御)。"""
    lay = _tmp_layout()
    r, calls = _eval(lay, rc=139)                 # segfault 相当
    assert r.aborted and not r.certified and len(calls) == 0
    st = wal.replay(lay)[r.variant]
    assert STAGE_VERIFY_DONE not in st.stages_seen   # verify に渡さず手前で reject
    assert STAGE_COMMIT not in st.stages_seen


def test_pipeline_empty_trace_aborts_before_verify():
    """規律2: 空トレース (commit 0) は verify に渡すと serializable に化ける → 手前で reject。"""
    lay = _tmp_layout()
    r, calls = _eval(lay, ncommit=0)
    assert r.aborted and not r.certified and len(calls) == 0
    st = wal.replay(lay)[r.variant]
    assert STAGE_VERIFY_DONE not in st.stages_seen
    assert STAGE_COMMIT not in st.stages_seen


def test_pipeline_trace_timeout_abort_records_timeout_s():
    """S4 consumer (規律3): trace-timeout の abort payload に timeout_s が載る。
    liveness-red の次手入力 — どの上限で打ち切られたかを WAL に残す
    (旧配線は extra ゼロで、timeout の中身が consumer に届かなかった)。"""
    lay = _tmp_layout()
    r, calls = _eval(lay, trace_timeout=True)
    assert r.aborted and not r.certified and len(calls) == 0
    st = wal.replay(lay)[r.variant]
    assert st.last_terminal.payload.get("reason") == "trace-timeout"
    assert st.last_terminal.payload.get("timeout_s") == pipeline.TRACE_TIMEOUT_S


def test_pipeline_empty_trace_abort_records_aborts():
    """S4 consumer (規律3): trace-empty の abort payload に aborts が載り、「回っているが
    全 abort (commit 枯渇)」と「そもそも回っていない」を WAL から区別できる (sort 変異の
    主要失敗形態の分離)。aborts=None も欠落でなく null で残す (計器未確定の可視化)。"""
    lay = _tmp_layout()
    r, _ = _eval(lay, ncommit=0, aborts=31337)
    p = wal.replay(lay)[r.variant].last_terminal.payload
    assert p.get("reason") == "trace-empty"
    assert p.get("commits") == 0 and p.get("aborts") == 31337
    lay2 = _tmp_layout()
    r2, _ = _eval(lay2, ncommit=0, aborts=None)
    p2 = wal.replay(lay2)[r2.variant].last_terminal.payload
    assert p2.get("reason") == "trace-empty"
    assert "aborts" in p2 and p2["aborts"] is None


def test_pipeline_bench_no_throughput_aborts():
    """A: bench が throughput を 1 つも出さないなら fitness 無しの COMMIT を書かず abort。

    正しさゲートは通過済み (certified) だが測定不能 → 不採用 (aborted)。両立する状態。"""
    lay = _tmp_layout()
    r, calls = _eval(lay, certified=True, median=None)
    assert r.aborted and r.fitness_tps is None   # 測定不能で不採用 (fitness 無し)
    assert len(calls) == 1                       # bench は走った (が throughput 取れず)
    st = wal.replay(lay)[r.variant]
    assert st.aborted and not st.committed
    assert STAGE_VERIFY_DONE in st.stages_seen   # 正しさゲートは通過している
    assert STAGE_COMMIT not in st.stages_seen
    assert isinstance(st.last_terminal.payload.get("bench_wall_s"), float)
    assert st.last_terminal.payload["bench_wall_s"] >= 0.0


def test_pipeline_bench_cv_undefined_aborts():
    """有効 rep 不足 (1 点のみ) 等で CV が定義できない測定は fitness として採用しない
    (規律4: within-run 品質ゲートを通せない測定を通さない)。旧実装は素通りし
    bench_done 後の log f-string (nf.cv*100) で TypeError → 意図しない eval-exception
    abort として permanent skip になっていた (洗練検査 2026-07-02 MED)。"""
    lay = _tmp_layout()
    r, calls = _eval(lay, certified=True, cv=None)
    assert r.aborted and r.fitness_tps is None
    assert len(calls) == 1                       # bench は走った (が CV 不定)
    st = wal.replay(lay)[r.variant]
    assert st.aborted and not st.committed
    assert st.last_terminal.payload.get("reason") == "bench-cv-undefined"  # 明示 admission
    assert STAGE_COMMIT not in st.stages_seen


def test_pipeline_competing_tenant_aborts_without_bench():
    """規律4 (admission fails-closed): bench 直前に競合ベンチを検知したら計測せず abort。

    certified は通過済みでも、汚染しうる環境では fitness を採らない (孤児 livelock 再発防止)。"""
    lay = _tmp_layout()
    r, calls = _eval(lay, certified=True,
                     competing=["999 /x/build-variants/silo_y/cc/silo/ycsb_silo.exe -t=48"])
    assert r.aborted and r.fitness_tps is None
    assert len(calls) == 0                       # 競合検知で実 bench を走らせない (汚染回避)
    st = wal.replay(lay)[r.variant]
    assert st.aborted and not st.committed
    assert STAGE_VERIFY_DONE in st.stages_seen   # 正しさゲートは通過 (abort は計測側の理由)
    assert STAGE_COMMIT not in st.stages_seen
    assert st.last_terminal.payload.get("bench_wall_s") == 0.0


def test_pipeline_unstable_commits_but_flags_for_exclusion():
    """§3.6(2): 規定ラウンドでも CV が収束しない測定は reject しない (正しさは通過済み) が、
    unstable フラグを EvalResult と WAL に立てる。採否の分布比較から呼び手が除外できるように
    する (沈黙して 1 点を採用しない)。"""
    lay = _tmp_layout()
    r, calls = _eval(lay, certified=True, unstable=True)
    assert r.certified and not r.aborted
    assert r.fitness_tps == 12345.0 and r.unstable is True
    st = wal.replay(lay)[r.variant]
    assert st.committed and STAGE_COMMIT in st.stages_seen   # 不採用ではない
    commit = [rec for rec in wal.read_records(lay)
              if rec.variant == r.variant and rec.stage == STAGE_COMMIT]
    assert commit and commit[-1].payload.get("unstable") is True


def test_pipeline_screen_reject_skips_verify_and_never_commits():
    lay = _tmp_layout()
    r, calls = _eval(lay, screening=_screening(), median=8499.0)
    assert r.aborted and not r.certified and r.fitness_tps is None
    assert len(calls) == 1 and len(calls.trace) == 0
    records = list(wal.read_records(lay))
    assert STAGE_VERIFY_DONE not in {rec.stage for rec in records}
    assert STAGE_COMMIT not in {rec.stage for rec in records}
    bench = [rec for rec in records if rec.stage == STAGE_BENCH_DONE][-1]
    assert bench.payload.get("screening") is True
    abort = [rec for rec in records if rec.stage == STAGE_ABORT][-1]
    assert abort.payload["reason"] == pipeline.SCREEN_REJECTION_REASON
    assert "verify" not in abort.payload
    assert abort.payload["screen"] == {
        "median_tps": 8499.0, "cv": 0.01, "baseline_tps": 10000.0,
        "baseline_ref": "stock-v1", "floor": 0.10, "k": 1.5,
        "margin": -0.1501}


def test_pipeline_stale_screening_falls_back_to_verify_first_and_records_trace():
    lay = _tmp_layout()
    now = time.time()
    screening = _screening(baseline_measured_at=now - 31 * 60)
    r, calls = _eval(
        lay,
        screening=screening,
        median=8000.0,
    )
    assert r.certified and not r.aborted
    assert calls.events == ["verify", "bench"]
    stale_notes = [note for note in r.notes if "stale-baseline" in note]
    assert len(stale_notes) == 1
    note_match = re.fullmatch(
        r"stale-baseline: baseline age (?P<age_s>\d+\.\d{3})s "
        r"exceeds reanchor threshold (?P<threshold_s>\d+\.\d{3})s; "
        r"screening disabled",
        stale_notes[0],
    )
    assert note_match is not None
    assert float(note_match.group("age_s")) >= 1860.0
    assert (
        float(note_match.group("threshold_s"))
        == screening.reanchor_threshold_s
    )
    records = list(wal.read_records(lay))
    bench = [rec for rec in records if rec.stage == STAGE_BENCH_DONE][-1]
    disabled = bench.payload["screening_disabled"]
    assert disabled["reason"] == "stale-baseline"
    assert disabled["age_s"] >= 31 * 60
    assert disabled["threshold_s"] == 1800.0
    commit = [rec for rec in records if rec.stage == STAGE_COMMIT][-1]
    assert "screened" not in commit.payload


def test_pipeline_fresh_screening_remains_active():
    lay = _tmp_layout()
    r, calls = _eval(
        lay,
        screening=_screening(baseline_measured_at=time.time() - 29 * 60),
        median=8000.0,
    )
    assert r.aborted and not r.certified
    assert calls.events == ["bench"]
    records = list(wal.read_records(lay))
    bench = [rec for rec in records if rec.stage == STAGE_BENCH_DONE][-1]
    assert bench.payload["screening"] is True
    assert "screening_disabled" not in bench.payload


def test_pipeline_screening_verify_red_keeps_existing_structured_abort():
    lay = _tmp_layout()
    r, calls = _eval(lay, screening=_screening(), median=9000.0,
                     certified=False)
    assert r.aborted and not r.certified and r.fitness_tps is None
    assert len(calls) == 1 and len(calls.trace) == 1
    records = list(wal.read_records(lay))
    assert STAGE_COMMIT not in {rec.stage for rec in records}
    abort = [rec for rec in records if rec.stage == STAGE_ABORT][-1]
    assert abort.payload["reason"] == "non-serializable"
    assert abort.payload["verify"]["anomalies"][0]["phenomenon"] == "G2"


def test_pipeline_screening_keeps_existing_bench_failure_reasons():
    cases = [
        ({"median": None}, "bench-no-throughput"),
        ({"median": 9000.0, "cv": None}, "bench-cv-undefined"),
    ]
    for mock_kw, reason in cases:
        lay = _tmp_layout()
        r, calls = _eval(lay, screening=_screening(), **mock_kw)
        assert r.aborted and not r.certified and r.fitness_tps is None
        assert len(calls) == 1 and len(calls.trace) == 0
        terminal = wal.replay(
            lay, admission_policy=_BUILD_CONTEXT.policy,
        )[r.variant].last_terminal
        assert terminal.stage == STAGE_ABORT and terminal.payload["reason"] == reason


def test_pipeline_screening_boundary_and_fails_safe_matrix():
    # threshold = 10000 * (1 - 1.5 * 0.10) = 8500。等号・曖昧点は verify 側。
    cases = [
        ("below-k-floor", 8499.0, 0.03, False, True),
        ("equal-k-floor", 8500.0, 0.03, False, False),
        ("near-floor-band", 8750.0, 0.03, False, False),
        ("floor-boundary", 9000.0, 0.03, False, False),
        ("inside-floor", 9500.0, 0.03, False, False),
        ("faster", 11000.0, 0.03, False, False),
        ("unstable", 8000.0, 0.03, True, False),
        # high-abort は厳密な >。等号は対象外へ逃がさず通常の screening 判定を行う。
        ("high-abort-equal", 8000.0, 0.06, False, True),
        ("high-abort", 8000.0, 0.060001, False, False),
        ("abort-rate-missing", 8000.0, None, False, False),
    ]
    for name, median, abort_rate, unstable, rejected in cases:
        lay = _tmp_layout()
        r, calls = _eval(lay, screening=_screening(), median=median,
                         abort_rate=abort_rate, unstable=unstable)
        records = list(wal.read_records(lay))
        stages = {rec.stage for rec in records}
        assert len(calls) == 1, name               # full bench は常に 1 回だけ
        if rejected:
            assert r.aborted and not r.certified, name
            assert len(calls.trace) == 0 and STAGE_COMMIT not in stages, name
        else:
            assert r.certified and not r.aborted, name
            assert len(calls.trace) == 1 and STAGE_COMMIT in stages, name
            commit = [rec for rec in records if rec.stage == STAGE_COMMIT][-1]
            assert commit.payload["screened"] is True, name
            assert commit.payload["fitness_tps"] == median, name


def test_evaluate_commit_writes_are_syntactically_verify_gated():
    """Prepare capability, sole writer, and both callers form one closed gate."""
    with open(pipeline.__file__, encoding="utf-8") as f:
        tree = ast.parse(f.read(), filename=pipeline.__file__)
    functions = {
        node.name: node for node in tree.body
        if isinstance(node, ast.FunctionDef)
    }
    core = functions["_prepare_evaluation_core"]
    writer = functions["_commit_prepared"]

    prepared_calls = [
        (owner.name, call)
        for owner in functions.values()
        for call in ast.walk(owner)
        if isinstance(call, ast.Call)
        and isinstance(call.func, ast.Name)
        and call.func.id == "_PreparedEvaluation"
    ]
    assert len(prepared_calls) == 1
    assert prepared_calls[0][0] == "_prepare_evaluation_core"

    verify_loops = [
        node for node in ast.walk(core)
        if isinstance(node, ast.For)
        and isinstance(node.iter, ast.Name)
        and node.iter.id == "passes"
    ]
    certified_assignments = [
        node for node in ast.walk(core)
        if isinstance(node, ast.Assign)
        and any(
            isinstance(target, ast.Attribute)
            and isinstance(target.value, ast.Name)
            and target.value.id == "res"
            and target.attr == "certified"
            for target in node.targets
        )
        and isinstance(node.value, ast.Constant)
        and node.value.value is True
    ]
    assert len(verify_loops) == len(certified_assignments) == 1
    prepared_call = prepared_calls[0][1]
    assert verify_loops[0].end_lineno < certified_assignments[0].lineno \
        < prepared_call.lineno

    stage_commit_calls = []
    for owner in functions.values():
        for call in ast.walk(owner):
            if not isinstance(call, ast.Call) or len(call.args) < 3:
                continue
            stage = call.args[2]
            if isinstance(stage, ast.Name) and stage.id == "STAGE_COMMIT":
                stage_commit_calls.append((owner.name, call))
    assert [owner for owner, _call in stage_commit_calls] == [
        "_commit_prepared", "_commit_prepared",
    ]
    assert {
        ast.unparse(call.func) for _owner, call in stage_commit_calls
    } == {
        "wal.log", "prepared.qualification_policy.event_sink.emit",
    }

    guard = [
        node for node in writer.body
        if isinstance(node, ast.If)
        and ast.unparse(node.test) == "not res.certified or res.aborted"
    ]
    assert len(guard) == 1
    assert len(guard[0].body) == 1 and isinstance(guard[0].body[0], ast.Raise)
    assert all(
        guard[0].end_lineno < call.lineno
        for _owner, call in stage_commit_calls
    )

    writer_callers = collections.Counter(
        owner.name
        for owner in functions.values()
        for call in ast.walk(owner)
        if isinstance(call, ast.Call)
        and isinstance(call.func, ast.Name)
        and call.func.id == "_commit_prepared"
    )
    assert writer_callers == {
        "evaluate": 1,
        "_run_balanced_schedule": 1,
    }


def test_pipeline_screening_with_no_bench_is_immediate_value_error():
    lay = _tmp_layout()
    with _mock_pipeline() as calls:
        try:
            pipeline.evaluate(
                Genome("silo", {"BACK_OFF": 1}), lay,
                _AUTH_CONTRACT.env_tag, "deadbeef",
                PerfConfig(records=1000, threads=2), clocks_per_us=1800,
                numactl=_AUTH_CONTRACT.numactl,
                authorization_contract=_AUTHORIZATION,
                do_bench=False, screening=_screening(), log=lambda *a: None, build_context=_BUILD_CONTEXT)
            assert False, "should raise ValueError"
        except ValueError as e:
            assert "screening" in str(e) and "do_bench=False" in str(e)
    assert len(calls) == 0 and len(calls.trace) == 0
    assert list(wal.read_records(lay)) == []


def test_pipeline_rejects_runtime_screening_mixed_into_legacy_campaign():
    """F4監査再現: helper不使用の既存COMMIT campaignへscreeningを後付けできない。"""
    lay = _tmp_layout()
    legacy_cfg = _cfg()
    _write_certified_lock(lay, _bound(legacy_cfg))
    commit_receipts.log_receipted_commit(
        lay, "already-committed", _T530_CONTRACT.env_tag, {
        "fitness_tps": 1.0,
        COMMIT_CONTRACT_SHA256_KEY: _T530_CONTRACT_SHA256,
        },
    )
    before = list(wal.read_records(lay))

    with _mock_pipeline() as calls:
        try:
            pipeline.evaluate(
                Genome("silo", {"BACK_OFF": 1}), lay,
                _AUTH_CONTRACT.env_tag, "deadbeef",
                PerfConfig(records=1000, threads=2), clocks_per_us=1800,
                numactl=_AUTH_CONTRACT.numactl,
                authorization_contract=_AUTHORIZATION,
                screening=_screening(), log=lambda *a: None, build_context=_BUILD_CONTEXT)
            assert False, "legacy campaign への runtime screening 混在は拒否すべき"
        except ValueError as exc:
            assert "campaign.lock" in str(exc) and "screening" in str(exc)
    assert calls.events == [] and calls.trace == []
    assert list(wal.read_records(lay)) == before


def test_pipeline_rejects_screening_policy_drift_from_campaign_lock():
    for changed in ({"baseline_ref": "other"}, {"floor": 0.11}, {"k": 1.6}):
        lay = _tmp_layout()
        locked = _screening()
        cfg = _cfg(search_config={**_cfg().search_config,
                                  **ident.screening_search_config(locked)})
        _write_certified_lock(lay, _bound(cfg))
        runtime = _screening(**changed)
        with _mock_pipeline() as calls:
            try:
                pipeline.evaluate(
                    Genome("silo", {"BACK_OFF": 1}), lay,
                    _AUTH_CONTRACT.env_tag, "deadbeef",
                    PerfConfig(records=1000, threads=2), clocks_per_us=1800,
                    numactl=_AUTH_CONTRACT.numactl,
                    authorization_contract=_AUTHORIZATION,
                    screening=runtime, log=lambda *a: None, build_context=_BUILD_CONTEXT)
                assert False, f"screening policy drift {changed} must be rejected"
            except ValueError as exc:
                assert "不一致" in str(exc)
        assert calls.events == [] and list(wal.read_records(lay)) == []


def test_pipeline_build_error_aborts():
    """overnight 耐性: ビルド失敗はこの variant 固有の失敗として abort 隔離する。"""
    lay = _tmp_layout()
    r, calls = _eval(lay, build_raises=True)
    assert r.aborted and not r.certified and len(calls) == 0
    st = wal.replay(lay)[r.variant]
    assert st.aborted and STAGE_BUILD_DONE not in st.stages_seen


def test_pipeline_build_error_payload_carries_exception_summary():
    """D50 教訓の診断改善: build-error の abort payload に例外要約 ("error" キー) を載せる。
    reason だけの WAL では失敗原因を帰属できず、kill 残骸毒の調査が build dir の実地検分
    まで遅延した (worklog 2026-07-11 (5))。"""
    lay = _tmp_layout()
    r, _ = _eval(lay, build_raises=True)
    aborts = [rec for rec in wal.read_records(lay)
              if rec.variant == r.variant and rec.stage == STAGE_ABORT]
    assert aborts and aborts[-1].payload.get("reason") == "build-error"
    err = aborts[-1].payload.get("error", "")
    assert "RuntimeError" in err and "build boom" in err


def test_exc_summary_truncates_tail_biased():
    """_exc_summary: 長い例外 (ビルドログ等) は本命が末尾に出やすいので末尾優先で畳む。
    短い例外は型名付きでそのまま返す。"""
    short = pipeline._exc_summary(RuntimeError("g++ 不在"))
    assert short == "RuntimeError: g++ 不在"
    long_e = RuntimeError("HEAD" + "x" * 5000 + "error: 本命はここTAIL")
    s = pipeline._exc_summary(long_e)
    assert s.startswith("RuntimeError: HEAD")
    assert s.endswith("error: 本命はここTAIL")
    assert len(s) < 1100                       # limit=1000 + 省略マーカ分で頭打ち


def test_pipeline_self_compute_identity_error_aborts_under_stock_id():
    """直接 caller (src_token=None) で source_digest.resolve が確定不能なら stock id で abort
    (fails-closed, 規律2)。loop は src_token を渡すので通らないが、直接 caller 用の防壁を回帰する
    (D24: loop の identity-error 経路と構造対称な pipeline 側の枝)。"""
    lay = _tmp_layout()
    g = Genome("silo", {"BACK_OFF": 1})
    saved = pipeline.source_digest
    pipeline.source_digest = _sd_mock(RuntimeError("g++ 不在"))
    try:
        r = pipeline.evaluate(g, lay, _AUTH_CONTRACT.env_tag, "deadbeef",
                              PerfConfig(records=1000, threads=2),
                              clocks_per_us=_AUTH_CONTRACT.clocks_per_us,
                              numactl=list(_AUTH_CONTRACT.numactl),
                              authorization_contract=_AUTHORIZATION,
                              do_bench=False, log=lambda *a: None, build_context=_BUILD_CONTEXT)
    finally:
        pipeline.source_digest = saved
    assert r.aborted and not r.certified
    assert r.variant == pipeline.variant_id(g)        # identity 不明 → stock id (canonical のみ)
    assert wal.replay(lay)[r.variant].aborted


# ===== STAGE2: S2 verify 2 本立て pipeline 配線 (D36 決定4、段5) =====

@contextlib.contextmanager
def _mock_pipeline_multipass(pass_results, median=12345.0, cv=0.01, competing=None,
                             probe_raises=None):
    """verify pass を呼び出し順に異なる結果で返す mock (_mock_pipeline は全 pass
    共通の固定戻り値しか表現できないため、S2 (2 パス目以降) 専用に用意する)。

    pass_results = [(ncommit, rc, aborts, certified), ...] — _run_trace/
    verify_trace_dir が呼ばれた順に 1 要素ずつ消費する。yield する dict:
      trace  = 各 _run_trace 呼び出しの {"flags":..., "numactl":...} 記録
      bench = 各 measure_point 呼び出しの numactl・rep return code 分岐記録
      bench_lock_enters = bench_lock() で入った回数 (verify pass 分 + bench 分)
    """
    saved = {}

    def patch(name, val):
        saved[name] = getattr(pipeline, name)
        setattr(pipeline, name, val)

    calls = {"trace": [], "bench": [], "bench_lock_enters": 0}

    @contextlib.contextmanager
    def fake_lock(*a, **k):
        calls["bench_lock_enters"] += 1
        yield

    idx_trace = {"i": 0}

    def fake_run_trace(binary, tdir, flags, clocks_per_us, timeout_s=None, numactl=None):
        i = idx_trace["i"]
        idx_trace["i"] += 1
        calls["trace"].append({"flags": dict(flags), "numactl": numactl})
        ncommit, rc, aborts, _ = pass_results[i]
        return pipeline._TraceRunResult(
            trace_c_lines=ncommit,
            returncode=rc,
            abort_counts=aborts,
            commit_count_witness=ncommit,
            batch_commit_count_witness=0,
        )

    idx_verify = {"i": 0}

    real_verify_trace_dir_with_capability = (
        pipeline.verify_trace_dir_with_capability
    )

    def fake_verify(tdir, *, expected_commits=None, **receipt_binding):
        i = idx_verify["i"]
        idx_verify["i"] += 1
        ncommit, _, _, certified = pass_results[i]
        assert expected_commits == ncommit
        fixture = "g1_serial" if certified else "r1_write_skew"
        return real_verify_trace_dir_with_capability(
            os.path.join(_HERE, "fixtures", fixture),
            **receipt_binding,
        )

    def fake_build(genome, commit, trace, src_token=None, ccbench_dir="", cache_root="",
                   *, admission, build_context, source_evidence):
        assert build_context is _BUILD_CONTEXT
        assert admission.as_wal_receipt()["source"] == source_evidence.as_receipt()
        bin_sha256 = ("da" if trace else "db") * 32  # 64 hex (WAL 新キー用)
        return types.SimpleNamespace(bin_hash=bin_sha256[:16], bin_sha256=bin_sha256,
                                     binary="/nonexistent/ycsb.exe", cached=False,
                                     configure_cmd="<cfg>", build_cmd="<build>")

    def fake_measure(*a, **k):
        calls["bench"].append({
            "numactl": k.get("numactl"),
            "record_rep_returncodes": "rep_returncodes" in k,
        })
        return types.SimpleNamespace(
            throughputs=[median, median], run_cmd="<run>",
            leading_indicators=lambda: {"throughput_tps": median, "abort_rate": 0.0,
                                        "latency_ns": 1.0, "llc_miss_rate": 0.0, "ipc": 1.0})

    def fake_remeasure(measure_fn, settle_fn=None, **k):
        pt = measure_fn()
        nf = types.SimpleNamespace(median=median, cv=cv, high_variance=False)
        return types.SimpleNamespace(point=pt, nf=nf, rounds=1, stable=True,
                                     unstable=False, cv_history=[cv])

    patch("buildcache", types.SimpleNamespace(
        build=fake_build, is_full_sha256=buildcache.is_full_sha256,
        DEFAULT_CXX=buildcache.DEFAULT_CXX,
        compilers_for_current_site=lambda: (
            buildcache.DEFAULT_CC, buildcache.DEFAULT_CXX,
        )))
    patch(
        "_compilers_for_current_site",
        lambda: (buildcache.DEFAULT_CC, buildcache.DEFAULT_CXX),
    )
    patch("_resolve_site", lambda _site=None: site_policy.PEGASUS_COMPUTE)
    patch("source_digest", types.SimpleNamespace(
        STOCK="stock", assert_worktree_within_allowlist=lambda *a, **k: None,
        resolve_evidence=lambda genome_value, commit, **kwargs: _source_evidence(
            genome_value, commit,
            source_root=(
                kwargs.get("ccbench_dir")
                or str(commit_receipts.proof_source_root())
            ),
        )))
    patch("_run_trace", fake_run_trace)
    patch("verify_trace_dir_with_capability", fake_verify)
    patch("bench_lock", fake_lock)
    patch("settle", lambda *a, **k: {"settled": True})

    def fake_competing():
        if probe_raises is not None:
            raise probe_raises
        return list(competing or [])
    patch("competing_bench_pids", fake_competing)
    patch("measure_point", fake_measure)
    patch("remeasure_until_stable", fake_remeasure)
    try:
        yield calls
    finally:
        for k, val in saved.items():
            setattr(pipeline, k, val)


def test_pipeline_extra_correctness_both_pass_tags_commit_and_uses_numactl_lock():
    """D36 決定4: legacy (既定) + S2 (extra_correctness) を順に通し、両方 certified
    なら STAGE_COMMIT.verify_configs に両タグが並ぶ。S2 パスだけ numactl + bench_lock
    (決定4-4) を使い、legacy パスは従来どおり並列可 (numactl 無し)。"""
    lay = _tmp_layout()
    _write_certified_lock(lay, _bound(_cfg()))
    numa = ["numactl", "--interleave=all"]
    with _mock_pipeline_multipass([(100, 0, 5, True), (900000, 0, 50000, True)]) as calls:
        r = pipeline.evaluate(
            Genome("silo", {"BACK_OFF": 1}), lay, _AUTH_CONTRACT.env_tag, "deadbeef",
            PerfConfig(records=1000, threads=2), clocks_per_us=1800, numactl=numa,
            authorization_contract=_AUTHORIZATION,
            extra_correctness=[(pipeline.S2_TAG, pipeline.s2_correctness_workload())],
            log=lambda *a: None, build_context=_BUILD_CONTEXT)
    assert r.certified and not r.aborted
    assert calls["trace"][0]["numactl"] is None           # legacy パス: numactl 無し
    assert calls["trace"][1]["numactl"] == tuple(numa)     # S2 パス: immutable prefix
    assert calls["bench_lock_enters"] == 2                 # S2 verify パス 1 + bench 1
    verify_recs = [rec for rec in wal.read_records(lay) if rec.stage == STAGE_VERIFY_DONE]
    assert [rec.payload["workload"]["tag"] for rec in verify_recs] == ["legacy", "s2"]
    commit = [rec for rec in wal.read_records(lay) if rec.stage == STAGE_COMMIT][-1]
    assert commit.payload.get("verify_configs") == ["legacy", "s2"]


def test_pipeline_extra_correctness_second_pass_red_aborts_with_workload_tag():
    """legacy は緑、S2 (2 パス目) が赤 → 即 abort。abort payload に workload タグ
    (D36 決定4-3) が載り、次手生成がどの構成で壊れたか帰属できる。legacy・S2 両方の
    STAGE_VERIFY_DONE が残る (verify_done は certified 判定前に書く既存仕様、S2 は
    verify まで到達して赤判定された = trace-empty 等の手前 reject とは異なる)。"""
    lay = _tmp_layout()
    with _mock_pipeline_multipass([(100, 0, 5, True), (900000, 0, 50000, False)]):
        r = pipeline.evaluate(
            Genome("silo", {"BACK_OFF": 1}), lay, _AUTH_CONTRACT.env_tag, "deadbeef",
            PerfConfig(records=1000, threads=2), clocks_per_us=1800,
            numactl=["numactl", "--interleave=all"],
            authorization_contract=_AUTHORIZATION,
            extra_correctness=[(pipeline.S2_TAG, pipeline.s2_correctness_workload())],
            do_bench=False, log=lambda *a: None, build_context=_BUILD_CONTEXT)
    assert r.aborted and not r.certified
    assert r.verdict == "non-serializable"        # 前パス (legacy) の verdict を持ち越さない
    abort = [rec for rec in wal.read_records(lay) if rec.stage == STAGE_ABORT][-1]
    assert abort.payload.get("workload") == {"tag": "s2"}
    assert abort.payload.get("verify", {}).get("verdict") == "non-serializable"
    verify_recs = [rec for rec in wal.read_records(lay) if rec.stage == STAGE_VERIFY_DONE]
    assert [rec.payload["workload"]["tag"] for rec in verify_recs] == ["legacy", "s2"]
    assert verify_recs[0].payload["certified"] is True
    assert verify_recs[1].payload["certified"] is False
    assert STAGE_COMMIT not in {rec.stage for rec in wal.read_records(lay)}


def test_pipeline_no_extra_correctness_matches_legacy_only_behavior():
    """回帰確認: extra_correctness 未指定 (既定) は legacy 1 パスのみ、bench_lock は
    verify 中に一切入らない (do_bench=False で bench 分もゼロ) — 既存 campaign の
    挙動を変えない (S2 は opt-in)。"""
    lay = _tmp_layout()
    _write_certified_lock(lay, _bound(_cfg()))
    with _mock_pipeline_multipass([(100, 0, 5, True)]) as calls:
        r = pipeline.evaluate(
            Genome("silo", {"BACK_OFF": 1}), lay, _AUTH_CONTRACT.env_tag, "deadbeef",
            PerfConfig(records=1000, threads=2), clocks_per_us=1800,
            numactl=_AUTH_CONTRACT.numactl,
            authorization_contract=_AUTHORIZATION,
            do_bench=False, log=lambda *a: None, build_context=_BUILD_CONTEXT)
    assert r.certified and calls["bench_lock_enters"] == 0
    verify_recs = [rec for rec in wal.read_records(lay) if rec.stage == STAGE_VERIFY_DONE]
    assert len(verify_recs) == 1 and verify_recs[0].payload["workload"]["tag"] == "legacy"
    commit = [rec for rec in wal.read_records(lay) if rec.stage == STAGE_COMMIT][-1]
    assert commit.payload.get("verify_configs") == ["legacy"]


def test_pipeline_fullscale_verify_and_bench_share_numactl_expression():
    """Split prepare/carrier/bench topology shares one immutable numactl value."""
    with open(pipeline.__file__, encoding="utf-8") as stream:
        tree = ast.parse(stream.read(), filename=pipeline.__file__)
    functions = {
        node.name: node for node in tree.body if isinstance(node, ast.FunctionDef)
    }
    assert {
        "_prepare_evaluation_core", "_bench_prepared",
    } <= set(functions)
    prepare = functions["_prepare_evaluation_core"]
    bench = functions["_bench_prepared"]
    fullscale_ifs = [
        node for node in ast.walk(prepare)
        if isinstance(node, ast.If)
        and isinstance(node.test, ast.Name)
        and node.test.id == "fullscale_isolated"
    ]
    assert len(fullscale_ifs) == 1, (
        "evaluate 内の exact Name('fullscale_isolated') 条件を持つ If を "
        f"1 件探したが {len(fullscale_ifs)} 件だった"
    )
    fullscale_if = fullscale_ifs[0]
    verify_calls = [
        call
        for statement in fullscale_if.body
        for call in ast.walk(statement)
        if isinstance(call, ast.Call)
        and isinstance(call.func, ast.Name)
        and call.func.id == "_run_one_pass"
    ]
    bench_calls = [
        node for node in ast.walk(bench)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id == "_run_bench"
    ]
    carriers = [
        node for node in ast.walk(prepare)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id == "_PreparedEvaluation"
    ]
    assert len(verify_calls) == 1, (
        "fullscale_isolated If 内の _run_one_pass 呼出を exact 1 件要求する"
    )
    assert len(carriers) == 1, "prepared carrier must be constructed exactly once"
    assert len(bench_calls) == 1, "split bench must call _run_bench exactly once"
    carrier_keywords = {item.arg: item.value for item in carriers[0].keywords}
    prefixes = (
        verify_calls[0].args[2],
        carrier_keywords["numactl"],
        bench_calls[0].args[3],
    )
    assert ast.unparse(prefixes[0]) == "numactl"
    assert ast.unparse(prefixes[1]) == "numactl"
    assert ast.unparse(prefixes[2]) == "prepared.numactl"


def test_pipeline_fullscale_verify_and_bench_share_immutable_numactl():
    """bench 2 経路と rep return code 2 分岐へ同じ immutable prefix を渡す。"""
    for use_screening in (False, True):
        for record_rep_returncodes in (False, True):
            lay = _tmp_layout()
            screening = _screening() if use_screening else None
            if screening is not None:
                locked_cfg = _cfg(search_config={
                    **_cfg().search_config,
                    **ident.screening_search_config(screening),
                })
                _write_certified_lock(lay, locked_cfg)
            else:
                _write_certified_lock(lay, _bound(_cfg()))
            supplied = list(_AUTH_CONTRACT.numactl)
            with _mock_pipeline_multipass(
                    [(100, 0, 5, True), (900000, 0, 50000, True)]) as calls:
                result = pipeline.evaluate(
                    Genome("silo", {"BACK_OFF": 1}), lay,
                    _AUTH_CONTRACT.env_tag, "deadbeef",
                    PerfConfig(records=1000, threads=2), clocks_per_us=1800,
                    numactl=supplied, authorization_contract=_AUTHORIZATION,
                    extra_correctness=[
                        (pipeline.S2_TAG, pipeline.s2_correctness_workload())
                    ],
                    screening=screening,
                    record_rep_returncodes=record_rep_returncodes,
                    log=lambda *a: None, build_context=_BUILD_CONTEXT)
            assert result.certified and not result.aborted
            assert len(calls["trace"]) == 2 and len(calls["bench"]) == 1
            verify_prefix = calls["trace"][1]["numactl"]
            bench_call = calls["bench"][0]
            bench_prefix = bench_call["numactl"]
            assert bench_call["record_rep_returncodes"] is record_rep_returncodes
            assert type(verify_prefix) is tuple
            assert verify_prefix == _AUTH_CONTRACT.numactl
            assert bench_prefix is verify_prefix


def test_pipeline_extra_correctness_normalizes_empty_list_numactl():
    """Pegasus の空 list は immutable な空 prefix として S2 trace に届く。"""
    authorization = ec.authorize("pegasus")
    contract = ec.lookup("pegasus")
    lay = _tmp_layout()
    _write_certified_lock(lay, _bound(_cfg()))
    with _mock_pipeline_multipass(
            [(100, 0, 5, True), (900000, 0, 50000, True)]) as calls:
        result = pipeline.evaluate(
            Genome("silo", {"BACK_OFF": 1}), lay,
            contract.env_tag, "deadbeef",
            PerfConfig(records=1000, threads=2),
            clocks_per_us=contract.clocks_per_us,
            numactl=[], env_contract=None,
            authorization_contract=authorization,
            extra_correctness=[
                (pipeline.S2_TAG, pipeline.s2_correctness_workload())
            ],
            do_bench=False, log=lambda *a: None,
            build_context=_BUILD_CONTEXT)
    assert result.certified and not result.aborted
    trace_prefix = calls["trace"][1]["numactl"]
    assert type(trace_prefix) is tuple
    assert trace_prefix == ()


def test_pipeline_qualification_rejects_list_numactl_before_sink_writes():
    """qualification は正規化前の list を exact tuple 不一致として拒否する。"""
    from orchestrator.qualification.artifacts import (
        QualificationEventSink,
        QualificationRoot,
        create_attempt,
    )

    contract = ec.lookup("pegasus")
    root = QualificationRoot(Path(_tmpdir("izanagi_qualification_numactl_")))
    capability = root.issue()
    layout = create_attempt(
        root, capability, series_id="a" * 64, attempt_id="b" * 64,
    )
    sink = QualificationEventSink(
        capability, layout, round_index=1, role="subject",
        source_lock_identity_sha256="e" * 64,
    )
    policy = pipeline.QualificationPipelinePolicy.t126_pegasus(sink)
    sink_path = (
        layout.attempt_dir
        / "rounds/0001/subject/evaluation-events.jsonl"
    )

    with _assert_raises_contains(
            ValueError,
            "qualification execution values do not exactly match Pegasus contract"):
        pipeline.evaluate(
            Genome("silo", {"BACK_OFF": 1}), layout,
            contract.env_tag, "deadbeef",
            PerfConfig(
                records=1_000_000, threads=48,
                workload={
                    "ycsb_zipf_skew": "0.9", "ycsb_rratio": "95",
                    "ycsb_rmw": "0", "ycsb_max_ope": "10",
                },
            ),
            clocks_per_us=contract.clocks_per_us,
            numactl=[], env_contract=contract,
            authorization_contract=ec.authorize("pegasus"),
            extra_correctness=[
                (pipeline.S2_TAG, pipeline.s2_correctness_workload())
            ],
            bench_max_rounds=1, record_rep_returncodes=True,
            qualification_policy=policy, log=lambda *a: None,
            build_context=_BUILD_CONTEXT)
    assert not sink_path.exists()


def _qualification_perf_case():
    from orchestrator.qualification.artifacts import (
        QualificationEventSink,
        QualificationRoot,
        create_attempt,
    )

    contract = ec.lookup("pegasus")
    root = QualificationRoot(Path(_tmpdir("izanagi_qualification_perf_")))
    capability = root.issue()
    layout = create_attempt(
        root, capability, series_id="a" * 64, attempt_id="b" * 64,
    )
    sink = QualificationEventSink(
        capability, layout, round_index=1, role="subject",
        source_lock_identity_sha256="e" * 64,
    )

    def perf_missing(*_args, **_kwargs):
        raise FileNotFoundError("fixture perf not found")

    receipt = perf_preflight_module.probe_perf_availability(
        perf_candidates=(), subprocess_runner=perf_missing,
    )
    policy = pipeline.QualificationPipelinePolicy.t126_pegasus(sink)
    return contract, layout, policy, receipt


def _qualification_perf_config(**overrides):
    values = {
        "records": 1_000_000,
        "threads": 48,
        "workload": {
            "ycsb_zipf_skew": "0.9", "ycsb_rratio": "95",
            "ycsb_rmw": "0", "ycsb_max_ope": "10",
        },
        "extime": 3,
        "reps": 5,
    }
    values.update(overrides)
    return PerfConfig(**values)


def test_pipeline_qualification_accepts_canonical_no_perf_shape():
    contract, layout, policy, receipt = _qualification_perf_case()
    with _mock_pipeline(certified=True) as calls:
        result = pipeline.evaluate(
            Genome("silo", {"BACK_OFF": 1}), layout,
            contract.env_tag, "deadbeef", _qualification_perf_config(),
            clocks_per_us=contract.clocks_per_us,
            numactl=contract.numactl, env_contract=contract,
            authorization_contract=ec.authorize("pegasus"),
            extra_correctness=[
                (pipeline.S2_TAG, pipeline.s2_correctness_workload())
            ],
            bench_max_rounds=1, record_rep_returncodes=True,
            qualification_policy=policy, use_perf=False,
            perf_preflight_receipt=receipt,
            log=lambda *_args: None, build_context=_BUILD_CONTEXT,
        )

    assert result.certified and not result.aborted
    assert calls.measure_kwargs
    assert calls.measure_kwargs[0]["use_perf"] is False


@pytest.mark.parametrize(
    "mutation",
    (
        "records", "threads", "workload", "extime", "reps", "correctness",
        "extra_correctness", "do_bench", "do_settle", "screening",
        "bench_max_rounds", "record_rep_returncodes",
    ),
)
def test_pipeline_qualification_keeps_every_non_perf_shape_predicate(mutation):
    """M15: use_perf 以外の qualification shape 条件は全て残す。"""
    contract, layout, policy, receipt = _qualification_perf_case()
    perf_overrides = {}
    kwargs = {
        "correctness": None,
        "extra_correctness": [
            (pipeline.S2_TAG, pipeline.s2_correctness_workload())
        ],
        "do_bench": True,
        "do_settle": True,
        "screening": None,
        "bench_max_rounds": 1,
        "record_rep_returncodes": True,
    }
    if mutation in {"records", "threads", "extime", "reps"}:
        perf_overrides[mutation] = {
            "records": 999_999,
            "threads": 47,
            "extime": 2,
            "reps": 4,
        }[mutation]
    elif mutation == "workload":
        perf_overrides["workload"] = {
            "ycsb_zipf_skew": "0.8", "ycsb_rratio": "95",
            "ycsb_rmw": "0", "ycsb_max_ope": "10",
        }
    elif mutation == "correctness":
        kwargs[mutation] = pipeline.s2_correctness_workload()
    elif mutation == "extra_correctness":
        kwargs[mutation] = []
    elif mutation == "screening":
        kwargs[mutation] = _screening()
    elif mutation in {"do_bench", "do_settle", "record_rep_returncodes"}:
        kwargs[mutation] = False
    else:
        kwargs[mutation] = 2

    with pytest.raises(
        ValueError,
        match=r"^qualification opt-in evaluation shape mismatch$",
    ):
        pipeline.evaluate(
            Genome("silo", {"BACK_OFF": 1}), layout,
            contract.env_tag, "deadbeef",
            _qualification_perf_config(**perf_overrides),
            clocks_per_us=contract.clocks_per_us,
            numactl=contract.numactl, env_contract=contract,
            authorization_contract=ec.authorize("pegasus"),
            qualification_policy=policy, use_perf=False,
            perf_preflight_receipt=receipt,
            log=lambda *_args: None, build_context=_BUILD_CONTEXT,
            **kwargs,
        )


def test_pipeline_use_perf_false_without_receipt_keeps_specific_rejection():
    """M-C1: None receipt と use_perf=False の専用拒否点を残す。"""
    lay = _tmp_layout()
    with pytest.raises(ValueError) as caught:
        pipeline.evaluate(
            Genome("silo", {"BACK_OFF": 1}), lay,
            _AUTH_CONTRACT.env_tag, "deadbeef",
            PerfConfig(records=1000, threads=2), clocks_per_us=1800,
            numactl=_AUTH_CONTRACT.numactl,
            authorization_contract=_AUTHORIZATION,
            do_bench=False, use_perf=False,
            log=lambda *_args: None, build_context=_BUILD_CONTEXT,
        )
    assert str(caught.value) == "use_perf=False には perf preflight receipt が必要"
    assert list(wal.read_records(lay)) == []


def test_pipeline_extra_correctness_allows_empty_prefix_when_contract_is_empty():
    """T-1174: Pegasus の bench 契約も verify prefix も空なら S2 を実行できる。

    prefix の非空性を要求する旧 gate への回帰を防ぎ、legacy + S2 の両 pass が実際に
    certified まで到達することを固定する。
    """
    authorization = ec.authorize("pegasus")
    contract = authorization.contract
    lay = _tmp_layout()
    _write_certified_lock(lay, _bound(_cfg()))
    with _mock_pipeline_multipass(
            [(100, 0, 5, True), (900000, 0, 50000, True)]) as calls:
        result = pipeline.evaluate(
            Genome("silo", {"BACK_OFF": 1}), lay,
            contract.env_tag, "deadbeef",
            PerfConfig(records=1000, threads=2), clocks_per_us=contract.clocks_per_us,
            numactl=contract.numactl, authorization_contract=authorization,
            extra_correctness=[(pipeline.S2_TAG, pipeline.s2_correctness_workload())],
            do_bench=False, log=lambda *a: None, build_context=_BUILD_CONTEXT)
    assert result.certified and not result.aborted
    assert [call["numactl"] for call in calls["trace"]] == [None, ()]


def test_pipeline_extra_correctness_rejects_empty_prefix_when_contract_requires_numactl():
    """T-1174/D36 決定4-4: linux-baremetal の bench 契約が numactl prefix を
    持つとき、prefix 無しの S2 verify は build/verify 前に fail-closed で拒否する。"""
    lay = _tmp_layout()
    with _assert_raises_contains(ValueError, "bench と同じメモリ配置"):
        pipeline.evaluate(
            Genome("silo", {"BACK_OFF": 1}), lay,
            _AUTH_CONTRACT.env_tag, "deadbeef",
            PerfConfig(records=1000, threads=2), clocks_per_us=1800,
            numactl=(), authorization_contract=_AUTHORIZATION,
            extra_correctness=[(pipeline.S2_TAG, pipeline.s2_correctness_workload())],
            do_bench=False, log=lambda *a: None, build_context=_BUILD_CONTEXT)
    assert list(wal.read_records(lay)) == []


def test_pipeline_fullscale_invalid_numactl_type_rejected_before_sink_write():
    """不正型は認可前の契約照合 gate が exact ValueError で拒否する。"""
    lay = _tmp_layout()
    expected_type = ValueError
    try:
        pipeline.evaluate(
            Genome("silo", {"BACK_OFF": 1}), lay,
            _AUTH_CONTRACT.env_tag, "deadbeef",
            PerfConfig(records=1000, threads=2), clocks_per_us=1800,
            numactl="numactl --interleave=all",
            authorization_contract=_AUTHORIZATION,
            extra_correctness=[
                (pipeline.S2_TAG, pipeline.s2_correctness_workload())
            ],
            do_bench=False, log=lambda *a: None,
            build_context=_BUILD_CONTEXT)
        assert False, "不正な numactl 型は契約照合 gate で拒否すべき"
    except expected_type as exc:
        assert type(exc) is expected_type
        assert "bench と同じメモリ配置" in str(exc)
    assert list(wal.read_records(lay)) == []


def test_pipeline_extra_correctness_rejects_nonempty_prefix_different_from_contract():
    """T-1174 の新しい拒否面: prefix が非空でも bench の環境契約と異なる配置なら
    受理しない。旧 ``not numactl`` 述語へ戻す変異をこのケースが検出する。"""
    lay = _tmp_layout()
    with _assert_raises_contains(ValueError, "bench と同じメモリ配置"):
        pipeline.evaluate(
            Genome("silo", {"BACK_OFF": 1}), lay,
            _AUTH_CONTRACT.env_tag, "deadbeef",
            PerfConfig(records=1000, threads=2), clocks_per_us=1800,
            numactl=("numactl", "--membind=0"),
            authorization_contract=_AUTHORIZATION,
            extra_correctness=[(pipeline.S2_TAG, pipeline.s2_correctness_workload())],
            do_bench=False, log=lambda *a: None, build_context=_BUILD_CONTEXT)
    assert list(wal.read_records(lay)) == []


def test_pipeline_extra_correctness_second_pass_competing_tenant_aborts():
    """D36 決定4-4 (敵対レビュー 2026-07-09 CONFIRMED): S2 パスは bench_lock だけでなく
    bench 本体と同じ competing_bench_pids() admission も通す。孤児/競合ベンチ検知時は
    verify-competing-tenant で fails-closed reject し、汚染計測を certified にしない。"""
    lay = _tmp_layout()
    numa = ["numactl", "--interleave=all"]
    with _mock_pipeline_multipass(
            [(100, 0, 5, True)], competing=["999 /x/ycsb_silo.exe -t=48"]) as calls:
        r = pipeline.evaluate(
            Genome("silo", {"BACK_OFF": 1}), lay, _AUTH_CONTRACT.env_tag, "deadbeef",
            PerfConfig(records=1000, threads=2), clocks_per_us=1800, numactl=numa,
            authorization_contract=_AUTHORIZATION,
            extra_correctness=[(pipeline.S2_TAG, pipeline.s2_correctness_workload())],
            do_bench=False, log=lambda *a: None, build_context=_BUILD_CONTEXT)
    assert r.aborted and not r.certified
    assert r.verdict == ""                        # B-4: legacy の 'serializable' を持ち越さない
    assert len(calls["trace"]) == 1               # legacy パスのみ実走、S2 は手前で reject
    abort = [rec for rec in wal.read_records(lay) if rec.stage == STAGE_ABORT][-1]
    assert abort.payload.get("reason") == "verify-competing-tenant"
    assert abort.payload.get("workload") == {"tag": "s2"}
    assert abort.payload.get("competing")


def test_pipeline_extra_correctness_second_pass_early_reject_clears_stale_verdict():
    """敵対レビュー 2026-07-09 CONFIRMED: legacy が certified で res.verdict に
    'serializable' 等を残した状態で、S2 パスが verify_trace_dir に到達する前に
    (trace 異常終了等で) reject されると、以前は古い verdict が aborted 結果に
    紛れ込んでいた。今は各パス開始時に verdict をクリアするので空のまま返る。"""
    lay = _tmp_layout()
    numa = ["numactl", "--interleave=all"]
    # 2 パス目の rc=139 (segfault 相当) → verify_trace_dir に到達せず trace-run-nonzero-exit
    with _mock_pipeline_multipass([(100, 0, 5, True), (0, 139, None, True)]):
        r = pipeline.evaluate(
            Genome("silo", {"BACK_OFF": 1}), lay, _AUTH_CONTRACT.env_tag, "deadbeef",
            PerfConfig(records=1000, threads=2), clocks_per_us=1800, numactl=numa,
            authorization_contract=_AUTHORIZATION,
            extra_correctness=[(pipeline.S2_TAG, pipeline.s2_correctness_workload())],
            do_bench=False, log=lambda *a: None, build_context=_BUILD_CONTEXT)
    assert r.aborted and not r.certified
    assert r.verdict == ""                         # legacy の 'serializable' を持ち越さない
    abort = [rec for rec in wal.read_records(lay) if rec.stage == STAGE_ABORT][-1]
    assert abort.payload.get("reason") == "trace-run-nonzero-exit"
    assert abort.payload.get("workload") == {"tag": "s2"}


def test_pipeline_bench_probe_error_aborts_with_structured_payload():
    """B-1/B-6: bench 直前の競合検知 probe (pgrep) が実行失敗すると、握りつぶさず
    bench-probe-error で abort し、abort payload に構造化 probe_error (kind/argv/
    returncode/errno/stdout/stderr) を残す (WAL 永続経路)。実 bench は走らない。"""
    from orchestrator.calibrator.runner import CompetingBenchProbeError
    lay = _tmp_layout()
    probe_err = CompetingBenchProbeError(
        "unexpected-rc", ["pgrep", "-af", "x"], returncode=2, stderr="pgrep boom")
    r, calls = _eval(lay, certified=True, probe_raises=probe_err)
    # bench 段の abort: 正しさゲートは通過済み (certified) だが probe 故障で不採用 (aborted)。
    assert r.aborted and r.fitness_tps is None
    assert len(calls) == 0                         # bench 未起動 (probe 手前で abort)
    assert STAGE_COMMIT not in {rec.stage for rec in wal.read_records(lay)}
    abort = [rec for rec in wal.read_records(lay) if rec.stage == STAGE_ABORT][-1]
    assert abort.payload.get("reason") == "bench-probe-error"
    pe = abort.payload.get("probe_error")
    assert pe and pe["kind"] == "unexpected-rc" and pe["returncode"] == 2
    assert pe["argv"] == ["pgrep", "-af", "x"]
    assert "pgrep boom" in pe["stderr_excerpt"]


def test_pipeline_verify_probe_error_aborts_and_clears_verdict():
    """B-1/B-4/B-6: S2 相当 verify パスの probe (pgrep) が実行失敗すると、
    verify-probe-error で abort し、legacy パスの 'serializable' を持ち越さず
    (aborted=True かつ verdict 空)、probe_error payload と S2 workload タグを残す。
    S2 の trace は走らない (probe 手前で reject)。"""
    from orchestrator.calibrator.runner import CompetingBenchProbeError
    lay = _tmp_layout()
    numa = ["numactl", "--interleave=all"]
    probe_err = CompetingBenchProbeError(
        "exec-failure", ["pgrep", "-af", "x"], errno=2, stderr="not found")
    with _mock_pipeline_multipass([(100, 0, 5, True)], probe_raises=probe_err) as calls:
        r = pipeline.evaluate(
            Genome("silo", {"BACK_OFF": 1}), lay, _AUTH_CONTRACT.env_tag, "deadbeef",
            PerfConfig(records=1000, threads=2), clocks_per_us=1800, numactl=numa,
            authorization_contract=_AUTHORIZATION,
            extra_correctness=[(pipeline.S2_TAG, pipeline.s2_correctness_workload())],
            do_bench=False, log=lambda *a: None, build_context=_BUILD_CONTEXT)
    assert r.aborted and not r.certified
    assert r.verdict == ""                         # B-4: 空 verdict
    assert len(calls["trace"]) == 1                # legacy のみ実走、S2 は probe 手前で reject
    abort = [rec for rec in wal.read_records(lay) if rec.stage == STAGE_ABORT][-1]
    assert abort.payload.get("reason") == "verify-probe-error"
    assert abort.payload.get("workload") == {"tag": "s2"}
    pe = abort.payload.get("probe_error")
    assert pe and pe["kind"] == "exec-failure" and pe["errno"] == 2
    verify_recs = [rec for rec in wal.read_records(lay) if rec.stage == STAGE_VERIFY_DONE]
    assert [rec.payload["workload"]["tag"] for rec in verify_recs] == ["legacy"]


def test_loop_probe_error_is_retryable_after_recovery():
    """B-3/D-3 番人テスト: bench-probe-error / verify-probe-error abort (transient 環境
    故障) は permanent skip でなく probe 復旧後の次 run で同一 variant が再評価される。
    run1 = probe 故障で terminal abort、run2 = 復旧 → 再評価・commit を固定する。"""
    from orchestrator.campaign import loop as L
    for reason in ("bench-probe-error", "verify-probe-error"):
        out_root = _tmpdir("izanagi_loop_probe_")
        cfg = CampaignConfig(spec_slug="t", search_tag="enum",
                             spec_content=f"probe-{reason}", ccbench_commit="deadbeef")
        g = Genome("silo", {"BACK_OFF": 1})
        v = pipeline.variant_id(g, "stock")
        lay = campaign_layout(str(ident.campaign_id(_bound(cfg))), out_root).ensure()
        _write_certified_lock(lay, _bound(cfg))
        # run1: probe 故障 → terminal abort (evaluate は呼ばれた体で WAL を直書き)
        _write_receiptful_attempt(
            lay, g, v, attempt_id=f"loop-probe-{reason}",
            terminal=STAGE_ABORT, reason=reason,
        )

        calls = []

        def fake_eval(g, *a, **kw):
            calls.append(g)
            return EvalResult(genome=g,
                              variant=pipeline.variant_id(g, kw.get("src_token")),
                              certified=True, aborted=False, fitness_tps=100.0)

        saved, saved_sd = L.evaluate, L.source_digest
        L.evaluate = fake_eval
        L.source_digest = _sd_mock("stock")
        try:
            s = L.run_campaign(
                cfg, [g], PerfConfig(records=1, threads=1),
                _AUTH_CONTRACT.env_tag, _AUTH_CONTRACT.clocks_per_us,
                numactl=list(_AUTH_CONTRACT.numactl),
                authorization_contract=_AUTHORIZATION,
                do_bench=False, output_root=out_root,
                               log=lambda *a: None, build_context=_BUILD_CONTEXT,
                               declared_use_class="official")
        finally:
            L.evaluate, L.source_digest = saved, saved_sd
        assert len(calls) == 1 and s.committed == 1 and s.skipped == 0, reason


def test_screening_driver_probe_error_is_retryable_after_recovery():
    """F2 番人テスト: screening_driver.evaluate_candidate も loop と同じ retryable 契約
    (model.RETRYABLE_ABORT_REASONS) で transient 環境故障 abort を再評価する。旧実装は
    identity-error を含む全 terminal を permanent skip する非対称だった — probe-error 2 種に
    加え identity-error も復旧後に再評価されること (意図的な loop.py との一致) を固定し、
    同時に非 retryable な terminal (verifier-red) は skip され続けること (過剰な広がりの番人)
    も固定する。run1 = terminal abort、run2 = 復旧後の evaluate_candidate 呼び出し。"""
    from orchestrator.campaign import screening_driver as SD
    retryable = ("bench-probe-error", "verify-probe-error", "identity-error")
    for reason in retryable + ("verifier-red",):
        out_root = _tmpdir("izanagi_screen_probe_")
        cfg = CampaignConfig(spec_slug="t", search_tag="sweep",
                             spec_content=f"screen-{reason}", ccbench_commit="deadbeef")
        g = Genome("silo", {"BACK_OFF": 1})
        v = pipeline.variant_id(g, "stock")
        lay = campaign_layout(str(ident.campaign_id(_bound(cfg))), out_root).ensure()
        _write_certified_lock(lay, _bound(cfg))
        # run1: terminal abort (evaluate は呼ばれた体で WAL を直書き)
        if reason == "identity-error":
            _write_prebuild_abort(
                lay, g, v, attempt_id=f"screen-{reason}", reason=reason,
            )
        else:
            _write_receiptful_attempt(
                lay, g, v, attempt_id=f"screen-{reason}",
                terminal=STAGE_ABORT, reason=reason,
            )

        calls = []

        def fake_eval(g, *a, **kw):
            calls.append(g)
            return EvalResult(genome=g,
                              variant=pipeline.variant_id(g, kw.get("src_token")),
                              certified=True, aborted=False, fitness_tps=100.0)

        saved, saved_sd = SD.evaluate, SD.source_digest
        SD.evaluate = fake_eval
        SD.source_digest = _sd_mock("stock")
        try:
            res = SD.evaluate_candidate(
                cfg, lay, g, PerfConfig(records=1, threads=1),
                _AUTH_CONTRACT.env_tag, _AUTH_CONTRACT.clocks_per_us,
                numactl=_AUTH_CONTRACT.numactl,
                authorization_contract=_AUTHORIZATION,
                screening=None, src_token="stock", log=lambda *a: None,
                build_context=_BUILD_CONTEXT)
        finally:
            SD.evaluate, SD.source_digest = saved, saved_sd
        if reason in retryable:
            assert len(calls) == 1 and res is not None and res.certified, reason
        else:
            assert calls == [] and res is None, reason


@pytest.mark.usefixtures("ratified_enforcement_source")
def test_loop_enables_s2_extra_correctness_via_search_config():
    """D36 決定4-1: search_config[SEARCH_CONFIG_VERIFY_KEY]=='legacy+s2' で
    run_campaign が evaluate() に S2 extra_correctness を渡す (opt-in の配線点)。"""
    from orchestrator.campaign import loop as L

    captured = {}

    def fake_eval(g, layout, env_tag, ccbench_commit, perf, clocks_per_us,
                  numactl=None, correctness=None, extra_correctness=None,
                  do_bench=True, do_settle=True, src_token=None, log=print,
                  ccbench_dir="", cache_root="", *, authorization_contract,
                  build_context,
                  capability_resolver=None, source_evidence=None,
                  verify_fanout_hosts=()):
        assert build_context is _BUILD_CONTEXT
        assert verify_fanout_hosts == ()
        captured["extra_correctness"] = extra_correctness
        v = pipeline.variant_id(g, src_token or "stock")
        wal.log(layout, v, STAGE_BUILD_START, env_tag, {"genome": g.canonical()})
        commit_receipts.log_receipted_commit(layout, v, env_tag, {
            "fitness_tps": 1.0,
            COMMIT_CONTRACT_SHA256_KEY: _T530_CONTRACT_SHA256,
        })
        return EvalResult(genome=g, variant=v, certified=True, aborted=False,
                          fitness_tps=1.0)

    out_root = _tmpdir("izanagi_loop_s2_")
    cfg = CampaignConfig(spec_slug="t", search_tag="sort", spec_content="x",
                         ccbench_commit="deadbeef",
                         search_config={pipeline.SEARCH_CONFIG_VERIFY_KEY:
                                        pipeline.VERIFY_LEGACY_PLUS_S2})
    saved_eval, saved_sd = L.evaluate, L.source_digest
    L.evaluate = fake_eval
    L.source_digest = _sd_mock("stock")
    try:
        L.run_campaign(cfg, [Genome("silo", {"BACK_OFF": 1})],
                       PerfConfig(records=1, threads=1),
                       _AUTH_CONTRACT.env_tag, _AUTH_CONTRACT.clocks_per_us,
                       numactl=list(_AUTH_CONTRACT.numactl),
                       authorization_contract=_AUTHORIZATION,
                       do_bench=False, output_root=out_root,
                        log=lambda *a: None, build_context=_BUILD_CONTEXT,
                        declared_use_class="official")
    finally:
        L.evaluate, L.source_digest = saved_eval, saved_sd
    assert captured["extra_correctness"] is not None
    assert [tag for tag, _ in captured["extra_correctness"]] == [pipeline.S2_TAG]


@pytest.mark.usefixtures("ratified_enforcement_source")
def test_loop_omits_extra_correctness_without_verify_search_config():
    """回帰確認: search_config に verify キーが無い既存 campaign は extra_correctness
    が None のまま (S2 は opt-in、既存 campaign の挙動を変えない)。"""
    from orchestrator.campaign import loop as L

    captured = {}

    def fake_eval(g, layout, env_tag, ccbench_commit, perf, clocks_per_us,
                  numactl=None, correctness=None, extra_correctness=None,
                  do_bench=True, do_settle=True, src_token=None, log=print,
                  ccbench_dir="", cache_root="", *, authorization_contract,
                  build_context,
                  capability_resolver=None, source_evidence=None,
                  verify_fanout_hosts=()):
        assert build_context is _BUILD_CONTEXT
        assert verify_fanout_hosts == ()
        captured["extra_correctness"] = extra_correctness
        v = pipeline.variant_id(g, src_token or "stock")
        wal.log(layout, v, STAGE_BUILD_START, env_tag, {"genome": g.canonical()})
        commit_receipts.log_receipted_commit(layout, v, env_tag, {
            "fitness_tps": 1.0,
            COMMIT_CONTRACT_SHA256_KEY: _T530_CONTRACT_SHA256,
        })
        return EvalResult(genome=g, variant=v, certified=True, aborted=False,
                          fitness_tps=1.0)

    out_root = _tmpdir("izanagi_loop_nos2_")
    cfg = CampaignConfig(spec_slug="t", search_tag="enum", spec_content="x",
                         ccbench_commit="deadbeef")
    saved_eval, saved_sd = L.evaluate, L.source_digest
    L.evaluate = fake_eval
    L.source_digest = _sd_mock("stock")
    try:
        L.run_campaign(cfg, [Genome("silo", {"BACK_OFF": 1})],
                       PerfConfig(records=1, threads=1),
                       _AUTH_CONTRACT.env_tag, _AUTH_CONTRACT.clocks_per_us,
                       numactl=list(_AUTH_CONTRACT.numactl),
                       authorization_contract=_AUTHORIZATION,
                       do_bench=False, output_root=out_root,
                        log=lambda *a: None, build_context=_BUILD_CONTEXT,
                        declared_use_class="official")
    finally:
        L.evaluate, L.source_digest = saved_eval, saved_sd
    assert captured["extra_correctness"] is None


@pytest.mark.usefixtures("ratified_enforcement_source")
def test_m12_loop_compute_uses_gxx_and_forwards_only_contract_and_prefix():
    from orchestrator.campaign import loop as L

    captured = {"resolve": [], "evaluate": []}
    contract = ec.lookup("pegasus")
    prefix = "/scr/job/gflags;/scr/job/glog"

    def resolve(genome_value, commit, *, ccbench_dir="", cxx="g++-13"):
        captured["resolve"].append(((genome_value, commit, ccbench_dir, cxx), {}))
        return _source_evidence(
            genome_value, commit,
            source_root=ccbench_dir or "/tmp/izanagi-test-ccbench",
        )

    def fake_eval(g, *args, **kwargs):
        captured["evaluate"].append(kwargs)
        return EvalResult(
            genome=g, variant=pipeline.variant_id(g, kwargs["src_token"]),
            certified=True, aborted=False, fitness_tps=1.0,
        )

    out_root = _tmpdir("izanagi_loop_compute_cxx_")
    cfg = CampaignConfig(
        spec_slug="t", search_tag="enum", spec_content="compute-cxx",
        ccbench_commit="deadbeef",
    )
    saved_eval, saved_sd = L.evaluate, L.source_digest
    saved_compilers = L._compilers_for_current_site
    saved_authorize = L._authorize_measurement
    L.evaluate = fake_eval
    L.source_digest = types.SimpleNamespace(STOCK="stock", resolve_evidence=resolve)
    L._compilers_for_current_site = lambda: ("gcc", "g++")
    bound_cfg = ident.bind_environment_contract(
        ident.bind_admission_policy(cfg, _BUILD_CONTEXT.policy), contract,
    )
    authorization_result = L._AuthorizationResult(
        authorized_contract=contract,
        execution_receipt={"fixture": "receipt"},
        bound_cfg=bound_cfg,
        campaign_identity=str(ident.campaign_id(bound_cfg)),
    )
    L._authorize_measurement = lambda *args, **kwargs: authorization_result
    try:
        summary = L.run_campaign(
            cfg, [Genome("silo", {"BACK_OFF": 1})],
            PerfConfig(records=1, threads=1), "pegasus", 2100,
            do_bench=False, output_root=out_root, log=lambda *a: None,
            env_contract=contract, dependency_prefix=prefix,
            numactl=contract.numactl,
            authorization_contract=ec.authorize(contract.env_tag),
            build_context=_BUILD_CONTEXT, declared_use_class="official",
        )
    finally:
        L.evaluate, L.source_digest = saved_eval, saved_sd
        L._compilers_for_current_site = saved_compilers
        L._authorize_measurement = saved_authorize

    assert captured["resolve"][0][0][-1] == "g++"
    assert captured["evaluate"][0]["env_contract"] == contract
    assert captured["evaluate"][0]["dependency_prefix"] == prefix
    assert "site" not in inspect.signature(L.run_campaign).parameters
    assert summary.campaign_id == authorization_result.campaign_identity
    assert summary.execution_receipt == {"fixture": "receipt"}


_RESERVATION_ENV_NAMES = (
    "IZANAGI_RESERVATION_JOB_ID",
    "IZANAGI_RESERVATION_REQUESTED_S",
    "IZANAGI_RESERVATION_SCHEDULER_STARTED_EPOCH",
    "IZANAGI_RESERVATION_DEADLINE_EPOCH",
    "IZANAGI_RESERVATION_HOST",
    "IZANAGI_RESERVATION_BOOT_ID",
    "IZANAGI_RESERVATION_SCRIPT_SHA256",
    "IZANAGI_RESERVATION_NONCE",
    "PBS_JOBID",
)


@contextlib.contextmanager
def _campaign_reservation_environment(present=True):
    sentinel = object()
    saved = {
        name: os.environ.get(name, sentinel)
        for name in _RESERVATION_ENV_NAMES
    }
    for name in _RESERVATION_ENV_NAMES:
        os.environ.pop(name, None)
    if present:
        now = time.time()
        started = now - 30.0
        requested = 3600
        boot_id = Path("/proc/sys/kernel/random/boot_id").read_text(
            encoding="ascii",
        ).strip()
        os.environ.update({
            "IZANAGI_RESERVATION_JOB_ID": "fixture-job-1411",
            "IZANAGI_RESERVATION_REQUESTED_S": str(requested),
            "IZANAGI_RESERVATION_SCHEDULER_STARTED_EPOCH": str(started),
            "IZANAGI_RESERVATION_DEADLINE_EPOCH": str(started + requested),
            "IZANAGI_RESERVATION_HOST": "fixture-host-1411",
            "IZANAGI_RESERVATION_BOOT_ID": boot_id,
            "IZANAGI_RESERVATION_SCRIPT_SHA256": "a" * 64,
            "IZANAGI_RESERVATION_NONCE": "fixture-nonce-1411",
            "PBS_JOBID": "fixture-job-1411",
        })
    try:
        yield
    finally:
        for name, value in saved.items():
            if value is sentinel:
                os.environ.pop(name, None)
            else:
                os.environ[name] = value


@contextlib.contextmanager
def _mock_required_attestation(L, order, *, matches=True):
    saved = {
        "load": L.env_attestation.load_verified_calibration,
        "attest": L.execution_guard.attest_and_build_receipt,
        "matches": L.execution_guard.receipt_matches_contract,
    }
    verified = object()
    receipt = {"schema": "fixture-required-receipt"}
    L.env_attestation.load_verified_calibration = (
        lambda loaded, root: order.append("load") or verified
    )
    L.execution_guard.attest_and_build_receipt = (
        lambda loaded, calibration: order.append("attest") or receipt
    )
    L.execution_guard.receipt_matches_contract = (
        lambda loaded, **kwargs: order.append("matches") or matches
    )
    try:
        yield receipt
    finally:
        L.env_attestation.load_verified_calibration = saved["load"]
        L.execution_guard.attest_and_build_receipt = saved["attest"]
        L.execution_guard.receipt_matches_contract = saved["matches"]


def _single_process_test_policy(base: Path):
    from orchestrator.campaign.durable_root import DurableRootPolicy

    return DurableRootPolicy(
        approved_roots=(base.resolve(),), forbidden_roots=(),
    )


def _assert_single_process_claim(summary, base: Path, bound_cfg: CampaignConfig):
    claim_root = base / "env" / "pegasus" / "claims"
    claim_files = sorted(claim_root.glob("*.claim"))
    assert len(claim_files) == 1
    payload = json.loads(claim_files[0].read_text(encoding="utf-8"))
    expected_digest = hashlib.sha256(
        ident.canonical_preimage(bound_cfg).encode("utf-8")
    ).hexdigest()
    assert payload["campaign_identity"] == summary.campaign_id
    assert payload["protocol_digest"] == expected_digest
    assert Path(summary.layout_root) == base / "campaigns" / summary.campaign_id
    assert claim_root.parents[2] == base
    return claim_root, payload


@pytest.mark.usefixtures("ratified_enforcement_source")
def test_required_contract_is_attested_once_at_run_campaign_sink():
    from orchestrator.campaign import loop as L
    from orchestrator.campaign import campaign_claim, reservation

    contract = ec.lookup("pegasus")
    order = []
    campaign_id_calls = []
    base = Path(_tmpdir("izanagi_loop_single_process_official_"))
    (base / "env" / "pegasus" / "claims").mkdir(parents=True)
    policy = _single_process_test_policy(base)
    saved = {
        "evaluate": L.evaluate,
        "source_digest": L.source_digest,
        "read_binding": reservation.read_binding,
        "check_reservation": reservation.check_reservation,
        "acquire_claim": campaign_claim.acquire_claim,
        "campaign_id": ident.campaign_id,
    }
    L.reservation.read_binding = (
        lambda environ: order.append("read_binding") or
        saved["read_binding"](environ)
    )
    L.reservation.check_reservation = (
        lambda binding, **kwargs: order.append("check_reservation") or
        saved["check_reservation"](binding, **kwargs)
    )
    L.campaign_claim.acquire_claim = (
        lambda claim_root, record: order.append("acquire_claim") or
        saved["acquire_claim"](claim_root, record)
    )

    def campaign_id_spy(cfg):
        campaign_id_calls.append(cfg)
        return saved["campaign_id"](cfg)

    L.ident.campaign_id = campaign_id_spy

    def fake_eval(genome, *args, **kwargs):
        order.append("evaluate")
        return EvalResult(
            genome=genome, variant=pipeline.variant_id(genome, kwargs["src_token"]),
            certified=True, aborted=False,
        )

    L.evaluate = fake_eval
    L.source_digest = _sd_mock("stock")
    cfg = CampaignConfig(
        spec_slug="t", search_tag="enum", spec_content="required-attestation-once",
        ccbench_commit="deadbeef",
    )
    bound_cfg = ident.bind_environment_contract(
        ident.bind_admission_policy(cfg, _BUILD_CONTEXT.policy), contract,
    )
    try:
        with _campaign_reservation_environment(), _mock_required_attestation(L, order) as receipt:
            summary = L.run_campaign(
                cfg,
                [Genome("silo", {"BACK_OFF": 0}), Genome("silo", {"BACK_OFF": 1})],
                PerfConfig(records=1, threads=1), contract.env_tag,
                contract.clocks_per_us, numactl=contract.numactl,
                do_bench=False, output_root=str(base), log=lambda *a: None,
                env_contract=contract, authorization_contract=ec.authorize(contract.env_tag),
                build_context=_BUILD_CONTEXT, declared_use_class="official",
                durable_root_policy=policy,
            )
    finally:
        L.evaluate = saved["evaluate"]
        L.source_digest = saved["source_digest"]
        L.reservation.read_binding = saved["read_binding"]
        L.reservation.check_reservation = saved["check_reservation"]
        L.campaign_claim.acquire_claim = saved["acquire_claim"]
        L.ident.campaign_id = saved["campaign_id"]
    assert order == [
        "load", "attest", "matches", "read_binding", "check_reservation",
        "acquire_claim", "evaluate", "evaluate",
    ]
    assert len(campaign_id_calls) == 1
    assert summary.execution_receipt is receipt
    _assert_single_process_claim(summary, base, bound_cfg)


@pytest.mark.usefixtures("ratified_enforcement_source")
def test_exploration_claim_uses_environment_output_root_and_single_identity():
    from orchestrator.campaign import campaign_claim, loop as L, reservation

    contract = ec.lookup("pegasus")
    order = []
    campaign_id_calls = []
    base = Path(_tmpdir("izanagi_loop_single_process_exploration_"))
    claim_root = base / "env" / "pegasus" / "claims"
    claim_root.mkdir(parents=True)
    policy = _single_process_test_policy(base)
    cfg = CampaignConfig(
        spec_slug="t", search_tag="enum", spec_content="exploration-claim-root",
        ccbench_commit="deadbeef",
    )
    bound_cfg = ident.bind_environment_contract(
        ident.bind_admission_policy(cfg, _BUILD_CONTEXT.policy), contract,
    )
    saved = {
        "evaluate": L.evaluate,
        "source_digest": L.source_digest,
        "read_binding": reservation.read_binding,
        "check_reservation": reservation.check_reservation,
        "acquire_claim": campaign_claim.acquire_claim,
        "campaign_id": ident.campaign_id,
    }

    def fake_eval(genome, *args, **kwargs):
        order.append("evaluate")
        return EvalResult(
            genome=genome, variant=pipeline.variant_id(genome, kwargs["src_token"]),
            certified=True, aborted=False,
        )

    L.evaluate = fake_eval
    L.source_digest = _sd_mock("stock")
    L.reservation.read_binding = (
        lambda environ: order.append("read_binding") or
        saved["read_binding"](environ)
    )
    L.reservation.check_reservation = (
        lambda binding, **kwargs: order.append("check_reservation") or
        saved["check_reservation"](binding, **kwargs)
    )
    L.campaign_claim.acquire_claim = (
        lambda root, record: order.append("acquire_claim") or
        saved["acquire_claim"](root, record)
    )

    def campaign_id_spy(candidate_cfg):
        campaign_id_calls.append(candidate_cfg)
        return saved["campaign_id"](candidate_cfg)

    L.ident.campaign_id = campaign_id_spy
    env_name = layout_module._EXPLORATION_OUTPUT_ROOT_ENV
    sentinel = object()
    saved_env = os.environ.get(env_name, sentinel)
    layout_module._reset_exploration_output_root_pin_for_tests()
    os.environ[env_name] = str(base)
    try:
        with _campaign_reservation_environment(), _mock_required_attestation(L, order) as receipt:
            summary = L.run_campaign(
                cfg, [Genome("silo", {"BACK_OFF": 1})],
                PerfConfig(records=1, threads=1), contract.env_tag,
                contract.clocks_per_us, numactl=contract.numactl,
                do_bench=False, log=lambda *a: None,
                env_contract=contract, authorization_contract=ec.authorize(contract.env_tag),
                build_context=_BUILD_CONTEXT, declared_use_class="exploration",
                durable_root_policy=policy,
            )
    finally:
        L.evaluate = saved["evaluate"]
        L.source_digest = saved["source_digest"]
        L.reservation.read_binding = saved["read_binding"]
        L.reservation.check_reservation = saved["check_reservation"]
        L.campaign_claim.acquire_claim = saved["acquire_claim"]
        L.ident.campaign_id = saved["campaign_id"]
        layout_module._reset_exploration_output_root_pin_for_tests()
        if saved_env is sentinel:
            os.environ.pop(env_name, None)
        else:
            os.environ[env_name] = saved_env

    assert order == [
        "load", "attest", "matches", "read_binding", "check_reservation",
        "acquire_claim", "evaluate",
    ]
    assert len(campaign_id_calls) == 1
    assert summary.execution_receipt is receipt
    assert Path(summary.layout_root) == (
        base / "exploration" / "campaigns" / summary.campaign_id
    )
    claim_files = sorted(claim_root.glob("*.claim"))
    assert len(claim_files) == 1
    payload = json.loads(claim_files[0].read_text(encoding="utf-8"))
    expected_digest = hashlib.sha256(
        ident.canonical_preimage(bound_cfg).encode("utf-8")
    ).hexdigest()
    assert payload["campaign_identity"] == summary.campaign_id
    assert payload["protocol_digest"] == expected_digest
    assert claim_root.parents[2] == base


@pytest.mark.usefixtures("ratified_enforcement_source")
def test_single_process_rejects_layout_invalid_campaign_identity_before_claim():
    from orchestrator.campaign import campaign_claim, loop as L

    contract = ec.lookup("pegasus")
    base = Path(_tmpdir("izanagi_loop_invalid_campaign_identity_"))
    claim_root = base / "env" / "pegasus" / "claims"
    claim_root.mkdir(parents=True)
    policy = _single_process_test_policy(base)
    claim_calls = []
    saved_claim = campaign_claim.acquire_claim
    campaign_claim.acquire_claim = (
        lambda *args, **kwargs: claim_calls.append((args, kwargs)) or
        saved_claim(*args, **kwargs)
    )
    cfg = CampaignConfig(
        spec_slug=".hidden", search_tag="enum",
        spec_content="layout-invalid-campaign-identity", ccbench_commit="deadbeef",
    )
    try:
        with _campaign_reservation_environment(), _mock_required_attestation(L, []):
            with pytest.raises(ValueError, match="不正な campaign_id"):
                L.run_campaign(
                    cfg, [], PerfConfig(records=1, threads=1), contract.env_tag,
                    contract.clocks_per_us, numactl=contract.numactl,
                    do_bench=False, output_root=str(base), log=lambda *a: None,
                    env_contract=contract,
                    authorization_contract=ec.authorize(contract.env_tag),
                    build_context=_BUILD_CONTEXT, declared_use_class="official",
                    durable_root_policy=policy,
                )
    finally:
        campaign_claim.acquire_claim = saved_claim
    assert claim_calls == []
    assert list(claim_root.glob("*.claim")) == []


@pytest.mark.usefixtures("ratified_enforcement_source")
def test_single_process_rejects_missing_reservation_binding_before_claim():
    from orchestrator.campaign import loop as L, reservation

    contract = ec.lookup("pegasus")
    base = Path(_tmpdir("izanagi_loop_missing_reservation_"))
    claim_root = base / "env" / "pegasus" / "claims"
    claim_root.mkdir(parents=True)
    policy = _single_process_test_policy(base)
    cfg = CampaignConfig(
        spec_slug="t", search_tag="enum", spec_content="missing-reservation",
        ccbench_commit="deadbeef",
    )
    with _campaign_reservation_environment(False), _mock_required_attestation(L, []):
        with pytest.raises(
                reservation.ReservationError,
                match="IZANAGI_RESERVATION_JOB_ID",
        ):
            L.run_campaign(
                cfg, [], PerfConfig(records=1, threads=1), contract.env_tag,
                contract.clocks_per_us, numactl=contract.numactl,
                do_bench=False, output_root=str(base), log=lambda *a: None,
                env_contract=contract, authorization_contract=ec.authorize(contract.env_tag),
                build_context=_BUILD_CONTEXT, declared_use_class="official",
                durable_root_policy=policy,
            )
    assert list(claim_root.glob("*.claim")) == []


@pytest.mark.usefixtures("ratified_enforcement_source")
def test_single_process_attestation_failure_precedes_claim_creation():
    from orchestrator.campaign import campaign_claim, loop as L

    contract = ec.lookup("pegasus")
    base = Path(_tmpdir("izanagi_loop_attestation_failure_"))
    claim_root = base / "env" / "pegasus" / "claims"
    claim_root.mkdir(parents=True)
    policy = _single_process_test_policy(base)
    order = []
    saved_claim = L.campaign_claim.acquire_claim
    claim_calls = []
    L.campaign_claim.acquire_claim = (
        lambda *args, **kwargs: claim_calls.append((args, kwargs)) or
        saved_claim(*args, **kwargs)
    )
    cfg = CampaignConfig(
        spec_slug="t", search_tag="enum", spec_content="attestation-failure",
        ccbench_commit="deadbeef",
    )
    try:
        with _campaign_reservation_environment(), _mock_required_attestation(
                L, order, matches=False):
            with pytest.raises(
                    L.execution_guard.ExecutionGuardError,
                    match="receipt",
            ):
                L.run_campaign(
                    cfg, [], PerfConfig(records=1, threads=1), contract.env_tag,
                    contract.clocks_per_us, numactl=contract.numactl,
                    do_bench=False, output_root=str(base), log=lambda *a: None,
                    env_contract=contract,
                    authorization_contract=ec.authorize(contract.env_tag),
                    build_context=_BUILD_CONTEXT, declared_use_class="official",
                    durable_root_policy=policy,
                )
    finally:
        L.campaign_claim.acquire_claim = saved_claim
    assert order == ["load", "attest", "matches"]
    assert claim_calls == []
    assert list(claim_root.glob("*.claim")) == []


@pytest.mark.usefixtures("ratified_enforcement_source")
def test_single_process_rejects_missing_claim_directory_before_acquire():
    from orchestrator.campaign import loop as L

    contract = ec.lookup("pegasus")
    base = Path(_tmpdir("izanagi_loop_missing_claim_root_"))
    policy = _single_process_test_policy(base)
    cfg = CampaignConfig(
        spec_slug="t", search_tag="enum", spec_content="missing-claim-root",
        ccbench_commit="deadbeef",
    )
    with _campaign_reservation_environment(), _mock_required_attestation(L, []):
        with pytest.raises(
                L.execution_guard.ExecutionGuardError,
                match="claim root",
        ):
            L.run_campaign(
                cfg, [], PerfConfig(records=1, threads=1), contract.env_tag,
                contract.clocks_per_us, numactl=contract.numactl,
                do_bench=False, output_root=str(base), log=lambda *a: None,
                env_contract=contract, authorization_contract=ec.authorize(contract.env_tag),
                build_context=_BUILD_CONTEXT, declared_use_class="official",
                durable_root_policy=policy,
            )
    assert not (base / "campaigns").exists()


@pytest.mark.usefixtures("ratified_enforcement_source")
def test_single_process_rejects_symlink_claim_directory_without_writing_target():
    from orchestrator.campaign import loop as L

    contract = ec.lookup("pegasus")
    base = Path(_tmpdir("izanagi_loop_symlink_claim_root_"))
    parent = base / "env" / "pegasus"
    parent.mkdir(parents=True)
    target = base / "claim-target"
    target.mkdir()
    claim_root = parent / "claims"
    claim_root.symlink_to(target, target_is_directory=True)
    policy = _single_process_test_policy(base)
    cfg = CampaignConfig(
        spec_slug="t", search_tag="enum", spec_content="symlink-claim-root",
        ccbench_commit="deadbeef",
    )
    with _campaign_reservation_environment(), _mock_required_attestation(L, []):
        with pytest.raises(
                L.execution_guard.ExecutionGuardError,
                match="claim root",
        ):
            L.run_campaign(
                cfg, [], PerfConfig(records=1, threads=1), contract.env_tag,
                contract.clocks_per_us, numactl=contract.numactl,
                do_bench=False, output_root=str(base), log=lambda *a: None,
                env_contract=contract, authorization_contract=ec.authorize(contract.env_tag),
                build_context=_BUILD_CONTEXT, declared_use_class="official",
                durable_root_policy=policy,
            )
    assert list(target.iterdir()) == []


@pytest.mark.usefixtures("ratified_enforcement_source")
def test_single_process_rejects_live_claim_for_same_protocol():
    from orchestrator.campaign import campaign_claim, loop as L, reservation

    contract = ec.lookup("pegasus")
    base = Path(_tmpdir("izanagi_loop_live_claim_"))
    claim_root = base / "env" / "pegasus" / "claims"
    claim_root.mkdir(parents=True)
    policy = _single_process_test_policy(base)
    cfg = CampaignConfig(
        spec_slug="t", search_tag="enum", spec_content="live-claim-conflict",
        ccbench_commit="deadbeef",
    )
    bound_cfg = ident.bind_environment_contract(
        ident.bind_admission_policy(cfg, _BUILD_CONTEXT.policy), contract,
    )
    protocol_digest = hashlib.sha256(
        ident.canonical_preimage(bound_cfg).encode("utf-8")
    ).hexdigest()
    with _campaign_reservation_environment():
        binding = reservation.read_binding(os.environ)
        existing = campaign_claim.ClaimRecord(
            campaign_identity="preexisting-live-claim",
            protocol_digest=protocol_digest,
            job_id=binding.job_id,
            host=binding.host,
            boot_id=binding.boot_id,
            pid=os.getpid(),
            proc_starttime=campaign_claim.read_proc_starttime(),
            created_utc=dt.datetime.now(dt.timezone.utc).isoformat(),
        )
        campaign_claim.acquire_claim(claim_root, existing)
        with _mock_required_attestation(L, []):
            with pytest.raises(campaign_claim.ClaimError, match="同一 protocol"):
                L.run_campaign(
                    cfg, [], PerfConfig(records=1, threads=1), contract.env_tag,
                    contract.clocks_per_us, numactl=contract.numactl,
                    do_bench=False, output_root=str(base), log=lambda *a: None,
                    env_contract=contract,
                    authorization_contract=ec.authorize(contract.env_tag),
                    build_context=_BUILD_CONTEXT, declared_use_class="official",
                    durable_root_policy=policy,
                )
    assert [path.name for path in claim_root.glob("*.claim")] == [
        "preexisting-live-claim.claim",
    ]


@pytest.mark.usefixtures("ratified_enforcement_source")
def test_linux_baremetal_skips_reservation_and_claim_for_non_single_process():
    from orchestrator.campaign import campaign_claim, loop as L, reservation

    contract = ec.lookup("linux-baremetal")
    calls = []
    saved = {
        "evaluate": L.evaluate,
        "source_digest": L.source_digest,
        "read_binding": reservation.read_binding,
        "acquire_claim": campaign_claim.acquire_claim,
    }
    L.reservation.read_binding = (
        lambda *args, **kwargs: calls.append("read_binding") or
        saved["read_binding"](*args, **kwargs)
    )
    L.campaign_claim.acquire_claim = (
        lambda *args, **kwargs: calls.append("acquire_claim") or
        saved["acquire_claim"](*args, **kwargs)
    )

    def fake_eval(genome, *args, **kwargs):
        return EvalResult(
            genome=genome, variant=pipeline.variant_id(genome, kwargs["src_token"]),
            certified=True, aborted=False,
        )

    L.evaluate = fake_eval
    L.source_digest = _sd_mock("stock")
    base = Path(_tmpdir("izanagi_loop_linux_baremetal_positive_"))
    cfg = CampaignConfig(
        spec_slug="t", search_tag="enum", spec_content="linux-positive-control",
        ccbench_commit="deadbeef",
    )
    try:
        with _campaign_reservation_environment(False):
            summary = L.run_campaign(
                cfg, [Genome("silo", {"BACK_OFF": 1})],
                PerfConfig(records=1, threads=1), contract.env_tag,
                contract.clocks_per_us, numactl=contract.numactl,
                do_bench=False, output_root=str(base), log=lambda *a: None,
                env_contract=contract, authorization_contract=ec.authorize(contract.env_tag),
                build_context=_BUILD_CONTEXT, declared_use_class="official",
            )
    finally:
        L.evaluate = saved["evaluate"]
        L.source_digest = saved["source_digest"]
        L.reservation.read_binding = saved["read_binding"]
        L.campaign_claim.acquire_claim = saved["acquire_claim"]
    assert summary.committed == 1 and summary.aborted == 0
    assert calls == []


# ===== STAGE2: campaign ループの堅牢性 (例外隔離 / run 内 dedup) =====

def _sd_mock(src_token):
    """loop の source_digest を差し替える mock。src_token が Exception なら resolve が raise
    (identity-error 経路)、それ以外はその文字列を返す (identity 核は実 g++/git 依存ゆえ mock)。"""
    if isinstance(src_token, Exception):
        def _resolve(*a, **k):
            raise src_token
    else:
        def _resolve(genome_value, commit, *, ccbench_dir="", cxx="g++-13"):
            if src_token != "stock" and len(src_token) != 64:
                # The loop-only tests replace evaluate() itself; preserve their
                # opaque identity sentinel without treating it as build evidence.
                return types.SimpleNamespace(src_token=src_token)
            return _source_evidence(
                genome_value,
                commit,
                src_token=src_token,
                source_root=(
                    ccbench_dir or str(commit_receipts.proof_source_root())
                ),
            )
    return types.SimpleNamespace(STOCK="stock", resolve_evidence=_resolve)


def _loop_with_fake_eval(fake_eval, genomes, spec_content, do_bench=False,
                         src_token="stock"):
    """run_campaign を fake evaluate 下で回し (summary, layout) を返す。

    loop は src_token id で skip/abort キーを揃える (D24)。identity 核 (source_digest) は実
    g++/git 依存ゆえ mock し、src_token を制御する (Exception なら identity-error 経路)。"""
    from orchestrator.campaign import loop as L
    out_root = _tmpdir("izanagi_loop_")
    cfg = CampaignConfig(spec_slug="t", search_tag="enum",
                         spec_content=spec_content, ccbench_commit="deadbeef")
    saved, saved_sd = L.evaluate, L.source_digest
    L.evaluate = fake_eval
    L.source_digest = _sd_mock(src_token)
    try:
        s = L.run_campaign(
            cfg, genomes, PerfConfig(records=1, threads=1),
            _AUTH_CONTRACT.env_tag, _AUTH_CONTRACT.clocks_per_us,
            numactl=list(_AUTH_CONTRACT.numactl),
            authorization_contract=_AUTHORIZATION, do_bench=do_bench,
                           output_root=out_root, log=lambda *a: None,
                           build_context=_BUILD_CONTEXT,
                           declared_use_class="official")
    finally:
        L.evaluate, L.source_digest = saved, saved_sd
    bound_cfg = _bound(cfg)
    lay = campaign_layout(str(ident.campaign_id(bound_cfg)), out_root)
    return s, lay


_PERF_PREFLIGHT_EVENT_LINES = (
    "1,,LLC-load-misses,0,100.00,,\n"
    "2,,LLC-loads,0,100.00,,\n"
    "3,,instructions,0,100.00,,\n"
    "4,,cycles,0,100.00,,\n"
)


def _perf_preflight_producer(mode, producer_calls):
    """実 perf に依存せず、production probe の subprocess seam だけを差し替える。"""
    def produce(*, perf_candidates):
        producer_calls.append(tuple(perf_candidates))

        def run(argv, **_kwargs):
            if mode == "unavailable":
                raise FileNotFoundError("perf")
            if mode == "probe_error":
                raise subprocess.TimeoutExpired(argv, 1)
            assert mode == "available"
            Path(argv[argv.index("-o") + 1]).write_text(
                _PERF_PREFLIGHT_EVENT_LINES, encoding="utf-8",
            )
            return types.SimpleNamespace(returncode=0, stdout="", stderr="")

        return perf_preflight_module.probe_perf_availability(
            perf_candidates=perf_candidates, subprocess_runner=run,
        )

    return produce


def _run_exploration_with_perf_preflight(mode):
    from orchestrator.campaign import loop as L

    out_root = _tmpdir(f"izanagi_loop_perf_{mode}_")
    cfg = CampaignConfig(
        spec_slug="t", search_tag="enum",
        spec_content=f"perf-preflight-{mode}", ccbench_commit="deadbeef",
    )
    candidate = Genome("silo", {"BACK_OFF": 1})
    producer_calls = []
    saved_sd = L.source_digest
    L.source_digest = _sd_mock("stock")
    try:
        with _mock_pipeline(certified=True) as bench_calls:
            summary = L.run_campaign(
                cfg, [candidate], PerfConfig(records=1000, threads=2),
                _AUTH_CONTRACT.env_tag, _AUTH_CONTRACT.clocks_per_us,
                numactl=list(_AUTH_CONTRACT.numactl),
                authorization_contract=_AUTHORIZATION,
                output_root=out_root, log=lambda *_args: None,
                build_context=_BUILD_CONTEXT,
                declared_use_class="exploration",
                perf_preflight_fn=_perf_preflight_producer(mode, producer_calls),
            )
    finally:
        L.source_digest = saved_sd
    layout = exploration_campaign_layout(summary.campaign_id, out_root)
    return summary, bench_calls, layout, producer_calls


@pytest.mark.usefixtures("ratified_enforcement_source")
def test_official_rejects_perf_preflight_seam_while_exploration_accepts_it():
    from orchestrator.campaign import loop as L

    parent = _tmpdir("izanagi_loop_perf_seam_namespace_")
    official_root = os.path.join(parent, "official-must-not-exist")
    cfg = CampaignConfig(
        spec_slug="t", search_tag="enum", spec_content="perf-seam-namespace",
        ccbench_commit="deadbeef",
    )
    candidate = Genome("silo", {"BACK_OFF": 1})
    producer_calls = []
    producer = _perf_preflight_producer("unavailable", producer_calls)
    common = (
        cfg, [candidate], PerfConfig(records=1000, threads=2),
        _AUTH_CONTRACT.env_tag, _AUTH_CONTRACT.clocks_per_us,
    )

    with pytest.raises(
            ValueError,
            match=r"official mode への非 default seam 注入を拒否する: "
                  r"\['perf_preflight_fn'\]",
    ):
        L.run_campaign(
            *common, numactl=list(_AUTH_CONTRACT.numactl),
            authorization_contract=_AUTHORIZATION,
            output_root=official_root, log=lambda *_args: None,
            build_context=_BUILD_CONTEXT, declared_use_class="official",
            perf_preflight_fn=producer,
        )
    assert producer_calls == []
    assert not os.path.exists(official_root)

    exploration_root = os.path.join(parent, "exploration")
    saved_sd = L.source_digest
    L.source_digest = _sd_mock("stock")
    try:
        with _mock_pipeline(certified=True):
            summary = L.run_campaign(
                *common, numactl=list(_AUTH_CONTRACT.numactl),
                authorization_contract=_AUTHORIZATION,
                output_root=exploration_root, log=lambda *_args: None,
                build_context=_BUILD_CONTEXT, declared_use_class="exploration",
                perf_preflight_fn=producer,
            )
    finally:
        L.source_digest = saved_sd
    assert len(producer_calls) == 1
    assert summary.committed == 1 and summary.aborted == 0
    assert summary.perf_preflight_receipt["status"] == "unavailable"


@pytest.mark.usefixtures("ratified_enforcement_source")
def test_exploration_no_perf_completes_bench_and_records_not_required():
    summary, bench_calls, layout, producer_calls = \
        _run_exploration_with_perf_preflight("unavailable")

    assert len(producer_calls) == 1
    assert summary.committed == 1 and summary.aborted == 0
    assert summary.perf_preflight_receipt["status"] == "unavailable"
    assert bench_calls.measure_kwargs
    assert all(call.get("use_perf") is False for call in bench_calls.measure_kwargs)
    bench = next(
        record for record in wal.read_records(layout)
        if record.stage == STAGE_BENCH_DONE
    )
    observation = bench.payload["perf_observation"]
    assert observation["use_perf"] is False
    assert observation["counter_status"] == "not_required"
    assert observation["missing_leading_indicators"] == []
    assert observation["preflight"]["status"] == "unavailable"
    assert bench.payload["leading_indicators"]["llc_miss_rate"] is None
    assert bench.payload["leading_indicators"]["ipc"] is None


def test_exploration_perf_probe_error_fails_closed_before_evaluation():
    from orchestrator.campaign import loop as L

    out_root = _tmpdir("izanagi_loop_perf_probe_error_")
    cfg = CampaignConfig(
        spec_slug="t", search_tag="enum", spec_content="perf-probe-error",
        ccbench_commit="deadbeef",
    )
    producer_calls = []
    with pytest.raises(perf_preflight_module.PerfPreflightError, match="判定不能"):
        L.run_campaign(
            cfg, [Genome("silo", {"BACK_OFF": 1})],
            PerfConfig(records=1000, threads=2),
            _AUTH_CONTRACT.env_tag, _AUTH_CONTRACT.clocks_per_us,
            numactl=list(_AUTH_CONTRACT.numactl),
            authorization_contract=_AUTHORIZATION,
            output_root=out_root, log=lambda *_args: None,
            build_context=_BUILD_CONTEXT,
            declared_use_class="exploration",
            perf_preflight_fn=_perf_preflight_producer(
                "probe_error", producer_calls,
            ),
        )
    assert len(producer_calls) == 1
    assert not os.path.exists(os.path.join(out_root, "exploration"))


@pytest.mark.usefixtures("ratified_enforcement_source")
def test_exploration_available_perf_preserves_measurement_behavior():
    summary, bench_calls, layout, producer_calls = \
        _run_exploration_with_perf_preflight("available")

    assert len(producer_calls) == 1
    assert summary.committed == 1 and summary.aborted == 0
    assert summary.perf_preflight_receipt["status"] == "available"
    assert bench_calls.measure_kwargs
    # True は既存 default のままなので measure_point の呼出し形も変えない。
    assert all("use_perf" not in call for call in bench_calls.measure_kwargs)
    bench = next(
        record for record in wal.read_records(layout)
        if record.stage == STAGE_BENCH_DONE
    )
    observation = bench.payload["perf_observation"]
    assert observation["use_perf"] is True
    assert observation["counter_status"] == "complete"
    assert observation["missing_leading_indicators"] == []
    assert observation["preflight"]["status"] == "available"


@pytest.mark.usefixtures("ratified_enforcement_source")
def test_run_campaign_requires_declared_use_class():
    """selector 省略は暗黙 official にせず、実行前に TypeError へ倒す。"""
    from orchestrator.campaign import loop as L

    parameters = inspect.signature(L.run_campaign).parameters
    assert "campaign_namespace" not in parameters
    declared = parameters["declared_use_class"]
    assert declared.kind is inspect.Parameter.KEYWORD_ONLY
    assert declared.default is inspect.Parameter.empty

    out_root = os.path.join(
        _tmpdir("izanagi_loop_namespace_default_"), "must-not-exist",
    )
    cfg = CampaignConfig(spec_slug="t", search_tag="enum",
                         spec_content="namespace-default", ccbench_commit="deadbeef")
    with pytest.raises(TypeError):
        L.run_campaign(
            cfg, [], PerfConfig(records=1, threads=1),
            _AUTH_CONTRACT.env_tag, _AUTH_CONTRACT.clocks_per_us,
            numactl=list(_AUTH_CONTRACT.numactl),
            authorization_contract=_AUTHORIZATION,
            do_bench=False, output_root=out_root, log=lambda *_args: None,
            build_context=_BUILD_CONTEXT,
        )
    assert not os.path.exists(out_root)


@pytest.mark.usefixtures("ratified_enforcement_source")
def test_run_campaign_exploration_namespace_reaches_lock_wal_and_pipeline():
    """exploration selector が marker/lock/WAL/evaluate の同一 layout まで届く。"""
    from orchestrator.campaign import loop as L

    out_root = _tmpdir("izanagi_loop_namespace_exploration_")
    cfg = CampaignConfig(spec_slug="t", search_tag="enum",
                         spec_content="namespace-exploration", ccbench_commit="deadbeef")
    genome = Genome("silo", {"BACK_OFF": 1})
    evaluated_layouts = []

    def fake_eval(g, layout, env_tag, ccbench_commit, perf, clocks_per_us, **kwargs):
        evaluated_layouts.append(layout)
        variant = pipeline.variant_id(g, kwargs.get("src_token"))
        wal.log(layout, variant, STAGE_BUILD_START, env_tag,
                {"genome": g.canonical()})
        commit_receipts.log_receipted_commit(layout, variant, env_tag, {
            "fitness_tps": 1.0,
            COMMIT_CONTRACT_SHA256_KEY: _T530_CONTRACT_SHA256,
        })
        return EvalResult(genome=g, variant=variant, certified=True, aborted=False,
                          fitness_tps=1.0)

    saved_eval, saved_sd = L.evaluate, L.source_digest
    L.evaluate = fake_eval
    L.source_digest = _sd_mock("stock")
    try:
        summary = L.run_campaign(
            cfg, [genome], PerfConfig(records=1, threads=1),
            _AUTH_CONTRACT.env_tag, _AUTH_CONTRACT.clocks_per_us,
            numactl=list(_AUTH_CONTRACT.numactl),
            authorization_contract=_AUTHORIZATION,
            do_bench=False, output_root=out_root, log=lambda *_args: None, build_context=_BUILD_CONTEXT,
            declared_use_class="exploration",
        )
    finally:
        L.evaluate, L.source_digest = saved_eval, saved_sd

    expected = exploration_campaign_layout(str(ident.campaign_id(_bound(cfg))), out_root)
    assert summary.layout_root == expected.root
    assert len(evaluated_layouts) == 1
    assert isinstance(evaluated_layouts[0], ExplorationCampaignLayout)
    assert evaluated_layouts[0].root == expected.root
    assert open(expected.namespace_file, "rb").read() == b'{"namespace":"exploration"}\n'
    assert os.path.isfile(expected.lock_file)
    assert os.path.isfile(expected.wal_file)
    assert [record.stage for record in wal.read_records(expected)] == [
        STAGE_BUILD_START, STAGE_COMMIT,
    ]


@pytest.mark.parametrize(
    "declared_use_class", ["qualification", "dry", "unknown"],
)
def test_run_campaign_rejects_unsupported_declared_use_class_before_output_creation(
        declared_use_class, monkeypatch):
    """非 materializing class は cid/layout の前に拒否する。"""
    from orchestrator.campaign import loop as L

    parent = _tmpdir("izanagi_loop_namespace_unknown_")
    out_root = os.path.join(parent, "must-not-exist")
    cfg = CampaignConfig(spec_slug="t", search_tag="enum",
                         spec_content="namespace-unknown", ccbench_commit="deadbeef")
    expected_cid = str(ident.campaign_id(_bound(cfg)))
    cid_calls = []
    original_campaign_id = L.ident.campaign_id

    def campaign_id_spy(*args, **kwargs):
        cid_calls.append((args, kwargs))
        return original_campaign_id(*args, **kwargs)

    monkeypatch.setattr(L.ident, "campaign_id", campaign_id_spy)
    with pytest.raises(ValueError):
        L.run_campaign(
            cfg, [], PerfConfig(records=1, threads=1), "test-env", 1800,
            authorization_contract=_AUTHORIZATION,
            do_bench=False, output_root=out_root, log=lambda *_args: None,
            build_context=_BUILD_CONTEXT,
            declared_use_class=declared_use_class,
        )
    assert cid_calls == []
    assert not os.path.exists(out_root)
    assert not os.path.exists(os.path.join(out_root, "campaigns", expected_cid))


@pytest.mark.usefixtures("ratified_enforcement_source")
def test_run_campaign_declared_use_class_does_not_change_campaign_id():
    """宣言は runtime path selector であり identity preimage へ入らない。"""
    from orchestrator.campaign import loop as L

    out_root = _tmpdir("izanagi_loop_namespace_identity_")
    cfg = CampaignConfig(spec_slug="t", search_tag="enum",
                         spec_content="namespace-identity", ccbench_commit="deadbeef")
    common = (
        cfg, [], PerfConfig(records=1, threads=1),
        _AUTH_CONTRACT.env_tag, _AUTH_CONTRACT.clocks_per_us,
    )
    official = L.run_campaign(
        *common, numactl=list(_AUTH_CONTRACT.numactl),
        authorization_contract=_AUTHORIZATION, do_bench=False,
        output_root=out_root, log=lambda *_args: None,
        build_context=_BUILD_CONTEXT, declared_use_class="official",
    )
    exploration = L.run_campaign(
        *common, numactl=list(_AUTH_CONTRACT.numactl),
        authorization_contract=_AUTHORIZATION, do_bench=False,
        output_root=out_root, log=lambda *_args: None, build_context=_BUILD_CONTEXT,
        declared_use_class="exploration",
    )
    assert official.campaign_id == exploration.campaign_id == str(ident.campaign_id(_bound(cfg)))


@pytest.mark.usefixtures("ratified_enforcement_source")
def test_loop_isolates_failing_genome():
    """1 genome の評価例外が campaign 全体を止めず、abort 記録で terminal 化する。"""
    seen = []

    def fake_eval(g, *a, **kw):
        seen.append(g)
        if g.flags["BACK_OFF"] == 0:
            raise RuntimeError("boom")           # 1 つ目が想定外の例外
        return EvalResult(genome=g, variant=pipeline.variant_id(g),
                          certified=True, aborted=False, fitness_tps=100.0)

    genomes = [Genome("silo", {"BACK_OFF": 0}), Genome("silo", {"BACK_OFF": 1})]
    s, lay = _loop_with_fake_eval(fake_eval, genomes, "isolate")
    assert len(seen) == 2                        # 例外でも 2 つ目を評価 (継続)
    assert s.aborted == 1 and s.committed == 1
    # 例外 variant は WAL に abort 記録 → 再起動で terminal_variants がスキップ
    bad = pipeline.variant_id(genomes[0])
    assert wal.replay(lay, admission_policy=_BUILD_CONTEXT.policy)[bad].aborted


@pytest.mark.usefixtures("ratified_enforcement_source")
def test_loop_dedup_identical_genome_in_one_run():
    """同一 (protocol, flags) の genome が複数あっても 1 run 内で 1 回しか評価しない (U1)。"""
    seen = []

    def fake_eval(g, *a, **kw):
        seen.append(g)
        return EvalResult(genome=g, variant=pipeline.variant_id(g),
                          certified=True, aborted=False, fitness_tps=100.0)

    genomes = [Genome("silo", {"BACK_OFF": 1}), Genome("silo", {"BACK_OFF": 1})]
    s, _ = _loop_with_fake_eval(fake_eval, genomes, "dedup")
    assert len(seen) == 1 and s.skipped == 1 and s.committed == 1
    # skip の確定済み id は summary に露出する (呼び手が revert 後 tree で再 resolve すると
    # stock id = 別 variant を引くため、ここが id の単一確定点 [T-157])
    assert s.skipped_variants == [pipeline.variant_id(genomes[1], "stock")]


@pytest.mark.usefixtures("ratified_enforcement_source")
def test_loop_dedup_uses_src_token_id():
    """coder variant (src_token != stock) で 1run dedup が起き src_token が evaluate に渡る (D24)。
    注: 同一 genome 2 本は stock id でも src_token id でも単一キーに潰れるためこのテストは skip
    キーのスキームを区別しない (dedup が起きる + src_token 伝播のみ確認)。skip キーが src_token id
    であること自体の load-bearing 検査は test_loop_recovery_skips_committed_src_token_variant
    (WAL の src_token id terminal で skip = 旧 stock-id 判定なら fail) が担う。"""
    seen = []

    def fake_eval(g, *a, src_token=None, **kw):
        seen.append(src_token)
        return EvalResult(genome=g, variant=pipeline.variant_id(g, src_token),
                          certified=True, aborted=False, fitness_tps=100.0)

    genomes = [Genome("silo", {"BACK_OFF": 1}), Genome("silo", {"BACK_OFF": 1})]
    s, _ = _loop_with_fake_eval(fake_eval, genomes, "srctok-dedup", src_token="codediff")
    assert len(seen) == 1 and seen[0] == "codediff"      # 1 回評価 + src_token が evaluate へ
    assert s.skipped == 1 and s.committed == 1
    assert s.skipped_variants == [pipeline.variant_id(genomes[1], "codediff")]  # [T-157]


def test_loop_recovery_skips_committed_src_token_variant():
    """WAL に src_token id で commit 済みの variant は再起動で skip する (リカバリ冪等 D, [HIGH])。
    旧実装は loop が stock id で skip 判定し WAL の src_token id terminal と一致せず再評価していた。
    fake_eval は commit WAL を書かないので、前回 run の成果を WAL に直接 seed して模す。"""
    from orchestrator.campaign import loop as L
    out_root = _tmpdir("izanagi_loop_recov_")
    cfg = CampaignConfig(spec_slug="t", search_tag="enum",
                         spec_content="recov", ccbench_commit="deadbeef")
    g = Genome("silo", {"BACK_OFF": 1})
    src_id = pipeline.variant_id(g, "codediff")
    assert src_id != pipeline.variant_id(g)              # src_token id ≠ stock id
    # 前回 run の成果を WAL に seed: src_token id で commit 済み (terminal)
    lay = campaign_layout(str(ident.campaign_id(_bound(cfg))), out_root).ensure()
    _write_certified_lock(lay, _bound(cfg))
    _write_receiptful_attempt(
        lay, g, src_id, attempt_id="recovery-codediff",
        terminal=STAGE_COMMIT,
    )

    calls = []

    def fake_eval(g, *a, **kw):
        calls.append(g)
        return EvalResult(genome=g, variant=src_id, certified=True, aborted=False)

    saved, saved_sd = L.evaluate, L.source_digest
    L.evaluate = fake_eval
    L.source_digest = _sd_mock("codediff")
    try:
        s = L.run_campaign(
            cfg, [g], PerfConfig(records=1, threads=1),
            _AUTH_CONTRACT.env_tag, _AUTH_CONTRACT.clocks_per_us,
            numactl=list(_AUTH_CONTRACT.numactl),
            authorization_contract=_AUTHORIZATION,
            do_bench=False, output_root=out_root, log=lambda *a: None,
            build_context=_BUILD_CONTEXT, declared_use_class="official")
    finally:
        L.evaluate, L.source_digest = saved, saved_sd
    assert len(calls) == 0 and s.skipped == 1            # src_token id terminal → 再評価しない
    # リカバリ skip = 重複提案の実体。呼び手 (_resolve_duplicate) はこの確定済み id だけを
    # 使う — revert 後 tree の再 resolve は stock id = 別 variant を引く ([T-157])
    assert s.skipped_variants == [src_id]


def test_replay_accepts_matching_contract_bound_commit_and_skips_evaluation():
    """lock=H_A/全COMMIT=H_A は terminal skip し evaluate/build を呼ばない。"""
    from orchestrator.campaign import loop as L

    out_root = _tmpdir("t530_matching_resume_")
    cfg = CampaignConfig(
        spec_slug="t530", search_tag="resume",
        spec_content="matching contract-bound resume", ccbench_commit="deadbeef",
    )
    bound = ident.bind_environment_contract(
        ident.bind_admission_policy(cfg, _BUILD_CONTEXT.policy),
        _AUTH_CONTRACT,
    )
    genome_value = Genome("silo", {"BACK_OFF": 1})
    variant = pipeline.variant_id(genome_value, "stock")
    layout = campaign_layout(str(ident.campaign_id(bound)), out_root).ensure()
    _write_certified_lock(layout, bound)
    _write_receiptful_attempt(
        layout, genome_value, variant,
        attempt_id="matching-contract-attempt", terminal=STAGE_COMMIT,
        contract=_AUTH_CONTRACT,
    )
    calls = {"evaluate": 0, "build": 0}

    def forbidden_evaluate(*_args, **_kwargs):
        calls["evaluate"] += 1
        raise AssertionError("terminal resume must not evaluate")

    def forbidden_build(*_args, **_kwargs):
        calls["build"] += 1
        raise AssertionError("terminal resume must not build")

    saved_eval = L.evaluate
    saved_build = L.buildcache.build
    saved_source_digest = L.source_digest
    L.evaluate = forbidden_evaluate
    L.buildcache.build = forbidden_build
    L.source_digest = _sd_mock("stock")
    try:
        summary = L.run_campaign(
            cfg, [genome_value], PerfConfig(records=1, threads=1),
            _AUTH_CONTRACT.env_tag, _AUTH_CONTRACT.clocks_per_us,
            numactl=list(_AUTH_CONTRACT.numactl),
            authorization_contract=_AUTHORIZATION,
            do_bench=False, output_root=out_root,
            log=lambda _message: None, build_context=_BUILD_CONTEXT,
            declared_use_class="official",
        )
    finally:
        L.evaluate = saved_eval
        L.buildcache.build = saved_build
        L.source_digest = saved_source_digest
    assert calls == {"evaluate": 0, "build": 0}
    assert summary.skipped == 1 and summary.evaluated == 0


@pytest.mark.usefixtures("ratified_enforcement_source")
def test_loop_isolates_identity_error():
    """source_digest.resolve が確定不能 (RuntimeError) なら loop が stock id で abort 隔離し継続。"""
    def fake_eval(g, *a, **kw):
        raise AssertionError("identity-error 時は evaluate を呼ばない")

    genomes = [Genome("silo", {"BACK_OFF": 0}), Genome("silo", {"BACK_OFF": 1})]
    s, lay = _loop_with_fake_eval(fake_eval, genomes, "id-err",
                                  src_token=RuntimeError("g++ 不在"))
    assert s.aborted == 2 and s.committed == 0 and s.evaluated == 2
    st = wal.replay(lay, admission_policy=_BUILD_CONTEXT.policy)
    for g in genomes:
        assert st[pipeline.variant_id(g)].aborted        # identity 不明ゆえ stock id で abort


@pytest.mark.usefixtures("ratified_enforcement_source")
def test_loop_identity_error_is_retryable_after_repair():
    """identity-error abort (transient) は permanent skip でなく環境修復後に再評価される (D25)。
    旧挙動は stock id terminal abort → 永久 skip で stock baseline を silently drop していた。"""
    from orchestrator.campaign import loop as L
    out_root = _tmpdir("izanagi_loop_iderr_")
    cfg = CampaignConfig(spec_slug="t", search_tag="enum",
                         spec_content="id-retry", ccbench_commit="deadbeef")
    g = Genome("silo", {"BACK_OFF": 1})
    calls = []

    def fake_eval(g, *a, **kw):
        calls.append(g)
        return EvalResult(genome=g, variant=pipeline.variant_id(g, kw.get("src_token")),
                          certified=True, aborted=False, fitness_tps=100.0)

    saved, saved_sd = L.evaluate, L.source_digest
    L.evaluate = fake_eval
    try:
        # run1: resolve が RuntimeError (g++ 一時不在) → identity-error abort (evaluate 呼ばれず)
        L.source_digest = _sd_mock(RuntimeError("g++ 一時不在"))
        s1 = L.run_campaign(
            cfg, [g], PerfConfig(records=1, threads=1),
            _AUTH_CONTRACT.env_tag, _AUTH_CONTRACT.clocks_per_us,
            numactl=list(_AUTH_CONTRACT.numactl),
            authorization_contract=_AUTHORIZATION,
            do_bench=False, output_root=out_root, log=lambda *a: None,
            build_context=_BUILD_CONTEXT, declared_use_class="official")
        assert s1.aborted == 1 and len(calls) == 0
        # run2: 環境修復 (resolve 成功 → stock) → 永久 skip でなく再評価・commit
        L.source_digest = _sd_mock("stock")
        s2 = L.run_campaign(
            cfg, [g], PerfConfig(records=1, threads=1),
            _AUTH_CONTRACT.env_tag, _AUTH_CONTRACT.clocks_per_us,
            numactl=list(_AUTH_CONTRACT.numactl),
            authorization_contract=_AUTHORIZATION,
            do_bench=False, output_root=out_root, log=lambda *a: None,
            build_context=_BUILD_CONTEXT, declared_use_class="official")
    finally:
        L.evaluate, L.source_digest = saved, saved_sd
    assert len(calls) == 1 and s2.committed == 1 and s2.skipped == 0   # 修復後に再評価


def test_loop_identity_error_retryable_survives_inflight_crash():
    """identity-error abort → 修復後の再評価が in-flight クラッシュ (BUILD_START のみで
    途切れ) しても、次 run で再評価される (D25 の保証がクラッシュ 1 回で破れない)。

    旧実装は retryable 判定が st.last (最終レコード) 依存だったため、BUILD_START が
    最後になると判定から漏れ、aborted の粘着により permanent skip が復活していた
    (洗練検査 2026-07-02 HIGH)。overnight クラッシュ→再起動は WAL の設計前提。"""
    from orchestrator.campaign import loop as L
    out_root = _tmpdir("izanagi_loop_iderr_crash_")
    cfg = CampaignConfig(spec_slug="t", search_tag="enum",
                         spec_content="id-retry-crash", ccbench_commit="deadbeef")
    g = Genome("silo", {"BACK_OFF": 1})
    v_stock = pipeline.variant_id(g)
    lay = campaign_layout(str(ident.campaign_id(_bound(cfg))), out_root).ensure()
    _write_certified_lock(lay, _bound(cfg))
    # run1: identity-error abort (stock id)
    _write_prebuild_abort(
        lay, g, v_stock, attempt_id="identity-error-1",
        reason="identity-error",
    )
    # run2: 修復後の再評価が BUILD_START を書いた直後にクラッシュ (COMMIT/ABORT なし)
    wal.log(lay, v_stock, STAGE_BUILD_START, "test-env", {
        "genome": g.canonical(), "build_attempt_id": "identity-crash-2",
    })

    calls = []

    def fake_eval(g, *a, **kw):
        calls.append(g)
        return EvalResult(genome=g, variant=pipeline.variant_id(g, kw.get("src_token")),
                          certified=True, aborted=False, fitness_tps=100.0)

    saved, saved_sd = L.evaluate, L.source_digest
    L.evaluate = fake_eval
    L.source_digest = _sd_mock("stock")
    try:
        # run3: 環境修復済み → retryable 判定は last_terminal (identity-error abort) 基準
        # なので再評価される (旧実装は evaluated=0 / skipped=1 で永久 skip)
        s3 = L.run_campaign(
            cfg, [g], PerfConfig(records=1, threads=1),
            _AUTH_CONTRACT.env_tag, _AUTH_CONTRACT.clocks_per_us,
            numactl=list(_AUTH_CONTRACT.numactl),
            authorization_contract=_AUTHORIZATION,
            do_bench=False, output_root=out_root,
                            log=lambda *a: None, build_context=_BUILD_CONTEXT,
                            declared_use_class="official")
    finally:
        L.evaluate, L.source_digest = saved, saved_sd
    assert len(calls) == 1 and s3.committed == 1 and s3.skipped == 0


@pytest.mark.usefixtures("ratified_enforcement_source")
def test_loop_resume_recovery_aborts_real_pipeline_crash_after_start():
    """実 evaluate/WAL writer の start→process death→resume 境界を通す。"""
    from orchestrator.campaign import artifact_admission
    from orchestrator.campaign import loop as L

    class ProcessCrash(BaseException):
        pass

    out_root = _tmpdir("izanagi_loop_real_writer_recovery_")
    cfg = CampaignConfig(
        spec_slug="t", search_tag="enum", spec_content="real-writer-recovery",
        ccbench_commit="deadbeef",
    )
    genome_value = Genome("silo", {"BACK_OFF": 1})
    saved_source_digest = L.source_digest
    try:
        with _mock_pipeline(certified=True):
            L.source_digest = pipeline.source_digest
            real_build = pipeline.buildcache.build

            def crash_after_start(*_args, **_kwargs):
                raise ProcessCrash("simulated process death after fsynced start")

            pipeline.buildcache.build = crash_after_start
            try:
                try:
                    L.run_campaign(
                        cfg, [genome_value], PerfConfig(records=1, threads=1),
                        _AUTH_CONTRACT.env_tag, _AUTH_CONTRACT.clocks_per_us,
                        numactl=list(_AUTH_CONTRACT.numactl),
                        authorization_contract=_AUTHORIZATION, do_bench=False,
                        output_root=out_root, log=lambda *_args: None,
                        build_context=_BUILD_CONTEXT,
                        declared_use_class="official",
                    )
                    assert False, "BaseException crash が loop を脱出すべき"
                except ProcessCrash:
                    pass
            finally:
                pipeline.buildcache.build = real_build

            lay = campaign_layout(
                str(ident.campaign_id(_bound(cfg))), out_root,
            )
            before_recovery = open(lay.wal_file, "rb").read()
            first_records = wal.read_records(lay)
            assert [record.stage for record in first_records] == [STAGE_BUILD_START]

            summary = L.run_campaign(
                cfg, [genome_value], PerfConfig(records=1, threads=1),
                _AUTH_CONTRACT.env_tag, _AUTH_CONTRACT.clocks_per_us,
                numactl=list(_AUTH_CONTRACT.numactl),
                authorization_contract=_AUTHORIZATION, do_bench=False,
                output_root=out_root, log=lambda *_args: None,
                build_context=_BUILD_CONTEXT, declared_use_class="official",
            )
    finally:
        L.source_digest = saved_source_digest

    records = wal.read_records(lay)
    assert [record.stage for record in records] == [
        STAGE_BUILD_START, STAGE_ABORT, STAGE_BUILD_START,
        STAGE_BUILD_DONE, STAGE_VERIFY_DONE, STAGE_COMMIT,
    ]
    first_start, recovery_abort, retry_start = records[:3]
    assert first_start.payload["build_attempt_id"] != \
        retry_start.payload["build_attempt_id"]
    assert recovery_abort.payload == {
        "reason": "recovery-abort-incomplete-attempt",
        "build_attempt_id": first_start.payload["build_attempt_id"],
        "build_admission_receipt_sha256":
            first_start.payload["build_admission_receipt_sha256"],
    }
    assert open(lay.wal_file, "rb").read().startswith(before_recovery)
    replayed = wal.replay(lay, admission_policy=_BUILD_CONTEXT.policy)
    state = replayed[first_start.variant]
    assert state.attempts[first_start.payload["build_attempt_id"]].aborted
    assert state.attempts[retry_start.payload["build_attempt_id"]].committed
    assert summary.committed == 1 and summary.skipped == 0
    admitted = artifact_admission.require_admitted_campaign(
        lay,
        purpose=artifact_admission.CampaignReadPurpose.HISTORICAL_RAW,
    )
    assert admitted.decision.admitted


def test_loop_identity_skip_is_visible_when_stock_id_terminal():
    """identity 確定不能かつ stock id が terminal 済みのときの skip は identity_skipped
    として summary に分離カウントされる (規律3: 成果物からの欠落を沈黙させない)。"""
    from orchestrator.campaign import loop as L
    out_root = _tmpdir("izanagi_loop_idskip_")
    cfg = CampaignConfig(spec_slug="t", search_tag="enum",
                         spec_content="id-skip-vis", ccbench_commit="deadbeef")
    g = Genome("silo", {"BACK_OFF": 1})
    v_stock = pipeline.variant_id(g)
    lay = campaign_layout(str(ident.campaign_id(_bound(cfg))), out_root).ensure()
    _write_certified_lock(lay, _bound(cfg))
    # 過去 run で stock id が commit 済み (coder variant の working-tree で再開する状況)
    _write_receiptful_attempt(
        lay, g, v_stock, attempt_id="identity-skip-commit",
        terminal=STAGE_COMMIT,
    )

    saved_sd = L.source_digest
    L.source_digest = _sd_mock(RuntimeError("git 一時故障"))
    try:
        s = L.run_campaign(
            cfg, [g], PerfConfig(records=1, threads=1),
            _AUTH_CONTRACT.env_tag, _AUTH_CONTRACT.clocks_per_us,
            numactl=list(_AUTH_CONTRACT.numactl),
            authorization_contract=_AUTHORIZATION,
            do_bench=False, output_root=out_root,
                           log=lambda *a: None, build_context=_BUILD_CONTEXT,
                           declared_use_class="official")
    finally:
        L.source_digest = saved_sd
    assert s.skipped == 1 and s.identity_skipped == 1 and s.evaluated == 0
    # id 未確定の skip は skipped_variants に積まない (捏造 id を下流へ流さない [T-157])
    assert s.skipped_variants == []


# ===== STAGE2: provenance / path 防御 =====

def test_buildcache_rejects_commit_mismatch():
    """宣言 ccbench_commit が submodule 実 HEAD とずれたら停止 (偽キャッシュヒット防止)。"""
    sub = buildcache._ccbench_dir()
    if not os.path.exists(os.path.join(sub, ".git")):
        skip("submodule 未 init")
    try:
        buildcache._verify_ccbench_commit(sub, "0000000deadbeef")
        assert False, "誤 commit 文字列で停止すべき"
    except RuntimeError:
        pass


def test_layout_rejects_path_traversal():
    """campaign_id にパス区切り/相対参照が混じると output/campaigns/ の外へ出る → 弾く。"""
    for bad in ("../evil", "a/b", "..", "", ".", ".hidden"):
        try:
            campaign_layout(bad, output_root="/tmp/izanagi_x")
            assert False, f"不正 id を弾くべき: {bad!r}"
        except ValueError:
            pass
    campaign_layout("readheavy-enum-abcd1234", output_root="/tmp/izanagi_x")  # 正常は通る


def test_exploration_output_root_env_precedence_and_official_isolation():
    """M1/M2: exploration だけが explicit > env > legacy default を使う。"""
    sentinel = object()
    saved_env = os.environ.get(layout_module._EXPLORATION_OUTPUT_ROOT_ENV, sentinel)
    saved_repo_output_root = layout_module.repo_output_root
    layout_module._reset_exploration_output_root_pin_for_tests()
    try:
        os.environ.pop(layout_module._EXPLORATION_OUTPUT_ROOT_ENV, None)
        legacy = os.path.join(saved_repo_output_root(), "..", "output")
        layout_module.repo_output_root = lambda: legacy
        default_layout = exploration_campaign_layout("env-default")
        assert default_layout.root == os.path.join(
            legacy, "exploration", "campaigns", "env-default",
        )
        layout_module.repo_output_root = saved_repo_output_root

        external = _tmpdir("izanagi_exploration_env_")
        os.environ[layout_module._EXPLORATION_OUTPUT_ROOT_ENV] = external
        first = exploration_campaign_layout("env-first")
        second = exploration_campaign_layout("env-second")
        assert first.root == os.path.join(
            external, "exploration", "campaigns", "env-first",
        )
        assert os.path.dirname(os.path.dirname(first.root)) == os.path.join(
            external, "exploration",
        )
        assert os.path.dirname(os.path.dirname(second.root)) == os.path.join(
            external, "exploration",
        )
        with pytest.raises(ValueError, match="official output_root"):
            campaign_layout("official-isolated")

        os.environ[layout_module._EXPLORATION_OUTPUT_ROOT_ENV] = ""
        explicit = "legacy-relative-explicit-root"
        explicit_layout = exploration_campaign_layout(
            "explicit-wins", output_root=explicit,
        )
        assert explicit_layout.root == os.path.join(
            explicit, "exploration", "campaigns", "explicit-wins",
        )
    finally:
        layout_module.repo_output_root = saved_repo_output_root
        layout_module._reset_exploration_output_root_pin_for_tests()
        if saved_env is sentinel:
            os.environ.pop(layout_module._EXPLORATION_OUTPUT_ROOT_ENV, None)
        else:
            os.environ[layout_module._EXPLORATION_OUTPUT_ROOT_ENV] = saved_env


def test_official_output_root_requires_external_root_and_supports_env(tmp_path):
    """Official roots fail closed when unset and resolve only a validated env root."""
    env_name = layout_module._OFFICIAL_OUTPUT_ROOT_ENV
    layout_module._reset_official_output_root_pin_for_tests()
    try:
        os.environ.pop(env_name, None)
        with pytest.raises(ValueError, match="official output_root"):
            campaign_layout("official-missing-root")

        external = tmp_path / "official-output"
        os.environ[env_name] = str(external)
        first = campaign_layout("official-env-root")
        assert first.root == str(external / "campaigns" / "official-env-root")
        assert Path(first.root).parent.parent == external.resolve()
    finally:
        layout_module._reset_official_output_root_pin_for_tests()


def test_official_output_root_explicit_value_is_validated_and_suffixes_are_not_exempt(
        tmp_path,
):
    """Explicit roots and campaigns/env suffixes go through the same external gate."""
    repository = Path(layout_module.repo_output_root())
    with pytest.raises(ValueError, match="official output_root"):
        campaign_layout("official-repo-explicit", output_root=str(repository))
    with pytest.raises(ValueError, match="official output_root"):
        campaign_layout(
            "official-repo-campaigns", output_root=str(repository / "campaigns"),
        )
    with pytest.raises(ValueError, match="official output_root"):
        campaign_layout(
            "official-repo-env", output_root=str(repository / "env"),
        )

    suffix_root = tmp_path / "suffix-target"
    suffix_root.mkdir()
    (suffix_root / "campaigns").symlink_to(tmp_path, target_is_directory=True)
    with pytest.raises(ValueError, match="symlink component"):
        campaign_layout("official-suffix-symlink", output_root=str(suffix_root))


def test_official_output_root_rejects_unsafe_values(tmp_path):
    """Official resolver mirrors the exploration symlink, dotdot, git, uid, and worktree gates."""
    env_name = layout_module._OFFICIAL_OUTPUT_ROOT_ENV
    layout_module._reset_official_output_root_pin_for_tests()

    def rejected(value, *, match="official output_root"):
        os.environ[env_name] = os.fspath(value)
        with pytest.raises(ValueError, match=match):
            campaign_layout("official-unsafe")

    try:
        rejected("")
        rejected("relative/output")
        rejected(tmp_path / "missing" / ".." / "resolved")

        repository = Path(layout_module.repo_output_root()).parent
        rejected(repository / "output")

        foreign_repo = tmp_path / "foreign-repo"
        (foreign_repo / ".git").mkdir(parents=True)
        rejected(foreign_repo / "output")

        symlink_target = tmp_path / "symlink-target"
        symlink_parent = tmp_path / "symlink-parent"
        symlink_parent.mkdir()
        (symlink_parent / "base-link").symlink_to(
            symlink_target, target_is_directory=True,
        )
        rejected(symlink_parent / "base-link")

        non_directory = tmp_path / "not-a-directory"
        non_directory.write_text("fixture\n", encoding="utf-8")
        rejected(non_directory)

        foreign_owner = tmp_path / "foreign-owner"
        foreign_owner.mkdir()
        saved_effective_uid = layout_module._effective_uid
        layout_module._effective_uid = lambda: foreign_owner.stat().st_uid + 1
        try:
            rejected(foreign_owner)
        finally:
            layout_module._effective_uid = saved_effective_uid

        container = tmp_path / ".codex" / "worktrees" / "wave" / "official"
        rejected(container, match="worktree container")
    finally:
        layout_module._reset_official_output_root_pin_for_tests()


def test_official_output_root_process_pin_rejects_drift(tmp_path):
    """Env-derived official roots are pinned for the process lifetime."""
    env_name = layout_module._OFFICIAL_OUTPUT_ROOT_ENV
    first = tmp_path / "official-pin-first"
    second = tmp_path / "official-pin-second"
    layout_module._reset_official_output_root_pin_for_tests()
    try:
        os.environ[env_name] = str(first)
        assert layout_module._resolve_official_output_root() == str(first.resolve())
        os.environ[env_name] = str(second)
        with pytest.raises(ValueError, match="process 内で変更"):
            layout_module._resolve_official_output_root()

        layout_module._reset_official_output_root_pin_for_tests()
        assert layout_module._resolve_official_output_root() == str(second.resolve())
        os.environ.pop(env_name)
        with pytest.raises(ValueError, match="process 内で変更"):
            layout_module._resolve_official_output_root()
    finally:
        layout_module._reset_official_output_root_pin_for_tests()


def test_exploration_output_root_env_rejects_unsafe_values():
    """M3/M4/M5: env root は fail-fast admission を満たす場合だけ受理する。"""
    from pathlib import Path

    sentinel = object()
    env_name = layout_module._EXPLORATION_OUTPUT_ROOT_ENV
    saved_env = os.environ.get(env_name, sentinel)
    layout_module._reset_exploration_output_root_pin_for_tests()

    def rejected(value):
        os.environ[env_name] = os.fspath(value)
        try:
            exploration_campaign_layout("unsafe-env")
            assert False, f"unsafe env root を拒否すべき: {value!r}"
        except ValueError:
            pass

    try:
        rejected("")
        rejected("relative/output")

        repository = Path(layout_module.repo_output_root()).parent
        rejected(repository)
        rejected(repository / "output" / "nested")

        foreign_repo = Path(_tmpdir("izanagi_foreign_repo_"))
        (foreign_repo / ".git").mkdir()
        rejected(foreign_repo / "output")
        assert not (foreign_repo / "output").exists()

        symlink_parent = Path(_tmpdir("izanagi_env_symlink_parent_"))
        symlink_target = Path(_tmpdir("izanagi_env_symlink_target_"))
        base_link = symlink_parent / "base-link"
        base_link.symlink_to(symlink_target, target_is_directory=True)
        rejected(base_link)
        rejected(base_link / "child")

        suffix_root = Path(_tmpdir("izanagi_env_suffix_symlink_"))
        (suffix_root / "exploration").mkdir()
        (suffix_root / "exploration" / "campaigns").symlink_to(
            symlink_target, target_is_directory=True,
        )
        rejected(suffix_root)

        autonomous_suffix_root = Path(_tmpdir("izanagi_env_8c_suffix_symlink_"))
        (autonomous_suffix_root / "exploration").mkdir()
        (autonomous_suffix_root / "exploration" / "autonomous-trials").symlink_to(
            symlink_target, target_is_directory=True,
        )
        rejected(autonomous_suffix_root)

        dotdot_root = (
            Path(_tmpdir("izanagi_env_dotdot_"))
            / "missing" / ".." / "resolved-base"
        )
        rejected(dotdot_root)

        non_directory = Path(_tmpdir("izanagi_env_non_directory_")) / "file"
        non_directory.write_text("not a directory\n", encoding="utf-8")
        rejected(non_directory)

        foreign_owner = Path(_tmpdir("izanagi_env_foreign_owner_"))
        saved_effective_uid = layout_module._effective_uid
        layout_module._effective_uid = lambda: foreign_owner.stat().st_uid + 1
        try:
            rejected(foreign_owner)
        finally:
            layout_module._effective_uid = saved_effective_uid
    finally:
        layout_module._reset_exploration_output_root_pin_for_tests()
        if saved_env is sentinel:
            os.environ.pop(env_name, None)
        else:
            os.environ[env_name] = saved_env


def test_exploration_output_root_env_resolves_worktree_container_before_ensure(
        tmp_path, monkeypatch,
):
    """D158: exploration は resolve 時でなく ensure 時に worktree を拒否する。"""
    worktree_container = tmp_path / ".codex" / "worktrees" / "wave"
    monkeypatch.setenv(
        layout_module._EXPLORATION_OUTPUT_ROOT_ENV,
        os.fspath(worktree_container),
    )
    layout_module._reset_exploration_output_root_pin_for_tests()
    try:
        assert layout_module._resolve_exploration_output_root() == str(
            worktree_container.resolve()
        )
    finally:
        layout_module._reset_exploration_output_root_pin_for_tests()


def test_exploration_output_root_env_process_pin_rejects_drift():
    """env 由来 root は raw 設定と解決値を process 内で固定する。"""
    sentinel = object()
    env_name = layout_module._EXPLORATION_OUTPUT_ROOT_ENV
    saved_env = os.environ.get(env_name, sentinel)
    first = _tmpdir("izanagi_exploration_pin_first_")
    second = _tmpdir("izanagi_exploration_pin_second_")
    layout_module._reset_exploration_output_root_pin_for_tests()
    try:
        os.environ[env_name] = first
        assert layout_module._resolve_exploration_output_root() == first
        os.environ[env_name] = second
        try:
            layout_module._resolve_exploration_output_root()
            assert False, "process 中の env root drift を拒否すべき"
        except ValueError:
            pass

        layout_module._reset_exploration_output_root_pin_for_tests()
        assert layout_module._resolve_exploration_output_root() == second
        os.environ.pop(env_name)
        try:
            layout_module._resolve_exploration_output_root()
            assert False, "pinned env の削除を拒否すべき"
        except ValueError:
            pass
    finally:
        layout_module._reset_exploration_output_root_pin_for_tests()
        if saved_env is sentinel:
            os.environ.pop(env_name, None)
        else:
            os.environ[env_name] = saved_env


def test_exploration_output_root_pin_rejects_env_removal_before_legacy_fallback():
    """pin 後の env 削除は reset なしで legacy base へ切り替えられない。"""
    sentinel = object()
    env_name = layout_module._EXPLORATION_OUTPUT_ROOT_ENV
    saved_env = os.environ.get(env_name, sentinel)
    first = _tmpdir("izanagi_exploration_pin_removed_")
    legacy = os.path.join(_tmpdir("izanagi_exploration_legacy_"), "output")
    layout_module._reset_exploration_output_root_pin_for_tests()
    try:
        os.environ[env_name] = first
        assert layout_module._resolve_exploration_output_root(
            legacy_base=legacy,
        ) == first
        os.environ.pop(env_name)
        try:
            layout_module._resolve_exploration_output_root(legacy_base=legacy)
            assert False, "pinned env 削除後の legacy fallback を拒否すべき"
        except ValueError:
            pass
    finally:
        layout_module._reset_exploration_output_root_pin_for_tests()
        if saved_env is sentinel:
            os.environ.pop(env_name, None)
        else:
            os.environ[env_name] = saved_env


def test_exploration_output_root_pin_is_shared_and_locked_across_aliases():
    """二重 module identity でも pin と原子化 lock は process 内で一つ。"""
    sentinel = object()
    env_name = layout_module._EXPLORATION_OUTPUT_ROOT_ENV
    saved_env = os.environ.get(env_name, sentinel)
    saved_sys_path = sys.path[:]
    try:
        sys.path.insert(0, _ORCH)
        alternate = importlib.import_module("campaign.layout")
    finally:
        sys.path[:] = saved_sys_path
    first = _tmpdir("izanagi_alias_pin_first_")
    second = _tmpdir("izanagi_alias_pin_second_")
    layout_module._reset_exploration_output_root_pin_for_tests()
    try:
        assert alternate is not layout_module
        assert (
            alternate._exploration_output_root_state
            is layout_module._exploration_output_root_state
        )
        os.environ[env_name] = first
        assert layout_module._resolve_exploration_output_root() == first
        os.environ[env_name] = second
        try:
            alternate._resolve_exploration_output_root()
            assert False, "別 alias からの process root drift を拒否すべき"
        except ValueError:
            pass

        layout_module._reset_exploration_output_root_pin_for_tests()
        os.environ[env_name] = first
        state = layout_module._exploration_output_root_state
        started = threading.Event()
        finished = threading.Event()
        results = []
        errors = []

        def resolve_in_thread():
            started.set()
            try:
                results.append(alternate._resolve_exploration_output_root())
            except Exception as exc:  # noqa: BLE001 - thread result is asserted below
                errors.append(exc)
            finally:
                finished.set()

        state["lock"].acquire()
        worker = threading.Thread(target=resolve_in_thread)
        try:
            worker.start()
            assert started.wait(1.0)
            assert not finished.wait(0.05), "resolver は process lock 内で動くべき"
        finally:
            state["lock"].release()
        worker.join(5.0)
        assert not worker.is_alive()
        assert errors == []
        assert results == [first]
    finally:
        layout_module._reset_exploration_output_root_pin_for_tests()
        if saved_env is sentinel:
            os.environ.pop(env_name, None)
        else:
            os.environ[env_name] = saved_env


def test_autonomous_trial_env_run_root_and_worktree_container_gate():
    """M7: 8c 省略 root は env base を使い、materialize 前に同じ gate を通る。"""
    from pathlib import Path

    from orchestrator.campaign import p3_autonomous_workload_trial as autonomous

    sentinel = object()
    env_name = layout_module._EXPLORATION_OUTPUT_ROOT_ENV
    saved_env = os.environ.get(env_name, sentinel)
    saved_assert = autonomous.assert_pinned_clean
    saved_run_trial = autonomous.run_trial
    saved_resolver = autonomous._resolve_exploration_output_root
    saved_trial_launch_admission = autonomous._trial_launch_admission
    saved_root = autonomous.ROOT
    external = _tmpdir("izanagi_autonomous_env_")
    captured = {}
    layout_module._reset_exploration_output_root_pin_for_tests()
    try:
        os.environ[env_name] = external
        autonomous.assert_pinned_clean = lambda *_args, **_kwargs: None

        def capture_run_trial(**kwargs):
            captured.update(kwargs)
            return {"status": "complete", "cells": []}

        autonomous.run_trial = capture_run_trial
        assert autonomous.main([
            "--trial-id", "env-root-trial",
            "--provider", "fixture",
            "--no-build",
            "--allow-unregistered-exploratory",
            "--ccbench-dir", os.path.join(external, "ccbench"),
        ]) == 0
        assert captured["run_root"] == Path(
            external, "exploration", "autonomous-trials", "env-root-trial",
        )

        layout_module._reset_exploration_output_root_pin_for_tests()
        os.environ.pop(env_name)
        captured.clear()
        legacy_root = Path(external, "resolved-checkout")
        autonomous.ROOT = legacy_root
        legacy_bases = []
        legacy_admission = autonomous.trial_registry.admit_unregistered_exploratory(
            trial_id="legacy-default-trial",
            workloads=list(autonomous.WORKLOADS),
            allow_unregistered_exploratory=True,
            repository_root=saved_root,
            registry_path=(
                saved_root / autonomous.trial_registry.DEFAULT_REGISTRY_PATH
            ),
        )

        def resolve_legacy(*, legacy_base=""):
            legacy_bases.append(legacy_base)
            return legacy_base

        def admit_legacy(**kwargs):
            assert kwargs["trial_id"] == "legacy-default-trial"
            assert kwargs["allow_unregistered_exploratory"] is True
            return legacy_admission

        autonomous._resolve_exploration_output_root = resolve_legacy
        autonomous._trial_launch_admission = admit_legacy
        assert autonomous.main([
            "--trial-id", "legacy-default-trial",
            "--provider", "fixture",
            "--no-build",
            "--allow-unregistered-exploratory",
            "--ccbench-dir", os.path.join(external, "ccbench"),
        ]) == 0
        assert captured["run_root"] == Path(
            legacy_root, "output", "exploration", "autonomous-trials",
            "legacy-default-trial",
        )
        assert legacy_bases == [str(legacy_root / "output")]

        autonomous.run_trial = saved_run_trial
        autonomous._trial_launch_admission = saved_trial_launch_admission
        autonomous.ROOT = saved_root
        container = Path(
            _tmpdir("izanagi_autonomous_gate_"),
            ".codex", "worktrees", "wave", "trial",
        )
        try:
            autonomous.run_trial(
                trial_id="container-gate",
                workloads=("ycsb-a",),
                generations=1,
                provider_kind="fixture",
                run_root=container,
                sub="unused",
                do_build=False,
                providers={},
                allow_unregistered_exploratory=True,
            )
            assert False, "8c run_root の worktree container を拒否すべき"
        except ValueError as exc:
            assert "worktree container" in str(exc)
            assert env_name in str(exc)
            assert "絶対 path" in str(exc)
            assert "job 専用" in str(exc)
            assert "base は exploration/ 自体ではない" in str(exc)
        assert not container.exists()
    finally:
        autonomous.assert_pinned_clean = saved_assert
        autonomous.run_trial = saved_run_trial
        autonomous._resolve_exploration_output_root = saved_resolver
        autonomous._trial_launch_admission = saved_trial_launch_admission
        autonomous.ROOT = saved_root
        layout_module._reset_exploration_output_root_pin_for_tests()
        if saved_env is sentinel:
            os.environ.pop(env_name, None)
        else:
            os.environ[env_name] = saved_env


def test_wal_materializers_reject_worktree_container_without_layout_ensure():
    """F98: factory 直後の WAL 公開 API も作成前に container を拒否する。"""
    from pathlib import Path

    container = Path(
        _tmpdir("izanagi_wal_gate_"), ".codex", "worktrees", "wave",
    )
    materializers = (
        ("write-lock", lambda item: wal.write_lock(item, "preimage")),
        (
            "log",
            lambda item: wal.log(
                item, "variant", STAGE_ABORT, "test-env", {"reason": "fixture"},
            ),
        ),
        ("atomic-lock", lambda item: wal.acquire_lock_atomic(item, "preimage")),
    )
    for suffix, materialize in materializers:
        layout = exploration_campaign_layout(
            f"wal-gate-{suffix}", output_root=str(container / suffix),
        )
        try:
            materialize(layout)
            assert False, f"{suffix} は worktree container を拒否すべき"
        except ValueError as exc:
            message = str(exc)
            assert "worktree container" in message
            assert layout_module._EXPLORATION_OUTPUT_ROOT_ENV in message
        assert not Path(layout.root).exists()


def test_wal_materializers_admit_official_layout_in_worktree_container(
    tmp_path=None,
):
    """Official layout の4 materializer は worktree container 内でも書ける。"""
    from pathlib import Path

    with _tmp_dir(tmp_path) as tmp:
        container = tmp / ".codex" / "worktrees" / "wave"

        append_layout = CampaignLayout(root=str(container / "append"))
        wal.log(
            append_layout, "official", STAGE_ABORT, "test-env",
            {"reason": "fixture"},
        )
        assert Path(append_layout.wal_file).is_file()

        write_lock_layout = CampaignLayout(root=str(container / "write-lock"))
        wal.write_lock(write_lock_layout, "official-preimage")
        assert Path(write_lock_layout.lock_file).read_text(
            encoding="utf-8",
        ) == "official-preimage"

        atomic_lock_layout = CampaignLayout(root=str(container / "atomic-lock"))
        assert wal.acquire_lock_atomic(atomic_lock_layout, "atomic-preimage")
        assert Path(atomic_lock_layout.lock_file).read_text(
            encoding="utf-8",
        ) == "atomic-preimage"

        repair_layout = CampaignLayout(root=str(container / "repair"))
        repair_layout.ensure()
        Path(repair_layout.wal_file).write_bytes(b"torn-tail")
        repaired = wal.repair_truncated_tail(repair_layout)
        assert repaired.status == "repaired"
        assert Path(repair_layout.wal_file).read_bytes() == b""
        assert repaired.receipt_path is not None
        assert Path(repaired.receipt_path).is_file()


def test_wal_repair_rejects_exploration_worktree_container(tmp_path=None):
    """Exploration repair は missing WAL でも materialization policy を先に通す。"""
    from pathlib import Path

    with _tmp_dir(tmp_path) as tmp:
        container = tmp / ".codex" / "worktrees" / "wave"
        layout = exploration_campaign_layout(
            "repair-gate", output_root=str(container / "base"),
        )
        try:
            wal.repair_truncated_tail(layout)
            assert False, "exploration WAL repair は container を拒否すべき"
        except ValueError as exc:
            assert "worktree container" in str(exc)
        assert not Path(layout.root).exists()


def test_ensure_exploration_namespace_rejects_worktree_container(tmp_path=None):
    """探索 namespace helper の直呼びも marker 作成前に container を拒否する。"""
    from pathlib import Path

    with _tmp_dir(tmp_path) as tmp:
        root = tmp / ".claude" / "worktrees" / "wave" / "exploration"
        try:
            ensure_exploration_namespace(str(root))
            assert False, "exploration namespace 直呼びは container を拒否すべき"
        except ValueError as exc:
            assert "worktree container" in str(exc)
        assert not root.exists()


def test_exploration_marker_precedes_campaign_directory_creation():
    """campaign directory 作成失敗時にも marker が先に exact bytes で残る。"""
    out_root = _tmpdir("izanagi_exploration_marker_order_")
    layout = exploration_campaign_layout("marker-order", output_root=out_root)
    original_makedirs = layout_module.os.makedirs

    def fail_campaign_root(path, *args, **kwargs):
        if os.path.abspath(os.fspath(path)) == os.path.abspath(layout.root):
            raise OSError("campaign directory creation failed")
        return original_makedirs(path, *args, **kwargs)

    layout_module.os.makedirs = fail_campaign_root
    try:
        try:
            layout.ensure()
            assert False, "campaign directory 作成失敗を伝播すべき"
        except OSError as exc:
            assert str(exc) == "campaign directory creation failed"
    finally:
        layout_module.os.makedirs = original_makedirs
    assert not os.path.exists(layout.root)
    assert os.path.abspath(layout.namespace_file) == layout.namespace_file
    assert open(layout.namespace_file, "rb").read() == b'{"namespace":"exploration"}\n'


def test_ensure_exploration_namespace_enforces_shared_marker_contract():
    """公開 helper は absolute path・exact bytes・symlink 拒否を単一契約で提供する。"""
    root = os.path.join(_tmpdir("izanagi_exploration_helper_"), "journal")
    marker = ensure_exploration_namespace(root)
    assert os.path.isabs(marker)
    assert open(marker, "rb").read() == b'{"namespace":"exploration"}\n'
    assert ensure_exploration_namespace(root) == marker

    with open(marker, "wb") as stream:
        stream.write(b'{"namespace":"official"}\n')
    try:
        ensure_exploration_namespace(root)
        assert False, "exact bytes 不一致を拒否すべき"
    except ValueError as exc:
        assert "exact contract" in str(exc)

    os.unlink(marker)
    target = os.path.join(root, "marker-target.json")
    with open(target, "wb") as stream:
        stream.write(b'{"namespace":"exploration"}\n')
    os.symlink(target, marker)
    try:
        ensure_exploration_namespace(root)
        assert False, "marker symlink を拒否すべき"
    except ValueError as exc:
        assert "symlink" in str(exc)


# ===== レポートが close-call シグナル (near_floor) を surface するか (A2, 規律3) =====

def test_report_verdict_surfaces_near_floor():
    """compare の near_floor (floor 近傍の faster) がレポート文字列に出る (dead wiring 防止)。"""
    from orchestrator.calibrator.stability import Comparison
    from orchestrator.campaign.p2_2_report import _verdict_str
    near = Comparison(verdict="faster", rel_median=0.035, p=0.012, near_floor=True)
    far = Comparison(verdict="faster", rel_median=0.40, p=0.012, near_floor=False)
    assert "cross-run 再現で裏取り要" in _verdict_str(near)
    assert "cross-run 再現で裏取り要" not in _verdict_str(far)


# ---- 素の runner ----

# ===== STAGE3 (Phase 3 identity): source_digest (D23) =====
#
# coder のコード差まで identity を覆う preprocess 後ハッシュ。実 g++/git に依存するので
# submodule 未 init / commit ずれ / working-tree が inert でない場合はスキップする。

# 後方互換 golden: silo 8 genome の variant_id (リファクタ前 = canonical のみハッシュ)。
# これが不変 = 既存 P2-2 WAL / build-variants と整合 (D23)。
_GOLDEN_VID = {
    "silo|BACK_OFF=0,NO_WAIT_LOCKING_IN_VALIDATION=0,NO_WAIT_OF_TICTOC=1,WAL=0": "b971a1d9f80a",
    "silo|BACK_OFF=0,NO_WAIT_LOCKING_IN_VALIDATION=0,NO_WAIT_OF_TICTOC=1,WAL=1": "cea1bcd0fddf",
    "silo|BACK_OFF=0,NO_WAIT_LOCKING_IN_VALIDATION=1,NO_WAIT_OF_TICTOC=0,WAL=0": "5185ee5e6094",
    "silo|BACK_OFF=0,NO_WAIT_LOCKING_IN_VALIDATION=1,NO_WAIT_OF_TICTOC=0,WAL=1": "e290fc7a3795",
    "silo|BACK_OFF=1,NO_WAIT_LOCKING_IN_VALIDATION=0,NO_WAIT_OF_TICTOC=1,WAL=0": "2092e34725c1",
    "silo|BACK_OFF=1,NO_WAIT_LOCKING_IN_VALIDATION=0,NO_WAIT_OF_TICTOC=1,WAL=1": "04c75d95b332",
    "silo|BACK_OFF=1,NO_WAIT_LOCKING_IN_VALIDATION=1,NO_WAIT_OF_TICTOC=0,WAL=0": "db4764543546",
    "silo|BACK_OFF=1,NO_WAIT_LOCKING_IN_VALIDATION=1,NO_WAIT_OF_TICTOC=0,WAL=1": "55af140d2cc6",
}
_PRE_T343_GOLDEN_CK0 = {  # T-343 以前の歴史的 stock cache key
    "silo|BACK_OFF=0,NO_WAIT_LOCKING_IN_VALIDATION=0,NO_WAIT_OF_TICTOC=1,WAL=0": "silo_24dd2f7509_t0",
}
_T343_GOLDEN_CK0 = {
    "silo|BACK_OFF=0,NO_WAIT_LOCKING_IN_VALIDATION=0,NO_WAIT_OF_TICTOC=1,WAL=0": "silo_d7eee324f7_t0",
}
_T816_GOLDEN_CK0 = {
    "silo|BACK_OFF=0,NO_WAIT_LOCKING_IN_VALIDATION=0,NO_WAIT_OF_TICTOC=1,WAL=0": "silo_2b19d78065_t0",
}


def test_source_digest_preimage_join_has_pre_refactor_golden_digests():
    """T-1749: extraction must preserve the old NUL/order/UTF-8 digest exactly."""
    golden = (
        (("alpha", "beta carrot", ""),
         "915b28ce3367127f137e980ca567a3113a63f37b9609add39a8290cbd682b354"),
        (("x",),
         "2d711642b726b04401627ca9fbac32f5c8530fb1903cc4db02258717921a4881"),
        ((),
         "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"),
        (("e-acute", "nihongo"),
         "5d7bf1b0f4579c0244a0d9bca6cf4a5aa800d5f63e1a183963aa944c529ebac7"),
        ((chr(233), chr(26085)),
         "f40dc8347e446af4a45697131fbc865dfef051dce15b903de7253da24b9a84cd"),
        ((chr(101) + chr(769),),
         "bf12767b0f2a56b2190075bae8169f656e3ce8d6357d4aff184bc6c7ea48f9f6"),
    )
    for parts, expected in golden:
        assert source_digest._digest(parts) == expected


def test_source_digest_compute_hashes_the_exported_preimage_bytes():
    preimage = b"T-1749 canonical source preimage fixture"
    expected = hashlib.sha256(preimage).hexdigest()
    original = source_digest.canonical_source_preimage_bytes
    source_digest.canonical_source_preimage_bytes = (
        lambda *_args, **_kwargs: preimage
    )
    try:
        assert source_digest.compute(Genome("silo", {})) == expected
    finally:
        source_digest.canonical_source_preimage_bytes = original


def test_source_preimage_artifact_path_is_proposal_content_addressed():
    proposal_sha256 = hashlib.sha256(b"proposal bytes").hexdigest()
    assert source_digest.source_preimage_artifact_relative_path(
        proposal_sha256
    ) == f"source-bindings/{proposal_sha256}.preimage"
    for invalid in ("", "A" * 64, "0" * 63, "../" + "0" * 64):
        with pytest.raises(ValueError, match="exact lowercase SHA-256"):
            source_digest.source_preimage_artifact_relative_path(invalid)


def _ccbench_head_or_skip():
    """submodule HEAD を返す。未 init なら None (テストをスキップ)。"""
    sub = buildcache._ccbench_dir()
    if not os.path.exists(os.path.join(sub, ".git")):
        return None
    r = subprocess.run(["git", "-C", sub, "rev-parse", "HEAD"],
                       capture_output=True, text=True)
    return r.stdout.strip() if r.returncode == 0 else None


def _submodule_initialized(sub=None) -> bool:
    """external/ccbench submodule が init 済みか (作業ツリー内に .git があるか)。
    未 init の submodule ディレクトリは空 (`.git` 不在) で、init 後は gitlink ファイル
    `.git` を持つ。この 1 点だけが skip と実検査を分ける (README『依存物不在時の skip』)。"""
    sub = sub if sub is not None else buildcache._ccbench_dir()
    return os.path.exists(os.path.join(sub, ".git"))


def _require_ccbench_file(rel):
    """submodule の実ファイル (rel は sub 相対) が要る source_digest テスト用ガード。
    skip は submodule 未 init (external/ccbench に .git が無い) のときだけ。init 済みで
    必須ファイルが欠けている場合は skip せずパスを返し、呼び手が open 等で自然に FAIL する
    — 新 pin がファイルを消した互換性回帰を skip に化けさせないため (README『依存物不在時
    の skip』の精密化)。"""
    sub = buildcache._ccbench_dir()
    if not _submodule_initialized(sub):
        skip("submodule 未 init (external/ccbench に .git 無し) — source_digest は実 ccbench ソースが要る")
    return os.path.join(sub, rel)


def test_require_ccbench_file_skips_only_on_uninitialized_submodule(tmp_path=None):
    """所見 A の positive control: skip 判定は submodule の init 状態だけで決まる。
    init 済みで必須ファイルが欠落 (新 pin がファイルを削除した互換性回帰) しても skip せず、
    呼び手が自然に FAIL できる。init/未 init を偽 submodule 構造で切り替えて区別を実測する。
    guard を旧 fail-open (ファイル欠落なら skip) へ退行させると (2) で skip に化けるため、
    その skip を AssertionError に変換して発火させる (skip に化けても素通りさせない)。"""
    saved = buildcache._ccbench_dir
    # skiputil.skip は pytest 配下では pytest.skip (Skipped) を、素の runner では custom Skip を
    # 投げる。ここでは skip 判定そのものを検査対象にするので PYTEST_CURRENT_TEST を一時退避し、
    # どちらの runner でも custom Skip に統一する — 統一しないと pytest 側でこの検査自体が (1) の
    # 時点で skip に化け、(2) の positive control (init+missing→no-skip) が一度も走らない。
    saved_env = os.environ.pop("PYTEST_CURRENT_TEST", None)
    with _tmp_dir(tmp_path) as tmp:
        try:
            # (1) 未 init (空 dir・.git 無し): skip する — これが本環境の実状態でもある
            uninit = tmp / "uninit"
            uninit.mkdir()
            buildcache._ccbench_dir = lambda: str(uninit)
            try:
                _require_ccbench_file("cmake/Options.cmake")
                assert False, "未 init submodule では skip すべき"
            except Skip:
                pass

            # (2) init 済み (.git あり) だが必須ファイル欠落: skip せず、存在しないパスを返す
            #     → 呼び手 (open) が FileNotFoundError で自然に FAIL する (skip に化けない)。
            #     旧 fail-open へ退行するとここで skip → AssertionError に変換して発火させる。
            initd = tmp / "initd"
            (initd / "cmake").mkdir(parents=True)
            (initd / ".git").write_text("gitdir: /elsewhere\n")   # gitlink ファイル相当
            buildcache._ccbench_dir = lambda: str(initd)
            try:
                p_missing = _require_ccbench_file("cmake/Options.cmake")
            except Skip:
                raise AssertionError(
                    "init 済み + ファイル欠落で skip してはいけない (fail-open 回帰)")
            assert not os.path.exists(p_missing)                   # 欠落 → open で自然 FAIL

            # (3) init 済み・ファイル存在: 従来どおり実パスを返し実検査が走る (skip しない)
            (initd / "cmake" / "Options.cmake").write_text("set(X 1)\n")
            p_present = _require_ccbench_file("cmake/Options.cmake")
            assert os.path.exists(p_present)
        finally:
            buildcache._ccbench_dir = saved
            if saved_env is not None:
                os.environ["PYTEST_CURRENT_TEST"] = saved_env


def _any_cxx():
    """同一の選択 compiler 内で source-digest の現行関係を検査する。

    compiler 版をまたぐ関係は保証しない。候補が全滅した場合だけ依存物不在として skip する。
    """
    for c in ("g++-13", "g++-12", "g++"):
        if shutil.which(c):
            return c
    skip("C++ toolchain 全滅 (g++-13/g++-12/g++ いずれも PATH に無い)")


def test_source_digest_silo8_variant_id_and_t343_cache_break_are_explicit():
    """variant_id は不変だが legacy cache key は T-343 receipt 束縛で意図的に変わる。"""
    for g in genome.SILO_SPACE.enumerate():
        assert pipeline.variant_id(g) == _GOLDEN_VID[g.canonical()], g.canonical()
    # cache_key は純関数 (ccbench_commit を pre-image に織り込む・working-tree 非依存)。
    # golden は kickoff pin (dff0f1e) で計算された値なので、live HEAD ではなくその固定 pin
    # で導出を検証する — 後続段 3 の pin 前進 (028f34d, D38) で cache_key が変わるのは
    # 設計どおり (content-addressed identity は pin と共に動く) で、backward-compat golden は
    # 「dff0f1e 時点の導出が安定か」を pin 非依存にテストする (裁定12/IDENT-1)。
    g0 = Genome("silo", {"BACK_OFF": 0, "NO_WAIT_LOCKING_IN_VALIDATION": 0,
                         "NO_WAIT_OF_TICTOC": 1, "WAL": 0})
    # commit 軸は歴史的 golden と同じ full pin に固定し、差を admission 成分だけへ帰属する。
    stock_admission = _admission_for(g0, pin.CURRENT_PIN)
    current = buildcache.cache_key(
        g0, pin.KICKOFF_PIN_FULL, False, admission=stock_admission,
    )
    assert current == _T816_GOLDEN_CK0[g0.canonical()]
    assert current not in {
        _PRE_T343_GOLDEN_CK0[g0.canonical()],
        _T343_GOLDEN_CK0[g0.canonical()],
    }


def test_source_digest_parse_options_defaults():
    """Options パース: 既定値・クォート剥がし・空値 unset (D23 finding 対策)。"""
    opts = _require_ccbench_file("cmake/Options.cmake")
    with open(opts, encoding="utf-8") as f:
        d = source_digest.parse_options_defaults(f.read())
    if "BACKOFF_FIXED" not in d:
        skip_conditional_unrun("template patch 未適用: Options.cmake に BACKOFF_FIXED 既定なし")
    assert d["BACKOFF_FIXED"] == "-1" and d["BACK_OFF"] == "1"
    assert "INSERT_READ_DELAY_MS" not in d        # 空値 ("") は除外


def test_source_digest_stock_roundtrip():
    """実 working-tree (inert) で silo 8 genome は src_token='stock' = 旧 id 不変 (後方互換)。"""
    head = _ccbench_head_or_skip()
    if head is None:
        skip("submodule 未 init — src_token roundtrip は実 working-tree が要る")
    cxx = _any_cxx()
    for g in genome.SILO_SPACE.enumerate():
        st = source_digest.src_token(g, head, cxx=cxx)
        assert st == source_digest.STOCK, g.canonical()
        assert pipeline.variant_id(g, st) == pipeline.variant_id(g)


def test_source_digest_fixed_variant_distinct():
    """BACKOFF_FIXED 枝は stock と別 id・値違いも別 id (alias 防止)。-1 は #else=stock。"""
    head = _ccbench_head_or_skip()
    if head is None:
        skip("submodule 未 init — BACKOFF_FIXED digest 分離は実 working-tree が要る")
    wt = source_digest._read(os.path.join(buildcache._ccbench_dir(), "include/backoff.hh"))
    if "#if BACKOFF_FIXED" not in wt:
        # 受入 suite は共有 submodule に template patch の窓を開けないため、
        # BACKOFF_FIXED が参照されない stock checkout では digest 分離を実走しない。
        skip_conditional_unrun("template patch 未適用: backoff.hh に #if BACKOFF_FIXED 無し")
    # 条件付き未実走を先に分類し、窓が開いた後だけ compiler 不在を依存物 skip にする。
    cxx = _any_cxx()
    base = {"BACK_OFF": 1, "NO_WAIT_LOCKING_IN_VALIDATION": 1,
            "NO_WAIT_OF_TICTOC": 0, "WAL": 0}
    g50 = Genome("silo", {**base, "BACKOFF_FIXED": 50})
    g10 = Genome("silo", {**base, "BACKOFF_FIXED": 10})
    gm1 = Genome("silo", {**base, "BACKOFF_FIXED": -1})
    t50, t10, tm1 = (
        source_digest.src_token(x, head, cxx=cxx) for x in (g50, g10, gm1)
    )
    assert tm1 == source_digest.STOCK             # -1 は #else = stock 枝に正規化
    assert t50 != source_digest.STOCK and t10 != source_digest.STOCK and t50 != t10
    assert pipeline.variant_id(g50, t50) != pipeline.variant_id(g50)
    assert (buildcache.cache_key(
        g50, head, False, t50,
        admission=_admission_for(g50, head, src_token=t50),
        cxx=cxx,
    ) != buildcache.cache_key(
        g50, head, False,
        admission=_admission_for(g50, head),
        cxx=cxx,
    ))


def test_source_digest_failsclosed_on_missing_define():
    """#if 参照マクロの供給漏れは fails-closed (規律6/2)。

    template patch 適用後の骨格は #ifndef+#error (全経路停止)、-Werror=undef は
    それ以外の未定義マクロ評価への防壁として残る。どちらも RuntimeError に落ちる。"""
    hh = _require_ccbench_file("include/backoff.hh")
    with open(hh, encoding="utf-8") as f:
        src = f.read()
    if "BACKOFF_FIXED" not in src:
        skip_conditional_unrun("template patch 未適用: backoff.hh に BACKOFF_FIXED 骨格なし")
    cxx = _any_cxx()
    opts = _require_ccbench_file("cmake/Options.cmake")
    with open(opts, encoding="utf-8") as f:
        complete_defines = source_digest._merge_defines(
            source_digest.parse_options_defaults(f.read()), {})
    source_digest._cpp_normalize(src, complete_defines, cxx=cxx)
    missing_defines = dict(complete_defines)
    missing_defines.pop("BACKOFF_FIXED")
    try:
        source_digest._cpp_normalize(src, missing_defines, cxx=cxx)
        assert False, "供給漏れで停止すべき (#error / -Werror=undef)"
    except RuntimeError as exc:
        diagnostic = str(exc)
        assert "BACKOFF_FIXED" in diagnostic
        assert any(marker in diagnostic.lower()
                   for marker in ("not defined", "undefined", "undef"))


def test_source_digest_semantic_comment_vs_behavior():
    """コメントのみ変更は同 digest (cpp -P 除去)、挙動変更 (memory_order) は別 digest。"""
    opts = _require_ccbench_file("cmake/Options.cmake")
    hh = _require_ccbench_file("include/backoff.hh")
    cxx = _any_cxx()
    with open(opts, encoding="utf-8") as f:
        defines = source_digest._merge_defines(
            source_digest.parse_options_defaults(f.read()), {})
    with open(hh, encoding="utf-8") as f:
        src = f.read()
    base = source_digest._cpp_normalize(src, defines, cxx=cxx)
    commented = source_digest._cpp_normalize(
        src + "\n// trailing comment\n", defines, cxx=cxx)
    behaved = source_digest._cpp_normalize(
        src.replace("memory_order_acquire", "memory_order_relaxed"),
        defines, cxx=cxx,
    )
    assert base == commented              # コメント不感 (honest: 挙動不変なら同 id)
    assert base != behaved                # 挙動変更は検出


def test_source_digest_allowlist():
    """allowlist 内 (Options.cmake/backoff.hh/transaction.cc) は通過、外 (util.cc) は
    fails-closed。transaction.cc は段 5 (D38 決定5) で編集面に加わったため、反例には
    未だ編集面外の隣接ファイル cc/silo/util.cc を使う (2026-07-09 差し替え)。"""
    saved = source_digest.subprocess
    try:
        # 異常系: git status を fake し util.cc の tracked 改変を注入 (allowlist 外)
        source_digest.subprocess = types.SimpleNamespace(
            run=lambda *a, **k: types.SimpleNamespace(
                returncode=0, stdout=" M cc/silo/util.cc\n M include/backoff.hh\n"),
            SubprocessError=Exception)
        try:
            source_digest.assert_worktree_within_allowlist("/x")
            assert False, "allowlist 外改変で停止すべき"
        except RuntimeError:
            pass
        # 正常系: allowlist 内 (transaction.cc 含む) + untracked (build 生成物) は無視
        source_digest.subprocess = types.SimpleNamespace(
            run=lambda *a, **k: types.SimpleNamespace(
                returncode=0,
                stdout=" M cmake/Options.cmake\n M include/backoff.hh\n"
                       " M cc/silo/transaction.cc\n?? build-variants/x\n"),
            SubprocessError=Exception)
        source_digest.assert_worktree_within_allowlist("/x")   # 例外なし = OK
    finally:
        source_digest.subprocess = saved


def test_edit_surface_constants_exact_relationship():
    """[T-149] 編集面定数のドリフト機械検査 (T-140 N2 の処方)。

    ALLOWLIST は EVOLVE_BLOCK_SOURCES からの導出にしない — 「digest 対象の拡張」と
    「編集認可面の拡張」は独立二段の信頼境界 review であり、導出は片方の gate を畳む
    (2026-07-28 段 3 レンズ A-2)。代わりに関係式を完全一致 + 型付き例外 (Options.cmake =
    template 専有) で機械検査し、片側だけの拡張 (ドリフト) をここで止める。"""
    # literal pin (対向 mask): tuple の順序は digest pre-image の一部 (parts 連結順)
    assert source_digest.EVOLVE_BLOCK_SOURCES == (
        "include/backoff.hh", "cc/silo/transaction.cc", "cc/mocc/transaction.cc"), \
        "EVOLVE_BLOCK_SOURCES の値/順序が変わった。意図的なら本 pin と全 consumer " \
        "(ALLOWLIST/guard_write/s6 freshness/凍結面) を明示更新する"
    assert source_digest.OPTIONS_CMAKE == "cmake/Options.cmake"
    assert source_digest.ALLOWLIST == (
        frozenset(source_digest.EVOLVE_BLOCK_SOURCES) | {source_digest.OPTIONS_CMAKE}), \
        "ALLOWLIST != EBS ∪ {Options.cmake} (完全一致 + 型付き例外)。EBS/ALLOWLIST の" \
        "片側だけを拡張していないか — 両方を独立に review して明示更新する"


def test_axis_driver_source_rel_within_edit_surface():
    """[T-149] 全編集 driver の書込対象の膜性検査。所属 (∈ EBS) だけでは編集面内での
    軸取り違え (例: sort driver が backoff.hh を指す) を全通しする (段 6 RA-2) ため、
    driver ごとの期待値を literal pin する。取り違えると driver は marker 不在の
    ソースを読み malformed reject に落ち、certified 受理集合が全 reject に縮む。"""
    from orchestrator.campaign import axis_trigger_gating, p3_s4_loop, p3_s4_loop_sort
    expected = [
        (p3_s4_loop, "include/backoff.hh"),          # 段 4 backoff 軸
        (p3_s4_loop_sort, "cc/silo/transaction.cc"),  # sort 軸 (D38)
        (axis_trigger_gating, "cc/silo/transaction.cc"),  # trigger-gating 軸
    ]
    for mod, rel in expected:
        assert mod.SOURCE_REL == rel, \
            f"{mod.__name__}.SOURCE_REL={mod.SOURCE_REL!r} (期待 {rel!r})"
        assert mod.SOURCE_REL in source_digest.EVOLVE_BLOCK_SOURCES, mod.__name__


def test_lock_path_edit_surface_requires_auditor_live():
    """スコープ gate (後続段 3, D38, 裁定14): lock 経路 (transaction.cc) を coder の
    編集面 (EVOLVE_BLOCK_SOURCES) に開くのは auditor live が機械的に緑になってから。

    段 3 時点では transaction.cc ∉ EVOLVE_BLOCK_SOURCES ゆえ含意は vacuously true
    (lock 経路変異は段 5)。段 5 で transaction.cc を編集面に加えたら、この含意が発火し
    auditor live の機械 4 点 (s3_lock_coverage.json の all_pass) が緑であることを強制
    する — 宣言でなくテストで gate する (test_settings_json_wires_both_hooks と同形式)。
    これで「auditor 不在で lock 経路が編集可能になる窓」を sequencing 依存でなく機械で塞ぐ。"""
    from orchestrator.campaign import source_digest
    from orchestrator.campaign.layout import repo_output_root
    if "cc/silo/transaction.cc" not in source_digest.EVOLVE_BLOCK_SOURCES:
        return                              # 段 3: 編集面外ゆえ含意は空真 (発火せず)
    # ここに来る = 段 5 で lock 経路を編集面に開いた。auditor live を要求する。
    path = os.path.join(repo_output_root(), "env", "linux-baremetal",
                        "calibration", "s3_lock_coverage.json")
    assert os.path.exists(path), (
        "transaction.cc を編集面 (EVOLVE_BLOCK_SOURCES) に加えたが auditor live の"
        f"機械実証 {path} が無い — 先に s3_lock_coverage driver を緑にすること (D38)")
    import json as _json
    with open(path, encoding="utf-8") as fh:
        data = _json.load(fh)
    assert data.get("all_pass") is True, (
        "s3_lock_coverage の checks が all_pass でない — lock 被覆 assert が positive "
        "control で歯を持つ実証が緑になるまで lock 経路を編集面に開いてはいけない (D38)")


def test_evolve_block_markers_structure_and_inert():
    """EVOLVE-BLOCK 骨格 (Phase 3 coder 編集面, D22/phase3.md) の構造と inert を検査。

    (1) template patch に BEGIN/END マーカーが 1 個ずつ・id 一致で入っている (どの checkout でも)。
    (2) working-tree に適用済みなら: マーカーが #if BACKOFF_FIXED の #if/#else/#endif を bracket し、
        マーカー (= // コメント) が inert digest を変えない (preprocess 後 HEAD 原本と byte-identical)。
    """
    repo = os.path.dirname(_ORCH)
    with open(os.path.join(repo, "patches", "silo-backoff-fixed.patch"), encoding="utf-8") as f:
        patch = f.read()
    mid = "silo-backoff-magnitude"
    assert patch.count(f"EVOLVE-BLOCK-BEGIN {mid}") == 1     # 1 個・id 一致
    assert patch.count(f"EVOLVE-BLOCK-END {mid}") == 1
    assert patch.count("EVOLVE-BLOCK-BEGIN") == 1            # 別 id の混入なし
    assert patch.count("EVOLVE-BLOCK-END") == 1

    head = _ccbench_head_or_skip()
    if head is None:
        return
    sub = buildcache._ccbench_dir()
    wt = source_digest._read(os.path.join(sub, "include/backoff.hh"))
    if "EVOLVE-BLOCK-BEGIN" not in wt:
        return            # clean stock checkout (template patch 未適用) — patch 側検査で十分
    # working-tree 側もマーカーが 1 個ずつ (H3 hook がマーカー走査で編集面を画定する前提。
    # 偽マーカー対・別 id ブロックの混入は digest では分かれるが構造検査でも弾く)
    assert wt.count("EVOLVE-BLOCK-BEGIN") == 1
    assert wt.count("EVOLVE-BLOCK-END") == 1
    # bracket 順序: BEGIN → #if BACKOFF_FIXED → #else → #endif → END (coder 編集面が #if/#else に閉じる)
    i_begin = wt.index("EVOLVE-BLOCK-BEGIN")
    i_if = wt.index("#if BACKOFF_FIXED")
    i_else = wt.index("#else", i_if)
    i_endif = wt.index("#endif", i_else)
    i_end = wt.index("EVOLVE-BLOCK-END")
    assert i_begin < i_if < i_else < i_endif < i_end
    # マーカーは inert: 既定 -1 (#else=stock) で preprocess 後 HEAD baseline と byte-identical
    g = Genome("silo", {"BACK_OFF": 1, "NO_WAIT_LOCKING_IN_VALIDATION": 1,
                        "NO_WAIT_OF_TICTOC": 0, "WAL": 0, "BACKOFF_FIXED": -1})
    assert source_digest.compute(g) == source_digest.baseline(g, head)


# ===== STAGE3 (Phase 3 kickoff blocking): #include 死角 / TOCTOU 再照合 / apply-revert =====
#
# 実 submodule を汚さず identity 系の実験を行うため、tmpdir に最小の偽 ccbench repo
# (git + Options.cmake + backoff.hh + silo/mocc transaction.cc) を作る。
# EVOLVE_BLOCK_SOURCES と同じ相対パスを使う。

_FAKE_BACKOFF_HH = (
    '#include "tsc.hh"\n'
    "class Backoff {\n"
    "public:\n"
    "  static int wait() {\n"
    "#if BACK_OFF\n"
    "    return 1;\n"
    "#else\n"
    "    return 0;\n"
    "#endif\n"
    "  }\n"
    "};\n")

# 段 5 (D38 決定5) で EVOLVE_BLOCK_SOURCES に加わった lock 経路。#if 指令を持たないので
# -Werror=undef の対象にならない (実 transaction.cc は BACK_OFF 等 Options.cmake 既定の
# マクロしか参照せず fake Options.cmake との整合を保つ必要はここでは無い、compute/baseline
# が同一 defines で同一ファイルを preprocess できれば足りる)。
_FAKE_TRANSACTION_CC = (
    "class Transaction {\n"
    "public:\n"
    "  void lockWriteSet() {}\n"
    "  void writePhase() {}\n"
    "};\n")

# T-755 の trace-hook 専用 mocc 編集面。source owner 分離・裸 option・非対称
# cache 名を同時に通す最小 TU。
_FAKE_MOCC_TRANSACTION_CC = (
    "#ifdef RWLOCK\n"
    "int mocc_rwlock_fixture = 1;\n"
    "#endif\n"
    "#ifdef DLR1\n"
    "int mocc_dlr1_fixture = 1;\n"
    "#endif\n"
    "#if INLINE_VERSION_OPT == 17\n"
    "int mocc_inline_fixture = 17;\n"
    "#endif\n")


# 実 CMake の構造 (cmake/Options.cmake の供給表 + cc/<protocol>/CMakeLists.txt の OPTIONS) を
# 模した fixture。source_digest は「cmake CACHE 変数の全体」でなく「実 TU へ -D される部分集合」
# だけを defines にする (T-148 fix round) ため、供給表が無い fixture は fails-closed で止まる。
# DEBUG_MSG は「CACHE には居るが silo TU には供給されない」実 Options.cmake の DEBUG_MSG (oze 用)
# と同じ役回りで、乖離マクロの回帰検査に使う。
_FAKE_OPTIONS_CMAKE = (
    'set(CCBENCH_BACK_OFF 1 CACHE STRING "exponential backoff")\n'
    'set(CCBENCH_WAL 0 CACHE STRING "silo fixture")\n'
    'set(CCBENCH_DEBUG_MSG 0 CACHE STRING "oze only — not supplied to silo TUs")\n'
    'set(CCBENCH_INLINE_VERSION_OPT_X 17 CACHE STRING "asymmetric fixture")\n'
    "function(ccbench_universal_definitions out_var)\n"
    "  set(${out_var}\n"
    "    BACK_OFF=${CCBENCH_BACK_OFF}\n"
    "    PARENT_SCOPE)\n"
    "endfunction()\n")
_FAKE_SILO_CMAKE = (
    "ccbench_add_protocol(silo\n"
    "  SOURCES   transaction.cc\n"
    "  WORKLOADS ycsb\n"
    "  OPTIONS\n"
    "    WAL=${CCBENCH_WAL}\n"
    ")\n")
_FAKE_MOCC_CMAKE = (
    "ccbench_add_protocol(mocc\n"
    "  SOURCES transaction.cc util.cc lock.cc\n"
    "  WORKLOADS ycsb tpcc bomb sbomb\n"
    "  OPTIONS\n"
    "    RWLOCK\n"
    "    DLR1\n"
    "    INLINE_VERSION_OPT=${CCBENCH_INLINE_VERSION_OPT_X}\n"
    ")\n")


def _fake_ccbench_repo():
    """(sub, head, git) — git は fake repo で任意コマンドを回すヘルパー。"""
    sub = _tmpdir("izanagi_fakecc_")
    os.makedirs(os.path.join(sub, "cmake"))
    os.makedirs(os.path.join(sub, "include"))
    os.makedirs(os.path.join(sub, "cc", "silo"))
    os.makedirs(os.path.join(sub, "cc", "mocc"))
    with open(os.path.join(sub, "cmake", "Options.cmake"), "w", encoding="utf-8") as f:
        f.write(_FAKE_OPTIONS_CMAKE)
    with open(os.path.join(sub, "cc", "silo", "CMakeLists.txt"), "w", encoding="utf-8") as f:
        f.write(_FAKE_SILO_CMAKE)
    with open(os.path.join(sub, "cc", "mocc", "CMakeLists.txt"), "w", encoding="utf-8") as f:
        f.write(_FAKE_MOCC_CMAKE)
    with open(os.path.join(sub, "include", "backoff.hh"), "w", encoding="utf-8") as f:
        f.write(_FAKE_BACKOFF_HH)
    with open(os.path.join(sub, "cc", "silo", "transaction.cc"), "w", encoding="utf-8") as f:
        f.write(_FAKE_TRANSACTION_CC)
    with open(os.path.join(sub, "cc", "mocc", "transaction.cc"), "w", encoding="utf-8") as f:
        f.write(_FAKE_MOCC_TRANSACTION_CC)

    def git(*args):
        r = subprocess.run(["git", "-C", sub, *args], capture_output=True, text=True)
        assert r.returncode == 0, f"git {args}: {r.stderr}"
        return r.stdout

    git("init", "-q")
    git("config", "user.email", "test@example.invalid")
    git("config", "user.name", "izanagi-test")
    git("add", "-A")
    git("commit", "-q", "-m", "stock")
    head = git("rev-parse", "HEAD").strip()
    return sub, head, git


def test_source_digest_source_protocol_registry_is_exact_and_unknown_is_runtime_error():
    """source owner の drift と未知 path は KeyError にせず variant 単位で停止する。"""
    assert tuple(source_digest.EVOLVE_BLOCK_SOURCE_PROTOCOLS) == source_digest.EVOLVE_BLOCK_SOURCES
    g = Genome("silo", {})
    try:
        source_digest._source_protocol("cc/unknown/transaction.cc", g)
        assert False, "未知 source は RuntimeError で停止すべき"
    except RuntimeError as exc:
        assert "未知 source" in str(exc)
    with unittest_mock.patch.dict(
            source_digest.EVOLVE_BLOCK_SOURCE_PROTOCOLS,
            {"cc/extra/transaction.cc": "extra"}, clear=False):
        try:
            source_digest._source_protocol("include/backoff.hh", g)
            assert False, "source owner registry の余分な key は exact-match で停止すべき"
        except RuntimeError as exc:
            assert "不一致" in str(exc)


def test_source_digest_effective_define_adapter_preserves_owner_and_rhs_mapping():
    options = (
        'set(CCBENCH_BACKOFF_FIXED -1 CACHE STRING "fixed")\n'
        'set(CCBENCH_BACKOFF_ALT 17 CACHE STRING "wrong rhs")\n'
        'function(ccbench_universal_definitions out_var)\n'
        '  set(${out_var}\n'
        '    BACKOFF_FIXED=${CCBENCH_BACKOFF_FIXED}\n'
        '    PARENT_SCOPE)\n'
        'endfunction()\n'
    )
    genome = Genome("silo", {"BACKOFF_FIXED": 5})
    resolved = source_digest.resolve_effective_defines_from_cmake_sources(
        "include/backoff.hh",
        genome,
        options_text=options,
        protocol_cmake_text=_FAKE_SILO_CMAKE,
    )
    assert resolved.owner_protocol == "silo"
    assert resolved.cache_name("BACKOFF_FIXED") == "BACKOFF_FIXED"
    assert resolved.effective_value("BACKOFF_FIXED") == "5"

    wrong_rhs = options.replace(
        "BACKOFF_FIXED=${CCBENCH_BACKOFF_FIXED}",
        "BACKOFF_FIXED=${CCBENCH_BACKOFF_ALT}",
    )
    wrong = source_digest.resolve_effective_defines_from_cmake_sources(
        "include/backoff.hh",
        genome,
        options_text=wrong_rhs,
        protocol_cmake_text=_FAKE_SILO_CMAKE,
    )
    assert wrong.cache_name("BACKOFF_FIXED") == "BACKOFF_ALT"
    assert wrong.effective_value("BACKOFF_FIXED") == "17"
    assert genome.cmake_defines() == ["-DCCBENCH_BACKOFF_FIXED=5"]


def test_source_digest_real_mocc_resolve_succeeds_with_source_owned_defines():
    """実 mocc positive control:裸 RWLOCK と MQLOCK absent registry を実 source で通す。"""
    cxx = _any_cxx()
    _require_ccbench_file("cmake/Options.cmake")
    _require_ccbench_file("include/backoff.hh")
    _require_ccbench_file("cc/silo/transaction.cc")
    _require_ccbench_file("cc/mocc/CMakeLists.txt")
    _require_ccbench_file("cc/mocc/transaction.cc")
    sub = buildcache._ccbench_dir()
    head = _ccbench_head_or_skip()
    assert head is not None, "init 済み ccbench の HEAD を解決できない (skip に化けてはいけない)"
    g = Genome("mocc", {})
    defines = source_digest._worktree_defines(sub, g, "cc/mocc/transaction.cc")
    assert defines.get("RWLOCK") == "1", "mocc の裸 OPTIONS RWLOCK が -DRWLOCK=1 に反映されていない"
    source_digest.assert_conditional_macros_covered(g, sub, cxx)
    token = source_digest.resolve(g, head, sub, cxx)
    # clean stock checkout では HEAD roundtrip も同時に固定する。template patch
    # 適用中の共有 checkout では、resolve 成功と供給表検査だけを受け入れる。
    if "EVOLVE-BLOCK-BEGIN" not in source_digest._read(
            os.path.join(sub, "include", "backoff.hh")):
        assert token == source_digest.STOCK
        assert source_digest.compute(g, sub, cxx) == source_digest.baseline(g, head, sub, cxx)


def test_source_digest_real_silo_resolve_succeeds_after_source_protocol_split():
    """実 silo 回帰: silo source と mocc source に各 owner の供給表を適用する。"""
    cxx = _any_cxx()
    for rel in (
            "cmake/Options.cmake", "include/backoff.hh", "cc/silo/CMakeLists.txt",
            "cc/silo/transaction.cc", "cc/mocc/CMakeLists.txt", "cc/mocc/transaction.cc"):
        _require_ccbench_file(rel)
    sub = buildcache._ccbench_dir()
    head = _ccbench_head_or_skip()
    assert head is not None, "init 済み ccbench の HEAD を解決できない (skip に化けてはいけない)"
    g = Genome("silo", {
        "BACK_OFF": 1,
        "NO_WAIT_LOCKING_IN_VALIDATION": 1,
        "NO_WAIT_OF_TICTOC": 0,
        "WAL": 0,
    })
    source_digest.assert_conditional_macros_covered(g, sub, cxx)
    token = source_digest.resolve(g, head, sub, cxx)
    if "EVOLVE-BLOCK-BEGIN" not in source_digest._read(
            os.path.join(sub, "include", "backoff.hh")):
        assert token == source_digest.STOCK
        assert source_digest.compute(g, sub, cxx) == source_digest.baseline(g, head, sub, cxx)


def test_source_digest_parse_bare_asymmetric_options_and_malformed_scope():
    """裸/KV option の positive と OPTIONS 範囲外・括弧不整合の fails-closed。"""
    cxx = _any_cxx()
    sub, head, _git = _fake_ccbench_repo()
    supplied = source_digest.parse_supplied_macros(_FAKE_OPTIONS_CMAKE, _FAKE_MOCC_CMAKE)
    assert {"BACK_OFF", "RWLOCK", "DLR1", "INLINE_VERSION_OPT"} <= supplied
    for name in ("SOURCES", "WORKLOADS", "mocc", "transaction", "ycsb", "INLINE_VERSION_OPT_X"):
        assert name not in supplied, name
    g = Genome("mocc", {})
    mocc_defines = source_digest._worktree_defines(sub, g, "cc/mocc/transaction.cc")
    silo_defines = source_digest._worktree_defines(sub, g, "cc/silo/transaction.cc")
    assert mocc_defines["RWLOCK"] == "1" and mocc_defines["DLR1"] == "1"
    assert mocc_defines["INLINE_VERSION_OPT"] == "17"
    assert "INLINE_VERSION_OPT_X" not in mocc_defines
    assert "RWLOCK" not in silo_defines and silo_defines["WAL"] == "0"
    assert source_digest.resolve(g, head, sub, cxx) == source_digest.STOCK
    source_digest.assert_trace_diff_matches_head(g, head, sub, cxx)

    unbalanced = _FAKE_MOCC_CMAKE.rstrip().rstrip(")") + "\n"
    try:
        source_digest.parse_supplied_macros(_FAKE_OPTIONS_CMAKE, unbalanced)
        assert False, "OPTIONS 呼び出しの閉じ括弧欠落は停止すべき"
    except RuntimeError as exc:
        assert "括弧" in str(exc)

    # A source/workload token with an option-like name remains outside the
    # OPTIONS range and is not a supplied macro.  An assignment-shaped token
    # outside that range is structurally ambiguous and must stop.
    scoped = (
        "ccbench_add_protocol(mocc SOURCES INLINE_VERSION_OPT WORKLOADS ycsb "
        "OPTIONS RWLOCK)\n")
    scoped_names = source_digest.parse_supplied_macros(_FAKE_OPTIONS_CMAKE, scoped)
    assert "INLINE_VERSION_OPT" not in scoped_names
    malformed_scope = (
        "ccbench_add_protocol(mocc SOURCES transaction.cc "
        "INLINE_VERSION_OPT=${CCBENCH_INLINE_VERSION_OPT_X} "
        "WORKLOADS ycsb OPTIONS RWLOCK)\n")
    try:
        source_digest.parse_supplied_macros(_FAKE_OPTIONS_CMAKE, malformed_scope)
        assert False, "OPTIONS 範囲外の供給形 token は停止すべき"
    except RuntimeError as exc:
        assert "OPTIONS 外" in str(exc)


def test_source_digest_proven_absent_macro_registry_self_checks_supply_sources():
    """MQLOCK は参照だけなら通るが、bare OPTIONS/#define 出現で registry stale を検知する。"""
    real_sub = buildcache._ccbench_dir()
    _require_ccbench_file("cc/mocc/transaction.cc")
    assert source_digest._assert_proven_repo_absent_macros(real_sub) == (
        source_digest.PROVEN_REPO_ABSENT_MACROS)

    sub, _head, _git = _fake_ccbench_repo()
    mocc_src = os.path.join(sub, "cc", "mocc", "transaction.cc")
    with open(mocc_src, "a", encoding="utf-8") as f:
        f.write("#ifdef MQLOCK\nint mqlock_reference_only;\n#endif\n")
    assert source_digest._assert_proven_repo_absent_macros(sub) == (
        source_digest.PROVEN_REPO_ABSENT_MACROS)

    sub, _head, _git = _fake_ccbench_repo()
    with open(os.path.join(sub, "cc", "mocc", "CMakeLists.txt"), "a", encoding="utf-8") as f:
        f.write(
            '\ntarget_compile_definitions(mocc_extra PRIVATE '
            '"$<INSTALL_INTERFACE:UNRELATED_FLAG=1>")\n'
        )
    assert source_digest._assert_proven_repo_absent_macros(sub) == (
        source_digest.PROVEN_REPO_ABSENT_MACROS)

    sub, _head, _git = _fake_ccbench_repo()
    with open(os.path.join(sub, "cc", "mocc", "CMakeLists.txt"), "a", encoding="utf-8") as f:
        f.write(
            '\ntarget_compile_definitions(mocc_extra PRIVATE '
            '"$<$<CONFIG:Debug>:MQLOCK>")\n'
        )
    try:
        source_digest._assert_proven_repo_absent_macros(sub)
        assert False, "MQLOCK を含む generator expression で停止すべき"
    except RuntimeError as exc:
        assert "CMake supply" in str(exc)
        assert "stale" in str(exc) or "静的な供給元を確定できない" in str(exc)

    sub, _head, _git = _fake_ccbench_repo()
    with open(os.path.join(sub, "cc", "mocc", "CMakeLists.txt"), "a", encoding="utf-8") as f:
        f.write("\n# stale supply case is intentionally live\n")
        f.write("ccbench_add_protocol(mocc_extra SOURCES x.cc WORKLOADS ycsb OPTIONS MQLOCK)\n")
    try:
        source_digest._assert_proven_repo_absent_macros(sub)
        assert False, "bare OPTIONS MQLOCK で registry stale を検知すべき"
    except RuntimeError as exc:
        assert "stale" in str(exc) and "CMake supply" in str(exc)

    sub, _head, _git = _fake_ccbench_repo()
    with open(os.path.join(sub, "cc", "mocc", "transaction.cc"), "a", encoding="utf-8") as f:
        f.write("#define MQLOCK 1\n")
    try:
        source_digest._assert_proven_repo_absent_macros(sub)
        assert False, "#define MQLOCK で registry stale を検知すべき"
    except RuntimeError as exc:
        assert "stale" in str(exc) and "#define MQLOCK" in str(exc)

    sub, _head, _git = _fake_ccbench_repo()
    with open(os.path.join(sub, "cc", "mocc", "CMakeLists.txt"), "a", encoding="utf-8") as f:
        f.write(
            '\nset_target_properties(mocc_extra PROPERTIES '
            'COMPILE_DEFINITIONS "FOO;MQLOCK")\n'
        )
    try:
        source_digest._assert_proven_repo_absent_macros(sub)
        assert False, "semicolon-list COMPILE_DEFINITIONS MQLOCK で registry stale を検知すべき"
    except RuntimeError as exc:
        assert "stale" in str(exc) and "CMake supply" in str(exc)


def test_source_digest_builtin_ifdef_not_aliased_to_stock():
    """critical (2026-07-04 敵対検証 / D34 案A): builtin definedness (`#ifdef __x86_64__` /
    __GNUC__ 等) で digest 環境と実ビルドが乖離する偽 cache hit を封鎖する。

    旧設計 (-undef) は builtin を全消しするため、EVOLVE-BLOCK に `#ifdef __x86_64__ / 別挙動 /
    #else / stock / #endif` と書くと digest 環境では #else(stock枝) に落ち preprocess 出力が
    baseline と byte 一致 → src_token='stock' に化け、別挙動の variant が stock の certified 結果を
    verify 素通りで継承する (規律2 直撃)。案A (-undef 廃止) で builtin を実ビルドと揃えれば、
    #ifdef が digest に正直に反映され STOCK に化けない = 別 cache_key で cache-miss ビルドされる。"""
    cxx = _any_cxx()
    g = Genome("silo", {"BACK_OFF": 1})
    sub, head, _git = _fake_ccbench_repo()
    hh = os.path.join(sub, "include", "backoff.hh")
    stock_token = source_digest.resolve(g, head, sub, cxx=cxx)
    assert stock_token == source_digest.STOCK                          # clean は STOCK
    stock_variant = pipeline.variant_id(g, stock_token)
    assert stock_variant == pipeline.variant_id(g)
    stock_key = buildcache.cache_key(
        g, head, False,
        admission=_admission_for(g, head),
        cxx=cxx,
    )
    # payload (return 1) に builtin definedness の別枝を注入。g++ では __GNUC__ が常に定義される
    # ので実ビルドは 999 枝、旧 -undef digest は #else で 1 (= stock と alias) になっていた。
    with open(hh, "w", encoding="utf-8") as f:
        f.write(_FAKE_BACKOFF_HH.replace(
            "    return 1;\n",
            "#ifdef __GNUC__\n    return 999;\n#else\n    return 1;\n#endif\n"))
    tok = source_digest.resolve(g, head, sub, cxx=cxx)
    assert tok != source_digest.STOCK, \
        "builtin definedness (#ifdef __GNUC__) が STOCK に化けた — 案A (-undef 廃止) の回帰"
    assert pipeline.variant_id(g, tok) != stock_variant
    assert source_digest.compute(g, sub, cxx=cxx) != source_digest.baseline(
        g, head, sub, cxx=cxx), \
        "別挙動 payload の digest が baseline と一致 (偽 cache hit)"
    changed_key = buildcache.cache_key(
        g, head, False, tok,
        admission=_admission_for(g, head, src_token=tok),
        cxx=cxx,
    )
    assert changed_key != stock_key


def test_source_digest_include_change_rejected_by_resolve():
    """phase3.md blocking (#include 死角, 最小案): #include の追加/差し替えは preprocess 前に
    除去され digest に現れない (identity 不変の死角) → resolve が HEAD 行集合との不一致で
    fails-closed abort する。恒久案 (行を identity に織り込んで許す) は include 先の中身が
    identity 外に dangling し中身違いの新規 header で variant 間 alias が残るため却下
    (2026-07-03 敵対検証 high)。行集合を HEAD 固定にすれば include 追加自体を止め穴ごと消える。"""
    cxx = _any_cxx()
    g = Genome("silo", {"BACK_OFF": 1})
    sub, head, _git = _fake_ccbench_repo()
    assert source_digest.resolve(g, head, sub, cxx=cxx) == source_digest.STOCK
    hh = os.path.join(sub, "include", "backoff.hh")
    # (a) #include の追加 → resolve が abort (行集合が HEAD と不一致)
    with open(hh, "w", encoding="utf-8") as f:
        f.write('#include "evil_extra.hh"\n' + _FAKE_BACKOFF_HH)
    try:
        source_digest.resolve(g, head, sub, cxx=cxx)
        assert False, "#include 追加で resolve が abort すべき"
    except RuntimeError as e:
        assert "#include" in str(e)
    # (b) 既存 #include の差し替え → resolve abort (中身違い header の alias を identity 核で遮断)
    with open(hh, "w", encoding="utf-8") as f:
        f.write(_FAKE_BACKOFF_HH.replace('#include "tsc.hh"', '#include "hacked.hh"'))
    try:
        source_digest.resolve(g, head, sub, cxx=cxx)
        assert False, "#include 差し替えで resolve が abort すべき"
    except RuntimeError:
        pass
    # (c) 復元で resolve が通過に戻る (誤検出でない)
    with open(hh, "w", encoding="utf-8") as f:
        f.write(_FAKE_BACKOFF_HH)
    assert source_digest.resolve(g, head, sub, cxx=cxx) == source_digest.STOCK
    # assert_includes_match_head 単体でも同じ判定 (resolve が駆動する一次防壁)
    with open(hh, "w", encoding="utf-8") as f:
        f.write('#include "evil_extra.hh"\n' + _FAKE_BACKOFF_HH)
    try:
        source_digest.assert_includes_match_head(g, head, sub, cxx=cxx)
        assert False, "assert_includes_match_head 単体でも abort すべき"
    except RuntimeError:
        pass


# 実 include/backoff.hh:123-125 と同型の TU 注入マクロ枝 (#define は cc/silo/*_silo.cc:3 が
# TU 側で供給) を持つ stock。T-148 系テストはこれを HEAD に commit してから枝内を編集する。
_FAKE_BACKOFF_GVD_HH = _FAKE_BACKOFF_HH + (
    "#ifdef GLOBAL_VALUE_DEFINE\n"
    "int backoff_global_state = 0;\n"
    "#endif\n")


def test_source_digest_tu_context_macro_edit_not_aliased_to_stock():
    """T-148 (worklog (27) 起票、P1): TU 注入マクロ (#define GLOBAL_VALUE_DEFINE) に条件づけ
    られた枝は単体 preprocess の素文脈で dead → 枝内編集が digest に不可視 = src_token が
    'stock' に化け、stock の certified 結果・cache バイナリを継承する (規律2 直撃。実 stock の
    該当枝は include/backoff.hh:123-125)。二重文脈 (素 + GLOBAL_VALUE_DEFINE=1) で両枝を
    identity に織り込み封鎖する。"""
    cxx = _any_cxx()
    g = Genome("silo", {"BACK_OFF": 1})
    sub, head, git = _fake_ccbench_repo()
    hh = os.path.join(sub, "include", "backoff.hh")
    with open(hh, "w", encoding="utf-8") as f:
        f.write(_FAKE_BACKOFF_GVD_HH)
    git("add", "-A")
    git("commit", "-q", "-m", "stock+gvd")
    head = git("rev-parse", "HEAD").strip()
    # 正例 (過剰拒否の検出): GVD 枝を持つ clean tree は reject されず STOCK のまま
    assert source_digest.resolve(g, head, sub, cxx) == source_digest.STOCK
    with open(hh, "w", encoding="utf-8") as f:
        f.write(_FAKE_BACKOFF_GVD_HH.replace("int backoff_global_state = 0;",
                                             "int backoff_global_state = 12345;"))
    tok = source_digest.resolve(g, head, sub, cxx)
    assert tok != source_digest.STOCK, \
        "GLOBAL_VALUE_DEFINE 枝内編集が STOCK に化けた (T-148 回帰 = stock 偽 alias)"
    assert source_digest.compute(g, sub, cxx) != source_digest.baseline(g, head, sub, cxx), \
        "枝内編集の digest が baseline と一致 (偽 cache hit)"


def test_source_digest_unknown_conditional_macro_fails_closed():
    """T-148 ガード: 条件指令が defines ∪ ファイル内 #define ∪ CONTEXT_MACROS ∪ builtin の
    どれでもないマクロを参照したら fails-closed。-Werror=undef は `#if MACRO` しか捕えず
    `#ifdef`/`defined()` は静かに偽枝を取る (g++ 実測 rc=0) ため、この形の未知文脈マクロは
    どの文脈でも digest が覆えない未知枝 = 次の GLOBAL_VALUE_DEFINE 型になる。"""
    cxx = _any_cxx()
    g = Genome("silo", {"BACK_OFF": 1})
    sub, head, _git = _fake_ccbench_repo()
    hh = os.path.join(sub, "include", "backoff.hh")
    with open(hh, "w", encoding="utf-8") as f:
        f.write(_FAKE_BACKOFF_HH.replace(
            "    return 1;\n",
            "#ifdef IZANAGI_T148_UNKNOWN_CTX\n    return 999;\n#else\n    return 1;\n#endif\n"))
    try:
        source_digest.resolve(g, head, sub, cxx)
        assert False, "未知マクロの #ifdef で resolve が abort すべき"
    except RuntimeError as e:
        assert "IZANAGI_T148_UNKNOWN_CTX" in str(e)
    # defined() 形式も同罪 (こちらも -Wundef 非発火)
    with open(hh, "w", encoding="utf-8") as f:
        f.write(_FAKE_BACKOFF_HH.replace(
            "    return 1;\n",
            "#if defined(IZANAGI_T148_UNKNOWN_CTX)\n    return 999;\n#else\n    return 1;\n#endif\n"))
    try:
        source_digest.resolve(g, head, sub, cxx)
        assert False, "未知マクロの defined() で resolve が abort すべき"
    except RuntimeError as e:
        assert "IZANAGI_T148_UNKNOWN_CTX" in str(e)


def test_source_digest_guard_accepts_builtin_local_and_supplied_macros():
    """正例 (過剰拒否の検出): 文脈ガードは (a) builtin definedness (#ifdef __GNUC__) を受理して
    別 identity にする (D34 案A / test_source_digest_builtin_ifdef_not_aliased_to_stock の仕様)、
    (b) ファイル内 #define のマクロを受理、(c) defines 供給済み (#if BACK_OFF) を受理する。
    受理集合を縮めてよいのは未知文脈マクロと __has_include だけ (段 4 事前登録の正例 P-2)。"""
    cxx = _any_cxx()
    g = Genome("silo", {"BACK_OFF": 1})
    sub, head, _git = _fake_ccbench_repo()
    hh = os.path.join(sub, "include", "backoff.hh")
    with open(hh, "w", encoding="utf-8") as f:
        f.write(_FAKE_BACKOFF_HH.replace(
            "    return 1;\n",
            "#ifdef __GNUC__\n    return 999;\n#else\n    return 1;\n#endif\n"))
    tok = source_digest.resolve(g, head, sub, cxx)
    assert tok != source_digest.STOCK      # reject でも stock 化けでもなく、受理して別 identity
    with open(hh, "w", encoding="utf-8") as f:
        f.write("#define IZANAGI_LOCAL_FLAG 1\n"
                "#ifdef IZANAGI_LOCAL_FLAG\nint izanagi_local_ok;\n#endif\n" + _FAKE_BACKOFF_HH)
    assert source_digest.resolve(g, head, sub, cxx) != source_digest.STOCK


def test_source_digest_trace_hidden_in_context_macro_branch_caught():
    """規律1 (観測者効果の分離): #ifdef GLOBAL_VALUE_DEFINE の内側に #if TRACE を隠すと、
    素文脈だけの diff-of-diffs では両 TRACE 値とも dead で D_variant==D_stock になり素通り
    していた。二重文脈 (T-148) の define 側で差分が現れ fails-closed になる。"""
    cxx = _any_cxx()
    g = Genome("silo", {"BACK_OFF": 1})
    sub, head, git = _fake_ccbench_repo()
    hh = os.path.join(sub, "include", "backoff.hh")
    with open(hh, "w", encoding="utf-8") as f:
        f.write(_FAKE_BACKOFF_GVD_HH)
    git("add", "-A")
    git("commit", "-q", "-m", "stock+gvd")
    head = git("rev-parse", "HEAD").strip()
    source_digest.assert_trace_diff_matches_head(g, head, sub, cxx)   # clean は通過 (正例)
    with open(hh, "w", encoding="utf-8") as f:
        f.write(_FAKE_BACKOFF_GVD_HH.replace(
            "int backoff_global_state = 0;",
            "int backoff_global_state = 0;\n#if TRACE\nint izanagi_trace_probe = 1;\n#endif"))
    try:
        source_digest.assert_trace_diff_matches_head(g, head, sub, cxx)
        assert False, "GVD 枝内の #if TRACE 隠しは diff-of-diffs 不一致で abort すべき"
    except RuntimeError as e:
        assert "diff-of-diffs" in str(e)


def test_source_digest_has_include_rejected():
    """computed include (#if __has_include(...)) は #include 行検査にも preprocess 後 digest にも
    現れず (-nostdinc で header 未発見 = dead 枝)、実ビルドだけ別バイナリになる documented hole
    (D34 known-limitation) だった。骨格・stock は不使用のため出現 = 逸脱として fails-closed で
    塞ぐ (T-148 ガードに同乗)。マクロ本体へ隠して条件式から literal を消す迂回も止める
    (段 6 レビュー B must-fix 3)。

    fixture は quoted の存在しない header を使う — `<atomic>` は -nostdinc の preprocess 自体を
    error にするため、ガードを外しても別理由で赤になり単一理由性が壊れる (DW-M03 の過剰決定、
    レビュー B should 2)。診断は専用メッセージ (「computed include」) まで pin する: 専用 raise を
    外しても識別子 `__has_include` は builtin に載らず未知マクロ経路で reject されるため
    受理集合は変わらず、変異 M4 は kill でなく diagnostic sensitivity pin 枠になる (DW-M08)。"""
    cxx = _any_cxx()
    g = Genome("silo", {"BACK_OFF": 1})
    sub, head, _git = _fake_ccbench_repo()
    hh = os.path.join(sub, "include", "backoff.hh")
    with open(hh, "w", encoding="utf-8") as f:
        f.write(_FAKE_BACKOFF_HH +
                '#if __has_include("izanagi_nonexistent.hh")\nint izanagi_evil = 1;\n#endif\n')
    try:
        source_digest.resolve(g, head, sub, cxx)
        assert False, "__has_include の出現で resolve が abort すべき"
    except RuntimeError as e:
        assert "__has_include" in str(e) and "computed include" in str(e)
    # マクロ本体へ隠す迂回 (条件式には literal が現れず、local #define で既知扱いになる形)
    with open(hh, "w", encoding="utf-8") as f:
        f.write('#define IZ_HAS_LOCAL __has_include("izanagi_nonexistent.hh")\n'
                "#if IZ_HAS_LOCAL\nint izanagi_evil = 1;\n#endif\n" + _FAKE_BACKOFF_HH)
    try:
        source_digest.resolve(g, head, sub, cxx)
        assert False, "#define 本体の __has_include で resolve が abort すべき"
    except RuntimeError as e:
        assert "__has_include" in str(e)


def test_source_digest_guard_lexes_like_the_preprocessor():
    """ガードの字句解析が g++ と食い違うと、指令を見落として偽 STOCK を作れる / 正当な式を
    過剰拒否する (段 6 レビュー B must-fix 2/4、いずれも g++-12 実測で確認):
    (a) `#/**/ifdef FOO` を g++ は条件指令として受理する (rc=0) — ガードも検出しなければならない。
    (b) 条件指令より**後ろ**の #define はその指令時点では未定義であり、既知に数えてはならない。
    (c) `#if 'A' == 65` の文字定数は識別子ではない — 拒否すれば受理集合を不当に狭める。
    (d) 文字列リテラル内の指令風文字列は指令ではない。"""
    cxx = _any_cxx()
    g = Genome("silo", {"BACK_OFF": 1})
    sub, head, _git = _fake_ccbench_repo()
    hh = os.path.join(sub, "include", "backoff.hh")

    def _resolve_err(body):
        with open(hh, "w", encoding="utf-8") as f:
            f.write(body)
        try:
            source_digest.resolve(g, head, sub, cxx)
            return None
        except RuntimeError as e:
            return str(e)

    # (a) コメントで分断された指令も検出する
    err = _resolve_err(_FAKE_BACKOFF_HH + "#/**/ifdef IZ_SPLIT_CTX\nint a;\n#endif\n")
    assert err and "IZ_SPLIT_CTX" in err, "コメント分断指令をガードが見落とした"
    # (b) 後方 #define は既知にしない
    err = _resolve_err(_FAKE_BACKOFF_HH +
                       "#ifdef IZ_LATE_CTX\nint a;\n#endif\n#define IZ_LATE_CTX 1\n")
    assert err and "IZ_LATE_CTX" in err, "指令より後ろの #define を既知扱いした"
    # (c) 文字定数は識別子でない (過剰拒否の検出 = 正例)
    err = _resolve_err(_FAKE_BACKOFF_HH + "#if 'A' == 65\nint charconst_ok;\n#endif\n")
    assert err is None, f"正当な文字定数条件を過剰拒否した: {err}"
    # (d) 文字列リテラル内の指令風文字列は指令でない (正例)
    err = _resolve_err('const char* s = "#ifdef IZ_IN_STRING";\n' + _FAKE_BACKOFF_HH)
    assert err is None, f"文字列リテラル内を指令と誤認した: {err}"


def test_source_digest_guard_lexes_multiline_and_malformed(tmp_path=None):
    """段 6 レビュー A の 4 反例 — いずれも「実ビルドで live・digest で dead・ガードは受理」の
    偽 STOCK alias を実測で構築されたもの。字句解析と定義状態の取り方を規格へ寄せて塞ぐ。

    (a) 複数行コメントは空白 1 個であって改行ではない。改行を保存すると
        `#if 1 /*<改行>*/ && defined(X)` の続きが走査から落ちる (A must-fix 1)。
    (b) `#if 0` の中の `#define` は実際には定義されない。静的な出現だけで既知扱いすると
        未知マクロを洗浄する (A must-fix 2)。
    (c) 数値の桁区切り `1'000` はリテラル開始ではない。リテラル扱いすると閉じ引用符を探して
        以降を飲み込み、その先の指令すべてがガードから消える (A must-fix 3)。
    (d) `#elifdef` / `#elifndef` も条件指令 (A should 1)。
    (e) 未終端のコメント/リテラル・raw string は解釈不能。静かに全消しして受理すると
        ガードが恒真化するので停止する (A should 3)。"""
    cxx = _any_cxx()
    g = Genome("silo", {"BACK_OFF": 1})
    sub, head, _git = _fake_ccbench_repo()
    hh = os.path.join(sub, "include", "backoff.hh")

    def _resolve_err(body):
        with open(hh, "w", encoding="utf-8") as f:
            f.write(body)
        try:
            source_digest.resolve(g, head, sub, cxx)
            return None
        except RuntimeError as e:
            return str(e)

    err = _resolve_err(_FAKE_BACKOFF_HH + "#if 1 /*\n*/ && defined(IZ_MLC_CTX)\nint a;\n#endif\n")
    assert err and "IZ_MLC_CTX" in err, "複数行コメントで分断された条件式の続きを見落とした"
    err = _resolve_err(_FAKE_BACKOFF_HH +
                       "#if 0\n#define IZ_DEAD_CTX 1\n#endif\n#ifdef IZ_DEAD_CTX\nint a;\n#endif\n")
    assert err and "IZ_DEAD_CTX" in err, "dead 枝の #define が未知マクロを既知に洗浄した"
    err = _resolve_err(_FAKE_BACKOFF_HH +
                       "#if 0\nstatic const int k = 1'000;\n#endif\n"
                       "#ifdef IZ_SEP_CTX\nint a;\n#endif\n")
    assert err and "IZ_SEP_CTX" in err, "桁区切りをリテラル開始と誤認し以降の指令を飲み込んだ"
    err = _resolve_err(_FAKE_BACKOFF_HH + "#if 0\nint a;\n#elifdef IZ_ELIF_CTX\nint b;\n#endif\n")
    assert err and "IZ_ELIF_CTX" in err, "#elifdef を条件指令として認識していない"
    assert _resolve_err(_FAKE_BACKOFF_HH + "/* unterminated\n") is not None
    assert _resolve_err('const char* s = "unterminated;\n' + _FAKE_BACKOFF_HH) is not None
    assert _resolve_err('const char* s = R"(raw)";\n' + _FAKE_BACKOFF_HH) is not None
    # 正例: 桁区切りを含む生きたコードと `__has_*` 演算子は受理する (過剰拒否の検出)
    err = _resolve_err(_FAKE_BACKOFF_HH + "static const int k = 1'000'000;\n"
                       "#if __has_cpp_attribute(nodiscard)\nint ok;\n#endif\n")
    assert err is None, f"正当な桁区切り / __has_cpp_attribute を過剰拒否した: {err}"


def test_source_digest_token_paste_bypass_rejected():
    """段 6 焦点再レビューの must-fix: `__has_include` の literal 検査は、マクロ名を
    トークン貼り合わせで組み立てられると迂回できる。`#define IZ_H __has_inc##lude` +
    `#if IZ_H("tsc.hh")` を g++ は `__has_include` として評価する (実測) のに、ガードは
    `IZ_H` を「先行しかつ実定義される #define」として既知扱いし受理していた。

    貼り合わせなしに新しい識別子を作る手段はないので、`#define` 本体の `##` (と digraph
    `%:%:`) を止めれば同型の難読化はまとめて閉じる。EVOLVE-BLOCK の骨格・stock はいずれも
    貼り合わせを使わない (実 stock の 2 ファイルには `#define` 自体が 1 行も無い)。

    「`#define` 行集合を HEAD 固定にする」案は採れない — template patch が骨格の
    `#define BACKOFF_FIXED -1` を足すため、現行 campaign が patch 適用中に停止する。"""
    cxx = _any_cxx()
    g = Genome("silo", {"BACK_OFF": 1})
    sub, head, _git = _fake_ccbench_repo()
    hh = os.path.join(sub, "include", "backoff.hh")
    for body in ("#define IZ_PASTE __has_inc##lude\n",
                 "#define IZ_PASTE __has_inc%:%:lude\n"):
        with open(hh, "w", encoding="utf-8") as f:
            f.write(body + '#if IZ_PASTE("tsc.hh")\nint izanagi_evil;\n#endif\n' + _FAKE_BACKOFF_HH)
        try:
            source_digest.resolve(g, head, sub, cxx)
            assert False, f"トークン貼り合わせ ({body.strip()}) で resolve が abort すべき"
        except RuntimeError as e:
            assert "##" in str(e) or "%:%:" in str(e)
    # 正例: 貼り合わせを使わない通常の #define は従来どおり受理する (過剰拒否の検出)
    with open(hh, "w", encoding="utf-8") as f:
        f.write("#define IZ_PLAIN 1\n#ifdef IZ_PLAIN\nint ok;\n#endif\n" + _FAKE_BACKOFF_HH)
    assert source_digest.resolve(g, head, sub, cxx) != source_digest.STOCK


def test_source_digest_char_literal_prefix_not_taken_as_separator():
    """段 6 焦点再レビュー nit 1: 桁区切りの判定を「直前が英数字」で行うと、接頭辞つき
    文字リテラル (`L'A'` / `u8'x'`) を区切りと誤認する。中身が `"` や `/` のとき
    (`u'"'`) は続きを未終端リテラルと見て、正当な C++ を停止させる (過剰拒否)。
    判定は「直前のトークンが数字で始まるか」で行う。"""
    _any_cxx()
    for src, want in (("x = 1'000;", "x = 1'000;"),      # 桁区切りは温存
                      ("x = 0x1F'FF;", "x = 0x1F'FF;"),
                      ("c = u'\"';", "c = u'';"),        # 接頭辞つきはリテラルとして中身除去
                      ("c = L'A';", "c = L'';"),
                      ("c = 'a';", "c = '';")):
        assert source_digest._lex_normalize(src, "x.hh").strip() == want, src


def test_source_digest_read_failure_is_runtime_error():
    """identity 経路のファイル読取失敗は `RuntimeError` に正規化する (段 6 レビュー A should 4)。
    `loop` / `pipeline.evaluate` / `buildcache._recheck_src_token` はいずれも
    `except RuntimeError` でしか受けないため、`OSError` が漏れると variant 単位の abort 隔離が
    破れ campaign 全体が落ち、build dir の破棄も走らない。

    `resolve()` 経由では allowlist 検査が先に発火して別理由で赤くなる (過剰決定、`DW-M03`) ので、
    読取を行う `_worktree_defines` を直接呼んで単一理由にする。"""
    _any_cxx()
    g = Genome("silo", {"BACK_OFF": 1})
    sub, _head, _git = _fake_ccbench_repo()
    os.remove(os.path.join(sub, "cc", "silo", "CMakeLists.txt"))
    try:
        source_digest._worktree_defines(sub, g, "cc/silo/transaction.cc")
        assert False, "protocol CMakeLists 不在で停止すべき"
    except RuntimeError as e:
        assert "CMakeLists.txt" in str(e)
    except OSError as e:                      # 正規化されていなければ OSError が漏れる
        assert False, f"OSError が RuntimeError に正規化されていない: {e!r}"


def test_source_digest_defines_match_real_tu_supply():
    """digest の -D 集合は cmake CACHE 全体でなく**実 TU へ供給される部分集合**でなければ
    ならない (段 6 レビュー B must-fix 1)。Options.cmake の CACHE には他 protocol 専用の
    マクロ (実 repo の DEBUG_MSG = oze 用) が居るが silo TU には渡らないため、一律 -D すると
    `#ifdef DEBUG_MSG` で digest と実ビルドの枝が逆転する。あわせて実ビルドの言語標準
    (CMAKE_CXX_STANDARD 20) を渡し `__cplusplus` の乖離も塞ぐ。"""
    cxx = _any_cxx()
    g = Genome("silo", {"BACK_OFF": 1})
    sub, head, _git = _fake_ccbench_repo()
    supplied = source_digest.parse_supplied_macros(_FAKE_OPTIONS_CMAKE, _FAKE_SILO_CMAKE)
    assert "BACK_OFF" in supplied and "WAL" in supplied     # universal + protocol OPTIONS
    assert "DEBUG_MSG" not in supplied                       # CACHE には居るが TU 非供給
    defines = source_digest._worktree_defines(sub, g, "cc/silo/transaction.cc")
    assert "DEBUG_MSG" not in defines, "TU 非供給マクロが digest の -D に残っている"
    assert defines.get("Linux") == "1", "実 TU の -DLinux が digest に無い"
    # 非供給マクロの definedness テストは未知マクロとして停止する (両環境の枝逆転を沈黙させない)
    hh = os.path.join(sub, "include", "backoff.hh")
    with open(hh, "w", encoding="utf-8") as f:
        f.write(_FAKE_BACKOFF_HH + "#ifdef DEBUG_MSG\nint a;\n#else\nint b;\n#endif\n")
    try:
        source_digest.resolve(g, head, sub, cxx)
        assert False, "TU 非供給マクロの #ifdef で resolve が abort すべき"
    except RuntimeError as e:
        assert "DEBUG_MSG" in str(e)
    # 言語標準: 実ビルド (C++20) と同じ枝を取る
    out = source_digest._cpp_normalize(
        "#if __cplusplus >= 202002L\nint cpp20;\n#else\nint cpp17;\n#endif\n", defines, cxx)
    assert "cpp20" in out, "digest の __cplusplus が実ビルド (CMAKE_CXX_STANDARD 20) と乖離"
    # 供給表を壊した Options は fails-closed (恒真化しない)
    try:
        source_digest.parse_supplied_macros('set(CCBENCH_BACK_OFF 1 CACHE STRING "x")\n', "")
        assert False, "供給表なしの Options で停止すべき"
    except RuntimeError as e:
        assert "ccbench_universal_definitions" in str(e)


def test_buildcache_recheck_detects_toctou():
    """build 出口の identity 再照合 (phase3.md blocking): resolve 時の src_token と
    再計算値が食い違えば fails-closed。新規ビルドは build dir ごと破棄する (汚染
    バイナリを campaign 非依存の共有キャッシュに永続させない)。"""
    g = Genome("silo", {"BACK_OFF": 1})
    saved = buildcache.source_digest
    bdir = _tmpdir("izanagi_toctou_")
    expected = _source_evidence(g, "deadbeef", source_root="/x")
    mutated = _source_evidence(g, "deadbeef", src_token="1" * 64, source_root="/x")
    assert os.path.isdir(bdir)
    buildcache.source_digest = types.SimpleNamespace(
        STOCK="stock", resolve_evidence=lambda *a, **k: mutated)
    try:
        try:
            buildcache._recheck_source_evidence(
                g, "deadbeef", "/x", "g++-13", expected, bdir, True,
            )
            assert False, "src_token 不一致で停止すべき"
        except RuntimeError as e:
            assert "TOCTOU" in str(e)
        assert not os.path.exists(bdir)              # 新規ビルドは破棄
        # 一致なら通過 (正常経路)
        buildcache.source_digest = types.SimpleNamespace(
            STOCK="stock", resolve_evidence=lambda *a, **k: expected)
        buildcache._recheck_source_evidence(
            g, "deadbeef", "/x", "g++-13", expected, "/nonexistent", False,
        )
    finally:
        buildcache.source_digest = saved


def test_buildcache_cache_hit_rechecks_identity():
    """cache hit 経路でも identity 再照合が走る (resolve→hit 判定間の TOCTOU も遮断)。
    hit の不一致は既存 (過去の正当な) 成果物なので破棄せず停止のみ。"""
    g = Genome("silo", {"BACK_OFF": 1})
    sub, head, _git = _fake_ccbench_repo()
    root = _tmpdir("izanagi_bc_root_")
    evidence = _source_evidence(g, head, source_root=sub)
    admission = derive_build_admission(_BUILD_CONTEXT, evidence)
    key = buildcache.cache_key(
        g, head, trace=True, src_token="stock", admission=admission,
    )
    bindir = os.path.join(root, key, "cc", "silo")
    os.makedirs(bindir)
    binary = os.path.join(bindir, "ycsb_silo.exe")
    with open(binary, "w") as f:
        f.write("fake-binary")
    buildcache._write_fsynced_json(
        os.path.join(root, key, buildcache._LEGACY_ADMISSION_SIDECAR),
        {"schema_version": buildcache._LEGACY_ADMISSION_SCHEMA,
         "admission": admission.as_cache_identity()},
    )
    saved = buildcache.source_digest

    def _sd(resolved):
        return types.SimpleNamespace(
            STOCK="stock",
            assert_worktree_within_allowlist=lambda *a, **k: None,
            assert_trace_diff_matches_head=lambda *a, **k: None,
            resolve_evidence=lambda *a, **k: resolved)

    try:
        buildcache.source_digest = _sd(
            _source_evidence(g, head, src_token="1" * 64, source_root=sub)
        )
        try:
            buildcache.build(g, head, trace=True, cache_root=root,
                             ccbench_dir=sub, src_token="stock",
                             build_context=_BUILD_CONTEXT, admission=admission,
                             source_evidence=evidence)
            assert False, "cache hit でも TOCTOU 不一致で停止すべき"
        except RuntimeError as e:
            assert "TOCTOU" in str(e)
        assert os.path.exists(binary)                # hit 側は破棄しない
        buildcache.source_digest = _sd(evidence)
        br = buildcache.build(g, head, trace=True, cache_root=root,
                              ccbench_dir=sub, src_token="stock",
                              build_context=_BUILD_CONTEXT, admission=admission,
                              source_evidence=evidence)
        assert br.cached and br.binary == binary     # 一致すれば hit が返る
    finally:
        buildcache.source_digest = saved


def test_build_cache_miss_wires_recheck():
    """回帰 (結線検査): build() の cache-miss 経路が build 完了直後に _recheck_src_token を
    駆動し、不一致なら build dir ごと破棄して停止する。単体テスト
    (test_buildcache_recheck_detects_toctou) は関数を直接呼ぶため、build() 側の呼び出しを
    消しても全緑のまま = 結線の消失を検出できない (2026-07-03 敵対検証 medium)。"""
    g = Genome("silo", {"BACK_OFF": 1})
    sub, head, _git = _fake_ccbench_repo()
    root = _tmpdir("izanagi_bc_miss_")
    evidence = _source_evidence(g, head, source_root=sub)
    admission = derive_build_admission(_BUILD_CONTEXT, evidence)
    key = buildcache.cache_key(
        g, head, trace=True, src_token="stock", admission=admission,
    )
    binary = os.path.join(root, key, "cc", "silo", "ycsb_silo.exe")

    def fake_run(cmd, what):                 # configure/build を no-op 化し binary だけ置く
        if what == "build":
            staging = cmd[cmd.index("--build") + 1]
            staging_binary = os.path.join(staging, "cc", "silo", "ycsb_silo.exe")
            os.makedirs(os.path.dirname(staging_binary), exist_ok=True)
            with open(staging_binary, "w") as f:
                f.write("fake-binary")

    def _sd(resolved):
        return types.SimpleNamespace(
            STOCK="stock",
            assert_worktree_within_allowlist=lambda *a, **k: None,
            assert_trace_diff_matches_head=lambda *a, **k: None,
            resolve_evidence=lambda *a, **k: resolved)

    saved_sd, saved_run = buildcache.source_digest, buildcache._run
    try:
        buildcache._run = fake_run
        buildcache.source_digest = _sd(
            _source_evidence(g, head, src_token="1" * 64, source_root=sub)
        )
        try:
            buildcache.build(g, head, trace=True, cache_root=root,
                             ccbench_dir=sub, src_token="stock",
                             build_context=_BUILD_CONTEXT, admission=admission,
                             source_evidence=evidence)
            assert False, "cache-miss 側でも build 直後の recheck で停止すべき"
        except RuntimeError as e:
            assert "TOCTOU" in str(e)
        assert not os.path.exists(os.path.join(root, key))   # 新規ビルドは dir ごと破棄
        buildcache.source_digest = _sd(evidence)
        br = buildcache.build(g, head, trace=True, cache_root=root,
                              ccbench_dir=sub, src_token="stock",
                              build_context=_BUILD_CONTEXT, admission=admission,
                              source_evidence=evidence)
        assert not br.cached and os.path.exists(br.binary)   # 一致なら新規ビルドが返る
    finally:
        buildcache.source_digest, buildcache._run = saved_sd, saved_run


def test_buildcache_stale_marker_discarded_before_configure():
    """回帰 (結線検査, D-9): build() の cache-miss 経路は configure より前に残骸 build dir
    (kill 等で中断された中途 build dir) を破棄する。fake `_run` で呼び出し列を記録し、
    configure 分岐では残骸マーカーが既に消えていることを assert、build 分岐では configure
    済みであることを assert した上で binary を書く。最終的に呼び出し列が
    `["configure", "build"]` の厳密一致であることまで固定する — `_clear_stale_build_dir`
    の呼び出し自体が消える将来 refactor 変異 (build 分岐だけが残っていれば緑になってしまう)
    を殺すため (2026-07-11 監査 L2-2 由来、フリー実装ではなく統合結線の歯として追加)。"""
    g = Genome("silo", {"BACK_OFF": 1})
    sub, head, _git = _fake_ccbench_repo()
    root = _tmpdir("izanagi_bc_stale_")
    evidence = _source_evidence(g, head, source_root=sub)
    admission = derive_build_admission(_BUILD_CONTEXT, evidence)
    key = buildcache.cache_key(
        g, head, trace=True, src_token="stock", admission=admission,
    )
    bdir = os.path.join(root, key)
    binary = os.path.join(bdir, "cc", "silo", "ycsb_silo.exe")
    marker = os.path.join(bdir, "CMakeCache.txt")

    # kill 等で中断された中途 build dir の残骸を事前設置 (CMakeCache.txt あり・binary 無し)。
    os.makedirs(bdir)
    with open(marker, "w", encoding="utf-8") as f:
        f.write("# This is the CMakeCache file.\n"
                "CMAKE_HOME_DIRECTORY:INTERNAL=/tmp/stale-worktree-vanished\n")

    def _sd(resolved):
        return types.SimpleNamespace(
            STOCK="stock",
            assert_worktree_within_allowlist=lambda *a, **k: None,
            assert_trace_diff_matches_head=lambda *a, **k: None,
            resolve_evidence=lambda *a, **k: resolved)

    calls = []

    def fake_run(cmd, what):
        calls.append(what)
        if what == "configure":
            # 破棄が configure より前に完了している (残骸マーカーはもう存在しない)。
            assert not os.path.exists(marker), \
                "残骸マーカーが configure 時点でまだ残っている — 破棄が configure より前でない"
            assert calls == ["configure"], calls
        elif what == "build":
            # configure が先に走っていることを確認してから binary を書く。
            assert calls == ["configure", "build"], calls
            staging = cmd[cmd.index("--build") + 1]
            staging_binary = os.path.join(staging, "cc", "silo", "ycsb_silo.exe")
            os.makedirs(os.path.dirname(staging_binary), exist_ok=True)
            with open(staging_binary, "w") as f:
                f.write("fake-binary")

    saved_sd, saved_run = buildcache.source_digest, buildcache._run
    try:
        buildcache._run = fake_run
        buildcache.source_digest = _sd(evidence)
        br = buildcache.build(g, head, trace=True, cache_root=root,
                              ccbench_dir=sub, src_token="stock",
                              build_context=_BUILD_CONTEXT, admission=admission,
                              source_evidence=evidence)
    finally:
        buildcache.source_digest, buildcache._run = saved_sd, saved_run

    assert calls == ["configure", "build"], calls  # 呼び出し列の厳密一致 (D-9)
    assert not os.path.exists(marker)               # 残骸マーカーは最終的にも不在
    assert not br.cached                            # cache-hit でなく fresh build
    assert os.path.exists(br.binary)


def test_buildresult_bin_hash_derives_from_full_sha256_both_paths():
    """A-3/D-7: bin_hash は bin_sha256[:16] の read-only 派生 (独立フィールドでない)。fresh /
    cache-hit 両経路で派生関係が成立し、bin_sha256 が実ファイルの full sha256 (64 hex) と一致。
    さらに hash 計算は経路あたり 1 回だけ (呼出し回数で固定)。"""
    g = Genome("silo", {"BACK_OFF": 1})
    sub, head, _git = _fake_ccbench_repo()
    root = _tmpdir("izanagi_bc_sha_")
    evidence = _source_evidence(g, head, source_root=sub)
    admission = derive_build_admission(_BUILD_CONTEXT, evidence)
    key = buildcache.cache_key(
        g, head, trace=True, src_token="stock", admission=admission,
    )
    binary = os.path.join(root, key, "cc", "silo", "ycsb_silo.exe")
    payload = b"real-fixture-binary-bytes"
    # 期待値は本番 helper でなく hashlib で独立に計算する (恒真回避)。
    expect = hashlib.sha256(payload).hexdigest()

    def fake_run(cmd, what):
        if what == "build":
            staging = cmd[cmd.index("--build") + 1]
            staging_binary = os.path.join(staging, "cc", "silo", "ycsb_silo.exe")
            os.makedirs(os.path.dirname(staging_binary), exist_ok=True)
            with open(staging_binary, "wb") as f:
                f.write(payload)

    sd = types.SimpleNamespace(
        STOCK="stock",
        assert_worktree_within_allowlist=lambda *a, **k: None,
        assert_trace_diff_matches_head=lambda *a, **k: None,
        resolve_evidence=lambda *a, **k: evidence)

    calls = {"n": 0}
    real_full = buildcache.full_sha256

    def counting_full(path):
        calls["n"] += 1
        return real_full(path)

    saved_sd, saved_run, saved_full = (
        buildcache.source_digest, buildcache._run, buildcache.full_sha256)
    try:
        buildcache._run = fake_run
        buildcache.source_digest = sd
        buildcache.full_sha256 = counting_full
        calls["n"] = 0
        fr = buildcache.build(g, head, trace=True, cache_root=root,
                              ccbench_dir=sub, src_token="stock",
                              build_context=_BUILD_CONTEXT, admission=admission,
                              source_evidence=evidence)
        assert not fr.cached
        assert calls["n"] == 1                       # fresh 経路で 1 回だけ
        assert fr.bin_sha256 == expect and len(fr.bin_sha256) == 64
        assert fr.bin_hash == fr.bin_sha256[:16]     # 派生 property
        calls["n"] = 0
        hr = buildcache.build(g, head, trace=True, cache_root=root,
                              ccbench_dir=sub, src_token="stock",
                              build_context=_BUILD_CONTEXT, admission=admission,
                              source_evidence=evidence)
        assert hr.cached
        assert calls["n"] == 1                       # cache-hit 経路でも 1 回だけ
        assert hr.bin_sha256 == expect
        assert hr.bin_hash == hr.bin_sha256[:16]
    finally:
        (buildcache.source_digest, buildcache._run,
         buildcache.full_sha256) = saved_sd, saved_run, saved_full


def test_buildresult_is_frozen():
    """A-3: BuildResult は frozen (bin_sha256 を後から書き換えて派生 short と乖離させられない)。"""
    br = buildcache.BuildResult(
        genome=Genome("silo", {}), trace=False, binary="/x",
        bin_sha256="a" * 64, build_dir="/d", cached=False)
    assert br.bin_hash == "a" * 16
    assert br.contract_sha256 is None
    try:
        br.bin_sha256 = "b" * 64
        assert False, "frozen dataclass は書き換え不能であるべき"
    except Exception as e:                       # FrozenInstanceError (dataclasses)
        assert "FrozenInstance" in type(e).__name__ or "frozen" in str(e).lower()


def test_assert_binary_sha256_accepts_exact_and_rejects_malformed():
    """A-6/A-5: assert_binary_sha256 は exact 64 lowercase hex のみ受理。15/16/63/65 桁・非 hex・
    大文字・正しい prefix だが異なる full は拒否、ファイル不在も含め BinaryDigestError 系に倒す
    (prefix 照合・fallback しない)。成功時は None を返す (bool でない)。"""
    d = _tmpdir("izanagi_asha_")
    path = os.path.join(d, "bin")
    payload = b"assert-fixture-bytes"
    with open(path, "wb") as f:
        f.write(payload)
    good = hashlib.sha256(payload).hexdigest()      # 独立計算 (恒真回避)

    assert buildcache.assert_binary_sha256(path, good) is None   # 成功時のみ復帰

    # 不一致 (正しい 16 字 prefix を持つが full が異なる) → Mismatch
    bad_full = good[:16] + ("f" if good[16] != "f" else "e") + good[17:]
    assert len(bad_full) == 64 and bad_full != good and bad_full[:16] == good[:16]
    try:
        buildcache.assert_binary_sha256(path, bad_full)
        assert False, "prefix 一致でも full 不一致は Mismatch であるべき"
    except buildcache.BinaryDigestMismatch:
        pass

    # 形不正はすべて BinaryDigestError (Mismatch でない = 照合前に拒否)
    for bad in (good[:15], good[:16], good[:63], good + "0",   # 15/16/63/65 桁
                good[:-1] + "g",                                # 非 hex
                good.upper()):                                  # 大文字
        try:
            buildcache.assert_binary_sha256(path, bad)
            assert False, f"形不正 expected を受理してはいけない: {bad!r}"
        except buildcache.BinaryDigestError as e:
            assert not isinstance(e, buildcache.BinaryDigestMismatch), bad

    # ファイル不在 → BinaryDigestError (full_sha256 の OSError を昇格)
    try:
        buildcache.assert_binary_sha256(os.path.join(d, "nope"), good)
        assert False, "ファイル不在は BinaryDigestError であるべき"
    except buildcache.BinaryDigestError:
        pass


def test_full_sha256_missing_file_raises_digest_error():
    """A-5: full_sha256 は OSError を握りつぶさず BinaryDigestError (cause 保持) に倒す。"""
    try:
        buildcache.full_sha256("/nonexistent/izanagi/bin")
        assert False, "不在ファイルは BinaryDigestError であるべき"
    except buildcache.BinaryDigestError as e:
        assert e.cause is not None


_FAKE_BACKOFF_TRACED = (
    '#include "tsc.hh"\n'
    "class Backoff {\n"
    "public:\n"
    "  static int wait() {\n"
    "#if TRACE\n"
    "    int trace_hits = 1;\n"
    "#else\n"
    "    int trace_hits = 0;\n"
    "#endif\n"
    "#if BACK_OFF\n"
    "    return 1 + trace_hits;\n"
    "#else\n"
    "    return trace_hits;\n"
    "#endif\n"
    "  }\n"
    "};\n")


def test_trace_diff_of_diffs_predicate():
    """観測者効果の二重検査 (diff-of-diffs, phase3.md blocking / D30 一次防壁):
    (a) stock は通過、(b) TRACE 非依存の payload 編集も通過 (正当な編集を巻き込まない)、
    (c) variant が #if TRACE の挙動差を追加したら fails-closed abort — nm の name-based
    検査では捕えない C++ ソースレベルの TRACE 混入 (規律1)。"""
    cxx = _any_cxx()
    g = Genome("silo", {"BACK_OFF": 1})
    sub, head, _git = _fake_ccbench_repo()
    hh = os.path.join(sub, "include", "backoff.hh")
    source_digest.assert_trace_diff_matches_head(g, head, sub, cxx=cxx)
    with open(hh, "w", encoding="utf-8") as f:                       # (b) TRACE 非依存の編集
        f.write(_FAKE_BACKOFF_HH.replace("return 1;", "return 2;"))
    source_digest.assert_trace_diff_matches_head(g, head, sub, cxx=cxx)
    with open(hh, "w", encoding="utf-8") as f:                       # (c) TRACE 挙動差の混入
        f.write(_FAKE_BACKOFF_HH.replace(
            "return 1;", "#if TRACE\n    int leak = 1;\n#endif\n    return 1;"))
    try:
        source_digest.assert_trace_diff_matches_head(g, head, sub, cxx=cxx)
        assert False, "TRACE 条件付きコードの追加で abort すべき"
    except RuntimeError as e:
        assert "diff-of-diffs" in str(e)


def test_trace_diff_of_diffs_allows_stock_hook_catches_inner_edit():
    """HEAD 自体が trace-hook (#if TRACE) を持つ場合の diff-of-diffs:
    (a) 未改変 worktree は D_variant == D_stock (両方非空) で通過 = 正当な trace-hook
    差分は許容。(b) ガードより前への行追加も通過 — ハンク位置 (@@ 行番号) を比較に
    入れないので、TRACE 非依存の編集で差分位置がずれても偽陽性にならない。
    (c) #if TRACE の内側の挙動差改変は D_variant≠D_stock で abort — 旧 nm 検査が
    素通しした「#ifdef TRACE 内側に挙動差を隠す攻撃」(GW2R-1 系) の閉塞。"""
    cxx = _any_cxx()
    g = Genome("silo", {"BACK_OFF": 1})
    sub, _head, git = _fake_ccbench_repo()
    hh = os.path.join(sub, "include", "backoff.hh")
    with open(hh, "w", encoding="utf-8") as f:
        f.write(_FAKE_BACKOFF_TRACED)
    git("add", "-A")
    git("commit", "-q", "-m", "traced stock")
    head2 = git("rev-parse", "HEAD").strip()
    source_digest.assert_trace_diff_matches_head(g, head2, sub, cxx=cxx)
    with open(hh, "w", encoding="utf-8") as f:                       # (b) ガード前に行追加
        f.write(_FAKE_BACKOFF_TRACED.replace(
            "  static int wait() {\n",
            "  static int wait() {\n    int pad = 0; (void)pad;\n"))
    source_digest.assert_trace_diff_matches_head(g, head2, sub, cxx=cxx)
    with open(hh, "w", encoding="utf-8") as f:                       # (c) ガード内改変
        f.write(_FAKE_BACKOFF_TRACED.replace("int trace_hits = 1;",
                                             "int trace_hits = 2;"))
    try:
        source_digest.assert_trace_diff_matches_head(g, head2, sub, cxx=cxx)
        assert False, "#if TRACE 内側の改変で abort すべき"
    except RuntimeError:
        pass


def test_build_wires_trace_diff_check():
    """結線検査: build() の cache-hit / fresh 両経路が観測者効果二重検査を駆動する
    (発火単位 = 毎 variant の trace/perf ビルド直後, phase3.md)。不一致は fresh なら
    build dir ごと破棄 (規律1 違反疑いのバイナリを共有キャッシュに残さない)、hit なら
    破棄せず停止のみ (_recheck_src_token と同じ非対称)。"""
    g = Genome("silo", {"BACK_OFF": 1})
    sub, head, _git = _fake_ccbench_repo()
    root = _tmpdir("izanagi_dod_root_")
    evidence = _source_evidence(g, head, source_root=sub)
    admission = derive_build_admission(_BUILD_CONTEXT, evidence)
    key = buildcache.cache_key(
        g, head, trace=True, src_token="stock", admission=admission,
    )
    binary = os.path.join(root, key, "cc", "silo", "ycsb_silo.exe")

    def _sd(trace_diff_raises):
        def _atd(*a, **k):
            if trace_diff_raises:
                raise RuntimeError("diff-of-diffs 不一致 (テスト注入)")
        return types.SimpleNamespace(
            STOCK="stock",
            assert_worktree_within_allowlist=lambda *a, **k: None,
            assert_trace_diff_matches_head=_atd,
            resolve_evidence=lambda *a, **k: evidence)

    def fake_run(cmd, what):
        if what == "build":
            staging = cmd[cmd.index("--build") + 1]
            staging_binary = os.path.join(staging, "cc", "silo", "ycsb_silo.exe")
            os.makedirs(os.path.dirname(staging_binary), exist_ok=True)
            with open(staging_binary, "w") as f:
                f.write("fake-binary")

    saved_sd, saved_run = buildcache.source_digest, buildcache._run
    try:
        buildcache._run = fake_run
        buildcache.source_digest = _sd(trace_diff_raises=True)
        try:                                     # fresh: 不一致 → 破棄 + 停止
            buildcache.build(g, head, trace=True, cache_root=root,
                             ccbench_dir=sub, src_token="stock",
                             build_context=_BUILD_CONTEXT, admission=admission,
                             source_evidence=evidence)
            assert False, "fresh build で diff-of-diffs 不一致なら停止すべき"
        except RuntimeError as e:
            assert "diff-of-diffs" in str(e)
        assert not os.path.exists(os.path.join(root, key))   # fresh は dir ごと破棄
        buildcache.source_digest = _sd(trace_diff_raises=False)
        br = buildcache.build(g, head, trace=True, cache_root=root,
                              ccbench_dir=sub, src_token="stock",
                              build_context=_BUILD_CONTEXT, admission=admission,
                              source_evidence=evidence)
        assert not br.cached                     # 通過なら新規ビルドが返る
        buildcache.source_digest = _sd(trace_diff_raises=True)
        try:                                     # hit: 検査は走る・破棄はしない
            buildcache.build(g, head, trace=True, cache_root=root,
                             ccbench_dir=sub, src_token="stock",
                             build_context=_BUILD_CONTEXT, admission=admission,
                             source_evidence=evidence)
            assert False, "cache hit でも diff-of-diffs 検査が走るべき"
        except RuntimeError:
            pass
        assert os.path.exists(binary)            # hit 側は破棄しない
    finally:
        buildcache.source_digest, buildcache._run = saved_sd, saved_run


def test_patchharness_apply_revert_roundtrip():
    """apply/revert ハーネス (phase3.md blocking): pinned-clean → apply → body →
    revert で working-tree が完全に戻る。patch が新規作成したファイル (checkout では
    消えない untracked 残骸) も除去される。"""
    from orchestrator.campaign import patchharness
    sub, head, git = _fake_ccbench_repo()
    hh = os.path.join(sub, "include", "backoff.hh")
    newf = os.path.join(sub, "include", "synth_new.hh")
    # patch を作る: 既存ファイル変更 + 新規ファイル追加 → reset --hard で元に戻す
    with open(hh, "w", encoding="utf-8") as f:
        f.write(_FAKE_BACKOFF_HH.replace("return 1;", "return 2;"))
    with open(newf, "w", encoding="utf-8") as f:
        f.write("int synth;\n")
    git("add", "-A")
    patch_text = git("diff", "--cached")
    git("reset", "-q", "--hard", "HEAD")
    patch_path = os.path.join(_tmpdir("izanagi_patch_"), "variant.patch")
    with open(patch_path, "w", encoding="utf-8") as f:
        f.write(patch_text)

    with patchharness.applied(patch_path, head[:12], sub) as files:
        assert sorted(files) == ["include/backoff.hh", "include/synth_new.hh"]
        with open(hh, encoding="utf-8") as f:
            assert "return 2;" in f.read()           # 適用されている
        assert os.path.exists(newf)
    with open(hh, encoding="utf-8") as f:
        assert f.read() == _FAKE_BACKOFF_HH          # 逐語で戻る
    assert not os.path.exists(newf)                  # 新規ファイル残骸も消える
    assert git("status", "--porcelain") == ""        # clean
    # body が例外でも revert される (finally)
    try:
        with patchharness.applied(patch_path, head[:12], sub):
            raise ValueError("body boom")
    except ValueError:
        pass
    with open(hh, encoding="utf-8") as f:
        assert f.read() == _FAKE_BACKOFF_HH
    assert not os.path.exists(newf)


def test_patchharness_git_retries_index_lock_then_succeeds():
    """checkout/apply の index.lock rc=128 だけを 200ms 間隔で retry し、成功時も
    CompletedProcess の追加属性に回数・理由を残す (silent retry にしない)。"""
    from orchestrator.campaign import patchharness
    results = [
        subprocess.CompletedProcess([], 128, "", "fatal: Unable to create 'index.lock'"),
        subprocess.CompletedProcess([], 128, "", "fatal: index.lock: File exists"),
        subprocess.CompletedProcess([], 0, "ok\n", ""),
    ]
    calls = []
    sleeps = []

    def runner(command, **kwargs):
        calls.append((command, kwargs))
        return results.pop(0)

    result = patchharness._git(
        "/fake/submodule", "checkout", "--", ".", _runner=runner,
        _sleep=sleeps.append)
    assert result.returncode == 0
    assert result.stdout == "ok\n"                 # 既存 output semantics は不変
    assert result.patchharness_retries == 2
    assert "index.lock" in result.patchharness_retry_trace
    assert "2 回" in result.patchharness_retry_trace
    assert len(calls) == 3
    assert sleeps == [0.2, 0.2]


def test_patchharness_git_non_index_lock_failure_is_not_retried():
    """同じ rc=128 でも index.lock 以外は従来どおり 1 回で失敗結果を返す。"""
    from orchestrator.campaign import patchharness
    calls = []

    def runner(command, **kwargs):
        calls.append((command, kwargs))
        return subprocess.CompletedProcess([], 128, "", "fatal: bad revision")

    result = patchharness._git(
        "/fake/submodule", "apply", "variant.patch", _runner=runner,
        _sleep=lambda _: (_ for _ in ()).throw(AssertionError("sleep must not run")))
    assert result.returncode == 128
    assert result.stderr == "fatal: bad revision"
    assert result.patchharness_retries == 0
    assert result.patchharness_retry_trace == ""
    assert len(calls) == 1


def test_patchharness_git_index_lock_retry_exhaustion_fails_closed():
    """index.lock が解けなくても retry は 5 回で打ち切り、rc=128 と痕跡を返す。"""
    from orchestrator.campaign import patchharness
    calls = []
    sleeps = []

    def runner(command, **kwargs):
        calls.append((command, kwargs))
        return subprocess.CompletedProcess([], 128, "", "fatal: index.lock exists")

    result = patchharness._git(
        "/fake/submodule", "checkout", "--", ".", _runner=runner,
        _sleep=sleeps.append)
    assert result.returncode == 128
    assert result.patchharness_retries == 5
    assert "5 回" in result.patchharness_retry_trace
    assert len(calls) == 6                         # 初回 + bounded retry 5 回
    assert sleeps == [0.2] * 5


def test_patchharness_git_disables_optional_locks_in_environment():
    """全 git 共通経路が親 env を保ったまま GIT_OPTIONAL_LOCKS=0 を上書きする。"""
    from orchestrator.campaign import patchharness
    captured = {}

    def runner(command, **kwargs):
        captured.update(kwargs)
        return subprocess.CompletedProcess([], 0, "head\n", "")

    result = patchharness._git(
        "/fake/submodule", "rev-parse", "HEAD", _runner=runner,
        _sleep=lambda _: None)
    assert result.returncode == 0
    assert captured["env"]["GIT_OPTIONAL_LOCKS"] == "0"
    assert captured["capture_output"] is True
    assert captured["text"] is True


def test_patchharness_real_shared_checkout_guard_is_pytest_only_and_fails_closed(
        tmp_path, monkeypatch):
    """実共有 submodule は正本印付き node だけが pytest 中に checkout できる。"""
    from orchestrator.campaign import patchharness

    real = patchharness._default_ccbench_dir()
    hermetic = tmp_path / "hermetic-ccbench"
    subprocess.run(["git", "init", "--quiet", str(hermetic)], check=True)
    with unittest_mock.patch.object(
            patchharness, "_git_repository_identity",
            side_effect=AssertionError("production では probe 禁止")):
        token = patchharness._PYTEST_NODE.set(None)
        try:
            patchharness._guard_real_shared_checkout(real)
        finally:
            patchharness._PYTEST_NODE.reset(token)
    for name in (
        "GIT_DIR", "GIT_INDEX_FILE", "GIT_WORK_TREE", "GIT_COMMON_DIR",
        "GIT_OBJECT_DIRECTORY", "GIT_ALTERNATE_OBJECT_DIRECTORIES",
        "GIT_CEILING_DIRECTORIES",
    ):
        monkeypatch.setenv(name, f"decoy-{name}")
    with patchharness._pytest_node_context("test_missing.py::test_missing", None):
        with pytest.raises(RuntimeError) as excinfo:
            with patchharness.checkout("unused-pin", base_dir=real):
                raise AssertionError("guard が checkout body より先に拒否すべき")
        message = str(excinfo.value)
        assert "test_missing.py::test_missing" in message
        assert "REAL_REPO_ACCESS_BY_NODE で ccbench=write と分類せよ" in message
        with pytest.raises(RuntimeError):
            with patchharness.checkout(
                    "unused-pin", base_dir=os.path.join(real, "include")):
                raise AssertionError("subdirectory guard が checkout より先に拒否すべき")
        patchharness._guard_real_shared_checkout(str(hermetic))
        with pytest.raises(RuntimeError, match="repository identity"):
            patchharness._guard_real_shared_checkout(str(tmp_path / "missing"))
    reader = types.SimpleNamespace(parent="read", ccbench="read")
    with patchharness._pytest_node_context("test_reader.py::test_reader", reader):
        with pytest.raises(RuntimeError, match="ccbench=write"):
            patchharness._guard_real_shared_checkout(real)
    writer = types.SimpleNamespace(parent=None, ccbench="write")
    with patchharness._pytest_node_context("test_writer.py::test_writer", writer):
        patchharness._guard_real_shared_checkout(real)


def test_source_digest_status_scrubs_git_environment_and_disables_optional_locks(
        monkeypatch):
    """paired status/diff と show は同じ衛生化 Git env で実 source を見る。"""
    forbidden = (
        "GIT_DIR", "GIT_INDEX_FILE", "GIT_WORK_TREE", "GIT_COMMON_DIR",
        "GIT_OBJECT_DIRECTORY", "GIT_ALTERNATE_OBJECT_DIRECTORIES",
        "GIT_CEILING_DIRECTORIES",
    )
    for name in forbidden:
        monkeypatch.setenv(name, f"decoy-{name}")
    monkeypatch.setenv("GIT_OPTIONAL_LOCKS", "1")
    captured = []

    def runner(command, **kwargs):
        captured.append((command, kwargs))
        if "status" in command:
            return subprocess.CompletedProcess(
                command, 0, " M include/backoff.hh\n?? build/\n", "")
        if "diff" in command:
            return subprocess.CompletedProcess(command, 0, b"real-source-diff", b"")
        if "show" in command:
            return subprocess.CompletedProcess(command, 0, "baseline\n", "")
        raise AssertionError(f"予期しない subprocess: {command!r}")

    monkeypatch.setattr(source_digest.subprocess, "run", runner)
    monkeypatch.setattr(source_digest, "assert_includes_match_head", lambda *args: None)
    monkeypatch.setattr(
        source_digest, "assert_conditional_macros_covered", lambda *args: None,
    )
    monkeypatch.setattr(source_digest, "compute", lambda *args: "a" * 64)
    monkeypatch.setattr(source_digest, "baseline", lambda *args: "b" * 64)

    evidence = source_digest.resolve_evidence(
        Genome("silo", {"BACK_OFF": 1}), "deadbeef", ccbench_dir="/real/ccbench",
    )
    assert evidence.tracked_paths == ("include/backoff.hh",)
    assert evidence.tracked_diff_sha256 == hashlib.sha256(b"real-source-diff").hexdigest()
    assert source_digest._git_show("/real/ccbench", "deadbeef", "include/backoff.hh") == (
        "baseline\n"
    )
    assert len(captured) == 3
    environments = [kwargs["env"] for _, kwargs in captured]
    assert environments[0] == environments[1] == environments[2]
    assert environments[0]["GIT_OPTIONAL_LOCKS"] == "0"
    assert all(name not in environments[0] for name in forbidden)
    assert all(kwargs["capture_output"] is True for _, kwargs in captured)


def test_patchharness_fails_closed_on_dirty_or_unpinned_tree():
    """apply 前の pinned-clean assert: tracked 改変が残る tree / pin 不一致 / 空 pin には
    patch を当てない (前 variant の revert 漏れ・別セッション残骸との合成を防ぐ)。"""
    from orchestrator.campaign import patchharness
    sub, head, git = _fake_ccbench_repo()
    # pin 不一致・空 pin
    for bad_pin in ("0000000", ""):
        try:
            patchharness.assert_pinned_clean(sub, bad_pin)
            assert False, f"pin={bad_pin!r} で停止すべき"
        except RuntimeError:
            pass
    patchharness.assert_pinned_clean(sub, head[:7])      # 正常は通る
    # dirty tree
    hh = os.path.join(sub, "include", "backoff.hh")
    with open(hh, "w", encoding="utf-8") as f:
        f.write(_FAKE_BACKOFF_HH + "// dirt\n")
    try:
        patchharness.assert_pinned_clean(sub, head[:7])
        assert False, "dirty tree で停止すべき"
    except RuntimeError:
        pass
    # untracked (ビルド生成物相当) は無視される
    git("checkout", "--", ".")
    with open(os.path.join(sub, "untracked_artifact"), "w") as f:
        f.write("x")
    patchharness.assert_pinned_clean(sub, head[:7])


def test_patchharness_applied_rejects_dirty_tree():
    """回帰 (駆動検査): applied() の enter が pinned-clean assert を駆動する。dirty tree には
    patch を当てず body にも入らない。assert_pinned_clean 単体が正しくても applied() が
    呼ばなければ防壁にならない — 駆動を消しても全緑のままだった
    (2026-07-03 敵対検証 medium: テスト正直さ)。"""
    from orchestrator.campaign import patchharness
    sub, head, git = _fake_ccbench_repo()
    hh = os.path.join(sub, "include", "backoff.hh")
    # 有効な patch を用意 (enter 内の順序が変わっても patch 読み込み失敗を dirty 拒否と
    # 誤認しないよう、patch 自体は常に読める状態にしておく)
    with open(hh, "w", encoding="utf-8") as f:
        f.write(_FAKE_BACKOFF_HH.replace("return 1;", "return 2;"))
    git("add", "-A")
    patch_text = git("diff", "--cached")
    git("reset", "-q", "--hard", "HEAD")
    patch_path = os.path.join(_tmpdir("izanagi_patch_dirty_"), "variant.patch")
    with open(patch_path, "w", encoding="utf-8") as f:
        f.write(patch_text)
    # tree を dirty 化 (前 variant の revert 漏れ相当)
    dirt = _FAKE_BACKOFF_HH + "// leftover dirt\n"
    with open(hh, "w", encoding="utf-8") as f:
        f.write(dirt)
    entered = []
    try:
        with patchharness.applied(patch_path, head[:12], sub):
            entered.append(True)
        assert False, "dirty tree では applied() の enter が停止すべき"
    except RuntimeError as e:
        assert "clean でない" in str(e)
    assert not entered                       # body に入っていない
    with open(hh, encoding="utf-8") as f:
        assert f.read() == dirt              # patch は当たっていない (dirt が原文のまま)


def test_patchharness_checkout_creates_isolated_worktree():
    """段5 git worktree 隔離: checkout() は pin_commit で使い捨て worktree を作り、
    exit で `git worktree list` から消える (base repo の working-tree は無傷)。"""
    from orchestrator.campaign import patchharness
    sub, head, git = _fake_ccbench_repo()
    with patchharness.checkout(head[:12], base_dir=sub) as wt:
        assert wt != sub
        assert os.path.isdir(wt)
        wt_git = lambda *a: subprocess.run(   # noqa: E731
            ["git", "-C", wt, *a], capture_output=True, text=True).stdout.strip()
        assert wt_git("rev-parse", "HEAD") == head
        with open(os.path.join(wt, "include", "backoff.hh"), encoding="utf-8") as f:
            assert f.read() == _FAKE_BACKOFF_HH          # base の HEAD 内容がそのまま見える
        listing = git("worktree", "list", "--porcelain")
        assert os.path.realpath(wt) in listing
    assert not os.path.exists(wt)                        # worktree ディレクトリごと破棄
    assert os.path.realpath(wt) not in git("worktree", "list", "--porcelain")
    assert git("status", "--porcelain") == ""             # base repo は無傷


def test_patchharness_checkout_two_concurrent_worktrees_independent():
    """同一 base から 2 つの checkout() を同時に開いても互いに干渉しない
    (段5 の目的そのもの: 呼び出しごとに一意パスなので並行評価が競合しない)。"""
    from orchestrator.campaign import patchharness
    sub, head, git = _fake_ccbench_repo()
    with patchharness.checkout(head[:12], base_dir=sub) as wt1:
        with patchharness.checkout(head[:12], base_dir=sub) as wt2:
            assert wt1 != wt2
            hh1 = os.path.join(wt1, "include", "backoff.hh")
            hh2 = os.path.join(wt2, "include", "backoff.hh")
            with open(hh1, "w", encoding="utf-8") as f:
                f.write(_FAKE_BACKOFF_HH.replace("return 1;", "return 111;"))
            # wt2 は wt1 への書き込みの影響を受けない (独立 worktree)
            with open(hh2, encoding="utf-8") as f:
                assert f.read() == _FAKE_BACKOFF_HH
        assert not os.path.exists(wt2)
        assert os.path.exists(wt1)                       # wt1 はまだ生きている
    assert not os.path.exists(wt1)
    assert git("status", "--porcelain") == ""


def test_patchharness_checkout_composes_with_applied():
    """checkout() が返す worktree path を applied() にそのまま渡せる (責務分離の確認)。
    patch は worktree 内だけに当たり、base repo の working-tree は無傷のまま。"""
    from orchestrator.campaign import patchharness
    sub, head, git = _fake_ccbench_repo()
    hh_base = os.path.join(sub, "include", "backoff.hh")
    with open(hh_base, "w", encoding="utf-8") as f:
        f.write(_FAKE_BACKOFF_HH.replace("return 1;", "return 2;"))
    git("add", "-A")
    patch_text = git("diff", "--cached")
    git("reset", "-q", "--hard", "HEAD")
    patch_path = os.path.join(_tmpdir("izanagi_patch_wt_"), "variant.patch")
    with open(patch_path, "w", encoding="utf-8") as f:
        f.write(patch_text)

    with patchharness.checkout(head[:12], base_dir=sub) as wt:
        with patchharness.applied(patch_path, head[:12], wt):
            with open(os.path.join(wt, "include", "backoff.hh"), encoding="utf-8") as f:
                assert "return 2;" in f.read()            # worktree 内には当たっている
            with open(hh_base, encoding="utf-8") as f:
                assert f.read() == _FAKE_BACKOFF_HH        # base repo の working-tree は無傷
    assert not os.path.exists(wt)
    assert git("status", "--porcelain") == ""


def test_patchharness_checkout_raises_on_add_failure():
    """存在しない pin では git worktree add が失敗し、fails-closed で RuntimeError になる
    (親ディレクトリの後始末も行う — テスト後に残骸が残らないことも確認)。"""
    from orchestrator.campaign import patchharness
    sub, head, git = _fake_ccbench_repo()
    try:
        with patchharness.checkout("0" * 40, base_dir=sub):
            assert False, "存在しない commit で worktree add は失敗すべき"
    except RuntimeError as e:
        assert "worktree add" in str(e)


def test_patchharness_checkout_leak_raises():
    """worktree 破棄後も base の一覧に残っていたら (leak) 沈黙せず例外にする (規律6)。
    実 remove は正常に走らせつつ、直後の監視関数だけ「まだ残っている」ふりに差し替えて
    fails-closed 経路を検査する (removal 自体を偽装すると実体の破棄まで検証できない)。"""
    from orchestrator.campaign import patchharness
    sub, head, git = _fake_ccbench_repo()
    saved = patchharness._worktree_paths
    captured = {}
    try:
        with patchharness.checkout(head[:12], base_dir=sub) as wt:
            captured["path"] = wt
            patchharness._worktree_paths = lambda base: [wt]   # exit 直前に「残存」を偽装
        assert False, "leak を検出したら例外にすべき"
    except RuntimeError as e:
        assert "leak" in str(e)
    finally:
        patchharness._worktree_paths = saved
    assert not os.path.exists(captured["path"])     # 実体は正しく破棄されている (leak は偽装のみ)


def test_loop_resume_repairs_tail_before_replay_and_surfaces_receipt():
    from orchestrator.campaign import loop as L

    out_root = _tmpdir("izanagi_loop_tail_resume_")
    cfg = ident.bind_admission_policy(
        CampaignConfig(spec_slug="t", search_tag="enum",
                       spec_content="tail-resume", ccbench_commit="deadbeef"),
        _BUILD_CONTEXT.policy,
    )
    layout = campaign_layout(str(ident.campaign_id(_bound(cfg))), out_root).ensure()
    _write_certified_lock(layout, _bound(cfg))
    prior_receipt, prior_sha = _wal_admission_receipt("prior")
    _attempt_start(layout, "prior", "prior-attempt", prior_receipt, prior_sha)
    _attempt_stage(
        layout, "prior", STAGE_BUILD_DONE, "prior-attempt", prior_sha,
    )
    _attempt_stage(
        layout, "prior", STAGE_COMMIT, "prior-attempt", prior_sha,
        fitness_tps=1.0,
    )
    with open(layout.wal_file, "ab") as stream:
        stream.write("途中".encode("utf-8")[:4])
    genome = Genome("silo", {"BACK_OFF": 1})
    messages = []

    def fake_eval(candidate, candidate_layout, env_tag, *args, **kwargs):
        records, truncated = wal.read_records_checked(candidate_layout)
        assert truncated is False and [r.variant for r in records] == ["prior"] * 3
        variant = pipeline.variant_id(candidate, kwargs["src_token"])
        admission = derive_build_admission(
            kwargs["build_context"], kwargs["source_evidence"],
        )
        attempt_id = "current-attempt"
        _attempt_start(
            candidate_layout, variant, attempt_id,
            admission.as_wal_receipt(), admission.receipt_sha256,
        )
        _attempt_stage(
            candidate_layout, variant, STAGE_BUILD_DONE, attempt_id,
            admission.receipt_sha256,
        )
        _attempt_stage(
            candidate_layout, variant, STAGE_COMMIT, attempt_id,
            admission.receipt_sha256, fitness_tps=2.0,
        )
        return EvalResult(genome=candidate, variant=variant, certified=True,
                          aborted=False, fitness_tps=2.0)

    saved_eval, saved_sd = L.evaluate, L.source_digest
    L.evaluate = fake_eval
    L.source_digest = _sd_mock("stock")
    try:
        summary = L.run_campaign(
            cfg, [genome], PerfConfig(records=1, threads=1),
            _AUTH_CONTRACT.env_tag, _AUTH_CONTRACT.clocks_per_us,
            numactl=list(_AUTH_CONTRACT.numactl),
            authorization_contract=_AUTHORIZATION,
            do_bench=False, output_root=out_root, log=messages.append,
            build_context=_BUILD_CONTEXT, declared_use_class="official")
    finally:
        L.evaluate, L.source_digest = saved_eval, saved_sd
    records, truncated = wal.read_records_checked(layout)
    repair_messages = [m for m in messages if "WAL tail repair:" in m]
    assert summary.committed == 1 and truncated is False
    assert [r.stage for r in records] == [
        STAGE_BUILD_START, STAGE_BUILD_DONE, STAGE_COMMIT,
        STAGE_BUILD_START, STAGE_BUILD_DONE, STAGE_COMMIT,
    ]
    assert len(repair_messages) == 1
    repair_payload = json.loads(repair_messages[0].split(": ", 1)[1])
    assert repair_payload["status"] == "repaired"
    assert repair_payload["removed_bytes"] == 4
    assert len(repair_payload["removed_sha256"]) == 64
    assert os.path.exists(repair_payload["receipt_path"])


@pytest.mark.usefixtures("ratified_enforcement_source")
def test_loop_does_not_append_abort_after_wal_io_error():
    from orchestrator.campaign import loop as L

    failures = (
        wal.WalAppendError("fixture-wal", 20, 7, "write", OSError("disk")),
        wal.WalFramingError("unframed"),
    )
    for index, failure in enumerate(failures):
        out_root = _tmpdir("izanagi_loop_wal_error_")
        cfg = CampaignConfig(spec_slug="t", search_tag="enum",
                             spec_content=f"wal-error-{index}",
                             ccbench_commit="deadbeef")
        genome = Genome("silo", {"BACK_OFF": 1})

        def fail(*args, **kwargs):
            raise failure

        saved_eval, saved_sd = L.evaluate, L.source_digest
        L.evaluate = fail
        L.source_digest = _sd_mock("stock")
        caught = None
        try:
            try:
                L.run_campaign(
                    cfg, [genome], PerfConfig(records=1, threads=1),
                    _AUTH_CONTRACT.env_tag, _AUTH_CONTRACT.clocks_per_us,
                    numactl=list(_AUTH_CONTRACT.numactl),
                    authorization_contract=_AUTHORIZATION,
                    do_bench=False, output_root=out_root,
                    log=lambda message: None, build_context=_BUILD_CONTEXT,
                    declared_use_class="official")
            except (wal.WalAppendError, wal.WalFramingError) as exc:
                caught = exc
        finally:
            L.evaluate, L.source_digest = saved_eval, saved_sd
        bound_cfg = _bound(cfg)
        layout = campaign_layout(str(ident.campaign_id(bound_cfg)), out_root)
        assert caught is failure
        assert wal.read_records(layout) == []


def _balanced_prepared_fixture(
        layout, arm, *, reps=20, use_perf=True, perf_preflight_receipt=None):
    events = []
    result = EvalResult(
        genome=Genome("silo", {"BACK_OFF": int(arm == "A")}),
        variant=f"variant-{arm}", certified=True, aborted=False,
    )

    def abort(reason, note, extra=None):
        result.aborted = True
        result.notes.append(note)
        events.append(("abort", reason, extra))
        return result

    def emit(*args):
        events.append(("emit", args[2], args[4]))

    prepared = pipeline._PreparedEvaluation(
        result=result,
        layout=layout,
        env_tag="linux-baremetal",
        perf_binary=arm,
        perf=PerfConfig(records=1000, threads=2, reps=reps),
        clocks_per_us=1800,
        numactl=None,
        do_bench=True,
        do_settle=False,
        log=lambda *_args: None,
        abort=abort,
        emit=emit,
        build_attempt_id=f"attempt-{arm}",
        build_admission_receipt_sha256=arm.lower() * 64,
        contract_sha256="c" * 64,
        verify_tags=[pipeline.LEGACY_TAG],
        receipt_for=lambda payload: payload,
        bench_max_rounds=1,
        record_rep_returncodes=False,
        qualification_policy=None,
        holdout_observation_admission=None,
        use_perf=use_perf,
        perf_preflight_receipt=perf_preflight_receipt,
        active_screening=None,
        screening_disabled_payload=None,
    )
    return prepared, events


def _exercise_balanced_schedule(
        values_for_block, *, settle_result=None, competing_fn=None, reps=20,
        arm_names=("variant-arm", "baseline-arm"), use_perf=True,
        perf_preflight_receipt=None, workload="balanced", root_seed="0" * 64):
    root = _tmpdir("izanagi_balanced_schedule_")
    layout = CampaignLayout(root)
    arm_a, events_a = _balanced_prepared_fixture(
        layout, "A", reps=reps, use_perf=use_perf,
        perf_preflight_receipt=perf_preflight_receipt,
    )
    arm_b, events_b = _balanced_prepared_fixture(
        layout, "B", reps=reps, use_perf=use_perf,
        perf_preflight_receipt=perf_preflight_receipt,
    )
    probes = []
    locks = []
    block_calls = []
    block_kwargs = []
    writes_during_blocks = []
    clock = iter(range(1_000_000, 2_000_000))

    @contextlib.contextmanager
    def one_lock():
        locks.append("acquire")
        yield

    def measure(binary, records, threads, clocks_per_us, **kwargs):
        writes_during_blocks.append(
            os.path.exists(os.path.join(root, "balanced-schedule-receipt.json"))
            or bool(events_a or events_b)
        )
        block_index = len(block_calls)
        block_calls.append(binary)
        block_kwargs.append(dict(kwargs))
        values = list(values_for_block(binary, block_index))
        observations = kwargs["rep_observations"]
        timestamps = kwargs["rep_timestamps"]
        observations[:] = [
            {"rep_index": index, "throughput": value}
            for index, value in enumerate(values)
        ]
        timestamps[:] = [
            {"rep_index": index, "started_at_ns": next(clock),
             "finished_at_ns": next(clock)}
            for index in range(5)
        ]
        from orchestrator.calibrator.model import ScalePoint
        measured = ScalePoint(records=records, threads=threads, run_cmd=binary)
        measured.throughputs = values
        return measured

    config = pipeline.BalancedScheduleConfig(
        workload=workload, root_seed=root_seed, arm_names=arm_names,
    )
    if settle_result is None:
        settle_result = {"settled": True, "load1": 0.0}

    def probe():
        probes.append("probe")
        return [] if competing_fn is None else competing_fn()

    with unittest_mock.patch.object(pipeline, "bench_lock", one_lock), \
            unittest_mock.patch.object(
                pipeline, "settle", lambda: settle_result), \
            unittest_mock.patch.object(
                pipeline, "competing_bench_pids", probe), \
            unittest_mock.patch.object(pipeline, "measure_point", measure), \
            unittest_mock.patch.object(
                pipeline, "_commit_prepared",
                lambda prepared, _bench: prepared.result):
        results, receipt = pipeline._run_balanced_schedule(
            [arm_a, arm_b], config,
        )
    return {
        "results": results,
        "receipt": receipt,
        "probes": probes,
        "locks": locks,
        "blocks": block_calls,
        "block_kwargs": block_kwargs,
        "events": events_a + events_b,
        "writes_during_blocks": writes_during_blocks,
        "root": root,
    }


def test_balanced_schedule_probes_each_five_rep_block_independently():
    """M1: two groups have eight independently observable block probes."""
    run = _exercise_balanced_schedule(lambda _arm, _block: [100.0] * 5)
    assert len(run["probes"]) == 8


def test_balanced_schedule_holds_one_lock_for_all_blocks():
    run = _exercise_balanced_schedule(lambda _arm, _block: [100.0] * 5)
    assert run["locks"] == ["acquire"]


def test_balanced_schedule_writes_nothing_until_every_block_finishes():
    run = _exercise_balanced_schedule(lambda _arm, _block: [100.0] * 5)
    assert run["writes_during_blocks"] == [False] * 8
    assert os.path.isfile(
        os.path.join(run["root"], "balanced-schedule-receipt.json")
    )


def test_balanced_schedule_records_aggregate_unstable_not_constant_false():
    """M2: a genuinely noisy complete arm must carry unstable=true."""
    run = _exercise_balanced_schedule(
        lambda _arm, block: [10.0, 20.0, 30.0, 40.0, 50.0]
        if block % 2 == 0 else [100.0, 200.0, 300.0, 400.0, 500.0]
    )
    assert run["receipt"]["arms"]["variant-arm"]["unstable"] is True


def test_balanced_schedule_cv_is_all_rep_cv_not_mean_block_cv():
    """M3: constant blocks at different levels have zero block CV but nonzero arm CV."""
    seen = {"A": 0, "B": 0}

    def values(arm, _block):
        seen[arm] += 1
        return [float(seen[arm] * 100)] * 5

    run = _exercise_balanced_schedule(values)
    arm = run["receipt"]["arms"]["variant-arm"]
    expected = statistics.stdev(arm["tps"]) / statistics.mean(arm["tps"])
    assert arm["cv"] == expected and arm["cv"] != statistics.mean(arm["block_cvs"])


def test_balanced_schedule_receipt_rows_match_sizing_schema_exactly():
    """One 60-pair workload emits 12 five-pair blocks in sizing row form."""
    run = _exercise_balanced_schedule(
        lambda arm, block: [float(1000 + block * 10 + index)
                            for index in range(5)],
        reps=60,
        arm_names=("fixed5", "no-backoff"),
    )
    rows = run["receipt"]["reps"]
    assert len(rows) == 120
    assert {row["arm"] for row in rows} == {"fixed5", "no-backoff"}
    assert {row["pair_index"] for row in rows} == set(range(60))
    assert {row["block"] for row in rows} == set(range(12))
    assert all(set(row) == {
        "arm", "block", "block_position", "ended_at_ns", "group",
        "pair_index", "started_at_ns", "tps",
    } for row in rows)
    assert all(row["group"] == row["pair_index"] // 10 for row in rows)
    assert all(row["block"] == row["pair_index"] // 5 for row in rows)
    assert all(
        row["block_position"] == row["pair_index"] % 5 for row in rows
    )
    intervals = [(row["started_at_ns"], row["ended_at_ns"]) for row in rows]
    assert intervals == sorted(intervals)
    assert all(start < end for start, end in intervals)


def test_balanced_receipt_real_producer_round_trips_consumer_and_sizing():
    """The producer's exact receipt is accepted unchanged by both consumers."""
    from orchestrator.campaign import paper_story_a1_paired as paired

    policy = paired.load_policy(paired.V3_PILOT_STUDY_ID)[0]
    workloads = []
    receipts = []
    for workload_name in paired.WORKLOAD_ORDER:
        arm_names = paired._workload_arm_order(policy, workload_name)
        root_seed = paired._workload_plan(
            policy, workload_name,
        )["schedule_root_seed"]
        run = _exercise_balanced_schedule(
            lambda arm, block: [
                float(
                    10_000
                    + (1_000 if arm == "A" else 0)
                    + block * 10
                    + index
                )
                for index in range(5)
            ],
            reps=60,
            arm_names=arm_names,
            workload=workload_name,
            root_seed=root_seed,
        )
        receipt = run["receipt"]
        arm_results = {
            name: {
                "raw_tps": receipt["arms"][name]["tps"],
                "variant": receipt["arms"][name]["variant"],
            }
            for name in arm_names
        }
        assert paired._balanced_schedule_receipt_errors(
            policy, workload_name, receipt, arm_results,
        ) == []
        receipts.append(receipt)
        workloads.append({
            "arms": arm_results,
            "campaign_id": f"campaign-{workload_name}",
            "errors": [],
            "schedule_receipt": {"document": receipt},
            "valid": True,
            "workload": workload_name,
        })

    sizing = paired._balanced_sizing_pilot_document(
        policy, {"complete": True, "workloads": workloads},
    )
    assert all(
        workload["observations"] is receipt["reps"]
        for workload, receipt in zip(sizing["workloads"], receipts)
    )


def test_balanced_schedule_requires_every_rep_at_the_runner_boundary():
    """A complete block is accepted only through runner's strict rep contract."""
    run = _exercise_balanced_schedule(lambda _arm, _block: [100.0] * 5)
    assert run["block_kwargs"]
    assert all(
        kwargs.get("require_all_reps") is True
        for kwargs in run["block_kwargs"]
    )


def test_balanced_schedule_records_canonical_perf_observation():
    """A no-perf preflight is projected into each real balanced BENCH_DONE."""
    receipt = perf_preflight_module.probe_perf_availability(
        perf_candidates=(),
        subprocess_runner=lambda *_args, **_kwargs: (_ for _ in ()).throw(
            FileNotFoundError("perf")
        ),
    )
    run = _exercise_balanced_schedule(
        lambda _arm, _block: [100.0] * 5,
        use_perf=False,
        perf_preflight_receipt=receipt,
    )
    bench_payloads = [
        event[2] for event in run["events"]
        if event[:2] == ("emit", STAGE_BENCH_DONE)
    ]
    assert len(bench_payloads) == 2
    assert all(
        payload["perf_observation"]["use_perf"] is False
        and payload["perf_observation"]["counter_status"] == "not_required"
        and payload["perf_observation"]["preflight"] == receipt
        for payload in bench_payloads
    )


def test_balanced_schedule_seed_bit_mapping_is_independently_rederived():
    """M8: the consumer derives bit 0=ABBA and bit 1=BAAB without producer reuse."""
    root_seed = "0" * 64
    bits = tuple(
        hashlib.sha256(
            (root_seed
             + f"a1-balanced5/v1|workload=balanced|group={group}").encode()
        ).digest()[-1] & 1
        for group in range(2)
    )
    expected = tuple(
        (("A",) * 5 + ("B",) * 10 + ("A",) * 5)
        if bit == 0 else
        (("B",) * 5 + ("A",) * 10 + ("B",) * 5)
        for bit in bits
    )
    actual = pipeline.derive_balanced_schedule(
        root_seed, "balanced", 2,
    )
    assert actual.blocks == expected


def test_balanced_schedule_redraw_uses_registered_preimage():
    """M5: a homogeneous first draw uses the policy's exact counter preimage."""
    root_seed = "0" * 63 + "5"
    actual = pipeline.derive_balanced_schedule(root_seed, "balanced", 2)
    assert actual.seed_counter == 1
    assert actual.effective_root_seed == (
        "e22dd77a1336ceffd09ed2b904703beee9924e68fae34dfa67159bdb13ba7897"
    )
    assert actual.group_bits == (1, 0)


def test_canonical_build_source_state_accepts_exact_clean_checkout():
    """Acceptance implication: exact policy HEAD plus tracked-clean passes."""
    sub, head, _git = _fake_ccbench_repo()
    Path(sub, "untracked-build-output").write_text("ignored", encoding="utf-8")
    pipeline._require_canonical_build_source_state(
        sub, head, build_kind="trace",
    )


def test_canonical_build_source_state_rejects_pin_or_tracked_drift():
    """Rejection implication: either wrong HEAD or tracked dirt rejects locally."""
    sub, head, _git = _fake_ccbench_repo()
    for build_kind, mutation in (("trace", "pin"), ("perf", "tracked")):
        if mutation == "tracked":
            Path(sub, "include/backoff.hh").write_text(
                "tracked drift\n", encoding="utf-8",
            )
        try:
            pipeline._require_canonical_build_source_state(
                sub,
                ("0" * 40 if mutation == "pin" else head),
                build_kind=build_kind,
            )
        except pipeline._CanonicalBuildSourceStateError as exc:
            assert exc.build_kind == build_kind
        else:
            raise AssertionError(f"{mutation} build source drift was accepted")


def test_balanced_build_boundary_is_one_guarded_trace_perf_wrapper():
    """M10 build layer: one guard dominates exact trace and perf build calls."""
    tree = ast.parse(Path(pipeline.__file__).read_text(encoding="utf-8"))
    core = next(
        node for node in tree.body
        if isinstance(node, ast.FunctionDef)
        and node.name == "_prepare_evaluation_core"
    )
    wrapper = next(
        node for node in ast.walk(core)
        if isinstance(node, ast.FunctionDef) and node.name == "_build_one"
    )
    wrapper_calls = [
        node for node in ast.walk(wrapper) if isinstance(node, ast.Call)
    ]
    assert sum(
        isinstance(call.func, ast.Name)
        and call.func.id == "_require_canonical_build_source_state"
        for call in wrapper_calls
    ) == 1
    build_calls = collections.Counter(
        ast.unparse(call.func) for call in wrapper_calls
        if ast.unparse(call.func) in {"buildcache.build", "buildcache.build_v2"}
    )
    assert build_calls == {
        "buildcache.build": 1,
        "buildcache.build_v2": 2,
    }
    invocations = [
        call for call in ast.walk(core)
        if isinstance(call, ast.Call)
        and isinstance(call.func, ast.Name)
        and call.func.id == "_build_one"
    ]
    assert len(invocations) == 2
    assert [ast.unparse(call.keywords[0].value) for call in invocations] == [
        "True", "False",
    ]
    handlers = [
        handler for handler in ast.walk(core)
        if isinstance(handler, ast.ExceptHandler)
        and isinstance(handler.type, ast.Name)
        and handler.type.id == "_CanonicalBuildSourceStateError"
    ]
    assert len(handlers) == 1
    assert "'build-source-state-error'" in ast.unparse(handlers[0])


def test_balanced_loop_binds_build_guard_to_campaign_policy_pin():
    """The balanced split passes the campaign's policy-derived pin verbatim."""
    from orchestrator.campaign import loop as campaign_loop

    tree = ast.parse(Path(campaign_loop.__file__).read_text(encoding="utf-8"))
    production = next(
        node for node in tree.body
        if isinstance(node, ast.FunctionDef) and node.name == "run_campaign"
    )
    calls = [
        call for call in ast.walk(production)
        if isinstance(call, ast.Call)
        and isinstance(call.func, ast.Name)
        and call.func.id == "_prepare_evaluation"
    ]
    assert len(calls) == 1
    keywords = {item.arg: item.value for item in calls[0].keywords}
    assert ast.unparse(keywords["canonical_build_pin"]) == "cfg.ccbench_commit"
    assert (
        "cfg.search_config.get('arm_order') != list(balanced_schedule.arm_names)"
        in ast.unparse(production)
    )


def test_production_passes_real_balanced_schedule_config_to_run_campaign():
    """Production has one validated policy-options route into run_campaign."""
    source_path = Path(_REPOSITORY) / "orchestrator/campaign/paper_story_a1_paired.py"
    tree = ast.parse(source_path.read_text(encoding="utf-8"), filename=str(source_path))
    functions = {
        node.name: node for node in tree.body
        if isinstance(node, ast.FunctionDef)
    }
    production = next(
        node for node in tree.body
        if isinstance(node, ast.FunctionDef) and node.name == "run_measurement"
    )
    execution_option_calls = [
        call for call in ast.walk(production)
        if isinstance(call, ast.Call)
        and isinstance(call.func, ast.Name)
        and call.func.id == "_campaign_execution_options"
    ]
    validator_calls = [
        call for call in ast.walk(production)
        if isinstance(call, ast.Call)
        and isinstance(call.func, ast.Name)
        and call.func.id == "_require_registered_execution_options"
    ]
    run_calls = [
        call for call in ast.walk(production)
        if isinstance(call, ast.Call)
        and isinstance(call.func, ast.Name)
        and call.func.id == "run_campaign"
    ]
    assert len(execution_option_calls) == len(validator_calls) == len(run_calls) == 1
    assert execution_option_calls[0].lineno < validator_calls[0].lineno \
        < run_calls[0].lineno
    assert [
        keyword.value.id for keyword in run_calls[0].keywords
        if keyword.arg is None and isinstance(keyword.value, ast.Name)
    ] == ["execution_options"]

    options_helper = functions["_campaign_execution_options"]
    configs = [
        call for call in ast.walk(options_helper)
        if isinstance(call, ast.Call)
        and isinstance(call.func, ast.Name)
        and call.func.id == "BalancedScheduleConfig"
    ]
    assert len(configs) == 1
    config_keywords = {item.arg: item.value for item in configs[0].keywords}
    assert set(config_keywords) == {
        "workload", "root_seed", "arm_names", "receipt_name",
    }
    assert ast.unparse(config_keywords["arm_names"]) == (
        "_workload_arm_order(policy, workload_name)"
    )

    from orchestrator.campaign import paper_story_a1_paired as paired
    v3 = paired.load_policy(paired.V3_PILOT_STUDY_ID)[0]
    for workload_name in paired.WORKLOAD_ORDER:
        options = paired._campaign_execution_options(v3, workload_name)
        registered = paired._require_registered_execution_options(
            v3, workload_name, options,
        )
        schedule = registered["balanced_schedule"]
        assert registered["bench_max_rounds"] == 1
        assert schedule.arm_names == paired._workload_arm_order(
            v3, workload_name,
        )
        assert schedule.root_seed == paired._workload_plan(
            v3, workload_name,
        )["schedule_root_seed"]
        assert schedule.receipt_name == paired.BALANCED_SCHEDULE_RECEIPT_NAME
        assert paired.campaign_config(
            v3, workload_name,
        ).ccbench_commit == paired.CANONICAL_CCBENCH_OID
    legacy = paired.load_policy()[0]
    assert paired._campaign_execution_options(legacy, "balanced") == {}
    assert paired._require_registered_execution_options(
        legacy, "balanced", {},
    ) == {}


@pytest.mark.usefixtures("ratified_enforcement_source")
def test_run_campaign_wires_nondefault_bench_max_rounds_to_evaluate():
    from orchestrator.campaign import loop as campaign_loop
    captured = []
    genome = Genome("silo", {"BACK_OFF": 1})

    def fake_evaluate(candidate, *_args, **kwargs):
        captured.append(kwargs.get("bench_max_rounds"))
        return EvalResult(
            genome=candidate,
            variant=pipeline.variant_id(candidate, kwargs["src_token"]),
            certified=True,
            aborted=False,
        )

    saved_evaluate = campaign_loop.evaluate
    saved_source_digest = campaign_loop.source_digest
    campaign_loop.evaluate = fake_evaluate
    campaign_loop.source_digest = _sd_mock("stock")
    try:
        campaign_loop.run_campaign(
            CampaignConfig(
                spec_slug="balanced-round-wiring",
                search_tag="test",
                spec_content="bench max rounds wiring",
                ccbench_commit="deadbeef",
            ),
            [genome],
            PerfConfig(records=1, threads=1),
            _AUTH_CONTRACT.env_tag,
            _AUTH_CONTRACT.clocks_per_us,
            numactl=list(_AUTH_CONTRACT.numactl),
            do_bench=False,
            output_root=_tmpdir("izanagi_round_wiring_"),
            log=lambda *_args: None,
            authorization_contract=_AUTHORIZATION,
            build_context=_BUILD_CONTEXT,
            declared_use_class="official",
            bench_max_rounds=1,
        )
    finally:
        campaign_loop.evaluate = saved_evaluate
        campaign_loop.source_digest = saved_source_digest
    assert captured == [1]


@pytest.mark.usefixtures("ratified_enforcement_source")
def test_run_campaign_forwards_only_non_none_holdout_observation_admission():
    from orchestrator.campaign import loop as campaign_loop

    parameter = inspect.signature(campaign_loop.run_campaign).parameters[
        "holdout_observation_admission"
    ]
    assert parameter.kind is inspect.Parameter.KEYWORD_ONLY
    assert parameter.default is None

    captured = []
    genome = Genome("silo", {"BACK_OFF": 1})
    admission = object()

    def fake_evaluate(candidate, *_args, **kwargs):
        captured.append((
            "holdout_observation_admission" in kwargs,
            kwargs.get("holdout_observation_admission"),
        ))
        return EvalResult(
            genome=candidate,
            variant=pipeline.variant_id(candidate, kwargs["src_token"]),
            certified=True,
            aborted=False,
        )

    saved_evaluate = campaign_loop.evaluate
    saved_source_digest = campaign_loop.source_digest
    campaign_loop.evaluate = fake_evaluate
    campaign_loop.source_digest = _sd_mock("stock")
    try:
        for label, options in (
            ("default", {}),
            ("admitted", {"holdout_observation_admission": admission}),
        ):
            campaign_loop.run_campaign(
                CampaignConfig(
                    spec_slug=f"holdout-transport-{label}",
                    search_tag="test",
                    spec_content=f"holdout transport {label}",
                    ccbench_commit="deadbeef",
                ),
                [genome],
                PerfConfig(records=1, threads=1),
                _AUTH_CONTRACT.env_tag,
                _AUTH_CONTRACT.clocks_per_us,
                numactl=list(_AUTH_CONTRACT.numactl),
                do_bench=False,
                output_root=_tmpdir(f"izanagi_holdout_transport_{label}_"),
                log=lambda *_args: None,
                authorization_contract=_AUTHORIZATION,
                build_context=_BUILD_CONTEXT,
                declared_use_class="official",
                **options,
            )
    finally:
        campaign_loop.evaluate = saved_evaluate
        campaign_loop.source_digest = saved_source_digest

    assert captured == [(False, None), (True, admission)]


def test_run_campaign_rejects_balanced_schedule_with_holdout_admission_before_output():
    from orchestrator.campaign import loop as campaign_loop

    output_root = Path(_tmpdir("izanagi_balanced_holdout_parent_")) / "must-not-exist"
    freeze = s8b_ratified_freeze.load_legacy_freeze(Path(_REPOSITORY))
    rr80 = freeze.document["holdouts"]["rr80"]
    perf = PerfConfig(
        records=rr80["records"],
        threads=rr80["threads"],
        workload=dict(rr80["ycsb"]),
        reps=20,
    )
    receipt = holdout_observation._new_durable_attempt_consumption_receipt(
        attempt_id="test-campaign-balanced-holdout",
        permitted_run_once_calls=perf.reps,
    )
    admission = (
        holdout_observation._issue_holdout_observation_admission_from_receipt(
            receipt=receipt,
            verified_freeze_document=freeze.document,
            freeze_holdout_key="rr80",
        )
    )
    holdout_observation.assert_issued_holdout_observation(admission)
    schedule = pipeline.BalancedScheduleConfig(
        workload="rr80",
        root_seed="1" * 64,
        arm_names=("a", "b"),
    )
    genomes = [
        Genome("silo", {"BACK_OFF": 1}),
        Genome("silo", {"BACK_OFF": 2}),
    ]
    with pytest.raises(
        ValueError,
        match=r"two arms require 2 \* perf\.reps observations",
    ):
        campaign_loop.run_campaign(
            CampaignConfig(
                spec_slug="balanced-holdout-conflict",
                search_tag="test",
                spec_content="balanced holdout conflict",
                ccbench_commit="deadbeef",
                search_config={
                    "pairing_design": "balanced-a5b5-b5a5-v1",
                    "arm_order": list(schedule.arm_names),
                    "workload": {"name": schedule.workload},
                },
            ),
            genomes,
            perf,
            _AUTH_CONTRACT.env_tag,
            _AUTH_CONTRACT.clocks_per_us,
            numactl=list(_AUTH_CONTRACT.numactl),
            do_bench=True,
            authorization_contract=_AUTHORIZATION,
            build_context=_BUILD_CONTEXT,
            declared_use_class="official",
            output_root=str(output_root),
            bench_max_rounds=1,
            balanced_schedule=schedule,
            holdout_observation_admission=admission,
        )
    assert not output_root.exists()


def test_run_campaign_rejects_multiple_genomes_with_holdout_admission_before_output():
    from orchestrator.campaign import loop as campaign_loop

    output_root = Path(_tmpdir("izanagi_multi_holdout_parent_")) / "must-not-exist"
    freeze = s8b_ratified_freeze.load_legacy_freeze(Path(_REPOSITORY))
    rr80 = freeze.document["holdouts"]["rr80"]
    perf = PerfConfig(
        records=rr80["records"],
        threads=rr80["threads"],
        workload=dict(rr80["ycsb"]),
    )
    receipt = holdout_observation._new_durable_attempt_consumption_receipt(
        attempt_id="test-campaign-multiple-genomes",
        permitted_run_once_calls=perf.reps,
    )
    admission = (
        holdout_observation._issue_holdout_observation_admission_from_receipt(
            receipt=receipt,
            verified_freeze_document=freeze.document,
            freeze_holdout_key="rr80",
        )
    )
    holdout_observation.assert_issued_holdout_observation(admission)
    with pytest.raises(
        ValueError,
        match=r"attempt-bound token has a finite run_once allowance",
    ):
        campaign_loop.run_campaign(
            CampaignConfig(
                spec_slug="multi-genome-holdout-conflict",
                search_tag="test",
                spec_content="multi-genome holdout conflict",
                ccbench_commit="deadbeef",
            ),
            [
                Genome("silo", {"BACK_OFF": 1}),
                Genome("silo", {"BACK_OFF": 2}),
            ],
            perf,
            _AUTH_CONTRACT.env_tag,
            _AUTH_CONTRACT.clocks_per_us,
            numactl=list(_AUTH_CONTRACT.numactl),
            do_bench=True,
            authorization_contract=_AUTHORIZATION,
            build_context=_BUILD_CONTEXT,
            declared_use_class="official",
            output_root=str(output_root),
            bench_max_rounds=1,
            holdout_observation_admission=admission,
        )
    assert not output_root.exists()


def test_balanced_schedule_quality_gate_signatures_accept_complete_input():
    """Acceptance implication: complete settled input implies two committed results."""
    run = _exercise_balanced_schedule(lambda _arm, _block: [100.0] * 5)
    assert len(run["results"]) == 2 and all(
        result.certified and not result.aborted for result in run["results"]
    )


def test_balanced_schedule_quality_gate_signatures_reject_each_named_condition():
    """Rejection implication: each named bad input implies whole-workload abort."""
    probe_error = pipeline.CompetingBenchProbeError(
        "exec-failure", ["pgrep"], errno=5,
    )
    cases = (
        ("bench-unsettled", {"settled": False}, None, [100.0] * 5),
        ("bench-probe-error", None,
         lambda: (_ for _ in ()).throw(probe_error), [100.0] * 5),
        ("bench-competing-tenant", None, lambda: ["999 ycsb_silo.exe"],
         [100.0] * 5),
        ("bench-no-throughput", None, None, []),
        ("bench-no-throughput", None, None, [100.0] * 4 + [None]),
        ("bench-cv-undefined", None, None, [0.0] * 5),
    )
    for reason, settled, probe, values in cases:
        run = _exercise_balanced_schedule(
            lambda _arm, _block, values=values: values,
            settle_result=settled,
            competing_fn=probe,
        )
        abort_reasons = [
            event[1] for event in run["events"] if event[0] == "abort"
        ]
        assert abort_reasons == [reason, reason]
        assert run["receipt"] == {}


def test_a1_build_source_contract_rejects_caller_chosen_digest():
    """An arbitrary mapping cannot opt a dirty source out of the clean gate."""
    sub, head, _git = _fake_ccbench_repo()
    Path(sub, "include/backoff.hh").write_text("undeclared edit\n", encoding="utf-8")
    for kind in ("trace", "perf"):
        try:
            pipeline._require_canonical_build_source_state(
                sub, head, build_kind=kind,
                a1_source_context={"root": sub, "expected": "a" * 64},
            )
        except pipeline._CanonicalBuildSourceStateError as exc:
            assert "context type differs" in str(exc)
        else:
            raise AssertionError("caller-selected dirty source contract was accepted")


def _run():
    fns = [v for k, v in sorted(globals().items())
           if k.startswith("test_") and callable(v)]
    passed = failed = skipped = 0
    for fn in fns:
        try:
            _refresh_certified_writer_authority()
            fn()
            print(f"PASS {fn.__name__}")
            passed += 1
        except Skip as e:
            print(f"SKIP {fn.__name__}: {e}")
            skipped += 1
        except AssertionError as e:
            print(f"FAIL {fn.__name__}: {e}")
            failed += 1
        except Exception as e:  # noqa: BLE001
            print(f"ERROR {fn.__name__}: {type(e).__name__}: {e}")
            failed += 1
    print(f"\n{passed} passed, {failed} failed, {skipped} skipped")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(_run())
