実装は完了しました。recorded/current blob map 比較だけを撤去し、他の受理条件は維持しています。

### 変更内容

- committed closure A/B mismatch:
  - 変更前: `E1-stale / recorded-current-closure-mismatch` で拒否
  - 変更後: exact `CertifiedCampaignView`、`E1 / recorded-closure` で受理
- uncommitted drift:
  - 従来どおり `current-closure-unavailable` で拒否
- `HistoricalCampaignView`:
  - read-only `verifier_assessment_basis`
  - exact 値 `recorded-at-original-verifier-epoch`
  - certified view には存在しない
- historical marker を Layer3、P2-2、critic/online digest、backoff provenance、S1 9-pair provenanceへ伝播
- Layer3 schema:
  - marker 無しの旧 historical v3 を受理
  - marker ありの `certifying_input=true` を拒否
  - legacy `recorded-current-closure-mismatch` enum を維持
- recorded commit blob/digest 束縛、purpose 必須性、view 型分離、legacy oracle reader は変更していません。

編集した production path:

- [artifact_admission.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2008-d1163-author/orchestrator/campaign/artifact_admission.py)
- [layer3_report.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2008-d1163-author/orchestrator/campaign/layer3_report.py)
- [layer3_schema.json](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2008-d1163-author/orchestrator/campaign/layer3_schema.json)
- [p2_2_report.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2008-d1163-author/orchestrator/campaign/p2_2_report.py)
- [digest.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2008-d1163-author/orchestrator/critic/digest.py)
- [plot_backoff.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2008-d1163-author/tools/plotting/plot_backoff.py)
- [plot_s1_9pair.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2008-d1163-author/tools/plotting/plot_s1_9pair.py)

編集した test path:

- `test_artifact_admission.py`
- `test_layer3_report.py`
- `test_bench_first_real_wal.py`
- `test_critic.py`
- `test_plot_backoff_ci.py`
- `test_s1_9pair_figure_provenance.py`

所有一覧外への追記はありません。既存 mismatch/drift node 名と S1 self-test 名集合も維持しています。

### 検査結果

静的検査はすべて成功しました。

- 変更 Python 12 fileの `py_compile`: rc=0
- Layer3 schema JSON parse: rc=0
- `Draft7Validator.check_schema`: rc=0
- `git diff --check`: rc=0
- production の旧 mismatch literalは、指定どおり dataclass/schema/oracle legacy reader の3面だけに残存

pytest は実走できませんでした。`tools/run_tests.py` で以下を含む焦点集合、単独 mismatch node、collect-onlyを試行しましたが、すべて `child_started=false`, rc=16でした。

- `test_certified_acceptance_rejects_e1_stale_exact_map_mismatch`
- `test_certified_acceptance_rejects_each_verifier_drift_fail_closed` 全7 parameter
- `test_certified_acceptance_distinguishes_current_closure_unavailable`
- historical 5 producer検査
- Layer3 schema正負境界
- legacy dataclass/schema/oracle検査

原因はPegasus loginの最低1 GiB予約に対するheadroom不足と、compute dispatchの `qstat -Q` preflight rc=1です。pytest nodeの実走数は0であり、緑とは報告しません。生成されたdispatch receiptは除去済みです。

未実走範囲は、上記焦点node、D1163の保持検査、変異1〜8、変更test module全走、親の受入全走です。

### 波及候補

別裁定候補として残るのは以下です。

- `current-closure-unavailable` の撤去
- persisted WAL共通 certification gate
- `_CERTIFIED_VIEW_TOKEN` の capability強化
- D956/D967の後継supersession
- external official 5 campaignの親環境での受理実測

docs、output、凍結artifact/campaign/figure bytesは編集せず、commitも作成していません。

## 総括

T-2008のplan v2を所有範囲内で実装しました。committed closure mismatchはcertified受理へ反転し、uncommitted drift拒否と全束縛検査を維持しています。historical markerは5 producerへ伝播し、Layer3のlegacy互換・certified禁止境界も追加済みです。残件はPegasus環境障害で未実走となったpytestと親受入全走です。
