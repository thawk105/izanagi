# ユーザー依頼 (2026-09-20、/dev-wave の引数、逐語)

B-10 待ち方 grid 正式走の論文図 (台帳 ID 未起票、docs + 生成器) — `docs/paper-story/results/2026-09-20-b10-waiting-grid-formal.md`
  (凍結稿、編集しない) の 3 族 Holm 判定と 36 cell の効果量・95% 区間・等価域 ±3.0% を 1 枚の forest 型の図にする。着手直前の local main から
fresh worktree。生成器は `tools/plotting/` に新設 (Codex author = D95、`tools/plotting/FIGURE_CONVENTIONS.md`
に従う、計測機の外で描く)、成果物は `docs/paper-story/figures/fig13_b10_waiting_grid_*.{png,pdf,provenance.json}` (番号は着手時に
figures/README.md で衝突を確認) と `figures/README.md` の節・日本語キャプション正文。データは稿が束縛する一次資料 (report phase `978195.nqsv`
の report・受領証) から読み、provenance は稿を `caption_source` として SHA-256 束縛する (F36)。書いてよいことは事前登録
`docs/b10-backoff-shape-preregistration.md` 発効版 §3 の範囲: 区間が ±3% に収まることを「等価性の成立」と呼ばず、36 cell
の個別有意差にも読み替えず、右 tail 2 稿と合成しない (D2157)。fig11 wave (entry 1738) と同形の軽量版。README の results
表は触らない。仮想リスク向けの gate・検査・台帳の追加は scope 外。
