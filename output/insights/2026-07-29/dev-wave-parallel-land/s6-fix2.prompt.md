# Stage 6 author fix round 2: focused residuals

You are the second and final planned Codex `role=author` fix unit for this Izanagi
dev-wave. Work only in:

`/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-skill`

The index contains the post-fix-1 integrated snapshot. Do not stage, reset, restore,
commit, or edit the index. Leave changes unstaged against it.

Exclusive editable ownership remains exactly:

- `tools/dev_wave_land.py`
- `orchestrator/tests/test_dev_wave_land.py`
- `tools/check_docs.py`
- `orchestrator/tests/test_check_docs.py`

Do not edit any docs, Skill, command, handoff, insight, other fixture, Git config,
submodule, or other path. No commit and no network.

Read `CLAUDE.md`, DW-S05-A/B/C, DW-S06-A/B/C, DW-G05, DW-O01..O06,
DW-O08..O20, DW-O23, DW-M02..M08, then:

- both original Stage 6 reviews
- `s6-adjudication.md`, including “焦点再レビュー後の第 2 fix 裁定”
- `s6-fix.md`
- `s6-rereview.md`
- the four owned files, staged snapshot, and current status

Close exactly the five adopted residuals:

1. Ignored collision precision:
   - Keep rejecting an actual existing ignored file/directory that target would
     replace, delete, or contain.
   - Do not reject target `cache/new.txt` merely because existing ignored sibling
     `cache/a.bin` was collapsed by status to `!! cache/`.
   - Add both the sibling positive and exact/ancestor collision negatives.
2. Revalidate the full control snapshot after target/collision inspection and
   immediately before invoking merge. If it differs from the earlier snapshot,
   fail closed without mutation. Add a wrapper/seam test that replaces a handoff or
   worktree after collision inspection but before merge and proves main unchanged.
3. Gitlink deletion recovery:
   - Compute both A and T gitlink maps.
   - On same-evidence rerun at T, require every target gitlink synchronized and every
     A-only removed gitlink worktree/nested Git metadata absent.
   - Add deletion tests proving residual path rejects and cleanup permits
     `already-landed`; do not launder A/T/audit.
4. Checker syntax coverage:
   - Catch obvious alternate land helper commands with/without `$`, with `python` or
     `python3`, and `tools/` or `./tools/`.
   - Catch direct ff commands including `git -C <main> merge ... --ff-only` and
     option order variants.
   - Add independent negatives for these variants and a prose positive to avoid
     overmatching ordinary explanation.
5. Acceptance connection:
   - Replace the in-process marker with an actually executed subprocess acceptance
     command in the synthetic repo. It must validate winner and loser content,
     exact HEAD/tree, and cleanliness, then emit a receipt.
   - Retry request must consume receipt tested-main/tested-tip; assert receipt tree
     equals the resynced tip tree.
   - Add a docs checker literal pin in common S09 for the existing order “all
     commits/acceptance results fixed, measure tested main/tip and audit list, then
     perform O23”. Add a negative test deleting that literal. Do not edit the docs;
     use the exact currently integrated text.

DW-S05 inheritance remains in force: code/tests only, no commit, no xfail, no test
weakening, no volatile hash expectations, no scope expansion, and exact red/green
reporting. Parent docs are integrated and `check_docs` must be unconditionally
green. Report outside consumers/fixtures that may be affected.

Run at minimum the same direct, combined, plain-runner/meta, docs, Codex-agent,
compile, and diff checks as fix round 1. Finish with changed files, exact results,
residual risk, and `## 総括`.
