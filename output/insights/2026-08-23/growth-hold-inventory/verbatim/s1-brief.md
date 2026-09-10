# 段 1 brief — dev-wave-growth-hold-inventory

base 4cbaf041 / main tip 90a6bcb2 / 2026-08-23

## scope

`orchestrator/tests/growth_test_holds.py` の `_HOLD_ROWS` 先頭 16 行
(`test_codex_reasoning_ab.py::*`、`_SNAPSHOT_CORPUS_REASON` 14 + `_ROLLOUT_REASON` 2) を
1 件ずつ「再導入 / 削除 / hold 継続」へ裁定し実装する。編集面は **`growth_test_holds.py` の
`_HOLD_ROWS` とその reason 定数**、および裁定が要求する場合のみ
`orchestrator/tests/test_codex_reasoning_ab.py` の**比例源除去**の 1 点。
`conftest.py` の hold 機構本体、`test_growth_test_holds_contract.py`、`tools/hold_inventory.py`
は稼働中 dev-wave-flaky-quarantine の編集面なので**触らない**。

## 確定済みユーザー裁定 (覆さない)

- D335: 成長比例テストは新設せず既存分は恒久保留。**削除は却下済み**。解除は
  ユーザー明示命令のみ (`RELEASE_EXPLICIT_USER_COMMAND_ONLY`)。既定を勝手に変えない。
- D451: 保留すると当該防壁の既定走行 node がゼロになるなら**保留しない**。
  比例源が別軸で除去できるならそちらを先に行う。部分保留は純損失。
- D463: 比例判定は**秒数でなく入力集合 F(t) の性質**で行う。

本 wave の引数はユーザー命令であり、「検出力が他テストと重複していて不要なら削除」を
D335 の削除却下 (=コストを理由とする削除の禁止) と両立する別基準として読む。
コストを理由に削除する裁定は本 wave では出さない。

## 段 0 実測 (すべて本 worktree、2026-08-23)

corpus `/home/SFC/tanab/.codex/sessions` は**実在** — 5,482 file / 5.13 GiB。
引数の前提「snapshot corpus の不在」は成り立たず、登録 reason 本文も「不在」ではなく
成長比例コストである。16 node は opt-in 実走で **20 items 全 PASS / 544.05 秒**。

| probe (repo 外) | 値 |
|---|---|
| `rglob("rollout-*.jsonl")` | 0.040 秒 / 5,482 file |
| `derive_independent_golden` (pinned) | 0.139 秒 |
| `_find_rollout(POS, pinned_label='POS')` | 0.036 秒 |
| `_find_rollout(POS, pinned_label=None)` | 329.754 秒 (cold) / 約 18.5 秒 (warm) |

D451 が 2026-08-16 に記録した「session corpus 軸 0.13 秒」を、corpus 成長後も再現した。

`benchmark_snapshots` は module scope。consumer 18 本のうち 14 本が hold で、
4 本 (`test_snapshot_submodule_object_store_is_recursive`,
`test_validate_schedule_legacy_different_arm_same_model_pair_remains_valid`,
`test_git_answer_object_reinjection_is_rejected`,
`test_supervisor_launches_pair_and_scrubs_git_environment`) は既定で走る。
よって fixture は既定走行で必ず構築され、**14 本の hold は corpus 列挙費を 1 秒も節約しない**。

## 親の provisional 裁定 (攻撃対象)

- **(P1)** 14 件の `_SNAPSHOT_CORPUS_REASON` は、登録 reason が事実と食い違う
  (fixture は既定で構築される)。よって「corpus 列挙が比例源」という根拠では hold を維持できない。
- **(P2)** `test_m2_production_golden_requires_both_routes` (0.55 秒) は、2 経路独立導出の
  一致と pin bytes を確かめる唯一の既定候補 node である。既定で走る
  `test_derive_independent_golden_wires_pins` は `_find_rollout` を monkeypatch した
  配線検査にすぎず実 golden を導出しない。D451 により **再導入**。
- **(P3)** `test_prompt_replacement_count_zero_expected_and_excess` は
  `_find_rollout` を `pinned_label` なしで呼ぶため 5.13 GiB 全走査経路へ落ちる
  (cold 329.75 秒 / warm 約 18.5 秒 × parametrize 3)。D451 の「比例源を別軸で除去」に従い
  呼出しへ `pinned_label="POS"` を与えれば 0.036 秒になり、比例源が消える。
  除去後に**再導入**する。
- **(P4)** 14 件のうち body 自体が高コストな node
  (`test_verify_replays_complete_fake_codex_experiment` 171.83 秒、
  `test_agent_sandbox_binds_exclude_attempt_receipt_directory` 29.39 秒 等) は、
  **比例ではない** (fixed-size snapshot への git/subprocess 作業)。
  比例でない以上 growth registry に留めるのは分類の誤りだが、
  無条件の再導入は全走 5 分予算を破る。ここが本 wave の設計択一である。

## 不変条件

- 環境変数の既定を変えない。`RELEASE_EXPLICIT_USER_COMMAND_ONLY` を維持する。
- hold を継続する行には、実測日と**機械可読な再評価条件**を残す。
- 正しさゲートを弱めない。再導入は検出力を増やす方向のみ。
- 稼働中 wave の編集面 (conftest.py / contract test / hold_inventory.py) に触れない。

## 成果物

- `_HOLD_ROWS` の裁定反映 (再導入 = 行削除、継続 = reason 更新)。
- 16 件それぞれの裁定と根拠を worklog fragment + insight へ逐語で残す。

## 並列分割

段 2 プラン 1 本、段 3 敵対 2 レンズ (sol=分類の正しさ / luna=予算と検出力の取引)、
段 5 実装 1 本 (編集面が単一 file 中心のため分割しない)、段 6 レビュー 2 本 + fix 1 本。

## 段 0 追加実測 — 既定走行の基準線 (hold 有効、同 file 全走)

`python3 -m pytest orchestrator/tests/test_codex_reasoning_ab.py`
→ **347 passed / 20 skipped / 135.45 秒**。durations 先頭に
`15.32s setup test_snapshot_submodule_object_store_is_recursive` が出る。
これが `benchmark_snapshots` の構築であり、hold 中の 14 件と無関係に既定で支払われている。
(P1) は実測で確定した。

16 node の opt-in 実走は 544.05 秒 (fixture setup 13.75 秒を含む)。
marginal は約 530 秒。既定 135.45 秒に足すと約 665 秒となり、
全走 5 分 (300 秒) の絶対上限を単独で破る。無条件の全件再導入は成立しない。

### per-node marginal (opt-in 実走の call 秒)

| node | 秒 | 定数 |
|---|---|---|
| test_prompt_replacement_count_zero_expected_and_excess (3 params) | 250.68 | ROLLOUT |
| test_verify_replays_complete_fake_codex_experiment | 171.83 | SNAPSHOT |
| test_agent_sandbox_binds_exclude_attempt_receipt_directory | 29.39 | SNAPSHOT |
| test_m3_focus_artifact_directions (3 params) | 18.32 | SNAPSHOT |
| test_m3_ignored_extra_and_missing | 14.95 | SNAPSHOT |
| test_f3_4_prelaunch_exception_completes_pair_and_allows_next_generation | 7.77 | SNAPSHOT |
| test_stale_commit_graph_referencing_pruned_commit_is_rejected_and_manifested | 7.49 | SNAPSHOT |
| test_cleaned_snapshot_records_absent_commit_graph_and_keeps_closure | 7.16 | SNAPSHOT |
| test_m3_snapshot_mode_change | 6.95 | SNAPSHOT |
| test_parent_numstat_controls_remain_pinned | 6.91 | SNAPSHOT |
| test_m3_symbolic_head_is_required | 3.82 | SNAPSHOT |
| test_m1_snapshot_head_pin_is_independent | 3.32 | SNAPSHOT |
| test_m2_production_golden_requires_both_routes | 0.55 | ROLLOUT |
| test_forbidden_commits_are_unreachable_in_both_cases | 0.01 | SNAPSHOT |
| test_attempt_four_is_rejected_before_launch | <0.005 | SNAPSHOT |
| test_pos_neg_submodule_initialization_state_mismatch_is_rejected | <0.005 | SNAPSHOT |

注意: `[0]` 213.64 秒は cold、`[9]` 18.99 / `[10]` 18.05 秒は warm (probe が page cache を
温めた後)。cold/warm いずれも corpus file 数に比例する。
