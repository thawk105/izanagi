単独段 dispatch: stage=focus; sandbox=read-only; parent=/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2674-recovery-codex
必読事項の射影:
- /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2674-recovery-codex/review.output.md — 読めなければ即停止
- /work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2674-recovery-codex/docs/paper-story/README.md — results系列とT-1998追補。読めなければ即停止
- /work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2674-recovery-codex/output/insights/2026-09-18/t2674-t1998-results-doc/README.md — 読めなければ即停止
- /work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2674-recovery-codex/output/insights/2026-09-18/t2674-t1998-results-doc/recovery.md — 読めなければ即停止
- /work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2674-recovery-codex/docs/spool/worklog/2026-09-18-dev-wave-t2674-t1998-results-doc-1.md — 読めなければ即停止

前レビューの新規should-fix2と既知must-fix旧受入記述、および親briefへの異議への対応だけを焦点再レビュー。
read-only、編集/commit禁止。書込可能tmpがないため静的検査でよく、pytest緑は要求しない。
予算が尽きそうなら途中結論を必ず出す。実装追加を要求せず、本題外gate/台帳/一般化を加えない。
凍結稿は旧tip e3f4d277fとbyte同一を維持して入口追補で限定した。旧rc70は不受理。
今回の単独51 passedはverbatim/recovery-focus-t1259.log、最終受入とは書き分けた。
旧逐語2本と今回レビューの末尾ASCII spaceを除き末尾LFを追加した。recovery.mdの復元法から原文hash一致を親が確認したが、独立にも検算する。
## 対応表 でfindingごとのclosed/partial/regressedと根拠、## 総括 で着地阻害の有無・未実走を報告。
