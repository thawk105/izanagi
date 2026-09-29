# 段 4 裁定 — md_23 VHash hot block (構成 B) を Cicada に入れる

2026-09-29 22:45 JST / 親 (manager) / 入力: s1-brief.md、plan.md (段 2)、consult-a.md (正しさ境界)、consult-b.md (実効性・過剰)。
裁定 inbox の再走査: wave 開始後の更新は 2026-09-29-interactive-evolution-verdicts.md (研究の進め方、本件と無関係) だけ。main は 8fe87f852 から不動。

## 1. 所見の裁定

| 所見 | 判定 | 採否 | 裁定 |
|---|---|---|---|
| plan §2 / A2 / B P4: ABORTED を hot から外すと物理列との一致と later_ver が崩れる | real | 採用 | P4 を撤回。hot は物理列の先頭 K 件 (ABORTED・PENDING を含む) の写し。ABORTED は第 2 段で stock どおり飛ばす。評価計画草稿 §2 の R3 の数え方 (ABORTED を除く) とは違う — 草稿は未発効、構成 D を作る wave で「hot miss = 論理 K 境界」の対応を取り直すと一次資料に書く |
| plan P1 / A: 記述子を atomic に | real | 採用 | seq・件数・wts・ptr を std::atomic にする |
| A3: seqlock の読み順序 | real | 採用 | Boehm (2012) の形に固定: writer = seq を偶→奇へ CAS (acq_rel) → `atomic_thread_fence(release)` → 記述子を relaxed store → seq を奇→偶 (release store)。reader = s1 = seq.load(acquire)、奇数なら fallback → 記述子を relaxed load でローカルへ写す → `atomic_thread_fence(acquire)` → s2 = seq.load(relaxed) → s1≠s2 なら fallback。ptr の dereference は s2 確認の後だけ |
| A4 / B P6: GC と再利用の寿命論証 | real (論証不足) | 採用 | 論証を一次資料に書く: (i) reader が採る版は、seq 確認時点の物理列で stock の第 1 段が止まる版と同じ。(ii) GC の切り離し点 V は確定版で V.wts < MinRts ≤ reader の rts ≤ trts なので、V が hot 写しにあれば reader は V 以前で止まり、無ければ hot の全件が V より新しい。(iii) seq 確認の後、V2 (新しい切り離し点) が reader の選んだ版 X より新しく挿入されることは、ro では writer の wts > rts、update では V2.wts < MinRts ≤ rts < MinWts_at_begin となり V2 の writer は reader の開始前に終わっている、のでどちらも起きない。(iv) GC は hot から切り離し点より古い記述子を seq 書き区間の中で消してから gcAfterThisVersion で再利用する。(v) ThreadRtsArray を tx の途中で動かさない (stock のまま、md_14 の暗黙の不変条件)。これは stock の安全性への帰着であり、証明ではなく論証と書く。実機では trace (GC 10 µs の高頻度回収 cell を含む) で巡回 0 を確かめる |
| A5 / B2: K=2/4 に正しさ検査が無い | real | 採用 | trace を stock・K=1・2・4・8 の全腕で回す。性能値を載せる腕は全部 trace を通す |
| A6 / B3: gc_inter_us は snapshot の古さではない | real | 採用 | 軸名は「GC 間隔」。COUNT build で ro tx の snapshot 遅れ (begin 時の wts − rts、ts 単位と、換算できれば µs) と、第 1 段で飛ばした版数の分布を cell ごとに実測して併記する。「古い snapshot ほど効く」は実測の遅れで言える範囲だけ書く |
| A7 / B6: 0.94 node 時間は外挿 | real | 採用 | smoke で実測してから本走を決める (§4) |
| A8 / B9: 到達と検出の帰属は別 | real | 採用 | 壊しは md_3 と同じ事象記録 (reached / changed / committed を stderr の CICADA_BREAK_EVENT に全件) と帰属規則 (代表 witness の rw 辺が事象の txn・key・読んだ版に一致) で判定。帰属できない検出は成功に数えない (§3) |
| A9: inert の対象 TU | real | 採用 | ycsb_cicada target の全 TU (transaction.cc・util.cc・ycsb_cicada.cc) を macro なしで同じ argv の -E 比較 (空行と行 marker を除く)。共通 header include/ycsb.hh は触らない (下の P7) ので他 protocol の TU は変わらない |
| A10: 監査表の射程 | real (nit) | 採用 | 「版リンクの変更 site は全件」と射程を書き、scan (read_internal を通らない場合)・gc_records (Tuple の削除)・TPC-C は本 wave の検査対象外と明記 |
| A1 / B10: 条件 gate 登録は所有外 | real | 採用 (必要最小で行う) | patch に新しい #if があると登録簿 test が接頭辞に関係なく赤になり、build する driver は gate を通す必要がある (D2288 の理由と同じ)。依頼の「ledger・README の該当 entry」の延長として、自分の 3 macro と自分の driver の起動 site・materializer の登録行だけを足す。既存 entry・判定・受理述語は変えない。並走 wave (md_21 等) の登録と land で衝突したら両方の entry を残す。decisions fragment に「所有外の必要最小の登録」として記録する |
| B1: H1 の判定と混ぜない | real | 採用 | 一次資料・図の名前は「構成 B の探索的な同時刻比較」。草稿 H1 の主指標 (commit 当たり LLC miss) と確認段は本 wave で測らないと書く |
| B4: 長い ro tx を外す | real (限定) | 採用 | 長い tx は入れない (P8 維持)。結論は「短い YCSB tx の範囲」に限り、長い固定 snapshot は後続と書く |
| B5: ro 比率の実現負荷 | real | 採用 | COUNT build で実現 ro 比率・ro/update commit・abort を cell ごとに記録。性能 build の stdout の commit/abort も残す。因果の内訳とは書かない |
| B7: cell を node に閉じると node 効果が分からない | real | 採用 | round を node に割る: 各 perf job が全 12 cell × 全 5 腕を回し、job ごとに 2 round、3 job で 6 round |
| B8: COUNT に stock の対照が無い | real | 採用 | COUNT は stock (K=0 で第 1 段の hop を数える) も含む 5 腕 × 代表 4 cell × 1 走 |
| B11: driver の置き場 | 不成立 | — | orchestrator/campaign/ に置く (CCBench の patch・build・gate・計算ノード起動を担うので先例 md_6 と同じ) |
| plan B3 (later_ver を null にする壊し) | — | 条件付き | B1 が発火しても帰属できない場合だけ作る |
| plan の include/ycsb.hh への WL hunk | refuted (親) | 不採用 | 先例 md_15 は ro 抽選を transaction.cc の begin() で行い共通 header を触っていない (patches/instr-cicada-version-lifetime.patch の begin hunk)。本 patch も同じ形にし、条件 gate の owner TU を transaction.cc に揃える |

## 2. plan v2 (確定)

### 2.1 patch の設計 (patches/cicada-vhash-hot-block-variant.patch、pin C 68106660 の cc/cicada だけ)
- macro (IZANAGI_ 接頭辞なし、未定義 = 0 = stock と前処理一致):
  - `CICADA_VHASH_K` ∈ {0,1,2,4,8}。0 は stock。K>0 で hot を持つ。K の値ごとに別 binary。それ以外の値は `#error`。
  - `CICADA_VHASH_COUNT` ∈ {0,1}。診断計数 (性能値に使わない)。K=0 でも有効 (stock 経路の第 1 段の hop 数を数える)。
  - `CICADA_VHASH_WL` ∈ {0,1}。実行時 flag `--vhash_ronly_pct` (int、既定 -1 = YCSB の生成のまま、0〜100) を定義。stock 対照を含む全腕をこの macro つきで build する。
  - 分岐は owner TU cc/cicada/transaction.cc とそれが include する cc/cicada/include/{tuple.hh,transaction.hh} にだけ置く。ycsb_cicada.cc・util.cc・共通 include/ は触らない。各挿入ブロックの後に無条件 `#line <pin の次行>`。
- Tuple (include/tuple.hh): `#if CICADA_VHASH_K` の中で `std::atomic<uint64_t> vh_seq_`、`std::atomic<uint32_t> vh_n_`、`std::atomic<uint64_t> vh_wts_[K]`、`std::atomic<Version*> vh_ptr_[K]` を latest_ の直後に置く (配置は実装子が alignment と共に報告)。init 2 種で Tuple 公開前に 1 件 (初期版; INLINE_VERSION_OPT=1 なら &inline_ver_) を入れる。
- reader (transaction.cc read_internal の第 1 段 :100-107 だけを置換): §1 A3 の手順で写し、wts ≤ trts の最初の記述子 i を選ぶ。ver = ptr[i]、later_ver = (i>0 ? ptr[i-1] : nullptr)。全件が新しすぎれば ver = ptr[n-1] から stock のループ (wts > trts の間 next) を続ける (later_ver も stock どおり更新)。fallback は stock の第 1 段をそのまま。第 2 段以降・read_set_ 記録は stock と同一。SINGLE_EXEC=1 の枝は触らない。
- writer (validation の Install :479-530): 各 write-set 要素ごとに、位置探索と CAS (先頭・途中の両方) を hot 書き区間の中で行い、CAS 成功時は挿入位置 p (新版の新しい方から数えた位置) < K なら shift 挿入 (溢れた末尾は捨てる、cold は列に残る)、p ≥ K なら不変。CAS 失敗でも区間を必ず閉じて再試行。早期 abort の `goto FINISH_VALIDATION` に区間を持ち込まない (区間を helper/scope に閉じる)。insert 経路 (新 tuple) は Tuple::init で済む。
- abort (writeSetClean): hot は変えない。
- GC (gc_versions): gc_lock_ 取得の後、`ver_->next_ = nullptr` の前に hot 書き区間を開き、切り離し点 (ver_) より古い記述子を消し、next_ の切断と min_wts_ 更新の後に区間を閉じ、その後で gcAfterThisVersion。lock 順は gc_lock_ → hot の一方向。
- COUNT (診断): thread ごとに、read の hot 採用・fallback (奇数 / 変化)・hot 外れで cold へ出た回数・第 1 段で飛ばした版数の分布 (0,1,2,3,4-7,8-15,16+)、ro の snapshot 遅れ (wts_.ts_ − rts_ の分布)、実現 ro / update の commit と abort、install ごとの hot 区間の保持と待ちの rdtscp サイクル、GC の区間の保持サイクル。終了時に 1 行 JSON `CICADA_VHASH_COUNT_JSON {...}` を stdout へ (出力の置き場は owner TU の静的オブジェクトの destructor 等、先例 instr-cicada-version-lifetime の方式)。
- TRACE: instr-cicada-trace.patch の上に重なる (pin → instr-cicada-trace.patch → 本 patch の厳密適用が通ること、pin → 本 patch 単独も通ること)。trace 用 build は INLINE_VERSION_OPT=1・INLINE_VERSION_PROMOTION=0。

### 2.2 壊し patch (本 patch の上にだけ重ねる無条件 patch、裸 macro なし、D2279 の形)
- B1 `patches/broken-cicada-vhash-stale-hot.patch`: hot 採用の読みで、選んだ記述子 i の 1 つ古い記述子 i+1 が存在し確定版なら、ro tx の読みの一部 (決定的な間引き、例: key の下位 bit) でそちらを返す。事象を reached / changed / committed で stderr に全件。**検出を期待** (ro は validation を持たない)。帰属できれば「1 本以上検出」を満たす。
- B2 `patches/broken-cicada-vhash-skip-pending.patch`: hot 採用の読みで、選んだ記述子の版が PENDING なら待たずに次の記述子 (無ければ列の next) の確定版へ進む。later_ver は物理の直前 (飛ばした PENDING 版)。**事前の予測 (結果前に登録)**: ro tx では PENDING 版の wts は rts より大きく (進行中の writer の wts ≥ MinWts > rts) 到達 0。update tx では validation (a) が later_ver = 飛ばした版から辿り直し、その版が確定すれば不一致で abort、abort なら同じ版に戻るので、committed な古い読みは 0 と予測。予測どおりなら「validation (a) に止められた (到達 n、changed n、committed 0)」と書き、検出には数えない。予測が外れて巡回が出たら帰属を照合して書く。
- B3 (条件付き): B1 が発火して committed 事象があるのに帰属 0 のときだけ、later_ver を nullptr にする壊しを足す。

### 2.3 driver と計算
- 置き場: `orchestrator/campaign/vhash_cicada_hot_block.py` + `orchestrator/tests/test_vhash_cicada_hot_block.py`、作図 `tools/plotting/plot_vhash_cicada_hot_block.py`。vhash_forwarding_prototype.py (md_21 所有、編集中) を import しない — 必要な手順は共有 module (buildcache・condition_meaning_gate・patchharness 等) から直接使うか自分の file に写す。
- subcommand: `build` (1 job: dependency build → 全 binary の build → inert の -E 比較 → gate の supply/meaning → binary を scratch へ置き sha256 と compile command を manifest へ)、`perf --job-index {0,1,2}` (manifest の sha256 を照合して走る)、`count`、`trace --job-index {0,1}`、`smoke`、`aggregate --raw ...`。build を 1 回にし、他 job は manifest を読む (build を node ごとに繰り返さない)。
- build 一覧: perf {stock(K=0), K1, K2, K4, K8} × WL=1、COUNT=0、TRACE=0、ADD_ANALYSIS=0 / COUNT {K0,1,2,4,8} × WL=1・COUNT=1 / trace {K0,1,2,4,8} × WL=1・TRACE=1 + B1・B2 (K=4 の trace 版に重ねる) = 17 binary (+ dependency)。
- 共通 argv: 48 thread、ycsb_tuple_num=1,000,000、zipf 0.9、ycsb_max_ope 10、ycsb_rmw 0、extime 3、clocks_per_us 2100。build 定数: BACK_OFF=0、INLINE_VERSION_OPT=1、INLINE_VERSION_PROMOTION=0、REUSE_VERSION=1、WRITE_LATEST_ONLY=0 (md_11 の観測最良)。
- 格子 (12 cell): (a) ro 格子 9 = vhash_ronly_pct {0,50,95} × gc_inter_us {10,1000,100000}、ycsb_rratio 50 (update tx の中の読み比)。(b) 通常 YCSB 3 = rr5 (gc 100)、rr50 (gc 100)、rr95 (gc 10)、vhash_ronly_pct -1。効かないはずの条件 = ro 0 の 3 cell と rr5。
- perf: 3 job × 各 2 round × 12 cell × 5 腕 = 360 run。round 内で cell ごとに 5 腕を回し、腕の順は round と cell で巡回 (ラテン方格的な回転)。stdout の throughput・commit・abort、wait4 の maxrss、elapsed を記録。
- COUNT: 1 job、代表 4 cell (ro95-gc100000、ro95-gc10、ro0-gc10、rr50) × 5 腕 × 1 走 = 20 run。
- trace: 2 job。md_3 の設定 (ycsb_tuple_num 200、zipf 0.9、extime 1、group_commit 0、SINGLE_EXEC 0、IZANAGI_TRACE_DIR) で、cell T1 = ro95・gc 100000・rr50、T2 = ro50・gc 10・rr50、T3 = md_3 の cell W (rratio 0、rmw true、max_ope 5、ro −1) の 3 cell × 5 腕 = 15 走 + B1・B2 × (T1, T2) = 4 走。判定器 `python -m verifier <dir> --json --quiet --protocol cicada --ccbench-root <src> --expected-commits N`、rc 0/1/3 を判定結果、2 を失敗。巡回が出た腕は即失格 (その腕の性能値は図に出さず失格と書く)。
- node: 同時に最大 6 node (build 完了後に perf 3・count 1・trace 2)。gen_S の node 専有で他 wave と同居しない。job 冒頭で他ユーザー・他 wave の process の不在を pgrep で記録。
- 集計: 同一 job・同一 round・同一 cell の K/stock 比。cell ごとに 6 round の比の全点・中央値・範囲 (最小〜最大) を出す。有意・一般化は書かない (探索段)。メモリは maxrss の腕間差と解析値 N × sizeof の増分 (sizeof は build 時に static_assert か出力で実測) を並べる。
- 図 (生成器付き、計測機の外): fig-k (K × throughput 比、cell 別)、fig-ro (ro 比率 × 利得、GC 間隔別)、fig-write (update 中心 cell の throughput 比 + COUNT の hot 区間サイクル/commit)。

## 3. 正しさの門と完了判定 (結果前に固定)
- 全 5 腕 × T1〜T3 で判定器が巡回 0 (上限 indeterminate)、trace の C 行 = ベンチの commit 数 (integrity)。1 つでも巡回 → その腕は失格、性能表から外し理由を書く。
- B1: committed 事象 ≥ 1 かつ判定 non-serializable かつ代表 witness のうち ≥ 1 件が事象に帰属 → 「検出」。どれかが欠ければ「未検出」と書き、B3 を条件どおり試す。
- B2: §2.2 の予測を照合して書く。
- inert: macro なしで 3 TU の -E 比較が一致。性能 binary の compile command に TRACE=1・CICADA_VHASH_COUNT=1・ADD_ANALYSIS=1 が無いこと。

## 4. 計算量と縮小梯子 (結果前に固定)
- 投入順: smoke (1 job: build 全部 + 各 perf 腕を ro95-gc100000 と rr5 で 1 走ずつ + trace K8 の T1 1 走 + 判定) → 実 Elapse から全体を再見積り → 本走。
- 見積りの式: 合計 = build job の Elapse + 3 × (perf 1 job の予測) + count + 2 × (trace 1 job の予測)。perf 1 job の予測 = 120 run × smoke で測った 1 run の最大 wall (遅い cell) + 60 s。trace 1 job の予測 = 走数 × smoke の trace 1 走 (build 除く、判定込み) の wall。
- smoke を含む合計が 7,200 node 秒以上なら結果を見ずに次の順で縮める: (1) perf の round を 6 → 4 (job 2 本)、(2) ro 格子を ro {0,95} × gc {10,100000} の 4 cell へ、(3) K を {1,8} へ、(4) なお超えれば投入せず見積りを一次資料に書いて停止。
- 1 job の walltime は予測 × 2 + 10 分。`--overall-grace` は `--queue-wait-timeout` 以上。

## 5. 変異の事前登録 (driver 側、DW-M01。anchor は実装後に確定し、単一理由性を確認できない変異は登録しない)
- M1: aggregate が perf_eligible でない run (COUNT/trace build) を throughput 表へ入れる → test 赤。
- M2: run 前の binary sha256 の照合を外す → test 赤。
- M3: K/stock 比の対が別 round (または別 job) の stock と組む → test 赤。
- M4: round × cell × 腕の欠け・重複を黙って捨てる → test 赤 (fail-closed であること)。
- M5: 判定器 rc 1 (巡回) の腕を失格にしない → test 赤。
- M6: 縮小梯子の順序を入れ替える (または閾値 7,200 を緩める) → test 赤。
- 各変異は「同じ入力を拒否する層が前後・内側に無く赤理由が 1 つ」を実装後に確認する。

## 6. 実装単位 (所有は素集合、並列投入)
- U1 (C++): patches/cicada-vhash-hot-block-variant.patch、patches/broken-cicada-vhash-stale-hot.patch、patches/broken-cicada-vhash-skip-pending.patch、patches/README.md (新しい節 1 つと壊し patch の表の行)。条件 gate 登録: orchestrator/campaign/condition_meaning_gate.py (DEFINE_SPECS・witness・site 数に 3 macro)、orchestrator/campaign/screening_driver.py (_CONDITION_DEFAULTS に 3 macro の既定 0)、orchestrator/tests/test_condition_meaning_gate.py、orchestrator/tests/test_p3_s4_loop.py (allowed_non_variant_tokens に本 patch の登録、要否は実物で判断)。login で「pin → 本 patch」「pin → instr-cicada-trace.patch → 本 patch」「+ B1」「+ B2」の厳密適用 (git apply --check、fuzz なし) と、macro なし・各 K の compile (login で可能な範囲: -fsyntax-only か実 build) を確かめる。
- U2 (Python): orchestrator/campaign/vhash_cicada_hot_block.py、orchestrator/tests/test_vhash_cicada_hot_block.py、tools/plotting/plot_vhash_cicada_hot_block.py、起動 site・materializer の登録 (orchestrator/campaign/materializer_admission.py、orchestrator/tests/test_ccbench_spawn_sites.py、orchestrator/tests/test_p3_build_authority_cli.py)。U1 の macro 名・flag 名・COUNT JSON の形 (§2.1) をこの裁定で固定済みとして並列に書く。
- 規模上限の目安: patch 本体 ≤ 700 行、driver ≤ 1,000 行、test ≤ 600 行。超えたら理由を報告。
- 親がやる: 統合 commit、計算ノード投入、一次資料・fragment・図の生成と commit、受入、land。

## 7. 研究前進と限界 (一次資料に書く枠)
- 言えるようになること: Cicada の中で構成 B (hot の記述子 K 個) を動かし、短い YCSB tx の範囲で K・ro 比率・GC 間隔ごとの throughput 比、書き込み側の費用、メモリ増、探索の短縮と snapshot 遅れの実測を、同時刻の stock 対照つきで示す。正しさは判定器で巡回 0 (上限 indeterminate)。
- 言えないこと: 草稿 H1 の確認段の判定 (LLC miss、確認段の新しい走行)、長い固定 snapshot、TPC-C、構成 D 以降、md_11 最良設定そのものの正しさ (md_20 並走中、main に未着地)。
