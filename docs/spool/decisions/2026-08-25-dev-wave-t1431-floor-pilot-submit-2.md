---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-08-25
wave: dev-wave-t1431-floor-pilot-submit
seq: 2
---

## {{D:effective-masstree-root-needs-two-independent-witnesses}}. 実効 masstree source root は cache 入力と生成 build system の一致で主張する

**決定:** floor の `sort_best` cell について、build が実際に使った masstree source root の
権威を、次の 2 つの独立した証跡の**一致**に置く。

- **A (cache 入力):** cell の build directory の `CMakeCache.txt` にある
  `FETCHCONTENT_SOURCE_DIR_MASSTREE`、無ければ `<FETCHCONTENT_BASE_DIR>/masstree-src`。
- **B (解決結果):** 生成された build system
  (`CMakeFiles/masstree_build.dir/DependInfo.cmake` の `CMAKE_MULTIPLE_OUTPUT_PAIRS`) が
  記録した `config.h` と `libkohler_masstree_json.a` の絶対 path 対の親ディレクトリ。

A と B が一致しなければ拒否する。生成器は `CMAKE_GENERATOR` の exact 照合で
`Unix Makefiles` に固定し、未知の生成器・証跡の欠落・複数 root は fail-closed とする。
呼び手が行う「実効 root は staged base の `<base>/masstree-src` でなければならない」
という exact 比較は従来どおり残す。すなわち A = B = expected の三者一致を要求する。

D425 の「実効 root を build 自身の成果物から読む」という要求はそのまま維持し、
その運び手を `masstree_SOURCE_DIR` という単一 key から上記 2 証跡へ置き換える。

**理由:**

- D425 が想定した `masstree_SOURCE_DIR` は、現行 CCBench pin では**出現しえない**。
  CCBench の `cmake/ThirdParty.cmake` は 1 引数形式の `FetchContent_Populate(masstree)` を
  使い、この形式は `<name>_SOURCE_DIR` を呼び出し scope の通常変数にしか設定せず
  CMakeCache へ書かない。実測でも当該 key は 0 件である。守るべきは
  「実効解決値を build 自身の成果物から読む」という性質であって、特定の key 名ではない。
- A だけでは D425 が名指しで警戒した経路が閉じない。CMake の変数解決では通常変数が
  cache 変数より優先されるため、ambient な toolchain file が
  `set(FETCHCONTENT_SOURCE_DIR_MASSTREE <別 root>)` を cache 指定なしで行うと、
  実効値は別 root になるのに `CMakeCache.txt` には argv 由来の値が残る。
  A だけを読むと、誤った tree で作った binary に対して A の検査も
  内容 receipt の再観測も両方緑になる。敵対レンズ 2 本が独立にこの経路を指摘した。
- B は `add_custom_command(OUTPUT ...)` の OUTPUT を生成器が展開した結果であり、
  通常変数による上書きも必ず反映される。A が「与えた入力」、B が「解決された結果」で
  あって、同じ値の二重読みではない。
- 生成器を exact 照合で固定するのは、B の layout が生成器依存だからである。
  想定外の生成器で B を推測して読むより、拒否して人間の判断を仰ぐほうが安全である。

**却下した選択肢:**

- **A だけを読む** — 上記の通常変数 shadow を検出できない。床値の数値が
  staged payload 以外の masstree 由来になりうる一方、completion manifest には
  staged root の hash が残るという、記録と実体の乖離を作る。
- **呼び手の expected 比較を `FETCHCONTENT_SOURCE_DIR_MASSTREE` の値へ切り替える** —
  staged base の外を指す override を受理してしまい、規律2 を弱める。
- **検査を警告へ落として先へ進める** — 規律2 の違反である。床値は certified な
  選択結果の下限として使われるため、依存の同一性が主張できない測定値には意味がない。
- **CCBench 側を `FetchContent_MakeAvailable` へ変えて lowercase key を cache へ載せる** —
  CCBench の改変は D16/D18/D20 の対象で、上流判断は人間に委ねる。
  izanagi 側だけで閉じられる修正を優先する。
- **生成器非依存の証跡を探して B の代わりにする** — 現行 pin と現行 argv では
  `CMAKE_GENERATOR` が cache に記録されており、exact 照合で固定できる。
  非依存化は将来 Ninja を使う判断が出たときに再設計すればよく、
  発火していない条件のために今実装しない。
