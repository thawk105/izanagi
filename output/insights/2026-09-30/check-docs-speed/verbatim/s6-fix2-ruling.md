# fix 第 2 巡の裁定 (親、2026-09-30 JST)

根拠 (計算ノード、同一 node bnode006 の交互 5 回、E3 r2 = commit 41b678391 の checker):
- wall 中央値 旧 37.52 s → 新 15.51 s (比 0.413)、stdout sha256 は全 12 走同一。
- **peak RSS 中央値 旧 309,024 KiB → 新 371,380 KiB (+62,356 KiB ≈ +61 MiB、+20%)**。
- 帰属 (親の算術): 各 archive の先頭 entry の本文 ID を `_ArchiveWorklog.first_entry_ids` に保持している。全 1,645 archive の先頭 entry の
  ID 付きトップレベル項目は計 839,548 件 (平均 510)。1 件 = 別実体の短い str (約 57 B) + list slot 8 B ≈ 65 B → 約 55 MB で、+61 MiB とほぼ一致する。
  ID の種類は数百しかない (同じ T が多数の entry に carry される) ため、同値の str が別実体として 84 万個並んでいる。

## fix 項目

- F4 (採用、レビュー B1/B2 の残り): `first_entry_ids` に保持する ID 文字列を `sys.intern` で共有実体にする
  (保持する箇所 = `_ArchiveWorklog(...)` へ渡す `archive_entry_ids[0]` だけ、例: `[sys.intern(task_id) for task_id in archive_entry_ids[0]]`)。
  `_top_level_ids` 本体・他の呼出し箇所・判定・所見は変えない。str の等価性は不変なので判定は変わらない。
- test の追加・変更は不要 (判定不変は親が repo 外 probe で再確認する)。既存テストの期待値は変更しない。

## 規模

check_docs.py の差分は数行以内。変異 M1〜M7 の anchor 行 (ruling-s4.md、`right.first_entry_ids,` を含む) は変更しない。
