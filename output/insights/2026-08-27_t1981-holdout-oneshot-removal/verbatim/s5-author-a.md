## 総括

現行は、同じ6-field効果 key の再予約と旧 attempt marker の再消費を拒否し、n-pilotでは承認値が偽なら拒否します。変更後は、過去の観測に関係なく予約ごとに新しい測定世代を発行し、同一測定世代内の attempt 二重消費だけを拒否します。

所有4ファイルのみ変更しました。Git commit/add等は行っていません。

## 実装した内容

- `measurement-generation-claims/` と `measurement-generation-consumed/` を新設し、旧 `claims/`・`consumed/` と分離。
- `measurement_generation_*` 接頭辞で世代ID、digest、cell claim digestを記録。
- `_key_fields` の6-field効果 keyは変更せず、`cell_effect_digest` として世代をまたいで維持。
- floor、oracle、legacy n-pilot、R33の全予約で新測定世代を発行。
- floorの承認引数を公開・内部予約署名から削除。
- `FloorHoldoutReservation.measurement_generation_digest` を追加。
- n-pilotの承認引数は署名を維持しつつ完全に不活性化。
- R33の公開receipt/manifest key集合は変更せず、既存`transaction_id`を測定世代IDへ結線。
- 旧v1/v2 claim、ledger、attempt markerのexact historical decoderを温存。
- currentとhistoricalをversion dispatchするfloor inspectorを実装。

変更ファイル:

- [s8b_holdout_admission.py](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t1981-holdout-oneshot-removal/impl-a/orchestrator/campaign/s8b_holdout_admission.py)
- [test_s8b_holdout_admission.py](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t1981-holdout-oneshot-removal/impl-a/orchestrator/tests/test_s8b_holdout_admission.py)
- [s8b_floor_evidence_fixture.py](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t1981-holdout-oneshot-removal/impl-a/orchestrator/tests/s8b_floor_evidence_fixture.py)
- [test_s8b_oracle_driver.py](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t1981-holdout-oneshot-removal/impl-a/orchestrator/tests/test_s8b_oracle_driver.py)

## 現行挙動と変更後挙動

- floor: 旧effect claimがあってもfresh予約可能。floor予約署名から承認引数を削除。
- oracle: 同じverified manifest/blockを再予約可能。
- legacy n-pilot: True/Falseどちらの承認引数でも同じ予約挙動。
- R33: 過去cellとのintersectionでは拒否せず、新transaction/測定世代を発行。
- attempt: 別測定世代の同一論理attemptは双方消費可能。同一測定世代の再消費はdurable markerで拒否。
- 未知`observation_role`、freeze signature一致、gflags、保護比率、canonical JSON、`O_CREAT|O_EXCL`は変更なし。

## 追加・改訂したテスト

指定された11 nodeidをすべて追加・維持しました。

- `test_floor_rereservation_ignores_legacy_cell_claims`
- `test_floor_fresh_rereservation_appends_generation_rows`
- `test_floor_attempt_single_use_is_scoped_to_measurement_generation`
- `test_attempt_ticket_is_durably_single_use`
- `test_legacy_n_pilot_repeated_reservation_is_admitted`
- `test_r33_repeated_reservation_uses_new_generation`
- `test_effect_key_is_stable_across_measurement_generations`
- `test_legacy_claim_bytes_remain_inspectable`
- `test_n_pilot_approval_argument_is_inert`
- `test_oracle_repeated_reservation_is_admitted`
- `test_oracle_attempt_single_use_is_scoped_to_measurement_generation`

統合テスト`test_floor_rereservation_ignores_legacy_cell_and_attempt_bytes_end_to_end`では、旧claim 12件、旧floor marker 96件、旧ledger/attempt-ledgerを配置し、fresh予約、finalize、最初のattempt消費、旧bytesのread-only inspectionまで通します。

R33同一世代の二重消費を固定する`test_r33_attempt_ticket_is_durably_single_use`も追加しました。

## 実走したもの / 実走できなかったもの

正式なpytest nodeidは一件も実走できておらず、緑は主張しません。

- `tools/run_tests.py`による指定nodeid実行: `qstat -Q preflight rc=1`、子未起動、`rc=16`
- 両所有テストファイルの`--collect-only`: 同じ理由で子未起動、`rc=16`
- AST構文検査: 4ファイル成功
- 指定11テストと統合テストの本体を`/tmp` fixture上で診断呼出し: 成功。ただしpytest nodeid実走ではありません。
- `git diff --check`: 成功
- 指定nodeid 11件のAST実在・ASCII名検査: 成功

runnerが診断receiptを`output/pegasus-dispatch/191732702fa4c525d15aeee3bf2ad84e/`と`e84b00a51a4e78f0990b67e5b653e9e7/`へ生成しました。編集・削除はしていません。

## 所有外への波及可能性

- `s8b_floor_campaign.py:7667-7676`は、削除した`irreversible_pilot_approved`を内部予約関数へ渡しています。実装子Bによるcaller更新が必須です。
- 同callerは追加された`measurement_generation_digest`をまだ利用していません。
- `s8b_oracle_n_pilot.py:2943-2953`は承認引数を引き続き渡しますが、署名を維持したため互換です。pin対象ファイルは未変更です。
- `test_s8b_holdout_freeze.py`と`test_s8b_ratified_verify.py`は旧`claims/`を直接検査します。旧namespaceとdecoderを残したためhistorical fixtureは維持されます。
- `test_s8b_floor_campaign.py`、`test_pegasus_floor_tools.py`、`test_s8b_freeze_io.py`は実装子B側のCLI・caller・fixture更新と統合が必要です。
- ファイル集合globを持つ`test_pytest_collection_config.py`を確認しましたが、新規ファイルは追加していないため更新不要です。
- `test_real_repo_serialization.py`のoracle nodeid列挙は限定されたT-080集合で、今回の追加・改名nodeidを列挙していません。旧名への参照も見つかりませんでした。

## 期待赤 (実装子 B 未 land 由来)

事前指定する期待findingは次の2種類だけです。

1. `s8b_floor_campaign.py`からの呼出しで、削除済み`irreversible_pilot_approved`による`unexpected keyword argument`。
2. 実装子B所有テストに残るfloor承認CLI/env/argv期待値と、新しいcaller契約の不一致。

これ以外の失敗は回帰として扱う必要があります。n-pilot/oracle側の予約署名不一致は期待赤ではありません。

## 未完・親の判断が要る点

- 実装子B差分との統合後に、指定nodeid、関連floor/oracleテスト、repository標準checkの正式実走が必要です。
- Pegasus dispatch infrastructure不調のため、本sandboxではpytest結果を確定できませんでした。
- commitは親担当のため作成していません。