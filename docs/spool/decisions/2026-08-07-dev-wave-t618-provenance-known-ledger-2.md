---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-08-07
wave: dev-wave-t618-provenance-known-ledger
seq: 2
---

## {{D:known-violation-note-field}}. 既知違反台帳の entry を 4 要素にし、注記を stdout へ公開する

**決定:** D221 が 3 つ組 `(full 40-hex SHA, expected_finding_kind, ruling)` と定めた
`KNOWN_PROVENANCE_VIOLATIONS` の entry を、**4 つ組 `(SHA, expected_finding_kind, ruling, note)`**
へ拡張する。D221 の他の条項はすべて不変で、本決定は schema の記述だけを置き換える。

- `note` は既定値 `""` の optional field とする。**空 note を持つ entry の stdout は逐語不変**で、
  既存 6 entry の出力は 1 byte も変わらない。
- 非空 `note` を持つ entry だけが `known-violation sha=… finding=… note=…` として公開される。
  rc=1 側と rc=0 側の出力は共通 helper へ集約し、片側だけが古い形式のまま残る経路を作らない。
- `note` の妥当性検査は、D221 が定めた lazy な台帳検査 (history 分岐内) の中で、既存の
  ruling 検査の直後に置く。**`str` でないとき**、または**非空かつ `note.splitlines() != [note]`**
  のとき `RuntimeError` を送出し、既存経路で rc=2 になる。`!= ""` の前置は必須である
  (省略すると `"".splitlines() == []` が `[""]` と一致せず、空 note の既存 entry が全部 rc=2 になる)。
- **照合条件・rc semantics・stale 判定・`--message-file` 経路・forward correction・waiver は
  一切変えない。** `note` は表示 field であって受理条件ではない。

**理由:**
- 既知違反には 2 種類ある — 帰属そのものが無いものと、帰属は在るが書式が崩れて Git が trailer と
  認識しないもの。後者を前者と同じ 1 行で記録すると、台帳の読み手は「AI が関与を隠した記録」だと
  誤読する。注記を持たせて公開すれば、rc=0 の隣で「なぜ既知なのか」を再診断なしに読める。
- `ruling` field は既に「どの裁定で 1 件増えたか」の tripwire になっているが、**裁定の出典を指す
  だけで内容を持たない**。同じ出典から複数の理由で entry が増えたとき、出典だけでは区別できない。
- 改行を拒否するのは、公開行が「1 entry = 1 物理行」であることに読み手も下流も依存するためである。
  `splitlines()` を使うと LF / CR / CRLF / U+2028 / U+2029 / NEL / VT / FF を一括で拒否できる。
  この幅を 1 例だけで pin すると `"\n" in note` への弱化を検出できないため、検査は最低 4 種の
  改行族で pin する。
- optional にして既存 entry を空のまま残すのは、**過去の裁定へ未裁定の説明を遡及追加しない**ため。
  全 entry へ必須の注記を課すと、書き手が裁定に無い説明を創作することになる。

**却下した選択肢:**
- 注記を source コメントだけに置く — 実行時に見えず、rc=0 の stdout を読む人・自動層のどちらにも
  届かない。台帳の公開が唯一の抑止であるという D221 の理由と整合しない。
- 全 entry に必須 `note` を課す — 既存 6 件へ遡及的な説明を書くことになり、出力の逐語互換も壊れる。
- `ruling` 文字列へ注記を畳み込む — 出典 field と説明 field が二義化し、片側 drift の tripwire が
  鈍る。
- 注記を docs 側に置き code から参照する — D221 の「code は docs を parse しない」を破る。
