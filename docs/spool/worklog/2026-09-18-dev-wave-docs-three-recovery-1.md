---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-18
wave: dev-wave-docs-three-recovery
seq: 1
title: 未land文書3件の回収監査と局所整合 (docsのみ、branch worktree-dev-wave-docs-three-recovery)
---

## 本文

- ユーザーが T-2129 / T-2440 / T-2669 を1回収waveへ束ね、land・成果保全・非稼働確認後の対象local清掃を許可した。
  改善実装・次wave・裁定の変更・spool挙動の変更は範囲外。
- 着手時local mainは b2037abfa1。指定tip 60015f6c74 / 4e60e07c98 / 690596918a は全て未回収で、旧作業木はclean。
  旧親はT-2440/T-2669でweekly limitによるblocked (tasks=0、queued=1、子processなし) のまま残存した。
  占有が残る旧worktreeは撤去しない。旧job dirは一次資料として保持する。
- 旧受入はT-2129/T-2440が指定tipでchild-green、T-2669は9 error・1 failedで受領証なし。今回の受入へ流用しない。
- 8f22d8c78 — 3 tipをmain起点で履歴付き統合。独立read-only監査はreal 1 / refuted 0。
  T-2129の検出時点の断定を条件付きへ局所修正し、焦点監査でclosed・GO。T-2669旧4所見も全closed。
  逐語・裁定 = output/insights/2026-09-18/dev-wave-docs-three-recovery/。
- 関連テストは747 passed・3 skipped。bounded localの上限到達後、runnerが計算ノード6371.nqsvへ切替えて完了。
  統合時のcheck_docs・check_codex_agents・spool dry-runはrc=0。全履歴provenanceは11,470件、新規違反なし、既知56件は別掲。
- 最終記録tipの受入・landはこの記録時点では未実施。結果の一次資料はrepo外同rootの本wave job dirへ保存する。
  実装差分ゼロで変異matrix免除。phaseの実装項目は進めず、完了遷移は取り込んだ旧3 fragmentに一度だけ置く。

## 次の一手差分
