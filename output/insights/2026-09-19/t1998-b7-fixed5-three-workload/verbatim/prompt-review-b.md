単独段 dispatch: stage=review; sandbox=read-only; parent=/home/SFC/tanab/.claude/jobs/f6bf33bb/ruling-s4.md

必読事項の射影:
- /home/SFC/tanab/.claude/jobs/f6bf33bb/ruling-s4.md (段 4 裁定 = plan v2・所有・不変条件。読めなければ即停止)
- /home/SFC/tanab/.claude/jobs/f6bf33bb/brief.md (段 1 brief。scope・不変条件・DW-G05。読めなければ即停止)
- /home/SFC/tanab/.claude/jobs/f6bf33bb/author.patch (author の差分全文 = レビュー対象。読めなければ即停止)
- /home/SFC/tanab/.claude/jobs/f6bf33bb/author-out.md (author の最終報告。読めなければ即停止)
- /home/SFC/tanab/.claude/jobs/f6bf33bb/tests-focus-1.log (親の実走: 対象 2 test file、307 passed。読めなければ即停止)
- /home/SFC/tanab/.claude/jobs/f6bf33bb/tests-meta-1.log (親の実走: meta-test 5 file、1071 passed / 6 skipped。読めなければ即停止)
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1998-three-workload-regression/orchestrator/tests/test_paper_story_a2_certification.py (適用後の test。読めなければ即停止)
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1998-three-workload-regression/orchestrator/tests/test_paper_story_a2_job_contract.py (適用後の test。読めなければ即停止)

repo root は /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1998-three-workload-regression (HEAD c18a80967 = 実装 commit)。module・policy・submitter・docs も同 root 配下を読んでよい。

# 依頼 — 段 6 敵対レビュー レンズ B: 過剰・削除 (DW-S03 のレンズを固定)

author の差分と親の裁定を守らず攻撃せよ。**足しすぎ・削りすぎ・局所修正で足りるところに一般化を入れていないか**を見る。
所見は file:line と具体的な壊れ方を伴う real だけを挙げ、推測は「未確認」に分ける。

## 観点

1. **過剰**: 実装が「新 policy 1 path の closed set 追加」を超えていないか — 新しい gate、汎用化 (study 集合を data-driven にする等)、互換層、partial の一般化、job body 変更、plotter 変更、docs 変更が混じっていないか。tests の追加 20 case のうち、既存 test と重複して検出力を増やさないもの、実体でなく性質だけを見る恒真なもの、tmp path や sha を焼き込んで揮発するものは無いか。
2. **削除・局所修正の可否**: 逆に、plan v2 が要求した検出 (adopted genome 不整合、未知 key、shape 不足、非 canonical 拒否、全件 materialize の正常/退行 2 param、partial 不変、3 request 契約、重複検出) のどれかが欠けていないか。欠けているなら最小の追加を示せ。
3. **研究前進への実効**: この実装で親が実際に投入した attempt (`b7f5-20260919a`、request 10807/10808/10809.nqsv、policy sha `c6b24050…`) の成果物を、親が後で `collect` して results 稿へ落とすとき、機構の出力 (certification.json の `effects`・cells・outer status) に不足や誤読の余地は無いか。判定規則 v2 (ruling-s4.md) が機構の実 field 名 (`cells[].performance.median_tps`、`effects`、`status`、`a4_noise_floor_status` 等) と一致しているか module で照合せよ。
4. **不変条件の実測**: A-2 / A-6 policy の bytes と protocol hash、既存 attempt leaf (`output/insights/2026-09-07_t2364-*`、`2026-09-08_t2411-*`) が実装 commit で無変更であることを `git diff 657e1e5a7 c18a80967 --stat` から確認。
5. **親自身の実測値**: 親の test log の件数 (307 / 1071+6) と author 報告の整合、親の brief・裁定の行番号・sha の実在。

## 制約

- read-only。pytest は走らせられない。静的検査でよい。
- 予算が尽きそうなら途中結論を出力形式どおり書いて終われ。
- scope 外の一般化・新 gate は提案せず「裁定パッケージ候補」に分ける。

## 出力形式

- `## must-fix` (番号、file:line、壊れ方、最小 fix)
- `## should-fix` (放置しても成果物の値・受理集合・参照を変えないもの)
- `## 削れるもの` (削っても検出力が落ちないもの、理由)
- `## refuted` (確認できた正しい点、根拠)
- `## 裁定パッケージ候補` (無ければ「なし」)
- `## 総括` (5 行以内)
