単独段 dispatch: stage=focus; sandbox=read-only; parent=/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-k2-loop-originals-lost-downstream

必読事項の射影:
- /work/1/SFC/tanab/dev-wave-jobs/dev-wave-k2-loop-originals-lost-downstream/review-1.md — 1 巡目レビュー (NO-GO、must-fix M1〜M7、nit 2)。読めなければ即停止。
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-k2-loop-originals-lost-downstream/output/insights/2026-09-20/k2-loop-originals-lost-downstream/reviews/s6-adjudication.md — 親の裁定と fix の対応表。読めなければ即停止。
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-k2-loop-originals-lost-downstream/output/insights/2026-09-20/k2-loop-originals-lost-downstream/README.md — fix 後の本体 (§0・§1・§2・§4 が変わった)。読めなければ即停止。
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-k2-loop-originals-lost-downstream/output/insights/2026-09-20/k2-loop-originals-lost-downstream/materials/reconstruction-log.md — 抜粋・要約 (冒頭の表記と §8・§9 を追加)。読めなければ即停止。
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-k2-loop-originals-lost-downstream/output/insights/2026-09-20/k2-loop-originals-lost-downstream/materials/reconstruction-stdout.txt — 生 stdout の逐語 (新規)。読めなければ即停止。
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-k2-loop-originals-lost-downstream/output/insights/2026-09-20/k2-loop-originals-lost-downstream/reviews/s4-ruling.md — P1 の文を修正。読めなければ即停止。
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-k2-loop-originals-lost-downstream/docs/spool/worklog/2026-09-20-dev-wave-k2-loop-originals-lost-downstream-1.md — fragment (M5 の修正 + 新規 T 1 件 + 本文の追記)。読めなければ即停止。
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-k2-loop-originals-lost-downstream/docs/paper-story/results/2026-09-20-k2-manual-loop-three-rounds.md — 3 巡稿 (§2.4 表の critic 読取対象、§5.1)。照合に使う。読めなければ即停止。
- /work/1/SFC/tanab/dev-wave-jobs/dev-wave-k2-loop-originals-lost-downstream/refs/cleanup-backup-loss-record-README.verbatim.md — 記録 wave README の逐語写し (§3 の結論の原文)。読めなければ即停止。

これは自分たちの研究記録 (docs-only、実装差分ゼロ) の焦点再レビューである。1 巡目レビューの所見 M1〜M7 と nit 2 件に対する親の fix が閉じたかを点検する。
親が実行済み: 追加実測 2 本 (`scan_roundtrip.py` = 6 root 615 file の sha 走査、`copy_pair_originals.py` = pair 原本 6 file の byte 複製) と生 stdout の採り直し (`sha_capture.py`)。
その stdout は `reconstruction-stdout.txt` に逐語で入っている (repo 外 script は読めなくてよい。読めない部分は「未検証 (読めず)」と書く)。
read-only sandbox なので pytest 緑は要求しない。静的検査でよい。**出力は file に書かず、最終メッセージの本文に全文を書け** (親の launcher が保存する)。
予算が尽きそうなら途中結論を出力形式どおり書いて終われ (無出力が最悪)。

点検すること:
1. 所見ごとに closed / partial / regressed を判定し、根拠 (file:行 または §・表の行) を書く。表なしで「閉じた」と言わない。
2. 親が書いた派生値・量化 (「5/5 一致」「6/6 一致」「615 file」「0 件」「23 file」「全 615 file に無い」「bytes 一致で再構成可」) は、`reconstruction-stdout.txt` の逐語と照合してから closed とする。
   照合できない量化は partial と書く。
3. fix で新しく入った文 (README §1 の走査 (a)/(b) 段落、§2 B-6 (c)/(d)、§4 全文、§0 の「補正」) に、1 巡目に無かった過大・不整合が無いか (regression)。
   特に §4 が「A を推奨」と「B は研究目的次第で合理」「C は一律に劣るとは言えない」を同時に書いて矛盾していないか、推奨の根拠が証拠の強さの前提と整合するか。
4. fragment の新規 T (README stale 注記) と `更新 [T-2795]` の追記文が、裁定を先取りせず、実測 (複製の作成) を事実として書いているか。
5. 記録 wave README §3 の原文と README §0 の「補正する」の対応が正確か (原文の結論を正しく引用しているか)。

## 出力形式 (見出しは全部 `##` の H2。`###` を使わない)

## 対応表
- M1〜M7、nit 1・2 の各行: closed / partial / regressed、根拠。
## 新規所見
- fix で入った regression や残る過大。無ければ「無し」。
## 総括
- GO / NO-GO と、NO-GO なら残る must-fix。最後の節は必ず `## 総括` (`#` を 2 個) とする。`### 総括` と書いてはならない。
