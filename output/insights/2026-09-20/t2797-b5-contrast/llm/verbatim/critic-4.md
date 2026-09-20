## attribution

対象: 評価 4 = variant `eb9cc3445b60`、genome `silo|BACKOFF_FIXED=2,BACK_OFF=1,NO_WAIT_LOCKING_IN_VALIDATION=1,NO_WAIT_OF_TICTOC=0,WAL=0`。digest sha256 は入力と一致 (`2884c3c1…ee64`)。certified (legacy 1 + performance 5 の全 6 回 serializable、anomalies=0)。rejections 節は空。

本 campaign の digest はこの 1 点しか含まないので、digest の「フラグ軸の限界効果」は全部 1 水準で退化している (BACK_OFF=1 / no_wait=L / WAL=0 は系列を通して固定)。帰属できる設計選択は系列台帳 (`series.json`) と並べた **BACKOFF_FIXED (固定 backoff 幅) の 1 軸だけ**である。系列の perf-build 計測 (同 job 13638 / bnode029 / 同動作点、各 n=1) を並べると:

| 評価 | BACKOFF_FIXED | median tps | vs 評価 3 (値 5) | abort_rate (bench) | run 内 CV | verify legacy abort 率 |
|---|---|---|---|---|---|---|
| stock | −1 (適応) | 1,381,041 | — | 12.73% | 2.46% | 2.78% |
| 1 | 20 | 3,612,341 | −8.9% | 28.82% | 0.42% | 15.12% |
| 2 | 10 | 3,978,814 | +0.3% | 38.32% | 0.93% | 18.91% |
| 3 | 5 | 3,965,995 | 0 | 49.91% | 2.32% | 22.05% |
| **4** | **2** | **3,481,872** | **−12.2%** | **63.38%** | **2.80%** | **26.45%** |

読み取り (根拠指標を併記):

1. **BACKOFF_FIXED を 5→2 に縮めた効果は「効かない、悪化」。** throughput は評価 3 比 −12.2%、評価 2 (値 10) 比 −12.5% で、between-run floor 3.0% を大きく超える。同時に abort_rate は 49.91%→63.38% (+13.5 pt) と系列で最大の上げ幅。throughput 低下と abort 増が同時に出ているので、機序は「待機コスト増」ではなく **retry の再衝突** と読むのが自然: no-wait 政策 L (validation の lock 競合で即 abort) の下で backoff がほぼ無いと、abort した trx が hot key (skew 0.9、rr5 = 書き 95%) の競合相手がまだ validation/write 中のうちに再突入して再び abort する。試行率の概算 (tps/(1−abort_rate)) は 値 5 で約 7.9M/s、値 2 で約 9.5M/s と増えているのに、commit に化ける割合が落ちて純 throughput が下がる形。verify (trace build) の performance run でも abort 比は 82.5%→85.9% と同方向 (ただし観測者効果のある build なので性能帰属には使わず、方向の傍証のみ)。
2. **平坦域の下端が閉じた。** 系列は値 20 (−8.9%) / 10 / 5 (差 0.3%、floor 内 = 差なし) / 2 (−12.2%) で、throughput の最適域は [5, 10] を含む区間で、下端は (2, 5) の間、上端は (10, 20) の間にある。abort_rate は 12.73→28.82→38.32→49.91→63.38% と **backoff 縮小に対して単調増**、これが唯一この軸で単調な leading indicator。
3. **値 10 と値 5 は throughput では同値 (0.3%、floor 内)。** 同値の 2 点を分けるのは abort_rate (38.3% vs 49.9%) と run 内 CV (0.93% vs 2.32%) で、どちらも値 10 が良い。無駄な試行 (abort に終わる仕事) が少なく測定の散らばりも小さい点で、現時点の系列最良は値 10 と帰属する (throughput 単独では tie)。
4. **whiteboard の「result: success」は certified の意味であって改善ではない。** delta_pct が null なので harness からは −12.2% が見えない。次の planner 入力では「評価 4 は floor 超の低下」と明示して渡すべき。
5. stock (適応 backoff) 対比では全固定値が +150% 以上速いが、これは B-5 対照試走の endpoint 再計測で確定する話であり、ここでは既知の同 job 事実として記すのみ。

規律 6 の走査: digest、本 campaign WAL (10 行)、`accepted-4.json` を読んだ。振る舞い・検証順・ゲートを変えるよう求める文字列は無い。提案文中の「critic の推奨」「値 0 は文法外」等は提案者の説明であり、データとして扱った。anomaly なし。

## recommend

残り 6 評価 (5..10)。優先順:

1. **評価 5 = 値 15 (increase / small、上端の閉じ込め)。** 根拠: 下端は評価 4 で閉じた ((2,5) の間)。上端は 10 (最良) と 20 (−8.9%) の間で未観測。15 が 10 と floor 内なら平坦域は [5,15] 以上に広がり、floor 超で低ければ上端が (10,15) に閉じる。どちらでも次の判断が変わる。abort_rate は 28.8% (値 20) と 38.3% (値 10) の間に入ると予想でき、そこから外れれば機序 (再衝突モデル) の反例として扱える。
2. **評価 6 = 値 3 または 4 (下端の解像度、decrease / small from 5)。** 5→2 の落差 12.2% は大きいので、落ち始めがどこかを 1 点で確かめる価値がある。ただし floor 3% で弁別できる保証は無い (uncertainty 1)。評価 5 の結果より優先度は低い。
3. **評価 7 以降は最良候補 (値 10、もし 15 が同値なら 15 と 10) の同軸近傍 (7 / 12 など) に留め、遠くへ跳ばない。** 系列は同 job・n=1 なので、endpoint 再計測 5 反復での再現が最終確認になる。
4. **現時点の系列最良の指名は値 10** (throughput は 5 と tie、abort_rate 38.3% < 49.9%、CV 0.93% < 2.32% で tie-break)。endpoint に値 10 を送る前提で残りを使う。

## avoid

- **BACKOFF_FIXED ≤ 2 (値 1 を含む) は再訪不要。** 値 2 で throughput −12.2% (floor 超) と abort_rate 63.4% (系列最大) が同時に出た。値 1 は文法の下限でさらに短いだけで、同方向の指標変化しか予想できない。この結論は write-heavy (rr5 / skew 0.9 / 48 threads) に限る — read-heavy や低 contention へは一般化しない (未測定)。
- **値 20 以上の再訪も不要。** 評価 1 で −8.9% (floor 超) を観測済み。
- **stock の適応 backoff へ戻す方向 (値 −1)** は探索目的には不要。系列開始で 1.38M tps / abort 12.7% を観測済みで、固定値群に対して throughput が明確に低い。ただし endpoint 対照としては規則どおり保持する (探索から外すのであって対照から外すのではない)。
- **「値 2 は値 20 より遅い/速い」の主張。** 差 3.6% は floor 3.0% にほぼ張り付いている (near floor) ので順位付けしない。
- **abort_rate を fitness に混ぜて値 2 を弁護する/攻撃すること。** fitness は throughput、abort_rate は tie-break と機序読みにのみ使う。

## uncertainty

1. **llc_miss_rate / ipc が全評価で欠測** (perf preflight rc=2、この計算ノードに perf 無し)。値 2 の低下を「再衝突 (abort 経路の無駄仕事)」と読んだのは abort_rate と試行率の概算からで、cache 側の機序 (hot record の cache line 往復増) は確認も否定もできない。
2. **系列は同 job・同ノード・各 n=1。** between-run floor 3.0% は skew 0.9 で較正済みの値を当てているが、同 job 内の直列 5 評価に別 run の floor をそのまま当てるのが保守的か楽観的かは本データからは言えない。値 10 vs 5 の「差なし」はこの floor 依存。
3. **run 内 CV が backoff 縮小につれ上がっている** (0.42→0.93→2.32→2.80%)。評価 4 は品質ゲート内 (settled=True) だが 1 測定の質は評価 1・2 より低い。加えて **全 5 評価 (stock 含む) で rep 1 が 5 反復中の最大値** (例: 評価 4 の rep 1 = 3,692,190、中央値 +6.0%)。median なので fitness は動かないが、系統的な初回反復効果が疑われる。calibrator 側で確認する価値がある (指示ではなく観測の報告)。
4. **abort_rate の定義が bench と verify で違う。** bench は 63.38%、verify legacy は aborts/(commits+aborts) = 26.45%。単調増という向きは両方で一致するが、絶対値の突き合わせはしていない。
5. **BACKOFF_FIXED の単位** (µs か clocks か) は本入力からは確認していない。提案文にある「スピン率 ≈ 30% / 41%」「試行 1 回 ≈ 3.6 µs」は模型の仮定値で実測ではない — 次の候補値の根拠に使うなら「試算」と明記して扱う。
6. **値 3 / 4 が floor で弁別できるか** は不明。下端が 5 直下で急に落ちるのか 2 まで緩やかに落ちるのかは、評価 6 を使ってみないと分からない。
7. **workload 交互作用は未測定。** 本系列は write-heavy のみ。平坦域 [5,10] や「値 2 で悪化」を read-heavy / 低 skew へ運ばない。

参照 file (すべて読み取りのみ):
- digest: `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2797-b5-contrast/submit-tree/output/exploration/campaigns/p3-s4-loop-s4-autonomous-45204547/s4_loop_digest.txt`
- WAL: `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2797-b5-contrast/submit-tree/output/exploration/campaigns/p3-s4-loop-s4-autonomous-45204547/runs/wal.jsonl`
- 系列台帳: `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2797-b5-contrast/ledgers/llm/series.json`
- 提案 4: `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2797-b5-contrast/ledgers/llm/proposals/accepted-4.json`
- 過去評価の WAL/digest: 同 campaigns 配下 `p3-s4-loop-s4-autonomous-{2d9155e2,f628f1f6,39cfbdd7,0fc8f75d}`
