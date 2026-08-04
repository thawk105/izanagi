# [T-409] 段 1 brief — EVOLVE-BLOCK hole の allowlist 化

基準: main 504ed6d / branch `worktree-wave-t409-evolve-hole-allowlist`。
本 wave は軽量版**ではない** (正しさ防壁に触る + 受理集合が変わる = DW-C00)。

## scope

trigger-gating 軸 hole の機械 pre-build gate を、**識別子 5 個の拒否リスト**から
**受理文法 (allowlist)** へ置き換える。`izanagi_gate_pass = <許可式>;` に一致しない
`implementation` は build 前に fails-closed で拒否する。sort 軸は scope 外 (D127 決定 (1)
の反対理由 2 = 合成が選択に化ける。sort は [T-410] が別途所有)。

## 確定済みユーザー裁定・既裁定

- [T-409] U1 (worklog (153)): 独立 wave で実装検討。**受理集合の縮小なので D96 手続が要る**
- **D127 決定 (1):** boolean-expression AST/DSL は「別 wave へ分離する」= 本 wave。却下ではない。
  反対理由 2 点が制約: (i) producer (role 定義) 契約と consumer だけ狭めると非互換、
  (ii) sort 軸では合成が事前 allowlist からの選択に化ける
- **D48 決定 2:** 構文契約は既に「要因 enum + コンパイル時定数のみ読取可・straight-line・
  副作用なし」。allowlist は**この既存契約を機械化するもの**であり、契約自体を新たに狭めない
- **D96:** 受理集合を変える改修は (1) 新 D の記録、(2) 境界テストの同時更新 を同じ変更単位で

## 実測した前提 (段 1、DW-O19 復元規律で実施)

- **A. 攻撃経路は real。** `include/ycsb.hh:102` の `makeProcedure(tx.pro_set_, ...)` は
  `RETRY:` (`:108`) の前で 1 回だけ。retry ループは `tx.pro_set_` を毎回舐め直す (`:117`)。
  `pro_set_` は `TxExecutor` member (`cc/silo/include/transaction.hh:37`) で `abort()` から届く。
  **訂正 (段 2 指摘、親が裏取り済):** `makeProcedure` は冒頭で `pro.clear()` する
  (`ycsb.hh:57`) ため、縮小は**同一論理トランザクションの retry 列内**に限られ、
  executor の後続トランザクションへは持ち越さない。攻撃の成立は変わらない
  (競合するトランザクションほど短くなって commit する = workload を黙って縮める) が、
  「恒久的」という初版の書き方は過大だった
- **B. hole は 1 行「置換」。** parser (`p3_autonomous_workload_trial.py:337`) は `\n`/`\r`
  不在しか見ないため `izanagi_gate_pass = true; pro_set_.pop_back();` が 1 物理行で通る
- **C. `axis_trigger_gating.py` は no-touch。** sha `47507d9b…c04c` が
  `output/s1-freeze/{known_axes,measurement}_freeze.json` に各 6 箇所 pin。両 JSON は
  `test_frozen_artifacts.py` の `FROZEN_MANIFEST` (23 件) で bytes 凍結
- **D. 訂正 (段 3 レンズ B 指摘、親が裏取り済)。** 初版は「pin は発火しない」と書いたが**過大**。
  正しくは「**テストが張られていないが、本番の検証経路では発火する**」。
  `s1_direct_comparison.load_verified_freeze` (`:119-131`) →
  `s1_measurement_freeze.verify_document` (`:387-408`) → `_verify_known_axes` が
  live source の sha を照合する。実測 (同ファイルへ 1 行足して全スイート = `5430 passed`) が
  示したのは**単体テストの穴**であって、pin の不在ではない。
  → no-touch 制約はより強い理由で維持。テストの穴は scope 外の real 所見として裁定へ
- **E. 正例は実在 (DW-O13)。** 受理済み `implementation` 26 件を成果物から回収。
  **訂正 (段 2 指摘):** 内訳は trigger 軸の代入式 **9 件** + trigger stock の説明文字列 1 件 +
  sort 軸 16 件であり、26 件すべてが trigger 正例ではない。trigger の 9 件は全て
  `izanagi_abort_reason_ == IzanagiAbortReason::kX` の `||` 連結で、全て `kUnset` 項を持つ。
  **新 gate に通すべきはこの 9 件だけ**で、残り 17 件を通すことを要求してはならない
- **F. DW-G01 生死確認。** libclang 14 は本ホストで import・`Index.create()` 成功
- **G. 既存の赤 1 件。** `test_ruleops.py::test_real_checkout_independent_maximum_package_and_runner_preflight`
  は main HEAD 504ed6d でも赤 ([T-407] 所有、非 UTF-8 blob)。本 wave の受入基準は
  「この 1 件以外に赤を増やさない」

## 不変条件

- `axis_trigger_gating.py` を編集しない (前提 C)。新 gate は別 module へ置き、
  執行側 `p3_s4_loop_trigger_gating.py` (非凍結) から参照する
- 前提 E の 26 件のうち trigger 軸の正例は**全て通る**こと。1 件でも落ちれば設計赤
- fail-closed: 文法に載らない入力は拒否。拒否理由に coder の式本文を載せない
  (既存 `_syntax_contract_reject_result` のリーク規律を継承)
- 規律 2: 性能のために文法を緩めない

## 判断が割れうる前提 (親の provisional 裁定 = 攻撃対象)

- **(P1) 実装方式 = 依存なしの字句+文法 recognizer。** libclang は使わない。
  理由: 受理言語が極小 (前提 E)、llvm-14 への新規依存は計算ノードで未検証、
  文字クラス prefilter で trigraph・行継続・コメント・エスケープを構造的に殺せる。
  **攻撃点:** 手書き字句解析が C++ の代替トークン (`or`/`bitor`) や digraph を取り逃すか
- **(P2) 拒否リストは残す (allowlist と併置)。** allowlist が真部分集合なので冗長だが、
  拒否理由の可読性と回帰検出のため残す。**攻撃点:** 二重管理でドリフトする
- **(P3) producer 側 (role 定義) も同じ文法へ更新する。** D127 反対理由 (i) への回答。
  **攻撃点:** role 定義を狭めると合成の自律性 (研究主張) を損なうか
- **(P4) scope は trigger 軸のみ。** **攻撃点:** hole 一般へ効かないなら T-409 の問題は残る

## 成果物影響 (DW-G05)

- 実装しない場合: `pro_set_` 級の変異が機械関所を素通しし、**certified 選択が
  「縮んだトランザクション」の throughput を根拠に選ばれうる**。受理集合は現状のまま広い
- 実装した場合: 受理集合は狭まる方向にのみ変わる。既存 26 正例の受理は不変 (不変条件)。
  凍結 bytes・proof chain・既存 certified 結果は不変

## 分割方針

- 段 2: codex read-only に file:line 粒度のプラン (文法定義・配線点・境界テスト・新 D 骨子)
- 段 3: 敵対相談 2 本 = レンズ A「文法の穴 (この文法を通る有害変異はあるか)」、
  レンズ B「受理集合と契約整合 (正例回帰・producer 契約・D96/D127 との整合)」
- 段 5: 実装子 1 本 (新 module + 配線 + テスト)。docs は親
