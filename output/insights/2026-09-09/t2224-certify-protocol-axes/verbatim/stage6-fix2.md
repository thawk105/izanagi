## 総括

指定された 2 ファイルだけを修正しました。docs の編集、commit、push、新規ファイルの残置はありません。既存の他 3 ファイルの差分には触れていません。

## 変更したハンク

- [tools/pegasus/certify_calibration.sh:589](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2224-fix2/tools/pegasus/certify_calibration.sh:589)
  - 変更前: case ラベル、`build_argv=`、`;;` が同一行。
  - 変更後: 各 protocol を複数行へ整形し、`build_argv=` を行内の先頭トークンに変更。
  - 理由: 字下げ対応の検査で全 3 分岐を確実に検出し、同一行の literal target も維持するため。

- [orchestrator/tests/test_pegasus_tools.py:523](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2224-fix2/orchestrator/tests/test_pegasus_tools.py:523)
  - 変更前: 両正規表現が `^([a-z_]+_argv)`、件数は `8`。
  - 変更後: 両方を `^[ \t]*([a-z_]+_argv)` に強化し、実測値 `10` に更新。3 protocol 分岐を理由とするコメントを追加。
  - 名前集合 assert、bare `cmake` の否定 assert は維持。

## 一致数の実測

字下げ許容の正規表現による一致は **10 件**です。

- `gflags_*_argv`: 3件
- `glog_*_argv`: 3件
- `configure_argv`: 1件
- `build_argv`: 3件（silo / mocc / tictoc）
- 字下げされた bare `cmake`: 0件

## silo の token 列が不変であることの確認

静的に確認しました。

- `configure_argv`: 今回変更なし。silo 用 define 6個を含む既存 token 列を維持。
- `build_argv`:  
  `$CMAKE_PATH | --build | $BUILD_DIR | --target | ycsb_silo.exe | -j | 48`  
  代入式内部は整形前と同一です。
- `calibrate_argv`: 今回変更なし。`env`、固定 PATH、calibrator、workload、binary、hash、receipt の既存 token 列を維持。
- `BINARY="$BUILD_DIR/cc/$CALIBRATION_PROTOCOL/${build_argv[4]}"` も変更なし。

## 実走した検査

- 字下げ許容正規表現: **10件**、bare `cmake`: **0件**
- `git diff --check`: 成功
- `python3 tools/check_codex_agents.py`: 成功
- `python3 tools/check_docs.py`: 成功
- `bash -n tools/pegasus/certify_calibration.sh`: PreToolUse hook が Pegasus 実行体の直接起動として拒否。迂回せず未実走。
- `python3 tools/run_tests.py orchestrator/tests/test_pegasus_tools.py`: `qstat -Q` preflight が `rc=1`、dispatcher は `rc=16`、`child_started=false`。**実装済み・未実走**。
- 失敗した dispatcher が生成した専用診断ディレクトリ内の4ファイルは、新規ファイル禁止を守るため除去済みです。再実行で再生成可能です。