---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-19
wave: dev-wave-t1362-reasoning-pin
seq: 1
title: 段5 author・段6 fix の reasoning を docs 権威から機械強制した (コード + テスト + docs + 記録、branch worktree-dev-wave-t1362-reasoning-pin、変異 matrix = baseline PASSED・6/6 KILLED・SURVIVED 0・MISMATCH 0)
---

## 本文

- エージェント工数: Codex 9 job (planner 1 / consult 2 / author・fix 3 / review 3)。
- 段3 敵対相談2レンズが D275 の未認識 (parse対象3節限定がT-1362裁定と矛盾) と、
  旧author/fix receiptの後方互換欠落を検出。段6 敵対レビュー2本のうちレンズAが
  それを実装差分側でも再確認し、fixで解消した。詳細は {{D:dev-wave-author-fix-docs-bound}}。
- 変異事前登録は当初7件で起草したが、check_docs.pyのDW-S05-A pin (段2で追加設計) を
  対象にした1件がtest_check_docs.py内200件超の無関係テストへ波及する広範カスケードと
  実測判明し、DW-M01の単一理由性要件を満たせないため spec から外した (probe→是正の
  2回走行、詳細は `output/insights/2026-08-19_t1362-reasoning-pin-mutation-spec.json` の
  commit 履歴)。同pinの正しさは専用の正例/decoy/duplicateテストが通常のtest suiteで
  別途検証している。
- test_codex_worker_launch.py の wall-clock 予算 (既定3秒) 依存テスト群が、共有計算機の
  高負荷下で断続的に失敗node集合を変えながらflakeすることを対照実験で確認した
  (fix適用前commit単独でも同型のflakeを再現、詳細は F57 への再発追記)。

## 次の一手差分

### 完了

- [T-1362] 段5 author・段6 fix の codex 起動へ docs 権威由来の `reasoning` 機械強制を実装し、
  check_docs.py へ DW-S05-A の exact-pin を追加し、旧 receipt との後方互換を保った。
  remaining: none
  base: 0b5cedd362ebdf7e58d73f99ad0f5f600c0ff5e9d79f7bd6d06b69051b61ce45
