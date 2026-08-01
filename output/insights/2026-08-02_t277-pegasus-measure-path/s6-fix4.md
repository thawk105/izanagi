B-f を全面撤去しました。docs 編集・commit は行っていません。

## 撤去内容

行番号は撤去前の位置です。

- 兄弟 driver の拒否呼び出し:
  - `backoff_sweep.py:84,125`
  - `p3_s4_loop.py:623`
  - `p3_s4_loop_sort.py:217`
  - `s6_sort_sweep.py:209,304`
  - `s8a_trigger_coverage.py:111,137,190,209`
  - `s8a_trigger_freq.py:82,125`
  - `s8a_trigger_sweep.py:252,350`
- 共有 helper:
  - `p3_s4_loop.py:80-82`
  - `site_policy.py:74-82`
- subprocess sink 防壁:
  - `buildcache.py:590-603,855-863` の `env_contract` 配線と legacy COMPUTE 拒否
  - `pipeline.py:211-225,669-670` の `_run_trace` 拒否と contract 転送
- screening identity 防壁:
  - `screening_driver.py:22,139-140` の `_REAL_EVALUATE` と identity 判定
- 上記に伴うテスト fixture の `env_contract` 引数・COMPUTE neutralization も撤去しました。

## 削除したテスト

以下の 5 件を削除しました。すべて B-f の正負例だけで、S1/S2/S2b/S3/S5/F1/F2 の検査は含みません。

- `test_legacy_measurement_shared_helper_rejects_compute_only`
- `test_all_legacy_programmatic_measurement_sinks_reject_compute`
- `test_compute_legacy_campaign_with_fake_evaluator_is_wiring_only`
- `test_compute_legacy_campaign_real_build_refuses_before_subprocess`
- `test_compute_legacy_campaign_cache_hit_refuses_before_trace_subprocess`

## 残した scope

- S1/S2: 受理集合と閉じた site→contract 対応は [p3_s4_loop_trigger_gating.py](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t277-pegasus-measure/orchestrator/campaign/p3_s4_loop_trigger_gating.py:285) に維持。
- S2b: Pegasus の `measurement_env` campaign 分離は同ファイルの [299 行](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t277-pegasus-measure/orchestrator/campaign/p3_s4_loop_trigger_gating.py:299) に維持。
- S3: v2 identity の site/prefix、compiler 解決、ambient prefix 束縛は [buildcache.py](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t277-pegasus-measure/orchestrator/campaign/buildcache.py:219) に維持。`pipeline.evaluate` の compiler・prefix 配線も残しています。
- S5: attestation は [loop.py](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t277-pegasus-measure/orchestrator/campaign/loop.py:54) から layout/WAL 前に一度だけ発火し、receipt は summary と trigger provenance へ伝播します。
- no-resume は [p3_s4_loop_trigger_gating.py](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t277-pegasus-measure/orchestrator/campaign/p3_s4_loop_trigger_gating.py:309) に維持。
- F1/F2: 公開 API に `site` はなく、authoritative campaign location は [同ファイル](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t277-pegasus-measure/orchestrator/campaign/p3_s4_loop_trigger_gating.py:444) の返値経路を維持。
- `screening_driver.py` は完全に HEAD 相当です。B-f シンボル、不要 import、dead code は検索上ゼロです。

## 最終差分

指定された凍結 4 ファイルはすべて差分ゼロです。

- `backoff_sweep.py`
- `p3_s4_loop_sort.py`
- `s6_sort_sweep.py`
- `s8a_trigger_sweep.py`

他の B-f 専用 source である `p3_s4_loop.py`、`s8a_trigger_coverage.py`、`s8a_trigger_freq.py`、`screening_driver.py`、`site_policy.py` も差分ゼロです。

```text
 orchestrator/campaign/buildcache.py                | 102 +++++-
 orchestrator/campaign/loop.py                      |  84 ++++-
 .../campaign/p3_autonomous_workload_trial.py       |  15 +-
 orchestrator/campaign/p3_s4_loop_trigger_gating.py | 230 ++++++++++---
 orchestrator/campaign/pipeline.py                  |  24 +-
 orchestrator/tests/test_build_site_gate.py         |  17 +
 orchestrator/tests/test_buildcache_v2.py           | 162 ++++++++-
 orchestrator/tests/test_campaign.py                | 171 +++++++++-
 .../tests/test_p3_autonomous_workload_trial.py     | 132 ++++++-
 .../tests/test_p3_s4_loop_trigger_gating.py        | 380 ++++++++++++++++++---
 10 files changed, 1170 insertions(+), 147 deletions(-)
```

## 検査

通過:

- `python3 -m py_compile` — rc=0
- `git diff --check` — rc=0
- `python3 tools/check_docs.py` — rc=0、違反なし
- `python3 tools/check_codex_agents.py` — rc=0
- docs 差分ゼロ、B-f シンボル検索ゼロ

計算ノード dispatch を試行した nodeid:

- `test_t080_freeze_migration.py::test_source_closure_exact_12_changed_51_unchanged_and_count_negatives`
- `test_p3_s4_loop_trigger_gating.py::{test_site_admission_matrix,test_environment_module_surface_and_default_seams,test_campaign_identity_is_unchanged_for_other_and_split_for_compute,test_fixture_cli_uses_authoritative_layout_and_preserves_legacy_bytes,test_compute_forwards_required_contract_and_records_sink_receipt}`
- `test_campaign.py::{test_m12_pipeline_compute_uses_gxx_for_source_digest_and_v2_builds,test_required_contract_is_attested_once_at_run_campaign_sink}`
- `test_buildcache_v2.py::{test_m7_v2_actual_site_change_is_cache_miss,test_m9_v2_ambient_dependency_prefix_change_is_cache_miss,test_m10_explicit_prefix_is_one_argv_token_and_removes_ambient_env}`

結果は `qstat -Q preflight rc=1`、runner `rc=16`。実走 nodeid は 0 件で、pytest 緑は主張しません。

## 総括

- B-f の兄弟 driver・共有 helper・subprocess sink・identity 判定を全面撤去しました。
- 凍結閉包に抵触した 4 driver は HEAD と差分ゼロです。
- screening と他の B-f 専用 source も HEAD 相当に戻しました。
- S1/S2/S2b/S3/S5/F1/F2 と no-resume は維持されています。
- 静的検査は通過しましたが、pytest は scheduler preflight 障害で未実走です。