## 対応結果

対象 test の fixture のみ修正しました。別 repo は作らず、既存 helper を使って同一 repo 内に seed の異なる第2 protocol 世代を作成します。

正例と exact 署名の負例 assertion は変更・緩和していません。

## 変更量

- 追加: 22 LOC
- 削除: 9 LOC
- changed LOC 合計: 31
- production、共有 helper、他 test、docs、`output/`、`external/` は未変更
- `git add`、commit、push、remote・branch 操作は未実施

## 検証結果

対象 nodeid:

`orchestrator/tests/test_s8b_attempt_registry.py::test_v2_reservation_rejects_claim_from_other_protocol_generation`

runner は指定された timeout override 付きで投入しましたが、以下で pytest child は起動しませんでした。

- runner rc: `16`
- `child_started=false`
- 理由: `qstat -Q preflight rc=1`

代替確認として、module を importし、`TemporaryDirectory` の `Path` を `tmp_path` として対象関数を直接呼び出しました。

- 結果: `DIRECT_CALL_PASS`
- 例外: なし
- 正しい protocol claim の正例と exact-signature 負例の両方が成立

さらに実行時だけ identity/protocol 検査を除去して再実行し、期待どおり次で赤化することを確認しました。

`DID NOT RAISE S8BAttemptRegistryError`

`python3 -m py_compile` と `git diff --check` も成功しています。

## 総括

- 直した内容: 同一 fixture repo 内に既存 helper で第2 protocol 世代を作るよう変更
- fixture 成立の確認方法と結果: 対象関数の直接呼び出しが例外なしで成功。検査除去時は `DID NOT RAISE` で失敗
- 追加した changed LOC: +22/−9、合計31
- あなたが読めなかった資料、確かめられなかった事実: 読めなかった資料なし。pytest 実走結果は dispatch infrastructure failure のため未確認