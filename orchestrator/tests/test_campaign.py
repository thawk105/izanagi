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

from campaign import (buildcache, genome, ident, pin, pipeline,  # noqa: E402
                      source_digest, wal)
from campaign.layout import CampaignLayout, campaign_layout      # noqa: E402
from campaign.lock import BenchBusy, bench_lock                  # noqa: E402
from campaign.model import (CampaignConfig, Genome,              # noqa: E402
                            STAGE_BENCH_DONE, STAGE_BUILD_DONE, STAGE_BUILD_START,
                            STAGE_COMMIT, STAGE_ABORT, STAGE_VERIFY_DONE)
from campaign.pipeline import EvalResult, PerfConfig             # noqa: E402
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


def test_buildcache_clears_stale_build_dir(tmp_path):
    """kill 残骸 (CMakeCache あり・binary 無し) は configure 前に破棄される。

    残骸 CMakeCache の一時 worktree パス焼き付きが以後の configure を永続的に即死させた
    2026-07-11 s8a stock build-error の回帰固定。"""
    bdir = tmp_path / "silo_deadbeef00_t0"
    bdir.mkdir()
    (bdir / "CMakeCache.txt").write_text("CMAKE_HOME_DIRECTORY:INTERNAL=/tmp/gone_wt/wt\n")
    binary = str(bdir / "cc" / "silo" / "ycsb_silo.exe")
    buildcache._clear_stale_build_dir(str(bdir), binary)
    assert not bdir.exists()                 # 中途 dir は破棄される


def test_buildcache_stale_clear_spares_complete_and_absent(tmp_path):
    """binary が完成している dir は破棄しない (正当な成果物)。bdir 不在は no-op。"""
    bdir = tmp_path / "silo_cafebabe00_t1"
    binpath = bdir / "cc" / "silo" / "ycsb_silo.exe"
    binpath.parent.mkdir(parents=True)
    binpath.write_bytes(b"\x7fELF")
    buildcache._clear_stale_build_dir(str(bdir), str(binpath))
    assert binpath.exists()                  # 完成品は温存
    absent = tmp_path / "no_such_dir"
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
                   aborts=7, build_raises=False, high_variance=False,
                   unstable=False, competing=None, trace_timeout=False):
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

    def fake_build(genome, commit, trace, src_token=None, ccbench_dir="", cache_root=""):
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
    if trace_timeout:
        def _raise_timeout(*a, **k):
            raise subprocess.TimeoutExpired(cmd="trace",
                                            timeout=pipeline.TRACE_TIMEOUT_S)
        patch("_run_trace", _raise_timeout)
    else:
        patch("_run_trace", lambda *a, **k: (ncommit, rc, aborts))
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
def _mock_pipeline_multipass(pass_results, median=12345.0, cv=0.01, competing=None):
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
        return types.SimpleNamespace(bin_hash="dead" + ("t" if trace else "p"),
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

    patch("buildcache", types.SimpleNamespace(build=fake_build))
    patch("source_digest", types.SimpleNamespace(
        STOCK="stock", assert_worktree_within_allowlist=lambda *a, **k: None,
        src_token=lambda *a, **k: "stock", resolve=lambda *a, **k: "stock"))
    patch("_run_trace", fake_run_trace)
    patch("verify_trace_dir", fake_verify)
    patch("bench_lock", fake_lock)
    patch("settle", lambda *a, **k: {"settled": True})
    patch("competing_bench_pids", lambda: list(competing or []))
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
    sub = buildcache._ccbench_dir()
    with open(os.path.join(sub, "cmake/Options.cmake"), encoding="utf-8") as f:
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
    sub = buildcache._ccbench_dir()
    with open(os.path.join(sub, "include/backoff.hh"), encoding="utf-8") as f:
        src = f.read()
    if "BACKOFF_FIXED" not in src:
        skip("template patch 未適用 (backoff.hh に BACKOFF_FIXED 骨格なし) — 適用後のみ")
    try:
        source_digest._cpp_normalize(src, {"BACKOFF_NOINLINE": "0"}, "g++-13")  # FIXED 欠落
        assert False, "供給漏れで停止すべき (#error / -Werror=undef)"
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


def _fake_ccbench_repo():
    """(sub, head, git) — git は fake repo で任意コマンドを回すヘルパー。"""
    sub = _tmpdir("izanagi_fakecc_")
    os.makedirs(os.path.join(sub, "cmake"))
    os.makedirs(os.path.join(sub, "include"))
    os.makedirs(os.path.join(sub, "cc", "silo"))
    with open(os.path.join(sub, "cmake", "Options.cmake"), "w", encoding="utf-8") as f:
        f.write('set(CCBENCH_BACK_OFF 1 CACHE STRING "exponential backoff")\n')
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
