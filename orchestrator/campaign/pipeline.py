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
import time
from dataclasses import dataclass, field
from typing import Callable, Dict, List, Optional, Sequence, Tuple

import sys as _sys
_HERE = os.path.dirname(os.path.abspath(__file__))
_sys.path.insert(0, os.path.dirname(_HERE))   # orchestrator/ を import パスに

from calibrator.runner import (CompetingBenchProbeError,        # noqa: E402
                               competing_bench_pids, measure_point, settle)
from calibrator.stability import remeasure_until_stable         # noqa: E402
from verifier import result_to_dict, verify_trace_dir          # noqa: E402
from verifier.parse import ParseError                           # noqa: E402

from . import buildcache, env_contract as _env_contract, ident, source_digest, wal  # noqa: E402
from .layout import CampaignLayout                              # noqa: E402
from .lock import bench_lock                                    # noqa: E402
from .env_contract import ExecutionEnvironmentContract          # noqa: E402
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


# --- S2 verify 構成 (D36 決定1/決定3: perf 代表 workload と完全同一、extime=3 で
# gate 3 点 all_pass — 正本 output/env/linux-baremetal/calibration/
# s2_verify_t48_skew0p9_rr50_rmw0.json)。s2_verify_calibration.py もこの定数を
# import する (二重定義によるドリフト防止)。 ---
S2_FLAGS: Dict[str, str] = {
    "ycsb_tuple_num": "1000000", "ycsb_zipf_skew": "0.9", "ycsb_rratio": "50",
    "ycsb_rmw": "false", "ycsb_max_ope": "10", "thread_num": "48",
}
S2_EXTIME = "3"
LEGACY_TAG = "legacy"
S2_TAG = "s2"
# CampaignConfig.search_config のキー (D36 決定4-1): S2 on/off はここに焼き込み
# campaign_id に反映する (別 campaign になり WAL terminal skip の汚染を防ぐ)。
SEARCH_CONFIG_VERIFY_KEY = "verify"
VERIFY_LEGACY_PLUS_S2 = f"{LEGACY_TAG}+{S2_TAG}"
# bench-first screening の terminal abort reason。WAL writer/reader が共有する暗黙 API。
SCREEN_REJECTION_REASON = "screen-slower-than-floor"


def s2_correctness_workload() -> CorrectnessWorkload:
    """S2 verify 構成 (D36 決定3 gate all_pass の確定値)。evaluate() の
    extra_correctness に渡す (search_config[SEARCH_CONFIG_VERIFY_KEY] ==
    VERIFY_LEGACY_PLUS_S2 のとき、loop.run_campaign が組み立てる)。"""
    return CorrectnessWorkload(flags={**S2_FLAGS, "extime": S2_EXTIME})


@dataclass
class PerfConfig:
    """bench 用の確定 calibration (records/threads/workload)。"""
    records: int
    threads: int
    workload: Dict[str, str] = field(default_factory=dict)
    extime: int = 3
    reps: int = 5


_QUALIFICATION_POLICY_TOKEN = object()


@dataclass(frozen=True, init=False)
class QualificationPipelinePolicy:
    """Exact T-126 opt-in for the shared evaluation seam.

    This separates full-scale isolation from the launch prefix, supplies
    bounded subprocess timeouts, and routes events to a qualification-only
    sink.  It grants no formal authority.
    """

    event_sink: object
    member_cap_s: int
    build_timeout_s: int
    bench_timeout_s: float
    require_settled: bool

    def __init__(self, *, _token: object, event_sink: object):
        if _token is not _QUALIFICATION_POLICY_TOKEN:
            raise TypeError("use QualificationPipelinePolicy.t126_pegasus()")
        from qualification.artifacts import QualificationEventSink
        if type(event_sink) is not QualificationEventSink:
            raise TypeError(
                "qualification event_sink must be exact QualificationEventSink")
        event_sink.assert_pipeline_binding(event_sink.layout)
        object.__setattr__(self, "event_sink", event_sink)
        object.__setattr__(self, "member_cap_s", 900)
        object.__setattr__(self, "build_timeout_s", 900)
        object.__setattr__(self, "bench_timeout_s", 120.0)
        object.__setattr__(self, "require_settled", True)

    @classmethod
    def t126_pegasus(cls, event_sink: object) -> "QualificationPipelinePolicy":
        return cls(_token=_QUALIFICATION_POLICY_TOKEN, event_sink=event_sink)


@dataclass(frozen=True, kw_only=True)
class ScreeningConfig:
    """bench-first screening の固定方針と、driver が再アンカーする基準点。"""
    baseline_tps: float
    baseline_ref: str
    baseline_measured_at: float
    floor: float
    k: float = 1.5
    baseline_abort_rate: float
    high_abort_factor: float = 2.0
    reanchor_threshold_s: float = 1800.0

    def __post_init__(self) -> None:
        checks = (
            (self.k >= 1.5, "k は 1.5 以上でなければならない"),
            (self.baseline_tps > 0, "baseline_tps は正でなければならない"),
            (0 < self.floor < 1, "floor は 0 より大きく 1 未満でなければならない"),
            (self.baseline_abort_rate >= 0,
             "baseline_abort_rate は 0 以上でなければならない"),
            (self.high_abort_factor >= 1.0,
             "high_abort_factor は 1.0 以上でなければならない"),
            (self.reanchor_threshold_s > 0,
             "reanchor_threshold_s は正でなければならない"),
        )
        for valid, message in checks:
            if not valid:
                raise ValueError(message)


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


def _exc_summary(e: BaseException, limit: int = 1000) -> str:
    """例外由来 abort の WAL payload に載せる要約 (D50 教訓: reason だけの WAL では
    build-error の現地調査を一次資料から始められず、kill 残骸毒の特定が遅延した)。
    ビルドログ等の長い出力は本命 (error: 行) が末尾に出やすいので末尾優先で畳む。
    limit は 200 超が前提 (先頭 200 + 末尾 limit-200 の算術が退化する。既定 1000 のみで使用)。"""
    s = f"{type(e).__name__}: {e}"
    if len(s) <= limit:
        return s
    return s[:200] + " …[中略]… " + s[-(limit - 200):]


def _run_trace(binary: str, trace_dir: str, flags: Dict[str, str],
               clocks_per_us: int, timeout_s: float = TRACE_TIMEOUT_S,
               numactl: Optional[Sequence[str]] = None):
    """trace-enabled binary を回し IZANAGI_TRACE_DIR に trace を吐く。

    返り値 `(ncommit, returncode, aborts)`。**呼び手は returncode を必ず検査する** —
    異常終了した run の部分トレースを certified にしないため (規律2)。aborts は stdout の
    `abort_counts_:` 集計 (完了条件「verify 中に合成枝 = abort-path が実行された証拠」の
    材料, phase3.md)。パース不能なら None — 呼び手が reject する (空振り認証の検査可能性を
    落としたまま緑を出さない)。numactl (D36 決定4-4): S2 相当の全規模 run はメモリ配置を
    bench と揃える (既定 legacy はメモリ配置に鈍感な小規模ゆえ None のまま)。"""
    args = (list(numactl) if numactl else []) + [binary] \
        + [f"-{k}={v}" for k, v in flags.items()] \
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


@dataclass(frozen=True)
class _BenchResult:
    """bench 成功時に COMMIT 判定へ渡す、既測値の最小集合。"""
    median_tps: float
    cv: float
    high_variance: bool
    unstable: bool
    leading_indicators: Dict


@dataclass(frozen=True)
class _BenchRound:
    """1 回の measure_point と、その rep 実行順 return code の対応。"""
    point: object
    rep_returncodes: List[int]


def _run_bench(perf_binary: str, perf: PerfConfig, clocks_per_us: int,
               numactl: Optional[Sequence[str]], do_settle: bool,
               layout: CampaignLayout, variant: str, env_tag: str,
               abort: Callable[[str, str, Optional[Dict]], EvalResult],
               log=print, screening: bool = False,
               bench_payload_extra: Optional[Dict] = None,
               bench_max_rounds: int = 3,
               record_rep_returncodes: bool = False,
               bench_timeout_s: Optional[float] = None,
               require_all_reps: bool = False,
               require_settled: bool = False,
               emit: Optional[Callable[[object, str, str, str, Dict], None]] = None,
               ) -> Tuple[Optional[EvalResult], Optional[_BenchResult]]:
    """現行の full bench を実行し、成功時は WAL に既測値を残す。"""
    # records は measure_point が -ycsb_tuple_num として渡す → workload に入れない
    # (入れると gflags last-wins で calibration の records を無言上書きする)。
    if "ycsb_tuple_num" in perf.workload:
        # assert だと python -O で消える。calibration の records を gflags last-wins で
        # 無言上書きする事故 (規律4 の動作点破壊) への唯一の防壁なので例外文にする。
        raise ValueError(
            "PerfConfig.workload に ycsb_tuple_num を入れない (records を上書きする)")

    # IZANAGI_TRACE_DIR を perf run にも対称に設定する (D36 決定4-5): verify run だけが
    # この環境変数を持つと、EVOLVE_BLOCK の共有コード (#if TRACE の外) が getenv 有無で
    # verify/perf を判別する経路になりうる (auditor.md 型3 の判別述語)。perf build は
    # TRACE がコンパイルアウトされ実際には未使用だが、変数の「有無」自体を判別子に
    # できなくする (値の中身までは踏み込まない — 残りは auditor の静的検査が担う)。
    dummy_tdir = tempfile.mkdtemp(prefix="izanagi_eval_notrace_")

    measured_rounds: List[_BenchRound] = []

    def _measure():
        qualification_kwargs = {}
        if bench_timeout_s is not None:
            qualification_kwargs["timeout_s"] = bench_timeout_s
        if require_all_reps:
            qualification_kwargs["require_all_reps"] = True
        if not record_rep_returncodes:
            return measure_point(
                perf_binary, perf.records, perf.threads, clocks_per_us,
                extime=perf.extime, reps=perf.reps,
                workload=perf.workload, numactl=numactl,
                extra_env={"IZANAGI_TRACE_DIR": dummy_tdir},
                **qualification_kwargs,
            )
        rep_returncodes: List[int] = []
        point = measure_point(
            perf_binary, perf.records, perf.threads, clocks_per_us,
            extime=perf.extime, reps=perf.reps,
            workload=perf.workload, numactl=numactl,
            extra_env={"IZANAGI_TRACE_DIR": dummy_tdir},
            rep_returncodes=rep_returncodes,
            **qualification_kwargs,
        )
        measured_rounds.append(_BenchRound(
            point=point, rep_returncodes=rep_returncodes,
        ))
        return point

    bench_wall_s = 0.0
    try:
        # 外れ値 → 自動再測定 (§3.6(2)): 反復内 CV が閾値超なら静定して測り直す。規定
        # ラウンドで収束しなければ unstable。再測定の実走も全て bench_lock 下 = 単一
        # テナント直列 (絶対規律4)。
        with bench_lock():
            # admission を fails-closed に (絶対規律4): bench_lock 取得直後・自分の bench
            # 開始前に競合/孤児ベンチを pgrep で直接確認し、居たら**汚染計測を採用せず
            # abort** する (settle の load EMA は laggy なので一次ゲートはこの確定信号)。
            # 孤児は規律6 に従い**自動 kill せず PID を表に出して停止** — 人間が処遇を
            # 判断する。driver の pre-flight が campaign 冒頭で 1 回見るのに対し、ここは
            # genome ごと = campaign 途中で湧いた競合も捕える。
            try:
                comp = competing_bench_pids()
            except CompetingBenchProbeError as e:
                # probe (pgrep) の実行自体が失敗 → 競合の有無を確定できない。握りつぶさず
                # 専用 reason で abort し、故障詳細を WAL payload に構造化して残す (規律3/4,
                # B-6)。この reason は transient infra 失敗として retryable 扱いされる (B-3)。
                return abort("bench-probe-error",
                             "競合検知 probe (pgrep) 実行失敗 → 競合の有無を確定できず "
                             "reject (環境故障・再評価可能, 規律3/4)",
                             {"probe_error": e.as_dict(),
                              "bench_wall_s": bench_wall_s}), None
            if comp:
                return abort("bench-competing-tenant",
                             "競合 ccbench ベンチを検知 → 汚染計測を採用せず reject (規律4)",
                             {"competing": comp, "bench_wall_s": bench_wall_s}), None
            settled = settle() if do_settle else None
            bench_started = time.monotonic()
            try:
                rem = remeasure_until_stable(_measure,
                                             settle_fn=settle if do_settle else None,
                                             max_rounds=bench_max_rounds)
            finally:
                bench_wall_s = float(max(0.0, time.monotonic() - bench_started))
    finally:
        shutil.rmtree(dummy_tdir, ignore_errors=True)
    pt, nf = rem.point, rem.nf
    if require_settled and (not settled or settled.get("settled") is not True):
        return abort(
            "bench-unsettled",
            "qualification bench did not reach settled=true → reject",
            {"settled": (settled.get("settled") if settled else None),
             "rounds": rem.rounds, "bench_wall_s": bench_wall_s},
        ), None
    selected_returncodes: Optional[List[int]] = None
    if record_rep_returncodes:
        selected_rounds = [item for item in measured_rounds if rem.point is item.point]
        if len(selected_rounds) != 1:
            return abort(
                "bench-returncodes-round-unbound",
                "採用 bench round と rep return code の対応が一意でない → reject",
                {"matching_rounds": len(selected_rounds),
                 "measured_rounds": len(measured_rounds),
                 "bench_wall_s": bench_wall_s},
            ), None
        selected_returncodes = list(selected_rounds[0].rep_returncodes)
    if nf is None or nf.median is None:
        # 全 rep で throughput が取れず測定不能 → fitness 無しの COMMIT を書かない。
        # 半端な評価を terminal commit にして永久 skip させない (A: atomicity)。
        return abort("bench-no-throughput", "bench 測定失敗 (throughput 無し) → reject",
                     {"tps": getattr(pt, "throughputs", None), "rounds": rem.rounds,
                      "rep_notes": getattr(pt, "notes", []),
                      "bench_wall_s": bench_wall_s}), None
    if nf.cv is None:
        # 有効 rep が 1 点のみ (残りは rep 失敗) / 全 rep tps=0 だと CV が定義できず、
        # within-run 品質ゲート (P2-1) を通せない → fitness として採用しない (規律4)。
        # 旧実装はここを素通りし直後の log f-string の nf.cv*100 で TypeError →
        # 意図しない eval-exception abort (permanent skip) になっていた (洗練検査 MED)。
        return abort("bench-cv-undefined",
                     f"CV 算出不能 (有効 rep {len(pt.throughputs)} 点) → reject",
                     {"tps": pt.throughputs, "rounds": rem.rounds,
                      "rep_notes": getattr(pt, "notes", []),
                      "bench_wall_s": bench_wall_s}), None
    leading_indicators = pt.leading_indicators()
    bench_payload = {
        "median_tps": nf.median, "cv": nf.cv,
        "bench_wall_s": bench_wall_s,
        "high_variance": nf.high_variance, "unstable": rem.unstable,
        "rounds": rem.rounds, "cv_history": rem.cv_history,
        "tps": pt.throughputs,
        # admission: load が静定したか (settle の戻り)。fails-closed の一次ゲートは
        # competing_bench_pids だが、settled=False の測定は forensic に残す (規律4)。
        "settled": (settled.get("settled") if settled else None),
        # leading indicators (§3.5): fitness を設計選択に帰属させる材料。
        # critic が abort率/latency/cache/IPC を読んで次の genome 方向を出す。
        "leading_indicators": leading_indicators,
        # rep 単位の失敗記録 (1e2c01c, 規律3)。部分失敗 (例 2/5 rep timeout) は
        # fitness が残り rep の median で成立するため、ここに載せないと「なぜ標本が
        # 痩せたか」が WAL の機械可読経路から消える (洗練検査 MED)
        "rep_notes": getattr(pt, "notes", []),
        "run_cmd": pt.run_cmd,                    # この測定点を再現する実行コマンド
    }
    if screening:
        bench_payload["screening"] = True
    if selected_returncodes is not None:
        bench_payload["rep_returncodes"] = selected_returncodes
    if bench_payload_extra:
        bench_payload.update(bench_payload_extra)
    (emit or wal.log)(layout, variant, STAGE_BENCH_DONE, env_tag, bench_payload)
    log(f"  [eval {variant}] bench: median {nf.median:,.0f} tps (CV {nf.cv*100:.2f}%"
        f"{f', {rem.rounds}rounds' if rem.rounds > 1 else ''}"
        f"{' ⚠UNSTABLE' if rem.unstable else ''})")
    return None, _BenchResult(
        median_tps=nf.median, cv=nf.cv, high_variance=nf.high_variance,
        unstable=rem.unstable, leading_indicators=leading_indicators)


def evaluate(genome: Genome, layout: CampaignLayout, env_tag: str,
             ccbench_commit: str, perf: PerfConfig,
             clocks_per_us: int, numactl: Optional[Sequence[str]] = None,
             correctness: Optional[CorrectnessWorkload] = None,
             extra_correctness: Optional[Sequence[Tuple[str, CorrectnessWorkload]]] = None,
             do_bench: bool = True, do_settle: bool = True,
             src_token: Optional[str] = None, log=print,
             ccbench_dir: str = "", cache_root: str = "",
             screening: Optional[ScreeningConfig] = None,
             bench_max_rounds: int = 3,
             expected_perf_sha256: Optional[str] = None,
             env_contract: Optional[ExecutionEnvironmentContract] = None,
             record_rep_returncodes: bool = False,
             qualification_policy: Optional[QualificationPipelinePolicy] = None) -> EvalResult:
    """1 genome を評価し WAL に記録する。

    `ccbench_dir`/`cache_root` (段5 git worktree 隔離): 省略時は共有固定パス既定 (既存動作と
    完全互換)。呼び手が `patchharness.isolated()` で作った worktree を `ccbench_dir` に渡すと
    ソースはその worktree から読み、`cache_root` を固定パス配下に据え置けばビルドキャッシュは
    campaign 非依存のまま共有される (worktree 間で内容キーが揃う)。campaign-id には含めない
    (ビルド結果に影響しない実装詳細 — numactl/do_bench と同じ実行時引数の扱い)。
    `bench_max_rounds` も同じ runtime-only 軸で campaign-id には含めない。既定 3 は従来の
    `remeasure_until_stable` 既定と同一で、事前登録が 1 measure_point に固定した driver
    だけ 1 を明示する。

    **正しさを確証できない variant は全て abort (fitness なし)** — verifier red だけで
    なく、ビルド失敗・trace 異常終了・空トレース・パース不能・bench 測定失敗も「採用
    しない」に倒す (規律2: certified を安売りしない / 空 DSG を緑と誤認させない)。
    abort も commit も terminal だが、abort は **fitness を付けず採用しない**。

    `expected_perf_sha256` (A-1, exact 64 lowercase hex): 指定時のみ、両ビルド完了直後・
    trace/bench 起動前に perf バイナリの full sha256 を厳密照合し、不一致 (期待値の形不正・
    照合不能を含む) は trace/bench を一切起動せず `bench-binary-mismatch` で abort する。
    期待値の供給元は freeze v2 で配線するため今回はデフォルト None のまま (未配線=従来同一)。

    `env_contract` は v2 consumer 専用の opt-in。指定時だけ contract namespace の
    `build_v2` を使い、未指定 caller (p3 loop を含む) は legacy build の呼出し形も
    namespace も不変に保つ。

    `record_rep_returncodes` も既定 False の opt-in。True の official oracle 経路だけ、
    採用した再測定 round と identity で一意に対応する rep rc を bench_done に残す。

    `screening` (D58) を指定したときだけ full bench を verify より前へ移し、明白な
    劣位点を uncertified のまま棄却する。COMMIT は従来どおり全 verify 構成通過後だけ。

    `extra_correctness` (D36 決定4): (tag, workload) の列。既定 correctness (tag
    LEGACY_TAG) に加え指定された構成を**全て**通した variant だけ certified にする
    (verify 2 本立て、既存 CorrectnessWorkload は置き換えず併存、決定2)。各構成は
    WAL に "workload":{"tag":...} で残り、次手生成 (critic) がどの構成で壊れたか
    帰属できる (決定4-3)。S2 相当 (t48 フルロード規模) は bench 並みの負荷ゆえ
    bench_lock + numactl 下で回す (決定4-4)。既定 legacy は軽量ゆえ従来どおり
    並列可 (lock.py の設計方針)。"""
    if (isinstance(bench_max_rounds, bool) or not isinstance(bench_max_rounds, int)
            or bench_max_rounds < 1):
        raise ValueError("bench_max_rounds は 1 以上の整数でなければならない")
    if qualification_policy is not None:
        if type(qualification_policy) is not QualificationPipelinePolicy:
            raise TypeError("qualification_policy は exact QualificationPipelinePolicy が必要")
        expected_contract = _env_contract.lookup("pegasus")
        qualification_policy.event_sink.assert_pipeline_binding(layout)
        if env_contract != expected_contract:
            raise ValueError("qualification opt-in requires the exact registered Pegasus contract")
        if (env_tag != expected_contract.env_tag
                or clocks_per_us != expected_contract.clocks_per_us
                or type(numactl) is not tuple
                or numactl != expected_contract.numactl):
            raise ValueError("qualification execution values do not exactly match Pegasus contract")
        if (perf.records != 1_000_000 or perf.threads != 48
                or perf.workload != {
                    "ycsb_zipf_skew": "0.9", "ycsb_rratio": "95",
                    "ycsb_rmw": "0", "ycsb_max_ope": "10",
                }
                or perf.extime != 3 or perf.reps != 5
                or correctness is not None
                or extra_correctness != [(S2_TAG, s2_correctness_workload())]
                or do_bench is not True or do_settle is not True
                or screening is not None or bench_max_rounds != 1
                or record_rep_returncodes is not True):
            raise ValueError("qualification opt-in evaluation shape mismatch")
    emit = (
        qualification_policy.event_sink.emit
        if qualification_policy is not None else wal.log
    )
    if screening is not None and not do_bench:
        raise ValueError("screening 指定時に do_bench=False は使えない")
    if screening is not None:
        # D58 campaign 分離: runtime 引数だけで既存 campaign へ screening を混在させない。
        # WAL/build を一切書く前に、campaign.lock の同一方針焼き込みを検証する。
        ident.verify_screening_preimage(screening, wal.read_lock(layout))
    correctness = correctness or CorrectnessWorkload()
    passes: List[Tuple[str, CorrectnessWorkload, bool]] = [(LEGACY_TAG, correctness, False)]
    for tag, wl in (extra_correctness or []):
        passes.append((tag, wl, True))
    if (any(fullscale_isolated for _, _, fullscale_isolated in passes)
            and not numactl and qualification_policy is None):
        # S2 相当 (use_numactl=True) は D36 決定4-4 で numactl interleave=all が必須。
        # numactl 無しで黙って通すと較正済み contention 条件からの静かな乖離になる
        # (敵対レビュー 2026-07-09 で確認)。ycsb_tuple_num の既存ガードと同じ流儀
        # (raise → run_campaign の except Exception が eval-exception abort に変換)。
        raise ValueError(
            "extra_correctness に numactl 必須の構成があるが numactl 未指定 "
            "(D36 決定4-4: S2 相当は bench と同じメモリ配置 numactl interleave=all で回す)")
    # identity (D23): coder のコード差まで覆う src_token を build 前に確定し、variant_id
    # (WAL キー) と build (cache_key) で共有する (TOCTOU 偽 hit を防ぐ)。loop は skip/abort
    # キーを同じ id に揃えるため src_token を確定済みで渡す (id 確定点の単一化, D24)。直接
    # caller (src_token=None) は自己計算し、identity を確定できない (allowlist 逸脱 /
    # preprocess 失敗 / git show 失敗) なら fails-closed で評価しない (best-effort skip を
    # identity 核に持ち込まない, 規律2)。
    if src_token is None:
        try:
            src_tok = source_digest.resolve(genome, ccbench_commit, ccbench_dir)
        except RuntimeError as e:
            v0 = variant_id(genome)        # stock id で abort を記録 (WAL キーを残す)
            emit(layout, v0, STAGE_BUILD_START, env_tag, {"genome": genome.canonical()})
            emit(layout, v0, STAGE_ABORT, env_tag,
                 {"reason": "identity-error", "error": _exc_summary(e)})
            log(f"  [eval {v0}] abort: identity-error ({e})")
            r = EvalResult(genome=genome, variant=v0, certified=False, aborted=True)
            r.notes.append(f"source_digest 確定不能 → reject ({e})")
            return r
    else:
        src_tok = src_token
    v = variant_id(genome, src_tok)
    res = EvalResult(genome=genome, variant=v, certified=False, aborted=False)
    emit(layout, v, STAGE_BUILD_START, env_tag,
         {"genome": genome.canonical(), "src_token": src_tok})

    def _abort(reason: str, note: str, extra: Optional[Dict] = None,
              workload_tag: Optional[str] = None) -> EvalResult:
        payload = {"reason": reason, **(extra or {})}
        if workload_tag is not None:
            # D36 決定4-3: どの verify 構成で壊れたかを次手生成が帰属できるようにする。
            payload["workload"] = {"tag": workload_tag}
        emit(layout, v, STAGE_ABORT, env_tag, payload)
        res.aborted = True
        res.notes.append(note)
        log(f"  [eval {v}] abort: {reason}")
        return res

    # --- build (trace + perf 別ビルド, 絶対規律1)。ビルド失敗はこの variant 固有の
    #     失敗として abort 隔離 (campaign 全体を落とさず前進, overnight 耐性) ---
    try:
        if env_contract is None:
            tr = buildcache.build(
                genome, ccbench_commit, trace=True, src_token=src_tok,
                ccbench_dir=ccbench_dir, cache_root=cache_root,
            )
            pf = buildcache.build(
                genome, ccbench_commit, trace=False, src_token=src_tok,
                ccbench_dir=ccbench_dir, cache_root=cache_root,
            )
        else:
            if not isinstance(env_contract, ExecutionEnvironmentContract):
                raise TypeError(
                    "env_contract は ExecutionEnvironmentContract でなければならない"
                )
            default_ccbench = buildcache._ccbench_dir()
            common = {
                "contract": env_contract,
                "ccbench_commit": ccbench_commit,
                "src_token": src_tok,
                "cc": buildcache.DEFAULT_CC,
                "cxx": buildcache.DEFAULT_CXX,
                "cache_root": cache_root or os.path.join(
                    default_ccbench, "build-variants",
                ),
                "ccbench_dir": ccbench_dir,
            }
            if qualification_policy is None:
                tr = buildcache.build_v2(genome, trace=True, **common)
                pf = buildcache.build_v2(genome, trace=False, **common)
            else:
                tr = buildcache.build_v2(
                    genome, trace=True,
                    timeout_s=qualification_policy.build_timeout_s, **common,
                )
                pf = buildcache.build_v2(
                    genome, trace=False,
                    timeout_s=qualification_policy.build_timeout_s, **common,
                )
    except (RuntimeError, subprocess.SubprocessError) as e:
        # 例外要約を payload に載せる (D50 教訓): reason="build-error" だけだと WAL から
        # 失敗原因 (configure 即死か compile error か) を帰属できず調査が build dir の
        # 実地検分から始まる。identity-error の "error" キーと同じ語彙。
        return _abort("build-error", f"ビルド失敗 → reject ({e})",
                      {"error": _exc_summary(e)})
    # trace_bin/perf_bin (16 文字) は sha256-prefix-16 / legacy-display-only (過去 WAL との
    # 対称性維持で不変)。trace_bin_sha256/perf_bin_sha256 (exact 64 lowercase hex) が照合系列。
    emit(layout, v, STAGE_BUILD_DONE, env_tag,
         {"trace_bin": tr.bin_hash, "perf_bin": pf.bin_hash,
          "trace_bin_sha256": tr.bin_sha256, "perf_bin_sha256": pf.bin_sha256,
          "trace_cached": tr.cached, "perf_cached": pf.cached,
          # fitness 計測に使う perf (trace-disabled) build の再現コマンド (規律1)。
          "perf_configure_cmd": pf.configure_cmd, "perf_build_cmd": pf.build_cmd})
    log(f"  [eval {v}] built trace={tr.bin_hash}{'(cache)' if tr.cached else ''} "
        f"perf={pf.bin_hash}{'(cache)' if pf.cached else ''}")

    # --- pre-run binary gate (A-1): 期待値が渡されたときだけ、両ビルド完了直後・trace/bench
    #     起動前に perf バイナリの (build 時に計算済みの) full sha256 を期待値と厳密照合する。
    #     再読・再ハッシュはしない (A-4: bin_sha256 が単一ソース)。期待値の形不正 (exact 64
    #     lowercase hex 以外) も受理せず、mismatch は trace/bench を一切起動せず fails-closed で
    #     abort する。expected_perf_sha256 の供給元 (ratified v2 の期待値取得) は今回未配線 —
    #     デフォルト None では従来と完全同一挙動。
    if expected_perf_sha256 is not None:
        if (not buildcache.is_full_sha256(expected_perf_sha256)
                or pf.bin_sha256 != expected_perf_sha256):
            return _abort(
                "bench-binary-mismatch",
                "perf バイナリ sha256 が期待値と不一致/期待値の形不正 → reject "
                "(trace/bench 未起動)",
                {"expected": expected_perf_sha256,
                 "actual": pf.bin_sha256,
                 "path": pf.binary})

    # --- verify (正しさゲート, 絶対規律2)。legacy (既定・軽量) + extra_correctness
    #     (S2 等・bench 並みの負荷) を順に全て通す (verify 2 本立て, D36 決定2/4) ---
    def _run_one_pass(tag: str, workload: CorrectnessWorkload,
                      pass_numactl: Optional[Sequence[str]]) -> Optional[EvalResult]:
        """1 verify 構成を通す。certified なら None、reject なら abort 済み EvalResult。"""
        # 前パスの verdict を持ち越さない (敵対レビュー 2026-07-09 で確認): このパスが
        # verify_trace_dir に到達する前に reject されたら res.verdict は空のまま返る
        # (前パスが certified で 'serializable' 等を残していても、今回 abort する結果に
        # 古い verdict を紛れ込ませない)。到達すれば下で今回の verdict に上書きされる。
        res.verdict = ""
        tdir = tempfile.mkdtemp(prefix=f"izanagi_eval_trace_{tag}_")  # TMPDIR=/home 配下
        try:
            try:
                ncommit, rc, aborts = _run_trace(tr.binary, tdir, workload.flags,
                                                 clocks_per_us, numactl=pass_numactl)
            except subprocess.TimeoutExpired:
                return _abort("trace-timeout", f"trace 取得タイムアウト ({tag}) → reject",
                              {"timeout_s": TRACE_TIMEOUT_S}, workload_tag=tag)
            # 異常終了・空トレースは「正しさ未確定」。verifier に渡すと空 DSG が
            # serializable=True に化け false-green になる (規律2 違反) → 手前で reject。
            if rc != 0:
                return _abort("trace-run-nonzero-exit",
                              f"trace バイナリ異常終了 ({tag}) rc={rc} → reject",
                              {"rc": rc, "commits": ncommit}, workload_tag=tag)
            if ncommit == 0:
                # aborts も載せる: 「回っているが全 abort (commit 枯渇)」と「そもそも回って
                # いない」を WAL から区別する (sort 変異の主要失敗形態の分離, 規律3)。None の
                # まま記録可 — abort_counts_ 行が出る前に死んだ、の可視化 (判定順で ncommit==0
                # がこの検査より先に来るため None がありうる)。
                return _abort("trace-empty",
                              f"空トレース ({tag}, commit 0) → 検証不能 reject",
                              {"commits": 0, "aborts": aborts}, workload_tag=tag)
            if aborts is None:
                # abort 数は「合成枝 (abort-path) が verify 中に実行された証拠」(phase3.md
                # 完了条件 2 / 残存リスク = 空振り認証)。取れない run を certified にすると
                # その検査可能性ごと落ちる → fails-closed で reject (規律3: 計器の故障を沈黙させない)。
                return _abort("trace-no-abort-counts",
                              f"ccbench stdout に abort_counts_ 集計が無い ({tag}) → "
                              "空振り認証を検査できず reject", {"commits": ncommit},
                              workload_tag=tag)
            try:
                vr = verify_trace_dir(tdir)
            except ParseError as e:
                return _abort("trace-parse-error", f"trace パース不能 ({tag}) → reject ({e})",
                              {"error": _exc_summary(e)}, workload_tag=tag)
            res.verdict = vr.verdict
            verify_payload = {
                "verdict": vr.verdict, "certified": vr.certified,
                "commits": ncommit, "aborts": aborts,
                "anomalies": len(vr.anomalies), "workload": {"tag": tag},
            }
            if qualification_policy is not None:
                verify_payload.update({
                    "argv": (
                        list(pass_numactl or ())
                        + [tr.binary]
                        + [f"-{key}={value}" for key, value in workload.flags.items()]
                        + [f"-clocks_per_us={clocks_per_us}"]
                    ),
                    "binary_sha256": tr.bin_sha256,
                })
            emit(layout, v, STAGE_VERIFY_DONE, env_tag, verify_payload)
            log(f"  [eval {v}] verify[{tag}]: {vr.verdict} ({ncommit} commits, {aborts} "
                f"aborts, {len(vr.anomalies)} anomalies)")
            if not vr.certified:
                # 正しさを破る/確証できない variant は即 reject。fitness を付けない (規律2)。
                # 規律3 (IDS の教訓): なぜ壊れたか (どの trx 間の・どの依存 ww/wr/rw で・どの版で
                # cycle ができたか + integrity) + どの構成 (workload タグ) で壊れたかを構造化して
                # abort payload に載せ、次手生成 (critic/planner) が読めるようにする
                # (digest.load_rejections が読む経路)。Phase 2 は全緑で発火しないが、LLM が
                # RED variant を出す Phase 3 でこれが load-bearing になる。
                vdict = result_to_dict(vr)
                vdict.pop("trace_dir", None)        # 使い捨て tmpdir = WAL に残す価値なし
                return _abort(vr.verdict, f"正しさゲート不通過 ({vr.verdict}, {tag}) → reject",
                              {"verify": vdict}, workload_tag=tag)
            return None
        finally:
            shutil.rmtree(tdir, ignore_errors=True)

    # baseline が古い場合は screening を無効化し、通常の verify-first 経路へ倒す。
    # 再アンカーは driver の責務であり、evaluate() は古い基準による偽棄却をしない。
    active_screening = screening
    screening_disabled_payload: Optional[Dict] = None
    if screening is not None:
        baseline_age_s = time.time() - screening.baseline_measured_at
        if baseline_age_s > screening.reanchor_threshold_s:
            active_screening = None
            screening_disabled_payload = {
                "screening_disabled": {
                    "reason": "stale-baseline",
                    "age_s": baseline_age_s,
                    "threshold_s": screening.reanchor_threshold_s,
                    "baseline_ref": screening.baseline_ref,
                }
            }
            res.notes.append(
                "stale-baseline: baseline age "
                f"{baseline_age_s:.3f}s exceeds reanchor threshold "
                f"{screening.reanchor_threshold_s:.3f}s; screening disabled")

    # screening 経路だけ bench を先行する。測定不能/CV 不定は _run_bench の既存 reason で
    # abort。unstable・abort率欠損・high-abort は曖昧側なので棄却せず verify へ送る。
    bench: Optional[_BenchResult] = None
    if active_screening is not None:
        aborted_result, bench = _run_bench(
            pf.binary, perf, clocks_per_us, numactl, do_settle,
            layout, v, env_tag, _abort, log, screening=True,
            bench_max_rounds=bench_max_rounds,
            record_rep_returncodes=record_rep_returncodes)
        if aborted_result is not None:
            return aborted_result
        assert bench is not None
        screen_reject = False
        if not bench.unstable:
            abort_rate = bench.leading_indicators.get("abort_rate")
            if abort_rate is not None:
                high_abort = abort_rate > (active_screening.baseline_abort_rate *
                                           active_screening.high_abort_factor)
                if not high_abort:
                    threshold = active_screening.baseline_tps * (
                        1 - active_screening.k * active_screening.floor)
                    screen_reject = bench.median_tps < threshold
        if screen_reject:
            return _abort(
                SCREEN_REJECTION_REASON,
                "bench-first screening の保守床を明白に下回る → uncertified reject",
                {"screen": {
                    "median_tps": bench.median_tps,
                    "cv": bench.cv,
                    "baseline_tps": active_screening.baseline_tps,
                    "baseline_ref": active_screening.baseline_ref,
                    "floor": active_screening.floor,
                    "k": active_screening.k,
                    "margin": bench.median_tps / active_screening.baseline_tps - 1,
                }})

    verify_tags: List[str] = []
    for tag, workload, fullscale_isolated in passes:
        # 各パス開始時・probe より前で前パスの verdict を消去する (B-4)。probe (競合検知)
        # や competing-tenant で _run_one_pass に到達せず abort する場合、_run_one_pass 内の
        # 消去が走らず前パスの 'serializable' が aborted 結果へ持ち越されるのを防ぐ。
        res.verdict = ""
        if fullscale_isolated:
            # S2 相当は bench 並みの負荷 → bench と同じ排他下で回す (D36 決定4-4)。
            # 後段の bench 用 bench_lock とはネストしない (逐次 = 別セクションで別途取得、
            # 同一プロセス内での flock 二重取得によるデッドロックを避ける)。
            with bench_lock():
                # bench 本体と同じ admission (絶対規律4、敵対レビュー 2026-07-09 で確認):
                # bench_lock は izanagi 自身の bench 同士しか排他せず、孤児化した子・
                # 他者が手起動した ycsb は掴まない。S2 は bench 並みの全規模 run ゆえ
                # 同じ汚染源に晒される — pgrep で直接確認し fails-closed で reject する。
                try:
                    comp = competing_bench_pids()
                except CompetingBenchProbeError as e:
                    # probe (pgrep) 実行失敗 → 競合の有無を確定できず reject。専用 reason +
                    # 構造化 probe_error payload (規律3/4, B-6)。retryable 扱い (B-3)。
                    aborted_result = _abort(
                        "verify-probe-error",
                        f"競合検知 probe (pgrep) 実行失敗 → S2 相当の verify ({tag}) は"
                        "競合の有無を確定できず reject (環境故障・再評価可能, 規律3/4)",
                        {"probe_error": e.as_dict()}, workload_tag=tag)
                else:
                    if comp:
                        aborted_result = _abort(
                            "verify-competing-tenant",
                            f"競合 ccbench ベンチを検知 → S2 相当の verify ({tag}) は汚染"
                            "計測のまま採用せず reject (規律4)",
                            {"competing": comp}, workload_tag=tag)
                    else:
                        aborted_result = _run_one_pass(tag, workload, numactl)
        else:
            aborted_result = _run_one_pass(tag, workload, None)
        if aborted_result is not None:
            return aborted_result
        verify_tags.append(tag)
    res.certified = True

    # COMMIT の全構文位置を認証完了判定の内側に閉じる。AST gate がこの形を固定する。
    if res.certified:
        if not do_bench:
            # 配線テストでベンチを省くとき: certified だけで commit (fitness なし)。
            if qualification_policy is None:
                wal.log(layout, v, STAGE_COMMIT, env_tag, {
                    "fitness_tps": None,
                    "note": "no-bench",
                    "verify_configs": verify_tags,
                })
            else:
                qualification_policy.event_sink.emit(
                    layout, v, STAGE_COMMIT, env_tag, {
                        "fitness_tps": None,
                        "note": "no-bench",
                        "verify_configs": verify_tags,
                    },
                )
            return res

        # --- bench (排他 + 静定, I/Admission)。screening 経路は既測なので再実行しない。 ---
        if bench is None:
            aborted_result, bench = _run_bench(
                pf.binary, perf, clocks_per_us, numactl, do_settle,
                layout, v, env_tag, _abort, log,
                bench_payload_extra=screening_disabled_payload,
                bench_max_rounds=bench_max_rounds,
                record_rep_returncodes=record_rep_returncodes,
                bench_timeout_s=(
                    qualification_policy.bench_timeout_s
                    if qualification_policy is not None else None
                ),
                require_all_reps=qualification_policy is not None,
                require_settled=(
                    qualification_policy.require_settled
                    if qualification_policy is not None else False
                ),
                emit=emit)
            if aborted_result is not None:
                return aborted_result
        assert bench is not None
        res.fitness_tps, res.cv, res.unstable = (
            bench.median_tps, bench.cv, bench.unstable)

        # --- commit (A: 全段通過した瞬間だけ) ---
        # unstable は規定ラウンドでも CV が収束しなかった印 = この 1 点を信用するな。正しさは
        # 通っているので reject はしないが、採否の分布比較から呼び手が除外する
        # (§3.6(4): 沈黙して 1 点を採用しない)。high_variance は採用ラウンド自体の騒がしさ。
        commit_payload = {
            "fitness_tps": bench.median_tps, "cv": bench.cv,
            "high_variance": bench.high_variance, "unstable": bench.unstable,
            "verify_configs": verify_tags,
        }
        if active_screening is not None:
            commit_payload["screened"] = True
        if qualification_policy is None:
            wal.log(layout, v, STAGE_COMMIT, env_tag, commit_payload)
        else:
            qualification_policy.event_sink.emit(
                layout, v, STAGE_COMMIT, env_tag, commit_payload)
        return res

    raise AssertionError("verify 完了前の非認証結果は COMMIT 経路へ到達できない")
