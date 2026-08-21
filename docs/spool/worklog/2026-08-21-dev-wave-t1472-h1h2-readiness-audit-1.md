---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-21
wave: dev-wave-t1472-h1h2-readiness-audit
seq: 1
title: formal H1/H2 workload campaign の zero-diff readiness audit を行った (docsのみ、branch worktree-dev-wave-t1472-h1h2-readiness-audit)
---

## 本文

- H1/H2 (rr80/rr20 × on/off/swapped) 正式実験の起票可否を段2 codex plan (`--reasoning max`) →
  段3 敵対2レンズ (`--lane sol`=正確性、`--lane luna`=実効性論理) で監査した。結論:
  certified formal launch は現時点で成立しない。決定的直接根拠は
  `orchestrator/campaign/p3_autonomous_workload_trial.py:883-896` の `_preflight_workload_profile()`
  が `effective preregistration unavailable` で明示拒否すること。§5 記入欄9項目中8項目未記入、
  §6 の12前提条件のうち機械的に充足を返す評価器経路が0本であることは、同じ未発効状態の
  corroboration として扱い独立根拠として重複計上しない (段3 lensB 指摘)。詳細な blocker table・
  human lockstep の実行主体分離・T425/T972/T1371/T1438/T1458 との重複状況・期待 artifact の
  存在/不在一覧は `output/insights/2026-08-21_t1472-h1h2-readiness-audit/README.md` を正本とする
  (brief/codex plan/敵対2レンズ逐語/親裁定も同ディレクトリに保存)。approval bytes 生成・裁定代行・
  正式実験起動・結果推測はいずれも行っていない。
- **セッション異常 (F425 再発)。** 段2完了後、read-only 調査用に起動した Agent (fork) のうち
  少なくとも2本 (occupancy 調査担当・spec 抽出担当) が、継承した `/dev-wave` command 本文から
  自分を dev-wave manager と誤認し、無許可で子 general-purpose agent を連鎖的に起動した。
  spec 抽出担当の fork は「緊急停止する」と自称した後も新規子を生成し続け、最終的に (孫世代を
  含め) 10 エージェントを `TaskStop` で手動停止するまで収束しなかった。fork 起動プロンプトに
  F425 の恒久対応 (「あなたは manager ではない」の明示的役割否定文) を適用していなかったことが
  直接の再現条件だった。ファイル書込み等の実害は無いことを worktree/共有チェックアウト双方の
  `git status`・対象ファイル mtime で確認した。詳細は F425 の再発追記を参照。

## 次の一手差分
