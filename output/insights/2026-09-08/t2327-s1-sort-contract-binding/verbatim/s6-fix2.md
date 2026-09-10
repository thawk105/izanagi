変更したファイル:

- [test_s8b_floor_campaign.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2327-fix2/orchestrator/tests/test_s8b_floor_campaign.py:2741)
  - L2741、L2742の参照を `configuration` から `configuration_id` へ修正。
  - `prepare` double の `cell["configuration"]` は変更なし。

`python3 -m py_compile orchestrator/tests/test_s8b_floor_campaign.py` は成功しました。

## 総括

実装済み・未実走です。  
production code、期待値、その他のテスト行は変更していません。