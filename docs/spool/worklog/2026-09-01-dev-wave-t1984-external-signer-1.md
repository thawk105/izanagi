---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-01
wave: dev-wave-t1984-external-signer
seq: 1
title: [T-1984] D906 の外部署名主体は部品を実装し、必須化は鍵儀式の後へ送る (コード + テスト + docs、branch worktree-dev-wave-t1984-external-signer、変異 7/7 KILLED)
---

## 本文

D906 の外部署名主体について、署名検証 library と repository 内の reference issuer を実装した。
**production の着地関門は 1 bit も変えていない。** 詳細な設計判断は
{{D:external-signer-parts-without-enforcement}}、閉じない範囲は
{{D:external-signer-unclosed-scope}}、positive control の充足境界は
{{D:external-signer-d431-partial}} を正本とする。

- **必須化しなかった理由は 4 つあり、いずれも実測または既裁定に基づく。** (1) 鍵を AI が生成すると
  D906 の要求そのものを満たさない、(2) 書込み防護機構は自分の subtree への書き込みを自ら拒否するため
  AI には防護対象を足せない、(3) 必須化は鍵が配置されるまで稼働中の全 wave の着地を止める、
  (4) 必須化しても旧い着地ツールを wave 側から起動する迂回が残るため「閉じた」と書けない。
- **親の独立実測 (段 3 の 2 レンズが出さなかったもの):** 排他権の payload は field 集合を厳密一致で
  検査し、解釈できない payload を「誰も保持していない」へ縮退させる。したがって D906 が要求する
  「排他権の世代」を payload へ足すと、旧い実装で稼働中の wave が保持中の排他権を空きと読み、
  受入の排他が壊れる。共有の排他権 directory を 6 本以上の wave が使っている。
  **世代は schema の slot に留め、production の値の生成源は決めていない。**
- **親 brief の前提 2 件を撤回した。** (P4) 「issuer へ起動権を移せば本 wave tip の署名実装が走る」は
  因果が誤りで、実際は repository 外の issuer が旧 launcher の出力を後段で署名するから成立する。
  (P5)「影響範囲は受領証 schema 版上げの既存前例と同程度」は誤りで、過去の受領証だけでなく
  legacy な排他権・非保持走行・旧い待ち手で稼働中の wave・鍵未配置期間まで止まる。
- **変異走行が実在の穴を 1 件検出した。** wave 名の束縛比較を外しても 1 件も赤にならなかった
  (SURVIVED)。既存の再送負例は別の排他権世代・別の検査 tip を使っており、wave 名の比較そのものを
  通っていなかった。**この穴は段 3 の敵対相談 2 レンズと段 6 の敵対レビュー 2 レンズをすべて
  通り抜けており、変異走行だけが検出した。** 負例を足して再走し 7/7 KILLED。
  初回の SURVIVED は変異台帳へ erratum として残す。
- **段 6 レビューが恒真化を 1 件検出した。** 固定鍵 loader と高水準検証 API を一度も通らない
  control 群で、loader が環境由来の鍵を採用しても高水準 API が署名検証を迂回しても緑のままだった。
  fix が固定 path の loader と高水準 API を実際に通る正例と 4 負例を追加して閉じた。
- **D431 は部分充足である。** 実在 production 受領証を canonical projection 述語へ通す control は
  充足。固定設定鍵の検証器へ production 発行の署名付き受領証を通す control は **unmet** —
  operational issuer と鍵が人手で配置されるまで発行できない。
  test 鍵の正例を production control と呼んでいない。
- **段 4 で登録した変異 2 件が対象を失っていた。** 書込み防護機構への変異として登録したが、
  同機構は AI が編集できないと段 5 直前に判明したため、実装単位ごと scope 外になった。
  段 6 レビューの再照準に従い署名境界の変異へ差し替えた。
- 実装面は Codex `role=author` が書いた (D95)。親は brief、裁定、統合、変異 probe、全走、記録のみ。
- 三軸語の機械走査は権威 CLI で rc=0、conjunction hit 0 件。

## 次の一手差分

### 更新

- [T-1984] **P1・部品実装済み → 人手の鍵儀式待ち**: D906 の外部署名主体は署名検証 library と
  reference issuer を実装した。**production の必須化は未実施で、着地受領証を根拠にした
  正しさ主張は D1197 に従い未閉鎖である。** 次の関門は人手の鍵儀式
  ({{T:external-signer-key-ceremony}})。その後に activation
  ({{T:external-signer-activation}})。
  base: 6412cfa614a9460be941f1eab1a282e28302ce44c96b727a51be3ed95eca9417

### 新規

- {{T:external-signer-key-ceremony}} **P1・ユーザー手番**: 外部署名主体の鍵儀式。
  repository 外の固定 subtree へ Ed25519 鍵対と operational issuer を人が配置し、
  同 subtree を書込み防護機構の防護対象へ人が追加する。**AI が代行すると D906 の
  「鍵と発行権限を AI が書ける領域の外に置く」を満たさなくなる** — 生成時点で AI が秘密を
  支配した事実は後から書込みを拒否しても消えない。防護対象の追加も、防護機構が自分の subtree への
  書き込みを自ら拒否するため AI には実行できない。配置後に production 発行の署名付き受領証を
  1 件取得すると、{{D:external-signer-d431-partial}} が unmet としている positive control が閉じる。
- {{T:external-signer-activation}} **P1・鍵儀式の後**: 署名必須化の activation。
  待ち手と着地ツールを同時に新 schema 専用へ切り替える。着手前に
  (a) 無署名受領証を正例として固定している既存テストの所有競合が解けていること、
  (b) 稼働 wave 数が少ない窓であること、を確認する。切り替えは稼働中の全 wave の着地を
  一時的に止めるため、影響範囲を worklog へ先に書いてから行う。
- {{T:acceptance-lease-generation-semantics}} **P1・ユーザー裁定待ち**: 排他権の世代の意味論。
  D906 は署名対象に「排他権の世代」を求めるが、現行の排他権 payload は field 集合を厳密一致で
  検査し、解釈できない payload を「誰も保持していない」へ縮退させるため、payload への追加は
  稼働中 wave の排他を壊す。さらに世代を必須化すると、排他権を保持しない走行の受領証発行が
  止まり D662 (待ち行列を廃止し `held` でも待たず投入する) と衝突する。
  **「D662 を改訂して非保持走行を着地不可とする」か「D906 を満たす別の世代意味論を採る」かの
  裁定が要る。** 本 wave では世代を schema の slot に留めた。
- {{T:acceptance-receipt-single-use}} **P2・ユーザー裁定待ち**: 再送防止の射程。
  署名済み context の束縛は別 wave・別 main・別 tip・別の排他権取得への再利用を拒否するが、
  **同一 context 内での 1 回限りの使用は保証しない。** D906 の「再送防止」が排他権取得間までか
  exact single-use までかが資料から確定しない。後者なら外部の消費台帳が要る。
- {{T:land-consumer-version-binding}} **P2・裁定待ち**: 着地ツールの版束縛。
  着地ツールは自身の実行 copy を `__file__` から解決し、cwd が wave の作業木であることしか
  検査しない。**署名検証を含まない旧い着地ツールを wave 側から起動すれば新しい検証を通らない。**
  署名を必須化してもこの迂回は閉じないため、「関門が不可避である」とは書けない。
  main 起点で consumer bytes を固定する設計は scope 拡張になるため、着手前に裁定を要する。
