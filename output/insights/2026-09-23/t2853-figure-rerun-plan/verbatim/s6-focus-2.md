## 総括

**NO-GO。** 前回までの所見は本文上おおむね解消しています。件数と指定された加算値も一致します。ただし、Elapse がない図について、代理値から「2 node 時間未満・確認不要」と確定している箇所が残ります。D2219 の見積り規則に合わせた判定が必要です。

## 対応表

| ID | 判定 | 根拠 |
|---|---|---|
| M1 | closed | fig13 の 18.68 h を待ちを含む投入〜完了の参考値とし、確認を未判定に変更。[計画書](/work/1/SFC/tanab/izanagi/.claude/worktrees/t2853-rerun-plan/output/insights/2026-09-23/t2853-figure-rerun-plan/README.md:29)、[B-10 結果稿](/work/1/SFC/tanab/izanagi/.claude/worktrees/t2853-rerun-plan/docs/paper-story/results/2026-09-20-b10-waiting-grid-formal.md:151)。 |
| M2 | closed | fig4 の 6.37 h を旧機の時間台帳として分離し、Pegasus の見積りを未確定とした。[計画書](/work/1/SFC/tanab/izanagi/.claude/worktrees/t2853-rerun-plan/output/insights/2026-09-23/t2853-figure-rerun-plan/README.md:69)、[S-1a 結果稿](/work/1/SFC/tanab/izanagi/.claude/worktrees/t2853-rerun-plan/docs/paper-story/results/2026-09-20-s1a-nine-pair-direct-comparison.md:141)。 |
| M3 | closed | fig15 を R2 から分け、TRACE=1 の観測の再実施とした。[計画書](/work/1/SFC/tanab/izanagi/.claude/worktrees/t2853-rerun-plan/output/insights/2026-09-23/t2853-figure-rerun-plan/README.md:18)、[図 README](/work/1/SFC/tanab/izanagi/.claude/worktrees/t2853-rerun-plan/docs/paper-story/figures/README.md:1968)、[見積り稿](/work/1/SFC/tanab/izanagi/.claude/worktrees/t2853-rerun-plan/output/insights/2026-09-22/t2853-repro-package-estimate/README.md:188)。 |
| M4 | closed | fig15 の生成器が読む repo 外入力と、追跡下の同一 SHA-256 の写しを併記。[計画書](/work/1/SFC/tanab/izanagi/.claude/worktrees/t2853-rerun-plan/output/insights/2026-09-23/t2853-figure-rerun-plan/README.md:120)、[図 README](/work/1/SFC/tanab/izanagi/.claude/worktrees/t2853-rerun-plan/docs/paper-story/figures/README.md:2025)。追跡下の5ファイルも一覧で確認した。 |
| M5 | closed | 20 図を、生成器のある17図、生成器が要るfig1、対象外のfig2・fig3に分割。[計画書](/work/1/SFC/tanab/izanagi/.claude/worktrees/t2853-rerun-plan/output/insights/2026-09-23/t2853-figure-rerun-plan/README.md:13)、[図一覧](/work/1/SFC/tanab/izanagi/.claude/worktrees/t2853-rerun-plan/docs/paper-story/figures/README.md:10)。 |
| M6 | closed | fig1 の保存評価の再生と、候補ごとに評価する G を分離。[計画書](/work/1/SFC/tanab/izanagi/.claude/worktrees/t2853-rerun-plan/output/insights/2026-09-23/t2853-figure-rerun-plan/README.md:22)、[見積り稿](/work/1/SFC/tanab/izanagi/.claude/worktrees/t2853-rerun-plan/output/insights/2026-09-22/t2853-repro-package-estimate/README.md:189)。 |
| S1 | closed | fig4 の選定履歴を構成別に記載し、read-heavy の事前固定値を明記。[計画書](/work/1/SFC/tanab/izanagi/.claude/worktrees/t2853-rerun-plan/output/insights/2026-09-23/t2853-figure-rerun-plan/README.md:69)、[S-1a 結果稿](/work/1/SFC/tanab/izanagi/.claude/worktrees/t2853-rerun-plan/docs/paper-story/results/2026-09-20-s1a-nine-pair-direct-comparison.md:440)。 |
| S2 | closed | fig8 の `job_elapsed_s` を driver 記録 (b) とした。[計画書](/work/1/SFC/tanab/izanagi/.claude/worktrees/t2853-rerun-plan/output/insights/2026-09-23/t2853-figure-rerun-plan/README.md:79)、[正式走 insight](/work/1/SFC/tanab/izanagi/.claude/worktrees/t2853-rerun-plan/output/insights/2026-09-16/b10-tail-formal-submit/README.md:176)。 |
| S3 | closed | fig2c を WAL 時刻差 (c) と明示。[計画書](/work/1/SFC/tanab/izanagi/.claude/worktrees/t2853-rerun-plan/output/insights/2026-09-23/t2853-figure-rerun-plan/README.md:75)、[WAL 記録](/work/1/SFC/tanab/izanagi/.claude/worktrees/t2853-rerun-plan/output/insights/2026-09-23/t2853-figure-rerun-plan/verbatim/wal-span.log:10)。 |
| N1 | closed | WAL の和は fig1 1,016.7 s、fig2b 1,214.0 s、fig2c 3,831.8 s。[WAL 記録](/work/1/SFC/tanab/izanagi/.claude/worktrees/t2853-rerun-plan/output/insights/2026-09-23/t2853-figure-rerun-plan/verbatim/wal-span.log:4)。fig5/7 は7,265 s、fig6 は6,057 s、fig10 は5×(386＋841＋1,218)＝12,225 s、fig11 は4,382 s、fig15 は5,866＋148＝6,014 s。fig15 の内訳は[結果稿](/work/1/SFC/tanab/izanagi/.claude/worktrees/t2853-rerun-plan/docs/paper-story/results/2026-09-20-mocc-witlight-four-arm.md:155)と同225行、fig10 と5 node 試算の元値は[B-7 結果稿](/work/1/SFC/tanab/izanagi/.claude/worktrees/t2853-rerun-plan/docs/paper-story/results/2026-09-19-b7-fixed5-three-workload-regression.md:115)に一致。 |
| FM1 | closed | 48 h を上限枠とし、Elapse 単価による確認判定を未判定へ変更。[計画書](/work/1/SFC/tanab/izanagi/.claude/worktrees/t2853-rerun-plan/output/insights/2026-09-23/t2853-figure-rerun-plan/README.md:83)、[B-10 結果稿](/work/1/SFC/tanab/izanagi/.claude/worktrees/t2853-rerun-plan/docs/paper-story/results/2026-09-20-b10-waiting-grid-formal.md:158)。43,200＋43,200＋86,400＝172,800 s＝48 h。 |
| FS1 | closed | cohort 2 の「Elapse 839秒」を (a) とし、job 別の内訳がないことも明示。[計画書](/work/1/SFC/tanab/izanagi/.claude/worktrees/t2853-rerun-plan/output/insights/2026-09-23/t2853-figure-rerun-plan/README.md:80)、[cohort 2 insight](/work/1/SFC/tanab/izanagi/.claude/worktrees/t2853-rerun-plan/output/insights/2026-09-19/b10-tail-cohort2/README.md:64)。3×839 s は個別会計値の和ではなく換算である。 |
| FS2 | closed | fig8 を fig8b に含め、重複計上しない6図と明記。[計画書](/work/1/SFC/tanab/izanagi/.claude/worktrees/t2853-rerun-plan/output/insights/2026-09-23/t2853-figure-rerun-plan/README.md:142)、[図一覧](/work/1/SFC/tanab/izanagi/.claude/worktrees/t2853-rerun-plan/docs/paper-story/figures/README.md:23)。 |
| FN1 | closed | 1.94 h は受入なしと明記し、0.25 h を足すと2.19 h と記載。[計画書](/work/1/SFC/tanab/izanagi/.claude/worktrees/t2853-rerun-plan/output/insights/2026-09-23/t2853-figure-rerun-plan/README.md:132)、[D2219](/work/1/SFC/tanab/izanagi/.claude/worktrees/t2853-rerun-plan/docs/decisions.md:71260)。 |

§4 の残る和も再計算すると、1.70＋3.40＋1.69＝**6.79**、1.06＋1.40＝**2.46**、0.27＋1.06＋1.70＋1.40＋3.40＋1.69＝**9.52**。これらは出所の異なる値を足した計画値であり、合計の算術が合うことと Elapse による確認判定の妥当性は別です。

## 新規所見

### must-fix

- **GM1 — Elapse がない図の「確認不要」を確定しない。** [計画書:26–32](/work/1/SFC/tanab/izanagi/.claude/worktrees/t2853-rerun-plan/output/insights/2026-09-23/t2853-figure-rerun-plan/README.md:26) は fig4・fig13 以外を単独なら2 node時間未満とし、[§2](/work/1/SFC/tanab/izanagi/.claude/worktrees/t2853-rerun-plan/output/insights/2026-09-23/t2853-figure-rerun-plan/README.md:67)でも fig2b・fig2c・fig8・fig8b を「不要」とする。しかし fig2b は別系列の WAL からの試算、fig2c は WAL 時刻差、fig8 は後始末を含まない driver 記録、fig8b はその値と cohort 2 の換算の和である（[WAL 記録](/work/1/SFC/tanab/izanagi/.claude/worktrees/t2853-rerun-plan/output/insights/2026-09-23/t2853-figure-rerun-plan/verbatim/wal-span.log:10)、[正式走 insight](/work/1/SFC/tanab/izanagi/.claude/worktrees/t2853-rerun-plan/output/insights/2026-09-16/b10-tail-formal-submit/README.md:184)）。[D2219](/work/1/SFC/tanab/izanagi/.claude/worktrees/t2853-rerun-plan/docs/decisions.md:71260) は見積りを job Elapse の実測単価で出すと定める。これらの「不要」は暫定とし、投入形を決めた段階で Elapse に基づく見積りを作って判定する、と§0・各行・§5を揃える。§4 の **2.46 h** のように現時点でも線を超える束については、確認「要」を維持できる。

### should

なし。

### nit

なし。