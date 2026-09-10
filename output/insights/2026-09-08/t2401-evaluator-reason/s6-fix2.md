## 追加したテスト

| scope | 固定した命題 |
|---|---|
| 1 | 境界入力を literal の 128 / 129 文字に変更し、`_DIAGNOSTIC_TEXT_MAX_LENGTH == 128` を直接 assertion |
| 2 | production evaluator は `ValueError` / `KeyError`、normalize は `TypeError` / `KeyError` を parameterize。test-registry evaluator に `ValueError`、normalize に `TypeError` を追加し、12 件の exact fallback と診断 3 field を固定 |
| 3 | type 抽出と reason 抽出の両 helper guardへ、それぞれ `KeyboardInterrupt` を追加 |
| 4 | `stderr.write()` が `ValueError` を送出しても、`main()` が終了値 1と同一 stdout bytes を保つことを固定 |
| 5 | 実 process CLI fixture を `RuntimeError` / `ValueError` で parameterizeし、path / module、text / JSON の全組合せで stdout bytes と exact stderr を固定 |

## 実走した nodeid と結果

- `orchestrator/tests/test_s8c_cli_entrypoints.py`: 20 passed、5.31秒
- `orchestrator/tests/test_s8c_preregistration_core.py`: 419 passed、22.12秒

いずれも指定された `PYTHONPATH=. python3 orchestrator/tests/<file>.py` の自走 harness で実走しました。

## 受理・拒否の含意

受理側: `[a-z0-9-]` のみで構成された128文字以下の reason は保持され、通る正例 `PreregistrationError("predicate-result-type")` は診断へ同じ reason を出す。  
拒否側: 129文字の reason や未捕捉であってはならない例外経路は、12件の fail-closed fallbackと `effective == false` の含意を維持する。

## production 無変更の確認

`git diff -- orchestrator/campaign/s8c_preregistration.py` は空でした。対象3ファイルの `git diff --numstat` でも変更は指定されたテスト2ファイルだけで、`git diff --check` も成功しています。

`git add`、commit、push、新規ファイル作成は行っていません。

## 未了・懸念

実装上の未了はありません。裁定記載どおり、有限個の例外型による検査は、試験済み型だけを列挙する意図的な catch 狭窄を完全には閉じません。

## 総括

scope 1〜5をテストだけで実装し、production の挙動と既存の期待値は変更していません。許可された両 harness は合計439件すべて緑です。