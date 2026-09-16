## 変更の要約

指定の 2 ファイルだけを変更しました。既存テスト・docs は未変更、git add / commit / stash / branch 操作は行っていません。

production の変更：

- 旧 412〜414 行：core の `ratified` 引数を削除。
- 旧 428〜434 行 → 新 425〜430 行：docstring を exact token 必須、拒否理由の集約継続、static loader 非呼出しの説明へ置換。
- 旧 488〜505 行：static fallback を除去し、`ratified_error` → token 欠落 → hash 照合の順に変更。
- 旧 624・638 行：core 呼出しから `ratified=` を削除。

既存の exact type 検査は維持しています。`_gate_check_validated`、`run_block`、`_parser`、`_exit_code`、`main` は変更前と AST 一致を確認しました。

`git diff --check` は成功。`git diff --stat` の出力：

```text
 orchestrator/campaign/s8b_oracle_driver.py | 46 ++++++++++++------------------
 1 file changed, 18 insertions(+), 28 deletions(-)
```

新規テストは未追跡のため上記には含まれません。245 行追加で、2 ファイル合計は 263 行追加・28 行削除です。

## 新規 node と実走結果

指定の起動形で **17 passed in 5.26s**。以下の nodeid はすべて `orchestrator/tests/test_s8b_gate_core_exact_launch_validated.py::` を接頭辞とします。

| nodeid の末尾 | 結果 |
|---|---|
| `test_public_reread_v2_requires_launch_validated` | PASSED |
| `test_public_reread_v2_ignores_injected_ratified` | PASSED |
| `test_core_v2_without_launch_validated_is_refused[both]` | PASSED |
| `test_core_v2_without_launch_validated_is_refused[floor-only]` | PASSED |
| `test_core_v2_without_launch_validated_is_refused[budget-only]` | PASSED |
| `test_core_exact_launch_validated_preserves_predicates[both]` | PASSED |
| `test_core_exact_launch_validated_preserves_predicates[floor-only]` | PASSED |
| `test_core_exact_launch_validated_preserves_predicates[budget-only]` | PASSED |
| `test_core_rejects_launch_validated_subclass` | PASSED |
| `test_public_ratified_load_errors_preserve_refusals[RatifiedFreezeError]` | PASSED |
| `test_public_ratified_load_errors_preserve_refusals[RuntimeError]` | PASSED |
| `test_public_explicit_ratified_error_keeps_early_return` | PASSED |
| `test_public_two_failed_reads_preserve_refusals` | PASSED |
| `test_core_launch_validated_missing_hash_remains_refused` | PASSED |
| `test_public_reread_v1_never_gets_missing_token_refusal` | PASSED |
| `test_cli_gate_check_transports_missing_token_refusal` | PASSED |
| `test_gate_core_signature_has_no_ratified_injection_port` | PASSED |

node 6 の `freeze-ratify: [reason] [reason] detail`、node 8 の二読目例外を含む拒否理由 4 件も exact 一致しました。個別 node の所要時間は未採取です。

## 既存 consumer の焦点走

| 対象 | 結果 |
|---|---|
| driver の指定 `-k` 集合 | **2 passed / 3 failed** |
| known-axes の `historical_oracle_nonadapter` | **1 passed**、261.88 秒 |
| driftguards の `gate_check or ratified_memo` | **5 passed / 1 skipped**、150.93 秒 |
| `no_production_module_constructs_ratified_freeze_directly` | **1 passed** |
| `private_validated_gate_has_only_run_block_as_production_caller` 単独 | **1 passed** |

driver の内訳：

- `test_gate_check_core_rejects_reverified_freeze_token`：PASSED。
- `test_private_validated_gate_has_only_run_block_as_production_caller`：PASSED。
- `test_run_block_reuses_launch_validated_and_legacy_loader_is_dead`：FAILED。
- `test_run_block_verifies_manifest_once_and_reuses_object`：FAILED。
- `test_v2_freeze_bytes_not_active_generation_is_refused`：FAILED。

前二つの失敗は診断用再実行でも再現し、両方とも次の refusal を確認しました。

```text
official-output-root: official output_root は repository 外でなければならない
```

これらは private gate を fake に置換しており、今回変更した core の検査には到達しない構成です。期待値を変更せず、失敗として残しています。

最後の失敗は fixture 構築時の `sealed snapshot child disconnected` → `snapshot cleanup failed` です。目的の hash 拒否検査は未到達です。

driftguards の skipped node は `test_gate_check_broken_binding_manifest_stacks_manifest_verify_refusal`。既存 growth hold によるもので、検証済みには数えていません。

## 波及の静的列挙

- production の core 呼出しは `gate_check` 内 5 箇所と `_gate_check_validated` 内 1 箇所。引数調整は指定の 2 箇所だけです。
- 所有外の直接 core consumer は既存 driver の historical token 拒否テストと known-axes の非 adapter テスト。両方の焦点走は PASSED。
- public `ratified=` / `ratified_error=` と、`real_repo_ratified_memo.patch_ratified_loader` の seam は維持しています。memo の 5 node は PASSED。
- 新規 fixture はファイル内限定です。既存 receipt memo、v2 emitter fixture、consumer helper を変更・import していません。
- 指定の `conftest.py`、`test_real_repo_serialization.py`、`acceptance_shards.py` の検索では、新規ファイル名・node 数を固定する該当箇所はありませんでした。

以上は静的探索結果であり、caller の権威ある閉包を証明するものではありません。

## 走らせていないもの

- 受入全走、変異 matrix、旧実装に対する KILL 実測。
- 広い consumer 全集合と `test_v2_standalone_gate_check_requires_full_floor_validation`。
- growth hold で skipped された binding gate 本体。
- sealed fixture 失敗後の hash 拒否 assertion。
- `check_codex_agents.py`、`check_docs.py`、provenance 監査。

新規 17 node に未実走はありません。実装済みですが、上記の統合・変異検証は未完了です。

## 総括

裁定どおりの実装と新規 17 node は完了し、全件 PASSED です。既存焦点走には **3 failed / 1 skipped** が残るため、全体緑・受入完了とは報告しません。既存期待値を緩和せず、2 ファイルの差分を親のレビューへ返します。