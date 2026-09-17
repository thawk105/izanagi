# 可逆最小正規化の記録 (DW-S07)

`git diff --check` の末尾空白抵触を避けるため、次の file だけ**行末の空白 (半角空白 / tab) を落とした**。可視文字は不変。
復元法: 下表の (行番号, 落とした文字列) を各行末へ戻すと原文 bytes に戻る (原文 sha256 と byte 数で検算)。
原文は job dir `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2731-cpp-normalize-dd/` に残る。

## `probe-evidence-root.diff.txt`

- 原文 sha256: `374cb352332eba4dc9816dadbbf34e61c3e25559a3b08e7483bd04ae477fcf2c` (1708 bytes)
- 正規化後 sha256: `b09b8eb54d26865c726c371f3eb145ea72a5edf02c8cab51d4b9c8a9719d8a47` (1700 bytes)
- 落とした行末: 行 6: '    ', 行 11: '    '

## `s5-focus-run-2.log`

- 原文 sha256: `1e9c48bc5ec39e8711d96b51a22b808ecd47f97905ded66cb58d808e988386a3` (7049 bytes)
- 正規化後 sha256: `c6c0c9b80828cf7143112e6376e1a132ac51be8e40643550fe1e905e777356f6` (7046 bytes)
- 落とした行末: 行 14: ' ', 行 33: ' ', 行 52: ' '

## `s5-focus-run.log`

- 原文 sha256: `ea3ab7debf52eefd3cebbb4b455bce881466006f7ca3a118c2804e53dfcb9d59` (3857 bytes)
- 正規化後 sha256: `c716e386bf7616e1fb4505a6eddcd77fadcf23c70f197a6469de11885e331ae2` (3855 bytes)
- 落とした行末: 行 14: ' ', 行 34: ' '
