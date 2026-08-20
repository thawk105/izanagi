---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-20
wave: t1428-worktree-submodule-tool
seq: 3
title: '[T-1428] worktree submodule 初期化を専用スクリプトへ集約した (コード+テスト+docs、branch worktree-T-1428-worktree-submodule-tool、変異matrix = baseline 51 passed・4/4 KILLED・SURVIVED 0・MISMATCH 0)'
---

## 本文

- 段1-3 (brief→プラン→敵対相談2本) を経て、段4で親が裁定した設計は {{D:worktree-submodule-init-tool}}。
- 段5実装後、親が実環境 (このworktree自身) に対して新CLIを直接実行したところ、再利用対象の
  既存関数 `update_submodules_no_fetch()` 自体が本 repo の実際の環境設定に対して失敗すること
  を発見した ({{F:submodule-nonlocal-url-false-reject}})。段4裁定の前提を覆す新事実のため
  DW-STOP に従い一旦停止し、AskUserQuestion でユーザーへ技術的選択肢
  (共有関数を直す/新スクリプト側だけ迂回/一旦停止) を提示した。ユーザーは「共有関数の
  事前検査を修正 (推奨)」を選択し、{{D:submodule-url-resolved-fallback}} で対応した。
- 段6 敵対レビュー2本 (独立、正しさ・安全境界レンズ/波及・一貫性・所有境界レンズ) が、
  独立に同一の脆弱性 ({{F:worktree-registry-spoofed-gitdir}}) を発見した。fix3巡目
  (DW-O16 上限) で修正し、統合後の焦点再レビュー1本で closed を確認した。焦点レビューが
  発見した残存ギャップ (別の実在 worktree への偽装) は実害度を評価し、
  {{F:worktree-registry-spoofed-gitdir}} の「残る限界」として記録し今回は対応しなかった
  ({{D:registered-worktree-chroot-boundary}})。
- 実環境検証: 自 worktree (冪等性) と、実装子用に新設した別 worktree
  (真に未初期化、nested submodule 含む) の双方に対して新CLI直接実行が成功した (rc=0)。
  焦点走 (test_dev_wave_submodule_init.py 等7ファイル) は 927 passed / 3 skipped。
- 変異matrix (`tools/mutation_worktree.py --commit 7b8a9e09`) は Pegasus queue 混雑による
  queue-wait-timeout (rc=16) で計4回中断し、都度 `--resume` で再試行して完走した
  (queue 混雑は `qstat -u tanab` で最大11件の並行 wave 待機を確認、他 wave 由来でこの wave の
  変異差分とは無関係)。初回本走で KILLED=1・MISMATCH=3 (SURVIVED 0、全件検出したが親の
  expected_nodes 予測が過小だった) となり、DW-M08 に従い実測 failed_nodes で spec を補正し
  再登録・再走して baseline 緑・4/4 KILLED・SURVIVED 0・MISMATCH 0 を確定した。
- 段2-6 で codex を計10回起動 (plan 1, consult 2, author 1, fix 3, review 2, focus 1)、
  全て `gpt-5.6-luna` / `reasoning=max` で完走。
- **待ち手の誤判定を実測**: `dev_wave_wait.py producer` が、実際にはプロセス生存中・
  変異未完了 (`summary.completed=0`) の状態で「完了」を通知した (`--max-wait-seconds` 到達を
  完了として扱った可能性)。通知を鵜呑みにせず `mutation-result.json` の中身と producer pid の
  生死を毎回自分で確認する運用に切り替え、以降の全ラウンドで正しく検出できた。

## 次の一手差分

### 完了

- [T-1428] worktree 再作成時の submodule 初期化を専用スクリプトへ集約し、実装・敵対レビュー・
  実環境検証・変異matrix・commit まで完了した。受入・land は本 wave 内で後続する。
  remaining: none
  base: 3089670d74359dbca7e19064ce81bd7779896e65d554324b02fa7f37fbb6d0ae
