---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-20
wave: dev-wave-t202-receipt-memo
seq: 1
title: '[T-202] real_repo_receipt_memo の2欠陥 (UID replay / pickle-before-isinstance) を閉じた (コード+テスト、branch worktree-dev-wave-t202-receipt-memo、変異matrix = baseline PASSED・3/3 KILLED・SURVIVED 0・MISMATCH 0)'
---

## 本文

- 2026-07-31 起票・19日 carry の最長 carry 残務。設計・経緯・reason 語彙・影響ファイルの詳細は
  commit `2fc7655e` 本文を正本とする (worklog へ逐語再掲しない)。設計判断は {{D:receipt-memo-nonce-json}}
  を参照。
- 段2 codex plan (read-only) が提案した worker 側 nonce 配線の file:line 主張
  (`conftest.py:900-906`) は、段3 敵対相談レンズA が現物 grep で不一致と検出した (その行域は
  `pytest_configure()` 本体で環境変数設定は無かった)。plan は xdist の伝播機構
  (`pytest_configure_node`/`workerinput`) 自体の実在は正しく検証していたが、**新設フックの
  具体的な設置行番号は誤っていた**。段4 で親が worker 側配線を「controller 限定
  `pytest_configure_node` とは別に、worker でも実行される既存 `if hasattr(config,
  "workerinput"):` 分岐相当の箇所」と訂正指示し、段5 実装はこれに従って正しく配線した。
  同型の近道 (「機構が存在する」の確認だけで「どこに書くか」まで plan を鵜呑みにする) の
  再発防止として、command 側への反映候補を検討したが、既存の段3 敵対相談運用
  (DW-S03 が「brief の file:line」を明示的に攻撃対象としている) で既に構造的に捕捉できている
  ため、新規の防壁追加は不要と判断した (今回は実際に段3 が捕捉に成功した実例)。
- 段6 敵対レビュー2本が、新設テストの `import pytest` 漏れ (親の焦点走で実測、
  132 passed/1 failed) と、DW-M01 変異事前登録候補のうち M2 (`object_pairs_hook`除去)・
  M4 (nonce除去) の positive control が単一理由性を満たさない設計問題を検出した。
  fix でこれら4件 (import漏れ、M2のduplicate-key再照準、M4のreader-replay再照準、
  書込側bytes上限の追加) を closed で解消した。
- 変異 M3 (`parse_constant`除去) は、`_is_json_tree()` の finite 検査が `receipt`/
  `t080_freeze_migration_observation`/`held_checks` の全ネスト値に対し常に冗長に効くため、
  単一理由の変異として独立登録できないと段6レビューBが判定した (コードは
  defense-in-depth として維持、`t080_freeze_migration.py:186-215` の既存パターンに倣った
  設計であり削除しない)。
- 変異 matrix は probe (`expected_status=SURVIVED`) で実際に落ちる node を先に観測してから
  本走 (`--runner-mode dispatch --force-dispatch --detached`) を registered した。
  probe と本走で observed failed_nodes は完全一致 (再現性確認)。
  baseline PASSED・M1/M2/M4 とも matches_expectation=true。
- 段6終了時点の焦点走 (test_real_repo_serialization.py, test_s8b_binding_driftguards.py,
  test_s8b_oracle_driver.py): fix後 133 passed / 20 skipped / 0 failed
  (20 skip は pre-existing、diff起因の新規skipなし)。
- 段8 自己改善候補1件を検出 (下記「次の一手」の新規項目)。
- 受入全走は本 fragment の commit 後に投入する (未実施)。

## 次の一手差分

### 完了

- [T-202] `orchestrator/tests/real_repo_receipt_memo.py` の2欠陥
  ((a) `--testrunuid` replay で実 receipt payer が0回になる、(b) `pickle.loads` が
  `isinstance` 判定より先に実行される) を、controller nonce の xdist 伝播 (新設
  `pytest_configure_node`) + closed-schema JSON (`object_pairs_hook`/`parse_constant`
  必須、schema検証後にのみ `ReceiptResolution` を構築) で閉じた。段6 敵対レビュー2本 →
  fix (4件closed) → 変異matrix (baseline PASSED・3/3 KILLED・SURVIVED 0・MISMATCH 0、
  probe再現性確認済み) まで完了 (commit `2fc7655e`)。受入全走は未実施 (次の一手へ持ち越し)。
  remaining: none
  base: 1c0171f109442dc3886f78c05a24606449332318881926688074db062df3f0ee

### 新規

- {{T:dev-wave-lane-required-for-consult}} **P2・新規**: `docs/dev-wave/core.md` の
  DW-C01「`--lane`は`--stage consult`専用。他段はrc=2で落ちる。」という文言を、
  本 wave で実測した `tools/dev_wave_codex.py` の実際の argparse 仕様
  (`--stage consult` では `--lane` が**必須**、未指定だと rc=1 で即死。他段は指定すると
  rc=2 で落ちる) に合わせて明確化する。「専用」という語は「consult でしか使えない」
  (今回誤読した意味) と「consult では必須」のどちらにも読め、本 wave で実際に段3 の
  初回投入が rc=1 で無駄撃ちになった (`--lane luna` を追加して再投入し解消)。
  dev-wave docs 3層の予算はほぼ満杯と既知 (`docs-budget-stewardship` 系の申し送り) のため、
  本 wave では反映を試みず候補記録に留める。
