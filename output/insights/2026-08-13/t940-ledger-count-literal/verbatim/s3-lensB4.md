## 総括

親の「39 件目で赤くなるのは件数 literal 2 箇所だけ」という実測は、通常の schema-valid な追加については概ね正しいです。ただし、実在する新違反の実効性確認、改名後の mutation spec、(a)(b)(d)(e) の変異帰属には未解決の穴があります。

親の `2 failed, 281 passed` は brief の実測結果として読みました。こちらでは pytest・mutation 本走は未実施です。Web 検索はしていません。T-940 固有の段 4 mutation spec / 受入 harness はまだ生成されておらず、読めませんでした。検索出力が一度大きくなったため、以後は対象ファイルを絞って確認しました。

### 1. 新しい実在違反の positive coverage — real

- 失敗シナリオ: 新 SHA が実際には違反を持つとして production 台帳と `expected` 表へ追加しても、現在の実在 commit 検査は固定 35 SHA だけです。新 SHA の kind/value が誤っていても、production と `expected` を同じ誤りで更新すれば赤くなりません。
- 根拠: production 台帳は [`tools/check_ai_provenance.py:225-569`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t940-ledger-count/tools/check_ai_provenance.py:225)、mirror は [`orchestrator/tests/test_check_ai_provenance.py:1386-1449`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t940-ledger-count/orchestrator/tests/test_check_ai_provenance.py:1386)。実在検査は固定リスト [`...:1459-1501`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t940-ledger-count/orchestrator/tests/test_check_ai_provenance.py:1459)で、production にある `187fed...`, `9408...`, `c968...` も対象外です。empty-registry も固定 30 件 [`...:2530-2567`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t940-ledger-count/orchestrator/tests/test_check_ai_provenance.py:2530)です。
- 直し方: 固定 35 件へ毎回追加するか、より適切には production の各 entry の SHA を個別に `_audit_history([sha])` へ通す独立 positive test を追加します。後者なら承認時の追加面は `expected` 表だけに保てます。内容完全一致は維持します。

### 2. 固定 35/30、stale、stdout が新 SHA で追加赤になるという読み — refuted

反証は checker の選択範囲です。`stale_eligible_commits` は `selected ∩ registry` [`tools/check_ai_provenance.py:1639-1646`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t940-ledger-count/tools/check_ai_provenance.py:1639)なので、固定リスト外の新 SHA は既存の 35/30 件検査へ影響しません。stale 系も synthetic registry を monkeypatch しています。

したがって、schema-valid・一意・固定リスト外の新 entry なら、変更後の直接赤は literal 表の node 一つだけです。これは「実在違反の positive coverage がある」こととは別問題です。

### 3. 他ファイル・stdout の件数 pin — refuted

`test_dev_wave_land.py` は fake checker の rc/reason/receipt を検査するだけで、台帳件数を pin していません（[`...:1250-1274`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t940-ledger-count/orchestrator/tests/test_dev_wave_land.py:1250)）。`test_hooks.py`、`test_check_docs.py`、docs 検査にも現行 38 件や対象 node の pin はありません。

stdout の `known-violations=` は registry 全体ではなく selected range の件数です（[`tools/check_ai_provenance.py:2560-2603`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t940-ledger-count/tools/check_ai_provenance.py:2560)）。既存テストの `=1` は synthetic または単一 SHA の出力 pin です（[`orchestrator/tests/test_check_ai_provenance.py:2446-2486`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t940-ledger-count/orchestrator/tests/test_check_ai_provenance.py:2446)、[`...:2630-2646`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t940-ledger-count/orchestrator/tests/test_check_ai_provenance.py:2630)）。削除対象ではありません。

### 4. P1 で `:1914` を含めること — refuted

「件数 literal 固定だけを外す」という裁定は行番号限定ではありません。原裁定も literal 固定と関数名の件数語を問題にしています（[`docs/archive/worklog-phase3-0812-488.md:573-577`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t940-ledger-count/docs/archive/worklog-phase3-0812-488.md:573)）。

実測でも新 entry 追加時に `:1448` と `:1914` の 2 node が赤くなっています（[`s1-brief.md:15-21`](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t940-ledger-count/s1-brief.md:15)）。`:1914` を残せば承認済み entry の追加で受入が止まり続けます。

`observed == expected` は全 5 field と長さを比較するため、literal assert を外しても受理集合は広がりません。

### 5. brief と plan の `:1914` 方針不一致 — real

- 失敗シナリオ: brief は `len(provenance.KNOWN_PROVENANCE_VIOLATIONS)` へ置換すると書いている一方（[`s1-brief.md:33-39`](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t940-ledger-count/s1-brief.md:33)）、plan は行削除を推奨しています（[`s2-plan.md:75-95`](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t940-ledger-count/s2-plan.md:75)）。段 4 の anchor と段 5 の実装がずれる可能性があります。
- 根拠: `tuple(registry.values()) == provenance.KNOWN_PROVENANCE_VIOLATIONS` 自体が長さと全値を比較します（現行 [`...:1911-1915`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t940-ledger-count/orchestrator/tests/test_check_ai_provenance.py:1911)）。
- 直し方: 段 4 前に裁定を固定してください。現実装では冗長な dynamic length assert を削除する方が明確です。どちらを選んでも内容一致は維持します。

### 6. nodeid 改名の外部 artifact 影響 — real

- 失敗シナリオ: 段 4 の `expected_nodes` が旧 `...is_exactly_thirty_eight_literal_entries` のままだと、現 harness は mutation 本走前の collection で旧 node が存在しないとして停止します。custom runner が collection を通す場合でも、新 node と旧 expected node の集合が一致せず MISMATCH になります。
- 根拠: 現行定義は [`orchestrator/tests/test_check_ai_provenance.py:1328`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t940-ledger-count/orchestrator/tests/test_check_ai_provenance.py:1328)。旧名は T-940 の brief/plan/handoff（`s1-brief.md:16`、`s2-plan.md:32`、`handoff.md:23`）と過去 wave の [`dev-wave-t316-r2-oracle/s9-kv.md:22`](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t316-r2-oracle/s9-kv.md:22) に残っています。harness は collection 実在確認を [`tools/mutation_harness.py:1137-1147`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t940-ledger-count/tools/mutation_harness.py:1137)で行い、kill 判定は集合完全一致です（[`...:1448-1450`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t940-ledger-count/tools/mutation_harness.py:1448)）。
- 直し方: active な mutation spec / handoff だけを新しい `test_known_violation_ledger_matches_literal_entries` へ更新し、collection を再確認してください。凍結された過去記録は改変しません。

現時点で T-940 固有の active mutation spec に旧 node が載っている証拠はありません。したがって現時点の受入 blocker ではなく、段 4 の登録 blocker です。

### 7. mutation 登録表の不足 — real

s2 plan の変異表は未知追加・note 変更・entry 削除の 3 件だけです（[`s2-plan.md:181-195`](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t940-ledger-count/s2-plan.md:181)）。ユーザー指定の (a)(b)(e) が未登録です。

直し方は、(a)(b)(e) を「KILLED」と偽らず、SURVIVED control または独立検査付き変異として段 4 spec に明記することです。

### 8. (a) 件数 literal の再導入 — real

- 失敗シナリオ: 現行 38 件の test source に `assert len(...) == 38` を戻しても、テスト動作は変わらず全テストがそのまま通る静的予測です。
- 根拠: 対象は test 自身の [`...:1328-1456`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t940-ledger-count/orchestrator/tests/test_check_ai_provenance.py:1328)であり、別の source-contract 検査はありません。harness の rc=0・失敗 node なしは SURVIVED です（[`tools/mutation_harness.py:1446-1450`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t940-ledger-count/tools/mutation_harness.py:1446)）。
- 直し方: 現状のままなら `expected_status=SURVIVED, expected_nodes=[]` として positive control にします。KILL を要求するなら、別 test/tool の AST/source-contract で絶対件数比較の再導入を検査します。関数名の旧名復元まで同じ変異に含めず、改名変異とは分離します。

### 9. (b) `observed == expected` の削除 — real

- 失敗シナリオ: この assert を削除しても、kind 集合検査と registry の自己比較は残ります。しかし `registry` は production 台帳から作られ、`tuple(registry.values()) == production` も同じ production 由来なので、test の `expected` と production の接続は消えます。
- 根拠: 削除対象は [`...:1449`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t940-ledger-count/orchestrator/tests/test_check_ai_provenance.py:1449)、自己比較は [`...:1915`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t940-ledger-count/orchestrator/tests/test_check_ai_provenance.py:1915)。固定 35 件も全 field の独立 golden ではありません。
- 直し方: 現状では SURVIVED と記録します。KILL が必要なら別層の source-contract、または独立 fixture で assert の存在を pin します。production と expected の二重 mirror をさらに増やすのは、更新面を不必要に増やすため避けます。

### 10. (c) 未知 entry の混入 — refuted（条件付き）

schema-valid、SHA 一意、expected 表を変更しない単独変異なら、変更後に赤くなるのは新しい literal-mirror node 一つです。

根拠は `observed` が production 全体を投影すること（[`...:1386-1394`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t940-ledger-count/orchestrator/tests/test_check_ai_provenance.py:1386)）と、registry の検証が別の entry を自動的に受理すること（[`tools/check_ai_provenance.py:591-617`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t940-ledger-count/tools/check_ai_provenance.py:591)）です。

invalid note、duplicate SHA、invalid kind を同時に混ぜると registry 検査が先に赤くなるため、mutation は単独・valid fixture として登録すべきです。

### 11. (d) 既存 note の 1 文字変更 — real

- 失敗シナリオ: 対象を `3f2c43d7580b...` にすると、literal mirror に加えて stdout の逐語検査も赤くなります。
- 根拠: primary は [`...:1449`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t940-ledger-count/orchestrator/tests/test_check_ai_provenance.py:1449)、`3f2c...` の note/stdout は [`...:2630-2646`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t940-ledger-count/orchestrator/tests/test_check_ai_provenance.py:2630)で pin されています。note の禁止文字等なら registry 検査 [`tools/check_ai_provenance.py:633-687`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t940-ledger-count/tools/check_ai_provenance.py:633)も追加されます。
- 直し方: 「既存 note」とだけ登録せず、対象 SHA と変更文字を固定してください。単一 node を期待するなら stdout pin のない `8ceebcd...` 等を使い、schema-valid な文字にします。`3f2c...` を使うなら expected_nodes は primary と stdout の 2 件です。

### 12. (e) duplicate SHA guard の削除 — real

- 失敗シナリオ: guard だけを削除しても、現 production の 38 entry は一意なので dictionary の結果は変わらず、変異は生存します。
- 根拠: guard は [`tools/check_ai_provenance.py:613-617`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t940-ledger-count/tools/check_ai_provenance.py:613)、production tuple は [`...:225-569`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t940-ledger-count/tools/check_ai_provenance.py:225)です。duplicate data を同時に注入しない限り guard の有無は観測できません。
- 直し方: synthetic duplicate SHA を monkeypatch して `_known_violation_registry()` が rc=2 相当で拒否する test を追加し、その node を expected にします。追加しない場合は guard削除を SURVIVED と登録します。guard削除と duplicate data 注入を一つの mutation にしないでください。

### 13. 承認済み entry 追加の更新面 — real

「expected 表だけ」は test 側だけなら正しいですが、repo 全体では正しくありません。

- 必須: production 台帳 [`tools/check_ai_provenance.py:225-569`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t940-ledger-count/tools/check_ai_provenance.py:225) と独立 mirror [`orchestrator/tests/test_check_ai_provenance.py:1396-1447`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t940-ledger-count/orchestrator/tests/test_check_ai_provenance.py:1396)。
- 現在は任意だが検出力上必要: 固定 35 件の実在 positive fixture。これを更新しない場合、受入は止まらないが新 entry の実在性を検査しません。
- 通常は不要: empty-registry の固定 30 件、stdout の `=1` fixture、docs、land/hooks/check_docs、CI/skip。これらは selected range または歴史的部分集合です。
- mutation 走だけの必須面: 改名後の active `expected_nodes`。旧 node のままだと受入 mutation が collection で停止します。

したがって「承認 entry 追加後の test maintenance は expected 表 1 箇所」は成り立ちますが、「repo 全体の更新が expected 表だけ」は成り立ちません。s2 plan 自身もこの区別を [`s2-plan.md:197-201`](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t940-ledger-count/s2-plan.md:197)で認めています。

### 14. 型 subclass による内容 oracle の回避 — real（現行 5 変異とは別の境界）

`_known_violation_registry()` は `tuple` / `str` / `KnownViolationSpec` の subclass を `isinstance` で受理します（[`tools/check_ai_provenance.py:591-603`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t940-ledger-count/tools/check_ai_provenance.py:591)）。悪意ある tuple subclass が test 側の iteration/equality だけで entry を隠し、checker 側には全 entry を返す形なら、`observed == expected` と registry 自己比較を欺けます。

通常の tuple literal 追加では発生しないため T-940 の通常 mutation ではありませんが、「内容完全一致が常に保たれる」という主張には穴があります。必要なら test 側で `type(KNOWN_PROVENANCE_VIOLATIONS) is tuple`、entry/field の exact type を検査してください。別 wave の scope とするなら、T-940 の検出力主張からは明確に除外してください。