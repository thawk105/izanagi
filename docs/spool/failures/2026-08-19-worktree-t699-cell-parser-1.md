---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-08-19
wave: worktree-t699-cell-parser
seq: 1
---

## 新規

### {{F:s8c-batch-limit-blocks-any-merge}}. 8c preregistration の batch 上限をリポジトリ成長がわずかに超え、main への merge を伴う受入が構造的に赤くなる [恒真ゲート] [検査の非対称]

- 事象: [T-699] の受入全走で `git merge --no-ff --no-commit main` 後、
  `orchestrator/tests/test_s8c_preregistration_invariant.py::test_candidate_freeze_matches_contract_and_generation_chain`
  と `::test_repository_tip_binds_current_decider_version_without_activation`
  (共に `@s8c-preregistration-candidate`) が `status=attributable-red` になった。
  `acceptance-red-check` が実測した通り、tested main (非merge commit) では両方 rc=0、
  wave tip (merge commit) では両方 rc=1 — T-699 の変更内容 (`tools/check_docs.py` の
  参照 cell grammar) とは無関係。
- 根本原因: `orchestrator/campaign/s8c_preregistration.py:1316` の `_batch_oids` は
  `len(commits) * len(paths) > MAX_BATCH_REQUESTS` (`MAX_BATCH_REQUESTS = 50_000`,
  同 107行) で `PreregistrationError("batch-request-limit", ...)` を投げる。実測値は
  **50017** — 上限をわずか 17 超過。`commits` は candidate commit の祖先集合、`paths` は
  generation-freeze 系の追跡ファイル群 (generation が進むたびに 1 件ずつ増える)。両者とも
  時間とともに単調増加するため、この閾値超過はリポジトリの自然な成長 (直近では世代8の
  condition-freeze 追加、worklog entry 678 = [T-1355]) だけで到達し、**merge commit の
  内容に関わらず今後のあらゆる dev-wave の受入 merge で再現しうる**。
- 影響: `tools/dev_wave_land.py` は受入 receipt (attributable-red なし) を必須とし
  免除経路が無い既存契約のため、この2テストが赤い限り
  main へ divergence がある**あらゆる wave が land 不能**になる。[T-699] 自身は
  `tools/check_docs.py` の修正を実装・段6敵対レビュー2本 (real所見ゼロ)・変異 matrix
  (2/2 KILLED, MISMATCH 0) まで完了しコード面は健全だが、この理由で land を進められず
  branch `worktree-t699-cell-parser` (commit `7147bf91`、main 取り込み後 `eff98184`) へ
  留め置いた。
- 恒久対応: 未実施 (`orchestrator/campaign/s8c_preregistration.py` は Phase 3 8c 側の実装面で
  本 wave の scope 外。`MAX_BATCH_REQUESTS` の引き上げ、または `_batch_oids`/祖先集合計算の
  重複排除・分割 batch 化のいずれかを、8c 側の専用 wave が判断すべき設計選択)。
- 再発検知: 未実装。次に main へ divergence を持つどの wave が受入 merge を試みても、
  `orchestrator/campaign/s8c_preregistration.py:107` の `MAX_BATCH_REQUESTS` と実測
  `len(commits) * len(paths)` の差が縮み続けている限り同型が起きる。差分 (実測値 − 上限) を
  受入の関門で可視化する監視が無い。
