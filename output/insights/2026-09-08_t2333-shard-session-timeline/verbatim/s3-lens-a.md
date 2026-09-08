## 総括

plan は現状のままでは不可です。`merge_reports` の未知 top-level field 拒否と D1620 の測定面は維持していますが、`session_timeline` を必須化し、その内容を検査して `INFRA_RC` にする設計は、D1647 の「gate・判定・受理集合には触れない」と正面から衝突します。

また、collection 終了時刻の採取位置が実際の hook chain より早く、親 brief 自体にも「受理集合を変えない」と「受理集合が変わる」の矛盾があります。静的検査のみ実施し、file 編集、commit、pytest 実行はしていません。

## must-fix

1. **`session_timeline` の必須化が受理集合を変更する。**

   現在は [`set(report) != _REPORT_FIELDS`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2333-shard-timeline/tools/acceptance_shards.py:618) が厳密一致を要求します。plan は [`session_timeline` を `_REPORT_FIELDS` の必須要素にする](/home/SFC/tanab/.claude/jobs/9b50de3a/tmp/artifacts/t2333-shard-timeline/plan.md:175)ため、従来受理された同じ `SCHEMA` の report は key 欠落で `report-invalid` になります。これは D1647 の明文である[「gate・判定・受理集合には触れず」](/home/SFC/tanab/.claude/jobs/9b50de3a/tmp/artifacts/t2333-shard-timeline/verbatim-rulings.md:3)に反します。

   さらに plan は、欠測、空の `workers`、NaN、infinity、key 不足を [`validate_report_evidence`](/home/SFC/tanab/.claude/jobs/9b50de3a/tmp/artifacts/t2333-shard-timeline/plan.md:181) から拒否します。有限性と非空性は単なる形ではなく値と cardinality の条件です。既存の「診断 payload 検査」と呼び替えても、新しい観測内容によって merge verdict が変わる点は同じです。[欠落を `report-invalid` と期待するテスト](/home/SFC/tanab/.claude/jobs/9b50de3a/tmp/artifacts/t2333-shard-timeline/plan.md:214)も違反を固定してしまいます。

   成果物への影響: 旧形式、欠測、または malformed な観測だけを持つ report が、既存 6 gate を満たしていても certified 受理から除外されます。

2. **collection 終了時刻の採取位置が実際の collection 終了ではない。**

   acceptance plugin の hook は [`trylast=True`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2333-shard-timeline/tools/acceptance_shards.py:825) ですが、conftest 側は wrapper です。acceptance hook が戻った後にも、conftest は [`_validate_real_repo_shard_state`、suffix strip、duration reorder](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2333-shard-timeline/orchestrator/tests/conftest.py:2065)を実行します。plan の [`setattr` 直後に `time.time()` を取る案](/home/SFC/tanab/.claude/jobs/9b50de3a/tmp/artifacts/t2333-shard-timeline/plan.md:93)はこれらより早く、plan 自身も[その差を認めています](/home/SFC/tanab/.claude/jobs/9b50de3a/tmp/artifacts/t2333-shard-timeline/plan.md:250)。親 brief の「同関数末尾」指定も誤った境界です。

   成果物への影響: `collection_finished_epoch_s` が実際より早い値になり、suffix 処理や LPT reorder の時間が collection 後の空白として report に誤記録されます。

3. **観測の欠測や採取例外が既存の受入結果を落とす。**

   controller の report 組立は [`except Exception` で `session.exitstatus = INFRA_RC`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2333-shard-timeline/tools/acceptance_shards.py:1024) に変換されます。plan がこの try 内へ worker payload の `max`、worker ID 結合、timeline 組立を追加するため、欠落した collection 値、空集合、型不一致、対応 worker 不在などの観測側エラーだけで rc 16 になります。

   xdist worker の [`_worker_payload` 呼出しは try の外](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2333-shard-timeline/tools/acceptance_shards.py:960)です。新 key を直接読む実装では欠測がそのまま hook 例外になります。また、plan の `float(report.start)` と `float(report.stop)` は missing、非数値、巨大整数で `AttributeError`、`ValueError`、`OverflowError` を投げ得ます。特に [`merge_reports` の捕捉対象](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2333-shard-timeline/tools/acceptance_shards.py:635)に `OverflowError` はありませんが、テスト計画は NaN と infinity だけです。

   成果物への影響: test、scheduler、既存 evidence が同一でも、timeline の採取または変換失敗だけで shard report が生成されないか certified verdict が rc 16 になります。

4. **追加 test 数と duration ledger の扱いが未解決で、plan の所有 file 集合が自己矛盾している。**

   plan は[変更を 3 file に限定](/home/SFC/tanab/.claude/jobs/9b50de3a/tmp/artifacts/t2333-shard-timeline/plan.md:5)しつつ、[12 test function と parametrize 展開](/home/SFC/tanab/.claude/jobs/9b50de3a/tmp/artifacts/t2333-shard-timeline/plan.md:208)を追加します。一方、addendum は既存計測が正しければ[未登録 node の余裕は 7 件](/home/SFC/tanab/.claude/jobs/9b50de3a/tmp/artifacts/t2333-shard-timeline/brief-addendum.md:15)であり ledger 更新が必要としています。

   ただし、親の stdout 行カウントが権威 test の `consumer_keys` と同一集合である証明はありません。実装側には path 解決と group suffix 除去を行う[専用 nodeid 正規化](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2333-shard-timeline/orchestrator/tests/conftest.py:1513)があります。したがって「余裕 7」は provisional のままであり、同時に plan から ledger を除外する根拠にも使えません。

   成果物への影響: 7 件という値が正しければ coverage test が赤になり、誤って ledger を更新すれば duration 値と LPT 順序が変わります。

5. **テスト計画が重要な誤実装を殺さない。**

   次の mutation は、列挙されたテストのままでは緑になり得ます。

   - collection clock を outer wrapper の unwind 前に取る。
   - acceptance 中の `access is None` でも clock read と interval 記録を行う。plan の no-op test は recorder の spec/state 不在だけで、timing wrapper のこの分岐を検査しません。
   - lock acquire failure または release failureでも complete interval を append する。plan は両動作を約束していますが、対応 test はありません。
   - 巨大 JSON integer の有限性検査で `OverflowError` を外へ漏らす。
   - final writer に完成済み synthetic state を渡すテストだけ通し、実際の collection hook から timestamp が届かない。

   成果物への影響: collection 境界の誤値、取得していない lock interval、失敗した release の成功記録、または report merge の例外が回帰テストを通過します。

## nit

- `SCHEMA` を v1 のままにしながら必須 shape を変える説明は弱いです。主たる問題は D1647 違反ですが、同じ schema label の旧 report が拒否される点も明記すべきです。
- 親の blob SHA 検索が証明するのは、2 個の Git blob OID が文字列として置かれていないことだけです。実際の blob ID は brief 記載値と一致しましたが、[`acceptance_shards.py` 全体を AST または source text で検査するテスト](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2333-shard-timeline/orchestrator/tests/test_run_tests_shards.py:1365)は存在します。現 plan はその条件を破っていませんが、「内容束縛が無い」まで一般化はできません。
- plan の xdist test は synthetic report を直接 hook に渡すため、xdist transport 自体の回帰テストではありません。今回は pytest 9.1.1 の復元実装を静的確認できたため前提は成立しますが、test 単体の証明範囲は限定的です。
- brief の成果物には worklog と decisions fragment が含まれますが、plan の「3 file に限定」と整合していません。

## plan の前提のうち実物と食い違う点

- [brief の D1647 要約](/home/SFC/tanab/.claude/jobs/9b50de3a/tmp/artifacts/t2333-shard-timeline/brief.md:11)は受理集合不変を要求しますが、同じ brief は[P1-a で新 field を必須化](/home/SFC/tanab/.claude/jobs/9b50de3a/tmp/artifacts/t2333-shard-timeline/brief.md:33)し、末尾では[受理集合が変わると明記](/home/SFC/tanab/.claude/jobs/9b50de3a/tmp/artifacts/t2333-shard-timeline/brief.md:71)しています。親 brief 自体の矛盾です。
- brief の「追加 field 自体では `validate_report_evidence` が赤にしない」は狭い意味では正しいものの、現物ではその前に top-level 厳密一致が走るため、`_REPORT_FIELDS` 未変更の追加 field は直ちに赤です。
- 「`pytest_collection_modifyitems` 末尾が collection 終了」という前提は、conftest wrapper の yield 後処理と食い違います。
- addendum が指定する `_report_from_json` という module-level 関数は pytest 9.1.1 にはありません。実物は `pytest_report_from_serializable` から `TestReport._from_json` を呼びます。
- plan の変更対象 3 file は、addendum が主張する ledger 更新と両立しません。
- 「余裕 7」は計算式自体は正しいですが、権威 test と同じ `consumer_keys` を数えた証拠がなく、権威値としては未確定です。

## 攻撃したが破れなかった点

- plan は `set(report) != _REPORT_FIELDS` を部分集合判定へ緩めません。したがって、任意の未知 top-level key、偽の shadow field、未承認の receipt fieldを持つ report が新たに通る設計ではありません。
- `merge_reports` の既存 6 gate、pytest rc 合成、scheduler 判定、`MergeResult` には timeline を流していません。問題はそれ以前の新 schema/timeline 検査です。
- receipt field と `tools/dev_wave_wait.py` の production 経路は変更対象に含まれず、D1620 の「最遅 shard の wall」という測定面は静的には維持されています。
- pytest 9.1.1 の復元経路は dict を `TestReport` constructor へ渡し、constructor は `start` と `stop` を明示的に復元します。`worker_id` なども `**extra` で保持されます。したがって P1-b の「新しい custom transport は不要」という結論は破れませんでした。
- serial 時の `"serial"` は現行 [`pytest_runtest_logreport`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2333-shard-timeline/tools/acceptance_shards.py:862)の既存表現と一致します。
- `_real_repo_locks` は[P、S の全対象 lock を取得してから yield し、逆順に解放](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2333-shard-timeline/orchestrator/tests/conftest.py:1347)するため、その context 全体の外側で時刻を取る境界方針自体は妥当です。
- plan は receipt や wall を timeline と比較する判定、前後関係、閾値、所要時間 gate を追加していません。数値順序を逆転しても既存 verdict が変わらないテスト方針も、この限定点では有効です。