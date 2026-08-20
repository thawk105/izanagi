---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-21
wave: t-1222-population-closure
seq: 1
title: '[T-1222] 成長比例母集合の未閉包を閉じ (11→12 node)、item2 の test 側欠陥を実装で解消した (コード+テスト、branch worktree-T-1222-population-closure、変異matrix = baseline PASSED・1/1 KILLED、item2静的gateは親の直接実測で裏取り)'
---

## 本文

- 一次資料は `docs/archive/worklog-phase3-0817-611.md`・同 `0817-638.md`
  (D499)・`output/insights/2026-08-16_t1222-growth-hold-sweep/`・同
  `2026-08-17_t1222-growth-leak-fix/`。D499 が「残件は母集合の未閉包のみ」と明記していた
  問題を閉じ、command が非対称に保護しなかった item2 を実装で解消した。判断根拠は
  {{D:t1222-item2-launcher-fix-supersedes-d499}}。
- 母集合再走査: 4 種の import idiom (package-relative / `sys.path` hack / `importlib` 動的
  ロード / `runpy`、既知11 node 自体がこの区別を怠った 08-16 走査の穴から見つかった) で
  `tools/*.py` 全 38 stem (brief 起草時「37」と誤カウントしたのを段4裁定で訂正) を
  `orchestrator/tests/` 全体と横断照合した。段3 lens B の敵対的指摘により、既知11 node の外に
  `test_check_subprocess_bytecode_guard.py::test_real_repo_clean` (実測 8.232 秒、
  `orchestrator/`+`tools/` 全 `.py` を rglob する安全ガード) を新規発見。冗長読取バグはなく
  (item3 型の修正余地なし)、item4 と同型の「安全ガードの全木走査は設計上必然」で `neither`
  (恒久保留への新規登録はしない)。同レンズの別指摘 (`test_s1_known_axes_freeze.py` 2 node) は
  `growth_test_holds.py:211,231` に既登録済みと確認し refuted。**母集合は 12 で閉じている。**
- D499 の item4 再訪条件 (90 秒閾値、決定時実測 約45秒) を `site=site_policy.OTHER` で
  Pegasus dispatch を回避し実測: `main()`=0.173 秒、`_audit_history()`=0.137 秒。生 CLI
  (`--range` のみ、site 未指定) は Pegasus LOGIN headroom/queue 判定を経由し 120 秒超でも
  未完走だった — 計算コストでなく dispatch/queue 待ちの計測になり不採用。premise は健在。
- item2 の実装は段2 codex plan (依存閉包が不完全) → 段3 敵対相談2レンズ (lens A が5件の
  major 所見: 依存閉包欠落・`pytest.skip.Exception`未対応・fixture生成順序・DW-M04一意性・
  self-load検出器 positive control破壊リスク。lens B は (P1) への「実装しない」推奨と、
  上記母集合所見) → 段4 親裁定 (P1 は実装する側を採用、lens A の5所見はすべて実装要件へ反映) →
  段5 Codex実装 → **親の実機検証で新規 real 欠陥1件を発見**: probe
  (`_sandbox_permits_short_alias_bind`) を親側 `_run_contained_serve_child()` へ移した結果、
  新設 `_dev_waves_serve_child.py` 内の `pytest.skip.Exception` 捕捉が到達不能になったのに
  `import pytest` が残存し、一部 Pegasus compute node で `ModuleNotFoundError` を誘発
  (`git checkout --` での新旧比較、DW-O19 に従い patch 退避→復元→diff 一致確認、2/2 再現・
  1/1 旧コード PASS で決定的と確認) → 段6 fix (該当 import/except 節を除去) → 焦点走 177 件
  全 PASS、という流れで進んだ。
- 変異事前登録は当初 M1 (launcher 定数の module 名を旧へ戻す)・M2 (growth contract 期待値を
  旧へ戻す) の2件。M1 は probe 走で `MISMATCH` — 対象定数が静的 assertion と実 subprocess
  起動の両方に使われる構造上、`xdist_group` 所属の socket test も副作用で赤くなり (原因は
  今回発見した pytest 欠陥と同型の `ModuleNotFoundError`)、D452 条件 (c) によりこの node は
  expected_nodes に加えられない。probe の生出力で静的 assertion 単体の正しい
  `AssertionError` を親が直接確認し、D452 の代替条項 (登録せず親の直接実測で裏取り) で処理した。
  M2 は1回目 dispatch artifact 収集失敗 (rc=16、`receipt scheduler_logs.stdout.path がない`、
  テスト結果ではない) で再投入、2回目で `KILLED`・期待どおり単一 node。
- **セッション異常 (再発なら段8 で一般化検討、今回は1例のみで DW-G03 未達):**
  worktree 隔離 (`EnterWorktree`) 前に起動した調査用 Agent fork (および再委任先の
  サブエージェント全6体) で、Bash が「worktree外のcwdへの拒否」エラーを恒常的に返し、
  `EnterWorktree`/`ExitWorktree` でも回復しなかった。fork は Read 中心の代替調査で完走。
  親 (worktree 隔離後に起動) は同じセッション内で Bash 正常。

## 次の一手差分

### 完了

- [T-1222] 成長比例母集合の未閉包 (D499 が「残件」と明記) を閉じ、既知の item2 test側欠陥を
  実装で解消した。母集合は12 node で閉じている (11 既知 + 新規発見1件、neither 分類)。
  remaining: none
  base: e55abb8ab6e53d7757d0432031c6b102d3928ebf944169d9e87b1378e530ed87

### 新規

- {{T:hold-inventory-bypass-surface-stale-labels}} **P2**: `tools/hold_inventory.py:107-141` の
  test 層 `bypass_surface` が `known-unresolved-bypass` と報告する4経路 (plain runner・
  `--noconftest`・`--confcutdir`・direct call) は、現行の二層 guard
  (`enforce_held_functions`/`_wrap_held_function`) が既に拒否しており誤報。
  `test_hold_inventory.py` が古い表現を固定している (2026-08-16 wave が「本waveが作った穴では
  ない」として起票のみ、本 wave も再確認しただけで未着手)。

- {{T:dev-wave-fork-before-enterworktree-breaks-bash}} **P2**: 背景 job で `EnterWorktree` 前に
  起動した Agent fork (および再委任先) で Bash が worktree 判定エラーを恒常的に返す事例を実測
  (本 worklog 「本文」節参照)。1 例のみで DW-G03 の族一般化閾値 (独立2例) 未達のため様子見。
  次回同型の事例が出たら「背景 job は worktree 隔離を先に完了してから調査 fork を起動する」を
  `docs/dev-wave/` へ一般化するか検討する。
