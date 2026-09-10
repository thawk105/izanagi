実装は完了しました。commit・docs 編集はしていません。

実装内容:

- 裁定 profile の4件を `resolved` に更新し、先送り3件を維持。
- required gate は8件のまま、5件を `resolved`、fixture assignment gate を指定どおり改名。
- selection enum、裁定状態 pin、required-gate 三者 hash pin を追加。
- 設計 §8.1 の selection 列、および §10 の段集合と gate ID の drift 検査を追加。
- 指定された11 test nodeを exact 名で追加。既存期待値を `unresolved_count=2`、`blocking_gates=3` に更新し、gate 選択をID検索へ変更。
- `status=incomplete`、`pending_count=5`、先送り3件、fixtures・row coverage・case raw hash群は維持。

算出した `entries_sha256` は:

`93cfe2b396d4831800537967d67628c7bca38b8b7595c4ffedaccb5e88211e41`

固定順の8 gate entry配列を入力に、`json.dumps(sort_keys=True, ensure_ascii=True, separators=(",",":"), allow_nan=False).encode("ascii")` 相当の canonical bytesを生成し、末尾LFを含めずSHA-256を計算しました。manifest literal・再計算値・module独立pinの一致を静的確認済みです。record全体は canonical JSON + LF 1 byteです。

検査結果:

- `git diff --check`: 成功
- JSON canonical bytes、gate件数・hash、変更禁止 subtreeのHEAD比較: 成功
- `python3 tools/check_codex_agents.py`: 成功
- `python3 tools/check_docs.py`: 成功
- pytest対象:
  `python3 tools/run_tests.py -q orchestrator/tests/test_calibration_freeze_authority_contract.py orchestrator/tests/test_plain_runner_coverage.py`
- runner結果: rc=16、`qstat -Q preflight rc=1`。収集・実行nodeidは0件です。したがって実装済み・未実走であり、緑は主張しません。

静的な波及可能性:

- `calibration_freeze_authority_execution.py::run_all_executable` と `test_calibration_freeze_authority_execution.py` が共有manifest loaderを利用します。fixture集合は不変ですが、旧gate ID・状態・順序を持つmanifestは新しいpinで拒否されます。
- `load_ruling_profile`、`validate_repository`、`require_stage0_complete` の利用者は、旧裁定状態や設計selection／段集合のdriftを新たに拒否されます。
- 検索上、上記以外のproduction callerはありません。execution fixtureおよびconsumer testは未実走です。

## 総括

- 段4裁定を許可された4ファイルへ実装しました。
- 段0は `incomplete`、先送り3件とcase bytesは不変です。
- required-gate SHA-256は `93cfe2b3…11e41` です。
- 静的検査は成功、pytestとmeta-testはdispatch基盤障害により未実走です。