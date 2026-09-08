## 実装した内容

- [reflux_result_evidence.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2437-unit-b/orchestrator/campaign/reflux_result_evidence.py:238)
  - 契約どおり `ResultEvidenceIssuanceContext`、`produce_ordered_wal_projection`、`issue_campaign_result_evidence` を追加。
  - `wal.ordered_attempt_frames()` の実 offset を再利用し、attempt 内の物理的な非連続を発行前に拒否。
  - terminal 時点の `wal.jsonl[0:byte_end]` を immutable prefix snapshot として保存。
  - source／projection／provenance を指定された content-addressed path に発行。
  - derive／provenance 検証／assemble／expected path 照合を全て memory 上で通した後、source → projection → provenance → record の順で発行。
  - create-only writer は `O_EXCL`、`O_NOFOLLOW`、全 bytes write、file／parent fsync、read-back exact 一致を満たす既存 primitive と `_ensure_parent_directories()` を再利用。`os.replace()` は不使用。
  - `execution_receipt=None` は `ResultEvidenceIssuanceRefused`。自己申告 digest は生成しない。
- [test_reflux_result_evidence.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2437-unit-b/orchestrator/tests/test_reflux_result_evidence.py:1081)
  - 指定された正例 2 件、負例 5 件を追加。
  - 実 `wal.log()`、実 verifier、実 issuer、実 `resolve_result_evidence()` を使用。
  - 拒否負例では発行前後の file snapshot が同一であることまで検査。

## 実走した検査

- 所有 test file 全体: `75 passed in 3.64s`
- 新規 node の JUnit 実測値:
  - `orchestrator/tests/test_reflux_result_evidence.py::test_campaign_producer_issues_real_wal_projection_and_resolves_interval` — 0.275s
  - `...::test_campaign_producer_preserves_nonzero_offset_for_second_attempt` — 0.412s
  - `...::test_campaign_producer_refuses_absent_execution_receipt_before_writes` — 0.148s
  - `...::test_campaign_producer_refuses_interleaved_attempt_before_writes` — 0.142s
  - `...::test_campaign_producer_refuses_nonexact_verify_result_before_writes` — 0.126s
  - `...::test_campaign_producer_treats_create_only_collision_as_failure` — 0.309s
  - `...::test_campaign_producer_snapshot_survives_append_while_live_ref_breaks` — 0.291s
- 制約 meta-test:
  - `test_plain_runner_coverage.py` 全 3 node — 3 passed
  - `test_consumer_source_has_no_nonaborted_construction_or_success_variant` — passed。exact 15-file 閉集合を維持。
- formal consumer 代表検査:
  - `test_exact_fixture_contract_reaches_only_p6_unavailable`
  - `test_synthetic_silo_source_producer_passes_formal_consumer_contract`
  - 上記と閉集合検査の計 3 node — 3 passed
- `py_compile`、`git diff --check` — passed
- 既存 file は pytest 専用 allowlist 対象で直接実行が no-op のため、`python3 -m pytest` は使わず Python 内の `pytest.main()` で実走。
- repository 全受入は未実走。

## 現行の受理・拒否挙動 (scope 前後)

scope 前は、既存 core が commit＋exact verifier order、または clean な exact `VerifyResult` と一致する単一 rejected witness class のみを受理していました。それ以外は発行拒否で、assembler は projection digest を束縛し、record issuer は参照先解決後に create-only 発行していました。

scope 後もこの受理集合は変更していません。新 producer はさらに、issued origin capability、execution receipt、物理的に連続した attempt、valid trigger binding、expected record path を要求します。consumer の判定式、reason code、3方向分岐は未変更です。

## 所有外 caller・共有 fixture・consumer test への波及 (静的列挙)

- 現時点の production caller は 0 件。単位 C の `loop.py` が固定 signature で呼び出す必要があります。
- 単位 A の `EvalResult` は import していません。`verify_result` と `build_attempt_id` は引数のみです。
- 共有 fixture と既存期待値は変更不要で、既存 68 node は継続して緑です。
- `reflux_formal_consumer.py` と consumer test は無変更です。
- `acceptance_duration_ledger.json` は親が main 取り込み後、`tools/update_acceptance_duration_ledger.py --add-only` で上記 7 node と実測値を登録する必要があります。

## 契約の問題

無し。

## 総括

単位 B の実装と焦点検査は完了しました。変更は指定された 2 file のみです。commit、docs 編集、push、branch 操作は行っていません。