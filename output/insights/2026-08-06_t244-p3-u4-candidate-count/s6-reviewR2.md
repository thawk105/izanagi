## 所見

### R2-1 — must-fix: 旧 key 拒否テストが実際の旧 payload を再現していない

[test_reflux_origin_ledger.py:2136](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-u4-candidate-count/orchestrator/tests/test_reflux_origin_ledger.py:2136) は、新しい sealed payload を残したまま `"cardinality"` を追加しているだけで、extra-key 拒否しか証明しない。旧 reserve/commit の `cardinality` 単独形や、全 count がない旧 sealed 形を alias 受理する実装はこの検査を通過できる。これは F29/F60 型の代表性不足である。

実際の旧形として、reserve/commit は `member_row_count` を除いて `cardinality` に置換し、sealed は3 countをすべて除いた payload、budget は旧 `batch_cardinality_min` 形を個別に拒否させる必要がある。

成果物影響: 旧形 alias が復活すると authority/event codec の受理集合が広がり、同じ試行状態を複数の event hash・proof-chain 参照で表せる。

### R2-2 — must-fix: T6 再裁定対象の liveness consumer が未追随

[liveness_probe.py:42](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-u4-candidate-count/output/insights/2026-08-05_t244-p3-liveness/liveness_probe.py:42) は旧 `batch_cardinality_min`、[同:178](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-u4-candidate-count/output/insights/2026-08-05_t244-p3-liveness/liveness_probe.py:178) は旧 `reserved_cardinality` を使用している。[T6 再裁定:191](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t244-p3-u4-candidate-count/s4-adjudication.md:191) と正面から不一致で、tracked wrapper は subprocess 成功と6件の PASS を要求する。[test_t244_p3_liveness_probe.py:17](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-u4-candidate-count/orchestrator/tests/test_t244_p3_liveness_probe.py:17)

policy を `batch_member_row_count_min=2`、`batch_distinct_candidate_count_min=1` にし、snapshot field を `reserved_member_row_count` に追随させる必要がある。

成果物影響: 6件の liveness witness がすべて `NOT_RUN` のため、この revision を参照する proof chain に mutation-kill 証跡を載せられない。

### R2-3 — must-fix: V18 の独立 raw fixture が tombstone 後の count を更新していない

[test_reflux_origin_ledger.py:2920](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-u4-candidate-count/orchestrator/tests/test_reflux_origin_ledger.py:2920) は元 payload の count を保持したまま第2 memberを tombstone に変えるため、合法セルでも `sealed_distinct_candidate_count=2` が残る。実際は distinct candidates=2、executed distinct candidates=1であり、decoder の拒否 [reflux_origin_ledger.py:1074](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-u4-candidate-count/orchestrator/campaign/reflux_origin_ledger.py:1074) が正しい。

matrix の合法性や decoder を緩めず、raw member列から3 countをテスト側で独立再計算する必要がある。production `_event_payload` の出力コピーによる修正は F27 型になる。

成果物影響: decoderを緩めて通すと、実行候補1件を2件と記録した event hash が proof chain と材料レポートへ固定される。

### R2-4 — must-fix: V07 の拒否理由期待が改名 closure から漏れている

[test_reflux_origin_ledger.py:1379](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-u4-candidate-count/orchestrator/tests/test_reflux_origin_ledger.py:1379) は `"batch minimum"` を期待するが、parser は `batch member row minimum` を label に渡し、`invalid batch member row minimum` を返す。[reflux_origin_ledger.py:320](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-u4-candidate-count/orchestrator/campaign/reflux_origin_ledger.py:320)

`Raises` を無条件化せず、期待文字列を新語彙へ正確に更新すべきである。

成果物影響: 未修正では受入テスト参照が赤のままとなり、certified 選択・試行台帳・proof chainをこの revisionへ束縛できない。

### R2-5 — must-fix: tombstone を含む origin-level count の分離がテストされていない

production は `sealed_member_row_count`、全 member の `origin_distinct_candidate_count`、非 tombstone の `origin_sealed_distinct_candidate_count` を分離している。[reflux_origin_ledger.py:1155](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-u4-candidate-count/orchestrator/campaign/reflux_origin_ledger.py:1155)

しかし `A,A,B(tombstoned)` テストは event/`SealedBatch` の `(3,2,1)` だけを確認し、snapshot・semantic objectを確認しない。[test_reflux_origin_ledger.py:4079](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-u4-candidate-count/orchestrator/tests/test_reflux_origin_ledger.py:4079) したがって、snapshotを非 tombstone unionに変える、または semantic countを相互に取り違える変異が生存する。混在例で semantic `(3,2,1)` と snapshot `2` を固定すべきである。

成果物影響: 試行台帳・材料レポートの origin候補数が2から1へ過小記録され、proof chainのsemantic commitmentも誤ったcountを束縛する。

## 独立検算・closure確認

更新 literal は production helperを使わず canonical JSON と SHA-256 から再計算し、次を確認した。

- sealed event SHA: `0924fe76119fcc5dffd0c0e5efa37ab25b51c6ee9a1ae1a432a1bf16deea9a05`
- reserve event SHA: `dfb3039e4d42e4b94c77096777cf59045a51a9b76c2920d406748cb599b9ce77`
- sealed frame: 2248行=`1,048,337`、2249行=`1,048,803`
- batch exact/conservative: 10行=`12,056/12,062`、100行=`93,869/93,872`、1000行=`911,972/911,972`
- decimal reserveは `3×(4−1)+2×(2−1)=11 bytes/batch`。33 batchでは qmax 73,717=`67,108,536`、73,718=`67,109,445`、上限=`67,108,864`。したがって実装側の 73,717/73,718 が正しく、段2見込みの73,718/73,719はT1の第3 count追加前の値である。

よって更新 golden に F27 型の自己参照は認めない。全171削除行も確認し、既存 assert の無補償削除、期待値反転、skip/xfail追加はなかった。

語彙走査では、触った2ファイルの完全一致 `"cardinality"` は [test_reflux_origin_ledger.py:2139](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-u4-candidate-count/orchestrator/tests/test_reflux_origin_ledger.py:2139) の1件だけ。ただしR2-1のとおり負例として不十分である。`_MAX_CLASS_CARDINALITY` は constraint class の数学的概念で意図的残存。独立 abandoned-frame helper は `member_row_count` へ追随済みである。

追加差分にT7の上限超過表現はない。D96の主要正負境界は存在するが、R2-1とR2-5によりテスト側の変更単位は未完成である。本レビューではpytestを実走していない。

## 総括

1. **NO-GO**
2. **must-fix: 5件**
3. **既存テスト期待値の弱体化はなし。** ただし最も重いテスト健全性欠陥は、旧codec形を再現せずalias復活を検出できないR2-1。