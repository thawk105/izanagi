# [T-1705] 正規化 cost の arm 間比較可能性を生成物へ自己宣言させる

- wave: `dev-wave-t1705-normalized-cost` / branch `worktree-dev-wave-t1705-normalized-cost`
- 実装 anchor commit: `00c8575abd25173a83154edb5dd01d2edb7ca76d`
- 変異走行の束縛 HEAD: `00c8575abd25173a83154edb5dd01d2edb7ca76d`

## 何を足したか

部分正規化 cost は 2026-08-25 に [T-1434] で既に生成されていたが、その値が**どの arm 間で
比較可能か**は生成物のどこにも書かれていなかった。行だけを読む consumer は、会計基盤も欠測構成も
違う行を同列の cost 比較として読める。本 wave は per-attempt 行と axis 行の双方へ additive な
`comparability` 宣言を足した。

- `basis_key` = 比較範囲 (`benchmark_task_id` / `stage` / `cache_condition`) +
  会計基盤 (`price_version` / `currency` / `price_unit` / 未計上 category / `coverage_status` /
  reasoning token の会計規則 / rounding) + `comparison_universe` (`material_manifest_sha256`)。
- `accounted_total_key` = 観測済み・観測不能・非発生の 4 count + status ごとの
  `(block_id, attempt)` のソート済み集合。
- 両 key が完全一致するときだけ `accounted_amount` を同列に読む。
- `rule` は保証範囲を「partial な accounted component total どうしの比較」に限定し、
  試行あたり平均・完全費用・実請求額を保証しないと明記する。`comparison_universe` が null の
  ときだけ同一 aggregate result 内へ限定する。

`requested_model` と `unit_prices` は比較条件に**入れない**。model ごとに公表単価が違うことを
USD へ正規化するのがこの層の目的であり、一致を要求すると目的を失う。

D932 に従い、宣言は gate にも certified field にもしない。`coverage_status` は `partial`、
`certification_status` は `not-certified` のまま。新しい `ValidationError`・拒否条件・
failure reason を足しておらず、受理集合は変えていない。D831 の凍結 literal と snapshot bytes も
変えていない。

## 段 3 / 段 6 の独立検証で判明した事実

- **既存 cost fixture は arm を 1 種類しか持っていなかった。** `_bound_price_schedule` の 2 slot は
  どちらも `arm="max"` で、arm 間比較を一度も覆っていない。
- 件数が揃っても観測できた試行の identity が arm 間で入れ替わっていれば paired 比較にならない。
- `basis_key` が比較 universe を識別しないと、別成果物の行が同じ比較集合を参照する。

## 変異台帳

spec v2 sha256 `e765e710d565df2e755bfefbb66c9454102485a4c2752e6bce22f10c1db6f196`
(`mutation-spec-v2.json`)。本走結果は `mutation-result-v2.json`。

| ID | 変異 | 結果 | 束縛するもの |
|---|---|---|---|
| M01 | 比較不一致時に `reasons.append(...)` を足して gate 化する | KILLED | 受理集合 |
| M02 | `basis_key` から `comparison_universe` を落とす | KILLED | 成果物の値 |
| M03 | `accounted_total_key` から pair unit identity 集合を落とす | KILLED | 成果物の値 |
| M04 | axis の count を最終集約でなく最初の per-attempt vector にする | KILLED | 成果物の値 |
| M05 | `basis_key.comparison_scope.benchmark_task_id` を literal へ固定 | KILLED | 成果物の値 |
| M06 | nested `rounding.decimal_places` を float にする | KILLED | 成果物の型 |
| M07 | `basis_key` へ `requested_model` を含める | KILLED | 正規化の目的 |
| M08 | `unavailable` の per-attempt 行から宣言を落とす | KILLED | 成果物の値 |
| M09 | pair unit identity の `attempt` 成分を literal `1` に固定 | KILLED | 成果物の参照範囲 |
| M10 | `comparison_universe.material_manifest_sha256` を literal へ固定 | KILLED | 成果物の参照範囲 |
| M11 | `rule` の null locality 条件を反転する | KILLED | 成果物の保証文言 |

**集計: registered 11 / completed 11 / KILLED 11 / MISMATCH 0 / SURVIVED 0 / TIMEOUT 0 /
PARSE_ERROR 0。**

### erratum (DW-M02 / DW-M08)

1 回目の走行 (spec sha256 `8e3e3a4d42bd087a38f2c8c0c9fd4820468ff902a55721fa0354e7f33a35bbe5`、
結果は `mutation-result.json`) は **SURVIVED 0 だが KILLED 5 / MISMATCH 6** だった。MISMATCH は
実装の検出力不足ではなく、親が事前に書いた期待 node 集合が不足していたためで、実測はいずれも
期待の上位集合または近接集合だった。`DW-M08` に従い 1 回目を probe と明記し、実測 node で
spec v2 へ再登録して本走した。**初回結果は消さず本 insight に残す。**

**M01 は過剰決定である。** 15 node が落ちる。受理集合を守る層が既に複数あり、単独変異としての
帰属は弱い。`DW-M03` に従い冗長 gate と明記し、単独変異の証拠から外す。M06 も既存の float 走査
test が同時に落とす。

### 走行環境の申し送り

本走は計算ノードの queue 枯渇で 3 回 `rc=16` になった。`artifact_error` は
`receipt scheduler_logs.stdout.path がない` で、実装の赤ではない。gen_S は待ち 49〜64 /
実行 51〜53 / 保留 96〜100 の混雑が続き、既定 15 分の queue 待ちでは足りなかった。login node の
`--runner-mode local` は harness が禁止するため迂回できない。
`IZANAGI_DISPATCH_QUEUE_WAIT_TIMEOUT_OVERRIDE=2200` を設定した 4 回目の `--resume` で全件が通った。
**この env override は queue 待ち時間だけを変え、判定・受理集合には触れない。**

## テスト実測

`orchestrator/tests/test_codex_reasoning_ab.py` の全走。

- fix 前 (login node bounded local): 607 passed / 27 skipped / rc=0
- fix 後 (計算ノード dispatch、request 965613): 610 passed / 27 skipped / rc=0

新規 8 nodeid はすべて明示走行で PASSED。

- `test_cross_arm_comparability_is_self_describing_and_model_normalized`
- `test_equal_counts_with_swapped_pair_units_are_not_comparable`
- `test_attempt_number_distinguishes_equal_count_pair_unit_identities`
- `test_distinct_non_null_manifest_digests_propagate_to_every_cost_row`
- `test_comparability_rule_preserves_polarity_and_null_locality_branch`
- `test_comparability_presence_and_mismatch_do_not_change_acceptance`
- `test_final_cost_artifact_comparability_contains_no_float_and_keeps_rounding`
- `test_null_comparison_universe_is_limited_to_same_aggregate_result`

## scope 外と裁定した real 所見

**cache write の未計上量が arm 間で系統的に違うかは判断できない。** 正規 receipt に数量 field が
無いためで、扱うには receipt schema の新しい登録世代が要る (事前登録 §10 が未着手と明記)。
本 wave の計算層 scope を越えるため実装せず、ここに記録する。

## 逐語

`verbatim/` に段 1 brief、段 4 裁定、段 3 の独立検証 2 本、段 6 のレビュー 2 本を置く。
