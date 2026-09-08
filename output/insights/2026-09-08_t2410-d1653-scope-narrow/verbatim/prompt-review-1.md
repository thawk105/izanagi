単独段 dispatch: stage=review; sandbox=read-only; parent=/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2410-d1653-scope-narrow

必読事項の射影:

- `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2410-d1653-scope-narrow/docs/spool/decisions/2026-09-08-dev-wave-t2410-d1653-scope-narrow-1.md` — 本レビューの主対象 (新規 decision fragment)。読めなければ即停止。
- `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2410-d1653-scope-narrow/docs/spool/worklog/2026-09-08-dev-wave-t2410-d1653-scope-narrow-1.md` — 副対象 (worklog fragment)。読めなければ即停止。
- `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2410-d1653-scope-narrow/docs/decisions.md` の D1653 (`## D1653.` を検索)、D1563 (`## D1563.`)、D1770 (`## D1770.`)、D548 (`## D548.`) の 4 エントリ本文 — 訂正対象と根拠。読めなければ即停止。
- `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2410-d1653-scope-narrow/CLAUDE.md` の「絶対規律」節、特に規律 2 と規律 7 — 弱体化の判定基準。読めなければ即停止。
- `/work/1/SFC/tanab/izanagi/output/insights/2026-09-07_t2254-old-grammar-cause/README.md` の §5.2 と §6 — 訂正後の境界の一次資料。読めなければ即停止。
- `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2410-d1653-scope-narrow/docs/spool/README.md` と `docs/spool/decisions/README.md` — fragment の形式契約。読めなければ即停止。

## 依頼

あなたは敵対レビュー役である。上記の新規 decision fragment (と worklog fragment) を**守らず攻撃する**。
親が書いた文であり、親の判断も検査対象である。

背景。ユーザー裁定 D1770 が「D1653 を追認し D1563 を supersede する。あわせて D1653 の
『再発行は規律 7 に反する』という表現は広すぎるので、射程を『live capture された時間付き束縛に
ついて』へ狭める」と定めた。本 wave はその記述修正だけを行う。新規実装はしない。
canonical 3 台帳の既存 bytes は fold 以外が変更できないため、訂正は新規 decision の追記で表している
(D548 が同型の先例)。

## 攻撃してほしい観点

1. **規律 2 / 規律 7 の弱体化。** この訂正文を読んだ将来の作業者が、「凍結成果物を作り直してよい」
   「測定時の束縛を後から作り直せる」と読み取れる余地はあるか。受理集合や correctness gate を
   1 mm でも緩める含意があるか。あるなら、どの文のどの語がそう読めるかを逐語で示せ。
2. **逐語の正確さ。** fragment が D1653 / D1770 / §5.2 から引いた文言・主張は、原文と一致するか。
   引用元に無い主張を足していないか。特に「13 件」「第 2 項の先頭文」といった具体の指示子が
   原文の実体と一致するかを現物で確かめよ。
3. **射程超過。** ユーザーは「本題の記述修正だけ。仮想リスク向けの gate・検査・台帳・一般化の追加は
   scope 外」と明示した。fragment に一般規則の新設や、裁定されていない判断が紛れていないか。
4. **手続きの妥当性。** 「既存 D の bytes を書き換えず新規エントリで訂正する」という判断は、
   D548・`docs/spool/README.md` の不変条件に照らして正しいか。より適切な既存機構
   (例えば失敗台帳の supersede 追記に相当するもの) が decisions 側にも在るのに見落としていないか。
5. **worklog fragment の主張の真偽。** 「広すぎる表現の所在は D1653 の 1 箇所だけ」という実測主張は
   現物で確かめられるか。反例があれば path と行を挙げよ。
6. **無効化・恒真化。** この訂正が、D1653 の必須条件や却下欄のいずれかを事実上無効化していないか。

## 制約

- **read-only sandbox である。書込み可能な tmp が無いため pytest を走らせて緑を示す必要はない。**
  静的検査 (現物の読み比べ) でよい。テストの実測は親が行う。あなたが走らせていない検査を
  「緑だった」と書いてはならない。
- ファイルを書けないので、**成果物は最終メッセージ本文にすべて書く。** 途中経過を file へ出さない。
- 予算が尽きそうなら、途中結論を下の出力形式どおりに書いて終われ。無出力が最悪である。
- repo を編集しない。commit しない。branch を触らない。
- 逐語引用は省略記号で切らない。引くなら原文のまま全文を引く。
- 「直すべき」と言うときは、置き換える文案を逐語で示せ。

## 出力形式

次の H2 節をこの順で書く。

## 所見

各所見を `- [重大度: 高|中|低] <1 行要約>` で始め、続けて (a) 根拠となる逐語と path、
(b) 何が起きるか (放置したときに成果物・受理集合・読み手の理解がどう変わるか)、
(c) 提案する置換文案、の 3 点を書く。所見が無ければ「所見なし」と書き、
**そう判断するために現物のどこを読んだかを列挙する**。

## 総括

real と判定した所見の件数、最も重い 1 件、親が採るべき最小の修正を 3 行以内で書く。
