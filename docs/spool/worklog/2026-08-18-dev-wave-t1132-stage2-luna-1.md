---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-18
wave: dev-wave-t1132-stage2-luna
seq: 1
title: dev-wave の codex を全段 luna@max へ切り替えた — 費用の運用選好としてユーザーが裁定し、token は増え単価が 1/25 になる (コード + docs、branch worktree-dev-wave-t1132-stage2-luna、変異 matrix = baseline PASSED・7/7 KILLED・SURVIVED 0・MISMATCH 0)
---

## 本文

- **ユーザー裁定の経緯 — scope が 3 度変わった。** 初回の指示は「gpt5.6sol を使っているところを
  一箇所 luna max に置き換えろ。claude よりも codex のトークン消費が激しすぎる」だった。
  親が段別消費を実測して「一箇所 (段 2) では 15.3% で目標に届かない」と報告し、
  次にユーザーが残量 (codex 80% / claude 123%、元は各 200% = 必要な削減 35.8%) を提示。
  さらに「luna はレートが遥かに安い」「luna は愚かだから luna を使う段は max でなければ
  受け入れない」という 2 つの事実と条件が加わり、最終的に
  **「sol を luna max に全部置き換えてもいいよ」**で確定した。
  親は事前に「C 案は段 3 レンズ 1・段 6 敵対レビュー・段 6 焦点再レビューの 3 つの敵対 gate を
  すべて luna にする案で、レンズの多様性が失われる (D241 の論点)」と明示して提示している。
- **この採用は品質同等性の証拠に基づかない。** [T-1146] の現行裁定 (c) が
  「体感や速度を理由に切り替えたくなった場合は、証拠に基づく判断ではなく**運用上の選好**として
  (b) を明示指示し、その旨を記録する道を残す」と定めており、本 wave はその道を通った。
  D423 が「supersede はユーザー裁定にだけ属する」とした権限をユーザー自身が行使した形である。
  詳細は {{D:dev-wave-all-luna-max}}。
- **親の誤り (F29 の再発)。** 親は費用の問いに対し receipt 170 本の **token 数だけ**を集計し、
  「luna は安くない、全段 max へ広げると +46.5% 悪化」と報告した。単価を一度も見ていなかった。
  実際には luna のレートは sol の 4% で、結論の向きが逆だった。ユーザーの
  「遥かにモデル料金レートが安い。それはわかってる?」で是正。failures へ再発として記録した。
- **棄却した所見。** レビュー A-02 (v2 は単一 model なので「全段同一」assert が恒真になる) は real だが
  nit と裁定 — v1 経路の回帰テストが段別 mapping を実際に検査しており、判別力はそちらにある。
  レビュー B が提案した「実装側で `high` を拒否する」も不採用 — 段 5 の effort は T-667 が
  pin 拡大を明示的に見送った意図的な unbound であり、拒否は見送り裁定の反転になる。
- **敵対レビュー 2 本が両方見落とした欠陥を、親の焦点走の範囲拡大が拾った。**
  権威行の model slug を「2 個ある前提」で入れ替える consumer が
  `test_codex_worker_launch.py` に 1 件あり、v2 (slug 1 個) で `IndexError` になっていた。
  レンズ B は同 file の consumer を列挙していたがこの 1 件は挙げていない。
  親の最初の焦点走もこの file を含めておらず、5 file へ広げて初めて出た。
- **変異 matrix は probe → 本走の 2 段で回した。** 初回 probe は期待 node 2 件が
  parametrize された実 node ID と一致せず preflight で fail-closed。`--collect-only` で
  権威一覧を取って修正した。2 回目の probe で baseline PASSED・4 KILLED・3 MISMATCH。
  MISMATCH の 2 件は期待集合が広すぎたためで、実測値を完全集合として再登録した
  (差の原因は**恒久保留テストが走らないこと** — `test_real_repo_clean` 等が growth-hold で
  `opted_in:false`)。残る 1 件 (段 6 effort pin の**値**を戻す変異) は **265 node が赤になる過剰決定**で、
  `DW-M03` に従い単独変異の証拠から外した。同じ性質は pin literal の変異 (実測 7 node、
  production path 検査を含む) が単一理由で押さえている。
- **セッション異常: 背景タスクの完了通知が実体より先に 3 連続で誤発火した。** 子も待ち手も
  生きているのに「completed exit 0」が届き、成果物も `.done` も存在しなかった。
  `DW-O01` の「完了は `.done` と exit code だけで判定し、通知を判定にしない」に救われた。
  最初の 1 回は親が pid file 作成前に待ち手を張った既知の型だが、残り 2 回は
  pid file 実在を確認してから張っており別要因である。
- **エージェント工数**: codex 子 6 本 (段 5 実装 1・段 6 敵対レビュー 2・fix 2・焦点再レビュー 1)。
  すべて `check_codex_output.py` rc=0。段 5 実装子だけが変更前の `gpt-5.6-sol` @ `high` で走り、
  段 6 以降はすべて新権威の `gpt-5.6-luna` @ `max` で走った。
- **変更が効いていることを受領証で実測した。** 段 6 敵対レビュー 2 本の receipt が
  `recorded_model=gpt-5.6-luna` / `recorded_effort=max`。token は過去平均の 1.89 倍で、
  D207 が観測した `high`→`max` の 2.02 倍とよく一致する。
  同一 token 量なら luna は sol の 4.0%、effort 増を織り込むと旧構成比 7.6%。

## 次の一手差分

### 完了

- [T-1146] 段 2 / 段 5 の codex model について、裁定 (c) が残した「運用上の選好として (b) を
  明示指示する」道をユーザーが通り、全段 luna@max として実装・land した。
  remaining: none
  base: 0eec6a3539a61220995000aa6932f7df63a73cd9b5e1f8556a841ebbb8597647

### 新規

- {{T:lens-diversity-after-single-model}} **P2・新規**: dev-wave の全段が同一 model になり、
  段 3 敵対相談 2 レンズと段 6 敵対レビュー 2 本の多様性が prompt だけになった。
  model 由来の系統的盲点が共通化する。prompt 以外の軸 (レンズ設計・入力射影・独立性の取り方) で
  多様性を回復するか、回復しないと裁定するかを決める。
- {{T:focus-run-covers-consumers}} **P2・新規・段 8 から**: 焦点走の集合を
  「変更した test file」から「**変更した production file を import・実行する consumer test**」まで
  広げる義務を `DW-O18` へ入れる。本 wave で実測した穴 (F242 再発) だが、`DW-O18` は L2 単節予算
  1000 bytes に対し現行 995 bytes で余裕 5 bytes、必要 124 bytes。既存の安全義務を削って空けるのは
  自己改善契約が禁じているため、**予算をどう作るか**の裁定が要る。
- {{T:stage5-effort-machine-binding}} **P2・新規**: 段 5 author と段 6 fix の `reasoning` は
  `effort_authority=unbound` で caller 指定のままであり、docs 契約と dispatcher test の記録だけが
  caller を縛る。本 wave は実際にこの鎖の切れ目を踏んだ (docs を `max` にしても runner script が
  `high` を渡し続けていた)。機械強制を入れるかは T-667 が pin 拡大を明示的に見送った判断の
  再訪にあたるため裁定へ返す。
