# 段 1 brief — md_33 Cicada の正しさの記録を中間案 M へ (T-2874、wave dev-wave-cicada-certified-m)

起点 local main `213d411c6` (開始 gate fresh rc 0、2026-09-30 14:4x JST)、CCBench pin C `68106660` (動かさない)。job dir `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-cicada-certified-m/`。

**研究前進:** VHash 論文の正しさの節 (論文ストーリー 3 版目 §4.5) に「TRACE ビルドで、生存中の tx が読んだ版が回収・再利用されていないこと、公開した全版が記録されていることを全 tx で照合し違反 0。照合は早すぎる回収と公開漏れを人為的に入れた版で発火する」と書けるようにし、構成 E / E-max と比較相手の最良設定の性能値を「未検証の診断値」から D2305 項 4 (2) の地位へ上げる材料を作る。完了判定 = md_24 §8 の完了条件 (下の成果物 4〜7)。

**確定済み裁定:** D2305 項 4 (M に決定。判定器 production と campaign は変えない。repo 外起動器の合否に入れる。izanagi 内部で certified と呼ばない。trace hook は patch のまま)、D2300 (B・U・P の定義、P は M に入らない)、D2295 (P5 = 安全点で下限を最新へ上げる は既読版を回収させるので却下済み)、D2302 (最良設定の inline slot 3 点比較)、D2279 (Cicada trace の置き場)。

**不変条件:** 絶対規律 1 (記録はすべて `#if TRACE` 内、TRACE=0 命令列一致)・2 (違反は即 fail、照合を甘くしない)・3 (違反は tx・key・版・事象を構造化して出す)。判定器 `orchestrator/verifier/` は 1 byte も変えない。trace v2 の既存行の bytes を変えない (未知の行種別は ParseError)。external/ccbench の gitlink を進めない。所有外 (patches/cicada-forwarding-*・instr-cicada-version-lifetime・cicada-interval-gc-*・external/ccbench の branch) は読むだけ。

**provisional 裁定 (攻撃対象):**
- (P1) inline 版: M の対象を `INLINE_VERSION_OPT=1 ∧ INLINE_VERSION_PROMOTION=0` まで広げる。inline 版の回収・再利用・返却は非 inline と同じ 3 関数 (`include/transaction.hh` の `gcAfterThisVersion`・`newVersionGeneration`・`writeSetClean`) の inline 分岐で起き、`inline_ver_` は Tuple 内で解放されないので、同じ照合を足すだけで覆える。PROMOTION=1 は既存の `#error` のまま。根拠: 比較相手の最良設定と E / E-max の実測がすべて OPT=1 (論文ストーリー 3 版目 §4.5)。範囲外と明記する案は、主比較の性能値を M の地位に上げられないので採らない。
- (P2) B の方式: md_24 の代替案 (Version に TRACE 専用の単調な世代番号、登録時に「世代→wts→世代」の一致組を控え、tx 終わりに世代を読み直す) を採る。条件: `REUSE_VERSION=1` を起動器が強制し、M の範囲 (YCSB、stock と forwarding 3 patch) で走行中に版 object を解放する経路が無いことを file:line で確かめ直す。主案 (版の外の事象台帳) は並行時の順序付けが重く +150〜250 行に収まらない見込み。
- (P3) U: `cpv()` の committed store の直前に status = pending を確かめ、(key・版 object・世代・wts・op) を tx ごとの TRACE 専用記録に積み、`traceCommit` で W 行の集合と双方向に照合し wts = C 行の版も見る。read 側 API 照合は md_24 §3.2 の呼び出し単位の規則 ((a) 再読・(b) own-write・(c) 外部 read、余分な登録 0、NOT_FOUND 0)。P と write 側 I は入れない。
- (P4) 出力: 違反は stderr の 1 行 1 件 (`CICADA_M_VIOLATION kind=… thid=… tx_seq=… key=… ver=… …`)、終了時に集計行 1 行 (照合した read・write・呼び出しの件数と各違反件数)。trace の行は増やさない。件数の一致を発火の証拠と呼ばない (発火の証拠は壊し patch だけ、md_24 A5)。
- (P5) 置き場: 計装は新規 `patches/instr-cicada-trace-m.patch` (instr-cicada-trace.patch の上に重ねる、`#if` 条件語は TRACE だけ)。同じ bytes が「pin C → instr → M」と「pin C → instr → forwarding-variant → forwarding-gc → forwarding-target → M」(または M を instr の直後) の両方に `git apply` で fuzz なしに当たること。instr-cicada-trace.patch は変えない。起動器は repo 外 (job dir、`launch_gcfix_run.py` と md_21 の `launch_cicada_run_target.py` を雛形に genome と M の集計行を足す)。
- (P6) 壊し 2 本 (repo、`patches/broken-cicada-m-*.patch`、無マクロの無条件、M の上に重ねる): B = P5 型 (stock の YCSB で、tx の途中で自 thread の ThreadRtsArray を最新の MinWts−1 へ上げて短く待つ)、U = `cpv()` の後・emit の前に write set から要素を 1 つ外す (md_24 A1 の列)。各々 reached / changed / committed の発火診断を stderr に全件出し、M の違反が壊した tx に帰属することを事前登録で判定する。異常終了は検出と数えない。B は default (OPT=0) と BEST (OPT=1) の両方で走らせ、inline 版での発火も数える。

**成果物:** 1. `patches/instr-cicada-trace-m.patch` 2. 壊し 2 本 3. `patches/README.md` の entry (ledger.json は entries 1 件固定なので足さない、md_3 の先例) 4. 負例: stock default (K・W・R × t1・t4)、BEST (md_20 の BEST、K・R × t4・t48)、E-max (md_21 の検査 cell) で巡回 0 ∧ M 違反 0 ∧ 照合件数 > 0 5. 正例: 壊し 2 本の M 違反 > 0 と帰属、既存の壊し 3 本を M の上に重ねても巡回を検出 6. TRACE=0 命令列一致 (pin C 対 pin C + instr + M、cicada の全 TU = ycsb・tpcc・bomb・sbomb、default と BEST の 2 genome) 7. 一次資料 `output/insights/2026-09-30/cicada-certified-m/README.md` (段 1 の判断、正例・負例、TRACE=0、書ける文・書けない文の表) 8. spool fragment (T-2874 の更新)。

**受入・実測環境:** 計算は Pegasus の計算ノード (`tools/pegasus/dispatch_compute.py --task generic`、`docs/pegasus-runbook.md`)、条件を 4〜5 job に割って同時投入、合計 < 2 node 時間 (見積り 20〜26 run × 80〜220 s + build ≈ 0.6〜1.2 node 時間)。受入全走は段 6 で `tools/dev_wave_wait.py acceptance`。TRACE=1 build の throughput は性能値に使わない。

**分割方針:** 段 5 の実装子は 2 単位 — U1 (repo: M 計装 patch・壊し 2 本。patches/README の entry は docs なので親が段 7 で書く) と U2 (repo 外: 起動器)。U2 は U1 の出力形式 (違反行・集計行の書式) に依存するので、段 4 で書式を確定してから並列投入する。

## 追補 (2026-09-30 15:4x JST、条件 13 = DW-O13 の読了遅れによる段 2 からの再実行)

この wave は照合 (検査) を新設するので `DW-O13` が着手時から成立していた。段 2 前に読んでいなかったため、契約どおり段 2 の plan・段 3 の相談・段 4 の裁定を invalidate し (`invalidated-v1/`、以後の子の入力にしない)、段 2 から再実行する。以下は親がコードで自分で確かめた事実の追補 (brief の前提の更新):
- (F-a) `gc_versions()` は tuple の GC 権 (`getGCRight`) の取得に失敗すると、その gcq 要素を再試行せず捨てる (`external/ccbench/cc/cicada/transaction.cc:815-818`)。読み手が GC 権を握る形の排他は TRACE ビルドの回収挙動を変える。
- (F-b) leader は全 worker の `GCFlag` が立ったときだけ `MinWts`・`MinRts` を更新する (`util.cc:281-322`)。tx の途中で待つ worker が flag を立てないと回収境界は進まない (構成 E-hb の安全点が flag を立てるのはこのため)。
- (F-c) `gc_records()` は削除済み record の tuple を走行中に `delete` する (`transaction.cc:845-855`)。YCSB の point read / update では DELETE を出さないので経路に入らない、という前提は実行範囲の限定として起動器で固定する必要がある。
- (F-d) `read_internal()` は `ldAcqLatest()` から版列を走査し、pending を待ってから `read_set_.emplace_back` する (`transaction.cc:79-126`)。版 pointer を得てから世代などを控えるまでに窓がある。
- (F-e) M の合否述語 (DW-O13): 述語の入力 (M の集計行・違反行、起動器の result の field) は未実在の新設である。各述語について入力 field の出所と、stock・壊しで要求値 (違反 0、照合件数 > 0、壊しで違反 > 0) が到達可能かを、本走の前の生死確認 job で実測してから本走の合否に採る。run の時間上限は既存 run の Elapse 分布の max への倍率で決める。
