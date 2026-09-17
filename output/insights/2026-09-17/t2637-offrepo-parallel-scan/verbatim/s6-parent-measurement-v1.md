# 親の実測 — 段 5 版 (直下 subdirectory 単位の分割) の tail (2026-09-17)

login node (load average 20〜90、共有)、warm (直前に変更前 tool の全走査あり)、fixture repo
`/work/1/SFC/tanab/t2637-audit-fixture/repo` (到達不能 commit 1 本・候補 4 file)、探索根 `/work/1/SFC/tanab/dev-wave-jobs`
(直下 1,252 entry、tool 計数で約 240k dir / 185 万 file)。

| 走 | tool | workers | 列挙 elapsed | 全体 elapsed | 備考 |
|---|---|---|---|---|---|
| fixture-old-warmup | 変更前 (main abc7085ae) | 1 | 1365.669 s | 1366.379 s | cold 寄り、load 88 |
| fixture-new16-warmup | 段 5 版 | 16 | 1041.759 s | 1043.369 s | warm、load 20〜45 |

段 5 版の heartbeat (15 秒間隔) から読んだ file 数の推移:

| 経過 | files | 速度 |
|---|---|---|
| 0〜60 s | 143k → 1,016k | 約 14,500 file/s (16 worker 全部が動く) |
| 60〜120 s | → 1,323k | 約 5,000 file/s |
| 120 s 以降 | → 1,813k (07:40) | 約 500〜1,000 file/s、**15 分以上** |

tail の間、`/proc/<pid>/task/*/fd` に開いていた探索根配下の directory は
`dev-wave-suite-floor-recheck/measure/run2/before-after-0_898290.nqsv/tmp/pytest-of-tanab/pytest-0/popen-gw40/.../repo/.git/objects/e9`
の型だけで、**1 本の部分木 (pytest の tmp repo が数万個ある深く小さい directory の森) を 1 worker が逐次に walk**していた。
他の 15 worker は task が無く遊んでいた (process 全体の CPU 9%、thread 17 本)。

結論: 直下 subdirectory 単位の分割は部分木の偏りに無力で、利得が最大部分木の逐次時間で頭打ちになる。
並列段の速度 (約 14,500 file/s) は変更前の約 1,350 file/s の 10 倍で、**Python thread の限界ではない**。
対処 = directory 1 個ごとの task を work queue で動的に配る (fix 指示 `s6-fix-prompt.md`)。

段 4 §3 の「prototype 判定 (列挙倍率 < 1.2 なら停止)」への erratum: 判定の目的は「Python thread では
倍率が出ない」ことの検出であり、上の並列段の速度がその前提を反証したため、停止ではなく分割単位の是正
(fix) へ進む。判定の閾値 (≥ 1.2) と D958 の受理条件は v2 の実測にそのまま適用する。
