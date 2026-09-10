実装と単位 A のテスト追加を完了しました。commit・docs 編集・許可外ファイルの編集はありません。

変更対象は指定された6ファイルのみです。

波及可能性を静的確認しました。

- `test_autonomous_trial_completeness.py`: manifestless `run_trial()` 5件に明示 opt-in が必要。
- `test_campaign.py`: `main()` / `run_trial()` の探索起動に flag が必要。
- `test_claude_transport.py`: `run_trial()` に flag、`_finish_trial()` に admission、`_run_workload()` に sealed scope が必要。
- `test_role_session_isolation.py`: manifestless `run_trial()` positive に明示 opt-in が必要。
- 親 runbook の flag 追記は未 land。これに依存する赤は単位 C 起因として扱う必要があります。

静的検査結果:

- 対象6ファイルの `py_compile`: rc=0
- `git diff --check`: rc=0
- `tools/check_codex_agents.py`: rc=0
- `tools/check_docs.py`: rc=0

## 総括

- 実装した gate:
  - U-4 既定拒否、holdout 無条件拒否、登録済み ID の探索拒否
  - sealed `TrialLaunchAdmission` と run scope 必須化
  - U-1 capability 型・commit・再計算 effective・digest の完全照合
  - formal manifest `prereg_commit` との完全一致
  - 単一 lifecycle ledger 内の start-once、exclusive flock、strict JSONL、fsync、terminal-once
  - run-start/report の同一 `launch_admission` 記録
- pytest 実走 nodeid: なし。全3回とも計算ノード dispatch 前に `qstat -Q` が失敗し rc=16。
  - 対象3 test file 一括: rc=16
  - 新設主要7 nodeid: rc=16
  - `test_s8c_preregistration_invariant.py` meta-test: rc=16
- 残る赤・未確認:
  - NQS socket 作成不可（errno 1）のため、全 pytest は実装済み・未実走。
  - m10〜m15 は単位 B の receipt/acceptance/downstream 所有であり、本編集境界では未実装・未検証。
  - 上記所有外 caller tests は親による明示 opt-in / admission 引き回し更新まで回帰候補。