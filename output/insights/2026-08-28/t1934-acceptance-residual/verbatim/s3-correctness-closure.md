## 所見

1. **High — plan v1のwave終了手順は契約違反**

   - **file:line:** [plan.md:73](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t1934-acceptance-residual/s2/plan.md:73)、[plan.md:79](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t1934-acceptance-residual/s2/plan.md:79)、[plan.md:93](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t1934-acceptance-residual/s2/plan.md:93)、[dev-wave.md:48](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t1934-acceptance-residual/.claude/commands/dev-wave.md:48)、[core.md:93](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t1934-acceptance-residual/docs/dev-wave/core.md:93)、[core.md:101](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t1934-acceptance-residual/docs/dev-wave/core.md:101)、[operations.md:91](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t1934-acceptance-residual/docs/dev-wave/operations.md:91)。
   - **論証:** 「実装しない」裁定が省略できるのは段5・6だけで、遷移は `4→7→8→9`。差分ゼロで免除されるのも変異matrixだけで、受入全走は明文で免除されない。段7はworklog等の記録とcommitを要求し、最終受入はその記録commit後でなければならない。
   - **成果物影響:** 記録を残さなければ非識別理由、実装しない裁定、未実走事項がdurable artifactにならない。最終受入を省けばtested tipが成立せず、段9のland入力も固定できない。
   - **scope:** T-1934内。plan v2で必須修正。

2. **Medium — 対象量が`pytest wall`からJUnit session残差へすり替わっている**

   - **file:line:** [s1-brief.md:3](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t1934-acceptance-residual/s1-brief.md:3)、[plan.md:5](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t1934-acceptance-residual/s2/plan.md:5)、[plan.md:17](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t1934-acceptance-residual/s2/plan.md:17)、[plan.md:59](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t1934-acceptance-residual/s2/plan.md:59)、[run_tests.py:1527](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t1934-acceptance-residual/tools/run_tests.py:1527)。
   - **論証:** planの59.223/49.039/49.557秒は `testsuite@time - max(observed report duration sum)` であり、briefが要求したpytest process wallではない。JUnit開始前とcutoff後のpytest内部時間を同じ時計で測るfieldがないため、既存証拠から正確なpytest wall残差へ戻せない。
   - **成果物影響:** 数値は「JUnit session残差」と記録すべきで、「pytest wall残差」や4成分の測定値としては採用不可。これは実装差分ゼロの判断を覆さず、むしろ識別不能を強める。
   - **scope:** 診断と記録はT-1934内。新しい恒久計時はscope外。

3. **Medium — `worker_occupancy`は完全なbusy-timeであることまで証明していない**

   - **file:line:** [acceptance_shards.py:862](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t1934-acceptance-residual/tools/acceptance_shards.py:862)、[acceptance_shards.py:976](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t1934-acceptance-residual/tools/acceptance_shards.py:976)、[acceptance_shards.py:985](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t1934-acceptance-residual/tools/acceptance_shards.py:985)、[acceptance_shards.py:542](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t1934-acceptance-residual/tools/acceptance_shards.py:542)、[plan.md:27](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t1934-acceptance-residual/s2/plan.md:27)。
   - **論証:** producerは有限・非負の`report.duration`だけを加算し、欠落nodeには`unobserved` workerと0秒を与えられる。validatorはworker別item総数とdurationの非負性を検査するだけで、各nodeの全phase duration受領を証明しない。`selected==finished`もlogfinishの一致でありduration完全性とは別である。
   - **成果物影響:** 残差は厳密には「JUnit time − 最大の観測済み有効report duration和」。欠落があれば残差は膨らむ。現物に欠落があるとは本射影から断定できないが、planの検査項目だけでは排除できない。
   - **scope:** 診断上の留保はT-1934内。新しいduration完全性gateや恒久計装はscope外。

4. **Medium — merge単体は`serial`も受理するため、tested-main runner束縛が不可欠**

   - **file:line:** [acceptance_shards.py:503](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t1934-acceptance-residual/tools/acceptance_shards.py:503)、[acceptance_shards.py:679](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t1934-acceptance-residual/tools/acceptance_shards.py:679)、[run_tests.py:1490](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t1934-acceptance-residual/tools/run_tests.py:1490)、[run_tests.py:2433](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t1934-acceptance-residual/tools/run_tests.py:2433)。
   - **論証:** mergeのscheduler gateは全shardが`serial`でも通す。一方、現行production runnerはcomputeでxdist/loadgroupを必須化し、受入形の非loadgroup上書きを拒否する。したがってworker起動短縮としてserialへ倒す案は、mergeが通ってもD838とT-1934不変条件に違反する。
   - **成果物影響:** runner束縛を外すと`effective_scheduler=serial`の受領証を正常受入へ昇格させ得る。
   - **scope:** T-1934では修理しない。loadgroupを弱める修理案の排除根拠としてのみ記録する。

## 修理候補の棄却表

三条件は「最大成分／現行main再現／単一所有path」。`○`が全てそろう候補はない。

| 成分 | 候補と実アンカー | 受理集合・証拠への影響 | 三条件 | 裁定 |
|---|---|---|---|---|
| collection | 二重の`_canonical_item`処理を一回化。[acceptance_shards.py:825](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t1934-acceptance-residual/tools/acceptance_shards.py:825) | byte等価なら集合不変だが、最大時間である証拠がない | ×／×／○ | 局所最適化候補にすぎず棄却 |
| collection | login collectionを権威化してworker全collectionを省く。[run_tests.py:1402](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t1934-acceptance-residual/tools/run_tests.py:1402)、[acceptance_shards.py:928](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t1934-acceptance-residual/tools/acceptance_shards.py:928) | independent collection、48 worker digest、observed universe一致を失う | ×／×／× | 禁止 |
| collection | login独立collection自体を省く。[acceptance_shards.py:661](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t1934-acceptance-residual/tools/acceptance_shards.py:661) | 現物ではcritical path外で、独立collection gateだけを弱める | ×／×／○ | 修理でなく検査削除 |
| worker起動 | internal shardのworker数を48から32等へ下げる。[run_tests.py:1495](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t1934-acceptance-residual/tools/run_tests.py:1495) | test集合は維持可能だがbusy tailとの交換条件が未測定。値も一意でない | ×／×／○ | 棄却 |
| worker起動 | `-n0`、serial、非loadgroup schedulerへ倒す | D838、規律2、loadgroup単一所有を破る。mergeのserial受理を利用してはならない | ×／×／× | 禁止 |
| prewarm | controller prewarmを早期化・非同期化する。[plan.md:35](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t1934-acceptance-residual/s2/plan.md:35) | 集合は同じでもreceipt/oracle readinessとのraceを導入し、freeze/oracle gateを弱め得る。既にcollectionと重なる | ×／×／△ | 棄却 |
| prewarm | cache、skip、consumerの追加deselectで発火を消す | freeze/oracle gate、恒久除外、selection契約を変更する | ×／×／× | 修理扱い禁止 |
| finalization | report正規化ループをbyte等価に最適化。[acceptance_shards.py:955](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t1934-acceptance-residual/tools/acceptance_shards.py:955) | byte等価なら受理集合不変だが、内部finalization最大・現行再現の証拠なし | ×／×／○ | 棄却 |
| finalization | report field、fsync、JUnit mergeを省く。[acceptance_shards.py:235](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t1934-acceptance-residual/tools/acceptance_shards.py:235)、[acceptance_shards.py:1431](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t1934-acceptance-residual/tools/acceptance_shards.py:1431) | report/JUnit完全性とdurabilityを弱める | ×／×／○ | 禁止 |
| finalization | report生成をJUnit cutoff後へ移す | 実wallを短縮せず測定境界だけを移す | ×／×／△ | metric gamingとして禁止 |

追加deselect、selection縮小、timeout延長、恒久計装、新監視基盤、T-1933の重い単体短縮は、いずれもT-1934の局所修理ではない。恒久除外は[run_tests.py:2411](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t1934-acceptance-residual/tools/run_tests.py:2411)、selected exact partitionは[acceptance_shards.py:665](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t1934-acceptance-residual/tools/acceptance_shards.py:665)、selected==finishedは[acceptance_shards.py:672](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t1934-acceptance-residual/tools/acceptance_shards.py:672)のまま固定する。

## wave閉鎖契約

plan v1の契約判定は次のとおり。

| plan v1の扱い | 判定 |
|---|---|
| 最大成分を識別できないため実装差分ゼロ | **妥当** |
| 段5・6を飛ばす | **妥当**。ただし段4でreal/refutedとplan v2を確定した後だけ |
| 正例・負例、変異matrixを作らない | **妥当**。差分ゼロ免除の範囲 |
| before/afterのpaired全受入を行わない | **妥当**。比較対象となる修理がないため |
| generic buildを行わない | **条件付きで妥当**。build対象差分がないため。ただし必要な受入・repo実読テストの代替にはならない |
| pytestを一切行わない | **不整合**。差分ゼロでも受入全走は免除されない |
| docs/worklogを変更しない | **不整合**。段7の記録義務に違反 |
| 段7・8・9を行わず停止 | **不整合**。許される遷移は`4→7→8→9` |

閉鎖に必要なplan v2は以下となる。

1. 段4で「最大成分、現行再現、単一所有pathの三条件なし」を裁定し、実装しないと確定する。
2. 段7前に、契約が要求する実repo読取テストを親が実走する。
3. 段7で非識別理由、JUnit境界、未実走事項、scope外候補をworklog fragmentと必要なinsightへ記録し、記録commitを作る。
4. 記録commit後に影響検査と最終受入全走を行う。paired性能比較は不要だが、最終受入そのものは必要。
5. 最終受入はD838のtested-main runner束縛、規律2、恒久除外、loadgroup、independent collection、selected==finished、freeze/oracle gateを全て維持する。直接pytestや別runnerで代用しない。
6. 段8を一度通す。候補ゼロなら変更なしでよい。
7. 段9で全commit、tested main/tip、受入結果、監査commit列を固定して通常land経路を使う。

本consult段ではpytest、build、受入、Git状態検査は実行していない。コード、docs、Git状態への変更操作も行っていない。

## 総括

実装差分ゼロの裁定は正しい。既存証拠からはcollection、worker起動、prewarm、finalizationのどれも最大成分として一意化できず、現行main再現も単一所有pathもそろわない。

ただし「差分ゼロだからその場で終了」は誤りである。T-1934は段4で実装なしを裁定した後、段7の記録、記録commit後の最終受入、段8、段9まで完遂しなければ閉鎖できない。