結論から言うと、段 2 プランはそのまま採ってはいけない。最大の破れは、D1649 の逐語を外して parser を通す新しい値を発明している点と、D1641 が確定した実体値を旧い「決定主体の案」まで確定したかのように扱う点である。

## 所見 1 — `開始時刻 = 予定日時の事前指定なし` は未授権の新規規範

(i) **主張**

発効版の値として `予定日時の事前指定なし` を書く案は、D1649 と矛盾する。採るべきなのは D1649 の逐語であり、段 2 プランの parser 回避案ではない。

(ii) **現物の逐語根拠**

D1649 は明示的に、

> 「欄は `未記入` のままでよく、実際の開始時刻は実走成果物側の記録だけを正本とする」

と決めている。[rulings.md:86](</home/SFC/tanab/.claude/jobs/74c07adf/tmp/wave-t2140-t2414/verbatim/rulings.md:86>)

D1812(b) が追加したのは、

> 「開始予定日時は固定日時を指名せず」  
> 「実投入時刻を投入時に追記する」

までである。[rulings.md:7](</home/SFC/tanab/.claude/jobs/74c07adf/tmp/wave-t2140-t2414/verbatim/rulings.md:7>)

対してプランは、

> 「発効版では固定日時の代わりに `…開始時刻 = 予定日時の事前指定なし` と記す」

と新しいセル値を規範化し、総括ではその理由を「現行 parser の sentinel 拒否との両立」と明記している。[stage2-plan.md:43](</home/SFC/tanab/.claude/jobs/74c07adf/tmp/wave-t2140-t2414/stage2-plan.md:43>)

これは裁定の反映ではなく、裁定と実装の不整合を文書側の新値で埋める追加判断である。

(iii) **放置したときに何が壊れるか**

`未記入` を非 sentinel の説明文へ替える将来規範は、他欄が埋まったときに admission の受理集合を実際に広げる。D1649 が許した状態と異なる値で発効でき、§5 の受理状態が変わる。

parser と D1649 が両立しないなら、この docs-only wave で第三の値を発明してはならない。D1649 を優先し、実装との不整合は別の明示裁定なしには解消できない。

(iv) **判定**

**real — must-fix**

## 所見 2 — D1641 の床値測定認可を、正式標本の認可へ拡張して読める

(i) **主張**

scope 2 の「測定は D1641 により認可済み」は対象を限定しておらず、B-4 正式標本の実走まで認可済みに見える。D1641 / D1477 の逐語が認可しているのは between-run floor の測定である。

(ii) **現物の逐語根拠**

D1641 の表題は、

> 「B-4 床値の担当 3 者は……測定を認可する」

であり、決定 2 も floor 手続きの中の認可である。[rulings.md:111](</home/SFC/tanab/.claude/jobs/74c07adf/tmp/wave-t2140-t2414/verbatim/rulings.md:111>)

D1477 も、

> 「床値 (between-run floor) の発効に要る人間手番 4 件」

と対象を限定する。[rulings.md:185](</home/SFC/tanab/.claude/jobs/74c07adf/tmp/wave-t2140-t2414/verbatim/rulings.md:185>)

一方、プランは §5.1 の正式実走の開始時刻項へ、限定なしに、

> 「測定は D1641 により認可済み」

と書く。[stage2-plan.md:43](</home/SFC/tanab/.claude/jobs/74c07adf/tmp/wave-t2140-t2414/stage2-plan.md:43>)

対象文書の §6 は「1 つでも未充足なら実走しない」であり、正式標本には §5 全欄と全前提条件が別途必要である。

(iii) **放置したときに何が壊れるか**

この文を正式標本の認可と読むと、§5・§6 未充足のまま primary outcome を生成できる。そうなれば発効版が結果より先だったという事前登録の根拠が失われ、B-4 レポートを登録追試として受理できない。

末尾の「本 wave では実走を許可しない」と矛盾しており、定型宣言では射程の広い本文を打ち消せない。

(iv) **判定**

**real — must-fix**

## 所見 3 — D1641 が確定したのは 12 項目の実体値であり、旧い「決定主体の案」ではない

(i) **主張**

プランは「上の割り当て表の 12 行は採否待ちではない」と書くが、直前の表は実体値ではなく「決定主体の案」である。D1641 決定 3 が確定したのは各項目の具体値であり、旧表の担当主体をそのまま採用したのではない。

(ii) **現物の逐語根拠**

旧表は、実行 site、セル集合、統計関数などの決定主体を多数「ユーザー」としている。[対象文書:976](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2140-t2414-b4-prereg-rulings/docs/phase3-b4-reflux-ablation-preregistration.md:976>)

旧手続きも、

> 「AI は……測定実行者・証拠の承認者・floor 欄の記入者にはならない」  
> 「ユーザーの採用裁定の後」

としている。[対象文書:937](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2140-t2414-b4-prereg-rulings/docs/phase3-b4-reflux-ablation-preregistration.md:937>)

しかし D1641 は、

> 担当 3 者を `thawk105` とし AI が操作する  
> calibrator 出力の承認は AI  
> 採用裁定は測定後に AI が行う

と決め、そのうえで 12 項目の具体値を列挙している。[rulings.md:113](</home/SFC/tanab/.claude/jobs/74c07adf/tmp/wave-t2140-t2414/verbatim/rulings.md:113>)

D1695 の射程は n を 59 から 62 に変え、5% 欠測許容を維持することだけである。[rulings.md:153](</home/SFC/tanab/.claude/jobs/74c07adf/tmp/wave-t2140-t2414/verbatim/rulings.md:153>)

プランはこれらを区別せず、

> 「上の割り当て表の 12 行は採否待ちではない」  
> 「証拠と採用裁定の要求は変わらない」

とする。[stage2-plan.md:65](</home/SFC/tanab/.claude/jobs/74c07adf/tmp/wave-t2140-t2414/stage2-plan.md:65>)

(iii) **放置したときに何が壊れるか**

旧表の「ユーザー」と D1641 の AI 委任が両方現役に見える。floor 成果物の確認・採用・§5 転記について、正しい委任下の成果物を拒否するか、逆に誤った主体の承認を正当化する。これは floor pin と、その floor を参照する primary verdict の参照系を変える。

「既裁定の反映」と書くことで、実際には裁定済み内容と矛盾する旧担当規則まで確定済みに見せている。

(iv) **判定**

**real — must-fix**

## 所見 4 — D1812(a) の「その artifact」は primary outcome の出現だけを覆う

(i) **主張**

D1812(a) を、同じ §5.1 にある母集合欄の「その artifact」に波及させてはならない。現プランの挿入位置自体は primary outcome の直後なので、この点では射程超過していない。

(ii) **現物の逐語根拠**

母集合欄は、

> `analysis_manifest` の artifact path・sha256・行数  
> `scheduled_attempt_registry` の artifact path・sha256

を要求する。[対象文書:193](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2140-t2414-b4-prereg-rulings/docs/phase3-b4-reflux-ablation-preregistration.md:193>)

別の primary outcome 欄は、

> 「その artifact path と sha256」

とだけ書く。[対象文書:203](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2140-t2414-b4-prereg-rulings/docs/phase3-b4-reflux-ablation-preregistration.md:203>)

D1812(a) の「path と sha256 の 5 member」と、理由の「consumer receipt では新 producer が要る」は、§5 に既記入の 5 source file とだけ対応する。manifest・registry・行数を要求する前者には対応しない。[rulings.md:7](</home/SFC/tanab/.claude/jobs/74c07adf/tmp/wave-t2140-t2414/verbatim/rulings.md:7>)

(iii) **放置したときに何が壊れるか**

もし前の出現にも広げれば、母集合の実体 manifest・registry が無いまま、source file 5 本で母集合欄を埋められる。予定 attempt の全件記録と結果後の選び直し防止が消え、報告集合と verdict が変わる。

ただし現プランは primary outcome の逐語アンカー直後だけへ入れているため、現在の案にこの破れはない。「§5.1 全体の『その artifact』」と一般化しないことが境界である。

(iv) **判定**

**疑い — 現プランについては反証済み、must-fix ではない**

## 所見 5 — 「1 つも緩めない」は発火条件ではなく、矛盾を隠す恒真宣言になっている

(i) **主張**

各追記末尾の定型文は、独立した保証として何も拘束していない。せいぜい解釈方針であり、先行文が受理値や認可範囲を変更していれば、その変更は残る。

(ii) **現物の逐語根拠**

絶対規律は、敵対監査で、

> 「恒真な保証 (謳うだけで発火しない assert)」

を特に疑うよう求める。[CLAUDE.md:95](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2140-t2414-b4-prereg-rulings/CLAUDE.md:95>)

対象文書自身も、§5.1.1 の規則について、

> 「それ自体では何も機械強制しない」

と明記する。

一方、プランの静的検査は「各 erratum に非緩和が揃っている」ことを確認項目にしており、scope 2 では新しい非 sentinel 値を規範化した同じ文中で「機械的な受理集合を変えない」と宣言している。

(iii) **放置したときに何が壊れるか**

所見 1 の値追加と所見 2 の認可範囲拡大は、末尾に否定文を置いても消えない。それでもレビューが定型句の存在を非緩和の証拠として数えると、実際には変わった受理集合・開始権限を「不変」と誤認する。

定型文そのものより、それを静的検査の合格根拠にしていることが破れである。

(iv) **判定**

**real — must-fix**

## 所見 6 — 親の不変条件は §7.1 全件報告を列挙していない

(i) **主張**

親 brief の「破ったら停止」は §5.1 と §6 を列挙するが、依頼が明示した §7 の全件報告規則を独立した不変条件にしていない。

(ii) **現物の逐語根拠**

brief の不変条件は、

> 「§5.1 の解除条件も §6 の前提条件も 1 つも緩めない」

までで、§7.1 を挙げない。[stage1-brief.md:27](</home/SFC/tanab/.claude/jobs/74c07adf/tmp/wave-t2140-t2414/stage1-brief.md:27>)

§7.1 は、

> 全 block・全 arm を完走  
> 停止・crash・未発火・protocol violation を含む全件報告  
> file-drawer 禁止

を独立規範としている。[対象文書:659](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2140-t2414-b4-prereg-rulings/docs/phase3-b4-reflux-ablation-preregistration.md:659>)

ただし scope 4 の実文案は、権威 producer・実体・全 campaign closure が無いことを残しており、現在の案が §7.1 を直接緩めてはいない。

(iii) **放置したときに何が壊れるか**

現案では値・受理集合への直接影響は確認できない。したがって新しい gate を足す理由にはならない。ただし親の不変条件一覧は攻撃面を漏らしており、「機構が存在する」を「全件 closure 済み」と誤認する変更を停止条件で捕まえられない。

(iv) **判定**

**疑い — nit。現案の scope 4 は全件報告を維持している**

## 所見 7 — scope 5 の in-place 置換自体は授権済みだが、置換後は直前の *事実* と衝突する

(i) **主張**

D1779 は D1765 に対する後発・個別の例外として、費用段落の書き直しを授権している。したがって括弧の in-place 置換自体は凍結違反ではない。破れは、括弧だけを替え、現在地を示す *事実* 3 文を現役のまま残すことにある。

(ii) **現物の逐語根拠**

D1765 の一般則は、

> 「既存の文を削除・書き換えせず、直後へ……追記」

である。[rulings.md:51](</home/SFC/tanab/.claude/jobs/74c07adf/tmp/wave-t2140-t2414/verbatim/rulings.md:51>)

しかし D1779 は個別に、

> 「費用の目安の段落を……書き直す」  
> 「構成の記述は本件の裁定範囲として括弧ごと残されている」

とする。[rulings.md:33](</home/SFC/tanab/.claude/jobs/74c07adf/tmp/wave-t2140-t2414/verbatim/rulings.md:33>)

現行の *事実* 文は、

> 候補側 248 セッション = 3,720 秒  
> 参照 124 セッション = 1,860 秒をさらに加える

と現在形で書く。[対象文書:1052](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2140-t2414-b4-prereg-rulings/docs/phase3-b4-reflux-ablation-preregistration.md:1052>)

プランの新括弧は、その直前の内訳を「現在の構成を表さない」とする一方、*事実* ラベルと本文を残す。[stage2-plan.md:117](</home/SFC/tanab/.claude/jobs/74c07adf/tmp/wave-t2140-t2414/stage2-plan.md:117>)

(iii) **放置したときに何が壊れるか**

同じ「費用の目安」に 5,580 秒の現役 *事実* と 7,440 秒の erratum が併存する。§11 の読み方は *事実* を現物から確認した現在地としているため、単なる履歴保存では済まない。どちらを §5 の総計測予算へ掛けるかが一意でなくなり、予算受理と投入計画が変わる。

(iv) **判定**

**real — must-fix。なお in-place 置換の授権不足という攻撃は反証される**

## 所見 8 — 7,440 秒は実測値ではなく、旧 session 単位を measurement 単位へ移した未証明の派生値

(i) **主張**

248 side session・496 measurement という構成数は brief 内の観測から導ける。一方、7,440 秒は同じ根拠からは導けない。旧文書の仮定は「1 session = 5 反復 × 3 秒」であり、プランはこれを「1 measurement = 5 反復 × 3 秒」へ置換している。

(ii) **現物の逐語根拠**

対象文書の現行記述は、

> 「1 セッション 5 反復 × 3 秒」

である。[対象文書:1053](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2140-t2414-b4-prereg-rulings/docs/phase3-b4-reflux-ablation-preregistration.md:1053>)

brief 自身も攻撃点として、

> 「起草時の『1 セッション = 5 反復 × 3 秒』」  
> 「現構成の『1 セッション = 2 測定』で単位が変わる」

と認識している。[stage1-brief.md:55](</home/SFC/tanab/.claude/jobs/74c07adf/tmp/wave-t2140-t2414/stage1-brief.md:55>)

それにもかかわらず、直後では、

> 「起草時の名目単位 (1 測定 = 5 反復 × 3 秒) を引き継ぐと 7,440 秒」

と、起草時には存在しなかった単位を「引き継ぎ」と呼んでいる。[stage1-brief.md:70](</home/SFC/tanab/.claude/jobs/74c07adf/tmp/wave-t2140-t2414/stage1-brief.md:70>)

D1779 が裁定したのは reference が pair-sample あたり 2 件になった構成への組み替えであり、D1699 も candidate と reference を同一 session に置くことまでである。各 measurement に 5 反復を別々に課すとは裁定していない。

(iii) **放置したときに何が壊れるか**

1 session あたり 15 秒なのか、2 measurement それぞれが 15 秒なのかで、名目費用は倍になる。未証明の 7,440 秒を §5 の総計測予算の材料にすると、受理可能なセル数・walltime・総予算を誤って固定する。

「名目」と書けば実測値への誤認は弱まるが、単位変換の根拠欠落は消えない。

(iv) **判定**

**real — must-fix**

## 所見 9 — D1649 は「新事実」ではなく、既存の限定的な規範裁定

(i) **主張**

親 brief に「D1649 は新事実である」という逐語そのものは見当たらない。ただしそのように分類しているなら誤りである。D1649 は 2026-09-05 のユーザー裁定であり、実測された新事実ではない。

(ii) **現物の逐語根拠**

brief 自身も D1649 を、

> 「決定 2 で撤廃済み」

と引用している。[stage1-brief.md:16](</home/SFC/tanab/.claude/jobs/74c07adf/tmp/wave-t2140-t2414/stage1-brief.md:16>)

D1649 の理由は「時刻は運用事実」と述べるが、D1649 自体は、その運用事実をどう事前登録で扱うかを決めた規範である。[rulings.md:95](</home/SFC/tanab/.claude/jobs/74c07adf/tmp/wave-t2140-t2414/verbatim/rulings.md:95>)

(iii) **放置したときに何が壊れるか**

語の分類だけなら成果物値は変わらない。しかし「事実の反映」と誤認すると、直接裁定の `未記入` より parser との便宜的整合を優先し、所見 1 の新規規範を正当化しやすくなる。実害は所見 1 に現れている。

(iv) **判定**

**疑い — 用語単独では nit、所見 1 と結合すると real**

## 総括

**must-fix**

- 所見 1: `開始時刻 = 予定日時の事前指定なし` は D1649 に反する未授権値で、将来の受理集合を変える。
- 所見 2: D1641 の床値測定認可を正式標本の認可に読める無限定表現。
- 所見 3: D1641 の実体値確定と、旧い「決定主体の案」を混同している。
- 所見 5: 非緩和定型文を保証・静的合格根拠として数えている。
- 所見 7: 現役の *事実* と新しい費用内訳が衝突し、総予算が一意でない。
- 所見 8: 7,440 秒は session から measurement への未証明な単位変更に依存する。

**nit / 反証済み**

- 所見 4: D1812(a) は primary outcome の出現だけを覆う。現プランの挿入位置はこの境界を守っている。
- 所見 6: 親の不変条件は §7.1 を列挙していないが、現行 scope 4 案そのものは全件報告 closure の不在を維持している。
- 所見 9: D1649 を「新事実」と呼ぶのは分類誤りだが、単独では文書値を変えない。
- scope 5 の in-place 置換は D1779 が個別に授権しており、凍結規律違反という攻撃は成立しない。