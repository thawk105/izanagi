---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-20
wave: dev-wave-t1172-land-lease-renew
seq: 1
title: '[T-1172] land直前のlease renewを実装した (コード+テスト、branch worktree-dev-wave-t1172-land-lease-renew、変異matrix = baseline 323 passed・7/7 KILLED・SURVIVED 0・MISMATCH 0)'
---

## 本文

- ユーザー裁定: 2026-08-17 /rulings 全件 第5回 (`docs/archive/worklog-phase3-0817-622.md:449`)。
  land直前のlease renewを入れる。裁定文の「660秒 > 300秒」の300秒は、段3 lensA (並行性安全性
  レンズ) の実測で waiter ticket の TTL であり lease 本体の TTL (2400秒) ではないと判明したが、
  受入完了〜land完了の間 claim() による heartbeat が一切発生しない区間が生じうるという renew の
  必要性自体は変わらず、実装方針は裁定どおり進めた。
- 棄却 finding: 段3 lensA の blocker1件 (stale判定〜`os.utime()`間のTOCTOU) と major1件
  (exclusive lock 保持中の他wave `claim()` との競合) は、既存 `claim()` の self-renew 分岐
  (`tools/wave_land_window.py:733-761`) も同型の特性を持つ既存挙動と判明したため、renew 固有の
  新規リスクではないと裁定し対象外とした ({{D:renew-non-acquiring-primitive}} 参照)。claim() 側を
  含めた族一般化は DW-G03 の独立2例要件を満たさず見送り、将来の hardening wave 候補として
  ここに記録する。
- セッション異常: 段6 fix 子 (stage=fix) が自身の Pegasus dispatch 環境障害 (`qstat -Q` preflight
  rc=1) でテスト実走できず、DW-S05-C に従い「実装済み・未実走」と正直に報告した。親が独立実走で
  108/108 green を確認した (実装コードは変更なし、テスト3件追加のみ)。
- 工数 (全て `gpt-5.6-luna`、reasoning=max): 段2 plan 402秒/6 call、段3 lensA (sol) 647秒/12 call、
  段3 lensB (luna) 370秒/9 call、段5 author 858秒/57 call、段6 lensC 289秒/9 call、
  段6 lensD 340秒/17 call、段6 fix 249秒/18 call。変異 matrix (B-057) M1-M7 = baseline
  323 passed (既知の無関係赤 `test_exploration_external_root_keeps_wave_clean` は
  `--deselect`、base commit でも失敗することを stash 退避で裏取り済み)・7/7 KILLED・
  SURVIVED 0・MISMATCH 0。

## 次の一手差分

### 完了

- [T-1172] land直前のlease renewを実装した。`tools/wave_land_window.py::renew()` (非取得型 —
  claim() の取得・待ち行列機構には一切触れず、既に自分が保持し stale でない lease の mtime だけ
  touch する) と `tools/dev_wave_land.py::main()` の呼び出し (best-effort、stderr ログは
  `land()` 呼び出し後・release ログ直前へ遅延させ、例外時 stderr 完全空文字契約を保つ) を実装。
  段2 codex plan、段3 敵対相談2レンズ、段6 敵対レビュー2レンズ+fix (blocker1件を3テスト追加で
  解消)、変異 matrix M1-M7 (7/7 KILLED) を実施した。
  remaining: none
  base: 4016098ea7253a036175c4b6f9ad640287c7d2bf707b924b35fd74df87c51013
