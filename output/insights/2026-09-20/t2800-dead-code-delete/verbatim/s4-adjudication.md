# 段 4 裁定 — [T-2800]/[T-2276] dead-code 削除 wave

- 日時: 2026-09-20 14:1x JST。main は着手時と同じ `947fd160a` (14:14 再確認)。裁定 inbox 再走査 (13:4x) に T-2800 関連の更新なし。
- 入力: `s1-brief.md`、`codex/s2-plan.md` (plan、rc=0)、`codex/s3-consult-A.md` (レンズ A 消しすぎ、sol、NO-GO / must-fix 2)、`codex/s3-consult-B.md` (レンズ B 残しすぎ・過剰、luna、条件付き GO / must-fix 1)。

## 所見の裁定

| 所見 | 判定 | 採否 | scope | 根拠・処置 |
|---|---|---|---|---|
| A-1 / B-1 / plan (P1): science-slice の対は D2172 項 6 (派生値 pin 維持、list-D:283 に `test_pinned_jobs_requirements_are_exact`) と項 5 R3 の重複指定で、項 5 優先と断定できない | real | 採用 | 内 | **対を残す** (択 (a))。両裁定を同時に満たし、優先順位を新設しない。DW-S04 の「裁定時の未見事実」に当たるが、保持は承認済み裁定のどちらも止めないので再裁定待ちへ戻さず、事実を insight に記録する (ユーザーが削除を望むなら項 6 の例外指定が要る、という 1 行) |
| A-2: `test_backoff_requested_us.py` は module 専用でない — live な `dispatch_compute._child_environment` の PBS 3 変数除去 (`:1092`、他 test に同等 assert なし — 親が `test_pegasus_dispatch_compute.py` で検算)、policy registry の包含/非包含 pin (`:688`)、残る patch の mu01/mu02 意味検査 (`:230`/`:297`/`:1061`) を持つ | real | 採用 | 内 | **requested-us の対も残す**。裁定の「module + 専用 test」の前提 (専用) が崩れ、被覆を残す test 分割は削除でなく新しい編集になる (本題の削除だけ)。3 条件の確認は「専用 test でない」で不成立 → 残す |
| A-3 / B-3: 「残る test の受理集合は不変」は不成立 | real | 採用 | 内 | 記述を「残存 site に課す述語を維持する。共有 exact 表の期待集合は削除 site 分だけ縮み、削除 test の被覆は消える」へ訂正 |
| A-4 / B-4: pin 行数の単位 | real | 採用 | 内 | 確定集合では共有 test の変更は spawn 表 4 行 (`test_ccbench_spawn_sites.py:215–218`) だけ。`:73–75` と `test_p3_build_authority_cli.py:152` は requested-us 保持により触らない |
| B-2: 保持理由の表現 (fanout は「将来直す」でなく「一回限り・結果凍結の分類が成立しない」、t1994 qualification は「観測器だが D2035 の連言を test が直接検査」、counterfactual は「文書・seed 契約の実装で三者照合の対象」) | real | 採用 | 内 | insight の「残すもの」表をこの表現にする |
| plan: `output/insights/2026-08-28_t1941-backoff-requested-us/job-body.sh:383` が driver を呼ぶ | real | 記録のみ | — | requested-us 保持で影響なし |
| plan / B: 台帳 coverage (`test_acceptance_schedule_order.py:704`) は現 HEAD 実走で確定 | real | 採用 | 内 | 焦点走に `test_acceptance_schedule_order.py` を含める (G5 は real repo 収集を行う test なので計算ノード dispatch) |
| plan: 閉包 47・import 例外台帳の直接確認 | real | 採用 | 内 | 焦点走に `test_p3_b4_wiring_probe.py`、`test_campaign_import_invariant.py` を追加 |
| B: M5 (未 stage 削除) は harness で表現できず別観測 | real | 不採用 (登録しない) | — | DW-O11 の gate は `test_run_tests_preflight.py::test_unstaged_deletion_gate_detects_count_and_scrubs_git_env` ほかが既に正例・負例で守る。本 wave は `git rm` で stage する (author 指示) |
| 追加削除 (残す 9 対から) | A/B とも 0 対 | — | — | 変更なし |

## plan v2 (確定)

**削除集合 = 13 file (Python 4,337 行)**:

R1 (6): `orchestrator/campaign/p2_5.py`、`orchestrator/campaign/s6_amendment_20260713_fence.py`、`orchestrator/manual_probes/t1994_capdrop_probe.py`、`orchestrator/manual_probes/t1994_readonly_snapshot_liveness.py`、`orchestrator/manual_probes/t1994_rootview_probe.py`、`orchestrator/manual_probes/t1994_seccomp_probe.py`。

R3 (4 対 = 7 file): `orchestrator/campaign/s6_canary_rename.py` (専用 test なし)、`tools/insights_date_layout.py` + `orchestrator/tests/test_insights_date_layout.py`、`tools/migrate_output_gzip.py` + `orchestrator/tests/test_migrate_output_gzip.py`、`tools/plotting/plot_t2266_tail_mechanism.py` + `orchestrator/tests/test_plot_t2266_tail_mechanism.py`。

**共有 test の追随 (author)**: `orchestrator/tests/test_ccbench_spawn_sites.py:215–218` の 4 行 (`("campaign/s6_canary_rename.py", "<module>.export_stock"): 3,` / `git_apply` / `normalize_cxx` / `verify`) を削除。他は 1 byte も変えない。

**docs の追随 (親、統合 commit)**: `orchestrator/tests/README.md:138` の `- test_insights_date_layout.py` を削除。

**残す (R3 の 11 対)**: brief の 9 対 + `backoff_requested_us.py` 対 (A-2) + `t1434_t1222_science_slice.py` 対 (P1)。

受入所要台帳の stale = 62 + 12 + 22 = **96 node / 6.349 worker 秒** (台帳の記録値、実測時間ではない)。台帳は編集しない。

## 不変条件 (訂正版)

- 削除と上記追随だけ。新しい gate・検査・台帳・一般化・互換層を足さない。残す module は 1 byte も変えない。
- `test_p3_b4_wiring_probe.py` の閉包 module 数 pin (47) に触れない (consult B が読取専用で閉包を再計算し 47・交差 0 を確認)。
- `patches/`、`output/`、凍結成果物・事前登録は変えない。
- 残存 site に課す述語を維持する。共有 exact 表 (spawn-site) の期待集合は canary の 4 site 分だけ縮む。削除 test 3 本 (96 node) の被覆は消える (被検体ごと消える)。
- DW-O11: 削除は `git rm` で stage する。

## 変異事前登録 (DW-M01、実装後に harness で走らせる。baseline = 削除 + 追随を commit した tip)

runner = `tools/run_tests.py -q -rf orchestrator/tests/test_ccbench_spawn_sites.py orchestrator/tests/test_plain_runner_coverage.py` (計算ノード dispatch)。

| id | 変異 (post-deletion tip に対する置換) | 期待 | 単一理由 |
|---|---|---|---|
| m0-equivalent-comment | `test_ccbench_spawn_sites.py` の `("campaign/s6_proposal_rounds.py", "<module>.call_headless"): 1,` 行の直前へコメント 1 行 `    # (equivalent mutation marker: comment only)` を挿入 | SURVIVED (expected_nodes []) | 過剰拒否の正例 (DW-M01) |
| m2-spawn-line-left | 同 file の同じ行の直前へ `    ("campaign/s6_canary_rename.py", "<module>.export_stock"): 3,` を戻す (module は削除済みのまま) | KILLED、`orchestrator/tests/test_ccbench_spawn_sites.py::test_reviewed_process_launch_inventory_is_recursive_and_exact` | exact Counter 比較 (`:2840–2847`) だけが赤。measurement 側 (`:4100–4107`) は Counter 減算で非正値を落とすので赤にならない (consult B) |
| m4-readme-line-left | `orchestrator/tests/README.md` の `- test_env_contract.py\n- test_layer3_report.py\n` を `- test_env_contract.py\n- test_insights_date_layout.py\n- test_layer3_report.py\n` に戻す (test file は削除済みのまま) | KILLED、`orchestrator/tests/test_plain_runner_coverage.py::test_allowlist_has_no_stale_or_self_runnable_entries` | `:81–83` の stale 検査が先に拒否し、self-runnable 検査へ到達しない (consult B) |

DW-M08: 期待 node が事前に 1 本ずつ確定しているので probe 走は行わず本走 1 回。実装後、置換 anchor が 1 箇所であることと単一理由を再確認してから spec を凍結する。

## 段 5 の分割と所有

- author 1 本 (Codex `role=author`、workspace-write、unit worktree `t2800-unit-delete`、base = wave tip `947fd160a`)。所有 = 削除 13 file + `test_ccbench_spawn_sites.py` の 4 行。commit・docs 編集はしない。
- 親: README 1 行、統合 commit、焦点走、変異、受入、記録。

## 焦点走 (親、計算ノード dispatch)

`tools/run_tests.py -q -rf orchestrator/tests/test_ccbench_spawn_sites.py orchestrator/tests/test_plain_runner_coverage.py orchestrator/tests/test_acceptance_schedule_order.py orchestrator/tests/test_p3_build_authority_cli.py orchestrator/tests/test_p3_b4_wiring_probe.py orchestrator/tests/test_campaign_import_invariant.py orchestrator/tests/test_t2187_adaptive_const_probe.py`
