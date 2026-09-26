# 逐語・log の可逆最小正規化 (DW-S07)

`git diff --check` に抵触する行末空白 (space / tab) と、file 末尾の余分な空行だけを除去した。可視文字は変えていない。
復元法: 下表の各行番号の末尾に記録した除去文字列 (`repr`) を戻し、file 末尾に記録した数の空行 (`\n`) を戻すと原文の sha256 に一致する。
Codex の逐語 (markdown) の行末空白 2 つは改行の指示で、除去で表示の改行が 1 行へまとまることがあるが、文字は失わない。

## verbatim/s2-plan.md

- 原文: 22796 byte、sha256 `80d2d62a3504e3846362184c54d58166e965e3f7bef05dcb3555f764baf68c96`
- 正規化後: 22788 byte、sha256 `f9d62d70f5552873788719adbd95750fa0169698c126db9ce829dbb2951bfc0e`
- 除去 (行番号: 末尾文字列の repr): 100: b'  '、101: b'  '、102: b'  '、103: b'  '
- file 末尾で除いた空行: 0
- 原文の末尾改行: なし (足していない)

## verbatim/s3-consult-A2.md

- 原文: 6903 byte、sha256 `07be5423a6b0aea66959c6615a428713bf2d4f74ac78b1f8d609371f1af6888e`
- 正規化後: 6893 byte、sha256 `cf22f51c8c939f81b8fd390f265d4f47e61dd8ff55a32e4150548d77b7b2d95e`
- 除去 (行番号: 末尾文字列の repr): 35: b'  '、36: b'  '、37: b'  '、38: b'  '、39: b'  '
- file 末尾で除いた空行: 0
- 原文の末尾改行: なし (足していない)

## verbatim/s3-consult-B.md

- 原文: 11131 byte、sha256 `d6485dcaa95539d13638909131b7ff81332a29d9a171b18d78d91c56ce843aef`
- 正規化後: 11085 byte、sha256 `f2a222bdc7584ff1f2bdd586c6e52347b87e21a5bac3e76190f6dbc37ab3fe17`
- 除去 (行番号: 末尾文字列の repr): 3: b'  '、4: b'  '、7: b'  '、8: b'  '、11: b'  '、12: b'  '、15: b'  '、16: b'  '、19: b'  '、20: b'  '、23: b'  '、24: b'  '、27: b'  '、28: b'  '、31: b'  '、32: b'  '、35: b'  '、36: b'  '、41: b'  '、42: b'  '、43: b'  '、44: b'  '、45: b'  '
- file 末尾で除いた空行: 0
- 原文の末尾改行: なし (足していない)

## verbatim/s5-author.md

- 原文: 6551 byte、sha256 `16210d84b504adb02172525a6cb9d8c40a7ea0fd59e3f58779b4359a78073843`
- 正規化後: 6541 byte、sha256 `41a50922d70474f2efc342d898b9ea06b673634dd58a67d14fdda4a7cc619064`
- 除去 (行番号: 末尾文字列の repr): 57: b'  '、58: b'  '、59: b'  '、60: b'  '、61: b'  '
- file 末尾で除いた空行: 0
- 原文の末尾改行: なし (足していない)

## verbatim/s6-fix1.md

- 原文: 2650 byte、sha256 `9fc8c215bc8ce37ff730c71ca5dabd1d69c16ac9d5376ee0e92826abb1935981`
- 正規化後: 2640 byte、sha256 `e0768c9fc734ebdc46a4e503784d24d445f44f8e417a1f4cd73786750998d493`
- 除去 (行番号: 末尾文字列の repr): 28: b'  '、29: b'  '、30: b'  '、31: b'  '、32: b'  '
- file 末尾で除いた空行: 0
- 原文の末尾改行: なし (足していない)

## verbatim/s6-fix2.md

- 原文: 965 byte、sha256 `354eeac044a0571a1f6fdd8ec137e18cc0c5b38ecf0e19207f361d59e49ab792`
- 正規化後: 961 byte、sha256 `7980761cd1d53040baf3c866adc066425341f59bef798cce2585017cf9f3f6d2`
- 除去 (行番号: 末尾文字列の repr): 15: b'  '、16: b'  '
- file 末尾で除いた空行: 0
- 原文の末尾改行: なし (足していない)

## verbatim/s6-review-A.md

- 原文: 2736 byte、sha256 `53379e63f7176c43b2b8248ad367897e5c580495ce6d1e9e8094a56a8be3a053`
- 正規化後: 2728 byte、sha256 `dac270d3b4cda3c9ccc49c2e13356a56ead5fd066ca65de3eee70a3b8d22b286`
- 除去 (行番号: 末尾文字列の repr): 15: b'  '、16: b'  '、17: b'  '、18: b'  '
- file 末尾で除いた空行: 0
- 原文の末尾改行: なし (足していない)
