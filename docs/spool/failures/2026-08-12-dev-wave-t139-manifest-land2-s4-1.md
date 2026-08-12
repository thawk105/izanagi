---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-08-12
wave: dev-wave-t139-manifest-land2-s4
seq: 1
---

## 新規

### {{F:approval-scope-splits-within-one-field}}. 承認済み文書の「どこまで承認済みか」が同じ field の中で節の粒度に割れており、導出規則の凍結を serialization の凍結と読み違えた [誤前提] [ドリフト]

- 事象: [T-139] land 2 session 4 の親が段 1 の実測として
  「`a09` の schedule は承認済み文書で完全に凍結されている」と結論し、逐語 seed
  (`7df15572…`)・導出式 `key(j, w, p)`・preimage の byte grammar・tie-break を根拠に
  「独立再導出は承認済み仕様の実装であって機構の新設ではない」と一般化して、
  段 3 の敵対レンズへ**攻撃対象の実測値として前渡しした**。
  段 3 レンズ A がこれを半分誤りと判定した。追補 A `a09` が凍結しているのは**導出規則まで**で、
  schedule 表の **serialization (canonical TSV・header・157 行・並び順) は
  `record-items-v2.md` §10 が「承認済み文書から一意には導けない選択」として明示した
  未承認閉包 8 件の第 4 番**である。
- 根本原因: 承認範囲を **field 名の粒度**で確認した。`a09` という 1 つの field の中に、
  承認済みの部分 (導出規則) と未承認閉包 (serialization) が同居していた。
  `a09` の節は「canonical bytes の SHA-256 を受領証へ記録する」と要求するだけで
  serialization を定めておらず、それを定めたのは**別文書の別節** (§10) である。
  親は `a09` の節だけを読み、§10 の閉包表と突き合わせなかった。
  実害は設計判断に直結した — この誤前提のままなら、PBS driver が canonical schedule digest を
  名乗る実装を承認済み仕様の実装として通し、**Q1/Q2 が「機構を新設しない」と見送った当の閉包を
  再導入していた**。
- 恒久対応: 承認済み文書に依拠して「これは新設ではなく既承認仕様の実装だ」と主張するときは、
  当該 field の節だけでなく、**同じ成果物の「未承認閉包」「本書が新設した閉包」「本書が保証しない
  こと」に相当する節を必ず突き合わせる**。izanagi では `record-items-v2.md` §10 と
  追補 A 末尾の「本書が主張しないこと」がその節に当たる。
  検出は本 wave では段 3 の敵対レンズが担った (親の実測値とその一般化を攻撃対象に含める
  `DW-S03` の規定が機能した実例)。
- 再発検知: 「承認済み仕様の実装であって新設ではない」という主張を brief に書いた wave は、
  段 3 のレンズ prompt にその主張を**攻撃対象の実測値として明示的に載せる**。
  載せた主張が「当該 field の節だけを根拠にしている」なら、レンズは同じ成果物の未承認閉包表を
  突き合わせて反証できる。本 wave はこの経路で検出した。

### {{F:brief-cites-own-measured-absence-as-authority}}. 自分で「canonical に存在しない」と測った decision を、同じ brief の別の節で受理条件の根拠として引いた [誤前提]

- 事象: 同 session の段 1 brief は、実測節に
  「canonical `docs/decisions.md` は D319 まで。解除 decision も
  粗い provenance 標準の decision も canonical に無い (grep 実測)」と書きながら、
  provisional 裁定 (P5) では「粗い provenance はその同じ decision が
  **既に認めた水準**である」と書いた。段 2 のプラン起草と段 3 レンズ B が独立に自己矛盾を指摘した。
- 根本原因: 裁定の**内容**(ユーザーが「見送る」と決めた) と、その裁定が**canonical 台帳へ
  fold された状態**を同一視した。ユーザー裁定は成立していたが、それを記録する decision は
  未 land branch 上にしかなく、canonical には無い。D292 が「wave の自己申告・manifest の宣言・
  handoff の記載では解除しない」と定めるのと同じ区別である。
  実害は proof chain の権威主張に直結した — 「粗い provenance で足りる」と canonical decision が
  認めていない状態で、collector 出力を材料レポートの proof chain に使えると読む余地を作った。
- 恒久対応: brief で「既決により X してよい」と書くときは、その既決が
  **canonical 台帳に fold 済みか、未 land の控えに留まるか**を明示する。
  後者なら、根拠として使えるのは「その wave が何を実装しないか」の**scope 決定まで**であって、
  成果物の**受理条件・権威主張**には使えない。
  なお本件は F1 (既存 docs を一次資料と一致するまで根拠にしない) とは型が違う —
  一次資料は正しく読めており、**同一 brief 内での前提の取り違え**である。
- 再発検知: brief に「canonical に無い」と書いた識別子を、同じ brief 内で全文検索する。
  実測節以外の出現が受理条件・権威主張の根拠になっていれば自己矛盾である。
  本 wave では段 2 と段 3 レンズ B が独立に指摘した。
