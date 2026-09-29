指定の 3 ファイルを修正しました。`run-acceptance-gated.sh`、docs、repo の既存実装ファイルは変更せず、git の add・commit も行っていません。

| 所見 | 状態 | 対応と根拠 |
|---|---|---|
| 1. shard の対応付け | closed | `command=` を JSON 配列として読み、正規化した tests path の完全一致で照合。[run-pair.sh](/work/1/SFC/tanab/izanagi/.claude/worktrees/acp-author/scratch-acp/run-pair.sh:112) |
| 2. 木と commit の証跡 | closed | 期待 commit を第 5 引数で受け、両 HEAD が不一致なら起動前に rc=3。record にも保存。fresh 木の作成証跡は親の log が担う。[run-pair.sh](/work/1/SFC/tanab/izanagi/.claude/worktrees/acp-author/scratch-acp/run-pair.sh:34) |
| 3. 実効 env | closed | 予定値での判定をやめ、3 shard の request 環境と終了後 pyc 数で K/H の無効条件を判定。[aggregate.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/acp-author/scratch-acp/aggregate.py:83) |
| 4. 対の重複・取り直し | closed | ID を `p1/p2/p1r/p2r` に限定し、重複は rc=2。各原対系列から有効な 1 対ずつ選択。[aggregate.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/acp-author/scratch-acp/aggregate.py:157) |
| 5. 出力先・pid | closed | 出力先が木の内側なら rc=2、pid は排他的に作成。[run-pair.sh](/work/1/SFC/tanab/izanagi/.claude/worktrees/acp-author/scratch-acp/run-pair.sh:8) |
| 6. 起動前のプロセス | closed | `pid,etime,args` の全行を保存し、該当行を record に列挙。[run-pair.sh](/work/1/SFC/tanab/izanagi/.claude/worktrees/acp-author/scratch-acp/run-pair.sh:42) |
| 7. 秒精度の境界 | closed | log mtime の ±1 秒以内を判定不能として H の支持判定から除外し、結果に表示。[aggregate.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/acp-author/scratch-acp/aggregate.py:46) |

差分は runner の起動前検査・記録、集計器の無効条件・総合判定、[SELFCHECK.md](/work/1/SFC/tanab/izanagi/.claude/worktrees/acp-author/scratch-acp/SELFCHECK.md:36) の検査記録です。`bash -n`、`py_compile`、`git diff --check` は成功。実物 shard を流用した模擬で W=366.649 秒、pre=129.503 秒、Δ=0 を確認し、H の request に `"1"` がある場合は invalid になりました。path の部分一致防止、期待 commit 不一致の rc=3、重複 ID と木内出力先の rc=2 も確認しました。一時ファイルは削除済みです。

## 総括

修正は完了しました。受入本走は実施しておらず、対照効果は未確認です。