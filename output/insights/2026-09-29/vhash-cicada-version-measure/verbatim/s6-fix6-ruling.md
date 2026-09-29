# 段 6 fix 6 (作図) の裁定 (2026-09-29 07:3x JST)

入力: 予備走 measure0 (33967.nqsv、@bf7e134ea = fix5 前の patch、A-none・A-wait1ms × gc 3 値 × 3 反復、raw /work/1/SFC/tanab/tmp/vhash-cicada-version-measure-2026-09-29/raw/measure-j0.json、13.5 MB) を現行の作図 script に通した出力 /work/1/SFC/tanab/tmp/vhash-cicada-version-measure-2026-09-29/fig-prelim/ (PNG 3 枚と provenance)。**予備走の値は結果に使わない。作図の欠点の洗い出しにだけ使う。** 所有は tools/plotting/plot_vhash_cicada_vlife.py だけ (fix5 と素集合)。

| # | 観察 | fix |
|---|---|---|
| P1 | 入力が raw 1 file 限定。本計測は 4 job (各 6 条件) の raw に分かれる | 複数の raw file を受け取り、条件 ID の重複・`ccbench_commit`/`patch_sha256`/`records` の不一致を拒否して併合する。provenance に全入力の sha256 |
| P2 | 図 1: 縦軸線形でほぼ全部が bucket 0 に集中し差が見えない。横軸が bucket 番号 | 縦軸を割合の対数 (0 を扱える形、例: symlog か 1−CDF の対数) にし、横軸 tick を bucket の上界 (0..8, 16, 32, …, 2048, >2048) で表記。凡例を整理 (条件が多いので workload × 長い tx 型でパネルを分けるか、gc_inter_us を色・長い tx 型を線種にする) |
| P3 | 図 2: update tx の深い read の割合は約 1e-5 と小さく、候補率は分母が小さいと CI が暴れる。read-only の深い read (固定 snapshot、forwarding の対象外) が図に無いが、予備走では gc_inter_us=100000 で read-only read の約半数が位置 1 以上 | 図 2 を 3 パネルにする: (a) update tx の read で位置 ≥ K の割合 (対数軸)、(b) read-only の read で位置 ≥ K の割合 (対数軸、「forwarding 対象外」と注記)、(c) 観測時点の楽観的 forwarding 候補率 (update tx の深い read が分母)。(c) は各点に分母 (深い read の総数) を注記し、分母が小さい点 (例: < 30) は白抜き等で区別する |
| P4 | 図 3: 凡例の色と系列が対応していない。分位点 (p50/p90) に t 分布 CI を付け、負の値へ振れて対数軸が崩れる | 系列の色 = 長い tx 型、線種 = p50 実線 / p90 破線、に統一。分位点には t 分布 CI を付けず、反復の min–max を範囲で描く (FIGURE_CONVENTIONS §2 は平均系の値に CI、分位点は範囲、と caption に明記)。回収時年齢は生成基準と上書き基準を別パネル。論理生存版数は平均 ± t CI のままでよい |
| P5 | 全図 | caption / 注記に「計器入り build の値。throughput は性能値ではない」「timestamp 空間 (clock boost を含む)」「位置の起点 (read = latest、validation = 走査開始点)」を入れる |

test: 自走 `--selftest` を、複数 file 併合 (正常と拒否 2 例)、分母注記、分位点の範囲描画 (負値にならない) を含む fixture で走らせる。
