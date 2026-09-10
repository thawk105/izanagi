# next-tasks command の repo 移設と、main 系統 blocker (c12e25078) の前進修正 — 逐語・変異台帳

- wave: `worktree-dev-wave-next-tasks-command-20260908` (background job、隔離 worktree)
- 日付: 2026-09-08
- base: main c12e25078 (この commit 自体が系統 blocker)
- commit: A=48837186c (gitlink 除去 + 既知違反登録)、B=d42f2bec5 (next-tasks.md + checker 登録 + test)、C=5650dc842 (母集団 pin 追従)

## 何をしたか

1. `/home/SFC/tanab/.claude/commands/next-tasks.md` (27054 bytes、sha256 `10c6c0b489783d075a2ef76cb90773d465a8c4141737b0d11ea1117703c9ee15`) を
   `.claude/commands/next-tasks.md` へ bytes 同一で置いた。本文は変えていない。
2. `tools/check_docs.py` の `COMMAND_LIMITS` に `TextLimit(27_100, 100)`、`COMMAND_INTERFACES` に
   `{frontmatter_keys: {description, argument-hint}, arguments_count: 0}` を登録した (Codex author)。
3. `orchestrator/tests/test_check_docs.py` の合成 fixture に同名 command を足し、
   `test_next_tasks_command_budget_literal_is_exact` を足した (Codex author)。
4. main 先頭 c12e25078 が `.codex/worktrees/*` 110 本を gitlink (mode 160000) として誤 commit していたので、
   `git rm --cached -r .codex/worktrees` (作業 file は触らない) と
   `tools/known_violations/c12e25078…--missing-codex-author--e71feba7….json` の登録を 1 commit (A) にした。
5. 登録で production 台帳の post-baseline 件数が 2→3 になり、`test_check_ai_provenance.py` の母集団 pin 4 箇所を
   `(53, 3)` へ追従させた (C、Codex fix 子)。

## 実測

- 全史 provenance 監査: 登録前 job 982930.nqsv → child rc=1「8802 件中 1 新規違反 (c12e25078、110 paths)」。
  登録後 (A の後) job 982978.nqsv → child rc=0、c12e25078 は known-violation として列挙される。
- fresh worktree の submodule 初期化: 除去前 `runtime-io-failure (update-no-fetch)` /
  `fatal: no submodule mapping found in .gitmodules for path '.codex/worktrees/accwall-unit-a'`。index から除去した後は OK。
- `python3 tools/check_docs.py`: B の後 rc=0「違反なし」。
- 焦点走 (計算ノード、`focus-run-1.log`): job 982982 = test_check_docs / test_check_ai_provenance / test_dev_wave_wait →
  4 failed / 1312 passed / 3 skipped。赤 4 件はすべて `_known_violation_group_stdout(53, 2)` の母集団 pin (post-baseline 2→3)。
  C の後 (`focus-run-2.log`) job bab00678 = test_check_ai_provenance / test_check_docs → 938 passed / 3 skipped、rc=0。
- 変異 matrix (HEAD 5650dc842、`tools/mutation_harness.py --runner-mode dispatch`、runner = `tools/run_tests.py orchestrator/tests/test_check_docs.py -q -rf --force-dispatch`):
  - probe (`mutation-spec-probe.json` / `mutation-ledger-probe.json`、全件 SURVIVED 登録): M1 赤 332 node、M2 赤 1 node、M3 赤 0。
  - 本走 (`mutation-spec-final.json` sha256 `323c6c6249cf9b7bca2f226a9f51cae0c988283ac74d87201060e7c4b386c14f` /
    `mutation-ledger-final.json`): baseline PASSED、**M1 KILLED (332/332 完全一致)、M2 KILLED (1/1)、M3 SURVIVED (登録どおり)**、
    MISMATCH 0、harness rc=0。走行後の tree は clean、HEAD 不変。
  - M1 (COMMAND_LIMITS の next-tasks 行を除く) の 332 node のうち semantic は
    `test_next_tasks_command_budget_literal_is_exact` の 1 件。残り 331 件は合成 fixture が 4 件目の command を書くため
    「command byte予算が未登録」で一律赤になる drift mask 型の巻き添え (DW-M03 の冗長 gate)。
  - M2 (予算を 27_101 へ) は同 test 1 node の単一理由 kill。
  - M3 (COMMAND_INTERFACES の next-tasks 行を除く) は SURVIVED。interface 登録を検査する test が無い診断上の空白として
    記録する (等価変異ではない。実 repo の check_docs では登録の有無で frontmatter 検査が消えるが、それを固定する test は
    足していない。追加は編集境界の裁定と併せてユーザーへ返す)。
- 受入: 記録 commit の後に投入する。受領証は job dir `acc/acceptance-1.receipt.json` に出る (本 README 執筆時点では未投入)。

## land について (bootstrap 問題)

`tools/dev_wave_land.py` は main..tip の差分 path が `.codex/worktrees` に重なると `RC_CONTROL_PLANE=21` で拒否し
(`_verify_target_collisions`)、除去した gitlink の実 path が残ると同期を拒む (`_removed_gitlinks_absent`)。override は無い。
commit A は通常 land 経路では着地できない。ユーザーが主 checkout で `git cherry-pick 48837186c` する手番が要り、
それが既知違反登録の批准を兼ねる。cherry-pick 後は wave 側で main を merge (両側とも同じ gitlink 削除と同一 blob の JSON なので
自動 merge) してから land する。

## 段構成と工数

段 1 (親 brief) → 段 2・3 省略 (plan は file:line 確定) → 段 4 → 段 5 author 1 本 (45 model call) → 段 6 レビュー 2 本
(レンズ C / D、いずれも起動 1 回目は `--reasoning` 指定で rc=2、2 回目で完走) + fix 1 本 + 変異 probe/本走 + 受入 → 段 7 →
段 8 → 段 9 (ユーザー手番待ち)。

## ファイル

- `verbatim/s1-brief.md`、`verbatim/s5-author-prompt.md`、`verbatim/s5-author.md`、`verbatim/s6-review-c-prompt.md`、
  `verbatim/s6-review-c.md`、`verbatim/s6-review-d-prompt.md`、`verbatim/s6-review-d.md`、`verbatim/s6-fix1-prompt.md`、
  `verbatim/s6-fix1.md`
- `mutation-spec-probe.json`、`mutation-ledger-probe.json`、`mutation-spec-final.json`、`mutation-ledger-final.json`
- `focus-run-1.log`、`focus-run-2.log`
