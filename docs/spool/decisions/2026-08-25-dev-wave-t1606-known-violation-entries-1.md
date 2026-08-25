---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-08-25
wave: dev-wave-t1606-known-violation-entries
seq: 1
---

## {{D:append-only-replaces-literal-mirror}}. known-violation の逐語 mirror は append-only 履歴不変条件で置換する

**決定:** D743 が着手条件とした「逐語 literal mirror の置換」は、同決定が列挙した 5 検査
(複合 key、tracked regular file / HEAD 一致、全 entry の実 commit 照合、公開 stdout の逐語検査、
投影外 consumer 閉包) **だけでは成立しない**。`tools/known_violations/**` を append-only とし、
着地済み entry file の blob 変更・削除・rename を git 履歴全体から拒否する検査を必須で加える。
この検査は引数なし (authoritative) の全史監査から呼び、land の全史監査関門で発火させる。

**理由:**

- 5 検査はいずれも **data 自身から導いた値どうしの照合**であり、`ruling` と `note` の真正性を
  固定しない。filename に本文の SHA-256 を入れても、書き換える側が新しい正しい digest を
  再計算できるため認証にならない。1 entry を書き換えて rename するだけで、全検査・全史監査・
  land 受領証が偽造後の値を自己追認する (段 3 の敵対相談が実証)。
- 逐語 mirror が担っていたのは「改竄に 2 面の同時編集を要求する」ことだった。append-only は
  「着地後の改変を履歴で検出する」ことで同じ目的を達し、**共通編集面を一切作らない**。
  したがって本 wave の目的 (並行 wave の台帳競合の削減) と両立する。
- 費用は無視できる。path 限定 `git log` は 6047 commit の repo で 0.87 秒 (実測)。

**射程と限定:**

- 呼ぶのは引数なしの authoritative 全史監査だけとする。`--message-file` は lazy 契約を壊すため、
  `--range` は合成 repo を監査する既存契約を壊すため、いずれも呼ばない。
- 新規 entry の追加 (`A`) は受理する。拒否するのは変更・削除・rename・file type 変更である。
- git が使えない・`git log` が非 0・履歴が取れない場合は fail-closed とする。
  「履歴が無いので通す」経路を作らない。

**却下した選択肢:**

- **5 検査だけで mirror を畳む** — 裁定根拠と公開 note の偽造を緑のまま許す。防壁の純減であり
  絶対規律 2 に反する。
- **期待 digest の一覧を別 file に置く** — 認証にはなるが、登録のたびに共通編集面を編集する
  ことになり、mirror と同じ競合を再生産する。
- **land 受領証へ registry 束縛 field を足す** — `tip_sha` が registry tree を推移的に既に
  束縛しており冗長。既存 test の位置指定 constructor 4 箇所を壊す割に得るものがない。

## {{D:no-data-derived-count-pins}}. 台帳の置換テストに data 由来の絶対数を書かない

**決定:** entry 単位格納へ移した台帳の検査に、`entry 数 == 53`、`distinct SHA == 52`、
kind 内訳、note 非空件数のような **data から導かれる絶対数の pin を置かない**。
網羅性は「loader の全 entry」と「監査が返した集合」の多重集合完全一致で表現する。

**理由:**

- 件数を test へ書くと、登録を 1 件足すたびにその数値を編集することになり、台帳末尾を
  directory へ分解して除いたはずの**共通編集面が test 側へ復活する**。
- さらに悪いことに、並行する 2 wave が両方 `53 -> 54` へ直すと、data は綺麗に union されて
  55 entry になる一方 test は 54 を期待するため、**競合なしで赤になる**。手解決の必要な
  競合を、検出しにくい形の赤へすり替えるだけになる。
- 判断基準は「新しい登録を 1 件足したときに、その pin の編集が要るか」である。要るなら
  共通編集面であり禁止、要らないなら (歴史上の固定 subset を pin する検査など) 許す。

**却下した選択肢:**

- **件数 pin を残す** — 上記のとおり wave の目的を打ち消す。
- **固定 SHA 一覧をすべて撤去する** — 過去 commit の固定 subset を監査する検査は、
  新規登録で編集を要求しないため共通編集面ではない。撤去は被覆の純減になる。
