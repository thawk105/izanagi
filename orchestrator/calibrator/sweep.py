# -*- coding: utf-8 -*-
"""倍々スイープを回して CalibrationResult を組むオーケストレーション (タスク4b)。

手順 (roadmap §4 / calibrator.md):
  1. TSC 周波数を実測 (clocks_per_us を確定)
  2. records を 1m→2m→4m→… と倍々に上げ各点で perf+throughput を測る
  3. cache miss 率の飽和点を analyze.find_saturation で決める
  4. 飽和点で baseline を連続 N 回測り noise floor (CV) を出す
  5. small/medium 2 点で scale 感度を測る
  6. CalibrationResult を env スコープ output/env/<tag>/ に書き出す

calibration は (env, thread数) ごとで入力非依存 (D13) → env スコープに置く。
"""
from __future__ import annotations

import glob
import os
import platform
import subprocess
from typing import Callable, Dict, List, Optional, Sequence

from . import analyze
from .model import (CalibrationResult, CertificationMeasurement, ScalePoint)
from .runner import measure_point, settle
from .tsc import measure_clocks_per_us
from orchestrator.holdout_observation import (
    CalibrationObservationCapability,
    _transition_calibration_observation_to_noise,
)


def _host_info() -> Dict[str, str]:
    return {
        "node": platform.node(),
        "machine": platform.machine(),
        "cpu_count": str(os.cpu_count() or 0),
        "kernel": platform.release(),
    }


def _parse_cache_size(s: str) -> Optional[int]:
    s = s.strip().upper()
    try:
        if s.endswith("K"):
            return int(s[:-1]) * 1024
        if s.endswith("M"):
            return int(s[:-1]) * 1024 * 1024
        return int(s)
    except ValueError:
        return None


def detect_l3_bytes() -> Optional[int]:
    """sysfs から L3 (last-level) cache の総量を検出する。

    index*/level==3 のキャッシュを shared_cpu_map で重複排除して size を合計
    (= 全ソケットぶんの L3)。読めなければ None。"""
    seen: Dict[str, int] = {}
    for idx in glob.glob("/sys/devices/system/cpu/cpu*/cache/index*"):
        try:
            with open(os.path.join(idx, "level")) as f:
                if f.read().strip() != "3":
                    continue
            with open(os.path.join(idx, "size")) as f:
                size = _parse_cache_size(f.read())
            key_path = os.path.join(idx, "shared_cpu_map")
            key = open(key_path).read().strip() if os.path.exists(key_path) else idx
        except OSError:
            continue
        if size is not None:
            seen[key] = size       # 同一 L3 インスタンスは 1 回だけ
    if not seen:
        return None
    return sum(seen.values())


def run_sweep(binary: str, threads: int, clocks_per_us: int,
              start_records: int, max_records: int,
              extime: int, reps: int,
              workload: Dict[str, str],
              numactl: Optional[Sequence[str]],
              l3_bytes: Optional[int] = None,
              early_stop: bool = True,
              measure_fn: Callable[..., ScalePoint] = measure_point,
              log=print,
              calibration_observation_capability: Optional[
                  CalibrationObservationCapability
              ] = None) -> List[ScalePoint]:
    """start→max を倍々で測り ScalePoint のリストを返す。

    early_stop=True なら、採用レコード数が確定した時点で打ち切る (絶対規律4
    「大きすぎるレコード数は時間を食うだけ」)。確定 = 次のいずれか:
    - 飽和点が末尾より前で確定 (後ろに平らな確認点が既にある)
    - 下限基準 (D15) が満たされた点が現れた (working set が L3×K を超えた最小 N が
      手に入った。それ以上大きくしても run が遅くなるだけ)
    打ち切ったことは log に残す。
    """
    points: List[ScalePoint] = []
    rec = start_records
    while rec <= max_records:
        log(f"  [sweep] records={rec:,} threads={threads} reps={reps} ...")
        measure_kwargs = {
            "extime": extime, "reps": reps, "workload": workload,
            "numactl": numactl,
        }
        if calibration_observation_capability is not None:
            measure_kwargs.update({
                "calibration_observation_capability": (
                    calibration_observation_capability
                ),
                "calibration_observation_phase": "sweep",
            })
        pt = measure_fn(binary, rec, threads, clocks_per_us, **measure_kwargs)
        mr = pt.miss_rate
        tps = pt.throughput
        rss = "" if pt.maxrss_kb is None else f" maxrss={pt.maxrss_kb/1024:.0f}MB"
        log(f"          miss_rate={'n/a' if mr is None else f'{mr*100:.3f}%'} "
            f"median_tps={'n/a' if tps is None else f'{tps:,.0f}'} "
            f"wall={pt.walltime_s:.1f}s{rss}")
        points.append(pt)
        if early_stop and len(points) >= 3:
            sat = analyze.find_saturation(points, l3_bytes=l3_bytes)
            if sat.saturated and sat.records < points[-1].records:
                log(f"  [sweep] 飽和を確認 (records={sat.records:,}, 末尾 "
                    f"{points[-1].records:,} まで平ら) → スイープ打ち切り")
                break
            if sat.lower_bound_selected:
                log(f"  [sweep] 下限基準を充足 (records={sat.records:,}, "
                    f"working set ≥ L3×{sat.l3_multiple:g}) → スイープ打ち切り")
                break
        rec *= 2
    return points


MAX_RECORDS_DEFAULT = 16_000_000   # 倍々スイープ上限 (cli.py と共有。規律4: 小さい方に統一)


def _apply_clocks_fallback(result: "CalibrationResult",
                           clocks_per_us: Optional[int]) -> int:
    """TSC 実測失敗 (None) 時は CCBench default 2100 を採用し、成果物 JSON/MD
    (result.clocks_per_us) にも notes と同じ事実を記録する (semi-silent 解消、audit §2)。"""
    if clocks_per_us is not None:
        return clocks_per_us
    result.notes.append("TSC 周波数を実測できず (cc 不在?)。clocks_per_us 未設定")
    result.clocks_per_us = 2100   # CCBench default にフォールバック (anatomy §6)
    result.notes.append("clocks_per_us を CCBench default 2100 にフォールバック")
    return 2100


def calibrate(binary: str, env_tag: str, threads: int,
              workload: Optional[Dict[str, str]] = None,
              start_records: int = 1_000_000,
              max_records: int = MAX_RECORDS_DEFAULT,
              extime: int = 3, sweep_reps: int = 3,
              noise_reps: int = 10,
              numactl: Optional[Sequence[str]] = None,
              clocks_per_us: Optional[int] = None,
              scale_small: Optional[Dict] = None,
              scale_medium: Optional[Dict] = None,
              certify: bool = False,
              skip_settle: bool = False,
              window_probe: Optional[Callable[[str], object]] = None,
              measurement_sink: Optional[List[CertificationMeasurement]] = None,
              bench_timeout_s: float = 120.0,
              subprocess_runner: Callable[..., object] = subprocess.run,
              log=print,
              calibration_observation_capability: Optional[
                  CalibrationObservationCapability
              ] = None,
              use_perf: bool = True) -> CalibrationResult:
    """フル校正を実行して CalibrationResult を返す。

    ``certify`` は既存 mode と別の fail-closed 経路である。TSC fallback、partial rep、
    missing maxrss と perf 有り時の missing counter を許さず、各 point を ``window_probe`` の
    pre/post で挟む。既定 False の挙動は従来どおり。
    """
    workload = dict(workload or {})

    if clocks_per_us is None:
        if certify:
            raise RuntimeError("certification requires measured TSC; fallback is forbidden")
        log("[calibrate] TSC 周波数を実測中 ...")
        clocks_per_us = measure_clocks_per_us()
        log(f"[calibrate] clocks_per_us = {clocks_per_us} MHz (実測)")

    result = CalibrationResult(
        env_tag=env_tag, threads=threads, clocks_per_us=clocks_per_us,
        workload=workload, host=_host_info())
    if not certify:
        clocks_per_us = _apply_clocks_fallback(result, clocks_per_us)

    # (1) admission control: campaign 冒頭で 1 回だけ静定を待つ (calibrator.md)。
    # 点ごとには待たない (settle の docstring 参照)。
    if not skip_settle:
        log("[calibrate] admission control: load average の静定を待機 ...")
        st = settle()
        log(f"[calibrate] load1={st['load1']:.2f} "
            f"(閾値 {st['threshold']:.1f}, settled={st['settled']})")
        if not st["settled"]:
            result.notes.append(
                f"開始時 load average {st['load1']:.2f} が静定閾値 {st['threshold']:.1f} "
                "を超過。他プロセスの負荷が測定に混入した可能性 (再校正を検討)")

    # L3 総量を検出 (飽和点が無いときの下限基準 D15 に使う)
    l3_bytes = detect_l3_bytes()
    if l3_bytes:
        result.host["l3_total_bytes"] = str(l3_bytes)
        log(f"[calibrate] L3 総量検出: {l3_bytes/1024/1024:.0f} MB")
    else:
        result.notes.append("L3 総量を sysfs から検出できず (下限基準が使えない)")

    def _measure(kind: str, binary_arg: str, records: int, threads_arg: int,
                 clocks_arg: int,
                 calibration_observation_capability: Optional[
                     CalibrationObservationCapability
                 ] = None,
                 calibration_observation_phase: Optional[str] = None,
                 **kwargs) -> ScalePoint:
        reps = int(kwargs.get("reps", 0))
        if certify and window_probe is None:
            raise RuntimeError("certification window_probe is required")
        if window_probe is not None:
            window_probe(f"{kind}:pre:{records}:{threads_arg}")
        point: Optional[ScalePoint] = None
        measurement_kwargs = dict(kwargs)
        if not use_perf:
            measurement_kwargs["use_perf"] = False
        if calibration_observation_capability is not None:
            measurement_kwargs.update({
                "calibration_observation_capability": (
                    calibration_observation_capability
                ),
                "calibration_observation_phase": (
                    calibration_observation_phase or kind
                ),
            })
        try:
            if certify:
                point = measure_point(
                    binary_arg, records, threads_arg, clocks_arg,
                    timeout_s=bench_timeout_s, require_all_reps=True,
                    require_complete_metrics=True,
                    subprocess_runner=subprocess_runner, **measurement_kwargs,
                )
            else:
                # 既定 mode は既存の call shape と partial-rep semantics を保つ。
                point = measure_point(
                    binary_arg, records, threads_arg, clocks_arg,
                    **measurement_kwargs)
            return point
        finally:
            if window_probe is not None:
                window_probe(f"{kind}:post:{records}:{threads_arg}")
            if point is not None and measurement_sink is not None:
                measurement_sink.append(CertificationMeasurement(
                    kind=kind, expected_reps=reps, point=point,
                ))

    # (2)(3) 倍々スイープ + 飽和判定 (膝が無ければ下限基準 D15)
    log("[calibrate] 倍々スイープ開始")
    sweep = run_sweep(binary, threads, clocks_per_us, start_records, max_records,
                      extime, sweep_reps, workload, numactl,
                      l3_bytes=l3_bytes,
                      measure_fn=lambda *a, **kw: _measure("sweep", *a, **kw),
                      calibration_observation_capability=(
                          calibration_observation_capability
                      ),
                      log=log)
    result.sweep = sweep
    result.saturation = analyze.find_saturation(sweep, l3_bytes=l3_bytes)
    sat = result.saturation
    if not use_perf:
        result.notes.extend(sat.notes)
        result.saturation = None
        return result
    log(f"[calibrate] 飽和: {'YES' if sat.saturated else 'NO'}"
        f"{' (下限基準)' if sat.lower_bound_selected else ''} "
        f"→ records={sat.records:,}")

    if calibration_observation_capability is not None:
        _transition_calibration_observation_to_noise(
            calibration_observation_capability,
            saturation_records=sat.records,
        )

    # (4) noise floor: 飽和点で連続 noise_reps 回
    log(f"[calibrate] noise floor: records={sat.records:,} を {noise_reps} 回 ...")
    nf_point = _measure(
        "noise", binary, sat.records, threads, clocks_per_us,
        extime=extime, reps=noise_reps, workload=workload, numactl=numactl,
        calibration_observation_capability=calibration_observation_capability,
        calibration_observation_phase="noise",
    )
    result.noise_floor = analyze.noise_floor(nf_point.throughputs)
    nf = result.noise_floor
    log(f"[calibrate] noise floor CV = "
        f"{'n/a' if nf.cv is None else f'{nf.cv*100:.2f}%'}"
        f"{' (HIGH)' if nf.high_variance else ''}")

    # (5) scale 感度: certification は not-measured を記録するため実測しない。
    if certify:
        return result

    # 既定 mode だけ small/medium 2 点 (既定 small 4t/1m, medium threads/sat.records)
    sm = scale_small or {"threads": 4, "records": 1_000_000}
    md = scale_medium or {"threads": threads, "records": sat.records}
    log(f"[calibrate] scale: small {sm['threads']}t/{sm['records']:,} ...")
    small_pt = _measure(
        "scale-small", binary, sm["records"], sm["threads"], clocks_per_us,
        extime=extime, reps=sweep_reps, workload=workload, numactl=numactl,
    )
    log(f"[calibrate] scale: medium {md['threads']}t/{md['records']:,} ...")
    medium_pt = _measure(
        "scale-medium", binary, md["records"], md["threads"], clocks_per_us,
        extime=extime, reps=sweep_reps, workload=workload, numactl=numactl,
    )
    result.scale = analyze.scale_sensitivity(small_pt, medium_pt)

    return result
