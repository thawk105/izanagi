## 総括

実装は完了しました。docs・所有外ファイルは編集せず、commit も作成していません。

- manifest schema に required `spec_sha256` を追加し、builder 3 経路と approved builder へ伝播。
- `verify_manifest` と seal wrapper に default なしの required `approved_spec` を追加。
- approved spec の schedule、campaign、run contract、binding、reasons、generator versions、SHA-256 を manifest ID 検査前に完全照合。
- `ReviewedSpec.document` / `.schedule` を再帰 immutable 化し、raw bytes・pin・snapshot の再束縛を追加。
- `_validate_run_contract` は変更せず、generic builder の余剰 key 受理を維持。
- 共有 fixture factory、8 投影の metamorphic test、signature/consumer/durable-0 機械検査を追加。
- `PIN_GATE_SPEC_RAW` / `PIN_GATE_SPEC_SHA256` は未変更。

主な変更箇所:

- [s8b_oracle_manifest.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t804-spec-sha256/orchestrator/campaign/s8b_oracle_manifest.py:43)
- [s8b_oracle_spec.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t804-spec-sha256/orchestrator/campaign/s8b_oracle_spec.py:53)
- [共有 fixture](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t804-spec-sha256/orchestrator/tests/s8b_oracle_spec_fixture.py:17)
- [manifest tests](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t804-spec-sha256/orchestrator/tests/test_s8b_oracle_manifest.py:1434)
- [機械契約 tests](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t804-spec-sha256/orchestrator/tests/test_s8b_oracle_manifest_contract.py:82)

検査状況は「実装済み・pytest 未実走」です。以下の nodeid を `tools/run_tests.py` で起動しましたが、Pegasus の `qstat -Q` preflight が失敗し rc=16 で停止しました。

- `test_verify_manifest_accepts_exact_approved_spec_projection`
- `test_verify_manifest_rejects_one_spec_divergent_projection`
- `test_reviewed_spec_document_and_schedule_are_recursive_immutable`
- `test_generic_builder_still_accepts_run_contract_extra_key`

新設テストと meta-test `test_pytest_collection_config.py` の collect-only も同じ rc=16 で未実行です。緑は主張しません。`py_compile`、`git diff --check`、公開 signature の静的確認は成功しています。

事前指定した統合時の意図的な赤は次の2件です。xfail にはしていません。

- loader consumer pin: `s8b_oracle_judge.py` の `load_official_manifest` 利用待ち
- verifier caller pin: `s8b_oracle_judge.py` の `verify_manifest` 利用待ち

AST 棚卸しではこの2件以外の consumer 集合は一致しました。pytest 未実走のため、実テスト上の回帰有無は未確定です。

所有外への波及は、production の driver 2 caller、report 1 caller、および B 所有の driver/report/judge テスト helper 群です。B 実装後には共有 fixture の利用、judge の2 consumer 追加、最終 source bytes に対する親段での pin 更新が必要です。combined verdict 層と動的 `getattr` / 動的 import は今回の機械検査範囲外です。