# Stage 6 focused re-review adjudication — round 2

## Verdict

The focused re-review NO-GO is accepted. The pre-round-2 integrated state is
preserved in `s6-r2-pre-fix-integrated.patch`.

All five partial findings and both new MUST findings are real. They remain one
fix unit because history-epoch validation, receipt/ledger control identity,
global signal budgeting, and the maximum-package test all share the same
candidate-package snapshot boundary.

## Accepted

- RA-2: repeat the non-shallow, replace-ref, and graft boundary at result
  emission, not only HEAD identity.
- RA-8: reject or withhold control privilege for an oversize HEAD ledger blob
  before any blob read.
- RA-9 / RB-5: make the real-checkout non-empty package independent of
  production `inspect` output. Build its target, signal, and history oracle
  from controlled committed content plus independent Git/literal values.
- RB-2: cache raw pickaxe history by snapshot/token before per-candidate
  control filtering, enforce a global signal-token budget before history work,
  and test the largest accepted package through the 60-second runner boundary.
- RR-1: require the receipt head to be an existing ancestor commit whose tree
  contains the candidate blob. Between that head and the checked snapshot,
  permit changes only to the ledger and the ledger-wide set of pinned receipt
  paths; reject unrelated changes.
- RR-2: reject the ledger path when it aliases any receipt, replacement guard,
  replacement node module, or insight source path. Keep a separate custom
  ledger positive control.

## Preserved scope

- No index/staged-tree binding.
- No D97 `PYTEST_ADDOPTS` classifier change.
- No task-run recording for preflight refusal.
- No mutation producer, deletion action, approval, or safety claim.

## Re-review requirement

After the round-2 fix and docs synchronization, repeat the same focused
closed/partial/regressed review. Mutation remains blocked until every accepted
row is closed and no new BLOCKER/MUST remains.
