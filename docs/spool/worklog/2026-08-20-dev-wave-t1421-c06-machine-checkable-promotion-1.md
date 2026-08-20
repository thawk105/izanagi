---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-20
wave: dev-wave-t1421-c06-machine-checkable-promotion
seq: 1
title: '[T-1421]/[T-1384] 8c条件6 (C06、budget consumer) をmachine_checkableへ昇格した (コード+テスト、branch worktree-dev-wave-t1421-c06-machine-checkable-promotion、変異matrix = baseline PASSED・4/4 KILLED・SURVIVED 0・MISMATCH 0)'
---

## 本文

D529 手順 (契約反転・registry登録・DECIDER_VERSION v5→v6・第10世代 condition-freeze record 発行を
不可分の1commit) で C06 を昇格した。T-1355/T-1379 (C05/C07 昇格) と同型。[T-1384] は同一 C06
昇格を指す 2026-08-18 起票の重複 carry で、本 wave の着地で両方を完了させる。

段3 敵対相談2レンズ (sol/luna) は blocker 0件・1件 (計2件)。luna レンズの blocker
(「過去commitのreason code遷移」) は親が `evaluate_all`/`_evaluate_undefined` を直接読んで検証し
refuted と裁定 ({{D:c06-past-commit-reason-drift-is-precedented}})。段6 敵対レビュー2本は blocker
0件、real所見は「g10 recordがuntrackedのため明示的git add必要」(実装済み) のみ。

親が段5実装後に独自の consumer test 拡張焦点走 (DW-O26) を行い、10件の追加red
(test_p3_autonomous_workload_trial.py・test_trial_registry.py) を発見。`git stash` によるA/B検証
(2回、100%再現性) で自分の変更に起因すると確定し、`contract_loader_binding` の commit前提tripwire
(disk bytes ≠ HEAD blob 検出) と特定した。統合commit後に該当11nodeid (10件+
test_current_repository_snapshot_exactly_matches_head) を再実走し **1275 passed, 0 failed** で
全て解消したことを確認した。

変異matrixは当初 `@s8c-preregistration-candidate` (xdist_group) サフィックス付きnodeが
harness の期待node事前登録で「pytest collectionに実在しない」としてabortした。該当3nodeを
`--deselect` でmutation run自体から除外し (DW-C01「既存赤はdeselect」の趣旨を準用、対象は
redundantな検出層でregulation上も単一理由性に問題なし)、baseline PASSED・4/4 KILLED・
SURVIVED 0・MISMATCH 0 で完走した。

reachability検査の甘さ (段2 codex plan・段3 lensA/lensB・段6 レビュー2本が独立に確認) は
本waveでは修正せず {{D:c06-reachability-gap-deferred}} により後続waveへ送る。

## 次の一手差分

### 完了

- [T-1421] C06 (budget consumer) の machine_checkable 昇格を D529 手順で完了した。
  remaining: none
  base: e4a75174c69ddfcff24e13e110f365d3f8c97a58dfaf96662c0c8f87cc982d00

- [T-1384] [T-1421] と同一内容の重複 carry。本 wave の着地で解消する。
  remaining: none
  base: c08b7305de4c6e8d5b06995ff31d0b153ef6cc1cd3a9d2924f19053c3fdaf3ca

### 新規

- {{T:c06-reachability-hardening}} **P2・新規**: `_evaluate_c06` の reachability 検査を強化する。
  現状は (a) supervisor 不在時にスキップ、(b) reachable呼出しの集合だけを見て順序・データフローを
  見ない、(c) `_ledger_lock`/`_check_limit_state` は存在のみ検査。`SATISFIABLE_CONDITION_IDS` が
  空のため regulation2 は現状でも侵害されないが、machine_checkable=true という宣言が示す検査の
  強さと実装のギャップは残る。詳細は {{D:c06-reachability-gap-deferred}}。

- {{T:mutation-worktree-xdist-group-node-registration-gap}} **P3・新規**: `tools/mutation_worktree.py`
  の期待node事前登録 (collection存在チェック) が `@<xdist_group>` サフィックス付き node id
  (pytest-xdist の group scheduling マーカー) を「pytest collectionに実在しない」として拒否する。
  実行時の `failed_nodes` には同じ node が group サフィックス付きで現れるため、影響を受けた
  mutation は expected_nodes への正確な登録ができず MISMATCH になるか、`--deselect` で当該test を
  mutation run から除外する回避が要る。今回 (M1: C06契約反転・M4: DECIDER_VERSION revert) は
  redundant な検出層だったため実害なく回避できたが、xdist_group付きtestが単一の検出層になる
  mutationでは登録不能になりうる。`docs/dev-wave/mutation.md` (DW-M07/M08 周辺) への手順追加候補。
