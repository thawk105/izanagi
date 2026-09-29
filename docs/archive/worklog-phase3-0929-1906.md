## 2026-09-29 (1906) — /rulings 全件 第 39 回 — 索引 5 行を裁定した。CCBench の pin を C2' 系へ進めるのは CCBench の CI (build・format) が緑の tip に限り、MOCC の read-heavy は比較に普通に使ったうえで MOCC の欠陥を直し、探索の独立反復の再提示は T-2871 → T-2867 の後に置く (docs のみ、branch worktree-rulings-all-20260928)

- **窓は entry 1898〜1905、決定は D2273〜D2276。** 前回の全件走は第 38 回 (D2272、収集 entry 1895、提示後に 1896・1897)。収集は main `19d3f2bae` (entry 1902) で始め、提示 (21:4x JST) の後に
  別 session の通知を受けて local main を自分で読み直し、`51f896352` (entry 1905) で索引を改訂して再提示した (新項 = [T-2854] の問い 2 と [T-2872])。受領文 (2026-09-28 0 時台 JST、逐語) は
  「1, 推奨通り。あなたの仕事はのちにCI落ちしたりしていた。CCBench CIが通る品質を意識してください。2, 普通に使います。そして修理もします。例えば、PostgreSQLなどでバグがあった時、過去にそれが使われたすべての研究論文の結果は意味のないものになったでしょうか？そうではない。もちろんバグは直す必要があります。他推奨通り」。
- **次の一手 104 項を carry 鎖の実体まで解決した (未解決 0)。** 機械走査は 7 件。見送り台帳の相乗りは [T-1015]・[T-436] が再成立したが D1780 で索引外。19:15 JST 以降の typed のユーザー発話は他の session に無かった。
- **索引 5 行 = ユーザー裁定待ち 3 (pin 前進・MOCC read-heavy・T-2850 の条件) + 人間手番 1 (push) + 収載維持 1。裁定済み未実装 34** (見出しが裁定済み・決定・了承で → の先に実装・手番・待ちが残る型)。
  Git は記録の時点で未 push 0 (提示時点は 62)、CCBench の `izanagi-tpcc-v3-silo-mocc` もユーザーが push 済み。
- **相談 4 本 (read-only、`--lane sol`、medium)。** 最初の 2 本は出力節の `## 総括` 指定を書き忘れて不受理 (`f43_fragment`、既知型の再発)、本文を原典で検算して使った。A は索引外の [T-2850] の判定に反対 (D2274 項 4 が新事実) → 採用して索引へ新設。
  追加の C は新 2 項に同意し修正 4 点 (較正の時期・GitHub 取得の確認・断定しない・追加報告の扱い) → 採用。B・D は漏れ 0。
- **裁定は D2277 (5 項)。** 項 1 = C2' 系への pin 前進を承認、ただし CCBench の CI (build・format) が緑の tip に限る、項 2 = MOCC の read-heavy は普通に使い MOCC の欠陥は直す (推奨 (a) は不採用)、
  項 3 = [T-2850] の再提示条件は維持し [T-2871] → [T-2867] → 再提示、項 4 = push 済み、項 5 = 収載維持。
- **CCBench の CI の実測:** GitHub の Actions で izanagi の branch (e9e477ca・C `681066606`・a6f2c7410) は build success・format failure。手元の clang-format 14 で C2' の変える 4 file の違反は C で 26・17・3・0、C2' で 36・23・25・0。失敗台帳 F1056。
- 索引・起草推奨・相談の出力は `/work/1/SFC/tanab/dev-wave-jobs/rulings-all-20260927c/` (`materials-index.md` / `materials-addendum.md` / `final-index-note.md` / `artifacts/`)。整形の測定 script は `/work/SFC/tanab/tmp/rulings39-20260928/fmt_check.py`。
  裁定の控えは repo 外 `rulings-inbox/2026-09-28-rulings-full39-verdicts.md`。
- **事故 (near miss):** 記録用の worktree を `EnterWorktree` で作るとき session の cwd が `external/ccbench` のままで、CCBench の中に worktree を作った。未変更のまま `git worktree remove` と branch 削除で撤去し、izanagi 側で作り直した。
  空 dir `external/ccbench/.claude/worktrees` は guard が rmdir を拒否したので残した (git の追跡外)。
- **実装面の差分は 0 である。** 変更は台帳 fragment だけ。
- 工数: codex 子 4 本 (consult)。計算ノード job は受入のみ。

### 次の一手 — 「(番号)」だけの項は、その番号のエントリ (archive 含む) から変わらない持ち越し

- [T-139] (1905)
- [T-265] (1905)
- [T-129] (1905)
- [T-238] (1905)
- [T-570] (1905)
- [T-580] (1905)
- [T-793] (1905)
- [T-823] (1905)
- [T-841] (1905)
- [T-1069] (1905)
- [T-1071] (1905)
- [T-1234] (1905)
- [T-1295] (1905)
- [T-1524] (1905)
- [T-1660] (1905)
- [T-1702] (1905)
- [T-1703] (1905)
- [T-1708] (1905)
- [T-1784] (1905)
- [T-1794] (1905)
- [T-1832] (1905)
- [T-1834] (1905)
- [T-1882] (1905)
- [T-1883] (1905)
- [T-1944] (1905)
- [T-1950] (1905)
- [T-2000] (1905)
- [T-2005] (1905)
- [T-2052] (1905)
- [T-2084] (1905)
- [T-2092] (1905)
- [T-2100] (1905)
- [T-2172] (1905)
- [T-2205] (1905)
- [T-2218] (1905)
- [T-2221] (1905)
- [T-2222] (1905)
- [T-2244] (1905)
- [T-2245] (1905)
- [T-2250] (1905)
- [T-2273] (1905)
- [T-2277] (1905)
- [T-2288] (1905)
- [T-2300] (1905)
- [T-2318] (1905)
- [T-2322] (1905)
- [T-2323] (1905)
- [T-2351] (1905)
- [T-2378] (1905)
- [T-2387] (1905)
- [T-2404] (1905)
- [T-2415] (1905)
- [T-2422] (1905)
- [T-2425] (1905)
- [T-2451] (1905)
- [T-2453] (1905)
- [T-2459] (1905)
- [T-2461] (1905)
- [T-2463] (1905)
- [T-2511] (1905)
- [T-2522] (1905)
- [T-2538] (1905)
- [T-2541] (1905)
- [T-2559] (1905)
- [T-2560] (1905)
- [T-2561] (1905)
- [T-2575] (1905)
- [T-2604] (1905)
- [T-2606] (1905)
- [T-2648] (1905)
- [T-2685] (1905)
- [T-2699] (1905)
- [T-2725] (1905)
- [T-2739] (1905)
- [T-2740] (1905)
- [T-2741] (1905)
- [T-2754] (1905)
- [T-2755] (1905)
- [T-2759] (1905)
- [T-2767] (1905)
- [T-2787] (1905)
- [T-2806] (1905)
- [T-2808] (1905)
- [T-2818] (1905)
- [T-2820] (1905)
- [T-2827] (1905)
- [T-2829] (1905)
- [T-2838] (1905)
- [T-2840] (1905)
- [T-2846] (1905)
- [T-2848] (1905)
- [T-2850] **P1 (VLDB 差分分析 P3: 探索の独立反復の費用・成果の曲線) — 本比較は今は投入しない (D2272 項 2)。[T-2869] の扱いは決まった (D2273: 本比較には適用しない)。[T-2867] の見積りが揃った時点で AI が並べて順番と規模を再提示。条件は維持し、順は [T-2871] → [T-2867] の実装と生死確認 → 再提示 (D2277 項 3)**: 事前登録 v1 (D2231)・追補 1〜3。試走 v2 (cohort `t2850-trial-v2`、18 job) は
  2026-09-27 03:40 JST に終わり、job Elapse 計 28.70 node 時間、15 系列すべて score あり (追補 3 §1)。追補 3 に §8 の入力と本比較の固定値
  (cohort `t2850-main-v1`、系列番号 100 + b、固定 commit `299aa022e`、trace 保全の opt-in、LLM 親は同時 4 本以下) を登録し、課題の集合を S1-wh に決めた (D2265)。残りは 3 つ。
  (1) **本比較は今は投入しない (D2272 項 2、ユーザー裁定)。C_max は決めていない。** 空間が B-5 と同じ S1 で n = 10 の分類が弱いこと・[T-2869] の不公平が未補正なこと・LLM の待ちが node 上に残ることによる。再提示のときの材料として、事前登録の提案 C_max は 510 で、C(10) ≤ C_max < C(60) (丸めずに比べる、概数 110.544・663.263 node 時間) なら系列数 10 (第 2 段、C(10) = 110.5 node 時間、幅 93〜124、A = 30 の使い切りで最大 +43、
  LLM の直列時間 26.7 時間、暦の理想下限 6.7 時間・見込み 10〜15 時間)。確認後に発効の決定 (C_max・課題・系列数・保全先の実 path・追補 3 の raw SHA-256) を書き、
  repo 外の glue v4 (`dev-wave-jobs/dev-wave-t2850-trial-v2-followup/glue-v4/`) で投入する。LLM 系列は 4 本ずつ段階投入する。
  D2219 項 6 の再提示条件 (LLM の直列時間が律速) は文言どおり成立し、H100 の open-weight LLM 案は再提示のうえ今回も採らなかった (D2272 項 3、条件は残る)。
  (2) MOCC (S2)・policy IR (S3) は、その空間の最初の生成より前の追補で足す。read-heavy・balanced を本比較に入れるなら検査の同時化と静定の上限を別の追補で決める (追補 2 §7)。
  (3) **[T-2869] の扱い (D2273)**: 修正 (planner prompt に axis の固定値を明示) は main に入ったが、本比較は固定 commit `299aa022e` の現行 prompt のまま行う (本登録 §3.1 の具体的な食い違いを確定できない)。
  再提示には択一を並べる: A (推奨) = そのまま本比較、再試走なし、報告で A 消費・axis 不一致の内訳を開示 / B = 修正を適用、生成前に事後改訂の追補を置き LLM 系列を試走し直す (試走 v2 の LLM 3 job の実績 12.41 node 時間 + LLM 直列時間)。
  表は `output/insights/2026-09-27/t2869-planner-axis-name/README.md` §5。S2・S3 の追補で K0 系列を登録するときは修正後の commit を使える (その時点の prompt を発効束に書く)。
  **生成・選択には [T-2851] の留保条件を使わない**。材料 `output/insights/2026-09-27/t2850-trial-v2-analysis/README.md`。
  (4) **再提示の条件は維持 (D2277 項 3、ユーザー裁定)。** D2274 項 4 で方策軸の系列は job をまたぐ 2 本目の pair が claim で止まると分かったので、[T-2867] の見積りは [T-2871] の修復 → [T-2867] の実装と生死確認 (C++ 形・IR 形・機械生成 IR) の後に揃う。揃った時点で AI が並べて再提示する。[T-2851] の YCSB 側の発効もこれに従って待つ。
- [T-2851] (1905)
- [T-2852] (1905)
- [T-2853] (1905)
- [T-2854] **P1・段 1 の一部完了 (D2212 項 2、D2219 項 2) 、単位 11 の材料は済 → 規則 v2 を D297 検査器に実装し C → C2' は GCC 11.4 / 12.3 とも pass (D2275) → C2' 系への pin 前進は承認 (D2277 項 1、CCBench の CI (build・format) が緑の tip に限る) → 残り = pin 前進 wave (AI、整形 commit・CI・D297 の取り直し・同時更新)・新 tip の人間の push・TPC-C の探索 loop への配線 (評価単位までの配線は済、D2276)**: TPC-C 段 1 (NewOrder / Payment、CCBench 既定比 45% + 43%、
  点読み・点書き・insert のみで `tx.scan` を使わない) の合成候補を直列化可能性で認定できるようにする。設計 = `output/insights/2026-09-21/tpcc-trace-certification-design/README.md`
  (§7.1 の実装単位、§8 の親決定)。実装は Codex author、正しさゲートは不変、trace は compile 時に除去する (規律 1)。
  **済:** 単位 1・2 (CCBench 側、D2225、`output/insights/2026-09-22/t2854-tpcc-ccbench-v3/README.md`) = CCBench の local branch
  `izanagi-tpcc-v3-trace` に pin e9e477ca の子として C1 `56b5cb709628c9cac98e4e18ff676defc77a9117` (trace.hh の v3 helper・tpcc.hh の取引種別 context と
  trace build 限定の計数) と C2 `a6f2c7410d58ad140a62b11cc1beab29bfcd191b` (silo の v3 emitter)。計算ノード 1 走で v3 の構造・witness・内容、YCSB v2 の certified、
  TRACE=0 の前処理と逆アセンブルの一致、変異 6 件を確認。この branch は 2026-09-23 08:4x JST に人間が GitHub へ push した (D2227 項 7 の「今は push しない」と食い違い、F937 の再発)。
  公開済みのまま残し、pin 候補ではない (D2235 項 1、C1 / C2 は job dir の自己完結 bundle にも保全済み)。単位 11 で C の上へ乗せ直し、
  header 差分の受理方法と結合確認を揃えた候補は別名の branch で人間の push 判断へ渡す (D16、同名への force push はしない)。単位 4 (verifier 側、D2224、entry 1828、
  `output/insights/2026-09-22/t2854-tpcc-verifier-v3/README.md`) = v3 を (表, key) で読み cycle に表と取引種別を載せる。単位 3 (mocc 側、D2230、`output/insights/2026-09-23/t2854-mocc-v3-emitter/README.md`) =
  CCBench の local branch `izanagi-tpcc-v3-mocc` に [T-2844] の候補 C `68106660686232781bca3be792a750d3e19d7a8a` の子として C1' `6aa7a58fccff9efa218067d1b7ce83026a75357d`
  (C1 の cherry-pick、header の blob は C1 と同一) と C3 `53f6b09757331ac7200f3f6bb5d526a676480fe3` (mocc の v3 emitter)。計算ノード 1 走で C を基点に同じ形の確認
  (v3 の構造・witness・内容、YCSB v2 の certified、TRACE=0 の前処理と逆アセンブルの一致、変異 6 件) を満たした。この branch も今は push しない
  (bundle で保全、単位 11 の候補の材料)。存在履歴 (entry 1843、D2232、`output/insights/2026-09-23/t2854-v3-existence/README.md`) =
  設計 §3.3 を silo の版付けに裏付けた段 1 の契約で検査し、単位 4 が立てた印 `Integrity.v3_existence_unverified` を撤去。単位 1・2 の実 trace (silo) は公開 API で certified、
  単位 3 の実 trace (mocc) も存在違反 0 (mocc の認定は X/P 証拠面が pin に入った後)。mocc でも存在の契約 (初期ロードの版が (1,0)、insert は既存 key で失敗) が
  静的に成り立つことは単位 3 の insight §6。単位 5 (entry 1852、D2238、`output/insights/2026-09-23/t2854-unit5-v3-wiring/README.md`) =
  CLI の `--json`・pipeline の reject 診断・受領証 digest を `core.result_to_dict_v3` に配線 (v2 は bytes・digest 不変)、pipeline の `_run_trace` は `tpcc_` で 57:43 の 4 flag が
  文字列で一致するときだけ受理し、verifier 後に v3 を要求 (v2 は既存 `trace-witness-unsupported-workload` で reject)。§6.1 の段 1 例は既存試験への対応づけと合成 v3 の
  lost update・直列対照・executor の witness 欠落 3 形態で揃えた (「genesis の誤用」は存在検査の `read-unborn-genesis`)。実 trace (silo) は pipeline の executor で certified。
  **単位 11 (本 entry、D2244、`output/insights/2026-09-26/t2854-unit11-combined/README.md`):** 新しい local branch `izanagi-tpcc-v3-silo-mocc` =
  C `68106660` → C1' → C3 → C2' `40a7f4acb174ca43cb590f40d13847216a1564bc` (C2 の cherry-pick、新規 commit はこれだけ、未 push、job dir の自己完結 bundle に保全)。計算ノード 1 走 (Elapse 243 秒) で C を基点に、
  TPC-C の silo・mocc とも v3 の構造・witness・内容、YCSB の silo・mocc とも v2 の certified、TRACE=0 の 21 entry の前処理と 4 binary の逆アセンブルの一致、
  変異 4 件 (共有 header の setter、共有 header の `#line`、silo の表、mocc の種別) の KILLED を確認。現行の D297 検査器は C → C2' を `include/tpcc.hh` の header 差分で拒否する (rc=1)。
  D297 の合格・TPC-C の certified は名乗らない。
  **残り:** (1) C 単独の pin 前進は [T-2858] で承認・実施済み (D2227 項 1) で、C1' / C2' / C3 は C の上の別候補として改めて承認を求める。**D297 の header 差分の受理規則は設計審査を終えた (D2249 項 2 の択 1、D2255、`output/insights/2026-09-26/t2854-d297-header-review/README.md`):** 規則 v2 = header の M 差分に限り、実 compile database の全 entry から `-MG` なしの依存列挙 (旧・新 × TRACE=0/1) で変更 header の consumer を選び、選定 configure 集合 (stock と、consumer を含む production target の protocol の genome 空間。C → C2' では stock + silo 8 + mocc 8 = 17) の各 configure で全 consumer entry の TRACE=0 完全展開と include 活性を GCC 11.4 / 12.3 の別 configure で旧新比較する (実行は計算ノード)。**規則 v2 の承認と実装の委任は D2260 項 1 で決まった (ユーザー裁定、推奨どおり)。** **実装済み (D2275、`output/insights/2026-09-27/t2854-d297-header-v2/README.md`):** header 用の 4 引数 (`--header-cc` `--third-party-cache` `--dependency-prefix` `--scratch-root`) を全部与えたときだけ header の M 差分を規則 v2 で検査し、与えなければ従来どおり拒否する。改訂後の検査器で C → C2' は計算ノード 1 job (31903.nqsv、Elapse 1,944 秒) で **GCC 11.4・12.3 とも pass** (選定 17 configure、tictoc・cicada 各 24 genome は consumer なし、consumer 21 entry、予定 = 実行 357、.cc 2 本も match、gitlink `third_party/shirakami` は旧新一致)。負例対照 (tpcc.hh の `#line 56` 削除) は TPC-C consumer の完全展開不一致で拒否。変異 12 件 KILLED。wave の計算は受入を除き約 0.80 node 時間。**問い 2 は承認された (D2277 項 1、ユーザー裁定「推奨通り。…CCBench CIが通る品質を意識してください」)。** 進める先は CCBench の CI (`.github/workflows/build.yml` の Release 全 protocol build と `format.yml` の clang-format 14 `--dry-run --Werror`) が緑の tip に限る。GitHub の Actions では izanagi の branch (e9e477ca・C `681066606`・a6f2c7410) は build success・format failure で、手元の clang-format 14 で C2' の変える 4 file の違反は C で 26・17・3・0、C2' で 36・23・25・0 ({F})。pin 前進 wave (AI、CCBench 側は Codex author) の順: (1) C2' の上に整形だけの commit を乗せ build と format を CI と同じ手順で通す、(2) 新 tip で D297 規則 v2 の判定を C 基点で取り直す (D2275 の pass は `40a7f4ac` に限る)、(3) 人間が新 tip を別名 branch で push し、GitHub の CI 緑と当 commit の取得を確かめてから gitlink・`CCBENCH_FULL_SHA`・`CURRENT_PIN` を同時更新、(4) patch 54 本の厳密適用を最初に測り、較正は新 pin を使う系列の着手時に取る。si の trace v2 は branch へ移さず patch のまま (D2277 項 1、D2260 項 4 への答え)。C2' の branch `izanagi-tpcc-v3-silo-mocc` はユーザーが push 済み (`40a7f4acb`)。以下は承認前の記録: この結果・実費・pin 波及 (同 insight §7: code 5 file・test 14 file・`patches/README.md`、C2' の変える 4 file に当たる patch 54 本は C2' での適用可否が未測定、C を束縛する較正記録は D2184 どおり保持) を示して、C2' `40a7f4ac` の pin 前進を承認するか (条件つき事前承認は推さない)。承認後の pin 前進 wave は patch 54 本の厳密適用を最初に測る。この問い 2 の機会に、si の trace v2 (`patches/instr-si-trace-v2.patch`、[T-2847]、D2252) を `izanagi-trace` 枝へ移して pin を進めるかも併せて諮る (D2260 項 4)。それまで pin は C。C2' の D297 pass は改訂後の検査器の結果 (上記) に限って言い、単位 11 の証拠を遡って pass と呼ばない。TPC-C の certified は名乗らない。D780 項 2 は維持し、その比較を trace 完全除去の防壁と呼ばない。択 2 (C2' 限定の例外)・択 3 (header を変えない作り直し)・択 4 (何もしない) は採らない。段 2 も header を変えるので、規則 v2 は段 2 の pin 前進にも適用できる (合格するかは段 2 の実差分で確かめる)。**人間の手番:** 整形後の新 tip を別名 branch で push すること (force 不要)。pin 前進の承認は済んだ (D2277 項 1、同時更新は AI の wave、先例 D2150 / D2184)。
  v3 emitter が pin に入るまで、現 pin の tpcc binary は v2 を出し単位 5 の v3 要求で reject される。
  (2) campaign で TPC-C の候補を評価する配線は評価単位まで済 (D2276、`output/insights/2026-09-27/t2866-tpcc-campaign-wiring/README.md`): buildcache と `pipeline.evaluate` が workload (ycsb / tpcc) を受け、
  `tpcc_<protocol>.exe` を build し `-tpcc_num_wh` で bench へ渡す。critic の説明文も TPC-C の v2 reject に合わせた。計算ノードの錨 s1-H-base で build・evaluate・bench が走り、現 pin の v2 trace は既存 reason で abort (bench 未起動)。
  残りは TPC-C の探索 loop への配線 (`loop.run_campaign` の workload・verify mode、TPC-C の calibration、`calibrator/cli.py` の ycsb target 固定) で、TPC-C の探索設計と一緒に行う。
  D297 検査器の規則 v2 は production target を `buildcache._v2_commands` の `--target` から導き `ycsb_<protocol>.exe` の形だけを受理する (D2275) ので、TPC-C を production target に入れる段ではこの選定も広げる。
  現 pin の perf binary は取引別の commit / abort 件数を出さない (同 insight §3.1)。
  単位 1・2 の実 trace は `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2854-tpcc-ccbench-v3/evidence/traces-2/`、単位 3 の実 trace は
  `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2854-mocc-v3-emitter/evidence/traces-1/`、単位 11 (C2' の silo・mocc) は
  `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2854-unit11-combined/evidence/traces-1/` に zstd で保持。
  段 2 へは段 1 の存在契約をそのまま広げない (削除後の再挿入で版順が存在の遷移と逆になりうる、範囲読みの不在は §4.3 の初期キー一覧、entry 1843 の insight §8)。
  見送り台帳 [T-156] (selector-8b descriptor への set-size 条件) の発火条件は単位 5 で再評価した (pipeline は受理するが corpus の実体は無いので着手しない、単位 5 の insight §8)。
  設計 insight §9 の CCBench 所見 (D2219 項 7): 段 1 で観測できたのは実行時の OrderLine 番号が 0 始まりであることだけ。寿命と範囲読みの所見は [T-2855]、
  si の所見は si を走らせる wave の担当。計算: 検証走・計測・開発の検査を含め 1 タスクの job 合計が 2 node 時間以上になる投入は、見積りを示してユーザー確認後に
  投入する (D2212 項 4、D2219 項 1)。一次資料 `output/insights/2026-09-21/vldb-direction/gap-analysis.md` §10、roadmap §3.1。
- [T-2855] (1905)
- [T-2859] (1905)
- [T-2864] (1905)
- [T-2865] (1905)
- [T-2867] (1905)
- [T-2870] (1905)
- [T-2871] (1905)
- [T-2872] **P1・裁定済み (D2277 項 2: read-heavy は比較に普通に使い、MOCC の欠陥は直す) → 欠陥の切り分けと修理 (AI、CCBench 側は Codex author・CCBench の CI を通す)**: MOCC の read-heavy (48 thread・1,000,000 record・rr95、pin C) では、stock 自体が性能構成の検査に落ちる反復がある ([T-2868] insight §3、観測 3/109 = 2.8%、95% 区間 0.6〜7.8%)。t2849 の read-heavy の stock 比・終点選択・certified 終点はこの実装の上の値である。
  - 裁定 (D2277 項 2、ユーザー): 択 (a)(b)(c) のどれでもなく「普通に使います。そして修理もします」。t2849 の read-heavy の値は pin C の MOCC の上の測定として有効に扱い (規律 7)、論文ではこの cell の stock に同じ形の G2 (3/109) が出たことを事実として書く。D2261 項 6 の「決まるまで論文の主張に使わない」は read-heavy の比較の使用について置き換わった。規律 2 は不変 (anomaly を検出した候補は即 reject)。原因は未分離なので「MOCC は非直列化可能」と断定しない。
  - 残り (AI): (iii) 本体と (iv) hook の切り分け (観測者効果の小さい計器、既往 T-2774 §7・T-2779 §3)、本体の欠陥なら CCBench の MOCC を直す (Codex author、CCBench の CI の build・format を通す)。上流への push・PR・追加報告は人間の判断 (D16・D18・D20)。修理後の版で測り直すかは修理が pin に入る時点で示す。

