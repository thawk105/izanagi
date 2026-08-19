---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-19
wave: worktree-t391-condition-dispatch-verbatim-check
seq: 1
title: '[T-391] 条件 dispatch 表の発火条件セルへの参照 token 密輸検出を provenance 側から移植した (コード + テスト + docs、branch worktree-t391-condition-dispatch-verbatim-check、変異 matrix = baseline PASSED・1/1 KILLED・SURVIVED 0・MISMATCH 0)'
---

## 本文

- [T-391] の finding 本文 (worklog archive entry 146、2026-08-03 起票) を実測で検証したところ、
  finding が例示した具体例 (条件09の発火条件を「可能性が判明」から「変更すると決定」へ狭めても
  緑のまま通る) は、**2026-08-09 commit `8d2339708` ([T-313] の副産物、CONDITION_TRIGGER_CONTRACT
  による逐語照合の追加) で既に閉じていた**。実編集・即時復元 (finding の exploit を実際に
  `.claude/commands/dev-wave.md` へ適用して `check_docs` が検出することを確認 → revert) と、
  `git show f0bf1202^:tools/check_docs.py` (起票時点の版) の直接読解で確認した。
  worklog の carry stub (`- [T-391] (672)` 等) はこの完了を反映せず (681) まで機械的に
  持ち越され続けていた — [T-715] (entry 673) と同型の「carry の完了節記入漏れ」。
- finding のもう一方の要素「列所有」は、finding が引用した行範囲
  (`tools/check_docs.py:1761-1837,2873-2940`、起票時点の版) を照合すると
  `pair_owners`/`ownership_mismatches` ("key 所有が不一致") ではなく、
  `_condition_dispatch_table()` の `leaked_tokens` (第2列=発火条件セルへの参照 token 密輸検出、
  D110 決定3 に対応する provenance 側の独立 finding) を指すと判断した。この部分は
  dev-wave 側 (`.claude/commands/dev-wave.md` の条件 dispatch 表) に未移植だったので、
  `_dispatch_tables()` へ同型の機構を実装した (`_DispatchTables.condition_leaked_tokens`、
  独立の「diagnostic sensitivity」finding)。
- 実装は Codex `role=author` 子 (`t391-condition-dispatch-leaked-tokens`, model=gpt-5.6-luna,
  reasoning=high, outcome=accepted) が担当。brief どおりの最小差分
  (`tools/check_docs.py` 3箇所 + `orchestrator/tests/test_check_docs.py` テスト1件、計40行)。
- 変異 matrix (単一変異、`if leaked:` → `if False and leaked:`) は
  `tools/mutation_harness.py --runner-mode dispatch --detached` で本走し、baseline PASSED・
  1/1 KILLED (単一理由・matches_expectation=true)・SURVIVED 0・MISMATCH 0。
  新規コードのため旧 HEAD への同一置換は構造的に不可能 (フィールド自体が存在しない) であり、
  「新旧両走」の代替根拠は上記の起票時点ソース読解 (leaked-token 相当の処理が皆無) とする。
- 段8 自己改善: 背景 job (worktree 隔離) の handoff 配置で、`docs/handoff/README.md` に
  DW-O20 (背景 job は repo 外) への導線が無く、本 wave 自身が一度 worktree 内
  `docs/handoff/` へ誤って作成する near-miss を起こした (実害なし、check_wave_startup.py
  実行前に検出・是正)。`docs/handoff/README.md` へ 1 行の pointer を追加した
  (docs-only、専用 commit)。

## 次の一手差分

### 完了

- [T-391] 条件 dispatch 表の「発火条件の逐語」(既に解決済みと判明) と「列所有」
  (leaked-token 検出を本 wave で実装) の両方を閉じた。
  remaining: none
  base: 32ff573a1a3adac0d6345b2e049aea32d0029a63c04560552ffe47c8debb9c98
