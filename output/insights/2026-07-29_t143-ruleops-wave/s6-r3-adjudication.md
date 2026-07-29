# Stage 6 focused re-review adjudication — round 3

## Verdict

The round-2 focused re-review NO-GO is accepted. The pre-round-3 integrated
state is preserved in `s6-r3-pre-fix-integrated.patch`.

Both findings are real and form the final bounded repair unit. Mutation remains
blocked until a final focused re-review closes them without regressing the
previous 21 closed rows.

## Accepted

- RR-1: the receipt epoch must cover the union of paths touched by every commit
  in `receipt_head..snapshot.head`, not only the net endpoint tree difference.
  Add an independent negative where an unrelated path changes and is reverted.
- R2R-1: every Git subprocess must receive `GIT_NO_LAZY_FETCH=1`. Add a
  synthetic non-shallow promisor repository with a missing promised blob and a
  poisoned local helper; prove RuleOps fails closed without invoking the helper
  or mutating Git metadata.

## Preserved scope

- Keep all previously closed RA/RB/RR rows closed.
- No index/staged-tree binding.
- No D97 `PYTEST_ADDOPTS` classifier change.
- No task-run recording for preflight refusal.
- No mutation producer, deletion action, approval, or safety claim.
