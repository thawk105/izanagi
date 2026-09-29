## 対応表 (所見・状態・根拠 file:行)

| 所見 | 状態 | 根拠 |
|---|---|---|
| 1. 原因の切り分け | **closed** | [README.md:19](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-ccbench-cicada-bugfix/output/insights/2026-09-29/ccbench-cicada-bugfix/README.md:19)、[同:127](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-ccbench-cicada-bugfix/output/insights/2026-09-29/ccbench-cicada-bugfix/README.md:127) は原因を未特定と明記。[result-DIAG.json:10666](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-ccbench-cicada-bugfix/output/insights/2026-09-29/ccbench-cicada-bugfix/verbatim/evidence/result-DIAG.json:10666)・[同:10714](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-ccbench-cicada-bugfix/output/insights/2026-09-29/ccbench-cicada-bugfix/verbatim/evidence/result-DIAG.json:10714) の観測範囲に収まる。 |
| 2. integrity の対象 | **closed** | [README.md:102](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-ccbench-cicada-bugfix/output/insights/2026-09-29/ccbench-cicada-bugfix/README.md:102) は結果のある14走行に限定。残る2走行は [result-ALL.json:5336](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-ccbench-cicada-bugfix/output/insights/2026-09-29/ccbench-cicada-bugfix/verbatim/evidence/result-ALL.json:5336)・[同:5467](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-ccbench-cicada-bugfix/output/insights/2026-09-29/ccbench-cicada-bugfix/verbatim/evidence/result-ALL.json:5467) で `rc=-6`、`summary=null`。 |
| 3. job 数 | **closed** | [README.md:121](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-ccbench-cicada-bugfix/output/insights/2026-09-29/ccbench-cicada-bugfix/README.md:121) は「独立した2 job・計3回の走行」と記載。 |
| 4. 8 genome と実測範囲 | **closed** | [README.md:19](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-ccbench-cicada-bugfix/output/insights/2026-09-29/ccbench-cicada-bugfix/README.md:19)・[decisions:17](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-ccbench-cicada-bugfix/docs/spool/decisions/2026-09-29-worktree-dev-wave-ccbench-cicada-bugfix-1.md:17) は、異常を観測した1設定と、安全側の判断による8設定の除外を区別している。 |
| 5. 計算 job の失敗 | **closed** | [README.md:101](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-ccbench-cicada-bugfix/output/insights/2026-09-29/ccbench-cicada-bugfix/README.md:101)・[同:151](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-ccbench-cicada-bugfix/output/insights/2026-09-29/ccbench-cicada-bugfix/README.md:151) に job `rc=1` と異常終了2走行の内訳を記録。 |
| 6. 160 field の内訳 | **closed** | [README.md:22](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-ccbench-cicada-bugfix/output/insights/2026-09-29/ccbench-cicada-bugfix/README.md:22)・[同:139](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-ccbench-cicada-bugfix/output/insights/2026-09-29/ccbench-cicada-bugfix/README.md:139) は rc・offset 以外の field も明示。単独10段×4、系列20段×6は [patch-apply-G.json:4](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-ccbench-cicada-bugfix/output/insights/2026-09-29/ccbench-cicada-bugfix/verbatim/evidence/patch-apply-G.json:4)・[同:66](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-ccbench-cicada-bugfix/output/insights/2026-09-29/ccbench-cicada-bugfix/verbatim/evidence/patch-apply-G.json:66) と合う。 |
| 焦点再確認・新所見1：macro 数 | **closed** | [README.md:21](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-ccbench-cicada-bugfix/output/insights/2026-09-29/ccbench-cicada-bugfix/README.md:21) は「含む計4つ」に修正され、[同:132](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-ccbench-cicada-bugfix/output/insights/2026-09-29/ccbench-cicada-bugfix/README.md:132) の4つの列挙と一致。 |
| 焦点再確認・新所見2：記録間の言い過ぎ | **closed** | [decisions:17](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-ccbench-cicada-bugfix/docs/spool/decisions/2026-09-29-worktree-dev-wave-ccbench-cicada-bugfix-1.md:17)・[worklog:31](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-ccbench-cicada-bugfix/docs/spool/worklog/2026-09-29-worktree-dev-wave-ccbench-cicada-bugfix-3.md:31) は、重複登録を戻した確認を YCSB K・R、計装なしの確認を TPC-C に限定した。 |

## 新しい所見

なし。修正で新たに生じた言い過ぎ、数値の誤り、3記録間の食い違いは、指定された証拠との照合では見つからなかった。

## 判定 (GO)

段7の6所見と焦点再確認の新所見2件は、すべて **closed**。記録修正を受理できる。

## 総括

原因は未特定とされ、実測範囲と安全側の除外判断も区別された。16走行中2走行の異常終了、診断での巡回数と `TRACE=0` の異常終了、160 field の内訳は、修正後の記述と整合する。