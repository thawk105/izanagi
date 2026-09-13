---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-09-14
wave: dev-wave-t1706-schedule-bytes-toctou
seq: 3
---

## 新規

### {{F:one-read-swaps-the-observed-artifact}}. 二重読みを一度読みへ直す起草案が、残る 1 回の読み先をすり替えて別の欠陥を作った [誤前提] [防壁の射程誤認]

- 事象: `tools/codex_reasoning_ab.py` の `supervise_pair` は、run root の frozen copy を
  hash 用と解析用に別々に読んでいた。段 2 の起草案はこれを 1 回読みへ直す際、
  **読む対象を frozen から source へ移した** (`schedule_sha = _sha256(source_schedule_bytes)`)。
  依頼の文面 (「一度だけ読み、その同じ bytes から導く」) は満たすが、
  **現行が持っていた「frozen が壊れていたら拒否する」力を失う。**
  正当な source を保存した直後に frozen を壊れた JSON へ上書きすると、現行は
  `cannot read JSON object` で止まるが、起草案は source を hash・解析して launch まで進む。
  段 3 の敵対レンズ A が、この反例を構成して覆した。
- 根本原因: 「読み回数を 1 にする」という**数の要件**だけを見て、
  「その 1 回が何を観測しているか」という**対象の要件**を見なかった。
  二重読みは (i) 観測の重複と (ii) 観測対象の一致、という 2 つの性質を同時に持っており、
  (i) だけを直すと (ii) を壊しうる。
- 実害: なし (near miss)。段 3 の敵対相談で段 5 の実装前に覆り、
  裁定でプラン v2 を「frozen を 1 回読む」へ差し替えた。
- 恒久対応: {{D:schedule-authenticated-bytes-one-read}} が supervisor の authority を
  frozen と明記し、source を authority にしてはならない理由を本文に持つ。
  機械側の検知は変異 M6 (`_sha256(schedule_bytes)` → `_sha256(frozen_schedule.read_bytes())`)
  が担い、frozen の read 計数が 2 になることで落ちる。
- 再発検知: 読み回数を減らす修正では、**減らした後に残る 1 回が元と同じ対象を読むか**を
  裁定で明示的に確かめる。段 3 の敵対レンズに「この修正が失う観測は何か」を必ず入れる。
