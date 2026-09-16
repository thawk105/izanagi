# 逐語の可逆最小正規化 (erratum)

`git diff --check` の末尾空白検査に抵触したため、`DW-S07` が許す可逆最小正規化を 1 file に
だけ施した。**可視文字は 1 つも変えていない。**

## 対象

`s3-consult-sol-correctness-lens.md` (段 3 レンズ A の逐語)

| 項目 | 値 |
|---|---|
| 原文 sha256 | `6d46be7f5c3f079dab70241cfe808e7a1433489eb3841525442877a51398c27a` |
| 原文 byte 数 | 6901 |
| 正規化後 sha256 | `027cf9c26e397953b4f5a75e537aabf19b8fb9c18e1b08cb055d5466bb52e462` |
| 正規化後 byte 数 | 6897 |
| 変えた箇所 | 63 行目と 64 行目の**行末の半角空白 2 個ずつ、計 4 byte を削除** |

63・64 行は Markdown の強制改行 (行末 2 空白) であり、子が引用ブロック内で使ったものである。

## 復元法

63 行目と 64 行目の行末に半角空白を 2 個ずつ足すと原文 bytes に戻る。

```
sed -i '63s/$/  /' s3-consult-sol-correctness-lens.md
sed -i '64s/$/  /' s3-consult-sol-correctness-lens.md
```

復元後の sha256 が上表の原文 sha256 と一致することで可逆性を確認できる。
他の逐語 file には正規化を施していない。
