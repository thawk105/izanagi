# 段 1 brief — [T-2379] test_s8b_approved.py / test_profiler_directive.py の sys.path 暗黙依存を自己完結にする

- 研究前進: 土台。狭い file 選択走 (焦点走・変異 baseline) が 2 file の import 事故で偽赤になり 1 走を空費する
  (worklog entry 1644 の f1、entry 1306 の D1707)。最小差分 = 2 file の import 行を自己完結形に直す。完了判定 = 対象 2 file だけの
  選択走が緑、かつ全収集 (受入) も緑。
- scope: `orchestrator/tests/test_s8b_approved.py` の `from tests.skiputil import Skip, skip  # noqa: E402` と
  `orchestrator/tests/test_profiler_directive.py:341` の `    from codex_roles import policy  # noqa: PLC0415` の 2 箇所だけ。
  conftest / skiputil / production / runner / collection 絞り込み (D711 gate 2) は触らない。gate・検査・台帳・一般化の追加は scope 外。
- 確定済み裁定: D95 (実装面は Codex author)、D1707 (2 file を自己完結させれば直る技術的欠陥、絞り込みは別裁定)。
- 実測 (段 1): 開始 gate rc=0 (main 302b94796 と乖離 0)。対象 2 file だけの選択走 (request 5501.nqsv、計算ノード自動 dispatch) は
  `1 failed / 58 passed / 1 error`:
  - `test_s8b_approved.py` 収集時 `ModuleNotFoundError: No module named 'tests'`
  - `test_profiler_directive.py::test_derived_directive_is_accepted_by_the_role_policy_check` で
    `ModuleNotFoundError: No module named 'codex_roles'` (test_profiler_directive.py:341)
  単独 1 file (5493.nqsv) も rc=1。副作用の供給元 = `test_campaign.py` / `test_campaign_import_invariant.py` / `test_reflux_ir.py`
  (`sys.path.insert(0, ORCHESTRATOR)`)。login で直接 pytest は guard 拒否 (runner 経由が正規経路)。
- 編集面照合: 対象 2 file と skiputil.py を触る branch tip / 作業ツリーは 0 件 (210 branch, 208 worktree)。conftest.py は
  2 tip + 5 codex 木が触るが本 wave は非接触。
- 不変条件: (a) `sys.path` 挿入を増やさない (両 file とも ROOT を自分で挿入済み、`orchestrator/` の挿入は足さない)、
  (b) 検査の意味を変えない (同じ `policy` module の関数・同じ `Skip`/`skip` の意味)、(c) 他 module の収集順に依存しない。
- (P1) 修正形: `orchestrator.` 接頭の絶対 import (`from orchestrator.tests.skiputil import Skip, skip  # noqa: E402` /
  `    from orchestrator.codex_roles import policy  # noqa: PLC0415`) を採る。代替の `from skiputil import` は pytest の
  prepend import-mode (rootdir 挿入) に依存し file 自身の bootstrap で閉じない。`orchestrator.tests.skiputil` は
  `test_s8b_protocol_builder.py`、`orchestrator.codex_roles` は `test_codex_agents.py` 等に先例あり。
  namespace package (`orchestrator/`・`orchestrator/tests/` に `__init__.py` 無し) で通る。
- 成果物: 2 file の import 行修正 (Codex author)、変異 matrix、単独選択走緑 + 受入全走緑、worklog fragment、insight README。
- 分割: 実装子 1 本 (2 file、所有分割不要)。軽量版 (DW-C00): 設計択一は割れず (P1 のみ)、正しさ防壁・受理集合に触れない →
  段 2・3・段 6 レビュー子を省く。

## 変更面アンカー表 (行番号は base 302b94796)

| file | 行 | 現行 (逐語) | 変更後 (逐語) |
|---|---|---|---|
| orchestrator/tests/test_s8b_approved.py | 31 | `from tests.skiputil import Skip, skip  # noqa: E402` | `from orchestrator.tests.skiputil import Skip, skip  # noqa: E402` |
| orchestrator/tests/test_profiler_directive.py | 341 | `    from codex_roles import policy  # noqa: PLC0415` | `    from orchestrator.codex_roles import policy  # noqa: PLC0415` |
