[severity: must-fix]  
[攻撃シナリオ] 現 suite は 17,160 node、現物台帳は 15,909 node → plan は 1 node でも欠ければ割付全体を count mode へ戻すため、少なくとも 1,251 node が欠け、duration 割付は必ず静かに不発になる。report に allocation mode も残らず、「実装・実測したが実際は旧割付」という偽の評価が成立する。D532 が指摘した再生成債務が、soft な順位劣化から機能全体の停止へ悪化して再発している。  
[根拠 anchors.md:58-65; orchestrator/tests/acceptance_duration_ledger.json:15913-15915; artifacts/s2-plan.md:24-30; artifacts/s2-plan.md:48-65; docs/decisions.md:21940-21942]  
[提案] 現 scope の「台帳を再生成しない」と両立しないので実装しない。続行するなら、部分台帳方針を再裁定し、`allocation_mode` と ledger digest を実走 evidence に必ず残す。

[severity: must-fix]  
[攻撃シナリオ] K=2 / K=1 / K=1 / K=2 を各2走 → 比較できるのは K の効果だけで、count 割付と duration 割付の差は一度も実走されない。さらに K=2 は2ノードの最大値、K=1 は1ノード値なので、ノード性能・共走・cache・時間帯が交絡する。既存 a1/a2 は pytest wall で K=2 が45.84秒遅いが、これも1回ずつで一般化できない。  
[根拠 brief.md:7-11; anchors.md:58-67; docs/decisions.md:21913-21925; docs/decisions.md:28005-28012]  
[提案] 割付採否は同一 tip・K=2 固定で count/duration の AB/BA を最低8 pair（16 arm走）行う。paired差の標準偏差を \(s_d\) とし、17秒差なら \(n=\lceil((1.96+0.84)s_d/17)^2\rceil\) を事前登録する（\(s_d=30\)秒なら25 pair）。

[severity: must-fix]  
[攻撃シナリオ] 全 shard 合計 \(W=4215.5+3257.0=7472.5\)、K=2 → \(W/(48K)=77.84\)秒なのに、P2 は155.7秒を代入している。しかも鎖が平均 capacity を上回ることは「鎖が律速候補」でしかなく、鎖の開始遅延・別 component の裾・idle gap・可変残差を消さないため、0〜17秒という利得上限は導けない。実際、K変更で総 busy-time は約9,000秒から14,862秒へ変化している。  
[根拠 brief.md:40-44; artifacts/s2-plan.md:145-161; anchors.md:74-87; docs/decisions.md:28000-28006]  
[提案] P2 と0〜17秒上限を採否根拠から削除する。不等式は再検討 trigger に限定し、利得はK=2固定の割付A/Bで判定する。

[severity: must-fix]  
[攻撃シナリオ] shard-1 へ重い component を移す → 参照走の残差39.2秒を仮に固定しても、最遅 worker が132.0秒から228.01秒を超えれば shard-0 の267.21秒を超える。閾値は増分96.01秒（brief の266.89秒を使えば95.69秒）にすぎない。さらに「固定費」は test report duration に入らない prewarm・collection後処理・idle・集約を含み、selected内容で発火する prewarm があるため、割付変更で残差自体も動く。実際の残差は旧走56.4/39.2秒から新走84.61/58.98秒へ変化している。  
[根拠 anchors.md:44-53; anchors.md:69-80; tools/acceptance_shards.py:799-809; tools/acceptance_shards.py:920-959; orchestrator/tests/conftest.py:1517-1550]  
[提案] `wall−worker duration和` を固定費と呼ばず、collection・prewarm・scheduler開始・finalizationを時刻計装する。shard-1 の閾値は各A/B走で再計算する。

[severity: must-fix]  
[攻撃シナリオ] 「K=2台帳をK=2割付へ使う」→ 生成器は任意のJUnitを受け取るだけで、現物schemaにも生成日時・tested tip・K・worker数・scheduler・nodeが無い。したがって現台帳がいつ、どのKで採取されたかは現物から確認不能である。また仮にK=2由来でも、元のcount割付からduration割付へ共走相手を変えればdurationも変わるため、同じKだけでは自己整合的にならない。  
[根拠 tools/update_acceptance_duration_ledger.py:34-65; tools/update_acceptance_duration_ledger.py:204-240; orchestrator/tests/acceptance_duration_ledger.json:15913-15915; docs/decisions.md:21918-21921; docs/decisions.md:28005-28006]  
[提案] provenance sidecarへ tip・K・scheduler・worker数・入力JUnit digest・nodeタグを束縛する。再生成をscope外のままにするなら、現台帳をK=2自己整合の根拠にせず実装を見送る。

[severity: must-fix]  
[攻撃シナリオ] 同じ台帳をD746とshard割付が消費 → K=1では走内順序だけ、K=2では順序と割付の両方が変わり、K比較は二機構の合成効果になる。部分台帳ではD746は既知値と第96位擬似値で発火する一方、planの割付は全体count fallbackとなる。非loadgroup走では既存readerが台帳を読まないため、現planでは両方不発である。この発火行列をreportが記録しないため、結果を層別できない。  
[根拠 orchestrator/tests/conftest.py:953-1002; orchestrator/tests/conftest.py:1032-1052; orchestrator/tests/conftest.py:1388-1396; docs/decisions.md:29077-29088; artifacts/s2-plan.md:69-83]  
[提案] reorder有無・allocation mode・ledger digestを実走ごとに記録し、K=2 count/durationのfactorだけを切り替える。片方だけ発火した走を同じ母集団へ混ぜない。

[severity: should-fix]  
[攻撃シナリオ] K=2がK=1と同等または遅い → a1/a2では最大pytest wallが307.29対261.45秒、job Elapse合計も544対270秒で、PBS requestとworker数も2倍になる。単一request失敗率を \(q\) とすれば、独立近似でもK=2の失敗率は \(1-(1-q)^2\) となり、さらにmerge gate固有の故障面が加わる。queueを速度目標から外しても、request数・queue可用性・資源消費は消えない。  
[根拠 anchors.md:62-67; anchors.md:82-87; docs/decisions.md:28363-28375; docs/decisions.md:28381-28400]  
[提案] 本wave内では4層実測と「duration割付を実装しない」裁定まで行える。既定K変更はscope外なので、K=1化は別裁定へ送り、node秒・core秒・request数・no-verdict率も併記する。

[severity: should-fix]  
[攻撃シナリオ] `real-repo` 210.5秒/72件を不変の分割不能鎖として一般化 → 現正本は73 functionで、そのうち4件は実資源を使わないover-approximationである。既存xdist groupがあるitemには`real-repo` markerを追加しないため、実際の鎖集合はmarkerやcollection変更でも動く。参照走の72件との差も未説明で、210.5秒は当該走の観測値にしかならない。  
[根拠 brief.md:30-33; anchors.md:22-23; orchestrator/tests/conftest.py:338-354; orchestrator/tests/conftest.py:1327-1333; docs/decisions.md:28000-28006]  
[提案] 各走で実際のreal-repo node集合・件数・durationを記録する。細分化はD532の別scopeだが、固定床として採否式へ入れない。

## 未確認事項

- 現物台帳の正確な生成Kは確認不能。履歴から受入shard走由来とは推定できるが、K=2を証明するfieldはない。
- a3k1 / a4k2 は射影資料上で未完了であり、4走設計の最終値はない。
- node identity、同居job、cache状態、collection/prewarm/finalizationの区間時刻は未記録。
- anchors記載の生report・JUnit・dispatcher logは独立再集計していない。
- pytestは実行しておらず、緑とは判定していない。Web検索も使用していない。

## 総括

must-fix 6件。推奨は、現planのduration重み割付を実装しないことである。  
最大の理由は、現台帳ではweighted経路が必ずsilent fallbackし、機能が実効発火しない点にある。  
P2の0〜17秒上限は算術・論理とも成立せず、予定4走も割付効果を測っていない。  
scope 1のK比較は完遂してよいが、D724の既定K変更は別裁定として切り出すべきである。  
再検討は、provenance付き台帳・発火証拠・K=2固定のcount/duration対測定を用意できた時点に限る。