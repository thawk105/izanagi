## 総括

- 1. 問題なし。両親の差分は合成後も各 patch-id が完全一致し、消失・改変ハンクはありません。
- wave 側の追加 81 行、main 側の `+197/-5` が双方そのまま保持されています。
- 2. 問題なし。構文木検査で重複定義、重複 import 束縛、同名 pytest fixture はすべて 0 件でした。
- 3. 問題なし。main 側の `_mock_pipeline`、`ScriptedPoint` などの変更は、追加 2 テストが利用する fixture/helper に影響しません。
- 対象テストは [test_campaign.py:4984](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-seam-checknet/orchestrator/tests/test_campaign.py:4984) と [test_campaign.py:5027](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-seam-checknet/orchestrator/tests/test_campaign.py:5027) です。
- 編集はしていません。`git diff --check --cached` も問題ありません。
- 2 nodeid の実走は標準 runner が `qstat -Q` 認証エラーで rc=16 となり、テスト本体は未実行です。
- 判定: 合成は正しい。