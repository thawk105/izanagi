結論は **NO-GO**。pytest は実行していない。以下の「同じ結果になる」は静的にテストの識別力を評価したもので、実走結果ではない。

`docs/failures.md` の型タグ一覧、とくに [恒真ゲート]・[テスト代表性]（[F9](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-u4-candidate-count/docs/failures.md:115)、[F21](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-u4-candidate-count/docs/failures.md:274)、[F28](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-u4-candidate-count/docs/failures.md:466)）、前提一般化の F29、pin 閉包の F30/F39 を攻撃面に含めた。

## 所見

### A-1 — real — U-4 の誤読経路が別の公開 field に残る

親 brief は誤読元を `cardinality / sealed_queries` と明記しているが、改名対象は `cardinality` だけである（[brief.md:17](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t244-p3-u4-candidate-count/brief.md:17)、[brief.md:51](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t244-p3-u4-candidate-count/brief.md:51)）。プランはさらに、同名の `distinct_candidate_count` を origin-wide な `OriginSnapshot` と batch-local な `SealedBatch` の両方へ置く（[plan.md:67](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t244-p3-u4-candidate-count/s2/plan.md:67)、[plan.md:68](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t244-p3-u4-candidate-count/s2/plan.md:68)）。

現在の公開面には `OriginSealed.sealed_queries`、`OriginSnapshot.queries_used/sealed_queries`、`len(SealedBatch.members)` が残る（[ledger.py:537](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-u4-candidate-count/orchestrator/campaign/reflux_origin_ledger.py:537)、[ledger.py:559](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-u4-candidate-count/orchestrator/campaign/reflux_origin_ledger.py:559)、[ledger.py:581](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-u4-candidate-count/orchestrator/campaign/reflux_origin_ledger.py:581)）。行数である旨の文字列は class 冒頭の docstring ではなく、実際の `__doc__` に残らない位置にある。しかも既定値1の `A,A` を certifiable seal まで受理することが明示されている（[plan.md:207](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t244-p3-u4-candidate-count/s2/plan.md:207)）。

したがって将来 consumer が `terminal_status == certifiable && sealed_queries >= 2`、または origin-wide count を batch count と読めば、同じ誤認が再現する。少なくとも `sealed_member_row_count`、`origin_distinct_candidate_count` のように scope を名前へ焼き込み、新 D で P4 consumer が参照してよいのは batch-local count だけと固定すべきである。

**成果物影響:** 現在値は production entry 0 件なので不変だが、将来の certified 選択・材料レポート・試行台帳・proof chain が単一候補 × replicate を候補2点以上として受理・参照しうる。

### A-2 — real — `any` の全 batch 検査をテストが束縛していない

推奨 gate は全 sealed batch に対する `any(...)` である（[plan.md:43](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t244-p3-u4-candidate-count/s2/plan.md:43)）。しかし複数 batch 負例は `A,A` と `B,B`、すなわち両方とも不適格である（[plan.md:221](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t244-p3-u4-candidate-count/s2/plan.md:221)）。

この入力では、次の誤実装も正しい gate と同じく拒否する。

- `all(batch_is_below_minimum)`
- 最初の batch だけ検査
- 最後の batch だけ検査
- 「適格 batch が1件もない場合だけ拒否」

`good(A,B) → bad(C,C) → good(B,D)` の3 batchを置き、中央の1件だけを理由に certifiable seal が拒否される負例が必要である。これは `all`、first-only、last-only を一度に殺せる。

**成果物影響:** authority が下限2を明示しても、不適格 batch を適格 batch の間へ置くと certifiable 選択が受理され、材料レポート・台帳・proof chain の batch 集合が不正に拡大する。

### A-3 — real — 実現不能な candidate minimum を authority が受理できる

候補 IR は正準5 bitで、候補空間は厳密に32点である（[reflux_ir.py:36](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-u4-candidate-count/orchestrator/campaign/reflux_ir.py:36)、[reflux_ir.py:113](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-u4-candidate-count/orchestrator/campaign/reflux_ir.py:113)）。プラン自身も feasibility frame で最大32種を使う（[plan.md:79](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t244-p3-u4-candidate-count/s2/plan.md:79)）。

一方、policy 編集点は candidate minimum の下限1しか指定せず（[plan.md:63](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t244-p3-u4-candidate-count/s2/plan.md:63)）、feasibility 更新も member minimum しか挙げていない（[plan.md:81](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t244-p3-u4-candidate-count/s2/plan.md:81)）。このままなら `candidate_min=33`、または `candidate_min=9, qmax=8` の authority を parse できる一方、certifiable seal は構成不能になる。現行コードは同種の不可能な member/floor policy を parse 時に拒否している（[ledger.py:313](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-u4-candidate-count/orchestrator/campaign/reflux_origin_ledger.py:313)、[ledger.py:2163](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-u4-candidate-count/orchestrator/campaign/reflux_origin_ledger.py:2163)）。

`candidate_min <= 32` かつ `candidate_min <= qmax` を authority feasibility に加え、32/33 と qmax-1/qmax+1 の正負境界を置く必要がある。

**成果物影響:** 実現不能 authority を受理した試行は certifiable 選択の受理集合が空になり、材料レポート・試行台帳・proof chain が abort または未終端参照へ固定される。

### A-4 — real — 「tombstone も候補数へ含める」が赤くならない

プランは tombstone を含む全 member から候補数を数えると規定する（[plan.md:53](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t244-p3-u4-candidate-count/s2/plan.md:53)）。しかし D96 テスト群には tombstoned candidate の count 境界がなく、既存 V18 の混在例も row 長と outcome しか検査していない（[test.py:2902](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-u4-candidate-count/orchestrator/tests/test_reflux_origin_ledger.py:2902)、[test.py:2915](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-u4-candidate-count/orchestrator/tests/test_reflux_origin_ledger.py:2915)）。プランのテスト編集表にも V18 はない。

現行 reducer は `sealed_count` と `tombstoned_count` を分けるため（[ledger.py:1440](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-u4-candidate-count/orchestrator/campaign/reflux_origin_ledger.py:1440)）、誤って「非 tombstone candidate だけ」を数える実装は自然に入りうる。`A=accepted, B=tombstoned` で event/batch/snapshot の member=2、distinct=2を固定する必要がある。

**成果物影響:** distinct count が1へ過少記録され、authority 下限2の正当な batch が拒否されるため、certified 選択の受理集合が縮み、レポート・台帳・proof chain の候補数も不一致になる。

### A-5 — 疑い — origin-wide union の期待値が V17 に明記されていない

`OriginSnapshot` は `len(replicate_counts)`、すなわち origin-wide union を返す計画である（[plan.md:71](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t244-p3-u4-candidate-count/s2/plan.md:71)）。既存 V17 は同じ候補 A を2 batchに跨って反復するため、union=1、batch-local sum=2を区別できる良い負例である（[test.py:2600](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-u4-candidate-count/orchestrator/tests/test_reflux_origin_ledger.py:2600)、[test.py:2606](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-u4-candidate-count/orchestrator/tests/test_reflux_origin_ledger.py:2606)）。

ただしプランは「公開 count の中心境界へ拡張」とだけ書き、`snapshot.distinct_candidate_count == 1`、各 `SealedBatch == 1`、各 event == 1 を明記していない（[plan.md:194](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t244-p3-u4-candidate-count/s2/plan.md:194)）。これらを明記して実装されるなら本疑いは refuted となる。

**成果物影響:** snapshot が batch-local count の総和2を返すと、将来の材料レポート・試行台帳・proof chain が origin の候補集合を水増しする。

## 受理集合の具体照合

- 無条件に単一候補 batch を `BatchSealed` で拒否する実装は、既存 V17 の `A,A` 反復正例（[test.py:2600](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-u4-candidate-count/orchestrator/tests/test_reflux_origin_ledger.py:2600)）を落とす。
- 既存テストには単一候補の certifiable `OriginSealed` 正例がない。したがってプランの I3 default 正例は必要であり、省けない。
- V14、V16、V34 の certifiable 正例は既定の `A,B` を使うため、意図した実装では維持される（[test.py:1963](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-u4-candidate-count/orchestrator/tests/test_reflux_origin_ledger.py:1963)、[test.py:2239](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-u4-candidate-count/orchestrator/tests/test_reflux_origin_ledger.py:2239)、[test.py:3705](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-u4-candidate-count/orchestrator/tests/test_reflux_origin_ledger.py:3705)）。
- 旧 payload key の拒否と新 key の受理はプランが明示した raw codec 受理集合の置換で、意図しない拡大ではない。A-3 の実現不能 policy 受理は意図しない拡大である。

## M1〜M7 の独立裏取り

| 前提 | 判定 | 独立確認 |
|---|---|---|
| M1 | 反証なし | tracked Python を検索し、test/probe と ledger 自身以外に import/call はない。現行 P3 driver は `reflux_ir` のみ importする（[p3 driver:45](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-u4-candidate-count/orchestrator/campaign/p3_autonomous_workload_trial.py:45)）。 |
| M2 | 反証なし | authority は `origins:[]`（[authority:1](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-u4-candidate-count/orchestrator/campaign/reflux_origin_authority_v2.json:1)）、production 初期化は明示拒否（[ledger.py:2781](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-u4-candidate-count/orchestrator/campaign/reflux_origin_ledger.py:2781)）。 |
| M3 | 反証なし | opening と sealed member が候補 bytes を保持し（[ledger.py:482](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-u4-candidate-count/orchestrator/campaign/reflux_origin_ledger.py:482)、[ledger.py:495](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-u4-candidate-count/orchestrator/campaign/reflux_origin_ledger.py:495)）、seal 受理時に正準検査後 `replicate_counts` へ入る（[ledger.py:1394](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-u4-candidate-count/orchestrator/campaign/reflux_origin_ledger.py:1394)、[ledger.py:1467](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-u4-candidate-count/orchestrator/campaign/reflux_origin_ledger.py:1467)）。 |
| M4 | 反証なし | preimage は candidate/query/replicate（[ledger.py:635](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-u4-candidate-count/orchestrator/campaign/reflux_origin_ledger.py:635)）、salt は外側で加わる（[ledger.py:621](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-u4-candidate-count/orchestrator/campaign/reflux_origin_ledger.py:621)）。検査対象は commitment 集合だけ（[ledger.py:1283](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-u4-candidate-count/orchestrator/campaign/reflux_origin_ledger.py:1283)）。 |
| M5 | 反証なし | P4 consumer はなく、現在の certifiable gate は query floor（[ledger.py:1497](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-u4-candidate-count/orchestrator/campaign/reflux_origin_ledger.py:1497)）。 |
| M6 | 反証なし | 23件の frozen manifest に ledger/authority はなく（[test_frozen_artifacts.py:38](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-u4-candidate-count/orchestrator/tests/test_frozen_artifacts.py:38)）、runtime は git-common-dir 配下（[ledger.py:1615](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-u4-candidate-count/orchestrator/campaign/reflux_origin_ledger.py:1615)）。実 checkout に runtime store と source SHA pin は見つからなかった。 |
| M7 | 反証なし | registry 空・runtime 不在のため、D189 と同じ「再解釈対象なし」は成立する。schema/domain は現行 v2（[ledger.py:74](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-u4-candidate-count/orchestrator/campaign/reflux_origin_ledger.py:74)）。 |

なお、プランの codec 数値（1,048,300/1,048,766、12,019/93,832/911,935、67,108,224/67,109,133）は独立算術と一致した。

## nit

- `BatchSealed` の入力 shape が将来も `batch_id + members` だけであることを、`dataclasses.fields` の exact assertion で固定すると自己申告 field の混入を早期検出できる。現状は [ledger.py:531](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-u4-candidate-count/orchestrator/campaign/reflux_origin_ledger.py:531) の2 fieldだが、D96テストには構造 assertion が明記されていない。
- M4 の「異なる preimage なら commitment は必ず全異」は暗号学的には言い過ぎである。実際の保証は、受理された commit が commitment 重複検査を通っていること。M4 の結論自体は変わらない。

## 裁定パッケージ候補

P4 consumer、origin-proofs sidecar、report v3 の実装は要求しない。ただし、それらが batch-local count と authority minimum を必須参照するまで「U-4 全体を閉じた」とは名乗れない。この残余は新 D に明記し、今回の名乗りを「記録形分離と conditional gate」へ限定する必要がある。

## 総括

1. **NO-GO**
2. **must-fix 4件**（A-1〜A-4。A-5は明示 assertion が入れば refuted）
3. 最も重い所見は **A-2**。現行テスト案では `all`・first-only・last-only の誤 gate が同じ拒否結果になり、authority が明示した per-batch 防壁を実際に迂回できる。