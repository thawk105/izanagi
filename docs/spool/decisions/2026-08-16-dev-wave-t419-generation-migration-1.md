---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-08-16
wave: dev-wave-t419-generation-migration
seq: 1
---

## {{D:env-generation-activation-is-human-lockstep}}. 環境契約 g2 の活性化は上位権限束の人間 lockstep に従属する — D143 (b) は裁定済みだが単独では発効できない

**決定 (2026-08-16 ユーザー裁定 = D143 決定 (3) 択 (b) の実施可否):**
D143 決定 (3) は択 (b)「述語を正とし、較正を取り直して登録し直す + 取得時受入検査」で確定した。
**このうち「取り直す」と「取得時受入検査」は既に land 済みであり、未実施は「登録し直す」
= 環境契約世代の活性化だけである。** そして**その活性化を本 wave では実施しない。**

活性化は D272 と `docs/calibration-freeze-authority-bundle-design.md` の
既裁定 (2026-08-10 / 2026-08-11) に従属する。すなわち
**(i) 環境世代と ratified freeze 世代の lockstep (片側交代は却下済み)**、
**(ii) 上位束の承認 A と発効 X はともに人間**、である。同設計は段 0 が `incomplete` で、
上位 cancellation record の扱いがユーザー裁定待ちのまま残っている。
2026-08-16 の裁定控えは上位権限束に言及しておらず、
**「AI が単独で環境側だけ発効してよい」は裁定時の未見事実である。**

**実測 (本 wave が worktree で取得。すべて実装差分ゼロの read-only 観測):**

1. **活性化は実行時の受理挙動を変えない。** canonical clock 述語は期待列の**中央値だけ**を使い、
   帯検査は**観測列にのみ**適用する。g1 と g2 は中央値 2101.0・tolerance 2.0 が同一で、
   帯は両者とも [2058.98, 2143.02] である。
   `compare_profiles` の 21 field のうち g1/g2 で値が異なるのは 4 件だけで、
   `tsc` 系は `round(median)` 比較でともに 2100、clock 帯は同一である。
2. **`effective_clock.method` の比較は恒真である。** 当 field は
   「expected と observed がともに非空 str」だけで pass になり、値の一致を見ない。
   その結果、期待側が素朴法・観測側が方式 α という**実体不一致が pass として receipt に残る**。
   g2 の期待側は方式 α なので、活性化すれば実体が一致する。
3. **壁 1 (実行時 attestation) は g1 のままでも構造上開いている。** certified 経路は
   現行 probe (方式 α) を使い、方式 α は静穏時に凍結中央値 2101.0 の帯を
   9/9 通過・過剰拒否 0 で通る (probe 因果実験の一次資料)。
   登録較正側の `method` を要求する consumer は probe 自身以外に存在しない。
   **したがって「較正を再登録しないと計算ノードで何も走らない」は成り立たない。**
4. **凍結 floor protocol の live admission は活性化で新規に閉じる。** 移行前は
   歴史検証・live 検証がともに通り、移行後は歴史検証だけが通る。
   同様に新規へ転じる current gate は floor 投入 admission・ratified live launch・
   holdout candidate producer の 3 経路である。
5. **一方、silo 完全検証と prediction seal は活性化以前から別理由で閉じている。**
   silo の公開 `verify-result` は今日すでに
   `correctness provenance values mismatch` で赤であり、原因は module 定数の
   ccbench pin 前進と証拠側 pin の不一致である。current binding 検査には到達しない。

**理由:**
- D272 が「環境だけ進めると live admission の契約 hash が食い違う」と名指しで却下した経路を、
  本 wave の計画がそのまま踏んでいた。実測 4 はその予測が正しいことを確認した。
- 実測 1 と 3 により、活性化を急ぐ根拠 (「これを通さないと何も走らない」) は存在しない。
  期限の圧力が無いなら、既裁定の人間手番を飛ばす理由も無い。
- 活性化 record は create-only の hard-link no-replace で、誤発行を正規経路で巻き戻せない。
  不可逆な発効ほど人間手番の価値が高い。

**却下した選択肢:**
- **上位束を待たずに環境側だけ発効する** — D272 が名指しで却下した経路であり、
  実測 4 の 3 経路が新規に閉じ、床値 v2 へ到達する sanctioned な発行経路も存在しない。
- **活性化はせず既知例外集合の走査領域だけ広げる** — 現時点で ever-active 集合と
  active 集合が一致するため検査内容が 1 bit も変わらず、走査領域を戻す変異が必ず生存する。
  等価変異になり単一理由性を満たせない。
- **`effective_clock.method` の恒真比較だけ先に是正する** — 是正すると期待側 (素朴法) と
  観測側 (方式 α) が不一致になり、活性化前の Pegasus 全 attestation が即座に落ちる。
  活性化と対でしか入れられない。
- **versioned protocol path の seam だけ先に land する** — path と hash の authority は
  人間承認済み上位束の generation record から解決すべきで、
  receipt に選ばせると submitter が検証対象を選べる受理拡大になる。束が未確定のまま作ると
  作り直しになる。

**supersede:** D431 の member inventory 第 2 行は runtime attestation を
「unmet — D143 のユーザー裁定待ち」と書いているが、D143 は 2026-08-16 に択 (b) で裁定済みである。
正しい状態は **「D143 裁定済み (択 b)。positive control の充足は環境世代 g2 の活性化に従属し、
活性化は上位権限束の人間 lockstep 待ち」** である。
登録済み較正を自分の述語へ通す positive control は、g1 が active である限り赤であり、
g2 を active にすれば緑になる。skip / xfail / 期待反転で緑に見せない点は D431 のまま不変。

**研究状態への影響:** 本 D 自体は受理集合・certified 選択・proof chain を 1 件も変えない。
変わるのは、活性化を実施する将来 wave が満たすべき前提条件と、その actor が人間であることの明示である。
