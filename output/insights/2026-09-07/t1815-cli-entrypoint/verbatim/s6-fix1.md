## 所見対応表 (F-1〜F-4)

| 所見 | 状態 | 対応 |
|---|---|---|
| F-1 | closed | 評価用 commit 後に `HEAD_ONLY.txt` だけの第2 commitを作成。`HEAD != 評価対象 commit` を fixture 内で検査し、oracle/CLI は第1 commitを使用 |
| F-2 | closed | allowlist 環境を module-scope fixture 1箇所に定義。全 Git 呼び出し、親 process の oracle 評価、4 CLI subprocess に適用。ambient `PYTHONPATH`・`PYTHONHOME`・`GIT_*` は継承しない |
| F-3 | closed | module docstring に transport 等価性のみを検査し、意味の正しさは既存 predicate/invariant tests が担うと明記 |
| F-4 | closed | oracle fixture docstring を「worker ごとに1回、直列1回、xdist最大4回」に訂正 |

## 実走結果 (nodeid と rc)

通常状態で以下4 nodeをすべて実走し、passしました。

- `test_cli_entrypoint_matches_library_report[prereg-path]`
- `test_cli_entrypoint_matches_library_report[prereg-module]`
- `test_cli_entrypoint_matches_library_report[gate-path]`
- `test_cli_entrypoint_matches_library_report[gate-module]`

実走結果：

- `PYTHONPATH=. python3 orchestrator/tests/test_s8c_cli_entrypoints.py`: rc=0、4 passed
- `python3 orchestrator/tests/test_s8c_cli_entrypoints.py`: rc=0、4 passed
- 復元確認を含む同じ `PYTHONPATH` なし実走3回: すべて rc=0、4 passed

## 検出力回復の実証

`s8c_gate_report.py` の `sys.path.insert(...)` を一時削除して確認しました。

- `PYTHONPATH` なし: rc=1、`[gate-path]` のみ failed、残り3 node passed
- 外側に `PYTHONPATH=.` あり: rc=1、同じく `[gate-path]` のみ failed

したがって、継承 `PYTHONPATH` による M4 の mask は解消されています。行は復元済みで、復元後の `git diff --exit-code -- orchestrator/campaign/` は rc=0・差分なしです。

## 残った懸念・親へ返す判断

対象4所見はすべて closed。scope 内の残件はありません。production file、docs、その他のテストは最終状態で変更しておらず、commitも作成していません。`effective` は oracle で明示的に `False` を検査し、全CLI経路との既存一致検査も維持しています。

## 総括

変更は [test_s8c_cli_entrypoints.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1815-cli-entrypoint/orchestrator/tests/test_s8c_cli_entrypoints.py) のみです。

- 差分: 81 insertions / 17 deletions
- 内容: 閉じた環境、2 commit fixture、transport 射程説明、xdist 評価回数説明、`effective=False` の事前検査
- `git diff --check`: rc=0
- 最終自走: rc=0、4 passed
