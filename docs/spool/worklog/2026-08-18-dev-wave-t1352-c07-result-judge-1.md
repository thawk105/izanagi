---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-18
wave: dev-wave-t1352-c07-result-judge
seq: 1
title: 8c 条件 7 の consumer (result judge) と静的 evaluator を新設する (コード + テスト、branch worktree-dev-wave-t1352-c07-result-judge)
---

## 本文

- **command 引数どうしが両立しないことを段 1 前の実測で検出した。** 依頼は
  「`_MACHINE_EVALUATORS` へ `_evaluate_c07` を登録する」と「証拠契約 JSON の
  `machine_checkable` は絶対に反転しない」を同時に求めていたが、この 2 つは成立しない。
  worktree で実編集・即時復元して測った結果、登録を入れるだけで契約由来の全単射検査
  2 件 (`test_machine_checkable_contract_and_evaluator_registry_are_bijective` と
  `test_satisfiable_predicate_requires_negative_control`) が evaluator の中身によらず赤になる。
  反転側も不可能で、契約 C07 の `reachable_from` にある `accept_trial` は repo に実在せず
  (C09 は `assert_trial_registry_acceptance` へ改名済み)、
  `test_machine_contract_rejects_prewave_accept_trial_name` がその不在を pin している。
  よって「反転しない」という指示が正しく、譲るのは「登録」の側と裁定した ({{D:c07-consumer-before-activation}})。
- **親の初回実測は範囲を誤っていた。** 段 3 の敵対レンズが独立に検出した。親の probe は
  `_negative_control_case` に C07 分岐を作らずに辞書だけへ追加したため、4 赤のうち 1 件は
  helper の AssertionError で落ちており C07 の判定に帰属できない。結論を支えるのは全単射検査
  2 件だけである。gap 台帳 snapshot は設計上 cross-wave review で更新する台帳であり blocker ではない。
  注入不全の赤を kill と数えない規律が要る (F33 の再発として記録)。
- 敵対レビュー 2 本が挙げた must-fix のうち、次を実装で閉じた。いずれも「謳うだけで発火しない保証」
  を防ぐもので、規律 2 の直接の適用である。
  - `verify_floor_bytes` を呼ばずに `judge` → `publish_result_table` を実行できた
    (検証が publish の必須前提でなかった) → 床値を含まない receipt を必須入力にした
  - observation が `correctness_gate_passed=True` を自称するだけで gate 通過と認められた
    → raw 値へ束縛した digest の再計算照合を要求した。信頼根そのものは scope 外と docstring に明記
  - `manifest["source_binding"]` の**欠落**が一致扱いになり、観測後の閾値差し替えが通った
    → 欠落・不正を判定不能へ倒した
  - holdout 集合が空のとき `all()` の空真値で条件が成立になった → 空入力は 3 条件とも判定不能に固定
  - publish の rollback 失敗を握り潰し部分表が残りえた → transaction directory と完了 marker で原子化
  - `_evaluate_c07` が「戻り値を未使用変数へ代入するだけ」でも消費済みと認定した
    → 関数内の到達使用まで見る検査に替え、宣言 path 上の decoy を拒否するテストを足した
- 親が実測して確定した権威: ratified 世代 document は top-level に `floor_protocol` と
  `floor_source` の 2 つの床 artifact、`env_tag`、`frozen_at_head` を持つ。実装が持っていた
  measurement head の推測 fallback 連鎖を消し、この権威だけを使う形にした
  ({{D:floor-provenance-not-judge-input}})。
- 期待 cell 集合を生成行から導出する形は恒真になるため、独立引数として受け取る形に固定した
  ({{D:predeclared-cell-set-must-be-independent}})。
- **本 wave は C07 を発効させない。** `_evaluate_c07` は production の `evaluate_all` から到達せず、
  C07 は `floor-judge-contract-undefined` のままである。certified 選択も台帳行も増えない。
  本 wave の値は「束ね wave が 1 手で反転できる形」ではなく「反転に何が足りないかを確定させた形」
  と、恒真でない判定器を用意したことにある。
- **ユーザー裁定へ返す事項**: 束ね wave の「1 手反転」は成立しない。反転には
  (a) 契約 C07 の入口名を実在する acceptance 入口へ是正、(b) `MACHINE_CONTRACT_FUNCTION_CHECKS`
  への C07 mapping 追加、(c) 新しい条件凍結世代の発行、の 3 つが同時に要る。
  欠落を exclusion pin で隠さない。あわせて、公式性能表を消費する acceptance 配線
  (現行 receipt は構造的に `certifying: false`)、実走層 (schedule / master seed /
  attempt registry / correctness gate / observation producer)、§5 の 8 欄記入も本 wave の scope 外である。
- **段 8 の自己改善候補 3 件は dev-wave docs の予算満杯のため実装せずユーザー裁定へ返す。**
  command 入口は 9492 / 9500 bytes で空きが 8 bytes しかなく、reference 3 層も満杯である。
  (a) `DW-S01` の段 1 前実測に「command 引数どうしの両立不能を測る」観点を明示する
  (本 wave で実際に発火した)。(b) `DW-M04` へ「注入不全の赤を kill と数えない」を
  対称義務として明示する (F33 再発として failures には記録済み)。
  (c) `DW-O01` へ「codex 子の再投入は prompt の**内容**を変えないと job-id が同一になり
  既存受領証を上書きできず rc=2 で止まる」「review 子は既定の CLI 報告トークン上限
  1,000,000 で SIGTERM し出力 0 bytes になりうる」を追記する (どちらも本 wave で実測)。
- 子の工数: plan 1 本、敵対相談 2 本、実装 2 本、敵対レビュー 2 本 (1 本は CLI 報告トークン上限で
  2 回失敗し、上限を上げて 3 回目で成功)、fix 2 本。

## 次の一手差分

### 更新

- [T-1352] **P1・一部完了**: 8c 条件 7 の consumer (`orchestrator/campaign/s8c_result_judge.py`) と
  静的 evaluator (`_evaluate_c07`) を新設した。残件は (a) 証拠契約の `machine_checkable` 反転と
  `_MACHINE_EVALUATORS` 登録・negative control 登録・条件凍結の新世代発行を束ね wave で 1 回に行う、
  (b) 最終判定層の現用実装から旧条件 3 と scale gate を撤去する、の 2 つ。
  base: d7d46332b6fe35eecbb4f354d86bb6079b7d67f25eb3f0e989b474ea9ea20634
