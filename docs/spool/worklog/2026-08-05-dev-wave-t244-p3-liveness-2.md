---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-05
wave: dev-wave-t244-p3-liveness
seq: 2
title: [T-244] P3 の生死実験を fixture ledger 上で成立させた — 実 driver 出力を載せた同一候補 R=2 が受理・counter 更新・seal 復元まで通り、本番 provisioning は開けないと確定した (コード + docs、受入 6454 passed / 20 skipped、変異 3/3 KILLED、branch worktree-dev-wave-t244-p3-liveness)
---

## 本文

- **本 wave の射程。** D179 §8 と U-9 (a) の裁定どおり生死実験だけを行い、本体 (reservation FSM /
  report v3 / origin-proofs sidecar / completeness / field 分離 / critic 後置 / ever-issued cell 台帳) は
  一切実装していない。結論と名乗りの上限は {{D:t244-p3-liveness-fixture-only}}、
  変異での裏取り方法は {{D:disposable-probe-mutation-wrapper}}。
- **段 1 前の前提実測で裁定の前提が 2 つ動いた。** (i) 本番 authority は `origins: []` のままで、
  entry 追加には未確定の予算値が要る。ただし ledger は予算値の意味も evidence の実在も検査しないため、
  **適当な値でも機械的には通ってしまう** — 止めているのは機械ではなく規律だけである。
  (ii) E 段 CLI は `--preview-wire` だけが login ノードで走り、実 iteration 経路は
  `site=PEGASUS_LOGIN` で拒否される。§8 が想定した「E には実走可能な既存 CLI がある」の限定。
- **段 5 は 1 巡空振りした。** 親 brief の誤前提を実装子が fail-closed で差し戻した
  ({{F:brief-missed-closed-vocabulary}})。親が brief を訂正して再投入した。
- **段 6 の fix は 4 巡した。** 敵対レビュー 2 本が独立に同じ穴 (preview artifact が実 driver 実行へ
  束縛されていない) を指摘し must-fix 8 件を採用。1 巡目が probe を 486 コード行へ膨張させたため
  差し戻し ({{F:fix-inflated-disposable-probe}})、2 巡目で 180 行へ縮小、その際に receipt から
  実体 field が落ちる回帰を親が検出して 3 巡目で復元、焦点再レビューが残した 2 件を 4 巡目で閉じた。
  `DW-O16` の 3 巡上限を 1 巡超えたので本巡で打ち切り、残余は変異で裏取りして裁定した。
- **scope 外として不採用にした real 所見 2 件。** (i) probe の wire 正準性検査が ledger と同じ
  canonicalizer を再呼出しする (独立な IR canonicalizer を書くのは使い捨て確認に不相応)。
  (ii) fixture manifest が本番では成立しない値を持つ (docstring と receipt で明示済み)。
  いずれも {{D:t244-p3-liveness-fixture-only}} の「残る限定」に記録した。
- **実測の順序 (`DW-O12`)。** 変異 matrix は wave の統合 commit (`641547f4`) で走らせ、
  その後 local main 10 commit (docs のみ、実装面と非交差) を取り込んでから受入全走を回した。
  変異の runner を pytest ラッパにする決定は段 4 ではなく段 6 preflight で下した。
- **成果物の所在。** probe・receipt・brief・段 4 裁定・敵対レビュー 2 本の逐語・段 6 裁定は
  `output/insights/2026-08-05_t244-p3-liveness/`。変異 spec と ledger、子の逐語は repo 外の
  wave job dir。

## 次の一手差分

### 更新

- [T-244] **P3 は生死確認済み → D96 分割 wave 起票可。ただし本番 provisioning は U-10 未決で開かない。P2 は U-1〜U-3 の D96 wave 起票可。P4 は ledger 側適合、P5 残余は U-2、未着手は P7・P9**:
  **P3**: D179 §8 の生死実験を完了した。実 E driver が出した wire と diff digest を載せた
  同一候補 R=2 の 1 batch が 3 event として受理され、query counter 0→2 / iteration counter 0→1、
  seal 後に wire と evidence digest を replicate 0/1 で復元。負の control も理由固定で拒否を確認。
  **名乗りの上限と残る限定は {{D:t244-p3-liveness-fixture-only}}** — fixture store 上の生死のみで、
  P3 充足・provisioning 解禁・候補 batch・実行 outcome は名乗らない。本番 authority は `origins: []`
  のまま変更していない。**次は reservation FSM (U-5) / report v3 / origin-proofs sidecar (U-4 の
  field 分離を含む) / completeness / critic 後置 (U-8) / ever-issued cell 台帳 (U-3) を D96 の
  同一変更単位で分割 wave として起票する。1 wave にまとめない。** U-7 は確定済み
  (cygnus 再測定はせず Pegasus で新規測定)。**U-10 (予算値 Imax/Qmax/Kmax/Bmin/floor tuple) は
  依然 authority 発行の裁定待ちで、これが決まるまで本番 authority へ entry を 1 件も書かない。**
  **P2**: U-1〜U-5 裁定済みで U-1〜U-3 の D96 wave 起票可 (正本 =
  `output/insights/2026-08-05_t244-p2-noninterference/s4-adjudication.md`)。
  **P1**: 変わらず機械部品のみで未充足。**P4**: ledger 側実装済み (D166)、充足は名乗らない。
  **P5**: 残余は U-2 のみ。**未着手**: P7・P9。P3 は依然 FAIL、cap-lift FAIL、D114 上限 1 不変
  base: f4fe9372f762cadbb81f461b19c2e0ecc0fe5424def34867a44ef126439a97ad
