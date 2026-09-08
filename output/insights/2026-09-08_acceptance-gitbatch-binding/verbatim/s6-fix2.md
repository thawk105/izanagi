## 修正結果

E-01 は **closed** です。

- `_allow_read_only_git` は production の `_GIT_HARDEN` を関数内 import し、`/usr/bin/git` から repo root までの prelude 全体を exact 比較します。
- `-C` の探索を廃止し、位置を固定しました。
- env、caller stack、`-C` の path 解決検査、operation grammar は維持しています。
- `contract_loader_binding` から p3 probe への import はないため循環しません。発行側と許可側の定数を共有し、複製ドリフトを避ける方式を選びました。
- test helper は full argv override に対応し、指定された6負例と production prelude の2正例を検査します。

## 台帳

JUnit 代替走から add-only updater を実行しました。

```text
added=0
skipped_existing=65
excluded_total=0
```

全65 nodeが登録済みだったため、台帳の変更はありません。

## 検査結果

指定範囲の全449 nodeidを実走し、すべて緑です。

- `test_p3_b4_wiring_probe.py::*`: 65 passed
  - 範囲: `test_allow_read_only_git_accepts_exact_batch_loader_argv` から `test_source_and_test_are_the_only_non_output_worktree_changes`
  - `test_actual_main_positive_baseline_all_drivers[base|sort|trigger]` の3 driverを含む
- `test_t671_source_binding.py::*`: 302 passed
- `test_acceptance_schedule_order.py::*`: 79 passed、warning 1件
- `test_plain_runner_coverage.py::*`: 3 passed

`tools/run_tests.py` は dispatch preflight で rc=16となり、`child_started=false` でした。計算ノードには投入されていません。自走 harnessによるJUnit代替走は65 passedです。

## Git差分

```text
orchestrator/campaign/p3_b4_wiring_probe.py    | 15 +++--
orchestrator/tests/test_p3_b4_wiring_probe.py | 83 +++++++++++++++++++++++----
2 files changed, 83 insertions(+), 15 deletions(-)
```

追跡対象の変更は上記2 pathのみです。commitは作成していません。

## 総括

E-01: **closed**。Git preludeをproduction発行形へexact固定しました。  
指定6負例とls-tree／cat-file正例を追加しました。  
焦点走は全449 nodeidが緑です。  
台帳は全node登録済みで変更なし、commitなしです。