## 所見 (must-fix / nit、file:line 付き)

**must-fix: なし。** HEAD は `b4631a92e`。対応表14行の参照先を読み直し、中心結論を覆す誤引用・接続経路は見つかりませんでした。

以下、`README.md` は `output/insights/2026-09-17/b2-delta-min-connection/README.md` を指します。

- **nit — README.md:52：manifest の `n` は任意欄。**  
  `s8c_result_judge.py:392` は `"n" in manifest` の場合だけ一致を要求します。「manifest に `n` があれば一致を要求」とすると正確です。共通 `n` による全 cell の反復集合検査は `:400-442` にあり、「`n` も1組」という結論は正しいです。

- **nit — README.md:71、84、89：束縛図の対象と保証範囲を限定する。**  
  registry が検査するのは manifest の **trials** と各 runtime report の cells です (`trial_registry.py:791-801,1672-1688`)。「trial manifest の cells」は両者を混同します。また judge のラベルは任意の異なる2文字列なので、`:84` の `"H1" / "H2"` は「正規 manifest の場合」と補足すると対応表5行目と揃います。`:90` の「下流で逆転が起きる余地は無い」も「registry の導出・検査範囲では」と限定するのが適切です。存在しない judge → registry 呼び出しを図示しているわけではありません。

- **nit — README.md:156、162、164：検索結果の要約に小さな不一致。**  
  `:156` の「他は docs/archive と output/insights」は、判定器自身の型定義・注釈・型検査を省略しています。`:161` の検索は呼び出しだけでなく `def judge` 2件も返します。`:164` の「test 3 file」は、正確には **テストコード2ファイルと `acceptance_duration_ledger.json`** です。production consumer が見つからないという結論には影響しません。

## 段 4 裁定の反映漏れ

**insight に反映すべき採用事項の実質的な漏れはありません。**

行番号補正、generation の文字列照合、共通 `n`、`{C10}`、別名2ラベルの限界、二重評価を候補にしない扱い、D1481 の設計方向、条件付き非同値導出、検索範囲、測定履歴を断定しない制限、docs の部分的陳腐化が反映されています。

「単一 holdout manifest への分割は契約外」は独立した一文にはなっていませんが、対応表5行目の「2ラベル × 3 arm・6 cell」という記述で内容は保持されています。fragment の完了形式は本レンズの確認対象外です。

## GO / NO-GO と理由

**GO。** 上記は補足・表現修正であり、新しい裁定を必要としません。

- 結論は「holdout 別値の未接続」に限定され、逆接続・誤受理・測定履歴の断定はありません。
- `effective` の連言は `section5_value_violations` を消費せず、指定検索範囲で違反を検査するコードはテストのみです。
- `d1 < mean_delta ≤ d2` の導出は `s8c_result_judge.py:1550` の厳密な `>` と一致します。
- 副次項目は将来の検討事項に留まり、異なる `n` の認可や新しい gate の導入を確定していません。

## 総括

**must-fix 0件、nit 3件。** 現行ソースの未接続という結論と、D1481 / D1326 に引き継ぎ新規裁定を求めない判断は妥当です。静的レビューのみ実施し、編集・テスト実走は行っていません。