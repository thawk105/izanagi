---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-09-01
wave: dev-wave-t2113-sort-oracle-ir-liveness
seq: 2
---

## {{D:sort-oracle-ir-liveness-bounded}}. sort oracle の IR 化は技術的に生きている。ただし主張の範囲を測定に縛る

**決定:** D1355 が実装前に確かめよと定めた生死確認は**真**である。権威集合 15 件は 3 opcode の
型付き IR へ全件表現でき、その trusted evaluator は現行 2 corpus の関係行列を実 oracle と
完全一致で再現し、未知 opcode・型不一致・任意 C++ 文字列を評価前に拒否した。3 field に対する
完全閉包 79 値でも同じことが成立した。**したがって parser・receipt・合成エージェントの設計へ
進むことを技術的理由で止めない。**

同時に、この測定が**licence しない**主張を確定する。以後の wave は次を根拠にしてはならない。

- 供給網検証済みの oracle 実行である — dependency manifest 検証は迂回した。
- D344 を supersede した、または D39 と同じ実験である — 未裁定である。
- certified `sort_best` の受理経路を置換できる、または権威集合を 79 値へ広げてよい —
  D1357 の 15 組 exact binding とは別の権威であり、79 値で置き換えると受理集合が広がる。
- 現行 pin が将来 evaluator の pointer 規則を保護する — `CORPUS_SHA256` は allocation 順の
  変更を捕捉せず、`CONTRACT_VERSION` / `AXIOM_CHECKER_VERSION` は固定整数である。

**理由:**

- 測定は模擬型ではなく**実 oracle の TU・型・allocator・broker** で行った。D344 が実型 harness を
  必須とした理由 (模擬では SWO を満たすが実型では満たさない comparator が通る) は、
  ground truth を production 実装そのものにすることで回避している。
- 緑が恒真でないことを負例対照 3 件で確かめた。符号つき storage・逆順 pointer rank・
  NUL 切り詰め key のいずれも検出された (KILLED)。とくに pointer rank の逆転が
  各 corpus 108 セルで検出されたことは、pointer 順位の導出が偶然の一致でないことを示す。
- 一方で、生死確認は「技術的に可能か」しか答えていない。D344 がユーザー裁定へ返した論点は
  可否ではなく実験同一性であり、それは測定では決まらない。

**却下した選択肢:**

- 生死確認が真なので D344 は自動的に supersede されたとみなす — 却下理由が技術的不能では
  なかった以上、技術的に可能だと示しても却下理由は解消しない。
- 主張範囲を書かずに真とだけ記録する — 後続 wave が受理集合の置換まで licence されたと
  読む余地を残す。
- 模擬型 harness の結果で終端する — D344 が明示的に閉じた穴を再び開ける。
