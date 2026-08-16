## 変更内容

段 2 からの裁定変更を反映しました。

- receipt field 追加は不採用。`pre-submit.json`、`submit-receipt.json`、`top_keys` は変更していません。
- 承認 env は literal `1` ではなく、既存 submission nonce と同じ 32 桁 lowercase hex にしました。

変更は指定された 3 ファイルだけです。

- [submit_floor.sh](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1180-pilot-approval/tools/pegasus/submit_floor.sh:9)
  - usage と zero-arity 承認引数を追加。
  - 承認変数を ambient env 非依存の literal `0` で初期化。
  - 承認時だけ `export_spec` に承認 env=`$NONCE` を追加。[該当箇所](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1180-pilot-approval/tools/pegasus/submit_floor.sh:417)

- [floor_campaign.sh](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1180-pilot-approval/tools/pegasus/floor_campaign.sh:346)
  - 承認 env の設定有無を `${VAR+x}` で区別。
  - 設定済みで nonce 不一致なら `write_failure 2 submit_binding` 後に停止。
  - driver argv を配列化し、検証済み承認時だけ flag を末尾に一度追加。[該当箇所](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1180-pilot-approval/tools/pegasus/floor_campaign.sh:968)

- [test_pegasus_floor_tools.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1180-pilot-approval/orchestrator/tests/test_pegasus_floor_tools.py:990)
  - 未承認・承認済み driver argv、nonce export、ambient env、dry-run receipt bytes、不一致 fail-closed、zero-arity を追加・固定。
  - 共有 helper `_submit` / `_successful_submission` は既存呼び出しと互換の optional 引数だけを追加。

## 受理・拒否挙動

| 入力 | 変更前 | 変更後 |
|---|---|---|
| 承認引数なし | nonce のみ qsub export。driver は既存 4 引数で、driver gate が pilot を拒否 | qsub argv、receipt bytes、driver 4 引数とも変更前と一致 |
| 承認引数あり | unknown argument、rc=2 | nonce と承認 env に同値を export。driver 末尾へ承認 flag を一度追加 |
| `--confirm-... true` | 承認 option 自体が不存在 | zero-arity のため `true` が unknown argument、rc=2 |
| 承認 env 未設定 | job は参照しない | 正常受理、driver flag なし |
| 承認 env が nonce と一致 | job は参照せず driver flag なし | 正常受理、driver flag あり |
| 承認 env が空、`1`、`true`、別 nonce | job は参照しない | rc=2、stage=`submit_binding`。build・driver 未起動 |
| dry-run + 承認 | option 不存在 | scheduler-free。未承認時と receipt bytes が完全一致 |

raw `qsub`、driver 直接起動、Python API、承認主体の人間性認証は引き続き scope 外です。

## テスト

実走コマンドは既存の self-runner `python3 orchestrator/tests/test_pegasus_floor_tools.py` です。内部で pytest を起動し、対象ファイル全体を実行します。

- `orchestrator/tests/test_pegasus_floor_tools.py`: **80 passed**
- pytest collect-only: **80 nodeid collected**
- 制約 meta-test `test_plain_runner_coverage.py`: **3 passed**
  - `test_every_test_file_is_self_runnable_or_allowlisted`
  - `test_allowlist_has_no_stale_or_self_runnable_entries`
  - `test_this_metatest_is_itself_self_runnable`

主要な実走 nodeid:

- `test_submit_floor_non_dry_run_success_writes_real_submission_record`
- `test_submit_floor_explicit_confirmation_exports_submission_nonce`
- `test_floor_job_invokes_fixed_pilot_cli_without_bypass[unconfirmed-four-arguments]`
- `test_floor_job_invokes_fixed_pilot_cli_without_bypass[confirmed-flag-appended-once]`
- `test_floor_job_rejects_confirmation_not_bound_to_submission_nonce[empty|literal-one|different-nonce|literal-true]`
- `test_submit_floor_does_not_inherit_ambient_confirmation`
- `test_submit_floor_confirmation_dry_run_preserves_receipt_bytes`
- `test_submit_floor_confirmation_is_zero_arity`
- `test_submit_floor_dry_run_is_scheduler_free_and_writes_exact_receipts`
- `test_submit_receipt_round_trips_through_job_validator[producer-receipt-accepted|different-job-rejected]`
- `test_floor_job_hardens_interpreter`

親が行う段 6 の変異実走、受入全走、repository-wide 検査は未実走です。本結果をそれらの代替とは扱いません。

## bash 構文検査

直接の `bash -n` コマンドは Pegasus 防壁が `floor_campaign.sh` を dispatch-required と判定して拒否しました。防壁は迂回せず、既存テストが subprocess で両方へ正確に `bash -n` を実行しています。

- `test_floor_shell_syntax[submit_floor.sh]`: PASSED
- `test_floor_shell_syntax[floor_campaign.sh]`: PASSED

加えて `git diff --check` は成功しました。

## 所有外への波及可能性

- `certified_writer_admission._FLOOR_KEYS` は receipt の exact key 集合を要求します。receipt schemaを変えていないため受理集合は不変です。
- `orchestrator/tests/certified_writer_fixtures.py` の base receipt fixtureも変更不要です。
- `test_hooks.py` と admission registry上の `submit_floor.sh=local-ok`、`floor_campaign.sh=dispatch-required` は不変です。
- `floor_scoping.sh` は別部分を踏襲しており、今回の承認 seam を消費しません。
- `s8b_floor_campaign.py` の CLI と exact Boolean gate、および `test_s8b_floor_campaign.py` は無編集です。
- shell bytes の変更により、実投入には新しい commit blob とそれに対応する receipt hash が必要です。既存の source/blob 束縛機構が処理します。
- テスト共有 helper の既存 caller は全 80 件の対象ファイル全走で回帰なしを確認しました。

## 変異対応

| 変異 | 赤にするテスト |
|---|---|
| N1 無条件 driver flag | `test_floor_job_invokes_fixed_pilot_cli_without_bypass[unconfirmed-four-arguments]` |
| N2 非空なら承認 | 不一致テストの `literal-one`、`different-nonce`、`literal-true` |
| N3 failure/exitせず続行 | 不一致テスト全ケース。failure 引数または build/driver marker assertion |
| N4 既定値を `1` | `test_submit_floor_non_dry_run_success_writes_real_submission_record` |
| N5 常時 export append | 同上、および ambient 非継承テスト |
| N6 ambient env 初期化 | `test_submit_floor_does_not_inherit_ambient_confirmation` |
| P1 一致時も常時拒否 | `test_floor_job_invokes_fixed_pilot_cli_without_bypass[confirmed-flag-appended-once]` |

## 総括

指定 3 ファイルだけを変更し、commit・docs 編集・scheduler 投入は行っていません。  
未承認経路の qsub argv、receipt bytes、driver 4 引数、Python 呼出し pin は維持されています。  
承認は submission nonce と完全一致する場合だけ driver flagへ変換されます。  
対象テスト全 80 件と制約 meta-test 3 件は緑です。  
段 6 の変異 matrix と親の受入全走は未実走です。