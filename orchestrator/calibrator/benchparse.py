# -*- coding: utf-8 -*-
"""CCBench の stdout → メトリクス辞書。

出力形式 (ccbench-anatomy.md §6): 1 行 1 メトリック、`<label>:\\t<value>`
(タブ区切り)。label は trailing `_` を持つことがある (`commit_counts_:`) ので
最初のタブで split してリテラル一致で拾う。

校正で使うのは:
- `throughput[tps]:` = 主 throughput (commits/sec, 整数)。clocks_per_us 非依存。
- `commit_counts_:` = 総 commit 数 (精度が要るとき actual_extime で割り直す材料)。
- `actual_extime:` = TSC 実測秒。`FLAGS_extime` (OS sleep 目標) との乖離が
  scheduling noise の安価な検出シグナル (anatomy §6 / roadmap §3.6(2))。
- `#FLAGS_*` / `#ShowOptParameters()` 行 = provenance (workload param / build-time -D)。
"""
from __future__ import annotations

import re

from typing import Dict, Optional


def parse_bench_stdout(text: str) -> Dict[str, str]:
    """`label:\\tvalue` 行を辞書化。label の末尾 `:` は剥がす。

    provenance 行 (`#FLAGS_*` / `#...`) も `#` 込みのキーで保持する。
    値は文字列のまま返す (数値化は呼び手が用途に応じて行う)。
    """
    out: Dict[str, str] = {}
    for line in text.splitlines():
        if "\t" not in line:
            continue
        label, _, value = line.partition("\t")
        label = label.strip()
        if label.endswith(":"):
            label = label[:-1]
        if label:
            out[label] = value.strip()
    return out


def _num(s: Optional[str]) -> Optional[float]:
    if s is None:
        return None
    t = s.strip()
    # maxrss の末尾 " kB" 等の単位を落とす
    t = t.split()[0] if t else t
    if t.lower() in ("nan", "-nan", "inf", "-inf", ""):
        return None
    try:
        return float(t)
    except ValueError:
        return None


def throughput_tps(metrics: Dict[str, str]) -> Optional[float]:
    """主 throughput (commits/sec)。無ければ commit_counts_/actual_extime で代替。"""
    v = _num(metrics.get("throughput[tps]"))
    if v is not None:
        return v
    # フォールバック: 生 commit 数 / 実測秒 (anatomy §6 の高精度版)
    commits = _num(metrics.get("commit_counts_"))
    extime = actual_extime(metrics)
    if commits is not None and extime not in (None, 0):
        return commits / extime
    return None


def integer_abort_commit_counts(metrics: Dict[str, str]) -> tuple[int, int]:
    """Read exact decimal counters without passing through floating point."""
    counts = []
    for key in ("abort_counts_", "commit_counts_"):
        value = metrics.get(key)
        if not isinstance(value, str) or re.fullmatch(r"[0-9]+", value) is None:
            raise ValueError(f"{key} must be a decimal integer string")
        counts.append(int(value))
    aborts, commits = counts
    if aborts + commits == 0:
        raise ValueError("abort_counts_ + commit_counts_ must be positive")
    return aborts, commits


def abort_rate(metrics: Dict[str, str]) -> Optional[float]:
    """abort 率 (aborts / (commits+aborts))。CC が競合をどう捌くかの leading indicator
    (no-wait の即abort vs retry、backoff の効果が直接出る、roadmap §3.5)。

    ccbench は `abort_rate:` を直接出すが、欠損/`-nan` のときは生カウントから再計算する。"""
    v = _num(metrics.get("abort_rate"))
    if v is not None:
        return v
    aborts = _num(metrics.get("abort_counts_"))
    commits = _num(metrics.get("commit_counts_"))
    if aborts is not None and commits is not None and (aborts + commits) > 0:
        return aborts / (aborts + commits)
    return None


def latency_ns(metrics: Dict[str, str]) -> Optional[float]:
    """1 トランザクションの平均レイテンシ [ns] (ccbench `latency[ns]:`)。"""
    return _num(metrics.get("latency[ns]"))


def actual_extime(metrics: Dict[str, str]) -> Optional[float]:
    return _num(metrics.get("actual_extime"))


def nominal_extime(metrics: Dict[str, str]) -> Optional[float]:
    # FLAGS_extime は provenance 行 (#FLAGS_extime) で出ることがある
    for k in ("FLAGS_extime", "#FLAGS_extime"):
        v = _num(metrics.get(k))
        if v is not None:
            return v
    return None
