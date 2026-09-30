# 段 6 fix9 裁定 — md_22 [T-2911] (2026-09-30 02:3x JST)

焦点走 6 (11a04fb5c、44 file、36816.nqsv、02:19〜02:23 JST): **1 failed** (他は緑)。
赤: `orchestrator/tests/test_vhash_ro_gc_publish.py::test_record_raw_round_trip_into_plot_and_boundary_table` (386 行)。
`plot.main` → `check_figure_layout` → `ValueError: figure text outside canvas: '$\mathdefault{2\times10^{-2}}$' (32.7, -1436.5, 70.3, 20.1)`。
帰属: 本 wave の作図器 (fix8)。合成 fixture の値域で、対数軸の副目盛りラベル (2×10⁻²) の文字 artist が図の外の座標に置かれ、配置検査が数えた。matplotlib は表示範囲 (view interval) の外の目盛りにも Text を持つが描画しない。親が実データで作図したときは起きていない (job dir `fig/plot3.log` rc=0)。

- **FB-15:** 配置検査が数える文字を「実際に描かれるもの」に限る。具体的には、目盛りラベルは、その目盛りの位置が軸の表示範囲の内側にあるものだけを数える (`axis.get_view_interval()` と tick の `get_loc()` で判定、matplotlib の描画規則と同じ)。はみ出し・重なり・凡例の重なりの検出はそのまま残す (描かれる文字の検査を弱めない)。
- test: (1) 表示範囲の外の副目盛りラベルだけがはみ出す図は通る、(2) 描かれる文字 (タイトル・凡例・表示範囲の内側の目盛りラベル) が図の外に出る図は引き続き拒否される、の 2 つを実体の `check_figure_layout` で固定する。既存の作図 test (合成 fixture と実データ値域) が通ることを確かめる。
- 子は login で実データ (raw/measure1.json・raw/throughput1.json) に対しても作図器を実走し、rc=0 を報告する。
