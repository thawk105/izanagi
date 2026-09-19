# 逐語の可逆最小正規化台帳 (DW-S07)

行末の空白 (markdown の 2 空白改行、diff の空 context 行の 1 空白) と EOF の余分な空行を除いた。可視文字は不変。
復元法: 各行末に元の空白を戻す。原文は job dir `/home/SFC/tanab/.claude/jobs/0a534e2c/tmp/` の同名 file (author-u1-out.md、review-a-out.md 等) と、
patch は `author-u1.patch` (原文 sha256 は下表)。

| file | 原文 sha256 | 原文 bytes | 正規化後 sha256 | 正規化後 bytes | 変更行数 |
|---|---|---:|---|---:|---:|
| author-u1-out.md | c9e1e4e4131ea54648640cd70213b021f839a4242f5c89d97cc63a2ee72f8360 | 5251 | b60bd5b90bf0d62ff649e1998d703709589d4d3989157ddb10ba9737bf579b93 | 5248 | 2 |
| author-u1-patch.md | 4ca9dac512857897c7511868d900e738056e5e0550594d2bfcf136f18964da81 | 8443 | 2e307d152d644664aebe69009c5e35c3235d5daeca30193bcb9cbbd9a612b4d2 | 8433 | 10 |
| brief.md | a5d75e691364a1ec7058708babe0770d00a3b583b13bce9e720ad6722dc1f3b7 | 6937 | bfcfca7b7f6fcb6aabd3029f263209d272ff3d23bed50dd888ba14795f570263 | 6936 | 0 |
| review-a-out.md | aaabf7379570d9422f123255366394ea0b5768b34787607538b05f87281dd577 | 8956 | 2383bd4e75a3d98f9307932473403ab938b1d18ef5a3f17565f6b309a348ac2f | 8929 | 14 |
| review-b-out.md | b5e40d7df61c669527cd4d867a5430e70ff3bd6e86ec04b3eafa48853def64c6 | 12186 | f4ce8f0c48f9d1bc2e235796cf3dff79e76ccd99b1c90de9d18899fc420a52cd | 12187 | 0 |
| rulings-verbatim.md | d6da45e67be38d8e96d07af469b61cc438e5aada36b110c0d3f3ec153de7b50d | 6831 | 6477a1707a83616292b50cbf1d089534472adfbf8101076aaff6a4eca10d1f24 | 6830 | 0 |
