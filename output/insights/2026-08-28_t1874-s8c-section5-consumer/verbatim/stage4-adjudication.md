# T-1874 段4裁定

## 総括

GO ではなく、ユーザー再裁定待ちで fail-closed 停止する。段5 author は起動しない。発効連言、v7、g12だけの部分実装も行わない。

## real / refuted

- real: 現行 formal producer/acceptance は各6 trialの `replicate_index=0` だけを受け、既存 judge が必要な exact `6×n` (`n>=2`) throughput observation blockを供給しない。
- real: reportに `fitness_tps` 候補は存在し得るが必須でなく、raw performance bytes、correctness、trace-disabled、外部issuer attestationへ独立束縛されていない。
- real: §5 validatorはH1/H2別値を正当に許す一方、既存 `judge` はscalar `_ContrastParams` 1個だけを両holdoutへ適用する。
- real: 3表のcreate-only transactionとacceptance receiptのexclusive-createは別transactionで、相互digest/transaction IDを持たない。
- real: `trial_registry` は6-report集約点だが supervisor からの直接callerではなくCLI consumer。artifact-flowとして「supervisor→acceptance」と読むかは追加裁定が要る。
- real: 現行 C07 evaluatorはjudge内部の3 entrypointだけを検査し、production callerを検出しない。
- refuted: throughput候補bytesがproduction reportに一切無い、という段2の強い一般化。`fitness_tps` は存在し得る。ただし上記authority不足によりblocker結論は変わらない。
- refuted: value gateだけ先行すると直ちにconsumerなしで発効可能になる、という説明。全12 predicate連言は残る。ただし単一変更単位を割るため先行landは不可。

## 採否とscope

- 採用: `section5_value_violations` 空集合の発効連言、commit blobからの§5再読、report側に永続化済み発効digestとの独立照合、既存judge/3表の再利用、v7/g12同一commitという方向。
- 不採用: report順をscheduleにする、G1/G2をn反復にする、bench wall秒をthroughputにする、consumerがattestationを自己発行する、H1/H2同値を仮定する、judgeを2回呼んでprivate結果を合成する。
- scope外: report/attempt schemaの拡張、judge params型のH別mapping化、§5同値規範化、新campaign orchestrator、3表/receiptの新transaction schema。ユーザー指示どおり実装しない。

## 追加裁定が必要な4点

1. supervisorはreport producer、registry CLIはproduction aggregate consumer、というartifact-flow解釈でよいか。直接callを要求するなら新orchestratorを許すか。
2. H1/H2別paramsを既存judgeへ渡すため、既存 `_ContrastParams` のholdout別mapping化と、§5で両holdout同値を要求する案のどちらを採るか。
3. exact `6×n` throughput rowsとraw-value attestationを、どの既存producerへversioned追加することを許すか。
4. canonical 3表output root、表digestとacceptance receiptの回復可能な束縛、receipt schema更新を許すか。

## 通る正例と禁止署名

- 通る正例: H1/H2それぞれの登録n個の独立replicateが、事前schedule row、raw throughput bytes、correctness pass、trace-disabled、外部issuer attestationへ束縛され、発効commitの対応paramsで1回の既存judgeを通り、exact 6 cellの独立3表がreceiptと同じtransaction identityへ束縛される。
- 禁止署名: report順/G1-G2/bench wall/consumer自己発行digestを正規authorityとして使う実装は不採用。既存judge複製、別schema、汎用workflow、scope外機構の先回りはしない。

## 変異

実装面差分ゼロで段5へ進まないため、変異事前登録・matrixは対象外。未実走を緑とは記録しない。
