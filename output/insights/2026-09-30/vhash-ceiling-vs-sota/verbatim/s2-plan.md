# 段 2 実装計画

**段 3 で最初に攻撃する前提は P1 の trace 木です。** 親の実測は `pin→trace→ro-gcflag-workload→V` までを示しますが、trace 上の IGC・FWD までは示していません。そこを `git apply --check` で確認するまで、両腕の正しさ検査を実行可能と見なさないでください。以下は静的検査による計画です。テスト、ビルド、計測は実行していません。

## 1. workload patch — 単位 A

新設する [cicada-ceiling-workload.patch](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-vhash-ceiling-vs-sota/patches/cicada-ceiling-workload.patch) の契約を次で固定します。

| 項目 | 実装契約と根拠 |
|---|---|
| macro | `IZANAGI_CICADA_CEILING_WORKLOAD`、値は 0/1、未定義・0 は完全 inert。`#if` は owner `cc/cicada/ycsb_cicada.cc` に **2 行**、companion `include/ycsb.hh` に **2 行**を置く。[既存 gate 登録例](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-vhash-ceiling-vs-sota/orchestrator/campaign/condition_meaning_gate.py:92) に合わせる。 |
| flag | `--izanagi_ceiling_ronly_pct=0..100` を通常 worker の tx 単位に適用。`--batch_th_num=0/1` と `--batch_max_ope=1000` は既存 flag を使い、新 flag を増やさない。[common.hh](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-vhash-ceiling-vs-sota/external/ccbench/cc/cicada/include/common.hh:65)、[util.cc](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-vhash-ceiling-vs-sota/external/ccbench/cc/cicada/util.cc:21)。 |
| 生成 | [ycsb.hh](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-vhash-ceiling-vs-sota/external/ccbench/include/ycsb.hh:102) の `makeProcedure` 直後に 1 個の `#if` を置く。`thid_ >= FLAGS_thread_num` なら `pro_set_` を 1,000 read に作り直す。通常 worker は指定率の抽選後、read-only なら全操作を read、更新なら最低 1 write にする。最後に先頭 `Procedure` の `ronly_`・`wonly_` を再計算する。[既存の同種処理](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-vhash-ceiling-vs-sota/patches/instr-cicada-version-lifetime.patch:421) は意味の参考に留める。 |
| commit | [ycsb.hh](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-vhash-ceiling-vs-sota/external/ccbench/include/ycsb.hh:106) が `tx.is_ronly_` を設定し、[transaction.cc](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-vhash-ceiling-vs-sota/external/ccbench/cc/cicada/transaction.cc:934) の read-only commit に入る。retry は既存の `RETRY` へ戻り、同じ手続きを保持する。新 patch は `transaction.cc` に触れない。 |
| 完了数 | **P3 を採用。** [ycsb.hh](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-vhash-ceiling-vs-sota/external/ccbench/include/ycsb.hh:166) が成功時に既に増やす `local_commit_counts_` を使う。[runner.hh](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-vhash-ceiling-vs-sota/external/ccbench/common/runner.hh:300) の join 後、[ycsb_cicada.cc](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-vhash-ceiling-vs-sota/external/ccbench/cc/cicada/ycsb_cicada.cc:54) の `return 0` 直前で batch worker の slot だけを読む。`IZANAGI_CICADA_CEILING_WORKLOAD_V1 {"schema":1,"batch_threads":1,"batch_ops":1000,"batch_commits":N}` をちょうど 1 行出す。hot path に計数を足さず、perf build でも長い読み手の完了を検出できる。`batch_th_num=0` では `batch_commits=0`。 |

`ycsb_cicada.cc` のもう一つの `#if` は [using namespace std](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-vhash-ceiling-vs-sota/external/ccbench/cc/cicada/ycsb_cicada.cc:21) 直後に flag 定義を置く。header 側のもう一つは [flag 宣言の終端](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-vhash-ceiling-vs-sota/external/ccbench/include/ycsb.hh:33) の直後に置く。

**適用順は workload patch を最後**にする。`pin→V→workload`、`pin→V→IGC→workload`、`pin→V→FWD→workload`、`pin→trace→V→workload`、および trace 上の IGC・FWD の順で、各段に `git apply --check` と `git apply` を使う。GNU patch の fuzz 0 は判定に使わない。[IGC の変更 hunk](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-vhash-ceiling-vs-sota/patches/cicada-interval-gc-variant.patch:129) は `transaction.cc` と複数 header、[FWD の変更 hunk](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-vhash-ceiling-vs-sota/patches/cicada-forwarding-variant.patch:366) は `ycsb_cicada.cc` の先頭と runner 呼出し周辺に及ぶ。したがって新 patch の `ycsb_cicada.cc` 末尾 hunk は `return 0` と catch を短い文脈にし、FWD が変える [runner 呼出し](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-vhash-ceiling-vs-sota/patches/cicada-forwarding-variant.patch:514) を文脈に含めない。trace は [main 冒頭](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-vhash-ceiling-vs-sota/patches/instr-cicada-trace.patch:134) を変更するため、ここも hunk 文脈を避ける。`include/ycsb.hh` は IGC・FWD が触らない一方、既存 rogc workload patch とは重なるため、後者をこの行列へ混ぜない。

## 2. 条件 gate と pin 閉包 — 単位 A

[condition_meaning_gate.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-vhash-ceiling-vs-sota/orchestrator/campaign/condition_meaning_gate.py:92) に `DefineSpec(ROUTE_CMAKE_CXX_FLAGS, _CICADA_YCSB_OWNER, "ycsb_cicada.exe", "patches/cicada-ceiling-workload.patch", inert_values=("0",))`、[owner witness](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-vhash-ceiling-vs-sota/orchestrator/campaign/condition_meaning_gate.py:448) に `#if IZANAGI_CICADA_CEILING_WORKLOAD`、[site count](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-vhash-ceiling-vs-sota/orchestrator/campaign/condition_meaning_gate.py:659) に owner の 2、[companion](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-vhash-ceiling-vs-sota/orchestrator/campaign/condition_meaning_gate.py:678) に header の 2 を登録する。`#if` の行数は完成 patch の追加行から数え直す。

閉包は [screening_driver.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-vhash-ceiling-vs-sota/orchestrator/campaign/screening_driver.py:78)、[test_condition_meaning_gate.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-vhash-ceiling-vs-sota/orchestrator/tests/test_condition_meaning_gate.py:50) の macro 一覧・fixture・特殊 patch 扱い（209、496、552、1627、1676、3602、3686 行付近）、[test_p3_s4_loop.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-vhash-ceiling-vs-sota/orchestrator/tests/test_p3_s4_loop.py:8557) の裸 macro allowlist、[test_screening_driver.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-vhash-ceiling-vs-sota/orchestrator/tests/test_screening_driver.py:680) の macro 一覧と既定値を追随させる。[総和 pin](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-vhash-ceiling-vs-sota/orchestrator/tests/test_condition_meaning_gate.py:1279) は現在の 298 に完成 patch の **owner site 数**を足す。companion site は別登録であり、この総和へ二重に足さない。[CXX flags 登録件数 pin](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-vhash-ceiling-vs-sota/orchestrator/tests/test_condition_meaning_gate.py:3831) も 1 増やす。

新 patch の用途と適用順を [patches/README.md](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-vhash-ceiling-vs-sota/patches/README.md:450) に記す。

## 3. driver — 単位 B

新設 [vhash_ceiling_vs_sota.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-vhash-ceiling-vs-sota/orchestrator/campaign/vhash_ceiling_vs_sota.py) は `smoke / verify / prelim / diag / compare / aggregate` を持つ。source copy、逐次 `git apply`、condition gate、build、実行、trace 判定は [vhash_ro_gc_publish.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-vhash-ceiling-vs-sota/orchestrator/campaign/vhash_ro_gc_publish.py:155) の構造を使い、genome は [vhash_cicada_vlife.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-vhash-ceiling-vs-sota/orchestrator/campaign/vhash_cicada_vlife.py:59) の `tuned` と `verify_genome_commands` に束縛する。全腕で同じ tuned genome を使い、S だけ ro-gcflag を無効にする。

| 点 | 条件 | 予備の腕 |
|---|---|---|
| P1 | rr5、ro 0%、48 通常 worker、skew .6、batchR 1 | S、R、IGC mode 3、IGC mode 1 |
| P2 | P1 の skew .9 | 上記と C-min K=1 |
| P3 | P1 の skew .97 | 上記と C-min K=1 |
| P4 | rr50、ro 95%、12 通常 worker、skew .9、batchR 0 | S、R |

各点は record 100 万、値 4 B、通常 tx 10 操作、batchR は 1,000 read。[flag 組立ての既存例](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-vhash-ceiling-vs-sota/orchestrator/campaign/vhash_ro_gc_publish.py:235) を基にする。hot v2 の K=1・8 は着地した場合だけ追加し、E は修理版が着地した場合だけ依頼の待機型 2 点を追加する。旧 E や hot v1 で欠測を埋めない。

build は **木 × genome × 腕の compile macro × 用途**で識別する。S は pin＋workload、R は pin＋V＋workload、IGC は R＋IGC＋workload、C は R＋FWD＋workload。IGC mode 1/3 と C の K は実行時 flag なので同一用途内で binary を共用する。perf は workload・必要な機構 macro のみ、diag は対応する `IZANAGI_CICADA_RO_GCFLAG_COUNT`・`CICADA_INTERVAL_COUNT`・`CICADA_FWD_COUNT`、trace は `TRACE` を加えた別 build とする。[既存の禁止関数](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-vhash-ceiling-vs-sota/orchestrator/campaign/vhash_ro_gc_publish.py:119) を拡張し、perf に TRACE、VLIFE、名前に `COUNT` を含む macro、`ADD_ANALYSIS` があれば拒否する。build manifest の macro と compile command の実値を照合する。

**GC 間隔の固定規則:** 予備は全腕を 10・100 µs の双方で 3 round × 10 秒走らせる。点ごとに R の `throughput[tps]` 中央値だけで高い間隔を選ぶ。同値は事前に 10 µs と定める。以後、その点の全腕を選んだ間隔で比較し、別間隔の腕/R 比を採用しない。これは依頼の「相手側で先に選んで点ごとに固定」に合う。ただし R を見て選ぶ手順を予備の腕結果から独立させ、30 秒比較前に選択と入力 SHA を記録する。大きな勝ちが出た点は R の追加調整後に再比較する。

job は **点 × GC 間隔 × round**で予備を分割する。各 job に同じ点の全腕を入れ、round ごとに腕順を回転・逆順化して位置を均衡させる。基礎行列は 16 腕セル × 2 間隔 × 3 round = 96 走、24 job、各 job は 2〜5 条件で実行時間 20〜50 秒＋起動費用。30 秒比較は点 × round の 12 job、各 4〜5 条件で 120〜150 秒＋起動費用。driver は投入前に各 job の**直列条件数・run 秒・見積り総秒**を出し、1 node 1 job、node local `TMPDIR`、共有 repo への書込みなしとする。[単独性の既存呼出し](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-vhash-ceiling-vs-sota/orchestrator/campaign/vhash_ro_gc_publish.py:251) を使い、残存 benchmark process は次の走行を拒否する。

raw は JSONL で、`schema, command, point, gc_inter_us, arm, round, order, duration_s, flags, genome_witness, build_macro, binary_sha256, patch_sha256, node, started_at, ended_at, rc, stdout_path, stderr_path, throughput_tps, batch_commits, verifier` を必須とする。parser は [parse_bench_stdout](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-vhash-ceiling-vs-sota/orchestrator/campaign/vhash_ro_gc_publish.py:300) と新しい workload V1 行を読み、欠落・重複・JSON 重複 key・負値・flag と記録の食い違いを拒否する。P1〜P3 で `batch_commits=0` の走行は勝ちに数えない。

腕/R は**同一 point・GC・round・node の対**で `arm_tps / R_tps` を計算し、その比の中央値を取る。集約済み TPS の比は使わない。有望点は予備の eligible 腕/R 比の最大値が最も高い P1〜P3、同点は P2→P3→P1 の事前順で選ぶ。隣接点は skew 順の直近を選び、P2 なら P3、P1 なら P2、P3 なら P2 と固定する。全敗でも P2 を代表点として残す。選んだ 2 点で**新しい** 6 round × 30 秒を走らせ、代表点 ≥1.5、隣接 ≥1.3、完了・正しさ条件を照合する。P4 は read-only 指定自体の対照として報告し、長い読み手の隣接点にしない。

診断は [ro-gcflag count](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-vhash-ceiling-vs-sota/patches/cicada-ro-gcflag-variant.patch:19) の公開回数、[IGC count](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-vhash-ceiling-vs-sota/patches/cicada-interval-gc-variant.patch:236) の `pruned`・`chain_versions`・`reuse_pool`・hops、[FWD count](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-vhash-ceiling-vs-sota/patches/cicada-forwarding-variant.patch:48) の trigger・attempt・success・position、全用途共通の `batch_commits` を読む。R/C で IGC の `chain_versions` と同等の総版数をこの macro 群だけから得られるとは扱わず、その列は欠測として明記する。VLIFE を使う追加診断は既存 IGC/FWD と patch 衝突するため、成立する木だけに限定する。

trace は各機構腕と workload の組を [既存 verify 呼出し](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-vhash-ceiling-vs-sota/orchestrator/campaign/vhash_ro_gc_publish.py:304) と同じ判定器へ渡す。C 行数＝commit 数、巡回 0、integrity 0、`READ_WTS_MISMATCH=0` を要求する。rc 1 は失格、rc 3 は upper-bound indeterminate と表記し certified にしない。

## 4. test — 単位 B

新設 `orchestrator/tests/test_vhash_ceiling_vs_sota.py` に、少なくとも次を置く。

- **正例:** 4 点の flag、tuned genome 束縛、IGC mode 1/3 の build 共用、workload V1 の厳密 parse、同一 round の比、R の中央値による GC 固定、腕順の位置均衡、全敗時 P2 選択、verify の rc 0。
- **負例:** perf build に TRACE・VLIFE・各 COUNT 混入、macro manifest と compile command の不一致、異なる round/node/GC の比、batchR 完了 0、欠落・重複・負値の出力、検証 rc 1、rc 3 を certified とする誤り、trace の C 行不一致、単独性違反、5 分超または 2 node 時間以上の見積り。
- **結合面:** [materializer_admission.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-vhash-ceiling-vs-sota/orchestrator/campaign/materializer_admission.py:118) に新 build 関数を diagnostic 登録し、[spawn sites](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-vhash-ceiling-vs-sota/orchestrator/tests/test_ccbench_spawn_sites.py:87)、[perf closure](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-vhash-ceiling-vs-sota/orchestrator/tests/test_official_perf_closure.py:46)、[build authority CLI](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-vhash-ceiling-vs-sota/orchestrator/tests/test_p3_build_authority_cli.py:161)、[test README](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-vhash-ceiling-vs-sota/orchestrator/tests/README.md:193) の発見・登録面を追随する。

## 5. 作図器 — 単位 B

新設 `tools/plotting/plot_vhash_ceiling_vs_sota.py` は raw JSONL から対比を再計算し、点ごとの腕/R 比と 95% CI、R の GC 選択、batchR 完了数を見える形にする。PNG・PDF・`<図>.provenance.json` に入力 SHA256、条件、主要値を残す。[FIGURE_CONVENTIONS.md](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-vhash-ceiling-vs-sota/tools/plotting/FIGURE_CONVENTIONS.md:24) の小標本 CI、[provenance](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-vhash-ceiling-vs-sota/tools/plotting/FIGURE_CONVENTIONS.md:68)、[保存前の重なり検査](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-vhash-ceiling-vs-sota/tools/plotting/FIGURE_CONVENTIONS.md:85) に従う。テストは全点・全腕・両 GC・6 round の実寸 fixture で本物の matplotlib Figure を検査し、欠測 hot/E、重複 raw、異なる SHA、注釈の重なりを負例にする。作図は計測機の外で行う。

## 6. 腕の発火条件

| 腕 | P1〜P3 の長い読み手 | P4 |
|---|---|---|
| S | read-only commit 時の GC 公開が進まない stock 対照。batchR の完了を必ず確認する。 | ro 指定 95% の stock 対照。 |
| R | read-only commit でも GC 公開を進める。[ro-gcflag patch](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-vhash-ceiling-vs-sota/patches/cicada-ro-gcflag-variant.patch:28)。長い読み手が保持する版の費用は残りうる。 | 修正自体の効果を検出する主対照。 |
| R+C-min K=1 | [FWD の条件](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-vhash-ceiling-vs-sota/patches/cicada-forwarding-variant.patch:137) が `!this->is_ronly_` なので batchR 自身は前進しない。通常の更新 tx が深い版列を読む P2/P3 でだけ発火を期待する。 | 対象腕に含めない。 |
| R+IGC mode 3 | 剪定を呼ばず install 経路を通る対照。[IGC patch](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-vhash-ceiling-vs-sota/patches/cicada-interval-gc-variant.patch:548)。 | 対象腕に含めない。 |
| R+IGC mode 1 | 保護点の間の版を剪定する。batchR の可視版を残したまま版列・費用が減るかを見る。 | 対象腕に含めない。 |

修理版 E が後日入っても、[GC 接続の read-only 除外](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-vhash-ceiling-vs-sota/patches/cicada-forwarding-gc.patch:435) のため batchR を RA 外で前進させる腕にはならない。E は依頼の待機型更新 tx 2 点だけに適用する。

## 7. 計算見積りと削り順

基礎 build は S/R/C/IGC の perf・trace と必要な diag で約 11〜12 本。hot/E が着地した場合と smoke を含む上限計画は依頼の **約 25 本**。親の実測 22.6 秒/本なら build 純時間は約 565 秒。masstree 競合があるため build 同士は直列化し、5 本前後ずつの shard に分ける。

基礎予備は 96 走 × 10 秒＝960 秒、30 秒比較は最大 2 点 × 5 腕 × 6 round × 30 秒＝1,800 秒。診断・verify の短走、build、起動・初期化費用を加え、投入前に driver が全 job の積算値を出す。現時点の純実行時間は約 3,325 秒に短走と起動費用を足すため、**2 node 時間以内という判定は smoke の実時間を入れて再計算するまで保留**する。上限を超えたら、未着地なら当然 hot/E を欠測、次に弱い追加腕、最後に長時間比較の第 2 点を削る。正しさ検査、R、batchR の代表点は削らない。[共通指示](/work/SFC/tanab/tmp/vhash-ceiling-2026-09-30/common.txt) の 2 node 時間以上なら投入前に止める条件を守る。

## 8. リスクと段 3 の攻撃対象

1. **trace 適用:** trace→V→IGC/FWD→workload の `git apply` と実 build は未確認。[trace patch](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-vhash-ceiling-vs-sota/patches/instr-cicada-trace.patch:104) と各機構の `transaction.cc` hunk が衝突する可能性を先に検査する。失敗した場合、既存 patch を編集して迂回しない。
2. **完了数の意味:** `local_commit_counts_` が batch worker でも 1 tx につき 1 増えることは [YCSB 成功経路](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-vhash-ceiling-vs-sota/external/ccbench/include/ycsb.hh:161) から読める。runner の集計前後で slot が変わらないこと、`batch_commits` と trace C 行が一致することを smoke/verify で攻撃する。
3. **機構の発火:** C は長い read-only tx を前進させない。IGC mode 3 は剪定しない。カウンタが 0 の腕に「機構が効いた」と書かない。
4. **比較の汚染:** GC 選択を腕の結果から行う、腕ごとに node を固定する、diag TPS を性能値に使う、batchR が完了しない勝ちを採用する、の各負例を test で拒否する。
5. **SOTA の穴:** md_18 の IGC 試作は Steam・HANA の性能代表ではない。[依頼原文](/work/SFC/tanab/tmp/vhash-ceiling-2026-09-30/request-md_42.txt) に沿い、一次資料では修正済み Cicada に対する結果と、区間 GC の文献上の未比較部分を分ける。

## 総括

- 単位 A の契約は macro 1 個、owner `#if` 2 行、header `#if` 2 行、完了数 V1 行 1 本。
- workload を `ycsb.hh` の手続き生成で作り、既存 read-only commit と commit 数を使う。
- 単位 B は同一 round の R 対、R だけで固定した GC 間隔、30 秒の新しい 6 round を判定の核にする。
- 基礎予備は 24 job・96 走、比較は最大 12 job・60 走。各 job の直列時間と総 node 時間を投入前に出す。
- trace 上の IGC・FWD 適用と build は未確認で、段 3 の最優先攻撃対象。
- 計画は静的検査のみ。テスト、ビルド、計測による受入結果は親が取得する。