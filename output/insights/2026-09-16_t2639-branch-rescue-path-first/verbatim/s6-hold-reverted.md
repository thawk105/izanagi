## 読んだ資料

- 射影資料 `/home/SFC/tanab/.claude/jobs/3440ad3e/tmp/f300.txt`
- `orchestrator/tests/flaky_test_holds.py`
- validator が参照する `docs/failures.md` の F300 節

## 追加した hold 4 件 (file:line と各 field の値)

登録先: [flaky_test_holds.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2639-impl/orchestrator/tests/flaky_test_holds.py:233)

各 node ID は `orchestrator/tests/` + 下表の値です。

| 行 | 登録 key | green_run_count |
|---|---|---:|
| 233 | `test_p3_b4_producer_auth_experiment.py::test_disposable_tree_mutation_does_not_change_main_worktree` | 2 |
| 259 | `test_run_tests_preflight.py::test_headroom_short_queue_unavailable_cap_oom_stops_without_dispatch` | 6 |
| 285 | `test_check_ai_provenance.py::test_provenance_headroom_short_queue_unavailable_cap_oom_stops` | 7 |
| 311 | `test_t338_submission_gate_unit5.py::test_receipt_publish_call_sites_are_path_aware_and_allow_event_sink` | 5 |

4 件共通の値:

- `known_failure_node_ids`: 登録 key と同じ 1 要素の `frozenset`
- `same_tree`: `True`
- `green_collection_condition` / `red_collection_condition`: `ACCEPTANCE_COLLECTION`（`"acceptance-full-suite"`）
- `failure_signature`: `"赤になった test の集合は走行ごとに変わり"`
- `cause`: `"走行の内側で、repo root を全走査する検査と repo root 配下に scratch を作っては消す検査が競合する。"`
- `evidence_id`: `"F300"`
- `reintroduction_task_id`: `"acceptance-same-run-scratch-churn"`

観測文は各々、次の形式で登録しました。

`2026-09-16、同一 tip・同一差分の受入全走で attempt {番号} の {回数} 回、当該 node が{緑/赤}だった。`

| 行 | green_observation の番号・回数 | red_observation の番号・回数 |
|---|---|---|
| 233 | `1, 6`・2 回 | `2, 3, 4, 5, 7, 8`・6 回 |
| 259 | `1, 2, 3, 4, 6, 8`・6 回 | `5, 7`・2 回 |
| 285 | `2〜8`・7 回 | `1`・1 回 |
| 311 | `1, 3, 4, 5, 7`・5 回 | `2, 6, 8`・3 回 |

## failure_signature が F300 節に存在することの確認

射影 `f300.txt` に選択した文字列が存在することを、現物の読み取りと正規化後の部分一致で確認しました。4 件の関数名もすべて存在します。

## 自己検査の結果

- 構文解析: 成功。
- 射影資料をメモリ上の証拠参照先として、変更していない validator で追加 4 件を検証: 成功。
- **通常の import: 失敗。** 作業木の `docs/failures.md` の F300 節には対象の関数名が 4 件ともなく、validator が `ValueError` を送出します。
- 追加前の既存テキストをすべて保持したことを確認。
- pytest は未実行。

## 直さなかったもの と その理由

証拠台帳の不一致は、`docs/failures.md` が編集禁止のため修正していません。既存 hold・validator・実装・他のテストも変更していません。git add・commit・push は行っていません。

## 総括

**実装済み・未実走。closed ではありません。** 指定の 4 件のみ追加しましたが、現在の作業木では証拠台帳の不一致により通常の validator は通りません。