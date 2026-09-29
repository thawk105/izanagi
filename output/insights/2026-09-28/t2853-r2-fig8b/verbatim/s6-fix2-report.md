[scratch/t2853_r2_fig8b_plot.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2853-r2-plot-fix2/scratch/t2853_r2_fig8b_plot.py) のみ変更しました。`r2-single` と `r2` は、原生成器の直接起動ではなく、実行した Python・wrapper・全引数を生成器の `build_provenance` / `build_provenance_v2` に渡します。実行 cwd が repo root と異なる場合は、その cwd を記録します。測定値の受理条件、レイアウト検査、caption 置換は変更していません。

**実走結果**

| 検証 | 結果 |
| --- | --- |
| R2-a / R2-b の `r2-single` | 両方 rc=0。`validate_external_sources` と `validate_repo_closure` 通過。caption に各 R2 attempt と「原 cohort と合成しない」旨を確認 |
| provenance の `reproduction.command` を変更せず再実行 | 両方 rc=0。再生成前後の `artist_series` が一致。出力 prefix の変更なし |
| `control` | rc=0、`artist_series match` |
| 原 cohort 1 の v1 陽性対照 | rc=0、既存 fig8 provenance の `artist_series` と一致 |
| `r2` の原データ対照 | rc=0。`/tmp` から実行して `reproduction.cwd: /tmp` を確認。記録コマンドの再実行も rc=0、`artist_series` 一致 |
| 負例 2 本 | report dir 欠落は rc=3、異なる SHA の生成器は rc=2。どちらも図を出さずに停止 |

R2-a の provenance に記録されたコマンドは次のとおりです。

```sh
/usr/bin/python3.10 /work/1/SFC/tanab/izanagi/.codex/worktrees/t2853-r2-plot-fix2/scratch/t2853_r2_fig8b_plot.py --generator /work/1/SFC/tanab/izanagi/.codex/worktrees/t2853-r2-plot-fix2/tools/plotting/plot_b10_static_tail_formal.py r2-single --measurement-root /work/1/SFC/tanab/b10-backoff-grid-t2853-r2-20260928 --group b10-backoff-grid-20260927T231112Z-3258589 --report-dir group-report-r2-a --label R2-a --remeasures 1 --completed-jst 2026-09-28 --results-document output/insights/2026-09-28/t2853-r2-fig8b/README.md --out-prefix /work/1/SFC/tanab/izanagi/.codex/worktrees/t2853-r2-plot-fix2/scratch/out/fig8_r2a_b10_static_tail
```

R2-b も同じ呼び出し形式で、`--group b10-backoff-grid-20260927T231120Z-3259762 --report-dir group-report-r2-b --label R2-b --remeasures 2 --out-prefix …/fig8_r2b_b10_static_tail` を記録し、そのまま再実行しました。CLI は `--generator <絶対path>` の後に `control`、`r2`、`r2-single`、`table` を指定する形です。今回の fix では `table` と表の独立手計算は**未実走**です。

最終 SHA-256: `c6aa81179999b7f5f8c89fd3de146b7e5c7dccfddf39106697a41ef940296d27`。`git diff --check` は通過しました。検証で更新された既存出力は開始時の内容へ戻し、最終差分は wrapper 1 file のみです。commit は作成していません。

## 総括

F1 の再生成記録を修正し、R2-a／R2-b と `r2` の記録コマンドが実際に再生成できることを確認しました。