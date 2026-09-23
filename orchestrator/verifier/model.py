# -*- coding: utf-8 -*-
"""Izanagi verifier — データモデル。

trace を読んだ後の中間表現と、依存グラフ (DSG) / 異常 (anomaly) の構造化表現。
ここには「正しさ検証に必要なもの」だけを置く。性能数値 (throughput 等) は
**一切持ち込まない** — verifier の入力側隔離 (roadmap §3.4-4, anti-fabrication
isolation)。verifier の入力は trace、commit witness、protocol/source context に限る。
"""
from __future__ import annotations

from dataclasses import dataclass, field
import os
from pathlib import Path
import re
from typing import TYPE_CHECKING, Dict, List, Optional, Tuple

if TYPE_CHECKING:
    from .parse import SortPermutationViolation, TxnFramingViolation

# 版ID = (epoch, tid)。同一キー上ではこの組が producer trx を一意に決める
# (ww 競合で tid が単調増加するため。trace-hook の実測で版重複 0 を確認済み)。
# (epoch, tid) の辞書式順序が、そのキー上の版の全順序になる。
Version = Tuple[int, int]

# 初期 DB ロードが書いた版。producer trx を持たない (Tuple::init が epoch=1,tid=0)。
GENESIS: Version = (1, 0)


PROOF_SURFACE_EVIDENCE_PRESENT = "evidence-present"
PROOF_SURFACE_EVIDENCE_ABSENT = "evidence-absent"
PROOF_SURFACE_UNAVAILABLE = "unavailable"
_PROOF_SURFACE_VALUES = frozenset({
    PROOF_SURFACE_EVIDENCE_PRESENT,
    PROOF_SURFACE_EVIDENCE_ABSENT,
    PROOF_SURFACE_UNAVAILABLE,
})
_PROOF_SURFACE_PROTOCOLS = frozenset({"silo", "si", "mocc"})
_COMPILED_SOURCE_SUFFIXES = frozenset({".c", ".cc", ".cpp", ".cxx"})
_SOURCE_COMMENT_PATTERN = re.compile(r"//[^\n]*|/\*.*?\*/", re.DOTALL)
_CONDITIONAL_OPEN_PATTERN = re.compile(r"^\s*#\s*(?:if|ifdef|ifndef)\b")
_CONDITIONAL_CLOSE_PATTERN = re.compile(r"^\s*#\s*endif\b")
_CONDITIONAL_ALTERNATE_PATTERN = re.compile(r"^\s*#\s*(?:else|elif)\b")
_LITERAL_IF_ZERO_PATTERN = re.compile(r"^\s*#\s*if\s+0\s*$")
_LITERAL_TRACE_PATTERN = re.compile(r"^\s*#\s*if\s+TRACE\s*$")
_LOCK_COVERAGE_EMITTER_PATTERN = re.compile(
    r"\bizanagi_trace::emit_lock_violation\s*\(",
)
_PERMUTATION_EMITTER_PATTERN = re.compile(
    r'\bizanagi_trace::stream\s*\([^)]*\)\s*<<\s*"P "',
)
_WRITE_INTENT_EMITTER_PATTERNS = (
    re.compile(r"\bizanagi_trace::emit_write_intent_violation\s*\("),
    re.compile(r'\bizanagi_trace::stream\s*\([^)]*\)\s*<<\s*"I "'),
)


@dataclass(frozen=True)
class ProofSurfaceAssessment:
    """X/P/I emitter の compiled-source text assessment。"""

    protocol: Optional[str] = None
    lock_coverage: str = PROOF_SURFACE_UNAVAILABLE
    permutation: str = PROOF_SURFACE_UNAVAILABLE
    write_intent: str = PROOF_SURFACE_UNAVAILABLE

    def __post_init__(self) -> None:
        if self.protocol is not None and type(self.protocol) is not str:
            raise TypeError("proof-surface protocol must be exact str or None")
        for name, value in (
            ("X", self.lock_coverage),
            ("P", self.permutation),
            ("I", self.write_intent),
        ):
            if value not in _PROOF_SURFACE_VALUES:
                raise ValueError(f"proof-surface {name} value is invalid: {value!r}")

    def certification_gate_satisfied(self) -> bool:
        """Certification が要求する X/P の text evidence が揃うときだけ真。"""
        return (
            self.lock_coverage == PROOF_SURFACE_EVIDENCE_PRESENT
            and self.permutation == PROOF_SURFACE_EVIDENCE_PRESENT
        )

    def as_record(self) -> Dict[str, Optional[str]]:
        """VERIFY_DONE 用の X/P/I 三面 projection。"""
        return {
            "protocol": self.protocol,
            "X": self.lock_coverage,
            "P": self.permutation,
            "I": self.write_intent,
        }


def _normalize_compiled_source_text(source: str) -> str:
    """コメントと literal ``#if 0`` block を共通規則で除く。"""
    source = _SOURCE_COMMENT_PATTERN.sub(
        lambda found: "\n" * found.group(0).count("\n"), source,
    )
    conditional_depth = 0
    dead_if_zero_depth: Optional[int] = None
    retained_lines = []
    for line in source.splitlines(keepends=True):
        directive_line = line.rstrip("\r\n")
        if _CONDITIONAL_OPEN_PATTERN.match(directive_line):
            conditional_depth += 1
            if (dead_if_zero_depth is None
                    and _LITERAL_IF_ZERO_PATTERN.match(directive_line)):
                dead_if_zero_depth = conditional_depth
        if dead_if_zero_depth is None:
            retained_lines.append(line)
        # #else/#elif は評価せず、literal #if 0 全体を対応する #endif まで捨てる。
        if _CONDITIONAL_CLOSE_PATTERN.match(directive_line):
            if conditional_depth == dead_if_zero_depth:
                dead_if_zero_depth = None
            conditional_depth = max(0, conditional_depth - 1)
    return "".join(retained_lines)


def compiled_protocol_source_texts(
        protocol: str, ccbench_root: Path | str,
) -> Optional[Tuple[str, ...]]:
    """CMake ``SOURCES`` の compiled source を列挙し lexical normalization する。

    D1373 と X/P/I assessment が同じ source 集合と同じコメント・literal
    ``#if 0`` 除去規則を見るための唯一の実装である。CMake/source の欠落、不正、
    読取不能は ``None`` とする。
    """
    # D1373 の wave 前 semantics を保つ。CMake が列挙する absolute path や
    # ``..`` を裁定なしに拒否せず、protocol/root の型エラーもここで握り潰さない。
    protocol_dir = Path(ccbench_root) / "cc" / protocol
    if not protocol_dir.is_dir():
        return None
    try:
        cmake_source = (protocol_dir / "CMakeLists.txt").read_text(
            encoding="utf-8",
        )
    except (OSError, UnicodeDecodeError):
        return None

    # CMake の行コメント内にある helper 名を invocation と誤認しない。
    cmake_source = re.sub(r"#.*$", "", cmake_source, flags=re.MULTILINE)
    source_paths: Optional[Tuple[Path, ...]] = None
    for match in re.finditer(
        r"\bccbench_add_protocol\s*\((.*?)\)", cmake_source, re.DOTALL,
    ):
        tokens = match.group(1).split()
        if not tokens or tokens[0] != protocol:
            continue
        if source_paths is not None or tokens.count("SOURCES") != 1:
            return None
        source_index = tokens.index("SOURCES") + 1
        section_indexes = [
            tokens.index(section, source_index)
            for section in ("WORKLOADS", "OPTIONS")
            if section in tokens[source_index:]
        ]
        source_end = min(section_indexes, default=len(tokens))
        source_names = tokens[source_index:source_end]
        if not source_names:
            return None
        relative_names = tuple(Path(name) for name in source_names)
        if any(name.suffix not in _COMPILED_SOURCE_SUFFIXES
               for name in relative_names):
            return None
        paths = tuple(protocol_dir / name for name in relative_names)
        if any(not path.is_file() for path in paths):
            return None
        source_paths = paths
    if source_paths is None:
        return None

    normalized = []
    try:
        for path in source_paths:
            normalized.append(_normalize_compiled_source_text(
                path.read_text(encoding="utf-8"),
            ))
    except (OSError, UnicodeDecodeError):
        return None
    return tuple(normalized)


@dataclass(frozen=True)
class CompiledProtocolSourceSnapshot:
    """One immutable input snapshot for the compiled-source text predicates."""

    protocol: str
    ccbench_root: str
    normalized_sources: Optional[Tuple[str, ...]]


def capture_compiled_protocol_source_snapshot(
        protocol: str, ccbench_root: Path | str,
) -> CompiledProtocolSourceSnapshot:
    """Capture the exact normalized source texts consumed by later assessment."""
    root = os.path.realpath(os.path.abspath(os.fspath(ccbench_root)))
    return CompiledProtocolSourceSnapshot(
        protocol=protocol,
        ccbench_root=root,
        normalized_sources=compiled_protocol_source_texts(protocol, root),
    )


def _literal_trace_regions(source: str) -> str:
    """literal ``#if TRACE`` の first branch 内にある text だけを返す。"""
    # None は評価しない一般 conditional、bool は literal TRACE conditional の
    # first branch 内外を表す。一般 conditional の枝はどちらも保持する。
    conditional_stack: List[Optional[bool]] = []
    retained_lines = []
    for line in source.splitlines(keepends=True):
        directive_line = line.rstrip("\r\n")
        if _CONDITIONAL_OPEN_PATTERN.match(directive_line):
            conditional_stack.append(
                True if _LITERAL_TRACE_PATTERN.match(directive_line) else None
            )
            continue
        if _CONDITIONAL_ALTERNATE_PATTERN.match(directive_line):
            if conditional_stack and conditional_stack[-1] is not None:
                conditional_stack[-1] = False
            continue
        if _CONDITIONAL_CLOSE_PATTERN.match(directive_line):
            if conditional_stack:
                conditional_stack.pop()
            continue
        trace_states = [
            state for state in conditional_stack if state is not None
        ]
        if trace_states and all(trace_states):
            retained_lines.append(line)
    return "".join(retained_lines)


def assess_protocol_proof_surfaces(
        protocol: Optional[str], ccbench_root: Optional[Path | str],
) -> ProofSurfaceAssessment:
    """X/P/I emitter call の compiled-source text evidence を三値評価する。

    compiled source の literal ``#if TRACE`` first branch に emitter の呼出しが
    在ることしか言わない。
    前処理条件の評価、到達可能性、実際の発火、verifier が読めることは証明しない。
    未指定、対象外 protocol、source 不読、走査例外は三面
    とも ``unavailable`` にする。読取例外を evidence-present へ変換しない。
    """
    recorded_protocol = protocol if type(protocol) is str else None
    unavailable = ProofSurfaceAssessment(protocol=recorded_protocol)
    if protocol not in _PROOF_SURFACE_PROTOCOLS or ccbench_root is None:
        return unavailable
    try:
        snapshot = capture_compiled_protocol_source_snapshot(
            protocol, ccbench_root,
        )
        return assess_compiled_protocol_source_snapshot(snapshot)
    except Exception:
        # Source/scan failure is an unavailable assessment, never positive evidence.
        return unavailable


def assess_compiled_protocol_source_snapshot(
        snapshot: CompiledProtocolSourceSnapshot,
) -> ProofSurfaceAssessment:
    """Assess X/P/I from one immutable compiled-source text snapshot.

    The snapshot contains the exact lexically normalized texts scanned here; no
    mutable source path is reopened.  This still proves only that emitter calls
    occur in compiled-source text inside a literal ``#if TRACE`` first branch.
    It does not evaluate preprocessing conditions, reachability, actual firing,
    or verifier readability.
    """
    if type(snapshot) is not CompiledProtocolSourceSnapshot:
        raise TypeError("compiled protocol source snapshot must be exact")
    protocol = snapshot.protocol
    unavailable = ProofSurfaceAssessment(
        protocol=protocol if type(protocol) is str else None,
    )
    if (protocol not in _PROOF_SURFACE_PROTOCOLS
            or snapshot.normalized_sources is None):
        return unavailable
    try:
        trace_regions = tuple(
            _literal_trace_regions(source)
            for source in snapshot.normalized_sources
        )

        def assessed(found: bool) -> str:
            return (
                PROOF_SURFACE_EVIDENCE_PRESENT
                if found else PROOF_SURFACE_EVIDENCE_ABSENT
            )

        lock_coverage = assessed(any(
            _LOCK_COVERAGE_EMITTER_PATTERN.search(source)
            for source in trace_regions
        ))
        permutation = assessed(any(
            _PERMUTATION_EMITTER_PATTERN.search(source)
            for source in trace_regions
        ))
        write_intent = assessed(any(
            pattern.search(source)
            for source in trace_regions
            for pattern in _WRITE_INTENT_EMITTER_PATTERNS
        ))
    except Exception:
        # Snapshot/scan failure is unavailable, never positive evidence.
        return unavailable
    return ProofSurfaceAssessment(
        protocol=protocol,
        lock_coverage=lock_coverage,
        permutation=permutation,
        write_intent=write_intent,
    )


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


@dataclass(kw_only=True)
class ReadV3(Read):
    table: int


@dataclass(kw_only=True)
class WriteV3(Write):
    table: int


@dataclass(kw_only=True)
class TxnV3(Txn):
    tx_type: int
    schema: int = field(default=3, init=False)


ObjectIdentity = str | tuple[int, str]


def object_identity(access: Read | Write) -> ObjectIdentity:
    return (access.table, access.key) if isinstance(access, (ReadV3, WriteV3)) else access.key


def object_label(key: ObjectIdentity) -> str:
    return f"table={key[0]} key={key[1]}" if isinstance(key, tuple) else f"key={key}"


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


@dataclass(frozen=True, kw_only=True)
class EdgeReasonV3(EdgeReason):
    table: int


@dataclass(kw_only=True)
class AnomalyV3(Anomaly):
    cycle_tx_types: tuple[int, ...]


@dataclass(frozen=True)
class ExistenceViolation:
    """A v3 existence-history violation for one read or write version."""
    txid: int
    table: int
    key: str
    version: Version
    kind: str
    ops: Tuple[str, ...] = ()


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

    **同種の例外 = write_intent_violations (T-152):** writePhase の write_set_ と API
    write intent の相互被覆が破れ、write-set membership または API 意図を復元できない
    ことを示す。write 完全性を認証できないため indeterminate に倒すが、これ自体は
    cycle ではないので serializable という純グラフ事実は変えない。検出源は
    writePhase の #if TRACE assert が emit する I 行。

    **同種の例外 = permutation_violations (段 5, D41):** validationPhase の write_set_
    sort が要素を欠落/複製させた (非 strict-weak-order comparator の UB) ことを示す。
    lock_coverage_violations と同じ理由で indeterminate に倒す — sort が破れると
    lock 獲得順序の前提自体が崩れ、その後の trace 版 stamp が信用できない。cycle は
    生まない。検出源は validationPhase の #if TRACE assert が emit する P 行。

    **framing_violations:** C が宣言した R/W 件数と実行数の不一致、または必須 E の
    欠落・重複を示す。frame が壊れた trace は R/W 辺が欠落している可能性があるため、
    DSG が acyclic でも serializable を認証しない。
    """
    orphan_reads: int = 0       # 非 genesis なのに producer の write が無い read
    version_dups: int = 0       # 同一 (key, ver) を異なる trx が産んだ
    dup_txids: int = 0          # 同一 txid が複数の C 行を持つ
    genesis_commits: int = 0    # commit が genesis 番兵 (1,0) 以下の trx (非物理)
    missing_txids: int = 0      # txid の欠番 (密連番保証の破れ = trx 丸ごと欠落)
    write_version_mismatch: int = 0  # W 行の版が C 行 commit と不一致の trx
    malformed_keys: int = 0     # key が小文字 hex 形式でない (表現揺れは競合辺を消す)
    framing_violations: int = 0  # C/E frame の件数・終端 integrity 違反
    framing_violation_details: List["TxnFramingViolation"] = field(
        default_factory=list)
    lock_coverage_violations: int = 0  # X 行の件数 (writePhase で lock 被覆が破れた write。D38)
    write_intent_violations: int = 0  # I 行の件数 (write_set_ と API write intent の被覆破れ。T-152)
    permutation_violations: int = 0  # P 行の件数 (validationPhase の sort が要素を欠落/複製。D41)
    permutation_violation_details: List["SortPermutationViolation"] = field(
        default_factory=list)
    expected_commits: Optional[int] = None  # trace 外 counter の期待 commit 数
    observed_commits: Optional[int] = None  # dedup 後の trace committed txn 数
    notes: List[str] = field(default_factory=list)
    # 非 wire field。result_to_dict() と receipt schema には投影しない。
    proof_surfaces: ProofSurfaceAssessment = field(
        default_factory=ProofSurfaceAssessment,
    )

    existence_violations: int = 0
    existence_violation_details: Optional[List[ExistenceViolation]] = None

    def clean(self) -> bool:
        commit_witness_clean = (
            (self.expected_commits is None and self.observed_commits is None)
            or (
                self.expected_commits is not None
                and self.observed_commits is not None
                and self.observed_commits == self.expected_commits
            )
        )
        return (self.orphan_reads == 0 and self.version_dups == 0
                and self.dup_txids == 0 and self.genesis_commits == 0
                and self.missing_txids == 0 and self.write_version_mismatch == 0
                and self.malformed_keys == 0 and self.framing_violations == 0
                and self.lock_coverage_violations == 0
                and self.write_intent_violations == 0
                and self.permutation_violations == 0
                and self.proof_surfaces.certification_gate_satisfied()
                and self.existence_violations == 0
                and commit_witness_clean)


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
    # A 行 (abort 要因の記録、段 8a/D48 positive control 計装) の要因別カウント。
    # 違反ではなく集計データ — integrity/verdict に不関与 (計装 patch を当てた
    # characterization run でのみ非空。通常 verify では常に空)。
    abort_reasons: Dict[str, int] = field(default_factory=dict)
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
