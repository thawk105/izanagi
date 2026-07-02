# -*- coding: utf-8 -*-
"""WAL (write-ahead log) と クラッシュリカバリ (orchestrator-design.md D/A)。

探索は一晩回しっぱなしでクラッシュ前提。各 variant の評価を**ログ先行書き込み**で
進め (`build_start → build_done → verify_done → bench_done → commit`)、再起動時に
リプレイして「どこまで評価済みか」を復元し途中再開する。

- **D (durability):** 追記ごとに flush+fsync。クラッシュで追記済みレコードを失わない。
- **A (atomicity):** commit レコードがある variant だけ採用。なければ破棄して再評価
  (half-evaluated を population に混ぜない)。
- **末尾切れトレラント:** 追記中のクラッシュで最終行が壊れていても、その 1 行だけ
  捨ててリプレイを続ける (WAL の定石)。
"""
from __future__ import annotations

import json
import os
import time
from typing import Dict, List, Optional

from .layout import CampaignLayout
from .model import (STAGE_ABORT, STAGE_COMMIT, EvalState, WalRecord)


# ---- シリアライズ ----

def _record_to_line(r: WalRecord) -> str:
    obj = {"variant": r.variant, "stage": r.stage, "env_tag": r.env_tag,
           "ts": r.ts, "payload": r.payload}
    return json.dumps(obj, ensure_ascii=False, separators=(",", ":"))


def _line_to_record(line: str) -> WalRecord:
    o = json.loads(line)
    return WalRecord(variant=o["variant"], stage=o["stage"], env_tag=o["env_tag"],
                     ts=o["ts"], payload=o.get("payload", {}))


# ---- 追記 (D) ----

def append(layout: CampaignLayout, record: WalRecord) -> None:
    """WAL に 1 レコードを追記。flush+fsync で耐久化。"""
    os.makedirs(layout.runs_dir, exist_ok=True)
    line = _record_to_line(record) + "\n"
    new_file = not os.path.exists(layout.wal_file)
    # 'a' は O_APPEND 相当でレコード境界がアトミックに近い。fsync でディスクまで。
    fd = os.open(layout.wal_file, os.O_WRONLY | os.O_CREAT | os.O_APPEND, 0o644)
    try:
        os.write(fd, line.encode("utf-8"))
        os.fsync(fd)
    finally:
        os.close(fd)
    if new_file:
        # 初回作成時はディレクトリエントリも fsync し、WAL ファイルの存在自体を耐久化
        # する (D)。これが無いとファイル作成直後のクラッシュで WAL ごと失われうる。
        dfd = os.open(layout.runs_dir, os.O_RDONLY)
        try:
            os.fsync(dfd)
        finally:
            os.close(dfd)


def log(layout: CampaignLayout, variant: str, stage: str, env_tag: str,
        payload: Optional[Dict] = None, ts: Optional[float] = None) -> WalRecord:
    """WalRecord を組んで追記する糖衣。ts 省略時は現在時刻。"""
    rec = WalRecord(variant=variant, stage=stage, env_tag=env_tag,
                    ts=ts if ts is not None else time.time(),
                    payload=payload or {})
    append(layout, rec)
    return rec


# ---- リプレイ / リカバリ (D, A) ----

def read_records(layout: CampaignLayout) -> List[WalRecord]:
    """WAL を全レコード読む。最終行が壊れていたら (追記中クラッシュ) その行だけ捨てる。"""
    if not os.path.exists(layout.wal_file):
        return []
    out: List[WalRecord] = []
    with open(layout.wal_file, "r", encoding="utf-8") as f:
        lines = f.readlines()
    for i, line in enumerate(lines):
        line = line.strip()
        if not line:
            continue
        try:
            out.append(_line_to_record(line))
        except (json.JSONDecodeError, KeyError):
            # 末尾の切れた 1 行だけは許容 (クラッシュ)。途中行の破損は異常。
            if i == len(lines) - 1:
                break
            raise
    return out


def replay(layout: CampaignLayout) -> Dict[str, EvalState]:
    """WAL をリプレイし variant ごとの評価状態を復元する。"""
    states: Dict[str, EvalState] = {}
    for r in read_records(layout):
        st = states.get(r.variant)
        if st is None:
            st = EvalState(variant=r.variant)
            states[r.variant] = st
        st.stages_seen.append(r.stage)
        st.env_tag = r.env_tag
        st.last = r
        if r.stage == STAGE_COMMIT:
            st.committed = True
            st.last_terminal = r
        elif r.stage == STAGE_ABORT:
            st.aborted = True
            st.last_terminal = r
    return states


def terminal_variants(states: Dict[str, EvalState]) -> set:
    """評価が終わっている (commit=採用 / abort=不採用) variant 集合 = スキップ対象。"""
    return {v for v, st in states.items() if st.terminal}


def resumable_variants(states: Dict[str, EvalState]) -> set:
    """未終端 = リカバリで破棄して再評価すべき variant (in-flight クラッシュ)。"""
    return {v for v, st in states.items() if st.resumable}


# ---- campaign.lock (同一性の正準 pre-image) ----

def write_lock(layout: CampaignLayout, preimage: str) -> None:
    os.makedirs(layout.root, exist_ok=True)
    # 初回のみ書く (既存があれば上書きしない = identity は不変)。
    if not os.path.exists(layout.lock_file):
        with open(layout.lock_file, "w", encoding="utf-8") as f:
            f.write(preimage)


def read_lock(layout: CampaignLayout) -> Optional[str]:
    if not os.path.exists(layout.lock_file):
        return None
    with open(layout.lock_file, "r", encoding="utf-8") as f:
        return f.read()
