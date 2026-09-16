## 変更点

指定の 5 ファイルだけを変更しました。

- `digest.py`: 指標を明示の 4 種に変更し、latency の整形分岐を削除。帰属例と除外理由を更新。
- `runner.py`: `_summarize_rep_results()` を追加し、direct／deferred の両経路で使用。
- `model.py`: 集約規則と WAL に latency を保持する理由をコメントに記載。`_median`・5 key は維持。
- `test_critic.py`: 指定の既存 4 箇所を更新、新規テスト 1 本を追加。
- `test_calibrator.py`: 新規 5 本・9 node を追加。自走でも direct／deferred を別 node として走らせるため、harness を拡張しました。これが plan-v2 に対する補足です。

変更前は、偶数有効 reps の abort_rate／latency_ns に上側中央の代表 rep の値が入りました。変更後は中央 2 rep の算術平均とし、片側でも欠損なら None、単一 rep field と奇数時の規則は維持します。

## 実走結果

両コマンドに `PYTHONDONTWRITEBYTECODE=1` を付けて実行しました。

| コマンド | 実走範囲 | 結果 |
|---|---|---|
| `PYTHONPATH=. python3 orchestrator/tests/test_calibrator.py` | 自走 harness 全 node | **78 passed / 0 failed / 0 skipped** |
| `PYTHONPATH=. python3 orchestrator/tests/test_critic.py` | 自走 harness 全 77 関数 | **29 passed / 48 failed** |

calibrator の新規実走 nodeid（接頭辞は `orchestrator/tests/test_calibrator.py::`）：

```text
test_measure_point_even_reps_average_central_indicators[direct]
test_measure_point_even_reps_average_central_indicators[deferred]
test_measure_point_odd_reps_preserve_legacy_values[direct]
test_measure_point_odd_reps_preserve_legacy_values[deferred]
test_measure_point_even_reps_none_indicator_is_none[direct]
test_measure_point_even_reps_none_indicator_is_none[deferred]
test_measure_point_parity_uses_valid_reps_not_requested[direct]
test_measure_point_parity_uses_valid_reps_not_requested[deferred]
test_measure_point_no_valid_reps_keeps_last_parsed_fields
```

critic の変更対象では `test_load_workload_preserves_legacy_commit_without_build_attempt_id` が passed。他の既存変更 3 本と新規 `test_digest_omits_latency_from_projection_table_and_axes` は admission で停止しました。失敗本文の主要部分：

```text
ContractLoaderBindingError: contract-loader-drift:
disk bytes が HEAD blob と不一致: orchestrator/calibrator/runner.py

CampaignVerifierEpochRejected:
campaign verifier epoch rejected certified acceptance:
state=E1-stale reason=current-closure-unavailable
```

既存 harness の引数注入不足も発生しています：

```text
TypeError: test_contract_mismatch_is_raised_before_receipt_validation()
missing 1 required positional argument: 'monkeypatch'
```

期待した例外に届かない失敗：

```text
Regex pattern did not match.
Expected regex: 'no preceding verify_done'
Actual message: 'campaign verifier epoch rejected certified acceptance: ...'
```

`git diff --check` は成功。変異 matrix は指定どおり未実行です。critic の対象断言の確認と受入全走は親に残ります。

## 波及の静的列挙

- `test_calibrator_deferred_output.py`: deferred 開封時点、例外、out parameter の契約。
- `pipeline.py`／`test_campaign.py`: bench 集約、WAL の指標、abort_rate による screening。偶数 reps の境界で screen-reject／verify 送りが変わり得ます。
- `p3_s4_loop`／`test_p3_s4_loop.py`、`online_digest.py`: digest 表・軸から latency が消えます。
- `backoff_sweep_report.py`: `load_workload` の consumer。指定例の `test_backoff_sweep_report.py` は現 checkout では見つかりませんでした。
- WAL 直読の 8c／layer3／backoff extended sweep: key 集合は維持し、今後の偶数 reps の値が変化。
- 共有 fixture の `campaign_lock_test_support.py`: HEAD 束縛により、今回の未 commit 差分で critic の admission が停止。
- role 文書の latency 記述、過去 WAL、人手射影は残件です。

## 総括

実装済み。変更は許可された 5 ファイルのみです。
calibrator は新規 9 node を含む 78 node が成功しました。
critic は 29 passed／48 failed。対象断言まで到達していない検査があります。
commit・push・docs 編集・禁止された Git 操作は実行していません。
統合 commit 後の critic 再検査・変異 matrix・受入は親へ引き継ぎます。
