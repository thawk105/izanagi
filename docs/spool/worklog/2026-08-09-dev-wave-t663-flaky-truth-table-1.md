---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-09
wave: dev-wave-t663-flaky-truth-table
seq: 1
title: [T-663] launcher 負荷フレークの失敗署名が 7 条件に多義だと特定し、次回再発を自己申告させる計装を入れた — 原因は未確定でフレークは直っていない (テストのみ、受入 7505 passed / 20 skipped・赤ゼロ、変異 3/3 KILLED・事前登録一致、branch worktree-dev-wave-t663-flaky-truth-table)
---

## 本文

- 依頼は「非決定性の源を特定し、再現条件を固定するか test を決定的にする」だった。
  調べると **[T-663] は F57 の族の 1 例**で、恒久対応は既に [T-190] へ割り当て済みだった。
  先行観測の [T-427] と同署名である。本 wave は T-190 の計装部分を実施した。
- **特定できたこと。** 失敗署名 `assert 1 == 0` / 出力空は、production の `accepted` を成す
  7 条件のどれが欠けても生じる。区別する receipt は pytest tmp とともに失われるため、
  F57 が 9 回再発しても原因が絞れなかった。**観測不足であって解析不足ではない。**
- **していないこと。** test は決定的になっていない。原因も確定していない。
  F57 と T-190 は閉じない。予算拡大は {{D:flake-instrument-before-widening}} で不採用にした。
  T-190 の残作業 (原因分離と fixture harden) は substance が変わらないので本文更新せず carry する。
  入ったのは計装だけである。
- **段 3 が親 brief を 2 点倒した。** (i)「evidence grace の余裕が薄い」は比較対象の取り違え
  (期限は session/rollout の発見までで、親は完了後の総所要と比べていた)。
  (ii)「予算を縮める probe が機序を確認した」は正の対照にすぎず、実障害の原因が
  予算超過であることは示さない。どちらも裁定文で明示的に撤回した。
- **段 2 のプランは半分を不採用にした。** 予算を一律 2 倍にする案に対し、レンズ A が
  4 拡大それぞれについて「拡大後だけ通る具体的回帰」を構成した。計装が先、値は実 artifact の後。
- **段 6 のレビューは 2 本とも NO-GO** で、must-fix 計 10 件。壊れた receipt を正しい真理値の
  ように表示する、FIFO で診断が止まって一次情報ごと消える、結線検査が実経路を通らず恒真、
  の 3 件はいずれも「原因が分かるようになった」という保証が偽になる型だった。
- **計装自体がフレークで壊れる欠陥を見つけた** ({{F:flake-instrumentation-broke-under-the-flake}})。
  親が予算を縮める probe で決定的に再現し、実 launcher を走らせる meta-test 7 呼び出しを
  「起こりえない期待値」へ統一して解消した。
- **親の手順ミスで fix 1 巡目を消した** ({{F:checkout-restore-wiped-uncommitted-child-work}})。
  未 commit の子成果が乗った tree で probe を `git checkout --` 復元した。段 5 は退避 patch から
  byte 一致で復元し、fix は再実行した。実害は 1 巡ぶんの工数。
- 変異は事前登録 3 本すべて KILLED、観測 node は事前登録と完全一致、baseline 緑。
  M1 / M2 は赤くなった node が新 meta-test だけで、同席した既存テストは全て緑だった =
  変更前の検出面はこの 2 変異を検出しない。`DW-M08` の新旧両走はこの 1 走で満たしている。
- **受入全走は 7505 passed / 20 skipped / 赤ゼロ** (1225 秒、request `896530`、main `ce1de6df` 取り込み後)。
  この走行では F57 は発火せず、計装が実負荷で何を出すかはまだ観測できていない。
  受入 lease は 3 回の待ち直しを要し、15 秒間隔の 240 回では 1 度も取れず、
  3 秒間隔の 357 回目でようやく `acquired` になった。並行 wave の受入枠が飽和している。
- エージェント工数: Codex 6 session (plan 1 / 段 3 相談 2 / 実装 1 / 段 6 レビュー 2 = 6、
  および fix 2 = 計 8)。親 = brief・実測 probe 4 本・裁定・統合 commit・変異・受入・記録。
- 一次資料と逐語 = `output/insights/2026-08-09_t663-launcher-flake-diagnostic/`。

## 次の一手差分

### 更新

- [T-663] **P3・計装済み・実 artifact 待ち**: 受入全走限定フレークの失敗署名が受理 conjunct
  7 条件に多義であることを特定し、次回再発でどれが落ちたかを自己申告させる計装を入れた。
  原因は未確定で、test は決定的になっていない。残りは実負荷で artifact を 1 件得ること。
  base: d436df53b7efc4319ae738ec054176165041b0c1518affd0cedd13241778c6d3

### 新規

- {{T:launcher-fixture-budget-ruling}} **P2・新規・ユーザー裁定待ち**: launcher テストの
  時間予算 (wall 3 秒 / evidence 1.0 秒 / termination 0.05 秒 / 外側 timeout 10 秒) を
  広げるか。実負荷の artifact を 1 件得てから、値と据え置き sentinel を根拠付きで決める。
  本 wave は根拠不足を理由に据え置いた
- {{T:dispatch-relay-diagnostic-reach}} **P2・新規**: 失敗診断が dispatch の末尾 64 KiB 中継を
  越えて人間へ届くことを機械検査する。現状は例外 message 内で末尾へ要約を再掲するだけで、
  後続出力が 64 KiB を超える全走では診断全体が中継から消えうる
- {{T:publication-wall-gate-gap}} **P2・新規**: launcher は最終 publication 後に wall gate を
  再評価しない。receipt の staging / publication が 10〜20 秒級で停滞しても accepted で通る
- {{T:launcher-early-receipt}} **P3・新規**: preflight 失敗と publication 失敗では receipt が
  存在せず、受理 conjunct の診断が得られない。早期 receipt を置くか裁定する
- {{T:flake-absence-evidence}} **P3・新規**: 「負荷フレークが消えた」ことの証明方法を決める。
  有限回の緑では不在を示せないため、記録の正直な表現も併せて裁定する
- {{T:probe-clean-tree-gate}} **P3・新規**: 親が実編集 probe を行う前に作業ツリーが clean で
  あることを機械確認する。未 commit の子成果がある状態での復元は復旧不能な破壊になる
