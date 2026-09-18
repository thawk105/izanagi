単独段 dispatch: stage=focus; sandbox=read-only; parent=/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2674-t1998-results-doc

必読事項の射影:
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2674-t1998-results-doc/docs/paper-story/results/2026-09-18-t1998-balanced-stock-inline-accepted.md — fix 後の統制稿 (commit e31030990)。読めなければ即停止。
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2674-t1998-results-doc/docs/paper-story/README.md — fix 後の README (results 表の 2026-09-18 行)。読めなければ即停止。
- /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2674-t1998-results-doc/s6-review-lensA-3.output.md — レンズ A の所見 (must-fix 7 / should-fix 2)。読めなければ即停止。
- /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2674-t1998-results-doc/s6-review-lensB-3.output.md — レンズ B の所見 (must-fix 1 / should-fix 4 / nit 1)。読めなければ即停止。
- /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2674-t1998-results-doc/projection/README-results-series.md — results 系列の規則 (逐語)。読めなければ即停止。
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2674-t1998-results-doc/docs/t1998-balanced-stock-inline-preregistration.md — 事前登録 v1。読めなければ即停止。
- /work/1/SFC/tanab/t1998-balanced-stock-inline-runs/t1998-balanced-stock-inline-20260913T132723Z-548740-balanced/result.json — 権威 bytes。読めなければ即停止。
- /work/1/SFC/tanab/t1998-balanced-stock-inline-runs/t1998-balanced-stock-inline-20260913T132723Z-548740-balanced/campaigns/backoff-sweep-silo-balanced-sweep-0dd37c05/campaign.lock — 権威 bytes。読めなければ即停止。
- /work/1/SFC/tanab/t1998-balanced-stock-inline-runs/t1998-balanced-stock-inline-20260913T132723Z-548740-balanced/campaigns/backoff-sweep-silo-balanced-sweep-0dd37c05/runs/wal.jsonl — campaign WAL。読めなければ即停止。
- /work/1/SFC/tanab/t1998-balanced-stock-inline-runs/t1998-balanced-stock-inline-20260913T132723Z-548740-balanced.stderr — job stderr (NQSV の終了要約)。読めなければ即停止。
- /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2589-consumer-repair/decision-final.json — consumer の判定 JSON。読めなければ即停止。
- /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2674-t1998-results-doc/projection/D1993.md — 裁定 D1993 (逐語。理由節の「legacy 1 回 + performance 5 回」の出所)。読めなければ即停止。

## 依頼 (fix 後の焦点再レビュー、1 本)

あなたは read-only の焦点再レビュー子である。書き込み可能な tmp は無いので pytest 緑は要求しない。静的検査だけでよい。
予算が尽きそうなら途中結論を下の出力形式どおり書いて終われ (無出力が最悪)。

親は 2 本のレビュー (レンズ A 9 件、レンズ B 6 件) の所見をすべて real として稿へ反映し、commit e31030990 にした。
親の判断のうち次は「部分採用」である: レンズ B 所見 4 (8 点表) は表を削除せず、登録外 2 点の比較文と行 2 の hash 余談を削り、
注意書き 1 文に置き換えた (依頼文が「8 genome 分の campaign 記録を含む一次資料全体」と言うことを根拠に、表は残す編集判断)。
親が §4 (j) を訂正するにあたり、main の first-parent 列を a551cdd3 から古い順に辿り直し、b1a3d45d61ac7a62f589c514683e5ba999b50609
(2026-09-14 08:30:25 JST) が是正 commit 4d7cd40a9 を最初に含み、その第 1 親 e0b1c3366a54a98c66bb1408fbf4469f10155a33 は含まないことを
`git merge-base --is-ancestor` で確かめた (あなたは git を読み取りで使ってよい)。

やること:
1. **所見ごとの対応表。** レンズ A の 1〜9、レンズ B の 1〜6 の計 15 件について、fix 後の稿で `closed` / `partial` / `regressed` を
   判定し、根拠 (稿の節と現物の値) を書く。表なしで「閉じた」と言わない。
2. **親が書いた派生値・量化の再計算。** fix 後の稿にある「全項一致」「すべて」「だけ」「23 key」「40 record」「63 blob」「限定 20 件」
   「8 点とも」「両 arm とも」などの量化を、現物から数え直して照合する。訂正した箇所 (§4 (j) の commit、§2.5 の出所、`ycsb_*` key、
   `perf_counter_statuses` の型、`genome` の階層、事前登録 §4 冒頭の引用) にも同じ検算を掛ける。
3. **新規所見。** fix が新しい誤り・過大主張・規則違反を生んでいないか (regression)。特に §2.3 に足した呼出し経路の記述
   (loop.py が correctness を渡さない、lock の search_config に verify key が無い) を、campaign.lock の現物と、
   `git show a551cdd3014708993475108f014aacbf32c21137:orchestrator/campaign/loop.py` の現物で確かめる。

出力形式 (Markdown、日本語):
- `## 対応表` — 15 行 (レンズ・番号・重さ・判定 closed/partial/regressed・根拠)。
- `## 検算` — 量化ごとに現物の値と稿の値。
- `## 新規所見` — 無ければ「なし」と確かめた対象。あれば must-fix / should-fix / nit と直し方。
- `## 総括` — closed / partial / regressed の件数、新規所見の件数、着地を止めるべきかの判定 (止める / 止めない) と 1 行の理由。
