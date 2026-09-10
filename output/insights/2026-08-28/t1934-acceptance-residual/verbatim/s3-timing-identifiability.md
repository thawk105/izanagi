## 所見

結論は「実装差分ゼロで停止」が正しいです。ただし、親briefのP2とplanの一部表現は修正が必要です。既存artifactから最大成分を決めることはできません。

- 高: `R`は4成分の加算分解ではありません。

  shard-0の実値は `T=160.920`、`M=max busy sum=101.696815627`、`R=59.223184373` です。[report.json](</work/1/SFC/tanab/.izanagi-acceptance-shards/40fc419debb24c1345a03f83238d0d98/shard-0/report.json:1>) の`worker_occupancy`は各workerのreport duration和にすぎず、開始、終了、idleを持ちません。[acceptance_shards.py:862](</work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t1934-acceptance-residual/tools/acceptance_shards.py:862>)、[acceptance_shards.py:983](</work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t1934-acceptance-residual/tools/acceptance_shards.py:983>)

  最後に終わるworkerを`j`、そのbusy和を`q_j`、テスト開始前遅延を`a_j`、worker内idleを`g_j`、内部finalizationを`F`とすると、

  `R = a_j + g_j + F - (M - q_j)`

  です。最後のworkerが最大busy workerでない場合、末尾項は負になります。したがって残差は非負4成分とidleの単純な和ですらありません。[plan.md:40](</work/1/SFC/tanab/dev-wave-jobs/dev-wave-t1934-acceptance-residual/s2/plan.md:40>) の注意は正しいものの、「混在」より強く「加算モデルが成立しない」と明記すべきです。

  同一artifactに合う具体的反例は次のとおりです。

  - 反例A: gw14が`59.223184`秒後にbusy処理を開始し、`101.696816`秒連続実行してcutoffで終了する。残差は全て起動、collectionなどの前置遅延で説明できる。
  - 反例B: gw14は時刻0から`101.696816`秒で終了する。一方、最小busy和のgw24はscheduler待ちの後、時刻`68.641187`から`92.278813`秒実行してcutoffで最後に終了する。残差はscheduler idleとcritical worker不一致で説明できる。
  - 反例C: gw14が時刻0から`101.696816`秒で終了し、その後`59.223184`秒を内部finalizationに使う。これも同じJUnitとreportを生成できる。

  成果物影響: collection、worker起動、prewarm、finalizationのいずれも最大と選べず、修理pathを決定できません。

- 高: 親briefの「finalizationは1秒未満」は成立しません。

  [s1-brief.md:13](</work/1/SFC/tanab/dev-wave-jobs/dev-wave-t1934-acceptance-residual/s1-brief.md:13>) の1秒未満という値が表せるのは、よくてもJUnit cutoff後のrunner側tailです。最後のtest終了からJUnit cutoffまでの内部finalizationではありません。

  acceptance reportは`pytest_sessionfinish(trylast=True)`で作られ、`finished`もsortされるため、最後のtest、最後のworker、終了時刻は失われています。[acceptance_shards.py:955](</work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t1934-acceptance-residual/tools/acceptance_shards.py:955>) 同秒mtimeも同一秒内の順序や、最後のtestからJUnit hookまでを測りません。plan自身は後段で正しく限定しています。[plan.md:36](</work/1/SFC/tanab/dev-wave-jobs/dev-wave-t1934-acceptance-residual/s2/plan.md:36>)、[plan.md:59](</work/1/SFC/tanab/dev-wave-jobs/dev-wave-t1934-acceptance-residual/s2/plan.md:59>)

  得られる粗い上界は、通常のpytest lifecycleを前提として`0 <= F <= R`、shard-0なら約`59.224秒`までです。従ってfinalizationを最大候補から除外できません。

  成果物影響: P2を根拠にfinalization修理を候補外へ落としてはいけません。

- 高: 指定資料だけではJUnitとxdistの正確なhook順を現行sourceで確定できません。

  repo内で確認できる順序は以下までです。

  1. runnerが`--junitxml`、xdist、acceptance plugin付きpytestを起動する。[run_tests.py:1495](</work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t1934-acceptance-residual/tools/run_tests.py:1495>)
  2. conftestのcollection wrapperがmarkerを付与し、acceptance pluginの`trylast` hookが全universeから担当外をdeselectする。[conftest.py:1983](</work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t1934-acceptance-residual/orchestrator/tests/conftest.py:1983>)、[acceptance_shards.py:825](</work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t1934-acceptance-residual/tools/acceptance_shards.py:825>)
  3. controllerが最初の該当`pytest_xdist_node_collection_finished`でreceipt prewarm、続いてoracle prewarmを同期実行する。[conftest.py:2149](</work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t1934-acceptance-residual/orchestrator/tests/conftest.py:2149>)
  4. workerのsessionfinish payloadをcontrollerが回収し、controllerのacceptance `pytest_sessionfinish(trylast=True)`がreportを書く。
  5. memo終了処理は`pytest_unconfigure`で行われる。[conftest.py:2903](</work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t1934-acceptance-residual/orchestrator/tests/conftest.py:2903>)

  しかし、JUnit pluginとxdist DSession/schedulerのsource、pytest/xdistの実走versionが射影されていません。`run_tests.py`はxdist `>=2.5`しか要求せず、artifactにもversionがありません。従ってJUnitのsession timestampがworker launchの前か後か、collection callbackとscheduler登録の厳密な順序、JUnit hookとreport hookの相対順は、この証拠集合ではsource照合不能です。

  成果物影響: scheduler startからJUnit timestampまでの4.129秒をworker起動から完全に分離する主張は採用できません。

- 高: K=2/K=3の5 shardにはprewarmを識別する統計条件がありません。

  shard-0 reportの全17455件を現行allocatorで静的に再割当した結果は次です。これは現行source上の反実仮想配置であり、K=2実走値ではありません。[acceptance_shards.py:377](</work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t1934-acceptance-residual/tools/acceptance_shards.py:377>)

  | K | shard | selected | receipt consumer | oracle consumer | 主なgroup成分 |
  |---:|---:|---:|---:|---:|---|
  | 2 | 0 | 8728 | 36 | 28 | real-repo等、3100件 |
  | 2 | 1 | 8727 | 0 | 0 | dev-waves-runtime、105件 |
  | 3 | 0 | 5819 | 36 | 28 | real-repo等、3100件 |
  | 3 | 1 | 5818 | 0 | 0 | dev-waves-runtime、105件 |
  | 3 | 2 | 5818 | 0 | 0 | groupなし |

  prewarm有無は5セル全てで巨大なreal-repo連結成分の有無と完全に共線です。さらにK変更でselected数とLPT配置が変わります。反復もなく、K=2の直接artifactも射影されていません。従って約10秒差はprewarm値でも上界でも下界でもありません。[plan.md:38](</work/1/SFC/tanab/dev-wave-jobs/dev-wave-t1934-acceptance-residual/s2/plan.md:38>) の結論は正しく、親briefの「最大でも約10秒」は撤回対象です。

  成果物影響: prewarmを最大成分または修理対象に選べません。

- 中: login collectionを「critical path外」と断定するのは過大です。

  実装は全dispatch processをstartした後、親でlogin collectionを同期実行しています。[acceptance_shards.py:1305](</work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t1934-acceptance-residual/tools/acceptance_shards.py:1305>)、[acceptance_shards.py:1335](</work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t1934-acceptance-residual/tools/acceptance_shards.py:1335>) したがって、login branchがcomputeより先に完了したなら、7.98秒全体が直列tailとして外側wallへ加算されたわけではありません。

  一方、login collectionはdispatch子のsubmit処理やshared filesystemアクセスと併走します。CPU、memory、filesystem競合によるcompute側遅延をsourceもtimestampも排除していません。また直接のlogin log、shard-1/2 JUnit、receiptは今回の射影外です。[plan.md:49](</work/1/SFC/tanab/dev-wave-jobs/dev-wave-t1934-acceptance-residual/s2/plan.md:49>) は「terminal joinを支配しなかった可能性が高い」までに弱めるべきです。

  成果物影響: 7.98秒を残差から減算してはいけません。ゼロ寄与の一般化もできません。

- 中: 「約49秒の共通bundle」は強すぎます。

  49.039秒と49.557秒は近い二つの混合スカラーにすぎず、collection、launch、idle、finalizationの同一部分が共通だとは識別されていません。[plan.md:61](</work/1/SFC/tanab/dev-wave-jobs/dev-wave-t1934-acceptance-residual/s2/plan.md:61>) は「類似した残差値」に改めるべきです。

- 低: shard-0残差の6桁表示は見かけ上の過剰精度です。

  [junit.xml](</work/1/SFC/tanab/.izanagi-acceptance-shards/40fc419debb24c1345a03f83238d0d98/shard-0/junit.xml:1>) のsuite timeは`160.920`とミリ秒精度です。9桁のbusy和との差を`59.223184`秒と表示しても、少なくともJUnit丸め幅の不確かさが残ります。主要判定は変わりませんが、残差は`59.223秒`程度と記すのが妥当です。

## 4成分の反証表

| 成分 | 識別できる事実 | 得られる値または界 | 反証 |
|---|---|---|---|
| worker起動 | 48 workerがpayloadを返したこと | duration非同定。JUnit timestampとの包含関係もdependency source不足 | launchをJUnit前4.129秒側にも、JUnit内残差側にも置ける |
| collection | 48 workerが同一17455件をcollectionしたこと | 開始、終了なし。旧走12.86秒は現行界ではない | worker間並行、launchとの重なり、prewarmとの重なりを変えて同じdigestを生成できる |
| prewarm | consumer shardでreceipt、oracleが各1回同期発火すること | 非consumer shardは0。consumer shardのdurationとcritical寄与は非同定 | 約10秒差はreal-repo成分、割付、node、idleと完全に交絡する。collection overlapによりraw costとwall寄与も異なる |
| finalization | JUnit cutoff後の短いrunner tailと、reportがsessionfinishで作られること | 内部`F`はshard-0で粗く`0から約59.224秒` | 最後のtest timestampがなく、59.223秒全体をfinalizationへ割り当ててもartifactと矛盾しない |

従って得られる界は非負、非consumerのprewarmが0、finalizationが残差以下という粗いものだけです。最大成分を順位付けするには不十分です。

## 停止条件の判定

| 停止条件 | 判定 |
|---|---|
| 4成分モデルが観測量を閉じる | 不成立。scheduler idle、critical worker不一致、phase overlapが残る |
| 最大成分を一意に決められる | 不成立。各反例が同じartifactに適合する |
| K=2/K=3からprewarmを統計識別できる | 不成立。prewarmとreal-repo成分が完全共線、反復なし、K=2直接artifactなし |
| 現行mainで同一成分が反復再現済み | 証拠なし。今回の射影からは検証不能 |
| 単一の局所所有pathが決まる | 不成立。runner、shard plugin、conftest、dependency schedulerのどこにも一意化できない |
| 1件の修理とpaired全受入へ進める | 不可 |

停止自体は妥当です。必要な修正は実装ではなく、plan上の断定を弱めることです。ただし本dispatchはread-onlyかつ変更禁止なので、ファイルは変更していません。

## 総括

最大成分は識別不能です。親briefの「finalizationは1秒未満」と「prewarmは最大でも約10秒」は誤りで、planの「login collectionはcritical path外」「約49秒の共通bundle」も断定が強すぎます。

T-1934は実装差分ゼロで停止すべきです。pytest/buildは実行しておらず、既存artifactの静的解析だけを行いました。コード、docs、Git状態は変更していません。