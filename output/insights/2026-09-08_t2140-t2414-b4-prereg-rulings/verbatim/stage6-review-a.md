## 対応表

|所見|状態|適用結果|
|---|---|---|
|A1 開始時刻の未授権値|closed|発明した `予定日時の事前指定なし` は入らず、D1649 の `未記入` を逐語反映。§0 との関係も未裁定としている。|
|A2 D1641 の認可範囲|closed|床値測定だけの認可であり、正式標本には §5・§6 が別途必要と明記。|
|A3 §11.1 の決定主体案と確定値|partial|§11.1 / §11.2 自体は訂正されたが、§11.3 に逆の権限記述が残り、文書全体では root cause が閉じていない。|
|A4 D1812(a) の射程|closed|primary outcome の出現だけに限定し、母集合の manifest / registry を明示的に除外。|
|A5 恒真な非緩和宣言|partial|多くは具体的拘束へ置き換わったが、発火しない「本追記は許可しない／緩めない」も残る。|
|A6 §7.1 全件報告|closed|§7.2 に、全件報告を実効化しないことと file-drawer が開いたままであることを明記。|
|A7 費用段落の現旧矛盾|partial|現行値との矛盾は解消したが、段4が述べた「逐語で保存」は成立しない。|
|A8 7,440 秒の単位根拠|closed|measurement ごとに `reps` が掛かる実装根拠と、名目値にすぎない限定を追加。|
|A9 D1649 の分類|closed|「新事実」ではなく既裁定の本文反映として記述。|
|B1 逐語アンカー|closed|7 挿入点すべて期待箇所へ適用されている。|
|B2 exact 1 pair 前提|closed|`1 pair・1セル` と P 個の場合の `124P / 248P / 496P` を明記。|
|B3 reference 件数|closed|pair-sample あたり 2、side session あたり 1 という記述。|
|B4 起草時費用の時系列|closed|n=59 と D1695 後の旧構成を分け、5,310 / 5,580 秒を正しく保存。|
|B5 ledger 機構の実在範囲|closed|型・純関数・generator・validator・local issuer までに限定。権威 producer / launcher 配線不在も維持。|
|B6 `output/` 0 件の限定|closed|B-4 issuer の固定名 3 成果物に限定。|
|B7 他の不存在断言|closed|§7.2 / §10 のみを訂正し、scope を広げていない。|
|B8 living-doc lint|closed|追加 bytes に行番号参照や禁止 placeholder 形式はない。|
|B9 成果物数・worklog|partial|適用差分は対象文書 1 件だけ。段4がいう検査条件の言い直しや後段の insight / spool は指定資料から検証不能。|
|B10 bytes pin|closed|凍結対象だった旧 312–596 行の内部に編集はなく、前方挿入による移動だけ。|
|B11 開始時刻の新規値|closed|A1 と同じ。未授権値は入っていない。|
|B12 brief の小誤記|partial|authoritative producer の出所は本文で正されたが、brief の行番号訂正は適用 bytes から検証不能。|

集計は closed 16、partial 5、regressed 0。ただし partial のうち成果物の意味を壊すものは A3 だけである。

## 所見 1 — §11.3 が D1641 の権限・確定状態を逆転させたまま残る

(i) 主張

§11.1 / §11.2 の訂正そのものは裁定どおりだが、その後に現れる §11.3 が、担当者・対象集合・統計関数・採用主体を再び「ユーザー手番」としている。A3 の root cause は文書全体では partial である。

(ii) 適用後 bytes の逐語

§11.1 の追記は、

> 「担当 3 者……をいずれも `thawk105` 名義とし操作を AI 委任」  
> 「校正済み `PerfConfig` の承認と成果物の採用裁定を……AI が行う」

とする。[対象文書:1049](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2140-t2414-b4-prereg-rulings/docs/phase3-b4-reflux-ablation-preregistration.md:1049>)

§11.2 の追記も 12 項目を採用済みとする一方、

> 「§11.3 が列挙する残りの手番については本追記では何も述べない」

と明記する。[対象文書:1067](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2140-t2414-b4-prereg-rulings/docs/phase3-b4-reflux-ablation-preregistration.md:1067>)

その §11.3 は後段で、

> 「担当者の指名、対象集合、標本数、統計関数、採用証拠の受理 — いずれもユーザー手番」  
> 「残り (担当者の指名、対象集合、統計関数、採用証拠の受理……) は……ユーザー手番」

と残る。[対象文書:1190](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2140-t2414-b4-prereg-rulings/docs/phase3-b4-reflux-ablation-preregistration.md:1190>)

(iii) 放置時の破損

有効な floor 成果物の採用主体が AI 委任なのか追加のユーザー裁定なのか、対象集合・統計関数が凍結済みか未決かが一意でない。これは §5 に受理できる floor pin と、その floor を参照する primary verdict の参照系を変える。

ただし §11.3 の訂正は D1812(c) が名指しした §11.1 / §11.2 の外である。この wave で黙って編集範囲を広げるべきではなく、現状では D1812(c) を完全に closed と宣言せず、追加授権へ返す必要がある。

(iv) real / 疑い

real — must-fix。修正には scope の追加授権が必要。

## 所見 2 — 削除 9 行は授権範囲内だが、逐語保存ではない

(i) 主張

削除はすべて §11.2「費用の目安」の単一段落内であり、後発・個別の D1779 が「段落を書き直す」と授権した範囲に収まる。絶対規律 7 が保護する実測成果物でもないため、削除自体は凍結違反ではない。

一方、段4の「旧派生値は erratum に逐語で残した」は事実ではない。

(ii) 適用後 bytes の逐語

削除前には、

> 「1 セッション 5 反復 × 3 秒」  
> 「組み替え後の目安は D1699 の実装が確定してから書き直す」

があった。[applied.diff:119](</home/SFC/tanab/.claude/jobs/74c07adf/tmp/wave-t2140-t2414/applied.diff:119>)

適用後は、

> 「1 測定 = 5 反復 × 3 秒を置くと……7,440 秒」

であり、上の旧文言は erratum 内にも存在しない。[対象文書:1123](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2140-t2414-b4-prereg-rulings/docs/phase3-b4-reflux-ablation-preregistration.md:1123>)

ただし 236 / 3,540 / 118 / 1,770 / 5,310 および 248 / 3,720 / 124 / 1,860 / 5,580 という旧派生値はすべて保存されている。

(iii) 放置時の破損

現行費用値や受理集合は変わらない。失われるのは、旧計算が session 単位で記述されていたという逐語的な監査履歴と、「逐語保存した」という段4説明の正確性だけである。

(iv) real / 疑い

real — nit。D1779 の授権、D1765 との関係、絶対規律 7 のいずれについても成果物を止める違反ではない。

## 所見 3 — 非緩和宣言の一部はなお発火しない

(i) 主張

A5 は大半が閉じた。各追記は、維持する具体条件を名指ししている。ただし「本追記は許可しない／緩めない」という主語限定の文は、それ自体では gate も受理条件も拘束しない。

(ii) 適用後 bytes の逐語

実際に拘束を示す記述としては、

> 「記入した 5 値が記入時点の bytes と一致することは、引き続き要求する」  
> 「manifest と registry……は source file で代替できない」

がある。[対象文書:221](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2140-t2414-b4-prereg-rulings/docs/phase3-b4-reflux-ablation-preregistration.md:221>)

§7.2 にも、

> 「file-drawer は開いている」  
> 「§7.1 の全件報告規則を実効化せず」

という実質的限定がある。[対象文書:721](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2140-t2414-b4-prereg-rulings/docs/phase3-b4-reflux-ablation-preregistration.md:721>)

一方で、

> 「本追記は §5.1 の解除条件も §6 の前提条件も緩めない」  
> 「本追記は測定の開始も……許可しない」

という非作動の宣言も残る。[対象文書:1058](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2140-t2414-b4-prereg-rulings/docs/phase3-b4-reflux-ablation-preregistration.md:1058>)

(iii) 放置時の破損

これらを独立した保証として数えると、機械強制や権限遮断が存在すると誤認する。ただし今回の bytes では、直近に具体的な path/hash 条件、正式標本の全条件、file-drawer の未閉鎖が併記されており、宣言だけで受理集合は広がっていない。

(iv) real / 疑い

疑い — nit。A5 は partial だが、実質的緩和は検出しない。

## 所見 4 — §5.1・§6・§7 の緩和密輸および未裁定規範の追加は検出しない

(i) 主張

適用後 bytes は、D1812 / D1779 / D1649 / D1641 / D1695 / D1477 / D1699 の射程内に留まる。新しい義務・許可・実験値は確定していない。

(ii) 適用後 bytes の逐語

- D1812(a): source file 5 member に限定し、manifest / registry の代替を禁止。[対象文書:216](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2140-t2414-b4-prereg-rulings/docs/phase3-b4-reflux-ablation-preregistration.md:216>)
- D1649 / D1477: 固定日時を置かず、実時刻は成果物側へ記録。[対象文書:275](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2140-t2414-b4-prereg-rulings/docs/phase3-b4-reflux-ablation-preregistration.md:275>)
- D1812(d): library / local issuer の実在だけを認め、権威 producer・正式 launcher・成果物実体の不在を保持。[対象文書:709](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2140-t2414-b4-prereg-rulings/docs/phase3-b4-reflux-ablation-preregistration.md:709>)
- D1641 / D1695: 12 項目の既裁定と n=62 を反映するが、floor の path/hash 条件は維持。[対象文書:1049](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2140-t2414-b4-prereg-rulings/docs/phase3-b4-reflux-ablation-preregistration.md:1049>)
- D1779 / D1699: 現構成の名目費用へ書き換え、未校正 `PerfConfig` による実時間保証ではないと限定。[対象文書:1123](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2140-t2414-b4-prereg-rulings/docs/phase3-b4-reflux-ablation-preregistration.md:1123>)

`124P / 248P / 496P` は n=62・2 campaign・P pair の算術であり、新しい実験規範ではない。header と `reps` の記述も実装事実の根拠であって、新しい許可ではない。

(iii) 放置時の破損

この観点での追加破損はない。正式標本は依然として §5 全欄・§6 全条件を要求し、§7.1 の file-drawer closure も成立していない。

(iv) real / 疑い

緩和・新規規範の疑いは refuted。

## 所見 5 — 指定された三つの矛盾対は、追加の緩和にはなっていない

(i) 主張

§7.2 と §10、§11.1 と §11.2 は、追記を時系列順に読めば一致する。§5.1 の開始時刻と §0 は解決していないが、その未解決を明示したため、現状は「発効不能」という fail-closed な状態として読める。

(ii) 適用後 bytes の逐語

- §7.2 は「file-drawer は開いている」、§10 は「file-drawer の機械強制は、本書が閉じない事項」と一致する。[対象文書:721](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2140-t2414-b4-prereg-rulings/docs/phase3-b4-reflux-ablation-preregistration.md:721>) [対象文書:932](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2140-t2414-b4-prereg-rulings/docs/phase3-b4-reflux-ablation-preregistration.md:932>)
- §11.1 は値の正本を D1641 とし、§11.2 は残る *案* 表記を起草履歴と読む。[対象文書:1053](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2140-t2414-b4-prereg-rulings/docs/phase3-b4-reflux-ablation-preregistration.md:1053>) [対象文書:1067](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2140-t2414-b4-prereg-rulings/docs/phase3-b4-reflux-ablation-preregistration.md:1067>)
- §0 は placeholder が残れば検査を閉じる。[対象文書:37](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2140-t2414-b4-prereg-rulings/docs/phase3-b4-reflux-ablation-preregistration.md:37>)
- 開始時刻追記は「関係は本追記では決めない」「発効版でどう書くかは未裁定」とする。[対象文書:285](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2140-t2414-b4-prereg-rulings/docs/phase3-b4-reflux-ablation-preregistration.md:285>)

(iii) 放置時の破損

開始時刻欄について、他の欄を満たしても現在の admission は開かない。ただしこれは隠れた緩和ではなく、段4がユーザー裁定へ返した既知の発効不能状態である。非 sentinel 値を勝手に発明するより安全側である。

追加の実害は所見1の §11.3 競合に限られる。

(iv) real / 疑い

指定された三対に関する追加の矛盾疑いは refuted。開始時刻問題自体は既知の未裁定事項。

## 所見 6 — B9 / B12 の非本文裁定は適用 bytes だけでは閉鎖確認できない

(i) 主張

段4がいう検査条件の言い直し、後段の insight / spool、brief の行番号訂正は、適用差分にも対象文書にも含まれない。

(ii) 適用後 bytes の逐語

[applied.diff](</home/SFC/tanab/.claude/jobs/74c07adf/tmp/wave-t2140-t2414/applied.diff:1>) の変更先は `docs/phase3-b4-reflux-ablation-preregistration.md` 1 件だけである。authoritative producer の出所については本文が正しく `p3_b4_analysis_ledgers.py` としている。

(iii) 放置時の破損

対象文書の値・受理集合・参照には影響しない。ただし B9 / B12 を「適用済み」とする段4の説明全部を、この静的レビューの資料だけから証明することはできない。

(iv) real / 疑い

疑い — nit / evidence-limited。

## 総括

must-fix:

- §11.1 / §11.2 が D1641 に従って担当・値・採用主体を確定済みとする一方、後段の §11.3 が同じ事項をユーザー手番として残している。floor pin の採用主体と凍結済み参照集合を変える実害がある。ただし §11.3 の訂正は本 wave の明示 scope 外なので、黙って編集せず追加授権へ返す必要がある。

nit:

- D1779 による削除 9 行は授権範囲内で、旧数値も保存されているが「逐語保存」ではない。
- 非緩和・非許可の宣言には発火しない文が残る。ただし具体的拘束が併記され、今回の受理集合は広がっていない。
- B9 の検査条件変更と記録成果物、B12 の brief 行番号訂正は指定された適用 bytes から検証不能。

静的検査のみを行い、file の変更・commit・pytest は行っていない。