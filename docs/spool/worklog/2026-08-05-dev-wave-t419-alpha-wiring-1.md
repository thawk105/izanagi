---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-05
wave: dev-wave-t419-alpha-wiring
seq: 1
title: 方式 α を本番 attestation の取得経路へ結線した — 較正再取得の着手条件 1 件目が成立し、裁定パッケージ 5 件を返す (コード + docs、branch worktree-dev-wave-t419-alpha-wiring)
---

## 本文

- **段 1 の前提実測で「既存被覆はこの変更を検出しない」ことが分かった。** 取得方式を表す
  `method` 文字列だけを 1 行変異しても、clock / freeze 系 6 test file の 330 件が 1 件も落ちなかった。
  よって検出力は純増分にしか帰属せず、既存テストに寄りかかれない。変異は即時復元した。
  併せて login node で α を実演し (単読みでは 4 CPU が帯外、走行 CPU を 5 点へ移した CPU ごと最小では
  1 CPU)、機構が効きかつ恒真にならないことと、affinity の変更・復元が可能なことを確かめた。
  **この実演は機構の存在を示すだけで、本番手続きの妥当性根拠にはしない** ({{D:alpha-acquisition-identity}})。
- **親の provisional 裁定 1 件を段 3 の敵対レンズが撤回させた。** 親は pin が効いたことの検査に
  `/proc/self/stat` を使うと書いたが、affinity は呼び出し thread に効くのに同 stat は
  thread-group leader のものであり、pin した thread を見ていない。{{F:self-stat-not-thread-stat}} に
  記録し、`/proc/thread-self/stat` へ是正した。
- **段 3 の敵対レンズが「実測済みの α と本番案は別プロトコル」と指摘し、親は real と裁定した。**
  9/9 の should-pass を得た実験の α 群は時間幅が広く、本番の連続 5 読みは約 100 ms に集中する。
  機序の除去は時間窓に依存しないが一過性の吸収は依存するため、宣言した最小 interval を identity へ
  載せ、**9/9 を本番手続きの妥当性根拠には使わない**と決めた。
- **段 6 のレビュー 2 本とも NO-GO を返し、うち 1 件は誤受理経路だった。** pin mask の exact 検査が
  interval 待機の前にあり、待機中に affinity を広げられても pre/post の瞬間だけ target 上にいれば
  通った。検査を待機の直後へ移した ({{F:pin-check-gap-during-wait}})。復元例外が pin/read の本来の
  失敗理由を上書きしていた点も是正した。
- **偽 kill 3 件を harness 走行前に潰した (F113 の同型再発)。** CPU 集合 drift の負例が別例外で
  赤くなっていた件、reader 外れ値 fixture が実際の pin と結び付いていなかった件、静穏正例が
  完全一致で過剰拒否変異を検出できなかった件。いずれもレビューのレンズに「その負例が赤くなる理由は
  1 つか」を入れていたために走らせる前に見つかった。
- **schema を広げないことを、証拠上の損失として明記して決めた。** K 回取得したことの事後証拠は
  成果物に残らず、`method` は手続きの証明ではない。必須 key を足せば旧 probe corpus と登録済み較正が
  method 比較へ届く前に落ち、observed 側だけに足しても較正発行経路が observed を expected へ
  転用するため exact 検査に当たる。取得 transcript の凍結は別 wave として裁定へ返す。
- **変異は事前登録 14 件 (負例 13・過剰拒否を検出する正例 1) で、初回走行で 14/14 kill・期待 node
  完全一致・SURVIVED 0。** 単一理由性のため pre / post 検査と CPU 集合 / identity 検査を別変異に分け、
  K 退化は「最初の snapshot を再利用する」形へ、K 未満の切り下げは selector と reducer を同時に
  緩める三層変異へ再照準した。受入全走は local main 74b15367 を取り込んだ tip で 6482 passed / 20 skipped。
- **段 8 の自己改善は候補 2 件で、規則の追加はしなかった。** 1 件目は「非 ASCII を含む
  parametrize の期待 node は pytest が escape した形で書く」で、既存契約の「期待 node と記録 node は
  突き合わせ前に同じ形式へ正規化する」でそのまま処理できた (収集出力から取って登録し、初回一致)。
  2 件目は「worktree 隔離セッションでは redirect 付き複合コマンドが guard に拒まれるので起動 script を
  書く」で、本 wave でも 4 回発火した。置き場である条件節の byte 予算が塞がっている状況は前 2 wave と
  変わらないため、予算を上げず安全義務も削らず、**3 回目の発火実績として記録するに留める**。
- 逐語と変異台帳は `output/insights/2026-08-05_t419-alpha-wiring/`。

## 次の一手差分

### 完了

- [T-528] 方式 α を本番 attestation の取得経路へ結線した。走行 CPU を決定的に 5 点へ移しながら
  読み、論理 CPU ごとの最小値を採る。方式 identity は K・最小 interval・選択規則から組み立てる。
  受理述語・凍結 bytes・pin は変えていない。
  remaining: none
  base: 61221bd5a00f636bd1777c7f189031cee9ebb3a86e9dc6d626ad2ec51fab0972

### 更新

- [T-419] **P1・着手条件 (i) 成立 → 残るは (ii)(iii)(iv)**: 方式 α の本番結線は完了
  ({{D:alpha-acquisition-identity}})。残る着手条件は (ii) 正規 CLI の accepted publish receipt、
  (iii) 独立な self-comparison、(iv) 既知の自己不整合較正の例外集合が空になること。
  結線により live probe と登録済み較正は `effective_clock.method` で必ず不一致になるため、
  取得が成功すれば method を含む比較 failure、失敗すれば probe 失敗として拒否される。
  受理集合は閉鎖のまま変わらない。凍結 bytes・pin の更新は再取得と同じ wave が持つ。
  一次資料 = `output/insights/2026-08-05_t419-alpha-wiring/README.md`
  base: 3e1e9dd8559ff67b623436273e086952f2deb0b74554e38f77b1aaf97bd12690

### 新規

- {{T:alpha-production-protocol-validation}} **P1・新規・ユーザー裁定待ち**: 本番の α 取得手続きを
  計算ノードで検証する。因果実験が 9/9 の should-pass を得たのは randomized pin sweep 由来の
  時間幅が広い群であり、本番は宣言した 50 ms 間隔の 5 読みである。機序の除去は移るが一過性の吸収は
  移らない。静穏ノードで本番手続きが過剰拒否しないことを実測するか、実測せず運用に入るかを裁定したい
- {{T:acquisition-transcript-schema}} **P2・新規・ユーザー裁定待ち**: 取得手続きの事後証拠
  (K 個の snapshot、pin target、読みの前後の走行 CPU、時刻) を versioned schema へ凍結する。
  現状 method は手続きの identity であって証明ではなく、単読みを K 回複製した実装でも成果物からは
  区別できない。旧 probe corpus・較正 loader・profile hash・登録 artifact・contract pin を同時に
  動かすため、独立した wave と裁定を要する
- {{T:oracle-reservation-probe-allowance}} **P2・新規・ユーザー裁定待ち**: oracle の予約式に
  attestation probe の所要時間が入っていない。α で 1 probe あたり最低 0.2 秒かかるようになったが、
  予約式は行ごとの試行上限と finalization しか数えず安全余裕が 0 である。行数 N なら最低
  (N+1)×0.2 秒が未計上で、上限近くで recheck が失敗しうる。probe allowance の新設か予約式の改訂が要る
- {{T:t126-attestation-type-mismatch}} **P2・新規・ユーザー裁定待ち**: 資格判定 driver の
  attestation 比較が 2 層で型不整合を起こしており、成功経路へ到達できない。比較に較正オブジェクトを
  渡している既知の層に加え、それを直しても profile hash 計算が observed 型を受理しない層が残る。
  既知の fail-closed だが 2 層目は今回新たに確認したもので、資格試行台帳に観測 profile が
  1 件も載らない状態が続く
- {{T:probe-warmup-carryover}} **P2・新規・ユーザー裁定待ち**: α の巡回が後続測定へ残す暖機の
  持ち越しを評価する。affinity を復元しても走行 CPU・cache・P-state は戻らず、oracle は行ごと、
  較正 CLI は測定の前後に probe する。affinity 変更を短命な helper process へ隔離する案は
  attest する主体が変わる意味変更を伴うため本 wave では採らなかった。ablation の要否を裁定したい
