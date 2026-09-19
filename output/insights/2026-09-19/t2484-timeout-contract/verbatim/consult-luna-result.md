## 総括

**GO（実装着手）。must-fixなし。** P1は既存拒否を維持したまま成立する。局所helper、3 caller、早期診断、DW-M06/M07更新で閉じられ、新gate・区間監視・schema追加は不要。P=180秒の実測妥当性と終端回収は、親の検証事項として残る。

**must**

なし。planは既に絶対保証を否定しており、静的確認で成果物の受理・参照・検査回収を壊す未対処の欠陥は特定できなかった。

**should**

- **180秒を「前段Pの根拠ある上限」と扱わない。**
  対象：[plan-result.md:33](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2484-timeout-contract/plan-result.md:33)、`tools/pegasus/dispatch_compute.py:4200,4232,4245`。
  再現例：Q直前の観測後、sleep＋qstatを挟んでRUNを初観測すると、その時刻からW＋Gへ期限が再設定される。回収期限もEND観測後から始まる。したがって180秒には前段以外の遅れも含まれる。
  最小処置：180秒は「前段と観測・終端処理の運用余裕」と説明する。15.9秒から導出済み、全条件で先行発火ゼロ、hold消滅とは記さない。新しい監視機構は不要。

- **検証の組合せを膨らませない。**
  対象：[plan-result.md:43](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2484-timeout-contract/plan-result.md:43)、同:54。
  再現例：Q/W/G/A/Cの各欠落を全caller・全override条件で交差させても、同じ予算算術の欠落を重複検出する。
  最小処置：予算算術の境界と各callerの配線を分け、経路差があるcollectionのW、dispatch hang、local hangを押さえる。変異はplanどおり選択nodeへ絞り、F33の完全一致を維持する。

**nit**

- [brief.md:5](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2484-timeout-contract/brief.md:5)の「全区間を覆う」は、単独引用すると上限保証に読める。
  再現例：式だけを成果insightへ転記し「dispatcherより先に切れない」と結論する。
  最小処置：「全区間を計上した運用予算」と補足する。承認済み(a-1)+(a-3)の再択一は不要。

**refuted（攻撃して成立しなかった懸念）**

- **「max補正は必ずcollectionの受理集合を広げる」：refuted。**
  `tools/mutation_harness.py:1451,1524`。Q/G=1800/600、spec=2399なら、gateへ元値を渡す限り従来どおり拒否される。max後の値を渡す変更だけがF891/F932を壊す。既存テスト`test_t2337_dispatch_timeout_overrides.py:138`がその境界を固定している。

- **「Wは3600固定にすればさらに削れる」：refuted。**
  `tools/run_tests.py:1343`、`tools/pegasus/dispatch_compute.py:507`。override=`02:00:00`は転送・解釈されるため、実行側を3600固定にすると予算を3600秒過小評価する。反対にcollectionはoverrideを転送しないため、両経路の区別は必要。

- **「dispatch hang値を外すならhold処理も削れる」：refuted。**
  `tools/mutation_harness.py:1994`、`orchestrator/tests/test_mutation_harness.py:1842`。有限の外側timeoutは残る。発火時の変異残置・hold・後続停止は引き続き必要で、F185/F901対策として削除できない。

静的確認のみ。編集・commit・子起動・pytest実行は行っていない。