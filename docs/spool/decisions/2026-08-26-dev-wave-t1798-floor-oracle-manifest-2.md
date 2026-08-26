---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-08-26
wave: dev-wave-t1798-floor-oracle-manifest
seq: 2
---

## {{D:canonical-dependency-material}}. 床値 oracle の依存材料は規則で導出した canonical root へ射影し、build 境界は二根で照合する

**決定:** 床値の `sort_best` cell について、oracle が判定する依存 root を、実 source root から
規則で導出した canonical root にする。宣言集合は **VCS の tracked 一覧と `config.h` と生成した
`PIN` の和**とし、test fixture を production から参照しない。`PIN` は検証済み HEAD と改行から
生成し、実 source にある `PIN` は読まない。pin 比較は既存の
`sort_swo_oracle._prepare_verified_dependency` を再利用し、第二の pin 実装を作らない。

build 境界は canonical root への単純な付け替えにせず、**二根検査**にする。

- canonical root には既存の exact verifier (`_verify_dependency_root`) を掛ける。
- 実 source root には canonical との等価検査を掛ける。tracked 集合、宣言 path の bytes、HEAD、
  `config.h` を対象とし、各 file を読取時 identity 付きで読んだうえで、**全 file を読み終えた後に
  それらが一つの安定状態だったことを一括再検査する。**
- archive は宣言集合に含めず、従来どおり独立 hash で照合する。

受理集合は二段に分けて述べる。**oracle 単体の root 述語の受理集合は不変である。**
一方「実 source root から floor が PASS する」という合成述語の受理集合は空集合から非空へ拡大する。
拡大は等価射影に限る。

**本決定が束縛しないもの**を明記する。archive (`libkohler_masstree_json.a`) の**生成権威は
束縛しない**。archive は生成後に観測した hash を権威として運ぶだけで、それを作った tool の
identity は検査していない。宣言外の生成物 (`configure`、`config.h.in`、`GNUmakefile`、object file)
も検査していない。したがって**因果鎖を閉じたとは主張しない**。

**理由:**

- **実 source root は oracle の受理形になり得ない。** floor の preflight は依存 root が VCS の
  top-level であることを要求するので、root には必ず VCS metadata が入る。oracle は root 直下再帰の
  全 regular file 集合が宣言集合と exact 一致することを要求する。実測では実 root 196 file に対し
  宣言は 101 で、差の 95 件は VCS metadata と prebuild 生成物だった。実 root に manifest を置く案は
  成功する入力を持たない。
- **規則導出なら pin を緩めずに到達できる。** 実測では、宣言 101 path のうち実 root に無いのは
  `PIN` だけで、残り 100 path は `config.h` を含めすべて bytes 一致した。規則で組み立てた manifest は
  凍結 fixture のそれと byte-identical になり pin と一致する。独立な 2 つの実 root で確認した。
  `config.h` は configure 生成物だが、同じ recipe を別 base で走らせても bytes が一致した。
- **canonical だけを見る build 境界は D953 を壊す。** 実 source の非 `config.h` tracked file が
  変わっても通ってしまう。実 source だけを見る形は成功集合が空のままである。二根で見て初めて
  「oracle が受理した材料と build が読む材料が同じ」が成立する。
- **pin 一致は宣言 bytes の同一性しか証明しない。** 宣言外の file が root に無いことは
  canonical root の作り方が保証するのであって pin が保証するのではない。両者を混同しない。
- **合成 root では pin 一致に到達できない。** 生成する `PIN` の中身は実 HEAD であり、合成 checkout の
  HEAD が pin 済み commit になることはない。したがって合成材料での試験は「pin 不一致で
  fail-closed する」ことの確認に限り、pin 一致から先は実 checkout を要する明示 opt-in が担う。
  この非対称は隠さず試験設計へ書く。

**却下した選択肢:**

- **宣言側を実在へ合わせて pin を広げる** — VCS metadata の可変内容を宣言に含めることになり
  安定しない。受理集合を広げるので規律 2 に反する。
- **build 境界の検査対象を canonical root へ単純に付け替える** — oracle と build が別材料でも
  通る。D953 が閉じた穴を開け直す。
- **test fixture の宣言リストを production が読む** — production が test 資材へ依存する。
  規則で導出すれば、規則の誤りは pin 不一致として fail-closed する。
- **pin 比較を新 module で再実装する** — 同じ規則を 2 箇所で実装すると両方を通る入力が
  空になりうる (F625 の型)。既存関数を再利用すれば構造的に避けられる。
- **prebuild が使う tool の identity をこの決定で束縛する** — 実行権威の変更であり、
  D425 が別審査とした型に属する。CCBench の改変も伴う。代わりに保証水準の限定を明記した。
- **合成材料で pin 一致まで通す試験を作る** — 原理的に不可能である。迂回するには pin か
  VCS probe を置換することになり、どちらも受理集合か検査そのものを壊す。
