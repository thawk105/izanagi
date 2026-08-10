| レビュー | # | 重み | 状態 | 根拠 (file:line) |
|---|---:|---|---|---|
| A | 1 | blocker | closed | 推論規則を削除し、「**本 field が定めるのは配分の数値だけ**」「公表用の検定統計量、帰無分布、未調整 `p` 値」を定めないと明記した。`addendum-b.md:122-130`。有限標本妥当性も主張しない。`addendum-b.md:208-212` |
| A | 2 | blocker | closed | `a10` の `T_k` は「**標本数設計のための planning 統計量として定義された**」との非規範参照に限定した。`addendum-b.md:132-138` |
| A | 3 | must-fix | closed | Holm、未調整 p 値、同時区間、両者の対応をすべて `b02` の非定義事項へ移した。`addendum-b.md:122-129`。「**本 field だけでは公表表を生成できない**」とも明記した。`addendum-b.md:144-146` |
| A | 4 | nit | closed | key を逐語で `affects_primary_q: false` に狭めた。`addendum-b.md:107`。さらに `alpha_pub_k` と primary `α_k` は「**別 namespace の別量**」とした。`addendum-b.md:140-142` |
| A | 5 | must-fix | closed | 引上げ時は「**本追補を書き換えるのではなく**」「新しい study と新しい追補」を承認し、旧 blob・過去結果を不変に保つと固定した。`addendum-b.md:89-92` |
| A | 6 | must-fix | closed | 「データを見ずに凍結された」とは主張せず、時点独立性は文面から検証不能とした。`addendum-b.md:222-226`。package も同じ限定へ下げた。`package.md:25-28` |
| A | 7 | must-fix | closed | 内訳を逐語で `検証 1 + pilot 8 + pilot 予備 2 + 本走 13 + 本走予備 2 = 26` に訂正した。`addendum-b.md:81-85`、`package.md:32-34` |
| A | 8 | must-fix | partial | 保留選択肢と公表手続きの別裁定は追加された。`package.md:119-129,173-178`。しかし未接続の `alpha_pub_1` を含む現追補の承認をなお推奨し、primary を前進可能としている。`package.md:175-176` |
| B | 1 | blocker | regressed | 元の閉集合違反は削除された。`addendum-b.md:122-130`。しかし削除後は `alpha_pub_1` が「適用先を持たない」。`addendum-b.md:144-146`。それでも package は現追補の承認・前進を推奨する。`package.md:175-176` |
| B | 2 | blocker | partial | pilot 条件を追加しない点は「**`submit_main` の投入前だけ**」「pilot の受理条件を追加しない」と修正した。`addendum-b.md:55-57`。一方、台帳 path・entry digest・予約 commit を受領証の必須項目とする新 schema は残った。`addendum-b.md:181-185` |
| B | 3 | blocker | closed | primary foreign key を削除し、「primary 側の予約 entry を公表側の受理条件にしない」と明記した。`addendum-b.md:171-175`。root は caller・親系列 ID を入力にせず、`(root, ordinal)` を create-only で一意化する。`addendum-b.md:165-169,177-179` |
| B | 4 | must-fix | closed | 「承認発話それ自体では発効しない」「canonical 台帳へ fold した commit 以後」と統一した。`addendum-b.md:15-17`、`package.md:22-23`。README も未凍結・未発効とした。`README.md:8-10` |
| B | 5 | must-fix | closed | 3 成果物とも追補 A の内訳へ揃った。`addendum-b.md:81-85`、`package.md:32-34`、`README.md:17-21`。追補 A の正本は `addendum-a-reissue.md:607-619` |
| B | 6 | must-fix | closed | README は値を「**未承認**」とし、pilot 前凍結の時点独立性を主張しない。`README.md:17,29-31`。`q` 非影響も primary に限定した。`README.md:27-28`。R2 erratum の実効欠落も明記した。`README.md:52-55` |
| B | 7 | must-fix | partial | 別の summable schedule、非規範参照、公表手続きの新 core、primary 非参照、承認保留が選択肢へ追加された。`package.md:83-88,99-126,138-140,173-178`。ただし B8(a) の推奨は未確定の公表手続きを main 前提から外しており、安全な帰結になっていない。`package.md:175-176` |
| B | 8 | nit | partial | package は「**T-139 の core を対象とする**」erratum に限定した。`package.md:160-163`。しかし一次資料 `s4-adjudication.md` の「`output/insights/` 配下の erratum は…だけ」という無限定の偽記述は残っている。`s4-adjudication.md:23-24` |

## 新規所見

### [blocker] `b02` の適用先が無いまま、現 study を発効・前進可能とする退行

[判定]

`b02` から未承認の推論規則を削ったこと自体は正しい。しかし修正後は `alpha_pub_1 = 0.025` に適用先がなく、公表表を生成できない。それにもかかわらず package は現追補の承認を推奨し、「本走の primary 判定はこれで前へ進められる」としている。

これは単なる「後で実装する」欠落ではない。未調整 p 値・多重調整・区間の選択は規範そのものであり、本走データを見た後まで未固定なら事前登録にならない。さらに core §14 は、新 core が必要なら別 study と定めているため、後から現 study の空欄を新 core で埋めた扱いにはできない。

[根拠: `addendum-b.md:144-146`; `package.md:10-11,119-126,173-181`; `preregistration.md:313-316,438-441`]

[成果物影響]

現 package の推奨どおり承認すると、追補 B は発効可能なのに、公表する調整済み p 値・同時区間・有意セル集合を一意に再生成できない。main を先行させれば、公表手続きの結果依存選択経路が残り、材料レポートと proof chain が閉じない。

[最小の直し方]

B8(a) の推奨を撤回する。少なくとも次のいずれかへ固定する。

- B4 の権威ある公表手続きと、それに対応する新 study の core・追補をデータ投入前に凍結するまで、現追補 B は保留する。
- `b01`〜`b03` を設計入力として先に裁定する場合も、現 study の発効済み追補・`submit_main` の十分条件とは扱わず、公表手続きが固定されるまで main admission を拒否する。

package 冒頭の「3 本で完結」も、現状は完結していない旨へ直す必要がある。

## 残存 blocker

### [blocker] レビュー B #2 の受領証 schema 拡張が残っている

[判定]

pilot admission の縮小は解消したが、`b03` は依然として、公表台帳の path・予約 entry digest・予約 commit を raw receipt の必須項目にし、validator の新しい照合条件を設けている。これは「正規の根の同定方法」を越えて core §12 の必須 schema と受理集合を変更する、元所見の未修正部分である。

[根拠: `addendum-b.md:181-185`; `preregistration.md:278-297,339-343`]

[成果物影響]

core 準拠の receipt でも新規項目が無ければ main が拒否される。ユーザーは root の同定方法だけを承認したつもりでも、実際には receipt schema と validator の受理集合まで変更することになる。

[最小の直し方]

`b03` から受領証必須項目と validator schema の規定を削除し、canonical root、caller 非選択、create-only の `(root, ordinal)` 一意性だけに限定する。追加 receipt schema が必要なら、新 core を伴う別 study の裁定対象へ送る。

## 退行検査

- exact-key は一意である。fields は `addendum-b.md:61` の直後から `:201` の直前までで、字義 grammar に一致する `### ` 見出しは `b01` (`:63`)、`b02` (`:94`)、`b03` (`:148`) の3本だけ。集合は正確に `{b01, b02, b03}`。
- `b03` の primary 参照削除後も、規範上の reset 防止は成立する。root は親系列 ID・caller 引数を入力にせず (`addendum-b.md:165-169`)、canonical 公表台帳で `(root, ordinal)` を create-only に一意化する (`:177-179`)。ただし active gate は未実装であることも草案自身が認める (`:192-195`)。
- 資源内訳は追補 A `a10` の `1 + 8 + 2 + 13 + 2 = 26` と一致する。`addendum-a-reissue.md:607-619`。core §11 は総数 26 のみを固定し、旧 `8 + 2 + 13 + 3` を目安と明記しているため矛盾しない。`preregistration.md:271-273`
- admission deny は文面上 `submit_main` 前に限定されている。`addendum-b.md:55-57,73-75,184-190`。pilot を拒否する経路は修正後本文には残っていない。
- README は概ね主張を適切に弱めたが、package の「3 本で完結」と B8(a) 推奨は実態より強い。`package.md:10-11,175-176`

## 総括

closed / partial / regressed: **11 / 4 / 1**（not-applicable: 0）

残る blocker 件数: **2 件**

GO / NO-GO: **NO-GO — 現状の未凍結草案 + 承認パッケージを、そのままユーザーへ提示して承認を勧めてはならない。**

実走・build・テストは行っていない。read-only での静的読解のみであり、pytest 緑は主張しない。
