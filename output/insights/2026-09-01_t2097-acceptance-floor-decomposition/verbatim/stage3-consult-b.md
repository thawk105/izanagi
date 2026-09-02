## 総括

親の「床は 126.13 秒 + 87.8 秒で、87.8 秒は排他待ちではない」という帰属は支持されない。126.13 秒は単走の下界だが、87.8 秒は原因別に分解されていない slack である。  
JUnit は setup / call / teardown を全て含む一方、外側 protocol hook での lock 取得待ちは含まない。したがって P2 は棄却すべきである。  
固定 duration・shard-0 固有費不変なら短縮上限は約 9.54 秒で親の 7.8 秒に近い。固有費 21.9 秒も消えるなら約 31.4 秒で段 2 上端に近いが、既存 artifact ではどちらか判定できない。  
静的検査と既存 artifact の読取りだけを行い、新しいテスト・実測は実行していない。

## 数値の作り方の欠陥

1. **台帳 9610.0 秒と実走 wall の混用**

   - [HANDOFF.md:43](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2097-exclusion-closure-split/HANDOFF.md:43) の `9610/(48×3)=66.7` は歴史的台帳からの値であり、08:15 実走の仕事量ではない。
   - 実走の testcase 合計は 12548.9 秒なので、同じ走の容量下界は `12548.9/(48×3)=87.15` 秒である。
   - 現在の selected 19215 node に対する台帳 exact-key 被覆は 17571 node、91.44%。被覆外 node の実走時間だけで約 2052.6 秒ある。
   - 代表例では最長 node が台帳 55.0 秒 [ledger:12460](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2097-exclusion-closure-split/orchestrator/tests/acceptance_duration_ledger.json:12460) に対し実走 126.133 秒で、2.29 倍である。
   - 正しい同走比較でも `87.15 < 126.13` は維持されるため、最大単体が容量下界を上回るという結論自体は変わらない。ただし、それだけでは「割付を変えても実 wall が動かない」とは言えない。

2. **歴史的 group 合計と実走最長 node の比較**

   - 親は台帳 group 合計 83.5 / 52.0 / 16.0 秒を、実走最長 126.13 秒と比較している。
   - 同じ実走で集計すると `campaign-repository-scan=0`、`dev-waves-runtime=15.428`、`s8c-predicate-snapshot=67.873`、`s8c-preregistration-candidate=0` 秒である。これらが 126.13 秒未満という結論は変わらない。
   - ただし台帳の writer 0.19 秒は、その走の lock 待ちを表さない。短い writer 自身が長い reader 群の解放を待つ時間は protocol 外なので、この値から排他待ちを否定できない。

3. **JUnit `time` の範囲**

   - 実走は pytest 9.1.1 [stdout:2](/work/1/SFC/tanab/.izanagi-acceptance-shards/349543d56cdc8d141798abb3626121e9/shard-0/dispatch/shard-0/izdw-shard-0.o963739:2)。
   - repository の [pytest.ini:12](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2097-exclusion-closure-split/pytest.ini:12) は `junit_duration_report` を上書きしていない。
   - pytest 9.1.1 の既定は `total` [junitxml.py:410](/home/SFC/tanab/.local/lib/python3.10/site-packages/_pytest/junitxml.py:410) で、各 report の `when` が setup / call / teardown の全てについて duration を加算する [junitxml.py:624](/home/SFC/tanab/.local/lib/python3.10/site-packages/_pytest/junitxml.py:624)。
   - よって setup / call / teardown の省略で説明される残差は **0 秒**。5816.6 秒は三 phase の合計である。ただし worker の生存時間全体ではない。

4. **87.8 秒の正しい記述的分解**

   同じ artifact では次のように分けられる。

   - 最長 node: 126.133 秒
   - shard-0 最大 worker の report 累積: 135.676 秒
   - pytest wall: 213.91 秒
   - 最長 node 後の同一 worker 上の report 時間: `135.676-126.133=9.543` 秒
   - report 外の差: `213.91-135.676=78.234` 秒
   - shard-1/2 の report 外差の平均: 約 56.337 秒
   - shard-0 固有の report 外差: `78.234-56.337=21.897` 秒

   したがって `87.777 = 9.543 + 56.337 + 21.897` は記述的には成立する。ただし 56.337 秒を collection / worker 起動、21.897 秒を負荷由来とする因果分解ではない。

5. **LPT と makespan 下界の混同**

   - [parent-measurements.md H:225](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2097-exclusion-closure-split/materials/parent-measurements.md:225) の 4183.0 秒は実走 JUnit 由来なので、ここ自体に台帳との混用はない。
   - `total/3=4182.97` が下界であり、LPT の結果は通常は構成した割付の上界である。本件では両者がほぼ一致した、という扱いが正しい。
   - さらに `/48=87.1` と最長 node 126.1 の比較は、worker 内 packing、group、protocol lock、report 外時間を除いた下界でしかない。
   - 現行最大 worker の report 累積は 135.676 秒なので、固定 duration でも 126.133 秒まで約 9.54 秒の余地が残る。「makespan は 1 秒も動かない」は強すぎる。

6. **`wall = 最長 node + 87.8`**

   - 残差を `wall-最長 node` と定義すれば代数的な等式だが、critical path の分解式ではない。
   - 最長 node の開始時刻、最終終了 worker、lock 待ち、scheduler gap の時系列が artifact にないため、87.8 秒を独立な固定費として足す根拠はない。
   - また 213.91 秒は shard-0 の pytest wall であり、job Elapse は 227 秒 [dispatcher.log:36](/work/1/SFC/tanab/.izanagi-acceptance-shards/349543d56cdc8d141798abb3626121e9/shard-0/dispatcher.log:36)。D1320 の job/session 層まで含む「受入 wall」の等式ではない。

7. **親 7.8 秒対、段 2 の 20〜32 秒**

   - 固定 duration と shard-0 の report 外差 78.234 秒が不変なら、理想値は約 `126.133+78.234=204.37` 秒、短縮上限は **9.54 秒**。親の 7.8 秒は粗い残差 80 秒を置いた近似としてはこちらに近い。
   - shard-0 固有 21.897 秒が全て消えるなら、約 `126.133+56.337=182.47` 秒、短縮は **31.44 秒**。段 2 の上端はこちらの仮定である。
   - 段 2 の約 21 秒という容量換算は、移動可能仕事量を 48 で割った値だが、現行 `5816.6/48=121.2` は既に最長 node 126.1 より小さい。したがって約 21 秒を wall 短縮へ直接計上できない。
   - 結論は **どちらも単走からは支持されない**。固定 duration の静的モデルでは親側が近いが、実効果の判定ではない。

## 測れていない量

- [conftest.py:2068](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2097-exclusion-closure-split/orchestrator/tests/conftest.py:2068) の wrapper は、[conftest.py:2083](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2097-exclusion-closure-split/orchestrator/tests/conftest.py:2083) で `_real_repo_locks()` を取得してから内側 protocol へ `yield` する。したがって取得待ちは setup report より前である。
- cross-process の実待ちは [conftest.py:1155](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2097-exclusion-closure-split/orchestrator/tests/conftest.py:1155) の EAGAIN 再試行、same-process 待ちは [conftest.py:1220](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2097-exclusion-closure-split/orchestrator/tests/conftest.py:1220) の condition wait で起きる。現在の monotonic 値は deadline 判定にしか使われず、成果物へ記録されない。
- `report.json` も [acceptance_shards.py:862](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2097-exclusion-closure-split/tools/acceptance_shards.py:862) で setup / call / teardown の `TestReport.duration` を加算するだけで、同じ lock 待ちを含まない。
- よって「残差 87.8 秒は排他待ちではない」は実測で支持されていない。shard-2 に約 56 秒あることは共通 report 外費用の存在を示すだけで、shard-0 固有約 22 秒に lock 待ちがないことを示さない。
- controller prewarm も [conftest.py:2088](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2097-exclusion-closure-split/orchestrator/tests/conftest.py:2088) で test protocol 前に実行され、未計時である。提案対象 file を分割しても、receipt consumer は `test_s8b_oracle_driver.py` に残る [conftest.py:610](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2097-exclusion-closure-split/orchestrator/tests/conftest.py:610) ため、prewarm が shard-0 から消えるとは限らない。

最小計測は、EAGAIN 再試行と condition wait の実待ちだけを `monotonic` で累積し、node / resource / mode / protocol-or-prewarm 別に artifact へ出すこと。既存 JUnit と report だけでは足りない。原因を粗く二分するだけなら lock context 進入前後の差でもよいが、Git path 解決や uncontended syscall を混ぜるため、排他待ちの確定には再試行箇所の計時が必要である。

## 一般化の限界

単走では支えられない主張は次のとおり。

- 126.13 秒が今後も固定した最長単体床であること。
- 87.8 秒、80 秒、56 秒のいずれかが不変な固定費であること。
- shard-0 固有 21.9 秒が負荷により生じ、細分化で消えること。
- 逆に、その 21.9 秒が負荷と無関係で残ること。
- protocol lock 待ちが無いこと。
- file 細分化の効果が 0、7.8、20、32 秒のいずれかになること。
- 現行 duration を再配置しても各 node の duration が不変であること。
- pytest wall の分解を job Elapse や session 合計へ一般化すること。

親が追記した [parent-measurements.md F:131](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2097-exclusion-closure-split/materials/parent-measurements.md:131) の 14 session は、単走より強い記述的証拠である。各 session の `shard-*/junit.xml`、`report.json`、`dispatcher.log`、`dispatch/shard-*/request.json` を見ると、selected digest は同一だが tested tip は 7 種類にまたがる。観測結果は次のとおり。

- report 外差の中央値は shard-0 77.21 秒、shard-1 56.38 秒、shard-2 56.62 秒。
- shard-0 固有差は中央値 20.29 秒、範囲 18.86〜27.85 秒で、複数走でも再現する。
- shard-0 最長 node は 118.6〜219.3 秒まで動き、126.13 秒は固定床ではない。
- この 14 走には細分化後の B arm がないため、固有差が負荷原因か固定処理かは判定できない。lock 待ちも全走で未記録である。
- 主 artifact 自体も現 HEAD `1d2706f9` ではなく、`tested_main=78991963...` [request.json:1](/work/1/SFC/tanab/.izanagi-acceptance-shards/349543d56cdc8d141798abb3626121e9/shard-0/dispatch/shard-0/request.json:1) である。

段 2 の A/B 設計は **効果量 8〜32 秒の検出には不十分**。同一 K=3・48 worker、同一 tip、同一 selected digest の paired 化は必要だが、「32 秒より小さい差では採らない」という規則では 8〜32 秒の仮説を原理的に採れない。D1019 の 32.27 秒は K=2 の二走間差 1 個であり、分散推定や検出閾値ではない。複数の順序を反転・無作為化した A/B pair を取り、paired 差の分布と区間を出す必要がある。必要 pair 数は現時点では推定不能である。

## 親 brief と段 2 プランへの異議

1. **親 P1:** 「数学的下界 126.1 秒は細分化で下がらない」は成立するが、「実 wall / makespan は動かない」への拡張は成立しない。現行 report 累積だけでも約 9.54 秒の packing 余地がある。
2. **親 P2:** 棄却。[HANDOFF.md:99](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2097-exclusion-closure-split/HANDOFF.md:99) の「shard-2 に残差があるから shard-0 も排他待ちではない」は論理的に成立しない。実際、shard-0 には全走で約 19〜28 秒の追加差がある。
3. **親の前提 5〜7:** 台帳 group / cohort / 総量と単走 JUnit / wall を混ぜている。同走値へ置換しても最大単体下界は残るが、lock 待ち否定と makespan 不変は残らない。
4. **親 H:** `LPT で下界` という表現、残差 80 秒の固定、下界と実 wall の同一視に異議がある。7.8 秒は条件付きシナリオである。
5. **段 2 の床帰属:** 「約 56 秒は共通費らしい」「21.9 秒は未計測」という記述は妥当。ただし 56 秒を固定費、21.9 秒を細分化で消える費用として期待値へ使うことはできない。
6. **段 2 の 20〜32 秒:** 下端 20 秒は非拘束な容量差を wall に計上しており、上端 32 秒は未計測の shard-0 固有差が全消滅する仮定である。いずれも既存 artifact で支持されない。
7. **段 2 の A/B 採否:** paired という方向は正しいが、単一 pair と 32 秒閾値では対象効果を検出できない。複数 pair と lock/prewarm 計時が必要である。