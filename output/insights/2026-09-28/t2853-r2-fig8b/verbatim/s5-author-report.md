作成した使い捨て wrapper は [scratch/t2853_r2_fig8b_plot.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2853-r2-plot-author/scratch/t2853_r2_fig8b_plot.py) のみです。SHA-256 は `e2ce041abd46794c3f4ffcbd9f9681f9286286a983d1200b878615c502c9bacd`。commit はしていません。生成器の SHA-256 は指定値 `96f8f5de59e43eacedde47f58e8c8269f1162144f919349a4e809b805c6c2810` のままです。

### CLI と実走結果

以下の共通変数を使います。

```bash
S=scratch/t2853_r2_fig8b_plot.py
GEN=/work/1/SFC/tanab/izanagi/.codex/worktrees/t2853-r2-plot-author/tools/plotting/plot_b10_static_tail_formal.py
ROOT=/work/1/SFC/tanab/b10-backoff-grid-t2500-formal
OUT=/work/1/SFC/tanab/izanagi/.codex/worktrees/t2853-r2-plot-author/scratch/out
G1=b10-backoff-grid-20260915T061814Z-545445
G2=b10-backoff-grid-20260919T131526Z-2235286
```

- `control` を実走し、**rc=0、`control: artist_series match`**。図と provenance は [fig8b_control.provenance.json](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2853-r2-plot-author/scratch/out/fig8b_control.provenance.json) と同じ prefix の PNG・PDF に出力しました。

```bash
python3.10 "$S" --generator "$GEN" control \
  --measurement-root "$ROOT" \
  --reference-provenance docs/paper-story/figures/fig8b_b10_static_tail_cohort2.provenance.json \
  --out-prefix "$OUT/fig8b_control"
```

- `r2` に原 2 group を見立てて実走し、**rc=0**。PNG・PDF・[provenance](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2853-r2-plot-author/scratch/out/fig8b_r2.provenance.json) を出力し、`validate_external_sources` と `_validate_repo_closure_v2` はともに通過しました。図中の両見出しと caption は R2-a／R2-b の文言になり、`artist_series` は control と完全一致しました。

```bash
python3.10 "$S" --generator "$GEN" r2 \
  --measurement-root "$ROOT" \
  --group-a "$G1" --report-dir-a group-report-20260915 \
  --group-b "$G2" --report-dir-b group-report-20260919-cohort2 \
  --completed-jst 2026-09-28 \
  --results-document output/insights/2026-09-28/t2853-r2-fig8b/README.md \
  --out-prefix "$OUT/fig8b_r2"
```

- `table` は **rc=0、4 group 受理・拒否 0**。[対照表](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2853-r2-plot-author/scratch/out/fig8b_four_group_table.md) を出力しました。

```bash
python3.10 "$S" --generator "$GEN" table \
  --group "original cohort 1" "$ROOT" group-report-20260915 "$G1" \
  --group "original cohort 2" "$ROOT" group-report-20260919-cohort2 "$G2" \
  --group R2-a "$ROOT" group-report-20260915 "$G1" \
  --group R2-b "$ROOT" group-report-20260919-cohort2 "$G2" \
  --out "$OUT/fig8b_four_group_table.md"
```

負例も実走しました。上記 `r2` コマンドの `--report-dir-a` を `missing-report`、prefix を `fig8b_negative_missing` にした場合は **rc=3** で入力欠落を表示し、図は作りませんでした。上記 `control` の `--generator` に wrapper 自身の絶対 path を渡した場合は SHA 不一致で **rc=2**、図なしでした。

DAT の整数カウンタと throughput から別計算した原 cohort 1・write-heavy の値は、1250 µs の throughput **0.906 ± 0.002 M tps**、abort rate **0.0377 ± 0.0001**、1250→9999 µs の throughput 比 **0.444**。3 値とも表と一致しました。

差し替えたのは `COHORTS[1]`・`COHORTS[2]` の `group_id`、`completed_jst`、`report_dir`、`pinned_sha256`、`results_document`、および `CLAIM_BOUNDARY_V2` です。関数は `_caption_v2` と `make_figure_v2` の**元の戻り値への文言置換**だけを wrapper で包みました。`role` と、verdict・gate・failures・stock pin・SHA・DAT・正しさに関する生成器の検査は変更していません。

## 総括

指定された原データによる陽性対照、R2 見立て描画、4 group 表、2 つの負例は実走済みです。**実際の新規 R2 report を使った描画、表の拒否 group 分岐、描画後の closure 失敗分岐は未実走**です。