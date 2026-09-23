# verbatim/ の可逆な最小正規化の記録 (DW-S07)

`git diff --check` の行末空白 (Markdown の改行用の半角空白 2 個) に抵触したため、可視文字を変えずに行末の空白だけを除いた。

| file | 原文 sha256 | 原文 bytes | 正規化後 sha256 | 正規化後 bytes | 変更 | 復元法 |
|---|---|---|---|---|---|---|
| `s6-review.md` | `dff9eaa6d32c30bd8a76f9da51a2f4e2b80b26ffefd213eedb458b1009b453cc` | 6229 | `4a0d837c30c1f277235e109fc408360e4df1ec5f5a040b1bd906466c7244660a` | 6215 | 9・12・13・16・21・24・29 行目の行末の半角空白 2 個ずつ (計 14 byte) を削除 | 各行の末尾に半角空白 2 個を戻す。原文は job dir `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2847-patch-verify/codex/s6-review.md` |
| `s6-focus-1.md` | `e700fd9df3b87bffe458a712ba86dc0d45a2388e1fa4c0b35feb044f26e96302` | 5438 | `a907d5658ea9b50802f6cb4d6b368e4235ab333fdd2231891de2bbf0a728e833` | 5434 | 20・23 行目の行末の半角空白 2 個ずつ (計 4 byte) を削除 | 同上。原文は `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2847-patch-verify/codex/s6-focus-1.md` |
| `s6-focus-2.md` | `e8e710315ba101af139c8ef5055566421cb302114058f6a2f1d5ac1bdc8ddad0` | 4993 | `867ab30205381eba3ec213a48439855b745e86d20f86f53e5fbf03aaabead1b8` | 4987 | 19・20・27 行目の行末の半角空白 2 個ずつ (計 6 byte) を削除 | 同上。原文は `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2847-patch-verify/codex/s6-focus-2.md` |
