---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-16
wave: dev-wave-t304-throughput-rename
seq: 1
title: [T-304] throughput_ops_sec を実体名 throughput_tps へ改め、live role 定義の記述 drift 3 種を直す — 判定器の版 bump が要るという最大の分岐を実測で閉じた (コード + docs、branch worktree-dev-wave-t304-throughput-rename、受入全走 = 23966 passed / 68 skipped、変異 5/5 KILLED)
---

## 本文

- ユーザー裁定 (worklog entry (109)) の択 (a) を [T-304] / [T-305] とも採用した。設計判断は
  {{D:throughput-tps-rename}}。**値は正しく名前だけが誤りである**という性質は wave を通じて不変に扱った。
- **最大の分岐は「8c 事前登録の `DECIDER_VERSION` を bump する必要があるか」だった。** 段 3 の
  2 レンズが独立に identity 到達を指摘し、成立すれば D439 により wave を 2 本へ割る必要があった。
  親が実測して**不要**と確定した (根拠は {{D:throughput-tps-rename}} 決定 4)。射影 module の
  blob 同一性は変わるため、旧登録が `projection-blob-mismatch` になることだけを開示した。
- **棄却した所見 (refuted):** 段 3 レンズ B の「`throughput_tps` の同名化が混同を生む」、
  「schema v4 化は過剰」、段 6 レビュー B の「旧成果物の読み替えに機構が要る」。
  いずれも現物の読解で反証された。
- **親 brief の誤りを 6 点、段 4 で訂正した。** とくに (i)「旧名 0 件だから行は競合しない」は
  実測と推論を混ぜていたため後半を撤回し、(ii) [T-305] を同一 wave に含める根拠を、T-1008 の
  再訪条件からの類推 (レンズ B が反証) ではなく本 wave のユーザー指示そのものへ差し替えた。
- **段 2 プランの誤分類を親が止めた。** `src/coder-spec.md` §4 は本文が自ら「旧設計で superseded」
  「経緯記録として残す」と宣言する歴史記録であり、live copy ではない。改名しない。
- **段 6 レビューは 2 本とも実装本体の追加修正を出さなかった** (レンズ A 所見 0 件、レンズ B は
  must-fix 1 件が親担当の所要台帳更新)。所見ゼロを変異なしで緑と数えない規律に従い変異を回した。
- **変異は 3 度投げ直した。** (i) 初回は kill 集合が 153 / 214 node と大きく中継上限に当たった。
  (ii) designated gate だけへ絞って 2〜3 node に縮めた。(iii) `review_ledger` の source pin を戻す
  変異は `test_codex_agents.py` を **import 時に落として 48 件の collection error** にするため、
  node 抽出が test ID を作れず `PARSE_ERROR` になった。同じ pin 閉包を adapter 側の source sha で
  突く形へ差し替えて 5/5 KILLED になった。初回・二回目の結果は erratum として insight に残す。
- **`test_reflux_originless_compatibility.py` の凍結 golden は M1 / M2 / M3 に対して冗長 gate である**
  (payload bytes が変われば発火する)。意味の gate は M1 が projection の exact-key、M2 / M3 が
  producer 実走経路である。単独変異の証拠としては意味 gate の側を読む。
- 所要台帳の更新で、焦点走の JUnit 全体を渡すと本題と無関係な未登録 nodeid が 43 件追加された。
  子が正直に停止して報告したため、親が本 wave の 3 node だけへ射影した JUnit を作って投げ直した。
- 一次資料 = `output/insights/2026-09-16/t304-throughput-rename/`。
- 工数: codex 子 8 本 (plan 1、consult 2、review 2、author 3 — うち台帳 author は 2 度の停止報告を
  含む)。計算ノード job は焦点走 1 + 変異 24 走。

## 次の一手差分

### 完了

- [T-304] `throughput_ops_sec` を `throughput_tps` へ改め、[T-305] の記述 drift 3 種も同一 wave で
  直した。role schema は v4 へ、report schema は v3 据え置き。旧名成果物の読み替えは
  {{D:throughput-tps-rename}} 決定 3 で決めた。
  remaining: none
  base: 5a39cb91a01d320932f7e4536dd5f5da54909359d41062727956a45368b561ee

### 新規

- {{T:preregistration-rerun-after-contract-loader-change}} **P2・新規 (本エントリ)・ユーザー裁定要**:
  contract-loader path の bytes を変える改修のあと、改名前 commit を指す既存の登録は
  `projection-blob-mismatch` になる。記録済み測定は無効にならないが、既存実走を新しい checkout で
  再受理させる必要があるかと、その手順を決める。pin の緩和は候補に入れない。
- {{T:role-doc-drift-beyond-adjudicated-three}} **P3・新規 (本エントリ)**:
  裁定 (109) が挙げた記述 drift 3 種の外にも実在する食い違いが残る。planner の「現行測定値」が
  世代間で凍結される点、coder の baseline が全世代で凍結される点、手動射影 runbook 2 件に
  実在しない `last_delta_pct` が残る点。いずれも自律 trial の validator には到達しないが、
  手動 prompt と role 本文の不一致は残る。直すか据え置くかを決める。

### 見送り追記

- [T-305] 2026-09-16 に [T-304] と同一 wave で記述 drift 3 種を実装した。D205 による active 除外は、本 wave のユーザー指示が両者を同一 wave と名指ししたことで解けた。
