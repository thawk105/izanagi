---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-08
wave: dev-wave-t2406-s4loop-gflags
seq: 1
title: [T-2406] 段 4 loop の job body へ gflags/glog 供給経路を移植し、計算ノードで masstree 事前構築まで通した — 次の関門は condition gate の preprocess (コード + テスト + docs、branch worktree-dev-wave-t2406-s4loop-gflags、変異 15/17 KILLED・期待 node 完全一致・残 2 は等価と mask の正例)
---

## 本文

- 依頼: D1773 (ユーザー裁定、/rulings 全件 第 14 回) の実装。`tools/pegasus/floor_scoping.sh` の gflags/glog
  prologue を `tools/pegasus/p3_s4_loop_pegasus.sh` へそのまま移植し、契約テストと admission registry を同じ commit
  で揃え、`CMAKE_PREFIX_PATH` を driver 本走まで保持する。全 9 段 (契約テストの受理集合が変わるため軽量版にしない)。
- 段 3 (2 レンズ) と段 6 (2 レビュー) の所見: real・採用 10 件 (TMPDIR / install dir の束縛、検査面の実行面統一、
  事前構築への explicit `dependency_prefix`、TMPDIR / PATH の順序 marker、export 後 unset の拒否、コメント行の偽
  heredoc opener、`CMAKE_PREFIX_PATH` 行の exact 3 行 allowlist、prebuild < driver 2 本、heredoc 内 fragment の
  コメントアウト拒否、README §7 の実測境界)、real・不採用 (scope 外・記録) 6 件、refuted 2 件。
  設計判断は {{D:s4-loop-prefix-contract-exact-three-lines}}。
- registry は分類・reason・gate・evidence に変えるものが無く不変とした。D1773 (c) は「変える場合は同じ commit」と読む
  (段 3 レンズ A の nit)。ユーザーがこの読みを覆すなら再裁定。
- 素材: 計算ノードでの生死確認 (job `983020.nqsv`、固定 SHA a173f0ab5 の detached checkout、43S) で、
  gflags/glog prologue と masstree 事前構築が通り、receipt の `configure_argv` に 2 prefix が残った。
  driver 本走は condition gate `supply=preprocess-failed meaning=declared-meaning-observed` で rc=1。
  D1737 の留保「供給経路を足せば最後まで通るかは未実測」に対する答えは「事前構築までは通る、次は gate」。
- 変異: probe → 両層 probe → 本走の 3 段。本走は 17 変異、KILLED 15 / SURVIVED 2 (等価変異 m12 と、fix の
  exact 3 行 allowlist が旧検査を含意して mask する m13)、期待 node 完全一致、baseline PASSED。mask は両層同時変異
  m17 で KILLED を確認した。
- 受入: この記録 commit を含む tip に対して land 前に全走 (結果は受入 receipt と land 出力、終端の報告に残す)。
- セッション異常: `cd <別 worktree> && …` で永続 shell の cwd を移し Bash が全拒否、`EnterWorktree(path=自 worktree)` で
  復旧 (実害なし、F873 の再発として同 F へ再発追記)。
- 一次資料: `output/insights/2026-09-08_t2406-s4loop-gflags-prologue/README.md` (evidence、逐語、変異台帳、裁定)。
- 工数: codex 子 6 本 (plan 1、consult 2、author 1、review 2、fix 1 = 7 本)、計算ノード job 1 本 + 変異 dispatch 18 走 + 受入。

## 次の一手差分

### 完了

- [T-2406] D1773 を実装し main へ着地させた。契約テストの受理集合は exact 3 行 allowlist に固定、registry 不変、
  計算ノードで masstree 事前構築まで通ることを実測した。
  remaining: none
  base: c176f4ac2d1e61082aca753c670d905e58089fc3f0775ed23701ef36d2feefd3

### 新規

- {{T:s4-loop-condition-gate-preprocess-on-compute}} **P1・新規・裁定パッケージ候補**: 段 4 loop の job body は
  計算ノードで masstree 事前構築まで通るようになったが、driver 本走が `condition_meaning_gate` の supply arm
  (`preprocess-failed`) で止まる (job `983020.nqsv`、2026-09-08)。gate の preprocess argv と stderr を evidence root へ
  写す形で再現し、gflags/glog の include 経路 (計算ノードに system gflags が無い) との関係を確かめる。正しさ gate に
  触るので、修正方向は裁定パッケージで返す。
