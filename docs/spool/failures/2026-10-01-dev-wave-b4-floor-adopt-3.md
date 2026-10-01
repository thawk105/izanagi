---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-10-01
wave: dev-wave-b4-floor-adopt
seq: 3
---

## 新規

### {{F:docs-cell-read-by-code-scoped-as-docs-only}}. コードが読む事前登録セルへの記入を、consumer を走らせずに「docs のみ・計算 0」と見積もった [手順漏れ]

- 事象: B-4 床値の採用裁定 (md_3) は「§5 floor 欄へ pin を書くだけ、docs のみ・計算 0」として起票された。前 wave の材料は
  「読み取り関数の述語の読解で通る (実行はしていない)」と書いていた。記入を当てた木で B-4 系 test を走らせると、resolver が
  spec の束縛する追跡外 binary を lstat できず pin を拒否し、材料レポートが評価器の前で止まって 34 failed + 2 errors になった
  (記入を戻した木では同じ 4 file が 259 passed)。記入は保留した ({{D:b4-floor-adopt-defer-entry}})。main へ着地していれば
  受入と材料レポートが binary を置いていない全 checkout で赤になっていた (near miss)。
- 根本原因: 記入先の欄を resolver・材料レポート生成器・実文書回帰 test が読むことを、見積りの段で実行して確かめなかった。
  test 側も docstring で「floor 登録 wave で更新する」と予告していたが、起票と材料はそれを拾わなかった。
- 恒久対応: `docs/dev-wave/operations.md` の `DW-O09` (docs のみの wave でも、変更 path で test を検索し hit を読む) が
  本 wave の発見経路として既にある。見積りの側は memory `docs-cell-read-by-code-run-consumer-tests-first`
  (記入を当てた木と戻した木で consumer test を比べてから「docs のみ」と言う) を固定した。新しい gate・検査は足さない。
- 再発検知: 事前登録・凍結文書のセル記入を扱う wave で、記入を当てた木の consumer test の実走記録が brief に無い場合が同型。
