# 段 6 敵対レビュー — レンズ B

## 所見

### 1. [blocker] `b02` が未固定の公表推論規則を新設している

[判定]  
構成要素ごとの判定は次のとおり。

- 6 セル、周辺統計量: 追補 A `a10` の参照。
- 周辺 p 値式: planning model を公表推論へ転用する新しい規範。
- Holm: 元の Q7 は「Holm または closed testing」であり、Holm への一意な固定は新規。
- Holm 閾値列: Holm を選んだ場合の算術的導出。
- `C_w(q)` の同時区間: `a11` と core §16 の参照として読める。
- R5 正分母 guard: 既存ユーザー裁定の参照。

したがって syntactic key が `b02` でも、意味上は「spending 関数の数値割当て」を越えている。

[根拠: file:line]

- `addendum-b.md:124-134` — 「family と統計量は既存契約」「`p_k = 1 − T_{J−1}(T_k)`」「Holm の閾値列は…」
- `addendum-a-reissue.md:701-703` — 「planning model のもとで `T_k` は…非心 t 分布に従う」
- `2026-08-03_t338-rf-statistical-design/package.md:216-220` — 「workload 別・cell 別の主張も公表するなら Holm または closed testing」
- `preregistration.md:341-343` — `b02` に委譲されたのは「個別公表系列の累積 spending 関数の数値割当て」
- `package.md:123-132` — 公表手続きの正本文書が無く、追補 B は正本になれないと自認している。

[成果物影響]  
材料レポートの未調整・調整済み p 値、有意セル集合、個別公表の受理集合が変わる。primary の `q` 自体は変えなくても、公表上の偽陽性制御を一意に再導出できない。

[最小の直し方]  
`b02` を spending の式・domain・未使用 tail だけに縮める。6 セル等は非規範的な参照に限定し、p 値式・Holm 選択・公表 protocol は削除する。B3 は「既存参照」と「未固定の p 値・多重調整」を分割し、後者が権威ある新 core で決まるまで公表表を生成不能とする。

---

### 2. [blocker] `b03` が pilot admission と受領証 schema を追加している

[判定]  
「pilot 1 本目より前」という時相境界は既存契約の参照ではなく新規制約であり、core の `pilot_admission: requires_addendum_a` を狭める。公表台帳の path・entry digest・予約 commit の必須記録も、新しい receipt 要件である。

`(publication_family_root, ordinal)` の一意性は `b03` の自然な実装範囲に入りうるが、`primary_reservation_entry_digest` の一意性は別の新規条件である。

[根拠: file:line]

- `addendum-b.md:185-188` — 「pilot 1 本目の投入より前に済ませる」
- `addendum-b.md:196-202` — 「一意性の要件は 2 本」「受領証は、台帳の path・予約 entry の digest・予約 commit を必須記録」
- `preregistration.md:7-8` — `pilot_admission: requires_addendum_a`、`main_admission: requires_addendum_a_and_b`
- `preregistration.md:388-414` — pilot resolver の要件は core と追補 A に閉じ、追補 B は `submit_main` で追加される。
- `preregistration.md:278-297` — raw receipt の必須項目を core §12 が列挙している。

[成果物影響]  
core と追補 A を満たす pilot が、公表予約の不在だけで新たに拒否される。試行台帳の必須 schema と validator の受理集合も変わる。

[最小の直し方]  
`b03` から pilot 前予約と receipt schema の新設を外す。追補 B の main admission より前という既存境界へ戻す。より早い予約や追加 receipt field が必要なら、core を変える別 study として裁定する。

---

### 3. [blocker] primary 予約との foreign key は `a13` の利用に留まらず、別台帳間の新しい拘束である

[判定]  
primary 予約の存在・digest・ordinalを読むこと自体は既存 `a13` の利用である。しかし、公表 entry にその digest を必須保持させ、ordinal exact 一致と digest 一意性を公表側の受理条件にする部分は新規契約である。

書込み・残高共有がないため物理的には別台帳だが、ordinal 系列は lockstep に結合される。U8 はこの結合を裁定していない。

[根拠: file:line]

- `addendum-b.md:182-192` — 「別の canonical 台帳」「primary 予約 entry の digest を必須の read-only 親参照」「ordinal は…exact 一致」
- `addendum-b.md:196-197` — `primary_reservation_entry_digest` にも一意性を要求。
- `addendum-a-reissue.md:919-930` — `a13` が要求するのは primary 側の create-only 予約と `(family_root, ordinal)` の非重複。
- `preregistration.md:248-250` — U8 は「primary 系列と個別公表系列に別々の累積台帳」を要求。
- `package.md:96-103` — B4 自身がこの結合を未裁定事項としている。

なお、`package.md:97-98` の「完全に独立だと公表側だけが 1 本目を名乗れる」は成立しない。草案自身の canonical public root・caller 非選択・create-only 予約だけで、その経路は既に閉じられる（`addendum-b.md:176-186`）。

[成果物影響]  
正規の公表台帳で一意に予約されていても、primary digest の欠落・ordinal の不一致だけで公表 entry と本走が拒否される。試行台帳の親子関係と、両系列で受理される ordinal 集合が変わる。

[最小の直し方]  
`parent_reference`、primary digest の一意性、ordinal exact 一致を削り、公表台帳自身の canonical root と create-only ordinal だけで閉じる。系列間の対応が必要なら、U8 と core の変更を伴う別 study として裁定する。

---

### 4. [must-fix] `authority: none` と発効時点の説明が成果物間で一致しない

[判定]  
`addendum-b.md` 本体は、発効点・自己 digest 禁止・core 三つ組を追補 A と同等以上の強度で記述している。一方 package は一箇所で「ユーザー承認時点」に発効すると読め、README は未承認値を「確定」と呼んでいる。

[根拠: file:line]

- `addendum-b.md:16-18` — 「canonical 台帳へ fold した commit 以後にのみ効力」
- `package.md:22-23` — 「承認をいただいた時点で…文書としては効力あり」
- `package.md:138-142` — 後段では「承認する決定を台帳へ畳んだ commit 以後」と正しく書く。
- `README.md:8-10` — 「ここには凍結した逐語を置く」
- `README.md:16` — 「確定した数値・手続き」
- `README.md:46` — 「凍結していない」

[成果物影響]  
ユーザー発話後、fold 前の blob を resolver・材料レポート・台帳が発効済み参照として扱う時間窓が生じる。

[最小の直し方]  
全成果物を「未承認草案」「承認だけでは未発効」「canonical fold commit 以後に発効」へ統一する。「確定」「凍結した逐語」を「草案で提案する値」「未凍結の逐語」に置換する。

---

### 5. [must-fix] `b01` の資源内訳が発効済み追補 A と食い違う

[判定]  
草案と README/package は `8 + 2 + 13 + 3` を候補 1 本分としているが、追補 A の確定内訳は検証割当て 1、本走予備 2 を含む `1 + 8 + 2 + 13 + 2 = 26` である。core 自身も旧内訳を「目安であって確定値ではない」と限定している。

[根拠: file:line]

- `addendum-b.md:85-86` — 「pilot 8 + 予備 2 + 本走 13 + 予備 3」
- `package.md:29-30`、`README.md:17-19` — 同じ内訳を根拠として再掲。
- `addendum-a-reissue.md:609-618` — 「検証割当て 1」「本走…予備 2」「合計 26」
- `preregistration.md:271-273` — `8 + 2 + 13 + 3` は「目安であって確定値ではない」。

[成果物影響]  
試行台帳で検証割当てを落とす、または本走予備を 3 と誤記する。26 割当ての消費・予備関係・投入可能 slot が食い違う。

[最小の直し方]  
3 成果物を追補 A の `1 + 8 + 2 + 13 + 2` に揃える。`K=1` はこの内訳からの科学的導出ではなく、26 上限に対応させた governance 提案であることだけを根拠に残す。

---

### 6. [must-fix] README の「結論」に検証不能・未裁定の主張が混ざっている

[判定]  
README の各結論行を照合した結果は次のとおり。

| README | 判定 |
|---|---|
| 14-15 exact-key 一意 | 支持あり。字義解析でも確認できた |
| 16「確定した」 | 盛っている。未承認 |
| 17-19 `b01` | 値は提案だが資源内訳が誤り |
| 20-22 `b02` | 級数和は正しい。FWER 主張は未固定の公表検定が有効であることに条件付き |
| 23-25 `b03` | 未裁定 B4 を「正規の根」として確定的に記述しており盛っている |
| 26-28 pilot 非依存 | 成果物内の証拠がなく、草案自身が検証不能と認める |
| 29-30 `q` 非影響 | `q` を変更しない点は支持あり。「両者に触れない」は字義上偽で、本文が `a11/a13` を明示参照 |
| 31-36 6 セル・統計量 | `a10` に逐語があり支持あり |
| 37-39 `0.05` 全額案の棄却 | 数学例は支持あり |
| 40-41 `δ_MC` 撤回 | `a12` が Monte Carlo familywise error と定義しており支持あり |
| 42-45 R2 blocker refuted | 裁定は確認できたが、erratum 未発行中なので実効契約上の blocker は消えていない |
| 46 未凍結 | 支持あり |
| 47-48 core bytes・実装面ゼロ | 静的追試で支持あり |

[根拠: file:line]

- `README.md:26` — 「pilot の結果に一切依存しない」
- `addendum-b.md:242-244` — 「データを 1 点も見ずに書かれたことは、本書の文面からは検証できない」
- `README.md:42-45` — R2 blocker を「refuted」としつつ erratum 未発行を併記。
- `addendum-a-reissue.md:829-833` — core §7 の義務との差を「本 wave は解消していない」。

[成果物影響]  
時点独立性や erratum 適用を未検証のまま、材料レポートが「事前登録どおり」と参照する proof chain を作りうる。

[最小の直し方]  
「式は pilot raw を入力に取らない」と「実際に raw を見る前に凍結された」を分離する。後者は fold commit・pilot 初回投入時刻・予約 commit で未検証と書く。R2 は「裁定済み・erratum 未実施・現時点の gate は未解消」とする。

---

### 7. [must-fix] package の選択肢が非網羅的で、推奨側へ誤った帰結で誘導している

[判定]  
少なくとも B1・B2・B3・B4・B6 は網羅的でないか、非推奨案の帰結が過大である。

- B1: cap を大きくしても、別の資源上限まで自動承認されるわけではない。
- B2: `0.05/(k(k+1))` と初回全額のほかにも、幾何配分等の summable schedule がある。
- B3: 既存の6セル・統計量と、未固定の p 値・多重調整を別々に裁定する選択肢がない。
- B4: canonical な独立公表台帳だけでも reset を防げるため、「完全独立なら抜け道が残る」は誤り。
- B6: 推奨 (a) の「実装 wave で1本へ集約」が非権威の実装資料なら正本欠落を解消せず、権威を持たせるなら同節が拒否する「第3の権威」になる。

[根拠: file:line]

- `package.md:45-48` — 大きい cap を「資源の承認が無い候補まで投入可能に見える」とだけ説明。
- `package.md:60-65` — spending の選択肢が2つだけ。
- `package.md:84-89` — 6セルから p 値・Holm・区間までを一括選択にしている。
- `package.md:97-103` — foreign key が無いと reset できると説明。
- `package.md:129-132` — 実装 wave での集約を推奨する一方、独立 protocol を「第3の権威」として拒否。

[成果物影響]  
`b01`、`alpha_pub_1`、将来 tail、試行台帳の親子関係、公表 p 値・区間の受理集合について、ユーザーが実在する中間案を選べない。

[最小の直し方]  
各問いを独立パラメータへ分割し、少なくとも「別の summable schedule」「foreign key 無しの canonical 公表台帳」「既存参照だけ採用して未固定の公表推論は停止」を追加する。非推奨案の帰結は資源 gate と統計 gate を分けて記述する。

---

### 8. [nit] s4 の erratum 実測記述が字義上は偽

[判定]  
「`output/insights/` 配下の erratum は1本だけ」は字義どおりには偽であり、他 study の erratum が複数存在する。意図は「T-139 core を対象とする既発行 erratum」だと推定でき、その限定なら §15 用1本だけで、§7 用は見つからなかった。

[根拠: file:line]

- `s4-adjudication.md:23-24` — 「`output/insights/` 配下の erratum は `erratum-core-s15.md` だけ」
- `2026-08-06_t401-racct-permanent/brief-erratum-1.md:1-5` — 別の erratum が実在。
- `2026-08-08_t139-addendum-a/erratum-core-s15.md:1-8` — T-139 の既存 erratum は core §15 用。

[成果物影響]  
直接の certified 値は変わらない。ただし approval manifest の erratum exact set を説明する際、repo 全体列挙と study 対象列挙を混同しうるため nit とする。

[最小の直し方]  
「T-139 の当該 core を target とする発行済み erratum は §15 用1本だけ」と限定する。

## 追試結果

### exact-key

字義 grammar での fields 範囲は `addendum-b.md:62-222`。検出された `### ` 見出しは次の3本だけだった。

- `addendum-b.md:63` — `b01`
- `addendum-b.md:96` — `b02`
- `addendum-b.md:154` — `b03`

欠落・余剰はない。fields 内 fenced block に `^## ` / `^### ` は0件。`---` は line 221 にあるが見出しではない。引用は `> ` で始まり、YAML 内の key も `### ` で始まらないため field と解釈される経路はない。

### core §13・§14・§9

- 「投入前 admission deny」は core §15 の resolver failure と同型であり、§9 の新しい attempt failure 分類とは数えない。
- 開始後は既存の reject/判定不能だけへ写し、予備置換・ordinal 解放・新分類を禁じているため、否定検査8との直接衝突はない。
- 問題は分類名ではなく、`b03` が新しい admission predicate を閉集合外から追加している点である。

### s4 の独立実測6件

1. `a10` の6成分・`T_k` 定義: 追試一致（`addendum-a-reissue.md:686-699`）。
2. 追補A fields内 fenced heading 0件: 全範囲 `75-946` を走査して追試一致。
3. R2裁定済み: 追試一致（`docs/archive/worklog-phase3-0809-327-328.md:463-472`）。
4. R2 §7 erratum未発行: T-139対象に限定すれば追試一致。repo全体の erratum が1本という字義は不一致。
5. R5裁定済み: 追試一致（同 `:472-473`）。
6. core三つ組: review HEAD は `7552e322783fcfd1202fcf1c338271d16ffdad20`。`7552e322` と `88d68f9…` の双方で core blob SHA-256 は `ac939af4de87dff0cd3964e37cef975d57919a709d57f4e9523c8b6a9fcd60e9`、`88d68f9…` は review HEAD の祖先。追試一致。ただし将来 checkout の不変条件ではない。

### 実装面

対象ディレクトリにあるのは Markdown 8ファイルだけだった。コード・テスト・実行可能 script・機械設定はない。実装面ゼロは追試一致。

一方、`addendum-b.md:201-202` の receipt 必須項目・validator 動作は将来 wave の単なる責務説明を越えて現在の規範を設定しており、所見2の閉集合違反に含めた。

## 総括

blocker 件数: **3件**

最も重い1件: **`b02` が未固定の p 値・Holm 公表手続きを既存契約として取り込み、材料レポートの有意集合を閉集合外から決めていること**

GO / NO-GO: **NO-GO**

実走・build・pytest・その他のテストは一切行っていない。ファイル書換えも行っていない。