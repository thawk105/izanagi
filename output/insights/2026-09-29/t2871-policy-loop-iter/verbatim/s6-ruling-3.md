# [T-2871] 段 6 裁定 3 (親) — 焦点走 4 回目 (33662.nqsv、40b3d09fd) の赤 3 件

焦点走: 3 failed, 390 passed in 37.37s (focus4.log)。namespace inventory (R10) は緑。T1〜T3 の子は import を通過し、実 `_authorize_measurement` から評価まで到達した。

| # | 赤 | 原因 (失敗本文とコードから) | 裁定 | 処置 |
|---|---|---|---|---|
| R11 | `test_pair_pegasus_two_processes_use_distinct_claims_and_measurement_wal`・`test_pair_pegasus_reused_identity_keeps_one_shot_claim` | 1 本目の子で候補は certified、stock が `abort: admission-error (source evidence は stock/review/generator/coder のどれも支持しない)` (build_admission.py:717)。方策 driver の `main` は `patchharness.checkout` を **1 回**だけ開き、候補 (template patch を当てた状態) と stock (patch を外した同じ木) を同じ `sub` で評価する。harness の `checkout` 代役は backoff の 2 checkout 手本を写しており、`resolve_evidence` の代役が「root が 2 本目なら STOCK」と判定するため、stock の評価に候補の token (`'d'*64`) を返していた。実物の admission は正しく拒否している (production の欠陥ではない。t2865 の本番 pair 31855 では同じ流れで stock が `certified-stock`) | real・自分起因 (この wave の test の代役) | fix-3 (test 側のみ): 代役を production と同じ「1 checkout」に合わせる。`resolve_evidence` の代役は genome が stock genome (方策 flag なし) のとき STOCK、候補 genome のとき非 STOCK を返す。build 代役の assert も「coder authority を持つのは候補 genome の build だけ」「`ccbench_dir` は唯一の checkout root」に合わせる。admission・claim・reservation・session は差し替えない |
| R12 | `test_pair_pegasus_crash_consumes_iteration_before_measurement` | 1 本目の子 (強制終了) が作った source dir を、2 本目の子が `_source(root)` で再び `mkdir(parents=True)` して `FileExistsError` | real・自分起因 | fix-3: source の用意を親 (`_policy_pair_case`) で 1 回だけ行い、子は作らない (または冪等にする) |

受理・拒否の含意: R11・R12 は test の代役と準備だけを直し、driver・admission の受理集合を変えない。通る正例 = 1 checkout で候補 (coder authority あり、非 STOCK) → stock (authority なし、STOCK) の順に実 admission を通る T1。拒否されるべき例 (変えない) = stock の評価に非 STOCK の evidence が来たら実 admission が `BuildAdmissionError` で拒否する (今回の赤そのもの)。
