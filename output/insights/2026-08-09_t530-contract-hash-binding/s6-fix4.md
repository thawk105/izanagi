C-01 の最小修正を実装しました。docs・commit・pytest は触れていません。

### 対応表

| 判定 | 所見 |
|---|---|
| closed | C-01（静的確認済み・未実走） |
| partial | なし |
| regressed | なし |

C-02・C-03 は変更していません。

### 実装内容

- [_prepare_campaign_identity](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t530-contract-hash-binding/orchestrator/campaign/p3_autonomous_workload_trial.py:610) を `site`・`contract` 必須引数化し、linux literal lookup を削除。
- workload 入口で site と contract を各1回だけ解決。
- 既存 `_SITE_ENV_TAGS`／`_campaign_cfg_for_site` を再利用し、Pegasus のみ `measurement_env=pegasus` を付与。
- identity・campaign_id・layout・既定 drive に同一 contract を伝播。
- [drive_iteration](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t530-contract-hash-binding/orchestrator/campaign/p3_s4_loop_trigger_gating.py:716) は内部注入時も site/env_tag 不一致を fail-closed で拒否。

受理・拒否挙動の変化:

- 正当な `PEGASUS_COMPUTE` は Pegasus H・campaign ID・layout のまま drive へ進める。
- `OTHER` は従来どおり linux H、`measurement_env` なし。
- T-276 transport admission、未知 site、layout 照合など既存拒否条件は緩和していない。
- 指示外の受理拡大・縮小はない。

### テスト

追加 nodeid:

- `test_p3_autonomous_workload_trial.py::test_pegasus_workload_identity_layout_and_drive_use_pegasus_contract`
- `test_p3_autonomous_workload_trial.py::test_other_workload_identity_layout_and_drive_use_linux_contract`

既存 nodeid の変更・削除はありません。歴史世代の campaign-id 定数も維持し、C-01 用定数を追加しました。

静的検査:

- `git diff --check`: 成功
- `py_compile`: 成功
- contract 必須化・linux literal 不在・workload 内 site/lookup 各1回: AST 確認成功
- pytest／受入検査: 指示どおり未実走

波及可能性:

- 所有外の `_prepare_campaign_identity` caller: 静的検索上なし。
- 共有 fixture `t325_registered_trial`: 歴史的 linux manifest を保つため `OTHER` を明示。
- consumer test: `test_p3_s4_loop_trigger_gating.py` の public fallback／AST pin。既存呼出しは既定経路を維持。
- custom drive fixture には新しい private keyword を渡さず、既存 seam を維持。

## 総括

- C-01 は実装上 closed。
- Pegasus identity・layout・drive を同一 Pegasus contract に統一。
- OTHER の従来挙動と歴史定数は維持。
- C-02・C-03、docs は未変更。
- commit は未作成。
- **実装済み・未実走。**