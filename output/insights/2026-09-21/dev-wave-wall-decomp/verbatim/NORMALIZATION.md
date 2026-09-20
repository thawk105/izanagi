# verbatim の可逆最小正規化 (末尾空白の除去のみ、可視文字不変、DW-S07)

`git diff --check` の末尾空白抵触を避けるため、次の file の行末の空白 (半角空白 / tab) だけを除去した。原文は job dir `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-wall-decomp/` (codex/*.md、verbatim/*) にそのまま残る。復元は各行末へ記載の bytes を戻す。

| file | 原文 sha256 | 原文 bytes | 正規化後 sha256 | 正規化後 bytes | 除去 (行: 除去 bytes) |
|---|---|---|---|---|---|
| attempt_gaps_t2804_final.txt | 21736e669744feeba00c8abade4254994fcb059869313fae56e7b1d344361072 | 1502 | 33776cf12caa6924fffa9e5c334bae0add4a8e2d3328fda2169bcd275b31a792 | 1442 | 15 行、各行末の [b'    '] |
| focus-2-dispatch-evidence/mtimes.txt | 7aebf2a07d1e99d54c32abea3b9e6767f4c037ae072916184c622c8e558e1b9f | 344 | 7aebf2a07d1e99d54c32abea3b9e6767f4c037ae072916184c622c8e558e1b9f | 344 |  |
| s6-focus-A.md | b6508432c6b4c89552b45ca200a36c75d08aea8a960bce0525f7e056d4d44f2d | 7390 | b6508432c6b4c89552b45ca200a36c75d08aea8a960bce0525f7e056d4d44f2d | 7390 |  |
| s6-review-A.md | 410922b9a14412dbb601dff6d1f81cfa7f6092fbd70fc9f7461944107d8fb183 | 16388 | 4e144202c9514a0e2d34d4836c58ca3d1f7eb1af2cbb621d015b93e5c3239aee | 16386 | 131: b'  ' |
