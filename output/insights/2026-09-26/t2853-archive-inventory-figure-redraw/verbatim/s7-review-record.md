## 所見

1. **must-fix — `complete` の意味が広すぎる。** [insight §1.1](/work/1/SFC/tanab/izanagi/.claude/worktrees/t2853-archive-inventory-figure-redraw/output/insights/2026-09-26/t2853-archive-inventory-figure-redraw/README.md:33)、[decisions fragment](/work/1/SFC/tanab/izanagi/.claude/worktrees/t2853-archive-inventory-figure-redraw/docs/spool/decisions/2026-09-26-worktree-t2853-archive-inventory-figure-redraw-1.md:15)、[worklog fragment](/work/1/SFC/tanab/izanagi/.claude/worktrees/t2853-archive-inventory-figure-redraw/docs/spool/worklog/2026-09-26-worktree-t2853-archive-inventory-figure-redraw-1.md:22) は `complete` なら build 時と同じ pin・patch があると述べる。一方、[実装](/work/1/SFC/tanab/izanagi/.claude/worktrees/t2853-archive-inventory-figure-redraw/orchestrator/campaign/pipeline.py:2715) は `evidence=None` でも `complete` を書き、[直接呼出しの試験](/work/1/SFC/tanab/izanagi/.claude/worktrees/t2853-archive-inventory-figure-redraw/orchestrator/tests/test_t2853_trace_preservation.py:348) がその経路を使う。**代案:** 主張を「標準評価経路で `SourceEvidence` が渡された inventory」に限定し、evidence がない場合の null を明記する。

2. **must-fix — 再現 argv の差を「出力 prefix」だけとしている。** [insight の分類表](/work/1/SFC/tanab/izanagi/.claude/worktrees/t2853-archive-inventory-figure-redraw/output/insights/2026-09-26/t2853-archive-inventory-figure-redraw/README.md:76) に対し、[compare.log](/work/1/SFC/tanab/izanagi/.claude/worktrees/t2853-archive-inventory-figure-redraw/output/insights/2026-09-26/t2853-archive-inventory-figure-redraw/verbatim/compare.log:13) には `--repo-root` に相当する argv の差が 5 件ある。**代案:** 「出力 prefix と実行 worktree の repo root の違い」と記す。

3. **should — PNG 17/17 の実ファイル比較は、指定された一次資料から追認できない。** [insight](/work/1/SFC/tanab/izanagi/.claude/worktrees/t2853-archive-inventory-figure-redraw/output/insights/2026-09-26/t2853-archive-inventory-figure-redraw/README.md:69) は実ファイルの sha256 比較を述べる。[compare.log](/work/1/SFC/tanab/izanagi/.claude/worktrees/t2853-archive-inventory-figure-redraw/output/insights/2026-09-26/t2853-archive-inventory-figure-redraw/verbatim/compare.log) では provenance 上の PNG sha256 に差がないが、実ファイル 17 組の hash 一覧はない。**代案:** 比較結果を逐語資料へ残すか、根拠を provenance の一致に限定する。

4. **should — carry から未解決の見積り情報が落ちた。** [旧 carry](/work/1/SFC/tanab/izanagi/.claude/worktrees/t2853-archive-inventory-figure-redraw/docs/archive/worklog-phase3-0923-1848.md:626) にある「fig10 は単価から確認が必要、fig13・fig4 は単価がなく未判定」が[更新後](/work/1/SFC/tanab/izanagi/.claude/worktrees/t2853-archive-inventory-figure-redraw/docs/spool/worklog/2026-09-26-worktree-t2853-archive-inventory-figure-redraw-1.md:22)から消えている。**代案:** R2 の見積り待ちに続けて残す。

5. **nit — `env` 未設定時の無呼出しは保全処理の射程で書くと明確。** [insight](/work/1/SFC/tanab/izanagi/.claude/worktrees/t2853-archive-inventory-figure-redraw/output/insights/2026-09-26/t2853-archive-inventory-figure-redraw/README.md:35) の記述は、[finally の分岐](/work/1/SFC/tanab/izanagi/.claude/worktrees/t2853-archive-inventory-figure-redraw/orchestrator/campaign/pipeline.py:2201) と[試験](/work/1/SFC/tanab/izanagi/.claude/worktrees/t2853-archive-inventory-figure-redraw/orchestrator/tests/test_t2853_trace_preservation.py:306) が示す「追加した保全処理」については正しい。**代案:** 「保全処理では」を補う。

## 照合した数値

| 主張 | 判定 | 根拠 |
|---|---|---|
| 17 図、leaf 差 142 件、8 種の内訳 17・51・33・9・5・2・24・1、未分類 0 | 一致 | [classify.log](/work/1/SFC/tanab/izanagi/.claude/worktrees/t2853-archive-inventory-figure-redraw/output/insights/2026-09-26/t2853-archive-inventory-figure-redraw/verbatim/classify.log:3)、[compare.log](/work/1/SFC/tanab/izanagi/.claude/worktrees/t2853-archive-inventory-figure-redraw/output/insights/2026-09-26/t2853-archive-inventory-figure-redraw/verbatim/compare.log) の 17 見出し・142 leaf |
| 図の値の差 0 | 一致 | 全列挙された差は上記 8 種。説明文の差を図の判定値と区別する記述も整合 |
| 17/17 rc=0、PNG 実ファイル bytes 一致 | 確かめられない | [redraw.log](/work/1/SFC/tanab/izanagi/.claude/worktrees/t2853-archive-inventory-figure-redraw/output/insights/2026-09-26/t2853-archive-inventory-figure-redraw/verbatim/redraw.log:68) に fig3b の単独走と fig2c・fig4 の再実行 rc がなく、実ファイル hash 一覧もない。provenance の PNG sha256 差は 0 |
| 焦点走 10 failed / 3,933 passed、次走 3,945 passed / 14 skipped、単独走 18 passed・73 passed / 2 skipped | 一致 | [focus-1](/work/1/SFC/tanab/izanagi/.claude/worktrees/t2853-archive-inventory-figure-redraw/output/insights/2026-09-26/t2853-archive-inventory-figure-redraw/verbatim/focus-1.log:355)、[focus-2](/work/1/SFC/tanab/izanagi/.claude/worktrees/t2853-archive-inventory-figure-redraw/output/insights/2026-09-26/t2853-archive-inventory-figure-redraw/verbatim/focus-2.log:43)、[focus-3](/work/1/SFC/tanab/izanagi/.claude/worktrees/t2853-archive-inventory-figure-redraw/output/insights/2026-09-26/t2853-archive-inventory-figure-redraw/verbatim/focus-3.log:16)、[focus-4](/work/1/SFC/tanab/izanagi/.claude/worktrees/t2853-archive-inventory-figure-redraw/output/insights/2026-09-26/t2853-archive-inventory-figure-redraw/verbatim/focus-4.log:17) |
| baseline PASSED、M1〜M12 の 12 件 KILLED、C0 SURVIVED | 一致 | [変異本走要約](/work/1/SFC/tanab/izanagi/.claude/worktrees/t2853-archive-inventory-figure-redraw/output/insights/2026-09-26/t2853-archive-inventory-figure-redraw/verbatim/mutation-final-summary.txt:1)。probe は 12 件とも期待 SURVIVED に対し MISMATCH |
| 焦点走 Elapse 353・380・13・104 s | 一致 | focus 各 log の `Elapse` |
| 変異 30 job の Elapse 348 s、合計 1,198 s | 一部確かめられない | 既知 4 走は 850 s、348 s を足す算術は 1,198 s。ただし指定された変異要約には各 job の Elapse がない |
| production 51 → 64 追加行、test 106 → 191 追加行 | 一致 | 指定 commit と基準 commit の `git diff --numstat`、[裁定 2](/work/1/SFC/tanab/izanagi/.claude/worktrees/t2853-archive-inventory-figure-redraw/output/insights/2026-09-26/t2853-archive-inventory-figure-redraw/verbatim/s6-ruling-2.md:28) |

R1 の再実行は実施していないと明記され、性能測定や新たな正しさの実測も主張していない。兄弟 node は[fan-out 経路](/work/1/SFC/tanab/izanagi/.claude/worktrees/t2853-archive-inventory-figure-redraw/orchestrator/campaign/pipeline.py:2233)で扱われ、示された保全呼出しの対象外。fragment の見出し・placeholder・必須 field は各 [spool 規則](/work/1/SFC/tanab/izanagi/.claude/worktrees/t2853-archive-inventory-figure-redraw/docs/spool/README.md)と静的に整合する。

## 総括

**NO-GO。** must-fix は 2 件。

1. `complete` と build 時 pin・patch の一致保証を、`SourceEvidence` がある経路に限定する。
2. 再現 argv の差に repo root の変更 5 件を含める。