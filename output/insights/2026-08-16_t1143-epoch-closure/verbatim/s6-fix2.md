## 1. 変更した file と行

[orchestrator/tests/test_artifact_admission.py:1147](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1143-epoch-closure/orchestrator/tests/test_artifact_admission.py:1147)

- drift 前に同一 campaign を `HISTORICAL_RAW` 目的で読み出す処理を追加。
- 記録された `campaign_verifier_epoch` の完全値を `expected_epoch` に採用。
- `_expected_fixture_epoch()` と他テスト、既存 assert は未変更。

## 2. 所見への対応

`partial`。

根本原因への修正は実装済みで、現行 tree との静的整合も確認済みです。ただし指定 pytest は dispatch infrastructure failure により 0 件実行だったため、未実走要件を `closed` とは申告しません。

## 3. 変異時に per-path 判別が戻る理由

閉包から `X` を外すと、historical view と例外はいずれも同じ campaign の記録済み 11-path epoch を使うため、無関係な epoch 不一致が消えます。

- `[X]` は drift が current closure に含まれず、`CampaignVerifierEpochRejected` が発生しないため `pytest.raises` が赤になります。
- `[X 以外]` は未 commit drift を `current-closure-unavailable`、commit 済み drift を `recorded-current-closure-mismatch` として従来どおり拒否します。
- 両例外の epoch は記録値との完全一致を引き続き要求します。
- state、reason code、lock/WAL bytes 不変の assert は変更していません。

## 4. production を 1 byte も変えていないことの確認方法と結果

`git diff --quiet HEAD -- orchestrator/campaign/ orchestrator/verifier/` は `rc=0` でした。

`git diff --name-only` の出力は `orchestrator/tests/test_artifact_admission.py` のみです。`docs/` と `output/` も `git diff --quiet` が `rc=0`。commit は作成しておらず、HEAD は `999357c5` のままです。

## 5. 実走した検査

対象予定範囲:

`orchestrator/tests/test_artifact_admission.py::test_certified_acceptance_rejects_each_verifier_drift_fail_closed`

4 parameter node 全件を `tools/run_tests.py --force-dispatch` で投入しましたが、`qstat -Q preflight rc=1` により runner が `rc=16` で停止し、pytest は 0 件実行でした。したがって緑とは扱いません。

その他の確認:

- `git diff --check`: 成功
- `python3 tools/check_codex_agents.py`: `rc=0`
- `python3 tools/check_docs.py`: `rc=0`
- 現行 tree では production closure と fixture の exact 12 path が一致するため、記録 epoch は従来の期待値と静的に整合します。

## 総括

同一 campaign の記録 epoch を完全一致 oracle に使う最小修正を実装しました。  
per-path 変異では対象 path の node だけが `pytest.raises` 不成立で赤になる構造へ戻ります。  
production、docs、output は無変更で、commit も作成していません。  
pytest は dispatch 障害により未実走のため、対応状態は `partial` です。