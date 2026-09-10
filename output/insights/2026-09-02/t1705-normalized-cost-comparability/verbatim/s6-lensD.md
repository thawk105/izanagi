## 検証した範囲

指定された 5 資料を全文確認し、差分の 2 ファイルと関連する集約・validation・test inventory を静的に追跡した。pytest と変異実走はしていない。

確認結果は次のとおり。

- pair identity は status 別の `(block_id, attempt)` 集合として生成され、ソートされている。`tools/codex_reasoning_ab.py:10024-10037`
- count が同じで identity が異なる反例は実在し、`b01` と `b02` の入れ替わりによって key が不一致になる。`orchestrator/tests/test_codex_reasoning_ab.py:16012-16059`
- `comparison_universe=null` の現行規則は同一 aggregate 内だけに限定しており、現行文言自体は過大でも過小でもない。`tools/codex_reasoning_ab.py:9994-9998`
- 現行 `rule` は平均、完全費用、実請求額を明示的に保証外としており、文言自体は妥当。`tools/codex_reasoning_ab.py:9988-9998`
- fixture の arm は実際に `max` と `high` であり、成果物上でも名指し確認される。`orchestrator/tests/test_codex_reasoning_ab.py:6565-6571,15918-15920`
- 複数試行 axis は `alpha/stage-1/sol/null/frozen/max` と `alpha/stage-1/luna/null/frozen/high` の各 axis に `b01`、`b02` の 2 試行が入る。`_AXIS_FIELDS` と arm は各 axis 内で一致している。`tools/codex_reasoning_ab.py:9795-9801`、`orchestrator/tests/test_codex_reasoning_ab.py:6565-6569,15968-16009`
- 新規 test file はない。既存 `orchestrator/tests/test_codex_reasoning_ab.py` への 5 nodeid 追加だけである。duration ledger の網羅検査は 90% の比率 gate で、当該 suite を exact 固定する検査ではない。`orchestrator/tests/test_acceptance_schedule_order.py:704-714`、`orchestrator/tests/test_update_acceptance_duration_ledger.py:364-389`

## 変異 M1〜M8 と、落ちるはずのテストの対応表

| ID | 静的に落ちるはずのテスト | 直接検出する箇所 | 前後の冗長 gate |
|---|---|---|---|
| M1 | `test_comparability_presence_and_mismatch_do_not_change_acceptance` | mismatch を含む 4 結果について `(valid, failure_reasons, experiment_complete) == (True, [], True)` を固定。`test_codex_reasoning_ab.py:16144-16156` | なし。all-zero は `unavailable` 分類であり rejection reason にはならない。変異で追加する reason だけが受理集合を変える |
| M2 | `test_cross_arm_comparability_is_self_describing_and_model_normalized`、`test_null_comparison_universe_is_limited_to_same_aggregate_result` | 非 null と null の双方で `comparison_universe` object を直接参照。`:15948-15950,16225-16227` | なし。additive metadata に対する後段 schema gate はない |
| M3 | `test_cross_arm_comparability_is_self_describing_and_model_normalized`、`test_equal_counts_with_swapped_pair_units_are_not_comparable` | exact identity 集合と、同一 count・異 identity の key 不一致を固定。`:15931-15941,16037-16059` | なし。swapped fixture は両 arm とも `(1,1,0,2)` で既存 count gate には差がない |
| M4 | `test_cross_arm_comparability_is_self_describing_and_model_normalized`、`test_equal_counts_with_swapped_pair_units_are_not_comparable`、`test_comparability_presence_and_mismatch_do_not_change_acceptance` | axis の exact count を 2、または `(1,1,0,2)` と固定。`:15977-16009,16037-16048,16125-16138` | なし。per-attempt 行は正しくても axis exact assertion が独立して落とす |
| M5 | `test_cross_arm_comparability_is_self_describing_and_model_normalized` | comparison scope の集合を `{alpha/stage-1, beta/stage-2}` に固定。`:15902-15916` | なし。schedule validator は入力 task を検査するが、出力の hard-code は拒否しない |
| M6 | `test_final_cost_artifact_comparability_contains_no_float_and_keeps_rounding`、既存 `test_p01_bound_cost_is_mapping_driven_decimal_partial_and_uncertified` | comparability tree の float 走査と nested `decimal_places` の exact `int` 型検査。`:16184-16211`。既存 cost tree 全体の float 走査も該当。`:15821-15824` | なし。成果物生成後の型 validator はなく、assertion が直接検出する |
| M7 | `test_cross_arm_comparability_is_self_describing_and_model_normalized` | sol/max と luna/high の `basis_key` equality、および forbidden key の再帰的 disjoint 検査。`:15918-15926,15951-15962` | なし。両 requested model は allowlist 内なので前段で拒否されない |
| M8 | `test_equal_counts_with_swapped_pair_units_are_not_comparable`、`test_final_cost_artifact_comparability_contains_no_float_and_keeps_rounding` | unavailable を含む全 resource 行で comparability の存在を検査。`:16060-16063`。最終成果物中の comparability tree 件数も resource+axis と固定。`:16184-16194` | なし。all-zero unavailable は正常な三分類であり rejection reason を生成しない |

事前登録された M1〜M8 に限れば、落ちるテストをすべて名指しでき、冗長 gate による過剰決定も見つからなかった。

## 検出力の穴

- H1: `pair_units_by_status[].attempt` の入力追随を検査していない。全 comparability fixture が `attempt=1` なので、attempt を literal `1` にした変異が生存する。
- H2: 非 null `material_manifest_sha256` が 1 種類しかない。`null` と `"d"*64` だけを場合分けして hard-code する変異が生存する。
- H3: `rule` は意味ではなく単語の存在だけを検査している。否定の反転、null locality の否定、非 null 行への locality 制限の誤適用が生存する。

## 所見 (重大な順)

1. 高: 非 null comparison universe の値伝播が 1 sentinel にしか束縛されず、異なる manifest を同じ universe に固定する変異を検出できない。

   根拠: `orchestrator/tests/test_codex_reasoning_ab.py:15690-15696,15948-15950,16214-16228,16691-16713`

   影響: 放置すると異なる material manifest の行が同じ比較集合を参照し、別実験間差を arm 間差として扱う偽陽性が生じる。受理集合は変わらない。

2. 高: pair unit identity の `attempt` 成分が変化する fixture がなく、attempt を常に `1` とする変異を検出できない。

   根拠: `orchestrator/tests/test_codex_reasoning_ab.py:15614-15619,15704-15720,16021-16059`

   影響: 放置すると retry generation 間で observed/unavailable identity が入れ替わっても key が一致し、対応していない試行の費用を比較可能として参照できる。受理集合は変わらない。

3. 中: `rule` のテストが極性と条件分岐を固定していない。

   根拠: `orchestrator/tests/test_codex_reasoning_ab.py:15963-15966,16224-16228`

   影響: 放置すると「平均・完全費用・実請求額も比較可能」または「null でも別成果物間比較可能」への意味反転や、非 null universe の不要な同一 result 限定がテストを通り、成果物の保証文言と参照範囲が変わる。

## 判断できなかった点と、その理由

- pytest と変異は実走していないため、上表は制御フローと assertion に基づく静的判定である。緑または実測 KILLED とは判定していない。
- acceptance duration ledger の実収集後の正確な coverage 比率は collect-only を行っていないため未確認。ただし新規 test file はなく、当該 suite を exact 列挙するメタテストも見つからなかった。
- cache write 未計上量の arm 間差は receipt に数量がないため判断不能。ただし現行 `rule` は完全費用を保証しておらず、この不明点を過大主張してはいない。

## 総括

M1〜M8 は静的にはすべて kill でき、各 fixture は別 gate に先取りされていない。pair identity の block 入れ替わり、異なる arm、同一 axis の複数試行、null universe、非 gate 性も実体を伴っている。

ただしレンズ D 全体としては要修正である。少なくとも `attempt=2` を含む identity 入れ替わり、異なる 2 個の非 null manifest digest の伝播、`rule` の exact 文言または極性と null 条件を固定するテストが必要である。