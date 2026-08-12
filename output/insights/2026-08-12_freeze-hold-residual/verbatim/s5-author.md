現行挙動:

- production: `HELD = True` により 21 check ID を保留
- test: env 未設定/空は保留, exact token `explicit-user-command` は解除, その他の非空値は拒否
- 素の runner は pytest collection hook を通らず test 保留を迂回可能

実装 scope:

- [tools/hold_inventory.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-freeze-hold-residual/tools/hold_inventory.py:1)
  - exact 2 層の inventory
  - schema と completeness
  - configured/effective status
  - human/json CLI
  - plain runner と Pegasus allowlist の bypass surface
- [test_hold_inventory.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-freeze-hold-residual/orchestrator/tests/test_hold_inventory.py:1)
  - source 集合との exact equality
  - count/digest
  - `main()` の両 format
  - env 3 状態
  - release literal の独立 pin
  - completeness と過剰保証禁止

検査結果:

- human/json CLI 実起動: 成功
- manual contract probe: 成功
- `check_codex_agents.py`: 成功
- `check_docs.py`: 成功
- `git diff --check`: 成功
- pytest: 実装済み, 未実走
  - 対象: `orchestrator/tests/test_hold_inventory.py` 全 4 nodeid
  - `tools/run_tests.py` で 2 回試行
  - collection 前に `qstat -Q preflight rc=1` で停止
  - login headroom も 0 のため直接 pytest は起動せず
  - 関連 meta-test も未実走

所有外への波及可能性:

- `freeze_verification_hold.py` と `growth_test_holds.py` の台帳変更は inventory 出力へ反映される
- `conftest.py` の env 判定変更は effective status 契約へ影響する
- `dispatch_compute.py` の allowlist 変更は release transport 契約へ影響する
- `test_growth_test_holds_contract.py` と `test_pegasus_dispatch_compute.py::test_tests_task_env_allowlist_is_exact` が関連 consumer test
- raw runner bypass は T-930 の未解決事項として残る

## 総括

dev-wave 段 5 の境界に従い、新規 2 ファイルだけを編集しました。禁止ファイル、docs、既存期待値は未変更で、commit も作成していません。必須 pytest だけは Pegasus 実行基盤の阻害により未実走です。