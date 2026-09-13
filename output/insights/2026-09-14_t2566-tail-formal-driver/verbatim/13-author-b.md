## 実装したもの

- `benchparse.py`：十進整数文字列を直接 `int` にする parser を追加。
- `runner.py`：通常・遅延開封の両測定関数に整数記録の opt-in を追加。
- `pipeline.py`：opt-in の転送、採用 point の観測検査、conditional `reps` の発行を追加。
- `loop.py`：correctness と整数記録 opt-in を非既定時だけ転送。
- `test_layer3_report.py`：conditional 4 key、旧 payload の明示集合、旧 schema による `reps` 拒否の検査を追加。

**変更は未検証です。commit・docs 編集はしていません。**

## 既定 False で従来と同一であることの根拠

静的には、既存 parser の処理を変更せず、整数 parser・観測追加・`reps` 発行を opt-in 内に限定しました。`_BENCH_PAYLOAD_EXTRA_KEYS` は `{"screening_disabled"}` のままです。

変更前は、整数カウンタが無くても通常測定を受理し、abort 率は印字値を優先します。payload は required 13 key、conditional 3 key、extra 1 key でした。互換性の実走証明は未完了です。

## 実走結果

次の4ファイル全体を `tools/run_tests.py -n 2` で指定しました。

- `orchestrator/tests/test_layer3_report.py`
- `orchestrator/tests/test_calibrator.py`
- `orchestrator/tests/test_calibrator_deferred_output.py`
- `orchestrator/tests/test_screening_opt_in.py`

**rc=16。`qstat -Q preflight rc=1` により dispatch が失敗し、pytest 子プロセスは開始されませんでした。実走 nodeid・緑はありません。** 契約 loader 束縛による赤でもありません。

ログ：`/tmp/t2566-b-focus.log`

追加検査は**実装済み・未実走**です。制約 meta-test は `test_real_repo_serialization.py`、`test_growth_test_holds_contract.py`、`test_hold_inventory.py` を検索しましたが、洗い出し・実走とも未完了です。

## 意図的な赤 (未 land 依存)

事前指定 finding 集合：**空集合**。未 land 依存を理由に意図的に赤にしたテストはありません。相手側の新規テストとの統合検証は未実施です。

## 波及可能性の静的列挙

指定された production ファイル群で `rep_observations` を参照するのは次の **5ファイル**でした。

- `s8b_floor_attempt_launcher.py`
- `s8b_floor_campaign.py`
- `s8b_floor_stats.py`
- `s8b_ratified_freeze.py`
- `s8b_terminal_evidence.py`

`screening_driver.py`、`p3_s4_loop*.py`、`paper_story_a*.py` には当該文字列の直接参照はありませんでした。

共有 fixture・consumer test では `s8b_v2_freeze_fixture.py`、`test_s8b_floor_campaign.py`、`test_calibrator_deferred_output.py`、`test_campaign.py` の参照を確認しました。公開 API・prepared 経路を含む波及調査は未完了です。

## 守れなかったこと

**テスト runner が所有外のファイルを自動生成しました。**

`output/pegasus-dispatch/40ae2668f96ed180f61b7ad260433017/receipt.json`

これは「所有 path 以外を編集しない」という境界に抵触するため、指定どおり発見時点で作業を停止しました。削除も追加の変更になるため行っていません。

## 総括

指定5ファイルへの実装変更は置きました。  
テストは dispatch の前処理で停止し、実走できていません。  
runner による所有外 receipt 生成を確認し、作業を停止しました。  
統合前に差分レビュー、焦点走、meta-test の検証が必要です。