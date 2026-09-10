## 総括

段6 fixを実装済み・未実走です。今回編集したファイルは次の2つです。

- [test_s8c_preregistration_invariant.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1379-c05-activation/orchestrator/tests/test_s8c_preregistration_invariant.py)
- [test_s8c_preregistration_core.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1379-c05-activation/orchestrator/tests/test_s8c_preregistration_core.py)

自己点検結果:

1. 1a: 非`.py` pathを空の関数・symbol集合として登録し、早期returnする処理を追加済み。
2. 1b: C05の`consume_schedule`と`verify_schedule`をfunction checksへ追加済み。
3. 1c: 指定されたC05の4つのexclusion pinを追加済み。
4. 2a: frozen hashを`a40fc173...b17b5a6`へ更新済み。
5. 2b: `nul`、`cr`、`lf`の3つのexpected SHA-256を指定値へ更新済み。
6. 2c: decider versionの3箇所をv5へ更新し、対応するテスト関数名もv5へ変更済み。

`git diff --check`は問題ありません。pytestは指示どおり実走していません（実装済み・未実走）。docsは編集せず、commitも作成していません。既存の段5差分は保持しています。