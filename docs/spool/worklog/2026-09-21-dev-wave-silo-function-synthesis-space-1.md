---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-21
wave: dev-wave-silo-function-synthesis-space
seq: 1
title: Silo の待機と lock 競合応答を関数単位で合成する軸 silo-function-policy を設計し、3 レンズの条件付き採用で固定した — 方策だけを LLM に開き、受理する C++ を型付きの部分言語に、状態を worker 内の 1 個に閉じる (docs のみ、branch worktree-dev-wave-silo-function-synthesis-space)
---

## 本文

- **依頼と処理の流れ。** 依頼はユーザー直接の設計 wave で、台帳 ID は未起票 (主題 slug)。実験の計算は投げない。次の順で処理した。
  1. 段 1 brief
  2. 段 2 codex plan
  3. 段 3 codex consult 2 本 + auditor role 1 本
  4. 段 4 裁定
  5. insight と decisions fragment
  6. 焦点再レビュー 3 巡 (1 巡目 = codex review + auditor、2・3 巡目 = codex focus)
  7. 記録
- 実装面の差分はゼロ (D95 の docs-only)。変異 matrix は免除、受入全走は実施する。設計判断は {{D:silo-function-policy-axis}}、一次資料は insight `output/insights/2026-09-21/silo-function-synthesis-space/` (README と `verbatim/`)。
- **使ったユーザー裁定。** VLDB 方針の裁定の控え (repo 外 `dev-wave-jobs/rulings-inbox/2026-09-21-vldb-direction-verdicts.md`) の項 3 と項 4。
  - 項 3: 関数単位の空間を開く。正しさゲートは不変。
  - 項 4: 1 タスクの計算が 2 node 時間以上なら事前確認。
  - wave 開始後に inbox へ入った更新 (/rulings 第 30 回) は本題に触れない。
- **親の暫定裁定で覆ったもの。**
  - P4 (CC ヘッダの include より前に領域を置いて封じ込める): 不成立。最初の CC include で `std::atomic` と CC の大域が同時に見える。
  - P2 (構成上、直列化可能性を壊せない): 撤回。自由 C++ の未定義動作を無視していた。
  - P6 (C++ 本文を共通にすれば同一空間比較): 修正。比較 A (同じ IR) と比較 B (空間拡張) に分けた。
  - P5 (観測と状態): 草稿が txn 内へ縮めた後、状態の射程の択一で worker 内の txn 間に決めた。
    - B の推奨を採った。A と auditor は txn 内を支持した。
    - 根拠は、txn をまたぐ負荷追従を表現するためである。
- **棄却・見送り。**
  - 型 10 (no-wait の wait 化) による上限付き wait の一律拒否: refuted。
  - 式中の `TRACE` による verify 判別: 既存 diff-of-diffs が捕まえるので部分 refuted。
  - 次の 4 つは、発火条件つきで見送った。lock 方策は既定で「verify 中の発火証拠なし」と表示する。
    - 候補ごとの sanitizer
    - 候補ごとの TRACE 計数と PIN 前進
    - 新 X 理由 `lock-held-at-abort`
    - per-worker commit 分布の記録
- **焦点再レビュー。**
  - 1 巡目: codex は NO-GO (must-fix 8)、auditor は条件付き採用を維持 (must-fix 2)。主な指摘は bool 昇格による signed 算術、自己初期化、代替綴り、hole 境界、成功通知の検査、LLM×IR の経路、帰属。
  - 2 巡目: NO-GO (must-fix 2)。`/ %` の型規則と、constexpr の記憶域・文法の未確定が指摘された。
  - 3 巡目: 2 巡目の 5 件は全て closed、新たに must-fix 1 (部分式の代入による順序なし書込み)。
  - DW-O16 の 3 巡上限により、親が裁定して閉じた。
    - 処置: 代入を独立した文に限る。
    - 根拠: 呼出しどうしは不定順序であり、UB にならないことを親が検算した。
    - 記録: `verbatim/s7-focus-ruling-3.md`。
- **工数。**
  - codex (gpt-6-astra / medium): 6 本・71 call・2,142 秒。
    - plan 17 call 605 秒
    - consult A 9 call 310 秒
    - consult B 10 call 268 秒
    - review 16 call 456 秒
    - focus 2 巡目 13 call 331 秒
    - focus 3 巡目 6 call 172 秒
  - auditor role (Claude subagent) 2 本: 17 tool call 452 秒、10 tool call 311 秒。
  - 親の計算投入なし。wave の壁時計は、開始 gate 21:37 JST (`startup-gate.log`) から記録 commit まで。
- 受入全走の結果と land の結果は本 entry に書けない (記録 commit の後に走るため)。

## 次の一手差分

### 新規

- {{T:silo-policy-onboarding-docs}} **P2・新規 (docs、C 段の前)**: `docs/axis-onboarding.md` §4 の表に第 3 列 (関数群・複数 hook・状態の軸) を足し、段階 E の planner-v4 再利用にこの軸の例外を合わせる。
  - 案は insight `output/insights/2026-09-21/silo-function-synthesis-space/README.md` §8。
  - {{D:silo-function-policy-axis}} の実装着手前の必須条件である。
- {{T:silo-policy-stage-c}} **P1・新規 (Codex author、C 段、計算は投入前にユーザー確認)**: {{D:silo-function-policy-axis}} の必須条件に従い、段階 C を実装・実測する。
  - 実装: 骨格 patch、api header、型付きの構文検査と単独 TU compile。
  - 実測: probe build の焦点試験 (3 hook)、既存 3 負例の軸 ON 積み直し (2 方策)、機構の変異、検査段ごとの自己試験と UBSan harness 1 回、手書き方策の生死確認。
  - 前提は onboarding docs の項の land。
  - 投入前にタスク合計の node 時間を示してユーザー確認を取る (設計時の換算は 2.41〜4.12 node 時間)。
