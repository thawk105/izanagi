---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-14
wave: dev-wave-acceptance-bottleneck
seq: 1
title: 受入全走のボトルネックを実測分解し、速度改善候補 2 件を反証した (実装差分ゼロ、branch worktree-dev-wave-acceptance-bottleneck)
---

## 本文

- ユーザー依頼は「受入全走のボトルネックを改善してください。リワードハック禁止」。
  親は候補を 2 つ立て、**いずれも実測で反証して `DW-S04` の「実装しない」裁定**とした。
  実装差分ゼロのため変異 matrix は免除、受入全走は実走した。
  逐語と数値は `output/insights/2026-08-14_acceptance-bottleneck-decomposition/`。
- **ボトルネックの分解を初めて定量化した。** pytest 本体 146.67 秒に対し受入 1 回の実時間は
  318〜2755 秒で、支配項は lease 待ち (93%)。critical section は
  pytest 156 秒 + 親の受入後作業 約 290 秒 + land 53 秒 + (赤のとき) checker 15 + 63n 秒。
  **遅いのはテストではなく「1 回で終わらないこと」である。**
- **受入試行 31 回中 成功 8 回。失敗 23 件のうち 16 件 (70%) の原因は既に main で閉じていた。**
  最多の `probe worktree is not clean` 13 件は [T-1053] で、collect の 120 秒 timeout 3 件は
  `_DISPATCH_TIMEOUT_SECONDS = 5100.0` で解消済み。**着手前に台帳と insight を引いたので
  二重実装を免れた。**
- **[T-1053] 修正後の checker を初めて実走で検証した。** base main に対し 6 回 (うち 2 回は同時実行)
  走らせ、6/6 とも指紋 gate を通過。rulings 第 12 回 #2 が置いた [T-1066] 再訪条件は現時点で不成立。
- **反証 1 = [T-1090] の有界並列化。** 段 2 プランは実装可能な設計を出したが、段 3 の 2 レンズが
  独立に blocker を出した。決め手は親の強化した形で、checker の単独 rerun は
  `rerun_rc == 1` なら**非帰属 = land を通す**向きに効くのに対し、signal / launcher 系テスト族は
  負荷で落ちることが 544 / 548 で実測済みである。4 並列にすればこの単独走のノイズ床が上がり、
  **帰属する赤を非帰属と誤判定して land を通す方向へ系統的に偏る**。
  効果は受入試行 31 回に均して約 26 秒しかなく、`--force-dispatch` の 4 本同時投入は
  他 wave の qsub 待ちを増やしうるため全体では負になりうる。設計判断は
  {{D:verdict-input-context-is-invariant}}。
- **反証 2 = merge message provenance の claim 前 fail-fast。** 実測 2 件がいずれも
  lease 待ち約 2500 秒を消費してから拒否されていたので前倒しを設計したが、成立しない。
  **`check_ai_provenance --message-file` の合否は message 内容でなく repository 状態の関数**である。
  t1050 は受入試行 1 で拒否・試行 5 で受理されたが、両者は同一の message file を使い、
  その file は 20:45:45 以降不変であった (sha256 `be4ac776…`)。
  claim 前の clean index ではこの入力が通るため、救おうとした 2506 秒は救えない。
- **親は自分の誤りを 3 件、子の指摘と自分の実測で訂正した。** (1) 「n=5 なら並列度 4 で約 100 秒」は
  算術誤り (正しくは 141 秒)。(2) 「受理集合を 1 bit も変えない」は誤りで、実際は 3 種類の縮小がある。
  (3) provisional 裁定 P1 (共有状態は submodule の読みだけ) と P3 (通常経路 2 走で receipt の
  byte 一致を示せる) は段 2・段 3 の双方から反証された。
- **並行 wave との所有衝突を実測した。** `dev-wave-t1076-waiter-bytes-contract` は ahead commit 0 件
  だが `tools/dev_wave_wait.py` とそのテストに未コミット変更を持つ。commit 数だけで
  「未着手だから触ってよい」と判断すると衝突する。
- codex 子は 4 本 (plan v1 / consult sol / consult luna / plan v2、すべて max・read-only)、
  全て `outcome=accepted`。実装子・fix 子・review 子は「実装しない」裁定のため起動していない。
- 放置した場合、[T-1090] は「別 wave の設計事項」として台帳に残り続け、次に着手した wave が
  同じ並列化を実装して正しさ防壁のノイズ床を上げる。本 wave はその経路を実測で塞いだ。

## 次の一手差分

### 更新

- [T-1090] **P3・要裁定**: 非帰属 checker は赤 n 件に対し collection と rerun で dispatch を
  2n 回行う。**本 wave が実測モデルを取り、有界並列化は不採用を推奨した**
  (低負荷で `T(n) = 15 + 63n`、P=4 の節約は受入試行あたり平均 約 26 秒。
  単独 rerun のノイズ床を上げて帰属する赤を非帰属へ倒す偏りがあり、
  `--force-dispatch` の同時投入は他 wave を遅らせうる)。
  代替として **1 dispatch job で複数 node を扱う設計** (2n qsub を n または 1 へ減らす) を推奨する。
  これは rerun の実行環境を変えないので同じ偏りを生まない。dispatcher の secure task と
  receipt schema の新設が要るため、着手可否はユーザー裁定を待つ。
  base: 7837c3df6b0ac419a752762aae9d68bdce19eadb85732ab8148d89388e6b19fb

### 新規

- {{T:provenance-message-verdict-depends-on-repo-state}} **P2・新規・要裁定**:
  `check_ai_provenance.py --message-file` の合否が message 内容でなく repository 状態
  (`MERGE_HEAD`・staged path 集合) の関数であることが、受入の再走を誘発している。
  同一 message file が受入試行 1 で拒否・試行 5 で受理された実測がある。
  親は毎回「message が悪い」と誤解して message を書き直す codex 子を起動しており、
  **失敗時に checker の stdout を出さないことがこの誤解を固定している**。
  診断を出す処方は [T-1092] と同型だが、`tools/dev_wave_wait.py` を
  `dev-wave-t1092-receipt-diagnostics` と `dev-wave-t1076-waiter-bytes-contract` が
  所有しているため、3 者の順序をユーザーが決める必要がある。
- {{T:acceptance-lease-hold-after-green}} **P2・新規**: 受入 lease の critical section の内訳は
  pytest 156 秒 + **親が受入成功後に lease を握ったまま行う作業 約 290 秒** + land 本体 53 秒である。
  最大の削減余地はコードでなく手順にある。「段 8 の編集は受入より前に済ませる」は既に裁定済みだが、
  実測では受入完了から land 起動まで 288 秒空いていた (t1053: 00:13:25 → 00:18:13)。
  受入投入前に land 用の commit と記録を完成させる手順を dev-wave 契約へ書けるか検討する。
- {{T:red-check-receipt-completeness-not-verified}} **P2・新規**: 受入 waiter は非帰属 checker の
  receipt について schema と非帰属 status と sorted unique nodes までしか検査せず、
  `collections` の順序・欠落、`submodules` の型・順序、collections と nodes の件数対応を
  再検証しない。raw bytes hash は壊れた bytes をそのまま記録するだけである。
  checker 側が壊れた場合に consumer が防壁にならない (段 3 レンズ A の所見)。
- {{T:dev-wave-docs-budget-blocks-small-fixes}} **P3・新規・要裁定**: 段 8 の自己改善が
  **予算で実際に塞がれた**。「受入試行の終端・所要・失敗 stage の一次資料は job artifact directory の
  待ち手 log と子 log であり docs には無い」という 2 行を足そうとしたが、
  話題が合う `DW-O18` は 995 bytes / 単節予算 1000 bytes、`DW-O02` は L1.5 の合計予算が満杯で、
  どちらにも入らなかった。`docs/dev-wave/operations.md` の L2 節は
  `DW-O09` 997・`DW-O17` 974・`DW-O19` 984・`DW-O20` 996 と軒並み上限際にある。
  契約どおり変更を止めて裁定へ返す。予算値の引き上げは提案しない。
  空きのある L2 節 (`DW-O03` 261、`DW-O13` 165 など) は話題が合わず、
  意味を保った統合ができない。新設節は D271 の鏡像条件を満たすか要判断。
- {{T:acceptance-attempt-outcome-ledger}} **P3・新規**: 受入試行の終端 (成功・失敗 stage・所要秒)
  を機械集計する仕組みが無く、本 wave は job dir の mtime と log から手作業で復元した (約 30 分)。
  受入 receipt か task-run へ「lease 待ち秒・critical section 秒・終端 stage」を残せば、
  以後のボトルネック裁定が実測でできる。
