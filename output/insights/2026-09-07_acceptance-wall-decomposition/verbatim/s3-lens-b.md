## 総括

静的検査の結論は、段 2 プランから「中央値 324.3 秒を有意に短縮できる」とはまだ言えない、です。厳格な意味での `blocker` は 0 件ですが、効果見積りを無効にする `should-fix` が 10 件あります。

特に重要なのは次の三点です。

- L2 の lock 共有は、同時 miss した worker の 70 秒を消しません。1 worker が構築する間、他 worker は約 70 秒待つためです。構造上の利得はほぼゼロで、得られる可能性があるのは重複構築による競合の軽減だけです。
- D1020 の引き金は誤適用されています。`W` は一走全体、`K=3` です。提示中央値を仮に同一走として検算しても `C=161.6 > W/(48K)=約129` であり、成立していません。
- `worker_occupancy.duration_s` は worker の busy time ではなく、setup/call/teardown の `TestReport.duration` 合計です。protocol 外の lock 待ち、scheduler gap、collection、起動を含みません。

また、最新 75 artifact の静的再集計では collection digest が 40 種類、universe は 20,410 から 21,111 件でした。324.3 秒は固定 tip・固定受入集合の中央値ではなく、複数 branch/tip世代の混合値です。

書込み、pytest 実走、commit、branch 操作は行っていません。

## critical path の判定 (案ごとに a / b / c)

| 案 | 判定 | 根拠 |
|---|---|---|
| selected-file collection | **b** | test開始前の最遅 worker collectionを短縮する案。controller自身はcollectしない。別経路が律速ならc |
| L1-A `_canonical_item` 一回化 | **b、ただし実質cの可能性大** | collection残差だけを縮める。旧上限0.2から0.6秒で、最遅collectorが変わらなければwall効果ゼロ |
| L1-B ledger圧縮 | **b、未証明ならc** | worker起動前のpayload転送・復号だけが対象。最大worker実行時間は縮めない |
| L1-C prewarm重畳 | **b、自然重畳が無ければc** | controller barrierを縮め得るが、既存4.17から4.97秒は同期prewarm自身が作った通知遅延の疑いがある |
| L2 t080 host cache | **a、ただしlock待ちへ置換されればc** | 最近の9走ではshard-0最大occupancyがt080 workerだった。ただし同時missでは全workerがbase完成を待つ |
| floor host cache | **c** | direct consumerが1 nodeでcache hitが無く、段2も0秒と判定 |
| L3 duration shard割付 | **c、現時点** | 正しいD1020検算では再検討引き金が示されておらず、11.6秒は定所要時間模型だけ |
| L4 test削除 | **c、現時点** | 最新親測定は候補ゼロ。段2の5件はcritical workerへの所属を示していない |

`worker_occupancy` の最大値がt080であるという最近の直接証拠は [T-2298 measurements](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-acceptance-wall-20260907/output/insights/2026-09-04_t2298-t2273-shard0-critical-path/measurements.md:42) にあります。ただし同じ文書は、occupancyにprotocol外待ちが入らないことも明記しています。

## L1 の効果への反証

所見 B-01 — severity: `should-fix`

- 反証シナリオ: 親promptが指定した「controllerの全collectionが残ってworker絞込みがゼロになる」シナリオは、現行xdistには当たりません。controllerはcollectionを禁止し、48 worker全員のcollection到着後に初めてscheduleします。[dsession.py](/home/SFC/tanab/.local/lib/python3.10/site-packages/xdist/dsession.py:102)、[同](/home/SFC/tanab/.local/lib/python3.10/site-packages/xdist/dsession.py:274)、[loadscope.py](/home/SFC/tanab/.local/lib/python3.10/site-packages/xdist/scheduler/loadscope.py:357)
- 根拠: 各workerはcollectionを実行してitem IDを送ります。[remote.py](/home/SFC/tanab/.local/lib/python3.10/site-packages/xdist/remote.py:152)、[同](/home/SFC/tanab/.local/lib/python3.10/site-packages/xdist/remote.py:256)
- ただし別の反証シナリオ: scoped collectionを速くしても、最遅worker以外だけが速くなる、prewarmやcontroller callbackが次の律速になる、または別shardが全体最大になる場合、wall効果はゼロです。
- 効果上限: login nodeの較正だけを使うなら `87.57 - 27.44 = 60.13秒` がcollection-only差の上限です。「そのまま効く」値ではありません。[親測定](/home/SFC/tanab/.claude/jobs/98cb6669/tmp/measurements.md:20)
- 提案: 同一計算ノード、同一tip、同一xdist argvで `max(worker collection end)` を対測定し、`first test start` まで縮んだ量だけをL1効果とすること。

外側のlogin collectorはshard起動後に並走しますが、各shardのJUnit wallには含まれません。[acceptance_shards.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-acceptance-wall-20260907/tools/acceptance_shards.py:1243)、[同](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-acceptance-wall-20260907/tools/acceptance_shards.py:1335)。したがってcontroller collectionの代替律速とは扱えません。

所見 B-02 — severity: `should-fix`

- 反証シナリオ: L1-Aが各workerで0.6秒短縮しても、worker collection終了時刻の最大値を持つworkerが別要因で遅ければwallは変わりません。L1-Bも118 MBという総転送量を減らすだけで、slowest-worker起動時刻が変わらなければゼロです。
- 根拠: 段2自身がL1-Aを旧測定上限0.2から0.6秒、L1-Bをwall未測定としています。[s2-plan](/home/SFC/tanab/.claude/jobs/98cb6669/tmp/dw-artifacts/dev-wave-acceptance-wall-20260907/s2-plan.md:386)
- 提案: L1-A/Bは実装前に計算ノード上の48-worker collection A/Bで `last collection end` の差を測ること。1秒未満なら本waveのwall leverから外すこと。

所見 B-03 — severity: `should-fix`

- 反証シナリオ: 現行prewarmは最初のcollection通知をcontrollerが処理している最中に同期実行されます。この4秒中に他workerがcollectionを終えても、通知はevent queueに溜まります。観測された「最初から最後の通知幅」が約4秒でも、thread化後の完了時刻は `max(prewarm完了, 最終worker完了)` のままで、wall短縮は0秒になり得ます。
- 根拠: prewarmは同期関数で、初回だけ実仕事を行います。[conftest.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-acceptance-wall-20260907/orchestrator/tests/conftest.py:774)。collection callbackから直接呼ばれています。[conftest.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-acceptance-wall-20260907/orchestrator/tests/conftest.py:2153)。過去のcontroller受信幅は51.010から55.176秒でした。[T-2097 measurements](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-acceptance-wall-20260907/output/insights/2026-09-02_t2097-residual-breakdown/measurements.md:128)
- 提案: controller受信時刻ではなく、worker側のcollection endとprewarm start/stopを同一monotonic時計で比較すること。自然な重畳時間が3秒以上という条件を満たさなければL1-Cを実装しないこと。

selected-file collectionを本waveで不採用にする段2判断自体は、効果面からも妥当です。

## L2 の効果への反証

所見 B-04 — severity: `should-fix`

- 反証シナリオ: 7 workerがdefault keyを同時に要求し、base構築を `B=70秒`、各testのcopyと本体を `q_i` とします。現状の無競合critical pathは概ね `B + max(q_i)`。共有lock後も、1 workerがBを払い、残る6 workerはBだけ待ってから処理するため、やはり `B + max(q_i)` です。構造上の短縮は0秒です。
- 根拠: 現行helperはkey miss時にbaseを構築し、その後testごとにcopytreeします。[test_s8b_oracle_driver.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-acceptance-wall-20260907/orchestrator/tests/test_s8b_oracle_driver.py:893)。親の直列実測でも最初のnodeが73.64秒、cache hit後は3.70から14.98秒です。[親測定](/home/SFC/tanab/.claude/jobs/98cb6669/tmp/measurements.md:35)
- 帰結: 「残るnodeは約4秒」にはなりません。同時missしたnodeは、約70秒のbuildを約70秒のlock waitへ置き換えるだけです。利得候補は、並列構築時の競合による132から155秒への膨張を、isolatedの60から77秒へ戻す部分だけです。[T-2298 measurements](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-acceptance-wall-20260907/output/insights/2026-09-04_t2298-t2273-shard0-critical-path/measurements.md:107)
- 提案: 191.6から100から120秒という予測を撤回し、48 simultaneous cold missで、各workerの `lock_wait/build/copy/body` を分けた局所A/Bを先に行うこと。

lock共有が現状より遅くなる反証例もあります。

- lockをcopytree完了まで保持する実装なら、48 workerのcopyが直列化され、`70 + 48×copy` になります。
- lockをpublish直後に解放しても、48 workerが同じtreeを一斉にcopyするthundering herdが起きます。現在の独立構築が時間的に散っている場合、`共有build + 同期copyの最大時間` が現状の最大時間を超え得ます。
- 二段cacheでは、同じbasisを待った5 final-key builderが一斉にreceipt発行へ進むため、単に競合の時刻を後段へ移す可能性があります。

提案は、lockをpublish前だけに限定し、その契約をtestで固定したうえで、48 contender時のp50/p90/maxを現行と比較することです。

所見 B-05 — severity: `should-fix`

- 反証シナリオ: 4つのsingleton final keyはfinal cache hitを一度も生みません。basis共有部分が小さければL2利得はdefault keyだけに限定されます。
- 根拠: 実sourceの対象は10 testではなく6 function、11 nodeです。[test_s8b_oracle_driver.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-acceptance-wall-20260907/orchestrator/tests/test_s8b_oracle_driver.py:933)。内訳はdefault 7、`distinct_basis_blob` 1、bad trailer 1、extra path 1、issue false 1です。[同](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-acceptance-wall-20260907/orchestrator/tests/test_s8b_oracle_driver.py:1374)、[同](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-acceptance-wall-20260907/orchestrator/tests/test_s8b_oracle_driver.py:1465)、[同](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-acceptance-wall-20260907/orchestrator/tests/test_s8b_oracle_driver.py:1787)、[同](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-acceptance-wall-20260907/orchestrator/tests/test_s8b_oracle_driver.py:4378)
- 提案: 効果計算を「final build 11から5」「basis build 11から2」に分け、basisとreceipt発行の実測時間を別々に出すこと。親測定の「default 8から9 node」は7 nodeへ訂正すること。[親測定](/home/SFC/tanab/.claude/jobs/98cb6669/tmp/measurements.md:148)

## T-1933 負結果との整合

所見 B-06 — severity: `should-fix`

- 反証シナリオ: grouping後のwall不変が「1 workerが70秒と本体を直列に背負ったから」ではなく、別workerまたは約60秒のreport外区間がcritical pathだった可能性があります。保存artifactにはworker start/stop frontierが無く、原因を分離できません。
- 根拠: T-1933が実際にgroup化したのはdefault keyの3 function、6 nodeです。full K=3はpre中央値244.810秒、post245.707秒で+0.897秒でした。[T-1933 source README](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-acceptance-wall-20260907/output/insights/2026-08-28_t1933-acceptance-longest-node/sources/acceptance-fastest-README.md:10)。一方、worker duration総和は6456から4864秒へ1592秒減ってもwallは変わりませんでした。[同](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-acceptance-wall-20260907/output/insights/2026-08-28_t1933-acceptance-longest-node/sources/acceptance-fastest-README.md:43)
- 判定: 親の説明は定性的にはあり得ますが、artifactで検証済みではありません。算術も「3×4」ではなく6 nodeが対象です。
- L2への帰結: T-1933は、重複構築を6から1へ減らしてもwallが下がらなかった実例です。worker跨ぎ共有は本体の並列性を残す点で別案ですが、本体は3.7から15秒程度で、最初のbase barrierは残ります。したがってT-1933はL2の正の根拠ではなく、full A/B必須という負の先例です。
- 提案: L2の採否にT-1933の原因説明を使わず、現行11 nodeのcold simultaneous miss A/Bとfull acceptance A/Bだけを使うこと。

## 既裁定の再適用と検算

所見 B-07 — severity: `should-fix`

- 反証シナリオ: 親は各shardについて `C_i < W_i/48` を計算しましたが、D1020の式では `W` は一走全体、`K` はshard数です。[D1020](/home/SFC/tanab/.claude/jobs/98cb6669/tmp/rulings-d1019-d1020.md:42)
- 検算:
  - 表の `W=7963+5757+4957=18677`
  - `W/(48×3)=129.70`
  - `C=max(78.5,16.7,161.6)=161.6`
  - よって `C > W/(48K)` であり、引き金は不成立です。
  - shard-2の `4957/48` は103.27であり、表の101.4とも一致しません。4867の誤記としても閾値は129.08で、結論は変わりません。[親測定](/home/SFC/tanab/.claude/jobs/98cb6669/tmp/measurements.md:6)
- さらに、D1020は同じ一走のCとWを要求します。shard別中央値を合成して一走の引き金とすること自体が不適格です。[D1020](/home/SFC/tanab/.claude/jobs/98cb6669/tmp/rulings-d1019-d1020.md:54)
- 提案: 75走をsession単位にjoinし、各走について `W=全3 shardのJUnit duration合計`、`C=全component中の最大鎖`、`K=3` を再計算すること。それまではL3をD1020成立と記載しないこと。

所見 B-08 — severity: `should-fix`

- 反証シナリオ: all-known時だけduration割付を発火させるなら、未知nodeが毎走残って旧割付へ戻ります。partial coverageで動かすなら、どの測定を重みにしたか後から判定できません。
- 根拠: 現行ledgerは19,519 nodeです。[acceptance_duration_ledger.json](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-acceptance-wall-20260907/orchestrator/tests/acceptance_duration_ledger.json:17574)。親の21,005 universeに対して92.93%で、D1019の92.5%問題は実質そのままです。ledger schemaにはtip、K、scheduler、worker数、入力JUnit digestがありません。[同](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-acceptance-wall-20260907/orchestrator/tests/acceptance_duration_ledger.json:1)。reportのclosed 14 fieldにも`allocation_mode`がありません。[acceptance_shards.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-acceptance-wall-20260907/tools/acceptance_shards.py:61)
- 判定: 段2は「同じ変更単位に入れる」とだけ述べ、schema、未知node規則、producer、consumer、走行証拠を設計していません。[s2-plan](/home/SFC/tanab/.claude/jobs/98cb6669/tmp/dw-artifacts/dev-wave-acceptance-wall-20260907/s2-plan.md:231)
- 提案: L3は引き続き不採用。再開するならprovenance付きledger、未知node policy、実効allocation modeのsidecar証拠を先に具体化すること。

D531について、L3を実装前模型だけで採らずA/Bへ送る段2判断は正しいです。ただし必要な反復数がありません。[D531](/home/SFC/tanab/.claude/jobs/98cb6669/tmp/rulings-d531-d532.md:1)

## 測定方法論への反証

所見 B-09 — severity: `should-fix`

- 反証シナリオ: workerがtest間のscheduler gapやprotocol外lock待ちで30秒止まっても、`duration_s` は増えません。そのworkerが最後に終わる真のcritical workerでも、別workerが最大occupancyとして選ばれます。
- 根拠: pluginは各phaseの`report.duration`をnode単位に加算し、後でworkerごとに合計しています。[acceptance_shards.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-acceptance-wall-20260907/tools/acceptance_shards.py:862)、[同](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-acceptance-wall-20260907/tools/acceptance_shards.py:973)。xdist自身が送る全protocol durationは別eventですが、report生成には使われません。[remote.py](/home/SFC/tanab/.local/lib/python3.10/site-packages/xdist/remote.py:226)。real-repo lockはphaseの外側を包みます。[conftest.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-acceptance-wall-20260907/orchestrator/tests/conftest.py:2073)
- 判定: `duration_s` は「報告phase時間合計」であり、「busy時間」でも「worker span」でもありません。`wall=max occupancy+residual` は残差を差で定義した恒等式で、critical pathを説明した証拠ではありません。
- 提案: workerごとにfirst protocol start、last protocol stop、protocol duration、phase duration、inner gap、lead、tailを記録し、最後に終わったworkerをcritical workerとすること。

所見 B-10 — severity: `should-fix`

- 反証シナリオ: login nodeでは96 core、異なるcache温度、負荷、Python環境、共有filesystem状態で87.57秒、計算ノードでは48 coreで別値になる場合、差60.13秒を受入へ転移できません。
- 根拠: 親測定はloginと計算ノードを混在させています。[親測定](/home/SFC/tanab/.claude/jobs/98cb6669/tmp/measurements.md:1)。runbookも性能比較のnode交絡を明示しています。[pegasus-runbook.md](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-acceptance-wall-20260907/docs/pegasus-runbook.md:1315)
- 判定: T-2298の119から56秒は方向を支持しますが、別host、別時刻、full非shard対selected shardであり、転移量の対測定ではありません。[T-2298 measurements](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-acceptance-wall-20260907/output/insights/2026-09-04_t2298-t2273-shard0-critical-path/measurements.md:72)、[同](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-acceptance-wall-20260907/output/insights/2026-09-04_t2298-t2273-shard0-critical-path/measurements.md:135)
- 提案: L1の約55秒と全体200から230秒予測を撤回し、計算ノード内paired測定で置換すること。L2の専有計算ノード測定は別に保持してよいです。

所見 B-11 — severity: `should-fix`

- 反証シナリオ: test追加でuniverseが増えた時期の遅い走と、古い小さいsuiteの速い走を一つの中央値へ混ぜると、現行mainのbaselineではなくmain進行量を測ります。
- 根拠: 最新75 sessionをartifact mtime順に静的再集計すると、2026-09-04 15:07から09-07 10:03の間にcollection digestが40種類、universe countが36種類あり、20,410から21,111件へ動いていました。先頭例は [report.json](/work/1/SFC/tanab/.izanagi-acceptance-shards/3d5d4d5f874a65b4673cae6cad515c6f/shard-0/report.json:1)、末尾例は [report.json](/work/1/SFC/tanab/.izanagi-acceptance-shards/b1cd36ed1e694711c17eb297e16445ce/shard-0/report.json:1) です。
- 判定: 324.3秒は歴史的な運用分布としては有効ですが、現行tipのbefore値や効果量推定には使えません。report schemaにtested tip、hostname、開始時刻もありません。
- 提案: 同一tested tip、同一collection digest、同一K、同一worker数、同一hold状態だけでbaselineを作ること。既存75走は原因候補探索に限定すること。

所見 B-12 — severity: `should-fix`

- 反証シナリオ: 計装1走がたまたまcollectionの軽いnodeまたはt080競合の重いnodeへ当たれば、140秒残差の主因分類が逆転します。
- 根拠: 段2は原因分解用の計装付き受入を1回だけとしています。[s2-plan](/home/SFC/tanab/.claude/jobs/98cb6669/tmp/dw-artifacts/dev-wave-acceptance-wall-20260907/s2-plan.md:53)。過去9走ではshard-0の `wall-maxocc` が95から207秒まで動いています。[T-2298 measurements](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-acceptance-wall-20260907/output/insights/2026-09-04_t2298-t2273-shard0-critical-path/measurements.md:42)
- 提案: 原因分解も少なくとも固定tipで3から5反復し、中央値と範囲を出すこと。1走は配線確認にだけ使うこと。

## A/B 対測定の設計

D531を満たす測定は次の形にします。

1. L1/L2の旧経路と新経路を同じcommitに残し、環境変数でarm A/Bを切り替える。sidecarへexpected HEAD、arm、K=3、worker=48、collection digest、growth/flaky hold状態、Python/pytest/xdist版、3 hostnameを保存する。
2. 3計算ノードを一つのblockとして確保し、shard indexとhostnameの対応をblock内で固定する。AとBを別々のscheduler jobへ投げてnodeと処置を一対一対応させてはならない。[pegasus-runbook.md](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-acceptance-wall-20260907/docs/pegasus-runbook.md:1328)
3. block内で `ABBA` または `BAAB` を無作為に選び、4 full acceptanceを逐次実行する。session cacheは毎走新規にし、OS/Lustre cacheの順序効果はABBAで均衡させる。
4. 主指標は各full acceptanceの `max(3 shardのJUnit testsuite@time)`。各pairの `A-B` を作ってから中央値を求める。t080 node時間、last collection end、worker spanは原因診断用で、主指標の代用にしない。
5. red集合、selected/finished、collection digestが不一致のpairは事前規則で無効とする。値を見てから除外しない。
6. L1+L2合成armが有意に改善した場合だけ、同じ手順でL1とL2をablationする。

必要回数について、D1019の32.27秒は2走の差であって標準偏差ではありません。したがって確定的なpower計算には使えません。感度計算として、paired差の標準偏差を32秒、両側5%、power 80%と仮定すると、

`n_pairs = ceil((2.80 × 32 / 検出したい秒数)^2)`

です。

| 検出したい短縮 | 必要pair | full acceptance回数 |
|---:|---:|---:|
| 70秒 | 2 | 4 |
| 55秒 | 3 | 6 |
| 20秒 | 21 | 42 |
| 15.8秒 | 33 | 66 |
| L3の11.6秒 | 60 | 120 |
| L1-Cの4.97秒 | 326 | 652 |
| L1-Aの0.6秒 | 22,301 | 44,602 |

実運用案は、20秒を最小実益と仮置きし、ABBAの都合で11 block、22 pair、**44回のfull acceptance**です。最初の4 block、16走は効果を見ずにpaired分散だけを確認し、標準偏差が32秒を超えるなら上式で総数を増やします。20秒という最小実益は親裁定が必要です。

名指しすると、L1-A、L1-C、L3、L4の個別効果は32秒級のばらつきに対して小さすぎ、full acceptanceで単独検出する費用に見合いません。L1-Bは効果量が未測定なので回数を決められません。これらは先に局所critical-path測定で落とすべきです。

## 所見一覧 (severity 付き)

| ID | severity | 所見 |
|---|---|---|
| B-01 | should-fix | xdist controller collection仮説は反証されたが、60.13秒が受入wallへそのまま効く主張も未証明 |
| B-02 | should-fix | L1-A/Bは総仕事量または非critical workerだけを縮め、wall効果ゼロになり得る |
| B-03 | should-fix | L1-Cの4秒通知幅は同期prewarm自身による観測汚染の疑い |
| B-04 | should-fix | L2は70秒buildを70秒lock waitへ置換し、構造上はcritical pathを縮めない |
| B-05 | should-fix | t080は11 node、default 7。4 singleton final keyの共有利得は0 |
| B-06 | should-fix | T-1933の負結果は実測済みだが、親の因果説明はartifactから確定できない |
| B-07 | should-fix | D1020のW/Kを誤適用。提示値では引き金不成立 |
| B-08 | should-fix | D1019の92.5%被覆、provenance欠落、発火証拠欠落はL3案で未解決 |
| B-09 | should-fix | `worker_occupancy.duration_s` はbusy timeではなくphase duration合計 |
| B-10 | should-fix | login collection値を計算ノード受入の秒数へ直接転移できない |
| B-11 | should-fix | 75走中央値は40 collection digestを混ぜ、現行tip baselineにならない |
| B-12 | should-fix | 原因分解1走と反復数未指定A/Bでは中央値短縮を示せない |
| B-13 | should-fix | 段2のL4 5件削除と、親最新測定の「候補ゼロ」が矛盾 |

`blocker` はありません。L2には競合軽減、L1には残差短縮の可能性が残り、「実装しても必ず効果ゼロ」とまでは証明できないためです。

## 未解決・要親裁定

- D1020の引き金は不成立としてL3を閉じ直すか。推奨は閉じ直す。
- L2を「70秒削減」ではなく「競合膨張分だけが候補」として、48 simultaneous cold-miss A/Bからやり直すか。推奨はやり直す。
- full A/Bの最小実益を20秒とするか。採るなら11 ABBA block、44 full acceptanceを最低計画とする。
- 同一3-node allocation内でA/Bを閉じる測定経路を用意できるか。できなければD531を満たさない。
- L1-AとL1-Cをwall leverから外すか。推奨は、局所対測定で1秒未満なら実装しない。
- L4は親最新測定の「削除候補ゼロ」と段2の「5 node削除」のどちらを正とするか。効果面の推奨はL4を本waveから外す。
- 既存75走は原因探索専用とし、324.3秒を現行tipのbefore中央値として使わないことを承認するか。推奨は承認する。