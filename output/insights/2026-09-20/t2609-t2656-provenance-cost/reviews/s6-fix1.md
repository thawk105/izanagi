## 総括

[対象テスト](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2609-unit-impl/orchestrator/tests/test_check_ai_provenance.py:8429)のみ修正しました。変更前後は以下です。

```diff
     (tmp_path / '.git' / 'order').write_text('z.py\nnew.py\na.py\n')
+    # Both diff-tree plumbing paths ignore diff.orderFile; compare their lists
+    # directly so Git's path order (including duplicates after decoding) matters.
     expected = {oid: provenance._commit_paths(oid) for oid in [root, second]}
-    assert expected[root] != sorted(expected[root])
     assert provenance._batch_nonmerge_paths([root, second]) == expected
```

orderFile 設定、symlink・特殊文字・非 ASCII 名を維持し、実 Git による両経路のリストを順序込みで比較します。

pytest は **未実走**。対象 nodeid を `tools/run_tests.py` 経由で試行しましたが、`qstat -Q preflight rc=1`、runner rc=16、`child_started=false` でした。

静的確認では、対象テスト外の AST・所有外の追跡ファイル差分・実装ファイルの SHA256 は変更前と一致。所有外へのコード変更の波及はありません。`git diff --check` も成功しました。