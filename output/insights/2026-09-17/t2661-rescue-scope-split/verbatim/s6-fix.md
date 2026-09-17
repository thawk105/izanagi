## 所見対応表

| 所見 | 状態 | 確認 |
|---|---|---|
| U1 所見 1 | closed | 全角記号を半角化。rescue の commit・件数・terminal parser と衝突しないことを目視確認。 |
| U1 所見 2 | closed | `_checked_git` に trap を追加。M3 が trap の AssertionError で赤になることを実走確認。 |

## 変更一覧

- [tools/audit_dangling_commits.py:1926](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2661-impl/tools/audit_dangling_commits.py:1926)：`（…）；` → `(…);`。文言は維持。
- [orchestrator/tests/test_audit_dangling_commits.py:4311](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2661-impl/orchestrator/tests/test_audit_dangling_commits.py:4311)：`_audit_snapshot` のみ trap → `_checked_git` にも `_forbid_offrepo_io` を追加。

## 実走結果

指定コマンド `PYTHONPATH=. python3 orchestrator/tests/test_audit_dangling_commits.py`：**166 passed、rc 0**。

復元後、同 harness で以下の nodeid を選択実走：**3 passed、163 deselected、rc 0**。共通接頭辞は `orchestrator/tests/test_audit_dangling_commits.py::`。

- `test_explicit_off_disclosure_is_distinct_from_missing_root`
- `test_explicit_full_without_root_is_execution_failure[absent]`
- `test_explicit_full_without_root_is_execution_failure[empty]`

`git diff --check` も rc 0。

## 反実仮想

full＋roots 空の RuntimeError ブロックを一時削除し、上記 absent／empty を実走：**2 failed、164 deselected、rc 1**。両方とも `_checked_git` の trap に到達。赤理由の逐語行：

```text
E       AssertionError: off must not touch offrepo I/O
```

一時削除はバイト単位で復元済み。復元後の `git diff --stat`：

```text
 orchestrator/tests/test_audit_dangling_commits.py | 1 +
 tools/audit_dangling_commits.py                   | 2 +-
 2 files changed, 2 insertions(+), 1 deletion(-)
```

## 期待値変更

既存 test の期待値は一切変更していません。開示行の assert は半角化の影響を受けず、追随変更も不要でした。専用エラー文言 assert は維持しています。

## 総括

対象 nit 2 件を closed としました。受理集合は不変で、変更は所有 2 file のみです。docs 編集・`git add`・`git commit` は行っていません。
