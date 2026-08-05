---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-08-05
wave: dev-wave-t419-u2-contract-generation
seq: 1
---

## 新規

### {{F:fuse-masks-mutation-attribution}}. 後段の fail-closed 安全弁が、狙った検査の変異を隠した [恒真ゲート] [変異帰属]

- 事象: 世代 validator に「構造・連番・key 一致・hash 一意性・隣接遷移」の検査と、その後段に
  「世代列は 1 本」の bootstrap fuse を同居させた。事前登録した変異のうち 2 件
  (隣接検査の呼出し削除、hash 一意性検査の削除) は、狙った検査を消しても後段の fuse または
  隣接検査が**同じ入力を拒否する**ため、赤の理由が一つに絞れなかった。harness 上は KILLED と
  出るが、実際には診断 message の差で赤くなっていただけである。
- 根本原因: 負例 fixture が、狙った検査**以外**でも拒否される入力になっていた。
  過剰決定 (冗長 gate) を単独変異の証拠に使った。
- 恒久対応: fuse を含まない private validator を分離し、負例は「検査を消すと**受理されてしまう**」
  ことで赤になるようにした。hash 一意性は、異なる env の 1 世代列 2 本が同じ contract hash を
  持つ collision seam へ差し替えた。tuple 型の負例も、空 tuple (fuse でも落ちる) から
  「有効な要素を 1 件入れた list」へ変えた。
- 再発検知: 変異の期待 node と実測 node の突き合わせ。この wave では独立 golden を 3 テストが
  共有する変異が MISMATCH として出て、冗長 gate であることが判明した。

### {{F:delegation-seam-left-unpinned-by-its-own-fix}}. 検査を private へ切り出した fix が、委譲そのものを未固定にした [恒真ゲート] [変異帰属]

- 事象: {{F:fuse-masks-mutation-attribution}} の是正で public validator を
  「private validator への委譲 + fuse」に分けたところ、負例がすべて private を直接呼ぶようになり、
  **委譲の 1 行を削除しても検出されない** seam が新たに生じた。public へ渡していたのは
  有効な入力と fuse に到達する入力だけだった。1 度目の是正では public 経路の負例を足したが、
  それは private 側の検査を消しても赤になるため、委譲専用の witness にはならなかった。
- 根本原因: 「検査本体の帰属」を直したときに、「本体を呼んでいること」の帰属を作り直さなかった。
  抽出 refactor は検査を 1 つ増やすのではなく、検査対象の境界を 1 つ増やす。
- 恒久対応: private helper を spy へ置換し、public validator が同じ mapping で spy を
  ちょうど 1 回呼ぶことを直接 assert する専用テストを置いた。spy が private 実装を遮断するため、
  赤の理由は「委譲が無い」ことだけに絞れる。
- 再発検知: 抽出 refactor を含む fix のあとは、抽出先だけでなく**呼び出し辺**にも変異を登録する。
