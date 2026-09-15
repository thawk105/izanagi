---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-09-16
wave: dev-wave-t2638-codex-worktree-retirement
seq: 2
---

## 再発

### F119

- **再発: 2026-09-16** — 向きが逆の同型 ([T-2638])。F119 は `git diff-tree -m` が merge で
  **過大計上**する側だったが、今回は `git log --find-object` が merge で**過少計上**した。
  `git log` は既定で merge commit の差分を作らないため、`merge(main):` 経由で main へ入った blob が
  「どの commit にも無い」と判定される。実証: 同じ blob が `-m` / `--diff-merges=first-parent` を
  付けると merge commit `9f2f8d3a3` に見つかり、`git rev-parse refs/heads/main:<path>` は
  **その blob が main の現行内容そのもの**だと返した。この誤判定のまま「子 worktree に着地して
  いない内容が 6 件ある」と報告する直前だった。**根本原因は F119 と同じで、merge commit に対する
  git の差分生成の既定を確かめずに判定器へ据えたこと。** 恒久対応 = 内容の着地判定は
  `git rev-parse <ref>:<path>` と `git hash-object` の直接比較を一次とし (O(1)・履歴を歩かない・
  merge の影響を受けない)、履歴検索は `-m` 付きの補助に限り、**`--find-object` の無 hit を単独の
  否定根拠にしない**。再発検知 = memory `git-find-object-misses-merge-commits`。
  なお `--find-object` の hit も「その commit の tree にその blob がある」ことを意味しない
  (削除された側でも hit する) ため、証拠 commit として記録するなら `ls-tree` で tree を直接照合する。

### F300

- **再発: 2026-09-16** — churn の出所が**同じ走行の内側**という変種 ([T-2638])。docs のみの wave で
  受入全走を 4 回投入し、4 回とも赤になった (赤 3 件 → 33 件 → 1 件 → 2 件)。赤は毎回
  「走行中に作業木・submodule の状態が変化した」族で、`assert_repository_unchanged` の `before`
  bytes には `?? .t316-live-<乱数>/…` が入っていた。これは**同じ受入走行の別テストが wave 作業木へ
  作った scratch** である。F300 の既往は「親が repo 内で別作業をした」「別 session が local main を
  進めた」だったが、今回は**走行の内側で完結しており、親も他 session も何もしていない**。
  赤になった test の集合は走行ごとに変わり (同一 tip・同一差分)、単独走では全件緑
  (3 件 → 3 passed、30 件 → 199 passed、1 件 → 1 passed)。変更した path
  (`docs/spool/**`・`output/insights/**`) は赤になった 4 test file とその production module の
  どこからも参照されておらず、差分到達不能を機械的に確認した。
  **恒久対応は未定。** `orchestrator/tests/flaky_test_holds.py` への登録は `DW-O18` が
  「main 既存 F を証拠に Codex role=author が登録」と定めるが、本再発追記が main へ着地するまで
  その証拠が存在しない (循環)。影響を受ける test は
  `test_p3_b4_producer_auth_experiment.py::test_disposable_tree_mutation_does_not_change_main_worktree`、
  同 `::test_case_failure_records_aborted_and_remaining_cases_continue`、
  `test_run_tests_preflight.py::test_headroom_short_queue_unavailable_cap_oom_stops_without_dispatch`、
  `test_check_ai_provenance.py::test_provenance_headroom_short_queue_unavailable_cap_oom_stops`。
  再発検知 = 受入 log の FAILED 行がこの 4 件のいずれかだけで、単独走が緑になること。
