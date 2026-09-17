## 変更した file と anchor (file:line、old → new)

指定2 file の4か所のみ変更しました。

- `tools/check_docs.py:734`：`TextLimit(5_460, 400)` → `TextLimit(5_732, 400)`
- `orchestrator/tests/test_check_docs.py:9872`：`TextLimit(5_460, 400)` → `TextLimit(5_732, 400)`
- 同 `:7426`：`_pad_to_bytes` の `5_461` → `5_733`
- 同 `:7604`：`5461 bytes > 予算 5460 bytes` → `5733 bytes > 予算 5732 bytes`

## 実走結果 (`check_docs.py` の変更前後の rc と出力)

変更前：rc=1

```text
check_docs: 1 件の違反
  - .agents/skills/next-tasks/SKILL.md: 5730 bytes > 予算 5460 bytes
```

変更後：rc=0

```text
check_docs: 違反なし
```

`PYTHONPATH=. python3 orchestrator/tests/test_check_docs.py` は growth hold により開始前拒否（rc=1）。

```text
GrowthTestHoldBypassRefused: IZANAGI_GROWTH_HOLD_BYPASS_REFUSED_V1 {"node_id":"test_check_docs.py::*","release_env":"IZANAGI_RUN_GROWTH_HELD_TESTS","release_token":"explicit-user-command"}
```

`git diff --check` は成功しました。

## 総括

数値追従は実装済み、checker は通過しました。テストは**実装済み・未実走**で、親による関連テストと変異 matrix の実走が残ります。commit・`git add`・branch 操作はしていません。
