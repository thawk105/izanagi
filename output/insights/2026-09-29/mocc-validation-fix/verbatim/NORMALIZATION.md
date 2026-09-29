# verbatim の可逆正規化 (DW-S07)

`git diff --check` に抵触する行末の空白・tab と、file 末尾の余分な空行だけを除いた。可視文字は変えていない。
復元法: 各 file の `stripped_suffix_by_line` の行 (1 始まり) の末尾へ記録した文字列 (JSON の文字列、`\t` は tab) を戻し、`removed_trailing_newlines` の数だけ末尾に改行を足すと、`original_sha256` の bytes に戻る。

```json
[
 {
  "path": "verbatim/F-to-X-diff.md",
  "original_sha256": "ae6bc316e523e25d6316640f501daac735bfa718579a750c9393cd743d91da2b",
  "original_bytes": 1157,
  "normalized_sha256": "024d41845681dbcc6b721d4debce0b0fc9a7eb05655d908e2f9feac04dab07dd",
  "stripped_suffix_by_line": {
   "11": " ",
   "30": " "
  },
  "removed_trailing_newlines": 0
 },
 {
  "path": "verbatim/evidence/inventory-C.tsv",
  "original_sha256": "30e4f4331213d0528a008632844a0382310539a5d44131aec60dd87a5c54dcf9",
  "original_bytes": 1295,
  "normalized_sha256": "15e00e348e93ac76f513e47ea023ee9bf780e10a37033577a2b78ce059aeec94",
  "stripped_suffix_by_line": {
   "3": "\t",
   "4": "\t",
   "5": "\t",
   "6": "\t",
   "7": "\t",
   "8": "\t",
   "12": "\t"
  },
  "removed_trailing_newlines": 0
 },
 {
  "path": "verbatim/evidence/inventory-F.tsv",
  "original_sha256": "54c2531fb91d93a9c5011e969b89dc452683ff1d7eca38ecdac25a4bc6114284",
  "original_bytes": 1391,
  "normalized_sha256": "d694f5280eec837b3b90986452903bdf6fcf18c96fa861476f69cfc206218670",
  "stripped_suffix_by_line": {
   "5": "\t",
   "6": "\t",
   "7": "\t",
   "8": "\t",
   "12": "\t"
  },
  "removed_trailing_newlines": 0
 },
 {
  "path": "verbatim/evidence/inventory-X.tsv",
  "original_sha256": "1e8a92894205d756e58e75076dff0c79291e26f638f4b0a8bd4d26e3712fcaab",
  "original_bytes": 1391,
  "normalized_sha256": "32da0bb1b081074115458031b83a214eb6c12bcdc1e934b14efdc271371e7450",
  "stripped_suffix_by_line": {
   "5": "\t",
   "6": "\t",
   "7": "\t",
   "8": "\t",
   "12": "\t"
  },
  "removed_trailing_newlines": 0
 },
 {
  "path": "verbatim/evidence/smoke1-summary.md",
  "original_sha256": "3a6821766e0d4f5c6a0d05ba8c75481ea6a548b8f21bf7942e13ae1f3a41d48a",
  "original_bytes": 1361,
  "normalized_sha256": "b10268e52304d9585f8c309902d36470663b7ffd17d7db9c05124d186565ecd1",
  "stripped_suffix_by_line": {},
  "removed_trailing_newlines": 1
 },
 {
  "path": "verbatim/mk-X.log",
  "original_sha256": "2b4cdee26372e0fee16a2873169944535a39934e5d797816eb4c631e32f41c6a",
  "original_bytes": 4679,
  "normalized_sha256": "2974f5effc5618d4abe60d31ebf9bec56bd1252c546436fc3f2a844c423c498e",
  "stripped_suffix_by_line": {
   "26": " ",
   "45": " "
  },
  "removed_trailing_newlines": 0
 },
 {
  "path": "verbatim/s5-author-A.md",
  "original_sha256": "22b64a3f6e37c42a03aa00fc7cf121cddf8bfe078637ee7cc746b47e6a25accb",
  "original_bytes": 3602,
  "normalized_sha256": "609a922ca2935f8877ae6b481322d09731a5390947ce1be77432d23d45964af5",
  "stripped_suffix_by_line": {
   "13": " ",
   "32": " "
  },
  "removed_trailing_newlines": 0
 }
]
```
