---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-28
wave: dev-wave-t1908-pegasus-floor
seq: 1
title: [T-1908] Pegasus write-heavy / balanced の current-pin floor scoping を既存 driver だけで再取得した（計測 + docs、branch worktree-dev-wave-t1908-pegasus-floor、実装差分なし）
---

## 本文

- ユーザー指定どおり、T-1905 と output root・prereg・driver の重複を開始時に検査した。T-1905 は
  B-10 prereg / `b10_backoff_shape` driver / campaign root、本 wave は既存
  `pegasus_floor_scoping` driver / repo 外 create-only root で、重複は無かった。
- ruling inbox #3 と D86 erratum の明示認可、D145 の量の境界、current activation serial 1 の
  Pegasus g1 contract、登録 calibration、queue 利用可を確認してから request `953495.nqsv` を投入した。
  script 既定の 3 時間予約は本 wave の 20〜30 分上限に対し過大なので、queued のまま walltime だけを
  30 分へ縮めた。測定内容と request ID は変えていない。
- 性能値は bnode006 で取得した。01:10:06〜01:16:48 JST、elapsed 406 秒、source commit
  `f34e19be94a3608099773ac6c1a12a98ae992048`、CCBench pin `511c953`、records 1,000,000、
  threads 48、clock 2100、trace-disabled stock baseline、within 10 reps、between 8 sessions × 5 reps。
- write-heavy は within CV 2.8641% / same-cohort between-session CV 1.2410% / abort 80.73%、
  balanced は 2.1585% / 0.5706% / 69.42%。両方 `high_variance=false`。job 非 0、単一テナント違反、
  環境値不一致は無く、raw JSON の tracked copy は外部原本と SHA-256 が一致した。
- D145 に従い、値は `same-submission-cohort-allocation-session-median-cv`、time-window cluster 1、
  compare 非適格である。正式 floor、certified evidence、環境同一性の完全証明へ昇格しない。
  B-10 prereg 本文、external-floor-derived reference、判定閾値、consumer、driver は変更していない。
- artifact と再現情報の正本は `output/insights/2026-08-28_t1908-pegasus-floor-scoping/`。
  read-heavy と判定器 / 成果物への版束縛を含む [T-1942] は完了させず、変更していない。
- 実装差分 0 のため D95 author と変異 matrix は免除。焦点検査は scoping driver 10 passed、repo-wide
  unknownness scan は初回 local OOM を緑に数えず、計算ノード再走 1 passed。全受入は
  18,185 passed / 61 skipped、child-green。`check_codex_agents` と `check_docs` は緑、provenance は
  新規違反 0。最初の artifact commit 前に `git diff --check` が hard-break の末尾空白を検出したが、
  連続 command が停止せず commit まで進んだため、意味不変の補正 commit を追加して以後は個別 rc で閉じた。
- エージェント工数: worker 0。既存 driver 無変更の docs / calibration artifact wave のため、
  段 2・3・5・6 は軽量版で省略し、親が実測・監査・記録を行った。

## 次の一手差分

### 完了

- [T-1908] Pegasus の write-heavy / balanced の current-pin same-cohort between-session 下限を、
  既存 driver の 2 workload 最小走で取得し、非配線の独立 artifact と insight へ束縛した。
  remaining: none
  base: c63cdfe8593718a52bc6ae462829b89964093046671e5f95892c2db54681efb4
