---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-11
wave: dev-wave-t786-docs-budget
seq: 1
title: docs 予算棚卸し wave — 上限を上げずに 8 件を入庫し 6 件を審査結果として返した (コード + docs、受入 8715 passed / 20 skipped / 558.18 秒 / rc=0、変異 6/6 KILLED、branch worktree-dev-wave-t786-docs-budget)
---

## 本文

- **予算値を 1 bytes も上げずに入庫した** ([T-127] の「上限を上げず空ける」)。実測は
  L1 10,625 → 10,606 / 10,625、L1.5 9,554 → 9,564 / 9,566、`DW-O09` 935 → 997 / 1,000、
  `DW-O18` 615 → 733 / 1,000、rulings command 4,991 → 4,996 / 5,000、
  dev-wave command 9,497 → 9,498 / 9,500。枠は意味等価な縮約 30 箇所で 588 bytes 作った
  (L1 3 箇所 49 / L1.5 12 箇所 213 / rulings 10 箇所 187 / dev-wave command 5 箇所 139)。
  方針は「tool が既に強制している内容の列挙を pointer へ畳む」で、義務は 1 つも落としていない。
- **scope が wave 中に 8 件 → 13 件へ増えた。** 起動基準 (worklog 404) から main を取り込むと
  worklog 407/408 が同じ [T-786] を「同梱 9 件 + [T-789] 合流」へ更新していた。最新裁定を採り
  狭めずに実施した ([[ruling-status-follow-to-latest-entry]] の適用)。さらに並行 rulings
  セッションが 10 件目 (索引は local main の worklog で作る) を追送し、採用した。
- **親の provisional 裁定 (P1) を段 3 で撤回した。** 「待ち手正本へ結線すれば [T-757] と
  [T-738](c) は 0 bytes で解消する」と読んだが、`tools/dev_wave_wait.py` は今も `--pid` を受理し、
  pid-file が producer 自身の産出かを検証せず、`/proc` 不読時は starttime 照合なしの PID-only へ
  降格する。[T-757] は明文で入庫し、[T-738](c) は導線消滅として不要と判定した。
- **親 brief の「現状の余白では 1 件も入らない」も過度な一般化だった。** L2 単節予算で完結する
  候補は層合計の余白と無関係に入る — [T-784] は `DW-O09` を 935 → 997 にしただけで入り、
  同節の縮約を要さなかった。
- **[T-765] は byte では入るが安全裁定として除外した。** `DW-S04` の変異免除を「実装しないと
  裁定した wave」から「実装差分ゼロの全 wave」へ広げる案で、段 3 レンズ A が blocker 判定し
  段 2 のプラン自身も非等価と認めた。本 wave 自身がその免除の第一号になりえた。
- **段 2 の 1 回目は model call 上限 100 で強制終了し、成果物ゼロで 1,377 秒を空費した。**
  原因は `tools/check_docs.py` (4,700 行) の網羅読み。再投入では親の実測値 (層別 byte 表・余白・
  該当行番号) を prompt へ前渡しし、上限を 300 へ上げ、「200 call を超えたら打ち切って
  その時点の結論を書け」を明記して成功した。
- **段 6 の fix 子は出力が完全 (`## 総括` あり、2,066 bytes、`codex_exit_code=0`) でありながら
  receipt の `evidence_status=invalid` で未採用扱いになった** (`launcher_rc=1`)。作業物は tree に
  入っていたため、親が実走 (408 passed) と独立監査 (guard が fail-open でない・既存テストの
  期待値が無改変・negative control 9 件が guard を通過し続ける) を経て採用した。
- **縮約 wave では reflow も pin を壊す。** `DW-S06-C` の reasoning 文は行単位の exact 一致で、
  D2 巻き戻し構造の正規表現は `段 2 プラン前` を空白込み literal で見る。改行位置を変えただけで
  2 度 `check_docs` を赤にした。詳細は {{F:reflow-breaks-line-anchored-pins}}。
- **段 4 の変異事前登録が 2 つの層を取り違えていた。** 登録した 9 件は docs fixture を壊す形で、
  実装子はそれをテスト側の negative control として実装した (こちらが正しく、かつ強い)。
  harness の matrix は production を壊す 6 件へ組み直した。**6/6 KILLED、MISMATCH 0、SURVIVED 0。**
  特に M5 (打消し語検査を殺す) が `decoy-optional` に殺されたことが、新設検査が
  「literal がそこにあるか」だけを見る恒真な検査でないことの実証である。
- 受入全走は **8715 passed / 20 skipped / 558.18 秒 / rc=0** (受入 lease 内、計算ノード dispatch)。
  記録 commit を含む tip で走らせ、走行前に main を取り込んで base digest を取り直した。
- 逐語・変異台帳・審査結果 package は
  `output/insights/2026-08-11_t786-docs-budget/` に凍結した。

## 次の一手差分

### 完了

- [T-773] 待ち手正本 `tools/dev_wave_wait.py` の結線を docs 層で完了した。command 段 6/9 と
  `DW-C00` / `DW-O01` の normative line を全文一致で pin する機械検査
  `_check_dev_wave_waiter_consumer_pins` を新設し、打消し語の併記も赤にする。runtime 層の
  未閉包は {{T:waiter-runtime-receipt}} へ分離した。
  remaining: none
  base: fc0aedd8ce7a8e0f33693040cd2e4e8fb71cdbe802376b1def9ffc01637c6dcb

- [T-757] producer 自身が `--pid-file` を `echo $$` で書く義務を `DW-O01` へ明文化した。
  結線による構造的不要化は成立しないことを段 3 で実測したため、明文で入庫した。
  remaining: none
  base: b12da00d4a5ef6c0d741d831cdb903a3b16dd272de9b52b65cb55f986154770e

- [T-769] `DW-M08` へ「期待 node は完全集合で、正規化した記録 node との完全一致だけを KILLED と
  する」を入れ、3 度目の見送りを解消した。F138 の probe 条件は保持した。
  remaining: none
  base: c31f3440042cce814228e2e1e9635769d96a968c592a9e6fb2d48cf71b292ef2

- [T-775] (i) `DW-S05-C` へ「親の名指しを網羅と見なさず制約 meta-test を自ら洗い出す」、
  (ii) `DW-M08` の完全一致判定をともに入庫した。
  remaining: none
  base: 8a304e32147761a05b2be9e766d627f6d6330c381da46a3c089d71873a40e5f6

- [T-784] `DW-O09` の pin 閉包へ「全 field から同一性 hash を導く dataclass・schema」を加えた。
  L2 単節の既存 slack 内で完結し、他層を消費しなかった。
  remaining: none
  base: 0b5a1aaeb656eb6fbb749c8d14dae3c6dc6a2bd9ec68a050d7391bc9fe6d0c75

### 更新

- [T-786] **P2・棚卸し実施済み → 未入庫 6 件の採否がユーザー裁定待ち**: 入庫 8 件 (rulings 3 /
  [T-773] / [T-757] / [T-769] / [T-775] / [T-784] / [T-789](3))、未入庫 6 件。
  **予算引き上げは推奨しない** — 未入庫 6 件のうち 2 件は別解 (機械検査化・運用) で閉じ、
  2 件は実害が `DW-G03` の独立 2 例に届かず、1 件は本 wave の結線で不要化し、1 件は再訪条件が
  未成立で、引き上げを正当化する候補が 1 件も残らなかった。審査結果の正本は
  `output/insights/2026-08-11_t786-docs-budget/verbatim/package.md`。
  base: 5a18c288956585d58e64e1444eada7eba3f8c5c27a3e8e23ef236dab98df975f

- [T-765] **P3・ユーザー裁定待ち (安全) → 予算ではなく免除範囲の問題として差し戻す**:
  `DW-S04` の変異免除を「実装差分ゼロの wave」へ一般化する案は byte 上は入る (置換自体が -30) が、
  変異検査の免除範囲を実際に広げる。択 = (a) 一般化する / (b) 現行のまま曖昧さを残す /
  (c) 曖昧さだけを解く別表現を探す。親の推奨は (c)。
  base: 4d8d6aaef2f321b136cf91cf78d0f335c982d79e14afade6a5e60a6343ba543d

- [T-788] **P3・未入庫 → docs でなく機械検査で閉じることを推奨**: `DW-O02` への制御 byte 走査
  1 行は L1.5 を 110 bytes 超過して入らなかった。artifact 生成側で走査すれば L1.5 を
  1 bytes も使わずに閉じるため、{{T:control-byte-scan-tool}} へ移す。
  base: 9e98779f891d412fe7c6985744903e5617f59cef39265a9be8c0da4bb4982a51

- [T-789] **P2・(3) 入庫済み → (1)(2) は再訪条件付きで返す**: (3) は `DW-O18` へ入った。
  (1)(2) は `DW-O02` へ 105 bytes 必要で入らず、既存義務 (prompt に読めなければ即停止する指示を
  入れる) が実質的に (2) を覆う。**再訪条件 = 同型の空費が 2 例目に達したとき**。
  base: 9394f69cd9f2f80d9c4642bc08c0bb8b2e7ce1200adda6e8398893afa8151722

- [T-760] **P3・再訪条件は未成立**: L1.5 の残余は 2 bytes で、「余白が出たとき」は成立しない。
  base: 8569c174afd0430ce16ee6c73e520157623ce3d2f04210d00ee2c8aa243b6d63

### 新規

- {{T:waiter-runtime-receipt}} **P2・新規・ユーザー裁定待ち**: [T-773] の結線は docs 層までで、
  **manager が実行時に本当に待ち手正本を呼んだこと**は保証しない。
  `tools/dev_wave_wait.py acceptance` は `--` 以降に任意の child command を受け取り invocation
  receipt を発行しないため、文書に canonical literal を置いたまま実行時に手書き待ち手を呼ぶ wave を
  機械的に検出できない。段 3 の 2 レンズが独立に指摘した。択 = (a) 待ち手に invocation receipt
  (stage・wave・argv・script digest の束縛) を発行させ段 7 の記録検査で照合する / (b) docs 層で
  留め実害の再発を待つ。成果物影響 = (b) なら F32 族 (自己マッチ死、独立 2 例、実測 20 時間 23 分
  + 7 時間 36 分) の再発経路が runtime 側に残る。親の推奨は (a) を別 wave で起票。

- {{T:control-byte-scan-tool}} **P3・新規**: [T-788] の制御 byte 混入を docs の義務ではなく
  artifact 生成側の機械検査で閉じる。混入すると grep が binary 扱いして検索から落ちるため
  収集系にも影響する。docs 予算を 1 bytes も使わずに閉じられる。
