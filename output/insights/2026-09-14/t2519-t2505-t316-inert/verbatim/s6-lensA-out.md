## 拒否の維持

**通常経路は維持されていますが、stderr 書込み失敗時は同一ではありません。**

`if not admission.admitted:` と従来の `RuntimeError` 文面は不変です。しかし追加された `print` が先に例外を送出すると、従来の拒否例外へ到達しません。閉じた stderr なら `ValueError`、書込み先の障害なら `OSError` 等が該当します。これらを保護する処理はありません。

一方、非 Mapping の `evidence` や異型の record による攻撃は成立しませんでした。実 evaluator は `MappingProxyType` を持つ record を発行し、直前の family admission が record の型・evidence・発行元を検証します。非 dict であること自体は `.get` の障害になりません。

## 受理集合と D1849 / D1625

差分では以下が不変です。

- D1625 の理由コードと comparison の２組、および組の exact 一致検査。
- `_condition_gate_receipt_summary` と `SCHEMA_VERSION`。
- `condition_meaning_gate.py`。
- 既存テストの期待値。追加は１件だけです。

正常に print できた場合、detail は stderr のみに出ます。例外文面へ連結する処理も、stderr を receipt に取り込む処理もありません。`_error` は捕捉した例外の型と `str(exc)` のみを記録するため、evidence mapping が receipt へ流入する攻撃は成立しません。

ただし、出力障害時は次項のとおり receipt のエラー値が変わります。

## 追加 test は機構を通るか

**実 CMake・実 evaluator・実 family admission・変更対象の拒否分岐を通ります。stub はありません。**

一時コピーの CMakeLists に仕込んだ `FATAL_ERROR` が configure を失敗させ、`_run_process` の detail が赤 supply record に入り、追加 print へ到達します。固有 witness と rc・argv の検査があるため、別の早期失敗だけで緑になる作りではありません。meaning の detail 欠落も実際の `declaration=None` 経路を通ります。

これは拒否診断の正例であり、inert 比較到達や今回の実測原因の再現を証明するものではありません。

nit は以下です。

- `assert cmake in lines[0]` は実行時取得なので揮発 path の焼込みではありません。ただし gate は executable を `resolve` するため、`which` が symlink の別名を返す環境では正しい出力でも失敗し得ます。解決済み path を期待する方が整合します。
- `len(lines) == 2` は診断行追加などの正しい変更でも壊れる、表示形式への過剰な固定です。
- `captured.out == ""` は stderr 出力という要件に沿います。例外文面の完全一致も今回の拒否維持には有用ですが、stderr 障害時の維持までは検査していません。

## must-fix

1. **診断出力の失敗が従来の拒否例外を置換する。**  
   対象：[probe の追加 print](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2519-t2505-t316-inert/tools/pegasus/probes/t316_sandbox_backend_probe.py:1968)。診断処理が失敗しても従来の `RuntimeError` を送出する構造にしてください。  
   **成果物への影響：receipt の `observations.S6.error.type/message` が条件関門の拒否情報から出力障害の型・文面へ変わり、拒否理由が失われます。受理集合は広がりません。**

## 成立しなかった攻撃

- print が拒否を飲み込み、build 継続や受理へ転じる経路。
- 非 dict の evidence、異型 record が追加 `.get` まで到達する実経路。
- evidence mapping や正常に print した detail の receipt への混入。
- D1625 の exact 一致、schema、gate 本体の変更。
- stub や別経路の失敗による追加テストの偽の緑。
- 既存テストの削除・期待値緩和。

## 総括

must-fix は１件：stderr 障害時にも従来の拒否例外を維持する必要があります。  
受理集合・D1849／D1625 は維持され、追加テストは実機構を通ります。  
本レビューは静的検査のみ。145件・追加単体の成功は親の実走報告に基づきます。