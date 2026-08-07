## 候補比較

先に重要な訂正がある。現行 task-run の `tokens` は task 単位の空欄ではなく、`agent_run` 専用 field である。

- JSON Schema は `tokens` を4区分で定義するが（`tools/task_runs/schema_v1.json:99-108`）、`tokens` が存在できるのは `event=agent_run` のみ（同 `:161-173`）。その場合は product/model/reasoning/role/status/duration まで必須になる（同 `:210-214`）。
- Python validator も同じ閉集合である（`tools/task_runs/schema.py:314-332,425-435`）。
- 値を埋める契約者は writer ではなく CLI caller（`tools/task_runs/cli.py:76-87,138-155`）。writer が決めるのは seq/timestamp/event_id/source（`tools/task_runs/ledger.py:715-830`）。
- 実データにも `agent_run` は1件あり、4 token は null である（`output/task-runs/20260720-ruling-ac-wal-terminal-43708d1e/events.jsonl:2`）。最終 report の `0/1` はこの1件であり（`...task-efficiency.md:102-111`）、他 run の `0/0` は「空欄」ではなく agent event 自体が無いことを表す（同 `:113-126`）。
- 集計は agent event だけを数え（`tools/task_runs/aggregate.py:288-294`）、`task_kind/product/model` cohort に入れる（同 `:382-410`）。Claude の worktree/window 合算をここへ押し込むと agent 数・model cohort を偽る。

以下の行数は実装差分の概算である。

| 候補 | 実在する seam | 必要な変更・新規ファイル | 既存受理集合 | 判定 |
|---|---|---|---|---|
| (a) 定期観測 | `tools/claude_session_ledger.py:905-1029` の CLI だけ。repo 内に定期 caller は無い | 現行関数への数行追加では不可。新規 snapshot writer 約80–120行と、repo 外を含む scheduler 定義が必要 | task-run は不変だが、新しい snapshot schema・保存場所・周期の受理集合が生じる | **不在** |
| (b) wave 記録へ添付 | `docs/dev-wave/core.md:84-97` は prose/spool 手順で、typed writer 関数ではない | 新規 attachment writer 約80–100行と stage 7 呼出しが必要。`docs/dev-wave/*` へ契約追加できる余地もない | 自由書式なら受理集合自体が無く、typed 化すれば新しい artifact schema が必要 | **不在** |
| (c) A/B endpoint | Codex 専用 seam は実在。`tools/codex_reasoning_ab.py:27-40` が ledger を in-process importし、`:2722-2728,2854-2860,2952-2963` で canonical parser を使う | 同 `collect_run()` へ10–20行足すだけでは Claude の paired arm が存在せず意味不成立。正しく作るなら新規 harness/receipt/schema が必要 | 既存 Codex A/B receipt の受理集合を変えるか、別 endpoint の受理集合を新設する | **Codex seam のみ実在、Claude seam は不在** |
| (d) task-run | namespace・append writer・report は実在。自然な発火点は `finish_run()`（`tools/task_runs/ledger.py:885-888`） | 正しい形なら task-level event、collector adapter、schema/report を追加。概算: 新規 adapter 100–130行、writer 35–50行、validator 80–120行、report 50–70行 | 現行 `agent_run` へ直書きなら構文上は不変だが意味が破綻。task-level event なら受理集合が変わる | **受け皿は実在、P1 が想定した field seam は不在** |

`tools/run_tests.py:813-841,1462-1511` は唯一の自動記録先例で、専用 wrapper が失敗を握りつぶし child の結果を変えない。Claude 集計をここへ結線すると、同じ project/window をテスト回数だけ重複記録するので採らない。

## 推奨

候補は **(d)** を採る。ただし、親 P1 の「既存 `agent_run.tokens` を producer が埋める」という実装には同意しない。推奨するのは、次世代 task-run に task-level の `claude_session_usage` event を設ける **(d-v2)** である。

本 wave は実装へ進まず、現時点では「結線先の決定＋ユーザー裁定パッケージ」までとする。理由は次の3点である。

1. 現行 `agent_run` へ入れるには、aggregate に存在しない model/reasoning/role/duration を作る必要があり、report の agent cohort を汚す。
2. 現行 Claude report は schema version 2 の project/window 集計であり（`tools/claude_session_ledger.py:836-893`）、D206 が要求する population を格納する場所が task-run/v1 に無い。
3. 凍結済み pilot の次 root 名と、凍結済み v1 の受理集合を拡張するか v2 にするかが未裁定である。

consumer は観測のみとする。`claude_session_usage` の欠測は report に出すが、`validate_run()` の完了条件にはしない。収集失敗後も `task_end` を記録し、`tools/dev_waves/checker.py:668-676` の既存 task-run 完了 gate に usage 完備条件を追加しない。

## 最小実装プラン

以下は「新しい task-run/v2 世代」を裁定した場合の実装案である。

### import と canonical parser

- `tools/codex_reasoning_ab.py:27-40` と同じく、consumer 側から module を in-process importする。
- 新規 `tools/task_runs/claude_usage.py` に約14行の bytecode 抑止付き import shim を置き、`claude_session_ledger.py` の公開 collector を呼ぶ。
- CLI subprocess と stdout の `json.loads` は使わない。また transcript JSONL を task-run 側で再解釈しない。したがって D206 の「第3の parser」は生じない。
- `tools/claude_session_ledger.py:905-1029` の収集本体を `collect_report(...)` へ抽出し、`main()` は parse・render・exit code のみにする。純移動が中心で、追加は約20–30行。既存 JSON schema version 2 は維持する。

### 帰属 key

記録対象は次の組とする。

```text
(resolved worktree → Claude project slug,
 resolved worktree cwd filter,
 [task.json.started_at, collection_started_at))
```

- worktree は `tools/task_runs/ledger.py:296-304` の filesystem repo-root 解決を公開 helper 化して得る。
- 現行 ledger は literal slug を受け取るだけで（`tools/claude_session_ledger.py:186-215`）、repo 内に path→slug resolver は無い。
- インストール済み Claude 2.1.223 には、resolved path の英数字以外を `-` にし、200文字超は先頭200文字＋32-bit hash の base36 suffix とする private rule が存在し、現 worktree から既存 project directory への一致も得られた。ただしこれは line-addressable な repo 契約ではない。
- `tools/claude_session_ledger.py:92-105` 付近へ約25–35行で `project_slug_for_cwd()` を追加する。長い非ASCII path も JavaScript `charCodeAt` 相当の UTF-16 code unit／signed 32-bit 演算で合わせる。
- 計算した project directory が存在しない場合は全 root 走査へ fallback しない。収集を欠測として fail-open にする。これで M7/M11 型の誤帰属を避ける。
- slug だけでは task-run ID は transcript に束縛されない。`start_run()` は cap/date/damage を検査するだけで、同一 worktree の open run 重複を拒否しない（`tools/task_runs/ledger.py:527-596`）。adapter は同 root の task 時間窓重複を検査し、曖昧なら記録しない。作業自体は止めない。
- `--project=<derived slug>` と resolved cwd の補助 filter を併用する。`--cwd-contains` 単独は使用しない。
- `--include-sidechains` 相当を有効にし、`tools/claude_session_ledger.py:770-771,1012-1013` の disjoint な `combined` を task 観測値とする。

### token と source

既存4区分への写像は次で固定する。

| task-run field | Claude ledger schema v2 |
|---|---|
| `input_tokens` | `combined.raw_input_tokens` |
| `cached_tokens` | `combined.cache_read_input_tokens + combined.cache_creation_input_tokens` |
| `output_tokens` | `combined.output_tokens` |
| `total_tokens` | `combined.raw_input_tokens + combined.output_tokens` |

根拠は `raw_input_tokens` の定義（`tools/claude_session_ledger.py:731-762`）と既存回帰（`orchestrator/tests/test_claude_session_ledger.py:147-205`）。これなら `cached≤input` と `total=input+output`（`tools/task_runs/schema.py:374-393`）を満たす。cache read/create の内訳は新 event 内にも残し、4区分への圧縮だけで失わない。

source は既存名だけで構成する。

```json
{
  "timestamp": "system-clock",
  "duration": "not-applicable",
  "metrics": "tool-reported",
  "tokens": "product-reported"
}
```

- 現行 source 名の受理集合は `tools/task_runs/schema_v1.json:88-97`、event 別組合せは `tools/task_runs/schema.py:335-371`。
- この consumer は Claude 実行を包んで時間を測っていないため、`monotonic-clock` や `wrapper-observed` は名乗らない。
- `not-exposed` は現行では全 token が null の agent event、`not-applicable` は token 次元を持たない event に使われる。収集失敗を `not-exposed` やゼロへ読み替えず、usage event 自体を欠測にする。
- 専用 writer だけが上記 source を付ける。汎用 `append_event()` から `claude_session_usage` を書く経路は拒否する。

### event と writer

- **新規** `tools/task_runs/schema_v2.json`（約330–370行）  
  v1 を基に `claude_session_usage` を追加する。payload は token 4区分、cache 内訳、model/tool call の別 field、time window、走査件数、unreadable、limit、root/sidechain 配分、project/cwd binding を含む。
- `tools/task_runs/schema.py:18-54,314-371,396-473,520-582`（約80–120行変更）  
  v1 read compatibility と v2 writer を分離する。usage は run 当たり高々1件、`task_end` 前だけを許すが、0件も valid とする。
- **新規** `tools/task_runs/claude_usage.py`（約100–130行）  
  worktree/slug/window の解決、strict collector 呼出し、`limit_reached`・strict issue・重複窓の拒否、token 写像を所有する。
- `tools/task_runs/ledger.py:633-666`（約8–12行）  
  専用 event の source triple を writer-owned で追加する。
- `tools/task_runs/ledger.py:715-830`（約15–25行）  
  専用 API だけから append できるようにし、再試行時は既存 usage event を再利用する。
- `tools/task_runs/ledger.py:885-888`（約15–20行）  
  v2 run の `finish_run()` で usage を best-effort 記録してから `task_end` を追記する。通常例外は usage 欠測へ落とすが、`task_end` 自体の失敗は従来どおり返す。
- `tools/task_runs/aggregate.py:275-410`（約50–70行）  
  task-level usage を独立集計し、`_agent_events` と product/model cohort へ混ぜない。finished v2 run を分母に欠測率を出す。
- `tools/task_runs/__init__.py:3-35`（2–4行）  
  専用 writer API を公開する。
- `tools/task_runs/cli.py:121-123,197-216`  
  `finish` を発火 seam とする。新しい raw JSON 引数は足さない。
- `tools/task_run.py:8-16` と `tools/task_run_report.py:8-16`  
  いずれも薄い entry point なので変更不要。
- `tools/run_tests.py`  
  変更不要。ここへ Claude 集計を足さない。

### population と privacy

D206 の population を捨てて token だけ保存する案は不可である。一方、現行 task-run は raw selector/node 名を禁止する（`output/task-runs/README.md:60-63`）。

推奨 payload は raw root/slug/cwd を保存せず、次を保存する。

- `projects_root_kind=claude-default`
- `selection_rule=resolved-worktree-slug-v1`
- project/cwd の SHA-256 binding
- 正確な時間窓と判定 basis
- file/byte/unreadable/malformed/limit 件数
- root/sidechain 配分
- canonical ledger schema version

この redacted population が D206 の「黙って決めない」を満たすかはユーザー裁定事項とする。literal selector が必須という裁定なら、現行 privacy 契約との両立案が無いため (d) は不成立になる。

### pilot と root

- 現行 root は `pilot-final.json` が存在し、`start_run()` が `tools/task_runs/ledger.py:542-548` で拒否する。日数上限も同 `:553-557` で拒否される。
- final marker の生成は `tools/task_runs/aggregate.py:750-779,781-866`。既存回帰は `orchestrator/tests/test_task_run_aggregate.py:395-407`。
- 一方、root 名が決まれば、現行 CLI の `--root` と `init-pilot`（`tools/task_runs/cli.py:40-50`、`tools/task_runs/ledger.py:359-374`）だけで別の **v1 root** は作れる。したがって「どの新 root もコード変更なしには開始不能」ではない。
- ただし task-level event を持つ v2 root はコード変更前には書けない。
- 新世代を現 root の子 directory に置くと `_root_candidates()` が unknown entry とする（`tools/task_runs/ledger.py:394-431`）。別 sibling root か、旧 root の移設が必要である。
- sibling root を採る場合は、`tools/task_runs/cli.py:25-26`、`tools/run_tests.py:854-856,965-967,1478-1480`、`tools/task_run_check.py:28-34`、`tools/dev_waves/daemon.py:1117-1128` の既定 path を同時に切り替える。usage 欠測を gate にしないため `tools/dev_waves/checker.py:668-676` の完了条件は変えない。

### 発見可能性

- `docs/README.md:65-67` の `codex_worker_ledger.py` の隣へ、`claude_session_ledger.py` の read-only 台帳説明を1行追加する。
- `docs/dev-wave/*` は変更しない。
- 新 root/schema の運用契約は、root 名の裁定後に対応する `output/task-runs*/README.md` へ置く。

## テスト

予定 nodeid と殺す対象は次のとおり。

- `orchestrator/tests/test_claude_session_ledger.py::test_public_collect_report_matches_cli_json_schema_v2` — CLI subprocess 化や public collector と CLI の意味ずれを殺す。
- `orchestrator/tests/test_claude_session_ledger.py::test_project_slug_for_cwd_matches_short_and_hashed_claude_encoding` — slash 置換、200文字境界、signed hash、非ASCII処理の誤りを殺す。
- `orchestrator/tests/test_task_run_claude_usage.py::test_finish_maps_all_three_input_buckets_and_preserves_population` — cache creation/read の脱落と population 廃棄を殺す。
- `orchestrator/tests/test_task_run_claude_usage.py::test_project_and_cwd_filters_are_combined_and_never_fall_back_to_all_projects` — M7/M11 型の誤 project 帰属を殺す。
- `orchestrator/tests/test_task_run_claude_usage.py::test_overlapping_task_windows_skip_usage_without_blocking_task_end` — 同一 transcript の二重帰属と consumer の gate 化を殺す。
- `orchestrator/tests/test_task_run_claude_usage.py::test_retry_after_usage_append_before_task_end_is_idempotent` — usage 成功後・task_end 前停止による二重計上を殺す。
- `orchestrator/tests/test_task_run_ledger.py::test_claude_usage_source_matrix_rejects_generic_and_wrapper_claims` — caller による source 偽装と新 source 名の混入を殺す。
- `orchestrator/tests/test_task_run_aggregate.py::test_claude_usage_never_enters_agent_or_product_model_cohorts` — agent 数/model cohort 汚染を殺す。
- `orchestrator/tests/test_task_run_aggregate.py::test_missing_claude_usage_is_reported_but_run_remains_valid` — 観測 consumer の完備 gate 化を殺す。

共有 fixture への静的波及:

- `test_claude_session_ledger.py:20-35,112-125` の loader/runner は public collector 比較に再利用する。CLI option を増やさないなら `:1268-1286` は不変。
- `test_task_run_ledger.py:21-35,140-150` の public API pin、`:153-203` の全 event fixture、`:206-230` の source matrix を v2 分だけ拡張する。`_null_agent_payload()` は変えない。
- `test_task_run_aggregate.py:59-91,144-169` の source/event/healthy fixture は v1 回帰として残し、v2 専用 fixture を追加する。既存 operation count の期待値を usage 追加で機械的に書き換えない。
- `orchestrator/tests/conftest.py:108-121` に consumer が読む private Claude 環境値の隔離を追加し、新規テストだけが明示設定する。
- sibling root を採る場合は dev-waves/check-docs/run-tests の path 固定テストにも波及する。

テストは実行していない。以上は read-only の静的検査結果である。

## ユーザー裁定が要る点

1. **schema と世代**

   - A. **新しい `task-run/v2` と sibling rootを作る（推奨）**。凍結 v1 の受理集合を保存する。
   - B. 新 sibling rootで `task-run/v1` に event を加算する。実装は小さいが、凍結済み version の受理集合を変更する。
   - C. 現行 `agent_run` へ aggregate を擬装する。schema 変更は少ないが、agent/model cohort と population 契約が壊れるため非推奨。

2. **root 名と既定 path**

   - A. `output/task-runs-v2/` のような sibling を採り、全既定 caller を切り替える（推奨）。
   - B. 凍結 v1 を別名へ移し、canonical `output/task-runs/` を新世代へ再利用する。
   - C. 新 root は明示 `--root` / env の opt-in のみにし、既定 caller は凍結 root のままにする。production coverage が成立しにくいため非推奨。

3. **帰属保証**

   - A. dedicated worktree＋非重複時間窓を pilot 契約とし、重複時は欠測にする（推奨）。
   - B. private な Claude session ID まで canonical ledger の filter に追加する。より強いが、Claude report schema の更新と private runtime 依存が増える。
   - C. slug/window の重複を許容する。二重帰属を排除できないため非推奨。

4. **population の privacy 表現**

   - A. derivation rule＋digest＋完全な走査/time-window metadata を tracked event に保存する（推奨）。
   - B. raw projects root・slug・cwd selector を保存するため、現行 privacy 契約へ明示例外を設ける。
   - C. population を保存しない。D206 と両立しないため不採用。

## 総括

(d) の開発観測 namespace は適切だが、現行 `agent_run.tokens` への直接結線は成立しない。  
推奨は、新世代 task-run に task-level `claude_session_usage` を追加し、`finish_run()` から fail-open で記録する案である。  
本 wave は root/schema/privacy のユーザー裁定までで止めるべきで、現時点では実装開始条件が揃っていない。  
最も弱い前提は、worktree path→Claude project slug の符号化が現行 Claude の private implementation に依存する点である。