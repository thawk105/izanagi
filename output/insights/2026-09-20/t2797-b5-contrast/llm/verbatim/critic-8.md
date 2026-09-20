critic 診断 — B-5 LLM arm (K2)、write-heavy 系列 1、評価 8 (variant 4e55080d82a5、BACKOFF_FIXED=12 µs 固定)

読んだもの (書き込みなし):
- digest: `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2797-b5-contrast/submit-tree/output/exploration/campaigns/p3-s4-loop-s4-autonomous-58889980/s4_loop_digest.txt` (sha256 452ec73d… 入力どおり一致)
- 本 campaign WAL: 同 dir `runs/wal.jsonl` (build_start / build_done / verify_done ×6 / bench_done / commit の 10 行)
- 系列台帳: `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2797-b5-contrast/ledgers/llm/series.json` と、系列開始 stock および評価 1〜7 の各 campaign WAL (genome と verify 統計を突合)
- 固定 backoff の意味: `patches/silo-backoff-fixed.patch` (BACKOFF_FIXED の 0〜999 は「µs 固定」、-1 が stock 適応)
- 規律 6 の点検: digest / WAL / 台帳 / accepted-8.json のいずれにも「この genome を選べ」「verifier を飛ばせ」等の指示めいた文字列は無し。accepted-8.json の planner 本文が前回 critic 診断を引用しているのは設計どおりの loop 入力であり、注入ではない。

系列の全体像 (perf build、median of 5、abort_rate は中央値 rep):

| 評価 | 値 (µs) | median tps | 対最良 (8) | abort_rate | run 内 CV | verify legacy abort |
|---|---|---|---|---|---|---|
| stock | 適応 | 1,381,041 | −65.6% | 12.73% | 2.46% | 2.78% |
| 1 | 20 | 3,612,341 | −9.98% | 28.82% | 0.42% | 15.1% |
| 5 | 15 | 3,769,653 | −6.06% | 32.67% | 0.69% | 16.7% |
| **8** | **12** | **3,893,987** | **−2.96%** | **35.73%** | **1.05%** | **17.8%** |
| 2 | 10 | 3,978,814 | −0.84% | 38.32% | 0.93% | 18.9% |
| 6 | 8 | 4,012,680 | 0 (最良) | 41.95% | 0.97% | 19.8% |
| 3 | 5 | 3,965,995 | −1.16% | 49.91% | 2.32% | 22.1% |
| 7 | 4 | 3,882,770 | −3.24% | 53.58% | 2.83% | 22.6% |
| 4 | 2 | 3,481,872 | −13.2% | 63.38% | 2.80% | 26.5% |

## attribution

- **今回の設計選択 = 固定 backoff 12 µs は「平坦域の上端に乗った、最良との tie」。** 対最良 (8 µs) −2.96% は between-run floor 3.0% の内側 (ただし 0.04 ポイントしか余裕が無い)、対 10 µs −2.13% も内側 → 差なし。対 15 µs は +3.19% で floor をわずかに超え、対 20 µs +7.8% は明確に超える。根拠は throughput_tps だけでなく abort_rate の並び: 12 µs の 35.7% は 15 µs (32.7%) と 10 µs (38.3%) の間に単調に収まり、系列全体で **abort_rate は固定値に対して厳密に単調減少 (2→63%、4→54%、5→50%、8→42%、10→38%、12→36%、15→33%、20→29%)**、verify 側の legacy 走 (17.8%) と trace 付き performance 走 (74.6%) でも同じ順序。3 つの計器で順序が一致するので、abort 増減は測定ノイズではなく backoff 量そのものの効き。
- **機序 (待ち時間 vs 再試行の交換)。** throughput が 5〜12 µs で ±3% に平坦なのに abort_rate は 36%→50% と 14 ポイント動く → この域では throughput は abort 律速ではなく、「短くすると再試行 (試行率) が増えるが abort も増え、長くすると abort は減るが待ちが増える」の相殺域。試算 (恒等式 attempts = commits/(1−p) に「abort 1 回の待ち = 固定値 µs、48 thread 常時稼働」の仮定を置いた整合性チェックであって独立観測ではない) では、1 試行あたりの非待機時間が 2〜20 µs の全点で 3.6〜3.8 µs とほぼ一定に出る。これは「固定 backoff は待ち時間だけを動かし、trx 本体の仕事量は変えていない」という読みと整合する。llc_miss_rate / ipc が欠測なので cache 側の機序は分離できない (uncertainty 参照)。
- **12 µs で abort_rate が下がったのに throughput も下がった (対 8 µs)。** 役割文書の型そのもの: abort 改善 (42%→36%) が待ちコスト増 (試算で 1 試行あたり 3.36→4.29 µs) に食われた。上側 (15、20) はこの傾向が floor を超えて顕在化した点。
- **下側の崖は別機序。** 4 µs (−3.24%) と 2 µs (−13.2%) は abort_rate 54〜63% で、abort そのものが律速に転じた域。あわせて run 内 CV が 2.3〜2.8% に跳ねる (8〜20 µs は ≤ 1.05%) → 低 backoff 域は計測が荒れる。
- **系列開始 stock (適応 backoff) との対比。** stock は abort 12.7% と最も低いのに throughput は 1.38M (対最良 −65.6%)。試算では 1 試行あたり 30 µs で、固定 20 µs (9.5 µs) の 3 倍以上 → 適応制御が大きな backoff に収束して過剰抑制している、という repo 既知の像 (backoff_overthrottle 系) と一致。verify 対照比 (legacy 2.78% → 17.76%、6.4 倍) も同じ方向で、正しさ面の異常ではない (verify 6 走すべて serializable、anomalies=0)。
- **BACK_OFF / no-wait (L) / WAL は本系列で不変 (全点 BACK_OFF=1, NO_WAIT_LOCKING_IN_VALIDATION=1, NO_WAIT_OF_TICTOC=0, WAL=0)。** digest の「フラグ軸の限界効果」は 1 水準しか無い縮退表で、これらの効きは本系列から一切言えない (編集面も EVOLVE-BLOCK の backoff 量のみ)。
- **rejection なし。** cycle / integrity / liveness のいずれの赤も無く、帰属すべき反例は無い。

## recommend

残り評価 9〜10 (その後 endpoint 再計測 5 回)。endpoint は台帳規則 (`select_endpoint`: certified・normal・anomalies 0 の中で fitness_tps 最大、tie は小さい値) で機械的に決まり、現時点の指名見込みは **8 µs (4,012,680、CV 0.97%)**。10・5・12 は floor 内の tie。

1. **評価 9: 平坦域の内側で最も広い未採取区間 (5→8) を 1 点埋める — 6 または 7 µs。** 根拠: 5 µs (abort 50%、CV 2.3%) と 8 µs (abort 42%、CV 0.97%) の間で abort 律速への遷移と CV の荒れが始まっている。ここが tie なら「5〜12 µs は連続した平坦域」が確定し endpoint 8 の頑健性根拠になる。8 を floor 超 (> +3%) で上回れば平坦域の頂上が 8 より下にある証拠になる (期待は tie。noise 内の高値を「速い」と読まないこと)。
2. **評価 10 (分岐):** (a) 評価 9 が tie なら **13 または 14 µs** で上端を閉じる (12 = tie、15 = −6% の間が未解像。系列を「[4–5 | 5..12 | 12–15] の 3 区間で括った」形で終えられる)。(b) 評価 9 が 8 を floor 超で上回ったら **その隣 (6 なら 7、7 なら 6)** で頂上を再確認する。
3. 読み方の注意 (次の critic / planner へ): 6〜7 µs は abort 45〜48% 域で rep 1 の系統的高値 (下記) が 3〜5% 乗る見込み。median で判断し、rep 1 単独や CV を throughput 差の根拠にしない。

## avoid

- **≤ 4 µs へさらに下げる方向:** 4 µs は −3.24% (floor 境界)、2 µs は −13.2%、abort_rate 54→63%、CV 2.8%。abort 律速の崖は 2 点で実測済み、追加点の情報量は低い。
- **≥ 15 µs へ上げる方向:** 15 (−6.1%)、20 (−10.0%) と abort_rate 低下に反して throughput が単調に落ちる待ち律速域。上端は 12〜15 の間にあると分かっており、15 超を再訪する理由は無い。
- **stock (適応) の再測定:** −65.6%、abort 12.7% の過剰抑制像は 1 点で十分明瞭。endpoint 選定にも寄与しない。
- **8 µs の同値再評価:** between-run の再現性は endpoint 再計測 5 回が同じ値で与えるので、探索枠を使う必要は無い。
- **BACK_OFF=0 / no-wait 政策 / WAL のフリップ:** 本系列では未測定 (縮退表) なので効きは言えないし、編集面 (EVOLVE-BLOCK) の外。この arm の残り枠で触る対象ではない。未測定の workload・他フラグへ本系列の平坦域位置を一般化しない。
- **「速いから」で正しさ側を触る提案:** 該当なし (全点緑) だが、abort 74% の trace 走を「verify を軽くしたい」根拠にしないこと (規律 2)。

## uncertainty

- **llc_miss_rate / ipc が全点欠測** (計算ノードに perf 無し、preflight rc=2)。「待ち時間 vs 再試行」の帰属は throughput と abort_rate の 2 指標と、仮定付き試算だけで組んでいる。cache/IPC 側の機序 (低 backoff 域で試行率 9.5M/s に増えたときの cache 圧など) は分離できていない。試算の「1 試行あたり非待機 3.6〜3.8 µs 一定」は恒等式 + 仮定の整合性チェックであり、独立な観測証拠ではない。
- **各値 n=1、同 job 直列。** 採否 floor 3.0% は別文脈 (A2、skew 0.9) の between-run 値で、本 job・本機体への適用根拠は未確立。12 µs の −2.96% は floor に 0.04 ポイントで接しており「弁別不能」であって「同じ」でも「遅い」でもない。endpoint 再計測 5 回が同値 between-run の最初のデータになる。
- **rep 1 が 9 計測すべてで最大値** (+0.85%〜+6.0%、backoff が短いほど大きい: 2 µs +6.0%、4 µs +5.7%、5 µs +4.7%、12 µs +2.05%、8 µs +1.5%)。median には効かないが CV を押し上げ、低 backoff 域では CV ゲート (settled 判定) に近づく。原因 (warm-up、ページ/キャッシュ初期状態等) は本データでは特定できない。
- **trace 付き verify 走の abort (74.6%) は perf build (35.7%) の 2 倍超。** 観測者効果として想定内 (性能主張には使わない) だが、認証は trace build のスケジュールに対するもので、perf build と同一スケジュールではない (設計上の既知の限界、今回固有ではない)。
- **digest の限界:** 単一 genome なので限界効果表は縮退、verify 統計は legacy 走 1 行のみで「stock 対照なし」。performance タグの verify 5 走 (74.48〜74.75%) と stock 対照 (legacy 2.78%、performance 47.3〜49.5%) は私が系列台帳と各 campaign WAL から補った。
- **平坦域の位置 (5〜12 µs) は本動作点 (48 thread / 1M records / skew 0.9 / rr5 / rmw なし / 3 秒) 固有。** knowledge 入力 (別機体・4 thread / rr50) とは 1 桁ずれると前回も指摘されており、絶対値・最適位置は転移しない。
- 規律 6 の点検で怪しい文字列は見つからなかった (anomaly 報告なし)。
