---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-08
wave: worktree-dev-wave-t2067-bcd-population
seq: 1
title: [T-2067] load-only consumer の母集合を今日の main で数え直した — 未強制は 2 群で、うち 1 群は先行 wave が母集合から外していた (docs のみ、branch worktree-dev-wave-t2067-bcd-population、実装面の差分ゼロにつき変異 matrix は DW-S04 の免除)
---

## 本文

- **依頼の前提だった「3 群」は 1202 (09-02) 当時の値で、1236 (09-03) が既に 4 群へ訂正していた。**
  1345 の carry はその訂正前の文面を写し、(c)(d) も 1236 が「完了」と記録したものを未完として
  再掲していた。着手前の一次資料照合で止め、子を起動する前に前提を作り直した。詳細は F35 の再発。
- **letter の指す内容が entry ごとに drift している。** (c) は 1202 の旧 public builder →
  1236 で private 化完了 → 1345 で別内容 (`verify_manifest` の library 経路) と、同じ letter に
  別の主題が載っている。「1345 が (a) 着地後の再監査を意図して (b) を再開した」可能性は
  段 3 レンズ B が指摘したとおり否定できないので、意図は断定せず数と drift だけを記録した。
- **母集合の件数は権威ある閉包に由来しない、と明記した。** `load_ratified_freeze` の caller を
  exact 一致で固定するメタテストは repo に実在しない (段 2 と段 3 レンズ A が独立に、
  切らない検索で確認)。したがって 9 callsite の正本は今回の AST 走査である。隣接する
  `build_observations` / `_gate_check_validated` / `verify_manifest` には caller 閉包テストが
  実在するので、対象を取り違えると「在るものを無い」と書くことになる点も併記した。
- **先行 wave の除外 1 件を独立検算で戻した。** 1236 は `s8b_oracle_driver.py:496` を
  「private core の self-load であり public v2 wrapper はこの形で到達させない」として母集合から
  外していたが、段 2 が公開 CLI からの到達経路を示し、段 3 レンズ A が具体 trace まで詰めた。
- **段 3 の 2 レンズが割れた。** レンズ A は `:496` を must-fix とし、レンズ B は「安定した
  production 入力の穴ではない」としてコード変更案の撤回を must-fix とした。**事実認定は一致して
  いる** — 到達には二読の状態変化が要る、という点で同じ。割れたのは分類だけである。親は
  DW-G04 (発火条件を既存 artifact path か計測 ID で書けるか) と DW-G05 (成果物影響を示せるか) で
  裁き、**実装は不採用・分類の訂正は採用**とした。ユーザーの scope 制約 (仮想リスク向けの
  gate・検査・台帳・一般化の追加は scope 外) とも同じ向きである。
- **段 2 が併せて提案した regression node は不採用にした。** 「初回 load 失敗 → 二回目成功」を
  mock で作る node であり、既存入力の回帰ではなく仮想遷移の新設に当たる。
- **不実装にしたが、承認済み裁定への新事実があるので裁定パッケージへ送る。** D65 決定 (5) は
  「public gate_check は v2 で必ず自己検証」と定めているが、この分岐ではその不変条件が成立しない。
  DW-S04 に従い親が不採用で閉じず、択一をユーザーへ返す。
- **D1371 の前提が今日も成立することを実物で確認した。** C06 予算経路は
  `p3_autonomous_workload_trial.py:2074` の schedule authority resolver が無条件に失敗するため
  `reserve_all_cells` へ到達しない。再評価の発火条件だった C05 も上流待ちのままである。
- 段 2・段 3 の子 3 本はいずれも read-only sandbox のため pytest を実走していない。
  prompt でその旨を明示し、緑とは申告させていない。実測はすべて親が行った。
- 逐語と母集合表は `output/insights/2026-09-08_t2067-bcd-population/`。

## 次の一手差分

### 更新

- [T-2067] **P1・(a)(b)(c)(d) 完了、(e)(f)(g) が残件 + 裁定待ち 1 件**: (b) の母集合を 2026-09-08 の
  main で数え直した。静的 loader の production callsite は 9 箇所で、強制済み 7 (狭い選択 API 5 +
  full launch validation 2) / 未強制 2 である。未強制は C06 予算群
  (`p3_autonomous_workload_trial.py:4957`、D1371 が不実装と裁定・再評価条件の C05 は上流待ち) と、
  standalone gate の二読 fallback (`s8b_oracle_driver.py:496`) の 2 つ。後者は先行 wave が母集合から
  外していたものを本 wave が独立検算で戻した — 到達には「初回 read 失敗 → 直後の再 read 成功」という
  外部要因の状態変化が要り、`:503` の sha256 完全一致により受理されうる freeze は active 世代
  そのものに限られる。件数の出所は AST 走査であり、loader の caller を exact 固定する権威ある閉包は
  repo に実在しない。(c)(d) は先行 wave で閉じ今日も現物で成立する ((c) の private 化と負例 test、
  (d) の stub 無し genuine 正負 4 node)。残る library 非対称 (`verify_manifest` が選択 token を
  要求しない、`build_observations` の optional 引数、`_write_approved_manifest`) は production 到達
  0 件のため実装しない。**裁定待ち**: `_gate_check_core` の v2 fallback を (i) 現状維持で台帳へ
  記録するか、(ii) exact `LaunchValidatedFreeze` 必須へ縮めて D65 決定 (5) の不変条件を全分岐で
  成立させるか。(ii) は実装面のため Codex role=author と変異事前登録が要る。
  (e) s8c C06 予算群 (D1371)、(f) 起動証明書の実時間性 (D1241 が機構を禁じている)、
  (g) s8c production final claim 配線 (D1371) は残件のまま。
  **いずれも D1241 / D1313 の advisory / non-certifying 上限を解除しない。**
  base: 266e2f7fc4aa9502475d935dec5fb427a7ebc1a49114e11c5d36ef0b060bf522
