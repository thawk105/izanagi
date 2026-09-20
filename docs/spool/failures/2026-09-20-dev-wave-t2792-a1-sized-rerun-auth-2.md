---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-09-20
wave: dev-wave-t2792-a1-sized-rerun-auth
seq: 2
---

## 再発

### F39

- **再発: 2026-09-20** — A-1 sized の認可 record gate を足す wave で `orchestrator/campaign/paper_story_a1_paired.py` へ 121 行を挿入し、
  `test_ccbench_spawn_sites.py` の deferred-gate 登録簿が pin する `run_measurement` の sink 行番号 (7428、台帳と期待表の 2 箇所) がずれて
  1 node が赤になった。段 1 の pin 閉包は同 test file を path 検索で hit させながら「AST 構造 pin」と分類して行番号を読まず、段 3 の相談と
  段 6 のレビュー 2 本も指摘しなかった。**違いは検出点である** — 2026-09-08 の再発が足した運用 (位置を台帳に持つ test を焦点走の consumer 集合へ入れる)
  を親が守っていたため、受入全走でなく親の焦点走 1 回目 (land 前) で出て、fix 1 巡 (pin 7428 → 7545) で閉じた (実害なし)。
  恒久対応の置き場所の問題 (`DW-O09` の単節予算) は 2026-09-08 の記述から変わっていない。運用の補強として、
  同 driver を触る wave の段 1 で `grep -n "paper_story_a1_paired" orchestrator/tests/test_ccbench_spawn_sites.py` の 5 つ組を読み、
  fix 1 巡分を計画に入れる (memory `closure-and-search-discipline` に追記)。
