---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-08
wave: dev-wave-t181-stage6-high
seq: 3
title: [T-227] 段 6 review 子の reasoning を high に確定し機械 pin を張った — 契約 drift の pin が 3 巡続けて恒真だった (コード + docs、受入 7376 passed / 20 skipped、変異 15/15 期待一致 (実効 kill 12 / 診断 pin 2 / SURVIVED 1)、branch worktree-dev-wave-t181-stage6-high)
---

## 本文

- **ユーザー裁定 (2026-08-08)。** 段 6 の reasoning を `high` にする。既存裁定
  (`DW-S06-A` / `DW-S06-C` は `max`、引き下げは A/B の 10 run 再走後) を明示 supersede する。
  既存欠陥 2 件 (節ごと不可視化、曖昧値) も本 wave で直す。詳細は
  {{D:stage6-reasoning-high}}、逐語と台帳は
  `output/insights/2026-08-08_t181-stage6-high/`。
- **親 brief の前提が段 3 で覆り、ユーザー再裁定へ戻した。** brief は「段 6 は D207 の pin 対象外
  だから初回確定であり引き下げではない」と置いたが、段 3 レンズ B が archive worklog にしかない
  既存ユーザー裁定を発見。親が一次資料で裏を取り real と裁定し、`DW-S04` に従って採否を決めず
  選択肢 α (max のまま実装) / β (high) / γ (再走してから決める) を付けて返した。ユーザーは β。
  取りこぼしの経緯は F154 の再発項 に記録した。
- **段 2 プランは不採用。** 機械面 (byte 会計 +2、pin 挙動) は親の独立再測と完全一致したが、
  (a) 条件節「実装 wave は」の脱落が docs-only wave への受理集合拡大になる、
  (b) 削除対象「全体へ 1 本でよい」の「1 本」を巡回数上限と取り違えていた
  (導入 commit `7deb54ef` の逐語「fix 単位ごとの個別レビューは不要とする」が原義) の 2 件を
  親が段 4 で real と裁定した。両方を保存する文面へ差し替え、byte は `operations.md` 導入 2 文の
  縮約で捻出した。**予算値は 1 byte も上げていない** (aggregate 25,185 → 25,169 / 25,200)。
- **段 6 レビュー 2 本と焦点再レビュー 2 巡はすべて `reasoning=high` で起動した** — 本 wave が
  land する新契約の最初の適用例 (dogfood)。焦点再レビュー 2 巡目で `regressed=0` を確認。
- **段 6 fix 3 巡目は親の期待値誤りで 1 度空振りした。** 親が prompt へ書いた「CR-only 文書も通る」は
  再レビュー probe の読み違いで、実装子が実測 (CR 全文で 12 findings) で食い違いを見つけ、
  **テストを甘くせず実装せずに停止して報告した**。`DW-S06-B` の「期待値が誤りと判断したら
  実装を変えず報告して止める」が正しく発火した例。親が期待値を訂正して投げ直した。
  新規所見への対応ではないため `DW-O16` の巡回数には数えない。
- **工程差異 (`DW-O12`)。** 段 4 は「停止条件に local main の SHA 比較を足す」と設計したが
  **機械 gate としては実装せず**、親が投入前後に手で確認する運用で代替した。結果として stale は
  踏まなかったが設計どおりではない。{{T:main-sha-stop-gate}} へ起票した。
- **変異は総数を水増ししない形で記録した。** 事前登録 v1 の 3 件 (M4 / M5 / M6) は段 6 レビューが
  実装後のコードを読んで kill 意味論の不成立を指摘したため v2 へ再照准し、v1 は erratum として
  insight に残した。本走は受領 node ごとに走行範囲を絞る 10 group 構成で単一理由の receipt を取り、
  15/15 が期待一致。内訳は受理集合を変える kill 12、diagnostic sensitivity pin 2 (M4 / M5)、
  SURVIVED 1 (M6、mask を事前登録済み)。M4 / M5 が受理集合を変えないことは親が production 経路で
  実測した (fence 隠蔽ケースの S06 finding が 2 → 1 に減るだけで、0 になるのは両層同時の M7 のみ)。

## 次の一手差分

### 完了

- [T-227] `DW-S06-A` / `DW-S06-C` の reasoning を `high` として明記し、節ごとに機械 pin した。
  値の確定という本項の要求は充足した。実起動値の機械保証は本項の射程外で
  {{T:stage6-launcher-binding}} へ分離した。
  remaining: none
  base: 2b4f7d61a4a4c4a9cd67023a1ddf8e2281d3af47aba05e7adb645edcaa27e6d7

### 更新

- [T-181] **P1・裁定済み → 認証再走待ち (射程を限定)**: 最終版装置での 10 run 再走で
  認証済み台帳を得る。段 6 の effort 採用は 2026-08-08 のユーザー裁定が既存裁定を
  supersede して先行したため、**本項はもはや段 6 採用の前提条件ではない**。
  ただし A/B 装置そのものの認証と、他段への一般化の根拠としては引き続き必要である。
  base: a8a56395b7da64bff7ac12bec04b6867687ec05a1a773196df84411417ac9b98

- [T-184] **P1・裁定済み → 段 6 を除いて再走待ち**: 工程別 policy の採用は認証再走の後、を維持する。
  ただし**段 6 (`DW-S06-A` / `DW-S06-C`) だけは 2026-08-08 のユーザー裁定で先に確定した**ため
  本項の対象から外れる。残る対象は段 2 / 段 3 / 段 5 と model・resource・retry の matrix。
  base: 1f15acff27287b96b039c6c4b479909b85a4599975c53f807aafef9ed33f0a44

### 新規

- {{T:stage6-launcher-binding}} **P2・新規**: 段 6 の子が実際に指定 effort で起動することの
  機械保証を入れる。現状 docs pin が拘束するのは docs の記述だけで、親が組み立てる起動 command は
  拘束しない。launcher 結線と receipt 検査の設計を裁定へ返す
- {{T:wording-pin-freeze}} **P3・新規・裁定待ち**: 規範文 pin は文面を凍結する。意味を変えない
  語順・助詞・空白の修正でも docs 単独ではできず、docs + checker + test + 採用裁定を要求する。
  drift を強く止める意図した強度だが、正当な文面改善まで実装面変更へ昇格させる代償を受容するか
- {{T:stage5-effort-pin-residual}} **P3・新規**: `DW-S05-A` の `high` と `DW-S06-B` の
  literal 不在は pin 対象外のまま。将来の drift を台帳が見逃す。pin 対象を広げるかを裁定へ返す
- {{T:cr-only-section-extraction}} **P3・新規**: CR-only 改行の文書を
  `_reference_id_sections()` と必須 H2 inventory が扱えず、正当な内容でも複数 finding になる。
  対応するか、非対応を明示するかを決める
- {{T:main-sha-stop-gate}} **P3・新規**: dev-wave の子投入 preflight に local main の SHA 比較を
  足す。現状は親の手検査で代替しており、並行 wave が先に land しても投入側は気づけない
