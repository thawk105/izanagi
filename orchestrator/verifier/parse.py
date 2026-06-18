# -*- coding: utf-8 -*-
"""trace ログのパーサ。

入力形式 (patches/README.md / include/trace.hh と一致):
  per-thread ファイル `trace_<thid>.log`、1イベント1行。
    C <txid> <thid> <epoch> <tid>             committed txn。版ID=(epoch,tid)=commit順
    R <txid> <key_hex> <ver_epoch> <ver_tid>  read。見た版
    W <txid> <key_hex> <op> <epoch> <tid>     write。op∈{U,I,D}。新版=この trx の commit

1 trx の C/R/W 行は **同一ファイル内で連続** (1 worker が trx を逐次実行し、
writePhase 内で C→R…→W… を一括 emit するため)。C 行が trx の区切り。
txid はグローバル単調なので、ファイルをまたいで txid で束ねられる。
"""
from __future__ import annotations

import glob
import os
from typing import Dict, List

from .model import Read, Txn, Version, Write


class ParseError(Exception):
    pass


def _parse_file(path: str, txns: Dict[int, Txn], dup_txids: List[int]) -> None:
    """1 ファイルをパースして txns に追記する。C 行ごとに current を切り替え。"""
    current: Txn | None = None
    with open(path, "r", encoding="ascii") as fh:
        for lineno, raw in enumerate(fh, 1):
            line = raw.rstrip("\n")
            if not line:
                continue
            tag = line[0]
            f = line.split()
            try:
                if tag == "C":
                    # C <txid> <thid> <epoch> <tid>
                    _, txid, thid, epoch, tid = f
                    txid_i = int(txid)
                    if txid_i in txns:
                        # 同一 txid の二度目の C — データ健全性違反 (txid は大域一意のはず)。
                        # 下の代入で最初の trx の R/W は失われる (last-wins)。これを dup_txids に
                        # 記録し integrity を unclean にする → verdict は indeterminate になり、
                        # 落ちた辺が cycle を隠して false-green になる事故を防ぐ (絶対規律2)。
                        dup_txids.append(txid_i)
                    current = Txn(
                        txid=txid_i,
                        thid=int(thid),
                        commit=(int(epoch), int(tid)),
                    )
                    txns[txid_i] = current
                elif tag == "R":
                    # R <txid> <key_hex> <ver_epoch> <ver_tid>
                    _, txid, key, ve, vt = f
                    _expect(current, txid, path, lineno)
                    current.reads.append(Read(key=key, ver=(int(ve), int(vt))))
                elif tag == "W":
                    # W <txid> <key_hex> <op> <epoch> <tid>
                    _, txid, key, op, epoch, tid = f
                    _expect(current, txid, path, lineno)
                    current.writes.append(Write(key=key, op=op))
                else:
                    raise ParseError(
                        f"{path}:{lineno}: unknown record tag {tag!r}: {line!r}")
            except ValueError as e:
                raise ParseError(
                    f"{path}:{lineno}: malformed line {line!r}: {e}") from e


def _expect(current: Txn | None, txid: str, path: str, lineno: int) -> None:
    if current is None:
        raise ParseError(
            f"{path}:{lineno}: R/W before any C (txid={txid})")
    if int(txid) != current.txid:
        # 連続性の前提が破れている (トレースの破損か、別 trx の行が割り込んだ)。
        raise ParseError(
            f"{path}:{lineno}: txid {txid} does not match open txn "
            f"{current.txid} (C/R/W must be contiguous per txn)")


def parse_trace_dir(trace_dir: str) -> tuple[List[Txn], List[int]]:
    """trace_*.log を全て読み、committed txn のリストを返す。

    返り値: (txns, dup_txids)。dup_txids は同一 txid の C が複数あった件
    (健全性チェック用)。txns は txid 昇順。
    """
    if not os.path.isdir(trace_dir):
        raise ParseError(f"not a directory: {trace_dir}")
    paths = sorted(glob.glob(os.path.join(trace_dir, "trace_*.log")))
    if not paths:
        raise ParseError(f"no trace_*.log files under {trace_dir}")
    txns: Dict[int, Txn] = {}
    dup_txids: List[int] = []
    for p in paths:
        _parse_file(p, txns, dup_txids)
    ordered = [txns[k] for k in sorted(txns.keys())]
    return ordered, dup_txids
