## 実装した差分

- `orchestrator/campaign/s8b_floor_campaign.py:6283`：指定の2行だけ追加。

```diff
+        except CampaignAbort:
+            raise
         except (RuntimeError, subprocess.TimeoutExpired) as exc:
```

- `orchestrator/tests/test_s8b_floor_campaign.py:9914`、`:9962`：指定の負例・正例を追加。例外同一性、probe 回数、実 journal、結果未生成、plain RuntimeError の失敗記録を検証します。
- 実際の全差分：[stage5-owned.patch](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2596-impl/stage5-owned.patch)。

## 実装前の受理・拒否挙動

測定側の `CampaignAbort` は `RuntimeError` 節に捕捉され、post-probe 後に失敗 session として処理されていました。競合があれば `competing_process` が優先され、継続・retry は admission 判定に依存します。

今回、非 certified 経路の当該 abort を即時停止へ変更しました。plain `RuntimeError`、`TimeoutExpired`、非 abort の `FloorCampaignError` の扱い、certified・最終 inspection の受理条件は不変です。

## 実走した検査

**実装済み・テスト未実走。緑／赤の判定はありません。**

`tools/run_tests.py -n 0` に次の nodeid を指定しました。接頭辞は `orchestrator/tests/test_s8b_floor_campaign.py::` です。

- `test_measure_campaign_abort_propagates_without_launch_failure`
- `test_measure_runtime_error_records_launch_failure`
- `test_post_probe_runs_on_launch_error_and_competing_takes_precedence`
- `test_admission_failure_creates_no_result_pending_bytes`（全パラメータ）

runner は rc=16。`qstat -Q` が `Unknown user-id` を返し、子プロセスは未起動でした。同ファイルの `--collect-only` も同じ原因で未実走です。M1〜M3 の変異検査も未実走です。

静的検査は成功：`git diff --check`、両ファイルの AST parse、実装2行のみの変更、既存関数の AST 不変、新設テスト名の重複なし。

## 制約 meta-test の洗い出し

以下を独自に特定し、runner に指定しましたが、同じ rc=16 で未実走です。

- `orchestrator/tests/test_plain_runner_coverage.py` 全体：自走 harness。
- `orchestrator/tests/test_acceptance_schedule_order.py::test_g5_real_ledger_covers_at_least_90_percent_of_real_collection`：所要時間台帳の網羅率。
- `orchestrator/tests/test_pytest_collection_config.py::test_repo_pytest_ini_has_no_addopts_and_pins_testpaths`：収集設定。
- `orchestrator/tests/test_real_repo_serialization.py::test_real_repo_group_collection_exactly_matches_canonical_nodes`：収集・共有資源分類。

対象ファイルに適用される専用の命名 meta-test は検索範囲で未発見。名前の一意性は静的確認しました。

探索先の `tools/tests`、`pyproject.toml`、`orchestrator/tests/__init__.py` は不在でした。必読4ファイルは読取可能でした。

## 波及可能性の静的列挙

- admission wrapper・注入 callback：当該 abort が元の例外のまま伝播します。wrapper の3拒否条件それぞれの到達性は未検証です。
- resume／checkpoint／liveness：未完了 `session-start` と aborted terminal を扱う経路へ波及します。開始済み retry 枠は消費済みのままです。
- 共有 fixture：変更なし。これを import する `test_s8b_dependency_prefix_bridge.py` も未変更・未実走です。
- report／artifact consumer：abort 経路では失敗 session と `result.json` が生成されなくなります。未知の外部 consumer 全体は保証していません。
- certified 経路は対象 try より前に return します。

## 総括

指定2ファイルだけを変更し、最後の操作で **103行・対象2ファイルのみ・非空**の patch を書き出しました。docs 編集・commit・push は行っていません。

親側で回帰・meta-test・変異検査の実走が必要です。