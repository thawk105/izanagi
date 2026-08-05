実装済み・未実走です。指定4ファイルだけを変更し、docs 編集・commit は行っていません。

| 所見 | 状態 | 対応 |
|---|---|---|
| G-1 / NR-02 / C-03 | partial | `_write_exclusive` が作成成功後の I/O 失敗時だけ、自身が作成した inode を確認して削除。caller は正常 return 後だけ temp を所有。既存 file / symlink 衝突を保存する negative test を追加 |
| G-2 / NR-01 / PC-01 | partial | 選択肢 **(b)** を採用。`rejection.json` に全 `attestation_profile` と canonicalization 識別子を保存し、成果物内の profile だけから SHA-256 を再計算するテストを追加 |
| G-3 / NR-03 / C-02 | partial | shape・policy・値取得を evaluator 内の一度の評価へ集約。`__contains__` / `keys` / `get` が例外を投げる `Mapping` でも public 述語が `False`、診断が構造化エラーになる vector を追加 |

(b) を選んだ理由は、既存の `attestation_profile_sha256` の意味と既存期待値を変えず、hash の完全な preimage と canonicalization 規則を成果物へ自己完結させられるためです。

静的検査は成功しました。

- 変更4ファイルの `python3 -m py_compile`
- `git diff --check`
- 変更対象が許可された4ファイルだけであることの exact 検査
- 既存テストの assertion・期待値変更は **0件**
- 既存の temp failure 2テストは期待値を保ったまま、production helper の `fsync` failure を直接踏む fixture に強化

未実走の主要 nodeid は以下です。

- `test_execution_guard.py::test_effective_clock_custom_mapping_failures_are_structured_rejections`
- `test_execution_guard.py::test_effective_clock_public_predicate_preserves_legacy_overflow_short_circuits`
- `test_execution_guard.py::test_effective_clock_evaluator_decomposition_boundary_vectors`
- `test_calibrator_certify.py::test_cli_rejection_profile_hash_recomputes_from_artifact_only`
- `test_calibrator_certify.py::test_cli_publish_temp_collision_preserves_existing_path[file]`
- `test_calibrator_certify.py::test_cli_publish_temp_collision_preserves_existing_path[symlink]`
- `test_calibrator_certify.py::test_cli_publish_temp_write_failure_removes_partial_file`
- `test_calibrator_certify.py::test_cli_publish_temp_cleanup_failure_is_structured`

所有外への波及可能性は、public clock 述語を使う execution receipt consumer、`silo_ladder_rung1`、env contract/attestation tests、`rejection.json` を opaque manifest 化する Pegasus collector/final receipt、ならびに `_write_exclusive` を共有する calibration・report・sidecar・publish receipt の全書込み経路です。共有 fixture は `_invoke`、`_pegasus_shaped_probe` です。

## 総括

- G-1 の他者所有 temp 削除回帰を所有フラグと inode 確認で修正した。
- 既存 file / symlink 衝突の非破壊テストを追加した。
- G-2 は選択肢 (b) で hash preimage を成果物へ自己完結させた。
- G-3 は Mapping の評価重複と例外漏出を解消した。
- 既存期待値は1つも変更していない。
- 指定4ファイル以外、docs、commitには触れていない。
- 静的検査は成功したが、Pegasusログインノードのため pytest は未実走。
- 親実測の 663 passed / 2 skipped は未再検証であり、緑は主張しない。