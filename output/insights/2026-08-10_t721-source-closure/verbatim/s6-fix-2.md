FR-01: **closed（実装済み・未実走）**

現行挙動を実測し、2 path とも exact な `ArtifactAdmissionError("campaign requires a directory, campaign.lock, and WAL")` であることを確認しました。[test_artifact_admission.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t721-source-closure/orchestrator/tests/test_artifact_admission.py:762) に型・理由の完全一致検査を追加しています。

追加 nodeid（2件）:

- `...::test_existing_evidence_campaign_classification_exact_rejection[p3-t178-ycsb-a-workload-conditioned-autonomous-0a11751c]`
- `...::test_existing_evidence_campaign_classification_exact_rejection[p3-t178-ycsb-a-workload-conditioned-autonomous-9785aec6]`

落とす改変: evidence 2 path の入口拒否が classification 成功へ変わる、または例外型・理由が変わる改変。

テストは親 nodeid（2件）を指定しましたが、`qstat -Q` preflight 失敗で rc=16。実走 0 件です。`git diff --check` は成功しました。production/docs の変更、add、commit はありません。

## 総括

FR-01 はテスト追加により closed。  
既存の 32-lock census と 30 campaign mapping は維持。  
対象は指定されたテストファイルのみ。  
dispatch 不成立のため実装済み・未実走です。