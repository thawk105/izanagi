## 所見の対応表

| 所見 | 状態 | 根拠 |
|---|---|---|
| red 1 | partial | 呼出し数を2へ更新済み。ただし別の合計 assert が `22 == 21` で失敗。 |
| red 2 | closed | 全7件成功。第2 assert の guard inventory 一致も実走確認。 |

## 変更の要約

指定2 test file の inventory と指定コメントだけを変更しました。

- `test_campaign.py`: S4 の `run_campaign` 呼出し数を1→2。
- `test_official_perf_closure.py`: `_REVIEWED_PERF_FILES` の辞書順位置に S4 を追加。`_ADDED_REVIEWED_GUARDS` は変更なし。

現物の `p3_s4_loop.py` の呼出しは stock 経路 **1986行**、候補経路 **2165行**です。

## 実走結果

指定の `pytest.main(...)` 形式で実行しました。

| 対象 | 件数・結果 | rc |
|---|---|---:|
| `orchestrator/tests/test_campaign.py::test_certified_writer_authorization_caller_inventory_is_closed` | 1 failed、425 deselected | 1 |
| `orchestrator/tests/test_official_perf_closure.py` 全件 | 7 passed | 0 |

後者には `test_outer_perf_file_and_added_guard_inventory_is_exact` を含み、両 assert が成功しています。`git diff --check` も成功しました。

## 波及

perf heuristic は `p3_s4_loop.py` の次の条件に一致します。

- 3038・3040行: `calibrated_perf`（末尾 `_perf`）、`perf_workload`（先頭 `perf_`）。
- 3163行の条件式・3164行の `if`: `calibrated_perf`。
- `verify_performance` 自体は不一致。3169行の単独条件は対象外です。

production・docs は未変更。`git add`／`git commit` は実行していません。

## 未了・懸念

`test_campaign.py:5413` の合計固定値 `21` が残っています。指定更新後の合計は22です。今回の「他の assert を変更しない」という制約に従い、変更せず残しました。解消には親による合計 pin 更新の追加裁定が必要です。

## 総括

指定2件の更新と実走は完了しました。red 2 は解消、red 1 は合計 pin の不整合が残るため未解消です。