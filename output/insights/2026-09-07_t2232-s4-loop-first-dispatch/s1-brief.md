# 段 1 brief — [T-2232 後続] 段 4 loop Pegasus job body の初回投入

## 依頼の前提を覆す新事実 (段 4 で再裁定)

依頼本文が求める「段 4 自律 loop 用の Pegasus job script を作り、既存の投入経路から実 job を
投入できる状態にする」は **2026-09-07 03:19 に着地済み**である。

- land 受領証 `dev-wave-jobs/dev-wave-t2232-s4-loop-pegasus-job-script/land-2.json`:
  `status=landed`、`main_after=1a820a913`、`tested_tip=e59d8e4c3`
- `git merge-base --is-ancestor 1a820a913 HEAD` = 0
- worklog entry (1286) = `docs/archive/worklog-phase3-0907-1285-1286.md:538`
- 一次資料 = `output/insights/2026-09-05_t2232-s4-loop-pegasus-job-script/README.md`、変異 16/16 KILLED
- 依頼本文の制約 (F813、masstree `config.h` 事前構築、python3.10 shim、`-o`/`-e` の repo 外転送、
  登録簿・手順書投影・README の同時同期) はすべて着地物が満たしている

依頼本文は land 自身の fold が書いた **stale carry** である。再実装しない。
台帳が明示する残件は「初回投入と reservation / attestation の実効確認は後続 wave」であり、
`grep -rn p3_s4_loop_pegasus docs/` の結果は runbook §7.0 投影行と D1663 だけで、実走記録はない。

## scope (F35「stale なら依存項目を繰り上げる」)

`tools/pegasus/p3_s4_loop_pegasus.sh` を **既存の投入経路から実際に 1 回投入し、
どこまで通ってどこで止まるかを実測して記録する**。fixture 経路 (`--value 20`) を使う。

- scope 内: 専用 checkout の用意、hydrate、evidence root の用意、qsub 1 本、結果の読解、記録
- scope 外: 予測された障害の先回り修正、attestation 照合の緩和、job body の機能追加、一般化
- 実装面の差分は既定でゼロ。実測した欠陥に対する修正の要否は段 4 で裁定する

## 不変条件

- 規律 2: 正しさゲートを緩めない。job body の `refuse` を回避する迂回を実装しない
- F813: PATH の CMake wrapper で third-party を注入しない (job body の現状を変えない)
- 推測で迂回しない。割れたら再現条件と停止点を記録して止める
- `-o` / `-e` は evidence root へ向け、投入時 directory を汚さない
- REPO_ROOT に `.claude/worktrees/` / `.codex/worktrees/` 配下を使わない (job body が rc=2)

## 割れうる前提 (親の provisional 裁定・攻撃対象)

- (P1) 固定 SHA の detached worktree を REPO_ROOT にしてよい。`git-common-dir` は primary repo を
  指すので、evidence root は primary repo の外にも置く必要がある → job dir 配下に置く
- (P2) 計算ノードに `/scr/$USER` が在り書ける
- (P3) 計算ノードに `python3.10` が在り `orchestrator.campaign.p3_s4_loop` を import できる
- (P4) 計算ノード側 `qstat -f` から reservation 2 値が取れる。
  **login 実物では成立を確認済み** (limits 1 件 = 21600、`Started Request Time` が `date -d` で解ける)。
  計算ノード側の view が同一かは未実測
- (P5) masstree の FetchContent 事前構築が proxy 経由で通る
- (P6) driver が `env_attestation` の exact 照合を通る (台帳が名指しする未実測障害)
- (P7) claim root の provisioning が submit-tree 配下で通る (同上)

## 成果物

- evidence root: `compute-result.json`、`reservation.json`、`masstree-prebuild-receipt.json`、
  `allocation-qstat.*`、`job.stdout` / `job.stderr`
- insight dir に一次資料 (投入 argv、job ID、停止点、再現条件)
- worklog / decisions / failures fragment (spool 形式)

## 分割方針

軽量版。設計択一は割れず、正しさ防壁に触れず、受理集合も変えないので段 2・3 と段 6 review 子は
省く。実測は省かない。実測した欠陥への修正が必要と裁定した場合だけ、Codex `role=author` の
実装子と fix 後の焦点再レビューを起こす。

## 受入・実測環境

- 投入: login node から `qsub` (`/system/tool/bin/qsub`)、queue `gen_S` は ENA/ACT (RUN 24 / QUE 9)
- third-party cache root = `/work/1/SFC/tanab/izanagi-thirdparty-cache` (runbook §6 正本、3 本実在)
- 受入全走は段 7 の記録 commit 後に投入する
