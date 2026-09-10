指定 2 ファイルのみ編集し、commit は作成していません。

| 所見 | 状態 | 対応 |
|---|---|---|
| G1 | partial（実装済み・未実走） | 所有権を状態機械化し、cleanup 開始時に権限を消費。成功は `RETAINED` へ確定し、全経路で handler を復元。古い cleanup closure は残らない。 |
| G2 | partial（実装済み・未実走） | `NONE / UNKNOWN / ACQUIRED` を分離。構造化された non-acquired 応答後は `NONE` とし release しない。待ち札の300秒失効コメントも追加。 |
| G3 | partial（実装済み・未実走） | commit 直後に SHA を固定し、その SHA の message を検査。受入起動直前にも `HEAD` の一致を再確認。 |
| G4 | partial（実装済み・未実走） | Git/helper を専用 process group で起動し、timeout 時は group 全体を kill。abort 後に `MERGE_HEAD` 不在と tracked clean を検査。 |
| G5 | partial（実装済み・未実走） | producer の missing-file、invalid PID source を literal event 列の exact 比較へ変更。 |
| G6 | partial（実装済み・未実走） | 成功境界・実 handler・mask 順序・timeout 後の非 retry/process-group kill を壊すと赤になるテストへ強化。 |
| G7 | partial（実装済み・未実走） | M1 は subprocess 0 回を直接検査。M4/M5/M8 は後段まで到達可能な routing fixture とし、投入回数だけで変異を殺す構成に変更。 |

変更ファイル：

- [tools/dev_wave_wait.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t740-canonical-waiter/tools/dev_wave_wait.py)
- [test_dev_wave_wait.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t740-canonical-waiter/orchestrator/tests/test_dev_wave_wait.py)

検証結果：

- 対象範囲 `orchestrator/tests/test_dev_wave_wait.py` を `tools/run_tests.py` 経由で2回試行
- いずれも `qstat -Q preflight rc=1` の dispatch infrastructure failure。実行された nodeid はありません
- AST parse、production import、`git diff --check`: 成功
- `python3 tools/check_codex_agents.py`: rc=0
- `python3 tools/check_docs.py`: rc=0
- worktree の変更は指定された2ファイルだけ

所有外への波及可能性：

- repo 内に当該 script や内部 lifecycle 型を直接参照する caller/shared fixture は見つかりませんでした。
- `tools/wave_land_window.py` の release 契約には依存しますが、同ファイルは未変更です。
- `.claude/commands/dev-wave.md` と `docs/dev-wave/**` は引き続き未結線で、今回の scope 外です。
- consumer test、main land 済みテストの期待値は変更していません。

## 総括

G1〜G7 の実装と回帰テストは完了していますが、Pegasus の dispatch infrastructure failure により pytest 未実走です。このため全所見を `closed` とは認定せず、`partial（実装済み・未実走）` と報告します。commit は作成していません。