単独段 dispatch: stage=focus; sandbox=read-only; parent=/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2853-r2-fig6

必読事項の射影:
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2853-r2-fig6/output/insights/2026-09-29/t2853-r2-fig6/verbatim/s6-review-b.md (前回の所見。読めなければ即停止)
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2853-r2-fig6/output/insights/2026-09-29/t2853-r2-fig6/README.md の §5 と §9 (読めなければ即停止)
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2853-r2-fig6/output/insights/2026-09-29/t2853-r2-fig6/figures/README.md (処置の本体。読めなければ即停止)
- /work/1/SFC/tanab/izanagi-repro-archive/t2853-r2-fig6-20260929/ (図の provenance・wrapper・README。読めなければ即停止)

あなたは izanagi の dev-wave 段 6 の焦点再レビュー子 (read-only) である。対象は commit `297a20555` (前回 `75749a951` からの差分)。
書込可能な tmp は無いので静的検査でよい。予算が尽きそうなら途中結論を出力形式どおり書いて終われ。

1. 前回の所見 B-1・B-2・B-3 ごとに closed / partial / regressed を表で判定せよ。B-3 は受入の実走後に親が記録する予定の項で、この時点では open が正しい (未実施をそう書いているかを見る)。
2. figures/README.md の再生成手順が、置き場の wrapper の argv (subcommand・必須引数) と一致し、そのまま実行できる形か (path・sha256 の一致)。
3. 注記の文 (「R2 と原 attempt の効果はどちらも正で符号差は無い」「この文は原 fig6 の定型文」) が一次資料 (certification の effects、原 fig6 の README 節) と合うか。
4. 差分が新しく誤りや過剰な主張を持ち込んでいないか。

## 出力形式

所見ごとの closed / partial / regressed の表、新規所見 (`ID / 重大度 / 場所 / 問題 / 根拠 / 直し方`)、最後に GO / NO-GO と `## 総括` 節 (3 行以内)。
