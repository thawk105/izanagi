使い捨て wrapper を [scratch/t2853_r2_fig6_plot.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2853-r2-fig6-author/scratch/t2853_r2_fig6_plot.py) に作成しました。sha256 は `e3367d042f5d688935cd2b431d9787d7aff893dcc70660371dda4afdfe4783c6` です。生成器は変更しておらず、sha256 は `aac636595ec0b211133edcc18bc1f72f984e346f58e7146da444396ea8d86448` です。ハッシュの記録は各成功出力の `.wrapper.json` に置きました。

以下は実走コマンドです。変数は表示を短くするための絶対 path の表記です。`--r2-*` には、結果がまだ無い R2 の代わりに原 attempt を渡しています。

```bash
W=/work/1/SFC/tanab/izanagi/.codex/worktrees/t2853-r2-fig6-author
M=/work/1/SFC/tanab/izanagi-measurements/dev-wave-paper-story-a2-cert-20260824/t2364-20260907b
C=$W/output/insights/2026-09-07_t2364-paper-story-a2-certification/certification.json
R=$W/output/insights/2026-09-07_t2364-paper-story-a2-certification/raw-manifest.json
P=$W/docs/paper-story/figures/fig6_a2_certification_observed_positive.provenance.json
G=$W/tools/plotting/plot_a2_certification.py
O=$W/scratch/out
B="python3.10 $W/scratch/t2853_r2_fig6_plot.py --generator $G"

$B control --measurement-root "$M" --certification "$C" --raw-manifest "$R" --out-prefix "$O/fig6_control_artist" --existing-provenance "$P"  # rc=0
$B draw --measurement-root "$M" --certification "$C" --raw-manifest "$R" --out-prefix "$O/fig6_control_draw"  # rc=0
$B table --original-measurement-root "$M" --original-certification "$C" --original-raw-manifest "$R" --r2-measurement-root "$M" --r2-certification "$C" --r2-raw-manifest "$R" --out "$O/fig6_comparison.md"  # rc=0

$B draw --measurement-root "$O/missing-root" --certification "$C" --raw-manifest "$R" --out-prefix "$O/fig6_missing_root"  # rc=2
python3.10 "$W/scratch/t2853_r2_fig6_plot.py" --generator "$G" --expected-generator-sha256 0000000000000000000000000000000000000000000000000000000000000000 draw --measurement-root "$M" --certification "$C" --raw-manifest "$R" --out-prefix "$O/fig6_wrong_generator"  # rc=2
$B draw --measurement-root "$M" --certification "$W/scratch/tmp/certification-one-byte.json" --raw-manifest "$R" --out-prefix "$O/fig6_mutated_cert"  # rc=2
```

`control` は `control: artist_series match` を出しました。`draw` は [PNG](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2853-r2-fig6-author/scratch/out/fig6_control_draw.png)、[PDF](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2853-r2-fig6-author/scratch/out/fig6_control_draw.pdf)、provenance を生成し、外部入力と repo の両 closure 検証が通りました。[対照表](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2853-r2-fig6-author/scratch/out/fig6_comparison.md) は両列とも受理され、NFC も確認済みです。

負例 4(c) では、certification の attempt ID の `b` を `c` にした **1 byte 差**の copy を使いました。wrapper がその copy の sha256 を実行時計算したため、生成器の hash 照合より先には止まらず、生成器の embedded policy 検査で `fetchcontent_path_argument_prefixes` 欠落として拒否されました。3つの負例はいずれも図を出していません。

**未実走:** R2 実データでの `draw` と `table`。所有外 caller・共有 fixture・consumer test への波及はありません。`git status --porcelain --untracked-files=no` は空で、tracked file は変更していません。

## 総括

wrapper の陽性対照、描画、対照表、指定の負例を実走しました。R2 実データが到着すれば、同じ wrapper にその入力を渡せます。