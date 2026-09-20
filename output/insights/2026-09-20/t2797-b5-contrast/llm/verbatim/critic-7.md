## 前提 (読んだ材料)

- digest: `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2797-b5-contrast/submit-tree/output/exploration/campaigns/p3-s4-loop-s4-autonomous-680cb8f9/s4_loop_digest.txt` (sha256 一致 `378b22d7…feac2`)
- 本評価 WAL: 同 dir `runs/wal.jsonl` (10 行: build 2・verify 6・bench 1・commit 1、genome `silo|BACKOFF_FIXED=4,BACK_OFF=1,NO_WAIT_LOCKING_IN_VALIDATION=1,NO_WAIT_OF_TICTOC=0,WAL=0`)
- 系列台帳: `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2797-b5-contrast/ledgers/llm/series.json` + 系列開始 stock (campaign 2d9155e2) と評価 1〜6 の各 campaign WAL
- 提案: `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2797-b5-contrast/ledgers/llm/proposals/accepted-7.json`
- 編集面の骨格: `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2797-b5-contrast/patches/silo-backoff-fixed.patch` (BACKOFF_FIXED の単位は µs、-1 = stock 適応)

系列を BACKOFF_FIXED (µs) の順に並べ直した表 (perf build の median / 中央値 rep の abort_rate / run 内 CV / trace build 5 走の abort 率):

| 評価 | µs | median tps | abort_rate | CV | trace abort (perf 動作点) | 対 8 µs (系列最良) |
|---|---|---|---|---|---|---|
| stock | 適応 (-1) | 1,381,041 | 12.7% | 2.46% | 49.3% | −65.6% |
| 4 | 2 | 3,481,872 | 63.4% | 2.80% | 85.9% | −13.2% |
| **7 (本評価)** | **4** | **3,882,770** | **53.6%** | **2.83%** | **83.3%** | **−3.24%** |
| 3 | 5 | 3,965,995 | 49.9% | 2.32% | 82.5% | −1.2% |
| 6 | 8 | 4,012,680 | 42.0% | 0.97% | 78.9% | 0 |
| 2 | 10 | 3,978,814 | 38.3% | 0.93% | 76.8% | −0.8% |
| 5 | 15 | 3,769,653 | 32.7% | 0.69% | 71.9% | −6.1% |
| 1 | 20 | 3,612,341 | 28.8% | 0.42% | 67.8% | −10.0% |

## attribution

- **変えた設計選択は 1 軸だけ (固定 backoff の量、BACKOFF_FIXED µs)。** BACK_OFF=1 / no-wait L / WAL=0 は系列全体で固定なので、digest の「フラグ軸の限界効果」節は各軸 1 水準の退化表で、これらへの帰属は不能 (BACK_OFF=1 の効果を読まない)。
- **本評価 (4 µs) は 5 µs と tie、8 µs (系列最良) とは floor 上で弁別不能。** 対 5 µs −2.1%、対 8 µs −3.24% (between-run floor 3.0%)。rep 1 が系統的に最大 (下記 uncertainty 3) なので rep 2〜5 の median で見ても対 5 µs −2.4% で、判定は変わらない。「4 µs は遅い」ではなく「平坦域 [5,10] の下端に接する」。
- **abort_rate は単調に上がり、提案時の予測 (52〜56%) の内側 (53.6%) に入った。** 2→4→5→8→10→15→20 µs で 63.4→53.6→49.9→42.0→38.3→32.7→28.8%。trace build の abort 率 (85.9→83.3→82.5→78.9→…→67.8%) と legacy verify (26.5→22.6→22.1→19.8→…→15.1%) も同じ向きの単調列で、本評価は列の上に乗っている。**abort 増 = 短い backoff で hot key に即座に再衝突する機序** (candidate の再衝突モデル) を支持する観測で、証明ではない。
- **throughput は abort_rate に対して非線形に落ちる。** 8→4 µs で abort +11.6 pt に対し throughput −3.2% (floor 上)、4→2 µs で abort +9.8 pt に対し throughput −10.3% (floor を大きく超える)。abort が 55% 前後を超えると捨てる仕事が実効仕事を上回り、崖になる。崖の位置は **2 と 4 µs の間** と絞れた (評価 7 の主目的が達成)。
- **stock 適応 backoff は「待ち過ぎ」で負けている。** abort_rate は 12.7% と系列で最小なのに throughput は 1.38M で平坦域の 1/2.9。abort が少ないのに遅い = 待ち時間 (idle) に throughput を落としている機序 (待ち時間は独立指標が無く throughput の低下でしか見えない)。llc/ipc 欠測のため cache 機序は除外できないが、abort と throughput の向きが逆なのは待機コスト説と整合。
- **verify run の abort 統計 (digest の legacy 22.63%) は、digest が stock 対照なしとしたが、系列開始 stock の campaign WAL から対照が引ける:** legacy 2.78% (8.1 倍)、perf 動作点 trace 49.3% (1.69 倍)。倍率は大きいが系列の単調列に乗っており、本評価固有の異常ではない。trace build は perf build より abort 率が一律高い (計器の overhead で critical section が伸びる) ので、比較には比だけ使う。

## recommend

残り 3 評価 (8〜10) と endpoint 指名に向けて、leading indicator で裏付く順:

1. **endpoint 指名は 8 µs のまま維持する。** 根拠: 平坦域 [5,10] の中央で、下側は評価 7 で「4 は tie、2 は崖」と実測済み (下側マージン ≥ 3 µs)。abort_rate 42% は平坦域の中で最も低く (5 µs の 49.9%、4 µs の 53.6% より)、崖の機序 (abort > 55%) から最も遠い。CV も 0.97% と平坦域の中で安定側。
2. **評価 8 = 12 µs (平坦域の上端の解像)。** 上側は 10 µs (対 8 −0.8%、tie) と 15 µs (−6.1%、floor 超) の間が未解像で、下側 (4〜5 µs で解像済み) より情報が残っている。12 µs が tie なら平坦域は [4,12] と両側が対称に言え、落ちれば上端が 10〜12 と確定する。abort_rate の予測 (単調列の内挿): 35〜38%。
3. **評価 9 = 8 µs の再評価 (harness が同一 genome の再投入を受ける場合)。** between-run floor 3.0% は別 run 間で較正した値で、同 job 直列・各 n=1 の本系列に当てる実測根拠が無い (提案文の uncertainty 2 と同じ)。系列最良の再測定 1 点があれば、4 vs 8 の −3.24% が「差」か「同 job 反復差」かを系列内で言える。受けない場合は評価 9 も 10 も内挿 (6 or 7 µs) に回すが、tie の再確認にしかならず新最良は期待しない。
4. **評価 10 = 評価 8 の結果で分岐。** 12 µs が tie なら 6 µs (平坦域内の最良探し、期待は tie)、落ちたなら 11 µs は取らず 8 の再評価または 7 µs。いずれも「新最良」より「指名の頑健化」目的。

## avoid

- **≤ 3 µs:** 2 µs で −13.2% (abort 63.4%)、4 µs で既に abort 53.6% と崖の直上。3 µs を取っても崖の位置の解像 (2〜4 の間) が 1 µs 縮まるだけで、指名は変わらない。
- **≥ 15 µs:** 15 で −6.1%、20 で −10.0%。abort_rate は下がる (32.7%、28.8%) のに throughput が落ちる = 待機コスト側の損失で、この動作点では再訪不要。
- **stock 適応 (-1) の再測定:** 平坦域の 1/2.9、abort 12.7% と throughput の向きが逆で機序も明確。endpoint 対照としては harness が別途持つ。
- **同じ動作点での「平坦域の内側補間だけ」に残り予算を使い切ること:** 5・8・10 は floor 内で並んでおり、6・7・9 µs は n=1 では弁別できない。
- 以上はすべて write-heavy / skew 0.9 / 48 threads の 1 動作点に限る。read-heavy・balanced には一般化しない (K2 旧配線 rr50 / 4 threads では最適が 30〜40 µs で、平坦域の位置が動作点で 1 桁動く)。

## uncertainty

1. **llc_miss_rate / ipc が全評価で欠測** (bnode029 に perf 無し、preflight rc=2)。機序の推定は abort_rate と throughput の 2 指標だけで、「再衝突で捨てる仕事」と「cache / IPC の変化」を分離できない。stock の「待ち過ぎ」説も同様に候補仮説。
2. **各値 n=1・同 job 直列。** between-run floor 3.0% の適用根拠が無く、4 vs 8 の −3.24% は floor に接している。「差なし」とも「遅い」とも断定せず「弁別不能」と読む。
3. **rep 1 が 8 評価すべて (stock 含む) で 5 反復中の最大値。** median には効かないが CV を押し上げる (本評価 2.83% は系列最高)。endpoint 再計測にも同じ効果が乗るので、calibrator 側の確認事項として報告する (観測であって指示ではない)。本評価は quality=normal / settled=True と親が開示しているので、harness の品質閾値は critic.md の within-run 2.28% とは別物と理解した。
4. **digest の verify 統計は本 campaign 1 点のみで対照を持たない。** 対照は系列開始 stock の WAL から critic が補った。trace build の abort 率 (83%) は perf build (54%) より一律高く、絶対値は使わない。
5. **digest の限界効果節は退化 (1 水準)。** BACK_OFF / no-wait / WAL の交互作用は本系列では測っていない。
6. **規律 6 の走査:** digest・本評価 WAL の payload・series.json の note (すべて空文字)・proposal 本文を読んだ範囲で、ゲートや検証順序を上書きする指示めいた文字列は無かった。proposal に前回 critic の recommend への言及があるが、これは通常の loop 入力であり anomaly ではない。

(書き込みは行っていない。読み取りは jq / cat / sed -n / find / grep と、output/ 配下でない series.json への python3 読み取りのみ。)
