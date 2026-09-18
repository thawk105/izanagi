## 総括

[probe/t2774_probe.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2774-unit2-probe/probe/t2774_probe.py) を修正しました（655行、untracked）。

| 仕様 | 判定 | 対応 |
|---|---|---|
| 1 | closed | configure/build を独立化。pilot 全 argv 一致を確認。warm-up も同じ設定 |
| 2 | closed | bindings に configure_defines／全 configure argv を記録。既存 pairs 経路にも適用 |
| 3 | closed | arms-json／rounds を追加。組の必須・排他と JSON 検証 |
| 4 | closed | arm ごとの pin 解決・clean 検査・順次 patch 適用・各種 SHA256 記録 |
| 5 | closed | 回転順、通し ordinal、round／order、planned_runs。既存 pair を維持 |
| 6 | closed | witness=false では env 2項目・witness dir を生成しない |
| 7 | closed | witness／pin で discriminator を限定。対象外理由と manifest の arm pin を記録 |
| 8 | closed | 動的 arm 集計と2例を追加。既存10例の本体・期待値は不変 |
| 9 | closed | B2 を指定 summarize コマンドで再集計。両 arm とも **N/m/k = 14/14/0** |

検証結果：

- `selftest: PASS 12/12 cases`（rc=0）
- `ast.parse: PASS`
- pilot 全 configure argv 一致、helper import、回転順：PASS
- 模擬検査：run_one 7分岐、CLI 10例、build argv／timeout：PASS
- 変更していない診断 patch の `patch --dry-run`：rc=0

closed は実装・静的／模擬検査の完了を示します。**compute、実 build、benchmark、実 trace の verifier／discriminator は未実走**です。

runner SHA256：
`24e03cd15c8768e4f25aa076e0f965ac3aa592ab8761bfa71265317923c28d97`

書込みは runner と自分の scratch のみ。所有外への変更は無し。tracked 差分、patch 編集、文書作成、禁止された Git 操作はありません。
