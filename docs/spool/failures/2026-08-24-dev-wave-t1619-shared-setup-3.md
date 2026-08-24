---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-08-24
wave: dev-wave-t1619-shared-setup
seq: 3
---

## 新規

### {{F:mutation-blob-face-invisible}}. blob として読まれる面への変異が見えず偽 SURVIVED を作りかけた [恒真ゲート] [テスト代表性]

- 事象: 段 4 で登録した 5 変異のうち 3 件が、被検査テストから構造的に見えない面を対象にしていた。
  段 2 plan がその 3 件を「赤くなる」と設計し、段 3 の敵対 2 レンズもこれを指摘しなかった。
  そのまま走らせれば「変異が生き残った」という誤った証拠を作っていた。
- 根本原因: 変異 harness は変異を commit せず working tree へ書く。一方、評価対象を
  **resolved commit の git blob として読む**テストには working tree の変更が届かない。
  「変異が効かない」と「変異が見えない」を実行前に区別する手順が無かった。
- 恒久対応: {{D:mutation-visibility-probe-before-registering}} — 事前登録の前に、
  可視の正例と不可視の負例を 1 本ずつ実測して可視面の表を作る。実測できない面へは登録しない。
- 再発検知: 事前登録した各変異について、可視面の型 (import される評価器 / blob として読まれる
  評価対象 / working tree から読み直される面) を裁定文へ書く。型を書けない変異は登録しない。
  本 wave の実測では、評価器コードの変異は 1 件だけを赤にし、評価対象 file の変異は 5 件すべてを
  緑のままにした。

### {{F:mutation-harness-group-suffix}}. 変異 harness が xdist group 接尾辞を正規化せず KILLED を得られない [手順漏れ]

- 事象: xdist group を新設した版で変異 matrix を走らせると、5 変異すべてが MISMATCH になった。
  検出力は変わっていない。期待 node は pytest collection (接尾辞なし) に対して実在検査され、
  失敗 node は `@<group>` 接尾辞付きで記録されるため、どちらの書き方でも完全一致しない。
  接尾辞付きで書いた spec は collection 検査で「期待 node が実在しない」と拒否された。
- 根本原因: harness の記録側に `_strip_group_suffix` 相当の正規化が無く、
  期待側の検証基準 (collection) と記録側の表記が食い違う。
- 恒久対応: {{D:shared-prelude-needs-group-and-fixture}} の手順として、group を新設する wave は
  harness の status label を証拠にせず、**両版の失敗 node 集合を正規化して突き合わせる**。
  本 wave はこの比較を実行し、同一 spec bytes・両版 baseline 緑のもとで 5 変異すべての
  kill 集合が完全一致することを確かめた。tool 側の正規化は
  {{T:mutation-harness-group-suffix}} で閉じる。
- 再発検知: group を持つ node を期待 node に含む spec を走らせたとき、
  MISMATCH の原因が接尾辞だけであることを正規化比較で切り分ける。
  {{T:mutation-harness-group-suffix}} が入れば harness 側の負例と正例で機械検出できる。
