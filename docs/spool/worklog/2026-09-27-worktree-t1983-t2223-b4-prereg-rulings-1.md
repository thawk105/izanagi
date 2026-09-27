---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-27
wave: worktree-t1983-t2223-b4-prereg-rulings
seq: 1
title: [T-1983] [T-2223] B-4 事前登録の既裁定 2 件 — 開始時刻の拘束撤廃 (D1649) は 09-08・09-16 の追記で反映済みと確認し、上限統計の登録簿を 2 件のまま凍結 (D1535) を §11.2 へ追記した (docs のみ、branch worktree-t1983-t2223-b4-prereg-rulings)
---

## 本文

- 依頼の (1) D1649 は、事前登録 §5.1「開始時刻」項の 2026-09-08 [T-2140] 追記と 2026-09-16 [T-2464] 追補で既に反映済みだった。受理側も `開始時刻 = 未記入` を受理しており、文書の bytes は変えていない。根拠は `output/insights/2026-09-27/t1983-t2223-b4-prereg-rulings/README.md` §2。
- (2) D1535 の記入先は §11.2「保守側の合成」とした (「各セルの上限統計を凍結で先に閉じる」と書く唯一の箇所)。凍結 spec 3 本 (D2138) は D1535 の 2 件を既に束縛しており、spec・driver・§5 表は変えていない。
- 段 2・3 は軽量版で省いた。段 6 の read-only レビュー 1 本は NO-GO (must-fix 1・should-fix 1、どちらも real) を返し、fix 後の焦点再レビューは GO だった。
- login node での関連テストの焦点走は hook が pytest を拒否したので行わず、受入全走に任せた。
- DW-S07 の三軸語走査は rc=1 だったが、hit は既存 3 file (`output/env/pegasus/calibration/s8b-floor-official/20260916T111925Z-2c8cf9be/` の journal / manifest / result、D2120 項 2 (d) の既知の帰結) だけで、本 wave の新規・変更 file の hit は 0 件。
- carry の閉じ損ね ([T-1983]) は新しい F を起こさず、F428 の再発として記録した。

## 次の一手差分

### 完了

- [T-1983] (ii) D1649 決定 2 の本文反映は、[T-2140] (2026-09-08) の追記と [T-2464] (2026-09-16) の追補で済んでいたことを確認した。(i) と (iii) は D1649 で維持と裁定済みで、作業は残っていない。
  remaining: none
  base: 8d407bb1010d246d468fddaab6994e98c8c18a2f1e702ec1ea19a3c01190d66d
- [T-2223] 上限統計の登録簿を現行の 2 件 (`sample_max/v1`・`max_over_closed_strata/v1`) のまま凍結する旨 (D1535) を、事前登録 §11.2「保守側の合成」へ追記した。凍結 spec 3 本 (D2138) が同じ 2 件を束縛していることも併記した。
  remaining: none
  base: 16cc3a77af7ff331dcd1111e96b08838afc51e76f3f3ea987a020355e4621ccd
