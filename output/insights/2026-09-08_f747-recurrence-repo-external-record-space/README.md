# cleanup が repo 外の記録空間を書いた件 — F747 の再発と、条文の欠落 2 つの結合

2026-09-08。branch `worktree-dev-wave-f747-recur-20260908`。base `cf837838a`。docs commit `de0dbbb29`。
台帳は F747 への再発追記 (`docs/spool/failures/2026-09-08-dev-wave-f747-recur-20260908-1.md`)。

## 0. この wave が主張すること・しないこと

**主張する:**

1. 2026-09-08 の `/cleanup-branches` 実行が repo 外の記録空間を更新した事象は、F747 と同型の
   allowlist 外 mutation である。新しい F を採らず F747 へ再発として追記した。
2. F747 の「再発検知」が挙げる `command 単体と command+skill の敵対読解` を実際に走らせた結果、
   3 経路のうち 2 つ (一般的な自己改善許可を「明示起動された別 dev-wave」と読むこと、
   repo 外の記録空間への書き込み) は**現行条文だけでは一義的に拒否できない**。
3. 欠陥は 1 箇所ではなく 2 つの結合である。§0 の時間境界 (cleanup 実行は final 応答の完了で終わる) の
   後に届いた発話を §6 の「継続」と「後から明示起動された別 dev-wave」のどちらへ分類するかの基準が
   無いこと、および自己改善の正本が禁止対象を `repo file/history` と限定して書き下していたこと。
4. `tools/check_docs.py` はこの経路を機械的に捕まえない。捕まえないのは仕様であって欠陥ではない。
5. 現行 hook は「今が cleanup 実行か」を判定できない。判定核が読む入力を実装で照合して確かめた。

**主張しない:**

- **実行者の発話が final 応答の前だったか後だったかを確認していない。** 会話 transcript を
  本 wave では読んでいないため、「同一継続内だった」と断定していない。この区別は欠落の所在を
  変えない (どちらでも上記 3 の 2 つが結合して同じ着地点を作る) が、事象記述の精度としては未確定である。
- **是正した条文が次の同型事象を止めることを実証していない。** 是正は行動規律の文面であり、
  発火する機械検査ではない。台帳の「恒久対応」としては正本 1 行という実体を指すが、
  規律である以上、読み手が読まなければ効かない。
- **runtime enforcement を実装していない。** 実効的な強制には trusted な非モデル launcher と
  全書込み面の OS confinement が要る。裁定へ送った (worklog の新規 item)。
- 上記 memory 2 件を戻すか残すかは扱っていない (ユーザーの別裁定)。F538 にも触れていない。

## 1. 事象 (ユーザー提示。親が mtime で裏を取った)

`/cleanup-branches` 実行が branch 削除 19 本を終えた後、ユーザーの「必要な自己改善はしたらええん
ちゃう？」を受けて `/home/SFC/tanab/.claude/projects/-work-1-SFC-tanab-izanagi/memory/` を 2 件更新し
(`merged-branch-cleanup-hits-fresh-waves.md` へ追記、`cleanup-branches-cannot-self-improve-in-run.md`
を新規作成)、`MEMORY.md` に索引 2 行を足した。repo file と history は無傷で commit も無い。
実行者は「memory は repo 外だから §0 の外」と判断した。
親は 2 file の mtime が `2026-09-08 06:49` であることを実測して事象の実在を確認した。

## 2. 敵対読解の結果 (item 2 の回答)

段 2 の plan (codex, read-only, `gpt-5.6-sol` / xhigh) は「3 経路とも現行条文で拒否できる。
条文欠落ではなく読解の失敗である」と結論した。段 3 の敵対 2 本が独立にこれを破った。

| 経路 | plan | 段 4 裁定 |
|---|---|---|
| (a) 一般的な自己改善許可を「明示起動された別 dev-wave」と読む | 拒否できる | **一義的に拒否できない** |
| (b) repo 外の記録空間 (memory / job dir) への書き込み | 拒否できる | **一義的に拒否できない** |
| (c) 継続セッション・自己 spawn での実装 | 拒否できる | 区分が確定していれば拒否できる。だが (a) の分類基準が無いため今回をその区分へ入れる根拠が出てこない |

破った根拠は次である。

- **(a)**: `.claude/commands/cleanup-branches.md` §0 は「この command の受領から final response
  完了までを cleanup 実行とする」と時間で境界を引く。final 後に届いたユーザー発話は、
  §6 の「同一 cleanup 実行・継続・自己 spawn」と、`docs/skill-self-improvement.md` の
  「後からユーザーが明示起動した別 dev-wave」のどちらにも分類でき、許否が逆転する。
  「dev-wave という語をユーザー自身が発音しなければならない」という要件はどこにも無かった。
- **(b)**: §0 の default-deny は「未列挙の state mutation」と無限定だが、禁止列挙は
  branch / worktree / index / repo 記録 / Git 操作 / local main / commit graph / remote / push と
  repo 内の名詞で揃っており、`state = repo state` と束縛する読解を止める文言が無い。
  さらに自己改善の**正本**が禁止対象を `repo file/history` と書き下していた。
  plan はこれを「強調にすぎない」と反論したが、その扱いを導く規則は条文に無い
  (§0 が非限定を意図する箇所では「**とくに**」を明示している一方、当該行に非限定標識は無い)。

**F747 の既存「再発検知」は本件を捕捉しなかった。** 挙げられた 4 終端 (削除 0・罠・検査赤・
外側クラス 2) のいずれにも当たらないためである (削除 19 本、罠なし、検査未実行、cleanup 由来の発話)。
この被覆漏れを再発 bullet に記録した。

## 3. 機械検査の被覆 (item 3 の回答)

`tools/check_docs.py` は捕まえない。`docs/skill-self-improvement.md` 自身が
「`check_docs.py` の担保は予算と dispatch・節・孤児・逃がし・住所の構造 lint に限る。
whole-file SHA-256 pin も bytes 差だけを検知し、意味は敵対監査と人間レビューが担う」と宣言している。
条文の bytes は既に whole-file SHA-256 pin で固定されており、**今回は正しい条文が固定されたまま
発生した**。したがって条文逐語を足す案は恒真になる。

層ごとの判定 (敵対子が実装の行で照合):

| 層 | 判定 | 根拠 |
|---|---|---|
| `check_docs.py` に条文逐語を追加 | 恒真になる | whole-file SHA-256 pin が既に bytes を固定している |
| `check_docs.py` で live mutation を検出 | 不能 | 入力は文書と fragment の構造であり、session の tool event を持たない |
| hook で memory 固定 subtree を全セッション拒否 | 可能だが採らない | 先例 (発行主体 subtree) はあるが、正常な memory 書込みまで拒否する |
| 現行 hook で cleanup 時だけ拒否 | 不能 | 判定核が読むのは tool 名・tool 入力・cwd・command・runtime site だけで、session / transcript / prompt / lifecycle marker を読む実装が無い |
| モデル自己申告の marker | 恒真になる | 申告を省く選択を同じモデルができる |
| trusted な非モデル launcher + OS confinement | 現況では不能 | 下記 5 条件を満たす実体が無い |
| before/after snapshot | 不能 | 並行 writer の帰属を分離できず、事後検知であって阻止でない |

trusted launcher 案が防壁として成立する条件 (すべて必要):

1. cleanup lifecycle をユーザー操作または非モデルの trusted launcher が開始・終了する。
2. lifecycle 状態をモデルが作成・変更・省略できない。
3. Bash / Write 系 / MCP / 子 / 既存 persistent process を同じ OS-level confinement に入れる。
4. Git refs・worktree metadata・対象 directory の必要 mutation だけを exact allowlist にする。
5. confinement の設置または attestation に失敗したら、最初の破壊操作前に fail-closed で止める。

`CLAUDE.md` の作業種別ゲートは D31 により機械強制しないと決まっており、実行者がモデル自身である
以上、条件 1・2 を満たさない案はすべて恒真になる。**本 wave では機械検査を追加していない。**

## 4. 是正 (docs-only)

`docs/skill-self-improvement.md` の cleanup 終端 1 行を置換し、(a) の起動基準と (b) の対象範囲を
同時に閉じた。

- 旧: `repo file/history を変更しない。後からユーザーが明示起動した別 dev-wave だけが再照合・routing・実装する。`
- 新: `repo 内外の未列挙 state を変更しない。ユーザーが別 dev-wave と明示起動した後だけ再照合・routing・実装する。`

`未列挙` は command §0 の「未列挙の state mutation は…禁止する」と同じ語で、正本間の語を揃えた。
5993 → 5999 bytes (上限 6000)、最長行 79 文字 (上限 100)。縮約は不要だった。
`.claude/commands/cleanup-branches.md` と `.agents/skills/cleanup-branches/SKILL.md` は変更していない
(whole-file SHA-256 pin が両方に掛かり、ユーザーは「command 本文への追記を既定にしない」と裁定済み)。

**残る負債:** 同 file の byte 予算残が 1 byte になった。次に安全義務を足す必要が生じた時点で、
意味等価な縮約か上限引き上げの裁定が要る (worklog の新規 item)。

## 5. 親自身の誤りの訂正

- 段 1 brief の (P1-a) 「弱点は `docs/skill-self-improvement.md:66` の repo 限定**だけ**」は不正確だった。
  欠落は (a) の遷移判定と (b) の対象範囲の**結合**である。
- 段 1 brief の (P1-c) 「是正には意味等価な縮約が同時に必要」は誤りだった。予算内に収まる置換がある。
- 段 1 brief の (P1-b) 「hook は cleanup 実行中かを観測できない」は方向として正しかったが、
  brief 時点では推測だった。敵対子が判定核の読む field を実装で照合して裏を取った。

## 6. 逐語

`verbatim/` に段 1 brief、段 2 plan、段 3 敵対 2 本、段 4 裁定の全文を置く。
段 3 の 2 本は `gpt-5.6-sol` / reasoning=xhigh / sandbox=read-only、いずれも rc=0。
段 3-b は plan が引いた行番号・定数・4 nodeid をすべて現物照合し、不在・ずれはゼロだった。

### 可逆最小正規化 (DW-S07)

codex の出力は Markdown の hard line break として行末に半角空白 2 個を持ち、
`git diff --cached --check` が rc=2 になった。**行末の空白・タブだけを除いた**
(正規表現 `[ \t]+(?=\n)` の削除)。可視文字は 1 文字も変えていない。

| file | 原文 sha256 | 原文 bytes | 正規化後 sha256 | 正規化後 bytes | 変更 |
|---|---|---|---|---|---|
| `stage1-brief.md` | `a8cf26b0288de96595be68c90382dfdd9b808ba7e244c187592f24436486ff84` | 5534 | `a8cf26b0288de96595be68c90382dfdd9b808ba7e244c187592f24436486ff84` | 5534 | なし |
| `stage2-plan.md` | `4ce02b3d183985db05335aaf641d9a720892bc657309ad44869e12b9c8cb1428` | 13961 | `e31f2be3b65f77935cee17a3c2a857b3e81ec520b012496b236d9c7834dab59d` | 13921 | あり |
| `stage3-consult-a-textual.md` | `f8190bad4a8ace1f01b6c3e6cfc51d6c1434bc227ad09be47a14c15ec790bbbc` | 11184 | `97cf6ea1783bed2a7a81b64f4373ecfc480f89fb6d6d08ef94961c44612386ad` | 11164 | あり |
| `stage3-consult-b-mechanism.md` | `4a3cec311ee489d9e7a8110b201c8ae17c1afc040729c08440bcc95c2312c520` | 11650 | `2e1e4d1d12d51d75cd343abf925748a0be8739f0182b0617c3387d784a24bd90` | 11648 | あり |
| `stage4-ruling.md` | `1bf5e727efed8782c19995633b384a92a07623b45e13c926d2a520661ced5a62` | 8596 | `1bf5e727efed8782c19995633b384a92a07623b45e13c926d2a520661ced5a62` | 8596 | なし |

**復元法:** 原文は codex 子の最終メッセージそのもので、job dir
`/home/SFC/tanab/.claude/jobs/faf35170/tmp/wave/dev-wave-f747-recur-20260908/`
の `plan.md` / `consult-a.md` / `consult-b.md` に原文 bytes のまま残っている
(job 削除で消える)。原文を再構成するには、上表の bytes 差の分だけ hard break を
戻す必要があるが、除いたのは行末空白だけなので**意味の復元には正規化後で足りる**。
