単独段 dispatch: stage=consult; sandbox=read-only; parent=/work/1/SFC/tanab/izanagi/.claude/worktrees/t2273-shard0-local-copy

必読事項の射影 (読めなければ即停止し、読めなかった path を書いて終われ):
- /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2273-shard0-local-copy/s1-brief.md — 親の段 1 brief。**これ自身も検査対象。**
- /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2273-shard0-local-copy/codex/s2-plan-out.md — 段 2 plan。**検査対象。**
- /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2273-shard0-local-copy/verbatim/T-2273-origin.md、D2044-item15.md、D2068.md、D357.md — 依頼と既裁定の逐語。
- /work/1/SFC/tanab/izanagi/.claude/worktrees/t2273-shard0-local-copy/output/insights/2026-09-23/t2273-shard0-bottleneck-4/README.md — 第 4 回診断。
- /work/1/SFC/tanab/izanagi/.claude/worktrees/t2273-shard0-local-copy/orchestrator/tests/test_s8b_oracle_driver.py — plan が引く行 (794〜1000、1036〜1230、1390〜1470、1899〜2000)。必要な範囲だけ grep / sed で引く。
- 必要なら /work/1/SFC/tanab/izanagi/.claude/worktrees/t2273-shard0-local-copy/orchestrator/campaign/s8b_holdout_freeze.py の `enumerate_repository_files` と、builder が起動する発行 subprocess が fixture の output/ を scan する経路。

## 目的 (レンズ A: 正しさ境界・整合・実効性)

これは自分たちの受入 test 基盤の高速化 wave の段 3 敵対相談である。brief と plan を守る側に立つな。次を根拠 (file:line) 付きで攻撃せよ。

1. **受理集合・正しさ防壁:** 写し経由にしたとき、発行 subprocess の production scan が見る fixture の output/ の集合・bytes が、現行 (builder ごとの直接複製) と変わりうる経路はないか。D2044 項 15 の全件性検査 2 か所 (1983〜1984 / 1994〜1998 行) は builder 経路を覆わない — plan の新正例はその穴を実際に埋めるか。D2068 の却下 3 案に実質的に当たる部分はないか。
2. **並行性:** key 別 lock を保持したまま写し lock を取る形で deadlock・残骸の誤使用・`close()` の最後の退出者による削除との競合はないか。失敗した写し生成の後始末、fork 子 (`_t080_cache_fork_call`) の場合。
3. **session snapshot の意味:** 生成後の変更が後続 builder に反映されない点で、現行で赤になっていた状況が緑になる (受理集合が広がる) 経路は実在するか。実在するなら実環境 (受入全走中に output/ を変える主体の有無) で到達可能か。
4. **実効性:** 写しの生成 1 回が Lustre 上で直列に全 builder を待たせる形で、診断の −123.9 秒のうちどれだけが残る見込みか (見積りは根拠付きで。未測定なら未測定と書く)。非共有検査 builder (1079 行) の 1 回が残る影響。
5. **変異の帰属:** plan の変異 5 本が単一理由で kill されるか、他層に mask されないか、期待 node が正しいか。
6. **親自身の実測値とその一般化:** brief の数値・行番号・「8 本が同時刻 ±0.3 秒に読む」等の主張の出所を検算せよ。

read-only で書込可能 tmp が無いので静的検査でよい。テストの実測は親が行う。予算が尽きそうなら途中結論を下の出力形式どおり書いて終われ。

## 出力形式

- `## 所見` (番号付き。各所見に 重大度 must-fix / should / nit、根拠 file:line、反証されうる形、最小是正)
- `## 総括` (3〜6 行。GO / 修正後 GO / NO-GO)
