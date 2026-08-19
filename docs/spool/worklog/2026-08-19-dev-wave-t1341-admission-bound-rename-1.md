---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-19
wave: dev-wave-t1341-admission-bound-rename
seq: 1
title: [T-1341] max_wall_clock_s を wall_clock_admission_bound_s へ改名した (コード+テスト+docs+記録、branch worktree-dev-wave-t1341-admission-bound-rename、変異matrix = baseline PASSED・2/2 KILLED・SURVIVED 0・MISMATCH 0)
---

## 本文

- 裁定原文: `docs/archive/worklog-phase3-0819-670.md:562` (/rulings 全件 第 7 回、択 (a) + 改名)。
  新名称 `wall_clock_admission_bound_s` は裁定原文に明記が無いため実装 wave 側で設計した。根拠と
  却下案は {{D:wall-clock-admission-bound-rename}}。
- 軽量版 (DW-C00): 純粋な識別子改名で正しさゲート・受理集合を変えないため段 2/3・段 6 review 子は
  省略した。段 5 (Codex `role=author`) が対象 4 ファイル (tools/codex_worker_launch.py,
  tools/dev_wave_codex.py, orchestrator/tests/test_codex_worker_launch.py,
  orchestrator/tests/test_dev_wave_codex.py、69 箇所) を一括改名し、grep 残存ゼロ・diff 69/69
  で完了。`wall_clock_s` (実測値、bare) と `wall_clock_scope` は対象外のまま維持を確認した。
- 親の実測: `tools/run_tests.py orchestrator/tests/test_codex_worker_launch.py
  orchestrator/tests/test_dev_wave_codex.py -q` が 67〜69 failed を示したため、diff を退避し
  同一 HEAD の改名前 (baseline) でも同数の failed を確認、単独再走 1 本
  (`test_hook_preflight_validates_repo_root`) は 1 passed で再現せず。既知 F57 (launcher 族の
  負荷依存フレーク) に帰属し本 diff 非帰属と判定した。子 (Codex author) は sandbox の Pegasus
  dispatch preflight 到達不能 (qstat -Q rc=1 EACCTAUTH) で pytest 未実走のため親が実走検収した。
- 変異 matrix: 初回登録 2 件のうち 1 件 (check-receipt の Decimal 分岐 selector) が SURVIVED
  (`test_check_receipt_marks_self_asserted_limits_and_accepts_external_expectations` の入力値
  "3" では Decimal 比較と fallback `==` 比較が偶然一致し、改名と無関係の既存カバレッジの弱さと
  判明)。DW-M02 に従い `_check_external_expectations` の `limit_names` tuple 要素落としへ
  再照準し、2/2 KILLED (SURVIVED 0・MISMATCH 0) で確定した。初回 erratum は job dir
  (`/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t1341-admission-bound-rename/`) に保全。

## 次の一手差分

### 完了

- [T-1341] `max_wall_clock_s` を `wall_clock_admission_bound_s` へ改名し、docs へ記録した。
  remaining: none
  base: 68a7eadd893e726854cd2d6003556f539b4950761d13de879f25984e84a1bed5
