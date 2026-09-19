## 総括

A1 の修正は完了しました。変更は指定の2ファイルのみです。

- `tools/dev_wave_cleanup.py:242,1564,1574–1575`：`check-attr --all` と属性名による判定へ変更。旧 allowlist を削除。
- `orchestrator/tests/test_dev_wave_cleanup.py:309–324`：`named-x`／`named-unspecified` を追加。後者は作業木だけに `secret=` 行を残し、clean status と rc20／`backup-precheck`、非変更を検査します。

`git diff --check` は成功しました。**直接呼出し3ケースと反実仮想は未実走**です。実行前に拒否されたため、一時的な検査無効化も行われていません。commit・報告ファイルは作成していません。

自動承認レビュー（PreToolUse `guard_bash`）が直接呼出し用コマンドを拒否しました。理由は「保護対象パスと不透明構文の同居により分類不能」です。このため、動作検証完了とは報告できません。