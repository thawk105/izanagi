# 逐語・log の可逆最小正規化 (DW-S07)

`git diff --check` に抵触する行末空白 (space / tab) と、file 末尾の余分な空行だけを除去した。可視文字は変えていない。
復元法: 下表の各行番号の末尾に記録した除去文字列 (`repr`) を戻し、file 末尾に記録した数の空行 (`\n`) を戻すと原文の sha256 に一致する。
Codex の逐語 (markdown) の行末空白 2 つは改行の指示で、除去で表示の改行が 1 行へまとまることがあるが、文字は失わない。

## evidence/compute-1-dispatch.log

- 原文: 4939 byte、sha256 `514d36bd6c628022265ecb021b446a816a5bba3515070ee1b11d9b559464b394`
- 正規化後: 4938 byte、sha256 `ecdd5de1d2c9f809c6f962d899694d8b12feb223dc8011d35ebf365466e8f0d2`
- 除去 (行番号: 末尾文字列の repr): 33: b' '
- file 末尾で除いた空行: 0
- 原文の末尾改行: あり (保持)

## verbatim/s5-author-A.md

- 原文: 11266 byte、sha256 `1089aca9a0e61576a691268ef407d0699fd0ce4d797f04839cdabb2101a1cdcb`
- 正規化後: 11261 byte、sha256 `6f9c7be0b620018401e99ca19b711b94a8fe40d6b4942d80a8529faad861af76`
- 除去 (行番号: 末尾文字列の repr): 25: b' '、40: b' '、70: b' '、153: b' '、159: b' '
- file 末尾で除いた空行: 0
- 原文の末尾改行: なし (足していない)

## verbatim/s5-author-B.md

- 原文: 25779 byte、sha256 `569a0d77cf3a5727b5bd0cfa29004e5b1a0f2df342c64c8ca956c2736a367ef5`
- 正規化後: 25772 byte、sha256 `696a77d0ae74da61022c0e2a00ad736c361b77fd0c45b2bd6b558076cac8788a`
- 除去 (行番号: 末尾文字列の repr): 34: b' '、78: b' '、99: b' '、100: b' '、106: b' '、159: b' '、160: b' '
- file 末尾で除いた空行: 0
- 原文の末尾改行: なし (足していない)
