# 段 6 裁定 2 — [T-2853] (5'') fig1 生成器

入力: 焦点再レビュー 1 巡目 (`codex/s6-focus-1.md`、NO-GO)。対応表: A-M1・A-M3・A-S1・B-S1・P-M1・P-S1〜P-N1 closed、A-M2/B-M1 partial (= F-M1)、B-S2 partial (M6 の node 確定は親の変異 probe の仕事で fix の対象外)。

| ID | 裁定 | 採否 | 理由 |
|---|---|---|---|
| F-M1 (caption の共通条件が read-heavy の値だけ) | real | 採用 (should 相当) | 現データでは 3 campaign とも read 比以外同一 (fix 子の実測) で図の値は変わらない (G05 の must-fix ではない)。ただし caption が「共通条件」と書く主張の根拠が欠けており、数行で閉じる。read 比以外の条件 (threads・records・seconds・clocks_per_us・zipf_skew・rmw・numactl・perf・env_tag・repetitions・ccbench_commit) が 3 campaign で一致しなければ `FigureDataError` とし、caption はその共通値から書く |
| F-S1 (caption 等式が独立検査でない) | real | 採用 | F-M1 の検査を純関数に切り出し、1 campaign の条件 (例: threads) を変えた入力で `FigureDataError` になる test を足す |
| B-S2 partial | — | fix 対象外 | 変異 probe で node を確定する (親) |

変異の追加登録 (fix 前): M14 = 共通条件の一致検査を外す → F-S1 の新 test で kill。
fix の範囲は所有 2 file のまま、上限 450 / 300 行。既存テストの期待値を変えない。
