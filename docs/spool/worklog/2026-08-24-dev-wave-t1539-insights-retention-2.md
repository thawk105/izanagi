---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-24
wave: dev-wave-t1539-insights-retention
seq: 2
title: cleanup occupancy既知赤を一時隔離しT-1539のland経路を回復した
---

## 本文

- T-1539の受入全走は`test_git_argv_spy_sees_only_allowlisted_cleanup_commands`が消滅pid型occupancy issueを3 scan連続観測しrc22で停止した。現行main、wave、serial単独走で再現し、T-1539のMarkdown差分から構造的に到達不能だった。
- 同nodeの主張はgit argv allowlistでありoccupancyではないため、既存`_stub_unoccupied`で局所分離した。対象nodeは1 passed。その後の同file serial走は同じrc22が別6 nodeで再現し83 passedだったため、D679のfile環境前提破損としてユーザー直接指示どおり一時除外した。
- canonical acceptanceだけがexact `test_dev_wave_cleanup.py`を除外する。explicit file/node、selector、collect-onlyは実行可能なまま。foreign/multiple entry、metadata drift、`--confcutdir`、duplicate suite root、mutable iterable/PathLikeはcommand前拒否またはtargeted扱いとし、検証済みcanonical tupleをlocal/dispatch/login collection/internal shard/receiptへ一貫して渡す。
- 敵対review 2本は計7件のreal所見を検出し、fix後focusはclosed 5・partial 0・regressed 0、新規blocker/must-fix 0。焦点走はselection契約2fileが287 passed、run_tests consumer 5fileが378 passed/1 skipped、cleanup対象nodeが1 passed。`check_codex_agents.py`と`check_docs.py`は緑。
- 変異probeはrunner-mode localでも内側runnerがPegasusへdispatchし、request `941934.nqsv`のorphan-holdで停止した。RUN終端を待って規定順でdirty sourceを復元し、probe結果はmatrix根拠に使わなかった。縮小したfinal2はbaseline PASSED・2/2 KILLED・SURVIVED/MISMATCH/TIMEOUT 0で、期待node全集合と実測が一致した。
- 実装commitは`14d06b28`。一時除外の解除は{{T:dev-wave-cleanup-occupancy-churn}}だけが所有する。

## 次の一手差分

### 新規

- {{T:dev-wave-cleanup-occupancy-churn}} **P1・新規**: `tools/check_worktree_occupancy.py`の消滅pid型issueが高process churn下で3 scan連続し、`test_dev_wave_cleanup.py`の実occupancy正例をrc22にする根本原因を修理する。専用live-process負例とunoccupied正例を維持し、explicit file走を全緑にして`orchestrator.test_selection_contract`のcleanup exclusionを同じwaveで空集合へ戻す。F489再発とD705の有界再試行不足を起点にし、skip/xfail/assert緩和で閉じない。
