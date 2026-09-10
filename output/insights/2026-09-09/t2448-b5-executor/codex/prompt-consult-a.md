単独段 dispatch: stage=consult; lane=sol; sandbox=read-only; parent=/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2448-b5-executor

必読事項の射影 (読めなければ即停止):
- /home/SFC/tanab/.claude/jobs/33fc4cd7/tmp/dev-wave-t2448-b5-executor/brief.md (親の段 1 brief。**これ自身も攻撃対象である**)
- /home/SFC/tanab/.claude/jobs/33fc4cd7/tmp/dev-wave-t2448-b5-executor/plan_1.md (段 2 のプラン。主たる攻撃対象)
- /home/SFC/tanab/.claude/jobs/33fc4cd7/tmp/dev-wave-t2448-b5-executor/rulings-verbatim.md (D95 と D1895 の逐語)
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2448-b5-executor/docs/related-work/claim-survey/2026-09-07-backoff-axis-b5-search-preregistration.md
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2448-b5-executor/docs/related-work/claim-survey/2026-09-08-backoff-axis-b5-closure-preregistration.md
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2448-b5-executor/docs/related-work/claim-survey/2026-09-08-backoff-axis-b5-closure-record.md
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2448-b5-executor/orchestrator/axis_b5_search/catalog.py
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2448-b5-executor/orchestrator/axis1_search/ (先例)

## 役割

あなたは dev-wave 段 3 の敵対検証子 (レンズ A = **正しさ境界**) である。read-only sandbox なので書込み可能な tmp は無く、
pytest は走らせなくてよい (静的検査でよい)。**プランを守らせるのではなく、壊しに行くのが役目である。**
親の brief も段 2 のプランも、どちらも誤りうる。親の実測値とその一般化も疑ってよい。

対象は軸 B5 の文献調査実行器である。この実行器が守るべき正しさは「性能」ではなく
**事前登録の意味が実行によって損なわれないこと**である。次の観点で攻撃せよ。

## 攻撃の観点

1. **完走述語を緩める経路** (部分登録 §5.1 の 6 条件)。プランの実装が、
   `meta.per_page` / `itemsPerPage` / `@sent` を実要素数の代わりに使う、最終ページで総件数照合を省く、
   cursor 連鎖の欠落を見逃す、DBLP の `@first` 連続性を見ない、といった形で受理集合を広げていないか。
   **プランに書かれていないために結果的に緩くなる箇所**も探せ。
2. **事後登録になる経路**。部分登録 §2.3 と §5.3 は「preflight の観測をそのまま期待値に据えない」と要求する。
   プランの fixture・期待 echo・期待 AST が、過去の生応答 (`output/insights/2026-09-08_t2380-b5-closure/probe/`) を
   見てから作られる形になっていないか。test の期待値が実装の出力から導かれる自己参照になっていないか。
3. **fail-closed の穴**。live preflight は 1 member でも `不達` / `非収録` なら軸全体を `未完走` にして
   走行を開始させない。プランのどこかに、例外・既定値・「記録だけして先へ進む」経路が残っていないか。
   閉包登録 §2.4 (c) が禁じた「`非収録` を見て member から外す」形が、実装の都合として紛れ込んでいないか。
4. **D1895 違反**。走行前に検索語彙・ブロック所属・枝・cutoff・control anchor・補助探索範囲を緩める効果を持つ
   実装 (正規化のしすぎ、語の小文字化、重複排除、空 query の読み飛ばし等) が無いか。
5. **seal の健全性**。registration preflight が束縛する path 集合に、
   (a) 自分自身の hash を自分に書く自己参照、(b) 束縛したつもりで実際には束縛されない file (新規追加が検出されない、
   directory 単位で見ていない)、(c) 束縛対象から漏れた「実行器」の一部 (import 先、定数を持つ別 file、schema、fixture)
   が無いか。**「実行器の bytes を束縛した」と名乗れるかを、漏れの側から検査せよ。**
6. **親 brief の (P1)〜(P3) の当否**。とくに (P3) で checkpoint / resume を scope 外にしたことが、
   「registration preflight は閉じるが、実行器としては走らせられない」中途半端を作らないか。
   scope 外にすると成果物 (実行記録・`RW3` の主張) がどう変わるかを 1 行で書け。
7. **本 wave で live preflight を実行しない**という親の裁定の当否。実行が必要だと考えるなら、
   誰の認可が要るか、実行すると何が不可逆になるかを書け。

## 出し方

各所見に次を付けよ。**根拠は必ず file:line か凍結文の節番号で示す。**

- `real` / `refuted` の自己判定と、その理由。
- 放置したときに成果物 (実行記録の値・受理集合・`RW3` の主張) がどう変わるかを 1 行。
  これを書けない所見は `nit` と自己申告せよ。
- 是正案。ただし**依拠する裁定の逐語より強い断定をしない**こと。

## 禁止

- ファイルを 1 つも書かない・変更しない。git 操作をしない。外部 network を使わない (名前解決も request も禁止)。
- 凍結済み文書と `catalog.py`、catalog JSON の変更を提案しない。
- 依頼された実行器の外へ、新しい gate・検査・台帳・一般化を足す提案をしない。
  そういう案を出すときは「scope 外の提案」と明記し、実装案ではなく裁定パッケージ候補として書け。
- 出力に結合文字 U+0300〜U+036F を使わない。

## 出力形式

見出しは全部 H2 (`## `) で書く。最後の節は必ず `## 総括` (`#` を 2 個) とする。`### 総括` と書いてはならない。
予算が尽きそうなら途中結論をこの形式で書いて終われ (無出力が最悪)。

## 完走述語を緩める経路
## 事後登録になる経路
## fail-closed の穴
## D1895 との整合
## seal の漏れ
## 親 brief への反論
## 総括
