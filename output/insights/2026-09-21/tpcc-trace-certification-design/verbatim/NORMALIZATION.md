# verbatim の可逆な最小正規化 (DW-S07)

`git diff --check` の行末空白に当たる行だけを正規化した。見える文字は変えていない。

| file | 原文 sha256 / bytes | 正規化後 sha256 / bytes | 除去した位置 | 復元法 |
|---|---|---|---|---|
| `s3-consult-A.md` | `a21c45a2b773eb1ce6e8fb4daafa1d7556e65d06dfe2f1c5e4c052e42a49760e` / 22,182 | `04b2a2554074d9ea0fcd3db3b1877e71eaa1a31be6632694c36dbb25af9a6f2e` / 22,178 | 98 行目と 101 行目の行末の空白 2 文字ずつ (Markdown の改行指定、計 4 byte) | 両行の末尾に半角空白を 2 つずつ足すと原文の sha256 に戻る |

他の verbatim file (`s1-brief.md` / `s2-plan.md` / `s3-consult-B.md` / `s4-ruling.md` / `s6-review.md` / `s6-focus.md`) は行末空白を含まず、無変更で写した。
