---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-06
wave: dev-wave-t532-name-mask-binding
seq: 1
title: [T-532] known 軸凍結の trigger record へ name↔mask 束縛一致検査を入れた — 現在値を変えない dormant gate だと実測し、裁定パッケージ 2 件を返す (コード + docs、branch worktree-dev-wave-t532-name-mask-binding)
---

## 本文

- **親 brief の成果物影響の記述が誤っており、段 3 の敵対レンズが是正した。** 親は
  「`name` が certified 選択・材料レポート・試行台帳へ流れる」と書いたが、試行台帳が記録するのは
  `configuration_id` であり、judge の出力は `winner_configuration_id` で、`name` 欄は存在しない。
  さらに現 checkout に certified 選択の consumer が無い (worklog (231) [T-470] に既記録)。
  正しい影響は「D50 が選んだ `system_gate` の意図と実際に materialize される述語が乖離し、
  binary・`src_token`・`variant_id`・throughput と `entry_sha256` / `binding_entry_sha256` が変わる」。
  親は誤りを認めて DW-G05 を書き直した。
- **本検査は現行 official の受理集合を一件も狭めない dormant gate である。** official の受理集合は
  空のままなので、現時点で「誤 certification 経路を閉じた」とは書かない。実効化は [T-478] / [T-531] の
  世代移行で新世代 artifact を発行する時点である。段 3 のレンズ B が親の (P3)
  「生成層 + schema 層の 2 点で本番到達に十分」を「呼出し可能性から将来の防御へ一般化し過ぎ」と否定し、
  親はこれを採用して記述を限定した。
- **既存被覆の棚卸しも段 3 が是正した。** 親は「production の同性質検査は extime 較正の read-heavy
  1 record だけ」と書いたが、test 層に `test_reflux_ir` の
  `test_frozen_gate_predicates_match_six_records_with_three_distinct_masks` があり、
  `{"g_rt": 4, "g_rl": 8, "ident_all": 31}` を手書き固定して現行 6 record を既に照合していた。
  これは新しい名が現れれば手で更新するまで機能しない test 専用 golden なので、純増は
  **production gate の新設**である。二重化ではなく独立 oracle として残した。
- **段 1 の前提実測を 4 件行い、うち 1 件は結論の射程を自分で狭めた。** generator へ probe 1 行を
  入れて freeze 系 8 test file を実走し 238 passed / 1 skipped で赤ゼロだったが (即時復元)、
  段 3 のレンズ A が「この 8 file から generator を自由に編集してよいとは一般化できない」と指摘した。
  親は結論を「この 8 file の範囲では追加の赤が出ない」に限定し、legacy `verify_document` の
  generator sha 照合面が緑だとは主張しないと明記した。[T-492] 当時の赤 1 本は同 wave の是正で
  解消済みであることも実測で確認した。
- **段 6 のレビュー 2 本と焦点再レビューが must-fix を 3 件出し、いずれも実装側の欠陥だった。**
  (a) 無効名の負例を単一 test node 内で順に走査していたため、型検査を消す変異が走査順の手前の
  `str` subclass で赤くなり、事前登録した比較偽装の kill を証明していなかった ({{F:scan-order-false-kill}})。
  (b) name→mask index の構築が module 読み込み時に走り、失敗すると consumer の構造化拒否境界と
  pytest collection を壊した。初回検査呼出しへ遅延し、成功時だけキャッシュする形に直した。
  (c) 非 str 拒否の診断が f-string で `repr` を先に実行するため、`__repr__` が例外を送出する object では
  `FreezeError` にならなかった。受理集合を変えない診断経路だけの修正であり DW-G05 の基準では
  nit だが、新規コードの契約違反なので直した。
- **変異は事前登録 7 件 (負例 5・過剰拒否を検出する正例 2) で、最終版は 7/7 kill・node 完全一致。**
  初回走行で M5 が MISMATCH になったのは**親の登録ミス**である。「`ident_all` の別名登録を削除する」
  変異として登録したのに、置換後の文字列に登録行を残したため、実際には「別名の衝突検査だけを削除する」
  変異になっていた。検査側の欠陥ではない。初回台帳は消さず erratum として insight に残した。
- **変異走行は選択式で範囲を絞っている。** runner は 2 test file に `-k` 選択式を付けたもので、
  suite 全体ではない。登録した性質に対応する node をすべて含む選択であることを確認したうえで、
  絞っている事実を台帳と本記録の双方に残す。
- **scope 外の real 所見 2 件を裁定パッケージとして返す。** いずれも本 wave の裁定
  (対象を name↔mask 束縛に限定する) の外側にあり、実装していない。
  逐語と根拠は `output/insights/2026-08-06_t532-name-mask-binding/`。
- 受入全走は fix 前 6475 passed / 20 skipped、fix 後 6476 passed / 20 skipped、
  land 直前の再走は本エントリの後段に記す。いずれも Pegasus 計算ノードで実測した。

## 次の一手差分

### 完了

- [T-532] 凍結文書の trigger record へ name↔mask 束縛一致検査を生成層と schema 層の双方へ入れ、
  期待名の権威を emitter の正引きに置いた ({{D:trigger-name-mask-forward-authority}})。現行凍結物は
  再発行していない。official 受理集合が空のため現在値は変わらず、実効化は [T-531] の世代移行時。
  remaining: none
  base: 96fdae7914b2ceebe5efe50b99748d4f4606d079d637f513f28b535e7ed01f16

### 新規

- {{T:s1b-pairing-mask-identity}} **P2・新規・ユーザー裁定待ち**: `assert_s1b_pairing` は
  gate と ident_all の述語を**生文字列**で比較するため、両 record を mask 31 の名にし、
  一方の述語にだけ外側空白を付けると「gate と ident は別物」という要求を迂回できる。期待表は
  文書自身から構築されるので自己無矛盾になり、S-1B の gate on/off 対比が同一構成同士の比較に
  なりうる。閉じるには比較を復元 mask 同士に変える必要があり、その consumer
  (`t080` の pairing 検証、measurement freeze の pairing 複製) へ波及する。穴は本 wave 以前から
  存在し本 wave が作ったものではないため実装しなかった
- {{T:holdout-name-mask-bypass}} **P2・新規・ユーザー裁定待ち → [T-531] の受入条件へ**: holdout 凍結は
  known 文書を直接読んで entry を複製し、検証も複製との equality だけなので、name↔mask 束縛を迂回する。
  ratified と report も source / entry hash しか見ない。非正準 producer 由来の known 文書を与えると
  `variant_binding` の name と述語が食い違ったまま selector basis hash・`binding_entry_sha256`・
  manifest の `entry_sha256`・pilot 実測値がその文書へ束縛される。[T-533] と同一面で
  [T-531] へ同梱すると裁定済みのため、同統合の受入条件へ「canonical membership だけでなく
  name↔mask 束縛も holdout / ratified 境界で必須」と明記することを推奨する
