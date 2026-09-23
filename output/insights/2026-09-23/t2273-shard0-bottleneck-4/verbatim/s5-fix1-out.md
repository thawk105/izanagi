修正完了です。変更は [runner](/work/1/SFC/tanab/izanagi/.claude/worktrees/author-t2273-probe/tools/t2273_replica_runner.py) のみです。

- staging を `/scr/<user>` 配下へ変更。利用不可なら X を止め、`incomplete.json` を記録します。TMPDIR は維持し、staged repo は成功・失敗時とも削除します。
- A2・X 前に、子走の前後差分から登録した残骸を削除します。開始時のパスを保護し、UID・inode を照合。削除件数・bytes を記録します。
- 各走・staging 前後に quota と statvfs、staging の配置先・mount・filesystem を記録します。
- plugin・analyzer は変更していません。新しい staging 欄は既存の全体表示に含まれます。

pegasus02 で以下を実走し、いずれも rc 0 でした。

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH="$PWD/tools:$PWD" python3 -B /tmp/t2273-r2-check.py
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH="$PWD/tools:$PWD" python3 -B /tmp/t2273-fix1-check.py
git diff --check
```

既存の正例・負例は期待値を変更せず通過。追加検査では、既存物・未帰属物・差し替えパス・symlink 参照先の保護、smoke/A2 残骸の削除と件数・bytes、`/scr` 不在時の停止、`/tmp` fallback 拒否を確認しました。別途、小さい実 git repo で clone 後の失敗時削除も確認しました。

`git status --porcelain`：

```text
 M tools/t2273_replica_runner.py
```

## 総括

指定範囲の修正と login 合成検査を完了しました。
計算ノード本走は **実装済み・未実走** です。
worktree での `git add`・`git commit` は行っていません。