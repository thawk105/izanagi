# -*- coding: utf-8 -*-
"""orchestrator (campaign engine) STAGE1 の単体テスト (machine 非依存)。

pytest でも 素の `python orchestrator/tests/test_campaign.py` でも走る。
WAL/lock のテストは TMPDIR 配下に一時 campaign を作る (conftest.py は TMPDIR を
設定しないので、明示されていなければ環境既定の /tmp)。
"""
from __future__ import annotations

import atexit
import ast
import collections
import contextlib
import errno
import fcntl
import hashlib
import inspect
import json
import os
import shutil
import subprocess
import sys
import tempfile
import threading
import time
import types

_HERE = os.path.dirname(os.path.abspath(__file__))
_ORCH = os.path.dirname(_HERE)
sys.path.insert(0, _ORCH)

from campaign import (buildcache, genome, ident, pin, pipeline,  # noqa: E402
                      source_digest, wal)
from campaign import env_contract as ec                          # noqa: E402
from campaign import layout as layout_module                     # noqa: E402
from campaign.layout import (CampaignLayout,                     # noqa: E402
                             ExplorationCampaignLayout,
                             campaign_layout, ensure_exploration_namespace,
                             exploration_campaign_layout)
from campaign.lock import BenchBusy, bench_lock                  # noqa: E402
from campaign.model import (CampaignConfig, Genome,              # noqa: E402
                            STAGE_BENCH_DONE, STAGE_BUILD_DONE, STAGE_BUILD_START,
                            STAGE_COMMIT, STAGE_ABORT, STAGE_VERIFY_DONE,
                            STAGE_S1_SESSION, STAGE_S8B_ORACLE_SESSION,
                            STAGES, WAL_STAGES)
from campaign.pipeline import (EvalResult, PerfConfig,           # noqa: E402
                               ScreeningConfig)
from skiputil import Skip, skip                                  # noqa: E402
from verifier.model import (Anomaly, CycleEdge, EdgeReason,       # noqa: E402
                            Integrity, RW, VerifyResult)


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
    return CampaignConfig(**base)


def test_campaign_id_deterministic():
    assert str(ident.campaign_id(_cfg())) == str(ident.campaign_id(_cfg()))


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


def test_screening_search_config_omits_none_and_preserves_legacy_campaign_id():
    base = {"tier": "0-1", "scale": "silo"}
    search = {**base, **ident.screening_search_config(None)}
    assert search == base and "screening" not in search
    cfg = _cfg(search_config=search)
    assert str(ident.campaign_id(cfg)) == "readheavy-locont-fullsearch-45ca7ab9"


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
    """repr 正準化は screening key が無い歴史的 campaign の pre-image に触れない。"""
    import dataclasses

    from campaign.backoff_sweep import WORKLOADS as BACKOFF_WORKLOADS
    from campaign.backoff_sweep import config_for as backoff_config
    from campaign.s6_sort_sweep import config_for as s6_config

    # 歴史的 id は当時の ccbench pin (dff0f1e) で刻まれている。driver の現行 pin が
    # 進んでも pre-image 検査が成立するよう、照合はここで歴史的 pin に固定する。
    expected = {
        str(ident.campaign_id(dataclasses.replace(
            backoff_config(tag, workload), ccbench_commit="dff0f1e")))
        for tag, workload in BACKOFF_WORKLOADS
    }
    assert expected == {
        "backoff-sweep-silo-write-heavy-sweep-4891e99f",
        "backoff-sweep-silo-balanced-sweep-3d39fe94",
        "backoff-sweep-silo-read-heavy-sweep-9d37b4cf",
    }
    assert str(ident.campaign_id(s6_config("balanced"))) == \
        "p3-s6-sort-sweep-balanced-sweep-dd25aa8c"
    assert str(ident.campaign_id(s6_config("write-heavy"))) == \
        "p3-s6-sort-sweep-write-heavy-sweep-0484feef"


def test_identity_mismatch_guard():
    cfg = _cfg()
    stored = ident.canonical_preimage(cfg)
    ident.verify_against_lock(cfg, stored)                # 一致 → 例外なし
    try:
        ident.verify_against_lock(_cfg(spec_content="x"), stored)
        assert False, "should raise IdentityMismatch"
    except ident.IdentityMismatch:
        pass


def test_ensure_campaign_identity_uses_atomic_lock_and_loser_only_verifies():
    cfg = _cfg()
    lay = _layout()
    saved_write_lock = wal.write_lock

    def forbidden_write_lock(*_args, **_kwargs):
        raise AssertionError("非原子 write_lock を呼んではならない")

    wal.write_lock = forbidden_write_lock
    try:
        assert ident.ensure_campaign_identity(cfg, lay) is True
        assert wal.read_lock(lay) == ident.canonical_preimage(cfg)
        assert ident.ensure_campaign_identity(cfg, lay) is False
    finally:
        wal.write_lock = saved_write_lock


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
            ident.ensure_campaign_identity(cfg, lay)
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
        ident.ensure_campaign_identity(cfg, symlinked)
        assert False, "symlink WAL を lock 作成前に拒否すべき"
    except OSError as exc:
        assert exc.errno == errno.EINVAL
    assert open(target, "rb").read() == b"target-bytes"
    assert not os.path.exists(symlinked.lock_file)

    nonregular = _layout(); nonregular.ensure()
    os.mkdir(nonregular.wal_file)
    try:
        ident.ensure_campaign_identity(cfg, nonregular)
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
            ident.ensure_campaign_identity(cfg, lay)
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
        ident.ensure_resumable_wal(cfg, lay)
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
    wal.write_lock(lay, ident.canonical_preimage(stored_cfg))
    wal.log(lay, "v", STAGE_BUILD_START, "test")
    with open(lay.wal_file, "ab") as stream:
        stream.write(b"torn-tail")
    before = open(lay.wal_file, "rb").read()
    try:
        ident.ensure_resumable_wal(requested_cfg, lay)
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
    kt = buildcache.cache_key(g1, "abc123", trace=True)
    kp = buildcache.cache_key(g1, "abc123", trace=False)
    assert kt.endswith("_t1") and kp.endswith("_t0")    # trace 有無で別ビルド (規律1)
    assert kt != kp
    assert kt.startswith("silo_")
    assert kt != buildcache.cache_key(g2, "abc123", trace=True)  # genome 感度
    assert kt != buildcache.cache_key(g1, "xyz999", trace=True)  # ccbench-commit 感度


# ===== STAGE2: variant_id (WAL キー) =====

def test_variant_id_deterministic_and_sensitive():
    a = pipeline.variant_id(Genome("silo", {"BACK_OFF": 1, "WAL": 0}))
    a2 = pipeline.variant_id(Genome("silo", {"WAL": 0, "BACK_OFF": 1}))  # 順不同
    b = pipeline.variant_id(Genome("silo", {"BACK_OFF": 0, "WAL": 0}))
    assert a == a2 and len(a) == 12      # canonical なので flag 記述順に非依存
    assert a != b                        # flag 値が違えば別 id


# ===== STAGE2: 評価パイプライン (build→verify→[bench]→commit) =====
#
# 実ビルド/実機なしでパイプラインの制御フローと **規律2 の自動執行** を回帰テスト化する。
# pipeline モジュールの外部依存 (buildcache/verify/bench) をダミーに差し替え、
# verifier の verdict だけを操作して abort/commit の分岐を検査する。

def _tmp_layout():
    root = _tmpdir("izanagi_pipe_")
    return CampaignLayout(root=os.path.join(root, "campaigns", "test")).ensure()


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
                   trace_content=None, site_compilers=None):
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

    def fake_build(genome, commit, trace, src_token=None, ccbench_dir="", cache_root=""):
        bench_calls.builds.append(("legacy", trace, None))
        if build_raises:
            raise RuntimeError("build boom")
        bin_sha256 = ("da" if trace else "db") * 32  # 64 hex (WAL 新キー用)
        return types.SimpleNamespace(bin_hash=bin_sha256[:16], bin_sha256=bin_sha256,
                                     binary="/nonexistent/ycsb.exe", cached=False,
                                     configure_cmd="<cfg>", build_cmd="<build>")

    def fake_build_v2(genome, *, contract, ccbench_commit, trace, src_token,
                      cc, cxx, cache_root, ccbench_dir="", timeout_s=None,
                      dependency_prefix=""):
        bench_calls.builds.append(("v2", trace, contract.contract_sha256))
        bench_calls.build_roots.append(ccbench_dir)
        bench_calls.build_options.append({
            "cc": cc, "cxx": cxx, "dependency_prefix": dependency_prefix,
        })
        if build_raises:
            raise RuntimeError("build boom")
        bin_sha256 = ("da" if trace else "db") * 32
        return types.SimpleNamespace(
            bin_hash=bin_sha256[:16], bin_sha256=bin_sha256,
            binary="/nonexistent/ycsb.exe", cached=False,
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
    # source_digest は identity 核 (実 git/g++ 依存)。pipeline の段階遷移テストでは
    # mock し stock 固定 (source_digest 自体は専用テストで実機検証する)。
    def fake_source_resolve(*args, **kwargs):
        bench_calls.source_resolve_calls.append((args, kwargs))
        return "stock"

    patch("source_digest", types.SimpleNamespace(
        STOCK="stock",
        assert_worktree_within_allowlist=lambda *a, **k: None,
        src_token=lambda *a, **k: "stock",
        resolve=fake_source_resolve))
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
        wal.write_lock(lay, ident.canonical_preimage(cfg))
    with _mock_pipeline(**mock_kw) as calls:
        r = pipeline.evaluate(
            Genome("silo", {"BACK_OFF": 1}), lay, "test-env", "deadbeef",
            PerfConfig(records=1000, threads=2), clocks_per_us=1800,
            do_bench=do_bench, screening=screening,
            expected_perf_sha256=expected_perf_sha256,
            record_rep_returncodes=record_rep_returncodes,
            log=lambda *a: None)
    return r, calls


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
            Genome("silo", {"BACK_OFF": 1}), lay, "test-env", "deadbeef",
            PerfConfig(records=1000, threads=2), clocks_per_us=1800,
            do_bench=False, env_contract=contract, log=lambda *a: None,
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
            do_bench=False, env_contract=contract, dependency_prefix=prefix,
            log=lambda *a: None,
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
            Genome("silo", {"BACK_OFF": 1}), lay, "test-env", "deadbeef",
            PerfConfig(records=1000, threads=2), clocks_per_us=1800,
            do_bench=False, env_contract=contract, ccbench_dir=prepared_tree,
            log=lambda *a: None,
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
        terminal = wal.replay(lay)[r.variant].last_terminal
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
                Genome("silo", {"BACK_OFF": 1}), lay, "test-env", "deadbeef",
                PerfConfig(records=1000, threads=2), clocks_per_us=1800,
                do_bench=False, screening=_screening(), log=lambda *a: None)
            assert False, "should raise ValueError"
        except ValueError as e:
            assert "screening" in str(e) and "do_bench=False" in str(e)
    assert len(calls) == 0 and len(calls.trace) == 0
    assert list(wal.read_records(lay)) == []


def test_pipeline_rejects_runtime_screening_mixed_into_legacy_campaign():
    """F4監査再現: helper不使用の既存COMMIT campaignへscreeningを後付けできない。"""
    lay = _tmp_layout()
    legacy_cfg = _cfg()
    wal.write_lock(lay, ident.canonical_preimage(legacy_cfg))
    wal.log(lay, "already-committed", STAGE_COMMIT, "test-env", {"fitness_tps": 1.0})
    before = list(wal.read_records(lay))

    with _mock_pipeline() as calls:
        try:
            pipeline.evaluate(
                Genome("silo", {"BACK_OFF": 1}), lay, "test-env", "deadbeef",
                PerfConfig(records=1000, threads=2), clocks_per_us=1800,
                screening=_screening(), log=lambda *a: None)
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
        wal.write_lock(lay, ident.canonical_preimage(cfg))
        runtime = _screening(**changed)
        with _mock_pipeline() as calls:
            try:
                pipeline.evaluate(
                    Genome("silo", {"BACK_OFF": 1}), lay, "test-env", "deadbeef",
                    PerfConfig(records=1000, threads=2), clocks_per_us=1800,
                    screening=runtime, log=lambda *a: None)
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
        r = pipeline.evaluate(g, lay, "test-env", "deadbeef",
                              PerfConfig(records=1000, threads=2), clocks_per_us=1800,
                              do_bench=False, log=lambda *a: None)
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

    def fake_build(genome, commit, trace, src_token=None, ccbench_dir="", cache_root=""):
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
    patch("source_digest", types.SimpleNamespace(
        STOCK="stock", assert_worktree_within_allowlist=lambda *a, **k: None,
        src_token=lambda *a, **k: "stock", resolve=lambda *a, **k: "stock"))
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
            Genome("silo", {"BACK_OFF": 1}), lay, "test-env", "deadbeef",
            PerfConfig(records=1000, threads=2), clocks_per_us=1800, numactl=numa,
            extra_correctness=[(pipeline.S2_TAG, pipeline.s2_correctness_workload())],
            log=lambda *a: None)
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
            Genome("silo", {"BACK_OFF": 1}), lay, "test-env", "deadbeef",
            PerfConfig(records=1000, threads=2), clocks_per_us=1800,
            numactl=["numactl", "--interleave=all"],
            extra_correctness=[(pipeline.S2_TAG, pipeline.s2_correctness_workload())],
            do_bench=False, log=lambda *a: None)
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
            Genome("silo", {"BACK_OFF": 1}), lay, "test-env", "deadbeef",
            PerfConfig(records=1000, threads=2), clocks_per_us=1800,
            do_bench=False, log=lambda *a: None)
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
            Genome("silo", {"BACK_OFF": 1}), lay, "test-env", "deadbeef",
            PerfConfig(records=1000, threads=2), clocks_per_us=1800,
            extra_correctness=[(pipeline.S2_TAG, pipeline.s2_correctness_workload())],
            do_bench=False, log=lambda *a: None)
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
            Genome("silo", {"BACK_OFF": 1}), lay, "test-env", "deadbeef",
            PerfConfig(records=1000, threads=2), clocks_per_us=1800, numactl=numa,
            extra_correctness=[(pipeline.S2_TAG, pipeline.s2_correctness_workload())],
            do_bench=False, log=lambda *a: None)
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
            Genome("silo", {"BACK_OFF": 1}), lay, "test-env", "deadbeef",
            PerfConfig(records=1000, threads=2), clocks_per_us=1800, numactl=numa,
            extra_correctness=[(pipeline.S2_TAG, pipeline.s2_correctness_workload())],
            do_bench=False, log=lambda *a: None)
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
            Genome("silo", {"BACK_OFF": 1}), lay, "test-env", "deadbeef",
            PerfConfig(records=1000, threads=2), clocks_per_us=1800, numactl=numa,
            extra_correctness=[(pipeline.S2_TAG, pipeline.s2_correctness_workload())],
            do_bench=False, log=lambda *a: None)
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
        lay = campaign_layout(str(ident.campaign_id(cfg)), out_root).ensure()
        wal.write_lock(lay, ident.canonical_preimage(cfg))
        # run1: probe 故障 → terminal abort (evaluate は呼ばれた体で WAL を直書き)
        wal.log(lay, v, STAGE_BUILD_START, "test-env",
                {"genome": g.canonical(), "src_token": "stock"})
        wal.log(lay, v, STAGE_ABORT, "test-env",
                {"reason": reason, "probe_error": {"kind": "exec-failure"}})

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
            s = L.run_campaign(cfg, [g], PerfConfig(records=1, threads=1), "test-env",
                               1800, do_bench=False, output_root=out_root,
                               log=lambda *a: None)
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
        lay = campaign_layout(str(ident.campaign_id(cfg)), out_root).ensure()
        wal.write_lock(lay, ident.canonical_preimage(cfg))
        # run1: terminal abort (evaluate は呼ばれた体で WAL を直書き)
        wal.log(lay, v, STAGE_BUILD_START, "test-env",
                {"genome": g.canonical(), "src_token": "stock"})
        wal.log(lay, v, STAGE_ABORT, "test-env", {"reason": reason})

        calls = []

        def fake_eval(g, *a, **kw):
            calls.append(g)
            return EvalResult(genome=g,
                              variant=pipeline.variant_id(g, kw.get("src_token")),
                              certified=True, aborted=False, fitness_tps=100.0)

        saved = SD.evaluate
        SD.evaluate = fake_eval
        try:
            res = SD.evaluate_candidate(
                cfg, lay, g, PerfConfig(records=1, threads=1), "test-env", 1800,
                screening=None, src_token="stock", log=lambda *a: None)
        finally:
            SD.evaluate = saved
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
                  ccbench_dir="", cache_root=""):
        captured["extra_correctness"] = extra_correctness
        v = pipeline.variant_id(g, src_token or "stock")
        wal.log(layout, v, STAGE_BUILD_START, env_tag, {"genome": g.canonical()})
        wal.log(layout, v, STAGE_COMMIT, env_tag, {"fitness_tps": 1.0})
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
                       PerfConfig(records=1, threads=1), "test-env", 1800,
                       output_root=out_root, log=lambda *a: None)
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
                  ccbench_dir="", cache_root=""):
        captured["extra_correctness"] = extra_correctness
        v = pipeline.variant_id(g, src_token or "stock")
        wal.log(layout, v, STAGE_BUILD_START, env_tag, {"genome": g.canonical()})
        wal.log(layout, v, STAGE_COMMIT, env_tag, {"fitness_tps": 1.0})
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
                       PerfConfig(records=1, threads=1), "test-env", 1800,
                       output_root=out_root, log=lambda *a: None)
    finally:
        L.evaluate, L.source_digest = saved_eval, saved_sd
    assert captured["extra_correctness"] is None


def test_m12_loop_compute_uses_gxx_and_forwards_only_contract_and_prefix():
    from campaign import loop as L

    captured = {"resolve": [], "evaluate": []}
    contract = ec.lookup("pegasus")
    prefix = "/scr/job/gflags;/scr/job/glog"

    def resolve(*args, **kwargs):
        captured["resolve"].append((args, kwargs))
        return "stock"

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
    L.source_digest = types.SimpleNamespace(STOCK="stock", resolve=resolve)
    L._compilers_for_current_site = lambda: ("gcc", "g++")
    L._authorize_measurement = lambda *args, **kwargs: {"fixture": "receipt"}
    try:
        summary = L.run_campaign(
            cfg, [Genome("silo", {"BACK_OFF": 1})],
            PerfConfig(records=1, threads=1), "pegasus", 2100,
            do_bench=False, output_root=out_root, log=lambda *a: None,
            env_contract=contract, dependency_prefix=prefix,
            numactl=contract.numactl,
        )
    finally:
        L.evaluate, L.source_digest = saved_eval, saved_sd
        L._compilers_for_current_site = saved_compilers
        L._authorize_measurement = saved_authorize

    assert captured["resolve"][0][0][-1] == "g++"
    assert captured["evaluate"][0]["env_contract"] == contract
    assert captured["evaluate"][0]["dependency_prefix"] == prefix
    assert "site" not in inspect.signature(L.run_campaign).parameters
    assert summary.campaign_id == str(ident.campaign_id(cfg))
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
            env_contract=contract,
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
        def _resolve(*a, **k):
            return src_token
    return types.SimpleNamespace(STOCK="stock", resolve=_resolve)


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
        s = L.run_campaign(cfg, genomes, PerfConfig(records=1, threads=1),
                           "test-env", 1800, do_bench=do_bench,
                           output_root=out_root, log=lambda *a: None)
    finally:
        L.evaluate, L.source_digest = saved, saved_sd
    lay = campaign_layout(str(ident.campaign_id(cfg)), out_root)
    return s, lay


def test_run_campaign_default_namespace_remains_official():
    """selector 省略時は既存どおり official root を使う。"""
    from campaign import loop as L

    out_root = _tmpdir("izanagi_loop_namespace_default_")
    cfg = CampaignConfig(spec_slug="t", search_tag="enum",
                         spec_content="namespace-default", ccbench_commit="deadbeef")
    summary = L.run_campaign(
        cfg, [], PerfConfig(records=1, threads=1), "test-env", 1800,
        do_bench=False, output_root=out_root, log=lambda *_args: None,
    )
    expected = campaign_layout(str(ident.campaign_id(cfg)), out_root)
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
        wal.log(layout, variant, STAGE_COMMIT, env_tag, {"fitness_tps": 1.0})
        return EvalResult(genome=g, variant=variant, certified=True, aborted=False,
                          fitness_tps=1.0)

    saved_eval, saved_sd = L.evaluate, L.source_digest
    L.evaluate = fake_eval
    L.source_digest = _sd_mock("stock")
    try:
        summary = L.run_campaign(
            cfg, [genome], PerfConfig(records=1, threads=1), "test-env", 1800,
            do_bench=False, output_root=out_root, log=lambda *_args: None,
            campaign_namespace="exploration",
        )
    finally:
        L.evaluate, L.source_digest = saved_eval, saved_sd

    expected = exploration_campaign_layout(str(ident.campaign_id(cfg)), out_root)
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
            do_bench=False, output_root=out_root, log=lambda *_args: None,
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
    common = (cfg, [], PerfConfig(records=1, threads=1), "test-env", 1800)
    official = L.run_campaign(
        *common, do_bench=False, output_root=out_root, log=lambda *_args: None,
    )
    exploration = L.run_campaign(
        *common, do_bench=False, output_root=out_root, log=lambda *_args: None,
        campaign_namespace="exploration",
    )
    assert official.campaign_id == exploration.campaign_id == str(ident.campaign_id(cfg))


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
    assert wal.replay(lay)[bad].aborted


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
    lay = campaign_layout(str(ident.campaign_id(cfg)), out_root).ensure()
    wal.write_lock(lay, ident.canonical_preimage(cfg))
    wal.log(lay, src_id, STAGE_BUILD_START, "test-env", {"genome": g.canonical()})
    wal.log(lay, src_id, STAGE_COMMIT, "test-env", {"fitness_tps": 100.0})

    calls = []

    def fake_eval(g, *a, **kw):
        calls.append(g)
        return EvalResult(genome=g, variant=src_id, certified=True, aborted=False)

    saved, saved_sd = L.evaluate, L.source_digest
    L.evaluate = fake_eval
    L.source_digest = _sd_mock("codediff")
    try:
        s = L.run_campaign(cfg, [g], PerfConfig(records=1, threads=1), "test-env",
                           1800, do_bench=False, output_root=out_root, log=lambda *a: None)
    finally:
        L.evaluate, L.source_digest = saved, saved_sd
    assert len(calls) == 0 and s.skipped == 1            # src_token id terminal → 再評価しない
    # リカバリ skip = 重複提案の実体。呼び手 (_resolve_duplicate) はこの確定済み id だけを
    # 使う — revert 後 tree の再 resolve は stock id = 別 variant を引く ([T-157])
    assert s.skipped_variants == [src_id]


def test_loop_isolates_identity_error():
    """source_digest.resolve が確定不能 (RuntimeError) なら loop が stock id で abort 隔離し継続。"""
    def fake_eval(g, *a, **kw):
        raise AssertionError("identity-error 時は evaluate を呼ばない")

    genomes = [Genome("silo", {"BACK_OFF": 0}), Genome("silo", {"BACK_OFF": 1})]
    s, lay = _loop_with_fake_eval(fake_eval, genomes, "id-err",
                                  src_token=RuntimeError("g++ 不在"))
    assert s.aborted == 2 and s.committed == 0 and s.evaluated == 2
    st = wal.replay(lay)
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
        s1 = L.run_campaign(cfg, [g], PerfConfig(records=1, threads=1), "test-env",
                            1800, do_bench=False, output_root=out_root, log=lambda *a: None)
        assert s1.aborted == 1 and len(calls) == 0
        # run2: 環境修復 (resolve 成功 → stock) → 永久 skip でなく再評価・commit
        L.source_digest = _sd_mock("stock")
        s2 = L.run_campaign(cfg, [g], PerfConfig(records=1, threads=1), "test-env",
                            1800, do_bench=False, output_root=out_root, log=lambda *a: None)
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
    lay = campaign_layout(str(ident.campaign_id(cfg)), out_root).ensure()
    wal.write_lock(lay, ident.canonical_preimage(cfg))
    # run1: identity-error abort (stock id)
    wal.log(lay, v_stock, STAGE_BUILD_START, "test-env", {"genome": g.canonical()})
    wal.log(lay, v_stock, STAGE_ABORT, "test-env",
            {"reason": "identity-error", "error": "g++ 一時不在"})
    # run2: 修復後の再評価が BUILD_START を書いた直後にクラッシュ (COMMIT/ABORT なし)
    wal.log(lay, v_stock, STAGE_BUILD_START, "test-env", {"genome": g.canonical()})

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
        s3 = L.run_campaign(cfg, [g], PerfConfig(records=1, threads=1), "test-env",
                            1800, do_bench=False, output_root=out_root,
                            log=lambda *a: None)
    finally:
        L.evaluate, L.source_digest = saved, saved_sd
    assert len(calls) == 1 and s3.committed == 1 and s3.skipped == 0


def test_loop_identity_skip_is_visible_when_stock_id_terminal():
    """identity 確定不能かつ stock id が terminal 済みのときの skip は identity_skipped
    として summary に分離カウントされる (規律3: 成果物からの欠落を沈黙させない)。"""
    from campaign import loop as L
    out_root = _tmpdir("izanagi_loop_idskip_")
    cfg = CampaignConfig(spec_slug="t", search_tag="enum",
                         spec_content="id-skip-vis", ccbench_commit="deadbeef")
    g = Genome("silo", {"BACK_OFF": 1})
    v_stock = pipeline.variant_id(g)
    lay = campaign_layout(str(ident.campaign_id(cfg)), out_root).ensure()
    wal.write_lock(lay, ident.canonical_preimage(cfg))
    # 過去 run で stock id が commit 済み (coder variant の working-tree で再開する状況)
    wal.log(lay, v_stock, STAGE_BUILD_START, "test-env", {"genome": g.canonical()})
    wal.log(lay, v_stock, STAGE_COMMIT, "test-env", {"fitness_tps": 100.0})

    saved_sd = L.source_digest
    L.source_digest = _sd_mock(RuntimeError("git 一時故障"))
    try:
        s = L.run_campaign(cfg, [g], PerfConfig(records=1, threads=1), "test-env",
                           1800, do_bench=False, output_root=out_root,
                           log=lambda *a: None)
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
_GOLDEN_CK0 = {  # cache_key (trace=False) の後方互換 golden (1 例)
    "silo|BACK_OFF=0,NO_WAIT_LOCKING_IN_VALIDATION=0,NO_WAIT_OF_TICTOC=1,WAL=0": "silo_24dd2f7509_t0",
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


def test_source_digest_silo8_id_backward_compatible():
    """silo 8 genome の variant_id/cache_key がリファクタ後も不変 (既存 WAL/cache 整合)。
    デフォルト src='stock' は canonical のみハッシュ = 旧値 (実機非依存)。"""
    for g in genome.SILO_SPACE.enumerate():
        assert pipeline.variant_id(g) == _GOLDEN_VID[g.canonical()], g.canonical()
    # cache_key は純関数 (ccbench_commit を pre-image に織り込む・working-tree 非依存)。
    # golden は kickoff pin (dff0f1e) で計算された値なので、live HEAD ではなくその固定 pin
    # で導出を検証する — 後続段 3 の pin 前進 (028f34d, D38) で cache_key が変わるのは
    # 設計どおり (content-addressed identity は pin と共に動く) で、backward-compat golden は
    # 「dff0f1e 時点の導出が安定か」を pin 非依存にテストする (裁定12/IDENT-1)。
    g0 = Genome("silo", {"BACK_OFF": 0, "NO_WAIT_LOCKING_IN_VALIDATION": 0,
                         "NO_WAIT_OF_TICTOC": 1, "WAL": 0})
    # golden は full hash (旧 live HEAD) で計算された値。pin.KICKOFF_PIN_FULL で照合する。
    assert (buildcache.cache_key(g0, pin.KICKOFF_PIN_FULL, False)
            == _GOLDEN_CK0[g0.canonical()])


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
    assert (buildcache.cache_key(g50, head, False, t50)
            != buildcache.cache_key(g50, head, False))


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
    assert os.path.isdir(bdir)
    buildcache.source_digest = types.SimpleNamespace(
        STOCK="stock", resolve=lambda *a, **k: "mutated123")
    try:
        try:
            buildcache._recheck_src_token(g, "deadbeef", "/x", "g++-13",
                                          expected="stock", bdir=bdir,
                                          built_fresh=True)
            assert False, "src_token 不一致で停止すべき"
        except RuntimeError as e:
            assert "TOCTOU" in str(e)
        assert not os.path.exists(bdir)              # 新規ビルドは破棄
        # 一致なら通過 (正常経路)
        buildcache.source_digest = types.SimpleNamespace(
            STOCK="stock", resolve=lambda *a, **k: "stock")
        buildcache._recheck_src_token(g, "deadbeef", "/x", "g++-13",
                                      expected="stock", bdir="/nonexistent",
                                      built_fresh=False)
    finally:
        buildcache.source_digest = saved


def test_buildcache_cache_hit_rechecks_identity():
    """cache hit 経路でも identity 再照合が走る (resolve→hit 判定間の TOCTOU も遮断)。
    hit の不一致は既存 (過去の正当な) 成果物なので破棄せず停止のみ。"""
    g = Genome("silo", {"BACK_OFF": 1})
    sub, head, _git = _fake_ccbench_repo()
    root = _tmpdir("izanagi_bc_root_")
    key = buildcache.cache_key(g, head, trace=True, src_token="stock")
    bindir = os.path.join(root, key, "cc", "silo")
    os.makedirs(bindir)
    binary = os.path.join(bindir, "ycsb_silo.exe")
    with open(binary, "w") as f:
        f.write("fake-binary")
    saved = buildcache.source_digest

    def _sd(resolved):
        return types.SimpleNamespace(
            STOCK="stock",
            assert_worktree_within_allowlist=lambda *a, **k: None,
            assert_trace_diff_matches_head=lambda *a, **k: None,
            resolve=lambda *a, **k: resolved)

    try:
        buildcache.source_digest = _sd("mutated456")
        try:
            buildcache.build(g, head, trace=True, cache_root=root,
                             ccbench_dir=sub, src_token="stock")
            assert False, "cache hit でも TOCTOU 不一致で停止すべき"
        except RuntimeError as e:
            assert "TOCTOU" in str(e)
        assert os.path.exists(binary)                # hit 側は破棄しない
        buildcache.source_digest = _sd("stock")
        br = buildcache.build(g, head, trace=True, cache_root=root,
                              ccbench_dir=sub, src_token="stock")
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
    key = buildcache.cache_key(g, head, trace=True, src_token="stock")
    binary = os.path.join(root, key, "cc", "silo", "ycsb_silo.exe")

    def fake_run(cmd, what):                 # configure/build を no-op 化し binary だけ置く
        if what == "build":
            os.makedirs(os.path.dirname(binary), exist_ok=True)
            with open(binary, "w") as f:
                f.write("fake-binary")

    def _sd(resolved):
        return types.SimpleNamespace(
            STOCK="stock",
            assert_worktree_within_allowlist=lambda *a, **k: None,
            assert_trace_diff_matches_head=lambda *a, **k: None,
            resolve=lambda *a, **k: resolved)

    saved_sd, saved_run = buildcache.source_digest, buildcache._run
    try:
        buildcache._run = fake_run
        buildcache.source_digest = _sd("mutated789")
        try:
            buildcache.build(g, head, trace=True, cache_root=root,
                             ccbench_dir=sub, src_token="stock")
            assert False, "cache-miss 側でも build 直後の recheck で停止すべき"
        except RuntimeError as e:
            assert "TOCTOU" in str(e)
        assert not os.path.exists(os.path.join(root, key))   # 新規ビルドは dir ごと破棄
        buildcache.source_digest = _sd("stock")
        br = buildcache.build(g, head, trace=True, cache_root=root,
                              ccbench_dir=sub, src_token="stock")
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
    key = buildcache.cache_key(g, head, trace=True, src_token="stock")
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
            resolve=lambda *a, **k: resolved)

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
            os.makedirs(os.path.dirname(binary), exist_ok=True)
            with open(binary, "w") as f:
                f.write("fake-binary")

    saved_sd, saved_run = buildcache.source_digest, buildcache._run
    try:
        buildcache._run = fake_run
        buildcache.source_digest = _sd("stock")
        br = buildcache.build(g, head, trace=True, cache_root=root,
                              ccbench_dir=sub, src_token="stock")
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
    key = buildcache.cache_key(g, head, trace=True, src_token="stock")
    binary = os.path.join(root, key, "cc", "silo", "ycsb_silo.exe")
    payload = b"real-fixture-binary-bytes"
    # 期待値は本番 helper でなく hashlib で独立に計算する (恒真回避)。
    expect = hashlib.sha256(payload).hexdigest()

    def fake_run(cmd, what):
        if what == "build":
            os.makedirs(os.path.dirname(binary), exist_ok=True)
            with open(binary, "wb") as f:
                f.write(payload)

    sd = types.SimpleNamespace(
        STOCK="stock",
        assert_worktree_within_allowlist=lambda *a, **k: None,
        assert_trace_diff_matches_head=lambda *a, **k: None,
        resolve=lambda *a, **k: "stock")

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
                              ccbench_dir=sub, src_token="stock")
        assert not fr.cached
        assert calls["n"] == 1                       # fresh 経路で 1 回だけ
        assert fr.bin_sha256 == expect and len(fr.bin_sha256) == 64
        assert fr.bin_hash == fr.bin_sha256[:16]     # 派生 property
        calls["n"] = 0
        hr = buildcache.build(g, head, trace=True, cache_root=root,
                              ccbench_dir=sub, src_token="stock")
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
    key = buildcache.cache_key(g, head, trace=True, src_token="stock")
    binary = os.path.join(root, key, "cc", "silo", "ycsb_silo.exe")

    def _sd(trace_diff_raises):
        def _atd(*a, **k):
            if trace_diff_raises:
                raise RuntimeError("diff-of-diffs 不一致 (テスト注入)")
        return types.SimpleNamespace(
            STOCK="stock",
            assert_worktree_within_allowlist=lambda *a, **k: None,
            assert_trace_diff_matches_head=_atd,
            resolve=lambda *a, **k: "stock")

    def fake_run(cmd, what):
        if what == "build":
            os.makedirs(os.path.dirname(binary), exist_ok=True)
            with open(binary, "w") as f:
                f.write("fake-binary")

    saved_sd, saved_run = buildcache.source_digest, buildcache._run
    try:
        buildcache._run = fake_run
        buildcache.source_digest = _sd(trace_diff_raises=True)
        try:                                     # fresh: 不一致 → 破棄 + 停止
            buildcache.build(g, head, trace=True, cache_root=root,
                             ccbench_dir=sub, src_token="stock")
            assert False, "fresh build で diff-of-diffs 不一致なら停止すべき"
        except RuntimeError as e:
            assert "diff-of-diffs" in str(e)
        assert not os.path.exists(os.path.join(root, key))   # fresh は dir ごと破棄
        buildcache.source_digest = _sd(trace_diff_raises=False)
        br = buildcache.build(g, head, trace=True, cache_root=root,
                              ccbench_dir=sub, src_token="stock")
        assert not br.cached                     # 通過なら新規ビルドが返る
        buildcache.source_digest = _sd(trace_diff_raises=True)
        try:                                     # hit: 検査は走る・破棄はしない
            buildcache.build(g, head, trace=True, cache_root=root,
                             ccbench_dir=sub, src_token="stock")
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
    cfg = CampaignConfig(spec_slug="t", search_tag="enum",
                         spec_content="tail-resume", ccbench_commit="deadbeef")
    layout = campaign_layout(str(ident.campaign_id(cfg)), out_root).ensure()
    wal.write_lock(layout, ident.canonical_preimage(cfg))
    wal.log(layout, "prior", STAGE_COMMIT, "test-env", {"fitness_tps": 1.0})
    with open(layout.wal_file, "ab") as stream:
        stream.write("途中".encode("utf-8")[:4])
    genome = Genome("silo", {"BACK_OFF": 1})
    messages = []

    def fake_eval(candidate, candidate_layout, env_tag, *args, **kwargs):
        records, truncated = wal.read_records_checked(candidate_layout)
        assert truncated is False and [r.variant for r in records] == ["prior"]
        variant = pipeline.variant_id(candidate, kwargs["src_token"])
        wal.log(candidate_layout, variant, STAGE_BUILD_START, env_tag,
                {"genome": candidate.canonical()})
        wal.log(candidate_layout, variant, STAGE_COMMIT, env_tag,
                {"fitness_tps": 2.0})
        return EvalResult(genome=candidate, variant=variant, certified=True,
                          aborted=False, fitness_tps=2.0)

    saved_eval, saved_sd = L.evaluate, L.source_digest
    L.evaluate = fake_eval
    L.source_digest = _sd_mock("stock")
    try:
        summary = L.run_campaign(
            cfg, [genome], PerfConfig(records=1, threads=1), "test-env", 1800,
            do_bench=False, output_root=out_root, log=messages.append)
    finally:
        L.evaluate, L.source_digest = saved_eval, saved_sd
    records, truncated = wal.read_records_checked(layout)
    repair_messages = [m for m in messages if "WAL tail repair:" in m]
    assert summary.committed == 1 and truncated is False
    assert [r.stage for r in records] == [
        STAGE_COMMIT, STAGE_BUILD_START, STAGE_COMMIT]
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
                    "test-env", 1800, do_bench=False, output_root=out_root,
                    log=lambda message: None)
            except (wal.WalAppendError, wal.WalFramingError) as exc:
                caught = exc
        finally:
            L.evaluate, L.source_digest = saved_eval, saved_sd
        layout = campaign_layout(str(ident.campaign_id(cfg)), out_root)
        assert caught is failure
        assert wal.read_records(layout) == []


def _run():
    fns = [v for k, v in sorted(globals().items())
           if k.startswith("test_") and callable(v)]
    passed = failed = skipped = 0
    for fn in fns:
        try:
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
