単独段 dispatch: stage=focus; sandbox=read-only; parent=/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-mocc-g2-observation-results

必読事項の射影:
- /work/1/SFC/tanab/dev-wave-jobs/dev-wave-mocc-g2-observation-results/codex/s6-review.md — 段 6 レビューの所見 (must-fix 1 / should-fix 4 / nit 1)。読めなければ即停止。
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-mocc-g2-observation-results/docs/paper-story/results/2026-09-20-mocc-g2-observation-conditions.md — fix 後の統制稿 (未 commit)。読めなければ即停止。
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-mocc-g2-observation-results/docs/paper-story/README.md — results 表の `results/2026-09-20-mocc-g2-observation-conditions.md` の行 (fix 後)。読めなければ即停止。
- /work/1/SFC/tanab/dev-wave-jobs/dev-wave-mocc-g2-observation-results/scratch/apply_fix1.py — 親が当てた fix の逐語 (置換前後)。読めなければ即停止。
- /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2779-mocc-g2-observation-conditions/s4-ruling.md — 事前登録 (項 6・7)。読めなければ即停止。
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-mocc-g2-observation-results/output/insights/2026-09-18/t2779-mocc-g2-observation-conditions/README.md — 記録 insight (§4 の検出力・基準率の説明)。読めなければ即停止。
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-mocc-g2-observation-results/output/insights/2026-09-18/t2779-mocc-g2-observation-conditions/verbatim/mocc-transaction-e9e477ca.cc.txt — source (`writePhase()` の C 行書式)。読めなければ即停止。
- /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2779-mocc-g2-observation-conditions/arm-B/B1/runs/082-e9-instr-nowit/trace/trace_33.log — 生 trace (`grep -m1 "^C 406139 "` で 1 行だけ読む。全文を読まない)。読めなければ即停止。
- /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2779-mocc-g2-observation-conditions/arm-B/B1/runs/082-e9-instr-nowit/trace/trace_0.log — 生 trace (`grep -m1 "^C 406140 "` で 1 行だけ読む)。読めなければ即停止。
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-mocc-g2-observation-results/docs/decisions.md — D1373 を `grep -n "^## D1373\."` で引いて該当 D だけ読む。読めなければ即停止。

## 依頼 (焦点再レビュー、read-only)

あなたは read-only の焦点再レビュー子である。書き込み可能な tmp は無い。静的検査だけでよい。予算が尽きそうなら途中結論を下の出力形式どおり書いて終われ。

段 6 レビューの所見 1〜6 に親が fix を当てた (逐語は `apply_fix1.py`)。**所見ごとに closed / partial / regressed を判定する対応表を作れ。**
表なしで「閉じた」と判定しない。加えて、fix で親が新たに書いた派生値・事実命題を原データから再計算・再照合するまで closed としない:

- §4 項 12 の C 行の書式 (`C <txid> <thid> <epoch> <tid> <read_set 数> <write_set 数>`) を source の `writePhase()` と照合し、B1/082 の 2 行
  (`C 406139 33 42 176 4 6`、`C 406140 0 42 177 6 4`) を生 trace の現物と照合する。
- §2 項 5 の「s4-ruling 項 6 の逐語」と称する引用句が原文と一致するか、「記録 insight §4 にある」と書いた 4 つの値 (7/120、2/40、0.30、約 0.70) が
  実際に insight §4 にあり s4-ruling には無いか。検出力の丸め前 4 値 (0.831467 / 0.721809 / 0.302390 / 0.701730) を独立に再計算する
  (片側 Fisher α=.05、n=120 ずつ、独立 Bernoulli、完全抑制 / 部分抑制 0.02 / α=.025)。
- §0.2 の新しい配置根拠 (単一の観測 protocol の完走) が README の規則「1 file = 1 結果 (1 protocol または 1 campaign 群の完走)」と整合するか、
  README の表 1 行の追記語と稿が整合するか。
- §5 項 16 の新文が D1373 の現況を断定していないか。
- §3.6 の例文が 4 block・各 arm 合計 120 走と読めるか。
- §4 の項目番号の付け替え (12 → 13 項目、項 12 新設) で、稿内の相互参照 (§3.4 → §4 項 12、§5 項 17 → §4 項 12、§4 項 3 → 項 12) が正しいか。
- fix が既存の正しい記述を壊していないか (regressed の探索)。

出力形式 (Markdown、日本語):
- `## 対応表` — 所見 1〜6 の各行に closed / partial / regressed、根拠 (現物の値と稿の値)。
- `## 新規所見` — fix で生じた新しい誤り (無ければ「なし」と確かめた対象)。
- `## 総括` — closed / partial / regressed の件数、新規所見の件数、着地を止めるべきかの判定 (止める / 止めない) と 1 行の理由。
