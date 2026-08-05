---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-05
wave: dev-wave-t244-p4-batch-freeze
seq: 1
title: [T-244] P4 batch freeze を ledger 側契約として実装した — W2/W3 を適合させ W4 は terminal 統一まで強め、P4 充足は名乗らない (コード + docs、branch worktree-dev-wave-t244-p4-batch-freeze)
---

## 本文

- **依頼は「P4 実装 — W2/W3 の適合 + P4 充足判定まで」。** D153 の W1〜W5 はユーザーが
  2026-08-04 の /rulings で全件採用済みで、archive (186) が「P4 実装 wave を起票できる」と
  記録していた。段 1 の前提実測で **W2 と W3 はいずれも非適合**と確定し (candidate 平文の distinct
  強制が replicate を排除、evidence digest 束縛が batch 結果に存在しない)、実装へ進んだ。
- **段 3 の敵対 2 レンズ・段 6 の敵対レビュー 2 本とも独立に NO-GO。** 所見は段 3 が 14 件、
  段 6 が 10 件で、**refuted は段 6 のうち 1 件の一部だけ** (W3 に referent 解決まで読み込む拡大解釈)。
  残りは全件 real と裁定し、Δ1〜Δ14 と F1〜F8 で閉じた。焦点再レビューは
  **closed 9 / partial 1 / regressed 0** を独立確認し、新設検査に恒真はなく、境界数値も独立再計算で一致した。
- **親の実測が段 2 プランを訂正した点 (brief-erratum)。** brief に書いた「outcome は自由文字列で
  素通し」は誤りで、codec 層が二値に閉じており commit 経路は必ずそこを通る。fail-open は private
  reducer の直接呼び出しだけだった。また brief の「W2 非適合を放置すると certifiable 集合が広くなる」も
  **方向が逆**で、過少計数は seal を難しくする (狭める)。実際に広がるのは ordinal 導入後の水増し経路である。
  設計材料 (`output/insights/2026-08-04_t244-p4-batch-freeze/`) と設計本文 §4③ を brief の入力に
  挙げていなかったのも漏れで、段 4 で読んで W4 の規範定義を裁定根拠に加えた。
- **W4 は裁定文より強い読みを採った。** 設計本文 §4③-5 の目的 (早期停止の有無を公開面から消す) に
  照らすと、全 tombstone だけ 2 event で終わる形は terminal 種別と event 数で早期停止を漏らす。
  全経路を 3 event に統一し、専用 tombstone event 型を削除した。**byte 長の同一化は保証しない**ことを
  明示的な受容残余として記録した。
- **P4 は充足しない。** 名乗りは「W1〜W5 の ledger 側契約に適合する P4 batch-freeze prototype」まで。
  会計は U-G と同型で残余 6 点。並行 wave が独立に実測した「現行 production caller はどれも
  合法 batch (cardinality>=2) を作れない」が、発火 path 不在の一次証拠である。設計判断は
  {{D:p4-batch-freeze-ledger-conformance}}。
- **scope 外の real 所見 3 件のうち 2 件を起票**した ({{T:reflux-query-receipt-binding}}、
  {{T:reflux-evidence-resolver-contract}})。3 件目 (並行 producer wave との landing closure) は、
  当の wave が実装を止めて docs のみ land したため消滅した。
- **手順違反 1 件 (自己申告)**: 変異走行中に spool fragment を作って untracked file を増やし、
  harness の preflight を rc=2 で止めた。(194) と同型の「走行中に worktree を触る」違反である。
  fragment を commit してから再走し、実害は再走の一手間だけだった。
- 子の工数: 段 2 が約 20 分、段 3 の 2 本が並列で約 15 分、段 5 実装が約 25 分、段 6 レビュー 2 本と
  fix と焦点再レビューと spec 作成でそれぞれ 10〜25 分 (いずれも codex `gpt-5.6-sol`、
  段 2/3/6 レビューは effort=max、実装系は high)。セッション異常なし。
- **受入 (2026-08-05、worktree `dev-wave-t244-p4-batch-freeze`、統合 commit `61fc520`、
  すべて計算ノード dispatch):** 対象 3 file の部分走は fix 前 **35 passed / rc=0** (request 889289)、
  fix 後 **39 passed / rc=0** (request 889422)。local main (`4b55888`) を merge commit `762a591` で
  取り込んだ後の**全走は 6073 passed / 19 skipped / 0 failed (rc=0)** (request 889498、564.19s)。
  `python3 tools/check_docs.py` = 違反なし。`check_ai_provenance.py` は統合 commit 後 rc=0 (request 889446)。
- **変異 matrix (B-057、`tools/mutation_harness.py` dispatch mode、統合 commit 後に本走):**
  **27/27 完走、KILLED 26 + MISMATCH 1、SURVIVED 0、TIMEOUT 0。** spec sha256 =
  `6bbcc67661ac11cf88a72dd5d4aa2b7bd7832cd2a869950edb0d2095db1dec54`、anchor = `61fc520`。
  MISMATCH は M-13 (evidence tamper) で、**期待 node は赤くなったうえで共有 fixture 経由の V16 も
  赤くなった上位集合**である。過剰検出であり検出漏れではないので再走せず実測のまま記録する。
  内訳は KILLED 対象 24 件 + **diagnostic sensitivity pin 3 件** (M-9″ / M-16′ / M-22)。pin は
  焦点再レビューが「単一理由性が立たない」と実測した変異で、**KILLED に数えない**扱いへ親が降格した。
  恒真 residual 4 件 (実 query 一対一・seal 前の外部漏洩・referent 実在・provider pin) も事前に明記した。

## 次の一手差分

### 更新

- [T-244] **P1・P2 は実装差し戻しでユーザー裁定 5 件待ち。P3 は (4)(5) 裁定済み + (1)(2)(3) 設計起草待ち。P4 は ledger 側契約に適合 (充足は未達)。P5 残余は U-2。未着手は P7・P9 の 2 件**:
  **P4**: D153 の W1〜W5 を **ledger 側で実装完了** ({{D:p4-batch-freeze-ledger-conformance}})。
  member identity を `(wire, origin-wide query ordinal, origin-wide replicate ordinal)` の正準
  preimage へ束縛し、replicate は seal 前に公開しない。outcome と evidence digest claim を単一
  commitment へ束縛し三値 matrix を codec/reducer 二層で閉じた。terminal を 3 event に統一し
  tombstone event 型を削除、member row 数を cardinality に固定した。salt を exactly 32 hex にし、
  authority feasibility に partition 存在検査・origin 横断 head 合算・十進桁を含む byte 上界を入れた。
  schema は v2 へ分離。**P4 充足は名乗らない** — 残余は producer 結線・driver 結線・実 authority 登録・
  seal 前漏洩を防ぐ storage 契約・formal consumer・proof chain 結線の 6 点で、U-G と同型の会計である。
  production caller ゼロ・authority registry 空は不変で受理集合の現在値も不変。
  本 wave の schema v2 分離は空 registry の版名変更であり、実在 authority の世代移行の主体・契約は
  決めていない (P3 の裁定パッケージ (2) の所有面)。逐語は
  `output/insights/2026-08-05_t244-p4-batch-freeze/`。
  **P3・P2・P1・P5・未着手の状況は (201) から変わらない** — P3 は producer 結線が D163 で実装不能と
  確定し裁定パッケージ (1)(2)(3) が設計 wave 待ち、P2 は D164 で設計メモ凍結、P1 は機械部品のみ、
  P5 は U-1 実装済みで残余 U-2、未着手は P7・P9 の 2 件。cap-lift は FAIL、D114 の上限 1 も不変。
  base: 953863ef4d2867b49c713fadf056e0544175281600c316be1f1557787f48c570

### 新規

- {{T:reflux-query-receipt-binding}} **P2・新規**: origin ledger の member row を物理 query へ束縛する。
  現状 ledger は実 query を観測せず、同一 wire・同一 evidence を正しく番号付ければ counter が増える。
  producer/driver が member ごとに 1 実 query を実行したことの receipt を要求する設計は W1 と P7 の面。
  敵対レビューが実測した水増し経路 (`output/insights/2026-08-05_t244-p4-batch-freeze/s3-lensA.md` A-1) が出所。
- {{T:reflux-evidence-resolver-contract}} **P2・新規**: evidence digest の resolver 契約を決める。
  ledger は digest claim を commitment へ束縛するだけで referent を解決しない (W5 の分界どおり)。
  authority-backed evidence receipt にするか content-addressed resolver にするかは未裁定で、
  formal consumer はこれが無いと evidence bytes を取得できない (同 s3-lensA.md A-2 / s3-lensB.md B-4)。
