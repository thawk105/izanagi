# verbatim/ の可逆な最小正規化の記録 (DW-S07)

`git diff --check` の行末空白に抵触したため、可視文字を変えずに行末の空白だけを除いた。

| file | 原文 sha256 | 原文 bytes | 正規化後 sha256 | 正規化後 bytes | 変更 | 復元法 |
|---|---|---|---|---|---|---|
| `s6-focus-1.md` | `35be995b7cabeb0b88518b87145609974782c43ae18558be357f4de24d902989` | 10794 | `7983234e2bd09c653a140ddf26895ca705491d94b017b1a2fc242e1ad89d0906` | 10782 | 83〜88 行目 (`## 総括` の本文 6 行) の行末の半角空白 2 個ずつ (計 12 byte) を削除 | 83〜88 行目の末尾に半角空白を 2 個ずつ戻す。原文は job dir の `s6-focus-1.md` |
| `s6-review.md` | `6584f69b742d04646af9d18e97dc0baaf110a5d6206d6632f1a24dfa2a776871` | 11775 | `f483da4c96479de7e7008bfbab00394fa58167d05540c04be5eebee58f4da31a` | 11763 | 50〜55 行目 (`## 総括` の本文 6 行) の行末の半角空白 2 個ずつ (計 12 byte、Markdown の改行指定) を削除 | 50〜55 行目の末尾に半角空白を 2 個ずつ戻す。原文は job dir `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2847-verifier-detection-design/s6-review.md` |
