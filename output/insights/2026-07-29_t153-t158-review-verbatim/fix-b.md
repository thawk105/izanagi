段 6 fix 実装子 B の担当範囲を完了しました。docs 編集・stage 更新・git commit は行っていません。

### 所見対応表

| 所見 | 状態 | 対応 |
|---|---|---|
| R1-4 | closed | marker を symlink 非許容 regular file に限定し、`.git` の実在・非 symlink も検査 |
| R1-5 | closed | `docs/handoff` symlink を拒否。regular file の `README.md` 以外をすべて残置扱い |
| R1-8 | closed | `os.open(O_RDONLY\|O_NOFOLLOW)` → `fstat(fd)` → 同一 fd から 10 MiB+1 読込へ変更 |
| R1-9 | closed | 4 種の GIT poison を注入し、子 env からの除去を検証 |
| R1-10 | closed | 上限テストを literal `10 * 1024 * 1024` に固定 |
| R1-12 | closed（B該当分） | `_git` の `UnicodeDecodeError` を是正案付き集約 failure に変換 |
| R2-6 | closed | `--forbid-worktree-handoff` へ改名。`--external-handoff PATH` の外部実在 file 検査を追加 |
| R2-7 | closed | `.git` 欠落・symlink の負例を追加 |
| R2-12 | closed | FIFO parameter に `hasattr(os, "mkfifo")` の `skipif` を追加 |

partial / regressed はありません。

### 変更箇所

- [tools/check_wave_startup.py](/home/SFC/tanab/github/izanagi/.claude/worktrees/t153-author-b/tools/check_wave_startup.py:32)
  - Git allowlist・decode failure: 32–65
  - submodule 実体検査: 134–157
  - worktree handoff: 160–191
  - external handoff: 194–221
  - CLI/wiring: 224–281
- [tools/check_codex_output.py](/home/SFC/tanab/github/izanagi/.claude/worktrees/t153-author-b/tools/check_codex_output.py:55)
  - bounded fd read: 55–64
  - `O_NOFOLLOW`、`fstat`、同一 fd 検査: 67–110
- [test_check_wave_startup.py](/home/SFC/tanab/github/izanagi/.claude/worktrees/t153-author-b/orchestrator/tests/test_check_wave_startup.py:118)
  - submodule/handoff/external handoff: 118–218
  - GIT poison: 223–258
  - decode failure: 268–281
- [test_check_codex_output.py](/home/SFC/tanab/github/izanagi/.claude/worktrees/t153-author-b/orchestrator/tests/test_check_codex_output.py:66)
  - FIFO skip: 66–90
  - V11・TOCTOU・growth・fail-closed: 93–149

### 実行 nodeid と結果

- `orchestrator/tests/test_check_wave_startup.py`
- `orchestrator/tests/test_check_codex_output.py`  
  結果: **45 passed**
- `orchestrator/tests/test_plain_runner_coverage.py::test_every_test_file_is_self_runnable_or_allowlisted`  
  結果: **1 passed**
- `python3 tools/check_codex_agents.py`: OK
- `python3 tools/check_docs.py`: 違反なし
- `git diff --check HEAD -- <所有4ファイル>`: 問題なし

### 波及静的列挙

- checker の consumer は各専用 test file のみ。
- 旧 `--expect-external-handoff` は repository 内 0 件。
- `_MAX_READ_BYTES` の参照は実装内部のみ。テストからの import なし。
- docs・製品コード・他 checker への変更なし。
- `git status` は所有4ファイルのみ `AM`。段5の staged 内容に対する今回の fix は unstaged のままです。

### 変異 kill 対応表

| 変異 | kill nodeid |
|---|---|
| V6 | `test_check_wave_startup.py::test_resume_rejects_invalid_submodule_marker[missing\|directory\|symlink]` |
| V7 | `test_check_wave_startup.py::test_fresh_rejects_dirty_tree` |
| V8 | `test_check_codex_output.py::test_small_fragment_is_rejected_even_with_heading` |
| V9 | `test_check_codex_output.py::test_fenced_heading_does_not_satisfy_requirement` |
| V11 | `test_check_codex_output.py::test_read_limit_rejects_file_larger_than_ten_megabytes` |
| V13 | `test_check_wave_startup.py::test_forbid_worktree_handoff_rejects_handoff_directory_symlink` |
| P3 | `test_check_codex_output.py::test_normal_output_is_accepted` |
| P4 | `test_check_wave_startup.py::test_fresh_normal_worktree_is_accepted` |
| P5 | `test_check_wave_startup.py::test_external_handoff_accepts_existing_file_outside_repo` |

## 総括

**GO（実装子 B 担当範囲）。期待赤・実測赤ともに 0 件です。**