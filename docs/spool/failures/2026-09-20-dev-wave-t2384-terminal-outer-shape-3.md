---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-09-20
wave: dev-wave-t2384-terminal-outer-shape
seq: 3
---

## 再発

### F50

- **再発: 2026-09-20** — 8c formal consumer の terminal 外枠 gate の wave (D1730 実装) で、条件 dispatch 13 (`DW-O13`、gate 新設時、
  最遅 = 段 2 前) を段 1 brief に「gate を足す」と書いた時点で辿らず、段 3 の後に気づいた (near miss、実害なし)。契約どおり段 2〜4 の成果物を無効化し、
  実環境 log で gate 入力の到達性 (outer 5 key exact 490/490、attempt ごとに terminal 1 件 = 16/16) を実測してから段 2〜4 をやり直した
  (codex 子 3 本の再投入、約 15 分)。型は同じ「L2 節の読了が発火より遅れる」。段 1 brief を書き終えた直後に条件表 08/09/10/13 を
  一括再評価する手順を memory へ置いた。`DW-S01` へ同旨の 1 文 (76 bytes) を足す案は `check_docs` の L1 予算
  (10701 > 10625 bytes) に当たり、D782 / D730 に従い docs 側へは入れていない。
