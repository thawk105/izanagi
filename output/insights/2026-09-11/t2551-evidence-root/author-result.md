## 総括

T-2551は**実装済み・未実走**です。所有2ファイルのみ編集し、docs編集・commitはしていません。

- productionはcanonical化直後の再export **1行**を追加。
- 既存fixtureで相対・絶対pathを入力し、repoへのcwd変更後もPythonの環境値・解決先・実書込先が同じcanonical directoryになることを検証。
- scheduler/build/driver本体は模擬。対象のshell path変換は実物です。
- 既存拒否条件、CMAKE_PREFIX_PATH exact 3行、correctness期待は維持しました。

追加nodeid：

```text
orchestrator/tests/test_p3_s4_loop_job_contract.py::test_evidence_root_reaches_actual_job_driver_as_canonical_path[relative]
orchestrator/tests/test_p3_s4_loop_job_contract.py::test_evidence_root_reaches_actual_job_driver_as_canonical_path[absolute]
```

検証は`tools/run_tests.py`経由で契約テストファイル全体を指定しましたが、`qstat -Q preflight rc=1`によりrunnerはrc=16。**テスト起動0件**です。`git diff --check`は成功しました。

静的に確認した波及先：

- consumer：`orchestrator/campaign/p3_s4_loop.py`、`test_p3_s4_loop.py`
- 分類契約：`admission_registry.json`、`test_hooks.py`
- node管理：`acceptance_duration_ledger.json`、collection制約
- fixture共有：同ファイル内の既存K2正常系2テスト。所有外の共有fixture変更なし。

焦点・全走と事前登録済みM1変異の確認は親へ引き継ぎます。