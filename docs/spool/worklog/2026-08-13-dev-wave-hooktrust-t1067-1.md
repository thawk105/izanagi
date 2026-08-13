---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-13
wave: dev-wave-hooktrust-t1067
seq: 1
title: codex 子の SIGTERM は警告の誤分類ではなく evidence 猶予だった — dispatcher へ猶予を公開し、分類変更は前提が覆ったのでユーザーへ差し戻した (コード + docs、branch worktree-dev-wave-hooktrust-t1067)
---

## 本文

- 起点は裁定控え rulings11-12 #2 (「codex CLI 0.147.0 の hook-trust 警告 event 2 件を
  launcher がエラー扱いして子を SIGTERM する誤分類を直す」) と [T-1067]。
  **段 1 の実測でこの前提が覆った。**
- 生死実験 (DW-G01): 同一 launcher・同一 CLI で `--evidence-grace-s` だけを 90 秒へ変えた子は
  accepted (model_calls=4、exit 0)。その events にも同じ hook-trust error item が 2 件出ている。
  本 wave で accepted になった 5 走すべてに同じ 2 件が出ており、うち 3 走は effort=max。
  静的にも `_consume_stdout_event` は `thread.started` と `turn.completed` しか見ておらず、
  `item.completed` を type を問わず無視する。**誤分類は実在せず、真因は evidence deadline
  (既定 5 秒) だった。すなわち裁定 #2 の対象 A の真因は [T-1067] である。**
- 親の実測: 成功 4 走の rollout 到着は attempt 開始から delta -0.4〜+0.1 秒。
  **正常時の evidence 到着は 1 秒未満**で、5 秒既定は通常十分。失敗 3 件は起動側の裾 (>7 秒)。
- 観測実験: turn 内で失敗する command 4 種 (rc=1,1,2,3) を実行させても `item.type=error` は
  0 件。失敗は `command_execution.exit_code` に載る。
- **A (分類変更) は実装しない。** 観測できる field が `item.type` と位置だけである以上、
  pre-turn を一律許容すれば未知の致命的 startup error を通す fail-open、一律拒否すれば実 5 走が
  全滅する。ユーザー裁定の二条件 (allowlist 禁止・fail-open 禁止) を同時に満たす設計が無い。
  in-turn 側は発火する実 artifact path が 0 件で、`DW-G04` (条件付き機能の発火 gate) に従い設計メモ止まり。
  `DW-S04` に従い親は不採用にせず、新事実を添えてユーザー再裁定へ戻した
  (控え = dev-wave-jobs/rulings-inbox/2026-08-13-codex-launcher-error-item-classification.md)。
- 敵対相談 2 本 + 敵対レビュー 2 本が独立に効いた。段 6 で両レビューが一致して挙げた 2 件は
  どちらも **land すれば確実に赤になる回帰**だった: (a) 既定 90 秒と
  「grace <= max-wall-clock」の組合せで `--max-wall-clock-s 17` の既存 node が rc=2、
  (b) receipt への `evidence_grace_s` 封印が版なしの v3 拡張で、新 receipt から field を
  消しても `_validate_receipt` / `_audit_receipt_value` が rc=0 になる。
  (b) は「謳うだけで発火しない保証」なので **B-3 ごと撤回**した。
  (a) はレビューの対案 (既存テストへ flag を足す) を採らず、**適応既定 `min(90, max-wall-clock)`**
  にして既存 caller を 1 つも壊さない形へ変えた。
- 段 5 実装子は裁定外に launcher 側へも関係検査を足していた。親の差分監査で検知し、
  段 6 レビューへ明示的に掛けて real と裁定、削除した。
- **受入全走・変異 matrix は未実施のまま停止した。** 理由は環境であって差分ではない。
  `test_codex_worker_launch.py` は login node の bounded scope 予算 (前回ピーク由来の 1.94GiB)
  では cgroup attest が 3 回連続 rc=16 で失敗し、4.29GiB を与えた走行では 59 件が
  `codex_exit_code=-15` (cgroup OOM による fake 子の kill) で赤になる。
  一方 `test_dev_wave_codex.py` は 17 passed / 3.94 秒で全緑。
  計算ノードへの dispatch は、親が段 6 で自分の焦点走 job を qdel したことにより
  F47 型ラッチ (`compute-marker-not-observed`, request 909514.nqsv) が立って停止した。
  **ラッチは fail-closed の防壁なので削除していない。** 解除はユーザー手番 ({{T:f47-latch-recovery}})。
- 工数: codex 子 8 本 (plan 1・consult 2・author 1・review 2・fix 2) + 観測 probe 1 本。
  すべて `--evidence-grace-s 90` の回避で起動した。本 wave が land すれば
  worklog entry 541 記載の回避手順 (dry-run argv へ後付け) は二重指定になるため廃止する。

## 次の一手差分

### 完了

- [T-1067] `tools/dev_wave_codex.py` に `--evidence-grace-s` を追加し、
  既定 `min(90, --max-wall-clock-s)` で launcher へ 1 回だけ透過するようにした。
  あわせて Decimal のまま nanosecond へ写像する共有 validator を新設し、
  1 ns 未満へ丸められる値と overflow を rc=2 で拒む。
  remaining: none
  base: 90476ecec35f6e058148117076be9f2ba00c7df18d6edcb5a63622cec9ba1eb9

### 新規

- {{T:codex-error-item-classification}} **P2・新規・ユーザー裁定待ち**:
  launcher が `item.type=error` を一切見ない件の扱い。裁定 #2 の前提が実測で覆ったため
  差し戻す。択一 = (1) 現状維持、(2) 完全な turn lifecycle
  (`turn.started` ちょうど 1 回 → `turn.completed`) を `evidence_status=complete` の
  必要条件にする、(3) Codex CLI に機械可読な severity / code を要求する経路を確保してから分類する。
  控え = dev-wave-jobs/rulings-inbox/2026-08-13-codex-launcher-error-item-classification.md。
- {{T:f47-latch-recovery}} **P1・新規・ユーザー手番**:
  worktree `dev-wave-hooktrust-t1067` の
  `output/pegasus-dispatch/submission-disabled.json` (F47 型ラッチ、
  reason=`compute-marker-not-observed`、request 909514.nqsv) を解除しないと
  本 wave の受入全走と変異 matrix を実施できない。原因は親の qdel であり、
  投入自体は qstat で QUE として可視だった (F49 の有効性検査は成立していた)。
- {{T:launcher-test-memory-on-login}} **P2・新規**:
  `orchestrator/tests/test_codex_worker_launch.py` は login node の bounded scope 予算では
  完走できない (1.94GiB で cgroup attest が rc=16、4.29GiB で fake 子が cgroup OOM され
  59 件が exit -15 で赤)。予算算出が前回ピーク由来のため、このファイルだけ恒常的に
  不足する。dispatch 前提と明記するか、予算算出を見直すかを決める。
- {{T:evidence-receipt-sealing}} **P2・新規**:
  `evidence_grace_s` は caller が変えられて受理集合に影響するのに receipt から復元できない。
  版なしの optional field 追加は本 wave で撤回済み。receipt v4 で
  `evidence_grace_s` + `evidence_policy_version` + 構造化 rejection reason を
  まとめて封印する案を検討する。
- {{T:termination-reason-sealing}} **P2・新規**:
  `evidence_forced_stop` が receipt に出ないため、SIGTERM が evidence deadline 由来か
  外部 signal 由来かを receipt から区別できない。本 wave の P1 も
  「実測 5 走で裏付けた強い推論」までしか言えなかった。
- {{T:waiter-failclosed-vs-producer-files}} **P2・新規**:
  子が正しさで拒否されると output が公開されず、`dev_wave_wait.py producer` は
  それを `producer-files` (liveness/artifact 欠損) として扱う。正しさ拒否と
  producer 障害を receipt outcome で区別する。
