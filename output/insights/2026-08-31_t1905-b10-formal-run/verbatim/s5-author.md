## 総括

実装は完了していますが、pytest は基盤障害で起動できていないため、`closed` とは申告しません。commit は作成していません。

### 変更した file

- [b10_backoff_shape_campaign.sh](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1905-b10-formal-run/tools/pegasus/b10_backoff_shape_campaign.sh:37)
  - git-common-dir から決定的な外部 `official-output` root を導出。
  - `campaigns`、`campaign-locks`、`env/pegasus/claims` を作成。
  - 親環境の値を一度 unset し、`IZANAGI_OFFICIAL_OUTPUT_ROOT` を明示 export。
- [b10_backoff_shape_sweep.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1905-b10-formal-run/orchestrator/campaign/b10_backoff_shape_sweep.py:2800)
  - official root を中央 resolver で解決。
  - claim root を provisioning し、解決済み root 専用の `DurableRootPolicy` を生成。
  - 同じ root を全 `campaign_layout` と `run_campaign` に渡し、policy も注入。
- [test_b10_backoff_shape_sweep.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1905-b10-formal-run/orchestrator/tests/test_b10_backoff_shape_sweep.py:1465)
  - M1/M2/M3 の独立検査と、layout/writer の同一 root 配線検査を追加。

### R1〜R6

- R1: root は nonce 非依存で、全 phase job が同じ git-common-dir から `.../b10-backoff-shape/official-output` を導出。
- R2: shell の repo 内拒否に加え、Python の `resolve_campaign_output_root("official")` を通過必須化。現 checkout の実導出 rootは `/work/1/SFC/tanab/izanagi-job-evidence/b10-backoff-shape/official-output` で、中央 resolver により repo 外と確認済み。
- R3: `campaign_layout` 2箇所と `run_campaign` が同じ `resolved_output` を使用。
- R4: 判定面、`PreregistrationSpec`、grid、統計・曝露・欠測規則、binding field は変更なし。
- R5: correctness/certification/resume/build-WAL gate は変更なし。
- R6: `_write_reports` の `root / "output" / "env" / ENV_TAG / ...` は変更なし。

### 実走したテスト

実走した pytest nodeidはありません。

以下を `tools/run_tests.py` 経由で要求しましたが、いずれも pytest child 起動前に `rc=16`、`child_started=false`、`qstat -Q preflight rc=1` で停止しました。

- 新設4 nodeと既存shell構文検査1 node
- `orchestrator/tests/test_b10_backoff_shape_sweep.py` 全体

したがって、追加検査・既存検査・consumer test はすべて「実装済み・未実走」です。直接の `bash -n` も login-node guard に拒否されたため、迂回していません。

実走できた非pytest検査:

- `python3 tools/check_codex_agents.py`: rc=0
- `python3 tools/check_docs.py`: rc=0
- `git diff --check`: rc=0
- 変更Python 2 fileのAST parse: 成功
- 禁止対象のtracked diff検査: rc=0

### 変異 M1 / M2 / M3

- M1 → `test_t1905_m1_job_exports_official_root_and_missing_env_fails_closed`
  - export 削除だけで赤。理由は official root 未設定。実経路でも中央 resolver が同じ理由で拒否する。
- M2 → `test_t1905_m2_job_root_passes_real_external_and_claim_capability_gates`
  - repo 内 root を実 `resolve_campaign_output_root` に渡すため赤。理由は repository ancestor の存在のみ。
- M3 → `test_t1905_m3_job_root_is_identical_across_phase_job_nonces`
  - nonce 2値から異なる root が得られて赤。理由は相を跨ぐ同一性違反のみ。

M2の外部性とM3の決定性は独立しており、M3の各rootは単体では外部性 gateを通る設計です。無関係な別層による先行拒否はありません。

### 波及可能性

静的に確認した所有外 surface:

- 呼び手・共有機構: `layout.resolve_campaign_output_root`、`env_scope_dir`、`loop.run_campaign`、`DurableRootPolicy`
- 共有fixture: `orchestrator/tests/conftest.py::_isolate_official_output_root_env`
- consumer tests:
  - `test_campaign.py::test_certified_writer_authorization_caller_inventory_is_closed`
  - `test_ccbench_spawn_sites.py` のprocess inventory検査
  - `test_p3_build_authority_cli.py::test_tracked_python_coder_authority_ast_closure_is_exact`
  - `test_official_perf_closure.py::test_official_perf_surface_inventory_is_exact`
  - `test_hooks.py::test_bash_pegasus_registry_schema_and_fixed_classes`
  - `test_condition_meaning_gate.py`
- `submit_b10_backoff_shape.sh` は未変更。job script SHAが変わるため、既存の失敗済みreceipt/jobは再利用せず、land後にfresh submitが必要です。

### 未解決・未実走・懸念

- pytestとconsumer testはdispatch基盤障害により未実走。
- そのため正式走の再投入はまだ行えず、本件は未閉鎖。
- 初期状態から存在した未追跡 `output/insights/2026-08-31_t1905-b10-formal-run/` には触れていません。
- docs、output、patch、submit script、layout/loop等の禁止対象にtracked変更はありません。