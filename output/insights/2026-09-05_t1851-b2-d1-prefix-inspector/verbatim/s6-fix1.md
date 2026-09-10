実装は完了しましたが、pytest は実行基盤の制約で開始できなかったため、全所見を `partial（実装済み・未実走）` とします。

| 所見 | 状態 | 対応 |
|---|---|---|
| F1 | partial | 同一 shared root に production API で A/B 世代を作り、B proof と外部 A の拒否、A/A の正例を real inspector で追加 |
| F2 | partial | 手書き validator を除去。production validator の spy 2 回、正常 proof、bool N、zero head、wrong schema を検査 |
| F3 | partial | 不変 pin node を base と完全一致へ復元し、v4/v5 schema assertion を新規 node へ移動 |
| F4 | partial | 合成 v1 を production scheduler authority で生成し、後段 replay 成功を直接確認する構成へ変更 |
| F5 | partial | v4 node に None を通す validator seam を追加。別 v5 node で seam 到達正例を追加 |
| F6 | partial | 対象負例を診断 node、reason 順序 pin、変異観測外と明記 |
| F7 | partial | literal、digest 4 種、row_count を区別する parametrize ID を追加 |

変更箇所は [test_s8b_floor_stats.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/t1851-b2-d1-fix1/orchestrator/tests/test_s8b_floor_stats.py:663)、[test_s8b_floor_contract.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/t1851-b2-d1-fix1/orchestrator/tests/test_s8b_floor_contract.py:187)、[test_s8b_attempt_registry.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/t1851-b2-d1-fix1/orchestrator/tests/test_s8b_attempt_registry.py:3455)、[test_attempt_registry_core_s8b_profile.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/t1851-b2-d1-fix1/orchestrator/tests/test_attempt_registry_core_s8b_profile.py:2483) です。

静的検査は次を確認済みです。

- 4 ファイルの AST parse 成功
- `git diff --check` 成功
- F3 の不変 pin node は `50dbf9158` と完全一致
- production 4 ファイルの差分 SHA-256 は統合 patch と一致
- docs、commit、production の追加変更なし

pytest runner は 3 回試行しましたが、local admission は別 scope の 4,114,160,440 byte 予約により拒否され、compute dispatch は sandbox 内の `qstat -Q` socket エラーで `rc=16`、child 未起動でした。実走 node は 0 件です。

## 総括

- F1〜F7: すべて partial（実装済み・未実走）、regressed 判定なし。
- fix1 net 行数: floor_stats +206、floor_contract +3、attempt_registry +17、core_profile +9。
- 実走結果: 0 passed / 0 failed、runner rc=16、child_started=false。
- 静的検査: AST 4 files OK、diff check OK、不変 pin base 一致。
- production 変更が必要と判明した点: 静的確認範囲ではなし。