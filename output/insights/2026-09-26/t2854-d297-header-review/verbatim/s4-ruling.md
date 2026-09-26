# [T-2854] D297 header 審査 — 段 4 裁定 (親、2026-09-26)

入力: brief `s1-brief.md`、plan `out/s2-plan.md`、相談 A (正しさ境界、`--lane sol`) `out/s3-consult-A.md`、相談 B (実効性と過剰・削除、`--lane luna`) `out/s3-consult-B.md`。
全子 codex read-only・medium、`check_codex_output.py` rc=0。裁定 inbox の再走査 (段 4 直前): wave 開始後の新着なし。local main は wave 中に 6c3913bc5 → 1f169cbbd (T-2273 の insight と fold のみ、本審査に影響なし)。

## §1 所見の裁定

| # | 所見 | 判定 | 採否・処置 |
|---|---|---|---|
| A1 | `-MG` は未生成 header の先で依存探索を止め、間接 consumer を落として緑にしうる | real (must-fix) | 採用。規則 v2 R3: 生成物 (masstree `config.h`) を用意した後、選定 configure の**全 entry**の依存列挙を `-MG` なしで成功させる。1 entry でも失敗・欠落 header があれば拒否 |
| A2 / B1 | genome configure の「その protocol の entry だけ」を文脈にすると、同じ configure で実際に変わった他 protocol の argv (実測: `CCBENCH_KEY_SORT` が d2pl・ermia・mocc・si・ss2pl の 60 entry に効く) を捨てるのに「production 文脈」と名乗る | real (must-fix) | 採用。R4: 選定した各 configure では**その configure の全 consumer entry**を比べる (同一 (entry, argv) は 1 回に集約)。保証名に「選定 configure 集合」を明記し、production の全文脈とは書かない |
| B2 | 64 genome 一律は研究前進に対し過大 | real (should) | 採用。R4 の選定集合を stock + 「変更 header を読む production target の protocol の genome 空間」に限る (C → C2' では silo 8・mocc 8、configure 17)。tictoc・cicada の genome は C2' では主張しない |
| A3 | compile database の母集合は build の母集合ではない (opt-in target 等) | real (should) | 採用。保証の主語を「選定 configure の compile database に載る entry」に統一し、database 外を残る穴に書く |
| A4 | TRACE の実効値は argv への追加だけでは確定しない | real (should) | 採用。R6: 比較 (TRACE=0) と依存照会 (TRACE=1) のそれぞれで前処理の macro 状態から TRACE の実効値を確認し、確認できない entry・不透明 argv (`@file`・`-Wp,`) は拒否 |
| A5 | 正規化で消えるものを保証名で限定 | real (should、一部) | 採用。保証は完全展開と include 活性 (入退場 file 列) に限り、line marker 全体・診断位置の同一性は名乗らない。root 置換は照合済み prefix の境界付きだけ |
| A6 | D780 項 2 の別防壁を単独設計した | refuted | 不成立 (相談 A 自身も不成立)。裁定文に「compile database は選定 source 比較の文脈入力であり、admission build・receipt との対応を証明しない」を置く |
| A7 | .cc 既存拒否・mocc 例外・承認順序を緩める | refuted | 不成立。「pass」は改訂後の検査器の新しい結果にだけ使い、単位 11 の既存証拠を遡って D297 pass と呼ばない、を明記 |
| A8 | brief の実測を一般則にした | refuted | 不成立。数値には「stock・当該 configure」の条件を添えたまま使う |
| B3 | P7 の変異に再演・既存拒否の確認が混じる | real (should) | 採用。新分岐が誤って緑にする形だけを変異にし、既存拒否 (CMake・.cc include 行・件数) は回帰 test で維持。H-line は実 CCBench の代表負例として 1 回 |
| B4 | 承認事項に実装形 (schema field・CLI 引数) まで入れすぎ | real (should) | 採用。承認対象は受理条件・保証名・選定規則・費用の測り方に限る。report は旧 `files` の意味を保ち、版上げの要否は実装時に決める |
| B5 | 「全 TU 前処理には build が必要」は言い過ぎ | real (should) | 採用。「選定 entry の前処理に必要な生成物 (masstree `config.h`、`masstree_build` target) を用意する段が要り、login では行えない (build は hook が拒否)」に改める |
| B6 | 提示は 2 段・2 問で足りる | real (nit) | 採用。今回の問い = 規則 v2 の承認 + 実装の委任 (規則だけ承認し実装を留保する回答も受けられる形)。C2' の pin 前進は実装後の C → C2' pass・実費・pin 波及を示してから別に問う |
| B7〜B10 | 全 entry 完全比較・probe 無修正流用・GCC 2 版等の削除・段 2 に効かない | refuted | 不成立 (相談 B 自身も不成立)。段 2 は「適用できる」と書き「合格する」とは書かない |

## §2 規則案 v2 (審査結果として記録する設計)

- **R1 適用範囲:** raw diff の M・mode 不変の header 拡張子 path にだけ新分岐を足す。A/D/R/C・mode 変更・非 C/C++ (CMake を含む) の拒否、.cc の単体比較 (16 文脈・mocc の trace.hh 1 行例外、D2207) は不変。header と .cc が同居すれば両検査の積。
- **R2 source と生成物:** 旧・新を worktree で取り出し tree を照合 (`git archive` は export-ignore で cc/oze を落とす)。FetchContent の第三者 source は両側同一の固定 source。選定 configure ごとに前処理に要る生成物を用意する (実行場所は計算ノード)。
- **R3 consumer:** 選定 configure の compile database の全 entry (target・argv を鍵) を母集合とし、`-MG` なしの依存列挙を旧・新 × TRACE=0/1 で全件成功させ、変更 header を 1 度でも読む entry の和集合を consumer とする。変更 header ごとに選定集合全体で consumer 0 件なら拒否。旧新の database は root 正規化後に entry 集合・argv が一致しなければ拒否。
- **R4 文脈 (選定 configure 集合):** stock configure (production と同じ Release・sanitizer OFF・`CCBENCH_TRACE=0`) と、変更 header の consumer を含む production target (現行 buildcache の `ycsb_<protocol>.exe`) の protocol が genome 空間を持つとき、その空間の全 genome の configure。各 configure の**全 consumer entry**を比べ、同一 (entry, argv) は集約。選定集合は report に列挙する。
- **R5 比較:** 各 (compiler, configure, entry) で旧・新の完全展開 (`-E -P -dD`) と include 活性 (`-E` の入退場 file 列) を root 正規化後に byte 比較。compiler は GCC 11.4 / 12.3 を**それぞれ別 configure・別 database**で (argv[0] の差し替えはしない)。比較の予定集合を先に固定し、実行済み集合と厳密一致を要求 (0 件・欠落は拒否)。`__DATE__` 等が混入し再現条件を固定できなければ拒否。
- **R6 TRACE の実効値:** 比較時 TRACE=0・依存照会時 TRACE=1 を前処理の macro 状態で確認。不透明 argv は拒否。
- **R7 保証名:** 「選定 configure 集合の compile database に載る変更 header consumer entry における、TRACE=0 完全展開と include 活性の同一性」。D780 項 1 の文言 (D297 の保証の証明であり、trace 完全除去には必要条件の一つ) を継承。compile database は文脈入力であって admission build・receipt との対応を証明しない。D780 項 2 の別防壁ではなく、D774 の限界は据え置く。
- **残る穴 (明記):** 選定 configure 外の文脈 (他 genome 空間・Debug・opt-in target・将来の production option)、database 外の TU、GCC 以外の compiler、admission build の全 TU・link object・trace symbol / data・receipt との未結合 (D780 項 2)。TPC-C の campaign 配線 (T-2854 残り (2)) で tpcc target が production に入るときは R4 により silo・mocc の tpcc entry も genome 文脈に入る (同じ選定規則で自動的に広がる)。

## §3 実装 wave へ渡す変異の事前登録案 (本 wave では登録・実行しない)

新分岐が誤って緑にする形だけ (相談 B 所見 3):
1. 間接 consumer: 直接 include を持たず別 header 経由でだけ変更 header を読む TU (合成 fixture)。直接 include 列挙へ劣化させた実装を殺す。
2. header の TRACE=0 側の値変更 (`#if !TRACE` 内を含む) → 完全展開不一致。
3. header 内の必須 include を `#if TRACE` 内へ移す → include 活性不一致。
4. 生成 header 不在で依存探索が途中停止する形 (A1) → 依存列挙失敗で拒否。`-MG` へ劣化させた実装を殺す。
5. 選定 configure で他 protocol の consumer の argv だけが変わる形 (A2) → その entry を比較対象から外した実装を殺す (合成 fixture)。
6. consumer 0 件、比較予定集合から 1 件を落とす → 拒否。
7. 実 CCBench の代表負例 H-line (`tpcc.hh` の `#line 56` 削除) を新分岐経由で 1 回。
既存拒否 (CMake 差分・.cc include 行・件数・A/D/R/C) は回帰 test として維持し、変異にしない。

## §4 承認事項案 (ユーザー裁定へ出す形)

- **問い 1 (今):** 規則 v2 (§2 の R1〜R7 と残る穴) を承認し、その実装を Codex author の wave に委任するか。答え方: (a) 承認 + 委任 (推奨) / (b) 規則だけ承認し実装は留保 / (c) 却下 (現行 D297 のまま、C2' は拒否のまま、段 2 も同じ諮問が再び要る)。
  委任の範囲: 検査器の新分岐・合成 fixture・§3 の変異・実 CCBench の C → C2' の実走 (GCC 2 版)。費用は未実測なので上限を書かない — 最初に計算ノードで 1 configure + 生成物 + 前処理の生死確認 (DW-G01) を取り、選定 17 configure × 2 compiler × 旧新の見積りを実測単価で出す。1 タスクの job 合計が 2 node 時間以上ならユーザー確認後に投入 (D2212 項 4)。
- **問い 2 (実装後):** C2' `40a7f4ac` の pin 前進を承認するか。前提 = 改訂後の検査器で C → C2' が GCC 11.4 / 12.3 とも pass、実費、pin 前進の波及 (D2150 / D2184 の先例どおり gitlink・`CCBENCH_FULL_SHA`・`CURRENT_PIN` の同時更新) を示すこと。条件つき事前承認は推さない (未実測の GCC 12.3・genome 文脈の正例を合格前に引き受けることになる)。
- それまで pin は C のまま。C2' は D297 の合格も TPC-C の certified も名乗らない (D2244 項 4)。branch `izanagi-tpcc-v3-silo-mocc` の push は人間の手番 (任意の時点)。

## §5 段の遷移

本 wave は「実装しない」裁定なので 4 → 7 → 8 → 9。実装面の差分ゼロのため変異 matrix は免除 (DW-S04)。受入全走は免除しない。記録は一次資料 (検査器・buildcache・実測) から事実を再抽出する docs-only なので、段 7 で独立 read-only レビュー 1 本を残す (DW-C00)。
