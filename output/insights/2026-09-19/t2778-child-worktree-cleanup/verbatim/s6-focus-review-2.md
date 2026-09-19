## 総括

対象 HEAD `c9e4ad77a`。指定の残り2件は **closed**。`git diff 2a8127c4e HEAD` の全削除行を確認し、新たな回帰・既存期待値の緩和は見つかりませんでした。

以下、`C`＝`tools/dev_wave_cleanup.py`、`T`＝`orchestrator/tests/test_dev_wave_cleanup.py`、親資料は指定 parent 配下です。

| 番号 | 判定 | 根拠 file:line |
|---|---|---|
| A1 | **closed** | `C:1564` が `check-attr --stdin -z --all` を使用。`C:1570` で終端 NUL と3要素単位を検査し、`:1573` で属性名・値を正しく取り出す。空出力も受理する。`:1574` は `filter`／`eol`／`working-tree-encoding` を値によらず拒否し、`text` は `set`／`auto` のみ拒否。allowlist も `C:242` で置換済み。 |
| A1・負例 | **closed** | `T:313` の `tr a-z A-Z` はサイズを維持。`:319` で全追跡ファイルを再正規化し、`:322`〜`:324` で「blob 大文字・作業木小文字・status clean」を明示検査する。`:325` は従来の `backup-precheck` 拒否を維持し、`T:163`〜`:168` で rc20・理由・非変更も検査。親 `focus-4.log:36,40` に当該ケースを含む成功記録あり。 |
| N1 | **closed** | 親 `mutation-spec-v2.json:80` の m4 は2件を列挙。`T:225` と `T:480` が tar を開くため、ゼロ bytes 化で両方失敗する。他の関連検査は存在確認・自己整合する digest・非変更検査であり、追加の検出 node は見当たらない。静的確認上、完全集合。 |
| 回帰確認 | **closed** | 差分の削除6行をすべて確認。`C:242,1564,1574` は意図した属性判定修正、`T:309` 以降は既存 `x` ケースを残したパラメータ化と検査追加。既存 assertion の削除・反転・緩和なし。 |

8件の anchor は **HEAD の `C` に各1箇所だけ逐語一致**しました。

| 変異 | 行 |
|---|---:|
| m0 | 1539 |
| m1 | 1505 |
| m2 | 1540 |
| m3 | 1539 |
| m4 | 1712 |
| m5 | 1788 |
| m6 | 1449 |
| m7 | 1017 |

親の `focus-4.log:10,16,40` は dispatch `11171.nqsv`、**187 passed・rc=0**。受入全走・変異実走の証拠とは扱っていません。本レビューで pytest は実走していません。

**GO**