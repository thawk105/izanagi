## 総括

1. 変更した 3 箇所

   - [tools/check_docs.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-dangling-audit-offrepo-authority/tools/check_docs.py:403) の `CLEANUP_COMMAND_SHA256`
   - [test_check_docs.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-dangling-audit-offrepo-authority/orchestrator/tests/test_check_docs.py:264) の `_EXPECTED_CLEANUP_COMMAND_SHA256`
   - 同ファイルの `_SYNTHETIC_CLEANUP_COMMAND` を現 command と完全同期

2. SHA-256 確認

   - command: 3924 bytes
   - synthetic literal: 3924 bytes
   - SHA-256: `5d0087f8f5dd69e248589bbd8df84ba428cd6383868e6057e1bfb4b9b516586a`
   - 書き込み前後とも提示値と一致
   - 書き込み後の byte 完全一致: `True`

3. 検査結果

   - `python3 tools/check_docs.py`: rc=0、`check_docs: 違反なし`
   - `git diff --check`: 合格
   - 焦点 pytest 2件: dispatch preflight が `qstat -Q` rc=1、runner rc=16 で未起動。**実装済み・未実走**であり、緑は主張しません。
   - docs 編集・commit・その他の git 状態変更は行っていません。