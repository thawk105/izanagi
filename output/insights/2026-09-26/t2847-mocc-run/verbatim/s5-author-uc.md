## 変更

| file | 差分 |
|---|---|
| [condition_meaning_gate.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2847mc-uc/orchestrator/campaign/condition_meaning_gate.py:233) | 2 macro の `DefineSpec`、`cc/mocc/transaction.cc` の witness、site 数 5・9 を登録。冒頭の登録件数も更新。 |
| [screening_driver.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2847mc-uc/orchestrator/campaign/screening_driver.py:86) | 両 macro の既定値を `0` に設定。 |
| [test_condition_meaning_gate.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2847mc-uc/orchestrator/tests/test_condition_meaning_gate.py:49) | 登録順、patch と fixture の束縛、domain、site 数、件数と docstring の固定値を更新。 |
| [test_p3_s4_loop.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2847mc-uc/orchestrator/tests/test_p3_s4_loop.py:8474) | 裸マクロの patch 別許容表に 2 本を追加。 |
| [test_ccbench_spawn_sites.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2847mc-uc/orchestrator/tests/test_ccbench_spawn_sites.py:3553) | sink 分類の固定件数を更新。在庫照合は既存の動的照合を使用。 |
| [test_screening_driver.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2847mc-uc/orchestrator/tests/test_screening_driver.py:663) | 既定値 `0` と、Genome 経由では裸マクロを供給できないことを固定。 |

patch 本文の `+#if <macro>` は V25 が **5 行**、V34 が **9 行**で、U-A 報告と一致しました。define 総数は 57→59、compile-time witness は 39→41、CXX flags 経路は 33→35 です。新 2 macro は s1・certify probe の source 候補集合に無いため、それぞれの `proven-unreachable` は 53→55、43→45。全 patch interface を覆う s8b の `covered` は 57→59 としました。受理述語や供給経路の処理は変更していません。

Genome の `CCBENCH_` key は `-DCCBENCH_<macro>=1` を生成します。両登録の要求経路は `CMAKE_CXX_FLAGS` の裸マクロであり、screening の build 引数照合が Genome からの供給を `screening-build-route-mismatch` で拒否することを source と静的実行で確認しました。既定値表の `0` 以外に新たな供給経路は追加していません。

## 検査と引き継ぎ

pytest は**実走できていません**。下記 6 nodeid を指定した `python3 -m pytest` は PreToolUse hook に拒否され、`tools/run_tests.py` 経由も queue 照会失敗で **rc=16、child 未起動**でした。重い file 全体も実装済み・未実走です。親の計算ノードでの焦点走が必要です。

- `test_condition_meaning_gate.py::{test_compile_time_branch_registry_and_fixtures_are_bound_to_real_patches,test_v1_domain_and_claim_boundaries_are_exact,test_module_claim_names_the_exact_59_define_supply_domain}`
- `test_p3_s4_loop.py::test_all_naked_izanagi_macro_patches_are_registered_or_allowlisted`
- `test_ccbench_spawn_sites.py::test_patch_define_inventory_matches_condition_gate_registry`
- `test_screening_driver.py::test_screening_condition_requests_cover_exact_define_specs`

静的検査は 6 file の AST、patch site 数と供給経路の照合、`git diff --check`、`check_codex_agents.py`、`check_docs.py` が通過しました。所有外 caller・共有 fixture のコードは変更していません。consumer 側で未実走の範囲には、追加した screening の 2 パラメータ、条件 gate の patch 束縛、sink 分類の 2 test が含まれます。

[T-2849] との合流対象は [test_ccbench_spawn_sites.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2847mc-uc/orchestrator/tests/test_ccbench_spawn_sites.py:3573) の **3573、3576、3600、3609 行**の件数です。`t2849-unit-a` の現作業木では対応値が 39・43・29・29 の旧基準にあり、この単位の 55・59・45・45 をそのまま採用せず、取り込み時に双方の増分を確認してください。merge は行っていません。

R7 変異で赤になる見込みの node は次のとおりです。いずれも**静的予測で、probe 未実走**です。

| 変異 | 赤になる見込みの test |
|---|---|
| M1: V25 を `_DEFINE_SPECS` から削除 | `test_patch_define_inventory_matches_condition_gate_registry`、`test_v1_domain_and_claim_boundaries_are_exact` |
| M2: V34 witness を削除 | `test_compile_time_branch_registry_and_fixtures_are_bound_to_real_patches` |
| M3: V34 の登録 key を 1 字変更 | `test_patch_define_inventory_matches_condition_gate_registry`、`test_v1_domain_and_claim_boundaries_are_exact` |
| M4: V25 site 数を +1 | `test_compile_time_branch_registry_and_fixtures_are_bound_to_real_patches` |

## 総括

指定の 6 file で新 patch 2 本を登録し、patch 実数に基づく固定値を追随させました。pytest の緑判定はまだありません。親の焦点走と [T-2849] の件数合流が残ります。