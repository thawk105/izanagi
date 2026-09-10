## 変更

[orchestrator/tests/test_ccbench_spawn_sites.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2396-author/orchestrator/tests/test_ccbench_spawn_sites.py:879) の行番号 pin を2箇所とも `7146` から `7209` へ更新しました。他の tracked file は変更していません。

## 検査

- production scanner による実測:
  - `<module>.run_measurement`: `7209`
  - `<module>._run_measurement_v3`: `6962`
- deferred gate 台帳の全8 entry: 各 live sink とちょうど1件ずつ一致
- exact ledger テスト関数の直接実行: PASS
- `git diff --check`: PASS
- `tools/run_tests.py` 経由の対象 pytest: rc=16
  - `qstat -Q` preflight で dispatch infrastructure failure
  - child は未起動
  - 実装済み・未実走です

## 総括

自分で実測した正しい行番号は `7209` です。台帳定義と exact 集合 literal の2箇所を同じ値へ修正し、全 entry の一意一致を確認しました。ラッパー経由の pytest は dispatch 失敗のため緑とはしていません。