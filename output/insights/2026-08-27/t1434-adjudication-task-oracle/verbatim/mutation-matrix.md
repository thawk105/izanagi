# 変異 matrix — [T-1434] adjudication 層の task-specific oracle 対応

- harness: `tools/mutation_harness.py`、`--runner-mode dispatch --detached`
- runner argv: `python3 tools/run_tests.py orchestrator/tests/test_codex_reasoning_ab.py -q -rf --force-dispatch`
- spec: `mutation-spec.json`
  sha256 `adb668a634cdb6d94a99cb4624265febbe8c55db9fe01c56c164013ccd0dd88a`
- 束縛 HEAD: `287b994df89bd5bff0ac8fbca17a334bb5a0b6d3`
- **baseline: PASSED (rc=0、80.099s、failed_nodes 0 件)**
- **結果: KILLED 9 / SURVIVED 0 / MISMATCH 0 / TIMEOUT 0 / PARSE_ERROR 0、
  期待との一致 9/9 (registered 9・completed 9・matching 9)**

## 2 段構えにした理由

`DW-M08` は「期待 node は完全集合で、同形式へ正規化した記録 node との完全一致だけを KILLED とする」と
定める。期待 node を推測で書くと、当たっていても偶然か実力かが分からない。そこで
`DW-M07` の手順どおり、**先に全件 SURVIVED 期待の probe を回して観測 node を集め**、
その完全集合を pin した本走を別に回した。probe では 9 件すべてが MISMATCH (= 全部赤になり
node が取れた) となり、本走では 9 件すべてが KILLED で完全一致した。

## 変異一覧

| ID | 変異 | 期待 node | 結果 |
|---|---|---|---|
| m01 | `_load_adjudication` の per-task 集合取得から `benchmark_task_id=` を落として union へ戻す | `test_load_adjudication_rejects_cross_task_equivalent_from_manifest_union[parent]` / `[second-reader]` | KILLED |
| m02 | raw reader 行の検査を parent のみへ狭める | `test_load_adjudication_rejects_cross_task_equivalent_from_manifest_union[second-reader]` | KILLED |
| m03 | `oracle_kind` を combined verdict から削除 | `test_replay_manifest_forwards_external_task_manifest_to_real_adjudication_loader`、`test_m6_verdict_packet_swap_restore_digest_layers_are_redundant`、`test_verify_checks_pre_post_snapshot_for_every_shared_oracle_run`、`test_verify_replays_complete_fake_codex_experiment` | KILLED |
| m04 | `verdict.get("oracle_kind")` を既定値つきへ変え、欠落を受理させる | `test_aggregate_verified_rejects_adjudication_oracle_kind_mismatch[missing]` のみ | KILLED |
| m05 | `_aggregate_verified` の `oracle_kind` exact 比較を丸ごと削除 | 同 `[wrong]` と `[missing]` の両方 | KILLED |
| m06 | **既に着地していた** `_aggregate_verified` の `equivalent not in known_finding_ids` を削除 | `test_aggregate_verified_rejects_cross_task_equivalent_from_manifest_union` のみ | KILLED |
| m07 | `_replay_manifest` の `task_manifest=task_manifest` を `task_manifest=TASK_MANIFEST` へ | `test_replay_manifest_forwards_external_task_manifest_to_real_adjudication_loader`、`test_replay_manifest_forwards_external_task_manifest_digest_at_loader_boundary` | KILLED |
| m08 | dimension join 失敗時の packet 単位 reason 追加を削除 | `test_load_adjudication_dimension_join_failure_is_reasoned_and_not_joined` のみ | KILLED (**下記のとおり診断 pin**) |
| m09 | per-task 集合を `frozenset()` へ (過剰拒否) | `test_replay_manifest_forwards_external_task_manifest_to_real_adjudication_loader` のみ | KILLED |

## 単一理由性の確認 (`DW-M01`)

- **m02 と m04 が対で単一理由性を示した。** m02 は `[second-reader]` だけを赤にし `[parent]` を
  緑のまま残す。m04 は `[missing]` だけを赤にし `[wrong]` を緑のまま残す。
  どちらも「両方赤になる」のではないので、reader 方向と wrong/missing の 2 軸が
  独立に所有されている。
- **m06 は機構の必要性の反実仮想である。** `_aggregate_verified` の task 別ゲートは
  事前登録 §5.3 で「機構は着地」と記録されていたが、**削除しても本 wave 前は全テストが緑**
  だった。本 wave で新設した 1 node だけがこれを検出する。

## m08 は correctness kill に数えない (`DW-M08`、段 6 レビュー B の RB2)

m08 が消すのは packet 単位の診断 reason だけである。`_slot_dimension_map` が先に
slot 単位の reason (`s01: schedule stage does not match benchmark task manifest`) を積み、
変異の有無にかかわらずその slot は `joined` されず、成果物は既に無効である。
つまり**受理集合は変わらず、赤は診断文字列の一致だけで出ている。**
`DW-M03` の「診断文字列だけの赤を kill にしない」と `DW-M08` の
「受理集合を変えず構造化シグナルだけを pin する変異は kill でなく diagnostic sensitivity pin へ
別枠記録する」に従い、**診断 sensitivity pin** として別枠に置く。

したがって内訳は **correctness kill 8 件 + 診断 sensitivity pin 1 件**である。
harness の集計は 9 件すべてを KILLED と出すが、その 9 をそのまま
「正しさゲートを守る変異が 9 件」と読んではいけない。

## m07 の帰属 (段 6 レビュー B の RB1)

m07 は 2 node を赤にする。**新しい帰属を担うのは
`test_replay_manifest_forwards_external_task_manifest_digest_at_loader_boundary` である** —
この node は `_load_adjudication` を実物へ委譲する spy で包み、渡された manifest の
canonical digest だけを 1 個の assert で検査する。もう 1 つの node
(`..._to_real_adjudication_loader`) は既存の digest 検査と union 検査でも赤になるため、
**そちらを m07 の配線証明として数えてはならない。**
RB1 はまさにこの点を指摘し、fix で専用 node を足して閉じた。
