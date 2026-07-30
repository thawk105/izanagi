## 実装対象

- `tools/codex_worker_launch.py:新規（予定 1–850）` — CLI、live 監視、process group 終了、receipt、manifest writer、receipt 独立検査を単一ファイルに置く。
- [tools/codex_worker_ledger.py:118–144](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t180-resource-envelope/tools/codex_worker_ledger.py:118) — `--manifest` selector を追加。
- `orchestrator/tests/test_codex_worker_launch.py:新規` — fake Codex executable による launcher 回帰。
- [test_codex_worker_ledger.py:998–1078](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t180-resource-envelope/orchestrator/tests/test_codex_worker_ledger.py:998) — manifest 選択 fixture を追加。
- [docs/dev-wave/operations.md:6–11](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t180-resource-envelope/docs/dev-wave/operations.md:6) — DW-O01 を wrapper 経由へ結線する。
- [test_check_docs.py:2050](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t180-resource-envelope/orchestrator/tests/test_check_docs.py:2050) — DW-O01 が launcher を迂回できない literal pin を追加。

## 1. CLI surface

`tools/codex_worker_launch.py:新規 1–165` に `run` と `check-receipt` の subcommand を置く。

### `run`

| option | 型・既定値 | 契約 |
|---|---|---|
| `--job-id` | 必須、ASCII ID | manifest/receipt の job identity |
| `--prompt-file` | 必須、絶対 path | non-empty UTF-8 regular file |
| `--cwd` | 必須、絶対 directory | Codex `-C` へそのまま渡す |
| `--sandbox` | 必須、`read-only` / `workspace-write` | Codex `-s` へそのまま渡す |
| `--model` | 既定 `gpt-5.6-sol` | 現行 DW-O01 の model を保持 |
| `--reasoning` | 必須、既定なし | 段ごとの既存値をそのまま渡し、launcher が `max` 等を勝手に選ばない |
| `--max-wall-clock-s` | 必須、正の有限 number | retry を含む job 全体の単調時計上限 |
| `--max-model-calls` | 必須、正整数 | job 全 attempt の累積上限 |
| `--max-billable-tokens` | 必須、正整数 | receipt の `cli_reported` 累積上限 |
| `--max-attempts` | 既定 `1`、正整数 | 最初の実行を含む機械的上限 |
| `--artifact-dir` | 必須、絶対 directory | attempt 別 stdout/stderr/output を保存 |
| `--output-file` | 必須、絶対 path | accepted attempt だけを排他的に公開 |
| `--receipt` | 必須、絶対 path | `O_EXCL` で一度だけ作成 |
| `--manifest` | 必須、絶対 path | wave 共通 manifest |
| `--sessions-root` | `$CODEX_HOME/sessions`、未設定時 `~/.codex/sessions` | [ledger:111–115](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t180-resource-envelope/tools/codex_worker_ledger.py:111) と同値 |
| `--codex-bin` | 既定 `codex` | テストでは必ず fake executable の絶対 path |
| `--evidence-grace-s` | 既定 `5.0` | thread ID / rollout 発見の短い race 吸収 |
| `--termination-grace-s` | 既定 `2.0` | SIGTERM から SIGKILL まで |
| `--poll-interval-s` | 既定 `0.1` | live tail 間隔 |

resource limit に数値既定を置かない。stage 別 policy の採用は T-184 所有であり、T-180 は caller に明示を要求する。

生成 argv は `tools/codex_worker_launch.py:新規 430–455` で次に固定する。

```text
codex exec --json
  -m <model>
  -c model_reasoning_effort="<reasoning>"
  -s <sandbox>
  -C <cwd>
  -o <attempt-output>
  <prompt-text>
```

`shell=False`、`stdin=DEVNULL`、`close_fds=True`、`start_new_session=True`。`--ephemeral` は追加しない。

### `check-receipt`

```text
python3 tools/codex_worker_launch.py check-receipt \
  --receipt <receipt.json> --manifest <wave-manifest.json>
```

receipt の strict schema、semantic binding、manifest membership、final output SHA-256、[check_codex_output.py:67–115](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t180-resource-envelope/tools/check_codex_output.py:67) の再実行を行う。

### rc

| rc | `run` | `check-receipt` |
|---|---|---|
| `0` | Codex rc=0、evidence 完備、全上限内、validator rc=0、output/manifest/receipt 永続化済み | accepted receipt と全 binding が有効 |
| `1` | valid receipt はあるが job 非採用。上限停止または attempt 上限消化 | schema は有効だが outcome が非採用 |
| `2` | 引数、spawn、manifest/receipt I/O、validator 自身の異常等の launcher integrity error | receipt 欠損、破損、未知 field、hash/manifest 不一致 |

Codex の生 return code は passthrough せず receipt の `codex_exit_code` に保存する。

## 2. live 強制ループ

`tools/codex_worker_launch.py:新規 300–610` を次の関数構成にする。

- `_consume_stdout_line()` — [events.py:310–332](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t180-resource-envelope/orchestrator/codex_roles/events.py:310) の `parse_jsonl` を一行単位で使い、完全な JSON object だけを解釈する。raw bytes は先に attempt stdout file へ書く。
- `_discover_rollout()` — `thread.started.thread_id` を canonical lowercase UUID として検査し、`sessions_root/**/rollout-*-<session_id>.jsonl` を探索する。0 件は grace 内再試行、2 件以上は evidence invalid。
- `_tail_rollout()` — fd と byte offset を保持し、LF で閉じた行だけを [events.py:273–307](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t180-resource-envelope/orchestrator/codex_roles/events.py:273) の `strict_json_loads` へ渡す。末尾の未完行は buffer と raw file に残す。
- `_update_usage()` — `token_count` の `info` が object の event 数を `model_calls` とする。[ledger:159–193](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t180-resource-envelope/tools/codex_worker_ledger.py:159) と同じ整数・非負検査を行い、最後の有効な `total_token_usage` から `input_tokens - cached_input_tokens + output_tokens` を `cli_reported` として計算する。
- `_terminate_process_group()` — owned process group 全体を TERM→grace 中の drain→KILL→reap する。
- `_run_attempt()` / `_run_job()` — attempt 内実測と job 累積値を分離する。

ループ順序は固定する。

1. `time.monotonic_ns()` で job deadline を確認する。
2. stdout を drain し、最初の thread ID を取得する。異なる ID や重複 event は evidence invalid。
3. rollout を発見して先頭から tail し、`session_meta.session_id` と filename/thread ID の三者一致を要求する。model/effort identity も CLI 引数と照合する。
4. 最新 usage と `model_calls` を job 累積へ反映する。
5. process が既に終了していれば最終 drain 後に評価する。実測が上限以下なら、上限と同値でも正常完了を許す。
6. process が生存中なら、優先順 `wall_clock → model_calls → billable_tokens` で最初の到達理由を latch する。件数・token は `>=` で停止し、次の model call を許さない。
7. latch 後は process group へ SIGTERM。grace 中も stdout/rollout を tail し、最終 actuals を更新する。残存 group へ SIGKILL を送り、leader と descendant を reap する。
8. log・rollout・attempt output を fsync/hash してから receipt を作る。

token は model call 完了後の event でしか観測できないため、一回分の overshoot は不可避であり receipt の final actuals に隠さず残す。

race の扱いは次で固定する。

- thread ID 未到来: wall-clock 監視は継続し、`evidence_grace_s` 到達で group 終了。attempt の `session_id=null`、`evidence_status="missing"`。
- thread ID 到来・rollout 未作成: grace 内は再探索する。作成後は byte 0 から読むため、それ以前の event を失わない。
- process が先に終了: 最終探索・drain を一度行い、それでも thread ID/rollout/session metadata が無ければ非採用。
- malformed usage/JSON: 最後の有効値を証拠として保存するが attempt は accepted にしない。
- limit 検出と自然終了が同じ poll: process 終了を先に確定し、`actual <= limit` だけ正常完了を許す。`actual > limit` は非採用。

retry は prompt bytes、model、reasoning、sandbox、cwd を一切変えず、非採用かつ全累積上限に残量がある場合だけ次へ進む。error text、safety-filter、失敗原因を分類せず、alternate model や backoff も実装しない。

部分出力は attempt ごとの次の三面を削除・上書きしない。

```text
<artifact-dir>/attempt-0001.events.jsonl
<artifact-dir>/attempt-0001.stderr.log
<artifact-dir>/attempt-0001.output.md
```

未完 JSON bytes も raw stdout file に残す。`--output-file` へ公開するのは Codex rc=0かつ validator rc=0 の attempt だけとする。

## 3. receipt exact schema

`tools/codex_worker_launch.py:新規 166–299, 611–760`。全 object は closed field-set、全 field 必須、未知 field・duplicate key・bool-as-int・非有限 number を拒否する。[receipt.py:95–163](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t180-resource-envelope/tools/dev_waves/receipt.py:95) の書き味を踏襲する。

```text
Receipt = {
  schema_version: 1,
  job_id: string,
  prompt_sha256: lowercase-hex64,
  model: string,
  reasoning: string,
  sandbox: "read-only" | "workspace-write",
  cwd: absolute-path,
  artifact_dir: absolute-path,
  output_path: absolute-path,
  output_sha256: lowercase-hex64 | null,
  manifest_path: absolute-path,

  limits: {
    max_wall_clock_s: positive-number,
    max_model_calls: positive-int,
    max_billable_tokens: positive-int,
    max_attempts: positive-int
  },

  actuals: {
    wall_clock_s: nonnegative-number,
    attempt_count: nonnegative-int,
    model_calls: nonnegative-int,
    input_tokens: nonnegative-int,
    cached_input_tokens: nonnegative-int,
    output_tokens: nonnegative-int,
    reasoning_output_tokens: nonnegative-int,
    total_tokens_raw: nonnegative-int,
    cli_reported: nonnegative-int
  },

  outcome: "accepted" | "not_accepted" | "launcher_error",
  stop_reason:
      "completed"
    | "max_wall_clock_s"
    | "max_model_calls"
    | "max_billable_tokens"
    | "max_attempts"
    | "launcher_error",
  launcher_rc: 0 | 1 | 2,

  session_id: canonical-uuid | null,
  codex_exit_code: int | null,
  validator_rc: int | null,

  attempts: [Attempt, ...]
}
```

```text
Attempt = {
  attempt_index: positive-int,
  accepted: bool,
  evidence_status: "complete" | "missing" | "invalid",
  limit_trigger:
      null
    | "max_wall_clock_s"
    | "max_model_calls"
    | "max_billable_tokens",

  wall_clock_s: nonnegative-number,
  session_id: canonical-uuid | null,
  rollout_path: absolute-path | null,
  stdout_path: absolute-path,
  stderr_path: absolute-path,
  output_path: absolute-path,
  output_sha256: lowercase-hex64 | null,

  model_calls: nonnegative-int,
  input_tokens: nonnegative-int,
  cached_input_tokens: nonnegative-int,
  output_tokens: nonnegative-int,
  reasoning_output_tokens: nonnegative-int,
  total_tokens_raw: nonnegative-int,
  cli_reported: nonnegative-int,

  codex_exit_code: int | null,
  validator_rc: int | null
}
```

semantic binding:

- top-level `session_id` / `codex_exit_code` / `validator_rc` は最後の Attempt と一致。
- `actuals.attempt_count == len(attempts)`、token/count actuals は attempt の累積。
- `cli_reported` は常に `input_tokens - cached_input_tokens + output_tokens`。
- `accepted` は最後の attempt が evidence complete、Codex rc=0、validator rc=0、上限内、manifest entry 存在、final output hash 一致の場合だけ。
- retry が複数 session を作るため、top-level singular ID だけに依存せず全 lineage を `attempts` に残す。

永続化は [receipt.py:307–335](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t180-resource-envelope/tools/dev_waves/receipt.py:307) と同じく `O_NOFOLLOW|O_CREAT|O_EXCL`、canonical JSON + LF、file fsync、parent directory fsync。`run` は書いた receipt を再openして `check-receipt` と同じ検査を通した後だけ rcを返す。

## 4. wave manifest

`tools/codex_worker_launch.py:新規 230–360` の exact schema:

```text
WaveManifest = {
  schema_version: 1,
  sessions: [
    {
      job_id: string,
      attempt_index: positive-int,
      session_id: canonical-lowercase-uuid
    },
    ...
  ]
}
```

- 全 field 必須、未知 field 禁止、`sessions` は 1–1024 件。
- `(job_id, attempt_index)` と `session_id` は各々一意。
- thread ID を rollout と照合できた直後に記録する。job が後で非採用になっても削除しないため、費消した全 session が ledger 対象になる。
- thread ID が得られなかった attempt は manifest に入れず receipt に `null` として残す。

並列追記は JSONL の裸 append ではなく、stable lock + whole-document replace とする。

1. `<manifest>.lock` を `O_NOFOLLOW|O_CREAT|O_RDWR` で開き `flock(LOCK_EX)`。
2. lock 内で最新 manifest を bounded strict read。欠損時だけ新規 object を初期化。
3. entry を加え、`(job_id, attempt_index, session_id)` 順に sort。
4. 同一 directory の一意な temp file を `O_EXCL` で作り、canonical JSON + LF を write/fsync。
5. `os.replace(temp, manifest)`、parent directory fsync、unlock。

lock を manifest 本体へ掛けない。replace 後に inode が変わって別 lock へ分裂する race を避けるためである。読者は旧版または新版の完全な JSON のどちらかだけを見る。

## 5. ledger の `--manifest`

[tools/codex_worker_ledger.py:118–144](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t180-resource-envelope/tools/codex_worker_ledger.py:118):

- `--manifest PATH` を非 repeatable option として追加。
- `--manifest` と既存 `--cwd-contains` の同時指定は argparse rc=2。intersection/union の暗黙意味を作らない。
- manifest の strict parser を新設し、launcher と同じ field set、UUID、重複規則を独立に検査する。

[tools/codex_worker_ledger.py:696–752](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t180-resource-envelope/tools/codex_worker_ledger.py:696):

- main 冒頭で manifest allowlist を読む。
- scan 自体は従来どおり全 rollout を行い、各 file の全 `session_meta` を見て allowlist と exact match した file だけ選ぶ。
- 選択対象 file 内の malformed JSON、multiple metadata、duplicate session ID 等は従来どおり issue に残す。
- manifest にある ID が rollout に無ければ `manifest_session_missing` issue。`--strict` なら rc=2。
- structural manifest error、欠損 file、空 `sessions` は `--strict` の有無にかかわらず rc=2。

変更しない境界:

- `--manifest` 未指定時は [ledger:724–752](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t180-resource-envelope/tools/codex_worker_ledger.py:724) の既存 `--cwd-contains` OR/部分一致を同じ branch のまま通す。
- [ledger:552–608](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t180-resource-envelope/tools/codex_worker_ledger.py:552) の totals/public record、[ledger:611–653](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t180-resource-envelope/tools/codex_worker_ledger.py:611) の human output、[ledger:797–816](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t180-resource-envelope/tools/codex_worker_ledger.py:797) の JSON/rc は既存 selector では変更しない。
- 既存呼出しの stdout/stderr bytes を golden 比較し、manifest 機能追加による値・列・issue 順の drift を拒否する。

## 6. DW-O01 結線

[docs/dev-wave/operations.md:6–11](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t180-resource-envelope/docs/dev-wave/operations.md:6) を追記ではなく置換・縮約する。

- raw `codex exec` を `codex_worker_launch.py run` で包む。
- 完了・採用条件を launcher rc=0かつ `check-receipt` rc=0 とする。
- log grep による完了判定禁止、prompt non-empty、stdin close、`check_codex_output.py` の既存条件を維持。
- model は `gpt-5.6-sol`、reasoning/sandbox は [workers.md:5–8](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t180-resource-envelope/docs/dev-wave/workers.md:5) および [workers.md:19–24](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t180-resource-envelope/docs/dev-wave/workers.md:19) の値を明示して渡す。

`docs/dev-wave/**` は現在 23,962 / 24,000 bytes なので、O01 の旧 shell/`.done` 説明を置換して aggregate を増やさない。予算上限変更はしない。

## 7. テスト計画

`orchestrator/tests/test_codex_worker_launch.py:新規 1–180` に `_write_fake_codex()` を置く。各テスト専用の executable Python script を `tmp_path` に生成し、必ず `--codex-bin <absolute-fake>` と一時 `CODEX_HOME` を渡す。fake は argv を検査し、stdout event と rollout JSONL を `flush()+fsync()`、`-o` file を任意タイミングで生成する。実 Codex、network、inference、monkeypatch は使わない。

| nodeid 案 | fixture / 何を kill するか |
|---|---|
| `test_normal_completion_writes_accepted_receipt_manifest_and_output` | 正常 fake。receipt/manifest/output/validator のいずれかを省く変異を kill |
| `test_dw_o01_model_reasoning_sandbox_and_stdin_are_preserved` | `max` と `high` を parameterize。model drift、reasoning 既定化、stdin 未close、`--ephemeral` 混入を kill |
| `test_wall_clock_limit_terminates_leader_and_sigterm_ignoring_descendant` | fake が SIGTERM 無視の descendant を spawnし PID を記録。leaderだけ殺す実装、KILL fallback 欠落を kill |
| `test_model_calls_limit_tails_live_rollout` | N 件 event 後に fake を sleep。stdout usage 依存、off-by-one、counter 無効化を kill |
| `test_billable_limit_uses_input_minus_cached_plus_output` | cached input を大きくした累積 usage。raw input/total token を誤用する実装を kill |
| `test_cumulative_limits_do_not_reset_between_attempts` | attempt 1 と2の合算で limit 到達。attempt ごとの予算 reset を kill |
| `test_max_attempts_never_spawns_attempt_n_plus_one` | 常に非採用の fake と invocation counter。無制限 retry、N+1 off-by-one を kill |
| `test_retry_stops_after_first_accepted_attempt` | 1回目非採用、2回目正常。成功後の余計な retry を kill |
| `test_delayed_rollout_creation_is_polled_from_byte_zero` | thread ID 後に rollout を遅延作成。即時 missing 判定、先頭 event 取りこぼしを kill |
| `test_missing_thread_id_stops_unmetered_process_group` | IDを出さず descendant と sleep。wall limit まで無監視で走る実装を kill |
| `test_missing_rollout_stops_after_evidence_grace` | IDのみ出して sleep。usage 不明を0として受理する実装を kill |
| `test_exact_limit_allows_already_exited_success` | 最終値が上限と同値で直ちにexit。`>=` の無条件事後拒否 race を kill |
| `test_usage_overshoot_after_exit_is_rejected` | 最終 `cli_reported` が上限超過。自然exitを優先して受理する実装を kill |
| `test_partial_stdout_and_attempt_output_survive_group_kill` | fragment と未完 JSON bytes を書いて sleep。削除・上書き・buffer 廃棄を kill |
| `test_malformed_usage_is_not_silently_counted_as_zero` | malformed cumulative usage。fail-open undercount を kill |
| `test_run_refuses_to_overwrite_existing_receipt` | 既存 receipt sentinel。O_EXCL 欠落と既存証拠破壊を kill |
| `test_check_receipt_rejects_missing_unknown_and_duplicate_fields` | literal schema oracle。writer/reader 同時弱化を kill |
| `test_check_receipt_rechecks_output_hash_validator_and_manifest` | receipt 後に各 artifact を個別改変。自己申告だけの受理を kill |
| `test_parallel_jobs_preserve_both_manifest_entries` | launcher 2 process を同一 manifest へ同時投入。lost update、manifest inode lock、非原子的 rewrite を kill |

[test_codex_worker_ledger.py:53–204](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t180-resource-envelope/orchestrator/tests/test_codex_worker_ledger.py:53) の既存 `_materialize()` を流用して次を追加する。

- `test_manifest_selects_exact_ids_when_cwd_is_shared_or_reused`
- `test_manifest_selection_preserves_existing_session_values`
- `test_manifest_missing_session_is_strict_failure`
- `test_manifest_rejects_unknown_fields_duplicate_ids_and_noncanonical_uuid`
- `test_manifest_and_cwd_contains_are_mutually_exclusive`
- `test_without_manifest_stdout_and_stderr_remain_byte_identical`

[test_check_docs.py:2050](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t180-resource-envelope/orchestrator/tests/test_check_docs.py:2050) 付近へ
`test_dw_o01_routes_codex_exec_through_resource_envelope_launcher` を追加し、`codex_worker_launch.py`、receipt 検査、既存 model literal を pin する。

親が実装後に走らせる範囲は launcher/ledger/check-output/check-docs の関連 nodeid、`python3 tools/check_codex_agents.py`、`python3 tools/check_docs.py`。本 read-only 段では未実行であり、緑とは記録しない。

## 択一と provisional 裁定

- 択一: manifest を JSONL append にするか、単一 JSON + stable lock + replace にするか。**推奨は後者** — 並行 lost update と crash 時の中途半端な行を同時に防ぎ、ledger は旧版か新版の完全 object だけを読む。
- 択一: reasoning に launcher 既定を置くか必須引数にするか。**推奨は必須** — plan/consult と implementation で現行値が異なり、共通既定は必ずどこかを変更する。
- 択一: receipt を singular session だけにするか全 attempt を持たせるか。**推奨は top-level terminal ID + `attempts`** — 親 brief の field を保ちつつ retry の全費消を欠落させない。
- (P1)〜(P5) への反対はない。P3 は「全 identity を固定した機械的再実行、累積 envelope、既定1回」、P5 は「attempt artifact を不変保存」と具体化する。
- T-183 候補として返すもの: error text/safety-filter 分類、failure 別 retry 可否、alternate model、backoff、escalation。T-180 には入れない。

## 総括

- **GO** — rollout live tail、closed receipt、原子的 manifest、exact ledger selector を一つの実装境界として確定できる。
- 主要リスクは usage event が model call 完了後にしか来ず、一回分の token overshootを完全には防げないこと。
- thread ID/rollout 欠損は短い grace 後に process group 全体を終了し、0 usage として受理しない。
- DW-O01 の実結線と 24,000-byte aggregate 予算を同時に守らない実装は NO-GO。
- read-only のため実装・pytest は未実施。