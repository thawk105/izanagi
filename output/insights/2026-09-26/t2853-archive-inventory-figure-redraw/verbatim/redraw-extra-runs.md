# redraw.log の外で実行した 3 図の rc と出力時刻

`redraw.log` (script `redraw.sh`) に rc 行が無い 3 回の実行。rc は親の shell が各 command の直後に表示した値 (log file ではなく会話内の観測)、時刻は出力 file の mtime (`stat -c %y`)。

| 図 | command (出力 prefix) | rc | 出力 3 file の mtime (JST) |
|---|---|---|---|
| fig3b | `python3 tools/plotting/plot_arc_status.py --states tools/plotting/arc_status_story_2026-09-19.json <job dir>/redraw/fig3b_arc_status_2026-09-20` (script の前に単独で) | 0 | 14:00:12 (png・pdf・provenance) |
| fig2c | `python3 tools/plotting/plot_b10_extended_backoff.py redraw-tmp/fig2c_b10_extended_backoff /work/1/SFC/tanab/b10-backoff-grid-runs5` (worktree 内の一時 dir、後で job dir へ移動。stdout は redraw.log に追記) | 0 | 14:02:07〜14:02:08 |
| fig4 | `python3 tools/plotting/plot_s1_9pair.py redraw-tmp/fig4_s1a_9pair_direct_comparison output/reports/s1_direct_comparison/report.json --develop … --block2 …` (同上) | 0 | 14:02:12〜14:02:13 |

fig2c・fig4 は script の中では出力 prefix が repo 外のため rc=2 / rc=1 で拒否された (redraw.log の `rc[fig2c]=2`・`rc[fig4]=1`)。上の再実行はその後の 1 回ずつである。
