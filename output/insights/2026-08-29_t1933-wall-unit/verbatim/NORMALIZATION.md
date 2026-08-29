# 逐語の可逆最小正規化 (DW-S07)

`git diff --check` が行末空白と EOF の余分な空行を検出したため、
**可視文字を変えない最小の正規化**だけを適用した。原文 hash・byte 数・復元法を以下に記録する。
正規化前の bytes は repo 外の job directory
`/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t1933-wall-unit/` にも残っている
(`out/s3-correctness.md`、`out/s3-effectiveness.md`、`analyze11.txt`、`analyze12.txt`、
`analyze_prof.txt`)。

## 適用した操作

- 行末空白の除去: `sed -i 's/[ \t][ \t]*$//' <file>`
  対象は `measurements/analyze11.txt`、`verbatim/s3-correctness.md`、`verbatim/s3-effectiveness.md`。
  Codex の 2 レンズは Markdown の hard line break (行末 2 空白) を使っており、
  除去で改行の描画が段落結合に変わるが、**文字は 1 つも失われていない**。
- EOF の余分な空行の除去: `perl -0pi -e 's/\n+\z/\n/' <file>`
  対象は `measurements/analyze12.txt`、`measurements/analyze_prof.txt`。
  末尾 newline は 1 つ残している。

## hash と byte 数

| path | 正規化前 sha256 | 前 bytes | 正規化後 sha256 | 後 bytes |
|---|---|---:|---|---:|
| `measurements/analyze11.txt` | `4d2db9e7e652bf4a8d5c762bffcc1d536be283ebd31a165fb985a2b3e7e48291` | 1,248 | `6345982454b41f0a8ae8c714de71d1619476652de315198d02aea3bbafc6c980` | 1,247 |
| `measurements/analyze12.txt` | `f949b47322a5b0254eeca64dedac91430f33f47af28da80e74d507ea0aed9882` | 1,314 | `5164b6c8e8d65b32f95fdaf1b3738c07a418da16dfd29d5ff8a423e35f78883e` | 1,313 |
| `measurements/analyze_prof.txt` | `3c641f00c6328b69ba96ef7947e1dfffd716ddd47fd02e671ab064ed3ae99584` | 6,448 | `00ab01c547b73c0250be8e57ad2abad26423b4f04dfd634f180f12d19b457df8` | 6,446 |
| `verbatim/s3-correctness.md` | `bd4783e5ff3cb98d3c97096fed3d81e7a9e2c77912adf3970c3fd6a364e7768a` | 20,155 | `9ff206d51c379fc891322c778c4babbc4492441e5b98b00e8e3687f268758538` | 20,007 |
| `verbatim/s3-effectiveness.md` | `a4df35f9b78309a4d0c5877c49a5e9d6ee1feb7a9cf40a32ec88b61cca6d454e` | 12,314 | `4133465f71da24e7bb0c569c3fcd40274bc2e9eea5424e34b0d22a7b31f2304f` | 12,232 |

## 復元法

正規化は空白の除去だけなので逆写像は一意に定まらない。原文が必要なときは
上記 job directory の同名 file を使い、`sha256sum` が「正規化前 sha256」と一致することで
同一性を確かめる。job directory が失われている場合、この正規化は**復元できない**。
その場合でも可視文字は本 repo 側の file と一致する。
