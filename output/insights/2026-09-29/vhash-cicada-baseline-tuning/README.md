# VHash 論文の比較相手 Cicada を較正し、最良の設定を実測で決めた (主 baseline の準備、2026-09-29)

authority: none / default_effect: no-state-change (可変状態の正本は worklog 末尾と現行 phase doc)。
wave `dev-wave-vhash-cicada-baseline-tuning` (branch 同名)、起点 local main `1887f56e4` (開始 gate fresh rc 0、2026-09-29 09:53 JST)、CCBench submodule = pin `68106660` (動かしていない、Cicada のソースは無改変)。
job dir `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-vhash-cicada-baseline-tuning/` (段 1 brief・段 2 plan・段 3 相談 2 本・段 4 / 6 裁定・Codex の prompt と報告・job spec・計測の起動ログ)。依頼は `/work/1/SFC/tanab/tmp/vhash-2026-09-29/md_11.txt` (同 dir `request-md_11.txt` に逐語)。
生出力: `output/env/pegasus/vhash-cicada-baseline-tuning/<job-id>/` (runs.jsonl・job-manifest.json。run 行は stdout/stderr の sha256 を持つ)。run ごとの stdout/stderr と build ログ (計 968 本、末尾空白を含む生ログ) は repo へ入れず `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-vhash-cicada-baseline-tuning/raw-archive/vhash-cicada-baseline-tuning/<job-id>/` に退避した。集計: 本 dir の `summary.json` (`tools/vhash_cicada_tuning` の `analyze` 出力)。図: 本 dir の `figures/` (生成器 `tools/plotting/plot_vhash_cicada_tuning.py`)。

**この資料の性能値はすべて「正しさ未検証の診断値」である。** 測った Cicada の設定は検査器 (izanagi の直列化可能性判定) に通していない。serializable とは書かない。採否・headline・compare・floor には接続しない (§9)。

## 1. 依頼と結論

依頼 (VHash 論文の並行 wave md_11): 論文の主比較は「最適化と GC 設定を調整した Cicada」(出典メモ §25・§28.1、最初の版 §9)。「GC 間隔を不適切に大きくした Cicada だけに勝っても不十分」なので、提案を測る前に比較相手を公平に強くしておく。着手時点で CCBench の Cicada の最適化フラグ空間 (`orchestrator/campaign/genome.py` の `CICADA_SPACE`、正準 24 点) の定義はあったが、Cicada 用のレコード数とばらつき幅の記録は無かった。

結論:

1. **レコード数は 4 workload とも 1,000,000。** 計算ノードで perf が使えず (preflight rc 非 0) cache miss 率の飽和は判定できなかったので、calibrator の第二基準 (D15: maxrss が L3 の 4 倍を超える最小 N) で決めた。1M で maxrss 1.11〜1.25 GB ≥ 4 × 110,100,480 B (§3)。
2. **Cicada の走行間ばらつき (control の job 間 session median の CV) は 0.43〜0.81%。** 5 session・4 投入束・4〜5 node。D145 の意味の floor ではない (§4)。
3. **stock の既定設定は最良から大きく離れている。** J2 (確認) の観測最良は、rr5・rr50・rr95 が同じ `BACK_OFF=0, INLINE_VERSION_OPT=1, INLINE_VERSION_PROMOTION=0, REUSE_VERSION=1, WRITE_LATEST_ONLY=0` で、既定 (control) に対し rr5 2.15 倍・rr50 4.54 倍・rr95 3.41 倍。100 操作型は `BACK_OFF=0, INLINE_VERSION_OPT=0, INLINE_VERSION_PROMOTION=0, REUSE_VERSION=0, WRITE_LATEST_ONLY=0` で 1.38 倍 (§6)。**論文の比較相手に CCBench の既定の Cicada を使うと、弱い baseline になる。**
4. **最大の要因は BACK_OFF=0 (abort 後の待ちを入れない)。** 48 thread・skew 0.9 では throughput が 2〜4 倍になる一方、abort 率も上がる (rr50 で 0.14 → 0.42)。REUSE_VERSION=0 は rr5〜rr95 で大きく遅く、RSS が 3〜4 GB に膨らむ (§5)。
5. **GC 間隔は 10〜100 µs が最良付近で、10,000 µs では最良設定が大きく落ちる** (rr95 で 1,105 万 → 640 万 tps)。既定 control は GC 間隔にほとんど反応しない (§6、図 (b))。
6. **stock CCBench の不具合 2 件を見つけた** (Cicada は改変していない): (a) `INLINE_VERSION_OPT=1` かつ `INLINE_VERSION_PROMOTION=1` の 8 genome は compile できない。測れた空間は 24 点でなく 16 点。(b) 「読み取り後に待つ」ための `WORKER1_INSERT_DELAY_RPHASE` の分岐も compile できず、この長い tx の型 (W5) は測れなかった (§8)。
7. **「最良から ばらつき 以内の候補集合」はどの workload も最良 1 点だけだった** (次点は幅のわずかに外、§6)。ただしこの集合は事前登録どおりの記述的なリストで、統計的な同等性の証明ではない。

## 2. 条件表

| 項目 | 値 |
|---|---|
| 環境 | Pegasus 計算ノード (gen_S、Xeon Platinum 8468 × 1、48 core、SMT 無効、L3 110,100,480 B)。login node では計測していない |
| CCBench | pin `68106660`、stock (patch なし)。`-DCCBENCH_TRACE=0 -DCCBENCH_ADD_ANALYSIS=0` (検査用 trace・計器なし、絶対規律 1) |
| thread | 48 (`-thread_num=48`)、numactl なし (Pegasus の環境契約) |
| 走行 | `-extime=3`、`-clocks_per_us=2100`、`-ycsb_zipf_skew=0.9`、`-ycsb_rmw=0`。性能値は `throughput[tps]` |
| workload | W1 rr5・W2 rr50・W3 rr95 (各 `-ycsb_max_ope=10`)、W4 操作数が多い型 = rr95・`-ycsb_max_ope=100` (全 thread の全 tx が 100 操作)、W5 読み取り後に待つ型 = rr50 + worker 1 が commit 前に 1 ms 待つ (build 時 define) → **compile 不能で欠測** |
| genome | `CICADA_SPACE` の正準 24 点のうち build できた 16 点 (§8)。control = CMake 既定の正準点 `BACK_OFF=1, INLINE_VERSION_OPT=0, INLINE_VERSION_PROMOTION=0, REUSE_VERSION=1, WRITE_LATEST_ONLY=0` (既定は PROMOTION=1 だが OPT=0 では data path が同じ冗長点なので正準点で代表させた) |
| gc_inter_us | J1: W2 は {10, 100, 1000}、他は 10。J2: {10, 100, 1000, 10000} |
| 反復 | J0 within-run 10、J1 2 (縮小梯子 R3)、J2 3 |
| binding | build ごとに compile_commands.json の `ycsb_cicada.exe` target の 3 TU の -D を期待値と照合、binary sha256 を記録。run ごとに `#FLAGS_*` 行を argv と照合 |

`-tuple_num` 等の接頭辞なし flag は Cicada の YCSB の workload を変えない (`include/ycsb.hh` は `-ycsb_*` を読む) ので使っていない。rr20・rr80 は holdout 関門の対象なので使っていない。

## 3. レコード数の較正 (J0)

calibrator の方針 (`.claude/agents/calibrator.md`): 1M から倍々に上げ、LLC miss 率が飽和する最小 N、飽和が無ければ D15 の下限 (maxrss ≥ 4 × L3) を採る。control genome・48 thread・各点 3 反復。

計算ノードの literal `perf` の preflight は nonzero-rc で不可だった (job-manifest の `perf_preflight`)。したがって **miss 率の飽和は判定していない**。N は D15 の RSS 下限で決めた。1M で下限を満たしたので 4M で打ち切った。

| workload | N | maxrss (3 反復平均) | throughput (tps、3 反復平均) |
|---|---:|---:|---:|
| W1 rr5 | 1M | 1,249,400 kB | 1,038,050 |
| | 2M | 2,234,060 kB | 977,625 |
| | 4M | 4,137,112 kB | 957,182 |
| W2 rr50 | 1M | 1,164,150 kB | 759,405 |
| | 2M | 2,157,530 kB | 766,454 |
| | 4M | 4,032,640 kB | 803,838 |
| W3 rr95 | 1M | 1,134,032 kB | 3,270,790 |
| | 2M | 2,111,280 kB | 3,293,840 |
| | 4M | 3,953,750 kB | 3,379,880 |
| W4 100 操作 | 1M | 1,113,460 kB | 69,737 |
| | 2M | 2,078,190 kB | 75,885 |
| | 4M | 3,901,050 kB | 78,903 |

4 × L3 = 440,401,920 B ≈ 430,080 kB なので、全 workload で 1M が下限を満たす。Cicada は 1M でも版の予約 (`-pre_reserve_version` 既定 10,000 / thread) 等で RSS が 1 GB を超える。既存の Pegasus 較正 11 件 (silo・mocc・tictoc) も 1M〜2M で D15 採用だった。

within-run のばらつき (J0、確定 N、control、連続 10 反復、perf なし) の CV: W1 1.07%・W2 1.56%・W3 0.73%・W4 1.43%。これは 1 測定の品質の量 (D19) で、採否の閾値ではない。

## 4. 走行間ばらつき

**量の名前:** Cicada control の job 間 session-median CV (複数投入束)。control genome・N=1M・gc_inter_us=10 の run を job ごとに rep median にまとめ (J0 の within-run 10 反復は 1 session)、その標本 CV を取った。

| workload | CV | session (=job) 数 | 投入束数 | node 数 |
|---|---:|---:|---:|---:|
| W1 rr5 | 0.463% | 5 | 4 | 5 |
| W2 rr50 | 0.812% | 5 | 4 | 4 |
| W3 rr95 | 0.430% | 5 | 4 | 5 |
| W4 100 操作 | 0.477% | 5 | 4 | 5 |

投入束は J0c (11:28)・J1 (11:56)・J1 の再投入 (12:06)・J2 (12:31) の 4 つ (いずれも JST、起動ログの start 時刻)で、すべて 2026-09-29 の約 1 時間の中にある。**これは D145 の意味の between-run floor ではない** (時間窓 cluster は実質 1 つ、session 数 5)。D1373 の関門 (trace hook の証拠が無い protocol の floor 生成を拒否) を迂回する floor artifact (`output/env/*/calibration/between_run_noise_*`) は作っておらず、compare・採否にも接続していない。Cicada の floor は未取得のままである。

## 5. 探索 (J1、GC=10 中心、反復 2)

24 点を 6 点ずつ 4 job に割り、各 job に control を置いた。build できない 8 点 (§8) は測れず、落ちた 2 job の build できる genome を 1 job にまとめて再投入した。J1 は候補の選抜にだけ使い、最良の値は J2 で測り直した (選抜と推定を分ける、段 4 裁定)。

J1 の rep median (tps)。genome は `B=BACK_OFF O=INLINE_VERSION_OPT P=INLINE_VERSION_PROMOTION R=REUSE_VERSION W=WRITE_LATEST_ONLY`。

| genome | W1@10 | W2@10 | W2@100 | W2@1000 | W3@10 | W4@10 |
|---|---:|---:|---:|---:|---:|---:|
| B0 O0 P0 R0 W0 | 430,073 | 793,763 | 806,596 | 720,549 | 6,153,034 | 92,301 |
| B0 O0 P0 R0 W1 | 463,966 | 801,688 | 732,764 | 819,915 | 6,198,598 | 89,119 |
| B0 O0 P0 R1 W0 | 2,166,890 | 3,260,851 | 3,288,123 | 3,153,345 | 10,123,545 | 83,592 |
| B0 O0 P0 R1 W1 | 1,939,207 | 2,960,679 | 2,924,918 | 2,829,202 | 10,123,620 | 84,977 |
| B0 O1 P0 R0 W0 | 485,964 | 729,804 | 766,227 | 829,617 | 9,319,262 | 87,031 |
| B0 O1 P0 R0 W1 | 449,566 | 808,696 | 835,249 | 771,219 | 9,355,565 | 89,427 |
| B0 O1 P0 R1 W0 | 2,146,815 | 3,441,106 | 3,486,822 | 3,302,454 | 10,936,773 | 85,276 |
| B0 O1 P0 R1 W1 | 2,057,195 | 3,092,414 | 3,163,682 | 3,014,960 | 10,963,986 | 87,304 |
| B1 O0 P0 R0 W0 | 390,888 | 550,157 | 600,544 | 567,243 | 2,795,710 | 67,723 |
| B1 O0 P0 R0 W1 | 360,417 | 552,392 | 538,149 | 545,755 | 2,781,463 | 70,371 |
| **B1 O0 P0 R1 W0 (control)** | 1,037,198 | 761,995 | 764,863 | 792,321 | 3,265,110 | 69,219 |
| B1 O0 P0 R1 W1 | 662,184 | 729,069 | 758,969 | 776,758 | 3,197,810 | 67,747 |
| B1 O1 P0 R0 W0 | 529,870 | 687,757 | 682,748 | 704,700 | 3,164,129 | 71,881 |
| B1 O1 P0 R0 W1 | 493,096 | 627,779 | 622,626 | 660,038 | 3,107,569 | 70,610 |
| B1 O1 P0 R1 W0 | 1,077,878 | 777,748 | 794,084 | 820,617 | 3,450,817 | 72,434 |
| B1 O1 P0 R1 W1 | 666,034 | 752,312 | 725,731 | 774,216 | 3,397,137 | 70,613 |
| O1 P1 の 8 点 | build 不能 | | | | | |

見えること (探索値、正しさ未検証):
- **BACK_OFF=0** が W1〜W3 で最大の要因 (REUSE=1 どうしで 2〜4 倍)。
- **REUSE_VERSION=0** は W1・W2 で大きく遅い。maxrss は BACK_OFF=0 かつ REUSE=0 の 4 点で W1・W2 とも 3.6〜4.8 GB、BACK_OFF=1 かつ REUSE=0・WRITE_LATEST_ONLY=0 の 2 点で W1 だけ 3.1〜3.5 GB に膨らむ。他の REUSE=0 の点・条件は 1.1〜2.0 GB で、REUSE=0 だけで RSS が決まるわけではない (版 object を使い回さないことが一因と推定、未検証)。W4 (100 操作) では逆に REUSE=0 が上位に来た。
- INLINE_VERSION_OPT=1 は W2・W3 で数 % 上、WRITE_LATEST_ONLY=1 は W1 で下。
- 選抜 (job 内 control 比の median 上位 2、W2 は GC 3 点の最大で順位): W1 {B0 O1 P0 R1 W0, B0 O0 P0 R1 W0}、W2 同左、W3 {B0 O1 P0 R1 W1, B0 O1 P0 R1 W0}、W4 {B0 O0 P0 R0 W0, B0 O1 P0 R0 W1}。

## 6. 確認 (J2) — 最良設定と候補集合

各 workload を 1 job にし、選抜 2 点 + control を gc_inter_us {10, 100, 1000, 10000} × 3 反復で、rep ごとに順序を並べ替えて測った。score = 同じ job の GC=10 control の rep median に対する比の rep median。**best = score 最大、候補集合 = score ≥ score_best × (1 − cv_w)** (cv_w は §4 の値。結果を見る前に段 4 で固定した規則)。

| workload | 観測最良 (genome, GC) | score | best の throughput (tps) | control@10 (tps) | 候補集合 | 次点 (score) |
|---|---|---:|---:|---:|---|---|
| W1 rr5 | B0 O1 P0 R1 W0, 100 µs | 2.154 | 2,234,869 | 1,037,526 | best のみ | 同 genome GC 10 (2.143、閾値 2.144) |
| W2 rr50 | B0 O1 P0 R1 W0, 100 µs | 4.536 | 3,477,599 | 766,719 | best のみ | 同 genome GC 10 (4.491、閾値 4.499) |
| W3 rr95 | B0 O1 P0 R1 W0, 10 µs | 3.413 | 11,050,316 | 3,238,120 | best のみ | B0 O1 P0 R1 W1, GC 10 (3.390、閾値 3.398) |
| W4 100 操作 | B0 O0 P0 R0 W0, 1000 µs | 1.383 | 96,365 | 69,688 | best のみ | 同 genome GC 10 (1.329) |

GC 間隔と throughput (J2 の rep median、tps):

| workload・genome | GC 10 | GC 100 | GC 1000 | GC 10000 |
|---|---:|---:|---:|---:|
| W1 best (B0 O1 P0 R1 W0) | 2,223,866 | 2,234,869 | 2,146,081 | 1,542,133 |
| W1 control | 1,037,526 | 1,047,578 | 1,040,733 | 944,066 |
| W2 best (B0 O1 P0 R1 W0) | 3,443,572 | 3,477,599 | 3,289,515 | 2,778,108 |
| W2 control | 766,719 | 766,122 | 809,065 | 797,633 |
| W3 best (B0 O1 P0 R1 W0) | 11,050,316 | 10,985,690 | 10,049,277 | 6,399,244 |
| W3 control | 3,238,120 | 3,276,082 | 3,279,546 | 3,072,973 |
| W4 best (B0 O0 P0 R0 W0) | 92,603 | 92,388 | 96,365 | 88,778 |
| W4 control | 69,688 | 69,172 | 69,231 | 69,868 |

abort 率 (J2、GC 10 の rep 平均): W1 best 0.20 / control 0.067、W2 best 0.425 / control 0.141、W3 best 0.056 / control 0.022、W4 best 0.916 / control 0.732。BACK_OFF=0 は abort を増やしても再実行を待たないので、48 thread・skew 0.9 では throughput が上がる。

読み方:
- **rr5・rr50・rr95 の論文の主比較相手は `B0 O1 P0 R1 W0` を GC 10〜100 µs で動かした Cicada** が候補になる。rr50 はこの wave で唯一、GC {10,100,1000} × 16 genome の全体を J1 で見ているので「GC {10,100,1000} 上の 16 点全体の観測最良」と言える。他の workload は「GC=10 で選抜した候補の中の観測最良」である。
- GC 10 と 100 の差は 0.5〜1% で、ばらつき幅とほぼ同じ。**GC 10 と 100 のどちらを最良と書くかは、この測定では決めきれない** (候補集合の規則ではぎりぎり 1 点だが、差は 1% 未満)。
- 最良設定は **GC 10,000 µs で自身の最高値から 8〜42% 落ちる** (W1 31.0%・W2 20.1%・W3 42.1%・W4 7.9%。§28.1 の「基準方式は短い GC 間隔で局所性を維持する必要がある」に合う向き)。control は落ち方が小さい (自身の最高値から 0〜10%: W1 9.9%・W2 1.4%・W3 6.3%・W4 0% = GC 10,000 が最高)。この図は「GC 間隔を不適切に大きくした Cicada」がどれだけ弱いかの目安になる。
- W4 (100 操作) は最良でも control の 1.38 倍で、abort 率 0.92 と高い。長い tx では Cicada 自体が厳しい。

## 7. 図

生成器: `tools/plotting/plot_vhash_cicada_tuning.py` (作図は login、計測機の外)。再生成:

```bash
MPLCONFIGDIR=<tmp> PYTHONPATH=. python3 -m tools.plotting.plot_vhash_cicada_tuning \
  --runs output/env/pegasus/vhash-cicada-baseline-tuning/{cicada-j0c,cicada-j1-0,cicada-j1-2,cicada-j1-13,cicada-j2-0,cicada-j2-1,cicada-j2-2,cicada-j2-3}/runs.jsonl \
  --summary output/insights/2026-09-29/vhash-cicada-baseline-tuning/summary.json \
  --out-prefix output/insights/2026-09-29/vhash-cicada-baseline-tuning/figures/vhash-cicada
```

- **図 (a) `figures/vhash-cicada-j1.{png,pdf}`** — J1 (探索値): workload 別 (W1〜W4) の段に、genome ごとの throughput の rep median (棒、Mtps) と、同じ job の control に対する比 (折れ線、右軸) を描く。W2 は GC 10・100・1000 µs を色で分ける。横軸は `CICADA_SPACE` の列挙順の番号 (0〜23) で、control は破線 (14)。build できない 8・9・10・11・20・21・22・23 (OPT=1 かつ PROMOTION=1) は描いていない。番号と設定の対応は `figures/vhash-cicada-j1.provenance.json` の `genome_index`。
- **図 (b) `figures/vhash-cicada-j2.{png,pdf}`** — J2 (確認値): workload 別に gc_inter_us (対数) と throughput の rep median (Mtps) を、選抜 2 点と control で描く。凡例は `B0 O1 P0 R1 W0` 形式 (B=BACK_OFF、O=INLINE_VERSION_OPT、P=INLINE_VERSION_PROMOTION、R=REUSE_VERSION、W=WRITE_LATEST_ONLY)。系列と正準表記の対応は provenance の `series`。
- どちらの図も表題に「正しさ未検証の診断値」を、caption に欠測 (W5・build 不能 8 点) を書いている。provenance JSON は入力 runs.jsonl の sha256・集計値 (tps のまま)・表示単位の換算 (1,000,000 で割る) を持つ。保存前に生成器の重なり検査を通っている (fix-6 で実データの桁の重なりを検査が止め、軸を Mtps にして通した)。

## 8. CCBench の不具合 (還元候補、還元判断: ユーザー確認待ち)

### 8.1 INLINE_VERSION_OPT=1 かつ INLINE_VERSION_PROMOTION=1 が compile できない

- 発見: pin `68106660` の stock Cicada を `CCBENCH_INLINE_VERSION_OPT_CICADA=1`・`CCBENCH_INLINE_VERSION_PROMOTION=1` で build すると、BACK_OFF・REUSE_VERSION・WRITE_LATEST_ONLY の値によらず 8 genome すべてが compile error になる。他の 16 genome は全て build できた。
- 再現条件: 48 core 計算ノード、gcc 11 (`/usr/bin/x86_64-linux-gnu-g++-11`)、`-DCMAKE_BUILD_TYPE=Release -DCCBENCH_TRACE=0`、target `ycsb_cicada.exe`。build ログ (repo 外): `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-vhash-cicada-baseline-tuning/raw-archive/vhash-cicada-baseline-tuning/cicada-j1-1/` と `cicada-j1-3/` の `build-*.build.log` (失敗 8 本。例 `cicada-j1-1/build-742b1b3d0c51.build.log` sha256 `b2d83d977f2677f7b7085ef7c9fd6c3b58426cd09c452976d84bcab3eec1150a`)。どの build が失敗したかは repo 内の各 job の job-manifest.json にも残る。
- 該当コード: `cc/cicada/include/transaction.hh:198-212` (`inlineVersionPromotion`)。207 行の `write(s, key, TupleBody(ver->body_));` で `error: cannot convert 'Storage' to 'int'`。
- 仮説: `TxExecutor::write` の引数が変わった後、`#if INLINE_VERSION_OPT` / `#if INLINE_VERSION_PROMOTION` の内側だけが追随していない (既定は OPT=0 なので既定 build では compile されない)。
- izanagi との関係: `genome.py` の `CICADA_SPACE` の注記は「24 通りは YCSB workload での静的導出であり実測ではない」と書く。現 pin の実測では build できるのは 16 通り。md_3 (`output/insights/2026-09-29/vhash-cicada-verifier/README.md`) は TRACE=1 でこの組を `#error` で止めたが、TRACE=0 でも build できないことはこの wave で分かった。
- 還元判断: ユーザー確認待ち。

### 8.2 WORKER1_INSERT_DELAY_RPHASE の分岐が compile できない

- 発見: `CCBENCH_WORKER1_INSERT_DELAY_RPHASE=1` と `-DWORKER1_INSERT_DELAY_RPHASE_US=1000` で build すると compile error。
- 再現条件: 上と同じ。build ログ (repo 外): `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-vhash-cicada-baseline-tuning/raw-archive/vhash-cicada-baseline-tuning/cicada-j0b/build-34300401c3df.build.log` (215〜235 行、sha256 `8a66de1ee5588c965aa96cbbd0b2fc80c731e1fbd774def605133f1cd2a23b5e`) と `cicada-j0c/` の同名 file。
- 該当コード: `cc/cicada/transaction.cc:923-927`。924 行の `thid` は未宣言 (member は `thid_`)、925 行の `clock_delay` も未宣言 (include 不足)。`WORKER1_INSERT_DELAY_RPHASE_US` はソース全体で定義が無い。runtime flag `-worker1_insert_delay_rphase_us` (`cc/cicada/include/common.hh:61`) は表示されるだけで、この分岐から読まれない。
- 仮説: 計測撹乱ノブとして genome の軸から外され build されないまま腐った。
- 影響: 依頼の「読み取り後に待つ型」の長い tx (W5) は stock のまま作れず欠測。
- 還元判断: ユーザー確認待ち。

(もう 1 点: Cicada の `ShowOptParameters()` は定義だけで呼出しが無い (呼ぶのは ss2pl だけ)。不具合ではないが、起動時の option 表示で build 条件を確かめることはできない。本 wave は compile command で確かめた。)

## 9. 確かめたこと・確かめていないこと

確かめたこと:
- stock Cicada の 16 genome を trace・計器なしで build し、compile command の -D と binary sha256 で条件を束縛して 48 thread で測った (§2)。
- レコード数は D15 の RSS 下限で 1M (§3)。
- control の job 間 session-median CV (5 session、4 投入束) (§4)。
- J1 で選び J2 で測り直した観測最良と、事前登録の規則による候補集合 (§6)。

確かめていないこと・限界:
- **正しさ:** 最良設定を含めどの設定も検査器に通していない。md_3 の trace patch で `B0 O1 P0 R1 W0` 等を検査する作業は次の一手。ただし md_3 の patch は OPT=1 かつ PROMOTION=1 を扱えない (これは今回 build 不能なので影響しない)。
- **LLC miss 率の飽和:** perf が使えず未判定。N は RSS 下限の選択であって飽和点ではない。
- **between-run floor:** D145 の意味の floor ではない。時間窓は約 1 時間の 1 つ。
- **選抜の限界:** W1・W3・W4 は GC=10 で選んだ上位 2 点だけを GC 掃引した。他の genome が別の GC で最速になる可能性は測っていない。rr50 だけは GC {10,100,1000} × 16 点を J1 で見た。
- **縮小梯子:** 計算予算 (合計 2 node 時間未満) のため、事前登録した梯子 R1 (J2 の上位 3 → 2)・R2 (J2 の GC 格子から 1 µs を外す)・R3 (J1 の反復 3 → 2) を結果を見る前の式どおりに適用した。R4 (W4 の J2 を W3 の選抜で作る) は実装しておらず、使っていない。
- **workload の範囲:** skew 0.9 だけ (uniform なし)。長い tx は「全 thread の全 tx が 100 操作」の 1 型だけで、短い tx と混ぜる型・読み取り後に待つ型は stock では作れなかった。
- **測れた空間:** 24 点中 16 点。build できない 8 点が仮に速くても、stock の比較相手としては使えない。
- **作図と summary の束縛:** 作図器は summary の入力 path とセルの有無を照合し、値は生の runs.jsonl から再集計する。解析後に同じ path の中身が変われば summary と違う図を受理しうる (焦点再レビュー S06-C-3、実装しない)。今回の図は provenance の J1 96 セル・J2 48 セルが summary と一致することをレビューが確かめた。provenance は入力の sha256 を持つ。
- **private helper 依存:** build の依存準備は別 wave の `orchestrator/campaign/s3_mocc_lock_coverage` の private 関数を 1 箇所で使う。他 wave の変更で壊れうる (段 6 レビュー B-B8、受容)。

## 10. 論文の次の版に使える結論

- 構成 A (基準 Cicada) の設定: **`BACK_OFF=0, INLINE_VERSION_OPT=1, INLINE_VERSION_PROMOTION=0, REUSE_VERSION=1, WRITE_LATEST_ONLY=0`、gc_inter_us 10〜100 µs** (rr5・rr50・rr95)。100 操作型は `BACK_OFF=0, INLINE_VERSION_OPT=0, INLINE_VERSION_PROMOTION=0, REUSE_VERSION=0, WRITE_LATEST_ONLY=0`。いずれも正しさ未検証。
- md_6 (forwarding 試作、2026-09-29 13:02 JST 時点の local main に着地、`output/insights/2026-09-29/vhash-forwarding-prototype/README.md`) の条件 (48 thread・1M・skew 0.9・rr50・GC {10,100,1000}) はこの wave の N と一致する。md_6 の driver は genome の -D を渡さない CMake 既定の build で stock を測っている (`orchestrator/campaign/vhash_forwarding_prototype.py` の configure 引数は mocc の STOCK_G だけを除き、Cicada の cache option を渡さない) ので、その stock は CMake 既定 (BACK_OFF=1、INLINE_VERSION_OPT=0、INLINE_VERSION_PROMOTION=1、REUSE_VERSION=1、WRITE_LATEST_ONLY=0) で、この wave の control と data path 上同じ設定 (OPT=0 では PROMOTION の値は data path を変えない) であり、rr50 では最良より約 4.5 倍遅い Cicada である。**forwarding の効果を論文で比べるときは、上の最良設定を土台に測り直す必要がある。** (md_6 の C / F と stock の差の結論自体を否定するものではない — 同じ土台どうしの比較だから。)
- 図 §28.1 (GC 間隔と throughput) の基準線は図 (b)。
- 「GC 間隔を不適切に大きくした Cicada」は GC 10,000 µs で最良設定が自身の最高値から 8〜42% (rr5〜rr95 では 20〜42%) 落ちた Cicada、と数値で示せる。

## 11. 計算と工程

計算ノードの job (NQSV の Elapse):

| job | request | Elapse | 結果 |
|---|---|---:|---|
| J0 (cicada-j0) | 34458 | 18 s | 並列 build の masstree 競合 (推定) で失敗 → fix-2 |
| J0b | 34586 | 32 s | 待機 build が compile 不能で J0 全体停止 → fix-3 |
| J0c | 34682 | 344 s | 完了 |
| J1-0・1・2・3 | 34777・34778・34776・34775 | 424・33・305・33 s | 1・3 は OPT1 P1 の build 不能で失敗 |
| J1-13 (1・3 の再編) | 34820 | 254 s | 完了 |
| J2-0〜3 | 34871〜34874 | 165・214・164・166 s | 完了 |

計測の Elapse 合計 2,152 s = 35.9 node 分 (開発検査は §12)。

## 12. 工程・レビュー・変異

- 段 2 plan 1・段 3 相談 2 (規律と正しさの境界 / 実効性・過剰・見積り): must-fix 5 件をすべて採用 (GC=10 選抜の限界の明記と rr50 の全点 GC 3 点、J1 探索と J2 確認の分離、表示値でなく compile command での binding、後続比較の共通条件、見積り)。最良設定の正しさ検査は scope 外として次の一手。逐語は job dir の consult-a.md・consult-b.md・s4-ruling.md。
- 段 5 author 1 + fix 7 巡 (fix-1: Cicada は表示行を印字しない / fix-2: 並列 build の masstree 競合と build ログ / fix-3: 待機 build の compile 不能を W5 欠測として続行 / fix-4・4b: 段 6 レビュー所見 / fix-5: build 不能 genome の作図 / fix-6: 実データ桁の重なり / fix-7: 凡例と番号)。fix-4 は従属する期待の許可を書き漏らし子が停止した (F733 の再発)。
- 段 6 レビュー 2 (測定と集計 / 過剰・削除) と焦点再レビュー 1。焦点再レビューの must-fix 1 (§6 の GC 低下率の範囲の誤り「13〜42%」→「8〜42%」) と should 1 (REUSE=0 の RSS の記述範囲) を本文で直した。作図の summary 束縛 (S06-C-3) は §9 に限界として書いた。
- 変異 (M1〜M9、`tools/mutation_worktree.py`、独立 clone・commit `cdd14ea8f`、dispatch): 9 件すべて事前登録どおり KILLED、baseline 緑。login 自走で期待 node を集め、最終 commit で再確認した。M1 は fix-5〜7 の作図 test 追加で期待 node が変わったので最終 commit の観測で再登録した (旧期待は job dir の mutation-spec-v1-erratum-M1.json と mutation-erratum.md)。M1 は列挙と内部防壁 (24 点でなければ停止) の両層変異として事前登録した。harness の duration (queue 待ち込みの上限): baseline 33 s、M1 479 s・M2 452 s (queue 待ち)、M3〜M9 各 32〜33 s、合計 1,159 s。
