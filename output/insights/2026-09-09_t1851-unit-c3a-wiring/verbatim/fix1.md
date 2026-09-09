## 総括

訂正済み ordinal 束縛へ launcher test helper を合わせ、元の 12 件を解消しました。  
planned は `retry_ordinal=None`、retry は `measurement_ordinal` に束縛しています。  
負例 2 件を新設し、3 file 合計 301 passed / 0 failed です。  
変更は所有 test だけで、production、docs、staging、commit はありません。

## 直した helper と理由 (file:line)

- [test_s8b_floor_attempt_launcher.py:1034](/work/1/SFC/tanab/izanagi/.codex/worktrees/t1851-c3-fix1/orchestrator/tests/test_s8b_floor_attempt_launcher.py:1034): 局所 planned builder の旧値 `0` を `None` に訂正。
- [test_s8b_floor_attempt_launcher.py:1437](/work/1/SFC/tanab/izanagi/.codex/worktrees/t1851-c3-fix1/orchestrator/tests/test_s8b_floor_attempt_launcher.py:1437): `_v2_terminal_from_opened()` が planned では `None`、retry では `slot_id[3]` の `measurement_ordinal` を生成するよう訂正。
- [test_s8b_floor_attempt_launcher.py:1526](/work/1/SFC/tanab/izanagi/.codex/worktrees/t1851-c3-fix1/orchestrator/tests/test_s8b_floor_attempt_launcher.py:1526): retry 負例用に 2 軸を分離可能にし、`measurement_ordinal=2`、`attempt_ordinal=1` を使用。

## 強度の対照 (負例 2 種の nodeid と、新設か既存かの区別)

いずれも新設です。

- `test_s8b_floor_attempt_launcher.py::test_planned_terminal_rejects_nonnull_retry_ordinal`
  - planned の `None` を recovery 軸の `0` に置換すると、terminal 発行を拒否。
- `test_s8b_floor_attempt_launcher.py::test_retry_terminal_rejects_recovery_ordinal_substitution`
  - retry の正しい値 `2` を `attempt_ordinal=1` に置換すると、terminal 発行を拒否。

両方とも exact reason `campaign_record.retry_ordinal differs from durable identity` を確認します。

## 実走結果 (command と passed/failed の実数)

```text
PYTHONPATH=. python3 orchestrator/tests/test_s8b_floor_attempt_launcher.py
73 passed, 0 failed

PYTHONPATH=. python3 orchestrator/tests/test_s8b_terminal_evidence.py
79 passed, 0 failed

PYTHONPATH=. python3 orchestrator/tests/test_s8b_attempt_registry.py
149 passed, 0 failed
```

## 残った懸念

指定範囲内にはありません。`git diff --check` も通過し、差分は所有 test file だけです。