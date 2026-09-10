実装は完了しましたが、pytest は実行基盤障害で開始できていません。そのため所見はすべて `partial（実装済み・未実走）` とし、`closed` は主張しません。docs・commit・`tools/check_ai_provenance.py` は変更していません。

## 実装内容

[dev_wave_land.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-provenance-known-violation/tools/dev_wave_land.py:2090) を次のように修正しました。

- 最初に nonblocking lock を取得。busy なら checker を起動せず即時 `lock-busy`。
- lock 内で既存の cheap check を実行し、`locked_main != tested_tip` の場合だけ監査へ進む二相構成。
- 監査中は lock を解放し、終了後に再取得。取得不能なら `lock-busy`。
- 再取得直後と再 preflight 後に、main/wave HEAD・種別付き collision path 集合・control-plane identity を照合。
- ignored collision の消失を、元から空だった状態と区別して `RC_PROVENANCE` で拒否。
- `locked_main == tested_tip` の already-landed／active fold recovery では監査を起動しない。
- receipt を `tip_sha / checker_blob_sha / executed_bytes_sha / returncode` に拡張。
- 束縛 FD の bytes を実行前後に SHA-256 化し、committed blob 内容と照合。
- timeout を 3900 秒から 480 秒へ変更。
- 監査境界で捕捉可能な `BaseException` を `RC_PROVENANCE` へ変換。
- FD close を idempotent 化し、最初の close 失敗でも二つ目を閉じ、各 field を `-1` に更新。
- pathname 実行中だけ差し替えて復元する race は検出できないことを docstring に明記。

[test_dev_wave_land.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-provenance-known-violation/orchestrator/tests/test_dev_wave_land.py:1223) には、必須ケースと FD cleanup 検査を追加しました。既存期待値の反転・緩和・skip・削除はしていません。

## 検査結果

焦点 13 nodeid を正規 runner へ投入しました。

- `test_nonblocking_common_lock_reports_lock_busy`
- `test_provenance_gate_accepts_tip_zero_and_lands`
- `test_provenance_gate_rejects_tip_nonzero_before_ff`
- `test_provenance_audit_runs_with_global_lock_released`
- `test_already_landed_does_not_run_failing_provenance_checker`
- `test_provenance_audit_detects_removed_ignored_collision`
- `test_provenance_receipt_rejects_each_bound_field`
- `test_provenance_audit_rejects_executed_bytes_mismatch`
- `test_provenance_binding_close_is_idempotent_and_closes_both_fds`
- `test_provenance_receipt_rejects_tip_that_moves_during_audit`
- `test_provenance_subprocess_contract_and_exception_mapping`
- `test_provenance_checker_missing_and_symlink_components_are_rejected_clean`
- `test_active_transaction_recovery_completes_with_provenance_red`

さらに `test_dev_wave_land.py` 全体と plain-runner meta-test 3 nodeidも投入しました。しかし全3回とも pytest 開始前に `qstat -Q preflight rc=1`、runner rc=16 で停止しました。したがって実装済み・pytest 未実走です。

成功した静的検査:

- `python3 -m py_compile tools/dev_wave_land.py orchestrator/tests/test_dev_wave_land.py`
- `git diff --check`
- `python3 tools/check_codex_agents.py`
- `python3 tools/check_docs.py`

## レビュー所見対応表

| 所見 | 状態 | 対応 |
|---|---|---|
| A: M1〜M9 が7/9 | partial | M5を実行予定FD bytes対blob、M8を常時監査／常時非監査へ再照準するテストを追加。未実走。 |
| A: 実行checkerとreceiptが未束縛 | partial | FD bytesを実行前後に照合しreceiptへSHAを格納。pathname一時差し替え復元窓は残る。 |
| A: recoveryがfold commitを作る | partial | 親再裁定どおり「FFを行うか」で線引きし、recoveryは監査対象外。欠落・非0・timeoutテストは未実走。 |
| A: checker副作用で拒否入力を受理 | partial | HEAD、collision集合、control identityを監査前後で照合。ignored file消失テストは未実走。 |
| A: already-landed/recovery意味破壊 | partial | `locked_main == tested_tip` では監査を一切起動しない。未実走。 |
| A: fixtureが恒真化 | partial | lock marker、失敗checker不起動、到達可能なdirty bytes負例を追加。未実走。 |
| A: 例外・FD cleanup不完全 | partial | `BaseException`変換、idempotentかつ独立closeを実装・テスト追加。未実走。 |
| A: receiptのtree範囲 | partial | superproject tipとchecker bytesを束縛。import依存閉包・一時HEAD復元は未束縛。 |
| B1: lock-busy即時契約 | partial | lockを最初に取得し、marker不在と2秒未満を固定。未実走。 |
| B2: no-admitも監査される | partial | already-landedとactive recoveryを監査対象外へ。未実走。 |
| B3: 3900秒timeout | partial | 480秒へ短縮。lease heartbeat/fencingや運用docsは所有外。 |
| B4: FDのbytesを実行に束縛していない | partial | 同一FD bytesを実行前後にblob内容と照合。pathname実行の残余raceは明記。 |
| B5: 未検証状態でchecker実行 | partial | 初回lock内検査と監査後の全再検査、fingerprint照合を実装。瞬間的変更・復元窓は残る。 |
| B6: rc consumer/docs不十分 | partial | JSON schemaと成功status集合は不変と静的確認。docsは明示的編集禁止のため未対応。 |
| B7: fixture波及 | partial | SHA/path/cwd契約は維持し、既存race wrapperへの二相化影響を静的確認。全体テスト未実走。 |

`regressed` と判定した所見はありませんが、pytest未実走のため確定していません。

## 所有外への波及可能性

- CLI caller は新規FF時だけ最大480秒の監査と、新しい `RC_PROVENANCE=29` を受けます。
- `wave_land_window` はstatusだけを見ており、既存どおり `rejected` を失敗扱いします。
- 共有 `_Repo` fixtureを使う全landテスト、CLI E2E、Git wrapper、race、FD継承、fold/recovery consumerが二相化の影響対象です。
- `LandResult.as_json()` のfieldと成功statusは変更していません。
- runbook、DW-O23、D102/D239等のdocs整合は親側の所有です。

## 総括

- (a) 二相lock、no-admit監査省略、監査窓fingerprint、FD bytes receipt、480秒timeout、BaseException／FD cleanupを実装しました。
- (b) 焦点13 nodeid、対象ファイル全体、meta-test 3本を投入しましたが、すべてpytest開始前のrunner rc=16。静的検査4種は成功しています。
- (c) 閉じたと断言できる所見は未実走のためありません。残余riskはpathname一時差し替え復元、HEADの一時移動復元、checkerのimport依存閉包未束縛、所有外docs未更新です。