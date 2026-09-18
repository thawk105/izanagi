## 総括

**実装済み・未実走です。** 指定された 2 ファイルだけを変更しました。

- `tools/spool_fold.py:3424` に lazy import を追加。3475 行以降で `DevWavesError` の code と sanitize 済み detail を指定形式の JSON で表示します。`from exc`、その他の例外表示、構造的拒否の 2 行は維持しています。受理・拒否判定は変更していません。
- `orchestrator/tests/test_spool_fold.py:27` に import、2452 行に指定の正例テストを追加。既存 helper と実 verifier を使い、健全状態の確認後に dangling HEAD を作ります。stub・monkeypatch は追加していません。

実走対象の新 nodeid:
`orchestrator/tests/test_spool_fold.py::test_commit_identity_gate_exception_path_reports_declared_detail`

pytest は起動前に拒否されたため、**実行件数 0、passed / failed 件数は未取得**です。M1 も未実施で、「新テストだけが detail 欠落を理由に赤になる」ことは未確認です。変異は適用しておらず、最終状態は修正実装です。detail の実物も未観測で、期待値 `{"kind":"head","label":"git"}` との一致は未確認です。

静的列挙の結果:

- caller: `tools/spool_fold.py:3501`（mark）、3526（finalize）、`tools/dev_wave_land.py:5343`。
- test consumer: `orchestrator/tests/test_dev_wave_land.py:6271` の同名 stub、7915 の実呼び出し。
- 指定文字列の `grep -rn` は今回追加したテストだけに一致。既存 test・docs の pin はありません。
- meta-test は `orchestrator/tests/test_fold_gate_nodes_contract.py` に存在します。特に `test_ast_derived_reader_set_matches_registry_in_both_directions` が AST 由来のテスト集合を検査します。こちらも未実走です。

実装上の設計逸脱はありません。未完は通常実走・変異検証・meta-test 実走です。`git diff --check` は成功しました。最終 `git diff --stat`:

```text
 orchestrator/tests/test_spool_fold.py | 20 ++++++++++++++++++++
 tools/spool_fold.py                   |  6 ++++++
 2 files changed, 26 insertions(+)
```

自動承認レビュー（PreToolUse hook / `guard_bash`）が指定 pytest の直接実行を拒否しました。理由は実行場所が Pegasus ログインノード `pegasus02` であり、計算ノードでの実行を要求するためです。