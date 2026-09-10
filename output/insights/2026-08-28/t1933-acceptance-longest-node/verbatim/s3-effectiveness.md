## 総括

plan v2の「snapshot案は0 byte」「D104を再開しない」は妥当です。一方、「対象内に他の最大1原因がない」「固定4-node baselineがacceptance critical pathを代表する」という断定は成立していません。

現時点ではauthorへ進めず、実装面は0 byteを維持すべきです。ただし、T-080 cached baseを毎node全量複製する経路だけは未計測の実効候補です。完全な「候補なし」を主張して閉じるなら、この1点に限定した事前profileには価値があります。

本段ではWeb、書込み、test、profileを実行しておらず、新たな緑は報告しません。

## real findings

1. 判定: real — 固定baselineは同一条件A/Bには使えるが、acceptance critical pathの代表ではない。

   - 固定argvは4 nodeだけを`-n 0`で実行します。`baseline-argv.md:6`、`baseline-argv.md:7`、`baseline-argv.md:10`
   - 測定fieldは`effective scheduler=serial`、`4 passed / 147.55秒`です。`baseline-argv.md:18`
   - 一方、ledgerは17,639 nodeのduration mapですが、記録条件、worker配置、argv、commit、hostを持ちません。`acceptance_duration_ledger.json:2`、`acceptance_duration_ledger.json:17643`、`acceptance_duration_ledger.json:17645`
   - 差はfloor snapshotが79.0から4.18、T-080 snapshotが50.0から2.61、single-defectが55.0から86.57、draft-finalizeが53.0から51.93です。方向すら揃わないため、単純な倍率補正は不可能です。
   - 32-worker時にsnapshot wallが約42秒まで伸びる既存実測も、並行I/O感度を示しています。`test_s8b_floor_campaign.py:1645`、`test_s8b_floor_campaign.py:1646`

   効果帰結: 固定baselineから言えるのは「このserial sliceでの前後差」までです。acceptance全体の最長nodeやworker critical pathを短縮したとは証明できません。

2. 判定: real — plan v2はserial critical pathと最長nodeを混同しています。

   - `-n 0`では4 node全部が直列経路なので、snapshotの短縮も147.55秒のwallを短縮します。
   - ただしsnapshot 2 nodeを完全消去しても6.79秒、147.55秒の4.60%が絶対上限で、86.57秒の最長nodeの同一性は変わりません。実際の重複除去効果は6.79秒未満です。
   - acceptance並列実行では、最長nodeとworker critical pathは同義ではありません。ledgerにはworker鎖がありません。

   効果帰結: 「fixed slice wallには最大4.60%効く可能性がある」が正確であり、「critical pathに全く効かない」は強すぎます。一方、実益が小さいという結論は維持できます。

3. 判定: real — snapshot重複除去の安全な実装境界は見つからない。

   - floor対象nodeはoptimized/referenceを各4回呼びます。`test_s8b_floor_campaign.py:1739`、`test_s8b_floor_campaign.py:1740`、`test_s8b_floor_campaign.py:1750`、`test_s8b_floor_campaign.py:1762`
   - 両実装はそれぞれ規則を再取得します。`test_s8b_floor_campaign.py:1655`、`test_s8b_floor_campaign.py:1680`
   - T-080対象nodeも4回snapshotを取り、各回で規則を再取得します。`test_s8b_oracle_driver.py:567`、`test_s8b_oracle_driver.py:616`、`test_s8b_oracle_driver.py:626`、`test_s8b_oracle_driver.py:633`
   - optimized/reference間の値源共有とlive再観測省略は禁止されています。`authority-v2.md:23`

   効果帰結: 計測可能な上限は6.79秒ですが、安全条件を守った具体案の上限は0秒です。snapshot面は0 byteが妥当です。

4. 判定: real — D104とは別の未反証コストが直接helperに1件残っています。

   - `_t080_stub_free_e2e_repo()`はcache済みbaseであっても、呼出しごとに36MB、約2300 fileのrepoを`shutil.copytree`で全量複製します。`test_s8b_oracle_driver.py:895`、`test_s8b_oracle_driver.py:925`、`test_s8b_oracle_driver.py:926`
   - 86.57秒nodeと51.93秒nodeはいずれもこのhelperを1回呼びます。`test_s8b_oracle_driver.py:1372`、`test_s8b_oracle_driver.py:1473`
   - helperには合計11 consumer nodeがあります。`test_s8b_oracle_driver.py:938`、`test_s8b_oracle_driver.py:1006`
   - 別inodeかつcopy-on-writeのcloneなら、破壊的変異を独立実体へ隔離する要件と両立する余地があります。hardlinkはbaseを汚し得るため不適格です。独立実体要件は`test_s8b_oracle_driver.py:902`、`test_s8b_oracle_driver.py:903`です。

   効果帰結: これはworker/session cache、variant統合、correctness値源共有ではなく、D104の再開には当たりません。ただし`:926`単独のdurationが測られておらず、filesystemがreflinkを支える保証もないため、現時点で実益はrealと判定できません。「候補なし」というplan v2の断定だけが未証明です。

5. 判定: real — T-1933を「最長短縮の完了」と呼ぶことはできません。

   - global最長はscope外140秒、次もscope外94秒です。`acceptance_duration_ledger.json:8185`、`acceptance_duration_ledger.json:4374`
   - scope内ledger値はfloor snapshot 79秒、single-defect 55秒です。`acceptance_duration_ledger.json:11766`、`acceptance_duration_ledger.json:12460`
   - 0 byteではどのdurationも短縮していません。親brief自身も不成立時の0 byte終了を別成果として認めています。`brief.md:17`

   効果帰結: 完了名称は「scope内で安全かつ実効的な短縮案なし、0 byteで調査終了」とすべきです。「acceptance最長短縮完了」「DW-G05達成」は不正確です。

## refuted findings

1. 判定: refuted — ledgerの79/55秒を現行実装の効果gateへ直接使える。

   固定baselineと条件が一致せず、ledgerにも条件metadataがありません。ledgerは候補抽出と全体順位の参考には使えますが、前後効果の基準にはできません。

2. 判定: refuted — 固定baselineが無価値である。

   request `954274.nqsv`、outcome=`child`、rc=0、scheduler=`serial`という明確な測定fieldがあり、同じ固定argvによる局所A/Bには最も強い基準です。`baseline-argv.md:17`、`baseline-argv.md:18`

3. 判定: refuted — snapshot重複除去でglobal最長が下がる。

   snapshot 2 nodeを完全消去してもscope外140秒と94秒が残ります。global最長値への直接効果は0秒です。

4. 判定: refuted — 86.57/51.93秒へ効くにはD104を再開するしかない。

   `test_s8b_oracle_driver.py:926`の全量cloneは未反証です。ただし効果量未計測なので、これを根拠に直ちに実装へ進むこともrefutedです。

5. 判定: refuted — 追加のfull acceptance A/Bを実装前に行う必要がある。

   B実装がない段階ではA/Bになりません。またglobal最長がscope外なので、full acceptance再走は現在の実装可否を決めません。必要なのは最大でも`:926`の局所cost attributionです。

## 効果判定

| 候補 | fixed sliceへの効果 | global最長への効果 | 判定 |
|---|---:|---:|---|
| snapshot rules共有 | 6.79秒未満、4.60%未満 | 0秒 | 安全境界不成立、0 byte |
| D104 cache、variant統合 | 過去A/Bで改善不成立 | 不明 | 禁止、0 byte |
| cached base全量cloneのCoW化 | 未計測、86.57/51.93秒双方に作用可能 | 直接は0秒 | 未反証、実装前profileのみ価値あり |
| T-1933を最長短縮として完了 | 短縮なし | 短縮なし | 不成立 |

## 推奨裁定

現時点ではauthorへ進めず、実装面0 byteを維持してください。ただしplan v2の理由は「候補が存在しない」ではなく、「snapshot案は安全性と効果gateを通らず、T-080 clone案は実益未証明」と修正すべきです。

完全に閉じる前の追加作業を1件だけ許すなら、`test_s8b_oracle_driver.py:926`について、cache miss build、cached base clone、clone後の`verify_receipt`群を分離する局所profileが妥当です。本段のbaselineや緑には数えず、source instrumentationなしで実施し、cloneが事前に定めた実益閾値を安定して超えた場合だけD95 authorへ渡します。超えない、またはCoW非対応なら直ちに0 byteで終了します。

snapshot profile、D104再試行、full acceptance A/Bは追加コストに見合いません。T-1933の終了記録は「scope内negative result」であり、「最長短縮達成」ではありません。
