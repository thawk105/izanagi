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

- {"allocations":{},"authored":"2026-08-03","content_sha256":"29aa3202b41f594be5075fb3f12d0f99545ab75c4f9069d0a8f34b17d098cc93","seq":1,"wave":"dev-wave-t296-layer-c-calibration"}

- {"allocations":{"T:fold-signature-completeness":"[T-365]","T:supervised-land-cutoff":"[T-366]"},"authored":"2026-08-03","content_sha256":"d32e618476419626f9b282a933ee70f08fe0ef50c75c3816f2b48cf1e04ffd4c","seq":1,"wave":"dev-wave-land-merge-signature"}
- {"allocations":{"D:land-signature-outside-trusted-cutoff":"D132"},"authored":"2026-08-03","content_sha256":"9926e972272c5d04cccd4b769dc5436dc7e36b3f38a751e3b5e57fff274bb5de","seq":2,"wave":"dev-wave-land-merge-signature"}
- {"allocations":{},"authored":"2026-08-03","content_sha256":"4e874ed400eb217d959fc8c5d068264e4c858290997f0dc63ba57280d6a27f80","seq":3,"wave":"dev-wave-land-merge-signature"}

- {"allocations":{"T:active-job-qdel-prohibition":"[T-367]","T:dev-wave-child-test-execution-contract":"[T-369]","T:dispatch-timeout-input-validation":"[T-370]","T:running-job-state-evidence":"[T-368]"},"authored":"2026-08-03","content_sha256":"7d9cc592d8311f571e4c63e1ac5f929bbb82c5c4622dd3f74f64d13e5bc461ff","seq":1,"wave":"dev-wave-t363-deadline"}
- {"allocations":{"D:run-observation-deadline":"D133"},"authored":"2026-08-03","content_sha256":"cd85fa5a70a9ab5dee78bb46e4d314779cf0933c3c2cce5ac163902ed96e6b74","seq":2,"wave":"dev-wave-t363-deadline"}
- {"allocations":{"F:diagnostic-only-mutation-counted-as-kill":"F86","F:untrusted-run-latch-poisoning":"F85"},"authored":"2026-08-03","content_sha256":"5daa65e3be52edd7dba96811a8e916b4c12f4c9f54e81f0b4e0ea0afbdfd65ab","seq":3,"wave":"dev-wave-t363-deadline"}

- {"allocations":{},"authored":"2026-08-03","content_sha256":"10c157d7c2177eb5563f2004ee7f25aa558c9c7a490a402e8f49e331e89ea8fe","seq":1,"wave":"dev-wave-t338-rf-statdesign"}
- {"allocations":{"D:rf-statdesign-package":"D134"},"authored":"2026-08-03","content_sha256":"37c23ce027db0bf8c4a916d56926d7bf6940abf1627b7a402daae6f0848c716a","seq":2,"wave":"dev-wave-t338-rf-statdesign"}
- {"allocations":{},"authored":"2026-08-03","content_sha256":"54dcc8f90749feeb95dbfad4578f299665d5590e30c2bd01330238a739e6c500","seq":3,"wave":"dev-wave-t338-rf-statdesign"}

- {"allocations":{"T:codex-launch-fake-flake":"[T-377]","T:devwave-m01-shrink-mutation-enumeration":"[T-375]","T:devwave-s01-provisional-refutation-probe":"[T-376]","T:effort-vocabulary-subset-binding":"[T-372]","T:model-reasoning-compat-gate":"[T-371]","T:profile-effort-early-check":"[T-374]","T:task-runs-reasoning-validity":"[T-373]"},"authored":"2026-08-03","content_sha256":"7648a74030a2ad38bfe476caebe0ffe6b94e5fcf4e220ca64bc43c018defaafd","seq":1,"wave":"dev-wave-t189-reasoning-allowlist"}
- {"allocations":{"D:effort-allowlist-inside-supervisor-digest":"D135"},"authored":"2026-08-03","content_sha256":"cef16ab8ed93c041ed810bba3a2e28308b6773338de807b224720953cfa93f9c","seq":2,"wave":"dev-wave-t189-reasoning-allowlist"}
- {"allocations":{"F:positive-mutation-node-enumeration":"F87"},"authored":"2026-08-03","content_sha256":"35f37e81daded8d838a16f1051b13ee168ea1ff9e99ce89fc032cf7cc90a5a79","seq":3,"wave":"dev-wave-t189-reasoning-allowlist"}

- {"allocations":{"T:admission-issuer-trust-boundary":"[T-378]","T:dev-wave-patch-baseline-and-runner-host":"[T-386]","T:historical-artifact-reclassification":"[T-381]","T:immutable-source-snapshot":"[T-384]","T:materializer-closure-shell":"[T-379]","T:mutation-reaim-m02-m08-m11":"[T-385]","T:no-build-attempt-canonical-form":"[T-387]","T:s8b-refreeze-receipt-chain":"[T-383]","T:t126-control-remeasurement":"[T-382]","T:transitive-provenance-freeze":"[T-380]"},"authored":"2026-08-03","content_sha256":"d3d35e380a4f9b1f4cf17e8cebc6fae51a87cc6f549c1eff7245579da91d9df1","seq":1,"wave":"dev-wave-t342-344-provenance"}
- {"allocations":{"D:provenance-capability":"D136"},"authored":"2026-08-03","content_sha256":"5da4015117c0db8c9761b4572a6d4af679cf0351b1404b21c805cc4dafc3b3ce","seq":2,"wave":"dev-wave-t342-344-provenance"}

- {"allocations":{},"authored":"2026-08-03","content_sha256":"14e86826e564a356beb5aaee639ee3a8f421803abffea8fc7c296f48e3f4b2b5","seq":1,"wave":"dev-wave-t313-read-budget"}
- {"allocations":{},"authored":"2026-08-03","content_sha256":"6d5781e3f7bd01d54325233a29dd8ea7b613202a97b8ae5bba82c7583851a2e7","seq":2,"wave":"dev-wave-t313-read-budget"}

- {"allocations":{},"authored":"2026-08-03","content_sha256":"588251e77feffabebb9d9c29800f3b97c479581d8901fd171865cf0514c85bd5","seq":1,"wave":"rulings-2026-08-03-c"}

- {"allocations":{},"authored":"2026-08-03","content_sha256":"d1055e8fdff60cd713f1cb40317d85b0fba78394a9eb4392b1fa2e0c41a67795","seq":1,"wave":"rulings-2026-08-03-d"}

- {"allocations":{},"authored":"2026-08-03","content_sha256":"028fa5a334105c0b776007b1deed6aa0bdfd146126f05e82339a108085c7b145","seq":1,"wave":"rulings-2026-08-03-e"}

- {"allocations":{},"authored":"2026-08-03","content_sha256":"ae6ef36877be5e24de9db7e6339388f6c8df3aabd72f2518c38820226462e936","seq":1,"wave":"rulings-2026-08-03-f"}

- {"allocations":{},"authored":"2026-08-03","content_sha256":"739d824f486924d860d4c29c5b57795b6ae6f2599c2767af46dd0c2257ec0fbf","seq":1,"wave":"rulings-2026-08-03-g"}

- {"allocations":{},"authored":"2026-08-03","content_sha256":"5ebd74ff64db1310ad6bc2776faaed52cb679adf933d9603514fc4afa51c92a4","seq":1,"wave":"rulings-2026-08-03-h"}

- {"allocations":{"F:compute-node-default-python-is-oneapi":"F88","F:python-and-shell-executable-acceptance-diverge":"F89"},"authored":"2026-08-03","content_sha256":"3a1fd1fb2277aed2f582e5b5a69753c3d07c834459301e18f039b81a0a472cc5","seq":1,"wave":"dev-wave-t293-perf-site"}
- {"allocations":{"D:two-sided-control-for-gateless-measurement":"D137"},"authored":"2026-08-03","content_sha256":"fb897941ed2b60cde65eed9f43c1daae42ff22761dd658bf6b19ed150c6fa2d6","seq":2,"wave":"dev-wave-t293-perf-site"}
- {"allocations":{"T:land-window-vs-acceptance":"[T-389]","T:output-snapshot-test-flake":"[T-388]"},"authored":"2026-08-03","content_sha256":"4490a59485358aaf5b9c44457437cc33513180565ab95b9eab5242def77fcb8b","seq":3,"wave":"dev-wave-t293-perf-site"}

- {"allocations":{"T:d122-optin-retirement":"[T-390]"},"authored":"2026-08-03","content_sha256":"c62232f63ebe3c3be9696b56fb1806027384f1761a4033ba2674a1e1ea7c708e","seq":1,"wave":"rulings-2026-08-03-i"}

- {"allocations":{"T:dispatch-condition-verbatim-gate":"[T-391]","T:land-without-check-receipt":"[T-393]","T:qsub-interpreter-contract":"[T-395]","T:reference-preamble-unreachable":"[T-392]","T:supervisor-dwctx-unwired":"[T-394]"},"authored":"2026-08-03","content_sha256":"f2caf24448c840621abbccbd6d41f6e3e7ca1453675f073760e4800505752a4c","seq":1,"wave":"dev-wave-t328-docs-externalize"}
- {"allocations":{},"authored":"2026-08-03","content_sha256":"59062836230a95e3fe066b822e98cb981796c22f336c6e13aa0a33b21cb5a012","seq":2,"wave":"dev-wave-t328-docs-externalize"}

- {"allocations":{},"authored":"2026-08-03","content_sha256":"f36202a292b2842bae3d274e5dc02e47d4fcd2d4828cfa8f0e914d0acbf4ad9e","seq":1,"wave":"dev-wave-task-inventory"}

- {"allocations":{"T:placeholder-gate-recursion":"[T-398]","T:sort-integrity-witness":"[T-397]","T:trigger-gating-ast-allowlist":"[T-396]"},"authored":"2026-08-04","content_sha256":"26f92431e71090c8aeee302188f5266c9b548f32a327786f77ed8464ba8cfeac","seq":1,"wave":"dev-wave-t244-p6-contract"}
- {"allocations":{"D:p6-inductive-contract":"D138"},"authored":"2026-08-04","content_sha256":"c25095af63bd4871facf99ead5c10192439db6f56e507401b5356b82f121530a","seq":2,"wave":"dev-wave-t244-p6-contract"}
- {"allocations":{"F:placeholder-gate-nonrecursive":"F90"},"authored":"2026-08-04","content_sha256":"c300bf9f2ca8b278b3b335effc5c227bf985480ea9d37d3171a6da6eec4d86f6","seq":3,"wave":"dev-wave-t244-p6-contract"}

- {"allocations":{"T:admissibility-splits-danger":"[T-400]","T:racct-lag-admissibility":"[T-401]","T:t361-execution-host-confirm":"[T-402]","T:t362-mitigation-leg":"[T-399]"},"authored":"2026-08-04","content_sha256":"8c28ba5f92e30ff0456ccfeb3f2496295afb3abd2c10dcdf9debc8d0dad5bdaf","seq":1,"wave":"dev-wave-t361-362-probes"}
- {"allocations":{"D:probe-controller-owns-submission":"D141","D:t361-cross-node-flock-blocked":"D140","D:t362-walltime-sigkill":"D139"},"authored":"2026-08-04","content_sha256":"11b847b3c774f623c9531fc6225ca0b25cfea20c614814dabcf3fdd178f867e6","seq":2,"wave":"dev-wave-t361-362-probes"}
- {"allocations":{"F:admissibility-conjunct-rejects-danger":"F93","F:controller-no-recovery-path":"F92","F:parent-underestimated-cleanup-cost":"F91","F:static-checks-missed-undefined-name":"F94"},"authored":"2026-08-04","content_sha256":"f3b060dafc2ceb29f932416a4931677b6fd838112497e2125497817f893f7fa4","seq":3,"wave":"dev-wave-t361-362-probes"}
