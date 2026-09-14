# 逐語の正規化 erratum

`verbatim/` の各 file は Codex 子の最終メッセージをそのまま置いたものである。ただし 4 file は
Markdown の hard line break として**行末の半角空白**を含んでおり、`git diff --check` に抵触した。
DW-S07 の「可逆最小正規化」に従い、**行末空白だけ**を削除して収録した。**可視文字は 1 つも
変わっていない。**

| file | 正規化前の byte 数 | 正規化前の sha256 | 削った行数 |
|---|---|---|---|
| `s2-plan.md` | 19820 | `c625c5830c96f6511efc31458f2b30ee6c89434735afe97d3c184f6d7da4b0ca` | 5 |
| `s3-lensA.md` | 9472 | `305f69ff6e5ee6dda5252b65628a30928b4c06eff4a225788523c9d9b50967bd` | 9 |
| `s3-lensB.md` | 13274 | `a423171e8b561a0fe98c0bc831951a497c61e73b645990fed0ba98cb81213e20` | 4 |
| `s6-lensC.md` | 5290 | `b0143f152555d418e6274495f4d165f547f074ba33251157b1ccc09bd7efe6d1` | 2 |

**復元法:** 削ったのは `[ \t]*$` にマッチする末尾空白だけである。正規化は
`sed -i 's/[ \t]*$//' <file>` で行った。元 bytes は wave の job directory
(`/home/SFC/tanab/.claude/jobs/b6c0f330/tmp/wave-artifacts/t434-t1709-t1338/`) にある Codex
launcher の成果物であり、その `receipt.json` が `output_sha256` として封じている。

他の 4 file (`s5-u1.md`、`s5-u2.md`、`s6-lensD.md`、`s6-fix1.md`) は無変更である。
