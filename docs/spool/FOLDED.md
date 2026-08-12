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

- {"allocations":{"T:transport-probe-lane":"[T-517]"},"authored":"2026-08-05","content_sha256":"854c5ffd6e27bd0ee22da0834db3c1cae476ee745281530804e5ddb0c7ef4c2b","seq":1,"wave":"dev-wave-t420-wall1-driver"}
- {"allocations":{},"authored":"2026-08-05","content_sha256":"596c5c9f79256f00889233d6538d5a91644995329465f11cb3767e6a5c6a92b6","seq":2,"wave":"dev-wave-t420-wall1-driver"}

- {"allocations":{},"authored":"2026-08-05","content_sha256":"b0513e43fe724488d3b13c08f2bf1f7401dad16d3b83ad6c80f2a96f4f41e1a2","seq":1,"wave":"rulings-20260805-m"}

- {"allocations":{},"authored":"2026-08-05","content_sha256":"3ff85b4eeefd2df136a93908fc70e59656ea83278e43d37c17837a0cfe2cb594","seq":1,"wave":"dev-wave-t213-shared-scratch"}

- {"allocations":{"D:pegasus-admission-registry":"D175"},"authored":"2026-08-05","content_sha256":"3a77ae066f56a9590136b87d8c90e014340158ddf55f45c965ca3b531433964d","seq":1,"wave":"dev-wave-t481-pegasus-admission"}
- {"allocations":{"F:classification-bootstrap-deadlock":"F123","F:fix-prompt-restore-without-exceptions":"F124","F:norm-procedure-barrier-three-way-drift":"F122","F:pegasus-blanket-rule-porous":"F121"},"authored":"2026-08-05","content_sha256":"6c7c2124e4f811096c209ecff3e42f3e419e348600b455351cdcf9e15ea28462","seq":2,"wave":"dev-wave-t481-pegasus-admission"}
- {"allocations":{"T:collect-receipt-input-caps":"[T-519]","T:dev-wave-fix-prompt-contract":"[T-521]","T:guard-bash-residual-bypasses":"[T-518]","T:pegasus-admission-registry-authority":"[T-522]","T:pegasus-measurement-surface":"[T-520]"},"authored":"2026-08-05","content_sha256":"9106562d4166e27257dbadad3dbc93998a56a0d0546cfb4f280cbedaaa9b9e42","seq":3,"wave":"dev-wave-t481-pegasus-admission"}

- {"allocations":{"T:holdout-full-condition-binding":"[T-525]","T:holdout-workload-projection":"[T-527]","T:s8b-pilot-holdout-observation":"[T-523]","T:s8c-check-cli-double-import":"[T-526]","T:trial-experiment-unit-redesign":"[T-524]"},"authored":"2026-08-05","content_sha256":"7c42991aeaa2939168150f34d71d5a3d8a59c9f261e3ff7c8da90d63e1a42089","seq":1,"wave":"dev-wave-t470-t327-wiring"}
- {"allocations":{"F:merge-author-trailer-without-conflict":"F125"},"authored":"2026-08-05","content_sha256":"98326473e1500d9e539b0525eb5a04c065d3dbeb333eda67342506f9acf8a6ce","seq":2,"wave":"dev-wave-t470-t327-wiring"}

- {"allocations":{"T:campaign-env-contract-none-bypass":"[T-530]","T:contract-generation-activation-authority":"[T-529]","T:probe-method-alpha-production-wiring":"[T-528]"},"authored":"2026-08-05","content_sha256":"5e5043888a1cb1daa9ef30b5e033cb2ca31c04be4a0c6b8401eb5e112f906811","seq":1,"wave":"dev-wave-t419-u2-contract-generation"}
- {"allocations":{"D:contract-generation-bootstrap-fuse":"D176"},"authored":"2026-08-05","content_sha256":"8e979989eb8b5bc208477bc33bb5c5c0db58ee12410e118003adb712a7379108","seq":1,"wave":"dev-wave-t419-u2-contract-generation"}
- {"allocations":{"F:delegation-seam-left-unpinned-by-its-own-fix":"F127","F:fuse-masks-mutation-attribution":"F126"},"authored":"2026-08-05","content_sha256":"c28ac6462783df4243880b7174bd30b6838f7ed2ff77be7b22c955582b959f72","seq":1,"wave":"dev-wave-t419-u2-contract-generation"}

- {"allocations":{"T:freeze-membership-authority-provenance":"[T-534]","T:freeze-refreeze-generation-transition":"[T-531]","T:holdout-freeze-semantic-closure":"[T-533]","T:trigger-name-mask-binding":"[T-532]"},"authored":"2026-08-05","content_sha256":"bb636da57e7a681ad102dfc9b3f171b343462c446f8de7959509b6441fe8d1f1","seq":1,"wave":"dev-wave-t492-freeze-semantic-membership"}
- {"allocations":{"D:freeze-generator-self-hash-boundary":"D178","D:freeze-semantic-membership-at-schema":"D177"},"authored":"2026-08-05","content_sha256":"33b86c87bbf2b2dae19fc45594d7cb75d8ab7d8f332924bfaa1c7d5351a00dcd","seq":2,"wave":"dev-wave-t492-freeze-semantic-membership"}
- {"allocations":{},"authored":"2026-08-05","content_sha256":"83aadb0307b673d25bf10dcc8a32284c5740b02df9da659e068806e3d991e371","seq":3,"wave":"dev-wave-t492-freeze-semantic-membership"}

- {"allocations":{},"authored":"2026-08-05","content_sha256":"1f57c7d35f4ca1b10db8d993830fe616c613e637c2d8847a8f7096f5fa597bed","seq":1,"wave":"dev-wave-t244-p3-design"}
- {"allocations":{"D:t244-p3-design-package":"D179"},"authored":"2026-08-05","content_sha256":"38be6579fb57198f591288310813ec8a641efb529410c3bb6ab067795a496d65","seq":1,"wave":"dev-wave-t244-p3-design"}
- {"allocations":{"F:concurrent-codex-same-output-path":"F128"},"authored":"2026-08-05","content_sha256":"e3e6a455e67acad33e0539d94b6e66209479f782b39caa76e211d9766b09e8e3","seq":1,"wave":"dev-wave-t244-p3-design"}

- {"allocations":{},"authored":"2026-08-05","content_sha256":"a0fa05077c01f205633be656761f051ed8d4eaf913b184687b6e8023d792bb30","seq":1,"wave":"rulings-20260805-n"}

- {"allocations":{},"authored":"2026-08-05","content_sha256":"0e4305fd4d709265aedb18cc25864ff3c71824fa77131eca0c1bc2ec94314697","seq":1,"wave":"rulings-20260805-o"}

- {"allocations":{},"authored":"2026-08-05","content_sha256":"d9739ed2277641c376886ce422302d207c0e558aabc3c7557f37624be3d995f0","seq":1,"wave":"rulings-20260805-p"}

- {"allocations":{"T:compute-result-channel-ownership":"[T-536]","T:trust-root-control-surface":"[T-535]"},"authored":"2026-08-05","content_sha256":"208c145e00d7be244acbcf8a22ec6a294f23a6d33232d8331883c38b148aeb9f","seq":1,"wave":"dev-wave-t213-redefine"}

- {"allocations":{"D:pegasus-measurement-turn":"D180"},"authored":"2026-08-05","content_sha256":"5373d9e393233cbcc9ab58d31de3f5282c24f2430fbe1b1bd0a6d27128f00d22","seq":1,"wave":"dev-wave-t520-measurement-turn"}
- {"allocations":{"T:dev-wave-docs-only-contract":"[T-537]"},"authored":"2026-08-05","content_sha256":"10f31a925b726f873b1c582d946fe74bded5e247eac5151265b817ebb12ca24c","seq":2,"wave":"dev-wave-t520-measurement-turn"}

- {"allocations":{"T:acquisition-transcript-schema":"[T-539]","T:alpha-production-protocol-validation":"[T-538]","T:oracle-reservation-probe-allowance":"[T-540]","T:probe-warmup-carryover":"[T-542]","T:t126-attestation-type-mismatch":"[T-541]"},"authored":"2026-08-05","content_sha256":"761737c3a9d60d35d8b0c12cd12d7b655598e3172126e073fe237b8d93eeb9fb","seq":1,"wave":"dev-wave-t419-alpha-wiring"}
- {"allocations":{"D:alpha-acquisition-identity":"D181","D:thread-self-stat-for-pin-check":"D182"},"authored":"2026-08-05","content_sha256":"ff24918041aa72aec6a24b8db060dc4dae7e129ec91a511402de64f4e8c008c7","seq":1,"wave":"dev-wave-t419-alpha-wiring"}
- {"allocations":{"F:pin-check-gap-during-wait":"F130","F:self-stat-not-thread-stat":"F129"},"authored":"2026-08-05","content_sha256":"bb6cba7c479194ff7a75d532ddb31c95f311873f476683c7a67b7338d2471eda","seq":1,"wave":"dev-wave-t419-alpha-wiring"}

- {"allocations":{"D:disposable-probe-mutation-wrapper":"D184","D:t244-p3-liveness-fixture-only":"D183"},"authored":"2026-08-05","content_sha256":"19848d26c03f809697adcfe2b3ed117281ef2287f14172f5dc4e395a869d9858","seq":1,"wave":"dev-wave-t244-p3-liveness"}
- {"allocations":{},"authored":"2026-08-05","content_sha256":"68276f8e4e33f41878e790e972312e894166e0cfb19e2f0567a0895ebc6c6c0c","seq":2,"wave":"dev-wave-t244-p3-liveness"}
- {"allocations":{"F:brief-missed-closed-vocabulary":"F131","F:fix-inflated-disposable-probe":"F132"},"authored":"2026-08-05","content_sha256":"738c90a98283e6e77a8455a4e12294a1496e4d2ef6ec4a1424059495da7811b7","seq":3,"wave":"dev-wave-t244-p3-liveness"}

- {"allocations":{},"authored":"2026-08-06","content_sha256":"c88894833f585a48e99929cb131e6070c4f8a792f3a5517eac3a44e69b116f8d","seq":4,"wave":"dev-wave-t244-p3-liveness"}

- {"allocations":{"T:holdout-name-mask-bypass":"[T-544]","T:s1b-pairing-mask-identity":"[T-543]"},"authored":"2026-08-06","content_sha256":"986b35902528975dce3d34ca5e6af0cc80ac29205b81720df76a9b67785ea92a","seq":1,"wave":"dev-wave-t532-name-mask-binding"}
- {"allocations":{"D:trigger-name-mask-forward-authority":"D185"},"authored":"2026-08-06","content_sha256":"6f2cbfdfd9c73abe73683d0009a779a4a049b61db7b675017858b8a8670579ca","seq":2,"wave":"dev-wave-t532-name-mask-binding"}
- {"allocations":{"F:scan-order-false-kill":"F133"},"authored":"2026-08-06","content_sha256":"611b843835dc9ed6753a24acd9b1a30c60c62538e1f8744f7708babc409c560e","seq":3,"wave":"dev-wave-t532-name-mask-binding"}

- {"allocations":{"T:acceptance-mode-and-receipt":"[T-545]","T:dispatch-request-env-revalidation":"[T-547]","T:staged-delete-tree-identity":"[T-546]"},"authored":"2026-08-05","content_sha256":"afc9fe150b410224270c6d40225aa10fb608947c7c8c02dc0fe418f4e48c4d1d","seq":1,"wave":"dev-wave-t450-t412-preface"}
- {"allocations":{"D:acceptance-deletion-gate-fail-closed":"D186"},"authored":"2026-08-05","content_sha256":"6bf6d36c4b81883b8e1be68c35e43e34e8e12fe95cd595f559b657758232569e","seq":2,"wave":"dev-wave-t450-t412-preface"}

- {"allocations":{"T:disposable-probe-scale-cap":"[T-550]","T:pegasus-dependency-general-procurement":"[T-548]","T:probe-exclusivity-witness":"[T-549]","T:t139-mechanism-ablation":"[T-551]"},"authored":"2026-08-06","content_sha256":"c24504a36b6d33076f4bf6e2c987fb056472f2a7bceda6eff57d4c7f628853ca","seq":1,"wave":"dev-wave-t139-alt-x-probe"}
- {"allocations":{"D:t139-alt-x-partial-recovery":"D187"},"authored":"2026-08-06","content_sha256":"d89ef131f0695aa4dd74a9ce1b0372102e6ac7649a03b31256c132dbc7bd4588","seq":2,"wave":"dev-wave-t139-alt-x-probe"}
- {"allocations":{"F:local-single-statement-dependency":"F135","F:probe-clean-tree-scheduler-droppings":"F134"},"authored":"2026-08-06","content_sha256":"5f69185edc70acde0cc7c5d9b51983420b6938353970991f6d0c2d95b37905b4","seq":3,"wave":"dev-wave-t139-alt-x-probe"}

- {"allocations":{},"authored":"2026-08-06","content_sha256":"aa5f7e60863577f44675596e21e5412ba91e04f7e96b9e23de285521df902955","seq":1,"wave":"dev-wave-t495-branch-deletion-path"}
- {"allocations":{},"authored":"2026-08-06","content_sha256":"9bf775a9dd5c313364c575cec5516a2e01032fff0c0e2b386138e0480b5d8f58","seq":2,"wave":"dev-wave-t495-branch-deletion-path"}

- {"allocations":{"T:probe-terminal-proof-provenance":"[T-552]"},"authored":"2026-08-06","content_sha256":"5d16cb54eed816e6e3572abe8011187a63c1484d231397611f74b7701413276f","seq":1,"wave":"dev-wave-t401-racct-permanent"}
- {"allocations":{},"authored":"2026-08-06","content_sha256":"26c348e883671b10e5821b087ce68460bc0f99efffac05d388e03f9e7192a799","seq":2,"wave":"dev-wave-t401-racct-permanent"}

- {"allocations":{"F:concurrent-dispatch-during-acceptance":"F136"},"authored":"2026-08-05","content_sha256":"78f351a8f0ca48392f545ca5ebf4afe94c0b44addf0d45750f9461d27e0e2ee7","seq":3,"wave":"dev-wave-t520-measurement-turn"}

- {"allocations":{"T:admission-living-doc-closure":"[T-556]","T:admission-reason-gate-sync":"[T-555]","T:barrier-policy-on-old-commits":"[T-557]","T:dev-wave-docs-budget-headroom":"[T-558]","T:hook-wiring-skip-gate":"[T-554]","T:s8c-git-timeout-under-load":"[T-553]"},"authored":"2026-08-06","content_sha256":"ccabe4895244adc0c3b114956d953e5ca9fb975e6f902660d712c2e20157a85c","seq":1,"wave":"dev-wave-t522-admission-registry"}
- {"allocations":{"D:pegasus-admission-registry-canonical":"D188"},"authored":"2026-08-06","content_sha256":"39fab98631ab4a97b98f2e787239e7c9dc560519f8d0a9dad3bc8be48b90ea6d","seq":2,"wave":"dev-wave-t522-admission-registry"}
- {"allocations":{},"authored":"2026-08-06","content_sha256":"34c3b12d2b6146523240ec4571a774b39cc38fa48b3a4cc438afa2838b43b8a2","seq":3,"wave":"dev-wave-t522-admission-registry"}

- {"allocations":{},"authored":"2026-08-06","content_sha256":"0a9940e2b1e02c43a79da18661139a86db78a792fc24c7de06bed90ecfe05454","seq":1,"wave":"dev-wave-t244-p3-reservation-fsm"}
- {"allocations":{"D:mutation-attribution-masked-by-earlier-layer":"D190","D:origin-ledger-prequery-reservation":"D189"},"authored":"2026-08-06","content_sha256":"09491e30f01dccc033c6ceda3835611331ae3b0d68984bbc0f3148ffde293184","seq":1,"wave":"dev-wave-t244-p3-reservation-fsm"}

- {"allocations":{"T:certify-attempt-path-runbook":"[T-562]","T:certify-midjob-source-drift":"[T-563]","T:certify-reservation-formula":"[T-561]","T:independent-verifier-receipt":"[T-560]","T:publish-transaction-position":"[T-559]"},"authored":"2026-08-06","content_sha256":"a8edebb86b635bdd960029025e9515733916df1f7de382689f385aeef4282efc","seq":1,"wave":"dev-wave-t419-u2-recalibration"}
- {"allocations":{"D:certify-clock-gate-early-and-published-recheck":"D191"},"authored":"2026-08-06","content_sha256":"8e32a7bcc93e6e8df58a8e20a9341de5886e99c48ef31a7b561e5e8cc13a36ce","seq":2,"wave":"dev-wave-t419-u2-recalibration"}
- {"allocations":{"F:cleanup-fix-creates-destructive-path":"F137","F:mutation-expected-nodes-underregistered":"F138"},"authored":"2026-08-06","content_sha256":"fd915b5d32fb0e35785603d110cefbcd4c95ad811b19164c604c756e7543c22b","seq":3,"wave":"dev-wave-t419-u2-recalibration"}
- {"allocations":{"T:certify-pinned-dependency-sources-missing":"[T-564]"},"authored":"2026-08-06","content_sha256":"466ae95956cb0deec3eb29b9416322122618027099bdf15b3548289a622e5309","seq":4,"wave":"dev-wave-t419-u2-recalibration"}
- {"allocations":{},"authored":"2026-08-06","content_sha256":"a8b25368f5d51fe3a0bd2fd6e43f10da7ab8cc2bcbce5a3a36d1aa0b4768f170","seq":5,"wave":"dev-wave-t419-u2-recalibration"}

- {"allocations":{},"authored":"2026-08-06","content_sha256":"449fff529de98c94549f9922feddedbd42d42b1d2a2eb73fe060083b2a2c80e7","seq":1,"wave":"dev-wave-t244-p2-noninterference"}
- {"allocations":{"D:critic-candidate-label-projection":"D192"},"authored":"2026-08-06","content_sha256":"cd13ae288cf4303ffc06a030bf2a51f89d0736dd053cb4b85b11d561082ab98b","seq":1,"wave":"dev-wave-t244-p2-noninterference"}
- {"allocations":{},"authored":"2026-08-06","content_sha256":"d825041451f3f42881012fd61b7a68b116d4639472876eba0298562926185efb","seq":1,"wave":"dev-wave-t244-p2-noninterference"}

- {"allocations":{"T:attempt-local-signal-binding":"[T-567]","T:campaign-execution-lease":"[T-565]","T:guided-nobuild-pseudo-wal":"[T-569]","T:plotter-admission-gate":"[T-570]","T:recovered-campaign-certifiability":"[T-566]","T:replay-read-only":"[T-571]","T:trigger-recovered-provenance":"[T-568]"},"authored":"2026-08-06","content_sha256":"21a3869d9b8b002724ec48bfbfd7b54a2a4feb854d61623e0597fec2a8db0047","seq":1,"wave":"dev-wave-t459-resume-topology"}
- {"allocations":{"D:incomplete-attempt-recovery":"D193"},"authored":"2026-08-06","content_sha256":"c7d8d7252b048e14594fc526170d13c58beb51c9be7ee8d28a4ff9a61a9c4c08","seq":2,"wave":"dev-wave-t459-resume-topology"}
- {"allocations":{},"authored":"2026-08-06","content_sha256":"7f1c89d339a19207f3be050386e59f4b2c102a68ba9185a446d4dcff2c221af3","seq":3,"wave":"dev-wave-t459-resume-topology"}

- {"allocations":{"T:dw-g01-untracked-default":"[T-572]","T:t503-probe-kill-provenance":"[T-573]"},"authored":"2026-08-06","content_sha256":"aaf093a98e7cec09f686852a55f02d6d0d4dca50bcf61c7c04c7574849eb4b86","seq":1,"wave":"dev-wave-t503-liveness"}
- {"allocations":{"D:liveness-probe-single-commit":"D195","D:t503-liveness-probe-scope":"D194"},"authored":"2026-08-06","content_sha256":"5df5686719652116f0571c7c4342ec91c34f60822d0c2dd3b675ef32ff607aad","seq":2,"wave":"dev-wave-t503-liveness"}
- {"allocations":{"F:t503-probe-realmachine-mismatch":"F139"},"authored":"2026-08-06","content_sha256":"f9bd99447c287d98e166cea5e85c6e3e0a0a56863e949bbb4c0eb1131d9e5712","seq":3,"wave":"dev-wave-t503-liveness"}

- {"allocations":{"D:activation-authority-blocked-on-historical-resolver":"D196","D:env-contract-activation-naming":"D197"},"authored":"2026-08-06","content_sha256":"619bbbdacdb8ad5c237f5d60e06275f11667c8eac71c212d3e1eccbe277549c0","seq":1,"wave":"dev-wave-t529-activation-authority"}
- {"allocations":{},"authored":"2026-08-06","content_sha256":"56cdcd4205bbecd80b7ac1d3bfe6bd713c48995cdf8ce2ab0598932bf515f816","seq":2,"wave":"dev-wave-t529-activation-authority"}
- {"allocations":{"T:historical-contract-resolver-dispatch":"[T-574]","T:silo-promotion-consumer-identity":"[T-575]"},"authored":"2026-08-06","content_sha256":"24703b2bff8697ff67c39707f5fb71f136e0433112495f47b4558996e610ac3d","seq":3,"wave":"dev-wave-t529-activation-authority"}

- {"allocations":{},"authored":"2026-08-06","content_sha256":"373d2455276ffa154ffcf7db39cbc07416ab7e0e3df6d9d4fd44b7b700dada98","seq":1,"wave":"dev-wave-t244-p3-u4-candidate-count"}
- {"allocations":{"D:u4-member-rows-vs-candidates":"D198"},"authored":"2026-08-06","content_sha256":"c5c3484f9d306fe55dbc01acfcd850d7e4c74649e07841b40f3fa1a201c2787e","seq":1,"wave":"dev-wave-t244-p3-u4-candidate-count"}
- {"allocations":{},"authored":"2026-08-06","content_sha256":"42484a13bb13ce5c01e639fb3c87e0d59e93dc776018d92a39166ae97bbbc25a","seq":1,"wave":"dev-wave-t244-p3-u4-candidate-count"}

- {"allocations":{"T:dev-wave-budget-priority":"[T-577]","T:dev-wave-l2-delta-audit":"[T-579]","T:dev-wave-single-launch-route":"[T-576]","T:mutation-key-remaining-vectors":"[T-578]"},"authored":"2026-08-06","content_sha256":"3e9ca7b3934b7bf4536d6a91f1418f1534e43907761098cba260b256711f78c2","seq":1,"wave":"dev-wave-t454-testification"}
- {"allocations":{},"authored":"2026-08-06","content_sha256":"ac213f689be8ab4f0837b90bb4ae6377752e359347c14b02ab34118258766959","seq":2,"wave":"dev-wave-t454-testification"}

- {"allocations":{"D:no-issuerless-capability-freeze":"D199"},"authored":"2026-08-06","content_sha256":"2e786592053092bc63c27f4d641e56462817985458520aadb207112a4de6ebea","seq":1,"wave":"dev-wave-t503-restore-durability"}
- {"allocations":{"T:clean-tracked-ignored-blindness":"[T-581]","T:proof-receipt-code-closure":"[T-580]"},"authored":"2026-08-06","content_sha256":"011aaa2a8a3308b6242e450a8856a2a2474e5ea22a3ff5fb2349d5e96208e9b6","seq":2,"wave":"dev-wave-t503-restore-durability"}

- {"allocations":{"T:dependency-source-hydrate":"[T-585]","T:production-current-history-binding-test":"[T-582]","T:submit-certify-repo-root-binding":"[T-584]","T:submit-certify-scheduler-output":"[T-583]"},"authored":"2026-08-06","content_sha256":"4e6add24354bb3597f5390e44b7fde9c400f6d0065acf751b6d454483bba77e2","seq":1,"wave":"dev-wave-t564-dependency-source"}
- {"allocations":{"D:dependency-source-out-of-home":"D200"},"authored":"2026-08-06","content_sha256":"4c04b1059ec7db2291567d4a982d7d51aebe2aaf46e5b32ceeed764c30248c32","seq":1,"wave":"dev-wave-t564-dependency-source"}
- {"allocations":{"F:artifact-ingest-breaks-corpus-completeness":"F140","F:second-artifact-turns-single-element-pick-nondeterministic":"F141"},"authored":"2026-08-06","content_sha256":"64950e701e3cb80c869d6aad9b128cc7f14944a048455a595cc5a328978e5356","seq":1,"wave":"dev-wave-t564-dependency-source"}

- {"allocations":{"D:s8c-wiring-not-fireable":"D201"},"authored":"2026-08-06","content_sha256":"d09ff6b4ad0c9ba27cc1b57b065a9faac6bbd24c959b79d30f9b4bcab8a78f25","seq":1,"wave":"dev-wave-t244-p3-8c-wiring"}
- {"allocations":{},"authored":"2026-08-06","content_sha256":"42b726584c2bfd1e051b262529e34272c78347d2d821fda4102761206b5972bc","seq":2,"wave":"dev-wave-t244-p3-8c-wiring"}
- {"allocations":{},"authored":"2026-08-06","content_sha256":"1d98958226d86c64d1300cd988004fae409ed43d910830e2222e20f78f1ac26b","seq":3,"wave":"dev-wave-t244-p3-8c-wiring"}

- {"allocations":{"D:generation-guarantee-scope-limit":"D203","D:historical-reverify-entry-split":"D202"},"authored":"2026-08-06","content_sha256":"439c3034b7f638b13019a15051d1380e6e68633141e9d710f2dde31fb0afab26","seq":1,"wave":"dev-wave-t574-historical-resolver"}
- {"allocations":{"T:generation-resume-availability":"[T-587]","T:oracle-run-contract-legacy-fallopen":"[T-588]","T:silo-verify-result-semantics":"[T-586]"},"authored":"2026-08-06","content_sha256":"bacfadcef1123374c54ba03a326bd76b8388ade81320f5650264991486714408","seq":2,"wave":"dev-wave-t574-historical-resolver"}
- {"allocations":{"F:readonly-entry-shared-with-live-admission":"F142","F:redundant-gate-counted-as-new-guarantee":"F143"},"authored":"2026-08-06","content_sha256":"ddc5b88fd30f32134ca1ec2d35b65f955c763e1b6408a4f37b9d162352fb1d17","seq":3,"wave":"dev-wave-t574-historical-resolver"}

- {"allocations":{"T:cleanup-dangling-codex-rewrite":"[T-589]","T:fetch-third-party-admission":"[T-591]","T:merge-provenance-author-rule":"[T-590]"},"authored":"2026-08-06","content_sha256":"42ad6cd573c50f1ecc787743b49fe05735640a5e2dde01300b7724e620f45e00","seq":1,"wave":"rulings-20260806-a"}
- {"allocations":{"D:branch-deletion-user-instruction":"D204"},"authored":"2026-08-06","content_sha256":"5be68689314f27377800aeb8ea2ef7e2b4bbe287d489222427bbed96070ef1ab","seq":2,"wave":"rulings-20260806-a"}
- {"allocations":{"T:dangling-audit-scope-fixes":"[T-593]","T:dw-rules-batch-adoption":"[T-592]","T:guard-worktree-compound-analysis":"[T-594]"},"authored":"2026-08-06","content_sha256":"d0599245f2f954793d8f55b951cb7843b5d1b4b8d627c841334c9550e278633c","seq":3,"wave":"rulings-20260806-a"}
- {"allocations":{},"authored":"2026-08-06","content_sha256":"bfcf610b0b37492999daa0d8feab2907a3658679e32732e851c7bbac50835dbb","seq":4,"wave":"rulings-20260806-a"}
- {"allocations":{},"authored":"2026-08-06","content_sha256":"f5e5ac7873bc5bb9e2160fa9ed7ff74dd26e79b88d4e51ffeeb9d2c5b9776054","seq":5,"wave":"rulings-20260806-a"}
- {"allocations":{},"authored":"2026-08-06","content_sha256":"c0e7074d623c926a77ee60d916ac6a390856e03c4ab9a765e9a3b9f8b12597b4","seq":6,"wave":"rulings-20260806-a"}
- {"allocations":{},"authored":"2026-08-06","content_sha256":"bb336c8f09c42b7a45f5e298faa41a76c45d860f152d6b5907edf824b9001f59","seq":7,"wave":"rulings-20260806-a"}
- {"allocations":{},"authored":"2026-08-06","content_sha256":"6356f14231749a134ec193b2e9cef90e4a5e7ff6bdb70c72d0f9fe4672a4461b","seq":8,"wave":"rulings-20260806-a"}
- {"allocations":{},"authored":"2026-08-06","content_sha256":"7fe69cfb26af11f55485d10923f0132b759b7983a60df79b78b4cd34e15b65b8","seq":9,"wave":"rulings-20260806-a"}
- {"allocations":{"D:prototype-robustness-bar":"D205"},"authored":"2026-08-06","content_sha256":"d769a9f166f835635fe2911791f33ca34010e69c54bb1564822a2aa2aedada42","seq":10,"wave":"rulings-20260806-a"}

- {"allocations":{"D:claude-session-ledger":"D206","D:effort-downshift-needs-controlled-experiment":"D207","D:no-fixed-token-rates-in-entry-docs":"D208"},"authored":"2026-08-06","content_sha256":"316b9193cb85dd207a07e493d2f6c9cb78dcdf1b4a193ad387bf27d25a429891","seq":1,"wave":"dev-wave-token-hygiene"}
- {"allocations":{"F:bg-job-idled-without-a-wait":"F145","F:measurement-double-count-reported-to-user":"F144"},"authored":"2026-08-06","content_sha256":"a737decc61fc7ebc0ec536efbd62acf0d63b10b6869a2f64020baed1091818f9","seq":2,"wave":"dev-wave-token-hygiene"}
- {"allocations":{"T:claude-session-ledger-consumers":"[T-598]","T:codex-effort-ab-evaluation":"[T-595]","T:dev-wave-reference-budget-exhausted":"[T-597]","T:main-provenance-trailer-red":"[T-596]"},"authored":"2026-08-06","content_sha256":"91584765f8b41aa6dff7bda40a7508d79326cf7b2cd585a11d7f059bc994df99","seq":3,"wave":"dev-wave-token-hygiene"}

- {"allocations":{},"authored":"2026-08-06","content_sha256":"5c01dac163b27b2dba858671e18e107ee21a9e20fcdd5601da59d275be5d573f","seq":1,"wave":"dev-wave-t244-u10-draft"}
- {"allocations":{"F:fix-begets-fix":"F146"},"authored":"2026-08-06","content_sha256":"a028310995444a9afd3c91df4558aab21c563c053403a8381f44a63b57211c0f","seq":2,"wave":"dev-wave-t244-u10-draft"}

- {"allocations":{},"authored":"2026-08-06","content_sha256":"2fed40a8cd025b16b8c27395d814ee58e8922c18ce32ed731ba9bce7506b578b","seq":11,"wave":"rulings-20260806-a"}

- {"allocations":{},"authored":"2026-08-06","content_sha256":"09856c7b6f40ac4a158d48b569e456948b23a562085ea2924d223ac8813e9b0a","seq":12,"wave":"rulings-20260806-a"}

- {"allocations":{"T:four-outcome-ledger":"[T-601]","T:login-build-namespace":"[T-599]","T:reclaim-credit-ruling":"[T-600]","T:scope-escape-containment":"[T-602]"},"authored":"2026-08-06","content_sha256":"65576c74de0ca7a6fcff44394e7405cf71ec4355d6599cb816aa651a4dba4b7c","seq":1,"wave":"dev-wave-t300-login-headroom"}
- {"allocations":{"D:login-headroom-admission":"D209","D:no-arbitrary-argv-bounded-launcher":"D210"},"authored":"2026-08-06","content_sha256":"332df86f8b8c14ed49f564b671a558057b0105e2e5479a36de09a050bb147cb6","seq":1,"wave":"dev-wave-t300-login-headroom"}
- {"allocations":{"F:clean-tree-precondition-kills-normal-work":"F148","F:new-behavior-broke-existing-tool-contract":"F149","F:refusal-path-side-effect":"F147"},"authored":"2026-08-06","content_sha256":"9df742a8c04f804e9403237f8910521e2040418f7dc31852f97d84000801477d","seq":1,"wave":"dev-wave-t300-login-headroom"}

- {"allocations":{"T:check-docs-positive-control-flake":"[T-603]","T:login-bounded-scope-attest-failure":"[T-604]"},"authored":"2026-08-07","content_sha256":"db204c2fed1513e2d4dc3b235f8b9737624264ef6d968744cbc8519410ae62ed","seq":1,"wave":"dev-wave-t244-p3-u3-ever-issued"}
- {"allocations":{"D:u3-ever-issued-not-monotone":"D211"},"authored":"2026-08-07","content_sha256":"03d334d975b287ea90141ea67256e4c66331d5be96afb02fd9eeea680c8194d3","seq":2,"wave":"dev-wave-t244-p3-u3-ever-issued"}

- {"allocations":{"D:current-only-resume-spec":"D213","D:receipt-expectation-scope":"D212","D:silo-verify-result-current-compat":"D214"},"authored":"2026-08-07","content_sha256":"a5bed81b172ef1db3a2816f165e9158c8498b717400db3b449cea36671e96257","seq":1,"wave":"dev-wave-t574-world"}
- {"allocations":{"T:generator-hash-rollover":"[T-608]","T:receipt-diagnostic-reach":"[T-605]","T:reverify-reachability":"[T-607]","T:v2-manifest-producer":"[T-606]"},"authored":"2026-08-07","content_sha256":"0a10a56268ef2bd96058d4383d307f4e07dc206e90496d42dab9d0511ff3bd5b","seq":2,"wave":"dev-wave-t574-world"}
- {"allocations":{"F:tautological-exception-type-pin":"F150"},"authored":"2026-08-07","content_sha256":"ce9622204c6e4e0fba251e58b29f2ab79f392880e6736703332d3ac711f64cbf","seq":3,"wave":"dev-wave-t574-world"}

- {"allocations":{},"authored":"2026-08-07","content_sha256":"4f5e6563a34b116e896df0c1d139b801e20dc6970cbf91bd2b6c659835d09d48","seq":4,"wave":"dev-wave-t574-world"}

- {"allocations":{"T:certified-writer-prewrite-closure":"[T-609]"},"authored":"2026-08-07","content_sha256":"161a292b0f7f8943b8c28959ca5f93962989402505da25c2c8a3d7147540fbb3","seq":1,"wave":"dev-wave-t529-activation-impl"}
- {"allocations":{"D:activation-authority-blocked-by-entry-surface":"D215"},"authored":"2026-08-07","content_sha256":"2b04a920cad5636f1415d98db96ee50aa7a7921a05daa3beca34a82b2c9ab446","seq":2,"wave":"dev-wave-t529-activation-impl"}
- {"allocations":{"F:ruling-matched-by-topic-not-options":"F151"},"authored":"2026-08-07","content_sha256":"a5e24c7402e37d45d314c76e66760a5ab0e3afcea8906df74c5d3549de1aeaa4","seq":3,"wave":"dev-wave-t529-activation-impl"}

- {"allocations":{"T:mutation-harness-force-dispatch":"[T-613]","T:mutation-worktree-activation-package":"[T-610]","T:mutation-worktree-run-location-class":"[T-611]","T:mutation-worktree-stale-gc":"[T-612]"},"authored":"2026-08-07","content_sha256":"80fb55d138d0a5a8b95022cb8e56e9108e10fef8735c00e4db0b136609d02c63","seq":1,"wave":"dev-wave-t503-disposable-worktree"}
- {"allocations":{"D:disposable-mutation-worktree":"D216"},"authored":"2026-08-07","content_sha256":"eb01dae4bf11347f62ff0138d0a91f3d1e5d6b04f290db02717abb74734fccc1","seq":2,"wave":"dev-wave-t503-disposable-worktree"}
- {"allocations":{"F:stage1-rc-read-through-pipe":"F152"},"authored":"2026-08-07","content_sha256":"e551b551c0c8d0d1d0fd62a236f177143fc878f9ebc69215b28a1ce53f925b4a","seq":3,"wave":"dev-wave-t503-disposable-worktree"}

- {"allocations":{},"authored":"2026-08-07","content_sha256":"0e073239598ee6e40bb4e941da1bc914ac4df941774ba0f4ee8b0b1d0fa4bc92","seq":1,"wave":"dev-wave-t244-p3-u8-critic"}
- {"allocations":{"D:critic-after-cell-admission":"D217"},"authored":"2026-08-07","content_sha256":"93bf2c3a7cac88e9e8a0c9c803530632879a13fee4d569839a786fe4eb3c4fb2","seq":2,"wave":"dev-wave-t244-p3-u8-critic"}

- {"allocations":{},"authored":"2026-08-07","content_sha256":"ca68583974ccc672dcee0edf0329f325f8eb4b4707d45e58287969f2980c1e2c","seq":13,"wave":"rulings-20260806-a"}

- {"allocations":{"T:provenance-red-repair":"[T-614]"},"authored":"2026-08-07","content_sha256":"1b24451e3995312995f2bd569a05a2e0ccbe9055e4e9e779bc60c8271220f06f","seq":1,"wave":"dev-wave-red-tests"}
- {"allocations":{"F:acceptance-shape-silent-gate-skip":"F153"},"authored":"2026-08-07","content_sha256":"251f36bb9244e3d834568a97d4bdce4a1a0e8b0ee5b832ece814790850731bdf","seq":1,"wave":"dev-wave-red-tests"}
- {"allocations":{},"authored":"2026-08-07","content_sha256":"a76c40a428963e3cde88154b972635a0baedca1dae525ffa309b493443e5d43b","seq":2,"wave":"dev-wave-red-tests"}

- {"allocations":{},"authored":"2026-08-07","content_sha256":"d46c9ffbf4670c29d77fbf712a63b630125ec1272ee90487d0db50f22e73dbb8","seq":14,"wave":"rulings-20260806-a"}

- {"allocations":{"T:calibration-activation-frozen-protocol":"[T-615]","T:registered-glob-nondeterminism":"[T-617]","T:withdrawn-ruling-not-propagated-policy":"[T-616]"},"authored":"2026-08-07","content_sha256":"e8276b2cc09b2f4f5c78f0b31a22af87aa0a48f0a107a85f5dc46feddbc6c147","seq":1,"wave":"dev-wave-t419-iii"}
- {"allocations":{"D:independent-verification-satisfied-form":"D218"},"authored":"2026-08-07","content_sha256":"e39931e498fc5c77059ec15946408fd0bfd64769ab4a78c1fca85358f095aa77","seq":2,"wave":"dev-wave-t419-iii"}
- {"allocations":{"F:withdrawn-ruling-not-propagated":"F154"},"authored":"2026-08-07","content_sha256":"4fefaf164e1b6f8cee8d3ca6c90527b49718d69b0e7fe1d0ededf839cc55f7dd","seq":3,"wave":"dev-wave-t419-iii"}

- {"allocations":{},"authored":"2026-08-07","content_sha256":"dd54e8b6829e8c0a51032277ac10736338a0dbd48c874cec50264848e6eeec89","seq":15,"wave":"rulings-20260806-a"}

- {"allocations":{},"authored":"2026-08-07","content_sha256":"ba8987c6ad480f21463130ea5c6fd2d0a087df2fe7e717e606940d6f8cbe1e44","seq":1,"wave":"dev-wave-t244-8c-wiring-design"}
- {"allocations":{"D:wiring-preconditions-8c":"D219"},"authored":"2026-08-07","content_sha256":"2fee6cc5f15e0ec6a1e2973a18229d1401f52ba21fa79ce15a9eb879267a700e","seq":2,"wave":"dev-wave-t244-8c-wiring-design"}

- {"allocations":{},"authored":"2026-08-07","content_sha256":"50e59a860021b61b20b6beaa3de6dc13d39543975b0ba53eb83563030bd07abf","seq":1,"wave":"dev-wave-t598-ledger-consumer"}
- {"allocations":{"D:claude-ledger-consumer-wiring":"D220"},"authored":"2026-08-07","content_sha256":"17fcf6f8ef6163b1fdee827b4961b4018b422657798e690603dfd97455ae3446","seq":2,"wave":"dev-wave-t598-ledger-consumer"}

- {"allocations":{"T:dev-wave-mutation-runner-mode-doc":"[T-620]","T:provenance-audit-consumer-gap":"[T-621]","T:provenance-default-range-blind-spot":"[T-619]","T:provenance-known-violation-residual":"[T-618]"},"authored":"2026-08-07","content_sha256":"874eeedc965c838b9169081927f21dc2940132086681f1633832bf8cac0a3144","seq":1,"wave":"dev-wave-t614-provenance-ledger"}
- {"allocations":{"D:known-violation-ledger":"D221","D:nonacceptance-run-warning":"D222"},"authored":"2026-08-07","content_sha256":"4db9d4ef06fbf4fb59e520cf05ee5d01788e7d80d0e00c127bfc6adcd0c049d4","seq":2,"wave":"dev-wave-t614-provenance-ledger"}

- {"allocations":{"T:reasoning-ab-apparatus-generalization":"[T-622]"},"authored":"2026-08-07","content_sha256":"fc00a7b98cc7b5b2be05c8d0ea04df51589a1258f2d27a227e89ddbf0a5fd68f","seq":1,"wave":"dev-wave-t595-reasoning-ab"}
- {"allocations":{"D:reasoning-ab-endpoint-requires-full-waves":"D224","D:reasoning-effort-adoption-latch":"D223"},"authored":"2026-08-07","content_sha256":"9f32d4b29d769b694b9eb65ff8a2ee625c968ee96ca730ea096ee4eedbdfba5e","seq":2,"wave":"dev-wave-t595-reasoning-ab"}
- {"allocations":{},"authored":"2026-08-07","content_sha256":"bdf02f11e5842e493bf419ecb25fd0530aa27733e240fde84ccf26c49fedfaa2","seq":3,"wave":"dev-wave-t595-reasoning-ab"}

- {"allocations":{"T:d-transition-rule-wording-hole":"[T-624]","T:floor-protocol-invalid-return-single-reason":"[T-623]"},"authored":"2026-08-07","content_sha256":"c2bcbd3e9c2adf503290a6cadc1adb50a6b7032b1a23b62646e215e5d8daeb23","seq":1,"wave":"dev-wave-t529-impl-reraise"}
- {"allocations":{"D:floor-protocol-two-lane":"D226","D:g04-firing-material-exists":"D225"},"authored":"2026-08-07","content_sha256":"4822c9b7bedcd541d3dfb2e6f2429904d6c672704544fc9b813f390da474228a","seq":2,"wave":"dev-wave-t529-impl-reraise"}
- {"allocations":{"F:mutation-collection-preflight":"F155","F:stale-done-file-short-circuits-waiter":"F156"},"authored":"2026-08-07","content_sha256":"402f6b6c6ff8d5429c7cf4b082ee9ee2f27390ad9c4c80f2e25ca6b656f92abb","seq":3,"wave":"dev-wave-t529-impl-reraise"}

- {"allocations":{"T:mutation-rf-effective-option":"[T-626]","T:waiter-rule-dispatch-strength":"[T-625]"},"authored":"2026-08-07","content_sha256":"e1be0ff35c071ced649fecca907f5c3a576094f255be1b200577c897d730899f","seq":1,"wave":"dev-wave-t597-budget"}
- {"allocations":{},"authored":"2026-08-07","content_sha256":"2875c9b4562792418bf9de16c7d0d21d1918dd57aca792fba975f5d4a24d2b27","seq":2,"wave":"dev-wave-t597-budget"}
- {"allocations":{"D:budget-reduction-by-duplication":"D227"},"authored":"2026-08-07","content_sha256":"0e9874b88434bac9152df6858cb2c4ef17d6b71c3d0b3b09e209c57ed9faf6a9","seq":3,"wave":"dev-wave-t597-budget"}

- {"allocations":{},"authored":"2026-08-07","content_sha256":"928d5e90d871004c5cf05e7e37906fae4bcdf670636959d507d0be03bb19bdc1","seq":16,"wave":"rulings-20260806-a"}

- {"allocations":{},"authored":"2026-08-07","content_sha256":"fb8206725c5a66ef8758c49ea4bcde060ccd05c65fb146e68786a55a3eae889a","seq":17,"wave":"rulings-20260806-a"}

- {"allocations":{"D:activation-transition-rejects-no-op":"D228"},"authored":"2026-08-07","content_sha256":"17e8510b0d231585e706772ec05b00564e5a3eb65947b433aac631995523e64e","seq":1,"wave":"dev-wave-t624-activation-noop"}
- {"allocations":{},"authored":"2026-08-07","content_sha256":"3b063eef33933bfa27b54a8b6d8826314447dad577caa152c8700cf172a13e1a","seq":2,"wave":"dev-wave-t624-activation-noop"}
- {"allocations":{"T:activation-env-membership-migration":"[T-628]","T:activation-transition-predicate-form":"[T-627]"},"authored":"2026-08-07","content_sha256":"f7e01790413c3880f3e360d4a8c1077f297cbad3b2ae7441a6ef92311e59773a","seq":3,"wave":"dev-wave-t624-activation-noop"}

- {"allocations":{},"authored":"2026-08-07","content_sha256":"3af261ecabb40ddbdc4e9947d5f2ee768d6908963fd04bf0da59ca0c6e461982","seq":1,"wave":"dev-wave-t139-mainrun-design"}
- {"allocations":{"D:t139-mainrun-design":"D229"},"authored":"2026-08-07","content_sha256":"aaca7271dedd7d7c92d764e4c8496607e084dacb27c518614384263f2ca6781f","seq":2,"wave":"dev-wave-t139-mainrun-design"}
- {"allocations":{"F:ruling-fact-finding-staleness":"F157"},"authored":"2026-08-07","content_sha256":"d8e13afc693db9889fc5ad4ea217e57986c755f5fd313d8a9a724fd0bfb28972","seq":3,"wave":"dev-wave-t139-mainrun-design"}

- {"allocations":{"T:provenance-audit-argmax-scale":"[T-630]","T:provenance-scope-needle-ambiguity":"[T-629]"},"authored":"2026-08-07","content_sha256":"84638133123820959ded2a3c63562da9f69008c3d9cf03c794e1eb903cbda69e","seq":1,"wave":"dev-wave-t619-provenance-range"}
- {"allocations":{"D:provenance-uniform-epoch-predicate":"D230"},"authored":"2026-08-07","content_sha256":"4e5b61426fca35672867997d20eb107975c844b2e6c65bb8ef54f26659240b97","seq":1,"wave":"dev-wave-t619-provenance-range"}

- {"allocations":{"T:mutation-single-reason-vs-single-node":"[T-631]"},"authored":"2026-08-07","content_sha256":"e74612c654601a5fd0df92f1ac0445b4e6a264c524ac538a31aff7b252b854cd","seq":1,"wave":"dev-wave-t618-provenance-known-ledger"}
- {"allocations":{"D:known-violation-note-field":"D231"},"authored":"2026-08-07","content_sha256":"cad60e19e32075454398f7750daa0ccd6e7e4a3fc6d0be8028812a6068507dc9","seq":2,"wave":"dev-wave-t618-provenance-known-ledger"}
- {"allocations":{},"authored":"2026-08-07","content_sha256":"a49998b178ba25710f2d847a98a75062561c0f765de36cf5266e2d2f6dde6478","seq":3,"wave":"dev-wave-t618-provenance-known-ledger"}

- {"allocations":{},"authored":"2026-08-07","content_sha256":"2ee1a230c356ad01d0af5abc7b65f1c7550140c81982422bbbd70dc0797e566a","seq":18,"wave":"rulings-20260806-a"}

- {"allocations":{},"authored":"2026-08-07","content_sha256":"a543f49cce38e1e7b18146f096f54122424bba1c2007177ec5abd28bc69de8dc","seq":19,"wave":"rulings-20260806-a"}

- {"allocations":{},"authored":"2026-08-07","content_sha256":"16fe70df71d0219d036d5964abee12cee12c8114e5782836d7163d7001ecfa63","seq":20,"wave":"rulings-20260806-a"}

- {"allocations":{},"authored":"2026-08-07","content_sha256":"ff65c3e896b79602493b5bce6f42e5910385922b05ef150779a752ba4260e6fd","seq":21,"wave":"rulings-20260806-a"}

- {"allocations":{"T:condition-table-unparsable-row":"[T-637]","T:dispatch-condition-literal-pin-policy":"[T-634]","T:m08-old-run-undefined":"[T-636]","T:s01-ruling-source-scope":"[T-635]","T:waiter-dispatch-observability":"[T-633]","T:waiter-rule-fourth-element":"[T-632]"},"authored":"2026-08-07","content_sha256":"af12b797673e19f7c3e7dbd7b75589b7323fce22e0b5d265f969658d6aad2351","seq":1,"wave":"dev-wave-t625-waiter-dispatch"}
- {"allocations":{"F:pre-ruling-proposal-as-decision":"F158"},"authored":"2026-08-07","content_sha256":"8862aaf2c0c8d77e559a9b439bbfb80300fae2fc86bbb44518fae84474327f48","seq":2,"wave":"dev-wave-t625-waiter-dispatch"}

- {"allocations":{"T:ai-classification-turn-violation-handling":"[T-639]","T:usage-collector-siting-classification":"[T-638]"},"authored":"2026-08-07","content_sha256":"1d18fac0702c6df89207bc9cb701750750b91c16ad832beca353e76b897fd610","seq":1,"wave":"dev-wave-t598-forward-collection"}
- {"allocations":{"D:wave-usage-missing-rule":"D232","D:wave-usage-selector-and-siting":"D233"},"authored":"2026-08-07","content_sha256":"176d2fa76b233bb5d5dc1b7c94c7ea9b7a1ffe6cbe383e545e6682ea08d1063d","seq":2,"wave":"dev-wave-t598-forward-collection"}
- {"allocations":{"F:ai-ran-classification-measurement":"F159","F:fix-narrowed-acceptance-without-positive-control":"F161","F:unclassified-tool-on-login-node":"F160"},"authored":"2026-08-07","content_sha256":"454ad79efc8c0426c29209dd615fb07acdd805751bb53c7d419a88bf25b1a8da","seq":3,"wave":"dev-wave-t598-forward-collection"}

- {"allocations":{"D:t139-paired-prereg-gate":"D234"},"authored":"2026-08-07","content_sha256":"cd0a21c8d36e8684188925e2cfb2b868e9fcda28e3999fcac42f0e10fa3e3228","seq":1,"wave":"dev-wave-t139-prereg-freeze"}
- {"allocations":{"T:devwave-budget-exhausted":"[T-641]","T:devwave-zero-diff-acceptance-scope":"[T-642]","T:t139-producer-preconditions":"[T-643]","T:t139-samechange-residual":"[T-640]"},"authored":"2026-08-07","content_sha256":"bccbe60611c069a74c583e4ef496797c6ff7abe2f362387e64d43a1bc9b4b62b","seq":2,"wave":"dev-wave-t139-prereg-freeze"}
- {"allocations":{},"authored":"2026-08-07","content_sha256":"d6f57618f76fd5f79b751765bb3bc227cb599baf7bbc5c64fd988971a0df5183","seq":3,"wave":"dev-wave-t139-prereg-freeze"}

- {"allocations":{"T:floor-protocol-source-commit-binding":"[T-646]","T:no-bench-certified-contract-scope":"[T-647]","T:site-policy-evidence-hardening":"[T-645]","T:write-free-attestation-before-first-write":"[T-644]"},"authored":"2026-08-07","content_sha256":"fc6a5a7bda31b9bdabc8af09c1ea155dd3d4f4b38c68d2bf01573e3ae4f0e834","seq":1,"wave":"dev-wave-t609-certified-writer-closure"}
- {"allocations":{"D:certified-writer-sink-authorization":"D235","D:tests-declare-site-not-inherit":"D236"},"authored":"2026-08-07","content_sha256":"496a388d537b273f9a4bf9b0f7d3d055aa478021397047baf6d8207685165468","seq":2,"wave":"dev-wave-t609-certified-writer-closure"}
- {"allocations":{"F:fix-child-fail-open-to-green":"F162","F:stale-base-worktree-integration":"F163"},"authored":"2026-08-07","content_sha256":"4789bc6395c9ed437f15617667bfef5c3fef220f33e2903e152337a9c65ba8d8","seq":3,"wave":"dev-wave-t609-certified-writer-closure"}

- {"allocations":{},"authored":"2026-08-08","content_sha256":"2e23688d1f7c88e1d28bc73595227c8a6566506873019fc0f386a31fcbc1a6ab","seq":22,"wave":"rulings-20260806-a"}

- {"allocations":{},"authored":"2026-08-08","content_sha256":"de557cedc78ea10e237cb2d9a296c7044fb34692468a37cd4164d924ca846a36","seq":1,"wave":"dev-wave-t632-waiter-condition"}
- {"allocations":{"F:qdel-deleted-peer-session-job":"F164"},"authored":"2026-08-08","content_sha256":"51e239b1528f485a5eff24cde1f8ab810629c06ab0858202b404c6ad8929f97c","seq":2,"wave":"dev-wave-t632-waiter-condition"}

- {"allocations":{"T:devwave-acceptance-exemption-evidence":"[T-648]"},"authored":"2026-08-08","content_sha256":"25e5e2960a039f659f6ee49d2eef123b79925ec94316fdadd25bb793228e6fdd","seq":1,"wave":"dev-wave-t642-s04-scope"}
- {"allocations":{"D:dev-wave-reference-self-funding":"D238","D:dw-s04-acceptance-not-exempt":"D237"},"authored":"2026-08-08","content_sha256":"c4af4cf4121cc8154be561344a887b67a9850ecf622b4a5b03526b4207b4064f","seq":2,"wave":"dev-wave-t642-s04-scope"}

- {"allocations":{},"authored":"2026-08-08","content_sha256":"651c7392e96e1e9766aa5391703ce22fea64cf25cc38df2b2228d2230d9615d4","seq":1,"wave":"dev-wave-t139-producer"}
- {"allocations":{"F:corrected-estimate-reintroduced":"F165"},"authored":"2026-08-08","content_sha256":"c247a8b77d01017197e9822fd8479b9f7ff2d0a4e848c49926b5f3b2210680d7","seq":2,"wave":"dev-wave-t139-producer"}

- {"allocations":{"T:acceptance-walltime-headroom":"[T-653]","T:land-tool-byte-invariant":"[T-654]","T:lease-e2e-measurement":"[T-651]","T:lease-fencing-token":"[T-649]","T:lease-transaction-wrapper":"[T-650]","T:receiver-contract-jit":"[T-652]"},"authored":"2026-08-08","content_sha256":"357b3d677f650cbc94b2a0b2194e5c8f08ec8ae7e57a7c5f9d80a6aa88777b0f","seq":1,"wave":"dev-wave-peer-land-coordination"}
- {"allocations":{"D:acceptance-lease-advisory":"D239"},"authored":"2026-08-08","content_sha256":"5d157af9c8df30ce49fe98025e6166511bbf41961502388a059e7fd7c7a3400c","seq":2,"wave":"dev-wave-peer-land-coordination"}
- {"allocations":{"F:acceptance-walltime-exceeded":"F167","F:mutation-runner-ran-local":"F166"},"authored":"2026-08-08","content_sha256":"419aa979a5c85e8ee2b146d49257ad7a3e628722059b75fcf4a501ab426507a5","seq":3,"wave":"dev-wave-peer-land-coordination"}

- {"allocations":{"T:acceptance-run-walltime-headroom":"[T-656]","T:admission-measured-table-non-pegasus":"[T-655]"},"authored":"2026-08-08","content_sha256":"ef01865e99fa2979f11a0d2399078a3145aa3a6f3756a5c2315737468c48a752","seq":1,"wave":"dev-wave-t639-admission-scope"}
- {"allocations":{"D:admission-scope-deny-only":"D240"},"authored":"2026-08-08","content_sha256":"d6c3956c7859250e5d2a37055477a88d4a47e35badfdc5354a19d8d1056ffe05","seq":2,"wave":"dev-wave-t639-admission-scope"}
- {"allocations":{"F:mutation-expected-nodes-overdetermined":"F168"},"authored":"2026-08-08","content_sha256":"2fed1bfb6336d8f9c16844862f9c7c02b3263983b58dfd0e7b515660a5fdc34d","seq":3,"wave":"dev-wave-t639-admission-scope"}

- {"allocations":{"T:activation-issue-deploy-window":"[T-659]","T:activation-receipt-entry-wiring":"[T-658]","T:activation-tail-rollback-observability":"[T-660]","T:dev-wave-budget-for-grep-authority":"[T-661]","T:pegasus-g2-activation":"[T-657]"},"authored":"2026-08-08","content_sha256":"80ea2cb553c8119aaeda0c0362295671912353de53c561fd9911a59493cb41ba","seq":1,"wave":"dev-wave-t529-activation"}
- {"allocations":{"F:grep-r-misses-tracked-hit":"F169"},"authored":"2026-08-08","content_sha256":"b5b88edf591313b26cb8ea3dbfd4fdc944f3eb88f09b531f1a89ac12de324249","seq":2,"wave":"dev-wave-t529-activation"}

- {"allocations":{"T:codex-worker-launch-truth-table-flake":"[T-663]","T:dev-wave-docs-budget-relief":"[T-664]","T:dev-wave-model-runtime-binding":"[T-662]"},"authored":"2026-08-08","content_sha256":"dfb6e7b8fb1c9a3f4b6a94bbfb878de446d0af427d867f189eef52395f30a088","seq":1,"wave":"worktree-dev-wave-t182-luna-stage3"}
- {"allocations":{"D:dev-wave-model-single-authority-absence-pin":"D242","D:stage3-hybrid-model-user-ruling":"D241"},"authored":"2026-08-08","content_sha256":"1e5a1e351f63aae05a259c55c89e0174627b2e48a8a3c6866a478978d9ed85b5","seq":2,"wave":"worktree-dev-wave-t182-luna-stage3"}

- {"allocations":{"D:stage6-reasoning-high":"D243"},"authored":"2026-08-08","content_sha256":"b8b2a4f701681e4d98e5f20c9957983fbf6a1b8a29bd7a9faaa372d3e9ef9bff","seq":1,"wave":"dev-wave-t181-stage6-high"}
- {"allocations":{"F:substring-pin-tautology":"F170"},"authored":"2026-08-08","content_sha256":"ddcc63ac162d08681e1b78a9ecdb66cdece07704df7ff6af41a7d6f61563acfb","seq":2,"wave":"dev-wave-t181-stage6-high"}
- {"allocations":{"T:cr-only-section-extraction":"[T-668]","T:main-sha-stop-gate":"[T-669]","T:stage5-effort-pin-residual":"[T-667]","T:stage6-launcher-binding":"[T-665]","T:wording-pin-freeze":"[T-666]"},"authored":"2026-08-08","content_sha256":"7d055656edce537ac7a1bea4e118f7f394175e040cebe4e9e6c4a0a1ed3e0134","seq":3,"wave":"dev-wave-t181-stage6-high"}

- {"allocations":{},"authored":"2026-08-08","content_sha256":"8c505e5a21aec74e1f81a54c18f6a14db9d9c89f3b61ff92eda49d5de1739643","seq":1,"wave":"dev-wave-t139-addendum-a"}
- {"allocations":{},"authored":"2026-08-08","content_sha256":"e448981105092f4a3e5ccee97dc72ce938e147ef96e151674ecf711a20d8cbf8","seq":2,"wave":"dev-wave-t139-addendum-a"}

- {"allocations":{"T:walltime-queue-wait-correlation":"[T-670]"},"authored":"2026-08-08","content_sha256":"6762dce2b523b05560b40cabf244e540e9ce13b6b2381f32277f54b93a5aa6ea","seq":1,"wave":"dev-wave-t656-walltime"}
- {"allocations":{"D:dispatch-default-walltime-40min":"D244"},"authored":"2026-08-08","content_sha256":"3cc7bcdc473b79fea6752260d9734be9cb3ddab14419f31104f42c9160b18465","seq":2,"wave":"dev-wave-t656-walltime"}
- {"allocations":{},"authored":"2026-08-08","content_sha256":"e7cad804904b303e23dd40cdf1acfb62b38f06ae2935b083c1f7f6fc8bd1a721","seq":3,"wave":"dev-wave-t656-walltime"}

- {"allocations":{"D:activation-transition-bound-pair":"D245"},"authored":"2026-08-08","content_sha256":"fa67818eb8e8317af0e27d2dd828a4458d445a841d2e6ee783cf681ec8a75f6e","seq":1,"wave":"dev-wave-t627-noop-binding"}
- {"allocations":{"T:activation-certified-writer-source-binding":"[T-671]","T:activation-transition-property-based-tests":"[T-673]","T:dev-wave-mid-wave-contract-change":"[T-672]"},"authored":"2026-08-08","content_sha256":"4c3c1c3bbe9966f61b66987edf2a4f0e58d417fe76d906f3213f9e518962d824","seq":2,"wave":"dev-wave-t627-noop-binding"}

- {"allocations":{},"authored":"2026-08-08","content_sha256":"47442d21c8701fe66528433168a0c3098b89d49effd74f02466ac959bd10adc4","seq":1,"wave":"dev-wave-t665-t662-launch-binding"}

- {"allocations":{"T:certified-read-boundary-ruling-package":"[T-674]"},"authored":"2026-08-09","content_sha256":"4456138b5f3faf53809e202dce33c3fdf32ad8dc6049c979be5b1069031b4521","seq":1,"wave":"dev-wave-t530-contract-hash-binding"}
- {"allocations":{"D:contract-hash-identity-and-commit-binding":"D246"},"authored":"2026-08-09","content_sha256":"49fbc7b140def587f82c15aa3a31440a0d48731aad2fa3dc00fa4bb329c89e6a","seq":2,"wave":"dev-wave-t530-contract-hash-binding"}
- {"allocations":{"F:codex-auth-expiry-mid-wave":"F172","F:dual-module-identity-across-test-and-production":"F171"},"authored":"2026-08-09","content_sha256":"4c30e44c622bb420b1becdb445cc3b13bae1462b5c7753a52b56a01dbe173187","seq":3,"wave":"dev-wave-t530-contract-hash-binding"}

- {"allocations":{},"authored":"2026-08-09","content_sha256":"fa9ef8cf1a7be009be816958e710c917b0b86f623169fa10dbc92e4651577bb9","seq":1,"wave":"dev-wave-t337-t339-rf-ruling"}

- {"allocations":{"T:whole-file-pin-semantic-gap":"[T-675]"},"authored":"2026-08-09","content_sha256":"c74da12be4fee419af0f49a22faf277e5a8f1c9d950787a63c7c4acd50759b83","seq":1,"wave":"dev-wave-dangling-audit-offrepo-authority"}
- {"allocations":{"D:offrepo-copy-needs-landed-reference":"D247","D:path-boundary-set-is-fail-safe-inverted":"D248"},"authored":"2026-08-09","content_sha256":"45c5acb969b5270593b673f956913cbc047c7309b7b501ba6acfa3a30e692430","seq":1,"wave":"dev-wave-dangling-audit-offrepo-authority"}
- {"allocations":{"F:budget-trim-removed-safety-pointer":"F173"},"authored":"2026-08-09","content_sha256":"6bcde4fc501f19bc9c4cad284db49b41985253283ad4fcab3d9db72717434f8e","seq":1,"wave":"dev-wave-dangling-audit-offrepo-authority"}

- {"allocations":{},"authored":"2026-08-09","content_sha256":"6d4343c873ea4882196c9e875a9a2895868a700fcd65146d0e276174b1953291","seq":1,"wave":"dev-wave-t659-activation-deploy-window"}
- {"allocations":{},"authored":"2026-08-09","content_sha256":"ac13989af935d11e1afa11a59876fbf4691904a01ebad3855faf70304fd28714","seq":2,"wave":"dev-wave-t659-activation-deploy-window"}

- {"allocations":{"T:dispatch-relay-diagnostic-reach":"[T-677]","T:flake-absence-evidence":"[T-680]","T:launcher-early-receipt":"[T-679]","T:launcher-fixture-budget-ruling":"[T-676]","T:probe-clean-tree-gate":"[T-681]","T:publication-wall-gate-gap":"[T-678]"},"authored":"2026-08-09","content_sha256":"ab32db70467bc216db84fa50ae02ac9d49e936aea201013d58fab73e0ab097d7","seq":1,"wave":"dev-wave-t663-flaky-truth-table"}
- {"allocations":{"D:flake-instrument-before-widening":"D249","D:flake-instrumentation-must-not-depend-on-the-flake":"D250"},"authored":"2026-08-09","content_sha256":"5d2a6024188414adff54344c46d54897d14b2c41b884f76a156216f666f1444e","seq":2,"wave":"dev-wave-t663-flaky-truth-table"}
- {"allocations":{"F:checkout-restore-wiped-uncommitted-child-work":"F174","F:flake-instrumentation-broke-under-the-flake":"F175"},"authored":"2026-08-09","content_sha256":"3c14442451eaec0859a0f8fa04d159f8e485095fd7551dbcc1704e0fefa38c52","seq":3,"wave":"dev-wave-t663-flaky-truth-table"}

- {"allocations":{},"authored":"2026-08-09","content_sha256":"6e819af0dc034bfbc1093cc296d1aad391c83b6a3b0e6c0c6d745e316b468c55","seq":1,"wave":"dev-wave-t316-semantic-gate"}

- {"allocations":{"T:t659-probe-missing-codex-author":"[T-682]"},"authored":"2026-08-09","content_sha256":"630640e57aa8d3cba245f06547f0c4f2dd3e2974c1f6f6f26c67cc21ba5e08e2","seq":1,"wave":"dev-wave-t648-fallback-ledger"}
- {"allocations":{},"authored":"2026-08-09","content_sha256":"8428740dde8445a2a1d102aedf826ca6364f7c6ed06540f013f068fcc5175eef","seq":2,"wave":"dev-wave-t648-fallback-ledger"}

- {"allocations":{},"authored":"2026-08-08","content_sha256":"8df386241fa2cb3b766dfa9719805331d27e0dd38de8c1115cf50539018b8120","seq":23,"wave":"rulings-20260806-a"}
- {"allocations":{},"authored":"2026-08-08","content_sha256":"9354c3a881581dda8ad420de24d6cae3c0fd42e8d9565e351460e1fc5adcd1aa","seq":24,"wave":"rulings-20260806-a"}
- {"allocations":{},"authored":"2026-08-08","content_sha256":"d5d4e1c0a3ddc1a9f0bb670d5d5f5b6868400c171efb03d967bb77d9ea9f803b","seq":25,"wave":"rulings-20260806-a"}
- {"allocations":{},"authored":"2026-08-08","content_sha256":"7195229ffb6944f72ff627c84bcab7721c5227c62e3d499530df1e4f5563aab3","seq":26,"wave":"rulings-20260806-a"}
- {"allocations":{},"authored":"2026-08-08","content_sha256":"9b6da840bac8cbf2499a43b72b64eea3ec8ceb3e470ac8be6bb8ad2011a909aa","seq":27,"wave":"rulings-20260806-a"}
- {"allocations":{},"authored":"2026-08-09","content_sha256":"bff79286f65d630daad87b4d6addb5b1cf8d80810cb890d610cb83a2f2ec6945","seq":1,"wave":"rulings2-20260809"}

- {"allocations":{},"authored":"2026-08-08","content_sha256":"75a9fb646ac290a464934f25f95dd40848ee9b4416a65c1445c88a2e7c7ac934","seq":1,"wave":"dev-wave-t664-docs-budget"}
- {"allocations":{},"authored":"2026-08-08","content_sha256":"8a3874fde71f62c627605acdb74bedd62113147908b51843b43ce31275137a8b","seq":2,"wave":"dev-wave-t664-docs-budget"}

- {"allocations":{"T:acceptance-lease-fairness":"[T-684]","T:caller-inventory-any-tautology":"[T-683]"},"authored":"2026-08-09","content_sha256":"88d882ae14d45af64091c8b0f5b7e5e53e5b110d7c93dd2c0a9777b8d1a0567b","seq":1,"wave":"dev-wave-t671-source-binding"}

- {"allocations":{},"authored":"2026-08-09","content_sha256":"e1055cdc238b3392d380917e26d1b4af2b2133608d53d81aa497d655d7411e4e","seq":1,"wave":"dev-wave-t139-r4-probe"}

- {"allocations":{},"authored":"2026-08-09","content_sha256":"ad4a791905d0986e55ba403d1127fb6e8a529a3c7ac9ee7280a139a47731c5dc","seq":1,"wave":"dev-wave-t659-evidence-erratum"}

- {"allocations":{},"authored":"2026-08-09","content_sha256":"13ef1a13a267a1d1405fb02f69a27cdbe9c28849174521c5ab1e5bad72859e97","seq":28,"wave":"rulings-20260806-a"}
- {"allocations":{},"authored":"2026-08-09","content_sha256":"fc36eb2411b5f0a79fbeba2bb2ede13ccc1c51d92687c75d32681588f072e8e1","seq":1,"wave":"rulings2-20260809-b"}

- {"allocations":{"T:score-decision-extraction-defect":"[T-685]"},"authored":"2026-08-09","content_sha256":"959f039b57d2d9658c32ecc0578ec50ed49e7c9a95d0f8e9cb5e6748aeedd52b","seq":1,"wave":"dev-wave-t181-certified-rerun"}
- {"allocations":{"F:frozen-scorer-decision-regex":"F176"},"authored":"2026-08-09","content_sha256":"ac041fff54e820e7f740554c1edd67d93a389207f3cf44b1741bd5c5dfcf3889","seq":1,"wave":"dev-wave-t181-certified-rerun"}

- {"allocations":{"T:insights-verbatim-not-checked":"[T-686]"},"authored":"2026-08-09","content_sha256":"e6af09df648007308fc90c8abfde0d8df2ce8d5134cd34b4d4321e6be0454fed","seq":1,"wave":"dev-wave-t682-provenance-known-violations"}
- {"allocations":{"F:blacklist-only-note-gate":"F177"},"authored":"2026-08-09","content_sha256":"b2c84d87a6d76a810af429d5a77829ca980028eda8140f10095a99e83c3da475","seq":2,"wave":"dev-wave-t682-provenance-known-violations"}

- {"allocations":{"D:diagnostic-line-prefix-not-pipe":"D252","D:failure-digest-producer-side":"D251"},"authored":"2026-08-09","content_sha256":"19ae57d58fe2f3f59b3dbf72046c094601158282b7fc232a9f978b7bd6c4c52a","seq":1,"wave":"dev-wave-t677-relay-reach"}
- {"allocations":{"F:in-tree-temp-test-tree":"F178"},"authored":"2026-08-09","content_sha256":"80eb22600a57ab87d36f1907d30d371daa82d25aa5d8e0d3034006bf40ef0af3","seq":2,"wave":"dev-wave-t677-relay-reach"}
- {"allocations":{"T:dev-wave-docs-budget-full":"[T-690]","T:digest-infra-kill-evidence":"[T-688]","T:digest-stash-session-binding":"[T-691]","T:digest-xdist-crash-coverage":"[T-687]","T:relay-best-effort-durability":"[T-689]"},"authored":"2026-08-09","content_sha256":"1e9151c686c2d4b305f6a19327f66b4140cb81556135428e5af3b38478516c1e","seq":3,"wave":"dev-wave-t677-relay-reach"}

- {"allocations":{"T:s8c-wall-clock-budget-policy":"[T-692]"},"authored":"2026-08-09","content_sha256":"6509e68498a632735635aebf484924e134dbb23f5ac591fec19ecb04d67ddb8f","seq":1,"wave":"dev-wave-red-suite-20260809"}
- {"allocations":{},"authored":"2026-08-09","content_sha256":"fc262047be04ca91e49b9e830bf03ff590efa94aba91cf7a7d330875dc764444","seq":2,"wave":"dev-wave-red-suite-20260809"}

- {"allocations":{"T:canonical-lease-waiter":"[T-694]","T:lease-claim-rc-semantics":"[T-693]"},"authored":"2026-08-09","content_sha256":"2e49d6b1957ad78260e52a575ff93b531e903f9eb72b881742583e76da47e352","seq":1,"wave":"dev-wave-t684-lease-fifo"}
- {"allocations":{"D:acceptance-lease-fifo-queue":"D253"},"authored":"2026-08-09","content_sha256":"c74662dd41cfcea2585659ed5ac3233469e86bceb8ca410a4870054970540af3","seq":1,"wave":"dev-wave-t684-lease-fifo"}
- {"allocations":{"F:acceptance-lease-no-fairness":"F179","F:fifo-queue-self-sustaining-deadlock":"F180"},"authored":"2026-08-09","content_sha256":"b75754a857bad3b2f8ecae011fe5507492d9c96703a1b2128099137b8ce226d9","seq":1,"wave":"dev-wave-t684-lease-fifo"}

- {"allocations":{"T:dev-wave-docs-budget-blocks-gate-sync":"[T-695]","T:exploration-external-root-test-red-both-nodes":"[T-698]","T:land-gate-immutable-trust-root":"[T-696]","T:s8c-git-batch-timeout-under-load":"[T-697]"},"authored":"2026-08-09","content_sha256":"0b54137fe4e0321b0628fd47930f4855c2f6a6e3dce841e94afddd49c6c54942","seq":1,"wave":"dev-wave-t139-provenance-known-violation"}
- {"allocations":{"D:land-ff-only-provenance-gate":"D254"},"authored":"2026-08-09","content_sha256":"8155801802269121b357a1092c7d52b2469641ff66f80850fc1566530baf4b8b","seq":1,"wave":"dev-wave-t139-provenance-known-violation"}
- {"allocations":{},"authored":"2026-08-09","content_sha256":"4aa1a5845eed50ffcf547172ceaa9950c2b9e53f5faa3efc24616af49caedd4a","seq":1,"wave":"dev-wave-t139-provenance-known-violation"}

- {"allocations":{"T:dev-wave-ctx-supervisor-wiring":"[T-702]","T:dev-wave-read-scope-envelope":"[T-701]","T:dispatch-cell-grammar":"[T-699]","T:l2-admission-control":"[T-700]"},"authored":"2026-08-09","content_sha256":"402ba9c55b19580a1fc26b8433b25be179561ce4e20e2d7efa68e1b8e1159a64","seq":1,"wave":"dev-wave-t313-read-budget-gate"}
- {"allocations":{"D:dev-wave-layer-read-budget":"D255"},"authored":"2026-08-09","content_sha256":"6bd82c195c3fd6f85359c14028428bfce047f0ea90b1b0596d80893696c2363b","seq":2,"wave":"dev-wave-t313-read-budget-gate"}
- {"allocations":{"F:range-marker-over-expansion":"F181"},"authored":"2026-08-09","content_sha256":"7643a4205b7e4ae051a43672872413a1e240419c36e2a9877734402b8db385c7","seq":3,"wave":"dev-wave-t313-read-budget-gate"}

- {"allocations":{"F:fragment-update-clobbers-pending-ruling":"F182"},"authored":"2026-08-09","content_sha256":"c9901aaa5cae2045127406d4afae04179094bc7bd03f64e6a70ea8b3b422452c","seq":1,"wave":"rulings-20260806-a"}
- {"allocations":{},"authored":"2026-08-09","content_sha256":"b1a6bd5cb88bde11edec2282c561ea1271732b528348240fe94d06f5412e9887","seq":29,"wave":"rulings-20260806-a"}
- {"allocations":{},"authored":"2026-08-09","content_sha256":"fdb4dc02553c2711835dbdb86fed655992ba522f25010f2070bd3430b7df813b","seq":30,"wave":"rulings-20260806-a"}
- {"allocations":{},"authored":"2026-08-09","content_sha256":"75a9526d6124b841decb32a730f79497c89680518d1b42ff9cd3cf0fd47e03b4","seq":31,"wave":"rulings-20260806-a"}

- {"allocations":{"T:atomic-publish-output-rollback":"[T-705]","T:launcher-interrupt-rc-split":"[T-706]","T:mutation-positive-control-subset":"[T-709]","T:publication-commit-protocol":"[T-703]","T:receipt-post-commit-exception":"[T-704]","T:replace-invalid-publication-pin":"[T-708]","T:staged-temp-replacement-window":"[T-707]"},"authored":"2026-08-09","content_sha256":"7504586913392ff2813674fe5b9c7190c60a4ae9e4ac3fe3c3838764c0bd36ef","seq":1,"wave":"dev-wave-t678-publication-wall-gate"}
- {"allocations":{"D:late-admission-gate-at-last-reversible-point":"D256"},"authored":"2026-08-09","content_sha256":"381cd40658829b40776eebffa11ad00b3f9663a19c338ec019802d463873c92a","seq":1,"wave":"dev-wave-t678-publication-wall-gate"}

- {"allocations":{"T:conflict-failure-reason-diagnostic":"[T-712]","T:scorer-decision-grammar-contract":"[T-710]","T:spool-failures-update-path":"[T-711]"},"authored":"2026-08-09","content_sha256":"a25fb458d0c6d271a1e324f4fccfa8f441ba1561ec739a73d1a0908646a4b4ae","seq":1,"wave":"dev-wave-t685-scorer-erratum"}
- {"allocations":{"F:mutation-spec-diverged-from-preregistration":"F184","F:scorer-conflict-guard-inert":"F183"},"authored":"2026-08-09","content_sha256":"8c3ed0d27b29eb00215f9a0cb63e7048239137b36a6e646993653bd924df8ac0","seq":2,"wave":"dev-wave-t685-scorer-erratum"}

- {"allocations":{},"authored":"2026-08-09","content_sha256":"087ecf010e2238ae858f3353df2bf931eeeac4cfcfb320a42a09f625e0cb3e81","seq":1,"wave":"dev-wave-provenance-model-switch-rule"}

- {"allocations":{"T:evidence-path-control-char":"[T-714]","T:s8c-heavy-git-xdist-group":"[T-713]"},"authored":"2026-08-09","content_sha256":"33740252c49c16f1476ebc1483ada6ec4adc8fc0462467c0ef383081e4869520","seq":1,"wave":"dev-wave-t553-git-budget"}
- {"allocations":{"D:git-work-proportional-budget":"D257"},"authored":"2026-08-09","content_sha256":"27be8510a9271fa22fd1dba33a8d3246d6963c7c909c46ebe6ac610686cb7175","seq":2,"wave":"dev-wave-t553-git-budget"}
- {"allocations":{"F:lease-state-matched-literally":"F186","F:mutation-spec-timeout-below-dispatch-floor":"F185"},"authored":"2026-08-09","content_sha256":"93b10a0cc036e9ca3fc74fdf7d9801da25763adcb432dfcda32f54e3a5f5ce20","seq":3,"wave":"dev-wave-t553-git-budget"}

- {"allocations":{},"authored":"2026-08-09","content_sha256":"40e904aaf1ff6bce870bb1353de6e498f50df74579c66ec96d99907fbe51cd09","seq":1,"wave":"dev-wave-t673-transition-pbt-package"}
- {"allocations":{},"authored":"2026-08-09","content_sha256":"3a4e0a100f796d4c1cf3f7ea88acc1199620b98da96551895cb91019a71cfa8f","seq":2,"wave":"dev-wave-t673-transition-pbt-package"}

- {"allocations":{"T:acceptance-walltime-ceiling":"[T-717]","T:cli-second-resolution":"[T-718]","T:mutation-expected-node-overdetermination":"[T-719]","T:realrepo-payer-closure":"[T-715]","T:s8c-canonical-group":"[T-716]"},"authored":"2026-08-10","content_sha256":"4787b49e85645f990bd3fecc2df6165abe75f6e8c3f4b21a9489796123b8f119","seq":1,"wave":"dev-wave-t692-r3-xdist-walltime"}
- {"allocations":{"D:xdist-group-closure-audit":"D258"},"authored":"2026-08-10","content_sha256":"6a6d7b86746aa36d24eb97cad666d7149770605a632c11867ca3d718a57a380e","seq":1,"wave":"dev-wave-t692-r3-xdist-walltime"}

- {"allocations":{"D:campaign-identity-authority-split":"D259"},"authored":"2026-08-09","content_sha256":"e1d434e13e6b08716d45bd1b3209ce514c34c553eb5bab2d67563bc7cd6b4dff","seq":1,"wave":"dev-wave-t671-impl"}
- {"allocations":{"T:authority-external-anchor":"[T-722]","T:guided-lane-nonforgeable-marker":"[T-723]","T:import-namespace-unification":"[T-720]","T:r1-closure-expansion":"[T-721]"},"authored":"2026-08-09","content_sha256":"3af0defaa7d06c85816834c49775153df77826a83bb4b558c79ead6a5fa27bcc","seq":2,"wave":"dev-wave-t671-impl"}
- {"allocations":{"F:dual-import-namespace-breaks-exact-type-checks":"F187","F:parent-adds-gates-outside-approved-ruling":"F188"},"authored":"2026-08-09","content_sha256":"69da3a4f8f6674d38e9385fd6a73ab0762fadcbc11a50aa6157b23256fcd2051","seq":3,"wave":"dev-wave-t671-impl"}

- {"allocations":{},"authored":"2026-08-09","content_sha256":"b6cd991c3cf930fbc869f1261401fa23fd149801d2ad91c89ab2cafc86a52ebd","seq":32,"wave":"rulings-20260806-a"}

- {"allocations":{"T:spool-fold-carry-legacy-stub":"[T-724]"},"authored":"2026-08-09","content_sha256":"e9960b1c781698e7993a4f9300c5da716ec39d6ec54c6bd9e72b76eb48bf76bd","seq":1,"wave":"dev-wave-suite-floor-recheck"}
- {"allocations":{"D:history-scan-copy-clause":"D260"},"authored":"2026-08-09","content_sha256":"6c6600c4d34b76efa90cd09f746d177c6574d7a9e09a2b36ed36086f3c754fe2","seq":2,"wave":"dev-wave-suite-floor-recheck"}
- {"allocations":{"F:acceptance-in-synthetic-checkout":"F189","F:spool-fold-carry-legacy-stub":"F190"},"authored":"2026-08-10","content_sha256":"7dba74ed1840e72ec32ad8631933c3721844210457179f75f09cad2401237f87","seq":3,"wave":"dev-wave-suite-floor-recheck"}

- {"allocations":{},"authored":"2026-08-10","content_sha256":"5b1881d8f7ad1bf260020af2eaad898636047e92d12a4513148892a8447febad","seq":33,"wave":"rulings-20260806-a"}

- {"allocations":{},"authored":"2026-08-10","content_sha256":"dc5f52dc273b8564523dc8ff71506345404333c836dc67e897fb3797fdf72b6d","seq":1,"wave":"dev-wave-t657-restore-redesign"}

- {"allocations":{"T:acceptance-lease-merge-after-acquire":"[T-725]"},"authored":"2026-08-10","content_sha256":"5929e142d566ff342ef56afc16f385a0a5b6215f736bcf36d27c73da3e8a6ce4","seq":1,"wave":"dev-wave-t674-d125-supersession"}
- {"allocations":{"D:d125-campaign-id-invariance-superseded":"D261"},"authored":"2026-08-10","content_sha256":"c0cdbb8d3048dfd73a586c1ee19598352f6daf44c01f06ba1744112c8f5d5a7d","seq":1,"wave":"dev-wave-t674-d125-supersession"}
- {"allocations":{"F:acceptance-lease-behind-livelock":"F191"},"authored":"2026-08-10","content_sha256":"39a653c683bd34052d1e340797ba9b7e1007711ab5a06431b70ffebf29fa9409","seq":2,"wave":"dev-wave-t674-d125-supersession"}

- {"allocations":{},"authored":"2026-08-10","content_sha256":"0a984a5c01892fa8d09210efff675181e8123b09f8a4e90e0e5615cbf9de1bd2","seq":1,"wave":"dev-wave-t139-producer-slice"}
- {"allocations":{"D:t139-erratum-validator-registry":"D263","D:t139-reference-binding-not-a-gate":"D264","D:t139-stage2-approval-payload":"D262"},"authored":"2026-08-10","content_sha256":"3af3cd1569bba51d4e28ccbc9aaa32e8a46a5a087476196fed1454531d661706","seq":2,"wave":"dev-wave-t139-producer-slice"}
- {"allocations":{"F:codex-child-reads-parent-protocol-as-own":"F193","F:lease-json-matched-as-plaintext":"F192"},"authored":"2026-08-10","content_sha256":"a54723a8be242d3e875f4a7245bfb67cfbe91d146e9514539fbfd0e6a0d0e264","seq":3,"wave":"dev-wave-t139-producer-slice"}

- {"allocations":{"T:ruleops-batch-blob-memory-bound":"[T-729]","T:ruleops-cap-is-per-call-only":"[T-727]","T:ruleops-default-controls-swallows-git-timeout":"[T-728]","T:ruleops-preflight-60s-ceiling":"[T-726]"},"authored":"2026-08-10","content_sha256":"ca4813c584ee0bf9761ed74a81a732d9e47a11d126b7ee8b5f61d788ee7023f1","seq":1,"wave":"dev-wave-t510-ruleops-git-budget"}
- {"allocations":{"D:ruleops-git-timeout-budget":"D265"},"authored":"2026-08-10","content_sha256":"cf9bd040483ffd734475868a4c3a2c170c6278268a0b253517501563c6658bd5","seq":2,"wave":"dev-wave-t510-ruleops-git-budget"}
- {"allocations":{"F:parametrize-id-breaks-node-extraction":"F194"},"authored":"2026-08-10","content_sha256":"dc8e2d7254b89ce830d0fd139c648e27221e7ad4a9523e0988d55d7d72cf5574","seq":3,"wave":"dev-wave-t510-ruleops-git-budget"}

- {"allocations":{"D:stage-reasoning-policy-adoption":"D266"},"authored":"2026-08-10","content_sha256":"099f190e68c68fe2641b109a49d90306e80fb9f192c4c5d1d7673fc0a9e359bf","seq":1,"wave":"dev-wave-t184-reasoning-policy"}
- {"allocations":{},"authored":"2026-08-10","content_sha256":"266de09a59255b4d3170967e0eaf3cc43fec34f470d67b251338cfc4a1d42c75","seq":2,"wave":"dev-wave-t184-reasoning-policy"}
- {"allocations":{},"authored":"2026-08-10","content_sha256":"658e3387528edbfc7c5c62b68af8d9828792d5009adac54da8dd87b9c03808d8","seq":3,"wave":"dev-wave-t184-reasoning-policy"}

- {"allocations":{"T:evidence-path-nul-alias":"[T-730]","T:land-test-scope-dependent-red":"[T-731]"},"authored":"2026-08-10","content_sha256":"f781fc1618f9e716fdb2d21c08c180ae3cf042d915b5165236ddd5eba8223a7d","seq":1,"wave":"dev-wave-t714-evidence-path-ctrlchar"}
- {"allocations":{"D:evidence-path-identity-wall":"D267"},"authored":"2026-08-10","content_sha256":"0e2c2976175b17aee371e1b7d52689b99de518b247e77a40c612d149facafe14","seq":2,"wave":"dev-wave-t714-evidence-path-ctrlchar"}
- {"allocations":{"F:lease-claim-output-is-json":"F195"},"authored":"2026-08-10","content_sha256":"b1412b2d5f85d7070f373cef0afad7daafb583d0bb7e6ae9614ef474c602c8ad","seq":3,"wave":"dev-wave-t714-evidence-path-ctrlchar"}

- {"allocations":{"T:acceptance-lease-waiter-merge-contract":"[T-732]"},"authored":"2026-08-10","content_sha256":"2c1c15e4f84e1d4b7eb69a32537ebb7dd9497f3f872c73c6c6428f5c6548d8af","seq":1,"wave":"dev-wave-t683-caller-closure"}
- {"allocations":{"F:acceptance-lease-overtaken-while-queued":"F196"},"authored":"2026-08-10","content_sha256":"96c287c043ca741889af665c49470ae575021a5c84c5821eca1a525a934424bc","seq":2,"wave":"dev-wave-t683-caller-closure"}

- {"allocations":{"T:certified-sink-gate":"[T-734]","T:enforcement-transitive-closure":"[T-733]","T:local-run-tmp-git-ancestor":"[T-736]","T:source-closure-wire-rename":"[T-735]"},"authored":"2026-08-10","content_sha256":"6c9f1ec00aa4f17ec4d82ee26f0dfcf33f2b85e29d0d0c1daa6de8a125413d16","seq":1,"wave":"dev-wave-t721-source-closure"}
- {"allocations":{"D:enforcement-source-closure":"D268"},"authored":"2026-08-10","content_sha256":"30ef680599ddee8710abeada63b11fb32eb996010177904d1db064b326f9b858","seq":2,"wave":"dev-wave-t721-source-closure"}
- {"allocations":{"F:acceptance-lease-starves-on-prefetch-merge":"F197"},"authored":"2026-08-10","content_sha256":"d6c4c1b0754b907f02d26107bd66eb915c20ffcb72b7094d975db6b372b11605","seq":3,"wave":"dev-wave-t721-source-closure"}

- {"allocations":{},"authored":"2026-08-10","content_sha256":"6dffa1ea154f5b8901abd0160d3ad89bf1c21a012933af4dc7770a05eaa6a31d","seq":34,"wave":"rulings-20260806-a"}

- {"allocations":{"T:loader-issuer-integration-pin":"[T-737]"},"authored":"2026-08-10","content_sha256":"c3a548f0374df5c9bb0bbab2c51a396d12ee0a35f5394964073c8e50997c3d7b","seq":1,"wave":"dev-wave-t673-residual"}
- {"allocations":{"F:mutation-spec-field-contract-unwritten":"F198"},"authored":"2026-08-10","content_sha256":"19d7a44b628e1554ed2e04d20c1548e16123bb75776296dd1dd0e16a86839db3","seq":2,"wave":"dev-wave-t673-residual"}

- {"allocations":{"T:dev-wave-waiter-pid-rule":"[T-738]"},"authored":"2026-08-10","content_sha256":"8760c421bdb160d883242aa54e9744f7d51b817bc648503dc0bb546d503e7a77","seq":1,"wave":"dev-wave-t139-addendum-b2"}
- {"allocations":{},"authored":"2026-08-10","content_sha256":"0d2deb65ee395bbaca60e6ad675a034b101058ff4d5456f06c719908b0517b59","seq":2,"wave":"dev-wave-t139-addendum-b2"}

- {"allocations":{"D:guard-input-exact-str":"D269","D:lease-waiter-internal-merge":"D270"},"authored":"2026-08-10","content_sha256":"86d758a5a14bc4b0f26948944511a527d9618bf3b46d32195a91702b6a389eac","seq":1,"wave":"dev-wave-t730-t732-nul-lease-merge"}
- {"allocations":{"T:canonical-acceptance-waiter":"[T-740]","T:freeze-layer-nul-gate":"[T-739]","T:guard-non-str-input":"[T-742]","T:spool-failures-supersede":"[T-741]"},"authored":"2026-08-10","content_sha256":"8a8198cdf3879b8c767a61f329681bc9075cd3145eb05d470ca1cfd4f316b483","seq":2,"wave":"dev-wave-t730-t732-nul-lease-merge"}

- {"allocations":{},"authored":"2026-08-10","content_sha256":"44f5cd3abd359686c54d6e70a80a80dc4d2b6e42f7d3f0b3690f108075523102","seq":1,"wave":"dev-wave-t700-t695-l2-admission"}
- {"allocations":{"D:l2-admission":"D271"},"authored":"2026-08-10","content_sha256":"9e4c3d2516ad308561c46849bd2ac24e73ee2cbb3ecb385812bf8f44059c912c","seq":2,"wave":"dev-wave-t700-t695-l2-admission"}

- {"allocations":{"T:design-wave-review-rubric":"[T-743]"},"authored":"2026-08-10","content_sha256":"dcf3d95092953538995c2dd5fbbce9a08de1e05ebd724b9a4c895c584c77d190","seq":1,"wave":"dev-wave-t657-permanent-bundle-design"}
- {"allocations":{"D:calibration-freeze-authority-bundle":"D272","D:design-completion-criteria-need-positive-fixture":"D273"},"authored":"2026-08-10","content_sha256":"c374d85c32f03fd3af64c1d44156fa7445205be3ad52b3f3b28032671674ca36","seq":2,"wave":"dev-wave-t657-permanent-bundle-design"}

- {"allocations":{},"authored":"2026-08-10","content_sha256":"b58f7cd63dc6d660ec4c093de828ea58eeadd3a19ff66bfc93afe339915808c6","seq":35,"wave":"rulings-20260806-a"}
- {"allocations":{},"authored":"2026-08-10","content_sha256":"7f6b1aa4e7c0aff0f018c1d0c281300a39a8cf333c1f63f73ad75adf0791ee1b","seq":36,"wave":"rulings-20260806-a"}

- {"allocations":{},"authored":"2026-08-10","content_sha256":"879632ecf64347ab0c2bac75dc005814cb2fa731670586bb1a6fa8f0c33fa554","seq":3,"wave":"dev-wave-t657-permanent-bundle-design"}

- {"allocations":{},"authored":"2026-08-10","content_sha256":"a8b728430377d9a540619e9cbb17234b05c2aab1beacece6be4b2f77e03261d1","seq":37,"wave":"rulings-20260806-a"}

- {"allocations":{"T:dual-namespace-permanent-policy":"[T-744]","T:import-scan-non-source-artifacts":"[T-745]","T:t720-untracked-campaign-residue":"[T-746]"},"authored":"2026-08-10","content_sha256":"0491ac2f3fe3e69ea572ab6cc5ce9433a8295c296709da05d70080cd43b00ab2","seq":1,"wave":"dev-wave-t720-import-unify"}
- {"allocations":{"F:mutation-found-what-review-missed":"F199","F:parent-ruling-broke-under-measurement":"F201","F:secondary-fanout-missed-in-scope":"F200"},"authored":"2026-08-10","content_sha256":"9fe7d314d8e899dc0d4e43d97a1453bbda95736d765d84d3ecace076b5b8aba5","seq":2,"wave":"dev-wave-t720-import-unify"}

- {"allocations":{},"authored":"2026-08-10","content_sha256":"366815694db051a27b38084a10a8b059299e18a2ee4f277585da2b0288eeca99","seq":38,"wave":"rulings-20260806-a"}

- {"allocations":{},"authored":"2026-08-10","content_sha256":"41827a52a54ec81edf3e323957c4fe6a8d623a833c74e01e3370a5fc6e9ea71f","seq":1,"wave":"dev-wave-t675-pin-semantic-gap"}
- {"allocations":{"F:codex-child-oom-under-shared-user-cap":"F202"},"authored":"2026-08-10","content_sha256":"809a17a45a301ef1250e8528d8d09d759195db1f59ae7afcdd62253a1d861718","seq":1,"wave":"dev-wave-t675-pin-semantic-gap"}

- {"allocations":{"T:s8b-floor-toolchain-binding":"[T-747]","T:s8b-legacy-verify-cli-supersede":"[T-749]","T:s8b-restart-order-vs-generation":"[T-748]","T:s8b-v2-producer-and-manifest-wiring":"[T-750]"},"authored":"2026-08-10","content_sha256":"4815518b3203f106a018dcd12e109954f7dad774170fafded2193af25c6e3261","seq":1,"wave":"dev-wave-t8b-reopen-inspection"}

- {"allocations":{},"authored":"2026-08-10","content_sha256":"ef6aa8e3d0bfa277d1b4ffd41e65078779237887f435f627dfc6a12db2248a70","seq":39,"wave":"rulings-20260806-a"}
- {"allocations":{},"authored":"2026-08-10","content_sha256":"3b60930af22d7ef5f32818ed5bd5eb17ef7b9dc7db86b2f80f32f9c09d52460d","seq":40,"wave":"rulings-20260806-a"}
- {"allocations":{},"authored":"2026-08-10","content_sha256":"3b0f46e7a810f14b9403f9bba09635a3121bc6b489f5533ea471c377b509e1d0","seq":41,"wave":"rulings-20260806-a"}

- {"allocations":{},"authored":"2026-08-10","content_sha256":"77a8469ebcaa1a5a006e9413a7e024ef70f4ce503eccd0d84802dd88f5fe45f8","seq":42,"wave":"rulings-20260806-a"}

- {"allocations":{"T:mutation-expected-nodes-two-pass":"[T-753]","T:ruleops-epoch-evidence-checkpoint":"[T-751]","T:ruleops-history-boundary-race":"[T-752]","T:wave-startup-detect-duplicate-job":"[T-754]"},"authored":"2026-08-10","content_sha256":"f2053d9359a7f8de8c5777e288e1cf8485af4fc747207b72c2429fcbfca25a1c","seq":1,"wave":"dev-wave-t726-pickaxe-epoch"}
- {"allocations":{"D:ruleops-pickaxe-epoch-window":"D274"},"authored":"2026-08-10","content_sha256":"935ebf7065fedad6211535f85cda884fda0d2f824e0e1433dd78c9def9444f9b","seq":2,"wave":"dev-wave-t726-pickaxe-epoch"}
- {"allocations":{"F:duplicate-dev-wave-job":"F203"},"authored":"2026-08-10","content_sha256":"57ccc9651b1b612d2846096843b13ba8a1b726e4b1c77b3af7fc70724d44204a","seq":3,"wave":"dev-wave-t726-pickaxe-epoch"}

- {"allocations":{"T:ccbench-anatomy-corrections":"[T-758]","T:dev-wave-waiter-liveness-note":"[T-757]","T:s1-design-choice-ruling":"[T-755]","T:trace-completeness-v2":"[T-756]"},"authored":"2026-08-10","content_sha256":"124315288f708e92c2eade023fd860de3c24359c27a3bdeea355486272b7b017","seq":1,"wave":"dev-wave-s1-design-choice"}

- {"allocations":{},"authored":"2026-08-10","content_sha256":"f2a9c497bb7dc89c0cbbeb7b711bf8a48e1982ff8132af483c8e019bc672eb98","seq":1,"wave":"dev-wave-t316-sandbox-measure"}
- {"allocations":{"F:discharge-overrejection-unguarded":"F204","F:renameat2-einval-on-work":"F205"},"authored":"2026-08-10","content_sha256":"5d4452a11452080f1475d7d7afb5d2ec8dcb379af4e5582d0ae1502854e939f4","seq":1,"wave":"dev-wave-t316-sandbox-measure"}
- {"allocations":{"F:stale-checker-range-audit":"F206"},"authored":"2026-08-10","content_sha256":"2b661a26ba5eeec0e532044ddf187e4d448df27b92db1978963b177592d97fd9","seq":2,"wave":"dev-wave-t316-sandbox-measure"}

- {"allocations":{},"authored":"2026-08-10","content_sha256":"eab9c1cc83665a8abcb65751259459967f7786e257579ff24c5c4e4135c8b53d","seq":43,"wave":"rulings-20260806-a"}
- {"allocations":{},"authored":"2026-08-11","content_sha256":"30deb243250dc45ac236c9c6c8d1eccca4c104dccf68d4b13d80149dbd4e492f","seq":44,"wave":"rulings-20260806-a"}

- {"allocations":{"T:dispatcher-sandbox-normative":"[T-760]","T:launch-binding-set-equality":"[T-759]","T:u2028-branch-redundancy":"[T-761]"},"authored":"2026-08-10","content_sha256":"6f314c65f06d64b5d02b61cdddc9e40e690114a89a68ceebe24a6ba712d9214d","seq":1,"wave":"dev-wave-t665-t662-launch-binding-impl"}
- {"allocations":{"D:derived-value-test-needs-independent-oracle":"D276","D:launch-value-docs-binder":"D275"},"authored":"2026-08-10","content_sha256":"7995597b7150dffb531b01b99eddb4895d1ffd4d40ee7e8822f1b944b68ab2cf","seq":2,"wave":"dev-wave-t665-t662-launch-binding-impl"}
- {"allocations":{"F:derived-oracle-circular-test":"F207","F:documented-route-not-executable":"F208"},"authored":"2026-08-10","content_sha256":"18fdafa915de339172ce54648a0db1cb660b13729bd168161f9f414f746a5093","seq":3,"wave":"dev-wave-t665-t662-launch-binding-impl"}

- {"allocations":{"T:ident-activation-transition-pin":"[T-762]","T:issuer-test-syspath-restore":"[T-764]","T:loader-layer-semantic-kill":"[T-763]"},"authored":"2026-08-11","content_sha256":"99160070130fccb08a124d2a83e30d6f3e28ee20985f176265c84450cc0878eb","seq":1,"wave":"dev-wave-t737-rebuild"}
- {"allocations":{},"authored":"2026-08-11","content_sha256":"f3efe767a9e2d7159943b8d415c9592cb9a0f4b736e25101433a43391ed71897","seq":2,"wave":"dev-wave-t737-rebuild"}

- {"allocations":{"T:dw-s04-zero-diff-exemption":"[T-765]"},"authored":"2026-08-11","content_sha256":"0e4ac88a7b7cd2b218ec6fc79ce761306b0c7c1da933328a7d947930c02b3061","seq":1,"wave":"dev-wave-t139-publication-core"}

- {"allocations":{"T:dev-wave-l15-budget-headroom":"[T-769]","T:dry-run-after-bytes":"[T-768]","T:land-rollback-state-retention":"[T-766]","T:reserved-label-display-equivalence":"[T-767]"},"authored":"2026-08-11","content_sha256":"5fe8b35d5308af335c87b6127cf8127e2fc5f93459b6e6adecab5539f53a6898","seq":1,"wave":"dev-wave-t741-failures-supersede"}
- {"allocations":{},"authored":"2026-08-11","content_sha256":"a584715ae1966a28521f7fb4cb595bef224858ac4922a308a4ba8e35024dd528","seq":1,"wave":"dev-wave-t741-failures-supersede"}

- {"allocations":{},"authored":"2026-08-11","content_sha256":"2990edadcb7627242ef458aac71614a9ebcaac86472abe205235725e9adf96c3","seq":2,"wave":"dev-wave-t741-failures-supersede"}

- {"allocations":{"T:s8b-git-failure-skip-narrowing":"[T-771]","T:template-patch-test-window":"[T-770]"},"authored":"2026-08-11","content_sha256":"9a33c83f71935a2c49ee929d07586441ddacbced4c5315ecf3c9059d707b3c03","seq":1,"wave":"dev-wave-known-red-exceptions"}
- {"allocations":{"F:pseudo-skip-passes-as-green":"F209"},"authored":"2026-08-11","content_sha256":"8972eabe984df635815eb46068d930fb9af6adabe84b0b17dd2a47dda4720ce7","seq":2,"wave":"dev-wave-known-red-exceptions"}

- {"allocations":{"T:codex-launch-receipt-termination-flake":"[T-772]"},"authored":"2026-08-11","content_sha256":"0737287d91b73ca7de58b7b83851202b211ffb50f094ab0bb00c884ea07aca3d","seq":1,"wave":"dev-wave-t657-stage0"}
- {"allocations":{"D:calibration-freeze-authority-stage0":"D277"},"authored":"2026-08-11","content_sha256":"1a5c8f5867e3ae82e46b70a97c624e86f3f0d8f6e3b59e75b62c5e306c39e62f","seq":2,"wave":"dev-wave-t657-stage0"}

- {"allocations":{"T:dev-wave-l15-budget-exhausted":"[T-775]","T:mutation-harness-hang-artifact":"[T-776]","T:waiter-acceptance-shape":"[T-774]","T:waiter-consumer-binding":"[T-773]"},"authored":"2026-08-11","content_sha256":"3392c7f4bd6ad5e3fa96586922a788eb9e18939c75f74345edc4d3f137f2a939","seq":1,"wave":"dev-wave-t740-canonical-waiter"}

- {"allocations":{"D:address-edge-structural-lint":"D278"},"authored":"2026-08-11","content_sha256":"a78beec6b59fc844746ca03860cbb5635b10acd63cda7ba9089b83f14fbef7e1","seq":1,"wave":"dev-wave-t675-address-edge-lint"}
- {"allocations":{},"authored":"2026-08-11","content_sha256":"be8f9a33e21fb89216e0324cc408127a6c161afb86ac78e5b55bafe2b6e8a8c1","seq":2,"wave":"dev-wave-t675-address-edge-lint"}
- {"allocations":{"T:address-edge-lint-layer-coverage":"[T-777]","T:mutation-expected-node-scope-doc":"[T-778]"},"authored":"2026-08-11","content_sha256":"d3477ea1fc3923a0efd0d0004ad28d157e967f56c0c51d4664158c4b1f969f96","seq":3,"wave":"dev-wave-t675-address-edge-lint"}

- {"allocations":{},"authored":"2026-08-11","content_sha256":"5b55714e65329af83d078f48e9f2a091f1ce96f0b07911eb01e79460604a014a","seq":1,"wave":"dev-wave-t673-d-guard-measurement"}
- {"allocations":{"F:fold-dryrun-before-acceptance":"F212","F:guard-preempts-later-diagnostics":"F211","F:preregistered-nodes-need-runner-scope":"F210"},"authored":"2026-08-11","content_sha256":"8ddb59e74f014e310821bea4e3906095b3b611f95208e777e9f643d1fb2a5799","seq":2,"wave":"dev-wave-t673-d-guard-measurement"}

- {"allocations":{},"authored":"2026-08-11","content_sha256":"199e9ebf96f81a4dd884fd290170f3cd3878b05dd29f7a7085fa9178a5389a74","seq":4,"wave":"dev-wave-t675-address-edge-lint"}

- {"allocations":{"D:normative-section-exact-pin":"D280","D:o25-admission-exemption":"D279"},"authored":"2026-08-11","content_sha256":"b3fa7a42d1f53200ad1ca7e086bc6d75ae0642391beab98f344dc7fa9cdfeee9","seq":1,"wave":"dev-wave-t695-t700-l2-routing"}
- {"allocations":{"T:ruling-numbers-are-means":"[T-780]","T:stage5-recheck-main":"[T-779]"},"authored":"2026-08-11","content_sha256":"d9441702895a5163b09686eafd9a5eb223a5adb2e6cacd9217cc21eb159c3888","seq":2,"wave":"dev-wave-t695-t700-l2-routing"}

- {"allocations":{"T:dw-o09-hash-bound-dataclass":"[T-784]","T:floor-campaign-site-compiler":"[T-783]","T:legacy-cache-key-default-toolchain":"[T-785]","T:oracle-manifest-schedule-authority":"[T-782]","T:t088-admission-authority":"[T-781]"},"authored":"2026-08-11","content_sha256":"4bb18ca562478387665e4256ba0c890e272132e18d8f772ce1a95dd00a9c01ef","seq":1,"wave":"dev-wave-t8b-restart-integration"}
- {"allocations":{},"authored":"2026-08-11","content_sha256":"c5a87761c4e7c0d2ada5079b0278fddc15ec34b12cd54611fd098bac35d2ecc7","seq":1,"wave":"dev-wave-t8b-restart-integration"}

- {"allocations":{"T:rulings-sweep-budget":"[T-786]"},"authored":"2026-08-11","content_sha256":"b748da3ad3f8329f4e0f5c3a4ffa1651db7d0de90149d5ae4732ccddc0d9017e","seq":45,"wave":"rulings-20260806-a"}
- {"allocations":{"F:rulings-sweep-literal-miss":"F213"},"authored":"2026-08-11","content_sha256":"b2730230d5745f0399828914f8541b8e7420c01527ae549c06a26bcfd8e717c1","seq":46,"wave":"rulings-20260806-a"}

- {"allocations":{},"authored":"2026-08-11","content_sha256":"f02e1cae671b170a883d7ecc7f1f9a04ca83ac4011cc56f349f83ce3312ada98","seq":47,"wave":"rulings-20260806-a"}

- {"allocations":{},"authored":"2026-08-11","content_sha256":"fc67878040b3ab20624614f7984351d19158c8e4ca66a73219edbdb31c982cd1","seq":48,"wave":"rulings-20260806-a"}

- {"allocations":{"T:artifact-control-char-scan":"[T-788]","T:freeze-layer-crlf-gate":"[T-787]"},"authored":"2026-08-11","content_sha256":"0e12c49762351f6d7acc557fef3383a39e1c53424a77ce9fbc4c6cf6b9fae00a","seq":1,"wave":"dev-wave-t739-freeze-nul"}
- {"allocations":{"D:freeze-layer-nul-gate":"D281"},"authored":"2026-08-11","content_sha256":"348ece450c21548d437a677fb6c96be977605154db161e43d75b229674f01775","seq":2,"wave":"dev-wave-t739-freeze-nul"}

- {"allocations":{"T:dev-wave-docs-budget-review":"[T-789]"},"authored":"2026-08-11","content_sha256":"3cac629a35916738307bdb3d6d5b7a960a5738d62d6bddf95a33ff348fef8ed2","seq":1,"wave":"dev-wave-t139-manifest-land1"}
- {"allocations":{"D:t139-record-items-and-second-erratum-approval":"D282"},"authored":"2026-08-11","content_sha256":"5b3921bae872533a97528b69d420fc96e42f831366d8eaf5405bdf3973d7e055","seq":1,"wave":"dev-wave-t139-manifest-land1"}

- {"allocations":{},"authored":"2026-08-11","content_sha256":"28285996a3e64824f8cab679c0b34212b54e3691058d968213fd14be85ae4920","seq":49,"wave":"rulings-20260806-a"}

- {"allocations":{"T:conditional-unrun-boundary-run":"[T-790]","T:records-vs-acceptance-ordering":"[T-791]","T:reflux-sys-path-hidden-coupling":"[T-792]"},"authored":"2026-08-11","content_sha256":"33edcce0419a9eecf64ec66167b75af339ef6c90cd5be11e80abbd2747d84c75","seq":1,"wave":"dev-wave-t770-conditional-unrun"}

- {"allocations":{},"authored":"2026-08-11","content_sha256":"1ed693c8ce36ac5b148f0f0e7288d0449c5669581af2fa29624e5eb6e8ed0b81","seq":1,"wave":"dev-wave-t781-spool-feasibility"}

- {"allocations":{"T:t139-publication-layer-impl":"[T-793]"},"authored":"2026-08-11","content_sha256":"352b124f6132baf451d47d8cad297b6331772e462517243989d2f9780dae280c","seq":1,"wave":"dev-wave-t139-pubcore-stage2"}
- {"allocations":{"D:t139-addendum-b-no-primary-ledger-reference":"D284","D:t139-publication-downstream-exception":"D283"},"authored":"2026-08-11","content_sha256":"974f5bf8f70b5195859155a6f226470919257e21e6a1ee64c6622c9bc25c74a5","seq":1,"wave":"dev-wave-t139-pubcore-stage2"}
- {"allocations":{"F:diff-count-instrument-contaminated-claim":"F214"},"authored":"2026-08-11","content_sha256":"ddaf7ae112a3c4b46d3f8bcca81d1bd0e7fc798126b63718badebe3cf9f98e06","seq":1,"wave":"dev-wave-t139-pubcore-stage2"}

- {"allocations":{},"authored":"2026-08-11","content_sha256":"5d25712797501f1362162a7562125daec88c4c3e76c4f494f017312c0b476d1c","seq":50,"wave":"rulings-20260806-a"}

- {"allocations":{},"authored":"2026-08-11","content_sha256":"40e3400bcabea7e7b971ce8dc1b37843a62d541fcf5177f241559f4724ea8067","seq":51,"wave":"rulings-20260806-a"}

- {"allocations":{"T:cfab-design-row-extraction-declared-form-only":"[T-797]","T:cfab-revocation-record-schema":"[T-795]","T:cfab-stage0-completion-unreachable":"[T-794]","T:cfab-stage6-completion-predicate":"[T-796]"},"authored":"2026-08-11","content_sha256":"ceee57ea924a61366a0a9cf49a23dc85803ae25aaaf81bbb31e3768d0a267566","seq":1,"wave":"dev-wave-t657-stage0-rulings"}
- {"allocations":{"F:design-literal-hidden-in-html-comment":"F215","F:mutation-spec-renumbered-after-preregistration":"F216"},"authored":"2026-08-11","content_sha256":"e0c7ccd1aee1e877779e1bbaa415d9816720db1061f5403152b7cc8c2a292b02","seq":2,"wave":"dev-wave-t657-stage0-rulings"}
- {"allocations":{"D:design-literal-binding-rejects-html-comments":"D285","D:dev-wave-waiter-pid-and-codex-coldstart":"D286"},"authored":"2026-08-11","content_sha256":"5df2a09f5ffc1ceb3d42c4f3610bb0591b1a2b0fb7c2fc066aabe51a4834b4a6","seq":3,"wave":"dev-wave-t657-stage0-rulings"}

- {"allocations":{},"authored":"2026-08-11","content_sha256":"c17acce403a0391868c30845df177d186f171814bbe3aa86282e710169c3c2b3","seq":52,"wave":"rulings-20260806-a"}

- {"allocations":{"T:dryrun-git-admin-no-write":"[T-802]","T:fold-finalize-protocol":"[T-798]","T:fold-state-head-binding":"[T-799]","T:rollback-lifecycle-details":"[T-801]","T:rollback-state-inspection":"[T-800]"},"authored":"2026-08-11","content_sha256":"2eeeaec13db4463c9d5202a17ffcffa7ee0e3de03fb2f704e58fc354d0bdff92","seq":1,"wave":"dev-wave-t766-t768-resume-diff"}
- {"allocations":{},"authored":"2026-08-11","content_sha256":"694f8616196d584bb23ccda37c289c0d368b0776d68f9604b55357bcda032434","seq":2,"wave":"dev-wave-t766-t768-resume-diff"}

- {"allocations":{"T:budget-authorization-proof-chain":"[T-805]","T:dev-wave-launch-procedure-gaps":"[T-806]","T:legacy-writer-path-containment":"[T-807]","T:manifest-spec-propagation":"[T-804]","T:oracle-spec-trust-root":"[T-803]"},"authored":"2026-08-11","content_sha256":"7f5a3178022576be563e4ec0d2da5b0cc86f05d3d3c0d5f3b8dc47f1979770e9","seq":1,"wave":"dev-wave-t750-freeze-v2-manifest"}
- {"allocations":{"D:manifest-choke-point-cell-product":"D288","D:pinned-literal-human-approval":"D287"},"authored":"2026-08-11","content_sha256":"5f9d88e3a00e9858f75e594524d031898e23214e0aad30e74507a8cfe401e8bc","seq":2,"wave":"dev-wave-t750-freeze-v2-manifest"}

- {"allocations":{"T:mutation-fanout":"[T-808]","T:node-variance-protocol":"[T-810]","T:s8c-workload-fanout":"[T-809]"},"authored":"2026-08-11","content_sha256":"aa82b007952ae2f4f79a6c72e0a716ffda74a95b06c68bf9d823caf4163d147b","seq":1,"wave":"dev-wave-parallel-dispatch"}
- {"allocations":{"D:compute-job-fanout":"D289"},"authored":"2026-08-11","content_sha256":"6f3ce4f86046fcf3f0bcfc1ad9eca3a9e74c437c4a9f3dbd798e1372c89aa8d6","seq":2,"wave":"dev-wave-parallel-dispatch"}

- {"allocations":{},"authored":"2026-08-11","content_sha256":"4e831598e3abba12fdd1a17e97cf31071d86e28f00b9750586027410509ed0ac","seq":53,"wave":"rulings-20260806-a"}

- {"allocations":{},"authored":"2026-08-11","content_sha256":"c695efbaaf906fe771e35b22cf57e7b2749ae4faa234bff788ec5e687e9e5126","seq":54,"wave":"rulings-20260806-a"}

- {"allocations":{"T:dw-o01-lane-scope":"[T-811]"},"authored":"2026-08-11","content_sha256":"678fa8a38f4f114f15630f21bb0ceea90c0cc0252e33af1789eb6f9af9d8387a","seq":1,"wave":"dev-wave-t787-freeze-crlf"}
- {"allocations":{"D:freeze-crlf-single-call-scope":"D290"},"authored":"2026-08-11","content_sha256":"97a5d0186477a85eb090935b3292cf1673eb806e8811165fe518f02bfe92000f","seq":2,"wave":"dev-wave-t787-freeze-crlf"}

- {"allocations":{},"authored":"2026-08-11","content_sha256":"1f140c9a36ce8484b0400d47584594884537697a32acf6aa2719a03964c4827d","seq":1,"wave":"dev-wave-t139-pubcore-approve"}
- {"allocations":{"D:t139-publication-core-approval":"D291"},"authored":"2026-08-11","content_sha256":"ae26ddcb0f8dd681346f2e40993ee570bf4c09d658d31fadc8ba08c57717947c","seq":1,"wave":"dev-wave-t139-pubcore-approve"}

- {"allocations":{"D:submission-deny-release-authority":"D292"},"authored":"2026-08-11","content_sha256":"c71d0ddfbdd909d4f472aa18868cb4cef497d435fd27a151bbecda86c3be049b","seq":55,"wave":"rulings-20260806-a"}
- {"allocations":{},"authored":"2026-08-11","content_sha256":"7e4ef68b1dd9bbd1f817174c76bb909a49672e7a4eb5f7c7a0ca62e8a7575f20","seq":56,"wave":"rulings-20260806-a"}

- {"allocations":{"T:acceptance-lease-self-renew":"[T-812]"},"authored":"2026-08-11","content_sha256":"a47dc500a29c45571726f0ce04fcf9a93f416c7a1294931dd6701927304a0fb7","seq":57,"wave":"rulings-20260806-a"}

- {"allocations":{"T:acceptance-shard-eval":"[T-813]"},"authored":"2026-08-11","content_sha256":"33b41b060e4bd763b47582e4f8f414818e1efe62b0b7321349dcaf98939a65e7","seq":58,"wave":"rulings-20260806-a"}

- {"allocations":{"T:dw-g05-partial-land-direction":"[T-814]"},"authored":"2026-08-11","content_sha256":"fff7468637ec006f8fa60070ee43fa6ff37347993540d75cfa0c2dac9e839dc6","seq":1,"wave":"dev-wave-t8b-restart-residue"}
- {"allocations":{"D:toolchain-binding-and-unlock-are-inseparable":"D293"},"authored":"2026-08-11","content_sha256":"75d8fcb7520c3f6ea6538594b2a062648321fdaebe7252450347c81e92d03632","seq":2,"wave":"dev-wave-t8b-restart-residue"}
- {"allocations":{},"authored":"2026-08-11","content_sha256":"2c45ec232c70d8d9128ed44f2e5951a914da3fa555d89a47587bfb022fdb4587","seq":3,"wave":"dev-wave-t8b-restart-residue"}

- {"allocations":{"T:codex-hook-trust-and-surfaces":"[T-815]"},"authored":"2026-08-11","content_sha256":"aef5a6d3d75c9ea00022309d94ed225c0629cbd963f6d37f993e880a03fcd26b","seq":1,"wave":"dev-wave-codex-hook-parity"}
- {"allocations":{"F:codex-cannot-write-own-config-dir":"F218","F:codex-web-search-evidence":"F217"},"authored":"2026-08-11","content_sha256":"7383a5629385491e85f8ffaa7c788e968daa0838dce1409c6278d4f6117c6de4","seq":2,"wave":"dev-wave-codex-hook-parity"}
- {"allocations":{"D:codex-hook-wiring":"D294"},"authored":"2026-08-11","content_sha256":"d774c81d3b51bba6f9af3b8cc8380120c0baa042fdf8a78c69dff53919f54aee","seq":3,"wave":"dev-wave-codex-hook-parity"}

- {"allocations":{"T:coverage-driver-commit-witness":"[T-818]","T:legacy-commit-witness-backfill":"[T-817]","T:mutation-runner-drift-scope":"[T-819]","T:trace-v2-cpp-pin-approval":"[T-816]"},"authored":"2026-08-11","content_sha256":"e30f995f366ab92b2bedf98721c07b14c6bdb002c523e55194a06ebe41d352e5","seq":1,"wave":"dev-wave-t756-trace-v2"}
- {"allocations":{"D:trace-completeness-external-counter":"D295"},"authored":"2026-08-11","content_sha256":"79e0e707c9ad68a29c7c909cb565ba82ca4f14e1b2c1365e459aaec2d7f0b4b8","seq":2,"wave":"dev-wave-t756-trace-v2"}
- {"allocations":{},"authored":"2026-08-11","content_sha256":"3f38e164e1ee941a436381d7b5b2afda8937aa7281d3bbc2dd5fb7b90dd4a8fe","seq":3,"wave":"dev-wave-t756-trace-v2"}

- {"allocations":{},"authored":"2026-08-11","content_sha256":"ee206a3df76e7065c4f7644566926b3a1b5ce0c35226cfa148bcde7b22c83b75","seq":59,"wave":"rulings-20260806-a"}
- {"allocations":{},"authored":"2026-08-11","content_sha256":"1cd80e29a266aa38eff605e47246eacee5a402f1d8042f70cbea2345fc639f5b","seq":60,"wave":"rulings-20260806-a"}

- {"allocations":{"T:exec-module-systemexit":"[T-820]","T:fold-provenance-durable-artifact":"[T-821]"},"authored":"2026-08-11","content_sha256":"93819a427c1945eefad7fc32483206b6c9f65e19f67c5f6af817d4f7bfe97dce","seq":1,"wave":"dev-wave-t798-t799-fold-window"}

- {"allocations":{},"authored":"2026-08-11","content_sha256":"c87e779726dfdb561588c2d19fd64b533623e300e12d9ddc3b88056f15346635","seq":61,"wave":"rulings-20260806-a"}
- {"allocations":{},"authored":"2026-08-11","content_sha256":"123f0da1ff21e5068a27ee37d1926c135332f381287bb4f8000262b7fe643a19","seq":62,"wave":"rulings-20260806-a"}

- {"allocations":{"T:pegasus-job-env-pitfalls":"[T-823]","T:s8c-acceptance-layer3-gap":"[T-822]"},"authored":"2026-08-11","content_sha256":"7986c64599905e8b3c800631134395858e9de7b774056897f2e0952b5af5707f","seq":1,"wave":"dev-wave-t809-8c-fanout"}

- {"allocations":{"T:control-byte-scan-tool":"[T-825]","T:waiter-runtime-receipt":"[T-824]"},"authored":"2026-08-11","content_sha256":"3d5fca18b25bdfeee05b24b576f39877ac16d47ef8fb8cef69908d69024f9b03","seq":1,"wave":"dev-wave-t786-docs-budget"}
- {"allocations":{"F:reflow-breaks-line-anchored-pins":"F219"},"authored":"2026-08-11","content_sha256":"ee83bbdd6c61aafcdb3cf2785fcf37f2f92a28efb09eae8ed12167225bce3151","seq":2,"wave":"dev-wave-t786-docs-budget"}

- {"allocations":{},"authored":"2026-08-11","content_sha256":"414af363582fee40a92b69399a7267178859e8a5f735cd6ea9243cb1c0da8bb1","seq":63,"wave":"rulings-20260806-a"}

- {"allocations":{},"authored":"2026-08-11","content_sha256":"b5b69013f1eed280068c41821534a8a86683a8c78c02fd7984239fc369a0e68b","seq":64,"wave":"rulings-20260806-a"}

- {"allocations":{},"authored":"2026-08-11","content_sha256":"2963c3efa0a227159cb490d6dd0146202b97cfdd16970da0e2e880128ca16a3f","seq":1,"wave":"dev-wave-t813-shard-eval"}
- {"allocations":{},"authored":"2026-08-11","content_sha256":"45bc12a3a0d6df2ba1dffb70f84252b1663568c47f5d0596888bf278cb066586","seq":2,"wave":"dev-wave-t813-shard-eval"}

- {"allocations":{"T:acceptance-partition-invariance":"[T-826]","T:acceptance-slow-tests":"[T-827]"},"authored":"2026-08-11","content_sha256":"bb1633270592ba73e9b2d4cebeb8b3657c686c55564e97c81d4e8293a34b968e","seq":65,"wave":"rulings-20260806-a"}

- {"allocations":{},"authored":"2026-08-11","content_sha256":"5d581974f7f629a0a03ebbd7c0f2cfce0b8ba01199d9078bbb476472fc31a989","seq":66,"wave":"rulings-20260806-a"}

- {"allocations":{"T:cfab-hash-pin-detection-gap":"[T-829]","T:check-docs-fence-scanner-column":"[T-830]","T:upper-cancellation-record":"[T-828]"},"authored":"2026-08-11","content_sha256":"fccbb75f5264a075062422ca4306aab4ce62b9e899638178f06c3bba5f80d10d","seq":1,"wave":"dev-wave-t657-stage0-fold"}
- {"allocations":{},"authored":"2026-08-11","content_sha256":"913c11c384e8b7e6e270abdf63838c53f50fcf4294e7475a2df3663849047073","seq":2,"wave":"dev-wave-t657-stage0-fold"}

- {"allocations":{"T:living-docs-node-variance":"[T-832]","T:node-variance-impl":"[T-831]"},"authored":"2026-08-11","content_sha256":"82b2d4808cdd19011ee6020eb3c681bf81b3edf625d30b025438f9848eeef278","seq":1,"wave":"dev-wave-t810-node-variance"}
- {"allocations":{},"authored":"2026-08-11","content_sha256":"1e4961a9efd8c407d119a5eda8e4782b65bb8a18f24f02a6b15ee54e50fe3af8","seq":2,"wave":"dev-wave-t810-node-variance"}

- {"allocations":{"T:trace-stdout-same-run-nonce":"[T-833]","T:verifier-epoch-consumer-inventory":"[T-834]"},"authored":"2026-08-11","content_sha256":"792f16d045c58399826983f9a0e8ab0d745ce0993973e0da7ff25e6c7b143e19","seq":1,"wave":"dev-wave-t817-verifier-epoch"}

- {"allocations":{"T:acceptance-record-order-contract":"[T-836]","T:runbook-request-id-pre-submission":"[T-835]"},"authored":"2026-08-11","content_sha256":"52a3fcac30251da88bb83c2b7ffbfa15ce145fb705bd37e9bcd4d78729ba9fa7","seq":1,"wave":"dev-wave-t809-fanout-conditions"}

- {"allocations":{"T:trace-v2-commit-topology":"[T-837]","T:trace-v2-emitter-verifier-wiring":"[T-839]","T:trace-v2-step4-protocol-gate":"[T-838]"},"authored":"2026-08-11","content_sha256":"5a525b968b7e70e218d7f8f4cc40135df690593e9e12fe3551c6a96ee80c0174","seq":1,"wave":"dev-wave-t756-fn2-trace-v2"}
- {"allocations":{"D:trace-v2-in-editable-surface":"D296","D:trace0-preprocess-identity-gate":"D297"},"authored":"2026-08-11","content_sha256":"0d200faaa0ee8e505acb3b2b6c4610e9009e5f7b35e8d22b984675683d129344","seq":2,"wave":"dev-wave-t756-fn2-trace-v2"}
- {"allocations":{"F:mutation-digest-truncation-hides-expected-nodes":"F220","F:plan-child-asserts-absent-toolchain":"F221"},"authored":"2026-08-11","content_sha256":"f1e65a487615b66b4fd91cb3fb1833f8fcb21de1350fe7694bc54221cdb33834","seq":3,"wave":"dev-wave-t756-fn2-trace-v2"}

- {"allocations":{"T:backoff-value-truncation":"[T-843]","T:codex-roles-import-path":"[T-846]","T:dw-o01-artifact-root":"[T-845]","T:launcher-termination-flake":"[T-844]","T:t316-coder-derived-bypass":"[T-840]","T:t316-forbidden-identifiers-vacuous":"[T-842]","T:t316-gate-receipt-binding":"[T-841]"},"authored":"2026-08-11","content_sha256":"7ca3e99bcac4deb11f36c4cb6bb5c9a317a981416ec8129190403d7fb4cbe824","seq":1,"wave":"dev-wave-t316-semantic-gate-impl"}
- {"allocations":{"D:coder-hole-effect-gate":"D298"},"authored":"2026-08-11","content_sha256":"9158576e97999a58a820cc471d2cdd945684b5bc74b561f8003b796f496a58ba","seq":1,"wave":"dev-wave-t316-semantic-gate-impl"}

- {"allocations":{"T:lease-invocation-fencing":"[T-847]"},"authored":"2026-08-11","content_sha256":"356fa6945e58659d9256e87cfca875b9b3f1e667e07046d7274027b62a3e2a13","seq":1,"wave":"dev-wave-t812-lease-self-renew"}
- {"allocations":{"D:lease-self-renew-scope":"D299"},"authored":"2026-08-11","content_sha256":"a0c36ccda61dfc9bf4533fef5942af3f249be8b97135c7d34164421f54df0bd7","seq":2,"wave":"dev-wave-t812-lease-self-renew"}
- {"allocations":{"F:codex-observation-cap-kills-lens":"F222"},"authored":"2026-08-11","content_sha256":"a99440b888f83091d86242da5789c4ea185d793d45bd53ab9176884bfa1e34f2","seq":3,"wave":"dev-wave-t812-lease-self-renew"}

- {"allocations":{"T:fanout-exact-n-run":"[T-851]","T:fanout-tamper-evidence":"[T-849]","T:fanout-uncovered-gates":"[T-850]","T:legacy-mutation-reservation":"[T-852]","T:mutation-timeout-semantics":"[T-848]"},"authored":"2026-08-11","content_sha256":"cd27f34c01b4c1fd3c1b8c2589f0872dbb06df29c9d2b813043afe66a212caf5","seq":1,"wave":"dev-wave-t808-mutation-fanout"}
- {"allocations":{"D:mutation-fanout-contract":"D300"},"authored":"2026-08-11","content_sha256":"3f22b793ac1a96ebbf6d902409b6fcaf1b37e0e825700a62fe8ba72ead2fc068","seq":1,"wave":"dev-wave-t808-mutation-fanout"}

- {"allocations":{"T:dw-s04-docs-only-carveout":"[T-854]","T:dw-s04-scope-of-impl-diff":"[T-853]","T:normalize-non-nfc-test-literals":"[T-855]"},"authored":"2026-08-11","content_sha256":"2beaee1b2bb4cd2ad95cce3f879603619195430b663402d6d298da636d011325","seq":1,"wave":"dev-wave-t765-exemption-wording"}
- {"allocations":{"D:dw-s04-conjunction":"D301"},"authored":"2026-08-11","content_sha256":"4405f6195f259b0b23625a903b84fa2f66a4c85ccd1475945567bd9e0d32a111","seq":2,"wave":"dev-wave-t765-exemption-wording"}
- {"allocations":{"F:non-nfc-line-invalidates-codex-run":"F223"},"authored":"2026-08-11","content_sha256":"a5a0ada3c70e918e8304291eafd950b95d2555aa1cbdef26321c9f51e48b749c","seq":3,"wave":"dev-wave-t765-exemption-wording"}

- {"allocations":{"T:legacy-observations-retirement":"[T-857]","T:official-sink-audit":"[T-858]","T:oracle-verdict-sealing":"[T-856]"},"authored":"2026-08-11","content_sha256":"d76dc0000bba21639f1657de49d8a3de18bd6c92d64249c951cd3469b837d845","seq":1,"wave":"dev-wave-t804-spec-sha256"}
- {"allocations":{"D:judge-reverifies-not-compares-pin":"D304","D:mutation-expected-nodes-from-collection":"D303","D:spec-binding-by-rederivation":"D302"},"authored":"2026-08-11","content_sha256":"09064ff67cebc90d8d9060eca7a6abb21503c067178aff31659984e58e2f6e3f","seq":2,"wave":"dev-wave-t804-spec-sha256"}
- {"allocations":{"F:codex-cannot-perform-merge":"F225","F:mutation-node-id-nonascii":"F224","F:source-hash-pin-drags-mutations":"F226"},"authored":"2026-08-11","content_sha256":"c1b6eeedba5261bec9b1c65ca69af4f6bb6d699219d3fc0abd2544833db0b5ba","seq":3,"wave":"dev-wave-t804-spec-sha256"}

- {"allocations":{"T:guided-wal-status":"[T-860]","T:legacy-campaign-admission":"[T-861]","T:trace-run-binding-nonce":"[T-859]"},"authored":"2026-08-12","content_sha256":"09c418ea7494001689080b281ffd8dda70f779c4a5bf673ca5b2692f9e6c1b04","seq":67,"wave":"rulings-20260806-a"}

- {"allocations":{},"authored":"2026-08-12","content_sha256":"3aa920a826f01eae565de32ec2fea6ceae44259e202391d0fa7f4d2dc63d2926","seq":68,"wave":"rulings-20260806-a"}

- {"allocations":{"T:approval-decision-machine-schema":"[T-864]","T:pubcore-s81-root-erratum":"[T-863]","T:publication-reservation-writer":"[T-862]","T:spool-fold-real-fixture-closure":"[T-865]"},"authored":"2026-08-11","content_sha256":"48fbcee3be71e60b6d74af53dd078f314e331ab25c6e81e49bcf109a30a94286","seq":1,"wave":"dev-wave-t793-pubcore-impl"}
- {"allocations":{"D:marker-gate-scope":"D306","D:publication-trust-root":"D305"},"authored":"2026-08-11","content_sha256":"c4197ce0df367252d7da90299b0c92a611553de4a4923d9eca3fc60b7bcf2805","seq":1,"wave":"dev-wave-t793-pubcore-impl"}
- {"allocations":{"F:test-assumes-empty-spool":"F228","F:tools-to-orchestrator-gate-import":"F227"},"authored":"2026-08-11","content_sha256":"b78f5294bdf81f6e6d9a28244b0e0869fcdceaab4b45220ca3fd9a5a38de39d2","seq":1,"wave":"dev-wave-t793-pubcore-impl"}

- {"allocations":{"T:run-tests-overall-grace":"[T-870]","T:t793-d305-supersession-expectation":"[T-869]","T:t810-approval-trust-root":"[T-868]","T:t810-coordinator-and-wrapper":"[T-866]","T:t810-guard-and-budget":"[T-867]"},"authored":"2026-08-12","content_sha256":"f270e0fc8af5b82c5f5b237c76bb3d2364d3c848ccaaad27b7b075bcfe379be3","seq":1,"wave":"dev-wave-t810-harness"}

- {"allocations":{"T:codex-launch-argv-preflight":"[T-875]","T:floor-artifact-toolchain-report-schema":"[T-872]","T:floor-attempt-toolchain-provenance":"[T-871]","T:toolchain-authority-completeness":"[T-873]","T:toolchain-binding-other-producers":"[T-874]"},"authored":"2026-08-11","content_sha256":"4b19f89610b4a3bc963790fe429da265abb0128a93c8202dc5b698dd28343726","seq":1,"wave":"dev-wave-t783-toolchain-binding"}
- {"allocations":{"D:site-resolution-and-binding-land-together":"D308","D:toolchain-binding-scope-narrowed":"D307"},"authored":"2026-08-11","content_sha256":"df1831511f662dc4a68acca9f1e9beaf5dc7c77818c2b75fc4b12475d0ea2dcd","seq":2,"wave":"dev-wave-t783-toolchain-binding"}
- {"allocations":{"F:redundant-gate-masks-authority-mutation":"F229"},"authored":"2026-08-11","content_sha256":"0edc71cea511f24794520a72d4da5b7e4172c4ccabab4ed9c73f3c7916776529","seq":3,"wave":"dev-wave-t783-toolchain-binding"}

- {"allocations":{"T:dw-artifact-root-subdir-precreate":"[T-877]","T:mutation-node-xdist-group-suffix":"[T-876]","T:test-s8b-approved-tests-import":"[T-878]"},"authored":"2026-08-12","content_sha256":"ffa04a93d973c0900608764226e1425fea16a77e1abfd26477515c02c714f346","seq":1,"wave":"dev-wave-t717-t485-t792"}
- {"allocations":{"D:evidence-content-addressed-resolver":"D310","D:walltime-sixty-minutes":"D309"},"authored":"2026-08-12","content_sha256":"e63316ff6ce67c80fd8adb5e4323726673c72544d1ba98b9b34771c7f7cddf75","seq":2,"wave":"dev-wave-t717-t485-t792"}

- {"allocations":{"T:verifier-negative-txid-false-green":"[T-879]"},"authored":"2026-08-12","content_sha256":"7c0f470313474beb00edede9ed935527e719a4512d61ecb3ed18d41233e77d3e","seq":1,"wave":"dev-wave-t816-step4"}

- {"allocations":{"T:focal-red-invisible-to-acceptance":"[T-881]","T:load-rotate-limit-import-provenance":"[T-880]"},"authored":"2026-08-12","content_sha256":"6ce1e313fd8a2a9eac93fd4ab4cb98947193544bb9af59ad3f97319037585f28","seq":1,"wave":"dev-wave-t860-test-red"}

- {"allocations":{"D:keep-gains-below-target":"D312","D:no-history-proportional-test-cost":"D311","D:optin-needs-dispatch-env-allowlist":"D314","D:t080-history-scan-batched":"D313"},"authored":"2026-08-12","content_sha256":"2756b2d21bc9b5862d3f195d8eeeb13860b0e78662db2ccfad1de2766eae98f1","seq":1,"wave":"dev-wave-t827-slow-tests"}
- {"allocations":{"T:codex-sessions-history-scan":"[T-884]","T:decompose-batch-vs-optin":"[T-882]","T:preserve-git-clone-isolation-cost":"[T-885]","T:record-hostname-with-perf":"[T-883]"},"authored":"2026-08-12","content_sha256":"24f46555a9a878b0ec4c6bb4d829dbd122d7c73bf4733189ee443723b4c706d7","seq":2,"wave":"dev-wave-t827-slow-tests"}

- {"allocations":{"T:main-red-t793-d305-supersession-pin":"[T-888]","T:rollout-lookup-remove-history-proportionality":"[T-886]","T:t201-d-xdist-group-reassessment":"[T-887]"},"authored":"2026-08-12","content_sha256":"c705715a424535ac0ff7053614089d3b03e500b0d880e0a69bc69f38928f1228","seq":1,"wave":"dev-wave-module-fixture-cost"}
- {"allocations":{"D:session-meta-candidate-scan":"D315","D:supersession-pin-derivation":"D316"},"authored":"2026-08-12","content_sha256":"511d6f451d17f16769fee6354dbb31882b92f0f8921f8b1eb7b25aef2aeeb033","seq":2,"wave":"dev-wave-module-fixture-cost"}
- {"allocations":{"F:expected-nodes-stale-after-fix":"F230"},"authored":"2026-08-12","content_sha256":"87abe876f610deab339450aa3394c67b7a38cd9c644a76ac46b7dea3876f6c06","seq":3,"wave":"dev-wave-module-fixture-cost"}

- {"allocations":{"T:fold-commit-transaction-binding":"[T-891]","T:fold-subset-shape-flake":"[T-892]","T:fold-terminal-idempotence":"[T-889]","T:standalone-fold-serialization":"[T-890]"},"authored":"2026-08-11","base":"a2e78921aaa88e180686107a3464bfac0f5d7e3f","content_sha256":"dd231e327e31bcc78825de70e2edb4c8892c79c1e617315203486838d4f2c9e1","seq":1,"tested_tip":"84fc6bf49e03ba08fc5a3cf9818220485139a29e","wave":"dev-wave-t798-t799-finalize","wave_ref":"refs/heads/worktree-dev-wave-t798-t799-finalize"}
- {"allocations":{"D:bind-the-plan-input-closure-not-just-the-head":"D319","D:fold-commit-identity-is-the-authority":"D317","D:receipt-schema-positional-cutover":"D318"},"authored":"2026-08-11","base":"a2e78921aaa88e180686107a3464bfac0f5d7e3f","content_sha256":"7d83ac79f543f9d9986bfeffeb416bf5020d101fa927245683034f2358069310","seq":2,"tested_tip":"84fc6bf49e03ba08fc5a3cf9818220485139a29e","wave":"dev-wave-t798-t799-finalize","wave_ref":"refs/heads/worktree-dev-wave-t798-t799-finalize"}

- {"allocations":{"T:floor-campaign-clone-cost":"[T-893]"},"authored":"2026-08-12","base":"ccb2379e120419b790df3994e1c8f878036b1fb6","content_sha256":"a58846d4536e9ab53715f62bd500eb4f05c118c6810f16c37bb51dfaeb62805e","seq":1,"tested_tip":"e1a1b5f0f8526a25094a90e5f3cc5fff6ad55064","wave":"dev-wave-floor-campaign-speed","wave_ref":"refs/heads/worktree-dev-wave-floor-campaign-speed"}
- {"allocations":{},"authored":"2026-08-12","base":"ccb2379e120419b790df3994e1c8f878036b1fb6","content_sha256":"cc3f8514483e216bade24961898dc088a5c8f9082a66c7950b0f69a8e02b8861","seq":2,"tested_tip":"e1a1b5f0f8526a25094a90e5f3cc5fff6ad55064","wave":"dev-wave-floor-campaign-speed","wave_ref":"refs/heads/worktree-dev-wave-floor-campaign-speed"}

- {"allocations":{"F:land-phase-probe-cannot-use-hooks":"F232","F:waiter-merge-conflict-hides-paths":"F231"},"authored":"2026-08-12","base":"4ef913f66f37eddbb2bec40b187907950070ed39","content_sha256":"56a7b2da93754018ae047c247fc86f18d07cc40eb27e45e66d8ae55d8f9130cb","seq":3,"tested_tip":"36db928a9b948e6f0d4eb8949ee67224f346f5ed","wave":"dev-wave-t798-t799-finalize","wave_ref":"refs/heads/worktree-dev-wave-t798-t799-finalize"}
- {"allocations":{"T:waiter-conflict-diagnostics":"[T-894]"},"authored":"2026-08-12","base":"4ef913f66f37eddbb2bec40b187907950070ed39","content_sha256":"1b27788806f44eab4fe524ed9c09d481e0aff429b1b7f04047f3a6d077038798","seq":4,"tested_tip":"36db928a9b948e6f0d4eb8949ee67224f346f5ed","wave":"dev-wave-t798-t799-finalize","wave_ref":"refs/heads/worktree-dev-wave-t798-t799-finalize"}

- {"allocations":{"T:duplicate-sink-residency":"[T-896]","T:terminal-item-retirement-check":"[T-895]"},"authored":"2026-08-12","base":"a70a5acd432e824fe688a88ef5df448c7def221d","content_sha256":"969506c12f475a17ff085eb81e2db3484ea309e05171976b17b974960391e55b","seq":1,"tested_tip":"eb04dc368823ff004400b470e3e7b8d13c5497e7","wave":"dev-wave-t499-triage","wave_ref":"refs/heads/worktree-dev-wave-t499-triage"}
- {"allocations":{"F:fold-two-fragments-same-task":"F233"},"authored":"2026-08-12","base":"a70a5acd432e824fe688a88ef5df448c7def221d","content_sha256":"102f30e9e1e88cd3b5ae02265ec31c92cdb91d32a021a1d260bd2bf0f923ce94","seq":2,"tested_tip":"eb04dc368823ff004400b470e3e7b8d13c5497e7","wave":"dev-wave-t499-triage","wave_ref":"refs/heads/worktree-dev-wave-t499-triage"}
- {"allocations":{},"authored":"2026-08-12","base":"a70a5acd432e824fe688a88ef5df448c7def221d","content_sha256":"9d765127466b12b1eca4d0dc543774d7bf625771c4f40df3a885363b7a4a7080","seq":1,"tested_tip":"eb04dc368823ff004400b470e3e7b8d13c5497e7","wave":"rulings-20260812-coarse-provenance","wave_ref":"refs/heads/worktree-dev-wave-t499-triage"}
- {"allocations":{"D:coarse-provenance-standard":"D320"},"authored":"2026-08-12","base":"a70a5acd432e824fe688a88ef5df448c7def221d","content_sha256":"bb2b9117023bb0bff1d195ac33afd19064b70b6be82738a44954ed2046ea62d5","seq":2,"tested_tip":"eb04dc368823ff004400b470e3e7b8d13c5497e7","wave":"rulings-20260812-coarse-provenance","wave_ref":"refs/heads/worktree-dev-wave-t499-triage"}

- {"allocations":{"T:trigger-admission-binding-optional":"[T-897]"},"authored":"2026-08-12","base":"0a6ded47ff4a0c954714ba4d8271b8410ff9a092","content_sha256":"913f01b1b6131e0c88c175ff45bf96e6dc4bb286ef124c485076ebf42ef43b3a","seq":1,"tested_tip":"3193cd09baefd2f91bedf097e9f07803fd4e4eb0","wave":"dev-wave-t513-trigger-exact","wave_ref":"refs/heads/worktree-dev-wave-t513-trigger-exact"}
- {"allocations":{"D:trigger-admission-exact-bytes":"D321"},"authored":"2026-08-12","base":"0a6ded47ff4a0c954714ba4d8271b8410ff9a092","content_sha256":"0cb23060875bbe53b871e72c3270562fc72fd3764123e0ac1ccbb308888e898c","seq":2,"tested_tip":"3193cd09baefd2f91bedf097e9f07803fd4e4eb0","wave":"dev-wave-t513-trigger-exact","wave_ref":"refs/heads/worktree-dev-wave-t513-trigger-exact"}

- {"allocations":{},"authored":"2026-08-11","base":"49cf6a5ff0add79d1a66ee4044a42fdfa332d51c","content_sha256":"fd9caaacafe6ac89e8504ae5525889003b3eb3d13841ccf526d99a2db942d769","seq":1,"tested_tip":"ec3e94701d256de598adfed91c757d8806472b08","wave":"dev-wave-t139-manifest-land2","wave_ref":"refs/heads/worktree-dev-wave-t139-manifest-w2"}
- {"allocations":{"F:mutation-preregistration-before-implementation":"F234","F:split-leaves-isomorphic-defect":"F235"},"authored":"2026-08-11","base":"49cf6a5ff0add79d1a66ee4044a42fdfa332d51c","content_sha256":"925850e10d254cdd54d1d1dc515761f0ab854adee4699d3529b9d4178418c3c2","seq":2,"tested_tip":"ec3e94701d256de598adfed91c757d8806472b08","wave":"dev-wave-t139-manifest-land2","wave_ref":"refs/heads/worktree-dev-wave-t139-manifest-w2"}
- {"allocations":{},"authored":"2026-08-11","base":"49cf6a5ff0add79d1a66ee4044a42fdfa332d51c","content_sha256":"5fbb3f5253694de199a487a2d0fe689b8663c9ea8eb2f02ef42c07cd00174852","seq":1,"tested_tip":"ec3e94701d256de598adfed91c757d8806472b08","wave":"dev-wave-t139-manifest-land2-s2","wave_ref":"refs/heads/worktree-dev-wave-t139-manifest-w2"}
- {"allocations":{},"authored":"2026-08-11","base":"49cf6a5ff0add79d1a66ee4044a42fdfa332d51c","content_sha256":"2071fe34ca96b39a368527d022bc75f95d04050402a4f7f9b95bba04e2c526ef","seq":1,"tested_tip":"ec3e94701d256de598adfed91c757d8806472b08","wave":"dev-wave-t139-manifest-land2-s2","wave_ref":"refs/heads/worktree-dev-wave-t139-manifest-w2"}
- {"allocations":{},"authored":"2026-08-12","base":"49cf6a5ff0add79d1a66ee4044a42fdfa332d51c","content_sha256":"19126445b69e0731a81989ef013f27723b5ca51258818adfe5ddb5707fb83765","seq":1,"tested_tip":"ec3e94701d256de598adfed91c757d8806472b08","wave":"dev-wave-t139-manifest-land2-s3","wave_ref":"refs/heads/worktree-dev-wave-t139-manifest-w2"}
- {"allocations":{"F:pending-rulings-invisible-on-unlanded-branch":"F236"},"authored":"2026-08-12","base":"49cf6a5ff0add79d1a66ee4044a42fdfa332d51c","content_sha256":"cba9ce3fdac2793b726fdf49a506ad0c47b3073184f0b50ff97e7a459497879d","seq":1,"tested_tip":"ec3e94701d256de598adfed91c757d8806472b08","wave":"dev-wave-t139-manifest-land2-s3","wave_ref":"refs/heads/worktree-dev-wave-t139-manifest-w2"}
- {"allocations":{},"authored":"2026-08-12","base":"49cf6a5ff0add79d1a66ee4044a42fdfa332d51c","content_sha256":"9dc915c495eb0dd6e5ce294297cb70ecf09424c5eb93cf66fbd7c3e11b40872d","seq":1,"tested_tip":"ec3e94701d256de598adfed91c757d8806472b08","wave":"dev-wave-t139-manifest-land2-s4","wave_ref":"refs/heads/worktree-dev-wave-t139-manifest-w2"}
- {"allocations":{"F:approval-scope-splits-within-one-field":"F237","F:brief-cites-own-measured-absence-as-authority":"F238"},"authored":"2026-08-12","base":"49cf6a5ff0add79d1a66ee4044a42fdfa332d51c","content_sha256":"19b071222816755c97e25b5f2b46aadbd57a786710243c73cfccf53bc258f166","seq":1,"tested_tip":"ec3e94701d256de598adfed91c757d8806472b08","wave":"dev-wave-t139-manifest-land2-s4","wave_ref":"refs/heads/worktree-dev-wave-t139-manifest-w2"}
- {"allocations":{},"authored":"2026-08-10","base":"49cf6a5ff0add79d1a66ee4044a42fdfa332d51c","content_sha256":"4c6dd6bd72f3f248c28b53f05b3bde3c1ee0bc214746977cabdab4257ab32bb1","seq":1,"tested_tip":"ec3e94701d256de598adfed91c757d8806472b08","wave":"dev-wave-t139-manifest-w1","wave_ref":"refs/heads/worktree-dev-wave-t139-manifest-w2"}
- {"allocations":{"D:erratum-registry-membership-is-not-approval":"D322"},"authored":"2026-08-10","base":"49cf6a5ff0add79d1a66ee4044a42fdfa332d51c","content_sha256":"a6d1af7cad5fd2de6e3cecf454c82e1e66842f931c8545b7493614be1f0adef8","seq":1,"tested_tip":"ec3e94701d256de598adfed91c757d8806472b08","wave":"dev-wave-t139-manifest-w1","wave_ref":"refs/heads/worktree-dev-wave-t139-manifest-w2"}

- {"allocations":{"T:cmake-realpath-binding":"[T-900]","T:floor-run-resume-rescue":"[T-901]","T:floor-wrapper-writer-failure-rc":"[T-898]","T:pilot-api-seam-evidence-profile":"[T-899]"},"authored":"2026-08-12","base":"e447b87b9a10f4195f694cce768284ccc5bc6fbc","content_sha256":"626123c3055a264daa9098ade5ebc482121e428c24e5a5450c272741764640c0","seq":1,"tested_tip":"9e5bce895084dafa2fa44a3116ebb97bd8dc7505","wave":"dev-wave-t748-pilot-path","wave_ref":"refs/heads/worktree-dev-wave-t748-pilot-path"}
- {"allocations":{"D:floor-wrapper-fixed-pilot":"D323","D:shell-guard-token-counting":"D324"},"authored":"2026-08-12","base":"e447b87b9a10f4195f694cce768284ccc5bc6fbc","content_sha256":"08c5579e5e9036f76dcacd88bd9d93bbcf61bb7685e1c34ce51e24f58240bace","seq":2,"tested_tip":"9e5bce895084dafa2fa44a3116ebb97bd8dc7505","wave":"dev-wave-t748-pilot-path","wave_ref":"refs/heads/worktree-dev-wave-t748-pilot-path"}
- {"allocations":{},"authored":"2026-08-12","base":"e447b87b9a10f4195f694cce768284ccc5bc6fbc","content_sha256":"989d6aaad457cde5d7e524daca9fc0443da250c91793e1713928cd4034de8911","seq":3,"tested_tip":"9e5bce895084dafa2fa44a3116ebb97bd8dc7505","wave":"dev-wave-t748-pilot-path","wave_ref":"refs/heads/worktree-dev-wave-t748-pilot-path"}
- {"allocations":{},"authored":"2026-08-12","base":"e447b87b9a10f4195f694cce768284ccc5bc6fbc","content_sha256":"6580d3b2207106147f9262e4775e0df0481f8b4fe44dc30d039382739249d0b6","seq":4,"tested_tip":"9e5bce895084dafa2fa44a3116ebb97bd8dc7505","wave":"dev-wave-t748-pilot-path","wave_ref":"refs/heads/worktree-dev-wave-t748-pilot-path"}

- {"allocations":{},"authored":"2026-08-12","base":"778979ad044817e1d23b9862389133a84e0cd087","content_sha256":"296cd6d6dd2e6d9f84ff7455b6df818eff4eba0db4f80cff5d6d277e489e39c5","seq":1,"tested_tip":"9524ba4faca696a2e461e0586379220a63a8e36e","wave":"dev-wave-t881-focused-run","wave_ref":"refs/heads/worktree-dev-wave-t881-focused-run"}
- {"allocations":{"D:focal-run-rides-along":"D325"},"authored":"2026-08-12","base":"778979ad044817e1d23b9862389133a84e0cd087","content_sha256":"589f77578430d488c286db1d023397c047f39f9a9047895f6c6bbe7525d4f0ba","seq":2,"tested_tip":"9524ba4faca696a2e461e0586379220a63a8e36e","wave":"dev-wave-t881-focused-run","wave_ref":"refs/heads/worktree-dev-wave-t881-focused-run"}

- {"allocations":{"T:acceptance-set-strengthening-candidates":"[T-903]","T:hash-object-leading-dash":"[T-904]","T:holdout-live-scan-cost":"[T-902]"},"authored":"2026-08-12","base":"6402d8e188cd5d239728f30d964e0c7348bfdf59","content_sha256":"92a687b77582e38e04149cfabdd8a2de136d327dd7dfc389ded509e1bdbb6b16","seq":1,"tested_tip":"dd79ddad1f2452a472d8bdffacf12ef89708f4ce","wave":"dev-wave-acceptance-bottleneck","wave_ref":"refs/heads/worktree-dev-wave-acceptance-bottleneck"}
- {"allocations":{"F:fix-stage-role-name-collision":"F239"},"authored":"2026-08-12","base":"6402d8e188cd5d239728f30d964e0c7348bfdf59","content_sha256":"55361786298fe52f038232f0caa1ca5f05dc0aff94bba5b7bee4b449b4e740c8","seq":2,"tested_tip":"dd79ddad1f2452a472d8bdffacf12ef89708f4ce","wave":"dev-wave-acceptance-bottleneck","wave_ref":"refs/heads/worktree-dev-wave-acceptance-bottleneck"}

- {"allocations":{},"authored":"2026-08-12","base":"bebf43234a5d44e7fcc616ed8c60137c826265db","content_sha256":"98fa590b8e3f78527d395453564aa8891fb45591c0d9be89fb7a8999a4419d1a","seq":1,"tested_tip":"8397bbc0593bc6b70143348e4b18be4539ae819e","wave":"dev-wave-t184-stage-measurements","wave_ref":"refs/heads/worktree-dev-wave-t184-stage-measurements"}

- {"allocations":{"T:codex-guard-bytes-pin":"[T-905]","T:codex-launch-paths-uncovered":"[T-906]"},"authored":"2026-08-12","base":"9c09254426e48a5304773a5704f239465f0d5aa2","content_sha256":"9a34ce691f4225a40767b1d529134e5d260b81aed673f8b315a1f5ae3ced6bb5","seq":1,"tested_tip":"d143cfcce081e2ef54910dbf7e2396d676d78bea","wave":"dev-wave-t-codex-hook-trust","wave_ref":"refs/heads/worktree-dev-wave-t-codex-hook-trust"}
- {"allocations":{"D:codex-hook-refusal-evidence":"D327","D:codex-hook-trust-bypass":"D326"},"authored":"2026-08-12","base":"9c09254426e48a5304773a5704f239465f0d5aa2","content_sha256":"8157f3e82d297a9a371258403962d2dd57755d0f9604ca1873cbe09b195b426f","seq":2,"tested_tip":"d143cfcce081e2ef54910dbf7e2396d676d78bea","wave":"dev-wave-t-codex-hook-trust","wave_ref":"refs/heads/worktree-dev-wave-t-codex-hook-trust"}
- {"allocations":{},"authored":"2026-08-12","base":"9c09254426e48a5304773a5704f239465f0d5aa2","content_sha256":"db52effcbb989df4604c6529c9a21f99ac33fb32a25a78a59edbba1728395dfa","seq":3,"tested_tip":"d143cfcce081e2ef54910dbf7e2396d676d78bea","wave":"dev-wave-t-codex-hook-trust","wave_ref":"refs/heads/worktree-dev-wave-t-codex-hook-trust"}

- {"allocations":{"T:acceptance-path-bypasses-waiter":"[T-908]","T:acceptance-run-window-coverage":"[T-907]","T:cleanup-signal-window":"[T-909]","T:dev-wave-docs-budget-blocked-notes":"[T-911]","T:mutation-subset-match-frame":"[T-912]","T:untracked-acceptance-policy":"[T-910]"},"authored":"2026-08-12","base":"7b6f91a8884ee93dfc36698364a05f62fb4fc80d","content_sha256":"eb42b552005ab5c71902c27d9e55897ca390dcda535751442157cac0d0409af1","seq":1,"tested_tip":"4872c26c9727620d8f2fb09009de9a1e2df88206","wave":"dev-wave-t725-t694-lease-clean","wave_ref":"refs/heads/worktree-dev-wave-t725-t694-lease-clean"}
- {"allocations":{},"authored":"2026-08-12","base":"7b6f91a8884ee93dfc36698364a05f62fb4fc80d","content_sha256":"af404c223b060d9cc5d1907bb865c8a1ec13bf5d037066926bbac6ed4e4340e4","seq":2,"tested_tip":"4872c26c9727620d8f2fb09009de9a1e2df88206","wave":"dev-wave-t725-t694-lease-clean","wave_ref":"refs/heads/worktree-dev-wave-t725-t694-lease-clean"}

- {"allocations":{"T:brief-anchor-table-single-source":"[T-916]","T:hold-manifest-integration":"[T-914]","T:holdout-scan-optimize-not-hold":"[T-915]","T:publication-ledger-r2-hold-entries":"[T-913]"},"authored":"2026-08-12","base":"1e0fd1b633136ffba4da51bc19b4f332827b3ac5","content_sha256":"5b39b60cd369fc6223138fd2d9377316352d826247e8425056b601bc08def650","seq":1,"tested_tip":"68c83c2d95e4e79e4031ff68c76dca7e3f1ffc9f","wave":"dev-wave-freeze-chain-hold","wave_ref":"refs/heads/worktree-dev-wave-freeze-chain-hold"}
- {"allocations":{"F:hold-target-colocated-with-correctness-gate":"F240"},"authored":"2026-08-12","base":"1e0fd1b633136ffba4da51bc19b4f332827b3ac5","content_sha256":"0961fd15fed4afaa2aaa3c7a71b6020f2da1e59189e985a6f871d5f9e70846b9","seq":2,"tested_tip":"68c83c2d95e4e79e4031ff68c76dca7e3f1ffc9f","wave":"dev-wave-freeze-chain-hold","wave_ref":"refs/heads/worktree-dev-wave-freeze-chain-hold"}
- {"allocations":{"T:freeze-chain-hold":"[T-917]","T:mutation-volatile-tree-rule":"[T-918]","T:solo-speedup-no-extrapolation":"[T-919]"},"authored":"2026-08-12","base":"1e0fd1b633136ffba4da51bc19b4f332827b3ac5","content_sha256":"a1e873dfce3ec46234e0863e80f35349143e0cf066e746b0817642dcd5a21799","seq":1,"tested_tip":"68c83c2d95e4e79e4031ff68c76dca7e3f1ffc9f","wave":"rulings4-20260812","wave_ref":"refs/heads/worktree-dev-wave-freeze-chain-hold"}
- {"allocations":{"D:freeze-verification-hold":"D328"},"authored":"2026-08-12","base":"1e0fd1b633136ffba4da51bc19b4f332827b3ac5","content_sha256":"c432d431e1b809352fce174fbbeda8ecf7a550fad5a4c580c1795d589f966a34","seq":2,"tested_tip":"68c83c2d95e4e79e4031ff68c76dca7e3f1ffc9f","wave":"rulings4-20260812","wave_ref":"refs/heads/worktree-dev-wave-freeze-chain-hold"}

- {"allocations":{"T:floor-preflight-perf-check":"[T-921]","T:pegasus-compute-perf-restore":"[T-920]"},"authored":"2026-08-12","base":"f45c79b1f55f0379cb5f5fa2fe06902a08005348","content_sha256":"cab75aff6071ab4428cd20c0d806958c01c3f74c70d2b94a894e5bb75a210d9f","seq":5,"tested_tip":"7e587c8273307d183cb6bf6a9e448a405f67a64c","wave":"dev-wave-t748-pilot-path","wave_ref":"refs/heads/worktree-dev-wave-t748-pilot-path"}
- {"allocations":{"D:attestation-tool-name-is-provenance":"D329","D:site-resolved-compiler-is-required-argument":"D330"},"authored":"2026-08-12","base":"f45c79b1f55f0379cb5f5fa2fe06902a08005348","content_sha256":"c2fff270658bfb3b13d738a84831939ede415b2a321cc94514a691b494a060a8","seq":6,"tested_tip":"7e587c8273307d183cb6bf6a9e448a405f67a64c","wave":"dev-wave-t748-pilot-path","wave_ref":"refs/heads/worktree-dev-wave-t748-pilot-path"}
- {"allocations":{"F:pegasus-compute-perf-missing":"F241"},"authored":"2026-08-12","base":"f45c79b1f55f0379cb5f5fa2fe06902a08005348","content_sha256":"185dad2a535058c44f345458daa60a381a2b7fae7b16bc517b046740db2e5520","seq":7,"tested_tip":"7e587c8273307d183cb6bf6a9e448a405f67a64c","wave":"dev-wave-t748-pilot-path","wave_ref":"refs/heads/worktree-dev-wave-t748-pilot-path"}
- {"allocations":{},"authored":"2026-08-12","base":"f45c79b1f55f0379cb5f5fa2fe06902a08005348","content_sha256":"475c8004d0d5f7e2b02e3f3cc27340a59d8a270c1d29f8e9db0a1854d03f428e","seq":8,"tested_tip":"7e587c8273307d183cb6bf6a9e448a405f67a64c","wave":"dev-wave-t748-pilot-path","wave_ref":"refs/heads/worktree-dev-wave-t748-pilot-path"}

- {"allocations":{"T:dev-wave-l15-budget-blocks-self-improvement":"[T-925]","T:t810-e2e-wiring":"[T-922]","T:t810-m6-attribution":"[T-924]","T:t810-m7-overdetection":"[T-926]","T:t810-ratify-admission-values":"[T-923]"},"authored":"2026-08-12","base":"aab330bb3c28048a6b8f489b88a85f6ce02b3830","content_sha256":"830b864156d867479543bee09b2cbed3735a765fcbb9e4fbdd9f6b68bba33c39","seq":2,"tested_tip":"b979c3b2244275a39e62e85d2d1f53d5f3c8de9d","wave":"dev-wave-t810-harness","wave_ref":"refs/heads/worktree-dev-wave-t810-harness"}
- {"allocations":{"D:t810-launch-authorization-witness":"D331"},"authored":"2026-08-12","base":"aab330bb3c28048a6b8f489b88a85f6ce02b3830","content_sha256":"f37cca011e0bb0b93a5a101e4c550f1bc7c6aa677e172e0891557e292a759927","seq":3,"tested_tip":"b979c3b2244275a39e62e85d2d1f53d5f3c8de9d","wave":"dev-wave-t810-harness","wave_ref":"refs/heads/worktree-dev-wave-t810-harness"}
- {"allocations":{"F:child-cannot-run-tests-defect-survives-review":"F242","F:m7-frozen-table-shared-coverage":"F243"},"authored":"2026-08-12","base":"aab330bb3c28048a6b8f489b88a85f6ce02b3830","content_sha256":"6c0941aabeb895d4330f1b4572ac2fb093a2d9622361ad7048614bee9ccfb7de","seq":4,"tested_tip":"b979c3b2244275a39e62e85d2d1f53d5f3c8de9d","wave":"dev-wave-t810-harness","wave_ref":"refs/heads/worktree-dev-wave-t810-harness"}

- {"allocations":{"T:mutation-waiter-early-return":"[T-927]"},"authored":"2026-08-12","base":"4928e1a3f7a5bf605866f455872fe77b2c74884c","content_sha256":"c660cba719a484a5daa0c919b110ee3167d8e60ccc8d8d6664de7f6c97dbf268","seq":1,"tested_tip":"4520e05e15e3aeedf785f59dd3d027ac7af0819c","wave":"dev-wave-t316-copyout-t840","wave_ref":"refs/heads/worktree-dev-wave-t316-copyout-t840"}
- {"allocations":{"D:build-output-copyout-contract":"D332","D:coder-issuer-machine-closure":"D333","D:redundant-gate-not-counted-as-evidence":"D334"},"authored":"2026-08-12","base":"4928e1a3f7a5bf605866f455872fe77b2c74884c","content_sha256":"827f11b45a75f772df5b421be3aca29a48f5b26d68c1125d19cbf186c044c419","seq":1,"tested_tip":"4520e05e15e3aeedf785f59dd3d027ac7af0819c","wave":"dev-wave-t316-copyout-t840","wave_ref":"refs/heads/worktree-dev-wave-t316-copyout-t840"}
- {"allocations":{"F:equivalent-mutation-recorded-as-unkillable":"F245","F:flaky-anchor-contaminates-mutation-attribution":"F244"},"authored":"2026-08-12","base":"4928e1a3f7a5bf605866f455872fe77b2c74884c","content_sha256":"df3a95d3ff5b150d4c71447463beaffb5e7e7cac934967e78cc05743e734821e","seq":1,"tested_tip":"4520e05e15e3aeedf785f59dd3d027ac7af0819c","wave":"dev-wave-t316-copyout-t840","wave_ref":"refs/heads/worktree-dev-wave-t316-copyout-t840"}

- {"allocations":{"T:growth-hold-measured-seconds":"[T-931]","T:growth-hold-memo-payer":"[T-929]","T:growth-hold-plain-runner":"[T-930]","T:growth-hold-remaining-inventory":"[T-928]"},"authored":"2026-08-12","base":"ba6ac268481f44d5f691bce4261107df8c0fbba4","content_sha256":"610115baa4e331b83f7a47be88ea370b6c73e37f3d369e9209248d642b2510ab","seq":1,"tested_tip":"ab06fda46e45fd64e2dd1c13a59499f634d7da4e","wave":"dev-wave-growth-tests","wave_ref":"refs/heads/worktree-dev-wave-growth-tests"}
- {"allocations":{"T:growth-test-sweep":"[T-932]","T:submission-single-os-write":"[T-933]"},"authored":"2026-08-12","base":"ba6ac268481f44d5f691bce4261107df8c0fbba4","content_sha256":"8166c3e5482a452539cab178c443a029a143d37c3a9cf2f366ba6b335f1f654b","seq":1,"tested_tip":"ab06fda46e45fd64e2dd1c13a59499f634d7da4e","wave":"rulings3-20260812","wave_ref":"refs/heads/worktree-dev-wave-growth-tests"}
- {"allocations":{"D:repo-growth-proportional-test-hold":"D335"},"authored":"2026-08-12","base":"ba6ac268481f44d5f691bce4261107df8c0fbba4","content_sha256":"b168c8da7333382b6c8e3bd32bf8a2a0592515516f3befc4e9940b986b3177b1","seq":2,"tested_tip":"ab06fda46e45fd64e2dd1c13a59499f634d7da4e","wave":"rulings3-20260812","wave_ref":"refs/heads/worktree-dev-wave-growth-tests"}

- {"allocations":{},"authored":"2026-08-12","base":"9f8d6aef14d844d2c6d869a8eb9fd0c0e7e9cd4f","content_sha256":"6c9a4b8cfb07f1a71ddfbfea8401e742d86585f0105c2c6f3dff53f306ca354d","seq":1,"tested_tip":"9f8d6aef14d844d2c6d869a8eb9fd0c0e7e9cd4f","wave":"dev-wave-t816-step4-impl","wave_ref":"refs/heads/worktree-dev-wave-t816-step4-impl"}
- {"allocations":{"D:frozen-evidence-historical-binding":"D336"},"authored":"2026-08-12","base":"9f8d6aef14d844d2c6d869a8eb9fd0c0e7e9cd4f","content_sha256":"90969dbd45eed6b3cee167a3e620c169e94a4e2ca403ac51d611cddad30a1c64","seq":1,"tested_tip":"9f8d6aef14d844d2c6d869a8eb9fd0c0e7e9cd4f","wave":"dev-wave-t816-step4-impl","wave_ref":"refs/heads/worktree-dev-wave-t816-step4-impl"}
- {"allocations":{"F:consumer-liveness-misjudged":"F246"},"authored":"2026-08-12","base":"9f8d6aef14d844d2c6d869a8eb9fd0c0e7e9cd4f","content_sha256":"d7147389d6f80e24bd2ea723bec4ed728b834f1a5692e8e4a2a271c260cc37ba","seq":1,"tested_tip":"9f8d6aef14d844d2c6d869a8eb9fd0c0e7e9cd4f","wave":"dev-wave-t816-step4-impl","wave_ref":"refs/heads/worktree-dev-wave-t816-step4-impl"}
- {"allocations":{"T:dev-wave-resume-at-stage-4-contract":"[T-934]","T:gitlink-advance-authorship-gap":"[T-935]"},"authored":"2026-08-12","base":"9f8d6aef14d844d2c6d869a8eb9fd0c0e7e9cd4f","content_sha256":"ac46f3d759967f7b1b01242b0c646e35a202059542c815635255852249d74a54","seq":2,"tested_tip":"9f8d6aef14d844d2c6d869a8eb9fd0c0e7e9cd4f","wave":"dev-wave-t816-step4-impl","wave_ref":"refs/heads/worktree-dev-wave-t816-step4-impl"}

- {"allocations":{"T:provenance-merge-combined-diff-exemption":"[T-938]","T:rollout-lookup-true-proportionality":"[T-939]","T:scan-session-rows-full-corpus-parse":"[T-937]","T:thread-id-rejects-parent-sessions":"[T-936]"},"authored":"2026-08-12","base":"0e258720b7bb51cfde7c904885bcaeb63bd983b5","content_sha256":"675110a9698d56bc5cb8a04a943c0e1926d77de2579d55914f05b61e7835a91e","seq":1,"tested_tip":"66396bdaaa4af6f624632b6bd67db82242adbaf4","wave":"dev-wave-t886-rollout-fastpath","wave_ref":"refs/heads/worktree-dev-wave-t886-rollout-fastpath"}
- {"allocations":{"D:fastpath-three-exception-regions":"D337"},"authored":"2026-08-12","base":"0e258720b7bb51cfde7c904885bcaeb63bd983b5","content_sha256":"937ac18bce4cea0379519c9b714f2e13bf29afa6a0acc23975f0807a1cd3271b","seq":2,"tested_tip":"66396bdaaa4af6f624632b6bd67db82242adbaf4","wave":"dev-wave-t886-rollout-fastpath","wave_ref":"refs/heads/worktree-dev-wave-t886-rollout-fastpath"}
- {"allocations":{"F:mutation-placed-where-target-path-never-reaches":"F247"},"authored":"2026-08-12","base":"0e258720b7bb51cfde7c904885bcaeb63bd983b5","content_sha256":"7d53d2e58789690574ff032f8a90bfb0f37e8a7208623d463bf9c2c6d18cb007","seq":3,"tested_tip":"66396bdaaa4af6f624632b6bd67db82242adbaf4","wave":"dev-wave-t886-rollout-fastpath","wave_ref":"refs/heads/worktree-dev-wave-t886-rollout-fastpath"}

- {"allocations":{"T:apply-d316-to-provenance-registry-test":"[T-940]"},"authored":"2026-08-12","base":"7b22439d45f492442d88c6408b37a9c1a122bf7f","content_sha256":"ecdb42b1d9b842be441faaffe4e9e3932e6d6ff10aeecb22fcb07c395a0aa5af","seq":4,"tested_tip":"b8dc0a97891e6d2f28f913aaef03b876b5d23e04","wave":"dev-wave-t886-rollout-fastpath","wave_ref":"refs/heads/worktree-dev-wave-t886-rollout-fastpath"}
- {"allocations":{"F:known-violation-ledger-count-pinned-literally":"F248","F:submodule-pointer-drift-after-merge":"F249"},"authored":"2026-08-12","base":"7b22439d45f492442d88c6408b37a9c1a122bf7f","content_sha256":"d180d39cf1bb4895cecb6c8f77fc9acf93a8fd8175c1d5ff125dad007550b6ab","seq":5,"tested_tip":"b8dc0a97891e6d2f28f913aaef03b876b5d23e04","wave":"dev-wave-t886-rollout-fastpath","wave_ref":"refs/heads/worktree-dev-wave-t886-rollout-fastpath"}

- {"allocations":{"T:eight-c-wiring-rulings":"[T-942]","T:mutation-anchor-coverage":"[T-943]","T:p6-implementation-wave":"[T-941]"},"authored":"2026-08-12","base":"6331284e3e418cd3485daaee77024a39ee9ceac9","content_sha256":"338f40e0e1ac3de391f36767f36eeccc6e2493729150ccac9d7650d28bdbc359","seq":1,"tested_tip":"071358471e9fea4ee471143f11fbd5228ca51668","wave":"dev-wave-8c-formal-consumer-wiring","wave_ref":"refs/heads/worktree-dev-wave-8c-formal-consumer-wiring"}
- {"allocations":{"D:formal-consumer-never-issues-non-aborted":"D338","D:private-seam-not-a-trust-boundary":"D339","D:receipt-resolution-out-of-scope":"D340"},"authored":"2026-08-12","base":"6331284e3e418cd3485daaee77024a39ee9ceac9","content_sha256":"f62c7fa72e0ac4dd88469c7d686262c41b210849c0d9971cea4264e55d9c8f41","seq":1,"tested_tip":"071358471e9fea4ee471143f11fbd5228ca51668","wave":"dev-wave-8c-formal-consumer-wiring","wave_ref":"refs/heads/worktree-dev-wave-8c-formal-consumer-wiring"}
- {"allocations":{"F:background-completion-notification-without-output":"F250"},"authored":"2026-08-12","base":"6331284e3e418cd3485daaee77024a39ee9ceac9","content_sha256":"22c08fb045eabe308419aaee4eb7f3a76a8cc6431e64ebcf5ef673d017e21e96","seq":1,"tested_tip":"071358471e9fea4ee471143f11fbd5228ca51668","wave":"dev-wave-8c-formal-consumer-wiring","wave_ref":"refs/heads/worktree-dev-wave-8c-formal-consumer-wiring"}

- {"allocations":{"T:dev-wave-reference-budget-has-zero-headroom":"[T-946]","T:startup-gate-blocks-wave-resume":"[T-945]","T:testops-observation-restart":"[T-944]"},"authored":"2026-08-12","base":"3e7809ab2b048b566ed923091e13df9006d3b877","content_sha256":"33769bdd6cf2e05d721561408b86ddf04a7c9b52eb6ea6f147e813dd00f2403f","seq":1,"tested_tip":"c5ba87a274293036cf99f8fc521ff0a310739662","wave":"dev-wave-testops-observation","wave_ref":"refs/heads/worktree-dev-wave-testops-observation"}
- {"allocations":{"D:testops-observation-frozen-pilot":"D341"},"authored":"2026-08-12","base":"3e7809ab2b048b566ed923091e13df9006d3b877","content_sha256":"165973cb297fc457bbfb06ca2a6f88d3221c85da030abf2a98629d98767780d5","seq":2,"tested_tip":"c5ba87a274293036cf99f8fc521ff0a310739662","wave":"dev-wave-testops-observation","wave_ref":"refs/heads/worktree-dev-wave-testops-observation"}

- {"allocations":{"T:cleanup-submodule-halflanded-worklog":"[T-951]","T:coarse-provenance-fragment-land":"[T-947]","T:rulings-fifth-batch-land":"[T-948]","T:t139-addendum-b-unique-residue":"[T-950]","T:t657-orphan-canonical-citation":"[T-949]","T:testops-observation-ownership":"[T-952]"},"authored":"2026-08-12","base":"d6457230be01c78cb0a09040843178c4463ce247","content_sha256":"ccb1bc13bb9fbacc2082b9f562f8c8a438bff956d34bc4b21e6ac21aaf9dea3c","seq":1,"tested_tip":"b91b0533d6768e4bd2802893915844b78c232614","wave":"dev-wave-t952-residue-sweep","wave_ref":"refs/heads/worktree-dev-wave-t952-residue-sweep"}

- {"allocations":{},"authored":"2026-08-12","base":"fe35e89d11022465ca05602c6523efab3fa1d786","content_sha256":"80c3669e87cd4327efb03395b1c4e64dde6433121e0ce7d2fef24cdd6fae2a63","seq":1,"tested_tip":"497403a1972bc8a3580f80182e34ece83ca89e35","wave":"dev-wave-t499-approval-turns","wave_ref":"refs/heads/worktree-dev-wave-t499-approval-turns"}

- {"allocations":{},"authored":"2026-08-12","base":"a1f81a009331fe3727f4caa82976f813ce718a15","content_sha256":"6929b71afbef7e5f9221832cc30fd40b43956112d7630158db3bd2209909f1c0","seq":1,"tested_tip":"1ad031492458390ce9d6e14f371e3888495ea8f6","wave":"dev-wave-t184-followup","wave_ref":"refs/heads/worktree-dev-wave-t184-followup"}
- {"allocations":{"D:sendside-no-instruction-shaped-artifacts":"D343","D:worktree-liveness-by-cmdline":"D342"},"authored":"2026-08-12","base":"a1f81a009331fe3727f4caa82976f813ce718a15","content_sha256":"e6b1fbd2fe7b9780a13392057528ae965b14d6930509609460c6b491127f5abb","seq":1,"tested_tip":"1ad031492458390ce9d6e14f371e3888495ea8f6","wave":"dev-wave-t184-followup","wave_ref":"refs/heads/worktree-dev-wave-t184-followup"}
- {"allocations":{"F:contamination-detector-false-positive-on-rejected":"F252","F:dryrun-argv-missing-artifact-parent":"F254","F:running-worktree-deleted-by-cwd-scan":"F251","F:truncated-job-prompt-absent-from-job-dir":"F253"},"authored":"2026-08-12","base":"a1f81a009331fe3727f4caa82976f813ce718a15","content_sha256":"ba7967c615ff251854f859884ff180aadb972d520b70b20adff17f0b4461fcc0","seq":1,"tested_tip":"1ad031492458390ce9d6e14f371e3888495ea8f6","wave":"dev-wave-t184-followup","wave_ref":"refs/heads/worktree-dev-wave-t184-followup"}

- {"allocations":{"T:sort-swo-oracle-mutation-coverage":"[T-954]","T:sort-swo-oracle-residuals":"[T-953]"},"authored":"2026-08-12","base":"0f35e043e2c00278c868708538de7f795b2b934a","content_sha256":"12794ed6cf0983e9f6623df201812f2f522b148aa8099aef253cf75df04f9a9a","seq":1,"tested_tip":"f226b3d4fc6e8045b7fbf6f9c87181a7dc8315d9","wave":"dev-wave-t316-r2-oracle","wave_ref":"refs/heads/worktree-dev-wave-t316-r2-oracle"}
- {"allocations":{"D:oracle-contract-in-campaign-identity":"D345","D:sort-swo-independent-oracle":"D344"},"authored":"2026-08-12","base":"0f35e043e2c00278c868708538de7f795b2b934a","content_sha256":"e817c38e7fd6360c8fb5dc72e8725375babb4de8fce5f0c2b603de0503a78d4c","seq":2,"tested_tip":"f226b3d4fc6e8045b7fbf6f9c87181a7dc8315d9","wave":"dev-wave-t316-r2-oracle","wave_ref":"refs/heads/worktree-dev-wave-t316-r2-oracle"}
- {"allocations":{"F:adversary-blocked-when-asked-for-bypass-artifacts":"F256","F:immutable-projection-breaks-exact-type-checks":"F255","F:merge-submodule-gitlink-blocks-land":"F257"},"authored":"2026-08-12","base":"0f35e043e2c00278c868708538de7f795b2b934a","content_sha256":"a015816ae0dc283b3bb322e183b95d284f5725d7b5082ab4df370babe53a9110","seq":3,"tested_tip":"f226b3d4fc6e8045b7fbf6f9c87181a7dc8315d9","wave":"dev-wave-t316-r2-oracle","wave_ref":"refs/heads/worktree-dev-wave-t316-r2-oracle"}

- {"allocations":{"T:guard-pin-independent-trust-root":"[T-955]","T:guard-pin-other-launch-paths":"[T-957]","T:guard-pin-toctou":"[T-956]"},"authored":"2026-08-12","base":"198f0d4b5c99a8220051a6c2c18d1c8a80abd5bf","content_sha256":"4ea79830cba8dfacf7d59f8c993cff1dbaf4781978372b3c86ffbdb308364941","seq":1,"tested_tip":"0e609a5fe26669d9f8db5ca1ddde147b5b590292","wave":"dev-wave-t905-guard-bytes-pin","wave_ref":"refs/heads/worktree-dev-wave-t905-guard-bytes-pin"}
- {"allocations":{"D:guard-bytes-pin-authority":"D346"},"authored":"2026-08-12","base":"198f0d4b5c99a8220051a6c2c18d1c8a80abd5bf","content_sha256":"3c69a3bda4039e1d08dfcdca7761c05288d3f61b556095ea24469608d9a5b3d1","seq":2,"tested_tip":"0e609a5fe26669d9f8db5ca1ddde147b5b590292","wave":"dev-wave-t905-guard-bytes-pin","wave_ref":"refs/heads/worktree-dev-wave-t905-guard-bytes-pin"}
- {"allocations":{},"authored":"2026-08-12","base":"198f0d4b5c99a8220051a6c2c18d1c8a80abd5bf","content_sha256":"26a919162396f6252cfdd8d606ce921a460bce9e3695bfa7d8509ff20543e172","seq":3,"tested_tip":"0e609a5fe26669d9f8db5ca1ddde147b5b590292","wave":"dev-wave-t905-guard-bytes-pin","wave_ref":"refs/heads/worktree-dev-wave-t905-guard-bytes-pin"}

- {"allocations":{"T:durable-write-guard-family":"[T-958]"},"authored":"2026-08-12","base":"35ab6f3f69758fa6a499777de870a5a00811d3d2","content_sha256":"ee372ebb2e5a380aa242edbe0e19dfa525fc85003789e381e6cb0234a0dd6574","seq":1,"tested_tip":"5b93af1acf37b8bfcf6d0b9847933f70b8c6efef","wave":"dev-wave-t933-submission-write","wave_ref":"refs/heads/worktree-dev-wave-t933-submission-write"}

- {"allocations":{"T:l2-slack-routing":"[T-959]"},"authored":"2026-08-12","base":"2310ea67845a98c9cdda10f5e8412e3f872b57df","content_sha256":"28ccdd875378ef12c82353d3fdf79999c4e3e535154de3c603c185aaa3415cc8","seq":1,"tested_tip":"ffc69176d8b04d44e923bd4af680c3c558e09cf5","wave":"dev-wave-t925-l15-inventory","wave_ref":"refs/heads/worktree-dev-wave-t925-l15-inventory"}
- {"allocations":{"F:git-segv-false-red-in-acceptance":"F258"},"authored":"2026-08-12","base":"2310ea67845a98c9cdda10f5e8412e3f872b57df","content_sha256":"5f97ec6c5f2ee873034a64ede6df2efb09f887a2f683e580ad3e30995e266252","seq":2,"tested_tip":"ffc69176d8b04d44e923bd4af680c3c558e09cf5","wave":"dev-wave-t925-l15-inventory","wave_ref":"refs/heads/worktree-dev-wave-t925-l15-inventory"}

- {"allocations":{"T:publication-ledger-strict-extension-uncovered":"[T-961]","T:runner-rejects-conftest-suppression":"[T-960]"},"authored":"2026-08-12","base":"1af0b4be0d9527f6e3277de45eb9e194ec78736e","content_sha256":"c75d22bf9f85ef7c2b1a0f6c18e85a69ca968c7388f3df75e2abeb3a8c5b5e1c","seq":1,"tested_tip":"844b000e8ab3905149bf0a87848b45d8cd39591e","wave":"dev-wave-freeze-hold-residual","wave_ref":"refs/heads/worktree-dev-wave-freeze-hold-residual"}
- {"allocations":{"D:hold-inventory-declares-its-own-incompleteness":"D347"},"authored":"2026-08-12","base":"1af0b4be0d9527f6e3277de45eb9e194ec78736e","content_sha256":"4037dd3c3e99676b05eefc557ae0fba76bc60ca05a979f146987b60f029f8403","seq":2,"tested_tip":"844b000e8ab3905149bf0a87848b45d8cd39591e","wave":"dev-wave-freeze-hold-residual","wave_ref":"refs/heads/worktree-dev-wave-freeze-hold-residual"}

- {"allocations":{"T:addendum-b-b4-erratum-option":"[T-962]","T:orphan-branch-deletion-ruling":"[T-963]"},"authored":"2026-08-12","base":"6df25c7cb54644c45e01123d7faec4c7c6783224","content_sha256":"3b48a8c9df6072bde1e085092c17d7395587582faa84942ca91a694bab57d15c","seq":1,"tested_tip":"5607745d6ec3ee4185580817450c550c4931dc3e","wave":"dev-wave-t949-951-branch-land","wave_ref":"refs/heads/worktree-dev-wave-t949-951-branch-land"}

- {"allocations":{"T:leading-dash-symlink-spec-gate":"[T-964]"},"authored":"2026-08-12","base":"3373ef21de9bfffe4bb9fa3c383671da0bc047d6","content_sha256":"9775f9f04b220d58a3ee4ce234ac8bc1bf317435bd372e391e4b7263fd84230b","seq":1,"tested_tip":"251b0c295576df0b705547337da3bc7aea82555f","wave":"dev-wave-t904-hashobject-sep","wave_ref":"refs/heads/worktree-dev-wave-t904-hashobject-sep"}
- {"allocations":{"F:codex-web-search-invalidates-evidence":"F259"},"authored":"2026-08-12","base":"3373ef21de9bfffe4bb9fa3c383671da0bc047d6","content_sha256":"d0da36e4c5a9deb0c7cd3142e717d7ca2760ccaf8071d3ba3cb3a74debfc3784","seq":2,"tested_tip":"251b0c295576df0b705547337da3bc7aea82555f","wave":"dev-wave-t904-hashobject-sep","wave_ref":"refs/heads/worktree-dev-wave-t904-hashobject-sep"}

- {"allocations":{"T:a12-grammar-promotion":"[T-965]","T:a12-runner-admission-registration":"[T-966]"},"authored":"2026-08-12","base":"bff84a9e0f87e7b888b1297c94491261b96d1ce1","content_sha256":"e36196d2f793d942802d3b97f811154714d1627d63a1eb272c26e5dbdf75e61a","seq":1,"tested_tip":"631f7ae34ec239ca85d1176369dc7d40280be9c8","wave":"dev-wave-t139-a12-stress-check","wave_ref":"refs/heads/worktree-dev-wave-t139-a12-stress-check"}
- {"allocations":{"F:codex-nfc-evidence-loss":"F260","F:pbs-directive-violations-need-submission":"F261"},"authored":"2026-08-12","base":"bff84a9e0f87e7b888b1297c94491261b96d1ce1","content_sha256":"da2731d90850b3b1ce5901626994a6020c44e62d910e73602b2aab829695954b","seq":2,"tested_tip":"631f7ae34ec239ca85d1176369dc7d40280be9c8","wave":"dev-wave-t139-a12-stress-check","wave_ref":"refs/heads/worktree-dev-wave-t139-a12-stress-check"}

- {"allocations":{"T:floor-rep-rc-evidence":"[T-968]","T:floor-reservation-timeout-budget":"[T-969]","T:perf-candidate-adoption":"[T-970]","T:perf-condition-propagation":"[T-967]"},"authored":"2026-08-12","base":"36d873367ae8064850f56bc793ce303857b44396","content_sha256":"2be6ec188a218929b517cd4086e43f2bea4b9e1e7d1afaae129dfad192030077","seq":1,"tested_tip":"2988e5dc3d59ab10e56afb2b3e460d28fc0612ee","wave":"dev-wave-t921-perf-preflight","wave_ref":"refs/heads/worktree-dev-wave-t921-perf-preflight"}
- {"allocations":{"D:perf-preflight-pilot-scoped":"D348"},"authored":"2026-08-12","base":"36d873367ae8064850f56bc793ce303857b44396","content_sha256":"7d72accbb6ccc5246ee13e7c6bbb0dcea5c71401bc28ccad31765918cf6b1e87","seq":1,"tested_tip":"2988e5dc3d59ab10e56afb2b3e460d28fc0612ee","wave":"dev-wave-t921-perf-preflight","wave_ref":"refs/heads/worktree-dev-wave-t921-perf-preflight"}

- {"allocations":{"T:perf-receipt-persist-before-build":"[T-972]","T:sort-swo-oracle-unavailable-on-floor":"[T-971]"},"authored":"2026-08-13","base":"7c9ac4655e341fc8c1e3887ad8c21f2d8d5d3961","content_sha256":"4151bcc2647c01d74ced6bd2327578e8a2f0a27441b81d7d0463f7843715644e","seq":2,"tested_tip":"9a08ebccaf6bcc2ef0112909b5624894ef4d2def","wave":"dev-wave-t921-perf-preflight","wave_ref":"refs/heads/worktree-dev-wave-t921-perf-preflight"}

- {"allocations":{"T:t810-budget-canonical-ledger":"[T-977]","T:t810-executable-authority":"[T-973]","T:t810-guard-two-phase":"[T-976]","T:t810-node-read-toctou":"[T-975]","T:t810-production-producer":"[T-978]","T:t810-staged-dependency-closure":"[T-974]"},"authored":"2026-08-12","base":"f50a28b92187c0dfec8c707912fa68e72a6d5e1f","content_sha256":"85cbd369c133994e1ad25c9c7a337cc8a958dc63eb43e831b7952bcf628e5b5d","seq":1,"tested_tip":"178d90a7f371edba329468df495f312b6f8f6f92","wave":"dev-wave-t922-measure-happypath","wave_ref":"refs/heads/worktree-dev-wave-t922-measure-happypath"}
- {"allocations":{"D:t810-shipped-anchor":"D349"},"authored":"2026-08-12","base":"f50a28b92187c0dfec8c707912fa68e72a6d5e1f","content_sha256":"f388f666af91941d5d0c3246e16f70c79d3e4c4daf8695010c274f405b11c5ae","seq":2,"tested_tip":"178d90a7f371edba329468df495f312b6f8f6f92","wave":"dev-wave-t922-measure-happypath","wave_ref":"refs/heads/worktree-dev-wave-t922-measure-happypath"}
- {"allocations":{"F:focus-review-mustfix-transcription-loss":"F262"},"authored":"2026-08-12","base":"f50a28b92187c0dfec8c707912fa68e72a6d5e1f","content_sha256":"85c939a588ecf89ad39dcf5ce083cf46d3cb50e7e27ae3a64bcd92d32d619d96","seq":3,"tested_tip":"178d90a7f371edba329468df495f312b6f8f6f92","wave":"dev-wave-t922-measure-happypath","wave_ref":"refs/heads/worktree-dev-wave-t922-measure-happypath"}

- {"allocations":{"T:acceptance-worker-timeline-instrumentation":"[T-980]","T:codex-evidence-status-invalid-diagnosis":"[T-981]","T:history-scan-two-phase-ruling":"[T-979]","T:prefilter-scan-sharing-backlog":"[T-982]"},"authored":"2026-08-12","base":"347d6ec608f3f41eb29f9aec8b6975b301534a41","content_sha256":"7ddd254559df2559494e736674671ecfb4ecfb6323ef618663513167bec35870","seq":1,"tested_tip":"11498849f4958a62e5a92784c37fc6b655746d4b","wave":"dev-wave-t950-acceptance-floor","wave_ref":"refs/heads/worktree-dev-wave-t950-acceptance-floor"}
- {"allocations":{"D:prefilter-binds-to-actual-expressions":"D350","D:prefilter-safety-rests-on-slow-path-equivalence":"D351"},"authored":"2026-08-12","base":"347d6ec608f3f41eb29f9aec8b6975b301534a41","content_sha256":"c31b15227e7b73a08724156061f5cd56c3be2076368940a8740ead20117c2f1d","seq":2,"tested_tip":"11498849f4958a62e5a92784c37fc6b655746d4b","wave":"dev-wave-t950-acceptance-floor","wave_ref":"refs/heads/worktree-dev-wave-t950-acceptance-floor"}
- {"allocations":{"F:codex-web-search-duplicate-id-discards-output":"F263","F:multi-axis-masks-value-side-literal-check":"F264"},"authored":"2026-08-12","base":"347d6ec608f3f41eb29f9aec8b6975b301534a41","content_sha256":"4059b053bf697cbd10e2448e6f4a259a0a1250365624b086af1c0db8c3114799","seq":3,"tested_tip":"11498849f4958a62e5a92784c37fc6b655746d4b","wave":"dev-wave-t950-acceptance-floor","wave_ref":"refs/heads/worktree-dev-wave-t950-acceptance-floor"}

- {"allocations":{},"authored":"2026-08-13","base":"dbf423877f6d928cf52d4f4de3a3ff86e6ba4eb3","content_sha256":"96cfa4deb9e08173ae5058e2ec43645fc39108c8cd650d1b74d73f0ec6acf21e","seq":1,"tested_tip":"7157b7ca041d1f0a17ef9bbdf60ef2204bd0541f","wave":"dev-wave-rulings-land-20260812","wave_ref":"refs/heads/worktree-dev-wave-rulings-land-20260812"}
- {"allocations":{"F:chained-old-branch-merge":"F266","F:wave-side-fragment-deletion":"F265"},"authored":"2026-08-13","base":"dbf423877f6d928cf52d4f4de3a3ff86e6ba4eb3","content_sha256":"f0821ca5cc98ce9d8a07b0ec536df7c4f8eae96e2a7b242c750e097e1159f9a7","seq":2,"tested_tip":"7157b7ca041d1f0a17ef9bbdf60ef2204bd0541f","wave":"dev-wave-rulings-land-20260812","wave_ref":"refs/heads/worktree-dev-wave-rulings-land-20260812"}
- {"allocations":{},"authored":"2026-08-12","base":"dbf423877f6d928cf52d4f4de3a3ff86e6ba4eb3","content_sha256":"a65c23953cddda988f516e0b7ea3c02471df165efb62cbe376e414395fa183a4","seq":3,"tested_tip":"7157b7ca041d1f0a17ef9bbdf60ef2204bd0541f","wave":"rulings-20260812-coarse-provenance","wave_ref":"refs/heads/worktree-dev-wave-rulings-land-20260812"}
- {"allocations":{"T:codex-hook-trust":"[T-983]"},"authored":"2026-08-12","base":"dbf423877f6d928cf52d4f4de3a3ff86e6ba4eb3","content_sha256":"5044d82e239af7ce4380802cf22240186ee0ccdce3ec74bfddfb4ef36864c73b","seq":4,"tested_tip":"7157b7ca041d1f0a17ef9bbdf60ef2204bd0541f","wave":"rulings-20260812-coarse-provenance","wave_ref":"refs/heads/worktree-dev-wave-rulings-land-20260812"}
- {"allocations":{"T:l15-budget-inventory":"[T-984]"},"authored":"2026-08-12","base":"dbf423877f6d928cf52d4f4de3a3ff86e6ba4eb3","content_sha256":"191bb1363ca95fd8aa8776009a72a54a0fceed1af2cff82b58c53f2ea2aefc7f","seq":1,"tested_tip":"7157b7ca041d1f0a17ef9bbdf60ef2204bd0541f","wave":"rulings6-20260812","wave_ref":"refs/heads/worktree-dev-wave-rulings-land-20260812"}
- {"allocations":{"D:hold-no-bypass":"D353","D:perf-optional-measurement":"D352"},"authored":"2026-08-12","base":"dbf423877f6d928cf52d4f4de3a3ff86e6ba4eb3","content_sha256":"b44bd633cbb430402bd2817e161c076401836b90427783270e0e44f84ca015cf","seq":2,"tested_tip":"7157b7ca041d1f0a17ef9bbdf60ef2204bd0541f","wave":"rulings6-20260812","wave_ref":"refs/heads/worktree-dev-wave-rulings-land-20260812"}
- {"allocations":{"T:budget-approval-material":"[T-986]","T:login-headroom-unreclaimable":"[T-985]","T:oracle-spec-producer-design":"[T-987]"},"authored":"2026-08-12","base":"dbf423877f6d928cf52d4f4de3a3ff86e6ba4eb3","content_sha256":"579865ee700e4ffc5a21ca3b2233f9c5768018fd53277b8a68488a44d86374d7","seq":1,"tested_tip":"7157b7ca041d1f0a17ef9bbdf60ef2204bd0541f","wave":"rulings7-20260812","wave_ref":"refs/heads/worktree-dev-wave-rulings-land-20260812"}
- {"allocations":{"D:login-headroom-unreclaimable":"D354"},"authored":"2026-08-12","base":"dbf423877f6d928cf52d4f4de3a3ff86e6ba4eb3","content_sha256":"4cbc93349db8e5cc14bd78423b48c72d94d80868e61d5e1e06645a3a661e8dbb","seq":2,"tested_tip":"7157b7ca041d1f0a17ef9bbdf60ef2204bd0541f","wave":"rulings7-20260812","wave_ref":"refs/heads/worktree-dev-wave-rulings-land-20260812"}

- {"allocations":{"T:oracle-spec-producer-design":"[T-988]"},"authored":"2026-08-12","base":"adf7997fdb675a5e0e9481596e4f838825fb97c4","content_sha256":"06ad73e8379d1834225841ab03a69bc31310da63974bfefbfd3ce95adcd090f3","seq":1,"tested_tip":"aabe44e08da2bfe0ac46e05456cc7e3c86f02504","wave":"dev-wave-t499-spec-producer-design","wave_ref":"refs/heads/worktree-dev-wave-t499-spec-producer-design"}
- {"allocations":{"D:oracle-approval-not-machine-enforced":"D356","D:oracle-spec-durable-is-lifecycle-not-schema":"D355"},"authored":"2026-08-12","base":"adf7997fdb675a5e0e9481596e4f838825fb97c4","content_sha256":"9fabb4768e00206c89463d9415fa424e4f2722b5ae2bf28c8c9cf637d3b4564a","seq":1,"tested_tip":"aabe44e08da2bfe0ac46e05456cc7e3c86f02504","wave":"dev-wave-t499-spec-producer-design","wave_ref":"refs/heads/worktree-dev-wave-t499-spec-producer-design"}

- {"allocations":{"T:benchmark-snapshots-cross-worker":"[T-993]","T:benchmark-snapshots-payer-cost":"[T-989]","T:git-optional-locks-missing":"[T-991]","T:real-repo-closure-gaps":"[T-990]","T:receipt-memo-flock-wait":"[T-992]"},"authored":"2026-08-13","base":"03685f7ab16397ad8dbde30aa8083f56785f5148","content_sha256":"e2cf9400548bb60351ab76b65c967d326d245e42b231d55cabde647dc84a40ae","seq":1,"tested_tip":"60ddb2b1d5c292c5c69fd05f798d1da6105534ae","wave":"dev-wave-acceptance-critpath","wave_ref":"refs/heads/worktree-dev-wave-acceptance-critpath"}
- {"allocations":{"D:acceptance-wall-needs-repeated-runs":"D357","D:real-repo-group-stays-serialized":"D358"},"authored":"2026-08-13","base":"03685f7ab16397ad8dbde30aa8083f56785f5148","content_sha256":"36959505b9e0c26a75ad6ceb5f394f1efd3a9719928e5c3a2d16756664603f6b","seq":2,"tested_tip":"60ddb2b1d5c292c5c69fd05f798d1da6105534ae","wave":"dev-wave-acceptance-critpath","wave_ref":"refs/heads/worktree-dev-wave-acceptance-critpath"}

- {"allocations":{"T:ledger-entry-liveness-coverage":"[T-995]","T:ledger-exact-type-pin":"[T-994]"},"authored":"2026-08-13","base":"01487bb46497fba8c991bde9d3534353294eca51","content_sha256":"8b753c05b6fec1f3242e0a27edfc2c1648d6cc41d074581ddb877510e9fee445","seq":1,"tested_tip":"b0cde7eb6997be8bb19810884a12efd62a34b635","wave":"dev-wave-t940-ledger-count","wave_ref":"refs/heads/worktree-dev-wave-t940-ledger-count"}
- {"allocations":{"D:ledger-count-dynamic":"D359"},"authored":"2026-08-13","base":"01487bb46497fba8c991bde9d3534353294eca51","content_sha256":"0d053d2772fbfa50dd6d70f45e912dbd6ec16a36eaa207e3b2c41b266856e6f5","seq":2,"tested_tip":"b0cde7eb6997be8bb19810884a12efd62a34b635","wave":"dev-wave-t940-ledger-count","wave_ref":"refs/heads/worktree-dev-wave-t940-ledger-count"}
- {"allocations":{"F:codex-large-output-breaks-evidence":"F267"},"authored":"2026-08-13","base":"01487bb46497fba8c991bde9d3534353294eca51","content_sha256":"0cdd9cd8d035f347a33793d8bdddcecda409c55da2337ee407cfdc16a7505b58","seq":3,"tested_tip":"b0cde7eb6997be8bb19810884a12efd62a34b635","wave":"dev-wave-t940-ledger-count","wave_ref":"refs/heads/worktree-dev-wave-t940-ledger-count"}

- {"allocations":{},"authored":"2026-08-13","base":"8f485ac6f78f22b9afa5ca93ad0590aed802afa3","content_sha256":"0fde550d9d00b3bf3d8c9b16e5ca105e57325bf5d4a7c1bc5dfd772173c47d75","seq":1,"tested_tip":"828ba3cee685771a054a2183ada2078d8fc2283b","wave":"dev-wave-t983-hook-trust-reconcile","wave_ref":"refs/heads/worktree-dev-wave-t983-hook-trust-reconcile"}
- {"allocations":{},"authored":"2026-08-13","base":"8f485ac6f78f22b9afa5ca93ad0590aed802afa3","content_sha256":"4aa22ecd916335d92661c2a94f04f3d1201fd4070b5e01cad006d09561c4e6e6","seq":2,"tested_tip":"828ba3cee685771a054a2183ada2078d8fc2283b","wave":"dev-wave-t983-hook-trust-reconcile","wave_ref":"refs/heads/worktree-dev-wave-t983-hook-trust-reconcile"}

- {"allocations":{"T:hold-nested-session":"[T-996]","T:hold-runner-cwd-diagnostics":"[T-997]"},"authored":"2026-08-12","base":"a4957341b3f8b076bb2a01087d81eb1361817582","content_sha256":"83e75d0facc955c34faf2d462739cdfbdcbf70cf2dc224d48ba1267487217da9","seq":1,"tested_tip":"09755906f08132d9e52db88b98953bf7c669f28c","wave":"dev-wave-t930-hold-no-bypass","wave_ref":"refs/heads/worktree-dev-wave-t930-land2"}
- {"allocations":{"D:hold-two-layer-enforcement":"D360"},"authored":"2026-08-12","base":"a4957341b3f8b076bb2a01087d81eb1361817582","content_sha256":"7c87c195acfd2f8a78d42680b8a74196c6341eab675bc90351127193a8c52578","seq":2,"tested_tip":"09755906f08132d9e52db88b98953bf7c669f28c","wave":"dev-wave-t930-hold-no-bypass","wave_ref":"refs/heads/worktree-dev-wave-t930-land2"}
- {"allocations":{"F:octopus-merge-breaks-s8c-history":"F269","F:waiter-premature-zero":"F268"},"authored":"2026-08-12","base":"a4957341b3f8b076bb2a01087d81eb1361817582","content_sha256":"9ca5a7b6ea5078297a5a12408f7059bcbcc649fe4fd12aac7c83ab5102241438","seq":3,"tested_tip":"09755906f08132d9e52db88b98953bf7c669f28c","wave":"dev-wave-t930-hold-no-bypass","wave_ref":"refs/heads/worktree-dev-wave-t930-land2"}

- {"allocations":{"T:collect-usage-slug-dash-bug":"[T-999]","T:ledger-subagent-collision":"[T-998]"},"authored":"2026-08-13","base":"c360e502dff7540ebd1193e622dd9228ac612973","content_sha256":"ba10ff8e787208d0dcdf46b551cbe0abc6426900259ce415816d10e940ce53cd","seq":1,"tested_tip":"8d509f1eeaa419c0763b221bf89c149c9ceec99a","wave":"rulings8-20260813","wave_ref":"refs/heads/worktree-rulings8-20260813"}
- {"allocations":{"D:paper-artifacts-keep-tracked":"D361"},"authored":"2026-08-13","base":"c360e502dff7540ebd1193e622dd9228ac612973","content_sha256":"da1c75934ef558c41c58c6b5ef18b516adbebb8c7472f7c5a410701f4a3824b6","seq":2,"tested_tip":"8d509f1eeaa419c0763b221bf89c149c9ceec99a","wave":"rulings8-20260813","wave_ref":"refs/heads/worktree-rulings8-20260813"}
- {"allocations":{},"authored":"2026-08-13","base":"c360e502dff7540ebd1193e622dd9228ac612973","content_sha256":"264cef873f570790e52dbdfb7bdab2b85ea309bb333a83ebc1ca6fad95792304","seq":3,"tested_tip":"8d509f1eeaa419c0763b221bf89c149c9ceec99a","wave":"rulings8-20260813","wave_ref":"refs/heads/worktree-rulings8-20260813"}

- {"allocations":{},"authored":"2026-08-13","base":"28cca4f12a17577e77a561f0a349e7286fabee96","content_sha256":"f2e409cb2d28e08237511e6909c2f1db3684cfe6b739ef23d2db1681dc836360","seq":1,"tested_tip":"f5fce8e136fe0f1a4009b5e381a5fe7d10f1982d","wave":"dev-wave-t930-followup","wave_ref":"refs/heads/worktree-dev-wave-t930-followup"}

- {"allocations":{"T:cleanup-dangling-audit-runtime":"[T-1000]","T:cleanup-occupancy-checker":"[T-1001]","T:codex-validator-heading":"[T-1002]","T:octopus-merge-invariant":"[T-1003]"},"authored":"2026-08-12","base":"5519f78331482bea32320b3b74f1e22b884e5129","content_sha256":"ac8a60f209db128d483243dd4683a80016e3b942f757a273c3e84cf68dd3af49","seq":1,"tested_tip":"dbf7c3dfff2bb2a96a3d664c507cba1846dd632c","wave":"cleanup-branches-cherry-3stage","wave_ref":"refs/heads/worktree-cleanup-branches-cherry-3stage"}
- {"allocations":{"F:cherry-path-existence":"F270","F:octopus-merge-in-main":"F271"},"authored":"2026-08-12","base":"5519f78331482bea32320b3b74f1e22b884e5129","content_sha256":"c63bc2d471b7a1be64a358205990a3535a774bd6a116cb543fbc39f6d01e024c","seq":1,"tested_tip":"dbf7c3dfff2bb2a96a3d664c507cba1846dd632c","wave":"cleanup-branches-cherry-3stage","wave_ref":"refs/heads/worktree-cleanup-branches-cherry-3stage"}
- {"allocations":{"D:known-red-does-not-block-acceptance":"D362"},"authored":"2026-08-13","base":"5519f78331482bea32320b3b74f1e22b884e5129","content_sha256":"b3731c86567915a7b465e9f60933b72383d263c5f45745c003df38fedb3923b2","seq":2,"tested_tip":"dbf7c3dfff2bb2a96a3d664c507cba1846dd632c","wave":"cleanup-branches-cherry-3stage","wave_ref":"refs/heads/worktree-cleanup-branches-cherry-3stage"}

- {"allocations":{"T:codex-worker-launch-acceptance-flake":"[T-1005]","T:startup-gate-residual-hardening":"[T-1004]"},"authored":"2026-08-13","base":"28f1b8a7de0d3ef1c4e99b826d1651dd05c35e7e","content_sha256":"023dbb10767e42eb86b0d3c22587739c514c6df87f9a962f85b70d44f3db9fba","seq":1,"tested_tip":"d18c86a07e0fe96080e0bb9a0e612be08b87a887","wave":"dev-wave-t945-resume-mode","wave_ref":"refs/heads/worktree-dev-wave-t945-resume-mode"}
- {"allocations":{"D:startup-gate-containment-is-raw-graph":"D364","D:startup-resume-mode-is-conditioned-fresh":"D363"},"authored":"2026-08-13","base":"28f1b8a7de0d3ef1c4e99b826d1651dd05c35e7e","content_sha256":"2480500fdce9499602915b5474c30e86f1751d39fe21d25372ad7f512fa620b8","seq":1,"tested_tip":"d18c86a07e0fe96080e0bb9a0e612be08b87a887","wave":"dev-wave-t945-resume-mode","wave_ref":"refs/heads/worktree-dev-wave-t945-resume-mode"}
