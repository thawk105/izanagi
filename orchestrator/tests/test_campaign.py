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
import errno
import fcntl
import hashlib
import importlib
import inspect
import io
import json
import os
import shutil
import subprocess
import sys
import tempfile
import threading
import time
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
sys.path.insert(0, _ORCH)

from campaign import (buildcache, campaign_lock, genome, ident, pin, pipeline,  # noqa: E402
                      site_policy, source_digest, trigger_gate_binding, wal)
from campaign import env_contract as ec                          # noqa: E402
from campaign.build_admission import (  # noqa: E402
    BuildAdmission,
    BuildAdmissionError,
    GeneratorId,
    add_coder_build_authority_argument,
    build_run_context,
    derive_build_admission,
)
from campaign import layout as layout_module                     # noqa: E402
from campaign.layout import (CampaignLayout,                     # noqa: E402
                             ExplorationCampaignLayout,
                             campaign_layout, ensure_exploration_namespace,
                             exploration_campaign_layout)
from campaign.lock import BenchBusy, bench_lock                  # noqa: E402
from campaign.model import (CampaignConfig, Genome,              # noqa: E402
                            COMMIT_CONTRACT_SHA256_KEY,
                            STAGE_BENCH_DONE, STAGE_BUILD_DONE, STAGE_BUILD_START,
                            STAGE_COMMIT, STAGE_ABORT, STAGE_VERIFY_DONE,
                            STAGE_S1_SESSION, STAGE_S8B_ORACLE_SESSION,
                            STAGES, WAL_STAGES, WalRecord)
from campaign.pipeline import (EvalResult, PerfConfig,           # noqa: E402
                               ScreeningConfig)
from campaign.reflux_ir import TriggerGateIR, emit_predicate     # noqa: E402
from campaign.source_digest import SourceEvidence                # noqa: E402
from skiputil import Skip, skip                                  # noqa: E402
from verifier.model import (Anomaly, CycleEdge, EdgeReason,       # noqa: E402
                            Integrity, RW, VerifyResult)
from certified_writer_fixtures import (                          # noqa: E402
    build_admission_fixture,
    build_source_drift_fixture,
)
from campaign_lock_test_support import build_v2_lock              # noqa: E402

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
        wal.log(layout, variant, STAGE_COMMIT, contract.env_tag, {
            **propagated, "fitness_tps": 100.0,
            "contract_sha256": contract.contract_sha256,
        })
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
    # T-671 で H が identity から外れ、current は admission-policy 世代の ID に戻る。
    assert current == _T343_REPRESENTATIVE_CAMPAIGN_ID
    assert current not in {historical, _T530_REPRESENTATIVE_CAMPAIGN_ID}


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
    from campaign import loop as L

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
                build_context=_BUILD_CONTEXT, log=lambda _message: None,
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
    # T-671 では runtime authority H を hash しないため T343 identity が current。
    assert str(ident.campaign_id(_bound(cfg))) == _T343_REPRESENTATIVE_CAMPAIGN_ID
    assert str(ident.campaign_id(_bound(cfg))) not in {
        _PRE_T343_REPRESENTATIVE_CAMPAIGN_ID,
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

    from campaign.backoff_sweep import WORKLOADS as BACKOFF_WORKLOADS
    from campaign.backoff_sweep import config_for as backoff_config
    from campaign.s6_sort_sweep import config_for as s6_config

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
        backoff_cfgs = [
            _bound(dataclasses.replace(
                backoff_config(tag, workload), ccbench_commit="dff0f1e",
            ))
            for tag, workload in BACKOFF_WORKLOADS
        ]
        s6_cfgs = [
            _bound(s6_config(tag)) for tag in ("balanced", "write-heavy")
        ]
    finally:
        ec.lookup = saved_lookup
    current_backoff = {str(ident.campaign_id(cfg)) for cfg in backoff_cfgs}
    # T-671 で H が preimage から消え、current は T343 値になる。
    assert current_backoff == _T343_BACKOFF_CAMPAIGN_IDS
    assert current_backoff.isdisjoint(_T530_BACKOFF_CAMPAIGN_IDS)

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
    # 同じ理由で S6 current も T530 H 込み値ではなく T343 値になる。
    assert {str(ident.campaign_id(cfg)) for cfg in s6_cfgs} == \
        _T343_S6_CAMPAIGN_IDS
    assert {str(ident.campaign_id(cfg)) for cfg in s6_cfgs}.isdisjoint(
        _T530_S6_CAMPAIGN_IDS
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
    wal.log(lay, "v1", STAGE_BUILD_START, "linux-baremetal")
    wal.log(lay, "v1", STAGE_BUILD_DONE, "linux-baremetal", {"bin_hash": "abc"})
    wal.log(lay, "v1", STAGE_VERIFY_DONE, "linux-baremetal", {"verdict": "serializable"})
    wal.log(lay, "v1", STAGE_COMMIT, "linux-baremetal", {"tps": 900000})
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
    wal.log(
        lay, "contract-v", STAGE_COMMIT, _T530_CONTRACT.env_tag,
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
    wal.log(
        lay, "mismatched-v", STAGE_COMMIT, _T530_CONTRACT.env_tag, {
            "build_attempt_id": "mismatched-attempt",
            "build_admission_receipt_sha256": committed_sha,
            COMMIT_CONTRACT_SHA256_KEY: "0" * 64,
        },
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
    wal.log(legacy, "legacy-v", STAGE_COMMIT, "historical-env", {"fitness_tps": 1.0})
    assert wal.replay(legacy)["legacy-v"].committed

    from campaign import guided, replay

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
    wal.log(lay, "v", STAGE_COMMIT, _T530_CONTRACT.env_tag, {
        "build_attempt_id": "attempt-a",
        "build_admission_receipt_sha256": "1" * 64,
        COMMIT_CONTRACT_SHA256_KEY: _T530_CONTRACT_SHA256,
    })
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
    wal.log(lay, "v4", STAGE_COMMIT, "linux-baremetal")
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
    wal.log(lay, "v4", STAGE_COMMIT, "linux-baremetal")
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
        wal.log(rejected, "v", STAGE_COMMIT, "test", payload=[])
        assert False, "falsy list を empty object に正規化してはならない"
    except wal.WalPayloadTypeError as exc:
        assert exc.path == "payload"
    assert not os.path.exists(rejected.runs_dir)

    accepted = _layout()
    record = wal.log(accepted, "v", STAGE_COMMIT, "test", payload=None)
    assert record.payload == {}
    assert wal.read_records(accepted)[0].payload == {}


def test_wal_blank_line_is_rejected_but_collected_reader_keeps_valid_records():
    lay = _layout(); lay.ensure()
    wal.log(lay, "before", STAGE_COMMIT, "test")
    wal.log(lay, "after", STAGE_COMMIT, "test")
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
    wal.log(lay, "before", STAGE_COMMIT, "test")
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
        wal.log(lay, "before", STAGE_COMMIT, "test")
        with open(lay.wal_file, "ab") as stream:
            stream.write(tail)
        before = open(lay.wal_file, "rb").read()
        try:
            wal.log(lay, "after", STAGE_COMMIT, "test")
            assert False, "unframed tail への append を拒否すべき"
        except wal.WalAppendError as exc:
            assert exc.phase == "tail-gate"
            assert exc.wal_path == lay.wal_file
            assert exc.written_bytes == 0 < exc.total_bytes
            assert isinstance(exc.cause, wal.WalFramingError)
        assert open(lay.wal_file, "rb").read() == before


def test_wal_repair_tail_then_append_restores_independent_frames():
    lay = _layout(); lay.ensure()
    wal.log(lay, "before", STAGE_COMMIT, "test")
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
    wal.log(lay, "after", STAGE_COMMIT, "test")
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
    wal.log(framed, "v", STAGE_COMMIT, "test")
    size = os.path.getsize(framed.wal_file)
    result = wal.repair_truncated_tail(framed)
    assert result == wal.WalTailRepairResult(
        "noop", size, size, 0, None, "", None)


def test_wal_repair_receipt_is_durable_and_complete_before_truncate():
    lay = _layout(); lay.ensure()
    wal.log(lay, "before", STAGE_COMMIT, "test")
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
        wal.log(lay, "short", STAGE_COMMIT, "test", {"text": "あ"})
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
            wal.log(zero, "zero", STAGE_COMMIT, "test")
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
        wal.log(lay, "first", STAGE_COMMIT, "test")
        wal.log(lay, "second", STAGE_COMMIT, "test")
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
            wal.log(lay, "close-failure", STAGE_COMMIT, "test")
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
    wal.log(lay, "before", STAGE_COMMIT, "test")
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
            wal.log(lay, "v", STAGE_COMMIT, "test", payload)
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
    wal.log(lay, "v", STAGE_COMMIT, "test", payload)
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
    wal.log(append_layout, "before", STAGE_COMMIT, "test")
    held = os.open(append_layout.wal_file, os.O_RDWR)
    fcntl.flock(held, fcntl.LOCK_EX)
    append_started = threading.Event()
    append_done = threading.Event()
    append_errors = []

    def append_worker():
        append_started.set()
        try:
            wal.log(append_layout, "after", STAGE_COMMIT, "test")
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
    wal.log(repair_layout, "before", STAGE_COMMIT, "test")
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
    wal.log(lay, "v1", STAGE_COMMIT, "linux-baremetal", {"fitness_tps": 1})
    wal.log(lay, "v1", STAGE_COMMIT, "linux-baremetal", {"fitness_tps": 2})  # 再書き (最後勝ち)
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


def test_trigger_campaign_epoch_never_writes_pre_t428_paths():
    from campaign import loop as campaign_loop
    from campaign import p3_s4_loop_trigger_gating as trigger_driver

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
        build_context=context, campaign_namespace="exploration",
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


def test_p1_run_campaign_accepts_registered_contract():
    from campaign import loop as campaign_loop

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
        output_root=_tmpdir("izanagi_authorization_run_"),
        authorization_contract=_AUTHORIZATION,
        build_context=_BUILD_CONTEXT, log=lambda *_args: None,
    )
    assert summary.total == 0 and summary.results == []


def test_certified_writer_authorization_caller_inventory_is_closed():
    campaign_dir = Path(_ORCH) / "campaign"
    expected_run_calls = {
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
    assert sum(expected_run_calls.values()) == 15

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
    from campaign import certified_writer_admission as admission
    from campaign import certified_writer_preflight as helper

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
    from campaign import certified_writer_admission as admission
    from campaign import certified_writer_preflight as helper

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
                        integrity=Integrity(), n_txns=100, n_reads=300,
                        n_writes=100, n_keys=50, n_edges=120)


def _red_vr():
    """実 VerifyResult (赤): rw を含む 2-cycle (G2) anomaly を持つ non-serializable。"""
    edges = [CycleEdge(src=1, dst=2,
                       reasons=[EdgeReason(etype=RW, key="aa", u_ver=(1, 1), v_ver=(1, 2))]),
             CycleEdge(src=2, dst=1,
                       reasons=[EdgeReason(etype=RW, key="bb", u_ver=(1, 1), v_ver=(1, 2))])]
    a = Anomaly(cycle=[1, 2], phenomenon="G2", edges=edges)
    return VerifyResult(trace_dir="/tmp/ev", serializable=False, anomalies=[a],
                        integrity=Integrity(), n_txns=2, n_reads=2,
                        n_writes=2, n_keys=2, n_edges=2)


@contextlib.contextmanager
def _mock_pipeline(certified=True, median=12345.0, cv=0.01, rc=0, ncommit=100,
                   aborts=7, abort_rate=0.03, build_raises=False,
                   high_variance=False, unstable=False, competing=None,
                   trace_timeout=False, probe_raises=None,
                   bench_rounds=None, round_binding="unique",
                   trace_content=None, site_compilers=None, source_raises=False,
                   build_cached=False,
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
            self.lock_enters = 0
            self.competition_probes = 0

    class ScriptedPoint:
        """ScalePoint 同様、値等価だが identity は別にできる round fixture。"""
        def __init__(self, round_median, reps=2):
            self.throughputs = ([] if round_median is None else
                                [round_median] * reps)
            self.run_cmd = "<run>"
            self._median = round_median

        def leading_indicators(self):
            return {"throughput_tps": self._median,
                    "abort_rate": abort_rate, "latency_ns": 1000.0,
                    "llc_miss_rate": 0.2, "ipc": 1.5}

        def __eq__(self, other):
            return (isinstance(other, ScriptedPoint)
                    and self.throughputs == other.throughputs
                    and self.run_cmd == other.run_cmd)

    bench_calls = CallEvidence()
    real_verify_trace_dir = pipeline.verify_trace_dir
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
        if "rep_returncodes" in k:
            k["rep_returncodes"].extend(spec["rep_returncodes"])
        point = ScriptedPoint(spec["median"], reps=k.get("reps", 2))
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
                      dependency_prefix=""):
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
        return types.SimpleNamespace(
            bin_hash=bin_sha256[:16], bin_sha256=bin_sha256,
            binary="/nonexistent/ycsb.exe", cached=build_cached,
            configure_cmd="<cfg-v2>", build_cmd="<build-v2>",
            contract_sha256=contract.contract_sha256,
        )

    patch("buildcache", types.SimpleNamespace(
        build=fake_build, build_v2=fake_build_v2,
        is_full_sha256=buildcache.is_full_sha256,
        _ccbench_dir=buildcache._ccbench_dir,
        DEFAULT_CC=buildcache.DEFAULT_CC, DEFAULT_CXX=buildcache.DEFAULT_CXX,
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
            source_root=ccbench_dir or "/tmp/izanagi-test-ccbench",
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
            if trace_content is not None:
                with open(os.path.join(trace_dir, "trace_0.log"),
                          "w", encoding="ascii") as stream:
                    stream.write(trace_content)
            return ncommit, rc, aborts
        patch("_run_trace", fake_trace)
    # 実 VerifyResult を返す (result_to_dict が S4 で abort payload を作るので duck-type 不可)。
    if trace_content is None:
        patch("verify_trace_dir", lambda tdir: _green_vr() if certified else _red_vr())
    else:
        patch("verify_trace_dir", real_verify_trace_dir)
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
          record_rep_returncodes=False, **mock_kw):
    """1 genome を mock 下で評価し (EvalResult, bench 呼び出し回数 list) を返す。"""
    if screening is not None and wal.read_lock(lay) is None:
        cfg = _cfg(search_config={**_cfg().search_config,
                                  **ident.screening_search_config(screening)})
        _write_certified_lock(lay, _bound(cfg))
    with _mock_pipeline(**mock_kw) as calls:
        r = pipeline.evaluate(
            Genome("silo", {"BACK_OFF": 1}), lay, _AUTH_CONTRACT.env_tag, "deadbeef",
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


def test_trigger_build_start_binding_uses_same_source_evidence_as_both_cache_builds():
    lay = _tmp_layout()
    from campaign import axis_trigger_gating

    source_root = _tmpdir("izanagi_trigger_materialized_")
    source_path = os.path.join(source_root, axis_trigger_gating.SOURCE_REL)
    os.makedirs(os.path.dirname(source_path), exist_ok=True)
    predicate = emit_predicate(TriggerGateIR(20))
    with open(source_path, "w", encoding="utf-8") as stream:
        stream.write(
            f"// EVOLVE-BLOCK-BEGIN {axis_trigger_gating.MARKER_ID}\n"
            "#if BACKOFF_TRIGGER_GATING\n"
            f"{predicate}\n"
            "#else\ntrue;\n#endif\n"
            f"// EVOLVE-BLOCK-END {axis_trigger_gating.MARKER_ID}\n"
        )
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
    from campaign import axis_trigger_gating

    source_root = _tmpdir("izanagi_trigger_cross_binding_")
    source_path = os.path.join(source_root, axis_trigger_gating.SOURCE_REL)
    os.makedirs(os.path.dirname(source_path), exist_ok=True)
    predicate_a = emit_predicate(TriggerGateIR(20))
    with open(source_path, "w", encoding="utf-8") as stream:
        stream.write(
            f"// EVOLVE-BLOCK-BEGIN {axis_trigger_gating.MARKER_ID}\n"
            "#if BACKOFF_TRIGGER_GATING\n"
            f"{predicate_a}\n"
            "#else\ntrue;\n#endif\n"
            f"// EVOLVE-BLOCK-END {axis_trigger_gating.MARKER_ID}\n"
        )
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
    from campaign import loop as L
    from campaign import screening_driver as SD

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
                build_context=bad, log=lambda *_args: None,
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
    from campaign import p3_s4_loop_sort as sort_preview
    from campaign import p3_s4_loop_trigger_gating as trigger_preview

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


def test_pipeline_v2_passes_nondefault_prepared_ccbench_tree_to_both_builds():
    lay = _tmp_layout()
    contract = ec.lookup("linux-baremetal")
    prepared_tree = "/approved/prepared-cell-tree"
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
        "C 0 0 5 10\n"
        "W 0 aa U 5 10\n"
        "I 0 aa write-set-entry-without-intent\n"
    )
    i_rows = [line for line in trace_content.splitlines() if line.startswith("I ")]
    assert i_rows == ["I 0 aa write-set-entry-without-intent"]  # DW-M03: 単一理由

    lay = _tmp_layout()
    r, calls = _eval(lay, trace_content=trace_content)

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


def test_run_trace_parses_abort_from_stdout():
    """回帰 (結線検査): 実 _run_trace が ccbench stdout を _parse_abort_counts に通して
    第 3 返り値で返す。_parse_abort_counts 単体と pipeline 層 (_run_trace ごとモック) の
    テストだけでは、この結線を消しても (旧配線 = stdout を捨てる) 全緑のまま
    (2026-07-03 敵対検証 medium: テスト正直さ)。"""
    sdir = _tmpdir("izanagi_runtrace_bin_")
    fake = os.path.join(sdir, "fake_ccbench.sh")
    with open(fake, "w", encoding="utf-8") as f:
        f.write("#!/bin/sh\nprintf 'abort_counts_:\\t42\\n'\n")
    os.chmod(fake, 0o755)
    n, rc, aborts = pipeline._run_trace(fake, _tmpdir("izanagi_runtrace_t1_"),
                                        {"w": "1"}, 1800)
    assert (n, rc, aborts) == (0, 0, 42)
    fake2 = os.path.join(sdir, "fake_noabort.sh")
    with open(fake2, "w", encoding="utf-8") as f:
        f.write("#!/bin/sh\nprintf 'commit_counts_:\\t9\\n'\n")
    os.chmod(fake2, 0o755)
    _, _, aborts = pipeline._run_trace(fake2, _tmpdir("izanagi_runtrace_t2_"), {}, 1800)
    assert aborts is None                    # 集計行なし → None (呼び手が fails-closed)


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
    r, calls = _eval(
        lay,
        screening=_screening(baseline_measured_at=now - 31 * 60),
        median=8000.0,
    )
    assert r.certified and not r.aborted
    assert calls.events == ["verify", "bench"]
    assert any("stale-baseline" in note and "1860" in note for note in r.notes)
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
    """設計 §5-5(i): evaluate 内に verify なし COMMIT の構文位置を作れないことを固定。"""
    with open(pipeline.__file__, encoding="utf-8") as f:
        tree = ast.parse(f.read(), filename=pipeline.__file__)
    evaluate_node = next(
        n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == "evaluate")

    parents = {}
    for parent in ast.walk(evaluate_node):
        for child in ast.iter_child_nodes(parent):
            parents[child] = parent

    verify_loop = next(
        n for n in ast.walk(evaluate_node)
        if isinstance(n, ast.For)
        and isinstance(n.iter, ast.Name) and n.iter.id == "passes")
    certified_assignment = next(
        n for n in ast.walk(evaluate_node)
        if isinstance(n, ast.Assign)
        and any(isinstance(t, ast.Attribute)
                and isinstance(t.value, ast.Name) and t.value.id == "res"
                and t.attr == "certified" for t in n.targets)
        and isinstance(n.value, ast.Constant) and n.value.value is True)
    assert verify_loop.end_lineno < certified_assignment.lineno

    commit_calls = []
    for node in ast.walk(evaluate_node):
        if not isinstance(node, ast.Call) or len(node.args) < 3:
            continue
        if not (isinstance(node.func, ast.Attribute)
                and isinstance(node.func.value, ast.Name)
                and node.func.value.id == "wal" and node.func.attr == "log"):
            continue
        stage = node.args[2]
        if isinstance(stage, ast.Name) and stage.id == "STAGE_COMMIT":
            commit_calls.append(node)

    assert len(commit_calls) == 2
    for call in commit_calls:
        assert call.lineno > certified_assignment.lineno
        cur = parents.get(call)
        inside_certified_if = False
        while cur is not None and cur is not evaluate_node:
            if (isinstance(cur, ast.If)
                    and isinstance(cur.test, ast.Attribute)
                    and isinstance(cur.test.value, ast.Name)
                    and cur.test.value.id == "res"
                    and cur.test.attr == "certified"):
                inside_certified_if = True
                break
            cur = parents.get(cur)
        assert inside_certified_if

    # mutation resistance: verify loop より前へ
    # `if False: wal.log(..., STAGE_COMMIT, ...)` を挿すと call 数・行順・認証 if の
    # いずれも満たせず、このテストが落ちることを意図した形状検査である。


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
    wal.log(lay, "already-committed", STAGE_COMMIT, _T530_CONTRACT.env_tag, {
        "fitness_tps": 1.0,
        COMMIT_CONTRACT_SHA256_KEY: _T530_CONTRACT_SHA256,
    })
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
      bench_lock_enters = bench_lock() で入った回数 (verify pass 分 + bench 分)
    """
    saved = {}

    def patch(name, val):
        saved[name] = getattr(pipeline, name)
        setattr(pipeline, name, val)

    calls = {"trace": [], "bench_lock_enters": 0}

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
        return ncommit, rc, aborts

    idx_verify = {"i": 0}

    def fake_verify(tdir):
        i = idx_verify["i"]
        idx_verify["i"] += 1
        _, _, _, certified = pass_results[i]
        return _green_vr() if certified else _red_vr()

    def fake_build(genome, commit, trace, src_token=None, ccbench_dir="", cache_root="",
                   *, admission, build_context, source_evidence):
        assert build_context is _BUILD_CONTEXT
        assert admission.as_wal_receipt()["source"] == source_evidence.as_receipt()
        bin_sha256 = ("da" if trace else "db") * 32  # 64 hex (WAL 新キー用)
        return types.SimpleNamespace(bin_hash=bin_sha256[:16], bin_sha256=bin_sha256,
                                     binary="/nonexistent/ycsb.exe", cached=False,
                                     configure_cmd="<cfg>", build_cmd="<build>")

    def fake_measure(*a, **k):
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
            source_root=kwargs.get("ccbench_dir") or "/tmp/izanagi-test-ccbench",
        )))
    patch("_run_trace", fake_run_trace)
    patch("verify_trace_dir", fake_verify)
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
    assert calls["trace"][1]["numactl"] == numa            # S2 パス: numactl あり
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


def test_pipeline_extra_correctness_requires_numactl():
    """D36 決定4-4: use_numactl=True を含む extra_correctness (S2 相当) は numactl
    必須。無指定を黙って劣化させず fails-closed で ValueError にする
    (敵対レビュー 2026-07-09 CONFIRMED: numactl 無しで S2 が静かに較正条件から
    乖離しうる欠落の修正)。build/verify に一切触れる前に即エラーになる。"""
    lay = _tmp_layout()
    try:
        pipeline.evaluate(
            Genome("silo", {"BACK_OFF": 1}), lay,
            _AUTH_CONTRACT.env_tag, "deadbeef",
            PerfConfig(records=1000, threads=2), clocks_per_us=1800,
            authorization_contract=_AUTHORIZATION,
            extra_correctness=[(pipeline.S2_TAG, pipeline.s2_correctness_workload())],
            do_bench=False, log=lambda *a: None, build_context=_BUILD_CONTEXT)
        assert False, "should raise ValueError"
    except ValueError:
        pass


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
    from calibrator.runner import CompetingBenchProbeError
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
    from calibrator.runner import CompetingBenchProbeError
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
    from campaign import loop as L
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
                               log=lambda *a: None, build_context=_BUILD_CONTEXT)
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
    from campaign import screening_driver as SD
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


def test_loop_enables_s2_extra_correctness_via_search_config():
    """D36 決定4-1: search_config[SEARCH_CONFIG_VERIFY_KEY]=='legacy+s2' で
    run_campaign が evaluate() に S2 extra_correctness を渡す (opt-in の配線点)。"""
    from campaign import loop as L

    captured = {}

    def fake_eval(g, layout, env_tag, ccbench_commit, perf, clocks_per_us,
                  numactl=None, correctness=None, extra_correctness=None,
                  do_bench=True, do_settle=True, src_token=None, log=print,
                  ccbench_dir="", cache_root="", *, authorization_contract,
                  build_context,
                  capability_resolver=None, source_evidence=None):
        assert build_context is _BUILD_CONTEXT
        captured["extra_correctness"] = extra_correctness
        v = pipeline.variant_id(g, src_token or "stock")
        wal.log(layout, v, STAGE_BUILD_START, env_tag, {"genome": g.canonical()})
        wal.log(layout, v, STAGE_COMMIT, env_tag, {
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
                       output_root=out_root, log=lambda *a: None, build_context=_BUILD_CONTEXT)
    finally:
        L.evaluate, L.source_digest = saved_eval, saved_sd
    assert captured["extra_correctness"] is not None
    assert [tag for tag, _ in captured["extra_correctness"]] == [pipeline.S2_TAG]


def test_loop_omits_extra_correctness_without_verify_search_config():
    """回帰確認: search_config に verify キーが無い既存 campaign は extra_correctness
    が None のまま (S2 は opt-in、既存 campaign の挙動を変えない)。"""
    from campaign import loop as L

    captured = {}

    def fake_eval(g, layout, env_tag, ccbench_commit, perf, clocks_per_us,
                  numactl=None, correctness=None, extra_correctness=None,
                  do_bench=True, do_settle=True, src_token=None, log=print,
                  ccbench_dir="", cache_root="", *, authorization_contract,
                  build_context,
                  capability_resolver=None, source_evidence=None):
        assert build_context is _BUILD_CONTEXT
        captured["extra_correctness"] = extra_correctness
        v = pipeline.variant_id(g, src_token or "stock")
        wal.log(layout, v, STAGE_BUILD_START, env_tag, {"genome": g.canonical()})
        wal.log(layout, v, STAGE_COMMIT, env_tag, {
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
                       output_root=out_root, log=lambda *a: None, build_context=_BUILD_CONTEXT)
    finally:
        L.evaluate, L.source_digest = saved_eval, saved_sd
    assert captured["extra_correctness"] is None


def test_m12_loop_compute_uses_gxx_and_forwards_only_contract_and_prefix():
    from campaign import loop as L

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
    L._authorize_measurement = lambda *args, **kwargs: (
        contract, {"fixture": "receipt"},
    )
    try:
        summary = L.run_campaign(
            cfg, [Genome("silo", {"BACK_OFF": 1})],
            PerfConfig(records=1, threads=1), "pegasus", 2100,
            do_bench=False, output_root=out_root, log=lambda *a: None,
            env_contract=contract, dependency_prefix=prefix,
            numactl=contract.numactl,
            authorization_contract=ec.authorize(contract.env_tag),
            build_context=_BUILD_CONTEXT,
        )
    finally:
        L.evaluate, L.source_digest = saved_eval, saved_sd
        L._compilers_for_current_site = saved_compilers
        L._authorize_measurement = saved_authorize

    assert captured["resolve"][0][0][-1] == "g++"
    assert captured["evaluate"][0]["env_contract"] == contract
    assert captured["evaluate"][0]["dependency_prefix"] == prefix
    assert "site" not in inspect.signature(L.run_campaign).parameters
    expected_cfg = ident.bind_environment_contract(
        ident.bind_admission_policy(cfg, _BUILD_CONTEXT.policy), contract,
    )
    assert summary.campaign_id == str(ident.campaign_id(expected_cfg))
    assert summary.execution_receipt == {"fixture": "receipt"}


def test_required_contract_is_attested_once_at_run_campaign_sink():
    from campaign import loop as L

    contract = ec.lookup("pegasus")
    receipt = {"schema": "fixture-required-receipt"}
    verified = object()
    order = []
    saved = {
        "load": L.env_attestation.load_verified_calibration,
        "attest": L.execution_guard.attest_and_build_receipt,
        "matches": L.execution_guard.receipt_matches_contract,
        "evaluate": L.evaluate,
        "source_digest": L.source_digest,
    }
    L.env_attestation.load_verified_calibration = (
        lambda loaded, root: order.append("load") or verified
    )
    L.execution_guard.attest_and_build_receipt = (
        lambda loaded, calibration: order.append("attest") or receipt
    )
    L.execution_guard.receipt_matches_contract = (
        lambda loaded, **kwargs: order.append("matches") or True
    )

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
    out_root = _tmpdir("izanagi_loop_attestation_once_")
    try:
        summary = L.run_campaign(
            cfg,
            [Genome("silo", {"BACK_OFF": 0}), Genome("silo", {"BACK_OFF": 1})],
            PerfConfig(records=1, threads=1), contract.env_tag,
            contract.clocks_per_us, numactl=contract.numactl,
            do_bench=False, output_root=out_root, log=lambda *a: None,
            env_contract=contract, authorization_contract=ec.authorize(contract.env_tag),
            build_context=_BUILD_CONTEXT,
        )
    finally:
        L.env_attestation.load_verified_calibration = saved["load"]
        L.execution_guard.attest_and_build_receipt = saved["attest"]
        L.execution_guard.receipt_matches_contract = saved["matches"]
        L.evaluate = saved["evaluate"]
        L.source_digest = saved["source_digest"]
    assert order == ["load", "attest", "matches", "evaluate", "evaluate"]
    assert summary.execution_receipt is receipt


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
                source_root=ccbench_dir or "/tmp/izanagi-test-ccbench",
            )
    return types.SimpleNamespace(STOCK="stock", resolve_evidence=_resolve)


def _loop_with_fake_eval(fake_eval, genomes, spec_content, do_bench=False,
                         src_token="stock"):
    """run_campaign を fake evaluate 下で回し (summary, layout) を返す。

    loop は src_token id で skip/abort キーを揃える (D24)。identity 核 (source_digest) は実
    g++/git 依存ゆえ mock し、src_token を制御する (Exception なら identity-error 経路)。"""
    from campaign import loop as L
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
                           build_context=_BUILD_CONTEXT)
    finally:
        L.evaluate, L.source_digest = saved, saved_sd
    bound_cfg = _bound(cfg)
    lay = campaign_layout(str(ident.campaign_id(bound_cfg)), out_root)
    return s, lay


def test_run_campaign_default_namespace_remains_official():
    """selector 省略時は既存どおり official root を使う。"""
    from campaign import loop as L

    out_root = _tmpdir("izanagi_loop_namespace_default_")
    cfg = CampaignConfig(spec_slug="t", search_tag="enum",
                         spec_content="namespace-default", ccbench_commit="deadbeef")
    summary = L.run_campaign(
        cfg, [], PerfConfig(records=1, threads=1),
        _AUTH_CONTRACT.env_tag, _AUTH_CONTRACT.clocks_per_us,
        numactl=list(_AUTH_CONTRACT.numactl),
        authorization_contract=_AUTHORIZATION,
        do_bench=False, output_root=out_root, log=lambda *_args: None, build_context=_BUILD_CONTEXT,
    )
    expected = campaign_layout(str(ident.campaign_id(_bound(cfg))), out_root)
    assert summary.layout_root == expected.root
    assert os.path.isdir(expected.root)
    assert not os.path.exists(os.path.join(out_root, "exploration"))


def test_run_campaign_exploration_namespace_reaches_lock_wal_and_pipeline():
    """exploration selector が marker/lock/WAL/evaluate の同一 layout まで届く。"""
    from campaign import loop as L

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
        wal.log(layout, variant, STAGE_COMMIT, env_tag, {
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
            campaign_namespace="exploration",
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


def test_run_campaign_rejects_unknown_namespace_before_output_creation():
    """未知 namespace は official fallback せず directory 作成前に拒否する。"""
    from campaign import loop as L

    parent = _tmpdir("izanagi_loop_namespace_unknown_")
    out_root = os.path.join(parent, "must-not-exist")
    cfg = CampaignConfig(spec_slug="t", search_tag="enum",
                         spec_content="namespace-unknown", ccbench_commit="deadbeef")
    try:
        L.run_campaign(
            cfg, [], PerfConfig(records=1, threads=1), "test-env", 1800,
            authorization_contract=_AUTHORIZATION,
            do_bench=False, output_root=out_root, log=lambda *_args: None, build_context=_BUILD_CONTEXT,
            campaign_namespace="typo",
        )
        assert False, "未知 namespace を拒否すべき"
    except ValueError as exc:
        assert "namespace" in str(exc)
    assert not os.path.exists(out_root)


def test_run_campaign_namespace_does_not_change_campaign_id():
    """namespace は runtime path selector であり identity preimage へ入らない。"""
    from campaign import loop as L

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
        output_root=out_root, log=lambda *_args: None, build_context=_BUILD_CONTEXT,
    )
    exploration = L.run_campaign(
        *common, numactl=list(_AUTH_CONTRACT.numactl),
        authorization_contract=_AUTHORIZATION, do_bench=False,
        output_root=out_root, log=lambda *_args: None, build_context=_BUILD_CONTEXT,
        campaign_namespace="exploration",
    )
    assert official.campaign_id == exploration.campaign_id == str(ident.campaign_id(_bound(cfg)))


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
    from campaign import loop as L
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
            build_context=_BUILD_CONTEXT)
    finally:
        L.evaluate, L.source_digest = saved, saved_sd
    assert len(calls) == 0 and s.skipped == 1            # src_token id terminal → 再評価しない
    # リカバリ skip = 重複提案の実体。呼び手 (_resolve_duplicate) はこの確定済み id だけを
    # 使う — revert 後 tree の再 resolve は stock id = 別 variant を引く ([T-157])
    assert s.skipped_variants == [src_id]


def test_replay_accepts_matching_contract_bound_commit_and_skips_evaluation():
    """lock=H_A/全COMMIT=H_A は terminal skip し evaluate/build を呼ばない。"""
    from campaign import loop as L

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
        )
    finally:
        L.evaluate = saved_eval
        L.buildcache.build = saved_build
        L.source_digest = saved_source_digest
    assert calls == {"evaluate": 0, "build": 0}
    assert summary.skipped == 1 and summary.evaluated == 0


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


def test_loop_identity_error_is_retryable_after_repair():
    """identity-error abort (transient) は permanent skip でなく環境修復後に再評価される (D25)。
    旧挙動は stock id terminal abort → 永久 skip で stock baseline を silently drop していた。"""
    from campaign import loop as L
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
            build_context=_BUILD_CONTEXT)
        assert s1.aborted == 1 and len(calls) == 0
        # run2: 環境修復 (resolve 成功 → stock) → 永久 skip でなく再評価・commit
        L.source_digest = _sd_mock("stock")
        s2 = L.run_campaign(
            cfg, [g], PerfConfig(records=1, threads=1),
            _AUTH_CONTRACT.env_tag, _AUTH_CONTRACT.clocks_per_us,
            numactl=list(_AUTH_CONTRACT.numactl),
            authorization_contract=_AUTHORIZATION,
            do_bench=False, output_root=out_root, log=lambda *a: None,
            build_context=_BUILD_CONTEXT)
    finally:
        L.evaluate, L.source_digest = saved, saved_sd
    assert len(calls) == 1 and s2.committed == 1 and s2.skipped == 0   # 修復後に再評価


def test_loop_identity_error_retryable_survives_inflight_crash():
    """identity-error abort → 修復後の再評価が in-flight クラッシュ (BUILD_START のみで
    途切れ) しても、次 run で再評価される (D25 の保証がクラッシュ 1 回で破れない)。

    旧実装は retryable 判定が st.last (最終レコード) 依存だったため、BUILD_START が
    最後になると判定から漏れ、aborted の粘着により permanent skip が復活していた
    (洗練検査 2026-07-02 HIGH)。overnight クラッシュ→再起動は WAL の設計前提。"""
    from campaign import loop as L
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
                            log=lambda *a: None, build_context=_BUILD_CONTEXT)
    finally:
        L.evaluate, L.source_digest = saved, saved_sd
    assert len(calls) == 1 and s3.committed == 1 and s3.skipped == 0


def test_loop_resume_recovery_aborts_real_pipeline_crash_after_start():
    """実 evaluate/WAL writer の start→process death→resume 境界を通す。"""
    from campaign import artifact_admission
    from campaign import loop as L

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
                build_context=_BUILD_CONTEXT,
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
    assert artifact_admission.require_admitted_campaign(lay).decision.admitted


def test_loop_identity_skip_is_visible_when_stock_id_terminal():
    """identity 確定不能かつ stock id が terminal 済みのときの skip は identity_skipped
    として summary に分離カウントされる (規律3: 成果物からの欠落を沈黙させない)。"""
    from campaign import loop as L
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
                           log=lambda *a: None, build_context=_BUILD_CONTEXT)
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
        official = campaign_layout("official-isolated")
        assert official.root == os.path.join(
            saved_repo_output_root(), "campaigns", "official-isolated",
        )

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
        sys.path.insert(0, os.path.dirname(_ORCH))
        alternate = importlib.import_module("orchestrator.campaign.layout")
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

    from campaign import p3_autonomous_workload_trial as autonomous

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
    from calibrator.stability import Comparison
    from campaign.p2_2_report import _verdict_str
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


def _require_g13():
    """source_digest の preprocess は g++-13 を直接叩く (D23)。PATH に無い環境では skip
    (README の『C++ toolchain が無い環境では skip として数える』契約)。toolchain のある
    環境では従来どおり実 preprocess を走らせるので検査は弱まらない。"""
    if shutil.which("g++-13") is None:
        skip("C++ toolchain 不在 (g++-13 が PATH に無い) — source_digest preprocess は実 g++-13 が要る")


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
    assert current == _T343_GOLDEN_CK0[g0.canonical()]
    assert current != _PRE_T343_GOLDEN_CK0[g0.canonical()]


def test_source_digest_parse_options_defaults():
    """Options パース: 既定値・クォート剥がし・空値 unset (D23 finding 対策)。"""
    opts = _require_ccbench_file("cmake/Options.cmake")
    with open(opts, encoding="utf-8") as f:
        d = source_digest.parse_options_defaults(f.read())
    if "BACKOFF_FIXED" not in d:
        skip("template patch 未適用 (Options.cmake に BACKOFF_FIXED 既定なし) — 適用後のみ")
    assert d["BACKOFF_FIXED"] == "-1" and d["BACK_OFF"] == "1"
    assert "INSERT_READ_DELAY_MS" not in d        # 空値 ("") は除外


def test_source_digest_stock_roundtrip():
    """実 working-tree (inert) で silo 8 genome は src_token='stock' = 旧 id 不変 (後方互換)。"""
    head = _ccbench_head_or_skip()
    if head is None:
        skip("submodule 未 init — src_token roundtrip は実 working-tree が要る")
    if not shutil.which("g++-13"):
        skip("g++-13 不在 — preprocess 実測は計測ホスト (linux-baremetal) 限定")
    for g in genome.SILO_SPACE.enumerate():
        st = source_digest.src_token(g, head)
        assert st == source_digest.STOCK, g.canonical()
        assert pipeline.variant_id(g, st) == pipeline.variant_id(g)


def test_source_digest_fixed_variant_distinct():
    """BACKOFF_FIXED 枝は stock と別 id・値違いも別 id (alias 防止)。-1 は #else=stock。"""
    head = _ccbench_head_or_skip()
    if head is None:
        skip("submodule 未 init — BACKOFF_FIXED digest 分離は実 working-tree が要る")
    wt = source_digest._read(os.path.join(buildcache._ccbench_dir(), "include/backoff.hh"))
    if "#if BACKOFF_FIXED" not in wt:
        # clean stock checkout (template patch 未適用) では BACKOFF_FIXED が参照されず
        # digest が分離しない (assert が偽 fail する)。適用済み working-tree 前提を明示。
        skip("template patch 未適用 (backoff.hh に #if BACKOFF_FIXED 無し) — digest 分離は適用後のみ")
    base = {"BACK_OFF": 1, "NO_WAIT_LOCKING_IN_VALIDATION": 1,
            "NO_WAIT_OF_TICTOC": 0, "WAL": 0}
    g50 = Genome("silo", {**base, "BACKOFF_FIXED": 50})
    g10 = Genome("silo", {**base, "BACKOFF_FIXED": 10})
    gm1 = Genome("silo", {**base, "BACKOFF_FIXED": -1})
    t50, t10, tm1 = (source_digest.src_token(x, head) for x in (g50, g10, gm1))
    assert tm1 == source_digest.STOCK             # -1 は #else = stock 枝に正規化
    assert t50 != source_digest.STOCK and t10 != source_digest.STOCK and t50 != t10
    assert pipeline.variant_id(g50, t50) != pipeline.variant_id(g50)
    assert (buildcache.cache_key(
        g50, head, False, t50,
        admission=_admission_for(g50, head, src_token=t50),
    ) != buildcache.cache_key(
        g50, head, False,
        admission=_admission_for(g50, head),
    ))


def test_source_digest_failsclosed_on_missing_define():
    """#if 参照マクロの供給漏れは fails-closed (規律6/2)。

    template patch 適用後の骨格は #ifndef+#error (全経路停止)、-Werror=undef は
    それ以外の未定義マクロ評価への防壁として残る。どちらも RuntimeError に落ちる。"""
    hh = _require_ccbench_file("include/backoff.hh")
    with open(hh, encoding="utf-8") as f:
        src = f.read()
    if "BACKOFF_FIXED" not in src:
        skip("template patch 未適用 (backoff.hh に BACKOFF_FIXED 骨格なし) — 適用後のみ")
    _require_g13()  # 供給漏れ停止と preprocess 起動不能を取り違えないため g++-13 不在は skip
    try:
        source_digest._cpp_normalize(src, {"BACKOFF_NOINLINE": "0"}, "g++-13")  # FIXED 欠落
        assert False, "供給漏れで停止すべき (#error / -Werror=undef)"
    except RuntimeError:
        pass


def test_source_digest_semantic_comment_vs_behavior():
    """コメントのみ変更は同 digest (cpp -P 除去)、挙動変更 (memory_order) は別 digest。"""
    opts = _require_ccbench_file("cmake/Options.cmake")
    hh = _require_ccbench_file("include/backoff.hh")
    _require_g13()
    with open(opts, encoding="utf-8") as f:
        defines = source_digest._merge_defines(
            source_digest.parse_options_defaults(f.read()), {})
    with open(hh, encoding="utf-8") as f:
        src = f.read()
    base = source_digest._cpp_normalize(src, defines, "g++-13")
    commented = source_digest._cpp_normalize(src + "\n// trailing comment\n", defines, "g++-13")
    behaved = source_digest._cpp_normalize(
        src.replace("memory_order_acquire", "memory_order_relaxed"), defines, "g++-13")
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
        "include/backoff.hh", "cc/silo/transaction.cc"), \
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
    from campaign import axis_trigger_gating, p3_s4_loop, p3_s4_loop_sort
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
    from campaign import source_digest
    from campaign.layout import repo_output_root
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
# (git + Options.cmake + backoff.hh) を作る。EVOLVE_BLOCK_SOURCES と同じ相対パスを使う。

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


# 実 CMake の構造 (cmake/Options.cmake の供給表 + cc/<protocol>/CMakeLists.txt の OPTIONS) を
# 模した fixture。source_digest は「cmake CACHE 変数の全体」でなく「実 TU へ -D される部分集合」
# だけを defines にする (T-148 fix round) ため、供給表が無い fixture は fails-closed で止まる。
# DEBUG_MSG は「CACHE には居るが silo TU には供給されない」実 Options.cmake の DEBUG_MSG (oze 用)
# と同じ役回りで、乖離マクロの回帰検査に使う。
_FAKE_OPTIONS_CMAKE = (
    'set(CCBENCH_BACK_OFF 1 CACHE STRING "exponential backoff")\n'
    'set(CCBENCH_DEBUG_MSG 0 CACHE STRING "oze only — not supplied to silo TUs")\n'
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


def _fake_ccbench_repo():
    """(sub, head, git) — git は fake repo で任意コマンドを回すヘルパー。"""
    sub = _tmpdir("izanagi_fakecc_")
    os.makedirs(os.path.join(sub, "cmake"))
    os.makedirs(os.path.join(sub, "include"))
    os.makedirs(os.path.join(sub, "cc", "silo"))
    with open(os.path.join(sub, "cmake", "Options.cmake"), "w", encoding="utf-8") as f:
        f.write(_FAKE_OPTIONS_CMAKE)
    with open(os.path.join(sub, "cc", "silo", "CMakeLists.txt"), "w", encoding="utf-8") as f:
        f.write(_FAKE_SILO_CMAKE)
    with open(os.path.join(sub, "include", "backoff.hh"), "w", encoding="utf-8") as f:
        f.write(_FAKE_BACKOFF_HH)
    with open(os.path.join(sub, "cc", "silo", "transaction.cc"), "w", encoding="utf-8") as f:
        f.write(_FAKE_TRANSACTION_CC)

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


def test_source_digest_builtin_ifdef_not_aliased_to_stock():
    """critical (2026-07-04 敵対検証 / D34 案A): builtin definedness (`#ifdef __x86_64__` /
    __GNUC__ 等) で digest 環境と実ビルドが乖離する偽 cache hit を封鎖する。

    旧設計 (-undef) は builtin を全消しするため、EVOLVE-BLOCK に `#ifdef __x86_64__ / 別挙動 /
    #else / stock / #endif` と書くと digest 環境では #else(stock枝) に落ち preprocess 出力が
    baseline と byte 一致 → src_token='stock' に化け、別挙動の variant が stock の certified 結果を
    verify 素通りで継承する (規律2 直撃)。案A (-undef 廃止) で builtin を実ビルドと揃えれば、
    #ifdef が digest に正直に反映され STOCK に化けない = 別 cache_key で cache-miss ビルドされる。"""
    _require_g13()
    g = Genome("silo", {"BACK_OFF": 1})
    sub, head, _git = _fake_ccbench_repo()
    hh = os.path.join(sub, "include", "backoff.hh")
    assert source_digest.resolve(g, head, sub) == source_digest.STOCK   # clean は STOCK
    # payload (return 1) に builtin definedness の別枝を注入。g++ では __GNUC__ が常に定義される
    # ので実ビルドは 999 枝、旧 -undef digest は #else で 1 (= stock と alias) になっていた。
    with open(hh, "w", encoding="utf-8") as f:
        f.write(_FAKE_BACKOFF_HH.replace(
            "    return 1;\n",
            "#ifdef __GNUC__\n    return 999;\n#else\n    return 1;\n#endif\n"))
    tok = source_digest.resolve(g, head, sub)
    assert tok != source_digest.STOCK, \
        "builtin definedness (#ifdef __GNUC__) が STOCK に化けた — 案A (-undef 廃止) の回帰"
    assert source_digest.compute(g, sub) != source_digest.baseline(g, head, sub), \
        "別挙動 payload の digest が baseline と一致 (偽 cache hit)"


def test_source_digest_include_change_rejected_by_resolve():
    """phase3.md blocking (#include 死角, 最小案): #include の追加/差し替えは preprocess 前に
    除去され digest に現れない (identity 不変の死角) → resolve が HEAD 行集合との不一致で
    fails-closed abort する。恒久案 (行を identity に織り込んで許す) は include 先の中身が
    identity 外に dangling し中身違いの新規 header で variant 間 alias が残るため却下
    (2026-07-03 敵対検証 high)。行集合を HEAD 固定にすれば include 追加自体を止め穴ごと消える。"""
    _require_g13()
    g = Genome("silo", {"BACK_OFF": 1})
    sub, head, _git = _fake_ccbench_repo()
    assert source_digest.resolve(g, head, sub) == source_digest.STOCK    # clean = stock 通過
    hh = os.path.join(sub, "include", "backoff.hh")
    # (a) #include の追加 → resolve が abort (行集合が HEAD と不一致)
    with open(hh, "w", encoding="utf-8") as f:
        f.write('#include "evil_extra.hh"\n' + _FAKE_BACKOFF_HH)
    try:
        source_digest.resolve(g, head, sub)
        assert False, "#include 追加で resolve が abort すべき"
    except RuntimeError as e:
        assert "#include" in str(e)
    # (b) 既存 #include の差し替え → resolve abort (中身違い header の alias を identity 核で遮断)
    with open(hh, "w", encoding="utf-8") as f:
        f.write(_FAKE_BACKOFF_HH.replace('#include "tsc.hh"', '#include "hacked.hh"'))
    try:
        source_digest.resolve(g, head, sub)
        assert False, "#include 差し替えで resolve が abort すべき"
    except RuntimeError:
        pass
    # (c) 復元で resolve が通過に戻る (誤検出でない)
    with open(hh, "w", encoding="utf-8") as f:
        f.write(_FAKE_BACKOFF_HH)
    assert source_digest.resolve(g, head, sub) == source_digest.STOCK
    # assert_includes_match_head 単体でも同じ判定 (resolve が駆動する一次防壁)
    with open(hh, "w", encoding="utf-8") as f:
        f.write('#include "evil_extra.hh"\n' + _FAKE_BACKOFF_HH)
    try:
        source_digest.assert_includes_match_head(g, head, sub)
        assert False, "assert_includes_match_head 単体でも abort すべき"
    except RuntimeError:
        pass


def _any_cxx():
    """実在する g++ を返す (skip は全滅時のみ)。T-148 系テストは digest の等値/非等値と
    受理/拒否の**関係**だけを見る — 関係は g++ 版に依存しない (digest 値自体は環境依存で
    pin しない仕様、D34)。中核 positive control が g++-13 不在の環境で skip されると
    偽緑になる ([T-137] の教訓) ため fallback で実 preprocess を必ず走らせる。"""
    for c in ("g++-13", "g++-12", "g++"):
        if shutil.which(c):
            return c
    skip("C++ toolchain 全滅 (g++-13/g++-12/g++ いずれも PATH に無い)")


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
        source_digest._worktree_defines(sub, g)
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
    defines = source_digest._worktree_defines(sub, g)
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
    _require_g13()
    g = Genome("silo", {"BACK_OFF": 1})
    sub, head, _git = _fake_ccbench_repo()
    hh = os.path.join(sub, "include", "backoff.hh")
    source_digest.assert_trace_diff_matches_head(g, head, sub)       # (a) stock 通過
    with open(hh, "w", encoding="utf-8") as f:                       # (b) TRACE 非依存の編集
        f.write(_FAKE_BACKOFF_HH.replace("return 1;", "return 2;"))
    source_digest.assert_trace_diff_matches_head(g, head, sub)
    with open(hh, "w", encoding="utf-8") as f:                       # (c) TRACE 挙動差の混入
        f.write(_FAKE_BACKOFF_HH.replace(
            "return 1;", "#if TRACE\n    int leak = 1;\n#endif\n    return 1;"))
    try:
        source_digest.assert_trace_diff_matches_head(g, head, sub)
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
    _require_g13()
    g = Genome("silo", {"BACK_OFF": 1})
    sub, _head, git = _fake_ccbench_repo()
    hh = os.path.join(sub, "include", "backoff.hh")
    with open(hh, "w", encoding="utf-8") as f:
        f.write(_FAKE_BACKOFF_TRACED)
    git("add", "-A")
    git("commit", "-q", "-m", "traced stock")
    head2 = git("rev-parse", "HEAD").strip()
    source_digest.assert_trace_diff_matches_head(g, head2, sub)      # (a)
    with open(hh, "w", encoding="utf-8") as f:                       # (b) ガード前に行追加
        f.write(_FAKE_BACKOFF_TRACED.replace(
            "  static int wait() {\n",
            "  static int wait() {\n    int pad = 0; (void)pad;\n"))
    source_digest.assert_trace_diff_matches_head(g, head2, sub)
    with open(hh, "w", encoding="utf-8") as f:                       # (c) ガード内改変
        f.write(_FAKE_BACKOFF_TRACED.replace("int trace_hits = 1;",
                                             "int trace_hits = 2;"))
    try:
        source_digest.assert_trace_diff_matches_head(g, head2, sub)
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
    from campaign import patchharness
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
    from campaign import patchharness
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
    from campaign import patchharness
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
    from campaign import patchharness
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
    from campaign import patchharness
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


def test_patchharness_fails_closed_on_dirty_or_unpinned_tree():
    """apply 前の pinned-clean assert: tracked 改変が残る tree / pin 不一致 / 空 pin には
    patch を当てない (前 variant の revert 漏れ・別セッション残骸との合成を防ぐ)。"""
    from campaign import patchharness
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
    from campaign import patchharness
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
    from campaign import patchharness
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
    from campaign import patchharness
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
    from campaign import patchharness
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
    from campaign import patchharness
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
    from campaign import patchharness
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
    from campaign import loop as L

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
            do_bench=False, output_root=out_root, log=messages.append, build_context=_BUILD_CONTEXT)
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


def test_loop_does_not_append_abort_after_wal_io_error():
    from campaign import loop as L

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
                    log=lambda message: None, build_context=_BUILD_CONTEXT)
            except (wal.WalAppendError, wal.WalFramingError) as exc:
                caught = exc
        finally:
            L.evaluate, L.source_digest = saved_eval, saved_sd
        bound_cfg = _bound(cfg)
        layout = campaign_layout(str(ident.campaign_id(bound_cfg)), out_root)
        assert caught is failure
        assert wal.read_records(layout) == []


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
