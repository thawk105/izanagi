---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-08-17
wave: dev-wave-t1202-t1197-cross-module-reach
seq: 1
---

## 新規

### {{F:noop-replace-mutation-fixture}}. 負例 fixture の文字列置換が一致せず変異が no-op になっていた [恒真ゲート] [テスト代表性]

- 事象: 述語の負例 param が `VALUE_FLOW_C12.replace(old, new)` で被検体を作っていたが、`old` が
  fixture 本文に存在せず置換が起きなかった。生成された「変異体」は正例と byte 単位で同一で、
  それに対して `UNSATISFIED` を要求していたため必ず赤になった。同 file の
  `.replace()` ベース変異 70 param を全件検査したところ、no-op はこの 1 件だった。
- 根本原因: 置換の元文字列を fixture の実本文と突き合わせずに書いた。fixture では対象の代入行と
  次の目印行の間に 4 行挟まっており、複合文字列が一致しなかった。置換が起きたことを
  確かめる検査が無かったため、no-op のまま「負例がある」と見なせる状態だった。
- 恒久対応: 当該 param に「置換が適用されたこと (source が元と異なること)」と「対象名の代入が
  意図した回数あること」を確かめる assert を常設した
  (`orchestrator/tests/test_s8c_preregistration_predicates.py` の value-flow 負例)。
  置換ベースで被検体を作る負例は、置換の実在を同じテスト内で assert する。
- 再発検知: 上記 assert が fails-closed で発火する。加えて変異 matrix が当該 param を
  期待 kill node に持つため、負例が空振りに戻れば変異が生存して検出できる。

### {{F:parent-misjudged-red-as-implementation-defect}}. 親が焦点走の赤を fixture 欠陥でなく実装の緩みと即断した [手順漏れ]

- 事象: 段 6 fix 後の焦点走で負例 1 件が赤になった。親は「実装が受理集合を広げた」と裁定し、
  実装を厳格化する fix 巡を投入した。実際の原因は fixture の no-op 変異で、実装は正しかった。
  同じ wave の後段でも、変異 1 件の生存を「検出力の穴」と裁定して負例追加の巡を投入したが、
  真因は述語節が恒真であることによる等価変異だった。いずれも子が実装を変えずに停止し、
  親が独立に検証して裁定を撤回した。
- 根本原因: 赤と生存の原因仮説を 1 つに絞って裁定した。被検体が期待どおり構成されているか、
  変異が実際に挙動を変えうる位置にあるかを先に潰していなかった。
- 恒久対応: 実装子契約の「期待値が誤りと判断したら実装を変えずに報告して止まれ」
  (`docs/dev-wave/workers.md` の `DW-S06-B`) が両方を捕まえた。この契約は現に効いており、
  fix prompt から省略しない。あわせて `docs/dev-wave/mutation.md` の `DW-M02`
  (生存はまず他層の mask と等価変異を疑う) を生存時の最初の手順として守る。
- 再発検知: 子の停止報告を親が独立検証する手順そのものが検知経路である。子が停止したのに
  親が押し切って実装を変えた場合、変異 matrix で当該負例が生存または過剰決定として現れる。
