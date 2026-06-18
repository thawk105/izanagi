# -*- coding: utf-8 -*-
"""`perf stat` 出力 → PerfCounters。

校正の飽和シグナルは LLC (= L3) の load miss 率なので、最低限 `LLC-load-misses`
と `LLC-loads` を拾う (roadmap §4)。`instructions` / `cycles` も IPC 確認用に拾う。

入力は 2 形式を許容する:
- **CSV モード** (`perf stat -x,` で出力。runner が使う既定): 1 行 =
  `<value>,<unit>,<event>,<run-time>,<pct>,<metric>,<metric-unit>`。
  value は桁区切り無しの素の数値。`<not counted>` / `<not supported>` は欠損。
- **人間可読モード** (素の `perf stat`): `<value>  <event>  # ...`。value は
  ロケール次第で桁区切り (`,`) を持つ。

CSV を優先しつつ人間可読も拾えるようにして、テストではモック文字列を直接渡す。
"""
from __future__ import annotations

import re
from typing import Optional

from .model import PerfCounters

# 拾うイベント名 → PerfCounters の属性。perf は環境で `LLC-load-misses` を
# `LLC-load-misses:u` 等に化かすので prefix 一致で吸収する。
_EVENT_ATTR = {
    "llc-load-misses": "llc_load_misses",
    "llc-loads": "llc_loads",
    "instructions": "instructions",
    "cycles": "cycles",
}

# 人間可読 1 行: 先頭の数値 (桁区切り `,` 許容) + 空白 + イベント名。
_HUMAN_RE = re.compile(r"^\s*([\d,]+(?:\.\d+)?)\s+([A-Za-z][\w.:/\-]+)")

# 欠損マーカ
_MISSING = {"<not counted>", "<not supported>", "<notcounted>", "<notsupported>"}


def _canon(event: str) -> Optional[str]:
    """イベント名を正規化し、拾う対象なら属性名を返す。"""
    e = event.strip().lower()
    # perf の修飾子サフィックス (:u :k :upp 等) を落とす
    e = e.split(":")[0]
    return _EVENT_ATTR.get(e)


def _to_int(token: str) -> Optional[int]:
    t = token.strip().strip('"')
    if t.lower() in _MISSING or t == "":
        return None
    t = t.replace(",", "")          # 桁区切りを除去
    try:
        # perf は整数カウンタでも稀に小数を出す (metric 行) ので float 経由
        return int(float(t))
    except ValueError:
        return None


def _parse_csv_line(line: str, out: PerfCounters) -> bool:
    """CSV 行なら out に反映して True。CSV でなければ False。"""
    fields = line.split(",")
    if len(fields) < 3:
        return False
    event = fields[2].strip().strip('"')
    attr = _canon(event)
    if attr is None:
        # 拾わないイベントでも CSV 行ではあるなら raw に残す
        if event and _looks_like_event(event) and _to_int(fields[0]) is not None:
            out.raw[event] = _to_int(fields[0])
            return True
        return False
    val = _to_int(fields[0])
    if val is not None:
        setattr(out, attr, val)
        out.raw[event] = val
    return True


def _parse_human_line(line: str, out: PerfCounters) -> bool:
    m = _HUMAN_RE.match(line)
    if not m:
        return False
    attr = _canon(m.group(2))
    val = _to_int(m.group(1))
    if val is None:
        return False
    out.raw[m.group(2)] = val
    if attr is not None:
        setattr(out, attr, val)
    return True


def _looks_like_event(s: str) -> bool:
    return bool(re.match(r"^[A-Za-z][\w.:/\-]+$", s.strip()))


def parse_perf_stat(text: str) -> PerfCounters:
    """perf stat の stdout/stderr テキストから PerfCounters を組む。"""
    out = PerfCounters()
    for line in text.splitlines():
        if not line.strip():
            continue
        # CSV を先に試し、ダメなら人間可読。
        if _parse_csv_line(line, out):
            continue
        _parse_human_line(line, out)
    return out
