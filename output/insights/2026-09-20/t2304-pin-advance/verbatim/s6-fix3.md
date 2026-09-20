## 変更の要約

対象テストの inline literal 1行だけを更新しました。

```diff
-        "p3-t178-ycsb-a-workload-conditioned-autonomous-4b75e24e"
+        "p3-t178-ycsb-a-workload-conditioned-autonomous-d567badf"
```

コメントと独立 pin を維持しました。旧値は `_T816_POLICY_BOUND_CAMPAIGN_IDS` と既存の epoch テストで保持されているため、このテストへの `!=` 追加は省きました。

## 確認

- `rg` で fix1 報告の再計算値と current dict の同 key が `d567badf` で一致することを確認。
- `python3 -m py_compile`：成功。
- `git diff --check`：成功。
- pytest は未実行。

## 総括

指定の1ファイル・1テスト・1行の修正を完了しました。他ファイル・docs の編集、`git add`／`commit`／`checkout`／`stash` は行っていません。