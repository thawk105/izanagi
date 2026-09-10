実装は完了しました。変更は指定された2ファイルのみで、commit は作成していません。`tools/mutation_harness.py` は開始時・終了時とも SHA-256 `65e3390d...f15597dd` で不変です。

### 現行の受理・拒否挙動

既存 `mutation_harness.py` の受理集合は変更していません。引き続き exact worktree root、clean な固定 HEAD、checkout 外の spec/out、登録済み spec hash、追跡済み runner/test、`--resume` identity/evidence 完全一致を要求します。

新しい wrapper は次をすべて満たす場合だけ受理します。

- source が exact worktree root
- scratch が全 registered worktree 外の既存・非 symlink・書込可能 directory
- spec/out が registered/generated worktree 外
- container が不存在で、`mkdir(exist_ok=False)` により今回だけが所有
- commit が full SHA に解決され、生成 HEAD と一致
- 生成木の porcelain が空、`external/ccbench` が gitlink pin どおり初期化済み
- 同一絶対 out の外側 lock を取得
- 非 plan-only 実走は `--detached`
- 完走時は terminal ledger、または `--plan-only`

否定条件、lock 競合、共有木 drift、evidence/teardown/admin binding 不整合は fail-closed で rc=125 です。child 異常終了・例外・SIGINT/SIGTERM は未完了として container を保持します。

差分は「使い捨て木経由の任意経路を追加した」ことだけです。direct harness の admission、台帳 schema、consumer の受理集合は拡大・縮小していません。

### 変更範囲

- [tools/mutation_worktree.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t503-disposable-worktree/tools/mutation_worktree.py:1)
- [orchestrator/tests/test_mutation_worktree.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t503-disposable-worktree/orchestrator/tests/test_mutation_worktree.py:1)

`git status --short` は上記2ファイルだけが untracked です。

### 実装述語と段4裁定の対応

| 実装述語 | 段4裁定 |
|---|---|
| CLI、source HEAD を既定 commit として full SHA 化 | §2-1、A-6 |
| 絶対 out 由来の非 blocking `flock` | §2-2、A-5/B-1 |
| exact source、scratch/spec/out の境界、既存 container 非接触 | §2-3、A-3/B-7 |
| detached worktree、no-fetch submodule、HEAD/porcelain/gitlink 再検査 | §2-4 |
| generated container cwd、runner argv/stream 透過、repository 選択 `GIT_*` 除去 | §2-5、A-1/B-11 |
| terminal ledger または plan-only のみ teardown、未完了保持 | §2-6、A-10/B-6 |
| evidence を削除前に `<out>.dispatch-evidence` へ rename、resume 前に同一絶対 path へ復元 | §2-6、B-5 |
| container と自 admin dir のみ削除。admin backpointer を再検査 | §2-6、A-4/B-8 |
| source/main の porcelain・submodule stdout bytes を前後比較 | §2-7、MW-14 |
| wrapper SHA、commit、paths、child rc、evidence、snapshot 結果の receipt | §2-8、B-4 |
| stale 自動掃除なし、既存 container 拒否 | §2-9、DW-G04 |
| active child process group への SIGINT/SIGTERM 転送 | MW-12 |
| cleanup/postcondition failure が child rc より優先して rc=125 | MW-11 |

`git worktree prune`、`git worktree remove`、`git submodule deinit` は実装・テストに含まれていません。

### MW-01〜MW-14 の exact nodeid

| ID | 無効化すると赤になる nodeid |
|---|---|
| MW-01 | `orchestrator/tests/test_mutation_worktree.py::test_source_must_be_the_exact_worktree_root` |
| MW-02 | `orchestrator/tests/test_mutation_worktree.py::test_scratch_inside_any_registered_worktree_is_rejected` |
| MW-03 | `orchestrator/tests/test_mutation_worktree.py::test_scratch_symlink_is_rejected` |
| MW-04 | `orchestrator/tests/test_mutation_worktree.py::test_existing_container_is_preserved_and_never_claimed` |
| MW-05 | `orchestrator/tests/test_mutation_worktree.py::test_same_out_from_different_scratch_is_rejected` |
| MW-06 | `orchestrator/tests/test_mutation_worktree.py::test_post_provision_rejects_head_mismatch` |
| MW-07 | `orchestrator/tests/test_mutation_worktree.py::test_teardown_removes_only_own_admin_dir` |
| MW-08 | `orchestrator/tests/test_mutation_worktree.py::test_dispatch_evidence_is_relocated_before_delete` |
| MW-09 | `orchestrator/tests/test_mutation_worktree.py::test_incomplete_run_keeps_container_for_resume` |
| MW-10 | `orchestrator/tests/test_mutation_worktree.py::test_child_return_code_is_propagated` |
| MW-11 | `orchestrator/tests/test_mutation_worktree.py::test_teardown_failure_overrides_child_rc` |
| MW-12 | `orchestrator/tests/test_mutation_worktree.py::test_sigint_and_sigterm_are_forwarded` |
| MW-13 | `orchestrator/tests/test_mutation_worktree.py::test_spec_and_out_inside_registered_worktree_are_rejected` |
| MW-14 | `orchestrator/tests/test_mutation_worktree.py::test_shared_tree_drift_fails_closed` |

A-1/B-11 置換の追加3点は次です。

- `orchestrator/tests/test_mutation_worktree.py::test_fake_harness_wrapper_is_exactly_transparent_between_observation_points`
- `orchestrator/tests/test_mutation_worktree.py::test_real_harness_local_e2e_uses_disposable_tree_between_observation_points`
- `orchestrator/tests/test_mutation_worktree.py::test_relocated_evidence_is_revalidated_by_resume_plan_only_between_observation_points`

全17テストの docstring に「共有木の観測点間 bytes 不変だけを主張し、物理永続性は主張しない」を残しています。

### 検証結果

実施済みの静的検査:

- `python3 -m py_compile`：2ファイルとも成功
- 新規ファイルに対する `git diff --check --no-index`：問題なし
- 禁止3 command の文字列検査：0件
- 全17テストの docstring AST 検査：欠落0件
- `mutation_harness.py` hash：開始時・終了時一致

pytest は実装済み・未実走です。次の対象を `tools/run_tests.py` から3回 dispatch しましたが、すべて計算ジョブ起動前に失敗しました。

```text
orchestrator/tests/test_mutation_worktree.py
orchestrator/tests/test_plain_runner_coverage.py
```

結果はいずれも `Pegasus dispatch infrastructure failure: qstat -Q preflight rc=1`、runner rc=16 です。したがって実行済み nodeid は0件で、緑とは申告しません。

### 所有外への波及可能性

- caller: 現時点で tracked caller はありません。`DW-M05`、operations、dispatcher への配線は未実装なので自動 activation されません。
- direct harness caller: 従来どおり共有 checkout を直接指定でき、wrapper receipt の有無も consumer は検査しません。
- runner caller: runner argv は無改変です。絶対 source checkout の runner pathを渡すと、生成木側 harness の既存 identity gate が拒否します。通常は `tools/run_tests.py` のような生成木相対表記が必要です。
- shared fixture: 既存 fixture は変更していません。新規テストは `tmp_path` 内の main/linked worktree/local submodule origin だけを使用します。
- consumer test: 新規 test file は self-runner を持つため `test_plain_runner_coverage.py` の対象になります。
- harness consumer: dispatch ledger の絶対 evidence path は、teardown 後には wrapper の rehydrate を経由しないと再検証できません。
- 運用分類: 新規 `tools/` script は V-8 未裁定のため `unknown = dispatch-required` のままです。
- docs/checker: tools map、runbook、DW-M05、check_docs 側の分類連携は今回の所有外です。

### 実装しなかった段4項目

明示された2ファイル以外は編集禁止だったため、以下は実装していません。

- `DW-M05`、operations、runbook、worklog、design doc の更新
- harness admission、legacy direct 経路停止、consumer admission（V-7）
- 実行場所の cgroup charged-memory 分類（V-8、人間手番）
- owner record、exclusive lease、scheduler terminal 証明、自動 GC（V-9/A-3残部）
- inode-bound teardown、stale 自動削除
- write-ahead journal、fsync契約、原子的 target 置換、in-place repair
- V-4/V-5 の capability/metadata admission
- 変異 matrix、受入全走、`check_docs`、`check_codex_agents`、provenance 監査
- commit

これらを closed/完了とは扱っていません。

## 総括

実装の骨子:

- commit 固定の detached worktree と no-fetch submodule を作り、既存 harness を無変更で起動します。
- out 基準 lock、terminal 条件付き teardown、自 admin 限定削除で共有面を絞りました。
- dispatch evidence は削除前に外へ退避し、resume plan-only 時に同一絶対 pathへ戻します。
- receipt と前後 snapshot により wrapper 自身の identity・結果・共有木不変判定を残します。

未解決は、Pegasus dispatch infrastructure failure により17テストと meta-test が未実走であること、V-7/V-8/V-9およびdocs配線がscope外であることです。

親が最初に確認すべき3点:

1. 計算ノードで新規17 nodeと `test_plain_runner_coverage.py` を実走する。
2. terminal ledger判定、evidence→container→自admin の teardown順をレビューする。
3. 実 harness dispatch E2Eの evidence退避後 `--resume --plan-only` 再検証を最優先で確認する。