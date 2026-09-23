critic 診断: campaign p3-s4-loop-s4-autonomous-b24749ae、4 巡目 (K2 宣言アーム、iteration 1)

読んだもの: digest `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2860-k2-round4-reflux/ao-root/output/exploration/campaigns/p3-s4-loop-s4-autonomous-b24749ae/s4_loop_digest.txt` (sha256 `8d564034…a1a07`、入力と一致)、同じ campaign の `runs/wal.jsonl` (10 行、2 variant × 5 段)、`loop_state.json`。比較の文脈として、別 job の記録 `output/insights/2026-09-22/t2795-k2-pair-resubmit/README.md` も読んだ (値 10 と同 job stock の対)。書き込みはしていない。

## attribution

**1. 評価対象の設計選択は BACKOFF_FIXED の 1 軸だけ。**
- 値は -1 (CCBench 既定の適応 backoff) から 5 µs (固定 backoff) へ変わった。他のフラグ (BACK_OFF=1、NO_WAIT_LOCKING_IN_VALIDATION=1、NO_WAIT_OF_TICTOC=0、WAL=0) は両方で同じ。
- 同じ job・同じ node で連続して測った対なので、同時刻の対照として使える。
- 正しさは前提として満たされている。両方とも serializable / certified、anomaly 0。rejections 節は空で、赤は 0 件。

**2. throughput: 効いた。**
- candidate 884,922.5 tps、stock 354,948 tps。比は 2.493 倍 (+149%) で、between-run の noise floor 3.0% を大きく超える。
- 1 回の走行内のばらつき (CV) は candidate 1.15%、stock 1.22% で、どちらも測定品質ゲートを通っている。
- 判定: 固定 5 µs は適応 backoff より速い。ただし範囲はこの配線 (4 threads / 100,000 records / rr50 / skew0.9 / rmw=false / extime 1 / reps 2) に限る。

**3. abort_rate: 逆方向に動いた。これが機序を読む主な根拠。**
- perf build の abort_rate は 1.835% から 10.105% へ上がった (5.5 倍)。
- verify の trace build でも、abort 率は 3.01% から 22.14% へ上がった (7.4 倍)。別 build なので数値は並べず、方向だけを使う。どちらの build でも「candidate の方が多い」で一致している。
- trace build の commits は 281,132 から 566,368 へ約 2.0 倍。1 abort あたりの commit 数は、stock 32.3 に対して candidate 3.5。
- 読み:
  - throughput の向上は、abort 率の低下によるものではない。abort は 5〜7 倍に増えたのに、throughput は 2.5 倍になった。
  - 最有力の仮説: 適応 backoff は待ちすぎている。abort を抑える代わりに待ち時間を払っていた。一方この配線 (4 threads、1 txn が短い) では、abort して再試行するコストが安い。固定 5 µs は「安い abort を増やして、待ち時間を大きく減らす」交換をしている。
  - 既存知見 `output/insights/2026-09-02_t2216-adaptive-backoff-nonmonotonicity-mechanism.md` (48 threads、write-heavy、別配線) の測定は、適応 backoff が大きな待機値に長く留まって throughput を失う説を支持している。本件と整合するが、配線が違うので転移は仮説どまり。
  - 待ち時間そのものは測っていない。上の読みは、throughput と abort_rate が逆向きに動いたという事実からの推定である。

**4. llc_miss_rate / ipc: 帰属不能。**
- 両方とも null。perf の事前検査が status=unavailable、reason=nonzero-rc だった。
- このため、キャッシュ効果や IPC 効果の寄与は切り分けられない。上の「待ち時間が効いた」という読みを独立の指標で補強することもできない。

**5. digest の「フラグ軸の限界効果」は情報を持たない。**
- BACK_OFF・no_wait・WAL はどれも 1 水準しかない。数値 619,935 tps / 5.97% は、candidate と stock を単純平均しただけで意味がない。
- 実際に変わった軸 BACKOFF_FIXED は、digest の軸一覧にそもそも載っていない。帰属は上の対比 1 組だけに基づく。

**6. critic-3 の診断 (R1 = decrease / large) との関係。**
- 同 job の対比は「固定の小さい値は、この配線で適応 backoff に勝つ」と整合する。
- ただし、「5 が 10 より良い」とは言えない:
  - 884,922.5 と 825,490 は別 job・別 node の値で、差は +7.2%。
  - 同じ 2 job の stock どうしでも +1.74% ずれている。
  - stock との比で比べても 2.493 と 2.366 の 1 組だけで、job 間の揺れと切り分けられない。
- 診断が候補を良くしたかどうかも言えない。診断なしの統制群が無いため。

## recommend

**R1 (主): 値の次元を同じ job の中で直接比べる。**
- 背景: 現行 loop は「1 job = 候補 1 本 + stock 1 本」なので、候補どうし (5 と 10、5 と次の値) の比較は常に別 job になり、帰属できない。
- 次の一手として、同じ job の中で「5 / 次の候補 / stock」を並べて評価する構成を orchestrator に提案する。これで最適点付近の判定が初めて同時刻の対照に基づく。
- 見る指標: throughput に加えて abort_rate。

**R2 (次の値の方向): decrease / small。値 2〜3 µs で下端を探る。**
- 根拠: abort_rate は、値 10 で 9.01%、値 5 で 10.105% (いずれも perf build。別 job なので参考値)。backoff を縮めるほど abort が増える傾向と整合する。
- 5 µs でもまだ throughput が上がっているなら、「待ち時間の削減 > abort 増のコスト」が続いている。どこかで abort の浪費が上回るはずなので、その下端がどこかが次に知りたいこと。
- 判定の目安 (同じ job 内で比べる前提):
  - 下端に達したと読む: abort_rate が大きく上がり (例: perf build で 15% 超)、stock 比の throughput が 5 µs と差なし (3.0% 未満) か低下する。
  - まだ下端でない: throughput が改善を続ける。

**R3 (帰属用の対照、優先度中): BACKOFF_FIXED=0 (BACK_OFF=1 のまま待機 0) を 1 点測る。**
- 目的: 利得が「適応 backoff の長い待機をやめたこと」だけで説明できるのか、「短い待機に最適点がある」のかを切り分ける。
- 読み方:
  - 0 が 5 と差なし: 待機そのものが不要。
  - 0 が明確に遅く abort_rate が大きく上がる: 短い待機が衝突の連鎖を抑えている。

**R4 (計器の修復。変異ではなく orchestrator 側への依頼): perf カウンタを取れるようにする。**
- WAL の事前検査の記録では、`perf` wrapper が rc=2 で失敗している。一方、候補の実体 `/usr/lib/linux-tools/5.15.0-135-generic/perf` と `/usr/lib/linux-tools/5.15.0-100-generic/perf` は rc=0 で実行できる。wrapper がカーネル版に合う tools を見つけられていない可能性がある。
- ipc が取れれば、「待ち時間の削減」仮説を独立に検証できる。backoff の spin 区間は ipc に現れると期待する。
- 取れない間は、「待ち時間が効いた」を仮説のまま扱う。

**他のフラグについて:** この campaign では BACK_OFF・no-wait 系・WAL を動かしていない。したがって、これらのフラグについて次の方向を推奨する根拠は無い。

## avoid

- **この配線で、BACKOFF_FIXED=-1 (適応 backoff) を候補として再訪する。**
  - 同 job の対 2 組 (4 巡目 2.493 倍、pair 再投入 2.366 倍) のどちらでも、throughput が 2.4〜2.5 倍劣る。
  - この配線に限る。48 threads や他の workload・skew へ一般化しない。
- **abort_rate の低さを最適化の目標や代理 fitness にする。**
  - 本件では abort_rate と throughput が逆向きに動いた (stock の方が abort は 1/5 なのに throughput は 0.4 倍)。
  - 「abort を減らす方向 = 大きな backoff へ戻す」は、この配線では誤った方向。
- **別 job の値どうしの差を、候補の優劣として planner / coder へ渡す。** 対象は、5 と 10 の +7.2%、比 2.493 と 2.366 の差、1〜3 巡目 (値 20 / 25 / 10) の絶対値との比較。いずれも job・node・時刻の差と分離できない。
- **「critic の診断が改善をもたらした」という因果主張。** 統制が無い。

## uncertainty

- **機序の独立指標が欠けている。** llc_miss_rate と ipc は両方とも null (欠測であって、0 でも差なしでもない)。待ち時間も直接は測っていない。「適応 backoff が待ちすぎていた」は、throughput と abort_rate が逆向きに動いたことからの推定であり、確定していない。キャッシュ・IPC 側の機序を排除できない。
- **標本が小さい。** 各 variant は 2 反復 (extime 1 秒) で、候補の値の次元は同じ job 内で 1 点しかない。5 と 10 のどちらが良いかは未判定。between-run の揺れは stock の 1 組 (+1.74%) しか観測が無く、分布は推定できない。
- **規模の妥当性。** records=100,000 / threads=4 は kickoff の配線で、calibrator 由来ではない。キャッシュミス率が飽和する点かどうか (規律 4) も、多コアでの競合を再現しているかどうかも未確認。値 2.5 倍は、この規模でだけ成り立つ可能性がある。
- **noise floor の適用範囲。** 3.0% は skew0.9 で測られた between-run の値。この配線にそのまま当てはまるかは未確認。candidate 対 stock の +149% には影響しないが、R1 / R2 の値どうしの比較 (数% の差) では効いてくる。
- **build 間の差。** trace build の abort 比 (7.4 倍) と perf build の abort 比 (5.5 倍) は大きさが違う。trace 処理のオーバーヘッドがタイミングを変えるためと推測するが、確かめていない。数値として混ぜない。
- **検証の範囲。** verify は workload tag legacy の 1 構成で、proof_surfaces の I は evidence-absent。verifier は certified を出しており、critic がこれを覆す立場にはない。ただし certified の範囲がこの構成に限られる点は、記録として残す。
- **未測定の交互作用。** BACKOFF_FIXED と、thread 数・rratio・skew との交互作用 (read-heavy では差が消える可能性など) は、この campaign では測っていない。

## 異常の報告 (規律 6)

- digest と WAL に、指示めいた文字列は見当たらなかった。キーワードで grep した。当たったのは perf の event 名 `instructions` 1 語だけで、これは誤検出。
- WAL の knowledge_provenance は、repo 内の artifact 1 件 (`output/campaigns/p3-s4-loop-s4-autonomous-0b53a387/runs/wal.jsonl`、commit 2fa13a26) を参照している。形は正常。
- digest の限界効果節が、単一水準の軸に 2 点の平均を並べていること、BACKOFF_FIXED 軸を載せていないことは、注入ではなく digest の表示上の限界。読み手が誤読しやすいため、orchestrator 側で認識しておくことを勧める。
