---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-09-27
wave: dev-wave-t2104-flock-scope
seq: 3
---

## 再発

### F50

- **再発: 2026-09-27** — campaign flock 保持区間の拡大の wave (D1346 実装) で、段 1 brief の provisional 裁定に「run_campaign は渡された保持を照合し、不一致は fail-closed」と書いた時点で条件 dispatch 13 (`DW-O13`、検証の新設、最遅 = 段 2 前) が成立していたのに辿らず、段 3 の相談 2 本を終えて段 4 に入る直前に気づいた (near miss、実害なし)。契約どおり段 2・3 の成果物を無効化し、照合入力 (driver と run_campaign と producer の lock path) の到達可能性をコードと実 campaign 53 件で測ってから段 2・3 をやり直した (codex 子 3 本の再投入、約 40 分)。型は同じ「L2 節の読了が発火より遅れる」。2026-09-20 に memory へ置いた「brief 直後に条件表 08/09/10/13 を一括再評価する」手順を、memory 索引の 1 行が表出しておらず段 1 で引けなかった。`DW-S01` への 1 文追加は L1 予算満杯のため docs 側へは入れず、memory の索引行へ表出する。
