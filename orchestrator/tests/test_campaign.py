# -*- coding: utf-8 -*-
"""orchestrator (campaign engine) STAGE1 の単体テスト (machine 非依存)。

pytest でも 素の `python orchestrator/tests/test_campaign.py` でも走る。
WAL/lock のテストは TMPDIR (=/home 配下) に一時 campaign を作る。
"""
from __future__ import annotations

import atexit
import contextlib
import os
import shutil
import subprocess
import sys
import tempfile
import types

_HERE = os.path.dirname(os.path.abspath(__file__))
_ORCH = os.path.dirname(_HERE)
sys.path.insert(0, _ORCH)

from campaign import (buildcache, genome, ident, pipeline,       # noqa: E402
                      source_digest, wal)
from campaign.layout import CampaignLayout, campaign_layout      # noqa: E402
from campaign.lock import BenchBusy, bench_lock                  # noqa: E402
from campaign.model import (CampaignConfig, Genome,              # noqa: E402
                            STAGE_BENCH_DONE, STAGE_BUILD_DONE, STAGE_BUILD_START,
                            STAGE_COMMIT, STAGE_ABORT, STAGE_VERIFY_DONE)
from campaign.pipeline import EvalResult, PerfConfig             # noqa: E402
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

def _tmpdir(prefix: str) -> str:
    """テスト用一時 dir。プロセス終了時に後始末する (TMPDIR=/home 配下に leak させない)。"""
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
                   build_raises=False, high_variance=False, unstable=False,
                   competing=None):
    """pipeline の外部依存をダミー化。trace の rc/commit 数・bench の throughput・
    build 失敗を引数で操作し、evaluate の分岐 (特に規律2 の abort) を検査する。
    yield する list = measure_point (実 bench) が呼ばれた回数の証跡。"""
    bench_calls = []
    saved = {}

    def patch(name, val):
        saved[name] = getattr(pipeline, name)
        setattr(pipeline, name, val)

    @contextlib.contextmanager
    def fake_lock(*a, **k):
        yield

    def fake_measure(*a, **k):
        bench_calls.append(1)                            # 実 bench が走った証跡
        return types.SimpleNamespace(
            throughputs=([] if median is None else [median, median]),
            run_cmd="<run>",
            leading_indicators=lambda: {"throughput_tps": median,
                                        "abort_rate": 0.03, "latency_ns": 1000.0,
                                        "llc_miss_rate": 0.2, "ipc": 1.5})

    def fake_build(genome, commit, trace, src_token=None):
        if build_raises:
            raise RuntimeError("build boom")
        return types.SimpleNamespace(bin_hash="dead" + ("t" if trace else "p"),
                                     binary="/nonexistent/ycsb.exe", cached=False,
                                     configure_cmd="<cfg>", build_cmd="<build>")

    patch("buildcache", types.SimpleNamespace(build=fake_build))
    # source_digest は identity 核 (実 git/g++ 依存)。pipeline の段階遷移テストでは
    # mock し stock 固定 (source_digest 自体は専用テストで実機検証する)。
    patch("source_digest", types.SimpleNamespace(
        STOCK="stock",
        assert_worktree_within_allowlist=lambda *a, **k: None,
        src_token=lambda *a, **k: "stock",
        resolve=lambda *a, **k: "stock"))
    patch("_run_trace", lambda *a, **k: (ncommit, rc))
    # 実 VerifyResult を返す (result_to_dict が S4 で abort payload を作るので duck-type 不可)。
    patch("verify_trace_dir", lambda tdir: _green_vr() if certified else _red_vr())
    def fake_remeasure(measure_fn, settle_fn=None, **k):
        # 自動再測定を 1 ラウンドに畳む。measure_fn を呼ぶことで実 bench の証跡を残し、
        # 実 noise_floor 同様 throughput が空なら median=None。median/cv/unstable は引数で操作。
        pt = measure_fn()
        nf = types.SimpleNamespace(
            median=(median if pt.throughputs else None), cv=cv,
            high_variance=high_variance)
        return types.SimpleNamespace(point=pt, nf=nf, rounds=1,
                                     stable=not unstable, unstable=unstable,
                                     cv_history=[cv])

    patch("bench_lock", fake_lock)
    patch("settle", lambda *a, **k: {"settled": True})
    patch("competing_bench_pids", lambda: list(competing or []))  # 既定: 単一テナント
    patch("measure_point", fake_measure)
    patch("remeasure_until_stable", fake_remeasure)
    try:
        yield bench_calls
    finally:
        for k, v in saved.items():
            setattr(pipeline, k, v)


def _eval(lay, do_bench=True, **mock_kw):
    """1 genome を mock 下で評価し (EvalResult, bench 呼び出し回数 list) を返す。"""
    with _mock_pipeline(**mock_kw) as calls:
        r = pipeline.evaluate(
            Genome("silo", {"BACK_OFF": 1}), lay, "test-env", "deadbeef",
            PerfConfig(records=1000, threads=2), clocks_per_us=1800,
            do_bench=do_bench, log=lambda *a: None)
    return r, calls


def test_pipeline_green_commits_with_fitness():
    lay = _tmp_layout()
    r, calls = _eval(lay, certified=True)
    assert r.certified and not r.aborted
    assert r.fitness_tps == 12345.0 and len(calls) == 1
    st = wal.replay(lay)[r.variant]
    assert st.committed and not st.aborted
    assert STAGE_COMMIT in st.stages_seen


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


def test_pipeline_build_error_aborts():
    """overnight 耐性: ビルド失敗はこの variant 固有の失敗として abort 隔離する。"""
    lay = _tmp_layout()
    r, calls = _eval(lay, build_raises=True)
    assert r.aborted and not r.certified and len(calls) == 0
    st = wal.replay(lay)[r.variant]
    assert st.aborted and STAGE_BUILD_DONE not in st.stages_seen


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


# ===== STAGE2: provenance / path 防御 =====

def test_buildcache_rejects_commit_mismatch():
    """宣言 ccbench_commit が submodule 実 HEAD とずれたら停止 (偽キャッシュヒット防止)。"""
    sub = buildcache._ccbench_dir()
    if not os.path.exists(os.path.join(sub, ".git")):
        return                                   # submodule 未 init ならスキップ
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


def test_source_digest_silo8_id_backward_compatible():
    """silo 8 genome の variant_id/cache_key がリファクタ後も不変 (既存 WAL/cache 整合)。
    デフォルト src='stock' は canonical のみハッシュ = 旧値 (実機非依存)。"""
    for g in genome.SILO_SPACE.enumerate():
        assert pipeline.variant_id(g) == _GOLDEN_VID[g.canonical()], g.canonical()
    head = _ccbench_head_or_skip()
    if head:
        g0 = Genome("silo", {"BACK_OFF": 0, "NO_WAIT_LOCKING_IN_VALIDATION": 0,
                             "NO_WAIT_OF_TICTOC": 1, "WAL": 0})
        assert buildcache.cache_key(g0, head, False) == _GOLDEN_CK0[g0.canonical()]


def test_source_digest_parse_options_defaults():
    """Options パース: 既定値・クォート剥がし・空値 unset (D23 finding 対策)。"""
    sub = buildcache._ccbench_dir()
    with open(os.path.join(sub, "cmake/Options.cmake"), encoding="utf-8") as f:
        d = source_digest.parse_options_defaults(f.read())
    assert d["BACKOFF_FIXED"] == "-1" and d["BACK_OFF"] == "1"
    assert "INSERT_READ_DELAY_MS" not in d        # 空値 ("") は除外


def test_source_digest_stock_roundtrip():
    """実 working-tree (inert) で silo 8 genome は src_token='stock' = 旧 id 不変 (後方互換)。"""
    head = _ccbench_head_or_skip()
    if head is None:
        return
    for g in genome.SILO_SPACE.enumerate():
        st = source_digest.src_token(g, head)
        assert st == source_digest.STOCK, g.canonical()
        assert pipeline.variant_id(g, st) == pipeline.variant_id(g)


def test_source_digest_fixed_variant_distinct():
    """BACKOFF_FIXED 枝は stock と別 id・値違いも別 id (alias 防止)。-1 は #else=stock。"""
    head = _ccbench_head_or_skip()
    if head is None:
        return
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
    """#if 参照マクロの供給漏れは -Werror=undef で fails-closed (規律6/2)。"""
    sub = buildcache._ccbench_dir()
    with open(os.path.join(sub, "include/backoff.hh"), encoding="utf-8") as f:
        src = f.read()
    try:
        source_digest._cpp_normalize(src, {"BACKOFF_NOINLINE": "0"}, "g++-13")  # FIXED 欠落
        assert False, "供給漏れで停止すべき (-Werror=undef)"
    except RuntimeError:
        pass


def test_source_digest_semantic_comment_vs_behavior():
    """コメントのみ変更は同 digest (cpp -P 除去)、挙動変更 (memory_order) は別 digest。"""
    sub = buildcache._ccbench_dir()
    with open(os.path.join(sub, "cmake/Options.cmake"), encoding="utf-8") as f:
        defines = source_digest._merge_defines(
            source_digest.parse_options_defaults(f.read()), {})
    with open(os.path.join(sub, "include/backoff.hh"), encoding="utf-8") as f:
        src = f.read()
    base = source_digest._cpp_normalize(src, defines, "g++-13")
    commented = source_digest._cpp_normalize(src + "\n// trailing comment\n", defines, "g++-13")
    behaved = source_digest._cpp_normalize(
        src.replace("memory_order_acquire", "memory_order_relaxed"), defines, "g++-13")
    assert base == commented              # コメント不感 (honest: 挙動不変なら同 id)
    assert base != behaved                # 挙動変更は検出


def test_source_digest_allowlist():
    """allowlist 内 (Options.cmake/backoff.hh) は通過、外 (transaction.cc) は fails-closed。"""
    saved = source_digest.subprocess
    try:
        # 異常系: git status を fake し transaction.cc の tracked 改変を注入
        source_digest.subprocess = types.SimpleNamespace(
            run=lambda *a, **k: types.SimpleNamespace(
                returncode=0, stdout=" M cc/silo/transaction.cc\n M include/backoff.hh\n"),
            SubprocessError=Exception)
        try:
            source_digest.assert_worktree_within_allowlist("/x")
            assert False, "allowlist 外改変で停止すべき"
        except RuntimeError:
            pass
        # 正常系: allowlist 内 + untracked (build 生成物) は無視
        source_digest.subprocess = types.SimpleNamespace(
            run=lambda *a, **k: types.SimpleNamespace(
                returncode=0,
                stdout=" M cmake/Options.cmake\n M include/backoff.hh\n?? build-variants/x\n"),
            SubprocessError=Exception)
        source_digest.assert_worktree_within_allowlist("/x")   # 例外なし = OK
    finally:
        source_digest.subprocess = saved


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
