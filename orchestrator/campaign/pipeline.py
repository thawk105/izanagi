# -*- coding: utf-8 -*-
"""評価パイプライン状態機械 — build → verify → [bench] → commit (orchestrator-design.md A/I/D)。

Phase 1 の全コンポーネントを束ねる統合点:
  buildcache (trace/perf 別ビルド, 絶対規律1) → verifier (正しさゲート, 絶対規律2) →
  calibrator.runner (bench_lock 下で perf, I) → WAL commit (A)。

**A (atomicity):** 各段を WAL に先行書き込みし、全段通過した瞬間だけ commit。
verifier が非 certified を返したら **abort** (絶対規律2: 正しさを破る variant は失格、
fitness を付けない)。**I (isolation):** bench は bench_lock + settle で排他・静定。
**D:** WAL 追記で再起動時に再開可能。
"""
from __future__ import annotations

import hashlib
import os
import re
import shutil
import subprocess
import tempfile
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Sequence

import sys as _sys
_HERE = os.path.dirname(os.path.abspath(__file__))
_sys.path.insert(0, os.path.dirname(_HERE))   # orchestrator/ を import パスに

from calibrator.runner import (competing_bench_pids,            # noqa: E402
                               measure_point, settle)
from calibrator.stability import remeasure_until_stable         # noqa: E402
from verifier import result_to_dict, verify_trace_dir          # noqa: E402
from verifier.parse import ParseError                           # noqa: E402

from . import buildcache, source_digest, wal                   # noqa: E402
from .layout import CampaignLayout                              # noqa: E402
from .lock import bench_lock                                    # noqa: E402
from .model import (Genome, STAGE_ABORT, STAGE_BENCH_DONE,      # noqa: E402
                    STAGE_BUILD_DONE, STAGE_BUILD_START, STAGE_COMMIT,
                    STAGE_VERIFY_DONE)


def variant_id(genome: Genome, src_token: str = source_digest.STOCK) -> str:
    """genome 正準表現 + コード差 (src_token, D23) の安定ハッシュ = variant の id (WAL キー)。

    stock (working-tree==HEAD baseline) は src を省き旧 id を温存 (後方互換: silo 8 genome の
    既存 WAL キーが不変)。coder が EVOLVE-BLOCK を書き換えた variant だけ src 込みの新 id。"""
    src = "" if src_token == source_digest.STOCK else f"|src={src_token}"
    return hashlib.sha256(f"{genome.canonical()}{src}".encode("utf-8")).hexdigest()[:12]


@dataclass
class CorrectnessWorkload:
    """verify 用の小規模・高 contention workload (trace を verifier に回せる規模)。"""
    flags: Dict[str, str] = field(default_factory=lambda: {
        "ycsb_tuple_num": "200", "ycsb_zipf_skew": "0.9", "ycsb_rratio": "50",
        "ycsb_rmw": "true", "ycsb_max_ope": "5", "thread_num": "4", "extime": "1"})


@dataclass
class PerfConfig:
    """bench 用の確定 calibration (records/threads/workload)。"""
    records: int
    threads: int
    workload: Dict[str, str] = field(default_factory=dict)
    extime: int = 3
    reps: int = 5


@dataclass
class EvalResult:
    genome: Genome
    variant: str
    certified: bool
    aborted: bool
    fitness_tps: Optional[float] = None
    cv: Optional[float] = None
    unstable: bool = False           # 規定ラウンドでも CV が収束しなかった (§3.6(2))
    verdict: str = ""
    notes: List[str] = field(default_factory=list)


# ccbench 正常終了時の集計行 (common/result.cc displayAbortCounts、displayAllResult が
# 無条件に出す)。^ アンカー必須 — batch_abort_counts_ 行を誤マッチさせない。
_ABORT_COUNTS_RE = re.compile(r"(?m)^abort_counts_:\s*(\d+)\s*$")


def _parse_abort_counts(stdout: str) -> Optional[int]:
    """ccbench stdout から総 abort 数を読む。行が無ければ None (呼び手が fails-closed に倒す)。"""
    m = _ABORT_COUNTS_RE.search(stdout or "")
    return int(m.group(1)) if m else None


# trace run の timeout。S2 verify 構成の gate2 run timeout (120s) と同値に揃えてある
# (s2_verify_calibration.py)。abort payload (trace-timeout) にも記録する — 「どの上限で
# 打ち切られたか」が無いと liveness-red の次手入力が空になる (規律3)。
TRACE_TIMEOUT_S = 120.0


def _run_trace(binary: str, trace_dir: str, flags: Dict[str, str],
               clocks_per_us: int, timeout_s: float = TRACE_TIMEOUT_S):
    """trace-enabled binary を回し IZANAGI_TRACE_DIR に trace を吐く。

    返り値 `(ncommit, returncode, aborts)`。**呼び手は returncode を必ず検査する** —
    異常終了した run の部分トレースを certified にしないため (規律2)。aborts は stdout の
    `abort_counts_:` 集計 (完了条件「verify 中に合成枝 = abort-path が実行された証拠」の
    材料, phase3.md)。パース不能なら None — 呼び手が reject する (空振り認証の検査可能性を
    落としたまま緑を出さない)。"""
    args = [binary] + [f"-{k}={v}" for k, v in flags.items()] \
        + [f"-clocks_per_us={clocks_per_us}"]
    env = dict(os.environ, IZANAGI_TRACE_DIR=trace_dir)
    # WAL=1 の genome は cwd/log/log<thid> に log を書く (CCBench fileio.hh genLogFileName)。
    # log/ が無いと open 失敗で LibcError → uncaught → SIGABRT。cwd を trace_dir にし log/ を
    # 用意する (trace_dir は使い捨て → log も一緒に消える。trace 出力は IZANAGI_TRACE_DIR で別制御)。
    os.makedirs(os.path.join(trace_dir, "log"), exist_ok=True)
    proc = subprocess.run(args, env=env, capture_output=True, text=True,
                          timeout=timeout_s, cwd=trace_dir)
    n = 0
    if os.path.isdir(trace_dir):
        for fn in os.listdir(trace_dir):
            if fn.startswith("trace_") and fn.endswith(".log"):
                with open(os.path.join(trace_dir, fn)) as f:
                    n += sum(1 for line in f if line.startswith("C "))
    return n, proc.returncode, _parse_abort_counts(proc.stdout)


def evaluate(genome: Genome, layout: CampaignLayout, env_tag: str,
             ccbench_commit: str, perf: PerfConfig,
             clocks_per_us: int, numactl: Optional[Sequence[str]] = None,
             correctness: Optional[CorrectnessWorkload] = None,
             do_bench: bool = True, do_settle: bool = True,
             src_token: Optional[str] = None, log=print) -> EvalResult:
    """1 genome を評価し WAL に記録する。

    **正しさを確証できない variant は全て abort (fitness なし)** — verifier red だけで
    なく、ビルド失敗・trace 異常終了・空トレース・パース不能・bench 測定失敗も「採用
    しない」に倒す (規律2: certified を安売りしない / 空 DSG を緑と誤認させない)。
    abort も commit も terminal だが、abort は **fitness を付けず採用しない**。
    """
    correctness = correctness or CorrectnessWorkload()
    # identity (D23): coder のコード差まで覆う src_token を build 前に確定し、variant_id
    # (WAL キー) と build (cache_key) で共有する (TOCTOU 偽 hit を防ぐ)。loop は skip/abort
    # キーを同じ id に揃えるため src_token を確定済みで渡す (id 確定点の単一化, D24)。直接
    # caller (src_token=None) は自己計算し、identity を確定できない (allowlist 逸脱 /
    # preprocess 失敗 / git show 失敗) なら fails-closed で評価しない (best-effort skip を
    # identity 核に持ち込まない, 規律2)。
    if src_token is None:
        try:
            src_tok = source_digest.resolve(genome, ccbench_commit)
        except RuntimeError as e:
            v0 = variant_id(genome)        # stock id で abort を記録 (WAL キーを残す)
            wal.log(layout, v0, STAGE_BUILD_START, env_tag, {"genome": genome.canonical()})
            wal.log(layout, v0, STAGE_ABORT, env_tag,
                    {"reason": "identity-error", "error": str(e)})
            log(f"  [eval {v0}] abort: identity-error ({e})")
            r = EvalResult(genome=genome, variant=v0, certified=False, aborted=True)
            r.notes.append(f"source_digest 確定不能 → reject ({e})")
            return r
    else:
        src_tok = src_token
    v = variant_id(genome, src_tok)
    res = EvalResult(genome=genome, variant=v, certified=False, aborted=False)
    wal.log(layout, v, STAGE_BUILD_START, env_tag,
            {"genome": genome.canonical(), "src_token": src_tok})

    def _abort(reason: str, note: str, extra: Optional[Dict] = None) -> EvalResult:
        wal.log(layout, v, STAGE_ABORT, env_tag, {"reason": reason, **(extra or {})})
        res.aborted = True
        res.notes.append(note)
        log(f"  [eval {v}] abort: {reason}")
        return res

    # --- build (trace + perf 別ビルド, 絶対規律1)。ビルド失敗はこの variant 固有の
    #     失敗として abort 隔離 (campaign 全体を落とさず前進, overnight 耐性) ---
    try:
        tr = buildcache.build(genome, ccbench_commit, trace=True, src_token=src_tok)
        pf = buildcache.build(genome, ccbench_commit, trace=False, src_token=src_tok)
    except (RuntimeError, subprocess.SubprocessError) as e:
        return _abort("build-error", f"ビルド失敗 → reject ({e})")
    wal.log(layout, v, STAGE_BUILD_DONE, env_tag,
            {"trace_bin": tr.bin_hash, "perf_bin": pf.bin_hash,
             "trace_cached": tr.cached, "perf_cached": pf.cached,
             # fitness 計測に使う perf (trace-disabled) build の再現コマンド (規律1)。
             "perf_configure_cmd": pf.configure_cmd, "perf_build_cmd": pf.build_cmd})
    log(f"  [eval {v}] built trace={tr.bin_hash}{'(cache)' if tr.cached else ''} "
        f"perf={pf.bin_hash}{'(cache)' if pf.cached else ''}")

    # --- verify (正しさゲート, 絶対規律2) ---
    tdir = tempfile.mkdtemp(prefix="izanagi_eval_trace_")   # TMPDIR=/home 配下
    try:
        try:
            ncommit, rc, aborts = _run_trace(tr.binary, tdir, correctness.flags,
                                             clocks_per_us)
        except subprocess.TimeoutExpired:
            return _abort("trace-timeout", "trace 取得タイムアウト → reject",
                          {"timeout_s": TRACE_TIMEOUT_S})
        # 異常終了・空トレースは「正しさ未確定」。verifier に渡すと空 DSG が
        # serializable=True に化け false-green になる (規律2 違反) → 手前で reject。
        if rc != 0:
            return _abort("trace-run-nonzero-exit",
                          f"trace バイナリ異常終了 rc={rc} → reject",
                          {"rc": rc, "commits": ncommit})
        if ncommit == 0:
            # aborts も載せる: 「回っているが全 abort (commit 枯渇)」と「そもそも回って
            # いない」を WAL から区別する (sort 変異の主要失敗形態の分離, 規律3)。None の
            # まま記録可 — abort_counts_ 行が出る前に死んだ、の可視化 (判定順で ncommit==0
            # がこの検査より先に来るため None がありうる)。
            return _abort("trace-empty",
                          "空トレース (commit 0) → 検証不能 reject",
                          {"commits": 0, "aborts": aborts})
        if aborts is None:
            # abort 数は「合成枝 (abort-path) が verify 中に実行された証拠」(phase3.md
            # 完了条件 2 / 残存リスク = 空振り認証)。取れない run を certified にすると
            # その検査可能性ごと落ちる → fails-closed で reject (規律3: 計器の故障を沈黙させない)。
            return _abort("trace-no-abort-counts",
                          "ccbench stdout に abort_counts_ 集計が無い → 空振り認証を"
                          "検査できず reject", {"commits": ncommit})
        try:
            vr = verify_trace_dir(tdir)
        except ParseError as e:
            return _abort("trace-parse-error", f"trace パース不能 → reject ({e})")
        res.verdict = vr.verdict
        wal.log(layout, v, STAGE_VERIFY_DONE, env_tag,
                {"verdict": vr.verdict, "certified": vr.certified,
                 "commits": ncommit, "aborts": aborts,
                 "anomalies": len(vr.anomalies)})
        log(f"  [eval {v}] verify: {vr.verdict} ({ncommit} commits, {aborts} aborts, "
            f"{len(vr.anomalies)} anomalies)")
        if not vr.certified:
            # 正しさを破る/確証できない variant は即 reject。fitness を付けない (規律2)。
            # 規律3 (IDS の教訓): なぜ壊れたか (どの trx 間の・どの依存 ww/wr/rw で・どの版で
            # cycle ができたか + integrity) を構造化して abort payload に載せ、次手生成
            # (critic/planner) が読めるようにする (digest.load_rejections が読む経路)。Phase 2 は
            # 全緑で発火しないが、LLM が RED variant を出す Phase 3 でこれが load-bearing になる。
            vdict = result_to_dict(vr)
            vdict.pop("trace_dir", None)        # 使い捨て tmpdir = WAL に残す価値なし
            return _abort(vr.verdict, f"正しさゲート不通過 ({vr.verdict}) → reject",
                          {"verify": vdict})
        res.certified = True
    finally:
        shutil.rmtree(tdir, ignore_errors=True)

    if not do_bench:
        # 配線テストでベンチを省くとき: certified だけで commit (fitness なし)。
        wal.log(layout, v, STAGE_COMMIT, env_tag, {"fitness_tps": None,
                                                   "note": "no-bench"})
        return res

    # --- bench (排他 + 静定, I/Admission) ---
    # records は measure_point が -ycsb_tuple_num として渡す → workload に入れない
    # (入れると gflags last-wins で calibration の records を無言上書きする)。
    if "ycsb_tuple_num" in perf.workload:
        # assert だと python -O で消える。calibration の records を gflags last-wins で
        # 無言上書きする事故 (規律4 の動作点破壊) への唯一の防壁なので例外文にする。
        raise ValueError(
            "PerfConfig.workload に ycsb_tuple_num を入れない (records を上書きする)")

    def _measure():
        return measure_point(pf.binary, perf.records, perf.threads, clocks_per_us,
                             extime=perf.extime, reps=perf.reps,
                             workload=perf.workload, numactl=numactl)

    # 外れ値 → 自動再測定 (§3.6(2)): 反復内 CV が閾値超なら静定して測り直す。規定ラウンドで
    # 収束しなければ unstable。再測定の実走も全て bench_lock 下 = 単一テナント直列 (絶対規律4)。
    with bench_lock():
        # admission を fails-closed に (絶対規律4): bench_lock 取得直後・自分の bench 開始前に
        # 競合/孤児ベンチを pgrep で直接確認し、居たら**汚染計測を採用せず abort** する
        # (settle の load EMA は laggy なので一次ゲートはこの確定信号)。孤児は規律6 に従い
        # **自動 kill せず PID を表に出して停止** — 人間が処遇を判断する。driver の pre-flight が
        # campaign 冒頭で 1 回見るのに対し、ここは genome ごと = campaign 途中で湧いた競合も捕える。
        comp = competing_bench_pids()
        if comp:
            return _abort("bench-competing-tenant",
                          "競合 ccbench ベンチを検知 → 汚染計測を採用せず reject (規律4)",
                          {"competing": comp})
        settled = settle() if do_settle else None
        rem = remeasure_until_stable(_measure,
                                     settle_fn=settle if do_settle else None)
    pt, nf = rem.point, rem.nf
    if nf is None or nf.median is None:
        # 全 rep で throughput が取れず測定不能 → fitness 無しの COMMIT を書かない。
        # 半端な評価を terminal commit にして永久 skip させない (A: atomicity)。
        return _abort("bench-no-throughput", "bench 測定失敗 (throughput 無し) → reject",
                      {"tps": getattr(pt, "throughputs", None), "rounds": rem.rounds,
                       "rep_notes": getattr(pt, "notes", [])})
    if nf.cv is None:
        # 有効 rep が 1 点のみ (残りは rep 失敗) / 全 rep tps=0 だと CV が定義できず、
        # within-run 品質ゲート (P2-1) を通せない → fitness として採用しない (規律4)。
        # 旧実装はここを素通りし直後の log f-string の nf.cv*100 で TypeError →
        # 意図しない eval-exception abort (permanent skip) になっていた (洗練検査 MED)。
        return _abort("bench-cv-undefined",
                      f"CV 算出不能 (有効 rep {len(pt.throughputs)} 点) → reject",
                      {"tps": pt.throughputs, "rounds": rem.rounds,
                       "rep_notes": getattr(pt, "notes", [])})
    res.fitness_tps, res.cv, res.unstable = nf.median, nf.cv, rem.unstable
    wal.log(layout, v, STAGE_BENCH_DONE, env_tag,
            {"median_tps": nf.median, "cv": nf.cv,
             "high_variance": nf.high_variance, "unstable": rem.unstable,
             "rounds": rem.rounds, "cv_history": rem.cv_history,
             "tps": pt.throughputs,
             # admission: load が静定したか (settle の戻り)。fails-closed の一次ゲートは
             # competing_bench_pids だが、settled=False の測定は forensic に残す (規律4)。
             "settled": (settled.get("settled") if settled else None),
             # leading indicators (§3.5): fitness を設計選択に帰属させる材料。
             # critic が abort率/latency/cache/IPC を読んで次の genome 方向を出す。
             "leading_indicators": pt.leading_indicators(),
             # rep 単位の失敗記録 (1e2c01c, 規律3)。部分失敗 (例 2/5 rep timeout) は
             # fitness が残り rep の median で成立するため、ここに載せないと「なぜ標本が
             # 痩せたか」が WAL の機械可読経路から消える (洗練検査 MED)
             "rep_notes": getattr(pt, "notes", []),
             "run_cmd": pt.run_cmd})              # この測定点を再現する実行コマンド
    log(f"  [eval {v}] bench: median {nf.median:,.0f} tps (CV {nf.cv*100:.2f}%"
        f"{f', {rem.rounds}rounds' if rem.rounds > 1 else ''}"
        f"{' ⚠UNSTABLE' if rem.unstable else ''})")

    # --- commit (A: 全段通過した瞬間だけ) ---
    # unstable は規定ラウンドでも CV が収束しなかった印 = この 1 点を信用するな。正しさは
    # 通っているので reject はしないが、採否の分布比較から呼び手が除外する
    # (§3.6(4): 沈黙して 1 点を採用しない)。high_variance は採用ラウンド自体の騒がしさ。
    wal.log(layout, v, STAGE_COMMIT, env_tag,
            {"fitness_tps": nf.median, "cv": nf.cv,
             "high_variance": nf.high_variance, "unstable": rem.unstable})
    return res
