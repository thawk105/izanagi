# -*- coding: utf-8 -*-
"""source_digest — variant の identity を「コードの差」まで覆う preprocess 後ハッシュ (D23)。

Phase 3 では coder (LLM) が CCBench の EVOLVE-BLOCK 領域を書き換える。フラグだけで
決まっていた identity (cache_key / variant_id) を**ソース内容**まで覆わないと、
同じ genome で別コードの variant が同一キーを共有し偽 cache hit になる (規律2 への
直接攻撃)。本モジュールはその identity 核を計算する。

設計 (decisions D23、3 レンズ敵対レビューで確定):
- **方式 E:** 対象ソースから #include を除去し `g++ -E -P -nostdinc -Werror=undef
  -D...` で preprocess (= #if/#else 解決 + コメント除去) した出力を sha256。include を
  展開しないので小さい。defines = Options.cmake の `set(CCBENCH_<NAME> <v>
  CACHE ...)` デフォルト (CCBENCH_ 剥がし・クォート剥がし・空値 unset) を base に
  genome.flags で上書き。
- **道Y (digest==実枝の構造保証、D34 で -undef 廃止後):** 組込 builtin (__x86_64__ 等) を
  **実ビルドと同じく定義済みのまま** preprocess する (-undef を外した = D34/案A)。これで
  EVOLVE-BLOCK 内の生 `#ifdef __x86_64__`/`defined()` は digest 環境でも実枝を取り identity に
  正直に反映される (別挙動なら digest が動く = 偽 cache hit しない)。旧設計は -undef で
  builtin を消し「digest と実ビルドの乖離を hook が生 #ifdef 禁止で埋める」前提だったが、
  方針 A で hook payload 検査を削除した後この前提が崩れ builtin definedness の偽 cache hit が
  critical になった (2026-07-04 敵対検証) ため、identity 核側で実環境と揃えて根本封鎖した。
  本モジュールの -Werror=undef は #if/#elif が未定義マクロ (骨格 BACKOFF_FIXED 等の供給漏れ)
  を参照したら rc≠0 で捕える防壁として維持。非決定 builtin (__DATE__ 等) は churn するが
  偽 hit しない (毎回 cache-miss、正しさ不変)。
- **#include 死角の閉塞 (phase3.md blocking, 最小案):** preprocess 前に #include 行を
  除去する (環境非依存化) ため、正規化出力だけでは coder の #include 追加/差し替え
  (別ファイルを取り込む = バイナリが変わる) が identity 不変 = stock と alias になり、
  既存バイナリの偽 cache hit で**変更が一度もコンパイルされないまま certified 記録**
  される。対策 = **EVOLVE_BLOCK_SOURCES の #include 行集合が HEAD baseline と異なれば
  resolve で fails-closed abort** (`assert_includes_match_head`)。coder は EVOLVE-BLOCK の
  #if 枝しか触れず #include 追加は禁止 (phase3.md 閉じた領域制約) なので、include 行が
  HEAD と 1 行でも違えば逸脱 = 停止する。「行を identity に織り込んで許す」恒久案は却下:
  include **先ファイルの中身**は identity に乗らず、中身違いの新規 header で variant 間
  alias が残る (2026-07-03 敵対検証 high)。行集合を丸ごと HEAD 固定にすれば include 追加
  そのものを止めるのでこの穴ごと消える。template patch は #include を足さない
  (silo-backoff-fixed.patch) ので inert = 完了条件 1 (inert=stock cache-hit) を壊さない。
  computed include (`#if __has_include(...)`) は #include 行に現れない別死角だったが、
  T-148 の文脈ガード (下記) が出現を一律 fails-closed で止める (骨格・stock は不使用ゆえ
  skeleton 抽出不要。D34 known-limitation の解消)。
- **マクロ文脈死角の閉塞 (T-148):** TU 注入マクロ (`cc/silo/*_silo.cc:3` の
  `#define GLOBAL_VALUE_DEFINE`) に条件づけられた枝は、単体 preprocess の素文脈では dead に
  なり枝内編集が digest に不可視 = stock 偽 alias だった (`-Werror=undef` は `#ifdef`/
  `defined()` を捕えない)。対策は二層: (1) CONTEXT_MACROS に登録済みのマクロは「素 + define」
  の**両文脈**で preprocess し両枝を identity に織り込む (compute/baseline/_trace_pair_diff。
  builtin definedness の D34/案A と対で、既知の乖離源は digest 側で実枝被覆)。(2) 条件指令が
  参照するマクロが defines ∪ 先行する #define ∪ CONTEXT_MACROS ∪ builtin (-dM) に閉じるか
  検査し、未知マクロと __has_include は resolve で fails-closed abort
  (assert_conditional_macros_covered。次の GLOBAL_VALUE_DEFINE 型を沈黙させない)。(3) digest の
  -D 集合自体を**実 TU 供給集合**へ揃える (parse_supplied_macros + PLATFORM_MACROS +
  BUILD_FLAGS) — cmake CACHE 全体を一律 -D すると他 protocol 専用マクロ (DEBUG_MSG 等) が
  digest だけ定義済みになり、`#ifdef` で枝が逆転する (段 6 レビュー B、2026-07-28)。
  **正直に (駆動点):** ガードを駆動するのは resolve() であって compute()/baseline()/src_token()
  単体ではない。legacy `buildcache.build(src_token=None)` は src_token() を直接呼ぶため、その
  経路のガードは build 出口の `_recheck_src_token` (resolve を通る) まで遅れる。現行 driver
  (S1/S6/S8a・loop・p3_s4_loop) は patch 適用中に resolve() した token を評価へ渡す。
- **後方互換:** working-tree の preprocess が HEAD baseline と一致する (= stock/inert) なら
  src トークンを "stock" に正規化し pre-image から省く → silo 8 genome の旧 id を温存。
- **fails-closed:** identity を決める計算は best-effort skip しない (buildcache の commit/nm
  照合と違う)。g++ 不在・rc≠0・git show 失敗・allowlist 外改変は全て RuntimeError で停止。
"""
from __future__ import annotations
import difflib
import hashlib
import os
import re
import subprocess
from dataclasses import dataclass, field
from typing import Dict, Iterable, List, Mapping, Optional

from ..verifier.model import (
    CompiledProtocolSourceSnapshot,
    capture_compiled_protocol_source_snapshot,
)
from .model import Genome


def effective_gate_witness_requirement(genome: Genome, requested: bool) -> bool:
    """Return the effective D5 requirement for one candidate."""
    if type(requested) is not bool:
        raise TypeError("require_gate_witness must be bool")
    return requested or (genome.protocol == "silo" and
                         genome.flags.get("SILO_ORDER_VARIANT", 0) != 0)

# ---- 対象集合 (kickoff の固定集合。動的なマーカー走査はマーカー導入後に格上げ) ----
OPTIONS_CMAKE = "cmake/Options.cmake"
# cc/silo/transaction.cc = 後続段 3 (D38) の lock 経路。編集面への追加は段 5 (D38 決定5) で
# auditor live 機械 4 点 (test_lock_path_edit_surface_requires_auditor_live) の gate 下に解禁。
# cc/mocc/transaction.cc = T-755 の trace-hook 目的だけの編集面拡張。D38 の auditor-live 前提は
# test_campaign.py:10394-10412 の cc/silo/transaction.cc リテラル検査に限られ、mocc には適用しない。
# 段 4 の coder loop (p3_s4_loop.SOURCE_REL) はまだ backoff.hh 単一マーカーのみを駆動する —
# ここでの追加は identity/allowlist 層の地ならしで、実マーケット化 (template patch) は別タスク。
EVOLVE_BLOCK_SOURCES = (
    "include/backoff.hh", "cc/silo/transaction.cc", "cc/mocc/transaction.cc")
# Defines are source-owned when the identity pre-image spans multiple protocols.
# ``None`` means the genome protocol (the universal backoff header), while an
# explicit value selects the CMakeLists belonging to that source's protocol.
EVOLVE_BLOCK_SOURCE_PROTOCOLS = {
    "include/backoff.hh": None,
    "cc/silo/transaction.cc": "silo",
    "cc/mocc/transaction.cc": "mocc",
}
# template patch (silo-backoff-fixed.patch) が touch するファイル。working-tree の
# tracked 改変がこれを超えたら coder の編集面が EVOLVE-BLOCK を逸脱した印 → 停止。
ALLOWLIST = frozenset({
    "cmake/Options.cmake", "include/backoff.hh", "cc/silo/transaction.cc",
    "cc/mocc/transaction.cc",
})

STOCK = "stock"        # 後方互換: working-tree==HEAD baseline のときの src トークン
SOURCE_EVIDENCE_SCHEMA = "source-evidence/v1"
COMPILED_PROTOCOL_SOURCE_SNAPSHOT_SCHEMA = (
    "compiled-protocol-source-snapshot/v1"
)
EMPTY_TRACKED_DIFF_SHA256 = hashlib.sha256(b"").hexdigest()
SOURCE_BINDING_DIRECTORY = "source-bindings"


def verification_variant_id(genome: Genome, source_token: str = STOCK) -> str:
    """SourceEvidence と verifier receipt が共有する variant identity。"""
    suffix = "" if source_token == STOCK else f"|src={source_token}"
    return hashlib.sha256(
        f"{genome.canonical()}{suffix}".encode("utf-8")
    ).hexdigest()[:12]


def _is_sha256(value: object) -> bool:
    if type(value) is not str or len(value) != 64:
        return False
    try:
        int(value, 16)
    except ValueError:
        return False
    return value == value.lower()


def serialize_compiled_protocol_source_snapshot(
        snapshot: CompiledProtocolSourceSnapshot,
) -> dict[str, object]:
    """Project one immutable proof-source snapshot into an exact JSON body."""
    if (type(snapshot) is not CompiledProtocolSourceSnapshot
            or type(snapshot.protocol) is not str or not snapshot.protocol
            or type(snapshot.ccbench_root) is not str
            or not os.path.isabs(snapshot.ccbench_root)
            or (snapshot.gate_d5_sources is not None
                and (type(snapshot.gate_d5_sources) is not tuple
                     or len(snapshot.gate_d5_sources) != 4
                     or any(type(item) is not str
                            for item in snapshot.gate_d5_sources[:3])
                     or type(snapshot.gate_d5_sources[3]) is not bool))
            or (snapshot.normalized_sources is not None
                and (type(snapshot.normalized_sources) is not tuple
                     or any(type(item) is not str
                            for item in snapshot.normalized_sources)))):
        raise ValueError("CompiledProtocolSourceSnapshot が直列化不能")
    body = {
        "schema": COMPILED_PROTOCOL_SOURCE_SNAPSHOT_SCHEMA,
        "protocol": snapshot.protocol,
        "ccbench_root": snapshot.ccbench_root,
        "normalized_sources": (
            None if snapshot.normalized_sources is None
            else list(snapshot.normalized_sources)
        ),
    }
    if snapshot.gate_d5_sources is not None:
        body["gate_d5_sources"] = list(snapshot.gate_d5_sources)
    return body


def deserialize_compiled_protocol_source_snapshot(
        value: object,
) -> CompiledProtocolSourceSnapshot:
    """Rebuild an exact proof-source snapshot without reading its source tree."""
    required = {
        "schema", "protocol", "ccbench_root", "normalized_sources",
    }
    if type(value) is not dict or set(value) not in (
            required, required | {"gate_d5_sources"}):
        raise ValueError("proof source snapshot key 集合が不正")
    normalized = value["normalized_sources"]
    gate_sources = value.get("gate_d5_sources")
    if (value["schema"] != COMPILED_PROTOCOL_SOURCE_SNAPSHOT_SCHEMA
            or type(value["protocol"]) is not str or not value["protocol"]
            or type(value["ccbench_root"]) is not str
            or not os.path.isabs(value["ccbench_root"])
            or ("gate_d5_sources" in value
                and (type(gate_sources) is not list or len(gate_sources) != 4
                     or any(type(item) is not str for item in gate_sources[:3])
                     or type(gate_sources[3]) is not bool))
            or (normalized is not None
                and (type(normalized) is not list
                     or any(type(item) is not str for item in normalized)))):
        raise ValueError("proof source snapshot binding が不正")
    return CompiledProtocolSourceSnapshot(
        protocol=value["protocol"],
        ccbench_root=value["ccbench_root"],
        normalized_sources=(
            None if normalized is None else tuple(normalized)
        ),
        gate_d5_sources=(
            None if gate_sources is None else tuple(gate_sources)
        ),
    )


@dataclass(frozen=True, slots=True)
class SourceEvidence:
    """One source-root-bound evidence projection for build admission.

    ``source_root`` records which checkout was inspected, while ``tracked_clean``, the tracked
    diff digest, and ``tracked_paths`` are derived from one status snapshot.  The non-wire proof
    snapshot freezes the compiled-source predicate input for the build/verifier path.  The checkout
    remains mutable, so buildcache must still re-resolve and compare both projections at its exit.
    """

    schema_version: str
    source_root: str
    ccbench_commit: str
    genome_sha256: str
    src_token: str
    source_bytes_sha256: str
    tracked_clean: bool
    tracked_diff_sha256: str
    tracked_paths: tuple[str, ...]
    # Build/verifier の同一プロセス内だけで使う非 wire 束縛。receipt key は増やさない。
    proof_source_snapshot: Optional[CompiledProtocolSourceSnapshot] = field(
        default=None, repr=False, compare=False,
    )
    verification_variant: Optional[str] = field(
        default=None, repr=False, compare=False,
    )

    _KEYS = frozenset({
        "schema", "source_root", "ccbench_commit", "genome_sha256", "src_token",
        "source_bytes_sha256", "tracked_clean", "tracked_diff_sha256", "tracked_paths",
    })

    def __post_init__(self) -> None:
        if self.schema_version != SOURCE_EVIDENCE_SCHEMA:
            raise ValueError("SourceEvidence schema_version が不正")
        if type(self.source_root) is not str or not os.path.isabs(self.source_root):
            raise ValueError("SourceEvidence source_root は absolute path が必要")
        if type(self.ccbench_commit) is not str or not self.ccbench_commit:
            raise ValueError("SourceEvidence ccbench_commit が不正")
        if not _is_sha256(self.genome_sha256):
            raise ValueError("SourceEvidence genome_sha256 が不正")
        if self.src_token != STOCK and not _is_sha256(self.src_token):
            raise ValueError("SourceEvidence src_token が不正")
        if not _is_sha256(self.source_bytes_sha256):
            raise ValueError("SourceEvidence source_bytes_sha256 が不正")
        if type(self.tracked_clean) is not bool:
            raise ValueError("SourceEvidence tracked_clean は exact bool が必要")
        if not _is_sha256(self.tracked_diff_sha256):
            raise ValueError("SourceEvidence tracked_diff_sha256 が不正")
        if (type(self.tracked_paths) is not tuple
                or any(type(path) is not str or not path for path in self.tracked_paths)
                or self.tracked_paths != tuple(sorted(set(self.tracked_paths)))):
            raise ValueError("SourceEvidence tracked_paths は sorted unique tuple[str, ...] が必要")
        if self.tracked_clean != (not self.tracked_paths):
            raise ValueError("SourceEvidence tracked_clean と tracked_paths が不整合")
        if self.tracked_clean != (self.tracked_diff_sha256 == EMPTY_TRACKED_DIFF_SHA256):
            raise ValueError("SourceEvidence tracked_clean と tracked diff digest が不整合")
        if (self.proof_source_snapshot is not None
                and type(self.proof_source_snapshot)
                is not CompiledProtocolSourceSnapshot):
            raise ValueError("SourceEvidence proof source snapshot が不正")
        if (self.proof_source_snapshot is not None
                and self.proof_source_snapshot.ccbench_root != self.source_root):
            raise ValueError("SourceEvidence proof source snapshot root が不一致")
        if (self.verification_variant is not None
                and (type(self.verification_variant) is not str
                     or not self.verification_variant)):
            raise ValueError("SourceEvidence verification variant が不正")

    def as_receipt(self) -> dict[str, object]:
        return {
            "schema": self.schema_version,
            "source_root": self.source_root,
            "ccbench_commit": self.ccbench_commit,
            "genome_sha256": self.genome_sha256,
            "src_token": self.src_token,
            "source_bytes_sha256": self.source_bytes_sha256,
            "tracked_clean": self.tracked_clean,
            "tracked_diff_sha256": self.tracked_diff_sha256,
            "tracked_paths": list(self.tracked_paths),
        }

    def _bind_runtime_verification(
            self, *,
            proof_source_snapshot: CompiledProtocolSourceSnapshot,
            verification_variant: str,
    ) -> "SourceEvidence":
        """Bind missing non-wire fields once while preserving this instance.

        Production ``resolve_evidence()`` supplies both fields at construction.
        In-process legacy/test resolvers may omit them; the pipeline completes
        only those runtime fields before forwarding this exact object to the
        capability resolver and both build APIs.  An existing conflicting
        binding is never replaced.
        """
        if type(proof_source_snapshot) is not CompiledProtocolSourceSnapshot:
            raise ValueError("SourceEvidence proof source snapshot が不正")
        if proof_source_snapshot.ccbench_root != self.source_root:
            raise ValueError("SourceEvidence proof source snapshot root が不一致")
        if type(verification_variant) is not str or not verification_variant:
            raise ValueError("SourceEvidence verification variant が不正")
        if (self.proof_source_snapshot is not None
                and self.proof_source_snapshot != proof_source_snapshot):
            raise ValueError("SourceEvidence proof source snapshot が既存束縛と不一致")
        if (self.verification_variant is not None
                and self.verification_variant != verification_variant):
            raise ValueError("SourceEvidence verification variant が既存束縛と不一致")
        if self.proof_source_snapshot is None:
            object.__setattr__(
                self, "proof_source_snapshot", proof_source_snapshot,
            )
        if self.verification_variant is None:
            object.__setattr__(
                self, "verification_variant", verification_variant,
            )
        if (self.proof_source_snapshot != proof_source_snapshot
                or self.verification_variant != verification_variant):
            raise ValueError("SourceEvidence runtime binding が競合した")
        return self

    @classmethod
    def from_receipt(cls, value: object) -> "SourceEvidence":
        if not isinstance(value, Mapping) or set(value) != cls._KEYS:
            got = sorted(repr(key) for key in value) if isinstance(value, Mapping) else type(value).__name__
            raise ValueError(
                f"SourceEvidence receipt key 集合が不正: expected={sorted(cls._KEYS)} got={got}"
            )
        paths = value["tracked_paths"]
        if type(paths) is not list or any(type(path) is not str for path in paths):
            raise ValueError("SourceEvidence receipt tracked_paths は list[str] が必要")
        return cls(
            schema_version=value["schema"],
            source_root=value["source_root"],
            ccbench_commit=value["ccbench_commit"],
            genome_sha256=value["genome_sha256"],
            src_token=value["src_token"],
            source_bytes_sha256=value["source_bytes_sha256"],
            tracked_clean=value["tracked_clean"],
            tracked_diff_sha256=value["tracked_diff_sha256"],
            tracked_paths=tuple(paths),
        )


@dataclass(frozen=True, slots=True)
class EffectiveDefineResolution:
    """Source-owner-aware CMake cache-to-TU define resolution.

    This is a static rederivation from captured CMake source. It is not a
    post-configure compiler command and does not claim exact build input.
    """

    source_rel: str
    owner_protocol: str
    supplied_macros: frozenset[str]
    bare_macros: frozenset[str]
    cache_by_tu_macro: tuple[tuple[str, str], ...]
    effective_values: tuple[tuple[str, str], ...]

    def cache_name(self, macro: str) -> str | None:
        return dict(self.cache_by_tu_macro).get(macro)

    def effective_value(self, macro: str) -> str | None:
        return dict(self.effective_values).get(macro)

# TU 注入マクロ (T-148): -D でなく取り込み側 TU の #define で供給されるマクロ。単体 preprocess の
# 素文脈では常に未定義 = 条件枝が dead になり、枝内編集が digest に不可視 (stock 偽 alias) になる。
# ここに登録したマクロは compute/baseline/_trace_pair_diff が「素 + define」の両文脈で preprocess し
# 両枝を identity に織り込む。未登録の同型マクロは assert_conditional_macros_covered が fails-closed
# で止める (登録漏れが沈黙しない)。現状 GLOBAL_VALUE_DEFINE のみ (cc/silo/*_silo.cc:3 が #define し
# include/backoff.hh:123 が #ifdef 参照)。2 個以上に増やすときは結合枝 (#if defined(A)&&defined(B))
# の被覆に組合せ文脈が要るか再設計する (現状は単一マクロずつの文脈で十分)。
CONTEXT_MACROS = ("GLOBAL_VALUE_DEFINE",)

# These macros are not supplied by the current repository at all.  Unlike
# CONTEXT_MACROS, this is not a TU-injected context: every use remains in the
# false branch, and the registry is revalidated against the checkout before it
# is added to the conditional-coverage known set.
PROVEN_REPO_ABSENT_MACROS = frozenset({"MQLOCK"})

# 実 TU に無条件で入るがマクロ供給表に現れないもの (ProtocolHelpers.cmake が
# `CMAKE_SYSTEM_NAME STREQUAL "Linux"` で `target_compile_definitions(... Linux)` する)。
# 計測層は Linux 専有 (D13/環境契約) なので digest 側も定義済みで揃える。値なしの純 definedness。
PLATFORM_MACROS = {"Linux": "1"}
# 実ビルドのコンパイル環境フラグ。digest がこれを外したまま preprocess/照会すると条件枝が
# 実ビルドと逆転する (段 6 レビュー、いずれも g++-12 実測):
# - `-std=c++20`: cmake/CompileOptions.cmake の `CMAKE_CXX_STANDARD 20` + `CXX_EXTENSIONS OFF`。
#   外すと `#if __cplusplus >= 202002L` が逆転し、認識される指令 (`#elifdef` 等) も変わる。
# - `-O3 -DNDEBUG`: buildcache が `-DCMAKE_BUILD_TYPE=Release` で configure し、CompileOptions.cmake
#   は RELEASE フラグを上書きしないため GNU 既定のこの 2 つが実 TU に必ず入る。外すと
#   `__NO_INLINE__` / `__OPTIMIZE__` / `NDEBUG` の definedness が反転する。
BUILD_FLAGS = ("-std=c++20", "-O3", "-DNDEBUG")
# digest と実ビルドで同一に評価される組込演算子 (同一 cxx・同一 std なので乖離しない) =
# 受理してよい。`__has_include` 系だけは header 探索パスに依存し digest が -nostdinc で
# 常に 0 に倒れるため別扱い (fails-closed、下記ガード)。
KNOWN_HAS_OPERATORS = frozenset({
    "__has_builtin", "__has_attribute", "__has_cpp_attribute", "__has_c_attribute",
    "__has_feature", "__has_extension"})
INCLUDE_PROBE_OPERATORS = ("__has_include_next", "__has_include")

_SET_RE = re.compile(
    r"set\(\s*CCBENCH_(\w+)\s+(.*?)\s+CACHE\s+STRING", re.IGNORECASE)
_INCLUDE_RE = re.compile(r"(?m)^[ \t]*#[ \t]*include\b.*$")
_COND_DIRECTIVE_RE = re.compile(
    r"(?m)^[ \t]*#[ \t]*(?:if|ifdef|ifndef|elif|elifdef|elifndef)\b(.*)$")
_DEFINE_RE = re.compile(r"(?m)^[ \t]*#[ \t]*define[ \t]+(\w+)[^\n]*")
_IDENT_RE = re.compile(r"\b[A-Za-z_]\w*\b")
_RAW_STRING_RE = re.compile(r'(?:u8|u|U|L)?R"')
# トークン貼り合わせ (`##` と digraph `%:%:`)。マクロ本体でこれを許すと、走査が literal で
# 探している名前を分割して組み立てられる (`__has_inc##lude`)。貼り合わせなしに新しい識別子を
# 作る手段はないので、ここを止めれば同型の難読化はまとめて閉じる。
_TOKEN_PASTE_RE = re.compile(r"##|%:%:")
_CHAR_PREFIXES = ("u8", "u", "U", "L")
# `__has_builtin(__builtin_expect)` の引数は builtin 名や属性名でマクロ参照ではない。
# 演算子ごと式から落としてから識別子を拾う (落とさないと引数を未知マクロと誤判定する)。
_HAS_OP_CALL_RE = re.compile(r"\b__has_\w+\s*\([^()]*\)")
# CMake が TU へ渡すマクロ供給表の行 (`NAME=${CCBENCH_NAME}`)。universal は Options.cmake の
# ccbench_universal_definitions()、protocol 固有は cc/<protocol>/CMakeLists.txt の OPTIONS。
_UNIVERSAL_FN_RE = re.compile(
    r"function\(\s*ccbench_universal_definitions.*?endfunction\(\)", re.DOTALL)
_SUPPLY_RE = re.compile(
    r"([A-Za-z_]\w*)\s*=\s*\$\{CCBENCH_([A-Za-z_]\w*)\}\Z")
_OPTION_IDENT_RE = re.compile(r"[A-Za-z_]\w*\Z")
_CMAKE_SECTION_NAMES = frozenset({"SOURCES", "WORKLOADS", "OPTIONS"})
_PROTOCOL_CMAKE = "cc/{protocol}/CMakeLists.txt"
_BUILTIN_MACRO_CACHE: Dict[tuple, frozenset] = {}
_CPP_ENV_PREFIX_CACHE: Dict[tuple, str] = {}


def _ccbench_dir() -> str:
    here = os.path.dirname(os.path.abspath(__file__))     # <repo>/orchestrator/campaign
    repo = os.path.dirname(os.path.dirname(here))         # <repo>
    return os.path.join(repo, "external", "ccbench")


def _strip_cmake_comments(text: str) -> str:
    """CMake のコメントを空白化し、文字列・bracket argument・改行を保持する。

    Bracket argument は quote 外でだけ開始する。したがって quoted argument 内の
    ``[[maybe_unused]]`` を bracket と誤認して後続 command を隠すことはない。
    """
    out: List[str] = []
    i = 0
    quoted = False
    escaped = False
    comment = False
    while i < len(text):
        c = text[i]
        if comment:
            if c == "\n":
                out.append(c)
                comment = False
            else:
                out.append(" ")
            i += 1
            continue
        if quoted:
            out.append(c)
            if escaped:
                escaped = False
            elif c == "\\":
                escaped = True
            elif c == '"':
                quoted = False
            i += 1
            continue
        bracket = _cmake_bracket(text, i)
        if bracket is not None:
            opener_len, closer = bracket
            end = text.find(closer, i + opener_len)
            if end < 0:
                raise RuntimeError(
                    "source_digest: CMake bracket argument/comment が未終端 — "
                    "マクロ供給表を確定できないため fails-closed (T-148)"
                )
            out.append(text[i:end + len(closer)])
            i = end + len(closer)
            continue
        if c == '"':
            quoted = True
            out.append(c)
        elif c == "#":
            bracket_comment = _cmake_bracket(text, i + 1)
            if bracket_comment is not None:
                opener_len, closer = bracket_comment
                end = text.find(closer, i + 1 + opener_len)
                if end < 0:
                    raise RuntimeError(
                        "source_digest: CMake bracket comment が未終端 — "
                        "マクロ供給表を確定できないため fails-closed (T-148)"
                    )
                segment = text[i:end + len(closer)]
                out.extend("\n" if char == "\n" else " " for char in segment)
                i = end + len(closer)
                continue
            comment = True
            out.append(" ")
        else:
            out.append(c)
        i += 1
    if quoted:
        raise RuntimeError(
            "source_digest: CMake 文字列が未終端 — マクロ供給表を確定できないため "
            "fails-closed (T-148)"
        )
    return "".join(out)


def _scan_cmake_parentheses(text: str, open_pos: int, label: str) -> tuple[str, int]:
    """``open_pos`` の括弧を balanced scan し、内側と閉じ括弧直後を返す。"""
    if open_pos >= len(text) or text[open_pos] != "(":
        raise RuntimeError(f"source_digest: {label} の括弧開始位置が不正 → fails-closed")
    depth = 1
    quoted = False
    escaped = False
    i = open_pos + 1
    while i < len(text):
        c = text[i]
        if quoted:
            if escaped:
                escaped = False
            elif c == "\\":
                escaped = True
            elif c == '"':
                quoted = False
        elif c == '"':
            quoted = True
        elif (bracket := _cmake_bracket(text, i)) is not None:
            opener_len, closer = bracket
            end = text.find(closer, i + opener_len)
            if end < 0:
                raise RuntimeError(
                    f"source_digest: {label} の bracket argument が未終端 — "
                    "マクロ供給表を確定できないため fails-closed (T-148)"
                )
            i = end + len(closer)
            continue
        elif c == "(":
            depth += 1
        elif c == ")":
            depth -= 1
            if depth == 0:
                return text[open_pos + 1:i], i + 1
        i += 1
    raise RuntimeError(
        f"source_digest: {label} の括弧が不整合 (閉じ括弧なし) — "
        "マクロ供給表を確定できないため fails-closed (T-148)"
    )


def _cmake_calls(text: str, name: str) -> List[str]:
    """コメントを除いた CMake text から ``name(...)`` の引数を抽出する。"""
    clean = _strip_cmake_comments(text)
    # quoted message()/string() payload に含まれる ``name(...)`` は CMake
    # command ではない。検索面だけ文字列中身を空白化し、body の実文字列は
    # tokenizer 用に clean 側から取り出す。
    scan = list(clean)
    quoted = False
    escaped = False
    index = 0
    while index < len(clean):
        char = clean[index]
        if quoted:
            if escaped:
                scan[index] = " "
                escaped = False
            elif char == "\\":
                scan[index] = " "
                escaped = True
            elif char == '"':
                quoted = False
            else:
                scan[index] = " "
        elif char == '"':
            quoted = True
        elif (bracket := _cmake_bracket(clean, index)) is not None:
            opener_len, closer = bracket
            end = clean.find(closer, index + opener_len)
            if end < 0:
                raise RuntimeError(
                    "source_digest: CMake bracket argument が未終端 — "
                    "マクロ供給表を確定できないため fails-closed (T-148)"
                )
            for bracket_index in range(index, end + len(closer)):
                if clean[bracket_index] != "\n":
                    scan[bracket_index] = " "
            index = end + len(closer)
            continue
        elif char == "#":
            # Comments were already blanked, but retain this guard for direct
            # callers that pass a partially normalized snippet.
            scan[index] = " "
        index += 1
    call_re = re.compile(rf"\b{re.escape(name)}\s*\(", re.IGNORECASE)
    scan_text = "".join(scan)
    calls: List[str] = []
    for match in call_re.finditer(scan_text):
        open_pos = clean.find("(", match.start(), match.end())
        body, _ = _scan_cmake_parentheses(clean, open_pos, name)
        calls.append(body)
    return calls


def _cmake_tokens(text: str) -> List[str]:
    """CMake の簡易 argument tokenizer。コメント・引用符不整合は停止する。"""
    tokens: List[str] = []
    i = 0
    n = len(text)
    while i < n:
        while i < n and text[i].isspace():
            i += 1
        if i >= n:
            break
        if text[i] == "#":
            while i < n and text[i] != "\n":
                i += 1
            continue
        token: List[str] = []
        while i < n and not text[i].isspace():
            c = text[i]
            bracket = _cmake_bracket(text, i)
            if bracket is not None:
                opener_len, closer = bracket
                end = text.find(closer, i + opener_len)
                if end < 0:
                    raise RuntimeError(
                        "source_digest: CMake bracket argument が未終端 — "
                        "供給表を確定できないため fails-closed (T-148)"
                    )
                token.append(text[i + opener_len:end])
                i = end + len(closer)
                continue
            if c == '"':
                i += 1
                escaped = False
                while i < n:
                    c = text[i]
                    if escaped:
                        token.append(c)
                        escaped = False
                    elif c == "\\":
                        escaped = True
                    elif c == '"':
                        i += 1
                        break
                    else:
                        token.append(c)
                    i += 1
                else:
                    raise RuntimeError(
                        "source_digest: CMake argument の引用符が未終端 — "
                        "供給表を確定できないため fails-closed (T-148)"
                    )
                continue
            token.append(c)
            i += 1
        if token:
            tokens.append("".join(token))
    return tokens


def _add_supply_detail(
        names: set[str], bare_names: set[str], cache_names: Dict[str, str],
        left: str, right: str | None, label: str,
) -> None:
    """供給名の重複・裸/KV 衝突を fails-closed で検査して登録する。"""
    if right is None:
        if left in cache_names:
            raise RuntimeError(
                f"source_digest: {label} で供給 macro {left!r} が裸/KV 混在 — "
                "供給値を一意に確定できないため fails-closed (T-148)"
            )
        bare_names.add(left)
    else:
        if left in bare_names:
            raise RuntimeError(
                f"source_digest: {label} で供給 macro {left!r} が裸/KV 混在 — "
                "供給値を一意に確定できないため fails-closed (T-148)"
            )
        previous = cache_names.get(left)
        if previous is not None and previous != right:
            raise RuntimeError(
                f"source_digest: {label} で供給 macro {left!r} の cache 名が衝突 "
                f"({previous!r} / {right!r}) → fails-closed (T-148)"
            )
        cache_names[left] = right
    names.add(left)


def _parse_supply_tokens(
        tokens: List[str], label: str,
) -> tuple[set[str], set[str], Dict[str, str]]:
    """供給 token 列から (全名, 裸名, 左辺→cache 名) を作る。"""
    names: set[str] = set()
    bare_names: set[str] = set()
    cache_names: Dict[str, str] = {}
    i = 0
    while i < len(tokens):
        token = tokens[i]
        match = _SUPPLY_RE.fullmatch(token)
        if match:
            _add_supply_detail(
                names, bare_names, cache_names, match.group(1), match.group(2), label,
            )
            i += 1
            continue
        if _OPTION_IDENT_RE.fullmatch(token):
            if i + 2 < len(tokens) and tokens[i + 1] == "=":
                rhs = tokens[i + 2]
                rhs_match = re.fullmatch(r"\$\{CCBENCH_([A-Za-z_]\w*)\}", rhs)
                if rhs_match:
                    _add_supply_detail(
                        names, bare_names, cache_names, token, rhs_match.group(1), label,
                    )
                    i += 3
                    continue
                raise RuntimeError(
                    f"source_digest: {label} の option {token!r} に CCBENCH cache 右辺がない "
                    "→ fails-closed (T-148)"
                )
            if i + 1 < len(tokens) and tokens[i + 1].startswith("="):
                rhs = tokens[i + 1][1:]
                rhs_match = re.fullmatch(r"\$\{CCBENCH_([A-Za-z_]\w*)\}", rhs)
                if rhs_match:
                    _add_supply_detail(
                        names, bare_names, cache_names, token, rhs_match.group(1), label,
                    )
                    i += 2
                    continue
                raise RuntimeError(
                    f"source_digest: {label} の option {token!r} に CCBENCH cache 右辺がない "
                    "→ fails-closed (T-148)"
                )
            _add_supply_detail(names, bare_names, cache_names, token, None, label)
            i += 1
            continue
        raise RuntimeError(
            f"source_digest: {label} の option token {token!r} が未対応 — "
            "実 TU のマクロ供給を確定できないため fails-closed (T-148)"
        )
    return names, bare_names, cache_names


def _parse_universal_macro_details(
        options_text: str,
) -> tuple[set[str], set[str], Dict[str, str]]:
    """universal definitions function の供給 call から供給詳細を取る。"""
    clean = _strip_cmake_comments(options_text)
    match = re.search(
        r"\bfunction\s*\(\s*ccbench_universal_definitions\b",
        clean, re.IGNORECASE,
    )
    if not match:
        raise RuntimeError(
            "source_digest: Options.cmake に ccbench_universal_definitions() が見つからない — "
            "実 TU のマクロ供給集合を確定できないため fails-closed (T-148)"
        )
    open_pos = clean.find("(", match.start(), match.end())
    _, body_end = _scan_cmake_parentheses(
        clean, open_pos, "ccbench_universal_definitions function",
    )
    end_match = re.search(r"\bendfunction\s*\(", clean[body_end:], re.IGNORECASE)
    if not end_match:
        raise RuntimeError(
            "source_digest: ccbench_universal_definitions() の endfunction() がない — "
            "供給表を確定できないため fails-closed (T-148)"
        )
    body = clean[body_end:body_end + end_match.start()]
    names: set[str] = set()
    bare_names: set[str] = set()
    cache_names: Dict[str, str] = {}

    def merge(parsed: tuple[set[str], set[str], Dict[str, str]]) -> None:
        for left in parsed[0]:
            _add_supply_detail(
                names, bare_names, cache_names, left, parsed[2].get(left),
                "ccbench_universal_definitions()",
            )

    for set_body in _cmake_calls(body, "set"):
        tokens = _cmake_tokens(set_body)
        if not tokens:
            continue
        try:
            end = tokens.index("PARENT_SCOPE")
        except ValueError:
            continue
        payload = [token for token in tokens[1:end] if not token.startswith("${")]
        merge(_parse_supply_tokens(payload, "ccbench_universal_definitions()"))

    visibility = {"PRIVATE", "PUBLIC", "INTERFACE"}
    for definitions_body in _cmake_calls(body, "target_compile_definitions"):
        tokens = _cmake_tokens(definitions_body)
        if not tokens:
            continue
        payload = [
            token for index, token in enumerate(tokens)
            if index > 0
            and not token.startswith("${")
            and token.upper() not in visibility
        ]
        if payload:
            merge(_parse_supply_tokens(payload, "ccbench_universal_definitions()"))
    return names, bare_names, cache_names


def _parse_protocol_macro_details(
        protocol_cmake_text: str,
) -> tuple[set[str], set[str], Dict[str, str]]:
    """protocol CMake の OPTIONS 範囲だけから供給詳細を取る。"""
    clean = _strip_cmake_comments(protocol_cmake_text)
    names: set[str] = set()
    bare_names: set[str] = set()
    cache_names: Dict[str, str] = {}
    for body in _cmake_calls(clean, "ccbench_add_protocol"):
        tokens = _cmake_tokens(body)
        if not tokens or not _OPTION_IDENT_RE.fullmatch(tokens[0]):
            raise RuntimeError(
                "source_digest: ccbench_add_protocol() の protocol 名が不正 — "
                "供給表を確定できないため fails-closed (T-148)"
            )
        option_positions = [
            index for index, token in enumerate(tokens)
            if token.upper() == "OPTIONS"
        ]
        if len(option_positions) > 1:
            raise RuntimeError(
                "source_digest: ccbench_add_protocol() に OPTIONS が複数ある — "
                "範囲を一意に確定できないため fails-closed (T-148)"
            )
        option_start = option_positions[0] if option_positions else None
        outside = tokens if option_start is None else tokens[:option_start]
        if option_start is not None:
            next_sections = [
                index for index in range(option_start + 1, len(tokens))
                if tokens[index].upper() in _CMAKE_SECTION_NAMES
            ]
            option_end = min(next_sections) if next_sections else len(tokens)
            outside = tokens[:option_start] + tokens[option_end:]
            option_tokens = tokens[option_start + 1:option_end]
            parsed = _parse_supply_tokens(option_tokens, "ccbench_add_protocol OPTIONS")
            for left in parsed[0]:
                _add_supply_detail(
                    names, bare_names, cache_names, left, parsed[2].get(left),
                    "ccbench_add_protocol OPTIONS",
                )
        for index, token in enumerate(outside):
            if _SUPPLY_RE.fullmatch(token):
                raise RuntimeError(
                    f"source_digest: ccbench_add_protocol() の OPTIONS 外に供給形 token "
                    f"{token!r} — fails-closed (T-148)"
                )
            if (_OPTION_IDENT_RE.fullmatch(token) and index + 2 < len(outside)
                    and outside[index + 1] == "="
                    and re.fullmatch(r"\$\{CCBENCH_[A-Za-z_]\w*\}", outside[index + 2])):
                raise RuntimeError(
                    "source_digest: ccbench_add_protocol() の OPTIONS 外に CCBENCH "
                    "供給形 token — fails-closed (T-148)"
                )
    return names, bare_names, cache_names


def _parse_supplied_macro_details(
        options_text: str, protocol_cmake_text: str,
) -> tuple[frozenset[str], frozenset[str], Dict[str, str]]:
    """universal/protocol の供給名、裸名、左辺→cache 名を返す。"""
    universal = _parse_universal_macro_details(options_text)
    protocol = _parse_protocol_macro_details(protocol_cmake_text)
    names = universal[0] | protocol[0]
    bare_names = universal[1] | protocol[1]
    cache_names = dict(universal[2])
    for left, right in protocol[2].items():
        previous = cache_names.get(left)
        if previous is not None and previous != right:
            raise RuntimeError(
                f"source_digest: macro {left!r} の universal/protocol cache 名が衝突 "
                f"({previous!r} / {right!r}) → fails-closed (T-148)"
            )
        cache_names[left] = right
    if not names:
        raise RuntimeError(
            "source_digest: マクロ供給表が空 — CMake 構造が変わった疑い → "
            "fails-closed (T-148)"
        )
    return frozenset(names), frozenset(bare_names), cache_names


def parse_options_defaults(options_text: str) -> Dict[str, str]:
    """Options.cmake の `set(CCBENCH_<NAME> <v> CACHE STRING ...)` から既定値辞書を作る。

    CCBENCH_ 接頭辞を剥がす (ソース内マクロ名と一致)。値のクォートを剥がし、剥がして
    空 ("") は cmake の remove_definitions=未定義 意味論に合わせ **除外** する
    (`-DINSERT_READ_DELAY_MS=""` の罠を回避、D23)。
    """
    out: Dict[str, str] = {}
    for m in _SET_RE.finditer(options_text):
        name = m.group(1)
        val = m.group(2).strip()
        if len(val) >= 2 and val[0] == '"' and val[-1] == '"':
            val = val[1:-1]
        if val == "":
            continue
        out[name] = val
    return out


def parse_supplied_macros(options_text: str, protocol_cmake_text: str) -> frozenset:
    """実 TU へ実際に `-D` される マクロ名の集合を CMake ソースから静的に取る (fails-closed)。

    Options.cmake の全 `set(CCBENCH_<NAME> ...)` は cmake CACHE 変数にすぎず、TU に届くのは
    `ccbench_universal_definitions()` の供給表 + protocol の `ccbench_add_protocol(... OPTIONS ...)`
    に列挙されたものだけである (残りは他 protocol 専用。例 `DEBUG_MSG` は oze 用)。digest が
    Options 既定を一律 `-D` すると「digest では定義済み・実 silo TU では未定義」の乖離が生まれ、
    `#ifdef DEBUG_MSG` で枝が逆転して偽 cache hit になる (レビュー B must-fix 1、T-148 fix round)。
    variant patch は protocol CMakeLists (ALLOWLIST 外) でなく Options.cmake の供給表へ追記する
    規約 (silo-backoff-fixed.patch / silo-sort-variant.patch) なので、patch 適用後もここが追随する。
    configure 出力 (compile_commands.json) でなく CMake ソースを読むため D23 の鶏卵は起きない。
    パース結果が空なら CMake 構造の変化とみなし停止する (恒真化防止)。"""
    names, _bare_names, _cache_names = _parse_supplied_macro_details(
        options_text, protocol_cmake_text,
    )
    return names


def _merge_defines(defaults: Dict[str, str], flags: Dict[str, int],
                   supplied: Iterable[str] = (), *, bare_names: Iterable[str] = (),
                   cache_names: Mapping[str, str] | None = None) -> Dict[str, str]:
    """Options 既定を base に genome.flags で上書き (未定義マクロ 0 扱い穴を base で塞ぐ)。

    T-148 fix round: `supplied` (実 TU へ届くマクロ名集合、parse_supplied_macros) を渡すと、
    それに含まれないマクロを落とし PLATFORM_MACROS を足して**実ビルドの -D 集合と揃える**。
    genome.flags も同じフィルタに掛ける — 供給表に無いフラグは cmake CACHE に入るだけで TU に
    届かず、digest だけが定義済みになる乖離を生むため。"""
    merged: Dict[str, str] = dict(defaults)
    for k, v in flags.items():
        merged[k] = str(v)
    if len(CONTEXT_MACROS) > 1:
        # 単発文脈列は結合枝 (#if defined(A) && defined(B)) を覆えない。増やすなら
        # 組合せ文脈への再設計が要るので、増えた時点で機械的に止める (段 6 レビュー A nit 3)。
        raise RuntimeError(
            "source_digest: CONTEXT_MACROS が 2 個以上 — 単発文脈列では結合枝を覆えないため停止 "
            "(組合せ文脈への再設計が要る、T-148)")
    bare = set(bare_names)
    mapping = dict(cache_names or {})
    if (bare or mapping) and not supplied:
        raise RuntimeError(
            "source_digest: 裸/cache mapping があるのに supplied 集合が空 — "
            "実 TU の供給範囲を確定できないため fails-closed (T-148)"
        )
    if supplied:
        keep = set(supplied)
        if not bare <= keep:
            raise RuntimeError(
                f"source_digest: bare_names が supplied の部分集合でない: "
                f"bare={sorted(bare)} supplied={sorted(keep)} → fails-closed (T-148)"
            )
        clash = keep & set(CONTEXT_MACROS)
        if clash:
            # 文脈マクロが実 TU 供給集合にも居ると素文脈が define 文脈へ縮退し、
            # 反対枝 (#ifndef 側) が両文脈とも dead = 再び identity 死角になる。
            raise RuntimeError(
                f"source_digest: CONTEXT_MACROS {sorted(clash)} が実 TU 供給集合にも存在 — "
                "素文脈が縮退して反対枝が digest から落ちるため停止 (T-148)。供給されるように"
                "なったマクロは CONTEXT_MACROS から外し、両枝の被覆方法を再設計する。")
        # flags の上書きは先に済ませる。cache 名の値は filter 前の merged から
        # 取り、左辺へ転送してから不要な右辺 key を落とす。
        pre_filter = dict(merged)
        merged = {k: v for k, v in merged.items() if k in keep}
        for left, right in mapping.items():
            if left in flags:
                # genome.flags の左辺指定を最優先し、後続の bare assignment
                # だけが無条件裸 option を実 TU と同じ 1 に固定する。
                continue
            if right in pre_filter:
                merged[left] = pre_filter[right]
        merged.update(PLATFORM_MACROS)
        # 裸 option は CMake の target_compile_definitions で -DNAME になる。
        # genome.flags/filter の後、filter の外側で明示値を置く (D93/T-1437)。
        for name in bare:
            merged[name] = "1"
    return merged


_REPO_CMAKE_NAMES = frozenset({"CMakeLists.txt"})
_REPO_CMAKE_SUFFIXES = frozenset({".cmake"})
_REPO_CXX_SUFFIXES = frozenset({
    ".c", ".cc", ".cpp", ".cxx", ".h", ".hh", ".hpp", ".hxx", ".inl", ".ipp", ".tcc",
})
_CMAKE_SUPPLY_CALL_NAMES = (
    "target_compile_definitions", "add_definitions", "add_compile_definitions",
    "add_compile_options", "target_compile_options", "set_target_properties",
)

_CMAKE_SUPPLIES = "SUPPLIES"
_CMAKE_DOES_NOT_SUPPLY = "DOES_NOT_SUPPLY"
_CMAKE_UNPROVABLE_REPO_VALUE = "UNPROVABLE_REPO_VALUE"
_CMAKE_VAR_RE = re.compile(r"\$\{([A-Za-z_]\w*)\}")
_CMAKE_STATIC_EXPANSION_LIMIT = 32
_C_RAW_STRING_OPEN_RE = re.compile(
    r'(?:u8|u|U|L)?R"([^ ()\\\t\r\n]{0,16})\('
)


def _splice_c_line_continuations(text: str) -> str:
    """C/C++ translation phase 2 の backslash-newline を除去する。"""
    return re.sub(r"\\(?:\r\n|\n)", "", text)


def _strip_utf8_bom(text: str) -> str:
    """単一の先頭 UTF-8 BOM だけを compiler の署名として正規化する。"""
    if not text.startswith("\ufeff"):
        return text
    without_bom = text.removeprefix("\ufeff")
    if without_bom.startswith("\ufeff"):
        raise RuntimeError(
            "source_digest: 先頭 UTF-8 BOM が重複しているため "
            "directive の認識面を確定できない → fails-closed"
        )
    return without_bom


def _cmake_bracket(text: str, start: int) -> tuple[int, str] | None:
    """``start`` の CMake bracket opener について opener 長と closer を返す。"""
    match = re.match(r"\[(=*)\[", text[start:])
    if match is None:
        return None
    equals = match.group(1)
    return len(match.group(0)), f"]{equals}]"


def _strip_c_comments_without_splicing(text: str) -> str:
    """C/C++ comment を除き、raw string を一つの literal として飛ばす。"""
    out: List[str] = []
    i = 0
    n = len(text)
    quote: str | None = None
    escaped = False
    block = False
    line = False
    while i < n:
        c = text[i]
        nxt = text[i + 1] if i + 1 < n else ""
        if line:
            if c == "\n":
                out.append(c)
                line = False
            else:
                out.append(" ")
            i += 1
            continue
        if block:
            if c == "*" and nxt == "/":
                out.extend((" ", " "))
                i += 2
                block = False
            else:
                out.append("\n" if c == "\n" else " ")
                i += 1
            continue
        if quote is not None:
            out.append(c)
            if escaped:
                escaped = False
            elif c == "\\":
                escaped = True
            elif c == quote:
                quote = None
            i += 1
            continue
        raw_match = _C_RAW_STRING_OPEN_RE.match(text, i)
        if raw_match is not None and i > 0 and (
            text[i - 1].isalnum() or text[i - 1] == "_"
        ):
            # R"..." is a raw opener only at a token boundary.  In particular,
            # the R in fooR"(x" is part of the identifier and must not hide a
            # later physical #define from either supply view.
            raw_match = None
        if raw_match is not None:
            delimiter = raw_match.group(1)
            closer = f"){delimiter}\""
            end = text.find(closer, raw_match.end())
            if end < 0:
                raise RuntimeError(
                    "source_digest: C/C++ 供給源の raw string が未終端 — "
                    "repo-wide macro registry を確定できないため fails-closed (T-1437)"
                )
            segment = text[i:end + len(closer)]
            out.extend("\n" if char == "\n" else " " for char in segment)
            i = end + len(closer)
            continue
        if c == "/" and nxt == "*":
            out.extend((" ", " "))
            i += 2
            block = True
        elif c == "/" and nxt == "/":
            out.extend((" ", " "))
            i += 2
            line = True
        elif c == "'" and _is_digit_separator(text, i):
            # C++ digit separator (1'000) is not a character literal opener.
            out.append(c)
            i += 1
        elif c in {'"', "'"}:
            quote = c
            out.append(c)
            i += 1
        else:
            out.append(c)
            i += 1
    if block or quote is not None:
        raise RuntimeError(
            "source_digest: C/C++ 供給源のコメント/文字列が未終端 — "
            "repo-wide macro registry を確定できないため fails-closed (T-1437)"
        )
    return "".join(out)


def _strip_c_comments_for_supply(text: str) -> str:
    """phase 2 splice の後に comment を除いた compiler-faithful supply view。"""
    return _strip_c_comments_without_splicing(_splice_c_line_continuations(text))


def _c_supply_views(text: str) -> tuple[str, str]:
    """phase-2 view と従来の物理行 view の和集合を返す。"""
    return (
        _strip_c_comments_for_supply(text),
        _strip_c_comments_without_splicing(text),
    )


def _repo_macro_token_matches(
    token: str, macro: str, *, flags_string: bool = False
) -> bool:
    """CMake の literal compile-definition token が macro を供給するか。"""
    if "$<" in token and macro in token:
        raise RuntimeError(
            "source_digest: CMake supply token に generator expression がある — "
            "macro の静的な供給元を確定できないため fails-closed (T-1437)"
        )
    escaped = re.escape(macro)
    for element in token.split(";"):
        if not element:
            continue
        if (
            re.fullmatch(rf"-D{escaped}(?:=.*)?", element)
            or re.fullmatch(rf"{escaped}(?:=.*)?", element)
            or re.search(rf"(?<![A-Za-z0-9_])-D{escaped}(?:=|\b)", element)
            or (
                flags_string
                and re.search(rf"(?<!\S)-D[ \t]+{escaped}(?:=|\b)", element)
            )
        ):
            return True
    return False


def _cmake_calls_including_bracket_arguments(text: str, name: str) -> List[str]:
    """旧 view と同じく bracket argument 内の見かけの call も列挙する。

    Bracket-aware parser が新たに通した入力を旧拒否集合から落とさないためだけの
    monotonicity view である。quoted argument と comment 内の見かけの call は除く。
    """
    clean = _strip_cmake_comments(text)
    scan = list(clean)
    quoted = False
    escaped = False
    for index, char in enumerate(clean):
        if quoted:
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == '"':
                quoted = False
            if char != "\n":
                scan[index] = " "
        elif char == '"':
            quoted = True
    call_re = re.compile(rf"\b{re.escape(name)}\s*\(", re.IGNORECASE)
    scan_text = "".join(scan)
    calls: List[str] = []
    for match in call_re.finditer(scan_text):
        open_pos = clean.find("(", match.start(), match.end())
        body, _ = _scan_cmake_parentheses(clean, open_pos, name)
        calls.append(body)
    return calls


def _cmake_command_records(text: str) -> list[tuple[str, str]]:
    """CMake command を source order で列挙し、argument 内の見かけの call は除く。"""
    clean = _strip_cmake_comments(text)
    records: list[tuple[str, str]] = []
    i = 0
    while i < len(clean):
        bracket = _cmake_bracket(clean, i)
        if bracket is not None:
            opener_len, closer = bracket
            end = clean.find(closer, i + opener_len)
            if end < 0:
                raise RuntimeError(
                    "source_digest: CMake bracket argument が未終端 — "
                    "供給表を確定できないため fails-closed (T-148)"
                )
            i = end + len(closer)
            continue
        if clean[i] == '"':
            i += 1
            escaped = False
            while i < len(clean):
                if escaped:
                    escaped = False
                elif clean[i] == "\\":
                    escaped = True
                elif clean[i] == '"':
                    i += 1
                    break
                i += 1
            continue
        if clean[i].isalpha() or clean[i] == "_":
            end_name = i + 1
            while end_name < len(clean) and (
                clean[end_name].isalnum() or clean[end_name] == "_"
            ):
                end_name += 1
            open_pos = end_name
            while open_pos < len(clean) and clean[open_pos].isspace():
                open_pos += 1
            if open_pos < len(clean) and clean[open_pos] == "(":
                name = clean[i:end_name]
                body, end = _scan_cmake_parentheses(clean, open_pos, name)
                records.append((name.lower(), body))
                i = end
                continue
            i = end_name
            continue
        i += 1
    return records


def _expand_static_cmake_value(
    value: str,
    bindings: Mapping[str, str],
    *,
    seen: frozenset[str] = frozenset(),
    depth: int = 0,
) -> tuple[str, bool]:
    """既知 binding だけを有限再帰展開し、未証明部分の有無も返す。"""
    if depth >= _CMAKE_STATIC_EXPANSION_LIMIT:
        return value, True
    unprovable = False

    def replace(match: re.Match[str]) -> str:
        nonlocal unprovable
        name = match.group(1)
        if name in seen or name not in bindings:
            unprovable = True
            return match.group(0)
        expanded, nested_unprovable = _expand_static_cmake_value(
            bindings[name],
            bindings,
            seen=seen | {name},
            depth=depth + 1,
        )
        unprovable = unprovable or nested_unprovable
        return expanded

    expanded = _CMAKE_VAR_RE.sub(replace, value)
    if len(expanded) > 1024 * 1024:
        return value, True
    return expanded, unprovable


def _classify_cmake_supply_tokens(
    tokens: Iterable[str],
    macro: str,
    bindings: Mapping[str, str],
    *,
    flags_string: bool = False,
) -> str:
    """raw guard、literal、静的展開の固定順で supply token を分類する。"""
    raw_tokens = list(tokens)
    for token in raw_tokens:
        if "$<" in token and macro in token:
            # This pre-existing rejection deliberately precedes classification:
            # expanding OTHER=$<...,MQLOCK,...> must never turn an old red input green.
            _repo_macro_token_matches(token, macro)
    if any(
        _repo_macro_token_matches(token, macro, flags_string=flags_string)
        for token in raw_tokens
    ):
        return _CMAKE_SUPPLIES

    unprovable = False
    for token in raw_tokens:
        expanded, unresolved = _expand_static_cmake_value(token, bindings)
        unprovable = unprovable or unresolved
        if _repo_macro_token_matches(expanded, macro, flags_string=flags_string):
            return _CMAKE_SUPPLIES
    return _CMAKE_UNPROVABLE_REPO_VALUE if unprovable else _CMAKE_DOES_NOT_SUPPLY


def _set_property_compile_definition_tokens(tokens: list[str]) -> list[str] | None:
    """set_property(... PROPERTY COMPILE_DEFINITIONS ...) の値だけを返す。"""
    upper = [token.upper() for token in tokens]
    for index in range(len(tokens) - 1):
        if upper[index:index + 2] == ["PROPERTY", "COMPILE_DEFINITIONS"]:
            return tokens[index + 2:]
    return None


def _repo_cmake_supply_classification(text: str, macro: str) -> str:
    """CMake の静的に証明できる供給を三値分類する。

    ``set()``、literal ``string(CONCAT)``、``list(APPEND)`` だけを source order で
    解決する。未認識 command は無視し、``UNPROVABLE_REPO_VALUE`` としても記録しない。
    三値はこの関数内だけの分類であり、report や bool の呼び手には surface しない。

    静的解析は ``if``/``else`` の実行分岐、``foreach``、``function`` 呼出し、
    ``CACHE`` / ``PARENT_SCOPE`` の実行時値を追わない。また CMake の eager expansion と
    本実装の遅延展開は異なり、例えば ``set(A MQLOCK); set(B ${A}); set(A ${B})`` は
    実 CMake では MQLOCK でも本実装では循環になる。変数鎖も 32 段までである。
    これら未認識・解決不能形の背後に registry macro が隠れうるため、本分類が証明するのは
    repo text に認識済みの当該供給源が無いことだけで、実 build の全 define の不在ではない。
    D723 と同型に未証明値は「供給と主張しない」へ倒し、拒否理由にはしない。
    """
    bindings: dict[str, str] = {}
    saw_unprovable = False
    for name, body in _cmake_command_records(text):
        tokens = _cmake_tokens(body)
        supply_tokens: list[str] | None = None
        flags_string = False
        if name in _CMAKE_SUPPLY_CALL_NAMES:
            supply_tokens = tokens
        elif name == "set_property":
            supply_tokens = _set_property_compile_definition_tokens(tokens)
        elif (
            name == "set"
            and tokens
            and re.fullmatch(
                r"CMAKE_CXX_FLAGS(?:_[A-Za-z0-9_]+)?", tokens[0], re.IGNORECASE
            )
        ):
            supply_tokens = tokens[1:]
            flags_string = True

        if supply_tokens is not None:
            outcome = _classify_cmake_supply_tokens(
                supply_tokens, macro, bindings, flags_string=flags_string
            )
            if outcome == _CMAKE_SUPPLIES:
                return outcome
            saw_unprovable = saw_unprovable or outcome == _CMAKE_UNPROVABLE_REPO_VALUE

        if name == "set" and tokens and _OPTION_IDENT_RE.fullmatch(tokens[0]):
            payload = tokens[1:]
            for terminator in ("CACHE", "PARENT_SCOPE"):
                if terminator in payload:
                    payload = payload[:payload.index(terminator)]
            bindings[tokens[0]] = ";".join(payload)
        elif name == "string" and len(tokens) >= 2 and tokens[0].upper() == "CONCAT":
            pieces: list[str] = []
            unprovable = False
            for token in tokens[2:]:
                expanded, unresolved = _expand_static_cmake_value(token, bindings)
                pieces.append(expanded)
                unprovable = unprovable or unresolved
            if not unprovable and _OPTION_IDENT_RE.fullmatch(tokens[1]):
                bindings[tokens[1]] = "".join(pieces)
            else:
                saw_unprovable = True
        elif name == "list" and len(tokens) >= 2 and tokens[0].upper() == "APPEND":
            variable = tokens[1]
            pieces: list[str] = []
            unprovable = False
            for token in tokens[2:]:
                expanded, unresolved = _expand_static_cmake_value(token, bindings)
                pieces.append(expanded)
                unprovable = unprovable or unresolved
            if not unprovable and _OPTION_IDENT_RE.fullmatch(variable):
                previous = bindings.get(variable, "")
                bindings[variable] = ";".join(part for part in (previous, *pieces) if part)
            else:
                saw_unprovable = True

    # Monotonicity view: bracket-aware parsing must not make an input accepted
    # when the former bracket-unaware search rejected a supply-shaped payload.
    for name in (*_CMAKE_SUPPLY_CALL_NAMES, "set_property"):
        for body in _cmake_calls_including_bracket_arguments(text, name):
            tokens = _cmake_tokens(body)
            supply_tokens = (
                _set_property_compile_definition_tokens(tokens)
                if name == "set_property"
                else tokens
            )
            if supply_tokens is not None and _classify_cmake_supply_tokens(
                supply_tokens, macro, {}
            ) == _CMAKE_SUPPLIES:
                return _CMAKE_SUPPLIES

    return _CMAKE_UNPROVABLE_REPO_VALUE if saw_unprovable else _CMAKE_DOES_NOT_SUPPLY


def _repo_cmake_supplies_macro(text: str, macro: str) -> bool:
    """Compatibility predicate: only statically proven supply is affirmative."""
    return _repo_cmake_supply_classification(text, macro) == _CMAKE_SUPPLIES


def _is_repo_supply_path(path: str) -> bool:
    """checkout/tree の双方で同じ repo-wide supply 対象集合を選ぶ。"""
    basename = os.path.basename(path)
    suffix = os.path.splitext(basename)[1].lower()
    return basename in _REPO_CMAKE_NAMES or suffix in (
        _REPO_CMAKE_SUFFIXES | _REPO_CXX_SUFFIXES
    )


def _git_tree_entries(root: str, commit: str) -> Iterable[tuple[str, str, str, str]]:
    """commit tree を mode/type/OID/path 付きで fail-closed に列挙する。"""
    try:
        result = subprocess.run(
            ["git", "-C", root, "ls-tree", "-r", "-z", commit, "--"],
            capture_output=True,
            env=_sanitized_git_env(),
        )
    except (OSError, subprocess.SubprocessError) as exc:
        raise RuntimeError(
            f"source_digest: git ls-tree {commit} 起動失敗 ({exc}) — commit tree の "
            "macro supply を確定できないため fails-closed (T-1506)"
        ) from exc
    if result.returncode != 0:
        stderr = result.stderr.decode("utf-8", errors="replace").strip()
        raise RuntimeError(
            f"source_digest: git ls-tree {commit} 失敗 (rc={result.returncode}): "
            f"{stderr[-300:]} → commit tree の macro supply を確定できないため "
            "fails-closed (T-1506)"
        )
    if result.stdout and not result.stdout.endswith(b"\0"):
        raise RuntimeError(
            "source_digest: git ls-tree -z の出力が NUL 終端でない — commit tree の "
            "macro supply を確定できないため fails-closed (T-1506)"
        )

    records = result.stdout.split(b"\0")
    if records and records[-1] == b"":
        records.pop()
    seen: set[str] = set()
    for record in records:
        header, separator, raw_path = record.partition(b"\t")
        if not separator:
            raise RuntimeError(
                "source_digest: git ls-tree entry に path 区切りがない — commit tree の "
                "macro supply を確定できないため fails-closed (T-1506)"
            )
        try:
            fields = header.decode("ascii").split()
            path = raw_path.decode("utf-8")
        except UnicodeError as exc:
            raise RuntimeError(
                "source_digest: git ls-tree entry の path/header が UTF-8/ASCII でない — "
                "commit tree の macro supply を確定できないため fails-closed (T-1506)"
            ) from exc
        if len(fields) != 3:
            raise RuntimeError(
                f"source_digest: git ls-tree entry header が不正: {fields!r} — "
                "commit tree の macro supply を確定できないため fails-closed (T-1506)"
            )
        if not path:
            raise RuntimeError(
                "source_digest: git ls-tree entry の path が空 — commit tree の macro "
                "supply を確定できないため fails-closed (T-1506)"
            )
        if path in seen:
            raise RuntimeError(
                f"source_digest: git ls-tree entry の path が重複: {path!r} — commit tree "
                "の macro supply を確定できないため fails-closed (T-1506)"
            )
        seen.add(path)
        mode, object_type, oid = fields
        yield mode, object_type, oid, path


def _checkout_gitlink_oid(root: str, rel: str) -> str | None:
    """rel 自身が repository 境界なら submodule checkout の commit を返す。"""
    checkout = os.path.join(root, rel)
    git_marker = os.path.join(checkout, ".git")
    if (
        not os.path.isdir(checkout)
        or os.path.islink(checkout)
        or os.path.islink(git_marker)
        or not (os.path.isfile(git_marker) or os.path.isdir(git_marker))
    ):
        return None
    try:
        top_level_result = subprocess.run(
            ["git", "-C", checkout, "rev-parse", "--show-toplevel"],
            capture_output=True,
            text=True,
            env=_sanitized_git_env(),
        )
    except (OSError, subprocess.SubprocessError, UnicodeError):
        return None
    if top_level_result.returncode != 0:
        return None
    top_level = top_level_result.stdout.strip()
    if not top_level or os.path.realpath(top_level) != os.path.realpath(checkout):
        return None

    try:
        head_result = subprocess.run(
            ["git", "-C", checkout, "rev-parse", "--verify", "HEAD^{commit}"],
            capture_output=True,
            text=True,
            env=_sanitized_git_env(),
        )
    except (OSError, subprocess.SubprocessError, UnicodeError):
        return None
    if head_result.returncode != 0:
        return None
    oid = head_result.stdout.strip()
    if not re.fullmatch(r"[0-9a-f]+", oid):
        return None
    return oid


def _repo_supply_files(
    root: str, *, commit: str | None = None
) -> Iterable[tuple[str, str]]:
    """repo-wide macro supply audit の対象 C/C++/CMake text を列挙する。

    submodule の中身は不在証明の対象外である。初期化済み checkout があれば従来どおり
    os.walk で読むが、gitlink coverage を確認できなくても top-level tree の監査は続ける。
    """
    if not os.path.isdir(root):
        raise RuntimeError(
            f"source_digest: ccbench repo が directory でない: {root!r} → "
            "repo-wide macro registry を確定できないため fails-closed"
        )

    def raise_walk_error(exc: OSError) -> None:
        raise RuntimeError(
            f"source_digest: checkout directory の列挙に失敗: "
            f"path={exc.filename!r} ({exc}) → repo-wide macro registry を "
            "確定できないため fails-closed (T-1506)"
        ) from exc

    for directory, dirs, files in os.walk(root, onerror=raise_walk_error):
        dirs[:] = [name for name in dirs if name != ".git"]
        for filename in files:
            if not _is_repo_supply_path(filename):
                continue
            path = os.path.join(directory, filename)
            yield path, _read(path)

    if commit is None:
        return
    for mode, object_type, oid, path in _git_tree_entries(root, commit):
        if mode in {"100644", "100755"}:
            if object_type != "blob":
                raise RuntimeError(
                    f"source_digest: regular file mode の tree entry が blob でない: "
                    f"path={path!r} mode={mode!r} type={object_type!r} → fails-closed "
                    "(T-1506)"
                )
            if _is_repo_supply_path(path):
                yield path, _git_show(root, commit, path)
        elif mode == "120000":
            raise RuntimeError(
                f"source_digest: commit tree に symlink entry がある: {path!r} — link先の "
                "macro supply を確定できないため fails-closed (T-1506)"
            )
        elif mode == "160000":
            if object_type != "commit":
                raise RuntimeError(
                    f"source_digest: gitlink mode の tree entry が commit でない: "
                    f"path={path!r} type={object_type!r} → fails-closed (T-1506)"
                )
            checkout_oid = _checkout_gitlink_oid(root, path)
            if checkout_oid != oid:
                # 未初期化・非 repository・別 HEAD は coverage を主張しない。
                # submodule の中身は上の docstring のとおり不在証明の対象外である。
                continue
        else:
            raise RuntimeError(
                f"source_digest: commit tree に未対応 mode がある: "
                f"path={path!r} mode={mode!r} → fails-closed (T-1506)"
            )


def _assert_proven_repo_absent_macros(
    ccbench_dir: str = "", *, commit: str | None = None
) -> frozenset[str]:
    """registry macro が checkout と指定 commit tree に無いことを毎回検証する。

    checkout/commit の canonical CMake は別 view namespace で解析する。同一 logical
    path が両 view にあることは重複構文ではない。解決不能な間接 CMake 値は供給と
    主張せず、拒否にも使わないため、その背後の supply は証明範囲外として残る。
    """
    overlap = set(PROVEN_REPO_ABSENT_MACROS) & set(CONTEXT_MACROS)
    if overlap:
        raise RuntimeError(
            f"source_digest: PROVEN_REPO_ABSENT_MACROS と CONTEXT_MACROS が衝突 "
            f"({sorted(overlap)}) → registry の意味が曖昧なため fails-closed"
        )
    for macro in PROVEN_REPO_ABSENT_MACROS:
        if not _OPTION_IDENT_RE.fullmatch(macro):
            raise RuntimeError(
                f"source_digest: absent registry の macro 名が不正: {macro!r} → "
                "fails-closed"
            )
    sub = ccbench_dir or _ccbench_dir()
    hits: List[str] = []
    # Enumeration can invoke git for every commit-tree blob.  Materialize it once
    # and reuse it for every macro and lexical view (subprocess multiplier 1.00).
    supply_files = list(_repo_supply_files(sub, commit=commit))
    namespaced_files: list[tuple[str, str, str, str]] = []
    seen: set[tuple[str, str]] = set()
    root_real = os.path.realpath(sub)
    for path, text in supply_files:
        if os.path.isabs(path):
            view = "checkout"
            logical_path = os.path.relpath(os.path.realpath(path), root_real)
        else:
            view = "commit"
            logical_path = path
        key = (view, logical_path)
        if key in seen:
            raise RuntimeError(
                "source_digest: repo supply path が同一 view 内で重複: "
                f"view={view!r} path={logical_path!r} → fails-closed (T-1506)"
            )
        seen.add(key)
        namespaced_files.append((view, logical_path, path, text))

    for view, logical_path, path, text in namespaced_files:
        text = _strip_utf8_bom(text)
        basename = os.path.basename(path)
        suffix = os.path.splitext(basename)[1].lower()
        if basename in _REPO_CMAKE_NAMES or suffix in _REPO_CMAKE_SUFFIXES:
            # Parsing all protocol/universal supply tables also makes malformed
            # CMake visible even when the malformed token is unrelated to the
            # current registry macro.
            clean_cmake = _strip_cmake_comments(text)
            protocol_details = _parse_protocol_macro_details(clean_cmake)
            universal_details = (set(), set(), {})
            if re.search(r"\bfunction\s*\(\s*ccbench_universal_definitions\b", clean_cmake,
                         re.IGNORECASE):
                universal_details = _parse_universal_macro_details(clean_cmake)
            for macro in PROVEN_REPO_ABSENT_MACROS:
                if (macro in protocol_details[0]
                        or macro in universal_details[0]
                        or _repo_cmake_supplies_macro(text, macro)):
                    hits.append(f"{view}:{logical_path}: CMake supply")
        elif suffix in _REPO_CXX_SUFFIXES:
            for clean in _c_supply_views(text):
                for macro in PROVEN_REPO_ABSENT_MACROS:
                    if re.search(
                            rf"(?m)^[ \t]*(?:#|%:)[ \t]*define[ \t]+"
                            rf"{re.escape(macro)}(?:[ \t(]|$)",
                            clean):
                        hits.append(f"{view}:{logical_path}: #define {macro}")
    if hits:
        raise RuntimeError(
            "source_digest: PROVEN_REPO_ABSENT_MACROS が stale — repo に供給源が出現: "
            f"{sorted(set(hits))[:12]!r} → fails-closed (T-1437)"
        )
    return PROVEN_REPO_ABSENT_MACROS


def _cpp_normalize(
    source_text: str, defines: Dict[str, str], cxx: str,
    *, _environment_only: bool = False,
) -> str:
    """#include を除去し preprocess (#if/#else 解決 + コメント除去) した正規化出力を返す。

    -nostdinc で系ヘッダは辿らないが、**組込 builtin (__x86_64__ 等) は実ビルドと同じく
    定義済みのままにする** (D34 / 案A)。旧 -undef は builtin を全消しして環境非依存に
    していたが、digest 環境と実ビルドが乖離し、EVOLVE-BLOCK 内の生 `#ifdef __x86_64__` が
    digest では stock 枝・実ビルドでは別枝を取る**偽 cache hit** を生んだ (方針 A で hook の
    payload 検査を削除し道Y の「生 #ifdef を hook で禁止」前提が消えた後は一次防壁がこれを
    塞げず critical、2026-07-04 敵対検証)。builtin を実環境と揃えれば `#ifdef`/`defined()` が
    digest に正直に反映され偽 hit しない。-Werror=undef は #if/#elif の未定義マクロ参照
    (= 骨格 BACKOFF_FIXED 等の defines 供給漏れ) を rc≠0 にして fails-closed (D23 / 規律6)。
    代償 = digest 値が cxx/環境に依存する (別環境で別値) が、cache は env/<tag> 軸で環境別
    (D13) ゆえ実害なし。非決定 builtin (__DATE__ 等) は churn するが偽 hit しない
    (毎回 cache-miss = 新規ビルド+verify、正しさ不変)。g++ 不在・preprocess 失敗は
    RuntimeError (identity 核に best-effort skip を持ち込まない)。

    -dD で有効枝の source の #define / #undef を pre-image に残す (F1016: file 間へ
    漏れる指令が消え、別プログラムを stock と同一視した)。skipped 枝の指令は出ない。
    対象 GCC の実測では predefined と command-line 定義も出力されるため、同じ argv の
    空入力出力を環境 prefix として剥がす。剥がさないと追加供給 BACKOFF_FIXED /
    BACKOFF_NOINLINE だけで inert template が非 stock になる。builtin の条件評価は
    定義済みのまま維持する。prefix 不一致は RuntimeError で fails-closed。
    残る限界: include 行を除去するため指令と include の相対位置は識別せず、
    #pragma push_macro / pop_macro の復元値も出力に現れない (D2104 項 2 の scope 外)。
    _trace_pair_diff (diff-of-diffs) の比較式 D_variant == D_stock は不変だが、
    #if TRACE 内の未使用 #define / #undef も差分素材になるため受理集合は狭まる (規律 2 と同方向)。
    """
    prefix = ""
    if not _environment_only:
        key = (cxx, tuple(sorted(defines.items())))
        if key not in _CPP_ENV_PREFIX_CACHE:
            _CPP_ENV_PREFIX_CACHE[key] = _cpp_normalize(
                "", defines, cxx, _environment_only=True,
            )
        prefix = _CPP_ENV_PREFIX_CACHE[key]

    stripped = _INCLUDE_RE.sub("", source_text)
    args = [cxx, "-E", "-P", "-dD", "-nostdinc", "-Werror=undef", *BUILD_FLAGS]
    for k in sorted(defines):
        args.append(f"-D{k}={defines[k]}")
    args += ["-x", "c++", "-"]
    try:
        r = subprocess.run(args, input=stripped, capture_output=True, text=True)
    except (OSError, subprocess.SubprocessError) as e:
        raise RuntimeError(
            f"source_digest: preprocess を起動できない ({cxx}: {e}) — identity を確定"
            "できないため fails-closed で停止 (D23)") from e
    if r.returncode != 0:
        raise RuntimeError(
            f"source_digest: preprocess 失敗 (rc={r.returncode})。#if が参照する "
            "マクロが defines に揃っていない (供給漏れ) 疑い → fails-closed。\n"
            f"  {r.stderr.strip()[-500:]}")
    if _environment_only:
        return r.stdout
    if not r.stdout.startswith(prefix):
        raise RuntimeError(
            "source_digest: preprocess 出力が空入力の環境 prefix と不一致"
            " — identity を確定できないため fails-closed"
        )
    return r.stdout.removeprefix(prefix)


def _context_overlays() -> List[Dict[str, str]]:
    """digest が織り込むマクロ文脈の列: 素文脈 + CONTEXT_MACROS 各 1 個の define 文脈。"""
    return [{}] + [{m: "1"} for m in CONTEXT_MACROS]


def _normalize_contexts(source_text: str, defines: Dict[str, str], cxx: str) -> str:
    """全文脈の正規化出力を文脈タグ付きで連結する (T-148: TU 注入マクロの両枝を identity に乗せる)。

    素文脈だけの preprocess では `#ifdef GLOBAL_VALUE_DEFINE` 枝 (backoff.hh:123、TU の
    #define で供給) が dead になり、枝内編集が digest に不可視 = src_token が 'stock' に化けて
    stock の certified 結果・cache バイナリを継承する (規律2 直撃、実測 2026-07-28)。define 文脈を
    足して両枝を pre-image に織り込めば、どちらの枝の編集も digest を動かす。タグと \\x02 区切りは
    文脈間の出力境界の衝突 (別文脈の連結が偶然同一 bytes になる) を防ぐ。"""
    parts = []
    for overlay in _context_overlays():
        tag = ",".join(f"{k}={v}" for k, v in sorted(overlay.items())) or "base"
        parts.append(f"[ctx:{tag}]\n" + _cpp_normalize(
            source_text, dict(defines, **overlay), cxx))
    return "\x02".join(parts)


def _dump_macros(source_text: str, defines: Dict[str, str], cxx: str) -> frozenset:
    """`-dM` で「この環境・このソースで実際に定義されるマクロ」名の集合を取る (fails-closed)。

    実ビルドと同じ `BUILD_FLAGS` で照会する。`-Werror=undef` は付けない (未知マクロを含む
    ソースでも定義状態は取れる必要があるため — 未知の判定はガード本体の仕事)。"""
    args = [cxx, "-dM", "-E", "-nostdinc", *BUILD_FLAGS]
    for k in sorted(defines):
        args.append(f"-D{k}={defines[k]}")
    args += ["-x", "c++", "-"]
    try:
        r = subprocess.run(args, input=_INCLUDE_RE.sub("", source_text),
                           capture_output=True, text=True)
    except (OSError, subprocess.SubprocessError) as e:
        raise RuntimeError(
            f"source_digest: マクロ定義状態の照会を起動できない ({cxx}: {e}) — 文脈ガードを"
            "確定できないため fails-closed で停止 (D23)") from e
    if r.returncode != 0:
        raise RuntimeError(
            f"source_digest: マクロ定義状態の照会に失敗 (rc={r.returncode}) → fails-closed。\n"
            f"  {r.stderr.strip()[-300:]}")
    names = frozenset(m.group(1) for m in _DEFINE_RE.finditer(r.stdout))
    if not names:
        raise RuntimeError(
            "source_digest: マクロ定義状態の照会が空 — 文脈ガードが恒真化するため停止")
    return names


def _environment_macros(defines: Dict[str, str], cxx: str) -> frozenset:
    """ソース非依存の定義済みマクロ (builtin + BUILD_FLAGS + -D)。プロセス内 cache。

    D34 案A で builtin は digest 環境でも定義済み = `#ifdef __GNUC__` 等は受理して別 identity に
    する仕様 (test_source_digest_builtin_ifdef_not_aliased_to_stock)。照会フラグは実ビルドに
    揃える — `-O3 -DNDEBUG` を外すと `__NO_INLINE__` 等が「digest では定義済み・実ビルドでは
    未定義」になり、その否定形の枝を digest だけが dead 扱いする (段 6 レビュー A must-fix 4)。"""
    key = (cxx, tuple(sorted(defines.items())))
    got = _BUILTIN_MACRO_CACHE.get(key)
    if got is None:
        got = _dump_macros("", defines, cxx)
        _BUILTIN_MACRO_CACHE[key] = got
    return got


def _is_digit_separator(src: str, i: int) -> bool:
    """`src[i]` の `'` が数値の桁区切り (`1'000`) か — 文字リテラルの開始でないか。

    桁区切りは pp-number の内側にしか現れないので、直前のトークンが数字で始まるかで判定する。
    直前を「英数字なら区切り」と素朴に見ると接頭辞つき文字リテラル (`L'A'`, `u8'x'`) を
    取り違え、中身が `"` や `/` のとき (`u'"'`) 未終端リテラルとして正当なコードを止める
    (段 6 焦点再レビュー nit 1)。"""
    j = i
    while j and (src[j - 1].isalnum() or src[j - 1] == "_"):
        j -= 1
    return j < i and src[j].isdigit()


def _lex_normalize(source_text: str, rel: str = "") -> str:
    """翻訳フェーズ 2-3 の近似: 行継続とコメントを畳み、リテラル中身を消す (fails-closed)。

    条件指令の静的走査を素の正規表現でやると C++ の字句と食い違い、ガードが素通りする
    (段 6 レビュー、いずれも g++ 実測で偽 STOCK alias を構築):
    - `#/**/ifdef FOO` は正規の条件指令。`#` 直後に空白しか許さない走査は見落とす (B must-fix 2)。
    - 複数行コメントは**空白 1 個**であって改行ではない。`#if 1 /*<改行>*/ && defined(X)` は
      1 論理行の指令なので、改行を保存すると続きの被演算子が走査から落ちる (A must-fix 1)。
      したがってここではブロックコメント内の改行を残さない (行数は保存しない — 診断は行番号でなく
      指令の逐語を出す)。行コメント `//` の改行は規格どおり残す。
    - `#if 'A' == 65` の文字定数は識別子でない。拾うと受理集合を不当に狭める (B must-fix 4)。
      一方 `1'000` の桁区切りはリテラル開始ではない — リテラル扱いすると閉じ引用符を探して
      以降のソースを飲み込み、その先の指令すべてがガードから消える (A must-fix 3)。
    - 未終端のコメント/リテラルと raw string は「解釈不能」であり、静かに全消しして受理すると
      ガードが恒真化する。identity 核の契約どおり停止する (A should 3)。"""
    src = _splice_c_line_continuations(source_text)
    out, i, n = [], 0, len(src)
    while i < n:
        c = src[i]
        nxt = src[i + 1] if i + 1 < n else ""
        if c == "/" and nxt == "*":
            j = src.find("*/", i + 2)
            if j < 0:
                raise RuntimeError(
                    f"source_digest: {rel} に未終端のブロックコメント — 条件指令を字句として"
                    "解釈できないため fails-closed (T-148)")
            out.append(" ")
            i = j + 2
        elif c == "/" and nxt == "/":
            j = src.find("\n", i)
            j = n if j < 0 else j
            out.append(" ")
            i = j
        elif c in "Ru8UL" and _RAW_STRING_RE.match(src, i):
            raise RuntimeError(
                f"source_digest: {rel} に raw string literal — 字句正規化が未対応のため "
                "fails-closed (骨格・stock は不使用、T-148)")
        elif c == "'" and _is_digit_separator(src, i):
            out.append("'")          # 数値の桁区切り (1'000)。リテラル開始ではない
            i += 1
        elif c in "\"'":
            j, quote = i + 1, c
            while j < n and src[j] not in (quote, "\n"):
                j += 2 if src[j] == "\\" else 1
            if j >= n or src[j] == "\n":
                raise RuntimeError(
                    f"source_digest: {rel} に未終端の文字列/文字リテラル — 条件指令を字句として"
                    "解釈できないため fails-closed (T-148)")
            out.append(quote + quote)
            i = j + 1
        else:
            out.append(c)
            i += 1
    return "".join(out)


def _assert_conditional_macros_covered(source_text: str, defines: Dict[str, str],
                                       cxx: str, rel: str,
                                       known_absent: Iterable[str] = ()) -> None:
    """条件指令が参照するマクロが既知集合に閉じるか検査する (fails-closed、T-148 ガード)。

    -Werror=undef は `#if MACRO` の未定義参照しか捕えず、`#ifdef`/`#ifndef`/`defined()` は
    静かに偽枝を取る (g++ 実測 rc=0)。既知集合 = defines (実 TU 供給集合まで絞った Options 既定 +
    genome.flags + PLATFORM_MACROS) ∪ **その指令より前の** ファイル内 #define ∪ CONTEXT_MACROS
    (両文脈で被覆済み) ∪ 組込 builtin (-dM、D34 案A で受理仕様)。ここに無いマクロの条件枝は
    digest がどの文脈でも覆えない未知枝 (次の GLOBAL_VALUE_DEFINE 型) なので停止する。

    T-148 fix round (段 6 レビュー A/B):
    - 走査対象は `_lex_normalize` を通した字句で、`#/**/ifdef` 形の指令も、コメントで分断された
      論理行の続きも検出する。リテラル中身は識別子にしない。不整形は停止する。
    - `#define` の既知化は「**その指令より前**に静的に現れ、**かつ実際に定義される**」ものに限る。
      後ろの `#define` はその時点で未定義であり、`#if 0` 等の dead 枝にある `#define` は
      そもそも定義されない — どちらも既知に数えると未知マクロを洗浄してしまう (A must-fix 2)。
      実定義は `-dM` の実照会で取る (`#undef` も自動的に反映される)。
    - `__has_include` / `__has_include_next` は条件式の literal 出現だけでなく、そこへ
      **展開されうる `#define` 本体**も止める (`#define IZ_HAS __has_include(...)` → `#if IZ_HAS`
      の迂回、B must-fix 3)。#include 行検査にも preprocess 後 digest にも現れず (digest 環境は
      -nostdinc で header 未発見 = dead 枝)、実ビルドだけ別バイナリになる identity 死角
      (D34 known-limitation の fails-closed 化)。header 探索に依存しない他の `__has_*` 演算子は
      digest と実ビルドで同一に評価されるので受理する — 引数 (builtin 名・属性名) はマクロ参照
      ではないので演算子ごと式から落としてから識別子を拾う (A should 2)。
    - 予約識別子 (`__NO_INLINE__` 等) でも、この環境照会に現れないものは受理しない。`BUILD_FLAGS`
      で実ビルドに揃えた範囲の外に未知のフラグ差が残りうる以上、「定義されていない予約名の
      definedness テスト」は乖離候補として停止側に倒す (A must-fix 4 の残余。骨格・stock は
      いずれも使用しないので実害はない)。"""
    scan = _lex_normalize(source_text, rel)
    for m in _DEFINE_RE.finditer(scan):
        body = m.group(0)
        if _TOKEN_PASTE_RE.search(body):
            raise RuntimeError(
                f"source_digest: {rel} の #define 本体にトークン貼り合わせ (## / %:%:) — "
                "走査が literal で探す名前を分割して組み立てられる (`__has_inc##lude` は g++ が "
                "`__has_include` として評価する。実測) ため停止 (T-148)。EVOLVE-BLOCK の骨格・"
                f"stock は貼り合わせを使わない。\n  定義: {body.strip()!r}")
        for probe in INCLUDE_PROBE_OPERATORS:
            if probe in body:
                raise RuntimeError(
                    f"source_digest: {rel} の #define 本体に {probe} — 条件式へ展開されると "
                    "computed include が digest を迂回する (literal 検査の裏をかく経路) ため停止 "
                    f"(T-148)。\n  定義: {body.strip()!r}")
    defs_at: List[tuple] = [(m.start(), m.group(1)) for m in _DEFINE_RE.finditer(scan)]
    live = _dump_macros(source_text, defines, cxx) if defs_at else frozenset()
    base_known = (
        set(defines) | set(CONTEXT_MACROS) | set(known_absent)
        | _environment_macros(defines, cxx)
    )
    unknown = set()
    for m in _COND_DIRECTIVE_RE.finditer(scan):
        expr = m.group(1)
        for probe in INCLUDE_PROBE_OPERATORS:
            if probe in expr:
                raise RuntimeError(
                    f"source_digest: {rel} の条件指令に {probe} — computed include は "
                    "#include 行検査にも preprocess 後 digest にも現れず (digest 環境は -nostdinc "
                    "で header 未発見 = dead 枝)、実ビルドだけ別バイナリになる identity 死角の"
                    "ため停止 (D34 known-limitation の fails-closed 化、T-148)。\n"
                    f"  指令: {m.group(0).strip()!r}")
        known = base_known | {name for pos, name in defs_at if pos < m.start() and name in live}
        for ident in _IDENT_RE.findall(_HAS_OP_CALL_RE.sub(" ", expr)):
            if ident in ("defined", "true", "false") or ident in KNOWN_HAS_OPERATORS:
                continue
            if ident not in known:
                unknown.add(ident)
    if unknown:
        raise RuntimeError(
            f"source_digest: {rel} の条件指令が未知マクロ {sorted(unknown)} を参照 — 実 TU 供給"
            "マクロ・先行する #define・CONTEXT_MACROS・builtin のいずれでもなく、digest はこの"
            "条件枝をどの文脈でも覆えない (TU 注入マクロ GLOBAL_VALUE_DEFINE 型の identity 死角、"
            "偽 cache hit の運び屋) ため fails-closed で停止 (T-148)。既知の文脈マクロなら "
            "CONTEXT_MACROS への登録 (= 両文脈 digest 化) が正しい封鎖で、この検査の緩和ではない "
            "(規律2)。")


def assert_conditional_macros_covered(genome: Genome, ccbench_dir: str = "",
                                      cxx: str = "g++-13") -> None:
    """working-tree の EVOLVE_BLOCK_SOURCES 全体に文脈ガードを適用する (resolve が駆動)。"""
    sub = ccbench_dir or _ccbench_dir()
    known_absent = _assert_proven_repo_absent_macros(sub)
    for rel in EVOLVE_BLOCK_SOURCES:
        defines = _worktree_defines(sub, genome, rel)
        _assert_conditional_macros_covered(
            _read(os.path.join(sub, rel)), defines, cxx, rel, known_absent,
        )


def _include_lines(source_text: str) -> str:
    """#include 行の列 (順序込み・生バイト)。HEAD 一致検査の比較素材。

    preprocess (_cpp_normalize) は #include を除去してから走るので、include の追加/削除/
    差し替えは正規化出力に現れない (identity 不変の死角)。この列を HEAD baseline と比較して
    1 行でも違えば abort する (assert_includes_match_head)。条件コンパイルで死んでいる枝の
    #include も含む = 安全側 (dead 枝の include 差し替えも止める)。順序込みで比較する
    (include 順序も取り込むヘッダを変えうる)。"""
    return "\n".join(m.group(0) for m in _INCLUDE_RE.finditer(source_text))


def _read(path: str) -> str:
    """identity 経路のファイル読取。失敗は RuntimeError に正規化する。

    呼び手 (`loop`・`pipeline.evaluate`・`buildcache._recheck_src_token`) は identity 確定の
    失敗を `except RuntimeError` で受けて variant 単位の abort に隔離する。`OSError` を
    そのまま投げると campaign 全体が落ち、build dir の破棄 (`_discard_build_dir`) も走らない
    (段 6 レビュー A should 4)。HEAD 側 (`_git_show`) は既に RuntimeError 化してあり、
    working-tree 側だけ非対称だった。"""
    try:
        with open(path, encoding="utf-8") as f:
            return f.read()
    except OSError as e:
        raise RuntimeError(
            f"source_digest: {path} を読めない ({e}) — identity を確定できないため "
            "fails-closed で停止 (D23)") from e


def _sanitized_git_env() -> dict[str, str]:
    """Repository 指定を親から継承せず、Git read の index 副作用を抑止する。"""
    env = os.environ.copy()
    for name in (
        "GIT_DIR", "GIT_INDEX_FILE", "GIT_WORK_TREE", "GIT_COMMON_DIR",
        "GIT_OBJECT_DIRECTORY", "GIT_ALTERNATE_OBJECT_DIRECTORIES",
        "GIT_CEILING_DIRECTORIES",
    ):
        env.pop(name, None)
    env["GIT_OPTIONAL_LOCKS"] = "0"
    return env


def _git_show(ccbench_dir: str, commit: str, rel: str) -> str:
    """submodule の特定 commit のファイル内容 (baseline = patch 前 stock)。"""
    try:
        r = subprocess.run(
            ["git", "-C", ccbench_dir, "show", f"{commit}:{rel}"],
            capture_output=True, text=True, env=_sanitized_git_env(),
        )
    except (OSError, subprocess.SubprocessError, UnicodeError) as e:
        raise RuntimeError(
            f"source_digest: git show 起動失敗 ({e}) — baseline を確定できず "
            "fails-closed (D23)") from e
    if r.returncode != 0:
        raise RuntimeError(
            f"source_digest: git show {commit}:{rel} 失敗 (rc={r.returncode})。"
            f"submodule 未 init / commit 不一致を疑え → fails-closed。\n"
            f"  {r.stderr.strip()[-300:]}")
    return r.stdout


def _canonical_preimage_bytes(parts: Iterable[str]) -> bytes:
    """Return the historical digest preimage: ordered UTF-8 parts joined by NUL."""
    return "\x00".join(parts).encode("utf-8")


def _digest(parts: Iterable[str]) -> str:
    return hashlib.sha256(_canonical_preimage_bytes(parts)).hexdigest()


def source_preimage_artifact_relative_path(proposal_sha256: str) -> str:
    """Return the proposal-byte-addressed campaign artifact path."""
    if not _is_sha256(proposal_sha256):
        raise ValueError(
            "proposal_sha256 は exact lowercase SHA-256 でなければならない: "
            f"{proposal_sha256!r}"
        )
    return f"{SOURCE_BINDING_DIRECTORY}/{proposal_sha256}.preimage"


def _assert_source_protocols_exact() -> None:
    """EVOLVE_BLOCK_SOURCES と source-owner registry の drift を停止する。"""
    if tuple(EVOLVE_BLOCK_SOURCE_PROTOCOLS) != EVOLVE_BLOCK_SOURCES:
        raise RuntimeError(
            "source_digest: EVOLVE_BLOCK_SOURCE_PROTOCOLS の key 集合/順序が "
            "EVOLVE_BLOCK_SOURCES と不一致 — source owner を一意に確定できないため "
            "fails-closed (T-1437)"
        )


_assert_source_protocols_exact()


def _source_protocol(rel: str, genome: Genome) -> str:
    """EVOLVE-BLOCK source の owner protocol を返す。未知 source は RuntimeError。"""
    _assert_source_protocols_exact()
    try:
        owner = EVOLVE_BLOCK_SOURCE_PROTOCOLS[rel]
    except KeyError as exc:
        raise RuntimeError(
            f"source_digest: EVOLVE-BLOCK の未知 source {rel!r} — "
            "protocol owner を確定できないため fails-closed (T-1437)"
        ) from exc
    if owner is None:
        return genome.protocol
    if type(owner) is not str or not owner:
        raise RuntimeError(
            f"source_digest: source {rel!r} の owner protocol が不正: {owner!r} → "
            "fails-closed (T-1437)"
        )
    return owner


def _protocol_cmake_rel(protocol: str) -> str:
    if type(protocol) is not str or not protocol:
        raise RuntimeError(
            f"source_digest: protocol が不正: {protocol!r} → fails-closed (T-1437)"
        )
    return _PROTOCOL_CMAKE.format(protocol=protocol)


def resolve_effective_defines_from_cmake_sources(
    source_rel: str,
    genome: Genome,
    *,
    options_text: str,
    protocol_cmake_text: str,
) -> EffectiveDefineResolution:
    """Rederive effective TU values from captured owner-specific CMake source.

    ``genome.flags`` models the caller's ``CCBENCH_<name>`` cache overrides.
    Each TU macro then receives the value of the cache variable named on the
    right-hand side of its CMake mapping. This intentionally does not use the
    older digest shortcut that lets a left-hand genome flag bypass a wrong
    cache mapping: a wrong RHS must remain observable to supply consumers.

    ``protocol_cmake_text`` is caller-supplied captured text. This generic
    adapter derives ``owner_protocol`` from ``source_rel`` but does not attest
    that the caller obtained those bytes from that owner's path. Consumers
    claiming path provenance must bind and verify that capture themselves.
    """
    if type(source_rel) is not str or not source_rel:
        raise ValueError("source_rel must be a non-empty exact string")
    if type(options_text) is not str or type(protocol_cmake_text) is not str:
        raise TypeError("captured CMake inputs must be exact strings")
    owner = _source_protocol(source_rel, genome)
    supplied, bare_names, cache_names = _parse_supplied_macro_details(
        options_text, protocol_cmake_text,
    )
    cache_values = parse_options_defaults(options_text)
    cache_values.update({name: str(value) for name, value in genome.flags.items()})
    effective: Dict[str, str] = {}
    for macro in supplied:
        if macro in bare_names:
            effective[macro] = "1"
            continue
        cache_name = cache_names.get(macro)
        if cache_name is not None and cache_name in cache_values:
            effective[macro] = cache_values[cache_name]
    effective.update(PLATFORM_MACROS)
    return EffectiveDefineResolution(
        source_rel=source_rel,
        owner_protocol=owner,
        supplied_macros=supplied,
        bare_macros=bare_names,
        cache_by_tu_macro=tuple(sorted(cache_names.items())),
        effective_values=tuple(sorted(effective.items())),
    )


def _worktree_defines(sub: str, genome: Genome, source_rel: str | None = None) -> Dict[str, str]:
    """working-tree 版の実効 defines (実 TU 供給集合に揃えたもの、T-148 fix round)。"""
    options_text = _read(os.path.join(sub, OPTIONS_CMAKE))
    protocol = genome.protocol if source_rel is None else _source_protocol(source_rel, genome)
    proto_text = _read(os.path.join(sub, _protocol_cmake_rel(protocol)))
    supplied, bare_names, cache_names = _parse_supplied_macro_details(
        options_text, proto_text,
    )
    return _merge_defines(
        parse_options_defaults(options_text), genome.flags, supplied,
        bare_names=bare_names, cache_names=cache_names,
    )


def _head_defines(sub: str, genome: Genome, ccbench_commit: str,
                  source_rel: str | None = None) -> Dict[str, str]:
    """HEAD (pin) 版の実効 defines。baseline と working-tree で同じ絞り方を使う。"""
    options_text = _git_show(sub, ccbench_commit, OPTIONS_CMAKE)
    protocol = genome.protocol if source_rel is None else _source_protocol(source_rel, genome)
    proto_text = _git_show(sub, ccbench_commit, _protocol_cmake_rel(protocol))
    supplied, bare_names, cache_names = _parse_supplied_macro_details(
        options_text, proto_text,
    )
    return _merge_defines(
        parse_options_defaults(options_text), genome.flags, supplied,
        bare_names=bare_names, cache_names=cache_names,
    )


def canonical_source_preimage_bytes(
    genome: Genome, ccbench_dir: str = "", cxx: str = "g++-13",
) -> bytes:
    """Return the exact normalized bytes hashed for working-tree source identity.

    Source order, context normalization, the NUL delimiter, and UTF-8 encoding are
    the pre-existing ``_digest(parts)`` contract.  Exposing those bytes lets a
    later consumer rederive the digest without the mutable checkout or compiler.
    """
    sub = ccbench_dir or _ccbench_dir()
    parts = []
    for rel in EVOLVE_BLOCK_SOURCES:
        defines = _worktree_defines(sub, genome, rel)
        parts.append(_normalize_contexts(_read(os.path.join(sub, rel)), defines, cxx))
    return _canonical_preimage_bytes(parts)


def compute(genome: Genome, ccbench_dir: str = "", cxx: str = "g++-13") -> str:
    """working-tree の EVOLVE-BLOCK ソースを genome の defines で正規化した digest。

    T-148: 正規化は全マクロ文脈 (_context_overlays) で取り、TU 注入マクロの条件枝も
    identity に乗せる。defines は実 TU 供給集合まで絞る (_worktree_defines)。baseline と
    同一の文脈列・同一の絞り方を使うため stock (working-tree==HEAD) の src_token 正規化 =
    silo 8 golden id は不変。"""
    return hashlib.sha256(
        canonical_source_preimage_bytes(genome, ccbench_dir, cxx)
    ).hexdigest()


def assert_includes_match_head(genome: Genome, ccbench_commit: str,
                               ccbench_dir: str = "", cxx: str = "g++-13") -> None:
    """EVOLVE_BLOCK_SOURCES の #include 行集合が HEAD baseline と一致するか (fails-closed)。

    preprocess は #include を除去してから走る (環境非依存化) ので、include の追加/削除/
    差し替えは digest に現れない = 「別ファイルを取り込みバイナリが変わるのに identity 不変」
    の死角になる (2026-07-03 敵対検証 high)。coder は #if 枝しか触れず #include 追加は
    phase3.md の閉じた領域制約で禁止なので、include 行が HEAD と 1 行でも違えば逸脱として
    停止する。順序込みで比較 (include 順序も取り込むヘッダを変えうる)。git show 失敗は
    identity 核ゆえ RuntimeError (best-effort skip を持ち込まない)。"""
    sub = ccbench_dir or _ccbench_dir()
    for rel in EVOLVE_BLOCK_SOURCES:
        cur = _include_lines(_read(os.path.join(sub, rel)))
        base = _include_lines(_git_show(sub, ccbench_commit, rel))
        if cur != base:
            raise RuntimeError(
                f"source_digest: {rel} の #include 行集合が HEAD baseline と不一致 — "
                "coder の #include 追加/差し替えは preprocess 後 digest に現れず偽 cache hit "
                "の死角になるため停止 (phase3.md 閉じた領域制約 / 2026-07-03 敵対検証 high)。\n"
                f"  HEAD: {base!r}\n  現在: {cur!r}")


def _trace_pair_diff(source_text: str, defines: Dict[str, str], cxx: str) -> List[str]:
    """TRACE=1 と TRACE=0 の正規化出力の差分**内容** (unified diff の +/- 行のみ)。

    ハンクヘッダ (@@ 行番号) は比較素材から除外する — variant の正当な payload 編集
    (TRACE 非依存) でも行数が動けばハンク位置はずれるため、位置を比較に入れると
    偽陽性になる。差分の中身 (どの行が TRACE で増減するか) だけを見る。
    TRACE は最後に明示上書きする (Options.cmake の CCBENCH_TRACE 既定 0 に依存しない。
    genome.flags への TRACE 混入は model.Genome が禁止済み)。
    T-148: 差分も全マクロ文脈で取る — 素文脈だけだと `#ifdef GLOBAL_VALUE_DEFINE` の内側に
    `#if TRACE` を隠す攻撃が両 TRACE 値とも dead で D_variant==D_stock になり素通りする
    (規律1 の穴)。文脈タグを行に前置し、別文脈間の差分相殺も防ぐ。"""
    out: List[str] = []
    for overlay in _context_overlays():
        tag = ",".join(f"{k}={v}" for k, v in sorted(overlay.items())) or "base"
        base = dict(defines, **overlay)
        p1 = _cpp_normalize(source_text, dict(base, TRACE="1"), cxx)
        p0 = _cpp_normalize(source_text, dict(base, TRACE="0"), cxx)
        diff = difflib.unified_diff(p0.splitlines(), p1.splitlines(), n=0, lineterm="")
        out.extend(f"[ctx:{tag}]{ln}" for ln in diff
                   if ln[:1] in "+-" and not ln.startswith(("+++", "---")))
    return out


def assert_trace_diff_matches_head(genome: Genome, ccbench_commit: str,
                                   ccbench_dir: str = "", cxx: str = "g++-13") -> None:
    """観測者効果の二重検査 — diff-of-diffs (phase3.md blocking / D30 一次防壁)。

    述語: working-tree の preprocess(TRACE=1) − preprocess(TRACE=0) の差分 D_variant が、
    pinned HEAD から同様に取った D_stock と**一致**する。つまり「variant が TRACE 条件付き
    コードを追加/改変していない = trace/perf ビルドの差は stock の trace-hook 由来のみ」を
    機械保証する (規律1: 観測者効果の分離)。nm の name-based 検査 (_assert_no_trace_symbols)
    が見逃す data-structure 観測者効果・`#ifdef TRACE` の内側に挙動差を隠す攻撃も、
    D_variant≠D_stock として捕える。対象 = EVOLVE_BLOCK_SOURCES (coder の編集面全体。
    それ以外の worktree 改変は assert_worktree_within_allowlist が既に遮断)。

    fails-closed: diff 不一致・preprocess 取得不能 (RuntimeError 伝播) とも abort
    (警告に格下げしない)。**保証しないこと (正直に):** 検証専用メタデータが #if TRACE の
    **外** (両ビルド共通) に常駐するケースはこの述語では判定不能 — その場合コストは perf
    ビルドにも乗り fitness が自己ペナルティを受けるため false-green にはならず、意味判定は
    auditor / 人間レビュー領域 (phase3.md タスク定義)。"""
    sub = ccbench_dir or _ccbench_dir()
    # buildcache._assert_trace_diff invokes this gate after its preceding
    # _recheck_source_evidence/resolve_evidence call.  The latter validates the
    # repo-absent registry; this function keeps the per-source owner split here
    # and does not reintroduce one shared genome-level define set.
    for rel in EVOLVE_BLOCK_SOURCES:
        cur_defines = _worktree_defines(sub, genome, rel)
        head_defines = _head_defines(sub, genome, ccbench_commit, rel)
        d_var = _trace_pair_diff(_read(os.path.join(sub, rel)), cur_defines, cxx)
        d_stock = _trace_pair_diff(_git_show(sub, ccbench_commit, rel), head_defines, cxx)
        if d_var != d_stock:
            raise RuntimeError(
                f"source_digest: 観測者効果の二重検査 (diff-of-diffs) 不一致 — {rel} の "
                "TRACE=1/TRACE=0 preprocess 差分が pinned HEAD の同差分と食い違う。variant が "
                "TRACE 条件付きコードを追加/改変した疑い (規律1: 検証コードの perf ビルド混入、"
                "または #ifdef TRACE 内側への挙動差の隠蔽) → fails-closed で停止 "
                "(phase3.md blocking / D30)。\n"
                f"  D_stock ({len(d_stock)} 行): {d_stock[:8]!r}\n"
                f"  D_variant ({len(d_var)} 行): {d_var[:8]!r}")


def baseline(genome: Genome, ccbench_commit: str, ccbench_dir: str = "",
             cxx: str = "g++-13") -> str:
    """HEAD (commit) の stock ソース (patch 前) を同じ defines で正規化した digest。

    defaults も Options.cmake の HEAD 版から取る (patch が足した CCBENCH_BACKOFF_FIXED が
    無くても HEAD backoff.hh はそれを #if 参照しないので preprocess は変わらない)。
    供給集合の絞り込み (T-148 fix round) も HEAD 版 CMake から取り、working-tree 側と
    同じ規則で行う。
    """
    sub = ccbench_dir or _ccbench_dir()
    parts = []
    for rel in EVOLVE_BLOCK_SOURCES:
        defines = _head_defines(sub, genome, ccbench_commit, rel)
        parts.append(_normalize_contexts(
            _git_show(sub, ccbench_commit, rel), defines, cxx,
        ))
    return _digest(parts)


def _bind_backoff_grammar_version(
    raw_digest: str, backoff_grammar_version: Optional[int],
) -> str:
    """Domain-separate a non-stock source digest for one explicit grammar."""

    if backoff_grammar_version is None:
        return raw_digest
    if (type(backoff_grammar_version) is not int
            or backoff_grammar_version < 1):
        raise ValueError(
            "backoff_grammar_version must be None or an exact positive integer"
        )
    preimage = (
        b"backoff-src-token/v1\0grammar="
        + str(backoff_grammar_version).encode("ascii")
        + b"\0source="
        + raw_digest.encode("ascii")
    )
    return hashlib.sha256(preimage).hexdigest()


def _bind_sort_oracle_contract_id(
    raw_digest: str, sort_oracle_contract_id: Optional[str],
) -> str:
    """Domain-separate a non-stock source digest for one sort oracle contract."""

    if sort_oracle_contract_id is None:
        return raw_digest
    if (type(sort_oracle_contract_id) is not str
            or not sort_oracle_contract_id
            or "\0" in sort_oracle_contract_id
            or not sort_oracle_contract_id.isascii()):
        raise ValueError(
            "sort_oracle_contract_id must be None or a non-empty ASCII str "
            "without NUL"
        )
    preimage = (
        b"sort-src-token/v1\0contract="
        + sort_oracle_contract_id.encode("ascii")
        + b"\0source="
        + raw_digest.encode("ascii")
    )
    return hashlib.sha256(preimage).hexdigest()


def _resolved_src_token(
    current: str, baseline_digest: str, backoff_grammar_version: Optional[int],
    *, sort_oracle_contract_id: Optional[str] = None,
) -> str:
    if (backoff_grammar_version is not None
            and sort_oracle_contract_id is not None):
        raise ValueError(
            "backoff_grammar_version and sort_oracle_contract_id are mutually exclusive"
        )
    if current == baseline_digest:
        return STOCK
    if sort_oracle_contract_id is not None:
        return _bind_sort_oracle_contract_id(
            current, sort_oracle_contract_id,
        )
    return _bind_backoff_grammar_version(current, backoff_grammar_version)


def src_token(genome: Genome, ccbench_commit: str, ccbench_dir: str = "",
              cxx: str = "g++-13", *,
              backoff_grammar_version: Optional[int] = None) -> str:
    """identity に織り込む src トークン。

    working-tree が stock/inert (HEAD baseline と同一 digest) なら "stock" (後方互換:
    pre-image から省かれ旧 id を温存)、coder が枝を変えていれば実 digest を返す。
    """
    cur = compute(genome, ccbench_dir, cxx)
    base = baseline(genome, ccbench_commit, ccbench_dir, cxx)
    return _resolved_src_token(cur, base, backoff_grammar_version)


def _tracked_status_paths(ccbench_dir: str = "") -> tuple[str, ...]:
    """Return sorted tracked paths from one porcelain snapshot; ignore untracked output."""

    sub = ccbench_dir or _ccbench_dir()
    try:
        r = subprocess.run(["git", "-C", sub, "status", "--porcelain"],
                           capture_output=True, text=True, env=_sanitized_git_env())
    except (OSError, subprocess.SubprocessError) as e:
        raise RuntimeError(
            f"source_digest: git status 起動失敗 ({e}) — working-tree の健全性を "
            "確認できず fails-closed (D23)") from e
    if r.returncode != 0:
        raise RuntimeError(
            f"source_digest: git status 失敗 (rc={r.returncode}) → fails-closed。\n"
            f"  {r.stderr.strip()[-300:]}")
    paths = set()
    for line in r.stdout.splitlines():
        if not line.strip():
            continue
        xy, path = line[:2], line[3:]
        if xy == "??":                       # untracked = build 生成物等、ソース改変でない
            continue
        if " -> " in path:                   # rename: "old -> new"
            path = path.split(" -> ")[-1]
        path = path.strip()
        if path:
            paths.add(path)
    return tuple(sorted(paths))


def _assert_paths_within_allowlist(paths: Iterable[str]) -> None:
    extra = set(paths) - set(ALLOWLIST)
    if extra:
        raise RuntimeError(
            "source_digest: ALLOWLIST 外の tracked 改変を検知 → 偽 cache hit を防ぐため "
            f"停止 (coder の編集面が EVOLVE-BLOCK を逸脱)。allowlist={sorted(ALLOWLIST)} "
            f"外={sorted(extra)} (D23)")


def _tracked_diff_sha256(ccbench_dir: str = "") -> str:
    """Hash the full staged+unstaged tracked diff against HEAD, including binary patches."""

    sub = ccbench_dir or _ccbench_dir()
    try:
        r = subprocess.run(
            ["git", "-C", sub, "diff", "--binary", "HEAD", "--"],
            capture_output=True, env=_sanitized_git_env(),
        )
    except (OSError, subprocess.SubprocessError) as e:
        raise RuntimeError(
            f"source_digest: git diff 起動失敗 ({e}) — tracked diff evidence を "
            "確定できず fails-closed (T-342)"
        ) from e
    if r.returncode != 0:
        stderr = r.stderr.decode("utf-8", errors="replace") if isinstance(r.stderr, bytes) else r.stderr
        raise RuntimeError(
            f"source_digest: git diff 失敗 (rc={r.returncode}) → fails-closed。\n"
            f"  {(stderr or '').strip()[-300:]}"
        )
    payload = r.stdout if isinstance(r.stdout, bytes) else r.stdout.encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def assert_worktree_within_allowlist(ccbench_dir: str = "") -> None:
    """submodule working-tree の tracked 改変が ALLOWLIST 内か検査する (fails-closed)。

    coder の編集面は EVOLVE-BLOCK (= template patch が touch するファイル) に閉じている
    べき。それを超えた tracked 改変 (例 transaction.cc の M) は source_digest が覆わない
    偽 hit 源 (D23 finding F-allowlist) なので停止する。untracked (??、build 生成物等) は
    無視する。git が無い/失敗は identity 核なので fails-closed。
    """

    _assert_paths_within_allowlist(_tracked_status_paths(ccbench_dir))


def resolve_evidence(
    genome: Genome,
    ccbench_commit: str,
    *,
    ccbench_dir: str = "",
    cxx: str = "g++-13",
    backoff_grammar_version: Optional[int] = None,
    sort_oracle_contract_id: Optional[str] = None,
    require_gate_witness: bool = False,
) -> SourceEvidence:
    """Resolve build evidence and bind it to the inspected source root.

    The status snapshot yields ``tracked_clean`` and the exact tracked path set; its corresponding
    full tracked diff is hashed before source normalization.  The checkout is still mutable, so a
    later consumer must compare a freshly resolved full ``SourceEvidence`` at the build boundary.
    """

    sub = ccbench_dir or _ccbench_dir()
    source_root = os.path.realpath(os.path.abspath(sub))
    tracked_paths = _tracked_status_paths(sub)
    _assert_paths_within_allowlist(tracked_paths)
    tracked_diff_sha256 = _tracked_diff_sha256(sub)
    if (not tracked_paths) != (tracked_diff_sha256 == EMPTY_TRACKED_DIFF_SHA256):
        raise RuntimeError(
            "source_digest: git status と tracked diff が同一 clean/dirty 状態を示さない — "
            "取得中の source 変更または mixed snapshot の疑いのため fails-closed (T-342)"
        )
    assert_includes_match_head(genome, ccbench_commit, sub, cxx)
    assert_conditional_macros_covered(genome, sub, cxx)
    current = compute(genome, sub, cxx)
    base = baseline(genome, ccbench_commit, sub, cxx)
    token = _resolved_src_token(
        current,
        base,
        backoff_grammar_version,
        sort_oracle_contract_id=sort_oracle_contract_id,
    )
    genome_sha256 = hashlib.sha256(genome.canonical().encode("utf-8")).hexdigest()
    return SourceEvidence(
        schema_version=SOURCE_EVIDENCE_SCHEMA,
        source_root=source_root,
        ccbench_commit=ccbench_commit,
        genome_sha256=genome_sha256,
        src_token=token,
        source_bytes_sha256=current,
        tracked_clean=not tracked_paths,
        tracked_diff_sha256=tracked_diff_sha256,
        tracked_paths=tracked_paths,
        proof_source_snapshot=capture_compiled_protocol_source_snapshot(
            genome.protocol, source_root,
            require_gate_witness=require_gate_witness,
        ),
        verification_variant=verification_variant_id(genome, token),
    )


def resolve(genome: Genome, ccbench_commit: str, ccbench_dir: str = "",
            cxx: str = "g++-13", *,
            backoff_grammar_version: Optional[int] = None) -> str:
    """variant の identity (src_token) を確定する単一窓口 = allowlist 検査 + src_token。

    **WAL は書かない** (呼び手が skip 判定・abort 記録を担う) ので、loop (評価前に skip キーを
    決める) と pipeline.evaluate (直接 caller の自己計算) の両方が同じ計算を共有でき、id 確定点が
    二重化しない (D23/D24: identity を消費側まで一致させる)。**fails-closed**: allowlist 逸脱・
    #include 行の HEAD 不一致・条件指令の未知マクロ / __has_include・preprocess 失敗・git show
    失敗は RuntimeError (best-effort skip を identity 核に持ち込まない)。"""
    assert_worktree_within_allowlist(ccbench_dir)
    assert_includes_match_head(genome, ccbench_commit, ccbench_dir, cxx)  # #include 死角 (最小案)
    assert_conditional_macros_covered(genome, ccbench_dir, cxx)           # マクロ文脈死角 (T-148)
    return src_token(
        genome,
        ccbench_commit,
        ccbench_dir,
        cxx,
        backoff_grammar_version=backoff_grammar_version,
    )
