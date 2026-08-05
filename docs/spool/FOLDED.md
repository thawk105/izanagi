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

- {"allocations":{"T:guarded-qdel-proof-chain":"[T-405]","T:orphan-job-reconciliation":"[T-403]","T:qdel-target-discovery-identity":"[T-404]","T:receipt-persist-signal-window":"[T-406]","T:ruleops-non-utf8-blob-red":"[T-407]"},"authored":"2026-08-04","content_sha256":"b00bf4b306a4137f64bc096f677b92c161a3ac6f18a33ab3000dccbb3fc19b64","seq":1,"wave":"wave-t367-qdel-guard"}
- {"allocations":{"D:fresh-qstat-gate-scope":"D142"},"authored":"2026-08-04","content_sha256":"410a8dacb939a86bb225c1c0fff08e8d39d8f877d9e606e8b77936f6cff63539","seq":2,"wave":"wave-t367-qdel-guard"}

- {"allocations":{},"authored":"2026-08-04","content_sha256":"7f80e82b700387cdc41dc61c7ecc42559cc7fb6a04f40b740b66b2d98a2cb73b","seq":1,"wave":"rulings-2026-08-04-a"}

- {"allocations":{"T:executable-symlink-parity":"[T-408]"},"authored":"2026-08-04","content_sha256":"a78da45ccaa59c17387b8cea94e2abcd52a5fcd5644473cf9ea0ad6de94210d7","seq":1,"wave":"rulings-2026-08-04-b"}

- {"allocations":{"T:evolve-hole-ast-allowlist":"[T-409]","T:sort-axis-integrity-witness":"[T-410]"},"authored":"2026-08-04","content_sha256":"6f96890e457ab8da57f1b37772836bc01f1a2a9d2b2451de0ac76ddb9503d2e6","seq":1,"wave":"rulings-2026-08-04-c"}

- {"allocations":{},"authored":"2026-08-04","content_sha256":"38d060ca38b421eb184964561b83d5ee16ddf21742c49d97c37e723ef45fe48c","seq":1,"wave":"rulings-2026-08-04-d"}

- {"allocations":{},"authored":"2026-08-04","content_sha256":"d99e35646e21501ef1ea174d3a19873a13ca5f54dfa036e39988f0463382da9b","seq":1,"wave":"rulings-2026-08-04-e"}

- {"allocations":{"T:dev-wave-l2-pruning":"[T-412]","T:t287-rulings-reflection":"[T-411]"},"authored":"2026-08-04","content_sha256":"2f71b8cd8a132adf314bd8deed2e2921613d2fe877421fba46aeb283a5507092","seq":1,"wave":"rulings-2026-08-04-f"}

- {"allocations":{},"authored":"2026-08-04","content_sha256":"a9121e7ad6e7b45609896bedef785942a8a1f9b862fa534e0291ad96fd321282","seq":1,"wave":"rulings-2026-08-04-g"}

- {"allocations":{"T:rulings-claim-verification":"[T-413]"},"authored":"2026-08-04","content_sha256":"5b82b4513fe0d88494d2547ba806345a3b1e7c9b5db120b865d73ddc31beb669","seq":1,"wave":"rulings-2026-08-04-h"}

- {"allocations":{"T:mutation-harness-node-normalization":"[T-417]","T:t287-checkpoint-integrity":"[T-416]","T:t287-error-message-redaction":"[T-418]","T:t287-layer3-reader":"[T-415]","T:t287-producer-domain":"[T-414]"},"authored":"2026-08-04","content_sha256":"a48cfa60ee02930450fa8c8b95e16b3ebf2dbf3c87c0a61840be6ae81c61b665","seq":1,"wave":"dev-wave-t287-checkpoint-values"}
- {"allocations":{"F:mutation-harness-realrepo-node":"F95"},"authored":"2026-08-04","content_sha256":"3f406e81f057d2b6f4ff17136e8db6d2a7862bcdba05bbde3d5a73acefdc4d27","seq":2,"wave":"dev-wave-t287-checkpoint-values"}
- {"allocations":{"F:nonutf8-evidence-blob-lands-red":"F96"},"authored":"2026-08-04","content_sha256":"301c27b0776dd1198f49b0327c4fa36229f978230738b57acb3e2d5b4b8ecd13","seq":3,"wave":"dev-wave-t287-checkpoint-values"}

- {"allocations":{"F:campaign-run-blocks-wave-land":"F98","F:pegasus-attestation-self-rejecting":"F97","F:qsub-positional-args-invented":"F99"},"authored":"2026-08-04","content_sha256":"1f5be4a32eb7070a6eb150bde252012caea92898499e88eac2c9aa63f826a457","seq":1,"wave":"wave-a-transport-smoke"}
- {"allocations":{"D:pegasus-attestation-blocks-wall1":"D143","D:pegasus-numactl-single-node":"D144"},"authored":"2026-08-04","content_sha256":"a56f0ee6f799aa01599b331f13d55ddfd3d95643beaf46d693a7c943217a2ee3","seq":2,"wave":"wave-a-transport-smoke"}
- {"allocations":{"T:pegasus-attestation-ruling":"[T-419]","T:pegasus-s2-numactl-proxy":"[T-421]","T:ruleops-nonutf8-artifact":"[T-423]","T:wall1-transport-recheck":"[T-420]","T:wave-land-vs-campaign-guard":"[T-422]"},"authored":"2026-08-04","content_sha256":"24522a775f04ead06af5bfab5fec99e8e7d6202b687b7e90d07f3d646a2b8765","seq":3,"wave":"wave-a-transport-smoke"}

- {"allocations":{},"authored":"2026-08-04","content_sha256":"7d4e792db89d71de136eb9ff950f56b18cfd9217d0f51544f2888a1777076ab6","seq":1,"wave":"rulings-2026-08-04-i"}

- {"allocations":{"T:between-run-floor-window-design":"[T-425]","T:certify-job-script-binding":"[T-424]"},"authored":"2026-08-04","content_sha256":"ba43fe6f2f09f9bbf939b7f1fd4f6120c4a7d2cebd45808c17a083a90d16892c","seq":1,"wave":"wave-t088-floor"}
- {"allocations":{"D:between-run-floor-cohort":"D145"},"authored":"2026-08-04","content_sha256":"5a53d35ab0148d73ab52992561a4d07aec63d9b69ad6c239cad8fe60c5790bac","seq":2,"wave":"wave-t088-floor"}

- {"allocations":{"T:permutation-check-coverage":"[T-426]"},"authored":"2026-08-04","content_sha256":"b29e8a767b72d9c85a0a5f6cac35b55c05a8b95176b74d8e86e157da1cc71bde","seq":1,"wave":"wave-t410-sort-integrity-witness"}
- {"allocations":{"D:sort-witness-observation-equivalence":"D146"},"authored":"2026-08-04","content_sha256":"20c6ed262e147e79ab2792e35da00394ed4b8d7bfcf9492f947345e15436234f","seq":1,"wave":"wave-t410-sort-integrity-witness"}
- {"allocations":{"F:known-red-waiver-not-checked-before-stop":"F101","F:main-checkout-mutated-from-worktree-session":"F100"},"authored":"2026-08-04","content_sha256":"642b70925e58570bf4c228ff543ad8c82d5abf82744db24f47d071fde8361ca6","seq":1,"wave":"wave-t410-sort-integrity-witness"}

- {"allocations":{},"authored":"2026-08-04","content_sha256":"43271f3d1cc90e33ee1d2b58bd859e63fc6be95591aebc181380f0b51c1a8e41","seq":1,"wave":"dev-wave-t412-l2-pruning"}

- {"allocations":{},"authored":"2026-08-04","content_sha256":"4265503560154c159dab2a017069ce2e8a0333b040aab21713c8672524f369f4","seq":1,"wave":"wave-t244-p3-origin-ledger"}
- {"allocations":{"D:p3-origin-ledger-deferred":"D147"},"authored":"2026-08-04","content_sha256":"a91cf3701a95c118353e2d3adf0bcaada23b9efcdf46ce204c03ab4f74bf20c6","seq":2,"wave":"wave-t244-p3-origin-ledger"}

- {"allocations":{"T:codex-worker-launch-flake":"[T-427]"},"authored":"2026-08-04","content_sha256":"884dc1b16d0112b9b4b7e31012234bd7b6734f1169e81e934d656df38559b03d","seq":1,"wave":"wave-t409-evolve-hole-allowlist"}
- {"allocations":{"F:adversarial-prompt-refused":"F102"},"authored":"2026-08-04","content_sha256":"649386f5ad9a150ff8e9f9e06d3cbf4ea635bdd737be35d3b8e55c37eebdd5ac","seq":2,"wave":"wave-t409-evolve-hole-allowlist"}

- {"allocations":{},"authored":"2026-08-04","content_sha256":"55c4905ca85a72463ad35cca5e0357ca917335c52768319973a6d279d8aa4d44","seq":1,"wave":"wave-t244-p5-injection-gate"}
- {"allocations":{"D:p5-provider-and-session-isolation":"D148"},"authored":"2026-08-04","content_sha256":"16ece9b11cde676df14853d12992ca013c51b25847c774067c079b681e381206","seq":1,"wave":"wave-t244-p5-injection-gate"}

- {"allocations":{"T:codex-launch-receipt-flake":"[T-431]","T:dev-wave-detach-contract":"[T-432]","T:reflux-ir-production-wiring":"[T-428]","T:reflux-rejection-disclosure-closure":"[T-429]","T:ruleops-blob-blocks-full-suite":"[T-430]"},"authored":"2026-08-04","content_sha256":"ba5399d7714fca7f20d6eb21b7bdca1f95cf253cdf02254990c90175f0cfd0aa","seq":1,"wave":"wave-t244-p1-ir-emitter"}
- {"allocations":{"D:reflux-ir-p1-component":"D149"},"authored":"2026-08-04","content_sha256":"0d91c08c3dd6d0dc026d106318b9c1d1f67973afbbf22e23896c0a647acb01df","seq":2,"wave":"wave-t244-p1-ir-emitter"}
- {"allocations":{"F:dev-wave-child-dies-with-tool-call":"F103","F:pgrep-matches-parallel-wave-child":"F104"},"authored":"2026-08-04","content_sha256":"b2ebee70aa77122af96efe3c16c2c23ba71085b2e913f4878098cbc14e0bab22","seq":3,"wave":"wave-t244-p1-ir-emitter"}

- {"allocations":{"D:t244-u2-na-bifurcation":"D150"},"authored":"2026-08-04","content_sha256":"17fdc2e2c8063a5b2aad5fa4227d53d21c44c2f686a8ddd3fddf77c3c4e9bd23","seq":1,"wave":"dev-wave-t244-u2-na-bifurcation"}
- {"allocations":{"T:t244-cap-lift-doc-pointer":"[T-436]","T:t244-cap-lift-receipt":"[T-434]","T:t244-p6-semantic-contract":"[T-433]","T:t244-prereg-refresh":"[T-435]"},"authored":"2026-08-04","content_sha256":"0b40b483e35e3838c710f9a20a0142767e9f58c4653665d15396eb0376c2ca68","seq":2,"wave":"dev-wave-t244-u2-na-bifurcation"}

- {"allocations":{"T:ruleops-git-stderr-strict":"[T-439]","T:ruleops-inventory-mutation-matrix":"[T-437]","T:ruleops-realrepo-xdist-group":"[T-438]","T:ruleops-test-candidate-decode":"[T-440]"},"authored":"2026-08-04","content_sha256":"e12e87683a0ebb01067fd1eb798b703abf7cd09cd3359bded3c5e38c4aa1b698","seq":1,"wave":"wave-t407-ruleops-binary-blob"}
- {"allocations":{"D:ruleops-inventory-skip-non-utf8":"D151"},"authored":"2026-08-04","content_sha256":"92d3837a96138ccf9cd0e2709b681aed0607c8a234f030c714fa6873cee2bf8f","seq":2,"wave":"wave-t407-ruleops-binary-blob"}

- {"allocations":{"T:backoff-hole-allowlist":"[T-441]","T:freeze-live-source-regression":"[T-442]"},"authored":"2026-08-04","content_sha256":"db2f98d99c889d8d064f06d23867551b75e4aba387728b9833b5be7f889501d6","seq":1,"wave":"rulings-20260804"}

- {"allocations":{"T:codex-reasoning-ab-tmp-flake":"[T-447]","T:mimalloc-tag-pin-sync":"[T-446]","T:mutation-runner-known-red":"[T-448]","T:thirdparty-acquisition-receipt":"[T-444]","T:thirdparty-cache-same-uid-toctou":"[T-449]","T:thirdparty-fetchcontent-other-campaigns":"[T-443]","T:thirdparty-hydrate-enforcement":"[T-445]"},"authored":"2026-08-04","content_sha256":"c65411154d21bf2dbbfd883e43f0185907cd63c59c38ee1541c956b8f01968f7","seq":1,"wave":"wave-t340-thirdparty-fetch"}
- {"allocations":{"D:thirdparty-fetch-path":"D152"},"authored":"2026-08-04","content_sha256":"2faf074cc396f83479cbff5cb8a13dd78af9e49b1d8bf50ba0cfa750753b10e7","seq":2,"wave":"wave-t340-thirdparty-fetch"}
- {"allocations":{"F:commit-during-acceptance-run":"F106","F:empty-dir-untracked-fixture":"F105","F:mutation-masked-by-outer-verify":"F107"},"authored":"2026-08-04","content_sha256":"ac99a447f04775e69a1ac87bb2985ccfc49d32a10fa63c3ee8a9793cd4a14fec","seq":3,"wave":"wave-t340-thirdparty-fetch"}

- {"allocations":{},"authored":"2026-08-04","content_sha256":"aa65722aba8e89afebbc371220785165e7819f7cc57bc049882e957bf6df090f","seq":1,"wave":"dev-wave-t244-p4-batch-freeze"}
- {"allocations":{"D:t244-p4-batch-freeze-defer":"D153"},"authored":"2026-08-04","content_sha256":"b2ba987703f16b57a5abb30ab4be204241462a6662f59e1904a97ce9953feecb","seq":2,"wave":"dev-wave-t244-p4-batch-freeze"}

- {"allocations":{},"authored":"2026-08-04","content_sha256":"6a64a6c0426f7375c23ba51c5a217a8b8745fc76e450fcd1aed4d080da7bad57","seq":1,"wave":"rulings-20260804-b"}

- {"allocations":{"T:dw-o15-dedup":"[T-450]"},"authored":"2026-08-04","content_sha256":"cd679f2731f36ebb34b07b635d88904d22040a21cb2fdd1a4bfe3f3707fc96b9","seq":1,"wave":"rulings-20260804-c"}

- {"allocations":{},"authored":"2026-08-04","content_sha256":"b52244c2c1c815b717bb6be13a3cd5badbd8d5a7e90d8953ca8fe06e9a3c5dd9","seq":1,"wave":"dev-wave-t410-sort-witness"}

- {"allocations":{},"authored":"2026-08-04","content_sha256":"aa0862b5f3386b5cc57dd410e224d30b32b511821c5f16f06675a921b4913225","seq":1,"wave":"rulings-20260804-d"}

- {"allocations":{},"authored":"2026-08-04","content_sha256":"d37ff46f30694f98a3f4691ca990f69b56d3e58cf9ea03100e5972d1870fe71d","seq":1,"wave":"dev-wave-t434-cap-lift-receipt"}

- {"allocations":{},"authored":"2026-08-04","content_sha256":"38467ad92e88e0b030ba1a0ad477d3ab4a934cfefbc811f0420f3e0d68d87c63","seq":1,"wave":"wave-t338-q3q5-stale"}
- {"allocations":{},"authored":"2026-08-04","content_sha256":"20410778215d78be0dbcbffd1bdb525a6c615e04a962758c50f86cb61cfeeb97","seq":2,"wave":"wave-t338-q3q5-stale"}

- {"allocations":{"T:run-tests-queue-wait-passthrough":"[T-451]"},"authored":"2026-08-04","content_sha256":"25c08dc8a6413700dcc8799b63603dfac73a4ce41767217629ff847cc3fa39f3","seq":1,"wave":"dev-wave-t433-p6-contract"}
- {"allocations":{"D:p6-sufficiency-contract":"D154"},"authored":"2026-08-04","content_sha256":"d66836e6a24cfbcf3ed56f499682780f317b9899f849fcae3cd9da789fcc6a6a","seq":2,"wave":"dev-wave-t433-p6-contract"}

- {"allocations":{"T:dev-wave-docs-budget-second-case":"[T-454]","T:effective-clock-tolerance-authority":"[T-452]","T:silo-ladder-clock-consumer":"[T-453]"},"authored":"2026-08-04","content_sha256":"6470e210a707ce7c105441192e00370f3e2042cd0e2d454346682b5055650b57","seq":1,"wave":"wave-t419-attestation-clock"}
- {"allocations":{"D:effective-clock-self-consistency-gate":"D155"},"authored":"2026-08-04","content_sha256":"6eeb81837283cd622b07a85e5f7a61a4595e93e2d2c66e7c14f0a1179749a0a2","seq":2,"wave":"wave-t419-attestation-clock"}
- {"allocations":{"F:attestation-e2e-fixture-clamped-observation":"F109","F:attestation-probe-observer-effect":"F108"},"authored":"2026-08-04","content_sha256":"cdbdba36ce0228d39f3c9385015623a0e31898047588af6a4a344c785fa27921","seq":3,"wave":"wave-t419-attestation-clock"}

- {"allocations":{"T:guard-bash-sanction-fetch-tool":"[T-455]"},"authored":"2026-08-04","content_sha256":"7c19e69a17d9cd71f59e98a1d4221b9af2a410dca930f6914d588156796dd3ce","seq":1,"wave":"rulings-20260804-e"}
- {"allocations":{"D:p6-semantic-sufficiency-contract":"D156"},"authored":"2026-08-04","content_sha256":"3c13d947519dcf8df011ce609504131a8156665a76193411577cac55bc43666f","seq":2,"wave":"rulings-20260804-e"}

- {"allocations":{"D:u1-driver-injection-rejection":"D157"},"authored":"2026-08-04","content_sha256":"8f58defa2cf2206aed8b51e11d1f107ad72e8764446f8a997968969cd94eee72","seq":1,"wave":"dev-wave-t244-p5-u1-drive-preview"}
- {"allocations":{},"authored":"2026-08-04","content_sha256":"5ec0b4867b4bd439bc59e4abf8a7b21a87096c78cb363a7f3e991ec770cc3a7e","seq":2,"wave":"dev-wave-t244-p5-u1-drive-preview"}

- {"allocations":{},"authored":"2026-08-04","content_sha256":"b6a0bf60fd5478a5959768535b7c0cb88cfe9ca42a71896a2039286875597ef1","seq":1,"wave":"rulings-20260804-f"}

- {"allocations":{"T:exploration-resume-root-manifest":"[T-457]","T:official-campaign-root-externalization":"[T-456]"},"authored":"2026-08-04","content_sha256":"a5945593d4b78d765cc07c49cdd6147900d0645aa48b76c346de5b2657a85e93","seq":1,"wave":"dev-wave-t422-campaign-external-root"}
- {"allocations":{"D:exploration-external-output-root":"D158"},"authored":"2026-08-04","content_sha256":"d0bfa7029e3959174dfb3d0dd8f6c57319d6d6e7fe07d6330d13aa69284f1699","seq":2,"wave":"dev-wave-t422-campaign-external-root"}

- {"allocations":{"T:mutation-harness-diagnostic-category":"[T-458]"},"authored":"2026-08-04","content_sha256":"d5ce037ee7dca54d0092b184f9d699d2eda4ad21187d5a353b5ff3d77dc265c5","seq":1,"wave":"dev-wave-t244-p3-redesign"}
- {"allocations":{"D:p3-origin-ledger-prototype-v3":"D159"},"authored":"2026-08-04","content_sha256":"216f109daeaa22023de1d3f15fb67a363f0629ccb051f9a55939e78e3f15726d","seq":2,"wave":"dev-wave-t244-p3-redesign"}
- {"allocations":{},"authored":"2026-08-04","content_sha256":"7be16005ee46163bf89710652dfbde6a211bb8d920411bddcb031c5abdd12003","seq":3,"wave":"dev-wave-t244-p3-redesign"}

- {"allocations":{},"authored":"2026-08-04","content_sha256":"5ecab05e405c53981c49a9fa1ca289135d9c40665b988c3d323526c516caa4a1","seq":1,"wave":"wave-t425-floor-scoping"}

- {"allocations":{},"authored":"2026-08-04","content_sha256":"15e0a990716abc8f1b7c2de0cf1bb6c9f008a756dd9cba85c8e503644f63f27b","seq":1,"wave":"wave-cleanup-worktrees"}

- {"allocations":{"T:auditor-nits-producer-schema":"[T-466]","T:epoch-budget-rule":"[T-463]","T:machine-materializer-emitter":"[T-464]","T:provenance-automerge-rule":"[T-467]","T:report-binding-receipt":"[T-462]","T:s8b-duplicate-key-disclosure":"[T-465]","T:source-evidence-aba-snapshot":"[T-460]","T:trigger-crash-resume-topology":"[T-459]","T:trigger-witness-table":"[T-461]"},"authored":"2026-08-04","content_sha256":"de0a247032b63817d0841e14684d48eb85ebb575cc10d7aa5b2783bb0e2e00a6","seq":1,"wave":"dev-wave-t428-reflux-wiring"}
- {"allocations":{"D:trigger-wire-only-acceptance":"D160"},"authored":"2026-08-04","content_sha256":"d51f5b458ee0dd9d861711c4cd62a1f00f18346931a258a25a6ba158108c4d06","seq":1,"wave":"dev-wave-t428-reflux-wiring"}

- {"allocations":{"T:trial-acceptance-wiring":"[T-470]","T:trial-launch-ledger":"[T-469]","T:trial-registry-authority":"[T-468]"},"authored":"2026-08-04","content_sha256":"fc39a9c35ffc12f04ced2b1c21f873fd39a6bc7638457d5f64bc90e20bca59ec","seq":1,"wave":"dev-wave-t325-trial-registry"}

- {"allocations":{"T:restore-bound-measurement":"[T-471]"},"authored":"2026-08-04","content_sha256":"10af71f6dbbf70339f6efc48b7c0ed4bdb54c7e2ece307a26b10b80fedf6ef67","seq":1,"wave":"dev-wave-t399-t400-signal-mitigation"}
- {"allocations":{"D:probe-evidence-three-way-split":"D161"},"authored":"2026-08-04","content_sha256":"fbb7ddd12bc4314ee8d86d309a3c32ed0e95cd296dfcab651d251436467d82c7","seq":2,"wave":"dev-wave-t399-t400-signal-mitigation"}

- {"allocations":{"F:single-tenancy-unreachable-on-compute-node":"F110","F:unreadable-diagnostic-treated-as-fatal":"F111"},"authored":"2026-08-05","content_sha256":"5d6e5a3d283eb355cbd237d4f8f37a71e6c6f18dc8d0988f77abd121fbd72002","seq":1,"wave":"dev-wave-t419-probe-experiment"}
- {"allocations":{},"authored":"2026-08-05","content_sha256":"5d6d507d70a0b911baa4996561df5e41984a7e4b26479eed9842709e79ee357a","seq":2,"wave":"dev-wave-t419-probe-experiment"}

- {"allocations":{"T:layer3-claim-boundaries":"[T-473]","T:s1-freeze-membership-gate":"[T-472]","T:trigger-artifact-reinspection":"[T-474]"},"authored":"2026-08-05","content_sha256":"c3e87f463f50209dc0709b532341d04143475700c3c1d26846d674a9a3a19077","seq":1,"wave":"rulings-20260805-a"}

- {"allocations":{"T:calibration-contract-generation":"[T-475]","T:calibration-producer-provenance":"[T-477]","T:reflux-ledger-flock-flake":"[T-476]"},"authored":"2026-08-04","content_sha256":"97cecf110e1856a5d41cae409082ad02aeebf67794bcd4f605a38eb61210b565","seq":1,"wave":"dev-wave-t452-clock-tolerance-authority"}

- {"allocations":{"T:calibration-contract-generation-migration":"[T-478]"},"authored":"2026-08-05","content_sha256":"7802c6e19955a80d6eae7fd86d19599ad5039a0564580990bd20279274bd7292","seq":1,"wave":"rulings-20260805-b"}

- {"allocations":{"T:qualification-role-field-name":"[T-479]"},"authored":"2026-08-05","content_sha256":"b3ad4d4ec99cf603857241eb5450cb5bfd5aec529e8a3a44179bb544092a78fa","seq":1,"wave":"dev-wave-t337-qualification-authority"}
- {"allocations":{"D:qualification-authority-boundary":"D162"},"authored":"2026-08-05","content_sha256":"758c5e4c6a89f9ed34e86229b35e9022b7b355095464b8d5038fb641f4c4f6a3","seq":1,"wave":"dev-wave-t337-qualification-authority"}
- {"allocations":{},"authored":"2026-08-05","content_sha256":"7c369188b90356f14fdc6d01254ed90002b6e059db65c37282602497fb9163b3","seq":2,"wave":"dev-wave-t337-qualification-authority"}

- {"allocations":{},"authored":"2026-08-05","content_sha256":"95d67da5b5a92cf3c58a653e2d1d38d1503e03a2d105eb20c1dd7b2efb552fdb","seq":1,"wave":"dev-wave-t244-p3-producer-wiring"}
- {"allocations":{"D:p3-producer-wiring-blocked":"D163"},"authored":"2026-08-05","content_sha256":"3649c1f5f13cb11e441302cc8a8b0caac8392aa75071a0fa4e41fb1e370456b2","seq":2,"wave":"dev-wave-t244-p3-producer-wiring"}

- {"allocations":{},"authored":"2026-08-05","content_sha256":"f8b2986bc50da09a881e4ba0925842225a2f4c71318dac6d4594556cb0e9ba73","seq":1,"wave":"rulings-20260805-c"}

- {"allocations":{},"authored":"2026-08-05","content_sha256":"fbbb011ded6d43d20459b0ef242be737d789d381cca3a88237e60caa10641730","seq":1,"wave":"rulings-20260805-d"}

- {"allocations":{"T:ruleops-inventory-parallel-flake":"[T-480]"},"authored":"2026-08-05","content_sha256":"148eb81cff89ea461a90920c1b2abc1f9a4f2b1fa3aaeac8ccefe7fedb982c81","seq":1,"wave":"dev-wave-t244-p2-noninterference"}
- {"allocations":{"D:t244-p2-literal-tripwire-remand":"D164"},"authored":"2026-08-05","content_sha256":"18572e8140f5226c9048110282309d9f62132cfddd700a55bd5e3d8987cae0a2","seq":2,"wave":"dev-wave-t244-p2-noninterference"}

- {"allocations":{},"authored":"2026-08-05","content_sha256":"ed85cf4a9b71fc2ceb0c671c31a22f6c13646aeda05ef47ff8aff155efe2c72c","seq":1,"wave":"dev-wave-t327-prereg-activation"}
- {"allocations":{"D:s8c-automatic-activation":"D165"},"authored":"2026-08-05","content_sha256":"2250f18e20f2329b6e130be64161da7d99af0f5c0c3d736ad81c8018ac0ce2e7","seq":1,"wave":"dev-wave-t327-prereg-activation"}

- {"allocations":{"T:guard-bash-module-borrow-family":"[T-483]","T:pegasus-login-procedure-blocked-family":"[T-481]","T:sanctioned-path-argv-granularity":"[T-482]"},"authored":"2026-08-05","content_sha256":"a2d42cfbaf9469dfa926c58fe714c20593a02ed767764c62db9c2834ecfc5593","seq":1,"wave":"dev-wave-t455-guard-bash-sanction-fetch"}

- {"allocations":{},"authored":"2026-08-05","content_sha256":"e8ec964b78f2b9bf76478e4382a06de754f94e7c6ad5e0591a602c5b0f87bf3c","seq":1,"wave":"dev-wave-t419-probe-rerun"}

- {"allocations":{"T:reflux-evidence-resolver-contract":"[T-485]","T:reflux-query-receipt-binding":"[T-484]"},"authored":"2026-08-05","content_sha256":"d4dc9ef1386b69a4dd301f8231a88cb75c5318a3be045d6ca72bda3d02504b74","seq":1,"wave":"dev-wave-t244-p4-batch-freeze"}
- {"allocations":{"D:p4-batch-freeze-ledger-conformance":"D166"},"authored":"2026-08-05","content_sha256":"bd86948b32b4b7ad9fac1cbd35e2f92e5227514473e7b0409ba4d46727f767ab","seq":2,"wave":"dev-wave-t244-p4-batch-freeze"}
- {"allocations":{},"authored":"2026-08-05","content_sha256":"faaa472fb6a70abc4a19a13c5defa53949464081d33309b03534168e0fe59377","seq":3,"wave":"dev-wave-t244-p4-batch-freeze"}

- {"allocations":{"T:assert-head-cost":"[T-489]","T:interruption-safe-restore":"[T-487]","T:production-cleanup-leg":"[T-486]","T:warn-delivery-latency":"[T-488]"},"authored":"2026-08-05","content_sha256":"abd0f906755effdf5ba199b96d059b408bd883bc4372236de5190e8b620852ba","seq":1,"wave":"dev-wave-t471-restore-bound"}
- {"allocations":{"F:fix-prompt-existing-test-ambiguity":"F112"},"authored":"2026-08-05","content_sha256":"0eb1d6238d5ecb4235953013f21de3a34408af3473cb28c5924f4eb5f0b0d332","seq":2,"wave":"dev-wave-t471-restore-bound"}

- {"allocations":{"T:t472-scope-out-rulings":"[T-490]"},"authored":"2026-08-05","content_sha256":"e2a859713675b3fe259314d02ced9290867dd66cd839ccdc37180f092c4d446e","seq":1,"wave":"dev-wave-t472-canonical-predicate-consumers"}
- {"allocations":{"D:consumer-local-canonical-membership":"D167"},"authored":"2026-08-05","content_sha256":"aafa3d14a57295c403ed2c1e9ca0fbc1d4f4a147063921172c00f9d1b47634a0","seq":2,"wave":"dev-wave-t472-canonical-predicate-consumers"}
- {"allocations":{"F:mutation-preregistration-false-kill":"F113"},"authored":"2026-08-05","content_sha256":"c5891a5b90a8705fd580b1c33136909782a692717c4f2ed5c8676a89c6ee27ee","seq":3,"wave":"dev-wave-t472-canonical-predicate-consumers"}

- {"allocations":{},"authored":"2026-08-05","content_sha256":"c5116a45a20f3aa82bdb61861a88a0c6eccb68f4e705fb5964bf00fb64c653fa","seq":1,"wave":"rulings-20260805-e"}

- {"allocations":{},"authored":"2026-08-05","content_sha256":"c4d77aedc56569d3f6d8d064e08f2ca5582e361ff277df51a9db460548578653","seq":1,"wave":"rulings-20260805-f"}

- {"allocations":{},"authored":"2026-08-05","content_sha256":"b1f1d03493176d577f94fefae7840cf4d8daff5ac0cba55d98b09f09dd8f9302","seq":1,"wave":"dev-wave-f26-recurrence-record"}
- {"allocations":{"T:dw-s09-cleanup-pointer-budget":"[T-491]"},"authored":"2026-08-05","content_sha256":"23eda8d8c663fb33caec4c21896fc2f10ecd14d73b53e985caa5e717696b6321","seq":2,"wave":"dev-wave-f26-recurrence-record"}

- {"allocations":{"T:freeze-semantic-membership":"[T-492]","T:sort-comparator-authority":"[T-493]"},"authored":"2026-08-05","content_sha256":"13bcfcec5fb3398aea72674fadd8df2aff326e5df31b4734c8eda7e32fe899d7","seq":1,"wave":"rulings-20260805-g"}

- {"allocations":{"T:branch-deletion-path-investigation":"[T-495]","T:cleanup-unreachable-audit":"[T-494]"},"authored":"2026-08-05","content_sha256":"2722fd8f61f2292fe98bf43ed62446e0407ee76631c699a1acfb0f6de8a62bb1","seq":1,"wave":"rulings-20260805-h"}

- {"allocations":{},"authored":"2026-08-05","content_sha256":"d2f06f62c2e89bfde1a71d5a6d1dd123a62611f1797d6641113c8193be01cc9b","seq":1,"wave":"dev-wave-test-failure-triage"}

- {"allocations":{"T:ruleops-real-repo-inventory-flake":"[T-496]"},"authored":"2026-08-05","content_sha256":"7f1dceed480e1e241e0e427f0a80592eafc5906b1050cf3e8a23ca69eda062f0","seq":1,"wave":"dev-wave-t476-flock-race-flake"}
- {"allocations":{"D:flock-observation-by-event":"D168"},"authored":"2026-08-05","content_sha256":"8f2df874e37fe93d47ed8c7d89c9d513a97fd397d84b037a837b1632703e2a5e","seq":2,"wave":"dev-wave-t476-flock-race-flake"}
- {"allocations":{"F:mutation-run-vs-acceptance-run":"F114"},"authored":"2026-08-05","content_sha256":"b60cfe551c66b5de49dd199477bc73f0738358794e5078909a18ea00615b342c","seq":3,"wave":"dev-wave-t476-flock-race-flake"}

- {"allocations":{"T:campaign-prefix-cache-feasibility":"[T-498]","T:devwave-worker-class1-branch":"[T-497]","T:next-action-backlog-triage":"[T-499]"},"authored":"2026-08-05","content_sha256":"d0ad80bf88ce4a5d88de021df8f5e73db7fc1d557feaaa4ab8b78146fb36bb95","seq":1,"wave":"dev-wave-token-economy"}
- {"allocations":{"D:compact-carry-format":"D169"},"authored":"2026-08-05","content_sha256":"b1aba49c09f03ffc45456555cb1565409997fa6bb8ed90cb25d9be0dff15d3e2","seq":2,"wave":"dev-wave-token-economy"}
- {"allocations":{"F:acceptance-repo-write-race":"F115"},"authored":"2026-08-05","content_sha256":"d261bf5da153ffa00e5b5b1b22ba8c9695bf3b9b61fa7932f26bbabe50c6077d","seq":3,"wave":"dev-wave-token-economy"}

- {"allocations":{},"authored":"2026-08-05","content_sha256":"8da1fc40307b83aa14e1ff0603c2bd8d3a23d022104520f00afcf07571d1a246","seq":1,"wave":"rulings-20260805-i"}

- {"allocations":{"T:post-policy-machine-sweep-membership":"[T-500]","T:trigger-provenance-implementation-overload":"[T-502]","T:wal-side-aba-in-admission":"[T-501]"},"authored":"2026-08-05","content_sha256":"bb0f3abe42a386d7a1e7b2db914172f31928ac124c2b15ba5a009da1ea9b1f30","seq":1,"wave":"dev-wave-t474-legacy-trigger-admission"}
- {"allocations":{"D:legacy-trigger-raw-view-denial":"D170"},"authored":"2026-08-05","content_sha256":"a3faa86758bf46549e021d32fa8202c2e398da9526d3596a1f30b378eb3dbe7c","seq":1,"wave":"dev-wave-t474-legacy-trigger-admission"}

- {"allocations":{"T:clean-gate-ignored-blindness":"[T-504]","T:dev-wave-budget-headroom":"[T-505]","T:mutation-restore-durability-impl":"[T-503]"},"authored":"2026-08-05","content_sha256":"a43058c98d6b8a91f65b7c577e004f0b8a13fedbe53c3f4559b465c2da0a3618","seq":1,"wave":"dev-wave-t487-design"}

- {"allocations":{},"authored":"2026-08-05","content_sha256":"7df174450d32364368ff133931e36d79fcad28ea157568d19933f30c20c3a190","seq":1,"wave":"dev-wave-t478-calibration-contract-generation"}

- {"allocations":{"T:dev-wave-docs-budget-at-ceiling":"[T-508]","T:loader-self-pass-quarantine":"[T-506]","T:silo-driver-syspath-restore":"[T-509]","T:t126-attest-type-bug":"[T-507]"},"authored":"2026-08-05","content_sha256":"7d0dc5d59b67f6e39596431f59cf4f843e979d36eb6535508536ad12475d9f16","seq":1,"wave":"dev-wave-t452-t453-clock-authority"}
- {"allocations":{"D:effective-clock-policy-authority":"D171"},"authored":"2026-08-05","content_sha256":"aeee656674d7ddda5d41546e59ce7a9f42361f19dd4fff959273a1ba7b705461","seq":2,"wave":"dev-wave-t452-t453-clock-authority"}
- {"allocations":{"F:test-green-by-removing-production-gate":"F116"},"authored":"2026-08-05","content_sha256":"3231342cf0c8a35fa5d97463f193ec623347345c1ff81da6ed9a18fc0d063cf9","seq":3,"wave":"dev-wave-t452-t453-clock-authority"}

- {"allocations":{"T:first-run-classification-site":"[T-511]","T:mutation-harness-xdist-group-nodes":"[T-512]","T:ruleops-git-timeout-threshold":"[T-510]"},"authored":"2026-08-05","content_sha256":"cbc207af728da0d0a33c5a38fe3fcd4323850076901761840779dc2341268e68","seq":1,"wave":"dev-wave-t496-ruleops-inventory-diag"}
- {"allocations":{"D:ruleops-failclosed-threshold-unchanged":"D172"},"authored":"2026-08-05","content_sha256":"4ff520bee2bf0d7ff5218158c9825f335a2bd61626d35f7e4e941fbd2dc51d60","seq":2,"wave":"dev-wave-t496-ruleops-inventory-diag"}
- {"allocations":{"F:first-run-classification-site-undefined":"F117"},"authored":"2026-08-05","content_sha256":"4d6d1cd7493a5d3ded9f3a394e1821c061dc79af3bb6a4c51b3480fd7dbb71a0","seq":3,"wave":"dev-wave-t496-ruleops-inventory-diag"}

- {"allocations":{"T:diffq-reject-identity-canonicalization":"[T-515]","T:premateralized-source-admission-fold":"[T-513]","T:wait-without-polling-noise":"[T-514]"},"authored":"2026-08-05","content_sha256":"62f0ea551387a519f14b85ace503b6d738bbf6a71ac5b0c20809b093e895aa9e","seq":1,"wave":"dev-wave-t490-u1-u2"}
- {"allocations":{"D:fold-before-materialize-at-shared-boundary":"D174","D:materializer-authority-independent-of-producer":"D173"},"authored":"2026-08-05","content_sha256":"19d9af3f707bfa710b7c8e37bc8555a18de8a2bdca62ca6163fdaa4eb9227018","seq":1,"wave":"dev-wave-t490-u1-u2"}
- {"allocations":{},"authored":"2026-08-05","content_sha256":"56202e66b567949a2351c4992e4be227f096274e8b5b4aefd2805c3cec950b1d","seq":1,"wave":"dev-wave-t490-u1-u2"}

- {"allocations":{"T:dangling-audit-content-delta":"[T-516]"},"authored":"2026-08-05","content_sha256":"9adfe279584fe7e55791f3257a95c209c10a9096cbb22fed1c3132defd196d82","seq":1,"wave":"rulings-20260805-j"}

- {"allocations":{},"authored":"2026-08-05","content_sha256":"d6146de91f878fd48f70a48706f32b39ef16c4a8abac17a35bfc3ec18d0d8e1f","seq":1,"wave":"rulings-20260805-k"}

- {"allocations":{},"authored":"2026-08-05","content_sha256":"31a0dd45b2e788b7d091f7eb01cc5c0c5158465d011bb511cf3488adfeb024b7","seq":1,"wave":"dev-wave-cleanup-dangling-audit"}
- {"allocations":{"F:branch-deleted-with-unlanded-work":"F118","F:implementation-blocked-by-provenance-after-the-fact":"F120","F:merge-parentwise-diff-inflates-changed-paths":"F119"},"authored":"2026-08-05","content_sha256":"b70ad4050cd705abb23a3445c26dbc5b7f4d46e1650d034ea75d32bc6560d7dc","seq":1,"wave":"dev-wave-cleanup-dangling-audit"}

- {"allocations":{},"authored":"2026-08-05","content_sha256":"9c13fc950ef4cb942f2144ce001b36a2e3ce8e1bd33a5e7682c9a965744f3b3a","seq":1,"wave":"rulings-20260805-l"}
