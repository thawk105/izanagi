# Claude/Codex 過剰追加抑制規則 — plan・敵対レビュー記録

- ユーザー指示: Claude/Codex の next-tasks・dev-wave・rulings で、過剰実装・過剰ガードレールを避ける。
- 最小配置: dev-wave は共通 `DW-G05`、rulings は共通 Claude dispatcher、next-tasks は独立する personal Claude/Codex 定義へ各1箇所。
- 変更しなかった入口: Codex dev-wave / rulings Skill は共通 dispatcher を全文実行する既存契約で到達するため、重複を足さなかった。
- 新設しなかったもの: checker、スコア、台帳、新しい G 節、文書予算、投げ文への一般規則複製。
- 変異 matrix: docs-only・実装面差分ゼロのため免除。

## レビュー結論

- 段2 plan 1本、段3敵対相談2本、段6敵対レビュー2本、焦点再レビュー3巡を実行した。
- 初回所見は、局所修正の誤除外、主目的機能の脱落、必要性の自己申告通過、ユーザー要求範囲の曖昧さを修正した。
- 文書予算への縮約で生じた `DW-S01`・rulings 収集範囲・`DW-G05` must-fix 降格規則の意味落ちを復元した。
- 3巡目の残所見は exact 規則の復元と `check_docs` 緑を親が実測して closed と裁定し、3巡上限後の追加レビューは起動しなかった。

逐語は `verbatim/` に保存した。
