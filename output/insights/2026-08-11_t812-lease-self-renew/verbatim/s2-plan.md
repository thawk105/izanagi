# 段 2 実装プラン

実装面は `tools/` 2 ファイルと対応テスト 2 ファイルに限定する。`held-self` は「今回作った lease」ではないため専用 ownership 値で扱い、失敗時は merge を abort する一方、lease は release しない。

| claim 結果 | mtime | 待ち手 | 失敗時の lease |
|---|---:|---|---|
| `acquired` | 新規作成時刻 | 即進行 | release |
| 外部 holder の `held` / `queued` | 不変 | polling | release しない |
| fresh な自己保持 `held-self` | 現在時刻へ更新 | 即進行 | release しない |
| stale な自己保持 | 既存 stale 回収後 `acquired` | 即進行 | acquired と同じ |
| 自己更新失敗・自己状態不整合 | 更新を信用しない | 即 rc=70 | release しない |

## 1. lease primitive

対象: [tools/wave_land_window.py:236](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t812-lease-self-renew/tools/wave_land_window.py:236)

1. `_result()`（236–252 行）

   - JSON schema は変えない。既存 signature の `unavailable_reason` と、`holder == self_holder` から計算する `holder_self` をそのまま使う。
   - 新しいトップレベル `reason` は作らず、失敗理由は従来どおり `source={"status":"unavailable","reason":"self-renew-failed"}` に置く。

2. `_lease_result()`（382–389 行）

   - signature を次の意味へ拡張する。

     ```python
     _lease_result(
         state, lease, self_holder, *,
         age_seconds: int | None = None,
         unavailable_reason: str | None = None,
     )
     ```

   - `age_seconds is None` なら従来どおり `lease.age_seconds`、指定時だけ override する。
   - `_result()` へは keyword で `age_seconds` と `unavailable_reason` を渡す。
   - これにより更新成功は `age_seconds=0`、更新失敗は元の観測 age と `holder_self=true` を同時に返せる。

3. `claim()` の fresh lease 分岐（641–744 行、特に 719–737 行）

   - `not lease.stale` かつ payload valid の現在位置を維持する。したがって stale 自己保持は `held-self` にせず、既存の unlink → 再作成 → `acquired` 経路へ流す。
   - 723 行の `lease.holder == self_holder` 分岐を次の順序にする。

     1. 自分の待ち札だけを `_drop_ticket_best_effort()` で落とす。他 wave の札には触れない。
     2. `renewed_ns = time.time_ns()` を一度取得する。
     3. ticket heartbeat（509–530、568–573 行）と同じ前例に従い、O_RDONLY の `lease.fd` に対して `os.utime(lease.fd, ns=(renewed_ns, renewed_ns))` を呼ぶ。payload は書き換えず、`fsync` も追加しない。
     4. `os.fstat(lease.fd)` → `_validate_owned_regular()` → `_same_entry(directory_fd, _LEASE_NAME, refreshed_metadata)` を実行する。
     5. 成功なら `_lease_result("held-self", ..., age_seconds=0)`。
     6. `os.utime` / `fstat` / owner・regular 検査の失敗、または更新後 `_same_entry == False` は、retry・`held`・成功扱いにせず `_lease_result("unavailable", ..., unavailable_reason="self-renew-failed")`。

   - `_same_entry` の更新後再確認は必要。flock は同一 inode の協調者しか守らず、名前の unlink/replacement を防がない。更新前の照合は `_open_lease()` 319 行ですでに済んでいる。
   - `_open_lease(..., exclusive=True)` が 661 行で得た `LOCK_EX` は、更新、post-`fstat`、post-`_same_entry`、結果構築まで保持し、737 行の `finally: os.close(lease.fd)` で初めて解放する。
   - foreign holder は現在の `_lease_result("held", ...)` のままとし、mtime を更新しない。

### `age_seconds` と TTL

- `held-self.age_seconds` は「更新後の mtime の経過秒」で、成功応答では厳密に整数 `0` とする。TTL 残秒そのものではない。
- lease payload の `ttl: 2400` と `main_sha` は書き換えない。TTL の authority は更新した mtime と既存の `_POLICY_TTL_SECONDS=2400` であり、stale 境界も現在の「2400 秒超」のまま。
- `self-renew-failed` では元の `lease.age_seconds` を返す。`source.status=unavailable` なので、その age を更新成功の証拠には使わせない。

## 2. canonical waiter

対象: [tools/dev_wave_wait.py:51](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t812-lease-self-renew/tools/dev_wave_wait.py:51)

1. state 集合（51–54 行）

   - `_CLAIM_STATES` に `held-self` を追加し、全語彙を `{acquired, held-self, held, queued, stale-held, unavailable}` とする。
   - 意味を混同しないよう、別定数として以下を置く。

     - accepted: `{acquired, held-self}`
     - polling: `{held, queued}`

   - `stale-held` / `unavailable` は既知 state だが polling 対象にはしない。

2. ownership（91–103 行）

   - P2 を採用し、`_LeaseOwnership.HELD_SELF = "held-self"` を新設する。`NONE` にはしない。
   - 理由: `NONE` へ落とすと `_cleanup_lifecycle()` が merge abort まで省略し、worktree に `MERGE_HEAD` を残しうる。
   - 権限は次のように分ける。

     - `ACQUIRED` / `UNKNOWN`: merge abort と lease release の権限あり。
     - `HELD_SELF`: 今回開始した merge の abort 権限だけあり、lease release 権限なし。
     - `RETAINED`: 成功終端。親の land 終端へ委譲。
     - `NONE`: cleanup 不要。

3. `_claim_once()`（577–604 行）

   - subprocess 開始前の `UNKNOWN` は維持する。
   - state を allowlist で確認した直後、semantic validation より先に ownership を確定する。

     - `acquired` → `ACQUIRED`
     - `held-self` → `HELD_SELF`
     - `unavailable + self-renew-failed` → `HELD_SELF`
     - 従来形式の `held` などで `holder_self is True` → `HELD_SELF`
     - その他の既知非取得 state → `NONE`

   - `held-self` の受理には、少なくとも次の exact shape を要求する。

     - `holder_self is True`
     - `type(age_seconds) is int and age_seconds == 0`
     - `source == {"status": "ok", "reason": None}`

   - 次は polling せず `_StageFailure` にする。

     - `unavailable`、`holder_self=true`、`source.reason=="self-renew-failed"`  
       → stage `claim-self-renew-failed`
     - `held-self` の shape 不整合  
       → stage `claim-self-unverified`
     - 旧実装形の `state="held", holder_self=true`、または `queued` / `stale-held` なのに自己 holder  
       → stage `claim-self-unverified`

   - いずれも既定の `RC_FAIL_CLOSED=70`。未知・壊れた JSON の既存 `claim-json` / `claim-state` と `UNKNOWN` cleanup は変えない。

4. `_wait_until_acquired()`（607–628 行）

   - 621 行を accepted 集合の membership に変更する。
   - `acquired` と `held-self` の双方で `claim_started_at` を保存して直ちに返す。
   - polling は `held` / `queued` だけ。自己状態異常は `_claim_once()` で例外になるため、sleep と `claim-timeout` へ到達しない。
   - 関数名は不要な churn を避けて維持する。

5. cleanup（721–781、784–919 行）

   - `_cleanup_after_claim()` に keyword `release_lease: bool` を追加する。
   - `merge_pending` なら ownership にかかわらず現在の `_abort_pending_merge()` を実行する。
   - `release_lease=True` のときだけ `_release_once()` を呼ぶ。
   - `_cleanup_lifecycle()` は `HELD_SELF` も cleanup 対象に含めるが、`release_lease=False` を渡す。権限は実処理前に従来どおり消費し、再入を no-op にする。
   - `held-self` 失敗時は stderr に一度だけ次を出す。

     ```text
     acceptance: held-self lease retained; this invocation has no release authority
     ```

   - 成功時は既存の 894 行で `RETAINED` へ遷移するため、この診断も release も行わない。
   - 自己更新失敗時の public CLI 出力は、上の保持診断に続けて `_print_outcome()` から次を stderr へ出す。stdout に claim JSON を再掲しない。

     ```text
     error: stage=claim-self-renew-failed rc=70
     ```

   - shape 不整合は同様に `error: stage=claim-self-unverified rc=70`。受入 command、sleep、release は実行しない。

## 3. テスト計画

### `test_wave_land_window.py`

対象: [orchestrator/tests/test_wave_land_window.py:120](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t812-lease-self-renew/orchestrator/tests/test_wave_land_window.py:120)

- 新設 `test_self_claim_renews_mtime_and_returns_held_self`

  - 最初の claim で取得後、lease mtime を十分古い fresh 時刻へ固定し、同じ wave で再 claim。
  - `state=held-self`、`holder_self is True`、`age_seconds == 0`、`source.status=ok`、mtime が `_NOW_NS` へ前進することを確認。
  - payload bytes、holder、元の `main_sha`、`ttl=2400` が不変であることも確認する。

- 新設 `test_foreign_held_claim_does_not_renew_lease`

  - 別 wave の claim は従来どおり `held` / `holder_self=false` で、lease mtime と payload が不変。

- 新設 `test_self_claim_renew_failure_is_structured_unavailable`

  - lease fd の `os.utime` を `OSError` にし、`state=unavailable`、`holder_self=true`、`source.reason=self-renew-failed`、元 mtime 不変を確認。

- 新設 `test_self_claim_rechecks_same_entry_after_renewal`

  - `_open_lease()` 内の最初の `_same_entry` は成功させ、更新後照合だけ失敗させる。
  - `held-self` を返さず `self-renew-failed` になることで post-update 検査の実在を固定する。

- 新設 `test_self_claim_renew_holds_exclusive_flock`

  - `os.utime` callback 中に別 fd から nonblocking `LOCK_EX` を試し、busy になることを確認する。

- 新設 `test_stale_self_claim_reacquires_instead_of_renewing`

  - 2401 秒の自己 lease は `held-self` ではなく既存経路の `acquired`。新 inode、新 `main_sha` を確認する。

- 現行 [test_second_wave_is_held_by_first_holder:140](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t812-lease-self-renew/orchestrator/tests/test_wave_land_window.py:140) と、他 wave の `held` assert は変更しない。
- brief にある「自己 claim が `held` を返す既存 assert」は現 tree には存在しない。`_claim()` を同じ wave で二度呼ぶテストはゼロである。なお [test_status_distinguishes_free_and_held:562](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t812-lease-self-renew/orchestrator/tests/test_wave_land_window.py:562) は自己 `status` の assert であり、`status` は引き続き `held` のため書き換えない。

### `test_dev_wave_wait.py`

対象: [orchestrator/tests/test_dev_wave_wait.py:186](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t812-lease-self-renew/orchestrator/tests/test_dev_wave_wait.py:186)

- 191–193 行付近へ、canonical な `held-self` JSON を投入する test helper を追加する。
- 現行 `test_acceptance_non_acquired_state_never_runs_command`（553–576 行）は `test_acceptance_non_accepted_state_never_runs_command` へ改名し、parameter は `held` / `queued` / `stale-held` / `unavailable` の4件を維持する。

  - `held` / `queued` は max-wait で停止。
  - `stale-held` / `unavailable` は即 `claim-state`。
  - いずれも command 非実行を維持する。

- 新設 `test_acceptance_held_self_runs_command_without_polling`

  - valid `held-self` で sleep せず postclaim 検査と command へ進み、成功時 release しない。

- 新設 `test_acceptance_legacy_self_held_fails_closed_without_polling`

  - wave 前の `{"state":"held","holder_self":true,...}` を返し、`claim-self-unverified` / rc=70、sleep・command・release 全てなし。

- 新設 `test_acceptance_invalid_held_self_fails_closed`

  - stable `ids=` 付きで `holder-false`、`age-nonzero`、`source-unavailable` を検査し、全て `claim-self-unverified`。

- 新設 `test_public_main_self_renew_failure_reports_reason_without_poll_or_release`

  - public `main()` 経由で rc=70、stderr の保持診断と `stage=claim-self-renew-failed` を exact 確認。stdout、sleep、command、release はなし。

- 新設 `test_held_self_merge_failure_aborts_without_releasing_lease`

  - `held-self` 後に behind を発生させ、merge 失敗を注入。
  - `git merge --abort` と clean postcondition は実行するが、`wave_land_window.py release` は呼ばない。
  - これで `HELD_SELF` を `NONE` または `ACQUIRED` へ潰す両退行を検出する。

- [test_cleanup_consumes_ownership_before_release_and_is_idempotent:1647](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t812-lease-self-renew/orchestrator/tests/test_dev_wave_wait.py:1647) を `ACQUIRED` と `HELD_SELF` に広げ、前者だけが release することを固定する。
- [test_second_signal_is_deferred_until_cleanup_completes:1768](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t812-lease-self-renew/orchestrator/tests/test_dev_wave_wait.py:1768) は新しい `release_lease=True` 引数へ追随する。
- deadlock 再現として新設 `test_default_wiring_second_acceptance_reuses_self_held_lease`

  - real git repo と real helper を使い、同じ wave で事前 claim → canonical waiter を実行する。
  - `--max-wait-seconds 1` として旧コードでも長時間 hang させない。
  - 現行コードは `held` → `claim-timeout rc=70`、新コードは `held-self` → command sentinel 実行 → rc=0 となる。

## 4. 事前登録する最小変異

| ID | 最小変異 | KILL する nodeid |
|---|---|---|
| M01 | 自己分岐を wave 前の `return _lease_result("held", lease, self_holder)` へ戻す | `test_self_claim_renews_mtime_and_returns_held_self`; `test_default_wiring_second_acceptance_reuses_self_held_lease` |
| M02 | accepted 集合を wave 前の `{acquired}` のみに戻す | `test_acceptance_held_self_runs_command_without_polling`; deadlock 再現テスト |
| M03 | `os.utime(lease.fd, ...)` だけを除去して `held-self` は返す | `test_self_claim_renews_mtime_and_returns_held_self` |
| M04 | 更新後 `_same_entry` を省略、または false を成功扱いする | `test_self_claim_rechecks_same_entry_after_renewal` |
| M05 | 更新失敗を `held-self` 成功または `held` polling に変える | `test_self_claim_renew_failure_is_structured_unavailable`; `test_public_main_self_renew_failure_reports_reason_without_poll_or_release` |
| M06 | `HELD_SELF` を `ACQUIRED` に写して release 権限を与える | `test_held_self_merge_failure_aborts_without_releasing_lease` |
| M07 | `HELD_SELF` を `NONE` に写し、merge abort も省略する | `test_held_self_merge_failure_aborts_without_releasing_lease` |
| M08 | `held + holder_self=true` / invalid `held-self` の即時 fail-closed guard を除去する | `test_acceptance_legacy_self_held_fails_closed_without_polling`; `test_acceptance_invalid_held_self_fails_closed[...]` |

## 5. repo 全体の波及

repo-wide `rg` で確認できる実 runtime consumer は次の2本だけである。

- producer: [tools/wave_land_window.py:641](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t812-lease-self-renew/tools/wave_land_window.py:641)
- claim JSON consumer: [tools/dev_wave_wait.py:577](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t812-lease-self-renew/tools/dev_wave_wait.py:577)

それ以外の該当箇所は以下。

- 契約テスト: `test_wave_land_window.py`、`test_dev_wave_wait.py`
- 現行運用文: [`.claude/commands/dev-wave.md:52`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t812-lease-self-renew/.claude/commands/dev-wave.md:52) が「`acquired` のときだけ投入」としており、実装後は stale。`dev-wave` 改善候補として親が docs-only で `{acquired, held-self}` へ整合する必要がある。
- 設計正本: `docs/decisions.md` D253 は queue state、D270 の 12435–12438 行は acquired-only。D270 は歴史を書き換えるより、本裁定による supersede を親の記録段で明示する。
- `docs/failures.md` F186/F192/F195/F196、`docs/worklog.md` T-812、`docs/archive/**`、`output/insights/**` は履歴・証跡であり runtime consumer ではない。
- `tools/pegasus/dispatch_compute.py:228,258` の `queued` は scheduler state、`orchestrator/campaign/s8b_budget.py:520` の `held` は別状態機械。変更対象外。
- 他の `.py` / `.sh` に claim JSON の state を読む consumer はない。

## 6. runbook §7.3 の逐語的不整合

親が [docs/pegasus-runbook.md:759](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t812-lease-self-renew/docs/pegasus-runbook.md:759) を直す際、少なくとも次が実装後と食い違う。

- 787–789 行: 「**それ以外のすべての終わり方 … では待ち手が release する。**」  
  `held-self` 後の失敗は release しない例外になる。

- 796–800 行: 「トップレベル `state` の値と `acquired` の **exact 比較**で投入可否を決める。」  
  exact membership `{acquired, held-self}` に変わる。

- 807 行: 「**`acquired` の直後に**待ち手自身が local main を取り直す。」  
  accepted state の直後、すなわち `acquired` / `held-self` 双方に適用される。

- 823–826 行: 「`held` / `queued` … **その後の失敗では release しない**。」  
  `held-self` は polling state ではなく進行 stateだが、同様に release 権限がないことを別記する必要がある。

- 864–866 行: 「受入と land の**どの終わり方でも** lease を手放す。」  
  `held-self` 失敗では保持したまま親の終端 release に委ねるため非同値。

- 875–877 行: 「2 走目の前に `claim` し直す。取り直せなければ 2 走目を投入しない。」  
  fresh 自己保持なら mtime を更新し `held-self` / `age_seconds=0` を返して進む、と明記する必要がある。

## 7. scope と残余 risk

- `tools/run_tests.py`、`_is_acceptance_run`、docs-only fold race は一切変更しない。fold race は既存の裁定パッケージ候補のまま返す。
- release → reacquire は採らない。他 wave の lease・待ち札を更新または削除しない。
- 最大の残余 risk は holder が wave slug の digest だけで、同一 slug の直列な再実行と同時実行を識別できないこと。同一 slug の waiter が重複起動すると双方が `held-self` で進みうるため、「1 slug につき active invocation は1本」を前提として段4で明記すべきである。invocation token/fencing の新設は本 scopeへ混ぜない。
- read-only 段2のため pytest・変異は実走しておらず、緑は主張しない。

## 総括

- 自己 claim は EX flock 内で fd mtime を更新・inode 再照合し、`held-self / age_seconds=0` を返す。
- 待ち手は `{acquired, held-self}` で進み、自己異常は polling せず理由付き rc=70 にする。
- P2 は専用 `HELD_SELF` enumで実装し、merge abort は行うが release はしない。
- 最大 risk は同一 slug の同時 invocation を holder digest だけでは識別できない点。
- 親の択一は P2維持（推奨・既定）対 release権限付与であり、本プランは P2維持を採る。