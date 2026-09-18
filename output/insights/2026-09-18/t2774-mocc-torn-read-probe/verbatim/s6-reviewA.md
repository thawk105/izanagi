## 判定と確認範囲

**GO。ただし、観測結果の記録としてのGOです。原因識別・診断patchの効果確認には到達していません。** 現物のpatchと再分類後の集計に、今回の成果物を誤らせる未修正のmust-fixは見つかりませんでした。

指定資料を読み、Q1の112走、Q2の200走、smokeの2走を確認しました。各 `run.json` とブロックの `result.json` は一致し、保存されたverifier結果から再分類・再集計した値も両summaryと一致しました。pytest・build・benchmarkの再実行、ファイルへの書込みは行っていません。

以下、`J/` は指定job directory、`M:行` は `J/verbatim/mocc-transaction-e9e477ca.cc`、`I:行` は `J/verbatim/instr-applied/cc/mocc/transaction.cc`、`runner:行` は `J/probe/t2774_probe.py` を指します。

## must-fix

**なし。**

ただし、次の二点は既に解消された問題として明記する必要があります。

- Q1は段4追記2どおり、`BACK_OFF=1` の副次観測です。Q2と合算して主解析にできません。
- Q2原本の75走に残る `failure` は旧runnerの分類誤りです。現行summaryは保存済みverifier結果から `indeterminate` へ再分類しており、この訂正は妥当です。

## should

**S1 — plain armの「検出率」と「判定確定率」を区別してinsightへ記載する。**

- **根拠:** [summary-q2.json](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2774-mocc-torn-read-probe/arm-B/summary-q2.json:4)、runner:185–215。`p058-plain` は38走、`e9-plain-nowit` は37走が `indeterminate`。`m=40` は「有効なverifier応答数」であり、全走の直列化可能性が確定したという意味ではありません。
- **放置時の影響:** 2/40・3/40を通常の確定判定に基づく率と同一視したり、`k_over_decisive_m=1` を再現率100%と誤読したりします。
- **是正案:** plain armは「全40走中のG2 signal検出数」と記し、indeterminate数を併記してください。原本からsummaryへの75件の再分類も記録し、旧原本を訂正後の分類と混在させないでください。

**S2 — 「識別未到達」と「診断効果未確認」を主判定に含める。**

- **根拠:** summary-q2.json:112–181、runner:318–339。witness onの2 armはともに0/40。G2の7走はすべてwitness offで、discriminatorは全200走で `not-run`、comparisonは0件です。
- **放置時の影響:** 診断前から未再現だった結果を「診断でG2が消えた」、識別未実行を「supported」またはdiscriminatorの「no-g2」と誤記します。
- **是正案:** 「witness有効条件でG2を得られず、payload-lineage識別には未到達。診断armと同時対照の検出数差は0」と明記してください。

**S3 — cold abortの適応挙動と曝露量を、診断の解釈に含める。**

- **根拠:** [診断patch](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2774-mocc-torn-read-probe/probe/mocc-close-version-counter-gap.patch:8)、M:364、915–978、1069–1077。追加cold abortはread-set登録前に戻るため、その対象readは `construct_RLL()` の温度更新・失敗read登録を受けません。
- **放置時の影響:** 二つの局所検査だけの効果として率差を解釈し、再試行・温度・lock経路の変化を取り落とします。
- **是正案:** 「固定した既存観測に対するattempt単位の追加拒否」と限定してください。Q2の総commit数も、instr-wit **21,664,020**、diag-wit **21,722,599**と併記できます。実行全体のcommit数が単調に減るという主張は、実測とも一致しません。

## nit

**N1 — runnerの一般化には、今回未発火の集計境界がある。**

- **根拠:** runner:131、190–195、469、555。正の `total_cycles` を現象名の検査なしに `g2` と呼び、Nは `planned_runs` ではなく保存済みrun数から作ります。
- **放置時の影響:** 今回は全7 anomalyがG2、全予定走が完了しているため、成果物は変わりません。別実験ではG0/G1cの誤標識、未開始走の分母脱落が起こり得ます。
- **是正案:** 今回の被覆限界として記録してください。再利用する場合に、cycleとG2の区別、未開始走の分母規則を定義すれば十分です。

**N2 — discriminatorには、現行verifierのrc=3との既存不整合が残る。**

- **根拠:** `mocc_g2_discriminator.py:453–461` はindeterminateに `serializable=False` を要求しますが、`model.py:503–519` の非空・acyclic・unclean結果は `serializable=True` です。
- **放置時の影響:** 今回はcycle正の走だけを呼出対象にするため、集計・識別結果は変わりません。該当rc=3入力を直接渡す場合は、blockerによる `indeterminate` に届く前に入力拒否になります。
- **是正案:** 今回のrunner修正でdiscriminatorを緩めず、到達範囲の注記に留めてください。

## 診断patchの正しさとintegrity

**追加拒否として妥当です。**

- cold側はbody copy後、既存の版再読前にcounterを検査し、`W_LOCKED` ならabortします。retryや新しい成功分岐はありません（patch:8–17）。
- validation側は既存の版比較・counter検査を残し、その後の版再読が異なれば `failed_verification_` を立ててabortします（patch:22–35）。
- ただし、追加loadによる実行時刻の変化まで含めた全実行間のcommit集合包含は証明しません。counter検査後に始まるwriterも含め、あらゆる競合を排除するpatchという意味ではありません。

基準sourceに2 hunkをメモリ上で適用し、既存の全1352行（`#line` 指令を除く）が**元の論理行番号のまま保存される**ことを確認しました。既存の `#if TRACE`、stamp、emissionは変更されていません。追加の `#line 350`／`#line 1038` も適切です。

再構成した診断sourceのSHA256は次の値で、Q2の4ブロックすべてのbindingと一致しました。

`1c5da7c8439144d02621071622e5eba31f1ff583c4fbda5efdfe7483c2c3168a`

integrityの実測は次のとおりです。

| 対象 | clean | lock / permutation / write-intent違反 |
|---|---:|---:|
| Q1 instr、diag | 各56/56 | 全走0 / 0 / 0 |
| Q2 instr-nowit、instr-wit、diag-wit | 各40/40 | 全走0 / 0 / 0 |
| Q2 p058-plain、e9-plain-nowit | 各0/40 | 全走0 / 0 / 0 |
| smoke instr、diag | 各1/1 | 全走0 / 0 / 0 |

plainのuncleanは、違反カウンタ0と矛盾しません。現行gateはX/P emitterのsource evidenceも要求します（`model.py:77–82,450–467`）。また、**write-intent違反0はI計装の被覆実証ではありません**。X/Pの存在条件とIの存在は別です。

## 分類・集計の検算

`classify` のrc対応は現行modelと整合します（runner:94–134）。

| rc | verdict | certified / serializable | runner分類 |
|---|---|---|---|
| 0 | serializable | true / true | no-g2 |
| 1 | non-serializable | false / false | g2 |
| 3 | indeterminate | false / true | indeterminate |

aggregate三カウンタ、cycle数、報告anomaly数との整合を検査しています。G2のrc=1を失敗へ落とさず、discriminator未実行・識別不能とも分離しています。timeout、空trace指定、benchmark失敗、不正JSON、rc不整合は `failure` です。rc=3自体は失敗ではありません。

`discriminator_result` は終了rc=0、stdoutとJSONの結論一致、schema、blockers/comparisonsの型を確認します。非ゼロ終了や結果不整合は `input-rejected` です。timeout等もこの分類に入り、詳細はprocess記録で区別されます。結論の意味論をrunnerで再実装するものではありません。

runnerは両CLIを呼び、raw出力を分類しています（runner:306–316、330–339）。対象のverifier/discriminatorについて、`git diff main...HEAD` と対象ファイルの対HEAD差分は空でした。**規律2に反する受理集合変更は確認されません。**

再計算結果は以下です。Q2は全armでN=m=40、failure=0です。

| Q2 arm | k | indeterminate | decisive_m | k/m | 両側CP95% | k/decisive_m | 全投入の識別範囲 |
|---|---:|---:|---:|---:|---|---:|---|
| p058-plain | 2 | 38 | 2 | 5.0% | [0.611%, 16.920%] | 100% | [5.0%, 100%] |
| e9-plain-nowit | 3 | 37 | 3 | 7.5% | [1.574%, 20.386%] | 100% | [7.5%, 100%] |
| e9-instr-nowit | 2 | 0 | 40 | 5.0% | [0.611%, 16.920%] | 5.0% | [5.0%, 5.0%] |
| e9-instr-wit | 0 | 0 | 40 | 0% | [0%, 8.810%] | 0% | [0%, 0%] |
| e9-diag-wit | 0 | 0 | 40 | 0% | [0%, 8.810%] | 0% | [0%, 0%] |

ここでCP区間は、独立Bernoulliを仮定した**検出signalの率**に対するものです。plain armのindeterminateを認証済みno-g2に変換する区間ではありません。`all_submitted_rate_bounds` は未確定走を両端に割り振る標本内の識別範囲で、母集団率の信頼区間とは別です。

CP実装は、下限で \(P_p(X\ge k)=0.025\)、上限で \(P_p(X\le k)=0.025\) を反転しており、向き・端点処理とも正しいです。別実装の二項係数による直接和でも照合し、最大差は約 \(5.6\times10^{-16}\) でした。

**名指しすべき原本との差は75件の分類訂正です。**

| arm | 保存原本 | 再分類後summary |
|---|---|---|
| p058-plain | failure=38、m=2、k=2 | failure=0、indeterminate=38、m=40、k=2 |
| e9-plain-nowit | failure=37、m=3、k=3 | failure=0、indeterminate=37、m=40、k=3 |

ブロック別の訂正数はQ1/Q2/Q3/Q4で **19/19/20/17**。summaryの `inputs.status_changes` と一致します。summary入力のSHA256も全件一致しました。

Q1は両armともN=m=decisive_m=56、k=0、CP95%=[0, 0.0637501]。smokeは各0/1で、Q1の分母には含まれていません。

discriminatorはQ1各56件、Q2各40件がすべて `not-run`。四結論・入力拒否・comparisonsはすべて0件です。識別率はQ2の先頭3 armで0/2、0/3、0/2、witness onの2 armでは分母0のためnullです。これは計器の識別性能0%を測った結果ではありません。

## P1の被覆境界と今回のanomaly

歴史的5件（`J/verbatim/t1892-results.md:110–126`）と同様に、今回の**7走・7 cycleもすべて長さ2、両辺rw、別thid、同epoch、commit tid差1**でした。各走の `total_cycles=anomaly_count=1` で、報告打切りはありません。

次表のrunは `J/arm-B/<block>/runs/<run>/`。形は `verifier.json`、thidとcommit版は記載したraw C行から確認しました。

| block / run | cycle txid | thid | commit版 | C行：traceファイル番号:行 |
|---|---|---|---|---|
| Q1 / 010-p058-plain | 340513, 340514 | 7, 4 | (33,112), (33,113) | 7:110777、4:175292 |
| Q2 / 040-e9-plain-nowit | 748934, 748936 | 33, 16 | (69,37), (69,38) | 33:375739、16:325289 |
| Q3 / 036-e9-instr-nowit | 424162, 424163 | 28, 37 | (46,67), (46,68) | 28:244507、37:32160 |
| Q4 / 032-e9-instr-nowit | 182647, 182648 | 9, 2 | (20,328), (20,329) | 9:81858、2:114555 |
| Q4 / 040-e9-plain-nowit | 370499, 370500 | 11, 9 | (36,530), (36,531) | 11:14060、9:40724 |
| Q4 / 043-p058-plain | 676564, 676565 | 25, 29 | (62,137), (62,138) | 25:347704、29:474592 |
| Q4 / 044-e9-plain-nowit | 88887, 88888 | 24, 13 | (9,1219), (9,1220) | 24:55385、13:58578 |

今回は各辺のrw reasonが1本ずつ、計14本でした。歴史的ordinal 32には一辺に2 reasonがあり、この細部は同一ではありません。また、上表の「tid差1」は**cycle内の二つのcommit版**についてです。reader版とoverwriter版の差がすべて1という意味ではありません。

P1の存在例は引き続き成立します。ただし、cold・RLL空・別keyへの交差read/write、Wのy検査がRのy施錠より先、Rのx版検査とcounter検査の間にWがpublish/unlockする、という前提付きです（M:280–354、989–1038）。

`max_rset_` は再取得版を最大値に取り込むだけで再検証しません。その他の最大版・直前commit版・epochが上回らなければtid差1になり得ます（M:1038、1118–1131）。**今回の形の一致はこの存在例と整合しますが、cold/RLL状態や二つのload間の順序を観測した証拠ではありません。**

## producer差・観測者効果・結論の上限

Q2の鎖は **2/40 → 3/40 → 2/40 → 0/40 → 0/40** です。

| 変更段 | 観測から言えること | 言えないこと |
|---|---|---|
| p058 → e9、witness off | signalは両producerで再現 | producer差が無影響、環境が同等 |
| X/P追加 | 3/40から2/40。追加後もG2再現 | X/Pがraceを抑制すると確定 |
| witness on | 2/40から0/40 | 抑制効果・S行単独の因果効果が確定 |
| 診断patch追加 | 0/40から0/40 | 診断で率が下がった、必要性を確認 |

静的には観測者効果の候補があります。

- witnessのS出力はpublishとunlockの間です（M:1195–1207、I:1260–1272）。P1が要求する「readerの二観測間にwriterがpublishとunlockを完了する」配置を変え得ます。
- witnessはS出力だけでなく、L出力、stampの書込み・decodeも追加します（M:68–110、1134–1199）。今回のon/off比較はこれらをまとめた介入です。
- X計装はwritePhase入口、write直前、publish直前の3検査点、P計装はsort前後の集合検査を追加します（I:992–1016、1184–1259）。違反行が0件でも実行負荷は0ではありません。
- BACK_OFFはabort時の待機とleader側の適応処理を有効化します（I:1105–1115、1291–1295）。Q1はwitness on同士で0/56対0/56なので、backoff単独の抑制効果は識別できません。

曝露量も変わっています。Q2の平均commit数/走は鎖の順に約 **797,192 → 784,935 → 711,199 → 541,601 → 543,065** でした。固定3秒のrun当たり検出率であり、同数のcommit機会に対する比較ではありません。

独立標本としての片側Fisher参考値は、X/P追加の3対2で **0.5**、witness追加の2対0で **0.246835**、診断追加の0対0で **1.0**。node内反復・回転順・複数比較を調整していない参考値であり、いずれも抑制効果の確証にはなりません。0/40の片側95%上限は **7.216%**、両側CP上限は **8.810%** です。

「(a)と整合」は、**候補の条件付き順序論証が観測形に反しない**という意味までです。「(a)を識別した」「(ii)だけが原因」「診断で根因を確認」は不可です。

discriminatorの結論が得られた場合でも、意味は以下に限定されます（`mocc_g2_discriminator.py:575–624,648–653`）。

- **supported:** 対象comparisonのreader-version producerと先頭stamp producerが一致。stamp外の混合、(i)の時間的重なり、hookの整合した誤帰属、writer版・commit順序・verifier版順序仮定を排除しません。
- **contradicted:** 少なくとも一つのproducer不一致。版/payload不整合とhookの取り違えは分離できず、不一致だけで「新版stamp」とも断定できません。
- **今回:** 両結論とも0件であり、以上の識別証拠自体がありません。分岐2・3は残ります。

T-1892の5/42は旧束縛の観測として維持します。今回のp058の2/40はその歴史的推定と矛盾する証拠ではありませんが、環境同等性を実証もしません。T-1943のwitness on・1 cellの `no-g2` も維持し、「その走で識別対象を得なかった」と読みます。今回のwitness on・0/40はその観測と両立し、間隙不存在の証明にも、旧判定の無効化にもなりません。

## 総括

**GO：再分類済みの観測結果と、原因識別未到達を記録する成果物として。根因確定・診断効果確認という結論にはNO-GOです。**

insightの主判定文案：

> BACK_OFF=0の固定cellでは、producer・計装・witness・診断変更の鎖に沿ったG2 signal検出数は2/40、3/40、2/40、0/40、0/40だった（先頭2 armのcycleゼロ走は現行verifierでindeterminate）。7件のcycle形はvalidationの別読みによる静的候補(a)と整合するが、すべてwitness offで、payload-lineage識別には到達しなかった。witness有効時の未再現は観測者効果の仮説と両立するものの、診断効果、各間隙の寄与・必要性・根因、およびhook／verifier仮定の分岐は確定しない。
