---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-16
wave: dev-wave-t1167-8c-reservation-wiring
seq: 1
title: 8c 事前登録 C12 は構成上充足不能と実測し裁定パッケージへ返す (docs、branch worktree-dev-wave-t1167-8c-reservation-wiring)
---

## 本文

- 依頼は「8c launch path へ配線する」「契約から明示的に外す」の二択で決めて実装することだったが、
  実測で二択の前提が覆ったため、どちらも実装せず裁定パッケージとして返した。裁定本体は
  {{D:s8c-c12-unsatisfiable-by-construction}}。
- 依頼の前提自体は正しかった。`check_reservation` の実 call site は t126 driver、8b oracle driver、
  8b floor campaign の 3 箇所 2 系統で、8c launch path からの到達はゼロである。
- 台帳が記していたより乖離は深い。契約が要求する `single_process_required` は `reservation.py` に
  存在せず、評価器の到達判定は同一 module 内しか辿らないため、正しく cross-module 実装しても
  C12 は永久に充足しない。
- 現在の緑は捏造した被検体に対する緑だった。契約は 12 条件すべてを `machine_checkable: false` と
  しており、実 tree に対して C12 の述語は一度も走っていない。既存テストは
  `def single_process_required(): pass` だけを持つ捏造 module に述語を撃っている。
- **契約改訂側へ渡すべき実測値**: 契約 row を in-memory で反転して実 HEAD の blob に評価器を
  実行したところ、C12 は `UNSATISFIED` / `environment-contract-consumer-absent` を返した。
  しかしこの reason が指す `lookup` と `attest_and_build_receipt` は実際には 8c で走っている。
  反転は赤を出すのではなく、実在する強制を不在と誤って報告する。
- 親 brief の誤りを 2 件、子の指摘と自分の再測で訂正した。(a) `lookup` の位置は `loop.py` ではなく
  trigger gating module の別名経由である。(b)「8c は attestation を通る」は pegasus 契約に限った
  主張で、linux-baremetal は `attestation_mode` が `none` かつ `single_process=False` である。
  親の当初の二分は後者を落としていた。
- 配線側は実装可否を開かなかった。D419 が「強制だけを先に入れる」を却下しその解除をユーザー手番と
  定め、8c 用 wrapper の新設も他タスクの所有境界としているためである。実測でも
  `IZANAGI_RESERVATION_*` を供給する production launcher は床値 campaign と t126 の 2 本だけで、
  8c 用は存在しない。
- 外す側は稼働中の別 wave が契約 JSON・評価器・凍結世代を所有しているため本 wave では実装できない。
  起動時と裁定直前の 2 回、稼働 wave の編集面を確認した。
- `check_reservation` が `host` / `script_sha256` / `nonce` を何とも照合しておらず単独性も
  証明しないことを実測したが、この権威不足は既に裁定済みの別タスクが所有していたため
  新規起票しなかった。
- 敵対レンズ 2 本はいずれも配線に反対し、独立に「捏造 fixture だけが通る」「実測 sink は
  `loop.run_campaign` であって親が挙げた分岐ではない」を指摘した。後者は採用し、
  配線を検討する場合の sink として裁定パッケージへ書いた。
- 実装差分ゼロのため変異 matrix は免除。docs のみの変更である。

## 次の一手差分

### 更新

- [T-1167] **P1・ユーザー裁定待ち**: 8c 事前登録 C12 の allocation 節の処遇。実測により
  「配線する / 契約から外す」の二択は前提が誤っていると判明した
  ({{D:s8c-c12-unsatisfiable-by-construction}})。C12 は未配線なのではなく**構成上充足不能**で、
  実在しない symbol を要求し、かつ到達判定が同一 module 内限定のため正しい cross-module 実装でも
  充足しない。実際に欠けているのは allocation 検査だけで、`lookup` と attestation は
  pegasus 経路では実際に走っている。
  **択 (a) 実測 sink へ isolation policy で gate した allocation binding を配線する**
  — 前提として D419 の却下解除 (ユーザー手番) と、`IZANAGI_RESERVATION_*` を供給する
  8c 用 launcher の新設が要る。後者は他タスクの所有境界。
  **択 (b) allocation 節を契約から外す** — 現に成立している保証は 1 つも消えないが、
  正式 8c の受理が allocation 証拠を要求するという事前登録の意図が消える。実装面は
  稼働中の別 wave の所有。
  **択 (c) 節を「実現可能な allocation binding」へ縮小する** — 単独性の主張を落とし、
  PBS job・boot・期限の束縛だけを条件にする。**親の推奨は (c)** — (a) は供給側 launcher が
  無いまま fail-closed 検査を置くことになり、(b) は充足不能の原因が allocation 節だけでない以上
  乖離を閉じきらない。ただし (c) も述語の表現力を直さない限り機械判定は変わらないため、
  {{T:prereg-predicate-module-local-reachability}} と同時に扱う必要がある。
  base: 2e96f164d13da69e61f8f6260eff73087dfa948877604708e253a23cbe8eb83d

### 新規

- {{T:prereg-predicate-module-local-reachability}} **P1・新規**: 8c 事前登録述語族の到達判定が
  同一 module 内の top-level 定義しか辿らない。設計上 cross-module に分かれている consumer は
  実行されていても「不在」と判定される。C12 はこれにより構成上充足不能だが、同じ helper を
  6 条件の評価器が共有しているため C12 固有の問題ではない。述語の表現力を上げるか、
  各条件を述語が実際に検査できる形へ再定式化するかを決める。
- {{T:c12-false-negative-on-flip}} **P1・新規**: C12 の `machine_checkable` を反転すると、
  実 tree に対して `UNSATISFIED` / `environment-contract-consumer-absent` を返す。しかし
  この reason が指す 2 つの consumer は pegasus 経路で実際に走っており、診断は誤りである。
  反転を行う改訂の中で条件を再定式化し、実在する強制を不在と報告しない形にする。
  誤診断のまま land すると、実在する強制を消す方向の改修を誘発する。
