## 総括

変更は [probe-t2802/run-measure.sh](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2802-unit-probe/probe-t2802/run-measure.sh:104) のみです。

- 104〜122行: HEAD/clean/diff 照合を loop 内へ移動し、直後に `gate_open` を追加。閉じていれば RUN dir を作らず `stable=0` で戻ります。`GATE_MAX_ROUNDS` は共有し、再照合も行います。
- 117〜118行: 最終判定の値を `LEADERS` / `L1` に保存。投入時の再計数を削除しました。
- 最終判定も gate.log に残ります。既存の abort 経路と run.json の field・意味は維持しました。

検査結果:
- `bash -n probe-t2802/run-measure.sh`: rc=0。
- JOBDIR のみ一時空ディレクトリへ差し替えたメモリ上のスクリプトで、引数不足・tips 不在を確認。ともに rc=2、`runs/` を含め出力作成なし。

測定走の起動、docs 編集、commit・git 操作は行っていません。