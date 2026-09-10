# Stage 6 adjudication — T-143 RuleOps

## Verdict

NO-GO. Both independent post-implementation reviews are accepted as substantive.
The integrated pre-fix state is preserved in
`s6-pre-fix-integrated.patch`.

The accepted findings form one fix unit because the Git snapshot boundary,
control-artifact treatment, evidence schema, candidate validation, runtime
budget, and their negative tests share the same RuleOps trust boundary.
Splitting them would leave intermediate states that appear usable but are
neither safely read-only nor operationally checkable.

## Accepted for the fix unit

- Disable repository-local signature, external-diff, textconv, and recursive
  submodule execution surfaces; add a poisoned-local-config regression.
- Capture one HEAD object ID, bind every inventory and evidence query to it,
  and reject a HEAD change observed before emitting a result.
- Treat pathspecs literally and stop broad history exclusions from allowing a
  control filename to hide earlier non-control history.
- Reject ledger/target aliasing. A tracked control artifact is trusted only
  after its HEAD blob has been checked as a strict RuleOps artifact; an
  untracked draft is never silently granted control-artifact exclusion.
- Replace permissive first-64-lines marker scanning with a strict,
  byte-leading marker grammar. Reject quoting, fencing, duplication, and
  non-strict JSON.
- Validate stripped, control-free rationale/query strings. For test
  replacement claims, verify the advisory symbol exists and cross-check the
  receipt node, target, review state, guard result, and failed-node evidence.
- Make evidence overflow explicit and bound reads before full decoding.
- Replace self-derived test oracles with literal expectations and repair the
  M5/M6/M8 fixtures so each advertised reason is independently exercised.
- Emit a complete advisory mutation-receipt draft from inspection and test the
  documented inspect → candidate → check route.
- Memoize repeated snapshot/evidence work, bound candidate/query cardinality,
  and prove a non-empty check stays inside the runner's 60-second preflight
  budget.
- Remove the runner's duplicate default-ledger constant and rely on the
  RuleOps CLI default.
- Normalize CLI argument failures into the documented stable error envelope.
- Strengthen a checkout-level dry run so it proves a non-empty known hit and a
  complete non-empty candidate flow rather than only checking exit status and
  a kind label.

## Deferred, with scope preserved

- Index/staged-tree binding is not added in this wave. RuleOps remains an
  advisory HEAD-snapshot proposal mechanism, not a staged-deletion verifier.
- The pre-existing `PYTEST_ADDOPTS` acceptance-bypass surface belongs to the
  shared D97 option classifier, not RuleOps. It needs a separate task.
- Recording preflight refusal as an individual task-run result is a runner
  observability change and is deferred separately.

## Re-review requirement

After the single fix unit, run focused independent review against every
accepted item above. No mutation or acceptance stage may start while either
focused reviewer leaves a blocker or must-fix finding open.
