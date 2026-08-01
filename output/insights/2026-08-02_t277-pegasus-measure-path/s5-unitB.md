実装単位 B を完了しました。docs 編集・commit は行っていません。単位 A の所有ファイルも編集していません。pytest は Pegasus scheduler の preflight 障害により未実走で、緑は主張しません。

### 変更ファイルごとの差分要旨

- [p3_s4_loop_trigger_gating.py](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t277-pegasus-measure/orchestrator/campaign/p3_s4_loop_trigger_gating.py)
  - 受理集合を `{OTHER, PEGASUS_COMPUTE}` に限定。
  - 閉じた site→tag 対応を追加し、環境変数 override は不採用。
  - Pegasus のみ `search_config["measurement_env"]="pegasus"` を追加。
  - required attestation、receipt 再検算、provenance merge、no-resume gate を実装。
  - compute のみ `env_contract` と dependency prefix を `run_campaign` へ渡す。
- [p3_autonomous_workload_trial.py](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t277-pegasus-measure/orchestrator/campaign/p3_autonomous_workload_trial.py)
  - 解決済み site と env 分離済み campaign identity を `trigger.drive_iteration` へ配線。
  - build は `OTHER` 以外を成果物・provider 作成前に拒否し、8c compute 運転を未開放のまま維持。
- [p3_s4_loop.py](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t277-pegasus-measure/orchestrator/campaign/p3_s4_loop.py)
  - 兄弟 driver 共通の compute 拒否 helper を追加し、自身の build 経路にも適用。
- [p3_s4_loop_sort.py](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t277-pegasus-measure/orchestrator/campaign/p3_s4_loop_sort.py)
  - build 前に共有 helper を呼ぶ。
- [s8a_trigger_sweep.py](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t277-pegasus-measure/orchestrator/campaign/s8a_trigger_sweep.py)
  - sweep 計測開始前に共有 helper を呼ぶ。
- [s8a_trigger_freq.py](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t277-pegasus-measure/orchestrator/campaign/s8a_trigger_freq.py)
  - build・計測準備前に共有 helper を呼ぶ。
- [s8a_trigger_coverage.py](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t277-pegasus-measure/orchestrator/campaign/s8a_trigger_coverage.py)
  - build・計測準備前に共有 helper を呼ぶ。
- [s6_sort_sweep.py](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t277-pegasus-measure/orchestrator/campaign/s6_sort_sweep.py)
  - sweep 計測開始前に共有 helper を呼ぶ。
- [backoff_sweep.py](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t277-pegasus-measure/orchestrator/campaign/backoff_sweep.py)
  - workload 計測開始前に共有 helper を呼ぶ。
- [test_p3_s4_loop_trigger_gating.py](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t277-pegasus-measure/orchestrator/tests/test_p3_s4_loop_trigger_gating.py)
  - AST 契約、受理行列、正負の behavioral 境界、attestation 順序・失敗、receipt merge、env 分離、resume、全兄弟 driver の共有 helper 使用を追加。
- [test_p3_autonomous_workload_trial.py](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t277-pegasus-measure/orchestrator/tests/test_p3_autonomous_workload_trial.py)
  - site 配線と、8c compute build が artifact/provider 前に拒否されることを固定。
- [test_s8a_trigger_sweep.py](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t277-pegasus-measure/orchestrator/tests/test_s8a_trigger_sweep.py)
  - 既存 OTHER fixture を明示。
- [test_s6_sort_sweep.py](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t277-pegasus-measure/orchestrator/tests/test_s6_sort_sweep.py)
  - 既存 OTHER fixture を明示。
- [test_screening_opt_in.py](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t277-pegasus-measure/orchestrator/tests/test_screening_opt_in.py)
  - backoff の既存 legacy fixture を OTHER に固定。

### 受理・拒否挙動

変更前:

- trigger: `OTHER` のみ受理。
- COMPUTE/LOGIN/SUSPECT/未知 site は拒否。
- contract は常に `linux-baremetal`。
- 兄弟 driver は LOGIN/SUSPECT のみ既存 gate で拒否し、COMPUTE は `linux-baremetal` 計測として進み得た。

変更後:

- trigger: `OTHER` と `PEGASUS_COMPUTE` のみ受理。
- LOGIN/SUSPECT/未知 site は behavioral に拒否。
- OTHER は `linux-baremetal` の legacy build。
- COMPUTE は `pegasus` contract、v2 build、required attestation。
- 兄弟 driver は COMPUTE を共有 helper で明示拒否。既存の LOGIN/SUSPECT 拒否と OTHER 挙動は維持。
- 8c build は引き続き OTHER 限定で、compute capability は追加していない。

### Campaign env 分離

Pegasus compute の場合だけ、元 config のコピーへ `measurement_env="pegasus"` を追加します。OTHER では元の `CampaignConfig` 自体を返すため、既定 campaign ID は次のままです。

`p3-s8a-trigger-loop-s8a-trigger-autonomous-3f72ecd5`

テストでは OTHER の config/object/ID が完全不変であることと、Pegasus ID が別になることを独立固定しました。

### Resume gate の mask 回避

既存 loop state を作成したうえで、8c の `_assert_fresh_campaign_state` を no-op にした fixture を使用します。その状態でも trigger 側の `allow_resume=False` 検査だけが `ExecutionGuardError` を発生させ、attestation・`run_campaign`・WAL build stage に到達しないことを固定しました。

### 静的な波及可能性

- `p3_autonomous_workload_trial` は trigger の site-aware campaign identity と trailing `site` keyword を消費。
- `s1_direct_comparison.prepare_cell` は trigger module の構文検査だけを使用するため、計測 routing への影響なし。
- `test_p3_s4_loop.py` は `TRIGGER_LOOP.ENV_TAG` を参照し、定数を残したため互換。
- `test_real_repo_serialization.py` と `conftest.py` は既存 drive nodeid を直列化対象として保持。
- `test_build_site_gate.py` は coverage の内部 build helperを直接検査する。compute 拒否は driver `main` に置いたため既存 site-gate 単体検査は不変。
- `test_screening_opt_in.py`、s8a/s6 sweep fixture は計算ノード実行時にも legacy OTHER 条件を明示するよう追随。
- 単位 A の `run_campaign` / `evaluate` consumer 群、共有 fixture、凍結成果物は変更していない。

### 検査結果

通過した静的検査:

- 変更したコード・テスト14ファイルの `python3 -m py_compile`
- `git diff --check`
- `python3 tools/check_codex_agents.py`
- `python3 tools/check_docs.py`

pytest は2回 dispatchしましたが、いずれもテスト開始前に `qstat -Q preflight rc=1`、runner rc=16 で停止しました。

重点 nodeid:

- `test_site_admission_matrix`
- `test_admit_env_contract_behaviorally_rejects_non_admitted_sites`
- `test_campaign_identity_is_unchanged_for_other_and_split_for_compute`
- `test_required_attestation_order_and_compute_v2_forwarding`
- `test_attestation_failure_stops_before_campaign_and_wal`
- `test_compute_existing_loop_state_rejected_after_neutralized_freshness`
- `test_all_legacy_sibling_drivers_call_single_shared_compute_rejection`
- `test_run_trial_rejects_compute_build_before_artifact_or_provider`

あわせて関連9 test fileと、F42 meta-testの `test_plain_runner_coverage.py` / `test_real_repo_serialization.py` も dispatch 対象にしました。テスト赤ではなく dispatch infrastructure failureで、submodule index lock 由来の偽赤は発生していません。

## 総括

- exact admission、閉じた contract 対応、Pegasus campaign 分離を実装しました。
- OTHER campaign ID と legacy build 呼出しは維持しています。
- required attestation と receipt provenance を実測直前に実発火させました。
- no-resume gate は freshness gate を無効化した条件でも独立して効きます。
- 兄弟 legacy driver は共有 helper で compute を拒否します。
- 8c compute 運転、lease、claim、reservation、`/scr` namespace は追加していません。
- 静的検査は通過、pytest は scheduler preflight 障害により未実走です。