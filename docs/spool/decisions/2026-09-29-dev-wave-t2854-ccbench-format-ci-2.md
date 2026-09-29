---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-09-29
wave: dev-wave-t2854-ccbench-format-ci
seq: 2
---

## {{D:t2854-fmt-commit-line-restore}}. CCBench の整形 commit F は clang-format 14 の整形に、TRACE=0 の論理行番号を戻す `#line` を最小限足す形にする。F の CI 2 本は CI image で手元通過し、D297 規則 v2 は C → F を GCC 11.4 / 12.3 とも pass

対象: T-2854。資料: D2277 項 1、D2275、D2255、D780 項 1、D95、insight `output/insights/2026-09-29/t2854-ccbench-format-ci/README.md` (§0・§2・§3)、段 4 裁定 `verbatim/s4-ruling.md`、段 6 裁定 `verbatim/s6-ruling.md`。

**決定:**

1. **F の中身:** C2' `40a7f4ac` の上の F `25898d00` は、違反のある 3 file (mocc・silo の transaction.cc、trace.hh) の clang-format 14 の整形と、整形で行数が変わった `#if TRACE` 区間の直後に置く `#line` (mocc 115、silo 365・381) だけとする。`#line` の値は TRACE=0 で出力される全コード行の推定行番号が C2' と一致するように決め、`ERR` の `__LINE__` 展開値の一致でも確かめた。字句・文字列・コメント文言・既存 directive の値は変えない。作成は Codex author、commit は親 (trailer = Codex author・Codex reviewer・Claude manager)。
2. **CI の手元通過:** format は F の checkout で CI の step を login の clang-format 14.0.0 と CI image `:latest` の 14.0.6 の両方で 213 file・rc=0 (対照の C2' は rc=123・84 件)。build は計算ノードで CI image `:ci` (GCC 13.3.0) を apptainer `--userns` で動かし、CI の configure・build argv に offline 供給の 4 引数だけを足して rc=0。記録の言い方は「CI image と CI の build 手順による手元通過」で、GitHub Actions の緑は push 後に確かめる。
3. **D297:** 検査器 (D2275 の判定時と同一 blob) で C → F は GCC 11.4・12.3 とも pass。pass は F に限って言い、TPC-C の certified と trace 完全除去は名乗らない (D780 項 1)。負例対照は再実施しない。
4. **pin と push:** gitlink・`CCBENCH_FULL_SHA`・`CURRENT_PIN`・patches は変えない。F の branch `izanagi-tpcc-v3-silo-mocc-fmt` の push は人間の手番。GitHub の CI の緑と F の取得の確認後に、同時更新と patch 54 本の厳密適用を別 wave で行う (D2277 項 1 (3)(4))。

**理由:**
- 整形だけだと、行数が変わる `#if TRACE` 区間の後ろで TRACE=0 の論理行番号がずれる (mocc -3、silo 最大 +2)。mocc の TRACE=0 有効コードの `ERR;` は `include/debug.hh` の `NNN` 経由で `__LINE__` に展開されるので、trace 用コードの整形が TRACE=0 の性能計測 build を変える (規律 1)。D2277 の「意味を変えない整形だけ」の趣旨は TRACE=0 を変えないことで、`#line` はそのための最小の付随変更であり、この branch の既存 commit (C1'・C3・C2') が取っている作法と同じ。
- CI image を使うと compiler・cmake・system の依存が CI と揃い、`-Wall -Wextra -Werror` の下で字下げ依存の警告 (GCC 13) が build を割らないことまで確かめられる。依存 cache に残る git 管理外の生成物 (masstree の `config.h`・`.a`) を持ち込むと、masstree の custom command が作り直さず手元 GCC の古い生成物を使うので、clean clone で供給した。

**却下した選択肢:**
- 整形だけの commit — TRACE=0 の build が変わり、D297 の header 分岐 (実 include 込みの完全展開) でも拒否される見込みだった。
- `// clang-format off` で整形を避ける — format の CI は通るが、上流の整形規則に合わせるという依頼の品質を満たさない。
- host の GCC 11 / 12 で build して CI 相当と呼ぶ — CI の compiler (GCC 13) と違い、字下げ依存の警告の差を確かめられない。
- 負例対照 (tpcc.hh の `#line 56` 削除) の再実施 — 検査器は同一 blob で、依頼が求めるのは F の正例判定。約 0.26 node 時間を省いた。
