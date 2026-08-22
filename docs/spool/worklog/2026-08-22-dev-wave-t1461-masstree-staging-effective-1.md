---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-22
wave: dev-wave-t1461-masstree-staging-effective
seq: 1
title: '[T-1461] floor campaignのmasstree/mimalloc/googletest依存解決をstaged FetchContentで実効化した (コード+テスト、branch worktree-dev-wave-t1461-masstree-staging-effective、変異matrix = baseline PASSED・MUT-1〜8 8/8 KILLED・SURVIVED 0・MISMATCH 0)'
---

## 本文

- D656 の scope 拡大裁定 (2ファイル限定案は dead wiring 実測済み) を受け、依存解決
  (`buildcache.prepare_masstree_fetchcontent`/`_v2_commands`)・独立 expected hash
  (config.h/archive の sha256 を policy.json 凍結 pin closure 外の新規
  `tools/pegasus/policies/floor_masstree_payload_v1.json` へ束縛)・pin 検証の CMake 実行前
  移動 (`_verify_pristine_floor_dependency_sources`)・REFREEZE_DISQUALIFYING_SEAM_NAMES
  登録まで含む実装を完了した。
- DW-G01 生死実験 (計算ノード実測、network 遮断) で SOURCE_DIR staged transport が
  offline で no-refetch のまま build 成功することを確認済み。
- 段6 敵対レビュー 2 本の後、実 pytest 実走で 70 件の失敗を検出 (静的レビュー 2 本は
  検出できなかった空 `source_dirs` での無条件 `KeyError` が主因 — staged 機能を使わない
  既存の全 floor campaign 呼出しを壊す回帰)。fix 3 巡 (DW-O16 上限) で 0 failures /
  1304 passed へ収束。
- 段6 変異 matrix (8変異) の収束過程で 2 つの実質的な知見を得た。
  1. MUT-3 (archive_sha256 の独立 expected hash 比較を無効化) が SURVIVED —
     `test_floor_postflight_staged_source_set_and_expected_hash_are_enforced` が
     config_sha256/payload_policy_sha256 の不一致ケースは書いていたが archive_sha256 の
     並行ケースを書き忘れていた、というテストカバレッジの実質欠落 (実装コード自体は
     正しかった)。archive_sha256 版ケースを追加 (commit `6f689ae8`) して解消した。
  2. MUT-5 (REFREEZE_DISQUALIFYING_SEAM_NAMES 1 key 削除) の expected_nodes 収束で
     `docs/failures.md` F95 (real-repo 直列化 node の xdist_group 接尾辞が
     mutation_harness.py の preflight と実測で異なる表記を要求する既知の構造的制約、
     2026-08-04 初出・08-16/17/18 に再発) を追加で再発させた。素の node id を
     expected_nodes から除外するだけでは不十分で (runner argv に `--deselect` を
     足さないとそのテストは実行され続け failed_nodes に残る) MISMATCH を再現した。
     台帳を検索して正しい回避策 (`--deselect=<素の node id>` を runner argv へ追加) を
     発見し、baseline PASSED・161/161 KILLED (matches_expectation=true) で最終確定した。
     台帳を検索する前に不完全な回避を複数回試し変異本走を無駄にした。F95 へ再発記録済み。
- 実装コミット `1488fe68` (role=author codex + role=integrator claude)、テスト追加
  commit `6f689ae8`、main 取り込み merge `e13047b9` (D662 に従い受入前に取り込み、
  重複ファイルなしの自動 merge)。
- 残存所見 2 件 (`mv -T` の非 atomic 上書きリスク、base-only モードで source_dir kwargs を
  受け取らないことの明示的 negative test 欠如) は段6 焦点レビューで real/refuted 裁定済み:
  前者は各 submission が nonce 別 directory のため実質無害、後者は if 分岐が単純で
  mutation matrix (MUT-8 KILLED) が正方向を検証済みのため機能的リスク低いと判断し、
  いずれも fix 不要で受容した。

## 次の一手差分

### 完了

- [T-1461] floor campaignのmasstree/mimalloc/googletest依存解決をstaged FetchContentで実効化した (コード+テスト、branch worktree-dev-wave-t1461-masstree-staging-effective、変異matrix = baseline PASSED・MUT-1〜8 8/8 KILLED・SURVIVED 0・MISMATCH 0)
  remaining: none
  base: 90ad9cdf01083c0e78630d1f5dfbe981788fc5b6a3717cf5901c0f09e50e8d63
