---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-08-15
wave: dev-wave-t856-verified-oracle-verdict
seq: 2
---

## {{D:oracle-verdict-seal-by-rederivation}}. oracle verdict の封印は再導出と canonical 型厳密比較で行う

**決定:** `judge_combined` は `VerifiedOracleVerdict` 封印 token だけを受理する。token は
`verify_oracle_verdict` が (1) strict load、(2) `ReviewedSpec` exact type、(3) 両 sha256 が
exact `str`、(4) manifest document の nested 値が plain JSON 型ちょうど、(5) schedule 射影、
(6) manifest document の canonical hash 再導出照合、(7) manifest の `spec_sha256` と
approved spec の束縛、(8) oracle の `manifest_sha256` と検証済み manifest の束縛、
(9) observations からの `judge_oracle` 再導出、(10) 再導出結果と入力文書の canonical JSON
**文字列**一致 をすべて通したときだけ発行する。token は発行時の document canonical hash を
束縛し、`judge_combined` は plain 型と hash を再照合してから中身を取り出す。

**理由:**
- schema 名と manifest sha の照合だけでは、正しい公開 sha を転記した改竄 verdict が通る。
  これは D304 が「公開 pin との比較は迂回者が転記すれば満たせる」と決めた型と同一である。
  再導出まで行って初めて、単独の verdict 文書の改竄が閉じる。
- 比較に dict 等値を使うと Python の `True == 1.0` が成立し、median を `true` へ差し替えた
  verdict が一致と判定される。実測では、その verdict は下流の実数判定で拒否されるため
  結論が成立から判定不能へ倒れる。canonical JSON 文字列比較はこの型混同を落とす。
- 全文書 1 本の比較にすると、余剰 top-level key・malformed holdouts・別 schema は
  すべて不一致として落ちる。個別 guard を並べると冗長 gate になり、変異の単一理由性が壊れる。
- (6) は発行時と同じ canonical hash 関数を使うため、正当な token を誤って落とさない。

**却下した選択肢:**
- **manifest sha 束縛だけを足す** — 公開 sha を転記した semantic 改竄が残る。
- **掲載だけの証拠 field を足す** — 恒真化であり、起票時に却下済み。
- **observations 層にも封印 token 境界を新設する** — D304 がレポート層と判定層の間の
  改竄防御まで広げる権威の設計判断として明示的に scope 外に置いている。

## {{D:seal-trust-boundary-by-reflection}}. 封印 token の信頼境界は反射操作の有無で引く

**決定:** izanagi の封印 token (検証済み文書を表す型) が防ぐ範囲は、**通常の Python 操作で
成立する迂回まで**とする。具体的には、発行済み token の内包 dict の item 代入、
`str` / `dict` の subclass を作って渡すこと、duck typing で `.document` を持つ別 object を
渡すことは**防ぐ**。`object.__setattr__` / `object.__new__` / `__closure__` 参照など
**反射操作**を要する偽造は信頼境界外とし、防御を足さず docstring に明記する。

**理由:**
- 「in-process 偽造は信頼境界外」とだけ書くと範囲が曖昧で、通常の dict 代入だけで結論を
  変えられる状態を「境界外だから仕方ない」と見逃す。実際にレビューはこの穴を突いた。
- 反射操作まで防ごうとすると、封印は言語機能との軍拡になり、検査の維持費が
  防いでいるリスクを上回る。境界を反射の有無で引くと、実装も docstring も一意に決まる。
- 通常操作側は安価に閉じられる。発行時 hash の束縛、`type(x) is str`、
  nested 値の plain JSON 型検査はいずれも数行で、それぞれ独立に入力を落とす。

**却下した選択肢:**
- **「in-process 偽造は境界外」だけを書いて何も足さない** — 通常の dict 代入で結論が
  変わる状態が残る。
- **document を再帰的に不変化する** — consumer が Mapping として読む前提を壊し、
  既存の三値判定本体まで書き換えが波及する。
