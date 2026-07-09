# -*- coding: utf-8 -*-
"""critic digest の単体テスト (machine 非依存・mock WAL)。

pytest でも 素の `python orchestrator/tests/test_critic.py` でも走る。
"""
from __future__ import annotations

import atexit
import os
import shutil
import sys
import tempfile

_HERE = os.path.dirname(os.path.abspath(__file__))
_ORCH = os.path.dirname(_HERE)
sys.path.insert(0, _ORCH)

from campaign import wal                                          # noqa: E402
from campaign.layout import CampaignLayout                        # noqa: E402
from campaign.model import (STAGE_ABORT, STAGE_BENCH_DONE,        # noqa: E402
                            STAGE_BUILD_START, STAGE_COMMIT, STAGE_VERIFY_DONE)
from critic.digest import (STOCK_SRC_TOKEN, LivenessRejection,    # noqa: E402
                           build_digest, load_liveness_rejections,
                           load_rejections, load_verify_abort_signals,
                           render_rejections, render_text)


def _tmp_layout():
    d = tempfile.mkdtemp(prefix="izanagi_critic_")
    atexit.register(shutil.rmtree, d, ignore_errors=True)
    return CampaignLayout(root=d).ensure()


def _write(lay, genome, committed=True, **li):
    wal.log(lay, genome, STAGE_BUILD_START, "test", {"genome": genome})
    wal.log(lay, genome, STAGE_BENCH_DONE, "test", {"leading_indicators": li})
    if committed:                                  # digest は committed のみ拾う
        wal.log(lay, genome, STAGE_COMMIT, "test", {"fitness_tps": li.get("throughput_tps")})


_G = "silo|BACK_OFF={b},NO_WAIT_LOCKING_IN_VALIDATION={l},NO_WAIT_OF_TICTOC={t},WAL={w}"


def test_load_sorts_by_throughput_and_marginal_back_off():
    lay = _tmp_layout()
    # BACK_OFF 0→1: throughput 半減・latency 倍・abort 不変 (= backoff は latency コスト)
    _write(lay, _G.format(b=0, l=1, t=0, w=0),
           throughput_tps=8_000_000, abort_rate=0.05, latency_ns=1000,
           llc_miss_rate=0.2, ipc=1.5)
    _write(lay, _G.format(b=1, l=1, t=0, w=0),
           throughput_tps=4_000_000, abort_rate=0.05, latency_ns=2000,
           llc_miss_rate=0.2, ipc=1.5)
    d = build_digest("balanced", {"ycsb_rratio": "50"}, lay)
    assert len(d.genomes) == 2
    assert d.fastest.flags["BACK_OFF"] == 0           # throughput 降順
    bo = next(e for e in d.axes if e.axis == "BACK_OFF")
    assert bo.means["throughput_tps"] == {"0": 8_000_000, "1": 4_000_000}
    assert abs(bo.rel_throughput - (-0.5)) < 1e-9     # 0→1 で -50%
    assert bo.means["abort_rate"]["0"] == bo.means["abort_rate"]["1"]  # abort 不変
    assert bo.means["latency_ns"] == {"0": 1000, "1": 2000}            # latency 倍


def test_no_wait_axis_is_categorical_LT():
    lay = _tmp_layout()
    _write(lay, _G.format(b=0, l=1, t=0, w=0),         # L = 即abort
           throughput_tps=2_700_000, abort_rate=0.40, latency_ns=500,
           llc_miss_rate=0.3, ipc=1.0)
    _write(lay, _G.format(b=0, l=0, t=1, w=0),         # T = retry
           throughput_tps=1_900_000, abort_rate=0.50, latency_ns=700,
           llc_miss_rate=0.3, ipc=0.9)
    d = build_digest("balanced", {}, lay)
    nw = next(e for e in d.axes if e.axis == "no_wait")
    assert set(nw.levels) == {"L", "T"}                # NWL=1→L / NWT=1→T に畳む
    assert nw.means["throughput_tps"]["L"] == 2_700_000
    assert nw.means["throughput_tps"]["T"] == 1_900_000
    assert nw.means["latency_ns"]["L"] == 500 and nw.means["latency_ns"]["T"] == 700


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
    d = build_digest("x", {}, lay)
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
    d = build_digest("x", {}, lay)
    assert len(d.genomes) == 1                   # 非 committed は不採用
    assert d.genomes[0].flags["BACK_OFF"] == 0


def test_render_text_has_axes_and_indicators():
    lay = _tmp_layout()
    _write(lay, _G.format(b=0, l=1, t=0, w=0), throughput_tps=8_000_000,
           abort_rate=0.05, latency_ns=1000, llc_miss_rate=0.2, ipc=1.5)
    txt = render_text([build_digest("read-heavy", {"ycsb_rratio": "95"}, lay)])
    assert "read-heavy" in txt
    assert "BACK_OFF" in txt and "no_wait" in txt and "WAL" in txt
    assert "throughput_tps" in txt and "abort_rate" in txt
    assert "限界効果" in txt


def test_load_rejections_surfaces_structured_anomaly():
    """S4 (規律3 配線): load_rejections が verify-red の構造化 anomaly を次手入力として拾い、
    verify を持たない abort (build-error 等) は除外する。`load_workload` (緑) と対をなす。"""
    lay = _tmp_layout()
    red = _G.format(b=1, l=1, t=0, w=0)
    builderr = _G.format(b=0, l=1, t=0, w=0)
    # verify-red の variant (pipeline が書く形 = abort payload に verify 構造)
    wal.log(lay, red, STAGE_BUILD_START, "test", {"genome": red, "src_token": "codediff1"})
    wal.log(lay, red, STAGE_ABORT, "test",
            {"reason": "non-serializable",
             "verify": {"verdict": "non-serializable", "anomaly_count": 1,
                        "anomalies": [{"phenomenon": "G2", "cycle": [1, 2],
                                       "edges": [{"from": 1, "to": 2, "types": ["rw"],
                                                  "reasons": [{"type": "rw", "key": "aa"}]}]}],
                        "integrity": {"clean": True}}})
    # verify を持たない abort (build-error) は規律3 の次手入力ではない → 除外
    wal.log(lay, builderr, STAGE_BUILD_START, "test", {"genome": builderr})
    wal.log(lay, builderr, STAGE_ABORT, "test", {"reason": "build-error"})

    rej = load_rejections(lay)
    assert len(rej) == 1                          # build-error は除外
    assert rej[0].genome == red
    assert rej[0].flags["BACK_OFF"] == 1          # genome flags まで復元
    assert rej[0].verdict == "non-serializable"
    assert rej[0].anomalies[0]["phenomenon"] == "G2"
    assert rej[0].anomalies[0]["edges"][0]["reasons"][0]["key"] == "aa"
    assert rej[0].integrity == {"clean": True}
    # コード軸の識別 (D23): 同 canonical 別コードの RED variant が alias しないよう
    # WAL キーと src_token も次手入力に載る
    assert rej[0].variant == red
    assert rej[0].src_token == "codediff1"


def test_load_liveness_rejections_surfaces_reason_and_extra():
    """S4 consumer (規律3): liveness-red (verify 前に死んだ) が構造化されて次手入力に
    届き、infra 系 (build-error/eval-exception 等) は詳細でなく正規化 reason の件数に
    集約される (詳細は返さないが沈黙もさせない)。verify-red は混ざらない。"""
    lay = _tmp_layout()
    to = _G.format(b=1, l=1, t=0, w=0)
    wal.log(lay, to, STAGE_BUILD_START, "test", {"genome": to, "src_token": "codediff9"})
    wal.log(lay, to, STAGE_ABORT, "test", {"reason": "trace-timeout", "timeout_s": 120.0})
    te = _G.format(b=0, l=1, t=0, w=0)
    wal.log(lay, te, STAGE_BUILD_START, "test", {"genome": te})
    wal.log(lay, te, STAGE_ABORT, "test",
            {"reason": "trace-empty", "commits": 0, "aborts": 4321})
    b1 = _G.format(b=0, l=0, t=1, w=0)
    wal.log(lay, b1, STAGE_BUILD_START, "test", {"genome": b1})
    wal.log(lay, b1, STAGE_ABORT, "test", {"reason": "build-error"})
    b2 = _G.format(b=1, l=0, t=1, w=0)
    wal.log(lay, b2, STAGE_BUILD_START, "test", {"genome": b2})
    wal.log(lay, b2, STAGE_ABORT, "test",
            {"reason": "eval-exception: TypeError: boom"})   # 動的部は正規化で畳む
    vr = _G.format(b=1, l=1, t=0, w=1)
    wal.log(lay, vr, STAGE_BUILD_START, "test", {"genome": vr})
    wal.log(lay, vr, STAGE_ABORT, "test",
            {"reason": "non-serializable",
             "verify": {"verdict": "non-serializable"}})

    lrs, other = load_liveness_rejections(lay)
    assert {l.reason for l in lrs} == {"trace-timeout", "trace-empty"}
    lto = next(l for l in lrs if l.reason == "trace-timeout")
    assert lto.extra.get("timeout_s") == 120.0
    assert lto.variant == to and lto.src_token == "codediff9"
    assert lto.flags["BACK_OFF"] == 1
    lte = next(l for l in lrs if l.reason == "trace-empty")
    assert lte.extra.get("commits") == 0 and lte.extra.get("aborts") == 4321
    assert other == {"build-error": 1, "eval-exception": 1}


def test_rejection_types_keep_forward_workload_tag():
    """D36 決定 4 (段 5 配線予定) への前方寛容: abort payload に workload タグが来たら
    verify-red / liveness-red の両型が生値で保持する (形の確定は D36 実装時)。"""
    lay = _tmp_layout()
    red = _G.format(b=1, l=1, t=0, w=0)
    wal.log(lay, red, STAGE_BUILD_START, "test", {"genome": red})
    wal.log(lay, red, STAGE_ABORT, "test",
            {"reason": "non-serializable", "workload": {"tag": "s2"},
             "verify": {"verdict": "non-serializable", "anomalies": [],
                        "integrity": {}}})
    lv = _G.format(b=0, l=1, t=0, w=0)
    wal.log(lay, lv, STAGE_BUILD_START, "test", {"genome": lv})
    wal.log(lay, lv, STAGE_ABORT, "test",
            {"reason": "trace-timeout", "workload": {"tag": "s2"}})
    rej = load_rejections(lay)
    lrs, _ = load_liveness_rejections(lay)
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
    wal.log(lay, red, STAGE_BUILD_START, "test", {"genome": red, "src_token": "cd1"})
    wal.log(lay, red, STAGE_ABORT, "test",
            {"reason": "non-serializable",
             "verify": _red_verify_payload(total_cycles=57)})
    out = render_rejections(load_rejections(lay), [], {}, None)
    assert "cycle 全数 57 / witness 1 件" in out
    assert "抜粋" in out                                # 切り詰めの明示
    assert "T1 → T2" in out and "rw key=aa" in out      # どの依存を断つかが読める


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
    wal.log(lay, red, STAGE_BUILD_START, "test", {"genome": red, "src_token": "cd1"})
    wal.log(lay, red, STAGE_ABORT, "test",
            {"reason": "non-serializable", "verify": _red_verify_payload()})
    lrs = [LivenessRejection(genome=red, flags={}, reason="trace-timeout",
                             extra={"timeout_s": 120.0}, variant="v1")]
    stock = _G.format(b=0, l=1, t=0, w=0)
    wal.log(lay, stock, STAGE_BUILD_START, "test",
            {"genome": stock, "src_token": STOCK_SRC_TOKEN})
    wal.log(lay, stock, STAGE_VERIFY_DONE, "test",
            {"verdict": "serializable", "commits": 900, "aborts": 100})
    out = render_rejections(load_rejections(lay), lrs, {"build-error": 1},
                            load_verify_abort_signals(lay))
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
    wal.log(lay, v, STAGE_BUILD_START, "test", {"genome": v, "src_token": "cdI"})
    wal.log(lay, v, STAGE_ABORT, "test",
            {"reason": "indeterminate",
             "verify": _indeterminate_verify_payload(
                 txns=97, missing=3,
                 notes=["missing txids sample: [7, 8, 9]"])})
    rej = load_rejections(lay)
    assert len(rej) == 1 and rej[0].verdict == "indeterminate"
    assert rej[0].integrity["missing_txids"] == 3
    out = render_rejections(rej, [], {}, None)
    assert "missing_txids" in out                    # どのカウンタが非ゼロか
    assert "missing txids sample" in out             # notes (欠番の見本) が届く
    assert "cycle 全数" not in out                   # cycle 型の描画をしない (区別)


def test_empty_dsg_rejection_renders_explicitly():
    """J8-B 形状 (ii): integrity 全クリーンでも txns=0 (空 DSG) の indeterminate は
    「trace が空」を明示する — 7 カウンタ全ゼロの空パネルとして沈黙しない
    (実 run では trace-empty が手前で先取るが、verifier 単体経路では到達する形)。"""
    lay = _tmp_layout()
    v = _G.format(b=0, l=1, t=0, w=0)
    wal.log(lay, v, STAGE_BUILD_START, "test", {"genome": v, "src_token": "cdE"})
    wal.log(lay, v, STAGE_ABORT, "test",
            {"reason": "indeterminate",
             "verify": _indeterminate_verify_payload(txns=0, clean=True)})
    out = render_rejections(load_rejections(lay), [], {}, None)
    assert "trace が空 (txns=0)" in out
    assert "緑ではない" in out                       # クリーンでも certify しない旨


def test_verify_abort_signal_stock_contrast():
    """J1 シグナル: verify run の abort 率を stock 対照比つきで表示 (閾値判定なし)。"""
    lay = _tmp_layout()
    stock = _G.format(b=0, l=1, t=0, w=0)
    wal.log(lay, stock, STAGE_BUILD_START, "test",
            {"genome": stock, "src_token": STOCK_SRC_TOKEN})
    wal.log(lay, stock, STAGE_VERIFY_DONE, "test",
            {"verdict": "serializable", "commits": 900, "aborts": 100})
    var = _G.format(b=1, l=1, t=0, w=0)
    wal.log(lay, var, STAGE_BUILD_START, "test", {"genome": var, "src_token": "cd2"})
    wal.log(lay, var, STAGE_VERIFY_DONE, "test",
            {"verdict": "serializable", "commits": 600, "aborts": 400})
    out = render_rejections([], [], {}, load_verify_abort_signals(lay))
    assert "rate=10.00%" in out                       # stock 100/1000
    assert "rate=40.00%" in out and "stock 比 4.0×" in out


def test_verify_abort_signal_no_stock_and_legacy_are_explicit():
    """規律3 (沈黙禁止): stock 対照不在・旧形式 WAL (aborts 記録なし)・未発火の
    3 形は明示表示 (欠落を無言で流さない)。"""
    lay = _tmp_layout()
    var = _G.format(b=1, l=1, t=0, w=0)
    wal.log(lay, var, STAGE_BUILD_START, "test", {"genome": var, "src_token": "cd3"})
    wal.log(lay, var, STAGE_VERIFY_DONE, "test",
            {"verdict": "serializable", "commits": 500})     # aborts 無し = 旧形式
    out = render_rejections([], [], {}, load_verify_abort_signals(lay))
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
    wal.log(lay, stock, STAGE_BUILD_START, "test",
            {"genome": stock, "src_token": STOCK_SRC_TOKEN})
    wal.log(lay, stock, STAGE_VERIFY_DONE, "test",
            {"verdict": "serializable", "commits": 900, "aborts": 100,
             "workload": {"tag": "legacy"}})
    wal.log(lay, stock, STAGE_VERIFY_DONE, "test",
            {"verdict": "serializable", "commits": 1_500_000, "aborts": 500_000,
             "workload": {"tag": "s2"}})
    out = load_verify_abort_signals(lay)
    assert len(out) == 1
    assert out[0].commits == 900 and out[0].aborts == 100  # S2 (2 件目) でなく legacy を採用


def test_stock_token_matches_source_digest():
    """STOCK_SRC_TOKEN のローカル定数が source_digest.STOCK から drift しない。"""
    from campaign import source_digest
    assert STOCK_SRC_TOKEN == source_digest.STOCK


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
