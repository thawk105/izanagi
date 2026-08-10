# [T-740] 段 2 実装プラン

## 変更対象

| 対象 | 指示 |
|---|---|
| `tools/dev_wave_wait.py:1-500`（新規） | `producer` / `acceptance` の 2 サブコマンドを持つ唯一の待ち手正本として実装する。 |
| `orchestrator/tests/test_dev_wave_wait.py:1-520`（新規） | 正規の依存注入 seam を使い、producer、claim 判定、merge、release の不変条件を固定する。 |
| [`docs/pegasus-runbook.md:757`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t740-canonical-waiter/docs/pegasus-runbook.md:757) | 親が §7.3 に使用例と正本参照を書く。実装子は編集しない。 |
| [`tools/wave_land_window.py:1`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t740-canonical-waiter/tools/wave_land_window.py:1) | 改変しない。新 script から CLI subprocess として呼ぶ。 |

`tools/README.md`、`docs/dev-wave/**`、phase doc は対象外とする。

## 既存 lease API の前提

[`tools/wave_land_window.py:641`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t740-canonical-waiter/tools/wave_land_window.py:641) と [`tools/wave_land_window.py:869`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t740-canonical-waiter/tools/wave_land_window.py:869) の現行契約をそのまま利用する。

| サブコマンド | 現行出力・rc | 新待ち手の扱い |
|---|---|---|
| `claim` | stdout は JSON。`acquired` / `held` / `queued` / `stale-held` / `unavailable` のいずれも通常は rc=0。CLI・内部拒否は rc=2。 | rc を先に単独判定し、rc=0 のときだけ JSON を parse。トップレベル `state == "acquired"` の exact 比較だけを受理する。 |
| `release` | stdout は JSON。`released` / `free` / `not-owner` / `unavailable` も通常は rc=0。 | rc と JSON state を別々に判定する。`released` / `free` / `not-owner` は「現在保持していない」と確認できた終端、`unavailable`・未知 state・不正 JSON は cleanup failure。 |
| `status` | 既定は key=value、`--json` 時だけ JSON。 | 使用しない。claim の代替にも待ち条件にも使わない。 |
| `message` | 成功時は固定通知文、land JSON 拒否は rc=3。 | 本 script の scope 外。既存 land 通知手順に残す。 |

JSON parser は duplicate key を拒否し、JSON object とトップレベル `state` の文字列型を確認する。追加 field は許容するが、`holder_self` や `source` を追加 gate にして現行受理集合を厳しくしない。

## CLI 契約

### `producer`

```text
python3 tools/dev_wave_wait.py producer \
  --done-file PATH \
  --artifact-file PATH \
  (--pid PID | --pid-file PATH)
```

| argument | 必須性・既定値 | 契約 |
|---|---|---|
| `--done-file PATH` | 必須 | producer が残す `.done` regular file。内容は解釈しない。 |
| `--artifact-file PATH` | 必須 | 成果物 regular file。空ファイルも「実在」として扱う。 |
| `--pid PID` | `--pid-file` と排他的に片方必須 | 正の十進 PID。 |
| `--pid-file PATH` | `--pid` と排他的に片方必須 | ASCII の正の十進 PID 1 個だけを読む。不存在・不正値は待たず fail-closed。 |
| poll 間隔 | CLI 面なし、固定 5 秒 | 不要な調整面を増やさない。テストでは sleeper を注入する。 |

`pattern`、`match`、`pgrep` 等を受け取る argument・位置引数を一切作らない。

### `acceptance`

```text
python3 tools/dev_wave_wait.py acceptance \
  --wave WAVE \
  [--lease-dir PATH] \
  [--merge-message-file PATH] \
  [--poll-seconds SECONDS] \
  -- COMMAND [ARG ...]
```

| argument | 必須性・既定値 | 契約 |
|---|---|---|
| `--wave WAVE` | 必須 | `claim` と `release` に同じ値を渡す。 |
| `--lease-dir PATH` | 任意 | 省略時は `IZANAGI_WAVE_LEASE_DIR`。両方無ければ claim 前に rc=2。 |
| `--merge-message-file PATH` | 任意、既定 `None` | behind=0 なら不要。behind>0 なのに未指定・不存在・非 file なら merge/受入を実行せず release。指定済みなら待機前と merge 直前の両方で再確認する。 |
| `--poll-seconds SECONDS` | 任意、既定 30 | 現行 runbook に合わせ 30〜120 の整数だけを受理する。 |
| `-- COMMAND...` | delimiter と非空 command が必須 | shell を介さず、その argv をそのまま 1 回だけ実行する。 |

CLI には `--repo`、lease TTL、受入 command の組立機能を作らない。repository は起動時 cwd とし、lease helper は同じ checkout の `tools/wave_land_window.py` を解決する。

### exit code

| rc | 意味 |
|---:|---|
| 0 | producer の三点照合完了、または受入 command rc=0 かつ cleanup 確認済み。 |
| 2 | CLI usage、PID/環境変数等の起動前入力不正。 |
| 70 | liveness 不明、必須 file 欠落、claim JSON/state、Git、subprocess 起動等の fail-closed。 |
| 74 | `git merge --abort` または `release` の完了を確認できない。主処理の rc より優先する。 |
| 130 | `KeyboardInterrupt`。cleanup が確認できた場合。 |
| その他の非 0 | 受入 command の rc をそのまま返す。signal 終了は `128 + signal` に正規化する。cleanup failure 時は rc=74 を優先する。 |

すべての失敗は stage と元 rc を stderr に 1 行で出し、traceback は出さない。受入 command の stdout/stderr は継承し、claim/release/Git の機械出力は個別に capture する。

## `tools/dev_wave_wait.py` の構成

新規ファイルなので、以下を初版の配置・レビュー anchor とする。

| 予定行 | 関数・型 | 責務と不変条件 |
|---|---|---|
| `1-45` | 定数、`_CommandResult`、`_Outcome`、`_PidState` | rc、poll 範囲、SHA regex、既知 lease state を一か所へ固定する。 |
| `46-105` | `_Effects`、default effects | `run(argv, cwd, capture)`、`sleep`、`kill(pid, 0)`、`is_file`、`read_text`、`getenv` を注入可能にする。default subprocess は `shell=False`、`check=False`。 |
| `106-170` | `_parse_cli()`、`_split_command()`、`_parse_pid()` | `acceptance` の `--` を必須化し、producer の argument surface を exact allowlist にする。 |
| `171-225` | `_pid_state()`、`_resolve_pid()`、`wait_for_producer()` | producer の生死を PID の `os.kill(pid, 0)` 相当だけで判定する。pattern 経路を持たない。 |
| `226-285` | `_run_capture()`、`_parse_json_object()`、`_main_sha()`、`_behind_count()` | 各 subprocess の rc を値の parse より先に個別判定する。pipeline、`|| true`、shell 複合条件を作らない。 |
| `286-335` | `_claim_once()`、`_wait_until_acquired()` | claim stdout 全体を JSON parse し、トップレベル state の exact 比較だけで遷移する。 |
| `336-415` | `_merge_main_if_needed()`、`_abort_pending_merge()` | main 取り直し、behind、merge、dry-run、commit、再検査を順番どおり実行する。 |
| `416-475` | `_release_once()`、`run_acceptance()` | 外側の `try/except/finally` で異常・中断・受入赤を含む全同期終端を release へ集約する。merge cleanup は release より先。 |
| `476-500` | `main()` | CLI request を core 関数へ渡し、outcome を exit code と診断へ変換する。 |

テストは `_Effects` に fake を渡す。`subprocess.run`、`time.sleep`、file API を直接 monkeypatch しない。

## `producer` の状態機械

1. PID source を一度だけ解決する。missing、複数指定、不正文字、0 以下、file 読取失敗は rc=2。
2. `_pid_state(pid)` は次の三値を返す。

   - `ALIVE`: `kill(pid, 0)` 成功。必ず sleep して再試行し、`.done` と artifact が既にあっても返らない。
   - `DEAD`: `ESRCH`。この時点で filesystem を取り直す。
   - `UNKNOWN`: `EPERM` その他の OSError。死とみなさず rc=70。

3. `DEAD` 後に `.done` と artifact の両方が regular file なら rc=0。
4. 片方でも無ければ、producer はもう生成できないため待ち続けず rc=70。
5. `.done` 内容、artifact size/hash、producer の成否は新たな第四条件にしない。

これにより `.done` と artifact が先に揃っても PID が生きている間は完了せず、PID 死後に artifact が無い場合も偽の完了にならない。

## `acceptance` の状態機械

### claim loop

各 claim の直前に毎回 `git rev-parse main` を実行し、その回で得た 40 桁 lowercase SHA を `--main-sha` に渡す。

| claim 結果 | 遷移 |
|---|---|
| rc 非 0 | 受入を投入せず fail-closed → `release` |
| stdout が不正 JSON、duplicate key、object 以外、state 非文字列・未知値 | fail-closed → `release` |
| `state == "acquired"` | lease 取得済み状態へ進む |
| `state == "held"` | 受入なし。poll sleep 後、main を再取得して claim を再実行 |
| `state == "queued"` | 同上。claim 再実行が待ち札の mtime を更新する |
| `state == "stale-held"` | retry せず fail-closed → `release` |
| `state == "unavailable"` | retry せず fail-closed → `release` |

`held` / `queued` の 30〜120 秒 poll は待ち札 TTL 300 秒未満なので、正常待機中は札を更新し続ける。`state` 以外の field、stderr、JSON 内診断に `"acquired"` があっても判定材料にしない。

### `acquired` 後

[`docs/pegasus-runbook.md:788`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t740-canonical-waiter/docs/pegasus-runbook.md:788) と同じ順序に固定する。

1. `git rev-parse main`

   - claim 時の SHA を使い回さない。
   - rc=0 と exact SHA の両方を個別確認する。

2. `git rev-list --count HEAD..main`

   - rc=0 の後に非負整数を parse。
   - 0 なら merge しない。
   - 1 以上なら message file を再確認して次へ進む。

3. behind の場合だけ以下を順番に実行する。

   1. `git merge --no-ff --no-commit main`
   2. `git commit --dry-run -F <message-file>`
   3. `git commit -F <message-file>`

   各 rc を個別に確認する。`--ff-only`、`--no-edit`、rebase、reset、自動 message は使わない。

4. merge の有無にかかわらず、`git rev-list --count HEAD..main` を再実行する。

   - rc=0 かつ parsed count=0 のときだけ受入 command へ進む。
   - main が再度進んで count>0 になった場合は二度目の merge を試さず、受入なしで release する。

5. `--` 後の受入 command を shell なしで 1 回実行する。

受入投入の受理集合は次の積に限定する。

```text
claim rc=0
AND parsed top-level state == "acquired"
AND acquired 後の全 Git stage rc=0
AND 最終 HEAD..main count == 0
AND behind 時の明示 message file による merge commit 成功
```

### abort と release

- `git merge` を呼び始めてから `git commit` 成功までを `merge_pending` として追跡する。
- その区間の rc 非 0、例外、`KeyboardInterrupt` では `git merge --abort` を先に実行する。
- abort の rc が非 0 でも `release` は必ず続行する。最終 rc は cleanup failure の 74。
- commit 成功後の再検査失敗や受入赤では、作成済み commit を巻き戻さず release だけを行う。
- `release` は正常、受入赤、claim 異常、待機中断を含め 1 回だけ呼ぶ。
- release JSON の `released` / `free` / `not-owner` は cleanup 済み、`unavailable`・不正出力・非 0 rc は rc=74。
- SIGKILL、ホスト停止等の unwind 不可能な死は既存 lease TTL に委ね、新たな fencing や daemon は作らない。

lease TTL 2400 秒の更新機構は追加しない。1 invocation は受入 command 1 本だけとし、二走目は別 invocation で新たに claim する。

## テスト計画

`orchestrator/tests/test_dev_wave_wait.py:1-85` では、既存 peer test の import 形（[`test_wave_land_window.py:16`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t740-canonical-waiter/orchestrator/tests/test_wave_land_window.py:16)）に合わせて script をロードする。`_FakeEffects` に subprocess 結果、PID state、file state、sleep 時例外を登録し、呼出順を記録する。`tmp_path`、`capsys`、`pytest.mark.parametrize` は使うが、core side effect の monkeypatch は使わない。

- `orchestrator/tests/test_dev_wave_wait.py::test_pid_probe_calls_kill_zero_for_exact_pid` — exact PID と signal 0 の組だけを使い、pgrep/pattern 変異を殺す。
- `...::test_producer_waits_while_pid_alive_then_completes_after_death` — file が揃っていても PID 生存中は返らず、死後だけ rc=0。
- `...::test_producer_dead_without_required_file_fails_closed[done]` — `.done` 欠落を完了にしない。
- `...::test_producer_dead_without_required_file_fails_closed[artifact]` — 必須条件 (d) を固定する。
- `...::test_producer_accepts_exactly_one_pid_source[direct]` — `--pid` 正例。
- `...::test_producer_accepts_exactly_one_pid_source[pid-file]` — 注入した file read による `--pid-file` 正例。
- `...::test_producer_rejects_invalid_pid_source[neither]` — PID 未指定を拒否。
- `...::test_producer_rejects_invalid_pid_source[both]` — PID source 二重指定を拒否。
- `...::test_producer_cli_surface_has_no_pattern_input` — producer parser の option/dest を exact allowlist と比較し、pattern 入力面の不存在を固定する。
- `...::test_acceptance_non_acquired_state_never_runs_command[held]` — held では投入せず、再 claim へ進む。
- `...::test_acceptance_non_acquired_state_never_runs_command[queued]` — queued では投入せず、再 claim へ進む。
- `...::test_acceptance_non_acquired_state_never_runs_command[stale-held]` — stale-held は terminal fail。
- `...::test_acceptance_non_acquired_state_never_runs_command[unavailable]` — unavailable は terminal fail。
- `...::test_acceptance_ignores_acquired_outside_top_level_state` —別 field・nested field・stderr の `"acquired"` で投入しない。
- `...::test_acceptance_rejects_claim_json[malformed]` — JSON parse 不能を fail-closed。
- `...::test_acceptance_rejects_claim_json[duplicate-state]` —曖昧な duplicate state を拒否。
- `...::test_acceptance_rejects_claim_json[unknown-state]` —未知 state を拒否。
- `...::test_acceptance_rejects_claim_json[non-string-state]` —型偽装を拒否。
- `...::test_held_and_queued_refresh_main_before_every_claim` —各 poll で新しい main SHA を claim に渡し、sleep 間隔と待ち札更新を固定する。
- `...::test_acquired_reloads_main_before_behind_check` — claim 用 SHA の使い回しを殺す。
- `...::test_merge_required_without_message_file_releases_before_submission` —必須条件 (e)。
- `...::test_merge_sequence_and_postcheck_are_exact` — merge、dry-run、commit、再検査、command、release の順序と `--ff-only` / `--no-edit` 不在を固定する。
- `...::test_nonzero_stage_blocks_submission_and_releases[preclaim-rev-parse]`
- `...::test_nonzero_stage_blocks_submission_and_releases[claim]`
- `...::test_nonzero_stage_blocks_submission_and_releases[postclaim-rev-parse]`
- `...::test_nonzero_stage_blocks_submission_and_releases[behind-count]`
- `...::test_nonzero_stage_blocks_submission_and_releases[merge]`
- `...::test_nonzero_stage_blocks_submission_and_releases[commit-dry-run]`
- `...::test_nonzero_stage_blocks_submission_and_releases[commit]`
- `...::test_nonzero_stage_blocks_submission_and_releases[postcheck]` —各段の rc を独立に見て後段へ進めないことを固定する。
- `...::test_merge_failure_aborts_before_release` — `merge --abort` → `release` の順序を固定する。
- `...::test_acceptance_command_red_is_propagated_after_release` —受入赤でも release し、cleanup 成功時は child rc を保存する。
- `...::test_abnormal_path_always_releases[subprocess-error]` —例外経路の release。
- `...::test_abnormal_path_always_releases[keyboard-interrupt]` —中断経路の release、必須条件 (f)。
- `...::test_release_failure_overrides_primary_result` — lease cleanup 不明を成功・child rc で隠さない。
- `...::test_acceptance_cli_contract[missing-delimiter]`
- `...::test_acceptance_cli_contract[empty-command]`
- `...::test_acceptance_cli_contract[poll-29]`
- `...::test_acceptance_cli_contract[poll-121]`
- `...::test_acceptance_cli_contract[default-30]` — delimiter、command 非空、現行 poll 範囲・既定値を固定する。

## 親が §7.3 に書く内容

[`docs/pegasus-runbook.md:757-830`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t740-canonical-waiter/docs/pegasus-runbook.md:757) を次のように更新する。

1. §7.3 冒頭で、lease primitive は `tools/wave_land_window.py`、待ち手の正本は `tools/dev_wave_wait.py acceptance` と明記する。
2. 現行の手書き claim loop 例を、次の canonical invocation へ置換する。

   ```text
   python3 tools/dev_wave_wait.py acceptance \
     --wave "$W" \
     --merge-message-file "$MESSAGE_FILE" \
     -- python3 tools/run_tests.py --force-dispatch -q -rf
   ```

3. `--merge-message-file` は behind が判明した場合に必須だが、head-of-line blocking を避けるため通常運用では待機開始前に常に準備・指定する、と書く。
4. exact JSON state、個別 rc、main 再取得、merge/recheck、必ず release は script が担うとし、別 shell loop を書き直さないよう明記する。
5. background producer の例として `producer --done-file ... --artifact-file ... --pid-file ...` を載せ、pattern/pgrep を渡す例を置かない。
6. FIFO、待ち札 300 秒、lease 2400 秒、残余 race、queue degraded、message/land の説明は現行 [`docs/pegasus-runbook.md:780`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t740-canonical-waiter/docs/pegasus-runbook.md:780) 以降から削らない。
7. `tools/run_tests.py` の command は caller が `--` 後へ渡すものとし、待ち手側で `--force-dispatch` や対象 nodeid を合成しない。

## 検証手順

実装後、親が direct pytest ではなく次を実行する。

```text
python3 -m orchestrator.campaign.queue_state
python3 tools/run_tests.py --force-dispatch orchestrator/tests/test_dev_wave_wait.py -q -rf
python3 tools/run_tests.py --force-dispatch orchestrator/tests/test_wave_land_window.py -q -rf
python3 tools/run_tests.py --force-dispatch -q -rf
python3 tools/check_codex_agents.py
python3 tools/check_docs.py
```

queue 停止時は runbook §7 の規則に従い、`--force-dispatch` を外した bounded local 実行が admission される場合だけ実行する。commit 後は `python3 tools/check_ai_provenance.py` を実行する。

本段では read-only のため、これらは実走せず緑を主張しない。

## 所見

- 親 brief [`brief.md:79`](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t740-canonical-waiter/brief.md:79) の provisional P5 は 10 秒 poll を許す一方、現行 runbook [`docs/pegasus-runbook.md:780`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t740-canonical-waiter/docs/pegasus-runbook.md:780) は 30〜120 秒を正本としている。本プランは現行正本の 30〜120 秒を採る。10 秒を採用するなら、実装前に親が差分を裁定し runbook と同時変更する必要がある。
- 参考 `wait.sh:12-15` は PID による `kill -0` の正例だが、[`wait.sh:18`](/work/1/SFC/tanab/dev-wave-jobs/t139-addendum-b/wait.sh:18) 以降は artifact 欠落を表示するだけで exit 0 になる。PID 判定だけを踏襲し、artifact 欠落時の成功 semantics はコピーしない。
- `release` は `unavailable` でも rc=0 を返すため、rc だけでは cleanup を確認できない。新 script 側で release JSON state も判定する必要がある。
- `tools/wave_land_window.py` の改変は不要。必要な state、FIFO heartbeat、release ticket cleanup は既に提供されている。
- 最終再検査から受入 command 起動までに main が進む残余 raceと、2400 秒 TTL 超過後の fencing 不在は現行 §7.3 の既知限界として残す。

## 実装しないもの

- pattern、pgrep、process-name fallback。
- `status` を使う polling。
- lease helper の改変、lease heartbeat、fencing token、常駐 daemon。
- `.done` 内容の schema 化、artifact の非空・hash・内容検査。
- command が `tools/run_tests.py` または `--force-dispatch` を含むかの強制。
- 自動 merge message、`--no-edit`、`--ff-only`、rebase、reset、autostash。
- PID reuse 対策としての `/proc` start-time fingerprint。
- `tools/README.md`、`docs/dev-wave/**` への追記。

## 総括

- `tools/dev_wave_wait.py` に PID 三点照合の `producer` と、exact JSON claim・main merge・再検査・必ず release の `acceptance` を実装する。
- テストは side effect を `_Effects` へ注入し、pattern 面の不存在、部分一致拒否、全 rc、abort/release 順序を nodeid 単位で固定する。
- 現行 `tools/wave_land_window.py` は変更不要で、親は runbook §7.3 を canonical waiter の呼出しへ一本化する。
- 残る裁定点は brief の 10 秒 poll と現行 runbook の 30〜120 秒の不一致。本プランは現行散文正本を優先する。
- read-only のためテストは未実走であり、実測結果・緑は主張しない。