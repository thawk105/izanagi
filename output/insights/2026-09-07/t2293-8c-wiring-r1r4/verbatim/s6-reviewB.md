## blocker

1. **production caller が物理束縛用の必須引数3件を渡しておらず、新検査は実経路で一度も発火しない。**  
   [`evaluate_formal_origin` は3件を必須化](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2293-8c-wiring-r1r4/orchestrator/campaign/reflux_formal_consumer.py:1218)しているが、[唯一の production caller](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2293-8c-wiring-r1r4/orchestrator/campaign/p3_autonomous_workload_trial.py:1862)は `campaign_output_root`、`origin_run_plan_sha256`、`attempt_capability_sha256` を渡していない。`_finish_trial` は[report 構築前にこの caller を実行](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2293-8c-wiring-r1r4/orchestrator/campaign/p3_autonomous_workload_trial.py:3778)するため `TypeError` となる。さらに projection が未生成なので、[origin terminal の append も拒否](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2293-8c-wiring-r1r4/orchestrator/campaign/trial_registry.py:4932)される。親の焦点走 `625 passed / 4 failed` と一致する。  
   **成果物影響:** 試行台帳は start だけが残り、formal receipt、evidence root 参照、terminal projection が作られない。certified 選択は増えず、材料レポートも新しい物理束縛を参照できない。

## must-fix

1. **raw lifecycle loader では `origin_binding` と `origin_run_plan_sha256` の iff が成立していない。**  
   loader は [base と base+key を無条件に受理](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2293-8c-wiring-r1r4/orchestrator/campaign/trial_registry.py:4427)し、digest の形式しか見ない。対応関係は [terminal 行が来た時の projection 有無](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2293-8c-wiring-r1r4/orchestrator/campaign/trial_registry.py:4507)、または[最終 acceptance の report](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2293-8c-wiring-r1r4/orchestrator/campaign/trial_registry.py:5381)で初めて確認される。したがって start-only の (g)、(h) は loader 単体では拒否できない。start+偽 projection の組も loader だけなら通る。API writer は [`record_trial_start_once`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2293-8c-wiring-r1r4/orchestrator/campaign/trial_registry.py:4682)で拒否するが、段4裁定が要求した loader 強制を満たさない。  
   **成果物影響:** 偽 start が試行台帳上の trial ID を占有し、正式な再入を拒否させられる。最終 acceptance は防ぐが、台帳の値と参照可能な lifecycle 状態は変わる。

## nit

1. **33 identity の相異検査が重複している。**  
   producer は [`_derive_origin_campaign_runs`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2293-8c-wiring-r1r4/orchestrator/campaign/p3_autonomous_workload_trial.py:1322)で再検査するが、直後に呼ぶ topology builder も [`_validate_members`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2293-8c-wiring-r1r4/orchestrator/campaign/reflux_origin_topology.py:368)で同じ33相異を要求する。  
   **成果物影響:** 現時点ではなし。同一入力を同じ理由で二重拒否するだけである。

2. **別 trial・過去 attempt のテスト名が、実際に検査した範囲より強い。**  
   [`_relocate_ordered_wal`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2293-8c-wiring-r1r4/orchestrator/tests/test_reflux_formal_consumer.py:596)は現 trial の WAL bytes を別 root へコピーしている。したがって [別 trial test](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2293-8c-wiring-r1r4/orchestrator/tests/test_reflux_formal_consumer.py:796)と[過去 attempt test](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2293-8c-wiring-r1r4/orchestrator/tests/test_reflux_formal_consumer.py:826)が直接証明するのは root 所属検査であり、foreign WAL 内容の識別ではない。  
   **成果物影響:** なし。ただしテスト名だけを根拠に D1674 の上限を超えた保証を説明すると誤認を招く。

## 偽装入力の実測判定

現在の production 結線は blocker により consumer 呼出前に `TypeError` になる。以下の「consumer 判定」は `evaluate_formal_origin` とその下位検査を直接通した場合である。

| 入力 | 判定 | 実測アンカー | 成果物への意味 |
|---|---|---|---|
| (a) q10/q11 root・config 交換、provenance 再生成 | **consumer 単体では拒否。結線経路では新検査へ未到達。** FC05a-c が通ることは test helper `test_reflux_formal_consumer.py:559` で先に確認し、lock からの再構成 identity と予定 identity の不一致を `reflux_formal_consumer.py:429-435` で FC03 にする。 | `test_reflux_formal_consumer.py:755-775` | 通れば材料が q10 と q11 の物理 campaign を逆参照する。 |
| (b) 別 path・別 object envelope、33 identity 再宣言 | **限定的に拒否。** 別 path は固定 path `origin/recovery-envelope.json` の読取り `reflux_formal_consumer.py:385-386` で拒否し、別 object は disk bytes と引数 object の一致 `:387-394` で拒否する。ただし canonical path、digest 引数、attempt digest 引数まで整合的に差し替える直接 caller は lifecycle token を渡さないため、この API 単体では拒否できない。 | `reflux_formal_consumer.py:371-394`, `test_reflux_formal_consumer.py:737-752` | 通れば lifecycle の plan 参照と formal receipt の plan 参照が分離する。 |
| (c) 別 trial の33 WAL流用、provenance 書換え | **foreign root を参照する形は拒否。canonical root へ後置した整合的コピーは拒否できない。** projection と source WAL の両方を計算 root 配下へ限定する。 | `reflux_formal_consumer.py:940-948`, `test_reflux_formal_consumer.py:796-823` | 後者が通ると材料レポートは別 trial 由来の WAL を現 trial の材料として参照しうる。 |
| (d) 過去 attempt、別 replicate・別 prereg 世代の WAL | **authentic な current root・attempt digest を使う consumer では拒否。結線経路は未到達。** foreign root は `:940-948`、lock 内 attempt は `:904-918` で拒否する。replicate、attempt、prereg 世代は attempt capability digest の preimage に含まれる。 | `trial_registry.py:2226-2250`, `test_reflux_formal_consumer.py:826-851` | 通れば試行台帳が別 attempt の実行材料を現在 attempt へ帰属させる。 |
| (e) 実行後に canonical root へ整合 lock/WAL を後置 | **拒否できない。期待どおり。** 実装自身が明記している。 | `reflux_formal_consumer.py:20-23` | trusted-writer 前提が破られると、物理実行0件の偽材料を排除できない。 |
| (f) 1件だけ `build_attempt_id` 重複 | **consumer 単体では拒否。** 33件の attempt 相異を FC05a で検査する。 | `reflux_formal_consumer.py:1011-1012`, `test_reflux_formal_consumer.py:945-959` | 通れば2 record が同じ実行 attempt を指し、33件の全単射が崩れる。 |
| (g) originless start に digest を追加 | **API writer と最終 acceptance は拒否するが、start-only raw loader は拒否できない。** terminal が無い間は許可形として残る。 | `trial_registry.py:4427-4483`, `:4682-4686`, `:5381-5391` | 偽 start が trial ID を占有し、正式な試行を阻害できる。 |
| (h) origin start から digest を削除 | **API writer と完全な lifecycle/acceptance は拒否するが、start-only raw loader は拒否できない。** | `trial_registry.py:4507-4517`, `:4682-4686`, `:5381-5391` | 起点 plan の durable 参照が無い start を一時的に正当な台帳行として扱う。 |
| (i) `execution-provenance/v1` | **consumer 単体では拒否。** exact 8 keys と v2 literal の双方を要求する。 | `reflux_result_evidence.py:564-575` | 通れば v1/v2 の世代判別と `campaign_run_identity` 必須性が失われる。 |
| (j) native/legacy 混在 | **consumer 単体では拒否。** family 集合が `{"native-stage-payload"}` の完全一致でなければ trigger を返さず、FC05c になる。 | `reflux_formal_consumer.py:951-966`, `:1013-1018` | 通れば同じ projection に複数の trigger 解釈が生じる。 |

## 恒真化の探索

- `result_evidence.issuer.kind == "trusted-physical-harness"` は[文字列比較だけ](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2293-8c-wiring-r1r4/orchestrator/campaign/reflux_result_evidence.py:243)である。`execution_receipt_sha256` も[SHA-256形式だけを検査](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2293-8c-wiring-r1r4/orchestrator/campaign/reflux_result_evidence.py:604)し、receipt の実在や issuer を解決しない。これは権限・物理実行の証明ではない。

- `build_attempt_id` は projection、WAL、record、provenance 間で文字列を一致させるだけである。`reflux_result_evidence.py:668-679,704-705` と `reflux_formal_consumer.py:828-831,1098-1099` は整合性を証明するが、OS 上の実行を証明しない。

- classification の `authority_id="p3-autonomous-workload-trial"` と固定 policy digest も [`p3_autonomous_workload_trial.py:4862-4869`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2293-8c-wiring-r1r4/orchestrator/campaign/p3_autonomous_workload_trial.py:4862)では名乗りである。周囲の attempt capability は改ざん検知に使えるが、この文字列自体が実行主体を認証するわけではない。

- canonical leaf root の検査は完全な恒真ではない。planned identity から leaf を計算し、disk lock と WAL の実 path を照合している。ただし base の `campaign_output_root` は caller の文字列で、[type 検査しかない](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2293-8c-wiring-r1r4/orchestrator/campaign/reflux_formal_consumer.py:1247)。したがって証明できるのは「caller が指定した base の canonical leaf 配下」であり、deployment 上の唯一の root ではない。

- 33 identity 相異は producer `p3_autonomous_workload_trial.py:1322-1331` と topology `reflux_origin_topology.py:368-370` の二重検査である。

## 3項等式と identity の決定性

FC03 の3項等式は維持されている。`execution_provenance.campaign_id == trial_binding.campaign_id == capability.campaign_id` は [`reflux_formal_consumer.py:832-837`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2293-8c-wiring-r1r4/orchestrator/campaign/reflux_formal_consumer.py:832)に残り、物理値は別 key `campaign_run_identity` として `:919-923` で照合される。lock から物理 component を除いた論理 config も `:925-938` で capability の論理 ID へ戻される。物理値が論理 `campaign_id` へ混入して通る経路は見つからない。

物理 identity は論理 `CampaignConfig` に `{attempt_capability_sha256, query_ordinal}` を加え、`ident.canonical_preimage` から導出する `p3_autonomous_workload_trial.py:1270-1286`。PID・時刻・乱数の混入経路は見つからない。process identity 自体は PID と時刻を持つ `:1550-1557` が、attempt capability digest の preimage `trial_registry.py:2226-2250` には含まれない。

同一 slot・同一 q は同じ capability digest と同じ identity になる。再入は既存 run root と lifecycle start を `p3_autonomous_workload_trial.py:4794-4804` で fail-closed にする。別 attempt、別 replicate、別 prereg 世代は `attempt_index`、`replicate_index`、`prereg_generation`、P/C が digest に入るため別 identity になる。

## 名乗りの上限

名乗ってよいのは次までである。

- lifecycle start に起点専用 digest を加える writer/API/full-acceptance 契約を実装した。
- v2 provenance schema と、direct consumer の v2-only 受理を実装した。
- 33個の予定 identity を論理 config、slot digest、q から決定的に導出した。
- direct consumer に envelope、lock、論理/物理 identity、WAL 所属、shape family の静的整合検査を加えた。
- これらは caller base root と D1674 の trusted-writer 前提下の artifact consistency 検査である。

名乗ってはいけないのは次である。

- 「8c 結線完了」「production 経路で新検査が発火する」。唯一の caller が壊れている。
- 「P6 が発火する」。consumer は明示的に `P6Unavailable` しか生成しない。
- 「物理実行を保証する」「trusted harness を認証する」「execution receipt の実在を確認する」。
- 「発行3条件を満たした」「本番 authority が存在する」。依然 0/3、0件である。
- 「originless compatibility test は緑」。焦点走の同 test は origin-enabled 部分で失敗している。

source comment は D1674 の限界を [`reflux_formal_consumer.py:20-23`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2293-8c-wiring-r1r4/orchestrator/campaign/reflux_formal_consumer.py:20)と [`reflux_result_evidence.py:3-10`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2293-8c-wiring-r1r4/orchestrator/campaign/reflux_result_evidence.py:3)で正しく明記しており、コメント自体の過剰主張は見つからない。一方、`trusted-physical-harness` という issuer 名や foreign-WAL test 名を認証事実として読むことはできない。

## 受理集合の記録

裁定済み2件は差分どおり動いている。

1. lifecycle start は base 15 keys から、base と base+`origin_run_plan_sha256` の2択へ**拡張**された。
2. `execution-provenance/v2` が**追加**され、起点 consumer は v2-only へ**縮小**された。

ただし1件目の拡張は raw loader では裁定より広い。`origin_binding` を直接見ず、terminal projection または acceptance report まで iff を遅延するため、start-only の originless+key と origin-key欠落を受理する。これは must-fix の追加受理である。

「緩めていない」と書ける変更は envelope の固定 path/digest/object 一致、lock からの identity 再導出、attempt/q 束縛、WAL の computed root 所属、native-only family で、いずれも受理集合を縮小する。`OriginProducerInputs.run_plan` の廃止と consumer 必須引数追加は Python 呼出規約の縮小であり、wire 拡張ではない。`result-evidence/v1` の9 key と2 refs は不変である。

## 裁定パッケージ候補

- `issuer.kind` と未解決の `execution_receipt_sha256` は物理 producer・evidence writer 層の問題で、本 wave 内で権限証明へ格上げできない。
- canonical root への整合 lock/WAL 後置は拒否不能であり、D1674 の trusted-writer 運用前提そのものである。
- 材料レポートにこの保証限界を表示する renderer は scope 外のままである。

## 総括

判定: **fix 必要**。作り直しではなく、少なくとも production caller と lifecycle loader の修正が必要。  
最大点1: 必須3引数が唯一の caller から欠落し、新しい物理束縛検査は実経路で発火しない。  
最大点2: start-only raw lifecycle では origin key の iff を拒否できず、裁定より受理集合が広い。  
最大点3: canonical-root 検査は artifact 整合性までで、物理実行や trusted writer の認証にはならない。  
テストは今回実行しておらず、親の実走結果 `625 passed / 4 failed` と静的検査だけを根拠にした。