## 総括

静的 10 µs の `fixed10` 経路を修正しました。receipt がある場合は、本流と同じ offline configure 引数を同じ condition gate に渡します。gate の判定内容は変更していません。commit は作成していません。

## 変更 file と行数

- [p3_s4_loop_policy.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/t2867-run-author-y/orchestrator/campaign/p3_s4_loop_policy.py:439): +10／−1 行
- [test_p3_s4_loop_policy.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/t2867-run-author-y/orchestrator/tests/test_p3_s4_loop_policy.py:739): +54 行。既存試験の期待値は変更していません。

## 現行の受理・拒否挙動と変更後

変更前は、receipt があっても `fixed10` は gate を引数なしで呼び、記録された計算ノード実行では `config.h` 不在で拒否されました。変更後は receipt がある場合だけ本流と同じ入力を渡します。receipt がない場合の呼出し、stock・候補経路、CLI、既定 cfg は従来どおりです。

## 試験

- `test_fixed10_condition_gate_uses_offline_args_only_with_receipt[receipt]`
- `test_fixed10_condition_gate_uses_offline_args_only_with_receipt[no-receipt]`

gate 呼出し境界、offline 引数の射影、patch 適用、再開確認、campaign 実行、認可を試験内で差し替えています。`py_compile` と `git diff --check` は通過しました。指定の `run_tests.py` は **dispatch の `qstat -Q` 事前確認で rc=16** となり、試験の子プロセスは起動していません。実装済み・未実走です。

## 所有外への波及

所有外の caller・共有 fixture・consumer test・inventory を静的確認しました。`test_campaign.py` の certified-writer caller inventory は当該 driver の `run_campaign` 2 箇所を数えますが、呼出し数は不変です。`test_p3_exploration_namespace.py` の gate fixture、`test_p3_s4_loop.py` の gate 呼出し検査を確認しました。`test_p3_b4_wiring_probe.py` に該当参照はありません。

## 変異の位置

- M1: [driver:441](/work/1/SFC/tanab/izanagi/.claude/worktrees/t2867-run-author-y/orchestrator/campaign/p3_s4_loop_policy.py:441) の `configure_args` を外す変異 → `[receipt]` が検出。
- M2: [driver:439](/work/1/SFC/tanab/izanagi/.claude/worktrees/t2867-run-author-y/orchestrator/campaign/p3_s4_loop_policy.py:439) の receipt 条件を外す変異 → `[no-receipt]` が検出。

## 未解決・報告して止めたこと

試験は dispatch 障害のため未実走です。静的 10 µs の計算ノード実測も、この作業では行っていません。