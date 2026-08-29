# [T-2018] 段 1 — 親の実測 (逐語)

基準: worktree `dev-wave-t2018-condition-meaning-gate`、base commit `8d014c748` (local main)。
実測はすべて repo の外 (`$CLAUDE_JOB_DIR/tmp`) に置いた probe で行い、repo へは 1 byte も書いていない。

---

## 実測 1 — F718 の符号化を実 compiler で再現できる (生死実験、DW-G01)

`patches/silo-backoff-fixed.patch` の追加行から合成枝 (`#if BACKOFF_FIXED >= 0` の直後の 1 行、
909 bytes) をそのまま抜き、standalone な TU へ埋め、`g++ -O2 -std=c++17 -DBACKOFF_FIXED=<v>` で
build して `now_backoff` を印字させた。`start` (実体は `rdtscp()` の戻り) は hash bit が 0 になる値と
1 になる値の両方を強制した。

抽出した式の先頭: `double now_backoff = (static_cast<uint64_t>(BACKOFF_FIXED) / 1000ULL == 0ULL) ? static_cas`

| 供給値 v | 素朴解釈 | 実現 now_backoff (hash bit 0 / 1) |
|---|---|---|
| 0 | 0 µs | 0.000000 / 0.000000 |
| 1 | 1 µs | 1.000000 / 1.000000 |
| 5 | 5 µs | 5.000000 / 5.000000 |
| 10 | 10 µs | 10.000000 / 10.000000 |
| 100 | 100 µs | 100.000000 / 100.000000 |
| 900 | 900 µs | 900.000000 / 900.000000 |
| 999 | 999 µs | 999.000000 / 999.000000 |
| **1000** | **1000 µs** | **0.000000 / 0.000000** |
| 1001 | 1001 µs | 0.500000 / 0.500000 |
| 1500 | 1500 µs | 696.000000 / 700.500000 |
| **2000** | **2000 µs** | **0.000000 / 0.000000** |
| 2500 | 2500 µs | 750.000000 / 250.000000 |
| **3000** | **3000 µs** | **0.000000 / 0.000000** |
| 3007 | 3007 µs | 7.000000 / 7.000000 |

**結論 3 点。**

1. **F718 は実 compiler の出力として再現する。** v=1000 の実現値は 0.000000 で、
   F718 が数値の不連続から推定した「モード 1・振幅 0」がコード実行の実体として確認された。
2. **衝突点は 1000 だけではない。** v=2000、v=3000 も 0 µs を実現する。F718 の本文は
   1000 の 1 点だけを扱っているが、**商が 1 以上で剰余が 0 の値はすべて同じ穴に落ちる**。
   さらに商 3 以上は乱択枝を持たず剰余をそのまま返す (v=3007 → 7 µs) ため、
   「値域の上端を 999 にする」だけでは族は閉じない。
3. **実現条件は分布でありうる。** v=1500 は hash bit で 696.0 と 700.5 に分かれ、v=2500 は
   750.0 と 250.0 に分かれる。したがって関門は「要求スカラー == 実現スカラー」の形では書けない。

**この probe の限界 (誇張しない範囲):** 評価した TU は ccbench の実 TU ではない。実 TU の
マクロ環境 (`GLOBAL_VALUE_DEFINE` の TU 注入、`Linux`、`-DNDEBUG` 等) は再現していない。
したがってこの実測が示すのは「patch の合成枝の式が、供給値をこう復号する」までであり、
「実 build のその枝が実行される」ことではない。後者は D955 が未閉包と明記している範囲である。

---

## 実測 2 — 汚染点は現行の凍結格子に**残っている**

`orchestrator/campaign/backoff_extended_sweep.py:33` の `EXTENDED_SWEEP_US` は
`[0, 1, 2, 3, 4, 5, 6, 8, 10, 12, 15, 20, 25, 35, 50, 75, 100, 150, 200, 250, 300, 400, 500, 560, 600, 700, 800, 900, 1000]`
で、**末尾の 1000 が現物の main に在る**。F718 の恒久対応は「本 wave では格子から当該点を
除外して特徴づけた」であって、格子定数そのものは直していない。

さらに `orchestrator/tests/test_backoff_extended_sweep.py:121` が
`assert M.EXTENDED_SWEEP_US[-1] == 1000` で**汚染点を pin している**。
格子を直す変更は、この test と campaign identity の両方に触れる。

## 実測 3 — 族の射程は 2 経路に分かれる

条件を実行側へ渡す経路は 2 種類あり、既存の防壁の有無が違う。

- **経路 1 (hole-literal):** `orchestrator/campaign/p3_s4_loop.py` 系。coder が
  `now_backoff = <literal>` を直接書き、`assert_value_literal_consistent()`
  (`p3_s4_loop.py:953`) が宣言 scalar と literal の**数値一致**を機械照合する。
  復号は恒等なので F718 型は原理的に起きない。
- **経路 2 (define-decode):** `patches/silo-backoff-fixed.patch` を当てて
  `BACKOFF_FIXED=<v>` を build へ渡す driver 群。供給値は**ソース内の式が復号する**。
  ここに意味の関門は無い。**F707 と F718 はどちらも経路 2 である。**

経路 2 で値を条件へ復号する define は backoff だけではない。patch が Options.cmake と
`ccbench_universal_definitions()` の両方へ足す define を全 patch から機械抽出した結果:

| patch | 追加 define |
|---|---|
| `silo-backoff-fixed.patch` | `BACKOFF_FIXED` (量)、`BACKOFF_NOINLINE` (診断 0/1) |
| `variant-backoff-static50.patch` / `variant-backoff-red-1e9.patch` / `variant-noop-else-copy.patch` | 同上 |
| `silo-backoff-trigger-gating-variant.patch` | `BACKOFF_TRIGGER_GATING` (5-bit wire) |
| `silo-sort-variant.patch` / `broken-silo-sort-nonswo.patch` | `SORT_VARIANT` (enum) |
| `ss2pl-lock-protocol-study.patch` | `SS2PL_LOCK_IMPL`、`SS2PL_LOCK_KIND`、`SS2PL_DLR`、`SS2PL_WFG_DIAG` (enum + 0/1) |

`IZANAGI_BREAK_*` 系 9 patch と `instr-*` は define を Options.cmake へ足さず、条件指令から
参照するだけである (供給元が別)。

## 実測 4 — 既存の関門が届いている範囲

- **供給の関門 (F707 の恒久対応):** `backoff_profile.py:365`
  `_assert_distinct_backoff_binary_hashes()` は 7 点の binary sha256 が相異なることを要求する。
  **これは binary 水準の単射性であり、F718 は通す** — 1000 と 0 は別 binary になるが同じ意味を持つ。
- **供給集合の関門:** `orchestrator/campaign/source_digest.py` の
  `parse_supplied_macros()` / `assert_conditional_macros_covered()` (D23 道 Y、D34) が
  「条件指令が参照する識別子が実 TU 供給集合に閉じるか」を実 compiler で検査する。
  **これは供給の関門であって意味の関門ではない。**
- **実 compiler 入力の関門:** `orchestrator/campaign/s8b_compiler_input.py` は
  CMake Unix Makefiles の `flags.make` から `CXX_DEFINES` を採る。docstring 自身が
  `The manifest does not prove dynamic predicate reachability.` と限界を明記している。
- **`#error` による fails-closed:** patch は `#ifndef BACKOFF_FIXED` → `#error` を入れており、
  未定義供給は止まる。F718 はこれを通過する (供給されているため)。

## 実測 5 — 宣言の置き場所の候補が実在する

`patches/ledger.json` は `izanagi-patch-ledger/v1` で、entry ごとに `macro`、`report_macro`、
`symbols` (`kind: activation-identity`、`defined_count`) を宣言する registry である。
**ただし `scope` は `registered-entries-only` で、登録 entry は `silo_ladder_rung1` の 1 件だけ。**
backoff patch は未登録である。ここを宣言の置き場所にするなら、登録範囲の拡大が要る。

## 実測 6 — 既存被覆の性質検索 (純増の確認)

「要求値と実現条件の意味が一致するか」という性質で `docs/decisions.md` と
`docs/archive/worklog-*.md` を検索した。近いが別物である既裁定:

- **D706** (gate の述語は到達可能な値域を実測してから採用する) — 本 wave の probe はこれに従った。
- **D607 / D768** (whiteboard の値域検査を共有 validator で一本化) — 値域の形式検査であって
  実行側の意味ではない。
- **D955** (証明の種別は届いた範囲そのもので命名する) — 本 wave の関門の**命名規律**として効く。
  「意味を確かめた」と書けるのは実際に確かめた層までである。

**意味の関門そのものを扱う既裁定は見つからなかった。本 wave は純増である。**
