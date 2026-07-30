# Stage 6 adversarial review: contract, minimality, and test independence

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

Review through the shared-contract, minimality, and independent-test lens. Attack:

1. Whether Claude and Codex really route through one common Stage 9 operation
   without adapter drift or a hidden second normal main-mutation path.
2. Whether the roughly 1000-line helper is justified by the safety contract, or
   contains duplicative/dead machinery that can be removed without weakening it.
3. Whether tests independently specify behavior or merely mirror implementation
   constants/helpers; identify vacuous, overdetermined, transitional, or missing
   cases. In particular assess the temporary six-finding allowance in
   `test_real_repo_clean` now that parent docs are integrated.
4. Whether `check_docs` pins the intended section/path topology without broadening
   unrelated consumers or making checker and fixture share the same bug.
5. Whether docs accurately say that valid foreign control-plane artifacts are
   noncontact exceptions, unknown dirt is rejected, main movement requires a fresh
   context, and push/remote/rebase/force stay forbidden.
6. Whether the implementation adds behavior beyond the user-approved scope or
   weakens existing strict cleanliness gates such as `.gitignore` consumers.

For every finding, give severity, exact file/line, a minimal correction, and the
artifact/acceptance-set impact required by DW-G05. Do not label style-only or
out-of-scope simplification as must-fix. Call out any self-consistent checker/test
bug that could make both green while the user contract is wrong.

End with `## 総括` and exactly one verdict: `GO` or `NO-GO`.
