## 現行の受理と拒否

- compiler identity、comparable argv の不一致を先に拒否。
- 非 inert は root-dependent builtin、dependency closure、前処理 bytes の順で判定し、bytes が異なる場合だけ `requested-default-preprocess-different` で受理。
- inert は raw bytes 完全一致だけを `stock-inert-preprocess-identical` で受理し、不一致は `stock-inert-mismatch` で拒否していました。

## 実装した変更

[condition_meaning_gate.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2226-inert-root-diff/orchestrator/campaign/condition_meaning_gate.py:2250) に以下を実装しました。

- 線形な行対応比較と requested 側だけの一回走査置換。
- `source/<rel>` が requested dependency closure に実在する path のみ置換。
- build root は置換対象外。
- 残差なし、置換 1 件以上、root-dependent builtin 非空の場合のみ、新理由 `stock-inert-preprocess-root-location-only` で受理。
- raw bytes 完全一致枝と非 inert の判定順序、理由コード、evidence schema は維持。
- 新しい comparison、4 evidence field、exact schema、configure argv の `-S` source root 束縛を追加。

## 追加したテスト

[test_condition_meaning_gate.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2226-inert-root-diff/orchestrator/tests/test_condition_meaning_gate.py:614) に指定名どおり追加しました。

- `test_inert_root_location_only_difference_is_green`
  - `BACKOFF_FIXED=-1`
  - `BACKOFF_NOINLINE=0`
- `test_inert_semantic_difference_on_root_line_is_red`
- `test_inert_root_shaped_literal_outside_closure_is_red`
- `test_inert_root_difference_without_code_owned_file_builtin_is_red`
- `test_inert_root_location_evidence_binds_configure_source_roots`

すべて `tmp_path` の copy だけを変更します。意味差の負例は `__FILE__` と同じ物理行に配置しました。

## 実走結果

テスト結果はありません。すべて実装済み・未実走です。

`tools/run_tests.py` で以下を試しました。

- 上記 5 nodeid。parameterized case を含めて 6 case。
- `test_condition_meaning_gate.py` の collection。
- module 名検索で得た consumer 11 file と `test_plain_runner_coverage.py`。

いずれも test process は起動されず、`child_started=false`、`rc=16`、`qstat -Q preflight rc=1` で停止しました。login 側も最終観測で headroom 951,971,840 bytes のため、予約控除後の bounded local 実行条件を満たしませんでした。

静的には AST parse、指定した 5 関数名の存在確認、`git diff --check` を完了しています。

## 波及の静的列挙

直接 caller は `backoff_sweep`、P3 各 loop、A1/A2 certification、S1/S2/S3/S5/S6/S8a、`screening_driver`、`silo_ladder_rung1`、T152、T1683、T316、SS2PL study です。stock comparison を使う driver は root-location-only mismatch の受理へ進み得ます。

consumer test は module/function 検索で次を確認しました。

- backoff extended/profile/sweep
- ccbench spawn sites
- condition meaning gate
- P3 S4 loop
- paper story A1/A2
- S1 direct comparison
- S5 permutation coverage
- screening driver
- T316 sandbox probe

共有の `condition_gate_test_support.py` と静的 fixture は未変更です。T316 の旧 reason exact 契約は裁定どおり scope 外のままです。

## 残した未了

- 新設 nodeid、consumer test、meta-test の実走。
- test-first の現行赤確認も infrastructure failure のため未観測。
- 親による受入全走と commit。

## 総括

実装とテスト登録は working tree に残しましたが、実走できていないため closed とは申告しません。HEAD は `e6cbed86c` のまま、未 stage・未 commitで、変更ファイルは上記 2 件だけです。