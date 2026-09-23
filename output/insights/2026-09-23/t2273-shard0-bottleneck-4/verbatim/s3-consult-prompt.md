単独段 dispatch: stage=consult; sandbox=read-only; parent=/work/1/SFC/tanab/izanagi/.claude/worktrees/t2273-acceptance-bottleneck-diag

必読事項の射影:
- /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2273-acceptance-bottleneck-diag/s1-brief.md — 親の段 1 brief ((P1)(P2)、計測 Job R / Job C、判定の読み方)。読めなければ即停止。
- /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2273-acceptance-bottleneck-diag/verbatim/T-2273-origin.md — 依頼の逐語。読めなければ即停止。
- /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2273-acceptance-bottleneck-diag/verbatim/D1936-item35.md、D2219-item4.md — 既裁定の逐語。読めなければ即停止。
- /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2273-acceptance-bottleneck-diag/verbatim/t2817-jobB-analysis-A.json — 前回 (T-2817 Job B、旧台帳、1 走) の観測 wrapper の機械集計。`keys[].builds[]` の begin/end と seconds (copy/git/issue)、`keys[].flock_waits`、`consumers`、`shard`。読めなければ即停止。
- /work/1/SFC/tanab/izanagi/.claude/worktrees/t2273-acceptance-bottleneck-diag/output/insights/2026-09-21/t2825-ledger-refresh-ab/README.md — 起点 insight (結論 6、§6 走表、§10 限界)。読めなければ即停止。
- /work/1/SFC/tanab/izanagi/.claude/worktrees/t2273-acceptance-bottleneck-diag/output/insights/2026-09-21/t2817-acceptance-bottleneck-3/README.md — 前回診断 (結論 1〜2、§1.2 Job B の観測 wrapper、§8 限界)。読めなければ即停止。
- /work/1/SFC/tanab/izanagi/.claude/worktrees/t2273-acceptance-bottleneck-diag/output/insights/2026-09-19/t2786-base-decomposition-recovery/README.md — 共有 base 構築の内訳の既測。読めなければ即停止。
- /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2817-acceptance-bottleneck-3/probe/t2817_replica_runner.py、t2817_replica_plugin.py、t2817_replica_analyze.py — 再利用予定の probe (Codex author 作、repo 外)。読めなければ即停止。
- /work/1/SFC/tanab/izanagi/.claude/worktrees/t2273-acceptance-bottleneck-diag/orchestrator/tests/test_s8b_oracle_driver.py — `_T080SharedBases` (920 行付近)、`_t080_stub_free_e2e_repo` (995 行付近)、`_copy_git_visible_output` (847 行付近)、`_build_t080_stub_free_e2e_repo` (1437 行付近)。必要な範囲だけ grep で引く。読めなければ即停止。
- /work/1/SFC/tanab/izanagi/.claude/worktrees/t2273-acceptance-bottleneck-diag/orchestrator/tests/acceptance_duration_ledger.json と orchestrator/tests/conftest.py の並び替え (`_reorder_acceptance_items_by_duration`、pairing) — 必要な範囲だけ grep で引く。

## 目的

これは自分たちの受入 test 基盤の診断設計レビューである。[T-2273] 診断 wave の段 3 相談 (read-only、reasoning=medium) として、
**親の brief 自身を検査対象**とし、(P1)(P2)・計測設計 (Job R ×3、Job C)・判定の読み方・親の前提実測 (T-2817 Job B の読み) とその一般化・依頼との整合を点検し、
計算ノード job を投げる前に直すべき欠陥だけを根拠 (file:line、brief の節、JSON の key) 付きで指摘せよ。brief を守る側に立つな。
見つからなければ「見つからない」と書け。改善策の実装は本 wave の範囲外 (D1936 項 35) なので、実装案の良否ではなく「診断が正しく閉じ、次の一手 1 つの効果見込みが実測で示せるか」を点検せよ。

## 点検のレンズ (両方とも行う)

1. **正しさ・整合・実効性:** (a) 親の P1 (同時構築本数で copy が伸びる IO 競合) は T-2817 Job B の数字から正しく読めているか。copy 100.4 秒が 5 builder で揃う点に別解釈 (共通の待ち・同じ lock・page cache・git index 読み・CPU 飽和) はないか。issue 69 秒一定の読みは妥当か。(b) Job R の出力で L の経路 (flock 待ち・自分の構築・copytree・verify・残り) を分解し律速を同定できるか。builder の同時本数の時系列を wrapper の span から取れるか。欠ける計器は何か。(c) Job C (他負荷なし node で k 本同時の実 builder) は受入内の条件 (48 worker が CPU を使う) を再現しないので、C の k 曲線を R の効果見込みに換算するときの歪みは何か。直す最小の設計は何か (例: R 内の実測だけで閉じる読み方、C に背景負荷を足す、C を省く)。(d) 「A の t≈55 秒 189.98〜208.09 秒との差」に答える読み方は、A を再走せずに成り立つか。(e) 再利用予定の probe は現行 tip で動くか (wrap 対象の名前・引数・T-2817 固有の固定値)。
2. **過剰・削除:** 依頼は「本題の診断だけ」「次の一手 1 つ」。Job R 3 本・Job C は必要十分か、削れるものはあるか。brief に scope 外 (gate・検査・台帳・一般化・prewarm 実装) の混入はないか。2 node 時間の見積りは妥当か。

## 出力形式

所見ごとに: ID、重大度 (高/中/低)、根拠 (file:line / 節 / key)、何が誤るか (放置時に insight の律速判定・次の一手の効果見込みがどう変わるか 1 行)、最小の修正。最後に `## 総括` 節で GO / 修正後 GO / NO-GO と、Job R・Job C の推奨形を 5 行以内で書け。

注意: sandbox は read-only で書込可能 tmp がないため静的検査でよい。テスト・job の実測は親が行う。予算が尽きそうなら途中結論を出力形式どおり書いて終われ。
