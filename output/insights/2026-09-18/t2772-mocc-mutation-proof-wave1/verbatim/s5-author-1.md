## 変更 file 一覧

新規 3 file：

- `patches/broken-mocc-hot-update-unlock.patch`
- `orchestrator/campaign/s3_mocc_mutation_proof.py`
- `orchestrator/tests/test_mocc_mutation_proof.py`

登録簿閉包の既存 7 file：

- `orchestrator/campaign/{materializer_admission,condition_meaning_gate,screening_driver}.py`
- `orchestrator/tests/{test_condition_meaning_gate,test_ccbench_spawn_sites,test_p3_build_authority_cli,test_p3_s4_loop}.py`

## patch の検査結果

| 検査 | 結果 |
|---|---|
| e9e477ca＋計装への `apply --check` | rc=0 |
| 計装なし e9e477ca | rc=1 |
| pin 511c9538 | rc=1 |
| `-fsyntax-only` TRACE 1/0 × macro 1/0 | 4 組すべて rc=0 |

構文検査は指定の define・include・`-Wall -Wextra -Werror` で実走しました。

追加した `#line` は 17 / 460 / 1069 / 1195。既存計装の 7 箇所は保持しています。touch set は `cc/mocc/transaction.cc` のみです。

## driver の設計と CHECK_KEYS / MATRIX

32 check、36 走（必須 25／観測 11）を実装し、import で確認しました。

- stock 12 → lockskip 6 → perm 6 → early 6 → hot-update 6。
- TRACE=1 の 5 build と TRACE=0 の 2 build。
- R1 の integrity 対象集合、raw verifier record、失敗・timeout 記録、atomic 保存を実装。
- 新 module の直接 subprocess site は `_run_trace` の 1 箇所。
- TRACE=0 論理行比較は実走し、`#line ±1` の不一致検出も確認。

driver の 36 走と新 JSON 生成は未実走です。

## 登録簿の変更と件数 pin の実測値

AST／実 registry の件数は supply **39**、compile-time witness **15**、CXX_FLAGS route **17**。

cross-product は **35 / 39 / 25 / 25** で、裁定の予測と一致しました。`_DEFERRED_GATE_MEMBERS` の lineno は変更していません。

## 実走した検査

各 file の `::test_*` 全 node を指定 harness で実走：

| 範囲 | 結果 |
|---|---|
| `test_mocc_mutation_proof.py::test_*` | 10 passed、1 failed |
| `test_mocc_proof_surface.py::test_*` | 18 passed |
| `test_condition_meaning_gate.py::test_*` | 125 passed |
| `test_ccbench_spawn_sites.py::test_*` | 71 passed、2 skipped |
| `test_p3_build_authority_cli.py::test_*` | 19 passed |

単独 node も緑：

- `test_s8b_floor_campaign.py::test_materializer_registry_covers_all_python_build_launches`
- `test_p3_s4_loop.py::test_all_naked_izanagi_macro_patches_are_registered_or_allowlisted`

赤は `test_mocc_mutation_proof_json_is_complete_and_bound` の **JSON 不在による FileNotFoundError のみ**。仮 JSON・skip 化はしていません。[新 harness の詳細ログ](/tmp/t2772-new-final.log)

既存 skip は `test_define_sink_cross_product_t2491_rejects_injected_swallow` の `n10-try-star`／`n14-try-star-reraise`。実行 Python が `except*` 非対応のためです。

## 波及の静的列挙

- `test_plain_runner_coverage`：新 file は `_run()` を持つため allowlist 追加不要。
- `acceptance_duration_ledger`：新 node は未登録時の既定 weight 1 秒。実測時間の反映は親側の対象。
- 共有 condition fixture は実 registry を参照し、新 macro の既存 parameterized test も通過。
- 新 JSON consumer の成功経路と新 driver の実 condition gate は、親の compute 後に確認が必要。

旧 14 check・4 patch・3 負例 witness は不変です。旧回帰の受理・拒否対照は全緑でした。

## 総括

実装と指定検査を完了しました。残る実証は親側の compute／JSON 生成です。子の検査は親の受入全走を代替しません。

scratch dir は削除済み。最終 `git status --short` は **所有既存 7 file の M、新規 3 file の ?? のみ**でした。旧成果物と submodule の差分はなく、`git diff --check` も緑です。commit は作成していません。