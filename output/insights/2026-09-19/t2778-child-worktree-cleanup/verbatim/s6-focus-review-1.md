## 総括

**NO-GO。A1 は未解消で、m4 の expected_nodes に漏れがあります。** その他の指定所見は、裁定された修正範囲で閉じています。

対象 HEAD は `2a8127c4e`。指定資料、`fix.patch`、`git diff 2ba400087 HEAD` の全削除行を確認しました。pytest・変異は実走していません。親の `focus-2.log:47` は **269 passed / 1 skipped**、`:55` は **rc=0**。これは焦点走の証拠であり、変異結果ではありません。

以下、`C` は `tools/dev_wave_cleanup.py`、`T` は `orchestrator/tests/test_dev_wave_cleanup.py` を指します。

| 番号 | 判定 | 根拠 file:line／残る問題・最小修正 |
|---|---|---|
| A1 | **open** | `C:1574` が `filter` の文字列 `unspecified` を無条件に許可する。未指定状態と、実際の driver 名 `filter=unspecified` を区別できない。下記参照。 |
| A2 | closed | `C:1612` で削除対象 admin 配下の module に限定し、primary store に `pin^{commit}` が存在しなければ拒否。`C:257` の allowlist は絶対 `--git-dir=`、`cat-file -e`、SHA＋`^{commit}` の形を受理する。 |
| A3 | closed | `T:240` の stdin 待機、`:249` の書込み・close・期限付き正常終了確認へ変更。timeout 増量なし。親焦点走も成功。 |
| A4 | closed | `docs/dev-wave/operations.md:211` に両経路の `--main-worktree` を明記。`C:1424` の parser と整合。 |
| A5 | closed | 再照準された anchor は `C:1449`、`:1017`。`T:320` と `T:356` が、それぞれ正規化省略・main 再検証省略を検出する構造。正式変異実走は未確認。 |
| A6 | closed | `C:1687` の create-only 書込み・fsync 後、`:1843` で tmp → `os.link` → tmp unlink → directory fsync。既存 receipt は上書きしない。 |
| A7 | closed | `C:4` に schema・field・信頼境界・rename 両端。`docs/dev-wave/workers.md:21` に登録順と参照先。親の決定 fragment `docs/spool/decisions/2026-09-19-dev-wave-t2778-child-worktree-cleanup-2.md:28` に世代識別の限界、`:30` に対象外範囲。ただし fragment は HEAD の差分に含まれない親側資料。 |
| A8 | closed | `T:200` で `main(argv)` の rc0、`:201` で stdout、`:202` 以降で元の結果・復元検査を維持。 |
| B1 | closed | A4 と同じ。 |
| B2 | closed | `C:1675` で固定 main tip と子 HEAD の merge-base を取得し、`:1677` でそこから子 HEAD までの全差分を保存。`:1741` の receipt 集合にも追加。`T:213`、`:218` で集合と所有外報告を検査。allowlist は `C:251`。 |
| B3 | closed | A3 と同じ。 |
| B4 | closed | A7 に加え、`docs/dev-wave/operations.md:213` に tree entry・退避可能性、`:214` に親の unlock を明記。 |
| B5 | closed | 未使用の `ls-files --others -z --exclude-standard` は削除済み。現 allowlist は `C:239`。 |
| B6 | closed | `C:1588`、`:1602` で recursive status を各階層一度だけ取得。採用されなかった履歴・tree 再検証の省略は行っていない。 |

**A1 の具体的な残存穴**

`* filter=unspecified` と `filter.unspecified.clean` を設定すると、clean filter は実行されます。しかし `check-attr` の出力は、filter が未指定の場合と同じ `unspecified` です。

書込みを伴わないローカル Git 確認で、両者の属性出力が一致する一方、`secret=` 行を除去する driver によって `hash-object --stdin --path=…` の結果が変わることを確認しました。`-w` は使用していません。

このため、生 bytes にしかない行を filter が除去して status が clean になる入力では、`C:1574` を通過し、`C:1684` の dirty 退避にも入らず失われます。現在の `T:309` は driver 名 `x` だけなので検出しません。

**最小修正:** `check-attr --all` 等で実際に設定された属性を識別し、明示的な `filter=unspecified` を未指定扱いしない。対応する allowlist と、生 bytes が blob と異なる実 Git 負例を追加する。裁定の「unspecified」という状態を、出力文字列だけで判定する部分の補正が必要です。

**N1 / new / m4 の expected_nodes が不完全**

根拠は親 `mutation-spec.json:80` と `T:471`。m4 は dirty の有無にかかわらず tar をゼロ bytes にするため、指定正例に加え、`test_remove_child_detached_ancestry_and_empty_backup` も `tarfile.open()` で失敗します。

最小修正は、この node を m4 の expected_nodes に追加することです。テスト期待値の緩和は不要です。

変異 anchor の逐語照合結果は以下です。**すべて HEAD にちょうど1箇所**ありました。検出結果は静的判定です。表中の node はすべて `orchestrator/tests/test_dev_wave_cleanup.py::` 配下です。

| 変異 | anchor 行／件数 | 期待される検出・生存と理由 |
|---|---|---|
| m0 | `C:1539`／1 | **SURVIVED**。括弧追加のみで等価。 |
| m1 | `C:1505`／1 | `test_remove_child_rejects_unregistered_path`。別 path の entry を選択して manifest 拒否を失う。他 node の漏れは見当たらない。 |
| m2 | `C:1540`／1 | 登録済みの `test_remove_child_rejects_unintegrated_author_commit` と `test_remove_child_empty_owned_paths_requires_ancestry`。別の履歴保存検査は両入力を拒否しない。 |
| m3 | `C:1539`／1 | `test_remove_child_empty_owned_paths_requires_ancestry`。空所有集合だけが新たに統合扱いになる。 |
| m4 | `C:1712`／1 | `test_remove_child_archives_dirty_integrated_author_and_keeps_branch` **および未登録の** `test_remove_child_detached_ancestry_and_empty_backup`。両方とも空ファイルを tar として開けない。 |
| m5 | `C:1788`／1 | `test_remove_child_rejects_live_process_cwd`。後段の占有再検査は残るが、期待する rc21／occupancy・非変更から外れる。 |
| m6 | `C:1449`／1 | `test_child_modes_reject_noncanonical_path[manifest]`。header の alias が通過する。`manifest_is_closed[relative-path]` は exact entry 不一致で引き続き manifest 拒否となるため、追加 killer ではない。 |
| m7 | `C:1017`／1 | `test_remove_child_main_advance_during_removal_is_partial`。main の前進を拒否しなくなる。既存 binding 交換 node は先行する snapshot 検査で引き続き拒否される。 |

fix2 の submodule fixture は `T:418` で primary 側の module store を作り、`:424` で子を固定 branch から clone、`:427` で子 admin 配下へ吸収し、`:431` で pin 一致を確認しています。`local-only-pin` は子 module だけに commit を作って gitlink を更新するため、今回の A2 を狙う構成です。clean／拒否の既存期待値は維持されています。

既存 wave mode は `C:1015` の従来検査と `C:1859` の経路分岐を維持し、回帰は見つかりませんでした。基点からの cleanup テスト差分は追加のみです。fix 差分には receipt 集合への `committed.patch` 追加と空 patch 検査対象の追加がありますが、既存 assertion の反転・緩和・削除はありません。

DW-O28 は **996 bytes**。実 docs・checker literal・synthetic literal の一致を確認しました。DW-S05-A の登録、rename、fix 再登録は実装と整合します。DW-O28 の dirty 退避・manifest 検査の文は子経路の説明としては合っていますが、wave 本体にも適用されるように読めます。`operations.md:213` を「wave は clean、子木は退避可能性・manifest 束縛」と区別すると正確です。これは文面の明確化事項です。

**最終判定: NO-GO。解除条件は A1 の変換属性判定修正と、m4 の expected_nodes 補完です。**