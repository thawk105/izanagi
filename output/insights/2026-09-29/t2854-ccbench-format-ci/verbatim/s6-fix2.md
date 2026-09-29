## 変更内容

[run_ci_build.sh](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2854-fmt-a/output/runs/t2854-fmt-ci/scripts/run_ci_build.sh) の全 `apptainer exec` に `--userns` を追加しました。拒否された `--env HOME=…` を外し、`--home "$work/home"` に変更しました。report には `apptainer_exec_mode: "--userns"` を記録します。preflight の出力ファイル保存と失敗時の rc=3 は維持しています。

## 実走した command と rc

- `bash -n output/runs/t2854-fmt-ci/scripts/run_ci_build.sh`: rc=0
- `hostname`: rc=0、`pegasus02`
- 指定された一時ディレクトリでの `apptainer exec --userns --cleanenv --containall --home … --bind … <sif> g++ --version`: rc=255。出力は `FATAL: socket communication error: file file+net unix: getsockopt: operation not permitted`
- `rmdir` による一時ディレクトリ削除: rc=0

## 未実走・残る懸念

login での指定 probe が失敗したため、指示どおりそこで停止しました。失敗原因は特定していません。計算ノードでの本走は**実装済み・未実走**です。

## 総括

起動方式の修正と構文検査は完了しました。login の `--userns` 実走は rc=255 で、動作確認は通過していません。