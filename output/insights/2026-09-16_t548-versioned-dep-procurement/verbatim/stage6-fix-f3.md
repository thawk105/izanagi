## 総括

所有ファイル `orchestrator/tests/test_silo_ladder_rung1_evidence.py` のみ修正しました。F1 差分・凍結 evidence・既存の歴史定数は変更せず、commit もしていません。

定数の変更（値は追補 2 から転記）：

- `EXPECTED_CURRENT_PBS_JOB_SHA256`：
  `117b3bb4a4789b00b2b2e8335ee78a6f329125e26aa42c6002283fd0ed894f0e` →
  `99687368a1fdf10d8f699be3a32afd2814f51d98bcad5fbdf6a1862ca72b456f`
- `EXPECTED_HISTORICAL_SUBMITTER_SHA256`：未定義 →
  `e12ac6589f7587540b38d5c528b2561e446031b4ce0ee48443ee4be583d8e9b2`
- `EXPECTED_CURRENT_SUBMITTER_SHA256`：未定義 →
  `6990ad4470aba09b8c62224f33a453c330a0be4fbb913cf1e477bb882659412b`

`submitter` を歴史値の辞書へ追加し、現行 bytes の exact pin と `binding != current` を維持しました。

指定コマンドを実走し、**2 passed / rc=0**。実走 nodeid：

- `orchestrator/tests/test_silo_ladder_rung1_evidence.py::test_silo_ladder_rung1_commit_witness_matches_committed_raw_data`
- `orchestrator/tests/test_silo_ladder_rung1_evidence.py::test_silo_ladder_rung1_committed_evidence_rebinds_content_not_head`

`sha256sum` の実測値は、両 shell とも上記の現行 pin・追補 2 の現行値と完全一致しました。`git diff --check` も rc=0。削除した test 関数は **0 件**です。