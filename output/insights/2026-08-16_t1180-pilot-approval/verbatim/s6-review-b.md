### 所見 1 — 実経路の順序を追加テストが固定していない

主張: 現在の実装順序自体は正しいが、追加テストは断片を望ましい順に再構成しており、実ファイル上の順序を回帰保証していない。

一次証拠 (file:line):

- static admission は `tools/pegasus/floor_campaign.sh:90-95`、承認照合は同 `:351-357`、receipt 厳密検査は同 `:412-499`、driver は同 `:968-978`。現状は正しい。
- `_run_floor_driver_tail` は `_confirmation_binding_fragment()` と `_driver_tail()` をテスト側で連結するだけである。`orchestrator/tests/test_pegasus_floor_tools.py:1029-1034`
- 不一致テストも承認断片の後ろへ synthetic な build/driver marker を置く。実際の build・driver 行は走らない。同 `:2015-2021`, `:2029-2070`
- 既存の full-script admission テストは最初の `/scr` 作成で停止するため、承認照合へ到達しない。同 `:254-324`, `:445-466`

成立条件: build または別の driver 起動 seam が承認照合より前へ移動しても、切り出した断片の後ろに marker を置くテストは引き続き「照合後に停止」を観測できる。これは `docs/failures.md:6486-6498` の F247、実経路でなく切り出し先だけを検査する型の再発である。

成果物への影響: 不一致 env で driver が先に起動すれば、`floor-driver.stdout`、`job-result.json`、床値 pilot 出力が拒否前に生成され、certified レポートの床値と下流の適格集合へ未承認測定が混入しうる。

must-fix か nit か: **must-fix**

推奨 fix: 実 shell の到達テストに加え、少なくとも static admission 呼出し、承認照合、`receipt_rc=0`、dependency build、`driver_argv` 実行の source index を順序固定する。断片テストは値域検査として残してよいが、順序保証には数えない。

### 所見 2 — ambient 非継承テストは qsub から job への seam を渡っていない

主張: テスト名と実装子報告は ambient env が driver に届かないことまで示唆するが、実際には submitter と driver を独立に検査している。

一次証拠 (file:line):

- ambient 値は submitter subprocess にだけ渡す。`orchestrator/tests/test_pegasus_floor_tools.py:1306-1324`
- driver は別の helper を `confirmation=None` で起動しており、捕捉した `qsub -v` から job env を構成していない。同 `:1325-1336`
- 親裁定自身が NQSV の既定 env 継承を未実測としている。`/work/1/SFC/tanab/dev-wave-jobs/t1180-pilot-approval/s4-adjudication.md:52-55,164-165`
- F22 は rc や argv だけでなく実 consumer の解釈まで突合するよう要求する。`docs/failures.md:352-364`

成立条件: NQSV が `-v` 指定外の ambient env も継承する場合、未承認投入は新設照合で `submit_binding` 拒否となり、従来の driver 4 引数経路へ到達しない。nonce 不一致なので誤承認にはならない。

成果物への影響: 安全側の availability 回帰であり、床値実測が 0 件のまま、certified レポートの床値欄が空のままになる。

must-fix か nit か: **nit / 親裁定済み残余リスク**

推奨 fix: 現テストを「submitter argv 非継承」と限定して命名・説明する。別途 T-1180-b で実 scheduler の env bytes を確認するか、捕捉した `-v` から job env を構成する seam テストを追加する。

### 所見 3 — 未承認経路の production 差分には exact 回帰を認めない

主張: 指定された exact 項目は静的差分上すべて保存されている。

一次証拠 (file:line):

- 既定値は ambient 非依存の literal `0`。`tools/pegasus/submit_floor.sh:29-36`
- `export_spec` の初期代入は従来どおり nonce だけで、append は承認時限定。同 `:417-420`
- `qsub_cmd` の語順と引数集合は不変。同 `:429-432`
- `%q` log は同じ `qsub_cmd` を出すため、未承認時は不変。同 `:433-435`
- pre-submit producer と receipt producer は差分外で、key・serialization も不変。同 `:359-377`, `:483-504`
- 未承認 driver は配列の基本 4 引数だけ。同 `floor_campaign.sh:968-978`
- PBS directive は `-A/-q/-l/-b` のまま。同 `:2-5`
- `"$PY" -I -B` の driver literal は配列内へ移っただけ。同 `:968-971`。既存の出現数 pin は `test_pegasus_floor_tools.py:689-702`。
- receipt key 集合は producer、`RECEIPT_KEYS`、`certified_writer_admission._FLOOR_KEYS` で一致する。`test_pegasus_floor_tools.py:36-58`; `certified_writer_admission.py:27-31,177-204`

既存テストの全件検索で、今回の argv・文字列・回数・schema・行構造へ直接波及する集合は次である。

- shell/PBS/Python 回数: `test_floor_shell_syntax`、`test_floor_pbs_directives_match_shared_and_floor_policies`、`test_floor_job_hardens_interpreter`
- env/driver: `test_floor_job_exports_exact_reservation_fields`、`test_floor_job_invokes_fixed_pilot_cli_without_bypass`、`test_floor_job_does_not_swallow_driver_rc`
- submit/receipt: `test_submit_floor_qsub_exports_nonce_without_third_party_cache`、`test_floor_scripts_use_create_only_leaves_and_json`、`test_submit_floor_dry_run_is_scheduler_free_and_writes_exact_receipts`、`test_submit_floor_non_dry_run_success_writes_real_submission_record`、`test_submit_receipt_round_trips_through_job_validator`
- `_driver_tail()` を実行する既存 5 件: `test_floor_driver_failure_propagates_rc`、`test_floor_driver_zero_rc_rejects_missing_w2_floor_metric`、`test_floor_driver_fd_setup_failure_does_not_mark_launch`、`test_floor_job_result_writer_failure_preserves_driver_rc`、`test_floor_job_result_writer_failure_with_successful_driver_keeps_rc_zero`。`test_pegasus_floor_tools.py:2232-2503`
- `_successful_submission` の既存 caller 8 件も optional 引数追加後と互換である。同 `:1231-1243,1417-1618,2078-2106`

`test_hooks.py` の全件検索では path/class pin のみ (`:2572-2604,3277-3304,3700-3748`)。`test_campaign.py` では `test_p2_actual_floor_and_t126_admission_accept_valid_evidence` (`:4943-4977`) が consumer 統合 pin である。

成立条件: 承認引数なし、かつ承認 env が job 側で未設定である通常経路。

成果物への影響: 現差分では receipt の受理集合、driver の未承認 argv、certified writer の floor receipt 受理集合は変化しない。

must-fix か nit か: 該当なし。

推奨 fix: production 修正不要。ただし所見 1 の順序 pin は追加する。

### 所見 4 — shell と既存 consumer に新たな破綻は見つからない

主張: `set -Eeuo pipefail`、trap、変数スコープ、既存 env consumer の観点では差分は堅牢である。

一次証拠 (file:line):

- `${VAR+x}` の存在確認後だけ直接参照するため、未設定変数で `nounset` は発火しない。`floor_campaign.sh:351-357,973-975`
- 不一致は `write_failure` 後の明示 `exit 2` であり、ERR trap による二重記録を起こさない。同 `:181-215,247-265,351-356`
- `driver_argv` は top-level の完全代入であり、関数内の `local` 漏れではない。同 `:968-975`
- 新規 subshell や command substitution は無い。既存 qsub subshellにも承認状態の戻り値を依存させていない。
- `IZANAGI_RESERVATION_*` と `IZANAGI_FLOOR_JOB_STAGING` の export は不変。同 `:740-747,954-955`
- `floor_liveness` は新しい `submit_binding` failure の `stage/message/rc` を既存の汎用経路で回収できる。`floor_liveness.py:104-121,215-253`
- fixture は job script hash を実 bytes から導出し、receipt key は旧集合のまま。`certified_writer_fixtures.py:127-150,260-268`

成立条件: shell 本体内で検証後の承認変数を再代入しないこと。現差分には再代入箇所はない。

成果物への影響: failure 診断、reservation、job staging、receipt admission の値と参照は維持される。F255 の consumer 取り残し型 (`docs/failures.md:6619-6634`) は本差分では再発していない。

must-fix か nit か: 該当なし。

推奨 fix: なし。将来再代入を許すなら、検証結果を内部 boolean に固定して driver append に用いる。

## 総括

production の未承認 qsub argv、receipt schema、driver 4 引数、Python hardening、PBS directive に回帰は見つからない。  
shell の未定義変数、trap 二重記録、subshell 消失、consumer 取り残しも認めない。  
ただし、追加テストが shell 断片を望ましい順に再構成しており、実経路の順序保証だけは成立していないため must-fix とする。  
ambient env の実 scheduler 到達は安全側の残余リスクで、親裁定どおり別実測が必要である。  
制約に従い pytest・編集・ネットワークアクセスは行っていない。