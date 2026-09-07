---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-09-08
wave: dev-wave-t2396-a1-receipt-oslink
seq: 2
---

## {{D:a1-receipt-file-publish-form}}. A-1 の受領証 file は staging + `os.link` に統一し、directory 公開は現行のまま残す

**決定:** D1732 が group submission receipt について決めた「完成した staging への `os.link`」を、
**A-1 driver が公開する受領証 file の共通形**とする。`complete` の completion receipt (v2 / v3 の
両経路) も同じ publisher を通す。materialize の bundle は **directory** を公開するため
`os.link` を使えず、現行の probe + fallback をそのまま残す。`receipts/submission-failure.json` は
本決定の対象外とする。staging の basename は kind ごとに分ける (submission と completion)。

**理由:**

- D1732 が「completion receipt と materialize 側も同族として同じ形へ棚卸しする」と定めた。
  棚卸しの結果、file は同じ形にでき、directory はできない、という非対称が実体だった。
- completion receipt は完成名を `O_EXCL` で直接開いてから bytes を書いていた。書込み途中で止まると
  **千切れた bytes が create-only 名を占有し、その attempt の proof chain を二度と閉じられない。**
  submission 側に staging がある理由と同型の欠陥である。
- materialize の staging は `mkdir` で作る directory であり、通常の user process は directory の
  hard link を作れない。同じ primitive へ置換できないことはコード上の事実である。
- kind ごとに staging basename を分けるのは、将来 basename の共通 prefix が伸びたときの
  衝突を防ぐためで、公開の受理集合は変えない。

**却下した選択肢:**

- 素の rename への退避 — 既存先を黙って上書きし create-only の排他性を落とす (D1732 が却下済み)。
- `O_EXCL` で完成名へ直接書く — 部分公開の窓を作る (D1732 が却下済み)。
- submission 受領証にも file system probe と機構選択の evidence を持たせる —
  `os.link` は Lustre でも tmpfs でも通るので選択肢が要らない。発火経路の無い条件付き機能になる。
- `receipts/submission-failure.json` まで同じ形へ広げる — D1732 の射程外であり、
  失敗台帳の意味と retry policy が別論点になる。

## {{D:a1-published-receipt-cleanup-contract}}. hard link 公開後の staging 撤去は宛先の同一性を前提にし、撤去失敗で公開を巻き戻さない

**決定:** 受領証を hard link で公開した後の staging 撤去は、**宛先が存在し、その `(st_dev, st_ino)` が
staging identity と一致すること**を unlink の前提にする。不成立なら staging を unlink せず
fail-closed で止める。撤去が失敗した場合は専用の例外型で報告し、**完成名を巻き戻さない**。
rc は非ゼロのままとし、message で「受領証は公開済みである」ことを明示する。v3 submit は
この例外では `submission-failure.json` を書かない。

**理由:**

- rename 公開では公開後に staging 名が消えるので撤去処理そのものが無かった。hard link 公開では
  **staging と宛先が同じ inode になる**ため、公開後に第三者が
  `unlink(staging)` と `rename(destination, staging)` を行うと、staging の identity 照合が通ってしまい
  **撤去が受領証の最後の link を消す。** 本 wave の機構変更が新しく作る破れであり、
  宛先の同一性を要求することで決定的な順序を閉じる。
- 既に consumer から見えた create-only の受領証を消す方が、staging を残すより危険である。
- 公開済みなのに失敗台帳を作るのは虚偽の記録になる。一方で rc を 0 にすると、
  破れた「staging を残さない」不変条件を黙って通すことになる。両方を避ける唯一の形が
  「非ゼロで報告し、失敗台帳は書かず、公開済みであることを message に書く」である。

**却下した選択肢:**

- 撤去失敗を非致命の診断にして rc=0 を返す — 不変条件の破れを黙らせる。
- 撤去失敗時に完成名を unlink して「公開失敗」へ戻す — 公開済みの受領証を消す。
- 宛先確認と unlink の間の競走まで閉じる — 非協調な同 uid writer を前提とし、その writer は
  受領証を直接消すこともできるので file 操作では閉じられない。threat model 自体の裁定へ返す。
