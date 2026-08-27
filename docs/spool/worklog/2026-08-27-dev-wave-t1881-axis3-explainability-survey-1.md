---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-27
wave: dev-wave-t1881-axis3-explainability-survey
seq: 1
title: [T-1881] 軸 3 (説明可能性) の母集合を事前登録し、自分の pilot が登録枝と同一 query だったことを敵対レビューが暴いた (docs のみ、branch worktree-dev-wave-t1881-axis3-explainability-survey、実装面の差分ゼロのため変異 matrix は DW-S04 で免除)
---

## 本文

- **依頼どおり母集合登録まで進め、実行はしていない。** 成果物は凍結物 2 本
  (`claim-survey/2026-08-27-axis3-search-preregistration.md` と
  同 `-axis3-index-measurements.md`) と claim-survey 一覧の 2 行。
- **軸 3 は登録後も `RW0` である。** ユーザーの依頼文は「母集合登録が終わっただけなら
  `RW1` と書いて」と述べたが、7.7.3 の `RW1` は候補文献または横断掃引の成果を条件とし、
  登録は候補を 1 件も生まない。**凍結済みの 2026-08-26 棚卸しが、同じ 26 エントリ走査を
  実行したうえで「軸 3 を目的とした検索を一度も行っていない。`RW0` から動かすには
  7.7.4 の母集合登録から始める必要がある」と書いている。**
  依頼より一段低い側であり、過大主張を避ける向きなので `RW0` を採った。
  段 6 のレビュー 1 本は逆に「26 エントリ走査が探索資産だから既に `RW1`」と主張したが、
  棚卸しの表が `RW1`/`RW0` を「軸を目的とした一次資料の深掘り」の有無で分けており、
  走査を資産に数えると軸 4 も `RW1` になって表が壊れるため refuted とした。
  **実務上の差は小さい** — 7.7.3 はどちらの段階でも新しい不在方向の表現を禁じ、
  差は既存文の逐語引用の可否だけである。
- **親自身の事前登録が汚染されていた。** 索引の取得量を測る pilot 16 組のうち
  **8 組が、同じ文書が登録する DBLP の枝 query と query-equivalent**であった。
  親は当初 1 件も開示せず、うち 1 組の 0 件を本文の実測として書いていた。
  `RW0` の軸が書けない外部索引の未検出を先取りしていたことになる。
  段 6 の敵対レビューが 1 件を指摘し、親が全 ID を突き合わせて 8 件と確定した。
  {{F:preregistration-pilot-leak}} と {{D:pilot-equivalent-query-disclosure}} に収容した。
- **索引の実測が設計を 2 度変えた。** (a) DBLP は `performance` 1 語で 188384 件 =
  1884 request を要し、起草案の「48 語を全件取得して client 側で集合演算」は
  10 語だけで 2613 request になって実行不能と判明した。連言は測った 16 組すべてが
  224 件以下だったので、**server 側の連言 1523 本**へ設計を変えた。
  (b) OpenAlex は echo を正規化して返す (語は辞書順、節順は query 依存、再送には決定的) ため、
  期待 echo を literal で登録すると正しい走行が無効になる。**typed AST 照合**へ変えた。
  後者は {{D:echo-ast-not-literal}} に収容した。
- **軸 1 の凍結物にも同じ潜在欠陥がある。** 軸 1 の事前登録は OpenAlex の期待 echo を
  literal 相当で登録している。**7.7.8 に従い凍結物は上書きせず、本項に記録だけ残す。**
  是正するなら新しい日付の supersede 版が要る。
- **`RW3` に到達する前に閉じるべき項目を blocking 5 件・non-blocking 4 件として登録した。**
  blocking のうち 1 件 (API 版番号の代用可否) は**人間裁定を要する** — 7.7.4 は索引の
  API/export の版を固定するよう求めるが 3 索引とも版番号を返さず、代用を許す裁定が無い。
  本 wave は代用を既成事実にしなかった。
- **OpenAlex は wave 途中から測れなくなった。** 本 wave の送信は約 13 request だが
  HTTP 429 が返り、`Retry-After` は 79725 秒 (約 22.1 時間) を示した。軸 1 の記録する
  「1 窓 100 request」に達していない。**無償枠が IP 単位で複数 wave に共有されている
  という解釈は推論であって直接観測ではない**ため、凍結物では推論として書き、
  共有単位の確定を実行段の preflight へ送った。
- **段 6 の敵対レビューが親の修正の中に regression を 2 度見つけた。** (a) 完走述語の
  条件 3 で「各ページで要求件数＝実要素数」と「最終ページは残件数でよい」を同時に要求し、
  総件数が page size の倍数でない正常走行が永久に未完走になる矛盾。(b) main-field control の
  語を実行段で選ぶ設計にしたことで事後裁量が入り、anchor が全滅すると control 0 本で
  論理積を通過できる穴 (7.7.6 の positive control 要求を弱める)。
  後者は**追加の検索式を作らず登録済み主 query の和集合に anchor が含まれることを検査する**
  形へ作り直した。
- **D1015 (一般手続きの正本を増やさない) への適合は未達のまま残した。** 主キー正規化・
  完走述語・amendment 規則は軸固有値ではなく一般手続きであり、レビューは 7.7 本体への
  集約を求めた。**規則の正本の改訂であり、かつ軸 1 の凍結物が同じ一般節を持つため
  軸 3 だけを動かすと非対称になる。単独 wave で既成事実にせず裁定パッケージへ送る。**
- 工数: codex 子 8 本 (plan 1、consult 2、review 2、focus 3)。
  全数 `gpt-5.6-sol` / `xhigh` / accepted、model call 計 85、output token 計 208547。
  段 6 は fix 3 巡 (`DW-O16` の上限) を使い、must-fix は延べ 33 件。
  **子はいずれも索引へ HTTP を送っていない** (規律どおり Web 検索を禁じ、実測は親が行った)。

## 次の一手差分

### 更新

- [T-1881] **P2・更新**: 軸 3 の母集合登録は完了した (凍結物 2 本を land)。
  残るのは登録した 1543 query ID の実行であり、その前に §13.1 の blocking 5 件を閉じる。
  うち API 版番号の代用可否は**ユーザー裁定待ち**。
  base: 4abdddc00082a15bdcfe95f9c865bd95ee2022b60c385693e46a929768c1537d

### 新規

- {{T:axis3-search-execution}} **P2・新規**: 軸 3 の登録した検索を実行する。
  `claim-survey/2026-08-27-axis3-search-preregistration.md` の §13.1 blocking 5 件を
  preflight で閉じてから、1543 query ID + control + 補助経路を完走させる。
  OpenAlex のレート制限 (実測で `Retry-After` 約 22 時間) が律速。
- {{T:axis3-api-version-ruling}} **P3・ユーザー裁定待ち**: 文献索引の API 版番号の代用可否。
  7.7.4 は索引の API / export の版を固定するよう求めるが、arXiv・OpenAlex・DBLP の
  3 索引とも版番号を返さない。「endpoint + 応答 field 名 + response header + raw digest を
  effective version とする」ことを許すかどうか。**許さないなら軸 1・軸 3 とも `RW3` 不可**。
- {{T:generic-search-procedure-hoist}} **P3・新規**: 主キー正規化・完走述語・amendment 規則を
  軸別の凍結物から `docs/related-work/README.md` 7.7 本体へ集約するかを裁定する。
  D1015 は手続きの正本を増やさないよう定めるが、軸 1・軸 3 の事前登録が同じ一般節を持つ。
  **軸 1 の凍結物に触れる必要があるため 7.7.8 の扱いと併せて決める。**
- {{T:axis1-echo-literal-supersede}} **P3・新規**: 軸 1 の事前登録が OpenAlex の期待 echo を
  literal 相当で登録している点を supersede する要否を判定する。
  {{D:echo-ast-not-literal}} と同じ欠陥であり、放置すると軸 1 の OpenAlex 枝が
  完走できない。**凍結物は上書きせず新しい日付版で扱う。**
