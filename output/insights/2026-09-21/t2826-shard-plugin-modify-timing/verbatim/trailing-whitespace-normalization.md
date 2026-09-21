# 逐語の行末空白の可逆正規化 (DW-S07)

`git diff --check` に触れる行末空白を 1 file から除いた。可視文字は不変。

| file | 原文 sha256 | 原文 bytes | 正規化後 sha256 | 正規化後 bytes | 行数 |
|---|---|---|---|---|---|
| `verbatim/s3-consult-out.md` | `bbf8d66d0bc7d09a7dfc8f2b961ccb8b4ebc36beefea95e87cc2f4586589e395` | 17251 | `f4b67432c651f596db5802523105cb7695f1767d5aff8f38c511dd40ad9fc04f` | 17167 | 42 |

- 除いた suffix は 42 行すべて同じ **半角空白 2 個 (0x20 0x20)** (Markdown の改行用)。
- 対象の行番号 (1 始まり): 5, 6, 7, 8, 11, 12, 13, 14, 17, 18, 19, 20, 23, 24, 25, 26, 29, 30, 31, 32, 35, 36, 37, 38, 41, 42, 43, 44, 47, 48, 49, 50, 53, 54, 55, 56, 61, 62, 63, 101, 102, 103。
- 復元法: 上の各行の末尾へ半角空白 2 個を戻すと原文 bytes に戻る (17167 + 42 × 2 = 17251)。
- 原文は wave 専用 dir `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2826-shard-plugin-modify-timing/codex/s3-consult-out.md` に残っている。
- 正規化は `sed -i -E 's/[[:space:]]+$//'` の 1 回で、正規化後の file と「原文から行末空白だけを除いたもの」が `diff` で一致することを確かめた。
