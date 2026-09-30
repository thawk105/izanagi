# -*- coding: utf-8 -*-
"""trace ログのパーサ。

入力形式 (patches/README.md / include/trace.hh と一致):
  per-thread ファイル `trace_<thid>.log`、1イベント1行。
    C <txid> <thid> <epoch> <tid> <read_count> <write_count>
                                                committed txn。版ID=(epoch,tid)=commit順
    R <txid> <key_hex> <ver_epoch> <ver_tid>  read。見た版
    W <txid> <key_hex> <op> <epoch> <tid>     write。op∈{U,I,D}。新版=この trx の commit
    X <txid> <key_hex> <reason>               lock 被覆違反 (writePhase の #if TRACE assert。D38)
    I <txid> <key_hex> <reason>               write intent 被覆違反 (writePhase の
                                               #if TRACE assert。T-152)
    P <reason>                                permutation 保存違反 (validationPhase の
                                               #if TRACE assert。D41)。txid を持たない —
                                               validationPhase は writePhase の txid 採番より
                                               前に走り、abort する trx でも起こりうるため
                                               txn 文脈と無関係に独立して出現しうる
    E <txid>                                  txn frame の必須終端

1 trx の C/R/W/X/I/E 行は **同一ファイル内で連続** (1 worker が trx を逐次実行し、
writePhase 内で C→R…→W…→E を一括 emit するため)。C/E が txn frame の境界。
txid はグローバル単調なので、ファイルをまたいで txid で束ねられる。
宣言された read/write 件数は R/W 行だけを数えて照合する。X/I は違反記録、P/A は
txid 非相関の記録なので件数へ含めない。全ての C frame は一致する E を必須とする。

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
from array import array
from dataclasses import dataclass, field
from typing import Dict, List, Literal, Optional, Sequence, Union

from .model import ObjectIdentity, Read, Txn, Write, ReadV3, TxnV3, WriteV3

_KEY_RE = re.compile(r"^(?:[0-9a-f]{2})+$")   # 小文字 hex・偶数長 (trace.hh key_to_hex)
_GATE_NAME_RE = re.compile(r"gate_(0|[1-9][0-9]*)\.log\Z")
_GATE_KEY_RE = re.compile(r"[0-9a-f]{16}\Z")
_GATE_UINT_RE = re.compile(r"0|[1-9][0-9]*\Z")
_GATE_MAX = (1 << 64) - 1


def _gate_paths(trace_dir: str) -> tuple[dict[int, str], list[str]]:
    """Enumerate the whole gate namespace, including malformed names."""
    paths: dict[int, str] = {}
    bad: list[str] = []
    with os.scandir(trace_dir) as entries:
        for entry in entries:
            if not entry.name.startswith("gate_"):
                continue
            match = _GATE_NAME_RE.fullmatch(entry.name)
            if match is None or not entry.is_file():
                bad.append(entry.name)
            else:
                paths[int(match.group(1))] = entry.path
    return paths, bad


def _gate_uint(token: str) -> int:
    if _GATE_UINT_RE.fullmatch(token) is None:
        raise ValueError(f"invalid decimal {token!r}")
    value = int(token)
    if value > _GATE_MAX:
        raise ValueError(f"uint64 overflow {token!r}")
    return value


def _gate_stamp(token: str, threads: int, *, written: bool) -> int:
    value = _gate_uint(token)
    writer, sequence = value >> 48, value & ((1 << 48) - 1)
    if written:
        if not (1 <= writer <= threads and sequence):
            raise ValueError(f"invalid writer stamp {token!r}")
    elif writer and not (1 <= writer <= threads and sequence):
        raise ValueError(f"invalid observed stamp {token!r}")
    return value


def _gate_row(line: str, threads: int):
    """Parse one Q/V row without retaining another whole trace."""
    words = line.rstrip("\n").split(" ")
    if not words or any(not word for word in words):
        raise ValueError("blank or noncanonical spacing")
    if words[0] == "V":
        if len(words) != 4 or _GATE_KEY_RE.fullmatch(words[2]) is None:
            raise ValueError("malformed V")
        return "V", _gate_uint(words[1]), words[2], _gate_stamp(
            words[3], threads, written=True)
    if words[0] != "Q" or len(words) < 4:
        raise ValueError("malformed Q/tag")
    txid = None if words[1] == "-" else _gate_uint(words[1])
    thid, n = _gate_uint(words[2]), _gate_uint(words[3])
    if n != len(words) - 4:
        raise ValueError("Q operation count mismatch")
    ops = []
    for word in words[4:]:
        parts = word.split(":")
        if len(parts) != 4:
            raise ValueError("malformed Q operation")
        op, key, observed, written = parts
        if op not in {"R", "W", "M"} or _GATE_KEY_RE.fullmatch(key) is None:
            raise ValueError("invalid Q operation/key")
        if (op == "W") != (observed == "-") or (op == "R") != (written == "-"):
            raise ValueError("invalid Q stamp sentinel")
        obs = None if observed == "-" else _gate_stamp(observed, threads, written=False)
        wr = None if written == "-" else _gate_stamp(written, threads, written=True)
        ops.append((op, key, obs, wr))
    return "Q", txid, thid, ops


class ParseError(Exception):
    pass


TxnFramingViolationKind = Literal[
    "count-mismatch", "missing-end", "duplicate-end",
]


@dataclass(frozen=True)
class TxnFramingViolation:
    """C/E frame と宣言 R/W 件数の構造化された integrity 違反。"""

    kind: TxnFramingViolationKind
    txid: int
    expected_reads: int | None = None
    observed_reads: int | None = None
    expected_writes: int | None = None
    observed_writes: int | None = None


SortPermutationKind = Literal[
    "size-changed", "rcdptr-set-changed", "unknown",
]
SortPermutationMultisetState = bool | Literal["NOT_EVALUATED"] | None


@dataclass(frozen=True)
class SortPermutationClass:
    """固定 origin 内での sort 軸の観測クラス。

    複数 VerifyResult/campaign run を横断する dedup・比較キーとして使ってはならない
    (D146 決定3)。意味を持つのは固定 origin 内だけである。
    """

    kind: SortPermutationKind
    size_preserved: bool | None
    rcdptr_multiset_preserved: SortPermutationMultisetState
    recognized: bool


@dataclass(frozen=True)
class SortPermutationViolation:
    """P 行 1 件の raw token と観測クラスを分離した event witness。"""

    observation: SortPermutationClass
    raw_reason: str
    source_thread_hint: int | None = None
    source_thread_hint_basis: Literal["canonical-filename"] | None = None


_CANONICAL_TRACE_NAME_RE = re.compile(r"^trace_([0-9]+)\.log$")


def _sort_permutation_observation(reason: str) -> SortPermutationClass:
    if reason == "size-changed":
        return SortPermutationClass(
            kind="size-changed",
            size_preserved=False,
            rcdptr_multiset_preserved="NOT_EVALUATED",
            recognized=True,
        )
    if reason == "rcdptr-set-changed":
        return SortPermutationClass(
            kind="rcdptr-set-changed",
            size_preserved=True,
            rcdptr_multiset_preserved=False,
            recognized=True,
        )
    return SortPermutationClass(
        kind="unknown",
        size_preserved=None,
        rcdptr_multiset_preserved=None,
        recognized=False,
    )


def _make_sort_permutation_violation(
        reason: str, path: str,
) -> SortPermutationViolation:
    match = _CANONICAL_TRACE_NAME_RE.fullmatch(os.path.basename(path))
    if match is None:
        source_thread_hint = None
        source_thread_hint_basis = None
    else:
        source_thread_hint = int(match.group(1))
        source_thread_hint_basis = "canonical-filename"
    return SortPermutationViolation(
        observation=_sort_permutation_observation(reason),
        raw_reason=reason,
        source_thread_hint=source_thread_hint,
        source_thread_hint_basis=source_thread_hint_basis,
    )


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
    framing_violations: List[TxnFramingViolation] = field(default_factory=list)
    # X 行 = writePhase の lock 被覆 assert が emit した違反 (D38)。(txid, key, reason)。
    # reason ∈ {not-locked-at-entry (獲得欠落), lock-lost-before-write (保持破れ)}。
    # これは trace-hook の問題でなく variant の CC 正しさ違反 (torn read 窓) で、
    # integrity.lock_coverage_violations に配線され verdict を indeterminate に倒す。
    lock_coverage_violations: List[tuple[int, ObjectIdentity, str]] = field(default_factory=list)
    # I 行 = writePhase の write_set_ と API write intent の相互被覆 assert が emit
    # した違反。(txid, key, reason)。X と同じ txid 相関型で、key 形式も検査する。
    # cycle ではなく write 完全性を認証不能にするため
    # integrity.write_intent_violations に配線され verdict を indeterminate に倒す。
    write_intent_violations: List[tuple[int, ObjectIdentity, str]] = field(default_factory=list)
    # P 行 = validationPhase の permutation 保存 assert が emit した違反 (D41)。reason
    # のみ (txid 無し、上記 schema コメント参照)。非 strict-weak-order comparator の
    # UB で write_set_ の要素が失われた/複製された可能性を示す。
    # integrity.permutation_violations に配線され verdict を indeterminate に倒す。
    permutation_violations: List[str] = field(default_factory=list)
    permutation_violation_details: List[SortPermutationViolation] = field(
        default_factory=list)
    # A 行 = abort 要因の記録 (段 8a trigger-gating 軸の検証計装、D48 positive
    # control)。**違反ではなく集計データ** — integrity/verdict には一切関与しない
    # (docstring の「非ゼロなら認証しない」はこのフィールドには適用されない)。
    # emit 元は characterization 専用の計装 patch のみ (通常 verify では現れない)。
    # 要因別カウント。coverage driver が ADD_ANALYSIS カウンタとの整合検査に使う。
    abort_reasons: Dict[str, int] = field(default_factory=dict)


@dataclass(frozen=True)
class _ParsedFileColumns:
    """Pickle-cheap, per-file parse result used by the production fast path."""

    path_index: int
    path: str
    worker_pid: int
    token_blob: bytes
    token_offsets: array
    txn_txid: array
    txn_thid: array
    txn_commit_epoch: array
    txn_commit_tid: array
    txn_read_offsets: array
    txn_write_offsets: array
    read_key_id: array
    read_ver_epoch: array
    read_ver_tid: array
    write_key_id: array
    write_op_id: array
    issues: ParseIssues
    schema: Optional[int]
    token_table: array
    txn_tx_type: array


@dataclass(frozen=True)
class _ParsedFileFailure:
    """A worker saw a per-file failure; the parent preserves path ordering."""

    path_index: int
    path: str
    worker_pid: int
    error: Exception
    cause: Optional[BaseException]


@dataclass(frozen=True)
class _ParsedFileNeedsLegacy:
    """A Python integer did not fit the compact signed 64-bit columns."""

    path_index: int
    path: str
    worker_pid: int
    schema: Optional[int]


_ParsedFileOutcome = Union[
    _ParsedFileColumns, _ParsedFileFailure, _ParsedFileNeedsLegacy,
]


@dataclass(frozen=True)
class _CompactTrace:
    """Final-winner references passed directly to the compact DSG builder."""

    files: tuple[_ParsedFileColumns, ...]
    winner_txid: array
    winner_path_index: array
    winner_row: array
    issues: ParseIssues
    worker_count: int
    parse_worker_pids: frozenset[int]
    n_reads: int
    n_writes: int


@dataclass(frozen=True)
class _LegacyTrace:
    txns: List[Txn]
    issues: ParseIssues


_TraceData = Union[_CompactTrace, _LegacyTrace]


# Diagnostic-only observation for the behavioral worker test.  It is not part
# of verification input, output, or any acceptance decision.
_LAST_PARSE_WORKER_PIDS: frozenset[int] = frozenset()


def _v3_integer(token: str, name: str, low: int = 0, high: Optional[int] = None) -> int:
    if re.fullmatch(r"0|[1-9][0-9]*", token) is None:
        raise ValueError(f"{name} must be canonical ASCII decimal: {token!r}")
    value = int(token, 10)
    if value < low or (high is not None and value > high):
        raise ValueError(f"{name} outside {low}..{high}: {value}")
    return value


def _check_file_schemas(files: Sequence[tuple[str, Optional[int]]]) -> None:
    first_path = schema = None
    for path, current in sorted(files):
        if current is None:
            continue
        if schema is None:
            first_path, schema = path, current
        elif current != schema:
            raise ParseError(f"mixed trace schemas: {first_path} (v{schema}) and {path} (v{current})")


def _check_key(key: str, issues: ParseIssues) -> None:
    if not _KEY_RE.match(key):
        issues.malformed_keys += 1
        if len(issues.malformed_key_sample) < 5:
            issues.malformed_key_sample.append(key)


def _record_count_mismatch(
        current: Txn, expected_reads: int, expected_writes: int,
        issues: ParseIssues,
) -> None:
    observed_reads = len(current.reads)
    observed_writes = len(current.writes)
    if observed_reads != expected_reads or observed_writes != expected_writes:
        issues.framing_violations.append(TxnFramingViolation(
            kind="count-mismatch",
            txid=current.txid,
            expected_reads=expected_reads,
            observed_reads=observed_reads,
            expected_writes=expected_writes,
            observed_writes=observed_writes,
        ))


def _record_missing_end(
        current: Txn, expected_reads: int, expected_writes: int,
        issues: ParseIssues,
) -> None:
    issues.framing_violations.append(TxnFramingViolation(
        kind="missing-end",
        txid=current.txid,
        expected_reads=expected_reads,
        observed_reads=len(current.reads),
        expected_writes=expected_writes,
        observed_writes=len(current.writes),
    ))


def _parse_file(
        path: str, txns: Dict[int, Txn], issues: ParseIssues,
        occurrences: Optional[List[Txn]] = None,
) -> Optional[int]:
    """1 ファイルをパースして txns に追記する。C/E で frame を管理する。"""
    current: Txn | None = None
    schema = None
    expected_reads = expected_writes = 0
    last_closed_txid: int | None = None
    with open(path, "r", encoding="ascii") as fh:
        try:
            for lineno, raw in enumerate(fh, 1):
                line = raw.rstrip("\n")
                if not line:
                    continue
                f = line.split()
                if not f:
                    raise ParseError(
                        f"{path}:{lineno}: unknown record tag {line[0]!r}: {line!r}")
                tag = f[0]
                if not line.startswith(tag):
                    # 先頭空白を許すと、従来 unknown だった record を split() が
                    # 正規 tag へ変えて受理集合を広げるため、旧拒否挙動を保つ。
                    raise ParseError(
                        f"{path}:{lineno}: unknown record tag {line[0]!r}: {line!r}")
                try:
                    access_extra = {}
                    if isinstance(current, TxnV3) and tag in ("R", "W", "X", "I"):
                        expected = {"R": 6, "W": 7, "X": 5, "I": 5}[tag]
                        if len(f) != expected:
                            raise ValueError(f"v3 {tag} expected exactly {expected} fields")
                        access_extra["table"] = _v3_integer(f[2], "table", 0, 10)
                        f = f[:2] + f[3:]
                        if tag == "W" and f[3] not in ("U", "I", "D"):
                            raise ValueError(f"invalid v3 W op: {f[3]!r}")
                    if tag == "C":
                        # C <txid> <thid> <epoch> <tid> <read_count> <write_count>
                        if len(f) == 5:
                            raise ParseError(
                                f"{path}:{lineno}: trace v1 C record is not supported; "
                                "expected 7 fields including read/write counts")
                        if len(f) not in (7, 10):
                            raise ParseError(
                                f"{path}:{lineno}: malformed C record: expected exactly "
                                f"7 fields, got {len(f)}: {line!r}")
                        current_schema = 3 if len(f) == 10 else 2
                        if schema is not None and schema != current_schema:
                            raise ParseError(f"{path}:{lineno}: mixed trace schemas")
                        schema = current_schema
                        extra = {}
                        if schema == 3:
                            ns = _v3_integer(f[7], "nS")
                            nq = _v3_integer(f[8], "nQ")
                            if ns != 0 or nq != 0:
                                raise ValueError("段 2 未対応: nS/nQ must be zero")
                            extra["tx_type"] = _v3_integer(f[9], "tx_type", 1, 5)
                        _, txid, thid, epoch, tid, read_count, write_count = f[:7]
                        txid_i = int(txid)
                        read_count_i = int(read_count)
                        write_count_i = int(write_count)
                        if txid_i < 0:
                            raise ParseError(
                                f"{path}:{lineno}: txid must be a non-negative integer: "
                                f"{txid_i}")
                        if read_count_i < 0 or write_count_i < 0:
                            raise ParseError(
                                f"{path}:{lineno}: declared read/write counts must be "
                                f"non-negative: reads={read_count_i} writes={write_count_i}")
                        if current is not None:
                            _record_count_mismatch(
                                current, expected_reads, expected_writes, issues)
                            _record_missing_end(
                                current, expected_reads, expected_writes, issues)
                        if txid_i in txns:
                            # 同一 txid の二度目の C — データ健全性違反 (txid は大域一意のはず)。
                            # 下の代入で最初の trx の R/W は失われる (last-wins)。これを dup_txids に
                            # 記録し integrity を unclean にする → verdict は indeterminate になり、
                            # 落ちた辺が cycle を隠して false-green になる事故を防ぐ (絶対規律2)。
                            issues.dup_txids.append(txid_i)
                        current = (TxnV3 if schema == 3 else Txn)(
                            **extra,
                            txid=txid_i,
                            thid=int(thid),
                            commit=(int(epoch), int(tid)),
                        )
                        if occurrences is not None:
                            occurrences.append(current)
                        txns[txid_i] = current
                        expected_reads = read_count_i
                        expected_writes = write_count_i
                        last_closed_txid = None
                    elif tag == "R":
                        # R <txid> <key_hex> <ver_epoch> <ver_tid>
                        _, txid, key, ve, vt = f
                        _expect(current, txid, path, lineno)
                        _check_key(key, issues)
                        current.reads.append((ReadV3 if access_extra else Read)(
                            key=key, ver=(int(ve), int(vt)), **access_extra))
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
                        current.writes.append((WriteV3 if access_extra else Write)(
                            key=key, op=op, **access_extra))
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
                            (current.txid, (access_extra["table"], key) if access_extra else key, reason))
                    elif tag == "I":
                        # I <txid> <key_hex> <reason>  write intent 被覆違反。
                        # writePhase の同一 txn に帰属するため X と同じく _expect を
                        # 通し、key の表現揺れも _check_key で integrity に残す。
                        _, txid, key, reason = f
                        _expect(current, txid, path, lineno)
                        _check_key(key, issues)
                        issues.write_intent_violations.append(
                            (current.txid, (access_extra["table"], key) if access_extra else key, reason))
                    elif tag == "E":
                        # E <txid>。直前の正常 close と同じ txid の E だけは
                        # structured duplicate-end として収集し、それ以外は拒否する。
                        if len(f) != 2:
                            raise ParseError(
                                f"{path}:{lineno}: malformed E record: expected exactly "
                                f"2 fields, got {len(f)}: {line!r}")
                        _, txid = f
                        txid_i = int(txid)
                        if current is None:
                            if last_closed_txid == txid_i:
                                issues.framing_violations.append(
                                    TxnFramingViolation(
                                        kind="duplicate-end", txid=txid_i))
                                # さらに E が続いても「直前の正常 close」ではない。
                                last_closed_txid = None
                                continue
                            raise ParseError(
                                f"{path}:{lineno}: E for txid {txid_i} has no matching "
                                "open txn")
                        if txid_i != current.txid:
                            raise ParseError(
                                f"{path}:{lineno}: E txid {txid_i} does not match open "
                                f"txn {current.txid}")
                        _record_count_mismatch(
                            current, expected_reads, expected_writes, issues)
                        last_closed_txid = current.txid
                        current = None
                    elif tag == "P":
                        # P <reason>  permutation 保存違反 (validationPhase の
                        # #if TRACE assert が emit、D41)。X と異なり txid を
                        # 持たない — validationPhase は commit 前 (txid 未採番)
                        # に走り abort する trx でも起こりうるため、どの txn
                        # ブロックの内外でも独立に出現しうる (_expect を通さ
                        # ない、current が None でも受理する)。
                        _, reason = f
                        issues.permutation_violations.append(reason)
                        issues.permutation_violation_details.append(
                            _make_sort_permutation_violation(reason, path))
                        if current is None:
                            last_closed_txid = None
                    elif tag == "A":
                        # A <reason>  abort 要因の記録 (段 8a、D48 positive
                        # control の計装 patch が abort() 冒頭で emit)。abort
                        # する trx は txid 未採番なので P と同じく txid 非相関
                        # (_expect を通さない)。違反ではなく集計データ —
                        # integrity/verdict に関与しない (ParseIssues の
                        # abort_reasons コメント参照)。
                        _, reason = f
                        issues.abort_reasons[reason] = (
                            issues.abort_reasons.get(reason, 0) + 1)
                        if current is None:
                            last_closed_txid = None
                    else:
                        raise ParseError(
                            f"{path}:{lineno}: unknown record tag {tag!r}: {line!r}")
                except ValueError as e:
                    raise ParseError(
                        f"{path}:{lineno}: malformed line {line!r}: {e}") from e
            if current is not None:
                _record_count_mismatch(
                    current, expected_reads, expected_writes, issues)
                _record_missing_end(
                    current, expected_reads, expected_writes, issues)
        except UnicodeDecodeError as e:
            # encoding="ascii" のデコードは行イテレーション時に発生し、上の行単位
            # try の外。生の UnicodeDecodeError を漏らすと呼び手の ParseError 隔離
            # (pipeline の variant 単位 abort) を突き抜けるためここでラップする。
            raise ParseError(f"{path}: non-ASCII bytes in trace: {e}") from e

    return schema


def _expect(current: Txn | None, txid: str, path: str, lineno: int) -> None:
    if current is None:
        raise ParseError(
            f"{path}:{lineno}: R/W/X/I outside an open C/E frame (txid={txid})")
    if int(txid) != current.txid:
        # 連続性の前提が破れている (トレースの破損か、別 trx の行が割り込んだ)。
        raise ParseError(
            f"{path}:{lineno}: txid {txid} does not match open txn "
            f"{current.txid} (C/R/W/X/I must be inside one contiguous C/E frame)")


def _trace_paths(trace_dir: str) -> List[str]:
    if not os.path.isdir(trace_dir):
        raise ParseError(f"not a directory: {trace_dir}")
    paths = sorted(glob.glob(os.path.join(trace_dir, "trace_*.log")))
    if not paths:
        raise ParseError(f"no trace_*.log files under {trace_dir}")
    return paths


def _effective_worker_count(n_files: int, workers: Optional[int]) -> int:
    if workers is not None:
        if isinstance(workers, bool) or not isinstance(workers, int) or workers < 1:
            raise ValueError("workers must be a positive integer or None")
        return min(n_files, workers, 48)
    affinity: Optional[int] = None
    try:
        affinity = len(os.sched_getaffinity(0))
    except (AttributeError, OSError):
        process_cpu_count = getattr(os, "process_cpu_count", None)
        if process_cpu_count is not None:
            affinity = process_cpu_count()
        if affinity is None:
            affinity = os.cpu_count()
    if affinity is None or affinity < 1:
        affinity = 1
    # Cgroup measurements saturated in elapsed time at 16 workers, while
    # charged memory kept rising beyond 16. Explicit requests retain their 48-worker cap.
    return min(n_files, affinity, 16)


def _token_at(columns: _ParsedFileColumns, token_id: int) -> str:
    start = columns.token_offsets[token_id]
    end = columns.token_offsets[token_id + 1]
    return columns.token_blob[start:end].decode("ascii")


def _object_at(columns: _ParsedFileColumns, token_id: int) -> ObjectIdentity:
    key = _token_at(columns, token_id)
    return (columns.token_table[token_id], key) if columns.schema == 3 else key


def _txn_from_columns(columns: _ParsedFileColumns, row: int) -> Txn:
    read_start = columns.txn_read_offsets[row]
    read_end = columns.txn_read_offsets[row + 1]
    write_start = columns.txn_write_offsets[row]
    write_end = columns.txn_write_offsets[row + 1]
    v3 = columns.schema == 3
    txn = (TxnV3 if v3 else Txn)(
        **({"tx_type": columns.txn_tx_type[row]} if v3 else {}),
        txid=columns.txn_txid[row],
        thid=columns.txn_thid[row],
        commit=(columns.txn_commit_epoch[row], columns.txn_commit_tid[row]),
    )
    txn.reads.extend(
        (ReadV3 if v3 else Read)(
            **({"table": columns.token_table[columns.read_key_id[index]]} if v3 else {}),
            key=_token_at(columns, columns.read_key_id[index]),
            ver=(columns.read_ver_epoch[index], columns.read_ver_tid[index]),
        )
        for index in range(read_start, read_end)
    )
    txn.writes.extend(
        (WriteV3 if v3 else Write)(
            **({"table": columns.token_table[columns.write_key_id[index]]} if v3 else {}),
            key=_token_at(columns, columns.write_key_id[index]),
            op=_token_at(columns, columns.write_op_id[index]),
        )
        for index in range(write_start, write_end)
    )
    return txn


def _parse_file_to_columns(task: tuple[int, str]) -> _ParsedFileOutcome:
    path_index, path = task
    local_txns: Dict[int, Txn] = {}
    occurrences: List[Txn] = []
    issues = ParseIssues()
    try:
        schema = _parse_file(path, local_txns, issues, occurrences)
    except (ParseError, OSError) as error:
        return _ParsedFileFailure(
            path_index, path, os.getpid(), error, error.__cause__,
        )

    token_blob = bytearray()
    token_offsets = array("Q", [0])
    token_ids = {}
    token_table = array("b")
    txn_tx_type = array("b")

    def intern(token: str, table: int = -1) -> int:
        identity = (table, token) if schema == 3 and table >= 0 else token
        token_id = token_ids.get(identity)
        if token_id is not None:
            return token_id
        token_id = len(token_ids)
        token_ids[identity] = token_id
        if schema == 3:
            token_table.append(table)
        token_blob.extend(token.encode("ascii"))
        token_offsets.append(len(token_blob))
        return token_id

    txn_txid = array("q")
    txn_thid = array("q")
    txn_commit_epoch = array("q")
    txn_commit_tid = array("q")
    txn_read_offsets = array("Q", [0])
    txn_write_offsets = array("Q", [0])
    read_key_id = array("I")
    read_ver_epoch = array("q")
    read_ver_tid = array("q")
    write_key_id = array("I")
    write_op_id = array("I")
    try:
        for txn in occurrences:
            if schema == 3:
                txn_tx_type.append(txn.tx_type)
            txn_txid.append(txn.txid)
            txn_thid.append(txn.thid)
            txn_commit_epoch.append(txn.commit[0])
            txn_commit_tid.append(txn.commit[1])
            for read in txn.reads:
                read_key_id.append(intern(read.key, read.table if schema == 3 else -1))
                read_ver_epoch.append(read.ver[0])
                read_ver_tid.append(read.ver[1])
            txn_read_offsets.append(len(read_key_id))
            for write in txn.writes:
                write_key_id.append(intern(write.key, write.table if schema == 3 else -1))
                write_op_id.append(intern(write.op))
            txn_write_offsets.append(len(write_key_id))
    except OverflowError:
        return _ParsedFileNeedsLegacy(path_index, path, os.getpid(), schema)

    return _ParsedFileColumns(
        path_index=path_index,
        path=path,
        worker_pid=os.getpid(),
        schema=schema, token_table=token_table, txn_tx_type=txn_tx_type,
        token_blob=bytes(token_blob),
        token_offsets=token_offsets,
        txn_txid=txn_txid,
        txn_thid=txn_thid,
        txn_commit_epoch=txn_commit_epoch,
        txn_commit_tid=txn_commit_tid,
        txn_read_offsets=txn_read_offsets,
        txn_write_offsets=txn_write_offsets,
        read_key_id=read_key_id,
        read_ver_epoch=read_ver_epoch,
        read_ver_tid=read_ver_tid,
        write_key_id=write_key_id,
        write_op_id=write_op_id,
        issues=issues,
    )


def _parse_file_worker(task: tuple[int, str]) -> _ParsedFileOutcome:
    return _parse_file_to_columns(task)


def _kill_pool_workers(executor) -> None:
    """A broken pool must terminate even when forked workers ignore SIGTERM."""
    for process in list((getattr(executor, "_processes", None) or {}).values()):
        try:
            process.kill()
        except ProcessLookupError:
            pass  # The worker exited between taking the snapshot and kill().


def _parallel_file_outcomes(
        paths: Sequence[str], worker_count: int,
) -> tuple[Optional[List[_ParsedFileOutcome]], List[_ParsedFileOutcome]]:
    """Return ordered outcomes, or ``None`` unless every path arrived exactly once."""
    received: List[_ParsedFileOutcome] = []
    try:
        import multiprocessing
        from concurrent.futures import ProcessPoolExecutor, as_completed

        context = multiprocessing.get_context("fork")
        executor = ProcessPoolExecutor(
            max_workers=worker_count, mp_context=context,
        )
        infrastructure_failure = True
        futures = []
        future = None
        try:
            futures = [
                executor.submit(_parse_file_worker, (index, path))
                for index, path in enumerate(paths)
            ]
            infrastructure_failure = False
            for future in as_completed(futures):
                try:
                    received.append(future.result())
                except Exception:  # worker exit/transport/bootstrap failure
                    infrastructure_failure = True
                    break
            if infrastructure_failure:
                for future in futures:
                    future.cancel()
        except BaseException:
            infrastructure_failure = True
            raise
        finally:
            if infrastructure_failure:
                _kill_pool_workers(executor)
            executor.shutdown(wait=True, cancel_futures=True)
            futures.clear()
            future = executor = None
    except (
            ImportError, OSError, BlockingIOError, RuntimeError, ValueError,
            AssertionError,
    ):
        return None, received

    if infrastructure_failure:
        return None, received
    indices = [outcome.path_index for outcome in received]
    if len(indices) != len(paths) or sorted(indices) != list(range(len(paths))):
        return None, received
    return sorted(received, key=lambda outcome: outcome.path_index), received


def _sequential_file_outcomes(paths: Sequence[str]) -> List[_ParsedFileOutcome]:
    return [_parse_file_worker((index, path)) for index, path in enumerate(paths)]


def _raise_worker_reported_error(outcome: _ParsedFileFailure) -> None:
    if outcome.cause is None:
        raise outcome.error
    raise outcome.error from outcome.cause


def _raise_parent_file_error(outcome: _ParsedFileFailure) -> None:
    if not isinstance(outcome.error, ParseError):
        _raise_worker_reported_error(outcome)

    # Reusing this exact scanner preserves line, message, __cause__, and traceback.
    # If the file disappears or otherwise becomes unreadable after the worker's
    # report, retain the original input failure instead of changing its priority.
    try:
        _parse_file(outcome.path, {}, ParseIssues())
    except ParseError:
        raise
    except OSError:
        _raise_worker_reported_error(outcome)
    raise RuntimeError(f"worker reported a non-reproducible ParseError: {outcome.path}")


def _merge_issues_and_winners(
        files: Sequence[_ParsedFileColumns], worker_count: int,
        worker_pids: frozenset[int],
) -> _CompactTrace:
    indexed_files = tuple(sorted(files, key=lambda columns: columns.path_index))
    issues = ParseIssues()
    winners: Dict[int, tuple[int, int]] = {}
    seen: set[int] = set()
    for columns in files:
        local = columns.issues
        issues.write_version_mismatches.extend(local.write_version_mismatches)
        issues.framing_violations.extend(local.framing_violations)
        issues.lock_coverage_violations.extend(local.lock_coverage_violations)
        issues.write_intent_violations.extend(local.write_intent_violations)
        issues.permutation_violations.extend(local.permutation_violations)
        issues.permutation_violation_details.extend(
            local.permutation_violation_details)
        issues.malformed_keys += local.malformed_keys
        if len(issues.malformed_key_sample) < 5:
            remaining = 5 - len(issues.malformed_key_sample)
            issues.malformed_key_sample.extend(local.malformed_key_sample[:remaining])
        for reason, count in local.abort_reasons.items():
            issues.abort_reasons[reason] = issues.abort_reasons.get(reason, 0) + count

        # Replay every C occurrence in sorted-file/line order.  The local
        # duplicate summary is intentionally ignored so cross-file duplicates
        # and last-wins are decided once, here in the parent.
        for row, txid in enumerate(columns.txn_txid):
            if txid in seen:
                issues.dup_txids.append(txid)
            seen.add(txid)
            winners[txid] = (columns.path_index, row)

    ordered_txids = sorted(winners)
    if ordered_txids:
        expected = ordered_txids[-1] + 1
        issues.missing_txids = expected - len(ordered_txids)
        if issues.missing_txids:
            candidate = 0
            for txid in ordered_txids:
                while candidate < txid and len(issues.missing_sample) < 5:
                    issues.missing_sample.append(candidate)
                    candidate += 1
                if candidate <= txid:
                    candidate = txid + 1

    winner_txid = array("q", ordered_txids)
    winner_path_index = array("I")
    winner_row = array("Q")
    n_reads = n_writes = 0
    for txid in ordered_txids:
        path_index, row = winners[txid]
        winner_path_index.append(path_index)
        winner_row.append(row)
        columns = indexed_files[path_index]
        n_reads += columns.txn_read_offsets[row + 1] - columns.txn_read_offsets[row]
        n_writes += (
            columns.txn_write_offsets[row + 1] - columns.txn_write_offsets[row]
        )
    return _CompactTrace(
        files=indexed_files,
        winner_txid=winner_txid,
        winner_path_index=winner_path_index,
        winner_row=winner_row,
        issues=issues,
        worker_count=worker_count,
        parse_worker_pids=worker_pids,
        n_reads=n_reads,
        n_writes=n_writes,
    )


def _finish_legacy_parse(paths: Sequence[str]) -> _LegacyTrace:
    txns: Dict[int, Txn] = {}
    issues = ParseIssues()
    schemas = [(path, _parse_file(path, txns, issues)) for path in paths]
    _check_file_schemas(schemas)
    ordered_txids = sorted(txns)
    if ordered_txids:
        expected = ordered_txids[-1] + 1
        issues.missing_txids = expected - len(ordered_txids)
        if issues.missing_txids:
            candidate = 0
            for txid in ordered_txids:
                while candidate < txid and len(issues.missing_sample) < 5:
                    issues.missing_sample.append(candidate)
                    candidate += 1
                if candidate <= txid:
                    candidate = txid + 1
    return _LegacyTrace([txns[txid] for txid in ordered_txids], issues)


def _parse_trace_dir_compact(
        trace_dir: str, *, workers: Optional[int] = None,
) -> _TraceData:
    global _LAST_PARSE_WORKER_PIDS
    paths = _trace_paths(trace_dir)
    worker_count = _effective_worker_count(len(paths), workers)
    received: List[_ParsedFileOutcome] = []
    if worker_count > 1:
        outcomes, received = _parallel_file_outcomes(paths, worker_count)
        if outcomes is None:
            # Partial results are never evidence: reread all files serially.
            received.clear()
            outcomes = _sequential_file_outcomes(paths)
    else:
        outcomes = _sequential_file_outcomes(paths)
    _LAST_PARSE_WORKER_PIDS = frozenset(
        outcome.worker_pid for outcome in outcomes
    )

    for outcome in outcomes:
        if isinstance(outcome, _ParsedFileFailure):
            _raise_parent_file_error(outcome)
    _check_file_schemas([(outcome.path, outcome.schema) for outcome in outcomes])
    if any(isinstance(outcome, _ParsedFileNeedsLegacy) for outcome in outcomes):
        return _finish_legacy_parse(paths)
    columns = [
        outcome for outcome in outcomes if isinstance(outcome, _ParsedFileColumns)
    ]
    return _merge_issues_and_winners(
        columns, worker_count, _LAST_PARSE_WORKER_PIDS,
    )


def parse_trace_dir(
        trace_dir: str, *, workers: Optional[int] = None,
) -> tuple[List[Txn], ParseIssues]:
    """Read ``trace_*.log`` and return txid-ordered committed transactions."""
    parsed = _parse_trace_dir_compact(trace_dir, workers=workers)
    if isinstance(parsed, _LegacyTrace):
        return parsed.txns, parsed.issues
    ordered = [
        _txn_from_columns(
            parsed.files[parsed.winner_path_index[index]],
            parsed.winner_row[index],
        )
        for index in range(len(parsed.winner_txid))
    ]
    return ordered, parsed.issues
