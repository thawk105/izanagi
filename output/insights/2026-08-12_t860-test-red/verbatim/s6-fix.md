## 総括

[orchestrator/tests/test_spool_fold.py:3015](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t860-test-red/orchestrator/tests/test_spool_fold.py:3015) に次の positive control を追加しました。

`test_fixture_tools_imports_uses_fixture_restores_state_and_propagates_exceptions`

この 1 node で契約 1〜4 を固定しています。

- 1: `launch_authority.__file__` が `tmp_path` 由来の fixture repo 配下であり、相対位置が `tools/dev_waves/launch_authority.py` であることを検査します。
- 2: 正常退出後、`sys.path` の全内容、`dev_waves*` の key 集合、各 module object identity が入場前と一致することを検査します。
- 3: marker 例外が同一 object のまま伝播し、例外退出後にも 2 と同じ復元が起きることを検査します。
- 4: 実 checkout の `launch_authority` を事前ロードし、fixture context 退出後に元の module object が `is` で戻ることを検査します。

恒真でない根拠は以下です。

- `sys.path.insert(0, str(ROOT / "tools"))` へ変異すると、`repo.resolve() in module_file.parents` と fixture-relative path 判定が落ちます。
- `sys.path[:] = original_path` を削ると、正常・例外経路双方の `sys.path == path_before` が落ちます。
- `dev_waves*` の削除を弱めると、fixture 限定 probe module が残り key 集合比較で落ちます。
- 元 module の再登録を削除・再生成へ変えると、module object の `is` 比較が落ちます。
- cleanup を正常経路だけにすると、例外退出後の path／module 比較が落ちます。
- 例外を握り潰すと `else` 節の `AssertionError`、別例外へ差し替えると marker の identity 比較が落ちます。

既存 node への波及はありません。既存 4 node、既存 helper、期待値、assert 本体には一切触れず、68 行の純増です。fixture 複製は新規 node で一度だけ行い、追加 probe は小さな fixture 内ファイルです。変更ファイルも指定の 1 本だけで、commit は作成していません。

AST 構文解析と `git diff --check` の静的確認のみ実施しました。pytest を含むテスト実行は行っておらず、状態は明確に **実装済み・未実走** です。