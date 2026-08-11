5 件とも実装・テスト追加済みですが、pytest は dispatch infrastructure の rc=16 で起動できなかったため、すべて `partial（実装済み・未実走）` とします。docs 編集・commit・B-06 対応は行っていません。

### 所見対応表

| 所見 | 状態 | 対応 |
|---|---|---|
| FIX-1 | partial | `acquired` を `holder_self` 拒否 guard から除外。実 helper 完全 payload fixture、command 1 回、`ACQUIRED` ownership、後段失敗時 release の正例を追加。 |
| FIX-2 | partial | `utime` 中に pathname を別 inode へ交換し、`utime → post-fstat → same-entry`、`self-renew-failed`、置換 bytes 不変を固定。 |
| FIX-3 | partial | flock 直後に pathname を交換し、post-flock metadata が locked fd の `fstat` 由来で、entry 不一致が `FileNotFoundError` へ倒れることを固定。 |
| FIX-4 | partial | source extra/missing key、bool age、大文字 12 桁 hex の負例を追加。全例で exact stage、sleep・command・release 0 を要求。 |
| FIX-5 | partial | status 中の `os.utime` 呼出し回数を厳密に 0 とし、既存 bytes/mtime 不変検査と併記。 |

主な変更箇所は [dev_wave_wait.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t812-lease-self-renew/tools/dev_wave_wait.py:598)、[test_dev_wave_wait.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t812-lease-self-renew/orchestrator/tests/test_dev_wave_wait.py:196)、[test_wave_land_window.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t812-lease-self-renew/orchestrator/tests/test_wave_land_window.py:316) です。段 5 から dirty な `tools/wave_land_window.py` は今回編集していません。

### 検査

以下はいずれも `tools/run_tests.py` 経由で試行しましたが、`qstat -Q` が `EACCTAUTH Unknown user-id` となり rc=16。pytest 本体は未起動です。

- 焦点 6 nodeid：rc=16
  - `test_acceptance_real_acquired_payload_runs_command_and_releases_on_failure`
  - `test_claim_once_real_acquired_payload_grants_acquired_ownership`
  - `test_acceptance_invalid_held_self_fails_closed`
  - `test_self_claim_detects_path_replacement_after_utime`
  - `test_open_lease_uses_locked_fd_metadata_after_path_replacement`
  - `test_self_status_does_not_renew_or_rewrite_lease`
- `test_wave_land_window.py` + `test_dev_wave_wait.py` 全体：rc=16
- `test_plain_runner_coverage.py`：rc=16
- `--collect-only` も同じ rc=16
- AST parse：rc=0
- `git diff --check`：rc=0

したがって、親が確認した 3 赤を消したという実走上の主張はしていません。

### 変更後の受理・拒否挙動

`OK*` は lower-case 12 桁 hex holder、`type(age_seconds) is int`、source が exact `{"status":"ok","reason":null}`。`RF` は source が dict かつ `reason="self-renew-failed"` です。

| state | holder_self | source | 挙動 | ownership / cleanup |
|---|---:|---|---|---|
| acquired | false / true | 任意 | 受理・進行 | `ACQUIRED`、後段失敗時 release |
| held-self | true | OK* | 受理・進行 | `HELD_SELF`、release なし |
| held-self | true | 非 OK* | `claim-self-unverified` | `HELD_SELF`、release なし |
| held-self | false | 任意 | `claim-self-unverified` | `HELD_SELF`、release なし |
| held | false | 任意 | polling | `NONE` |
| held | true | 任意 | `claim-self-unverified` | `HELD_SELF`、release なし |
| queued | false | 任意 | polling | `NONE` |
| queued | true | 任意 | `claim-self-unverified` | `HELD_SELF`、release なし |
| stale-held | false | 任意 | `claim-state` | `NONE` |
| stale-held | true | 任意 | `claim-self-unverified` | `HELD_SELF`、release なし |
| unavailable | false | 任意 | `claim-state` | `NONE` |
| unavailable | true | RF | `claim-self-renew-failed` | `HELD_SELF`、release なし |
| unavailable | true | その他 | `claim-self-unverified` | `HELD_SELF`、release なし |

### 静的な波及可能性

- `_acquired()` と `_RoutingAcceptanceEffects` の既定 payload を完全形へ統一したため、これらを共有する acceptance、merge、signal、cleanup consumer tests 全体が再実走対象です。
- `_claim_once` の private caller は `_wait_until_acquired` と同ファイル内テストのみ。公開 CLI では新規取得、stale 再取得、signal cleanup の 3 既知赤へ直接波及します。
- `_open_lease` の consumer は `claim`、`release`、`status`。FIX-3 は production 無変更で、その fd/pathname 契約をテストで固定しています。
- inode 交換および `utime` spy は pytest `monkeypatch` 内だけで復元され、共有 production state は変更しません。
- 新規テスト追加に伴う `test_plain_runner_coverage.py` と、親提示の real-helper 3 nodeid は必須再確認対象です。

## 総括

- FIX-1〜FIX-5 は実装済みですが、pytest 未実走のため全件 partial です。
- 受理集合は `{acquired, valid held-self}` のまま、fail-closed 条件も緩めていません。
- 残る risk はテスト未実走と、共有 acquired fixture 完全化による既存 consumer 赤です。
- 親は runner が利用可能になった後、焦点 6 nodeid、2ファイル全体、meta-test、既知の 3 赤を再走してください。