## 書いた file

[probe_truth_table.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2662-bounded-reference-truth-table/output/insights/2026-09-17/t2662-bounded-reference-truth-table/probe_truth_table.py) — 314 行。

主要関数の位置（同 file）:

- `load_tool`:22、`selftest`:42
- `regular_readable`:66、`real_paths`:73、`blob_from_git`:106
- `contents`:119、`quoted_contents`:138、`byte_record`:146
- `make_rows`:151、`summary_for`:224、`markdown`:235、`main`:258

標準 library のみ使用。エラー終了は rc=2（入力・module・出力）、3（selftest 不一致）、4（git）、5（実在 path）で区別します。

## 自己検査の実走結果

指定コマンドを実行し、rc=0。JSON も指定先に生成しました。以下は自己検査の参考値です。

```text
SELFTEST OK 6/6
total: 862
agree: 718
H>P: 144
P>H: 0
```

`H>P` 行の全 id:

```text
R0073 R0075 R0077 R0079 R0081 R0083 R0093 R0095 R0097
R0101 R0103 R0105 R0107 R0109 R0111 R0113 R0115 R0117 R0119
R0121 R0123 R0125 R0127 R0129 R0131 R0133 R0135 R0137 R0139
R0141 R0143 R0145 R0147 R0149 R0151 R0153 R0155 R0165 R0167
R0169 R0170 R0173 R0175 R0176 R0177 R0178 R0179 R0180
R0185 R0186 R0187 R0189 R0190 R0192 R0194 R0196 R0198
R0200 R0210 R0212 R0214 R0218 R0220 R0222 R0224 R0226
R0228 R0230 R0240 R0242 R0244 R0248 R0250 R0252 R0254
R0256 R0258 R0260 R0270 R0272 R0274 R0278 R0280 R0282
R0284 R0286 R0288 R0290 R0300 R0302 R0304 R0308 R0310
R0312 R0314 R0316 R0318 R0320 R0330 R0332 R0334 R0338
R0460 R0463 R0466 R0469 R0472 R0474 R0476 R0478 R0480
R0482 R0492 R0494 R0496 R0500 R0502 R0504 R0506 R0508
R0510 R0512 R0522 R0524 R0526 R0530
R0543 R0554 R0565 R0591 R0606 R0621 R0648 R0660 R0672
R0697 R0710 R0723 R0747 R0758 R0769 R0791 R0802 R0813
```

`P>H` 行の id: `[]`

実在 path の `H>P` 行:

```text
R0543 R0554 R0565 R0591 R0606 R0621 R0648 R0660 R0672
R0697 R0710 R0723 R0747 R0758 R0769 R0791 R0802 R0813
```

P14×C12 の陽性対照は、祖先 directory が helper・本番とも True（R0825）、file 自身はともに False（R0824）でした。

## 候補集合の網羅

実装した組:

| P型 | C型 |
|---|---|
| P0・P1 | C0〜C11 |
| P2〜P10・P12 | C0〜C10 |
| P11 | C0・C1 |
| P13・P14 | C12・C13 |
| 型なし | C14 単独 |

P2 は file と空白入り祖先の両方を起点にし、P12 は指定の 2 path を収録。引用・括り・右側衝突の全 variant を含めました。C11 は P0/P1 それぞれで指定範囲の全 21 offset を生成しています。

各 content に対して、`_reference_patterns` が返す file・祖先 pattern の全要素を個別行にしました。P13×C13 は各実在 file の 3 形、P14×C13 は実在 6 file の各 3 形です。

上記以外は契約の制限に従って除外しました。C14 は空 content・空 pattern の単独行です。

## 実在 path の扱い

`realpath-hits.txt` の順序を保持。以下の共通接頭辞に表の相対 path を連結した file を選びました。

```text
/work/1/SFC/tanab/dev-wave-jobs/dev-wave-suite-floor-recheck/measure/run2/before-after-0_898290.nqsv/tmp/pytest-of-tanab/pytest-0/
```

| 行 | 選択した file（共通接頭辞からの相対 path） | 検査 |
|---|---|---|
| 1 | `popen-gw38/test_generation_two_rejected_b0/g2 clean scan Ω/.gitattributes` | 存在・regular・読取可 |
| 2 | `popen-gw31/test_deterministic_artifacts_a0/a much longer root with spaces Ω/out/env/linux-baremetal/binaries/03cf76a54f56fe1615023dca369bd1d80c114488a65fe40b8425561dad522e71` | 存在・regular・読取可 |
| 3 | `popen-gw29/test_production_emitter_staged0/a much longer root with spaces Ω/repo/.gitattributes` | 存在・regular・読取可 |
| 4 | `popen-gw31/test_metacharacter_control_pat0/repo/output/insights/receipt[?]*.json` | 指定 file 自身、存在・regular・読取可 |
| 5 | `popen-gw3/test_chain_g2_env_tag_unchange0/g2 clean scan Ω/.gitattributes` | 存在・regular・読取可 |
| 6 | `popen-gw35/test_literal_pathspec_registry0/repo/:(glob)does-not-match` | 指定 file 自身、存在・regular・読取可 |

directory は `os.walk` の directory 名・file 名を sorted にして最初の regular file を選択しました。

P14 の `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2397-a1-attempt4/acceptance1.log` も存在・regular・読取可。C12 の main blob は `git cat-file` で取得成功。代役への置換はありません。

## 波及可能性

コードとして新規作成したのは probe 1 本だけです。指定された自己検査の生成物として `probe-selfcheck.json` も作成しました。既存 file は変更していません。`git diff --stat` は空でした。

`git status --short`:

```text
?? output/insights/2026-09-17/t2662-bounded-reference-truth-table/
```

この directory は作業開始時から未追跡で、既存の brief・裁定を含んでいました。`git add`・`git commit` は実行していません。

## 受理集合の自己申告

本番コード・既存テストは変更していないため、受理集合の変化は **0** です。

## 総括

probe を作成し、自己検査まで実走しました。今回の候補集合では差は `H>P` のみで、実在 path の合成参照でも発火しました。正本の表取得と最終判断は、親による job dir からの本走に引き継ぎます。