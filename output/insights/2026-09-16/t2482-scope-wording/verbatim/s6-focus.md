## 所見対応表

段6レビューの所見は、Aが0件、Bが should-fix 1件です。nit はありません。

| 所見 | 判定 | 根拠 |
|---|---|---|
| B：source bytes の例外の係り先が曖昧 | closed | `orchestrator/campaign/artifact_admission.py:85` の「本 map の外であり」直後に、`:86` で source bytes の例外を明記。独立 literal も `orchestrator/tests/test_artifact_admission.py:1381`、`orchestrator/tests/test_s1_9pair_figure_provenance.py:88` で追随 |

Bの「失敗node集合だけでは理由を証明できない」という確認事項も、下記の `test_output_tail` 照合で確認しました。

## 逐語照合

裁定 `stage4-ruling.md:91` から A2 v3 を抽出し、指定範囲の隣接文字列を `ast.literal_eval` で連結して比較しました。

| 対象 | 結果 |
|---|---|
| `orchestrator/campaign/artifact_admission.py:81` | 全290文字一致 |
| `orchestrator/tests/test_artifact_admission.py:1376` | 全290文字一致・独立 literal |
| `orchestrator/tests/test_s1_9pair_figure_provenance.py:83` | 全290文字一致・独立 literal |

半角空白、ASCII括弧、句読点を含め、1文字も違いません。

実commit `bfc53cc95` の差分も確認しました。変更は3ファイル・上記literal 3か所だけで、9行追加・9行削除です。identity_scope、tuple、受理述語、歴史値などへの変更はありません。

## 変異 probe の照合

台帳と各変異の `repo_head` は、いずれも `bfc53cc95b3e2445fe8c3468e317f0e60f8276a7` です。

以下の A は `test_artifact_admission.py::test_real_e0_is_rejected_only_by_certified_epoch_gate`、S は `test_s1_9pair_figure_provenance.py` の P1・P3・P8 の3 nodeを指します。

| 変異 | 台帳status | 赤node数・集合 | tailで確認した理由 |
|---|---|---|---|
| M0 | SURVIVED | 0 | rc=0、failed_nodes・tailとも空 |
| M1 | MISMATCH | 4：A＋S | A `:1371` の63/62不一致、S `:155` |
| M2 | MISMATCH | 4：A＋S | A `:1371` の非推移閉包句不一致、S `:155` |
| M3 | MISMATCH | 4：A＋S | A `:1376` の99/69不一致、S `:155` |
| M4 | MISMATCH | 4：A＋S | A `:1376` の除外説明不一致、S `:155` |
| M5 | MISMATCH | 4：A＋S | A `:1376` の完全性非主張句不一致、S `:155` |
| M6 | MISMATCH | 1：A | `:1371` の162/161不一致 |
| M7 | MISMATCH | 3：S | `:155` のみ |

Sの例外は全件 `ProvenanceError: HISTORICAL_RAW E0 differs: develop` で、`:386` から `:155` に到達しています。P3も先行のbytes検査で落ちていません。各failure digestは `errors=0`、`omitted_failures=0` で、他の理由の赤は見つかりません。

M0の共通drift核は、このprobeでは空です。M1〜M7の `MISMATCH` は、probe登録が `expected_status=SURVIVED`・期待node空であるためです。最終走の合格とは扱いません。

## 新規所見

**should-fix 1件：M4の実際の置換が追補の指定と異なります。**

`stage4-ruling.md:95` は、先頭空白付きの ` (収載 path の source bytes は委譲先であっても本 map の内)` だけを削除する指定です。しかし台帳のM4 `replacements` は、括弧句と後続の読点を削除し、先頭空白を残しています。`test_output_tail` でも結果が `外であり 完全性を主張しない` になっています。

失敗理由は指定のliteral不一致だけですが、**裁定どおりの単独変異を実測した記録にはなっていません**。M4の置換を裁定に合わせて再走し、最終記録へ反映してください。production fix自体の所見ではありません。

D1884に関する新規所見はありません。括弧句の主語は「収載 path の source bytes」に限定され、「委譲先であっても」は収載条件を拡張しません。tupleの定義を超える実行全体・外部環境の保証や、完全性の主張は追加されていません。

## 総括

段6の should-fix は **closed**。fixはA2 v3と完全一致し、指定範囲外の変更・新たな保証拡大・静的に確認できる退行はありません。

probeのnode集合と失敗理由は予測どおりです。ただし、**M4の置換内容に裁定との差異が1件あり、修正・再走が必要**です。必読資料はすべて読取済み。書込み・pytest実行はしていません。