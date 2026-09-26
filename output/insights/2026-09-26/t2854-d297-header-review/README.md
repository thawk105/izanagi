# [T-2854] D297 の header 差分受理規則の設計審査 — 変更 header を読む consumer TU を実 compile database の依存列挙で選び、選定 configure ごとに TRACE=0 完全展開と include 活性を比べる規則 v2 を審査した。実装はせず、規則の承認と実装の委任を 1 問、C2' の pin 前進を実装後の別の問いとして裁定へ出す

authority: none
default_effect: no-state-change

- 日付: 2026-09-26
- wave: `t2854-d297-header-review` (branch `worktree-t2854-d297-header-review`)。着手時 local main `6c3913bc5b0c67cb13cf6e38e0d9d55ecf9426d2` (開始 gate rc=0、`verbatim/startup-gate.log`)。wave 中に local main が `1f169cbbd` へ進み (T-2273 の insight と fold のみ)、記録の前に取り込んだ
- 依頼の逐語 = `verbatim/request.md`。裁定 = D2249 項 2 (択 1 の設計審査だけ。審査の承認・実装の委任・C2' の pin 前進の承認は結果を見て別に裁定)。材料 = `output/insights/2026-09-26/t2854-unit11-combined/README.md` §5.2 と worklog の [T-2854] 項
- 既裁定: D297、D774、D780、D2150 (iii)、D2184、D2207、D2225 決定 6、D2230、D2244、D2249
- job dir (親の使い捨て script・生 log・codex receipt・compile database): `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2854-d297-header-review/`

## 0. 結論

1. **規則案 v2 (§4) を審査結果とする。** header の M 差分に限り、実 CMake configure の compile database の全 entry から、`-MG` を使わない依存列挙 (旧・新 × TRACE=0/1) で変更 header を読む entry (consumer) を選び、選定 configure 集合 (stock と、変更 header を読む production target の protocol の genome 空間) の各 configure で、全 consumer entry の TRACE=0 完全展開 (`-E -P -dD`) と include 活性 (入退場 file 列) を GCC 11.4 / 12.3 の別 configure で旧新比較する。保証名は「選定 configure 集合の compile database に載る変更 header consumer entry における、TRACE=0 完全展開と include 活性の同一性」。
2. **D780 は維持する。** compile database は選定 source 比較の文脈入力であって、admission build・build receipt との対応を証明しない。link object・trace symbol / data・receipt を結ぶ D780 項 2 の別防壁ではなく、この比較を trace 完全除去の防壁とは呼ばない (D780 項 1 の「必要条件の一つ」を継承)。D774 の限界は据え置く。規律 1・2 は緩めない。
3. **敵対相談で 2 つの must-fix が成立し、v2 に反映した:** (A1) `-MG` は build 時生成 header の先で依存探索を止め、間接 consumer を落として緑にしうる → 生成物を用意し `-MG` なしで全 entry の依存列挙を成功させる。(A2 / B1) genome configure の「その protocol の entry だけ」を比べると、同じ configure で実際に変わった他 protocol の argv を捨てる (実測: `CCBENCH_KEY_SORT` が mocc 以外に d2pl・ermia・si・ss2pl の define も変える) → 選定 configure の全 consumer entry を比べ、保証名に「選定 configure 集合」を明記する。
4. **前提の実測 (login、stock configure 1 構成):** compile database は C・C2' とも 135 entry (source root 配下 117)、root 正規化で両側一致。変更 header (include/tpcc.hh・include/trace.hh) を TRACE=0/1 のどちらかで読む entry は両側とも 21 entry / 12 file で、単位 11 の直接 include 列挙と一致した (この構成では間接だけの consumer は 0。一般の閉包証明ではない)。login で試した consumer entry の前処理 (`-E`) は masstree の `config.h` (build 時生成) が無く失敗した。規則の実行では選定 entry の前処理に要る生成物を用意する段が要り、login では行えない (build は hook が拒否)。
5. **検査器の実装・pin 前進・branch push・計算投入はしていない。** pin は C のまま、C2' `40a7f4ac` は D297 の合格も TPC-C の certified も名乗らない (D2244 項 4)。GCC 12.3 と genome 文脈での C → C2' の正例は未実測。
6. **裁定へ出す形 (§7):** 問い 1 (今) = 規則 v2 の承認と実装の委任 (規則だけ承認し実装を留保する答えも可)。問い 2 (実装後) = 改訂後の検査器で C → C2' が GCC 2 版とも pass した結果・実費・pin 波及を示して、C2' の pin 前進を承認するか。

## 1. 依頼の完了条件と状態

| 完了条件 (`verbatim/request.md`) | 状態 |
|---|---|
| consumer TU を列挙し、TU ごとの文脈で header 差分を条件つきで受け付ける規則の設計を審査する | **済** — plan 1 本・敵対相談 2 本・段 4 裁定 (§3、§4) |
| insight と decisions fragment に記録する | **済** — 本 insight と decisions fragment (D 番号は land 時の fold が採番) |
| 裁定に出す承認事項 (実装の委任、C2' 40a7f4ac の pin 前進) の案 | **済** — §7 |
| 検査器の実装・pin 前進・branch push をしない | 守った (実装面の差分ゼロ) |
| D780 項 2 の維持、比較を trace 完全除去の防壁と呼ばない、規律 1・2 を緩めない | 守った (§4 R7、§5) |
| [T-2854] 項の fragment を land 前に main を取り込んで合わせる | 記録の前に main `1f169cbbd` を取り込み、base digest をその現物で取った。land 直前に再照合する |

## 2. 前提の実測 (親、login、段 1)

C (`68106660686232781bca3be792a750d3e19d7a8a`) と C2' (`40a7f4acb174ca43cb590f40d13847216a1564bc`) を CCBench submodule の一時 worktree (job tmp) に取り出し、
`cmake -S <src> -B <build> -DCMAKE_BUILD_TYPE=Release -DCMAKE_EXPORT_COMPILE_COMMANDS=ON -DCMAKE_PREFIX_PATH=/work/1/SFC/tanab/izanagi-a2-deps` (両方 rc=0、build はしない)。

| 測ったこと | 結果 | 出所 |
|---|---|---|
| compile database の entry 数 | 両側 135 (78 file)。source root 配下は 117。root を正規化すると両側の全 entry が一致 | job dir `evidence/compile_commands-C.json`・`-C2p.json` |
| 依存列挙 (実 argv + `-M -MG -DTRACE={0,1}`、全 135 entry) | error 0。変更 header を読む entry は両側とも 21 entry / 12 file (9 protocol の `tpcc_<p>.cc` と silo・si・mocc の `transaction.cc` × target)。直接 include の正規表現 (単位 11 probe) の 21 entry と完全一致 | `verbatim/evidence/consumers-c.txt`・`consumers-c2p.txt` |
| TRACE による依存の差 | mocc の `transaction.cc` は TRACE=1 でだけ trace.hh を読む。C2' では `tpcc_<p>.cc` 9 本が TRACE=1 で trace.hh も読む (C では読まない) | 同上 |
| consumer entry の前処理 (`-E`、login で試した分) | rc=1 (`config.h` 不在)。masstree の `config.h` は build 時に `masstree_build` target (bootstrap + configure + make + ar) が作る (`cmake/ThirdParty.cmake`)。login の `cmake --build` は hook が拒否する | job dir `tmp` の実行記録、`external/ccbench/cmake/ThirdParty.cmake` |
| genome を変えた configure (C2'、silo genome の 1 点と、他 protocol の option を全部 1 + TRACE=1 の 2 通り) | source root 配下の (file, target) 集合は 3 通りとも同じ 117。変わるのは `-D` だけ。silo genome では silo の 12 entry の `WAL` だけ。`CCBENCH_KEY_SORT` は d2pl・ermia・mocc・si・ss2pl の 60 entry に効く | `verbatim/evidence/genome-configure-measure.md` |

- production の build 経路 (`orchestrator/campaign/buildcache.py` の `_v2_commands`) は Release・sanitizer OFF・`genome.cmake_defines()`・`-DCCBENCH_TRACE=<0|1>` を configure に渡し、target は `ycsb_<protocol>.exe` だけ。genome 空間は silo 8・mocc 8・tictoc 24・cicada 24 (`orchestrator/campaign/genome.py`)。
- 現行検査器の 16 文脈は silo の有効 genome 8 × `GLOBAL_VALUE_DEFINE` 無 / 有で、実 compile command ではない (`tools/check_trace0_preprocess_identity.py` の `check`、`orchestrator/campaign/source_digest.py` の `_context_overlays`)。
- GCC 11.4 の stock 構成で 21 entry の完全展開と include 活性が C と C2' で一致することは、単位 11 の計算 1 走 (request 29455.nqsv) が既に示した。GCC 12.3・genome 文脈での一致は未実測。
- 使い捨て script (`consumers.py`・`tu_compare.py`) は repo に入れず job dir に残した (sha256 = `verbatim/evidence/job-dir-sha256.txt`)。`tu_compare.py` は login で `config.h` 不在のため比較まで到達していない。

## 3. 審査の経過 (段 2〜4)

- **段 2 plan** (`verbatim/s2-plan.md`): brief の provisional P1〜P8 におおむね賛成し、依存列挙を文脈ごとに取り直す、compiler ごとに別 configure を作る (argv[0] の差し替えはしない)、比較の予定集合を先に固定する、header と .cc が同居すれば両検査の積、変異に間接 consumer を必ず入れる、を補った。
- **段 3 相談 A** (正しさ境界、`verbatim/s3-consult-A.md`): must-fix 2 (A1 `-MG` の途中停止、A2 protocol 絞りで実 configure の効果を捨てる) と should 3 (A3 database ≠ build の母集合、A4 TRACE の実効値、A5 正規化で消えるもの) が成立。D780 項 2 の別防壁を単独設計したという攻撃、.cc 拒否・mocc 例外・承認順序を緩めるという攻撃、brief の数値の一般化は不成立。
- **段 3 相談 B** (実効性と過剰・削除、`verbatim/s3-consult-B.md`): must-fix 1 (B1 genome 文脈の保証範囲、A2 と同じ) と should 4 (B2 64 genome 一律は過大、B3 変異に再演と既存拒否が混じる、B4 承認事項に実装形まで入れすぎ、B5「全 TU に build 必要」は言い過ぎ)、nit 1 (B6 2 段 2 問で足りる) が成立。全 entry 完全比較への置換、probe の無修正流用、GCC 2 版・非零・予定集合照合の削除、段 2 に効かないという疑義は不成立。
- **段 4 裁定** (`verbatim/s4-ruling.md`): 成立した所見を全件採用して規則を v2 にし (§4)、実装しない裁定なので段 5・6 を飛ばした。

## 4. 規則案 v2

- **R1 適用範囲:** raw diff の M・mode 不変の header 拡張子 path にだけ新分岐を足す。A/D/R/C・mode 変更・非 C/C++ (CMake を含む) の拒否、.cc の単体比較 (16 文脈と mocc の trace.hh 1 行例外、D2207) は変えない。header と .cc が同じ差分にあれば両方の合格を要する。現行が拒否する header のコメントだけの変更も、条件を満たせば受理される (意図した受理集合の拡大)。
- **R2 source と生成物:** 旧・新を worktree で取り出して tree を照合する (`git archive` は export-ignore で cc/oze を落とす)。FetchContent の第三者 source は両側同一の固定 source。選定 configure ごとに、前処理に要る生成物 (masstree の `config.h`) を用意する。実行場所は計算ノード。
- **R3 consumer:** 選定 configure の compile database の全 entry (target・argv を鍵) を母集合とし、`-MG` を使わない依存列挙を旧・新 × TRACE=0/1 で全件成功させる (1 件でも失敗・欠落 header があれば拒否)。変更 header を 1 度でも読む entry の和集合を consumer とし、変更 header ごとに選定集合全体で consumer 0 件なら拒否。旧新の database が root 正規化後に entry 集合・argv で一致しなければ拒否。
- **R4 文脈 (選定 configure 集合):** stock configure (production と同じ Release・sanitizer OFF・`CCBENCH_TRACE=0`) と、変更 header の consumer を含む production target (現行 buildcache では `ycsb_<protocol>.exe`) の protocol が genome 空間を持つとき、その空間の全 genome の configure。各 configure で**全 consumer entry**を比べ、同一の (entry, argv) は 1 回に集約する。選定集合は report に列挙する。C → C2' では production の consumer が `ycsb_silo`・`ycsb_mocc`・`ycsb_si` (si は genome 空間なし) なので、stock + silo 8 + mocc 8 = 17 configure。
- **R5 比較:** 各 (compiler, configure, entry) で旧・新の完全展開 (`-E -P -dD`) と include 活性 (`-E` の line marker の入退場 file 列) を、照合済み prefix だけを置換する root 正規化の後に byte 比較する。compiler は GCC 11.4 / 12.3 をそれぞれ別 configure・別 database で (D2150 (iii) の先例)。比較の予定集合を先に固定し、実行済み集合と厳密一致を求める (0 件・欠落は拒否)。`__DATE__` 等が出力に混入し再現条件を固定できなければ拒否。
- **R6 TRACE の実効値:** 比較時の TRACE=0 と依存照会時の TRACE=1 を前処理の macro 状態で確認する。確認できない entry と不透明な argv (`@file`・`-Wp,`) は拒否。
- **R7 保証名と文言:** 「選定 configure 集合の compile database に載る変更 header consumer entry における、TRACE=0 完全展開と include 活性の同一性」。line marker 全体・診断位置の同一性は名乗らない。D780 項 1 の文言 (この検査は D297 の保証を証明するものであり、計測ビルドからの trace 完全除去に対しては必要条件の一つである) を継承する。compile database は文脈入力であって admission build・receipt との対応を証明しない。

## 5. 残る穴 (規則 v2 が覆わないもの)

- 選定 configure 外の文脈: 選定外の genome 空間 (C → C2' では tictoc・cicada)、Debug などの build type、opt-in target (`CCBENCH_BUILD_MICROBENCH` 等)、将来の production option。
- compile database に載らない TU (configure されない target・生成 source)。
- GCC 以外の compiler (D2150 は clang の比較未完了を受容した)。
- admission build の全 TU・link object・trace symbol / data・build receipt との未結合 (D780 項 2 の別防壁。静的に解決できない間接値の限界と同じ閉包でだけ設計する)。
- TPC-C の campaign 配線 ([T-2854] 残り (2)) で tpcc target が production に入ると、R4 により silo・mocc の tpcc entry も genome 文脈に入る (同じ選定規則で広がる。配線より前の pin 前進では tpcc entry は stock と、silo・mocc の genome configure の中で比べられる)。
- 段 2 (`include/tpcc.hh`・`include/tpcc/tpcc_initializer.hh` などの変更) にも規則は適用できる (`tpcc_initializer.hh` は `tpcc.hh` から読まれ、依存列挙で consumer が選ばれる)。合格するかは段 2 の実差分で確かめる。

## 6. 実装 wave へ渡す変異の事前登録案 (本 wave では登録・実行しない)

新しい分岐が誤って緑にする形だけ。既存の拒否 (CMake 差分・.cc の include 行・件数・A/D/R/C) は回帰 test として維持し、変異にしない (相談 B 所見 3)。

| # | 変異 | 殺す実装 (期待する拒否) |
|---|---|---|
| 1 | 直接 include を持たず別 header 経由でだけ変更 header を読む TU (合成 fixture) で、TRACE=0 側の値を変える | consumer を直接 include 列挙へ劣化させた実装 (完全展開不一致で拒否) |
| 2 | header の TRACE=0 側 (`#if !TRACE` 内を含む) の値変更 | 完全展開不一致 |
| 3 | header 内の必須 include を `#if TRACE` 内へ移す | include 活性不一致 |
| 4 | 生成 header が無いと依存探索が途中で止まる形 (A1) | `-MG` へ劣化させた実装 (依存列挙失敗で拒否) |
| 5 | 選定 configure で、他 protocol の consumer の argv だけが変わる形 (A2、合成 fixture) | その entry を比較から外した実装 |
| 6 | consumer 0 件、比較予定集合から 1 件を落とす | 拒否 |
| 7 | 実 CCBench の代表負例 H-line (`tpcc.hh` の `#line 56` を消す) を新分岐経由で 1 回 | TPC-C consumer の完全展開不一致 |

単一理由性 (DW-M01) は実装後に確かめる。

## 7. 裁定へ出す承認事項の案

**問い 1 (今) — 規則 v2 (§4 R1〜R7 と §5 の残る穴) を承認し、その実装を Codex author の wave に委任するか。**

| 答え | 帰結 |
|---|---|
| (a) 承認 + 委任 (推奨) | D297 の「header 一律拒否」を §4 の条件つき受理へ改訂する方針が決まり、実装 wave (検査器の新分岐・合成 fixture・§6 の変異・実 CCBench の C → C2' の実走 GCC 2 版) を起こせる |
| (b) 規則だけ承認し実装は留保 | 設計の承認だけを記録する。検査器と pin は現状のまま |
| (c) 却下 | 現行 D297 のまま。C2' は拒否されたまま、段 2 でも同じ諮問が再び要る |

費用は未実測なので上限を書かない。実装 wave は最初に計算ノードで 1 configure + 生成物 + 前処理の生死確認 (DW-G01) を取り、選定 17 configure × 2 compiler × 旧新の見積りを実測単価で出す。1 タスクの job 合計が 2 node 時間以上ならユーザー確認後に投入する (D2212 項 4)。Codex author は 1 wave を起点に修正を含め 1〜2 wave 以上 (上限ではない推測)。単位 11 の probe の部品 (compile argv の出力 option 除去、前処理・line marker の正規化、source tree の照合、計算 job の手順) は出発点に使え、直接 include の consumer 列挙と固定 21 件は使わない。

**問い 2 (実装後) — C2' `40a7f4ac` の pin 前進を承認するか。** 前提 = 改訂後の検査器で C → C2' が GCC 11.4 / 12.3 とも pass した結果、実費、pin 前進の波及 (先例 D2150 / D2184 の gitlink・`CCBENCH_FULL_SHA`・`CURRENT_PIN` の同時更新) を示すこと。条件つき事前承認は推さない (未実測の GCC 12.3・genome 文脈の正例と pin 波及を合格前に引き受けることになる)。

それまで pin は C のまま、C2' は D297 の合格も TPC-C の certified も名乗らない。「pass」は改訂後の検査器の新しい結果にだけ使い、単位 11 の証拠を遡って D297 pass と呼ばない。branch `izanagi-tpcc-v3-silo-mocc` の push は人間の手番 (任意の時点、force 不要)。

## 8. 経過

- **段 1:** brief (`verbatim/s1-brief.md`、provisional P1〜P8)。前提の実測は §2。段 2 の後に genome 別 configure の実測を足し、段 3 の必読に加えた (plan は読んでいない)。
- **段 2・3:** 受理集合を変える設計で正しさ防壁に触るので残した (DW-C00)。plan 1 本 → 敵対相談 2 本 (A = 正しさ境界・既裁定との境界、B = 実効性と過剰・削除)。依頼文 = `verbatim/s2-plan-prompt.md`・`s3-consult-A-prompt.md`・`s3-consult-B-prompt.md`。
- **段 4:** 実装しない裁定 (4 → 7 → 8 → 9)。実装面の差分ゼロなので変異 matrix は免除、受入全走は行う (DW-S04)。
- **段 7:** 一次資料から事実を再抽出した docs-only なので、記録の独立 read-only レビューを 1 本行った (DW-C00、`verbatim/s7-review-R-1.md`、依頼文 `verbatim/s7-review-R-prompt.md`)。GO、should 1 件 (「全 TU の前処理に `config.h` が要る」は言い過ぎで、確定したのは login で試した前処理の失敗と、選定 entry に要る生成物を用意すること) を直した。数値 (135 / 117 entry、21 / 12、17 configure、Codex 実績) と裁定・名乗りの境界は検算で一致。
- Codex 子は計 4 本 (段 2 plan・段 3 相談 2・段 7 記録レビュー 1)、全子 read-only。受領証の `actuals` の合計は model call 55、wall 849.0 秒 (plan 13 call・356.2 秒、相談 A 13 call・166.7 秒、相談 B 13 call・172.6 秒、記録レビュー 16 call・153.6 秒)。
- local main の前進 (6c3913bc5 → 1f169cbbd) は別 session の通知を契機に自分で読み直して確かめた (T-2273 の insight・fold だけで本審査に影響なし)。

## 9. 主張しないこと

- 規則 v2 で C → C2' が合格すること。GCC 12.3・genome 文脈の正例は未実測で、GCC 11.4 の stock 構成での一致 (単位 11) だけが実測済み。
- 間接 include だけの consumer が CCBench に一般に存在しないこと (実測は stock configure 1 構成・C と C2' だけ)。
- genome を変えても compile database の entry 集合が変わらないこと一般 (実測は 3 通りの configure だけ)。
- 規則 v2 が trace のコンパイル時完全除去を証明すること (D780 項 1)。
- 実装・計算の費用の上限。

## 10. 再現資料

- 本 insight の `verbatim/`: 依頼 `request.md`、brief `s1-brief.md`、段 2・3 の依頼文と出力 (`s2-plan*.md`・`s3-consult-*`)、段 4 裁定 `s4-ruling.md`、開始 gate `startup-gate.log`、実測の結果 `evidence/` (consumer 一覧 2 本・genome 別 configure の結果・job dir の script と compile database の sha256)。
- job dir `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2854-d297-header-review/`: `evidence/` (script・compile database 4 本・依存列挙の JSON)、`verbatim/` (既裁定の逐語)、`codex/` (receipt)、`prompts/`、`out/`。
- 一時の CCBench worktree (job tmp の `ccb-c`・`ccb-c2p`) と build dir は wave の終端で撤去する。
