## caller と fixture の全列挙

変更関数は [`_verification_source_disclosure`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2409-wal-verdict-bind/orchestrator/campaign/b10_backoff_shape_sweep.py:3359) です。worktree 全体の完全一致検索結果は次のとおりです。

production caller:

- [`_collect_report_inputs`:3600](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2409-wal-verdict-bind/orchestrator/campaign/b10_backoff_shape_sweep.py:3600) が唯一の直接 caller。3541 行の workload loop により write-heavy、balanced、read-heavy の各 1 回、計 3 回呼びます。
- production 経路は [`main`:4270](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2409-wal-verdict-bind/orchestrator/campaign/b10_backoff_shape_sweep.py:4270) → `run_formal` → report 分岐の [`_collect_report_inputs`:3985](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2409-wal-verdict-bind/orchestrator/campaign/b10_backoff_shape_sweep.py:3985) → 3600 行です。他の production caller はありません。

test caller / reference:

- [`test_report_collector_reads_only_three_formal_series_and_discloses_sources`:2601](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2409-wal-verdict-bind/orchestrator/tests/test_b10_backoff_shape_sweep.py:2601): 関数を monkeypatch し、2616 行で collector を呼ぶため、変更関数本体は通りません。
- [`test_verification_completeness_counts_records_and_discloses_wal_anomalies`:2779](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2409-wal-verdict-bind/orchestrator/tests/test_b10_backoff_shape_sweep.py:2779): 既存の直接 caller。`read_source` を 2787、2788 行から計 2 回呼びます。
- [`test_legacy_verify_done_verdict_accepts_exact_values_and_extra_payload`:2908](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2409-wal-verdict-bind/orchestrator/tests/test_b10_backoff_shape_sweep.py:2908): 新規直接 caller、1 node。
- [`test_legacy_verify_done_verdict_rejects_field_mutation`:2960](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2409-wal-verdict-bind/orchestrator/tests/test_b10_backoff_shape_sweep.py:2960): 新規直接 caller、8 node。
- [`test_legacy_verify_done_verdict_is_checked_before_disclosure_filter`:2988](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2409-wal-verdict-bind/orchestrator/tests/test_b10_backoff_shape_sweep.py:2988): 新規直接 caller、2 node。
- [`test_report_collector_accepts_exact_legacy_verdict_fixture`:3081](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2409-wal-verdict-bind/orchestrator/tests/test_b10_backoff_shape_sweep.py:3081): collector 経由の新規 caller。変更関数を 3 workload 分通します。

fixture / helper の共有先:

- 既存 test のローカル helper `read_source` は 2757 行で定義され、同じ test 内の 2787、2788 行だけから使われます。3 field の追加は [`2769-2771`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2409-wal-verdict-bind/orchestrator/tests/test_b10_backoff_shape_sweep.py:2769) のみです。
- 新規 [`_write_legacy_verdict_wal`:2859](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2409-wal-verdict-bind/orchestrator/tests/test_b10_backoff_shape_sweep.py:2859) は、2906、2957、2984、3054 行の上記 4 test だけが共有します。
- 新規 [`_legacy_verdict_frame`:2872](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2409-wal-verdict-bind/orchestrator/tests/test_b10_backoff_shape_sweep.py:2872) は、2901、2903、2937、2978、3040、3046 行から使われ、同じ 4 test に閉じています。
- collector 正例内の `indexed` と `validator` はその test のローカル helper で、他 test との共有はありません。

既存 fixture が検査していた順序不変性、未知 tag、非文字列 tag、overrun、未終端 tail、logical slot 数、JSON/Markdown report への開示は、2789-2856 行の assertion がすべてそのまま残っています。失われた暗黙の性質は「3 field が無い `verify_done` も通る」ことだけで、これは今回意図的に除外された受理です。

- 判定: refuted / nit
- 放置時の変化: 既存の disclosure 値と検査対象は変わらず、廃止対象だった missing-field 受理だけが消えます。
- 結論: GO

## meta-test への抵触

新規 test node は計 12 件です。

- `test_legacy_verify_done_verdict_accepts_exact_values_and_extra_payload`
- `test_legacy_verify_done_verdict_rejects_field_mutation[anomalies-nonzero]`
- `...[anomalies-bool-false]`
- `...[anomalies-missing]`
- `...[certified-false]`
- `...[certified-int-one]`
- `...[certified-missing]`
- `...[verdict-other]`
- `...[verdict-missing]`
- `test_legacy_verify_done_verdict_is_checked_before_disclosure_filter[unknown-tag]`
- `...[unmapped-variant]`
- `test_report_collector_accepts_exact_legacy_verdict_fixture`

所要時間台帳にはこの 12 node が 1 件もありません。台帳の宣言値と実 entry 数はともに 20,042 で整合しています。直近記録の収集母数約 21,866 に 12 を足すと約 21,878、単純比は `20042 / 21878 = 91.608008%` で、[`coverage >= 0.90`:712](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2409-wal-verdict-bind/orchestrator/tests/test_acceptance_schedule_order.py:712) には抵触しません。collection 実測は行っていないため、この比率を実測値とは扱いません。

一方、production への 10 行追加による行番号変化が別の meta-test に抵触します。

- `run_formal` 内の `run_campaign` sink は 4051 行から [`4061`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2409-wal-verdict-bind/orchestrator/campaign/b10_backoff_shape_sweep.py:4061) へ移動。
- deferred-gate 登録簿は [`4051` のまま](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2409-wal-verdict-bind/orchestrator/tests/test_ccbench_spawn_sites.py:885)。
- 同じ旧値を検査する expected set も [`4051` のまま](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2409-wal-verdict-bind/orchestrator/tests/test_ccbench_spawn_sites.py:2667)。

静的に赤になる既存 node は次の 3 件です。

- `test_ccbench_spawn_sites.py::test_deferred_gate_ledger_is_exact_and_every_entry_names_a_live_sink`: 4051 行の live sink が 0 件となり、2733 行の `len(matches) == 1` が失敗。
- `test_ccbench_spawn_sites.py::test_define_sink_cross_product_has_no_unreviewed_ungated_member`: `BACKOFF_FIXED` と 4061 行 sink の `reachable` failure が 1 件となり、2642 行の `failures == []` が失敗。
- `test_ccbench_spawn_sites.py::test_define_sink_cross_product_classifies_t2155_production_sinks_exactly`: 同じ failure 1 件により、2935 行の `failures == []` が失敗。

- 判定: real / must-fix
- 放置時の変化: report 内容の値は変わりませんが、deferred-gate の参照が実 sink を見失い、既存 meta-test 3 node が赤になります。
- 結論: NO-GO

## 所見

1. 上記の stale sink line が唯一の must-fix です。現在の現物では期待値 4051 を 4061 に同期する必要があります。T-2408 合成後に前段の行数が変わる場合は、その合成後の live 行を使う必要があります。

2. 既存 test の期待値自体は 1 つも編集されていません。差分は production `+10/-0`、test `+244/-0` で、既存 assertion の削除や値変更はありません。ただし、その結果として別 file の 4051 という既存期待値が stale になっています。

3. 新しい `PreflightError` が、別理由を検査する既存 test を先に止める経路はありません。唯一の既存直接 caller には正常な 3 field が追加され、unknown tag、overrun、tail、report disclosure まで従来どおり到達します。既存 collector test は変更関数を mock しているため影響を受けません。

4. 別 session の 2463-2670 行域への侵入はありません。`git diff --unified=0` の hunk は production 3409、test 2769 と 2859 だけです。

5. 現物 3 系列の WAL を read-only で確認しました。

   - write-heavy `e3de15eb`: 135 record、`verify_done` 90、exact 合格 90、不一致 0
   - balanced `143a3f74`: 135 record、`verify_done` 90、exact 合格 90、不一致 0
   - read-heavy `acf840c8`: 135 record、`verify_done` 90、exact 合格 90、不一致 0
   - 合計: 405 record、`verify_done` 270、exact 合格 270、不一致 0
   - 各系列の tag は `legacy=15`、`performance=75`。`anomalies` は JSON 字義 `0`、`certified` は `true`、`verdict` は `"serializable"` です。

したがって新しい verdict 述語自体は現物 3 系列を拒否せず、report 発行経路の値や系列選択を壊しません。full `phase=report` は発行副作用を避ける契約に従って実行していません。

- 判定: refuted / nit
- 放置時の変化: 現物 3 系列の受理集合、270 slot、135 block-cell report 値に変化はありません。
- 結論: GO

## GO / NO-GO

**NO-GO。**

WAL verdict 変更と現物 3 系列には波及欠陥はありませんが、10 行の挿入で deferred-gate の line binding が stale になり、既存 meta-test 3 node が確実に赤になるためです。

## 総括

caller、fixture、12 新規 node、現物 WAL、競合指定域をすべて静的確認しました。受入所要台帳の 90% gate は維持され、既存 fixture の別の検査性質も失われていません。唯一の must-fix は `test_ccbench_spawn_sites.py` の `run_formal` sink 参照 4051 と、現物 4061 の不一致です。pytest は実行しておらず、緑は主張しません。