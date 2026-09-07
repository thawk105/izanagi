## 変更結果

[test_paper_story_a1_job_contract.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2396-author/orchestrator/tests/test_paper_story_a1_job_contract.py:2643) のみを編集しました。production 実装、docs、schema、canonical bytes は変更していません。`git add`・commit も行っていません。

| 所見 | 対応 | 判定 |
|---|---|---|
| must-fix 1 / A-2・B-2 | `os.link` 1 回、専用例外、staging bytes、宛先不在を直接検査。通常成功例も追加 | partial（実装済み・未実走） |
| must-fix 2 / B-1 | v3 policy の `run_complete` から公開点へ到達し、link 直前の canonical staging と宛先不在を観測 | partial（実装済み・未実走） |
| must-fix 3 / B-3 | 宛先だけが消えた負例を追加。既存 identity 不一致テストは維持 | partial（実装済み・未実走） |

refuted と裁定された所見には手を加えていません。

## 検査

静的検査結果:

- `py_compile`：対象 2 ファイルとも成功
- `git diff --check`：成功
- top-level test 名：88 件、重複なし
- U+0300〜U+036F：対象 2 ファイルに該当なし

pytest は次の範囲を `tools/run_tests.py` 経由で試しましたが、すべて rc=16、test child 未起動でした。

- 焦点 4 nodeid:
  - `::test_published_receipt_cleanup_preserves_same_inode_after_destination_move`
  - `::test_published_receipt_cleanup_preserves_staging_when_destination_disappears`
  - `::test_published_receipt_cleanup_requires_destination_identity`
  - `::test_v3_complete_publishes_canonical_group_receipt_through_link_boundary`
- 同一 inode nodeid の単独再試行
- `test_paper_story_a1_job_contract.py` 全体
- 同ファイルの `--collect-only`
- 制約 meta-test:
  - `test_plain_runner_coverage.py::test_every_test_file_is_self_runnable_or_allowlisted`
  - `test_plain_runner_coverage.py::test_allowlist_has_no_stale_or_self_runnable_entries`
  - `test_acceptance_schedule_order.py::test_g5_real_ledger_covers_at_least_90_percent_of_real_collection`

原因は計算ノード dispatch の `qstat -Q` preflight におけるアカウント認証エラーです。テスト失敗は観測されておらず、緑も申告しません。

## 静的な波及列挙

production の参照グラフは次のままです。

- `_receipt_staging_path` → `_publish_receipt`、`_run_submit_v3`、`run_submit`
- `_remove_receipt_staging` → `_publish_receipt` のみ
- `_publish_receipt` → submission/completion wrapper
- `_publish_submission_receipt` → v2/v3 submit
- `_publish_completion_receipt` → v2/v3 completion
- `_PublishedReceiptCleanupError` → publisher の送出と v3 submit の専用 catch
- `run_complete` → CLI `main`

所有外で波及し得る箇所:

- `test_paper_story_a1_paired.py::test_run_complete_uses_raw_sidecar_gate_then_enables_final_view`
- 同ファイルの completion receipt／`consume_non_certifying_observation` consumer 群
- 共有 fixture `_submit_cli_fixture`、`_scheduler_completion_fixture`、`_v3_submit_cli_fixture`。今回は `_v3_submit_cli_fixture` を再利用し、fixture 自体は未変更

## 総括

must-fix 1〜3 はすべて修正実装済みですが、pytest child が一度も起動できなかったため判定は全件 `partial` です。実走済みテスト nodeid はありません。静的検査は成功しています。残した既知のテスト赤はありませんが、焦点・全ファイル・meta-test は dispatch 認証障害により未実走です。