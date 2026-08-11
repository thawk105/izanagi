---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-08-11
wave: dev-wave-t798-t799-finalize
seq: 2
---

## {{D:fold-commit-identity-is-the-authority}}. fold の復旧判定は phase でなく commit identity を権威にする

**決定:** transaction state の `phase` は lifecycle の marker に留め、**復旧時に「この fold は
commit 済みか」を決める権威は fold commit の identity** とする。identity は次の 5 条件の
完全一致で判定する — 単一 parent が `origin.tested_tip` であること、author header が
`<固定 identity> <unix timestamp> <±hhmm>` の厳密形であること、commit message の bytes が
固定文言と一致すること、親との diff が state から導いた期待集合と **path 集合・status・mode・
新 blob OID まで完全一致**すること、既存の宣言 fold 形状検査が受理すること。

**理由:**
- `git commit` の成功と phase の書換えは別の filesystem operation なので、その間で死ぬと
  「`phase=applied` なのに main は fold commit」という相が必ず残る。phase を権威にすると、
  この相は受理表の外側になり復旧できない。
- 上の 5 条件が成り立つなら fold は実際に commit されている。**phase field は検証可能な事実を
  1 つも足していない。** tree が phase と矛盾するとき phase を信じる方が危険である。
- 逆に identity 検査を持たずに phase だけを緩めると、path 形状しか見ない既存の宣言検査では
  mode を変えた手動 commit すら受理してしまう (実装前の敵対レビューが構成した)。

**却下した選択肢:**
- **phase を権威にし、`phase=committed` だけを受理する** — commit と phase 書換えの間の窓が
  復旧不能のまま残る。
- **commit 前に phase を `committed` にしておく** — 窓が「committed と宣言したが commit していない」
  側へ移るだけで、鏡像の問題になる。
- **commit message へ transaction ID を書いて束縛する** — 固定 message 契約と宣言 fold 検査へ
  波及するため、本 wave では採らず独立項へ切り出した。

## {{D:receipt-schema-positional-cutover}}. 追記専用台帳の schema 拡張は位置的 cutover で強制する

**決定:** 追記しかされない耐久 receipt (`docs/spool/FOLDED.md`) の record schema を拡張するとき、
parser は**旧 exact 集合と新 exact 集合の 2 つだけ**を受理し、**新 record が 1 つ現れたら
それ以降の record は新 exact 集合を必須**とする。第三の集合と、混在後の旧集合は拒否する。

**理由:**
- 既存 record を書き換えられない (履歴である) ため、旧集合の受理は避けられない。
- しかし「新 field を個別に optional として読む」形にすると、**cutover 後に書かれた record が
  新 field 無しで正式集合へ入れてしまう** — 検査が黙って無効になる fail-open である。
- 位置的 cutover は file の中身だけで判定でき、外部の marker も時刻も要らず、単調である。

**却下した選択肢:**
- **新 field を optional にして「有れば検査する」** — 上記の fail-open。
- **旧 record を一括で backfill する** — 値を推測することになり、耐久記録を捏造する。
- **schema version 行を file 冒頭へ置く** — 追記専用の形を壊し、既存 consumer 全部に波及する。

## {{D:bind-the-plan-input-closure-not-just-the-head}}. 採番を伴う transaction は入力 closure を束縛する

**決定:** 台帳の採番を含む transaction は、HEAD や target だけでなく**その計画が実際に読んだ
入力の closure** (canonical 台帳・archive・fragment・rotation 閾値・**採番と rendering を行う
engine 自身の bytes**) の hash を束縛し、mutation 前に再計算して照合する。

**理由:**
- 採番の入力には target でないものが含まれる (archive 台帳、見送り台帳、閾値定数)。
  target の before/after だけを束縛しても、**採番の入力が変わったことは検出できない**。
  実際に、archive を変えてから resume させて重複 ID を作れることが前 wave で実測された。
- HEAD の束縛だけでは足りない。同一 commit 内で入力を変えた場合や、HEAD を動かさない writer に
  効かないうえ、**engine の未 commit な書換え**は HEAD を 1 bit も動かさずに採番を変えられる。

**却下した選択肢:**
- **HEAD だけを束縛する** — 上記の 2 経路に効かない。
- **申告値 (caller が渡した値) を束縛する** — 束縛したことにならない。各値は束縛前に実体と照合する。
- **入力ごとに個別の検査を足す** — 入力が増えるたびに検査を足し忘れる。closure は集合で閉じる。
