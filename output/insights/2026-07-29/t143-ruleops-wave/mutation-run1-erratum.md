# T-143 RuleOps mutation run 1 erratum

Final base at start: `8976c14aa585bc47278ec5d6637edbb105bfe6e5`.

- M1 test-scope-empty: KILLED by
  `test_m1_m2_inventory_literal_scope_and_exact_keys`.
- M2 insight-scope-output-wide: KILLED by the same literal scope node.
- M3 HEAD-size-to-worktree-stat: **SURVIVED**, but this was an invalid
  injection. The manager changed `_inventory_item`, which is the `inspect`
  construction path, while the preregistered inventory gate is the separate
  item construction inside `build_inventory`.
- Initial diagnosis said the dirty replacement and committed candidate had
  equal byte lengths. Direct literal measurement refuted that diagnosis:
  committed candidate = 56 bytes, old dirty replacement = 38 bytes. The
  fixture was nevertheless strengthened to assert independent content and
  length inequality, but the run-1 survival was caused by the wrong anchor.

Per DW-M02/DW-M04/DW-M07 this run is not counted as final. The final run
retargeted M3 to `build_inventory`, verified the single tracked diff, and
reran the complete matrix from the new final implementation commit.
