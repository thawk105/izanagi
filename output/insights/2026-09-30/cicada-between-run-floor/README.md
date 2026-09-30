# Cicada の throughput の時間窓間ばらつきを、関門の対象外の診断経路で日内 6 窓にわたって測った — Y5・Y50・Y95 の主 GC で CV 0.69%・1.05%・0.70%、いずれも D19 の下限 3% より小さい (2026-09-30)

- 依頼: VHash 論文の並行 wave md_35 (台帳 [T-2915])。共通指示は `/work/1/SFC/tanab/tmp/vhash-2026-09-29/common.txt`。
- 計測データ: `output/env/pegasus/vhash-cicada-baseline-tuning/cfloor-w<1..6>-y<5|50|95>-j2-0/` (各 job の `job-manifest.json` と `runs.jsonl`)。生ログ (build ログ・run の stdout/stderr) は repo 外の `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-cicada-between-run-floor/raw-archive/`。
- 集計: `window-cv.json` (本 dir、sha256 `d9bfc20b12b245e28a82f380c88732d35a09ed6832cd041b4283489f4e36cad2`)。
- **この値は floor artifact ではなく、D1373 の関門を通った floor でもない** (§2)。

## 1. 依頼と結論

依頼: 評価計画の草稿 (`docs/vhash-evaluation-preregistration-draft.md` §8.3・§11 の P2) は、Cicada の throughput の差を判定する閾値を δ_T = ln(1 + max(0.030, f_T)) とし、f_T に D145 の意味の between-run floor (時間窓 cluster を複数持ち、動作点署名ごと) を置く。既存の floor 生成は D1373 の関門で Cicada を拒否する (D2291)。Cicada に floor を出す道を並べて決め、取れる道なら比較相手の最良設定と評価計画の主要な動作点で実測する。

結論:

1. **道は「関門の対象外の別手続き」を採った (§2)。** 関門を通す道は CCBench・pin・patches の変更が要り本 wave の所有外で、関門の受理を広げる案は緩和になるので採らない。md_11 の診断 driver (`tools/vhash_cicada_tuning/driver.py`) を無改変で使い、時間窓を 6 つ持つ計測をした。
2. **得た量の名前は「Cicada A の時間窓間 session-median CV (日内 6 窓・診断経路)」。** floor artifact・izanagi の compare・採否には接続せず、評価計画 §8.3 の f_T (D145 の意味の floor) としても代入しない。δ_T は D19 の下限で計算し、本値はその根拠として併記する (§2)。δ_T を上げる向きも、同等・悪化・A/A 判定・job 間の停止条件を通じて採否を動かしうるので安全側ではない (§2)。
3. **比較相手 A (md_11 の最良設定、md_20 で巡回 0・上限 indeterminate) の主 GC で、窓間 CV は Y5 0.69%・Y50 1.05%・Y95 0.70%** (§4)。3 動作点とも 3% より小さい。**δ_T は本値に関係なく D19 の下限で計算して ln 1.03** で (本値は代入しない、§2)、本値はその下限を使う判断の参考の根拠になる。窓中央値の最大/最小 − 1 は 1.89%・2.69%・2.13%。
4. **A の別 GC の腕 (A_alt) も 1.33%・1.06%・0.80% で 3% より小さい。** ただし Y5 の A_alt (GC 10 µs) だけ最大/最小 − 1 が 3.83% と 3% を超えた (§4)。
5. **同じ job に置いた control (md_11 の control) の窓間 CV は、GC 10 µs で 0.38〜0.82%、GC 100 µs を含めると 0.30〜0.96%。** md_11 が 1 投入束で測った control (GC 10 µs) の CV (0.43〜0.81%) と同じ程度で、日内の 6 窓に広げても大きくならなかった (§5)。
6. **日を跨ぐ変動と cold boot は測っていない。** 本値が 3% より小さいことは、真の (日を跨ぐ) floor が 3% より小さいことを示さない。R・L-w・100 操作型の cell も測っていない。評価計画 §8.3 の二択 (下限だけで発効するか、floor を待つか) は、ユーザーの判断として残る (§6)。

## 2. Cicada に floor を出す道の比較

| 道 | 中身 | この wave での可否 | 理由 |
|---|---|---|---|
| 1. 関門を通す | `orchestrator/campaign/between_run_floor.py` の関門 (D1373、`_protocol_source_has_trace_hook_evidence_only`) は、protocol の `cc/<protocol>/CMakeLists.txt` の SOURCES に列挙された同じ source に `trace.hh` の include・`#if TRACE`・`izanagi_trace::` 呼出しの 3 つが (コメントと `#if 0` を除いて) そろうときだけ floor の生成を許す。Cicada の hook は `patches/instr-cicada-trace*.patch` にしか無く、pin `6810666` の source には無い。さらに同 file の `BASELINES` に cicada が無く、引数解析で先に拒否される | 不可 (所有外) | 通すには CCBench の Cicada に hook を入れて pin を進める必要がある (D2083 項 5 と同じ条件)。CCBench・pin・patches は本 wave の所有外。関門の受理を「patch 適用後の source」へ広げる案は、現行述語の契約 (checkout の compiled SOURCES を読む) を変えて受理集合を広げるので採らない。patch 後の source を厳密に束縛する設計には別裁定の余地が残る (段 3 相談 A8) |
| 2. 関門の対象外の別手続き | md_11 の診断 driver (無改変) で、時間窓を複数持つ計測をする。量は estimand で名乗り、floor artifact (`output/env/*/calibration/between_run_noise_*`)・compare・採否へは接続しない | **採った** | D2291 項 1 の先例 (関門の射程は floor artifact の生成で、診断値として一次資料に書くのは迂回でない) と同じ経路。D145 項 2 (estimand を名乗り compare へ配線しない) を守る |
| 3. D19 の下限 0.030 だけを使う | 計測なし。δ_T = ln 1.03 | 道 2 と併存 | 計測しないと、Cicada の窓間の揺れが 3% を超えるかどうかを知らないまま下限を使うことになる |

**得た値の位置づけ (段 4 裁定、段 6 と焦点再レビューで訂正):** 評価計画 §8.3 は f_T を D145 の意味の floor に限っており、本値はそれに当たらない。したがって本値を f_T として代入するのではなく、**δ_T は D19 の下限で計算し (δ_T = ln 1.03)、本値は「Cicada の日内の窓間 CV はそれより小さかった」という根拠として併記する**。§8.3 の二択 (下限だけで発効 / floor を待つ) はそのまま残る。

δ_T を大きくする向きも安全側ではない。δ_T は評価計画の次の 4 箇所で効き、上げるとそれぞれ次のように変わる。

| δ_T が効く箇所 | δ_T を上げたときの変化 |
|---|---|
| 「改善」L > δ (§5.1) | 出にくくなる |
| 「同等」−δ < L かつ U < δ、「悪化」U < −δ (§5.1) | 同等は通りやすく、悪化は出にくくなる (例: [L, U] = [−0.035, 0.035] は δ = ln 1.03 で判定不能、ln 1.05 で同等)。§5.2 の「Cicada の最良設定に対して」は「改善または同等」を許す |
| A/A 判定 (§8.1: A 対 A′ が「改善」「悪化」なら、その cell の全判定を判定不能にする) | A/A で止まりにくくなり、止まっていた cell の主要比較が「改善」を主張できるようになる |
| job 間の停止条件 (§8.1: 2 job の中央値の差が 2δ を超えたら判定不能) | 止まりにくくなる |

つまり、D19 の下限を超える値を δ_T に入れると、採否は両方向に動きうる。そのような値が将来出たときは、これら 4 箇所への影響を含めて発効の wave が別に裁定する。本値は δ_T の計算に入れない (上の裁定) ので、値の大小に関係なく δ_T は下限のまま、どの判定も変わらない。今回の値がすべて 0.030 以下だったことは、下限を使う判断の参考の根拠にとどまる。Cicada の各構成の正しさは、評価計画 §7 の門が f_T と無関係に別に要求する。

## 3. 計測の設計 (結果を見る前に段 4 で固定)

- **時間窓:** 1 窓 = 1 投入束。予定 6 窓。窓 k+1 の投入は、窓 k の投入から 60 分以上後、かつ窓 k の 3 job がすべて終わった後。60 分は md_11 の 4 投入束の全幅 (約 1 時間、「実質 1 窓」と数えた) 以上に窓を離すための運用値で、窓の独立性や日を跨ぐ変動の捕捉を証明する値ではない (D1534 は最小間隔を独立性の規則として退けている)。時刻帯の block ではなく、各窓での再現も条件にしない (評価計画 §8.1 の「時間帯の block 分けはしない」とは別の話)。
- **各窓:** 3 job (Y5 = rr5、Y50 = rr50、Y95 = rr95) を 3 本の計測木から同時に計算ノードへ投入 (1 job 1 node)。各 job は driver の `make-spec --stage j2 --k 1 --gc-grid 10 100 --reps 5 --build-parallelism 2` が作る spec に、窓を表す `submission_cluster` (`cfloor-w<k>`) を足したもの。中身は A (`BACK_OFF=0, INLINE_VERSION_OPT=1, INLINE_VERSION_PROMOTION=0, REUSE_VERSION=1, WRITE_LATEST_ONLY=0`) と control (md_11 の control、`BACK_OFF=1, INLINE_VERSION_OPT=0, INLINE_VERSION_PROMOTION=0, REUSE_VERSION=1, WRITE_LATEST_ONLY=0`) を GC 10・100 µs で各 5 反復、反復ごとに順番を並べ替えた 20 run。seed は 10 × 窓番号 + workload 番号。1,000,000 件・48 thread・extime 3 秒・skew 0.9・rmw 0。build は `-DCCBENCH_TRACE=0 -DCCBENCH_ADD_ANALYSIS=0` (検査用 trace・計器なし、絶対規律 1)。stage 名 "j2" は driver の閉じた集合の継承で、md_11 の J2 とは別の計測である。
- **主量:** 動作点ごとに、A の主 GC (Y5・Y50 は 100 µs、Y95 は 10 µs。評価計画 §3.2) の窓ごとの反復中央値 (1 窓 1 標本、D1534) を並べた列の標本 CV (標準偏差 (n−1) / 平均)。A の別 GC (A_alt: Y5・Y50 は 10 µs、Y95 は 100 µs) と control の GC 10・100 µs も同じ形で出す。
- **診断欄 (f_T と呼ばない):** 窓ごとの ln(A の主 GC / control の GC 10) の標本標準偏差 (同じ job の中で共通に動く揺れを除いた量)、各 job 内の 5 反復の CV (within-run、1 測定の品質の量で差の判定には使わない、D19)。
- **欠測:** job が落ちた窓の動作点は欠測とし、代替窓 (7・8) で補う。主値 = 代替を含む合格窓すべての CV、感度 = 予定窓 1〜6 のうち合格した窓だけの CV。合格窓が 5 未満の動作点は値を出さない。5 反復がそろわない job は標本にしない。within-run の品質で標本を捨てない (floor を下げる向きの除外をしない)。
- **job の検査 (集計の前):** manifest の status complete・spec の sha256 の一致・build ごとの compile command の照合 (driver が記録した `compile_command_binding.valid` と、期待する -D: genome の 5 軸・TRACE=0・ADD_ANALYSIS=0・WORKER1_INSERT_DELAY_RPHASE=0)・binary sha256・spec と run の多重集合の一致・各 run の exit 0・perf なし・throughput 有限正・binary sha の一致・submission_cluster の一致。1 つでも外れた job は理由付きで棄却する。集計 script は run の実効 flags (thread 数・skew・extime など) を spec と直接には照合しない。その一致は次の連鎖で担保される: driver が run ごとに stdout の `#FLAGS_` 行を argv と照合し、不一致なら例外で job を止める (`tools/vhash_cicada_tuning/driver.py` の `check_flags`、manifest が complete にならない)。argv は spec の run の条件から driver が作る。段 6 レビューが 360 run の `flags_raw` を別経路で点検し、48 thread・1M 件・各 rratio・GC に不一致は 0 だった。
- **統計の限界:** 6 標本の CV は相対標準誤差がおよそ 3 割 (1/√(2 × 5) ≈ 0.32) と粗い。正規性を仮定した信頼上限は CV の厳密な区間にならないので出さない。代わりに窓中央値の最小・最大と (最大/最小 − 1) を並べる。

## 4. 結果

予定 18 job (6 窓 × 3 動作点) はすべて検査に合格した (棄却 0)。代替窓 7・8 は使っていない (`window-cv.json` の `missing_jobs` に未投入として 6 件出るのはこの代替窓の spec)。したがって主値 (`primary`) と感度 (`scheduled_only`) は同じ値になる。

### 4.1 署名ごとの窓間 CV

| 動作点 | 署名 | 窓数 | 窓間 CV | 窓中央値の最小〜最大 (tps) | 最大/最小 − 1 |
|---|---|---:|---:|---|---:|
| **Y5 (rr5)** | **A・GC 100 (主)** | 6 | **0.69%** | 2,212,095 〜 2,253,862 | 1.89% |
| Y5 | A・GC 10 (A_alt) | 6 | 1.33% | 2,189,158 〜 2,273,111 | 3.83% |
| Y5 | control・GC 10 | 6 | 0.67% | 1,028,490 〜 1,049,531 | 2.05% |
| Y5 | control・GC 100 | 6 | 0.39% | 1,036,387 〜 1,047,390 | 1.06% |
| **Y50 (rr50)** | **A・GC 100 (主)** | 6 | **1.05%** | 3,470,782 〜 3,563,986 | 2.69% |
| Y50 | A・GC 10 (A_alt) | 6 | 1.06% | 3,403,894 〜 3,490,923 | 2.56% |
| Y50 | control・GC 10 | 6 | 0.82% | 752,434 〜 770,324 | 2.38% |
| Y50 | control・GC 100 | 6 | 0.96% | 751,279 〜 770,696 | 2.58% |
| **Y95 (rr95)** | **A・GC 10 (主)** | 6 | **0.70%** | 10,859,436 〜 11,091,187 | 2.13% |
| Y95 | A・GC 100 (A_alt) | 6 | 0.80% | 10,756,393 〜 11,001,662 | 2.28% |
| Y95 | control・GC 10 | 6 | 0.38% | 3,241,114 〜 3,277,818 | 1.13% |
| Y95 | control・GC 100 | 6 | 0.30% | 3,241,310 〜 3,269,193 | 0.86% |

検算: Y50 の主値を `runs.jsonl` から別経路 (jq で A・GC 100 の 5 反復の中央値を窓ごとに取り、awk で標本 CV) で再計算し 1.0482% を得た。集計 script の値 (0.010482) と一致する。

### 4.2 窓ごとの主値 (A の主 GC の反復中央値、tps)

| 窓 | 投入 (JST) | Y5 (host) | Y50 (host) | Y95 (host) |
|---|---|---|---|---|
| 1 | 15:18:42 | 2,233,666 (bnode086) | 3,479,199 (bnode013) | 11,091,187 (bnode061) |
| 2 | 16:19:08 | 2,253,862 (bnode013) | 3,470,782 (bnode008) | 11,014,830 (bnode067) |
| 3 | 17:19:09 | 2,223,360 (bnode021) | 3,523,059 (bnode013) | 10,859,436 (bnode018) |
| 4 | 18:19:14 | 2,215,354 (bnode087) | 3,524,917 (bnode080) | 11,014,609 (bnode086) |
| 5 | 19:19:14 | 2,212,095 (bnode018) | 3,477,932 (bnode036) | 10,961,767 (bnode020) |
| 6 | 20:19:15 | 2,220,426 (bnode028) | 3,563,986 (bnode026) | 11,014,591 (bnode023) |

投入時刻は起動器の記録。job の開始時刻 (manifest の `started_utc`) は投入の 9〜491 秒後 (queue 待ち)。18 job は 14 の異なる node に割り当たった (複数回使われたのは bnode013 が 3 回、bnode086・bnode018 が各 2 回)。

### 4.3 診断欄 (f_T と呼ばない)

- 窓ごとの ln(A の主 GC / control の GC 10) の標本標準偏差: Y5 0.82%・Y50 1.04%・Y95 0.70%。A 単独の CV とほぼ同じで、同じ job の control と A が窓ごとにそろって動く揺れ (共通の揺れ) は目立たない。
- 各 job 内の 5 反復の CV (within-run、72 系列): 0.18〜3.81%、中央値 1.08% (中央の 2 系列の平均)。品質の閾値 5% (D19) を超える系列は無い。

## 5. 1 投入束の値 (md_11) との比較

| 動作点 | md_11 の control の CV (1 投入束・約 1 時間・5 session) | 本 wave の control・GC 10 の CV (日内 6 窓・約 5 時間) |
|---|---:|---:|
| Y5 | 0.463% | 0.67% |
| Y50 | 0.812% | 0.82% |
| Y95 | 0.430% | 0.38% |

D145 は「1 投入束の値は時間の変動を含まない下限で、系統的に低い側に倒れる」とした。今回、同じ量を約 5 時間の 6 窓へ広げても、値は 1 投入束のときと同じ程度だった。これは日内の数時間の変動が小さいことを示すが、日を跨ぐ変動が小さいことは示さない。

md_11 J2 (2026-09-29、前日、同じ genome・GC・件数・thread、3 反復) の A の値は参考として次のとおり (窓の標本には入れていない。反復数と job の構成が違い、A の選択に使った測定でもある): Y5 GC 100 2,234,869、Y50 GC 100 3,477,599、Y95 GC 10 11,050,316 tps。3 つとも本 wave の 6 窓の最小〜最大の内側にある。

**読んではいけないこと:** 窓間 CV が within-run の CV (中央値 1.08%) と同じ程度か小さいことを、「Cicada は安定している」と積極的に解釈しない。反復の中央値を取ると揺れは小さく出る (D145 の却下した選択肢と同じ構造)。

## 6. 評価計画への読み方

- **Y5・Y50・Y95 の A (主 GC) の署名:** δ_T は D19 の下限で計算して ln 1.03。本値はいずれも 3% より小さく、仮に式へ入れても δ_T は同じ値になる (本値は f_T ではないので代入はしない)。本値を添えて変わるのは根拠で、下限だけなら「Cicada の揺れが 3% 以下かは測っていない」、本値を添えれば「日内 6 窓の範囲では Cicada A の窓間の揺れは 3% より小さかった (日を跨ぐ変動・cold boot は未測定)」と書ける。
- **A_alt の署名** (「Cicada の最良設定に対して」の headline 判定、評価計画 §5.2) も CV は 3% より小さい。ただし Y5 の A_alt (GC 10) は窓中央値の最大/最小 − 1 が 3.83% で、6 窓のうち最も離れた 2 窓の差は 3% を超えた。δ_T はこの署名でも下限で計算するが、この署名の差の判定では窓による揺れが下限に近いことを併記するのが安全である。
- **R・L-w・100 操作型の cell は測っていない。** R は性能用 build で ro 指定率を制御する生成器が無い (評価計画 §4.2)。L-w は H4 の主指標が throughput でなく、throughput は費用の併記に使われる。D145 項 4 により、Y の値をこれらの cell へ外挿しない。これらの cell で throughput の閾値が要る判定には、評価計画 §8.3 の二択が残る。
- **評価計画 §10 の S0 の floor 行** (性能用 A × (Y 3 + R 3 + L-w 4) × 8 job × 5 rep) とは別の計測である。本値は関門を通っておらず、真正な floor の標本設計も未裁定なので、S0 の走行を差し引く根拠にはしない。S0 へ本値を再利用するかどうかと S0 の行列は、発効の wave が設計する。
- **3% を超える値が将来出た場合:** δ_T を上げると、「改善」は出にくくなる一方で、同等は通りやすく、悪化・A/A 判定・job 間の停止条件 (2δ) は止まりにくくなり、採否は両方向に動きうる (§2 の表)。したがってそのような値を δ_T に入れるかは、これら 4 箇所への影響を含めて発効の wave が別に裁定する。今回は該当しない。
- **§8.3 の二択はユーザーの判断として残す。** 本値は二択の判断材料であって、どちらかを決めるものではない。

## 7. 確かめたこと・確かめていないこと

確かめたこと:

- stock Cicada (pin `6810666`、patch なし) の A と control を、trace・計器なしの build (compile command の -D と binary sha256 で束縛) で、日内 6 窓 × 3 動作点、18 job で測った。18 job すべてが §3 に列挙した集計前の検査に合格した (実効 flags は §3 の連鎖と段 6 レビューの点検で一致)。
- 署名ごとの窓間 CV・最小・最大 (§4.1)。Y50 の主値は生データから別経路で再計算して一致した。
- 窓ごとの host と投入時刻 (§4.2)。
- md_11 の 1 投入束の control の CV との比較 (§5)。

確かめていないこと・限界:

- **日を跨ぐ変動・cold boot・時間の長い変動。** 6 窓は同じ日の約 5 時間に収まる。D145 が floor に求める「時間窓 cluster を複数」の形式は満たすが、窓の間隔 60 分は運用値で、窓の独立性を証明しない。真正な floor の標本設計 (D145 項 5 の時間窓 cluster 数と標本数の裁定) を本 wave で行ったとは主張しない。別の日に同じ spec 形・同じ起動器で窓を足すのは安価 (1 窓 3 job で約 6 node 分)。
- **関門を通った floor ではない。** floor artifact (`output/env/*/calibration/between_run_noise_*`) は作っておらず、izanagi の compare・採否に接続していない。
- **R・L-w・100 操作型の cell、48 thread 以外の thread 数、skew 0.9 以外、1M 件以外。** 動作点署名ごとの量なので外挿しない (D145 項 4)。
- **正しさ:** A と control の正しさは本 wave では検査していない。md_20 が同じ設定を判定器に掛け「その条件で巡回なし (上限 indeterminate)」としたのが根拠で、certified ではない。本 wave の throughput は正しさの主張に使わない。
- **統計の精度:** 6 標本の CV は粗い (§3)。信頼区間は出していない。
- **図は作っていない。** 値は §4 の表と `window-cv.json` にある。
- **ノードの同居:** md_29・31・32・33 と同じノードで測らないよう、driver の `_check_solo` (同じノードの競合 benchmark process があれば停止) に頼った。18 job とも停止していない。scheduler の割当てを専有の保証とは見なしていない。

## 8. 工程

- 段 1: brief (道の比較と計測の事前登録)。段 2 (codex の plan 起草) は省き、plan を brief と段 4 裁定に含めた。
- 段 3: 敵対相談 2 本 (A: 正しさ境界・関門の迂回・D145 への忠実さ、B: 過剰・統計・費用)。must-fix 5 件を含む 15 所見。主な反映: 値を「floor 取得済み」「f_T 確定」と書かない (A1)・60 分間隔を運用値と明記 (A2)・欠測と代替窓の表と感度 (A3)・md_11 J2 を窓に混ぜない (A4・B3)・正規性の信頼上限を出さない (A6・B2)・Y 以外は未測定と明記 (A7・B1)。
- 段 4: 所見をすべて real と裁定し、plan v2 (spec の入力 file・seed・submission_cluster・代替規則・集計の検査) を固定した。
- 段 5: 集計 script (`analyze_windows.py`) を Codex author が書いた (repo 外に置く。repo の実装面の差分はゼロ)。合成データの自走検査 3 件 (6 種の棄却・5 窓未満の未確立・代替窓の有無・create-only)。親が `cfloor-scratch/` を repo checkout の root に置いた配置で実走し 3 件 OK。repo 外の別の場所に置いたまま走らせると、自走検査が子の PYTHONPATH をその場所の親に上書きするため `tools` を import できず 9 件失敗する (配置の前提であって検査の欠陥ではない)。
- 計測: 窓 1 を 15:18、以後 60 分おきに 20:19 まで。利用上限で 20:21〜21:41 に中断したが、計測は中断前に全窓完了していた。
- 段 6: 敵対レビュー 1 本 (生データからの検算・過大主張・集計 script・観測者効果・過剰)。§4 の表は 360 run から丸めまで再現された。所見 6 件をすべて real と裁定し、文言と置き場で直した: R1 (must-fix) 「max があるので採否を緩める経路は無い」を訂正 (§2・§6)、R2 S0 の走行を差し引けるという読みを削除、R3 実効 flags の担保の連鎖を明記 (§3)、R4 script と spec を永続の置き場へ移し手順を直した (§10)、R5 within CV の中央値 1.09% → 1.08% と control の範囲の対象を明記、R6 Elapse の出典を明記 (§9)。
- fix 後の焦点再レビュー 1 本 (DW-O16): R2・R4・R5・R6 closed。派生値 (2,186 s・control の範囲・within 中央値・永続の置き場からの再実行の一致) は原データから再計算され一致。R1 は partial — δ_T は A/A 判定と job 間の停止条件 (2δ) にも効き、上げると止まっていた cell の「改善」も主張できるようになるので、「偽の改善は増えない」も判定全体では成り立たない (新所見 N1、must-fix)。また「0.030 以下なら f_T に代入してよい」は §8.3 が f_T を D145 の floor に限るのと食い違う (N2)。両方を直し、本値は f_T に代入せず D19 の下限で計算した δ_T の根拠として併記する形に統一した (§2 の表)。R3 は partial のまま — 集計 script 自体は実効 flags を照合しないが、レビュー 2 本がそれぞれ 360 run の argv と `flags_raw` を照合して不一致 0 で、値は変わらない。§3 に限界として書き、script は変えない。
- 焦点再レビュー 2 巡目: R1・N1・N2 closed (4 箇所の表に抜けなし、4 file の方針に矛盾なし)、R3 を partial のまま閉じる親裁定に反論なし。nit 2 件 (表の導入文の「緩む」、「3% 以下なので δ_T が動かない」という読み) を文言で直した。
- 変異 matrix: repo の実装面の差分がゼロなので免除 (DW-S04)。

## 9. 計算

計算ノードの job (NQSV の Elapse、各窓 3 job):

| 窓 | Y5 | Y50 | Y95 |
|---|---:|---:|---:|
| 1 | 112 s | 149 s | 139 s |
| 2 | 105 s | 108 s | 105 s |
| 3 | 105 s | 105 s | 107 s |
| 4 | 158 s | 277 s | 143 s |
| 5 | 133 s | 107 s | 106 s |
| 6 | 105 s | 106 s | 105 s |

18 job の Elapse 合計 2,275 s = 37.9 node 分 (約 0.63 node 時間)。1 本の最長 277 s (5 分未満)。2 node 時間を大きく下回る。出典は dispatch log (`/work/1/SFC/tanab/dev-wave-jobs/dev-wave-cicada-between-run-floor/dispatch-logs/w<k>-y<o>.log` の NQSV の `Elapse:` 行、request 番号も同じ log)。manifest の開始〜終了の差の合計 (2,186 s) は job body の中だけの時間で、Elapse とは別の量である。

## 10. 再生成

置き場 (repo 外、永続): `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-cicada-between-run-floor/`。`cfloor-scratch/analyze_windows.py` (sha256 `3abeb402cde2eb16cddb6970bfd674b16af04ba1f466a703c22688c14c8eb749`、Codex author)・`cfloor-scratch/selftest_analyze_windows.py` (`93b3f8a32bdc1ee7e3e682d6f90c046de45fff03f69e8ceeaa0f7d608cbc0a1a`)・`specs/` (窓 1〜8 の spec と make-spec の入力)・`gen-specs.sh`・`run-measure.sh`・`launch-window.sh`・`series.sh` (親の起動器)・`dispatch-logs/`・`raw-archive/`。

集計 (repo root から):

```bash
PYTHONPATH=. python3 /work/1/SFC/tanab/dev-wave-jobs/dev-wave-cicada-between-run-floor/cfloor-scratch/analyze_windows.py \
  --output-root output/env/pegasus/vhash-cicada-baseline-tuning \
  --specs-dir /work/1/SFC/tanab/dev-wave-jobs/dev-wave-cicada-between-run-floor/specs \
  --summary <新しい path>.json
```

この置き場から走らせた結果は、`window-cv.json` と入力 path の欄を除いて一致した (段 6 で確認)。自走検査は `cfloor-scratch/` を repo checkout の root へ写し、root から `python3 cfloor-scratch/selftest_analyze_windows.py` で走らせる (§8)。値そのものは `runs.jsonl` から §3 の定義 (窓ごとに 5 反復の中央値、窓間の標本 CV) でも再計算できる (§4.1 の検算と同じ手順)。
