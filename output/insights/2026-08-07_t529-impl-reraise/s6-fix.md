must-fix 2 件は実装済みですが、pytest が実行基盤の rc=16 で開始前停止したため、両所見とも `partial` です。緑・`closed` は主張しません。

## 所見対応表

| 所見 | 状態 | 対応 |
|---|---|---|
| C1: profile hash の二重正本 | `partial` | leaf の `profile_sha256` を唯一の実装とし、公開側を同一 object の alias 化。同一性テストを追加。未実走 |
| D-1: T419 binding の leaf 脱落 | `partial` | leaf を dirty 対象へ追加し、観測 SHA field と leaf-only dirty 負例を追加。未実走 |

`regressed` と判定した所見はありません。

## 編集ファイル

- [calibration_verify.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-impl-reraise/orchestrator/campaign/calibration_verify.py:29)
  - `_profile_sha256` を公開 `profile_sha256` へ変更。
  - `VerifiedCalibration` と loader 内部も同じ関数を使用。

- [env_attestation.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-impl-reraise/orchestrator/campaign/env_attestation.py:108)
  - `profile_sha256 = _calibration_verify.profile_sha256` として同一 object を公開。
  - `profile_to_dict` の挙動・型検査は変更なし。

- [t419_probe_causality.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-impl-reraise/tools/pegasus/probes/t419_probe_causality.py:3490)
  - `related` に `orchestrator/campaign/calibration_verify.py` を追加。
  - record に観測値 `calibration_verify_sha256` を追加。
  - 比較述語の引数、既存 `expected_*` field の意味は変更なし。

- [test_env_attestation.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-impl-reraise/orchestrator/tests/test_env_attestation.py:1111)
  - 公開側と leaf 側の関数同一性を固定するテストを追加。

- [test_t419_probe_causality.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-impl-reraise/orchestrator/tests/test_t419_probe_causality.py:1531)
  - leaf だけが dirty の場合に `matched=False` となる負例を追加。
  - leaf を `related` から外す変異では模擬 git status が空になり、テストが失敗する構造。

tracked 既存テストの期待値、docs、output、既発行 artifact は変更していません。git add / commit も行っておらず、index は空です。

## テスト結果

以下をすべて `python3 tools/run_tests.py` 経由で試行しました。

- `orchestrator/tests/test_env_attestation.py::test_profile_sha256_uses_leaf_canonical_implementation`
- `orchestrator/tests/test_t419_probe_causality.py::test_submission_binding_rejects_dirty_calibration_verify`
- `orchestrator/tests/test_real_repo_serialization.py::test_real_repo_group_collection_exactly_matches_canonical_nodes`
- 新規 2 nodeid の `--collect-only`
- 新規 2 nodeid の再試行

全 3 回とも pytest 開始前に以下で停止しました。

```text
Pegasus dispatch infrastructure failure: qstat -Q preflight rc=1
```

結果は runner rc=16 です。テスト失敗は観測されていませんが、実行自体されていないため「実装済み・未実走」です。

静的検査は以下が成功しました。

- 変更対象 5 Python ファイルの AST parse
- `git diff --check`
- `python3 tools/check_codex_agents.py`
- `python3 tools/check_docs.py`

## 所有外への波及可能性

- hash consumer:
  - `orchestrator/qualification/t126_driver.py`
  - `execution_guard` が消費する `VerifiedCalibration.attestation_profile_sha256`
  - `test_t126_qualification_driver.py`
  - `test_execution_guard.py`
  - `test_silo_ladder_rung1_driver.py`

- calibration loader の既存 caller:
  - `campaign/loop.py`
  - `qualification/t126_driver.py`
  - `s8b_floor_campaign.py`
  - `s8b_oracle_driver.py`
  - `s8b_oracle_report.py`
  - `s8b_ratified_freeze.py`
  - `silo_ladder_rung1.py`

- T419 consumer:
  - `run_experiment` と `finalize_output` が `_submission_binding` を使用。
  - 将来発行する T419 result の provenance に観測 field が増え、leaf dirty 時は `binding_verified=False` になる。
  - PBS/CLI の既存 expected field インタフェースは不変。
  - 既発行 T419 result artifact は未変更。

- 共有 fixture:
  - `test_env_attestation.py` の `_profile`／`_required_artifact` は変更なし。
  - T419 負例は subprocess と SHA 計算をテスト内だけで差し替え、共有 fixture へ現行 hash を焼き込んでいない。

- source bytes の変更により、将来の Silo `runtime_modules_sha256`、T419 の既存 `env_attestation` pin、commit/tree を束縛する T126 identity は統合 commit 後に変化し得ます。historical evidence の再書換えは不要かつ禁止です。

## 総括

C1 と D-1 の要求コード・回帰テストは最小範囲で実装済みです。静的検査は通過しましたが、pytest は Pegasus dispatch infrastructure failure により未実走なので、両所見は `partial` のまま親へ引き渡します。