## 総括

### 1. 対応表

| 所見 | 判定 | 対応 |
|---|---|---|
| R13 | **partial（実装済み・pytest 未実走）** | pytest を optional 化。fixture と `_run()` が共有する authorization refresh helper を追加。新規 test から必須 `monkeypatch` 引数と `pytest.raises` を除去。素 runner で全 262 test が呼び出され、新規 test は PASS |
| R14 | **partial（実装済み・pytest 未実走）** | worker thread が authority lock を保持し、main thread が fork する形へ修正。pipe/select timeout、timeout 時の kill/wait、worker 解放を実装。authority at-fork callback 欠落の動的変異を KILLED |

既存テストの期待値、production、docs は変更していません。

### 2. 変更ファイルと行数

- [test_campaign.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-activation/orchestrator/tests/test_campaign.py:33): +45 / -25
- [test_env_contract_activation.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-activation/orchestrator/tests/test_env_contract_activation.py:772): +17 / -2
- 合計: +62 / -27
- `conftest.py` は未変更。commit なし。

### 3. 走らせた検査と結果

- 素 runner（必須）:

  `python3 orchestrator/tests/test_campaign.py`

  結果: **247 passed / 6 failed / 9 skipped、rc=1**。R13 の新規 test は PASSし、全262 testが呼出し可能になりました。赤6件は既知の環境依存で、`/tmp/.git` を repository ancestor と判定する5件と、Pegasusログインノードで重い処理を拒否する1件です。

- pytest 不在確認:

  `python3 -S -c '<test_campaign.py を読み、refresh と新規 test を実行>'`

  結果: `PASS plain-no-pytest activation-order`、rc=0。

- R14 正例の直接実行: `PASS plain authority-held-lock-fork`、rc=0。
- authority at-fork callback の登録だけを fresh process で欠落させる動的変異: 15秒で `KILLED authority-at-fork callback omission`。child は kill/wait 済み、親はハングなし。
- AST検査: 262 test、必須引数を持つ test は0件。
- `py_compile`: 成功。
- `git diff --check`: 成功。
- `check_codex_agents.py`: 成功。
- `check_docs.py`: 成功。
- pyflakes: 既存の unused 警告4件のみ。今回の新規警告なし。

### 4. 未実走・未達

pytest targeted run:

`python3 tools/run_tests.py -q orchestrator/tests/test_campaign.py::test_activation_receipt_check_precedes_registry_runtime_site_and_selector_checks orchestrator/tests/test_env_contract_activation.py::test_held_lock_fork_reinitializes_child_cache_without_deadlock`

は `qstat -Q preflight rc=1`、runner rc=16で実行前停止しました。したがってR13/R14とも `closed` とは申告していません。pytest全走、正式な mutation harness 本走も未実走です。

### 5. 親への申し送り

- 計算ノードで対象2ファイルの pytest を再走してください。
- authority callback 欠落変異は、既存 node名 `test_held_lock_fork_reinitializes_child_cache_without_deadlock` のまま検出できます。mutation matrixへ authority側の callback削除変異を追加してください。
- 素 runner の残る6赤は今回の2所見外です。期待値緩和や `/tmp/.git` の削除では解消していません。
- worktree差分は上記2ファイルだけです。production変更は不要です。