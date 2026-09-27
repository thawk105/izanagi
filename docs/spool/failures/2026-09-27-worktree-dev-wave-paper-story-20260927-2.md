---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-09-27
wave: worktree-dev-wave-paper-story-20260927
seq: 2
---

## 再発

### F1

- **再発: 2026-09-27 (凍結物に残った執筆時点の誤り、論文ストーリー 2026-09-27 版の wave で発見)** — 2026-09-26 版 §6・§7 は認定較正 record の現物を「計 8 record」「現物は 8 record」と現在形で書いたが、MOCC の動作点を pin C で較正した 3 件 (`f72ad2c52`、2026-09-26 14:12 JST、D2248) は同版の起点 `6d198ca8a` の祖先で、起点の `output/env/pegasus/calibration/registered/` は 11 file だった (2026-09-23 版の起点 `65fd1422f` では 8 file で真)。前版から運んだ件数の文を、起点の現物の件数と照合せずに運んだのが原因。2026-09-27 版の §7 担当の子が起点の tree を数えて見つけ、同版の冒頭・§6・§7・§10 と README で訂正した。版の再導出では、運ぶ件数の文を起点の現物 (tree の file 数) で数え直す。
