## 総括

- 所有 2 ファイルに実装済み。差分は 7 hunks（driver 6、test 1）。
- 新規テストは 13 関数・24 parametrized cases。
- pytest 実走：passed 0／failed 0／新規 24 cases 未実走。**closed ではありません。**
- AST 構文確認と `git diff --check` は成功。
- ソース編集の scope 逸脱なし。commit・git 状態変更なし。
- runner が診断 receipt を `output/pegasus-dispatch/` に自動生成しています。

## 変更一覧

以下のパスは worktree root 相対です。

| file:line | 変更 |
|---|---|
| `orchestrator/qualification/t126_driver.py:106` | 比較行・hash・projection を保持する `AttestationMismatchError` |
| 同 `:479` | 比較条件を維持して typed raise に置換 |
| 同 `:495` | 子 helper：不一致 sidecar、成功 JSON、例外時 rc=31 |
| 同 `:528` | 親 message helper：相対 path・failed fields・読取り失敗時 fallback |
| 同 `:1277`, `:1312` | closure の子・親を helper に接続 |
| `orchestrator/tests/test_t126_qualification_driver.py:369` | 既存 fixture を再利用する補助関数と指定 13 テスト |

`run_series`・`verify()`・`attestation_records`・`evidence_manifest`・`execution_guard.py` は変更していません。

## 実走

| 検査 | 結果 |
|---|---|
| 指定の直接 pytest コマンド | PreToolUse hook が起動前に拒否 |
| driver 全体を `tools/run_tests.py` で実行 | rc=16、`qstat -Q preflight rc=1`、`child_started=false` |
| 関連 consumer 4 ファイル＋変異 registry meta-test | 同じ dispatch 障害で未実走 |
| 環境 literal・process inventory meta-test | 同じ dispatch 障害で未実走 |
| 所有 2 ファイルの AST parse | 成功 |
| `git diff --check` | 成功 |

探索して実行対象に加えた meta-test nodeid：

- `test_t126_pegasus_tools.py::test_fr3_mutation_node_registry_is_exact_and_complete`
- `test_env_contract.py::test_v2_modules_have_no_env_literals_outside_registry`
- `test_ccbench_spawn_sites.py::test_reviewed_process_launch_inventory_is_recursive_and_exact`

いずれも `orchestrator/tests/` 配下です。実走成功した pytest nodeid はありません。

## 変異 anchor 表

行番号は実装後の `orchestrator/qualification/t126_driver.py`。変異そのものは未実走です。

| ID | 行 | 対象 |
|---|---:|---|
| M1 | 516 | mismatch sidecar の `create_json` |
| M2 | 521–523 | 成功時の公開経路 |
| M3 | 513 | `failed_fields` |
| M4 | 512 | 全 `comparisons` の保存 |
| M5 | 502–520 | 空 comparisons を含む mismatch 分岐 |
| M6 | 524–525 | 書込み例外でも rc=31 |
| M7 | 501, 524 | probe 等の汎用失敗経路 |
| M8 | 528–546 | 親 message helper |
| M9 | 541–545 | reader 例外の吸収 |
| M10 | 1312 | production 親の message helper 呼出し |
| M11 | 1277 | production 子の helper 委譲 |
| E1 | 498 | helper docstring、挙動の等価対照 |

## 波及可能性

- **所有外 caller**：検索範囲では driver の `_attest`・`AttestationError`・`RC_ATTESTATION` の外部直接参照は見つかりませんでした。`collector.py` は `verify`、`submission.py` は `build_series_preimage` を import しています。
- **共有 fixture**：`_attest_fixture`、`_fsm`、`_evidence` を再利用。既存 fixture と assertion は変更していません。
- **`test_t126_pegasus_tools.py`**：変異 anchor registry、verify／receipt closure に波及し得ます。registry のみ実行を試行し、全体は未実走です。
- **`test_t126_qualification_artifacts.py`**：create-only・canonical JSON・capability 契約。
- **`test_campaign.py`**：driver の pipeline 呼出し数・構造 pin。
- **`test_official_perf_closure.py`／`test_artifact_admission.py`**：driver を含む authority・admission の静的閉包。
- **collector**：新規 T5 で sidecar の manifest 列挙を検査しますが、未実走です。

## 未実走・懸念

新規・既存テスト、変異 M1〜M11・E1、production `run()` 全体の E2E は未検証です。成功 bytes 不変や実 fork の確認はテストとして実装しましたが、実測済みとは報告しません。

段 4 裁定どおり、fsync stall、外側 timeout、SIGKILL 後の staging 残留は保証対象外です。driver identity が変わるため、新規 live 実走には変更を含む commit・source stage が必要です。

自動実行ガードは直接 pytest を「Pegasus ログインノード上の重量処理」として拒否しました。代替 runner も scheduler preflight に失敗し、テストを起動できませんでした。
