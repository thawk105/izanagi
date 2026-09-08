## 変更した file と要点

- [backoff_extended_sweep.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2418-author/orchestrator/campaign/backoff_extended_sweep.py:81)
  - `t2418-explore`、5 genome、専用 identity/report/disclosure を追加。
  - T2418 の完全・相異 binary SHA 検査を追加。
  - 既存 1 か所の `run_campaign` 経路へ合流。

- [test_backoff_extended_sweep.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2418-author/orchestrator/tests/test_backoff_extended_sweep.py:504)
  - literal pin、完全 SHA、凍結 WAL view、report、CLI、PBS routing のテストを追加。
  - 既存テストの期待値は変更なし。

- [b10_backoff_grid.sh](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2418-author/tools/pegasus/b10_backoff_grid.sh:186)
  - 新 run kind、専用 stage、driver 引数、5 commit/report finalizer を追加。

- [submit_b10_backoff_grid.sh](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2418-author/tools/pegasus/submit_b10_backoff_grid.sh:6)
  - CLI 受理値と qsub 環境転送を追加。

変更はこの4ファイルだけです。commit/add は実行していません。

## 実装した要件 1〜7 の対応

1. `_require_distinct_t2418_binary_hashes` を追加。5 genome、完全な trace-disabled `BuildResult`、genome 束縛、完全 SHA256、5 SHA の相異性を fail-closed で検査します。正例・各異常系もテスト済みです。
2. `declared_use_class="official"`、`reps`、`extime_s`、`records`、`threads` を search config、JSON top-level、`.dat` provenance に同値で追加しました。
3. `5`、`3`、および `[(0,-1),(1,-1),(1,4000),(1,6000),(1,11999)]` を独立 literal で pin しました。
4. `artifact_admission._immutable_records` を実際に通し、tuple／`MappingProxyType` 化された WAL view から capture・loader・report を検査しました。
5. T2418 の凍結 campaign view が既存 T2266 loader に拒否される負テストを追加しました。
6. `run_campaign` 呼び出しは引き続き1か所です。
7. 候補集合から導く membership などの恒真 assertion は追加していません。

## 実走したテストと結果

- `PYTEST_ADDOPTS=-vv PYTHONPATH=. python3 orchestrator/tests/test_backoff_extended_sweep.py`
  - 範囲: `orchestrator/tests/test_backoff_extended_sweep.py::*`
  - 結果: **47 nodeid passed**
  - 新規 T2418 nodeid:
    - `test_t2418_exact_grid_identity_order_and_disclosure_are_literal_pinned`
    - `test_t2418_frozen_wal_view_flows_through_capture_loader_and_reports`
    - `test_t2418_frozen_campaign_is_rejected_by_existing_t2266_consumer`
    - `test_t2418_prebuild_requires_five_distinct_trace_disabled_binaries`
    - `test_t2418_binary_identity_rejects_incomplete_or_malformed_bindings`
    - `test_t2418_run_path_uses_exact_five_genomes_and_shared_campaign_call`
    - `test_t2418_cli_requires_exact_five_and_both_report_artifacts`
    - `test_b10_run_kind_routes_t2418_through_job_submit_and_finalizer`

- `bash -n < tools/pegasus/b10_backoff_grid.sh`: passed
- `bash -n < tools/pegasus/submit_b10_backoff_grid.sh`: passed
- `git diff --check -- <指定4ファイル>`: passed

## 実走できなかったもの

- `tools/run_tests.py`、直接の pytest、リポジトリ全体の test suite は指定された sandbox 制約により未実走です。
- `orchestrator/tests/test_campaign.py` の meta-test は未実走です。ただし対象 source を静的確認し、`run_campaign` 呼び出しがちょうど1か所であることを確認しました。
- PBS 投入、build、性能計測は未実走です。
- docs checker、Codex agent checker、provenance checker は単独段射影および commit 禁止に従い未実走です。

## 所有外の caller・共有 fixture・consumer test への波及可能性

- `RUN_KINDS` は三値になったため、同 tuple を利用する CLI parser は新値を受理します。
- PBS job／submitter 以外の caller は変更していません。
- 共有 fixture、新規 test file、受入台帳は変更していません。
- T2266 の定数、関数、schema、artifact stem、完全 SHA 経路は維持されています。
- 親側では `test_campaign.py` を含む全体テスト、docs・台帳更新、commit、投入証拠の取得が必要です。

## 現行の受理・拒否挙動と、変えた点

従来の `extended`／`t2266-tail` に加え、`t2418-explore` を明示指定した場合だけ新経路を受理します。

T2418 は次を満たさなければ拒否します。

- exact 5 genome
- trace-disabled build が全件存在
- genome と build の束縛が一致
- 完全 SHA256 が5つすべて相異
- correctness-verified の committed WAL が5点
- 各点5 rep
- 完走 summary が total=5、committed=5、aborted=0
- 専用 `.dat`／`.json` report が両方存在

探索標本は専用 run kind・campaign identity・schema・stem で分離され、`declared_use_class` は既存 sweep と同じ `"official"` のままです。T2418 view は既存 T2266 consumer に混入できません。

## 総括

D1813 の `t2418-explore` 実装を指定4ファイルへ限定して完了しました。対象 harness は47件すべて緑、shell構文も正常です。全体 suite と PBS 実測は未実走のため、現時点では `closed` とは申告しません。