## 対応表 (所見・状態・根拠 file:行)

| 所見 | 状態 | 根拠 |
|---|---|---|
| 1. 原因の切り分け | **partial** | [一次資料:19](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-ccbench-cicada-bugfix/output/insights/2026-09-29/ccbench-cicada-bugfix/README.md:19)・[同:127](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-ccbench-cicada-bugfix/output/insights/2026-09-29/ccbench-cicada-bugfix/README.md:127) は観測範囲に限定した。一方、[同:110](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-ccbench-cicada-bugfix/output/insights/2026-09-29/ccbench-cicada-bugfix/README.md:110) は「G の修正が原因でない」「計装が原因でない」と断定し、[同:123](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-ccbench-cicada-bugfix/output/insights/2026-09-29/ccbench-cicada-bugfix/README.md:123) は異常終了を「promotion の経路そのものに由来」と断定する。[診断結果:10666](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-ccbench-cicada-bugfix/output/insights/2026-09-29/ccbench-cicada-bugfix/verbatim/evidence/result-DIAG.json:10666) が示すのは、重複登録を戻しても K・R の巡回が残り、TRACE=0 でも TPC-C が異常終了したことまで。 |
| 2. integrity の対象 | **closed** | [一次資料:102](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-ccbench-cicada-bugfix/output/insights/2026-09-29/ccbench-cicada-bugfix/README.md:102) は結果のある14走行に限定。[本走結果:5336](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-ccbench-cicada-bugfix/output/insights/2026-09-29/ccbench-cicada-bugfix/verbatim/evidence/result-ALL.json:5336)・[同:5467](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-ccbench-cicada-bugfix/output/insights/2026-09-29/ccbench-cicada-bugfix/verbatim/evidence/result-ALL.json:5467) の2走行は `rc=-6`、`summary=null`。 |
| 3. job 数 | **closed** | [一次資料:121](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-ccbench-cicada-bugfix/output/insights/2026-09-29/ccbench-cicada-bugfix/README.md:121) は「独立した2 job・計3回の走行」に修正。 |
| 4. 8 genome と実測範囲 | **closed** | [一次資料:19](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-ccbench-cicada-bugfix/output/insights/2026-09-29/ccbench-cicada-bugfix/README.md:19)・[decisions:17](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-ccbench-cicada-bugfix/docs/spool/decisions/2026-09-29-worktree-dev-wave-ccbench-cicada-bugfix-1.md:17) は、異常の実測が1設定で、8設定の除外は安全側の判断と明記。 |
| 5. 計算 job の失敗 | **closed** | [一次資料:101](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-ccbench-cicada-bugfix/output/insights/2026-09-29/ccbench-cicada-bugfix/README.md:101)・[同:150](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-ccbench-cicada-bugfix/output/insights/2026-09-29/ccbench-cicada-bugfix/README.md:150) に job `rc=1` と異常終了2走行の内訳を追記。 |
| 6. 160 field の内訳 | **partial** | [一次資料:139](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-ccbench-cicada-bugfix/output/insights/2026-09-29/ccbench-cicada-bugfix/README.md:139) は単独10×4、系列20×6の160 field と正しく説明。[patch 適用結果:4](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-ccbench-cicada-bugfix/output/insights/2026-09-29/ccbench-cicada-bugfix/verbatim/evidence/patch-apply-G.json:4)・[同:66](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-ccbench-cicada-bugfix/output/insights/2026-09-29/ccbench-cicada-bugfix/verbatim/evidence/patch-apply-G.json:66) と合う。ただし[一次資料:22](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-ccbench-cicada-bugfix/output/insights/2026-09-29/ccbench-cicada-bugfix/README.md:22) の「rc と offset の有無、160 項目」は内訳を再び誤読させる。 |

## 新しい所見

- **数値の誤り:** [一次資料:21](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-ccbench-cicada-bugfix/output/insights/2026-09-29/ccbench-cicada-bugfix/README.md:21) は未知マクロを「INLINE_VERSION_OPT ほか4つ」とするが、[同:132](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-ccbench-cicada-bugfix/output/insights/2026-09-29/ccbench-cicada-bugfix/README.md:132) の列挙は **計4つ**。
- **記録間の言い過ぎ:** [decisions:17](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-ccbench-cicada-bugfix/docs/spool/decisions/2026-09-29-worktree-dev-wave-ccbench-cicada-bugfix-1.md:17) の「この2つは観測した異常に必須ではない」は対象が広い。重複登録について確認したのは YCSB K・R の巡回、TRACE=0 について確認したのは TPC-C の異常終了である。[worklog:31](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-ccbench-cicada-bugfix/docs/spool/worklog/2026-09-29-worktree-dev-wave-ccbench-cicada-bugfix-3.md:31) も「計装の寄与」を調べたと読めるため、同じ範囲に限定すると整合する。

## 判定 (NO-GO)

所見1の原因断定が一次資料に残り、新しい数値誤りもある。記録の修正後に再判定する。

## 総括

所見2〜5は閉じた。所見1・6は部分対応。3記録の主要な走行数・巡回数は提示された結果と一致するが、原因の言い方と160 field の要約に修正が要る。