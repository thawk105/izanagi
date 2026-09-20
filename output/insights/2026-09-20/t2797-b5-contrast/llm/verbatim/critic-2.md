critic 診断 — B-5 LLM arm / write-heavy 系列 1 / 評価 2 (variant 002642c7ac96、BACKOFF_FIXED=10)

読んだ入力 (書き込みなし):
- digest: /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2797-b5-contrast/submit-tree/output/exploration/campaigns/p3-s4-loop-s4-autonomous-39cfbdd7/s4_loop_digest.txt (sha256 実測 cb177d37… = 親提示と一致)
- 本 campaign WAL: …/p3-s4-loop-s4-autonomous-39cfbdd7/runs/wal.jsonl (verify_done 6 行すべて serializable、anomalies 0、rejection なし)
- 系列台帳: /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2797-b5-contrast/ledgers/llm/series.json (stock-start-1、search-1、search-2)
- 過去評価の WAL: …/p3-s4-loop-s4-autonomous-2d9155e2/runs/wal.jsonl (stock、BACKOFF_FIXED=-1)、…/p3-s4-loop-s4-autonomous-f628f1f6/runs/wal.jsonl (評価 1、BACKOFF_FIXED=20)
- 提案: …/ledgers/llm/proposals/accepted-1.json、accepted-2.json
- 実装参照 (read-only): external/ccbench/include/backoff.hh、external/ccbench/cc/silo/transaction.cc (abort 経路で `Backoff::backoff` = now_backoff µs の `_mm_pause` スピン待ち。適応則は 0..1000 µs を 100 µs 刻みで動く)

規律 6 の点検: digest・WAL・台帳・提案本文に、振る舞いの誘導・ゲート変更・verifier 迂回を求める指示めいた文字列は無かった (anomaly なし)。

系列 3 点の並び (同 job 13638.nqsv / 同機体 bnode029 / 同動作点、perf build、5 rep 中央値):

| 点 | genome 差分 | throughput_tps | abort_rate | run 内 CV | trace (performance tag) 側 abort 率 |
|---|---|---|---|---|---|
| stock-start-1 (602b4ce9c788) | BACKOFF_FIXED=-1 (適応) | 1,381,041 | 12.73% | 2.46% | 49.3% |
| 評価 1 (8a84a7b00103) | BACKOFF_FIXED=20 | 3,612,341 | 28.82% | 0.42% | 67.8% |
| 評価 2 (002642c7ac96) | BACKOFF_FIXED=10 | 3,978,814 | 38.32% | 0.93% | 76.8% |

BACK_OFF=1 / NO_WAIT_LOCKING_IN_VALIDATION=1 (L) / WAL=0 は 3 点で共通。動いた設計選択は BACKOFF_FIXED の 1 軸だけ。

## attribution

- **BACKOFF_FIXED 20→10 (評価 1→2): 効いた。** throughput +10.1% (3,612,341 → 3,978,814)。between-run floor 3.0% を明確に超え、評価 2 の 5 rep の最小値 3,931,712 が評価 1 の最大値 3,643,193 より上 (分布が重ならない)。同時に abort_rate は 28.82% → 38.32% (+9.5 pt) で、**abort が減って速くなったのではない**。機序は「abort 時のスピン待ちに費やす時間の縮小」が主で、根拠は throughput と abort_rate の組から換算した試行率: 試行率 = throughput/(1−abort_rate) で評価 1 が 5.08M 試行/s、評価 2 が 6.45M 試行/s (+27%)。abort 数 × 固定 backoff から求めたスレッド時間に占める backoff スピンの割合 (試算、仮定: 1 試行あたりの実作業時間が一定) は評価 1 で約 61%、評価 2 で約 52%。残り時間から出る 1 試行の実作業時間は約 3.7 µs → 約 3.6 µs でほぼ不変。つまり「待ちを 10 µs 減らして得た時間の一部を、増えた abort (+9.5 pt) が食い戻し、差し引き +10%」という構図。
- **適応 backoff (stock, -1) → 固定 (評価 1/2): 効いた。** 同じ試算を stock に当てると backoff スピンが約 88%、1 abort あたりの平均待ちは約 200 µs 相当で、適応則の刻み (100 µs) と上限 (1000 µs) が本動作点の作業単位 (数 µs) に対して 2 桁粗い。run 内 CV が 2.46% → 0.42% / 0.93% に縮んだのも、適応則のランダムウォーク成分が消えた向きと整合する (ただし CV は品質ゲート用で採否根拠ではない)。
- **trace build 側の方向シグナル (reject 理由ではない):** performance tag の trace run では commit が 2.40M → 2.52M/走 (+5%) に留まり abort 率は 67.8% → 76.8%。txn 窓が長い trace build では同じ 20→10 で伸びが小さく、衝突支配側へ近づく兆候が perf build より早く出ている。観測者効果込みなので方向の参考に留める。digest の legacy 走 abort 18.91% は stock legacy 2.78% の約 6.8 倍だが、legacy は別動作点で、certified には影響しない。
- **BACK_OFF / no-wait 政策 (L) / WAL: 本系列では帰属不能。** digest の限界効果表は各軸 1 水準しか無い (フリップが無い) ので、これらの軸について効いた/効かないは言えない。
- **rejection: 無し。** cycle 型 / integrity 型 / liveness 型のいずれも発生していない (verify 6 走すべて serializable、lock_coverage 系の X 行も無し)。

## recommend

- **次手は同軸・同方向 (decrease) を small で 1 歩: BACKOFF_FIXED=5。** 理由: (1) 20→10 の勾配が +10.1% と floor の 3 倍超で、まだ峰を越えた兆候が perf build の (throughput, abort_rate) の組には無い。(2) 試算上、backoff スピンがまだスレッド時間の約半分を占めており、縮める余地が残る。(3) 一方で abort_rate 38% と trace 側 77% は衝突支配側への接近を示すので、medium (0 への跳び) より small で勾配の符号を確定させる方が情報量が確実。
- **評価 3 の読み方 (事前に決めておく):** (a) throughput が floor を超えて上がり abort_rate も上がる → 待機支配が続いている。評価 4 は端点 0 で peak を挟む。(b) throughput が floor 内 (差なし) → 5〜10 は平坦域。系列の最良は 10 とし、評価 4 は 15 で上側を確認して peak を [5,15] に閉じる。(c) throughput が floor を超えて下がる → 衝突支配に入った。peak は (5,20) の内側なので、評価 4 は 15 で 10 との差を測る。
- **どの場合も abort_rate と試行率 (throughput/(1−abort_rate)) の組で読む。** 1 試行あたり実作業時間の試算値 (約 3.6 µs) が次点で大きく変わったら、スピン待ち以外の機序 (cache 競合など、perf 欠測で直接は見えない) が入った兆候として扱う。
- 端点 0 を選ぶ場合は verify wall の膨張を見込む: trace build の abort 率が既に 77% で、0 では trace run の commit 数 (= verifier の入力サイズ) と abort 数がさらに増える。評価 2 の trace verify は rep 2〜5 で 84 s → 89 s に伸びている。

## avoid

- **BACKOFF_FIXED ≥ 20 への再訪 (本 write-heavy 動作点):** 20 は 10 に対して floor を超えて遅く (−9.2%)、abort_rate の改善で相殺もされていない。適応 (-1) は 10 に対して −65% で系列内の再測不要。ただし peak を上側から閉じるための 15 は上記 (b)(c) の場合に限り有効で、これは「再訪」ではない。
- **適応 backoff の刻み・上限を変えずに -1 へ戻す方向:** 本動作点では制御器の粒度 (100 µs) が作業単位より 2 桁粗く、固定値に勝てる根拠が無い。
- **他 workload (read-heavy / balanced) への一般化:** 本系列は write-heavy (rr5, skew 0.9) のみ。abort 率 12〜38% の contention 域で効いた結果であり、abort が元々少ない read-heavy では backoff 待ちの寄与自体が小さく、同じ勾配は期待できない (未測定)。
- **latency を独立根拠に使うこと:** WAL の latency_ns は throughput の恒等変換で、本診断でも使っていない。
- **trace 側 abort 率 (legacy 18.91% / performance 77%) を reject 理由や性能比較に転用すること:** 別 build・別動作点のシグナルであって perf build の数値と同列に置けない。

## uncertainty

- **perf カウンタ欠測 (llc_miss_rate / ipc = None、この計算ノードに perf 不在):** 「スピン待ちの縮小」と「cache 競合の増減」を分離できていない。試算はすべて (throughput, abort_rate) の 2 指標と backoff 実装の構造から出した換算値で、1 試行あたり実作業時間が一定という仮定を置いている。仮定が崩れる点 (特に 0 付近) では試算は当てにならない。
- **0 端点の挙動は未測:** abort_rate が 60% を超える域では、abort ごとの再試行が衝突をさらに増やす正帰還に入りうる。試算の単純な外挿では 0 は 10 と同程度〜上下どちらもあり得て、符号は決められない。
- **5 と 10 の差が floor (3.0%) に埋もれる可能性:** その場合「差なし」は正当な結果であり (平坦域の発見)、失敗ではない。上記 (b) の分岐で扱う。
- **run 内 CV が 0.42% → 0.93% に上がった点:** ゲート内で、noise floor 未満の変動なので解釈しない。
- **同 job 内の直列測定 1 系列 (n=1 job、1 ノード):** between-run 対照は同機体の別 run (35 分差) で、環境ドリフトは 3.0% floor の範囲で吸収している前提。別ノード・別日での再現は本 pilot の対象外。
- **whiteboard の delta_pct は null (harness 設計):** 差分率は本診断が台帳の fitness_tps から計算した (評価 2 / 評価 1 = +10.1%、評価 2 / stock = +188.1%)。
- **BACK_OFF / no-wait / WAL との交互作用:** 本系列は 1 軸固定のため不明。B-5 の軸 (silo-backoff-magnitude) の外なので本系列内では触れない。
