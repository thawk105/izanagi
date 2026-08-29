## 総括

現scopeでproduction consumerを完成できないというplanの最終結論は妥当です。Blockerはrealです。ただし、根拠には次の2点の修正が必要です。

- production reportにthroughput候補bytesが一切ない、という主張は強すぎます。`harness.fitness_tps` はthroughputとして射影され、harness outcome全体がreportへ保存されます。ただし必須fieldではなく、反復scheduleや外部raw-value attestationにも束縛されないため、judge入力には昇格できません。
- 発効連言だけの実装が「consumerなしで発効可能にする」というplanの説明は誤りです。既存連言は12 predicateの全充足を引き続き要求するため、値gate追加はfail-closedです。ただしv7/g12を伴う独立成果物として先行着地することは、親briefの単一変更単位と凍結閉包に反します。

## 所見

1. Blocker: exact `6 × n` observation authorityは既存production schemaから復元できません。

   judgeは6 cellそれぞれについて1始まりのreplicate `1..n`を要求し、scheduleはexact `6 × n`行でなければなりません。[s8c_result_judge.py:376](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t1874-s8c-section5-consumer/orchestrator/campaign/s8c_result_judge.py:376) [s8c_result_judge.py:388](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t1874-s8c-section5-consumer/orchestrator/campaign/s8c_result_judge.py:388) [s8c_result_judge.py:425](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t1874-s8c-section5-consumer/orchestrator/campaign/s8c_result_judge.py:425)

   一方、formal producerは`replicate_index == 0`だけを予約します。[p3_autonomous_workload_trial.py:1299](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t1874-s8c-section5-consumer/orchestrator/campaign/p3_autonomous_workload_trial.py:1299) [p3_autonomous_workload_trial.py:1330](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t1874-s8c-section5-consumer/orchestrator/campaign/p3_autonomous_workload_trial.py:1330) acceptanceも初期slot集合をexact six `replicate_index=0`へ固定するため、追加replicateは通りません。[trial_registry.py:3471](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t1874-s8c-section5-consumer/orchestrator/campaign/trial_registry.py:3471) [trial_registry.py:3484](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t1874-s8c-section5-consumer/orchestrator/campaign/trial_registry.py:3484)

2. Blocker: raw-value attestationも既存bytesから正当に構築できません。

   judgeはraw値のdigestとissuerを持つattestationを各観測に要求します。[s8c_result_judge.py:460](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t1874-s8c-section5-consumer/orchestrator/campaign/s8c_result_judge.py:460) [s8c_result_judge.py:493](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t1874-s8c-section5-consumer/orchestrator/campaign/s8c_result_judge.py:493) [s8c_result_judge.py:555](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t1874-s8c-section5-consumer/orchestrator/campaign/s8c_result_judge.py:555)

   reportの`raw_output_sha256`はraw performance bytesではなくattempt journalのhashで、`observation_sha256`はcell全体の別形式digestです。[p3_autonomous_workload_trial.py:3616](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t1874-s8c-section5-consumer/orchestrator/campaign/p3_autonomous_workload_trial.py:3616) [p3_autonomous_workload_trial.py:3618](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t1874-s8c-section5-consumer/orchestrator/campaign/p3_autonomous_workload_trial.py:3618) [p3_autonomous_workload_trial.py:3619](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t1874-s8c-section5-consumer/orchestrator/campaign/p3_autonomous_workload_trial.py:3619) consumerがreport値からjudge用digestとissuerを新規生成すれば形式上は通せますが、judgeのdocstringが外部producerをtrust rootと定める境界を破る恒真束縛です。[s8c_result_judge.py:2](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t1874-s8c-section5-consumer/orchestrator/campaign/s8c_result_judge.py:2)

3. Major: planの「throughput bytesがない」は狭く言い直す必要があります。

   harness outcomeの`fitness_tps`は`throughput_ops_sec`として読み取られます。[p3_autonomous_workload_trial.py:1665](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t1874-s8c-section5-consumer/orchestrator/campaign/p3_autonomous_workload_trial.py:1665) そのoutcomeはgeneration reportへ保存されます。[p3_autonomous_workload_trial.py:4111](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t1874-s8c-section5-consumer/orchestrator/campaign/p3_autonomous_workload_trial.py:4111) ただし`fitness_tps`はharnessの必須fieldではありません。[p3_autonomous_workload_trial.py:2093](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t1874-s8c-section5-consumer/orchestrator/campaign/p3_autonomous_workload_trial.py:2093)

   したがって正しい裁定は「throughputらしい値が存在しない」ではなく、「存在し得る値をexact反復schedule、correctness、raw-value issuerへ束縛する既存authorityがない」です。凍結文書自身もbench結果のdereference不足とharness値の個体cross-binding未実装を明記しています。[phase3-8c-preregistration.md:470](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t1874-s8c-section5-consumer/docs/phase3-8c-preregistration.md:470) [phase3-8c-preregistration.md:486](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t1874-s8c-section5-consumer/docs/phase3-8c-preregistration.md:486)

4. Blocker: H1/H2別§5値と単一`_ContrastParams`の衝突はrealです。

   §5 validatorはH1とH2のexact 2 blockを受理し、それぞれ独立した`n / delta_min / sd_max / unit / direction`を許します。[s8c_preregistration.py:892](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t1874-s8c-section5-consumer/orchestrator/campaign/s8c_preregistration.py:892) [s8c_preregistration.py:900](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t1874-s8c-section5-consumer/orchestrator/campaign/s8c_preregistration.py:900)

   judgeはscalar `_ContrastParams`を1個だけ受け、同じ`params.n`と閾値を両holdoutへ適用します。[s8c_result_judge.py:117](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t1874-s8c-section5-consumer/orchestrator/campaign/s8c_result_judge.py:117) [s8c_result_judge.py:1422](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t1874-s8c-section5-consumer/orchestrator/campaign/s8c_result_judge.py:1422) [s8c_result_judge.py:1460](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t1874-s8c-section5-consumer/orchestrator/campaign/s8c_result_judge.py:1460) [s8c_result_judge.py:1536](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t1874-s8c-section5-consumer/orchestrator/campaign/s8c_result_judge.py:1536)

   H1/H2同値を仮定する、judgeを2回呼んでprivate結果を合成する、holdout別型へ変更する、のいずれかが必要で、すべて現scope外です。

5. Major: report順、generation番号、bench wallの読み替えはいずれも不可です。

   - report pathsはtrial IDの集合一致しか検査されず、入力順にschedule意味はありません。[trial_registry.py:1598](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t1874-s8c-section5-consumer/orchestrator/campaign/trial_registry.py:1598) manifest側のcanonical順はholdout/arm順であって、乱数scheduleではありません。[trial_registry.py:758](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t1874-s8c-section5-consumer/orchestrator/campaign/trial_registry.py:758)
   - generation列はexact `[1,2]`を要求し、G2だけをoutcomeとして選びます。[s8c_result_judge.py:900](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t1874-s8c-section5-consumer/orchestrator/campaign/s8c_result_judge.py:900) [s8c_result_judge.py:913](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t1874-s8c-section5-consumer/orchestrator/campaign/s8c_result_judge.py:913) その後に別途complete scheduleを要求するため、G1/G2を`n=2`へ転用できません。[s8c_result_judge.py:1867](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t1874-s8c-section5-consumer/orchestrator/campaign/s8c_result_judge.py:1867)
   - `primary_value`はgenerationのbench wall秒合計です。[p3_autonomous_workload_trial.py:3515](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t1874-s8c-section5-consumer/orchestrator/campaign/p3_autonomous_workload_trial.py:3515) [p3_autonomous_workload_trial.py:3622](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t1874-s8c-section5-consumer/orchestrator/campaign/p3_autonomous_workload_trial.py:3622) judgeの固定単位は`throughput_tps`です。[s8c_result_judge.py:40](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t1874-s8c-section5-consumer/orchestrator/campaign/s8c_result_judge.py:40)

   これらの読み替えは凍結されたG2 outcome、完全block、全件報告を破るため、planの拒否判断が正しいです。

6. Major: 発効連言だけの先行について、planの危険説明は誤りですが、独立着地は不可です。

   `effective`は値gate追加後もfreeze、decider、全欄、全predicateの連言です。[s8c_preregistration.py:1951](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t1874-s8c-section5-consumer/orchestrator/campaign/s8c_preregistration.py:1951) 凍結規範も12条件の全充足を要求します。[phase3-8c-preregistration.md:281](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t1874-s8c-section5-consumer/docs/phase3-8c-preregistration.md:281) [phase3-8c-preregistration.md:288](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t1874-s8c-section5-consumer/docs/phase3-8c-preregistration.md:288) よってplan末尾の「発効し得るがconsumerへ到達できない」は成立しません。C07をconsumerなしでSATISFIEDへ倒す変更を同時に入れた場合だけ、その別の誤実装によって成立します。

   ただし受理意味変更はv7とg12、live doc、evidence、core/evaluator/projectionを同じ変更単位へ束縛する必要があります。[phase3-8c-preregistration.md:298](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t1874-s8c-section5-consumer/docs/phase3-8c-preregistration.md:298) [phase3-8c-preregistration.md:303](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t1874-s8c-section5-consumer/docs/phase3-8c-preregistration.md:303) 親briefも同一commitの凍結閉包を指定しています。[brief.md:7](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t1874-s8c-section5-consumer/brief.md:7) [brief.md:8](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t1874-s8c-section5-consumer/brief.md:8) したがって、実装作業順として先に書くのは安全ですが、独立成果物として先行着地してT-1874の一部完了を名乗るのは不可です。

7. Major: 3表とacceptance receiptのfailure atomicityは未解決です。

   `publish_result_table`のrollbackは3表の内部だけです。[s8c_result_judge.py:2411](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t1874-s8c-section5-consumer/orchestrator/campaign/s8c_result_judge.py:2411) [s8c_result_judge.py:2437](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t1874-s8c-section5-consumer/orchestrator/campaign/s8c_result_judge.py:2437) receiptは別のexclusive-createです。[trial_registry.py:6125](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t1874-s8c-section5-consumer/orchestrator/campaign/trial_registry.py:6125) 3表作成後、receipt前の失敗やprocess停止を既存transactionでは巻き戻せません。これは主Blockerが解消されても残る成果物整合性問題です。

## Blocker裁定

- `6 × n` schedule/observations: real blocker。
- 外部raw-value attestation: real blocker。
- H1/H2別params対scalar `_ContrastParams`: real blocker。
- report順、G1/G2、bench wallによる代用: 反証にならず、禁止が正しい。
- 3表とreceiptのfailure atomicity: production結線時に解決が必要な追加blocker。
- 発効値gate自体: 実装可能でfail-closed。ただし独立着地はscopeと凍結閉包に反する。

従って、既存schemaだけでT-1874全体を閉じる反証経路はありません。

## 反証または最小安全経路

既存schemaだけで試せる候補はすべて次の理由で失敗します。

- `harness.fitness_tps`を使う: 値は存在し得るが必須でなく、exact replicate、schedule、外部attestationがない。
- G1/G2を`n=2`にする: G2 outcomeと統計反復が別軸なので不可。
- 6 reportの順をscheduleにする: report順は集合入力でありschedule authorityではない。
- `schedule_row_sha256`から順を作る: digestしかなくrow bytesやschedule indexを復元できない。
- `observation_sha256`からjudge attestationを作る: digest対象が異なり、consumer生成ではissuer独立性もない。
- H1/H2が同値だと仮定する: 現§5 validatorが異値を正当に許すため、未裁定の規範変更になる。

最小安全経路は追加裁定を得て、同じ閉包で次を行うことです。

1. attempt/report authorityをexact `n` replicateへ拡張し、各schedule row bytes、throughput raw values、correctness、trace状態、外部issuer attestationをproduction producerから永続化する。
2. judge入力をholdout別paramsへ変更するか、§5をH1/H2同値へ再凍結する。後者も規範変更なのでユーザー裁定が必要。
3. 3表とreceiptを同じfinalization protocolへ置く。
4. その後にvalue gate、v7、live contract群、g12、production callerを同一commitへ束縛する。

## Scope外

指定された射影資料以外は参照していません。read-onlyのためテストは未実走であり、緑とは判定していません。trigger内部やLayer 3の非射影schemaに追加authorityがある可能性は本レビューの証拠に数えていませんが、射影されたproduction acceptanceと凍結規範だけでは上記Blockerを反証できません。