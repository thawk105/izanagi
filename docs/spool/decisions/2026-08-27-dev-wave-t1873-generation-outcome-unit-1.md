---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-08-27
wave: dev-wave-t1873-generation-outcome-unit
seq: 1
---

## {{D:generation-onoff-contrast-narrow-reading}}. generation/search の on/off 差と対比は、identity と正規形の連言・選言で判定する

**決定:** D1066 は判定 3 条件のうち入れ替え追従だけを「descriptor 条件付きの予測構成へ正規化した
比較」へ読み替えた。残る 2 条件について、次の狭い読みを採る。

- on/off 予測差の成立は、**最終世代 canonical variant の identity が異なり、かつ正規形も異なる**
  holdout が存在すること (連言)。
- 反復単位の対比における同一予測の短絡 (不成立へ倒す側) は、**identity が同じ、または正規形が同じ**
  こと (選言)。

対の作り方、主量、三値判定、退避の禁止といった対比そのものの規定は変えない。
単独読みへ戻すのは緩和であり、別途ユーザー承認を要する。

**理由:**
- canonical variant の identity は genome と source token の hash であり、独立に合成された 2 つの
  variant がこれを共有することは実質的に起こらない。identity だけで on/off 差を見ると条件が
  ほぼ恒に成立する。これは D1066 が入れ替え追従について認定した恒真性の、向きを反転した同型である。
- 正規形だけで見ると、identity が異なるものを同一と扱う。
- どちらの単独読みも一方向へ緩む。連言と選言はどちらの単独読みより受理集合が狭く、
  正しさゲートを緩めない側に立つ。D1066 が扱わなかった空白を狭い側へ埋めたものであり、
  裁定の変更ではない。

**却下した選択肢:**
- identity だけで判定する — 条件 1 が恒真に近くなる。
- 正規形だけで判定する — 異なる合成結果を同一と扱う。

## {{D:generation-swapped-constant-source-family}}. 入れ替え追従は、入れ替え元の正規形が定数なら不成立とする

**決定:** generation/search の入れ替え追従は、derangement の全組で正規形が exact 一致することに加え、
**入れ替え元の on 正規形が全 holdout で同一 (定数) でないこと**を成立の前提とする。
定数なら、完全なデータでも不成立とする。

**理由:**
- 「on arm は常に構成 A、off arm は常に構成 B」を返す生成器は、descriptor の中身に応答していないのに、
  on/off 差・入れ替え追従・対比のすべてを成立させられる。段 3 の敵対相談が完全な入力族として構成した。
- 8b 設計の判定基準は既に「一つの同一選択が複数 descriptor で予測されることは、データが完全なら
  descriptor 駆動を支持しないと報告する」と定めている。本決定はこれを generation/search の
  正規形比較へそのまま適用したものであり、新しい基準ではない。

**却下した選択肢:**
- exact 一致だけを見る — 定数の生成器が全条件を成立させる。
- 定数のとき判定不能へ倒す — データは完全であり、報告できる負の転帰を捨てることになる。

## {{D:generation-outcome-admissible-certified-only}}. 最終世代の正常な転帰は certified だけとする

**決定:** generation/search の最終世代 outcome として受理するのは `certified` だけとする。
既存 certified variant の再利用を表す転帰を含め、それ以外はすべて判定不能とする。

**理由:**
- 再利用の転帰を正常と数えるなら、その再利用が指す既存の correctness 証拠を判定器側で
  再検証しなければならない。再検証しないまま受理すると、証拠のない変異が certified な
  outcome として判定と結果表へ入る。
- 受理を certified だけに閉じれば、再検証の機構を足さずに同じ穴が消える。判定不能は
  descriptor 効果の負の証拠ではなく実行証拠の欠落として報告されるので、主張を作らない。

**却下した選択肢:**
- 再利用の転帰を正常に含め、証拠の再検証を判定器へ足す — 実走成果物が無い段階で
  機構だけが増える。
- 再利用の転帰を無条件に正常と数える — 証拠のない outcome が通る。
