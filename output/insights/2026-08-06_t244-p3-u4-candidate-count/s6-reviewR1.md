NO-GO。静的検査で must-fix 6 件です。pytest は実走しておらず、実測結果は提示された request `892393.nqsv` を根拠にしています。

### R1-1 — must-fix

V18 の赤は、実装ではなくテスト入力の stale derived count が原因です。`raw_payload` は元の `accepted,rejected` payload（実行 distinct=2）をコピーした後、member だけ `tombstoned` に変え、`sealed_distinct_candidate_count` を2のまま残しています。[test_reflux_origin_ledger.py:2920](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-u4-candidate-count/orchestrator/tests/test_reflux_origin_ledger.py:2920)。decoder が非 tombstone member から1を再計算して拒否するのは裁定どおりです。[reflux_origin_ledger.py:1064](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-u4-candidate-count/orchestrator/campaign/reflux_origin_ledger.py:1064)。合法3セルという期待値は変えず、raw fixture の derived count を独立に再計算すべきです。

成果物影響: 未修正または期待値弱体化で回避すると、tombstone を含む event の実行候補数改竄を proof chain が拒否する防壁を検証できません。

### R1-2 — must-fix

V07 の赤は実装側の拒否理由 regression です。既存テストは `"batch minimum"` を固定していますが、parse は label を `"batch member row minimum"` に変えたため、実際の理由が `"invalid batch member row minimum"` となり既存 anchor を含みません。[reflux_origin_ledger.py:320](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-u4-candidate-count/orchestrator/campaign/reflux_origin_ledger.py:320)、[test_reflux_origin_ledger.py:1379](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-u4-candidate-count/orchestrator/tests/test_reflux_origin_ledger.py:1379)。テストを緩めず、実装理由を member-row 語彙かつ既存 anchor 互換に直すべきです。

成果物影響: 受理集合と値は不変ですが、試行台帳・proof-chain 診断が参照する拒否理由 literal が非互換になります。

### R1-3 — must-fix

liveness probe の赤は実装側の consumer 取り残しです。probe は旧 `batch_cardinality_min` のままなので、まず exact budget-key 検査で停止します。[liveness_probe.py:42](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-u4-candidate-count/output/insights/2026-08-05_t244-p3-liveness/liveness_probe.py:42)。これだけ直しても、次に旧 `reserved_cardinality` で停止します。[liveness_probe.py:178](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-u4-candidate-count/output/insights/2026-08-05_t244-p3-liveness/liveness_probe.py:178)。T6 再裁定は両者の追随を明示しています。[s4-adjudication.md:191](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t244-p3-u4-candidate-count/s4-adjudication.md:191)。wrapper test の期待値は正しいです。

成果物影響: probe receipt の6検査がすべて `NOT_RUN` のままとなり、試行台帳・proof chain の ledger mutation liveness 参照を成立させられません。

### R1-4 — must-fix

M10 を殺す旧-key負例が誤照準です。唯一の `"cardinality"` 負例は、新旧両 key を持つ `batch-sealed` payloadへ余分な keyを足すだけです。[test_reflux_origin_ledger.py:2136](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-u4-candidate-count/orchestrator/tests/test_reflux_origin_ledger.py:2136)。しかし旧 `cardinality` が存在したのは `batch-reserved` / `batch-committed` です。[reflux_origin_ledger.py:886](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-u4-candidate-count/orchestrator/campaign/reflux_origin_ledger.py:886)、[reflux_origin_ledger.py:916](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-u4-candidate-count/orchestrator/campaign/reflux_origin_ledger.py:916)。旧-only alias を受け入れ、両-key入力は拒否する M10 はこのテストを通過します。新 key を除いて旧 keyへ置換した負例が必要です。

成果物影響: raw codec の受理集合が旧 reserved/committed event へ拡大しても検出されず、proof-chain event schema の参照一意性が後段検査頼みになります。

### R1-5 — must-fix

既定値1でも、従来受理されていた「全 member tombstoned の batch＋別の実行済み batch」を拒否します。全 tombstone batch の `sealed_distinct_candidate_count` は0になり、[reflux_origin_ledger.py:1554](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-u4-candidate-count/orchestrator/campaign/reflux_origin_ledger.py:1554)、既定下限1の全 batch gate がそれを拒否します。[reflux_origin_ledger.py:1624](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-u4-candidate-count/orchestrator/campaign/reflux_origin_ledger.py:1624)。例えば `A(tombstoned),B(tombstoned)` の後に `C(accepted),D(accepted)` を置けば floor=2を満たし旧実装では certifiable でしたが、現実装では拒否されます。これは「明示下限2以上だけが受理集合を狭める」という plan と衝突します。[s2/plan.md:16](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t244-p3-u4-candidate-count/s2/plan.md:16)。現テストは `A,A` と混在 tombstone しか固定していません。

成果物影響: 該当試行の terminal acceptance が certifiable から拒否へ変わり、試行台帳と将来の proof-chain 受理集合が既定 policy のまま縮小します。

### R1-6 — must-fix（land 条件）

T2 の参照規則を記す新 D が現 working tree にありません。裁定は、候補数として参照可能なのは batch-local count と authority 下限だけであり、row counter や `len(members)` は不可と明記するよう要求しています。[s4-adjudication.md:52](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t244-p3-u4-candidate-count/s4-adjudication.md:52)。実装報告も docs/output を変更していないと明記しています。[impl.md:1](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t244-p3-u4-candidate-count/s5/impl.md:1)。親が後段で追加する予定でも、この2-file差分だけを land してはいけません。

成果物影響: 材料レポート・試行台帳・proof chain の consumer が `sealed_queries` や member数を候補数として再び参照でき、今回分離した値が誤読されます。

## 仕様・変異の静的照合

T1 の3 countと非 tombstone gate、T2 の snapshot field名、T3 の中央だけ悪い3 batch、T4 の parse境界、T5 の origin-wide union、T7 の名乗り上限、T8 の機械的改名、および plan v2 の codec/semantic双方の導出・decode再照合・3 countのpreseal除外はコード上存在します。未反映または不十分なのは R1-3、R1-4、R1-5、R1-6です。

| 変異 | 静的判定 | 識別する検査 |
|---|---|---|
| M01 | KILL | T1 の batch count `(3,2,1)` assertion |
| M02 | KILL | T3 の `(2,1,2)` 中央負例 |
| M03 | KILL | 同上。first batch は適格 |
| M04 | KILL | T1 の tombstone 負例 |
| M05 | KILL | D96 の explicit-min aborted 正例 |
| M06 | KILL | explicit `distinct == min` 正例、T1 low正例 |
| M07 | KILL | V15 の3 count単独改竄 |
| M08 | KILL | V16 の独立 prospective SHAとV20のpreseal等価性 |
| M09 | KILL | T4 の `candidate_min == member_min + 1` |
| M10 | **SURVIVE** | R1-4。現負例は旧-only aliasを通らない |
| M11 | KILL | V17 の2 batch同一候補 union=1 |
| M12 | KILL | V24 の affine byte literal |
| M13 | KILL | D96 の既定1・`A,A` certifiable正例 |

## 総括

1. **NO-GO**
2. **must-fix: 6件**
3. 既知の赤3件の root cause:

   - `test_v18_evidence_outcome_contract_and_fixed_member_tombstones`: test fixture 側。memberを tombstone に変えたのに derived countを更新していない。期待値は維持し、入力構築を直す。
   - `test_v07_batch_prefix_member_row_distinctness_and_single_inflight`: 実装側。拒否理由から既存 `"batch minimum"` anchorを消した。テストではなく実装理由を直す。
   - `test_t244_p3_liveness_probe_kills_registered_ledger_mutations`: 実装・consumer側。probeの旧 policy keyと旧 snapshot fieldが未追随。wrapper testは直さない。