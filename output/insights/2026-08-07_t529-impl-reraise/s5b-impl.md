実装は完了しました。編集はコードとテストの 2 ファイルだけで、commit・git add は行っていません。pytest は Pegasus の dispatch 障害により未実走です。

## 編集内容

- [s8b_floor_campaign.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-impl-reraise/orchestrator/campaign/s8b_floor_campaign.py:308)

  - resolver 必須の `_validate_protocol_with_resolver` を追加。
  - callback 内で resolver を一度だけ呼び、exact `ExecutionEnvironmentContract`、`env_tag`、記録 hash の三一致を検査。
  - historical lane は `resolve_by_contract_sha256(recorded_hash, expected_env_tag=env_tag)` に固定し、fallback なし。
  - current lane は `lookup(env_tag)` と記録 hash の一致を要求。
  - 公開 `validate_protocol` を historical lane に固定。
  - builder、発行 read-back、fresh/resume admission を current lane へ移動。
  - admission で得た同一 contract object を calibration、execution receipt、build、計測 command receipt まで伝播し、後段 lookup を削除。
  - CLI は historical artifact 検証後、`run_campaign` 内で current admission を再実行する二段構成を維持。

- [test_s8b_floor_campaign.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-impl-reraise/orchestrator/tests/test_s8b_floor_campaign.py:4429)

  - g1/current g2 の historical 正例を追加。
  - unknown hash、cross-env hash、不正 resolver 返却の negative control を追加。
  - fresh run が current g2 不一致を I/O、calibration、measure より前に拒否する試験を追加。
  - synthetic required contract を使う既存 live 試験を current private lane へ明示移送。
  - contract を必須伝播する既存 helper/runner 呼出しを追従。
  - 既存 resume 試験の期待値は変更していません。

凍結 artifact の SHA-256 は引き続き `261cec1c7f423b3eebff41ee716d2bfe2c6fa9a10a9dd86d91eaf71612e74aac` です。

## 公開 `validate_protocol` の全 caller

公開関数へ直接到達する caller はすべて historical lane です。current lane の公開切替面はありません。

| caller | 行 | lane |
|---|---:|---|
| CLI `main` | `s8b_floor_campaign.py:3559` | historical。その後 `run_campaign` が current を再検証 |
| `test_s8b_floor_campaign.py` | 399, 997, 1002, 1007, 1016, 1036, 1053, 1061, 1075, 1082, 2474, 4445, 4473, 4896 | historical |
| `test_s8b_floor_contract.py` | 175 | historical |
| `test_s8b_protocol_builder.py` | 101, 167, 178, 187, 417 | historical |
| `test_s8b_ratified_freeze.py` | 284 | historical |

旧来の production 内部経路は次のように current private lane へ移しました。

| 経路 | 行 | lane |
|---|---:|---|
| protocol builder | `s8b_floor_campaign.py:510` | current |
| 発行直後 read-back | `s8b_floor_campaign.py:652` | current |
| fresh/resume live admission | `s8b_floor_campaign.py:2829` | current |
| prediction runner | `s8b_prediction_runner.py:1463` → builder | current |
| CLI live 実行 | historical 検証後に上記 live admission | current |

## 検査結果

最終差分に対して次の selector を `python3 tools/run_tests.py` 経由で指定しました。

- `test_public_validate_protocol_resolves_recorded_historical_generation_once`
- `test_public_validate_protocol_historical_failures_never_fallback_to_current`（3 parameter）
- `test_fresh_run_rejects_recorded_g1_when_current_contract_is_g2_before_io`
- `test_resume_under_unchanged_current_contract_generation_completes`
- `test_resume_rejects_recorded_g1_when_current_contract_is_g2_before_calibration`
- `test_measure_run_cmd_projection_removes_runtime_root_and_rejects_missing_token`
- `test_required_existing_claim_reports_owner_and_changes_nothing`
- `test_binary_receipt_mismatch_aborts`

結果は `rc=16`、`Pegasus dispatch infrastructure failure: qstat -Q preflight rc=1` でした。pytest の collection・test body には到達しておらず、テスト赤はありませんが、緑も主張しません。状態は「実装済み・pytest 未実走」です。

別途、以下の副作用なし検査は成功しています。

- `git diff --check`
- 編集した Python 2 ファイルの AST parse
- registry が両 env とも 1 世代であることの確認
- 凍結 protocol に対する historical/current 正規化結果の一致
- historical/current が同一 contract object を返すことの確認
- 凍結 bytes の SHA-256 再確認

## 今日の受理・拒否挙動

今日は実装前後で同一です。

- 現 registry は `linux-baremetal`、`pegasus` とも 1 世代だけです。
- 各記録 hash の historical 解決先は、同じ `env_tag` の current `lookup` と同一 object です。
- したがって既存の正当な protocol は historical/current の双方で同じ正規化結果になります。
- unknown hash、cross-env hash、current hash 不一致は従来どおり拒否されます。
- 実 registry に g2 がないため、新たに historical だけが受理する artifact は今日は存在しません。
- 将来 g2 が発効した場合だけ、凍結 g1 artifact の read-only 検証は継続し、fresh/resume は current admission で拒否されます。

## 総括

historical artifact 検証と current live admission を分離し、実行経路には同一 current contract object を一貫して伝播しました。凍結 bytes、既存期待値、no-touch 対象は不変です。pytest は Pegasus の `qstat` dispatch 障害により未実走のため、親による再実走が必要です。