## 総括

[tools/test_t2737_live_probe.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2737-noninert-fix1/tools/test_t2737_live_probe.py) のみ変更しました。**実装済み・未実走**です。

| 状態 | 所見 |
|---|---|
| partial | `backoff=1` に変更。実build確認は親が実施 |
| partial | `Path(__file__).with_suffix('.json')` から指定5キーを取得。dispatch実走は未確認 |
| closed | 静的確認：98行、全12 assert保持、構文正常、`git diff --check` 成功 |
| regressed | 静的確認で検出なし。実走回帰は未判定 |

波及範囲：

- **caller**：親の変異harnessが外部probeと同stemのJSONを配置する必要があります。
- **meta-test**：テスト新設・改名なし。確認した収集・直列化設定に名指し参照なし。
- **共有fixture**：変更なし。揮発hash固定なし。
- **consumer**：phase1／S、旧新TU前処理へ共通のBACK_OFF=1が渡ります。既存d2pl・bomb・tpcc・IMPL別テスト処理を保持しました。

production受理／拒否、既存期待値は変更していません。docs編集・stage・commitも未実施です。pytest・buildは実走しておらず、緑の報告はありません。