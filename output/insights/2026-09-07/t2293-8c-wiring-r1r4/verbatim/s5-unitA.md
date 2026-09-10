## 実装

- lifecycle startを15キーのbaseと、`origin_run_plan_sha256`を加えた16キー形の2択へ変更しました。[trial_registry.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2293-unit-a/orchestrator/campaign/trial_registry.py:204)
- API、loader、terminal対応、acceptance snapshotの各層でorigin bindingとのiffを検査します。
- execution provenanceをv2のexact 8キーへ移行し、v1は負例以外に残していません。[reflux_result_evidence.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2293-unit-a/orchestrator/campaign/reflux_result_evidence.py:126)
- `campaign_run_identity`はident形の末尾8 hexを持つ安全なcampaign IDとして検証します。
- `RESULT_EVIDENCE_SCHEMA_VERSION`はv1、evidence refは2本のままです。
- fixtureと固定baselineをv2へ更新しました。
- originlessの非揮発構造検査を維持し、`campaign_runs`だけでは通常campaign chainを迂回できない負例を追加しました。
- 編集は指定された8ファイルだけです。docsとcommitは変更していません。

## 検査

- Python 7ファイルのAST解析、baseline JSON解析、全fixture baselineの独立再計算、`git diff --check`は通過しました。
- pytest runnerは4回起動を試みましたが、すべてrc=16、`child_started=false`でした。
- 最終指定範囲は所有4テストファイルと`test_plain_runner_coverage.py`です。実行nodeidは0件です。
- 原因は`qstat -Q`の`EACCTAUTH Unknown user-id`と、local予算台帳を安全に更新できないことです。テストの緑・赤は未観測です。

## 他単位への波及

- Unit Bの`p3_autonomous_workload_trial.py`は、origin時の`record_trial_start_once`へ実envelope digestを渡す必要があります。現状のcallerは未結線です。
- Unit Cの`reflux_formal_consumer.py`はv2の`campaign_run_identity`を物理identity比較へ使用する必要があります。
- `test_p3_autonomous_workload_trial.py`と`test_reflux_formal_consumer.py`にある旧`fixture-run-%04d`は、新fixtureの8 hex形との整合が必要です。
- 共有fixture利用側として、`test_reflux_origin_artifacts.py`、`test_reflux_origin_binding.py`、`test_reflux_origin_client.py`、`test_reflux_origin_topology.py`、`test_reflux_source_closure.py`にも回帰可能性があります。
- `p3_s4_loop_trigger_gating.py`には変更signatureの直接参照は見つかりませんでした。

## 総括

- R1の15/16キー契約、sha256検証、origin iffを実装しました。
- R3のexecution-provenance/v2 exact 8キーとv1拒否を実装しました。
- result-evidence/v1と2本のrefは不変です。
- originless bytesと非揮発field集合を変えない実装・検査を追加しました。
- 静的検査は通過しています。
- pytestは基盤rc=16で子が起動せず、実装済み・未実走です。
- test-levelの残る赤は未観測です。
- Unit Bのdigest writer結線とUnit Cのphysical identity consumer結線が必要です。