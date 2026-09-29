# 段 1 brief — md_23 VHash hot block を Cicada に組み込む (構成 B)

wave: dev-wave-vhash-hot-block-cicada / 基準 main 8fe87f852 / 2026-09-29 22:20 JST / 依頼 /work/1/SFC/tanab/tmp/vhash-2026-09-29/md_23.txt (+ common.txt)

## 研究前進
論文ストーリー 2 版目 §8.1 の「hot 配置を Cicada に入れた計測 (構成 B) は無い」を埋める。H1 を Cicada の中で初めて測り、図 3 枚 (K×throughput、ro 比率×利得、書き込み側の費用) を出す。完了判定 = inert patch + 正しさの門 (判定器で巡回 0、壊し版の検出) + 同時刻対照の計測表と図が一次資料 output/insights/2026-09-29/vhash-hot-block-cicada/README.md にあること。

## scope (変更面の実アンカー、pin C 68106660 の external/ccbench)
- 版選択の第 1 段ループ (新しすぎる版を飛ばす): cc/cicada/transaction.cc:100-112 read_internal。第 2 段 (PENDING 待ち・ABORTED 飛ばし) :113-122 は stock のまま。
- 版の挿入: transaction.cc:479-524 validation の Install pending version (先頭 CAS :502-509 / 途中 CAS :511-517)。read 再検査 (a) :543-570 は later_ver_ から列を辿る (stock のまま)。
- abort: include/transaction.hh:343-370 writeSetClean (install 済みを aborted に)。
- GC: transaction.cc:806-843 gc_versions (gc_lock_ 下で ver_ の next を切る)、transaction.hh:173-197 gcAfterThisVersion (REUSE_VERSION で再利用)。
- key の先頭: include/tuple.hh:24-110 Tuple (latest_、INLINE_VERSION_OPT で inline_ver_、init 2 種)。
- read-only の決定: include/ycsb.hh:106 (is_ronly_ は手続きの先頭から)、ro の rts は begin() transaction.cc:34-43 で MinWts-1。
- 新規: patches/cicada-vhash-hot-block-variant.patch、patches/broken-cicada-vhash-*.patch (1 本以上)、patches/README.md の該当節、計測 driver (新規 file)、作図生成器、一次資料、spool fragment。
- 条件 gate の登録 (D2288 の先例、所有外だが必要最小): orchestrator/campaign/condition_meaning_gate.py と連動する在庫 (先例 merge 02c382253 の変更 file: materializer_admission.py、screening_driver.py の _CONDITION_DEFAULTS、tests/test_ccbench_spawn_sites.py、test_condition_meaning_gate.py、test_p3_build_authority_cli.py、test_p3_s4_loop.py)。

## 確定済みの裁定・依頼の制約
- SIMD を使わない、連続配置 + scalar 比較 (md_5)。forwarding patch とは重ねない (組合せは後続)。
- 判定器は変えない、上限は indeterminate (D2279)。性能値は trace も計器も外した build (絶対規律 1)。巡回が出た構成は即失格 (規律 2)。
- ledger.json に entry を足さない (D2288・D2279、entries 1 件固定の契約)。README の節で登録。
- 土台は md_11 の観測最良 (BACK_OFF=0, INLINE_VERSION_OPT=1, INLINE_VERSION_PROMOTION=0, REUSE_VERSION=1, WRITE_LATEST_ONLY=0, 48 thread, N=1M, skew 0.9, max_ope 10, rmw 0, extime 3, rr5/rr50 GC100・rr95 GC10)。最良設定の正しさ検査 (md_20) は並走中で main に無い → 一次資料に明記。
- 所有外 (読むだけ): external/ccbench (gitlink 不動)、patches/cicada-forwarding-*、vhash_forwarding_prototype.py、patches/cicada-ro-gcflag-*、tools/vhash_forwarding_model/、patches/cicada-interval-gc-*、patches/instr-cicada-trace*.patch。
- 計算は合計 2 node 時間未満。超える見込みなら投入せず見積りを書いて止める。条件は複数 node に割り同時投入、同時刻対照。

## 親の provisional 裁定 (攻撃対象)
- (P1) hot の実体: Tuple の中に seq (8 B) + 記述子 K 個 {wts, Version*} (16 B) を置く。値は置かない (Cicada の値は HeapObject の別確保、md_5 で K=8 の inline 値は最新版で遅い)。状態は記述子に写さず Version の status_ を読む。
- (P2) 一貫読み: 1 key 1 本の seqlock。reader は seq が奇数、または読み終えて seq が変わっていたら、spin せず stock の列の走査へ落ちる (意味が stock と同じ fallback)。
- (P3) 保守の不変条件: 「seq が偶数の各時点で、hot = 版の列の先頭 min(K, 長さ) 個の (wts, ptr)」。列の先頭 K 個を変えうる操作 (挿入 CAS、GC の切り離し) は seq の書き区間の中で行う。挿入は CAS の前に seq を取り、CAS 成功後に hot を更新して離す。更新方法は hot 内の位置へ shift 挿入 (列を辿り直さない)。K より奥への途中挿入は hot 不変。
- (P4) ABORTED の扱い: 評価計画草稿の R3 の数え方 (ABORTED を除き PENDING を数える) に合わせ、writeSetClean で hot から外す。反対案 = 列と同じく残し、読みで飛ばす (stock と同じ)。
- (P5) 読み: 第 1 段ループだけを hot の走査に置き換える。wts ≤ trts の最初の記述子 i を選び、later_ver = 記述子 i-1 の ptr (i=0 なら nullptr、stock と同じ意味)。hot に無ければ最後の記述子から列を辿る (cold)。第 2 段以降と read_set_ への記録は stock と同一。
- (P6) GC 安全: 読む版は stock と同じ選択規則なので、GC の切り離し点 (MinRts 未満の確定版) より古い版を選ばない。GC は切り離しの前に hot から切り離し点より古い記述子を消す (seq 書き区間)。REUSE_VERSION の再利用より前に hot から消えていること。
- (P7) macro: CICADA_VHASH_K (未定義 = 0 = stock、1/2/4/8)、CICADA_VHASH_COUNT (診断計数、性能値に使わない)、CICADA_VHASH_WL (実行時 flag: ro 比率。stock 対照もこれを立てた build)。IZANAGI_ 接頭辞なし (D2288)。各挿入後に #line (md_6 の教訓)。分岐は owner TU transaction.cc と header だけ (条件 gate の meaning 検査は owner TU だけを見る)。
- (P8) snapshot の古さの軸は stock flag の gc_inter_us {10, 1000, 100000} だけにし、長い tx の生成器は入れない (所有と規模を抑える)。
- (P9) 格子: ro 比率 {0, 50, 95}% × gc {10, 1000, 100000} (update tx は rr50) + 通常 YCSB rr5/rr50/rr95 (md_11 の GC) の 12 条件 × 構成 {stock, K1, K2, K4, K8} を 1 job 内で巡回順に交互に 5 round、2〜3 node へ割る。throughput は計器なし build、探索長・hot 当たり率・書き込み側の lock 費用は COUNT build の別走、メモリは maxrss と解析値 (N × (8 + 16K) B)。
- (P10) 正しさ: trace 版 (pin → instr-cicada-trace.patch → 本 patch、TRACE=1) を K = 1 と 8 で、ro 高比率 + 古い snapshot と update 中心の cell で判定器に通す。壊し: B1 = hot 走査で 1 つ古い記述子を選ぶ (ro で古い読み、検出を期待)、B2 = PENDING の記述子を飛ばす (update tx の validation (a) が止めうる → 検出されなければ「止められた」と事実で書く。結果前に予測を登録)。

## 成果物の形
patch 2〜3 本、README 節、driver (+ test)、作図生成器、一次資料 (結果・図・限界・確かめたこと/確かめていないこと)、spool fragment (worklog 新規 item、decisions に設計の選択)。

## 分割方針
Codex author 2 単位: (U1) patch 3 本 (variant + 壊し) と gate 登録一式、(U2) driver + test + 作図。U2 は U1 の macro 名と flag 名に依存 (段 4 で固定して並列投入)。計算は smoke 1 本 → 本走 (正しさ・計器・性能) を複数 node。
