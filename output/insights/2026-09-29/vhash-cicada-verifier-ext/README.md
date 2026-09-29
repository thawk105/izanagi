# Cicada の正しさ検査を insert と TPC-C へ広げた — stock の TPC-C 小走行は巡回 0、insert を壊した版を判定器が検出し帰属、trace を外した TPC-C の命令列は pin と一致。delete を含む並行走行では stock Cicada 自体が GC で異常終了する (VHash 論文の前提 G0 の続き、2026-09-29)

authority: none / default_effect: no-state-change (可変状態の正本は worklog 末尾と現行 phase doc)。
wave `dev-wave-vhash-cicada-verifier-ext` (branch 同名)、起点 local main `035fc11fa` (開始 gate fresh rc 0、2026-09-29 14:4x JST)、CCBench submodule = pin C `68106660` (動かしていない)。
job dir `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-vhash-cicada-verifier-ext/` (段 1 brief・段 2 plan・段 3 相談・段 4 裁定・Codex の prompt と報告・repo 外起動器・計測の原本 JSON と raw trace)。依頼は `/work/1/SFC/tanab/tmp/vhash-2026-09-29/md_17.txt` (同 dir `request-md_17.txt` に逐語)。
段 1〜6 の全文は `verbatim/` (依頼、段 1 brief、段 2 plan、段 3 相談 2 本、段 4 裁定 (R9 追補を含む)、段 5 の計測要約 3 本、段 6 レビュー 2 本と裁定、焦点再レビュー)。
逐語の正規化 2 件 (`git diff --check` 抵触のため、Markdown 改行用の行末空白を除去、可視文字不変): `verbatim/s3-consult-b.md` は 15 行、原文 sha256 `c277d4080496f0b495ae6048c23ebff153fecf1742f0ed2f67c127cb0c776b77`・5,270 byte → `a2de29a883a78dc7bce4d57496b2d0fb4111e723a43ab4cce54c71b7ff8e46d2`・5,240 byte。`verbatim/s6-review-a.md` は 8 行、原文 `ad4df27848eaf388945519e4002843bc96b192b0fb466ef6f731f3a8be639244`・2,091 byte → `8ff9f7b2fcba06a75e9362d3d19d03ed986c343d7ab9d51467cf44068218d0ab`・2,075 byte。原文は job dir の `consult-b.md`・`review-a.md` (復元はその file を写す)。
前段は `output/insights/2026-09-29/vhash-cicada-verifier/README.md` (md_3、D2279)。

## 1. 依頼と結論

依頼 (VHash 論文の並行 wave md_17、台帳 T-2874 の (4) の一部): md_3 の Cicada trace と判定器は YCSB の点読み・点更新だけを扱う。VHash の評価で TPC-C や insert のある負荷を使うと正しさの門 (絶対規律 2) を通せない。insert / delete の trace、TPC-C の Cicada TU の trace、trace を外した tpcc の命令列が pin と一致すること、を整え、壊した版で検出を確かめる。trace の書式は変えない (md_14 が使用中)。

結論:

1. **Cicada の TPC-C 走行を、既存の trace v3 (表番号付き、D2224 / D2225) で判定器に掛けられるようになった。** 新しい重ね patch `patches/instr-cicada-trace-tpcc.patch` が、TPC-C の取引の中だけ v3 を出し、それ以外 (YCSB) は md_3 の v2 のまま出す。判定器は 1 byte も変えていない (§2)。
2. **負例: stock Cicada の TPC-C 小走行 5 本はすべて巡回 0・存在履歴違反 0・integrity 数値項目 0・C 行 = commit 数。** insert だけの mix (NewOrder / Payment) の thread 1・4、StockLevel を増やした mix の thread 4、Delivery (delete) を含む全 mix の thread 1 (§3)。
3. **Delivery (delete) を含む全 mix (F cell) の 4 thread では、stock Cicada 自体が `gc_records()` の `ERR` で 11 回中 11 回異常終了した。** trace を外した pin C 無 patch の build でも 5 回中 5 回起きたので、trace の追加が原因ではなく、CCBench pin C の Cicada 側で起きている。delete の競合という機序は静的な読みによる仮説で、未実証 (§5)。このため delete を並行下で判定器に掛けた履歴はまだ無い。
4. **正例: insert の意味を壊した版 (insert した版に自分より古い時刻を付ける) を判定器が検出し、壊した insert に帰属できた。** 判定器は non-serializable を返し、生産者の無い版の読み (orphan read) 1,144,962 件のすべてが壊した insert の事象 (表・key・版) と一致した。巡回も 1 件出て、その辺も壊した insert の行に帰属した。加えて既存の壊し patch (read set 再検査を飛ばす) を TPC-C に重ねた版で、巡回 2,135 件・代表 witness 20 件中 20 件の帰属を確かめた (§4)。
5. **trace を外した build の命令列は pin と一致した** (絶対規律 1): tpcc・bomb・sbomb の各 3 TU (既存計装のみ) と、tpcc の 3 TU (C1' + 既存計装 + 重ね patch) の計 12 TU で差分 0 byte (§6)。
6. **判定の上限は indeterminate のまま** (Cicada に X / P / I の証拠面が無い)。範囲読みの phantom、不在の読み、campaign の受理経路は対象外。今回言えるのは「TPC-C 走行で**記録された点読みと書き**から、巡回・orphan read・存在履歴違反を検出する経路が働く」までである (§7)。

## 2. 設計

### 2.1 書式 — v3 は既存の書式

YCSB に insert / delete は無い (`external/ccbench/include/ycsb.hh` の操作は READ / WRITE / READ_MODIFY_WRITE だけ)。insert / delete は TPC-C (NewOrder の insert、Delivery の delete) と BOMB にある。TPC-C は表だけが違う同じ key bytes を持つので、表を持たない v2 では別の行の版が 1 本の版列に混ざる (D2224)。そこで TPC-C は判定器が既に受理する v3 で出す:

| 記録 | Cicada の TPC-C での中身 |
|---|---|
| `C <txid> <thid> <hi> <lo> <nR> <nW> 0 0 <tx_type>` | 版 = 自分の wts の上下 32 bit (md_3 と同じ)。nS = nQ = 0 (範囲読みの S / Q 行は出さない)。tx_type は CCBench の `TxType` (1〜5) |
| `R <txid> <table> <key_hex> <hi> <lo>` | table = 要素の `Storage` (0〜10)。版は md_3 と同じく読んだ時点に保存した wts、初期版は genesis `(1,0)` |
| `W <txid> <table> <key_hex> <U\|I\|D> <hi> <lo>` | 版 = 自分の wts。insert は I、delete は D |
| `E <txid>` | 同じ |

v2 / v3 の切替は silo の先例 (D2225 項 2) と同じく、CCBench の `include/tpcc.hh` が取引の begin 直後に置く取引種別の thread-local 文脈を `traceCommit()` が 1 回読み、非 0 なら v3、0 なら md_3 の v2 の式をそのまま通す。E の直後に文脈を 0 に戻す。

### 2.2 置き場 — 重ね patch

v3 の部品 (`include/trace.hh` の v3 出力関数と取引種別の文脈、`include/tpcc.hh` の文脈の設定と trace build の全 commit 計数) は pin C に無く、CCBench の local branch の C1' `6aa7a58f` (pin C の子、header 2 file だけ) にある。pin の C2' 系への前進は D2277 項 1 で承認済みだが、まだ C のままである。

- `patches/instr-cicada-trace.patch` (md_3) は **bytes を変えていない**。md_14 がこの上に forwarding の試作を重ねて YCSB を検査しているので、YCSB の出力と重ね適用を 1 byte も揺らさないため。
- TPC-C 用は新しい `patches/instr-cicada-trace-tpcc.patch` を重ねる。適用順は「C1' (以降) → `instr-cicada-trace.patch` → 本 patch」。変更は `cc/cicada/include/transaction.hh` の `traceCommit()` と `cc/cicada/tpcc_cicada.cc` の main (`initial_wts` の受け渡し、ycsb と同形) だけ。追加は `#if TRACE` の内側だけで、`#else` 側の `#line` で TRACE=0 の論理行番号を保つ。pin C 単独に本 patch を重ねた TRACE=1 build は作れない (C1' の部品が要る)。
- 依頼の「`instr-cicada-trace.patch` の更新」は「instr-cicada-trace 系の更新 = 重ね patch の新設」と読み替えた (段 4 裁定 R2)。

### 2.3 insert / delete の意味と、判定器の扱い

- 初期ロードだけが版 `initial_wts` (= genesis) を付け (`cc/cicada/include/tuple.hh` の `init(thid, body, param)`)、実行中の insert は自分の wts の新版を付ける (`init(thid, ver, wts)`)。key が木にあれば insert は失敗する。D2232 項 4 が別の CC に求める 2 点は Cicada でも成り立つ (実測: 全 W の版 > initial_wts)。
- delete は削除印の版 (`new Version(wts)`) を積み、commit で木から外す。deleted の版と木に無い key の読みは read set に入らないので R 行が出ない。判定器の v3 段 1 も不在の読みを表さない (nS = nQ = 0) ので扱いは一致するが、**不在の読みが作る依存は判定器に見えない** (§7)。
- read-own-insert は write set から読むので R を出さず、insert 後の update は同じ W に畳まれる。trace は取引が最後に残した I / D / U を記録する。
- `INLINE_VERSION_OPT=1` では実行中の insert が新版を tuple に繋がない (`tuple.hh` の `init(thid, ver, wts)`)。既定の 0 に固定して走らせ、1 は未対応。

### 2.4 判定器の側

production・テストとも変えていない。v3 の受理集合 (表 0〜10、取引種別 1〜5、nS = nQ = 0) に Cicada の値が入り、`--protocol cicada` は証拠面を unavailable にするので、巡回が無ければ indeterminate、あれば non-serializable になる (md_3 と同じ上限)。v3 の run では存在履歴の検査 (D2232) も走る。

## 3. 負例 — stock Cicada の TPC-C (C1' + 既存計装 + 重ね patch、TRACE=1)

共通条件: `tpcc_num_wh=1 extime=1 tpcc_interactive_ms=0 group_commit=0 clocks_per_us=2100`、CMake = `INLINE_VERSION_OPT_CICADA=0 INLINE_VERSION_PROMOTION=1 REUSE_VERSION=1 SINGLE_EXEC=0 WRITE_LATEST_ONLY=0 TRACE=1`。cell は `tpcc_perc_payment / order_status / delivery / stock_level` で M = 43 / 0 / 0 / 0 (NewOrder 57)、F = 43 / 4 / 4 / 4 (NewOrder 45)、R2 = 43 / 4 / 0 / 20 (NewOrder 33)。

| job | run | 判定 | 巡回 | integrity 数値項目・存在履歴違反 | C 行 = commit 数 | READ_WTS_MISMATCH | trace |
|---|---|---|---|---|---|---|---|
| L0 (l0-a) | M t1 | indeterminate | 0 | 全 0 | 30,984 = 30,984 | 0 | 41.2 MB・978,380 行 |
| L0 | M t4 | indeterminate | 0 | 全 0 | 42,676 = 42,676 | 0 | 55.4 MB・1,308,200 行 |
| L0 | F t1 | indeterminate | 0 | 全 0 | 18,543 = 18,543 | 0 | 42.3 MB・1,009,650 行 |
| L0 | F t4 | (benchmark 異常終了、§5) | — | — | — | — | — |
| J1 (j1-a) | R2 t4 | indeterminate | 0 | 全 0 | 30,766 = 30,766 | 0 | — |
| J1 | M t4 | indeterminate | 0 | 全 0 | 42,543 = 42,543 | 0 | — |

- integrity 数値項目 = orphan_reads・version_dups・dup_txids・genesis_commits・missing_txids・write_version_mismatch・malformed_keys・framing_violations・lock_coverage_violations・write_intent_violations・permutation_violations、に `existence_violations` を加えた。`integrity.clean` は証拠面が unavailable なので構造上 false で、「integrity 全体が clean」とは書かない。
- 全 run で、全 W の版が `initial_wts` より大きいこと (`all_w_after_initial`) を起動器が確かめた。
- F t1 は Delivery の delete と scan を含む (trace の W 行のうち op D が 7,700 行、op I が 116,582 行。`grep -cE '^W [0-9]+ [0-9]+ [0-9a-f]+ D '` で親が数えた)。並行が無いので delete の競合は起きていない。

## 4. 正例 — 壊した Cicada 2 本 (重ね patch の上に重ねる)

| id | patch | 壊し方 (単一 site) | 事前登録した検出 |
|---|---|---|---|
| β | `broken-cicada-insert-past-ts.patch` (新) | `insert()` で作る新版の wts を、自分の wts ではなく begin 時の読み時刻 `rts_` にする。insert した行が、自分より前に直列化された読み手にも見える | orphan read > 0 (R の版に生産者の W が無い) で、raw trace から数え直した件数が判定器と一致し、その R が事象の (表, key, 公開した版) に一致する |
| α | 既存 `broken-cicada-skip-read-recheck.patch` (bytes 不変) | validation の read set 再検査で不一致でも abort しない (md_3) | 巡回 (non-serializable) で、witness の rw 辺が事象の txn・key・読んだ版に一致する |

単一理由性: validation の版の install と write set 検査 (b) は INSERT を飛ばす (`cc/cicada/transaction.cc` の `validation()`) ので、β の変更を他の検査は止めない。α は md_3 で確認済み。診断は md_3 の 3 本と同形 (事象を commit した取引の分だけ全件、終了時に `CICADA_BREAK_FIRED`)。β の事象行には `table=` を足した。判定には使わず、repo 外起動器の帰属解析だけに使う。

| run (j1-a) | 判定 | 巡回 | orphan read | reached / changed / committed | 自身の他の integrity・C = commit | 帰属 | 分類 |
|---|---|---|---|---|---|---|---|
| β R2 t4 | non-serializable | 1 | 1,144,962 | 140,384 / 140,137 / 130,612 | 全 0・28,562 = 28,562 | 数え直し 1,144,962 = 判定器 1,144,962、事象と一致 1,144,962・不一致 0 | 期待した経路で検出 |
| α M t4 | non-serializable | 2,135 | 0 | 81,143 / 3,610 / 3,604 | 全 0・18,253 = 18,253 | 代表 witness 20 件中 20 件 (表まで照合、段 6 の再計算) | 期待した経路で検出 |

同じ cell の stock 対照 (R2 t4・M t4) は §3 のとおり合格した。

**段 6 の再計算 (レビュー所見 A1・B2):** 最初の帰属解析は、既存の壊し patch の事象行に表が無いため α の表照合を省いていた。起動器に保存済み原本からの再計算 mode を足し (Codex fix)、J1 原本を再走なしで再計算した (`rerun/.cicada-work/reattribute-j1-a.json`、原本 `runs/j1-a/result-J1-TPCC.json` は sha256 `51dd5b7d…77e7` のまま)。α は、事象の txn がその key を事象の版で読んだ R 行から表を復元し (3,604 件中 3,604 件、帰属不能 0、辺の表との不一致 0)、表まで照合して代表 witness 20 件中 20 件が帰属した。β は巡回の witness 1 件の rw 理由 5 件が、事象の表・key・読んだ版 (a_wts)・次の版 (b_wts) と一致した (`cycle_attribution`)。

**β の巡回 1 件 (事前登録では期待していない観測値、親が raw で照合し、段 6 の再計算で機械的にも一致):** G2、cycle [5, 397]。5 (NewOrder) → 397 (StockLevel) の wr 辺 (表 10 = Stock の 5 key)、397 → 5 の rw 辺 (表 8 = OrderLine の key `00010300000bba00`〜`…04`、読んだ版 (9237302, 3800210177)、次の版 (9237366, 833065218))。stderr の事象 `CICADA_BREAK_EVENT slug=insert-past-ts tx_wts=39674185704247554 table=8 key=00010300000bba00 a_wts=39673913793485569` と照合すると、読んだ版 = a_wts (β が付けた過去の版)、次の版 = tx_wts (5 の本来の版)。StockLevel は NewOrder 5 の Stock 更新を読んで 5 より後ろに直列化されたのに、5 が insert した OrderLine を過去の版で読んだため、判定器には「insert より前の版を読んだ」rw 辺として現れた。

**依頼の「巡回として検出」からの読み替え (段 4 裁定 R4、記録):** TPC-C で NewOrder 行を読むのは Delivery だけで、Delivery は読んだ行を自分で削除する。delete 経路の単一 site の壊しは他の検査 (install 時の最新版検査、validation の再検査と (b)) に止められ、committed な巡回を作らない (段 2 plan・段 3 相談 A / B・親の読み)。insert の意味を壊した履歴は、TPC-C では巡回より先に orphan read として判定器に現れる。そこで完了判定を「β を判定器が検出し帰属する (orphan read)」と「巡回の経路を α で確かめる」の 2 本で満たすことにした。判定器の門 (巡回・integrity 数値項目・存在履歴違反のどれかが 0 でなければ失格) は変えていない。結果として β でも巡回が 1 件出て、その辺も壊した insert に帰属した。delete を壊した正例は作っていない。

## 5. stock Cicada の delete 経路の欠陥 (CCBench への還元候補)

- **発見:** CCBench pin C の Cicada で TPC-C の全 mix (F cell、Delivery を含む) を 4 thread で走らせると、`gc_records()` の `if (latest->ldAcqStatus() != VersionStatus::deleted) ERR;` (`cc/cicada/transaction.cc:853`) で `ERROR: Success` を出して rc=1 で止まる。
- **再現条件:** `tpcc_num_wh=1`、`tpcc_perc_payment / order_status / delivery / stock_level` = 43 / 4 / 4 / 4、`thread_num=4`、`extime=1`、`group_commit=0`、上の CMake 値。GC-PROBE (gc-a、35506.nqsv、bnode046): pin C 無 patch の TRACE=0 build で 5 回中 5 回、C1' + 計装の TRACE=1 build で 5 回中 5 回。L0 の 1 回を合わせて 11 回中 11 回。thread 1 では完走した (1 回)。
- **仮説 (親の静的な読み、未実証):** 2 本の Delivery が同じ NewOrder 行を削除し合う。wts の大きい側は、commit 済みの削除版 D1 の上に自分の削除版 D2 を install する (`validation()` は DELETE の install で最新版の wts だけを見る) が、その後の read set 再検査か (b) の deleted 検査で abort し、`writeSetClean()` が D2 を `aborted` にする。D2 は tuple の最新版として残るので、D1 側の `gc_records()` が最新版の状態を deleted でないと見て `ERR` する。
- **影響:** 少なくとも F cell × 4 thread の Cicada の TPC-C は、原因を特定して直すまで完走しない (他の cell・thread 数・warehouse 数での発生は測っていない)。今回、並行下の delete を判定器に掛けた履歴は得られていない。
- **還元判断:** 原因の特定と修理は CCBench の変更を含み本 wave の所有外。D2277 項 2 (基盤の欠陥は使いながら直す) に沿って、原因の特定から始める修理を次の一手に起票する。上流への push・PR は人間の判断 (D16・D18・D20)。

## 6. TRACE=0 の同一性 (絶対規律 1)

同じ compile command (checkout の root だけ置換して一致を確認) で TRACE=0 build を作り比べた (L0、原本 `runs/l0-a/result-L0-TPCC.json` の `trace_zero_identity`)。

| 比較 | target | TU | objdump の命令列 | 前処理出力 | nm・strings |
|---|---|---|---|---|---|
| (i) pin C 対 pin C + 既存計装 | tpcc / bomb / sbomb | 各 `transaction.cc`・`util.cc`・workload TU の 3 TU | 9 TU とも差分 0 byte | 空行の増減だけ (空行以外の差分行 0) | 全文一致、trace 語の残存 0 |
| (ii) pin C 対 C1' + 既存計装 + 重ね patch | tpcc | 同じ 3 TU | 3 TU とも差分 0 byte | 同上 | 同上 |

md_3 が未比較と明記した tpcc / bomb / sbomb の TU を埋めた。(ii) は C1' の `include/tpcc.hh` の差分 (`#if TRACE` と `#line`) を含めて pin C と命令列が一致することを直接示す。
**途中の修正 1 件:** 最初の重ね patch は `tpcc_cicada.cc` の `#else` 側に `#line 31` を置いていた (正しくは 30)。`ERR` → `NNN` の `__LINE__` が `fprintf` の即値になるので、TRACE=0 の命令列が変わる形だった。親の静的レビューで計測前に見つけ、fix で直してから測った (上の表は直した後)。

## 7. 確かめたこと・確かめていないこと

確かめたこと:
- TPC-C (insert だけの mix の t1・t4、StockLevel を増やした mix の t4、全 mix の t1) で、stock Cicada の履歴が巡回 0・integrity 0・存在履歴違反 0・commit 数一致で判定器に通る。
- insert の版の時刻を壊した Cicada を判定器が non-serializable とし、orphan read と巡回の両方を壊した insert に帰属できる。
- 既存の read 再検査の壊しを TPC-C に重ねた版を巡回として検出し帰属できる (表付きの v3 witness で)。
- TRACE=0 の命令列一致 (12 TU)。
- 判定器の production を変えずに Cicada の v3 trace を読めること (実走)。
- F cell (Delivery を含む全 mix) × 4 thread で、stock Cicada が trace の有無に依らず `gc_records()` の `ERR` で落ちること (原因の経路は未特定)。

確かめていないこと (未対応の範囲):
- **並行下の delete の判定。** stock 自体が落ちるので、delete を含む並行走行の履歴を判定器に掛けていない。delete を壊した正例も作っていない。
- **範囲読み (scan) の phantom と不在の読み。** 範囲への insert・空の scan・不在の key の読みが作る依存は trace に表れない。対応には判定器側の S / Q 行と初期キー集合 (既存の設計 `output/insights/2026-09-21/tpcc-trace-certification-design/README.md` §4) が要る。Cicada に当てるときの差分は、phantom 防止が `node_map_` の node 版比較 (`cc/cicada/transaction.cc` の scan と `validation()` 末尾) であることと、scan の物理候補を `read_internal` の前で記録する位置の選び方。設計だけを記し、実装していない。
- **certified。** 証拠面 (X / P / I に当たるもの) は Cicada に無く、巡回なし = indeterminate が上限。
- **campaign の受理経路** (`orchestrator/campaign/pipeline.py`) への接続。今回の実走は repo 外の起動器で、campaign は Cicada の trace を供給しない。評価計画の「TPC-C は門の対象外」は、これらが揃うまで解消済みとは書かない。
- **BOMB / SBOMB の trace。** TRACE=0 の命令列比較だけをした。
- **内部の版昇格・`INLINE_VERSION_OPT=1`・`WRITE_LATEST_ONLY=1`・`REUSE_VERSION=0`・`SINGLE_EXEC=1`・`group_commit>0`。** 未検証 (版昇格は TRACE=1 で `#error`、md_3)。
- **YCSB の v2 出力 bytes の不変。** 既存計装の bytes を変えず、v2 の式を分岐の else にそのまま残した (静的)。YCSB を重ね patch 付きで走らせた比較はしていない。
- stock の F t4 の異常終了の機序 (§5 の仮説は静的な読み)。
- 今回の検索式と対象で見つからなかったもの (例: 新 patch の bytes pin 0 件) は、その範囲での陰性であって全経路の不存在証明ではない。

## 8. 後続に要るもの (次の版の材料)

- **stock Cicada の `gc_records()` 異常終了の原因特定と修理** (§5)。直るまで、少なくとも F cell × 4 thread の Cicada の TPC-C は完走しない。CCBench の変更 (Codex author、上流 CI の build・format を通す、D2277 項 1)。
- **pin の前進後:** C2' 系へ pin が進んだら、重ね順 (pin → 既存計装 → 重ね patch → 壊し patch) の厳密適用と生死確認を取り直す。
- **phantom と campaign 接続:** 判定器の S / Q 行と初期キー集合、campaign の trace 供給と Cicada の証拠面。TPC-C を評価計画の主要な判定に入れるにはこれらが要る。

## 9. 計算と工程

| tag | request | 内容 | job の所要 | 結果 |
|---|---|---|---|---|
| l0-a | 35456.nqsv | 生死確認 (stock 4 run・TRACE=0 12 TU) | 約 3.5 分 (06:42:18〜06:45:51 UTC) | stock 3 run 合格、F t4 異常終了、TRACE=0 全一致 |
| gc-a | 35506.nqsv | GC-PROBE (build 2・run 10) | 約 1 分 (07:15:38〜07:16:28 UTC) | 10 回中 10 回 `gc_records` の `ERR` |
| j1-a | 35507.nqsv | 本走 (stock 2・正例 2) | 約 1.5 分 (07:15:38〜07:17:10 UTC) | 正例 2 本とも期待した経路で検出 |

計測に使った起動器の job は L0-TPCC・GC-PROBE・J1-TPCC の 3 つ (起動器 sha256: L0 は `ceddfa39c906…a62a2`、GC-PROBE と J1 は `12de8bd7a2e7…a15f3d`)。起動器に残る YCSB 系の job と J1-FOCUS・cell S は今回使っていない。合計約 6 分 (受入・焦点走を除く)。2 node 時間を大きく下回るので、ユーザー確認の対象外。
段 6 の再計算は login で原本を読むだけ (約 5 秒、起動器 sha256 `36ef9330e551…dd3ccd`)。
Codex (gpt-6-sol、reasoning medium): 段 2 plan 1、段 3 相談 2、段 5 author 2 (T・B) と fix 1 (T の `#line`)、段 6 レビュー 2 と fix 1 (起動器の表照合・巡回照合・再計算 mode)。
