## 総括

候補を全撤回し、2ファイルとも `d85bbb21196f503440ef9641e3dec095e3b43844` のGit blobとbyte一致へ戻しました。

| 対象 | closed/partial/regressed | 対応 |
|---|---|---|
| `tools/pegasus/certify_calibration.sh` | closed | 並行copy候補を撤回し、起点の逐次処理へ復元 |
| `orchestrator/tests/test_pegasus_calibration_workload.py` | closed | 候補用test・補助変更を撤回し、既存期待・skipを完全復元 |

静的検算で両ファイルのblob一致、起点との差分空、作業ツリーの `git diff` 空（各rc=0）を確認しました。

3copy全成功後にpristine成功なら後段へ進み、copyまたはpristine失敗なら非0で停止する起点の挙動を維持。要求時間・timeout・標本設計・trace/perf・単独性も起点どおりです。所有外caller/consumerに対する候補由来の変更は全撤回されています。

テスト・計測は未実走です。docs・stage・commit・他ファイル変更・子agent起動は行っていません。既存の最大経路の不整合は未解決であり、今回closedとしたのは候補撤回のみです。