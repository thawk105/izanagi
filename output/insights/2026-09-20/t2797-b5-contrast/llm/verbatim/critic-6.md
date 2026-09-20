## attribution

対象: 評価 6 = variant `12ca3166fbc6`、genome `silo|BACKOFF_FIXED=8,BACK_OFF=1,NO_WAIT_LOCKING_IN_VALIDATION=1,NO_WAIT_OF_TICTOC=0,WAL=0`。digest sha256 は入力と一致 (`e1fde932…c92e`)。certified (legacy 1 + performance 5 の 6 回すべて serializable、anomalies=0、proof_surfaces は系列全評価と同じ X/P present・I absent)。rejections 節は空。本 campaign の digest は 1 点しか含まず「フラグ軸の限界効果」は全水準 1 つで退化している (BACK_OFF=1 / no_wait=L / WAL=0 は系列を通して固定)。帰属できる設計選択は系列台帳と並べた **BACKOFF_FIXED (固定 backoff 幅) の 1 軸だけ**である。

同 job 13638 / bnode029 / 同動作点 (1M records / 48 threads / rr5 / skew 0.9 / extime 3 / reps 5)、各 n=1 の perf-build 計測を BACKOFF_FIXED 順に並べる:

| 評価 | BACKOFF_FIXED | median tps | vs 値 10 | 5 反復の範囲 | abort_rate (bench) | run 内 CV | 試行率概算 tps/(1−abort) | verify legacy abort | verify performance abort (trace build) |
|---|---|---|---|---|---|---|---|---|---|
| stock | −1 (適応) | 1,381,041 | −65.3% | 1.341–1.422M | 12.73% | 2.46% | 1.58M/s | 2.8% | 49.3% |
| 1 | 20 | 3,612,341 | −9.2% | 3.607–3.643M | 28.82% | 0.42% | 5.08M/s | 15.1% | 67.8% |
| 5 | 15 | 3,769,653 | −5.3% | 3.763–3.826M | 32.67% | 0.69% | 5.60M/s | 16.6% | 71.8% |
| 2 | 10 | 3,978,814 | 0 | 3.932–4.033M | 38.32% | 0.93% | 6.45M/s | 18.9% | 76.8% |
| **6** | **8** | **4,012,680** | **+0.85% (floor 内)** | **3.970–4.073M** | **41.95%** | **0.97%** | **6.91M/s** | **19.7%** | **78.8%** |
| 3 | 5 | 3,965,995 | −0.3% (floor 内) | 3.908–4.152M | 49.91% | 2.32% | 7.92M/s | 22.1% | 82.5% |
| 4 | 2 | 3,481,872 | −12.5% | 3.445–3.692M | 63.38% | 2.80% | 9.51M/s | 26.4% | 85.8% |

読み取り (根拠指標を併記):

1. **値 8 は値 10・値 5 と「差なし」(平坦域内)。** throughput は値 10 比 +0.85%、値 5 比 +1.18% で、いずれも between-run floor 3.0% の内側。5 反復の範囲も 3 点で重なる (8: 3.970–4.073M、10: 3.932–4.033M、5: 3.908–4.152M)。数値上の系列最大は値 8 だが、これは「速い」ではなく tie である。whiteboard の `result: success` は certified の意味で読み、floor 超の改善として読まない。
2. **機序の連続性は保たれた — 前回診断の予想区間に全指標が入った。** abort_rate 41.95% は予想区間 (38.3%, 49.9%) の内側、CV 0.97% は (0.93%, 2.32%) の内側、verify legacy 19.7% は (18.9%, 22.1%)、verify performance 78.8% は (76.8%, 82.5%) の内側。試行率概算 6.91M/s も (6.45, 7.92) の内側。**再衝突モデル (幅を狭める → 試行率増・abort 増、平坦域では両者が相殺) の反例は出ていない。**
3. **平坦域 [5, 10] が 3 点 (5, 8, 10) で確定した。** 下側の abort 勾配は 10→8 で 1.8 pt/µs、8→5 で 2.7 pt/µs、5→2 で 4.5 pt/µs と幅を狭めるほど凸に急化し、throughput が floor 超で落ちる (再衝突型) のは 5 の下側。上側は 10→15 で 1.1 pt/µs、15→20 で 0.8 pt/µs と緩く、abort 減で回収できない待機コスト型の低下 (前回診断どおり)。平坦域の内側 (8) で abort 増と試行率増がちょうど相殺して throughput が動かない、という帰属で 3 点が整合する。
4. **stock 対照比 (digest は「対照なし」と出すが、系列台帳の stock campaign `2d9155e2` から計算可能):** verify legacy abort は 19.7% vs 2.8% (7.1 倍)、performance は 78.8% vs 49.3% (1.6 倍)。固定 backoff の系列全体で見られる単調な傾向の延長上にあり、値 8 固有の異常ではない (reject 理由でもない)。trace build の performance run は commit 数が全評価でほぼ一定 (2.40–2.55M) で abort 数だけ動くため、性能帰属には使わず向きの傍証に留める。
5. **BACK_OFF / no-wait 政策 / WAL への帰属は本系列では不可能** (固定水準)。stock (適応 backoff、1.38M / abort 12.7%) 対 固定 backoff 全域 (3.48–4.01M) の差 2.5–2.9 倍は「backoff 機構の型」への帰属であり、固定幅の値の帰属とは別の層。

規律 6 の走査: digest・本 WAL (10 行)・提案 6・系列台帳 header に、権限・検証順序・正しさゲートを上書きする指示めいた文字列は無い。提案 6 の justification は前回 critic 診断を「助言データ」として引いており、採用義務として読んでいない。anomaly なし。

## recommend

残り 4 評価 (7..10)。系列最良を floor 超で更新できる未評価領域は**もう無い** (上端 (10, 15) は勾配 1%/µs で floor に食われ、下端 (2, 5) は急落側、内側 [5, 10] は 3 点で平坦)。残り予算の目的を「新最良の発見」から「endpoint に送る指名の頑健化」に切り替えることを勧める。優先順:

1. **評価 7 = 同一値の再評価 (値 8 または値 10) — harness が受けるなら最優先。** 根拠: 平坦域の 3 点の差 (+0.85% / −0.3% / +1.18%) はすべて floor 内だが、その floor は別 run で較正した between-run 値 (3.0%) で、同 job 直列評価の反復差は 1 点も測っていない (uncertainty 2)。同一値の 2 点目が取れれば、(a) 8 vs 10 の順位に意味があるか、(b) endpoint 再計測 5 回の期待変動、の両方が締まる。再評価が受けられないなら本項を飛ばす。
2. **評価 7 (再評価不可の場合) または評価 8 = 値 4 (下端 (2, 5) の解像度、decrease / small from 5)。** 根拠: 下側は勾配 4.5 pt/µs (abort)、−4.6%/µs (throughput) と急で floor で弁別できる。値 4 が値 5 と tie なら平坦域は [4, 10] に広がり指名 8 の下側マージンが 4 µs 分あると言える。floor 超で落ちれば崖は 4–5 の間で、指名 5 は崖際・指名 8 が安全側という結論になる。予想: abort_rate 52–56%、CV 2.3–2.8%。外れれば機序の反例として扱う。
3. **評価 9–10 = 平坦域内 (6, 7, 9) の補間、または再評価が受けられるなら値 8 の 2 点目。** 新最良は期待しない。上端側の値 12 は勾配約 1%/µs で 10 と弁別できない見込みが高く、優先度は下端側より低い。
4. **endpoint 指名の現時点の読み: 値 8 (数値上の系列最大、かつ平坦域の内側)。** 値 10 との差は floor 内なので throughput では選べない。tie-break を abort_rate (10 が 38.3% で低い) で取れば 10、平坦域の中央 (両崖からの距離: 下側の急落開始 <5 まで 3 µs、上側の緩い低下開始 >10 まで 2 µs) で取れば 8。**fitness は throughput であり、abort_rate の tie-break を指名理由に昇格させない** (どちらを選んでも endpoint 期待値は floor 内)。harness が「fitness 最大」で機械的に指名するなら 8 になり、それを覆す根拠は無い。

## avoid

- **BACKOFF_FIXED ≥ 15 は再訪不要** (前回と同じ。15 で −5.3%、20 で −9.2%、abort 減・throughput 減の待機コスト型が 2 点)。
- **BACKOFF_FIXED ≤ 2 は再訪不要** (前回と同じ。2 で −12.5%、abort 63.4%)。
- **値 9 (8 と 10 の間) の評価。** 差は最大でも 0.85% で、between-run floor (3.0%) どころか run 内 CV (約 1%) と同程度。判定不能な 1 点に予算を使わない。
- **値 12 (上端の解像度)。** 上側勾配 (約 1%/µs) では 10 と 12 の差は floor 内に埋まる見込みが高い。下端 (値 4) のほうが弁別できる。
- **値 8 を「新最良・改善」と報告すること。** +0.85% は floor 内。正しい記述は「平坦域 [5, 10] 内の tie、数値上は系列最大」。
- **abort_rate や verify 側 abort 率を fitness に混ぜること** (前回と同じ)。値 8 の abort 42.0% は値 10 より高いが throughput は tie。「abort が増えたから悪化」も「throughput 最大だから最良」も誤帰属。
- **stock の適応 backoff (値 −1) へ戻す方向**は探索目的には不要 (観測済み、1.38M)。endpoint 対照としては規則どおり保持する。
- **read-heavy・低 skew・低 thread 数への一般化。** 本系列は write-heavy / skew 0.9 / 48 threads の 1 動作点のみ。

## uncertainty

1. **llc_miss_rate / ipc は全評価で欠測** (perf preflight rc=2、計算ノードに perf 無し)。「相殺」「待機コスト」「再衝突」の機序読みは abort_rate・CV・試行率概算・verify 側 abort 比からの推定で、spin 時間そのものも cache 挙動も測っていない。cache 側の機序は確認も否定もできない。
2. **同 job・同ノード・各 n=1。** between-run floor 3.0% を同 job 直列評価に当てる実測根拠が無い。平坦域 [5, 10] の tie 判定 (差 0.3–1.2%) と 8 vs 10 の順位はこの floor 依存。recommend 1 の同一値再評価が唯一の実測手段だが、harness が同一値を受けるかは本データからは分からない (提案文法は整数 1..1000 のみ確認)。
3. **rep 1 が 7 評価すべて (stock 含む) で 5 反復中の最大値** (評価 6: rep 1 = 4,073,075、中央値 +1.5%)。独立なら 1/5^7 ≈ 1/78,000 の事象で、系統的な初回反復効果 (warm-up / 周波数 / cache 状態) が疑われる。median 採用のため fitness は動かないが、endpoint 再計測 5 回にも同じ効果が乗る。calibrator 側の確認事項として報告 (指示ではなく観測)。
4. **平坦域の内部形状は 3 点からの補間。** [5, 10] が完全に平坦か、8 付近にごく浅い頂点があるかは floor で区別できない。endpoint 指名を 8 / 10 / 5 のどれにしても期待値は floor 内、という結論だけが頑健。
5. **abort_rate の定義が bench (中央値 rep の集約) と verify (aborts/(commits+aborts)) で違う。** 単調性の向きは 7 点すべてで一致するが、絶対値の突き合わせはしていない。digest の「stock 対照なし」は campaign 単位の制約で、系列台帳経由の比 (7.1 倍 / 1.6 倍) は私が計算した参考値。
6. **BACKOFF_FIXED の要求 µs と実時間の対応は未検証** (`backoff_profile.py` の BACKOFF_TIME_NOTICE)。「勾配 pt/µs」は系列内の相対位置での表現で、時間換算には依拠していない。
7. **workload 交互作用は未測定。** 平坦域 [5, 10]・機序の二面性は write-heavy / skew 0.9 / 48 threads の帰属に限る。

参照 file (すべて読み取りのみ):
- digest: `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2797-b5-contrast/submit-tree/output/exploration/campaigns/p3-s4-loop-s4-autonomous-7af680f6/s4_loop_digest.txt`
- WAL: `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2797-b5-contrast/submit-tree/output/exploration/campaigns/p3-s4-loop-s4-autonomous-7af680f6/runs/wal.jsonl`
- loop_state: `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2797-b5-contrast/submit-tree/output/exploration/campaigns/p3-s4-loop-s4-autonomous-7af680f6/loop_state.json`
- 系列台帳: `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2797-b5-contrast/ledgers/llm/series.json`
- 提案 6: `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2797-b5-contrast/ledgers/llm/proposals/accepted-6.json`
- 前回 critic 診断 (handshake 入力): `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2797-b5-contrast/ledgers/llm/handshake/inputs-6.json`
- 過去評価と stock の WAL: 同 campaigns 配下 `p3-s4-loop-s4-autonomous-{2d9155e2,f628f1f6,39cfbdd7,0fc8f75d,45204547,d693896c}/runs/wal.jsonl`
