着手前の挙動: Request ID と3必須フィールドが揃えば、Group Name の欠落・不一致でも受理していました。

実装済み・未実走（closed ではありません）。

- `dispatch_compute.py` に Group Name の exact `SFC` 検査を追加。
- fixture、4拒否ケース、正例、tail保持確認を更新。
- 静的確認・manual smoke は pass。直接 caller は同ファイルの2箇所のみ。独立 consumer は scope 外で変更なし。
- 実走: `python3 tools/run_tests.py ... -q` → `rc=16`、`qstat -Q` の `EACCTAUTH` で子未開始。赤はテスト赤ではなく infrastructure failure。
- コミット・docs変更なし。

## 総括

変更は [dispatch_compute.py:144](/work/1/SFC/tanab/izanagi/.claude/worktrees/t222-scheduler-group/tools/pegasus/dispatch_compute.py:144)、[dispatch_compute.py:939](/work/1/SFC/tanab/izanagi/.claude/worktrees/t222-scheduler-group/tools/pegasus/dispatch_compute.py:939)、[test_pegasus_dispatch_compute.py:99](/work/1/SFC/tanab/izanagi/.claude/worktrees/t222-scheduler-group/orchestrator/tests/test_pegasus_dispatch_compute.py:99) ほか指定テストのみ。wrapper 実走は未成立。