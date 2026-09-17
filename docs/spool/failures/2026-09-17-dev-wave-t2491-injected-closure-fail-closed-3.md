---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-09-17
wave: dev-wave-t2491-injected-closure-fail-closed
seq: 3
---

## 再発

### F1

- **再発: 2026-09-17** — [T-2491] wave の親が handoff・brief v1.1・段 4 裁定の時刻 (JST) を `date` や
  file の mtime で確かめず推定で書き、実時刻より 30〜60 分遅い値 (例: 裁定 22:55 → 実 22:09) を 5 箇所に残した。
  段 6 レビュー B が「事前登録の時刻表記が焦点走・統合 commit の時刻と照合できない」と指摘し、親が全部 mtime と
  `git log --format=%ci` で実測して訂正した (事前登録 → author 投入 → 実装の順序は保たれており成果物への影響は無い)。
  転写でなく推定でも同じ型になる。時刻・日付は書く直前に `date` / mtime / commit 日時から取る。

## supersede 追記

- F918 **supersede: 2026-09-17** — 恒久対応の「検査本体の強化はユーザー裁定へ返した」は D1882 の裁定と {{D:injected-closure-unswallowed-rule}} の実装 (commit 125ab5fd1 + 79dd07742、`orchestrator/tests/test_ccbench_spawn_sites.py`) で実施済み。同一置換の変異で閉包検査が旧版 PASSED / 新版 FAILED を実測 (`output/insights/2026-09-17/t2491-injected-closure-fail-closed/`)。再発検知の「負例だけが赤で閉包検査が緑なら何も保証していない」は引き続き有効。
