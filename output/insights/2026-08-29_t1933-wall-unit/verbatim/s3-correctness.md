[所見 1] `testsuite@time` を pytest session wall と読むこと自体は正しく、この疑義は反証される
[分類] measurement-validity
[根拠] `/home/SFC/tanab/.local/lib/python3.10/site-packages/_pytest/junitxml.py:644-653` は `self.suite_start = timing.Instant()` とし、session finish で `duration = self.suite_start.elapsed()` を計算する。`_pytest/main.py:326-372` では configure 後に `pytest_sessionstart`、test loop、`pytest_sessionfinish`、unconfigure の順である。`xdist/dsession.py:82-91` の worker 起動は sessionstart 内で行われる。
[反証シナリオ] launcher が pytest 起動前に30秒使い、JUnit が200秒なら、waiter wall は230秒でも `testsuite@time` は200秒である。親が対象を pytest session wall に限定する限り別量ではない。
[この所見が誤りである場合の条件] 対象 artifact がこの JUnit 実装とは異なる writer や版で生成され、`testsuite@time` が hook 間隔以外から作られていた場合。

[所見 2] `wall - max_occ` は全 worker が非実行である時間の下限ではなく、条件付きの上界である
[分類] measurement-validity
[根拠] `measurements.md:40` は「`wall − max_occ`（テストを 1 本も走らせていない時間の下限）」とする。一方 `tools/acceptance_shards.py:862-872` は worker ごとに setup、call、teardown の `report.duration` を単純加算するだけである。全 worker の phase interval の和集合を A、真の全体無稼働時間を N とすれば、`N = wall - |A|` かつ `|A| >= max_occ` なので `wall - max_occ >= N` である。
[反証シナリオ] wall 100秒で、worker A が前半50秒、worker B が後半50秒を切れ目なく実行すると、全体無稼働時間は0秒だが `wall - max_occ` は50秒になる。
[この所見が誤りである場合の条件] 「テストを走らせていない時間」を全 worker 共通の無稼働ではなく、最多 occupancy worker 個体の session 内非 phase 時間と定義し、全 phase duration が session 内に正確に収まる場合。

[所見 3] 親の LPT は下界ではなく feasible schedule の上界であり、「LPT で縮まらないなら実 scheduler でも縮まらない」は成立しない
[分類] correctness
[根拠] `parent-findings.md:13-15` は「観測された makespan の観測下界として使う」「「LPT でも縮まない」は「実 scheduler でも縮まない」を含意する」とする。しかし `xdist/scheduler/loadscope.py:367-402` は work unit を item 数で並べ、各 worker に初期 unit を配った後、少なくとも二 unit を持たせる。`xdist/scheduler/loadscope.py:313-336` は完了時に pending 数で動的補充する。`xdist/scheduler/loadgroup.py:55-59` は marker なし node を各一 unit とする。LPT の近似保証は `OPT <= LPT <= 約4/3 OPT` であり、実 scheduler と LPT の大小関係は定まらない。
[反証シナリオ] 2 worker、queue 順の所要が `[5, 1, target=2, 1, 1]` なら、xdist の初期二 unit 配布で worker A は `5+2=7`、worker B は `1+1+1=3` となる。target を0にすると wall は5へ2秒縮む。一方 LPT は介入前も `5` 対 `2+1+1+1=5`、介入後も makespan 5で、短縮0と誤判定する。
[この所見が誤りである場合の条件] 各 artifact について duration ledger、workqueue 順、動的補充、unit の不可分性を再現し、実 scheduler と LPT の割付けが介入前後とも同一になることを証明した場合。

[所見 4] 親の「最重単位を無料にしても中央値3.2秒」は D357 を満たす current-tip 因果量ではない
[分類] ruling-conflict
[根拠] `parent-findings.md:51` は「直近 4 走で最重単位を無料にしたときの短縮は +19.3 / +2.7 / +2.3 / +3.8 秒、中央 3.2 秒」とする。`analyze7.txt:2-5` の group は `9c62f3`、`6fbbc4`、`96dd39`、`ef85f4` と異なる。`verbatim/rulings.md:26-29` は「同一 tip・同一条件で 3 走以上を逐次に取り、中央値で述べる」と定める。しかも3.2秒は実 full wall の介入差でなく、所見3の LPT 再配置差である。
[反証シナリオ] 四走のうち一走だけ C06 node が126.6秒、残り三走は T-080 が最重なら、中央値3.2秒は tip差や host差による frontier 交代を丸めただけで、同一介入の効果を表さない。
[この所見が誤りである場合の条件] 四 group の receipt が同一 tested tip、同一条件、逐次実行を証明し、さらに同一 target への実介入を before/post 各3走で測った場合。

[所見 5] shard-1、shard-2 の「60走が54.4〜56.2秒に収まる」は表自身に反し、固定床の証拠にならない
[分類] measurement-validity
[根拠] `parent-findings.md:75-79` と `analyze9.txt:2-4` は shard-1 の最小52.7、p25 54.6、中央値55.1、p75 56.2、shard-2 の最小53.1、p25 54.4、中央値54.9、p75 55.6を示す。ところが `parent-findings.md:86` は「60 走・9 台の計算ノードにまたがって 54.4〜56.2 秒に収まる」と記す。54.4と56.2は範囲端ではなく中央四分位付近の値である。
[反証シナリオ] shard-1 の52.7秒はすでに主張範囲外であり、p75が56.2秒なら最大25%の走が56.2秒を超えていても表は同じになる。安定しているのは中央域であって全60走ではない。
[この所見が誤りである場合の条件] raw 60値の最小と最大が54.4と56.2で、掲載した52.7、53.1および `p75` ラベルがすべて誤記だった場合。

[所見 6] 約55秒を「48回の全件 collection でほぼ説明」とする因果帰属は未測定で、collection 回数にも一回の欠落がある
[分類] measurement-validity
[根拠] `parent-findings.md:91-100` は login node の単一 process collect-only を42.78、16.16、11.37秒と測り、`parent-findings.md:104-114` はそれを48 worker concurrent の約55秒へ外挿する。`tools/acceptance_shards.py:1306-1335` は K shard process を開始した後に独立な `collect_login` も併走させるため、K=3では48×3 worker collectionに login collection 1回を加えた145回である。親の `parent-findings.md:111` の「144 回」は login collection を数えていない。また `parent-findings.md:102` は18,954 item、同:154は18,895 itemと不一致である。
[反証シナリオ] compute node で48 worker spawnが35秒、collectionが15秒、controller suffixが5秒なら residual は55秒になるが、単一 login process の11秒から collection が主因とは同定できない。併走する login collectionが共有 filesystemを競合させる場合も同じである。
[この所見が誤りである場合の条件] compute node の worker phase traceが、spawn、collection、deselect、prewarm、scheduler、suffixを閉じ、collection区間が約55秒の主要部分を占めることを示し、item数差も解消した場合。

[所見 7] pooled 相関は「固定75秒」や「総仕事量律速ではない」という一般化を支えない
[分類] correctness
[根拠] `measurements.md:33-38` は pooled で slope 1.018、intercept 75.2だが、K=3 recent では slope 1.540、intercept -0.5である。同:49-50は total occupancy/worker の相関が低いことだけから「受入 wall は総仕事量律速ではなく、最 busy worker 律速」と結論する。`measurements.md:98-106` は corpus の tipと混雑度が揃っていないことも認める。
[反証シナリオ] host slowdown が全 node duration を同率に膨らませ、同時に workload imbalance が tipごとに変われば、max occupancyとの相関は高く、平均 occupancyとの相関は低くなる。これは総仕事量の効果が存在しないことを意味しない。
[この所見が誤りである場合の条件] 同一 tip、同一 worker数、同一 collection universeでの反復から、固定効果や host効果を分離したモデルでも係数と residual floor が保たれ、総仕事量への介入が full wall を動かさない場合。

[所見 8] P1c の「最 busy worker は2〜5 node」は全484走の提示値からは支持されない
[分類] correctness
[根拠] `analyze2.txt:2-5` は `n=484` に対し item count を2:82、3:63、5:58、6:2、7:1、8:1、9:1、17:1と出すが、合計は209で275走が未記載である。`measurements.md:54-56` も同じ欠落を説明しない。さらに `analyze2.txt:16-19` のK=3には29、31、54 itemの走が各1本ある。
[反証シナリオ] 未記載275走がすべて1 itemなら全体中央値は1で「2〜5」という記述は誤る。未記載値が100 itemならさらに強く誤る。どちらも掲載集計と両立する。
[この所見が誤りである場合の条件] analyze script が275走を除外した理由と値を開示し、P1c の母集合を209走またはcurrent recent 117走へ明示的に限定した場合。

[所見 9] P1d の「critical worker は2系統」は最長 node と worker 帰属を混同している
[分類] correctness
[根拠] `measurements.md:60-67` の117走の最長 node は candidate group 79、ungrouped C06 predicate 25、T-080 12、trial registry 1の四項目である。同:103-104は「artifact に nodeid → worker の対応が無い」と明記する。それでも `brief.md:51-53` は「最 busy worker を占めるのは 2 系統だけ」と一般化する。
[反証シナリオ] C06 predicate 126.6秒がgw46とは別の最後まで動くworkerにあり、T-080群が別worker群にある走では、candidate group、C06、T-080の少なくとも三機構が frontier を作る。既存 artifact では排除できない。
[この所見が誤りである場合の条件] nodeid→workerと終了時刻を持つ artifactが、全対象走のcritical workerを定義済み二系統だけで完全に説明した場合。

[所見 10] hold 解除で同定結果は反転し得るが、段2計画は hold opt-in 状態を同値性キーへ含めていない
[分類] consistency
[根拠] `parent-findings.md:176-188` は結論を「hold が効いている状態」に限定し、解除時は candidate group が1位へ戻るとする。`orchestrator/tests/conftest.py:2020-2030` は環境 opt-in がない場合だけ skip marker を付ける。`s2-plan.md:214-223` の保存項目は tested tip、K、worker数、collection digestまでで、`IZANAGI_RUN_GROWTH_HELD_TESTS` を含まない。`tools/acceptance_shards.py:742-768` の collection record は nodeid、path、xdist groupだけなので、skip markerやhold opt-inはdigestへ入らない。
[反証シナリオ] 同一 tip、同一 digestの三走のうち、一走だけ `IZANAGI_RUN_GROWTH_HELD_TESTS=explicit-user-command` なら、その走だけ五 nodeとfixtureが実行される。計画上は同値走に見えるがcritical frontierは反転する。
[この所見が誤りである場合の条件] baselineとpostの両方でhold環境を明示的にunsetへ固定し、その状態をartifactへ保存、検証する場合。hold解除状態を主張するなら、別母集合として同様に固定する必要がある。

[所見 11] 親は mixed-tip corpus を current-tip 主張へ使っており、規律7に対して段2計画の方が整合的である
[分類] consistency
[根拠] `measurements.md:98-106` は「同一 tip・同一混雑度での比較にはこの corpus はそのままでは使えない」「corpus は tip 混成」と明記する。それでも `parent-findings.md:179-188` は「現行 tip (hold 有効)」の1位、2位を断定する。一方 `s2-plan.md:273-283` は corpus の記述統計とcurrent-tip同定を分け、同:287-288も mixed-tip と digest固定の必要を明記する。
[反証シナリオ] 時刻上はhold着地後でも、artifactが一つ前のtested-mainや異なるduration ledgerを走らせていれば、直近四走のfrontierを現行tipへ移せない。
[この所見が誤りである場合の条件] 各対象 artifact のreceiptが同じcurrent tested tip、同じledger、同じhold状態を証明し、同一tip反復として再集計できる場合。

[所見 12] report v2 観測は性能測定走に残り、規律1の trace-disabled 分離を満たさない
[分類] consistency
[根拠] `brief.md:30` は「解析は既存 artifact の事後読取だけ。計測系へ観測を差し込まない」とする。対して `s2-plan.md:79-120` は全TestReportのstart/stop、worker、session milestoneを恒久reportへ追加し、同:210-221はそのinstrumentation tipでfull K=3を3走する。`xdist/dsession.py:326-341` はcontrollerが `pytest_runtest_logreport` hookを同期実行した後、別eventでscheduler completionを処理するため、追加処理はevent消費と補充時刻へ作用し得る。
[反証シナリオ] controllerで18,900 phase recordを正規化する処理がevent queueを詰まらせ、空いたworkerへの次unit配布を遅らせれば、観測対象のworker slackそのものが変わる。before/post両方に残すだけでは無観測wallへの外的妥当性を証明しない。
[この所見が誤りである場合の条件] 診断走と性能走を分離し、性能側ではhook、payload、event、validationを完全に除去するtrace-disabled経路を用いる場合。

[所見 13] skip、deselect、case縮小、assertion変更、timeout緩和が段2の短縮案へ紛れているという疑義は反証される
[分類] consistency
[根拠] `s2-plan.md:248-252` は介入を「その routine の自然な所要だけを短縮する、受理集合不変の介入」と限定し、「focus 走は証拠に数えない」とする。同:265-269もfull wall、target外変動、collection digest、worker数で判定する。既存 shard deselect と `growth_test_holds` のskipは観測対象として明示されており、新設または拡大の提案ではない。
[反証シナリオ] 将来の実装がT-080のparametrize caseを減らしたり、candidate nodeを追加holdしたりすれば規律2違反になるが、その操作は現プランには書かれていない。
[この所見が誤りである場合の条件] 「自然な所要の短縮」の具体化で、実際にskip、deselect、case、assertion、timeout、refusal文字列、観測例外のいずれかを変更した場合。

[所見 14] 段2の因果確認部分がD1260、D357を破るという疑義は、hold pin不足を除けば反証される
[分類] ruling-conflict
[根拠] `s2-plan.md:210-212` は同一条件のfull K=3を逐次3走、同:252-269はbeforeを3走、postを3走、中央値差、`ΔW / M0 < 0.10` を変化なし、focus走を証拠外とする。これは `verbatim/rulings.md:10-20` と同:26-29の3走、中央値、10%未満、full wall要件に一致する。
[反証シナリオ] focus nodeだけが50%短縮してもfull中央値が5%しか動かなければ、計画式は正しく「変化なし」とする。D1260と同じcache-hit代用にはならない。
[この所見が誤りである場合の条件] 実行時にAの構造判定だけで因果同定を確定する、focus走を採用する、各条件3走未満にする、中央値以外を主判定にする場合。

[所見 15] `node_execution` の整合検査は同じproducer値の再比較が多く、虚偽worker mappingを検出できない
[分類] tautology
[根拠] `s2-plan.md:102-109` はworkerがoccupancy keyにあること、worker別件数一致、loadgroupと`group_to_workers`一致を検査する。しかし現producerは `tools/acceptance_shards.py:973-992` で同じ `_REPORT_WORKERS` から `normalized_workers`、`worker_occupancy`、`group_to_workers` をすべて生成する。計画の `node_execution` も同:98で同じTestReport情報から作る。
[反証シナリオ] 全selected nodeを偽の`gw0`へ割り当て、同じ偽値からoccupancyとgroup mappingを再生成すれば、key、件数、group整合はすべて通るが、実際の48 worker配置は失われる。実mapping stubと全gw0 stubの両方が通る。
[この所見が誤りである場合の条件] WorkerControllerのdispatch eventなど独立な情報源から期待mappingを作り、producer側TestReport mappingとの不一致を拒否する場合。

[所見 16] wall分解の閉式は補集合の定義により恒真、またはprefixとsuffixを二重計上する
[分類] tautology
[根拠] `s2-plan.md:68-73` はzero-active intervalを「全 worker の setup/call/teardown interval の和集合の補集合」と定義する。同:240-246は `W = prefix + phase interval union + zero-active gaps + suffix` の一致を観測漏れ検査に使う。補集合を最初のsetupから最後のteardownの間に限定すれば式は定義上常に成立し、session全体の補集合ならprefixとsuffixを二重に足す。
[反証シナリオ] 30秒のphase eventを欠落させるとphase unionは30秒減るが、補集合gapが30秒増えるためwall式はそのまま閉じる。完全trace stubとphase欠落stubの双方が通る。
[この所見が誤りである場合の条件] zero-activeを補集合計算ではなく独立なworker activity counterまたはscheduler eventから測り、期待event数とphase coverageも別に検証する場合。

[所見 17] baseline slack `S_u` は候補固有量でなく、単一routineを選別できない
[分類] tautology
[根拠] `s2-plan.md:224-232` の `S_u` は `min(critical-worker lead, critical-shard lead)` の中央値で、uへの依存は「critical chain 上にない走では0」だけである。同:236-238はこの値から全候補、複数候補、exactly oneを判定するが、同じcritical chain上のroutineはすべて同じ値になる。候補集合の完全な列挙規則もないため、空集合なら「全候補で10%未満」が空虚に真となる。
[反証シナリオ] routine Aが60秒、続くroutine Bが60秒で同じcritical workerにあり、worker leadが50秒なら、AとBの両方に`S_u=50`が付く。候補集合をAだけにすればexactly one、AとBにすればfrontierとなり、artifactではなく候補列挙者が結論を決める。
[この所見が誤りである場合の条件] 候補集合を実行traceから完全かつ機械的に生成し、各uについて少なくとも`min(U_u, worker lead, shard lead)`のようなroutine固有の限界と介入結果を使う場合。

[所見 18] 二時点だけから「collectionは非線形に増え、床で最も速く伸びる」とする一般化は成立しない
[分類] measurement-validity
[根拠] `parent-findings.md:151-158` は2026-08-18と2026-08-29の二点だけを比較し、「床は件数に線形ではなく、それより速く伸びている」「床は受入 wall の中で最も速く伸びている項」と結論する。後者の時点だけでもwarm 11.37秒、cold 42.78秒というcache依存幅がある。
[反証シナリオ] 期間中に高価なcollection hookが一度追加され、その後item数を増やしても費用が一定なら、二点では2.79倍に見えても件数に対する超線形成長ではない。cold cacheやfilesystem状態の差でも同じ二点になる。
[この所見が誤りである場合の条件] 同じ実装と環境でitem数だけを複数水準へ操作した測定が超線形曲線を示し、他のwall構成項も同じ期間と条件で測ってcollection床の増加率が最大だと確認された場合。

## 総括

real: 2〜12、15〜18。refuted: 1、13、14の疑義。
最大の不確実性: nodeid→workerとphase timelineがなく、hold on/offもtested tipも揃っていないため、現行tipの実critical frontierは未同定。
静的検査のみで、pytestや新規性能測定は実行していない。