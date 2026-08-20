## 総括

修正完了。child から `pytest` 依存と SKIP 特別扱いを完全に除去しました。commit・docs変更なし。

## 修正内容 (file:line)

- [_dev_waves_serve_child.py:21](/work/1/SFC/tanab/izanagi/.claude/worktrees/T-1222-population-closure/orchestrator/tests/_dev_waves_serve_child.py:21)：`import pytest` を削除。
- 同ファイル:464：コメント中の `pytest` 字句も除去。
- 同ファイル:593-606：`_serve_child_main()` を PASS/FAIL のみへ変更。
- integration 側の parser・SKIP テスト・期待値は未変更。

## 検査結果 (nodeid・PASS/FAIL・実走の有無)

- `test_socket_roundtrip_works_beyond_108_byte_repository_path`：判定なし、実装済み・未実走。
- `test_contained_serve_child_uses_dedicated_helper_entrypoint`：判定なし、実装済み・未実走。

`tools/run_tests.py` は `qstat -Q` preflight failure（rc=1、child未起動、runner rc=16）で実走不能でした。`--force-dispatch` でも同結果です。

- 指定 AST コマンド出力：`False`
- child 内の `pytest` grep：該当なし
- `py_compile`：PASS
- `git diff --check`：PASS

## 波及可能性

child は SKIP を送出しなくなりますが、親側 parser の SKIP envelope 受理能力は維持しています。欠落していた pytest の計算ノード依存のみ解消されます。