## 変更内容

`orchestrator/tests/test_reflux_result_evidence.py` のみ修正しました。

- `_assert_layout_projection_rejected` から正例呼出しを分離。digest 計算・負例呼出し・match は維持。
- `test_ordered_wal_projection_accepts_exact_layouts` を新設。非空 bytes、JSON dict、attempt ID、schema、探索側の exact 型を検証。

## 新設・変更 nodeid

同ファイルに新設：

- `test_ordered_wal_projection_accepts_exact_layouts[official]`
- `test_ordered_wal_projection_accepts_exact_layouts[exploration]`

既存 nodeid・期待値は変更していません。

## 実走した検査 (未実走は明記)

pytest は未実走です。`PYTHONPATH=.` で import し、一時ディレクトリで直接呼び出しました。

- 通常：正例2件・負例全9件が成功。
- M3：上記11件中、新設正例 `[exploration]` だけが失敗。探索側を含む負例全9件は成功。
- メモリ上の gate を `finally` で復元後、全11件が再成功。

## 総括

must-fix を修正し、負例が正例の過剰拒否で赤化しないことを確認しました。production・変異 spec は未変更、commit は作成していません。