## 計測境界

残差は次で再計算できる。

`R = JUnit testsuite@time - max(report.worker_occupancy[*].duration_s)`

| shard | scheduler start | JUnit timestamp | start差 | JUnit time | 最遅 busy-time | 残差 |
|---|---:|---:|---:|---:|---:|---:|
| 0 | 21:06:11 | 21:06:15.128806 | 4.129 s | 160.920 s | 101.696816 s | 59.223184 s |
| 1 | 21:07:06 | 21:07:11.371515 | 5.372 s | 123.215 s | 74.176111 s | 49.038889 s |
| 2 | 21:01:43 | 21:01:50.353250 | 7.353 s | 146.192 s | 96.635016 s | 49.556984 s |

境界の意味は次のとおり。

| 証拠 | 測る境界 | 測らないもの |
|---|---|---|
| JUnit `testsuite@timestamp` | pytest session の開始 wall clock | scheduler start、worker ready、collection完了 |
| JUnit `testsuite@time` | session開始からJUnit側のsession終了cutoffまで | scheduler queue、job開始前、JUnit cutoff後のrunner処理 |
| receipt `scheduler_logs.stderr.tail` の `Started/Ended Request Time` | compute jobの外側開始・終了。秒粒度 | pytest内部の各phase |
| artifact `mtime` | shared FS上でartifactが確定した時刻。現物は秒粒度 | producer内部の論理イベント、同一秒内の順序 |
| `worker_occupancy.duration_s` | workerに帰属した各test report durationの和 | worker生存時間、collection、process起動、controller prewarm、test間idle、session finalization |

JUnit値は [shard-0 junit.xml](/work/1/SFC/tanab/.izanagi-acceptance-shards/40fc419debb24c1345a03f83238d0d98/shard-0/junit.xml:1)、[shard-1 junit.xml](/work/1/SFC/tanab/.izanagi-acceptance-shards/40fc419debb24c1345a03f83238d0d98/shard-1/junit.xml:1)、[shard-2 junit.xml](/work/1/SFC/tanab/.izanagi-acceptance-shards/40fc419debb24c1345a03f83238d0d98/shard-2/junit.xml:1) のroot fieldから取得した。scheduler accountingは各receiptの `scheduler_logs.stderr.tail`、例として [shard-0 receipt](/work/1/SFC/tanab/.izanagi-acceptance-shards/40fc419debb24c1345a03f83238d0d98/shard-0/dispatch/shard-0/receipt.json:81) にある。

receiptの `queue_wait_s` や `state_history` の最初の `RUN` はscheduler accounting startと同じ境界ではない。例えばshard-0は `queue_wait_s=5.253` だが、accounting上は作成21:01:37、開始21:06:11である。[receipt line 49](/work/1/SFC/tanab/.izanagi-acceptance-shards/40fc419debb24c1345a03f83238d0d98/shard-0/dispatch/shard-0/receipt.json:49) をcompute開始時刻の代用にはしない。

`worker_occupancy`についてはコードで確定できる。controllerが受けた `report.duration` をnodeごとに加算し、さらにworkerごとに合計しているだけである。[acceptance_shards.py:862](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t1934-acceptance-residual/tools/acceptance_shards.py:862)、[acceptance_shards.py:976](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t1934-acceptance-residual/tools/acceptance_shards.py:976)、[acceptance_shards.py:983](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t1934-acceptance-residual/tools/acceptance_shards.py:983)。したがって名称にかかわらず、これはbusy-time和であり、scheduler idleは残差へ入る。

## 4成分分解

| 成分 | 現物からの同定 | 結論 |
|---|---|---|
| collection | 各compute shardで48 workerすべてが全universeをcollectionし、deselect後の担当集合を得る。reportには同一digestが48個ある。[run_tests.py:1460](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t1934-acceptance-residual/tools/run_tests.py:1460)、[acceptance_shards.py:825](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t1934-acceptance-residual/tools/acceptance_shards.py:825)、[acceptance_shards.py:928](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t1934-acceptance-residual/tools/acceptance_shards.py:928) | 実行されたことと48 worker一致は同定。開始・終了timestampがなく、durationは非同定 |
| worker起動 | runner logに `created: 48/48 workers` と `48 workers [...]` が順序証拠としてある。例: [shard-0 log:6](/work/1/SFC/tanab/.izanagi-acceptance-shards/40fc419debb24c1345a03f83238d0d98/shard-0/dispatch/shard-0/izdw-shard-0.o950369:6) | 行timestampがなく、process生成、import、worker collectionを分離不能 |
| prewarm | controllerだけがconsumer検出時に同期実行し、一度実行後は再実行しない。[conftest.py:769](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t1934-acceptance-residual/orchestrator/tests/conftest.py:769)、[conftest.py:825](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t1934-acceptance-residual/orchestrator/tests/conftest.py:825)、[conftest.py:2149](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t1934-acceptance-residual/orchestrator/tests/conftest.py:2149) | shard-0だけreceipt consumer 36 node、oracle consumer 28 node。shard-1/2は双方0。発火有無は同定、durationは非同定 |
| finalization | reportはcontrollerの `pytest_sessionfinish` で生成される。[acceptance_shards.py:955](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t1934-acceptance-residual/tools/acceptance_shards.py:955)。JUnit/report mtimeは各shardで同じ秒 | JUnit cutoff後のrunner summary差は0.320/0.315/0.318秒。最後のtest完了からJUnit cutoffまでの内部finalizationはtimestamp欠如で非同定 |

prewarmありshard-0と、なしshard-1/2の残差差はそれぞれ10.184秒、9.666秒である。ただしこれは因果効果でも上限でもない。割付、node、collection、worker起動、scheduler idleが異なる非paired比較だからである。同定できるのは「prewarmがなくても49.039/49.557秒の残差が残る」ことだけで、prewarmは共通約49秒の必要原因ではない。

さらに4成分は直列加算できない。prewarmは最初の該当 `pytest_xdist_node_collection_finished` hook内で走るため、他workerのcollectionと重なり得る。worker起動と各worker collectionも並行する。また最大busy-time workerが最後に終了したworkerである証拠もない。従って残差には少なくとも次が混在する。

- worker起動、collection、controller prewarmの重なったcritical-path部分
- test間のxdist scheduler idleやprotocol外待ち
- `max busy-time worker` と実際の最終workerが異なることによる差
- 最後のtest後からJUnit cutoffまでの内部finalization

login側独立collectionは別物である。[run_tests.py:1402](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t1934-acceptance-residual/tools/run_tests.py:1402) がplugin specを除去した単独 `--collect-only` を起動し、compute側は48 workerごとに全collectionする。login collectionは [login-collection.log:17506](/work/1/SFC/tanab/.izanagi-acceptance-shards/40fc419debb24c1345a03f83238d0d98/login-collection.log:17506) で17455件、7.98秒。dispatch processを全てstartしてから並行実行される構造である。[acceptance_shards.py:1305](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t1934-acceptance-residual/tools/acceptance_shards.py:1305)、[acceptance_shards.py:1335](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t1934-acceptance-residual/tools/acceptance_shards.py:1335)。

現物ではlogin log mtimeが21:01:44で、最初のcompute JUnit session開始21:01:50.353より前である。shard-2 compute jobとは一部併走し、shard-0/1のqueue待ちとも併走した。このsessionではcritical pathへ載っていない。

## 最大成分と識別可能性

最大成分は一意に決められない。

親briefのP1は確認され、さらに「4成分モデルだけでは閉じない」と強化される。scheduler idleが第五の混入項であり、busy-time最大workerとcritical workerの同一性も証明されていない。

P2は一部だけ支持される。

- JUnit cutoff後のrunner処理は約0.32秒で、scheduler accounting endとの差も秒粒度で約0から0.455秒。ただし、これは最後のtestからJUnit cutoffまでを含むfinalization全体の上限ではない。
- prewarmありなしの観測差は約10秒だが、prewarm costの同定値や上限ではない。
- 約49秒は「collection、worker起動、idle、内部finalizationの共通bundle」であり、単一の最大成分ではない。

再現性条件も満たさない。これはREADME記載の旧計測tipにおけるK=3の一sessionであり、現行mainで同じ成分が反復した証拠がない。[README.md:5](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t1934-acceptance-residual/output/insights/2026-08-26_t826-acceptance-shard-k3/README.md:5)。したがって局所修理の所有pathも `run_tests.py`、`acceptance_shards.py`、`conftest.py` のいずれかへ一意化できない。

具体的停止条件は以下であり、すべて成立している。

- worker ready、worker collection完了、prewarm開始終了、最後のtest完了のtimestampがない。
- 最後に終了したworkerと最大busy-time workerの対応がない。
- prewarmありなしが割付とnodeを固定したpaired比較ではない。
- 現行mainでの同一成分の反復がない。
- 最大成分を除去する単一所有pathが確定しない。

よって実装差分ゼロで停止する。

## plan v1

1. 上記のfield定義を固定し、JUnit residualを4成分の測定値として扱わず、未観測idleを含む混合量として扱う。
2. 段3 reviewでは、`queue_wait_s`をscheduler startへ代用していないこと、`worker_occupancy`をworker elapsedと解釈していないこと、約10秒差をprewarm因果値と断定していないことを検査する。
3. 最大成分、現行main再現性、局所所有pathの三条件がそろわないため、コード、test、docs、worklogを変更せず終了する。
4. T-1933、重い単体、別成分、恒久計装、新監視基盤、skip/deselect/timeout変更には着手しない。
5. 条件が偽なので、1修理の所有path、正例・負例、paired全受入設計は提案しない。

規律2および、report/JUnit/receipt完全性、selected==finished、shard和==独立collection、scheduler==loadgroup、pytest rc、恒久除外、freeze/oracle gateは一切変更しない。

## 検査計画

本段で行う検査は静的照合だけとする。

- 3 shardのJUnit root fieldとreport `worker_occupancy`から残差を再計算する。
- report現物の `selected==finished`、48 worker digest、`effective_scheduler=loadgroup`、記録上の `pytest_rc=0` を照合する。
- selected総数5819+5818+5818=17455と、login独立collection 17455、merged JUnit `tests=17455` を照合する。
- runner log、scheduler accounting、artifact mtimeはそれぞれ異なる境界として扱う。
- 差分ゼロのためpytest/build、正例・負例、paired全受入は実行しない。

ここでのrcや件数は既存artifactの記録であり、本段でテストを実走して得た結果ではない。

## 総括

約49秒の共通残差は確認できるが、最大の単一成分ではなく、collection、worker起動、scheduler idle、内部finalizationの非識別bundleである。shard-0のprewarmあり差は約10秒だが因果同定できず、login独立collectionはこのsessionのcritical pathには載っていない。

最大成分、再現性、局所修理の三条件を満たさないため、T-1934は実装差分ゼロで停止する。pytest/buildは未実行で、コード、docs、Git状態は変更していない。