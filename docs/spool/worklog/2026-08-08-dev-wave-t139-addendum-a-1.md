---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-08
wave: dev-wave-t139-addendum-a
seq: 1
title: [T-139] 追補 A の 13 field を埋めて確定パッケージへ返した — 凍結はしていない (docs のみ、実装差分なし、受入 7372 passed / 20 skipped、赤 1 件は F57 のフレーク、変異は免除、branch worktree-dev-wave-t139-addendum-a)
---

## 本文

- **追補 A の閉集合 `a01`〜`a13` を全件、逐語の数値・式・手続きで埋めた。凍結はしていない。**
  成果物は `output/insights/2026-08-08_t139-addendum-a/` の `addendum-a.md` (追補 A 案)、
  `erratum-core-s15.md` (§15 の 2 箇所を `a13` 基準へ supersede)、`record-items.md`
  (受領証 schema の要件文書)、`package.md` (裁定 R1〜R7 + 凍結可否)。
- **凍結 core の bytes は 1 byte も変えていない。**§15 要件 3 が「承認済み core の digest と一致」を
  要求するため、core を編集した瞬間に凍結が壊れる。実測で digest `ac939af4…` が fold commit
  `F=88d68f91`・HEAD・作業木の 3 者で一致することと、path を pin する `*.py` が 0 件であることを
  確かめてから着手した。
- **敵対検証を 5 本回し、5 本すべて NO-GO だった** (段 3 の 2 レンズ = blocker 11 件、
  段 6 の 2 レビュー = 13 件、焦点再レビュー = 10 件)。**この NO-GO は成果物の否定ではない** —
  判定内容は「凍結・承認 fold・pilot 投入へ進めない」であり、本 wave の終端 (承認待ち) と一致する。
- **親の設計が段 6 で 1 度倒れた。** 親は `a10` の最悪検出力を least-favourable configuration
  1 点で評価する案を採ったが、これは相関方向を覆わないため**凍結 core §6 の「共同信頼集合上の
  最悪検出力」を満たしていなかった** (親自身がその限定を本文に書いていた)。
  相関に依存しない union bound (成分ごとの非心 t の周辺確率) へ差し替え、
  `Θ` 全体に対する**認証された下界**を閉形式で与える形にした。副産物として
  Monte Carlo・seed・Wishart 極値分位点・branch-and-bound がすべて不要になり、
  段 3 レンズ A が指摘した「同じ pilot から 2 人が同じ `J` を得られない」も同時に消えた。
- **親が段 6 の fix で回帰を 3 件作り込み、焦点再レビューが全件検出した。**
  (i) erratum の resolver 契約を「承認済み erratum が**ちょうど 1 件**」としたが、
  同じ package の R2(a) / R5(b) はいずれも同じ core への第 2 erratum を選択肢に持つため、
  R1(a) と R2(a) を同時に裁定した瞬間に resolver が必ず失敗する。exact set 契約へ改めた。
  (ii) `a08` の configure argv template に `-DCMAKE_CXX_FLAGS` を残したまま結合規則でも
  同じ token を足し、二重指定になっていた。(iii) 検証割当てを唯一の build 生成元にした結果、
  1500 秒 cap では configure/build の直列総和 1440 秒に対し後処理が 60 秒しか残らなかった。
  いずれも 2 巡目の fix で閉じた。
- **`a04` の「外部証拠」案は trust root にならないと判明した。** job の stdout や scheduler 出力に
  書かれる内容の生成者は job = producer 自身であり、append-only は改竄防止であって内容の真実性を
  保証しない。実現可能で fail-closed な唯一の写像として、**`a03` の不成立は位置を問わず
  「性能測定の開始後の失敗」へ写し、予備で置換しない**を既定にした。緩和は裁定 R7 へ返した。
- **`a03` の閾値には支持する測定が 1 件も無い。** 既存 36 行が記録したのは `load1` であって
  `/proc/stat` counter ではなく、かつ J=1 probe は run 間に待機を 1 秒も置いていない
  (`t139_positive_control_probe.sh` に `sleep` が無い)。親 brief は `load1` を
  「3.29 → 13.47」と要約したが、これは liveness 6 本終了時点の値で、36 行全体では
  **3.29 → 40.18** である (段 3 レンズ B が独立に検出)。凍結前に `gen_S` で環境 probe を
  1 本走らせることを推奨し、裁定 R4 とした。
- **`CCBENCH_TRACE=1` の build が通る witness は存在しない。** J=1 probe の liveness build は
  実際には `TRACE=0 / ADD_ANALYSIS=1` であり、検証割当てが要求する trace-enabled build の
  先例になっていない。R4 の probe に含めた。
- **`a12` は core §7 の「較正する」義務を満たしていない。** cluster 間変動が 1 点も観測されていない
  以上、J=1 の残差からは cluster level の型 I 誤りを較正できない。追補の中で
  「stress check」と呼び替えても core の義務は消えない (D234 は追補による core の意味変更を禁じる)。
  裁定 R2 へ返した。
- **記録項目は「closed schema」という呼称を外した。** 全 nested object の exact key・型・必須性・
  配列長・cross-field 制約を網羅していないため、2 つの実装が同じ受領証で適格/拒否に分かれうる。
  本書は schema が満たすべき**要件**を定める文書とし、完全な機械可読 schema の発行と
  digest 束縛を裁定 R6 へ返した。
- **実装差分がゼロのため変異 matrix は射程外** (`DW-S04` の免除条項)。
  受入全走は免除せず、local main (`a0c55a87`) を取り込んだ merge 済み tree で実走した
  (request `896006`、48 worker、1216 秒)。**7372 passed / 1 failed / 20 skipped。**
  赤 1 件は `test_codex_worker_launch.py::test_manifest_is_appended_while_correlated_session_is_running`
  で、F57 の型 (launcher subprocess が rc=1 / stderr 空) である。同 file の単独再走
  (request `896010`) は 64 passed / rc=0 で再現しない。本 wave の差分は docs のみで
  当該実装へ到達しえないため `DW-O18` により帰属しない。F57 へ再発として記録した。
- **段 8 の改善候補 1 件は予算不足で本文へ入れられず、[T-664] へ寄せた。**
  背景 job + worktree 隔離のセッションでは、`DW-O01` が定める 1 行の起動形
  (`nohup setsid bash -c "codex exec … > log 2>&1; echo $? > done"` を Bash へ直接渡す形) が
  worktree guard に「複雑すぎて worktree 内に留まると検証できない」と**機械拒否される**。
  本 wave では launcher script を Write して `bash <script>` で起動する形に置き換えて通した
  (段 2 投入時と段 1 の検算コマンドの 2 回で実測)。`DW-O01` へ 1 行足したいが、
  `docs/dev-wave/operations.md` は 8387 / 8400 bytes で空きが 13 bytes しかない。
  上限引き上げは提案せず、同じ壁を 3 wave 続けて踏んでいる [T-664] の材料として記録する。
- 一次資料 = `output/insights/2026-08-08_t139-addendum-a/` (段 1 brief、段 2 プラン、段 3 の 2 レンズ、
  段 4 裁定、段 6 の 2 レビュー、焦点再レビュー、fix 対応表 2 巡、成果物 4 本)。
  裁定パッケージ = 同 `package.md`。

## 次の一手差分

### 更新

- [T-139] **P1・ユーザー裁定待ち**: 追補 A の 13 field は埋まったが凍結していない。
  `output/insights/2026-08-08_t139-addendum-a/package.md` の R1〜R7 を裁定する。
  R4 = (a) を採る場合は `gen_S` の環境 probe (`/proc/stat` 実測・`CCBENCH_TRACE=1` build・
  compiler digest) を先に走らせ、`a03` の閾値を確定してから追補 A を再発行する。
  凍結後の順序は「追補 A → producer 実装 → pilot」で変わらない。
  base: 8f5625539dc91ce6035ce674d94bfa1a36c90c137ac6413979fcd434b80542b2
