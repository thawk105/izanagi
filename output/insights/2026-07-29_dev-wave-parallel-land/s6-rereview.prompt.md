# Stage 6 focused re-review after fix

You are a read-only focused reviewer for an Izanagi dev-wave. Work only in:

`/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-skill`

Do not edit, stage, restore, commit, run tests, or access the network. Read:

- `CLAUDE.md`
- `docs/dev-wave/workers.md` sections DW-S06-A/B/C
- `docs/dev-wave/core.md` section DW-G05
- `docs/dev-wave/operations.md` section DW-O16
- `output/insights/2026-07-29_dev-wave-parallel-land/s6-review-git.md`
- `output/insights/2026-07-29_dev-wave-parallel-land/s6-review-scope.md`
- `output/insights/2026-07-29_dev-wave-parallel-land/s6-adjudication.md`
- `output/insights/2026-07-29_dev-wave-parallel-land/s6-fix.md`
- the four current implementation/test files
- both the staged pre-fix snapshot (`git diff --cached`) and the unstaged fix
  (`git diff`), plus status

For each of the nine adopted must-fix items in `s6-adjudication.md`, produce a table:

| # | status (`closed` / `partial` / `regressed`) | exact evidence | residual artifact/acceptance impact |

Attack the implementation, not the fix report. In particular verify:

- lock is acquired before every shared mutable main/config/history/head check, and
  a mutating winner cannot make the loser emit a permanent rejection;
- ignored control containers are always validated, identity snapshots are stable,
  and target collision checks do not blanket-reject unrelated ignored caches;
- effective include/worktree filter config is rejected and partial mutation/unknown
  HEAD cannot be clean retryable `not-landed`;
- gitlink D16 recovery uses the same original evidence and rejects mismatch;
- the E2E actually binds new-main acceptance inputs, not just a vacuous marker;
- checker negatives are independent enough to catch O23 duplication, adapter drift,
  obvious alternate helper/direct ff, and the real-repo allowance is gone.

Identify any new regression introduced by the fix. Only mark must-fix when DW-G05
artifact or acceptance-set impact is concrete; keep style/nits/backlog separate.
No test claim may be based on your run because you must not run tests.

End with `## 総括` and exactly one verdict: `GO` or `NO-GO`.
