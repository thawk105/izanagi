# Izanagi 作業ログ (worklog)

セッションごとの進捗を時系列で記録する。git 履歴や各正本に入らない協議・異常・持ち越しを束ねる
「作業の索引」であり、commit 内容の再説明はしない。役割分担:

- 設計判断と却下案 → `docs/decisions.md`
- CCBench の構造的事実 → `docs/ccbench-anatomy.md`
- CCBench のバグ等の知見 → `output/insights/`
- タスク分解 → `docs/phaseN.md`
- **このファイル = それらを束ねる日誌 (各セッションの索引)**

## 新規エントリの書式 (D35)

過去エントリは凍結し、次の規約は新規エントリに適用する。

**新規エントリはこのファイルへ直接書かない。** `docs/spool/worklog/` へ fragment として書き、
land が lock 内で fold して本ファイルへ追記する (fragment 文法と fold producer 契約の正本は
`docs/spool/README.md`、**描画済み worklog の読み方と carry 書式の正本は本節**)。
エントリ番号・日付・carry 行 `- [T-NNN] (N)` の N・ローテーションはすべて fold が付ける。
以下の書式規約は、fold が生成する結果と、fragment に書く本文の両方に適用される。

- 本文化するのは、ユーザー承認・協議の決着、棄却 finding (refuted)、未コミット事象・セッション異常と
  救出、エージェント工数、人間判断待ち・持ち越し、次の一手など **git に入り得ない情報だけ**
- commit は「hash + 件名 (+ 位置づけ 1 行)」まで。連続群は「先頭..末尾 (N 本)」で表し、内容を再掲しない
- 監査の finding 全文と裁定は insight / audit JSON に凍結する。worklog はレンズ数、real/refuted 数、
  最重要 1〜3 件、一次資料ポインタの 10〜15 行に留める
- 論文素材になる段落は行頭に「素材:」を付ける。持ち越しは逐語再掲せず carry 行 `- [T-NNN] (N)`
  とする。N は**行内に明示された参照先エントリ番号**であり、実体本文は N を遡って読む。
  fold は、最初の fragment では現行 worklog の末尾エントリ番号を、同一 fold 内の後続 fragment では
  直前に生成したエントリ番号を入れる。**新エントリ番号 - 1 や全履歴の最大値から導出してはならない**
  (エントリ番号には欠番も非単調も起こりうる)。過去エントリの `- [T-NNN] 変わらず ((N) 参照)` は
  凍結した旧書式であり、fold は引き続き解決する
- docs(worklog) だけの commit は prose の body を付けず、件名 + 必須 trailer だけにする

### 次の一手の ID 規約 (D70)

「次の一手」の項目が黙って落ちる経路を塞ぐため、各項目に安定 ID を付け、`tools/check_docs.py` が
保存則を機械検査する。ID は角括弧で囲んだ `T-` + 連番で、**表記は 1 つに正規化する** —
1〜999 は 3 桁ゼロ埋め、1000 以上は先頭ゼロなしで書く。冗長なゼロ埋め (4 桁で 1 を表す等) は
同じ数値の二表記になるため**不正形式として赤にする**。

- **位置**: トップレベル list item (インデント無しの `1. ` または `- `) の**先頭**に置く。
  インデントされた子項目は原子として扱わない — **1 原子 = 1 トップレベル項目 = 1 ID** に平坦化する
  (子項目 `(a)(b)(c)` に原子を詰めると、その分は機械検査の網から外れる)
- **採番**: 現行 worklog (「ローテーション」節より後) + `docs/archive/worklog-*.md` + 見送り台帳に
  現存する有効 ID の最大値 + 1。並行セッションは番号を予約したとみなさず、統合直前に再走査して
  未統合側を振り直す (`landed` = main へ統合された時点)
- **不変性**: 一度 land した ID は変更・再利用しない
- **保存則 (機械検査)**: あるエントリの「次の一手」に現れた ID は、後続エントリのトップレベル項目
  (消化または継続) か、見送り台帳のトップレベル項目 (理由付き見送り) に現れなければ赤になる。
  ローテーション境界 (アーカイブ最新の末尾エントリ → 現行の先頭エントリ) も検査対象
- **この節と決定記録には有効 ID を書かない** (採番母集団と sink の自己汚染を避けるため、
  例示は `T-NNN` のようなプレースホルダで書く)

## ローテーション

Phase 境界または現行ファイルの肥大時 (`tools/check_docs.py` の閾値超過が
知らせる) に、過去分を `docs/archive/worklog-<範囲>.md` へ**移動**し、現行ファイルを軽く保つ
(ブート時に読むのは末尾エントリのみ、の運用を軽く保つため。2026-07-05 導入、D35)。
アーカイブは凍結 (訂正注記のみ追記可)。既存アーカイブの一覧は `docs/archive/README.md`。

---
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

## 2026-09-27 (1905) — [T-2868] MOCC read-heavy の literal 候補の G2 6 件は literal なしの stock でも同じ形で出た — verifier の判定は記録された trace と一致し、差し込みは待ち時間 1 行だけ。原因は MOCC 側 (本体か trace の記録) に絞られた (insight のみ、計算 3.83 node 時間、branch worktree-dev-wave-t2868-mocc-g2)

- 正本: `output/insights/2026-09-27/t2868-mocc-g2-cause/README.md` (切り分け表・再検査・stock 追加走・MOCC 所見の構造化)。t2849-mocc-conn の insight へ §10 を追記した (§4 の abort 率列が legacy の値だった件と分母の訂正、元の記述は不変)。
- ユーザー確認: stock 追加走の規模を AskUserQuestion で確認し、回答は「64 反復 (推奨)」(16 slot・4 job、見積り 3.6〜4.2 node 時間)。実費は段 A 0.345・段 B 3.18・再検査 0.31、計 3.83 node 時間 (request 31813・31863〜31866・32027)。
- 段 3 の相談 2 レンズの所見 12 件はすべて real・採用。最重要は次の 3 件。
  - 段 B の対照は既存 harness の stock 適応に一本化し、BACK_OFF=0 と runner 改造を削った。
  - 親の検出力の計算を撤回した (既観測の 0/30 を未観測として数えていた)。
  - 段 A の結論を「記録された trace の中の整合」に限定した。
- 親の誤読 2 件を記録で訂正した。1 slot の性能構成の反復を 4 と読んだ (正しくは最大 5、anomaly で打ち切り)。digest の abort 率を性能構成の値と読んだ (legacy の値)。
- 段 6 の read-only レビュー 1 本 (事実の再抽出): 件数・witness・統計値・Elapse はすべて一次資料と一致。所見 5 件をすべて real として docs を修正した。修正したのは、patch 照合から「意味の変更を排除」と広げた点、非有意な率比較から候補の原因を断定した点、publish の行番号 (1259〜1260)、(iii) の判定語、率の書き方。記録 commit の後の全史 provenance 監査 (32089.nqsv) は 13,101 件で新規違反なし。
- エージェント工数: Codex plan 1・consult 2・author 1 (probe 465 行、branch `t2868-probe-author` `d86ec8f48`、land しない)・review 1。
- 残置物 (掃除の対象): unit 木 `.claude/worktrees/t2868-probe-author` (未統合の probe branch なので remove-child は rc=20 の見込み)、job dir の submit 木 4 本 (`/work/1/SFC/tanab/tmp/t2868-mocc-g2-20260927/trees/sb1..4`、lock 済み)、trace 保全 `izanagi-repro-archive/t2868-mocc-stock-20260927` (35 GB)。
- 素材: 比較 harness の read-heavy 動作点 (48 thread・1,000,000 record・rr95) で、MOCC の stock は性能構成の検査に 74 反復中 3 件落ちた。literal 候補は 119 反復中 6 件で、率の差は検出されなかった (両側 Fisher p = 0.50)。正しさゲートは候補と stock を同じ基準で検査し、同じ実装の G2 を両方に検出した。これは「合成候補の誤りを捕まえた」例ではない。

- [T-2868] 6 件の原因を切り分けた。verifier の誤検出は記録された trace の下で排除 (同版の再実行と生の行の照合が 9/9 一致)。literal 差し込みによる source の直接変更は排除 (patch は待ち時間 1 行。待ち時間が並行実行を変える経路は残る)。literal は必要条件ではない (stock 3/74 で同じ形の G2。候補での寄与の有無と率の同等性は示していない)。MOCC 側に絞られ、本体と hook の分離は既往の三分岐の未達として新規課題の材料に含めた。

### 次の一手 — 「(番号)」だけの項は、その番号のエントリ (archive 含む) から変わらない持ち越し

- [T-139] (1904)
- [T-265] (1904)
- [T-129] (1904)
- [T-238] (1904)
- [T-570] (1904)
- [T-580] (1904)
- [T-793] (1904)
- [T-823] (1904)
- [T-841] (1904)
- [T-1069] (1904)
- [T-1071] (1904)
- [T-1234] (1904)
- [T-1295] (1904)
- [T-1524] (1904)
- [T-1660] (1904)
- [T-1702] (1904)
- [T-1703] (1904)
- [T-1708] (1904)
- [T-1784] (1904)
- [T-1794] (1904)
- [T-1832] (1904)
- [T-1834] (1904)
- [T-1882] (1904)
- [T-1883] (1904)
- [T-1944] (1904)
- [T-1950] (1904)
- [T-2000] (1904)
- [T-2005] (1904)
- [T-2052] (1904)
- [T-2084] (1904)
- [T-2092] (1904)
- [T-2100] (1904)
- [T-2172] (1904)
- [T-2205] (1904)
- [T-2218] (1904)
- [T-2221] (1904)
- [T-2222] (1904)
- [T-2244] (1904)
- [T-2245] (1904)
- [T-2250] (1904)
- [T-2273] (1904)
- [T-2277] (1904)
- [T-2288] (1904)
- [T-2300] (1904)
- [T-2318] (1904)
- [T-2322] (1904)
- [T-2323] (1904)
- [T-2351] (1904)
- [T-2378] (1904)
- [T-2387] (1904)
- [T-2404] (1904)
- [T-2415] (1904)
- [T-2422] (1904)
- [T-2425] (1904)
- [T-2451] (1904)
- [T-2453] (1904)
- [T-2459] (1904)
- [T-2461] (1904)
- [T-2463] (1904)
- [T-2511] (1904)
- [T-2522] (1904)
- [T-2538] (1904)
- [T-2541] (1904)
- [T-2559] (1904)
- [T-2560] (1904)
- [T-2561] (1904)
- [T-2575] (1904)
- [T-2604] (1904)
- [T-2606] (1904)
- [T-2648] (1904)
- [T-2685] (1904)
- [T-2699] (1904)
- [T-2725] (1904)
- [T-2739] (1904)
- [T-2740] (1904)
- [T-2741] (1904)
- [T-2754] (1904)
- [T-2755] (1904)
- [T-2759] (1904)
- [T-2767] (1904)
- [T-2787] (1904)
- [T-2806] (1904)
- [T-2808] (1904)
- [T-2818] (1904)
- [T-2820] (1904)
- [T-2827] (1904)
- [T-2829] (1904)
- [T-2838] (1904)
- [T-2840] (1904)
- [T-2846] (1904)
- [T-2848] (1904)
- [T-2850] (1904)
- [T-2851] (1904)
- [T-2852] (1904)
- [T-2853] (1904)
- [T-2854] (1904)
- [T-2855] (1904)
- [T-2859] (1904)
- [T-2864] (1904)
- [T-2865] (1904)
- [T-2867] (1904)
- [T-2870] (1904)
- [T-2871] (1904)
- [T-2872] **P1・ユーザー裁定待ち (VLDB: MOCC の比較の妥当性)**: MOCC の read-heavy (48 thread・1,000,000 record・rr95、pin C) では、stock 自体が性能構成の検査に落ちる反復がある ([T-2868] insight §3、観測 3/109 = 2.8%、95% 区間 0.6〜7.8%)。t2849 の read-heavy の stock 比・終点選択・certified 終点はこの実装の上の値である。
  - 扱いの択一: (a) MOCC の read-heavy を比較から外す / (b)「基準プロトコル自体が非直列化可能な cell」と注記して残す / (c) 反復を増やして率を推定してから決める。
  - 関連の人間手番: 上流報告案 [T-2791] へ本条件を追記するか。(iii) 本体と (iv) hook の分離は未達 (観測者効果の小さい計器が要る)。

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

## 2026-09-29 (1907) — [T-2852] VLDB 差分分析 P5 (workload 記述 × critic の介入) の事前登録を草稿で置き、試走 v2 の実測単価で見積りを取り直した — 一次資料の 120〜240 評価は 48.2〜96.4 node 時間 (換算の約 2.8 倍、LLM の待ちの node 占有が主因)。親の推奨は S1-wh の本走を今は投入せず S3 の後に回す (草稿 + insight、計算投入 0、branch dev-wave-t2852-p5-prereg)

- 正本: 草稿 `docs/workload-description-critic-intervention-preregistration.md` (未発効)、起草記録 `output/insights/2026-09-28/t2852-p5-intervention-prereg-draft/README.md`
  (実測の file:line・見積りの計算・ユーザー確認の束・段 2〜6 の経緯)、設計判断 D2278。
- 見積りの単価は試走 v2 の score を含まない集計 (`section8.json`・`failures-noscore.json`) だけから取った。親は試走 v2 の score を見ていない。
- 段 3 の相談 2 本 (統計・事前登録適合 / 実行可能性・規律・過剰) の所見 16 件はすべて real・採用。主なものは、critic なしで失敗理由の返却が消える件 (現行 K0 では
  構造化された失敗理由が critic 診断経由でしか planner・coder に届かない) への対処として失敗理由の写しを両水準に渡すこと、P3 登録の規模の規則を継承しないこと、
  表示の外に残る workload の露出の列挙、人手分類を 3 母集団に分けること、「2.8 倍」「66%」の言い方の訂正。
- 段 6 の read-only レビューは NO-GO (must-fix 2)。親が段 4 で足した「予備の観察」(記述の表示が coder の最初の提案を動かすかを記録入力から呼び直して見る) を、
  選び方の規則が固定されず依頼 (草稿と見積りだけ) を超えるとして外した。ほかに anomaly 0 件の出典の誤り (`section8.json` には件数の欄が無い) を直した。
  焦点再レビュー 2 巡で GO。
- 受入全走の 1・2 回目 (2026-09-28 08:36・08:55 JST) は Pegasus の定期保守 (9/28 09:00〜21:00 JST、全 queue が DIS/INA) に当たり、shard の queue 待ち
  900 秒の打ち切り (rc=70 source_rc=16) でテストは 1 件も走らなかった。本 wave に帰属しない。保守明けの 9/29 に投げ直した。
- エージェント工数: Claude 調査子 1 (sonnet、K0 への workload 情報と critic の経路の棚卸し)・Codex plan 1・consult 2・review 3 (初回 + 焦点再レビュー 2)、全 Codex は gpt-6-sol / medium。
- 全史 provenance 監査 (commit 1 の後): 13,125 件、新規違反なし。

### 次の一手 — 「(番号)」だけの項は、その番号のエントリ (archive 含む) から変わらない持ち越し

- [T-139] (1906)
- [T-265] (1906)
- [T-129] (1906)
- [T-238] (1906)
- [T-570] (1906)
- [T-580] (1906)
- [T-793] (1906)
- [T-823] (1906)
- [T-841] (1906)
- [T-1069] (1906)
- [T-1071] (1906)
- [T-1234] (1906)
- [T-1295] (1906)
- [T-1524] (1906)
- [T-1660] (1906)
- [T-1702] (1906)
- [T-1703] (1906)
- [T-1708] (1906)
- [T-1784] (1906)
- [T-1794] (1906)
- [T-1832] (1906)
- [T-1834] (1906)
- [T-1882] (1906)
- [T-1883] (1906)
- [T-1944] (1906)
- [T-1950] (1906)
- [T-2000] (1906)
- [T-2005] (1906)
- [T-2052] (1906)
- [T-2084] (1906)
- [T-2092] (1906)
- [T-2100] (1906)
- [T-2172] (1906)
- [T-2205] (1906)
- [T-2218] (1906)
- [T-2221] (1906)
- [T-2222] (1906)
- [T-2244] (1906)
- [T-2245] (1906)
- [T-2250] (1906)
- [T-2273] (1906)
- [T-2277] (1906)
- [T-2288] (1906)
- [T-2300] (1906)
- [T-2318] (1906)
- [T-2322] (1906)
- [T-2323] (1906)
- [T-2351] (1906)
- [T-2378] (1906)
- [T-2387] (1906)
- [T-2404] (1906)
- [T-2415] (1906)
- [T-2422] (1906)
- [T-2425] (1906)
- [T-2451] (1906)
- [T-2453] (1906)
- [T-2459] (1906)
- [T-2461] (1906)
- [T-2463] (1906)
- [T-2511] (1906)
- [T-2522] (1906)
- [T-2538] (1906)
- [T-2541] (1906)
- [T-2559] (1906)
- [T-2560] (1906)
- [T-2561] (1906)
- [T-2575] (1906)
- [T-2604] (1906)
- [T-2606] (1906)
- [T-2648] (1906)
- [T-2685] (1906)
- [T-2699] (1906)
- [T-2725] (1906)
- [T-2739] (1906)
- [T-2740] (1906)
- [T-2741] (1906)
- [T-2754] (1906)
- [T-2755] (1906)
- [T-2759] (1906)
- [T-2767] (1906)
- [T-2787] (1906)
- [T-2806] (1906)
- [T-2808] (1906)
- [T-2818] (1906)
- [T-2820] (1906)
- [T-2827] (1906)
- [T-2829] (1906)
- [T-2838] (1906)
- [T-2840] (1906)
- [T-2846] (1906)
- [T-2848] (1906)
- [T-2850] (1906)
- [T-2851] (1906)
- [T-2852] **P1・ユーザー確認待ち (VLDB 差分分析 P5: 介入による理由の説明)**: 事前登録の草稿 `docs/workload-description-critic-intervention-preregistration.md`
  (未発効) と、試走 v2 の実測単価による見積りを置いた (D2278)。発効に要るのは次のユーザー確認 (D2212 項 4、一括承認にしない)。
  (1) 進め方の択一: (a) S1-wh で本走 (6 cell × n = 3 / 4 / 5 で 72.3 / 96.4 / 120.5 node 時間、LLM の直列 48.0 / 64.0 / 80.0 時間、中央値の単価) か、
  (c) 介入と出力コードの分類を S3 (関数方策軸、[T-2867]) の生成器対照の後に別の登録で行うか。親の推奨は (c) (D2272 項 2 の 3 理由が本書にも残り、
  S1 の coder 出力は数値 1 行で機構の変更を読めない)。(2) (a) なら規模と評定者 (人 2 名)。発効には草稿 §13 の実装 (Codex author。役割文書の入力節の改訂は
  ユーザー承認事項) と計算確認が要る。材料は `output/insights/2026-09-28/t2852-p5-intervention-prereg-draft/README.md` §5。
- [T-2853] (1906)
- [T-2854] (1906)
- [T-2855] (1906)
- [T-2859] (1906)
- [T-2864] (1906)
- [T-2865] (1906)
- [T-2867] (1906)
- [T-2870] (1906)
- [T-2871] (1906)
- [T-2872] (1906)

## 2026-09-29 (1908) — VHash 論文の文献調査と新規性の位置づけ — 出典メモの文献要約を原典で照合し、本案 4 点を既知と未確定に分けた (insight のみ、branch worktree-dev-wave-vhash-related-work)

- 依頼: ユーザー依頼で親セッションが用意した投げ文 (`/work/1/SFC/tanab/tmp/vhash-2026-09-29/md_1.txt` と `common.txt`)。
  着手時、対象 item も `docs/paper-story-vhash/` も local main に未着地で、同じ中身の複製 (docs-snapshot) を読んだ。
  ユーザー就寝中のため判断は自分で行うよう、並行セッションの監督役から 2026-09-29 に連絡があった (ユーザーへの問い合わせは 0 件)。
- 成果物と結論: `output/insights/2026-09-29/vhash-related-work/README.md` (§0 が要約、§8 が 3 分類)。
- 検索の経緯: 事前登録した DBLP 12 本は全て HTTP 200 の bot 判定 HTML を返したため、結果を判定せず走行無効とし、
  OpenAlex の題名検索へ切り替えた (F1057)。
- 段 6 の read-only レビュー (codex 1 本) は NO-GO で所見 5 件 (must-fix 1・should-fix 3・nit 1)。全件 real と裁定して親が直した。
  must-fix は Morty の「前進の結果を truncation 境界に使う」という誤読 (版順序は開始時に固定)。should-fix の 1 件で、
  起草時に「言われていないと主張できる」に置いた 1 項目を、検索式と主張の対応を結果を見てから選んでいたこと、および
  要裁定 1 件を題名だけで範囲外にしていたことを理由に未確定へ移した。
- 焦点再レビュー (codex 1 本) は前回 5 件を全て closed とし、新規 2 件 (未取得候補の数え方が行数か文献数か曖昧・
  Morty の読んだ節に §4.1 が抜けている) を出した。どちらも記録の修正で、親が直して grep で確かめて閉じた (3 巡目は起動していない)。
- 工数: 原典を読む子 5 本 (Claude sonnet、並行)、段 6 のレビュー 1 本と焦点再レビュー 1 本 (codex、各 5 分未満)。計算ノードは使っていない。

### 次の一手 — 「(番号)」だけの項は、その番号のエントリ (archive 含む) から変わらない持ち越し

- [T-139] (1907)
- [T-265] (1907)
- [T-129] (1907)
- [T-238] (1907)
- [T-570] (1907)
- [T-580] (1907)
- [T-793] (1907)
- [T-823] (1907)
- [T-841] (1907)
- [T-1069] (1907)
- [T-1071] (1907)
- [T-1234] (1907)
- [T-1295] (1907)
- [T-1524] (1907)
- [T-1660] (1907)
- [T-1702] (1907)
- [T-1703] (1907)
- [T-1708] (1907)
- [T-1784] (1907)
- [T-1794] (1907)
- [T-1832] (1907)
- [T-1834] (1907)
- [T-1882] (1907)
- [T-1883] (1907)
- [T-1944] (1907)
- [T-1950] (1907)
- [T-2000] (1907)
- [T-2005] (1907)
- [T-2052] (1907)
- [T-2084] (1907)
- [T-2092] (1907)
- [T-2100] (1907)
- [T-2172] (1907)
- [T-2205] (1907)
- [T-2218] (1907)
- [T-2221] (1907)
- [T-2222] (1907)
- [T-2244] (1907)
- [T-2245] (1907)
- [T-2250] (1907)
- [T-2273] (1907)
- [T-2277] (1907)
- [T-2288] (1907)
- [T-2300] (1907)
- [T-2318] (1907)
- [T-2322] (1907)
- [T-2323] (1907)
- [T-2351] (1907)
- [T-2378] (1907)
- [T-2387] (1907)
- [T-2404] (1907)
- [T-2415] (1907)
- [T-2422] (1907)
- [T-2425] (1907)
- [T-2451] (1907)
- [T-2453] (1907)
- [T-2459] (1907)
- [T-2461] (1907)
- [T-2463] (1907)
- [T-2511] (1907)
- [T-2522] (1907)
- [T-2538] (1907)
- [T-2541] (1907)
- [T-2559] (1907)
- [T-2560] (1907)
- [T-2561] (1907)
- [T-2575] (1907)
- [T-2604] (1907)
- [T-2606] (1907)
- [T-2648] (1907)
- [T-2685] (1907)
- [T-2699] (1907)
- [T-2725] (1907)
- [T-2739] (1907)
- [T-2740] (1907)
- [T-2741] (1907)
- [T-2754] (1907)
- [T-2755] (1907)
- [T-2759] (1907)
- [T-2767] (1907)
- [T-2787] (1907)
- [T-2806] (1907)
- [T-2808] (1907)
- [T-2818] (1907)
- [T-2820] (1907)
- [T-2827] (1907)
- [T-2829] (1907)
- [T-2838] (1907)
- [T-2840] (1907)
- [T-2846] (1907)
- [T-2848] (1907)
- [T-2850] (1907)
- [T-2851] (1907)
- [T-2852] (1907)
- [T-2853] (1907)
- [T-2854] (1907)
- [T-2855] (1907)
- [T-2859] (1907)
- [T-2864] (1907)
- [T-2865] (1907)
- [T-2867] (1907)
- [T-2870] (1907)
- [T-2871] (1907)
- [T-2872] (1907)
- [T-2873] **P2・VHash 論文の文献調査と新規性の位置づけ (残件)**: 本 wave の insight
  (`output/insights/2026-09-29/vhash-related-work/README.md` §8.3) の未確定 U0〜U4 を確定させる。
  本文を取得できなかった候補 (§11.2 の 7 行、文献としては 8 本) を図書館経由で読み、検索式と主張の対応を先に固定した登録母集合検索
  (`docs/related-work/README.md` 7.7.4 の RW3) を行う。Lomet 2012 と本案の差を関連研究節の文に書き分けるのは次の版の wave の担当。

## 2026-09-29 (1909) — [T-2853] R2 の fig8b 単位 (fig8 を含む) を元の driver で Pegasus に測り直した — 原 cohort の source から 2 group × 3 job、両 group とも not-observed-in-any-workload、原 cohort と合成しない表と同じ生成器の fig8 形の図 (insight のみ、計算 1.40 node 時間、branch dev-wave-t2853-r2-fig8b)

- 依頼の driver 名 `submit_b10_backoff_shape.sh` は待ち方 grid (fig13) の driver で、fig8/fig8b の原 cohort は `submit_b10_backoff_grid.sh --run-kind t2500-tail-formal` で投げていた (手順書・原 group 名・事前登録追記の項 6)。依頼の「元の driver」に合わせて後者を使い、driver・job body は変えていない。
- 段 3 の過剰・削除レンズが「両 group を cohort 2 の commit に揃えると cohort 1 を測り直したことにならない」と指摘し、段 4 で各 group を原 cohort の source commit から投げる形 (A′) に改めた。現行 main は CCBench pin 6810666 で、生成器の固定検査 (`repo_stock_pin == "511c953"`) を通らず同じ生成器で描けないため使わなかった。
- Pegasus が 2026-09-28 09:00〜21:00 のシステム保守に入り、投入 (08:11) から開始 (19:56) まで約 11 時間 45 分待った。途中で session が再起動し、ユーザーの「続けられる？」で再開した。
- fig8b 形 (2 block を縦に詰める v2) は R2 の値で生成器のレイアウト検査 (目盛の文字枠の重なり) に拒否された。検査は外さず、同じ生成器の fig8 形 (v1) で group ごとに描いた。
- 図と表は repo 外の使い捨て wrapper (Codex author・fix が作成、repo には入れていない) が生成器を bytes 不変のまま import し、cohort 定数と役割語だけを差し替えて描いた。陽性対照で既存 fig8・fig8b の artist_series と完全一致。
- 段 6 はレビュー 2 本 (一次資料照合・正しさ境界 / 過剰・削除) と焦点再レビュー 1 本。所見 5 件は全 real で処置し、焦点再レビューは GO (fig8b 形の図が未生成である点は結果前の登録どおりの帰結として T-2853 の残りへ)。詳細は insight §9。
- 投入手順書 `docs/b10-backoff-static-tail-submission.md` §2 は `tools/pegasus/submit_b10_backoff_grid.sh` を直接起動する書き方だが、file mode が 100644 のため rc=126 (許可がありません) で止まる。`bash` で起動すれば通る (本 wave では手順書を変えていない)。
- 親が repo 外の運転・読取 script (投入・待機・投入前検査・凍結 digest の計算) を書いた。確定は job 自身の測定前検査 (fail-closed) に拠る。

### 次の一手 — 「(番号)」だけの項は、その番号のエントリ (archive 含む) から変わらない持ち越し

- [T-139] (1908)
- [T-265] (1908)
- [T-129] (1908)
- [T-238] (1908)
- [T-570] (1908)
- [T-580] (1908)
- [T-793] (1908)
- [T-823] (1908)
- [T-841] (1908)
- [T-1069] (1908)
- [T-1071] (1908)
- [T-1234] (1908)
- [T-1295] (1908)
- [T-1524] (1908)
- [T-1660] (1908)
- [T-1702] (1908)
- [T-1703] (1908)
- [T-1708] (1908)
- [T-1784] (1908)
- [T-1794] (1908)
- [T-1832] (1908)
- [T-1834] (1908)
- [T-1882] (1908)
- [T-1883] (1908)
- [T-1944] (1908)
- [T-1950] (1908)
- [T-2000] (1908)
- [T-2005] (1908)
- [T-2052] (1908)
- [T-2084] (1908)
- [T-2092] (1908)
- [T-2100] (1908)
- [T-2172] (1908)
- [T-2205] (1908)
- [T-2218] (1908)
- [T-2221] (1908)
- [T-2222] (1908)
- [T-2244] (1908)
- [T-2245] (1908)
- [T-2250] (1908)
- [T-2273] (1908)
- [T-2277] (1908)
- [T-2288] (1908)
- [T-2300] (1908)
- [T-2318] (1908)
- [T-2322] (1908)
- [T-2323] (1908)
- [T-2351] (1908)
- [T-2378] (1908)
- [T-2387] (1908)
- [T-2404] (1908)
- [T-2415] (1908)
- [T-2422] (1908)
- [T-2425] (1908)
- [T-2451] (1908)
- [T-2453] (1908)
- [T-2459] (1908)
- [T-2461] (1908)
- [T-2463] (1908)
- [T-2511] (1908)
- [T-2522] (1908)
- [T-2538] (1908)
- [T-2541] (1908)
- [T-2559] (1908)
- [T-2560] (1908)
- [T-2561] (1908)
- [T-2575] (1908)
- [T-2604] (1908)
- [T-2606] (1908)
- [T-2648] (1908)
- [T-2685] (1908)
- [T-2699] (1908)
- [T-2725] (1908)
- [T-2739] (1908)
- [T-2740] (1908)
- [T-2741] (1908)
- [T-2754] (1908)
- [T-2755] (1908)
- [T-2759] (1908)
- [T-2767] (1908)
- [T-2787] (1908)
- [T-2806] (1908)
- [T-2808] (1908)
- [T-2818] (1908)
- [T-2820] (1908)
- [T-2827] (1908)
- [T-2829] (1908)
- [T-2838] (1908)
- [T-2840] (1908)
- [T-2846] (1908)
- [T-2848] (1908)
- [T-2850] (1908)
- [T-2851] (1908)
- [T-2852] (1908)
- [T-2853] **P1・(1)(1')(1'') の保全口と (2)(2')(3) と (4) R2 の入口と (5) の計画・R2 の投入単位と Elapse 見積り・17 図の描き直し・fig1 の生成器・fig15 の入力・R2 の fig8b 単位は済み (VLDB 差分分析 P6: 再現パッケージ)**: EA&B は初回投稿時に全実験の再現パッケージのリンクと実行手順を要するので、実験と並行で作る。保存するもの = コード、生成パッチ、入出力、探索設定、失敗候補を含む実験データ、図表の生成手順。失敗候補と否定的結果を含めて公開してよく (D2212 項 6)、provenance は粗い粒度 (システム名・モデル表示名・おおよその時期、D320) で足り、凍結 chain は足さない。初段 (量・保存費の見積り、trace の保存・公開方針、再実行の 3 経路) は `output/insights/2026-09-22/t2853-repro-package-estimate/README.md`、(2) job dir にだけあった論文根拠データの写し (repo 外 `/work/1/SFC/tanab/izanagi-repro-archive/t2853-20260923/`、sha256 全件一致) と (3) 系列ごとの実行手順・R1 の入力一式は `output/insights/2026-09-23/t2853-repro-package-archive/README.md`、(1) の標準評価経路の trace 保全口は D2233 (env `IZANAGI_TRACE_ARCHIVE_ROOT` の opt-in)、(5) の主要図の再実行計画は `output/insights/2026-09-23/t2853-figure-rerun-plan/README.md` で済んだ。**(1') 保全口の inventory に R1 の入力一式の残り (verifier の等価 argv・repo commit・完全 SHA の pin と宣言値・patch の bytes と sha256・verifier module の sha256) を D2160・B-8 の runner と同じ名前で足し、標準評価経路では build 時の source evidence と照合できたものだけを complete にした (D2247)。(5') のうち生成器のある 17 図の描き直しは値の差 0 で済んだ** (`output/insights/2026-09-26/t2853-archive-inventory-figure-redraw/README.md`)。**(5'') のうち fig1 は生成器 `tools/plotting/plot_p2_5_search_cost.py` と後継図 `fig1b_phase2_negative` を追跡下の入力だけから作り、旧図と値が一致した** (`output/insights/2026-09-26/t2853-fig1-generator/README.md`)。**(5'') のうち fig15 は生成器の既定入力を追跡下の逐語写し (`output/insights/2026-09-19/mocc-witlight-arm-run/verbatim/`、sha256 は pin と 5/5 一致) に替え、写しから描き直して旧図と値の差 0 (PNG は bytes 一致) を確かめた** (`output/insights/2026-09-27/t2853-fig15-input/README.md`)。**(1'') P1 (関数単位の軸 silo-function-policy) の実行経路 = job body の方策 mode で保全口の opt-in を必須にし、(4) その候補を受ける R2 の入口 (方策 driver の `--replay-proposal`、job mode `replay`、保存 proposal を別 campaign で LLM なしに再評価) を置いて計算ノードで 1 回通した** (`output/insights/2026-09-27/t2865-silo-policy-stage-f/README.md`、D2270)。**(2') 新しく論文根拠になった [T-2850] 試走 v2・[T-2849] MOCC 疎通・[T-2865] 段階 F の job dir 固有分と submit checkout 内の campaign 原本 (7 組 9,041 file) を repo 外 `/work/1/SFC/tanab/izanagi-repro-archive/t2853-20260927/` へ写して sha256 全件一致、(5'') R2 の投入単位を図 1 本 = 1 タスク (fig8b は fig8 を含む) とし、B-10 の元 job に残っていた NQSV 会計で fig2c・fig8/fig8b・fig13 の Elapse を確定した** (`output/insights/2026-09-27/t2853-repro-rest/README.md`)。**(5'') R2 の fig8b 単位 (fig8 を含む) は元の driver `submit_b10_backoff_grid.sh --run-kind t2500-tail-formal` で、原 cohort の source commit (R2-a = cohort 1 の `0600887d9`・事前登録 `cad6f46d8`、R2-b = cohort 2 の `8737cacb4`) から 2 group × 3 job を 6 ノードで同時に測り直し (1.40 node 時間)、両 group とも集団 verdict `not-observed-in-any-workload`・18/18 区間 declining・正しさ 120/0 で、原 cohort と合成しない別 attempt として並べた表と同じ生成器の fig8 形の図 2 枚を記録した (fig8b 形は生成器のレイアウト検査で拒否。trace 保全口は driver に渡す口が無く未使用)** (`output/insights/2026-09-28/t2853-r2-fig8b/README.md`)。残り: (1'') P0・P3・TPC-C の実験を走らせる前に、その実行経路で保全口の opt-in を有効にする (保全先と容量は見積り稿 §7)。verify fan-out の兄弟 node の反復は保全対象外のまま。(5'') R2 の投入は論文投稿前に、単位ごとに見積り表 (上の insight §3.3) を示し、2 node 時間以上ならユーザー確認後に投げる (D2212 項 4)。確認が要るのは fig13 (18.33 node 時間)・fig4 (正典 4 campaign で 8.88〜9.83、試算)・fig10 (3.40)・fig2c (2.98)、fig8b (1.40) は済み、fig6 (1.70)・fig11 (1.69)・fig2b (0.70〜0.77) は別系列の Elapse を当てた試算からの暫定の「不要」であり、投入形を決めた段階でその単位の全 job の Elapse 見積りで判定し直す。fig2b・fig1 の下地・fig4 を Pegasus で走らせる経路が既存 driver で組めるかは未確認。fig8b 形 (2 group を 1 枚に縦に詰める形) の R2 図は、生成器 `plot_b10_static_tail_formal.py` の v2 のレイアウト検査が R2 の値で目盛の文字枠の重なりを検出して拒否したため未生成で、得るには生成器のレイアウト変更 (実装、Codex author と受入) が要る。fig15 は R2 でなく観測の再実施で、元の認可が 1 回限りのため再実施には改めて認可が要る。(6) 公開範囲 (全量か役割別か) の最終確定は投稿前のパッケージ組み立て時 (目標投稿 2027-02-01、概要提出 2027-01-25)。新しく論文根拠になった job dir は、実験と並行で同じ手順 (保存先 `tools/`) で写す。
- [T-2854] (1908)
- [T-2855] (1908)
- [T-2859] (1908)
- [T-2864] (1908)
- [T-2865] (1908)
- [T-2867] (1908)
- [T-2870] (1908)
- [T-2871] (1908)
- [T-2872] (1908)
- [T-2873] (1908)

## 2026-09-29 (1910) — Cicada の実行履歴を判定器に掛けられるようにした — trace patch・壊し patch 3 本・fixture テスト。stock は巡回 0、壊し 3 本は全部巡回を検出し壊した経路に帰属、TRACE=0 は命令列一致 (patch + test + insight、branch worktree-dev-wave-vhash-cicada-verifier)

- 依頼: VHash 論文の並行 wave md_3 (ユーザー依頼により親セッションが作成、`/work/1/SFC/tanab/tmp/vhash-2026-09-29/md_3.txt`)。一次資料 `output/insights/2026-09-29/vhash-cicada-verifier/README.md`、置き場と範囲の判断は D2279。
- ユーザーは夜間不在 (マネージャー連絡)。依頼の「検査器の変更とテスト」を「判定器の production は変えず、既存の読み込みを Cicada 形の fixture テストで固定する」と読み替えたのは、段 3 相談 2 本の賛否を材料に親が決めた (D2279 項 4)。
- peer 連絡 2 件を自分で裏取りして採用: `patches/ledger.json` は entries 1 件固定なので README だけに登録、patch の新しい `#if` 条件は条件 gate の定義一覧照合 (`orchestrator/tests/test_ccbench_spawn_sites.py`) に掛かるので `TRACE` 以外を書かない。
- 事前登録の外れ: 判定器側の変異 M-V1 (版の圧縮で tid を 31 bit に狭める) は「変更前 HEAD では生き残る」と登録したが、既存の境界テストが検出した。新テストは同じ変異を追加 3 node で検出するが、新テストだけが検出する差分は示していない (一次資料 §6)。
- 工程の不具合 3 件 (いずれも判定基準は変えずに直した): (1) 生死確認 1 回目は起動器が workload 別 target の compile command 4 件を 1 件に絞れず停止、(2) 本走 1 回目は判定器の代表 witness 20 件 (終盤) と事象の先頭 200 件打ち切り (序盤) が作りとして重ならず帰属 0、(3) 本走 2 回目は gen_S の混雑で dispatch の全体時限 (待ちを含む) に当たり未開始のまま自動取消 (`--overall-grace` を足した)。
- 段 6 レビュー: 観点 A (RV-1〜3) と B (B1〜B5)。帰属の未証明 (RV-1 / B1) は全件出力の再走と親の raw 照合で閉じた。TRACE=0 の主張は YCSB target の 3 TU に限定 (RV-3)。B4 (全件出力と焦点 job の縮小) は不採用。
- 計算ノード: job 8 本で Elapse 合計 434 s (受入・変異の dispatch を除く)。Codex (gpt-6-sol、medium): plan 1、相談 2、author 3、fix 3、review 2。

### 次の一手 — 「(番号)」だけの項は、その番号のエントリ (archive 含む) から変わらない持ち越し

- [T-139] (1909)
- [T-265] (1909)
- [T-129] (1909)
- [T-238] (1909)
- [T-570] (1909)
- [T-580] (1909)
- [T-793] (1909)
- [T-823] (1909)
- [T-841] (1909)
- [T-1069] (1909)
- [T-1071] (1909)
- [T-1234] (1909)
- [T-1295] (1909)
- [T-1524] (1909)
- [T-1660] (1909)
- [T-1702] (1909)
- [T-1703] (1909)
- [T-1708] (1909)
- [T-1784] (1909)
- [T-1794] (1909)
- [T-1832] (1909)
- [T-1834] (1909)
- [T-1882] (1909)
- [T-1883] (1909)
- [T-1944] (1909)
- [T-1950] (1909)
- [T-2000] (1909)
- [T-2005] (1909)
- [T-2052] (1909)
- [T-2084] (1909)
- [T-2092] (1909)
- [T-2100] (1909)
- [T-2172] (1909)
- [T-2205] (1909)
- [T-2218] (1909)
- [T-2221] (1909)
- [T-2222] (1909)
- [T-2244] (1909)
- [T-2245] (1909)
- [T-2250] (1909)
- [T-2273] (1909)
- [T-2277] (1909)
- [T-2288] (1909)
- [T-2300] (1909)
- [T-2318] (1909)
- [T-2322] (1909)
- [T-2323] (1909)
- [T-2351] (1909)
- [T-2378] (1909)
- [T-2387] (1909)
- [T-2404] (1909)
- [T-2415] (1909)
- [T-2422] (1909)
- [T-2425] (1909)
- [T-2451] (1909)
- [T-2453] (1909)
- [T-2459] (1909)
- [T-2461] (1909)
- [T-2463] (1909)
- [T-2511] (1909)
- [T-2522] (1909)
- [T-2538] (1909)
- [T-2541] (1909)
- [T-2559] (1909)
- [T-2560] (1909)
- [T-2561] (1909)
- [T-2575] (1909)
- [T-2604] (1909)
- [T-2606] (1909)
- [T-2648] (1909)
- [T-2685] (1909)
- [T-2699] (1909)
- [T-2725] (1909)
- [T-2739] (1909)
- [T-2740] (1909)
- [T-2741] (1909)
- [T-2754] (1909)
- [T-2755] (1909)
- [T-2759] (1909)
- [T-2767] (1909)
- [T-2787] (1909)
- [T-2806] (1909)
- [T-2808] (1909)
- [T-2818] (1909)
- [T-2820] (1909)
- [T-2827] (1909)
- [T-2829] (1909)
- [T-2838] (1909)
- [T-2840] (1909)
- [T-2846] (1909)
- [T-2848] (1909)
- [T-2850] (1909)
- [T-2851] (1909)
- [T-2852] (1909)
- [T-2853] (1909)
- [T-2854] (1909)
- [T-2855] (1909)
- [T-2859] (1909)
- [T-2864] (1909)
- [T-2865] (1909)
- [T-2867] (1909)
- [T-2870] (1909)
- [T-2871] (1909)
- [T-2872] (1909)
- [T-2873] (1909)
- [T-2874] **P2・新規 (VHash 前提 G0 の後続)**: Cicada の trace (`patches/instr-cicada-trace.patch`、D2279) は YCSB point read / update の巡回検出まで働く (一次資料 `output/insights/2026-09-29/vhash-cicada-verifier/README.md`)。残り: (1) forwarding 試作を instr patch に重ねて同じ起動器で検査する (巡回なしは indeterminate であって certified ではない)、(2) certified を要する campaign の門へ入れるなら Cicada 用の証拠面と campaign 側の trace 供給の設計 (研究前進の裁定候補)、(3) pin を C から進めたら 4 patch の厳密適用と生死確認の取り直し、(4) 未対応 = scan の phantom・insert / delete・版昇格 (`#error`)・`group_commit>0`・YCSB 以外、TRACE=0 は tpcc / bomb / sbomb の TU が未比較、(5) trace hook の `izanagi-trace` 枝への移送は人間の判断。

## 2026-09-29 (1911) — VHash と timestamp forwarding の論文ストーリー系列を新設し、並行 wave の投げ文を用意する (docs のみ、branch worktree-paper-story-vhash-setup)

- ユーザー指示 (2026-09-29): 外部の対話 AI との議論をまとめた研究メモ (VHash・選択的 timestamp forwarding・GC の協調) を
  貼り、「これで論文を一本書こうかと考えている」「docs/ に新しい paper-story のディレクトリを専用に設けてくれ」
  「図やグラフを多用してわかりやすく」「dev-wave を並列で投げまくって調査・試行錯誤・実装・実験を進めたい」
  「投げ文は /work/1/SFC/tanabe/tmp に md_1.txt のように外出しして」と依頼した。`/work/1/SFC/tanabe` は実在せず、
  実在する `/work/1/SFC/tanab/tmp` の下に置いた。
- 新設の判断は D2280。初版 `2026-09-29.md` は Mermaid 24 枚・文字の図 1 枚・画像 0 枚。
- 確かめた事実: CCBench の `cc/silo/transaction.cc` には `#if TRACE` があり、`cc/cicada/` の全ファイルには `TRACE` の
  文字列が無い。`orchestrator/verifier/` にも `cicada` の文字列が無い。Cicada の variant は現状、正しさ検査器を通せない。
- 並行 wave の投げ文 6 本 (文献・実測・正しさ検査・小さいモデル・配置の微小計測・forwarding 試作) を repo の外に置いた。
  各 wave は下の新規 item に対応する。投げ文は T 番号を持たず、item を本文の文言で探す形にした (ユーザー指摘「T番号に依存する必要ある？」)。
  本エントリの land より先に、同じ投げ文 (md_1) の文献調査 wave が docs の repo 外複製を読んで着手・着地し、
  文献調査の残件を [T-2873] として自分で登録した。重複を避けるため、本エントリは文献調査の新規 item を登録しない。
- 本エントリの land は、Pegasus の gen_S が 80〜90 本待ちの混雑で受入の shard が queue 待ち 900 秒で 8 回打ち切られ
  (テストは 0 件実行)、06:31 JST に門番経由の 9 回目で child-green になった。その後 main へ md_1 wave が着地したので
  取り込み直し、断片を直して受入をやり直した。
- 受入の赤の帰属 (DW-O18): 07:07 JST の受入 (tip 5104356aa、main f6772df03) で
  `orchestrator/tests/test_env_contract_activation.py` の 3 件
  (`test_historical_calibration_is_verified_only_when_resolved_in_source_stage[missing]`・同 `[modified]`・
  `test_import_performs_no_open_or_stat_io_in_worktree_or_archive_source_stage`) が、テスト内の
  `git archive ... HEAD` の 30 秒 timeout (`subprocess.TimeoutExpired`) で落ちた。本 branch の差分は docs と spool fragment だけで
  この経路に触れない。同じ tip で 3 件だけを計算ノードへ投げた単独再走 (request 33958.nqsv) は `3 passed in 11.11s`。
  混雑時の共有 FS による一過性で、本 branch に帰属しないと判定した。
- 同じく 07:31 JST の受入 (tip 58c6906aa、main da4068e0e) で `orchestrator/tests/test_t810_coordinator.py` の 3 件
  (`test_prepare_group_accepts_external_root_with_anchor_union`・`test_prepare_group_rejects_self_consistent_foreign_git_identity_before_any_mkdir`・
  `test_prepare_group_rejects_forged_git_identity_before_any_mkdir`) が `cannot read worktree registration: file is absent` で落ちた。
  本 branch は worktree 登録の経路に触れない。3 件だけの計算ノード単独再走は `3 passed in 5.27s`。受入中の並行 session による
  worktree 登録の変化と読み、本 branch に帰属しないと判定した。

### 次の一手 — 「(番号)」だけの項は、その番号のエントリ (archive 含む) から変わらない持ち越し

- [T-139] (1910)
- [T-265] (1910)
- [T-129] (1910)
- [T-238] (1910)
- [T-570] (1910)
- [T-580] (1910)
- [T-793] (1910)
- [T-823] (1910)
- [T-841] (1910)
- [T-1069] (1910)
- [T-1071] (1910)
- [T-1234] (1910)
- [T-1295] (1910)
- [T-1524] (1910)
- [T-1660] (1910)
- [T-1702] (1910)
- [T-1703] (1910)
- [T-1708] (1910)
- [T-1784] (1910)
- [T-1794] (1910)
- [T-1832] (1910)
- [T-1834] (1910)
- [T-1882] (1910)
- [T-1883] (1910)
- [T-1944] (1910)
- [T-1950] (1910)
- [T-2000] (1910)
- [T-2005] (1910)
- [T-2052] (1910)
- [T-2084] (1910)
- [T-2092] (1910)
- [T-2100] (1910)
- [T-2172] (1910)
- [T-2205] (1910)
- [T-2218] (1910)
- [T-2221] (1910)
- [T-2222] (1910)
- [T-2244] (1910)
- [T-2245] (1910)
- [T-2250] (1910)
- [T-2273] (1910)
- [T-2277] (1910)
- [T-2288] (1910)
- [T-2300] (1910)
- [T-2318] (1910)
- [T-2322] (1910)
- [T-2323] (1910)
- [T-2351] (1910)
- [T-2378] (1910)
- [T-2387] (1910)
- [T-2404] (1910)
- [T-2415] (1910)
- [T-2422] (1910)
- [T-2425] (1910)
- [T-2451] (1910)
- [T-2453] (1910)
- [T-2459] (1910)
- [T-2461] (1910)
- [T-2463] (1910)
- [T-2511] (1910)
- [T-2522] (1910)
- [T-2538] (1910)
- [T-2541] (1910)
- [T-2559] (1910)
- [T-2560] (1910)
- [T-2561] (1910)
- [T-2575] (1910)
- [T-2604] (1910)
- [T-2606] (1910)
- [T-2648] (1910)
- [T-2685] (1910)
- [T-2699] (1910)
- [T-2725] (1910)
- [T-2739] (1910)
- [T-2740] (1910)
- [T-2741] (1910)
- [T-2754] (1910)
- [T-2755] (1910)
- [T-2759] (1910)
- [T-2767] (1910)
- [T-2787] (1910)
- [T-2806] (1910)
- [T-2808] (1910)
- [T-2818] (1910)
- [T-2820] (1910)
- [T-2827] (1910)
- [T-2829] (1910)
- [T-2838] (1910)
- [T-2840] (1910)
- [T-2846] (1910)
- [T-2848] (1910)
- [T-2850] (1910)
- [T-2851] (1910)
- [T-2852] (1910)
- [T-2853] (1910)
- [T-2854] (1910)
- [T-2855] (1910)
- [T-2859] (1910)
- [T-2864] (1910)
- [T-2865] (1910)
- [T-2867] (1910)
- [T-2870] (1910)
- [T-2871] (1910)
- [T-2872] (1910)
- [T-2873] (1910)
- [T-2874] (1910)
- [T-2875] **P1・新規**: Cicada の版探索長・hot 相当の当たり率 (K 別の反実仮想)・forwarding の機会・GC 境界の遅れ・生存版数を診断計器 patch で実測する (メモ §29 段階 1)。
- [T-2876] **P1・新規**: Cicada に検査用トレースを足し、izanagi の正しさ検査器で多版の履歴を検査できるようにする。壊した Cicada の positive control も用意する (forwarding 試作の正しさゲートの前提)。
- [T-2877] **P1・新規**: 選択的 forwarding のプロトコルを小さいモデルで書き、reader・writer・forwarding・GC の割り込みを全探索して serializability を検査する (メモ §29 段階 2)。
- [T-2878] **P1・新規**: 版選択の配置を微小計測で比べる (連結リスト・連続配置 + scalar・連続配置 + SIMD、K・版の深さ・値の大きさ)。
- [T-2879] **P1・新規**: Cicada に cold 境界 (論理的な K 版) で発火する選択的 forwarding を inert variant patch として試作し、abort して再実行する対照と比べる (GC 保護は変えない、メモ §29 段階 3)。
- [T-2880] **P2・新規**: 上の 5 件と [T-2873] (文献調査) の一次資料が揃ったら、`docs/paper-story-vhash/` の 2 版目を全面再導出する (図を先に)。
