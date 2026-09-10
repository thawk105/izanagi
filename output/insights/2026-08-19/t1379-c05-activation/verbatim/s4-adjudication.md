# T-1379 段4 裁定

## ユーザー裁定 (2026-08-19)

段3 の両レンズが一致して指摘した P1 (schedule authority 構築不可能) について、
AskUserQuestion で確認した結果: **契約反転・`_MACHINE_EVALUATORS` 登録・DECIDER_VERSION
bump・凍結世代発行の 4 項目のみを本 wave で実装する。§5 master_seed 記入と
schedule.v1.json の commit は scope から除外し、T-1380 (権威の実体配線) 完了後の別 wave へ
裁定として返す。**

## 前提の更新 (実測、main 取り込み後)

- main は着手時 `a31832d9` から `c31c8fea` へ進行済み。fast-forward で取り込み済み。
- **T-1355 が先に DECIDER_VERSION v4 / g8 を消費して着地した** (合意時の想定と順序が逆転したが
  無競合で着地)。本 wave は次の未使用版 **v5** / 凍結世代 **g9** を使う。
- main 上の `_MACHINE_EVALUATORS` は既に `{1, 2, 4, 7, 9, 10, 11, 12}` (T-1355 が C07 を追加)。
  C05 (5) を追加すると `{1, 2, 4, 5, 7, 9, 10, 11, 12}` (9 個)。
- `worktree-dev-wave-t1353-c03-c08` (C03/C08) は引き続き **未着地**。
  `test_s8c_preregistration_predicates.py` の重複箇所を main 取り込み後に再実測した
  (詳細は下記)。
- レンズが指摘した `_load_s8c_schedule_authority` (p3:1555) は再確認の結果、
  C06 (budget) 向けの別スキーマ (`schedule_sha256`/`cells`/`limits`/`ledger_path`) であり、
  C05 の search-space/initial-state authority (`arms`/`workloads`/`role_contracts` 等) とは
  別物だった。ただし WORKLOADS が探索用で正式 H1/H2 と不一致という指摘自体は無関係に成立するため、
  P1 の結論 (今回は schedule artifact を commit しない) は変わらない。

## 所見の裁定 (real/refuted, 採否)

| # | 所見 (段3) | 判定 | 採否 |
|---|---|---|---|
| 1 | F393 後の検証手順「未 commit のまま `activation_report_at` で確認」は不成立 | REAL | 採用。親の段7 統合 commit 手順は「一時 commit → library で確認 → 必要なら reset --soft → 最終形へ組み直して 1 commit」とする (生死実験で実地検証済みの手順を踏襲) |
| 2 | P1: authority 構築不可能 | REAL | ユーザー裁定で対応済み (§5/artifact を scope 外へ) |
| 3 | 既存 snapshot (`:207-246`) の C05 期待値 | **REFUTED (再検証)** | 現在の期待値は既に `(EVIDENCE_UNDEFINED, "schedule-schema-absent")`。artifact を commit しない本 scope では `_evaluate_c05` も同じ値を返す (実装を読み確認済み)。**変更不要** |
| 4 | `test_legacy_contract_routes_machine_evaluators_to_undefined` との齟齬 | **REFUTED (再検証)** | このテストは `M.MACHINE_CHECKABLE_CONDITION_IDS` から対象を動的導出し、契約を人為的に全 False へ書き換えた legacy シナリオを検証する。`_evaluate_undefined` は `if number in _MACHINE_EVALUATORS:` を最初に評価するため、C05 registry 登録後はこの分岐が優先され、`elif number==5` には到達しない。**変更不要、コードの追加読解で反証** |
| 5 | C06 staged 件数 `len(...) == 7` → 8 | **REAL だが値が違う** | `test_current_contract_keeps_c06_staged_only:2993` の `len(M.MACHINE_CHECKABLE_CONDITION_IDS) == 8` を **`== 9`** へ (T-1355 の C07 登録で現在既に 8 のため) |
| 6 | 旧 bitflip test の収集消失 | REAL | 採用。`NON_MACHINE_CHECKABLE_NEGATIVE_CONTROL_CASES` が空になっても
  `test_c05_initial_state_hash_bitflip_is_single_shared_layer_failure` が収集され続ける形に直す (parametrize を専用の固定 tuple `(("nc_c05_initial_state_hash_bitflip", "C05"),)` に変更するなど) |
| 7 | t1353 との実ファイル衝突 (具体行番号) | REAL | 採用。symbol anchor 基準で編集 (下記) |
| 8 | file:line 精度 (`_evaluate_undefined` 終端 `:2659` 相当、`PredicateRegistry.evaluate_all` が正式名) | REAL | 実装子への参照を修正済み (本書に反映) |
| 9 | CLI/library 記述の不正確さ | REAL | worklog 記述で訂正 (bytes 不一致 = `evaluator-blob-mismatch`、evaluator 実行時例外 = `evaluator-exception`。原因は「未 commit の変更を旧 HEAD に対して検査した」手順側にあった) |
| 10 | 「実質再抽選」表現は過大 | REAL | brief 記述を訂正 (正しいリスクは同一 seed でも authority 変更で artifact bytes が再現不能になること) — ただし本 scope では artifact 自体を作らないため影響なし |
| 11 | mutation 設計 (`return consume_schedule(...)` → `return artifact`) は妥当 | REAL | 採用。置換回数を 1 と assert し、fixture が AST-only か runtime かを明示する |
| 12 | `SATISFIABLE_CONDITION_IDS` 変更不要 | 独立検証で確認 | 現状維持 (変更しない) |
| 13 (新規, 親の追加検証) | `_evaluate_undefined` の `elif number==5` は C05 登録後 dead code になる | REAL | **不採用 (削除しない)**。t1353 が同関数を大きく書き換え中でありconflict リスクを増やすだけで正しさに影響しない (到達不能なだけで誤動作しない)。段6 レビューで指摘されたら対応 |

## t1353-c03-c08 との重複 (main 取り込み後に再実測)

`git diff main worktree-dev-wave-t1353-c03-c08 -- orchestrator/tests/test_s8c_preregistration_predicates.py`
の hunk が触れる main 側の行範囲: 222-249, 253-261, 294-301, 550-743, 778-828, 828-990,
898-940, 940-1178, **2375-2412 (`test_satisfiable_predicate_requires_negative_control`)**,
2414-2421, 2448-2680, 2532-2556, **2990-2997 (`test_current_contract_keeps_c06_staged_only`)**。

実装子は行番号でなく次の symbol anchor で編集位置を特定すること。

- `NEGATIVE_CONTROL_CASES = {` 辞書リテラルの `}` 直前へ追記 (末尾行への 1 行追加は
  他 wave の追記と非衝突になりやすい)。
- `_negative_control_case` 内の既存 `if identifier == "nc_c12_...":` ブロックの直後に
  `if identifier == "nc_c05_...":` を追加。
- `test_satisfiable_predicate_requires_negative_control` 関数と
  `test_current_contract_keeps_c06_staged_only` 関数は **本文の値だけ** を変更し、
  関数のシグネチャ・前後の空行構造は変えない (t1353 が同じ関数を書き換えているため、
  無関係な整形変更は衝突面を広げる)。
- 段5 実装完了時点で t1353 が着地していれば、親が段6 直前に main を再取り込みし、
  実装子には再照準 fix を投げる。

## 変異事前登録 (B-057, DW-M01)

1. **契約反転を拒否**: `s8c_preregistration_evidence_contract.v1.json:227` の `machine_checkable`
   を `false` のままにする、または `_MACHINE_EVALUATORS` への `5: _evaluate_c05,` 登録を落とす。
   → `test_machine_checkable_contract_and_evaluator_registry_are_bijective` で reject。
   単一理由: 全単射不成立以外の赤を出さないことを実装子が確認する。
2. **到達性検査を弱める (段6 レビューA で範囲を修正、2026-08-19)**: 当初案は
   `required_calls` (:1666-1681) と `required_targets` (:1722-1733) の両方を対象にしたが、
   段6 レビューA が「新設 fixture (supervisor の `consume_schedule(...)` 呼出し自体を削除) は
   `required_targets` 層だけを検証しており、`required_calls` 層 (`consume_schedule` が
   `verify_schedule` を呼ぶことの検査) を弱める変異は fixture 側の到達不能で先にマスクされ
   SURVIVED になる」と実測で指摘 (DW-M02: 他層マスクの疑い)。よって**登録対象を
   `required_targets` (:1722-1733) の弱体化変異 1 件に限定する**。`required_calls` 層の
   検出力は今回の fixture では検証しない既知のギャップとし、worklog へ明記する
   (§6 前提条件 5 の consumer 内部呼び出し検査は entry (662) の scope で、本 wave は
   registry 登録が主目的のため)。→ `required_targets` 弱体化変異は新設 fixture の
   mutated 版が `UNSATISFIED`/`schedule-consumer-unreachable` にならなければ reject。
3. **DECIDER_VERSION を bump しない**: `s8c_preregistration.py:51` を v4 のまま残す。
   → g9 の `decider_version` フィールドと定数の不一致を検査する既存の凍結妥当性検査
   (`validate_condition_freeze_at` 系) で reject。

## 確定 scope (v2)

1. 契約 JSON: C05 `machine_checkable` false→true。
2. `_MACHINE_EVALUATORS` へ `5: _evaluate_c05,` 追加 (4 と 7 の間)。
3. `DECIDER_VERSION`: v4→v5。
4. メタテスト追随 (上表の該当項目)。
5. (親担当・段7) 凍結世代 g9 発行、統合 commit。§5 記入と schedule.v1.json commit は **含めない**。
