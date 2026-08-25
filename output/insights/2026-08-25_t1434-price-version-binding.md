# [T-1434] price_version 束縛 — 変異台帳と逐語記録

wave: dev-wave-t1434-price-version-binding /
branch: worktree-dev-wave-t1434-price-version-binding

## 1. 変異 matrix (本走)

- 対象 commit: `ebecff0a033da02f71714ec5d659f48410623936`
- spec: `mutation-spec-final.json` / `spec_sha256 = 8bd1ada4c39196e6088ca8f9860fb62b06daa41440b17fe957d525c1d3b7b5ae`
- harness: `tools/mutation_worktree.py` + `tools/mutation_harness.py`、`--runner-mode dispatch`
- runner: `python3 tools/run_tests.py --force-dispatch orchestrator/tests/test_codex_reasoning_ab.py -q -rf`
  (下記 §2 の 18 件を `--deselect`)

**結果: baseline PASSED (rc=0・失敗 0)、10/10 KILLED、SURVIVED 0、MISMATCH 0、TIMEOUT 0。**
期待 node は完全集合で登録し、全 10 件が完全一致した。
所要は baseline 288.2 秒、変異 10 件の合計 951.2 秒 (いずれも harness 記録値)。

| id | 変異した gate | 期待 node (完全集合) |
|---|---|---|
| m01 | price の等価判定 2 条件を同時に恒真化 | `test_nullable_price_negative_matrix_is_fail_closed[opaque]`、`[other-snapshot]` |
| m02 | 期待値なしの拒否を恒真化 | `test_nullable_price_negative_matrix_is_fail_closed[missing-expected]`、`test_non_null_price_binding_rejects_float_schema_v3`、`test_non_null_price_binding_is_schema_v3_only[v2]`、`[missing]`、`test_non_null_nullable_dimension_is_fail_closed[price_version]`、`test_validate_schedule_rejects_live_non_null_cache_or_price[price_version]` |
| m03 | 全 slot 一様性検査を素通り | `test_price_version_global_concentration_rejects_null_and_frozen_blocks` |
| m04 | record の exact field-set を恒真化 | `test_price_snapshot_record_is_exact_and_pinned[extra-key]`、`[missing-sha]`、`[missing-path]` |
| m05 | snapshot record の SHA 照合を恒真化 | `test_price_snapshot_record_is_exact_and_pinned[wrong-sha]` |
| m06 | 抜粋の実 bytes SHA 照合を恒真化 | `test_bound_price_rejects_changed_snapshot_or_excerpt_bytes[excerpt]` |
| m07 | `schema_version` の exact 型検査を恒真化 | `test_non_null_price_binding_rejects_float_schema_v3` |
| m08 | `block_order` の exact 型検査を恒真化 | `test_bound_price_requires_exact_integer_block_order[bool]`、`[float]` |
| m09 | `stage` の exact 型検査を恒真化 | `test_bound_price_rejects_numeric_stage_type_confusion[bool]`、`[float]` |
| m10 | **cache 側 control** — `cache_condition` の非 null 拒否を恒真化 | `test_expected_schedule_rejects_non_null_v2_cache_condition`、`test_non_null_nullable_dimension_is_fail_closed[cache_condition]` |

m10 が KILLED であることは、**cache の受理集合が本 wave で 1 bit も動いていない**ことの証拠である。
price 側を触った変更が cache 側の拒否を巻き添えにしていれば、この 2 件は変異前から赤になる。

## 2. baseline から `--deselect` した 18 件と、その根拠

`tools/mutation_worktree.py` は使い捨て worktree で外部 benchmark の submodule を **1 段だけ**
初期化し、入れ子の submodule を初期化しない。そのため `benchmark_snapshots` fixture に依存する
18 test が setup で error になり、baseline が `PARSE_ERROR` で止まった。

これは本 wave の実装の欠陥ではない。**同じ 18 件は親の worktree では緑である** —
`orchestrator/tests/test_codex_reasoning_ab.py` の単独走で 505 passed / 2 skipped を実測済み。
DW-M05 が定める「既存赤は `--deselect` で外し根拠を台帳へ書く」に従った。

外した 18 件はいずれも price 束縛の gate を通らないため、**変異の検出力は落ちていない。**
実際、10 変異すべてが残った test 集合だけで KILLED になった。

```
test_agent_sandbox_binds_exclude_attempt_receipt_directory
test_attempt_four_is_rejected_before_launch
test_cleaned_snapshot_records_absent_commit_graph_and_keeps_closure
test_f3_4_prelaunch_exception_completes_pair_and_allows_next_generation
test_git_answer_object_reinjection_is_rejected
test_m1_snapshot_head_pin_is_independent
test_m3_focus_artifact_directions
test_m3_ignored_extra_and_missing
test_m3_snapshot_mode_change
test_m3_symbolic_head_is_required
test_pos_neg_submodule_initialization_state_mismatch_is_rejected
test_replay_forwards_only_successful_snapshot_evidence_to_adjudication
test_snapshot_submodule_object_store_is_recursive
test_stale_commit_graph_referencing_pruned_commit_is_rejected_and_manifested
test_supervisor_launches_pair_and_scrubs_git_environment
test_validate_schedule_legacy_different_arm_same_model_pair_remains_valid
test_verify_checks_pre_post_snapshot_for_every_shared_oracle_run
test_verify_replays_complete_fake_codex_experiment
```

## 3. erratum — 親の予測が外れた件

段 5 直後に親は「price 判定の 4 条件のうち 2 つが過剰決定であり、単独 clause の変異は
相方に mask されて SURVIVED になる」と予測し、裁定文書へ記録した。

**本走では m01 が KILLED になり、予測は当たらなかった。**
ただし予測の対象と実施した変異が食い違っている。m01 は重複する 2 条件を**同時に**恒真化する
形で登録したので、単独 clause の変異ではない。**単独 clause の変異は登録しておらず、
予測はまだ検証されていない。** 予測が正しいかどうかは未確定のまま残す。

段 6 のレビュー 2 本も独立に同じ過剰決定を指摘しており、成果物の値は変わらないため
nit として backlog にした。この判断は変えない。

## 4. 変異走行で踏んだ手続き上の失敗 3 件 (実装とは無関係)

いずれも本 wave の実装の欠陥ではなく、走らせ方の問題である。

1. **使い捨て worktree の入れ子 submodule 未初期化** — 上記 §2。道具側の限界。
   `--resume` は記録済みの baseline 判定を再利用するため、後から submodule を初期化しても
   赤の判定が更新されない (計画上も `baseline=0 run`)。証拠台帳を書き換えて通す手は取らなかった。
2. **`--resume` の `--attempt-out` は既存 file を要求する** — 親が「再走では出力先を新 path にする」
   という別規則を resume にも当てはめ、存在しない path を渡して rc=2 になった。
   道具が出力する resume コマンドは既存 file を指しており、そちらが正しい。
3. **runner argv に wrapper を挟めない** — harness は runner の入口を
   `python -m pytest` か固定 HEAD の `tools/run_tests.py` に限定する。
   submodule 初期化を `bash -c` で前置する案は、`-rf` が独立トークンでなくなる点でも拒否された。

## 5. 本走 wrapper の rc=125 について

本走は 10/10 KILLED で完了したが、wrapper 自身は `rc=125`
(`共有木の観測 bytes が変化した`) で終わった。

原因は**別 session が走行中に local main を進めたこと**である。
親の worktree は走行前後とも `git status --porcelain` が空であり、
main の HEAD が `6d1d43ac` から `06bb563e` へ動いていた。

wrapper が主張するのは共有木の観測 bytes 不変だけで、その主張は無効になった。
一方、**測定は固定 commit `ebecff0a` の隔離 worktree で行われており実体は健全である。**
この区別を残す (F383 と同型の再発)。

## 6. 受理集合の独立 probe (親の実測)

テストの緑とは独立に、親が leaf 関数へ直接入力して受理・拒否を測った。**20 項目すべて期待どおり。**
特に「呼び手が別の値を期待値だと自称しても拒否される」ことを確認しており、
段 3 が指摘した「束縛が自己追認になっていないか」への直接の答えになっている。

| 入力 | 期待 | 実測 |
|---|---|---|
| null (従来形) | 受理 | 受理 |
| 凍結 version + 期待値一致 + v3 | 受理 | 受理 |
| 凍結 version・期待値なし | 拒否 | 拒否 |
| 任意文字列 / 空文字 / 非文字列 / 別 version | 拒否 | 拒否 |
| 呼び手が別 version を期待値と自称 | 拒否 | 拒否 |
| v2 + 凍結 version | 拒否 | 拒否 |
| cache 非 null (price は正しい) | 拒否 | 拒否 |
| 全 null / 全 frozen の一様 | 受理 | 受理 |
| null と frozen の混在 | 拒否 | 拒否 |
| record 余剰 key / key 欠落 / 非 object / path 不一致 / SHA 1 文字違い / 不在 | 拒否 | 拒否 |

fix 後には型混同の確認も行った。

| 入力 | 束縛 |
|---|---|
| `int 3` + 凍結 version | 発行される |
| `float 3.0` + 凍結 version | 発行されない |
| `float 3.0` + 全 null | 発行されない (旧受理集合は不変) |
| `int 3` + 全 null | 発行されない |

## 7. 親が実測したテスト結果 (子は全 3 本とも pytest 実走不能)

| 走 | 結果 |
|---|---|
| `test_codex_reasoning_ab.py` 単独 (段 5 後) | 494 passed, 2 skipped / 192.87s |
| 同 (fix 1 巡目後) | 496 passed, 2 skipped / 192.11s |
| 同 (fix 2 巡目後) | 505 passed, 2 skipped / 192.69s |
| consumer 焦点走 (段 5 後) | 212 passed, 1 skipped / 94.19s |
| consumer 焦点走 + docs checker (fix 2 巡目後) | 728 passed, 4 skipped / 96.59s |

consumer 焦点走の対象は `test_growth_test_holds_contract` / `test_hold_inventory` /
`test_real_repo_serialization` / `test_acceptance_schedule_order` /
`test_update_acceptance_duration_ledger` / `test_check_docs` (DW-O26 の consumer 拡張)。

## 8. 既存テストの保存の実測

fix 2 巡を経て test file の差分に削除行が現れたため、既存テストが弱められていないかを検査した。

**HEAD の全 11936 行が順序どおり現在の file に保存されている (欠落 0)。**
差分上の削除は hunk の再整列によるもので、既存テストの改変ではない。
