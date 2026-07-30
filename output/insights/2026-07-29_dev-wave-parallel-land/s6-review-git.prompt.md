# Stage 6 adversarial review: Git concurrency and trust boundary

You are a read-only adversarial reviewer for an Izanagi dev-wave. Work only in:

`/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-skill`

Do not edit files, run tests, commit, or access the network. Static inspection and
read-only Git commands are allowed. Read all of the following before judging:

- `CLAUDE.md`
- `output/insights/2026-07-29_dev-wave-parallel-land/parent-brief.md`
- `output/insights/2026-07-29_dev-wave-parallel-land/s4-adjudication-plan-v2.md`
- `output/insights/2026-07-29_dev-wave-parallel-land/s5-author.md`
- `tools/dev_wave_land.py`
- `orchestrator/tests/test_dev_wave_land.py`
- `tools/check_docs.py`
- `orchestrator/tests/test_check_docs.py`
- `.claude/commands/dev-wave.md`
- `.agents/skills/dev-wave/SKILL.md`
- `docs/dev-wave/core.md`
- `docs/dev-wave/operations.md`
- the current complete `git diff` and `git status --short`

Review through the Git concurrency and trust-boundary lens. Attack at least:

1. Every check-to-use race around main, wave, index, worktree registration, lock,
   merge, and postcondition verification.
2. Whether a cooperating parallel dev-wave can make another valid wave unsafe or
   spuriously blocked, including the same-base winner/loser sequence.
3. Whether schema-looking handoffs or directory-looking worktrees can bypass dirt
   rejection without a trustworthy Git-admin/backpointer relationship.
4. Symlinks, path replacement, inode replacement, linked-worktree `.git` files,
   submodules, replace/grafts/shallow/promisor/filter/lazy-fetch, hooks, fsmonitor,
   autostash, and child-process lock inheritance.
5. Whether any failure path mutates foreign artifacts, partially mutates main, or
   reports success without exact tested-main/tested-tip/audited-commit evidence.
6. Whether `already-landed`, `stale`, `busy`, `rejected`, and postcondition failure
   are distinct and fail closed.

Do not ask for broad hardening outside the cooperative same-host dev-wave threat
model unless it changes the requested artifact: safe, noncontact, ff-only local-main
integration for parallel Claude/Codex sessions. For every finding, give severity,
exact file/line, a concrete interleaving or exploit, and the artifact/acceptance-set
impact required by DW-G05. Mark speculative or out-of-scope points explicitly.

End with `## 総括` and exactly one verdict: `GO` or `NO-GO`.
