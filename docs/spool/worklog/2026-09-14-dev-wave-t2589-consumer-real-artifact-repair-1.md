---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-14
wave: dev-wave-t2589-consumer-real-artifact-repair
seq: 1
title: [T-2589] 対 consumer の実成果物非互換 2 件を直し、balanced の stock-inline 対を再測定なしで認証した (コード + docs、branch worktree-dev-wave-t2589-consumer-real-artifact-repair)
---

## 本文

- ユーザー指示は「codex に相談して決める。過剰実装・過剰ガードレールは禁止」。
  相談は別系統モデルの read-only 静的検査で行い、その結論と親の裁定を突き合わせた。
- **相談は親案に同意したうえで、親の説明を 3 点否定した。3 点とも採用した。**
  (1) 「受理集合は変わらない」は誤りで、拒否述語の撤去である以上受理集合は広がる。
  (2) D1876 は「保証しない範囲を明記する」前例ではあるが、既存検査の撤去を認可した前例ではない。
  (3) fixture 自体が実 producer と別物で、誤った等式を仕様化していたテストは撤去と両立しない。
- 親が独立に見つけた追加事項: 撤去対象のテストは **F909 の恒久対応そのもの**だった。
  一般の教訓は有効なままなので supersede 追記で現況だけを示した。決定は
  {{D:t1998-consumer-artifact-truth}}。
- 敵対レビュー 2 本 (正しさ境界 / 整合と実効性) は実装を止める所見を出さなかった。
  レンズ A は producer 経路・導入 commit・実 WAL を辿って「旧等式が正しい対応検査になる反例は
  無い」と確認し、レンズ B は「元の誤検査を戻すと新 fixture の受理例が落ちる」ことを示した。
  レンズ A の real 所見 2 件 (非保証記述の射程が広すぎる、1 成果物からの一般化) は、
  docstring の是正と前 wave insight への追補で閉じた。
- **認証された結果: accepted。** ratio 1.1122537536191646、improvement_percent 11.225375361916456。
  baseline median 3893509 tps (cv 0.0227)、target median 4330570 tps (cv 0.0128)、両 arm とも
  `unstable` は false。**再測定はしていない。** 2026-09-13 に保全した同じ成果物を通した。
  旧 headline の +11.3% は事前登録が期待値として固定しなかった値であり、近い値が出たことは
  事後の観察であって事前の予測ではない。
- 事前登録の bytes と 2 つの sha 定数は 1 byte も動かしていない。版は v1 のまま。
- 実装子の追加した linux-baremetal 受理テストは前提が成立せず赤になった。事前登録が pegasus 契約を
  pin している以上、他環境の成果物を端から端まで受理させるテストは書けない。前置選択を直接呼ぶ
  単体テストへ差し替えた。既存テストの期待値は 1 つも変えていない。
- 変異 matrix は baseline PASSED、3 変異すべて KILLED、期待 node 完全一致。
  **DW-M01 の逸脱を 1 件記録する** — spec は実装子の投入後に書いた。変異対象は親が段 5 brief で
  実装前に確定させた箇所であり実装子の出力から選んでいないが、登録の時点は契約より遅い。
- 受入台帳に削除 node が 0.0 秒で残り追加 node が未登録である。レビュー B のコード上の判定どおり
  受入は赤にならなかった。放置の判断であり修正ではない。
- 逐語・変異台帳・詳細は `output/insights/2026-09-14_t2589-consumer-real-artifact-repair/`。

## 次の一手差分

### 完了

- [T-2557] balanced の stock-inline 対を正式に測り、既存 consumer で認証した。
  accepted、improvement_percent 11.225375361916456。事前登録 v1 の bytes は不変。
  remaining: none
  base: 8b7791b0f38d364aabaa192fbb1c4e4713dd84e87ebd17b61afa1d5f2ff672d1
- [T-2589] 対 consumer の実成果物非互換 2 件を是正した。前置は環境契約から hash 束縛で解決し、
  再導出不能な腕内等式は撤去して非保証範囲を明記した。
  remaining: none
  base: 9b38d83b27b3a6ee99b81a5c782a4d7fedf69f5a7947bafc6ee6a88d77456595
