FC の修正を所有 path の 3 ファイルに実装しました。`_CONDITION_DEFAULTS` に新規 14 macro を既定値 0 で追加し、B01 の重複した個別照合表を削除しました。B03 の test 名は元の `...exact_38...` に戻し、本体の 57 と docstring は維持しています。commit はしていません。

件数固定値は、登録した 14 macro の直接の増分だけ更新しました。14 件すべてが `ROUTE_CMAKE_CXX_FLAGS` なので **19→33**。sink の分類では同じ 14 件が s1 と certify で到達不能、s8b で covered となるため、それぞれ **39→53、29→43、43→57** です。既存 assertion の緩和や skip はありません。

`git diff --check` と 3 ファイルの AST 解析は通りました。対象 3 ファイルの pytest は `tools/run_tests.py` 経由で試しましたが、Pegasus の `qstat -Q` 事前確認が失敗し、子テストは起動していません。**実装済み・未実走**です。

## 総括

焦点走の赤 4 件に対応する修正は完了しました。親側で計算ノード実走による確認が必要です。