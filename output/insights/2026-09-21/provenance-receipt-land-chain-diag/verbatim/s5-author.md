## 総括

4本を作成しました。

- [receipt_ledger.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/pcd-unit-probe/build/probe/receipt_ledger.py)
- [receipt_reuse_replay.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/pcd-unit-probe/build/probe/receipt_reuse_replay.py)
- [audit_attempt_ledger.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/pcd-unit-probe/build/probe/audit_attempt_ledger.py)
- [launch-force-dispatch.sh](/work/1/SFC/tanab/izanagi/.codex/worktrees/pcd-unit-probe/build/probe/launch-force-dispatch.sh)

**CLI、A1〜A5対応、近似・制限、P-2/P-3のstdout全文を含む報告:** [自己実走総括](/work/1/SFC/tanab/izanagi/.codex/worktrees/pcd-unit-probe/build/probe/out/self-run-summary.md)

P-1は **499件／19 partition／読取エラー0件**。P-2は85件の候補分類を実走しました。P-3も実走済みです。P-4は `bash -n` 成功、実走なし。tracked file変更・commit・既存テスト実行はありません。

**未完了:** P-2の51件のprefix replay。指定されたregistry loaderが内部で使う `git ls-files` と `git ls-tree` が、依頼の許可コマンド一覧に含まれません。確認への回答が未着のため実行前に止め、「未判定」と保存しています。replay成功とは報告していません。