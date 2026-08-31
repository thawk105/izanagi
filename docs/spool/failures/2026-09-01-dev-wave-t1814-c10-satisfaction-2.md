---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-09-01
wave: dev-wave-t1814-c10-satisfaction
seq: 2
---

## 再発

### F71

- **再発: 2026-09-01** — node 抽出規約の射程に **xdist group 接尾辞**が入っておらず、
  `@pytest.mark.xdist_group` を持つテストは変異 matrix の期待 node に**どちらの表記でも
  書けない**ことが判明した。group 接尾辞込み
  (`...::test_current_repository_snapshot_has_zero_satisfied_predicates@s8c-predicate-snapshot`)
  を書くと spec 事前検査が「期待 node が pytest collection に実在しない」で起動前に中止し、
  接尾辞を外すと比較器が接尾辞付きの記録 node と突き合わせて MISMATCH を返す。
  前回 (F71 本体) は抽出が 0 件になる向きだったが、今回は**抽出はされるが検査側と形式が
  揃わない**向きであり、根本原因は同じ「記録側と検査側で node 形式が揃っていない」。
  実測: 本走 2 回目は 4 変異中 2 変異が MISMATCH、差分は同じ 2 テストの接尾辞のみで
  SURVIVED は 0 だった。group を持つ 3 テストを runner argv の `--deselect` で外した 3 回目は
  4/4 KILLED / 一致 4/4。除外前の台帳
  (`mutation-ledger-real2.json`) は erratum として保存した。
- 恒久対応 (本再発分): **既存の `DW-M08` が既に「同形式へ正規化した記録 node との完全一致だけを
  KILLED とする」と定めており、`tools/mutation_harness.py` の比較器がこの正規化を記録側へ
  適用していない。** 規約の追加ではなく道具を規約へ合わせるのが対応であり、
  harness 側の正規化実装を本 fold で採番した新規タスクへ起票した。
  それまでの回避は `DW-M08` の erratum 手順 (期待から外し `--deselect`、除外前の実測を残す) で行う。
- 再発検知 (本再発分): 期待 node に `@` を含む文字列が 1 件でもあれば spec 事前検査が
  起動前に中止する (実測済みの fail-closed)。正規化実装後は、group 付き node を期待へ含めた
  spec が KILLED 一致することを正例として要求する。
