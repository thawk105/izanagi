結論は **NO-GO** です。数値主張は今回はすべて実測と一致しましたが、decisions の roadmap 条件対応、README の Q 対応、worklog の時制・問い分類に承認前 blocker が残っています。

## 1. 未閉鎖 11 件の対応表

| # | 1巡目の所見 | 判定 | 根拠 |
|---:|---|---|---|
| 1 | C blocker 1 — 追補 B の差分値が偽 | **closed** | B 本体から行数を除去し、3系統の変更だけを記載した (`addendum-b-v2.md:8-17`)。package の `47/31 (235→251)` は実測一致 (`package.md:194-200`) |
| 2 | D/B10 — B の exact diff 説明 | **closed** | package が変更量・変更分類・追加禁止文を正確に列挙 (`package.md:194-203`) |
| 3 | D/Q6 — B 差分と成果物影響 | **closed** | 正しい差分値と、承認時に変わる blob・admission 参照を記載 (`package.md:194-209`) |
| 4 | D/取りこぼし — B v2 変更説明 | **closed** | B 本体では自己参照を避け、package/README に実測値を置いた (`addendum-b-v2.md:8-17`; `README.md:37-40`) |
| 5 | D/B4 — README が C-1〜C-5 全件実行済み | **closed** | C-1・C-3・C-5 のみ実施、C-2・C-2b・C-4 は未実行と明記 (`README.md:3-6`) |
| 6 | D/B6 — roadmap 継承条件不足 | **partial** | source 追補 B と seed/runtime 乱数条件は追加された (`decisions fragment:29-30,34-38`)。ただし fold bytes 条件の対象が誤っている (`decisions fragment:24-28`; `roadmap.md:233`) |
| 7 | D/Q5 — README の core 差分が偽 | **closed** | `8追加/5削除、698→701、2箇所`へ修正済み (`README.md:13,54`) |
| 8 | D/worklog — 返却完了形と Q4〜Q7 一括凍結 | **partial** | title と冒頭は「packageへ載せた」「ユーザー手番未了」へ修正 (`worklog fragment:7,12-16`)。しかし本文にはなお「ユーザー再裁定へ戻した」「Q4〜Q7の凍結承認」が残る (`worklog fragment:29-30`) |
| 9 | D/decisions — roadmap 条件の列挙不足 | **partial** | 3条件を追加したが、fold 条件を source core ではなく downstream core に写しており、元条文と一致しない (`decisions fragment:24-30`; `roadmap.md:233`) |
| 10 | C nit — fence 規則の説明が parser と逆 | **not-addressed** | 文書は fence 内見出しも数えるとする (`addendum-b-v2.md:52-65`) が、parser は fence 内を skip する (`orchestrator/preregistration/addendum_envelope.py:122-143`) |
| 11 | D/A5 — 同じ fence 規則の相違 | **not-addressed** | package 自身も未修正 nit と記録している (`package.md:261-263`) |

## 2. 数値主張の独立再計算

`git diff --no-index --numstat` と現 bytes から再計算した結果です。

| 対象 | 実測 | 主張 | 判定 |
|---|---:|---:|---|
| 追補 B 初版 → v2 | **47追加 / 31削除、235→251行** | 同値 (`package.md:194-195`; `README.md:37`) | 一致 |
| core 初版 → v2 | **8追加 / 5削除、698→701行** | 同値 (`README.md:13,54`; `worklog fragment:58-59`) | 一致 |

追補 B v2 本体には、自身の `47/31` や `235→251` は残っていません。数値を外した理由だけがあり (`addendum-b-v2.md:8-10`)、package と README の数値は現 bytes と一致します。

`b01`・`b02` の field slice は次のとおりです。

- 初版: `addendum-b.md:63-147`
- v2: `addendum-b-v2.md:79-163`
- 双方: **5186 bytes**
- SHA-256: `98ba244e857a3707cab3a350796042160e43c81bf3c405a4e394706e2d5d6f6c`
- `cmp`: 一致

worklog の4 SHA-256もすべて実ファイルと一致しました (`worklog fragment:74-82`)。

| 対象 | 実測 SHA-256 |
|---|---|
| source core | `ac939af4de87dff0cd3964e37cef975d57919a709d57f4e9523c8b6a9fcd60e9` |
| 追補 A 再発行版 | `f7db96ce8ecb12359fedf56baea24939c629d4d16a1ec167c183425ea198cfec` |
| 新 core 初版 | `9b7bc1932dd76e0e72f5cd98f9de2e01a62c4a065e8ac0e0eb6a59e5a3f66a64` |
| 追補 B 初版 | `5071acbd9db18f022cb9603acef3a8cd3394ed17de80cc794468c1b1f5baa384` |

## 3. 3巡目の regression・整合検査

### decisions の fold 条件が別の義務へ変わっている

roadmap が要求するのは、**source core** の canonical bytes が、元の限定例外を発効させた fold commit 時点と同一であることです (`roadmap.md:233`)。

一方 decisions は、主語を「下流解析の推論構造を固定した core」としたうえで、その bytes を**今回の下流適用裁定の fold commit**へ束縛しています (`decisions fragment:24-28`)。これは以下の二重の不一致です。

- source core と元の限定例外 fold の同一性を明示的には継承できていない。
- roadmap にない、downstream core と今回の fold の同一性という新しい義務を追加している。

したがって `package.md:58` の「漏れなく対応させた」も現状では成立しません。

### README の Q 対応が package と不一致

README は「凍結承認 Q5〜Q7、新事実 Q1〜Q4」とします (`README.md:12`)。実際の package は次です。

- Q1〜Q3: 新事実・順序問題
- Q4〜Q5: core/B の凍結承認
- Q6〜Q7: 非凍結の追補 P に入れる候補値の裁定

根拠は `package.md:171,190,211,227`。ユーザーが誤った問いへ回答しうるため、表記 nit ではありません。

さらに README の一覧は B v2 を「`b03` の縮小1点のみ」とします (`README.md:14`) が、同じ README の詳細は preamble・`b03`・末尾節の3系統と明記しています (`README.md:37-40`)。exact bytes の承認入口として内部矛盾です。

### worklog の title・本文・次の一手

title と冒頭、次の一手は概ね一致しています。しかし本文だけが、

- 「ユーザー再裁定へ戻した」と完了形
- 「Q4〜Q7の凍結承認」

と記録しています (`worklog fragment:29-30`)。同 fragment の次の一手は Q4/Q5 を凍結承認、Q6/Q7を値承認と正しく分離しています (`worklog fragment:97-104`)。canonical 化前に揃える必要があります。

## 4. 承認前の必須修正

1. decisions の fold bytes 条件を、roadmap どおり「source core と元の限定例外 fold」の関係として記述する。downstream core へ別の fold 義務を課すなら、roadmap 継承ではなく独立裁定としてユーザーへ明示する。
2. README の Q 対応を Q1〜Q3／Q4〜Q5／Q6〜Q7へ同期し、「B は `b03` 縮小1点のみ」という要約を3系統の変更説明に合わせる。
3. worklog `:29-30` をユーザー手番未了の時制へ直し、Q4/Q5の凍結承認とQ6/Q7の値承認を分離する。

fence 規則2件は現 bytes の受理集合を変えないため、NO-GO理由には含めません。

## 総括

closed: **6**  
partial: **3**  
regressed: **0**  
not-addressed: **2**  
判定: **NO-GO**