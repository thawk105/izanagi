# [T-148] source_digest のマクロ文脈死角 — 実測・封鎖・変異台帳 (2026-07-28)

対象 = `orchestrator/campaign/source_digest.py` (variant identity の核、D23/D24/D34)。
wave branch = `dev-wave-t148-macro-context`。逐語 = `2026-07-28_t148-review-verbatim/`、
変異台帳 = `2026-07-28_t148-macro-context-mutation-ledger.json`。

## 1. 欠陥 (実測)

digest は対象ソースを **単体** preprocess する (`g++ -E -P -nostdinc -Werror=undef -D...`)。
このため digest 環境と実 TU 環境が乖離し、乖離した文脈に置かれたコードが identity から落ちる。

- **TU 注入マクロ (起票時の型)**: `cc/silo/*_silo.cc:3` が `#define GLOBAL_VALUE_DEFINE` し
  `include/backoff.hh:123-125` が `#ifdef` 参照する。単体 preprocess の素文脈では常に未定義 =
  枝が dead → 枝内編集が digest に不可視 → `src_token` が `"stock"` に化け、stock の certified
  結果と cache バイナリを継承する (規律 2 直撃)。メモリ内 positive control で偽 alias を実証。
- **`-Werror=undef` は防壁にならない**: 捕えるのは `#if MACRO` の未定義参照だけで、
  `#ifdef`/`#ifndef`/`defined()` は rc=0 で素通り (g++-12 実測)。
- **D23 の却下前提が死んでいた**: D23 は「#ifdef 供給完全性 assert は `GLOBAL_VALUE_DEFINE` を
  必須化すると詰む → EVOLVE-BLOCK 内 #ifdef 禁止は hook へ」と却下したが、方針 A (D30/D33) が
  hook の payload 検査を削除した時点でこの受け皿が消えた。builtin definedness 側だけ D34 が
  封鎖し、TU 注入側は D34 の「残る穴」リストにも載らないまま宙に浮いていた。

**段 6 の敵対レビュー 2 本が、同じ「環境乖離」族の別経路を計 8 系統提出し、親が g++-12 実測で
全件 real と確認した。**「実ビルドで live・digest で dead・ガードは受理」の完全な偽 STOCK alias で
ある。レンズ = 全層実効性・テストの歯 (codex) と被覆検証 (claude)。

- **言語標準の乖離**: 実ビルドは `cmake/CompileOptions.cmake` の `CMAKE_CXX_STANDARD 20`、digest は
  `-std` 未指定 (g++-12 既定 = C++17)。`#if __cplusplus >= 202002L` で枝が逆転する。
- **最適化フラグの乖離**: `buildcache` は `-DCMAKE_BUILD_TYPE=Release` で configure し、
  `CompileOptions.cmake` は RELEASE を上書きしないので実 TU には GNU 既定の `-O3 -DNDEBUG` が入る。
  digest 側にこれが無いと `__NO_INLINE__` が「digest で定義済み・実ビルドで未定義」になり、
  その否定形 (`#ifndef __NO_INLINE__`) の枝を digest だけが dead 扱いする。
- **供給集合の乖離**: digest は `Options.cmake` の CACHE 既定を一律 `-D` するが、実 TU に届くのは
  `ccbench_universal_definitions()` の供給表 + `cc/silo/CMakeLists.txt` の `OPTIONS` だけ。
  `DEBUG_MSG` (oze 専用) 等は「digest では定義済み・実 silo TU では未定義」になり `#ifdef` で逆転。
  逆に `Linux` (`ProtocolHelpers.cmake` が Linux 上で無条件付与) は digest 側にだけ無かった。
- **字句の乖離 (4 形)**: (a) g++ は `#/**/ifdef FOO` を条件指令として受理する (実測 rc=0) が、`#` の
  直後に空白しか許さない正規表現は見落とす。(b) 複数行コメントは空白 1 個であって改行ではないので、
  改行を保存すると `#if 1 /*<改行>*/ && defined(X)` の続きが走査から落ちる。(c) 数値の桁区切り
  `1'000` をリテラル開始と誤認すると閉じ引用符を探して以降のソースを飲み込み、その先の指令すべてが
  ガードから消える — **攻撃意図のない正当な C++ で発火する**。(d) 逆に `#if 'A' == 65` の文字定数を
  識別子と誤認して過剰拒否していた。
- **定義状態の乖離**: `#if 0` の中の `#define` は実際には定義されないのに、静的な出現だけで
  「既知マクロ」に数えて未知マクロを洗浄していた。条件指令より後ろの `#define` も同様。
- **名前の組み立てによる迂回 (焦点再レビューで発見)**: `__has_include` を literal で探す検査は、
  `#define IZ_H __has_inc##lude` のようにトークン貼り合わせで名前を組み立てられると素通りする
  (g++ は `__has_include` として評価する。実測)。貼り合わせなしに新しい識別子を作る手段はない
  ので、`#define` 本体の `##` / digraph `%:%:` を止めれば同型の難読化ごと閉じる。
  「`#define` 行集合を HEAD 固定にする」案 (include と同型) は採れない — template patch が骨格の
  `#define BACKOFF_FIXED -1` を足すため現行 campaign が patch 適用中に停止する。
- **指令集合の漏れ**: `#elifdef` / `#elifndef` を条件指令として認識していなかった。
- **不整形入力の fail-open**: 未終端のコメント/リテラルは「残りを空白化して受理」に倒れており、
  identity 核の fails-closed 契約と逆だった。
- **例外型の非対称**: working-tree 側の読取失敗が `OSError` で漏れ、`except RuntimeError` でしか
  受けない呼び手 (`loop` / `pipeline.evaluate` / `buildcache._recheck_src_token`) を貫通して
  campaign 全体を落とし、build dir の破棄も飛ばしていた (HEAD 側 `_git_show` は正規化済みだった)。

## 2. 封鎖 (実装)

1. **二重文脈 digest**: `CONTEXT_MACROS` (現状 `GLOBAL_VALUE_DEFINE`) を「素 + define」の両文脈で
   preprocess し、文脈タグ付き連結を pre-image にする。`compute` / `baseline` / `_trace_pair_diff`
   の 3 経路すべてに適用 — trace 側を素文脈のままにすると「`#ifdef GLOBAL_VALUE_DEFINE` の内側に
   `#if TRACE` を隠す」攻撃が両 TRACE 値とも dead で素通りする (規律 1 の穴)。
2. **digest 環境を実 TU 環境へ寄せる**: `parse_supplied_macros` が CMake **ソース**を静的パースして
   供給集合を取り (configure 出力でないので D23 の鶏卵は起きない)、`_merge_defines` がそれで
   `-D` 集合を絞り `PLATFORM_MACROS` (`Linux`) を足す。`BUILD_FLAGS`
   (`-std=c++20 -O3 -DNDEBUG` = 実ビルドの標準 + Release 既定) を preprocess とマクロ照会の双方へ
   渡す。供給表が取れない/空なら fails-closed。
3. **fails-closed 文脈ガード** (`assert_conditional_macros_covered`、`resolve` が駆動): 条件指令が
   参照する識別子が「実 TU 供給マクロ ∪ 先行しかつ実定義される `#define` ∪ `CONTEXT_MACROS` ∪
   環境マクロ (-dM)」に閉じなければ停止。走査は `_lex_normalize` を通した字句に対して行う —
   行継続とブロックコメントを畳んで**論理行**にし (コメントは空白 1 個であって改行ではない)、
   桁区切り `1'000` はリテラル開始として扱わず、文字定数と文字列中身は識別子にしない。
   `#define` の既知化は「その指令より前に現れ、かつ `-dM` で実際に定義される」ものに限る
   (`#if 0` 内の `#define` と `#undef` 済みは自動的に落ちる)。`#elifdef` / `#elifndef` も指令。
   未終端のコメント/リテラルと raw string は「解釈不能」として停止する (静かに全消しして受理すると
   ガードが恒真化する)。header 探索に依存しない `__has_*` 演算子は受理し、引数は識別子として
   拾わない。identity 経路の読取失敗は `RuntimeError` に正規化する (呼び手の abort 隔離を守る)。
4. **`__has_include` / `__has_include_next` の fails-closed 化**: 条件式の literal 出現と、そこへ
   展開されうる `#define` 本体の両方を停止させ、D34 の known-limitation (computed include) を
   解消した。骨格・stock が不使用なので D34 が却下理由に挙げた skeleton 抽出は要らない。
5. **文脈マクロの縮退防止**: `CONTEXT_MACROS` が供給集合と交差したら停止する。交差すると素文脈が
   define 文脈へ縮退し、反対枝 (`#ifndef` 側) が両文脈とも dead = 死角が再生する。
   2 個以上への増加も停止する (単発文脈列では結合枝 `#if defined(A) && defined(B)` を覆えない)。

## 3. 受入と変異

- 受入全走 = 3131 passed / 18 skipped (本マシン、cwd=repo root、**g++-12 実測**)。実 stock tree
  (pin d706650) で `resolve() == "stock"` を維持 = 過剰拒否ゼロ、trace diff-of-diffs 通過。
- **cxx について正直に**: production の既定 (`source_digest` / `buildcache.DEFAULT_CXX`) は
  `g++-13` だが本マシンに g++-13 は無い。既存の `_require_g13` テストは skip され、本 wave の
  新テストは実在コンパイラ fallback (`_any_cxx`) で g++-12 を使って実走している。中核 positive
  control を skip で空虚に緑にしない ([T-137] の教訓) ための選択で、検査しているのは digest の
  等値/非等値と受理/拒否の**関係**である。ただし「関係は g++ 版に依存しない」とは言い切れない
  (`#elifdef` の認識は std/版に依存する) ため、主張は「同一 cxx 内での関係は不変」に留める。
- 変異 matrix (最終 commit `3210357` に対して本走、`DW-M07`) = M1〜M15 のうち 13 件 KILLED、
  M12 は HANG-KILLED、M4 は PINNED。全件で期待 node と実 node が一致。
  - M4 (`__has_include` 専用 raise の無効化) は受理集合を変えない — 識別子 `__has_include` は
    環境マクロ集合に載らず未知マクロ経路で reject されるため、kill でなく diagnostic sensitivity
    pin 枠 (`DW-M08`)。専用メッセージ (「computed include」) まで assert して pin にした。
  - M12 (未終端コメントの停止を外す) は fails-closed が**無限ループ**へ倒れ、pytest が OOM で
    SIGKILL される。「gate を外すと hang する」= 受理挙動の変化なので kill 側に数える (`DW-M06`)。
- **erratum (初回走行、`DW-M02`/`DW-M04`)**: 最初の本走で M12/M13 が SURVIVED と記録されたが、
  どちらも誤記録だった。M12 は harness が rc=-9 (シグナル死) を「failed 空 → 生存」と数えていた
  (harness を hang 判定つきに是正)。M13 は fixture が `resolve()` 経由で allowlist 検査に先に
  当たる過剰決定 (`DW-M03`) だった (読取を行う `_worktree_defines` の直呼びに変えて単一理由化)。
  初回結果は消さずここに残す。
- テスト側の是正: `__has_include` の fixture は `<atomic>` を使うと `-nostdinc` の preprocess 自体が
  error になり「ガードを外しても別理由で赤」= 過剰決定 (`DW-M03`) だったため、quoted の存在しない
  header へ差し替えた。fake fixture には実 CMake と同じ供給表構造を持たせた (F29 型の「模擬を実測と
  偽る」距離を縮める方向)。

## 4. 残る穴 (正直に)

- **ガードの駆動点は `resolve()`**。legacy `buildcache.build(src_token=None)` は `src_token()` を
  直接呼ぶため、その経路ではガードが build 出口の `_recheck_src_token` まで遅れる。現行 driver
  (S1 / S6 / S8a / loop / p3_s4_loop) は patch 適用中に `resolve()` した token を評価へ渡す。
- **文脈は単一マクロずつ**。`CONTEXT_MACROS` が 2 個以上になったら結合枝
  (`#if defined(A) && defined(B)`) の被覆に組合せ文脈が要る (機械的に停止する)。
- **供給集合は CMake ソースの静的パース**。CMake の書き方が変われば追随できず、そのときは
  fails-closed で止まる (沈黙しない) が、パース対象の構文は暗黙の契約である。
- **環境の一致は `BUILD_FLAGS` の範囲まで**。実ビルドが将来別のフラグ (`-march` 等) を足せば、
  そのフラグが変える definedness で再び乖離しうる。現在は「環境照会に現れない予約識別子
  (`__NO_INLINE__` 型) の definedness テストは停止側に倒す」ことで残余を受けている。
- **`#undef` と枝の意味解析はしていない**。定義状態は `-dM` の実照会に委ねており、静的には
  「先行位置」しか見ていない。`-dM` が拾えない形 (マクロ引数依存など) は射程外。
- **ガードは working-tree 側だけに掛かる**。`baseline()` が読む pin 側の内容は検査しない。
  pin が固定である限り実害はない (現 pin d706650 の実ソースはガードを通ることを確認済み) が、
  pin を前進させるときは新 pin のソースがガードを通るか先に確かめる必要がある。
- **`__has_*` 演算子の allowlist は実質ゲートになっていない**。`KNOWN_HAS_OPERATORS` に無い
  `__has_*(...)` も式から落ちる。live 枝なら preprocess エラーで fails-closed、dead 枝なら実 TU も
  dead なので実害はないが、allowlist が効いているとは書けない。
- **`#if TRACE` の外に常駐する検証専用メタデータ**は従来どおり diff-of-diffs では判定不能
  (auditor / 人間レビュー領域、D30/phase3.md)。

## 5. 出口 (次の一手の材料)

- **[T-157] 新規 (P1、本 wave scope 外)**: `p3_s4_loop._resolve_duplicate` が `with applied(...)` の
  外で、しかも `ccbench_dir` 引数なしで `source_digest.resolve()` を呼ぶため、patch を revert した
  共有 tree の **stock** id を引く (`p3_s4_loop_sort` / `p3_s4_loop_trigger_gating` も同型)。
  重複提案の解決が別 variant の WAL を参照し、whiteboard・trigger provenance・checkpoint・critic
  digest に誤った variant 参照が永続化する。段 6 レビュー B の must-fix 5 (親が実コードで確認)。
- **[T-149] への追記材料**: 編集面の独立 hard-code に、本 wave が足した供給集合パーサの
  `_PROTOCOL_CMAKE` (protocol → CMakeLists パス) も同族として数えられる。
