# 段 5 単位 A 実装報告

## 1. 作った file と行数

- [tools/check_branch_rescue.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1825-rescue-gate/tools/check_branch_rescue.py): 1,791 行
- [orchestrator/tests/test_check_branch_rescue.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1825-rescue-gate/orchestrator/tests/test_check_branch_rescue.py): 764 行

最終 `git status --short --untracked-files=all`:

```text
?? orchestrator/tests/test_check_branch_rescue.py
?? tools/check_branch_rescue.py
```

指定外 file、docs、既存 test は変更していない。`git add`、commit も行っていない。

## 2. 現行の受理・拒否挙動 (実装前後で何が変わったか)

実装前:

- rescue CLI は存在しなかった。
- `check_branch_landed.py` は単一 branch / commit-ish の landed 判定のみ。
- 既存 checker の rc は landed=0、not-landed=1、indeterminate=2。

実装後:

- `--branch` と `--retire-worktree` を複数受理し、全候補を一括で 1 回の closure に渡す。
- `--ledger-check` 単独、または preview と同時に実行できる。
- `not-landed` は可視化内容であり rc=0 の受理集合に含む。
- 技術的不完全だけを rc=2、完全な通知を rc=3、usage を rc=64 とした。
- 既存 checker の挙動・期待値は一切変更していない。

## 3. rc / schema の実装状況 (裁定 §2.1 §3 との対応表)

| 契約 | 実装 |
|---|---|
| schema | `izanagi-branch-rescue-v1` |
| rc=0 | snapshot、closure、判定、期限が完全。landed / not-landed は問わない |
| rc=2 | timeout、上限、parse、root 移動、private ref、期限不明、checker 不完全など。rc=3 より優先 |
| rc=3 | 可視化が完全で ledger 通知、または audit の未記帳 commit がある |
| rc=64 | CLI usage error。stdout は空 |
| rc=1 | 使用しない |
| 削除許可 | `deletion_authorized` field は作っていない |
| closure | [一括 `_closure()`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1825-rescue-gate/tools/check_branch_rescue.py:986) から `git rev-list ... --stdin` を 1 回呼ぶ |
| stdin | 正側は `<oid>`、負側は `^<oid>`。`--not` 行なし |
| landed 判定 | [公開 CLI subprocess](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1825-rescue-gate/tools/check_branch_rescue.py:1253)。1 件 8 秒、全体 300 秒、既定 64 件 |
| 上限超過 | commit を残し `assessment-limit-exceeded` の indeterminate にする |
| gc.auto | [fanout `17` 標本 heuristic](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1825-rescue-gate/tools/check_branch_rescue.py:1051)。総 loose 数は観測値のみ |
| coverage | `/cleanup-branches` dispatcher 可視化だけを保証。手動 `git branch -d`、DW-O28、D978 未施行部分を JSON に明記 |
| object 保持 | top-level と ledger 出力で `object_retention_provided: false` 固定 |

## 4. root 3 分類の実装箇所 (file:line)

中心実装は [`_snapshot()`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1825-rescue-gate/tools/check_branch_rescue.py:682)。

1. 恒久 root:

   - 撤去候補以外の全 `refs/*`: [line 736 付近](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1825-rescue-gate/tools/check_branch_rescue.py:736)
   - 残存 worktree HEAD / commit 型 index: [line 817 付近](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1825-rescue-gate/tools/check_branch_rescue.py:817)
   - closure の stdin 負側へ `^<oid>` として投入。

2. 期限付き root:

   - 残存 reflog old/new: [line 838 付近](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1825-rescue-gate/tools/check_branch_rescue.py:838)
   - prunable worktree HEAD / index / reflog: [line 801 付近](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1825-rescue-gate/tools/check_branch_rescue.py:801)
   - 負側には入れず、commit の `retention.additional_sources` に期限と設定根拠を記録。

3. root にしないもの:

   - candidate ref: [line 724](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1825-rescue-gate/tools/check_branch_rescue.py:724)
   - candidate reflog: [line 850](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1825-rescue-gate/tools/check_branch_rescue.py:850)
   - retired worktree HEAD / index / reflog: [line 791](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1825-rescue-gate/tools/check_branch_rescue.py:791)
   - pseudoref、alternate refs、検証不能 private refs。private ref、replace、grafts、shallow は rc=2。

開始・終了 digest の照合は [line 1670](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1825-rescue-gate/tools/check_branch_rescue.py:1670)。

## 5. 事前登録変異への負例の対応表 (m01..m17 と正例、各々どのテストが殺すか)

| ID | 殺す test |
|---|---|
| m01 | `test_m01_surviving_reflog_is_time_limited_not_negative_root` |
| m02 | `test_m02_nonretired_detached_worktree_head_is_permanent_root` |
| m03 | `test_m03_candidate_reflog_is_not_a_post_cleanup_root` |
| m04 | `test_m04_remote_ref_is_in_full_refs_namespace_root_set` |
| m05 | `test_m05_all_candidates_are_subtracted_in_one_closure` |
| m06 | `test_m06_rev_list_stdin_uses_caret_oids_and_never_not_line` |
| m07 | `test_m07_indeterminate_assessment_forces_rc2` |
| m08 | `test_m08_not_landed_is_content_not_technical_failure` |
| m09 | `test_m09_loose_deadline_uses_object_mtime_not_now` |
| m10 | `test_m10_m11_packed_mtime_never_becomes_determinate_deadline` |
| m11 | `test_m10_m11_packed_mtime_never_becomes_determinate_deadline` |
| m12 | `test_m12_gc_auto_uses_fanout_sample_not_total_count` |
| m13 | `test_m13_closure_limit_keeps_the_over_limit_observation`、`test_assessment_limit_marks_every_unrun_commit` |
| m14 | `test_m14_unledgered_audit_finding_returns_rc3` |
| m15 | `test_m15_retention_claim_is_fixed_false_and_true_entry_is_rejected` |
| m16 | `test_m16_git_allowlist_rejects_forbidden_command_before_spawn` |
| m17 | `test_m17_root_digest_movement_forces_rc2` |
| p01 | `test_p01_empty_closure_is_complete_rc0` |
| p02 | `test_p02_real_checker_landed_and_loose_deadline_is_rc0` |
| p03 | `test_p03_real_checker_not_landed_is_still_rc0` |
| p04 | `test_p04_missing_ledger_and_real_audit_zero_is_rc0` |

追加で index commit、prunable worktree、private ref、alternate object、2 detached worktree、repo bytes 不変も実 Git fixture で検査した。

## 6. 実走結果 (nodeid と範囲、そのまま貼る)

指定 runner の最終実行:

```text
$ python3 tools/run_tests.py orchestrator/tests/test_check_branch_rescue.py
警告: 受入形でない走行です。この結果を受入全走として扱わないでください。
[Pegasus dispatch] receipt を /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1825-rescue-gate/output/pegasus-dispatch/93a7e0780d2fb6c67c3fa4f1e8742e36/receipt.json へ保存しました (child rc=16)
Pegasus dispatch infrastructure failure: qstat -Q preflight rc=1
IZANAGI_DISPATCH_OUTCOME_V1 {"child_rc":null,"child_started":false,"kind":"infra","reason":"dispatch-error"}
IZANAGI_TASK_RUN_DIAGNOSTIC_V1 recording-unavailable:dispatch-no-child
```

rc=16、child 未起動。したがって pytest nodeid は 1 件も実走されておらず、緑とは報告しない。

内容走査で特定したメタテストの runner 実行も同じ理由で未起動:

```text
警告: 受入形でない走行です。この結果を受入全走として扱わないでください。
Pegasus dispatch infrastructure failure: qstat -Q preflight rc=1
[Pegasus dispatch] receipt を /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1825-rescue-gate/output/pegasus-dispatch/92011cfc86868cb9d3e32cbe4cbd0bcf/receipt.json へ保存しました (child rc=16)
IZANAGI_DISPATCH_OUTCOME_V1 {"child_rc":null,"child_started":false,"kind":"infra","reason":"dispatch-error"}
IZANAGI_TASK_RUN_DIAGNOSTIC_V1 recording-unavailable:dispatch-no-child
```

対象 nodeid:

```text
orchestrator/tests/test_login_headroom.py::test_ceiling_numeric_literal_occurs_only_in_login_headroom_module
orchestrator/tests/test_login_headroom.py::test_local_budget_constants_are_defined_only_in_login_headroom_leaf
orchestrator/tests/test_pegasus_dispatch_compute.py::test_best_effort_qdel_production_caller_is_only_fresh_gate
orchestrator/tests/test_p3_build_authority_cli.py::test_tracked_python_coder_authority_ast_closure_is_exact
orchestrator/tests/test_pytest_collection_config.py::test_permanent_exclusion_table_has_no_other_verifier_or_oracle_tests
```

補助診断として、pytest を緑と称さない前提で test 関数 28 件を使い捨て実 Git repo に直接適用した結果:

```text
PASS test_alternate_only_commit_has_indeterminate_external_retention
PASS test_assessment_limit_marks_every_unrun_commit
PASS test_m01_surviving_reflog_is_time_limited_not_negative_root
PASS test_m02_nonretired_detached_worktree_head_is_permanent_root
PASS test_m03_candidate_reflog_is_not_a_post_cleanup_root
PASS test_m04_remote_ref_is_in_full_refs_namespace_root_set
PASS test_m05_all_candidates_are_subtracted_in_one_closure
PASS test_m06_rev_list_stdin_uses_caret_oids_and_never_not_line
PASS test_m07_indeterminate_assessment_forces_rc2
PASS test_m08_not_landed_is_content_not_technical_failure
PASS test_m09_loose_deadline_uses_object_mtime_not_now
PASS test_m10_m11_packed_mtime_never_becomes_determinate_deadline
PASS test_m12_gc_auto_uses_fanout_sample_not_total_count
PASS test_m13_closure_limit_keeps_the_over_limit_observation
PASS test_m14_unledgered_audit_finding_returns_rc3
PASS test_m15_retention_claim_is_fixed_false_and_true_entry_is_rejected
PASS test_m16_git_allowlist_rejects_forbidden_command_before_spawn
PASS test_m17_root_digest_movement_forces_rc2
PASS test_normal_preview_preserves_repository_control_bytes
PASS test_p01_empty_closure_is_complete_rc0
PASS test_p02_real_checker_landed_and_loose_deadline_is_rc0
PASS test_p03_real_checker_not_landed_is_still_rc0
PASS test_p04_missing_ledger_and_real_audit_zero_is_rc0
PASS test_private_ref_presence_is_reported_and_never_used_as_negative_root
PASS test_prunable_worktree_roots_are_time_limited_not_negative
PASS test_retiring_one_of_two_same_detached_heads_keeps_the_other_root
PASS test_surviving_index_commit_is_root_but_blob_is_not_commit_root
PASS test_usage_rc64_and_fixed_coverage_boundary
TOTAL 28
```

メタテストも同じ直接診断では 5 nodeid 相当が通過した。

## 7. 所有外への波及可能性 (caller・共有 fixture・consumer test の静的列挙)

- 現時点の production caller: なし。repo 全体の静的検索でも新 schema / CLI の既存参照は 0。
- 予定 caller: 単位 B 所有の `.claude/commands/cleanup-branches.md`。
- subprocess 依存:
  - `tools/check_branch_landed.py`
  - `tools/audit_dangling_commits.py`
- 共有 fixture: なし。新 test file 内の helper だけを使用。
- consumer test:
  - 今回の `test_check_branch_rescue.py`
  - 単位 B 予定の `test_branch_rescue_ledger.py`
  - 上記 5 件の repository-wide 内容走査メタテスト
- JSON consumer は `coverage_boundary`、`decision_inputs`、`ledger`、`deletion_loss_closure` を固定名として利用できる。

## 8. やらなかったこと・未解決

やらなかったこと:

- 単位 B 所有の `docs/unreachable-object-ledger.md`
- `orchestrator/tests/test_branch_rescue_ledger.py`
- `.claude/commands/cleanup-branches.md`
- その他 docs、worklog、decisions、README
- 既存 tool / test の変更
- `git add`、commit
- Web 検索
- repo を変異させる Git command の実装

未解決:

- Pegasus sandbox が socket を作れず `qstat -Q` が失敗するため、指定 runner の pytest 実走は rc=16 のまま。親側で同じ 2 command の再実走が必要。
- runner が生成した今回分の ignored dispatch receipt は exact path を確認後に除去済み。

台帳 schema [`LEDGER_FIELDS`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1825-rescue-gate/tools/check_branch_rescue.py:65) の全 field:

| field | 型 |
|---|---|
| `schema` | string。`izanagi-unreachable-object-ledger-v1` |
| `entry_id` | string |
| `recorded_at` | string |
| `source_refs` | array[string] |
| `source_tips` | object。key=full refname、value=full oid string |
| `assessment_report_sha256` | string |
| `object_oid` | string |
| `object_type` | string。固定値 `commit` |
| `assessment_schema` | string。固定値 `izanagi-branch-landed-v1` |
| `assessment_verdict` | string enum: `landed` / `not-landed` / `indeterminate` |
| `assessment_reason` | string |
| `storage_kind` | string |
| `object_mtime` | string または null |
| `loss_possible_not_before` | string |
| `lower_bound_basis` | string |
| `gc_auto_threshold` | integer または null |
| `loose_count_at_loss` | integer または null |
| `gc_headroom_at_loss` | integer または null |
| `status` | string enum: `pending` / `rescued` / `accepted-loss` / `reachable-again` / `object-missing` |
| `resolved_at` | string または null |
| `rescue_ref` | string または null |
| `resolution_note` | string または null |
| `object_retention_provided` | boolean。固定値 `false` |

## 総括

指定された 2 file だけを作成し、裁定 v2 の一括 closure、root 3 分類、期限、標本 gc.auto、landed subprocess、ledger audit、rc 0/2/3/64、coverage boundary を実装した。事前登録 m01〜m17 と p01〜p04 はすべて負例・正例を用意し、直接診断では全 28 test が通過した。

唯一の未完了は、外部の `qstat` socket 制限によって指定 runner の pytest child が起動できなかった点である。