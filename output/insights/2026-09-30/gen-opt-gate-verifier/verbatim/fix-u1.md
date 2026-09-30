## 変更内容 (file ごと、sha256)

- [ycsb.hh](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2884-u1/output/runs/t2884-u1/ccbench/include/ycsb.hh): 冒頭の `#line 17` を `#line 16` に修正。他の `#line` は変更していません。sha256: `6702d3b73b76d0a9f67a08716780c116a1c387d4191fd363ec4fc3e7432147e8`
- [launch_gate_liveness_v3.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2884-u1/output/runs/t2884-u1/scripts/launch_gate_liveness_v3.py): JSON の key 名を定数 `GATE_KEYS` に集約し、S・X・B・N の事前登録評価を条件別に修正。N の `descriptive` を起動器の正常な結果として扱います。sha256: `3871ac8699852182dbf605aaadbf6ec6e2ba38ba8dcce8483a696b583fd243ba`

commit は作成していません。

## `#line` の突き合わせ結果

`#if TRACE` 区間を除き、各 `#line` の指定番号から F の同じ番号の行と文字列比較しました。**213 論理行すべて一致**しました。変更後の指定番号は `16, 108, 109, 127, 132, 142, 166` です。`/usr/bin/clang-format --dry-run --Werror` は rc=0 でした。

## 起動器の key 名と条件別の評価 (自己確認の結果)

`report.py` に合わせ、違反計数は `unreachable`, `D1a`, `D1b1`, `D1b2`, `D1c`, `D2a`, `D2b_i`, `D2b_ii`、発生条件は `own_write_read_transactions`, `written_transactions`、D5 は `D5`、意味の版は `meaning_version` を読みます。

判定器を import し、空の `trace_0.log` と `gate_0.log` に `require_gate_witness=True` を指定して、版 2 の `gate_witness` を含む実際の JSON 投影を作りました。その**投影の値を条件ごとに変更した自己確認**では、S・X・B が `match`、N が `descriptive` でした。負例は X の発生条件 0、S の巡回 1、B の committed 0 がいずれも `mismatch`、N の gate 節欠落が `descriptive` でした。これらは起動器の評価関数の確認であり、4 条件の CCBench 実走結果ではありません。

## 実走した command と rc

- 論理行番号を突き合わせる Python 文字列処理: rc=0、213 行一致。
- `/usr/bin/clang-format --dry-run --Werror output/runs/t2884-u1/ccbench/include/ycsb.hh`: rc=0。
- `PYTHONPATH=<wave 木> python3` による `verify_trace_dir`・`result_to_dict` と `prereg` の合成投影自己確認: rc=0。
- 起動器の Python 構文 compile: rc=0。`sha256sum` と `git -C R/ccbench diff`: rc=0。
- 最初の import 確認は作業ディレクトリ側の判定器を読み、`require_gate_witness` 未対応で rc=1。`/tmp` から wave 木を `PYTHONPATH` に指定して再実行し、rc=0 で版 2 の投影を確認しました。
- ルートの `git status --short` は応答がなく中断し、rc=130。`R/ccbench` の `git status --short` は rc=0 でした。

## 未実走・残る懸念

pytest、CCBench build、計算ノードでの S・X・B・N 実走、TRACE=0 の前処理出力比較は未実走です。合成投影の自己確認は JSON の読み取りと評価分岐を検査したもので、各条件の実際の trace や D5 成立を証明しません。

## 総括

指定の 2 ファイルを修正し、F との全論理行一致、format、判定器の版 2 JSON に基づく条件別評価を確認しました。実走による事前登録の一致判定は残っています。