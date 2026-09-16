## 所見一覧

**静的レビューでは real の不具合は見つかりませんでした。must-fix 0、nit 0 です。** 以下、検討した懸念を refuted として記します。pytest・変異 matrix・受入全走の成功を示すものではありません。

以下の参照では、`V`＝`orchestrator/campaign/s8c_acceptance_receipt.py`、`T`＝`orchestrator/tests/test_s8c_acceptance_receipt_v2.py`、`C`＝`orchestrator/campaign/autonomous_trial_completeness.py`、`R`＝`orchestrator/tests/test_trial_registry.py` とします。

| 懸念 | 判定 | 根拠 |
|---|---|---|
| 裁定と実装が異なる | refuted | 新ブロック・追加テストとも plan v2 に一致。V:2039、V:2053、T:931 |
| C02 を残せば complete＋空 cells が通る | refuted | mandatory-reasons 通過後、新ブロックが拒否。V:2053 |
| 別 gate の例外でも負例が成功する | refuted | 期待する code・全文を `^…$` で限定。T:955、T:995 |
| 新判定・assert が恒真である | refuted | status と descriptor の有無により分岐し、前提 assert も変更前の入力値を検査。V:1461、V:2053、T:942、T:970 |
| 正規 partial・no-build・v1 を新たに拒否する | refuted | partial は条件外、descriptor 証明ありは条件不成立、v1 は適用対象外。V:1999、V:2053 |

## 裁定との食い違い

**なし。**

- production は mandatory-reasons の直後、aggregate の前。条件式、`receipt-arm-binding`、`complete trial lacks descriptor proof` は裁定の逐語どおりです（`s4-adjudication.md:39`、V:2039、V:2053、V:2061）。
- テストは指定既存関数の直後に3関数4 node を追加。名前、`[v2]`／`[v5]`、組み立て順、期待 regex が一致します（裁定:55、T:906、T:931）。
- conflicting descriptor は int 80 を確認して79へ変更し、digest の同期を行わず、既存拒否を確認してから cells を削除しています（T:970）。
- 正例は C02 を明示追加し、指定 trial を terminal-failure にしています（T:1013）。
- 提供差分には helper・import・既存期待値・台帳の変更はありません（`impl-29b0f70d7.patch:22`）。

## 再現 case の修正後判定

下表は修正前の再現結果と現物の評価順に基づく**静的判定**です。

| case | 修正後の拒否 |
|---|---|
| A2 / A3 / B2 | `[receipt-arm-binding] complete trial lacks descriptor proof` |
| C2 / C3 | 同上。no-build leaf 検証と mandatory-reasons を通過して新判定へ |
| A1 / C1 | 従来どおり `[receipt-mandatory-reasons] c02-arm-binding-unproven was dropped without descriptor proof` |
| B1 | 従来どおり `[receipt-arm-binding] cell descriptor content digest differs from receipt` |
| C4 | 従来どおり `[receipt-cross-binding] [cross-binding] build report must contain at least one cell` |

空 cells は descriptor proof を False にします。全 trial の proof が同じ順序で追加されるため、`zip` が未検査 trial を落とす経路もありません（V:1461、V:1507、V:2008、V:2025）。

B1 は descriptor digest 比較で先に拒否されます（V:1476）。C4 は v5 の leaf 再導出中に拒否され、新ブロックには到達しません（V:2026、C:4235）。

## テストの実効性

**別層での先行失敗を成功として扱う懸念は refuted です。**

負例3 node は report bytes の変更ごとに hash を更新し、receipt を commit する helper を通します。arm execution、run-start、freeze の期待 digest は保持されます。cells 削除後に v5 化するため、leaf は削除後の cells 数から生成されます（T:299、T:506、T:944、T:985）。

aggregate と attempt registry の検証は新判定より後です。したがって負例はこれらを実行して通過するテストではありませんが、これらで先に落ちることもありません（V:2061、V:2083）。新判定を無効化した際の後続通過は、変異実行で確認する事項です。

**正例が capability に到達できない懸念も refuted です。** helper は report／row を partial にそろえ、hash を更新した後、その hash に対応する terminal-failure を作ります（T:425、T:455）。leaf 計算後の status 変更も問題ありません。no-build leaf は cells 数を含みますが status を含まないためです（C:4176）。

正例は verified の status・C02・certifying を検査し、`require_current_verified_receipt` を実際に呼びます。同関数は再検証するため、SHA 比較は単なる自己比較ではありません（T:1021、V:2110）。

前提 assert にも意味があります。

- `complete`：report と row が新条件の対象であることを固定。
- `do_build is False`：build 空 cells の既存拒否との混同を防止。
- `type(...) is int` と `== 80`：変異元の型・値を固定し、79への変更が実際の変更であることを保証。

いずれも値を代入して直後に同じ値を確認する恒真形ではありません（T:942、T:970）。

## scope 外候補

新たに報告すべき実在問題はありません。

受理集合の縮小は v2〜v5 の descriptor 証明を欠く complete に限定されます。v3／v4 は共通経路の読解であり、実測確認ではありません（V:1999、V:2053）。

producer テストの complete report は descriptor を保持し、partial report は新条件の対象外です。既存の producer 発行 receipt を新条件が拒否する根拠はありません（R:1055、R:1775、R:2987、R:3005）。

## 総括

**実装は裁定に一致し、指定の欠陥を塞ぐ構造になっています。修正要求はありません。**

動的なテスト成功・変異検出力は未確認です。また、確認できる効果は verifier／v5 capability の受理集合の是正までであり、certified 成果物への到達を実証したものではありません。