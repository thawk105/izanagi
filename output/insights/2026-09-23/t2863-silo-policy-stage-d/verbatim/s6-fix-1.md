`aggregate` に、初走・再測すべての固定 workload と、abort0 の本文 hash、stock／B0-L-W0 の genome flags の照合を追加しました。不一致は error と `binary: null` になります。受理・拒否テストを追加し、裁定で指定された投入スクリプトのテストを削除しました。

所有外への波及は、**`aggregate` が読む初走・再測 JSON の受理判定**です。`run`、計測経路、IR、coverage、docs は変更していません。

## 総括

- 変更: [集計コード](/work/1/SFC/tanab/izanagi/.claude/worktrees/t2863-fix-1/orchestrator/campaign/silo_policy_recon.py:204)と[テスト](/work/1/SFC/tanab/izanagi/.claude/worktrees/t2863-fix-1/orchestrator/tests/test_silo_policy_recon.py:153)のみ。
- 静的確認: `py_compile` と `git diff --check` は成功。
- 実走: なし。`tools/run_tests.py orchestrator/tests/test_silo_policy_recon.py -q` は PBS 事前確認で `rc=16` となり、テスト本体は未開始。
- **実装済み・未実走**。対象範囲は `orchestrator/tests/test_silo_policy_recon.py` 全体で、緑判定はまだありません。
- リスク: 追加した受理・拒否テストを実走で確認できていません。