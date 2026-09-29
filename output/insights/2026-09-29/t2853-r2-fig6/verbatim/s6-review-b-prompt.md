単独段 dispatch: stage=review; sandbox=read-only; parent=/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2853-r2-fig6

必読事項の射影:
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2853-r2-fig6/output/insights/2026-09-29/t2853-r2-fig6/README.md (レビュー対象の本体。読めなければ即停止)
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2853-r2-fig6/output/insights/2026-09-29/t2853-r2-fig6/verbatim/request.md (依頼の逐語。読めなければ即停止)
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2853-r2-fig6/output/insights/2026-09-29/t2853-r2-fig6/verbatim/s1-brief.md と s4-ruling.md (親の brief と裁定。親自身も検査対象。読めなければ即停止)
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2853-r2-fig6/output/insights/2026-09-28/t2853-r2-fig8b/README.md (先例。読めなければ即停止)
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2853-r2-fig6/docs/phase3.md の [T-2853] fig6 の行と /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2853-r2-fig6/docs/spool/worklog/2026-09-29-worktree-dev-wave-t2853-r2-fig6-1.md (読めなければ即停止)
- /work/1/SFC/tanab/izanagi-repro-archive/t2853-r2-fig6-20260929/ (図・対照表・wrapper・README。読めなければ即停止)

あなたは izanagi の dev-wave 段 6 の敵対レビュー子 (read-only) である。対象は wave branch の commit `75749a951` と repo 外の成果物。
書込可能な tmp は無いので静的検査でよい。テストの実走は親が行う。予算が尽きそうなら途中結論を出力形式どおり書いて終われ。

## レンズ B — 過剰・削除 (依頼への適合)

1. 依頼の逐語 (「本題だけ」「成果は insight のみ」「表と同じ生成器の図に並べる」「trace 保全口は渡せるなら使う」「2 以上ならユーザー確認後に投入」「仮想リスク向けの gate・検査・台帳・一般化は scope 外」) に対し、成果物が足りないもの・余計なものを挙げよ。
2. insight・phase の行・worklog fragment が、書いてある以上のこと (再現精度、統合 status、条件差の効果、性能の認証、他 workload への転移) を言っていないか。逆に、読者が誤読しうる箇所 (R2 が原 attempt の置き換えに読める、caption の定型文、provenance の再現 argv、dir 名 `2026-09-07_t2364-…` の中身が R2 であること) の注記が足りているか。
3. 親の見積りと判断 (t2489 の Elapse を単価にした 1.96、受入 0.25、確認の取り方、軽量版で段 2・3 を省いたこと) に穴が無いか。親自身の実測値の一般化を探せ。
4. 削ってよい記述・ログ、または本題に要るのに欠けている一次資料があれば挙げよ。

## 出力形式

所見ごとに `ID / 重大度 (must-fix・should-fix・nit) / 場所 / 問題 / 根拠 / 直し方` を書く。最後に GO / NO-GO と `## 総括` 節 (3 行以内) を置く。
