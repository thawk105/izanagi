---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-03
wave: dev-wave-t2229-t2230-verify-cost-erratum
seq: 1
title: [T-2229] 「直列性検査 1 回 23 分」の帰属と積み方、および cell と変種の単位混同を追記訂正した (docs + insight、branch worktree-dev-wave-t2229-t2230-verify-cost-erratum、実装面 0・変異 matrix 免除)
---

## 本文

- **ユーザー依頼の scope は「本題の訂正だけ」**で、仮想リスク向けの gate・検査・台帳・一般化の
  追加は scope 外だと最初に確定していた。訂正は追記で行い、当時の判定は遡って書き換えない。
  実装面の差分は 0 で終わり、子は 1 本も起動していない (docs-only の軽量版)。
- **起動時の重複検査で、回避すべき file が入れ替わった。** ユーザーは
  `docs/b10-multinode-formal-run-design.md` を別 wave が編集すると指示していたが、同 file には
  本 wave の訂正対象語 (「23 分」「3.83」「12:00:00」) が 1 件も無く、branch にも作業木にも
  差分が無かったので、そもそも当たらなかった。代わりに
  `docs/archive/worklog-phase3-0902-1189.md` の H2 直後 (訂正注記を置く slot) を
  `dev-wave-t2200-k2-role` が staged で所有していた。同 slot を避け、1189 への in-file 注記は
  書いていない。作業木の未 commit 差分まで見なければ、この衝突は見えなかった。
- **canonical 台帳の既存 bytes は fold だけが追記でき、書き換える経路が無い。** そのため
  D1485 と D1489 の本文は直さず、訂正を {{D:verify-cost-mixed-interval-erratum}} の追記として
  書いた。この導線は `docs/spool/README.md` の不変条件節を読んで初めて分かった。
- **着手時の見込みを実測が 1 つ覆した。** 親は「1189 の検査器並列化タスクも max 誤りの
  担い手である」と見込んでいたが、同項は既に「1 回 22-24 分」へ直っており、費用の単位も
  「45 cell ではなく 15 認証単位」へ訂正済みだった。残っていたのは帰属の誤りだけである。
  これに合わせて A-6 insight の追記の該当行を書き直した。
- **数値は一次資料から取り直した。** 帯 1346.9-1465.6 秒は
  `output/insights/2026-09-02_b10-trace-truncation/README.md`、
  read-heavy campaign の commit 3 / 開始 4 / 登録 15 点と「性能 cell = 3 block x 15 点 = 45」は
  `output/insights/2026-09-02_b10-missing-iterations-scope/README.md` にある。
  積み直し (約 24.43 分 / 約 4.07 時間 / 約 2.95 倍) はその場で検算した。

## 次の一手差分

### 完了

- [T-2230] `docs/archive/worklog-phase3-0902-1187.md` の「15 cell 中 3 cell」に、H2 直後の
  訂正注記を追記した。完了したのは 3 変種の認証 attempt (登録 15 点のうち 4 点開始・
  commit 到達 3 点) であって 3 cell ではないこと、性能 `fitness_tps` が全件 null で性能 record が
  1 件も無いこと、1 workload の性能 cell は 3 block x 15 点 = 45 なので「15 cell」という母数が
  存在しないことを書いた。既存 bytes は 1 バイトも変えていない (32 行の純追記、削除 0 行)。
  remaining: none
  base: f46b332d5b75093a5e53b505cd83b629e39738c1c8d624ef5da49add59569f65

### 更新

- [T-2229] **P2**: 「直列性検査 1 回 23 分」の帰属 (混合区間であって検査器単体の費用ではない) と
  積み方 (23 分は帯の max でなく中ほど。上端 1465.6 秒で 10 回は約 4.07 時間、`12:00:00` の倍率は
  約 2.95 倍) を訂正した。到達先は {{D:verify-cost-mixed-interval-erratum}} (D1485 と D1489 の分)、
  `output/insights/2026-09-02_paper-story-a6-certification/README.md` の追記訂正、
  `docs/archive/worklog-phase3-0902-1187.md` の訂正注記の 3 つ。walltime `12:00:00` の結論は
  動かしていない。残るのは `docs/archive/worklog-phase3-0902-1189.md` の検査器並列化タスクの
  逐語への in-file 注記 1 か所だけで、同 file の訂正注記 slot を並行 wave が所有していたため
  本 wave では書いていない (帯は同項で既に「22-24 分」へ直っており、残る誤りは帰属だけ)。
  base: 7c4b8b2e68a247b2d6bdfbdd898b173b8a2728996e7dd1dca9d50748c493ec77
