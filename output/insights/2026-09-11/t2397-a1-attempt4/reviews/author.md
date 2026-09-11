## 総括

**実装済み・未実走です。** 固定追補、同一 patched source の関門／build／初回 collection 転送、依存供給、consumer、関連テスト、98行の一回限り probe を追加しました。commit・add・submit・性能 bench・docs 編集は行っていません。

変更ファイル：

- `orchestrator/campaign/paper_story_a1_source.py`、`paper_story_a1_source.v1.json`
- `orchestrator/campaign/paper_story_a1_paired.py`
- `orchestrator/campaign/loop.py`、`pipeline.py`
- `tools/pegasus/paper_story_a1_paired.sh`
- `orchestrator/tests/test_paper_story_a1_paired.py`、`test_paper_story_a1_job_contract.py`、`test_campaign.py`
- `orchestrator/manual_probes/test_t2397_a1_source.py`

旧 policy／prereg／patch は変更していません。独立 reference の期待 tree と実 root／full HEAD を build 直前に照合し、契約なしの dirty 拒否を維持します。SourceEvidence の clean 状態は変更しません。FetchContent は既存 pristine 検査・prebuild・5引数転送を使用します。

検査結果：

- `check_codex_agents.py`、`check_docs.py`、`git diff --check`：成功。
- 途中の Python AST／shell 構文検査：成功。
- 関連 pytest と制約 meta-test：**実走0件**。2回とも `qstat -Q` preflight rc=1、dispatch rc=16、子未起動。
- 最後の shell 構文検査は hook に拒否され、再試行していません。

変異用の対応は次のとおりです。変異自体は未実走です。

| 変異 | 対応 node／単一理由 |
|---|---|
| M1・M2 | `test_t2397_a1_source`：実依存を供給した正例から prefix／patched source だけを脱落 |
| M3 | `test_v3_ccbench_tracked_clean_gate_is_real_and_reason_is_layer_specific_M10`：固定 patch 正例に宣言外ファイル1個 |
| M4 | `test_v3_measurement_runs_one_selected_campaign_but_registers_exact_triple`：campaign の root 転送だけ変更 |
| M5・M6 | `test_a1_amended_exact_configure_consumer_M5_M6`：実 build grammar の root／token を1箇所変更 |
| M7 | `test_a1_detail_all_records_atomic_and_idempotent`、`test_a1_detail_save_exception_preserves_rejection` |
| M8 | `test_a1_amendment_binding_rejects_single_changed_input_M8`：追補／patch binding を1件変更 |

所有外の確認対象は、`buildcache`、`patchharness`、`s8b_expected_materialization`、`s8b_floor_campaign`、`condition_meaning_gate`、共有 fixture／実 repository 分類を持つ `conftest.py`、`test_real_repo_serialization.py`、`test_plain_runner_coverage.py` です。いずれも編集していません。親の追加文書も残しています。

親のレビュー・commit 後、対象 checkout から実行してください。probe の追加環境変数は不要で、dispatcher の `PBS_JOBID`、既存 `hydrate.json`、以下の `probe-head.txt` を読みます。

```bash
git rev-parse HEAD > /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2397-a1-attempt4/probe-head.txt
python3 tools/run_tests.py --force-dispatch orchestrator/manual_probes/test_t2397_a1_source.py -q -s
```

証拠出力先は job directory 配下の `source-probe/<PBS_JOBID>/`。3 workload・全6 arm の関門／trace・perf build／verify を対象とし、bench は呼びません。

関連・全走と独立レビュー、probe の実機確認後の投入コマンド：

```bash
python3 orchestrator/campaign/paper_story_a1_paired.py submit \
  --study-id paper-story-a1-20260901-balanced5-pilot-v1 \
  --expected-head "$(git rev-parse HEAD)" \
  --attempt-root /work/1/SFC/tanab/dev-wave-jobs/dev-wave-paper-story-a1-balanced5-pilot-20260901/measurement/attempt-0004 \
  --third-party-source-root /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2397-a1-attempt4/third-party-hydrated
```

残件は pytest／meta-test／probe の実走、M1〜M8の確認、独立レビュー、親の commit と投入です。成功・closed は主張していません。