## base からの両側の差分 (それぞれ何をしたか)

- ours:
  - `s8b_floor_campaign.py` の `injected-build_fn` pinを `4715 → 4707`。
  - 同ファイルの `campaign` pinを `8642 → 8636`。
  - 台帳本体と鏡像の期待集合を合わせて計4箇所変更。
- theirs:
  - `b10_backoff_shape_sweep.py` の `campaign` pinを `4460 → 4470`。
  - 台帳本体と鏡像の期待集合を合わせて計2箇所変更。
- どちらも entry の追加・削除や、行番号以外のフィールド変更はありません。

## merged が両側の意図を保っているか

保っています。

base から merged への全文差分は、ours の4箇所と theirs の2箇所を合わせた6個の行番号置換だけです。ours から merged への差分は theirs の変更だけ、theirs から merged への差分は ours の変更だけでした。

## 期待集合の件数 (base / ours / theirs / merged)

`8 / 8 / 8 / 8` です。

各版とも以下を確認しました。

- `_DEFERRED_GATE_MEMBERS` は8件。
- 鏡像の期待集合も8件。
- `(relative_path, owner, sink_kind, sink_scope, sink_lineno)` の集合は台帳本体と鏡像で一致。
- `(relative_path, sink_kind, sink_scope)` による重複はありません。
- entry の消失・増加はありません。

## 行番号 pin の値の確認

merged では次の値が台帳本体と鏡像の両方に残っています。

- `s8b_floor_campaign.py` / `injected-build_fn` / `<module>.build_cells.invoke_build`: `4707`
- `s8b_floor_campaign.py` / `campaign` / `<module>.main`: `8636`
- `b10_backoff_shape_sweep.py` / `campaign` / `<module>.run_formal`: `4470`

theirs は s8b の同じ entry を変更していないため、どちらの値が現物と一致するか判断できないという競合は発生していません。

## 意味が混ざっている箇所 (無ければ「無し」)

無し。

`relative_path`、`owner`、`reason`、`sink_kind`、`sink_scope` は全版で保持され、変更された行番号が別 entry に紛れ込んだ箇所もありません。

## 総括

自動 merge は両側の意図を欠落なく保存しています。期待集合は8件のままで、台帳本体と鏡像も一致し、意味的な混在は認められません。

監査は4版の全文差分と構文上の集合比較による静的確認です。テストは実行していません。ファイルの作成・変更、`git`、commit は行っていません。