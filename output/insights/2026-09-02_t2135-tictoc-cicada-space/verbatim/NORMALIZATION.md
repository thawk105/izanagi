# 逐語の可逆最小正規化 (DW-S07)

`git diff --check` が行末空白を検出したため、**行末空白の除去だけ**を行った。
可視文字は 1 文字も変えていない。除去された空白は Markdown の hard line break 記法
(行末 2 空白) と、親が書いた erratum の shell 例 1 行の末尾空白である。

## 復元方法

各行の末尾へ元の空白を戻す操作は、下記の「除去前 sha256」と一致するまで
行末に空白を付け直すことで確認できる。除去は次と等価である。

```
perl -pe 's/[ \t]+$//' <除去前> > <除去後>
```

## 除去前の原文 hash と byte 数

| file | 除去前 sha256 | 除去前 byte |
|---|---|---|
| `mutation-erratum.md` (親作成) | `e3b95289c63fdc79390ecd7782ceefad63feb75fc392410631f1fc398237c2d5` | 1444 |
| `verbatim/s2-plan.md` | `88b4e5cf4af1ee5ea83a9fb925cbacd1c8372b08c1f20cbb42da1a3e71c62180` | 17653 |
| `verbatim/s3-lens-a.md` | `4214cd9b27f0c9b9c5b81e7700deb33160471ecade61be3a995d16af536b9ebb` | 11568 |
| `verbatim/s3-lens-b.md` | `08f6ddd903f4504f6281e4a72be7a8273dd2f757d3c4c0cecbdb13d0828d8f1d` | 15909 |
| `verbatim/s5-author.md` | `81c7b2bfb167979a716b500097c8e0ca4be1a2061032dcdef916e0ccdd8a0deb` | 6539 |
| `verbatim/s6-fix1.md` | `a4e7085d38608838bfc1ce6c7a91f238c9e52744c270e6aabe2058fa5becd435` | 4096 |
| `verbatim/s6-focus.md` | `827ec0d0be60dbaa455ed3ee2555c456be60a74fd71b17dc0476171525f3b0a1` | 9135 |
| `verbatim/s6-review-a.md` | `c77d20ccdd1a916e1dd936c69817e2a15474ac58d09599b463c47cfa04fde67c` | 11769 |
| `verbatim/s6-review-b.md` | `e94d16593cd3ca54526db7ef418b93dc9ab20a6c1c40a321dd302479f2b126dc` | 8333 |

`verbatim/s5-author.md` の除去前 sha256 は、段 5 実装子の受領証
(`receipt.json` の `attempts[0].output_sha256`) が記録する値と一致する。

行末空白を持たなかった逐語 (`s1-brief.md`、`s3-parent-remeasure.md`、`s4-ruling.md`、
`s6-focus2.md`、`s6-parent-remeasure-2.md`) は変更していない。
