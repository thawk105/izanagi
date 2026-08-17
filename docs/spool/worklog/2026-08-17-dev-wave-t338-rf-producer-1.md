---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-17
wave: dev-wave-t338-rf-producer
seq: 1
title: RF producer は実装せず、閂の所在を公表層から投入 gate へ訂正した — 起動命令が名指しした既存機構は 2 件とも実在しなかった (docs のみ、branch worktree-dev-wave-t338-rf-producer)
---

## 本文

- **実装しない裁定 ({{D:rf-producer-blocked-by-admission-gate}})。** 段 2 プラン 1 本と段 3 敵対
  レンズ 2 本の総括がいずれも NO-GO。親は所見 20 件を**全件 real** と裁定した (refuted 0 件)。
  実装差分ゼロのため変異 matrix は `DW-S04` により免除。
- **D481 が見ていなかった閂を特定した。** producer を止めているのは公表層ではなく投入 gate である。
  受領証を永続化する関数は `PreregBinding` を必須とし (record-items-v2 §6.10)、その名前は
  D264 が gate 完成まで非 export と定めている。残余は D264 が名指しで却下した
  「台帳だけが producer 実装済みへ進む半実装」に一致するため land しない。
- **起動命令の前提が 2 件とも崩れた (実測)。** 命令は「既存機構は attempt registry を持つ
  `s8b_floor_stats.py` と `s8b_floor_campaign.py`」と書いたが、前者は自らの保証境界として
  attempt registry を保証しないと明記しており、後者のそれは私有 runner クラスの私有メソッドで
  床値 protocol に束縛され export されていない。D229 決定 (7) の名指しは
  `orchestrator/qualification/attempt_ledger.py` である。
- **命令が課した D496 関門は発火しなかった。** 承認済み出力契約 (D282 pin 済み schema と
  record-items-v2) の双方で `floor` / `床値` の出現は 0 件、schema は 3 arm を同一受領証内で
  必須とする。ただし敵対レンズ 2 本が親の一般化を独立に反証したため、結論は承認済み出力契約の
  範囲へ狭めた。実装依存と campaign lifecycle 条件は次 wave の段 1 要件として残した。
- **親が自分の実測を 3 件訂正した。** M4 = 文字列 0 件から実装依存の不在を導けない
  (設置先 package は import graph 上 calibrator を引く)。M6 = 固定三つ組は 6 件ではなく 7 件で、
  pin の権威経路は test ではなく `approval_payload.py` の `load_approval_payload` と
  `read_pinned_blob` である。M2 = 「再利用不能」は直接再利用の範囲に限る。
- **親の provisional 裁定 5 件のうち 3 件が反証された。** (P2) `dry` による end-to-end 受領証、
  (P3) 生死確認 probe、(P4) 必須 kill 3 件の登録可能性がいずれも成立しない。(P1) は差し戻し。
- **D229 決定 (8) の必須 kill 3 件は producer 段では達成できない**と実測記録した。
  「kill 済み」とは記録していない。どの段の受入条件に置くかはユーザー裁定へ返した。
- **段 8 自己改善 1 件。** 起動命令の名指しが実在しなかったことを受け、`DW-S01` の実測義務を
  「承認済み裁定と引数の前提」へ広げた。dev-wave docs の L1 予算は満杯で、当初案 (2 行) は
  90 bytes 超過で赤になったため、空き 14 bytes に収まる 9 bytes の最小形へ縮めて統合した。
  予算値は上げていない。exact pin は `test_check_docs.py` 449 passed / 3 skipped で無傷を確認。
- 裁定パッケージ = `output/insights/2026-08-17_t338-rf-producer/package.md`。
  Q1 (前進の経路、4 択)、Q2 (必須 kill 3 件の帰属段)、Q3 (再利用先の棚卸し) の 3 問。
  親の推奨はいずれも択 (a)。**閂は物理ではなく自分たちで課した 4 つの規則であることを明記した。**

## 次の一手差分

### 更新

- [T-338] **P1・ユーザー裁定待ち (裁定パッケージ 3 問)**: RF producer は実装しなかった。
  閂は公表層ではなく**投入 gate** である — 受領証を永続化する関数は `PreregBinding` を必須とし
  (record-items-v2 §6.10)、その名前は D264 が gate 完成まで非 export と定める。残余は D264 が
  名指しで却下した「台帳だけの半実装」に一致するため land しない。`dry` は qsub 事実を免除しない。
  D229 決定 (8) の必須 kill 3 件は producer 段では達成不能と実測した。順序
  `producer → pilot → validator/consumer → 本走` と `pilot_submission = forbidden` は保存。
  次の一手は裁定パッケージ Q1 の回答 (親の推奨は択 (a) = 投入 gate を 1 単位で完成させる。
  これは T-139 の作業になる)。正本 = {{D:rf-producer-blocked-by-admission-gate}}、
  `output/insights/2026-08-17_t338-rf-producer/`。
  base: 0d1731ca75d96fdd8ab6ab7cb377ee9cb2fff6eba3ba2c2b2e51d826d6a4025e
