## 所見ごとの対応表 (closed / partial / regressed)

| 所見 | 状態 | 対応 |
|---|---|---|
| fix 1：テスト復活 | partial | 実装済み・未実走 |
| fix 2：行番号 pin | partial | 実装済み・未実走 |

## 実装した差分 (file:line)

- `orchestrator/tests/test_s8b_oracle_driver.py:6276`：元の位置へ復活。docstring 以外の本文・assertion・注入 helper は基準 commit と逐語一致を確認。
- `orchestrator/tests/test_ccbench_spawn_sites.py:2942`：1793 → 1783。現物を指定の grep で確認。Counter は維持。manifest を指す pin はありません。

## 走らせたテストと結果 (実走 nodeid・範囲。未実走なら「実装済み・未実走」)

指定された両ファイル全体の runner コマンドを試しました。ともに `qstat -Q preflight rc=1` により **rc=16、child_started=false**。実走 nodeid はありません。**実装済み・未実走**です。

静的照合と `git diff --check` は通過しました。

## 所有外への波及可能性

production・docs は編集していません。指定 runner が `output/pegasus-dispatch/` 配下に receipt を生成しました。

## 指示と食い違った点

コード修正の逸脱はありません。runner による所有外の receipt 生成がありました。commit はしていません。

## 総括

2 件とも修正済みです。実走できていないため closed とはせず、親による検証へ引き継ぎます。