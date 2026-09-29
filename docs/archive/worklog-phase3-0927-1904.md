## 2026-09-27 (1904) — [T-2866] [T-2854] TPC-C の候補を campaign の評価単位 (buildcache・pipeline.evaluate・測定関数) で build・評価できるようにし、転移実行器の TPC-C 段 1 検証を D2238 の経路へ接続した。計算ノードの錨 s1-H-base で build・1 job・検証・bench・evaluate・単独性が期待どおり走り、現 pin の v2 trace は既存 reason で未確定 / abort と記録された (コード + test + insight、branch worktree-dev-wave-t2866-tpcc-campaign)

- 設計判断は D2276、記録は `output/insights/2026-09-27/t2866-tpcc-campaign-wiring/README.md`。段 1〜6 の逐語は同 dir の `verbatim/`、計算ノードの記録は `evidence/`。
- 親 brief の誤り 2 点を段 3 の相談 2 本が独立に反証した (実行器の `cell.flags` は int ではなく `_cell` が str 化済み、認定 gate は X/P の二面)。文字列化の差分は作らなかった。
- 焦点走 1 回目の赤 12 件は本 wave に帰属: 新 test が見つけた実欠陥 1 件 (`_prepare_evaluation_core` の反復変数が引数 `workload` を上書きし、v3 通過後の TPC-C bench が落ちる) と、`_PreparedEvaluation` を直接作る既存 fixture の取り残し 11 件。fix 1 巡で閉じ、焦点走 2 回目 2,765 passed・5 skipped。
- 変異 matrix (独立 clone、dispatch、HEAD `724088a08`): 事前登録の M1〜M14 が 14 件とも KILLED (期待 node と完全一致)、等価変異 M15 は SURVIVED (同 insight §2)。
- 受入 attempt 1 の赤 1 件 (`test_layer3_report.py::test_run_bench_ast_assignments_exactly_match_declared_payload_keys`、bench payload の条件付き key 数の pin) は本 wave に帰属。
  焦点走の consumer 集合に private symbol の consumer を入れ損ねた親の漏れで、bench・commit payload への `workload` 追加を取り下げて閉じた (同 insight §1)。
  fix 後の焦点走 3 回目 (consumer 44 file、HEAD `d8d337e7b`) は 5,716 passed・20 skipped、変異 final の再走も 14 KILLED・M15 SURVIVED。
- 段 6 review の不採用: RB3 (不正 workload の拒否 test の重複削減) は受理集合・成果物に影響しないので見送り。
- 実装子・fix 子の codex は sandbox が qstat を拒否するため pytest を実走できず、test は親の焦点走だけで確かめた。
- 計算ノードの生死確認は使い捨て driver (repo 外、Codex author) で 3 回: 1 回目 (31859.nqsv、32 秒) は build の toolchain manifest 不一致、2 回目 (31867.nqsv、38 秒) は FetchContent の実効 source root 不一致で、どちらも driver が production の job body と違う形で引数を渡していたため。
  3 回目 (31897.nqsv、374 秒、bnode018) で全照合が一致。job Elapse 合計 444 秒で D2212 項 4 の確認ライン未満。
- 範囲外の所見 (記録のみ): 現 pin の perf binary は取引別の commit / abort 件数を出さない。倉庫 1・48 thread で `insert order failed` が多数出る (同 insight §3.1)。

- [T-2866] 転移の実行器の TPC-C 検証を段 1 の認定経路へ接続した (D2276 項 4): 段 s1 の 57:43 cell は `pipeline._run_trace` → witness → 実 verifier (凍結した source root) → v3 要求を通り、
  v2 は未確定 (reason `trace-witness-unsupported-workload`、anomaly・非直列化は失格が優先)、s2 と s1 の非 57:43 は「認定経路なし」のまま。TPC-C の build 経路 (buildcache の workload) と TPC-C 用の単独性確認は
  計算ノードの錨 s1-H-base で実機確認した (単独性は TPC-C 実行中に既知 PID が見えて拒否、終了後に受理、composite probe も passed)。留保 cell は 0 走。発効時に固定する認定経路の値 (verifier の版・emitter と pin) は
  [T-2851] 残り (1) の発効束で記録する。記録 `output/insights/2026-09-27/t2866-tpcc-campaign-wiring/README.md` §3。

### 次の一手 — 「(番号)」だけの項は、その番号のエントリ (archive 含む) から変わらない持ち越し

- [T-139] (1903)
- [T-265] (1903)
- [T-129] (1903)
- [T-238] (1903)
- [T-570] (1903)
- [T-580] (1903)
- [T-793] (1903)
- [T-823] (1903)
- [T-841] (1903)
- [T-1069] (1903)
- [T-1071] (1903)
- [T-1234] (1903)
- [T-1295] (1903)
- [T-1524] (1903)
- [T-1660] (1903)
- [T-1702] (1903)
- [T-1703] (1903)
- [T-1708] (1903)
- [T-1784] (1903)
- [T-1794] (1903)
- [T-1832] (1903)
- [T-1834] (1903)
- [T-1882] (1903)
- [T-1883] (1903)
- [T-1944] (1903)
- [T-1950] (1903)
- [T-2000] (1903)
- [T-2005] (1903)
- [T-2052] (1903)
- [T-2084] (1903)
- [T-2092] (1903)
- [T-2100] (1903)
- [T-2172] (1903)
- [T-2205] (1903)
- [T-2218] (1903)
- [T-2221] (1903)
- [T-2222] (1903)
- [T-2244] (1903)
- [T-2245] (1903)
- [T-2250] (1903)
- [T-2273] (1903)
- [T-2277] (1903)
- [T-2288] (1903)
- [T-2300] (1903)
- [T-2318] (1903)
- [T-2322] (1903)
- [T-2323] (1903)
- [T-2351] (1903)
- [T-2378] (1903)
- [T-2387] (1903)
- [T-2404] (1903)
- [T-2415] (1903)
- [T-2422] (1903)
- [T-2425] (1903)
- [T-2451] (1903)
- [T-2453] (1903)
- [T-2459] (1903)
- [T-2461] (1903)
- [T-2463] (1903)
- [T-2511] (1903)
- [T-2522] (1903)
- [T-2538] (1903)
- [T-2541] (1903)
- [T-2559] (1903)
- [T-2560] (1903)
- [T-2561] (1903)
- [T-2575] (1903)
- [T-2604] (1903)
- [T-2606] (1903)
- [T-2648] (1903)
- [T-2685] (1903)
- [T-2699] (1903)
- [T-2725] (1903)
- [T-2739] (1903)
- [T-2740] (1903)
- [T-2741] (1903)
- [T-2754] (1903)
- [T-2755] (1903)
- [T-2759] (1903)
- [T-2767] (1903)
- [T-2787] (1903)
- [T-2806] (1903)
- [T-2808] (1903)
- [T-2818] (1903)
- [T-2820] (1903)
- [T-2827] (1903)
- [T-2829] (1903)
- [T-2838] (1903)
- [T-2840] (1903)
- [T-2846] (1903)
- [T-2848] (1903)
- [T-2850] (1903)
- [T-2851] (1903)
- [T-2852] (1903)
- [T-2853] (1903)
- [T-2854] **P1・段 1 の一部完了 (D2212 項 2、D2219 項 2) 、単位 11 の材料は済 → 規則 v2 を D297 検査器に実装し C → C2' は GCC 11.4 / 12.3 とも pass (D2275) → 残り = C2' pin 前進の承認 (ユーザー裁定、問い 2)・承認後の pin 前進 wave (AI)・人間の push・TPC-C の探索 loop への配線 (評価単位までの配線は済、D2276)**: TPC-C 段 1 (NewOrder / Payment、CCBench 既定比 45% + 43%、
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
  **残り:** (1) C 単独の pin 前進は [T-2858] で承認・実施済み (D2227 項 1) で、C1' / C2' / C3 は C の上の別候補として改めて承認を求める。**D297 の header 差分の受理規則は設計審査を終えた (D2249 項 2 の択 1、D2255、`output/insights/2026-09-26/t2854-d297-header-review/README.md`):** 規則 v2 = header の M 差分に限り、実 compile database の全 entry から `-MG` なしの依存列挙 (旧・新 × TRACE=0/1) で変更 header の consumer を選び、選定 configure 集合 (stock と、consumer を含む production target の protocol の genome 空間。C → C2' では stock + silo 8 + mocc 8 = 17) の各 configure で全 consumer entry の TRACE=0 完全展開と include 活性を GCC 11.4 / 12.3 の別 configure で旧新比較する (実行は計算ノード)。**規則 v2 の承認と実装の委任は D2260 項 1 で決まった (ユーザー裁定、推奨どおり)。** **実装済み (D2275、`output/insights/2026-09-27/t2854-d297-header-v2/README.md`):** header 用の 4 引数 (`--header-cc` `--third-party-cache` `--dependency-prefix` `--scratch-root`) を全部与えたときだけ header の M 差分を規則 v2 で検査し、与えなければ従来どおり拒否する。改訂後の検査器で C → C2' は計算ノード 1 job (31903.nqsv、Elapse 1,944 秒) で **GCC 11.4・12.3 とも pass** (選定 17 configure、tictoc・cicada 各 24 genome は consumer なし、consumer 21 entry、予定 = 実行 357、.cc 2 本も match、gitlink `third_party/shirakami` は旧新一致)。負例対照 (tpcc.hh の `#line 56` 削除) は TPC-C consumer の完全展開不一致で拒否。変異 12 件 KILLED。wave の計算は受入を除き約 0.80 node 時間。**問い 2 (ユーザー裁定、今):** この結果・実費・pin 波及 (同 insight §7: code 5 file・test 14 file・`patches/README.md`、C2' の変える 4 file に当たる patch 54 本は C2' での適用可否が未測定、C を束縛する較正記録は D2184 どおり保持) を示して、C2' `40a7f4ac` の pin 前進を承認するか (条件つき事前承認は推さない)。承認後の pin 前進 wave は patch 54 本の厳密適用を最初に測る。この問い 2 の機会に、si の trace v2 (`patches/instr-si-trace-v2.patch`、[T-2847]、D2252) を `izanagi-trace` 枝へ移して pin を進めるかも併せて諮る (D2260 項 4)。それまで pin は C。C2' の D297 pass は改訂後の検査器の結果 (上記) に限って言い、単位 11 の証拠を遡って pass と呼ばない。TPC-C の certified は名乗らない。D780 項 2 は維持し、その比較を trace 完全除去の防壁と呼ばない。択 2 (C2' 限定の例外)・択 3 (header を変えない作り直し)・択 4 (何もしない) は採らない。段 2 も header を変えるので、規則 v2 は段 2 の pin 前進にも適用できる (合格するかは段 2 の実差分で確かめる)。**人間の手番:** branch `izanagi-tpcc-v3-silo-mocc` の push
  (別名なので force 不要、任意の時点で可) と、審査後の裁定を経た pin 前進の承認 (承認後の gitlink・`CCBENCH_FULL_SHA`・`CURRENT_PIN` の同時更新は AI の wave、先例 D2150 / D2184)。
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
- [T-2855] (1903)
- [T-2859] (1903)
- [T-2864] (1903)
- [T-2865] (1903)
- [T-2867] (1903)
- [T-2868] (1903)
- [T-2870] (1903)
- [T-2871] (1903)

