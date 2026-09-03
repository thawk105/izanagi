## 対応結果

G4 は `partial（実装済み・未実走）` です。

[test_s8b_attempt_registry.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/t1851-a2alpha-fix2/orchestrator/tests/test_s8b_attempt_registry.py:2819) に独立 node を追加しました。

## 新設した nodeid

`orchestrator/tests/test_s8b_attempt_registry.py::test_v2_reservation_rejects_claim_from_other_protocol_generation`

実 `FloorAttemptConsumptionMarker` capability を公開経路 `reserve → finalize → consume → validate` で発行しています。

- 正しい protocol の claim は `ReservedAttempt` として受理
- 別 protocol 世代の claim は exact 署名で拒否

`[s8b-attempt-registry-consume] v2 admission claim differs from the registry generation or slot`

## 受理集合の検査

identity 検査と protocol 比較を両方除去すると、別 protocol 世代の claim に対する `reserve_attempt_slot()` が拒否されず `ReservedAttempt` を返します。

そのため、負例の `pytest.raises(...)` assertion が `DID NOT RAISE` で破れます。別署名への変化ではなく、不正 claim が拒否集合から受理集合へ移る差を検出します。

## 検査結果

runner に新設 nodeid を2回指定しましたが、いずれも pytest child 起動前の infrastructure failure でした。

- runner rc: `16`
- `child_started=false`
- 理由: `qstat -Q preflight rc=1`
- 実走した pytest nodeid: なし
- 状態: 実装済み・未実走

`queue-wait-timeout` ではないため、指定された timeout override は使用していません。

静的検査は成功しています。

- `python3 -m py_compile orchestrator/tests/test_s8b_attempt_registry.py`
- `git diff --check`

## 変更量と境界

- 追加: 76 LOC
- 削除: 0 LOC
- production、docs、`output/`、`external/`、共有 helperは未編集
- `git add`、commit、push、remote・branch 操作は未実施

## 総括

- G4: `partial（実装済み・未実走）`
- 新設 nodeid: `test_v2_reservation_rejects_claim_from_other_protocol_generation`
- 受理集合の根拠: 両検査除去時に foreign-protocol claim が受理され、`pytest.raises` が `DID NOT RAISE` で破れる
- 実走結果: pytest child 起動前に2回とも infra rc=16
- 追加した changed LOC: 76
- 読めなかった資料: なし
- 確かめられなかった事実: 新設 node の実行結果、および両検査除去変異での実際の赤化結果