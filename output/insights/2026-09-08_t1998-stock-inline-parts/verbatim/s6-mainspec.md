## 書いた spec

[mutation-main-spec.json](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1998-stock-inline-parts/output/insights/2026-09-08_t1998-stock-inline-parts/mutation-main-spec.json) を新規作成しました。

## probe spec からの差分

- 全件の `expected_status`: `SURVIVED` から `KILLED`
- 全件の `expected_nodes`: probe 2 回目の観測 node
- その他の field の変更: 無い

`estimated_run_seconds` は実測範囲内のため `150` のままです。

## 期待 node の写し取り検算

| ID | spec | probe2 |
|---|---:|---:|
| M1 | 1 | 1 |
| M2 | 1 | 1 |
| M3 | 1 | 1 |
| M4 | 2 | 2 |
| M5 | 1 | 1 |
| M6 | 2 | 2 |
| M7 | 1 | 1 |
| M8 | 1 | 1 |
| M9 | 1 | 1 |
| M10 | 2 | 2 |
| M11 | 2 | 2 |
| M12 | 1 | 1 |
| M13 | 1 | 1 |
| M14 | 5 | 5 |
| M15 | 3 | 3 |
| M16 | 1 | 1 |

全件で文字列、順序、件数の完全一致を確認しました。

## 総括

JSON 構文と probe spec からの変換結果を検算済みです。指定外ファイルの変更、テスト、変異 harness、build、benchmark、qsub、git add、commit は行っていません。