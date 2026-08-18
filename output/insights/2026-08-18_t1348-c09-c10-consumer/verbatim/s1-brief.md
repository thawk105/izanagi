# 段 1 brief — 8c 条件 C09 / C10 の consumer 実装

wave: worktree-dev-wave-t1348-c09-c10-consumer / 背景 job / 2026-08-18 18:05 JST 起点

## 1. 実測ベースライン (親が本 worktree HEAD=38f173cb で取得)

`M.get_registry().evaluate_all("HEAD", repo_root=".")`:

- C09 UNSATISFIED / `formal-acceptance-layer3-consumer-absent`
- C10 UNSATISFIED / `cross-binding-verifier-incomplete`
- 12 条件中 SATISFIED は 0 件 (この wave 後も 0 件のまま = 目標状態は SATISFIED ではない。下記 4 節)

AST probe (`trial_registry.assert_trial_registry_acceptance`):
- `assert_campaign_layer3_chain` 呼び出し: **なし**
- 文字列 `"no-build"`: **なし** / `"certifying"`: あり
- `verify_s8c_cross_binding` 呼び出し: **なし**

repo 全体 grep: `verify_s8c_cross_binding` / `read_and_verify_bytes` は production に **0 件**
(存在するのは評価器の述語文字列と predicates テストの合成 fixture のみ)。

## 2. scope

**やる:**
1. `orchestrator/campaign/trial_registry.py` の `assert_trial_registry_acceptance` を C09 の
   consumer にする。読み込んだ 6 report それぞれについて、build report なら
   `autonomous_trial_completeness.assert_campaign_layer3_chain` を実走し、
   no-build または chain 欠落の report を certify しない。
2. `orchestrator/campaign/autonomous_trial_completeness.py` に権威 verifier
   `verify_s8c_cross_binding` を新設し、参照された byte 列を読み直して
   supervisor(role_event) / provider / proposal / WAL / bench / Layer 3 の各 field を束縛する。
   acceptance が registry 受理より前にこれを呼ぶ。
3. 上記 2 つの production 配線に対する正例・負例テスト、および下記 5 節の pin 閉包更新。

**やらない (scope 外):**
- `s8c_preregistration_evidence_contract.v1.json` の編集 (評価器・契約は既に実装済み)
- `output/s8c-preregistration/condition-freeze.v1.g*.json` などの凍結 record の編集
- 評価器 `_evaluate_c09` / `_evaluate_c10` 本体の変更
- C01 / C04 / C12 など他条件の consumer 配線

## 3. 不変条件 (破ったら wave 失敗)

- **恒真ゲートを作らない。** 追加する assert は、wave 前の実 report 内容で発火しうる形でなければ
  ならない。「常に真になる」検査で C09/C10 を通してはならない (規律 2)。
- 評価器が要求する識別子・文字列は結果であって目的ではない。
  `"no-build"` / `verify_s8c_cross_binding` / `read_and_verify_bytes` を
  **未使用の literal やダミー関数として置くだけの実装は不採用**とする。
- fail-closed。cross-binding の入力が欠落・不整合なら受理せず `TrialRegistryError` で止める。
- acceptance は現在も構造的に `certifying: False` である
  (`test_acceptance_v2_has_no_certifying_issuance_branch` が pin)。この性質を反転させない。
- 既存の acceptance 経路のテストを弱めない。fixture を通すために production の検査を緩めない。

## 4. 成果物の形 (`DW-G05` 成果物影響)

- **目標状態**: C09 / C10 がともに
  `EVIDENCE_UNDEFINED` / `completion-proof-not-machine-checkable` になる。
  これは C02 / C11 と同じ「機械検査部分は通過、完遂証明は実走待ち」の終端であり、
  この枠組みで機械的に到達できる最良値である。SATISFIED を返す経路は評価器に存在しない
  (依頼文の「SATISFIED まで持っていく」はこの終端を指すものとして読み替えた。P1)。
- **実装しない場合の影響**: 8c 正式系列は前提条件 12 件のうち 2 件が未充足のまま実走できず、
  層3 材料レポートの検査は任意実行 CLI のままで、acceptance が発行する受領証は
  「proposal / raw response / provider envelope / build 成果物 / bench 結果と WAL の
  cross-binding が正式 proof chain として束縛されていない」状態を維持する
  (docs/phase3-8c-preregistration.md §6 条件 9・10 の本文)。

## 5. 変更面 (実アンカー表 — 親が実測した位置)

| path | anchor | 何が要るか |
|---|---|---|
| `orchestrator/campaign/trial_registry.py` | `assert_trial_registry_acceptance` (2557) | layer3 chain 実走・no-build 非 certify・cross-binding 呼び出し |
| `orchestrator/campaign/trial_registry.py` | receipt 構築 (2913 付近 `receipt_value = {`) | reason code 追加 / cross-binding 受領証 digest の束縛先 |
| `orchestrator/campaign/autonomous_trial_completeness.py` | `assert_campaign_layer3_chain` (2837) | 呼び出し規約 `(*, report, output_root)` |
| `orchestrator/campaign/autonomous_trial_completeness.py` | 新設 `verify_s8c_cross_binding` + `read_and_verify_bytes` | 12 field の byte 再読と束縛 |
| `orchestrator/campaign/autonomous_trial_completeness.py` | 既存 `_bound_regular_bytes` (444) / `_check_registered_proposal` (611) / `_check_registered_provider_artifacts` (647) | 再利用元 |
| `orchestrator/campaign/s8c_acceptance_receipt.py` | `SCHEMA_VERSION` (24) / `MANDATORY_NON_CERTIFYING_REASONS` (30) / `C02_ARM_BINDING_UNPROVEN` (33) / `_TOP_LEVEL_KEYS` (38) | 新 reason code と (必要なら) 新 field の受け皿 |
| `orchestrator/campaign/p3_autonomous_workload_trial.py` | layer3 呼び出し (2729) | producer 側の既存形。`do_build and cells` のときだけ呼ぶ |
| `orchestrator/tests/test_s8c_preregistration_predicates.py` | `test_current_repository_gap_reason_snapshot_requires_cross_wave_review` (139) | C09/C10 行の反転 |
| `orchestrator/tests/test_s8c_preregistration_invariant.py` | `MACHINE_CONTRACT_FUNCTION_CHECKS` (42) / `MACHINE_CONTRACT_FUNCTION_EXCLUSIONS` (87) | 下記 pin 移動 3 件 |
| `orchestrator/tests/test_trial_registry.py` | `_base_report` (360) `"do_build": False` / `"cells": []` | 既存 fixture は全部 no-build |

### pin 閉包 (機械的に必ず赤になる。取り残すと受入 1 本を捨てる)

`test_machine_contract_function_names_exist_and_checked_set_is_exact` は
checked / excluded を **完全一致**で pin する。実装後に分類が動くのは次の 3 件:

1. `("C09", "orchestrator/campaign/trial_registry.py", "assert_campaign_layer3_chain")`
   — `different-module-token` 除外 → trial_registry が名前を持つので **checked へ移動 (自動で赤)**
2. `("C10", "orchestrator/campaign/autonomous_trial_completeness.py", "verify_s8c_cross_binding")`
   — `declared-unimplemented-token` → 実装したので **checked へ移す (放置しても緑だが嘘になる)**
3. `("C10", "orchestrator/campaign/trial_registry.py", "verify_s8c_cross_binding")`
   — 同上

`classify` は declared-unimplemented pin を symbol 検査より先に見るため 2・3 は放置でも通る。
**放置は「宣言止まり」の再導入であり不採用**とする。3 件とも CHECKS へ移し、
EXCLUSIONS から落とす。

## 6. 攻撃対象の provisional 裁定 (親の暫定判断。段 3 で攻撃せよ)

- **(P1) 目標終端は `EVIDENCE_UNDEFINED / completion-proof-not-machine-checkable`。**
  依頼文の「SATISFIED」はこの終端の言い換えとして読む。評価器に SATISFIED を返す枝が無いことを
  親が実測済み (`_evaluate_c09` / `_evaluate_c10` の成功枝はいずれも
  `EVIDENCE_UNDEFINED` + `COMPLETION_PROOF_NOT_MACHINE_CHECKABLE`)。
- **(P2) C09 の「certify しない」は新 non-certifying reason code で表現する。**
  acceptance は既に無条件 `certifying: False` なので、「certify を止める」は
  受領証の `non_certifying_reason_codes` に内容由来の code を積む形が実装可能な唯一の意味を持つ。
  既存の `C02_ARM_BINDING_UNPROVEN` (`descriptor_proofs` が揃わないときだけ積む) が先例。
  **これだけでは恒真になりうる**ため、build report に対する
  `assert_campaign_layer3_chain` の**実走**を fail-closed の本体とし、reason code は補助とする。
- **(P3) `cross_binding_receipt_sha256` の置き場所は receipt top-level を第一候補とする。**
  `output/s8c-trial-registry/receipts/` に commit 済み receipt は 0 件であることを親が実測済み
  (`git ls-files output/s8c-trial-registry/` が空) なので、凍結 bytes を壊す心配はない。
  ただし `_TOP_LEVEL_KEYS` は exact 集合であり、schema v2 のまま key を足すか v3 へ上げるかは
  段 3 で攻撃してほしい。**契約 JSON の field path は評価器の検査対象ではない**
  (invariant テストは `reachable_from` の token と consumer entrypoint だけを分類する) ため、
  この置き場所の選択は C10 の充足判定を左右しない。
- **(P4) 既存 acceptance テストの fixture は全て `do_build: False` / `cells: []`。**
  C09 のゲートはこれらを壊さない形 (no-build は reason code を積むだけで受理は継続) にする。
  受理そのものを拒否する設計にすると既存テストが総崩れになり、scope が跳ね上がる。
  この読みが条件本文に対して甘すぎないかを段 3 で攻撃してほしい。
- **(P5) acceptance が layer3 に渡す `output_root` は report の `cells[].campaign_root` の
  親の親から導く** (producer 2720-2736 と同形)。build cell が 0 件なら chain 実走は起きない。
  この「build cell 0 件」経路が C09 の抜け道にならないかを段 3 で攻撃してほしい。

## 7. 並行 wave との干渉 (親が実測)

稼働中 3 本。`git diff --name-only main...<branch>` で確認済み。

- `worktree-dev-wave-t1333-t1310-workload-profile`: **本 wave と 3 file 重複** —
  `autonomous_trial_completeness.py` / `test_s8c_preregistration_predicates.py` /
  `test_trial_registry.py`。特に predicates テストの状態表 tripwire の **C01 行**を書き換えている
  (本 wave は C09/C10 行)。同一 hunk 内 8 行差なので land 時に競合しうる。
  t1333 側は `autonomous_trial_completeness.py` に触るが `verify_s8c_cross_binding` は新設しておらず、
  **本 wave の実装対象とは重複しない**ことを確認済み。
- `worktree-dev-wave-t1286-commit-receipt`: 40 file 超だが
  `trial_registry.py` / `autonomous_trial_completeness.py` は含まない。
- `worktree-dev-wave-t688-job-kill-evidence-r2`: main との差分 0 file。

対応: 段 6 の受入直前に local main を再取り込みし、状態表 tripwire の競合はその時点で解消する。

## 8. 分割方針

軽量版ではなく段 2・3 を実施する (`DW-C00`: 正しさ防壁に触り、受理集合が変わる)。
- 段 2: read-only codex 1 本で file:line プラン起草
- 段 3: 敵対 2 本 (レンズ A = 恒真ゲート・reward hack、レンズ B = pin 閉包・既存テスト破壊)
- 段 5: 実装子 1 本 (2 file の相互依存が強く分割すると往復が増える)
- 段 6: 敵対レビュー 2 本 + fix + 変異 matrix + 受入全走

## 9. 受入・実測環境

- テスト実行は本 worktree 内で `python3 tools/run_tests.py` (相対・素の名前ちょうど)。
- 焦点走には変更 production file の検査側を含める:
  `test_trial_registry.py` / `test_autonomous_trial_completeness.py` /
  `test_s8c_preregistration_predicates.py` / `test_s8c_preregistration_invariant.py` /
  `test_layer3_report.py` / `test_p3_autonomous_workload_trial.py`。
- 受入全走は背景投入し、lease を `tools/dev_wave_wait.py acceptance` で claim してから投げる。
