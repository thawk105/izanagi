---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-22
wave: dev-wave-t2847-verifier-detection-design
seq: 1
title: [T-2847] verifier の検出力と容量を計算なしで設計した — 現行の判定は巡回・trace の完全性・証拠面 (X/P) と trace 外の commit 件数で決まり、abort・取引内の中間版・値・範囲読みの述語・liveness は判定の外。小履歴コーパス 27 案 (本書の走査で同じ意味の test が無いのは 2 案)、CC 変異 34 (族 26、変更機構 22) と無改変 si 1 の検出期待表、既存 broken patch 16 本の現行 pin への適用可否 (silo 11 本だけが素の pin に当たる)、si の v1 拒否、容量評価の計画と [T-2351] の関係、論文用の射程文 (docs のみ、branch worktree-dev-wave-t2847-verifier-detection-design)
---

## 本文

- 依頼 (ユーザー直接起動の `/dev-wave [T-2847]`、逐語 = insight `verbatim/request-t2847.md`): VLDB 差分分析 §4 P0 の計算なし設計。実 trace の取得・変異の実走・parser 改修、gate・検査・台帳の追加は scope 外。成果は insight `output/insights/2026-09-22/t2847-verifier-detection-design/README.md`。
- 段取り: 軽量版。親の事実収集 (Claude の読み取り子 sonnet 3 本: verifier の意味論 / fixture 22 件 / broken patch と si) → 段 2 plan (codex read-only 1 本、変異 34 行とコーパス 27 案の起草) → 段 4 裁定 (実装しない。mocc の数値は 2026-09-18 の 36 走 JSON に統一、無改変 si と `max_rset_` を外す変異を追加、si の GC 行を削除) → 親が insight を起草 → 段 6 read-only review 1 本 → 訂正 → 焦点再レビュー。段 3 は省略 (設計択一が割れず、正しさ防壁・受理集合を変えない)。変異 matrix は実装面の差分ゼロで免除 (DW-S04)。
- 段 6 review は NO-GO (must-fix 10・should 3)、親の判定はすべて real で全件採用。最重要 3 件: (1) si の update は read set から R を消すので、first-updater-wins を外した lost update は v2 化しても巡回にならず indeterminate (起草と初稿は「巡回で N」と書いていた)。(2) mocc の lockskip / early-unlock と hot regime の hot-update-unlock は 4 thread で version dup が併発する (JSON の各 run の `integrity.version_dups`、3,564〜67,777)。(3) 「純増 14」には test 内の合成入力で被覆済みの案が含まれていた。焦点再レビュー 1 巡目 (NO-GO、must-fix 1) の指摘で G1c 型の巡回も既存 test (`_ordinal_witness_trace`) にあると分かり、最終の区分は再説明 13・inline 被覆済み 10・説明の追加 2・未被覆 2 (同じ取引の二重読み 2 種。実 silo は 2 度目の読みを read set から返すので実 trace には出ない合成入力)。焦点再レビューの他の指摘 (hot-update-unlock の regime 条件、profile job の読み方、D2214 の条件付きの安全主張) も全件採用した。
- 新事実: (1) 既存 broken patch 16 本のうち現行 pin `e9e477ca` にそのまま当たるのは silo の 11 本 (`git apply --check`、fuzz なし)。mocc 4 本は計装 patch の上、trigger-misattr は trigger-gating 骨格の上でだけ当たる。write-intent 4 本は当たるが現行 pin に `I` の emitter が無く、改竄が certified になりうる。(2) 「無改変 si で 3,576 巡回」(2026-06-18) は v1 を受理していた当時の verifier の記録で、v2 専用化 (`fb5e74a17`、2026-08-12) 以降 si の emitter は移植されていない。論文稿 2026-09-21c の検出力の段落はこの断りを持たない (本 wave は論文稿を編集しない)。(3) 末尾の取引・末尾だけを持つ thread file の欠落は、commit 証人を渡さない API / CLI の呼び出しでは certified になりうる (特性化 test あり、pipeline は常に渡す)。(4) D2214 の P1 の v1 (方策だけを開く) は、その条件付きの安全主張 (契約に適合した方策が正常に返る限り) の下では §4.1・§4.2 の機構を骨格に残すので、LLM が壊した候補を verifier が捕らえた記録は作れない (D2214 項 2 も同旨)。
- 素材: 論文用の射程文 (短文・方法節・妥当性への脅威・使わない言い方の表) は insight §7。
- 記録前検査: 三軸語走査は rc 1 だが hit は main に既存の 3 file (`output/env/pegasus/calibration/s8b-floor-official/20260916T111925Z-2c8cf9be/`) だけで本 wave の file は 0 件。raw 1 file と codex 逐語 2 file の行末空白を可逆に除去し、`raw/NORMALIZATION.md` と `verbatim/NORMALIZATION.md` に原文 sha256・bytes・位置を記録。検査に使った使い捨て script (適用検査・JSON 集計・二重読み走査) は repo に入れず job dir に置いた。
- 段 6 の前に local main `ad4bd2bb7` (D2219 = /rulings 第 31 回の記録を含む) を固定 SHA で前方 merge (`dd587fe88`)。
- 工数: codex 子 = plan 1 + review 1 + focus 2 の 4 本。Claude の読み取り子 3 本 (sonnet)。計算ノード job は受入だけ。wave の壁時計は開始 gate (2026-09-22 08:5x JST、job dir `startup-gate.log`) から。wave 開始時の `EnterWorktree` は checkout 中の EINTR で失敗し、branch だけ残ったので既存 branch を指す `git worktree add` (timeout 560) で作り直した。受入全走と land の結果は本 entry にも insight にも書けない (受入は記録 commit の後に走り、land の結果は fold の後に確定する)。

## 次の一手差分

### 更新

- [T-2847] **P1・設計済み (VLDB 差分分析 P0: 検証の意味と容量)**: 計算なしの設計を insight `output/insights/2026-09-22/t2847-verifier-detection-design/README.md` に記録した — 判定の範囲 (§2)、小履歴コーパス 27 案 (§3、本書の走査で同じ意味の test が無いのは F03・F06 の 2 案)、CC 変異 34 と無改変 si 1 の検出期待表 (§4、族 26・変更機構 22)、既存 broken patch 16 本の現行 pin への適用可否と記録 (§5.1)、si の v1 拒否 (§5.3)、容量評価の計画と [T-2351] との関係 (§6)、論文用の射程文 (§7、済)。
  残り = (1) コーパスの未被覆 2 案 (F03・F06) と B06 の分類 `G1c` の assert を test として実装する (Codex author。fixture dir として置くなら `test_capacity_all_fixture_results_match_frozen_baseline` の凍結一覧の更新が同じ変更に要る)。(2) 変異の実走 (§4。既存 16 本は既存 driver、新規は D16 第 3 類の out-of-tree patch)。(3) 容量の実測 (§6.3。まず VLDB の実験が検証する trace の長さを計算なしで決め、既存の実測範囲 = write-heavy / balanced 10 s・read-heavy 6 s・巡回 0 の外だけを測る)。(4) si の emitter の v2 化 ([T-2854] の実装単位 (12) に相乗り)。完了 = 検出表の実測と容量の実測表。
  計算: (1)〜(3) はいずれも、同じタスクで投げる job の合計 (開発の検査を含む) が 2 node 時間以上なら投入前に見積りを示してユーザー確認 (D2212 項 4、D2219 項 1)。一次資料 `output/insights/2026-09-21/vldb-direction/gap-analysis.md` §4 P0。
  base: 5a4e8872e46c031dc17dfd92b43ac1d132afbd8166576b4a40c9f8c04a2a2fea
