## 総括

- verifier 発行・PID/process seal 付き capability と、ledger 単位で一回限りの COMMIT receipt を実装した。
- production producer 5 件を、`wal.append` と qualification sink の2支配点へ配線した。
- pytest は正規 runner の Pegasus dispatch failure (`rc=16`) により未実走。実装済み・未実走であり、closed ではない。
- docs・単位A所有ファイルは変更せず、commit も作成していない。

## 変更点 (file:line)

- [commit_receipt.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1286-commit-receipt/orchestrator/verifier/commit_receipt.py:92)
  - verifier capability、receipt schema、payload/lock/variant binding、replay evidence、receipt ID を実装。
- [core.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1286-commit-receipt/orchestrator/verifier/core.py:160)
  - 実検証と同じ entrypoint 呼び出しから capability を発行。
- [wal.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1286-commit-receipt/orchestrator/campaign/wal.py:386)
  - flock 下で既存 receipt ID を走査し、最初の write 前に live receipt を検証。
  - [内部 recovery writer](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1286-commit-receipt/orchestrator/campaign/wal.py:1401) は `STAGE_ABORT` 以外を runtime 拒否。
- [pipeline.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1286-commit-receipt/orchestrator/campaign/pipeline.py:1247)
  - 全 verifier pass の capability から4 producer用 receiptを発行。
- [replay.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1286-commit-receipt/orchestrator/campaign/replay.py:179)・[guided.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1286-commit-receipt/orchestrator/campaign/guided.py:135)
  - source receipt/evidenceを保持し、destination lockへ再束縛。bare `certified=True` を拒否。
- [artifacts.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1286-commit-receipt/orchestrator/qualification/artifacts.py:772)
  - qualification ledgerのread→receipt検証→appendをflock内へ統合。
  - [schema](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1286-commit-receipt/orchestrator/qualification/t126_evaluation_event_schema.json:74) と [validator](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1286-commit-receipt/orchestrator/qualification/artifacts.py:953) も更新。
- [test support](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1286-commit-receipt/orchestrator/tests/commit_receipt_support.py:44)
  - post-policy receipt helperとlegacy raw writerを分離。
- [専用テスト](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1286-commit-receipt/orchestrator/tests/test_t1286_commit_receipt.py:110)
  - 自走 harness付きで追加。既存 `len==2` / `len==4` assertionは不変更。

## 負の対照

専用テストには以下を追加したが、pytestとしては未実走。

- v1 WALへreceiptなし／serialized dictのみで直接appendし、bytes不変。
- qualification実sinkへreceiptなし／serialized dictのみでemitし、bytes不変。
- 同一receiptの二回目、lock差し替え、payload変更を拒否。
- empty traceの`certified=false`とwrite-skewのnon-serializable結果から発行を拒否。
- `_append_records_locked`へのCOMMITを拒否。
- bare `GenomeResult(certified=True)`を拒否。
- exact `CertifiedCampaignView`のreceiptless source recordを実`load_landscape`経路から流した`cmd_evaluate`を拒否。
- 正常COMMIT、legacy receiptless replay/recovery byte不変、fork後のprocess seal再利用拒否、production producer exact 5件を収録。

## 現行挙動と変更後の受理集合

従来は構文上有効なCOMMITなら、verifier判定・lock identity・一回性と無関係に両sinkが受理していた。

変更後、新規COMMITは同一processのverifier entrypointが発行したlive capabilityから作られ、sink・raw lock SHA-256・variant・terminal payloadが一致し、同一ledgerでreceipt IDが未使用の場合だけ受理する。非COMMITの受理集合と`parse_line`は維持した。

既存receiptless WALはread/replay/recovery可能なままである。別layoutへのreceipt再利用はledger単位裁定のscope外であり、閉じたとは主張しない。

## 波及可能性

所有外のreceiptless callerとして静的に確認したもの：

- `test_artifact_admission.py`
- `test_screening_driver.py`
- `test_s8b_oracle_report.py`
- `test_backoff_consumers.py`
- `test_campaign_lock_wal_consumers.py`
- `test_s8b_oracle_driver.py`
- `test_s6_sort_sweep.py`
- `test_s1_report.py`
- `test_p3_s4_loop.py`
- `test_s8a_trigger_sweep.py`

qualification schema/constructor/validatorの共有fixtureでは、`test_t126_qualification_artifacts.py`、`test_t126_qualification_driver.py`、`test_t126_pegasus_tools.py`への更新波及が見込まれる。receipt issuerをenforcement source closureへ追加する作業は単位C所有面であり、本差分には含めていない。

## 未実走・未解決

実行要求範囲は `orchestrator/tests/test_t1286_commit_receipt.py -q`。`python3 tools/run_tests.py`で2回試行したが、いずれも `qstat -Q preflight rc=1`、dispatch infrastructure failure `rc=16`となり、pytest nodeidは1件も実行されていない。

実走済みの静的検査は、変更production/testの`py_compile`、schemaの`json.tool`、module import smoke、`git diff --check`で、すべて成功した。所有外fixtureの移行とpytest実測が残る。