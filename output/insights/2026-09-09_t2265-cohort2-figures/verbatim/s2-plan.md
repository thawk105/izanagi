## A. 生死

**判定: GO。測定前停止の理由はない。** cohort 2 診断 3 cell と legacy performance 7 腕は意図的に別の表として扱われ、診断 cell 名を performance 集計表から引く経路はない。禁止された 4 file の改修は不要である。

- performance の固定集合は `none, stock, tuned, tuned-u10240, cw, cw-as, cw-as-dyn` である。[plot_dynamic_backoff.py:74](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2265-cohort2-perf6/tools/plotting/plot_dynamic_backoff.py:74)
- cohort 2 診断は別集合 `cw-as-dyn-c2-p0/p1/p2` として定義される。[plot_dynamic_backoff.py:79](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2265-cohort2-perf6/tools/plotting/plot_dynamic_backoff.py:79)
- 問題の test fixture は、performance 側を `_performance_document(index)` から作るため legacy 7 腕 x 168 点のままであり、cohort 2 のとき変更するのは A+B+C 化と `extime_s=6` だけである。[test_plot_dynamic_backoff.py:185](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2265-cohort2-perf6/orchestrator/tests/test_plot_dynamic_backoff.py:185) [test_plot_dynamic_backoff.py:391](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2265-cohort2-perf6/orchestrator/tests/test_plot_dynamic_backoff.py:391)
- 診断 fixture だけが cohort 2 の 3 cell、schema v4、extime 6 になる。[test_plot_dynamic_backoff.py:322](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2265-cohort2-perf6/orchestrator/tests/test_plot_dynamic_backoff.py:322) [test_plot_dynamic_backoff.py:363](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2265-cohort2-perf6/orchestrator/tests/test_plot_dynamic_backoff.py:363)
- 対象 test 自体もこの組合せを `load_inputs` へ渡し、18 診断 run と cohort 2 cell を確認している。[test_plot_dynamic_backoff.py:586](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2265-cohort2-perf6/orchestrator/tests/test_plot_dynamic_backoff.py:586)

全経路の静的確認:

1. `load_inputs`
   - 診断 schema v4 は cohort 2 の exact 3 cell と `expected_extime_s=6` を選ぶ。[plot_dynamic_backoff.py:661](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2265-cohort2-perf6/tools/plotting/plot_dynamic_backoff.py:661) [plot_dynamic_backoff.py:683](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2265-cohort2-perf6/tools/plotting/plot_dynamic_backoff.py:683)
   - その extime だけを performance parser へ渡す。[plot_dynamic_backoff.py:1254](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2265-cohort2-perf6/tools/plotting/plot_dynamic_backoff.py:1254)
   - performance row は常に legacy `CELLS` に対して検査される。診断 cell は参照しない。[plot_dynamic_backoff.py:399](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2265-cohort2-perf6/tools/plotting/plot_dynamic_backoff.py:399) [plot_dynamic_backoff.py:491](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2265-cohort2-perf6/tools/plotting/plot_dynamic_backoff.py:491)
   - 共通 identity の一致後、performance 集計と対比は performance 文書だけから作る。[plot_dynamic_backoff.py:1274](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2265-cohort2-perf6/tools/plotting/plot_dynamic_backoff.py:1274) [plot_dynamic_backoff.py:1282](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2265-cohort2-perf6/tools/plotting/plot_dynamic_backoff.py:1282)

2. `make_thread_figure`
   - `_aggregate_performance` は legacy 7 腕 x 3 workload x 8 threads の168行を必ず作る。[plot_dynamic_backoff.py:901](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2265-cohort2-perf6/tools/plotting/plot_dynamic_backoff.py:901)
   - 図はその aggregate map を同じ `CELLS` で引くため、完全な168点入力なら KeyError・空系列にならない。[plot_dynamic_backoff.py:1335](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2265-cohort2-perf6/tools/plotting/plot_dynamic_backoff.py:1335) [plot_dynamic_backoff.py:1353](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2265-cohort2-perf6/tools/plotting/plot_dynamic_backoff.py:1353)

3. `make_contrasts_figure`
   - H1-H7 の分子・分母はすべて legacy 7 腕内である。[plot_dynamic_backoff.py:133](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2265-cohort2-perf6/tools/plotting/plot_dynamic_backoff.py:133)
   - 各対内標本も performance 文書だけから引く。[plot_dynamic_backoff.py:970](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2265-cohort2-perf6/tools/plotting/plot_dynamic_backoff.py:970)
   - forest plot はこの24点 x 7対比を描き、診断 cell を参照しない。[plot_dynamic_backoff.py:1425](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2265-cohort2-perf6/tools/plotting/plot_dynamic_backoff.py:1425)

4. `make_diagnostic_figure`
   - diagnostic の `cell_order` と diagnostic の `runs` だけを引く。[plot_dynamic_backoff.py:1516](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2265-cohort2-perf6/tools/plotting/plot_dynamic_backoff.py:1516)
   - 色表には cohort 2 の3名称がすべて存在する。[plot_dynamic_backoff.py:1541](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2265-cohort2-perf6/tools/plotting/plot_dynamic_backoff.py:1541)
   - test は実 Figure を作り、cohort 2 の3ラベルが軸へ出ることを確認する。[test_plot_dynamic_backoff.py:608](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2265-cohort2-perf6/orchestrator/tests/test_plot_dynamic_backoff.py:608)

5. `build_provenance`
   - performance 入力記録と診断入力記録は別々に構築される。[plot_dynamic_backoff.py:1624](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2265-cohort2-perf6/tools/plotting/plot_dynamic_backoff.py:1624)
   - provenance は performance の aggregate/contrast と diagnostic の `_diagnostic_values` を別キーへ格納し、相互 cell lookup をしない。[plot_dynamic_backoff.py:1742](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2265-cohort2-perf6/tools/plotting/plot_dynamic_backoff.py:1742) [plot_dynamic_backoff.py:1748](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2265-cohort2-perf6/tools/plotting/plot_dynamic_backoff.py:1748)

6. `check_figure_layout`
   - thread と diagnostic は実寸 2 x 3 axes を返す。[plot_dynamic_backoff.py:1417](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2265-cohort2-perf6/tools/plotting/plot_dynamic_backoff.py:1417) [plot_dynamic_backoff.py:1606](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2265-cohort2-perf6/tools/plotting/plot_dynamic_backoff.py:1606)
   - contrasts は checker 契約用の 2 x 3 行列を返しつつ、checker が全 `fig.axes` を検査する設計である。[plot_dynamic_backoff.py:1481](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2265-cohort2-perf6/tools/plotting/plot_dynamic_backoff.py:1481)
   - main は3図すべてを保存前に checker へ通し、例外時は一切公開しない。[plot_dynamic_backoff.py:1796](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2265-cohort2-perf6/tools/plotting/plot_dynamic_backoff.py:1796) [FIGURE_CONVENTIONS.md:85](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2265-cohort2-perf6/tools/plotting/FIGURE_CONVENTIONS.md:85)

cohort 2 test は全 CLI 経路を直接は走らせず、`load_inputs` と diagnostic Figure までの被覆である。ただし、残る経路には診断 cell を performance 表から引く箇所がない。したがって、**この異種 cell 集合そのものによる KeyError・空系列・fail-closed 例外はない**。実データ固有の bbox は最終作図時の checker が判定するが、測定前停止の根拠ではない。

## B. 投入 argv

launcher は次の canonical submit tree へ `cd` してから実行する。

```bash
cd /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2265-cohort2-perf6/submit-tree
```

rep ごとに cell literal の開始位置を巡回させる必要がある。driver は入力順をそのまま `cell_order` へ書き、plot は `CELLS[i:] + CELLS[:i]` を要求するためである。[t2187_adaptive_const_probe.py:3684](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2265-cohort2-perf6/tools/pegasus/probes/t2187_adaptive_const_probe.py:3684) [plot_dynamic_backoff.py:462](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2265-cohort2-perf6/tools/plotting/plot_dynamic_backoff.py:462)

exact 7 行:

```bash
qsub -l elapstim_req=00:40:00 -v 'IZANAGI_T2187_MODE=performance,IZANAGI_T2187_BACKOFF_TRACE=0,IZANAGI_T2187_EXTIME=6,IZANAGI_T2187_CELLS=none:0:100:1000:10+stock:1:100:1000:10+tuned:1:1:1000:2560+tuned-u10240:1:1:1000:10240+cw:1:1:1000:2560:10000:10240:0:100:100:0+cw-as:1:1:1000:2560:10000:10240:1:1:4:0+cw-as-dyn:1:1:1000:2560:10000:10240:1:1:4:1,IZANAGI_T2187_WORKLOADS=write-heavy+balanced+read-heavy,IZANAGI_T2187_THREADS=6+12+18+24+30+36+42+48,IZANAGI_T2187_REP_INDEX=0,IZANAGI_T2187_STAGE=1,IZANAGI_T2187_OUT_DIR=/work/1/SFC/tanab/izanagi-job-evidence/dynamic-backoff/perf' /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2265-cohort2-perf6/submit-tree/tools/pegasus/probes/t2187_adaptive_const_probe.pbs
qsub -l elapstim_req=00:40:00 -v 'IZANAGI_T2187_MODE=performance,IZANAGI_T2187_BACKOFF_TRACE=0,IZANAGI_T2187_EXTIME=6,IZANAGI_T2187_CELLS=stock:1:100:1000:10+tuned:1:1:1000:2560+tuned-u10240:1:1:1000:10240+cw:1:1:1000:2560:10000:10240:0:100:100:0+cw-as:1:1:1000:2560:10000:10240:1:1:4:0+cw-as-dyn:1:1:1000:2560:10000:10240:1:1:4:1+none:0:100:1000:10,IZANAGI_T2187_WORKLOADS=write-heavy+balanced+read-heavy,IZANAGI_T2187_THREADS=6+12+18+24+30+36+42+48,IZANAGI_T2187_REP_INDEX=1,IZANAGI_T2187_STAGE=1,IZANAGI_T2187_OUT_DIR=/work/1/SFC/tanab/izanagi-job-evidence/dynamic-backoff/perf' /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2265-cohort2-perf6/submit-tree/tools/pegasus/probes/t2187_adaptive_const_probe.pbs
qsub -l elapstim_req=00:40:00 -v 'IZANAGI_T2187_MODE=performance,IZANAGI_T2187_BACKOFF_TRACE=0,IZANAGI_T2187_EXTIME=6,IZANAGI_T2187_CELLS=tuned:1:1:1000:2560+tuned-u10240:1:1:1000:10240+cw:1:1:1000:2560:10000:10240:0:100:100:0+cw-as:1:1:1000:2560:10000:10240:1:1:4:0+cw-as-dyn:1:1:1000:2560:10000:10240:1:1:4:1+none:0:100:1000:10+stock:1:100:1000:10,IZANAGI_T2187_WORKLOADS=write-heavy+balanced+read-heavy,IZANAGI_T2187_THREADS=6+12+18+24+30+36+42+48,IZANAGI_T2187_REP_INDEX=2,IZANAGI_T2187_STAGE=1,IZANAGI_T2187_OUT_DIR=/work/1/SFC/tanab/izanagi-job-evidence/dynamic-backoff/perf' /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2265-cohort2-perf6/submit-tree/tools/pegasus/probes/t2187_adaptive_const_probe.pbs
qsub -l elapstim_req=00:40:00 -v 'IZANAGI_T2187_MODE=performance,IZANAGI_T2187_BACKOFF_TRACE=0,IZANAGI_T2187_EXTIME=6,IZANAGI_T2187_CELLS=tuned-u10240:1:1:1000:10240+cw:1:1:1000:2560:10000:10240:0:100:100:0+cw-as:1:1:1000:2560:10000:10240:1:1:4:0+cw-as-dyn:1:1:1000:2560:10000:10240:1:1:4:1+none:0:100:1000:10+stock:1:100:1000:10+tuned:1:1:1000:2560,IZANAGI_T2187_WORKLOADS=write-heavy+balanced+read-heavy,IZANAGI_T2187_THREADS=6+12+18+24+30+36+42+48,IZANAGI_T2187_REP_INDEX=3,IZANAGI_T2187_STAGE=1,IZANAGI_T2187_OUT_DIR=/work/1/SFC/tanab/izanagi-job-evidence/dynamic-backoff/perf' /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2265-cohort2-perf6/submit-tree/tools/pegasus/probes/t2187_adaptive_const_probe.pbs
qsub -l elapstim_req=00:40:00 -v 'IZANAGI_T2187_MODE=performance,IZANAGI_T2187_BACKOFF_TRACE=0,IZANAGI_T2187_EXTIME=6,IZANAGI_T2187_CELLS=cw:1:1:1000:2560:10000:10240:0:100:100:0+cw-as:1:1:1000:2560:10000:10240:1:1:4:0+cw-as-dyn:1:1:1000:2560:10000:10240:1:1:4:1+none:0:100:1000:10+stock:1:100:1000:10+tuned:1:1:1000:2560+tuned-u10240:1:1:1000:10240,IZANAGI_T2187_WORKLOADS=write-heavy+balanced+read-heavy,IZANAGI_T2187_THREADS=6+12+18+24+30+36+42+48,IZANAGI_T2187_REP_INDEX=4,IZANAGI_T2187_STAGE=1,IZANAGI_T2187_OUT_DIR=/work/1/SFC/tanab/izanagi-job-evidence/dynamic-backoff/perf' /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2265-cohort2-perf6/submit-tree/tools/pegasus/probes/t2187_adaptive_const_probe.pbs
qsub -l elapstim_req=00:40:00 -v 'IZANAGI_T2187_MODE=performance,IZANAGI_T2187_BACKOFF_TRACE=0,IZANAGI_T2187_EXTIME=6,IZANAGI_T2187_CELLS=cw-as:1:1:1000:2560:10000:10240:1:1:4:0+cw-as-dyn:1:1:1000:2560:10000:10240:1:1:4:1+none:0:100:1000:10+stock:1:100:1000:10+tuned:1:1:1000:2560+tuned-u10240:1:1:1000:10240+cw:1:1:1000:2560:10000:10240:0:100:100:0,IZANAGI_T2187_WORKLOADS=write-heavy+balanced+read-heavy,IZANAGI_T2187_THREADS=6+12+18+24+30+36+42+48,IZANAGI_T2187_REP_INDEX=5,IZANAGI_T2187_STAGE=1,IZANAGI_T2187_OUT_DIR=/work/1/SFC/tanab/izanagi-job-evidence/dynamic-backoff/perf' /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2265-cohort2-perf6/submit-tree/tools/pegasus/probes/t2187_adaptive_const_probe.pbs
qsub -l elapstim_req=00:40:00 -v 'IZANAGI_T2187_MODE=performance,IZANAGI_T2187_BACKOFF_TRACE=0,IZANAGI_T2187_EXTIME=6,IZANAGI_T2187_CELLS=cw-as-dyn:1:1:1000:2560:10000:10240:1:1:4:1+none:0:100:1000:10+stock:1:100:1000:10+tuned:1:1:1000:2560+tuned-u10240:1:1:1000:10240+cw:1:1:1000:2560:10000:10240:0:100:100:0+cw-as:1:1:1000:2560:10000:10240:1:1:4:0,IZANAGI_T2187_WORKLOADS=write-heavy+balanced+read-heavy,IZANAGI_T2187_THREADS=6+12+18+24+30+36+42+48,IZANAGI_T2187_REP_INDEX=6,IZANAGI_T2187_STAGE=1,IZANAGI_T2187_OUT_DIR=/work/1/SFC/tanab/izanagi-job-evidence/dynamic-backoff/perf' /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2265-cohort2-perf6/submit-tree/tools/pegasus/probes/t2187_adaptive_const_probe.pbs
```

値の根拠:

- plus 区切りは qsub 境界専用で、PBS が comma 区切りへ戻す。[t2187_adaptive_const_probe.pbs:67](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2265-cohort2-perf6/tools/pegasus/probes/t2187_adaptive_const_probe.pbs:67) [t2187_adaptive_const_probe.pbs:262](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2265-cohort2-perf6/tools/pegasus/probes/t2187_adaptive_const_probe.pbs:262)
- 7 literal は plot の configuration と一致する。[plot_dynamic_backoff.py:97](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2265-cohort2-perf6/tools/plotting/plot_dynamic_backoff.py:97)
- 既存 `978014` の `grid_spec` と rep 0 の文字列は完全一致する。[978014 JSON:8](/work/1/SFC/tanab/izanagi-job-evidence/dynamic-backoff/perf/stage1-rep0-0_978014.nqsv.json:8)
- workload、threads は plot の固定軸である。[plot_dynamic_backoff.py:71](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2265-cohort2-perf6/tools/plotting/plot_dynamic_backoff.py:71)
- PBS は mode、trace、extime、rep、stage を読み、performance driver argv へ渡す。[t2187_adaptive_const_probe.pbs:70](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2265-cohort2-perf6/tools/pegasus/probes/t2187_adaptive_const_probe.pbs:70) [t2187_adaptive_const_probe.pbs:430](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2265-cohort2-perf6/tools/pegasus/probes/t2187_adaptive_const_probe.pbs:430)
- 拡張 cell を含むので dynamic output directory は必須であり、指定 prefix 下でなければ拒否される。[t2187_adaptive_const_probe.pbs:243](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2265-cohort2-perf6/tools/pegasus/probes/t2187_adaptive_const_probe.pbs:243)
- 出力名は `stage1-repN-${PBS_JOBID//:/_}.json` になる。[t2187_adaptive_const_probe.pbs:419](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2265-cohort2-perf6/tools/pegasus/probes/t2187_adaptive_const_probe.pbs:419)

`IZANAGI_T2187_STEP_POLICY_SEED` は**指定しない**。7腕には12-field の policy 2 cell がない。PBS は末尾 `:2` の12-field cell があるときだけ seed を必須にし、driver も `cell.step_policy == 2` のときだけ要求する。[t2187_adaptive_const_probe.pbs:146](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2265-cohort2-perf6/tools/pegasus/probes/t2187_adaptive_const_probe.pbs:146) [t2187_adaptive_const_probe.py:3139](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2265-cohort2-perf6/tools/pegasus/probes/t2187_adaptive_const_probe.py:3139)

walltime と内側予算:

- `-l elapstim_req=00:40:00`、すなわち2400秒を維持する。PBS の既定値も同じである。[t2187_adaptive_const_probe.pbs:5](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2265-cohort2-perf6/tools/pegasus/probes/t2187_adaptive_const_probe.pbs:5)
- 既存実測上端731秒へ `168 x (6-3) = 504` 秒を加えると上限見積りは1235秒。2400秒との差は1165秒である。[s1-brief.md:117](/home/SFC/tanab/.claude/jobs/4e2c74ed/tmp/wave/s1-brief.md:117)
- `OUTER_WALLTIME_S`、`BUILD_BUDGET_S`、`PROLOGUE_BUDGET_S`、`EXIT_MARGIN_S` は performance 分岐ではdriverへ渡らず、certify 分岐だけで使う。[t2187_adaptive_const_probe.pbs:420](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2265-cohort2-perf6/tools/pegasus/probes/t2187_adaptive_const_probe.pbs:420) [t2187_adaptive_const_probe.pbs:447](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2265-cohort2-perf6/tools/pegasus/probes/t2187_adaptive_const_probe.pbs:447) よって今回の7行には入れず、extime 6 に合わせた変更も不要。
- 参考に certify の既定契約は  
  `540 prologue + 900 build + 180 run + 120 positive-control + 5400 verifier + 300 exit = 7440 < 8100 outer`  
  で成立する。[t2187_adaptive_const_probe.py:107](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2265-cohort2-perf6/tools/pegasus/probes/t2187_adaptive_const_probe.py:107) [t2187_adaptive_const_probe.py:121](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2265-cohort2-perf6/tools/pegasus/probes/t2187_adaptive_const_probe.py:121) [t2187_adaptive_const_probe.py:1458](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2265-cohort2-perf6/tools/pegasus/probes/t2187_adaptive_const_probe.py:1458)

## C. identity

`_common_identity` が比較する raw field は、実際には `patch_stack` 自体も含む15個である。[plot_dynamic_backoff.py:253](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2265-cohort2-perf6/tools/plotting/plot_dynamic_backoff.py:253) 漏れを避けて全15個を判定する。

| field | 新 performance の書込み経路 | cohort 2 診断との判定 |
|---|---|---|
| `repo_head` | PBS が `git -C "$REPO_ROOT" rev-parse HEAD` を採り driver へ渡す。[PBS:48](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2265-cohort2-perf6/tools/pegasus/probes/t2187_adaptive_const_probe.pbs:48) driver が再照合後に書く。[driver:3635](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2265-cohort2-perf6/tools/pegasus/probes/t2187_adaptive_const_probe.py:3635) | **一致。** detached `8bdf173cc` からなら full SHA `8bdf173cc81e5371db7b7bcddb8bdcbb5aeff235`。診断実値は同値。[985851 JSON:19](/work/1/SFC/tanab/izanagi-job-evidence/dynamic-backoff/trace/t2265-cohort2/stage1-rep0-0_985851.nqsv.json:19) |
| `prereg_sha256` | 常に `docs/dynamic-backoff-preregistration.md` の bytes を hash する。[driver:84](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2265-cohort2-perf6/tools/pegasus/probes/t2187_adaptive_const_probe.py:84) [driver:951](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2265-cohort2-perf6/tools/pegasus/probes/t2187_adaptive_const_probe.py:951) | **一致。** extime と無関係で、bytes 不変なら `cc8975...ee68`。[985851 JSON:20](/work/1/SFC/tanab/izanagi-job-evidence/dynamic-backoff/trace/t2265-cohort2/stage1-rep0-0_985851.nqsv.json:20) |
| `ccbench_commit` | `CURRENT_PIN` を書く。[driver:47](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2265-cohort2-perf6/tools/pegasus/probes/t2187_adaptive_const_probe.py:47) [driver:3701](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2265-cohort2-perf6/tools/pegasus/probes/t2187_adaptive_const_probe.py:3701) | **一致:** `511c953`。[985851 JSON:29](/work/1/SFC/tanab/izanagi-job-evidence/dynamic-backoff/trace/t2265-cohort2/stage1-rep0-0_985851.nqsv.json:29) |
| `ccbench_head` | `_ccbench_head` が full pin と exact 比較し、その値を書く。[driver:644](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2265-cohort2-perf6/tools/pegasus/probes/t2187_adaptive_const_probe.py:644) [driver:3702](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2265-cohort2-perf6/tools/pegasus/probes/t2187_adaptive_const_probe.py:3702) | **一致:** `511c9538e4e8efa54b45cda62e72389ed3b706ec`。[985851 JSON:30](/work/1/SFC/tanab/izanagi-job-evidence/dynamic-backoff/trace/t2265-cohort2/stage1-rep0-0_985851.nqsv.json:30) |
| `driver_sha256` | 実行中の `__file__` bytes を hash。[driver:916](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2265-cohort2-perf6/tools/pegasus/probes/t2187_adaptive_const_probe.py:916) | **一致:** `8d5c0c...9fa64`。診断実値と、brief が示す8bdf側のbytesが同じ。[985851 JSON:31](/work/1/SFC/tanab/izanagi-job-evidence/dynamic-backoff/trace/t2265-cohort2/stage1-rep0-0_985851.nqsv.json:31) [s1-brief.md:45](/home/SFC/tanab/.claude/jobs/4e2c74ed/tmp/wave/s1-brief.md:45) |
| `pbs_sha256` | driver が同名 `.pbs` の bytes を hash。[driver:91](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2265-cohort2-perf6/tools/pegasus/probes/t2187_adaptive_const_probe.py:91) [driver:919](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2265-cohort2-perf6/tools/pegasus/probes/t2187_adaptive_const_probe.py:919) | **一致:** `cc0ee8...58e85`。[985851 JSON:32](/work/1/SFC/tanab/izanagi-job-evidence/dynamic-backoff/trace/t2265-cohort2/stage1-rep0-0_985851.nqsv.json:32) |
| `repo_status_clean` | PBS が tracked status を検査し `--repo-clean 1`、driver が再検査して `True` を書く。[PBS:53](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2265-cohort2-perf6/tools/pegasus/probes/t2187_adaptive_const_probe.pbs:53) [driver:893](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2265-cohort2-perf6/tools/pegasus/probes/t2187_adaptive_const_probe.py:893) | **一致:** `true`。[985851 JSON:63](/work/1/SFC/tanab/izanagi-job-evidence/dynamic-backoff/trace/t2265-cohort2/stage1-rep0-0_985851.nqsv.json:63) |
| `patch_sha256` | `_patch_stack_identity` が patch A を hash し固定 SHA と照合。[driver:806](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2265-cohort2-perf6/tools/pegasus/probes/t2187_adaptive_const_probe.py:806) | **一致:** `9b2153...8f54b`。[985851 JSON:66](/work/1/SFC/tanab/izanagi-job-evidence/dynamic-backoff/trace/t2265-cohort2/stage1-rep0-0_985851.nqsv.json:66) |
| `dynamic_patch_sha256` | 同関数が patch B bytes を hash。[driver:815](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2265-cohort2-perf6/tools/pegasus/probes/t2187_adaptive_const_probe.py:815) | **一致:** `f3fe6b...df824`。[985851 JSON:67](/work/1/SFC/tanab/izanagi-job-evidence/dynamic-backoff/trace/t2265-cohort2/stage1-rep0-0_985851.nqsv.json:67) |
| `counterfactual_patch_sha256` | 同関数が patch C bytes を hash。[driver:818](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2265-cohort2-perf6/tools/pegasus/probes/t2187_adaptive_const_probe.py:818) | **一致:** `4c04ca...d2ff`。[985851 JSON:68](/work/1/SFC/tanab/izanagi-job-evidence/dynamic-backoff/trace/t2265-cohort2/stage1-rep0-0_985851.nqsv.json:68) |
| `patch_stack` | A、B、C の順で常に3 entry を組む。[driver:821](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2265-cohort2-perf6/tools/pegasus/probes/t2187_adaptive_const_probe.py:821) | **一致:** 診断も A+B+C。[985851 JSON:69](/work/1/SFC/tanab/izanagi-job-evidence/dynamic-backoff/trace/t2265-cohort2/stage1-rep0-0_985851.nqsv.json:69) |
| `patch_stack_sha256` | version headerと順序付き `path sha` 行を hash。[driver:826](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2265-cohort2-perf6/tools/pegasus/probes/t2187_adaptive_const_probe.py:826) | **一致:** `14ac8f...91082`。[985851 JSON:83](/work/1/SFC/tanab/izanagi-job-evidence/dynamic-backoff/trace/t2265-cohort2/stage1-rep0-0_985851.nqsv.json:83) |
| `records` | pinned driver の `p2_2.RECORDS` を import し payload へ書く。[driver:3632](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2265-cohort2-perf6/tools/pegasus/probes/t2187_adaptive_const_probe.py:3632) [driver:3695](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2265-cohort2-perf6/tools/pegasus/probes/t2187_adaptive_const_probe.py:3695) | **一致:** `1000000`。[985851 JSON:23](/work/1/SFC/tanab/izanagi-job-evidence/dynamic-backoff/trace/t2265-cohort2/stage1-rep0-0_985851.nqsv.json:23) |
| `extime_s` | explicit env `6`をPBSが `--extime` へ渡し、driverが書く。[PBS:73](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2265-cohort2-perf6/tools/pegasus/probes/t2187_adaptive_const_probe.pbs:73) [driver:3696](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2265-cohort2-perf6/tools/pegasus/probes/t2187_adaptive_const_probe.py:3696) | **一致:** `6`。[985851 JSON:24](/work/1/SFC/tanab/izanagi-job-evidence/dynamic-backoff/trace/t2265-cohort2/stage1-rep0-0_985851.nqsv.json:24) |
| `clocks_per_us` | `env_contract.lookup("pegasus")` の固定 contract 値を import 時に読む。[driver:98](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2265-cohort2-perf6/tools/pegasus/probes/t2187_adaptive_const_probe.py:98) payload と測定へ同じ値を渡す。[driver:3698](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2265-cohort2-perf6/tools/pegasus/probes/t2187_adaptive_const_probe.py:3698) [driver:3792](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2265-cohort2-perf6/tools/pegasus/probes/t2187_adaptive_const_probe.py:3792) | **一致:** `2100`。[985851 JSON:26](/work/1/SFC/tanab/izanagi-job-evidence/dynamic-backoff/trace/t2265-cohort2/stage1-rep0-0_985851.nqsv.json:26) |

`clocks_per_us` は各ノードで校正する測定値ではなく、hard-selected Pegasus contract の固定値である。したがって、7本が別ノードへ散ってもこの field がノードごとに変わる経路はなく、identity 不一致の危険はない。

schema は非 trace の `_artifact_contract_metadata` が `SCHEMA_VERSION`、すなわち `izanagi-cicada-adaptive-3const-probe/v3` を選ぶ。[t2187_adaptive_const_probe.py:59](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2265-cohort2-perf6/tools/pegasus/probes/t2187_adaptive_const_probe.py:59) [t2187_adaptive_const_probe.py:3102](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2265-cohort2-perf6/tools/pegasus/probes/t2187_adaptive_const_probe.py:3102) plot 側も A+B+C identity なら performance v3 を要求する。[plot_dynamic_backoff.py:469](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2265-cohort2-perf6/tools/plotting/plot_dynamic_backoff.py:469)

## D. 投入元 tree

投入前に次を満たす。

```bash
SUBMIT_TREE=/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2265-cohort2-perf6/submit-tree

git -C "$SUBMIT_TREE" submodule update --init --checkout external/ccbench
git -C "$SUBMIT_TREE/external/ccbench" rev-parse HEAD
git -C "$SUBMIT_TREE/external/ccbench" status --porcelain --untracked-files=all
git -C "$SUBMIT_TREE" status --porcelain --untracked-files=no
```

期待値:

- superproject HEAD: `8bdf173cc81e5371db7b7bcddb8bdcbb5aeff235`
- `external/ccbench` HEAD: `511c9538e4e8efa54b45cda62e72389ed3b706ec`
- 両 status: 空

`8bdf173cc` の gitlink は上記 full ccbench pin である。`submodule update --init --checkout` は detached superproject の gitlinkへ checkoutするので、この pinになる。driver の固定 pin とも一致する。[t2187_adaptive_const_probe.py:72](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2265-cohort2-perf6/tools/pegasus/probes/t2187_adaptive_const_probe.py:72)

PBS が要求する順序:

1. `PBS_O_WORKDIR` が canonical pathそのものであること。[t2187_adaptive_const_probe.pbs:43](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2265-cohort2-perf6/tools/pegasus/probes/t2187_adaptive_const_probe.pbs:43)
2. HEAD が exact 40 hexであること。[t2187_adaptive_const_probe.pbs:48](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2265-cohort2-perf6/tools/pegasus/probes/t2187_adaptive_const_probe.pbs:48)
3. tracked status が空であること。未追跡 file はこの検査対象外。[t2187_adaptive_const_probe.pbs:53](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2265-cohort2-perf6/tools/pegasus/probes/t2187_adaptive_const_probe.pbs:53)
4. driver と policy が regular fileで、symlinkでないこと。[t2187_adaptive_const_probe.pbs:60](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2265-cohort2-perf6/tools/pegasus/probes/t2187_adaptive_const_probe.pbs:60)
5. driver 起動後、ccbench full HEADを確認し、その後 pinned-cleanを確認する。[t2187_adaptive_const_probe.py:3657](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2265-cohort2-perf6/tools/pegasus/probes/t2187_adaptive_const_probe.py:3657)

失敗順:

- **未初期化:** superproject の tracked status は通り得るが、driver の最初の submodule check `_ccbench_head` で、`rev-parse`不能または得られたHEADの不一致として落ちる。後続 `assert_pinned_clean` には進まない。[t2187_adaptive_const_probe.py:644](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2265-cohort2-perf6/tools/pegasus/probes/t2187_adaptive_const_probe.py:644)
- **pinずれ:** 通常は最初にPBSの superproject tracked-status検査が submodule変更として検出する。そこで見えない設定の場合も、driver の full-pin exact 比較が落とす。[t2187_adaptive_const_probe.py:651](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2265-cohort2-perf6/tools/pegasus/probes/t2187_adaptive_const_probe.py:651)
- **pin一致だが submodule dirty:** PBS status が先に検出し得る。そこで見えなくても、full HEAD検査後の `assert_pinned_clean` が落とす。[t2187_adaptive_const_probe.py:3659](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2265-cohort2-perf6/tools/pegasus/probes/t2187_adaptive_const_probe.py:3659)

launcher は submit tree 外の job dir から起動されても、qsub直前に上記絶対パスへ `cd` する。これにより `PBS_O_WORKDIR` が正しい canonical rootになる。

## E. P1/P2

### P1: 採る

値を1つも見る前に、companion 測定専用の短い新規文書を mainへ commitする。ただし、そのcommitを submit treeへ取り込んではならない。測定用 treeは identity一致のため `8bdf173cc` のまま固定する。登録文書には少なくとも次を凍結する。

- legacy 7腕、3 workload、8 threads、extime 6、7 block
- rep 0..6 の巡回順
- trace-disabled、未認証
- 1本失敗時の n=6 規則
- 診断入力 `985851`
- H1-H7 は extime 3 の凍結判定を置き換えず、extime 6 companion の記述であること
- submit tree `8bdf173cc`、登録文書自身の commit/SHA、およびそのSHAを `submitted-jobs.txt` と insightへ記録すること

登録なしでは、extime 6 の腕・観測長・反復数・順序・欠測規則が outcome-blind に固定されたとは言えない。したがって、新しい図は生成できても、H1-H7 を「事前登録済み extime 6 の確認的判定」「extime 3 判定の再確認」とは主張できず、post hocな companion 記述に限られる。既存登録は extime 3、schema v2を固定している。[dynamic-backoff-preregistration.md:71](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2265-cohort2-perf6/docs/dynamic-backoff-preregistration.md:71) cohort 2文書も trace-disabled performanceを明示的に覆わない。[backoff-counterfactual-cohort2-preregistration.md:366](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2265-cohort2-perf6/docs/backoff-counterfactual-cohort2-preregistration.md:366)

これは実際に今から行う本題の測定条件を登録する文書であり、仮想リスク向けの新gate・一般化・追加台帳ではない。禁止事項には抵触しない。

既存2文書の bytes 制約は次のように分けて理解する。

- `docs/dynamic-backoff-preregistration.md`: **機械的にも変更禁止。** 新performanceの `prereg_sha256` はこのfileをhashする。変更すると既存診断の `cc8975...ee68` と一致せず、plotが拒否する。
- `docs/backoff-counterfactual-cohort2-preregistration.md`: **変更しない結論は正しいが、「prereg_sha256が変わるから」という理由は正確でない。** このfileのSHAは cohort 2 traceの `counterfactual_preregistration` に入る。[t2187_adaptive_const_probe.py:3123](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2265-cohort2-perf6/tools/pegasus/probes/t2187_adaptive_const_probe.py:3123) plot の common identityにはこのfieldがない。ただし同文書自身が発効後の変更を新version/new commitで扱うと定め、既存成果物の意味を束縛しているため、今回もbytes不変とする。[backoff-counterfactual-cohort2-preregistration.md:15](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2265-cohort2-perf6/docs/backoff-counterfactual-cohort2-preregistration.md:15)

### P2: 採る

診断はjob ID昇順先頭の `985851` を固定する。成果物自身も `pbs_jobid=0:985851.nqsv`、`rep_index=0` を持つ。[985851 JSON:21](/work/1/SFC/tanab/izanagi-job-evidence/dynamic-backoff/trace/t2265-cohort2/stage1-rep0-0_985851.nqsv.json:21)

この規則は軌跡、event数、方向的中率、描画結果を見ない outcome-blindな選択である。12本は同時投入され全件完走した集合である。[README.md:96](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2265-cohort2-perf6/output/insights/2026-09-08_t2265-cohort2/README.md:96) 「中央値に近い」「見やすい」などの結果依存選択へ変更しない。

## F. launcher 仕様

段5の author が書く launcher `.sh` は、次の限定仕様とする。

1. 配置と実行

   - repo内に1本だけ作る。禁止された plot/probe/PBS/test は変更しない。
   - 親が launcherをjob dirへ退避してから、そのコピーを実行する。
   - launcherは自身の所在に依存せず、固定 absolute submit treeへ `cd` する。
   - `set -Eeuo pipefail`、`umask 077`。
   - qsub argvは B の7行と byte-equivalentにする。repごとの cell順を配列へ明記し、実行時に算出し直さない。

2. 7本の投入とjob ID

   - rep 0..6を順にqsubする。投入は数秒差の同時投入扱いでよい。
   - qsub stdout全体をjob IDとして取得し、PBSと同じ安全形式 `^([0-9]+:)?[A-Za-z0-9._-]+$` を要求する。[t2187_adaptive_const_probe.pbs:28](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2265-cohort2-perf6/tools/pegasus/probes/t2187_adaptive_const_probe.pbs:28)
   - 成功したqsubごとに直ちに `submitted-jobs.txt` へ追記する。
   - qsub非0、空job ID、形式不正では以後を自動再試行せず停止する。既に記録済みのjob IDは失わない。

3. `submitted-jobs.txt` の形式

   先頭に固定metadata、その後TSV 1行/jobとする。

   ```text
   submit_tree	/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2265-cohort2-perf6/submit-tree
   repo_head	8bdf173cc81e5371db7b7bcddb8bdcbb5aeff235
   companion_prereg_commit	<投入前commit>
   companion_prereg_sha256	<新規登録文書のsha256>
   columns	submitted_utc	rep_index	pbs_jobid	expected_json	qsub_argv
   2026-...Z	0	0:NNNNNN.nqsv	/work/1/SFC/tanab/izanagi-job-evidence/dynamic-backoff/perf/stage1-rep0-0_NNNNNN.nqsv.json	qsub ...
   ```

   `submitted_utc` はUTC ISO 8601、`qsub_argv` は再現可能なshell-quoted逐語。既存登録も投入argvとjob IDをこの台帳へ残すよう定める。[dynamic-backoff-preregistration.md:171](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2265-cohort2-perf6/docs/dynamic-backoff-preregistration.md:171)

4. 完了待ち

   - job名を使わず、台帳のexact job ID 7個を個別に `qstat -f "$jobid"` する。8文字で切れるjob名列は生存判定に一切使わない。
   - `qstat -f` のrcではなく、出力の `job_state` をparseする。
   - `Q/H/W/R/E/S/T/B` は生存中、`F` は終了と扱う。未知・欠落stateは成功と推定せず、監視エラーとして停止する。
   - `F` では `Exit_status` も確認し、0以外なら失敗として記録する。`qstat -f` が終了済みjobへrc=0を返しても、`job_state=F` で正しく終了判定できる。
   - 全jobが `F` になった後、job IDから期待JSON名を組み立て、regular fileの存在を確認する。性能値はこの段階で開かない。
   - poll間隔は30秒程度。親が待つ処理であり、launcher本体へ自動作図は入れない。

5. 途中失敗規則を投入前に固定

   - qsubがjob IDを返して受理された後は、そのrepを自動再投入しない。
   - 7本中6本がcomplete JSONを作れば、その6本だけをplot入力にして n=6で進む。t値は `t(0.975,5)=2.5706`。[dynamic-backoff-preregistration.md:91](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2265-cohort2-perf6/docs/dynamic-backoff-preregistration.md:91)
   - partial journalは図・判定に使わない。[dynamic-backoff-preregistration.md:146](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2265-cohort2-perf6/docs/dynamic-backoff-preregistration.md:146)
   - completeが5本以下ならplot自身の6本要件を満たさないため停止する。[plot_dynamic_backoff.py:1247](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2265-cohort2-perf6/tools/plotting/plot_dynamic_backoff.py:1247)
   - qsub自体がjob IDを返す前に失敗した場合だけ、親が「実際にjobが成立していない」と確認した後、未投入repを再投入してよい。job ID取得後のnode障害、遅さ、測定値、分散を理由とした置換はしない。
   - 複数receiptが偶発的に生じた場合は値を見ず、最初に完走した1件だけを採るという既存規則を維持する。[dynamic-backoff-preregistration.md:154](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2265-cohort2-perf6/docs/dynamic-backoff-preregistration.md:154)

## 総括

実行順は次で固定する。

1. extime 6 companion専用の新規登録文書をmainへcommitする。既存2登録文書は変更しない。
2. submit treeは `8bdf173cc` のまま固定し、ccbenchをgitlink `511c9538...` へ初期化する。
3. author作成のlauncherをjob dirへ退避し、Bの巡回済み7 argvを投入する。
4. exact job IDと `job_state` で待ち、7 completeまたは事前固定規則による6 completeを確定する。
5. login nodeで診断 `985851` と新performance 6または7本をplotへ渡す。
6. 3図のPNG/PDFとprovenanceを生成し、未認証、extime 6 companion、extime 3の凍結判定を置換しない旨をinsightへ記す。

**最重要結論は GO。** legacy 7腕performanceとcohort 2の3-cell診断を混ぜる構造は生成器が受理でき、両cell空間を誤って交差参照する経路はない。ファイル変更、qsub、テスト実測は行っていない。