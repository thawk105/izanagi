# Stage 6 author fix: parallel dev-wave land

You are the single Codex `role=author` fix unit for an Izanagi dev-wave. Work only in:

`/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-skill`

The index contains the pre-fix integrated snapshot. Do not stage, reset, restore, commit,
or edit the index. Your changes must remain as unstaged working-tree changes against
that snapshot.

Your exclusive editable ownership is exactly:

- `tools/dev_wave_land.py`
- `orchestrator/tests/test_dev_wave_land.py`
- `tools/check_docs.py`
- `orchestrator/tests/test_check_docs.py`

Do not edit docs, skills, commands, handoff, insights, fixtures outside these four
files, Git config, submodules, or any other path. Do not commit. Do not access the
network. Read before editing:

- `CLAUDE.md`
- `docs/dev-wave/workers.md` sections DW-S05-A/B/C and DW-S06-A/B/C
- `docs/dev-wave/core.md` section DW-G05
- `docs/dev-wave/operations.md` sections DW-O01..O06, DW-O08..O20, DW-O23
- `docs/dev-wave/mutation.md` sections DW-M02..M08
- `output/insights/2026-07-29_dev-wave-parallel-land/parent-brief.md`
- `output/insights/2026-07-29_dev-wave-parallel-land/s4-adjudication-plan-v2.md`
- `output/insights/2026-07-29_dev-wave-parallel-land/s5-author.md`
- both `s6-review-git.md` and `s6-review-scope.md`
- `output/insights/2026-07-29_dev-wave-parallel-land/s6-adjudication.md`
- all four owned files and the staged/unstaged diff

Implement every adopted must-fix in `s6-adjudication.md`, with these clarifications:

1. Acquire the common lock nonblocking after request/repository identity validation
   but before inspecting mutable shared main/config/history/HEAD/cleanliness/audit
   state. A competing lander mutating main must make the loser return `lock-busy`,
   not transient `rejected`. Keep all mutation-capable Git commands inside the lock.
2. Always validate both control containers even if Git excludes/ignores them.
   Compare control-plane identity/binding snapshots around status observation so
   pathname replacement fails closed. Do not reject unrelated pre-existing ignored
   caches. Before merge, reject target changes that collide with an existing ignored
   path or a foreign validated control-plane artifact; never touch foreign files.
3. Inspect effective config including local includes and worktree scope, with
   global/system config still disabled. Reject filter/promisor/partial-clone
   execution surfaces before merge and test both include and worktree-config cases.
4. If post-merge HEAD cannot be observed, return a non-retryable postcondition
   failure. If merge leaves HEAD short of T but changes index/worktree, do not call
   it clean `not-landed`; return a distinct non-retryable postcondition failure.
5. Preserve the original A/T/audited sequence for gitlink-changing waves. The first
   successful ff may require D16 and report postcondition failure; after actual
   submodules are synchronized to T, rerunning the same request may return
   `already-landed`. Do not accept uninitialized or mismatched submodules.
6. Add independent audit-sequence negatives for reverse order, extra commit, and
   same-length wrong commit.
7. Delete the six-finding transitional allowance from `test_real_repo_clean`.
8. Require the helper path to occur only once in all operations and only in O23.
   Exact-pin the current Codex adapter sentence that Stage 9 follows only the common
   land contract. Add independent negative fixtures for an obvious alternate land
   helper and direct `git merge --ff-only` main mutation in command/Skill without
   overmatching ordinary prose.
9. In the two-wave E2E, after winner land and loser resync, run an explicit synthetic
   acceptance check bound to the exact resynced tip, then retry with
   `tested_main=winner_tip` and exact `winner_tip..resynced_tip` audit closure.

DW-S05 inheritance:

- Keep code/test ownership disjoint from parent docs and do not commit.
- Do not xfail the intentional or new red. Do not weaken tests, inject current
  hashes into expected values, or bake volatile diagnostics into expectations.
- State the previous accepted/rejected behavior before changing it; do not broaden
  scope beyond the adjudication.
- If you claim green, report exact commands/node ranges. Your run does not replace
  the parent's acceptance run.
- Run meta-tests for changed/new tests. Parent docs are now integrated, so
  `check_docs` and `test_real_repo_clean` must be unconditionally green; there is no
  expected transitional finding.
- Report possible effects on callers, shared fixtures, and consumers outside your
  ownership.

At minimum run:

- `python3 -m pytest -q orchestrator/tests/test_dev_wave_land.py`
- `python3 -m pytest -q orchestrator/tests/test_check_docs.py`
- `python3 -m pytest -q orchestrator/tests/test_dev_wave_land.py orchestrator/tests/test_check_docs.py`
- the repository's plain-runner/meta-test coverage relevant to these files
- `python3 tools/check_docs.py`
- `python3 tools/check_codex_agents.py`
- `python3 -m py_compile tools/dev_wave_land.py tools/check_docs.py`
- `git diff --check` for your unstaged changes

Finish with changed files, exact test results, residual risks, and `## 総括`.
