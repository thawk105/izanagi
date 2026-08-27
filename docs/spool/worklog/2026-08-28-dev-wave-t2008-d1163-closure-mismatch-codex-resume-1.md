---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-28
wave: dev-wave-t2008-d1163-closure-mismatch-codex-resume
seq: 1
title: [T-2008] D1163 の closure mismatch gate 撤去を実装した (code + tests + docs、branch worktree-dev-wave-t2008-d1163-closure-mismatch-codex-resume、変異 baseline 8/8 PASSED・KILLED 8/8)
---

## 本文

- 実装 commit は `20bdef0b8`、診断順位 fix は `cbae5f296`、historical consumer fix は
  `c4fb9ad44`。main 取込み後の中間受入 tip は `79532ab38`。
- 段3 consultation 2本、段6 initial review 2本、焦点再レビュー 3本。最重要な real 所見は
  historical marker の consumer 脱落、過去 figure の current-SHA 偽拒否、Layer3 consumer の旧5-key/新6-key互換。
- 変更 test module 7本は単独で合計 493 passed。撤去対象外束縛の保持検査は 36 passed。
  fix4 後は backoff 12、autonomous completeness 257、trial/workload 3 passed。
- 変異 matrix は baseline 8/8 PASSED、KILLED 8、SURVIVED/MISMATCH/TIMEOUT 0。
  repo 内 test が同一権限主体の共謀改変を完全に防げない限界は D387 どおり。
- 中間受入は初回 14 failed を fix4 へ返し、再走で `18306 passed / 61 skipped`、
  red 0、flake 0、`child-green`。provenance は新規違反 0、既知履歴 54 件を分離表示。
- 一次資料・変異・裁定パッケージは
  `output/insights/2026-08-28_t2008-d1163-closure-mismatch/README.md`。
- scope 外として `current-closure-unavailable`、persisted WAL 共通 certification、public token capability、
  D956/D967 supersession を実装せず裁定パッケージへ返した。

## 次の一手差分

### 完了

- [T-2008] D1163 の `recorded-current-closure-mismatch` 拒否を exact 1 条件だけ撤去し、
  D422 の purpose・view型・受理点・reason reader・recorded blob 束縛を維持した。
  remaining: none
  base: 52d1aa03882ac90b52f18ccdce2ce75f7c2a76afef2c114be6f403a27cb2aafa

### 新規

- {{T:current-closure-unavailable-ruling}} **P1・ユーザー裁定待ち**:
  `current-closure-unavailable` も規律 7 に従って撤去するか。推奨は撤去。
- {{T:persisted-wal-certification-ruling}} **P1・ユーザー裁定待ち**:
  persisted WAL の verdict/receipt を全 certified consumer の共通 admission 層で束縛するか。
- {{T:certified-view-token-capability-ruling}} **P2・ユーザー裁定待ち**:
  `_CERTIFIED_VIEW_TOKEN` の module-private 限界を外部 capability へ移すか。
- {{T:d956-d967-supersession-ruling}} **P2・ユーザー裁定待ち**:
  D956/D967 の現行 code 同一性理由を後継決定で明示 supersede するか。
- {{T:mutation-fixed-source-clone}} **P2・dev-wave 改善候補**:
  並行 land 中の mutation wrapper を共通 main 進行で rc=125 にしない fixed-source clone 手順を安全に自動化する。
