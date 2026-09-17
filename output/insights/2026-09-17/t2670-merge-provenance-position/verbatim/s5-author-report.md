## 変更した file と差分の要約 (file:line)

- `tools/dev_wave_wait.py:607,3864`：監査を commit の HEAD pin 取得直後へ移設。契約コメントを追加。cleanup の実処理・監査 argv・診断設定は維持。
- `orchestrator/tests/test_dev_wave_wait.py:757,6284–8740`：既存期待列を更新し、実 git 負例を追加。

差分は指定2ファイルのみ、170行追加・68行削除。作業リポジトリの commit・docs 編集はしていません。

## 現行と変更後の受理・拒否挙動 (各 2 文)

現行は main にだけ存在する provenance 違反を見逃して受入 command を投入します。wave の既存履歴や merge message の違反は拒否します。

変更後は main にだけ存在する違反 commit を持つ取り込みを、commit 後・受入投入前に拒否します。merge commit を保持して所有 lease を解放し、それ以外の受理条件を維持します。

## 既存 test の更新一覧 (test 名 / 変えた期待 / 維持した主張)

以下の名前には `test_` を前置します。

| test 名 | 変えた期待 | 維持した主張 |
|---|---|---|
| `postclaim_merge_without_implementation_conflict_accepts_self_report` | history を commit 後へ | self-report 成功・投入 |
| `owned_path_prefix_is_not_overlap_and_reaches_submission` | 同上 | prefix 非重複・投入1回 |
| `missing_owned_path_skips_diff_warns_and_reaches_submission` | 同上 | diff 不在・警告・成功 |
| `merge_sequence_and_postcheck_are_exact` | history を pin 後へ | mutation 列・禁止 option・lease 表示・queue 消費 |
| `nonzero_stage_blocks_submission_and_releases` | 全14段の期待順序、history 赤の abort 不在 | rc・stage・投入不在・release・完全イベント一致 |
| `postmerge_tracked_dirty_blocks_submission_and_releases` | history を pin 後へ | dirty 拒否・投入不在・release |
| `malformed_ai_agent_message_fails_provenance_before_commit` | merge 側 history 期待を削除 | commit 不在・abort・release |
| `merge_history_provenance_failure_blocks_submission_releases_and_returns_reason` | commit・pin 通過、abort 不在 | 理由全文・source_rc・投入0・release1回 |
| `merge_history_provenance_unexpected_rc_fails_closed` | commit 済み・abort 不在を追加 | source_rc=29・fail closed |
| `committed_message_without_ai_agent_never_runs_acceptance` | history を pin 後へ | message-postcheck 拒否・投入不在・release |

連続登録 helper `_provenance` を解消し、3利用箇所を分離しました。

## 新規負例 test (fixture の構成・各 assert・timeout)

`test_real_git_main_only_history_violation_blocks_acceptance_after_commit`（8636行）を追加しました。

- 実 git fixture、新規到達性 checker、repo 外の SHA・trace・runner 計数ファイルを使用。
- claim 前 history は緑、message は緑、commit 後 history は赤を trace で確認。
- rc=70、stage、source_rc=1、違反理由、runner 投入0回を確認。
- 監査時 lease 存在・終了時不在、開始 tip と main tip を親とする2親 merge、違反 SHA の開始時非到達・終了時到達を確認。
- MERGE_HEAD・receipt・log 不在、tracked clean を確認。
- 新規 subprocess 呼び出しに `timeout=120`。SHA は fixture 内で生成。

## 直接呼び出し検査の結果 (DIRECT_CALL / 反実仮想の赤化 / 復元確認)

**DIRECT_CALL：27ケース成功。** 対象 nodeid はすべて `orchestrator/tests/test_dev_wave_wait.py::` 配下で、上表10関数（段別テストは全14ケース）、新規負例、および以下です。

- `test_postclaim_merge_provenance_failure_rejects_self_report`
- `test_positive_postmerge_behind_count_blocks_only_submission`
- `test_created_commit_identity_change_blocks_submission`

結果ログ：[t2670-direct.log](/tmp/t2670-direct.log)。

M2（監査呼び出し除去）では、新規負例の **runner 計数0の assertion が赤化**。実際の計数は1でした。実装をバイト単位で復元し、新規負例の再成功と `git diff --check` を確認しました。

pytest 全体と M0・M1・M3〜M5 は未実走です。

## meta-test と consumer への波及 (静的列挙)

指定の `grep -rn "test_dev_wave_wait" orchestrator/tests tools` と追加検索で確認しました。

- `test_plain_runner_coverage.py`：既存ファイルは allowlist 登録済み。ファイル新設・改名なし。
- `test_fold_gate_nodes_contract.py`：禁止 launcher payload の検査対象は spool test の到達関数群。今回の新規負例は対象外。
- `test_check_docs.py`：waiter consumer pin は docs の契約を検査。今回のテスト本文・名前には依存しない。
- `test_pytest_collection_config.py`：除外表の検査に新規 node を追加する必要なし。
- `test_dev_wave_wait_compute.py`：waiter を独立 import。変更した acceptance 経路への依存なし。
- `test_run_tests_shards.py`：shard 定数は不変。未知 nodeid の既定コストがあり、duration ledger 更新は不要。
- 所有外の land・issuer は waiter bytes を参照するため束縛値は変化するが、固定 hash の更新箇所なし。
- 共有 fixture `_real_waiter_repo`・`_write_exact_runner`・routing fake は変更なし。land／resume-boundary の実 git consumer は未実走。

## 総括

指定2ファイルの実装を完了しました。直接呼び出し27ケースと監査除去による意味的な赤化を確認し、変異は復元済みです。pytest／consumer 全体は **実装済み・未実走**として親へ引き継ぎます。