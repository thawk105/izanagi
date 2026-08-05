実装済み・未実走です。production コード、docs、M7 は変更せず、commit も行っていません。

追加テストは [`test_validate_generations_public_rejects_invalid_single_generation_candidate()`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-u2-contract-generation/orchestrator/tests/test_env_contract.py:427) です。一世代列に `generation=2` を入れ、public `validate_generations()` が private 構造検査へ委譲することを固定します。

委譲を no-op にした場合：

- exact tuple、exact `GenerationEntry`、有効な contract、key 一致、hash 一意を満たす。
- 列長は 1 なので bootstrap fuse も通過する。
- public 関数が正常終了し、`pytest.raises` が「例外なし」で赤になる。

拒否理由は `generation` が期待値 1 でないことだけです。生成時には正整数 2 として受理され、隣接検査は一世代なので発火せず、前後に同じ入力を拒否する層はありません。

所有外への静的な波及可能性は、pytest collection node が 1 件増えること、ファイル全体を選択する runner の実行対象が増えること、外部の test 件数・node 一覧台帳が更新対象になりうることです。repo 内に新 test 名の固定参照はありません。production API・golden hash・consumer への波及はありません。

`git diff --check` と対象 2 ファイルの `py_compile` は成功しました。pytest は実走しておらず、緑とは主張しません。

## 総括

- public validator の一世代負例を 1 件追加。
- 委譲削除時は例外が消え、追加テストが赤になる。
- 赤の理由は generation 連番検査の欠落だけ。
- production コード・既存期待値・M7 は未変更。
- docs 編集・commit・pytest 実走なし。
- 変更は test ファイルの 10 行のみ。