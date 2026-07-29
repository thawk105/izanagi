## 所見対応表

| 所見 | 判定 | 対応 |
|---|---|---|
| New-5 | closed | `--external-handoff` 指定時も worktree handoff 残置検査を必須化。正例 rc=0、残置負例 rc=1 を固定 |
| New-6 | closed | fresh の `symbolic-ref` decode 失敗を git 読み取り失敗として報告。detached HEAD 誤診を防止 |
| New-7 | closed | strict UTF-8 decode に変更し、`UnicodeDecodeError` を「非 UTF-8 成果物」の rc=1 理由へ変換 |

## 変更箇所

- [tools/check_wave_startup.py:93](/home/SFC/tanab/github/izanagi/.claude/worktrees/t153-author-b/tools/check_wave_startup.py:93): detached HEAD と git 読み取り失敗を分離
- [tools/check_wave_startup.py:243](/home/SFC/tanab/github/izanagi/.claude/worktrees/t153-author-b/tools/check_wave_startup.py:243): external handoff 指定時の残置検査を必須化
- [tools/check_codex_output.py:107](/home/SFC/tanab/github/izanagi/.claude/worktrees/t153-author-b/tools/check_codex_output.py:107): strict UTF-8 decode と例外理由化
- [test_check_wave_startup.py:181](/home/SFC/tanab/github/izanagi/.claude/worktrees/t153-author-b/orchestrator/tests/test_check_wave_startup.py:181): external handoff 正負例と P5
- [test_check_wave_startup.py:293](/home/SFC/tanab/github/izanagi/.claude/worktrees/t153-author-b/orchestrator/tests/test_check_wave_startup.py:293): symbolic-ref decode 回帰
- [test_check_codex_output.py:68](/home/SFC/tanab/github/izanagi/.claude/worktrees/t153-author-b/orchestrator/tests/test_check_codex_output.py:68): 非 UTF-8 負例と V16
- 両 checker を mode `100755` に変更し、直接 `--help` 実行成功

## 実行結果

- nodeid `orchestrator/tests/test_check_wave_startup.py`、`orchestrator/tests/test_check_codex_output.py`: **48 passed**
- nodeid `orchestrator/tests/test_plain_runner_coverage.py::test_every_test_file_is_self_runnable_or_allowlisted`: **1 passed**
- 次の追加 nodeid: **4 passed**

  - `test_check_wave_startup.py::test_external_handoff_accepts_existing_file_outside_repo`
  - `test_check_wave_startup.py::test_external_handoff_also_rejects_worktree_handoff_leftover`
  - `test_check_wave_startup.py::test_fresh_symbolic_ref_decode_error_is_git_failure_not_detached`
  - `test_check_codex_output.py::test_non_utf8_output_is_rejected`

- `python3 tools/check_codex_agents.py`: OK
- `python3 tools/check_docs.py`: 違反なし
- `git diff HEAD --check`: 違反なし

## V16 / P5 kill 対応

- **V16:** strict decode を `errors="replace"` に戻すと、非 UTF-8 payload が見出しを満たして rc=0 となり、負例が赤化。
- **P5:** 残置なし判定を恒偽化すると、外部 handoff 実在・残置なしの rc=0 正例が赤化。残置あり負例も rc=1 を固定。

## 総括

New-5/New-6/New-7 はすべて closed。期待赤なし、docs 編集・commit なし。変更は所有対象4ファイルのみです。