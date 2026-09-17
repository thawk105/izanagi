# -*- coding: utf-8 -*-
"""A2: between-run noise floor を実機で確定する独立ドライバ (直列・単一テナント, 絶対規律4)。

calibrator が確定済みの **within-run** noise floor (1 measure_point の reps の CV = その 1 測定の
品質, 2.28%) は、variant と baseline が**別 run/別ビルド**で測られる現実を過小評価する。compare の
採否丸め閾値は『差が信用できるかの下限』= **between-run** であるべき (roadmap §3.6(4), A2)。

ここでは silo の baseline genome (B0-L-W0 = p2_2 が比較に使う stock 構成) を確定動作点で、
**8 個の独立セッション** (各 = reps=5 の measure_point = 実 campaign 1 測定と同形) 回し、
session-median の CV (= between-run noise floor) を `stability.between_run_noise_floor` で出す。
同じ点で within-run floor (reps=10 の 1 measure_point) も測り、両者を併記する (用途が違うので
『between > within』とは主張しない — between=差の floor / within=測定の品質)。

high-abort 域こそ run 間ドリフトが大きい (worklog: no-backoff abort 82% が最大の分散源) ので、
write-heavy(rr5, high-abort) と balanced(rr50, 既存 within 2.28% の点) の 2 点で測る。fresh な
back-to-back セッションは cold-boot/温度ドリフトを含まない**下限**なので、wired する floor は本値と
cross-campaign の genuine な between データ (sweep vs repro, 別時間窓) を突き合わせ保守側に採る。
read-heavy(rr95) は段 8a D 偵察の必須前提 (D48 前提 (b)、シート F4 — trigger-gating 軸の
最良ケース側 workload) で追加 (2026-07-11)。既存 2 点と同形 (同 genome/同動作点) で測る。

**pin の注記 (2026-07-11):** 既存 2 点 (write-heavy/balanced) は dff0f1e (p2_2 歴史 pin) で
実測済み。本 driver は以後 `pin.CURRENT_PIN` でビルドする — floor の用途は現行 pin で走る
campaign (D 偵察等) の採否参照線であり、pin 側に合わせるのが用途に正しい。perf ビルド
(trace=False) では izanagi-trace ブランチの差分は #if TRACE で全て消えるため物理量としての
floor は pin 間で同等 (buildcache の nm ガードが trace シンボル混入を fails-closed に検査)。

  python orchestrator/campaign/between_run_floor.py            # 両動作点
  python orchestrator/campaign/between_run_floor.py write-heavy # 1 点だけ
"""
from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path

if __package__ in {None, ""}:  # pragma: no cover - direct CLI execution
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
    __package__ = "orchestrator.campaign"

from ..calibrator.analyze import noise_floor                       # noqa: E402
from ..calibrator.runner import measure_point                      # noqa: E402
from ..calibrator.stability import between_run_noise_floor        # noqa: E402
from ..verifier.model import compiled_protocol_source_texts        # noqa: E402
from . import buildcache, pin, source_digest              # noqa: E402
from .build_admission import (GeneratorId, build_run_context,  # noqa: E402
                                      derive_build_admission)
from .layout import env_scope_dir                    # noqa: E402
from .model import Genome                                # noqa: E402
from .p2_2 import (CLK, ENV_TAG as DEFAULT_ENV_TAG, EXTIME,  # noqa: E402
                           NUMA, RECORDS, THREADS, _assert_single_tenant)


CCBENCH_COMMIT = pin.CURRENT_PIN   # docstring「pin の注記」参照 (2026-07-11)
# Mirrored by orchestrator/campaign/screening_driver.py to avoid its heavy import chain.
BETWEEN_RUN_FLOOR_SCHEMA_VERSION = "between-run-noise-floor/v1"

# protocol ごとの stock baseline。silo は既存 floor を生成した値を変えない。
BASELINES = {
    "silo": Genome("silo", {
        "BACK_OFF": 0,
        "NO_WAIT_LOCKING_IN_VALIDATION": 1,
        "NO_WAIT_OF_TICTOC": 0,
        "WAL": 0,
    }),
    "mocc": Genome("mocc", {
        "BACK_OFF": 1,
        "KEY_SORT": 0,
        "TEMPERATURE_RESET_OPT": 1,
    }),
    # tictoc: 準備登録 (D2114 項 4、T-2760)。値は現行 pin の external/ccbench/cmake/Options.cmake
    # の cache 既定 (BACK_OFF, NO_WAIT_LOCKING_IN_VALIDATION, NO_WAIT_OF_TICTOC, PREEMPTIVE_ABORTS,
    # TIMESTAMP_HISTORY) で、mocc と同じく CMake 既定を stock とする。TICTOC_SPACE の点 (no-wait は
    # (1,0)、D1418) で、accepted な tictoc 認定較正 record (rr50 / rr95、D2083) の genome と同一。
    # 現行 pin には trace hook が無く、下の D1373 関門が build 前に拒否する (実測の開通は別件)。
    "tictoc": Genome("tictoc", {
        "BACK_OFF": 1,
        "NO_WAIT_LOCKING_IN_VALIDATION": 1,
        "NO_WAIT_OF_TICTOC": 0,
        "PREEMPTIVE_ABORTS": 1,
        "TIMESTAMP_HISTORY": 1,
    }),
}
# Compatibility name for code that consumes the historical silo baseline.
BASELINE = BASELINES["silo"]
CCBENCH_ROOT = Path(__file__).resolve().parents[2] / "external" / "ccbench"

WITHIN_REPS = 10        # within-run floor: 既存 calibration と同じ reps=10 (2.28% と同形)
SESSION_REPS = 5        # between: 各セッションは実 campaign と同形 (p2_2 REPS=5)
SESSIONS = 8            # 独立セッション数 (CV 推定の相対 SE ~27%, 保守側に丸めて使う)

POINTS = [
    ("write-heavy", {"ycsb_zipf_skew": "0.9", "ycsb_rratio": "5", "ycsb_rmw": "0"}),
    ("balanced", {"ycsb_zipf_skew": "0.9", "ycsb_rratio": "50", "ycsb_rmw": "0"}),
    ("read-heavy", {"ycsb_zipf_skew": "0.9", "ycsb_rratio": "95", "ycsb_rmw": "0"}),
]

PEGASUS_ENV_TAG = "pegasus"
ENV_TAG_OVERRIDE = "IZANAGI_BETWEEN_RUN_ENV_TAG"


def _selected_env_tag() -> str:
    value = os.environ.get(ENV_TAG_OVERRIDE, DEFAULT_ENV_TAG)
    if value not in {DEFAULT_ENV_TAG, PEGASUS_ENV_TAG}:
        raise ValueError(
            f"{ENV_TAG_OVERRIDE} must be {DEFAULT_ENV_TAG!r} or "
            f"{PEGASUS_ENV_TAG!r}, got {value!r}"
        )
    return value


def _measurement_profile(env_tag: str) -> tuple[int, list[str]]:
    if env_tag == PEGASUS_ENV_TAG:
        return 2100, []
    return CLK, NUMA


def _wl_tag(wl: dict) -> str:
    return (f"skew{str(wl['ycsb_zipf_skew']).replace('.', 'p')}"
            f"_rr{wl['ycsb_rratio']}_rmw{wl['ycsb_rmw']}")


def _protocol_source_has_trace_hook_evidence_only(
    protocol: str, ccbench_root: Path | str | None = None,
) -> bool:
    """protocol binary の列挙 source に trace hook の text-level 証拠があれば真。

    この述語は hook の意味論的正しさや測定値の正しさを証明しない。
    コメント除去後の同一 file に trace.hh include、
    ``#if TRACE``、izanagi_trace hook 呼出しという文字列が揃うかだけを見る。
    プリプロセッサ条件は評価せず、literal ``#if 0`` directive の block だけは
    証拠から除く。目的は証拠不在を fail-closed に拒否することで hook の実在を
    証明することではない。CMake SOURCES の欠落・読取不能も拒否する。
    前処理条件の評価、到達可能性、実際の発火、verifier が読めることは証明しない。
    """
    sources = compiled_protocol_source_texts(
        protocol, ccbench_root or CCBENCH_ROOT,
    )
    if sources is None:
        return False

    include_pattern = re.compile(
        r'^\s*#\s*include\s+["<][^">]*trace\.hh[">]', re.MULTILINE,
    )
    guard_pattern = re.compile(r"^\s*#\s*if\s+TRACE\b", re.MULTILINE)
    hook_pattern = re.compile(r"\bizanagi_trace::[A-Za-z_]\w*\s*\(")
    for source in sources:
        if (include_pattern.search(source) and guard_pattern.search(source)
                and hook_pattern.search(source)):
            return True
    return False


def measure_point_floor(
    binary: str,
    workload: dict,
    baseline: Genome = BASELINE,
    clocks_per_us: int = CLK,
    numactl: list[str] = NUMA,
    use_perf: bool = True,
    log=print,
) -> dict:
    """1 動作点で within-run と between-run の noise floor を測る。"""
    def measure_session():
        pt = measure_point(binary, RECORDS, THREADS, clocks_per_us, extime=EXTIME,
                           reps=SESSION_REPS, workload=workload, numactl=numactl,
                           use_perf=use_perf)
        return pt.throughput            # session 代表値 = reps の median

    # within-run floor (reps=10 の 1 セッション = その測定の品質)。
    log(f"  [within] {WITHIN_REPS} reps を 1 セッションで ...")
    w_pt = measure_point(binary, RECORDS, THREADS, clocks_per_us, extime=EXTIME,
                         reps=WITHIN_REPS, workload=workload, numactl=numactl,
                         use_perf=use_perf)
    within = noise_floor(w_pt.throughputs)
    log(f"  [within] CV={'n/a' if within.cv is None else f'{within.cv*100:.2f}%'} "
        f"(median {'n/a' if within.median is None else f'{within.median:,.0f}'}, "
        f"abort {(w_pt.abort_rate or 0)*100:.0f}%)")

    # between-run floor (独立 8 セッションの session-median の CV)。セッション間の admission は
    # **lag-free な競合検知** (_assert_single_tenant = competing_bench_pids, A1 と同型) を使う。
    # settle (load EMA) は連続 run 間では残像でほぼ即 return し独立性も足さない (runner.settle
    # docstring) ので per-session ゲートには使わない。競合が現れたら fails-closed で中断 (規律4)。
    log(f"  [between] {SESSIONS} 独立セッション (各 reps={SESSION_REPS}) ...")
    between = between_run_noise_floor(measure_session, settle_fn=_assert_single_tenant,
                                      sessions=SESSIONS)
    log(f"  [between] CV={'n/a' if between.cv is None else f'{between.cv*100:.2f}%'} "
        f"(sessions={between.sessions}, median "
        f"{'n/a' if between.median is None else f'{between.median:,.0f}'})")
    return {
        "schema_version": BETWEEN_RUN_FLOOR_SCHEMA_VERSION,
        "workload": workload, "genome": baseline.canonical(),
        "records": RECORDS, "threads": THREADS, "clocks_per_us": clocks_per_us,
        "abort_rate": w_pt.abort_rate, "run_cmd": w_pt.run_cmd,
        "within_run": {"reps": WITHIN_REPS, "cv": within.cv, "median": within.median,
                       "mean": within.mean, "stdev": within.stdev,
                       "throughputs": within.throughputs,
                       "high_variance": within.high_variance},
        "between_run": {"sessions": between.sessions, "reps_per_session": SESSION_REPS,
                        "cv": between.cv, "median": between.median, "mean": between.mean,
                        "stdev": between.stdev,
                        "session_throughputs": between.session_throughputs,
                        "high_variance": between.high_variance, "notes": between.notes},
    }


def _write_out(
    tag: str,
    workload: dict,
    res: dict,
    env_tag: str = DEFAULT_ENV_TAG,
    protocol: str = "silo",
    log=print,
) -> str:
    out_dir = os.path.join(env_scope_dir(env_tag), "calibration")
    os.makedirs(out_dir, exist_ok=True)
    protocol_part = "" if protocol == "silo" else f"_{protocol}"
    stem = f"between_run_noise{protocol_part}_t{THREADS}_{_wl_tag(workload)}"
    json_path = os.path.join(out_dir, stem + ".json")
    md_path = os.path.join(out_dir, stem + ".md")
    existing = [path for path in (json_path, md_path) if os.path.exists(path)]
    if existing:
        raise FileExistsError("between-run floor 出力は create-only: " + ", ".join(existing))
    wr = res["between_run"]
    wi = res["within_run"]
    wi_cv = "n/a" if wi["cv"] is None else f"{wi['cv']*100:.2f}%"
    wr_cv = "n/a" if wr["cv"] is None else f"{wr['cv']*100:.2f}%"
    wi_med = "n/a" if wi["median"] is None else f"{wi['median']:,.0f}"
    wr_med = "n/a" if wr["median"] is None else f"{wr['median']:,.0f}"
    L = [f"# between-run noise floor — {env_tag} / {tag} ({_wl_tag(workload)})", "",
         "> A2 (orchestrator/campaign/between_run_floor)。計測は trace-disabled build (規律1)・"
         "単一テナント直列 (規律4)。既存 calibration JSON は不可侵で本ファイルは別出力。", "",
         f"- genome (baseline): `{res['genome']}`",
         f"- 動作点: records={res['records']:,} / threads={res['threads']} / "
         f"clocks_per_us={res['clocks_per_us']} / {_wl_tag(workload)}",
         f"- abort_rate: {(res['abort_rate'] or 0)*100:.0f}%", "",
         "## noise floor (用途が違う 2 値を併記)", "",
         "| 種別 | 構成 | CV | median tps | 用途 |",
         "|---|---|---:|---:|---|",
         f"| within-run | {wi['reps']} reps × 1 session | {wi_cv} | "
         f"{wi_med} | その 1 測定の品質 (remeasure 品質ゲート) |",
         f"| between-run | {wr['sessions']} sessions × {wr['reps_per_session']} reps | "
         f"{wr_cv} | {wr_med} | 差が信用できるかの下限 (compare の丸め閾値) |", "",
         "between-run は session-median の散らばり。settle は admission (独立性でない) ため "
         "cold-boot/温度ドリフト未含 = **下限**。wired する floor は cross-campaign の genuine な "
         "between データと突き合わせ保守側に採る (worklog 2026-06-28)。", "",
         "**再現:**", "", "```bash", res["run_cmd"], "```", ""]
    json_text = json.dumps(res, indent=2, ensure_ascii=False)
    md_text = "\n".join(L)
    created: list[str] = []
    try:
        # 既存の確定 calibration JSON は不可侵 (byte-identical provenance)。別ファイルに書く。
        with open(json_path, "x", encoding="utf-8") as f:
            created.append(json_path)
            f.write(json_text)
        with open(md_path, "x", encoding="utf-8") as f:
            created.append(md_path)
            f.write(md_text)
    except BaseException:
        for path in reversed(created):
            try:
                os.unlink(path)
            except FileNotFoundError:
                pass
        raise
    log(f"  wrote {json_path}\n  wrote {md_path}")
    return json_path


def _parse_cli_args(argv) -> tuple[str | None, str]:
    sel = None
    protocol = "silo"
    protocol_seen = False
    args = list(argv[1:])
    index = 0
    while index < len(args):
        arg = args[index]
        if arg == "--protocol":
            if protocol_seen or index + 1 >= len(args):
                raise ValueError("--protocol は値付きで 1 回だけ指定する")
            protocol = args[index + 1]
            protocol_seen = True
            index += 2
            continue
        if arg.startswith("--protocol="):
            if protocol_seen:
                raise ValueError("--protocol は 1 回だけ指定する")
            protocol = arg.split("=", 1)[1]
            protocol_seen = True
            index += 1
            continue
        if arg.startswith("-") or sel is not None:
            raise ValueError("引数が不正")
        sel = arg
        index += 1
    if protocol not in BASELINES:
        raise ValueError(
            f"unknown protocol: {protocol!r} (選択肢: {sorted(BASELINES)})"
        )
    return sel, protocol


def main(argv) -> int:
    try:
        sel, protocol = _parse_cli_args(argv)
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        print(f"usage: {argv[0]} [point] [--protocol PROTOCOL]", file=sys.stderr)
        return 2
    pts = [p for p in POINTS if sel is None or p[0] == sel]
    if not pts:
        print(f"unknown point: {sel} (選択肢: {[p[0] for p in POINTS]})")
        return 2
    baseline = BASELINES[protocol]
    if not _protocol_source_has_trace_hook_evidence_only(protocol):
        raise ValueError(
            f"protocol {protocol!r} の現行 CCBench source に trace hook の証拠がない"
        )

    env_tag = _selected_env_tag()
    clocks_per_us, numactl = _measurement_profile(env_tag)

    _assert_single_tenant()             # campaign 冒頭の単一テナント確認 (規律4)
    print(f"[build] {protocol} baseline (perf=trace-disabled) ...")
    build_context = build_run_context(generator_id=GeneratorId.BACKOFF_SWEEP)
    build_kwargs = {}
    if env_tag == PEGASUS_ENV_TAG:
        resolved_cc, resolved_cxx = buildcache.compilers_for_current_site()
        evidence = source_digest.resolve_evidence(
            baseline, CCBENCH_COMMIT, cxx=resolved_cxx,
        )
        build_kwargs.update(cc=resolved_cc, cxx=resolved_cxx)
    else:
        evidence = source_digest.resolve_evidence(baseline, CCBENCH_COMMIT)
    br = buildcache.build(
        baseline, ccbench_commit=CCBENCH_COMMIT, trace=False,
        admission=derive_build_admission(build_context, evidence),
        build_context=build_context, source_evidence=evidence,
        **build_kwargs,
    )
    print(f"[build] {'cache hit' if br.cached else 'built'}: {br.binary}")

    results = []
    for tag, workload in pts:
        print(f"\n=== between-run floor  workload={tag}  ({workload}) ===")
        if env_tag == PEGASUS_ENV_TAG:
            res = measure_point_floor(
                br.binary, workload, baseline=baseline,
                clocks_per_us=clocks_per_us, numactl=numactl,
                use_perf=False,
            )
            _write_out(tag, workload, res, env_tag=env_tag, protocol=protocol)
        else:
            res = measure_point_floor(br.binary, workload, baseline=baseline)
            _write_out(tag, workload, res, protocol=protocol)
        results.append((tag, res))

    print("\n=== between-run noise floor サマリ ===")
    print(f"  {'workload':12s} {'within(10rep)':>14s} {'between(8sess)':>15s} {'abort':>6s}")
    for tag, res in results:
        wi = res["within_run"]["cv"]
        wr = res["between_run"]["cv"]
        ab = res["abort_rate"] or 0
        print(f"  {tag:12s} "
              f"{('n/a' if wi is None else f'{wi*100:.2f}%'):>14s} "
              f"{('n/a' if wr is None else f'{wr*100:.2f}%'):>15s} "
              f"{ab*100:>5.0f}%")
    print("\n→ wired する BETWEEN_RUN_CV は上記 fresh 値と cross-campaign genuine データ "
          "(sweep vs repro) の保守側 (最大) を人間が確定する。")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
