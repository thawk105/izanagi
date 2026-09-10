## 総括

現行 scope のまま着手できる安全な経路はありません。段2 plan の停止判断は正しい一方、次の3点を修正する必要があります。

- `trial_registry` は唯一の6-report集約点ですが、supervisorからの実 call chainではありません。
- 現行 C07 evaluator はproduction callerを一切検出しません。
- 3表とacceptance receiptを一体化する既存transactionはありません。

したがって `section5_value_violations`、v7、g12だけを先行着地させてはいけません。

## 所見

1. `trial_registry` 配置は集約点としては正しいが、supervisor consumerという表現には一致しません。

   `p3_autonomous_workload_trial` から `assert_trial_registry_acceptance` への呼出しはなく、実際のproduction入口はregistry CLIです。[trial_registry.py:6156](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t1874-s8c-section5-consumer/orchestrator/campaign/trial_registry.py:6156) から [trial_registry.py:6223](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t1874-s8c-section5-consumer/orchestrator/campaign/trial_registry.py:6223)。従って段2 planの `run_trial -> reports -> acceptance` はartifact provenanceであり、静的なcaller chainではありません。

2. C07 evaluatorは実 callerを検出できません。

   契約はconsumerをjudge自身に置いています。[contract:267](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t1874-s8c-section5-consumer/orchestrator/campaign/s8c_preregistration_evidence_contract.v1.json:267)  
   evaluatorもentrypointを3関数へhard-codeし、consumer pathとjudge pathの一致を要求します。[s8c_preregistration_evidence.py:2776](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t1874-s8c-section5-consumer/orchestrator/campaign/s8c_preregistration_evidence.py:2776)  
   その後に検査するのはjudge内部だけで、最終結果も常に `EVIDENCE_UNDEFINED` です。[s8c_preregistration_evidence.py:3068](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t1874-s8c-section5-consumer/orchestrator/campaign/s8c_preregistration_evidence.py:3068)

   段2 planの「consumer_requirementをtrial_registryへ変更」は、D537とこのhard-codeの双方に反します。正しくはconsumer_requirementをjudgeに残し、別のrequired evidenceとしてproduction callerを追加すべきです。

3. H1/H2別paramsは現judgeへ渡せません。

   `_ContrastParams` はscalar一個で、`judge` も一個だけ受け取ります。[s8c_result_judge.py:117](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t1874-s8c-section5-consumer/orchestrator/campaign/s8c_result_judge.py:117)、[s8c_result_judge.py:1947](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t1874-s8c-section5-consumer/orchestrator/campaign/s8c_result_judge.py:1947)  
   H1/H2別値を構築せよというbriefと、judge schema不変更は同時には満たせません。

4. 既存scheduleとattemptはjudgeの反復集合ではありません。

   `s8c_schedule` は明示的に6 cell ordinalだけで、観測や反復blockではありません。[s8c_schedule.py:1](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t1874-s8c-section5-consumer/orchestrator/campaign/s8c_schedule.py:1)、[s8c_schedule.py:317](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t1874-s8c-section5-consumer/orchestrator/campaign/s8c_schedule.py:317)  
   judgeは6×n行を要求します。[s8c_result_judge.py:376](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t1874-s8c-section5-consumer/orchestrator/campaign/s8c_result_judge.py:376)  
   formal acceptanceの初期slot集合はreplicate 0だけです。[trial_registry.py:3471](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t1874-s8c-section5-consumer/orchestrator/campaign/trial_registry.py:3471)

5. throughputそのものが完全に不存在という段2記述は強すぎます。

   supervisor内部には `fitness_tps` 由来のthroughputがあります。[p3_autonomous_workload_trial.py:1665](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t1874-s8c-section5-consumer/orchestrator/campaign/p3_autonomous_workload_trial.py:1665)  
   ただし正式terminal authorityの `primary_value` はbench wall秒であり、judge用の6×n schedule、correctness、trace-disabled、独立issuer付きraw-value attestationにはなっていません。[p3_autonomous_workload_trial.py:3616](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t1874-s8c-section5-consumer/orchestrator/campaign/p3_autonomous_workload_trial.py:3616)、[s8c_result_judge.py:493](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t1874-s8c-section5-consumer/orchestrator/campaign/s8c_result_judge.py:493)

6. 段2 planの配置行は早すぎます。

   `5978–5997` 後にもmeasurement target再読とreport snapshot再確認が続きます。[trial_registry.py:6013](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t1874-s8c-section5-consumer/orchestrator/campaign/trial_registry.py:6013)、[trial_registry.py:6030](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t1874-s8c-section5-consumer/orchestrator/campaign/trial_registry.py:6030)  
   条件付き最小アンカーは、それらが完了する `6101` 後、receipt構築前です。

7. 3表とreceiptは失敗原子的ではありません。

   3表publisherは自身の例外時には作成済み表を削除しますが、acceptance receiptは別のrepository内O_EXCL書込みです。[s8c_result_judge.py:2384](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t1874-s8c-section5-consumer/orchestrator/campaign/s8c_result_judge.py:2384)、[trial_registry.py:5343](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t1874-s8c-section5-consumer/orchestrator/campaign/trial_registry.py:5343)  
   現receiptには3表のpath、digest、transaction IDもありません。[trial_registry.py:6102](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t1874-s8c-section5-consumer/orchestrator/campaign/trial_registry.py:6102)  
   表成功後のreceipt失敗、receipt成功後の表失敗、process crashを既存機構だけで閉じられません。

## Blocker裁定

着手には次の4点だけ、追加裁定が必要です。

1. supervisorがreport producerで、registry CLIがproduction aggregate consumerというartifact-flow解釈を認めるか。直接callを要求するなら、新しいcampaign orchestratorが必要となり現scope外です。

2. H1/H2について、既存judge一個が既存 `_ContrastParams` のH別mappingを受ける最小拡張を許すか、または§5で両holdout同値を規範化するか。

3. exact 6×n throughput rowsとraw-value attestationを、どの既存producer/schemaが発行するか。既存report/attempt schemaのversioned拡張も禁止するなら実装不能です。

4. canonical 3表出力rootを定め、表digestをreceiptへ束縛するC07専用の回復可能transactionとreceipt schema更新を許すか。単なる呼出し順だけでは失敗原子性を満たしません。

## 反証または最小安全経路

裁定後の最小経路は次です。

- [trial_registry.py:5551](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t1874-s8c-section5-consumer/orchestrator/campaign/trial_registry.py:5551) を唯一の6-report consumerとして維持する。
- 全snapshot再確認後の [trial_registry.py:6101](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t1874-s8c-section5-consumer/orchestrator/campaign/trial_registry.py:6101) にC07専用consumerを置く。
- existing judgeを一度だけ呼び、3表とreceiptを同一transaction IDとdigest集合へ束縛する。
- C07契約にはproduction caller evidenceを追加するが、D537どおりconsumer_requirementはjudgeの3 entrypointに残す。
- [s8c_preregistration_evidence.py:2776](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t1874-s8c-section5-consumer/orchestrator/campaign/s8c_preregistration_evidence.py:2776) を、registry entrypointから3関数への実import/call、順序、戻り値使用まで検査する形へ拡張する。
- consumer、evaluator、receipt transactionが閉じた同一commitでだけv7とg12を発行する。

## Scope外

- 別judge、並行schema、汎用workflow、G1/G2の反復扱い、wall秒のthroughput転用は拒否します。
- 射影されたT-2018所有pathとの現時点の重複はありません。[authority-s2.md:26](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t1874-s8c-section5-consumer/authority-s2.md:26) 後発重複、特に`source_digest`へ触れる必要が生じた場合はauthor開始前に停止対象です。
- read-onlyのためテストは未実走です。