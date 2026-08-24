---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-08-24
wave: dev-wave-t319-official-marker-allowlist
seq: 3
---

## 新規

### {{F:acceptance-self-merge-rewrites-running-waiter}}. 受入の自動 main 取り込みが実走中の待ち手 bytes を差し替え、全走 1 本を receipt 未発行で捨てた [手順漏れ] [コンテキスト浪費]

- 事象: local main を含まない wave tip から受入全走を投入した。待ち手は claim 後に自分で main を
  merge して tip を進め、full suite を最後まで走らせたが、終端の receipt 照合で
  `receipt-waiter-sha256-mismatch` を検出し `restart-required` (rc=70) で停止した。
  expected は merge 後の tree にある `tools/dev_wave_wait.py` の
  `4b4a5aa4b9ae67a4819449a39d2e4b2b441ef0d942f90d23f2c3dc49dacfc7d0`、
  actual は起動時に実行した merge 前の
  `67bf0adb04662249c766d25e3a9c885939d3402fb74bc4dd4a9e5087c1e14523` である。
  receipt も log も公開されないため走行は成功として数えられず、full suite 1 本と
  その wall-clock が丸ごと失われた。この wave は同じ理由で 1 回中断し、3 度目の context で再開した。
- 根本原因: 待ち手が claim 後の behind を自分で解消する活性経路 (F522 の恒久対応が指す経路) と、
  D524 が課す「実行 bytes == tree の blob」の束縛が、**取り込む差分が待ち手自身を変更するとき**に
  両立しない。待ち手は自分を書き換える merge を自分で実行するので、実行中の bytes は定義上
  merge 後の tree と別物になる。照合は終端に置かれているため、赤は全走が終わってから出る。
  F385 / D524 が積み残した「起動権が tip 側待ち手にある」構造の、費用が最大化する形での顕在化である。
- 恒久対応: 受入投入前に `HEAD..main` が束縛対象の実行体 (待ち手・launcher・runner) の bytes を
  変えるかを検査し、変えるなら親が先に wave tip へ main を取り込んでから投入する。
  本 wave はこの順で投入し直し、待ち手 SHA 不一致を再現しないことを実測した。契約の同期は
  {{T:acceptance-bound-executable-main-takein}} が `DW-O18` / `DW-O27` と subprocess test に対して行う。
  F522 の「停止せず活性経路を使う」は取り下げない — 本項はその前提条件を足すものである。
- 再発検知: main 側が `tools/dev_wave_wait.py` を変更した状態で、behind な tip から acceptance を
  投入する subprocess test。launcher が全走後に `restart-required` を返し receipt を発行しなければ再発とする。
  先に main を取り込んだ tip からの同一投入では receipt が発行されることを対の正例とする。

## 再発

### F106

- **再発: 2026-08-24** — [T-319] official marker allowlist wave の resume 3。**9 度目**であり、
  受入全走の投入から結果取得までの間に、親が段 7 の spool fragment 2 本
  (`docs/spool/decisions/...`、`docs/spool/failures/...`) を worktree へ書いた。
  **新しいのは失敗の現れ方である。** 過去 8 件は harness preflight の `rc=2`、走行中の偽の赤、
  走行後の共有木事後検査 (`rc=125`)、workspace-write の子による削除のいずれかだった。今回は
  待ち手の**走行後 clean 検査**が `stage=postrun-clean rc=70` で止め、未追跡 2 file を stderr へ
  列挙した。full suite は最後まで走って `1 failed / 15068 passed / 60 skipped` という
  利用可能な判定を出していたが、**receipt が発行されないため land には一切使えない**。
  判定が出ているのに捨てられる点で、preflight で走る前に止まる型より損失が大きい。
  さらに、直前の再発 (同日) が恒久対応の向きを「走行前に、結果を待たない記録を書き終えて
  commit しておく」という順序の固定だと明記しており、親はその追記を読める位置にいながら
  同じ順序違反を犯した。**規律の言語化が順序の設計の代わりにならない**という 2026-08-06 以来の
  観察を、これで 3 例目として強める。恒久対応は F106 のまま。本 wave は記録と段 8 の編集を
  すべて commit し終えてから最終受入を投入する順序へ切り替えた。
