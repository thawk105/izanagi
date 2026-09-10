# fix Unit J 報告

## 1. F-J1 の根本原因と是正

admission 拒否用に `run_block` の factory 経由 return を追加し、既定の refused return 数を 13 本から14 本へ増やしたことが原因でした。

admission 拒否は実走前 gate 拒否なので、G12 claim 拒否と共通の `_make_gate_decision` return に集約しました。[s8b_oracle_driver.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t523-holdout-admission/orchestrator/campaign/s8b_oracle_driver.py:1328)

静的照合結果は以下の既定形です。

- `refused-via-gate-decision`: 13 本
- `budget_exhausted_before_attempt`: 1 本
- terminal status variable: 1 本

## 2. F-J2 の根本原因と是正

subprocess fixture が新設された共有 durable admission root を隔離しておらず、過去の one-shot claim と衝突して、本来の binding protocol violation より先に `refused`／rc 2 へ停止していました。

protocol テスト専用の一時 admission root を subprocess 内へ渡し、実際の reservation・claim・ledger 処理を保ったまま binding violation へ到達できるようにしました。[test_s8b_oracle_driver.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t523-holdout-admission/orchestrator/tests/test_s8b_oracle_driver.py:3576)

production の rc 意味論は変更していません。

- admission／gate refusal: rc 2
- protocol violation: rc 3

## 3. メタテスト・期待値を緩めていない根拠

メタテスト本体、rc 3 の期待値、skip 条件は変更していません。一時 root の locator だけを差し替えており、admission 実装自体は迂回していません。

AST による同等条件の静的照合と、`refused=2`／`protocol_violation=3` の rc smoke は成功しました。

## 4. 実走したテスト / 実走できなかったもの

対象 nodeid:

- `test_gate_decision_is_built_only_by_factory_and_all_run_returns_propagate`
- `test_v3_cli_subprocess_returns_rc_3_on_protocol_violation`

以下の両方を試しましたが、いずれも `qstat -Q preflight rc=1`、wrapper rc=16 で pytest 起動前に停止しました。

- `tools/run_tests.py --force-dispatch`
- `tools/run_tests.py` による自動配置

したがって状態は「実装済み・未実走」であり、緑は主張しません。

## 5. 気づいたが直していない点

Pegasus dispatch 基盤が現在利用できませんでした。指定外の [T-524]／[T-525]、docs、逐語、fixture の holdout 軸には触れていません。commit と git サブコマンドも実行していません。

## 総括

F-J1 は admission 拒否を既存の factory return へ集約し、return 形状契約を復元した。  
F-J2 は subprocess fixture の durable state 漏れを隔離し、protocol violation の rc 3 経路を維持した。  
メタテスト、期待値、production の rc 表は変更していない。  
静的検査は成功したが、dispatch 基盤 rc=16 のため対象 nodeid は未実走である。