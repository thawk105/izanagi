# 親の追加観測 (段 1〜2、2026-09-21、worktree HEAD = local main d99c556df)

いずれも親が Bash で実測した値。command は各行に記す。

1. 受入赤の node (項 9 の 2 例、`grep "^FAILED\|failed.*passed"`):
   - T-2737 `dev-wave-t2737-noninert-codex/acceptance-child-final-1.log` (mtime 2026-09-19 21:38:47): 3 failed, 25276 passed, 69 skipped。
     FAILED = `test_ccbench_spawn_sites.py::test_define_sink_cross_product_classifies_t2155_production_sinks_exactly`、`::test_define_sink_cross_product_t2520_certify_entry_removal`、`::test_patch_define_inventory_matches_condition_gate_registry`。
   - T-2797 `dev-wave-t2797-b5-contrast/acceptance-child-final-1.log` (mtime 2026-09-21 04:28:58): 2 failed, 26725 passed, 69 skipped。
     FAILED = `test_ccbench_spawn_sites.py::test_reviewed_ccbench_measurement_launches_use_bounded_sites`、`::test_reviewed_process_launch_inventory_is_recursive_and_exact`。
2. T-2737 実装 commit `0bd0895da` (2026-09-19 07:51:41 +0900) の変更 file (`git show --stat`): production は `tools/pegasus/run_ss2pl_lock_study.py` (+40/-) と
   `patches/ss2pl-lock-protocol-study.patch` (207 行)。他は docs / insight。
3. T-2820 = D2194 項 8 (裁定 2026-09-21、worklog archive `worklog-phase3-0921-1771.md` で「裁定済み → 実装手番 (Codex author)」、entry 1794 の次の一手まで持ち越し)。
   現行 `docs/dev-wave/operations.md` DW-O26 はまだ 4 群。job dir `dev-wave-t2820-branch-residue` は別件 (残骸 branch) で T 番号が衝突している疑い (本 wave の scope 外)。
4. 所要台帳 `orchestrator/tests/acceptance_duration_ledger.json` (最終 commit `b820bbaa7` 2026-09-21 12:19:26 +0900): `test_ccbench_spawn_sites.py` は 47 node、直列 224.53 秒。
   47 node 中 5 node が整数値 (上位 = 100.0 / 43.0 / 41.0 / 13.0 / 8.0 秒)、全 24,812 node 中の整数値は 528。
   inventory 4 群の直列値: test_campaign.py 152.16 / test_official_perf_closure.py 36.83 / test_p3_exploration_namespace.py 38.86 / test_p3_b4_wiring_probe.py 110.34。
   `test_check_subprocess_bytecode_guard.py` 37.01。全 357 file の直列合計 18,067.7 秒、file 別 p50 1.87 / p90 111.29 / max 2,804.04 秒。
5. 列挙型探索 (`grep -lE "\.rglob\(|\.glob\(|\.iterdir\(|os\.walk\(" orchestrator/tests/test_*.py`): 369 file 中 130 file (`test_ccbench_spawn_sites.py` を含む)。
   台帳の直列合計 13,519.1 秒 (全体 18,067.7 秒の 74.8 %、12 file は台帳に無い)。tmp_path を列挙するだけの file も含む粗い上限。
6. t2797 の焦点集合 21 file = `dev-wave-t2797-b5-contrast/focus/run-focus.sh` の既定 argv (変更 test 7 のうち `test_ccbench_spawn_sites.py` は含まれない。
   含まれる変更 test は 6 = b5_generator_contrast / b5_generator_contrast_report / b5_contrast_launch / p3_s4_loop / p3_s4_loop_job_contract / hooks)。
   focus-3 (request 14257.nqsv): Created 04:16:37 → Started 04:16:44 → Ended 04:18:48、2526 passed, 10 skipped in 122.25s。
   dispatch は worktree の `output/pegasus-dispatch/orphan-holds/` に create-only の hold を書く (log 3 行目)。
7. site 判定 (`orchestrator/campaign/site_policy.py:30-37`, `:66-77`): hostname (bnode) と NQSV 証拠で決め、`PBS_JOBID` 等の env は分類条件にしない。
8. 標本外: 2026-09-21 07:38〜14:06:02 JST に land 記録 (status=landed) を持つ wave は 12 (dwm08-selfrun-probe / waiter-collect-latency / acceptance-resubmit-causes /
   focus-run-count-diagnosis / provenance-cold-diag / land-roundtrip-diagnosis / t2812-old-series-realignment / t2807-b8-effective / login-check-wall /
   codex-selfrun-precheck / t2344-source-bound-emitters / t2795-k2-pair-repair)。項 4 (a) の標本 (12 wave、07:38 固定) には入れない。
9. plan §3 の「21 file の argv は特定不能」への補足: `dev-wave-t2797-b5-contrast/focus/detach-focus.sh` は `run-focus.sh <tag> [files...]` を呼び、
   files 省略時は `run-focus.sh` の既定 21 file を使う。focus-3.log (77 行) と focus-3.spawn.log (空) は argv を記録していない。
   t2797 insight §4 と acceptance-resubmit-causes §5 の「21 file」と件数は一致する。親は計測用集合として既定 21 file を使い、「focus-3 と同一の argv」とは主張しない。
10. 親の事後上限 (plan §4 の P2 批判を受けた試算、攻撃対象): 「置換」を「その走を単独走 1 file に変えても、同じ wave の後続の集合走が最終 tip を覆い、
   その走が赤で次 fix の入力になっていない」= 事後的に冗長な緑の集合走 + merge 後の再走、と広く取ると、
   t2804 focus-1 (緑、後に focus-2 が最終集合) 1 本、residue f2 (緑、後に f3 / f4) 1 本、t2797 focus-1 / focus-2 (緑、後に focus-3) 2 本 = 計 4 本。
   t2344 f2 (fix1 tip の最後の全集合走、f3 は inventory 4 群 + 変更 test 5 の部分集合) と t2814 / t2810 は 0。
   ⇒ 事後の最良でも置換で覆えるのは 20 中 4、残件は 16〜20 (事前には冗長と分からないので上端 20)。単独走は受入前の任意 tip でよいとする前回診断の読みに依る。
