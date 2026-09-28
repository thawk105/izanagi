[scratch/t2853_r2_fig8b_plot.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2853-r2-plot-fix1/scratch/t2853_r2_fig8b_plot.py) に `r2-single` を追加しました。SHA-256 は `2e1feab709e5c2e746fe8f570377e74154adfd1b2f12b86d1e00a17c80d743b5` です。生成器は変更せず、commit もしていません。

### 使い方

共通して `--generator "$PWD/tools/plotting/plot_b10_static_tail_formal.py"` をサブコマンドの前に指定します。

- `control --measurement-root ROOT --reference-provenance REF --out-prefix ABSOLUTE_FIG8B_PREFIX`
- `r2 --measurement-root ROOT --group-a ID --report-dir-a DIR --group-b ID --report-dir-b DIR --completed-jst DATE --results-document REPO_PATH --out-prefix ABSOLUTE_FIG8B_PREFIX`
- `r2-single --measurement-root ROOT --group ID --report-dir DIR --label R2-a --remeasures 1 --completed-jst DATE --results-document REPO_PATH --out-prefix ABSOLUTE_FIG8_PREFIX`（R2-b は `--label R2-b --remeasures 2`）
- `table --group LABEL ROOT DIR ID` を 4 回指定し、`--out PATH` を指定

### 実走結果

| 実行 | rc | 結果 |
|---|---:|---|
| R2-a `r2-single` | 0 | [出力 provenance](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2853-r2-plot-fix1/scratch/out/fig8_r2a_b10_static_tail.provenance.json)。外部入力・repo closure とも通過 |
| R2-b `r2-single` | 0 | [出力 provenance](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2853-r2-plot-fix1/scratch/out/fig8_r2b_b10_static_tail.provenance.json)。同じく通過 |
| 原 cohort 1 の `r2-single` | 0 | 既存 fig8 provenance と `artist_series` が完全一致 |
| 既存 `control` | 0 | `artist_series match` |
| 既存 `r2` に原データを指定 | 0 | 2 検査通過、`control` と `artist_series` 一致。PDF の両 block 見出しと caption が R2 文言 |
| 既存 `table` | 0 | 4 group 受理、拒否 0 |
| 存在しない report dir／異なる SHA の生成器 | 3／2 | いずれも図を出さず停止 |

R2-a・R2-b の caption はそれぞれ「原 cohort 1／2 の再測定で、原 cohort と分離し合算しない」と明記されています。表の原 cohort 1、write-heavy の 1000・1250・9999 µs について、report JSON の反復値から平均と 95% CI を独立計算し、表示値との一致を確認しました（throughput は順に `0.993 ± 0.002`、`0.906 ± 0.002`、`0.402 ± 0.003` M tps）。

`r2-single` で差し替える生成器の属性は `COHORTS[1]`、`CLAIM_BOUNDARY_V2`、`GROUP_ID`、`REPORT_JSON`、`REPORT_DAT`、`COMPLETE_JSON`、`PINNED_SHA256`、`_caption`、`make_figure` です。入力 SHA は実ファイルから計算して表示します。測定値の受理条件とレイアウト検査は変更していません。

## 総括

指定された実走項目はすべて実施し、通過しました。未実走項目はありません。