---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-19
wave: dev-wave-t8c-precondition-audit
seq: 1
title: 段8c正式系列の起動条件(§6 前提条件1〜12)を機械証拠で棚卸しした(read-only診断、branch worktree-dev-wave-t8c-precondition-audit)
---

## 本文

- entry (702) が「T-1391/T-1352 land 後の 8c 正式系列着手条件の確認が研究トラックへ戻る唯一の
  糸口」と記した確認を実施した。判定器は `orchestrator/campaign/s8c_preregistration.py` /
  `s8c_preregistration_evidence.py`。**CLI (`check` subcommand) は 12 条件全部を
  `evaluator-exception` へ潰すため使わず、library 経路
  (`s8c_preregistration_evidence.get_registry().evaluate_all("HEAD", repo_root=...)`) で
  直接実測した** ([[judge-diagnostics-via-library-not-cli]] の既知の罠を再現・再確認)。
- **結論: commit `050b0648` (現 main) 時点で 12 条件すべて未充足。ただし内訳は一様でない。**
  - **C02/C04/C07/C09/C10/C11/C12 (7 条件)**: 評価器内の全構造・到達性チェックが通過し、
    各評価器自身の終端 (`EVIDENCE_UNDEFINED` / `completion-proof-not-machine-checkable`) に
    到達済み。これは「ほぼ満足」ではない — `s8c_preregistration_evidence.py` を
    `PredicateStatus.SATISFIED` で grep すると `is_satisfied()` の比較式 1 箇所以外にヒットが
    無い。**12 個の `_evaluate_c*` 関数のどれ一つとして SATISFIED を構築するコード経路を
    持たない。** `SATISFIABLE_CONDITION_IDS` の空集合 (evidence.py:3070) はその上の二重の
    安全弁であり、今のコードでは発火する機会自体が無い。
  - **C01**: `_evaluate_c01` (evidence.py:1931-1962) の直接 probe で、5 段の下位検査のうち
    4 段 (workload_supervisor 存在・sinks 到達・`_campaign_for`/`_perf_for`/`_descriptor_for`
    が `{1_000_000,48}` のリテラルを含む・`main→run_trial→sinks` 到達) が全部通過することを
    確認した (T-1391 land の効果を直接確認)。**唯一の残り: `load_ratified_freeze()` 戻り値の
    `.sha256` 属性は到達可能に使われているが (`p3_autonomous_workload_trial.py:4212`)、
    `.holdouts` 属性は main からの到達可能な call graph 内で 1 箇所も使われていない。**
  - **C05**: 最初の分岐 (evidence.py:2081-2086) で即 block。
    `output/s8c-preregistration/schedule.v1.json` が不在 (実測)。consumer module
    `orchestrator/campaign/s8c_schedule.py` は実在し関数 shape も揃っているため、artifact の
    生成 (master_seed 確定を含む) だけが残る。T-1379 commit 本文が既にこれを「T-1380 待ち」と
    明記しており (D546)、既存トラッキングと一致する。
  - **C06**: 本番 dispatch は `_evaluate_undefined` の number==6 分岐が固定 reason
    (`budget-consumer-contract-undefined`) を返すだけで、実装は検査しない。**しかし staged
    評価器 `_evaluate_c06`/`_c06_field_path_verdict` (evidence.py:3358-3477) を現 HEAD の
    `orchestrator/campaign/s8c_budget.py` に対して直接実行すると、他の 7 条件と同じ終端
    (`completion-proof-not-machine-checkable`) まで到達した。** 契約 JSON
    (`machine_checkable=false`) と `_MACHINE_EVALUATORS` 未登録 (`_STAGED_EVALUATORS` のまま)
    だけが残るギャップで、専用 test (`test_current_contract_keeps_c06_staged_only` ほか、
    test_s8c_preregistration_predicates.py:3666-3722) が意図的 pin として存在する。
    T-1355 (C07 昇格)・T-1379 (C05 昇格) と同型の昇格手順が D529 で定義済み。
  - **C03/C08**: `trial_registry.py` に対する AST 構造検査 (関数 shape・到達性・field 名) は
    両条件とも終端まで通過するが、`output/s8c-preregistration/trial-manifest.v1.json` と
    `prereg-effective-binding.v1.json` は共に不在 (実測)。C06 と異なり staged evaluator の
    別置き機構は無く、`_evaluate_undefined` の number in {3,8} 分岐から直接呼ばれている。
    doc (§6 衝突(c)) は「実行 registry が依然として単一識別子を要求し二段束縛を消費しない」
    という、AST 検査ではカバーしきれない可能性のある実行時ギャップを指摘しており、この指摘が
    現行コードに対しても有効かは未検証。
- **doc staleness (副次的発見)**: T-1379 (今日 10:42, commit `9f89da3d`, C05 を
  machine_checkable 昇格・`DECIDER_VERSION` を v5・generation 9) は
  `docs/phase3-8c-preregistration.md` 本文を 1 行も変更していない
  (`git show 9f89da3d -- docs/phase3-8c-preregistration.md` が空 diff)。同文書「現在地」節は
  「8 条件・4 条件」という T-1355 時点 (第 8 世代) の記述のまま。あわせて C12 について、同文書
  §6 衝突(e) は「2026-08-17 時点で両 consumer が実在するが 8c 起動経路から到達が無い」と記すが、
  今回の probe では `environment_contract.lookup`/`execution_guard.attest_and_build_receipt`/
  `allocation_consumer` の到達をすべて確認した。どの後続 commit が到達性を作ったかは本 wave では
  未追跡 (scope 外)。
- §5 (実走前に埋める欄、doc 本文) は `check --json` の JSON 出力で 9 欄中「検定 4 点」のみ
  FILLED、残り 8 欄 UNFILLED (この部分の CLI 出力は reason_code 要約ではなく FILLED/UNFILLED
  状態そのものなので信頼できる)。
- 実装 (未充足条件の解消) は本 wave の scope 外。次の一手差分に新規 4 件を追加した。

## 次の一手差分

### 新規

- {{T:c01-ratified-holdouts-consumption}} **P1・新規**: 条件 1 (C01) の残存未充足サブ条件を
  解消する。`orchestrator/campaign/p3_autonomous_workload_trial.py` の `main→run_trial` 到達
  範囲内で、`load_ratified_freeze()` の戻り値 (`s8b_ratified_freeze.py`) の `.holdouts` 属性を
  到達可能に消費する処理を追加する (`.sha256` は既に 4212 行で到達済み)。根拠:
  `orchestrator/campaign/s8c_preregistration_evidence.py:1947-1957`。
- {{T:c06-budget-machine-checkable-promotion}} **P1・新規**: 条件 6 (budget consumer) を
  machine_checkable へ昇格する。`orchestrator/campaign/s8c_budget.py` は staged 評価器
  (`_evaluate_c06`/`_c06_field_path_verdict`, evidence.py:3358-3477) の全構造検査を現 HEAD で
  既に通過することを直接実行で確認済み。手順は D529 (契約 JSON 反転・`_MACHINE_EVALUATORS`
  登録・`DECIDER_VERSION` bump・新世代 condition-freeze record を不可分の 1 commit) に従い、
  T-1355/T-1379 と同型。`test_current_contract_keeps_c06_staged_only`
  (test_s8c_preregistration_predicates.py:3666-3671) の期待値更新を伴う。
- {{T:c03-c08-manifest-binding-readiness}} **P2・新規**: 条件 3/8 (二段束縛) の昇格可否を調査
  する。`trial_registry.py` に対する AST 構造検査は両条件とも終端まで通過するが、doc §6 衝突(c)
  が指摘する「実行 registry は単一識別子のまま」という実行時ギャップが AST 検査でカバーされて
  いるかを精査する。加えて `output/s8c-preregistration/trial-manifest.v1.json` /
  `prereg-effective-binding.v1.json` の実体 artifact 生成が要る (C06 と異なり staged evaluator
  基盤が無いため、まず調査から)。
- {{T:s8c-prereg-doc-narrative-sync}} **P3・新規**: `docs/phase3-8c-preregistration.md` の
  「現在地」節を T-1379 後 (9 条件 machine_checkable・generation 9・v5) の状態へ更新する。
  あわせて C12 到達可能性 (§6 衝突(e)) の 2026-08-17 時点の記述を現状に合わせて見直す。
  凍結対象 (本ブロック相当か) は改訂手続きの適用要否とあわせて確認する。
