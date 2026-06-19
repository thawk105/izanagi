# -*- coding: utf-8 -*-
"""orchestrator (campaign engine) STAGE1 の単体テスト (machine 非依存)。

pytest でも 素の `python orchestrator/tests/test_campaign.py` でも走る。
WAL/lock のテストは TMPDIR (=/home 配下) に一時 campaign を作る。
"""
from __future__ import annotations

import os
import sys
import tempfile

_HERE = os.path.dirname(os.path.abspath(__file__))
_ORCH = os.path.dirname(_HERE)
sys.path.insert(0, _ORCH)

from campaign import genome, ident, wal                          # noqa: E402
from campaign.layout import CampaignLayout                       # noqa: E402
from campaign.lock import BenchBusy, bench_lock                  # noqa: E402
from campaign.model import (CampaignConfig, Genome,              # noqa: E402
                            STAGE_BUILD_DONE, STAGE_BUILD_START,
                            STAGE_COMMIT, STAGE_ABORT, STAGE_VERIFY_DONE)


# ===== genome 列挙 =====

def test_silo_space_size_and_constraint():
    gs = genome.space_for("silo")
    assert gs.raw_size() == 16              # 2^4
    genomes = gs.enumerate()
    assert len(genomes) == 12               # 相互排他 (両 no-wait=1) を 4 除外
    # 両 no-wait=1 は 1 個も無い
    for g in genomes:
        assert not (g.flags["NO_WAIT_LOCKING_IN_VALIDATION"] == 1
                    and g.flags["NO_WAIT_OF_TICTOC"] == 1)


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


def test_identity_mismatch_guard():
    cfg = _cfg()
    stored = ident.canonical_preimage(cfg)
    ident.verify_against_lock(cfg, stored)                # 一致 → 例外なし
    try:
        ident.verify_against_lock(_cfg(spec_content="x"), stored)
        assert False, "should raise IdentityMismatch"
    except ident.IdentityMismatch:
        pass


# ===== WAL / recovery / atomicity (D, A) =====

def _layout():
    d = tempfile.mkdtemp(prefix="izanagi_camp_")     # TMPDIR=/home 配下
    return CampaignLayout(root=d)


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
    states = wal.replay(lay)                              # 例外を投げず
    assert states["v4"].committed
    assert "v5" not in states                             # 壊れた行は捨てる


def test_lock_preimage_roundtrip_and_immutable():
    lay = _layout(); lay.ensure()
    pre = "preimage-A"
    wal.write_lock(lay, pre)
    assert wal.read_lock(lay) == pre
    wal.write_lock(lay, "preimage-B")                    # 既存があれば上書きしない
    assert wal.read_lock(lay) == pre


# ===== bench 排他ロック (I) =====

def test_bench_lock_exclusive():
    fd_path = os.path.join(tempfile.mkdtemp(prefix="izanagi_lock_"), "bench.lock")
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


# ---- 素の runner ----

def _run():
    fns = [v for k, v in sorted(globals().items())
           if k.startswith("test_") and callable(v)]
    passed = failed = 0
    for fn in fns:
        try:
            fn()
            print(f"PASS {fn.__name__}")
            passed += 1
        except AssertionError as e:
            print(f"FAIL {fn.__name__}: {e}")
            failed += 1
        except Exception as e:  # noqa: BLE001
            print(f"ERROR {fn.__name__}: {type(e).__name__}: {e}")
            failed += 1
    print(f"\n{passed} passed, {failed} failed")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(_run())
