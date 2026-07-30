## 総括

- 対象 test のみ修正。子 PID を deadline 付きで待ち、未登録時は明示的に失敗。
- 停止理由・limit trigger・残存 process・`_assert_pid_gone` の検査は維持。
- 焦点 node: `...::test_sigterm_ignoring_child_is_killed -q -rf` → `1 passed`。
- 指定全走: `python3 -m pytest orchestrator/tests/test_codex_worker_launch.py -q -rf` → `58 passed`。
- 負荷試験: `python3 -m pytest orchestrator/tests/test_codex_worker_launch.py -q -n 16` を同時に2回 → 各 `58 passed`。
- `git diff --check` 成功。実装・docs は変更せず、commit も作成していない。