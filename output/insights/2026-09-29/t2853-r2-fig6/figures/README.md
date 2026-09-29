# figures/ — R2 fig6 (attempt `t2853r2-20260929a`) の図と対照表

- `fig6_r2_a2_certification.png` / `.provenance.json` — R2 attempt を原 fig6 と同じ生成器 `tools/plotting/plot_a2_certification.py` (sha256 `aac63659…8448`、bytes 不変) で描いた図。
  原 fig6 (`docs/paper-story/figures/fig6_a2_certification_observed_positive.*`) の置き換えではなく、原 attempt と合成しない別 attempt の記録である (insight §0)。
- `fig6_comparison_table.md` — 原 attempt `t2364-20260907b` と R2 を、同じ生成器の `load_measurements` で別々に読んで並べた表。

## caption を読むときの注意

caption は生成器が記録から組んだ既定文のままである。attempt ID・request・host・時刻・効果・pin は R2 の値だが、末尾の
「The older series is not a comparator, and the cause of the sign difference has not been identified.」は、原 fig6 で旧 attempt (fig5、内蔵 adaptive backoff の on/off を測った別条件) との関係を述べる生成器の定型文である。
**R2 と原 attempt の効果はどちらも正で、両者の間に符号差は無い。** この文を R2 と原 attempt の関係として読まない。

## 再生成の手順

provenance の `reproduction` は生成器を直接起動する argv を記録するが、R2 の certification は生成器の repo 内 pin 表に無いので、そのままでは入力 hash 検査で止まる (値は変わらない)。
再生成は、入力 file の sha256 を実行時に計算して生成器の既存の差し替え口 `expected_hashes` に渡す repo 外の wrapper で行う。repo root (生成器の sha256 が上と同じ checkout) で:

```
A=/work/1/SFC/tanab/izanagi-repro-archive/t2853-r2-fig6-20260929
R=$A/collect-root/output/insights/2026-09-07_t2364-paper-story-a2-certification
M=/work/1/SFC/tanab/izanagi-measurements/dev-wave-paper-story-a2-cert-20260824
OUT=$(mktemp -d)
python3.10 $A/tools/t2853_r2_fig6_plot.py --generator $PWD/tools/plotting/plot_a2_certification.py \
  --expected-generator-sha256 aac636595ec0b211133edcc18bc1f72f984e346f58e7146da444396ea8d86448 \
  draw --measurement-root $M/t2853r2-20260929a --certification $R/certification.json \
  --raw-manifest $R/raw-manifest.json --out-prefix "$OUT/fig6_r2_a2_certification"
```

`$R` の dir 名は policy の tracked destination の写しで、中身は R2 attempt である (原 attempt の dir ではない)。対照表の argv は `$A/README.md`。
wrapper の sha256 は `e3367d042f5d688935cd2b431d9787d7aff893dcc70660371dda4afdfe4783c6`。
