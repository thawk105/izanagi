実装は完了しました。コードとテストのみを変更し、docs・凍結 authority・commit には触れていません。ただし指定ランナーが dispatch 前に失敗したため、pytest は未実走です。

現行の受理・拒否挙動は次のとおりです。

- 既定起動は引き続き探索 3 workload のみを受理します。
- holdout を探索 admission に渡す経路は、従来どおり `u4-holdout-workload` で拒否します。
- formal selector は admission より前に、指定された文言で必ず拒否します。
- closed set 外の selector も拒否します。
- formal 専用 Layer-3 枝や新しい admission modeは追加しておらず、正式 run の受理集合は広げていません。

実装内容:

- [producer](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1333-t1310-workload-profile/orchestrator/campaign/p3_autonomous_workload_trial.py)
  - workload entry を `ycsb`・`records`・`threads` に構造化。
  - campaign、perf、descriptor の 3 sink を同じ entry から導出。
  - formal entry は `HOLDOUTS` から生成し、legacy freeze・module 表・arm descriptor digest を束縛。
  - `--workloads` の既定を `DEFAULT_WORKLOADS` に限定。
  - provenance を `load_legacy_freeze` から構築。
  - formal selector を `formal launch is not admissible: effective preregistration unavailable` で fail-closed。
- [consumer](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1333-t1310-workload-profile/orchestrator/campaign/autonomous_trial_completeness.py)
  - descriptor の `scale.records` と `scale.threads` を producer entry から独立再投影。
  - legacy freeze を独立に再ロードし、path・sha256・四 key を再導出。
- 対応テストを追加し、既存 fixture の呼び出し形だけを構造化 entry に追随させました。既存 assertion の期待値は変更していません。

静的検証では、探索 canonical SHA-256 は 3 件とも baseline と完全一致し、formal descriptor digest も rr80=`80501db0…d843`、rr20=`53230b8b…550b` と一致しました。変更 6 file の formal ratio conjunction は両 holdout とも 0 hit、AST parse と `git diff --check` も成功しています。凍結対象の差分はありません。

既存期待値との静的な衝突は、指示どおり変更せず停止対象として残しました。

- `test_t1311_registered_identity_consumes_issued_arm_bytes`
- `test_t1311_registered_workload_binds_proposal_and_all_invocations`
- `test_public_cli_holdout_opt_in_reaches_u4_gate_without_workload_patch`
- `test_m04_programmatic_holdout_reaches_u4_gate_before_unknown_workload`
- land 後の `test_current_repository_gap_reason_snapshot_requires_cross_wave_review`

前四件は旧 flat entry または「formal entry が表にない」という期待です。最後の一件は commit 後に C01 reason が新 source 形へ遷移することによる予測です。

実走は `tools/run_tests.py` 経由で通常選択、collect-only、`--force-dispatch` の3回を試しましたが、すべて `qstat -Q` が rc=1、子 runner が rc=16 で終了しました。したがって実走済み nodeid は 0 件で、結果は「実装済み・未実走」です。

所有外への波及候補は `test_trial_registry.py`、`test_claude_transport.py`、`test_campaign.py`、role-session 系、reflux 系、Layer-3 consumer 系、および共有 `t325_registered_trial` fixture と originless baseline です。

## 総括

- 完了: 裁定 2.1〜2.6、および 2.7 の fail-closed をコード・テストへ実装。
- 未完了: pytest 実走。dispatch 基盤の rc=16 により未実走。
- 実走した nodeid: 0 件。
- 静的検証: baseline hash、formal digest、0-hit、AST、diff check は一致。
- 波及: registry、transport、role-session、reflux、Layer-3 と共有 formal fixture。
- docs・凍結 authority は未変更、commit なし。