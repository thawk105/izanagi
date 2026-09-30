## 1. fix ごとの判定 (closed / partial / regressed と根拠 file:line)

| fix | 判定 | 根拠 |
|---|---|---|
| fix5・verify 受理条件 | **closed** | [受理関数](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-ro-gc-publish/orchestrator/campaign/vhash_ro_gc_publish.py:125) は数値 11 項目を必須の 0 とし、legacy report にない `existence_violations` は 0 として扱い、値があれば 0 を要求する。`stats.txns` も workload の commit 数と照合する。[`Integrity.clean()`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-ro-gc-publish/orchestrator/verifier/model.py:501) と比べて外れた条件は証拠面ゲートだけ。`stats.txns` は判定器の観測 commit 数そのもの（[core.py:61](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-ro-gc-publish/orchestrator/verifier/core.py:61)、[report.py:102](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-ro-gc-publish/orchestrator/verifier/report.py:102)）。rc・巡回・不一致・COUNT の条件も維持されている。 |
| fix6・spawn-site 行番号 | **closed** | [テストの 216 行指定](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-ro-gc-publish/orchestrator/tests/test_ccbench_spawn_sites.py:3605) は、HEAD の [`cmake --build` 呼び出し](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-ro-gc-publish/orchestrator/campaign/vhash_ro_gc_publish.py:216)を指す。分類期待値 4／68 は変わっていない。 |
| fix7・作図値と数表 | **closed** | [paired_values](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-ro-gc-publish/tools/plotting/plot_vhash_ro_gc_publish.py:27) は measure の両 arm の絶対値と throughput の対ごとの比を raw から計算する。[数表](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-ro-gc-publish/tools/plotting/plot_vhash_ro_gc_publish.py:82)も VLIFE を再解析する。stock の公開 0 回に境界年齢を補っていない。 |
| fix8・図の表示と配置 | **closed** | 0 回と未定義は[データ軸と別の帯](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-ro-gc-publish/tools/plotting/plot_vhash_ro_gc_publish.py:205)に表示される。凡例は軸外にあり、[配置検査](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-ro-gc-publish/tools/plotting/plot_vhash_ro_gc_publish.py:257)には凡例とデータ軸の重なり検出が追加された。親の PNG 2 枚を目視し、0 回を約 100 回/s と読む配置や点を隠す凡例は見られなかった。 |

## 2. 派生値の照合

- [verify2.json](/work/SFC/tanab/tmp/vhash-ro-gc-publish-2026-09-29/raw/verify2.json) の **24/24 走**で、rc=3、巡回 0、数値違反 0、`stats.txns` と workload commit 数の一致、READ_WTS_MISMATCH 0、ro commit と flag 立ての正数、受理フラグ true を各走で再確認した。commit 合計は **12,321,579**、flag 立ては **196〜209,933**。`existence_violations` は legacy report の全 24 走で省略されている。
- [measure1.json](/work/SFC/tanab/tmp/vhash-ro-gc-publish-2026-09-29/raw/measure1.json) の VLIFE worker counter から公開回数と境界年齢を再計算し、144 走の summary と一致した。長い ro の stock は **36/36 走で公開 0 回、境界年齢は未定義**。variant は **289〜299 回**。例として S0・長い ro・反復 1 は variant **299 回／3 秒 = 99.67 回/s、境界年齢 14,145.52 µs**。
- [throughput1.json](/work/SFC/tanab/tmp/vhash-ro-gc-publish-2026-09-29/raw/throughput1.json) の 72 対から再計算した。長い ro は **1.5604〜16.8314**。条件別平均は S0 **6.0807**、S50 **3.9645**、S95 **1.5854**、T0 **4.2450**、T50 **16.7407**、T95 **15.4973** で提示値と一致する。
- **長い ro なしの範囲は提示値と不一致**。全 36 対の実値は **0.9643〜1.0734**。T0・反復 3 は **3,431,587 / 3,558,460 = 0.96435**、S50・反復 1 も **0.98367** で、提示下限 0.985 を下回る。
- 図の provenance に記録された measure・throughput raw の SHA-256 は、現在の両 raw と一致した。境界年齢差と ro 保持者割合の数表も worker counter から再計算し、fix8 報告の 6 条件の値と一致した。

## 3. 新しい所見 (重大度 must-fix / should-fix / nit、file:line、放置時に成果物がどう変わるか 1 行、修正案)

- **must-fix — [s6-fix7-ruling.md:9](/work/SFC/tanab/tmp/vhash-ro-gc-publish-2026-09-29/s6-fix7-ruling.md:9)、[throughput1.json:595936](/work/SFC/tanab/tmp/vhash-ro-gc-publish-2026-09-29/raw/throughput1.json:595936)、[同:606200](/work/SFC/tanab/tmp/vhash-ro-gc-publish-2026-09-29/raw/throughput1.json:606200)**：親が一次資料に使う予定の「長い ro なし 0.985〜1.073」は誤り。放置すると最低の対で約 **3.6%** 低下した実測が成果物から落ちる。**修正案：**範囲を **0.964〜1.073** に直し、36 対を対象にした値と明記する。

差分上、fix5〜fix8 が持ち込んだ受理条件の追加の緩み、無関係な既存期待値の変更、恒真のテストは確認しなかった。[作図テスト](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-ro-gc-publish/orchestrator/tests/test_vhash_ro_gc_publish.py:224)は対数軸・欠損表示・系列記号を検査し、[凡例重なりの陰性テスト](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-ro-gc-publish/orchestrator/tests/test_vhash_ro_gc_publish.py:277)も実際の検査関数を通る。

## 4. GO / NO-GO

**fix5〜fix8 の実装統合は GO。一次資料の確定は、throughput 範囲を直すまで NO-GO。** 並行中の焦点走 6 は、このレビューでは結果未確認として扱う。

## 総括

受理条件、sink 行番号、図と数表の再計算、0 回・未定義の表示は意図どおり。修正が必要なのは、親の派生値に残った **0.985 という誤った下限**である。