## 総括

静的読解の結論は次のとおり。

- **実装面差分 0 で C3b は実行可能。** 現行 `HEAD=8fbcb70a5f4f5c098c13026c425ade66a4d6db23` は plan 時点で tracked/untracked とも clean だった。ただし投入直前に再検査する。
- **未 land commit での official 走行は可能。** submitter と job body が要求するのは、clean な committed `HEAD`、receipt の `source_commit`、job script blob の一致であり、main への ancestor/land 判定はない。
- **新しい producer script は不要。** 既存の live verifier、registry reader、strict JSON readerを一回限りの Python から使えば抽出できる。
- **(P1-3) の 8 種は不完全。** 少なくとも prefix proof の残り 6 key、`kind`・`round`・`cell_id`、`schedule_row_sha256`、post-probe、classification/terminal projection、opaque capability の非永続状態を補う必要がある。
- receipt は `output/insights/2026-09-09_t1851-unit-c3b-floor-range/README.md` 1 本で成立する。ただし exact JSON literal、型、件数、min/max、source path、SHA-256、artifact に無い field を明記する。
- **テスト、Pegasus 投入、pytest は実行していない。緑とは報告しない。**

## 投入手順の実行計画

1. **使い捨て checkout を exact commit で用意する。**

   - `8fbcb70a5f4f5c098c13026c425ade66a4d6db23` の dedicated checkout から、その checkout 内の `tools/pegasus/submit_floor.sh` を直接起動する。
   - real submit では `--repo-root`、`--attempts-root`、`--job-script` override が拒否されるため、別 checkout を指す引数で代用しない。[`submit_floor.sh:78-98`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-unit-c2/tools/pegasus/submit_floor.sh:78)
   - `output/` は実 directoryで、symlink や別実体でないことが必要。[`submit_floor.sh:89-108`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-unit-c2/tools/pegasus/submit_floor.sh:89)

2. **drift を投入直前に確認する。**

   submitter 自身が次を qsub 前に検査する。[`submit_floor.sh:221-285`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-unit-c2/tools/pegasus/submit_floor.sh:221)

   - `git diff --quiet HEAD --`: tracked working-tree bytes 全体。
   - `git diff --cached --quiet HEAD --`: index 全体。
   - `git ls-files --others --exclude-standard`: standard ignore に掛からない untracked。
   - untracked は `output/*` だけ許容し、それ以外を拒否する。

   `.codex/worktrees/` は現在の exclude 規則に無いため、**非空で無視されていない `.codex/worktrees/...` は拒否対象**である。空 directory は Git に列挙されず、ignore 済み path も `--exclude-standard` により見えない。対照的に、現行 common `.git/info/exclude` は `.claude/worktrees/` を除外している。job 内でも `output` を除いた status を再検査する。[`floor_campaign.sh:777-787`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-unit-c2/tools/pegasus/floor_campaign.sh:777)

3. **queue、予算、quota、並走状態を確認する。**

   - `qstat -Q` で `gen_S` が `DIS` / `INA` でないこと、T-139 の pilot/本走が走っていないことを確認する。
   - submitter は `qstat -Q`、`pegasusinfo`、`rbudgetcheck`、`check_quota` の raw stdout/stderr/rc を保存し、どれかが非 0 なら qsub しない。[`submit_floor.sh:335-405`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-unit-c2/tools/pegasus/submit_floor.sh:335)
   - ただし `qstat -Q` が rc=0 で queue を disabled と表示する場合まで submitter は意味解析しない。operator が本文を読む必要がある。
   - policy は `project=SFC`、`queue=gen_S`、`nodes=1`、`floor_walltime_s=36000` でなければならない。[`submit_floor.sh:168-204`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-unit-c2/tools/pegasus/submit_floor.sh:168)

4. **third-party と gflags/glog を先に検証する。**

   - cache root は `/work/1/SFC/tanab/izanagi-thirdparty-cache`。[`pegasus-runbook.md:320-329`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-unit-c2/docs/pegasus-runbook.md:320)
   - `fetch_third_party.py hydrate` は既定で `output/env/pegasus/silo_ladder_rung1/job-staging/thirdparty-src` を作り、成功 JSON の **`.source_root`** にその絶対 path を出す。[`fetch_third_party.py:127-151`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-unit-c2/tools/pegasus/fetch_third_party.py:127)、[`fetch_third_party.py:723-762`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-unit-c2/tools/pegasus/fetch_third_party.py:723)
   - README 上、consumer に渡してよい field は `.source_root` だけで、`.cache_root` ではない。[`tools/pegasus/README.md:308-321`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-unit-c2/tools/pegasus/README.md:308)
   - **floor submitter にはその値を渡す CLI/env seam はない。** submitter は既定 pathを直接 hard-code している。[`submit_floor.sh:519-527`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-unit-c2/tools/pegasus/submit_floor.sh:519)  
     したがって hydrate 後に `.source_root` がこの path と exact 一致することを検査する。custom `--staging-root` は real floor submit には使えない。
   - `floor third-party source root is missing or unsafe` の発生箇所は [`submit_floor.sh:419-423`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-unit-c2/tools/pegasus/submit_floor.sh:419)。その後、3 source の閉集合、pin、全 untracked を含む clean、copy 後の再検査を行う。[`submit_floor.sh:425-516`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-unit-c2/tools/pegasus/submit_floor.sh:425)
   - `fetch_third_party.py verify-deps` で policy の gflags/glog も事前確認する。job 側は HEAD と全 untracked を含む clean を再検査する。[`floor_campaign.sh:1001-1031`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-unit-c2/tools/pegasus/floor_campaign.sh:1001)、[`floor_campaign.sh:1071-1101`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-unit-c2/tools/pegasus/floor_campaign.sh:1071)

5. **`output/claims` を確認する。**

   submitter が `output/claims` を次の条件で provisioning する。[`submit_floor.sh:530-559`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-unit-c2/tools/pegasus/submit_floor.sh:530)

   - symlink component がない。
   - `output/` の containment 内。
   - 既存なら directoryかつ mode exact `0700`。
   - 不在なら `mkdir -m 0700`。
   - dry-run でも作られる。

6. **hydrate 後に dry-run を 1 回行う。**

   `tools/pegasus/submit_floor.sh --dry-run` を実行し、pre-submit、payload staging、claims mode、表示された qsub argv を確認する。dry-run は submission directory と claims を作る副作用があり、third-party root が無ければ staging 自体を飛ばせるため、**hydrate より先の dry-run 成功は投入可能性の証拠にならない**。[`tools/pegasus/README.md:233-247`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-unit-c2/tools/pegasus/README.md:233)

7. **sanctioned wrapper から official を 1 本投入する。**

   `tools/pegasus/submit_floor.sh --confirm-official-floor-run` だけを使う。raw `qsub` を組み立てない。

   - 引数が無い real submit は staging や qsub より前に rc=2。[`submit_floor.sh:84-87`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-unit-c2/tools/pegasus/submit_floor.sh:84)
   - submitter は生成 nonce を `IZANAGI_SUBMISSION_NONCE` と `IZANAGI_CONFIRM_OFFICIAL_FLOOR_RUN` の両方へ入れる。[`submit_floor.sh:632-650`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-unit-c2/tools/pegasus/submit_floor.sh:632)
   - job は設定済み空値と nonce 不一致を build 前に別々の文言で拒否し、一致時だけ approval bit を立てる。[`floor_campaign.sh:545-566`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-unit-c2/tools/pegasus/floor_campaign.sh:545)
   - driver argv は固定 `--mode official`。一致時だけ `--confirm-official-floor-run` を 1 個 append する。[`floor_campaign.sh:1213-1225`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-unit-c2/tools/pegasus/floor_campaign.sh:1213)
   - qsub 成功後に `submit-receipt.json` と request ID を保存する。[`submit_floor.sh:647-723`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-unit-c2/tools/pegasus/submit_floor.sh:647)

8. **job 内の前提を確認する。**

   job body は次を fail-closed で要求する。

   - `PBS_JOBID`、`PBS_O_WORKDIR`、32 桁 nonce、Python 3.10 以上、create-only `/scr`。[`floor_campaign.sh:21-45`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-unit-c2/tools/pegasus/floor_campaign.sh:21)、[`floor_campaign.sh:168-185`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-unit-c2/tools/pegasus/floor_campaign.sh:168)、[`floor_campaign.sh:267-274`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-unit-c2/tools/pegasus/floor_campaign.sh:267)
   - receipt の source commit から読んだ static admission helper。[`floor_campaign.sh:221-265`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-unit-c2/tools/pegasus/floor_campaign.sh:221)
   - submission receipt の exact keys、nonce、job ID、project、queue、node 数、36000 秒。[`floor_campaign.sh:622-710`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-unit-c2/tools/pegasus/floor_campaign.sh:622)
   - 実行 script、commit blob、receipt script hash、current `HEAD` の完全一致。[`floor_campaign.sh:713-775`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-unit-c2/tools/pegasus/floor_campaign.sh:713)
   - qstat の host、start epoch、limit、remaining、hostname、boot ID。[`floor_campaign.sh:789-961`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-unit-c2/tools/pegasus/floor_campaign.sh:789)
   - `gcc`、`g++`、`cmake` の実体と version、gflags/glog build。[`floor_campaign.sh:990-1148`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-unit-c2/tools/pegasus/floor_campaign.sh:990)

   reservation の関係は次のとおり。

   - PBS directive: `10:00:00 = 36000 秒`。[`floor_campaign.sh:2-5`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-unit-c2/tools/pegasus/floor_campaign.sh:2)
   - `attempt_cap = extime 5 × reps 5 + verify 120 = 145 秒`。
   - `per_cell = build 900 + (8 planned + 2 retry) × 145 = 2350 秒`。
   - 12 cell subtotal `28200 秒`、shared dependency prebuild `1800 秒`。
   - `required_s=30000`、`safety_margin_s=600`、minimum envelope `30600 秒`。[`s8b_floor_campaign.py:1545-1588`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-unit-c2/orchestrator/campaign/s8b_floor_campaign.py:1545)
   - driver は scheduler 由来の 36000 秒 reservation に対して 30000+600 を検査し、値を journal の `reservation-preflight` に保存する。[`s8b_floor_campaign.py:7412-7432`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-unit-c2/orchestrator/campaign/s8b_floor_campaign.py:7412)、[`s8b_floor_campaign.py:7577-7603`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-unit-c2/orchestrator/campaign/s8b_floor_campaign.py:7577)
   - 36000−30600=5400 秒の raw headroom。約 900 秒の prologue 見積後は約 4500 秒だが、これは保証値ではない。[`floor_campaign.sh:9-17`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-unit-c2/tools/pegasus/floor_campaign.sh:9)

9. **1 job を待ち、最初の session を早期確認する。**

   - `#PBS -b 1` かつ campaign protocol は 12 cell を直列実行する。多ノード分割しない。
   - pilot の参考所要は約 2894 秒。[`pilot README:27-28`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-unit-c2/output/insights/2026-08-25_t1431-floor-pilot-values/README.md:27)
   - scheduler 待ちは `tools/dev_wave_wait.py compute` を使い、job-result または会計終了行を終端材料にする。ただし rc=0 は job 成功を意味しない。[`pegasus-runbook.md:1191-1237`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-unit-c2/docs/pegasus-runbook.md:1191)
   - journal が現れたら最初の数 session を確認する。全滅なら「継続しても official floor が得られない」として停止報告し、勝手な fresh 再投入はしない。[`phase3-8b-restart-runbook.md:229-234`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-unit-c2/docs/phase3-8b-restart-runbook.md:229)

10. **完走後に evidence を退避する。**

   `run-dir`、binary store、submission directory、job staging の 4 点を hash manifest 付きで repo 外へコピーする。さらに C3b の ordinal receipt を再現可能にするため、**共有 admission root の run 対応 registry、terminal/external evidence、classification claims、marker/attempt-ledger の snapshot も保全する**。これを保全できなければ receipt 作成前に停止する。

## gate 入力の完全列挙

以下で `RUN` は `output/env/pegasus/calibration/s8b-floor-official/<run-id>`、`AR` は `<git-common-dir>/izanagi/s8b-holdout-admission-v1` とする。

| field / 入力 | 消費する述語 | artifact 上の所在と receipt の集約 |
|---|---|---|
| `probe_before.rc`, `stdout`, `stderr`, `competing` | exact 4-key/type gate [`launcher.py:595-613`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-unit-c2/orchestrator/campaign/s8b_floor_attempt_launcher.py:595)、封印発行 [`launcher.py:687-706`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-unit-c2/orchestrator/campaign/s8b_floor_attempt_launcher.py:687)、competing 分岐 [`campaign.py:8876-8901`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-unit-c2/orchestrator/campaign/s8b_floor_campaign.py:8876) | `RUN/journal.jsonl` の `event=session` → `probe_before.*`、`RUN/result.json` → `sessions[].probe_before.*`、`AR/floor-attempt-registry-receipts/external-evidence/<digest>.json` → `probe_before.*`。rc は count/min/max/distinct、bool は distinct/count、stdout/stderr は JSON escaped distinct値・byte length・SHA-256。 |
| pre-probe の exact type、issuer state membership、weak owner identity、post-probe origin seal、`used` | read gate [`launcher.py:709-730`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-unit-c2/orchestrator/campaign/s8b_floor_attempt_launcher.py:709)、one-shot claim [`launcher.py:733-757`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-unit-c2/orchestrator/campaign/s8b_floor_attempt_launcher.py:733) | **artifact key は存在しない。** process-private weak map の状態である。receipt には「直接観測不能。下流 classification/terminal 成立は間接証拠」と明記する。 |
| `probe_after.rc`, `stdout`, `stderr`, `competing`, nullable | capture 後 probe と precedence [`launcher.py:1391-1419`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-unit-c2/orchestrator/campaign/s8b_floor_attempt_launcher.py:1391) | journal/result の `probe_after.*`、external-evidence の `probe_after.*`。未計測の pre-probe competing では null。pre-probe と同じ集約を行う。 |
| `kind`, `cell_id`, `round`, `retry_ordinal` | `measurement_ordinal = 0 if planned else retry_ordinal`、`slot_key=(cell_id, round, measurement_ordinal)` [`campaign.py:8902-8910`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-unit-c2/orchestrator/campaign/s8b_floor_campaign.py:8902) | journal の `session-start` / `session`、result の `sessions[]` と `attempts[]`。kind/cell は distinct、round/retry は count/null count/min/max/distinct。 |
| `slot_id[0..4]` = `freeze_holdout_key`, `configuration_id`, `repetition`, `measurement_ordinal`, `attempt_ordinal` | plan 構成 [`launcher.py:400-445`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-unit-c2/orchestrator/campaign/s8b_floor_attempt_launcher.py:400)、slot membership [`launcher.py:483-493`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-unit-c2/orchestrator/campaign/s8b_floor_attempt_launcher.py:483) | `AR/floor-attempt-registries/<freeze>/<protocol>/registry.jsonl` の genesis `slots[]` と各 event rowの分解 key。**`slot_id` という JSON key はない**ため 5-tuple を再構成する。genesis では 288 slot、`repetition=0..7`、`measurement_ordinal=0..2`、`attempt_ordinal={0}` を static closure として別記する。 |
| `schedule_row_sha256`, `schedule_sha256`, `freeze_sha256`, `protocol_sha256` | plan binding、genesis、reservation照合 [`launcher.py:386-399`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-unit-c2/orchestrator/campaign/s8b_floor_attempt_launcher.py:386)、[`launcher.py:1181-1197`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-unit-c2/orchestrator/campaign/s8b_floor_attempt_launcher.py:1181) | registry genesis/event rows、terminal evidence `attempt_binding.*`、result root、`result.attempt_registry.*`。digest は distinct/countと相互一致を記録する。 |
| `attempt_ordinal` | production reserve/replay は非 0 を拒否 [`registry.py:2532-2541`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-unit-c2/orchestrator/campaign/s8b_attempt_registry.py:2532)、[`registry.py:3681-3688`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-unit-c2/orchestrator/campaign/s8b_attempt_registry.py:3681) | registry genesis/event row `attempt_ordinal`。started/classified/terminal subsetでも distinct `{0}` を要求する。 |
| `retry_ordinal` と `measurement_ordinal` | planned は `None` iff measurement 0、retry は measurement ordinalと等値 [`terminal_evidence.py:1143-1166`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-unit-c2/orchestrator/campaign/s8b_terminal_evidence.py:1143)、durable replayも同じ [`registry.py:1417-1432`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-unit-c2/orchestrator/campaign/s8b_attempt_registry.py:1417) | journal/result `sessions[].retry_ordinal`、terminal evidence `campaign_record.retry_ordinal`、registry row `measurement_ordinal`。3者を slot join して全件等値を記録する。 |
| consumption marker の存在、`attempt_id`, `campaign_run_id`, `manifest_sha256`, `run_relpath`, `cell_id`, holdout/configuration identity | campaign は clean pre-probe 後だけ consume/validate [`campaign.py:8913-8943`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-unit-c2/orchestrator/campaign/s8b_floor_campaign.py:8913)、launcher は v2 schemaとの共存を要求 [`launcher.py:945-966`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-unit-c2/orchestrator/campaign/s8b_floor_attempt_launcher.py:945)、inspector は noncompetingなら有、pre-competingなら無を要求 [`admission.py:6733-6741`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-unit-c2/orchestrator/campaign/s8b_holdout_admission.py:6733) | `AR/measurement-generation-consumed/*.json` と `AR/attempt-ledger.jsonl`。literal `marker_present` key は無く、file/row 存在から導出する。opaque `consumption_marker` object、marker use 時の `repetition`/ordinal 引数は直接保存されない。 |
| reservation `attempt_binding` 12 key | terminal evidence と registry replay | terminal evidence `attempt_binding` の `admission_claim_digest`, `attempt_id`, `campaign_run_id`, `freeze_sha256`, `manifest_sha256`, `protocol_sha256`, `run_relpath`, `schedule_row_sha256`, `schedule_sha256`, `classification_receipt_sha256`, `classification_event_sha256`, `observation_event_sha256`。exact key set は [`terminal_evidence.py:83-100`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-unit-c2/orchestrator/campaign/s8b_terminal_evidence.py:83)。 |
| durable identity `attempt_id`, `cell_id`, `holdout_id`, `configuration_id`, `records`, `threads`, `workload`, `mode`, campaign/run/manifest identity | terminal evidence authoritative identityと durable claim replay [`registry.py:1433-1475`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-unit-c2/orchestrator/campaign/s8b_attempt_registry.py:1433) | result sessions、terminal evidence `campaign_record`、`workload_sha256`、measurement-generation claim、classification claim。workload raw三軸は receipt に複製せず、source path/hashと`workload_sha256`を記録する。 |
| `FloorMeasurementCapture`: `binary`, `records`, `threads`, `clocks_per_us`, kwargs `extime`, `reps`, `workload`, `numactl`, `use_perf`, `holdout_observation_admission` | campaign construction [`campaign.py:8714-8733`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-unit-c2/orchestrator/campaign/s8b_floor_campaign.py:8714)、launcher policy [`launcher.py:1022-1099`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-unit-c2/orchestrator/campaign/s8b_floor_attempt_launcher.py:1022) | manifest/result binaries、sessions、protocol、campaign-start execution receipt、marker/claimへ分散。`FloorMeasurementCapture` object、`clocks_per_us`の直接 run key、opaque observation capability は無い。間接 binding と source contractを明記する。 |
| `classified_at`, terminal `finished_at`, process `pid/starttime/execution_uuid`, `run_start_receipt_sha256` | launcher classification/terminal、registry phase rows | registry `classification.classified_at`、`terminal.finished_at`、`start.started_at/process_identity/run_start_receipt_sha256`、journal `campaign-start`。時刻は count/distinct/lexical min/maxを記録する。 |
| terminal fields `terminal_status`, `raw_output_sha256`, `report_sha256`, `observation_sha256`, `primary_value`, `failure_reason`, `measurement_retry_reason`, `terminal_evidence_sha256` | sealed terminal publish [`registry.py:3397-3412`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-unit-c2/orchestrator/campaign/s8b_attempt_registry.py:3397) | registry terminal rowsと terminal-evidence file。status/reasonは distinct/count、primaryはnull count/min/max、digestは全件対応を記録する。 |
| result v5 exact top-level set | schema branch [`campaign.py:6815-6855`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-unit-c2/orchestrator/campaign/s8b_floor_campaign.py:6815)、contract key set [`floor_contract.py:88-100`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-unit-c2/orchestrator/campaign/s8b_floor_contract.py:88) | `RUN/result.json`。v4 25 keyに `attempt_registry` を加えた集合。official degraded perf receiptがあればさらに `perf_preflight`, `perf_observation`。exact key setをそのまま記録する。 |
| prefix proof 7 key: `schema`, `registry_schema`, `freeze_sha256`, `protocol_sha256`, `schedule_sha256`, `row_count`, `chain_head_sha256` | exact proof validator [`attempt_registry_core.py:287-350`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-unit-c2/orchestrator/campaign/attempt_registry_core.py:287)、capture [`registry.py:1023-1047`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-unit-c2/orchestrator/campaign/s8b_attempt_registry.py:1023) | `RUN/result.json` → `attempt_registry.*`。parent推定の `row_count` だけでは不足。7 key 全部と registry 実体の prefixを照合する。 |
| live inspector の independent proof | reported count/headまで live registryを再生し比較 [`floor_stats.py:1155-1193`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-unit-c2/orchestrator/campaign/s8b_floor_stats.py:1155) | **別 artifact は発行されない。** result proofと registry bytesから一回限りの extractorで再導出し、receiptへ「再導出値」として記録する。 |

## 抽出経路

1. `JOB/floor-driver.stdout` を strict JSON として読み、exact `{"status","run_dir"}`、`status="completed"`、`run_dir` が固定 output root 内であることを再確認する。wrapper の同じ検査は [`floor_campaign.sh:1303-1317`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-unit-c2/tools/pegasus/floor_campaign.sh:1303)。
2. 移動前に submission、job-result、driver stdout/stderr、RUN の `manifest.json`、`journal.jsonl`、`result.json`、registry、参照 terminal/external evidence、markers の path・size・SHA-256 を採る。
3. JSON/JSONL は duplicate key と NaN/Infinity を拒否する一回限りの Python readerで読む。`jq` だけでは duplicate key、非有限値、複数 artifact joinを十分に検査できない。
4. registry pathは `result.freeze_sha256` と `result.protocol_sha256` から  
   `AR/floor-attempt-registries/<freeze>/<protocol>/registry.jsonl`  
   と導出する。[`s8b_attempt_profile.py:530-537`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-unit-c2/orchestrator/campaign/s8b_attempt_profile.py:530)
5. registryは result の `row_count` 行までを prefix とし、末行 `event_sha256 == chain_head_sha256`、全7 proof field、live行数が `row_count` 以上であることを確認する。
6. journal sessionと registry terminalを、次の再構成 slotで joinする。

   `slot=(holdout_id, configuration_id, round-1, 0 if retry_ordinal is null else retry_ordinal, 0)`

7. 次の件数式を検算する。

   - genesis slot数: `12 × 8 × 3 = 288`。
   - `N = pre-probe noncompeting session数`。
   - terminal row数、terminal evidence数、classification claim数、external evidence数、marker数はいずれも `N`。
   - crash/recoveryの無い完走では prefix `row_count = 1 + 5N`。C3a の2 terminal正例が11行だった実測とも一致する。
   - pre-probe competing session集合と marker集合は交わらず、noncompeting session集合と marker集合は一致する。
   - plannedは `retry_ordinal=null`かつ `measurement_ordinal=0`。retryが発火した場合は両 ordinalが同じ非負整数。`attempt_ordinal`は常に0。

8. `s8b_floor_stats.py` は validator APIであって値域抽出CLIではない。ただし live proof再導出は既に実装済みである。registryの公開 readerも全 replayを行う。[`s8b_attempt_registry.py:2436-2463`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-unit-c2/orchestrator/campaign/s8b_attempt_registry.py:2436)  
   よって **repoへ新しい producer scriptを足す必要はない**。複数runを同じschemaで自動集計する要求が生じた時だけ別単位で検討する。
9. `README.md` 内に source hash表、coverage件数、fieldごとの exact type/key set、distinct値、null数、数値min/max、artifact非所在一覧を置く。値部分はJSON literalとして記述する。
10. receiptとREADMEには次の限界文言を逐語で載せる。

> 本 receipt は、記載した commit、Pegasus job、環境 tag、mode、protocol および freeze による fresh default production campaign 1 回で、実際に観測された入力値だけを記録する。列挙値と min/max はこの run の観測集合および標本極値であり、launcher または consumer が受理しうる全値域、未発火分岐、他環境、他 mode、他 commit、将来 campaign の母集合または許容 bound を示さない。

## pin 閉包

- 新規 directory は `output/insights/2026-09-09_t1851-unit-c3b-floor-range/`、receiptは `README.md` とする。`gate-input-values.json` は作らない。
- この exact directory名、README path、`gate-input-values`について tracked `git grep` は既存 pin 0 件だった。
- `FROZEN_MANIFEST` は exact 23 pathの列挙であり、新規 insightをglobで取り込まない。[`test_frozen_artifacts.py:41-88`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-unit-c2/orchestrator/tests/test_frozen_artifacts.py:41)  
  したがって凍結23件、`FORMULA_ID`、既存登録簿の更新は不要。
- `output/insights/` は通常の holdout clean-scan対象である。scanは tracked regular fileと、standard ignore外のuntracked regular fileを列挙し、除外するのは `output/s8b-freeze/` だけ。[`s8b_holdout_freeze.py:124-129`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-unit-c2/orchestrator/campaign/s8b_holdout_freeze.py:124)、[`s8b_holdout_freeze.py:370-385`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-unit-c2/orchestrator/campaign/s8b_holdout_freeze.py:370)
- 走行が書く `result.json`、`manifest.json`、`journal.jsonl` には workload三軸が同一file内に現れるため、置いたまま次の official runを始めると hit 0 要求を破る。runbookも同じ理由で repo外退避を要求する。[`phase3-8b-restart-runbook.md:252-260`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-unit-c2/docs/phase3-8b-restart-runbook.md:252)
- receipt自身で同じ汚染を再現しないため、raw workload objectを転載しない。`workload_sha256`、source path、source SHA-256で束縛する。receipt作成後は既存 real-repository scanで `rr20=[]`, `rr80=[]` を再確認する。
- shared attempt registryは worktree scan外だが、ordinal receiptの一次資料である。briefの4点bundleだけでは registry replayを後日再現できないため、**shared-admission snapshotまたはその完全な参照file群もbundleに追加する必要がある**。これはrepo実装差分ではなく実測bundleの補強である。

## 停止条件

- tracked worktreeまたはindexがdirty、standard ignore外のuntrackedが`output/`外にある。
- `.codex/worktrees/`等が untrackedとして列挙された。
- hydrateの`.source_root`が submitter固定pathと一致しない、3 sourceのどれかがmissing、symlink、pin不一致、dirty。
- gflags/glogのsource、HEAD、clean、compiler/cmakeのいずれかが不成立。
- `output/claims`がdirectoryでない、symlink、modeが0700でない。
- `gen_S`がdisabled/inactive、予算・quota不足、T-139実走と競合する。
- `--confirm-official-floor-run`なし、nonce空、不一致、driverへflagがexact 1個渡らない。
- qsub非0、request ID parse不能、qstat不可視、計算ノードmarker/会計痕跡が確認できない。qsub後のparse不能はjobが存在する可能性があるため再投入しない。
- source commit、実行script、committed blob、receipt hashのどれかが不一致。
- scheduler limitが36000秒でない、または reservation の30000+600秒を満たさない。
- journal最初の数sessionが全滅。RUN中のjobを独断でqdelせず、request IDと状態を報告する。
- claim発行後のcrash、signal、wall timeout、`reservation-lost`。claim前であることを実artifactから証明できない限りfresh再投入しない。[`phase3-8b-restart-runbook.md:302-344`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-unit-c2/docs/phase3-8b-restart-runbook.md:302)
- driverが `rc=0` / `status=completed` でもfloorが全nullまたは非有限。driver単体では起こりうる既知状態である。現wrapperは finite `scale_ref`、`scalar_alt`、全pairを検査してrc=3へ変換する設計なので、その変換が見えなければwrapper未到達または欠陥として停止する。[`floor_campaign.sh:1232-1351`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-unit-c2/tools/pegasus/floor_campaign.sh:1232)
- `job-result.json`が欠落・不正。writer失敗時、driverが成功ならwrapperはなおrc=0で終了する穴がある。[`floor_campaign.sh:1355-1400`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-unit-c2/tools/pegasus/floor_campaign.sh:1355)
- `failure.json`の不在だけを成功証拠にしない。writerはbest-effortかつ最初の失敗だけで、writer自身のrcは握られる。[`floor_campaign.sh:368-408`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-unit-c2/tools/pegasus/floor_campaign.sh:368)
- `job-result.driver_rc != 0`、`mode != official`、source/script/nonce/reservationの不一致。
- result `schema != s8b-floor-result/v5`、v5 exact key集合不一致、`eligible_for_refreeze != true`。
- prefix proof 7 key不正、live registryが短い、末尾head不一致、result proofと再導出proof不一致。
- markerとpre-probe competingの双方向関係不成立。
- planned/retry ordinal join不成立、`attempt_ordinal != 0`、genesis 288 slot閉包不成立。
- terminal/external evidence、classification claim、marker、registry snapshotのいずれかをbundleへ保全できない。
- receiptに実artifactから再導出できない値、fake registry、injected `measure_fn`、pilot値が混入した。

## (P1) への評価

| 項 | 評価 | 根拠 |
|---|---|---|
| P1-1 未land commitでofficial走行 | **支持** | D811は「**別の source commit と script blob hash で再投入する**」と定めるだけでlandを要求しない。[`## D811`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-unit-c2/docs/decisions.md:30932) D926も保証範囲を「**標準投入経路で、その新しい source commit と script blob を明示承認して起動した**」までとする。[`## D926`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-unit-c2/docs/decisions.md:33371) D1161の逐語は「**床値 official 経路の残る閂は output/s8b-freeze-budget-approvals/g1.json の人間による承認だけ**」だが、D1398が「**人間承認は、床値 official 走行の前提条件ではない。走行結果を v2 candidate freeze へ昇格させる段の前提条件**」と限定し、D1161をその意味に限定解釈している。[`## D1161`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-unit-c2/docs/decisions.md:38805)、[`## D1398`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-unit-c2/docs/decisions.md:44337) コードにもmain ancestor gateはない。 |
| P1-2 receiptは`.md` 1本、producerなし | **支持** | 1 run限りでconsumer schemaもなく、既存readerと一回限りのstrict Pythonで全値を再導出できる。`README.md`をreceipt本体にし、exact JSON literalとsource hashを持たせればよい。ただしrepo外bundle manifestとshared-admission snapshotは別途必要。 |
| P1-3 gate入力は親列挙の8種 | **反対** | prefix proofはrow_countを含む7 key、ordinal slotは5軸とschedule digest、campaign wiringはkind/round/cell_id、probeはpost側も消費する。さらにcapability/markerの一部はartifactに保存されない。上の完全列挙へ置換する必要がある。 |
| P1-4 1 job・1 node直列 | **支持** | `floor_campaign.sh`が`#PBS -b 1`、10時間を固定し、floor protocolは12 cellの直列単一テナントを要求する。[`floor_campaign.sh:2-17`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-unit-c2/tools/pegasus/floor_campaign.sh:2)、[`pegasus-runbook.md:1357-1362`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-unit-c2/docs/pegasus-runbook.md:1357) pilot実績約48分に対して余裕もある。 |

## 未解決の問い

- exact freeze/protocol generationのshared admission rootに、現在既存row・marker・claimがあるかは実行時状態であり、静的読解では確定できない。qsub直前に件数とpathをsnapshotする必要がある。
- briefの「4点bundle」と、C3bが必要とするshared registry一次資料の保全が食い違う。本planはshared-admission snapshot追加を必須とする。
- restart runbookには「officialはperfあり形だけ」とする古い記述が残る一方、現コードはdefault probeがunavailableならofficial degraded receiptを受理する。[`s8b_floor_campaign.py:436-456`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-unit-c2/orchestrator/campaign/s8b_floor_campaign.py:436) 実走ではコードのartifactを記録し、この文書差を別途報告する。
- receiptをbranchへcommitするか、briefの「成果物をrepoへcommitしない」をreceiptにも適用するかが曖昧である。いずれでも、raw run artifactはrepo外退避し、receipt自身のholdout clean-scan hit 0を確認しなければならない。