---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-01
wave: dev-wave-t2060-current-closure-unknown
seq: 3
title: [T-2060] D1245 の歴史閲覧と現行認証の分離を実体化し、現行適合を unknown と表示する (code + tests + insight、branch worktree-dev-wave-t2060-current-closure-unknown)
---

## 本文

- **依頼文の前提が 1 つ実測と食い違った。** 「`current-closure-unavailable` を歴史閲覧の拒否理由に
  しない」は**中央 gate では既に成立していた** — 歴史 purpose は現行閉包を一切読まない。
  純増は (1) その構造を機構として固定すること と (2) 現行適合 unknown の明示表示である。
  D1245 の残り半分 (表示) はどこにも実体が無かった。
- **親の実測 2 件が過大一般化で、段 3 のレンズ A に訂正された。** (a)「現行閉包の可用性 =
  24 path が HEAD と一致」は誤りで、root 解決・Git 実行・race・timeout の失敗も同じ理由コードへ
  畳まれる。(b)「編集中は certified 経路のテストが一律赤」も誤りで、隔離 fixture を使うテストは
  未 commit 編集中でも緑になる。後者は期待赤の一括分類を禁じる根拠として実装子・fix 子へ渡した。
- **段 3 のレンズ B は「本 wave の scope では D1245 は満たされない」と判定した。** 過去の測定を
  実際に読む `replay.load_landscape` と S-1 の epoch gate が `CERTIFIED_ACCEPTANCE` を宣言して
  いるため、現行閉包が読めないと過去の測定が返らない。**親はこれを real と認めた上で実装しない
  と裁定した** — どの消費者がどちらの purpose を宣言するかは certified 成果物の受理集合を変える
  設計判断であり、ユーザーが「現行認証に必要な意味互換性は fail-closed のまま維持。ここを緩めるのは
  裁定の内容ではない」と明示しているため、親の一存では行わない。判断は {{D:purpose-declaration-is-per-consumer}}。
- **親が段 6 で、どちらのレビューも指摘していない実害を 1 件見つけた。** 自律試行の完全性検査は
  保存済み Layer 3 report と再構築を byte 比較しており、新 field のせいで**同 field を持たない
  保存済み report が必ず食い違う**。`output/campaigns/` の保存済み 7 件はいずれも同 field を持たない。
  **本 wave が防ごうとしている絶対規律 7 の違反そのものを実装が作り込んでいた。**
  さらにこの型は**テスト内で report を作れば両側に field が付いて緑になる**ため、テスト色では
  見えない。既存の legacy omission 正規化と同型の flag を 1 つ増やして閉じた。
  型と再発検知は {{F:new-report-field-invalidates-saved-artifacts}}。
- **実測。** 焦点走 18 file で 2073 passed / 18 skipped (計算ノード、181 秒)。
  変異は事前登録 8 件が **8/8 KILLED、期待 node は完全一致**、baseline 緑。
  ただし **kill として数えるのは境界変異 5 件** (M1/M2/M3/C1/C2) で、表示値の 2 件は
  診断感度 pin、certified 昇格の除去は liveness として別枠に置いた。
  **表示値の変異は 115 node に波及して過剰決定**であり、単独変異の証拠から外している。
  段 6 の node 分割は実測で効き、schema 禁止の変異は 1 node、除去の変異は別の 4 node に分離した。
- **新規 6 node のうち 3 つは旧実装でも通る。** 構造回帰・dirty certified 負例・certified schema
  node は D1245 実装の存在証明ではなく回帰 pin である。存在を証明するのは表示・投影・保存済み
  互換の 3 node と、変異 D1/D2/C1/C2 である。段 3 のレンズ A の指摘をそのまま記録する。
- **段 3 の A-03 (certified view token の偽造可能性) は D1252 が既裁定**で新事実ではないため
  再提起しない。**A-02 (COMMIT 0 件の campaign へ certified view が出る)** は今回の差分が導入した
  ものではなく、受理集合を縮小する変更が広範囲に及ぶため別 T とした。
- 実装子の完了報告にある「既存テストを一つも変更していない」は**不正確**である。追加のみだが、
  既存テスト 1 件の本文に行が 1 つ加わっている (手作りの certifying report から producer が
  出さない field を外すための fixture 調整)。期待値・assert・raises は不変。
- **受入全走が、本 wave と無関係な環境失効で赤になった。** 赤は全件
  `test_codex_reasoning_ab.py` で、本文はホーム配下の実 session rollout の不在。
  `.codex/sessions/2026/07` が失われ、参照している 5 session は
  `/home/SFC/tanab` と `/work/1/SFC/tanab` の全域検索で **0 件**。復元不能である。
  **期限切れ以降に受入を投げるすべての wave が同じ赤を受け取る。** 型は
  {{F:acceptance-depends-on-expiring-home-sessions}}。
- **ユーザー指示「codex と相談して決めて」に従い、相談 2 本を独立レンズで走らせた。**
  **両者とも repo 内 fixture への移設 (案 4) を推奨したが、親はこれを採らなかった** —
  両相談とも「移す元が残っているか」を確かめておらず、実測すると元 bytes は存在しない。
  期待値から逆算して fixture を作る道は、独立 2 経路の一致という当の性質を自作自演にする。
  **両相談の枠組みも 1 点訂正した** — 両者は skip を「coverage を失う」と評価したが、
  その coverage は既に失われており、緑にできない赤は coverage ではない。
  採った案と却下理由は {{D:expired-external-evidence-skips-only-on-absence}}。
- **blocker 修正の段 6 で、fail-closed の負例が形だけだったことを実測で見つけた。**
  負例が skip する側のラッパーを呼んでいたため、「重複も破損も skip に倒す」変異で
  node が失敗ではなく **skip** になり、変異が生存していた。下位 resolver へ向け直し、
  skip 経路自体の正例も別 node で持たせた。**再走で B2 / B3 がそれぞれ 1 node だけで KILLED**
  になり、単一理由性も成立した。
- **変異走行の射程を正直に狭めた。** 変異用の使い捨て worktree は入れ子 submodule を
  初期化できず、合成 fixture の baseline が緑にならない (`mutation_worktree.py` の
  `submodule update --init` は再帰的でない)。よって blocker の変異走行は
  **preflight 機構の検出器だけ**を対象にし、合成 fixture へ移した 22 node の検出力は
  この走行の観測範囲の外である。**受入全走で実走して確かめた。**
- **親が JST 時刻を実測せずに報告し続けた。** wave を通して一度も `date` を打たず、最初の推定値へ
  経過を足していた。ユーザーの別件の指摘で実測して発覚し、F1 の再発として記録した。
- **親の手順違反をもう 1 件記録する。** blocker 修正の変異事前登録を、fix 子の投入**後**に書いた
  (差分の閲覧前には凍結した)。DW-M01 は実装前を要求しており、投入前に書くべきだった。
- **親の自己訂正 2 件。** (1)「ディレクトリの mtime は 7 月分の削除時刻である」は言い過ぎで、
  言えるのは「その時刻に直下が変更され、現在 07 は存在しない」まで。
  (2)「test 側の照合再実装と production 側に食い違いは無い」は**不完全**で、照合述語は等価だが
  **周囲の候補選択が production の pinned-label 経路と食い違う**。述語だけを比べて結論した。

## 次の一手差分

### 完了

- [T-2060] D1245 の purpose 分離を機構として固定し、歴史側へ現行適合 unknown の表示を足した。
  消費者の purpose 再分類は {{D:purpose-declaration-is-per-consumer}} で別裁定とした。
  remaining: none
  base: a8ea464f42168e9f437826b5c9efdafebdf243d799b51476ef045cb8ac0b66c8

### 新規

- {{T:historical-consumer-purpose-reclassification}} **P1・ユーザー裁定待ち**: 過去の測定を読む
  消費者 (`replay.load_landscape`、S-1 の epoch gate、oracle の epoch 証拠) を歴史 purpose へ
  移すかを裁定する。S-1 は可用性 gate と保存済み COMMIT 証拠検査が別関数のため安全に分離できるが、
  素朴な付け替えでは `E0 / v1-authority-absent` の拒否まで落ちる。replay は exact 型と証拠
  capability に束縛され、緩めると規律 2 に触れる。
- {{T:historical-view-current-policy-dependency}} **P2・新規**: 歴史閲覧が前段で現行 policy と
  照合され、policy の版が上がると過去の v2 campaign が purpose を問わず読めなくなる。
  `current-closure-unavailable` とは別の識別子だが絶対規律 7 の同じ趣旨に触れる。
- {{T:expired-rollout-coverage-restoration}} **P2・新規**: 失効で失った coverage を取り戻す。
  実 POS rollout 由来の内容保証と production spec との統合保証が skip されたままである。
  **原本が別媒体に在る場合だけ** repo 内の最小 fixture へ移して復元できる。あわせて
  preflight resolver を production の候補選択 primitive へ一本化し (現状は 1 ケースで食い違う)、
  gate を node ごとの必要 label 集合へ細分化する。
- {{T:vacuous-persisted-commit-loop}} **P2・新規**: COMMIT record が 1 件も無い campaign では
  保存済み certification の検査 loop が空回りし、証拠なしで certified view が発行される。
  既存テストもこの受理を要求しているため、縮小には D1246 の共通 admission helper と
  既存 consumer の全数を伴う。
