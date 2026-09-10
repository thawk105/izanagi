## 実装した内容

- [tools/check_docs.py:3343](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t360-mutation-transport-task/tools/check_docs.py:3343)
  - `TASKS` 本体を保持し得る RHS subtree、container unpack、function default capture を拒否。
  - `TASKS[key]`、membership、`tuple(TASKS)` は正規の読み取りとして許可。
  - 比較対象は `{task: child_script}` のまま。`env_mode` / `argv_policy` へ広げておらず、D117 の否定文も未変更。
- [test_check_docs.py:2566](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t360-mutation-transport-task/orchestrator/tests/test_check_docs.py:2566)
  - container unpack、深い RHS alias、function default、literal 定義の境界テストを追加。
  - 実 dispatcher の期待写像を `mutation` / `generic` を含む 4 task に更新。
- [test_hooks.py:3967](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t360-mutation-transport-task/orchestrator/tests/test_hooks.py:3967)
  - exact generic gateway の正例と、別綴り・未知 task・別 path・外側 shell 再帰・直接 trampoline の負例を追加。
  - admission registry の compute site-gate 契約が崩れた場合の fail-closed テストを追加。
- [hooks/guard_bash.py:1179](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t360-mutation-transport-task/hooks/guard_bash.py:1179) は未変更です。`apply_patch` が hooks subtree 防護に拒否されました。正本 `hooks/README.md` は、README 以外の hooks 編集を防護有効化前の commit から再構築するよう要求しています。commit 禁止の本依頼内では正規に更新できませんでした。

## 受理集合の変化

- `check_docs.py`
  - 変更前: `alias = TASKS` の直接 alias は拒否するが、`(alias,) = (TASKS,)` は許可。
  - 変更後: mapping 本体を保持する container/unpack/RHS subtree/default capture を拒否。
  - 変更前後とも、literal `TASKS`、task spec の添字読み取り、membership、task 名 snapshot は許可。
- hook
  - 実際の変更前後は同一です。現在も exact gateway 内の `pytest` は許可、`python -m pytest` は拒否されます。
  - テストが要求する未 land の境界は、単一 top-level segmentの canonical
    `python3 tools/pegasus/dispatch_compute.py --task generic -- <非空 argv>`
    だけを許可する形です。

## テスト

- `test_dispatch_inventory_rejects_tasks_container_unpack_alias`
  - 無いと `(alias,) = (TASKS,)` による task 表 drift が静かに通ります。
- `test_dispatch_inventory_rejects_tasks_alias_in_assignment_rhs_subtree`
  - 無いと container 内へ深く埋めた alias が静かに通ります。
- `test_dispatch_inventory_rejects_tasks_function_default_capture`
  - 無いと default 引数経由の `TASKS` 変更が静かに通ります。
- `test_dispatch_inventory_rejects_tasks_alias_subscript_write`
  - 無いと既存の直接 alias 拒否が退行します。
- `test_dispatch_inventory_accepts_real_dispatcher_tasks_reads`
  - 無いと正規の 4 task 抽出や通常読み取りの過剰拒否を見逃します。
- `test_dispatch_inventory_accepts_literal_tasks_definition`
  - 無いと canonical literal 定義まで拒否しても気付けません。
- `test_bash_login_allows_exact_generic_compute_gateway[pytest|python-m-pytest]`
  - 無いと同値な pytest 綴りで gateway の可否が分裂します。
- `test_bash_login_rejects_nonexact_generic_gateway_boundaries[...]`
  - 無いと module綴り、別 path、未知 task、wrapper、外側 `bash -c`、直接 trampoline へ許可が漏れます。
- `test_bash_generic_gateway_requires_compute_site_gate_contract`
  - 無いと compute-only 前提を registry から確認できなくても例外が発火します。

各 owned file は AST parse 済みです。`git diff --check` も通過しました。

## 未実走

- pytest は一切実走していません。実装済み部分も未実走です。
- `test_check_docs.py` の直接 import は growth-hold 防壁に拒否されました。解除環境変数は設定していません。
- `check_docs` の extractor と `guard_bash.decide` は Python REPL から直接 probe しました。
- Web 検索、git add、commit、push、branch 操作は行っていません。

## 期待赤

親 docs 未 land による full `check_docs.py` の赤は exact 1 findingでした。

```text
TASKS_only=['generic', 'mutation'], runbook_only=[], child_script={}
```

それ以外に、hook 本体未変更による静的な期待赤があります。

- exact gateway の `python-m-pytest`
- module綴り、dot path、直接 script、`env` wrapper、未知 task、lookalike path
- 外側 shell 再帰、compound command、空 inner argv
- compute site-gate 契約欠落時の fail-closed

直接 trampoline と gateway 外の直接 `python -m pytest` は現在も拒否され、回帰していません。

## 波及可能性

- `tools/dev_waves/checker.py` は land 後の隔離 checkout で `check_docs` を exact 1 回実行します。親 docs と同じ統合 commit に入らなければ `check-docs` gate が赤になります。
- `tools/task_run_check.py`、`tools/dev_waves/daemon.py`、`tools/dev_wave_land.py` も full `check_docs` の consumer です。
- hook は `.claude/settings.json` から直接、`.codex/hooks.json` から `hooks/codex_guard.sh` 経由で使われます。
- `tools/check_codex_hooks.py` は `guard_bash.py` を copy・HEAD bytes pin の対象にします。将来 hook を未 commit で編集した期間は検査が意図どおり拒否します。
- `tools/codex_worker_launch.py` は同 checker を利用するため、hook の working bytes が HEAD と異なる間は worker 起動にも波及します。
- consumer test は `test_hooks.py` 全体、`test_codex_hooks.py`、`test_codex_worker_launch.py`。registry failure fixture は guard source を一時 repo へ複製して評価します。
- 既存の A/B 所有変更には触れていません。

## 裏取りできなかったこと

- hooks 防護のため、`guard_bash.py` への実装と修正後の `decide` probe は実施できませんでした。
- compute-only 前提そのものは、admission entry の `dispatch_compute --job-run site gate` と、dispatcher の job script・`_job_run` の二重 bnode gateから静的に確認しました。ただし hook がその契約を検証する実装は未 land です。
- pytest、実 queue、compute node 上の動作は確認していません。

## 総括

`check_docs.py` の alias/container/default capture 穴は実装と静的 probeまで完了し、親 docs 未 land以外の finding はありません。hook の境界テストは追加しましたが、自己防護とcommit禁止が衝突したため `guard_bash.py` 本体は未実装です。親側で防護有効化前の正規経路から hook 実装を再構築する必要があります。