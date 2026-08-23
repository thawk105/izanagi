---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-24
wave: rulings-20260824-recommended
seq: 3
title: rulings 推奨案 5 件を裁定として記録し、元 wave 2 本を回収 land した
---

## 本文

- ユーザー裁定「推奨通りで。main landまでよろしく」を、直前の rulings 出力で提示した
  床値救出 3 件と known-violation 2 件への採用として記録した。設計判断は
  {{D:floor-rescue-recovery-event-ruling}}、{{D:floor-rescue-estimand-ruling}}、
  {{D:s8c-terminal-reason-tightening-timing}}、{{D:known-violation-active-zero-metric}}、
  {{D:known-violation-entry-storage-ruling}}。
- 裁定対象は未 land branch の placeholder だったため、先に元 wave を canonical へ fold した。
  床値 wave は受入 `child-green`・赤 0・flake 0 の受領証を維持し、main `26c8979f` の
  衝突なき前方取り込みを機械再演して `10e8b557` へ land した。known-violation wave も
  `child-green`・赤 0・flake 0 の受領証を維持し、main `10e8b557` を取り込んで
  `21b12b52` へ land した。いずれも既存の locked worktree は変更せず、回収 branch を使った。
- T-1597 は D730 が既に処遇を決めた後に「ユーザー裁定待ち」として起票された正本間矛盾だった。
  新しい裁定を重ねず、D730 の既裁定 (原則実施しない、独立 3 例以上だけ例外) を適用して閉じた。

## 次の一手差分

### 完了

- [T-1597] D730 の既裁定を適用する。一般的な L1 予算引き上げや、空き枠を作るだけの再編は行わない。
  同型実害が独立 3 例以上あり、既存記述の削減でも収容できない個別項目だけ、D730 の例外として扱う。
  remaining: none
  base: b02ccb8df21494d7a230d34dcc0c0c06181b4346a580dd39968be8051ee5814a

### 更新

- [T-1505] **P1・裁定済み**: 8b production 配線を止めていたユーザー判断 5 点は
  {{D:floor-rescue-recovery-event-ruling}}、{{D:floor-rescue-estimand-ruling}}、
  {{D:s8c-terminal-reason-tightening-timing}} と既存 D510 で解決した。次は [T-1601]〜[T-1604] の
  実装・設計を行う。正式測定の認可を AI へ移したとは扱わない。
  base: 27cc0437e045398e5ca6910fcf052092fa4325c533239b670e068422ea5f80f6
- [T-1601] **P1・裁定済み・実装待ち**: 8b 専用 recovery event を共通 core の明示的 semantic handler として
  実装する。別 process の引き取りは scheduler accounting 等の外部証拠と fencing が揃う場合だけ許す。
  owner 束縛の全体緩和と、profile 許可表だけを増やす実装は禁止する
  ({{D:floor-rescue-recovery-event-ruling}})。
  base: 75c93712bfdaa6bb6bdd7fdb131f83f5b17a96c8dde3a2c78f12238353c9368f
- [T-1602] **P1・裁定済み・実装待ち**: 観測開始後の再走は、外部証拠で確認した node 障害と
  scheduler による外部中断の閉じた集合だけに許す。wall timeout、単なる process 消失、自己申告は
  除外し、exact 理由値と証拠源を実装前に凍結する ({{D:floor-rescue-estimand-ruling}})。
  base: e3253962b600c303de8154f4c5233f8b6c5debcad957b77a42fb60aea27f632f
- [T-1605] **P1・裁定済み・実装待ち**: known-violation は不可逆な歴史群と新規群へ分け、
  運用目標を新規群 0 とする。遡及訂正枠の一回性は解除しない
  ({{D:known-violation-active-zero-metric}})。
  base: 9115aa44db151a4035c12837250b693151c86c04f386e70500957f455708785c
- [T-1606] **P1・裁定済み・実装待ち**: 1 finding 1 file の entry 単位格納へ移行してよい。
  逐語 mirror は単純削除せず、複合 key、tracked regular file / HEAD 一致、全 entry の実 commit 照合、
  公開出力の逐語検査、投影外 consumer 閉包を同じ wave で置換する
  ({{D:known-violation-entry-storage-ruling}})。
  base: 57f461bb6856156d2b9c5e1c1d4edd5e6527f04764b7e76ed0d94d16f36b8ebe

### 新規

- {{T:s8c-terminal-reason-tightening}} **P1・裁定済み・実装待ち**: 次の正式 8c 走行または凍結世代更新より前に、
  事前分類受領証の失敗理由と terminal の再走理由の一致検査を必須化する。既存成果物と今回の互換
  facade は遡及変更せず、実装まで現行経路を新しい正式証拠の生成に使わない
  ({{D:s8c-terminal-reason-tightening-timing}})。
