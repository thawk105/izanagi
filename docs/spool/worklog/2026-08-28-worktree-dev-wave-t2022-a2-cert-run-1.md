---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-28
wave: worktree-dev-wave-t2022-a2-cert-run
seq: 1
title: [T-2022] A-2 fan-out 4-cell certificationを実走し、correctness certified・性能rejectを得た（コード + docs + 実機、branch worktree-dev-wave-t2022-a2-cert-run、変異matrix baseline PASSED・12/12 KILLED・SURVIVED 0・MISMATCH 0）
---

## 本文

- D646のland後別wave条件とD1139の批准撤去を確認し、2026-08-28のqueue混雑裁定どおり待ち件数だけでは投入を止めなかった。
- pre-existing attempt `t2022-20260827`の2 jobは旧worktree消失でidentity-error。新attemptの実走でpolicy case、build admission authority、Lustre publishの3実欠陥を順に露出し、D95 Codex authorへ最小修理を戻した。
- 実装commitは`cd161e49d`（submit/finish proof保全）、`e43a320af`（lowercase protocol）、`a0dd5c0bd`（canonical pin + BACKOFF_REPRO capability）、`639c1dbad`（spawn inventory）、`5dcea6e56`（EINVAL fallback）。
- 最終attempt `t2022-20260828c`、source=`639c1dbad`、pin=`511c953`、protocol=`136b823e...d9f4`。rr5=`954194.nqsv` / rr50=`954195.nqsv`を並行投入し、両終端後にlogin側finish-groupをexact 1回実行した。
- 4 cellすべてlegacy correctness 1/1、full-scale correctness 5/5 pass、performanceはtrace-disabled 5 samples complete。median TPSはrr5 stock 2,527,542 / fixed10 1,355,011（-46.3902%）、rr50 stock 3,662,448 / fixed5 1,248,603（-65.9080%）。outer statusは`reject`。
- tracked artifactは`output/insights/2026-08-24_paper-story-a2-certification/`、実走報告は`output/insights/2026-08-28_t2022-a2-certification-run/README.md`。A4 floorはopen、global minimalityは未確立、correctness argv独立観測なしの限界を維持した。
- focused検査は103 + 4 + 73 + 118 + 83 + 2 passed。final mutation4台帳の合計はbaseline PASSED、12/12 KILLED、SURVIVED/MISMATCH/TIMEOUT 0。受入はqueue timeoutをD612 overrideで再走しchild-green、spawn inventoryの帰属赤2件は2/2 passedで追随した。
- 失敗attemptの性能値は選別・流用せず、raw/acquisitionを最終attemptへ混ぜていない。verifier anomaly即reject、trace分離、絶対規律2を緩めなかった。

## 次の一手差分

### 完了

- [T-2022] A-2 fan-out submitterの実機初回検証と4-cell certificationを完了した。correctnessは4 cell certified、科学判定はadopted 2点の`reject`。
  remaining: none
  base: 16e45f08f4e7cccad27f37d0aaa2874b49e3cd993b1db9119136b1e8a4e33cb4

### 更新

- [T-2024] **P3・実測済み → 右寸法化待ち**: 正式fan-outのjob Elapseはrr5 3671s、rr50 3594s。現行06:00:00枠の次版を、この2値とsetup/cooldown余裕から別waveで決める。
  base: 29e1274130b21353bd869627dcdd5fe77eda71eb363669d364e424b2f384f69e

### 新規

- {{T:a2-partial-anomaly-lattice}} **P2・新規**: sibling driver非0と別workloadのraw anomalyが併存する場合のouter statusとpartial raw authorityを設計する。
- {{T:a2-correctness-argv-observation}} **P2・新規**: correctness run argv/binaryの独立観測をA-2 proof chainへ加えるか裁定する。現reportは非観測を明示済み。
- {{T:a2-publish-fallback-evidence}} **P2・新規**: EINVAL fallbackの選択事実とnon-cooperating writer限界をartifact schemaへ束縛するか裁定する。
