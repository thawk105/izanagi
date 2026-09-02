# 親の実測 — 段 6 の入力

## 着手前 baseline (本 branch HEAD `821c7ecfa`、実装差分なし、2026-09-02 20:07-20:17 JST)

| 対象 | 結果 |
|---|---|
| `test_s8b_attempt_registry.py` + `test_attempt_registry_core_s8b_profile.py` + `test_attempt_registry_core_equivalence.py` | **153 passed / 0 failed** / 13.25s |
| `test_s8b_floor_attempt_launcher.py` + `test_s8b_holdout_admission.py` + `test_s8b_scheduler_accounting.py` + `test_reflux_formal_consumer.py` | **278 passed / 0 failed** / 41.9s |
| `test_s8b_floor_campaign.py` | **468 passed / 3 skipped / 0 failed** / 427s |

**着手前の赤はゼロ。** ただし `test_trial_registry.py` は baseline を取っていない (親 brief の
consumer 表に production module `trial_registry.py` は載せたが、その test file を焦点集合へ
入れていなかった)。

## 実装差分適用後 (2026-09-02 21:25-21:34 JST、`s5-diff.patch` を wave worktree へ適用)

| 対象 | 結果 |
|---|---|
| 主面 3 file | **2 failed / 172 passed** / 10.44s |
| `test_trial_registry.py` + consumer 4 file | **116 failed / 387 passed** / 166.76s |
| `test_s8b_floor_campaign.py` | **468 passed / 3 skipped / 0 failed** / 65.7s |

## 赤の根本原因 — 1 つ。must-fix

**[実測] `attempt_registry_core._load_registry_bytes()` の戻り型を
`RegistryRows` から `tuple[RegistryRows, BudgetCounts]` へ変えたことが原因である。**

- 変更箇所: `orchestrator/campaign/attempt_registry_core.py:1400-1427` (実装差分)。
- 壊れた consumer: `orchestrator/campaign/trial_registry.py:2340-2350` の
  `_load_attempt_registry_bytes()` が `_attempt_core._load_registry_bytes` を
  **private のまま直接呼んでいる**。宣言戻り型は `tuple[dict[str, Any], ...]` のままで、
  実際には `(rows, counts)` の 2-tuple を受け取る。
- 症状: `AttributeError: 'tuple' object has no attribute 'get'` が
  `attempt_registry_core.py:1018` (`_assert_registry_rows_with_budget_counts` の
  `rows[0].get("event")`) で出る。8c profile (`p3-8c-attempt-registry/v2`) の replay 経路である。
- **`trial_registry.py` は編集禁止 file である** (段 5 契約)。したがって core 側で戻り型を
  戻すしかない。

**段 3 の 2 レンズはこの consumer を数え落とした。** レンズ A は
`assert_registry_rows` を callable として渡す 2 件 (`trial_registry.py:2224-2248,3437-3474`) を
挙げたが、**private `_load_registry_bytes` の直接呼出し `:2348` は挙げていない。**
静的レビューでは出ず、親の実走で初めて出た型である。

### 要求する直し方

`_load_registry_bytes()` の signature と戻り型を**元に戻す** (`-> RegistryRows`)。
予算 seed 版は別名の private 関数として足す (例:
`_load_registry_bytes_with_budget_counts(...) -> tuple[RegistryRows, BudgetCounts]`)。
`load_attempt_registry()` は前者、`load_attempt_registry_with_budget_counts()` は後者を使う。
**`trial_registry.py` を 1 byte も変更してはならない。**

### fix 後に緑を要求する範囲

- `orchestrator/tests/test_trial_registry.py` — 全緑 (現在 116 failed)
- `orchestrator/tests/test_attempt_registry_core_equivalence.py` — 全緑 (現在 2 failed)
- 主面 3 file — 全緑
- consumer 4 file + `test_s8b_floor_campaign.py` — 全緑を維持

## 親 brief への訂正 (段 7 で記録する)

親 brief の consumer 表は production module `trial_registry.py` を挙げながら、その test file
`orchestrator/tests/test_trial_registry.py` を焦点集合へ入れていなかった。**`DW-O26` の
「変更した production file を参照する consumer test も含める」を、参照関係で引ききれていなかった。**
今回はその漏れが 116 node の赤として現れた。以後の焦点集合は
`test_trial_registry.py` を含む。
