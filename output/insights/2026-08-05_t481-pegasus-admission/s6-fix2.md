実装済みですが、計算ノード dispatch 障害のため pytest は未実走です。docs・commit・既存テストの期待値には触れていません。

## 総括

### (a) 変更箇所

[guard_bash.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t481-pegasus-admission/hooks/guard_bash.py:183)

- registry: `.pbs` 2本を `unknown` 登録。
- `_SCRIPT_EXECUTOR_MODULE_OPTIONS`（345行）: `pydoc` / `doctest` / `unittest`、`trace --module` を追加し、`timeit` を除外。
- `_script_executor_targets`（710行）: 複数実行対象、module-name、非実行 mode を分類。
- `_shell_startup_targets` / `_shell_prefix_invocation`（778/811行）: startup file と残余 argv を分類。
- `_script_targets` / `_is_sanctioned`（852/886行）: 全実行対象を検査し、先頭 target による隠蔽を防止。
- `_interpreter_residual_violation`（983行）: `interpreter` / `invalid` / `stdin` / `command` の残余を fail-closed 化。
- `_heavy_segment_violation`（1019行）: 全 target、残余、shell command string の順に判定。

[test_hooks.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t481-pegasus-admission/orchestrator/tests/test_hooks.py:757)

- F1〜F4 の綴り差・複数 target・正例/拒否例を追加。
- inventory を `.pbs`、shebang、`stat` mode 対応へ変更（1146行）。
- `.pbs` 2本の `unknown`・DENY pin を追加（1172行）。
- HEAD 由来の既存 assert は変更なし。変更した test はすべて同 wave の新設 test。

### (b) baseline からの受理集合差分

ALLOW→DENY（裁定済み）:

- `python3 -m pytest.__main__ ...`
- `python3 -m _pytest.main ...`
- `python3 -m cProfile|profile|pdb|trace <Pegasus target>`
- `python3 -m trace --module tools.pegasus.exec_calibrate`
- `python3 -m runpy tools.pegasus.exec_calibrate`
- `python3 -m coverage run <Pegasus target>`
- `python3 -W ... <Pegasus target>` / `python3 -X ... <Pegasus target>`
- `bash -O ... <Pegasus target>` / `bash -o ... <Pegasus target>`
- `python3 -mpytest <sanctioned path>` と bundle・版付き形

DENY→ALLOW（裁定済み）:

- `python3 -mpy_compile <path>` / `python3 -Bmpy_compile -- <path>`
- `python3 -mjson.tool <path>`
- `python3 -mcompileall <path>`
- `python3.10 -Bmtimeit <Pegasus-looking statement>`
- `python3 -Bmrunpy <slash-containing path>`
- `python3 -mcProfile --help <path>`

F1 の startup file、F2 の `pydoc` / `doctest` / `unittest`、F3 の残余 argv、F4 の分離形4例は baseline の受理 bitへ復帰。F5 は registry 同期のみで runtime DENY不変です。実行体 inventory の範囲では、静的照合上、裁定外差分はありません。scope 外6面と既存5本の `local-ok` classも不変です。

### (c) 検査

- `python3 -m py_compile hooks/guard_bash.py orchestrator/tests/test_hooks.py`: rc=0
- `git diff --check`: rc=0
- 焦点 pytest 16 nodeを `python3 tools/run_tests.py` 経由で投入: rc=16、実走0 node
  - 対象: attached/bundle、module identity、executor、F1〜F5、nonrefusing site、shell再帰、registry schema/bit/inventory、provenance borrow
  - 原因: `qstat -Q preflight rc=1`
  - 直接確認: `NQSconnect: [API EACCTAUTH] Unknown user-id. (uid: 31609)`
- Pegasus login 上では pytest を直接走らせていません。したがって「実装済み・未実走」であり、closed・緑は申告しません。
- `check_codex_agents.py`、`check_docs.py`、変異 matrix、受入全走は親工程向けに未実行です。

### (d) 所有外への波及可能性

- production caller: `.claude/settings.json` の `guard_bash.py` PreToolUse 配線。
- 共有 consumer: `_SANCTIONED_PATHS`、provenance借用判定、pytest module判定、shell再帰。
- filesystem consumer: `tools/pegasus/` inventory。新しい shebang・`.pbs` は未登録なら meta-test が赤になります。
- docs consumer: `hooks/README.md` と `docs/pegasus-runbook.md` の registry説明。今回docsは未編集です。
- 既存の別所有差分 `docs/pegasus-runbook.md` は保存し、1 byteも触れていません。

### (e) 未修正所見

F1〜F5について実装上の未修正項目はありません。ただし実走不能のため解消確認は未完了です。レビューBのM5事前登録曖昧性、報告範囲問題、レビューAのdirectory nit、および裁定scope外6面は親の受理集合外なので変更していません。commitも作成していません。