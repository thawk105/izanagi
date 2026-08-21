## 所見一覧

1. `real / blocker`

   - 主張: `_load_adjudication` は task 非依存で無改修、という brief/plan の前提は誤り。
   - file:line 根拠: `tools/codex_reasoning_ab.py:5237` が `_validate_verdict_row` を呼び、`tools/codex_reasoning_ab.py:6447` が module 固定の `KNOWN_FINDINGS` を参照する。`KNOWN_FINDINGS` は `TASK_MANIFEST` 由来 (`:281-283`)。
   - 判定: `real / blocker`。custom manifest の `B-9` などは aggregate 到達前に unknown finding として拒否される。plan `s2-plan.md:55` の「全 task の union 検査」は、`_load_adjudication` に manifest を渡さない限り成立しない。

2. `real / blocker`

   - 主張: legacy schedule の受理後 row shape は byte 単位で維持されない。
   - file:line 根拠: 現行 `_validate_schedule` は raw row をそのまま返す (`tools/codex_reasoning_ab.py:5156`)。一方、normalizer は `benchmark_task_id`、`legacy_case`、`cache_condition`、`price_version` を追加する (`:2363-2377`, `:2400-2407`)。plan はさらに canonical fields を追加する (`s2-plan.md:38-42`)。
   - 判定: `real / blocker`。入力 schedule bytes は不変でも、返却 dict の key 集合は変わる。plan `s2-plan.md:60` の legacy projection は aggregate の一部だけで、schedule row projection を定義していない。

3. `unclear / major`

   - 主張: legacy schedule の schema version 互換化の呼び出し順が未確定。
   - file:line 根拠: 既存 fixture は `schema_version` なし (`orchestrator/tests/test_codex_reasoning_ab.py:320-348`)。`normalize_schedule` は version が `2` または `3` でないと拒否する (`tools/codex_reasoning_ab.py:2421-2429`)。plan は `expected_schedule_from_manifest(task_manifest, original_schedule)` と記載する (`s2-plan.md:29`)。
   - 判定: `unclear / major`。raw schedule を渡せば即拒否、compatibility view を渡せば受理される。plan は後者を明示していない。

4. `real / blocker`

   - 主張: task manifest の追加引数だけでは live task-specific replay/supervision へ到達できない。
   - file:line 根拠: `supervise_pair` は `_validate_schedule(schedule)` を固定呼出しする (`tools/codex_reasoning_ab.py:3699`)。`verify_manifest` も `_replay_manifest(manifest_path, sessions_root)` のまま (`:6277`)。さらに replay の snapshot 検証は default manifest を使う `verify_snapshot(..., case)` (`:6128`, `:2690`)。
   - 判定: `real / blocker`。plan `s2-plan.md:32,68-74` は caller plumbing を未定義のまま、alpha/beta は直接 helper を呼ぶテストでしか実行できない。

5. `real / major`

   - 主張: hard-code 一覧が `_validate_schedule` の POS/NEG gate を見落としている。
   - file:line 根拠: `tools/codex_reasoning_ab.py:5137-5154` は `scheduled_cases <= {"POS","NEG"}` のときだけ prompt/snapshot concentration と submodule state を検査する。
   - 判定: `real / major`。`legacy-alpha`/`legacy-beta` では条件が false になり、検査が丸ごと無効になる。plan `s2-plan.md:102-107` の「残存 POS/NEG は未処理漏れでない」は成立しない。

6. `real / major`

   - 主張: 既存 replay test は task_manifest keyword の透過で壊れうる。
   - file:line 根拠: `test_replay_passes_schedule_requested_model_to_collect_run` は一引数の monkeypatch を定義する (`orchestrator/tests/test_codex_reasoning_ab.py:6018-6020`)。plan は `_replay_manifest` に keyword-only manifest を追加する (`s2-plan.md:68-74`)。
   - 判定: `real / major`。`_validate_schedule(schedule, task_manifest=...)` を常時呼ぶと既存 fake が `TypeError` になる。plan `s2-plan.md:131-132` の「既存 test を維持」と矛盾する。

7. `refuted / minor`

   - 主張: canonical fields の追加だけで `supervise_pair` の既存 consumer が直ちに壊れる。
   - file:line 根拠: `supervise_pair` は `case`、`arm`、block fields だけを読む (`tools/codex_reasoning_ab.py:3702-3718`)。`_supervise_one` も明示 key だけを読む (`:3408-3411`)。
   - 判定: `refuted / minor`。dict の未知 key を拒否する検査はなく、追加 field 自体は pass-through できる。ただし次項の通り、case だけの検査では新 dimension の正しさまでは保証しない。

8. `unclear / major`

   - 主張: block 内一意性は新 schema でも安全に維持される。
   - file:line 根拠: `supervise_pair` の block 検査は `case` の一致だけ (`tools/codex_reasoning_ab.py:3706-3707`)。supervisor ledger も `block_id/block_order/case/arm` だけを比較する (`:5742`)。plan は validator 側に task/stage/cache/price 検査を寄せる (`s2-plan.md:30`)。
   - 判定: `unclear / major`。validator が全 dimension を厳密比較すれば動くが、その負例テストが test plan にない。validator の一欠落で異なる stage/cache/price の pair を Wave C consumer が受理する。

9. `real / major`

   - 主張: legacy aggregate output も byte 単位で非破壊。
   - file:line 根拠: 現行 resource row の key 集合は `tools/codex_reasoning_ab.py:5630-5645`。plan はそこへ5つの canonical fields を追加する (`s2-plan.md:58`)。既存 test は resource row の件数しか確認しない (`orchestrator/tests/test_codex_reasoning_ab.py:5866`)。
   - 判定: `real / major`。`primary` 等の旧 projection を残しても `resource_ledger` の各 dict shape は変わる。token output も exact equality assertion (`:6687-6695`) があり、axis ledger の追加位置次第で破壊される。

10. `refuted / minor`

   - 主張: `oracle_kind` 化で legacy POS/NEG の意味が逆転する。
   - file:line 根拠: `TASK_MANIFEST["tasks"]["POS"]["oracle_kind"] == "positive"`、NEG は `"negative"` (`tools/codex_reasoning_ab.py:209-214`)。`grep -n oracle_kind` の他の実使用も positive/negative と整合している (`:2537`, `:2582`)。
   - 判定: `refuted / minor`。正しい canonical lookup と compatibility fallback を実装すれば、`POS_PRIMARY` と `NEG_ADJUDICATED_FALSE_FINDING` の legacy 意味は維持できる。

11. `unclear / major`

   - 主張: 既存の変異 matrix 17/17 KILLED は今回の decision rewrite にそのまま帰属できる。
   - file:line 根拠: 現行 decision 分岐は `:5587-5619`、既存 label assertion は `orchestrator/tests/test_codex_reasoning_ab.py:6845-6865`。plan は複数 task axis ledger と旧 label を同時に導入する (`s2-plan.md:53-60`)。
   - 判定: `unclear / major`。legacy の4分岐が残っていても、複数 oracle task を一つの decision label にどう射影するかが未定義。D603/D614 の過去 9/9 と 8/8 は旧構造の実績であり、今回の label、axis、allowlist 変更の kill 帰属を証明しない。

12. `refuted / minor`

   - 主張: plan は D614 の Wave C 所有境界を超えている。
   - file:line 根拠: D614 は `_replay_manifest` の `collect_run` 呼出し `expected_requested_model` だけを許可した (`docs/decisions.md:24631-24637`)。現行の該当行は `tools/codex_reasoning_ab.py:6134-6145` で、plan も変更しないとしている (`s2-plan.md:70-73`)。
   - 判定: `refuted / minor`。plan の aggregate/replay 内部変更は Wave D 所有面内であり、`supervise_pair`、`collect_run`、launch schema は触らない。ただし `collect_run` は CLI 側にも別 call site (`:6840`) があるため、D614 の「唯一の呼出し箇所」は文字通りには不正確である。

13. `real / major`

   - 主張: brief の G04 不適用という判断は確定している。
   - file:line 根拠: `validate_nullable_dimensions` は live `_validate_schedule` から未接続だと明記されている (`tools/codex_reasoning_ab.py:2305-2321`)。plan はこれを live path に接続し、version、model、cache、price の新しい reject gate を発火させる (`s2-plan.md:23-29`)。brief は G04 を不適用としている (`s1-brief.md:172-176`)。
   - 判定: `real / major`。既存 field の配線でも、受理集合を変える live gate の新設である。発火条件、拒否集合、legacy projection を裁定なしに「既存検査」と扱うのは危険。

## brief への異議

- `_load_adjudication` が task 非依存という記述 (`s1-brief.md:11-14`) は、間接呼出しの `KNOWN_FINDINGS` 検査を落としている。
- 「既存 POS/NEG を byte 同一で維持する」不変条件 (`s1-brief.md:130-131`) と、正規化済み row/resource を返す plan は両立していない。
- G04 不適用 (`s1-brief.md:172-176`) は、未接続だった fail-closed gate を live path へ配線する事実を過小評価している。
- D614 の所有境界自体は、現行 call site と plan の変更範囲に照らして概ね正確。

## plan への異議

- `_load_adjudication` と `_validate_verdict_row` へ task manifest の known-finding union をどう渡すかを明示すべき。
- legacy raw view と canonical internal view を分離し、row/resource/token の exact projection をテストで固定すべき。
- custom manifest を `supervise_pair`、`verify_manifest`、`verify_snapshot` まで伝播するか、task-specific live path を scope 外と明記すべき。
- POS/NEG concentration gate と dynamic block mismatch の負例を追加すべき。
- 既存 monkeypatch の keyword 互換と、decision label の複数 task projection を定義すべき。

## 総括

最重要 blocker は、`_load_adjudication` が実際には global `KNOWN_FINDINGS` に依存し、task-specific verdict を aggregate 前に拒否する点である。  
次の blocker は、legacy schedule を canonical row として返す設計が、brief の byte-level 非破壊主張と両立しない点である。  
custom task manifest は内部 helper に注入できても、live supervisor、replay、snapshot oracle へ届かず、実経路として未閉包である。  
`supervise_pair` の追加 key pass-through 自体は壊れないが、case-only 検査は新 dimension の安全性を保証しない。  
oracle_kind の POS/NEG 対応そのものは正しいが、過去の 17/17 mutation 実績を今回の decision schemaへ移せる根拠はない。  
D614 境界の越境は確認できず、今回の主な問題は境界違反ではなく、task/generalization と legacy compatibility の未閉包である。  
これは静的検査のみの結論であり、pytest は実行していない。