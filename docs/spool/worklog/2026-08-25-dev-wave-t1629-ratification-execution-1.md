---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-25
wave: dev-wave-t1629-ratification-execution
seq: 1
title: [T-1629] 批准の執行経路を再設計し、AI が成りすませない実行主体なしでは D758 の 3 条件が同時に満たせないことを確定した (docs のみ、実装差分ゼロ、branch worktree-dev-wave-t1629-ratification-execution)
---

## 本文

- **結論は不可能性である。実装差分はゼロで land する。** D758 の 3 条件 —
  (i) 承認入力を AI が合成できない、(ii) その入力が在るときだけ機構が追記する、
  (iii) `hooks/` 配置による現行の AI 追記遮断を迂回せず作り直す — を同時に満たす設計は、
  この host の現行構成では存在しない。骨格と 3 択は
  {{D:ratification-execution-impossibility}}。**現行の防壁と受理集合は 1 mm も動かしていない。**

- **親の brief が置いた provisional 裁定 6 件のうち、2 件が子に壊された。**
  親は「人間が digest の先頭 8 桁を打つ」形を仮に置いたが、段 2 のプラン子が
  「短縮形は衝突検出の義務を増やすだけなので設計から排除し、40 桁の commit ID を丸ごと置く」
  へ差し替えた。ところが段 3 のレンズ B が、その 40 桁行こそ D758 決定 2 が名指しで拒否した
  「行の貼り付け」だと指摘した。**親案と子案が別々の理由で同じ要件を外していた**形であり、
  段 2 だけ、または段 3 だけでは捕まらなかった。

- **親の実測値の一般化が 1 件、子に正しく壊された。** 親は brief で「closure の 25 path を
  直近 30 日で 165 commit が触っている」から人間手番の再発頻度を推定したが、レンズ B が
  「批准が要るのは official な新規 campaign 初期化の直前だけであり、変更版数ではない」と
  指摘した。親が数え直すと `--first-parent` では 64 commit、tracked な official lock の
  新規追加は全期間 13 件・直近 30 日 0 件だった。**頻度を理由に「転記を残す」案を退けることは
  できない。** 親の推論を訂正して裁定へ反映した。

- **レンズ A が最も危険な破れを出した — 提案した handler 自身が無認証の追記 API になる。**
  `hooks/` 配下へ置いた handler も、受け取るのは stdin の JSON だけで、genuine な
  `UserPromptSubmit` と合成 stdin を区別する鍵・署名・capability を持たない。レンズ A が
  `guard_bash.decide()` を副作用なしに静的評価したところ、`printf ... | python3 hooks/<handler>.py`
  も単独起動も許可された (script-file interpreter は read-only 扱い)。handler 内部の
  `commit-tree` / `update-ref` は PreToolUse から見えない。**追記主体を防護 subtree へ置いても
  (i) は成立しない**という、設計の中心を否定する所見である。

- **「使い捨ての符号」で代替できないことも確定した。** 人間が短い符号を打つ形は AI に preimage を
  与えてしまい、AI はその後**別の digest の行**を書ける。承認を内容へ束縛するには符号を内容に
  対して計算する必要があり、それは転記そのものである。ここが不可能性の核である。

- **2026-08-24 の人間批准が、一度も使われないまま失効していたことを実測で確定した。**
  詳細は {{F:ratification-expired-before-use}}。行 (`db511c3d…`) は追記時点では正しかったが、
  その branch が main を 2 回取り込んだ結果、**自分の branch 上でも** digest が `1111720d…` へ
  移った。`authority` を持つ v2 lock は当該 branch にも main にも 0 件。
  D758 が言う「私への依存が強まると研究開発が遅滞します」は、頻度ではなく**失効**の形で
  既に実害になっていた。親は 25 blob から digest を再計算して 3 つの ref すべてで照合している。

- **refuted は 0 件だった。** レンズ A が must-fix 9 件 + should-fix 4 件、レンズ B が
  must-fix 9 件 + should-fix 2 件を出し、親が独立に裏取りできたものはすべて real だった。
  2 本は独立に走らせたが、handler の真正性・並行批准・原子性・二重定義の 4 点で結論が一致した。

- **台帳の履歴規則に、行が 2 本になった瞬間に発火する欠陥がある。** 現行の読み手は全史に対して
  「1 commit につき 1 行増、かつ直前 blob の完全な前置き」を要求する。分岐した 2 本の branch が
  それぞれ 1 行を足して合流すると、最終 bytes が正しくてもこの検査が必ず例外になり、
  受理 digest 集合の読み込み自体が落ちる。**今は台帳が空なので発火していないだけ**で、
  1 行目が land した瞬間から生きる。shallow clone では逆に置換履歴を観測できず恒真寄りに倒れる。
  本 wave では直さない — どの択を採るかで読み手の形自体が変わるうえ、closure を動かすと
  既存の批准行がさらに腐るためである。{{T:ratification-history-rule}} として起票した。

- **自動生成 commit の provenance が二択にしかならないことも確定した。** `hooks/` 配下の非 `.md` は
  実装面なので、非 `none` commit は Codex author 行を要求される。機構が作る commit へ
  `AI-Agent: none` を自動付与すると、AI が偽起動した場合にも同じ trailer が付いて偽の
  provenance が全史監査を通る。付けなければ land が止まる。呼出元を認証できない限り
  どちらも選べない。これも (i) が成立しないことの帰結である。

- **本 wave が実装を見送った具体案を明記する。** 表示専用の preflight ツール
  (現行 closure digest と未批准状態を出すだけのもの) を段 2 が推奨したが、受理集合も台帳 bytes も
  1 bit も動かさず、止まっている経路も解けないため不採用にした。レンズ B の
  「preflight-only で閉じるのは実装したふりに当たる」という判定に同意する。

- **子の工数 (receipt 実測、schema v4、3 本とも `accepted=true` / `evidence_status=complete`)。**
  段 2 plan = 847 秒 / 11 model call / 572,275 token。段 3 レンズ A (sol) = 888 秒 / 27 call /
  2,847,198 token。段 3 レンズ B (luna) = 620 秒 / 22 call / 1,850,902 token。
  段 5・6 は「実装しない」裁定により起動していない。

- 親の作法違反・セッション異常は無し。待ち手の偽完了も観測していない。

## 次の一手差分

### 更新

- [T-1629] **P1・ユーザー裁定待ち**: enforcement closure 批准の執行経路。
  {{D:ratification-execution-impossibility}} が (α) 平文承認へ移し主張文を書き換える /
  (β) 転記を残し official 起動の直前 1 回へ寄せる / (γ) AI が成りすませない実行主体を新設する
  の 3 択を返した。親の推奨は (β) を当面の運用とし (γ) を恒久解として起票すること。
  どの択でも {{T:ratification-history-rule}} を同じ変更で閉じる。
  base: 299019e611a02de1883643406816a50ea3a1ca18c2260fb464ccc3fc64c355f0

### 新規

- {{T:ratification-history-rule}} **P1・新規**: 批准台帳の全史検査を、並行批准と shallow clone の
  両方向で閉じる。現行は「1 commit につき 1 行増 + 直前 blob の完全な前置き」を全史へ要求する
  ため、分岐した 2 branch がそれぞれ 1 行を足して合流すると最終 bytes が正しくても受理 digest
  集合の読み込みが例外になり、certified lock が全滅する。shallow clone では置換履歴を観測できず
  逆に恒真寄りへ倒れる。台帳が空の今は発火せず、1 行目が land した瞬間から生きる。
  [T-1629] の択が決まってから、同じ変更で閉じる。
