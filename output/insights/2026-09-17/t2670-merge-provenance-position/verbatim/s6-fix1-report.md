## 変更内容 (file:line と diff)

[orchestrator/tests/test_dev_wave_wait.py:8641](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2670-merge-provenance-position/orchestrator/tests/test_dev_wave_wait.py:8641)

```diff
     repo, lease, env = _real_waiter_repo(tmp_path, wave=wave)
+    env["PYTHONDONTWRITEBYTECODE"] = "1"
```

## 受理・拒否の含意 (2 文) と通る正例

変更前は静的に guard を確認できず checker が拒否し、変更後は関数内の明示代入によって受理します。通る正例は `_run_self_report_acceptance` の同じ代入であり、対象テストの「main-only 違反 → stage 赤・command 0 回」という挙動は変わりません。

## 検査結果 (checker rc / diff --stat / 直接呼び出し)

- checker: **rc=0**
- `git diff --stat`: **1 file changed, 1 insertion(+)**（指定ファイルのみ）
- 対象関数の直接呼び出し: **PASS**（`tempfile.mkdtemp()` 使用）
- pytest: 未実行

## 総括

指定の1行だけ追加しました。既存の期待値・assert は変更していません。