#!/usr/bin/env python3
"""s6_canary_rename — D52 §3 独立再命名 canary の匿名化 + preprocess 同値の機械検証。

trigger-gating 骨格 patch (patches/silo-backoff-trigger-gating-variant.patch) から
識別子 rename + コメント除去 + 説明テキスト空化のみを施した匿名化 patch を生成し、
その 3 操作以外にコード構造を変えていないことを preprocess 同値 (cpp -fpreprocessed -P)
で機械検証する。正本 = docs/phase3-main-experiment.md 2026-07-12 追記 (D52) §3 /
output/insights/2026-07-12_s6-headline-system-level-reframe-draft.md §3。

匿名化の機械規則 (恣意的なコメント選別を排除するための構文位置ベース定義):
  1. rename map (骨格が導入した識別子・マーカー ID のみ。stock 由来識別子は対象外 —
     骨格構造からの再導出をさせるのが canary の設計)
  2. 追加行 (+) のコメント全除去 — C++ は文字列リテラル外の // 以降、CMake は行頭 # 行。
     EVOLVE-BLOCK マーカー行もコメント構文なので機械的に落ちる (「このコメントは特別」
     という人為選別を持ち込まない)。コメントのみの追加行は行ごと削除し hunk 長を再計算
  3. 人間向け説明テキストの構文位置の空化 — CMake set() の CACHE STRING docstring と
     #error のメッセージ文字列 (どちらもコード意味論に影響しない説明スロット)

検証 (verify): pinned stock に元 patch / 匿名化 patch を各々適用し、匿名側に逆 rename を
当てたうえで両者を正規化 (説明スロット空化 → cpp -fpreprocessed -P = コメント除去・
ディレクティブ非処理) して byte 一致を要求する。CMake は # コメント行除去 + docstring
空化で同様に比較。不一致は fails-closed (exit 1)。
"""

import argparse
import hashlib
import json
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
SUBMODULE = REPO_ROOT / "external" / "ccbench"
SOURCE_PATCH = REPO_ROOT / "patches" / "silo-backoff-trigger-gating-variant.patch"
PATCHED_FILES = ["cmake/Options.cmake", "cc/silo/transaction.cc"]

# 順序付き rename map。部分文字列包含 (CCBENCH_ 付き→なし) があるため長い方を先に置換する。
# 逆適用は逆順。骨格が導入したトークンのみ — stock 由来識別子 (lockWriteSet /
# validationPhase / Backoff::backoff / TransactionStatus 等) は匿名化しない。
RENAME_MAP = [
    ("CCBENCH_BACKOFF_TRIGGER_GATING", "CCBENCH_FEATURE_X"),
    ("BACKOFF_TRIGGER_GATING", "FEATURE_X"),
    ("IzanagiAbortReason", "EnumX"),
    ("izanagi_abort_reason_", "g_state_x_"),
    ("izanagi_gate_pass", "flag_x"),
    ("kUnset", "kX0"),
    ("kLockConflict", "kX1"),
    ("kUpdateAbsent", "kX2"),
    ("kReadValiTid", "kX3"),
    ("kReadValiLocked", "kX4"),
    ("kNodeVali", "kX5"),
    ("kInsertNode", "kX6"),
    ("kScanNode", "kX7"),
    ("silo-backoff-trigger-gating", "region-x"),
]


def apply_rename(text: str, reverse: bool = False) -> str:
    pairs = [(dst, src) for src, dst in reversed(RENAME_MAP)] if reverse else RENAME_MAP
    for src, dst in pairs:
        text = text.replace(src, dst)
    return text


def strip_cxx_comment(line: str) -> str:
    """文字列リテラル外の // 以降を除去。ブロックコメントは対象 patch に無い前提で fail。"""
    out = []
    in_str = False
    i = 0
    while i < len(line):
        c = line[i]
        if in_str:
            if c == "\\":
                out.append(line[i : i + 2])
                i += 2
                continue
            if c == '"':
                in_str = False
            out.append(c)
        else:
            if c == '"':
                in_str = True
                out.append(c)
            elif c == "/" and i + 1 < len(line) and line[i + 1] == "/":
                break
            elif c == "/" and i + 1 < len(line) and line[i + 1] == "*":
                raise SystemExit(f"block comment unsupported (add handling): {line!r}")
            else:
                out.append(c)
        i += 1
    return "".join(out).rstrip()


def blank_doc_slots(line: str) -> str:
    """人間向け説明テキストの構文位置 (CACHE STRING docstring / #error メッセージ) を空化。"""
    line = re.sub(r'(CACHE\s+STRING\s+)"[^"]*"', r'\1""', line)
    if re.match(r"\s*#\s*error\b", line):
        line = re.sub(r'"(?:[^"\\]|\\.)*"', '""', line)
    return line


def anonymize_added_line(text: str, target: str) -> "str | None":
    """+ 行 1 本の匿名化。None = 行ごと削除 (コメントのみ行)。"""
    text = apply_rename(text)
    if target.endswith(".cmake"):
        if re.match(r"\s*#", text):
            return None
        if "#" in text:
            raise SystemExit(f"mid-line cmake comment unsupported: {text!r}")
        return blank_doc_slots(text).rstrip()
    stripped = strip_cxx_comment(text)
    if stripped.strip() == "":
        return None
    return blank_doc_slots(stripped)


HUNK_RE = re.compile(r"^@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@(.*)$")


def anonymize_patch(patch_text: str) -> str:
    """unified diff の + 行のみを匿名化し、hunk ヘッダの新側行数を再計算する。
    コンテキスト行・- 行・diff メタ行は変更しない (assert で担保)。"""
    out_lines = []
    lines = patch_text.splitlines()
    i = 0
    target = None
    delta = 0  # 当該ファイル内の (new_start - old_start) 累積。行削除でずれるため再計算する
    while i < len(lines):
        line = lines[i]
        m = HUNK_RE.match(line)
        if line.startswith("+++ "):
            target = line[4:].strip()
            delta = 0
            out_lines.append(line)
            i += 1
            continue
        if not m:
            out_lines.append(line)
            i += 1
            continue
        # hunk 本体を収集
        old_start, old_len = int(m.group(1)), int(m.group(2) or "1")
        new_len = int(m.group(4) or "1")
        i += 1
        body = []
        remaining_old, remaining_new = old_len, new_len
        while i < len(lines) and (remaining_old > 0 or remaining_new > 0):
            b = lines[i]
            tag = b[:1]
            if tag == " " or b == "":
                remaining_old -= 1
                remaining_new -= 1
            elif tag == "-":
                remaining_old -= 1
            elif tag == "+":
                remaining_new -= 1
            elif tag == "\\":  # "\ No newline at end of file"
                pass
            else:
                raise SystemExit(f"unexpected patch line: {b!r}")
            body.append(b)
            i += 1
        new_body = []
        new_count = 0
        for b in body:
            if b.startswith("+"):
                anon = anonymize_added_line(b[1:], target or "")
                if anon is None:
                    continue
                new_body.append("+" + anon)
                new_count += 1
            else:
                if b.startswith(" ") or b == "" or b.startswith("\\"):
                    if b.startswith(" ") or b == "":
                        new_count += 1
                new_body.append(b)
        out_lines.append(f"@@ -{old_start},{old_len} +{old_start + delta},{new_count} @@")
        out_lines.extend(new_body)
        delta += new_count - old_len
    return "\n".join(out_lines) + "\n"


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def export_stock(dst: Path) -> str:
    """pinned HEAD の対象 2 ファイルを dst に展開し、pin hash を返す。"""
    pin = subprocess.run(
        ["git", "-C", str(SUBMODULE), "rev-parse", "HEAD"],
        check=True, capture_output=True, text=True,
    ).stdout.strip()
    tar = subprocess.run(
        ["git", "-C", str(SUBMODULE), "archive", "HEAD", *PATCHED_FILES],
        check=True, capture_output=True,
    ).stdout
    subprocess.run(["tar", "-x", "-C", str(dst)], input=tar, check=True)
    return pin


def git_apply(tree: Path, patch_file: Path) -> None:
    subprocess.run(
        ["git", "apply", "--whitespace=nowarn", str(patch_file)],
        cwd=tree, check=True, capture_output=True, text=True,
    )


def normalize_cxx(path: Path, workdir: Path) -> bytes:
    """説明スロット空化 → cpp -fpreprocessed -P (コメント除去・ディレクティブ非処理)。"""
    blanked = workdir / (path.name + ".blanked")
    blanked.write_text(
        "\n".join(blank_doc_slots(l) for l in path.read_text().splitlines()) + "\n"
    )
    r = subprocess.run(
        ["cpp", "-fpreprocessed", "-P", "-x", "c++", str(blanked)],
        check=True, capture_output=True,
    )
    return r.stdout


def normalize_cmake(path: Path) -> bytes:
    lines = []
    for l in path.read_text().splitlines():
        if re.match(r"\s*#", l):
            continue
        lines.append(blank_doc_slots(l).rstrip())
    return ("\n".join(lines) + "\n").encode()


def verify(anon_patch_file: Path) -> dict:
    """preprocess 同値の機械検証。戻り値 = provenance 断片。不一致は SystemExit。"""
    with tempfile.TemporaryDirectory(prefix="s6canary.") as td:
        tmp = Path(td)
        results = {}
        trees = {}
        for name, patch_file in (("orig", SOURCE_PATCH), ("anon", anon_patch_file)):
            tree = tmp / name
            tree.mkdir()
            pin = export_stock(tree)
            git_apply(tree, patch_file)
            trees[name] = tree
            results["submodule_pin"] = pin
        # 匿名側に逆 rename を適用 (テキストレベル)
        for rel in PATCHED_FILES:
            f = trees["anon"] / rel
            f.write_text(apply_rename(f.read_text(), reverse=True))
        for rel in PATCHED_FILES:
            a, b = trees["orig"] / rel, trees["anon"] / rel
            if rel.endswith(".cmake"):
                na, nb = normalize_cmake(a), normalize_cmake(b)
            else:
                na, nb = normalize_cxx(a, tmp), normalize_cxx(b, tmp)
            ok = na == nb
            results[rel] = {
                "equivalent": ok,
                "normalized_sha256_orig": sha256(na),
                "normalized_sha256_anon_unrenamed": sha256(nb),
            }
            if not ok:
                da = tmp / "norm_orig.txt"
                db = tmp / "norm_anon.txt"
                da.write_bytes(na)
                db.write_bytes(nb)
                diff = subprocess.run(
                    ["diff", "-u", str(da), str(db)], capture_output=True, text=True
                ).stdout
                print(diff[:4000], file=sys.stderr)
                raise SystemExit(f"FAIL: preprocess equivalence broken for {rel}")
        return results


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out", required=True, help="匿名化 patch の出力先")
    ap.add_argument("--provenance", required=True, help="provenance JSON の出力先")
    args = ap.parse_args()

    src_text = SOURCE_PATCH.read_text()
    anon_text = anonymize_patch(src_text)
    # 匿名化 patch に骨格導入トークンが残っていないことの直接 grep (belt-and-braces)
    for token, _ in RENAME_MAP:
        if token in anon_text:
            raise SystemExit(f"FAIL: token {token!r} leaked into anonymized patch")
    if re.search(r"izanagi", anon_text, re.IGNORECASE):
        raise SystemExit("FAIL: 'izanagi' leaked into anonymized patch")

    out = Path(args.out)
    out.write_text(anon_text)
    ver = verify(out)

    prov = {
        "what": "D52 §3 独立再命名 canary — 匿名化 patch の生成と preprocess 同値検証",
        "source_patch": str(SOURCE_PATCH.relative_to(REPO_ROOT)),
        "source_patch_sha256": sha256(src_text.encode()),
        "anonymized_patch": str(out),
        "anonymized_patch_sha256": sha256(anon_text.encode()),
        "rename_map": {src: dst for src, dst in RENAME_MAP},
        "comment_rule": "追加行の全コメント除去 (EVOLVE-BLOCK マーカー行含む・人為選別なし) + CACHE STRING docstring / #error メッセージの空化",
        "verification": ver,
        "verdict": "PASS",
    }
    Path(args.provenance).write_text(
        json.dumps(prov, ensure_ascii=False, indent=2) + "\n"
    )
    print(f"PASS: anonymized patch = {out}, provenance = {args.provenance}")


if __name__ == "__main__":
    main()
