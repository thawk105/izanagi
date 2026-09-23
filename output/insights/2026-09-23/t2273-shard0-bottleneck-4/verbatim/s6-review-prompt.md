単独段 dispatch: stage=review; sandbox=read-only; parent=/work/1/SFC/tanab/izanagi/.claude/worktrees/t2273-acceptance-bottleneck-diag

必読事項の射影:
- /work/1/SFC/tanab/izanagi/.claude/worktrees/t2273-acceptance-bottleneck-diag/output/insights/2026-09-23/t2273-shard0-bottleneck-4/README.md — レビュー対象 (親が書いた insight)。読めなければ即停止。
- /work/1/SFC/tanab/izanagi/.claude/worktrees/t2273-acceptance-bottleneck-diag/docs/spool/worklog/2026-09-23-t2273-acceptance-bottleneck-diag-1.md — レビュー対象 (worklog fragment)。読めなければ即停止。
- /work/1/SFC/tanab/izanagi/.claude/worktrees/t2273-acceptance-bottleneck-diag/output/insights/2026-09-23/t2273-shard0-bottleneck-4/verbatim/s4-ruling.md — 段 4 裁定と事前登録 (§3、追補 1 の R2 の事前登録、追補 2)。読めなければ即停止。
- /work/1/SFC/tanab/izanagi/.claude/worktrees/t2273-acceptance-bottleneck-diag/output/insights/2026-09-23/t2273-shard0-bottleneck-4/verbatim/T-2273-origin.md — 依頼の逐語。読めなければ即停止。
- 一次資料 (機械集計と生記録、repo 外): /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2273-acceptance-bottleneck-diag/analysis/r1.json、r2-a2.json、r2c-pair.json (大きいので jq 等で必要な key だけ引け)、job-out-r1/ と job-out-r2/ と job-out-r2b/ と job-out-r2c/ の env-before.json・run.json・incomplete.json・staging.json、run-r1.log / run-r2.log / run-r2b.log / run-r2c.log の NQSV footer (Elapse)。読めなければ即停止。
- /work/1/SFC/tanab/izanagi/.claude/worktrees/t2273-acceptance-bottleneck-diag/output/insights/2026-09-21/t2825-ledger-refresh-ab/README.md と output/insights/2026-09-19/t2786-base-decomposition-recovery/README.md と output/insights/2026-09-21/t2817-acceptance-bottleneck-3/README.md — 引用している既存値の出所。必要な節だけ。
- /work/1/SFC/tanab/izanagi/.claude/worktrees/t2273-acceptance-bottleneck-diag/orchestrator/tests/test_s8b_oracle_driver.py — `_copy_git_visible_output` の呼出し元 (README §1 の「builder の 1 箇所だけに効く」の根拠)。grep で引け。

## 目的

[T-2273] 診断 wave の段 6 独立レビュー (read-only)。これは一次資料から事実を再抽出して書いた docs-only の記録なので、**README と fragment の全ての数値・node 名・request 番号・件数・判定を一次資料から自分で再抽出して照合**し、食い違い・一次資料に無い主張・事前登録 (s4-ruling §3・追補 1) と違う読み方・過大な一般化 (1 対の観測を効果の確定値と読ませる、X の絶対値から 5 分未満を示唆する、原因を断定する等)・依頼との不整合を探せ。親を守る側に立つな。レンズは 2 つとも行う: (1) 正しさ・整合 (数値と判定の再抽出照合)、(2) 過剰・削除 (scope 外の主張・不要な記述・依頼が禁じた先行実装の示唆)。

## 出力形式

所見ごとに: ID、重大度 (must-fix / should / nit)、場所 (file と節)、一次資料の値 (path と key)、何が誤るか 1 行、最小の修正。数値を照合して一致したものは「照合済み一覧」に短く列挙せよ (照合範囲を示すため)。最後に `## 総括` 節で GO / 修正後 GO / NO-GO と must-fix 件数を書け。

注意: sandbox は read-only で書込可能 tmp がないため静的検査でよい。予算が尽きそうなら途中結論を出力形式どおり書いて終われ。
