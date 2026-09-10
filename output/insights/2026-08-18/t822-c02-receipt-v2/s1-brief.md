# 段 1 brief — [T-822] (ii) 後段: C02 機械検査化 + receipt v2 + 実名整備

## 0. 確定済みユーザー裁定 (本 wave の scope 命令)

証拠契約 C02 を機械検査可能にするための receipt v2 と `accept_trial` 実名の整備 (問 3 側) を行い、
C02 を評価器 table へ載せて `certifying=false` の必須理由を外せる状態にする。(i) は [T-1310] 待ちで
scope 外。恒真な保証を作らない — 負の対照を同じ land で足す。実装面は Codex author (D95)。

## 1. 親が実測した前提 (段 1 前・main a160f4aa)

- HEAD の 12 条件: C02=`EVIDENCE_UNDEFINED/arm-binding-declared-only`、
  C09=`UNSATISFIED/formal-acceptance-layer3-consumer-absent`、
  C10=`UNSATISFIED/cross-binding-verifier-incomplete`、C11 のみ `completion-proof-not-machine-checkable`。
- `accept_trial` は `trial_registry.py` に**存在しない**。実名は `assert_trial_registry_acceptance`
  (`trial_registry.py:2556`)。名は evaluator の literal (`s8c_preregistration_evidence.py:1490,1532`)
  **と contract JSON の両方**にある (C02 entrypoints/reachable_from、C09/C10 の field_paths も)。
- **実名へ直しても C09/C10 の判定は 1 bit も変わらない。** 実測: `assert_campaign_layer3_chain` と
  `verify_s8c_cross_binding` は `trial_registry.py` に 0 回出現。C09 は同じ理由で UNSATISFIED のまま、
  C10 は verifier 側で先に落ちて acceptance 検査へ到達しない。受理集合は広がらない。
- 実在する arm 機構 (T-1311): `bind_trial_arm:1220`、`assert_issued_trial_arm_execution:1258`、
  `assert_rederived_trial_arm_execution:1290`。acceptance の直接 call に
  `assert_execution_digest_chain` / `validate_execution_input_descriptor` /
  `_expected_registered_arm_execution_record` が実在する。C02 の gate 入力は実在する (`DW-O13` 充足)。
- `SATISFIABLE_CONDITION_IDS = frozenset()` で、6 評価器の終端はすべて
  `EVIDENCE_UNDEFINED/completion-proof-not-machine-checkable`。充足を返す経路は 1 本も無い。
- 凍結 pin 閉包: contract bytes は `evidence_contract_sha256` (domain 分離 hash) 経由で
  `condition-freeze.v1.g1..g5.json` の `protected_sha256` に入る。発行器は
  `s8c_preregistration.prepare_revision` (`ruling_reference` = `D<n>` 必須、
  `protected_sha256` 不変なら `spurious-revision` で拒否)。`MAX_GENERATIONS=1024` で g6 に余裕あり。
- receipt 側 pin: `MANDATORY_NON_CERTIFYING_REASONS`(`s8c_acceptance_receipt.py:25-28`)、
  producer(`trial_registry.py:2901-2924`)、および `test_reflux_originless_compatibility.py` の凍結 golden
  `_PRE_WAVE_ORIGINLESS_BASELINE`(:239) が `schema_version`・key 集合・2 語を exact に pin する。
- `output/s8c-trial-registry/` は**不在**。正式 receipt の凍結 bytes は 1 件も無い (`DW-O10` は
  fixture 経路のみ)。producer が書く種類 = `receipts/<manifest_sha>.json`・`registry.jsonl`・`lifecycle.jsonl`。

## 2. 不変条件 (破ったら stop)

- 受理集合を 1 bit も広げない。`test_candidate_is_not_effective_and_has_zero_satisfied_predicates`
  は緑のまま。C02 評価器の終端も他 6 本と同じ非充足理由にする。
- `certifying` は v2 でも構造的に `False`。`t468-approval-authority-absent` は必須のまま。
- 既存テストの期待値を反転・緩和・skip・削除しない。golden を「合わせるため」に書き換えない。
- 恒真禁止: v2 が `c02-arm-binding-unproven` を落とせる分岐には、落とせない負の対照を同じ land で置く。

## 3. 成果物の形

- U1 契約・評価器: C02 を `machine_checkable: true` + `_evaluate_c02` 新設、C02/C09/C10 の
  `accept_trial` を実名へ、`DECIDER_VERSION` を `s8c-decider/v3` へ bump。
  **新設メタ検査** = 契約が名指す関数名 (entrypoints と declared path 上の reachable_from hop) が
  当該 module の AST に実在することを要求する。純増検出力 = 問 3 型 (契約と実装の名前乖離) の再発検知。
  既存被覆を性質で検索した結果、この性質を検査する test は repo に **0 件**。
- U2 receipt v2: 新 `schema_version` と trial ごとの arm 実行束縛 field を足し、必須理由から
  `c02-arm-binding-unproven` を落とせる条件を「受領証自身の bytes 証拠が verify したときだけ」にする。
  producer を v2 発行へ。負の対照 3 種 (同一 holdout の 2 arm が同 digest / 束縛 field と report bytes
  の不一致 / 束縛 field 無しで理由だけ落とす) を同 land で足す。
- U3 凍結・docs (親): `docs/phase3-8c-preregistration.md` の §6 条件 2・衝突 (d)・「現在地」を実測へ更新、
  `prepare_revision` で g6 を発行、decisions/worklog fragment。

## 4. 攻撃対象の provisional 裁定 (段 3 はここを狙え)

- **(P1)** receipt v2 は v1 を残す additive schema とし、v1 の originless golden を壊さない。
- **(P2)** 必須理由を落とす根拠は**受領証自身の byte 証拠**であり、事前登録判定器の C02 充足ではない
  (充足経路は存在しないので、判定器に依存させると恒久に発火しない条件になる)。
- **(P3)** 凍結世代は本 wave で g6 を 1 回だけ発行し、契約 bytes の変更 3 件をまとめる。
- **(P4)** C02 評価器は静的 consumer 到達可能性だけを見る。実走 bytes の証明は receipt 層が担う。
- **(P5)** 実名整備は C02/C09/C10 の 3 条件すべてで行う (C09 だけ直すと同型の穴が残る)。
- **(P6)** `DW-G04` の発火条件: v2 の理由落とし分岐は fixture repo 上の originless bundle で
  実 producer 経路として発火する。正式 6 cell は [T-1310] 待ちで本 wave の発火条件ではない。

## 5. 成果物影響 (`DW-G05`)

実装しない場合: receipt は arm authority が実装済みでも `c02-arm-binding-unproven` を恒久に掲げ続け、
証拠契約は実装に無い関数名を名指ししたまま (i) 完了後も自動追随しない。certified 選択の値と
proof 参照は本 wave では 1 件も変わらない — 変わるのは受領証が掲げる非認証理由の集合と、
判定器が C02 を dispatch するか否かである。

## 6. 並列分割と環境

- U1 所有: `s8c_preregistration_evidence.py`、`s8c_preregistration_evidence_contract.v1.json`、
  `s8c_preregistration.py`、`test_s8c_preregistration_{predicates,core,invariant}.py`。
- U2 所有: `s8c_acceptance_receipt.py`、`trial_registry.py`、`test_trial_registry.py`、
  `test_reflux_originless_compatibility.py`、新規 receipt v2 test file (自走 harness 必須)。
- 所有は素集合。U3 は U1/U2 統合後に親が逐次実行 (g6 の hash が両者の最終 bytes に依存するため)。
- 実測環境: Pegasus login node。焦点走は bounded local、受入は `python3 tools/run_tests.py` を
  記録 commit 込みの最終 tip で 1 回。
