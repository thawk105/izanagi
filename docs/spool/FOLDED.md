# fold receipt (追記のみ)

fold 済み fragment の耐久記録。**`tools/spool_fold.py` だけが追記する。人が編集しない。**

同一内容の fragment が別のファイル名で再投入されたとき、それを replay として拒否するために使う
(receipt が無いと、fold 済みの内容が新しい ID で二重採番される)。

各行は 1 fragment に対応する JSON object の bullet で、`content-sha`・identity・採番結果を持つ。

## records

- {"allocations":{"T:deferred-active-id-overlap":"[T-356]","T:spool-authoring-cli":"[T-354]","T:spool-canonical-write-gate":"[T-350]","T:spool-completion-semantics":"[T-352]","T:spool-fold-crash-recovery":"[T-348]","T:spool-fold-plan-verification":"[T-347]","T:spool-mutation-attribution":"[T-349]","T:spool-mutation-wiring":"[T-355]","T:spool-receipt-hardening":"[T-353]","T:spool-rulings-collection":"[T-351]"},"authored":"2026-08-02","content_sha256":"cd97c323f72d6122e7081dcbb889f59d7d4e4218d36ca5fbba73d1fd64b3bd50","seq":1,"wave":"dev-wave-parallel-docs-spool"}
- {"allocations":{"D:dev-wave-budget-raise":"D129","D:parallel-doc-spool":"D128"},"authored":"2026-08-02","content_sha256":"7fb77c6164150b577db7d801f148ef1744e1ff6c272c440ae4ff557b903b3c11","seq":2,"wave":"dev-wave-parallel-docs-spool"}
- {"allocations":{"F:green-suite-cannot-run-on-real-repo":"F81","F:guard-expectation-inversion":"F80","F:guard-forbids-its-own-input":"F82","F:parent-ruling-forces-serial-only":"F83"},"authored":"2026-08-02","content_sha256":"7bc72d43087b735822da18f3faaf0041fcdb5af2353e9075f7efdf87332dc1f0","seq":3,"wave":"dev-wave-parallel-docs-spool"}

- {"allocations":{},"authored":"2026-08-02","content_sha256":"38bee18b96361b81d994ac08286808e94a9b8e224e8aba2b8241e3ff382baa51","seq":1,"wave":"rulings-2026-08-02-d"}

- {"allocations":{},"authored":"2026-08-02","content_sha256":"a16223580796ba5bb03df37cc4ab9ab2c285d34ba43f7f6ff594b6a6d6a3085a","seq":1,"wave":"rulings-2026-08-02-e"}
- {"allocations":{"T:fold-rotation-copy-detection":"[T-357]"},"authored":"2026-08-02","content_sha256":"71d9573af91b78f90cd2ddfaa059459baff8e088bb59aae50eac8ace2ed1e812","seq":2,"wave":"rulings-2026-08-02-e"}
- {"allocations":{},"authored":"2026-08-02","content_sha256":"5b4a6210a203d8bd6820121bde541f14e65badaceff3b3ddea462816491c499c","seq":3,"wave":"rulings-2026-08-02-e"}
- {"allocations":{"T:fold-deferred-firing-record":"[T-358]"},"authored":"2026-08-02","content_sha256":"b766418e00caee979cb75e4d44ec5706e909798cdf521bb51c9efd9e81584ecc","seq":4,"wave":"rulings-2026-08-02-e"}
- {"allocations":{},"authored":"2026-08-02","content_sha256":"6a33c6230d22d8b7c4d3087bc8bf14f4bd2afa8f619b8f3d92913786129ede92","seq":5,"wave":"rulings-2026-08-02-e"}
- {"allocations":{"T:dev-wave-reference-budget-overflow":"[T-359]"},"authored":"2026-08-03","content_sha256":"a7771cdaa972102def29129386102e8d3baf25792e5d5ccb97fbc221afdce80c","seq":1,"wave":"worktree-dev-wave-fold-rotation-copy"}

- {"allocations":{"T:cross-node-flock-probe":"[T-361]","T:dispatch-total-deadline-queue-wait":"[T-363]","T:mutation-collection-parallelism":"[T-364]","T:mutation-transport-bundle":"[T-360]","T:nqsv-walltime-signal-probe":"[T-362]"},"authored":"2026-08-03","content_sha256":"0d984ea8eab49a5d61db86e7fe08d305ea20190cffcc3e0783918cc41c35ac2c","seq":1,"wave":"worktree-dev-wave-t357-mutation-batch"}
- {"allocations":{"D:mutation-transport-bundle-smoke":"D130","D:mutation-transport-ruling-package":"D131"},"authored":"2026-08-03","content_sha256":"f0178fc1f72121f6a56ca74563765a34b8573ed8ef7e4aaaf5db40ebf147bd8f","seq":1,"wave":"worktree-dev-wave-t357-mutation-batch"}
- {"allocations":{"F:bundle-launcher-env-normalization":"F84"},"authored":"2026-08-03","content_sha256":"61092fad7d01a312ff69c171e016ab89b1fd7f5a156dd0e5e5193f333b00251a","seq":1,"wave":"worktree-dev-wave-t357-mutation-batch"}

- {"allocations":{},"authored":"2026-08-03","content_sha256":"f05d442d254306f07fe1a699c278288e4189f58437eda4f96ebb6f737c06bbe4","seq":1,"wave":"rulings-2026-08-03-a"}

- {"allocations":{},"authored":"2026-08-03","content_sha256":"91c398edcd92f5d69a992fb4436db0cfc85ef72f06921819ec599d5d9e0672bf","seq":1,"wave":"rulings-2026-08-03-b"}
