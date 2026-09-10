実装は指定 4 ファイルに限定して完了しました。docs 編集・commit は行っていません。pytest は Pegasus の dispatch 障害により未実走です。

## 受理・拒否挙動

| claim state | 現行 | 変更後 | 失敗時 release |
|---|---|---|---|
| `acquired` | 即受理 | 即受理 | あり |
| foreign `held` / `queued` | polling | polling | なし |
| `held` + `holder_self=true` | polling後 timeout | 即 `claim-self-unverified` | なし |
| valid `held-self` | 未知 state、`claim-state` | 即受理 | なし |
| invalid `held-self` | 未知 state、`UNKNOWN` cleanup | 即 `claim-self-unverified` | なし |
| foreign `stale-held` / `unavailable` | 即 `claim-state` | 同じ | なし |
| self-renew `unavailable` | 専用理由なし | 即 `claim-self-renew-failed` | なし |
| 壊れたJSON・未知 state | `UNKNOWN` cleanup | 変更なし | あり |

stale な自己 lease は従来どおり unlink → `acquired` で再取得します。

## 実装内容

- [wave_land_window.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t812-lease-self-renew/tools/wave_land_window.py:300)
  - flock 後の再 `fstat` を age/stale の authority に変更。
  - fresh 自己保持を EX flock 内で更新し、実 mtime 由来の age で `held-self` を返却。
  - `utime`、post-`fstat`、owner/regular 検査、inode 照合、更新後 stale をすべて `self-renew-failed` へ畳み込み。
  - payload は書き換えず、`status` も非更新のまま。

- [dev_wave_wait.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t812-lease-self-renew/tools/dev_wave_wait.py:581)
  - 受理集合を `{acquired, held-self}` に変更。
  - holder、exact bool、int age、exact source shape を検証。
  - `HELD_SELF` を新設し、merge abort 権限あり・release 権限なしに分離。
  - 自己状態不整合を polling せず exact stage の rc=70 に変更。

## テスト追加

[lease primitive tests](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t812-lease-self-renew/orchestrator/tests/test_wave_land_window.py:155) に以下を追加しました。

- renewal、実 mtime age、更新後 stale、foreign 非更新
- renewal の4注入点：`utime` / post-`fstat` / owner検査 / `_same_entry=False`
- renewal 中の EX flock、stale自己再取得、flock後 freshness、status不変

[waiter tests](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t812-lease-self-renew/orchestrator/tests/test_dev_wave_wait.py:649) には以下を追加しました。

- valid/invalid `held-self`、legacy self-held、renew失敗診断
- age 0 と実観測 age 7 の双方の受理
- 受入赤・postclaim失敗・signalで release/sleep 0、実 lease bytes/mtime不変
- merge失敗時の abort と非release
- real git/helper による事前 claim → 2回目受入の deadlock 再現
- 指定どおり `test_acceptance_non_accepted_state_never_runs_command` へ改名

## 検査結果

- AST compile：指定4ファイル、rc=0
- `git diff --check`：rc=0
- pytest focused（新設・改名20 base nodeid）：rc=16、実行開始前停止
- pytest collection（対象2ファイル）：rc=16、実行開始前停止
- pytest 対象2ファイル全体＋F42 meta-test  
  `test_plain_runner_coverage.py::test_every_test_file_is_self_runnable_or_allowlisted`：rc=16、実行開始前停止

全て `qstat -Q preflight rc=1` による dispatch infrastructure failure です。pytest の赤は0件ですが、緑も主張しません。実装済み・未実走です。meta-test も投入はしましたが未実走です。

## 波及可能性

- runtime consumer は `wave_land_window.py::main` と `dev_wave_wait.py::_claim_once` のみでした。
- 共有 fixture `_helper`、`_run_acceptance`、`_RoutingAcceptanceEffects` は既定挙動を維持して拡張しています。
- `orchestrator/tests/README.md` には対象2テストファイルが既に登録済みです。
- 過去の mutation ledger は旧テスト名を履歴として保持しています。親が作る今回の mutation spec は新 nodeid を使う必要があります。
- 親側では runbook/dispatcher の acquired-only 記述、変異実走、対象2ファイル全走、meta-test、commit が残っています。

## 総括

- R-1〜R-7を指定4ファイルへ実装し、docs・commitには触れていません。
- `held-self` は実mtimeを根拠に受理し、merge abort可・release不可です。
- 残る主要riskは同一slug重複invocation、heartbeat/fencing不在、版混在時の`UNKNOWN` cleanupです。
- Pegasus queue preflight障害のためpytestは実装済み・未実走で、親による再走が必須です。