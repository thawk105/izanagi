# verbatim の可逆最小正規化の記録

`git diff --check` の末尾空白抵触を避けるため、次の file だけ行末の空白を除いた (可視文字不変)。原本は job dir
`/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2791-mocc-upstream-report/codex/` にあり、復元法は各 record の `restore`。

```json
{
 "file": "s6-review-1.md",
 "original_sha256": "b3b3b5cc21b411157fc0ce69751f4b8155aaed2b29e41064e7d7455f2d11f160",
 "original_bytes": 10976,
 "normalized_sha256": "6dbb2c9d0a61475bfed17ec976e9c76214620ad2013d81b469b68369a25914b3",
 "normalized_bytes": 10946,
 "removed_trailing_whitespace_by_line": {
  "3": "  ",
  "7": "  ",
  "14": "  ",
  "18": "  ",
  "22": "  ",
  "30": "  ",
  "34": "  ",
  "38": "  ",
  "44": "  ",
  "48": "  ",
  "50": "  ",
  "55": "  ",
  "59": "  ",
  "63": "  ",
  "69": "  "
 },
 "restore": "各 line 番号の行末に removed の文字列 (JSON escape 済み、実体は空白 2 個) を付け直すと original_sha256 に戻る"
}
```
