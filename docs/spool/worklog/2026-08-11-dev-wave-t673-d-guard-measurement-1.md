---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-11
wave: dev-wave-t673-d-guard-measurement
seq: 1
title: 本番側 guard D を本番編集ゼロで実測した ([T-673] 残余 (3)) — land 直前に [T-737] が既存テストで同じ族を全域殺すことが判明し、D の CI 上の限界便益はゼロになった (docs のみ、受入 8275 passed / 20 skipped / 567.95 秒 / rc=0、変異 11 arm 107 entry 事前登録一致、branch worktree-dev-wave-t673-d-guard-measurement)
---

## 本文

- **裁定の一次資料。** rulings-inbox §56 (2026-08-10、発話「推奨通りで」) の [T-673] (3)
  「D 計測可・本番編集禁止恒久」。先行 wave の裁定パッケージが「D は本番編集禁止により
  測定対象から外れた」と記していた欠落を埋めた。成果物は
  `output/insights/2026-08-10_t673-d-guard-measurement/`。
- **本番編集ゼロを構造で担保した。** 段 2 プランは probe を side branch へ置く案だったが、段 3 の
  敵対レンズが「land しない commit でも object と ref は残り、cherry-pick → revert で land 履歴に
  一度入れられる」と指摘したため撤回し、**repo 外の `--shared` clone** へ置き替えた。
  izanagi の object DB に本番編集 commit を 1 つも作っていない。
- **land 直前に、承認済み裁定の前提を覆す新事実を見つけて測り直した。** 計測 base 以降に
  [T-737] が land し、既存テストに 65 env の chain を 3 層へ通すテストが 8 本増えていた
  (不正行はすべて末尾)。**現行 main で同じ 14 変異を走らせたところ 14/14 KILLED** で、
  登録した直接 slice 族は N = 1〜64 の全域で既存テストだけで殺される。
  よって **D の CI 検出上の限界便益はこの族についてゼロ**になり、裁定パッケージの中心的結論を
  書き換えた。計測 base 時点の corpus に対する 43 セルという値は、その旨を明記して残した。
- **敵対レビュー 4 本の所見 13 件はすべて real、refuted 0 件。** 追加 arm の提案 3 件は
  「arm を増やす」のでなく「測定器の node 族を増やす」形へ縮約して採用した。主指標は
  `KILLED`/`SURVIVED` ではなく**結果クラス**へ変えた — 入力ごとに「受理されたときだけ赤くなる node」と
  「拒否理由が意味的かを見る node」を分け、後者は kill に数えない。
- **D を 2 変種で測ったのは、レビューの懸念を数に変えるためである。** 「guard が既存の pin 済み
  診断を奪う」という指摘に対し診断保存型 D₁ と診断上書き型 D₂ を両方作った。結果、D₂ だけが
  既存の no-op 診断 3 node と発行 tool 1 node を追加で壊す。**設計論争が実測で決着した。**
- **事前登録を 2 回誤り、訂正して再走した (erratum)。** どちらも親の導出誤りで実装欠陥ではない。
  (i) 先行 wave の focal 4 node 用の期待値を、runner にファイル全体を渡す arm へ流用した。
  (ii) D₁ の G guard が発火すると P loop 自体が走らない先取り効果を見落とした。
  第 1 巡 77 entry のうち 47 entry を再走し、**最終 11 arm・107 entry は全件一致 (MISMATCH 0)**。
  第 1 巡の台帳は消さず insights へ凍結した。両誤りは
  {{F:preregistered-nodes-need-runner-scope}} と {{F:guard-preempts-later-diagnostics}} へ入れた。
- **arm 実行スクリプトが rc を握り潰していた欠陥も敵対レビューが見つけた。** 第 1 巡は
  `arm=f0 rc=1` の直後に次の arm を開始し、最終 rc も 0 だった。第 2 巡で是正した。
- **コスト測定は 2 度目で成立した。** 1 度目は `tools/run_tests.py --force-dispatch` 経由で投入したが
  必須の環境変数が計算ノードの job へ渡らず fail-closed で停止し、runbook §3 の batch 形で投入し直した。
  **先行 wave が単発観測で順位を付けられなかったのに対し、今回は事前登録した順位判定 3 条件が
  M=2/8/64 のすべてで成立し、「D₁ は測定可能に遅い (1 call 約 1〜1.6 µs)」と言えた。**
- **段 8 の候補 2 件は reference へ統合できなかった。** 発火段 (段 4) の `DW-M01` は L1 層で
  **予算残 0 bytes** ([T-627]・先行 [T-673] wave に続き 3 波連続)。裁定 §56 (7)「L2 か台帳」に従い
  failures fragment と memory 2 件へ振り分けた。
- **子の内訳。** codex 子 7 本 (段 2 plan / 段 3 レンズ 2 / 段 5 実装 / 段 5 コスト測定器 /
  段 6 fix / 段 6 追加 spec) と段 6 敵対レビュー 2 本。実装面はすべて Codex `role=author` が書き、
  親は brief・裁定・統合・全走・記録のみを行った。probe も測定器も land していない。
- **受入は tip `39e993cb` で 8275 passed / 20 skipped / 567.95 秒 / rc=0。** 本エントリと F3 arm の
  記録を足した最終 tip でも同一形で再走して緑を確認してから land した (2 走目の件数は job 逐語)。
- **本 wave は D を採用していない。** 採否と「本番編集禁止恒久」を解くか否かはユーザー裁定に返す。

## 次の一手差分

### carry

- [T-737]

### 更新

- [T-673] **P2・ユーザー裁定待ち (D の採否)**: §56 の (3) を消化した。本番編集ゼロのまま D の
  検出力・コスト・偽陽性・残穴を実測し、裁定パッケージ
  `output/insights/2026-08-10_t673-d-guard-measurement/RULING-PACKAGE.md` §7 で 5 点
  (D の採否と本番編集禁止の解除、overhead 約 1 µs/call の許容、D 自身の正例テストの作り方、
  probe clone の保存可否、発行 tool 層の実入力での露出) を返した。
  **[T-737] の land により、この族の CI 検出は既存テストが全域で担うことが実測された**ので、
  D を採る根拠は N ≥ 65 と runtime 防御に限られる。残余は (4) E (変異 spec の恒久登録) の
  運用義務の所在。
  base: 14ec004134674ebfb5cd11b80b2222759e41b1f0020421604fa352be26b90ed5
