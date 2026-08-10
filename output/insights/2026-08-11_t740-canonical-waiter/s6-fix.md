F1〜F10 を指定 2 ファイルだけで実装しました。docs、`tools/wave_land_window.py`、所有外テストは変更せず、commit / git add も行っていません。

### 所見対応表

| 所見 | 状態 | 対応 |
|---|---|---|
| F1 | partial | public `main()` の成功 return まで signal handler を維持し、成功後 signal callback・cleanup 中の再 signal 遅延を実装。実 signal subprocess テストも追加。未実走。 |
| F2 | partial | helper の claim 呼出し開始を明示追跡し、それ以前の preflight 失敗では release しない。未実走。 |
| F3 | partial | 検査済み message bytes を管理下の一時 file に固定。commit 後に `git log --format=%B` で trailer を再検査。未実走。 |
| F4 | partial | resolved cwd と `--show-toplevel` の一致を要求。指定された全 Git 環境変数を除去。branch suffix 契約は維持。未実走。 |
| F5 | partial | helper/Git stage に既定 300 秒 timeout。受入 child は timeout 無し。zombie を死亡判定。未実走。 |
| F6 | partial | 成功出力に lease 保持、TTL 残余、期限後の排他喪失、fencing 不在を表示。未実走。 |
| F7 | partial | `_claim_once` の直接単体テストと、後段まで到達可能な投入回数ベース E2E fixture を追加。未実走。 |
| F8 | partial | negative cases の全 `_Effects` event 列を literal exact 比較へ強化。未実走。 |
| F9 | partial | `worktree-<slug>`、環境変数 lease、実 merge/message、cwd、stdout/stderr 継承を結合検査へ追加。未実走。 |
| F10 | partial | JSON array/scalar、release 非0/不正JSON、merge abort 非0を追加検査。未実走。 |

全項目が `partial` なのは実装不足ではなく、段 6 契約上、pytest 未実走の所見を `closed` と申告できないためです。

変更箇所は [tools/dev_wave_wait.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t740-canonical-waiter/tools/dev_wave_wait.py:36) と [test_dev_wave_wait.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t740-canonical-waiter/orchestrator/tests/test_dev_wave_wait.py:357) のみです。

### 検査結果

- `python3 tools/run_tests.py orchestrator/tests/test_dev_wave_wait.py -q`
  - 2 回試行
  - いずれも `qstat -Q preflight rc=1` による dispatch infrastructure failure、rc=16
  - pytest 起動前停止のため、緑は主張しません
- Python compile 検査: 成功
- `git diff --check`: 成功
- `python3 tools/check_codex_agents.py`: 成功
- `python3 tools/check_docs.py`: 成功

### 所有外への波及可能性

- 現在、production caller は未結線です。`docs/pegasus-runbook.md` からの接続は親の担当です。
- `_Effects` の変更は内部 API で、静的検索上の利用者は所有内テストだけです。
- `test_campaign_import_invariant.py` の repository scan、実 `wave_land_window.py`、親の mutation matrix は影響確認対象ですが未実走です。
- message/commit command の変異 anchor は一時 file と commit-message postcheck の追加により更新が必要です。
- 任意 command、branch suffix、PID/starttime 契約、既知の fencing/race 限界は変更していません。

## 総括

F1〜F10 の限定修正は実装済みで、対象外ファイル・docs・既存 tracked テストには触れていません。現時点の唯一の未完了事項は、Pegasus scheduler preflight 障害により対象 pytest を実走できていないことです。