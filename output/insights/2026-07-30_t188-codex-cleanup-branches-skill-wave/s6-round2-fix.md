focused re-review の accepted partial を修正しました。

- 指定H2専用の top-level block exact照合へ変更。list、paragraph、blockquote、indented code、H3、fenceを構造として区別します。
- fence openerをHTML commentより先に認識し、backtick/tilde info-string bypassを閉鎖しました。
- commandを1 block/IDへ再編し、`CB-C01`〜`CB-C11`で固定しました。
- negative registryを`CB-N01`〜`CB-N28`へ拡張し、全IDのexactly-once収載とneedle存在をmeta-testで固定しました。
- dev-wave/rulingsの受理集合は変更していません。

変更したのは [tools/check_docs.py](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-cleanup-branches-skill/tools/check_docs.py:149) と [test_check_docs.py](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-cleanup-branches-skill/orchestrator/tests/test_check_docs.py:2104) のみです。Skill/metadata、docs、wave artifacts、handoff、submoduleは編集していません。commit・push・cleanupも未実施です。

検査結果:

- `pytest -q orchestrator/tests/test_check_docs.py`: **184 passed**
- `quick_validate.py .agents/skills/cleanup-branches`: valid
- `python3 tools/check_docs.py`: 違反なし
- `python3 tools/check_codex_agents.py`: OK
- `py_compile`: success
- `git diff --check`: success

追加stable nodeは15件です。

- `test_command_docs_guard_positive_controls[CB-N17]`〜`[CB-N28]`: 12件
- `test_cleanup_command_exact_clause_controls[CB-C11]`: 1件
- Skill/command legal-rewrap nodes: 2件
- 既存registry meta-testも強化済みです。

波及先はcleanup checkerの2 caller、合成Skill/command fixture、mutation registry、standalone test runnerです。親の全suite、mutation本走、cached 4-file確認、provenance/commit検査を代替しません。

## 総括

- closed: finding 4・8のpartial
- partial: finding 9は裁定どおり親の本走前記録に残置
- regressed: なし
- 変更files: checker/testsの2件
- 検査: 全指定項目green、pytest 184件
- 追加stable node: 15件