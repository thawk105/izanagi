## 実装

- [submit_certify.sh](/work/1/SFC/tanab/izanagi/.codex/worktrees/t583-author/tools/pegasus/submit_certify.sh:88)
  - Git common dir から repo 外 root を導出し、`mkdir -p`。
  - nonce 付き scheduler stdout/stderr の file path を `qsub -o/-e` へ追加。
  - 指定された2ブロック以外は byte-exact で変更していません。
- [test_pegasus_calibration_workload.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/t583-author/orchestrator/tests/test_pegasus_calibration_workload.py:228)
  - 指定された正例・負例を追加。
  - `tmp_path` 内の clean Git fixture で script を実走し、`qsub command:` を `shlex.split` して検査します。
  - 実運用 evidence directory は使用しません。
- `git add`、commit、branch 操作、docs 編集はしていません。変更は上記2ファイルだけです。

## 検査結果

pytest 本体が実走した nodeid はありません。すべて `tools/run_tests.py` が計算ノード dispatch 前の `qstat -Q` で rc=16となり、`child_started=false` でした。したがって以下は「実装済み・未実走」です。

- 新設2 nodeid
  - `test_submit_dry_run_passes_scheduler_file_paths_to_qsub`
  - `test_submit_dry_run_keeps_scheduler_output_outside_the_repository`
- 同 test file 全体
- 関連 consumer 4 nodeid
  - `test_shell_syntax[submit_certify.sh]`
  - `test_certify_calibration_policy_check_rejects_symlinks[submit_certify.sh]`
  - `test_certify_keeps_default_modules_and_uses_system_toolchain`
  - `test_submit_dry_run_does_not_resolve_cluster_commands`
- file 集合を列挙する meta-test
  - `test_permanent_exclusion_table_has_no_other_verifier_or_oracle_tests`

代替の `/tmp` clean fixture dry-run smoke は rc=0で、argv、絶対 file path、nonce一致、期待 root、repo/common repo 外配置を確認しました。fixture は削除済みです。

静的検査はすべて成功しています。

- `bash -n`
- Python AST parse
- `git diff --check`
- 禁止結合文字なし
- `python3 tools/check_codex_agents.py`
- `python3 tools/check_docs.py`

## 受理・拒否挙動

変更前の CLI whitelist、RRATIO検査、legacy env拒否、missing policy/script拒否、dirty gate、preflight失敗時停止は維持されています。変更後も新しい CLI、containment gate、専用 error、realpath/symlink検査はありません。

有効な clean submission の受理条件は維持し、構築される qsub argv に repo 外 `-o/-e` が加わります。新規に必要となる common-dir 解決または `mkdir -p` が失敗した場合だけ、既存の `set -Eeuo pipefail` により停止します。

## 波及面と残る risk

- 実行 caller は README/runbook等の手動投入経路です。`submit_floor.sh` の参照は出典コメントであり、直接呼び出しではありません。
- 共有 fixture は変更していません。`test_pegasus_tools.py` の clean fixture は既存 consumerとして影響候補です。
- `test_hooks.py`、`test_check_docs.py`、admission registry、acceptance duration ledger が静的 consumerです。新 nodeid の所要時間は未実測のため ledgerへ合成していません。
- 裁定どおり containment gate がないため、特殊な separate-git-dir topologyでは導出先が repo 内になり得ます。
- dry-runではNQSVの実受理・leaf書込みや、qsub非実行の因果は証明していません。

## 総括

- 実装: repo 外 scheduler file pathを `qsub -o/-e` へ追加。
- テスト: 指定の正例・負例を実装。
- 実走: `/tmp` smokeと静的 checkerは成功、pytestはdispatch障害で未実走。
- 残るrisk: 特殊Git配置、NQSV実動作、未計測ledger node。