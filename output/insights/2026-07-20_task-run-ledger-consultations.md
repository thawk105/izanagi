# 2026-07-20 task-run 台帳 wave — 逐語凍結 (brief / プラン / 敵対相談 / 裁定 / 実装報告 / 敵対レビュー / fix)

ハイブリッド標準ループの一次資料。要約は worklog / D66。変異台帳 = 2026-07-20_task-run-ledger-mutation-ledger.json

## 1. brief (親)
```
=== brief ここから ===
# brief — task-run 台帳 pilot (AI 開発作業の統計記録)

## scope
- handoff `docs/handoff/2026-07-19-ai-development-observability.md` の実装 (正本仕様。全 8 項目を読むこと)。
  pilot 規模 (10 task run または 2 週間)。全面強制・大規模自動計装はしない
- 成果物: `output/task-runs/` (README + <task-run-id>/task.json + events.jsonl + reports/)、
  append-only writer/validator の CLI (start/event/finish/validate)、`tools/run_tests.py` からの
  test-run 記録 (意味論不変)、集計器、unit テスト + negative control 一式
- docs 正本編集 (docs/README.md 地図・decisions・worklog) と統合 commit は親が行う

## 確定済みユーザー裁定 (handoff §完了した中間成果)
- 生の作業統計は docs/ でなく成果物側 (output/task-runs/) に置く
- commit trailer は既存 AI-Agent のまま。トークン・料金を trailer に追加しない
- 主キーは task_run_id (commit ID 主キー禁止)。commit は後続 event

## 親の事前裁定 (pilot 限り、可逆)
- 記録は fail-open: 台帳へ書けなくてもテスト・作業本体を止めない (劣化は stderr 警告 + 欠測記録)
- git 追跡: task.json / events.jsonl / reports を追跡。秘密・prompt 本文・session URL・料金・生ツール出力は記録禁止
- CLAUDE.md は編集しない (pilot 実証後にポインタ追加をユーザーへ提案)。導線は output/task-runs/README.md を詳細正本とし docs/README.md 地図に 1 行

## 不変条件
- campaign WAL / proof chain と混同されない名称・説明・置き場 (これは開発プロセス観測であり correctness/fitness 証拠ではない)
- validator は fail-closed (壊れた台帳を実際に赤くする。恒真化禁止)、writer は append-only・単調 seq・tz 付き ISO 8601
- token 非開示は null + measurement_source。概算と実測を同一 field に混ぜない
- 既存テスト・check_docs・check_ai_provenance・campaign 系の意味論を一切変えない

## 並列分割の方針
- 2 単位を想定: E1 = core (schema/writer/validator/CLI + テスト)、E2 = run_tests 記録 + 集計器 + テスト。
  ファイル所有は素集合にする。E2 が E1 の API に依存するなら interface を plan で凍結して並列可否を判断
- 実装子はコードとテストのみ編集。docs 編集・git commit 禁止
=== brief ここまで ===
```
## 2. プラン v1 (codex gpt-5.6-sol max / read-only) — 逐語

# 実装プラン案

結論は次のとおりです。

- 実装は `orchestrator/` ではなく `tools/task_runs/` に置く。
- E1/E2 は、下記 API と schema v1 を先に凍結すれば並列着手可能。ただし E2 の実結合テストは E1 到着後。
- `run_tests.py` は環境変数による明示 opt-in とし、通常経路の argv・stdio・pytest 終了コードを変えない。
- task-run validator は campaign WAL と異なり、末尾 truncate を含む破損を一切許容しない。
- task-run は開発プロセス観測であり、campaign correctness / fitness / benchmark proof chain には絶対に使わない。
- 本回答ではファイル編集・テスト実行をしていない。

## 1. 配置の裁定

### 採用案: `tools/task_runs/`

根拠:

- [orchestrator/README.md:10](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/README.md:10) は `orchestrator/campaign/` を探索・評価・WAL/ACID の中枢と定義している。
- [output/README.md:38](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/output/README.md:38) の proof chain は campaign lock/WAL に限定される。
- task-run は workload、variant、fitness、correctness の証拠ではなく、`run_tests.py` や check CLI と同じ「開発運用」責務である。
- `tools/` 直下へ単一巨大スクリプトを置かず、`tools/task_runs/` package と薄い entry point に分ける。

既存実装からは型を共有せず、次の idiom だけを流用する。

- O_APPEND + fsync: [wal.py:41](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/campaign/wal.py:41)
- `fcntl.flock`: [lock.py:41](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/campaign/lock.py:41)
- O_EXCL、部分 write loop、親 directory fsync: [campaign_claim.py:167](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/campaign/campaign_claim.py:167)
- duplicate key、非有限数、BOM、NUL、サイズ制限を持つ strict JSON: [events.py:273](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/codex_roles/events.py:273)
- Draft 7 と closed schema: [layer3_report.py:177](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/campaign/layer3_report.py:177)

campaign の `read_records()` は最終壊れ行を捨てる契約なので流用禁止です。[wal.py:75](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/campaign/wal.py:75)

## 2. schema v1

schema version は task/event 共通で `"task-run/v1"` とする。全 object は `additionalProperties: false`、数値は有限値のみとする。

### `task.json`

| field | 型・制約 | 意味 |
|---|---|---|
| `schema_version` | string、const `"task-run/v1"` | 未知版は拒否 |
| `task_run_id` | string、`YYYYMMDD-<slug>-<8hex>` | 主キー。commit SHA には依存しない |
| `objective` | string、1〜240文字、単一行、URI禁止 | prompt 本文ではない安全な要約 |
| `task_class` | integer、`1 / 2 / 3` | 現行 task-class gate の値 |
| `started_at` | timezone-aware ISO 8601 | writer は UTC `Z` で出力 |
| `base_commit` | lowercase 40 hex | start 時点の `HEAD` |
| `measurement_policy` | 下記 closed object | この run の観測契約 |

`measurement_policy` は全 field 必須とする。

```json
{
  "mode": "pilot",
  "max_task_runs": 10,
  "max_days": 14,
  "writer_failure": "fail-open",
  "token_values": "actual-or-null",
  "token_estimates": "prohibited",
  "sensitive_content": "prohibited",
  "test_recording": "explicit-opt-in"
}
```

終了情報で `task.json` を更新してはならない。終了は `task_end` event のみ。

`task_run_id` の slug は 1〜48 文字の lowercase英数字・ハイフンとし、乱数部は `secrets.token_hex(4)`。objective から自動生成しないことで prompt や秘密の混入を防ぐ。

### `events.jsonl` 共通 envelope

| field | 型・制約 |
|---|---|
| `schema_version` | const `"task-run/v1"` |
| `task_run_id` | task、directory 名と完全一致 |
| `seq` | integer、1 始まりで正確に +1 |
| `timestamp` | timezone-aware ISO 8601 |
| `event` | 下記 9 種のみ |
| `measurement_source` | 下記 closed object |

`measurement_source`:

```json
{
  "timestamp": "system-clock | caller-supplied",
  "duration": "monotonic-clock | timestamp-delta | caller-supplied | not-applicable",
  "metrics": "wrapper-observed | tool-reported | git-observed | caller-supplied | not-exposed | not-applicable",
  "tokens": "api-reported | product-reported | not-exposed | not-applicable"
}
```

event ごとの数量 source が混ざらないよう、timestamp、duration、一般 metrics、token を別々に表す。

### event 固有 field

以下は envelope 以外の必須 field。`stage_id`、`agent_run_id`、`review_id`、`rework_id` は最大64文字の安全な slug。

| event | 必須 field |
|---|---|
| `stage_start` | `stage_id: string`; `stage: planning \| research \| implementation \| test \| review \| documentation \| integration \| other` |
| `stage_end` | `stage_id`; `stage`; `outcome: completed \| failed \| interrupted`; `duration_s: number >= 0` |
| `agent_run` | `stage_id: string|null`; `agent_run_id`; `product`; `model`; `reasoning`; `role: author \| reviewer \| researcher \| manager \| integrator`; `scope: string|null`; `status: completed \| failed \| cancelled \| timed-out`; `duration_s`; `tokens` |
| `test_run` | `stage_id: string|null`; `suite_id`; `suite_kind: targeted \| full \| docs-check \| provenance-check \| static-check`; `duration_s`; `collected/passed/failed/skipped: integer>=0|null`; `exit_status: integer`; `trigger: baseline \| after-change \| after-failure \| final \| review-fix \| unspecified` |
| `wait` | `stage_id: string|null`; `wait_kind: user \| approval \| scheduler \| resource \| tool \| external \| other`; `duration_s` |
| `finding_summary` | `stage_id: string|null`; `review_id`; `review_kind: self \| independent \| user \| automated`; `real/refuted/unresolved: integer >= 0` |
| `commit` | `commit_sha: lowercase 40 hex`; `relation: authored \| integrated \| referenced` |
| `rework` | `stage_id: string|null`; `rework_id`; `cause: test-failure \| review-finding \| requirement-change \| integration-conflict \| implementation-defect \| other`; `duration_s` |
| `task_end` | `outcome: completed \| blocked \| abandoned \| interrupted` |

単位はすべて秒を表す `duration_s`。イベント timestamp は、duration を持つ event では区間の終了時刻とする。

pytest の `failed` は call failure に加えて setup/teardown error を含める。xfail/xpass は v1 では別計上しないため、4 count の和が `collected` と一致することは要求しない。

### token 契約

`tokens` は次の4 fieldだけを持つ。

```json
{
  "input_tokens": "integer >= 0 | null",
  "output_tokens": "integer >= 0 | null",
  "cached_tokens": "integer >= 0 | null",
  "total_tokens": "integer >= 0 | null"
}
```

意味論:

- `input_tokens` は cached 分を含む総 input。
- `cached_tokens` は `input_tokens` の内数。
- 3値が得られる場合、`total_tokens == input_tokens + output_tokens`。
- `cached_tokens <= input_tokens`。
- `measurement_source.tokens == "not-exposed"` なら4値すべて `null`。
- `api-reported` / `product-reported` なら少なくとも1値は非 null。
- 一部しか開示されない場合、未開示 field は `null` のままにする。
- v1 は概算を禁止する。`estimated_tokens` 等を追加すると closed schema で拒否する。概算導入時は v2 で別 field 群を追加する。

### record 間 invariant

- directory 名、task ID、全 event ID が一致。
- `seq` は `1,2,3,...` の連番。重複だけでなく gap も拒否。
- event timestamp は `started_at` 以後で、seq 順に非減少。等時刻は許容。
- 同時に開ける stage は1件。`stage_end` は現在開いている同じ ID/type を閉じる。
- stage ID の再利用、二重 end、task end 時の未閉鎖 stage を拒否。
- `stage_end.duration_s` が `timestamp-delta` source の場合、start/end timestamp 差と一致させる。
- stage に帰属する wait 区間は stage 内に収まり、互いに重複しない。
- `task_end` は最大1件。
- `task_end` 後は既存 commit の関連付けを可能にするため `commit` だけ許容し、その他の作業 event は拒否。
- commit は0件でもよく、1 task に複数件を許容する。
- stage/test/rework 等が最初の commit より前にあることを正常系として許容する。
- commit SHA を task_run_id や ledger identity として使用しない。

## 3. writer / validator / CLI

### CLI

薄い entry point を次の形にする。

```text
python3 tools/task_run.py start ...
python3 tools/task_run.py event <task-run-id> <event-type> ...
python3 tools/task_run.py finish <task-run-id> --outcome completed
python3 tools/task_run.py validate <task-run-id>
python3 tools/task_run.py validate --all
```

`event` は event 型ごとの argparse subparser とし、任意 JSON や raw command を受け取らない。seq と timestamp は指定不可で writer が付与する。

終了コード:

- `0`: 成功・valid
- `1`: schema/invariant 違反、対象不在、pilot 上限
- `2`: validator dependency 不在、I/O 等で検査自体を完遂不能

検査不能を成功扱いしない。

### create-only / append-only

`start`:

1. task-runs root の directory fd に `flock(LOCK_EX)`。
2. 既存 run を検証し、10 task または最初の run から14日到達なら新規 start を拒否。
3. ID directory を `mkdir` で新規作成。
4. `task.json` と空 `events.jsonl` を `O_CREAT|O_EXCL|O_NOFOLLOW` で作成。
5. partial write loop、file fsync、run directory/root directory fsync。
6. 既存 ID、部分生成物、symlink を上書き・自動削除しない。

`event` / `finish`:

1. `events.jsonl` 自体に exclusive `flock`。
2. lock 内で task と既存全 event を strict validate。
3. 次の seq と現在時刻を確定。
4. compact canonical JSON 1行を `O_APPEND` で追記。
5. fsync 後に lock 解放。
6. lock 待ちは有界。`run_tests.py` は timeout を fail-open warning に変換する。

単一所有契約は採らない。手動 CLI、`run_tests.py`、親 integration が別 process になり得るためである。

### validator の fail-closed 項目

必須検査:

- task/events file の不在、symlink、サイズ超過
- UTF-8不正、BOM、NUL、CR、非 NFC、duplicate JSON key、非有限数
- JSONL の空行、最終 newline 欠落、truncate 行、非 object 行
- 未知 schema version、未知 event、未知/余分 field
- directory/task/event の ID 不一致
- seq 重複、gap、0以下
- timezone 無し、解釈不能 timestamp、started_at より前、逆行
- 負 `duration_s`
- stage pairing、重複 stage ID、重複 end、未閉鎖 stage
- task_end 重複、task_end 後の非 commit event
- token total 不一致、cached 超過、not-exposed と実値の矛盾
- test count、finding count の負値
- commit SHA 不正
- task/event/line サイズ上限

推奨上限:

- `task.json`: 16 KiB
- JSONL 1行: 16 KiB
- `events.jsonl`: 8 MiB、最大10,000 event
- report: 1 MiB
- objective: 240文字

run 内のローテーションや truncate repair は行わない。pilot 終了後は新規 run を止め、10 run または14日分を一つの report に閉じる。

## 4. `run_tests.py` 配線

### 変更してはいけない境界

- command 構築と「ユーザー引数を最後に置く」契約: [run_tests.py:160](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/tools/run_tests.py:160)
- xdist 導入・version gate・直列 fallback: [run_tests.py:181](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/tools/run_tests.py:181)
- warning と command 構築順: [run_tests.py:198](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/tools/run_tests.py:198)
- pytest argv の最終確定: [run_tests.py:208](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/tools/run_tests.py:208)
- child status をそのまま返す地点: [run_tests.py:214](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/tools/run_tests.py:214)

### opt-in 契約

次の環境変数を使う。

- `IZANAGI_TASK_RUN_ID`: 設定時だけ記録を有効化
- `IZANAGI_TASK_RUNS_ROOT`: テスト用 override。既定は `output/task-runs`
- `IZANAGI_TASK_STAGE_ID`: 任意の stage 帰属
- `IZANAGI_TEST_TRIGGER`: trigger。未指定は `unspecified`
- `IZANAGI_TEST_SUITE_ID`: 任意の明示 suite ID

task-run package は `IZANAGI_TASK_RUN_ID` がある場合だけ遅延 import する。jsonschema 不在や import failure が通常の test-runner を壊してはならない。

### 取得点

- suite selection: [run_tests.py:182](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/tools/run_tests.py:182) で取得した `args` から判定。
- full/targeted: [run_tests.py:212](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/tools/run_tests.py:212) の `has_target` と `-k/-m/--lf` 等の selection option から保守的に分類。
- duration: [run_tests.py:214](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/tools/run_tests.py:214) の直前直後を `time.monotonic()` で囲む。
- exit status: 同じ `subprocess.call()` の戻り値。
- collected/pass/fail/skip: [conftest.py:106](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/tests/conftest.py:106) の既存 hook 群の後へ `pytest_sessionfinish` を追加し、controller だけが一時 sidecar に記録。
- trigger: subprocess 開始前に環境変数から読み、event に固定。

suite ID:

- 無選択の全体実行: `pytest-orchestrator-full`
- targeted: 正規化した repo-relative target と selection 条件の SHA-256 先頭12桁を用いた `pytest-targeted-<digest>`
- command、`-k` 式、node 一覧そのものは保存しない。

pytest sidecar は `session.testscollected` と terminal reporter stats だけを保持し、node 名・stdout・stderr を保存しない。xdist worker は書かず controller のみが create-only で書く。

### fail-open

- opt-in 無し: 現行 `subprocess.call(cmd)` をそのまま使う。
- opt-in 有りでも stdin/stdout/stderr は capture/tee せず継承。
- sidecar 不在・破損: duration/exit status は記録し、4 count を `null`、`metrics=not-exposed` として警告。
- ledger append failure: 最小 `test_run` event で一度だけ再試行。なお書けなければ、raw command を含まない定型 warning を stderr に出す。
- いかなる観測失敗でも pytest の元の return code を置換しない。
- ledger 全体が書けない場合、欠測 event 自体も永続化できない。この場合 report の欠測率は下限になるため README/report に明記する。

`docs-check`、`provenance-check`、`static-check` は v1 schema では区別できるが、pilot の自動配線対象は `run_tests.py` だけとする。既存 check CLI は変更しない。

## 5. 集計器

集計前に対象 run をすべて validate する。1件でも壊れていれば report を生成せず非0終了する。壊れた run を警告だけで除外してはならない。

### 時間

task ごとに以下を計算する。

- `lead_time_s = task_end.timestamp - task.started_at`
- `stage_elapsed_s(stage) = Σ stage_end.duration_s`
- `wait_time_s = Σ wait.duration_s`
- `active_time_s(stage) = stage_elapsed_s(stage) - 同 stage に帰属する wait`
- `active_time_s = Σ active_time_s(stage)`
- `unclassified_time_s = lead_time_s - Σ stage_elapsed_s`
- `stage_ratio = active_time_s(stage) / active_time_s`
- `test_time_ratio = Σ test_run.duration_s / active_time_s`

test/agent の並列実行では `test_time_ratio > 1` になり得るため、これは排他的 wall-time 比率ではなく「累積 process-time 比率」と明記する。

stage が1件も観測されていない場合、active を `0` にせず `null` とする。

### テストと手戻り

- full-suite 回数: `suite_kind == full`
- red→green 周回: suite ID ごとに、非0 exit が作る red 状態を次の exit 0 が閉じたとき1周
- red が連続しても1周。green 未到達は `open_red`
- rework 件数、原因別件数、`duration_s` 合計
- trigger 別回数、`unspecified` 率

### agent/token/finding/commit

- agent run 数、status 別件数、duration 合計
- token 4 field はそれぞれ observed 値だけを合計し、各 field の coverage を併記
- null をゼロに変換しない
- real/refuted/unresolved finding 合計
- finding 実効率は `real / (real + refuted)`。分母0なら null
- commit は件数と SHA の関連表だけ。token/commit、行数/token は生成禁止

### 欠測率

単一の曖昧な率だけにせず、少なくとも次を別々に出す。

- task end 欠測率
- lead time の未分類率
- event の stage_id 欠測率
- test count 4 field の null 率
- token 4 field の null 率
- trigger `unspecified` 率
- `measurement_source.* == not-exposed` の率

run event が丸ごと書けなかったケースは検出不能なので、「ledger 内で観測可能な欠測率の下限」と明示する。

pilot report は遅い task 上位、最大の時間区分、test/rework/wait/unclassified の候補分類を出すが、「削るべき工程」を自動決定しない。正しさ gate、negative control、独立 review は削減候補から除外し、ループ変更はユーザー裁定へ回す。

## 6. E1/E2 分割と凍結 interface

### 凍結 API

E1 が次を公開する。

```python
SCHEMA_VERSION = "task-run/v1"

class LedgerError(Exception): ...

@dataclass(frozen=True)
class ValidatedRun:
    path: Path
    task: Mapping[str, object]
    events: tuple[Mapping[str, object], ...]
    is_finished: bool
    open_stage_id: str | None

def start_run(root: Path, *, slug: str, objective: str,
              task_class: int, base_commit: str,
              started_at: datetime | None = None) -> str: ...

def append_event(root: Path, task_run_id: str, event_type: str,
                 payload: Mapping[str, object],
                 measurement_source: Mapping[str, str],
                 *, timestamp: datetime | None = None,
                 lock_timeout_s: float = 5.0) -> Mapping[str, object]: ...

def finish_run(root: Path, task_run_id: str, outcome: str,
               *, timestamp: datetime | None = None) -> Mapping[str, object]: ...

def validate_run(run_dir: Path, *,
                 require_finished: bool = False) -> ValidatedRun: ...
```

E2 は `append_event()` と `validate_run()` 以外の E1 内部関数へ依存しない。seq、timestamp、lock、canonical serialization を再実装しない。

### 並列可否

条件付きで並列可です。

- schema/API をこの計画どおり固定後、E1 と E2 は素集合のファイルで実装できる。
- E2 は mock/stub で単体開発可能。
- E2 の ledger 結合試験と全体試験だけは E1 到着後に直列実行。
- interface 変更が必要になった場合、E2 が独自互換 shim を作らず親へ戻す。

## 7. file:line 実装項目

### E1 — core

| path / 起点 | 概算 | 実装 |
|---|---:|---|
| `tools/task_runs/__init__.py` 新規 L1 | 約30行 | 上記公開 API だけを export |
| `tools/task_runs/schema_v1.json` 新規 L1 | 約500行 | task、measurement source、9 event の Draft 7 closed schema |
| `tools/task_runs/schema.py` 新規 L1 | 約260行 | schema load/check、strict JSON、timezone/token/stage/sequence semantic validator |
| `tools/task_runs/ledger.py` 新規 L1 | 約380行 | root/event flock、O_EXCL start、O_APPEND、fsync、pilot cap、API |
| `tools/task_runs/cli.py` 新規 L1 | 約280行 | typed `start/event/finish/validate` subcommand、exit code |
| `tools/task_run.py` 新規 L1 | 約15行 | repo path bootstrap と `cli.main()` |
| `orchestrator/tests/test_task_run_ledger.py` 新規 L1 | 約650行 | schema/writer/validator/CLI、全 negative control、process race |

E1 の test ファイル末尾は `pytest.main([__file__])` を持たせ、[test_plain_runner_coverage.py:60](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/tests/test_plain_runner_coverage.py:60) の allowlist 追加を不要にする。

### E2 — test recording / aggregation

| path / 起点 | 概算 | 実装 |
|---|---:|---|
| [tools/run_tests.py:26](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/tools/run_tests.py:26) | 追加約100行 | env 読取、suite fingerprint、monotonic timing、遅延 import、fail-open append |
| [tools/run_tests.py:214](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/tools/run_tests.py:214) | 置換点1か所 | opt-in 分岐。ただし返す値は必ず元 child rc |
| [orchestrator/tests/conftest.py:116](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/tests/conftest.py:116) | 追加約35行 | controller-only pytest session stats sidecar |
| `tools/task_runs/pytest_stats.py` 新規 L1 | 約100行 | count 射影、create-only sidecar、worker no-op |
| `tools/task_runs/aggregate.py` 新規 L1 | 約380行 | validate-first 集計、missingness、red→green、Markdown renderer |
| `tools/task_run_report.py` 新規 L1 | 約20行 | report CLI |
| `orchestrator/tests/test_run_tests_task_run.py` 新規 L1 | 約350行 | runner 意味論不変、stats、fail-open |
| `orchestrator/tests/test_task_run_aggregate.py` 新規 L1 | 約420行 | 手計算 fixture、欠測、red→green、invalid input refusal |

E2 は既存 [test_run_tests_nproc.py:95](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/tests/test_run_tests_nproc.py:95) の command golden を変更せず通す。

### 親 — 正本・統合

| path / 現在位置 | 作業 |
|---|---|
| `output/task-runs/README.md` 新規 L1、約250行 | 詳細正本。非 proof-chain 宣言、schema、CLI、privacy、fail-open、上限、保持、集計式 |
| [output/README.md:5](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/output/README.md:5) | tree に `task-runs/` を追加 |
| [output/README.md:38](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/output/README.md:38) | D13 の二軸外にある process 観測で、proof chain ではない旨を明記 |
| [docs/README.md:44](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/docs/README.md:44) | `output/task-runs/` への1行ポインタ |
| [docs/decisions.md:2485](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/docs/decisions.md:2485) | 統合時の次の未使用 D 番号を採番。現在なら D66 候補 |
| [docs/worklog.md:1020](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/docs/worklog.md:1020) | 実装結果、検査、pilot 開始条件、最初の task_run_id を末尾へ |
| [handoff:39](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/docs/handoff/2026-07-19-ai-development-observability.md:39) | 全8項目を吸収後に削除 |
| `output/task-runs/reports/<period>_task-efficiency.md` | 10 run または14日到達時に create-only 生成 |

`CLAUDE.md`、`tools/check_docs.py`、`tools/check_ai_provenance.py`、`tools/check_codex_agents.py`、campaign modules は編集しない。

## 8. unit / negative control

### E1

- start が task/event を create-only で生成する。
- 同一 ID の再 start が元 byte を変えず失敗する。
- append 後に旧 `events.jsonl` bytes が完全な prefix として残る。
- 2 process の同時 append が全件保持・seq 一意連番になる。
- timezone 付き UTC 出力。
- truncate 最終行を拒否。
- valid JSON でも終端 newline 無しを拒否。
- duplicate key、空行、BOM、NaN、過大行を拒否。
- duplicate seq と gap seq を拒否。
- task/event の未知 schema を拒否。
- 未知 event を拒否。
- task ID 不一致を拒否。
- timestamp 逆行・timezone 無しを拒否。
- 各 duration event の負値を拒否。
- token total 不一致を拒否。
- `cached_tokens > input_tokens` を拒否。
- `not-exposed` なのに token 非 null を拒否。
- token 4値 null の agent run を受理。
- 1 task の複数 commit を受理。
- commit より前の stage/test/finding event を受理。
- commit 0件の completed task を受理。
- task_end 後の commit を受理し、それ以外を拒否。
- stage overlap、wrong end、未閉鎖 stage を拒否。
- path traversal と symlink を拒否。

### E2

- opt-in 無しで command、stdio、rc が現行と同一。
- opt-in 有りでも pytest argv が不変。
- full/targeted/`-k` suite 分類。
- suite ID に command/node/selector 本文が入らない。
- monotonic duration と child exit status の一致。
- collected/passed/failed/skipped の controller 集計。
- xdist worker が sidecar を書かない。
- stats sidecar 不在時に null count と warning。
- ledger append exception 時も child rc を返す。
- invalid task-run ID 時も test 本体を実行する。
- invalid ledger を aggregator がスキップせず停止。
- 手計算 fixture の lead=1200、active=840、wait=60、unclassified=300 等を exact 比較。
- fail, fail, pass を red→green 1周と数える。
- 未到達 red を別計上。
- token null を0にせず coverage 低下として表示。
- report が token/commit、行数/token KPI を含まない。
- 同じ入力から report byte が決定的。

## 9. 変異テスト候補

| 殺す変異 | 赤くなるテスト |
|---|---|
| 最終壊れ行を campaign WAL 同様に無視 | `test_validate_rejects_truncated_final_line` |
| `seq > previous` だけにして gap を許容 | `test_validate_rejects_seq_gap` |
| duplicate seq 検査を削除 | `test_validate_rejects_duplicate_seq` |
| schema version 検査を削除 | `test_validate_rejects_unknown_schema` |
| unknown event を汎用 event として受理 | `test_validate_rejects_unknown_event` |
| timestamp order 検査を削除 | `test_validate_rejects_timestamp_regression` |
| timezone 無しを UTC と仮定 | `test_validate_rejects_naive_timestamp` |
| duration minimum を削除 | `test_validate_rejects_negative_duration` |
| token total 整合を削除 | `test_validate_rejects_inconsistent_total_tokens` |
| total に cached を二重加算 | cached 有り正常 fixture の positive test |
| cached subset 検査を削除 | `test_validate_rejects_cached_above_input` |
| not-exposed/null 連動を削除 | `test_validate_rejects_value_with_unexposed_tokens` |
| task 作成を `"w"` overwrite に変更 | `test_start_is_create_only_and_byte_preserving` |
| append 前に全ファイルを書き直す | `test_append_preserves_exact_prefix` |
| flock 呼出しを削除 | lock-call test と multi-process race test |
| directory/task/event ID 照合を削除 | `test_validate_rejects_task_id_mismatch` |
| task_end 後の通常 event を許容 | `test_validate_rejects_work_after_task_end` |
| aggregator が invalid run を warning skip | `test_report_refuses_any_invalid_run_without_output` |
| active を `lead-wait` と計算 | 手計算 fixture の `active=840` assertion |
| red ごとに1周加算 | fail/fail/pass fixture の `cycles=1` assertion |
| null token を0へ変換 | observed sum + coverage assertion |
| recording failure rc を返す | `test_recording_failure_preserves_child_exit_status` |
| command 全文を event に保存 | closed-schema/privacy assertion |

## 10. 検収順

1. E1 targeted tests。
2. E2 targeted tests。
3. `test_run_tests_nproc.py` と `test_plain_runner_coverage.py`。
4. campaign WAL / layer3 report の既存 targeted tests。
5. `python3 tools/run_tests.py` 全体。
6. `python3 tools/check_codex_agents.py`。
7. `python3 tools/check_docs.py`。
8. 親が docs・最初の実 task-run を統合。
9. 同一 commit に必要な phase checklist を含める場合は親が更新。
10. commit 後に `python3 tools/check_ai_provenance.py`。
11. push / PR は人間が実行。

## 要裁定

1. **長時間 class 1 audit を pilot の10件に含めるか。** 現行 `CLAUDE.md` では長時間 read-only audit も class 1。schema は 1〜3 を許容し、短い class 1 だけ運用で除外する案を推奨する。

2. **standalone check の自動記録範囲。** 本案では `docs-check` / `provenance-check` / `static-check` を schema 上は表現可能にするが、既存 check CLI は変更しない。pilot から自動配線まで要求する場合は、E2 の別 wrapper と追加意味論検査が必要になるため別裁定とする。

## プラン外の発見

既存バグは発見していません。

ただし実装開始時の再確認事項があります。

- handoff の基準 commit `95ed6fe` に対し、現在の HEAD は `9cbe36a`。
- worktree に未追跡の `docs/handoff/2026-07-20-dev-wave-observability.md` が存在する。本調査では内容を採用・編集していないため、親は docs 統合前に所有セッションを確認すること。
## 3. 敵対相談 A: 正しさ境界・防壁レンズ (max) — 逐語

判定は実装着手不可です。**must-fix 27件、should 2件**。指定された8観点すべてで具体的な破れ経路を構成できたため、所見ゼロの観点はありません。

1. (a) **must-fix — 大半の event に実発火経路がない**
   
   (b) E2 が自動生成するのは `run_tests.py` の `test_run` だけで、`start/task_end/stage/agent/wait/finding/rework/commit` や standalone check は手動 CLI のままです。`task_end` だけの run が valid になり、未記録の agent・wait・rework が「0件」に見えるため、[正本の機械取得要求](</home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/docs/handoff/2026-07-19-ai-development-observability.md:64>)を満たしません。
   
   (c) 修正案: セッション lifecycle と全対象 check の具体的 producer/canary を実装するか、report の主張範囲を「pytest 観測のみ」に縮小する。

2. (a) **must-fix — validator が実データへ常時結線されていない**
   
   (b) unit test は validator 関数を壊れた fixture へ呼ぶだけで、通常の全体検査は canonical `output/task-runs` を走査しません。最後の append 後に壊された run、名前を変えられた run、root 不在・0件を `validate --all` が緑にする実装でも検収を通せます。これは [F9 の恒真ゲート](</home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/docs/failures.md:88>)と同型です。
   
   (c) 修正案: activation manifest の期待 run 集合と canonical root を通常検査から必ず照合し、root不在・空集合・未知entryを赤にする live positive control を置く。

3. (a) **must-fix — 空 `events.jsonl` と終端 newline 規則が矛盾する**
   
   (b) `start` は0 byteの `events.jsonl` を作りますが、validator 項目は「最終 newline 欠落を拒否」です。文字どおり実装すると、最初の `event` が既存空ファイルの検証で失敗し、run は永久に追記不能です。
   
   (c) 修正案: 0 byteだけを明示的な valid 初期状態と定義するか、seq 0 の genesis record を設け、その負例・正例を固定する。

4. (a) **must-fix — append 前に候補 record を検証する手順がない**
   
   (b) 手順は「既存 stream を検証→seq/time決定→追記」であり、public API の不正 payload、時計逆行、16 KiB超行、10,001件目、8 MiB超過を先に永続化してから次回 validator が赤にします。argparse は generic `append_event()` の防壁ではありません。
   
   (c) 修正案: lock 内で候補を含む仮想 stream の schema・全 invariant・prospective size/count を検証し、失敗時は元 bytes 不変を保証する。

5. (a) **must-fix — `measurement_source` が自己申告で恒真化する**
   
   (b) caller が payload と source の両方を渡せるため、捏造値へ `monotonic-clock`、`api-reported`、`git-observed` と付けても valid です。caller-supplied timestamp に `system-clock` を付けることもでき、`base_commit` と commit relation も40桁なら実 Git 状態と無関係に通ります。
   
   (c) 修正案: generic API は全 source を強制的に `caller-supplied` とし、wrapper専用 API だけが時計・Git・API値を内部取得して強い source を設定する。

6. (a) **must-fix — event別 source/null/0 契約が閉じていない**
   
   (b) duration を持つ event は欠測を表せず、記録不能時に `0` を入れる誘因があります。逆に duration のない commit が `monotonic-clock`、tokens のない test が `api-reported`、`tokens=not-applicable` なのに実値あり、count の一部だけ null、という組合せを拒否する規則がありません。
   
   (c) 修正案: event型ごとの `if/then` source matrixを定義し、適用可能だが欠測は `null + not-exposed`、真の0と not-applicable を別表現にする。

7. (a) **must-fix — wait/stage の区間 invariant を現在の field では証明できない**
   
   (b) 区間終了の wall timestamp と monotonic duration しかないため、NTP補正を跨ぐと `timestamp-duration` は実開始時刻になりません。wait の stage 内包・相互非重複を誤判定でき、`stage_elapsed-wait` や `lead-Σstage` が負にもなります。浮動秒と timestamp 精度の「完全一致」も未定義です。
   
   (c) 修正案: 同一時計領域の start/end または run-relative monotonic offset を記録し、固定精度単位と clock anomaly 規則まで凍結する。

8. (a) **must-fix — stage参照と event identity が不足する**
   
   (b) `agent_run/test_run/finding/rework` は存在しない、終了済み、未来の `stage_id` を参照できます。`agent_run_id/review_id/rework_id` の重複禁止がなく、`test_run` には invocation ID 自体がないため、再送や二重記録を集計器が二重加算します。
   
   (c) 修正案: 全 event に一意な `event_id`、testに `test_run_id` を追加し、stage存在・開区間・ID再利用・commit重複の規則を明記する。

9. (a) **must-fix — valid-prefix truncate により seq が巻き戻る**
   
   (b) `events.jsonl` を過去の newline 境界まで切り戻せば、その prefix は schema・seqとも valid です。次回 writer は消えた seq を再利用し、truncate validator は発火しません。内部 hash chain だけでも古い正しい head までの truncate は検出不能です。
   
   (c) 修正案: 最終 size/seq/hash を別の create-only anchor または Git基準prefix検査へ固定するか、「append-only」はwriter局所契約で改竄検出ではないと格下げする。

10. (a) **must-fix — `start` 中断状態に回復契約がない**
    
    (b) `mkdir` 後、task作成後、events作成後、各 fsync の間で停止すると部分 run が残ります。次回 start がそれを検査対象にすれば root 全体が永久停止し、無視すれば pilot件数とreportから静かに消えます。自動削除禁止だけでは解決しません。
    
    (c) 修正案: 最後に作る create-only commit markerで公開済みrunを識別し、原bytesを保存した quarantine/recover 手順を定義する。

11. (a) **must-fix — fsync の不確定成功後の再試行が重複を作る**
    
    (b) write が完了してから fsync が例外になった場合、record は可視なのに caller は失敗を受けます。`run_tests.py` の「最小 event で一度再試行」は同じ test をもう一件追加し、回数・時間・red→greenを水増しします。
    
    (c) 修正案: append前に invocation IDを確定し、再試行時は同ID・同digestの既存recordを成功として照合する冪等 API にする。

12. (a) **must-fix — lock domain が統一されず snapshot が成立しない**
    
    (b) start は root directory、append は event inodeだけを lockし、validator/report の lock は未規定です。start/report が追記途中を読み、report列挙中に新規runが公開され、pathname交換後は旧inodeと新inodeを別々に lockできます。
    
    (c) 修正案: root shared/exclusive→run file の固定 lock順を全操作へ適用し、`openat/O_NOFOLLOW/fstat`した同一fdだけを検証・追記・再照合する。

13. (a) **must-fix — race test が実運用 filesystem を検査しない**
    
    (b) この worktree の `output/` は Lustre ですが、現行 [conftest](</home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/tests/conftest.py:1>) は現在の条件では `tmp_path` を `/dev/shm` へ向けます。tmpfs 上の flock/O_APPEND/directory-fsync 成功は Lustre 上の耐久・排他検収になりません。
    
    (c) 修正案: pilot開始前に canonical root 上で隔離した多process append・fsync・kill-point canaryを実施し、未対応filesystemでは開始をfail-closedにする。

14. (a) **must-fix — worktreeごとに別 ledger/lock/cap になる**
    
    (b) 既定 `output/task-runs` は各 worktree の別 inodeです。二つの作業セッションが各10件を開始でき、lockも共有せず、merge後に20件と競合reportが現れます。
    
    (c) 修正案: repo-wide pilotなら git-common-dir等に一意な共有registryを置くか、worktree単位pilotと明記して union/cap 検証を別途実装する。

15. (a) **must-fix — `task_end` が report の入力終端ではない**
    
    (b) task_end 後も commit を無期限に追記できます。create-only reportを生成した翌日に commit が追加されると、reportの関連表は不完全なまま再生成不能になり、「同じ入力なら決定的」は意味を失います。
    
    (c) 修正案: post-end commitを締める create-only `seal`/cutoffを追加し、reportはseal済みrunの固定digestだけを入力にする。

16. (a) **must-fix — campaign proof namespace との構造分離がない**
    
    (b) 現行 [output地図](</home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/output/README.md:1>) は output を探索成果物として扱い、`campaigns/*/runs` を [proof chain](</home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/output/README.md:38>) と定義します。root override をその配下へ向ければ開発台帳を proof namespace 内に生成できます。既存 hook の保護対象も [campaign側だけ](</home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/hooks/README.md:41>)で、Python内部書込みは境界になりません。
    
    (c) 修正案: canonical rootのrealpath containmentを強制しcampaign/env/freeze配下を拒否、全record/reportへ `authority=development-observation-only` と証拠利用不可のconstを入れる。

17. (a) **must-fix — 「正しさ防壁を削減候補から除外」が表現不能**
    
    (b) suite schemaには correctness-gate/negative-control の識別がなく、full suite内のどのnodeが防壁かも保存しません。docs/provenance/static check は自動配線されないため、集計器は防壁を認識できず、除外保証が恒真化します。[正本はこれらの削減を禁止](</home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/docs/handoff/2026-07-19-ai-development-observability.md:103>)しています。
    
    (c) 修正案: reviewed suite registryからprotected種別を機械付与して全checkを配線するまで、v1 reportから削減候補生成を撤去する。

18. (a) **must-fix — fail-open の丸ごと欠測が「高速化」に化ける**
    
    (b) lock timeoutやappend障害が起きた test は event自体がなく、stderr warningも永続化されません。重いrunほどlock競合しやすい場合、欠測は非ランダムとなり、test回数・時間・red周回が少ない「速いtask」として順位付けされます。「下限」と脚注するだけでは防げません。
    
    (c) 修正案: test本体はfail-openのまま独立なattempt/health receiptと照合し、capture完全性が証明できないtaskでは比較・順位・削減推論をfail-closedにする。

19. (a) **must-fix — pytest内 hook 障害は元の exit code を既に変える**
    
    (b) 現行 runner は [subprocessのrcを直接返す](</home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/tools/run_tests.py:214>)だけです。常時ロードされる conftest の `pytest_sessionfinish` が import、JSON、sidecar I/Oで例外になるとpytest自身が internal-error等へ変わり、wrapperが返すのは「元のrc」ではなく観測で汚染されたrcです。`tools.task_runs.pytest_stats` import時には package `__init__` も実行されます。
    
    (c) 修正案: dependency-free・opt-in限定・no-throwのplugin境界を作り、import不能、jsonschema不在、I/O例外を実subprocessへ注入して元rc/stdout/stderrを固定する。

20. (a) **should — sidecar のidentity・配置・後始末が未定義**
    
    (b) 同時・nested runnerが同じpathを使えばcreate-only衝突し、stale fileを誤読できます。repo内に置けばrepo不変テストを汚し、worker判定やsidecar用env自体がtestから観測可能です。
    
    (c) 修正案: repo外のprivate tempへ128-bit invocation ID付きで作り、O_EXCL/O_NOFOLLOW/0600・master厳密判定・size制限・確実なcleanupを定義する。

21. (a) **must-fix — full/targeted 判定が実 pytest 選択を表さない**
    
    (b) 現行 `_is_target` は [実在する任意pathをtarget扱い](</home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/tools/run_tests.py:113>)するため、`--rootdir .` の `.` でも `has_target=True` です。一方 `PYTEST_ADDOPTS=-k ...`、`--deselect`、`--ignore`、`--collect-only`、`-x`、config/plugin由来選択はargs走査から消え、縮小実行をfullと記録できます。
    
    (c) 修正案: pytest側でeffective config/selectionを射影し、不明要素が一つでもあれば `targeted` または新設 `unknown` に倒す。

22. (a) **must-fix — red→green がpytest障害をtest failureと混同する**
    
    (b) 「非0ならred」では exit 2=interrupt、3=internal error、4=usage error、5=no testsもredになります。rc5の後にrc0なら、テスト失敗を一件も直していなくてもred→green一周です。
    
    (c) 修正案: pytest標準ではrc1だけをtest-redとし、2〜5・signal・未知plugin codeは別のinfra/open状態として集計する。

23. (a) **must-fix — 欠測率の分母が未定義**
    
    (b) `stage_id` fieldを持たない commit/task_endを分母へ入れるか、`stage_id:null` の「非該当」と「取り損ね」をどう分けるかがありません。test event 0件ならcount null率が0%にもnullにもでき、stageが存在してactive=0なら各ratioがゼロ除算します。
    
    (c) 修正案: 各率に applicable集合・numerator・denominatorを固定し、denominator 0は必ずundefined、非該当と欠測を別codeで出力する。

24. (a) **must-fix — token の部分整合と異種集計が破れる**
    
    (b) `total=5,input=10,output=null` は3値揃っていないため記載規則上通り得ます。またAPI/product/model/cache定義が違う値を全taskで合算し、[正本の異種単純比較禁止](</home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/docs/handoff/2026-07-19-ai-development-observability.md:108>)に反します。
    
    (c) 修正案: 既知成分間でも `total>=input/output` 等を強制し、product/model/source/定義が同一のcohort以外は合算しない。

25. (a) **must-fix — 許可fieldへ禁止内容を格納できる**
    
    (b) `scope`、明示 `suite_id`、`product/model/reasoning`、task slugはsafe pattern・長さ・URI規則がなく、prompt全文、session URL、料金、raw commandを合法的に格納できます。privacy変異も新field追加しか見ず、raw commandを `scope` に入れる変異は緑です。短いSHA digestも低entropy selectorの秘匿にはなりません。
    
    (c) 修正案: 自由文をobjectiveの人手確認済み要約だけに限定し、他はenum/safe slug/digestへ閉じ、全文字fieldと余分なrun-dir fileを保存前privacy検査する。

26. (a) **must-fix — pilot母集団と上限を任意に操作できる**
    
    (b) 長時間class 1を含めるか未裁定のまま、記録するtaskだけを選べます。public `started_at` で最初のrunを未来日付にすれば14日上限を延ばせ、root overrideやworktree分割でも10件上限を回避できます。taskごとの `measurement_policy` 値がconstかも未確定です。
    
    (c) 修正案: 最初のrun前にcreate-only pilot manifestへsystem取得開始時刻・canonical root・const上限・客観的inclusion/exclusion規則を凍結し、clock injectionはtest内部だけにする。

27. (a) **must-fix — report の create-only/deterministic がI/O中断に耐えない**
    
    (b) O_EXCLで最終pathへ直接書けば途中停止でpartial reportが名前を占有し、再生成不能です。入力runのbyte digest、validator/generator identity、cutoffがなければ、後から同じ入力だったかも証明できません。
    
    (c) 修正案: 全入力hash manifest付きで先にrender/size検証し、対象FSで検証済みのno-replace publishとfile/parent fsync、partial artifactの保全回復手順を定める。

28. (a) **must-fix — negative control／変異表が宣言済み防壁を覆っていない**
    
    (b) 少なくとも「空初期file」「候補拒否時bytes不変」「valid-prefix truncate/replace」「start各kill点」「write成功後fsync失敗」「wait containment/overlap」「timestamp-delta一致」「stage参照」「各ID重複」「task_end重複」「source全組合せ」「root不在/未知entry」「実Lustre/別worktree race」「pytest rc 2〜5」「hook import/I/O失敗」「PYTEST_ADDOPTS」「allowed fieldへの秘密混入」「protected gate除外」が変異で裏取りされません。lock関数の呼出し確認だけでは [F21型のlive未結線](</home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/docs/failures.md:247>)を殺せません。
    
    (c) 修正案: schema・lifecycle・filesystem・runner・reportの各 invariantに一対一の壊し変異を割り当て、実producer→永続record→reportまでのlive E2Eを追加する。

29. (a) **should — pilot必須の計装overhead測定が実装表から消えている**
    
    (b) 正本は [秒/操作数での記録overhead測定](</home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/docs/handoff/2026-07-19-ai-development-observability.md:111>)を要求しますが、schema・event・集計式に該当値がありません。Lustre上のflock/fsync負荷を自分で作り、その遅延を作業工程の遅さと誤認できます。
    
    (c) 修正案: recording attempt数・lock待ち・serialize/append/fsync秒をhealth系列へ分離記録し、opt-in/off基準とのoverheadをpilot reportの必須項目にする。

読取専用で調査し、ファイル編集・テスト実行は行っていません。
## 4. 敵対相談 B: 整合・実効性・スコープレンズ (max) — 逐語

## 判定

**NO-GO。must-fix 21 件、should 2 件。** 所見ゼロの検査観点はありません。

1. **D13 の「二軸外」と宣言するだけでは契約改訂にならない**
   - (a) 重大度: **must-fix**
   - (b) 根拠: D13 は `output/` を campaign/env の二軸へ分ける決定です。[docs/decisions.md:180](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/docs/decisions.md:180)、[output/README.md:3](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/output/README.md:3)。さらに D65 と実装は既に `output/exploration/campaigns/` を導入していますが、現行 tree に載っていません。[docs/decisions.md:2456](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/docs/decisions.md:2456)、[layout.py:220](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/campaign/layout.py:220)
   - (c) 修正案: D66 で「D13 は実験証拠の二軸、task-runs は直交する開発運用 namespace」と明示改訂し、`exploration/` を含む現行 tree も同時に整合させる。

2. **新しい詳細正本が `check_docs.py` の検査網外になる**
   - (a) 重大度: **must-fix**
   - (b) 根拠: `check_docs.py` は living docs を手書き列挙し、その集合だけを検査します。[check_docs.py:21](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/tools/check_docs.py:21)、[check_docs.py:122](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/tools/check_docs.py:122)。`output/README.md` も新規 `output/task-runs/README.md` も対象外です。これは過去の「検査対象が黙って蒸発」した F9 と同型です。[docs/failures.md:88](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/docs/failures.md:88)
   - (c) 修正案: 両 README を fail-closed な列挙対象へ追加し、不在・壊れた D/path 参照で赤くなる positive control も追加する。

3. **pilot を実際に起動させる必読導線がない**
   - (a) 重大度: **must-fix**
   - (b) 根拠: クラス2/3の起動導線は CLAUDE → worklog/phase/handoff で、`docs/README.md` や `output/task-runs/README.md` は必読ではありません。[CLAUDE.md:22](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/CLAUDE.md:22)、[CLAUDE.md:38](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/CLAUDE.md:38)。handoff 項目4は開始・節目・終了の導線を決めるよう要求しています。[handoff 項目4](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/docs/handoff/2026-07-19-ai-development-observability.md:65)
   - (c) 修正案: クラス2/3の必読経路に pilot 用の短いポインタを置き、start、ID/env 設定、finish、commit 関連付けまでを一つの起動手順に固定する。

4. **計装負担を測らず、pilot に対して上限と手動操作面を盛りすぎている**
   - (a) 重大度: **must-fix**
   - (b) 根拠: 現案は start、env 設定、各 stage の start/end、agent/wait/rework/finding、finish、commit、validate を手動操作にし得る一方、handoff は計装オーバーヘッドを秒数・操作数で測るよう要求しています。[handoff:111](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/docs/handoff/2026-07-19-ai-development-observability.md:111)。10,000 event・8 MiB/run は10-run pilotの行動予算による根拠がなく、規律5とも衝突します。[CLAUDE.md:81](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/CLAUDE.md:81)
   - (c) 修正案: pilot の想定操作数から上限を逆算し、自動取得を start/test/finish に絞り、writer latency と手動操作数を report に含める。

5. **比較の分母となる「同種 task」が定義されていない**
   - (a) 重大度: **must-fix**
   - (b) 根拠: `task_class` は作業導線の分類であり、実装・監査・修正・文書化や難度を表しません。[CLAUDE.md:24](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/CLAUDE.md:24)。handoff は難度・成果を併記し、同種 task 内で比較するよう要求しています。[handoff:12](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/docs/handoff/2026-07-19-ai-development-observability.md:12)、[handoff 項目6](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/docs/handoff/2026-07-19-ai-development-observability.md:79)。長時間 class 1 の採否も未裁定のままです。
   - (c) 修正案: pilot 前に対象母集団を凍結し、少数の `task_kind`・事前 scope/難度帯・成果受入状態で層別し、同一層が複数なければ比較 KPI を出さない。

6. **`measurement_source` が数量単位で分離できず、caller が出所を自己認証できる**
   - (a) 重大度: **must-fix**
   - (b) 根拠: `test_run` では exit status は wrapper 実測、count は pytest sidecar、欠測時は count だけ `not-exposed` ですが、`metrics` は一値しかありません。さらに公開 API が `measurement_source` と timestamp を受け取るため、caller が `wrapper-observed` を名乗れます。handoff 項目3は自然言語自己申告と wrapper 実測の分離を要求しています。[handoff:64](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/docs/handoff/2026-07-19-ai-development-observability.md:64)
   - (c) 修正案: source を `exit_status`、`test_counts`、`agent_identity` 等の field group 単位にし、writer が経路から設定して caller 指定を禁止する。

7. **`base_commit` と commit event が Git 実測ではない**
   - (a) 重大度: **must-fix**
   - (b) 根拠: handoff は取得可能な git hash を wrapper が実測するよう求めています。[handoff 項目3](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/docs/handoff/2026-07-19-ai-development-observability.md:58)。しかし凍結 API は `base_commit` を引数で受け、commit は40桁形式しか検査せず、object の存在・到達性・現在 HEAD との関係を確認しません。
   - (c) 修正案: start 時に writer が `git rev-parse HEAD` を取得し、commit event も `cat-file` と明示した relation 条件を実測してから記録する。

8. **token の共通意味論と横断合計が製品差を潰す**
   - (a) 重大度: **must-fix**
   - (b) 根拠: handoff は製品・モデル・cache・圧縮で定義が違い、異種製品を単純比較しないよう警告しています。[handoff:108](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/docs/handoff/2026-07-19-ai-development-observability.md:108)。現案の「cached は input の内数」「total=input+output」を全 product-reported 値へ一律適用する根拠がなく、aggregate も product/model/source を跨いで合計します。
   - (c) 修正案: adapter ごとに正規化可能性を明記し、証明できない field は null、集計は `(product, model, token-source/semantics-version)` ごとに分離する。

9. **未閉鎖 stage の fail-closed 規則が通常の `stage_end` を不可能にする**
   - (a) 重大度: **must-fix**
   - (b) 根拠: event 追記は既存全 event を先に strict validate しますが、fail-closed 一覧と negative control は未閉鎖 stage を拒否します。したがって `stage_start` 後の ledger が invalid となり、次の `stage_end` を追記できません。handoff 項目3は途中状態と異常終了を扱う append-only writer を要求しています。[handoff 項目3](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/docs/handoff/2026-07-19-ai-development-observability.md:58)
   - (c) 修正案: unfinished run では最大1件の open stage を valid とし、`task_end` または `require_finished=True` のときだけ未閉鎖を拒否する。

10. **一度の torn append が10-run pilot 全体を永久に report 不可能にする**
   - (a) 重大度: **must-fix**
   - (b) 根拠: 既存 WAL は O_APPEND+fsync でも追記中クラッシュによる末尾切れが起こる前提です。[wal.py:8](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/campaign/wal.py:8)、[wal.py:75](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/campaign/wal.py:75)。現案は truncate を一切回復せず、invalid run が1件でも report 全体を拒否するため、fail-open 計装と運用上両立しません。
   - (c) 修正案: record を原子的に確定できる物理形式へ変えるか、破損 bytes を保存した明示 quarantine/recovery と非KPI診断 report を規定する。

11. **`test_run` の一度だけ再試行は二重計上を起こす**
   - (a) 重大度: **must-fix**
   - (b) 根拠: fsync 後の unlock/close 等で caller が失敗を受け取れば、record は既に durable でも再試行されます。既存 append も write→fsync→close の順です。[wal.py:47](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/campaign/wal.py:47)。`test_run` には一意な event ID がなく、suite ID は反復可能なので重複を判定できません。
   - (c) 修正案: 試行前生成の `test_run_id` を必須にして一意性を検査し、同一 ID の再試行は既存 record を返す idempotent append にする。

12. **wall-clock / active / wait の式が排他的な時間分解にならない**
   - (a) 重大度: **must-fix**
   - (b) 根拠: `stage_id:null` の wait は既に `unclassified=lead-stage` に含まれるのに、`wait_time` にも加算されます。また lead は wall timestamp 差、stage は monotonic/caller duration の和なので負の unclassified/active も作れます。並列 agent 中の「一方だけの待ち」を task 全体の idle として引く意味も未定義です。handoff は wall-clock と active/wait を明確に分けるよう要求しています。[handoff:103](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/docs/handoff/2026-07-19-ai-development-observability.md:103)
   - (c) 修正案: 同一時刻基準の区間 union で分解し、task 全体を止めた blocking wait と agent/lane 単位の concurrent wait を別型にする。

13. **必須 completion check が pilot の盲点になる**
   - (a) 重大度: **must-fix**
   - (b) 根拠: handoff 項目5は targeted/full/docs/provenance check の区別を要求しています。[handoff 項目5](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/docs/handoff/2026-07-19-ai-development-observability.md:72)。クラス2/3では `check_codex_agents.py`、`check_docs.py`、commit 後の provenance check が必須です。[AGENTS.md:26](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/AGENTS.md:26)。schema に名前だけ用意し、自動配線を「別裁定」に落とすと tail latency の主要候補を測れません。
   - (c) 修正案: raw command を受けない allowlist wrapper で少なくとも三つの必須 check の duration・rc を pilot から実測する。

14. **「任意の非0」を red とする red→green KPI は誤計上する**
   - (a) 重大度: **must-fix**
   - (b) 根拠: runner が取得するのは pytest の生 return code です。[run_tests.py:214](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/tools/run_tests.py:214)。非0には test failure 以外の interrupted、internal/usage error、no-tests-collected が含まれ、次の exit 0 で閉じると架空の修正周回になります。handoff 項目5が要求するのはテスト結果からの red→green 再構成です。[handoff:73](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/docs/handoff/2026-07-19-ai-development-observability.md:73)
   - (c) 修正案: pytest exit category を閉表化し、比較可能な suite の `TESTS_FAILED` だけを red、infra/collection/interrupt は別 outcome にする。

15. **`--lf` 等では suite ID が実際の test 集合を識別しない**
   - (a) 重大度: **should**
   - (b) 根拠: suite ID は argv/selector の hash だけですが、`--lf` の収集集合は pytest cache 状態で変わります。handoff は安定 suite ID による red→green 再構成を要求しています。[handoff:73](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/docs/handoff/2026-07-19-ai-development-observability.md:73)
   - (c) 修正案: node 名自体は保存せず、controller が実収集 node ID 集合の digest を追加し、digest 不一致は同一 suite cycle とみなさない。

16. **欠測率の分母と自己申告率が定義されていない**
   - (a) 重大度: **must-fix**
   - (b) 根拠: handoff は欠測率を必ず併記するよう要求しています。[handoff:82](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/docs/handoff/2026-07-19-ai-development-observability.md:82)。現案は `measurement_source.* == not-exposed` の denominator に `not-applicable` event を含めるか不明で、`caller-supplied` の割合も出さず、丸ごと書けなかった event は下限と注記するだけです。
   - (c) 修正案: 各率の eligible population・numerator・denominator を schema/report 契約に固定し、wrapper/tool/caller 別 coverage と検出不能な attempted-write failure を別表示する。

17. **task_end 欠測 run が「遅い task」ランキングから消える**
   - (a) 重大度: **must-fix**
   - (b) 根拠: lead time は task_end がなければ算出不能ですが、report は遅い task 上位を出します。14日終了時に未完の最長 task がランキングから消え、handoff が避けようとした生存者バイアスを再生します。[handoff:21](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/docs/handoff/2026-07-19-ai-development-observability.md:21)、[handoff:84](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/docs/handoff/2026-07-19-ai-development-observability.md:84)
   - (c) 修正案: 未完 run を cutoff 時点の右打切り下限として別表に必ず載せ、completed run と同じ順位・平均には混ぜない。

18. **create-only report が入力 ledger の凍結 snapshot になっていない**
   - (a) 重大度: **must-fix**
   - (b) 根拠: task_end 後も commit event を許すため、report 生成後に入力が変わります。handoff も commit は task_end に続き得るとしています。[handoff:70](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/docs/handoff/2026-07-19-ai-development-observability.md:70)。現案には root lock、対象 run/seq cutoff、source hash、report の crash-safe publish がありません。
   - (c) 修正案: cohort を root lock 下で閉じ、run ID・最終 seq・task/events SHA-256 を report に束縛し、temp+fsync+no-replace で公開後は late commit を次版へ送る。

19. **E1/E2 の凍結 interface に root discovery がなく、既知の F2 を再発させる**
   - (a) 重大度: **must-fix**
   - (b) 根拠: E2 aggregate は root から run 群を列挙する必要がありますが、E1 API は単一 `validate_run()` しか公開しません。過去に consumer ごとの directory discovery 分裂が F2 として起きています。[docs/failures.md:28](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/docs/failures.md:28)
   - (c) 修正案: E1 に `validate_root()/discover_runs()` と invalid/dependency/lock-timeout の例外分類を追加し、report CLI の対象選択も interface 凍結に含める。

20. **privacy 契約が自由文字列と環境変数経由で抜ける**
   - (a) 重大度: **must-fix**
   - (b) 根拠: safe slug とされるのは一部 ID だけで、`suite_id`、`product`、`model`、`reasoning`、`scope` 等の長さ・文字集合が未定義です。`IZANAGI_TEST_SUITE_ID` から command/session ID を入れられます。handoff は prompt、session URL、個人情報、秘密を禁止しています。[handoff:109](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/docs/handoff/2026-07-19-ai-development-observability.md:109)。D53 の識別子契約は既にあります。[docs/ai-provenance.md:30](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/docs/ai-provenance.md:30)
   - (c) 修正案: 全識別子を D53 相当の短い slug に閉じ、suite ID は wrapper 導出のみ、objective の秘密検出は機械保証不能と明記して report 既定表示から外す。

21. **Git 追跡・保持・次の pilot の lifecycle が未裁定**
   - (a) 重大度: **must-fix**
   - (b) 根拠: handoff 項目1は raw ledger/report の追跡方針、サイズ上限、ローテーションを裁定事項にしています。[handoff:45](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/docs/handoff/2026-07-19-ai-development-observability.md:45)。`.gitignore` は task-runs を除外しないため暗黙には追跡対象ですが、現案は pilot 後に止めるだけで、保持期間・凍結・次回 root・80 MiB 最大データの扱いを定めません。[.gitignore:17](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/.gitignore:17)
   - (c) 修正案: tracked/untracked を明記し、pilot generation/root、freeze、保持期間、次回 pilot、Git 履歴へ永続する情報の削除不能性まで README に固定する。

22. **worklog と D53 provenance の母集団が task-run と混線する**
   - (a) 重大度: **should**
   - (b) 根拠: worklog は Git/正本に入らない情報だけを索引化する契約です。[docs/worklog.md:16](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/docs/worklog.md:16)。一方、計画は実装結果・test・主要集約値を再掲します。また D53 trailer は採用に実質寄与した構成だけですが、`agent_run` は failed/cancelled/不採用も数えます。[docs/ai-provenance.md:47](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/docs/ai-provenance.md:47)
   - (c) 修正案: D66/README で母集団差を明記し、worklog は task_run_id・異常・裁定だけ、集約値は report、commit provenance は引き続き D53 trailer のみにする。

23. **negative control が上記の load-bearing 穴を殺さない**
   - (a) 重大度: **must-fix**
   - (b) 根拠: handoff 項目7は schema/writer/aggregation の壊れ方を実際に赤くすることを要求しています。[handoff 項目7](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/docs/handoff/2026-07-19-ai-development-observability.md:86)。現行候補には open-stage の中間 valid、ambiguous retry、pytest exit 2〜5、null-stage wait、並列 wait、unfinished censoring、post-report append、source 偽装、root discovery 分裂、欠測 denominator がありません。
   - (c) 修正案: これらを E1/E2 acceptance と変異表へ追加し、各変異が修正前に生存・修正後に kill されることを確認する。

## handoff 8項目との網羅対照

| handoff 項目 | 黙って落ちた、または未裁定の部分 | 関連所見 |
|---|---|---|
| 1. 既存契約との整合 | D13 の正式改訂、D65 namespace の地図、check_docs 編入、Git追跡・保持、worklog/D53 分離 | 1, 2, 21, 22 |
| 2. schema v1 | field 単位 source、異種 token 意味論、時間区間、比較用 task strata、全文字列の privacy 制約 | 5, 6, 8, 12, 20 |
| 3. writer / validator | Git 実測、open-stage 中間状態、torn append の回収、retry idempotency、root discovery | 7, 9, 10, 11, 19 |
| 4. AI 作業導線 | 必読起動経路、env/ID 設定、現実的な操作数、計装 overhead、役割分離 | 3, 4, 22 |
| 5. テスト効率 | standalone check 実測、pytest exit category、実収集集合を束縛した suite identity | 13, 14, 15 |
| 6. 集計 / report | 同種 task 分母、排他的時間式、欠測 denominator、異種 token 分離、未完 run、source snapshot | 5, 8, 12, 16, 17, 18 |
| 7. 検証 | open/crash/retry/exit-code/wait/censoring/snapshot/source/discovery の negative control | 23 |
| 8. 文書化 / 完了 | D66 による既存決定の明示改訂、lint 編入、保持裁定、worklog/D53 分離が未完のため handoff 削除条件未達 | 1, 2, 21, 22 |
## 5. 親裁定 — プラン v2 (V1〜V26) + 変異事前登録 M01〜M32

# 親裁定 — プラン v2 (task-run 台帳 pilot)

裁定者 = 親 (fable)。対象 = plan_final.md (v1) + consult_A_final.md (27 must-fix / 2 should) +
consult_B_final.md (21 must-fix / 2 should)。**プラン v1 は NO-GO を追認**し、以下の V 系列で v2 を確定する。

## 所見裁定の総括

- **real / 採用 (設計変更)**: A3 A4 A5 A6 A7 A8 A10 A11 A12 A14 A15 A16 A19 A20 A21 A22 A23 A24 A25
  A26 A27 A28 / B1 B2 B4 B5 B6 B7 B8 B9 B10 B11 B12 B13 B14 B15 B16 B17 B18 B19 B20 B21 B22 B23
- **real / 採用 = 主張の縮小・格下げで解消 (機構は足さない)**: A1 (report の主張範囲を縮小 = V23)、
  A9 (append-only は改竄検出でないと明記 = V6)、A17 (v1 report から削減候補推論を撤去 = V22)、
  A18 (検出不能欠測は限界として明記 + 順位系の主張縮小 = V18/V23)、A13 (実 FS canary = selfcheck に縮退 +
  既知限界明記 = V9)、A2 (activation manifest でなく root 実在・未知 entry 検査 + live positive control = V19)
- **refuted なし** (全所見に実穴または実行不能な曖昧さを確認)。ただし各所見の「修正案」は
  そのまま採用せず、pilot 規模 (規律 5) に整合する縮退版を V 系列で確定する
- **scope 外 → ユーザー裁定パッケージ行き: なし** (CLAUDE.md へのポインタ追加のみ pilot 実証後の
  ユーザー提案として worklog に記載 — B3 の縮退解 = V19-b)
- codex プラン v1 の要裁定 2 件: (1) 長時間 class-1 監査は opt-in で pilot に含めてよい (task_class=1
  で記録) = V24。(2) standalone check は「別裁定に落とす」を却下し、allowlist wrapper で pilot から
  配線する = V22 (B13 採用)

## V 系列 (プラン v2 = プラン v1 + 以下の差分。矛盾時は V が優先)

- **V1 (A3,B9) lifecycle 妥当性**: 0 byte の events.jsonl は明示的な valid 初期状態。未終了 run では
  open stage ちょうど 0 or 1 件を valid とする。task_end は open stage が残っていれば拒否。
  `require_finished=True` のときだけ task_end 不在・open stage を赤にする
- **V2 (A4) 事前検証**: append は lock 内で「既存 stream + 候補 record」の仮想 stream に対し
  schema・全 invariant・行/ファイルサイズ・event 数上限を検証してから書く。失敗時は元 bytes 不変
  (テストで byte 同一性を検証)
- **V3 (A5,A6,B6) source の自己申告遮断**: measurement_source と timestamp と seq は **writer が経路から
  決める。caller 引数から受けない** (public API に timestamp/source 引数を置かない。テストは module 内
  clock の monkeypatch で注入)。汎用 CLI event の metrics/duration source は強制 `caller-supplied`。
  強い source (`wrapper-observed`/`monotonic-clock`/`git-observed`) を設定できるのは wrapper 専用 API
  (`record_test_run` 等) のみ。event 型ごとの source 許容組合せを schema の if/then で閉表化
  (duration の無い event に `monotonic-clock` 等を拒否、tokens 非該当 event は `not-applicable` 固定)
- **V4 (B7) git 実測**: base_commit は start が内部で `git rev-parse HEAD` を実行して取得 (caller 引数
  廃止、source=git-observed)。commit event は `git cat-file -e <sha>^{commit}` で実在を確認してから
  記録、失敗は拒否
- **V5 (A8,A11,B11) event identity と冪等性**: envelope に `event_id` (16 hex、`secrets.token_hex(8)`、
  run 内一意) を必須追加。append の再試行は「書込み前に event_id を確定 → 曖昧な失敗後は再読して同
  event_id の record が存在すれば成功扱い」の冪等プロトコル。validator は event_id 重複を拒否。
  stage_id 参照は「存在する stage」のみ許容 (agent_run/test_run/finding/rework の stage_id は、その時点
  までに stage_start が現れた ID でなければ拒否)。agent_run_id/review_id/rework_id は run 内一意
- **V6 (A9) 主張の格下げ**: append-only は「writer 局所の crash-consistency 契約」であり改竄検出では
  ない、と README + D66 に明記。外部 anchor は git 追跡 (commit 履歴) に委ねる。hash chain は作らない
- **V7 (A10) start の中断回復**: 生成順 = mkdir → events.jsonl (O_EXCL) → task.json (O_EXCL、**最後 =
  publish marker**) → 各 fsync。valid な task.json を持たない directory は「incomplete-start」として
  隔離分類 (validate --all が列挙、cap に数えず、KPI から除外、自動削除しない)
- **V8 (A12) lock 秩序**: root 排他 flock = start / init-pilot / report publish。append = events.jsonl
  の排他 flock。open は O_NOFOLLOW + 開いた fd に対する fstat/検証/追記の同一 fd 規律
- **V9 (A13) 実 FS canary**: `task_run.py selfcheck <root>` を新設 — 実 root 上で O_EXCL・2 プロセス
  flock 排他・O_APPEND 交互追記・fsync を実測して合否を返す。pilot 開始前の必須手順として README に
  固定。tmpfs テストが Lustre の代理にならないことを既知限界として明記。kill-point 網羅 harness は
  pilot では作らない
- **V10 (A14,B21) worktree 局所性と追跡・保持の裁定**: 台帳 root は checkout 局所である事実を README に
  明記。merge は run directory の union (create-only なので競合しない)。report 時に cap 超過を検出したら
  超過を report に開示。git 追跡 = task.json / events.jsonl / reports / pilot.json を追跡。保持 = pilot
  世代は最終 report 後に凍結 (新規 start を拒否)、次 pilot は新 root 世代 (命名はその時に裁定)。
  git 履歴に入った記録は削除不能であることを README に明記 (だから privacy 制約が保存前検査である)
- **V11 (A15,A27,B18) report の публish 契約**: report 生成は root 排他 lock 下で cohort を確定し、
  report 本文に各 run の最終 seq + task.json/events.jsonl の SHA-256 を埋める (入力束縛)。temp へ
  render → fsync → 既存不在を確認して atomic rename (上書き禁止)。report 後の task_end 後 commit は
  次版 report の対象 (seal 機構は v1 では作らない — 入力束縛 digest で再現性の主張を閉じる)
- **V12 (B12,A7) 時間モデル v1**: lead = timestamp 差 (wall)。stage_end.duration_s は **writer が
  stage_start/end の timestamp 差から計算** (source=timestamp-delta、caller 供給廃止)。wait は task 全体
  を止める blocking wait のみ (stage_id field を v1 では持たない)、duration は caller-supplied と明示。
  test/agent duration は wrapper monotonic または caller-supplied。集計は lead / Σstage / Σwait /
  unclassified = lead − Σstage − Σwait を出し、**負値は clamp せず inconsistency flag を立てて率を null**。
  排他的分解を主張しない (非排他の観測値と README/report に明記)。duration は小数秒 (ms 精度に丸め)
- **V13 (A22,B14,B15) red→green 意味論**: red = pytest rc 1 (tests failed) のみ。rc 2/3/4/5・signal・
  未知は `infra` outcome として別集計し、cycle を開閉しない。cycle は suite_id 単位、
  collected_node_digest (sidecar が実収集 node ID 集合の SHA-256 先頭 12 桁のみ保存、node 名は保存
  しない) が両端で一致する場合のみ同一 suite とみなす。digest 欠測時は suite_id のみで対応付け、
  report に「digest 欠測下の対応付け」と開示
- **V14 (A21) full/targeted の保守判定**: wrapper 自身の argv 走査で判定 — full = 位置引数なし かつ
  選択系 flag (-k/-m/--lf/--ff/--deselect/--ignore/-x 等の閉表) なし かつ PYTEST_ADDOPTS 未設定/空。
  それ以外・未知 flag はすべて targeted に倒す
- **V15 (A19,A20) pytest hook の無害化**: sidecar 記録は wrapper が作る repo 外 private temp dir
  (O_EXCL、0600、絶対 path を IZANAGI_TASK_RUN_SIDECAR で子へ渡す) にのみ書く。conftest hook は env 変数
  不在なら即 no-op、本体は全体を bare try/except で包み例外を握り潰す (lazy import、module top で
  import しない)。xdist worker は no-op、controller のみ書く。障害注入テストで rc/stdout/stderr 不変を固定
- **V16 (A25,B20) privacy の型閉じ**: 全 string field は enum または safe slug
  (`^[a-z0-9][a-z0-9._-]{0,63}$`) に閉じる。自由文は objective のみ (単一行 ≤240 字、`://` 禁止)。
  `IZANAGI_TEST_SUITE_ID` env は**廃止** — suite_id は wrapper 導出のみ。scope は slug|null。
  raw command・node 名・selector 本文はどこにも保存しない
- **V17 (A24,B8) token 整合と集計分離**: 非 null ペアに対し cached≤input、total≥input、total≥output、
  3 値非 null なら total=input+output を強制。集計は (product, model) cohort 内でのみ合算し、cohort ごと
  に field coverage を併記。全体横断の token 合計は生成しない
- **V18 (A23,B16,B17) 分母の固定と打切り**: 各欠測率・比率の適用集合/分子/分母をコード定数 + README の
  式で固定。分母 0 は null (0% にしない)。not-applicable は分母から除外、not-exposed は欠測として分子。
  task_end 欠測 run は右打切りの別表 (started_at + 最終 event 時刻の下限併記) に必ず載せ、completed と
  順位・平均を混ぜない
- **V19 (B2,A2,B3) 検査網と導線**: (a) tools/check_docs.py の検査対象に output/README.md と
  output/task-runs/README.md を追加し、positive control (壊れた参照が実際に赤くなる負例) を
  test_check_docs.py に追加。(b) validate --all は root 不在・pilot.json 不在・未知 entry (run でも
  reports/ でもないもの) を赤にする。(c) 起動導線は worklog 次の一手 (クラス 2/3 セッションの必読正本)
  に pilot 手順ポインタを置く。CLAUDE.md は編集しない (pilot 実証後にユーザー提案)
- **V20 (A26) pilot manifest**: `task_run.py init-pilot <root>` が pilot.json (create-only) を生成 —
  schema_version、pilot_started_at (writer が system clock で取得)、max_task_runs=10、max_days=14。
  start は pilot.json 不在・cap 到達 (公開済み run 数 ≥10 または pilot_started_at から 14 日超) を拒否。
  task.json の measurement_policy は manifest と一致必須 (const)
- **V21 (A16) 証拠 namespace の封鎖**: root の realpath が output/campaigns・output/env・
  output/s1-freeze・output/s8b-freeze・output/s6-rounds・output/runs 配下なら拒否。task.json に const
  `"authority": "development-observation-not-evidence"` を必須追加
- **V22 (B13,A17) check 配線と削減推論の撤去**: `tools/task_run_check.py` (allowlist wrapper) が
  docs-check / provenance-check / codex-agents の**固定 argv** を自ら実行し duration/rc を test_run
  (suite_kind = docs-check/provenance-check/static-check) として記録する。raw command は記録しない。
  v1 report から「削れる工程」の推論・推奨を撤去 — 観測表のみ出す (削減判断はユーザー裁定へ)
- **V23 (A1,B4,A29,B29) producer の現実と overhead**: 自動記録 = test_run (run_tests + check wrapper)
  のみ。他 event は /dev-wave ループの親が CLI で記録する運用 (worklog 次の一手に手順を固定)。envelope
  に optional `recording_duration_s` (CLI 自身が monotonic で測る serialize+lock 待ち時間。fsync 後の
  時間は含まない — 限界として明記) を追加し、集計に操作数と overhead 合計を出す。report の主張範囲を
  「記録された event のみ。pytest/check は wrapper 実測、他は手動記録」と header に明記
- **V24 (B5) 比較の分母**: task.json に `task_kind` enum
  (implementation | audit-review | investigation | documentation | integration | other) を必須追加。
  report は task_kind 層内でのみ比較し、層に 1 run しかなければ比較 KPI を出さない。pilot 対象 =
  クラス 2/3 セッション + 長時間 class-1 監査の opt-in (task_class=1 で記録)
- **V25 (B1,B22) 契約改訂の明文化**: D66 で「D13 の二軸 = 実験証拠。task-runs = 直交する開発運用
  namespace (証拠ではない)」を明示改訂し、output/README.md の tree を現行実装 (exploration/ 含む) に
  整合させる。worklog へは task_run_id・異常・裁定のみ (集約値は report 側)。D53 provenance trailer の
  母集団 (採用寄与のみ) と agent_run event の母集団 (failed/不採用含む) の差を README に明記
- **V26 (B10) 破損時の縮退**: aggregator の既定は「damaged run が 1 件でもあれば report を出さず非 0
  終了」を維持。ただし `--diagnostic` flag で「damaged 一覧 (run ID + 破損理由) + 健全 run のみの観測表 +
  『不完全』headline」の診断 report を生成できる (silent skip は禁止のまま)。torn append の physical
  復旧は v1 では行わない (bytes 保全 + 隔離のみ)

## E 単位分割 (v2)

- **E1 (core)**: tools/task_runs/{__init__.py, schema_v1.json, schema.py, ledger.py, cli.py}、
  tools/task_run.py、orchestrator/tests/test_task_run_ledger.py。
  凍結 API (E2/E3 はこれ以外に依存禁止): SCHEMA_VERSION、LedgerError/DamagedRunError、ValidatedRun、
  `start_run(root, *, slug, objective, task_class, task_kind) -> str`、
  `append_event(root, task_run_id, event_type, payload) -> Mapping` (writer が seq/ts/source/event_id 付与)、
  `record_test_run(root, task_run_id, *, suite_id, suite_kind, duration_s, exit_status, counts, trigger,
  collected_node_digest) -> Mapping` (wrapper 専用強 source)、
  `finish_run(root, task_run_id, outcome) -> Mapping`、
  `validate_run(run_dir, *, require_finished=False) -> ValidatedRun`、
  `validate_root(root) -> RootReport` (published/incomplete/damaged/unknown の分類)、
  `discover_runs(root) -> tuple[Path, ...]`、`init_pilot(root) -> None`。
  CLI: start / event <type> / finish / validate [--all] / init-pilot / selfcheck
- **E2 (test recording)**: tools/run_tests.py (追記編集)、orchestrator/tests/conftest.py (追記編集)、
  tools/task_runs/pytest_stats.py、tools/task_run_check.py、orchestrator/tests/test_run_tests_task_run.py
- **E3 (集計 + 検査網)**: tools/task_runs/aggregate.py、tools/task_run_report.py、
  orchestrator/tests/test_task_run_aggregate.py、tools/check_docs.py (追記編集) +
  orchestrator/tests/test_check_docs.py (追記編集)
- 投入順: **E1 先行 → E1 差分を取り込んで E2 ∥ E3 並列** (E2/E3 のテストが tools.task_runs の実在に
  依存するため。interface は上記で凍結済み)
- 親: docs 一式 (output/task-runs/README.md、output/README.md、docs/README.md、D66、worklog)、統合、
  変異 matrix 実測、受入全走、最初の実 task-run 記録 (この wave 自身を dogfooding)

## 変異事前登録 (B-057) — 実装前凍結

各変異は「実装後に親が単独適用し、対応テストが赤くなること (KILL) を実測する」。plan v1 の 23 候補は
V 系列で無効になったものを差し替え、以下 32 本を登録する。

- M01 validator: 末尾 truncate 行を campaign WAL 同様に黙って捨てる → truncate 負例テスト
- M02 validator: seq gap 許容 (`seq > prev` のみ) → gap 負例
- M03 validator: seq 重複検査を削除 → 重複負例
- M04 validator: 未知 schema_version 受理 → 未知 schema 負例
- M05 validator: 未知 event 型を汎用受理 → 未知 event 負例
- M06 validator: timestamp 逆行検査を削除 → 逆行負例
- M07 validator: naive timestamp を UTC とみなす → naive 負例
- M08 validator: 負 duration 許容 → 負 duration 負例
- M09 validator: total≠input+output 許容 → token 不整合負例
- M10 validator: cached>input 許容 → cached 超過負例
- M11 validator: not-exposed なのに実値ありを許容 → 矛盾負例
- M12 validator: event_id 重複許容 → 重複 event_id 負例
- M13 validator: 存在しない stage_id 参照を許容 → 参照負例
- M14 validator: open stage 2 件を許容 → 多重 open 負例
- M15 validator: task_end 後の作業 event を許容 → post-end 負例
- M16 validator: task_end 時 open stage 残置を許容 → 未閉鎖 end 負例
- M17 writer: task.json を "w" 上書きに変更 → create-only/byte 保存テスト
- M18 writer: 候補事前検証を外し「書いてから次回検出」に → 不正 payload 時 bytes 不変テスト
- M19 writer: 生成順を task.json 先行に変更 → incomplete-start 分類テスト (publish marker 意味論)
- M20 writer: flock 呼び出しを削除 → 2 プロセス並行 append の全件保持・連番テスト
- M21 writer: 冪等再試行を無条件再 append に → 重複 event_id 検出テスト (V5)
- M22 writer: base_commit を caller 引数に戻す (git 実測を外す) → git-observed source テスト
- M23 writer: commit event の cat-file 実在確認を削除 → 偽 SHA 拒否テスト
- M24 writer: root containment 検査を削除 → campaigns 配下 root 拒否テスト
- M25 writer: pilot cap 検査を削除 → 11 件目 start 拒否テスト
- M26 schema: suite_id 等の slug pattern を外し自由文字列化 → privacy 負例 (raw command 様文字列の拒否)
- M27 run_tests: 記録失敗時に wrapper が child rc を差し替える → rc 保存テスト
- M28 run_tests: full/targeted 判定を「位置引数のみ」に緩める (PYTEST_ADDOPTS 無視) → ADDOPTS 負例
- M29 conftest hook: try/except を外す → 障害注入時 rc 不変テスト
- M30 aggregate: damaged run を warning でスキップして report 生成 → 既定 fail-closed テスト
- M31 aggregate: rc≠0 をすべて red 扱いに → rc 5→0 が cycle にならないテスト
- M32 aggregate: 右打切り run を completed と混ぜて順位付け → 打切り分離テスト

## 検収順 (v2)

1. E1 targeted → 2. E2/E3 targeted → 3. 隣接既存 (test_run_tests_nproc / test_plain_runner_coverage /
test_check_docs / campaign WAL 系) → 4. 変異 matrix M01〜M32 実測 → 5. 全走 (run_tests.py) 反復 →
6. check_codex_agents / check_docs → 7. 親 docs 統合 + dogfooding task-run 記録 → 8. commit +
check_ai_provenance (AI-Agent trailer、push なし)

## 6. 実装報告 E1 (core) — 逐語

E1 core を実装しました。許可された 7 ファイル以外は編集せず、git add/commit も行っていません。

実装内容:

- Draft 7 closed schema、strict JSON/JSONL 検査
- UTF-8、BOM、NUL、CR、NFC、duplicate key、NaN、サイズ上限
- seq/timestamp/stage/task_end/token/ID 間 invariant
- pilot manifest、cap、incomplete/damaged/unknown 分類
- create-only publish marker、O_NOFOLLOW、flock、O_APPEND、fsync
- 仮想 stream 事前検証と失敗時 byte 不変
- event_id による曖昧な fsync 失敗の冪等確認
- git HEAD/commit 実在確認
- typed CLI と filesystem selfcheck
- privacy slug、証拠 namespace 拒否、task authority
- writer 管理の seq/timestamp/source/event_id、ms 精度 duration、recording overhead

V 対応は V1〜V5、V7〜V9、V12、V16〜V17、V20〜V21、V23〜V24 の E1 範囲を反映しています。

検証結果:

- 指定コマンド: `64 passed in 2.01s`
- 自走 harness: `64 passed`
- plain-runner coverage: `3 passed`
- `check_codex_agents.py`: OK
- `check_docs.py`: 違反なし
- schema JSON/meta-schema、`git diff --check`: OK

テストは M01〜M26 の E1 変異を KILL 可能な負例を収録しています。実際の変異 matrix 適用は親の統合検収事項なので未実施です。E2/E3 の記録配線・集計器・docs は編集許可外のため実装していません。

主要ファイル: [ledger.py](/home/SFC/tanab/github/izanagi/.claude/worktrees/taskrun-e1/tools/task_runs/ledger.py)、[schema.py](/home/SFC/tanab/github/izanagi/.claude/worktrees/taskrun-e1/tools/task_runs/schema.py)、[test_task_run_ledger.py](/home/SFC/tanab/github/izanagi/.claude/worktrees/taskrun-e1/orchestrator/tests/test_task_run_ledger.py)
## 7. 実装報告 E2 (test recording) — 逐語

E2 の test-run 記録を実装しました。E1 ファイル、docs、git index/commit は変更していません。

実装:

- [run_tests.py](/home/SFC/tanab/github/izanagi/.claude/worktrees/taskrun-e2/tools/run_tests.py)
  - 明示 opt-in、suite fingerprint、monotonic duration、E1 経由の fail-open 記録
  - opt-in なしの command・stdio・rc を維持
- [pytest_stats.py](/home/SFC/tanab/github/izanagi/.claude/worktrees/taskrun-e2/tools/task_runs/pytest_stats.py)
  - controller-only sidecar、O_EXCL/0600、集計値と node 集合 digest のみ保存
- [conftest.py](/home/SFC/tanab/github/izanagi/.claude/worktrees/taskrun-e2/orchestrator/tests/conftest.py)
  - env 即 no-op、lazy import、bare exception handling、xdist worker no-op
- [task_run_check.py](/home/SFC/tanab/github/izanagi/.claude/worktrees/taskrun-e2/tools/task_run_check.py)
  - docs/provenance/static の固定 argv allowlist
- [test_run_tests_task_run.py](/home/SFC/tanab/github/izanagi/.claude/worktrees/taskrun-e2/orchestrator/tests/test_run_tests_task_run.py)
  - E2 回帰・障害注入テスト 28 件と自走 harness

V 対応:

- V13: 実収集 node ID 集合の SHA-256 先頭12桁のみ記録
- V14: 位置引数、選択 flag、未知 flag、非空 `PYTEST_ADDOPTS` を targeted 判定
- V15: private sidecar、controller-only、import/I/O/破損時も rc・出力不変
- V16: suite ID は wrapper 導出のみ。`IZANAGI_TEST_SUITE_ID` は未実装
- V22: check wrapper は3種類の固定 argv のみ
- V5: E1 `record_test_run()` の冪等プロトコルを利用し、失敗時は最小記録を一度だけ再試行

緑の証拠:

```text
指定合同走: 105 passed in 2.09s
E2 単体:    28 passed
plain-runner coverage: 3 passed
check_codex_agents: OK
check_docs: 違反なし
git diff --check: clean
```

できなかった項目はありません。git commit/add と commit 後 provenance 検査は明示禁止のため実施していません。
## 8. 実装報告 E3 (集計 + 検査網) — 逐語

実装単位 E3 を完了しました。E1/E2・docs・git 状態には変更していません。

### 実装

- [aggregate.py](/home/SFC/tanab/github/izanagi/.claude/worktrees/taskrun-e3/tools/task_runs/aggregate.py:200)
  - run 集計、欠測率、時間分解、red→green、token cohort、右打切り分離
  - damaged 時の fail-closed／`--diagnostic`
  - root/event lock 下の cohort 確定
  - final seq と両ファイル SHA-256 の入力束縛
  - fsync・create-only atomic publish
  - 決定的 Markdown renderer
- [task_run_report.py](/home/SFC/tanab/github/izanagi/.claude/worktrees/taskrun-e3/tools/task_run_report.py)
  - report CLI
- [check_docs.py](/home/SFC/tanab/github/izanagi/.claude/worktrees/taskrun-e3/tools/check_docs.py:30)
  - `output/README.md`
  - `output/task-runs/README.md`
  を living docs 検査へ追加
- [test_task_run_aggregate.py](/home/SFC/tanab/github/izanagi/.claude/worktrees/taskrun-e3/orchestrator/tests/test_task_run_aggregate.py:145)
  - 手計算 exact fixture、破損、診断、決定性、create-only、打切り、task_kind/token 分離など10テスト
- [test_check_docs.py](/home/SFC/tanab/github/izanagi/.claude/worktrees/taskrun-e3/orchestrator/tests/test_check_docs.py:124)
  - 合成 repo の正例、README 不在、壊れた参照の positive control を追加

### 検査結果

指定コマンド:

```text
80 passed in 2.01s
```

内訳は aggregate 10、check_docs 6、E1 ledger regression 64です。

追加検査:

```text
test_plain_runner_coverage.py: 3 passed
check_codex_agents.py: OK
git diff --check: clean
```

自走 harness も aggregate `10 passed`、check_docs `6 passed, 0 failed` です。

### V 対応

- V11: lock、入力 hash/final seq、fsync、上書き禁止 publish
- V12/V18: 非排他的時間、負値保持＋不整合、固定分母、0分母=`null`、右打切り別表
- V13: rc 1だけred、infra非介入、digest対応と欠測開示
- V17: task_kind/product/model 内だけのtoken合算とfield coverage
- V19a: 2 READMEの検査編入と正負fixture
- V22/V23: 観測表限定、主張範囲header、操作数・recording overhead
- V24: task_kind内比較のみ、完了runが1件なら比較なし
- V26: 通常は破損1件で無出力、診断時のみ「不完全」report
- report本文にwall clockを使わず、同一入力から同一bytes

### できなかった項目

`python3 tools/check_docs.py` 全体は、親が統合時に作成する `output/task-runs/README.md` 不在の1件だけで、予定どおり赤です。編集禁止のためREADME作成、handoff/worklog更新、git add/commitは行っていません。
## 9. 敵対レビュー R1: プラン整合・恒真化レンズ (high) — 逐語

結論は **NO-GO**。コード本体は広く実装されていますが、V10/V15/V18/V19/V23/V25 と変異テストに実穴があります。

## 所見

1. **V10: 最終 report 後の pilot 凍結が実装されていない**

   - real度: **確実**
   - 重大度: **must-fix**
   - 根拠: [ledger.py:354](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/tools/task_runs/ledger.py:354) の `start_run()` は damaged/unknown、件数、日数だけを検査し、report/frozen 状態を見ない。一方 [README.md:23](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/output/task-runs/README.md:23) は「最終 report 後に新規 start 拒否」と断言している。現 API には report を「最終」と指定する状態もない。
   - 反例: cap 未到達で report を publish した後も `start_run()` は成功する。
   - 修正案: create-only の凍結 marker と final-publish 操作を追加し、`start_run()` が root lock 内で拒否する。

2. **V10: merge 後の cap 超過を report が開示しない**

   - real度: **確実**
   - 重大度: **must-fix**
   - 根拠: [aggregate.py:473](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/tools/task_runs/aggregate.py:473) は `healthy_runs` を出すだけで、pilot の `max_task_runs` と比較しない。[aggregate.py:733](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/tools/task_runs/aggregate.py:733) にも超過判定がない。[README.md:72](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/output/task-runs/README.md:72) の「report が検出・開示」は恒真化している。
   - 反例: worktree union で published run を11件置くと、通常 report は生成されるが `cap_exceeded` が出ない。
   - 修正案: manifest 上限と published 数を report 入力に束縛し、超過数とフラグを必ず表示する。

3. **V15: hook が caller 任意の絶対 path に sidecar を作成できる**

   - real度: **確実**
   - 重大度: **must-fix**
   - 根拠: wrapper は [run_tests.py:298](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/tools/run_tests.py:298) で repo 外 private dir を作るが、hook 側の [pytest_stats.py:85](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/tools/task_runs/pytest_stats.py:85) は absolute path かだけを検査し、[pytest_stats.py:112](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/tools/task_runs/pytest_stats.py:112) が env 値をそのまま使用する。
   - 反例: `IZANAGI_TASK_RUN_SIDECAR=<repo内の未存在絶対path>` を設定して素の pytest を起動すると、wrapper 作成でない repo 内 sidecar を作れる。
   - 修正案: repo 外・親 directory の owner/mode・固定 basename を hook 側でも検証し、違反時は no-op にする。

4. **V23: `recording_duration_s` の実測範囲が裁定・README と不一致**

   - real度: **確実**
   - 重大度: **must-fix**
   - 根拠: timer は [ledger.py:525](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/tools/task_runs/ledger.py:525) で開始し、root/pilot 読取、既存 stream 全検証、stage 検索、commit の `git cat-file` まで含めて [ledger.py:599](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/tools/task_runs/ledger.py:599) で確定する。[README.md:78](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/output/task-runs/README.md:78) の「serialize + lock 待ちのみ」ではない。
   - 反例: 大きい既存 ledger や commit event では、全再検証/git subprocess 時間まで overhead に入る。
   - 修正案: lock 待ちと serialize の区間を個別計測して加算するか、裁定を変更して metric 名・説明を実態へ合わせる。

5. **V9: selfcheck のテストが no-op 変異でも緑になる**

   - real度: **確実**
   - 重大度: **must-fix**
   - 根拠: [test_task_run_ledger.py:824](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/tests/test_task_run_ledger.py:824) は「呼出後に unknown entry がない」だけを検査する。`selfcheck()` 本体を `return None` にしても成立する。
   - 再現: `ledger.selfcheck` を monkeypatch で no-op にして同 assertion を実行すれば緑。
   - 修正案: O_EXCL/flock/O_APPEND の各 failure 注入が非0/例外になる positive control を追加する。

6. **M10 の負例は別理由でも落ちるため、cached≤input 変異を KILL できない**

   - real度: **確実**
   - 重大度: **must-fix**
   - 根拠: [test_task_run_ledger.py:425](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/tests/test_task_run_ledger.py:425) は全 token が null の event、すなわち source=`not-exposed` を作ってから input/cached に実値を入れる。cached 超過検査を削除しても「not-exposed なのに実値あり」で落ちる。
   - 反例: [schema.py:332](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/tools/task_runs/schema.py:332) の cached 比較だけを削除しても、同テストは `_validate_source()` で赤のまま。
   - 修正案: 最初から `product-reported` の整合した token event を作り、cached だけを input 超過へ変異する。

7. **M17 のテストは task.json の open 面へ到達しない**

   - real度: **確実**
   - 重大度: **must-fix**
   - 根拠: [test_task_run_ledger.py:167](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/tests/test_task_run_ledger.py:167) の二回目 start は既存 run directory に対する `os.mkdir` で止まる。task.json の `O_EXCL` を `"w"` 上書きへ変えても対象コードは呼ばれない。
   - 反例: task.json 用 `_create_file` の flags だけを上書き型へ変えても、このテストは同じ `LedgerError` と byte 同一性で緑。
   - 修正案: 既存 task.json に対して task publish helper を直接発火させ、上書き拒否と bytes 不変を固定する。

8. **M06 の timestamp 逆行負例が wall clock 偶然性に依存する**

   - real度: **要検証**
   - 重大度: **should**
   - 根拠: [test_task_run_ledger.py:356](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/tests/test_task_run_ledger.py:356) は二件目を `started_at` へ戻すが、一件目が丸め後に `started_at` と同値なら逆行にならない。
   - 反例: `_utc_now` を全呼出で同一 millisecond に固定すると負例が成立しない。
   - 修正案: writer clock を明示時系列へ monkeypatch し、`event[0] > event[1] >= started_at` を fixture 自体で assert する。

9. **M29 は sessionfinish しか障害注入しておらず、他 hook の try/except 削除を検出しない**

   - real度: **要検証**
   - 重大度: **should**
   - 根拠: [test_run_tests_task_run.py:257](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/tests/test_run_tests_task_run.py:257) は `pytest_sessionfinish` のみ。`pytest_collection_finish` と `pytest_xdist_node_collection_finished` の例外握り潰しは未固定。
   - 反例: collection hook の try/except だけを削除しても現障害注入テストは緑。
   - 修正案: 三 hook を parametrized fault-injection で検査する。

10. **schema の source 閉表・nested unknown-field がテスト上は恒真化し得る**

   - real度: **確実**
   - 重大度: **should**
   - 根拠: [test_task_run_ledger.py:140](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/tests/test_task_run_ledger.py:140) は schema の meta-validity と API signature だけ。schema の各 if/then source 組合せ、pilot/task/source/tokens の未知 field を jsonschema へ与える負例がない。M26 だけは個別検査される。
   - 反例: `source_stage_end.duration` の const や nested `additionalProperties:false` を外しても、runtime 自前 validator が残るため既存テストはほぼ緑。
   - 修正案: 全 event/source の valid/invalid matrixと各 object の unknown-field負例を schema へ直接通す。

11. **V19/V25 の親 docs 配線が現在の working tree では未完で、check_docs が実際に赤い**

   - real度: **確実**
   - 重大度: **must-fix**
   - 根拠: [output/task-runs/README.md:5](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/output/task-runs/README.md:5) は未存在の D66 を参照する。実行結果は `check_docs: 1 件の違反 ... 実在しない D 参照 'D66'`。[output/README.md:5](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/output/README.md:5) の tree に `task-runs/` と `exploration/` がなく、[docs/worklog.md:1013](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/docs/worklog.md:1013) の現「次の一手」に pilot 手順もない。
   - 再現: `PYTHONDONTWRITEBYTECODE=1 python3 -B tools/check_docs.py` → rc 1。
   - 修正案: D66、output tree、worklog 起動ポインタを親統合で同時に land し、check_docs を再実行する。

12. **V18 の固定式が README にない／report CLI 例も実行不能**

   - real度: **確実**
   - 重大度: **should**
   - 根拠: コードは `RATE_DEFINITIONS` を report に出すが、[output/task-runs/README.md:88](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/output/task-runs/README.md:88) は適用集合・分子・分母を列挙していない。また [README.md:48](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/output/task-runs/README.md:48) は引数なし report コマンドを示すが、[aggregate.py:801](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/tools/task_runs/aggregate.py:801) は root と destination を必須にする。
   - 反例: README の通り `python3 tools/task_run_report.py` を実行すると argparse error。
   - 修正案: `RATE_DEFINITIONS` と同じ式表を README に置き、CLI 例へ root/output を明記する。

## V1〜V26 照合

| V | 判定 | 根拠概要 |
|---|---|---|
| V1 | 実装 | 0 byte、open stage、require_finished、task_end 検査あり |
| V2 | 実装 | virtual stream 全検証後に write、bytes 不変テストあり |
| V3 | 実装 | writer field 専有、source 閉表あり。ただし schema 回帰不足は所見10 |
| V4 | 実装 | HEAD 実測、commit cat-file 検査あり |
| V5 | 実装 | event_id 一意、同ID曖昧失敗回復、参照/ID invariantあり |
| V6 | **部分** | README の格下げはあるが D66 未実装 |
| V7 | 実装 | events→task publish marker、incomplete 分類あり |
| V8 | 実装 | root/events flock、append 同一fd、O_NOFOLLOW/fstatあり |
| V9 | **部分** | selfcheck 本体はあるが no-op を見抜けないテスト |
| V10 | **未達** | cap 開示・final freeze 欠落 |
| V11 | 実装 | root/event lock、digest/final_seq、create-only atomic publish |
| V12 | 実装 | timestamp delta、非排他集計、負値非clamp |
| V13 | 実装 | rc=1のみred、infra分離、digest-aware cycle |
| V14 | 実装 | ADDOPTS・未知flagをtargetedへ倒す |
| V15 | **部分** | fail-open/xdist/private tempはあるがhook側path境界がない |
| V16 | 実装 | typed fields、suite env廃止、hashed suite identity |
| V17 | 実装 | token invariant/cohort coverageあり |
| V18 | **部分** | コード/report式はあるがREADME固定式なし |
| V19 | **部分** | check_docs列挙・positive control・validate rootはあり、worklog導線なし |
| V20 | 実装 | pilot manifest、10件/14日、policy constあり |
| V21 | 実装 | evidence namespace拒否、authority constあり |
| V22 | 実装 | 固定argv check wrapper、削減推論なし |
| V23 | **部分** | producer/headerは整合、overhead計測範囲が不一致 |
| V24 | 実装 | task_kind層内比較、1件時KPIなし |
| V25 | **未達** | D66/output tree/worklog配線が未統合 |
| V26 | 実装 | 既定fail-closed、明示diagnosticのみ健全run集計 |

## M01〜M32 の未防御候補

明確な問題は以下です。

- **M10:** KILL不能。負例が token source 矛盾でも落ちる。
- **M17:** KILL不能。run directory 衝突で task.json open 面へ到達しない。
- **M06:** KILLが時刻偶然性に依存。
- **M29:** sessionfinish は KILL可能だが、collection系 hook の同変異は未防御。

M26 は `jsonschema` がない環境では schema 側変異を検査しない条件分岐ですが、現在環境には `jsonschema 3.2.0` があるため、この環境の matrix では実行可能です。残る M01〜M05、M07〜M09、M11〜M16、M18〜M28、M30〜M32 は静的には直接 assertion が対応しています。ただし今回は後述の sandbox 制約により実 KILL は未測定です。

## 所見ゼロの観点

- **凍結 API:** 不一致なし。公開 signature と export は指定 API に整合。
- **E1/E2/E3 の縫い目:** 不正な E1 内部依存なし。E2 は `record_test_run`、E3 は `ValidatedRun`・validator API 等の凍結面だけを利用。
- **現行 runtime validator の unknown field/if-then:** 実装自体は `_exact_keys` と source table で閉じている。所見10は弱体化を見抜けないテスト問題。
- **V13/V18 の集計分離:** rc=5 は infra、右打切りは比較母集団外、token は cohort 分離されており、現コード上の恒真条件は見つからなかった。

検証は `git diff --check`、14 Python file の AST parse、schema JSON parse が成功。`check_docs.py` は上記 D66 不在で rc 1。targeted pytest は実行を試みましたが、sandbox が `/tmp` を含む全 temporary directory への書込みを禁止しており、pytest 初期化前に `No usable temporary directory found` で停止したため、テスト green や mutation KILL は主張しません。
## 10. 敵対レビュー R2: 正しさ境界・意味論レンズ (high) — 逐語

# R2 裁定: NO-GO

未コミット差分に must-fix 13 件、should 2 件を確認した。

1. **wrapper の再試行が同一 event_id にならず、二重記録する** — (a) 確実、(b) must-fix。  
   (c) [run_tests.py:332](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/tools/run_tests.py:332)、[task_run_check.py:43](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/tools/task_run_check.py:43)、[ledger.py:592](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/tools/task_runs/ledger.py:592)。最初の `record_test_run` が fsync 後の unlock/close や SIGINT で例外になった場合、二回目は新しい event_id を生成する。純関数 probe でも二回呼ばれることを確認した。  
   (d) wrapper 側の二回目呼出しを削除し、曖昧 write の解決は E1 内の同一 event_id プロトコルだけに限定する。

2. **child 終了後の同期記録が rc 返却を最大約10秒遅延し、SIGINT を握り潰す** — (a) 確実、(b) must-fix。  
   (c) [run_tests.py:391](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/tools/run_tests.py:391)、[ledger.py:484](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/tools/task_runs/ledger.py:484)。5秒 lock timeout を二回試せるうえ、`BaseException` が `KeyboardInterrupt` まで飲む。probe では `keyboardinterrupt_propagated=False`。check wrapper も同型。  
   (d) `BaseException` を捕捉せず、記録は単発かつ短い上限時間で行い、SIGINT/SystemExit は必ず再送出する。

3. **テストを実行しない pytest invocation が full/green になる** — (a) 確実、(b) must-fix。  
   (c) [run_tests.py:60](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/tools/run_tests.py:60)、[run_tests.py:222](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/tools/run_tests.py:222)。`--help`、`--version`、`--setup-plan`、`--setup-only` はすべて `('full', 'pytest-orchestrator-full')` となる。rc=0 なら full green として red cycle を閉じ得る。  
   (d) 早期終了・非実行 flag を targeted/infra に倒し、実収集・実行を確認できない invocation は full にしない。

4. **sidecar 環境変数が wrapper 専用 capability になっていない** — (a) 確実、(b) must-fix。  
   (c) [conftest.py:119](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/tests/conftest.py:119)、[pytest_stats.py:85](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/tools/task_runs/pytest_stats.py:85)。直接 pytest で任意の絶対 path を `IZANAGI_TASK_RUN_SIDECAR` に設定すれば、task-run opt-in 無しでもその場所へ O_EXCL write する。またテスト本体は同 env を読んで sidecar を先に作成でき、任意 counts/digest が `wrapper-observed` として記録される。  
   (d) 内部 activation を検証し、親directoryのrepo外・0700・所有者を確認する。child生成 metrics は強 source から格下げする。

5. **`git-observed` が継承 `GIT_*` 環境で偽装できる** — (a) 確実、(b) must-fix。  
   (c) [ledger.py:213](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/tools/task_runs/ledger.py:213)。実測で通常は `9cbe36…`、`GIT_DIR=<ccbench gitdir>` 設定後は同じ `_git_head(worktree)` が `d70665…` を返した。commit 実在確認も同じ経路。  
   (d) `GIT_DIR/GIT_WORK_TREE/GIT_OBJECT_DIRECTORY/GIT_ALTERNATE_OBJECT_DIRECTORIES` 等を除去し、期待する worktree top-level と一致確認する。

6. **O_NOFOLLOW が最終成分しか守らず、directory 差替え race で containment を迂回できる** — (a) 要検証、(b) must-fix。  
   (c) [ledger.py:119](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/tools/task_runs/ledger.py:119)、[ledger.py:542](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/tools/task_runs/ledger.py:542)。root/run_dir の lstat 後にdirectoryをrenameし symlinkへ差し替えると、後続 `root / run_id / events.jsonl` は中間 symlink を辿る。report 側は [aggregate.py:656](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/tools/task_runs/aggregate.py:656) で O_NOFOLLOW 不在時に `0` へ縮退する。  
   (d) root/run directory fd を保持し、`openat2(RESOLVE_BENEATH|RESOLVE_NO_SYMLINKS)` またはdir_fd連鎖で全成分を固定する。

7. **report/validate が events flock を取る前に stream を読み、健全な並行 append を damaged と誤判定する** — (a) 確実、(b) must-fix。  
   (c) [aggregate.py:733](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/tools/task_runs/aggregate.py:733) は `validate_root` 後に初めて event lock を取る。一方 [ledger.py:433](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/tools/task_runs/ledger.py:433) の validator は flock 無し。短い部分 write を注入して同時に diagnostic report を走らせると、一時的な末尾断片を恒久 damaged としてpublishできる。  
   (d) discovery後、各 events fd を安定順にlockして、その同一fdからvalidateする。

8. **report digest が集計した bytes に束縛されていない** — (a) 確実、(b) must-fix。  
   (c) [aggregate.py:436](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/tools/task_runs/aggregate.py:436)、[aggregate.py:742](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/tools/task_runs/aggregate.py:742)。`validate_run` の後で `_manifest` が path を再openするため、その間のrename差替えで「Aを集計、BのSHAを掲載」が成立する。lockは旧inodeに残る。  
   (d) validateに用いた同一fdのraw bytesからSHAを計算し、再openしない。

9. **diagnostic report が自由文字列を永続化する** — (a) 確実、(b) must-fix。  
   (c) [schema.py:211](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/tools/task_runs/schema.py:211) は不正値を例外本文へ埋め、[aggregate.py:484](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/tools/task_runs/aggregate.py:484) はreasonをreportへそのまま書く。未知root entry名も無制約。probeで `pytest -k TOP_SECRET` が診断report bytesへ残ることを確認した。  
   (d) 永続化する破損理由を閉じたreason codeにし、entry名はsafe IDまたはdigestだけにする。

10. **有限な個別 duration から集計値 `inf`/`nan` が生成される** — (a) 確実、(b) must-fix。  
    (c) [schema.py:218](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/tools/task_runs/schema.py:218) は `1e308` を許容し、[aggregate.py:108](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/tools/task_runs/aggregate.py:108) の二件加算は `inf` になった。`inf/inf` は `nan` となり得る。  
    (d) durationへ現実的上限を設け、全sum・ratio後にも `math.isfinite` を強制する。

11. **merge後の pilot cap 超過を検出・開示しない** — (a) 確実、(b) must-fix。  
    (c) [ledger.py:373](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/tools/task_runs/ledger.py:373) は新規startだけを止めるが、`validate_root`/reportには published run数検査がない。[README.md:72](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/output/task-runs/README.md:72) の「reportが検出・開示」と不一致。11 directoryをunionしたrootは通常report対象になる。  
    (d) root reportへcap超過状態を追加し、通常・diagnostic report双方で明示する。

12. **最終report後の pilot freeze が未実装** — (a) 確実、(b) must-fix。  
    (c) [README.md:23](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/output/task-runs/README.md:23) は新規start拒否を契約するが、[aggregate.py:709](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/tools/task_runs/aggregate.py:709) はfreeze markerを作らず、startはcap/ageしか見ない。そもそも「final」を指定するsurfaceもない。  
    (d) create-only freeze markerと明示的final publish操作を追加し、startがmarker存在時に拒否する。

13. **`recording_duration_s` が文書の式と違う** — (a) 確実、(b) should。  
    (c) [ledger.py:525](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/tools/task_runs/ledger.py:525) から計時するため、root/pilot読取・既存stream全parse・validation・git確認まで含む一方、最終serialize/writeは含まない。[README.md:78](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/output/task-runs/README.md:78) の「serialize + lock待ちのみ」ではない。run長に応じて増え、overhead比較を歪める。  
    (d) 計測境界を式どおりに置くか、実際の「append pre-write latency」へ名称・説明を変更する。

14. **F9/F21型: 実repo検査を削除した結果、現在の赤がtargeted testから蒸発している** — (a) 確実、(b) must-fix。  
    (c) [test_check_docs.py:124](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/tests/test_check_docs.py:124) は合成fixtureだけを検査し、従来の `test_real_repo_clean` を削除した。実際に `python3 tools/check_docs.py` は [output/task-runs/README.md:5](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/output/task-runs/README.md:5) の不在D66参照でrc=1。  
    (d) D66を実体化し、合成positive controlに加えて実repo clean testを復元する。

15. **xdist controller結線がlive実測されていない** — (a) 要検証、(b) should。  
    (c) hookは [conftest.py:132](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/tests/conftest.py:132) にあるが、実pytest integration testは [test_run_tests_task_run.py:326](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/tests/test_run_tests_task_run.py:326) で強制的にxdistを無効化している。worker testもfake objectのみ。F21と同じ「単体hook健全≠runtime配送健全」。  
    (d) `-n 2 --dist loadgroup` の実subprocessでcontroller一回だけのsidecar、digest、rc/stdout/stderr不変を固定する。

## 所見ゼロだった観点

- clean envで `IZANAGI_TASK_RUN_ID` と内部sidecar envが共に無い通常経路は、command・stdio・rc・child envとも従来どおり `subprocess.call(cmd)`。追加importもstdlibのみ。
- prospective append検証、O_EXCL、events→task順、fsync-before-report-rename、部分write loop、root→eventsのlock順序自体には、上記race以外の破れを確認しなかった。
- null→0混入、分母0、右打切り混入、damaged silent skip、rc 2–5/signalのred化は確認しなかった。通常集計の安定sortも決定的。
- F2 discovery分裂は `_classify_root` への集約で再発なし。F3の性能証拠化もなし。F23/F24型のstdin待ち・ログ本文grep完了判定もない。
- clean env時のcampaign/check系への常時import・環境汚染は確認しなかった。

検査実績: `check_codex_agents.py` は成功、`git diff --check` は成功。pytestは実装失敗ではなく、このsandboxに書込み可能な一時directoryがなく、capture初期化前に実行不能だった。
## 11. 親裁定 — レビュー統合 (F-1〜F-23)

# 親裁定 — 敵対レビュー R1 (12 所見) + R2 (15 所見) の統合

判定: **refuted 0。全所見 real。** 重複統合後の fix 項目 F-1〜F-23 を確定する。
F-13/F-22/F-23 は docs 側 (親担当)、それ以外はコード fix (単一 codex 単位、E1/E2/E3 横断を親が許可)。

## コード fix (実装单位へ)

- **F-1 (R2-1)**: wrapper (run_tests.py / task_run_check.py) の二回目 record 呼出しを削除。曖昧 write の
  解決は E1 の同一 event_id 冪等プロトコルだけに限定する
- **F-2 (R2-2)**: 記録経路で BaseException を捕捉しない (Exception のみ)。KeyboardInterrupt /
  SystemExit は必ず再送出。lock timeout は単発・短縮 (2s) し、rc 返却遅延の上限を下げる
- **F-3 (R2-3)**: --help/--version/--setup-only/--setup-plan/--collect-only 等の非実行 flag を full に
  しない (選択系 flag の閉表へ追加、targeted へ倒す)。実行を確認できない invocation は full 禁止
- **F-4 (R1-3, R2-4)**: pytest_stats hook 側でも sidecar path を検証 (絶対 path・repo 外・親 dir が
  自 uid 所有かつ 0700・固定 basename prefix)。違反時は no-op。sidecar 由来 counts/digest の
  measurement_source は `tool-reported` へ格下げ (wrapper-observed を名乗らない)
- **F-5 (R2-5)**: git 実測 subprocess から GIT_DIR / GIT_WORK_TREE / GIT_INDEX_FILE /
  GIT_OBJECT_DIRECTORY / GIT_ALTERNATE_OBJECT_DIRECTORIES / GIT_CEILING_DIRECTORIES を除去し、
  toplevel が期待 repo root と一致することを確認する
- **F-6 (R2-6)**: root→run→file を dir_fd 連鎖 (os.open dir_fd= + O_NOFOLLOW を各成分に) で開き、
  中間 symlink 差替え race を遮断する (openat2 は使わず dir_fd で可)
- **F-7 (R2-7)**: report/validate --all の cohort 読取は各 events fd を安定順に flock してから同一 fd で
  validate する (lock 前読みの transient damaged 誤判定を遮断)
- **F-8 (R2-8)**: report の SHA-256 は validate に使った同一 fd の bytes から計算 (path 再 open 禁止)。
  ValidatedRun に task_bytes_sha256 / events_bytes_sha256 / final_seq を追加してよい (凍結 API の
  追加拡張を親が許可)
- **F-9 (R2-9)**: report へ永続化する破損理由を閉じた reason code 集合にし、entry 名は safe slug 検査
  通過分のみ・他は digest 表記。例外 message 本文を report へ流さない
- **F-10 (R2-10)**: duration_s に現実的上限 (≤ 10^7 s) を schema で強制し、集計の全 sum/ratio 出力に
  math.isfinite を強制 (非有限は集計エラー)
- **F-11 (R1-1, R2-12)**: `task_run_report.py --final` を追加 — root lock 下で report publish +
  create-only の pilot freeze marker を生成。start_run は marker 存在で拒否
- **F-12 (R1-2, R2-11)**: validate_root が published run 数 vs manifest cap を数え、report (通常・
  diagnostic 双方) が cap 状態と超過数を必ず表示する
- **F-14 (R1-5)**: selfcheck の positive control — O_EXCL/flock/O_APPEND/fsync の failure 注入で
  selfcheck が実際に失敗を返すテストを追加 (no-op 変異が緑にならないこと)
- **F-15 (R1-6)**: M10 負例を product-reported の整合 token event を基点に cached>input だけ壊す形へ
  修正 (単一原因負例化)
- **F-16 (R1-7)**: M17 用に task.json 生成面へ直接到達するテスト (既存 task.json への publish が
  拒否され bytes 不変) を追加
- **F-17 (R1-8)**: M06 負例を writer clock の monkeypatch で決定論化し、fixture 自体の時系列を assert
- **F-18 (R1-9)**: conftest の 3 hook (sessionfinish / collection_finish / xdist node) すべてへ
  parametrized 障害注入し rc/stdout/stderr 不変を固定
- **F-19 (R1-10)**: schema 直接の負例 matrix を追加 — 各 event の source if/then 違反、nested object の
  未知 field (tokens / measurement_source / pilot / task) を jsonschema 経路で拒否することを検査
- **F-20 (R2-14)**: test_check_docs.py の実 repo clean テスト (旧 test_real_repo_clean 相当) を復元する
  (合成 fixture と併置。D66 が親統合で land するまで targeted 赤は許容 — 蒸発が F9/F21 型のため復元が正)
- **F-21 (R2-15)**: xdist controller 結線の live テスト — 小さい合成テスト木で実 pytest subprocess を
  `-n 2 --dist loadgroup` 起動し、sidecar が controller 1 回だけ生成・digest 有・rc/stdout 不変を実測

## docs fix (親担当、段 7)

- **F-13 (R1-4, R2-13)**: recording_duration_s の裁定を改訂 — 実測範囲は「append 前処理 (root/pilot
  読取・既存 stream 検証・git 確認・serialize) で、write/fsync を含まない」。README と schema
  description をこの実態へ揃える (計測境界の変更はしない)
- **F-22 (R1-12)**: README へ欠測率の式表 (RATE_DEFINITIONS と同一) を転記し、report CLI 例を実引数
  付きに修正
- **F-23 (R1-11, R2-14)**: D66 採番・output/README tree (task-runs/ + exploration/)・worklog 次の一手の
  pilot 手順ポインタを親統合 commit で land し、check_docs 緑を回復

## 残余リスク (v1 で受容、README に明記)

- sidecar は同 uid のテストコードから理論上偽装可能 (tool-reported へ格下げ + 開発観測の位置づけで受容)
- validate CLI 単発 (--all 以外) は writer と非直列 (report 経路は F-7 で直列化済み)

## 12. fix 報告 — 逐語

F-1〜F-21 のコード fix を実装しました。docs/output、`tools/check_docs.py`、git staging/commit は変更していません。

### F 項目別

- F-1: [run_tests.py](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/tools/run_tests.py)・[task_run_check.py](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/tools/task_run_check.py) の二回目記録を削除。単発呼出しテストで検証。
- F-2: wrapper は `Exception` のみ捕捉、lock timeout を2秒化。`KeyboardInterrupt` 再送出テストで検証。
- F-3: help/version/setup/collect/fixtures/markers 等を targeted 化。[test_run_tests_task_run.py](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/tests/test_run_tests_task_run.py) の flag matrix で検証。
- F-4: [pytest_stats.py](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/tools/task_runs/pytest_stats.py) で絶対path、repo外、親所有者・0700、固定basenameを検査。sidecar metricsを `tool-reported` 化し負例で検証。
- F-5: [ledger.py](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/tools/task_runs/ledger.py) のgit subprocessから指定 `GIT_*` を除去し、filesystem上の期待toplevelと照合。foreign repo環境注入で検証。
- F-6: root→run→fileを `dir_fd`＋`O_NOFOLLOW` 連鎖へ変更。run directory symlink差替えテストで外部file不変を検証。
- F-7: validate/report cohortを安定順に全events flock後、同一fdから検査。部分append並行publishテストで検証。
- F-8: [schema.py](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/tools/task_runs/schema.py) の `ValidatedRun` に2 digestと`final_seq`を追加。同一fd bytesへの束縛をpath差替えテストで検証。
- F-9: [aggregate.py](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/tools/task_runs/aggregate.py) の診断理由を閉じたcode化し、unsafe entryをdigest化。秘密文字列がreportに残らない負例で検証。
- F-10: duration上限を10,000,000秒とし、全sum/ratioにfinite検査を追加。上限超過・overflow ratio負例で検証。
- F-11: `task_run_report.py --final`、create-only `pilot-final.json`、start凍結を実装。API/CLI双方でmarker生成とstart拒否を検証。
- F-12: `RootReport`にpublished count・cap状態を追加し、通常/diagnostic共通report headerへ常時表示。11-run fixtureで検証。
- F-13: docsは未編集。[schema_v1.json](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/tools/task_runs/schema_v1.json) のdescriptionだけを実測境界へ整合しschema検査。
- F-14: O_EXCL/flock/O_APPEND/fsyncの4種failure注入で`selfcheck()`が失敗するpositive controlを追加。
- F-15: cached>input負例を整合した`product-reported` event基点へ修正し、単一原因をassert。
- F-16: task publish helperへ直接到達し、既存`task.json`拒否とbytes不変を検証。
- F-17: writer clockを固定時系列へmonkeypatchし、逆行fixture自身の時系列をassert。
- F-18: [conftest.py](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/tests/conftest.py) の3 hookをparametrized障害注入し、戻り値/stdout/stderr不変を検証。
- F-19: 全event/sourceのJSON Schema直接matrixと、tokens/source/pilot/task未知field負例を追加。
- F-20: [test_check_docs.py](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/tests/test_check_docs.py) に`test_real_repo_clean`を復元。xfail化せずD66赤を維持。
- F-21: 実pytestを`-n 2 --dist loadgroup`で起動し、controller sidecar一件、counts、digest、rc/stdout/stderrを検証。

### 検証結果

- 指定targeted: **146 passed**
- `test_check_docs.py`: **6 passed / 1 failed**
  - 唯一の失敗は想定どおり、`output/task-runs/README.md:5` の不在D66参照
- 無引数全走: **2243 passed / 21 skipped / 2 failed**
  - 想定のD66失敗
  - 既存real-repoテスト1件がsandbox外のsubmodule `index.lock`を作れず環境失敗
- `check_codex_agents.py`: 緑
- `git diff --check`、Python compile、schema JSON parse: 緑

全走のreal-repo失敗が残したsubmodule差分は、確認したテスト由来の追加だけを逆適用し、`external/ccbench` cleanを復元済みです。