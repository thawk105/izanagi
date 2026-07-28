# [T-148] 段 6 焦点再レビュー (claude opus、read-only) — 逐語

対象 = fix commit `d2da2c6` (実装 `cc01c49` + 段 6 fix round)。判定は静的検査と g++-12 実測
(stdin パイプのみ、ファイル書込なし)。以下は返答の逐語。親の裁定は本 wave の worklog エントリと
`../2026-07-28_t148-macro-context.md` を正本とする。

---

## 1. 所見ごとの対応表

| ID | 判定 | 根拠 |
|---|---|---|
| B-mf1 | **closed** | `parse_supplied_macros` が実 `cmake/Options.cmake` の `ccbench_universal_definitions()` (ADD_ANALYSIS/BACK_OFF/KEY_SIZE/MASSTREE_USE/VAL_SIZE/TRACE) + `cc/silo/CMakeLists.txt` の OPTIONS 8 件を正しく抽出 (実行確認)。`DEBUG_MSG` は除外、`Linux=1` は `PLATFORM_MACROS` で追加、`-std=c++20` は `BUILD_FLAGS` 経由で `_cpp_normalize` と `_dump_macros` の双方へ。空値 `INSERT_*_DELAY_MS` が `parse_options_defaults` で落ちる挙動は実 `ccbench_normalize_options` の empty-skip と一致 |
| B-mf2 | **closed** | g++-12 実測で `#/**/ifdef` は指令。`_lex_normalize` 通過後 `#  ifdef` になり `_COND_DIRECTIVE_RE` が捕捉 |
| B-mf3 | **partial — 反例あり (must-fix)** | `#define` 本体の literal 検査は `##` 貼り合わせを見ない。`#define IZ_H __has_inc##lude` + `#if IZ_H("tsc.hh")` は g++-12 が実際に `__has_include` として評価する (実測: `-nostdinc` で 0、既定 path で 1) のに、ガードは `IZ_H` を先行 `#define` かつ `-dM` live で既知扱いし受理する |
| B-mf4 | **closed** | `#if 'A' == 65` は `_lex_normalize` が潰し識別子 0 個 → 受理。残余は nit 1 |
| B-mf5 | **not-addressed (裁定どおり)** | fix diff は `p3_s4_loop*.py` を触っていない。[T-157] として起票済み |
| B-s1 | **closed** | モジュール docstring が「駆動点は resolve()、legacy `buildcache.build(src_token=None)` は `src_token()` 直呼びでガードが `_recheck_src_token` まで遅れる」と明記 |
| B-s2 | **closed** | fixture が quoted の不在 header に変わり過剰決定が消えた。専用メッセージ「computed include」まで assert。第 2 段 (マクロ本体隠し) はガードを外すと緑になる = 歯あり |
| B-s3 | **closed** | handoff に highkey/norw/lockskip/early-unlock/permutation-erase/swap を列挙し訂正 |
| A-mf1 | **closed (GCC 準拠を実測確認)** | ブロックコメントを改行なしで畳む。`#if 1 /*<改行>*/ && defined(X)` は g++-12 で 1 指令 (実測) |
| A-mf2 | **closed** | 既知化が「先行位置 ∩ `-dM` 実定義」の二重条件。`#if 0` 内 `#define` は入らない |
| A-mf3 | **closed (報告された反例に対して)** | 桁区切り分岐で `1'000` 後の指令が飲まれない。残余は nit 1 |
| A-mf4 | **closed** | `_environment_macros` が `BUILD_FLAGS` 込みで照会。実測で digest 環境 = `NDEBUG` 定義済 / `__OPTIMIZE__` 定義済 / `__NO_INLINE__` 未定義 = Release TU と一致 |
| A-s1 | **closed** | `_COND_DIRECTIVE_RE` に `elifdef|elifndef` |
| A-s2 | **closed** | `KNOWN_HAS_OPERATORS` + `_HAS_OP_CALL_RE`。残余は nit 3 |
| A-s3 | **closed** | 未終端コメント/リテラル/raw string で RuntimeError |
| A-s4 | **closed** | `_read` が RuntimeError 化。orchestrator 全体を grep した結果、`source_digest.*` の呼び手 12 箇所はすべて `except RuntimeError` かそのまま伝播で、`except OSError` に依存する呼び手は 1 件も無い |
| A-s5 | **closed** | 新規 3 テストが A の反例 4 形・不整形 3 形・正例 4 形を被覆 |
| A-n1 | **closed** | `_lex_normalize` に改名、docstring も「翻訳フェーズ 2-3 の近似」 |
| A-n3 | **closed** | `len(CONTEXT_MACROS) > 1` で機械停止。全 digest 入口が必ず通る。供給集合との衝突検査も追加 |
| A-n2 | **not-addressed (裁定どおり)** | insight「残る穴」に記載あり |
| A-n5 | **not-addressed、かつ記録漏れ** | ガードは working-tree 側のみ、`baseline()` の pin 側内容は無検査。現 pin の実ソースはガードを通るので実害ゼロ、文書のみの穴 |
| A-P3 | **closed** | insight に「全走は g++-12 実測」「本マシンに g++-13 なし」「`_any_cxx` fallback」を明記 |

## 2. fix が新たに壊したものの検査

**過剰拒否の新規混入 — 1 件 (nit 級、fails-closed 方向)**
桁区切り判定は「直前が英数字/`_`」だけを見るため、接頭辞つき文字リテラル `L'…'` / `u'…'` /
`U'…'` / `u8'…'` を桁区切りと誤認する。中身が `"` か `/` の場合 (`u'"'`、`L'/'`) は続きを未終端
リテラルと判定して正当な C++ で RuntimeError になる (実行確認)。fix 前は字句解析自体が無かった
ので新規。実 `include/backoff.hh` / `cc/silo/transaction.cc` および全 patch 追加行にこの形は無く、
実ソースはガードを通過することを実行確認済み。

**ブロックコメントの改行畳み込み — 経路を開いていない (GCC 準拠を実測で確認)**
`int x; /*<改行>*/ #ifdef SECRET` → 畳み込みで行頭 `#` でなくなりガードは指令と見ない。g++-12 も
指令と見ない (テキストとして出力し `#else without #if` で rc≠0) → `_cpp_normalize` が fails-closed。
しかも `#ifdef` 文字列自体が preprocess 出力 = digest に載る。行頭の `/*<改行>*/ #ifdef X` は
g++ が指令として扱い、畳み込み後も行頭なのでガードも捕捉。`#ifdef A /*<改行>*/ #ifdef SECRET` は
g++ が警告 + エラー、ガードは畳んだ 1 行で両方の識別子を拾う (過剰包含だが安全側)。
結論: 後続指令が走査から漏れる経路は作られていない。

**`-DNDEBUG` の追加 — 実 TU と一致**
計測経路の cmake configure は全て `-DCMAKE_BUILD_TYPE=Release`。`CompileOptions.cmake` は
`CMAKE_CXX_FLAGS_RELEASE` を上書きしないので実 TU に GNU 既定 `-O3 -DNDEBUG` が入る。digest 側の
`-dM` 実測も一致し、`#ifdef NDEBUG` は digest でも Release 枝を取る。非 Release は ccbench の
devcontainer script のみで計測経路外。残余の乖離方向 (`_REENTRANT` 等) は「未知マクロ → 停止」で
fails-closed 側に倒れる。

**`_dump_macros` を `defs_at` 非空時だけ呼ぶ最適化 — 判定不変**
`defs_at` が空なら派生集合も空なので `known` は同一。エラー検出面でも `_environment_macros` が
`_dump_macros("")` を無条件に呼び、preprocess 不能な入力は `_cpp_normalize` (`-Werror=undef`) が
捕えるため、fails-closed の穴は開いていない (実行確認)。

**`_read` の RuntimeError 化 — 呼び手の破壊なし**
`except OSError` / `FileNotFoundError` に依存する呼び手はゼロ。逆に `pipeline.evaluate` / `loop` /
`_recheck_src_token` の variant 単位 abort 隔離が実際に効くようになった。

## 3. 総括

**NO-GO** (must-fix 1 件)。他 20 所見は裁定どおり closed / not-addressed で、fix による回帰・
新規の偽 STOCK 経路は検出されなかった。

### must-fix
`__has_include` のマクロ隠蔽封鎖 (B-mf3) が `##` 貼り合わせで迂回できる。反例 (実行確認済み。
ガードが受理、g++ は `__has_include` として評価):

```cpp
#define IZ_H __has_inc##lude
#if IZ_H("tsc.hh")
    double now_backoff = 42;              // 実ビルドはこちら (header 発見 = 1)
#else
    double now_backoff = Backoff_.load(std::memory_order_acquire);  // digest はこちら = stock 逐語
#endif
```

到達性: 方針 A / D33 で hook の payload テキスト検査は削除済みのため、EVOLVE-BLOCK hole 内の
`#define` を機械的に止めるのはこのガードだけ。`assert_includes_match_head` も
`assert_trace_diff_matches_head` も発火しない (指令は preprocess 出力から消える)。
成果物影響: 変更コードの `src_token` が `"stock"` に化け、stock の `variant_id`/`cache_key` を
継承 → stock certified record の skip・stock cache バイナリの返却 (= 変更が一度もコンパイルされない
まま certified 記録される)。規律2 直撃。
封鎖案: `assert_includes_match_head` と同型に、EVOLVE_BLOCK_SOURCES 内の `#define` 行集合が HEAD
baseline と一致しなければ停止する (coder の hole は straight-line code のみでマクロ定義は元々
禁止規約)。副次的に `##` 貼り合わせ・将来の同型難読化もまとめて閉じる。

### nit (must-fix にしない)
- nit 1: 桁区切り判定が接頭辞つき文字リテラル (`u'"'` 等) を誤解析して正当入力で停止しうる。
  fails-closed 方向で実ソース・全 patch に該当形なし。
- nit 2: A-n5 (pin 側内容は無検査) が insight の「残る穴」に未記載。裁定は「記録のみ」なので
  記録の追加だけで閉じる。
- nit 3: `_HAS_OP_CALL_RE` は `KNOWN_HAS_OPERATORS` 非掲載の `__has_*(...)` も式から落とすため、
  allowlist が実質ゲートになっていない。live 枝なら preprocess エラーで fails-closed、dead 枝なら
  実 TU も dead なので実害なし。

---

## 親の裁定 (2026-07-28)

- **must-fix = real、ただし提案された封鎖案は採らない。** 「`#define` 行集合を HEAD 固定」は
  template patch が骨格の `#define BACKOFF_FIXED -1` を足すため、現行 campaign が patch 適用中に
  停止する (レビューの「マクロ定義は元々禁止規約」は coder の hole 内の話で、patch の骨格には
  当たらない)。採ったのは**トークン貼り合わせ (`##` / `%:%:`) の停止** — 貼り合わせなしに新しい
  識別子を作る手段はないので、同じ締め効果を patch と両立して得られる。commit `3210357`。
- **nit 1 = real、修正した** (判定を「直前のトークンが数字で始まるか」へ)。正当な C++ を止めるのは
  受理集合の不当な縮小であり、fails-closed 方向でも放置しない。
- **nit 2 = 採用**、insight の「残る穴」に pin 側無検査を追記した。
- **nit 3 = 記録のみ** (実害なし)。insight の「残る穴」に「allowlist は実質ゲートでない」と明記。
