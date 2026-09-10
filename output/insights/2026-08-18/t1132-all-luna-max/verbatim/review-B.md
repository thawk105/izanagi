静的レビュー結果は NO-GO です。指定 3 文書と `diff.txt` は読了し、pytest は実走していません。

### B-01 — 段 5 caller が `reasoning=high` のまま

- 発火条件: v3 docs を land 後、author producer を起動すると `--reasoning high` が unbound stage の caller 値として採用される。`gpt-5.6-luna` には届くが effort は `high` のままになる。
- file:line: [s4-adjudication-v3.md:17](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t1132-stage2-luna/s4-adjudication-v3.md:17)、[runner-author2.sh:14](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t1132-stage2-luna/runner-author2.sh:14)、[runner-author.sh:15](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t1132-stage2-luna/runner-author.sh:15)、[dev_wave_codex.py:173](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1132-stage2-luna/tools/dev_wave_codex.py:173)、[codex_worker_launch.py:2363](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1132-stage2-luna/tools/codex_worker_launch.py:2363)、[codex_worker_launch.py:1689](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1132-stage2-luna/tools/codex_worker_launch.py:1689)、[codex_worker_launch.py:2197](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1132-stage2-luna/tools/codex_worker_launch.py:2197)
- 成果物影響: 段 5 の receipt が `requested_effort=high` / `recorded_effort=high` となり、裁定の `luna@max` と実行結果が不一致になる。fix の継承値も旧値になり得る。
- 判定: must-fix。caller 側を `max` に更新し、CLI の受理集合は変更しないこと。

### B-02 — dispatcher consumer test が author/fix の `high` を固定

- 発火条件: `test_dry_run_stage_and_lane_matrix` または fake fix dispatch を実行すると、author/fix に `high` を渡す。現在の CLI は受理するためテストはこの古い caller 契約を検出しない。
- file:line: [test_dev_wave_codex.py:101](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1132-stage2-luna/orchestrator/tests/test_dev_wave_codex.py:101)、[test_dev_wave_codex.py:103](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1132-stage2-luna/orchestrator/tests/test_dev_wave_codex.py:103)、[test_dev_wave_codex.py:439](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1132-stage2-luna/orchestrator/tests/test_dev_wave_codex.py:439)
- 成果物影響: テスト由来の launch argv が旧 effort を再現し、B-01 の stale caller を緑のまま見逃す。
- 判定: nit。S05 は意図的に unbound のため、実装側で `high` を拒否してはならない。

### 追跡結果

model の鎖は [operations.md:14](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1132-stage2-luna/docs/dev-wave/operations.md:14) → [launch_authority.py:445](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1132-stage2-luna/tools/dev_waves/launch_authority.py:445) → [launch_authority.py:489](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1132-stage2-luna/tools/dev_waves/launch_authority.py:489) → [codex_worker_launch.py:1687](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1132-stage2-luna/tools/codex_worker_launch.py:1687) → [codex_worker_launch.py:2196](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1132-stage2-luna/tools/codex_worker_launch.py:2196) で、v2 の全 route が `gpt-5.6-luna` になる。

lane choices、stage choices、`--reasoning` の受理集合、receipt schema は変更されていない。[dev_wave_codex.py:24](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1132-stage2-luna/tools/dev_wave_codex.py:24)、[codex_worker_launch.py:3034](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1132-stage2-luna/tools/codex_worker_launch.py:3034)、[codex_worker_launch.py:3738](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1132-stage2-luna/tools/codex_worker_launch.py:3738)。旧 receipt は authority commit を再構成する監査により互換性を保つ。[codex_worker_launch.py:3499](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1132-stage2-luna/tools/codex_worker_launch.py:3499)

## 総括

NO-GO。B-01 の stale caller が実際に `luna@high` の receipt を生成できるため、修正が必要です。レビューは read-only 静的検査のみで、pytest の緑は記録していません。