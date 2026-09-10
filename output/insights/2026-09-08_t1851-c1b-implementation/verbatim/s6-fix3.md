## 総括

- [test_s8b_terminal_evidence.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/t1851-c1b-fix3/orchestrator/tests/test_s8b_terminal_evidence.py:115) の workload と `run_cmd` の read ratio を `80` から `81` に変更。三軸は `81 / 0.9 / 0` となり、どの holdout とも一致しません。
- holdout-safe 陽性対照は scanner の canonical encoding helper から汚染 payload を生成する形に分離。既存の期待値は変更せず、workload と `run_cmd` の平文漏洩拒否を維持しました。
- conjunction 検算:

```text
conjunction hits: []
```

- 実走範囲: `orchestrator/tests/test_s8b_terminal_evidence.py` 全 nodeid。fixture 参照テストを含めて結果は維持されています。

```text
72 passed in 0.57s
```

- fixture の意図は維持できています。証拠文書では workload と `run_cmd` が digest のみで束縛され、明示的な holdout 平文の拒否も検査します。
- 所有外ファイルの変更、commit、docs 編集はありません。
- `git diff --stat`:

```text
orchestrator/tests/test_s8b_terminal_evidence.py | 17 +++++++++++++----
1 file changed, 13 insertions(+), 4 deletions(-)
```