# 段 1 brief — md_37 VHash hot block の書き込み側の排他を CAS の外へ出す (T-2926) + md_23 の残り (T-2927)

wave: dev-wave-vhash-hot-block-v2 (branch worktree-dev-wave-vhash-hot-block-v2) / 基準 local main 213d411c6 / 2026-09-30 15:00 JST (s1-brief.md の mtime) / 依頼 request-md37.txt (+ request-common.txt)。開始 gate fresh rc 0。

## 研究前進
論文ストーリー 2026-09-30 版 §0.3 の重心の択一 (案 1 = VHash を残す) の材料。md_23 (一次資料 output/insights/2026-09-29/vhash-hot-block-cicada/README.md) は構成 B が更新中心で stock 比 0.23〜0.80 倍、主因は key ごとの書き区間の待ち (1 update commit あたり約 10 万サイクル、§6) とした。書き込み側の排他を CAS の外へ出した設計を 1 度だけ測り、更新中心の比がどこまで戻るか・ro 95% の比が変わるかを同時刻対照で示す。完了判定 = 新設計の inert patch + 判定器 3 cell で巡回 0 + 壊し (B1・B2 相当と遅れた hot を狙う壊し) の検出 + 12 cell × {stock, md_23 の B, 新 B} の同時刻比の表と図 + md_23 の残り 4 点が一次資料 output/insights/2026-09-30/vhash-hot-block-cicada-v2/README.md にあること。

## scope (変更面の実アンカー、pin C 68106660 の external/ccbench)
- 読みの第 1 段: cc/cicada/transaction.cc:102-107 (read_internal、`ver = tuple->ldAcqLatest(); while (ver->ldAcqWts() > trts)`)。第 2 段 (PENDING 待ち・ABORTED 飛ばし) :108-119 は stock のまま。md_23 patch はこの第 1 段を hot 走査に置き換えた。
- 版の挿入: transaction.cc:478-531 (validation の Install pending version。位置探索 :499-510、先頭 CAS :516、途中 CAS :523)。md_23 は探索と CAS を key ごとの書き区間 (VHashGuard) の中で行い、K>0 では探索を列の先頭から行う。
- read 再検査 (a) :538-570 (later_ver_ から辿り、PENDING を待つ)、(b) :572-595。ro tx は validation を持たない。
- GC: transaction.cc:806-842 gc_versions (gc_lock_ → md_23 では hot の書き区間 → trim → 切り離し → 区間を閉じる → gcAfterThisVersion の再利用)、include/transaction.hh:173 gcAfterThisVersion、:343 writeSetClean。
- 時刻: begin() :34-43 (wts を ThreadWtsArray に公開 → rts = MinWts−1)、util.cc:280-316 cicadaLeaderWork (MinWts/MinRts)、include/time_stamp.hh (ts = localClock<<8 | tid)。
- 所有 (依頼の「所有」節が正本): patches/cicada-vhash-hot-block-* (更新または新 patch)、orchestrator/campaign/vhash_cicada_hot_block.py とそのテスト (orchestrator/tests/test_vhash_cicada_hot_block.py)、作図 tools/plotting/plot_vhash_cicada_hot_block.py (+ orchestrator/tests/test_plot_vhash_hot_block.py の該当部)、patches/broken-cicada-* の新規 (名前は vhash-post / vhash-* 系で md_32・md_33 と分ける)、patches/README.md の該当節、自分の一次資料と spool fragment。
- 所有外で必要最小になりうる在庫 (D2311 決定 4 の先例): orchestrator/campaign/condition_meaning_gate.py (DEFINE_SPECS、_OVERLAY_BASE_DEFINE_INTERFACES は tests/test_ccbench_spawn_sites.py:671)、materializer_admission.py:113、tests/test_ccbench_spawn_sites.py:82・110-112 (spawn site 件数)、test_condition_meaning_gate.py:3671、test_official_perf_closure.py:47、test_p3_build_authority_cli.py:162・185。新 macro を足すか overlay で済ませるかでここが変わる (P3)。
- 読むだけ: patches/cicada-forwarding-*・tools/vhash_forwarding_model/ (md_31)、external/ccbench の gitlink (md_32)、patches/instr-cicada-version-lifetime.patch (md_29)、M の計装 (md_33)、patches/instr-cicada-trace*.patch、判定器 (verifier/)。
- DW-O09: 変更予定 5 file (variant patch・driver・作図・壊し 2 本) の変更前 sha256 先頭 16 桁で repo 全体 (output/ 含む) を git grep して 0 件 (15:05 実測)。pin は path 参照の在庫だけ (上の所有外の行)。

## 確定済みの裁定・依頼の制約
- D2311 (md_23 の設計) の却下欄に「CAS の後に遅れて更新する案は本命の候補だが論証が無いので次の一手」とある。本 wave はその論証を先に書く (依頼 1)。PENDING の扱い (より新しい PENDING があれば待つ) を崩さない (依頼 1)。
- 判定器は変えない、上限 indeterminate (D2279)。巡回が出た構成は即失格 (規律 2)。性能値は trace も計器も外した build (規律 1)。ledger.json に entry を足さない (D2288・D2311 決定 5)。
- 土台は md_11 の観測最良 (BACK_OFF=0, INLINE_VERSION_OPT=1, INLINE_VERSION_PROMOTION=0, REUSE_VERSION=1, WRITE_LATEST_ONLY=0)、48 thread、N=1M、skew 0.9、max_ope 10、rmw 0、extime 3。格子は md_23 と同じ 12 cell (ro {0,50,95}% × gc {10,1000,100000} µs + rr5/rr50/rr95)。
- 合計 2 node 時間未満 (超える見込みなら投入せず見積りを書いて止める)。条件は複数 node に割り同時投入、走行中の他の計測 wave と同じ node で測らない。段 2・3・6 を省かない (依頼)。

## 親の provisional 裁定 (攻撃対象)
- (P1) 設計「B-post」: 版の挿入は stock のまま (位置探索は later_ver_ から、CAS も stock) で hot の書き区間の外。CAS 成功後に短い書き区間を取り、(wts, ptr) を hot へ wts 降順の位置に挿入する (列を辿らない。満杯なら最小を落とす)。この区間は writer の validation の中 (commit/abort の確定と次の begin() より前) で必ず終える。GC は md_23 と同じ (gc_lock_ → 書き区間 → trim → 切り離し → 閉じてから再利用)。
- (P2) 遅れて更新してよい条件の担保は、論証だけに頼らず読み手の「隣接確認」で機械的に作る: hot の copy (seqlock で一貫) から wts ≤ trts の最初の記述子 X = ptr[i] を選んだら、i ≥ 1 なら `ptr[i-1]->next_ == X`、i = 0 なら `tuple->latest_ == X` を acquire load で確かめ、成り立てば ver = X・later_ver = ptr[i-1] (i=0 は nullptr) として第 2 段 (stock の PENDING 待ち) へ進む。成り立たなければ stock の走査へ落ちる。確認の瞬間の列で stock の第 1 段が止まる版と later_ver が X・ptr[i-1] に一致すること (列は wts 降順・ptr[i-1].wts > trts) を論証の核にする。cold (全件 > trts) は md_23 と同じく ptr[n-1] から stock のループを続ける。
- (P3) hot の意味は「物理列の先頭の正確な写し」から「列の中の版を wts 降順に並べた K 個以下の手がかり」に弱まる。正しさは (P2) の確認と、pointer の生存 (GC が再利用前に trim する、writer は自版を自 tx の中で hot に入れる) だけに依存させる。反対案 = 確認なしで「ro は MinWts の性質、update は validation (a) が止める」の論証だけで遅れを許す。md_23 の壊し B2 (PENDING を飛ばす) が結果前の予測に反して T1 で 67 件 commit した事実が、この論証の前提 (ro の rts 以下に PENDING が来ない) を疑わせるので、親は確認ありを推す。
- (P4) 実装の形: md_23 の variant patch の bytes を変えず、その上に重ねる新 patch `patches/cicada-vhash-hot-block-post.patch` (新 macro を足さず、既存 `#if CICADA_VHASH_K` の中を置き換える overlay) にする。md_23 の B = pin + variant、B-post = pin + variant + post。条件 gate が overlay の中の新しい `#if CICADA_VHASH_COUNT` をどう扱うかは段 2 で実物 (condition_meaning_gate.py の overlay 規則) を読んで決める。overlay で通らない場合の代案 = variant patch に新 macro `CICADA_VHASH_POST` を足し、POST=0 の前処理が現行 variant と一致することを確かめる。
- (P5) 腕と K: stock (K=0・WL=1) と md_23 の B と B-post を K ∈ {1, 8} で並べる (5 腕、md_23 の perf job と同じ本数)。K=1 は md_23 §5.1 の K\*、K=8 は hot の読みが最も多い点。K=2・4 は測らない。
- (P6) 正しさ: trace build (pin → instr-cicada-trace.patch → variant → post) の B-post K ∈ {1, 8} を md_23 の T1・T2・T3 で判定器に通す。壊しは B-post の上に (a) md_23 の B1 (1 つ古い確定版を返す) と B2 (PENDING を飛ばす) の当て直し (context が合わなければ新 patch)、(b) 遅れた hot を読む誤りを狙う新しい壊し「隣接確認を外し、かつ writer が hot への挿入を一部飛ばす」(ro の読みが列にある新しい確定版を飛ばして古い版を返す経路。検出を期待し、結果前に到達数の見込みを登録する)。
- (P7) T-2927 (1) B2 の機序: 小モデルより先に計器 build で「B2 の committed 事象が ro tx か update tx か、update なら validation (a) で見た P の状態と読んだ版」を記録する壊しの計器版 (新 patch) を md_23 の B (K=4) の上で T1・T2 に 1 走ずつ走らせる。結果前に仮説を登録する。
- (P8) T-2927 (2) snapshot の遅れの計器: ts は `localClock<<8 | tid` なので 2^16 ts = 256 サイクルで飽和した。(wts−rts)>>8 (サイクル) を 2 冪 bucket で上限 2^40 まで数え、clocks_per_us で µs に換算できる形にする (COUNT の schema_version を上げる)。(3) estimate の trace job の所要を 2 job の走数の和にする。(4) fig-write の下段に書き区間の待ちサイクルを足す。
- (P9) 計測: perf 3 job × 2 round (12 cell × 5 腕、腕の順は round と cell で回転) を 3 node に同時投入、count 1 job (B と B-post の K 1・8 と stock、md_23 の COUNT 4 cell、新しい計器 = 書き区間の待ち・保持と隣接確認の失敗数)、trace 2 job、smoke 1 本。見積りは md_23 の Elapse (perf 518 s/job、trace 254+32 s、build 247 s、count 85 s、smoke 308 s) から約 1 node 時間。

## 成果物の形
patch (post overlay 1 本 + 壊し 2〜3 本 + B2 計器 1 本)、patches/README.md の節、driver と test の更新、作図の更新、一次資料 (論証・結果・図・限界・確かめたこと/確かめていないこと)、spool fragment (worklog: T-2926・T-2927 の完了または更新、decisions: 設計の選択)。

## 分割方針
Codex author 2 単位: (U1) C++ の patch 一式 (post overlay・壊し・B2 計器) と、必要なら条件 gate の登録一式、(U2) driver + test + 作図。U2 は U1 の patch 名・macro・計器の JSON 名に依存 (段 4 で固定して並列投入)。計算は smoke 1 本 → 本走 (build → perf 3・count・trace 2 を別 node に同時)。
