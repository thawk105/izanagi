# CC ごとの gen-opt ベース準備状況 (5 段) — 実物で確かめた原票と親の裁定 (md_9、2026-09-30)

- 出所: §0〜§3 は本 wave の読み取り専用の調査役 (Claude opus の子、file の最終更新 2026-09-30 12:19:11 JST) の原票をそのまま置いた。
  親は `orchestrator/verifier/model.py:37,77-82`、`orchestrator/campaign/source_digest.py:85-86`、`orchestrator/campaign/p3_s4_loop.py:122-127`、
  `output/insights/2026-09-29/mocc-validation-fix/README.md` §0 を実物で照合して一致を確かめた。他の行は子の読みのまま。
- **重さの正本は末尾の §4 (親の裁定)。** §1 の重さは子の提案で、§4 で 2 か所を直した。

- 調べた木: `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-gen-opt-cards-by-protocol` (HEAD `7648ea167`)、CCBench gitlink = pin C `68106660` (`git submodule status`)。
- 以下の path:line はこの木の実物。`external/ccbench/...` は pin C の中身。決定は `docs/decisions.md` の該当節だけを読んだ。
- 重さの定義は依頼どおり (0 / S=1 / M=2 / L=3)。**certified を出せない段を「有」とは書かない。検査を甘くして埋める案は数えない。** 重さは提案で、親が裁定する。
- 段 4 は「gen-opt (段 A・B、D2289) に要る関数単位の口」を基準に重さを付け、backoff の literal hole (既存の `include/backoff.hh` の穴を protocol 引数で差し込むだけ) の重さを別記した。

## 0. 共通の事実 (全 CC に効くもの)

| 事実 | 根拠 |
|---|---|
| certified の必要条件は `Integrity.clean()` で、その中に `proof_surfaces.certification_gate_satisfied()` (X と P の emitter が compiled source の `#if TRACE` 内に在る) が入る。対象 protocol は `{"silo","si","mocc"}` だけで、それ以外は X/P/I とも `unavailable` → clean が偽 → verdict の上限は indeterminate | `orchestrator/verifier/model.py:37`、`:77-82`、`:246-247`、`:275-277`、`:517`、`:556-570` |
| parser は v1 の C 行 (5 欄) を拒否し、v2 (7 欄) と v3 (10 欄、TPC-C) だけを読む | `orchestrator/verifier/parse.py:355-366` |
| pin C で `izanagi_trace::` を持つ source は silo・mocc・si の `transaction.cc` だけ。X/P emitter は silo (`cc/silo/transaction.cc:432` P、`:629/:653/:674` X) と mocc (`cc/mocc/transaction.cc:1011` P、`:1195/:1213/:1238/:1254` X) だけ。si は v1 helper `emit_commit` (`cc/si/transaction.cc:540`) | `grep` 実測 |
| pipeline の trace 許可は binary 名 prefix。`ycsb_*` は protocol を問わず通り、`tpcc_*` は段 1 の mix (payment 43 等) のときだけ通り、しかも v3 でなければ reject | `orchestrator/campaign/pipeline.py:458-466`、`:702-707` |
| build は protocol 汎用 (`ycsb_<protocol>.exe`) | `orchestrator/campaign/buildcache.py:632`、`:658` |
| EVOLVE-BLOCK の対象 source は 3 つ: `include/backoff.hh`・`cc/silo/transaction.cc`・`cc/mocc/transaction.cc` | `orchestrator/campaign/source_digest.py:85-94` |
| `include/backoff.hh` の `Backoff::backoff` は silo 以外の全 CC (tictoc・cicada・ermia・si・oze ほか) からも呼ばれる → backoff の literal hole は他 CC へ protocol 引数で差し込める見込み (先例 D2248) | `cc/tictoc/transaction.cc:8,491`、`cc/cicada/include/transaction.hh:166`、`cc/ermia/transaction.cc:7,846`、`cc/si/transaction.cc:7,605`、`cc/oze/include/transaction.hh:12,146` |
| 比較 harness・単回 loop・条件 gate・転移 runner は silo と mocc 以外を拒否 | `orchestrator/campaign/p3_s4_loop.py:122-128` (`campaign_pin_for_protocol`)、`:149-154` (`backoff_genome`)、`:3497` (argparse)、`orchestrator/campaign/t2849_comparison_harness.py:789` (argparse)、`orchestrator/campaign/condition_meaning_gate.py:1252`、`orchestrator/campaign/t2851_transfer_runner.py:188,209` |
| between-run floor の生成は D1373 の関門 (compiled source に `izanagi_trace::` 呼出しがあること) で拒否側に倒れる。stock baseline 表は silo・mocc・tictoc | `orchestrator/campaign/between_run_floor.py:59-86`、`:147`、`:318`、D1373 |
| genome 空間は silo・mocc・tictoc・cicada の 4 つだけ | `orchestrator/campaign/genome.py:106,124,147,178`、`SPACES` (同 file 直後) |
| 登録済みの認定較正 (`output/env/pegasus/calibration/registered/`) は ycsb_silo 4・ycsb_mocc 5・ycsb_tictoc 2 (cicada 等は 0)。between-run floor file は silo だけ (pegasus・linux-baremetal) | file の grep 実測 |
| 関数方策の一式 (`silo_function_policy_api.hh` の namespace `izanagi_silo_api`/`izanagi_silo_policy`、`axis_silo_function_policy.py` の `SOURCE_REL="cc/silo/transaction.cc"`・reason 表、`silo_policy_{grammar,ir,compile,coverage,recon,contrast*}.py`) は silo 専用。sort・trigger-gating も `cc/silo/transaction.cc` 専用 | `orchestrator/campaign/axis_silo_function_policy.py:4-27`、`axis_trigger_gating.py:24`、`orchestrator/campaign/silo_function_policy_api.hh:1,9-13`、`patches/silo-sort-variant.patch` (+++ `cc/silo/transaction.cc`) |
| D2289 決定 4: 新しい仕組みには既存ゲートに加えて (i) 検査用記録の差し込み点を LLM の編集範囲外に固定、(ii) 仕組みごとの小モデル全場面検査 を課す。どの CC をベースにしてもこの 2 つは別途要る (本表の重さには含めない) | D2289 |

## 1. CC × 5 段の表

凡例: 状態 = 有 / 部分 / 無 / 不可 (定義上 certified に到達しない)。重さ = 欠けている分を埋める提案 (0/S/M/L)。

| CC | (1) trace 計装 | (2) certified の証拠面 | (3) 性能計測 | (4) LLM が書く口 | (5) 比較基盤 | 合計 (点) |
|---|---|---|---|---|---|---|
| **silo** | 有・0 — pin C の `cc/silo/transaction.cc` に YCSB v2 (C `:602`・E `:698`)。TPC-C v3 は CCBench 枝 F `izanagi-tpcc-v3-silo-mocc-fmt` (`25898d00`) にあり pin 外 (TPC-C だけなら S) | 有・0 — X/P あり (§0)。ただし取引内の値の欠陥 (T-2885) は DSG に映らず、修正 `7e5fa528` は branch のみ (pin 前進で S) | 有・0 — `SILO_SPACE` (genome.py:106)、認定較正 4、between-run floor 3 workload、s8b floor | 有・0 — backoff magnitude・sort・trigger-gating・function-policy の 4 軸 | 有・0 — harness の既定。campaign pin は旧 pin `511c9538` (p3_s4_loop.py:119) | **0** |
| **mocc** | 有・0 — pin C の `cc/mocc/transaction.cc` に YCSB v2 (C `:1161`・E `:1268`)。TPC-C v3 は枝 F (pin 外) | 部分・S — X/P は pin C にある (D2236)。ただし stock の validation の隙間で rr95 の stock が G2 を出す (pin C で 5/112 走、t2872)。修理 X `f4a5169e` (D2304) は branch のみで D297 は「意図した修理差分で不合格」、pin 前進時の扱いは未裁定。V25 の 1 thread 盲点 (D2246) もある | 部分・S — `MOCC_SPACE` (genome.py:124)、認定較正 5 (D2248)、within-run CV (D2083)、floor baseline 表に登録 (between_run_floor.py:67) で関門も通るはずだが between-run floor は未実測 | 部分・M — backoff literal (D2248) と温度述語 hole (proof 用のみ、D2134 項 9 で探索は未認可) だけ。関数方策の口は無い (md_10 で設計中、未着地) | 有・0 — D2248 (protocol 引数)、D2261 (5 手法 × 3 workload 疎通、15 系列 b-complete) | **4** |
| **cicada** | 部分・S — pin には無し。out-of-tree `patches/instr-cicada-trace.patch` (YCSB v2、D2279) と重ね `instr-cicada-trace-tpcc.patch` (TPC-C v3、C1' 以降のみ、D2294)。OPT×PROMOTION は TRACE=1 で `#error` (D2279 項 5)。patch のまま据え置く裁定 (D2305 項 4) なので pipeline は現状この trace を使えない | 無・L — proof 集合外で上限 indeterminate (D2279 項 4、D2302)。D2300 の B/U/P 設計があり、D2305 項 4 で中間案 M (判定器を変えず repo 外起動器で合否) を採用、未実装 (T-2874)。M は certified ではない。certified には判定器の protocol 別の門 (案 A、campaign lock 閉包の再批准を伴う) が要る | 部分・S — `CICADA_SPACE` 24 (genome.py:178)。うち promotion 有効の 8 genome は pin で build 不能、修理 G 後も判定器が直列化違反を検出し失格 (D2308)。認定較正 0、floor baseline 表に無く D1373 で拒否 (D2291 は repo 外の診断 driver `tools/vhash_cicada_tuning/` で測り floor に接続しない) | 無・L — EVOLVE-BLOCK 対象外。VHash 系 variant (`cicada-forwarding-*` 等) は人の書いた patch で LLM の穴ではない。backoff literal だけなら S | 無・S — harness・条件 gate が拒否。VHash の比較は repo 外起動器 (D2302 項 4) | **9** (段 4 を backoff だけにすれば 7) |
| **tictoc** | 無・M — pin に `izanagi_trace` 無し、patch も無し。単版で `lockWriteSet` が sort → 施錠 (`cc/tictoc/transaction.cc:548-554`)。版 ID は `TsWord.wts` 47 bit (`include/tuple.hh:13-20`) を (1, wts) に写す案 (key ごとの単調増加は要実証) | 無・M — proof 集合外。Silo の X (writePhase の施錠被覆) と P (sort の置換保存) をそのまま移せる構造で、判定器の意味は単版 DSG のまま。protocol を proof 集合へ足す判定器の変更 + 壊し patch 一式 (先例 mocc T-2294・D2207・D2236) | 部分・S — `TICTOC_SPACE` 24 (genome.py:147)、認定較正 2 (rr50・rr95、D2083)、floor baseline 表あり (between_run_floor.py:77、D2127) だが trace hook が無いので D1373 で拒否 | 無・L — 関数方策の口は無い (MOCC 版ができれば移植で M に下がる見込み)。backoff literal だけなら S | 無・S — harness・条件 gate が拒否。D2248 と同形で足せる | **9** (段 4 を backoff だけにすれば 7) |
| **ermia** | 無・M — pin に無し。si の hook を流用できる、版 ID は raw `cstamp` (dormant な `ssn_commit()` の `cstamp<<1` に合わせると全 read が orphan になる罠、`docs/ccbench-anatomy.md:210`) | 無・L — 多版 (SI + SSN)。X/P は当てはまらず、Cicada の B/U に当たる多版の証拠面の新設計と protocol 別の門が要る。**stock の既知リスク:** readers bitmap が `1 << thid_` で int のシフト (`cc/ermia/include/transaction.hh:123,134`、`thid_` は `uint8_t` `:30`)、48 thread では thid ≥ 31 で未定義動作。直列化への影響は未実測 | 無・S — genome 空間・較正・baseline なし (先例 D1360 の空間追加) | 無・L (backoff だけなら S) | 無・S | **10** |
| **si** (参考) | 部分・S — pin は v1 (`cc/si/transaction.cc:540`、parser が拒否)。v2 は `patches/instr-si-trace-v2.patch` (D2252) | **不可** — proof 集合に入っているが X/P emitter が無く evidence-absent で clean が常に偽。そもそも stock SI は write skew で non-serializable を出す (D2252 項 4・5、V36 で巡回 2,236)。直列化可能性の certified は定義上出ない。出すなら SSI 化 = 別 CC (ERMIA 相当) | 無・S | 無 | 部分 — 検出期待表 (D2252) のみ | 対象外 |
| **mvto** (参考) | 無・M+M — pin の WORKLOADS は `bomb tpcc` だけで YCSB が無い (`cc/mvto/CMakeLists.txt:3`)。YCSB driver か TPC-C v3 が要る | 無・L — 多版 | 無・S | 無・L | 無・S | **11〜12** |
| **ss2pl** (参考) | 無・M — pin の WORKLOADS は `bomb tpcc`。YCSB は out-of-tree `patches/ss2pl-lock-protocol-study.patch` (D790) だけ。そこにある計器は待ちグラフ (D2094) で直列化 trace ではない | 無・L — 版 ID を持たない 2PL の意味論 (依頼の定義で L) | 無・S (D790 の 3 軸は study 用で genome 空間ではない) | 無・L | 無・S | **10** |
| **oze** (参考) | 無・M — YCSB は有る (`cc/oze/CMakeLists.txt:3`)。trace 無し | 無・L — 多版 graph (MVSG)。OCC/Oze の切替条件は常に false の TODO (`cc/oze/include/transaction.hh:1157-1171`) | 無・S | 無・L | 無・S | **10** |

合計は段 4 を「関数単位の口」で数えた値。d2pl は WORKLOADS が `sbomb dbomb` だけ (`cc/d2pl/CMakeLists.txt:3`) で表から外した。

## 2. CC ごとの補足

### silo
- 5 段すべて有。gen-opt の段 A の試し 1 本 (`gen-opt-stage-a-candidate` の「競合度順の施錠」) も Silo の上で設計されている。
- 残る事実: (a) 取引内の値の欠陥 (read-own-write・2 度目の update の値) は DSG 判定器に映らず、U0 の照合器 (D2b) で赤 (`output/insights/2026-09-29/silo-intra-txn-fix/README.md` §0)。修正 `7e5fa528` は branch のみ。(b) TPC-C v3 は枝 F (GitHub CI 緑、D2305 項 5 付近の記録) で pin 前進待ち。どちらも「pin 前進 wave」1 本 (S) で片付く見込み。

### mocc
- trace・X/P・比較基盤は揃っており、Silo の次に近い。
- **ただし stock に validation の隙間があり、read-heavy で stock が G2 を出す** (pin C で 5/112 走、`output/insights/2026-09-29/t2872-mocc-g2-split/README.md:66,71`)。D2261 項 6 の「候補 slot 25 件中 6 件で G2」はこれと同根と読める (t2872 の結論)。修理 X は F の子の branch にあり、G2 0/112・class A 0 (`output/insights/2026-09-29/mocc-validation-fix/README.md` §0・§4)、D297 は意図した差分で不合格、pin 前進時の扱いは別裁定 (D2304 項 3)。**修理を pin に入れるまで、rr95 で MOCC をベースにすると stock・候補とも一定率で reject される**ので、段 2 を「部分・S」とした。
- F → X で厳密適用から外れた patch は 0 本、C → F で外れるのは broken-mocc-early-unlock・hot-update-unlock の 2 本 (同 insight §5)。
- 段 4 は md_10 (MOCC 版の関数方策の軸の設計、計算なし) が並走中で未着地。Silo の文法・IR・compile の CC 非依存部を流用できれば M、一式を作り直すなら L。

### cicada
- trace・判定器の読み込みは実証済み (stock 巡回 0、壊し 3 本とも non-serializable・帰属 20/20、D2279 理由)。最良設定も巡回 0・上限 indeterminate (D2302)。**それでも certified は出ない** — これは判定器の仕様 (proof 集合外) で、D2279 項 4 が明示的に対象外と決めている。
- 採用済みの中間案 M (D2305 項 4) は「照合の中身を明記した測定値」として論文で扱ってよいが、izanagi 内部では certified と呼ばない (同項 (2))。gen-opt で Cicada 上の候補を certified 選択に載せるには案 A (§6 の設計から着手、D2305 項 4 (3)) が要る → L。
- M の対象範囲は YCSB の point read/update、`REUSE_VERSION=1`、`INLINE_VERSION_OPT=0`、`group_commit=0` に限る (D2300 項 4)。CICADA_SPACE の全域ではない。
- stock の既知欠陥: abort 時の use-after-free は未修正 (D2305 項 10)。gc_records・scan key の修理は branch 2 commit と同差分の out-of-tree patch (D2310)、build 不能 2 件は F の子 G (D2308)。
- 段 1 の「S」は、patch のまま据え置く裁定 (D2305 項 4) の下で pipeline が計装 patch を重ねて build する経路を足す分。枝へ移して pin を進める道は人間の判断。

### tictoc
- 単版・sort 後施錠という Silo と同じ骨格なので、X/P の移植は MOCC の先例 (T-2294 の計装 + 壊し 3 本 + proof、D2207・D2236) と同じ作業量に収まる見込み。判定器の意味は変えずに、proof 集合へ protocol を足す変更 (model.py:37) が要る — 判定器の production と campaign lock の閉包に触れる点は D2300 が cicada 案 A の費用として挙げたものと同種。
- 未実証の前提: 同じ key の上で wts が書きごとに真に増えること (新しい書き手の commit_ts > 旧版の rts ≥ 旧版の wts という論証で成り立つ見込み)、`TIMESTAMP_HISTORY`・`PREEMPTIVE_ABORTS` の各組で R 行が選んだ版を忠実に写すこと。
- 段 3 は空間・較正・baseline 表が揃っており、trace hook が pin の compiled source に入った時点で D1373 の関門が開く (between_run_floor.py:76 のコメントどおり)。

### ermia
- trace は si の hook 流用で済む見込みだが、多版 + SSN の certified には新しい証拠面が要る (L)。
- stock の `1 << thid_` (int) は 48 thread の計測点で未定義動作になる。SSN の reader 追跡が誤ると直列化の判定に効く可能性があり、ベースにする前に実測か修理が要る (本調査では未実測)。

### si・mvto・ss2pl・oze (参考)
- si は直列化可能性の基準では certified の対象になりえない (stock が write skew を出す)。ベースにするなら「SI → SSI」の意味の変更そのものが研究対象になる。
- mvto は YCSB が無く、ss2pl は YCSB が out-of-tree のスタディ patch だけ。oze は YCSB はあるが多版 graph。いずれも段 2 が L。

## 3. cc-readiness 要約 (`/work/1/SFC/tanab/tmp/gen-opt-2026-09-29/cc-readiness-2026-09-29.md`) との食い違い

| # | 要約の記載 | 実物で確かめた事実 | 根拠 |
|---|---|---|---|
| 1 | mocc (2)「通る」 | X/P は pin C にあり certified は出るが、stock の validation の欠陥で rr95 の stock が G2 を出す (pin C で 5/112 走)。修理は branch のみで pin 未前進 → 「部分」 | t2872-mocc-g2-split `:66,71`、mocc-validation-fix §0、D2304 |
| 2 | mocc (5)「read-heavy で stock も G2 を出す件は未決 (T-2868 / T-2872)」 | 原因は MOCC 本体の validation の隙間と確定し、修理 X (`f4a5169e`) で G2 0/112。残るのは pin 前進と D297 の扱いの裁定 | D2304、mocc-validation-fix §0・§8 |
| 3 | mocc (1)「TPC-C v3 は別枝 (izanagi-tpcc-v3-mocc)」 | 現行の候補は silo・mocc を束ねた枝 F `izanagi-tpcc-v3-silo-mocc-fmt` (`25898d00`、GitHub CI 緑)。`izanagi-tpcc-v3-mocc` は旧い途中の枝 | D2293、`docs/archive/worklog-phase3-0930-1959.md:150-156` |
| 4 | cicada (1)「YCSB v2 のみ」 | TPC-C v3 の重ね patch `instr-cicada-trace-tpcc.patch` もある (C1' 以降にのみ当たり、pin C 単独には当たらない) | D2294、`patches/README.md:16,992-1004` |
| 5 | cicada (2)「通らない」 | 一致。加えて D2305 項 4 で中間案 M を採用済み (未実装、T-2874)。M を満たしても certified とは呼ばない | D2305 項 4、D2300 |
| 6 | cicada (3)「有 (CICADA_SPACE)、VHash の診断計測」 | 空間はあるが、認定較正 0・floor は D1373 で拒否・promotion 有効の 8 genome は pin で build 不能で修理後も直列化違反で失格 → 「部分」 | genome.py:178、registered/ の実測、D2291、D2308 |
| 7 | tictoc (3)「有 (TICTOC_SPACE、較正・floor baseline)」 | baseline 表への登録はあるが、trace hook が無いので between-run floor は D1373 で拒否されて未実測。登録済みは within-run CV (D2083) のみ → 「部分」 | between_run_floor.py:72-86、D2083、D2127 |
| 8 | mvto・ss2pl「YCSB 版が無い」 | mvto は正しい。ss2pl は pin には無いが out-of-tree `ss2pl-lock-protocol-study.patch` が `ycsb_ss2pl.exe` を足す (D790) | `cc/mvto/CMakeLists.txt:3`、`patches/ss2pl-lock-protocol-study.patch` (CMake hunk) |
| 9 | si (2)「通らない (X/P なし)」 | 一致。加えて stock SI は write skew で non-serializable を出すので、X/P を足しても直列化可能性の certified は定義上出ない (「不可」) | D2252 項 4・5 |
| 10 | ermia「readers bitmap の `1 << thid_` が int (実コード未確認)」 | 実コードで確認。`cc/ermia/include/transaction.hh:123,134`、`thid_` は `uint8_t` (`:30`)。影響は未実測 | 実物 |
| 11 | oze「切替判定が常に false の TODO (未確認)」 | 実コードで確認。`should_switch_to_occ`・`should_switch_to_oze` とも `return false` (`cc/oze/include/transaction.hh:1157-1171`) | 実物 |
| 12 | 補足「t2849 harness の campaign_pin_for_protocol・backoff_genome は silo と mocc 以外を ValueError」 | 一致 (関数の実体は `p3_s4_loop.py:122-128,149-154`、harness は `_genome` 経由で呼ぶ `t2849_comparison_harness.py:38-39`)。拒否は他にも argparse (`:789`、`p3_s4_loop.py:3497`)・条件 gate (`condition_meaning_gate.py:1252`)・転移 runner (`t2851_transfer_runner.py:188,209`) | 実物 |
| 13 | 補足「pipeline の trace allowlist は ycsb_* と条件付きの tpcc_*」 | 一致。tpcc_* は段 1 の mix のときだけ許し、v3 でなければ verify 後に reject | pipeline.py:458-466,702-707 |
| 14 | silo の各段 | 一致。ただし要約は silo の取引内の値の欠陥 (DSG に映らない、修正は branch のみ) に触れていない | silo-intra-txn-fix §0 |

## 4. 親の裁定 (重さの正本)

`definition.md` §9 の点 (0 / S=1 / M=2 / L=3) で数える。段 4 は gen-opt の段 A・B に要る「関数単位の口」で数え、backoff の数値の穴だけで足りる場合の値を括弧に添える。

| CC | (1) trace | (2) certified の証拠面 | (3) 性能計測 | (4) LLM の口 | (5) 比較基盤 | 合計 | 備考 |
|---|---|---|---|---|---|---|---|
| silo | 0 | **S** (子の提案 0 から変更) | 0 | 0 | 0 | **1** | 取引内の値の修正 (`silo-intra-txn-fix`) は branch のみ。正しさ関門の設計 (`gen-opt-correctness-gate` §3.5・D2b) が gen-opt の評価開始の前提条件と書くので、MOCC の修理 X と同じく pin 前進 1 本 (S) を数える |
| mocc | 0 | S | S | M | 0 | **4** | 段 2 は修理 X (`f4a5169e`) を pin に入れるまで rr95 で stock が G2 を出す。段 4 は md_10 (並走中) の設計次第で L に上がりうる |
| cicada | S | **L** | S | L (S) | S | **9** (7) | 中間案 M (D2305 項 4) は certified ではない。certified には判定器の protocol 別の門 (案 A) が要る |
| tictoc | M | M | S | L (S) | S | **9** (7) | 単版・sort 後施錠で Silo の X/P を移せる見込み (未実証)。判定器の意味は変えない |
| ermia | M | **L** | S | L (S) | S | **10** (8) | stock の readers bitmap の int shift (48 thread で未定義動作) を先に確かめる必要 |
| si | S | **不可** | S | — | 部分 | 対象外 | stock が write skew を出す。直列化可能性の certified は定義上出ない |
| mvto | **L** (子の提案 M+M を L に丸めた) | L | S | L | S | **11** | pin に YCSB driver が無い (`cc/mvto/CMakeLists.txt:3`)。driver と trace の両方が要る |
| ss2pl | M | L | S | L | S | **10** | YCSB は repo 外の study patch (D790) だけで、pin には無い |
| oze | M | L | S | L | S | **10** | 多版の依存グラフ。OCC/Oze の切替判定は常に false (`cc/oze/include/transaction.hh:1157-1171`) |

全 CC に共通で、表の点に入れていないもの:

- **D2289 決定 4 の 2 関門** (検査用記録の差し込み点を LLM の編集範囲外に固定、仕組みごとの小モデル全場面検査) は、どの CC をベースにしても別途要る。
- **取引内の値の照合 (D2b) の前提:** `cc-profiles.md` の各 CC の 7 項が示すとおり、Silo 以外の CC も read を read set → write set の順に探す。D2b を certified の条件に入れるなら、Silo と同じ種類の修正が各 CC にも要る見込み (各 CC の実挙動は未実測)。CC ごとにほぼ同じ重さで掛かるので順番は変えないと見て、点に入れていない。
- **段 A の最初の試しは段 4 の口を必ずしも要さない。** 文献の最適化を人が名前つきの対照として書く試し (文献カード README §0) なら段 4 は 0 になる。そのときの合計は、段 4 を 0 とした値 (silo 1、mocc 2、cicada 6、tictoc 6、ermia 7、mvto 8、ss2pl 7、oze 7) になる。

