現行挙動は、`claim` の全通常 state が rc=0で返り、runbook 上はトップレベル `state == "acquired"` と Git 再検査の積だけを受理します。それ以外の state・不正出力・各 subprocess 非0は拒否します。producer の canonical waiter は未存在でした。この受理・拒否集合を基礎に、R1〜R12 の裁定差分のみ適用しました。

## 実装

- [tools/dev_wave_wait.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t740-canonical-waiter/tools/dev_wave_wait.py:61)
  - `_Effects` 注入 seamと `shell=False` の subprocess 実装。
  - [CLI 契約](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t740-canonical-waiter/tools/dev_wave_wait.py:140): `producer` / `acceptance`、30〜120秒 poll、最大待機時間、必須 `--`。
  - [producer 状態機械](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t740-canonical-waiter/tools/dev_wave_wait.py:216): exact PID、`/proc/<pid>/stat` start-time、pid-only 縮退の明示、死亡後30秒 grace。
  - [exact JSON claim](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t740-canonical-waiter/tools/dev_wave_wait.py:299): duplicate key・型・未知 state を拒否。
  - [tree identity preflight](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t740-canonical-waiter/tools/dev_wave_wait.py:354): worktree、非 detached、branch suffix、tracked clean。
  - [acceptance 状態機械](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t740-canonical-waiter/tools/dev_wave_wait.py:494): claim、main 再取得、behind merge、message trailer、postcheck、command、abort/release。
  - command rc=0 の成功終端だけ lease を保持。それ以外は releaseし、cleanup 不明は rc=74。
  - SIGTERM/SIGHUP/SIGINT を cleanup 経路へ通し、SIGKILL・host停止は既存TTLへ委譲。

- [orchestrator/tests/test_dev_wave_wait.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t740-canonical-waiter/orchestrator/tests/test_dev_wave_wait.py:42)
  - プラン記載の全 nodeid を追加。
  - production から独立した option literal 集合と公開CLI拒否検査。
  - negative case の subprocess 呼出し列を exact 比較。
  - start-time、grace、identity、signal、message trailer、成功時lease保持を追加検査。
  - [実 Git・実 lease helper の結合検査](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t740-canonical-waiter/orchestrator/tests/test_dev_wave_wait.py:737)を追加。

## 検査結果

pytest は実行開始できませんでした。緑は主張しません。

- `test_dev_wave_wait.py` 全体:
  - `--force-dispatch`: pytest起動前に `qstat -Q preflight rc=1`、runner rc=16。
  - bounded local admission: dispatchへ回った後、同じ理由で rc=16。
- `test_wave_land_window.py` と `test_campaign_import_invariant.py`:
  - pytest起動前に同じ infrastructure failure、rc=16。
- `--collect-only` も admission後に同じ rc=16。
- `python3 tools/check_codex_agents.py`: rc=0。
- `python3 tools/check_docs.py`: rc=0。
- AST解析、import smoke、両新規ファイルの whitespace check: 成功。
- `git status` は上記2ファイルの未追跡追加のみ。commit・addは未実施。

親 docs 未 land に起因して事前指定する赤 finding はありません。新規テストは docs 本文を参照しません。

## 残る所見

- 親による runbook §7.3 の canonical invocation 更新が未 land。
- scope外の caller/consumer は `.claude/commands/dev-wave.md`、`docs/dev-wave/**`、各 wave の手書き待ち手。canonical script への機械的結線は未実施です。
- 共有 fixture の変更はありません。影響候補は既存 lease helper、全テスト走査、import invariant、将来のrunbook callerです。
- 既知限界は、wave digestだけのrelease権限、最終postcheckからcommand開始までのrace、TTL超過時のfencing不在、SIGKILL・host停止、任意commandを受理全走として強制しない点です。
- 実走再開には Pegasus queue/preflight の復旧、またはrunnerが認めるbounded local余裕が必要です。

## 総括

指定された2ファイルだけに、プランv2の canonical waiterと防壁テストを実装しました。静的検査と非pytest checkerは通過していますが、全pytest nodeidは基盤rc=16のため実装済み・未実走です。