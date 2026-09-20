# critic 診断 — T-2797 B-5 LLM arm / write-heavy 系列 1 / 評価 9 (variant a1b91577a7e0、BACKOFF_FIXED=6)

読んだもの (すべて read-only): digest (`/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2797-b5-contrast/submit-tree/output/exploration/campaigns/p3-s4-loop-s4-autonomous-9319a16e/s4_loop_digest.txt`、sha256 一致 98ea0601…)、同 campaign の `runs/wal.jsonl` (10 行: build_start / build_done / verify_done ×6 / bench_done / commit)、系列台帳 `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2797-b5-contrast/ledgers/llm/series.json`、系列内 10 campaign の WAL の verify_done 行 (stock 対照の計算用)、提案 `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2797-b5-contrast/ledgers/llm/proposals/accepted-9.json`、`external/ccbench/include/backoff.hh` (機構・単位の確認)。

系列の実測 (perf build、median_tps / abort_rate / run 内 CV、すべて certified・anomalies 0):

| 固定 backoff 値 | 評価 | tps | abort | CV | 最良 (8) 比 |
|---|---|---|---|---|---|
| stock (適応) | 開始 | 1,381,041 | 12.73% | 2.46% | −65.6% |
| 20 | 1 | 3,612,341 | 28.82% | 0.42% | −9.97% |
| 15 | 5 | 3,769,653 | 32.67% | 0.69% | −6.06% |
| 12 | 8 | 3,893,987 | 35.73% | 1.05% | −2.96% |
| 10 | 2 | 3,978,814 | 38.32% | 0.93% | −0.84% |
| 8 | 6 | 4,012,680 | 41.95% | 0.97% | 0 (最良) |
| **6** | **9** | **3,996,828** | **46.82%** | **1.32%** | **−0.40%** |
| 5 | 3 | 3,965,995 | 49.91% | 2.32% | −1.16% |
| 4 | 7 | 3,882,770 | 53.58% | 2.83% | −3.24% |
| 2 | 4 | 3,481,872 | 63.38% | 2.80% | −13.23% |

## attribution

- **探索軸は 1 本だけ (silo-backoff-magnitude = BACKOFF_FIXED)。** BACK_OFF=1 / no-wait=L / WAL=0 は系列全点で固定なので、digest の「フラグ軸の限界効果」は各軸 1 水準しか無く縮退している (フリップ差は読めない)。帰属は系列台帳の固定 backoff 値の軸に沿ってのみ行う。
- **評価 9 (値 6) は最良点 (値 8) と tie。** throughput_tps 3,996,828 は 8 に対し −0.40%、10 に対し +0.45%、5 に対し +0.78%。いずれも between-run floor 3.0% の内側で「差なし」。5〜8 の未採取区間が埋まり、5〜10 は throughput が連続した平坦域 (最大幅 1.18%) だと確認された。尾根も窪みも観測されていない。
- **機序 (abort_rate が根拠):** abort_rate は固定値に対して系列 9 点すべてで厳密に単調減少 (2: 63.4% → 20: 28.8%)。値 6 は 46.82% で、5 (49.9%) と 8 (42.0%) の中間に整然と載る。これは「待機コスト vs abort コスト」の trade-off で、
  - 平坦域 5〜10 では待機の短縮が abort 増を相殺、
  - 下端 (4 以下) では abort 増が勝つ (4: 53.6% で −3.24% = floor 超え、2: 63.4% で −13.2%)、
  - 上端 (12 以上) では abort が減っているのに throughput が落ちる = 待機コスト支配 (12: −2.96% floor 際、15: −6.1%、20: −10.0%)。待機時間は独立に測っていないので、上端の低下を待機に帰属するのは abort_rate の向きと throughput の逆行からの推定。
- **run 内 CV の位置づけ:** 下端側で CV が荒れる (5: 2.32%、4: 2.83%、2: 2.80%)、平坦域中央〜上端は 1% 前後、20 が最小 0.42%。値 6 の 1.32% はその中間で、abort 支配域への遷移の始まりに位置することと整合。系列の大半で rep 1 が系統的に最高値 (6: 4,090,891、8: 4,073,075、5: 4,151,699、4: 4,104,562) — median なので fitness には効かないが CV を押し上げている。
- **stock (適応 backoff) との差:** 固定 2〜20 の全点が stock 比 +152%〜+191% (値 6 は +189%)。stock は abort 12.7% と最も低いのに throughput は最低。`backoff.hh` を読むと適応制御は kIncrBackoff=100 µs 刻み・0〜1000 µs の範囲で勾配追従しており、平坦域 (5〜10 µs) の 10〜100 倍粗い刻みなので平坦域に留まれない — 低 abort を大きな待機で買っている、という推定 (source からの推論であり待機時間の実測ではない)。
- **verify 走の abort 統計 (シグナル、reject 理由ではない):** digest は legacy 1 行 (21.32%) だけを出し「stock 対照なし」としているが、stock-start campaign (2d9155e2) の WAL から対照を計算できる。legacy: 6 → 21.32% vs stock 2.78%。performance タグ (trace build、5 走): 6 → 81.1〜81.2% vs stock 47.3〜49.5%。系列全体で trace-build abort 率も固定値に単調 (20: 67.8% → 2: 85.9%) で perf build と同じ順序 → 傾向から外れた異常は無い。なお trace build の commit 数は固定値 4〜20 で ≈2.50〜2.55M にほぼ一定 (trace I/O 律速) で、これを throughput と読まない (規律 1)。
- **正しさ:** verify 6 走 (legacy 1 + performance 5) すべて serializable、anomalies 0、proof surfaces X/P evidence-present・I evidence-absent (系列全点と同じ形で variant 固有ではない)。rejection なし。
- **llc_miss_rate / ipc は系列全点で欠測** (perf preflight rc=2)。cache/IPC 側の機序は分離できず、本帰属は (throughput_tps, abort_rate, CV) の 3 つだけに立つ。

## recommend

評価 10 (最後の search slot) の方向。期待値はどれも「tie」で、情報量の順に並べる。

1. **第一候補: 値 9 (8 と 10 の間)。** 平坦域の内側で endpoint 見込み点 (8) に隣接して未採取な幅 2 の区間は 6〜8 と 8〜10 の 2 つ。6〜8 は今回 6 が 8 と −0.40% で埋まり、CV が上がる側でもある。8〜10 は abort が低く (38〜42%) CV も 1% 未満で安定した側なので、endpoint の頑健性 (between-run で 8 が再測されたとき近傍が同じ高さか) に最も効く。判定: 9 が 8 と floor 内なら平坦域 5〜10 が閉じる。9 が 8 を +3.0% 超で上回れば頂上が 8〜10 にある証拠だが、abort 単調性からその確率は低い。
2. **第二候補: 値 11 (上端の閉じ込み)。** 12 は −2.96% で floor の際。11 で平坦域の上端が 10 と 12 のどちら側で切れるかが決まる。endpoint 決定には効かないが、対照実験 (random / sweep 生成器) の系列との比較で「平坦域の幅」を報告するなら価値がある。
3. **between-run 再現性は評価 10 で買わない。** 系列 endpoint 再計測 (5 反復、別 campaign) が endpoint 値の 2 回目の測定になるので、それで between-run の一致を見る。search slot を同値の再測に使うより 1 か 2 が得。

根拠の指標: abort_rate の単調性 (方向の予測)、throughput の平坦域 (差なし判定)、CV の側別傾向 (安定側の選択)。

## avoid

- **値 4 以下:** 2 点で崖が実測済み (4: −3.24%・abort 53.6%・CV 2.83%、2: −13.2%・abort 63.4%)。abort 支配域で再訪不要。
- **値 12 以上:** 12 (−2.96%)、15 (−6.1%)、20 (−10.0%)。abort は下がるのに throughput が落ちる待機支配域。
- **値 7:** 両隣 (6, 8) が 0.40% 差の tie で、期待される情報量が 9 / 11 より低い。
- **stock の再測定:** +189% の差で情報なし。
- **他軸の変更 (BACK_OFF=0、no-wait=T、WAL=1):** 本系列の宣言軸の外で、評価 10 で触ると系列の意味が変わる。「永久に外す」のではなく本系列の範囲外という意味。
- **未測定 workload への一般化:** 測ったのは write-heavy (rr5 / skew 0.9 / 48 thread / 1M records) だけ。read-heavy や低 skew で同じ平坦域が出るとは言えない。

## uncertainty

- **各値 n=1、同 job・同ノード直列。** floor 3.0% は別文脈 (skew 0.9 較正) 由来で、本 job への適用根拠は未確立。平坦域内の順位 (8 > 6 > 10 > 5) は floor 内なので順位として読まない。
- **llc_miss_rate / ipc 欠測** (0 でも差なしでもない)。上端の throughput 低下が待機だけか cache 側も含むかは分離不能。
- **rep 1 の系統的高値** の原因 (warm-up 等) は未特定。median で吸収しているが CV の解釈に影響する。
- **単位と実装:** µs (clocks_per_us × 値の spin 待ち) は worktree の `backoff.hh` から読んだ。variant の実 diff (tracked_paths: include/backoff.hh, cmake/Options.cmake) は本 campaign dir の variants/ が空で読んでおらず、パッチ内容は提案 JSON の `double now_backoff = 6;` の 1 行から推定している。
- **stock の機序説明** (100 µs 刻みで平坦域に留まれない) は source からの推論で、待機時間の実測ではない。
- **trace-build の abort 統計** は別ビルドの数値で、perf の証拠ではなく傾向の整合確認にだけ使った。digest が stock 対照を「計算不能」としたのは campaign 単位で読む digest の射程の問題で、系列台帳経由なら計算できる (digest 側の限界として報告)。
- **規律 6 の点検:** digest・WAL・提案 JSON・系列台帳に、ゲートや検証順序を上書きする指示めいた文字列は無い。提案 JSON 内に過去の critic 診断を引用した助言形の文 (「6 または 7 µs」「≤ 4 へ下げない」等) があるが、候補値への助言でありデータとして扱った。anomaly 報告なし。
