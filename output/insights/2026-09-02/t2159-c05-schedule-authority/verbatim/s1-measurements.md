# 親が段 1 で実測した値 (すべて HEAD = 24b31d2a37353d63a4f715ed2170d13e25df3fe3)

## M1. 12 述語の現在値

`s8c_preregistration_evidence.evaluate_all("HEAD", repo_root=<worktree>)` の出力そのまま。

```
C01	EVIDENCE_UNDEFINED	completion-proof-not-machine-checkable
C02	EVIDENCE_UNDEFINED	completion-proof-not-machine-checkable
C03	UNSATISFIED	manifest-registry-proof-undefined
C04	EVIDENCE_UNDEFINED	completion-proof-not-machine-checkable
C05	EVIDENCE_UNDEFINED	schedule-schema-absent
C06	EVIDENCE_UNDEFINED	completion-proof-not-machine-checkable
C07	EVIDENCE_UNDEFINED	completion-proof-not-machine-checkable
C08	EVIDENCE_UNDEFINED	prereg-binding-proof-undefined
C09	EVIDENCE_UNDEFINED	completion-proof-not-machine-checkable
C10	SATISFIED	cross-binding-readiness-satisfied
C11	EVIDENCE_UNDEFINED	completion-proof-not-machine-checkable
C12	EVIDENCE_UNDEFINED	completion-proof-not-machine-checkable
---
EVIDENCE_UNDEFINED	10
SATISFIED	1
UNSATISFIED	1
SATISFIABLE_CONDITION_IDS = ['C10']
```

SATISFIED は 1 件 (C10)。runbook の「0 件」は stale である。

## M2. ratified freeze の発効状態

`s8b_ratified_freeze.load_ratified_freeze()` は例外で終わる。

```
load_ratified_freeze RAISED: RatifiedFreezeError [no-active] live active pointer が無い (v2 未発効)
```

## M3. authority 18 key と production 値の型不一致 (現行コードで再確認)

- `s8c_generation_projection.LEAKPROOF_CONTEXT` (`:22-26`) は括弧で連結した**文字列**。
  `s8c_schedule._MAPPING_AUTHORITY_KEYS` は `leakproof_context` に **JSON object** を要求する。
- `p3_autonomous_workload_trial._whiteboard()` (`:1707-1709`) は loop state が無いとき `[]` を返す。
  `s8c_schedule._validate_non_degenerate_value` は**空配列を拒否**する。
- `descriptor_binding` は initial-state 側の**単数**キーで全 cell 共有の単一 mapping。
  search-space 側には別に `descriptor_bindings` (複数形) がある。

## M4. 事前登録 §5 の記入状態

`docs/phase3-8c-preregistration.md` §5 の表で「未記入」なのは、
累積ベンチ実時間の総上限と arm/holdout ごとの上限、env_tag、反復単位対比の判定パラメータ、
**master_seed**、未既知性再確認の証跡、swapped 対応表、6 cell manifest、実行責任者・開始時刻。
記入済みは検定 4 点の 1 行だけ。

## M5. budget shape が要求する値

`s8c_budget.BudgetLimits` (`:84-`) は `total_bench_s` / `per_arm_bench_s` / `per_holdout_bench_s`、
`ReservationCell` (`:116-`) は `cell_id` / `holdout` / `arm` / `reserved_bench_s` を要求する。
いずれも §5 の未記入欄に対応する数値である。

## M6. campaign lock の enforcement source closure

`campaign_lock.CONTRACT_LOADER_RELATIVE_PATHS` は 24 path の exact 集合で、
`s8c_preregistration.py`、`s8c_preregistration_evidence.py`、`s8c_generation_projection.py` を含む。
`p3_autonomous_workload_trial.py`、`s8c_schedule.py`、`s8c_budget.py` は**含まない**。

## M7. schedule artifact の pin 閉包

`output/s8c-preregistration/schedule.v1.json` を path で pin しているのは
証拠契約 JSON (`:194`) と test 3 file だけで、`FROZEN_MANIFEST` 相当の凍結台帳・trust root は無い。
artifact 自体が不在なので producer の出力 bytes 変更も現時点では発生しない。
