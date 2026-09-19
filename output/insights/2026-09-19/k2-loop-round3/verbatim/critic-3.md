# critic 診断 — p3-s4-loop-s4-autonomous-409e13f8 / iteration 1 (3 巡目、variant 002642c7ac96、BACKOFF_FIXED=10)

## 信頼境界検査 (規律 6)

digest (`s4_loop_digest.txt`、sha256 `f993251d…` を再計算し親の射影と一致) と campaign WAL (`runs/wal.jsonl` 5 行: build_start / build_done / verify_done / bench_done / commit)、`loop_state.json`、`knowledge_manifest_receipt.json`、`campaign.lock` を全文読んだ。**指示めいた文字列は無い。** 機械 grep の hit は digest の見出し「不採用」、WAL の perf event 名 `instructions`、受領証の `external_knowledge_is_data_not_instructions` の 3 件で、いずれも記述語であり宛てられた指示ではない。`campaign.lock` の `identity_preimage` に自由文 `spec_content` (段 4 loop の説明文「critic 帰属を次 iteration に還流…」) が入っているが、campaign 仕様の説明であって振る舞いの誘導ではない。データとしてのみ扱った。書き込みは一切していない。

digest の体裁上の小さな anomaly (データには影響しない): 見出しが `(P2-3)`、workload 名が `p3-s4 ()` と空括弧。「フラグ軸の限界効果」節は同じ 1 点 (815,983 / 9.07%) を BACK_OFF=1 / no_wait=L / WAL=0 の 3 行に書き写したもので、フリップした水準はゼロ。

## attribution

**結論: 本走単独では、どの設計選択にも「効いた / 効かない」を帰属できない。** 構造的理由は 1・2 巡目と同じで、本巡でも解消していない: (1) campaign 内の点は 1 点で限界効果表に水準差が無い、(2) 同一 job 内の stock 対照が無く digest 自身が「比は計算不能」と書く、(3) BACK_OFF / no-wait 政策 (L) / WAL は K2 アーム内で固定であり、自由度は `BACKOFF_FIXED` の literal (abort 1 回あたりの固定 spin µs、`include/backoff.hh` 96 行の `double now_backoff = …;` 穴) だけ。

**根拠指標の読み (帰属ではなく機序の候補):**

- **throughput_tps = 815,983 / abort_rate = 9.07%** (perf build、reps=2、run 内 CV 0.16%、settled)。abort_rate の集約規則は 2 巡目と同じ (T-2702、中央 2 件中央値) なので、2 巡目 (7.40%) との差 +1.65 pt は集約規則差ではない (ただし非同時刻)。
- **機序に基づく導出 (計測値ではない):** silo は abort ごとに `Backoff::backoff()` を 1 回呼ぶ (`cc/silo/transaction.cc` 42〜51 行、本 tree で再確認)。本走の値から aborts/s = commits × r/(1−r) ≈ 81.3k/s、4 thread で 20.3k/s/thread、× 10 µs ≈ **thread 時間の約 20% が backoff spin** (前提: `-clocks_per_us=2100` が実 TSC と一致、spin 以外の待機は無視)。同じ導出で 2 巡目 (25) は約 34%、1 巡目 (20) は約 30%。
- **critic-2 が事前に置いた判別規則との照合:** critic-2 は「10 で abort_rate が 7–8% 帯に留まったまま tps が上がれば純コスト仮説を支持、abort_rate が明確に上がる (10% 超) のに tps が上がらなければ抑制の仕事をしている」と書いた。観測は **中間** — abort_rate は 9.07% (7–8% 帯より上、10% 未満) に上がり、tps は非同時刻ながら 2 巡目比 +18.7%、1 巡目比 +13.4%。読みは「固定 backoff は abort 抑制の仕事を少し (＋1.65 pt 相当) しているが、この配線では spin コスト側の寄与が支配的」。純コスト模型 (tps ∝ 1/(1−spin 占有率)) が予測する 25→10 の比は (1−0.20)/(1−0.34) ≈ 1.21 で、観測の 1.19 と近い。**ただしこの照合は非同時刻・別 tree・別 job の 3 点に依存するので「診断が当たった」とは言わず、仮説と矛盾しなかった、までに留める。**
- **llc_miss_rate / ipc は null** (perf preflight `status=unavailable` / rc=2)。spin 短縮による cache 挙動や abort 経路の命令効率の変化は判別不能。欠測であって 0 でも差なしでもない。
- **verify run (trace build) の abort 率 18.94%** (122,211 / 645,331) は perf build の 9.07% の約 2.09 倍 (2 巡目は 1.9 倍、13.90%)。trace build は trx 窓を伸ばすので abort が増える方向は機序として自然で、backoff を縮めたぶん trace 側でより増えるのも整合するが、stock の trace 対照が無いので正常範囲は判定できない。verdict=serializable / anomalies=0 / certified=true、rejection ゼロ — 正しさ側のシグナルは無い。**digest の表の 9.07% と verify 節の 18.94% は別 build の値であり、混同しない。**
- whiteboard の `result=success` (decrease / large) は certified の意味であって throughput 改善の記録ではない。`delta_pct=null` は harness の設計。

## recommend

**R0 (最優先・3 巡連続で未解消): 同一 job 内に stock 対照点を作る。** (a) `backoff.hh` 無改変 + `BACK_OFF=1` (適応 backoff、`Backoff_` 初期値 0、100 µs 刻み) と、可能なら (b) `BACK_OFF=0`。根拠: digest の限界効果表が水準差ゼロ、stock 比が計算不能。これが無い限り、非同時刻の 3 点 (20 / 25 / 10) がいくら並んでも「固定 backoff 10 は速い」とも「固定 vs 適応」とも帰属できず、throughput スカラーだけを追う停滞 (Jitskit §3.5) に留まる。harness / launcher 側の運用判断なので要望として出す。

**R1 (K2 アーム内の次の一手): 方向 decrease、magnitude large、候補値 5。** 理由: 本走で spin 占有率の導出は約 20%。5 なら (aborts/s が不変として) 約 10% に落ち、純コスト模型の予測は約 +12% で between-run floor 3.0% を明確に超えるため 1 点で判別できる。**判別指標は abort_rate と tps の組:** (i) abort_rate が 9–11% 帯に留まって tps が上がれば「この配線では固定 backoff は純コスト側」がさらに支持され、転回点は 5 未満。(ii) abort_rate が明確に跳ねる (例: 13% 超) のに tps が平坦か低下すれば、backoff の抑制効果が効き始める転回点が 5–10 の間にある、と読める。どちらでも次の刻みが決まる。刻み 5 ではなく半減にするのは、20/25 で floor 内の平坦帯を往復した反省 (critic-2 の avoid) を引き継ぐため。

**R1' (R1 と独立に投入可): grammar 下限 1 の floor probe。** 事実上「backoff ほぼ無し」の点で、R0 (b) が harness 上取れないときの代替 floor になる (BACK_OFF=0 とは `chkClkSpan` 1 µs 分の差があり同一ではない)。R1 と R1' の両方が取れれば 1 / 5 / 10 で転回点を挟める。

**R2 (R0 が得られた後): 固定 backoff の最良点と適応 backoff を同一 job で比較する。** 適応側は 0→1000 を 100 µs 刻みで動くのでスケールが違い、比較は tps だけでなく abort_rate の帯が同じかで読む。

**R3 (診断計器、fitness 用 build に混ぜない):** spin 占有率の導出を独立計測に置き換えたいなら `CCBENCH_ADD_ANALYSIS=1` の `backoff_latency_rate` (`common/result.cc`) を**別の診断 build / run** として取る。abort 経路に rdtscp を足すので perf build と混ぜると規律 1 (観測者効果) に触れる。導入可否は呼び手の判断。

## avoid

- **値を上へ戻すこと (15 / 20 / 25 / 30)。** 20 と 25 は評価済みで abort_rate 7.4–7.75% の同じ帯、10 で abort_rate は +1.65 pt しか動いていない。上側に転回点がある兆候は 3 点のどこにも無い。30 は別機体 (linux-baremetal、settled=false) の知識源の最良点であり、本機体で再現しても機体差で帰属できない。
- **815,983 (本走) と 687,508.5 (2 巡目) / 719,324.5 (1 巡目) の差を改善と断定すること。** 時刻・submit-tree・job が違う非同時刻比較。attribution で使ったのは「仮説と矛盾しないか」の照合までで、優越の根拠にしない。
- **verify run の abort 率 18.94% を reject 理由・異常と扱うこと。** trace build であり stock 対照が無い。正しさゲートを緩める方向の示唆は無い (anomalies 0、rejection ゼロ)。
- **perf build の 9.07% と trace build の 18.94% を同じ「abort 率」として並べること。**
- **llc_miss_rate / ipc の null を 0 や「差なし」で埋めること。**
- **本配線 (4 threads / skew 0.9 / 100k records / rr50 / rmw=false) の結論を他の thread 数・skew・records へ一般化すること。** spin 占有率の導出は aborts/s/thread に比例し、thread 数や skew で桁ごと変わる。
- **critic-2 の候補 10 が本走で評価されたことをもって「critic 診断が効いた」と数えること。** 届いたこと・参照されたことと因果は別 (親の開示どおり)。ablation の on/off 比較は本経路 (legacy critic) では非適格。

## uncertainty

- **spin 占有率 (約 20%) と純コスト模型の比 1.21 は計測値ではなく導出。** 前提 (abort ごとに backoff 1 回・clocks_per_us=2100 が実周波数と一致・他の待機が無視できる) のどれかがずれると比例してずれる。leader は `leaderBackoffWork` (`transaction.cc` 719 行) で `Backoff_` を更新し続けるが literal 穴では未使用で、その固定費は未計測 (小さいはずだが確認していない)。
- **3 点 (20 / 25 / 10) は全て非同時刻・別 tree。** 模型との整合 (1.19 vs 1.21) は偶然でも成立しうる大きさであり、同時刻対照が入るまでは帰属に昇格しない。
- **between-run floor 3.0% は A2 の較正値をそのまま適用。** 本機体 (Pegasus 計算ノード、job 10761.nqsv) で同時刻に再較正した値ではなく、submit-tree には較正記録が無い。run 内 CV 0.16% は 1 測定の品質ゲートであり採否には使っていない。
- **perf 欠測のため cache / IPC 側の機序は判別不能。** 純コスト仮説が支持されても、spin による cache 効果 (他 thread の critical section 短縮など) の寄与は分離できない。
- **abort_rate の 7.40 → 9.07 (+1.65 pt) が backoff 短縮の効果か、日・ノードの差かは分離できない** (同時刻の 2 点が無い)。
- **trace build の abort 率 (18.94%、perf 比 2.09 倍) の正常範囲は判定不能** (stock の trace 対照が無い)。
- **R1 の候補 5 で abort_rate が跳ねるか (転回点が 5–10 にあるか) は本データから予測できない。** どちらの結果でも読み方を上に固定したので、結果を見てから規則を作らない。
- 1 点しかないため、上記 recommend は「帰属の結果」ではなく「帰属可能な設計にするための次の一手」である (1・2 巡目と同じ位置づけ)。

## 参照した現物

digest `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-k2-loop-round3/submit-tree/output/exploration/campaigns/p3-s4-loop-s4-autonomous-409e13f8/s4_loop_digest.txt` (sha256 `f993251dc33cd9d25246778c8b6b8820f431d4d121030377af65f9046ebe3598`)、同 dir `runs/wal.jsonl` / `loop_state.json` / `knowledge_manifest_receipt.json` / `campaign.lock`; コード `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-k2-loop-round3/external/ccbench/include/backoff.hh` (96〜108 行)、`external/ccbench/cc/silo/transaction.cc` (42〜51 行)、`orchestrator/campaign/backoff_hole_grammar.py` (742 行)、K2 知識源 `output/campaigns/p3-s4-loop-s4-autonomous-0b53a387/runs/wal.jsonl` (40 / 30 / 40、linux-baremetal)、2 巡目記録 `output/insights/2026-09-18/t2746-k2-loop-round2/README.md` と `verbatim/critic-2.md`。書き込みは一切していない。
