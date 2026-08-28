---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-28
wave: worktree-dev-wave-t2068-a2-partial-raw
seq: 1
title: A-2 exact-one partial raw authorityを実装・変異・受入した（コード + docs、branch worktree-dev-wave-t2068-a2-partial-raw）
---

## 本文

- T-2022残置authorを含む同一2file所有を再検査し、T-2022 dirty 0、live process 0、baseからcurrent mainの
  対象差分0を確認した。初回author receiptは`f43_fragment`だったため完成扱いせず、外来差分をD95 Codex
  authorへrefocus/fixとして戻した。
- exact 2 workload / successful subset exact 1だけのpartial v4、failed raw非読取、局所anomaly・effect非正の
  outer reject、canonical pathとevidence再導出validatorを実装した。full-successとauthority-noneはv3を維持した
  ({{D:a2-partial-raw-authority}})。
- 敵対review 2本はreal must-fix 4件を出し、fix後focus reviewはACCEPT、closed 4 / partial 0 / regressed 0。
- 対象file全走は98 passed。F662の空`/tmp/.git`が既存nodeを赤にしたため、他人所有物を削除せずrepo外TMPDIRで
  再走した。production gateは変更していない。
- 変異attempt 1のbaseline PARSE_ERRORとattempt 2のMISMATCH 3件を保全し、expected node完全集合へ再登録した。
  最終matrixは8/8 KILLED、SURVIVED 0、TIMEOUT 0、artifact error 0。
- 正式受入は18624 passed / 62 skipped、red 0、child-green。tested main `c384a90a0`、tested tip
  `e4cb2da91`、log SHA-256 `3cf842d00e67a9cbc67abe164b416ed42dc532de44e583926770d9af3b66cebd`。
- 完走済みA-2 artifactは非接触。failed sibling証拠一般化、cross-attempt reuse、別campaign、複数success subset、
  汎用fan-outはscope外のまま。

## 次の一手差分

### 完了

- [T-2068] exact-one partial raw authorityの実装、敵対review、8変異、受入を完了した。
  remaining: none
  base: 7f9eb1379e17008d6b46e0f5868e32822533d1236bedaa3360c33fce4b4bbd4e
