# verbatim の可逆最小正規化 (DW-S07)

`git diff --check` に抵触する行末空白を除去した。可視文字は不変。原本は repo 外 job dir `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2853-fig15-input/codex/` の同名 file。

| file | 原本 sha256 | 原本 byte | 変更行 | 正規化後 byte |
|---|---|---:|---|---:|
| `s6-review-A.md` | `267c0e4980627edad3a7cce685c791dc4b81bf7a1b2e78b25d4320cdd90b1a50` | 2970 | 20 行目 (「静的レビューのみ実施し、…」) の行末 space 2 個 | 2968 |

復元法: 20 行目の末尾に space 2 個を戻す (Markdown の強制改行)。
