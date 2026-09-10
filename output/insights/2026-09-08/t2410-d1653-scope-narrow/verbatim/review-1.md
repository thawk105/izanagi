## 所見

- [重大度: 高] D1653 の却下欄に同じ広すぎる主張が残っており、「1 箇所だけ」という実測も誤っている

  (a) D1653 には、理由欄の訂正対象とは別に次の文がある。

  > **旧記録を新閉包で発行し直す** — 規律 7 に反し、下流の digest 鎖と凍結成果物を巻き込む。

  [docs/decisions.md:50703](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2410-d1653-scope-narrow/docs/decisions.md:50703)

  一方、fragment は理由欄の先頭文だけを撤回し、「D1653 の決定本体 (`HISTORICAL_RAW` に限った別 decoder、必須の条件、却下した選択肢) は変更しない。」としている。

  [decision fragment:11](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2410-d1653-scope-narrow/docs/spool/decisions/2026-09-08-dev-wave-t2410-d1653-scope-narrow-1.md:11)  
  [decision fragment:18](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2410-d1653-scope-narrow/docs/spool/decisions/2026-09-08-dev-wave-t2410-d1653-scope-narrow-1.md:18)

  worklog の次の主張も反証される。

  > **広すぎる表現の所在は 1 箇所だけだと実測した。** `git grep` で「規律 7 に反する」を `docs` / `orchestrator` / `tools` (archive を除く) へ当て、D1653 の理由欄 第 2 項のほかに同じ主張は無いことを確かめた。コードにも他の docs にも無く、記述修正の変更面は台帳だけである。

  [worklog fragment:18](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2410-d1653-scope-narrow/docs/spool/worklog/2026-09-08-dev-wave-t2410-d1653-scope-narrow-1.md:18)

  検索語が「反する」だけなので、活用形「反し」を落としている。

  (b) 放置すると D1653 の却下欄だけを読んだ作業者には「再発行一般が規律 7 違反」という旧解釈がそのまま残る。必須条件や実装の受理集合を直接変更はしないが、D1770 が命じた記述修正を完遂できず、同一エントリ内に撤回済み主張と未撤回の同義主張が併存する。

  (c) decision fragment の決定冒頭を次へ置換する。

  > **決定 (ユーザー裁定 D1770 の実施):** D1653 の理由欄 第 2 項の先頭文「記録を新閉包で発行し直す案は規律 7 に反する。」を撤回する。あわせて、却下した選択肢 第 1 項「**旧記録を新閉包で発行し直す** — 規律 7 に反し、下流の digest 鎖と凍結成果物を巻き込む。」のうち「規律 7 に反し」を撤回する。D1653 が当該 lock 群の発行し直しを却下した結論、下流の digest 鎖と凍結成果物を巻き込むという理由、および必須の条件は変更しない。

  worklog の該当項は次へ置換する。

  > - **広すぎる表現は D1653 の 2 箇所にあることを実測した。** 理由欄 第 2 項の「規律 7 に反する」と、却下した選択肢 第 1 項の「規律 7 に反し」が同じ広すぎる主張を持つ。本 wave の新規 decision は両方を名指しして撤回する。

- [重大度: 中] 射程外の一般的な再発行判定規則を新設し、既存前提を十分条件から落としている

  (a) fragment は一般規則を却下すると言いながら、直後に次の一般規則を断定する。

  > どの成果物を再発行してよいかは、成果物ごとの時間付き束縛と下流 digest 鎖の有無で個別に決まる。

  [decision fragment:48](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2410-d1653-scope-narrow/docs/spool/decisions/2026-09-08-dev-wave-t2410-d1653-scope-narrow-1.md:48)

  また理由欄は「正当な追記・取り直しまで止まる」とするが、規律 7 本文には次の留保がある。

  > **新しい測定はいつでも開始できる。開始条件に、過去の承認済み状態とのコード同一性を置かない。** 事前登録の充足・凍結・環境契約・較正・correctness gate といった、**同一性と無関係な前提条件はそのまま残る**

  [CLAUDE.md:101](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2410-d1653-scope-narrow/CLAUDE.md:101)

  (b) 「時間付き束縛と下流 digest 鎖の有無で決まる」は、その二要素が再発行可否の十分な判定基準であるかのように読める。凍結、事前登録、環境契約、較正、correctness gate などを満たさない成果物でも、二要素だけを根拠に再発行できるという受理集合拡大の余地を作る。これはユーザーが scope 外とした一般化でもある。

  (c) 却下欄を次へ置換する。

  > - **再発行の可否を一般規則として書く** — 本決定の射程は D1653 が対象とした lock 群の当該理由文の訂正に閉じる。本決定は、それ以外の成果物の再発行可否や、その判定条件を定めない。既存の事前登録、凍結、環境契約、較正および correctness gate は変更しない。

  理由欄末尾の「正当な追記・取り直しまで止まる」は次へ置換する。

  > 広すぎる読みを残すと、既存の前提条件を満たす新しい測定や、後日作った派生記録の発行まで規律 7 だけを理由に一律に拒否する誤読を招く。本訂正は、それらに課される既存の前提条件を変更しない。

- [重大度: 低] worklog が合成した説明を一次資料の「逐語」と誤記している

  (a) worklog は次のように記す。

  > 規律 7 が禁じるのは「live capture された時間付き束縛の代替として後から作った記録を扱うこと」であって、派生記録の発行そのものではない。この逐語は本 wave が新たに測ったものではなく、当該 insight が既に凍結している。

  [worklog fragment:21](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2410-d1653-scope-narrow/docs/spool/worklog/2026-09-08-dev-wave-t2410-d1653-scope-narrow-1.md:21)

  一次資料の実際の逐語は次である。

  > 一方、D1653 の「旧記録を新閉包で発行し直すのは規律 7 に反する」という表現は広すぎる。旧 bytes を残したまま「後日作った派生記録」と明示して新 artifact を発行すること自体は規律 7 が禁じていない。**正確な境界は「その新 lock は当時の測定時 lock の代替にはならない」**である。

  [insight README.md:150](/work/1/SFC/tanab/izanagi/output/insights/2026-09-07_t2254-old-grammar-cause/README.md:150)

  (b) 意味上の根拠はあるが、worklog の引用内文は複数文を合成した新しい規範文であり、一次資料の逐語ではない。放置すると、後続作業者が一次資料に実在する文と誗認する。

  (c) worklog の該当項を次へ置換する。

  > - **訂正後の境界の一次資料は `output/insights/2026-09-07_t2254-old-grammar-cause/README.md` §5.2。** 同節は、測定後に時間付きの事実を復元できないこと、後日作った派生記録と明示した新 artifact の発行自体は禁止されないこと、および新 lock は当時の測定時 lock の代替にならないことを記録している。本 wave の decision 文はこれらを統合した記述であり、一次資料からの逐語引用ではない。

- [重大度: 低] 「この 13 件」が D1653 の 11 件との関係および実測母集団を示していない

  (a) D1653 は「外部 root の official lock 11 件が該当し、そのうち 3 件は論文図 fig2c の生成経路が実際に読んでいた。」とする。

  [docs/decisions.md:50681](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2410-d1653-scope-narrow/docs/decisions.md:50681)

  後続の一次資料は 13 件を確認しているが、明示的に範囲を限定する。

  > 範囲の限定: 走査したのは `/work/1/SFC/tanab/b10-backoff-grid-runs5` と `/work/1/SFC/tanab/izanagi-measurements` の 2 root だけである。「13 件」はこの 2 root での file path 数であって、保管領域全体の網羅ではない。D1563 が書いた 11 件は 2026-09-03 時点の数で、その後 A-2 が 2 件増えている。

  [insight README.md:81](/work/1/SFC/tanab/izanagi/output/insights/2026-09-07_t2254-old-grammar-cause/README.md:81)

  D1770 の内訳は B10 3 件と A-2 10 件であり、13 件という算術自体は一致する。

  [docs/decisions.md:53793](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2410-d1653-scope-narrow/docs/decisions.md:53793)

  (b) 数値は正しいが、fragment 内の「この 13 件」は先行する D1653 の 11 件から突然切り替わり、さらに保管領域全体の総数のようにも読める。受理集合は変えないが、対象 corpus の同一性と実測範囲を曖昧にする。

  (c) 「この 13 件については」を次へ置換する。

  > D1770 が対象とした 13 件、すなわち一次資料 §3 が `/work/1/SFC/tanab/b10-backoff-grid-runs5` と `/work/1/SFC/tanab/izanagi-measurements` の 2 root 内で旧 grammar への exact ordered 一致を確認した file path 13 件については

- [重大度: 低] D1770 では撤回文が名指しされていないという手続き理由と、新規追記が D1653 単独読みを塞ぐという含意が成立しない

  (a) fragment は次のように記す。

  > **D1770 の 1 文で足りるとする** — D1653 側から D1770 への手がかりが無く、撤回される文が名指しされない。読み手が D1653 だけを引く経路が塞がらない。

  [decision fragment:44](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2410-d1653-scope-narrow/docs/spool/decisions/2026-09-08-dev-wave-t2410-d1653-scope-narrow-1.md:44)

  しかし D1770 は次のように D1653 と対象表現を名指ししている。

  > あわせて D1653 の「再発行は規律 7 に反する」という表現は広すぎるので、**射程を「live capture された時間付き束縛について」へ狭める。**

  [docs/decisions.md:53785](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2410-d1653-scope-narrow/docs/decisions.md:53785)

  また spool の不変条件は「canonical の**既存 bytes は不変**。fold が行うのは末尾への追記と、次の 4 種の挿入だけである。」であり、decision への backlink 挿入は存在しない。

  [docs/spool/README.md:116](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2410-d1653-scope-narrow/docs/spool/README.md:116)

  (b) 新規 decision 追記という手続き自体は D548 と一致し、decisions 側に failure の `supersede 追記` 相当の機構もないため妥当である。ただし新規追記も D1653 の既存 bytes に手がかりを追加しないので、「D1653 だけを引く経路」は塞げない。誤っているのは手続きではなく、その必要性と効果の説明である。

  (c) 該当する却下項を次へ置換する。

  > - **D1770 の記録だけで訂正作業を終える** — D1770 は D1653 と広すぎる表現を名指ししているが、D1653 内の撤回対象 2 箇所を逐語では特定していない。D548 と同じく、新規 decision で撤回対象と訂正後の理解を逐語に記録する。canonical の既存 bytes は変更しないため、この追記が D1653 本体へ backlink を追加するものではない。

## 総括

real の所見は 5 件（高 1、中 1、低 3）。最重は、D1653 の却下欄に同じ広すぎる主張が残り、訂正が未完である点。  
親が採るべき最小修正は、D1653 の 2 箇所をともに撤回し、worklog の「1 箇所」を「2 箇所」へ直し、射程外の一般規則を削ること。