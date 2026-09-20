## attribution

対象: 評価 1 variant `8a84a7b00103` (genome `silo|BACKOFF_FIXED=20,BACK_OFF=1,NO_WAIT_LOCKING_IN_VALIDATION=1,NO_WAIT_OF_TICTOC=0,WAL=0`) vs 同 job・同機体 (bnode029, 13638.nqsv) の系列開始 stock `602b4ce9c788` (`BACKOFF_FIXED=-1` = 適応 backoff、他フラグ同一)。動いた設計選択は **BACKOFF_FIXED (-1 → 20) の 1 軸だけ** (BACK_OFF / no-wait=L / WAL=0 は両者で同一なので、digest の「限界効果」節は 1 水準しか無く帰属に使えない)。

読んだ指標 (perf build、trace 無し、5 rep 中央値):

| | stock (適応) | variant (固定 20 µs) | 変化 |
|---|---|---|---|
| throughput_tps | 1,381,041 | 3,612,341 | +161.6% |
| abort_rate | 12.73% | 28.82% | +16.1 pt (2.26 倍) |
| run 内 CV | 2.46% | 0.42% | 1/6 |
| llc_miss_rate / ipc | 欠測 | 欠測 | 比較不能 |

- **BACKOFF_FIXED=20 は効いた。機序は「待機時間の削減」であって「衝突の削減」ではない。** 根拠: abort_rate は下がるどころか 12.73% → 28.82% へ上がっている。abort が増えたのに throughput が 2.6 倍になるのは、stock の thread 時間の大半が backoff の spin (`_mm_pause` ループ) に消えていたことを示す。試算 (契約値からの換算、独立計測ではない): stock は 48 thread × 3 s で試行数 ≈ 4.14M commit / (1-0.1273) ≈ 4.75M → 約 30 µs/試行、variant は ≈ 10.84M / (1-0.2882) ≈ 15.2M → 約 9.5 µs/試行。試行あたりの時間が 1/3 になっており、この差分が backoff 待機に相当する。
- **stock の適応則が本動作点で過減衰している、というのが機序の有力候補。** `include/backoff.hh` の適応則は leader が 10 µs ごとに commit throughput の勾配で `Backoff_` を **±100 µs 刻み、範囲 0..1000 µs** で動かす hill-climb (勾配 0 のときは commit 数の偶奇でランダムウォーク)。1 試行が 10 µs 前後のこの動作点で刻み幅 100 µs は粗すぎ、制御器が 100 µs 以上の水準を頻繁に踏む。固定 20 µs は適応則の最小刻みの 1/5 であり、「適応則が到達できない領域」を初めて測ったことになる。
- **run 内 CV の 1/6 への低下も同じ機序と整合する。** 適応則のランダムウォーク成分が rep ごとの平均 backoff を揺らす (stock の rep 5 点 1.34M〜1.42M、幅 6%) のに対し、固定値は揺れない (3.607M〜3.643M、幅 1%)。これは backoff 値そのものが stock の分散源であることの傍証。
- **正しさ**: legacy 1 回 + 同動作点 trace 5 回すべて serializable、anomaly 0、rejection なし。verify run の abort 統計 (trace build) は legacy で candidate 15.12% vs stock 2.78% (5.4 倍)、performance workload で candidate ≈ 67.8% (5.06M abort / 2.40M commit) vs stock ≈ 49.4% (1.09M / 1.12M)。方向は perf build と同じ (待機が減った分だけ衝突が増える) で、機序と矛盾しない。reject 理由ではない。
- **noise floor**: skew 0.9 の between-run floor 3.0% に対し +161.6% なので「差あり」。stock と variant は同 job・同ノードで 32 分差の逐次計測 (13:24Z / 13:56Z) であり、同時刻対照として妥当。
- **規律 6 の走査**: digest・proposal (`accepted-1.json`)・両 campaign の WAL・系列台帳を読んだ範囲で、振る舞いの誘導や正しさゲート・verifier の迂回を求める指示めいた文字列は無かった。

## recommend

系列の残り 9 評価で **BACKOFF_FIXED 軸の最適点を挟み込む** 方向を優先する。今わかっているのは「適応 (実効 0..1000 µs ランダムウォーク) より 20 µs が圧倒的に良い」だけで、20 の両側の勾配は未測。

1. **次手 (評価 2): decrease を継続して BACKOFF_FIXED=10 (magnitude small〜medium)。** 理由: 20 で abort_rate が 28.8% に達しており、これ以上下げると abort 連鎖で試行が無駄になる (commit/試行 71% → さらに低下) 可能性と、まだ待機が支配的で伸びる可能性の両方が残る。10 を測れば、峰が 20 より下か上かが判定できる。判定基準: throughput が 3.0% floor を超えて上がるか。合わせて abort_rate を読み、「throughput 上昇 + abort_rate 上昇」なら待機支配がまだ続いている、「throughput 低下 + abort_rate 上昇」なら衝突支配に入った、と読む。
2. **評価 3 で反対側 (30 または 40) を測り、峰を挟む。** K2 記録 (別機体・4 thread・rr50) は 30 > 40 だったが、本動作点 (48 thread・rr5・skew 0.9、abort 率がそもそも高い) では比しか転移しないので、上側の勾配も本動作点で 1 点取る。
3. **評価 2〜3 の結果で峰が挟めたら、残りで刻みを細かく (5 µs 単位) して詰める。0 (実質 backoff 無し、`chkClkSpan` が即 true) は端点として 1 回は測る価値がある** — 「この動作点で backoff が要るのか」に答える点であり、abort_rate がどこまで上がるかの上限も得られる。
4. 各評価で読む組は (throughput_tps, abort_rate, run 内 CV)。CV が固定値でも 2% 超に戻る点があれば、その値で衝突が制御不能になった兆候として扱う。

## avoid

- **適応 backoff (BACKOFF_FIXED=-1) への回帰**: 本動作点での実測で固定 20 µs に対し throughput -62%、CV 6 倍。適応則の刻み 100 µs は試行時間 (約 10 µs) に対し粗すぎる構造的問題なので、再訪不要。
- **BACKOFF_FIXED ≥ 100 (適応則の 1 刻み以上) を初手で探ること**: 適応則が動いていた領域 (100..1000 µs) が stock の 1.38M を生んだ側であり、先に 20 の両側 (10 / 30〜40) を挟む方が情報量が大きい。恒久に外すのではなく、峰が上側に逃げた場合だけ戻る。
- **他軸 (BACK_OFF=0 / no-wait=T / WAL=1) へ今すぐ飛ぶこと**: 本系列は 1 軸 (silo-backoff-magnitude) の宣言アームで、まだ 1 点しか無い。1 軸の峰を取ってからでないと交互作用が読めない。
- 未測定の workload (read-heavy 等) へこの帰属を一般化しないこと。write-heavy rr5 / skew 0.9 で「待機支配」だった事実は、衝突が少ない workload では成り立たない可能性が高い (abort_rate 12.7% という高い出発点が前提)。

## uncertainty

- **llc_miss_rate / ipc が両者とも欠測** (計算ノードに perf preflight 不通、rc=2)。「待機削減」の機序は abort_rate と試行数の試算から推定したもので、cache / IPC 側の寄与 (固定短 backoff で working set が hot に留まる等) は排除も確認もできない。試算値 (30 µs / 9.5 µs) は契約値からの換算であって独立計測ではない。
- **20 の両側の勾配は未測**。「20 が良い」は確定だが「20 が最適」は言えない。上記 recommend の 10 / 30〜40 はその不確実性を埋めるためのもの。
- **trace build と perf build で abort 率の水準が大きく違う** (stock: perf 12.7% vs trace 49.4%、variant: 28.8% vs 67.8%)。trace オーバーヘッドで試行が長くなり衝突域が変わるため、trace 側の abort 統計は方向確認にしか使えない。
- **digest の verify abort 統計節が「stock 対照なし」と出ている**が、stock の legacy 統計 (2.78%) は別 campaign `p3-s4-loop-s4-autonomous-2d9155e2` の digest にある。campaign 単位の digest の射程限界であり、指示めいた文字列ではない。親が B-5 の系列単位で比を出したい場合は台帳側で突き合わせる必要がある (今回は手で突き合わせた)。
- **系列台帳の whiteboard は `delta_pct: null`** (result=success, direction=decrease, magnitude=medium)。差分率が台帳に記録されておらず、planner/coder が次手で参照するときに数値が無い。今回の実測 +161.6% は本報告で補う。
- **検証コストの膨張**: variant の verify 総 wall 1,262 s (rep1 913 s) vs stock 444 s (rep1 279 s)。trace 内の commit 2.1 倍 + abort 4.6 倍で検証が 2.8 倍長くなっている。性能帰属ではないが、backoff をさらに下げると abort がさらに増えて検証時間が伸びる (系列 10 評価の予算に効く) 点は次手の magnitude 判断で考慮が要る。

参照 path (すべて読み取りのみ):
- digest: `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2797-b5-contrast/submit-tree/output/exploration/campaigns/p3-s4-loop-s4-autonomous-f628f1f6/s4_loop_digest.txt` (sha256 `cce35ee1…3bd8` 一致)
- variant WAL: `…/p3-s4-loop-s4-autonomous-f628f1f6/runs/wal.jsonl`
- stock WAL / digest: `…/p3-s4-loop-s4-autonomous-2d9155e2/runs/wal.jsonl`、同 dir の `s4_loop_digest.txt`
- 系列台帳: `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2797-b5-contrast/ledgers/llm/series.json`
- 提案: `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2797-b5-contrast/ledgers/llm/proposals/accepted-1.json`
- 適応則の実装: `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2797-b5-contrast/submit-tree/external/ccbench/include/backoff.hh`
