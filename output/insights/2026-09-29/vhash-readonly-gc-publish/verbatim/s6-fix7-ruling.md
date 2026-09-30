# 段 6 fix7 裁定 — md_22 [T-2911] (2026-09-30 02:0x JST)

本計測の raw がそろった: 診断 `raw/measure1.json` (5c781ae7c、36634.nqsv、bnode005、144 走) と throughput `raw/throughput1.json` (5c781ae7c、36637.nqsv、bnode031、144 走)。
作図器 (981f2f63d 時点、`tools/plotting/plot_vhash_ro_gc_publish.py --measure raw/measure1.json --throughput raw/throughput1.json --out-prefix <dir>/ro_gc_publish`) は `check_figure_layout` の `ValueError: figure text outside canvas` で停止し、図を出さなかった (log は job dir の `fig/plot.log`)。帰属: 本 wave の作図器。fixture では出なかった値域 (実データ) で配置が崩れる。

実データの値域 (親の集計、条件内 6 反復):
- 公開回数 (3 s): 長い ro (wait10msR) の 6 条件で stock 0 (36/36 走)、variant 289〜299。長い ro なしで S95 stock 4,978・variant 139,567、T95 7,314・145,150、S0/T0 は両 arm 約 15,000〜26,000。
- 境界年齢の平均: stock は公開 0 回の条件で未定義。variant の wait10msR は 12.5〜14.3 ms、長い ro なしは 32〜366 µs。
- throughput の比 (variant/stock、対ごと): 0.985〜1.073 (長い ro なし) と 1.56〜16.83 (長い ro)。

- **FB-13:** 図を描き直す。(1) 図 1 は条件ごとに stock と variant の**絶対値**を並べる 2 panel (公開回数/s、境界年齢の平均 µs)、どちらも対数軸。stock が公開 0 回の条件は、値を補わず「公開 0 回」と分かる印 (x 軸付近の記号と凡例) で示す。反復点と平均を描く。(2) 図 2 は throughput の比 (variant/stock) を対数軸で、1 の線を引く。(3) 配置検査 (`check_figure_layout`) は残し、実データで通る配置にする (検査を緩めない)。(4) (b) の数表 (variant の wait10msR − none の境界年齢差、ro 保持者割合、stock 公開 0 回) の出力は残す。`tools/plotting/FIGURE_CONVENTIONS.md` に従う。
- 子は login で作図器を実データに対して実走し (出力は /tmp)、rc=0 と出力 file の一覧・所要を報告する。fixture test は実データの値域を含む形に直す。
- 既存テストの期待値は変えない (本 wave の作図 test は裁定どおり直してよい)。
