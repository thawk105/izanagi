---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-02
wave: dev-wave-t2097-fixed-cost-decomp
seq: 1
title: [T-2097] 受入 1 shard の残差 約 58 秒の内訳を測点付きで確定した — 95% が起動費用で、その大半は 48 worker の全 collection (docs のみ、branch worktree-dev-wave-t2097-fixed-cost-decomp、実装面の差分 0・変異 matrix 免除)
---

## 本文

- D1384 (ユーザー裁定) が指した「全 shard 共通の report 外費用 約 56 秒」を分解した。
  結論と実測は {{D:residual-is-startup-collection}}、一次資料は
  `output/insights/2026-09-02_t2097-residual-breakdown/` (README + measurements + 逐語 6 本)。
  **短縮の実装・提案はしていない。** D1384 が採らないと決めた 3 項にも踏み込んでいない。

- **親の一次資料に誤りがあった。** 前 wave の `measurements.md` §F は残差を
  `wall − max(最長単体, 総報告時間/48)` として表にしていたが、これは理論下界を引いた値であり、
  実測の最大 worker report 合計を引いた値ではない。段 3 のレンズ A が指摘し、
  14 走 42 shard を `report.json` から再計算した。実測値で引くと残差は下界差引より安定し、
  中央値は shard-0 が 77.21 秒、shard-1 が 56.38 秒、shard-2 が 56.62 秒
  (下界差引では同じ走が 57〜104 秒に散る)。

- **段 2 が親の分解定義を否定した。** 親は 3 区間 (開始・窓内・終端) で足りると考えたが、
  最繁 worker が最後に終わるとは限らないため「その後に他 worker が report していた時間」が抜ける。
  4 区間へ改めた。実測ではその項は 0.000 秒だったが、成立しない分解は使わない。

- **段 3 の 2 レンズが 21 所見 (BLOCKER 7) を返し、親は 20 件を採用した。** 特に効いたのは
  (a) 「固定費」という呼称が D1298 の上界規定と衝突する、(b) shard-2 だけでは「共通」と言えない
  (shard-1 も計装した)、(c) D918 の cache regime (テスト 0 件の走が cache 無しで 49.32 秒・
  有りで 15.40 秒) を既存被覆から落としていた、(d) 閉包式は恒等式であって検証ではない、の 4 点。
  不採用は 1 件 — 較正走で実行 item を空にすることを「テストを減らす」に当たるとした所見で、
  受入の判定・排他・選択を変えない較正であり規律 2 の禁止対象ではないと裁定した (先例 D711)。

- **計測が測定対象を 2 度壊した。** 詳細は {{F:probe-injection-perturbed-suite}}。
  1 回目は probe を worktree 直下に置いたため作業ツリー全体を見る検査が落ち、
  2 回目は plugin 注入に使った環境変数を実行環境として検査するテスト 58 件が落ちた。
  3 回目に「import 直後に環境変数を production の姿へ戻し、復元できたかを process ごとに検査する」
  形へ直して成立した。計装 arm と対照 arm の赤集合の一致を測定の受理条件にしている。

- **機体依存の赤を見つけた。** 詳細は {{F:compute-node-openssl-dependent-red}}。
  bnode011 / bnode013 / bnode032 の openssl は 1.1.1q で `pkeyutl -rawin` を持たず、
  `test_mocc_trace_pair.py` の 2 件などが落ちる。基準走の bnode026 では通っていた。
  **本 wave の差分とは無関係で、直していない。**

- 計算資源: gen_S へ 3 回投入 (966024 = 1 arm で停止、966221 = 2 arm で停止、
  966271 = 9/10 arm 成立、Elapse 1596 秒)。probe は Codex `role=author` が書き、親は実行だけを行った。
  probe は repo へ commit せず repo 外へ退避し、逐語を insight の `verbatim/` へ収めた
  (sha256: py = `28a8a5e059b962df...`、pbs = `3186f4f6f21261f1...`)。

- 実装面の差分は 0 byte。`DW-S04` により変異 matrix は免除。受入全走は免除せず、
  記録 commit 後に land 対象 tip へ投入した (`DW-O12`)。結果は land の受領証が正本。

## 次の一手差分

### carry

- [T-139]
- [T-307]

### 更新

- [T-2097] **P2・内訳は確定。短縮に踏み込むかは裁定待ち**: 残差 約 58 秒の 95% は
  session 開始から最初のテストが始まるまでの区間で、その大半 (約 51.7 秒) は
  48 worker が各自で全テストを collection する時間である。テスト 0 件の較正走が 55.73 秒。
  **同型の量は D711 (2026-08-23) で 12.86 秒だった。node 数 1.35 倍に対し費用 4.33 倍**であり、
  node 数だけでは説明できない。次に何をするか (増加の原因を worker 内部まで分解するか、
  D634 が却下した削減手段を増加後の費用で再考するか、放置するか) はユーザー裁定に返す。
  base: c59cf31386f61375e0e9448af95c9ea53a30d5c8a37349a9929994bc3d4dc87a

### 新規

- {{T:collection-cost-growth-cause}} **P2・新規・裁定待ち**: collection 費用が D711 時点の
  12.86 秒から 55.73 秒へ 4.33 倍になった原因を、worker 内部 (module import・conftest・
  fixture 収集・deselect) まで分解するかどうかの裁定。本 wave の測点は「controller が 48 本の
  collection 完了通知を受け取る時刻」までで、内訳は測っていない。
- {{T:openssl-node-dependent-red}} **P2・新規・裁定待ち**: 計算ノードの openssl 版によって
  受入が赤になる。能力判定して skip するか、署名経路を版非依存にするか、機体側を揃えるかの裁定。
