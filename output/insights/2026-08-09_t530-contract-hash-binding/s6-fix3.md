修正は [test_autonomous_trial_completeness.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t530-contract-hash-binding/orchestrator/tests/test_autonomous_trial_completeness.py:137) のみです。

| 分類 | 対象 | 結果 |
|---|---|---|
| closed | `ycsb-a` の失敗 | `A.env_contract` 由来へ統一 |
| closed | `ycsb-b` の失敗 | 同上 |
| closed | `ycsb-c` の失敗 | 同上 |
| partial | pytest による確認 | 指示どおり未実走 |
| regressed | 静的確認範囲 | なし |

静的確認範囲:

- 対象ファイルの `A._campaign_for`：contract、build context、`GeneratorId`、identity helper を `A` namespace に統一。
- 同ファイルの Layer3 fixture：contract、`CampaignConfig`、`Genome`、`SourceEvidence`、policy を `orchestrator.campaign` namespace 内で統一。
- `A.run_trial` 全5呼出し：外部 namespace の exact 型オブジェクト注入なし。
- 前巡までの変更対象：`test_p3_autonomous_workload_trial.py`、`test_campaign.py`、`test_p3_s4_loop_trigger_gating.py`、`test_s8a_trigger_sweep.py`、`test_critic.py`、`test_guided.py`、`test_p3_exploration_namespace.py`、`test_screening_driver.py`。
- 上記の contract、build context、policy、genome の生成元と受取側 module identity が一致することを確認。
- `git diff --check` 成功。

## 総括

実装済み・未実走です。  
production の exact 型検査は変更していません。  
期待値、skip、docs は変更していません。  
commit は作成していません。