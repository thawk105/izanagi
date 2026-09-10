## 所見一覧

1. **§5.2を実装根拠とする brief の解釈** `[unclear / major]`

   - 主張: §5.2が本 wave の4面実装を明示している。
   - 根拠: preregistration §5.2 は「実装は本 wave の scope 外」と明記し、全層横断の申し送りとしている（155-180行）。§5.3、末尾総括も実装・実走を将来 waveへ送っている。一方、D603/D614は後続の Wave D 自体を許している。
   - 判定: D603/D614による再スコープなら成立するが、§5.2単独は実装許可の根拠にならない。briefの引用は曖昧。

2. **「6条件のうち1つも成立しない」というP1前提** `[refuted / major]`

   - 主張: 本 wave後も6条件は全て未成立である。
   - 根拠: ITTは§4.1で既に解析規約として固定され、既存テスト `test_m9_post_treatment_failure_remains_in_denominator` も分母維持を検査する。`_load_adjudication` には verdict freeze、hash、bijection 検査もある（5159-5410行）。ただし独立custodian、provider cache、実価格、power lock、task-specific oracle等は未成立。
   - 判定: 「confirmatory gateが全て未達」はrealだが、「何も成立しない」は過大。装置の既存部分と実験前提を混同している。

3. **累積複雑化と実利用見込み不足** `[real / major]`

   - 主張: Wave A→B→C→Dの累積コストに対し、T-189着手の見込みをbriefは示していない。
   - 根拠: §5.3のreplayer、task catalog、独立oracle、cache、price、custodianは全て未実装。さらに今回の対象は約797行相当の5面（5085-5158、5441-5699、5898-6266、6298-6392）にまたがる。
   - 判定: 「すぐ使われる」根拠がないため、規律5に基づく差し戻し論はreal。単なる設計メモに留めるべきかは未裁定。

4. **既存のWave A基盤を配線する便益** `[refuted / minor]`

   - 主張: 未実装なら将来また同じ調査を要する。
   - 根拠: `validate_nullable_dimensions`、`normalize_schedule`、`expected_schedule_from_manifest` は既存実装・テスト済みだが、live `_validate_schedule` から未接続（2305-2441行）。配線すれば既存基盤を再利用できる。
   - 判定: 「止める理由が乏しい」という強い主張はrefuted。ただし、実際のconsumerや着手時期がないため、実装便益の大きさまでは証明されていない。

5. **DW-G04が「該当なし」というbriefの判断** `[real / major]`

   - 主張: 既存fieldの実路配線なので、新しい条件付き機能ではない。
   - 根拠: 現在はnullable検査がlive pathで発火しておらず、v3欠落fieldやnon-null cache/priceを新たにfail-closedする予定。これは受理集合を変える新しい実効gateである。
   - 判定: G04を無条件に除外する根拠は弱い。少なくとも発火条件と、`inconclusive`へ落とす境界を明示すべき。

6. **power simulationを実装してしまう越境** `[refuted / minor]`

   - 根拠: planはdynamic countをscheduleから読むだけで、`N_positive_min`、`N_negative_min`、power simulationを追加していない。
   - 判定: 越境なし。ただしschedule自身から件数を導くため、低powerを検出できない危険は残る。

7. **独立custodian実現方式への越境** `[refuted / minor]`

   - 根拠: `make_packets`と`_load_adjudication`の `same-owner-advisory` を維持し、別UID、ACL、handoffは追加しない。
   - 判定: 越境なし。独立blindを実現したとは主張できない。

8. **provider cache制御・実測への越境** `[refuted / minor]`

   - 根拠: `validate_nullable_dimensions` はnon-null cacheを拒否し、`_codex_exec_argv`にもcache制御引数はない（2305-2347、3255-3290行）。
   - 判定: 越境なし。schemaが `cache_condition` を持つことはcacheを制御・実測することではない。

9. **stage2/5 downstream replayerへの越境** `[refuted / minor]`

   - 根拠: planにreplayer、fix pass、downstream pin、acceptance判定の実装はない。
   - 判定: 越境なし。§12.3のfix gateは将来も `inconclusive` のまま。

10. **task catalog実データ・独立分類者への越境** `[refuted / minor]`

    - 根拠: `TASK_MANIFEST`の構造利用とsynthetic alpha/beta fixtureだけで、実task catalogや独立分類者2名は追加しない。
    - 判定: 越境なし。manifest schemaの一般化は分類者確保ではない。

11. **price snapshot実データ取得への越境** `[refuted / minor]`

    - 根拠: `price_version`はnull専用のままで、公式原表、SKU、取得コマンド、hashは追加しない。
    - 判定: 越境なし。

12. **T-189のpair意味論をarm次元で表現する誤り** `[real / blocker]`

    - 主張: 固定max/highをschedule由来の2つのarmへ一般化すればよい。
    - 根拠: preregistration §6.3では `arm` はreasoning effortであり、modelではない（311-312行）。同一task/stageのpairは、同じeffortで `requested_model` がsol/lunaの2 slotになる（286-320行）。planはblock内のarm集合を「2つのarm」として検査するため、正しい `arm=max`、modelだけ異なるpairを拒否し得る。
    - 判定: requested_modelを軸に追加するだけでは不十分。ここはT-189を実際に受理できないblocker。

13. **task-specific oracleの実効閉包不足** `[real / blocker]`

    - 主張: `_load_adjudication`はtask非依存なので変更不要。
    - 根拠: preregistration §5.3はtask-specific oracleのhash・件数を `_validate_schedule`、`_load_adjudication`、`_aggregate_verified` 全体で束縛するよう要求している（201-205行）。しかし現行 `_validate_verdict_row` はglobal `KNOWN_FINDINGS`を参照し（6446-6448行）、planはこれを変更しない。`task_manifest`をaggregateに渡しても、blindなverdict append/load段階には伝播しない。
    - 判定: 新task固有のfinding IDを実live経路で受理できない可能性があり、planの「task汎用化」は見た目だけになる。

14. **`routing_evidence_status`を計算する実体がない** `[real / blocker]`

    - 主張: axis ledgerとdecision dictが将来の3値判定に使える。
    - 根拠: repo内に `routing_evidence_status`、`apparatus_diagnostic`、`confirmatory-go`、`confirmatory-no-go` の実装はない。現行decisionは `POS_PRIMARY` / `NEG_ADJUDICATED_FALSE_FINDING` のままで、planも旧projectionを維持する（5515-5688行）。
    - 判定: raw observation ledgerとしては有用だが、§12.1/§12.3の判定器ではない。将来6項目が埋まっても、このplanだけでは3値を計算できない。

15. **cache未制御resourceの報告抑止不足** `[real / major]`

    - 主張: cache軸をresource ledgerに追加すれば将来利用できる。
    - 根拠: §12.3はcache gate未達時のtoken/wallを `not-applicable` と明記している（629-631行）。planは `cache_condition`をresourceへ運ぶが、cache gate判定も抑止も定義していない。現行token集計は単純に数値を合計する（5441-5512行）。
    - 判定: null cacheを持つapparatus diagnosticの数値が、resource比較結果に見える危険がある。

16. **既存fixtureへの波及「なし」は楽観的** `[unclear / major]`

    - 主張: legacy projectionを維持すれば既存nodeidの期待値変更はない。
    - 根拠: `_schedule`（320-348行）はschema_version、requested_model、cache/priceを持たない。現行normalizerはschema_version欠落を拒否するため、`_validate_schedule`側のv2推定が必須。`_aggregate_rows`（6609-6670行）はcase/armだけで、axis helperのfallbackが必須。さらに `test_replay_passes_schedule_requested_model_to_collect_run` のfake validator（6018行）は引数1個しか受けず、`task_manifest=`を内部転送すると壊れる。`make_packets`のcustodian fixtureはscheduleなしで、fallbackも必要。
    - 判定: 互換性は実装上の条件であり、現時点で「なし」と確認済みではない。pytestは未実走。

17. **単一実装単位の規模見積もり** `[real / major]`

    - 主張: 4面は相互依存するため分割不要。
    - 根拠: Wave C実績は `tools` 37行、tests 398行の変更だった。一方今回の対象関数本体は約797行に及び、新規テスト案は12 nodeid。schedule正常化、pair意味論、replay、aggregate、packet blindを同時に変える。
    - 判定: helper共有のため無秩序な並列分割は危険だが、「Wave C前例だから単一workerで安全」は成り立たない。少なくともschedule互換層と集計/replay層の逐次checkpointが必要な規模。

18. **DW-G05の機能影響** `[refuted / minor]`

    - 根拠: 指定の `grep -rln` と追加のsymbol検索では、実運用の呼出しは同ファイルのCLIと `orchestrator/tests/test_codex_reasoning_ab.py` のテストに限られる。`tools/check_ai_provenance.py`、hooks、docsは文字列・記録であり、`orchestrator/campaign/s8b_*`の `verify_manifest` は別実装。
    - 判定: certified選択、proof chain、通常の試行台帳への機能的consumerがないというbriefの主張は支持される。ただし、将来再調査コストは推測であり、緊急性の根拠にはならない。

## (P1) 実装可否への結論

- 「6条件が全て未成立なので必ず実装しない」: **refuted**。ITT、既存oracle freeze、Wave Aの汎用基盤は既に存在するため、前提は過大。ただしconfirmatory証拠が成立しない点はreal。
- 「A→B→C累積で、利用見込みがないため設計メモに戻す」: **real**。新しいconsumer、T-189開始条件、担当waveがbriefにないため、規律5上の反論は成立する。
- 「既存汎用層があるので止める理由は乏しい」: **refuted**。再利用便益は実在するが、現在の機能的consumerがなく、便益が実装コストを上回る証拠にはなっていない。
- **総合判定は `unclear / major`。** planの「装置面は実装する」という結論には無条件では同意しない。装置をapparatus diagnostic専用として進める余地はあるが、pair意味論、task oracle、cache resource抑止、将来statusの計算閉包が未解決である。

## brief への異議

あり。

- §5.2本文の「実装は本 wave の scope 外」と、4面を本waveの明示実装項目とするbriefの説明が一致していない。
- 「6条件が一つも成立しない」は、ITTや既存freezeまで未成立と数えるなら不正確。
- DW-G04を該当なしとしたが、normalizerをlive pathへ接続することで受理集合が変わる。
- DW-G05の「再調査コスト」は推測であり、機能影響なしという主張とは分けるべき。

## plan への異議

あり。

- `arm`を2値から動的化する設計は、modelをrequested_model、armをreasoning effortとするT-189 schemaに合わない。
- `_load_adjudication`を無変更にすると、task-specific finding ID・oracle hash・件数のlive検査が閉じない。
- `routing_evidence_status`や`apparatus_diagnostic`を出力する実装がなく、旧decision labelだけが残る。
- cache未制御時のtoken/wallを `not-applicable` にする処理がない。
- legacy schedule、direct aggregate fixture、monkeypatch fixtureを通す互換契約がfile:lineで不足している。
- 4面約797行と12件の新規テストを単一実装単位にする判断は、Wave C前例だけでは裏付け不足。

## 総括

最重要blockerは、planのblock検査がreasoning effortの2 armを要求し、同一effortでsol/lunaを比較するT-189 pairを正しく表現できない点である。  
次のblockerは、task-specific oracleをaggregate後だけで扱い、verdict validatorと`_load_adjudication`のglobal `KNOWN_FINDINGS`を残す点である。  
axis ledgerはraw apparatus dataとしては意味があるが、§12の3値statusやcache `not-applicable`を計算する成果物ではない。  
6つのscope外項目への実装越境は静的には見つからず、schema受理と実際の制御・実測は分離されている。  
P1の「絶対に実装しない」は過剰だが、現planの無条件実装も、規模・利用見込み・実効性の点で支持不十分である。  
編集とpytest実走は行っておらず、以上は指定資料と現行コード・fixtureの静的検査結果である。