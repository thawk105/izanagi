# 逐語の可逆な最小正規化 (DW-S07)

`git diff --check` に抵触する行末空白だけを除いた。可視文字は変えていない。いずれも markdown の強制改行 (行末の空白 2 字) である。

| file | 原文 sha256 | 原文 byte 数 | 正規化後 sha256 | 正規化後 byte 数 | 空白 2 字を除いた行 |
|---|---|---:|---|---:|---|
| `s3-consult-A.md` | `777178e4ff6a54b845cba43c5d7ead1d2059c751500763e41738bf7669cb90bd` | 22,592 | `1b533444bb32415cd2f1e88422105ee5d8cd6405764538800b8377f7b5a6c273` | 22,586 | 66, 124, 149 |
| `s3-consult-B.md` | `85f3504d8f14a96c632bc9e37731a66c1a3c8e244b2d3590bad1ca2dbf31652c` | 15,198 | `3f9c2bdb16580c7b14ef5de7f8a09b217ebac857c91f66d50c75e6946e4eadcf` | 15,130 | 5, 6, 9, 10, 13, 14, 15, 18, 19, 20, 23, 24, 25, 28, 29, 30, 33, 43, 44, 45, 48, 49, 52, 53, 58, 59, 62, 63, 64, 67, 68, 69, 72, 75 |
| `s7-review-A.md` | `d9931e4ea8f3e9dfe114842842ca34c0719b3e59331c8ec7db2f4999786ee285` | 20,708 | `a3d4d53ad588d2b219abfb5d1f4c82a4274341cf5f437ea4f359b6e1c4abe390` | 20,692 | 41, 60, 71, 80, 87, 96, 110, 119 |

復元法: 表の各行の末尾に空白 2 字を足すと原文 sha256 に戻る。

他の逐語 (`brief.md`、`s2-plan.md`、`s3-auditor.md`、`s4-ruling.md`、`s7-auditor-focus.md`、`s7-focus-ruling-1.md`、`s7-focus-2.md`、`s7-focus-ruling-2.md`、`s7-focus-3.md`、`s7-focus-ruling-3.md`、`vldb-direction-verdicts.md`) は行末空白を含まず、原文のまま写した。`s3-auditor.md` と `s7-auditor-focus.md` は Claude subagent の最終報告を親が写したもので、harness が各行に付けた字下げ 2 字だけを除いている (各 file 冒頭に記載)。
