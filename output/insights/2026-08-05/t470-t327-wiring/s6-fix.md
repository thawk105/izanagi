実装と関連テストを更新しました。commit・stage は行っていません。禁止対象および `docs/` は未編集です。

| 所見 | 状態 | 対応 |
|---|---|---|
| F1 | partial（実装済み・未実走） | report/run-start の admission 完全一致と acceptance 側再導出を追加 |
| F2 | partial（実装済み・未実走） | manifest・registry・lifecycle prefix・report・journal の再 hash と各改変テストを追加 |
| F3 | partial（実装済み・未実走） | lifecycle を byte prefix 長＋prefix hash 束縛へ変更。後続 append 正例を追加 |
| F4 | partial（実装済み・未実走） | start 後の例外を indeterminate terminal 化。terminal 書込失敗と再走拒否をテスト |
| F5 | partial（実装済み・未実走） | lifecycle の Git 履歴 strict-prefix 検査と削除再作成・改変 revert 負例を追加 |
| F6 | partial（実装済み・未実走） | finish admission と lifecycle token を使用時に再導出・再照合 |
| F7 | partial（実装済み・未実走） | Layer 3 に `certifying_input` を追加し launch admission から exact 投影 |
| F8 | partial（実装済み・未実走） | v3 reader は新 field 欠落を非認証として受理、generator は常時出力 |
| F9 | partial（実装済み・未実走） | public `run_trial()` scope 内で `_run_workload()` の T-276 検査を復元 |
| F10 | partial（実装済み・未実走） | m04 direct 呼出、m07 spy、m12 reason 分離、m15 validator 分離を追加 |
| F11 | partial（実装済み・未実走） | 恒真の nodeid 文字列 meta-test を削除 |
| F12 | partial（実装済み・未実走） | `test_s8c_acceptance_receipt.py` を README allowlist に追加 |

静的検査結果:

- `py_compile`: 対象 production 5本、関連 test 5本に成功
- `git diff --check`: 成功
- `tools/check_codex_agents.py`: 成功
- `tools/check_docs.py`: 成功

計算ノード実測は以下の6ファイルを対象に試行しましたが、dispatch 前の `qstat -Q` が `NQSconnect ... errno: 1` で失敗し、`tools/run_tests.py` は `rc=16` でした。実行済み nodeid は0件です。

- `test_trial_registry.py`
- `test_p3_autonomous_workload_trial.py`
- `test_s8c_acceptance_receipt.py`
- `test_layer3_report.py`
- `test_autonomous_trial_completeness.py`
- `test_plain_runner_coverage.py`

静的な波及候補は `test_campaign.py`、`test_claude_transport.py`、`test_p3_s4_loop_trigger_gating.py`、`test_role_session_isolation.py`、`test_s8c_preregistration_predicates.py`、`test_t126_qualification_artifacts.py` です。変更 API の所有外 production caller と共有 `conftest` fixture は検索上ありません。

## 総括

- closed: 0 / 12
- partial: 12 / 12（すべて実装済み・未実走）
- regressed: 0
- 残る赤の見込み: 静的検査上の既知の赤はありませんが、計算ノード未実走のため潜在的な test failure は未確定です。現在確認できる障害は Pegasus dispatch 基盤の `qstat` 失敗です。