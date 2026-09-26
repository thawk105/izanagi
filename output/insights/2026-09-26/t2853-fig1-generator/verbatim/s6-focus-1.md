## 対応表

| 裁定 1 の採用行 | 判定 | 根拠 |
|---|---|---|
| A-M1 | closed | p 注記は計算した `d['p']` を書式化する。[生成器:305](/work/1/SFC/tanab/izanagi/.claude/worktrees/t2853-fig1-redraw/tools/plotting/plot_p2_5_search_cost.py:305) |
| A-M2 / B-M1 | partial | 各 campaign の WAL・lock から条件を抽出するが、caption の共通条件は read-heavy の値だけを使う。[生成器:223](/work/1/SFC/tanab/izanagi/.claude/worktrees/t2853-fig1-redraw/tools/plotting/plot_p2_5_search_cost.py:223) |
| A-M3 | closed | closure は生成器 hash を照合せず、着地 test は README への caption 包含を確認する。[生成器:334](/work/1/SFC/tanab/izanagi/.claude/worktrees/t2853-fig1-redraw/tools/plotting/plot_p2_5_search_cost.py:334)、[test:160](/work/1/SFC/tanab/izanagi/.claude/worktrees/t2853-fig1-redraw/orchestrator/tests/test_plot_p2_5_search_cost.py:160) |
| A-S1 | closed | caption に各記号・線種の意味が入った。[生成器:229](/work/1/SFC/tanab/izanagi/.claude/worktrees/t2853-fig1-redraw/tools/plotting/plot_p2_5_search_cost.py:229) |
| B-S1 | closed | 照合対象を裁定の描画値に絞った。[生成器:134](/work/1/SFC/tanab/izanagi/.claude/worktrees/t2853-fig1-redraw/tools/plotting/plot_p2_5_search_cost.py:134) |
| B-S2 | partial | M6 の期待 kill は照合失敗へ訂正されたが、報告は「想定」で、指定された probe の node 確定はない。[fix 報告:28](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2853-fig1-redraw/codex/s6-fix-1.md:28) |
| P-M1 | closed | 自走用 `_run()` と入口を追加した。[test:171](/work/1/SFC/tanab/izanagi/.claude/worktrees/t2853-fig1-redraw/orchestrator/tests/test_plot_p2_5_search_cost.py:171) |
| P-S1 | closed | 軸・文字色を `#2a2a2a` に設定した。[生成器:280](/work/1/SFC/tanab/izanagi/.claude/worktrees/t2853-fig1-redraw/tools/plotting/plot_p2_5_search_cost.py:280) |
| P-S2 | closed | panel 題を左寄せにした。[生成器:319](/work/1/SFC/tanab/izanagi/.claude/worktrees/t2853-fig1-redraw/tools/plotting/plot_p2_5_search_cost.py:319) |
| P-S3 | closed | 点の横ずらしを 0.03 刻みに広げた。[生成器:292](/work/1/SFC/tanab/izanagi/.claude/worktrees/t2853-fig1-redraw/tools/plotting/plot_p2_5_search_cost.py:292) |
| P-N1 | closed | 上余白を `.84` に詰めた。[生成器:330](/work/1/SFC/tanab/izanagi/.claude/worktrees/t2853-fig1-redraw/tools/plotting/plot_p2_5_search_cost.py:330) |

## 新規所見

- **F-M1** — [生成器:223](/work/1/SFC/tanab/izanagi/.claude/worktrees/t2853-fig1-redraw/tools/plotting/plot_p2_5_search_cost.py:223)：balanced／write-heavy のスレッド数などが read-heavy と異なっても、caption は read-heavy の条件を全体の条件として表示する。共通条件の campaign 間一致を検査するか、条件を workload ごとに記載する。
- **F-S1** — [test:125](/work/1/SFC/tanab/izanagi/.claude/worktrees/t2853-fig1-redraw/orchestrator/tests/test_plot_p2_5_search_cost.py:125)：`main()` と同じ `caption()` を再実行する等式は caption 内容の独立検査にならず、F-M1 を検出できない。各 campaign の条件と caption の対応を別に検査する。

## 判定

**NO-GO。** F-M1 の修正が必要。

## 総括

静的検査では、現行データの条件値・試行数・未到達数・k は caption と図で整合する。生成器 383/450 行、test 206/300 行。テスト実走は親の担当。