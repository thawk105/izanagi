## 実装した内容

- [submit_t1998_balanced_stock_inline.sh](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1998-unit-b/tools/pegasus/submit_t1998_balanced_stock_inline.sh:1) を新設。
  - `balanced` だけを単一 `qsub` で投入。
  - 既存 A-5 job body を無改変で再利用。
  - queue、quota、Pegasus 情報、必須 command、Python 3.10、出力先、衝突を投入前に検査。
  - T-1998 固有 group id と、submitter/job body digestを含む atomic receipt を実装。
- [admission_registry.json](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1998-unit-b/tools/pegasus/admission_registry.json:364) に `local-ok` entry を追加。
- [test_t1998_launcher_contract.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1998-unit-b/orchestrator/tests/test_t1998_launcher_contract.py:19) に契約テスト6件と自走 harnessを追加。
- [test_hooks.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1998-unit-b/orchestrator/tests/test_hooks.py:3093) の分類表、4-field表、local evidence表へ追加。
- [pegasus-runbook.md](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1998-unit-b/docs/pegasus-runbook.md:552) に登録簿投影を追加。

## 実走した検査

- `orchestrator/tests/test_t1998_launcher_contract.py` 自走 harness: 6件成功。
  - `::test_submitter_launches_exactly_one_balanced_workload`
  - `::test_submitter_reuses_the_existing_a5_job_body_and_adds_no_job_body`
  - `::test_qsub_passes_all_five_a5_job_body_bindings`
  - `::test_output_parent_is_existing_absolute_and_outside_every_repo_ancestor`
  - `::test_preflight_and_atomic_receipt_match_the_a5_submission_strength`
  - `::test_submitter_is_registered_as_local_ok`
- `orchestrator/tests/test_hooks.py::test_bash_pegasus_registry_schema_and_fixed_classes`: 成功。
- `orchestrator/tests/test_plain_runner_coverage.py`: 自走 harness 3件成功。
- `bash -n`: 成功。
- registry JSON canonical parse、`git diff --check`: 成功。
- `python3 tools/check_docs.py`: `違反なし`。

## 所有外への波及可能性

- 現在の `git status` は指定された5 pathだけです。
- 検査中に runner が作った dispatch receipt directory は、`child_started=false` と内容を確認後、当該一時 directoryだけ除去しました。
- 既存 A-5 job body、submitter、契約テスト、登録簿 entry、`orchestrator/campaign/` は未変更です。
- A-5 job body内の global worktree prune自体は残りますが、新 launcherは兄弟 jobをfan-outしません。

## 現行の受理・拒否挙動

- 受理時は `balanced` 1本だけを投入し、要求される5変数をすべて `qsub -v` で渡します。
- 出力 parentの省略、相対・不存在・symlink・unsafe文字、repositoryとの包含関係、`.git`祖先、既存出力を投入前に拒否します。
- queueが`gen_S ENA/ACT`でない場合、quota検査失敗、Pegasus情報欠損、必須command欠損、Python 3.10不一致も拒否します。
- `qsub`失敗または空job idはfailure eventとしてatomic追記後に拒否します。

## 残した赤とその理由

- `tools/run_tests.py` 経由のpytest実行は実装済み・未実走です。runnerがdispatch経路を選びましたが、`qstat -Q`が認証エラーでrc=16となり、test child起動前に停止しました。
- この試行で`qsub`、計算ノード投入、build、benchmarkは実行されていません。
- 自走 harnessと直接呼出しした対象nodeにはassertion赤はありません。

## 総括

T-1998専用のbalanced単独launcher、登録閉包、契約テストを指定5 pathだけで実装しました。既存A-5の受理集合は変更していません。commit、`git add`、`qsub`は行っていません。