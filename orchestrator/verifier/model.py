# -*- coding: utf-8 -*-
"""Izanagi verifier — データモデル。

trace を読んだ後の中間表現と、依存グラフ (DSG) / 異常 (anomaly) の構造化表現。
ここには「正しさ検証に必要なもの」だけを置く。性能数値 (throughput 等) は
**一切持ち込まない** — verifier の入力側隔離 (roadmap §3.4-4, anti-fabrication
isolation)。verifier の入力は trace のみ。
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional, Tuple

# 版ID = (epoch, tid)。同一キー上ではこの組が producer trx を一意に決める
# (ww 競合で tid が単調増加するため。trace-hook の実測で版重複 0 を確認済み)。
# (epoch, tid) の辞書式順序が、そのキー上の版の全順序になる。
Version = Tuple[int, int]

# 初期 DB ロードが書いた版。producer trx を持たない (Tuple::init が epoch=1,tid=0)。
GENESIS: Version = (1, 0)


@dataclass
class Read:
    key: str        # キー生バイトの小文字 hex
    ver: Version    # 読んだ版 (ver_epoch, ver_tid)


@dataclass
class Write:
    key: str        # キー生バイトの小文字 hex
    op: str         # 'U' (update) | 'I' (insert) | 'D' (delete)
    # 書いた版は常にこの trx の commit (= Txn.commit) なので別持ちしない。


@dataclass
class Txn:
    """committed trx 一つ。abort した trx は writePhase に到達せず trace に出ない
    ので、ここに現れるのは全て committed。"""
    txid: int           # グローバル単調 id (TRACE ビルド限定)。grouping 用の主キー
    thid: int           # 実行スレッド
    commit: Version     # (epoch, tid) = 直列化点 = この trx が産んだ全版の版ID
    reads: List[Read] = field(default_factory=list)
    writes: List[Write] = field(default_factory=list)

    def write_keys(self) -> List[str]:
        return [w.key for w in self.writes]


# ---- 依存グラフ (Direct Serialization Graph; Adya) ----

# 辺の種類。すべて「a が直列順序で b より前」を意味する向き (a -> b)。
#   ww : a が版 V を書き、b が同キーの次版を書いた            (write-depends)
#   wr : a が版 V を書き、b がその V を読んだ                  (read-depends)
#   rw : a が版 V を読み、b が同キーで V の直後版を書いた      (anti-dependency)
WW = "ww"
WR = "wr"
RW = "rw"


@dataclass(frozen=True)
class EdgeReason:
    """辺 (u -> v) を正当化する 1 個の具体的競合。witness の人間可読化と
    G分類のため、どのキー・どの版でその依存が生じたかを保持する。"""
    etype: str          # WW | WR | RW
    key: str
    # その依存に関わる版。ww/wr は u が書いた版、rw は u が読んだ版 (と直後版)。
    u_ver: Optional[Version] = None
    v_ver: Optional[Version] = None


@dataclass
class Anomaly:
    """serializability 違反 1 件 = DSG 上の cycle 一つ。"""
    cycle: List[int]                    # cycle を成す txid の列 (先頭に戻る)
    phenomenon: str                     # "G0" | "G1c" | "G2"
    edges: List["CycleEdge"]            # cycle 各辺の正当化

    @property
    def length(self) -> int:
        return len(self.cycle)


@dataclass
class CycleEdge:
    src: int                # txid
    dst: int                # txid
    reasons: List[EdgeReason]   # この辺を正当化する競合 (1個以上)

    @property
    def types(self) -> List[str]:
        # 重複なし・出現順
        seen, out = set(), []
        for r in self.reasons:
            if r.etype not in seen:
                seen.add(r.etype)
                out.append(r.etype)
        return out


@dataclass
class Integrity:
    """trace データ自体の健全性 (CC の正しさとは別軸)。これが非ゼロなら
    『trace か trace-hook の問題』であって CC variant の anomaly ではない可能性
    が高い — 誤検出を防ぐため別枠で報告する。

    **重要 (絶対規律2):** integrity が unclean な run は、辺が落ちて real cycle を
    隠している恐れがあるため verifier は serializable を**認証できない** (= verdict
    は indeterminate)。malformed な入力を「正しさゲート通過」と報告してはいけない。

    **例外 = lock_coverage_violations (後続段 3, D38):** これだけは「trace-hook の
    問題」でなく **variant が引き起こした CC 正しさ違反** (lock 被覆を破って書いた =
    torn read が起こりうる)。だが verdict の帰結は他カウンタと同じ indeterminate で
    正しい — 被覆が破れると trace の版 stamp が信用できず (torn read は値が trace に
    載らない) DSG の辺が落ちている恐れがあるため serializable を認証できない。cycle は
    生まない (non-serializable にはならない) ので anomalies でなくこのカウンタに乗せ、
    critic は「機構欠落型」として読む (cycle 帰属を捏造しない)。検出源は writePhase の
    #if TRACE 被覆 assert が emit する X 行 (trace.hh emit_lock_violation)。

    **同種の例外 = permutation_violations (段 5, D41):** validationPhase の write_set_
    sort が要素を欠落/複製させた (非 strict-weak-order comparator の UB) ことを示す。
    lock_coverage_violations と同じ理由で indeterminate に倒す — sort が破れると
    lock 獲得順序の前提自体が崩れ、その後の trace 版 stamp が信用できない。cycle は
    生まない。検出源は validationPhase の #if TRACE assert が emit する P 行。
    """
    orphan_reads: int = 0       # 非 genesis なのに producer の write が無い read
    version_dups: int = 0       # 同一 (key, ver) を異なる trx が産んだ
    dup_txids: int = 0          # 同一 txid が複数の C 行を持つ
    genesis_commits: int = 0    # commit が genesis 番兵 (1,0) 以下の trx (非物理)
    missing_txids: int = 0      # txid の欠番 (密連番保証の破れ = trx 丸ごと欠落)
    write_version_mismatch: int = 0  # W 行の版が C 行 commit と不一致の trx
    malformed_keys: int = 0     # key が小文字 hex 形式でない (表現揺れは競合辺を消す)
    lock_coverage_violations: int = 0  # X 行の件数 (writePhase で lock 被覆が破れた write。D38)
    permutation_violations: int = 0  # P 行の件数 (validationPhase の sort が要素を欠落/複製。D41)
    notes: List[str] = field(default_factory=list)

    def clean(self) -> bool:
        return (self.orphan_reads == 0 and self.version_dups == 0
                and self.dup_txids == 0 and self.genesis_commits == 0
                and self.missing_txids == 0 and self.write_version_mismatch == 0
                and self.malformed_keys == 0 and self.lock_coverage_violations == 0
                and self.permutation_violations == 0)


@dataclass
class VerifyResult:
    """1 run (= 1 trace ディレクトリ) の検証結果。

    判定は2軸に分かれる:
    - `serializable` = DSG が非巡回かという**純粋なグラフ事実** (cycle が無い)。
    - `verdict` / `certified` = それを**安全に信用してよいか**。integrity が unclean
      なら (辺が落ちている恐れがあり) serializable を認証できないので indeterminate。

    オーケストレータの fitness ゲートは `certified` (= serializable かつ integrity
    clean) だけを「通過」とみなすこと。`serializable` 単独で通過扱いしてはいけない
    (絶対規律2)。
    """
    trace_dir: str
    serializable: bool
    anomalies: List[Anomaly] = field(default_factory=list)
    integrity: Integrity = field(default_factory=Integrity)
    # 統計 (説明可能性のため。性能数値ではない)
    n_txns: int = 0
    n_reads: int = 0
    n_writes: int = 0
    n_keys: int = 0
    n_edges: int = 0
    # cycle (SCC) の全数。anomalies は max_report で witness を切り詰めるが、
    # こちらは常に全数 (total ≤ max_report でも 0 でも入る)。gate の機械判定は
    # witness 数 len(anomalies) でなくこの値を使うこと (witness 上限での偽判定防止)。
    total_cycles: int = 0

    @property
    def verdict(self) -> str:
        """三値判定。"non-serializable" | "indeterminate" | "serializable"。"""
        if self.n_txns == 0:
            # 空トレース = 検証すべき実行が無い。空 DSG は無条件 acyclic だが、それを
            # serializable と認証してはいけない (絶対規律2: 空 DSG を緑と誤認しない)。
            # この安全側不変条件は最下層 (verify_trace_dir でなく VerifyResult) に置き、
            # CLI 直叩き経路でも pipeline 経路でも一律 indeterminate にする。
            return "indeterminate"
        if not self.serializable:
            return "non-serializable"        # cycle あり = 確定的に異常
        if not self.integrity.clean():
            return "indeterminate"           # cycle 無しだが辺が落ちている恐れ
        return "serializable"

    @property
    def certified(self) -> bool:
        """「正しさゲート通過」とみなしてよい唯一の条件。"""
        return self.n_txns > 0 and self.serializable and self.integrity.clean()
