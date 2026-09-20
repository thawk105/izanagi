# 逐語 file の可逆正規化の記録 (DW-S07)

`git diff --check` の行末空白抵触を、可視文字を変えずに行末の空白だけ削って解消した。復元法: 各行番号の末尾へ記録した空白列 (space = `s`、tab = `t`) を戻す。

## pilot/qsub-pilot.log

- 原文 sha256 `bc094f330836465ce0cf24d217d1c0d7c6f9a5b73871c1ff1be2969242c8d703` (583 bytes) → 正規化後 `b6f32f13fb7906d951b6114e374c022eb786ffb5b177d156a7d92f56530f2498` (579 bytes)、削った行数 4
- 行番号: 削った空白列 — 1: s、2: s、3: s、4: s

## verbatim/s3-consult-A.md

- 原文 sha256 `c93a06d08446aa69719d161af55bacacf1229b5dd6855eca0d6f1bc65935077f` (21882 bytes) → 正規化後 `a95963a410ee10f854a5ac9b8e3d3aa07f1977de88291e3240b170d3ffa65dc2` (21820 bytes)、削った行数 31
- 行番号: 削った空白列 — 11: ss、12: ss、25: ss、26: ss、41: ss、42: ss、53: ss、54: ss、71: ss、72: ss、83: ss、84: ss、95: ss、96: ss、103: ss、112: ss、113: ss、130: ss、131: ss、138: ss、143: ss、144: ss、155: ss、156: ss、173: ss、174: ss、179: ss、188: ss、189: ss、212: ss、213: ss

## verbatim/s6-review-A.md

- 原文 sha256 `f5e3708ded056c49b6773bec5f8e5e97603fe1c1c81699f88b1f45142a1f9933` (21889 bytes) → 正規化後 `b84001074f2b2c41e65ad37c9dedf02b27576fc7d0306f0169ef061d82003df6` (21863 bytes)、削った行数 13
- 行番号: 削った空白列 — 17: ss、36: ss、51: ss、71: ss、82: ss、93: ss、106: ss、126: ss、141: ss、159: ss、170: ss、198: ss、209: ss

## verbatim/s6-review-B.md

- 原文 sha256 `582ea6526d3d567124efaaf99d02772a1ae18d6b064714ad17c57c2ce647074f` (20066 bytes) → 正規化後 `bc68b7a9e4144ec755b6ab13dedc5588ccf22314ee407b366c6ee1fdbcbdbe1f` (20038 bytes)、削った行数 14
- 行番号: 削った空白列 — 18: ss、31: ss、44: ss、57: ss、68: ss、79: ss、94: ss、105: ss、123: ss、136: ss、162: ss、187: ss、204: ss、220: ss

復元は「行 L の末尾に記録の空白列を戻す」だけで、正規化後 sha256 と原文 sha256 の両方で検算できる。
