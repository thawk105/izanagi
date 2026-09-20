---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-09-21
wave: dev-wave-branch-residue-cleanup
seq: 2
---

## 新規

### {{F:cleanup-allowlist-structural-residue}}. 掃除規約の allowlist が構造的残骸に届かず、Codex 子 branch が約 40 wave 相当・155 本溜まった [手順漏れ]

- 事象: 2026-09-21 00:20 JST の `/cleanup-branches` で、稼働 session 6 本に対し worktree 42 本・branch 165 本が残っていた。command の
  安全条件 (`ahead=0` のみ `-d`、locked は報告のみ) で消せたのは branch 4 / worktree 4 だけで、残る 155 本はユーザー裁定と手作業
  (bundle 退避 → `-D`、約 26 分) に落ちた。09-17 の一括掃除も同じ壁で「Codex 子木は裁定へ」で止まっていた。
- 根本原因: dev-wave は Codex 子 (author / fix / probe / unit) ごとに branch と worktree を作るが、main へ入るのは親の統合 commit と
  記録 commit だけで、`DW-S05-A` の patch 統合は子 commit を main の祖先にしない (恒久に `ahead>0` で残る経路。155 本全部の原因が
  これだとは確定していない)。段 9 の自己撤去 (`DW-O28`、D2163) は
  worktree を消しても branch は残し、`/cleanup-branches` §2 は `ahead=0` しか消さないので、生成される残骸に対応する撤去経路がどこにも無かった。
  F747 (掃除が権限を合成して越権した型) の対になる「保守的すぎて溜まる」型。
- 恒久対応: {{D:cleanup-force-delete-and-child-branch}} — 経路 1 (`tools/dev_wave_cleanup.py remove-child` が統合証明済みの子 branch を
  履歴 bundle 退避後に専用経路で `-D`、`DW-O28` 改訂) と経路 2 (`.claude/commands/cleanup-branches.md` §0/§2 の裁定条件つき `-D` と
  削除直前の lock file 再検査)。段 9 は正常終了経路の流入削減、経路 2 は既存・例外残骸 (証明不能な子、同木の旧 fix branch、中断 wave) の
  回収を担い、被覆割合は未確定。
- 再発検知: `orchestrator/tests/test_dev_wave_cleanup.py` の正例 (非祖先・所有 path 一致・中間 commit を持つ子で bundle + `-D`) と負例
  (未統合 rc=20 で不変 / wave 本体 `-d` のみ / 共通 runner の `-D` 拒否 / bundle verify 失敗と削除失敗は partial)、`tools/check_docs.py` の
  command・skill・`DW-O28` の exact pin、本 wave 段 9 での自分の子木に対する実走。
