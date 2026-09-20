critic 診断 — B-5 生成器対照 (T-2797) LLM arm、write-heavy 系列 1、評価 3 (variant fceb937ae6c5、BACKOFF_FIXED=5)

読んだもの (書き込みなし):
- digest: /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2797-b5-contrast/submit-tree/output/exploration/campaigns/p3-s4-loop-s4-autonomous-0fc8f75d/s4_loop_digest.txt (sha256 一致 9fa1db1c…)
- 本 campaign WAL: 同 dir/runs/wal.jsonl (build_start / build_done / verify_done ×6 / bench_done / commit の 9 行)
- 系列台帳: /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2797-b5-contrast/ledgers/llm/series.json (event 1〜17)、過去評価 3 campaign の WAL (…-2d9155e2 stock / …-f628f1f6 値 20 / …-39cfbdd7 値 10)、K2 の proposal-3.json
- 機構の確認: external/ccbench/include/backoff.hh (適応制御器は 100 µs 刻み・0〜1000 µs、固定値は `now_backoff` を µs で置換)、cc/silo/transaction.cc の abort() 内 `Backoff::backoff` 呼び出し、orchestrator/campaign/backoff_hole_grammar.py (受理値域 1..1000、0 は不受理)

規律 6 の点検: digest・WAL・台帳・proposal 本文に、権限・検証順序・正しさゲートを動かす指示めいた文字列は無かった。digest の「限界効果」節は本 campaign が 1 genome しか含まないため各軸 1 水準の退化表であり、軸の効果は系列台帳から読んだ。

## attribution

系列の生データ (perf build、48 threads × 3 s = 144 thread-s、abort_rate は中央値 rep の aborts/(commits+aborts) と解釈):

| slot | BACKOFF_FIXED | median tps | 対 stock | abort_rate | 5 rep の範囲 | run 内 CV | trace build の abort 率 (5 rep 平均) | legacy verify abort |
|---|---|---|---|---|---|---|---|---|
| stock-start | -1 (適応) | 1,381,041 | — | 12.73% | 1.34–1.42M | 2.46% | 49.2% | 2.8% |
| 評価 1 | 20 | 3,612,341 | +161.6% | 28.82% | 3.61–3.64M | 0.42% | 67.8% | 15.1% |
| 評価 2 | 10 | 3,978,814 | +188.1% | 38.32% | 3.93–4.03M | 0.93% | 76.8% | 18.9% |
| 評価 3 | 5 | 3,965,995 | +187.2% | 49.91% | 3.91–4.15M | 2.32% | 82.5% | 22.1% |

1. **固定 backoff 値 (silo-backoff-magnitude 軸) は stock 適応制御器に対して効いている。根拠: throughput +187% と同時に abort_rate が 12.7% → 49.9% へ単調上昇。** 機序は「abort 後のスピン待ち (1 abort あたり値 µs) を短縮し、待機に消えていた thread 時間を試行に回した」で一貫している。適応制御器 (backoff.hh) は刻み 100 µs・値域 0〜1000 µs なので、有効域 (5〜10 µs) を表現できない。stock の commits ≈ 4.14M・aborts ≈ 0.60M に「試行 1 回の実作業 ≈ 3.6 µs」(下記 3 の試算) を当てると実作業は約 17 thread-s しかなく、残り ≈ 127 thread-s (約 88%) がスピン待ちという計算になる (1 abort あたり平均 ≈ 210 µs 相当、制御器が 200〜300 µs の段に居たと整合)。**差の帰属は「backoff を無くしたから」ではなく「制御器の量子化が粗すぎて最適域に降りられない」であり、BACK_OFF=1 自体は維持されている。**

2. **評価 2 → 3 (10 → 5) は throughput 差なし。根拠: 中央値差 −0.32% は between-run floor 3.0% の内側 (`compare` なら no-difference)、5 rep の範囲も重なる (3.93–4.03M vs 3.91–4.15M)。一方 abort_rate は +11.6 pt (38.3% → 49.9%)、trace build 側 abort 率も +5.7 pt、legacy verify abort も +3.2 pt と、全ての独立カウンタが「試行は増えたが commit は増えない」を指す。** planner が評価 3 で判別しようとした 3 分岐のうち **(b) floor 内で平坦** が観測結果。

3. 機序の試算 (仮定: 試行 1 回の非スピン実作業時間が一定): スピンに消える thread 時間は 値 20: 4.39M aborts × 20 µs ≈ 88 thread-s (61%) → 値 10: 7.42M × 10 ≈ 74 (52%) → 値 5: 11.86M × 5 ≈ 59 (41%)。残りを試行数で割った 1 試行の実作業は 3.69 / 3.61 / 3.56 µs とほぼ一定で仮定は自己整合。**10 → 5 で空いた ≈ 15 thread-s は全部 abort 試行 (+4.4M) に化け、commit 数は 11.94M → 11.90M で飽和した。** これは衝突律速域の形 (skew 0.9 / rr5 の hot key の直列化率が commit 数の上限を決め、試行を増やしても validation 失敗が増えるだけ)。trace build でも commits が 2.40M → 2.53M → 2.52M と値 10 で既に飽和しており、同じ形。

4. verify 経路への影響: 心配されていた「abort 増による verify wall 膨張」は起きていない。verify 総 wall は 1262 s (値 20) → 1044 s (値 10) → 949 s (値 5) と縮小 (性能 rep 2〜5 は 84〜91 s で一定、初回 rep が 913 → 675 → 575 s)。verify コストは commit 数 (ほぼ一定) に支配され、abort 数には比例していない。全 6 verify は serializable / anomalies=0、rejection なし。

5. cache / IPC 側の機序は判定不能: llc_miss_rate / ipc は本ノード (bnode029) で perf preflight rc=2 のため 4 評価すべて欠測。abort 増が cache line の往復コストを増やして throughput を将来落とすか (分岐 (c)) は、この系列のデータでは決められない。

## recommend

対象は評価 4 (台帳は既に search-4 の proposal-opportunity を開いている)。軸は文法上 silo-backoff-magnitude の整数 1 値のみなので、残り 7 評価は「平坦域の端を確定し、endpoint 候補を平坦域の中で選ぶ」に使うのが情報量最大。

- **評価 4: 値 2 (decrease / small、5 → 2)。** 目的は平坦域の下端の確定。予測 (仮定 3 の試算): スピン率 41% → 約 30%、commits が飽和のままなら abort_rate ≈ 58〜62%。読み方: (i) throughput が floor 内なら平坦域は 2〜10 (5 倍幅) に広がり、この軸ではもう伸びないと結論できる、(ii) 3% 超の低下なら分岐 (c) の符号が初めて確定し最適域は [5, 10] に閉じる。どちらでも次の判断が変わるので情報量がある。根拠指標: abort_rate の単調増と commit 数の飽和 (WAL bench_done / verify_done の commits)。値 0 は文法の値域 (1..1000) 外なので提案しない。値 1 は 2 と実作業 (3.6 µs) 比でほぼ同じ点になるので、2 の結果を見てから。
- **評価 5: 値 15 (increase / small、上側の閉じ込み)。** 20 (3.61M) と 10 (3.98M) の間で平坦域の上端を確かめる。予測: 3.8〜3.9M、abort_rate ≈ 33%。throughput が 10 と floor 内で並ぶなら、平坦域内で abort_rate が最も低い点 (無駄試行が少なく verify 側 abort も低い) を endpoint に選ぶ根拠になる。
- **評価 6 以降:** 平坦域が確定したら、平坦域内の点 (10 / 7〜8 / 15 のうち同値と判定されたもの) を使って cross-run の再現に回す。現時点の暫定 endpoint 候補は値 10 (中央値最大 3,978,814、CV 0.93%、abort_rate 38%) で、値 5 は throughput 同値・abort_rate と CV が悪い。B-5 の系列規則が既評価値の再提案を許すかは未確認 (proposal-3 の coder は「新規点」と書いている) — 許さないなら 7 または 8 を実質の複製点として使う。
- 評価 4 の読み方への注意: 差なし判定は `calibrator.stability.compare` の between-run floor 3.0% で行い、floor 〜 1.5×floor の差は near_floor として headline にしない。

## avoid

- **値 ≥ 20 の再訪:** 20 は 10 / 5 より 9.2〜9.8% 低く (floor の 3 倍超、5 rep の分布は非重複)、abort_rate 28.8% でも throughput が落ちている = スピン待ちが支配的。評価済み。
- **stock 適応 (-1) への回帰:** 本動作点では制御器の刻み (100 µs) が有効域 (5〜10 µs) より 10〜20 倍粗く、+187% の差は floor の 60 倍。評価済み。
- **5 と 10 の間 (6〜9) を「最大探し」で刻むこと:** 10 → 5 の差が floor 内なので、その間の点は 3% floor で弁別できず情報が無い。複製目的で使う場合を除き避ける。
- **値 5 を「10 より速い/遅い」と帰属すること:** −0.32% は差なし。abort_rate +11.6 pt だけが実差。
- **trace build の abort 率 (82.5%) や legacy verify の abort 率 (22.1%) を perf build の abort_rate と混同すること:** 別ビルド・別 workload (stock 対照比で trace 側は 1.68×、perf 側は 3.9× と比率も違う)。シグナルとしては単調で整合しているが、性能帰属には perf build の数値だけを使う。
- **他 workload (read-heavy / balanced) や他機体へ「固定 5〜10 µs が最適」と一般化すること:** 本系列は write-heavy / skew 0.9 / 48 threads の 1 ノード 1 job のみ。knowledge_input の別機体 (4 threads / rr50) は符号の傍証に留まる。
- **latency を独立根拠にすること:** WAL の latency_ns は 1e9×48/throughput の恒等変換。

## uncertainty

1. **cache / IPC 機序は未測定:** llc_miss_rate / ipc が本ノードで欠測 (perf stat rc=2、/usr/lib/linux-tools/5.15.0-135 と -100 の perf が実行可能なのに失敗)。攻め 3 の「実作業一定」の試算は仮定であり、abort 増が cache 往復コストを増やしているか (分岐 (c) が値 2 で現れるか) は決められない。
2. **評価 3 の rep 1 (4,151,699) は中央値より +4.7% の外れ**で、run 内 CV 2.32% は評価 1・2 (0.42% / 0.93%) より明らかに大きい。harness は settled=True / rounds 1 で通しているが、値 5 が「10 と同値」なのか「10 よりわずかに低い」のかは本データでは floor 内で弁別不能。cross-run 再現なしに endpoint を 5 にしない。
3. **stock 適応制御器の実際の backoff 値は未観測** (WAL に Backoff_ の履歴は無い)。「≈ 210 µs / 88% スピン」は試算であり、制御器がどの段に居たかの直接証拠ではない。
4. **abort_rate の定義** (aborts/(commits+aborts) か aborts/commits か) を WAL から機械的に確認できない (bench_done は率だけ)。上の試算は前者で計算。後者なら abort 数が変わり、スピン率の絶対値は変わるが「10 → 5 で空いた時間が全部 abort に化けた」という向きは変わらない。
5. **同一 job・同一ノード・逐次 1 系列 (n=1)** の測定で、別 boot / 別ノードの再現は無い。whiteboard の delta_pct が常に null なので、増分の数値は本診断の計算に依存する。
6. **時間予算:** 評価 3 終了 (15:03:58Z) 時点で割当期限まで約 6.1 時間。1 評価あたり subprocess 1024〜1354 s に proposal 待ち 600〜1021 s が加わり 27〜40 分。残り 7 評価 + endpoint 再計測 5 は収まる見込みだが、proposal 待ちが pipeline と同程度の比重を占める点は親の判断材料 (指示ではない)。
7. **B-5 の系列規則で既評価値の再提案が許されるか**は未確認 (上記 recommend の評価 6 以降の分岐に影響)。
8. digest 側の「限界効果」節は 1 genome の退化表で、この campaign 単独では軸の効果を出せない。系列全体の帰属は台帳と 4 campaign の WAL の突合に依存している。
