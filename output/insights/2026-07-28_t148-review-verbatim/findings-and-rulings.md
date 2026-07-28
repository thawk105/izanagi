# [T-148] 段 6 所見一覧 (焦点再レビュー用。closed / partial / regressed を判定してもらう対象)

fix commit = `d2da2c6` (実装 = `cc01c49` + 本 fix)。branch = `dev-wave-t148-macro-context`。

## レビュー B (codex、レンズ = 全層実効性・テストの歯) の所見

| # | 所見 | 親の裁定 | fix の主張 |
|---|---|---|---|
| B-mf1 | digest の preprocess 環境が実 TU と乖離 (`-std` 未指定 / Options CACHE 全体を一律 -D) | real・scope 内 | `BUILD_FLAGS = -std=c++20 -O3 -DNDEBUG`、`parse_supplied_macros` で供給集合に絞り `PLATFORM_MACROS` (`Linux`) を追加 |
| B-mf2 | `#/**/ifdef` 見落とし + 後方 `#define` を既知扱い | real・scope 内 | `_lex_normalize` + 位置つき既知集合 |
| B-mf3 | `#define IZ_HAS __has_include(...)` 経由の迂回 | real・scope 内 | `#define` 本体も検査、`__has_include_next` も対象 |
| B-mf4 | `#if 'A' == 65` の文字定数を未知マクロ扱い (過剰拒否) | real・scope 内 | リテラル中身除去 |
| B-mf5 | `p3_s4_loop._resolve_duplicate` が `with applied()` の外・`ccbench_dir` なしで resolve → stock id | real・**scope 外** | 未実装。[T-157] 起票 + 裁定パッケージ |
| B-s1 | docstring の「resolve に一本化済み」は過大 | 採用 | legacy `build()` 経路を明記 |
| B-s2 | `__has_include` fixture が `<atomic>` + `-nostdinc` で過剰決定 / M4 が pin にならない | 採用 | quoted の不在 header へ差替え、専用メッセージ (「computed include」) を assert |
| B-s3 | 裸マクロ patch は trigger 以外にも存在 (親の事実誤認) | 採用 | handoff/insight で訂正 (いずれも CMake 直 driver で resolve 非経由は不変) |

## レビュー A (claude、レンズ = 被覆検証) の所見

| # | 所見 | 親の裁定 | fix の主張 |
|---|---|---|---|
| A-mf1 | 複数行コメント内の改行保存で条件式の続きが走査から落ちる | real (再現) | ブロックコメントは改行を残さず論理行を畳む |
| A-mf2 | `#if 0` 内の `#define` が未知マクロを既知に洗浄 | real (再現) | 既知化を「先行位置 ∩ `-dM` 実定義」に |
| A-mf3 | 桁区切り `1'000` をリテラル開始と誤認し以降の指令を飲み込む | real (再現) | 直前が英数字なら桁区切りとして扱う |
| A-mf4 | builtin 照会に `-O3 -DNDEBUG` がなく `__NO_INLINE__` の definedness が反転 | real (再現) | `BUILD_FLAGS` を照会と preprocess の双方へ。加えて環境照会に現れない予約識別子は停止側 |
| A-s1 | `#elifdef` / `#elifndef` 未認識 | real | 指令正規表現に追加 |
| A-s2 | `__has_builtin` / `__has_attribute` / `__has_cpp_attribute` の過剰拒否 | real | `KNOWN_HAS_OPERATORS` を受理、引数は式から落とす |
| A-s3 | 不整形入力 (未終端コメント/リテラル) が静かに全消し = fails-closed でない | real | 未終端と raw string で停止 |
| A-s4 | protocol CMakeLists 不在が `OSError` で漏れ、呼び手の `except RuntimeError` を貫通 | real | `_read` を RuntimeError に正規化 |
| A-s5 | 新テストの被覆が docstring の一般命題より狭い | 採用 | A の反例 3 形 + 未終端 3 形 + 正例を追加 |
| A-n1 | `_phase12` の名前と docstring の不一致 | 採用 | `_lex_normalize` に改名し docstring を phase 2-3 に |
| A-n3 | `CONTEXT_MACROS` 2 個以上の機械強制なし | 採用 | `len > 1` で停止 |
| A-n2 / A-n5 | `#undef` 未モデル / pin 側内容は未検査 | 記録のみ (alias 源にならない) | 未実装 (insight の「残る穴」に記載) |
| A-P3 指摘 | 本マシンに g++-13 が無く production 既定は g++-13 = 親の全走は g++-12 の証拠 | real | insight と worklog に明記 (受入は g++-12 実測と表記) |

## 変異 matrix (fix commit d2da2c6 に対して本走、DW-M07)

M1〜M13: 11 KILLED + M12 HANG-KILLED (gate を外すと無限ループ = fails-closed が hang へ倒れる証拠、
DW-M06) + M4 PINNED (受理集合不変の診断 pin、DW-M08)。全件で期待 node と実 node が一致。
初回走行では harness が rc=-9 (OOM SIGKILL) を「SURVIVED」と誤記録し、M13 は allowlist 検査に
mask されていた (過剰決定) — 両方を是正した上での結果である (erratum として記録)。

## 受入

全走 3131 passed / 18 skipped (cwd=repo root、g++-12 実測)。実 stock tree (pin d706650) で
`resolve() == "stock"` 維持。`tools/check_docs.py` 緑、repo scan invariant 緑。
