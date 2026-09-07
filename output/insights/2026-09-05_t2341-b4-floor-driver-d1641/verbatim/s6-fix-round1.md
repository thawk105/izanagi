F1〜F6 をすべて修正しました。段 5 の未 commit 差分は保持し、commit と docs 編集はしていません。

| 所見 | 変更内容 | 箇所 |
|---|---|---|
| F1 | overflow-safe な偶数 median と最大有限 float の正例 | [driver:2431](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2341-author/orchestrator/campaign/floor_pair_driver.py:2431)、[test:2013](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2341-author/orchestrator/tests/test_floor_pair_driver.py:2013) |
| F2 | 符号を変換前に判定する total helper。run と finalize の巨大 int 対称検査 | [driver:1319](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2341-author/orchestrator/campaign/floor_pair_driver.py:1319)、[test:2050](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2341-author/orchestrator/tests/test_floor_pair_driver.py:2050) |
| F3 | terminal を planned 1 / dropped 0 / complete 0 に整合 | [test:2429](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2341-author/orchestrator/tests/test_floor_pair_driver.py:2429) |
| F4 | 5 境界を status/upper と summary/因果/derivation に分割。M11 専用高 D fixture を追加 | [test:2170](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2341-author/orchestrator/tests/test_floor_pair_driver.py:2170)、[test:2194](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2341-author/orchestrator/tests/test_floor_pair_driver.py:2194)、[test:2323](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2341-author/orchestrator/tests/test_floor_pair_driver.py:2323) |
| F5 | pre-probe test を改名し、measurement 例外後の post-probe と標本局所継続を別 node で復元 | [test:1514](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2341-author/orchestrator/tests/test_floor_pair_driver.py:1514)、[test:1573](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2341-author/orchestrator/tests/test_floor_pair_driver.py:1573) |
| F6 | pre/post × competing/indeterminate の4実経路を run→finalize で固定 | [test:1645](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2341-author/orchestrator/tests/test_floor_pair_driver.py:1645) |

変異を殺す node:

- M21: `test_mutation_21_max_finite_even_medians_generate_zero_upper`
- M22: `test_mutation_22_large_exact_int_is_total_in_run_and_artifact_rederivation[positive-overflow]` および `[negative-overflow]`

検査結果:

- 指定 harness: `175 passed / 0 failed`、1118.61 秒
- 初回は `174 passed / 1 failed`。失敗 node は `test_module_source_has_no_frozen_fallback_or_publish_bypass` で、段 5 差分中の `setdefault(` を動作等価な明示初期化へ修正後、全件再実走しました。
- `measure_point`: 1 call、位置引数 4、keyword 13 のままです。
- `git diff --check`: 成功
- 変更 path: 所有された 2 file のみ

## 総括

- 変更: production 1 file、test 1 file。fix 前後の diffstat 差は production 35行、test 288行。
- F1〜F6: 全件完了。
- test: 新設9 node、境界5 nodeを10 nodeへ分割、1 node改名。
- 実走: 175 passed / 0 failed。
- `measure_point`: 位置4 + keyword13、不変。
- 所有外への波及・変更: なし。
- commit・docs変更: なし。
- 未実装: なし。