#!/usr/bin/env python3
"""Workflow スクリプトの agent() model 省略 lint — 2026-07-19 のモデル経済監査で導入。

背景: Workflow tool の script 内 ``agent()`` は opts.model を省略すると親モデル
(このプロジェクトでは通例 fable) を暗黙継承し、fan-out がまとめて最上位モデルで走る。
guard_agent hook (hooks/README.md hook 4) は Agent tool しか見えず、script 内 spawn は
既知の盲点。hook での script lint は「brittle で偽陽性の害が大きい」として 2026-07-18 に
棄却済みのため、**hook 化はせず**、workflow 起動前の自己検査・過去 script の事後監査用の
standalone lint として置く (拒否はしない)。「毎回 opts.model を明示する」規律の正本は
memory (subagent-model-economy) 側。

使い方:
  python3 tools/check_workflow_models.py <script.js> [...]   # NG あり = exit 1
  python3 tools/check_workflow_models.py --dir <path>        # 配下の *.js を再帰走査

判定:
- ``agent(prompt)`` の第 2 引数が無い、または object literal に ``model`` / ``agentType``
  のどちらの key も無い → **NG** (違反)
- 第 2 引数が object literal でない (変数・関数呼び等)、または spread (``...``) /
  computed key (``[expr]:``) を含み静的に判定できない → **WARN** (exit code に影響
  しない — 偽陽性の害を避ける fail-open)
- ``agentType`` は .claude/agents/ named role の model/effort 両ピンで解決される前提で
  許可 (全 project role の両ピンは test_hooks.py の悉皆 gate が強制)
- ``model`` 明示済みでも ``effort`` 省略は **WARN** — 子はセッション effort を継承する
  ため、xhigh/ultracode 親では fan-out が全て xhigh 側に倒れる (codex 監査 2026-07-19)

既知の限界 (正直に): 文字列走査であり JS は実行しない。動的に組んだ opts・eval 相当・
workflow() 子スクリプトの中身は見えない。regex literal の判定は前置トークン
ヒューリスティックで、正規構文外の JS では誤判定し得る (迷う側は WARN に倒す)。
制御文の閉じ括弧直後の statement 位置 regex (``if (x) /re/.test(s)``) は誤 NG になり得る。
getter/setter や unicode escape の property key は認識しない (codex 監査 2026-07-19 指摘。
いずれも現実の workflow script では想定外の構文のため、修正せず限界として記録)。
"""
from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass
from pathlib import Path

# regex literal 開始と解釈する直前トークン末尾 (除算との曖昧性の標準ヒューリスティック)。
# 直前の非空白文字がこの集合、または行頭/return 等のキーワード末尾なら `/` を regex とみなす。
_REGEX_PREFIX_CHARS = set("([{,;:=!&|?+-*%^~<>")
_REGEX_PREFIX_KEYWORDS = ("return", "typeof", "case", "in", "of", "new", "delete", "void", "do", "else")


@dataclass
class Finding:
    line: int
    kind: str  # "ng" | "warn"
    message: str


def _mask_non_code(text: str) -> str:
    """コメント・文字列・regex literal の中身を空白化し、code 構造だけを残す。

    テンプレート literal の ``${ ... }`` 内は code として保存する (brace 深度で
    テンプレートへの復帰を判定)。マスク後のテキストでは括弧類が code のものだけに
    なるため、呼び出しの括弧対応・引数分割が単純な深度走査で安全にできる。
    """
    out = list(text)
    n = len(text)
    i = 0
    # スタック要素: ("code", brace_depth) | ("template",)
    stack: list[tuple] = [("code", 0)]

    def blank(j: int) -> None:
        if text[j] != "\n":
            out[j] = " "

    def prev_code_token_is_regex_prefix(j: int) -> bool:
        k = j - 1
        while k >= 0 and out[k] in " \t\n":
            k -= 1
        if k < 0:
            return True
        if out[k] in _REGEX_PREFIX_CHARS:
            # postfix ++/-- は値の終端 (除算の左辺になり得る) — regex 前置ではない
            if out[k] in "+-" and k >= 1 and out[k - 1] == out[k]:
                return False
            return True
        # 直前が識別子ならキーワードかどうかを見る
        m = re.search(r"[A-Za-z_$][\w$]*\Z", "".join(out[max(0, k - 10): k + 1]))
        if not (m and m.group(0) in _REGEX_PREFIX_KEYWORDS):
            return False
        # プロパティアクセス (obj.in) / private field (this.#in) はキーワードでなく名前
        p = k - len(m.group(0))
        while p >= 0 and out[p] in " \t\n":
            p -= 1
        return not (p >= 0 and out[p] in ".#")

    while i < n:
        state = stack[-1]
        c = text[i]
        if state[0] == "template":
            if c == "\\" and i + 1 < n:
                blank(i); blank(i + 1); i += 2
                continue
            if c == "`":
                # 終端は値トークン終端マーカー "0" — 直後の / を除算と正しく判定させる
                out[i] = "0"
                i += 1
                stack.pop()
                continue
            if c == "$" and i + 1 < n and text[i + 1] == "{":
                # `{` は残す — ${} 内の深度 0 カンマが呼び出しの引数区切りに見えないように
                blank(i); i += 2
                stack.append(("code", 0))
                continue
            blank(i); i += 1
            continue
        # code 状態
        depth = state[1]
        if c in "'\"":
            q = c
            blank(i); i += 1
            while i < n and text[i] != q and text[i] != "\n":
                if text[i] == "\\" and i + 1 < n:
                    blank(i); blank(i + 1); i += 2
                    continue
                blank(i); i += 1
            if i < n and text[i] == q:
                # 終端は "0" マーカー — "12" / 3 の / を regex と誤認しない
                out[i] = "0"
                i += 1
            continue
        if c == "`":
            blank(i); i += 1
            stack.append(("template",))
            continue
        if c == "/" and i + 1 < n and text[i + 1] == "/":
            while i < n and text[i] != "\n":
                blank(i); i += 1
            continue
        if c == "/" and i + 1 < n and text[i + 1] == "*":
            blank(i); blank(i + 1); i += 2
            while i + 1 < n and not (text[i] == "*" and text[i + 1] == "/"):
                blank(i); i += 1
            if i + 1 < n:
                blank(i); blank(i + 1); i += 2
            else:
                i = n
            continue
        if c == "/" and prev_code_token_is_regex_prefix(i):
            # regex literal: 文字クラス内の / はエスケープ不要
            blank(i); i += 1
            in_class = False
            while i < n and text[i] != "\n":
                if text[i] == "\\" and i + 1 < n:
                    blank(i); blank(i + 1); i += 2
                    continue
                if text[i] == "[":
                    in_class = True
                elif text[i] == "]":
                    in_class = False
                elif text[i] == "/" and not in_class:
                    out[i] = "0"    # regex literal も値 — 終端マーカー
                    i += 1
                    break
                blank(i); i += 1
            continue
        if c == "{":
            stack[-1] = ("code", depth + 1)
            i += 1
            continue
        if c == "}":
            if depth == 0 and len(stack) > 1:
                i += 1       # `}` は残す (${} 開き側と対で括弧バランスを保つ)
                stack.pop()  # ${ } を閉じてテンプレートへ復帰
                continue
            stack[-1] = ("code", max(0, depth - 1))
            i += 1
            continue
        i += 1
    return "".join(out)


def _match_paren(masked: str, open_idx: int) -> int:
    """masked[open_idx] == '(' の対応する ')' の index。見つからなければ -1。"""
    depth = 0
    for j in range(open_idx, len(masked)):
        if masked[j] in "([{":
            depth += 1
        elif masked[j] in ")]}":
            depth -= 1
            if depth == 0:
                return j
    return -1


def _split_top_level_ranges(span: str) -> list[tuple[int, int]]:
    """深度 0 のカンマで区切った各引数の (start, end) を返す。"""
    ranges: list[tuple[int, int]] = []
    depth = 0
    start = 0
    for j, c in enumerate(span):
        if c in "([{":
            depth += 1
        elif c in ")]}":
            depth -= 1
        elif c == "," and depth == 0:
            ranges.append((start, j))
            start = j + 1
    ranges.append((start, len(span)))
    return ranges


def _object_keys(masked_span: str, orig_span: str) -> tuple[set[str], bool]:
    """object literal の深度 1 の key 集合と、静的判定不能要素の有無を返す。

    構造 (深度・区切り) はマスク側で判定し、quoted key の文字列はマスクで
    消えるため原文側から取る (両者は 1:1 の位置対応)。第 2 返り値は
    spread (``...``) または computed key (``[expr]:``) の有無 — どちらも実行時に
    model を指定し得るため、呼び出し側は NG でなく WARN に倒す (fail-open)。
    """
    keys: set[str] = set()
    has_uncertain = False
    depth = 0
    expecting_key = False
    j = 0
    n = len(masked_span)
    while j < n:
        c = masked_span[j]
        if c in "([{":
            if c == "[" and depth == 1 and expecting_key:
                # computed key — 静的判定不能
                has_uncertain = True
                expecting_key = False
            depth += 1
            if c == "{" and depth == 1:
                expecting_key = True
            j += 1
            continue
        if c in ")]}":
            depth -= 1
            j += 1
            continue
        if depth == 1:
            if c == ",":
                expecting_key = True
                j += 1
                continue
            if expecting_key and not orig_span[j].isspace():
                if masked_span.startswith("...", j):
                    has_uncertain = True
                    expecting_key = False
                    j += 3
                    continue
                oc = orig_span[j]
                if oc in "'\"":
                    # quoted key: 名前は原文から読む
                    k = j + 1
                    name_chars: list[str] = []
                    while k < n and orig_span[k] != oc:
                        if orig_span[k] == "\\" and k + 1 < n:
                            k += 1
                            name_chars.append(orig_span[k])
                        else:
                            name_chars.append(orig_span[k])
                        k += 1
                    t = k + 1
                    while t < n and masked_span[t].isspace():
                        t += 1
                    if t < n and masked_span[t] == ":":
                        keys.add("".join(name_chars))
                    expecting_key = False
                    j = k + 1
                    continue
                m = re.match(r"[A-Za-z_$][\w$]*", masked_span[j:])
                if m:
                    # `model:` 形式に加え shorthand (`{model}`) も「指定あり」とみなす
                    keys.add(m.group(0))
                    expecting_key = False
                    j += m.end()
                    continue
                expecting_key = False
        j += 1
    return keys, has_uncertain


def _trim_aligned(masked_span: str, orig_span: str) -> tuple[str, str]:
    """マスク側の空白を基準に両者を同じ範囲へ刈り込む (1:1 の位置対応を保つ)。"""
    lead = len(masked_span) - len(masked_span.lstrip())
    end = len(masked_span.rstrip())
    return masked_span[lead:end], orig_span[lead:end]


def scan_script(text: str) -> list[Finding]:
    masked = _mask_non_code(text)
    findings: list[Finding] = []
    for m in re.finditer(r"(?<![A-Za-z0-9_$.#])agent\s*(?:\?\.\s*)?\(", masked):
        open_idx = masked.index("(", m.start())
        line = text.count("\n", 0, m.start()) + 1
        close_idx = _match_paren(masked, open_idx)
        if close_idx < 0:
            findings.append(Finding(line, "warn", "agent() の括弧対応を追えない (走査不能 — 手で確認する)"))
            continue
        after = close_idx + 1
        while after < len(masked) and masked[after].isspace():
            after += 1
        if after < len(masked) and masked[after] == "{":
            continue  # function agent(...) { / method 定義 — 呼び出しではない
        span_start = open_idx + 1
        ranges = _split_top_level_ranges(masked[span_start:close_idx])
        if len(ranges) < 2 or not masked[span_start + ranges[1][0]: span_start + ranges[1][1]].strip():
            findings.append(Finding(line, "ng", "agent() に opts が無い (model 省略 = 親モデル暗黙継承)"))
            continue
        abs_s, abs_e = span_start + ranges[1][0], span_start + ranges[1][1]
        opts_masked, opts_orig = _trim_aligned(masked[abs_s:abs_e], text[abs_s:abs_e])
        # 括弧で包んだ object literal (({...})) は剥がしてから判定する
        while (opts_masked.startswith("(")
               and _match_paren(opts_masked, 0) == len(opts_masked) - 1):
            opts_masked, opts_orig = _trim_aligned(opts_masked[1:-1], opts_orig[1:-1])
        if not opts_masked.startswith("{"):
            findings.append(Finding(line, "warn", f"opts が object literal でない ({opts_orig[:30]!r}) — 静的判定不能"))
            continue
        keys, has_uncertain = _object_keys(opts_masked, opts_orig)
        if "agentType" in keys:
            continue  # named role は frontmatter が model/effort を両ピン (悉皆 gate)
        if "model" in keys:
            if "effort" not in keys and not has_uncertain:
                findings.append(Finding(line, "warn", "model はあるが effort 省略 (セッション effort を継承 — xhigh 親では過剰側に倒れる)"))
            continue
        if has_uncertain:
            findings.append(Finding(line, "warn", "opts に spread / computed key があり model の有無を静的判定できない"))
            continue
        findings.append(Finding(line, "ng", f"agent() の opts に model / agentType が無い (keys={sorted(keys)})"))
    return findings


def check_paths(paths: list[Path]) -> int:
    ng = 0
    warn = 0
    for path in paths:
        try:
            text = path.read_text(encoding="utf-8")
        except OSError as exc:
            print(f"WARN: {path}: 読めない ({exc})", file=sys.stderr)
            warn += 1
            continue
        for f in scan_script(text):
            tag = "NG" if f.kind == "ng" else "WARN"
            print(f"{tag}: {path}:{f.line}: {f.message}")
            if f.kind == "ng":
                ng += 1
            else:
                warn += 1
    print(f"agent() model lint: NG={ng} WARN={warn} (files={len(paths)})")
    return 1 if ng else 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("scripts", nargs="*", type=Path, help="workflow script (.js)")
    parser.add_argument("--dir", type=Path, help="配下の *.js を再帰走査するディレクトリ")
    args = parser.parse_args(argv)
    paths = list(args.scripts)
    if args.dir:
        paths.extend(sorted(args.dir.rglob("*.js")))
    if not paths:
        parser.error("script か --dir のどちらかを指定する")
    return check_paths(paths)


if __name__ == "__main__":
    raise SystemExit(main())
