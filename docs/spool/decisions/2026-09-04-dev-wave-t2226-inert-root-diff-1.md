---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-09-04
wave: dev-wave-t2226-inert-root-diff
seq: 1
---

## {{D:inert-root-location-classification}}. inert 比較の置き場所判定は閉包束縛の差分分類で行い、生成元までは束縛しない

**決定:** D1523 が定めた「差を取ってから置き場所由来かを判定する」形を、次の述語で実装する。

- 差のある行だけを対象に、requested 側の出力に現れる `<requested source root>/<相対 path>` を
  `<control source root>/<相対 path>` へ写す。写してよいのは次の 3 条件をすべて満たす位置だけとする。
  1. 一致位置の直前の byte が path 文字集合に属さない (左 token 境界)。
  2. root の直後が `/` である。
  3. 続く相対 path を字句正規化した結果 `rel` について `source/<rel>` が **requested の依存閉包に実在する**。
- 写した後に 1 byte でも残差があれば赤。行数差、root に改行を含む、置換 0 件、
  code-owned な `__FILE__` / `__BASE_FILE__` の不在もすべて赤。
- **build root は置換対象に含めない。** 差が build root だけでも残差として赤にする。
- 置き場所由来だけと判定したときに限り、新しい理由コードで緑にする。前処理 bytes が完全一致する
  既存の緑は、判定経路も理由コードも変えない。
- **置換した span が compiler の `__FILE__` 展開であったことは証明しない。** この限界を成果物へ明記する。

**理由:**

- 判定が保証するのは「差のある行が root 文字列の差し替えだけで control 行と byte 完全一致する」ことである。
  相対 path が両側で同一である差は、同じものを別の場所に置いたことによる差である。
  相対 path が違えば残差が出て赤になる。
- source に実行時の一時 directory の絶対 path を書き込むことはできない。出力へ絶対 root が入る経路は
  compiler の `__FILE__` / `__BASE_FILE__` と、build system による source dir の埋め込みだけであり、
  どちらも置き場所由来である。生成元を証明しなくても、通す差は置き場所を揃えれば消える差に限られる。
- 閉包束縛と左 token 境界は、この保証をさらに狭めるための条件である。健全性の根拠ではないが、
  root 文字列が別の token の接頭辞になっている位置を落とすので、狭める方向 (規律 2 の向き) に効く。
- build root を外したのは、**発火条件を満たす実在の成果物 path も計測 ID も名指しできない**ためである。
  到達不能な述語を足すと、検査できない分岐が 1 本増える。外す方が受理集合が狭く、
  実際に必要になれば赤として観測される。
- 実測: `g++-12 -E -P` の `__FILE__` は相対 include 経由で `<root>/cc/silo/../../include/backoff.hh` と
  **正規化されない形**で出る。したがって `..` を含む相対 path を拒否することはできない。
  また `__FILE__` は「その語を含む file」ではなく「その語が展開された file」の path になるため、
  root 依存 builtin を持つ file の一覧へ置換先を縛る設計は実物では成立しない。

**却下した選択肢:**

- **`-fmacro-prefix-map` で compiler に root を正規化させ、追加でもう 1 回 preprocess して byte 完全一致を
  要求する** (段 6 レビューの推奨) — 生成の時点で畳む形であり、D1523 が却下した「比較の前に情報を捨てる」
  形に当たる。inert arm ごとに preprocess が 1 回増える。compiler 未対応時の fail-closed 枝を
  発火させる実在の成果物を名指しできない。
- 置換先の相対 path が control 側の閉包にも実在することを要求する — 発火する入力を作れない。
  requested の閉包にあって control の閉包に無い file は、その中身が requested 出力にだけ現れるので
  必ず残差で赤になる。検査できない述語は足さない。
- 相対 path の `..` と末尾 `/` を禁止する — 上の実測どおり `..` は実在の展開形に必ず現れる。
