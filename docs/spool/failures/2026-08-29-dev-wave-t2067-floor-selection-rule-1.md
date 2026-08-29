---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-08-29
wave: dev-wave-t2067-floor-selection-rule
seq: 1
---

## 再発

### F649

- **再発: 2026-08-29** — 段 4 裁定が最重要と位置づけた正例 (resume 由来の不適格な earlier があっても
  later の適格 run から candidate を作れる) を、段 5 実装子が earlier の `result.json` だけ複製し
  `_derive_floor_selection_eligibility` を monkeypatch で False へ差し替えて書いた。導出不能時の
  fail-closed 負例も実際の台帳破損ではなく例外 stub だった。段 6 の敵対レビュー 2 本のうち
  運用レンズだけが検出し、正しさレンズは見落とした (F649 初出と同じ検出比)。恒久対応の
  `DW-S05-C` への収容が現行 main に存在しないことを実測したため、本 wave で同節へ収容した。
