# 未land文書3件の回収監査

対象は T-2129 (60015f6c74)、T-2440 (4e60e07c98)、T-2669 (690596918a)。
着手時local mainは b2037abfa1467507cf92c851c83f262239f81641。
一次資料は各tipのspoolと、repo外 `/work/1/SFC/tanab/dev-wave-jobs/` の同名job dir。

- `review.md`: 独立read-only監査の逐語。must-fix 1、should/nit 0。
- `focus.md`: 文言修正後の焦点監査の逐語。所見1 closed、GO。
- 親裁定: 所見1をrealとして採用。dry-runも同じ `plan_fold` を通るため、検出がland後に限られるとの
  一般化を解消した。README・旧worklogのtitleと引用外注記だけを直した。旧依頼引用は保持する。
- T-2440は収集義務・出力規則・予算と整合。T-2669の旧4所見は全てclosed。新たな裁定はしない。
- 実装・テスト・gate・spool挙動は変更なし。変異matrixは実装差分ゼロのため免除。
- 関連検査: 統合commit 8f22d8c78 の `test_spool_fold.py` と `test_check_docs.py` は747 passed、3 skipped。
  bounded localのメモリ上限到達後、正規runnerが計算ノードrequest 6371.nqsvへ移行し完了した。
  README文言修正後の最終受入とは区別する。一次ログは同rootの `dev-wave-docs-three-recovery/related-tests.log`。
- 独立子は静的照合だけを担った。受入・provenance・land・旧processの占有確認は親の責任で行う。
