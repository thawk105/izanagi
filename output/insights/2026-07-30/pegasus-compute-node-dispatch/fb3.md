FB-1 / FB-2 はともに **closed** です。編集は所有対象の 2 ファイルだけで、docs 編集・commit・build・全走は行っていません。

- [guard_bash.py](/home/SFC/tanab/github/izanagi/.claude/worktrees/pegasus-fb/hooks/guard_bash.py:387)
  - `-mpytest`、`-mtools...`、`-qmpytest`、`-qm pytest`、`-Om pytest` を解析。
  - 分離形 `-m pytest` と exact sanctioned module の挙動を維持。
  - `-Wmodule`、`-Xmodule`、`python3 -c` 内の `m` は誤認しない。
  - shell の単一ハイフン短 option 群に `c` が含まれれば、次 token を command string として深さ 2 まで再帰。
- [test_hooks.py](/home/SFC/tanab/github/izanagi/.claude/worktrees/pegasus-fb/orchestrator/tests/test_hooks.py:504)
  - 新しい拒否形、非実行・sanctioned 許可形、既存分離形、`-c` のない script 実行を固定。
  - `site=None` / `OTHER` では新しい入力も従来どおり許可。
  - `_MENTION_RE` / `_LEAF_RE` / `_TREE_LITERAL_RE` / `_BUILDERS` / `_INTERP` / `_PURE_READERS` は未変更。

規則エラー時は `main()` 外周が例外を吸収し、防護対象を含まない通常操作は rc=0、防護対象を含む場合だけ rc=2 に倒れます。LOGIN の production `main()` 経由で `tools/run_tests.py`、`check_docs.py`、`git`、`codex exec`、`qsub`、`rg`、`cat` の許可をテスト固定しました。

検査結果:

- `python3 -m py_compile hooks/guard_bash.py orchestrator/tests/test_hooks.py`: rc=0
- `python3 -m pytest orchestrator/tests/test_hooks.py -q -rs`: **50 passed, 1 skipped**
  - 範囲: 同ファイルの全 nodeid
  - skip: 既存 `test_real_submodule_payload_edit`（submodule 未 init）
  - 主な nodeid:
    - `test_bash_login_blocks_attached_and_bundled_python_modules`
    - `test_bash_login_python_module_option_boundaries_allowed`
    - `test_bash_login_recurses_into_bundled_shell_command_options`
    - `test_bash_login_shell_without_command_option_stays_allowed`
    - `test_bash_other_keeps_legacy_acceptance_bits`
    - `test_bash_login_keeps_required_session_commands_available`
    - `test_bash_main_rule_error_is_scoped_to_protected_commands`
    - 既存の分離形・shell 再帰・module exact-path node
- 所有範囲の `git diff --check`: rc=0
- unstaged 差分は所有 2 ファイルのみ。

## 総括

- **FB-1: closed** — 密着・結合 Python `-m` の重量実行を拒否し、分離形、非実行形、sanctioned exact module は許可。
- **FB-2: closed** — `bash -xec` / `sh -euxc` 等を拒否し、`-c` のない `bash script.sh` 等は許可。再帰上限 2 は維持。
- 波及は LOGIN/SUSPECT の第二防壁に限定。OTHER/`site=None`、COMPUTE、既存防護パス判定、既知の script・変数展開等の限界は変更していません。