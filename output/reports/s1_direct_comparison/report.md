# S-1 直接比較 report

本設計は独立な検証相を持たない。ブロック化した単一登録追試 + gate 連言であり、旧記述の「スクリーニング → 検証相」はこの gate 連言として読み替える。

Holm 族 4 全体の裁定は行わない。α=0.0125 との比較は参考表示であり、族全体の裁定は人間または将来の consumer が行う。

## Hard gates

| gate | scope | status | reasons |
|---|---|---|---|
| freeze | all | pass |  |
| schedule | develop | pass |  |
| schedule | floor | pass |  |
| schedule | block1 | pass |  |
| schedule | block2 | pass |  |
| certified | samples | pass |  |
| sample counts | cells | pass |  |
| budget | incomplete comparisons | pass |  |

## Comparisons

| comparison | family | 判定 | relative median diff | floor_cmp | p_perm | p* | reasons |
|---|---|---|---:|---:|---:|---:|---|
| S-1a:balanced:p2_2_flag_opt | S-1a | 不成立 | -0.373765 | 0.03 | 1 | 1 |  |
| S-1a:balanced:backoff_fixed_best | S-1a | 不成立 | -0.446037 | 0.03 | 1 | 1 |  |
| S-1a:balanced:sort_best | S-1a | 成立 | 0.835081 | 0.03 | 0.000204082 | 0.000204082 |  |
| S-1a:write-heavy:p2_2_flag_opt | S-1a | 不成立 | -0.0934485 | 0.03 | 1 | 1 |  |
| S-1a:write-heavy:backoff_fixed_best | S-1a | 不成立 | -0.359897 | 0.03 | 1 | 1 |  |
| S-1a:write-heavy:sort_best | S-1a | 成立 | 0.555031 | 0.03 | 0.000204082 | 0.000204082 |  |
| S-1a:read-heavy:p2_2_flag_opt | S-1a | 不成立 | -0.551167 | 0.03 | 1 | 1 |  |
| S-1a:read-heavy:backoff_fixed_best | S-1a | 不成立 | -0.518903 | 0.03 | 1 | 1 |  |
| S-1a:read-heavy:sort_best | S-1a | 成立 | 0.984334 | 0.03 | 0.000204082 | 0.000204082 |  |
| S-1b:balanced:gate_on_vs_gate_off | S-1b | 成立 | 0.874244 | 0.03 | 0.000204082 | 0.000204082 |  |
| S-1b:write-heavy:gate_on_vs_gate_off | S-1b | 成立 | 0.60638 | 0.03 | 0.000204082 | 0.000204082 |  |
| S-1b:read-heavy:gate_on_vs_gate_off | S-1b | 成立 | 0.999298 | 0.03 | 0.000204082 | 0.000204082 |  |

## Families (Holm 族全体の裁定前の参考値)

| family | 三値判定 | family p | α=0.0125 以下 |
|---|---|---:|---|
| s1a | 不成立 | 1 | False |
| s1b | 成立 | 0.000204082 | True |

## 開示

- unstable 標本は除外せず、比較行の `unstable_counts` に全数を保持した。
- retry は比較行の `retry_events` に一覧を保持した。
- block1 と block2 のセル別中央値差は比較行の `block_effects` に保持した。
- 効果量 (中央値差、確率優越 A、両セル CV) は JSON の `effect_sizes` に保持した。
- 時間台帳: spent=22943.7s / total=43200s、retry=120.65s。

generated_at_head: `24202e270782a58343ef016592c1a4ae767ee0ce`
