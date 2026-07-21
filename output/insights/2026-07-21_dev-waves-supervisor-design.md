# bounded dev-waves supervisor 実装設計案

status: unadjudicated
authority: none
default_effect: no-state-change
as_of_commit: 81080592986e40cecf12a74d740beb474dfe4d71
canonical_state: docs/worklog.md 末尾 + docs/phase3.md + docs/decisions.md

本書は `/loop-w 3` の実装案であり、現行挙動を変更しない。採用後の実装 wave でコード、テスト、
運用正本、決定記録を同時に更新する。ユーザー要件は次の実行鎖である。

```text
interactive Claude session
  /loop-w 3  (project skill: request / observe only)
    -> external Python supervisor daemon
       -> fresh claude -p + /dev-wave (wave 1)
       -> independent verification + local main land confirmation
       -> fresh claude -p + /dev-wave (wave 2)
       -> ... up to max-waves
```

Codex CLI はこの機構を設計・実装する作業者であって、実行鎖には含めない。Codex の Auto / Auto-review
も本 supervisor の権限境界には数えない。

## 1. 結論

この仕組みは作れるし、**タスクごとに context を確実に切る目的には妥当**である。ただし、prompt 内で
`/dev-wave` を自己再帰させたり、同一 session の `/loop` を使ったりするのではなく、各 wave を OS process
単位で分ける。無限ループにはせず、`max-waves`、各 wave timeout、総 deadline、利用予算を必須にする。

v1 の推奨形は次のとおり。

1. project skill は `.claude/skills/loop-w/SKILL.md` に置き、人間だけが `/loop-w N` で起動できるよう
   `disable-model-invocation: true` にする。Claude Code の skill 名制約に合わせ `_` でなく `-` を使う。
2. skill は短命 client として、既に Claude の外で起動済みの Python daemon へ固定スキーマ要求を送る。
   skill 自身は `claude -p` を spawn しない。
3. daemon は wave ごとに exact local main SHA から Git worktree を作り、fresh `claude -p` を stdin
   `/dev/null` で起動する。
4. child の自然言語 final や exit code を信頼せず、構造化 receipt、Git main の状態、commit 集合、
   task-run、worklog、handoff、check 群を独立照合する。
5. 1 条件でも不一致なら次 wave を起動しない。曖昧状態を自動 retry、rebase、merge、force、cleanup で
   「直す」こともしない。
6. supervisor が見た値、実行した argv、状態遷移、判断理由を repo-local の gitignored append-only log
   へ残す。制御 log を書けなければ fail-closed 停止する。

## 2. なぜ daemon を Claude session の外に置くか

Claude Code が Bash tool で起動した shell には `CLAUDECODE=1` が設定される。これは script が Claude
配下であることを検出する公式の印である。skill から直接 Python を起動し、その Python がさらに
`claude -p` を起動すると nested launch になる。動いた環境だけを根拠にこの経路へ依存せず、また
`CLAUDECODE` を unset して制限を迂回しない。

daemon の起動契約は次に固定する。

- 通常 terminal、または人間が明示的に導入した user service から起動する。
- 起動時に `CLAUDECODE=1` を観測したら `nested-launch-environment` で拒否する。
- `/loop-w` は daemon が不在なら自動起動せず、起動コマンドを返して停止する。
- 将来 socket activation を足す場合も、service の導入・有効化は別の明示操作にする。skill が systemd
  設定を無断で作らない。

これにより実行関係は「skill が daemon へ要求を送る」であり、「親 Claude が子 Claude を偽装 spawn
する」ではない。daemon を使わない one-shot mode は通常 terminal からのみ許可し、skill からの実行は
doctor が拒否する。

## 3. 責務分離

### 3.1 `/loop-w` project skill

skill は LLM loop ではなく、request と観測の UI である。

- `$0` を 10 進整数として検査する。v1 は `1 <= N <= 5`。例は `/loop-w 3`。
- 空文字、符号、指数表記、追加引数、上限超過を拒否する。
- daemon の socket と protocol version を確認する。
- `submit` の応答にある `run_id` を表示し、`status --compact` を低頻度で poll する。
- poll は raw child stdout/stderr を親 context に流さず、wave、state、elapsed、reason code だけを返す。
- 親 Claude が compact / disconnect しても run は継続する。後で `/loop-w-status RUN_ID` または CLI
  `status` から再接続できる。
- 完了時は各 wave の before/after SHA、選択 task ID、検査結果、停止理由、runtime log path を要約する。
- cancel は別 skill / 明示 CLI に分け、`/loop-w` の通常経路に曖昧な「止める」を混ぜない。

skill frontmatter の候補:

```yaml
---
name: loop-w
description: fresh claude -p で bounded dev-wave supervisor run を要求し、状態を監視する
argument-hint: <max-waves: 1..5>
disable-model-invocation: true
allowed-tools: Bash(python3 tools/dev_waves.py client *)
---
```

`allowed-tools` はその tool を事前承認するだけで、他 tool を禁止する機能ではない。したがって skill 本文に
「client 以外で実装・Git 操作・child 起動をしない」と書き、settings の deny rule と supervisor の構造
検査を実効境界にする。引数を shell command へ文字列連結せず、Python client の argv 1 要素として渡す。

公式には旧 `.claude/commands/*.md` も動くが、新規実装は supporting files を持てる skill 形式を使う。
既存 `/dev-wave` は当面 command のままでよい。skill と同名 command がある場合 skill が優先されるため、
`loop_w.md` という互換 shim は v1 では作らない。

### 3.2 Python client

client は Unix domain socket へ次の allowlist request だけを送る。

```json
{
  "protocol_version": 1,
  "action": "submit",
  "repo_identity": "<git-common-dir digest>",
  "max_waves": 3,
  "profile": "default",
  "client_request_id": "<uuid>"
}
```

- arbitrary prompt、shell command、path、environment、model 名を request に含めない。
- socket は repo の gitignored runtime directory に置き mode `0600`。
- Linux では `SO_PEERCRED` で接続 UID を daemon UID と照合する。
- request は UTF-8、単一 JSON object、重複 key 不可、NUL 不可、最大 byte 数固定。
- 同一 `client_request_id` の再送は同じ結果を返し、run を二重作成しない。
- v1 は active run があれば `busy` を返す。queue は作らない。

### 3.3 Python supervisor daemon

daemon は唯一の制御主体である。

- repo identity ごとの advisory lock を保持する。ただしこれは supervisor 同士だけの排他であり、repo
  全体や人間の作業を排他したとは主張しない。
- main worktree を `git worktree list --porcelain` から解決する。cwd 推測や固定絶対 path に依存しない。
- main branch、cleanliness、submodule、HEAD、remote refs を各 wave 前後で観測する。
- Git worktree、child worker、receipt、checker、予算、停止判断を直列状態機械として管理する。
- child の出力を instruction として実行しない。次 wave に前 wave の transcript や final を渡さない。
- local main への fast-forward は現行 `/dev-wave` 段 9 の責務とし、supervisor はその実行を独立確認する。
  将来 supervisor 側 land に移すなら D69 と `/dev-wave` を同じ変更で更新する。
- push、remote branch 更新、PR 作成は行わない。

### 3.4 child worker

daemon 本体とは別の小さい worker process が 1 個の `claude -p` を所有する。

- `subprocess.Popen(argv_list, shell=False, stdin=DEVNULL, start_new_session=True)` を使う。
- stdout/stderr は専用 file に直結し、pipe backpressure で child を止めない。
- child PID、process start identity、argv digest、開始/終了時刻、return code を durable な
  `worker-exit.json` に create-only で残す。
- timeout / cancel は process group へ SIGTERM、grace 後 SIGKILL。PID だけでなく start identity を照合し、
  PID 再利用が曖昧なら自動 signal せず停止する。
- daemon が落ちても worker は完了記録を残す。daemon 再起動時は Git 実状態と `worker-exit.json` から
  replay し、成功済み wave を再実行しない。

## 4. 1 wave の具体的な実行

### 4.1 preflight

daemon は child を起動する前に最低限次を確認する。

- `max_waves`、per-wave timeout、total deadline、支出上限が設定済み。
- `claude` の path と version が許容範囲。必要 flag を `--help` probe で確認。
- `-p` では不正な settings が対話なしに無視され得るため、project/local/managed settings と hook 配線を
  child 起動前に独立 parse・検査し、読み込まれたはずだという推測に依存しない。
- main worktree が一意、branch が `main`、tracked/untracked/submodule を含め clean。
- main HEAD を `before_main_sha` として full SHA で固定。
- supervisor 自身の code/config/schema が clean。実行中に code が変わったら次 wave へ進まない。
- runtime directory が symlink でなく、owner/mode、空き容量、file size budget が正常。
- daemon が Claude 配下で起動されていない。
- active worker がいない。回復対象がある場合は新規 submit でなく明示 `resume` を要求。

予算が未指定なら live run を開始しない。`--max-budget-usd` を利用できる認証形では per-wave 上限を child
へ渡し、daemon 側も総額を監視する。subscription 等で正確な金額上限を表せない場合は、max-waves、
deadline、process timeout を必須の代替上限とし、「金額を保証した」とは記録しない。

### 4.2 exact-base worktree

Claude Code の `--worktree -p` は非対話終了時に cleanup されず、既定 base が local main と限らないため
使わない。daemon が次を実施する。

1. `before_main_sha` から branch `supervised/<run-id>/wNNN` を作る。
2. `.claude/worktrees/supervised-<run-short>-wNNN` に worktree を作る。
3. submodule は local object で `update --init --recursive --no-fetch` を試み、network が必要なら停止する。
4. worktree HEAD、branch、cleanliness、submodule SHA を再観測してから child を起動する。

v1 は worktree を自動削除しない。submodule 付き worktree cleanup は共有 config を壊し得るため、成功時も
残存 path を log し、既存 `/cleanup-branches` の人間確認付き手順へ渡す。`submodule deinit` を呼ばない。

### 4.3 child invocation

概念上の argv は次の形とする。実装時は現行 `claude --help` と live doctor で flag を確定する。

```text
claude -p
  --model <pinned-model>
  --effort <pinned-effort>
  --permission-mode auto
  --output-format json
  --json-schema <receipt-schema-json>
  --max-budget-usd <per-wave-budget-if-enforceable>
  --add-dir <resolved-main-worktree>
  /dev-wave --supervised-manifest <absolute-runtime-manifest-path>
```

- child は毎回新しい process で、`--continue` / `--resume` を使わない。
- stdin は必ず `/dev/null`。permission prompt 待ちを成功扱いしない。
- `auto` は child Claude の自動承認モードであり、Codex の Auto とは別物。利用可能性を doctor で確認し、
  unavailable / denied / abort はその wave の停止理由にする。`--dangerously-skip-permissions` へ fallback
  しない。
- slash skill/command は user message の先頭で呼ぶ必要があるため、supervisor 契約を `/dev-wave` より前へ
  prose として置かない。唯一の prompt を `/dev-wave --supervised-manifest <path>` とする。
- manifest は daemon が固定 schema で runtime directory に作り、run ID、wave index、worktree、main path、
  expected base SHA、receipt schema digest だけを持つ。free-text task や shell command は持たせない。
- `/dev-wave` は supervised flag を明示 parse し、manifest を strict validate してから通常段 1〜9 を実行する。
  不明 flag、manifest の owner/mode/path/run/base 不一致では開始しない。
- child が ordinary `git push` を行わないよう project rule、deny hook、Git 設定 tripwire を重ねる。ただし
  任意 script や explicit URL まで含む「push 不可能性」を証明したとは言わない。remote ref の前後比較も
  tripwire であって外部 remote 非変更の完全証明ではない。
- session persistence は debugging と privacy の択一。v1 推奨は `--no-session-persistence` を付けず、
  crash 調査可能性を残す。ただし session ID / URL は private raw log のみに置き、tracked artifact へ
  転記しない。採用時にユーザーが privacy 優先なら flag を反転する。

`/dev-wave` の supervised mode が追加する契約は概念上、次だけである。

```text
この process ではちょうど 1 wave 実行する。
開始基準 main は <full sha>。対象は worklog の current next action から選ぶ。
段 9 の local main ff-only 取り込みまで完了するか、閉じた stop reason で停止する。
次 wave を開始せず、schema v1 receipt だけを最終出力する。
```

### 4.4 child receipt

receipt は child の**主張**であって、単独の成功証拠ではない。

```json
{
  "schema_version": 1,
  "supervisor_run_id": "...",
  "wave_index": 1,
  "outcome": "completed",
  "stop_reason": "wave-completed",
  "base_main_sha": "40-hex",
  "landed_main_sha": "40-hex",
  "selected_task_ids": ["T-005"],
  "next_task_ids": ["T-004", "T-001"],
  "landed_commits": ["40-hex"],
  "child_task_run_id": "..."
}
```

`outcome` は `completed | no-actionable-task | user-ruling-required | blocked | failed` の閉集合。
`stop_reason` も schema enum にする。unknown field、重複 key、NaN、NUL、invalid UTF-8、size 超過、
base/run/wave 不一致を拒否する。`completed` 以外では `landed_main_sha` と `landed_commits` を null/空に
固定し、main が動いていたら不整合として停止する。

## 5. 独立 verification gate

`completed` を次 wave へ進めるには、少なくとも次をすべて満たす。

1. worker の structural exit record が存在し、return code 0。log grep で完了判定しない。
2. Claude CLI の single-result JSON envelope が strict parse でき、その structured output 部分が receipt
   schema に適合する。envelope の自然言語 `result` field を receipt の代替にしない。
3. receipt の run ID、wave index、base SHA が daemon の固定値と一致。
4. main worktree が依然 `main`、clean、submodule clean。
5. `after_main_sha != before_main_sha`。
6. `git merge-base --is-ancestor before after` が真。diverge、rewind、same-head は拒否。
7. `git rev-list --reverse before..after` の集合と順序が receipt の `landed_commits` と完全一致。
8. wave branch の監査済み tip と main after の関係が `/dev-wave` 段 9 の契約どおり。
9. selected task ID が wave 前 worklog の「次の一手」に存在し、wave 後 worklog で消化または保存則に従い
   引き継がれた。自然言語の意味的完了を supervisor が完全証明したとは主張しない。
10. child task-run が pilot 中なら `finished/completed` で、run ID が receipt と一致。task-run v1 は writer
    failure=fail-open の観測台帳なので、supervisor の制御 WAL や唯一の受入証拠にはしない。pilot 終了後も
    receipt と Git gate だけで動ける設計にする。
11. `python3 tools/check_codex_agents.py`、`python3 tools/check_docs.py`、関連受入テスト、commit 後の
    `python3 tools/check_ai_provenance.py` が記録どおり green。
12. active handoff の漏れがなく、worklog 最新 entry が前進。
13. supervisor code/config/schema の digest が wave 中に変わっていない。
14. remote ref snapshot と Git remote config に予期しない変化がない。これは push 防止の tripwire と明記。

`no-actionable-task` と `user-ruling-required` は正常停止だが、次 wave は起動しない。`blocked` / `failed`、
receipt 不在、検査不一致、main の外部移動も同じく fail-closed 停止する。

## 6. 状態機械

```text
CREATED
  -> PREFLIGHT
  -> READY
  -> WAVE_PREPARED
  -> CHILD_RUNNING
  -> CHILD_EXITED
  -> VERIFYING
  -> WAVE_ACCEPTED
       -> READY                 (accepted < max-waves and next task exists)
       -> COMPLETED             (max-waves reached)

any nonterminal state
  -> STOPPING
  -> BLOCKED | FAILED | INTERRUPTED
```

制約:

- durable event を先に append し、fsync が成功してから外部 side effect を起こす。
- 同時に `CHILD_RUNNING` は 1 個だけ。
- `WAVE_ACCEPTED` event が無い wave の次を始めない。
- terminal state から自動遷移しない。
- crash recovery は WAL replay と実状態の reconciliation。曖昧なら `AMBIGUOUS` 相当の terminal stop。
- main が既に land 済みで daemon が判断前に落ちた場合、Git と receipt が一致すれば同じ wave を
  `WAVE_ACCEPTED` に確定できるが、child を再実行しない。

主な closed reason code:

- preflight: `invalid-args`, `daemon-busy`, `nested-launch-environment`, `main-not-found`,
  `main-not-clean`, `main-moved`, `code-dirty`, `claude-unavailable`, `flag-unavailable`,
  `budget-invalid`, `runtime-io-failure`
- worker: `spawn-failed`, `permission-abort`, `timeout`, `nonzero-exit`, `log-limit`,
  `output-invalid`, `receipt-invalid`
- verification: `main-unchanged`, `main-dirty`, `main-not-ff`, `commit-mismatch`,
  `task-run-incomplete`, `worklog-invalid`, `handoff-leaked`, `check-failed`,
  `provenance-failed`, `submodule-dirty`, `remote-ref-changed`
- control: `wave-completed`, `max-waves-reached`, `no-actionable-task`,
  `user-ruling-required`, `signal-received`, `ambiguous-recovery`

## 7. 「何を見て、何をしたか」の log

### 7.1 保存場所

tracked log を main に追記すると自分で clean gate を壊す。したがって次を `.gitignore` へ追加する。

```text
output/dev-wave-supervisor/runtime/
```

run ごとの構成:

```text
output/dev-wave-supervisor/runtime/<run-id>/
  manifest.json                 create-only, sanitized configuration
  events.jsonl                  append-only control WAL
  status.json                   atomic replace の derived cache
  summary.md                    derived human view
  waves/001/
    prompt.txt                  private exact generated prompt
    stdout.json                 private raw Claude output
    stderr.log                  private raw stderr
    worker-exit.json            create-only structural completion record
    receipt.json                strict parse 後の sanitized receipt
    checks.json                 expected / observed / result
```

directory は `0700`、file は `0600`。symlink、hardlink、owner 不一致を拒否する。v1 は自動削除せず、
ユーザーが明示 export / purge するまで残す。追跡可能な insight へ export するときは session ID、URL、
credential、raw prompt/output を除いた sanitized summary だけを新規 file として作る。

### 7.2 event envelope

各 JSONL record は少なくとも次を持つ。

```json
{
  "schema_version": 1,
  "seq": 17,
  "event_id": "uuid",
  "run_id": "uuid",
  "wave_index": 1,
  "wall_time_utc": "2026-07-21T...Z",
  "monotonic_ns": 123,
  "actor": "supervisor",
  "event": "invariant_checked",
  "data": {
    "name": "main_is_descendant",
    "expected": true,
    "observed": true,
    "result": "pass"
  }
}
```

record type は `run_created`, `lock_acquired`, `preflight_observed`, `worktree_created`,
`child_spawn_prepared`, `child_spawned`, `child_heartbeat`, `child_exit_observed`, `output_parsed`,
`invariant_checked`, `wave_decision`, `budget_updated`, `signal_received`, `run_finished` の閉集合から始める。

特に残すもの:

- 実行 argv の allowlisted 表現と argv digest。secret 値は digest にも入れず `<redacted>`。
- cwd、resolved main/worktree path、before/after full SHA、branch、status porcelain の digest と要約。
- 各 subprocess の PID identity、開始/終了、return code、timeout/kill の signal と時刻。
- check ごとの command ID、期待値、観測値、rc、stdout/stderr artifact path と digest。
- receipt parse の schema version と validation errors。
- 継続/停止判断と唯一の closed reason code。
- 60 秒程度の heartbeat。全文ではなく elapsed、raw file byte 数、deadline 残だけ。

残さないもの:

- environment 全 dump、API key、auth token、credential path の内容。
- raw session URL / session ID を sanitized manifest、events、summary へ転記すること。
- raw stdout/stderr や prompt の tracked artifact 化。
- child final の文を supervisor の instruction として再利用すること。

### 7.3 durability と fail-closed

- append は partial write を処理して 1 record 全体を書き、`fsync(file)` する。新規 file/dir 作成時は親
  directory も fsync。
- line size、総 log size、raw stdout/stderr size に上限を置く。
- JSON encoder は NaN を拒否。decoder は duplicate key を拒否。
- WAL append/fsync が失敗したら新しい side effect を始めない。child 実行中なら停止 event を可能な別
  emergency file に残す試行後、process group を終了し、次 wave は起動しない。
- `status.json` と `summary.md` は WAL から再生成できる cache。これらの存在だけで完了を判断しない。
- `events.jsonl` の hash chain は v1 の正直だがバグりうる producer 境界には過剰なので入れない。
  append-only は API/挙動契約であり、改竄不能とは呼ばない。

## 8. crash / signal / resume

- daemon 起動時に active run を WAL から列挙し、worker-exit、PID identity、Git main/worktree を照合する。
- worker が生存中なら observer へ復帰する。見えない PID namespace 等で生存を証明できなければ停止。
- worker が終了済みなら receipt parse と verification を再開する。
- main land 後、`wave_decision` 前の crash は同じ child を再実行しない。
- side effect の実行有無を証明できない event gap は自動補完しない。`ambiguous-recovery` で停止し、人間へ
  expected/observed/artifact path を返す。
- SIGINT/SIGTERM は `signal_received` を書き、child group を止め、terminal record を書く。daemon 自身だけ
  終了して orphan child を残さない。
- `resume RUN_ID` は同一 run の reconciliation だけを行う。failed wave の「もう一回」は新規 run とし、
  同じ branch/worktree を暗黙再利用しない。

## 9. resource bounds

v1 の hard bounds 候補:

- `max_waves`: 必須、1..5。通常値 3。
- `per_wave_timeout`: 必須。初期候補 4 時間。
- `total_deadline`: 必須。N=3 の初期候補 12 時間。ただし各 wave timeout の単純加算以上にはしない。
- raw stdout + stderr: wave ごと 64 MiB 候補。超過時 terminate。
- runtime directory: run 全体上限と事前空き容量 gate を設ける。
- cost: enforceable な認証形では per-wave と total の両上限を必須。具体的な USD 値はユーザーが指定する。
- retry: v1 は 0。API 一時失敗も自動で次 child を作らない。resume / new run は明示操作。

値は pilot 実測前の候補であり、決定ではない。特に金額を推測 default にしない。

## 10. CLI surface

```text
python3 tools/dev_waves.py doctor [--live]
python3 tools/dev_waves.py serve --repo-root <path>
python3 tools/dev_waves.py client submit --max-waves N --profile default
python3 tools/dev_waves.py client status RUN_ID [--compact|--json]
python3 tools/dev_waves.py client cancel RUN_ID
python3 tools/dev_waves.py validate RUN_ID
python3 tools/dev_waves.py resume RUN_ID
python3 tools/dev_waves.py export RUN_ID --output <new-sanitized-path>
```

`doctor` の既定は model を呼ばない。`--live` も実装時に「課金なしで可能な CLI capability probe」と
「実 API call」を別 flag に分け、名称で誤認させない。`cancel`、`export`、service install、purge は
`/loop-w` 本体から自動実行しない。

## 11. 実装ファイル案

```text
.claude/skills/loop-w/SKILL.md
.claude/skills/loop-w/scripts/client.py       # thin, socket protocol only
tools/dev_waves.py                            # CLI entrypoint
tools/dev_waves/__init__.py
tools/dev_waves/cli.py
tools/dev_waves/protocol.py
tools/dev_waves/schema.py
tools/dev_waves/schema_v1.json
tools/dev_waves/ledger.py
tools/dev_waves/daemon.py
tools/dev_waves/worker.py
tools/dev_waves/git_state.py
tools/dev_waves/receipt.py
tools/dev_waves/checker.py
tools/dev_waves/redaction.py
output/dev-wave-supervisor/README.md          # tracked operational contract
orchestrator/tests/test_dev_waves_*.py
```

skill は短く保ち、壊れやすい処理は test 可能な Python へ置く。stdlib を基本とし、daemon framework を
追加しない。`SKILL.md` に長い状態機械や schema を複製せず `output/dev-wave-supervisor/README.md` を正本
として参照する。

採用実装時には `.claude/commands/dev-wave.md` も更新し、supervised invocation の receipt 契約、run ID、
expected base SHA、stop reason を明示する。通常の対話 `/dev-wave` の挙動は壊さない。

## 12. テスト計画

### 12.1 unit

- request / receipt / event の strict JSON: duplicate key、unknown key、NUL、invalid UTF-8、NaN、size limit。
- ledger partial write、fsync failure、directory fsync failure、derived cache 再生成。
- state transition の全許可辺と全禁止辺。terminal から遷移しないこと。
- redaction: key/token/session URL/environment が sanitized artifact に出ないこと。
- PID identity、timeout、SIGTERM→SIGKILL、worker-exit create-only。
- budget/deadline arithmetic、clock rollback の影響を monotonic clock で受けないこと。

### 12.2 temporary Git repo integration

fake `claude` executable と temp bare remote を使い、課金なしで次を実走する。

- 1 wave success、3 wave success。各回 PID/session marker が異なり前 transcript が次 prompt に無い。
- child nonzero、timeout、grandchild 残存、log cap 超過。
- malformed output、schema-valid だが run/base/wave が違う receipt。
- receipt completed だが same main、diverged main、dirty main、commit 集合不一致。
- main が外部 process で wave 中に前進。rebase/merge せず停止。
- task-run incomplete、worklog ID 保存則違反、handoff 残存、submodule dirty、check 赤。
- child が push を試みたとき tripwire が発火し次 wave を止める。
- daemon crash を child 開始前、実行中、exit 後、main land 後、decision 後の各点へ注入し、resume で
  duplicate child / duplicate land が起きない。
- WAL write failure 直後に次 side effect が無い。
- run 中の二重 submit が `busy`、同一 request ID 再送が idempotent。
- `CLAUDECODE=1` で daemon / one-shot が拒否され、skill client 自体は接続だけ可能。
- cleanup command と `submodule deinit` が supervisor argv に一度も現れない。

### 12.3 mutation matrix

少なくとも次の変異が受理集合または fail-closed 挙動を期待方向へ変えることを確認する。

- receipt だけを信頼する / exit code だけを信頼する / log の「完了」を grep する。
- same HEAD を許す / ancestor 判定を逆にする / commit 順序を集合比較だけに落とす。
- main clean、task-run、worklog、handoff、submodule、provenance の各 gate を 1 個ずつ除く。
- WAL fsync failure を無視する / failure 後も次 wave へ進む。
- malformed JSON を permissive parse / duplicate key last-wins にする。
- timeout 後に親 PID だけ kill し process group を残す。
- nested environment を許す / auto 不可時に dangerous permission mode へ fallback する。
- supervisor code digest の wave 間変化を許す。
- crash-after-land で child を再実行する。
- failed worktree を自動削除または submodule deinit する。

単に診断文字列が変わってテストが赤くなるだけの mutation は kill に数えない。失敗テスト名を記録し、
fixture が単一理由であることを確認する。

## 13. 段階導入

1. **設計裁定**: 本書の open decisions をユーザーが確定。
2. **機械層だけ実装**: fake child、temp repo、全 failure injection。real model 呼び出しなし。
3. **doctor / daemon canary**: daemon 起動、skill submit、status reconnect。child は fake のまま。
4. **real no-op capability probe**: 課金・外部変更の有無を明示して 1 回だけ。
5. **real max-waves=1**: 小さい承認済み task で handoff、task-run、local main land、log を人間監査。
6. **crash drill**: real child を増やさず、凍結 artifact から resume/reconciliation を実測。
7. **real max-waves=3**: それまでの stop reason / log volume / cost を反映した後に初めて許可。

いきなり unattended 3 wave を走らせない。pilot 中は daemon を foreground で起動し、人間が log path と
stop reason を即時確認できるようにする。

## 14. 実装前に必要なユーザー裁定

本設計から分岐する本質的な択一は次の 4 件。

1. **daemon 起動方式**: 推奨は通常 terminal で foreground 起動。user service / socket activation は
   v1 に入れない。
2. **child permission mode**: 推奨は explicit `--permission-mode auto` + repo deny rules。利用不可なら停止。
   dangerous bypass は候補にしない。
3. **session persistence**: 推奨は pilot 中のみ保持し raw private log から追跡可能にする。本運用前に
   privacy と調査可能性を再裁定。
4. **予算値**: max-waves=3 のほか、per-wave / total timeout と enforceable な cost 上限はユーザー指定。

それ以外、特に fail-closed、no push、ff-only、no automatic retry/cleanup、control WAL 分離は安全性の
中核なので択一にしない。

## 15. 公式仕様との対応

- Claude Code の新規 project skill は `.claude/skills/<name>/SKILL.md` が推奨で、`/name` で直接呼べる。
  `.claude/commands` は互換の旧形式。
- skill の `disable-model-invocation: true` は人間だけの起動にでき、`allowed-tools` は事前承認であって
  tool allowlist ではない。
- invoked skill は同一 session の context に残り、auto-compaction 後も一定 budget で再添付される。
  したがって child task context の完全分離には skill 再帰でなく fresh process が必要。
- `claude -p` は非対話 session を開始して終了できる。`/clear` は同じ保存 session の context を空にする
  操作であり、OS process 境界ほど強い fresh-run 証拠にはしない。
- Bash tool 配下には `CLAUDECODE=1` が設定されるので、daemon はこれを nested-launch preflight に使う。

参照:

- https://code.claude.com/docs/en/slash-commands
- https://code.claude.com/docs/en/cli-usage
- https://code.claude.com/docs/en/env-vars
- https://code.claude.com/docs/en/sessions
