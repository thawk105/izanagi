## 所見

1. **should-fix — 一段変異 M2 の結果分類が未実装。** [spec-v1.json:14](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-vhash-cicada-gc-records-fix/stage5/spec-v1.json:14) は `record-only` を指定し、[起動器:630](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-vhash-cicada-gc-records-fix/stage5/launch_gcfix_run.py:630) は走行結果に関係なく `met=True` を返す。個々の `gc_records_err` は保存されるので、親が t4・t8 の結果から R3 所定の **KILLED／SURVIVED** を集計・記録すれば足りる。放置すると起動器の成功だけでは M2 の結果を示せず、一次資料の変異結論が欠ける。

2. **nit — V1 の見積りは実際の指定より 10 run 多い。** [s4-ruling.md の R3](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-vhash-cicada-gc-records-fix/s4-ruling.md) は 76 run と記すが、[spec-v1.json:2](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-vhash-cicada-gc-records-fix/stage5/spec-v1.json:2) の合計は 20＋20＋3＋20＋3＝**66 run**。合否の受理集合は変わらないが、一次資料の実施数と事前見積りの参照がずれる。

実装報告の自己検査は、clang-format、厳密適用 (a)〜(h)、`py_compile`、dry-run、`bash -n` を実走・rc 0 と**表で主張**している。ただし各検査の完全な command と個別の出力は報告にないため、こちらでは再現証拠として照合できない。[author-xv-1.md の自己検査](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-vhash-cicada-gc-records-fix/author-xv-1.md)。CMake build、CI、ASan、TRACE=0 命令列比較、期待値判定の本走は報告どおり**未実走**。

## 裁定との対応

| 項目 | レンズ B の判定 |
|---|---|
| R1 | [修理 patch:4](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-vhash-cicada-gc-records-fix/stage5/fix-cicada-gc-records.patch:4) は `gc_records()` のみ +5／−1。待機判定と非 deleted への `ERR` を保ち、余計な整形もない。上限 +15／−3 内。 |
| R2 | 親 worktree で tracked の追加は当該 patch のみで、stage5 版と byte 一致。[CI script:9](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-vhash-cicada-gc-records-fix/stage5/run_ci_build.sh:9) の親 OID は F。CI と CCBench 修理 commit の実測・照合は本レビューの範囲では未確認。 |
| R3 | build 別 runs、期待値集約、ASan 指定、trace の D 件数・thread 数・計数値、identity 呼出しは揃う。M2 の分類は所見 1。spec の V1 は 66 run、V2 は 12 run。 |
| R4 | [一段変異 patch:4](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-vhash-cicada-gc-records-fix/stage5/onelevel-cicada-gc-records.patch:4) は `while`→`if` だけを変える。M1・M3 の期待値は spec にある。 |
| R5 | `git status` は空、`external/ccbench` の HEAD は pin C `68106660…` で status も空。docs・orchestrator・tools・他 wave patch の変更は見えない。 |

md_19 の予定箇所は [transaction.hh:200](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-vhash-cicada-gc-records-fix/external/ccbench/cc/cicada/include/transaction.hh:200) と [transaction.cc:923](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-vhash-cicada-gc-records-fix/external/ccbench/cc/cicada/transaction.cc:923)。本修理の 849 行付近とは直接重ならない。後で一本にまとめる際は、同一 `transaction.cc` の行移動と trace patch の適用順を再確認する必要がある。

## 総括

修理 patch 自体は小さく、R1 の意味と所有範囲に合う。親の実走後、M2 の KILLED／SURVIVED を明示して記録することが、レンズ B で残る実質的な確認事項。