## 総括

実装済み・未実走。所有ファイルの2リテラルだけを更新しました。

- [3385行](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2724-t080-recovery-pin/orchestrator/tests/test_ccbench_spawn_sites.py:3385)：`1788 → 1794`（`injected-evaluate_fn`）。
- [3463行](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2724-t080-recovery-pin/orchestrator/tests/test_ccbench_spawn_sites.py:3463)：`1775 → 1781`（`campaign`）。

親統合木の `run_block` を読み、実位置と両呼出しASTの一致を確認しました。既存kind・期待件数・他wave追加は維持しています。

既存メタテストの未被覆sink拒否、未登録sinkの延期禁止、sinkごとのgate要求を静的確認しました。pytestは未実走で、親統合後の正規runnerによる検証が必要です。

所有外への波及：参照先は `s8b_oracle_driver.py`。共有fixture変更なし。`orchestrator`・`tools` のPython検索では外部consumer参照なし。docs・親木への書込み、Git操作、報告artifact作成はありません。