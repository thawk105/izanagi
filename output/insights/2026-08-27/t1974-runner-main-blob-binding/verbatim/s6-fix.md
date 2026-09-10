実装済み・未実走です。pytest、checker、変異 matrix は起動していません。

主な修正:

- [dispatcher writer](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1974-runner-main-blob-binding/tools/pegasus/dispatch_compute.py:928) を compact canonical JSON 1 行と末尾改行へ変更。書き込み前に `fstat` と `S_ISFIFO` を検査し、閉鎖 fd と非 pipe fd を拒否します。
- [writer/parser seam test](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1974-runner-main-blob-binding/orchestrator/tests/test_acceptance_launcher.py:604) を指定 node 名で追加しました。
- [resume gate E2E](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1974-runner-main-blob-binding/orchestrator/tests/test_resume_gate_acceptance_boundary.py:273) に K=1 と synthetic runner の正規申告を追加。rc 0、runner 1 回、受領証成功の期待は維持しています。同 file に同型 node はありませんでした。
- [M9 実 Git test](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1974-runner-main-blob-binding/orchestrator/tests/test_pegasus_dispatch_compute.py:4169) は main/tip bytes が異なる repo と実 subprocess を使用します。
- [bound `_job_run` E2E](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1974-runner-main-blob-binding/orchestrator/tests/test_pegasus_dispatch_compute.py:4223) は実 request、実 envelope、実 main blob child を通し、result の申告 object を exact 比較します。

### 所見対応表

| 所見 | 状態 | 理由 |
|---|---|---|
| A-1 | partial | fd の再利用事故は FIFO 検査で閉鎖。fork worker が fd を継承する構造的残余は裁定どおり段階 P では残る。 |
| A-2 | closed | resume E2E に明示 K=1 と canonical 申告を追加し、成功期待を維持。 |
| A-3 | closed | dispatcher writer を 1 行 canonical 化し、launcher parser 直結 seam を追加。 |
| A-4 | 不採用 | 恒真な長さ条件は裁定どおり防御的重複として残置。 |
| B-1 | closed | M4 を index 検査全削除へ再照準し、正常 K/digest/nonce と `[0,0,2]` だけで拒否を観測。 |
| B-2 | closed | M9 を pathname 再 hash へ再照準し、main/tip が異なる実 repo で検出。 |
| B-3 | closed | M7 は runner 起動回数、M11 は scheduler 未到達を観測し、例外文言依存を除去。 |
| B-4 | closed | 完全な bound request を `_job_run` に通す E2E を追加。 |
| B-5 | closed | A-2 と同じ resume E2E 更新で解消。 |

### 変異対応

| 変異 | 赤にする test | 単一理由 |
|---|---|---|
| M1 | `test_binding_reports_reject_extra_count` | 現行制御フローでは件数違反だけが拒否層。 |
| M2 | `test_binding_report_digest_mismatch_is_rejected` | digest だけ不一致。 |
| M3 | `test_binding_report_nonce_mismatch_is_rejected` | nonce だけ不一致。 |
| M4 | `test_binding_reports_require_exact_index_multiset[dup]` | 件数と他 field は正常で index だけ `[0,0,2]`。 |
| M5 | `test_binding_enforcement_precedes_receipt` | 不正申告時の受領証生成順だけを観測。 |
| M6 | `test_launcher_owns_k_from_environment_not_reports` | 環境 K=3 と自己申告 K=2 の authority 差だけを観測。 |
| M7 | `test_unset_shard_env_fails_closed_before_runner` | 未設定時に runner が起動したかを call list で観測。 |
| M8 | `test_bound_child_executes_main_blob_not_worktree` | main/tip の実行結果だけを観測。M9 の pathname hash は fixture 内で分離。 |
| M9 | `test_bound_child_reports_digest_of_executed_buffer` | 実行 input は同義、main/tip bytes の hash 差だけを観測。 |
| M10 | `test_manifest_present_adds_runner_binding_to_request` | 完全 manifest 時の request binding 有無を観測。 |
| M11 | `test_partial_manifest_environment_fails_closed` | 1 key 部分 manifest が scheduler へ到達したかを観測。 |
| M12 | `test_binding_applies_only_to_tests_task` | 非 tests task への binding 適用だけを観測。 |
| M13 | `test_binding_report_writer_output_parses_in_launcher` | dispatcher writer の framing だけを launcher parser で検査。 |

単一理由性は静的には成立していますが、変異本走による確認は未実施です。

### 波及可能性

- `tools/run_tests.py` と `tools/acceptance_shards.py`: caller と fork worker。後者の fd 継承が既知の構造的残余です。
- `tools/dev_wave_wait.py`: K 注入と launcher 起動元。production は未変更で、共有 synthetic fixture は既に canonical 申告対応済みです。
- `tools/dev_wave_land.py` と `orchestrator/tests/test_dev_wave_land.py`: v5 受領証 consumer。受領証 schema と field 集合は変更していません。
- `test_run_tests_preflight.py`、`test_mutation_harness.py`: binding 無しの synthetic request は従来の unbound fallback 対象です。
- `test_plain_runner_coverage.py`、`test_pytest_collection_config.py`、`test_check_docs.py`、`test_site_policy.py`、`test_fold_gate_nodes_contract.py`: file 集合、import、source scan の波及候補です。
- `_Scheduler` と `_write_exact_runner` の共有 fixture、および resume 固有 runner は新 optional report に対応済みです。

6 対象ファイルの compile、`git diff --check`、禁止結合文字走査は完了しました。`_ENV_PROJECTION_FIELDS`、`TASKS[*].env_allowlist`、`result.json` の `O_EXCL` は不変です。git add、commit は実行していません。

作業ツリーには親所有の既存 [docs/pegasus-runbook.md](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1974-runner-main-blob-binding/docs/pegasus-runbook.md) 差分がありますが、この fix では触れていません。

## 総括

- canonical writer、FIFO fd 検査、resume E2E、bound `_job_run` E2E を実装済みです。
- M4、M7、M9、M11、M13 を訂正後の変異へ再照準しました。
- fork worker の fd 継承は裁定どおり段階 P の残余です。
- pytest、checker、変異 matrix は未実走です。