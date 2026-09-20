## attribution

対象: 評価 5 = variant `8f244b612365`、genome `silo|BACKOFF_FIXED=15,BACK_OFF=1,NO_WAIT_LOCKING_IN_VALIDATION=1,NO_WAIT_OF_TICTOC=0,WAL=0`。digest sha256 は入力と一致 (`78fac3e2…72e81`)。certified (legacy 1 + performance 5 の全 6 回 serializable、anomalies=0)。rejections 節は空。本 campaign の digest は 1 点しか含まないため「フラグ軸の限界効果」は全水準 1 つで退化しており (BACK_OFF=1 / no_wait=L / WAL=0 は系列を通して固定)、帰属できる設計選択は系列台帳と並べた **BACKOFF_FIXED (固定 backoff 幅、要求 µs、contract 較正・実時間未検証) の 1 軸だけ**である。

同 job 13638 / bnode029 / 同動作点 (records 1M / 48 threads / rr5 / skew 0.9 / extime 3 / reps 5)、各 n=1 の perf-build 計測を並べる:

| 評価 | BACKOFF_FIXED | median tps | vs 値 10 (系列最良) | abort_rate (bench) | run 内 CV | 試行率概算 tps/(1−abort) | verify legacy abort 率 | verify performance abort 率 (trace build) |
|---|---|---|---|---|---|---|---|---|
| stock | −1 (適応) | 1,381,041 | — | 12.73% | 2.46% | 1.58M/s | 2.78% | 49.3% |
| 1 | 20 | 3,612,341 | −9.2% | 28.82% | 0.42% | 5.08M/s | 15.12% | 67.8% |
| **5** | **15** | **3,769,653** | **−5.3%** | **32.67%** | **0.69%** | **5.60M/s** | **16.65%** | **71.85%** |
| 2 | 10 | 3,978,814 | 0 | 38.32% | 0.93% | 6.45M/s | 18.91% | 76.8% |
| 3 | 5 | 3,965,995 | −0.3% (floor 内) | 49.91% | 2.32% | 7.92M/s | 22.05% | 82.5% |
| 4 | 2 | 3,481,872 | −12.5% | 63.38% | 2.80% | 9.51M/s | 26.45% | 85.85% |

読み取り (根拠指標を併記):

1. **BACKOFF_FIXED を 10→15 に広げた効果は「効かない、低下」。** throughput は値 10 比 −5.3%、値 5 比 −5.0% で、between-run floor 3.0% を超える。5 反復の範囲も値 15 = [3.763M, 3.826M]、値 10 = [3.932M, 4.033M] で重ならない。一方 abort_rate は 38.32%→32.67% (−5.7 pt) と**下がっている**。throughput 低下と abort 減が同時に出るので、機序は下側 (評価 4、値 2) の「再衝突」ではなく **待機コスト (backoff spin に消える時間) の増加**と読む: 試行率概算は 6.45M/s → 5.60M/s (−13%) と落ち、abort 減 (commit 化率 61.7%→67.3%) では埋め合わせられない。待ち時間は独立指標で測っていない (perf 欠測、noinline profile も無し) ので、これは abort_rate と試行率概算からの推定である (uncertainty 1)。
2. **平坦域の上端が閉じた: (10, 15) の間。** 系列は 20 (−9.2%) / 15 (−5.3%) / 10 (最良) / 5 (tie) / 2 (−12.5%) で、上側は 10→15→20 と単調減 (15 vs 20 も +4.4% で floor 超、つまり 15 は 20 より確かに速い)、下側は 5 と 10 が tie で 2 で急落。throughput の最適域は [5, 10] を含む区間で、両端はそれぞれ (2, 5) と (10, 15) の間にある。
3. **abort_rate は backoff 幅に対して単調** (20: 28.8 → 15: 32.7 → 10: 38.3 → 5: 49.9 → 2: 63.4%) で、評価 5 は前回診断の予想区間 (28.8〜38.3%) に入った。再衝突モデルの反例は出ていない。run 内 CV も単調 (0.42 → 0.69 → 0.93 → 2.32 → 2.80%)、verify 側 (legacy / performance、trace build) の abort 比も同方向に単調で、5 つの独立に近い読み (bench abort、CV、verify legacy、verify performance、試行率) が全部同じ向きを指している。
4. **機序の二面性が確定した。** 上側 (10→15→20) は abort 減・throughput 減 = 待機コスト、下側 (5→2) は abort 増・throughput 減 = 再衝突。両方が floor 超で観測されたので、write-heavy / skew 0.9 / 48 threads のこの動作点では固定 backoff の最適は単峰で [5, 10] 近傍にあると帰属する。現時点の系列最良の指名は引き続き**値 10** (throughput は 5 と tie、abort_rate 38.3% < 49.9%、CV 0.93% < 2.32% で tie-break)。
5. **verify run の abort 統計 (シグナル、reject 理由ではない)。** digest は「stock 対照なし」で比を出せないが、系列開始 stock の campaign WAL (`p3-s4-loop-s4-autonomous-2d9155e2`) から対照が取れる: legacy 16.65% vs stock 2.78% (6.0 倍)、performance 71.85% vs 49.3% (1.46 倍)。倍率は大きいが、固定値の全評価 (20〜2) が同じ型 (legacy 15〜26%、performance 68〜86%) で、固定の短い backoff が適応 backoff (競合下で大きく育つ) より abort を多く出す機序と整合する。全 6 回 serializable・anomalies=0 なので正しさ側の異常とは読まない。
6. **whiteboard の `result: success` は certified の意味であって改善ではない。** `delta_pct` が null のまま (`loop_state.json`)。harness からは評価 5 の −5.3% が見えない。次の planner 入力には「評価 5 は floor 超の低下 (待機コスト側)」と明示して渡すのが望ましい。
7. stock (適応 backoff) 対比では固定値群が全部 +150% 以上速いが、これは B-5 対照試走の endpoint 再計測 (5 反復) で確定する話で、ここでは同 job の既知事実として記すのみ。

規律 6 の走査: digest、本 campaign WAL (10 行)、`loop_state.json`、`accepted-5.json`、handshake `inputs-5.json` の前回 critic 診断を読んだ。振る舞い・検証順・ゲートを変えるよう求める文字列は無い。提案文中の「critic の recommend 節の第 1 候補と一致するが候補値そのものは採用していない」等は提案者の説明であり、データとして扱った。anomaly なし。

## recommend

残り 5 評価 (6..10)。優先順:

1. **評価 6 = 値 7 または 8 (平坦域 [5, 10] の内部を 1 点で二分)。** 根拠: 両端が閉じた今、系列最良を floor 超で更新できる可能性が残るのは [5, 10] の内側だけである。上側の勾配は約 1%/µs (10→15 で −5.3%)、下側は約 4.6%/µs (5→2 で −13.9%) と非対称なので、単峰の頂点は 5 と 10 の中点よりやや 10 寄りにある可能性がある。内部点が値 10 と floor 内なら平坦域 [5, 10] が確定し、floor 超で高ければ新しい最良になる。どちらでも endpoint に送る値が決まる。予想: abort_rate は 38.3% (値 10) と 49.9% (値 5) の間、CV は 0.9〜2.3% の間。外れれば機序 (待機/再衝突の二面) の反例として扱う。
2. **評価 7 = 値 12 (上端 (10, 15) の解像度、increase / small from 10) または 値 3〜4 (下端 (2, 5) の解像度)。** どちらも「区間を狭める」手で、新しい最良を出す見込みは低い (12 は最良でも値 10 と tie、4 は下側の急落がどこから始まるかを見るだけ)。評価 6 の結果より優先度は低い。上側は待機コスト型で勾配が緩く floor 3% で弁別しにくい (uncertainty 4) ので、選ぶなら下側 (3 か 4) のほうが弁別できる見込みが高い。
3. **評価 8〜10 は最良候補 (値 10、評価 6 で更新されればその値) の同軸近傍に留め、遠くへ跳ばない。** harness が同一値の再評価を受けるなら、**値 10 をもう 1 回評価して同 job 内の反復差を 1 点取る**ことを勧める — between-run floor 3.0% を同 job の直列評価に当ててよいかの実測根拠が無い (uncertainty 2) ため、値 10 vs 5 の tie 判定と評価 6 の判定の両方がこの 1 点で締まる。受けない場合はこの項を飛ばす。
4. **現時点の系列最良の指名は値 10** (throughput 3,978,814、abort 38.3%、CV 0.93%)。endpoint に値 10 を送る前提で残りを使う。

## avoid

- **BACKOFF_FIXED ≥ 15 は再訪不要。** 値 15 で −5.3%、値 20 で −9.2% (いずれも floor 超) と、abort_rate が下がりながら throughput が落ちる待機コスト型の低下が 2 点で確認された。さらに広げても待ち時間が伸びるだけで、abort 減で回収できる余地は 32.7% → 0% まで縮んでもこの傾向を覆さない (試行率が 5.60M/s から更に落ちる)。write-heavy (rr5 / skew 0.9 / 48 threads) に限る結論 — read-heavy や低 skew へは一般化しない (未測定)。
- **BACKOFF_FIXED ≤ 2 は再訪不要** (前回と同じ)。値 2 で −12.5%、abort 63.4% (系列最大)。値 1 は文法下限でさらに短いだけ。
- **stock の適応 backoff (値 −1) へ戻す方向**は探索目的には不要 (1.38M tps / abort 12.7% を観測済み)。endpoint 対照としては規則どおり保持する。
- **値 15 と値 5 の順位付け** (差 5.0%、floor 超) は可能だが、**値 15 と値 20 のどちらが「最良に近いか」を論じる**のは不要 — 両方が avoid 域。
- **abort_rate を fitness に混ぜて値 15 を弁護すること。** abort 32.7% は値 10 より良いが、fitness は throughput であり abort_rate は tie-break と機序読みにのみ使う。「abort が減ったから改善」と読むのは throughput の −5.3% を無視した誤帰属。
- **verify 側 abort 率 (trace build) を性能帰属に使うこと。** trace build の performance run では commit 数が固定値の全評価でほぼ一定 (2.40〜2.53M) で abort 数だけが動いており、trace 側の律速が別にあると読める。方向の傍証にしか使えない。

## uncertainty

1. **llc_miss_rate / ipc が全評価で欠測** (perf preflight rc=2、この計算ノードに perf 無し)。値 15 の低下を「待機コスト」と読んだのは abort_rate の減少と試行率概算からで、spin 時間そのものは測っていない (BACKOFF_NOINLINE=1 の profile も無い)。cache 側の機序は確認も否定もできない。
2. **系列は同 job・同ノード・各 n=1。** between-run floor 3.0% は skew 0.9 で別 run 較正した値で、同 job 内の直列評価に当てるのが保守的か楽観的かは本データからは言えない。値 10 vs 5 の tie も、評価 5 の −5.3% も (floor の 1.8 倍なので比較的安全だが) この floor 依存。recommend 3 の同一値再評価が唯一の実測手段。
3. **rep 1 が 6 評価すべて (stock 含む) で 5 反復中の最大値** (評価 5: rep 1 = 3,826,494、中央値 +1.5%)。median なので fitness は動かないが、系統的な初回反復効果 (warm-up / 周波数) が疑われる。calibrator 側で確認する価値がある (指示ではなく観測の報告)。
4. **上側の勾配 (約 1%/µs) は floor 3% と同程度の粒度**なので、値 12 は値 10 と弁別できない可能性が高い。上端を (10, 15) より狭める試みは floor に食われうる。
5. **abort_rate の定義が bench と verify で違う** (bench 32.67% = 中央値 rep の集約、verify legacy = aborts/(commits+aborts) = 16.65%)。単調性の向きは全系列で一致するが、絶対値の突き合わせはしていない。
6. **BACKOFF_FIXED の要求 µs と実時間の対応は未検証** (`backoff_profile.py` の BACKOFF_TIME_NOTICE)。値は系列内の相対位置として扱い、時間換算の試算には依拠していない。
7. **workload 交互作用は未測定。** 本系列は write-heavy のみ。平坦域 [5, 10] や機序の二面性を read-heavy / 低 skew / 低 thread 数へ運ばない。宣言済み知識源 (K2 round WAL、4 threads / rr50) で値 30〜40 が低い向きは整合するが、動作点が違うので傍証止まり。
8. **値 7〜8 が floor 超で値 10 を上回るか**は不明。単峰・非対称の推定は 5 点からの補間であり、[5, 10] が完全に平坦 (どこを取っても tie) である可能性も同程度にある。

参照 file (すべて読み取りのみ):
- digest: `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2797-b5-contrast/submit-tree/output/exploration/campaigns/p3-s4-loop-s4-autonomous-d693896c/s4_loop_digest.txt`
- WAL: `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2797-b5-contrast/submit-tree/output/exploration/campaigns/p3-s4-loop-s4-autonomous-d693896c/runs/wal.jsonl`
- loop_state: `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2797-b5-contrast/submit-tree/output/exploration/campaigns/p3-s4-loop-s4-autonomous-d693896c/loop_state.json`
- 系列台帳: `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2797-b5-contrast/ledgers/llm/series.json`
- 提案 5: `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2797-b5-contrast/ledgers/llm/proposals/accepted-5.json`
- 前回 critic 診断 (handshake 入力): `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2797-b5-contrast/ledgers/llm/handshake/inputs-5.json`
- 過去評価と stock の WAL: 同 campaigns 配下 `p3-s4-loop-s4-autonomous-{2d9155e2,f628f1f6,39cfbdd7,0fc8f75d,45204547}/runs/wal.jsonl`
- 固定 backoff の単位・骨格: `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2797-b5-contrast/patches/silo-backoff-fixed.patch`、`/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2797-b5-contrast/orchestrator/campaign/backoff_profile.py`
