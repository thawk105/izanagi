修正は `tools/t2273_replica_runner.py` のみです。

- `/scr` の書込み可否・node-local mount を確認し、未存在の `/scr/<user>` を 0700 で作成します。既存なら所有者・directory を確認します。
- 今回作成したユーザーディレクトリだけ、終了時に空なら削除。作成・削除の有無を `staging.json` に記録します。
- TMPDIR 継承、残骸掃除、quota 記録、clean 検査、pair 順序は維持しています。

pegasus02 で以下を実走し、すべて rc 0 でした。

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH="$PWD/tools:$PWD" python3 -B /tmp/t2273-r2-check.py
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH="$PWD/tools:$PWD" python3 -B /tmp/t2273-fix1-check.py
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH="$PWD/tools:$PWD" python3 -B /tmp/t2273-fix2-check.py
git diff --check
```

既存の正例・負例は期待値を変更せず通過。追加検査は作成・既存保持・書込み不可・不在・非 local・失敗時削除・非空時保持を確認しました。本番の判定処理と実 clone を使い、mount テキストだけを注入しています。

`git status --porcelain`：

```text
 M tools/t2273_replica_runner.py
```

## 総括

指定範囲の修正と合成検査を完了しました。
計算ノード本走は **実装済み・未実走** です。
worktree で `git add`・`git commit` は行っていません。