---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-22
wave: worktree-dev-wave-t646-master-seed-toctou
seq: 1
title: '[T-646] floor_protocol.json master_seed TOCTOU の holdout freeze producer 残存経路を修正した (コード+テスト、branch worktree-dev-wave-t646-master-seed-toctou、変異matrix = baseline PASSED・M1-M2 2/2 KILLED・SURVIVED 0・MISMATCH 0)'
---

## 本文

- [T-646] は「qsub 後に working tree だけ書き換えた master_seed が job 側の dirty 検査
  (`output/` 除外) をすり抜け、driver が別 schedule を走らせる」という主張だった。着手前実測
  (使い捨て repro script + 実 repo での非破壊 `resolve_current_floor_protocol` 呼出し) で、
  主経路 (`run_campaign`/CLI、`s8b_ratified_freeze.py`、`s8b_holdout_admission.py`) は
  commit `cca78d3d` (2026-08-17、床値 protocol 権威の resolver 配線) で既に working-tree-only
  mutation を fail-closed 拒否すると確認した。carry は起票 (2026-08-08) から今回までの
  worklog fold 7 回 (entry 805〜811) を、この fix と無関係のまま素通りしていた。
- 段2 codex (read-only plan) が `s8b_holdout_freeze.py:1348-1378`
  (`_validate_floor_inputs`、`build_v2_g1_candidate` の producer write-path) だけが raw
  working tree 読込みのまま残っていると発見。同ファイル内の `measurement_closure` /
  `known_axes_freeze` / `generator` / `design_source` は既に `_blob_at_head` で captured
  HEAD blob 束縛済みだったが、floor protocol の読込みだけこの idiom から漏れていた。親が
  file:line を独立に追跡して確認した。
- 段3 敵対相談 2 レンズ・段6 敵対レビュー 2 レンズはいずれも所見 0 件 (real なし)。段3 lens A
  だけ、fix 実装 (`_blob_at_head`) 自体が共有する既存弱点 3 点 (HEAD が commit である保証がない・
  HEAD tree entry の exact mode 未検査・git replace object 未衛生化) を指摘し、scope 判断は
  {{D:t646-holdout-freeze-head-binding-scope}} に記録した。
- 変異事前登録 (B-057、段4): m1 (check 無効化、負例) / m2 (常時拒否、正例、既存 17 test が
  KILLED を裏取り)。実測 baseline PASSED・M1/M2 2/2 KILLED・SURVIVED 0・MISMATCH 0。
- 焦点走 (`orchestrator/tests/test_s8b_holdout_freeze.py`、計算ノード) は 121 passed, 2 skipped
  (author 自己申告と親の独立再走が一致)。
- [T-647] (bench を走らせない correctness-only の COMMIT を計測契約束縛の対象と数えるか) は
  独立の未裁定論点のため今回も scope 外 (ユーザー指示)。

## 次の一手差分

### 完了

- [T-646] holdout freeze producer (`s8b_holdout_freeze.py`) の floor protocol working-tree
  読込みを captured HEAD blob 束縛した。主経路は commit `cca78d3d` で既に安全と確認済み。
  remaining: none
  base: 01ce1bf0acd34adbbfcd661aa40ed4771f9aeb5f40888e2d8855f2a0efea8109

### 新規

- {{T:holdout-freeze-head-binding-hardening}} **P3・新規**: `s8b_holdout_freeze.py` の
  `_blob_at_head`/`head` 捕捉 (`measurement_closure` 等 4 箇所 + 本 wave が追加した floor
  protocol 束縛が共有) は、HEAD が commit である保証がない・HEAD tree entry の exact mode
  未検査・git replace object 未衛生化の 3 点が既存弱点として残る。`s8b_floor_campaign.py` の
  `_head_commit_oid`/`_head_blob_100644`/`_sanitized_floor_git_env` は同種の脅威をすべて
  閉じている。scope 判断の根拠は {{D:t646-holdout-freeze-head-binding-scope}}。
