## 実装した内容

- (c): [s8b_oracle_manifest.py:818](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2067-bcd-selection-closure/orchestrator/campaign/s8b_oracle_manifest.py:818) で 3 API を private 化し、`:1245` の内部 caller も追随させました。本体・docstring・serializer・例外・引数は不変です。
- (c): [test_s8b_oracle_manifest.py:1252](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2067-bcd-selection-closure/orchestrator/tests/test_s8b_oracle_manifest.py:1252) に旧 3 属性を拒否する parametrize 負例を追加しました。
- (d): [test_s8b_ratified_verify.py:854](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2067-bcd-selection-closure/orchestrator/tests/test_s8b_ratified_verify.py:854) に genuine earlier run helper を追加しました。実 admission API と inspector を使い、result/manifest/journal と admission 証拠だけを追記します。certificate は作りません。
- helper は selected artifact の全 bytes と既存 admission file を検査し、ledger は既存 prefix を保つことを固定します。resume 側は実 claim の `entry_kind=resume` と実 marker も確認します。
- (d): 実 loader と実 callee を通す launch/consumer の正負 4 test を `:1027–1080` に追加しました。既存 stub 2 test は HEAD と完全一致しています。

## 改名した caller の全列挙

実測 25 箇所、漏れ・余りなしです。`_build_manifest_from_ratified` の test caller は 0 件です。

- [test_s8b_oracle_manifest.py:196](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2067-bcd-selection-closure/orchestrator/tests/test_s8b_oracle_manifest.py:196)
  - `_build_manifest`: 196, 424, 469, 571, 607, 657, 858, 1591, 1807
  - `_write_manifest`: 402, 410, 443, 489, 528, 551, 630, 780, 801, 1607, 1848
- [test_s8b_oracle_report.py:268](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2067-bcd-selection-closure/orchestrator/tests/test_s8b_oracle_report.py:268)
  - `_build_manifest`: 268, 391
  - `_write_manifest`: 402
- [test_s8b_oracle_driver.py:2336](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2067-bcd-selection-closure/orchestrator/tests/test_s8b_oracle_driver.py:2336)
  - `_build_manifest`: 2336
  - `_write_manifest`: 2347

## 新規 test node の一覧

5 test 関数、parametrize 展開後は 7 concrete node です。

- `test_s8b_oracle_manifest.py::test_ungated_manifest_apis_are_not_public[build_manifest]`
- `test_s8b_oracle_manifest.py::test_ungated_manifest_apis_are_not_public[build_manifest_from_ratified]`
- `test_s8b_oracle_manifest.py::test_ungated_manifest_apis_are_not_public[write_manifest]`
- `test_s8b_ratified_verify.py::test_launch_validate_rejects_genuine_eligible_earlier_official_run` — derived True の earlier run を launch が rule-mismatch 拒否。
- `test_s8b_ratified_verify.py::test_launch_validate_accepts_genuine_ineligible_earlier_resume` — derived False の resume earlier run を launch が受理。
- `test_s8b_ratified_verify.py::test_g1_selection_helper_rejects_genuine_eligible_earlier_official_run` — consumer の genuine 負例。
- `test_s8b_ratified_verify.py::test_g1_selection_helper_accepts_genuine_ineligible_earlier_resume` — consumer の genuine 正例。

## 現行の受理・拒否挙動

- 変更前は旧 3 public 名から低位構築・保存へ直接到達できました。
- 変更後は旧 3 名が `AttributeError` となり、`build_approved_manifest` だけが public builder として残ります。
- private 3 関数の入力、返却、例外、create-only 動作は不変です。underscore 名を知る in-process caller までは機構的に封印していません。
- 選択 gate の受理集合は変更していません。derived-eligible な earlier official run は両経路で拒否し、resume により derived-ineligible な earlier run は両経路で通ります。
- anomaly variant の即時拒否も不変です。

## 実走状況

実装済み・未実走です。repo 指定 runner で新規 node、既存 stub 2 node、既存 approved 正例を要求しましたが、`qstat -Q preflight rc=1`、runner rc=16 で child は一度も開始されませんでした。緑とは申告しません。

静的検査は以下を完了しています。

- 編集 5 file の AST parse
- `git diff --check`
- 旧 public 属性不在・private 3 名と approved builder の callable smoke
- caller AST 集計が正確に 25
- 既存 stub 2 関数が HEAD と完全一致
- 許可 5 file 以外に差分なし

runner が自動生成した失敗 receipt の exact directory は除去し、最終状態に `output/` 差分は残していません。

## 所有外 caller・共有 fixture・consumer test への波及

- 旧 3 public 名の production caller はありません。production 内部 caller は `build_approved_manifest` の 1 箇所だけで追随済みです。
- 共有 fixture の `test_s8b_holdout_freeze.py`、`s8b_v2_freeze_fixture.py`、`test_s8b_ratified_freeze.py`、`s8b_floor_evidence_fixture.py` は未編集です。
- manifest の lexical/direct consumer 集合は次の 13 fileです: `test_s8b_binding_driftguards.py`, `test_s8b_experiment_numbers.py`, `test_s8b_holdout_admission.py`, `test_s8b_materialization.py`, `test_s8b_oracle_artifacts.py`, `test_s8b_oracle_driver.py`, `test_s8b_oracle_judge.py`, `test_s8b_oracle_manifest.py`, `test_s8b_oracle_manifest_contract.py`, `test_s8b_oracle_n_pilot.py`, `test_s8b_oracle_report.py`, `test_s8b_ratified_freeze.py`, `test_s8b_verdict.py`。
- 構造検査 4 file (`test_ccbench_spawn_sites.py`, `test_official_perf_closure.py`, `test_s8c_preregistration_invariant.py`, `test_s8c_preregistration_predicates.py`) は対象 token/process/predicate に変化がなく、更新不要です。
- `test_growth_test_holds_contract.py` は ratified-verify node を hold 対象外と明示しており、新 node 追加による registry 更新は不要です。
- `docs/phase3-8b-restart-runbook.md:276` の旧 public API 記述は親の修正待ちです。

## 期待赤の finding 集合

期待赤となる executable test node は空集合です。親 docs 未 land の状態では runbook の記述が陳腐化していますが、現行 `check_docs` と test 群にはこの API 名を pin する node がありません。

したがって、runner infrastructure failure 以外の赤は回帰として扱う必要があります。

## 総括

- (c) と (d) は指定 5 file 内だけで実装済みです。
- 最大の不確実性は、実 fixture の旧 selected-run rows と新 measurement-generation rows の混在、および launch 正例の後段 scan です。
- 親は最初に genuine 4 node、特に launch 正例を計算ノードで実測してください。
- 続いて公開面 3 case、既存 stub 2 node、13 consumer file、4 構造検査を走らせる必要があります。
- `git add`・`git commit` は実行していません。