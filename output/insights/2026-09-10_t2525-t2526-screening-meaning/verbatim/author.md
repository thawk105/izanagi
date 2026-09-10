## 総括

**所有6ファイルへ実装済み・未実走です。closed とは申告しません。**

- 既存の物理量宣言生成を `backoff_sweep` 内 helper へ抽出。同じ要求 mapping を外側 gate と screening caller へ渡します。
- optional 宣言を公開 `evaluate_candidate`、stock checkout の両分岐から転送し、`BACKOFF_FIXED` だけへ渡します。独自拒否 gate は追加していません。
- T2418 新走の identity/report schema を v2、status を `driver_declared_static_backoff_physical_us` に更新しました。
- docs・共有 fixture・旧 artifact・Git index は変更していません。commit 等も未実施です。

追加した検査候補は次のとおりです。パスはすべて `orchestrator/tests/` 配下です。

| node | 検査内容 |
|---|---|
| `test_screening_driver.py::test_evaluate_candidate_declared_backoff_reaches_real_gate` | 5→5、3000→1000 の green、1000→1000 の red。stock 有無の6ケース |
| `test_screening_driver.py::test_screening_undeclared_randomized_backoff_remains_unestablished` | b10 実 encode の無宣言乱択 |
| `test_backoff_sweep.py::test_backoff_screened_caller_forwards_intent_to_real_gate` | baseline/candidate 宣言から実意味 gate への到達 |
| `test_backoff_sweep.py::test_run_workload_shares_physical_mapping_with_screened_caller` | 外側と screening の mapping 同一性 |
| `test_backoff_extended_sweep.py::test_t2418_v2_discovery_does_not_select_v1` | 実ファイル探索による v1 除外・v2 選択 |

意味の正負は capture・meaning evaluator・family admission を差し替えていません。公開 API 検査では性能 sink を模擬し、caller 検査では campaign 準備と評価 wrapper を模擬しています。discovery 検査は承認済み WAL view の読取り境界を fixture に置換しています。既存 materializer 検査の config/JSON/DAT 期待値も承認済み v2 更新に整合しました。

実施済みは6ファイルの AST parse、関数名重複・禁止結合文字の確認、`git diff --check` です。指定 TMPDIR は sandbox の書込み許可外で、`test -w` も失敗したため pytest/build は起動していません。**緑の実走 node はありません。**

制約 meta-test は参照検索で `test_pytest_collection_config.py`、`test_growth_test_holds_contract.py`、`test_flaky_test_holds_contract.py`、`test_acceptance_schedule_order.py` を確認対象として抽出しました。これらも未実走です。

所有外への波及候補：

- caller：`s6_sort_sweep`、`s8a_trigger_sweep`、`backoff_requested_us/profile/repro/overthrottle`
- 共有 fixture：既存 `condition_meaning_gate/supplied` と stock。追加・編集不要
- consumer 検査：`test_screening_opt_in`、`test_t1416_backoff_compiler_binding`、`test_p2_2_site_aware`、`test_campaign`、`test_condition_meaning_gate`、backoff report/shape/consumer/provenance 系、s1 freeze 系
- read-only 棚卸し：s1 の literal 5/10/2、paper A2 の 10/5 は現行要求と一致しています。

親 harness 用の変異候補は以下です。**変異自体は未実施**で、期待 node は上表の候補です。置換は記載関数内に限定してください。

| 変異 | 一意な old → new | 期待 node 候補 |
|---|---|---|
| M1 | screening `_run_condition_gate_for_genome`：`backoff_fixed_declaration\n                    if request.macro` → `None\n                    if request.macro` | 公開 API の正負、caller |
| M2 | backoff helper：`canonical_float64_bits(float(physical))` → `canonical_float64_bits(float(raw))` | 公開 API の3000→1000、caller |
| M3 | screening `evaluate_candidate`：`backoff_fixed_declaration=backoff_fixed_declaration,` → `backoff_fixed_declaration=None,` | 公開 API の正負 |
| M4 | 下記 stock 分岐の置換 | 公開 API の `with_stock=True` |
| M5 | backoff `_run_screened_workload`：`genome.flags["BACKOFF_FIXED"],\n            ),` → `-1,\n            ),` | caller |
| M6 | `spec_slug=f"t2418-backoff-static-explore-v2-silo-{tag}",` → `spec_slug=f"t2418-backoff-static-explore-v1-silo-{tag}",` | discovery |
| M7 | `"driver_declared_static_backoff_physical_us"` → `"unestablished_for_positive_backoff_fixed_as_in_existing_sweep"` | 既存 config/materializer 検査。metadata 回帰 |

M4 の old：

```python
            source_root, genome, stock_root=stock_root, cxx=cxx, cmake=cmake,
            expected_toolchain_manifest=expected_toolchain_manifest,
            backoff_fixed_declaration=backoff_fixed_declaration,
```

new：

```python
            source_root, genome, stock_root=stock_root, cxx=cxx, cmake=cmake,
            expected_toolchain_manifest=expected_toolchain_manifest,
            backoff_fixed_declaration=None,
```