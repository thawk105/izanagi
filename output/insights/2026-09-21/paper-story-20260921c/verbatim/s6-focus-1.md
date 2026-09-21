## 前提と範囲

- 対象は worktree `/work/1/SFC/tanab/izanagi/.claude/worktrees/paper-story-2026-09-21c/` です。以下の path はここからの相対 path で書きます。job dir の file は `JOB/` と略します(= `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-paper-story-2026-09-21c/`)。
- 必読の file はすべて読めました。読んだのは、レビュー A・B の全文、`JOB/tools/fix_review_a.py`、`JOB/parent/s10-draft.md`、`JOB/parent/figures-fig3c.md`、`JOB/codex/readme.diff`、状態 JSON の全文です。一次資料は次の範囲を読みました。
  - B-8 単独稿 §3・§4
  - insight `t2807-b8-effective` §2〜§5
  - insight `t2344-closure-emitters` §5
  - 決定 D2194 項 2、D2201〜D2205
- 本文は現在 5,904 行あり、全文は読んでいません。grep で位置を出し、該当範囲だけを読みました。
- 静的検査だけを行いました。repo の file は 1 つも編集・作成していません。
- 修正後の本文の現在の sha256 は `7bd0ed01aa18…` です。
- job dir には `JOB/tools/fix_peer30.py`(15:43)がありますが、現物にはまだ当たっていません(下の新規所見 2)。本レビューは fix_review_a を当てた後、fix_peer30 を当てる前の状態を対象にしています。

## 対応表 — レビュー A(must-fix 6 / should-fix 9)

| 所見 (A/B-番号と要約) | 判定 | 根拠 (file:line と逐語) |
|---|---|---|
| A-M1 §9 の B-8「承認されたが未実施」(2 か所)と、版の連鎖が短いこと | closed | 21c.md:5671「この版の起点までに発効・校正・本走を実施して `pass`、D2202」。5713-5714「B-8 は発効した事前登録 v1 の 3 値判定 `pass` で取得したが…本走は段階認可 (D2200) までで未認可」。5724-5725「この版で B-8 の取得…K2 pair の driver 修復 (再投入は未) が加わった」 |
| A-M2 §8 B-8 の歴史小項目に「取得したとは書かない」が現在形で残る | closed | 21c.md:4808「当時は未発効 — この版の起点までに発効」。4820「2026-09-20b 版の時点では」。4822-4823「…場合だけとされた。** この版の起点までに…下の判定で取得した」。4869「当時 (2026-09-21 版の時点) の限定」。4871-4872「…完走し (校正の verifier wall 最大 491.4 s)」(insight §3 の 491.4 s と一致) |
| A-M3 検証相の「種」も要件を満たさないとする現在形 | closed | 21c.md:1678「対象・長さが B-8 の要件と違い (種は仕分け (2) の改定後は要件を満たす)」。3756-3757 も同じ形。4790-4791「当時の仕分けでは…3 要素のいずれも満たさないとされた。仕分け (2) の改定 (下) の後も、対象 (1) と長さ (3) が要件と違うので」。種の句は insight §2「仕分け (2) が改まっても B-8 には数えない」と、検証相の稿 71 行「独立 N 反復…run ごとに自己シード」から導ける。一次資料より強い断定ではない |
| A-M4 C35「pair の修復は本稿の起点で未実施」 | closed | claim-evidence:216「pair の再投入と 4 巡目は本稿の起点で未投入である (driver 側の修復は D2205 で着地、`L61`、`L56`)」 |
| A-M5 C42 の状態 JSON の path が旧いまま | closed | claim-evidence:222「状態 JSON `docs/paper-story/figures/arc_status_story_2026-09-21c.json`」。`tools/` 配下に 21c の JSON は無い(ls で確認)。`tools/` を grep しても参照 0 件 |
| A-M6 入力版の sha256 が現物と一致しない | **partial(未了・予定どおり)** | claim-evidence:31 は `fec37fc5…` のまま。現物は `7bd0ed01…` で、まだ一致しない。§10 の 5891 行は「sha256 は最終 bytes で再計算する」と予定形で書いている。§10 の完了形化と fix_peer30 の適用で bytes はさらに変わるので、最後に再計算して、land の直前に一致を確かめる必要がある |
| A-S1 §0 の「D2194 の 3 項が実施」 | closed(nit 付き) | 21c.md:18「2 つ (項 4・項 5) が実施され、項 2 が前提とする K2 pair の driver 修復が着地した」。21「D2187 の修復方向」は D2205 の決定文「D2187 の修復方向…を実装した」と一致する。D2194 項 2 の本文「pair 修復 wave (AI、D2187) の後に」とも整合する(nit は下の 4・5) |
| A-S2 C45「受理集合を動かしていない」 | closed(nit 付き) | claim-evidence:224「論文の主張の側で判定・値を動かしていない。** ただし closure 85 → 96 は certified decode の受理集合を縮めた」。insight t2344 §5「exact-85 で記録された campaign は certified の decode 段で拒否」と一致する。「機構・」の削除も確認した |
| A-S3 §8 冒頭の依頼が前版の文の残り | closed | 21c.md:3999-4000「この節がこの版の要求事項の中心である。** 依頼が求めた「B-8 の 3 値判定 `pass` の反映…」…(A-1 の…(D2194 項 6) は前版が行い、この版も保つ)」 |
| A-S4 fig3b との比較の相手が 1 版古い | closed | 21c.md:2078「**この版の §8 とは一致しない**…B-8 は…この版で取得 (3 値判定 `pass`)」。2274-2277「この版の状態図ではない (この版の状態図は fig3c)」「B-8 (取得 — 3 値判定 `pass`)、B-5 (…本走は段階認可)」。3865「(この版の §8 とは一致しない。…この版の状態図は fig3c)」 |
| A-S5 §7 の K2 pair 2 項と B-5 試走の項に更新が無い | closed | 21c.md:3840-3841「この版の更新: pair の launcher と one-shot claim の整合は driver 側で修復された」。3846-3848「この版の更新: 第 28 回 D2200 項 1 が本走を段階認可した…本走は未認可のまま」。3906-3907「前版の基準 HEAD で未実施だった。…この版の更新: driver 側の修復は着地した」 |
| A-S6 C25・L40 の仕分け (2) の明記が未来形 | closed(claim-evidence 側) | claim-evidence:190 の 2 か所と 336「発効 commit の wave が行った ([T-2807] insight §2)」。残る「行う」は grep で 0 件。ただし本文 21c に同じ型が 1 か所残る(新規所見 3) |
| A-S7 前稿を行番号で参照している | closed | claim-evidence:781「前稿の 2 行を」「g1 の validator の行の理由欄を」「LLM の必要性の行に」 |
| A-S8 下書き役向けの指示が凍結稿に漏れている | closed | claim-evidence:740 から facts-delta への言及が消えた。780「(C25 の先例に倣い、判定の記録そのものを科学的主張の側に、裁定・発効・投入の経緯を C39 に分けた)」 |
| A-S9 前版の執筆時点の誤りの境界事例 | partial | 読み方は §10 に明記された(21c.md:5831-5834「版名を冠した小項目の現在形をその版の時点の記述として読み…『2026-09-20b 版の時点では』を付けて過去形に直した」)。しかし A が代案として求めた「§0 に 1 文」は無い。§0 の 43 行と README 差分の 30 行は「段 6 の敵対レビューも…見つけなかった」のままで、境界事例の存在と §10 への参照が無い(新規 nit 15) |

## 対応表 — レビュー B(must-fix 1 / should-fix 8)

| 所見 (A/B-番号と要約) | 判定 | 根拠 (file:line と逐語) |
|---|---|---|
| B-M1 B-7 の副ラベルが必須 4 語の限定のうち 2 語を欠く | closed(layout は未確認) | figures/arc_status_story_2026-09-21c.json:196「fulfilled with limitations: single attempt; descriptive; non-certifying; repeat stability undetermined」。本文 21c.md:4734-4735「単一 attempt・descriptive・非認証・反復間安定性は未判定」の 4 語と一致する。草稿 figures-fig3c.md:30 も同じ文字列 |
| B-S1 GENERIC_CAPTION の「carries the recorded … limitations」 | **意図的不採用 — 理由は妥当、補足は概ね妥当** | 理由: 生成器の定数を変えることになり、D95 により Codex author が必要だが、Codex は 9 月 26 日まで利用上限にかかっている。B 自身も must-fix ではないとした。補足: figures-fig3c.md:96-99「**副ラベルは本文の【状態】の要約であり、限定を網羅しない** (たとえば B-8 の限定は単独稿 §4 の 11 項、B-7 は本文 §8 の 4 語)…正本は同版本文の §8」。caption の正文を置く節に書かれているので、読み手には届く。不足は 2 点ある(新規 nit 16)。(i) 本文 21c の「Fig 3c について論文執筆時に必ず守ること」(2284-2292)に同じ注意が無い。(ii) Codex が戻った後に次の状態図で caption を直す持ち越しが、insight にも decisions 断片にも記録されていない。なお decisions 断片の 37 行は「figures README に注記する — 新しい provenance に偽の caption が残る」として旧 caption の案を却下しており、今回の補足はそれと同じ手法を、偽ではなく過大な程度の文言に適用している |
| B-S2 M1 の期待 node 集合が狭い | closed(wave の記録で処理済み) | `JOB/mutation-spec-final.json` の M1 の expected_nodes は T10、T11[invalid-calendar-day]、T13 の 3 本。final の結果は KILLED 8 / SURVIVED 1、matching 9/9。`JOB/parent/insight-README.md:29` に erratum の記録がある。§10 はこの扱いに触れていない(新規 nit 14) |
| B-S3 B-5 の「staged, not authorized」が曖昧 | closed | JSON:182「not obtained; staged approval only; main run not authorized」。本文 4582-4583「段階認可は本走の認可ではない…本走は未認可」と一致する |
| B-S4 B-8 のラベル「Independent long-run validation」 | closed | JSON:201「Seed-varied long-run check」。副ラベル 203 に「operational definitions」を追加 |
| B-S5 第 3 幕の B-8 行に observed runs が無い | closed | JSON:89-91 のラベル「Final-candidate check」と副ラベル「B-8 pass; correctness check on observed runs; no performance claim」 |
| B-S6 B-4 の未了の主因が欠落 | closed | JSON:175「…eligible precursor absent; carrier ruled, not implemented」。本文 4460-4461「適格な赤 precursor 0 件 (再確認)」、4465-4466「裁定した (実装は…未実施)」と一致する |
| B-S7 fig3c 節に状態語の意味の節が無い | closed(nit 付き) | figures-fig3c.md:10-21 に 4 状態の例示と優先順位が入った。not obtained は「A-5 と B-2〜B-6」の 6 項目で、JSON の 6 項目と一致する。uncertified の 3 項目(A-1 / B-9 / B-10)も一致する(nit は 10・11) |
| B-S8 21c の JSON が単体 test で検査されていると読める | closed | figures-fig3c.md:89-91「**単体 test の実寸 fixture は 2026-09-19 版の JSON とその本文の複製であり、2026-09-21c 版の JSON を読む test は無い。**」。ただし同じ文の「実走の rc=0 で確かめた」は、図を作る前に書いた完了形である(未確認の範囲を参照) |

補足として、nit の扱いを 1 行ずつまとめる。
- A の nit 8 件
  - 反映済み: [T-2812] の射程、D2201 / D2203 の性格(2915)、連鎖 7 か所(3237 / 371・4017・4067 / 5728 / 2097)、§6 の要約(3181-3185)。
  - 一部反映: 1773 は直ったが、3381-3382 の「再提示された」は残る(直後の 3383 が補っている)。claim-evidence の小さな 4 点は、789・761・177 が直り、746 が残る。
  - 未反映・理由の記載なし: L75 などの出所の帰属。
  - 意図的に維持: fig3c の完了形。
- B の nit 11 件
  - 反映済み 7 件: B-9 の originals lost、A-5、優先順位、Silo の理由付け、fig3c.md の列挙、比較でないことの注記、plotting README の 418 行。
  - 生成器・test の変更になるので不採用 4 件: caption の系譜、T10 の冗長、docstring、figure_created の暦日 test。
  - CPython の文言依存は、B 自身が放置してよいとした。
  - 反映済みの refuted 付随 nit: `152c1d99d` への導線。`152c1d99d..76b60f6e1^` の範囲で生成器に変更が無いことを git log で確かめ、fig3b を生成した当時の bytes を辿れることは真だった。

## 新規所見(修正で生じたもの、または修正後に残った同型)

- [should-fix] docs/paper-story/claim-evidence/2026-09-21b.md:769 — §7 の継承表が「C1〜C23b / C25〜C31 / C34 / … | 同 ID で継承。内容は不変 (正典で再確認した)」と書いているが、前稿との行単位の比較で C7・C25・C34 の本文が変わっている — 根拠: python で行を比べると差分行は `C7, C24, C25, C33, C34, C35, C36, C39, C40, C42` と L 系である。
  - C25 は fix が「行う→行った」と「C39→C44」を変えた。
  - C34 は fix が [T-2812] の射程(D2201)を足した。
  - C7 は D2200 の注記(「第 28 回 D2200 項 1 は段階認可で」)を足している。
  - C25 と C34 は今回の fix が表を追随させずに作った不一致(regressed)である。
  - 修正案: C7・C25・C34 を「内容は不変」の行から外し、「C7: D2200 項 1 の注記を足した / C25: 仕分け (2) の明記の完了 ([T-2807] insight §2) と C44 参照 / C34: [T-2812] の射程 (D2201) を反映」の 3 行を足す。L40 の行にも「行った」への更新を 1 句足す。
- [should-fix] docs/paper-story/2026-09-21c.md:3969、5669、docs/paper-story/README.md:38(表の行) — 判定集合 30 枠を、本走の条件「独立 8 反復 × 3 workload × extime 10 s」に丸ごと帰属させている — 根拠: B-8 単独稿 §3.1 では校正 6 行が各 workload の 6 s と 10 s の各 1 回で、30 枠には extime 6 s の 3 枠が入る。3969 行「1 回の cohort (独立 8 反復 × 3 workload × extime 10 s、判定集合 30 枠)」は 8 × 3 = 24 と 30 が食い違ったまま並ぶ。
  - 親の `JOB/tools/fix_peer30.py` がこの 3 か所を用意しているが、現物には未適用である。
  - 同じ型の 21c.md:3248-3249「独立 8 反復 × 3 workload × extime 10 s の 1 回の cohort (判定集合 30 枠、本走 24 + 校正完走 6…)」は script の対象外である。内訳は書いてあるが、校正に 6 s が混ざることは書いていない。
  - 修正案: fix_peer30 を当ててから sha256 を再計算する。3248 も「(本走 24 枠 + 校正の完走 6 枠 (各 workload の extime 6 s / 10 s 各 1 回))」に揃える。
- [should-fix] docs/paper-story/2026-09-21c.md:3898-3899 — A-S6 と同じ型(仕分け (2) の明記を未来形で書く)が本文に残る:「仕分け (2) の限定明記は発効時に行う。」 — 根拠: 発効 commit `624c84986` がこれを書いた(insight §2)。同じ項の「この版の更新」(3900-3902)はこのことに触れていない。claim-evidence 側は「行った」へ直したので、表と本文で時制が食い違う。
  - 修正案: 「…発効時に行うとされ、発効 commit (`624c84986`、[T-2807] insight §2) の wave が行った。」とする。
- [nit] docs/paper-story/2026-09-21c.md:18 — 「第 27 回 D2194 が裁定した項のうち 2 つ (項 4・項 5) が実施され」は、項 1(B-8)を数えていない。第 1 で書いているので文脈上は正しいが、claim-evidence:24 と §7 の 3939 行「項 1・項 4・項 5 は…実施済み」とは件数が異なって見える。修正案: 「(項 1 の B-8 は第 1 に書いた)」を足す。
- [nit] docs/paper-story/2026-09-21c.md:160 — 21 行からは「項 2 の控え」を外したのに、§0 の 6 は「D2187 の修復方向・D2194 項 2 の控え」のまま残る。修正案: 「D2194 項 2 が前提とする」に揃える。
- [nit] docs/paper-story/claim-evidence/2026-09-21b.md:224 — fix の置換で「…でだけ読める)。 closure の tuple 収載は」と余分な空白が入った(太字を閉じた後にあった空白が残ったもの)。
- [nit] docs/paper-story/claim-evidence/2026-09-21b.md:215、510 — 761 行で直した「****」(太字記号の連結)と同じ型が C34 と §5 に残る。
- [nit] docs/paper-story/claim-evidence/2026-09-21b.md:746 — A の nit である二重空白「本稿は  §4.3」「には  数えない」が未修正。
- [nit] docs/paper-story/2026-09-21c.md:1756、3254-3255、claim-evidence:383(L75) — A の nit(単独稿 §4 は「信頼度」「1−εⁿ」「別の workload・thread 数・extime・別 pin へ広げない」を文字どおりには含まない)が未反映で、§10 にも不採用の理由が無い。修正案: 「(§4 項 2・11 と、それに基づくこの版の書き方)」と分けて書く。
- [nit] JOB/parent/figures-fig3c.md:26-29 — B-8 について「主張の支持ではない (obtained の定義)」とあるが、定義文は「need not support the claim(支持するとは限らない)」である。支持しないと断定する形になっている。修正案: 「主張の支持を意味しない」とする。
- [nit] JOB/parent/figures-fig3c.md:13-14 — obtained の例示だけが A-2(obtained)を欠く。他の 3 状態は全数を列挙しているので、A-2 が obtained でないように読めうる。修正案: A-2(observed-positive)を足すか、「例」と明記する。
- [nit] docs/paper-story/figures/arc_status_story_2026-09-21c.json:127 — A-5 の副ラベルが、fig3b の「Pegasus does not establish separate-boot reproduction」から「no separate-boot reacquisition」に変わり、未了理由(D1525: Pegasus では別 boot 再現にならない)が落ちた。【状態】の写しとしては一致しているが、fig3b 節の整合規則(figures README:1138「副ラベルの事実・限定・未了理由…まで比較する」)と、本文 §9 の 5688 行「**Pegasus では充足しない**」に照らすと情報が減っている。修正案: 「not obtained; Pegasus cannot establish separate-boot reproduction」(数字 token なし)。
- [nit] JOB/parent/s10-draft.md:74、21c.md:5887 — レビュー A を「(refuted 5)」と記録しているが、A の本文の [refuted] は 6 項目ある(9・10・16・17・25・87 行)。A 自身の集計を写した誤りである(DW-O16)。修正案: 「refuted 6(A の集計は 5)」とする。
- [nit] 21c.md:5879-5885(§10 段 6) — B の should-fix 8 件のうち、M1 の期待集合の扱い(probe で観測し、final spec で 3 node へ再照準した erratum)が書かれていない。現状は採用 6 件と不採用 1 件しか辿れない。修正案: 「M1 の期待 node は probe の観測で T13 を加えて 3 本へ再照準した (erratum、wave の記録)」を 1 句足す。
- [nit] 21c.md:43、README 差分 9 行・30 行 — 「段 6 の敵対レビューも前版の執筆時点の誤りを見つけなかった」のままで、A が挙げた境界事例 1 型への言及が無い。修正案: 「(境界事例 1 型は §10 (P2) の読みで数えない)」を足す。
- [nit] 21c.md:2284-2292 — GENERIC caption の過大な文言についての注意が、本文の「Fig 3c について論文執筆時に必ず守ること」に無い。持ち越しの記録も無い。修正案: 1 行「caption の 'sublabel carries the recorded … limitations' は要約の意で、限定の正本は §8」を足し、次の状態図で文言を直す持ち越しを insight に書く。
- [nit] 21c.md:3899、3877 — 更新ラベルの中で、修飾の無い「基準 HEAD」が残る(「基準 HEAD では発効 commit・校正・本走のいずれも未実施」「B-5 試走は基準 HEAD では未」)。3906 は「前版の基準 HEAD」に直したが、同型の 2 か所がそのままである。

攻撃が不成立だった点(記録として):
- 491.4 s は insight §3 と一致した。
- 「種は…要件を満たす」は一次資料からの導出の範囲内だった。
- 状態 JSON の anchor 20 本は、すべて本文の該当節にちょうど 1 行ずつ当たった(生成器と同じ正規表現で静的に数えた)。
- fig3b の JSON と比べた差分 12 項目(A-1 / A-4 / A-5 / B-4〜B-9 と第 3 幕の 3 行)は、figures-fig3c.md の列挙で漏れなく覆われていた。
- 時点語について: fix が入れた「前版」「2026-09-21 版」「2026-09-20b 版の時点では」「当時 (2026-09-21 版の時点)」は、いずれも指す版が正しかった。
- 副ラベルと【状態】の照合: B-7 の 4 語、B-8、B-4、B-5、B-6、B-9、A-1、A-4 はいずれも本文 §8 の【状態】と一致した。
- 生成器は `--states` の置き場を制約していない(`load_states` は repo root からの相対 path を読むだけ)。

## 総括

(a) **条件付き GO。** 前回の must-fix 7 件のうち 6 件は閉じ、古い現在形が並存する型は grep で探し直しても新たに見つからなかった。GO の条件は次の 3 つです。
1. land の直前に、最終 bytes(§10 の完了形化と fix_peer30 の適用を含む)で claim-evidence の入力 sha256 を再計算し、一致を確かめる(A-M6)。
2. fig3c を実際に生成し、保存前の layout check を通す。副ラベルは fig3b より長い(B-9 は 110 字、B-8 は 103 字、B-7 は 102 字)。
3. 新規の should-fix 3 件(§7 継承表の「内容は不変」、30 枠の帰属、本文 3899 の未来形)を当てる。

(b) must-fix と should-fix の計 24 件の内訳は、closed 21 / partial 2(A-M6、A-S9)/ regressed 0 / 意図的不採用 1(B-S1)。不採用の理由は妥当で、補足は figures README では足りているが、本文と持ち越しの記録には無い。

(c) 新規所見は must-fix 0 / should-fix 3 / nit 14。

(d) 未確認の範囲:
- fig3c の実生成、layout check、図の rc。figures-fig3c.md の 91 行「実走の rc=0 で確かめた」は、図を作る前に書いた完了形なので、生成後に実際の結果と照合する必要がある。
- 本文 5,904 行の通読。確認は grep と、該当する §0 / §2 (g) / §6 / §7 / §8 の各【状態】と B-8 項 / §9 / §10 の範囲に限った。
- claim-evidence の行の内容照合。行ごとに前稿との差分の有無を機械的に比べたが、内容まで照合したのは C25・C34・C35・C42・C44・C45、L40・L59・L75、§6、§7 だけである。
- fix_peer30.py は未適用なので、適用後の現物は見ていない。
- README は readme.diff と、表の行の grep だけを見た。
- D2200 の本文は読んでいない。段階認可の範囲は本文 §0 の 2 と、一貫性の照合で代えた。
- 実行を伴う検査(test・変異・作図)は一切行っていない。変異の結果は job dir の JSON の summary を読んだだけである。
