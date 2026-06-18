# -*- coding: utf-8 -*-
"""CalibrationResult → 人間可読テキスト / JSON 可能な dict。

出力先は env スコープ (`output/env/<env-tag>/`)。calibration は入力非依存なので
campaign スコープに置かない (D13)。「なぜそのレコード数?」の根拠 (スイープ全点・
飽和の推移・noise floor の生値) を全部書き出し、査読に先回りする (roadmap §4)。
"""
from __future__ import annotations

from typing import Any, Dict

from .model import (CalibrationResult, NoiseFloor, ScalePoint,
                    ScaleSensitivity, SaturationResult)


def _point_to_dict(p: ScalePoint) -> Dict[str, Any]:
    return {
        "records": p.records,
        "threads": p.threads,
        "llc_load_misses": p.counters.llc_load_misses,
        "llc_loads": p.counters.llc_loads,
        "llc_miss_rate": p.miss_rate,
        "throughput_median_tps": p.throughput,
        "throughputs": p.throughputs,
        "walltime_s": p.walltime_s,
    }


def _sat_to_dict(s: SaturationResult) -> Dict[str, Any]:
    return {
        "records": s.records,
        "saturated": s.saturated,
        "lower_bound_selected": s.lower_bound_selected,
        "threshold": s.threshold,
        "miss_rate_at": s.miss_rate_at,
        "cache_floor_warning": s.cache_floor_warning,
        "l3_bytes": s.l3_bytes,
        "l3_multiple": s.l3_multiple,
        "working_set_ratio": s.working_set_ratio,
        "series": s.series,
        "notes": s.notes,
    }


def _noise_to_dict(n: NoiseFloor) -> Dict[str, Any]:
    return {
        "throughputs": n.throughputs,
        "mean": n.mean,
        "median": n.median,
        "stdev": n.stdev,
        "cv": n.cv,
        "high_variance": n.high_variance,
        "notes": n.notes,
    }


def _scale_to_dict(s: ScaleSensitivity) -> Dict[str, Any]:
    return {
        "small": _point_to_dict(s.small),
        "medium": _point_to_dict(s.medium),
        "small_per_thread": s.small_per_thread,
        "medium_per_thread": s.medium_per_thread,
        "efficiency_ratio": s.efficiency_ratio,
        "scale_suspect": s.scale_suspect,
        "notes": s.notes,
    }


def result_to_dict(r: CalibrationResult) -> Dict[str, Any]:
    return {
        "env_tag": r.env_tag,
        "threads": r.threads,
        "clocks_per_us": r.clocks_per_us,
        "workload": r.workload,
        "host": r.host,
        "saturation": _sat_to_dict(r.saturation) if r.saturation else None,
        "noise_floor": _noise_to_dict(r.noise_floor) if r.noise_floor else None,
        "scale_sensitivity": _scale_to_dict(r.scale) if r.scale else None,
        "sweep": [_point_to_dict(p) for p in r.sweep],
        "notes": r.notes,
    }


def _pct(x) -> str:
    return "n/a" if x is None else f"{x*100:.3f}%"


def render_text(r: CalibrationResult) -> str:
    L = []
    L.append(f"== calibration [{r.env_tag}] threads={r.threads} ==")
    if r.clocks_per_us is not None:
        L.append(f"clocks_per_us (TSC 実測): {r.clocks_per_us} MHz")
    if r.workload:
        L.append("workload: " + ", ".join(f"{k}={v}" for k, v in r.workload.items()))

    if r.saturation:
        s = r.saturation
        if s.saturated:
            verdict = "SATURATED"
        elif s.lower_bound_selected:
            verdict = f"LOWER-BOUND (膝なし→working set≥L3×{s.l3_multiple:g})"
        else:
            verdict = "NOT-SATURATED (暫定値)"
        L.append("")
        L.append(f"-- saturation: {verdict} → records = {s.records:,} "
                 f"(Δ閾値 {_pct(s.threshold)}) --")
        L.append("  records         miss_rate    Δ           maxrss")
        for pt in s.series:
            d = pt.get("delta")
            dd = "" if d is None else f"{d*100:+.3f}pp"
            rss = pt.get("maxrss_kb")
            rr = "" if rss is None else f"{rss/1024:>7.0f}MB"
            L.append(f"  {int(pt['records']):>12,}  {_pct(pt['miss_rate']):>10}  "
                     f"{dd:>10}  {rr}")
        if s.working_set_ratio is not None:
            L.append(f"  working set / L3 = {s.working_set_ratio:.1f}×")
        if s.cache_floor_warning:
            L.append("  ⚠ cache_floor 警告: working set が cache に乗る疑い (下限割れ)")
        for note in s.notes:
            L.append(f"  · {note}")

    if r.noise_floor:
        n = r.noise_floor
        L.append("")
        L.append(f"-- noise floor (N={len(n.throughputs)} run) --")
        if n.median is not None:
            L.append(f"  median {n.median:,.0f} tps  mean {n.mean:,.0f}  "
                     f"CV {_pct(n.cv)}" + ("  ⚠ high variance" if n.high_variance else ""))
        for note in n.notes:
            L.append(f"  · {note}")

    if r.scale:
        sc = r.scale
        L.append("")
        L.append("-- scale sensitivity (small vs medium) --")
        L.append(f"  small  : {sc.small.threads}t/{sc.small.records:,}rec  "
                 f"per-thread {sc.small_per_thread:,.0f} tps"
                 if sc.small_per_thread else "  small  : per-thread n/a")
        L.append(f"  medium : {sc.medium.threads}t/{sc.medium.records:,}rec  "
                 f"per-thread {sc.medium_per_thread:,.0f} tps"
                 if sc.medium_per_thread else "  medium : per-thread n/a")
        if sc.efficiency_ratio is not None:
            L.append(f"  efficiency ratio (medium/small) {sc.efficiency_ratio:.2f}"
                     + ("  ⚠ scale-suspect" if sc.scale_suspect else ""))
        for note in sc.notes:
            L.append(f"  · {note}")

    for note in r.notes:
        L.append(f"· {note}")
    return "\n".join(L)
