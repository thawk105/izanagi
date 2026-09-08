## 変更した内容

- collector fixture の合成 lock 生成を削除。
- 3 系列とも `_historical_layout` 経由で現物 lock snapshot を配置。
- validator stub と `_collect_report_inputs` の呼び出し・戻り値を現行 API に追随。
- 135 cell / 270 slot、および拒否側の全不変条件は維持。

## 変更した file と行

- [test_b10_backoff_shape_sweep.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2409-wal-verdict-bind/orchestrator/tests/test_b10_backoff_shape_sweep.py:3577)
  - fixture: 3577–3669
  - 受理 test: 3672–3688
  - 拒否 test: 3691–3735

production・docs は未変更です。commit・push・branch 操作も行っていません。

## 走らせた検査と結果

- 指定 file 全体: rc=16、`qstat -Q` preflight 失敗。pytest child は未起動。
- 対象 2 node の限定実走: 同じく rc=16、pytest child は未起動。
- AST parse: 成功
- `check_codex_agents.py`: 成功
- `check_docs.py`: 成功
- `git diff --check`: 成功

## 赤の内訳と帰属

pytest は未実走のため、赤 node はありません。対象 2 node の緑、および他 node の regression 有無は未確認です。既知の `test_t1905_a5_tmp_official_root_is_rejected_by_real_durable_policy` にも触れていません。

## 総括

API 追随の修正は完了しています。残る確認は、Pegasus dispatch が利用可能な環境で指定コマンドを再実走することです。