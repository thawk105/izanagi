## 対応表

| 前回の新しい所見 | 判定 | 検算・根拠 |
|---|---|---|
| `INLINE_VERSION_OPT=1` の insert で `Tuple::body_` の key が空 | **partial** | [修正 patch:11](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-vhash-cicada-gc-records-fix/stage7/fix-cicada-gc-records-scan-key.patch:11) の予備で、最新版に key がある間は従来の key を使える。ただし最新版が body のない delete 版になると空 key が再発する。 |
| V3a の run 数 | **partial** | [spec-v3a.json](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-vhash-cicada-gc-records-fix/spec-v3a.json) は **10＋20＋3＋2＋3＝38 run**。[V3 結果要約:7](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-vhash-cicada-gc-records-fix/v3-result-summary.md:7) は 38 に訂正済みだが、追補裁定の「48 run」は未訂正。 |
| V2 の空 key 件数 | **open** | 原本の F 3 run・12 trace file を再計数すると **82〜114 行/file、計1,142行**。[V2 結果要約:7](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-vhash-cicada-gc-records-fix/v2-result-summary.md:7) の「88〜114」は未訂正。 |

## 新しい所見

- **should-fix — [scan-key patch:12–15](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-vhash-cicada-gc-records-fix/stage7/fix-cicada-gc-records-scan-key.patch:12)**：inline insert では [insert 用 `init()`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-vhash-cicada-gc-records-fix/external/ccbench/cc/cicada/include/tuple.hh:95) が空の inline body を `Tuple::body_` に複写する。さらに [delete 版](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-vhash-cicada-gc-records-fix/external/ccbench/cc/cicada/transaction.cc:399) が最新版なら予備も空になる。**成果物への影響：この構成の scan-key 修理は、削除版に対する元の空 key 障害を解消しない。**

- **should-fix — [scan-key patch:13](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-vhash-cicada-gc-records-fix/stage7/fix-cicada-gc-records-scan-key.patch:13)**：空文字を「key が欠落した」印として使っているが、[索引への insert](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-vhash-cicada-gc-records-fix/external/ccbench/include/masstree_wrapper.hh:135) と [`TupleBody`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-vhash-cicada-gc-records-fix/external/ccbench/include/tuple_body.hh:26) には空 key の拒否がない。`update()` も索引 key と渡された body key の一致を検査しない（[transaction.cc:196](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-vhash-cicada-gc-records-fix/external/ccbench/cc/cicada/transaction.cc:196)）。**成果物への影響：空 key を使う workload で最新版の body key が変われば、予備は正しい空の索引 key を捨てる。確認した TPCC 呼出しでその不一致が起きる、という主張ではない。**

- **nit — [追補裁定:51](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-vhash-cicada-gc-records-fix/s4-ruling-addendum-1.md:51)、[V2 結果要約:7](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-vhash-cicada-gc-records-fix/v2-result-summary.md:7)**：親の記録にはそれぞれ **V3a＝38 run**、**V2＝82〜114 行/file** と記す必要がある。**成果物への影響：実施数と障害量の記録が原本と食い違う。**

## 総括

**「どの構成でも修理が完了し、修理前より悪くならない」とは確認できない。** 通常の TPCC key では `Tuple::body_` の非空 key を使う経路は妥当だが、API は最新版との key 一致を保証しない。`std::string` は `string_view` から内容を複写するため、取得後の view の寿命には依存しない。一方、複写中に参照する tuple・版の寿命はこの差分では保証されない。

CI の [親検査:36–45](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-vhash-cicada-gc-records-fix/stage7/run_ci_build.sh:36) は、F の祖先性、`F..tip` の1〜2 commit、同範囲の merge 不在を意図どおり検査する。`(( … ))` は `if` 条件内なので `set -e` による早期終了を招かず、Git コマンド失敗は通過扱いにならない。依存 pin と image の検査は差分で変更されていない。判定は静的検査であり、fix 2 後の実走結果ではない。