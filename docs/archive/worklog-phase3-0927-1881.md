## 2026-09-27 (1881) — /rulings 全件 第 37 回 — 索引 10 行 (裁定待ち 4・人間手番 4・据え置き 1・収載維持 1) を推奨どおり裁定した。D297 の header 受理規則 v2 を承認して実装を委任し、正しさ防壁自身の束縛拡張 (D1075・第 3 回の T-734) を止め、受入の択 B は今は採らず同じ長さの期間で取り直し、si の trace v2 は patch のまま置く (docs のみ、branch worktree-rulings-all-20260927)

- **窓は entry 1868〜1879、決定は D2249〜D2258。** 前回の全件走は第 36 回 (entry 1868、D2249、窓は 1859〜1867)。収集・提示 (07:47 JST) は main `bad8365b9`、提示の直後に [T-2797] の記録が着地して
  main `3bcf17276` (entry 1880、D2259) になり、新しいユーザー判断の項は無いことを確かめた。受領文は「推奨通り」。
- **次の一手 117 項を carry 鎖の実体まで解決した (未解決 0)。** entry 1878 の持ち越し整理 (D2257) で 501 項が取り下げられた後の母集合。機械走査 (`sweep_pending.py`) は [T-2797] の「ユーザー確認待ち」を拾わず、
  全項の実体本文を語で総ざらいして補った。見送り台帳は [T-436] と [T-281] の相乗り条件が再成立した (どちらも D1780 のまま)。窓内の failures 追記に裁定を求めるものは無い。
- **稼働 session への照会と会話記録で 3 件を確かめた (索引外)。** [T-2797] はユーザーが 07:28 JST に同 wave の session で見送りを決めた (本人入力で確認、記録は D2259)。
  [T-2849] (3) の計算確認はユーザーが「20 候補 × 3 workload」と回答済み。[T-2865] 段階 E の `.claude/agents/` 差分は D2256 項 7 で承認済み。
- **[T-2838] の取り直しを D2249 項 3 の指示どおり本 rulings で行った。** 9/26 以降 (約 17 時間) は待ちの p90 567 秒・30 分以上 1 区間で、基準線 (約 5.5 日、p90 1,688 秒・11 区間) と期間が違うため比べられない。
- **索引 10 行 = ユーザー裁定待ち 4 + 人間手番 4 + 据え置き 1 + 収載維持 1。裁定済み未実装 38** (見出しが「裁定済み/既裁定 → 実装・手番・相乗り・待ち・実施」型の項を数えた。
  第 36 回の同法 126 との差は D2257 の取り下げ)。Git は未 push 113 (≥ 20 で人間手番)、CCBench `izanagi-tpcc-v3-silo-mocc` も未 push。
- **相談 2 本 (read-only、`--lane sol`、medium、両方受理)。** A は項 1 の根拠 (TPC-C は差分分析 §10 のユーザー裁定で必須) を訂正させ、項 2 に反対 ((a) 続ける) し起草の前提 (hook の射程) の誤りを指摘し、
  項 3 を根拠不足 (期間違い) とした → 根拠の訂正・前提の撤回・項 3 の推奨の改めを採用し、項 2 は (b) を維持して反対意見を提示に併記した。B は [T-2847] の si の trace v2 の枝移送・pin 前進 (人間の判断) を漏れとして拾った → 項 4 に採用。
- **裁定は D2260 (10 項)。** 項 1 = [T-2854] 規則 v2 を承認し実装を Codex author の wave に委任、項 2 = D1075 と第 3 回の [T-734] を取り下げ [T-733] [T-734] [T-2344] [T-2402] を止める
  (既存の束縛・検査は変えず、推移閉包の意味の source-bound は名乗らない)、項 3 = [T-2838] 択 B は今は採らず約 5.5 日たまった後に同じ長さで取り直す、項 4 = [T-2847] si の trace v2 は patch のまま
  (C2' の pin 前進を問う機会に併せて諮る)、項 5〜10 = 継続。
- 索引・起草推奨・相談の出力・取り直しは `/work/1/SFC/tanab/dev-wave-jobs/rulings-all-20260927/` (`materials-index.md` / `final-index-note.md` / `artifacts/consult-{a,b}-out.md` / `probe-since0926.md`)。
  裁定の控えは repo 外 `rulings-inbox/2026-09-27-rulings-full37-verdicts.md`。
- **実装面の差分は 0 である。** 変更は台帳 fragment だけ。
- 工数: codex 子 2 本 (consult)、Claude 子 1 本 (sonnet、見送り台帳の相乗り照合、read-only)。計算ノード job は受入のみ。

- [T-733] 取り下げ (D2260 項 2): 第 1 層 (exact 24 → 62 path) の後の残り (未収載 69 module の収載と非 import 委譲の束縛) は行わない。ユーザーが D1075 と 2026-08-16 第 3 回の [T-734] の裁定を名指して取り下げ、拡張を止めた (D2260 項 2)。既に束縛した収載 (exact-96 まで) と既存の検査・gate・変異の固定は変えず、推移閉包の意味で「certified 経路が source-bound である」とは名乗らない (D1884 の文言のまま)。規律 1・2 は不変。

- [T-734] 取り下げ (D2260 項 2): 全 certified sink への source gate は課さない。ユーザーが D1075 と 2026-08-16 第 3 回の [T-734] の裁定を名指して取り下げ、拡張を止めた (D2260 項 2)。既に束縛した収載 (exact-96 まで) と既存の検査・gate・変異の固定は変えず、推移閉包の意味で「certified 経路が source-bound である」とは名乗らない (D1884 の文言のまま)。規律 1・2 は不変。

- [T-2344] 取り下げ (D2260 項 2): tuple 起点の 2 段目 23 本と、それに付けた exact-85・exact-96 の歴史収載の再走査は行わない (歴史収載は現状のまま)。ユーザーが D1075 と 2026-08-16 第 3 回の [T-734] の裁定を名指して取り下げ、拡張を止めた (D2260 項 2)。既に束縛した収載 (exact-96 まで) と既存の検査・gate・変異の固定は変えず、推移閉包の意味で「certified 経路が source-bound である」とは名乗らない (D1884 の文言のまま)。規律 1・2 は不変。

- [T-2402] 取り下げ (D2260 項 2): gate report の推移閉包への所属の確認と、それに続く段階実装・個別収載の諮問は行わない。ユーザーが D1075 と 2026-08-16 第 3 回の [T-734] の裁定を名指して取り下げ、拡張を止めた (D2260 項 2)。既に束縛した収載 (exact-96 まで) と既存の検査・gate・変異の固定は変えず、推移閉包の意味で「certified 経路が source-bound である」とは名乗らない (D1884 の文言のまま)。規律 1・2 は不変。

### 次の一手 — 「(番号)」だけの項は、その番号のエントリ (archive 含む) から変わらない持ち越し

- [T-139] (1880)
- [T-265] (1880)
- [T-129] (1880)
- [T-238] (1880)
- [T-570] (1880)
- [T-580] (1880)
- [T-793] (1880)
- [T-823] (1880)
- [T-841] (1880)
- [T-1068] (1880)
- [T-1069] (1880)
- [T-1071] (1880)
- [T-1072] (1880)
- [T-1234] (1880)
- [T-1295] (1880)
- [T-1418] (1880)
- [T-1524] (1880)
- [T-1660] (1880)
- [T-1702] (1880)
- [T-1703] (1880)
- [T-1708] (1880)
- [T-1784] (1880)
- [T-1794] (1880)
- [T-1832] (1880)
- [T-1834] (1880)
- [T-1882] (1880)
- [T-1883] (1880)
- [T-1944] (1880)
- [T-1950] (1880)
- [T-1983] (1880)
- [T-2000] (1880)
- [T-2005] (1880)
- [T-2052] (1880)
- [T-2084] (1880)
- [T-2092] (1880)
- [T-2100] (1880)
- [T-2104] (1880)
- [T-2172] (1880)
- [T-2205] (1880)
- [T-2207] (1880)
- [T-2218] (1880)
- [T-2221] (1880)
- [T-2222] (1880)
- [T-2223] (1880)
- [T-2244] (1880)
- [T-2245] (1880)
- [T-2250] (1880)
- [T-2273] (1880)
- [T-2277] (1880)
- [T-2288] (1880)
- [T-2300] (1880)
- [T-2318] (1880)
- [T-2322] (1880)
- [T-2323] (1880)
- [T-2351] (1880)
- [T-2378] (1880)
- [T-2387] (1880)
- [T-2404] (1880)
- [T-2415] (1880)
- [T-2422] (1880)
- [T-2425] (1880)
- [T-2451] (1880)
- [T-2453] (1880)
- [T-2459] (1880)
- [T-2461] (1880)
- [T-2463] (1880)
- [T-2511] (1880)
- [T-2522] (1880)
- [T-2538] (1880)
- [T-2541] (1880)
- [T-2559] (1880)
- [T-2560] (1880)
- [T-2561] (1880)
- [T-2575] (1880)
- [T-2604] (1880)
- [T-2605] **P3・裁定済み (D2044 項 36 / D2104 項 38 / D2120 項 27 / D2150 項 8 / D2148 項 14 / D2172 項 11 / D2174 項 6 / D2186 項 9 /
  D2194 項 13 / D2200 項 11 / D2206 項 15 / D2211 項 14 / D2219 項 11 / D2227 項 10 / D2235 項 5 / D2237 項 4 / D2243 項 8 / D2249 項 8 / D2260 項 9) → ユーザー指定待ち**: 第 37 回も表記の指定は無く据え置き。`LICENSE.md` の
  必要表示と README の商用窓口が指す著作権者表記は、ユーザーの具体的な指定があれば AI が反映する。git author identity を根拠なく置換しない。
- [T-2606] (1880)
- [T-2648] (1880)
- [T-2685] (1880)
- [T-2699] (1880)
- [T-2725] (1880)
- [T-2726] (1880)
- [T-2727] (1880)
- [T-2739] (1880)
- [T-2740] (1880)
- [T-2741] (1880)
- [T-2754] (1880)
- [T-2755] (1880)
- [T-2759] (1880)
- [T-2767] (1880)
- [T-2787] (1880)
- [T-2806] (1880)
- [T-2808] (1880)
- [T-2818] (1880)
- [T-2820] (1880)
- [T-2827] (1880)
- [T-2829] (1880)
- [T-2838] **P2・択 A 実施済み → 択 B は今は採らない (D2260 項 3)、観測が基準線と同じ約 5.5 日たまった後 (2026-10-01〜10-02 頃) の裁定収集で同じ長さの期間で取り直して判断**: 択 A (leader の数え方を argv 先頭一致に統一、
  写し元を repo 外の雛形 `/work/1/SFC/tanab/dev-wave-jobs/_shared-templates/run-acceptance-gated.sh` 1 本にし、記憶 `acceptance-gate-no-workers-threshold` が指す) は entry 1861 で実施した (D2211 項 4)。
  基準線 (`output/insights/2026-09-26/t2838-gate-argv-unify/README.md` §4、9/21〜9/26 14:38 の約 5.5 日、雛形経由の門番 0 本) は n=139・中央値 174 秒・p90 1,688 秒・30 分以上 11 区間。
  第 37 回の取り直し (D2249 項 3 の指示、一次資料 `output/insights/2026-09-21/acceptance-gate-wait-diagnosis/verbatim/gate_wait_probe.py.md` の code block、sha256 796d1b65…、
  `--since 2026-09-26 --until 2026-09-27T07:36:00+09:00`、約 17 時間) は n=47・中央値 153 秒・p90 567 秒・30 分以上 1 区間 (受入 2 本の実際の競合、2,493 秒)。
  期間の長さが違うので差を雛形の効果とは判定できない (D2260 項 3)。次の裁定収集 (AI) で、9/26 以降の観測が約 5.5 日たまった後に同じ probe を `--since 2026-09-26` と同じ長さの `--until` で走らせ、
  基準線と比べられる形で B を改めて判断する (試すときは待ち・受入 wall・赤率を同時刻対照で比べる)。材料の読み方の案は同 README §5.3。
- [T-2840] (1880)
- [T-2846] (1880)
- [T-2848] (1880)
- [T-2849] (1880)
- [T-2850] (1880)
- [T-2851] (1880)
- [T-2852] (1880)
- [T-2853] (1880)
- [T-2854] **P1・段 1 の一部完了 (D2212 項 2、D2219 項 2) 、単位 11 の材料は済 → 規則 v2 は承認・実装を委任 (D2260 項 1) → 残り = D297 検査器への規則 v2 の実装 wave (AI、Codex author)・実装後の C2' pin 前進の承認・人間の push・campaign で TPC-C を評価する配線**: TPC-C 段 1 (NewOrder / Payment、CCBench 既定比 45% + 43%、
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
  **残り:** (1) C 単独の pin 前進は [T-2858] で承認・実施済み (D2227 項 1) で、C1' / C2' / C3 は C の上の別候補として改めて承認を求める。**D297 の header 差分の受理規則は設計審査を終えた (D2249 項 2 の択 1、D2255、`output/insights/2026-09-26/t2854-d297-header-review/README.md`):** 規則 v2 = header の M 差分に限り、実 compile database の全 entry から `-MG` なしの依存列挙 (旧・新 × TRACE=0/1) で変更 header の consumer を選び、選定 configure 集合 (stock と、consumer を含む production target の protocol の genome 空間。C → C2' では stock + silo 8 + mocc 8 = 17) の各 configure で全 consumer entry の TRACE=0 完全展開と include 活性を GCC 11.4 / 12.3 の別 configure で旧新比較する (実行は計算ノード)。**規則 v2 の承認と実装の委任は D2260 項 1 で決まった (ユーザー裁定、推奨どおり)。** 実装は Codex author の wave (AI) が行い、最初に計算ノードで生死確認を取り、見積りが 1 タスク 2 node 時間以上ならユーザー確認後に投入する。問い 2 = 実装後、改訂後の検査器で C → C2' が GCC 2 版とも pass した結果・実費・pin 波及を示して C2' `40a7f4ac` の pin 前進を承認するか (条件つき事前承認は推さない)。この問い 2 の機会に、si の trace v2 (`patches/instr-si-trace-v2.patch`、[T-2847]、D2252) を `izanagi-trace` 枝へ移して pin を進めるかも併せて諮る (D2260 項 4)。それまで pin は C、C2' は D297 の合格も TPC-C の certified も名乗らない。D780 項 2 は維持し、その比較を trace 完全除去の防壁と呼ばない。択 2 (C2' 限定の例外)・択 3 (header を変えない作り直し)・択 4 (何もしない) は採らない。段 2 も header を変えるので、規則 v2 は段 2 の pin 前進にも適用できる (合格するかは段 2 の実差分で確かめる)。**人間の手番:** branch `izanagi-tpcc-v3-silo-mocc` の push
  (別名なので force 不要、任意の時点で可) と、審査後の裁定を経た pin 前進の承認 (承認後の gitlink・`CCBENCH_FULL_SHA`・`CURRENT_PIN` の同時更新は AI の wave、先例 D2150 / D2184)。
  v3 emitter が pin に入るまで、現 pin の tpcc binary は v2 を出し単位 5 の v3 要求で reject される。
  (2) campaign で TPC-C の候補を評価する配線 (設計 §7.1 の単位に無い): production の build は `ycsb_<protocol>.exe` だけを作り (buildcache)、workload の登録・flag の受け渡しも ycsb だけ。
  critic の reason 説明「YCSB allowlist 外」も TPC-C の v2 reject に合わせる (単位 5 の insight §6・§9)。
  単位 1・2 の実 trace は `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2854-tpcc-ccbench-v3/evidence/traces-2/`、単位 3 の実 trace は
  `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2854-mocc-v3-emitter/evidence/traces-1/`、単位 11 (C2' の silo・mocc) は
  `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2854-unit11-combined/evidence/traces-1/` に zstd で保持。
  段 2 へは段 1 の存在契約をそのまま広げない (削除後の再挿入で版順が存在の遷移と逆になりうる、範囲読みの不在は §4.3 の初期キー一覧、entry 1843 の insight §8)。
  見送り台帳 [T-156] (selector-8b descriptor への set-size 条件) の発火条件は単位 5 で再評価した (pipeline は受理するが corpus の実体は無いので着手しない、単位 5 の insight §8)。
  設計 insight §9 の CCBench 所見 (D2219 項 7): 段 1 で観測できたのは実行時の OrderLine 番号が 0 始まりであることだけ。寿命と範囲読みの所見は [T-2855]、
  si の所見は si を走らせる wave の担当。計算: 検証走・計測・開発の検査を含め 1 タスクの job 合計が 2 node 時間以上になる投入は、見積りを示してユーザー確認後に
  投入する (D2212 項 4、D2219 項 1)。一次資料 `output/insights/2026-09-21/vldb-direction/gap-analysis.md` §10、roadmap §3.1。
- [T-2855] (1880)
- [T-2859] (1880)
- [T-2864] (1880)
- [T-2865] (1880)
- [T-2866] (1880)
- [T-2867] (1880)

