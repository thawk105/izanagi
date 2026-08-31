## 総括

共通 persisted COMMIT helper と CERTIFIED_ACCEPTANCE chokepoint 結線を実装した。  
受理集合は、全 COMMIT が同 attempt の正常 verify と有効 receipt を持つ集合へ縮小した。  
指定 fixture と M1〜M6・M10〜M13 の正負テストを追随した。  
pytest は Pegasus dispatch 障害で未実走。commit は作成していない。

## 現行の受理・拒否挙動 (変更前)

変更前は E1、epoch、attempt topology、contract binding が通れば、COMMIT に同 attempt の正常な `verify_done` がなくても、また receipt が不完全・不整合でも CERTIFIED_ACCEPTANCE view を発行し得た。

`_claims_certified_execution()` は v1 downgrade 検知用の保守的な claim 判定であり、意味は変更していない。

変更後は次を追加で拒否する。

- COMMIT 前に同一 variant・attempt の verify がない。
- verdict、certified、anomalies、workload tag が不正。
- receipt が実 lock SHA、variant、terminal payload に束縛されていない。
- receipt operation が COMMIT attempt と異なる。
- receipt evidence 列が WAL verify 列と異なる。

HISTORICAL_RAW、COMMIT のない campaign、COMMIT されず ABORT した赤 attempt は影響を受けない。

## 実装した内容 (file:line)

- [artifact_admission.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2061-wal-admission/orchestrator/campaign/artifact_admission.py:640)
  - immutable JSON を dict/list に戻す内部変換を追加。
  - `require_persisted_certified_commit()` を追加。
  - `CommitReceiptError` を cause 付き `ArtifactAdmissionError` に変換。
- [artifact_admission.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2061-wal-admission/orchestrator/campaign/artifact_admission.py:1261)
  - epoch gate 後、view 発行前に CERTIFIED_ACCEPTANCE の全 COMMIT を検査。
- [test_artifact_admission.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2061-wal-admission/orchestrator/tests/test_artifact_admission.py:414)
  - `_new_schema_campaign()` を正常 verify と正式発行 receipt 付き COMMIT へ更新。
  - raw record と immutable record の両入力を検査。
- [test_bench_first_real_wal.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2061-wal-admission/orchestrator/tests/test_bench_first_real_wal.py:160)
  - E1 化後の実 WAL fixture に、実 lock に束縛した receipt を正式発行。
- [test_critic.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2061-wal-admission/orchestrator/tests/test_critic.py:593)
  - 正常 fixture と retry fixture に完全な verify を追加。
  - committed retry に verify がない正例を admission 拒否負例へ改名・変更。
- [test_s6_sort_sweep.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2061-wal-admission/orchestrator/tests/test_s6_sort_sweep.py:757) と [test_s8a_trigger_sweep.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2061-wal-admission/orchestrator/tests/test_s8a_trigger_sweep.py:970)
  - certified fixture に attempt-bound の正常 verify を追加。

## 削った述語と、削った理由

段 2 案から次を実装対象外にした。

- `commits > 0`
- `aborts >= 0`
- `commit_witness` の exact key、commit count 一致、batch count 0
- `workload` の exact key 集合
- `verify_configs` の順序保持 deduplicate 一致

いずれも D1246 の verdict・receipt 束縛には不要で、実行側の診断 schema を過剰に固定するため。live producer 側の既存 gate は変更していない。

## 追加したテスト (node id 一覧)

- `test_artifact_admission.py::test_persisted_commit_gate_rejects[anomalies-positive]`
- `test_artifact_admission.py::test_persisted_commit_gate_rejects[receipt-terminal-mismatch]`
- `test_artifact_admission.py::test_persisted_commit_gate_rejects[receipt-operation-mismatch]`
- `test_artifact_admission.py::test_persisted_commit_gate_rejects[receipt-evidence-mismatch]`
- `test_artifact_admission.py::test_persisted_commit_gate_rejects[verify-attempt-mismatch]`
- `test_artifact_admission.py::test_certified_view_checks_every_commit[second-commit-invalid]`
- `test_artifact_admission.py::test_persisted_commit_gate_accepts[aborted-red-attempt-coexists]`
- `test_artifact_admission.py::test_persisted_commit_gate_accepts[no-commit-campaign]`
- `test_artifact_admission.py::test_persisted_commit_gate_accepts[nonzero-aborts]`
- `test_artifact_admission.py::test_historical_raw_unaffected[incomplete-receipt]`
- `test_artifact_admission.py::test_persisted_commit_helper_accepts_immutable_view`
- `test_critic.py::test_admission_rejects_committed_retry_attempt_without_verify`

## 変異の単一理由性の確認結果 (M1-M13 各々)

- M1: topology と receipt は anomalies を検査しない。helper の exact int zero 判定だけが拒否理由。
- M2: 通常 v2 topology は durable receipt terminal hash を再検査しない。既存 validator 呼び出しだけが拒否理由。
- M3: validator は operation を非空文字列として受理する。COMMIT attempt との一致判定だけが拒否理由。
- M4: WAL tag と `verify_configs` はともに `s2` で整合し、receipt 自体も `legacy` evidence として有効。evidence 列比較だけが拒否理由。
- M5: attempt A を verify 後 ABORT、attempt B を verify なし COMMIT とした topology-valid 入力。同 attempt verify 選択だけが拒否理由。
- M6: 2 attempt と両 receipt は topology-valid。第二 COMMIT の anomalies を検査する全 COMMIT loop だけが拒否理由。
- M7〜M9: author 単位 2 の所有範囲であり、本単位では未実装・未確認。
- M10: 赤 verify は ABORT attempt に属し COMMIT と無関係。campaign 全 verify を走査する過剰強化だけが拒否する。
- M11: topology-valid な COMMIT なし campaign。COMMIT 必須への過剰強化だけが拒否する。
- M12: HISTORICAL_RAW では helper を呼ばず、通常 v2 topology も receipt 完全性を検査しない。
- M13: `aborts=17` は topology と receipt schema の対象外。`aborts == 0` への過剰強化だけが拒否する。

## 実走した pytest の nodeid と結果

実走できた pytest node は 0 件。

`tools/run_tests.py` 経由で対象 node 群と全変更 test file、制約 meta-test を起動したが、どちらも `qstat -Q preflight rc=1`、child 未起動、runner rc=16 だった。テスト結果を緑とは扱っていない。

## 未実走・未完の範囲

実装済み・未実走:

- `test_artifact_admission.py` 全体
- `test_bench_first_real_wal.py` 全体
- `test_critic.py` 全体
- `test_s6_sort_sweep.py` 全体
- `test_s8a_trigger_sweep.py` 全体
- `test_plain_runner_coverage.py`
- `test_campaign_import_invariant.py`
- `test_acceptance_schedule_order.py::test_g5_real_ledger_covers_at_least_90_percent_of_real_collection`

静的には AST 構文解析、runtime import、`git diff --check` が成功した。変更は指定された 6 path のみ。author 単位 2 の raw consumer 結線は未実装であり、本単位だけでは land 不可。

## 所有外への波及可能性 (静的列挙)

中央 chokepoint 経由の既存 consumer 16 module・22 siteすべてで、保存 COMMIT の新 gate が発火する。主な対象は critic digest、S6、S8A、replay、layer3、backoff report 群、P3 loop 群、autonomous completeness、P3 red。

author 単位 2 で別途結線が必要:

- `backoff_requested_us.py`
- `s1_report.py`
- `s8b_oracle_report.py`
- `s6_sort_sweep.py::_replay_outcome`
- `s8a_trigger_sweep.py::_replay_outcome`
- `backoff_repro.py::_bench_tps`
- `paper_story_a2_certification.py::_raw_cell_from_wal`

追随候補:

- `test_s1_report.py`
- `test_s8b_oracle_report.py`
- `test_backoff_consumers.py`
- `test_backoff_requested_us.py`
- `test_paper_story_a2_certification.py`
- S8B oracle manifest の source hash と独立 golden
- 改名した critic node を保持する `acceptance_duration_ledger.json`

`commit_receipt_support.py` の legacy 負例 helper は変更していない。