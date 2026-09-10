# 親が実測で確定させた事実 (段 2 再投入の入力)

これは**確定済み**である。再検証は歓迎するが、**再導出に model call を使ってはならない。**
以下に載っていない部分だけを調べよ。

repo root = `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t990-t991-serial-closure`
(main `c360e502` 取り込み済み)

## A. `REAL_REPO_SERIAL_NODES` の閉包漏れ — 確定 3 系統 20 node

正本は `orchestrator/tests/conftest.py:160-219` (`REAL_REPO_SERIAL_NODES`)。
除外註記は `:228-235`。優先順は `:223-226` (`REAL_REPO_EXECUTION_PRIORITY`)。
独立 golden は `orchestrator/tests/test_real_repo_serialization.py:37`。

### 系統 1 (1 node) — fixture 経由で実 submodule source を読む

`test_s1_measurement_freeze.py::test_recorded_ccbench_pin_hold_and_release_positive_control`
(`:216-229`)。`freeze_env` (`:63-86`) → module scope `real_known_axes_doc` (`:43-60`) →
`K.build_document()` が実 submodule source を読む。同 fixture を取る兄弟 10 node は正本に列挙済み
(`conftest.py:196-205`)。**この 1 node だけ漏れている。**

### 系統 2 (2 node) — 実共有 submodule の管理領域を変える canary

`test_s8b_floor_campaign.py::test_slow_real_prepare_cell_to_buildcache_canary_one_configuration`
(`:3455`) と `::test_slow_real_prepare_cell_to_buildcache_v2_canary_one_configuration` (`:3498`)。
どちらも `prepare_cell` を実走し、`prepare_cell` は
`patchharness.checkout(pin, base_dir=str(ROOT / "external" / "ccbench"))`
(`orchestrator/campaign/s1_direct_comparison.py:527`) を呼ぶ。`checkout()` は
`git worktree add --detach` (`patchharness.py:291`) で**実共有 submodule の管理領域**に
linked worktree を登録し、exit で破棄する。直前に実 submodule へ `git rev-parse HEAD` も打つ
(`test_s8b_floor_campaign.py:3463-3466`)。
skipif は submodule の `.git` 実在 + cmake/gcc-13/g++-13/nm 実在 (`:3450-3454`)。

### 系統 3 (17 node) — module fixture が実 repo を clone し実 submodule を読む

`orchestrator/tests/test_codex_reasoning_ab.py` の module scope fixture
`benchmark_snapshots` (`:275-297`) が `TOOL.build_snapshot(_ROOT, ...)` を呼ぶ。
`tools/codex_reasoning_ab.py:1371-1375` が `git clone --no-hardlinks --no-checkout <実 repo>`、
`:1384` の `_init_submodules_from_local_source(repo, snapshot)` (`:687-700`) が
実 repo の index stage entry と直下 submodule を source として読む。
`grep -c "codex_reasoning_ab" orchestrator/tests/conftest.py` = 0 (正本の外)。

fixture が module scope なので、**worker 内で最初に走った消費 node が setup を払う。**
どれが最初かは静的に決まらないので **17 件全部か 0 件かの二択**である。17 件:

`test_parent_numstat_controls_remain_pinned`,
`test_forbidden_commits_are_unreachable_in_both_cases`,
`test_cleaned_snapshot_records_absent_commit_graph_and_keeps_closure`,
`test_stale_commit_graph_referencing_pruned_commit_is_rejected_and_manifested`,
`test_m1_snapshot_head_pin_is_independent`, `test_m3_snapshot_mode_change`,
`test_m3_symbolic_head_is_required`, `test_m3_ignored_extra_and_missing`,
`test_m3_focus_artifact_directions`, `test_snapshot_submodule_object_store_is_recursive`,
`test_pos_neg_submodule_initialization_state_mismatch_is_rejected`,
`test_git_answer_object_reinjection_is_rejected`,
`test_supervisor_launches_pair_and_scrubs_git_environment`,
`test_agent_sandbox_binds_exclude_attempt_receipt_directory`,
`test_verify_replays_complete_fake_codex_experiment`,
`test_attempt_four_is_rejected_before_launch`,
`test_f3_4_prelaunch_exception_completes_pair_and_allows_next_generation`

**注意: `test_codex_reasoning_ab.py` と `tools/codex_reasoning_ab.py` は並行 wave の lane であり
編集してはならない。** conftest 側の node 列挙だけが本 wave の編集面である。

## B. コメントと実装の食い違い — 確定 2 件

1. `conftest.py:167` のコメント「実 external/ccbench に patch を apply/revert する writer」は
   実装と食い違う。`test_p3_s4_loop.py:1850-1857` (および `:1818-1824`) で
   `patchharness.applied` が `contextlib.nullcontext()` へ差し替えられている。
   worklog entry 512 で親が「writer 7 node」分類を撤回した記述とも整合する。
   **node を正本から削るのではなく、分類の根拠を実装へ合わせる。**
2. `conftest.py:232-233` の除外註記「slow oracle canary は patchharness の隔離 worktree を使い、
   共有 submodule worktree を patch しない」は論法が誤り。**patch しないことは、共有 submodule の
   管理領域を変えないことを含意しない** (系統 2 が反例)。

## C. 正本へ入れてはならないと確定した候補 (refuted)

- `test_campaign.py::test_patchharness_*` (`:10279-10370`) は `_fake_ccbench_repo()` が返す
  tmp repo が相手 (`:10283`)。除外註記のこの部分は正しい。過剰に入れると直列鎖が無駄に伸びる。
- 実 root / 実 submodule へ git の書き込み動詞
  (`commit`/`add`/`update-ref`/`update-index`/`write-tree`/`gc`/`repack`/`stash`/`fetch`/
  `prune`/`notes`/`tag`/`reflog`/`worktree`) を打つ test を全 `orchestrator/tests/` で走査した結果、
  hit は `test_codex_reasoning_ab.py:1517` の `git fetch <実 repo>` 1 件のみで、これは実 repo の
  **読み取り**である (書込先は tmp repo)。`hash-object -w` の hit
  (`test_ruleops.py:1121,2968` / `test_spool_fold.py:89` / `test_t080_freeze_migration.py:1169`
  / `test_s8b_oracle_driver.py:1239`) はすべて tmp repo が対象。

## D. [T-991] の候補地 — 親の一次調査

`GIT_OPTIONAL_LOCKS=0` を設定しない `git status` 経路:

- `orchestrator/tests/repo_tree_util.py:20-27` `_repo_status()` — 実親 repo への読取。
  `env=` を渡していない。
- `orchestrator/campaign/source_digest.py:761-770` `_tracked_status_paths()` — 実共有 submodule
  への読取。`env=` を渡していない。working-tree 健全性の fails-closed 判定に使われる。
- `orchestrator/campaign/silo_ladder_rung1.py:963, 2084` — third-party source への読取。
  `_run()` (`:323`) は `scrub_environment()` (`:306-320`) の allowlist 結果を env にする。
  allowlist は `_ENV_ALLOW_EXACT` (`:117`)。

抑止済みの対照: `orchestrator/campaign/patchharness.py:71-75` — `os.environ.copy()` に
`GIT_OPTIONAL_LOCKS = "0"` を設定し、抑止理由をコメントで明記している。

## E. 既存被覆 (新設検査の純増検出力を測る基準)

`orchestrator/tests/test_real_repo_serialization.py` の既存 test 関数:

`test_real_repo_group_collection_exactly_matches_canonical_nodes` (`:567`),
`test_xdist_group_audit_rejects_synthetic_negative_controls` (`:618`),
`test_xdist_group_name_set_audit_rejects_isolated_negative_controls` (`:669`),
`test_canonical_real_repo_nodes_have_no_handwritten_xdist_group_decorator` (`:744`),
`test_handwritten_xdist_group_decorator_control_is_rejected` (`:755`),
`test_real_repo_priority_order_is_literal_and_writers_follow_barrier` (`:777`),
`test_protocol_builder_repo_tree_guard_is_wired_to_real_root` (`:823`),
`test_ratified_memo_has_a_real_resolution_payer` (`:900`),
`test_loadgroup_scheduler_keeps_same_group_on_one_worker_and_control_detects_absence` (`:955`),
`test_effective_tempdir_is_not_tmpfs` (`:1034`),
`test_suite_conftest_does_not_wire_tmpdir_to_tmpfs` (`:1088`),
`test_tmpdir_fstype_lookup_positive_and_negative_control` (`:1103`),
`test_tmpfs_tmpdir_wiring_scanner_positive_and_negative_control` (`:1181`),
`test_tmpdir_guards_are_present_and_load_bearing` (`:1298`)

**これらはすべて「正本 vs 独立 golden」「group 配線」「順序」の検査であり、
実資源接触から集合を導出していない。** 両方のリストに無い node は既存では検出できない。
