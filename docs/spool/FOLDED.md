# fold receipt (追記のみ)

fold 済み fragment の耐久記録。**`tools/spool_fold.py` だけが追記する。人が編集しない。**

同一内容の fragment が別のファイル名で再投入されたとき、それを replay として拒否するために使う
(receipt が無いと、fold 済みの内容が新しい ID で二重採番される)。

各行は 1 fragment に対応する JSON object の bullet で、`content-sha`・identity・採番結果を持つ。

## records

- {"allocations":{"T:deferred-active-id-overlap":"[T-356]","T:spool-authoring-cli":"[T-354]","T:spool-canonical-write-gate":"[T-350]","T:spool-completion-semantics":"[T-352]","T:spool-fold-crash-recovery":"[T-348]","T:spool-fold-plan-verification":"[T-347]","T:spool-mutation-attribution":"[T-349]","T:spool-mutation-wiring":"[T-355]","T:spool-receipt-hardening":"[T-353]","T:spool-rulings-collection":"[T-351]"},"authored":"2026-08-02","content_sha256":"cd97c323f72d6122e7081dcbb889f59d7d4e4218d36ca5fbba73d1fd64b3bd50","seq":1,"wave":"dev-wave-parallel-docs-spool"}
- {"allocations":{"D:dev-wave-budget-raise":"D129","D:parallel-doc-spool":"D128"},"authored":"2026-08-02","content_sha256":"7fb77c6164150b577db7d801f148ef1744e1ff6c272c440ae4ff557b903b3c11","seq":2,"wave":"dev-wave-parallel-docs-spool"}
- {"allocations":{"F:green-suite-cannot-run-on-real-repo":"F81","F:guard-expectation-inversion":"F80","F:guard-forbids-its-own-input":"F82","F:parent-ruling-forces-serial-only":"F83"},"authored":"2026-08-02","content_sha256":"7bc72d43087b735822da18f3faaf0041fcdb5af2353e9075f7efdf87332dc1f0","seq":3,"wave":"dev-wave-parallel-docs-spool"}
