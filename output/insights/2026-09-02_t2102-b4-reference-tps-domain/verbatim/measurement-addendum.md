# 段 3 の後に親が取った追加実測 (段 3 の 2 レンズはこれを見ていない)

段 3 の 2 レンズが見た実測は `measurement-1.json` だけである。すなわち repo 内 2 root、
WAL 60 file、`commit.fitness_tps` 852 観測。両レンズはこれを「母集合が違う」「恒真」
「repo 外 root を拾っていない」と批判した。批判を受けて親は次を追加で取った。

## 追加実測 A — key を絞らない上位集合 (`measurement-2.json`)

手順 `measure_all_tps_fields.py`。`output/campaigns/` 配下の全 JSON / JSONL を走査し、
key 名に `tps` または `throughput` を含む**全 field の全数値**を、key を指定せずに拾った。

- 走査 52 file / 候補 56 (残り 4 は JSON でない digest `.txt`)
- key 名 7 種: `tps` 2489 / `median_tps` 506 / `throughput_tps` 505 / `fitness_tps` 465 /
  `session_throughputs` 48 / `throughputs` 20 / `baseline_tps` 1
- 合計 4034 観測 → **非有限十進 0 件**

## 追加実測 B — マシン全域 (`measurement-3.json`)

手順 `measure_reference_tps_domain.py`、走査 root は `/work/1/SFC/tanab` 全体。
sol が「親の 2 root は official external output root を拾わない」と指摘した点への回答であり、
`b10-backoff-grid-runs5/...` などの repo 外 campaign root を含む。

- WAL 5541 file 発見、5537 走査、**読めなかった 4 件は名指しで記録**
  (いずれも `pytest-of-tanab/.../test_v5_truncated_wal_rejects_0`、
  `test_unframed_wal_tail_is_tran0` 等、「切り詰めた WAL を拒否する」ことを試す fixture であり
  campaign 成果物ではない)
- JSON 行 parse 失敗 22 件も件数として記録
- `commit.fitness_tps` 66119 観測 / 相異なり 615 → **非有限十進 0 件**
- `bench.median_tps` 62691 観測 / 相異なり 584 → **非有限十進 0 件**
- `bench.tps[]` 系列 315101 観測 / 相異なり 2841 → **非有限十進 0 件**
- 合計 **443911 観測 → 非有限十進 0 件**

## 追加実測 C — 封印済み B-4 成果物の不在 (マシン全域)

`find /work/1/SFC/tanab -maxdepth 8 -name scheduled-attempt-registry.jsonl -o
-maxdepth 8 -name analysis-manifest.json` → **0 件**。
repo 内 `output/` で `reference_tps` を含む file は 29 件で全部 `output/insights/` 配下の
設計文書・変異仕様・裁定逐語 (完全走査)。封印済み registry も manifest も、
このマシンのどこにも存在しない。

## 追加実測 D — exact 比の材料の不在 (恒真性批判への回答)

sol は「上流の exact `1/3` が `0.3333333333333333` へ丸められていても『有限』と報告する」
= 十進 token 判定は恒真だと指摘した。この筋が成立するには、丸める前の exact 比が
どこかに存在するか、材料から再構成できる必要がある。

`benchparse.py:53-63` の高精度版は `commit_counts_ / actual_extime` である。
この 2 つを campaign 成果物の全域で探した。

- `grep -rl "actual_extime" /work/1/SFC/tanab/izanagi/output/campaigns/` → **0 件** (rc=1)
- `grep -rl "commit_counts_" /work/1/SFC/tanab/izanagi/output/campaigns/` → **0 件** (rc=1)

`pipeline.py:331` は `commit_counts_` を witness counter として stdout から読むが、
WAL へは載せない。WAL の commit payload は `fitness_tps` / `cv` / `high_variance` /
`unstable` の 4 key だけである。

したがって「丸める前の exact 値」は記録に存在せず、遡って再構成することもできない。
`commits / extime` を exact 比として読む解釈は、材料が無いため
**現在の記録からは実行不能**である。

## 親が段 4 で採ろうとしている読み

1. `reference_tps` が指す量 (certified snapshot の session-level throughput) の
   production 値域は測り終えた。443911 観測、非有限十進 0 件。
2. 同じ量を exact 比として読む解釈は材料が無く再構成不能 (追加実測 D)。
3. caller が任意の有理数を渡せることは、issuer 自身が「caller schedule は外部の
   authoritative population に束縛されない」と明記する以上、
   「正当な upstream 出力」ではない (この点は sol も refuted 側で同意している)。
4. よって D1344 の (a) — registry の受理値域を狭める — を採る。
5. ただし D1344 の文面が言う「予定されている scheduled input の列挙」は空集合であり、
   親はその空集合を 0 件の根拠にしていない。空集合の理由は、registry の上流を束縛する
   producer が存在しないこと (D1345 / T-2103、および T-2050 / T-2051 の領域) である。
