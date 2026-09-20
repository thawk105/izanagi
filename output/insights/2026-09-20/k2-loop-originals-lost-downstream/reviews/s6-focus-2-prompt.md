単独段 dispatch: stage=focus; sandbox=read-only; parent=/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-k2-loop-originals-lost-downstream

必読事項の射影:
- /work/1/SFC/tanab/dev-wave-jobs/dev-wave-k2-loop-originals-lost-downstream/focus-1.md — 焦点再レビュー 1 巡目 (NO-GO、残 must-fix 4 = M1 の証拠・量化、M6 の入口表記、fragment の GO 先取り、受領証を除外しない限定文)。読めなければ即停止。
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-k2-loop-originals-lost-downstream/output/insights/2026-09-20/k2-loop-originals-lost-downstream/reviews/s6-adjudication.md — 親の裁定 (末尾「焦点再レビュー 1 巡目の裁定」F1〜F4 の fix 表)。読めなければ即停止。
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-k2-loop-originals-lost-downstream/output/insights/2026-09-20/k2-loop-originals-lost-downstream/README.md — fix 後 (6 行目、§0 の補正文、§1 の loop_state 行・digest 行・走査段落、§4 の前提段落が変わった)。読めなければ即停止。
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-k2-loop-originals-lost-downstream/output/insights/2026-09-20/k2-loop-originals-lost-downstream/materials/reconstruction-log.md — §8 の 24 への訂正と §10 (新規)。読めなければ即停止。
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-k2-loop-originals-lost-downstream/output/insights/2026-09-20/k2-loop-originals-lost-downstream/materials/reconstruction-stdout.txt — 生 stdout (`scan_values.py` の節を追加)。読めなければ即停止。
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-k2-loop-originals-lost-downstream/docs/spool/worklog/2026-09-20-dev-wave-k2-loop-originals-lost-downstream-1.md — fragment (段 6 の記述を実結果に直した)。読めなければ即停止。

これは自分たちの研究記録 (docs-only、実装差分ゼロ) の焦点再レビュー 2 巡目である。1 巡目の残 must-fix 4 件に対する親の fix が閉じたかだけを点検する。
親が実行済み: 追加実測 `scan_values.py` (同 6 root 615 file、21:36 JST。語 hit 24 file ごとの `start_wall` 数値の列挙、roundtrip 走行日の epoch 範囲との照合、
走査 (b) の条件込み採り直し)。その stdout は `reconstruction-stdout.txt` の `scan_values.py` 節に逐語で入っている。
read-only sandbox なので pytest 緑は要求しない。静的検査でよい。**出力は file に書かず、最終メッセージの本文に全文を書け** (親の launcher が保存する)。
予算が尽きそうなら途中結論を出力形式どおり書いて終われ (無出力が最悪)。

点検すること:
1. 残 must-fix 4 件それぞれについて closed / partial / regressed と根拠 (file:行)。
2. 新しい量化 (「24 file」「数値を持つのは 4 file」「roundtrip 走行日の epoch 範囲の値は 0 件」「走査 (b) の hit は round 2 scratch の digest 1 件・round 3 digest 0 件」) を
   `reconstruction-stdout.txt` の `scan_values.py` 節と照合してから closed とする。
3. fix で入った文に新しい過大・不整合が無いか (regression)。特に README §0 の「受領証を除く 4 file」と §1 の受領証行、§4 前提段落の「再構成対象のうち … それに現物が残る受領証」が
   §1 の表と整合するか。
4. fragment の段 6 の記述が結果を先取りしていないか (2 巡目 = 本レビューの結果は「`s6-focus-2.md` に」と書いてあるのが正しい形)。

## 出力形式 (見出しは全部 `##` の H2。`###` を使わない)

## 対応表
- 残 must-fix 4 件 (M1 証拠・量化 / M6 入口表記 / fragment の先取り / 受領証の限定) の各行: closed / partial / regressed、根拠。
## 新規所見
- fix で入った regression や残る過大。無ければ「無し」。
## 総括
- GO / NO-GO と、NO-GO なら残る must-fix。最後の節は必ず `## 総括` (`#` を 2 個) とする。`### 総括` と書いてはならない。
