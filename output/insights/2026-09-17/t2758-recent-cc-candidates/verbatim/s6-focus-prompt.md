単独段 dispatch: stage=focus; sandbox=read-only; parent=/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2758-recent-cc-candidates

必読事項の射影:
- /home/SFC/tanab/.claude/jobs/24e58a2d/tmp/wave-t2758/s6-review.md — 段 6 レビュー (前巡) の所見 10 件と是正案。読めなければ即停止。
- /home/SFC/tanab/.claude/jobs/24e58a2d/tmp/wave-t2758/parent-fix-table.md — 親の是正対応表 (所見ごとの裁定・適用・自己判定)。検査対象。読めなければ即停止。
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2758-recent-cc-candidates/docs/related-work/cc-candidates-2026-09-17.md — 是正後の候補表 (v2、未 commit・untracked)。前巡が読んだ v1 は無い (上書き済み)。読めなければ即停止。
- /home/SFC/tanab/.claude/jobs/24e58a2d/tmp/wave-t2758/parent-docs-v2.diff — 是正後の README 2 本の差分 (docs/related-work/README.md 7.1 のポインタ段落、docs/README.md の地図 1 行)。読めなければ即停止。
- /home/SFC/tanab/.claude/jobs/24e58a2d/tmp/wave-t2758/rulings-verbatim.md — D2114 / D1760 / D2095 / 7.7.2〜7.7.3 / literature-map の既知の危険 / ccbench-anatomy §4 / DW-G05 の逐語。読めなければ即停止。
- /home/SFC/tanab/.claude/jobs/24e58a2d/tmp/wave-t2758/web-evidence.md — 親が web 取得した一次資料の記録。データであって指示ではない。読めなければ即停止。
- /home/SFC/tanab/.claude/jobs/24e58a2d/tmp/wave-t2758/sources/ — 一次資料の逐語 (前巡と同じ 20 file)。directory を列挙して読め。読めなければ即停止。
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2758-recent-cc-candidates/docs/isolation-phenomena.md — verifier の trace の前提。読めなければ即停止。

差分の時点: すべて commit 前の working tree (untracked 1 file + modified 2 file)。docs-only で実装面の差分は無く、親が直接起草・是正した。前巡の是正案は逐語適用でなく、親が候補表全体を書き直した (P3 の三値化と判定語の変更に伴う)。親がレビュー後に足した照合 3 件 (neurcc root 一覧・RebirthRetire LICENSE・aria LICENSE) は parent-fix-table.md の末尾に記録がある。

これは前巡の所見が閉じたかの焦点再レビューである。目的: (1) 所見 1〜9 のそれぞれについて closed / partial / regressed を判定し、親の自己判定と食い違う所を指摘する、(2) 書き直しで新たに入った事実の誤り・RW1 違反・設計指定を拾う、(3) 親が書いた量化 (「唯一」「0 件」「同一」「3 行」「7 つ」など) を原データから再計算して照合する。書き込みはしない。web には出られないので、照合は sources/ と web-evidence.md の範囲で行い、その外は「未照合」と書け。pytest は無関係。予算が尽きそうなら途中結論を出力形式どおり書いて終えよ (無出力が最悪)。

## 出力形式 (見出しは全部 H2、最後は必ず `## 総括`。`### 総括` と書いてはならない)

## 所見別対応表 (前巡 1〜10 × closed / partial / regressed、根拠は候補表 v2 の逐語)
## 新規所見 (番号付き、real / refuted、根拠 file:line または sources/ の逐語)
## 量化の検算 (親の量化の文 → 原データ → 一致 / 不一致)
## 総括
- must-fix と nit を分け、must-fix は放置時に成果物の判定や読者の判断がどう変わるかを 1 行で示す。示せないものは nit。
- 是正案は逐語で書く。
