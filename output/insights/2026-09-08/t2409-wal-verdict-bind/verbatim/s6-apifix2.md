## 変更した内容

合成 `prereg.spec` への依存を除去しました。

- 実 lock 由来の歴史 spec を使用。
- validator が受け取った spec を記録。
- 歴史 `spec_sha256` を固定検査。
- 受信 spec の `block_orders` から cell を構築。

## 変更した file と行

- [test_b10_backoff_shape_sweep.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2409-wal-verdict-bind/orchestrator/tests/test_b10_backoff_shape_sweep.py:3581)
  - 歴史 spec の取得: 3581
  - `block_orders` による cell 構築: 3590
  - validator の spec 記録と digest 検査: 3649

production、docs は変更していません。

## 走らせた検査と結果

- 指定の file 全体: rc=16
  - `qstat -Q preflight rc=1`
  - `child_started=false`
  - 未実走
- 対象 2 node の限定実行: rc=16
  - 同じ dispatch 障害
  - 未実走
- `git diff --check`: rc=0
- `python3 tools/check_codex_agents.py`: rc=0
- `python3 tools/check_docs.py`: rc=0

## 赤の内訳と帰属

- 対象 2 件: 本 wave 帰属。原因箇所を修正済みですが、dispatch 障害のため緑は未確認です。
- `test_t1905_a5_tmp_official_root_is_rejected_by_real_durable_policy`: 別 wave 帰属。未変更です。
- 今回は test process 自体が未起動のため、新しい赤の有無も未確認です。

## 総括

要求された helper の最小修正のみ完了しました。commit、push、branch 操作は行っていません。