## 総括

合成は健全であり、自動 merge は両側の意図を保存する。  
変更先は同一ファイル内の別々の `frozenset` で、共通 consumer には集合自体が参照渡しされる。  
S8C の辞書順代表は変わるが、同一 file・group の代表選択なので検査の意味は変わらない。  
静的監査のみであり、collection／pytest の実測は親側に残る。

## 合成の監査

- `merge-ours.diff:5-12` は `_S8C_PREDICATE_SNAPSHOT_NODES_GOLDEN`、`merge-theirs.diff:5-15` は `_P3_B4_MATERIAL_REPORT_NODES_GOLDEN` を変更する。共通 base blob は同じ `555d2dbcc` で、hunk は基準行 257 と 290 に分離しており、自動 merge で双方の加算が残る。
- `orchestrator/tests/test_real_repo_serialization.py:259-311` では両集合が独立している。追加 node はそれぞれ異なる test file に属し、一方の追加が他方の集合の意味や要素を変えない。
- 同ファイル `:313-318` の `_LONG_LIVED_FIXTURE_GROUP_NODES_GOLDEN` は、P3 集合を `p3-b4-material-report`、S8C 集合を `s8c-predicate-snapshot` へ別々に結ぶ。`:1247-1261` が両 group の live collection と exact golden を同じ経路で比較する。
- 同ファイル `:343-352` の `_REAL_REPO_FIXTURE_ACCESS_GOLDEN` は S8C 集合そのものを `current_commit_snapshot[module]` の consumer 集合として参照し、`:1262-1279` が live fixture closure と完全一致させる。したがって S8C の追加は group 検査に加えて fixture consumer 検査にも伝播する。P3 はこの fixture-access 表の対象ではなく、long-lived group の exact 検査だけを受ける。
- 同ファイル `:1318-1345` の conflict-edge 導出は group ごとの access mode のみを見るため、集合内 node の増加では意味が変わらない。
- 単一要素抽出で影響するのは同ファイル `:4234` の S8C 代表だけである。追加前の `gap_reason...` から追加後の `c04_rejects...` へ辞書順先頭が変わるが、`:4233-4236` では filename と group が同じ固定値で、`:4244-4251` の検査対象も group component だけなので意味は不変。P3 集合には単一要素抽出がない。
- consumer の取り残しは見当たらない。両集合は `_LONG_LIVED_FIXTURE_GROUP_NODES_GOLDEN` へ直接流れ、S8C はさらに fixture-access 表へ直接流れる。C04 側の別登録についても `s4-adjudication.md:5-19,29` が invariant は更新不要、duration ledger は unknown node を許容すると裁定している。

## merge message

```text
merge(main): 共有 fixture group の golden 集合を両親から合成

wave 側では、C04 の実 repo 負例が current_commit_snapshot を共有するため、_S8C_PREDICATE_SNAPSHOT_NODES_GOLDEN に node を 1 件追加した。main 側では、material report の共有 group に加わった 4 node を _P3_B4_MATERIAL_REPORT_NODES_GOLDEN に追加した。

両変更は同じ test_real_repo_serialization.py 内でも別々の frozenset を更新する。_LONG_LIVED_FIXTURE_GROUP_NODES_GOLDEN はそれぞれを別 group に結び、_REAL_REPO_FIXTURE_ACCESS_GOLDEN は S8C 集合を current_commit_snapshot の consumer 集合として参照するため、双方を保存する合成は group の exact golden と fixture consumer 閉包を維持する。
```