# 逐語の可逆最小正規化 (行末空白の除去)

`DW-S07` は逐語の末尾空白が `git diff --check` に抵触する場合、**原文 hash・byte 数・復元法を
記録した可逆最小正規化だけ**を許す。本 wave では下記 5 file が該当した。

正規化は **各行の末尾から空白 (U+0020) と水平タブ (U+0009) を除去する**だけである。
Markdown の hard line break (行末 2 空白) が失われるが、**可視文字は 1 文字も変わっていない。**
それ以外の byte は一切触れていない。

| file | 原文 sha256 | 原文 bytes | 正規化後 bytes |
|---|---|---|---|
| `s3-luna.md` | `9826f6b4e5dabeff051707dbcdcf5738ec783e6d2ceb6bc70a51966c5ec0f428` | 20324 | 20316 |
| `s5-author.md` | `bab18a6ce8ed82c3195caeb9f9df256c6a414f113bcf7bf8db3df369d5bc9bf8` | 3376 | 3370 |
| `s6-fix1.md` | `0b5f1b424ca98c39ec3ca997c76f0234ed760485cb204e3f9403fb53514d2505` | 3453 | 3447 |
| `s6-review-luna.md` | `24f7ea4e3fd265252dcb3fed82fe78839613a028f4690fed10938796aa2af237` | 19922 | 19900 |
| `s6-review-sol.md` | `7fd7a4c35d26c808af4a126139e1165b19c0151475db2636bda6a61a01d5eeb7` | 8601 | 8577 |

`s5-author.md` の原文 sha256 は、段 5 の Codex receipt の `output_sha256` と一致する。
receipt は wave の job directory
(`/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2102-b4-reference-tps-domain/artifacts/`) にあり、
repository には入れていない。

## 復元法

正規化は行末空白の除去だけなので、除去された位置と個数を記録しない限り厳密な復元はできない。
原文が要るときは wave の job directory
(`/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2102-b4-reference-tps-domain/artifacts/t2102-b4-reference-tps-domain/`)
にある同名 file を上表の sha256 で照合して使う。job directory は session の生存期間に依存するため、
恒久的な原文の所在ではない。**上表の hash と byte 数は、正規化が可視文字を変えていないことを
後から検算するための束縛**であり、原文そのものの保管を主張するものではない。

正規化後の各 file の内容が、原文から行末空白だけを落としたものであることは、
原文があれば `python3 -c "..."` 相当の再正規化で byte 一致を確かめられる。
