---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-08-06
wave: dev-wave-t419-u2-recalibration
seq: 3
---

## 新規

### {{F:cleanup-fix-creates-destructive-path}}. 衛生上の所見を閉じる fix が、元の所見より重い破壊経路を新設した [権限逸脱]

- 事象: 段 6 レビューが「publish の一時ファイルが書込み失敗時に `registered/` へ残る」を
  must-fix として出した。fix 1 巡目は cleanup を無条件 `unlink` にし、
  **自分が作っていない既存ファイル・symlink まで削除する**経路を作った。
  焦点再レビューがこれを `regressed` と判定した。fix 2 巡目は `stat` による inode 検査を
  足したが、`stat` と `unlink` が分離した **TOCTOU** であり、しかもその危険な cleanup を
  共有 helper の全 caller へ拡大していた。2 回目の焦点再レビューが再び `regressed` と判定した。
  3 巡目で helper を wave 前の実装へバイト一致で戻し、掃除の代わりに
  「orphan の path を構造化 reason として申告する」形へ縮退させて閉じた。
- 根本原因: 残骸が残るという**衛生**の所見に対して、能動的な削除で応じた。
  削除は content-addressed で immutable な公開領域に対する破壊操作であり、
  元の所見 (ゴミが残る) より失敗時の被害が大きい。
  所見の重大度と対応の破壊力を突き合わせていなかった。
- 恒久対応: 正しさ防壁でない衛生所見は、**能動的な削除より申告 (構造化 reason) を既定**とする。
  破壊操作を伴う fix は、その操作が「自分が作ったものだけ」に限定されることを
  race を含めて示せない限り採らない。判断規律は `DW-O16` の焦点再レビューが担い、
  fix が破壊操作を含む巡では所見ごとの closed/partial/**regressed** 表を必ず取る。
- 再発検知: 焦点再レビューの対応表で `regressed` が出ること。本 wave では 2 巡連続で出た。

### {{F:mutation-expected-nodes-underregistered}}. 変異の期待 node を主要 node だけで登録し、実際の blast radius を過小に見積もった [テスト代表性]

- 事象: 事前登録した 10 変異を走らせたところ、全件で赤は出た (検出は成立) が
  **5 件が MISMATCH** になった。観測された赤 node 集合が、登録した期待集合の
  真の上位集合だったためである。例えば early gate を削除する変異は、登録した 5 node に加えて
  late gate 側の 3 node と metamorphic 1 node も赤にした。gate の欠陥ではなく親の登録が過少だった。
  観測集合で再登録して再走し、10/10 KILLED・期待 node 完全一致を得た。初回台帳は
  erratum として保持している。
- 根本原因: 期待 node を「その変異が主に狙う検査」だけで書き、
  **同じ入力経路を共有する他のテストも赤くなる**ことを数えていなかった。
  二重 gate (early と late) を意図的に併存させた設計では、片方を消すと
  両方を踏むテストが同時に赤くなるのが正常である。
- 恒久対応: 期待 node は「狙った検査」ではなく **その変異で赤くなる node の完全集合**として登録する。
  完全集合が事前に確定できないなら、初回走行を登録確認 (probe) として扱い、
  観測集合で再登録して再走し、初回台帳を erratum として残す。手順の正本は `DW-M08`
  (事前登録の期待 node と記録 node を同じ形式へ正規化して突き合わせる) と `DW-M02` (erratum 保持)。
- 再発検知: 変異 harness が MISMATCH を返し、観測集合が期待集合の上位集合であること。
