---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-25
wave: dev-wave-t1633-stage0-blocker-scope
seq: 1
title: [T-1633] 段 1 以降 owner の fixture assignment を段 0 blocker から外し、繰越義務として残した (コード + docs、branch dev-wave-t1633-stage0-blocker-scope、変異 matrix = baseline PASSED・9/9 KILLED・SURVIVED 0・MISMATCH 0)
---

## 本文

- D778 (ユーザー裁定) の 2 点のうち AI が実行できる配線を閉じた。開始順は D778 が解決済みで、
  本 wave はその配線と、残る blocker の owner つき一覧化を行った。activation record の発行、
  reviewed head 更新、上位 A/X、freeze seal、holdout 解禁、rr80/rr20 登録には触れていない。
  D437 / D444 の lockstep と人間 seal も不変である。
- 除外の根拠設計は {{D:stage0-deferral-three-way-match}}、免除でなく繰越とする設計は
  {{D:stage0-deferral-is-carry-not-waiver}} に置いた。
- **親の brief が 2 箇所で誤っていた。** (i)「fixture case へ owner を足す案では独立 pin 3 系統が
  動く」は誤りで、row-ID pin は row coverage を変えない限り不変である。段 2 の plan がコードで
  訂正した。(ii)「blocking gate が 4 件から 3 件になる」は不正確で、raw blocking gate は 4 件の
  ままであり 3 件になるのは段 0 effective である。段 3 の敵対レビューが指摘し、語彙を
  raw / excluded / effective の 6 値へ固定して全成果物で揃えた。
- **command 引数の「blocking gate 4 件」は変更前の実測値だった。** 変更後の段 0 blocker は
  裁定 profile の applicable unresolved 2 件と blocking gate 3 件である。
- 段 3 の敵対レビューが blocker を 2 件出した。(i) 除外すると将来、実行可能な陽性・陰性 fixture を
  1 件も持たない不変条件 5 行を残したまま段 0 を `complete` にできる。(ii) manifest の自己申告に
  よる applicability 回避になっている。どちらも real と裁定したが、提案された対策
  (5 行の fixture をいま固定する / 設計正本側に row→段→owner 表を作って導出する) は
  いずれも D763 が記録した循環を作り直すため採らず、繰越述語と三者一致へ置き換えた。
- **段 0 完了判定の production caller は 0 件である。** 呼び手は同 module のテストだけで、
  本 wave は campaign 成果物の値・certified 選択・材料レポートを一切変えていない。
  親の brief は当初これを過大に書いており、段 3 の敵対レビューの指摘で訂正した。
- 段 6 の敵対レビュー 2 本のうち 1 本は所見ゼロ、もう 1 本が must-fix 1 件と major 3 件を出した。
  親は 3 件を real & 要修正として fix 子へ投げ、焦点再レビューで全件 closed を確認した。
  設計正本の冒頭にある「ユーザー裁定待ち 1 件 (R4)」と §10.1 の U-A1 記述の不整合は、
  base と照合して**本 wave 以前から在る既存の不整合**と実測したため scope 外に置いた。
- 段 6 の敵対レビュー起動が 1 度 argv エラーで止まった。`--lane` は `--stage consult` でだけ
  指定でき、`--stage review` では rc=2 になる。子は起動していない。新しい done path で再投入した。
- 変異は事前登録 9 件 (負例 8 + 正例 1)。期待 node を事前に確定できなかったため `DW-M07` の
  手順どおり probe 走 (全件 SURVIVED 期待) で観測 node を集めてから本走を再登録した。
  逐語台帳は `output/insights/2026-08-25_t1633-stage0-blocker-scope-mutation.md`。
- 工数: codex 子 8 本 (plan 1、consult 2、author 1、review 2、fix 1、focus 1)。
  うち 1 本は argv エラーで起動せず作り直した。
- 段 8 の自己改善は候補 2 件を検討し、いずれも採用しなかった。(i) `--lane` の段別制約は
  `docs/dev-wave/core.md` の `DW-C01` に既に逐語で書かれており、文書の欠落ではなく親が
  適用しなかっただけである。(ii) `DW-O17` の「`--dry-run -F` 単独 rc=0」という句は
  `git commit --dry-run -F` とも provenance checker の `--message-file` とも読めるが、
  実測では誤読による失敗は起きておらず、入口・reference とも byte 予算が満杯であるため
  今回は本文を変更しない。

## 次の一手差分

### 完了

- [T-1633] D778 の配線を実装し、段 0 blocker の内訳と繰越義務を owner つきで readiness index へ
  残した。残る段 0 blocker は applicable unresolved 2 件と blocking gate 3 件である。
  remaining: none
  base: 2b1b232b3581bc9b3fd17662c3020edce05ce44a212ec5d8187fbba86016aee4

### 新規

- {{T:stage0-fixture-target-stage-assignment}} **P1・新規・ユーザー裁定待ち**: 繰越 fixture 5 件へ
  target stage と completion owner を割り付け、対象段の完了判定が「自段所有の pending が 0」を
  要求する配線を作るか決める。現在 owner は manifest literal の `stage1-and-later` だけで、
  個別 owner は未割当である。
- {{T:stage0-obligation-predicate-caller}} **P1・新規・ユーザー裁定待ち**: 繰越義務述語を呼ぶ
  production caller (段 6 X 候補入口) を実装するか決める。現在 caller は 0 件で、設計正本は
  「将来の段 6 実装が呼ばなければならない」と記すだけである。
- {{T:cfab-design-intro-stale-rulings}} **P2・新規**: 上位権限束設計の冒頭が「ユーザー裁定待ち
  1 件 (R4)」と書き、§10.1 が U-A1 を未裁定として記述する一方、§12.1 / §12.3 と module pin は
  双方 `resolved` である。本 wave 以前から在る既存の不整合として実測した。
