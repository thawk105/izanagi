許可された 5 file に実装済みです。pytest は指示どおり未実走です。ただし、許可外の既存 E2E 1 本が新契約と衝突するため、着地前の対応が必要です。

### 変更内容

- [tools/acceptance_launcher.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1974-runner-main-blob-binding/tools/acceptance_launcher.py:136)
  - shard 数を環境の `"1"`、`"2"`、`"3"` だけから確定。
  - nonce と継承 write-fd を生成し、fd・nonce・tested main の 3 key だけを runner 環境へ追加。
  - canonical JSON 申告を読み、件数、index、nonce、main、digest を執行。
  - outcome 書き込み後、completion と受領証の前に申告を検査。
  - 受領証 field と `_ENV_PROJECTION_FIELDS` は不変。

- [tools/pegasus/dispatch_compute.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1974-runner-main-blob-binding/tools/pegasus/dispatch_compute.py:777)
  - 3 key 全欠落は従来互換、部分欠落は qsub 前に拒否。
  - `tests` かつ完全な binding の場合だけ request に revision、nonce、K、index を追加。
  - compute 側で `git cat-file blob` を一度実行し、同じ buffer を hash と stdin 実行に使用。
  - compute result の optional fieldから検証済み申告を login 側 fd へ書き込み。
  - pathname fallback、`stdin=DEVNULL`、`result.json` の `O_EXCL` を維持。

- [test_acceptance_launcher.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1974-runner-main-blob-binding/orchestrator/tests/test_acceptance_launcher.py:412)
  - K=3 の P1、M1からM7、main mismatch、空・不正 shard 値を追加。
  - 既存受領証の exact bytes は変更せず、正規 fd 申告を追加。

- [test_pegasus_dispatch_compute.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1974-runner-main-blob-binding/orchestrator/tests/test_pegasus_dispatch_compute.py:4092)
  - 実 Git repo で main bytes のみを実行する E2E。
  - P2、M8からM12、intent index と argv index の不一致検査を追加。
  - fake scheduler の result に optional binding report を追加。

- [test_dev_wave_wait.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1974-runner-main-blob-binding/orchestrator/tests/test_dev_wave_wait.py:1041)
  - synthetic runner が継承 fd へ正規申告を書くよう更新。
  -指定された実 Git E2E 4 本へ明示 K=1 を設定し、成功期待を維持。

### 受理集合の差

変更前は shard 環境未設定、申告なし、非 dispatch の成功でも受領証を生成できました。

変更後は次を拒否します。

- shard 環境が未設定、空、不正。
- 申告不足、過剰、重複 index、nonce・main・digest 不一致。
- binding 環境 3 key の部分設定。
- authoritative な local 実行など、dispatch 申告が出ない走行。

3 key が全て無い通常 dispatcher は従来の pathname 起動を維持します。完全な binding がある `tests` dispatch だけが main blob stdin 実行になります。

### 変異対応

- M1: `test_binding_reports_reject_extra_count`
- M2: `test_binding_report_digest_mismatch_is_rejected`
- M3: `test_binding_report_nonce_mismatch_is_rejected`
- M4: `test_binding_reports_require_exact_index_multiset[dup]`
- M5: `test_binding_enforcement_precedes_receipt`
- M6: `test_launcher_owns_k_from_environment_not_reports`
- M7: `test_unset_shard_env_fails_closed_before_runner`
- M8: `test_bound_child_executes_main_blob_not_worktree`
- M9: `test_bound_child_reports_digest_of_executed_buffer`
- M10: `test_manifest_present_adds_runner_binding_to_request`
- M11: `test_partial_manifest_environment_fails_closed`
- M12: `test_binding_applies_only_to_tests_task`

### 静的検査と波及

- 変更 5 file の AST、禁止結合文字、`git diff --check` は通過。
- `check_docs._dispatch_inventory_from_source` は既存 `TASKS` 4 項目を exact に抽出し、finding は空。`TASKS[*].env_allowlist` と child script literal は不変。
- 受領証 consumer の `dev_wave_land`、optional request を読む `mutation_harness`、manifest 全欠落の dispatcher caller は静的には互換。
- file 集合メタテストとして [test_plain_runner_coverage.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1974-runner-main-blob-binding/orchestrator/tests/test_plain_runner_coverage.py:60) が存在します。親の焦点走対象です。
- pytest、全 checker、変異 matrix は未実走です。git add、commit は実行していません。

許可外の [test_resume_gate_acceptance_boundary.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1974-runner-main-blob-binding/orchestrator/tests/test_resume_gate_acceptance_boundary.py:248) も、申告なしで受領証成功を期待しています。新契約では赤になりますが、編集許可外かつ例外対象外なので変更せず停止しました。親による scope 裁定または fixture 更新が必要です。

## 総括

- main blob の compute runner 実行と fd 申告執行を実装済みです。
- shard env、受領証 schema、env allowlist、`O_EXCL` は変更していません。
- M1からM12と P1、P2を実装済み・未実走です。
- 最大の未確定点は、許可外の resume E2E 1 本が旧契約を固定していることです。