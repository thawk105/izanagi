# 焦点走 (親、削除後の 2 file)

- command: `python3 tools/run_tests.py orchestrator/tests/test_s8b_holdout_freeze.py orchestrator/tests/test_p3_s4_loop.py -q -rf` (作業ツリー = 削除 patch 展開後、commit 前)
- dispatch: request 10888.nqsv (gen_S)、2026-09-19 22:55 投入 → 23:0x 完了
- 結果: 670 passed, 2 skipped in 36.40s、rc=0
- 変更前の同 2 file の node 数: 164 (holdout) + 514 (p3_s4_loop) = 678 → 削除後 672 (passed 670 + skipped 2)
- log: /work/1/SFC/tanab/dev-wave-jobs/dev-wave-test-inventory-prune/focus-run.log
