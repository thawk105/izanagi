単独段 dispatch: stage=focus; sandbox=read-only; parent=/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-acceptance-resubmit-causes

必読事項の射影 (読めなければ即停止):
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-acceptance-resubmit-causes/output/insights/2026-09-21/acceptance-resubmit-causes/README.md — 親が段 6 所見を反映して訂正した診断 insight (未 commit)。§9b に所見ごとの処置表がある。
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-acceptance-resubmit-causes/output/insights/2026-09-21/acceptance-resubmit-causes/verbatim/s6-review.md — 段 6 レビューの報告 (所見 1〜8)。
- 同 dir の verbatim/classification.md (分類表の機械出力、不変)、verbatim/origin.md (依頼)、verbatim/s4-ruling.md。
- /work/1/SFC/tanab/dev-wave-jobs/dev-wave-acceptance-resubmit-causes/timelines-all.txt と各 job dir の一次資料 (/work/1/SFC/tanab/dev-wave-jobs/<job dir 名>/acceptance-*.chain.log、gate-loop-*.log、acceptance-<label>-<n>.started.txt / .finished.txt、docs/worklog.md 726 行付近 (T-2817 の再投入 tip の記述)、/work/1/SFC/tanab/dev-wave-jobs/dev-wave-cleanup-backup-loss-record/HANDOFF.md 23〜26 行)。
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-acceptance-resubmit-causes/docs/dev-wave/operations.md の `DW-O12` (86 行付近) と `DW-O20` (156 行付近)、`DW-O18` (137 行付近)。

## 目的

段 6 レビュー (NO-GO、must-fix 6 / should 1 / nit 1) への親の訂正が閉じたかを、所見ごとに **closed / partial / regressed** で判定せよ (DW-O16)。
親が書いた派生値の訂正 (119.6 分 = 7,174 秒、144.1 分 = 8,647 秒、D4 の再門番 122 / 152 / 151 / 140 秒 = 2.0〜2.5 分、失敗側外側 wall 0.8〜2.5 分、E の 14.5 分 = 門番 2.4 + 外側 12.1、D3 の 2.5 分、§6 の t2804 1.2 / t2153 2.5 分と再門番 2.5 / 2.3 分) は一次資料の時刻から再計算して照合するまで closed としない。
訂正で新たに強すぎる断定・依頼の禁止 (gate・台帳・一般化の追加、受理集合・門番・hold の意味論の変更、規律 2 の緩和) に触れる文・placeholder が入っていないかも見よ (regressed)。
親を守る側に立つな。書込可能 tmp は無い。静的検査 (読取り + grep + 手計算) でよい。

## 出力形式

- 所見 1〜8 の対応表: 「所見 N | 判定 (closed / partial / regressed) | 根拠 (README の節・一次資料の file:line・再計算値) | 残る指摘 (あれば)」。
- 新規所見があれば「新規 N: 要旨 / 根拠 / 影響 / 提案」。
- 最後に `## 総括` を必ず置き、GO / NO-GO と、残る must-fix / should / nit を分けて列挙し、must-fix 0 なら「must-fix なし」と明記する。予算が尽きそうなら途中結論を出力形式どおり書いて終われ。
