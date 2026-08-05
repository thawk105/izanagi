`check_docs` の stale / unchecked pyc 経路を閉じました。変更は指定された2ファイルのみです。

| 所見 | 判定 | 対応 |
|---|---|---|
| stale / unchecked pyc | closed | [check_docs.py](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t522-admission-registry/wt-B/tools/check_docs.py:2327) を exact source bytes の `compile()` / `exec()` に変更 |
| 例外・状態復元契約 | closed | `BaseException`、型名だけの単一 finding、`sys.modules` / `sys.dont_write_bytecode` 復元を維持 |
| stale pyc 回帰テスト | closed（実装） | [test_check_docs.py](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t522-admission-registry/wt-B/orchestrator/tests/test_check_docs.py:878) に unchecked stale pyc より現 source を優先するテストを追加 |
| B2 / B3 / B4 / B5 / B8 | partial | 親裁定どおり変更なし |
| `reason` / `primary_gate` 同期 | not-done | scope 外 |
| hook 配線検査 | not-done | scope 外 |
| living doc 閉集合化 | not-done | scope 外 |
| `hooks/guard_bash.py` | not-done | 他者所有のため未編集 |

確認結果：

- `python3 -m py_compile ...`: rc=0
- `python3 tools/check_docs.py`: rc=0、`check_docs: 違反なし`
- pytest: 実装済み・未実走。緑は主張しない
- commit・git 操作なし

## 総括

- admission loader の import machinery と stale pyc 経路を除去した。
- 意図的な unchecked stale pyc を固定する回帰テストを追加した。
- 実 repo の `check_docs` は rc=0 を維持した。
- 親裁定の partial / not-done 項目には触れていない。