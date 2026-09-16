# [T-2630] 既裁定・一次資料の逐語射影 (親が sed で原文から切り出した。編集していない)

## 1. D2044 項 25 (docs/decisions.md、local main a5f953a66)

対象: T-2630。

**決定:** 非再帰な走査境界から許された variant が、別挙動と stock identity 継承へ到達する例を
既存の変異 harness で実測する。未到達だけを不存在とは結論しない。

**理由・採らない案:** 到達すれば絶対規律 2 の穴そのものであり、実測は既存の道具で取れて
新しい機構を要しない。限界の明記だけで閉じる案は、穴の有無を未知のまま残すため採らない。

### 項 26 — 認定較正の打ち切り窓は限界のまま置く


## 2. 正本 worklog entry 1528 の [T-2630] 項 (docs/archive/worklog-phase3-0916-1528.md:733-736)

- [T-2630] **P2・裁定済み (D2044 項 25) → 実測手番**:
  非再帰な走査境界から許された variant が別挙動と stock identity 継承へ到達する例を、既存の
  変異 harness で実測する。**未到達だけを不存在とは結論しない。** 到達すれば絶対規律 2 の穴
  そのものであり、実測は既存の道具で取れて新しい機構を要しない。

## 3. 初出 worklog entry 1498 の [T-2630] 項 (docs/archive/worklog-phase3-0914-1498.md:702-705)

- [T-2630] **P2・新規**: `source_digest.py:85` / `:1895` /
  `:1662` の非再帰な走査境界 (`EVOLVE_BLOCK_SOURCES` の 3 file、`#include` 行は除去) から
  許可された variant が、実際に別挙動・stock identity 継承へ到達するかは未証明である。
  到達例を実測するか、限界の明記で閉じるかを裁定する。

## 4. T-1643 insight §9 (R-2) (output/insights/2026-09-14/t1643-has-include-real-pair/README.md:252-263)

## 9. 裁定パッケージ候補 (scope 外の real 所見)

本 wave では実装しない。

- **(R-1) legacy 分岐の compiler 引数の非対称。** `orchestrator/campaign/pipeline.py:1790` が
  site 選択した compiler を checker へ渡す一方、`common is None` の legacy 分岐 (`:2002`、
  `buildcache.py:3140`) は `cc/cxx` を渡さず既定 `g++-13` を使う。静的に確認できる非対称であり、
  到達可能性と既存防壁との関係の評価は別裁定。
- **(R-2) 走査範囲外の include 先の一般安全性。** `source_digest.py:85` / `:1895` / `:1662` の
  非再帰な走査境界は実在するが、そこから許可された variant が実際に別挙動・stock identity 継承へ
  到達するかは未証明である。今回は安全性主張の除外範囲として記載するに留める。
- **(R-3) コメントと観測の不一致。** `source_digest.py:372-373` と guard の拒否診断本文は

## 5. T-148 レビュー逐語の A-n2 (output/insights/2026-07-28/t148-review-verbatim/findings-and-rulings.md:33 / review-focus-claude-closed-partial-table.md:32)

| A-n2 / A-n5 | `#undef` 未モデル / pin 側内容は未検査 | 記録のみ (alias 源にならない) | 未実装 (insight の「残る穴」に記載) |
| A-n2 | **not-addressed (裁定どおり)** | insight「残る穴」に記載あり |

## 6. D34 の残る穴 (docs/decisions.md:813-814)

- 残る穴: computed include (`#if __has_include`) は #include 行に現れず -nostdinc で dead 化 = 依然 identity に
  乗らない (known-limitation、auditor + 規律6 監査領域、恒久 fix は skeleton 抽出が要り却下済み)。

## 7. 親の前提実測 (2026-09-16 login pegasus02、g++ 11.4.0、checker と同じ argv)

入力 3 種 (job tmp の stock.cc / sandwich.cc / undef.cc) を `g++ -E -P -nostdinc -Werror=undef -std=c++20 -O3 -DNDEBUG -DLinux=1 -x c++ <file>` に通した出力の sha256 は 3 つとも `dd769427aeef82acbf737bf904cbd82460112da44bc83da0a74e4ce078bb7029` (2 行: `int f();` / `int g() { return f(); }`)。sandwich.cc は `#define desired expected` / 空行 / `#undef desired` を先頭に持ち、undef.cc は `#undef Linux` を先頭に持つ。指令は出力に現れず、-P は空行も畳む。

superproject で `git show HEAD:external/ccbench/cc/silo/transaction.cc` を叩くと `fatal: path 'external/ccbench/cc/silo/transaction.cc' exists on disk, but not in 'HEAD'` (submodule は gitlink なので superproject の HEAD blob として取れない)。したがって `tools/mutation_harness.py` (`_read_head_sources` が `git show HEAD:<rel>` で固定 HEAD blob と照合) は submodule 内 file を直接変異できない。

CCBench の compile option: `external/ccbench/cmake/CompileOptions.cmake:32` に `PRIVATE -Wall -Wextra -Werror`。

silo TU への -D 供給 (`external/ccbench/cc/silo/CMakeLists.txt:5,9,10` と `cmake/Options.cmake:19,27,30,47`): `NO_WAIT_LOCKING_IN_VALIDATION=1`、`SLEEP_READ_PHASE=0`、`WAL=0`、`TRACE=0` (universal)。`cc/silo/transaction.cc` 本体の条件指令: `#if BACK_OFF` (:42,:719)、`#if ADD_ANALYSIS` (多数)、`#if TRACE` (:147,:174,…)、`#if NO_WAIT_LOCKING_IN_VALIDATION` / `#elif NO_WAIT_OF_TICTOC` (:161,:165)、`#if SLEEP_READ_PHASE` (:278: `sleepTics(SLEEP_READ_PHASE);`)、`#if WAL` (:636)。

`cc/silo/transaction.cc` の include 列 (:1-9): `<stdio.h>` `<algorithm>` `<string>` `"include/atomic_tool.hh"` `"include/log.hh"` `"include/transaction.hh"` `"include/scan_callback.hh"` `"../../include/trace.hh"`。`cc/silo/include/transaction.hh:9` が `"../../../include/backoff.hh"` を include し、その後 :10-20 で fileio/procedure/result/status/string/workload/common/log/silo_op_element/scan_callback/tuple を include する。`include/backoff.hh:9-12` は `"atomic_wrapper.hh"` `"result.hh"` `"tsc.hh"` `"util.hh"` を include。`cc/silo/include/atomic_tool.hh` は `common.hh` と `../../../include/inline.hh` を include し、`atomicAddGE()` が `expected`/`desired` の CAS ループ (`__ATOMIC_ACQ_REL`, `__ATOMIC_ACQUIRE`) を持つ。

template patch `patches/silo-backoff-fixed.patch` の hunk: `cmake/Options.cmake` に `@@ -18,6 +18,13 @@` と `@@ -61,6 +68,8 @@`、`include/backoff.hh` に `@@ -11,6 +11,15 @@` (include 直後) と `@@ -91,9 +100,29 @@ public:` (EVOLVE-BLOCK)。transaction.cc は触らない。`orchestrator/campaign/paper_story_a1_source.v1.json:6` が同 patch を `patch_sha256` で pin する。
