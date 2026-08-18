---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-18
wave: dev-wave-c05-schedule-consumer
seq: 1
title: 8c 条件 5 の schedule consumer を leaf として新設した — 依頼の 3 要求のうち評価器登録は凍結規約により不可分と判明し裁定へ返す (コード + テスト、branch worktree-dev-wave-c05-schedule-consumer、変異 matrix = baseline PASSED・9/9 KILLED・SURVIVED 0・MISMATCH 0)
---

## 本文

- 依頼は (i) consumer module の新設、(ii) `_evaluate_c05` の実装と `_MACHINE_EVALUATORS`
  への登録、(iii) 負の対照の追加で、契約 JSON の `machine_checkable` 反転と条件凍結 record の
  更新は scope 外と指定された。実測の結果 **(ii) の登録部分は scope 外の 2 件と不可分**と判明した。
  評価器の呼び分けは契約 JSON の `machine_checkable` が駆動しており登録表ではない。登録だけでも
  C05 の拒否理由が変わるため、凍結規約が要求する判定器版 bump と新世代 record の発行が必要になる。
  加えて登録単独では既存メタテスト 2 本が集合の完全一致で赤になる。したがって本 wave は
  (i)(iii) と `_evaluate_c05` 本体を納め、**登録・契約反転・世代発行を 1 つの原子的改訂単位**として
  {{D:c05-activation-is-atomic}} に記録し裁定へ返した。この分割は §5 記入規約
  「機構が満たされる時点で同じ改訂単位で記入する」とも整合する。
- 引数の scope 制約の理由「t822 wave が世代 7 を占有中」は **stale** だった (t822 は既に main へ
  着地済み)。ただし並行 wave が 8 本稼働し、うち 4 本が兄弟条件の consumer 実装であるため、
  世代の競合は実在する。**根拠が stale でも目的は妥当**と判定して制約を維持した。
- 敵対レビュー 2 本が独立に**循環 import** を blocker として指摘した。契約が要求する
  `run_trial -> verify_schedule` の配線は supervisor が新 module を import する向きであり、
  当初案のように新 module が supervisor から定数を取ると両立しない。権威を引数で受け取る
  依存性逆転へ変更し、key 集合を閉じて退化値を拒否する形にした。これで循環が消えると同時に、
  「実体が変わっても hash が変わらない」空洞と「全 cell が同じ値だから自明に通る」恒真性が
  同時に閉じた。詳細は {{D:c05-authority-inversion}}。
- **変異が検出力の欠落を 2 度暴いた。** 1 度目の probe で 9 件中 2 件が生存し、
  (a) `verify_schedule` が exact 検証と共有検証へ同じ権威を渡すため共有層が冗長、
  (b) `consume_schedule` が検証を通ることを守るテストが不在、と判明した。前者は外部供給の
  期待値を受け取る形へ、後者は seed 不一致の consume 検査の追加で塞いだ。cell 数検査は
  後段の全単射検査に隠れるため両層同時変異へ再照準した。**静的な敵対レビューだけでは
  この 3 件は閉じなかった。**
- 変異本走で `c05.m07` が 2 度とも計算資源側の終了コード (テスト結果ではないもの) で
  harness を fail-closed 停止させた。resume でも当該変異が最初に走って同じ失敗をしたため
  順序ではなく変異固有と切り分け、順番を入れ替えた独立 spec で回して完走させた。
  **再試行の前に毎回ログ本文を読み、rc を自前分類しなかった。**
- 段 5 / 段 6 の実装はすべて Codex `role=author` が書き、親は docs と裁定と実測だけを担った。
  子は pytest を実走できないため、焦点走・変異走は親が実測した。

## 次の一手差分

### 新規

- {{T:c05-activation-wave}} **P1・新規**: C05 の activation を 1 改訂単位で行う。
  契約 JSON の `machine_checkable` 反転、`_MACHINE_EVALUATORS` への登録、`DECIDER_VERSION` bump、
  凍結世代の発行、§5 `master_seed` の記入、schedule artifact の commit を**同一 commit**で行う。
  F393 に従い、契約を変えた commit を祖先に残さない形で組む。
- {{T:c05-production-wiring}} **P2・新規**: `run_trial -> load_schedule -> verify_schedule ->
  consume_schedule -> launch` を配線し、権威の実体 (`WORKLOADS` / `ROLE_FILES` /
  `ROLE_CONTRACTS` / `GATING_SPEC` / descriptor binding) を供給する。これが無い限り
  登録後の C05 は「consumer 到達不能」で止まる。
- {{T:schedule-index-namespace}} **P2・新規**: `schedule_index` が cell ordinal であることと、
  `s8b_oracle_manifest` の反復内 row 添字・observation `seq`・attempt 添字との対応付けを規約化する。
  契約が field 名を固定しているため改名できず、現状は docstring による明示に留めた。
- {{T:evaluator-static-only-limit}} **P3・新規**: 条件評価器が AST の名前と呼出し関係しか見ない
  弱さを族として扱う。C02・C04・C05 の 3 例で再現しており、独立 2 例の要件を満たす。
