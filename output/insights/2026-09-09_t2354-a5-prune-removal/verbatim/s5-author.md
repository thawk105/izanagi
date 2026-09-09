## 総括

段 4 裁定「プラン v2」を指定の 2 ファイルへ実装しました。  
A-5 cleanup から共有 gitdir の prune を撤去し、自 path の remove のみ残しました。  
実 Git fixture の新規 2 テストは self-run harness で正常・異常終了を含めて緑です。  
指定 pytest は実行基盤の容量・dispatch 障害により、実装済み・未実走です。

## 変更 diff の要約

- [a5_second_boot_backoff_sweep.sh](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2354-a5-prune-removal/tools/pegasus/a5_second_boot_backoff_sweep.sh:123)

  - `remove_rc`、`prune_rc` と共有 CCBench gitdir の prune ブロックを撤去。
  - `$JOB_CCBENCH`、`$JOB_REPO` への `worktree remove --force` は維持。
  - receipt を裸の cleanup rc で開始し、失敗した path のみ `remaining_*_path=` として追記。
  - `|| true`、cap 定数、budget assert は未変更。

- [test_a5_second_boot_job_contract.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2354-a5-prune-removal/orchestrator/tests/test_a5_second_boot_job_contract.py:16)

  - prune 正例 2 assert を、指定された実行可能 prune の不在 assert 1 行へ置換。
  - B-10 と同型のローカル Git helper と job 関数抽出 helper を追加。
  - 欠落した兄弟登録を保存する正常系 test と、locked 自 path の残置・receipt・終了 rc 優先順位を検査する失敗系 test を追加。
  - Git と cleanup 関数は実体を使用。`write_failure_receipt` だけを、許可どおり呼出回数と `worktree_cleanup` stage の観測用に stub 化。

変更はこの 2 ファイルだけです。`git add`、`git commit`、台帳・docs 編集は行っていません。`git diff --check` は rc=0 でした。

## 実走結果

- `python3 orchestrator/tests/test_a5_second_boot_job_contract.py`
  - rc=0、全 9 node 相当が通過。
  - 新規 node:

    - `orchestrator/tests/test_a5_second_boot_job_contract.py::test_a5_job_exit_cleanup_preserves_missing_sibling_worktree_registration`
    - `orchestrator/tests/test_a5_second_boot_job_contract.py::test_a5_cleanup_failure_records_remaining_paths_and_preserves_exit_precedence`

  - 既存 node:

    - `::test_current_scripts_are_a_positive_example_of_the_complete_contract`
    - `::test_finalizer_denominator_is_exactly_no_backoff`
    - `::test_finalizer_requires_all_eight_commits_and_zero_aborts`
    - `::test_inner_caps_and_final_margin_fit_strictly_inside_pbs_walltime`
    - `::test_job_body_accepts_exactly_the_two_adopted_workloads`
    - `::test_job_body_is_registered_only_as_dispatch_required`
    - `::test_submitter_workload_set_is_exactly_the_two_adopted_values`

  self-run の名前順自動収集に新規 2 関数が含まれ、実際に呼ばれることを確認済みです。

- file 集合の meta-test: `python3 orchestrator/tests/test_plain_runner_coverage.py`
  - rc=0、3/3 passed。
  - `::test_every_test_file_is_self_runnable_or_allowlisted`
  - `::test_allowlist_has_no_stale_or_self_runnable_entries`
  - `::test_this_metatest_is_itself_self_runnable`

- repo 規律に従い、pytest selector は `tools/run_tests.py` 経由で試行。
  - A-5 test file 全体: rc=16、child 未起動。
  - B-10 `-k worktree`: rc=16、child 未起動。
  - `test_acceptance_schedule_order.py::test_g5_real_ledger_covers_at_least_90_percent_of_real_collection`: rc=16、child 未起動。
  - すべて `qstat -Q` preflight rc=1（socket 作成不可）による dispatch infrastructure failure。同時に user slice は 16 GiB 上限付近、判定 headroom は 0 bytes でした。テストの赤はありませんが、これらの pytest node は実走していません。

## 波及の静的列挙

- job body の bytes と `script_sha256` が変わるため、T-1998 launcher の事前登録は着地後の新 digest で作り直す必要があります。
- A-5 の `write-heavy`／`balanced` と、この job body を再利用する T-1998 caller が新 cleanup を使用します。
- A-5 receipt の既知 runtime consumer は今回追加した test が最初です。B-10 の同名 receipt consumer は別 job bodyなので変更対象外です。
- 新規 2 node は acceptance duration ledger の被覆率へ影響します。台帳は指示どおり未変更です。
- `admission_registry.json` は path/class 登録であり hash pin ではないため、静的には変更不要です。

## 現行の受理・拒否挙動

| 面 | 変更前 | 変更後 |
|---|---|---|
| 共有登録 | cleanup が欠落兄弟登録を prune し得た | 欠落兄弟登録を維持 |
| 正常 cleanup | `0` と `prune_rc=0` | receipt は正確に `0\n` |
| remove 失敗 | prune を続行し、残置 path の構造化記録なし | 非 0 rc と失敗した自 path を記録し、登録・directory を維持 |
| 元 job rc | cleanup 失敗より元の非 0 rc を優先 | 同じ優先順位を維持 |
| 静的契約 | literal prune を要求 | 実行可能な literal `worktree prune` を拒否 |

## 未実走・未確認

- 指定された 2 pytest file 範囲と duration-ledger 被覆 meta-testは、実装済み・未実走です。
- `acceptance_duration_ledger.json` の更新と実被覆率確認は、JUnit を得る親の後続段へ残しています。
- job file 全体の `bash -n` は dispatch-required hook に拒否され未実走です。ただし変更した cleanup 関数は job body から抽出した実体を 4 ケースで実行済みです。
- Pegasus 計測、docs、commit、provenance 検査は本段の scope 外として行っていません。