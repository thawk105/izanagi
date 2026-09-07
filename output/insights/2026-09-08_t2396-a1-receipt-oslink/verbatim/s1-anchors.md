# 段 1 変更面アンカー表 (commit 0e02169b0 の実 file:line)

repo root = `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2396-a1-receipt-oslink`

## 変更対象 (production)

| anchor | 現状 | 本 wave での扱い |
|---|---|---|
| `orchestrator/campaign/paper_story_a1_paired.py:874-890` `_publish_submission_receipt` | staging を書き `_renameat2_directory(staging, path, _RENAME_NOREPLACE)` で公開。失敗時だけ staging を撤去 | **変更 (必須)。** `os.link` 公開 + 成功後の staging 撤去 |
| 同 `:4259-4261` `_run_complete_v3` の completion 書込み | `_exclusive_write(completion_path, completion)` で完成名へ直接書く | **(P1) 変更予定。** staging + `os.link` |
| 同 `:4349-4351` `run_complete` の completion 書込み | 同上 | **(P1) 変更予定。** staging + `os.link` |

## 変更しない (棚卸し対象・参照のみ)

| anchor | 内容 |
|---|---|
| `orchestrator/campaign/paper_story_a1_paired.py:8090-8126` `_observe_materialization_publish` | 公開先と同 FS で `RENAME_NOREPLACE` を 1 回試し EINVAL なら fallback を選ぶ (**directory** publish) |
| 同 `:8044-8052` `_publish_staging_noreplace` / `:8155-8186` `_publish_staging_after_einval` | materialize の 2 経路。directory なので `os.link` 不可 |
| 同 `:8256-8309` `_publish_materialization_bundle` | staging directory を作り `_publish_complete_staging` で公開 |
| 同 `:3037-3060` `_write_v3_submission_failure` | `receipts/submission-failure.json` を `_exclusive_write` で直接書く (**(P3)**) |
| 同 `:393-396` `PUBLISH_RENAME_NOREPLACE` / `PUBLISH_EINVAL_FALLBACK` / `_RENAME_DEFAULT` / `_RENAME_NOREPLACE` | materialize 側が使い続ける。削除しない |
| 同 `:8019-8042` `_renameat2_directory` | materialize が使い続ける。削除しない |

## 再利用する既存部品 (新機構を作らない)

| anchor | 内容 |
|---|---|
| `orchestrator/campaign/paper_story_a1_paired.py:796-814` `_exclusive_write_bytes` | `O_WRONLY\|O_CREAT\|O_EXCL\|O_NOFOLLOW` 0o600 + fsync、`(st_dev, st_ino)` を返す |
| 同 `:835-846` `_submission_receipt_staging_path` | `.<stem>.s-<pid hex>` を basename 長予算内で作る |
| 同 `:848-872` `_remove_submission_receipt_staging` | identity 照合つき unlink + 親 dir fsync |
| 同 `:816-833` `_exclusive_write` | create-only の直接書込み (完成名へ直書き) |

## repo 内の os.link 先例 (D1732 が言う 8 箇所ほか)

`orchestrator/campaign/create_only_store.py:207` (dir_fd + `follow_symlinks=False`、`FileExistsError` を
既存読取りへ分岐)、`orchestrator/qualification/atomic_publish.py:100`、
`orchestrator/campaign/s8b_attempt_registry.py:749`、`orchestrator/campaign/s8b_selector_freeze.py:922`、
`orchestrator/campaign/s8b_budget.py:145`、`orchestrator/campaign/layout.py:513`、
`orchestrator/campaign/t810_validator.py:1300,1587`、`orchestrator/campaign/p3_s4_loop.py:1903`。
**link+unlink の完成形の先例:** `orchestrator/calibrator/cli.py:334-353` `_rename_noreplace`
(`EEXIST` を publish-collision、`os.link` 後に `os.unlink(source)`)。

## 影響を受ける既存テスト (弱めずに置換・維持する)

| anchor | 内容 |
|---|---|
| `orchestrator/tests/test_paper_story_a1_job_contract.py:2310` `test_m1_submission_receipt_is_complete_before_final_path_is_visible` | 公開前に完成 bytes が最終 path に見えないこと。`_renameat2_directory` を monkeypatch |
| 同 `:2346` `test_m2_submission_receipt_publish_is_no_replace` | 既存先への公開が拒否され、`clean` へは通る |
| 同 `:2500` `test_submission_receipt_rename_failure_removes_owned_staging` | 公開失敗時に自分の staging を撤去 |
| 同 `:2529` `test_submission_receipt_cleanup_preserves_replaced_staging` | 差し替えられた staging を消さない (identity 検査) |
| 同 `:2559` `test_submit_rejects_foreign_staging_before_intent_and_qsub` | 他人の staging が居るとき投入前に拒否 |
| 同 `:2593` `test_submit_accepts_clean_evidence_and_staging_namespace` | 正例 |
| 同 `:2620` `test_submit_accepts_name_max_submission_basename` | basename 長の境界 |
| `orchestrator/tests/test_paper_story_a1_paired.py:2260-2400` | **materialize 側**の probe/fallback 検査。本 wave では変えない |

## 焦点走の consumer 集合 (DW-O26、production module 名で引いた実測)

`orchestrator/campaign/materializer_admission.py`、`orchestrator/tests/test_campaign.py`、
`test_ccbench_spawn_sites.py`、`test_hooks.py`、`test_official_perf_closure.py`、
`test_p3_build_authority_cli.py`、`test_p3_exploration_namespace.py`、
`test_paper_story_a1_headline.py`、`test_paper_story_a1_job_contract.py`、
`test_paper_story_a1_paired.py`。

## pin 閉包 (DW-O09、`git grep` 実測)

`paper_story_a1_paired.py` を bytes で pin する golden は **無い**
(`test_legacy_frozen_bytes_have_independent_literal_goldens` の literal 一覧に本 file は入っていない —
入っているのは `paper_story_a1_headline.py` 系)。受領証は durable base 上の runtime 成果物で、
repo 内の凍結成果物ではない。公開機構を key に張る pin はテストのみ (上表)。
