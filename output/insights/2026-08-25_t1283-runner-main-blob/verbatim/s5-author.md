実装済み・未実走です。指定 4 file だけを変更し、commit、`git add`、docs 編集は行っていません。

### 変更前の挙動

- launcher は tested-tip の runner を直接実行し、実行後も tested-tip だけを再取得していました。tested-main 欠落や main/tip divergence は suite 起動を妨げませんでした。
- land の child-green は tip digest だけを検査し、main/tip runner equality は non-attributable-only にしか適用していませんでした。そのため divergent child-green は受理され、non-attributable divergence は拒否されていました。

### 変更内容

- [tools/acceptance_launcher.py:173](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1283-runner-main-blob/tools/acceptance_launcher.py:173)
  - `_read_runner_blob` を任意 revision 対応に一般化しました。
  - [同 file:436](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1283-runner-main-blob/tools/acceptance_launcher.py:436) で main、tip の順に読み、bytes 不一致なら suite 前に拒否します。
  - main 由来の buffer だけを実行し、実行後 M3 も tested-main を再取得します。
  - `_run_blob` の interpreter は [同 file:216](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1283-runner-main-blob/tools/acceptance_launcher.py:216) の素の `python3` のままです。

- [tools/dev_wave_land.py:1065](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1283-runner-main-blob/tools/dev_wave_land.py:1065)
  - tested-tip と exact tested-main の runner entry を全 verdict で取得します。
  - 双方の blob 型、SHA、object ID equality を共通検査にしました。
  - receipt digest の照合先を main runner blob へ変更しました。
  - [同 file:1093](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1283-runner-main-blob/tools/dev_wave_land.py:1093) 以降の非帰属枝には checker equality だけを残しました。

- [orchestrator/tests/test_acceptance_launcher.py:83](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1283-runner-main-blob/orchestrator/tests/test_acceptance_launcher.py:83)
  - main buffer の object identity、main/tip divergence、双方の欠落を suite 前境界で固定しました。
  - [同 file:224](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1283-runner-main-blob/orchestrator/tests/test_acceptance_launcher.py:224) の M3 を main、tip、main の読取順へ改稿しました。

- [orchestrator/tests/test_dev_wave_land.py:245](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1283-runner-main-blob/orchestrator/tests/test_dev_wave_land.py:245)
  - fixture に `runner_digest_revision` を追加し、既定は従来どおり tip に維持しました。
  - [同 file:1523](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1283-runner-main-blob/orchestrator/tests/test_dev_wave_land.py:1523) 以降で child-green の正負例、main 欠落、一時 Git failure、exact revision lookup を固定しました。
  - divergence 系は tip digest を明示しています。
  - [同 file:1944](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1283-runner-main-blob/orchestrator/tests/test_dev_wave_land.py:1944) の real waiter E2E は runner を main commit に含める互換正例へ直しました。

### 追加・改名 nodeid

以下はすべて未実走です。

- `orchestrator/tests/test_acceptance_launcher.py::test_matching_main_and_tip_runner_blobs_execute_tested_main_source`
- `orchestrator/tests/test_acceptance_launcher.py::test_main_tip_runner_blob_mismatch_is_rejected_before_execution`
- `orchestrator/tests/test_acceptance_launcher.py::test_missing_tested_main_runner_is_rejected_before_execution`
- `orchestrator/tests/test_acceptance_launcher.py::test_missing_tested_tip_runner_is_rejected_before_execution`
- `orchestrator/tests/test_dev_wave_land.py::test_land_rejects_child_green_runner_blob_divergence`（改名）
- `orchestrator/tests/test_dev_wave_land.py::test_land_accepts_child_green_matching_main_and_tip_runner_blobs`
- `orchestrator/tests/test_dev_wave_land.py::test_land_child_green_runner_path_absence_is_permanent_rejection`
- `orchestrator/tests/test_dev_wave_land.py::test_land_child_green_runner_lookup_process_failure_is_retryable`

### 検査状況

`tools/run_tests.py` 経由で焦点 16 nodeid、変更 2 file の収集、次の meta-test 4 nodeidを試行しましたが、すべて rc=16、`child_started=false` でした。

- `test_pytest_collection_config.py::test_repo_pytest_ini_has_no_addopts_and_pins_testpaths`
- `test_pytest_collection_config.py::test_bare_pytest_collection_is_scoped_by_testpaths`
- `test_pytest_collection_config.py::test_ini_testpaths_and_runner_default_target_point_at_the_same_tree`
- `test_acceptance_schedule_order.py::test_g5_real_ledger_covers_at_least_90_percent_of_real_collection`

Pegasus の予約台帳を更新できず dispatch が選ばれ、`qstat -Q` が `EACCTAUTH Unknown user-id` で停止しました。pytest の収集・実行は一件も始まっていないため、緑とは報告しません。

静的検査では次を確認しました。

- 両 test file は AST parse 成功。追加・改名した各 test 定義は一件だけで、top-level 名重複なし。
- `git diff --check` 成功。
- schema v5、27 root field、canonical JSON、`_run_blob` は変更前と AST 同一。
- 揮発する commit SHA は fixture から動的取得し、期待値には固定理由、件数、呼出順だけを使用。
- duration ledger の追加・改名 8 nodeid は未登録ですが、ledger は編集許可外です。被覆 meta-test の実走が必要です。
- tracked 差分は指定 4 file のみ。既存の未追跡 `output/insights/2026-08-25_t1283-runner-main-blob/` は変更していません。

### 静的な波及可能性

- `tools/dev_wave_wait.py` は launcher outcome consumer のままで、main/tip equality の証拠自体は検証しません。
- `test_dev_wave_wait.py` の fake launcher receipt は新 equality の証明にならず、`test_resume_gate_acceptance_boundary.py` は real launcher の回帰対象です。
- `_Repo.request` を共有する land test 全体、already-landed、forward-main、fold、gitlink、複数 wave 系は未実走です。fixture の既定 digest は tip のまま維持しています。
- 過去または未追跡の divergent v5 receipt は新 land で拒否されます。
- claim 後に main の runner が更新された並行 wave は再受入が必要になり得ます。
- forward-main landing tip の runner は今回も receipt の検査対象外です。

## 総括

- tested-main runner を実行し、suite 前に main/tip equality を要求する実装にした。
- land の runner equality を全 verdict 共通へ移した。
- schema、canonical JSON、interpreter、retryable 分類は維持した。
- fixture の既定 tip digestを維持し、divergence 負例だけ明示指定した。
- 指定 4 file 以外は編集せず、commit と index 操作もしていない。
- Pegasus 認証障害により実装済み・未実走であり、親による全走と meta-test 実走が必要。