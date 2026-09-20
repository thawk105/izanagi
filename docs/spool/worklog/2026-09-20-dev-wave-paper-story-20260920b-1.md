---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-20
wave: dev-wave-paper-story-20260920b
seq: 1
title: 論文ストーリー 2026-09-20 第 2 版 (`2026-09-20b.md`) を正典全体から全項目再導出した — 凍結 v2 g1 の発効 (AI 委任の A / X、launch validation は未達) と B-7 の限定付き充足を取り込み、裁定待ち 4 件の裁定と 3 件の実装着地・単独稿 6 本・図 5 本を反映し、README の stale 注記 3 件を本文へ畳み、前版の執筆時点の誤りを 1 件 (「非列挙」未裁定、5 版連続) 訂正した (docs のみ、branch worktree-dev-wave-paper-story-20260920b、実装面差分ゼロにつき変異 matrix 免除)
---

## 本文

- 依頼は「論文ストーリー次版 `docs/paper-story/<着手日>.md` を正典全体から全項目再導出する (docs-only、前例 = 2026-09-20 版 wave の
  README §3)。着手直前の local main から fresh worktree。現行版 2026-09-20 以後に着地した results 稿 5 本 (mocc-g2 観測条件、mocc-witlight
  4 arm、K2 手動 loop 3 巡、S-1a 9 対、B-10 待ち方 grid 正式走) と着地していれば p24 静的 sweep 稿、図 5 本 (fig8b、fig10、fig11、fig12、
  fig3b) を反映し、現行版の事実誤認 2 点 (§4「第 2 cohort は fig8 に描かれていない」、§8 B-1「非列挙の定義の置き直しは未裁定」) を
  訂正する。資料の締切は着手時の local main に固定し p24・A-1 attempt-0002 の完了を待たない。最初に時点語を機械置換し、見出し・括弧書きの
  状態語も D 本文へ再照合する。README は受入の owned-path に入れず、表行は段 7 で main を取り込んでから当てる。§10 は草稿では予定形。
  英語稿・2 本目論文の版は作らない。gate・検査・台帳の追加は scope 外」。**全項目の再導出であり、一項目の差分改訂ではない。** 既存の版
  10 本・`results/` 19 稿・`figures/`・`claim-evidence/`・`docs/paper-story-backoff/` は 1 byte も変えていない。新規計測ゼロ。
- 版名は `2026-09-20b.md` (同日 2 版目。着手日が現行版と同じ日付なので、README の「新しい日付のスナップショットを追加する」規則を
  「新しい版を別 file で追加する」として適用。版の履歴表の日付欄は「2026-09-20 (第 2 版)」)。導出の起点は local main `fec4a8187`
  (2026-09-20 18:01 JST、entry 1746 までの fold を含む)。前版起点 `b7f970dfa` から entry 1712〜1746 の 35 件と D2165〜D2183 が加わった。
- **依頼が「事実誤認」と呼んだ 2 点の型判定 (段 1 で commit の祖先性と日時を実測):** (a) §4 の fig8 の文は、fig8b の commit `864d7135e`
  (08:05 author) が前版起点 `b7f970dfa` にも前版の fold `24bc8441b` (09:11) にも含まれず main 着地は 10:36 以後なので「当時は真で後続が
  古くした」型 — 訂正一覧には載せず本文で更新し、README の stale 注記に積まれていなかった分も吸収した。(b) 「非列挙」未裁定は D1441
  (2026-09-02、fold 07:43) で裁定済みで、2026-09-02 版 (fold 04:42) は当時真、2026-09-05 / 09-14 / 09-17 / 09-19 / 09-20 の 5 版 (各 2 箇所)
  は**執筆時点の誤り** — 前版は §8 B-5 で D1441 を引きつつ 4 か所で「未裁定」と書き版内で矛盾していた。冒頭の訂正 1 として 4 か所を
  「D1441 で操作的定義へ裁定済み。その定義の下で段階 B を再走した wave は無く、軸は休眠 (D52、D2158)」へ直した。F1 の再発 (実害) として
  failures へ追記。
- 反映集合: 依頼名指しの稿 6 本・図 5 本、README の stale 注記 3 件 (fig10・B-7 限定付き充足・fig12)、§6 / §8 の状態語を動かす裁定・実装
  (g1 の発効 D2166 / D2167 / D2180、B-7 D2174 項 3、A-1 rear gate D2178、K2 pair launcher D2183、B-5 段階裁定 D2172 項 4、B-8 事前登録
  D2175、fig8b D2173、mocc 追加実験の見送り D2172 項 7、受入 pairing の採用裁定 D2172 項 1)。それ以外の着地 (D2165 / D2168〜D2171 /
  D2176 / D2177 / D2179 / D2181 / D2182、T-2789 / T-2791 / T-2796 など) は §2 (e) / §5 の運用素材と状態語の訂正だけ。新しい主張は足して
  いない。**g1 の発効は「凍結 v2 g1 が発効した」と書き、「床値が発効したので oracle が走れる」「official 床値が科学的に有効」「人間が批准した
  holdout」とは書かない** (批准 loader は成功、full launch validation は既存不整合 2 件で `allowed: false` = [T-2810]、W-4 / W-5 は未、
  床は配線下限の値のまま、「AI が自己承認した世代」の呼称は D2180 の対象外)。**B-7 の充足は 4 語の限定 (単一 attempt・descriptive・
  非認証・反復間安定性は未判定) を必ず添え、報告要件であって採用・性能主張ではないと書き、§9 の 4 文へ入れない。** A-1 / K2 / B-5 は
  「gate / launcher / 共有部品の一部が着地」までで投入は 1 job も無い。「A-1 の値がある」「B-10 を閉じた」「再現されたので飽和しない」
  「mocc は第 2 成功例」「B-8 を取得した」「K2 で改善した」「pin を前進させた (基準 HEAD 時点)」は書いていない。
- 作り方: 前版を複製し、**最初に「前版」→「2026-09-19 版」(191 件)、「この版」→「前版」(178 件)、「本版」→「前版」(3 件) の機械置換を
  当ててから**、冒頭・§0・§2 (g)・§10 を全面差替え、他節は exact 1 回一致・all-or-nothing の置換 (job dir の script 21 本、186 件、
  fail-closed) で再導出した。§7 は前版の後半 11 項を前半末尾へ移し (87 項)、この版で 13 項を足した (計 100 項)。§0 は 13 点、§2 (g) は
  14 点、§2 (e) の運用素材はこの版で 7 つ。機械置換後の自己点検 (「未発効」「人間手番」「裁定待ち」「図は無い」「繰延べ」を grep) で
  16 件を付け替え、空白抜け 2 件を直した。
- 段構成は軽量版 (段 2・3 省略、段 5 = 親の docs 編集)。**段 6 は D2148 項 11 の read-only レビュー 1 本 (Codex gpt-6-astra、26 call、
  wall 510 秒、19:06〜19:14 JST) が NO-GO・所見 10 件 (must-fix 6 / should-fix 2 / refuted 2) を返し、親が一次資料で検算して real 8 /
  refuted 2** (refuted 2 件は親の型判定 (fig8b = 後続型、非列挙 = 裁定済み) をレビュー自身が攻撃候補として立て、自ら refuted と裁定
  したもの)。最重要は転記の誤り 3 件 (S-1a 稿の限定件数 16 → 19 = cohort2 稿の値を写した、fig8b の PDF SHA-256 `c5454544…` → `c5454454…`
  = 16 桁の目視、2026-09-02 版の着地時刻 07:14 → fold `45994d900` 04:42 = first-parent の merge を着地と誤認) と、B-5 の「試走を投入可能に
  する経路」の先取り (共有部品の一部が着地、試走に要る実装は残る、へ)。fix は `r22.py` (置換 15 件)。焦点再レビュー 1 本 (13 call、230 秒)
  は closed 10 / partial 0 / regressed 0 + 新規 must-fix 1 (§7 の前版由来の項目が supersede 済みの D2044 項 3 を恒久規律として残していた)
  で NO-GO → 親が対案どおり `r24.py` (置換 3 件 + 1) で直し、`check_docs` と path / D / F 実在検査を再走して閉じた (DW-O16、3 巡目は
  起動せず)。転記 SHA の集合比較 (`check_hashes.py`、8 桁 prefix 43 件) を訂正後に走らせ、29 件一致・残り 14 件は commit / identity /
  較正の digest。near-miss 3 件は F1 の再発として failures へ追記。**受入の claim 前の自己点検で、親の「実装残件として起票された項目も無い」
  (§8 B-1 ほか 5 箇所) が誤りと判明した** — 次の一手に [T-1871] (D1441 の 4 点を事前登録の追補として置く、裁定済み・実装待ち) が carry stub で残って
  おり、親は語で走査して stub の本文 (entry 1184) を遡らず、段 6 の 2 レビューも拾わなかった (レビュー 10 は「全履歴の不在は証明していない」と
  限定)。peer の着地通知 (追補 1 = entry 1752) を契機に直した (`r26.py`、5 件)。F1 再発 (near-miss) として failures fragment に追記。
- 検査: `check_docs.py` 違反なし (5 回)、三軸語走査は両 holdout とも hit 4 (official 床値 run dir 3 file + 候補 = chain 着地後の設計どおり、
  新版 file は hit 外)、引用 path 223 件の実在 (不在は相対断片 13 件と attempt-0002 の期待公開先 1 件)、D 231 件・F 17 件の見出し実在、
  祖先性 / 日時 33 件 (X1' / X2 / G / merge `629690fdd` / `0e647f84c` / A `a3bf67a8c` / X `70e87c9c9` / `ca3907e57` / fig8b は HEAD の
  祖先、fig8b は前版起点と前版 fold の祖先でない)、基準 HEAD の gitlink `511c9538`、`EXPECTED_FREEZE_TREES_SHA256` = `92099c87…`、
  A / X の record file 実在、NFC、`git diff --check` 0。一次資料は `output/insights/2026-09-20/paper-story-20260920b/README.md`
  (prompt・出力の逐語は同 `verbatim/`、レビュー出力 2 file は行末空白だけの可逆正規化、原文 sha256 は receipt と `verbatim-normalization.json`)。
- README は段 7 で local main `800178b39` (entry 1749 まで) を ff-only で取り込んでから更新した (版の履歴表 1 行、「最新 = `2026-09-20b.md`」、
  訂正一覧を「1 件」へ、stale 注記 3 件を本文へ移管し、着手後に着地した ccbench pin 前進 [T-2304] (D2184、entry 1747、main `6a3e15809`
  19:03 JST) を 1 件積んだ — 同版が「基準 HEAD の pin は `511c9538`」「pin 前進は承認済み・未実施」と書く箇所は起点 `fec4a8187` の時点で
  真。peer wave と重複しないことを SendMessage で確認して本 wave が積んだ)。取り込みで submodule の gitlink が `e9e477ca` へ進んだので
  `dev_wave_submodule_init.py` を再走した。受入の claim 前 (門番待ち中) に peer の着地通知 (A-1 attempt-0002 完走) から main を再読し、
  entry 1751〜1755 のうち版の状態語を動かす 4 件 ([T-1871] の追補 1 = entry 1752、第 26 回裁定 D2186 の B-8 段階認可 = 1751、K2 pair の初投入と
  pair 不成立 D2187 = 1754、A-1 attempt-0002 の完走と単独稿 = 1755) を stale 注記へ追加した (計 5 件。版本文は起点の状態のまま)。
- 段 5 の途中に peer wave (`dev-wave-t2304-pin-advance`) から advisory 3 通 (main の ff、land の rc=27 一時停止、landed) を受けたが、
  peer 通知は local main 再読の契機にだけ使い、起点は依頼どおり動かさず、land は同 wave の tool 修正 (main `108c16ddf` 以降) を取り込んだ
  tip で行う。
- 焦点走 (paper-story を読む test 9 file、計算ノード dispatch) と受入全走 (記録 commit 後の最終 tip で 1 走、README は owned-path 外) の
  結果は受領証と land の記録が持つ。child-green でなければ land しない。
- 工数: codex 子 2 本 (review 1、focus 1、全段 gpt-6-astra / medium)。author / fix 子は 0 (実装面ゼロ)。親: 前版全 10 節 (3,866 行)、
  entry 35 件の見出しと 12 件の本文、D 19 件、稿 6 本の冒頭、figures README 5 節、insight 12 本、path 223 件、SHA 集合比較 2 回。

## 次の一手差分
