## 登録閉包の漏れ

### 1. 実装報告の列挙に G6 契約が漏れている

- **所見:** 登録自体の漏れはないが、`s5-impl.md` の関連契約一覧は不完全。
- **根拠:** `test_real_repo_serialization.py:376` の新 canonical node → 同`:399` の `_LONG_LIVED_FIXTURE_GROUP_NODES_GOLDEN` → `test_acceptance_schedule_order.py:810` の実 collection 集合 → 同`:812` の完全一致 assert。したがって `test_g6_all_real_repo_items_stay_one_unit_and_keep_relative_order` も golden 登録漏れで赤になる。報告 `s5-impl.md:27` 以下に記載がない。
- **real か推測か:** **real・静的読解**。参照を2段以上追跡した。
- **must-fix か nit か:** **nit**。
- **放置時の影響:** 成果物・受理集合は変わらないが、親が実走対象を選ぶ際の参照一覧が欠ける。
- **推奨:** 親の検証対象に既存 G6 を含める。新しい検査の追加は不要。

登録閉包を辿り直した結果は次のとおり。

| 参照経路 | 検出する内容 |
|---|---|
| material golden `:362` → group 辞書 `:399` → `_assert_long_lived_fixture_group_contract:1327` → `test_real_repo_group_collection_exactly_matches_canonical_nodes:1586` | 新 node の golden 登録漏れを完全一致で検出 |
| 同 group 辞書 → G6 の実 collection 集合 `test_acceptance_schedule_order.py:804` → assert `:812` | **今回の報告漏れ**。同じ登録漏れを検出 |
| collection plugin `test_real_repo_serialization.py:972` → consumer 集約 `:1000` → `_fixture_consumers_from_report:1296` → 上記 meta-test | consumer 集約と個々の fixture closure の不一致を検出。consumer 登録は自動 |
| module marker `test_p3_b4_material_report.py:41` → collection report → group 契約・`test_shard_assignment_preserves_live_xdist_group_components_and_split_control:1735` | marker と shard 閉包を検査 |
| ledger → `test_update_acceptance_duration_ledger.py:306` の G7e → `:319` の件数一致 | 項目追加だけで count を更新しない変更を検出 |
| ledger／実 collection → `test_acceptance_schedule_order.py:704` → G5 coverage `:712` | 90%閾値。**1件の登録漏れを必ず検出する契約ではない** |
| module 末尾 `test_p3_b4_material_report.py:1582` → `pytest.main([__file__])` → module collection | 新関数を自動収集。別の手動登録は不要 |

AST照合では、変更後の **32 canonical 関数と golden 32件が完全一致**。新関数は非パラメータ化で、golden は `test_p3_b4_material_report.py::test_aggregate_authoritative_floor_reaches_public_material_report`、台帳はこれに `orchestrator/tests/` を付けた正しい形式だった。T1574 の固定対象に本 module はない（`test_update_acceptance_duration_ledger.py:368`）。

## 台帳の整合

### 2. 件数・実測根拠は整合するが、79秒は群への純増時間ではない

- **所見:** 追加項目・`nodeid_count` とも正しい。79秒を「新テスト追加による実時間の増分」と読むのは誤り。
- **根拠:** `acceptance_duration_ledger.json:3` に79.0秒、同`:23113` に23110。JSONを実際に数え、**旧23109項目 → 新23110項目、既存値の変更0件**を確認。`/tmp/t2591-aggregate-material-report.xml:1` の対象 testcase は78.765秒。実装イベントログの`:68` は setup 71.22秒、call 7.54秒。`s5-impl.md:19` も共有 fixture setup を含むと明記している。
- **real か推測か:** **real・静的集計および既存実走証跡の読解**。今回のレビューでは実走していない。
- **must-fix か nit か:** **nit**。台帳不整合・推測値の実測偽装はない。
- **放置時の影響:** 台帳の配分重みは79秒増えるが、共有 setup を伴う単体所要なので、実際の群全走の増分とは一致しない。
- **推奨:** 値を推測で差し替えず、群全走・受入 shard の実際の増分は**親が測れ**。

なお、`conftest.py:1538` は count 不一致で空辞書を返す。一方、`tools/acceptance_shards.py:392` は台帳の durations を直接読むため、同じ count 不一致でも両者が一様に空扱いになるわけではない。今回は件数が一致しており、この分岐差は発生しない。

## 既存期待値への波及

### 3. 既存期待値の変更・キャッシュ汚染経路は確認されなかった

- **所見:** 指定された既存部分は不動。新正例は契約どおり独立した入力期待値で公開 builder を検査している。
- **根拠:** 指定された変更前後の逐行差分は `test_p3_b4_material_report.py:958` への101行追加のみ。既存 import、冒頭定数、`_ABSENT_LEGACY_*`（`:56`）、`_write_floor_preregistration`（`:77`）、m9 の4状態（`:845`）を含め、旧関数・class の AST 差分も0件。新関数は`:1026` で builder を直接呼び、`:248`／`:257` の cache helper を使わない。
- **real か推測か:** **real・静的読解**。全順序での実行結果を実測した主張ではない。
- **must-fix か nit か:** **nit相当の確認事項。修正不要**。
- **放置時の影響:** 既存期待値・本番の受理／拒否集合が変わる経路は確認されない。テスト収集集合は意図どおり1件増える。
- **推奨:** 既存期待値を変更しないまま、親の予定済み検証を行う。

状態経路も追跡した。`immutable_publication:147` は module fixture で、生成時の `mock.patch` は返却前に終了する。新関数の helper → `_synthetic_source:53` → `_install_git`（`test_floor_pair_driver.py:335`）は同じ function-scope `monkeypatch` を使用する。Git・calibration・fsync・repository root・evaluator wrapper の復元漏れはコード上見つからない。新しい書込みは `tmp_path` 配下で、builder（`p3_b4_material_report.py:1222`）は出力を公開せず bytes を返す。

xdist では同 group 内の順序は `conftest.py:1748` の unit 単位並べ替えで保持される。ただし、群の実行開始順・配置は台帳増分で変わり得る。

## scope と衝突

### 4. 編集面は契約内。golden の指定位置同士は重ならない

- **所見:** 変更は指定3ファイルだけ。新 gate・汎用 helper・将来用抽象はない。
- **根拠:** 作業ツリーの変更一覧と差分は、テスト＋101行、serialization golden＋1行、台帳＋2／−1行。serialization の実挿入位置は変更後`:376` で、親が示した並行 wave の `_REAL_REPO_CLASSIFIED_NODES_GOLDEN`（`:52` 付近）とは別位置。台帳は`:3` と`:23113` を編集している。
- **real か推測か:** 自 wave の編集位置は **real・差分読解**。他 wave の未提示差分全体との無衝突は未確定。指定名 `worktree-dev-wave-t2515-calib-rr95-rr5` は調べた worktree ディレクトリ内では確認できなかった。
- **must-fix か nit か:** **nit**。
- **放置時の影響:** 指定された golden 位置同士には行単位の重複がない。両 wave が台帳の count を更新する場合、片側採用では統合後の件数が誤る。
- **推奨:** serialization の1行差分を維持する。台帳先頭への挿入競合を減らすなら、既存 material 群の近傍（`:1930`）への局所挿入が可能。統合時は両追加を残して実件数を照合する。

### 5. 5分上限の余裕は証明されていない

- **所見:** 台帳合計だけで「5分以内」と判定できない。既存実走証跡には直列全走の5分超過がある。
- **根拠:** 台帳を集計すると **49件166.276秒 → 50件245.276秒、＋79秒／47.51%増**。300秒までの台帳上の差は54.724秒。`tools/acceptance_shards.py:325` は file/group を連結し、`:405` で重みを合算、`:425` 以降で配分する。実装イベントログ`:63` は **serial、50 passed、304.11秒、rc=0**。
- **real か推測か:** 台帳値・304.11秒の記録は **real・証跡読解**。受入最遅 shard の新所要は**未測定**。
- **must-fix か nit か:** **nit／親の実測事項**。受入上限違反とまでは断定できない。
- **放置時の影響:** 配分重みと他 component の配置が変わり、受入完了時間が変わり得る。成果物値・本番受理集合への変更はない。
- **推奨:** 変更後の受入最遅 shard と材料 group の wall time は**親が測れ**。304.11秒を受入 shard の実測値へ読み替えない。

## 総括

**コード上の must-fix は確認できなかった。実装報告の明確な漏れは G6 契約の未列挙。**

`s5-impl.md` の実走主張はイベントログとJUnitで裏付けられた。meta-test・全体走・変異検証を未実走とする記述にも矛盾はない。「本番の受理・拒否挙動は不変」は production 差分ゼロと整合する。

親に残るのは、**G6を含む既存 meta-test、予定済み変異検証、受入最遅 shard の5分上限の実測**。本レビューは静的検査と既存証跡の読解のみで、テスト実行・ファイル変更・commit は行っていない。