---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-19
wave: t1303-spool-fold-digest
seq: 1
title: '[T-1303] spool_fold.py に carry 解決済み digest を出す読み取り専用 subcommand を足した (コード+テスト+docs+記録、branch worktree-tingly-watching-diffie、変異matrix = baseline PASSED・5/5 KILLED・SURVIVED 0・MISMATCH 0)'
---

## 本文

- command 引数が挙げた凍結境界の参照「D125 決定6・D108 決定2〜5」は実測すると Pegasus 計測パス・
  CC campaign network 境界の話で `tools/spool_fold.py` と無関係と判明した。真に効く凍結境界は
  D128 (台帳書き込みを land lock 内の fold へ一本化する) であり、独立に明記された「wave 側は
  書かない」制約と矛盾しないため、ユーザー再裁定へ戻さず前進した。DW-S04 の「未見事実が
  裁定前提を覆す」には該当しないと判断した。
- `docs/pegasus-runbook.md:785` (§7.3 受入 lease の待ち手節) が記す clean 述語
  「`git status --porcelain --untracked-files=no --ignore-submodules=none`」は現行の
  `tools/dev_wave_wait.py:384` の `_CLEAN_STATUS_ARGV` 実体 (`--untracked-files=all`) と
  食い違っており stale だった。受入 attempt 1 が未追跡の insight ディレクトリで
  `preflight-clean` rc=2 になり (lease 未消費、claim 前の fail-closed)、insight を commit して
  attempt 2 で解消した。runbook 修正候補は段8で自己改善ルーティングへ送る。
- 段6 レビューAが指摘した「極端な carry ordinal・深い carry 鎖が `_extract_latest_active`/
  `_global_ordinal_entries` で構造化エラーにならない」は、既存 `--dry-run`/apply 経路にも
  同じ露出がある pre-existing gap と確認し、この wave の scope 外・低優先度backlogとして
  新規タスク化した (下記「新規」参照)。
- 焦点走で `test_dev_wave_land.py::test_exploration_external_root_keeps_wave_clean` が
  campaign exploration root の `_has_git_ancestor` 判定絡みで失敗したが、git stash による
  clean tree (commit `bb9283f5` 単独) での単独再走でも同一 failure digest
  (sha256=a32fd745f30...) で再現し、本 wave の差分と無関係な pre-existing の赤と確定した。
  受入全走 (Pegasus dispatch 環境) ではこの node は再現せず 13515 passed / 0 failed / 96
  skipped で通過した — 環境依存 (実行 scheduler / tmp path 解決) の可能性が高いが根本原因は
  未特定のため新規 failures エントリは起こさず、この観測だけを記録に留める。
- `--base-digest '[T-1303]'` を自分自身の worklog 記録作業でも実際に使い (dogfooding)、
  `base:` の digest 取得を検証した。

## 次の一手差分

### 完了

- [T-1303] carry 解決済み digest を出す読み取り専用 subcommand `--base-digest` を
  `tools/spool_fold.py` へ追加した。段2 codex plan 起草・段3 敵対相談2レンズ・段4 親裁定
  (P1-b は独立 loader に確定、{{D:base-digest-independent-loader}} 参照)・段5 単一 Codex
  author 実装・段6 敵対レビュー2本 (must-fix無し)・変異matrix 5件 (baseline PASSED、
  5/5 KILLED・SURVIVED 0・MISMATCH 0、`output/insights/2026-08-19_t1303-spool-fold-digest/`)・
  受入全走 (verdict=child-green、13515 passed / 0 failed / 96 skipped) を完了した。
  `docs/spool/worklog/README.md` の `base:` 契約段落へ発見用ポインタも追加した。
  remaining: none
  base: 3069240692244502ac5e5c93bbb4721614af4b8bafc476f9ac139b047197c8e1

### 新規

- {{T:base-digest-extreme-ordinal-gap}} **P3・新規**: `_extract_latest_active`/
  `_global_ordinal_entries` (`tools/spool_fold.py`) は極端な carry ordinal 値
  (int 変換の未捕捉 `ValueError`) や極端に深い carry 鎖 (再帰実装による `RecursionError`) を
  構造化 `SpoolValidationError` にせず、`main()` もこれらを catch しない。段6敵対レビューが
  発見 (T-1303)。既存 `--dry-run`/apply からも同じ経路で到達可能な pre-existing gap であり
  実害は未観測。fix には shared write path (`_extract_latest_active`) への変更が要るため
  T-1303 の scope 外とした。
