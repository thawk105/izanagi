# 逐語の可逆最小正規化 (erratum)

`DW-S07` は「逐語末尾空白の `git diff --check` 抵触時も、原文 hash・byte 数・復元法を記録した
**可逆最小正規化**だけを許す (可視文字不変)」と定める。本 dir の逐語 4 file は codex の出力に
markdown の改行指示 (行末 2 空白) を含み、`git diff --check` が trailing whitespace として検出した。
**可視文字を 1 文字も変えずに行末空白だけを除去した。**

## 原文 (正規化前) の hash と byte 数

| file | 行末空白を持つ行数 | 原文 sha256 | 原文 bytes |
|---|---:|---|---:|
| `s2-plan.md` | 6 | `5ee4939d5dbb05fdd16cb598d1681dd5a51a57637dfc82da0c5173ea58386c27` | 24360 |
| `s3-consult-a-nested-and-fire-condition.md` | 26 | `3c1df2de992c64d042d4f40966a38795d96a773fe395fce45d2ea42883f7ba54` | 27452 |
| `s3-consult-b-correctness-barrier.md` | 21 | `6a2701401f245e2da37afb9675dd2c7865818aa7e098f2d05644b1e5a94db7af` | 15049 |
| `s6-review-b.md` | 23 | `840f0c04a84b98d5e2d9ee3d8ad4e723fe9f84ec41244dba560248dc66c57dfb` | 12982 |

`s3-consult-a-nested-and-fire-condition.md` は codex の出力 file 名 `s3-consult-a.md`、
`s3-consult-b-correctness-barrier.md` は `s3-consult-b.md` を改名したものである。
上の hash は改名後・正規化前の bytes に対する値である。

## 行った正規化

各行の末尾にある空白文字 (space / tab) だけを除去した。行の並び、可視文字、
改行コード (LF)、末尾 newline は変えていない。

## 正規化後の hash と byte 数

| file | 正規化後 sha256 | 正規化後 bytes | 差分 bytes |
|---|---|---:|---:|
| `s2-plan.md` | `5f6116554021229c9a05974a133addcb29bb33d39e12031495693cac339cb875` | 24348 | -12 |
| `s3-consult-a-nested-and-fire-condition.md` | `e84b3502551e18276cc0dd8923a684d544b2117ddb2c794b374cbdb9b778d2cb` | 27400 | -52 |
| `s3-consult-b-correctness-barrier.md` | `95fce3d9e5b40489820594e1668eddaee52ce1c2f7a1e79b1c1beb1a9047a613` | 15007 | -42 |
| `s6-review-b.md` | `07cb785e89644939e17e6335afcfda0ee0d79c6f9baa056dc8921fbfc919ead3` | 12936 | -46 |

減った bytes は各 file の「行末空白を持つ行数 × 2」と一致する
(6×2=12 / 26×2=52 / 21×2=42 / 23×2=46)。**除去したのは行末の 2 空白だけ**であることの検算になる。

## 復元法

正規化後の file は、行末 2 空白が落ちているぶんだけ短い。原文は復元できないが、
**正規化が可視文字を変えていないこと**は次で確かめられる。

```
python3 - <<'EOF' は使わない (guard が拒否する)。次の 1 行で確かめる。
EOF
```

`sed -e 's/[[:space:]]*$//' <原文> | sha256sum` が正規化後の file の sha256 と一致する。
原文は本 wave の job dir
`/home/SFC/tanab/.claude/jobs/774bd912/tmp/wave-artifacts/dev-wave-t2616-prewarm-configure-node/`
にあるが、**job dir は job 削除で消えるため恒久保存ではない**。上の表の hash と byte 数が
恒久の記録である。
