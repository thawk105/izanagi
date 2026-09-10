#!/usr/bin/env python3
"""資料のbytesを保存する一回限りの日付別移行。

計算ノードで計画JSONを確認後、そのファイルを --apply に渡す。
移動前に全計画を再検査する。同時書込みは禁止。
--output で新規JSONファイルへ保存すると、標準出力は件数のみになる。
"""
from __future__ import annotations

import argparse
import errno
import gzip
import hashlib
import json
import os
from pathlib import Path
import re
import stat
import subprocess
from urllib.parse import unquote, urlsplit, quote

BASE = "c68d08d9e452138c383e9b92076bf91451912700"
PREFIX = "output/insights/"
GUIDE = PREFIX + "layout-index"
DATED = re.compile(r"^(\d{4}-\d{2}-\d{2})_(.+)$")
CODE = {".py", ".sh", ".bash", ".cpp", ".cc", ".c", ".h", ".hh", ".hpp", ".patch", ".diff", ".so"}
# A conservative extra pin for the evidence tree whose raw leaves are indexed.
RAW_TOP = "2026-08-03_t361-t362-cluster-probes"
# Parent ruling for this one-time BASE migration: these two copytree call logs
# describe historical observations, not current path pins. Inventory and
# bytes/mode verification still cover them; retain their original directory.
HISTORICAL_COPYTREE_LOGS = frozenset({
    PREFIX + "2026-09-04_t2298-t2273-shard0-critical-path/measure/phase-20260904-223623-rep1.jsonl",
    PREFIX + "2026-09-04_t2298-t2273-shard0-critical-path/measure/phase-20260904-223914-rep2.jsonl",
})


def git(root: Path, *args: str) -> bytes:
    return subprocess.check_output(["git", *args], cwd=root)


def inventory(root: Path, base: str) -> dict:
    result = {}
    for entry in git(root, "ls-tree", "-rz", base, "--", PREFIX).split(b"\0"):
        if entry:
            header, path = entry.split(b"\t", 1)
            mode, kind, oid = header.decode().split()
            if kind != "blob" or mode not in {"100644", "100755"}:
                raise ValueError(f"non-regular Git entry: {path!r}")
            result[path.decode()] = {"mode": mode, "blob": oid}
    if not result:
        raise ValueError("empty baseline inventory")
    return result


def regular(root: Path, rel: str) -> os.stat_result:
    p = root
    for component in Path(rel).parts:
        p = p / component
        if p.is_symlink():
            raise ValueError(f"symlink: {p}")
    st = p.stat()
    if not stat.S_ISREG(st.st_mode):
        raise ValueError(f"non-regular file: {rel}")
    return st


def verify(root: Path, files: dict, moves: dict) -> None:
    for old, expected in files.items():
        rel = relocated(old, moves)
        st = regular(root, rel)
        digest = hashlib.sha1()
        digest.update(f"blob {st.st_size}\0".encode())
        with (root / rel).open("rb") as stream:
            for block in iter(lambda: stream.read(1024 * 1024), b""):
                digest.update(block)
        mode = "100755" if st.st_mode & 0o111 else "100644"
        if digest.hexdigest() != expected["blob"] or mode != expected["mode"]:
            raise ValueError(f"baseline bytes/mode changed: {old}")


def relocated(path: str, moves: dict) -> str:
    if path.startswith(PREFIX):
        top, sep, tail = path[len(PREFIX):].partition("/")
        if top in moves:
            return PREFIX + moves[top] + (sep + tail if sep else "")
    return path


def local_target(source: str, target: str, root: Path | None = None) -> str | None:
    target = unquote(target.strip("<>"))
    if "\0" in target:
        return None
    try:
        scheme = urlsplit(target).scheme
    except ValueError:
        # Malformed URL syntax is not a filesystem/read failure.
        return None
    if scheme or target.startswith(("//", "#")):
        return None
    target = target.split("#", 1)[0].split("?", 1)[0]
    if not target:
        return None
    if target.startswith("/"):
        if root is not None:
            try:
                return str(Path(target).relative_to(root))
            except ValueError:
                # Repository-root Markdown destinations also stay at the old
                # address when their source moves.
                if target.startswith("/output/"):
                    return os.path.normpath(target.lstrip("/"))
        return None
    return os.path.normpath(str(Path(source).parent / target))


def link_targets(text: str):
    # Inline links/images, definitions and HTML attributes. Include nested
    # parentheses in bare destinations (common in archived research filenames).
    # An unclosed angle destination must not fall back to a bare destination
    # or consume later prose/formulas across a line ending.
    angle = r'<[^<>\r\n]*>'
    bare = r'(?:[^\s()<>]|\([^()<>\r\n]*\))+'
    pattern = (rf'\]\(\s*({angle}|{bare})'
               rf'|^\s*\[[^\]\r\n]+\]:\s*({angle}|[^\s<>]+)'
               r'|(?:href|src)\s*=\s*["\x27]([^"\x27]+)')
    for match in re.finditer(pattern, text, re.MULTILINE | re.IGNORECASE):
        yield next(value for value in match.groups() if value is not None)


class PinNames:
    """Index actual aliases by their first Unicode word/hyphen run."""

    token = re.compile(r"[\w-]+")

    def __init__(self, aliases):
        self.by_token = {}
        special = []
        for name in sorted(aliases, key=len, reverse=True):
            first = self.token.match(name)
            if first:
                self.by_token.setdefault(first.group(), []).append(name)
            else:
                special.append(name)
        # Only punctuation-leading names need regex search. Lookahead keeps
        # overlapping starts until the common and special hits are merged.
        self.special = (re.compile(r"(?<![\w-])(?=(" +
                        "|".join(map(re.escape, special)) + r")(?![\w-]))")
                        if special else None)

    def find(self, text: str):
        hits = []
        for token in self.token.finditer(text):
            start = token.start()
            for name in self.by_token.get(token.group(), ()):
                end = start + len(name)
                if (text.startswith(name, start)
                        and not self.token.match(text, end)):
                    hits.append((start, end, name))
                    break  # Same-start alternatives prefer the longest name.
        if self.special:
            hits.extend((m.start(), m.end(1), m.group(1))
                        for m in self.special.finditer(text))
        consumed = 0
        for start, end, name in sorted(hits, key=lambda hit: (hit[0], -hit[1])):
            if start >= consumed:
                yield name
                consumed = end


def build_plan(root: Path, base: str = BASE) -> dict:
    files = inventory(root, base)
    verify(root, files, {})
    # Restrict only the old evidence inventory, not unrelated HEAD changes.
    actual = set()
    old_dirs = {str(parent) for rel in files for parent in Path(rel).parents
                if str(parent).startswith(PREFIX)}
    def walk_error(exc):
        raise exc

    for directory, dirs, names in os.walk(root / PREFIX, followlinks=False, onerror=walk_error):
        for name in dirs + names:
            path = Path(directory) / name
            if path.is_symlink():
                raise ValueError(f"symlink in insights: {path}")
            rel = str(path.relative_to(root))
            top = rel[len(PREFIX):].split("/")[0]
            if path.is_dir() and PREFIX + top in old_dirs and rel not in old_dirs:
                raise ValueError(f"untracked directory in old material: {rel}")
        actual.update(str((Path(directory) / name).relative_to(root)) for name in names)
    if actual != set(files):
        raise ValueError(f"insights inventory drift: extra={sorted(actual - files.keys())[:10]}, missing={sorted(files.keys() - actual)[:10]}")
    tops = sorted({p[len(PREFIX):].split("/")[0] for p in files})
    holds = {top: set() for top in tops}
    moves = {}
    for top in tops:
        match = DATED.fullmatch(top)
        if not match or not (root / PREFIX / top).is_dir():
            holds[top].add("legacy standalone or undated entry")
        else:
            moves[top] = "/".join(match.groups())
    for path, entry in files.items():
        top = path[len(PREFIX):].split("/")[0]
        if Path(path).suffix in CODE or entry["mode"] == "100755":
            holds[top].add("execution material: " + path)
    if RAW_TOP in holds:
        holds[RAW_TOP].add("raw evidence paths retained")
    for rel in HISTORICAL_COPYTREE_LOGS & files.keys():
        holds[rel[len(PREFIX):].split("/")[0]].add("historical observation logs retained")

    # Scan working tracked consumers, including independently quoted basenames
    # and date/topic pieces. Ordinary Markdown code spans remain indexable debt.
    tracked = git(root, "ls-files", "-z").decode().split("\0")
    aliases = {t: {t} for t in tops}
    for top in tops:
        if match := DATED.fullmatch(top):
            aliases.setdefault(match.group(2), set()).add(top)
    name_matcher = PinNames(aliases)
    links = []
    for rel in tracked:
        if not rel or rel.startswith("external/"):
            continue
        path = root / rel
        if not path.is_file() or path.is_symlink():
            continue
        is_md = path.suffix.lower() in {".md", ".html"}
        machine = rel.startswith(("tools/", "orchestrator/")) or (
            rel.startswith(("docs/", "output/")) and (
                not is_md or re.search(r"manifest|prereg|schema", path.name, re.I)
            )
        )
        if not (is_md or machine):
            continue
        opener = gzip.open if path.suffix == ".gz" else open
        markdown_lines = []
        try:
            with opener(path, "rt", encoding="utf-8", errors="replace") as stream:
                for number, line in enumerate(stream, 1):
                    pin_line = bool(re.search(r"sha256|manifest|prereg|digest|path.pin|\b[0-9a-f]{64}\b", line, re.I))
                    if rel not in HISTORICAL_COPYTREE_LOGS and (machine or pin_line):
                        for hit in name_matcher.find(line):
                            for top in aliases[hit]:
                                if (not rel.startswith(PREFIX + top + "/")
                                        or top in line or top[:10] in line):
                                    holds[top].add(f"machine/pin reference: {rel}:{number}")
                    if is_md:
                        markdown_lines.append(line)
            if is_md:
                for target in link_targets("".join(markdown_lines)):
                    resolved = local_target(rel, target, root)
                    if resolved:
                        try:
                            # stat keeps permission/I/O errors visible even on
                            # Python versions where Path.exists suppresses them.
                            (root / resolved).stat()
                        except OSError as exc:
                            if exc.errno in {errno.ENOENT, errno.ENOTDIR, errno.ENAMETOOLONG}:
                                continue
                            raise
                        links.append((rel, target, resolved))
        except (OSError, EOFError) as exc:
            raise ValueError(f"reference scan failed: {rel}: {exc}") from exc
    moves = {top: dest for top, dest in moves.items() if not holds[top]}
    # Removing a move can expose another cross-directory link: close to a fixpoint.
    while True:
        rejected = set()
        for source, target, old_target in links:
            if local_target(relocated(source, moves), target, root) != relocated(old_target, moves):
                for rel in (source, old_target):
                    if rel.startswith(PREFIX):
                        top = rel[len(PREFIX):].split("/")[0]
                        if top in moves:
                            rejected.add(top)
                            holds[top].add(f"existing link would break: {source} -> {target}")
        if not rejected:
            break
        for top in rejected:
            del moves[top]
    raw = {}
    for rel in files:
        parent = str(Path(rel).parent)
        raw.setdefault(parent, []).append(rel)
    raw = {p: sorted(leaves) for p, leaves in sorted(raw.items()) if len(leaves) > 1000}
    dates = sorted({dest.split("/")[0] for dest in moves.values()})
    result = {"base": base, "files": files, "moves": moves,
              "holds": {top: sorted(reasons) for top, reasons in holds.items() if reasons},
              "raw": raw, "summary": {"files": len(files), "before": len(tops),
                  "moved": len(moves), "after": len(tops) - len(moves) + len(dates) + 2}}
    preflight(root, result)
    return result


def navigation(plan: dict) -> dict[str, str]:
    pages = {}
    date_rows = {}
    for top in sorted(set(plan["moves"]) | set(plan["holds"])):
        day = top[:10] if DATED.fullmatch(top) else "legacy"
        dest = plan["moves"].get(top, top)
        labels = {
            "legacy standalone or undated entry": "既存の単独資料・日付なし",
            "execution material": "実行資材を含む",
            "raw evidence paths retained": "生証拠の配置を保持",
            "historical observation logs retained": "過去の観測ログの配置を保持",
            "machine/pin reference": "固定参照を保持",
            "existing link would break": "既存リンクを保持",
        }
        reason = "、".join(sorted({labels[r.split(":", 1)[0]]
                                  for r in plan["holds"].get(top, [])}))
        date_rows.setdefault(day, []).append(f"- [{top}](../{quote(dest)})" + (f" — 保留: {reason}" if reason else ""))
    index = ["# 研究資料", "", "旧名から現在の資料へたどる日付別一覧。",
             "保留理由の詳細は移行計画JSONを参照。", ""]
    for day, rows in sorted(date_rows.items()):
        pages[f"{GUIDE}/{day}.md"] = f"# {day}\n\n" + "\n".join(rows) + "\n"
        index.append(f"- [{day}](layout-index/{day}.md)")
    for group, (directory, leaves) in enumerate(plan["raw"].items(), 1):
        for start in range(0, len(leaves), 500):
            name = f"raw-{group}-{start // 500 + 1}.md"
            rows = [f"- [{Path(p).name}]({quote(os.path.relpath(relocated(p, plan['moves']), GUIDE))})" for p in leaves[start:start + 500]]
            pages[f"{GUIDE}/{name}"] = f"# {directory}\n\n" + "\n".join(rows) + "\n"
            index.append(f"- [生証拠 {group}・{start // 500 + 1}ページ](layout-index/{name})")
    pages[PREFIX + "README.md"] = "\n".join(index) + "\n"
    return pages


def preflight(root: Path, plan: dict) -> None:
    destinations = [PREFIX + d for d in plan["moves"].values()]
    destinations += list(navigation(plan))
    if len(destinations) != len(set(destinations)):
        raise ValueError("duplicate destination")
    for rel in destinations:
        path = root / rel
        if os.path.lexists(path):
            raise ValueError(f"destination collision: {rel}")
        for parent in path.parents:
            if parent == root:
                break
            if parent.is_symlink() or (parent.exists() and not parent.is_dir()):
                raise ValueError(f"unsafe destination parent: {parent}")


def apply_plan(root: Path, plan: dict) -> None:
    current = build_plan(root, plan["base"])
    if current != plan:
        raise ValueError("reviewed plan is stale or edited")
    # Entire plan was checked before the first mkdir/move. rename preserves all
    # file bytes and modes; no copy/recompression and no index writes.
    for top, dest in plan["moves"].items():
        target = root / PREFIX / dest
        target.parent.mkdir(exist_ok=True)
        if os.path.lexists(target):
            raise ValueError(f"destination collision: {target}")
        (root / PREFIX / top).rename(target)
    for rel, content in navigation(plan).items():
        path = root / rel
        path.parent.mkdir(exist_ok=True)
        with path.open("x", encoding="utf-8") as stream:
            stream.write(content)
    verify(root, plan["files"], plan["moves"])


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, default=Path(__file__).resolve().parents[1])
    operation = parser.add_mutually_exclusive_group()
    operation.add_argument("--apply", type=Path, metavar="REVIEWED_PLAN_JSON")
    operation.add_argument("--verify", type=Path, metavar="APPLIED_PLAN_JSON")
    parser.add_argument("--output", type=Path, metavar="NEW_JSON_FILE",
                        help="新規JSONへ保存し、標準出力には件数のみ表示（上書き不可）")
    args = parser.parse_args()
    output = None
    try:
        if args.output:
            # Reserve before apply so an output collision never follows a move.
            # Keep this report outside the evidence inventory being verified.
            if args.output.resolve().is_relative_to((args.repo / PREFIX).resolve()):
                raise ValueError("JSON保存先は output/insights の外を指定してください")
            output = args.output.open("x", encoding="utf-8")
        if args.apply or args.verify:
            plan = json.loads((args.apply or args.verify).read_text())
            if plan["base"] != BASE:
                raise ValueError("unexpected baseline")
            if args.apply:
                apply_plan(args.repo.resolve(), plan)
            else:
                root = args.repo.resolve()
                if plan["files"] != inventory(root, BASE):
                    raise ValueError("baseline inventory mismatch")
                verify(root, plan["files"], plan["moves"])
                for rel, content in navigation(plan).items():
                    regular(root, rel)
                    if (root / rel).read_text(encoding="utf-8") != content:
                        raise ValueError(f"navigation mismatch: {rel}")
        else:
            plan = build_plan(args.repo.resolve(), BASE)
        payload = json.dumps(plan, indent=2, ensure_ascii=True) + "\n"
        if output is not None:
            output.write(payload)
            output.close()
            print(json.dumps(plan["summary"], ensure_ascii=True))
        else:
            print(payload, end="")
        return 0
    except (OSError, ValueError, subprocess.CalledProcessError) as exc:
        if output is not None:
            output.close()
            args.output.unlink()
        parser.exit(1, f"資料移行: {ascii(str(exc))}\n")


if __name__ == "__main__":
    raise SystemExit(main())
