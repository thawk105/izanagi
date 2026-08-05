静的監査のみ実施し、編集・pytest 実行はしていない。結論は **NO-GO**。

## 所見

**R2-1 / blocker / formal acceptance は `launch_admission` のない report でも canonical receipt を発行する。**

- 根拠: producer は run-start/report に admission を記録するが、completeness の一致項目にも acceptance の照合項目にも含まれない。`orchestrator/campaign/p3_autonomous_workload_trial.py:1322`, `orchestrator/campaign/p3_autonomous_workload_trial.py:1895`, `orchestrator/campaign/autonomous_trial_completeness.py:420`, `orchestrator/campaign/trial_registry.py:2026`
- さらに acceptance 正例 fixture は admission を一切持たない。`orchestrator/tests/test_trial_registry.py:161`, `orchestrator/tests/test_trial_registry.py:182`, `orchestrator/tests/test_trial_registry.py:413`
- 失敗シナリオ: legacy/manual な6 report と lifecycle JSONを用意し、`prereg_commit`・manifest hash・HEADだけ合わせると、registered admission を通った証拠がなくても `output/s8c-trial-registry/receipts/<manifest-sha>.json` が発行される。
- 提案: acceptance と completeness で run-start/report の `launch_admission` 完全一致、`mode=registered-effective`、binding・activation digest・manifest・workload の再導出を必須化する。正例は6件を public producer から生成する。

**R2-2 / blocker / Layer 3 の探索入力隔離と downstream 消費は裁定どおり配線されていない。**

- 根拠: 裁定は探索 admission を検出して `certifying_input:false` を持たせる契約だが、実装は admission を渡さず一律 `acceptance_receipt:null` を書く。`/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t470-t327-wiring/s4-ruling.md:26`, `orchestrator/campaign/p3_autonomous_workload_trial.py:1167`, `orchestrator/campaign/layer3_report.py:492`
- production consumer は `render()` と fresh rebuild のどちらも generic `build_report()` のまま。`orchestrator/campaign/layer3_report.py:564`, `orchestrator/campaign/autonomous_trial_completeness.py:955`
- `build_accepted_report()` の caller は負例 test だけで、関数自身も “future entrypoint” と明記する。`orchestrator/campaign/layer3_report.py:501`, `orchestrator/tests/test_layer3_report.py:408`
- 失敗シナリオ: flag 付き探索 build の Layer 3 成果物に要求値 `certifying_input:false` が残らず、現行 production 経路では receipt による拒否関数自体が呼ばれない。
- 提案: launch admission を Layer 3 producer へ渡して required field を exact 投影し、completeness と実在する運用 consumer を fail-closed に更新する。consumer がないなら downstream 配線済みとは扱わない。

**R2-3 / must-fix / m04 は CLI preflight が先に拒否するため、`run_trial()` 内の順序変異を kill しない。**

- 根拠: `run_trial()` の admission は unknown 検査前だが、CLI は別途 admission を先行実行する。`orchestrator/campaign/p3_autonomous_workload_trial.py:1778`, `orchestrator/campaign/p3_autonomous_workload_trial.py:1823`, `orchestrator/campaign/p3_autonomous_workload_trial.py:2073`, `orchestrator/tests/test_p3_autonomous_workload_trial.py:2502`
- 失敗シナリオ: `run_trial()` の admission を unknown 検査後へ移しても、現 test は `main()` の preflight で同じ U-4 reason を得て緑のまま。programmatic `run_trial(rr80)` だけが `unknown workloads` に変わる。
- 提案: valid Git repo 上で `run_trial(... workloads=["rr80"], allow_unregistered_exploratory=True)` を直接呼び、U-4 reason code を完全一致で検査する。

**R2-4 / should / m07 の外側 commit 一致検査は下位 helper に遮られ、単一理由性がない。**

- 根拠: `admit_registered_launch()` と `require_effective_preregistration()` が同じ commit 一致を二重検査し、test は共通 prefix しか見ない。`orchestrator/campaign/trial_registry.py:1169`, `orchestrator/campaign/s8c_preregistration.py:1764`, `orchestrator/tests/test_trial_registry.py:737`
- 失敗シナリオ: 外側の manifest↔capability 検査だけ削除しても、下位 helper が同じ `[effective-preregistration]` で拒否し、m07 test は緑のまま。
- 提案: mutation anchor を一方へ集約するか、下位 helper を spy にして「外側だけ」を検査する負例を追加する。

**R2-5 / should / m12 は untracked と HEAD-bytes 不一致を同じ広い regex で受け、presence 検査の削除を見逃す。**

- 根拠: `committed is None` と `committed != raw` が連続し、test は gate prefix だけを期待する。`orchestrator/campaign/s8c_acceptance_receipt.py:492`, `orchestrator/tests/test_s8c_acceptance_receipt.py:171`
- 失敗シナリオ: `committed is None` 分岐だけ削除しても、次の `None != raw` が同じ reason prefix で赤を投げるため test は緑。
- 提案: presence と working-bytes mismatch の reason code を分け、message を末尾まで一致させる。

**R2-6 / should / m15 は非空検査と mandatory reason 検査が重複し、非空 predicate 単独の削除を kill しない。**

- 根拠: 空リストは非空検査の後でも mandatory subset 検査に拒否され、test は同一 gate prefix のみを見る。`orchestrator/campaign/s8c_acceptance_receipt.py:245`, `orchestrator/campaign/s8c_acceptance_receipt.py:257`, `orchestrator/tests/test_s8c_acceptance_receipt.py:216`
- 失敗シナリオ: `or not reasons_value` だけ削除しても、mandatory reason 不在で同じ例外となり test は緑。
- 提案: reason-list 契約を単一 validator/anchor に集約するか、m15 を二つの独立変異へ分割する。

**R2-7 / must-fix / receipt verifier は manifest hash を再検証せず、「全参照 bytes」を検証するとの主張が偽である。**

- 根拠: receipt は `manifest_path` と `manifest_sha256` を持つが、fresh hash 対象は registry・lifecycle・report・journalだけ。`orchestrator/campaign/s8c_acceptance_receipt.py:469`, `orchestrator/campaign/s8c_acceptance_receipt.py:498`
- 「all referenced bytes」正例も manifest を生成するだけで改変負例がない。`orchestrator/tests/test_s8c_acceptance_receipt.py:68`, `orchestrator/tests/test_s8c_acceptance_receipt.py:160`
- 失敗シナリオ: receipt commit 後に `input/manifest.json` だけ変更しても `VerifiedAcceptanceReceipt` が発行され、receipt 内 manifest SHA と現行 bytes の参照が分裂する。
- 提案: manifest にも `_assert_digest()` を適用し、manifest・registry・lifecycle・report・journalを各1種ずつ改変する負例を置く。

**R2-8 / must-fix / schema version を上げず既存 v3 に新 required field を追加し、過去の v3 受理集合を狭めている。**

- 根拠: shared v3 schemaへ実行時に `acceptance_receipt` を required 追加し、欠落を拒否する testまで置く。`orchestrator/campaign/layer3_report.py:194`, `orchestrator/campaign/layer3_report.py:207`, `orchestrator/tests/test_layer3_report.py:393`
- 失敗シナリオ: wave 前に生成された正規 `layer3-material-report/v3` は同じ schema version のまま field を持たないため、reader/fresh rebuild 比較で拒否される。
- 提案: 新 schema version を発行するか、旧 v3 reader の受理を維持して新 generator のみ field を追加する。version 据え置きなら人間裁定が必要。

**R2-9 / must-fix / runbook の3起動手順は新しい既定拒否に更新されず、すべて artifact 作成前に失敗する。**

- 根拠: fixture・Claude no-build・build の各コマンドに opt-in がない。`docs/phase3-s8c-autonomous-trial-runbook.md:64`, `docs/phase3-s8c-autonomous-trial-runbook.md:77`, `docs/phase3-s8c-autonomous-trial-runbook.md:96`
- 既定値と gate は拒否側。`orchestrator/campaign/p3_autonomous_workload_trial.py:1726`, `orchestrator/campaign/trial_registry.py:1101`
- 失敗シナリオ: runbook をそのまま実行すると `[u4-exploratory-opt-in]` で止まり、report は一件も生成されない。receipt 発行・commit・再検証手順も存在しない。
- 提案: exploratory 手順へ明示 flag と「常に non-certifying」を追加し、実在する acceptance/receipt 手順だけを記載する。

**R2-10 / should / direct `_run_workload()` の T-276 期待値が run-scope 拒否へ置換され、既存 gate の検出力が落ちた。**

- 根拠: 旧 `match="T-276"` test が scope error testへ変更された。`/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t470-t327-wiring/integrated.diff:2386`, `orchestrator/tests/test_p3_autonomous_workload_trial.py:997`
- worker 内の transport gate 自体は残る。`orchestrator/campaign/p3_autonomous_workload_trial.py:1416`
- 失敗シナリオ: sealed scope 内の worker transport 検査を削除しても、現 direct test はその手前の scope 不在だけを観測して緑となり、禁止 site の build 到達を検出しない。
- 提案: public `run_trial()` が発行した scope 内で `_run_workload()` を呼び、T-276拒否を別 test として復元する。

**R2-11 / nit / m10〜m15 の nodeid 存在検査は production 振る舞いに対して恒真である。**

- 根拠: test source に関数名文字列があることしか検査しない。`orchestrator/tests/test_s8c_acceptance_receipt.py:237`
- 失敗シナリオ:対象 test 本体を `pass` にしても名前が残る限り緑。
- 提案: この meta-test は削除し、実 mutation 実行結果または意味的 assertion を正本にする。

## 変異照合

| 変異 | 判定 | 主な実効 test |
|---|---|---|
| m01 | kill | `test_manifestless_launch_is_rejected_by_default_before_run_root` |
| m02 | kill | `test_holdout_exploratory_opt_in_is_unconditionally_rejected` |
| m03 | kill | `test_u4_holdout_set_is_derived_from_registry_bindings` |
| m04 | **疑い** | CLI preflight が変異を遮る（R2-3） |
| m05 | kill | `test_run_workload_direct_call_without_sealed_scope_is_rejected` |
| m06 | kill | tampered digest の direct helper test |
| m07 | **疑い** | 二重 commit 検査（R2-4） |
| m08 | kill | duplicate start と second-root 負例 |
| m09 | kill | `LOCK_EX` 呼出し観測 |
| m10 | kill | terminal 欠落の exact reason |
| m11 | kill | 二度目の receipt create |
| m12 | **疑い** | 同一 reason の後段検査（R2-5） |
| m13 | kill | report/journal 改変 |
| m14 | kill | valid non-certifying receipt の downstream 拒否 |
| m15 | **疑い** | mandatory reason 検査が遮る（R2-6） |
| m16 | 過剰拒否を検出可 | flag付き ycsb-a の複数 public 正例 |
| m17 | 過剰拒否を検出可 | manifest/registryなしの report 形状正例 |

## §4 契約照合

| 項目 | 判定 |
|---|---|
| 1. 編集面・protected files | PASS。evidence evaluator と contract JSON は未変更。contract 名への production rename もない |
| 2. certifying=true 不発行・reason非空 | PASS。producer/parser/admission の全経路が false 固定 |
| 3. 保証範囲の限定 | PASS。一回性は shared ledger 内、registry introduction は approval authority でないと明記 |
| 4. 既存期待値を緩めない | **FAIL**。R2-10。明示 opt-in は autouse なしで追加されている |
| 5. 12述語 status 不変 | PASS。protected evaluator未変更、0 SAT invariant testも維持 |

caller は、`assert_trial_registry_acceptance` の production CLI (`trial_registry.py:2221`) と test helper/direct負例まで更新済みで、旧 `_trial_launch_binding` の残存 caller もない。一方、`build_accepted_report` は test callerしかなく、runbook と production Layer 3 consumer が取り残されている。

## 総括

**NO-GO**

- blocker: **2件**
- kill されない疑いのある変異: **m04, m07, m12, m15**
- m16/m17 の正例は過剰拒否を検出できる。