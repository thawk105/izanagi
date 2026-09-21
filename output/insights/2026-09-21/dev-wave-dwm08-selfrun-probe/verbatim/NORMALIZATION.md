# verbatim の可逆最小正規化 (末尾空白の除去のみ、可視文字不変、DW-S07)

`git diff --check` の末尾空白抵触を避けるため、次の file の行末の空白 (半角空白 / tab) だけを除去した。原文は job dir `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-dwm08-selfrun-probe/codex/` にそのまま残る。復元は各行末へ記載の bytes を戻す。

| file | 原文 sha256 | 原文 bytes | 正規化後 sha256 | 正規化後 bytes | 除去 (行: 除去 bytes) |
|---|---|---|---|---|---|
| s6-focus-A.md | 3cc46e59afded96f98dc7697ab7cc9401f2365639908cce692e9b867f3d3e2fe | 6445 | e8a50ea83194478d32e6f9609608cf21ca6260c926a017832998a4109ad85b87 | 6433 | 33, 34, 37, 38, 41, 42: 各 b'  ' (2 bytes) |

他の verbatim (origin.md、brief.md、brief-v2.md、s6-fix-table.md、s6-review-A.md、semantic_diff_002f926f4_to_956cce1c9.txt、layer_bytes_956cce1c9.txt、fig13-probe-mtimes.txt、scripts.sha256) は末尾空白なしで原文のまま。
