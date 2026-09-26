#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""後続段 4 (coder 自律期) の diff 検疫層 (4a・新機構、phase3-s4-design-v1.md §1)。

coder (LLM) が合成した #if 枝コードを orchestrator がテンプレフレームに挿入したあと、
`git diff HEAD -- <EVOLVE-BLOCK ソース>` を読んで **変更が EVOLVE-BLOCK の hole 内に
収まっているか** を検証する fails-closed モジュール (source_digest / patchharness と同格)。

役割分担 (方針 A / D30/D33 / GW2R-1 の教訓):
- **主 gate = 行封じ込め (structural・load-bearing)。** diff の物理行構造だけを見て
  「変更行 ⊆ hole の物理行域」「フレーム行 (マーカー・#if/#else/#endif・stock 枝) は
  byte 不変 (= '+'/'-' に現れない)」を検査する。これは C++ レキサ回避 (backslash-newline
  splice 等) の影響を受けない — diff の行構造と固定行を見るだけだから。
- **内容検査 (`#` 指令・マーカー文字列・コメント delimiter byte・行末 backslash の拒否) =
  二次的な保守 gate。** コメント構文を解析せず、文字列・raw string 内も byte 一致で拒否する。
  明白な注入を早期に構造化 reject するが、当モジュールが保証するのは structural containment
  のみであり、C++ の意味 admission ではない。source_digest は実行する source の identity
  だけを束縛する。build_admission が既定拒否するのは caller が ``CODER_DERIVED`` と
  **自己分類した build request** であり、source bytes から provenance を検出してはいない。
  structural quarantine 単体は C++ の意味 security を提供しない。後段では有限 lexical
  coder-effect gate が受理集合を狭め、sort/trigger driver の auditor verdict は
  **mandatory deny-only veto; affirmative security credit なし**として build を止める。
  source 由来 capability と cache/replay class 束縛を欠くため、admission 層全体はまだ閉じていない。

**1 呼び出しにつき caller が指定した単一マーカーを検査する。** 複数マーカーを一括して
完全性検査する marker set completeness predicate / hunk-to-marker assignment は持たない
(design-v1 §1 敵対検証 contested #6)。

rejection は S4 rejection digest の新型 (rejection_type="diff-quarantine") として
構造化して返す (規律3・D37 パターン。critic が「形状から推理」せず「データから読み取る」)。
"""
from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Tuple


class DiffRejectSubtype(Enum):
    """S4 diff-quarantine の rejection サブタイプ (構造化診断用)。"""
    FRAME_ALTERED = "frame-altered"      # フレーム (マーカー/#if/#else/#endif/stock 枝) を触った
    HOLE_ESCAPE = "hole-escape"          # hole 内に禁止指令・マーカー・delimiter/splice が混入
    OUTSIDE_REGION = "outside-region"    # EVOLVE-BLOCK 領域外 (別行・別ファイル) に変更あり
    MALFORMED = "malformed"              # diff がパース不能 / HEAD と行が不整合 (fail-closed)
    HOST_EFFECT = "host-effect"          # structural pass 後の有限 lexical 効果 gate
    BACKOFF_GRAMMAR = "backoff-grammar"  # backoff marker 専用 Tier 1 grammar
    SORT_SWO_ORACLE = "sort-swo-oracle"  # 実型 relation matrix の独立 SWO oracle
    POLICY_GRAMMAR = "policy-grammar"
    POLICY_COMPILE = "policy-compile"


# hole 内で禁止する「行頭前処理指令」の検出。行頭 (先行空白許容) が `#`、または
# C++ の digraph `%:` (= `#`) で始まる行を指令とみなす。trigraph `??=` は C++17 で
# 廃止されたが念のため併記。**この検査の完全性は load-bearing ではない** (docstring 参照)。
# source_digest は回避後 bytes の identity を分けるだけで、意味上の安全性は証明しない。
_DIRECTIVE_RE = re.compile(r'^\s*(?:#|%:|\?\?=)')
# マーカー偽装検出は実際の marker 指令形 (BEGIN/END) に限定する。bare "EVOLVE-BLOCK" 部分文字列
# 一致は末尾コメント等の偶発的言及を誤 reject した (敵対 red-team 2026-07-07 false-positive)。
# 偶発的言及は parse_template_file の順序走査 (BEGIN→#if→#else→#endif→END) を汚染しない一方、
# 偽 BEGIN/END 指令だけは将来の再 parse を混乱させ得るので、そこだけ弾く。
_MARKER_RE = re.compile(r'EVOLVE-BLOCK-(?:BEGIN|END)')

# hole 内の内容検査は C++ のコメント構文を解釈しない。delimiter byte が文字列・raw
# string 内にあっても拒否する保守則とし、物理行末 backslash も line splice の入口として
# 閉じる (D33: text gate に翻訳フェーズの完全再現を載せない)。
_LINE_COMMENT_DELIMITER = "//"
_BLOCK_COMMENT_OPEN_DELIMITER = "/*"
# テンプレ原文は人間レビュー済みの designated source なので、物理行内で閉じる `//`
# は許可する。一方、coder 生成の挿入行は非信頼入力であり、文字列等との区別もせず
# `//` を含めて保守的に拒否する。テンプレ側でも後続の挿入行へ字句文脈を漏らし得る
# block comment delimiter は禁止し、line splice は別途行末 byte で拒否する。
_TEMPLATE_CONTEXT_LEAK_DELIMITERS = ("/*", "*/")

_BRANCH_DIRECTIVE = "content-directive"
_BRANCH_MARKER = "content-marker"
_BRANCH_LINE_COMMENT = "content-comment-line"
_BRANCH_BLOCK_COMMENT = "content-comment-block"
_BRANCH_LINE_SPLICE = "content-line-splice"
_BRANCH_TEMPLATE_COMMENT = "template-hole-comment-delimiter"
_BRANCH_TEMPLATE_SPLICE = "template-hole-line-splice"
_BRANCH_TRUNCATED_HUNK = "malformed-truncated-hunk"
_BRANCH_HUNK_HEADER = "malformed-hunk-header"
_BRANCH_OUTSIDE_HUNK = "malformed-outside-hunk"
_BRANCH_HEAD_RANGE = "head-anchor-range"
_BRANCH_HEAD_CONTENT = "head-anchor-content"
_BRANCH_OUTSIDE_FILE = "outside-file"
_BRANCH_DELETE_OUTSIDE = "delete-outside-hole"
_BRANCH_INSERT_OUTSIDE = "insert-outside-hole"


def _redacted_line_evidence(branch: str, line_label: str, line_number: int,
                            content: str) -> str:
    """非信頼行を逐語再掲せず、位置・byte 長・短縮 digest へ射影する。"""
    content_bytes = content.encode("utf-8")
    content_sha = hashlib.sha256(content_bytes).hexdigest()[:12]
    return (f"branch={branch} {line_label}={line_number} "
            f"byte_length={len(content_bytes)} sha256_12={content_sha}")


@dataclass
class TemplateMarker:
    """テンプレの EVOLVE-BLOCK マーカー領域 (1-indexed 行番号 + 原文テキスト)。"""
    marker_id: str                    # 例 "silo-backoff-magnitude"
    source_rel: str                   # EVOLVE_BLOCK_SOURCES の相対パス 例 "include/backoff.hh"
    begin_line: int                   # "EVOLVE-BLOCK-BEGIN <id>" の行
    if_line: int                      # "#if BACKOFF_FIXED >= 0" の行
    else_line: int                    # "#else" の行
    endif_line: int                   # "#endif" の行
    end_line: int                     # "EVOLVE-BLOCK-END <id>" の行
    frame_text: Dict[int, str] = field(default_factory=dict)  # フレーム行番号 -> 逐語テキスト
    hole_text: Dict[int, str] = field(default_factory=dict)   # hole 原文行番号 -> 逐語テキスト

    @property
    def hole_first(self) -> int:
        """hole の先頭行 (#if の次)。"""
        return self.if_line + 1

    @property
    def hole_last(self) -> int:
        """hole の末尾行 (#else の前)。空 hole なら hole_first > hole_last。"""
        return self.else_line - 1

    def in_hole(self, src_ln: int) -> bool:
        """src_ln が hole の内部 (#if と #else の間) か。"""
        return self.if_line < src_ln < self.else_line

    def in_block(self, src_ln: int) -> bool:
        """src_ln が EVOLVE-BLOCK 領域 (BEGIN..END) の内側か。"""
        return self.begin_line <= src_ln <= self.end_line


@dataclass
class _WalkLine:
    """diff hunk 内の 1 物理行を source/dest 行番号付きで表現。"""
    prefix: str          # '+', '-', ' '
    content: str
    src_ln: Optional[int]   # ' '/'-' のとき source ファイル行番号、'+' は None
    dst_ln: Optional[int]   # ' '/'+' のとき dest ファイル行番号、'-' は None
    anchor: int             # '+' が挿入される source 側の位置 (直後の source 行番号)


@dataclass
class DiffHunk:
    """unified diff の 1 ハンク。"""
    source_start: int
    source_count: int
    dest_start: int
    dest_count: int
    lines: List[Tuple[str, str]]   # (prefix, content)
    file_rel: str = ""             # このハンクが属するファイル (+++ b/<path> 由来)

    def walk(self) -> List[_WalkLine]:
        """各物理行を source/dest 行番号を追跡しながら列挙する。

        '+' 行の anchor = その行が挿入される直後の source 行番号 (連続する '+' の間は
        source_ln が進まないので同じ anchor を共有する)。"""
        out: List[_WalkLine] = []
        src = self.source_start
        dst = self.dest_start
        for prefix, content in self.lines:
            if prefix == ' ':
                out.append(_WalkLine(prefix, content, src, dst, src))
                src += 1
                dst += 1
            elif prefix == '-':
                out.append(_WalkLine(prefix, content, src, None, src))
                src += 1
            elif prefix == '+':
                out.append(_WalkLine(prefix, content, None, dst, src))
                dst += 1
        return out


@dataclass
class DiffQuarantineResult:
    """diff 検疫の結果。passed=False のとき digest に S4 rejection の構造化理由。"""
    passed: bool
    subtype: Optional[DiffRejectSubtype] = None
    reason: Optional[str] = None
    digest: Optional[Dict] = None      # critic/次手へ渡す構造化 digest (D37 パターン)
    violations: List[Dict] = field(default_factory=list)  # 検出した全違反 (先頭が primary)


_HUNK_RE = re.compile(r'^@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@')
# `+++ b/path`。git は `+++ b/include/backoff.hh` を出す (submodule 内は submodule root 相対)。
_PLUSFILE_RE = re.compile(r'^\+\+\+ (?:b/)?(.*?)(?:\t.*)?$')
# git が付す no-newline 注記 (内容行でなく、直前の +/-/context 行に付く = カウント消費しない)。
_NO_NEWLINE = "\\ No newline at end of file"


@dataclass
class ParsedDiff:
    """parse_diff の結果。malformed=True なら validate() は fail-closed で reject する。"""
    hunks: List[DiffHunk]
    malformed: bool = False
    reason: str = ""


def parse_diff(diff_text: str) -> ParsedDiff:
    """unified diff をハンク列に parse する。`+++ b/<path>` を追ってファイルを紐付ける。

    **fail-closed:** diff 構造 (ハンクヘッダ様の行) がありながら 1 つもハンクを取り出せない、
    ハンク本体が宣言カウントを満たさず途中終端する、no-newline 以外の生 `\\` 行が混ざる、等の
    不正入力は malformed=True にして「空 diff = 変更なし」との取り違え (fails-OPEN) を防ぐ
    (敵対 red-team 2026-07-07 で発見した未パースヘッダ・bare-backslash desync クラスへの対策)。
    """
    hunks: List[DiffHunk] = []
    lines = diff_text.split('\n')
    cur_file = ""
    i = 0
    n = len(lines)
    malformed = False
    reason = ""
    while i < n:
        raw = lines[i].rstrip('\r')
        mf = _PLUSFILE_RE.match(raw)
        if mf and raw.startswith('+++ '):
            cur_file = mf.group(1)
            i += 1
            continue
        m = _HUNK_RE.match(raw)
        if m:
            ss = int(m.group(1))
            sc = int(m.group(2) or 1)
            ds = int(m.group(3))
            dc = int(m.group(4) or 1)
            hunk_lines: List[Tuple[str, str]] = []
            i += 1
            # 本体はハンクヘッダの宣言カウント (source_count/dest_count) を消費して読む。
            # パターン照合で終端を探さない = 削除行内容が偶然 "--- " で始まる等の誤認を排除。
            src_left, dst_left = sc, dc
            while i < n and (src_left > 0 or dst_left > 0):
                cur = lines[i]
                curr = cur.rstrip('\r')
                if curr == _NO_NEWLINE:         # 直前行への注記。カウント消費なしで飛ばす
                    i += 1
                    continue
                p = cur[:1]
                if p == ' ':
                    hunk_lines.append((' ', curr[1:]))
                    src_left -= 1
                    dst_left -= 1
                elif p == '-':
                    hunk_lines.append(('-', curr[1:]))
                    src_left -= 1
                elif p == '+':
                    hunk_lines.append(('+', curr[1:]))
                    dst_left -= 1
                else:
                    break                       # 不正 prefix (bare `\`・`\r`・空) = 途中終端
                i += 1
            if src_left > 0 or dst_left > 0:
                # 宣言カウントを満たせなかった = ハンク truncated / 不正行混入 (fail-closed)。
                malformed = True
                content = lines[i].rstrip('\r') if i < n else ""
                reason = _redacted_line_evidence(
                    _BRANCH_TRUNCATED_HUNK, "diff_line", i + 1, content,
                )
                break
            hunks.append(DiffHunk(ss, sc, ds, dc, hunk_lines, cur_file))
        elif raw.startswith('@@'):
            # ハンクヘッダ様だが _HUNK_RE 不一致 (行番号詐称 `@@ --5,1 @@` 等) = 未パース (fail-closed)。
            malformed = True
            reason = _redacted_line_evidence(
                _BRANCH_HUNK_HEADER, "diff_line", i + 1, raw,
            )
            break
        elif raw.startswith(('--- ', 'diff --git ', 'index ')):
            i += 1                          # 既知のファイルヘッダ (無害) — 無視
        elif raw[:1] in ('+', '-'):
            # ハンク外に現れた body 様行 (`+`/`-`)。git は body 行を必ず正しくカウントした
            # ハンク内に置くので、これは (a) ヘッダ無しの裸 body か (b) 宣言カウント超過の残滓。
            # 黙って読み飛ばすと「空 diff = 変更なし」と誤認して fails-OPEN する
            # (敵対 red-team 2026-07-07 defeat-head-anchor) → fail-closed で reject。
            malformed = True
            reason = _redacted_line_evidence(
                _BRANCH_OUTSIDE_HUNK, "diff_line", i + 1, raw,
            )
            break
        else:
            i += 1
    return ParsedDiff(hunks=hunks, malformed=malformed, reason=reason)


class DiffQuarantine:
    """unified diff をテンプレ構造に照合する fails-closed gate。

    強制する不変条件:
    1. 変更ファイルは marker.source_rel のみ (他ファイル改変 = outside-region)。
    2. フレーム行 (マーカー・#if・#else・stock 枝・#endif) は byte 不変 ('+'/'-' に出ない)。
    3. 変更行 (削除 source 行・挿入 anchor) はすべて hole 内部。
    4. (二次・保守 byte gate) hole 内挿入行に生指令・マーカー・コメント delimiter・
       行末 backslash が無い。
    5. テンプレ hole 原文には文脈漏洩する block comment delimiter・行末 backslash が無い
       (`//` は信頼済み原文の物理行内で閉じるため許可)。
    """

    def __init__(self, template_marker: TemplateMarker, working_diff: str,
                 head_text: Optional[str] = None):
        """
        Args:
            template_marker: テンプレ (HEAD) から parse したマーカー定義。
            working_diff: `git diff HEAD -- <file>` の出力。
            head_text: 対象ファイルの **HEAD 内容** (`git show HEAD:<file>`)。渡すと各ハンクの
                context/削除行が申告行番号の HEAD 内容と一致するかを照合し (アンカー検証)、
                ハンクヘッダの行番号詐称・desync でフレーム/領域外変更を hole 内に誤帰属させる
                攻撃 (敵対 red-team 2026-07-07) を fail-closed で封じる。**自律ループは必ず渡すこと**
                — None のときは行番号を信頼するしかなく、信頼できる diff producer (git diff HEAD)
                専用の縮退モードになる。"""
        self.marker = template_marker
        self.diff_text = working_diff
        self.head_lines: Optional[List[str]] = (
            [ln.rstrip('\r') for ln in head_text.split('\n')] if head_text is not None else None)
        self.parsed: ParsedDiff = parse_diff(working_diff)
        self.hunks: List[DiffHunk] = self.parsed.hunks

    # -- 分類ヘルパ --------------------------------------------------------

    def _classify_src(self, src_ln: int) -> DiffRejectSubtype:
        """hole 外の source 行が「フレーム」か「領域外」か。"""
        if self.marker.in_block(src_ln):
            return DiffRejectSubtype.FRAME_ALTERED
        return DiffRejectSubtype.OUTSIDE_REGION

    def _classify_anchor(self, anchor: int) -> DiffRejectSubtype:
        """hole 外への挿入 anchor が「フレーム」か「領域外」か。

        anchor は「その source 行の直前に挿入」を意味する。BEGIN..END+1 の範囲内への
        挿入 = フレーム改変、それ以外 = 領域外。"""
        if self.marker.begin_line <= anchor <= self.marker.end_line + 1:
            return DiffRejectSubtype.FRAME_ALTERED
        return DiffRejectSubtype.OUTSIDE_REGION

    def _mk_digest(self, subtype: DiffRejectSubtype, reason: str,
                   diff_region: str, evidence: str) -> Dict:
        return {
            "rejection_type": "diff-quarantine",
            "subtype": subtype.value,
            "reason": reason,
            "diff_region": diff_region,
            "template_diff_id": self.marker.marker_id,
            "evidence": evidence,
        }

    @staticmethod
    def _line_evidence(branch: str, line_label: str, line_number: int,
                       content: str) -> str:
        """拒否行を逐語再掲せず、位置・byte 長・短縮 digest だけを返す。"""
        return _redacted_line_evidence(branch, line_label, line_number, content)

    def _content_evidence(self, branch: str, w: _WalkLine) -> str:
        """hole 挿入行用の非逐語 evidence。"""
        return self._line_evidence(branch, "anchor_line", w.anchor, w.content)

    def _check_template_hole_invariant(self) -> Optional[Dict]:
        """テンプレ hole 原文に文脈漏洩 delimiter / line splice が無いことを検査する。

        head_text があればそれを正本とし、無い縮退モードでは parse_template_file が保持した
        hole_text を使う。`/*` / `*/` または行末 backslash があれば、後続の coder 挿入行を
        token なしでコメント化し得るため、空 diff を含め MALFORMED で fail-closed にする。
        `//` は信頼済み原文の物理行内で完結するため許可する (行末 backslash との組合せは
        splice 検査が拒否)。非信頼の coder 挿入行では従来どおり `//` 自体も拒否する。
        """
        if self.head_lines is not None:
            hole_lines = []
            for src_ln in range(self.marker.hole_first, self.marker.hole_last + 1):
                if 1 <= src_ln <= len(self.head_lines):
                    hole_lines.append((src_ln, self.head_lines[src_ln - 1]))
        else:
            hole_lines = sorted(self.marker.hole_text.items())

        for src_ln, content in hole_lines:
            content = content.rstrip("\r")
            if any(delimiter in content
                   for delimiter in _TEMPLATE_CONTEXT_LEAK_DELIMITERS):
                return self._mk_digest(
                    DiffRejectSubtype.MALFORMED,
                    "テンプレ hole 原文に文脈漏洩する block comment delimiter byte を検出 "
                    "(fail-closed)",
                    f"template hole src 行 {src_ln}",
                    self._line_evidence(
                        _BRANCH_TEMPLATE_COMMENT, "source_line", src_ln, content))
            if content.endswith("\\"):
                return self._mk_digest(
                    DiffRejectSubtype.MALFORMED,
                    "テンプレ hole 原文に行末 backslash を検出 (fail-closed)",
                    f"template hole src 行 {src_ln}",
                    self._line_evidence(
                        _BRANCH_TEMPLATE_SPLICE, "source_line", src_ln, content))
        return None

    def _check_head_anchor(self, h: DiffHunk) -> Optional[Dict]:
        """ハンクの context/削除行が申告 source 行番号の HEAD 内容と一致するか検証。

        不一致なら MALFORMED digest を返す (= ハンクヘッダが行番号を詐称 or desync している)。
        一致すれば None。これにより walk() が導く src 行番号がすべて HEAD の実体に錨づけされ、
        行番号詐称でフレーム/領域外行を hole 行番号に見せかける攻撃が成立しなくなる。"""
        assert self.head_lines is not None
        H = self.head_lines
        for w in h.walk():
            if w.prefix in (' ', '-'):
                if not (1 <= w.src_ln <= len(H)):
                    return self._mk_digest(
                        DiffRejectSubtype.MALFORMED,
                        "ハンクの申告行番号が HEAD の範囲外 (行番号詐称の疑い)",
                        f"src 行 {w.src_ln} (HEAD 行数 {len(H)})",
                        self._line_evidence(
                            _BRANCH_HEAD_RANGE, "source_line", w.src_ln, w.content))
                if H[w.src_ln - 1] != w.content:
                    return self._mk_digest(
                        DiffRejectSubtype.MALFORMED,
                        "ハンクの context/削除行が HEAD 内容と不一致 (行番号詐称 or desync)",
                        f"src 行 {w.src_ln}",
                        self._line_evidence(
                            _BRANCH_HEAD_CONTENT, "source_line", w.src_ln, w.content))
        return None

    # -- 本体 --------------------------------------------------------------

    def validate(self) -> DiffQuarantineResult:
        violations: List[Dict] = []

        # (0a) パース不能/不整合 diff は fail-closed で reject (空 diff との取り違え防止)。
        if self.parsed.malformed:
            d = self._mk_digest(DiffRejectSubtype.MALFORMED,
                                "diff がパースできない / 構造不正 (fail-closed)",
                                "diff 全体", self.parsed.reason)
            return DiffQuarantineResult(passed=False, subtype=DiffRejectSubtype.MALFORMED,
                                        reason=d["reason"], digest=d, violations=[d])

        # (0b) テンプレ hole 原文の安全な字句境界を先に確認する。空 diff でも汚染済み
        #      テンプレを安全と扱わない。
        template_bad = self._check_template_hole_invariant()
        if template_bad is not None:
            return DiffQuarantineResult(
                passed=False, subtype=DiffRejectSubtype.MALFORMED,
                reason=template_bad["reason"], digest=template_bad,
                violations=[template_bad])

        # (0c) 真に空の diff = 変更なし。何も逸脱していない (no-op 判定は orchestrator の責務)。
        if not self.hunks:
            return DiffQuarantineResult(passed=True)

        for h in self.hunks:
            # (1) ファイル面: marker.source_rel 以外への変更は領域外。
            if h.file_rel and not _same_file(h.file_rel, self.marker.source_rel):
                violations.append(self._mk_digest(
                    DiffRejectSubtype.OUTSIDE_REGION,
                    "編集面外のファイルに変更あり",
                    f"{h.file_rel} @@ -{h.source_start} +{h.dest_start}",
                    self._line_evidence(
                        _BRANCH_OUTSIDE_FILE, "source_line", h.source_start, h.file_rel)))
                continue

            # (2) アンカー検証: context/削除行が申告行番号の HEAD 内容と一致するか。
            #     不一致 = ハンクヘッダが行番号を詐称 (or desync) → 封じ込め判定が信頼できない
            #     → fail-closed で reject (行番号詐称クラスを根絶)。head_text 未供与時は縮退。
            if self.head_lines is not None:
                anchor_bad = self._check_head_anchor(h)
                if anchor_bad is not None:
                    violations.append(anchor_bad)
                    continue

            for w in h.walk():
                if w.prefix == '-':
                    # 削除行: hole 内でなければフレーム/領域外の改変。
                    if not self.marker.in_hole(w.src_ln):
                        st = self._classify_src(w.src_ln)
                        violations.append(self._mk_digest(
                            st,
                            ("フレーム行 (マーカー/#if/#else/#endif/stock 枝) の削除・改変を検出"
                             if st is DiffRejectSubtype.FRAME_ALTERED
                             else "EVOLVE-BLOCK 領域外の行の削除・改変を検出"),
                            f"src 行 {w.src_ln}",
                            self._line_evidence(
                                _BRANCH_DELETE_OUTSIDE, "source_line", w.src_ln, w.content)))
                elif w.prefix == '+':
                    # 挿入行: anchor が hole 内でなければフレーム/領域外への挿入。
                    if not (self.marker.if_line < w.anchor <= self.marker.else_line):
                        st = self._classify_anchor(w.anchor)
                        violations.append(self._mk_digest(
                            st,
                            ("フレーム領域への行挿入を検出"
                             if st is DiffRejectSubtype.FRAME_ALTERED
                             else "EVOLVE-BLOCK 領域外への行挿入を検出"),
                            f"anchor src 行 {w.anchor}",
                            self._line_evidence(
                                _BRANCH_INSERT_OUTSIDE, "anchor_line", w.anchor, w.content)))
                        continue
                    # hole 内挿入 — 二次検査。C++ 構文を解釈せず、保守的な byte 規則で
                    # 生指令・マーカー・コメント delimiter・物理 line splice を拒否する。
                    if _DIRECTIVE_RE.match(w.content):
                        violations.append(self._mk_digest(
                            DiffRejectSubtype.HOLE_ESCAPE,
                            "hole 内に生の前処理指令 (#if/#else/#endif/#define/#include 等) を検出",
                            f"anchor src 行 {w.anchor}",
                            self._content_evidence(_BRANCH_DIRECTIVE, w)))
                    elif _MARKER_RE.search(w.content):
                        violations.append(self._mk_digest(
                            DiffRejectSubtype.HOLE_ESCAPE,
                            "hole 内に EVOLVE-BLOCK-BEGIN/END マーカー指令を検出 (フレーム偽装)",
                            f"anchor src 行 {w.anchor}",
                            self._content_evidence(_BRANCH_MARKER, w)))
                    elif _LINE_COMMENT_DELIMITER in w.content:
                        violations.append(self._mk_digest(
                            DiffRejectSubtype.HOLE_ESCAPE,
                            ("hole 内に禁止コメント delimiter byte を検出 "
                             "(文字列・raw string 内も保守的に拒否)"),
                            f"anchor src 行 {w.anchor}",
                            self._content_evidence(_BRANCH_LINE_COMMENT, w)))
                    elif _BLOCK_COMMENT_OPEN_DELIMITER in w.content:
                        violations.append(self._mk_digest(
                            DiffRejectSubtype.HOLE_ESCAPE,
                            ("hole 内に禁止コメント delimiter byte を検出 "
                             "(文字列・raw string 内も保守的に拒否)"),
                            f"anchor src 行 {w.anchor}",
                            self._content_evidence(_BRANCH_BLOCK_COMMENT, w)))
                    elif w.content.endswith("\\"):
                        violations.append(self._mk_digest(
                            DiffRejectSubtype.HOLE_ESCAPE,
                            "hole 内に行末 backslash を検出 (物理行 splice を fail-closed で拒否)",
                            f"anchor src 行 {w.anchor}",
                            self._content_evidence(_BRANCH_LINE_SPLICE, w)))

        if not violations:
            return DiffQuarantineResult(passed=True)

        # primary = 最も構造的な違反を先頭に (malformed > outside > frame > hole-escape)。
        order = {DiffRejectSubtype.MALFORMED.value: 0,
                 DiffRejectSubtype.OUTSIDE_REGION.value: 1,
                 DiffRejectSubtype.FRAME_ALTERED.value: 2,
                 DiffRejectSubtype.HOLE_ESCAPE.value: 3}
        violations.sort(key=lambda v: order.get(v["subtype"], 9))
        primary = violations[0]
        return DiffQuarantineResult(
            passed=False,
            subtype=DiffRejectSubtype(primary["subtype"]),
            reason=primary["reason"],
            digest=primary,
            violations=violations)


def _strip_ab_prefix(p: str) -> str:
    """diff パスの単一 `a/`・`b/` prefix だけを剥がす (それ以外の先頭文字は保持)。"""
    p = p.strip()
    if p.startswith(('a/', 'b/')):
        p = p[2:]
    return p


def _same_file(a: str, b: str) -> bool:
    """diff の b-path と marker.source_rel を正規化して**厳密一致**で比較。

    旧実装は `lstrip('./')` + `endswith` で `../../etc/include/backoff.hh` や repo-root の
    `backoff.hh` を target と誤認した (敵対 red-team 2026-07-07 multifile)。単一 `a/`・`b/`
    prefix だけ剥がし、posixpath.normpath 後の完全一致のみ許可。絶対パス・`..` 脱出は
    編集面外として即 False (path traversal 拒否)。"""
    import posixpath
    na = posixpath.normpath(_strip_ab_prefix(a))
    nb = posixpath.normpath(_strip_ab_prefix(b))
    for p in (na, nb):
        if not p or p.startswith('/') or p == '..' or p.startswith('../'):
            return False
    return na == nb


def parse_template_file(template_path: str, marker_id: str) -> Optional[TemplateMarker]:
    """テンプレファイルから EVOLVE-BLOCK マーカー定義を抽出する (1-indexed)。

    期待構造 (BEGIN と END の間にちょうど #if/#else/#endif の三枝が 1 組)::

        // EVOLVE-BLOCK-BEGIN <marker_id>
        ... (コメント等)
        #if <predicate>
        ...            <- hole (合成枝)
        #else
        ...            <- stock 枝
        #endif
        // EVOLVE-BLOCK-END <marker_id>

    構造が満たされなければ None (テンプレ異常 = 呼び出し側で fails-closed に倒す)。
    """
    try:
        with open(template_path, encoding="utf-8") as f:
            raw = f.read()
    except OSError:
        return None
    lines = raw.split('\n')

    begin_re = re.compile(r'EVOLVE-BLOCK-BEGIN\s+' + re.escape(marker_id) + r'\b')
    end_re = re.compile(r'EVOLVE-BLOCK-END\s+' + re.escape(marker_id) + r'\b')
    if_re = re.compile(r'^\s*#\s*if(?:def|ndef)?\b')
    else_re = re.compile(r'^\s*#\s*else\b')
    endif_re = re.compile(r'^\s*#\s*endif\b')

    begin_line = if_line = else_line = endif_line = end_line = 0
    frame_text: Dict[int, str] = {}

    # 1-indexed で走査。BEGIN を見つけてから順に三枝 → END を拾う。
    for idx, ln in enumerate(lines, start=1):
        if begin_line == 0:
            if begin_re.search(ln):
                begin_line = idx
                frame_text[idx] = ln
            continue
        # BEGIN 以降。
        if if_line == 0:
            if if_re.match(ln):
                if_line = idx
                frame_text[idx] = ln
            elif end_re.search(ln):
                return None                  # #if 前に END = 構造異常
            else:
                frame_text[idx] = ln         # BEGIN..#if 間のコメント (フレーム)
            continue
        if else_line == 0:
            if else_re.match(ln):
                else_line = idx
                frame_text[idx] = ln
            continue
        if endif_line == 0:
            if endif_re.match(ln):
                endif_line = idx
                frame_text[idx] = ln
            else:
                frame_text[idx] = ln         # stock 枝 (フレーム = 不可触)
            continue
        # #endif 以降 — END を探す。
        if end_re.search(ln):
            end_line = idx
            frame_text[idx] = ln
            break
        frame_text[idx] = ln                 # #endif..END 間 (フレーム)

    if not (begin_line and if_line and else_line and endif_line and end_line):
        return None
    if not (begin_line < if_line < else_line < endif_line < end_line):
        return None

    # hole (合成枝) 行はフレームでない → frame_text から除外。
    hole_text = {hl: lines[hl - 1] for hl in range(if_line + 1, else_line)}
    for hl in range(if_line + 1, else_line):
        frame_text.pop(hl, None)

    # source_rel = EVOLVE_BLOCK_SOURCES 由来の相対名を basename ベースで推定。
    # 呼び出し側 (orchestrator) は正確な rel を後から差し替え可能。
    import os
    source_rel = os.path.basename(template_path)

    return TemplateMarker(
        marker_id=marker_id,
        source_rel=source_rel,
        begin_line=begin_line,
        if_line=if_line,
        else_line=else_line,
        endif_line=endif_line,
        end_line=end_line,
        frame_text=frame_text,
        hole_text=hole_text,
    )


if __name__ == "__main__":
    print("diff_quarantine module loaded (後続段 4 4a)")
