## 現行挙動と変更後

変更前は、submission receipt が `renameat2(RENAME_NOREPLACE)` で公開され、completion receipt は完成名へ直接 `O_EXCL` 書込みされていました。既存先は拒否しますが、前者は Lustre で `EINVAL`、後者は部分公開の余地がありました。

変更後は submission/completion とも、canonical bytes を完成させた staging を `os.link(..., follow_symlinks=False)` で create-only 公開します。既存先は変更せず `PaperStoryError`、空き先は canonical bytes を公開して staging を撤去します。

## 実装

変更は許可された次の 2 ファイルだけです。

- [paper_story_a1_paired.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2396-author/orchestrator/campaign/paper_story_a1_paired.py:840)
- [test_paper_story_a1_job_contract.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2396-author/orchestrator/tests/test_paper_story_a1_job_contract.py:2310)

`test_paper_story_a1_paired.py`、docs、materialize 系、`submission-failure.json` publisher、一般 `_exclusive_write*` caller は変更していません。`git add`、commit も行っていません。

主な実装内容です。

- `.s-<pid hex>` / `.c-<pid hex>` の kind 分離 staging。
- submission/completion 共通 hard-link publisher。
- 公開済み cleanup では、宛先の存在と staging identity との一致を先に検証。
- 宛先不在・identity 不一致では staging を残して fail-closed。
- cleanup failure を `_PublishedReceiptCleanupError` とし、message に `receipt is already published` を明記。
- v3 submission では同例外時に failure receipt を書かない。
- completion の v2/v3 両 caller を共通 publisher へ変更。
- `link → destination parent fsync → staging unlink → parent fsync` を実装。

A-7 の probe 射程についても、Lustre 一般へ一般化せず、今回の実測 directory・時点に限定して報告しています。

## テストと検査

pytest の実走結果はありません。`tools/run_tests.py` で以下を要求しましたが、すべて `qstat -Q` の socket 作成拒否で rc=16、`child_started=false` となり、pytest child は起動しませんでした。

焦点範囲：

- `test_m1_submission_receipt_is_complete_before_final_path_is_visible`
- `test_m2_submission_receipt_publish_is_no_replace`
- `test_completion_receipt_publish_boundary_and_no_replace`
- `test_submission_receipt_link_failure_removes_owned_staging`（2 parameter cases）
- `test_submission_receipt_cleanup_preserves_replaced_staging`
- `test_published_receipt_cleanup_preserves_same_inode_after_destination_move`
- `test_receipt_publish_orders_link_fsync_unlink_fsync`
- `test_submit_rejects_foreign_staging_before_intent_and_qsub`
- `test_submit_accepts_clean_evidence_and_staging_namespace`
- `test_submit_accepts_name_max_submission_basename`
- `test_complete_only_issues_completion_receipt_without_materialize`
- `test_v3_published_cleanup_failure_does_not_write_failure_receipt`

制約メタテスト範囲：

- `test_plain_runner_coverage.py::test_every_test_file_is_self_runnable_or_allowlisted`
- `test_plain_runner_coverage.py::test_allowlist_has_no_stale_or_self_runnable_entries`
- `test_plain_runner_coverage.py::test_this_metatest_is_itself_self_runnable`

追加した `test_published_receipt_cleanup_requires_destination_identity` も実装済み・未実走です。

通過した静的検査：

- production/test の `compile(..., "exec")`
- production/test module import
- `git diff --check`
- test 関数名重複検査
- U+0300〜U+036F の diff 混入検査
- 変更 path 検査

期待赤集合は空です。観測された既知のテスト赤もありませんが、pytest 未実走のため緑とは申告しません。

## 変異 owner

- M-01: `test_published_receipt_cleanup_requires_destination_identity`
- M-02: `test_submission_receipt_cleanup_preserves_replaced_staging`
- M-03: `test_receipt_publish_orders_link_fsync_unlink_fsync`
- M-04: `test_receipt_publish_orders_link_fsync_unlink_fsync`
- M-05: `test_m2_submission_receipt_publish_is_no_replace`
- M-06: `test_completion_receipt_publish_boundary_and_no_replace`
- M-07: `test_completion_receipt_publish_boundary_and_no_replace`
- M-08: `test_m2_submission_receipt_publish_is_no_replace`
- M-09: `test_v3_published_cleanup_failure_does_not_write_failure_receipt`

A-1 指定の同一 inode 移動負例は、別途 `test_published_receipt_cleanup_preserves_same_inode_after_destination_move` が所有します。

## 波及の静的列挙

Production caller：

- `_run_submit_v3`
- `run_submit`
- `_run_complete_v3`
- `run_complete`

共有 fixture：

- `_submit_cli_fixture`
- `_stub_successful_submit`
- `_v3_submit_cli_fixture`
- `_v3_visibility`
- `_acquisition`
- `_noncertifying_bundle`
- `_scheduler_completion_fixture`

所有外 consumer/test：

- `orchestrator/campaign/materializer_admission.py`
- `tools/pegasus/paper_story_a1_paired.sh`
- `test_campaign.py`
- `test_ccbench_spawn_sites.py`
- `test_hooks.py`
- `test_official_perf_closure.py`
- `test_p3_build_authority_cli.py`
- `test_p3_exploration_namespace.py`
- `test_paper_story_a1_headline.py`
- `test_paper_story_a1_paired.py`

## 総括

A-1〜A-6、D-1〜D-8 はすべて `partial（実装済み・pytest 未実走）` です。未実施の実装項目はありません。既知の赤は残していませんが、Pegasus dispatch infrastructure の rc=16 により、親の段 6 で焦点走・consumer 走・全走を実施する必要があります。