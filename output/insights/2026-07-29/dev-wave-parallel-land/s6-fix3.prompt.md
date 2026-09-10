# Stage 6 author fix round 3/3: two final residuals

You are the final allowed Codex `role=author` fix unit for this wave. Work only in:

`/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-skill`

The index is the post-fix-2 snapshot. Do not stage, reset, restore, commit, or edit
the index. Exclusive editable files are exactly:

- `tools/dev_wave_land.py`
- `orchestrator/tests/test_dev_wave_land.py`
- `tools/check_docs.py`
- `orchestrator/tests/test_check_docs.py`

No other edit, docs edit, commit, config/submodule mutation, or network. Read
CLAUDE.md, DW-S05-A/B/C, DW-S06-A/B/C, DW-G05, DW-O16, the two latest re-reviews,
`s6-adjudication.md` through the round-3 ruling, and all owned code/tests/diffs.

Close only:

1. Gitlink-to-normal-entry mode change:
   - distinguish a pure removed gitlink from an A gitlink path that T replaces with
     a normal blob/tree;
   - for replacement, allow the intended T normal entry after land while requiring
     old submodule worktree identity and `.git/modules/<path>` metadata cleaned;
   - for pure deletion, continue requiring both path and metadata absent;
   - add a same-A/T/audited-evidence test: first post-land failure, cleanup, then
     `already-landed`, plus a residual-metadata rejection.
2. Obvious command detection with global/interpreter options:
   - command-like lines must detect a land-named `tools/*.py` token reached through
     `python`/`python3` despite options such as `-u`, `-B`, `-W ignore`;
   - detect `git ... merge ... --ff-only` despite global options such as
     `--no-pager`, `-c key=value`, `-C <path>` and their normal ordering;
   - prefer token/line structure or a broad command-line grammar over enumerating
     one exact option sequence;
   - add independent negatives for `python3 -u tools/alternate_land.py`,
     `python -B -W ignore ./tools/alternate_land.py`,
     `git --no-pager -C main merge --ff-only T`, and
     `git -c advice.detachedHead=false -C main merge T --ff-only`;
   - keep ordinary inline prose and non-ff/non-land commands green.

All DW-S05 constraints remain: no xfail/test weakening/volatile hashes/scope
expansion; exact red/green and outside-consumer report. Run the same direct,
combined, plain/meta, check_docs, check_codex_agents, compile, and diff checks as
round 2. End with `## 総括`.
