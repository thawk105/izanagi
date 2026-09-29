# 逐語の行末空白の可逆な正規化 (DW-S07)

`git diff --check` の行末空白に抵触した逐語 file だけ、行末の空白 (半角空白・tab) を除いた。可視文字は不変。
復元法: 各行番号の行末へ、記録した個数・種類の空白 (repr) を付け直すと原文 bytes に戻り、原文 sha256 と一致する。

## verbatim/s3-consult-a-out.md

- 原文 sha256 `1efc51f4f25ea144453575c1b1f39423aaa6370ee25e75d9bd25a6f1c1a77668`、9366 bytes → 正規化後 sha256 `0686708821968ad7ca3aecca02265954f9efafbb3afc0016136608de36e8772d`、9362 bytes
- 行末空白: 31 行 (2 個 b'  ')、32 行 (2 個 b'  ')

## verbatim/s6-e1-con-out.md

- 原文 sha256 `f2a69d10ccfcb9d83fecac77ed1abc70b0380fe0a1323eb0430370aa3751abb0`、5595 bytes → 正規化後 sha256 `e3929b1cd3c3bf35948b29f964b746116c4ea5727d0827ba2f40332bc2929207`、5591 bytes
- 行末空白: 27 行 (2 個 b'  ')、28 行 (2 個 b'  ')

## verbatim/s6-e1-pro-out.md

- 原文 sha256 `89a080d09b0d0d7a4e6f5a8e00b97c2bdea5ee56b2cc167e667cfdf6c25a4912`、4364 bytes → 正規化後 sha256 `bbe351ec60a7e65b21153b4c72e0897911e22e1ed6e79831b46e11cf2df4fefc`、4352 bytes
- 行末空白: 9 行 (2 個 b'  ')、10 行 (2 個 b'  ')、11 行 (2 個 b'  ')、12 行 (2 個 b'  ')、29 行 (2 個 b'  ')、30 行 (2 個 b'  ')

## verbatim/s6-review-a-out.md

- 原文 sha256 `1f956710553abe39b67c99ed674e7988ebe10c9b15f8c4110eb7e911cb5f35d8`、2640 bytes → 正規化後 sha256 `866d6a17c1c45243610bd22f0ec8536245aa8fd07813ed541d9840654fe54e6c`、2636 bytes
- 行末空白: 17 行 (2 個 b'  ')、18 行 (2 個 b'  ')
