## 総括

[build/t2686_ab_compare.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2686-measure-codex/build/t2686_ab_compare.py) のみ修正しました。

| 判定 | 結果 |
|---|---|
| closed | 指定条件が整合する `observations.patch_id` の merge 省略だけ許容。run summary にも明示 |
| closed | 実 raw 4件を受理。各14種、計56件の負例を拒否 |
| partial | 性能再測定・pytest 全走は未実施、親担当 |
| regressed | 今回の関数レベル検証では検出なし |

負例は timeout reason、parse error、別層 truncation、件数不整合など。実際の summary 式も検証しました。raw は読み取りのみで、payload・canonical bytes の不変を確認しました。

変更規模は **17行追加・4行削除、全153行**。所有外 consumer への波及は summary の追加フィールド `patch_id_merge_omission_only`。production・既存テスト・repo 外 driver は未変更です。