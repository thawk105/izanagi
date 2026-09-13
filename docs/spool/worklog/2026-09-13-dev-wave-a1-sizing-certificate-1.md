---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-13
wave: dev-wave-a1-sizing-certificate
seq: 1
title: [T-2164] A-1 balanced5のsizing証明書を凍結値で作り、本走policyを凍結した
---

## 本文

- 凍結済みの道具へ事前登録§5.4/§5.5の値だけを渡し、pilot attempt-0004からsizing証明書を作って
  別実装で再現した。status=selected、3 workloadとも最小の実現候補n=30をorder_index 0で選び、
  認証は1回目で通った。pilotから取ったのは散らばりとbaseline水準だけで、差の符号も大きさも
  取っていない。道具の式・確率・候補・種の定義域・停止規則は1 byteも変えていない。
- D1452のconsumer側照合を実装した。証明書は既に申告値を記録していたが、突き合わせる側が無かった。
  段3の敵対相談が反例を構成した — 候補上限を4096から4095へ書き替えても実現候補列は変わらず
  選ばれるnも変わらないので、既存consumerも再現側も通る。決定は{{D:a1-sized-policy-freeze}}。
- 段2のプランが実装前に実欠陥を見つけ、親が独立に再現した。証明書のplanned_sigma_tpsは
  .17gの十進文字列で、JSON数値へ落とすとDecimal(str(float))が別の値になる。現行consumerは
  sizedのkとplanned_sigma_tpsに数値を要求していたため、本番の証明書と一致するpolicyを書けなかった。
- 段3が本走policyのbytes pinの不在を出した。_policy_identityがsizedにだけNoneを返しており、
  pilotとv2にあるpinが発火しない。既存機構の対称化で塞いだ。新しいgateは作っていない。
- authority.formalはfalseのままにした。これは選択ではない。identとwalがsized studyを
  非認証laneのexact identity集合に持ち、両方が独立にformal is Falseを要求する。
- 実装子の初回は親の焦点走で79赤 (failed 6 / errors 73)。全件がsizing_inputs.pilot_resultの
  key集合が6個という単一原因に帰着し、既存テストの赤は0件だった。fix後282 passed / rc=0。
  テスト関数は124→133で削除・skip・xfailの追加なし。
- 段6レビューaはmust-fix 0。レビューbは事前登録本文の逐語照合で転記不一致0件、must-fix 2件は
  いずれも本文の言い過ぎ (result_authorityが「実装のどこからも読まれない」という断言、
  感度分析の独立性仮定の欠落)。数値は変えずに文言を直した。
- 段4で登録した変異M1は、段6レビューが「凍結済みの正しい証明書を読む正例が先に落ちるので
  負例による単独killにならない」と指摘したため、項の削除へ再照準した。観測後の訂正として記録する。
- 変異は記録前のanchor commitに対してprobeで観測nodeを集め、完全集合として固定した本走で
  5件すべてKILLED・期待node完全一致、baseline PASSED。
- 親がbriefに書いた「本番値でも数分」という所要時間の外挿は誤りだった。実際は0.36秒で、
  3 workloadとも候補1件で停止したためである。試行回数に単純比例しない。
- **本走は投入していない。** 正式測定の認可は[T-1505]により人間手番のままである。
  計測経路にはpilot専用の分岐が残っており、policyの受理完了は本走が起動可能になったことを
  意味しない。この未整備は新規項目として登録する。
- 成果物 = output/insights/2026-09-13/paper-story-a1-balanced5-sized-preregistration/ (事前登録・証明書・受領証)、
  orchestrator/campaign/paper_story_a1_paired.v3-sized.json (機械可読の正本)、
  output/insights/2026-09-13/t2164-a1-sized-policy/ (実装・相談・レビュー・変異の記録)。
- スキル自己改善の候補は段8で一度だけ裁定する。改善実装・次wave起動・pushは行わない。

## 次の一手差分

### 完了

- [T-2164] 反復数を決める道具の受理範囲をconsumerが事前登録の値とexact照合する形で閉じた。
  照合5項目の負例は変異で単独killを確認した。
  remaining: none
  base: f7b0077f2f4ec33033328a805277f4e52ea9ed105a60c1ac3b571e0fc61e1988

### 新規

- {{T:a1-sized-execution-path}} **P2・新規**: A-1 balanced5の本走を実行できるように、
  計測経路に残るpilot専用の分岐を一式で揃える。source契約がpilotのattemptを無条件に要求する点、
  hydrate入力とstagingの分岐、source bindingの生成箇所、amended buildのconfigure argvの受理形が
  対象である。1箇所だけの限定解除では足りないことを段3が数え上げた。
  正式測定の認可は[T-1505]により人間手番のままであり、本項目は認可の代替ではない。
