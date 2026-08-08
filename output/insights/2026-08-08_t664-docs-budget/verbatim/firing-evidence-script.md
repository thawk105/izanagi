# 親が段 1 で使った発火実績スクリプト (逐語)

`s1-evidence.md` の表を出したスクリプトそのもの。**欠陥品である** — 段 3 の 2 レンズが独立に
指摘したとおり、`jobs` を変数に持ちながら一度も走査しておらず、case-sensitive な少数 regex を
数えるだけで、読めないファイルを黙って skip する。**本 wave はこの hit 数を裁定根拠から外し、
直接事例だけを証拠に使った。** 再利用する場合はこの欠陥を先に直すこと。

実体は repo へ置かない (`.py` は D95 の実装面に当たり、Codex `role=author` を要求するため)。
稼働控えは `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t664-docs-budget/firing_evidence.py`。

```python
"""L2 節ごとに「内容による」発火実績を数える (ID 文字列検索ではない)。

親の独立実測。子の主張を段 4 で裏取りするために使う。
"""
import pathlib
import re
import sys

repo = pathlib.Path(sys.argv[1])
jobs = pathlib.Path("/work/1/SFC/tanab/dev-wave-jobs")

# 節 -> (bytes, 内容語の集合)。ID 文字列は入れない。
SECTIONS = {
    "DW-O04": (200, ["commit -F", "message file", "heredoc"]),
    "DW-O06": (210, ["index lock", "submodule.*偽赤", "sandbox 由来"]),
    "DW-O08": (183, ["submodule update --init", "未初期化"]),
    "DW-O09": (935, ["FROZEN_MANIFEST", "pin 閉包", "durable manifest", "凍結 snapshot"]),
    "DW-O10": (261, ["producer.*書く全ファイル", "write-path", "producer の出力 bytes"]),
    "DW-O11": (223, ["未 stage 削除", "rc=15", "削除を伴う"]),
    "DW-O12": (195, ["裁定予定を写", "実際に実行した手順", "逆の工程記録"]),
    "DW-O14": (200, ["monkeypatch", "注入 seam", "current_head"]),
    "DW-O16": (367, ["焦点再レビュー", "対応表", "closed / partial"]),
    "DW-O17": (702, ["trailer", "--dry-run -F", "full-history 監査"]),
    "DW-O18": (441, ["単独再走", "repo root", "偽赤", "帰属しない"]),
    "DW-O19": (602, ["git checkout --", "一時変異", "復元 bytes"]),
    "DW-O20": (489, ["check_wave_startup", "clean-tree", "untracked handoff"]),
}

TARGETS = [
    ("worklog", [repo / "docs" / "worklog.md"]),
    ("archive", sorted((repo / "docs" / "archive").glob("worklog-*.md"))),
    ("failures", [repo / "docs" / "failures.md"]),
    ("decisions", [repo / "docs" / "decisions.md"]),
    ("insights", sorted((repo / "output" / "insights").rglob("*.md"))),
]


def count(paths, pattern):
    rx = re.compile(pattern)
    n = 0
    for p in paths:
        try:
            text = p.read_text(errors="replace")
        except (OSError, UnicodeError):
            continue
        n += len(rx.findall(text))
    return n


print(f"{'節':8s} {'bytes':>5s}  " + "  ".join(f"{k:>9s}" for k, _ in TARGETS) + "   語別内訳")
for sec, (size, terms) in SECTIONS.items():
    totals = []
    for _, paths in TARGETS:
        totals.append(sum(count(paths, t) for t in terms))
    per_term = ", ".join(
        f"{t}={sum(count(paths, t) for _, paths in TARGETS)}" for t in terms
    )
    print(f"{sec:8s} {size:5d}  " + "  ".join(f"{n:9d}" for n in totals) + f"   {per_term}")
```
