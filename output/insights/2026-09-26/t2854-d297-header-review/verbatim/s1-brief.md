# [T-2854] D297 header 差分受理規則の設計審査 — 段 1 brief (親、2026-09-26 22:20 JST)

wave 木 = /work/1/SFC/tanab/izanagi/.claude/worktrees/t2854-d297-header-review (branch worktree-t2854-d297-header-review、基点 = local main 6c3913bc5、開始 gate rc=0)。

- **研究前進:** 論文の TPC-C 段 1 (silo・mocc) の直列化可能性認定 (gap-analysis §10 の P1) は C2' `40a7f4ac` の pin 前進待ちで止まり、その前提が「D297 が header 差分を受理できること」。本 wave の完了判定 = 審査結果 (規則案 v2 の採否・残る穴・費用) と承認事項案 (実装の委任、C2' pin 前進) を insight・decisions fragment に記録すること。
- **scope:** 設計審査だけ (docs-only)。検査器の実装・pin 前進・branch push・計算投入はしない。成果物 = insight 1 本、decisions / worklog fragment。
- **確定済み裁定:** D2249 項 2 (択 1 の審査のみ。審査の承認・実装の委任・C2' pin 前進の承認は結果を見て別裁定。それまで pin は C、C2' は D297 合格も TPC-C certified も名乗らない)、D297、D780 項 1〜3、D774、D2207 (include 規則を緩めない)、D2225 決定 6、D2244 項 4・5、D2150 (iii) (D297 の複数 compiler は GCC 11.4 / 12.3 で足りるとした先例)。
- **不変条件:** 規律 1・2 を緩めない。D780 項 2 を維持し、規則の比較を trace 完全除去の防壁と呼ばない (D780 項 1 の文言「必要条件の一つ」)。既存の拒否 (A/D/R/C、mode 変更、非 C/C++、.cc の include 行不一致、比較 0 件) は受理側へ動かさない。仮想リスク向けの gate・台帳・一般化を足さない。

## 親の provisional 裁定 (攻撃対象)

- (P1) **適用範囲:** header 拡張子の M 差分だけに新規則を足す。.cc 差分は現行の単体比較 (16 文脈・mocc の trace.hh 1 行例外) のまま。CMake 等の非 C/C++ 差分は現行どおり拒否し、その結果として旧新の compile database が root 以外で一致することを検査器自身が照合する。
- (P2) **consumer TU の母集合:** 実 CMake configure の compile database の全 entry を母集合とし、compiler の依存出力 (`-M -MG`) が旧・新 × TRACE=0/1 のいずれかで変更 header を含む entry を consumer とする。直接 include の正規表現 (単位 11 probe) は間接 include を拾わないので使わない。変更 header ごとに consumer 0 件なら拒否。
- (P3) **TU ごとの文脈:** consumer entry の実 compile argv (TRACE=0 固定)。genome 空間を持つ protocol は production と同じく genome ごとに configure し直した compile database を文脈にする (`buildcache._v2_commands` は `genome.cmake_defines()` を configure へ渡す)。現行の 16 文脈 (silo genome 8 × GLOBAL_VALUE_DEFINE 有無) は TU 比較には使わない (TU は自分で GLOBAL_VALUE_DEFINE を定義する)。
- (P4) **比較:** entry × 文脈 × compiler (GCC 11.4 / 12.3) ごとに、完全展開 (`-E -P -dD`) と include 活性 (`-E` の line marker の入退場 file 列) が root 正規化後に byte 一致。期待件数と実件数の一致を要求 (比較 0 件の緑を作らない)。
- (P5) **実行場所:** 全 TU 前処理は build 時生成 header (masstree の `config.h`、`masstree_build` target) を要するので build 段を含み、login では走らない。検査器は計算ノード job の中で走る。
- (P6) **保証名:** 「選定した build 文脈の consumer TU における TRACE=0 完全展開と include 活性の同一性」。D780 項 1 の文言を継承。link object・trace symbol / data・build receipt は結ばず、admission build の全 TU を覆うとは主張しない (D780 項 2 の別防壁ではない)。D774 の限界は据え置き。
- (P7) **実装時の変異 (事前登録の案):** header の TRACE=0 側の値変更、header 内 include の `#if TRACE` への移動、TRACE=0 側 `#define` の変更、`#line` 削除 (H-line 先例)、間接 consumer だけが読む header の変更 (直接 include 列挙へ劣化させると生存)、consumer 0 件、期待件数不一致、CMake 変更。
- (P8) **承認事項案:** (a) 規則案 v2 の承認、(b) 実装の委任 (Codex author 1 wave + 変異 + 計算 job、見積り付き)、(c) C2' pin 前進は実装済み検査器の C → C2' pass (GCC 2 版) を見て別に承認する (条件つき事前承認は推さない)。

## 前提の実測 (親、login、job dir `evidence/`)

- C と C2' を CCBench の一時 worktree に取り出し、`cmake -S … -DCMAKE_BUILD_TYPE=Release -DCMAKE_EXPORT_COMPILE_COMMANDS=ON -DCMAKE_PREFIX_PATH=/work/1/SFC/tanab/izanagi-a2-deps` (両方 rc=0)。
- compile database は両側 135 entry (78 file)。source / build root を正規化すると両側一致。
- 全 135 entry を実 argv + `-M -MG -DTRACE={0,1}` で依存列挙 (error 0)。変更 header (include/tpcc.hh・include/trace.hh) を含む entry は両側とも **21 entry / 12 file** で、単位 11 の直接 include 正規表現の 21 entry と完全一致 (この構成では間接だけの consumer は 0)。mocc/transaction.cc は TRACE=1 でだけ trace.hh を読む。C2' では tpcc_*.cc 9 本が TRACE=1 で trace.hh も読む (C では読まない)。
- 全 TU の前処理 (`-E`) は login では masstree の `config.h` 不在で rc=1 (build 時生成、`cmake/ThirdParty.cmake` の `masstree_build`)。GCC 11.4 の stock 構成での 21 entry 一致は単位 11 の計算 1 走が既に示した (insight §3)。GCC 12.3・genome 文脈での正例は未実測。
- 模擬と実の差: 上は stock (genome 無指定) configure 1 構成で、production の genome 別 configure・`-fmacro-prefix-map`・`CCBENCH_TRACE` の経路は通していない。

## 並列分割

段 2 = plan 1 本 (read-only)。段 3 = 敵対相談 2 本 (A: 正しさ境界・受理集合・D780/D774 との境界、B: 実効性と過剰・削除・費用・既存 probe 流用)。実装しない裁定なら 4→7→8→9。記録は docs-only で一次資料を再抽出するので段 7 で read-only レビュー 1 本を残す。
