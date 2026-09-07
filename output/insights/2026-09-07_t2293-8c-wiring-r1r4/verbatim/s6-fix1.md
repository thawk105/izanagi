## 対応結果

[production caller](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2293-fix1/orchestrator/campaign/p3_autonomous_workload_trial.py:1862) に次を結線しました。

- `campaign_output_root`: `producer.evidence_root`
- `origin_run_plan_sha256`: lifecycle start と同じ `runtime.run_plan_sha256`
- `attempt_capability_sha256`: 物理 identity 導出時に埋め込んだ slot capability digest

再計算や新規 digest 生成はありません。

| 所見 | 状態 | 結果 |
|---|---|---|
| originless compatibility | partial | runner は rc=16。test file に自走入口がなく未実走 |
| origin public capability/terminal | partial | 実走したが `P6Unavailable` 期待に対して `FC03` |
| origin public partial/completed | closed | 緑 |
| slot reservation ordering | closed | 緑 |

## 検査

実走した nodeid:

- `orchestrator/tests/test_p3_autonomous_workload_trial.py::test_origin_public_path_preserves_capability_identity_and_projects_terminal` — 赤、`FC03 != P6Unavailable`
- `orchestrator/tests/test_p3_autonomous_workload_trial.py::test_origin_public_result_distinguishes_partial_from_completed` — 緑
- `orchestrator/tests/test_p3_autonomous_workload_trial.py::test_registered_slot_is_reserved_before_first_performance_observation` — 緑

`tools/run_tests.py` に4 nodeidを渡した実行は rc=16で、子は起動しませんでした。`git diff --check` は緑です。

## 波及可能性

静的確認では production caller は修正箇所の1件だけです。

- consumer test の `_materialize_physical_evidence` は33個の canonical layout、`campaign.lock`、layout配下のWALを生成しています。
- 共有 fixture builder は flatなWAL/provenanceのみを生成し、`campaign.lock` を生成しません。
- P3側 `_origin_public_inputs` は共有 fixtureを使いますが、consumer test側の物理 evidence materializationを行っていません。
- そのため今回の結線で `TypeError` を越えた後、既存 fixtureがFC03で拒否されます。
- originless compatibility の origin-enabled比較も同じP3共有 helperを経由します。

禁止事項に従い、fixture、consumer test、期待値は変更していません。

## 編集ファイル

- [orchestrator/campaign/p3_autonomous_workload_trial.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2293-fix1/orchestrator/campaign/p3_autonomous_workload_trial.py:1862)

docs編集、commitは行っていません。

## 総括

3つの必須引数を既存producer値からproduction callerへ結線しました。  
P3指定検査は2件緑、1件赤です。  
赤はTypeErrorではなく、物理campaign lock不在によるFC03です。  
originless指定検査はrunner rc=16かつ自走入口不在のため未実走です。  
残る確認済み赤は1件、未実走は1件です。  
したがって全体状態はpartialです。