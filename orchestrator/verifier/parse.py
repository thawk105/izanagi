# -*- coding: utf-8 -*-
"""trace ログのパーサ。

入力形式 (patches/README.md / include/trace.hh と一致):
  per-thread ファイル `trace_<thid>.log`、1イベント1行。
    C <txid> <thid> <epoch> <tid>             committed txn。版ID=(epoch,tid)=commit順
    R <txid> <key_hex> <ver_epoch> <ver_tid>  read。見た版
    W <txid> <key_hex> <op> <epoch> <tid>     write。op∈{U,I,D}。新版=この trx の commit
    X <txid> <key_hex> <reason>               lock 被覆違反 (writePhase の #if TRACE assert。D38)
    P <reason>                                permutation 保存違反 (validationPhase の
                                               #if TRACE assert。D41)。txid を持たない —
                                               validationPhase は writePhase の txid 採番より
                                               前に走り、abort する trx でも起こりうるため
                                               txn 文脈と無関係に独立して出現しうる

1 trx の C/R/W 行は **同一ファイル内で連続** (1 worker が trx を逐次実行し、
writePhase 内で C→R…→W… を一括 emit するため)。C 行が trx の区切り。
txid はグローバル単調なので、ファイルをまたいで txid で束ねられる。

trace-hook が構造的に保証する不変条件は、破れを ParseIssues に収集して
integrity へ配線する (辺が落ちて cycle を隠す部分 trace を認証しない、絶対規律2):
  - txid は 0 始まりの密連番 (commit 直前の fetch_add でのみ採番・即 emit)
    → 欠番 = trx 丸ごと欠落 (thread の trace ファイル欠落・I/O 破損)
  - W 行の版 == その trx の C 行 commit (同じ maxtid を emit)
  - key は小文字 hex (key_to_hex)。表現揺れは同一キーを別キーに見せ競合辺を消す
"""
from __future__ import annotations

import glob
import os
import re
from dataclasses import dataclass, field
from typing import Dict, List

from .model import Read, Txn, Write

_KEY_RE = re.compile(r"^(?:[0-9a-f]{2})+$")   # 小文字 hex・偶数長 (trace.hh key_to_hex)


class ParseError(Exception):
    pass


@dataclass
class ParseIssues:
    """パース段で見つけた trace 健全性の問題 (core が integrity へ配線する)。

    いずれも「CC の anomaly」ではなく「trace が完全・整合である保証の破れ」。
    非ゼロなら verifier は serializable を認証しない (indeterminate)。
    """
    dup_txids: List[int] = field(default_factory=list)        # 二度目の C を見た txid
    write_version_mismatches: List[int] = field(default_factory=list)  # W 版 != C commit の txid
    malformed_keys: int = 0                                   # key 形式違反の件数
    malformed_key_sample: List[str] = field(default_factory=list)      # 違反 key の見本
    missing_txids: int = 0                                    # txid 欠番の個数
    missing_sample: List[int] = field(default_factory=list)   # 欠番の見本 (先頭数個)
    # X 行 = writePhase の lock 被覆 assert が emit した違反 (D38)。(txid, key, reason)。
    # reason ∈ {not-locked-at-entry (獲得欠落), lock-lost-before-write (保持破れ)}。
    # これは trace-hook の問題でなく variant の CC 正しさ違反 (torn read 窓) で、
    # integrity.lock_coverage_violations に配線され verdict を indeterminate に倒す。
    lock_coverage_violations: List[tuple] = field(default_factory=list)
    # P 行 = validationPhase の permutation 保存 assert が emit した違反 (D41)。reason
    # のみ (txid 無し、上記 schema コメント参照)。非 strict-weak-order comparator の
    # UB で write_set_ の要素が失われた/複製された可能性を示す。
    # integrity.permutation_violations に配線され verdict を indeterminate に倒す。
    permutation_violations: List[str] = field(default_factory=list)


def _check_key(key: str, issues: ParseIssues) -> None:
    if not _KEY_RE.match(key):
        issues.malformed_keys += 1
        if len(issues.malformed_key_sample) < 5:
            issues.malformed_key_sample.append(key)


def _parse_file(path: str, txns: Dict[int, Txn], issues: ParseIssues) -> None:
    """1 ファイルをパースして txns に追記する。C 行ごとに current を切り替え。"""
    current: Txn | None = None
    with open(path, "r", encoding="ascii") as fh:
        try:
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
                            issues.dup_txids.append(txid_i)
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
                        _check_key(key, issues)
                        current.reads.append(Read(key=key, ver=(int(ve), int(vt))))
                    elif tag == "W":
                        # W <txid> <key_hex> <op> <epoch> <tid>
                        # trace-hook は W の版 ≡ C の commit を保証する。不一致は「実際に
                        # stamp した版と表明 commit がずれた trace 口」の兆候で、blind write
                        # の ww 順序ずれは orphan_reads に乗らず cycle を見逃しうる → 照合。
                        _, txid, key, op, epoch, tid = f
                        _expect(current, txid, path, lineno)
                        _check_key(key, issues)
                        if (int(epoch), int(tid)) != current.commit:
                            issues.write_version_mismatches.append(current.txid)
                        current.writes.append(Write(key=key, op=op))
                    elif tag == "X":
                        # X <txid> <key_hex> <reason>  lock 被覆違反 (writePhase の
                        # #if TRACE assert が emit)。同一 txn の C/R/W と連続で出る
                        # (txid 相関を保つため writePhase の txid を共有)。key 形式も
                        # 検査する (表現揺れは帰属を汚す)。CC 正しさ違反として
                        # integrity.lock_coverage_violations に配線 (絶対規律2/D38)。
                        _, txid, key, reason = f
                        _expect(current, txid, path, lineno)
                        _check_key(key, issues)
                        issues.lock_coverage_violations.append(
                            (current.txid, key, reason))
                    elif tag == "P":
                        # P <reason>  permutation 保存違反 (validationPhase の
                        # #if TRACE assert が emit、D41)。X と異なり txid を
                        # 持たない — validationPhase は commit 前 (txid 未採番)
                        # に走り abort する trx でも起こりうるため、どの txn
                        # ブロックの内外でも独立に出現しうる (_expect を通さ
                        # ない、current が None でも受理する)。
                        _, reason = f
                        issues.permutation_violations.append(reason)
                    else:
                        raise ParseError(
                            f"{path}:{lineno}: unknown record tag {tag!r}: {line!r}")
                except ValueError as e:
                    raise ParseError(
                        f"{path}:{lineno}: malformed line {line!r}: {e}") from e
        except UnicodeDecodeError as e:
            # encoding="ascii" のデコードは行イテレーション時に発生し、上の行単位
            # try の外。生の UnicodeDecodeError を漏らすと呼び手の ParseError 隔離
            # (pipeline の variant 単位 abort) を突き抜けるためここでラップする。
            raise ParseError(f"{path}: non-ASCII bytes in trace: {e}") from e


def _expect(current: Txn | None, txid: str, path: str, lineno: int) -> None:
    if current is None:
        raise ParseError(
            f"{path}:{lineno}: R/W before any C (txid={txid})")
    if int(txid) != current.txid:
        # 連続性の前提が破れている (トレースの破損か、別 trx の行が割り込んだ)。
        raise ParseError(
            f"{path}:{lineno}: txid {txid} does not match open txn "
            f"{current.txid} (C/R/W must be contiguous per txn)")


def parse_trace_dir(trace_dir: str) -> tuple[List[Txn], ParseIssues]:
    """trace_*.log を全て読み、committed txn のリストを返す。

    返り値: (txns, issues)。txns は txid 昇順。issues はパース段で見つけた
    trace 健全性の問題 (dup txid / W 版不一致 / key 形式違反 / txid 欠番)。
    """
    if not os.path.isdir(trace_dir):
        raise ParseError(f"not a directory: {trace_dir}")
    paths = sorted(glob.glob(os.path.join(trace_dir, "trace_*.log")))
    if not paths:
        raise ParseError(f"no trace_*.log files under {trace_dir}")
    txns: Dict[int, Txn] = {}
    issues = ParseIssues()
    for p in paths:
        _parse_file(p, txns, issues)

    # txid 密連番検査: trace-hook は txid を commit 直前の fetch_add (0 始まり) でのみ
    # 採番・即 emit するため、committed txn の txid は 0..N-1 の密連番になる。欠番は
    # trx 丸ごとの欠落 (thread の trace ファイル欠落・ofstream の silent drop 等) で、
    # 欠けた辺が cycle を隠す → integrity 違反として indeterminate に倒す (絶対規律2)。
    if txns:
        expected = max(txns.keys()) + 1
        missing = expected - len(txns)
        if missing > 0:
            issues.missing_txids = missing
            issues.missing_sample = sorted(
                set(range(expected)) - set(txns.keys()))[:5]

    ordered = [txns[k] for k in sorted(txns.keys())]
    return ordered, issues
